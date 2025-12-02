"""
Camera sensor module (ESP32-CAM).
Fetches image from ESP32-CAM via HTTP.
"""

from __future__ import annotations

import os
import time
import requests
from pathlib import Path
from typing import Optional

# Default ESP32-CAM URL
ESP32_CAM_URL = os.environ.get("ESP32_CAM_URL", "http://192.168.4.1")

def capture_image(
    save_path: str = "capture.jpg",
    timeout: int = 10,
    base_url: Optional[str] = None,
) -> str:
    """
    Capture an image from the ESP32-CAM and save it to disk.
    Returns the saved file path.
    """
    target_url = (base_url or ESP32_CAM_URL).rstrip("/") + "/capture"
    print(f"[카메라] 이미지 요청 중: {target_url}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(target_url, timeout=5)
            if response.status_code == 200:
                # Save the image
                save_path = str(save_path)
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                print(f"[카메라] 저장 완료: {save_path}")
                return save_path
            else:
                print(f"[카메라] 응답 오류: {response.status_code}")
        except requests.RequestException as e:
            print(f"[카메라] 연결 실패 (재시도 중...): {e}")
        
        time.sleep(1)
    
    raise TimeoutError("카메라 응답 시간 초과")

def is_camera_connected(base_url: Optional[str] = None, timeout: int = 3) -> bool:
    """
    Check if ESP32-CAM is reachable without capturing an image.
    Returns True if camera is available, False otherwise.
    """
    try:
        target_url = (base_url or ESP32_CAM_URL).rstrip("/")
        # Try a simple ping or status check
        response = requests.get(target_url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False

__all__ = ["capture_image", "is_camera_connected"]
