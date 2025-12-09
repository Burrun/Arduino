
#!/usr/bin/env python3
"""
센서 모듈 종합 진단 스크립트
RTC, Fingerprint, Camera, GPS 센서를 상세하게 테스트합니다.
"""

from __future__ import annotations

import argparse
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# Serial Port Detection
# ============================================================

def list_all_serial_ports() -> List[Dict]:
    """모든 시리얼 포트를 상세하게 스캔합니다."""
    ports_info = []
    
    try:
        from serial.tools import list_ports
        for port in list_ports.comports():
            ports_info.append({
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "vid": port.vid,
                "pid": port.pid,
                "manufacturer": port.manufacturer,
            })
    except ImportError:
        print("⚠ pyserial 패키지가 설치되지 않았습니다.")
    
    # 추가로 /dev 디렉토리 스캔
    dev_ports = []
    for pattern in ["/dev/ttyS*", "/dev/ttyAMA*", "/dev/ttyUSB*", "/dev/serial*"]:
        import glob
        dev_ports.extend(glob.glob(pattern))
    
    for dev in dev_ports:
        if not any(p["device"] == dev for p in ports_info):
            ports_info.append({
                "device": dev,
                "description": "(직접 감지됨)",
                "hwid": None,
                "vid": None,
                "pid": None,
                "manufacturer": None,
            })
    
    return ports_info


def test_serial_port(port: str, baudrate: int = 57600, timeout: float = 1.0) -> Tuple[bool, str]:
    """시리얼 포트 열기 테스트"""
    try:
        import serial
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        ser.close()
        return True, "포트 열기 성공"
    except PermissionError:
        return False, "권한 오류 (sudo 또는 dialout 그룹 필요)"
    except FileNotFoundError:
        return False, "포트 없음"
    except Exception as e:
        return False, str(e)


# ============================================================
# RTC 테스트
# ============================================================

def test_rtc_detailed() -> Dict:
    """RTC 모듈 상세 테스트"""
    result = {
        "module": "RTC",
        "tests": [],
        "success": False,
    }
    
    print("\n" + "=" * 60)
    print("  RTC (Real-Time Clock) 테스트")
    print("=" * 60)
    
    # 1. I2C 버스 확인
    print("\n[1] I2C 버스 확인")
    print("-" * 40)
    i2c_devices = []
    try:
        import subprocess
        proc = subprocess.run(["i2cdetect", "-y", "1"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            print("✓ I2C 버스 1 사용 가능")
            # DS3231 RTC는 보통 0x68 주소
            if "68" in proc.stdout:
                print("✓ RTC (0x68) 감지됨")
                i2c_devices.append("0x68")
            else:
                print("⚠ RTC 주소(0x68)를 찾을 수 없음")
            result["tests"].append({"name": "I2C 버스", "passed": True})
        else:
            print(f"✗ I2C 감지 실패: {proc.stderr}")
            result["tests"].append({"name": "I2C 버스", "passed": False})
    except FileNotFoundError:
        print("⚠ i2cdetect 명령어 없음 (sudo apt install i2c-tools)")
        result["tests"].append({"name": "I2C 버스", "passed": None, "reason": "i2cdetect 없음"})
    except Exception as e:
        print(f"✗ I2C 확인 실패: {e}")
        result["tests"].append({"name": "I2C 버스", "passed": False})
    
    # 2. RTC 모듈 연결 테스트
    print("\n[2] RTC 모듈 연결")
    print("-" * 40)
    try:
        from modules.sensors import rtc
        
        is_connected = rtc.is_rtc_connected()
        if is_connected:
            print("✓ RTC 하드웨어 연결됨")
            result["tests"].append({"name": "RTC 연결", "passed": True})
        else:
            print("✗ RTC 하드웨어 연결 안됨")
            result["tests"].append({"name": "RTC 연결", "passed": False})
    except Exception as e:
        print(f"✗ RTC 모듈 로드 실패: {e}")
        result["tests"].append({"name": "RTC 연결", "passed": False})
    
    # 3. 시간 읽기 테스트
    print("\n[3] 시간 읽기 테스트")
    print("-" * 40)
    try:
        from modules.sensors import rtc
        timestamp, source = rtc.get_current_time(verbose=False)
        print(f"✓ 현재 시간: {timestamp.isoformat()}")
        print(f"  소스: {source}")
        result["tests"].append({"name": "시간 읽기", "passed": True})
        result["timestamp"] = timestamp.isoformat()
        result["source"] = source
    except Exception as e:
        print(f"✗ 시간 읽기 실패: {e}")
        result["tests"].append({"name": "시간 읽기", "passed": False})
    
    result["success"] = all(t.get("passed", False) for t in result["tests"] if t.get("passed") is not None)
    return result


# ============================================================
# Fingerprint 테스트
# ============================================================

def test_fingerprint_detailed() -> Dict:
    """지문 센서 상세 테스트"""
    result = {
        "module": "Fingerprint",
        "tests": [],
        "success": False,
    }
    
    print("\n" + "=" * 60)
    print("  Fingerprint (AS608) 테스트")
    print("=" * 60)
    
    # 1. 의존성 확인
    print("\n[1] 의존성 패키지 확인")
    print("-" * 40)
    deps_ok = True
    try:
        import serial
        print("✓ pyserial 설치됨")
    except ImportError:
        print("✗ pyserial 미설치")
        deps_ok = False
    
    try:
        import adafruit_fingerprint
        print("✓ adafruit-circuitpython-fingerprint 설치됨")
    except ImportError:
        print("✗ adafruit-circuitpython-fingerprint 미설치")
        deps_ok = False
    
    result["tests"].append({"name": "의존성", "passed": deps_ok})
    
    if not deps_ok:
        print("\n⚠ 필수 패키지를 설치하세요:")
        print("  pip install pyserial adafruit-circuitpython-fingerprint")
        return result
    
    # 2. 시리얼 포트 스캔
    print("\n[2] 시리얼 포트 스캔")
    print("-" * 40)
    ports = list_all_serial_ports()
    if ports:
        print(f"✓ 감지된 포트 {len(ports)}개:")
        for p in ports:
            print(f"  - {p['device']}: {p['description']}")
        result["tests"].append({"name": "포트 스캔", "passed": True})
    else:
        print("✗ 시리얼 포트 없음")
        result["tests"].append({"name": "포트 스캔", "passed": False})
    
    # 3. 각 포트에서 센서 연결 시도
    print("\n[3] 센서 연결 테스트")
    print("-" * 40)
    
    test_ports = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyS0"]
    test_ports.extend([p["device"] for p in ports if p["device"] not in test_ports])
    
    connected = False
    for port in test_ports:
        success, msg = test_serial_port(port, baudrate=57600)
        status = "✓" if success else "✗"
        print(f"  {status} {port}: {msg}")
        
        if success:
            # 실제 센서 통신 테스트 (직접 패킷)
            try:
                import serial
                ser = serial.Serial(port, baudrate=57600, timeout=2)
                
                # VfyPwd 핸드셰이크 패킷
                handshake = bytes([
                    0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF,
                    0x01, 0x00, 0x07, 0x13,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x1B
                ])
                ser.write(handshake)
                time.sleep(0.2)
                
                if ser.in_waiting > 0:
                    response = ser.read(ser.in_waiting)
                    if len(response) >= 12 and response[0:2] == bytes([0xEF, 0x01]):
                        print(f"    ✓ 센서 응답 수신! (포트: {port})")
                        connected = True
                        result["working_port"] = port
                ser.close()
            except Exception as e:
                print(f"    ✗ 통신 실패: {e}")
    
    result["tests"].append({"name": "센서 연결", "passed": connected})
    
    # 4. adafruit 라이브러리 연결 테스트
    if connected:
        print("\n[4] Adafruit 라이브러리 연결")
        print("-" * 40)
        try:
            from modules.sensors import fingerprint
            finger = fingerprint.connect_fingerprint_sensor()
            template_count = finger.template_count
            print(f"✓ 라이브러리 연결 성공")
            print(f"  등록된 지문: {template_count}개")
            result["tests"].append({"name": "라이브러리 연결", "passed": True})
            result["template_count"] = template_count
        except Exception as e:
            print(f"✗ 라이브러리 연결 실패: {e}")
            result["tests"].append({"name": "라이브러리 연결", "passed": False})
    
    result["success"] = all(t.get("passed", False) for t in result["tests"] if t.get("passed") is not None)
    return result


# ============================================================
# Camera 테스트
# ============================================================

def test_camera_detailed(esp32_url: Optional[str] = None) -> Dict:
    """카메라 (ESP32-CAM) 상세 테스트"""
    result = {
        "module": "Camera",
        "tests": [],
        "success": False,
    }
    
    print("\n" + "=" * 60)
    print("  Camera (ESP32-CAM) 테스트")
    print("=" * 60)
    
    from modules.sensors import camera
    
    # 1. 네트워크 연결 확인
    print("\n[1] ESP32-CAM 네트워크 연결")
    print("-" * 40)
    
    base_url = esp32_url or camera.DEFAULT_ESP32_URL
    print(f"  대상 URL: {base_url}")
    
    # Ping 테스트 (간단한 HTTP 요청)
    try:
        import requests
        response = requests.get(f"{base_url}/", timeout=3)
        print(f"✓ ESP32-CAM 응답: {response.status_code}")
        result["tests"].append({"name": "네트워크 연결", "passed": True})
    except requests.exceptions.ConnectionError:
        print("✗ 연결 실패 (ESP32-CAM이 켜져 있고 같은 네트워크인지 확인)")
        result["tests"].append({"name": "네트워크 연결", "passed": False})
        return result
    except Exception as e:
        print(f"✗ 연결 오류: {e}")
        result["tests"].append({"name": "네트워크 연결", "passed": False})
        return result
    
    # 2. 카메라 상태 확인
    print("\n[2] 카메라 상태 확인")
    print("-" * 40)
    try:
        is_connected = camera.is_camera_connected(base_url=base_url)
        if is_connected:
            print("✓ 카메라 모듈 정상")
            result["tests"].append({"name": "카메라 상태", "passed": True})
        else:
            print("✗ 카메라 모듈 오류")
            result["tests"].append({"name": "카메라 상태", "passed": False})
    except Exception as e:
        print(f"✗ 상태 확인 실패: {e}")
        result["tests"].append({"name": "카메라 상태", "passed": False})
    
    # 3. 이미지 캡처 테스트
    print("\n[3] 이미지 캡처 테스트")
    print("-" * 40)
    try:
        test_path = "/tmp/camera_test.jpg"
        saved_path = camera.capture_image(save_path=test_path, timeout=10, base_url=base_url)
        
        if os.path.exists(saved_path):
            size = os.path.getsize(saved_path)
            print(f"✓ 이미지 캡처 성공")
            print(f"  파일: {saved_path}")
            print(f"  크기: {size:,} bytes")
            result["tests"].append({"name": "이미지 캡처", "passed": True})
            result["image_size"] = size
            os.remove(saved_path)
        else:
            print("✗ 이미지 파일 생성 실패")
            result["tests"].append({"name": "이미지 캡처", "passed": False})
    except Exception as e:
        print(f"✗ 캡처 실패: {e}")
        result["tests"].append({"name": "이미지 캡처", "passed": False})
    
    result["success"] = all(t.get("passed", False) for t in result["tests"])
    return result


# ============================================================
# GPS 테스트
# ============================================================

def test_gps_detailed(esp32_url: Optional[str] = None) -> Dict:
    """GPS 모듈 상세 테스트"""
    result = {
        "module": "GPS",
        "tests": [],
        "success": False,
    }
    
    print("\n" + "=" * 60)
    print("  GPS 테스트")
    print("=" * 60)
    
    from modules.sensors import gps
    
    # 1. GPS 모듈 연결 확인
    print("\n[1] GPS 모듈 연결 확인")
    print("-" * 40)
    
    base_url = esp32_url
    try:
        is_connected = gps.is_gps_connected(base_url=base_url)
        if is_connected:
            print("✓ GPS 모듈 연결됨")
            result["tests"].append({"name": "GPS 연결", "passed": True})
        else:
            print("⚠ GPS 모듈 연결 안됨 또는 위성 미수신")
            result["tests"].append({"name": "GPS 연결", "passed": False})
    except Exception as e:
        print(f"✗ GPS 연결 확인 실패: {e}")
        result["tests"].append({"name": "GPS 연결", "passed": False})
    
    # 2. 위치 데이터 획득
    print("\n[2] 위치 데이터 획득")
    print("-" * 40)
    try:
        location = gps.get_current_location(timeout=15, base_url=base_url)
        lat = location.get("latitude", 0)
        lon = location.get("longitude", 0)
        
        if lat != 0 or lon != 0:
            print(f"✓ 위치 획득 성공")
            print(f"  위도: {lat}")
            print(f"  경도: {lon}")
            result["tests"].append({"name": "위치 획득", "passed": True})
            result["latitude"] = lat
            result["longitude"] = lon
        else:
            print("⚠ 위치가 0,0 (GPS 신호 없거나 실외로 이동 필요)")
            result["tests"].append({"name": "위치 획득", "passed": False})
    except Exception as e:
        print(f"✗ 위치 획득 실패: {e}")
        result["tests"].append({"name": "위치 획득", "passed": False})
    
    result["success"] = all(t.get("passed", False) for t in result["tests"])
    return result


# ============================================================
# 종합 테스트
# ============================================================

def run_all_tests(esp32_url: Optional[str] = None, skip_interactive: bool = False) -> Dict:
    """모든 센서 종합 테스트"""
    print("=" * 60)
    print("  센서 모듈 종합 진단")
    print("  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 시리얼 포트 전체 스캔
    print("\n[시리얼 포트 전체 스캔]")
    print("-" * 40)
    ports = list_all_serial_ports()
    if ports:
        for p in ports:
            print(f"  • {p['device']}: {p['description']}")
    else:
        print("  (감지된 포트 없음)")
    
    results = {}
    
    # RTC 테스트
    results["rtc"] = test_rtc_detailed()
    
    # Fingerprint 테스트
    results["fingerprint"] = test_fingerprint_detailed()
    
    # Camera 테스트
    results["camera"] = test_camera_detailed(esp32_url)
    
    # GPS 테스트
    results["gps"] = test_gps_detailed(esp32_url)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("  테스트 결과 요약")
    print("=" * 60)
    
    for module, data in results.items():
        status = "✓ 통과" if data["success"] else "✗ 실패"
        print(f"  {module.upper():12} {status}")
        for test in data.get("tests", []):
            t_status = "✓" if test.get("passed") else ("?" if test.get("passed") is None else "✗")
            print(f"    {t_status} {test['name']}")
    
    print()
    all_passed = all(r["success"] for r in results.values())
    if all_passed:
        print("✅ 모든 센서가 정상 작동합니다!")
    else:
        failed = [k for k, v in results.items() if not v["success"]]
        print(f"⚠ 일부 센서에 문제가 있습니다: {', '.join(failed)}")
    
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="센서 모듈 종합 진단 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python test.py                  # 모든 센서 테스트
  python test.py rtc              # RTC만 테스트
  python test.py fingerprint      # 지문 센서만 테스트
  python test.py camera           # 카메라만 테스트
  python test.py gps              # GPS만 테스트
  python test.py --esp32-url http://192.168.1.100  # ESP32 주소 지정
        """
    )
    parser.add_argument(
        "module",
        nargs="?",
        choices=["all", "rtc", "fingerprint", "camera", "gps"],
        default="all",
        help="테스트할 모듈 (기본: all)",
    )
    parser.add_argument(
        "--esp32-url",
        default=None,
        help="ESP32-CAM URL (기본: http://192.168.4.1)",
    )
    parser.add_argument(
        "--skip-interactive",
        action="store_true",
        help="대화형 테스트 건너뛰기",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    
    try:
        if args.module == "all":
            results = run_all_tests(args.esp32_url, args.skip_interactive)
            return 0 if all(r["success"] for r in results.values()) else 1
        elif args.module == "rtc":
            result = test_rtc_detailed()
        elif args.module == "fingerprint":
            result = test_fingerprint_detailed()
        elif args.module == "camera":
            result = test_camera_detailed(args.esp32_url)
        elif args.module == "gps":
            result = test_gps_detailed(args.esp32_url)
        else:
            print(f"알 수 없는 모듈: {args.module}")
            return 1
        
        return 0 if result["success"] else 1
        
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
        return 130
    except Exception as e:
        print(f"\n오류 발생: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

