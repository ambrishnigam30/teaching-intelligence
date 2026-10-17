"""Continuous autonomous commander for Mentora Intelligence Factory.

Runs end-to-end batches, auto-commits progress to Git and Hugging Face,
handles rate limits with exponential backoff, and updates STATUS.md metrics.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from src.corpus.ledger import CorpusLedger
from src.pipeline import load_env_file, run


def run_cmd(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess command cleanly returning stdout."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def git_commit_and_push(batch_index: int, active_summary: str = "") -> bool:
    """Commit and push updated ledger and status to origin main."""
    try:
        # Check if tracked files or status changed
        status_res = run_cmd(["git", "status", "--porcelain"])
        if not status_res.stdout.strip():
            print(f"[Git] No local changes detected after batch {batch_index}.")
            return False

        # Stage ledger, status, and generated packages
        run_cmd(["git", "add", "state/corpus_ledger.json", "STATUS.md"])
        if Path("generated").exists():
            run_cmd(["git", "add", "generated/"])
        if Path("intelligence").exists():
            run_cmd(["git", "add", "intelligence/"])
        if Path("assets").exists():
            run_cmd(["git", "add", "assets/"])

        diff_check = run_cmd(["git", "diff", "--cached", "--quiet"])
        if diff_check.returncode == 0:
            print(f"[Git] No staged diff after batch {batch_index}.")
            return False

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        commit_msg = f"feat(factory): batch {batch_index} progress - {now_str}"
        if active_summary:
            commit_msg += f" - {active_summary}"
        commit_msg += " [skip ci]"

        commit_res = run_cmd(["git", "commit", "-m", commit_msg])
        if commit_res.returncode != 0:
            print(f"[Git] Commit error: {commit_res.stderr.strip()}")
            return False

        print(f"[Git] Successfully committed: {commit_msg}")

        # Push with pull rebase retries to tolerate concurrent remote updates
        for retry in range(1, 6):
            pull_res = run_cmd(["git", "pull", "--rebase", "origin", "main"])
            push_res = run_cmd(["git", "push", "origin", "main"])
            if push_res.returncode == 0:
                print(f"[Git] Successfully pushed to origin main (attempt {retry}).")
                return True
            print(f"[Git] Push conflict or network blip on attempt {retry}, retrying in 3s...")
            time.sleep(3)

        print("[Git] Failed to push after 5 rebase retries.")
        return False
    except Exception as exc:
        print(f"[Git] Exception during commit/push: {exc}")
        return False


def get_current_metrics() -> dict:
    """Read ledger and status to extract current execution metrics."""
    ledger_path = Path("state/corpus_ledger.json")
    if not ledger_path.exists():
        return {}
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("items", [])
        total = len(items)
        extracted = sum(1 for it in items if it.get("status") == "EXTRACTED")
        partial = sum(1 for it in items if it.get("status") == "PARTIAL")
        quarantined = sum(1 for it in items if it.get("status") == "QUARANTINED")
        pending = sum(1 for it in items if it.get("status") == "PENDING")
        quota = sum(1 for it in items if it.get("status") == "PENDING_QUOTA")
        gates = {g: sum(1 for it in items if it.get("gate") == g) for g in range(7)}
        return {
            "total": total,
            "extracted": extracted,
            "partial": partial,
            "quarantined": quarantined,
            "pending": pending,
            "quota": quota,
            "gates": gates,
        }
    except Exception:
        return {}


def autonomous_loop(
    max_batches: int = 50,
    pages_per_batch: int = 10,
    time_budget_per_batch: int = 300,
    checkpoint_pages: int = 2,
    rate_limit_backoff: int = 60,
    max_consecutive_pauses: int = 5,
) -> None:
    """Execute continuous autonomous batches with auto-commit, push, and rate-limit backoff."""
    load_env_file()
    print("=" * 70)
    print("MENTORA AUTONOMOUS SYSTEMS COMMANDER — INITIALIZED")
    print(f"Max Batches: {max_batches} | Pages/Batch: {pages_per_batch} | Time Budget: {time_budget_per_batch}s")
    print("=" * 70)

    consecutive_pauses = 0

    for batch_idx in range(1, max_batches + 1):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] >>> Starting Batch {batch_idx}/{max_batches} (Subprocess Isolation)...")
        started = time.monotonic()
        hard_timeout = time_budget_per_batch + 45

        batch_cmd = [
            sys.executable,
            "-m",
            "src.pipeline",
            "--max-pages",
            str(pages_per_batch),
            "--time-budget-seconds",
            str(time_budget_per_batch),
            "--skip-discovery",
            "--checkpoint-pages",
            str(checkpoint_pages),
        ]

        try:
            res = subprocess.run(
                batch_cmd,
                timeout=hard_timeout,
                check=False,
            )
            elapsed = time.monotonic() - started
            metrics = get_current_metrics()

            if res.returncode != 0:
                print(f"[Commander] Batch {batch_idx} subprocess exited with non-zero code {res.returncode}")
                consecutive_pauses += 1
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Batch {batch_idx} completed in {elapsed:.1f}s.")
                consecutive_pauses = 0

            print(
                f"Metrics: Extracted: {metrics.get('extracted', 0)}/{metrics.get('total', 0)} | "
                f"Partial: {metrics.get('partial', 0)} | Quarantined: {metrics.get('quarantined', 0)} | "
                f"Quota Paused: {metrics.get('quota', 0)}"
            )

            # Check if more work exists in ledger
            ledger = CorpusLedger.from_path(Path("state/corpus_ledger.json"))
            has_more = bool(ledger.next_batch(1))

            # Commit and push
            active_info = (
                f"{metrics.get('extracted', 0)} files done, "
                f"{metrics.get('partial', 0)} partial, "
                f"{metrics.get('quarantined', 0)} quarantined"
            )
            git_commit_and_push(batch_idx, active_summary=active_info)

            if not has_more:
                print("\n[Commander] All eligible work items in ledger have been completed!")
                break

            if res.returncode != 0:
                if consecutive_pauses >= max_consecutive_pauses:
                    print(f"\n[Commander] Reached maximum consecutive pauses ({max_consecutive_pauses}).")
                    break
                print("[Commander] Pausing 10s before next batch retry...")
                time.sleep(10)

        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - started
            print(f"[Commander] Batch {batch_idx} timed out after {exc.timeout}s! Terminating child process.")
            consecutive_pauses += 1
            metrics = get_current_metrics()
            git_commit_and_push(batch_idx, active_summary=f"timeout after {exc.timeout}s")
            if consecutive_pauses >= max_consecutive_pauses:
                print(f"\n[Commander] Reached maximum consecutive pauses ({max_consecutive_pauses}).")
                break
            time.sleep(5)

        except Exception as exc:
            elapsed = time.monotonic() - started
            exc_str = str(exc)
            print(f"[Commander] Warning: Batch {batch_idx} raised {type(exc).__name__}: {exc_str[:200]}")
            traceback.print_exc()

            consecutive_pauses += 1
            git_commit_and_push(batch_idx, active_summary=f"pause: {type(exc).__name__}")

            if "QuotaExhausted" in type(exc).__name__ or "429" in exc_str:
                wait_sec = rate_limit_backoff * min(consecutive_pauses, 3)
                print(f"[Commander] Rate-limit backoff: Sleeping {wait_sec}s before next attempt (consecutive pauses: {consecutive_pauses})...")
                time.sleep(wait_sec)
            else:
                print(f"[Commander] Recovering from error; pausing 15s...")
                time.sleep(15)

            if consecutive_pauses >= max_consecutive_pauses:
                print(f"\n[Commander] Reached maximum consecutive pauses ({max_consecutive_pauses}).")
                print("All rotating provider keys and local vision engines are currently constrained.")
                print("Logging final status and concluding run cleanly.")
                break

    print("\n" + "=" * 70)
    print("MENTORA AUTONOMOUS SYSTEMS COMMANDER — RUN COMPLETE")
    final_metrics = get_current_metrics()
    print(f"Final Ledger State: {json.dumps(final_metrics, indent=2)}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-batches", type=int, default=50)
    parser.add_argument("--pages-per-batch", type=int, default=10)
    parser.add_argument("--time-budget", type=int, default=300)
    parser.add_argument("--checkpoint-pages", type=int, default=2)
    parser.add_argument("--backoff", type=int, default=60)
    args = parser.parse_args()

    autonomous_loop(
        max_batches=args.max_batches,
        pages_per_batch=args.pages_per_batch,
        time_budget_per_batch=args.time_budget,
        checkpoint_pages=args.checkpoint_pages,
        rate_limit_backoff=args.backoff,
    )


if __name__ == "__main__":
    main()
