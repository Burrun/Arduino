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
    HAS_FINGERPRINT_DEPS = True
except Exception:  # pragma: no cover - dev hosts often miss hardware deps
    serial = None
    adafruit_fingerprint = None
    list_ports = None
    HAS_FINGERPRINT_DEPS = False

UART_PORT = os.environ.get("FP_UART", "/dev/serial0")
UART_BAUD = int(os.environ.get("FP_UART_BAUD", "57600"))
print(f"[DEBUG] target UART_PORT={UART_PORT}, UART_BAUD={UART_BAUD}")


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
    for extra in ("/dev/ttyAMA0", "/dev/ttyS0", "/dev/serial0"):
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
    save_path: str = "fingerprint.pgm",
    timeout_sec: int = 10,
    width: int = 256,
    height: int = 288,
) -> str:
    """
    Capture a fingerprint image and store it as binary PGM (P5) file.
    Returns the saved file path.
    """
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
    data_list = finger.get_fpdata(sensorbuffer="image")  # List[int]
    
    if not data_list:
        raise RuntimeError("센서에서 이미지 데이터를 받지 못했습니다")
    
    raw = bytes(data_list)
    expected_size = width * height    
    save_path = str(save_path)
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    
    # PGM 파일 저장
    with open(save_path, "wb") as file:
        header = f"P5\n{width} {height}\n255\n".encode("ascii")
        file.write(header)
        
        if len(raw) >= expected_size:
            # 데이터가 충분하면 필요한 만큼만 사용
            file.write(raw[:expected_size])
        else:
            # 데이터가 부족하면 0으로 패딩
            file.write(raw)
            padding_size = expected_size - len(raw)
            file.write(bytes([0]) * padding_size)
            print(f"[지문] {padding_size} bytes 패딩 추가됨")
    
    print(f"[지문] PGM 저장 완료: {save_path}")
    return save_path

def probe_sensor_handshake(
    port: Optional[str] = None,
    baudrate: Optional[int] = None,
    timeout: float = 1.0,
) -> dict:
    """
    Perform low-level handshake test (VfyPwd) with fingerprint sensor.
    Returns dict with success status, port info, and response details.
    This is a lightweight check compared to full connection.
    """
    if not HAS_FINGERPRINT_DEPS:
        return {
            "success": False,
            "error": "Dependencies not installed",
        }
    
    target_port = port or UART_PORT
    target_baud = baudrate or UART_BAUD
    
    try:
        # Try to open serial port
        uart = serial.Serial(target_port, baudrate=target_baud, timeout=timeout)
        time.sleep(0.1)
        uart.reset_input_buffer()
        uart.reset_output_buffer()
        time.sleep(0.1)
        
        # Create fingerprint object
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        # Try to verify password (handshake with sensor)
        # This sends VfyPwd command which is lighter than full template count
        try:
            result = finger.verify_password()
            uart.close()
            
            if result == adafruit_fingerprint.OK:
                return {
                    "success": True,
                    "port": target_port,
                    "baudrate": target_baud,
                    "confirm_code": 0x00,
                    "response_hex": "OK (0x00)",
                }
            else:
                return {
                    "success": False,
                    "port": target_port,
                    "baudrate": target_baud,
                    "confirm_code": result,
                    "response_hex": f"0x{result:02X}",
                    "error": f"Sensor returned error code: 0x{result:02X}",
                }
        except Exception as e:
            uart.close()
            return {
                "success": False,
                "port": target_port,
                "baudrate": target_baud,
                "error": f"Handshake failed: {e}",
            }
            
    except (FileNotFoundError, serial.SerialException) as e:
        return {
            "success": False,
            "port": target_port,
            "baudrate": target_baud,
            "error": f"Port open failed: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "port": target_port,
            "baudrate": target_baud,
            "error": f"Unexpected error: {e}",
        }


def is_sensor_connected() -> bool:
    """
    Check if fingerprint sensor is connected using lightweight handshake.
    Returns True if sensor is available, False otherwise.
    """
    if not HAS_FINGERPRINT_DEPS:
        return False
    
    # Use the more reliable handshake method
    result = probe_sensor_handshake()
    return result.get("success", False)

async def capture_fingerprint_async(timeout_sec: int = 15) -> str:
    """
    Capture a fingerprint image asynchronously.
    Returns the saved file path.
    Raises RuntimeError if capture fails.
    """
    import asyncio
    from datetime import datetime
    
    print("[FINGERPRINT MODULE] Starting fingerprint capture...")
    
    # Create save directory
    image_dir = Path("data/fingerprints")
    image_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"fingerprint_{timestamp}.pgm"
    image_path = image_dir / filename
    
    # Run blocking fingerprint capture in executor
    def _capture():
        finger = connect_fingerprint_sensor()
        return capture_fingerprint_image(finger, save_path=str(image_path), timeout_sec=timeout_sec)
    
    loop = asyncio.get_event_loop()
    saved_path = await loop.run_in_executor(None, _capture)
    
    print(f"[FINGERPRINT MODULE] Captured: {saved_path}")
    return saved_path

__all__ = ["connect_fingerprint_sensor", "capture_fingerprint_image", "is_sensor_connected", "probe_sensor_handshake", "capture_fingerprint_async"]
