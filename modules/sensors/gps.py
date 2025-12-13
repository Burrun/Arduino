"""
GPS sensor module (ESP32-CAM / NEO-6M).
Fetches GPS data from ESP32-CAM via HTTP.
"""

from __future__ import annotations

import os
import time
import requests
from typing import Dict, Optional, Tuple


import re
from pathlib import Path
import asyncio

FALLBACK_LAT = 37.49638
FALLBACK_LON = 126.9569


def _nmea_to_decimal(raw: str, hemisphere: str) -> Optional[float]:
    """Convert NMEA ddmm.mmmm (lat) / dddmm.mmmm (lon) to decimal degrees."""
    if not raw or not hemisphere:
        return None
    try:
        deg_len = 2 if hemisphere in ("N", "S") else 3
        degrees = int(raw[:deg_len])
        minutes = float(raw[deg_len:])
        value = degrees + minutes / 60
        if hemisphere in ("S", "W"):
            value *= -1
        return value
    except ValueError:
        return None


def _parse_nmea_sentence(sentence: str) -> Optional[Tuple[float, float]]:
    """
    Try to extract (lat, lon) from a single NMEA sentence.
    Supports $GPRMC (A status) and $GPGGA (non-zero fix quality).
    Falls back to plain 'lat,lon' if present.
    """
    if sentence.startswith("$GPRMC"):
        parts = sentence.split(",")
        if len(parts) > 6 and parts[2] == "A":
            lat = _nmea_to_decimal(parts[3], parts[4])
            lon = _nmea_to_decimal(parts[5], parts[6])
            if lat is not None and lon is not None:
                return lat, lon

    if sentence.startswith("$GPGGA"):
        parts = sentence.split(",")
        if len(parts) > 6 and parts[6] not in ("0", ""):
            lat = _nmea_to_decimal(parts[2], parts[3])
            lon = _nmea_to_decimal(parts[4], parts[5])
            if lat is not None and lon is not None:
                return lat, lon

    # Keep support for existing plain "lat,lon" format
    if "," in sentence:
        parts = sentence.split(",")
        if len(parts) >= 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                pass

    return None


def is_gps_connected(base_url: Optional[str] = None, timeout: int = 3) -> bool:
    """
    Check if GPS data is being updated in gps/gps_data.txt.
    Waits up to timeout seconds for a file update.
    Returns True if the file is updated, False otherwise.
    """
    try:
        gps_file = Path("gps/gps_data.txt")
        if not gps_file.exists():
            return False
        
        # Get initial state
        initial_mtime = gps_file.stat().st_mtime
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for updates
            if gps_file.exists():
                current_mtime = gps_file.stat().st_mtime
                if current_mtime > initial_mtime:
                    return True
            
            time.sleep(0.1)
            
        return False
    except Exception:
        return False

async def get_current_location(wait_time: int = 5) -> Dict[str, str]:
    """
    Wait for wait_time seconds, then get the latest GPS data from gps/gps_data.txt.
    Parses the recent lines to find valid coordinates (NMEA or plain "lat,lon").
    Returns a dictionary with latitude, longitude, and timestamp
    """
    
    print(f"[GPS MODULE] Waiting {wait_time} seconds for latest GPS data...")
    await asyncio.sleep(wait_time)
    
    gps_file = Path("gps/gps_data.txt")
    
    lat = None
    lon = None
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Try to read from file
    if gps_file.exists():
        try:
            with open(gps_file, "r", encoding="utf8") as f:
                lines = f.readlines()

            # Check recent lines (latest first) for valid data
            for line in reversed(lines[-200:]):
                line = line.strip()
                match = re.search(r'\[(.+?)\]\s+(.+)', line)
                if not match:
                    continue

                ts = match.group(1)
                sentence = match.group(2).strip()
                parsed = _parse_nmea_sentence(sentence)
                if parsed:
                    temp_lat, temp_lon = parsed
                    if not (temp_lat == 0.0 and temp_lon == 0.0):
                        lat = temp_lat
                        lon = temp_lon
                        timestamp_str = ts
                        break
        except Exception as e:
            print(f"[GPS MODULE] Error reading file: {e}")
    
    # Use fallback if GPS data not available
    if lat is None or lon is None:
        print(f"[GPS MODULE] Using hardcoded fallback: {FALLBACK_LAT}, {FALLBACK_LON}")
        lat = FALLBACK_LAT
        lon = FALLBACK_LON
    
    return {
        "latitude": str(lat),
        "longitude": str(lon),
        "timestamp": timestamp_str
    }

__all__ = ["get_current_location", "is_gps_connected"]
