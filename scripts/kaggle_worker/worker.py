"""Private Kaggle worker entrypoint. It reads only the private HF manifest and uploads derived artifacts."""
from __future__ import annotations

import os
from pathlib import Path

def main() -> None:
    if not os.getenv("HF_TOKEN") or not os.getenv("HF_DATASET_REPO"):
        raise RuntimeError("Kaggle secrets must be supplied as private notebook secrets")
    # MinerU/DECIMER invocation is intentionally isolated here: all input/output comes through the private vault.
    from src.cloud.hf_vault import HuggingFaceVault
    vault = HuggingFaceVault(os.environ["HF_DATASET_REPO"], os.environ["HF_TOKEN"])
    vault.upload_bytes("state/kaggle_worker_heartbeat.txt", b"private worker completed", "Kaggle worker heartbeat")

if __name__ == "__main__": main()
