from __future__ import annotations

import json
import os
from typing import Any

def google_drive_service(token_json: str | None = None) -> Any:
    """Create a read-only Drive v3 service from the OAuth JSON held in Actions secrets."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    raw = token_json or os.environ.get("GOOGLE_DRIVE_TOKEN_JSON")
    if not raw: raise RuntimeError("GOOGLE_DRIVE_TOKEN_JSON is required for cloud Drive sync")
    credentials = Credentials.from_authorized_user_info(json.loads(raw), ["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=credentials, cache_discovery=False)
