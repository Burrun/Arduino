"""
I2C RTC(DS1307/DS3231 호환) helper.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional, Tuple

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
_LAST_DETECTED: dict | None = None


def _bcd_to_dec(value: int) -> int:
    """BCD를 10진수로 변환"""
    return (value // 16) * 10 + (value % 16)


def _probe_rtc(
    bus_candidates: Optional[List[int]] = None,
    addr_candidates: Optional[List[int]] = None,
    raise_on_fail: bool = False,
) -> Optional[Tuple[int, int]]:
    """
    Try common I2C bus/address combos to see if an RTC responds.
    Returns (bus, addr) on success, else None.
    """
    if not HAS_SMBUS:
        if raise_on_fail:
            raise RuntimeError("smbus 모듈이 없습니다. `sudo apt install python3-smbus`")
        return None

    buses = []
    if bus_candidates:
        buses.extend(bus_candidates)
    buses.extend([I2C_BUS_NUM, 1, 0])
    buses = [b for idx, b in enumerate(buses) if b is not None and b not in buses[:idx]]

    addrs = []
    if addr_candidates:
        addrs.extend(addr_candidates)
    addrs.extend([RTC_I2C_ADDR, 0x68, 0x51, 0x57])  # DS3231/DS1307/PCF8563/AT24Cxx common addrs
    addrs = [a for idx, a in enumerate(addrs) if a is not None and a not in addrs[:idx]]

    last_err: Optional[BaseException] = None

    for bus_num in buses:
        for addr in addrs:
            try:
                bus = smbus.SMBus(bus_num)
                try:
                    bus.read_byte_data(addr, 0x00)
                finally:
                    bus.close()

                global _LAST_DETECTED
                _LAST_DETECTED = {"bus": bus_num, "addr": addr}
                print(f"[RTC] 응답 확인: bus={bus_num}, addr=0x{addr:02X}")
                return bus_num, addr
            except BaseException as exc:
                last_err = exc
                continue

    if raise_on_fail and last_err:
        raise RuntimeError(f"RTC 응답 없음 (bus {buses}, addr {list(map(hex, addrs))}): {last_err}")
    return None


def is_rtc_connected(bus_num: int | None = None, address: int | None = None) -> bool:
    """I2C RTC가 연결되어 있는지 확인"""
    if bus_num is not None or address is not None:
        return _probe_rtc(
            bus_candidates=[bus_num] if bus_num is not None else None,
            addr_candidates=[address] if address is not None else None,
            raise_on_fail=False,
        ) is not None

    return _probe_rtc(raise_on_fail=False) is not None


def read_rtc(bus_num: int | None = None, address: int | None = None) -> datetime:
    """I2C RTC에서 시간 읽기"""
    probe = _probe_rtc(
        bus_candidates=[bus_num] if bus_num is not None else None,
        addr_candidates=[address] if address is not None else None,
        raise_on_fail=True,
    )

    if probe is None:
        raise RuntimeError("RTC I2C 응답이 없습니다.")

    detected_bus, detected_addr = probe

    try:
        bus = smbus.SMBus(detected_bus)
        addr = detected_addr
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
    
    probe = _probe_rtc(
        bus_candidates=[bus_num] if bus_num is not None else None,
        addr_candidates=[address] if address is not None else None,
        raise_on_fail=True,
    )

    target_bus, target_addr = probe

    try:
        bus = smbus.SMBus(target_bus)
        data = [
            _dec_to_bcd(dt.second),
            _dec_to_bcd(dt.minute),
            _dec_to_bcd(dt.hour),
            _dec_to_bcd(dt.isoweekday()),
            _dec_to_bcd(dt.day),
            _dec_to_bcd(dt.month),
            _dec_to_bcd(dt.year - 2000),
        ]
        bus.write_i2c_block_data(target_addr, 0x00, data)
        bus.close()
        print(f"[RTC] RTC 시간 설정 완료: {dt}")
    except Exception as e:
        raise RuntimeError(f"RTC I2C 쓰기 실패: {e}") from e


__all__ = ["is_rtc_connected", "read_rtc", "get_current_time", "set_rtc"]
