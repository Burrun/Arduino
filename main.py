from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from modules.sensors import fingerprint, rtc
from modules.transport import (
    BackendClient,
    DEFAULT_FILE_ENDPOINT,
    DEFAULT_METADATA_ENDPOINT,
)


def collect_rtc_data() -> Dict[str, str]:
    """
    Capture RTC timestamp and return payload metadata.
    """
    timestamp, source = rtc.get_current_time()
    return {
        "timestamp": timestamp.isoformat(),
        "time_source": source,
    }


def collect_fingerprint_data(image_dir: str, timeout: int) -> Dict[str, str]:
    """
    Capture fingerprint image and return payload metadata.
    """
    timestamp, source = rtc.get_current_time()
    filename = f"fingerprint_{timestamp.strftime('%Y%m%d_%H%M%S')}.pgm"
    image_path = Path(image_dir) / filename

    finger = fingerprint.connect_fingerprint_sensor()
    saved = fingerprint.capture_fingerprint_image(
        finger, save_path=str(image_path), timeout_sec=timeout
    )

    return {
        "fingerprint_image": saved,
    }


def deliver_to_backend(payload: Dict[str, str], client: BackendClient) -> Dict[str, dict]:
    """
    Send metadata and fingerprint file to backend.
    """
    responses = {
        "metadata": client.send_metadata(
            {
                "timestamp": payload["timestamp"],
                "time_source": payload["time_source"],
                "filename": Path(payload["fingerprint_image"]).name,
            }
        ),
        "file": client.upload_file(payload["fingerprint_image"]),
    }
    return responses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sensor data collection orchestrator.")
    parser.add_argument(
        "module",
        nargs="?",
        choices=["rtc", "fingerprint"],
        help="Specify a single module to run.",
    )
    parser.add_argument(
        "--image-dir",
        default="data/fingerprints",
        help="Directory to store captured fingerprint images.",
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
        help="Send results to backend if configuration is available.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override backend base URL (otherwise BACKEND_BASE_URL env is used).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional API key for backend Authorization header.",
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

    if args.module == "rtc":
        data = collect_rtc_data()
        print(f"[모듈] RTC:{data['time_source']} / timestamp:{data['timestamp']}")
        return 0

    if args.module == "fingerprint":
        data = collect_fingerprint_data(args.image_dir, args.timeout)
        print(f"[모듈] Fingerprint saved -> {data['fingerprint_image']}")
        return 0

    data = collect_sensor_data(args.image_dir, args.timeout)
    print(f"[모듈] RTC:{data['time_source']} / timestamp:{data['timestamp']}")
    print(f"[모듈] Fingerprint saved -> {data['fingerprint_image']}")

    if args.auto_backend:
        client = BackendClient(
            base_url=args.base_url,
            api_key=args.api_key,
            metadata_endpoint=args.metadata_endpoint or DEFAULT_METADATA_ENDPOINT,
            file_endpoint=args.file_endpoint or DEFAULT_FILE_ENDPOINT,
        )
        try:
            responses = deliver_to_backend(data, client)
            print("[모듈] Backend metadata response:", responses["metadata"])
            print("[모듈] Backend file response:", responses["file"])
        except Exception as exc:  # pragma: no cover - runtime reporting
            print(f"[모듈] Backend 전송 실패: {exc}")
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
