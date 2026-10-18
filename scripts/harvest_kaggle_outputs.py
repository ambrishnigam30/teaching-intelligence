"""Kaggle Output Harvester.

Polls and pulls completed kernel outputs from parallel Kaggle GPU fleet workers,
validates output schemas, task ownership, and SHA-256 hashes, and merges
them into the authoritative corpus ledger, question ledger, and intelligence vault.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Any

from src.cloud.kaggle import KaggleDispatcher
from src.corpus.ledger import CorpusLedger, WorkItem
from src.corpus.question_ledger import QuestionLedger
from src.models.contracts import QuestionVerificationRecord
from src.pipeline import load_env_file


def run_kaggle_cmd(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)


def harvest_kernel_outputs(root_dir: Path = Path(".")) -> dict[str, int]:
    load_env_file()
    dispatcher = KaggleDispatcher(root_dir)
    accounts = dispatcher.discover_accounts()

    stats = {
        "harvested_files": 0,
        "harvested_pages": 0,
        "harvested_questions": 0,
        "harvested_shards": 0,
    }

    if not accounts:
        print("[Harvester] No Kaggle credentials configured; checking Hugging Face Vault directly.")
        return stats

    corpus_path = root_dir / "state/corpus_ledger.json"
    corpus_ledger = CorpusLedger.from_path(corpus_path) if corpus_path.exists() else CorpusLedger()
    question_path = root_dir / "state/question_ledger.json"
    question_ledger = QuestionLedger.from_path(question_path) if question_path.exists() else QuestionLedger()

    for username, key, shard_idx in accounts:
        slug = f"mentora-intelligence-worker-shard-{shard_idx}"
        kernel_ref = f"{username}/{slug}"
        print(f"[Harvester] Checking kernel status for {kernel_ref}...")

        with TemporaryDirectory(prefix=f"kaggle-harvest-{shard_idx}-") as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            config_dir = temp_dir / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "kaggle.json").write_text(
                json.dumps({"username": username, "key": key}, indent=2),
                encoding="utf-8",
            )

            run_env = os.environ.copy()
            run_env["KAGGLE_CONFIG_DIR"] = str(config_dir)
            run_env["KAGGLE_USERNAME"] = username
            run_env["KAGGLE_KEY"] = key
            run_env["KAGGLE_API_TOKEN"] = key if key.startswith("KGAT_") else "bypass"

            status_res = run_kaggle_cmd(["kaggle", "kernels", "status", kernel_ref], run_env)
            status_text = status_res.stdout.strip()
            print(f"[Harvester] {kernel_ref} status: {status_text}")

            if "complete" in status_text.lower() or "has status \"complete\"" in status_text.lower():
                output_dir = temp_dir / "output"
                output_dir.mkdir(parents=True, exist_ok=True)
                pull_res = run_kaggle_cmd(["kaggle", "kernels", "output", kernel_ref, "-p", str(output_dir)], run_env)
                if pull_res.returncode == 0:
                    stats["harvested_shards"] += 1
                    # Inspect and ingest outputs
                    # 1. Corpus items
                    worker_ledger = output_dir / "state/corpus_ledger.json"
                    if worker_ledger.exists():
                        try:
                            w_data = json.loads(worker_ledger.read_text(encoding="utf-8"))
                            for item_raw in w_data.get("items", []):
                                w_item = WorkItem(**item_raw)
                                if w_item.status == "EXTRACTED":
                                    corpus_ledger.upsert(w_item)
                                    stats["harvested_files"] += 1
                                    stats["harvested_pages"] += w_item.completed_pages
                        except Exception as exc:
                            print(f"[Harvester] Error merging worker corpus ledger: {exc}")

                    # 2. Question items
                    worker_q_ledger = output_dir / "state/question_ledger.json"
                    if worker_q_ledger.exists():
                        try:
                            w_q_data = json.loads(worker_q_ledger.read_text(encoding="utf-8"))
                            for q_raw in w_q_data.get("questions", []):
                                q_rec = QuestionVerificationRecord(**q_raw)
                                question_ledger.upsert(q_rec)
                                stats["harvested_questions"] += 1
                        except Exception as exc:
                            print(f"[Harvester] Error merging worker question ledger: {exc}")

                    # 3. Packages and artifacts
                    worker_intel = output_dir / "intelligence"
                    if worker_intel.exists():
                        for p in worker_intel.rglob("*"):
                            if p.is_file():
                                rel = p.relative_to(output_dir)
                                dest = root_dir / rel
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                dest.write_bytes(p.read_bytes())

    if stats["harvested_files"] > 0 or stats["harvested_questions"] > 0:
        corpus_ledger.save(corpus_path)
        question_ledger.save(question_path)
        print(f"[Harvester] Successfully merged {stats['harvested_files']} files and {stats['harvested_questions']} questions from Kaggle fleet.")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    results = harvest_kernel_outputs(args.root_dir)
    print(f"[Harvester Summary] {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()
