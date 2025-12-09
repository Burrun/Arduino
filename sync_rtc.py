#!/usr/bin/env python3
"""RTC 시간 동기화 스크립트"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.sensors.rtc import set_rtc

if __name__ == "__main__":
    try:
        current_time = datetime.now()
        set_rtc(current_time)
        print(f"RTC 시간 동기화 완료: {current_time}")
    except Exception as e:
        print(f"RTC 동기화 실패: {e}")
        sys.exit(1)
