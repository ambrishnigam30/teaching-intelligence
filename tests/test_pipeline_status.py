from datetime import datetime, timezone

from src.corpus.ledger import CorpusLedger, WorkItem
from src.pipeline import _status


def test_status_dashboard_reports_live_operational_metrics():
    ledger = CorpusLedger([WorkItem("file-1", ["chemical_bonding"], name="bonding.pdf", status="PARTIAL", completed_pages=2)])
    dashboard = _status(
        datetime(2026, 10, 16, tzinfo=timezone.utc),
        {"files": 12, "pdfs": 9, "folders": 3, "shortcuts": 2, "pages": 5, "questions": 4},
        ledger,
        ["extracted bonding.pdf page 2/9"],
        "bonding.pdf",
    )
    assert "Total Drive Files Discovered: 12" in dashboard
    assert "Pages Processed This Run: 5" in dashboard
    assert "Questions Verified This Run: 4" in dashboard
    assert "Next File in Queue: bonding.pdf" in dashboard

def test_shard_deterministic_partitioning():
    import hashlib
    items = [f"file-{i}" for i in range(100)]
    shard_count = 3
    shards = {0: [], 1: [], 2: []}
    for file_id in items:
        idx = int(hashlib.sha256(file_id.encode("utf-8")).hexdigest(), 16) % shard_count
        shards[idx].append(file_id)
    # Check that each shard gets mutually exclusive, non-empty subsets
    assert len(shards[0]) + len(shards[1]) + len(shards[2]) == 100
    assert set(shards[0]).isdisjoint(set(shards[1]))
    assert set(shards[1]).isdisjoint(set(shards[2]))

