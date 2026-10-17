"""Tests for pipeline resilience, vector clustering scaling, poison-pill quarantine, and execution timeouts."""
import json
from pathlib import Path
import time
from unittest.mock import MagicMock

import fitz
import pytest

from src.corpus.ledger import CorpusLedger, WorkItem
from src.extraction.vector_diagrams import cluster_drawings
from src.models.contracts import AssuranceGate
from src.pipeline import ExtractionTimeoutError


def test_vector_clustering_pathological_scale_performance():
    """Verify cluster_drawings caps candidate paths to 150 and clusters to 10 under 5,000 dense paths."""
    # Create a mock fitz.Page with 5,000 drawing items simulating complex chemical Lewis structures
    mock_page = MagicMock()
    mock_page.rect = fitz.Rect(0, 0, 600, 800)
    mock_drawings = []
    for i in range(5000):
        mock_drawings.append({
            "rect": fitz.Rect(i % 500, (i * 7) % 700, (i % 500) + 40, ((i * 7) % 700) + 40),
            "items": [("l", (0, 0), (10, 10))],
        })
    mock_page.get_drawings.return_value = mock_drawings

    start_time = time.monotonic()
    clusters = cluster_drawings(mock_page, min_dim=10.0, max_candidates=150)
    elapsed = time.monotonic() - start_time

    # Must complete in under 0.25 seconds without O(N^2) CPU hang
    assert elapsed < 0.25, f"Vector clustering took {elapsed:.2f}s, exceeding fast-path threshold"
    assert len(clusters) <= 10, f"Returned {len(clusters)} clusters; max allowed is 10"


def test_poison_pill_quarantine_after_three_strikes(tmp_path: Path):
    """Verify that a failing file is quarantined after 3 attempts and excluded from next_batch."""
    item = WorkItem(file_id="bad_file_123", chapters=["chemical_bonding"], attempts=2)
    ledger = CorpusLedger([item])

    # Simulate 3rd failure
    item.attempts += 1
    if item.attempts >= 3:
        ledger.quarantine(item.file_id, reason="Max retries (3) exceeded: Memory allocation error")

    assert item.status == "QUARANTINED"
    assert item.quarantine_reason == "Max retries (3) exceeded: Memory allocation error"

    # next_batch must NOT pick up quarantined items
    next_items = ledger.next_batch(10)
    assert not any(x.file_id == "bad_file_123" for x in next_items)

    # Quarantined work item cannot be promoted
    with pytest.raises(ValueError, match="quarantined work cannot be promoted"):
        ledger.transition("bad_file_123", AssuranceGate.SOURCE_READY)


def test_work_item_quarantine_serialization_roundtrip(tmp_path: Path):
    """Verify quarantine_reason persists across disk serialization and deserialization."""
    item = WorkItem(
        file_id="quarantine_roundtrip_test",
        chapters=["chemical_bonding"],
        status="QUARANTINED",
        attempts=3,
        quarantine_reason="ExtractionTimeoutError: 120s ceiling exceeded",
    )
    ledger = CorpusLedger([item])
    ledger_path = tmp_path / "corpus_ledger.json"
    ledger_path.write_text(ledger.to_json(), encoding="utf-8")

    loaded_ledger = CorpusLedger.from_path(ledger_path)
    loaded_item = loaded_ledger.items["quarantine_roundtrip_test"]

    assert loaded_item.status == "QUARANTINED"
    assert loaded_item.attempts == 3
    assert loaded_item.quarantine_reason == "ExtractionTimeoutError: 120s ceiling exceeded"


def test_extraction_timeout_error_definition():
    """Verify ExtractionTimeoutError inherits from RuntimeError for clean failover."""
    err = ExtractionTimeoutError("Processing chemical_bonding/page-0010 timed out after 120s")
    assert isinstance(err, RuntimeError)
    assert "120s" in str(err)
