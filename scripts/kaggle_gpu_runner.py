"""Kaggle GPU fleet autonomous worker runner."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def start_ollama_and_pull() -> None:
    if sys.platform.startswith("linux"):
        try:
            print("Installing Ollama on Kaggle...")
            subprocess.run(["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"], check=True)
            print("Starting Ollama daemon...")
            subprocess.Popen(["ollama", "serve"])
            time.sleep(5)
            print("Pulling qwen2.5vl:7b (with fallbacks)...")
            subprocess.run(["sh", "-c", "ollama pull qwen2.5vl:7b || ollama pull qwen2.5vl:3b || ollama pull moondream || true"], check=False)
        except Exception as exc:
            print(f"Ollama setup warning: {exc}")


def main() -> None:
    shard_index = int(os.getenv("SHARD_INDEX", "0"))
    shard_count = int(os.getenv("SHARD_COUNT", "1"))
    max_pages = int(os.getenv("MAX_PAGES", "1500"))
    time_budget = int(os.getenv("TIME_BUDGET_SECONDS", "39600"))

    start_ollama_and_pull()
    os.environ["ENABLE_LOCAL_OLLAMA"] = "1"
    os.environ["CONTINUOUS_HF_CHECKPOINT"] = "1"
    os.environ["AUTO_SKIP_DISCOVERY_IF_POPULATED"] = "1"

    print(f"Starting Kaggle GPU extraction shard {shard_index}/{shard_count} for {max_pages} pages...")
    cmd = [
        sys.executable, "-m", "src.pipeline",
        "--skip-discovery",
        "--max-pages", str(max_pages),
        "--time-budget-seconds", str(time_budget),
        "--shard-index", str(shard_index),
        "--shard-count", str(shard_count),
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
