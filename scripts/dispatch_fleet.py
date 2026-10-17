"""Dispatch sharded worker fleet across all configured Kaggle accounts."""
from __future__ import annotations

import sys
from pathlib import Path

from src.cloud.kaggle import KaggleDispatcher
from src.pipeline import load_env_file


def main() -> None:
    load_env_file()
    dispatcher = KaggleDispatcher(Path("."))
    accounts = dispatcher.discover_accounts()
    if not accounts:
        print("[Dispatcher] No Kaggle accounts discovered in environment or .env.keys.")
        sys.exit(1)

    print(f"[Dispatcher] Discovered {len(accounts)} Kaggle accounts for fleet dispatch:")
    for username, _, shard_idx in accounts:
        print(f"  - Account: {username} (assigned shard {shard_idx}/{len(accounts)})")

    print(f"[Dispatcher] Packaging self-contained workers and dispatching to Kaggle...")
    results = dispatcher.dispatch_fleet({})
    print("[Dispatcher] Fleet dispatch results:")
    for res in results:
        print(f"  -> {res}")


if __name__ == "__main__":
    main()
