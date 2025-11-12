"""
Sensor collector modules for RTC and fingerprint hardware.
"""

from .rtc import get_current_time, read_rtc_ds3231  # noqa: F401
from .fingerprint import (
    connect_fingerprint_sensor,
    capture_fingerprint_image,
)  # noqa: F401

__all__ = [
    "get_current_time",
    "read_rtc_ds3231",
    "connect_fingerprint_sensor",
    "capture_fingerprint_image",
]
