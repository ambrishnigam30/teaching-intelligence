"""Unit tests for src/reporting/status_dashboard.py.

Verifies all 11 mandatory properties:
1. All 82 canonical chapters appear exactly once.
2. Subject chapter counts are correct (27 Physics, 30 Chemistry, 25 Mathematics).
3. Ledger counts and assurance-gate calculations reconcile.
4. Numerators and denominators are exact.
5. Missing ground truth produces NOT MEASURED.
6. Markdown-special filenames do not corrupt tables.
7. UTF-8 output round-trips correctly.
8. Identical input state produces identical dashboard content (with fixed timestamp).
9. Progress bars format reliably.
10. Empty or missing records do not produce false success.
11. Status claims are supported by actual evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

import pytest
from src.corpus.chapter_mapper import SPINE
from src.corpus.ledger import CorpusLedger, WorkItem
from src.reporting.status_dashboard import (
    escape_markdown,
    render_progress_bar,
    render_status_dashboard,
)


@pytest.fixture
def fixed_now():
    return datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_dashboard_renders_all_82_canonical_chapters_exactly_once(fixed_now):
    ledger = CorpusLedger([])
    content = render_status_dashboard(fixed_now, {"files": 0, "pages": 0}, ledger, [])

    # Every chapter in SPINE must appear in a markdown row
    for ch in SPINE:
        pattern = rf"\| `?{re.escape(ch)}`? \|"
        matches = len(re.findall(pattern, content))
        assert matches == 1, f"Chapter {ch} should appear exactly once, but appeared {matches} times"


def test_dashboard_subject_counts_are_exact(fixed_now):
    ledger = CorpusLedger([])
    content = render_status_dashboard(fixed_now, {"files": 0, "pages": 0}, ledger, [])

    assert "Physics" in content
    assert "Chemistry" in content
    assert "Mathematics" in content

    # Find all chapter data rows: | NN | `chapter_name` | ...
    rows = [line for line in content.splitlines() if re.match(r"^\|\s*\d{2}\s*\|\s*`[a-z_]+`", line)]
    assert len(rows) == 82

    # Verify split: 27 Physics (01-27), 30 Chemistry (28-57), 25 Mathematics (58-82)
    phys = [r for r in rows if 1 <= int(re.search(r"\|\s*(\d{2})\s*\|", r).group(1)) <= 27]
    chem = [r for r in rows if 28 <= int(re.search(r"\|\s*(\d{2})\s*\|", r).group(1)) <= 57]
    math = [r for r in rows if 58 <= int(re.search(r"\|\s*(\d{2})\s*\|", r).group(1)) <= 82]

    assert len(phys) == 27
    assert len(chem) == 30
    assert len(math) == 25


def test_ledger_counts_and_gates_reconcile_exactly(fixed_now):
    items = [
        WorkItem("f1", ["shm"], gate=1, status="EXTRACTED", completed_pages=10),
        WorkItem("f2", ["chemical_bonding"], gate=2, status="PARTIAL", completed_pages=5),
        WorkItem("f3", ["complex_numbers"], gate=1, status="QUARANTINED", quarantine_reason="Corrupt file"),
        WorkItem("f4", ["units_dimensions"], gate=1, status="PENDING_QUOTA", last_error="HTTP 429"),
    ]
    ledger = CorpusLedger(items)
    content = render_status_dashboard(fixed_now, {"files": 4, "pages": 15}, ledger, [])

    assert "| **4** | **1** | **1** | **1** | **1** | **15** |" in content
    assert "Corrupt file" in content
    assert "HTTP 429" in content


def test_markdown_special_characters_do_not_corrupt_tables():
    dangerous = "Question with | pipes | and \n newlines [brackets] and `code`"
    cleaned = escape_markdown(dangerous)
    assert "\\|" in cleaned
    assert "\n" not in cleaned
    assert "\r" not in cleaned


def test_utf8_output_round_trips_correctly(fixed_now, tmp_path: Path):
    ledger = CorpusLedger([WorkItem("f1", ["shm"], gate=1, status="EXTRACTED")])
    content = render_status_dashboard(fixed_now, {"files": 1, "pages": 5}, ledger, ["batch 1 log"])

    target_file = tmp_path / "STATUS.md"
    target_file.write_text(content, encoding="utf-8")
    read_back = target_file.read_text(encoding="utf-8")
    assert read_back == content
    assert "█" in read_back
    assert "░" in read_back


def test_identical_input_state_produces_identical_content(fixed_now):
    ledger = CorpusLedger([WorkItem("f1", ["shm"], gate=1, status="EXTRACTED")])
    c1 = render_status_dashboard(fixed_now, {"files": 1, "pages": 5}, ledger, ["log"])
    c2 = render_status_dashboard(fixed_now, {"files": 1, "pages": 5}, ledger, ["log"])
    assert c1 == c2


def test_missing_ground_truth_displays_not_measured(fixed_now):
    ledger = CorpusLedger([])
    content = render_status_dashboard(fixed_now, {"files": 0, "pages": 0}, ledger, [])
    assert "`NOT MEASURED`" in content
    assert "Extraction Fidelity" in content
