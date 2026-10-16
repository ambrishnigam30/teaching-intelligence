from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def _token_payload(token_json: str | None = None, token_path: str | None = None) -> tuple[dict[str, Any], Path | None]:
    # 1. Explicit argument or environment variable secret takes highest precedence
    raw = token_json if token_json is not None else os.getenv("GOOGLE_DRIVE_TOKEN_JSON", "")
    if raw.strip():
        return json.loads(raw), None

    # 2. Search for token.json in current directory or parent directories / absolute paths
    candidates = []
    if token_path:
        candidates.append(Path(token_path))
    candidates.extend([
        Path("token.json"),
        Path(__file__).resolve().parent.parent.parent / "token.json",
        Path.cwd() / "token.json"
    ])

    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8")), path

    raise RuntimeError("Set GOOGLE_DRIVE_TOKEN_JSON or provide GOOGLE_DRIVE_TOKEN_PATH containing valid token.json")


def google_drive_credentials(token_json: str | None = None, token_path: str | None = None) -> Any:
    """Load and refresh a read-only OAuth credential from Actions or a local token file."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    payload, local_path = _token_payload(token_json, token_path)
    credentials = Credentials.from_authorized_user_info(payload, [READONLY_SCOPE])
    if credentials.expired:
        if not credentials.refresh_token:
            raise RuntimeError("Google Drive token expired and has no refresh token; rerun scripts/auth_google_drive.py")
        credentials.refresh(Request())
        if local_path:
            local_path.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def google_drive_service(token_json: str | None = None, token_path: str | None = None) -> Any:
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=google_drive_credentials(token_json, token_path), cache_discovery=False)