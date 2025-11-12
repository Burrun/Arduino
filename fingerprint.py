"""
Standalone helper that uses the refactored sensor modules to capture a single
fingerprint image after printing the current RTC/system time.
"""

from __future__ import annotations

import sys

from modules.sensors import fingerprint, rtc


def main() -> int:
    current_time, source = rtc.get_current_time()
    print(f"[시간] {current_time.strftime('%Y-%m-%d %H:%M:%S')} (source={source})")

    try:
        finger = fingerprint.connect_fingerprint_sensor()
        out = fingerprint.capture_fingerprint_image(finger, save_path="fingerprint.pgm", timeout_sec=15)
        print(f"[지문] 이미지 저장 완료: {out}")
        return 0
    except Exception as exc:  # pragma: no cover - runtime feedback
        print(f"[지문] 실패: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
