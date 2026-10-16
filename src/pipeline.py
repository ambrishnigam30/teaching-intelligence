from __future__ import annotations

import os
from pathlib import Path
from src.cloud.hf_vault import HuggingFaceVault
from src.corpus.ledger import CorpusLedger
from src.drive.auth import google_drive_service
from src.drive.crawler import DriveCrawler
from src.drive.sync import discover_sources, work_items_for

def main() -> None:
    """Atomically publish the current ledger after a bounded priority batch."""
    ledger_path = Path("state/corpus_ledger.json")
    ledger = CorpusLedger.from_path(ledger_path)
    if os.getenv("GOOGLE_DRIVE_TOKEN_JSON"):
        service = google_drive_service()
        for item in work_items_for(discover_sources(DriveCrawler(DriveCrawler.google_client(service)))):
            ledger.upsert(item)
    batch = ledger.next_batch(limit=10)
    status = [f"# Mentora Intelligence Factory", f"Pending priority items: {len(batch)}"]
    for item in batch: status.append(f"- {item.file_id}: {item.status}, gate {item.gate}, chapters: {', '.join(item.chapters) or 'unmapped'}")
    Path("STATUS.md").write_text("\n".join(status) + "\n", encoding="utf-8")
    if os.getenv("HF_DATASET_REPO") and os.getenv("HF_TOKEN"):
        vault = HuggingFaceVault(os.environ["HF_DATASET_REPO"], os.environ["HF_TOKEN"])
        vault.ensure_private()
        vault.upload_bytes("state/corpus_ledger.json", ledger.to_json().encode(), "Atomic corpus ledger checkpoint")

if __name__ == "__main__": main()
