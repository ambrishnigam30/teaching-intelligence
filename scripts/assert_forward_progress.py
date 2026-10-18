"""Enforces strict non-zero forward progress assertion in CI runs.

Bans 'green CI theatre' by verifying that every marathon run either:
1. Extracts at least 1 new page or completes a file.
2. Reconstructs or verifies at least 1 new question.
3. Successfully transitions a poison-pill file to QUARANTINED (unblocking the queue).
4. Synthesizes a new Gate 4 Concept Package.
5. Or confirms that 100% of the corpus is already fully extracted and verified.

If zero progress was made while work remained, exits with code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SNAPSHOT_FILE = Path("state/marathon_initial_snapshot.json")


def take_snapshot() -> None:
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)

    extracted_files = 0
    total_pages = 0
    quarantined = 0
    pending_items = 0

    corpus_path = Path("state/corpus_ledger.json")
    if corpus_path.exists():
        try:
            from src.corpus.ledger import CorpusLedger
            ledger = CorpusLedger.from_path(corpus_path)
            items = list(ledger.items.values())
            extracted_files = sum(1 for it in items if it.status == "EXTRACTED")
            total_pages = sum(it.completed_pages for it in items)
            quarantined = sum(1 for it in items if it.status == "QUARANTINED")
            pending_items = sum(1 for it in items if it.status in {"PENDING", "PARTIAL", "PENDING_QUOTA"})
        except Exception as exc:
            print(f"[Snapshot] Warning loading corpus ledger: {exc}")

    question_count = 0
    verified_q_count = 0
    q_ledger_path = Path("state/question_ledger.json")
    if q_ledger_path.exists():
        try:
            from src.corpus.question_ledger import QuestionLedger
            ql = QuestionLedger.from_path(q_ledger_path)
            counts = ql.counts()
            question_count = counts.get("reconstructed", 0)
            verified_q_count = counts.get("verified_correct", 0)
        except Exception as exc:
            print(f"[Snapshot] Warning loading question ledger: {exc}")

    package_count = len(list(Path("intelligence/packages").glob("*.json"))) if Path("intelligence/packages").exists() else 0

    snapshot = {
        "extracted_files": extracted_files,
        "total_pages": total_pages,
        "quarantined": quarantined,
        "pending_items": pending_items,
        "question_count": question_count,
        "verified_q_count": verified_q_count,
        "package_count": package_count,
    }

    SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"[Snapshot] Initial marathon metrics recorded: {snapshot}")


def assert_progress() -> None:
    if not SNAPSHOT_FILE.exists():
        print("[AssertProgress] No initial snapshot found. Taking snapshot now.")
        take_snapshot()
        return

    try:
        initial = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[AssertProgress] Failed reading snapshot: {exc}")
        return

    # Measure current
    current_extracted = 0
    current_pages = 0
    current_quarantined = 0
    current_pending = 0

    corpus_path = Path("state/corpus_ledger.json")
    if corpus_path.exists():
        try:
            from src.corpus.ledger import CorpusLedger
            ledger = CorpusLedger.from_path(corpus_path)
            items = list(ledger.items.values())
            current_extracted = sum(1 for it in items if it.status == "EXTRACTED")
            current_pages = sum(it.completed_pages for it in items)
            current_quarantined = sum(1 for it in items if it.status == "QUARANTINED")
            current_pending = sum(1 for it in items if it.status in {"PENDING", "PARTIAL", "PENDING_QUOTA"})
        except Exception as exc:
            print(f"[AssertProgress] Warning loading corpus ledger: {exc}")

    current_questions = 0
    current_verified_q = 0
    q_ledger_path = Path("state/question_ledger.json")
    if q_ledger_path.exists():
        try:
            from src.corpus.question_ledger import QuestionLedger
            ql = QuestionLedger.from_path(q_ledger_path)
            counts = ql.counts()
            current_questions = counts.get("reconstructed", 0)
            current_verified_q = counts.get("verified_correct", 0)
        except Exception as exc:
            print(f"[AssertProgress] Warning loading question ledger: {exc}")

    current_packages = len(list(Path("intelligence/packages").glob("*.json"))) if Path("intelligence/packages").exists() else 0

    delta_files = current_extracted - initial.get("extracted_files", 0)
    delta_pages = current_pages - initial.get("total_pages", 0)
    delta_quarantined = current_quarantined - initial.get("quarantined", 0)
    delta_questions = current_questions - initial.get("question_count", 0)
    delta_verified_q = current_verified_q - initial.get("verified_q_count", 0)
    delta_packages = current_packages - initial.get("package_count", 0)

    print("\n" + "=" * 60)
    print("MARATHON PROGRESS DELTA AUDIT")
    print("=" * 60)
    print(f"Files Extracted:     {initial.get('extracted_files', 0)} -> {current_extracted} (delta {delta_files:+d})")
    print(f"Pages Extracted:     {initial.get('total_pages', 0)} -> {current_pages} (delta {delta_pages:+d})")
    print(f"Files Quarantined:   {initial.get('quarantined', 0)} -> {current_quarantined} (delta {delta_quarantined:+d})")
    print(f"Questions Rebuilt:   {initial.get('question_count', 0)} -> {current_questions} (delta {delta_questions:+d})")
    print(f"Questions Verified:  {initial.get('verified_q_count', 0)} -> {current_verified_q} (delta {delta_verified_q:+d})")
    print(f"Gate 4 Packages:     {initial.get('package_count', 0)} -> {current_packages} (delta {delta_packages:+d})")
    print(f"Remaining Work:      {current_pending} items pending")
    print("=" * 60)

    # Check if there is remaining work to do
    if initial.get("pending_items", 0) == 0 and current_pending == 0:
        print("[AssertProgress] PASS: Corpus is 100% complete! No pending work remains.")
        return

    # Check forward progress
    made_progress = (
        delta_files > 0
        or delta_pages > 0
        or delta_quarantined > 0
        or delta_questions > 0
        or delta_verified_q > 0
        or delta_packages > 0
    )

    if not made_progress:
        err_msg = (
            "FATAL: Zero forward progress detected during this cloud marathon run!\n"
            "0 pages extracted, 0 files resolved, 0 questions verified, 0 packages synthesized.\n"
            "Failing build immediately to stop 'green CI theatre' and alert engineering.\n"
            "Check API key quotas, runner network connectivity, or Kaggle worker dispatch."
        )
        print(f"\n::error::{err_msg}", file=sys.stderr)
        sys.exit(1)

    print("\n[AssertProgress] SUCCESS: Verified positive forward progress in this marathon run!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enforce Marathon Forward Progress Invariant")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--snapshot", action="store_true", help="Record initial metrics snapshot")
    group.add_argument("--assert", dest="do_assert", action="store_true", help="Assert positive forward progress")

    args = parser.parse_args()
    if args.snapshot:
        take_snapshot()
    elif args.do_assert:
        assert_progress()


if __name__ == "__main__":
    main()
