"""Private Kaggle worker entrypoint. It reads the private HF manifest/ledger and extracts pages."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    if not os.getenv("HF_TOKEN") or not os.getenv("HF_DATASET_REPO"):
        raise RuntimeError("Kaggle secrets must be supplied as private notebook secrets")

    from src.cloud.hf_vault import HuggingFaceVault
    vault = HuggingFaceVault(os.environ["HF_DATASET_REPO"], os.environ["HF_TOKEN"])
    shard_index = os.getenv("SHARD_INDEX", "0")
    vault.upload_bytes(f"state/kaggle_worker_heartbeat_shard_{shard_index}.txt", b"private worker active", "Kaggle worker heartbeat")

    runner_path = Path("scripts/kaggle_gpu_runner.py")
    if runner_path.exists():
        subprocess.run([sys.executable, str(runner_path)])
    else:
        shard_count = os.getenv("SHARD_COUNT", "1")
        subprocess.run([
            sys.executable, "-m", "src.pipeline",
            "--skip-discovery",
            "--max-pages", "1500",
            "--time-budget-seconds", "39600",
            "--shard-index", str(shard_index),
            "--shard-count", str(shard_count),
        ])


if __name__ == "__main__":
    main()
