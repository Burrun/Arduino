"""
GPS sensor module (ESP32-CAM / NEO-6M).
Fetches GPS data from ESP32-CAM via HTTP.
"""

from __future__ import annotations

import os
import time
import requests
from typing import Dict, Optional, Tuple

# Default ESP32-CAM URL
ESP32_CAM_URL = os.environ.get("ESP32_CAM_URL", "http://192.168.4.1")

def get_current_location(
    timeout: int = 10,
    base_url: Optional[str] = None,
) -> Dict[str, str]:
    """
    Get current location from ESP32-CAM GPS.
    Returns a dictionary with latitude, longitude, and timestamp.
    """
    target_url = (base_url or ESP32_CAM_URL).rstrip("/") + "/gps"
    print(f"[GPS] 위치 정보 요청 중: {target_url}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(target_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Expected format: {"lat": 37.123, "lon": 127.123, "timestamp": "..."}
                # Or similar. Adjusting to ensure we return strings.
                return {
                    "latitude": str(data.get("lat", "0.0")),
                    "longitude": str(data.get("lon", "0.0")),
                    "timestamp": str(data.get("timestamp", "")),
                }
            else:
                print(f"[GPS] 응답 오류: {response.status_code}")
        except requests.RequestException as e:
            print(f"[GPS] 연결 실패 (재시도 중...): {e}")
        
        time.sleep(1)

    raise TimeoutError("GPS 응답 시간 초과")
