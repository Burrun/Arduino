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
    """BCD를 10진수로 변환"""
    return (value // 16) * 10 + (value % 16)


def is_rtc_connected(bus_num: int | None = None, address: int | None = None) -> bool:
    """
    DS3231이 실제로 연결되어 있는지 확인합니다.
    
    Returns:
        bool: RTC 모듈이 연결되어 있으면 True
    """
    if not HAS_SMBUS:
        return False
    
    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or DS3231_ADDR
        # 간단히 1바이트 읽기 시도 (seconds register)
        bus.read_byte_data(addr, 0x00)
        bus.close()
        return True
    except Exception:
        return False


def read_rtc_ds3231(bus_num: int | None = None, address: int | None = None) -> datetime:
    """
    Read DS3231 registers (0x00~0x06) and return datetime.
    Raises RuntimeError if smbus is unavailable or I2C access fails.
    """
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 DS3231을 읽을 수 없습니다.")

    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or DS3231_ADDR
        data = bus.read_i2c_block_data(addr, 0x00, 7)
        bus.close()
        
        sec = _bcd_to_dec(data[0] & 0x7F)
        minute = _bcd_to_dec(data[1] & 0x7F)
        hour = _bcd_to_dec(data[2] & 0x3F)  # 24h mode
        date = _bcd_to_dec(data[4] & 0x3F)
        month = _bcd_to_dec(data[5] & 0x1F)
        year = _bcd_to_dec(data[6]) + 2000
        
        return datetime(year, month, date, hour, minute, sec)
    except Exception as e:
        raise RuntimeError(f"DS3231 I2C 통신 실패: {e}") from e


def get_current_time(
    fallback_to_system: bool = True,
    verbose: bool = True,
    strict: bool = False
) -> tuple[datetime, str]:
    """
    Try DS3231 first; optionally fallback to system clock.
    
    Args:
        fallback_to_system: True이면 RTC 실패 시 시스템 시간 사용
        verbose: True이면 상태 메시지 출력
        strict: True이면 RTC 연결 실패 시 경고 메시지 출력
    
    Returns:
        tuple(datetime, source_string): (시간, "DS3231" 또는 "SYSTEM")
    
    Raises:
        RuntimeError: fallback_to_system=False일 때 RTC 읽기 실패 시
    """
    # 먼저 연결 상태 확인
    if not is_rtc_connected():
        error_msg = "[RTC] DS3231 모듈이 연결되어 있지 않습니다"
        
        if verbose or strict:
            print(error_msg)
            if strict:
                print("[경고] RTC 모듈 연결 및 I2C 설정을 확인하세요!")
                print("[경고] - I2C가 활성화되어 있는지 확인 (raspi-config)")
                print("[경고] - DS3231 배선 확인 (SDA, SCL, VCC, GND)")
                print(f"[경고] - I2C 주소 확인: i2cdetect -y {I2C_BUS_NUM}")
        
        if not fallback_to_system:
            raise RuntimeError(f"{error_msg}. I2C 통신 불가.")
        
        if verbose:
            print("[RTC] 시스템 시간을 사용합니다")
        
        return datetime.now(), "SYSTEM"
    
    # RTC에서 시간 읽기 시도
    try:
        device_time = read_rtc_ds3231()
        if verbose:
            print(f"[RTC] DS3231에서 시간 읽기 성공: {device_time}")
        return device_time, "DS3231"
    
    except Exception as e:
        error_msg = f"[RTC] DS3231 읽기 실패: {type(e).__name__}: {e}"
        
        if verbose or strict:
            print(error_msg)
        
        if not fallback_to_system:
            raise RuntimeError(error_msg) from e
        
        if verbose:
            print("[RTC] 시스템 시간으로 폴백합니다")
        
        return datetime.now(), "SYSTEM"


def set_rtc_ds3231(dt: datetime, bus_num: int | None = None, address: int | None = None) -> None:
    """
    DS3231에 시간을 설정합니다.
    
    Args:
        dt: 설정할 datetime 객체
        bus_num: I2C 버스 번호
        address: DS3231 I2C 주소
    
    Raises:
        RuntimeError: smbus 없거나 I2C 통신 실패 시
    """
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 DS3231에 쓸 수 없습니다.")
    
    def _dec_to_bcd(value: int) -> int:
        """10진수를 BCD로 변환"""
        return (value // 10) * 16 + (value % 10)
    
    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or DS3231_ADDR
        
        data = [
            _dec_to_bcd(dt.second),
            _dec_to_bcd(dt.minute),
            _dec_to_bcd(dt.hour),      # 24h mode
            _dec_to_bcd(dt.isoweekday()),  # day of week (1=Monday)
            _dec_to_bcd(dt.day),
            _dec_to_bcd(dt.month),
            _dec_to_bcd(dt.year - 2000),
        ]
        
        bus.write_i2c_block_data(addr, 0x00, data)
        bus.close()
        print(f"[RTC] DS3231 시간 설정 완료: {dt}")
    
    except Exception as e:
        raise RuntimeError(f"DS3231 I2C 쓰기 실패: {e}") from e


__all__ = [
    "is_rtc_connected",
    "read_rtc_ds3231",
    "get_current_time",
    "set_rtc_ds3231",
]


# 사용 예시
if __name__ == "__main__":
    print("=== RTC DS3231 테스트 ===\n")
    
    # 1. 연결 확인
    print("1. RTC 모듈 연결 확인:")
    if is_rtc_connected():
        print("   ✓ DS3231 모듈 연결됨\n")
    else:
        print("   ✗ DS3231 모듈 연결 안 됨\n")
    
    # 2. 시간 읽기 (verbose 모드)
    print("2. 시간 읽기 (폴백 허용):")
    current_time, source = get_current_time(verbose=True)
    print(f"   시간: {current_time}")
    print(f"   소스: {source}\n")
    
    # 3. 엄격 모드 (RTC 필수)
    print("3. 엄격 모드 테스트:")
    try:
        current_time, source = get_current_time(fallback_to_system=False, verbose=True)
        print(f"   ✓ RTC 시간: {current_time}\n")
    except Exception as e:
        print(f"   ✗ 에러: {e}\n")
    
    # 4. 시간 설정 예시 (주석 처리)
    # print("4. RTC 시간 설정:")
    # new_time = datetime(2025, 11, 15, 14, 30, 0)
    # try:
    #     set_rtc_ds3231(new_time)
    #     print(f"   ✓ 시간 설정 완료: {new_time}\n")
    # except Exception as e:
    #     print(f"   ✗ 설정 실패: {e}\n")