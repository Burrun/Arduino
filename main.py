from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from modules.sensors import fingerprint, rtc, signature
from modules.transport import (
    BackendClient,
    DEFAULT_FILE_ENDPOINT,
    DEFAULT_METADATA_ENDPOINT,
)


def deliver_to_backend(
    metadata: Dict[str, str], client: BackendClient, file_path: Optional[str] = None
    ) -> Dict[str, dict]:
    """
    Send metadata and an optional file to the backend.
    """
    responses = {"metadata": client.send_metadata(metadata)}
    if file_path:
        responses["file"] = client.upload_file(file_path)
    return responses


def run_rtc_authentication(client: BackendClient):
    """
    Run the RTC authentication process.
    """
    print("[인증] RTC 인증을 시작합니다...")
    timestamp, source = rtc.get_current_time()
    metadata = {
        "auth_type": "rtc",
        "timestamp": timestamp.isoformat(),
        "time_source": source,
    }
    print(f"RTC 데이터: {metadata}")
    if client:
        responses = deliver_to_backend(metadata, client)
        print("[인증] 백엔드 응답:", responses)


def run_fingerprint_authentication(
    client: BackendClient, image_dir: str, timeout: int
):
    """
    Run the fingerprint authentication process.
    """
    print("[인증] 지문 인증을 시작합니다...")
    timestamp, _ = rtc.get_current_time()
    filename = f"fingerprint_{timestamp.strftime('%Y%m%d_%H%M%S')}.pgm"
    image_path = Path(image_dir) / filename

    finger = fingerprint.connect_fingerprint_sensor()
    saved_path = fingerprint.capture_fingerprint_image(
        finger, save_path=str(image_path), timeout_sec=timeout
    )
    print(f"지문 이미지가 저장되었습니다: {saved_path}")

    if client:
        metadata = {
            "auth_type": "fingerprint",
            "timestamp": timestamp.isoformat(),
            "filename": Path(saved_path).name,
        }
        responses = deliver_to_backend(metadata, client, file_path=saved_path)
        print("[인증] 백엔드 응답:", responses)


def run_signature_authentication(client: BackendClient, signature_dir: str):
    """
    Run the signature authentication process.
    """
    print("[인증] 서명 인증을 시작합니다...")
    timestamp, _ = rtc.get_current_time()
    saved_path = signature.capture_signature()
    # This is a placeholder, so we'll create a dummy file name
    filename = f"signature_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
    print(f"서명 파일: {filename}")

    if client:
        metadata = {
            "auth_type": "signature",
            "timestamp": timestamp.isoformat(),
            "filename": filename,
        }
        # In a real scenario, saved_path would be the actual path to the saved signature
        responses = deliver_to_backend(metadata, client, file_path=saved_path)
        print("[인증] 백엔드 응답:", responses)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Authenticator device main script.",
        epilog="""
        This script is designed to be run on a Raspberry Pi.
        It can be triggered by other processes or scripts to perform a specific authentication.
        Example: python3 main.py fingerprint --auto-backend
        """,
    )
    parser.add_argument(
        "module",
        choices=["rtc", "fingerprint", "signature"],
        help="The authentication module to run.",
    )
    parser.add_argument(
        "--image-dir",
        default="data/fingerprints",
        help="Directory to store captured fingerprint images.",
    )
    parser.add_argument(
        "--signature-dir",
        default="data/signatures",
        help="Directory to store captured signature images.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Seconds to wait for a finger on the sensor.",
    )
    parser.add_argument(
        "--auto-backend",
        action="store_true",
        help="Send results to the backend.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override backend base URL.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional API key for the backend.",
    )
    parser.add_argument(
        "--metadata-endpoint",
        default=None,
        help="Override metadata endpoint path.",
    )
    parser.add_argument(
        "--file-endpoint",
        default=None,
        help="Override file upload endpoint path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = None
    if args.auto_backend:
        client = BackendClient(
            base_url=args.base_url,
            api_key=args.api_key,
            metadata_endpoint=args.metadata_endpoint or DEFAULT_METADATA_ENDPOINT,
            file_endpoint=args.file_endpoint or DEFAULT_FILE_ENDPOINT,
        )

    try:
        if args.module == "rtc":
            run_rtc_authentication(client)
        elif args.module == "fingerprint":
            run_fingerprint_authentication(client, args.image_dir, args.timeout)
        elif args.module == "signature":
            run_signature_authentication(client, args.signature_dir)
    except Exception as exc:
        print(f"[오류] 인증 프로세스 실패: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
