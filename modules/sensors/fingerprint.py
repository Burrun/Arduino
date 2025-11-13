"""
Fingerprint sensor helpers (Adafruit/ZFM series).

Isolated so the acquisition logic can be reused by scripts that either save
images locally or forward them to a backend.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List, Optional

try:
    import serial
    import adafruit_fingerprint

    HAS_FINGERPRINT_DEPS = True
except Exception:  # pragma: no cover - dev hosts often miss hardware deps
    serial = None
    adafruit_fingerprint = None
    HAS_FINGERPRINT_DEPS = False

UART_PORT = os.environ.get("FP_UART", "/dev/serial0")
UART_BAUD = int(os.environ.get("FP_UART_BAUD", "57600"))


def connect_fingerprint_sensor(
    port: Optional[str] = None,
    baudrate: Optional[int] = None,
    timeout: float = 1.0,
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
        from serial.tools import list_ports

        available_ports = [info.device for info in list_ports.comports()]
    except Exception:
        available_ports = []

    candidate_ports: List[str] = []
    if target_port:
        candidate_ports.append(target_port)

    should_autofallback = not port or target_port not in available_ports
    if should_autofallback:
        for detected in available_ports:
            if detected not in candidate_ports:
                candidate_ports.append(detected)

    last_exc: Optional[BaseException] = None
    chosen_port: Optional[str] = None
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


    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
    if finger.count_templates() is None:
        raise RuntimeError("지문센서 연결 실패(배선/UART/전원 확인).")
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

    raw = bytearray()
    if finger.download_image(raw) != adafruit_fingerprint.OK:
        raise RuntimeError("이미지 다운로드 실패")

    expected_len = width * height
    if len(raw) != expected_len:
        print(
            f"[경고] 예상 바이트({expected_len}) != 수신({len(raw)}). 모델/해상도 확인 필요."
        )

    save_path = str(save_path)
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as file:
        header = f"P5\n{width} {height}\n255\n".encode("ascii")
        file.write(header)
        if len(raw) >= expected_len:
            file.write(raw[:expected_len])
        else:
            file.write(raw + bytes([0]) * (expected_len - len(raw)))

    return save_path


__all__ = ["connect_fingerprint_sensor", "capture_fingerprint_image"]
