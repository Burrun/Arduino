"""
Backend transport helper that encapsulates sending collected data to a server.

The concrete REST endpoints can be customized through constructor arguments or
environment variables so that hardware scripts stay clean.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import requests
except Exception:  # pragma: no cover - requests may be missing on dev host
    requests = None

DEFAULT_METADATA_ENDPOINT = os.environ.get("BACKEND_METADATA_ENDPOINT", "/api/v1/data")
DEFAULT_FILE_ENDPOINT = os.environ.get("BACKEND_FILE_ENDPOINT", "/api/v1/files")


class BackendClient:
    """
    Thin wrapper around HTTP POSTs with optional dry-run mode when configuration
    is incomplete or the `requests` dependency is unavailable.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        metadata_endpoint: str = DEFAULT_METADATA_ENDPOINT,
        file_endpoint: str = DEFAULT_FILE_ENDPOINT,
        timeout: int = 10,
        dry_run: Optional[bool] = None,
    ) -> None:
        self.base_url = base_url or os.environ.get("BACKEND_BASE_URL")
        self.api_key = api_key or os.environ.get("BACKEND_API_KEY")
        self.metadata_endpoint = metadata_endpoint
        self.file_endpoint = file_endpoint
        self.timeout = timeout

        self._session = requests.Session() if requests else None
        if dry_run is None:
            dry_run = not (self.base_url and self._session)
        self.dry_run = dry_run

    # -------------------- internal helpers --------------------
    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not self.base_url:
            raise RuntimeError("Backend base URL이 설정되지 않았습니다.")
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # -------------------- public API --------------------
    def send_metadata(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send JSON payload describing the collected data.
        Returns a dict with status/result for logging or testing.
        """
        if self.dry_run:
            print("[Backend] dry-run metadata:", json.dumps(payload, ensure_ascii=False))
            return {"status": "skipped", "reason": "dry-run"}

        url = self._build_url(self.metadata_endpoint)
        response = self._session.post(
            url, headers=self._headers(), json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    def upload_file(self, file_path: str, field_name: str = "file") -> Dict[str, Any]:
        """
        Upload a binary file (e.g., fingerprint PGM) to the backend.
        """
        resolved = Path(file_path)
        if not resolved.exists():
            raise FileNotFoundError(resolved)

        if self.dry_run:
            print(f"[Backend] dry-run upload: {resolved}")
            return {"status": "skipped", "reason": "dry-run"}

        url = self._build_url(self.file_endpoint)
        files = {field_name: resolved.open("rb")}
        headers = self._headers()
        headers.pop("Content-Type", None)  # requests sets multipart boundary
        response = self._session.post(url, headers=headers, files=files, timeout=self.timeout)
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}


__all__ = ["BackendClient"]
