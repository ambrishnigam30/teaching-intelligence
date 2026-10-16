from __future__ import annotations

import argparse
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scopes", required=True)
    parser.add_argument("--credentials", default="credentials.json")
    parser.add_argument("--token", default="token.json")
    args = parser.parse_args()
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(args.credentials, [args.scopes])
    credentials = flow.run_local_server(port=0)
    Path(args.token).write_text(credentials.to_json(), encoding="utf-8")
    print(f"Created read-only OAuth token at {args.token}")

if __name__ == "__main__": main()
