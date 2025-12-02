"""
I2C RTC(DS1307/DS3231 호환) helper.
"""

from __future__ import annotations

import os
from datetime import datetime

try:
    import smbus
    HAS_SMBUS = True
except ImportError:
    try:
        import smbus2 as smbus
        HAS_SMBUS = True
    except ImportError:  
        smbus = None
        HAS_SMBUS = False

I2C_BUS_NUM = int(os.environ.get("RTC_I2C_BUS", "1"))
RTC_I2C_ADDR = int(os.environ.get("RTC_I2C_ADDR", "0x68"), 16)


def _bcd_to_dec(value: int) -> int:
    """BCD를 10진수로 변환"""
    return (value // 16) * 10 + (value % 16)


def is_rtc_connected(bus_num: int | None = None, address: int | None = None) -> bool:
    """I2C RTC가 연결되어 있는지 확인"""
    if not HAS_SMBUS:
        return False
    
    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or RTC_I2C_ADDR
        bus.read_byte_data(addr, 0x00)
        bus.close()
        return True
    except Exception:
        return False


def read_rtc(bus_num: int | None = None, address: int | None = None) -> datetime:
    """I2C RTC에서 시간 읽기"""
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 RTC를 읽을 수 없습니다.")

    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or RTC_I2C_ADDR
        data = bus.read_i2c_block_data(addr, 0x00, 7)
        bus.close()
        
        sec = _bcd_to_dec(data[0] & 0x7F)
        minute = _bcd_to_dec(data[1] & 0x7F)
        hour = _bcd_to_dec(data[2] & 0x3F)
        date = _bcd_to_dec(data[4] & 0x3F)
        month = _bcd_to_dec(data[5] & 0x1F)
        year = _bcd_to_dec(data[6]) + 2000
        
        return datetime(year, month, date, hour, minute, sec)
    except Exception as e:
        raise RuntimeError(f"RTC I2C 통신 실패: {e}") from e


def get_current_time(verbose: bool = False) -> tuple[datetime, str]:
    """
    RTC에서 시간 읽기 (하드웨어 RTC 필수)
    Returns: (datetime, "RTC")
    Raises: RuntimeError if RTC is not connected or read fails
    """
    if not is_rtc_connected():
        raise RuntimeError("RTC 모듈이 연결되어 있지 않습니다.")
    
    try:
        device_time = read_rtc()
        if verbose:
            print(f"[RTC] RTC 시간: {device_time}")
        return device_time, "RTC"
    except Exception as e:
        raise RuntimeError(f"RTC 읽기 실패: {e}") from e


def set_rtc(dt: datetime, bus_num: int | None = None, address: int | None = None) -> None:
    """I2C RTC에 시간 설정"""
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 RTC에 쓸 수 없습니다.")
    
    def _dec_to_bcd(value: int) -> int:
        return (value // 10) * 16 + (value % 10)
    
    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or RTC_I2C_ADDR
        
        data = [
            _dec_to_bcd(dt.second),
            _dec_to_bcd(dt.minute),
            _dec_to_bcd(dt.hour),
            _dec_to_bcd(dt.isoweekday()),
            _dec_to_bcd(dt.day),
            _dec_to_bcd(dt.month),
            _dec_to_bcd(dt.year - 2000),
        ]
        
        bus.write_i2c_block_data(addr, 0x00, data)
        bus.close()
        print(f"[RTC] RTC 시간 설정 완료: {dt}")
    except Exception as e:
        raise RuntimeError(f"RTC I2C 쓰기 실패: {e}") from e


__all__ = ["is_rtc_connected", "read_rtc", "get_current_time", "set_rtc"]
