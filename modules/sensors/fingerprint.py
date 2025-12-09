"""
AS608 fingerprint sensor module.
Fingerprint sensor helpers (Adafruit/ZFM series).
"""

from __future__ import annotations

import os
import time

from pathlib import Path
from typing import List, Optional

try:   
    import serial
    from serial.tools import list_ports
    import adafruit_fingerprint
    from PIL import Image
    HAS_FINGERPRINT_DEPS = True
except Exception:  # pragma: no cover - dev hosts often miss hardware deps
    serial = None
    adafruit_fingerprint = None
    list_ports = None
    Image = None
    HAS_FINGERPRINT_DEPS = False

UART_PORT = os.environ.get("FP_UART", "/dev/ttyS0")
UART_BAUD = int(os.environ.get("FP_UART_BAUD", "57600"))
print(f"[DEBUG] target UART_PORT={UART_PORT}, UART_BAUD={UART_BAUD}")


def probe_sensor_handshake(
    port: Optional[str] = None,
    baudrate: Optional[int] = None,
    timeout: float = 2.0,
):
    """
    Send a raw VfyPwd (0x13) packet to the sensor and return response metadata.
    This is a lightweight check that mirrors `test/fingerprint_test.py`.
    """
    if not HAS_FINGERPRINT_DEPS:
        raise RuntimeError("pyserial이 설치되어 있어야 합니다.")

    target_port = port or UART_PORT
    baud = baudrate or UART_BAUD
    handshake = bytes(
        [
            0xEF,
            0x01,
            0xFF,
            0xFF,
            0xFF,
            0xFF,
            0x01,
            0x00,
            0x07,
            0x13,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x1B,
        ]
    )

    response = b""
    last_exc: Optional[BaseException] = None

    try:
        with serial.Serial(
            target_port,
            baudrate=baud,
            timeout=timeout,
        ) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(handshake)
            ser.flush()

            # Give the sensor a brief moment to respond
            end_at = time.time() + timeout
            while time.time() < end_at:
                waiting = ser.in_waiting
                if waiting:
                    response += ser.read(waiting)
                    # small extra read to catch trailing bytes
                    time.sleep(0.05)
                    response += ser.read(ser.in_waiting)
                    break
                time.sleep(0.05)
    except BaseException as exc:
        last_exc = exc

    success = (
        len(response) >= 12
        and response[0:2] == b"\xEF\x01"
        and response[9] == 0x00
    )
    confirm_code = response[9] if len(response) > 9 else None

    return {
        "success": success,
        "port": target_port,
        "baudrate": baud,
        "response_hex": response.hex(),
        "confirm_code": confirm_code,
        "error": last_exc,
    }


def connect_fingerprint_sensor(
    port: Optional[str] = None,
    baudrate: Optional[int] = None,
    timeout: float = 2.0,
):
    """
    Open UART connection and return `adafruit_fingerprint.Adafruit_Fingerprint`.
    Raises RuntimeError if deps are missing or sensor handshake fails.
    """
    if not HAS_FINGERPRINT_DEPS:
        raise RuntimeError(
            "지문 센서를 사용하려면 pyserial 및 adafruit-circuitpython-fingerprint가 필요합니다."
        )

    target_port = port or UART_PORT

    available_ports: List[str] = []
    try:
      

        available_ports = [info.device for info in list_ports.comports()]
    except Exception:
        available_ports = []

    candidate_ports: List[str] = []
    if target_port:
        candidate_ports.append(target_port)

    fallback_ports: List[str] = []
    if UART_PORT and UART_PORT not in fallback_ports:
        fallback_ports.append(UART_PORT)
    for extra in ("/dev/ttyS0", "/dev/ttyAMA0", "/dev/serial0"):
        if extra and extra not in fallback_ports:
            fallback_ports.append(extra)

    should_autofallback = not port or target_port not in available_ports
    if should_autofallback:
        for detected in available_ports:
            if detected not in fallback_ports:
                fallback_ports.append(detected)

    for extra in fallback_ports:
        if extra and extra not in candidate_ports:
            candidate_ports.append(extra)

    last_exc: Optional[BaseException] = None
    chosen_port: Optional[str] = None
    uart = None

    for candidate in candidate_ports:
        try:
            uart = serial.Serial(
                candidate,
                baudrate=baudrate or UART_BAUD,
                timeout=timeout,
            )
            chosen_port = candidate
            break
        except (FileNotFoundError, serial.SerialException) as exc:
            last_exc = exc

    if chosen_port is None:
        hint = (
            "감지된 시리얼 포트가 없습니다. 배선/전원 및 권한을 확인하세요."
            if not available_ports
            else "사용 가능한 포트: " + ", ".join(available_ports)
        )
        error_port = candidate_ports[0] if candidate_ports else target_port
        raise RuntimeError(
            f"지정한 포트({error_port})를 열 수 없습니다: {last_exc}. {hint}"
        ) from last_exc

    if chosen_port != target_port:
        print(
            f"[지문] 요청한 포트 {target_port!r} 대신 {chosen_port!r}에 자동 연결했습니다."
        )

    time.sleep(0.1)
    uart.reset_input_buffer()
    uart.reset_output_buffer()
    time.sleep(0.1)

    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("지문센서 연결 실패(배선/UART/전원 확인).") from None
    return finger


def capture_fingerprint_image(
    finger,
    save_path: str = "fingerprint.png",
    timeout_sec: int = 10,
    width: int = 256,
    height: int = 288,
) -> str:
    """
    Capture a fingerprint image and store it as PNG (uses Pillow).
    Returns the saved file path.
    """
    if Image is None:
        raise RuntimeError("Pillow(PIL) 패키지가 필요합니다. `pip install pillow`")

    print("[지문] 손가락을 센서에 올려주세요...")
    start = time.time()
    while time.time() - start < timeout_sec:
        result = finger.get_image()
        if result == adafruit_fingerprint.OK:
            break
        if result in (adafruit_fingerprint.NOFINGER, adafruit_fingerprint.IMAGEFAIL):
            time.sleep(0.2)
            continue
        raise RuntimeError(f"이미지 캡처 실패 코드: {result}")
    else:
        raise TimeoutError("지문 인식 시간 초과")

    # image 데이터 가져오기
    print("[지문] 지문 인식 성공! 이미지 데이터 다운로드 중... (약 5-10초 소요)")
    data_list: List[int] = []

    # Downloading ~50-90KB over 57600bps takes ~10-12s; bump timeout temporarily.
    original_timeout = getattr(getattr(finger, "_uart", None), "timeout", None)
    try:
        if getattr(finger, "_uart", None) and hasattr(finger._uart, "timeout"):
            finger._uart.timeout = max(original_timeout or 0, 15)
            try:
                finger._uart.reset_input_buffer()
                finger._uart.reset_output_buffer()
            except Exception:
                pass

        data_list = finger.get_fpdata(sensorbuffer="image")  # List[int]
    finally:
        if (
            getattr(finger, "_uart", None)
            and original_timeout is not None
            and hasattr(finger._uart, "timeout")
        ):
            try:
                finger._uart.timeout = original_timeout
            except Exception:
                pass
    
    if not data_list:
        raise RuntimeError("센서에서 이미지 데이터를 받지 못했습니다")
    
    raw = bytes(data_list)
    expected_size = width * height    
    save_path = str(save_path)
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    if len(raw) < expected_size:
        padding_size = expected_size - len(raw)
        raw = raw + bytes([0] * padding_size)
        print(f"[지문] {padding_size} bytes 패딩 추가됨")
    elif len(raw) > expected_size:
        raw = raw[:expected_size]

    image = Image.frombytes("L", (width, height), raw)
    image.save(save_path, format="PNG")

    print(f"[지문] PNG 저장 완료: {save_path}")
    return save_path

def is_sensor_connected() -> bool:
    """
    Check if fingerprint sensor is connected without performing full connection.
    Returns True if sensor is available, False otherwise.
    """
    if not HAS_FINGERPRINT_DEPS:
        return False
    
    try:
        finger = connect_fingerprint_sensor()
        # If we get here, sensor is connected
        return True
    except Exception:
        return False

__all__ = [
    "connect_fingerprint_sensor",
    "capture_fingerprint_image",
    "probe_sensor_handshake",
    "is_sensor_connected",
]
