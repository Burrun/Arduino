#!/usr/bin/env python3
"""
Simple serial probe for the AS608 fingerprint sensor.
Iterates over common UART ports (or user-provided list), sends the VfyPwd
handshake packet, and reports whether a valid response is received.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import List

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None


DEFAULT_PORTS = ["/dev/ttyS0", "/dev/serial0", "/dev/ttyAMA0", "/dev/ttyUSB0"]
# Header(0xEF01) + addr(FFFFFFFF) + packet id(0x01) + len(0x0007) +
# VfyPwd(0x13) + password(0x00000000) + checksum(0x001B)
DEFAULT_HANDSHAKE_HEX = "ef01ffffffff0100071300000000001b"


def build_port_list(user_ports: List[str] | None) -> List[str]:
    seen = set()
    candidates: List[str] = []
    for port in (user_ports or DEFAULT_PORTS):
        if port and port not in seen:
            candidates.append(port)
            seen.add(port)
    if list_ports:
        for info in list_ports.comports():
            if info.device and info.device not in seen:
                candidates.append(info.device)
                seen.add(info.device)
    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe fingerprint sensor over multiple serial ports.")
    parser.add_argument(
        "--ports",
        help="Comma-separated list of ports to try (defaults to common UART/USB ports).",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=57600,
        help="Baud rate to use (default: 57600).",
    )
    parser.add_argument(
        "--handshake",
        default=DEFAULT_HANDSHAKE_HEX,
        help="Hex string for the handshake packet (default: AS608 VfyPwd).",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=0.2,
        help="Seconds to wait for response after sending handshake.",
    )
    return parser.parse_args()


def main() -> int:
    if serial is None or list_ports is None:
        print("pyserial가 설치되어 있어야 합니다. pip install pyserial", file=sys.stderr)
        return 2

    args = parse_args()
    user_ports = [p.strip() for p in args.ports.split(",")] if args.ports else None
    ports = build_port_list(user_ports)
    handshake = bytes.fromhex(args.handshake)

    print(f"시도할 포트 목록: {', '.join(ports) if ports else '(없음)'}")
    success = False

    for port in ports:
        print(f"\n=== {port} 테스트 (baudrate={args.baud}) ===")
        try:
            ser = serial.Serial(port, baudrate=args.baud, timeout=args.wait)
            print(f"✓ 포트 열기 성공: {port}")
        except Exception as exc:
            print(f"❌ 포트 열기 실패: {exc}")
            continue

        try:
            ser.write(handshake)
            print(f"✓ 핸드셰이크 패킷 전송: {handshake.hex()}")
            time.sleep(args.wait)

            response = ser.read(ser.in_waiting or 64)
            if not response:
                print("❌ 센서 응답 없음 (타임아웃)")
            else:
                print(f"✓ 센서 응답 수신: {response.hex()}")
                if len(response) >= 10 and response[:2] == bytes([0xEF, 0x01]):
                    confirm_code = response[9]
                    if confirm_code == 0x00:
                        print("✅ 센서 연결 성공!")
                        success = True
                    else:
                        print(f"⚠ 센서가 오류 코드 반환: 0x{confirm_code:02X}")
                else:
                    print("⚠ 예상과 다른 응답 포맷")
        except Exception as exc:
            print(f"❌ 통신 중 오류: {exc}")
        finally:
            ser.close()

        if success:
            print(f"\n✅ 작동하는 포트 발견: {port}")
            break

    if not ports:
        print("감지된 포트가 없습니다.")
    elif not success:
        print("\n❌ 모든 포트에서 센서를 찾지 못했습니다.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
