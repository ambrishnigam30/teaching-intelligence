"""Reconcile and audit chapter mappings across all 7,103 items in the durable ledger.

Applies ChapterMapper to file names and virtual paths, updates archetypes and exam scopes,
and verifies representation across all 82 canonical JEE chapters.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from src.corpus.chapter_mapper import ChapterMapper, SPINE
from src.corpus.classifier import classify_file, classify_exam_scope
from src.corpus.ledger import CorpusLedger, WorkItem


def reconcile_ledger(
    ledger_path: Path = Path("state/corpus_ledger.json"),
    dry_run: bool = False,
) -> dict:
    if not ledger_path.exists():
        raise FileNotFoundError(f"Ledger not found at {ledger_path}")

    ledger = CorpusLedger.from_path(ledger_path)
    mapper = ChapterMapper()
    items = list(ledger.items.values())
    total_items = len(items)

    initially_mapped = sum(1 for it in items if it.chapters)
    newly_mapped = 0
    updated_archetypes = 0

    chapter_histogram: Counter[str] = Counter()

    for item in items:
        # Reconcile archetype and exam scope if unclassified
        first_path = item.virtual_paths[0] if item.virtual_paths else ""
        fresh_arch = classify_file(item.name, first_path)
        if fresh_arch != "UNCLASSIFIED" and item.archetype == "UNCLASSIFIED":
            item.archetype = fresh_arch
            updated_archetypes += 1

        fresh_scope = classify_exam_scope(item.name, first_path)
        if fresh_scope != "BOTH" and item.exam_scope == "BOTH":
            item.exam_scope = fresh_scope

        # Refresh chapter mapping from file name + virtual paths
        candidate_text = " ".join([item.name, *item.virtual_paths])
        fresh_chapters = mapper.map_text(candidate_text)
        if fresh_chapters:
            if fresh_chapters != item.chapters:
                if not item.chapters:
                    newly_mapped += 1
                item.chapters = fresh_chapters

        for ch in item.chapters:
            chapter_histogram[ch] += 1

    mapped_total = sum(1 for it in items if it.chapters)
    unmapped_items = [it for it in items if not it.chapters]
    unmapped_by_arch = Counter(it.archetype for it in unmapped_items)

    missing_chapters = [c for c in SPINE if c not in chapter_histogram]

    stats = {
        "total_items": total_items,
        "initially_mapped": initially_mapped,
        "newly_mapped": newly_mapped,
        "mapped_total": mapped_total,
        "unmapped_total": len(unmapped_items),
        "unmapped_by_archetype": dict(unmapped_by_arch),
        "spine_total": len(SPINE),
        "covered_chapters": len(chapter_histogram),
        "missing_chapters": missing_chapters,
        "updated_archetypes": updated_archetypes,
    }

    if not dry_run:
        ledger.save(ledger_path)
        print(f"[Reconciler] Ledger saved successfully to {ledger_path}")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes to ledger")
    parser.add_argument("--ledger", type=Path, default=Path("state/corpus_ledger.json"))
    args = parser.parse_args()

    stats = reconcile_ledger(ledger_path=args.ledger, dry_run=args.dry_run)
    print("=" * 60)
    print("MENTORA CORPUS CHAPTER RECONCILIATION SUMMARY")
    print("=" * 60)
    print(f"Total Discovered Items: {stats['total_items']}")
    print(f"Initially Mapped: {stats['initially_mapped']}")
    print(f"Newly Mapped: {stats['newly_mapped']}")
    print(f"Total Mapped Now: {stats['mapped_total']} ({stats['mapped_total']*100/stats['total_items']:.1f}%)")
    print(f"Total Unmapped: {stats['unmapped_total']} ({stats['unmapped_total']*100/stats['total_items']:.1f}%)")
    print(f"Canonical Chapters Covered: {stats['covered_chapters']}/{stats['spine_total']}")
    if stats['missing_chapters']:
        print(f"Missing Chapters ({len(stats['missing_chapters'])}): {stats['missing_chapters']}")
    else:
        print("ALL 82 CANONICAL CHAPTERS ARE ACCOUNTED FOR IN THE CORPUS!")
    print("\nUnmapped Items Breakdown by Archetype:")
    for arch, cnt in sorted(stats['unmapped_by_archetype'].items(), key=lambda x: -x[1]):
        print(f"  - {arch}: {cnt}")
    print("=" * 60)


if __name__ == "__main__":
    main()
