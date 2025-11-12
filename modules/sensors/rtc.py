"""
RTC(DS3231) sensor helper.

Separates hardware access so that other modules (e.g. module.py) can import
`get_current_time` without duplicating setup code.
"""

from __future__ import annotations

import os
from datetime import datetime

try:
    import smbus

    HAS_SMBUS = True
except Exception:  # pragma: no cover - defensive on headless dev hosts
    smbus = None
    HAS_SMBUS = False

I2C_BUS_NUM = int(os.environ.get("RTC_I2C_BUS", "1"))
DS3231_ADDR = int(os.environ.get("DS3231_ADDR", "0x68"), 16)


def _bcd_to_dec(value: int) -> int:
    return (value // 16) * 10 + (value % 16)


def read_rtc_ds3231(bus_num: int | None = None, address: int | None = None) -> datetime:
    """
    Read DS3231 registers (0x00~0x06) and return datetime.
    Raises RuntimeError if smbus is unavailable or I2C access fails.
    """
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 DS3231을 읽을 수 없습니다.")

    bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
    addr = address or DS3231_ADDR
    data = bus.read_i2c_block_data(addr, 0x00, 7)
    sec = _bcd_to_dec(data[0] & 0x7F)
    minute = _bcd_to_dec(data[1] & 0x7F)
    hour = _bcd_to_dec(data[2] & 0x3F)  # 24h mode
    date = _bcd_to_dec(data[4] & 0x3F)
    month = _bcd_to_dec(data[5] & 0x1F)
    year = _bcd_to_dec(data[6]) + 2000
    return datetime(year, month, date, hour, minute, sec)


def get_current_time(fallback_to_system: bool = True):
    """
    Try DS3231 first; optionally fallback to system clock.
    Returns tuple(datetime, source_string).
    """
    try:
        device_time = read_rtc_ds3231()
        return device_time, "DS3231"
    except Exception:
        if not fallback_to_system:
            raise
        return datetime.now(), "SYSTEM"


__all__ = ["read_rtc_ds3231", "get_current_time"]
