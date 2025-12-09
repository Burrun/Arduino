#!/usr/bin/env python3
"""
AuthBox API Integration Test Script

Tests the full authentication flow against the AuthBox server.
Supports both direct server testing and proxy mode (via local server.py).

Usage:
    python test_authbox_api.py --direct    # Direct to AuthBox server
    python test_authbox_api.py --proxy     # Via local proxy (default)
    python test_authbox_api.py --help      # Show options
"""

import argparse
import requests
import base64
import sys
import os
from pathlib import Path

# Configuration
AUTHBOX_SERVER_URL = "http://35.175.180.106:8080"
LOCAL_PROXY_URL = "http://localhost:5000"
SAMPLE_DIR = Path(__file__).parent / "sample"

# Test credentials (from API specification)
TEST_USER_ID = "0001"
TEST_PASSWORD = "1111"
TEST_SENDER_EMAIL = "b354b.36750@gmail.com"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_step(step_num: str, description: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {step_num}]{Colors.RESET} {description}")


def print_success(message: str):
    print(f"  {Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    print(f"  {Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str):
    print(f"  {Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str):
    print(f"  → {message}")


def load_sample_file(filename: str) -> bytes:
    """Load a sample file from the sample directory."""
    filepath = SAMPLE_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Sample file not found: {filepath}")
    with open(filepath, "rb") as f:
        return f.read()


def test_login(base_url: str, user_id: str, password: str) -> bool:
    """Step 1: User login"""
    print_step("1", "로그인 (Login)")
    
    try:
        response = requests.post(
            f"{base_url}/api/user/login",
            json={"id": user_id, "password": password},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("로그인 성공")
            return True
        else:
            print_error(f"로그인 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def test_start_verification(base_url: str, user_id: str) -> int | None:
    """Step 2: Start verification session and get logId"""
    print_step("2", "인증 시작 (Start Verification)")
    
    try:
        response = requests.post(
            f"{base_url}/api/verification/start",
            json={"userId": user_id},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            data = response.json()
            log_id = data.get("logId")
            if log_id:
                print_success(f"logId 발급: {log_id}")
                return log_id
            else:
                print_warning("logId가 응답에 없음")
                return None
        else:
            print_error(f"인증 시작 실패: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return None


def test_gps_verification(base_url: str, log_id: int, lat: float = 37.5665, lon: float = 126.9780) -> bool:
    """Step 3-1: GPS location verification"""
    print_step("3-1", "GPS 위치 인증")
    
    try:
        response = requests.post(
            f"{base_url}/api/verification/{log_id}/gps",
            json={"latitude": lat, "longitude": lon},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("GPS 인증 성공")
            return True
        else:
            print_error(f"GPS 인증 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def test_otp_verification(base_url: str, log_id: int, reporter_name: str = "최재호") -> bool:
    """Step 3-2: News OTP verification
    
    Note: OTP requires the user to input a reporter name from the latest 5 articles
    in 동아일보 사회 section. Example: 최재호, 최미송, 최예나, 임재혁, 구민기, 김혜린
    """
    print_step("3-2", "뉴스 OTP 인증")
    
    try:
        response = requests.post(
            f"{base_url}/api/verification/{log_id}/otp",
            json={"userReporter": reporter_name},
            timeout=30  # OTP requires server-side news crawling, needs more time
        )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("OTP 인증 성공")
            return True
        else:
            print_error(f"OTP 인증 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def test_face_verification(base_url: str, log_id: int) -> bool:
    """Step 3-3: Face verification
    
    For proxy mode: First upload image via /upload_image (like ESP32-CAM does),
    then call /api/verification/{logId}/face which uses the cached image.
    For direct mode: Send image directly to AuthBox.
    """
    print_step("3-3", "얼굴 인증 (Face)")
    
    try:
        image_bytes = load_sample_file("face.jpg")
        print_info(f"Loaded face.jpg ({len(image_bytes)} bytes)")
        
        # If proxy mode (localhost), upload image first like ESP32-CAM would
        if "localhost" in base_url or "127.0.0.1" in base_url:
            # Step 1: Upload image to cache (simulating ESP32-CAM)
            upload_response = requests.post(
                f"{base_url}/upload_image",
                data=image_bytes,
                timeout=10
            )
            if upload_response.status_code != 200:
                print_error(f"이미지 업로드 실패: {upload_response.status_code}")
                return False
            print_info("Image uploaded to cache")
            
            # Step 2: Call face verification (uses cached image)
            response = requests.post(
                f"{base_url}/api/verification/{log_id}/face",
                timeout=30
            )
        else:
            # Direct mode: send image directly to AuthBox
            response = requests.post(
                f"{base_url}/api/verification/{log_id}/face",
                files={"image": ("face.jpg", image_bytes, "image/jpeg")},
                timeout=30
            )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("얼굴 인증 성공")
            return True
        else:
            print_error(f"얼굴 인증 실패: {response.status_code}")
            return False
            
    except FileNotFoundError as e:
        print_error(str(e))
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def test_fingerprint_verification(base_url: str, log_id: int) -> bool:
    """Step 3-4: Fingerprint verification
    
    For proxy mode: server.py requires real fingerprint sensor, so we call AuthBox directly.
    For direct mode: Send image directly to AuthBox.
    """
    print_step("3-4", "지문 인증 (Fingerprint)")
    
    try:
        image_bytes = load_sample_file("fingerprint.png")
        print_info(f"Loaded fingerprint.png ({len(image_bytes)} bytes)")
        
        # Fingerprint always goes directly to AuthBox since server.py requires real sensor
        # In proxy mode, we bypass the proxy for this specific test
        if "localhost" in base_url or "127.0.0.1" in base_url:
            target_url = f"{AUTHBOX_SERVER_URL}/api/verification/{log_id}/fingerprint"
            print_info(f"Bypassing proxy, calling AuthBox directly")
        else:
            target_url = f"{base_url}/api/verification/{log_id}/fingerprint"
        
        response = requests.post(
            target_url,
            files={"image": ("fingerprint.png", image_bytes, "image/png")},
            timeout=30
        )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("지문 인증 성공")
            return True
        else:
            print_error(f"지문 인증 실패: {response.status_code}")
            return False
            
    except FileNotFoundError as e:
        print_error(str(e))
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def test_signature_verification(base_url: str, log_id: int) -> bool:
    """Step 3-5: Signature verification
    
    For proxy mode: server.py expects JSON with base64-encoded image.
    For direct mode: AuthBox expects multipart file upload.
    """
    print_step("3-5", "서명 인증 (Signature)")
    
    try:
        image_bytes = load_sample_file("signature.jpg")
        print_info(f"Loaded signature.jpg ({len(image_bytes)} bytes)")
        
        if "localhost" in base_url or "127.0.0.1" in base_url:
            # Proxy mode: send as base64 JSON (matching server.py's SignatureRequest)
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            response = requests.post(
                f"{base_url}/api/verification/{log_id}/signature",
                json={"image": f"data:image/jpeg;base64,{image_b64}"},
                timeout=30
            )
        else:
            # Direct mode: send as multipart file
            response = requests.post(
                f"{base_url}/api/verification/{log_id}/signature",
                files={"image": ("signature.jpg", image_bytes, "image/jpeg")},
                timeout=30
            )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("서명 인증 성공")
            return True
        else:
            print_error(f"서명 인증 실패: {response.status_code}")
            return False
            
    except FileNotFoundError as e:
        print_error(str(e))
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def test_mail_send(base_url: str, log_id: int, sender_email: str) -> bool:
    """Step 4: Send result email"""
    print_step("4", "결과 이메일 전송 (Mail)")
    
    try:
        response = requests.post(
            f"{base_url}/api/verification/{log_id}/mail",
            json={"senderEmail": sender_email},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print_success("메일 전송 성공")
            return True
        else:
            print_error(f"메일 전송 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"요청 실패: {e}")
        return False


def run_full_test(base_url: str, user_id: str, password: str, sender_email: str, skip_steps: list = None):
    """Run the complete authentication flow test."""
    skip_steps = skip_steps or []
    
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}AuthBox API Integration Test{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Target: {base_url}")
    print(f"User ID: {user_id}")
    print(f"Sample Dir: {SAMPLE_DIR}")
    print(f"{'='*60}")
    
    results = {}
    
    # Step 1: Login
    if "login" not in skip_steps:
        results["login"] = test_login(base_url, user_id, password)
        if not results["login"]:
            print_warning("로그인 실패 - 계속 진행합니다 (테스트 목적)")
    
    # Step 2: Start Verification
    log_id = test_start_verification(base_url, user_id)
    results["start"] = log_id is not None
    
    if not log_id:
        print_error("logId를 받지 못했습니다. 테스트를 중단합니다.")
        print_summary(results)
        return False
    
    # Step 3-1: GPS
    if "gps" not in skip_steps:
        results["gps"] = test_gps_verification(base_url, log_id)
    
    # Step 3-2: OTP
    if "otp" not in skip_steps:
        results["otp"] = test_otp_verification(base_url, log_id)
    
    # Step 3-3: Face
    if "face" not in skip_steps:
        results["face"] = test_face_verification(base_url, log_id)
    
    # Step 3-4: Fingerprint
    if "fingerprint" not in skip_steps:
        results["fingerprint"] = test_fingerprint_verification(base_url, log_id)
    
    # Step 3-5: Signature
    if "signature" not in skip_steps:
        results["signature"] = test_signature_verification(base_url, log_id)
    
    # Step 4: Mail
    if "mail" not in skip_steps:
        results["mail"] = test_mail_send(base_url, log_id, sender_email)
    
    print_summary(results)
    return all(results.values())


def print_summary(results: dict):
    """Print test summary."""
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for step, success in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if success else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {step:15} : {status}")
    
    print(f"{'='*60}")
    color = Colors.GREEN if passed == total else Colors.RED
    print(f"Result: {color}{passed}/{total} passed{Colors.RESET}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="AuthBox API Integration Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_authbox_api.py --direct          # Test AuthBox server directly
  python test_authbox_api.py --proxy           # Test via local proxy (default)
  python test_authbox_api.py --user myid       # Use custom user ID
  python test_authbox_api.py --skip face       # Skip face verification
        """
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--direct", action="store_true", help="Test AuthBox server directly")
    mode_group.add_argument("--proxy", action="store_true", help="Test via local proxy server (default)")
    
    parser.add_argument("--user", default=TEST_USER_ID, help=f"User ID (default: {TEST_USER_ID})")
    parser.add_argument("--password", default=TEST_PASSWORD, help=f"Password (default: {TEST_PASSWORD})")
    parser.add_argument("--email", default=TEST_SENDER_EMAIL, help=f"Sender email (default: {TEST_SENDER_EMAIL})")
    parser.add_argument("--skip", nargs="+", choices=["login", "gps", "otp", "face", "fingerprint", "signature", "mail"],
                        help="Skip specific steps")
    parser.add_argument("--url", help="Custom server URL (overrides --direct/--proxy)")
    
    args = parser.parse_args()
    
    # Determine target URL
    if args.url:
        base_url = args.url.rstrip("/")
    elif args.direct:
        base_url = AUTHBOX_SERVER_URL
    else:
        base_url = LOCAL_PROXY_URL
    
    # Check sample directory
    if not SAMPLE_DIR.exists():
        print_error(f"Sample directory not found: {SAMPLE_DIR}")
        print_info("Please create the 'sample' folder with test images.")
        sys.exit(1)
    
    # Run tests
    success = run_full_test(
        base_url=base_url,
        user_id=args.user,
        password=args.password,
        sender_email=args.email,
        skip_steps=args.skip or []
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
