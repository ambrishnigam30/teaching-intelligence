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
