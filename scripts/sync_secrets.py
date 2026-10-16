"""Safely sync secrets from .env.keys and token.json to GitHub Secrets."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

def main() -> None:
    env_keys_path = Path(".env.keys")
    if not env_keys_path.exists():
        print(".env.keys not found")
        return

    secrets: dict[str, str] = {}
    for line in env_keys_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if v:
            secrets[k] = v

    # If GOOGLE_DRIVE_TOKEN_JSON is empty in .env.keys, check token.json on disk
    if "GOOGLE_DRIVE_TOKEN_JSON" not in secrets or not secrets["GOOGLE_DRIVE_TOKEN_JSON"]:
        token_path = Path("token.json")
        if token_path.exists():
            secrets["GOOGLE_DRIVE_TOKEN_JSON"] = token_path.read_text(encoding="utf-8")

    # If KAGGLE_USERNAME or KAGGLE_KEY are missing but KAGGLE_USERNAME_1 is present
    if "KAGGLE_USERNAME" not in secrets and "KAGGLE_USERNAME_1" in secrets:
        secrets["KAGGLE_USERNAME"] = secrets["KAGGLE_USERNAME_1"]
    if "KAGGLE_KEY" not in secrets and "KAGGLE_KEY_1" in secrets:
        secrets["KAGGLE_KEY"] = secrets["KAGGLE_KEY_1"]

    # Also handle OPENROUTER_API_2 fallback typo if present
    if "OPENROUTER_API_2" in secrets and "OPENROUTER_API_KEY_2" not in secrets:
        secrets["OPENROUTER_API_KEY_2"] = secrets["OPENROUTER_API_2"]

    print(f"Found {len(secrets)} secrets to synchronize to GitHub Actions.")

    success_count = 0
    for key, value in secrets.items():
        if key == "GITHUB_REPOSITORY":
            continue
        try:
            subprocess.run(
                ["gh", "secret", "set", key],
                input=value.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            print(f"  [OK] Synced secret {key}")
            success_count += 1
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode("utf-8", errors="replace")
            print(f"  [FAIL] Failed to sync secret {key}: {err.strip()}")

    print(f"Secret synchronization complete: {success_count}/{len(secrets)} secrets synced.")

if __name__ == "__main__":
    main()
