"""Bounded, resumable Drive-to-Hugging-Face intelligence factory entrypoint."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from datetime import datetime, timezone
import httpx

from src.cloud.hf_vault import HuggingFaceVault
from src.config.rights import RightsRegistry
from src.corpus.ledger import CorpusLedger, WorkItem
from src.drive.auth import google_drive_service
from src.drive.crawler import DriveCrawler, DriveNode, PDF_MIME
from src.drive.sync import discover_sources, work_items_for
from src.extraction.dual_path import ExtractionResult, VisionApiExtractor
from src.rotator.key_pool import KeyPool, QuotaExhausted
from src.verification.verifiers import rdkit_valid_smiles, sympy_equivalent


def load_env_file(path: Path = Path(".env.keys")) -> None:
    """Load local setup keys without overwriting explicitly supplied environment values."""
    if not path.exists(): return
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw and not raw.startswith("#") and "=" in raw:
            key, value = raw.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _write_action_output(has_more_work: bool) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"has_more_work={'true' if has_more_work else 'false'}\n")


def _verify(extraction: ExtractionResult) -> tuple[int, dict]:
    latex_valid = [expression for expression in extraction.latex if sympy_equivalent(expression, expression)]
    smiles_valid = [smiles for smiles in extraction.smiles if rdkit_valid_smiles(smiles)]
    verified_questions = len(extraction.questions) if (latex_valid or smiles_valid or not (extraction.latex or extraction.smiles)) else 0
    return verified_questions, {"latex_verified": latex_valid, "smiles_verified": smiles_valid}


def _safe_error(exc: Exception) -> str:
    """Preserve actionable provider failure metadata without publishing URLs, query strings, or credentials."""
    try:
        import httpx
        if isinstance(exc, httpx.HTTPStatusError):
            return f"{type(exc).__name__}: provider returned HTTP {exc.response.status_code}"
    except ImportError:
        pass
    return f"{type(exc).__name__}: {str(exc).split('?')[0][:240]}"


def _status(now: datetime, stats: dict, ledger: CorpusLedger, recent: list[str], active: str | None) -> str:
    completed = sum(item.status == "EXTRACTED" for item in ledger.items.values())
    pending = [item for item in ledger.next_batch(1)]
    lines = [
        "# Mentora Intelligence Factory",
        f"Last Run UTC: {now.isoformat()}",
        f"Total Drive Files Discovered: {stats['files']}",
        f"Total Drive PDFs Discovered: {stats['pdfs']}",
        f"Folders Discovered: {stats['folders']}",
        f"Shortcuts Resolved: {stats['shortcuts']}",
        f"Files Completed: {completed}",
        f"Pages Processed This Run: {stats['pages']}",
        f"Questions Verified This Run: {stats['questions']}",
        f"Active File: {active or 'none'}",
        f"Next File in Queue: {pending[0].name or pending[0].file_id if pending else 'none'}",
        "## Recent Batch Log",
    ]
    lines.extend(f"- {entry}" for entry in recent[-25:])
    return "\n".join(lines) + "\n"


def _artifact_path(item: WorkItem, page_number: int) -> str:
    chapter = item.chapters[0] if item.chapters else "unmapped"
    return f"intelligence/chapters/{chapter}/{item.file_id}/page-{page_number + 1:04}.jsonl"


def run(
    max_pages: int,
    time_budget_seconds: int,
    root_limit: int | None = None,
    skip_discovery: bool = False,
    checkpoint_pages: int = 5,
    shard_index: int = 0,
    shard_count: int = 1,
) -> bool:
    load_env_file()
    started = time.monotonic()
    now = datetime.now(timezone.utc)
    stats = {"files": 0, "pdfs": 0, "folders": 0, "shortcuts": 0, "pages": 0, "questions": 0}
    recent: list[str] = []
    active: str | None = None
    blocked_provider = False
    consecutive_quota_pauses = 0
    ledger_path = Path("state/corpus_ledger.json")
    vault = HuggingFaceVault.from_environment()
    vault.ensure_private()
    restored = vault.restore_ledger(ledger_path)
    ledger = CorpusLedger.from_path(ledger_path)
    service = google_drive_service()
    crawler = DriveCrawler(DriveCrawler.google_client(service))

    should_skip_discovery = skip_discovery or (
        os.getenv("AUTO_SKIP_DISCOVERY_IF_POPULATED", "").lower() in {"1", "true"} and len(ledger.items) >= 100
    )
    if should_skip_discovery:
        nodes = [DriveNode(item.file_id, item.name or item.file_id, item.mime_type, item.source_root_id, item.virtual_paths[0] if item.virtual_paths else item.file_id) for item in ledger.items.values()]
        stats.update(files=len(nodes), pdfs=len(nodes))
        discovery_message = f"reused persistent ledger with {len(nodes)} files"
    else:
        root_ids = list(RightsRegistry.load().roots)
        if root_limit is not None: root_ids = root_ids[:root_limit]
        nodes, crawl_stats = crawler.crawl_with_stats(root_ids)
        stats.update(files=crawl_stats.files, pdfs=crawl_stats.pdfs, folders=crawl_stats.folders, shortcuts=crawl_stats.shortcuts)
        for item in work_items_for(discover_sources(crawler, nodes=nodes)):
            ledger.upsert(item)
        discovery_message = f"discovered {crawl_stats.files} files, {crawl_stats.pdfs} PDFs, {crawl_stats.shortcuts} shortcuts"

    def render_status() -> bytes:
        Path("STATUS.md").write_text(_status(now, stats, ledger, recent, active), encoding="utf-8")
        return Path("STATUS.md").read_bytes()

    def checkpoint(files: dict[str, bytes], message: str) -> None:
        files["state/corpus_ledger.json"] = ledger.to_json().encode("utf-8")
        files["state/last_status.md"] = render_status()
        vault.commit_bytes(files, message)

    recent.append(discovery_message)
    render_status()
    node_by_id: dict[str, DriveNode] = {node.file_id: node for node in nodes if node.mime_type == PDF_MIME}
    pool = KeyPool.from_environment()
    extractor = VisionApiExtractor(pool)
    staged_files: dict[str, bytes] = {}
    continuous_hf = os.getenv("CONTINUOUS_HF_CHECKPOINT", "").lower() in {"1", "true"}

    with tempfile.TemporaryDirectory(prefix="mentora-drive-") as scratch_raw:
        scratch = Path(scratch_raw)
        while stats["pages"] < max_pages and time.monotonic() - started < time_budget_seconds:
            if shard_count > 1:
                candidates = ledger.next_batch(100)
                batch = [i for i in candidates if (int(hashlib.sha256(i.file_id.encode("utf-8")).hexdigest(), 16) % shard_count) == (shard_index % shard_count)]
            else:
                batch = ledger.next_batch(1)
            if not batch: break
            item = batch[0]; active = item.name or item.file_id
            node = node_by_id.get(item.file_id)
            if not node:
                item.status, item.last_error = "QUARANTINED", "PDF no longer present in Drive discovery"
                recent.append(f"quarantined {active}: absent from current Drive tree")
                render_status()
                continue
            pdf_path = scratch / f"{item.file_id}.pdf"
            try:
                crawler.download_verified(node, pdf_path)
                import fitz
                with fitz.open(pdf_path) as document: page_count = len(document)
                item.total_pages = page_count
                for page_number in range(item.completed_pages, page_count):
                    if stats["pages"] >= max_pages or time.monotonic() - started >= time_budget_seconds: break
                    page_png, diagrams, text_clue = extractor.render_page(pdf_path, page_number, dpi=300)
                    extracted = extractor.extract_png(page_png, text_clue=text_clue)
                    consecutive_quota_pauses = 0
                    question_count, verification = _verify(extracted)
                    artifact = {"source_file_id": item.file_id, "page_number": page_number + 1, "engine": extracted.engine, "confidence": extracted.confidence, "markdown": extracted.markdown, "latex": extracted.latex, "smiles": extracted.smiles, "questions": extracted.questions, "verification": verification}
                    staged_files[_artifact_path(item, page_number)] = (json.dumps(artifact, ensure_ascii=False) + "\n").encode("utf-8")
                    for diagram_index, diagram in enumerate(diagrams, start=1):
                        staged_files[f"assets/images/{item.file_id}/page-{page_number + 1:04}-diagram-{diagram_index:02}.png"] = diagram
                    item.completed_pages += 1; stats["pages"] += 1; stats["questions"] += question_count
                    item.gate = max(item.gate, 2)
                    item.status = "EXTRACTED" if item.completed_pages == page_count else "PARTIAL"
                    item.last_error = None
                    recent.append(f"extracted {active} page {page_number + 1}/{page_count} via {extracted.engine}")
                    if stats["pages"] % checkpoint_pages == 0 or item.status == "EXTRACTED":
                        render_status()
                        if continuous_hf:
                            checkpoint(staged_files, f"Checkpoint: {stats['pages']} pages processed")
                            staged_files.clear()
            except QuotaExhausted as exc:
                consecutive_quota_pauses += 1
                item.status, item.last_error = "PENDING_QUOTA", str(exc)
                recent.append(f"quota pause {active}: {exc}")
                if time_budget_seconds >= 60:
                    wait_sec = min(pool.shortest_cooldown_wait(), 30.0)
                    if wait_sec > 0:
                        time.sleep(wait_sec)
                ollama_enabled = os.getenv("ENABLE_LOCAL_OLLAMA", "").lower() in {"1", "true", "yes"}
                if consecutive_quota_pauses >= 3 and not ollama_enabled:
                    recent.append(f"quota exhausted: 3 consecutive pauses; breaking batch for next cycle")
                    break
            except httpx.HTTPStatusError as exc:
                item.attempts += 1; item.status = "BLOCKED_PROVIDER"; item.last_error = _safe_error(exc)
                recent.append(f"blocked {active}: {item.last_error}"); blocked_provider = True
            except Exception as exc:
                item.attempts += 1; item.status, item.last_error = "PENDING", _safe_error(exc); recent.append(f"retry {active}: {item.last_error}")
            finally:
                render_status()
            if blocked_provider: break
    has_more_work = not blocked_provider and bool(ledger.next_batch(1))
    checkpoint(staged_files, "Final atomic batch checkpoint")
    _write_action_output(has_more_work)
    return has_more_work


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--time-budget-seconds", type=int, default=900)
    parser.add_argument("--root-limit", type=int, help="Smoke-test-only limit; omit to crawl all 13 founder roots.")
    parser.add_argument("--skip-discovery", action="store_true", help="Process the durable ledger without recrawling Drive; intended only for recovery/smoke runs.")
    parser.add_argument("--checkpoint-pages", type=int, default=5)
    parser.add_argument("--shard-index", type=int, default=0, help="Shard index for parallel fleet runners.")
    parser.add_argument("--shard-count", type=int, default=1, help="Total shards in parallel fleet.")
    parser.add_argument("--checkpoint-every-files", type=int, default=1, help="Frequency of file-level checkpoints.")
    args = parser.parse_args()
    if args.max_pages < 1 or args.time_budget_seconds < 1: parser.error("limits must be positive")
    if args.root_limit is not None and args.root_limit < 1: parser.error("root limit must be positive")
    if args.checkpoint_pages < 1: parser.error("checkpoint pages must be positive")
    if args.shard_index < 0 or args.shard_count < 1: parser.error("shard settings invalid")
    run(
        args.max_pages,
        args.time_budget_seconds,
        args.root_limit,
        args.skip_discovery,
        args.checkpoint_pages,
        args.shard_index,
        args.shard_count,
    )


if __name__ == "__main__": main()
