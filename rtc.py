"""
CLI helper to read DS3231 via the refactored RTC module.
"""

from __future__ import annotations

import sys

from modules.sensors import rtc


def main() -> int:
    try:
        current_time, source = rtc.get_current_time(fallback_to_system=False)
    except Exception as exc:
        print(f"[RTC] 읽기 실패: {exc}")
        return 1
    print(f"[RTC] {current_time.isoformat()} (source={source})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
