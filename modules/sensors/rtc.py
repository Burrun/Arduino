"""
I2C RTC(DS1307/DS3231 호환) helper.

하드웨어 접근을 분리해서 다른 모듈에서 `get_current_time`만 가져다
쓸 수 있게 해 주는 헬퍼입니다.
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

# DS3231 기본 I2C 주소는 0x68
RTC_I2C_ADDR = int(os.environ.get("RTC_I2C_ADDR", os.environ.get("DS3231_ADDR", "0x68")), 16)


def _bcd_to_dec(value: int) -> int:
    """BCD를 10진수로 변환"""
    return (value // 16) * 10 + (value % 16)


def is_rtc_connected(bus_num: int | None = None, address: int | None = None) -> bool:
    """
    I2C RTC(DS1307/DS3231)가 실제로 연결되어 있는지 확인합니다.
    
    Returns:
        bool: RTC 모듈이 연결되어 있으면 True
    """
    if not HAS_SMBUS:
        return False
    
    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or RTC_I2C_ADDR
        # 간단히 1바이트 읽기 시도 (seconds register)
        bus.read_byte_data(addr, 0x00)
        bus.close()
        return True
    except Exception:
        return False


def read_rtc(bus_num: int | None = None, address: int | None = None) -> datetime:
    """
    I2C RTC(DS1307/DS3231 호환)에서 레지스터(0x00~0x06)를 읽어 datetime으로 반환.
    
    Raises:
        RuntimeError: smbus 미존재 또는 I2C 접근 실패 시
    """
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 RTC를 읽을 수 없습니다.")

    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or RTC_I2C_ADDR
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
        raise RuntimeError(f"RTC I2C 통신 실패: {e}") from e


def get_current_time(
    fallback_to_system: bool = True,
    verbose: bool = True,
    strict: bool = False
) -> tuple[datetime, str]:
    """
    먼저 I2C RTC에서 읽기를 시도하고, 필요하면 시스템 시간으로 폴백.
    
    Args:
        fallback_to_system: True이면 RTC 실패 시 시스템 시간 사용
        verbose: True이면 상태 메시지 출력
        strict: True이면 RTC 연결 실패 시 경고 메시지 출력
    
    Returns:
        tuple(datetime, source_string): (시간, "RTC" 또는 "SYSTEM")
    
    Raises:
        RuntimeError: fallback_to_system=False일 때 RTC 읽기 실패 시
    """
    # 먼저 연결 상태 확인
    if not is_rtc_connected():
        error_msg = "[RTC] I2C RTC 모듈이 연결되어 있지 않습니다 (addr=0x68)"
        
        if verbose or strict:
            print(error_msg)
            if strict:
                print("[경고] RTC 모듈 연결 및 I2C 설정을 확인하세요!")
                print("[경고] - I2C가 활성화되어 있는지 확인 (raspi-config)")
                print("[경고] - RTC 배선 확인 (SDA, SCL, VCC, GND)")
                print(f"[경고] - I2C 주소 확인: i2cdetect -y {I2C_BUS_NUM}")
        
        if not fallback_to_system:
            raise RuntimeError(f"{error_msg}. I2C 통신 불가.")
        
        if verbose:
            print("[RTC] 시스템 시간을 사용합니다")
        
        return datetime.now(), "SYSTEM"
    
    # RTC에서 시간 읽기 시도
    try:
        device_time = read_rtc()
        if verbose:
            print(f"[RTC] I2C RTC에서 시간 읽기 성공: {device_time}")
        return device_time, "RTC"
    
    except Exception as e:
        error_msg = f"[RTC] RTC 읽기 실패: {type(e).__name__}: {e}"
        
        if verbose or strict:
            print(error_msg)
        
        if not fallback_to_system:
            raise RuntimeError(error_msg) from e
        
        if verbose:
            print("[RTC] 시스템 시간으로 폴백합니다")
        
        return datetime.now(), "SYSTEM"


def set_rtc(dt: datetime, bus_num: int | None = None, address: int | None = None) -> None:
    """
    I2C RTC(DS1307/DS3231 호환)에 시간을 설정합니다.
    
    Args:
        dt: 설정할 datetime 객체
        bus_num: I2C 버스 번호
        address: RTC I2C 주소
    
    Raises:
        RuntimeError: smbus 없거나 I2C 통신 실패 시
    """
    if not HAS_SMBUS:
        raise RuntimeError("smbus 모듈이 없어 RTC에 쓸 수 없습니다.")
    
    def _dec_to_bcd(value: int) -> int:
        """10진수를 BCD로 변환"""
        return (value // 10) * 16 + (value % 10)
    
    try:
        bus = smbus.SMBus(bus_num or I2C_BUS_NUM)
        addr = address or RTC_I2C_ADDR
        
        data = [
            _dec_to_bcd(dt.second),
            _dec_to_bcd(dt.minute),
            _dec_to_bcd(dt.hour),          # 24h mode
            _dec_to_bcd(dt.isoweekday()),  # day of week (1=Monday)
            _dec_to_bcd(dt.day),
            _dec_to_bcd(dt.month),
            _dec_to_bcd(dt.year - 2000),
        ]
        
        bus.write_i2c_block_data(addr, 0x00, data)
        bus.close()
        print(f"[RTC] RTC 시간 설정 완료: {dt}")
    
    except Exception as e:
        raise RuntimeError(f"RTC I2C 쓰기 실패: {e}") from e


# ---- 기존 DS3231 전용 이름과의 호환용 래퍼 ----

def read_rtc_ds3231(bus_num: int | None = None, address: int | None = None) -> datetime:
    return read_rtc(bus_num=bus_num, address=address)


def set_rtc_ds3231(dt: datetime, bus_num: int | None = None, address: int | None = None) -> None:
    return set_rtc(dt=dt, bus_num=bus_num, address=address)


__all__ = [
    "is_rtc_connected",
    "read_rtc",
    "set_rtc",
    "get_current_time",
    # 과거 이름
    "read_rtc_ds3231",
    "set_rtc_ds3231",
]


# 사용 예시
if __name__ == "__main__":
    print("=== I2C RTC(DS1307/DS3231) 테스트 ===\n")
    
    # 1. 연결 확인
    print("1. RTC 모듈 연결 확인:")
    if is_rtc_connected():
        print("   ✓ RTC 모듈 연결됨\n")
    else:
        print("   ✗ RTC 모듈 연결 안 됨\n")
    
    # 2. 시간 읽기 (폴백 허용)
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
    #     set_rtc(new_time)
    #     print(f"   ✓ 시간 설정 완료: {new_time}\n")
    # except Exception as e:
    #     print(f"   ✗ 설정 실패: {e}\n")
