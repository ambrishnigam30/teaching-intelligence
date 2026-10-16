from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def _token_payload(token_json: str | None = None, token_path: str | None = None) -> tuple[dict[str, Any], Path | None]:
    # 1. Check all possible environment variable names for the secret
    env_candidates = [
        token_json,
        os.getenv("GOOGLE_DRIVE_TOKEN_JSON"),
        os.getenv("GOOGLE_DRIVE_TOKEN"),
        os.getenv("DRIVE_TOKEN_JSON"),
        os.getenv("GDRIVE_TOKEN"),
    ]
    for raw in env_candidates:
        if raw and str(raw).strip():
            try:
                return json.loads(str(raw)), None
            except json.JSONDecodeError:
                pass

    # 2. Search for token.json across multiple fallback paths
    configured_path = token_path or os.getenv("GOOGLE_DRIVE_TOKEN_PATH") or os.getenv("DRIVE_TOKEN_PATH")
    file_candidates = []
    if configured_path:
        file_candidates.append(Path(configured_path))
    file_candidates.extend([
        Path("token.json"),
        Path("config/token.json"),
        Path("secrets/token.json"),
        Path(__file__).resolve().parent.parent.parent / "token.json",
        Path.cwd() / "token.json"
    ])

    for path in file_candidates:
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8")), path
            except Exception:
                pass

    raise RuntimeError(
        "Google Drive token not found! Please check that your GitHub Secret "
        "(GOOGLE_DRIVE_TOKEN_JSON, GOOGLE_DRIVE_TOKEN, etc.) is populated or token.json exists."
    )


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