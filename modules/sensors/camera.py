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
import asyncio

def is_camera_connected(base_url: Optional[str] = None, timeout: int = 3) -> bool:
    """
    Check if camera data is being updated in images/ folder.
    Waits up to timeout seconds for a new image.
    Returns True if a new image appears, False otherwise.
    """
    try:
        images_dir = Path("images")
        if not images_dir.exists():
            return False
        
        # Get initial state
        initial_mtime = 0.0
        files = list(images_dir.glob("*.jpg"))
        if files:
            initial_mtime = max(f.stat().st_mtime for f in files)
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for updates
            files = list(images_dir.glob("*.jpg"))
            if files:
                current_mtime = max(f.stat().st_mtime for f in files)
                if current_mtime > initial_mtime:
                    return True
            
            time.sleep(0.1)
            
        return False
    except Exception:
        return False

async def get_latest_image(wait_time: int = 5) -> str:
    """
    Wait for wait_time seconds, then return the path to the latest image in images/ folder.
    Raises FileNotFoundError if no images found.
    """
    print(f"[CAMERA MODULE] Waiting {wait_time} seconds for latest image...")
    await asyncio.sleep(wait_time)
    
    images_dir = Path("images")
    if not images_dir.exists():
        raise FileNotFoundError("No images folder found")
    
    # Get the most recent image file
    image_files = sorted(images_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not image_files:
        raise FileNotFoundError("No image received yet")
        
    return str(image_files[0])

__all__ = ["capture_image", "is_camera_connected", "get_latest_image"]
