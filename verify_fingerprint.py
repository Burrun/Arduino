#!/usr/bin/env python3
"""
지문 센서 모듈 검증 스크립트
AS608 지문 센서의 연결 상태와 기본 기능을 테스트합니다.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.sensors import fingerprint


def test_dependencies():
    """의존성 패키지 확인"""
    print("\n[1] 의존성 패키지 확인")
    print("-" * 40)
    
    if fingerprint.HAS_FINGERPRINT_DEPS:
        print("✓ pyserial: 설치됨")
        print("✓ adafruit-circuitpython-fingerprint: 설치됨")
        return True
    else:
        print("✗ 필수 패키지가 설치되지 않았습니다.")
        print("  설치 명령어:")
        print("  pip install pyserial adafruit-circuitpython-fingerprint")
        return False


def test_serial_ports():
    """사용 가능한 시리얼 포트 확인"""
    print("\n[2] 시리얼 포트 확인")
    print("-" * 40)
    
    if not fingerprint.HAS_FINGERPRINT_DEPS:
        print("✗ 패키지 미설치로 건너뜀")
        return False
    
    try:
        from serial.tools import list_ports
        ports = list(list_ports.comports())
        
        if ports:
            print(f"✓ 감지된 포트 {len(ports)}개:")
            for port in ports:
                print(f"  - {port.device}: {port.description}")
        else:
            print("⚠ 감지된 시리얼 포트 없음")
            print("  일반적인 포트:")
            print("  - /dev/serial0 (라즈베리파이 기본)")
            print("  - /dev/ttyAMA0 (UART)")
            print("  - /dev/ttyUSB0 (USB-시리얼)")
        
        print(f"\n  설정된 포트: {fingerprint.UART_PORT}")
        print(f"  설정된 보드레이트: {fingerprint.UART_BAUD}")
        return True
    except Exception as e:
        print(f"✗ 포트 확인 실패: {e}")
        return False


def test_sensor_connection():
    """지문 센서 연결 테스트"""
    print("\n[3] 지문 센서 연결 테스트")
    print("-" * 40)
    
    if not fingerprint.HAS_FINGERPRINT_DEPS:
        print("✗ 패키지 미설치로 건너뜀")
        return False
    
    try:
        print(f"→ {fingerprint.UART_PORT} 포트로 연결 시도 중...")
        finger = fingerprint.connect_fingerprint_sensor()
        print("✓ 지문 센서 연결 성공!")
        
        # 추가 정보 출력
        try:
            template_count = finger.template_count
            print(f"  등록된 지문 수: {template_count}")
        except:
            pass
        
        return finger
    except RuntimeError as e:
        print(f"✗ 연결 실패: {e}")
        return None
    except Exception as e:
        print(f"✗ 예외 발생: {type(e).__name__}: {e}")
        return None


def test_image_capture(finger):
    """지문 이미지 캡처 테스트 (선택적)"""
    print("\n[4] 지문 이미지 캡처 테스트")
    print("-" * 40)
    
    if finger is None:
        print("✗ 센서 연결 실패로 건너뜀")
        return False
    
    try:
        response = input("지문 이미지 캡처를 테스트하시겠습니까? (y/N): ").strip().lower()
        if response != 'y':
            print("→ 건너뜀")
            return True
        
        print("\n→ 손가락을 센서에 올려주세요...")
        test_path = "/tmp/fingerprint_test.pgm"
        saved_path = fingerprint.capture_fingerprint_image(
            finger,
            save_path=test_path,
            timeout_sec=10
        )
        
        # 파일 확인
        if os.path.exists(saved_path):
            file_size = os.path.getsize(saved_path)
            print(f"✓ 이미지 캡처 성공!")
            print(f"  저장 경로: {saved_path}")
            print(f"  파일 크기: {file_size:,} bytes")
            
            # 테스트 파일 정리
            os.remove(saved_path)
            print("  (테스트 파일 삭제됨)")
            return True
        else:
            print("✗ 이미지 파일이 생성되지 않았습니다")
            return False
            
    except TimeoutError:
        print("✗ 시간 초과: 10초 내에 손가락이 감지되지 않았습니다")
        return False
    except Exception as e:
        print(f"✗ 캡처 실패: {e}")
        return False


def main():
    print("=" * 50)
    print("  지문 센서 모듈 검증 (AS608)")
    print("=" * 50)
    
    results = {
        "dependencies": test_dependencies(),
        "serial_ports": test_serial_ports(),
    }
    
    finger = test_sensor_connection()
    results["connection"] = finger is not None
    
    if finger:
        results["capture"] = test_image_capture(finger)
    else:
        results["capture"] = None
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("  검증 결과 요약")
    print("=" * 50)
    
    for test_name, passed in results.items():
        if passed is None:
            status = "⏭ 건너뜀"
        elif passed:
            status = "✓ 통과"
        else:
            status = "✗ 실패"
        print(f"  {test_name}: {status}")
    
    # 전체 결과
    all_passed = all(v is True or v is None for v in results.values())
    critical_passed = results["dependencies"] and results["connection"]
    
    print()
    if critical_passed:
        print("✓ 지문 센서가 정상적으로 작동합니다!")
        return 0
    else:
        print("✗ 일부 테스트가 실패했습니다. 위의 오류 메시지를 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
