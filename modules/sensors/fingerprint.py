"""
Fingerprint sensor helpers (Adafruit/ZFM series).

Isolated so the acquisition logic can be reused by scripts that either save
images locally or forward them to a backend.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

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

    uart = serial.Serial(port or UART_PORT, baudrate=baudrate or UART_BAUD, timeout=timeout)
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
