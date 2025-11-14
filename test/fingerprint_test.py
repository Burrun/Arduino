#!/usr/bin/env python3
"""
AS608 지문 센서 진단 스크립트
"""
import serial
from serial.tools import list_ports
import time

def list_available_ports():
    """사용 가능한 시리얼 포트 목록"""
    print("\n=== 사용 가능한 시리얼 포트 ===")
    ports = list_ports.comports()
    if not ports:
        print("감지된 포트 없음")
        return []
    
    for port in ports:
        print(f"- {port.device}: {port.description}")
    return [p.device for p in ports]

def test_port(port, baudrate=57600):
    """특정 포트로 센서 테스트"""
    print(f"\n=== {port} 테스트 (baudrate={baudrate}) ===")
    
    try:
        # 시리얼 포트 열기
        ser = serial.Serial(port, baudrate=baudrate, timeout=2)
        print(f"✓ 포트 열기 성공: {port}")
        
        # 핸드셰이크 패킷 전송 (VfyPwd 명령)
        # 헤더(0xEF01) + 주소(0xFFFFFFFF) + 패키지ID(0x01) + 길이(0x0007) + 명령(0x13) + 비밀번호(0x00000000) + 체크섬
        handshake = bytes([
            0xEF, 0x01,           # 헤더
            0xFF, 0xFF, 0xFF, 0xFF,  # 주소 (기본값)
            0x01,                 # 패키지 식별자
            0x00, 0x07,           # 패킷 길이
            0x13,                 # 명령어 (VfyPwd)
            0x00, 0x00, 0x00, 0x00,  # 비밀번호 (기본값 0)
            0x00, 0x1B            # 체크섬
        ])
        
        ser.write(handshake)
        print(f"✓ 핸드셰이크 패킷 전송: {handshake.hex()}")
        
        # 응답 대기
        time.sleep(0.1)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"✓ 센서 응답 수신: {response.hex()}")
            
            # 응답 분석
            if len(response) >= 12:
                if response[0:2] == bytes([0xEF, 0x01]):
                    confirm_code = response[9]
                    if confirm_code == 0x00:
                        print("✅ 센서 연결 성공!")
                        return True
                    else:
                        print(f"⚠️ 센서가 오류 코드 반환: 0x{confirm_code:02X}")
                else:
                    print("⚠️ 잘못된 헤더")
            else:
                print(f"⚠️ 응답이 너무 짧음 (길이: {len(response)})")
        else:
            print("❌ 센서 응답 없음 (타임아웃)")
        
        ser.close()
        return False
        
    except PermissionError:
        print(f"❌ 권한 오류: sudo 또는 dialout 그룹 추가 필요")
        return False
    except serial.SerialException as e:
        print(f"❌ 시리얼 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False

def main():
    print("=" * 50)
    print("AS608 지문 센서 진단 도구")
    print("=" * 50)
    
    # 포트 목록
    available_ports = list_available_ports()
    
    # 테스트할 포트 목록
    test_ports = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyS0"]
    test_ports.extend([p for p in available_ports if p not in test_ports])
    
    # 각 포트 테스트
    success = False
    for port in test_ports:
        if test_port(port, baudrate=57600):
            success = True
            print(f"\n✅ 작동하는 포트 발견: {port}")
            break
    
    if not success:
        print("\n" + "=" * 50)
        print("❌ 모든 포트에서 센서를 찾을 수 없습니다.")
        print("\n해결 방법:")
        print("1. 배선 확인:")
        print("   - VCC → 3.3V (5V 아님!)")
        print("   - GND → GND")
        print("   - TX(센서) → RX(GPIO 15)")
        print("   - RX(센서) → TX(GPIO 14)")
        print("\n2. UART 설정:")
        print("   sudo raspi-config")
        print("   Interface Options → Serial Port")
        print("   - Login shell: No")
        print("   - Serial port hardware: Yes")
        print("\n3. 권한 설정:")
        print("   sudo usermod -a -G dialout $USER")
        print("   (재로그인 필요)")
        print("\n4. /boot/config.txt 확인:")
        print("   enable_uart=1")
        print("   dtoverlay=disable-bt")
        print("=" * 50)

if __name__ == "__main__":
    main()