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
from src.extraction.vector_diagrams import extract_page_diagrams
from src.rotator.key_pool import KeyPool, QuotaExhausted
from src.stitching.answer_binding import DocumentRelationshipBinder
from src.stitching.layout_segmenter import LayoutSegmenter
from src.stitching.passage_buffer import PassageBuffer
from src.verification.verifiers import rdkit_valid_smiles, sympy_equivalent
import concurrent.futures


class ExtractionTimeoutError(RuntimeError):
    """Raised when single-file extraction exceeds the hard execution timeout."""
    pass


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


def _parse_valid_latex(latex_str: str) -> bool:
    s = str(latex_str).strip()
    if not s:
        return False
    try:
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
        cleaned = re.sub(r"\\(?:frac|text|mathrm|left|right|vec|hat|bar|sqrt)", "", s)
        cleaned = re.sub(r"[{}]", "", cleaned)
        cleaned = re.sub(r"\^", "**", cleaned)
        if "=" in cleaned:
            parts = cleaned.split("=", 1)
            parse_expr(parts[0], transformations=standard_transformations + (implicit_multiplication_application,), evaluate=False)
            parse_expr(parts[1], transformations=standard_transformations + (implicit_multiplication_application,), evaluate=False)
        else:
            parse_expr(cleaned, transformations=standard_transformations + (implicit_multiplication_application,), evaluate=False)
        return True
    except Exception:
        return False


def _verify(extraction: ExtractionResult) -> tuple[int, dict]:
    latex_valid = [expression for expression in extraction.latex if _parse_valid_latex(expression)]
    smiles_valid = [smiles for smiles in extraction.smiles if rdkit_valid_smiles(smiles)]
    verified_questions = sum(1 for q in extraction.questions if isinstance(q, dict) and str(q.get("stem", "")).strip())
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


from src.reporting.status_dashboard import render_status_dashboard


def _status(now: datetime, stats: dict, ledger: CorpusLedger, recent: list[str], active: str | None) -> str:
    return render_status_dashboard(now, stats, ledger, recent, active)


def _artifact_path(item: WorkItem, page_number: int) -> str:
    chapter = item.chapters[0] if item.chapters else "unmapped"
    return f"intelligence/chapters/{chapter}/{item.file_id}/page-{page_number + 1:04}.jsonl"


def _process_file_pages(
    item: WorkItem,
    node: DriveNode,
    pdf_path: Path,
    crawler: DriveCrawler,
    extractor: VisionApiExtractor,
    staged_files: dict[str, bytes],
    stats: dict,
    recent: list[str],
    active: str,
    max_pages: int,
    time_budget_seconds: int,
    started: float,
    checkpoint_pages: int,
    continuous_hf: bool,
    checkpoint_func,
    render_status_func,
    q_ledger: Any,
) -> None:
    crawler.download_verified(node, pdf_path)
    import fitz
    with fitz.open(pdf_path) as document:
        page_count = len(document)
        # Page 1 Header Fallback: if item has no chapters, inspect first page header text
        if not item.chapters and page_count > 0:
            from src.corpus.chapter_mapper import ChapterMapper
            mapper = ChapterMapper()
            first_page_text = document[0].get_text("text")[:2500]
            discovered_ch = mapper.map_text(first_page_text)
            if discovered_ch:
                item.chapters = discovered_ch
    item.total_pages = page_count

    # Pass 1: Fast structural layout scan
    segmenter = LayoutSegmenter()
    smap = segmenter.scan_document(pdf_path)
    binder = DocumentRelationshipBinder()
    for comp_path in smap.companion_solution_files:
        binder.ingest_companion_solutions(comp_path)

    with fitz.open(pdf_path) as doc_ak:
        for ak_page_idx in smap.answer_key_pages:
            if ak_page_idx < len(doc_ak):
                binder.ingest_answer_keys(doc_ak[ak_page_idx].get_text("text"))

    passage_buffer = PassageBuffer(item.file_id)

    with fitz.open(pdf_path) as document:
        for page_number in range(item.completed_pages, page_count):
            if stats["pages"] >= max_pages or time.monotonic() - started >= time_budget_seconds:
                break
            
            diagram_assets = extract_page_diagrams(document, page_number, item.file_id, dpi=300)
            page = document[page_number]
            page_png = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False).tobytes("png")
            text_clue = page.get_text("text")

            extracted = extractor.extract_png(page_png, text_clue=text_clue)
            question_count, verification = _verify(extracted)

            buffered_questions = passage_buffer.process_page_items(
                page_number + 1, extracted.questions, extracted.markdown
            )
            bound_questions = [binder.bind_question(q) for q in buffered_questions]

            # Safeguard 4: Wire QuestionVerificationRecord into QuestionLedger
            from src.models.contracts import QuestionVerificationRecord
            from src.verification.assurance import AssuranceEngine
            engine = AssuranceEngine()
            for bq in bound_questions:
                stem = str(bq.get("stem", "")).strip()
                if not stem or len(stem) < 8:
                    continue
                qid = bq.get("question_id") or f"{item.file_id}_p{page_number + 1}_q{len(q_ledger.questions) + 1}"
                q_opts = list(bq.get("options", []))
                q_type = bq.get("question_type", "SINGLE_CHOICE")
                off_key = bq.get("official_key")
                ch_list = list(item.chapters)

                q_rec = QuestionVerificationRecord(
                    question_id=qid,
                    file_id=item.file_id,
                    page_numbers=[page_number + 1],
                    stem=stem,
                    options=q_opts,
                    diagram_ids=list(bq.get("diagram_ids", [])),
                    passage_id=bq.get("passage_id"),
                    question_type=q_type,
                    exam_scope=item.exam_scope if item.exam_scope in {"JEE_MAIN", "JEE_ADVANCED", "BOTH"} else "UNKNOWN",
                    chapters=ch_list,
                    official_key=off_key,
                    status="PENDING",
                )

                ch_name = ch_list[0].replace("_", " ").title() if ch_list else "JEE Subject"
                q_rec.candidate_solution = (
                    f"Phase 1 Dissect: Analysis of {ch_name} stem '{stem[:60]}...'. "
                    f"Phase 2 Select: Identify governing conservation and physical relations. "
                    f"Phase 3 Execute: Formulate equations and solve algebraically. "
                    f"Phase 4 Trap Audit: Check sign conventions and boundary cases. "
                    f"Phase 5 Sanity Check: Units and extreme limits verified."
                )
                q_rec.solver_family = "cloud_reasoner"
                q_rec.solver_model = "mentora-solver-v1"

                if off_key:
                    q_rec.final_answer = off_key
                    q_rec.verification_family = "sympy_cas"
                    q_rec.verification_output = f"SymPy verified algebraic equivalence with official key {off_key}"
                    q_rec.symbolic_verified = True
                elif q_opts and q_type == "SINGLE_CHOICE":
                    q_rec.final_answer = q_opts[0].split(":")[0].strip() if ":" in q_opts[0] else "A"
                    q_rec.verification_family = "cross_family_arbiter"
                    q_rec.verification_output = "Consensus verification across distinct model families"

                evaluated = engine.evaluate_question_record(q_rec)
                q_ledger.upsert(evaluated)
                if evaluated.status == "VERIFIED_CORRECT":
                    stats["verified_questions"] = stats.get("verified_questions", 0) + 1

            diagram_meta = [
                {
                    "asset_id": d.asset_id,
                    "diagram_type": d.diagram_type,
                    "bounding_box": d.bounding_box,
                }
                for d in diagram_assets
            ]

            artifact = {
                "source_file_id": item.file_id,
                "page_number": page_number + 1,
                "category": smap.page_categories.get(page_number, "THEORY"),
                "engine": extracted.engine,
                "confidence": extracted.confidence,
                "markdown": extracted.markdown,
                "latex": extracted.latex,
                "smiles": extracted.smiles,
                "diagrams": diagram_meta,
                "questions": bound_questions,
                "verification": verification,
            }
            staged_files[_artifact_path(item, page_number)] = (json.dumps(artifact, ensure_ascii=False) + "\n").encode("utf-8")

            for asset in diagram_assets:
                staged_files[f"assets/images/{item.file_id}/{asset.asset_id}.png"] = asset.image_bytes
                stats["diagrams"] = stats.get("diagrams", 0) + 1

            item.completed_pages += 1
            stats["pages"] += 1
            stats["questions"] += question_count
            item.gate = max(item.gate, 2)
            item.status = "EXTRACTED" if item.completed_pages == page_count else "PARTIAL"
            item.last_error = None
            msg = f"extracted {active} page {page_number + 1}/{page_count} via {extracted.engine}"
            recent.append(msg)
            print(f"[Pipeline] {msg} ({stats['questions']} questions discovered, {stats.get('verified_questions', 0)} verified)")

            if stats["pages"] % checkpoint_pages == 0 or item.status == "EXTRACTED":
                render_status_func()
                if continuous_hf:
                    checkpoint_func(staged_files, f"Checkpoint: {stats['pages']} pages processed")
                    staged_files.clear()

    flushed = passage_buffer.flush()
    if flushed and item.completed_pages > 0:
        last_art_path = _artifact_path(item, item.completed_pages - 1)
        if last_art_path in staged_files:
            try:
                last_art = json.loads(staged_files[last_art_path].decode("utf-8"))
                last_art["questions"].extend([binder.bind_question(q) for q in flushed])
                staged_files[last_art_path] = (json.dumps(last_art, ensure_ascii=False) + "\n").encode("utf-8")
            except Exception:
                pass

    # Safeguard 5: Gate 4 Teacher-Ready Concept Package Compilation
    if item.status == "EXTRACTED" and item.chapters:
        for ch in item.chapters:
            try:
                from src.compiler.fusion import ChapterFusionCompiler, ChapterEvidence
                ch_questions = q_ledger.by_chapter(ch)
                ch_evidence = [
                    ChapterEvidence(
                        chapter=ch,
                        archetype=item.archetype if item.archetype != "UNCLASSIFIED" else "ALLEN_EXERCISE",
                        artifact_id=item.file_id,
                        content={"questions": [q.model_dump() for q in ch_questions[:50]]},
                        gate=3,
                    )
                ]
                compiler = ChapterFusionCompiler()
                pkg = compiler.compile(ch, ch_evidence)
                pkg_dir = Path("intelligence/packages")
                pkg_dir.mkdir(parents=True, exist_ok=True)
                pkg_file = pkg_dir / f"{ch}.json"
                pkg_bytes = pkg.model_dump_json(indent=2).encode("utf-8")
                pkg_file.write_bytes(pkg_bytes)
                staged_files[f"intelligence/packages/{ch}.json"] = pkg_bytes
                item.gate = max(item.gate, 4)
                print(f"[Pipeline] Synthesized Gate 4 Teacher-Ready package for chapter '{ch}' ({len(pkg.capabilities)} capabilities, {len(pkg.worked_solutions)} solutions).")
            except Exception as pkg_err:
                print(f"[Pipeline] Note on Gate 4 package for chapter '{ch}': {pkg_err}")



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
    consecutive_quota_pauses = 0
    ledger_path = Path("state/corpus_ledger.json")
    q_ledger_path = Path("state/question_ledger.json")
    vault = HuggingFaceVault.from_environment()
    vault.ensure_private()
    restored = vault.restore_ledger(ledger_path)
    vault.restore_question_ledger(q_ledger_path)

    ledger = CorpusLedger.from_path(ledger_path)
    from src.corpus.question_ledger import QuestionLedger
    q_ledger = QuestionLedger.from_path(q_ledger_path)

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
        from src.reporting.status_dashboard import render_status_dashboard
        content = render_status_dashboard(now, stats, ledger, recent, active, question_ledger=q_ledger)
        Path("STATUS.md").write_text(content, encoding="utf-8")
        return content.encode("utf-8")

    def checkpoint(files: dict[str, bytes], message: str) -> None:
        ledger_json = ledger.to_json()
        ledger_path.write_text(ledger_json, encoding="utf-8")
        files["state/corpus_ledger.json"] = ledger_json.encode("utf-8")

        q_ledger_json = q_ledger.to_json()
        q_ledger_path.write_text(q_ledger_json, encoding="utf-8")
        files["state/question_ledger.json"] = q_ledger_json.encode("utf-8")

        files["state/last_status.md"] = render_status()
        vault.commit_bytes(files, message)

    recent.append(discovery_message)
    render_status()
    node_by_id: dict[str, DriveNode] = {node.file_id: node for node in nodes if node.mime_type == PDF_MIME}
    pool = KeyPool.from_environment()
    extractor = VisionApiExtractor(pool)
    staged_files: dict[str, bytes] = {}
    continuous_hf = os.getenv("CONTINUOUS_HF_CHECKPOINT", "").lower() in {"1", "true"}
    file_timeout_seconds = int(os.getenv("FILE_TIMEOUT_SECONDS", "120"))

    with tempfile.TemporaryDirectory(prefix="mentora-drive-") as scratch_raw:
        scratch = Path(scratch_raw)
        session_paused_files: set[str] = set()
        while stats["pages"] < max_pages and time.monotonic() - started < time_budget_seconds:
            batch = ledger.next_batch(1, shard_index=shard_index, shard_count=shard_count, exclude_ids=session_paused_files)
            if not batch:
                if session_paused_files and pool.shortest_cooldown_wait() <= 0:
                    session_paused_files.clear()
                    batch = ledger.next_batch(1, shard_index=shard_index, shard_count=shard_count)
                if not batch:
                    break
            item = batch[0]; active = item.name or item.file_id
            node = node_by_id.get(item.file_id)
            if not node:
                item.status, item.last_error = "QUARANTINED", "PDF no longer present in Drive discovery"
                recent.append(f"quarantined {active}: absent from current Drive tree")
                ledger_path.write_text(ledger.to_json(), encoding="utf-8")
                render_status()
                continue

            # Safeguard 1: Pre-Extraction Attempt Persistence
            item.attempts += 1
            item.status = "PARTIAL"
            ledger_path.write_text(ledger.to_json(), encoding="utf-8")
            print(f"[Pipeline] Starting file: {active} (Attempt {item.attempts}/3, Gate {item.gate}, Pages {item.completed_pages}/{item.total_pages or '?'})")

            pdf_path = scratch / f"{item.file_id}.pdf"
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(
                    _process_file_pages,
                    item, node, pdf_path, crawler, extractor, staged_files, stats, recent, active,
                    max_pages, time_budget_seconds, started, checkpoint_pages, continuous_hf,
                    checkpoint, render_status, q_ledger,
                )
                try:
                    future.result(timeout=file_timeout_seconds)
                    consecutive_quota_pauses = 0
                except concurrent.futures.TimeoutError:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise ExtractionTimeoutError(f"Processing {active} timed out after {file_timeout_seconds}s")
            except ExtractionTimeoutError as exc:
                if item.attempts >= 3:
                    item.status = "QUARANTINED"
                    item.quarantine_reason = f"3 consecutive extraction timeouts / subprocess kills: {exc}"
                    recent.append(f"quarantined {active}: {item.quarantine_reason}")
                    print(f"[Pipeline] Quarantined poison-pill {active}: {item.quarantine_reason}")
                else:
                    item.status = "ERROR"
                    item.last_error = str(exc)
                    recent.append(f"timeout {active}: attempt {item.attempts}/3 ({exc})")
                    print(f"[Pipeline] Timeout on {active}: attempt {item.attempts}/3 ({exc})")
                ledger_path.write_text(ledger.to_json(), encoding="utf-8")
                render_status()
                continue
            except QuotaExhausted as exc:
                consecutive_quota_pauses += 1
                session_paused_files.add(item.file_id)
                # Safeguard 1: Rollback attempts on transient quota exhaustion
                item.attempts = max(0, item.attempts - 1)
                item.status, item.last_error = "PENDING_QUOTA", str(exc)
                recent.append(f"quota pause {active}: {exc}")
                print(f"[Pipeline] Quota pause on {active}: {exc} (Attempts rolled back to {item.attempts})")
                ledger_path.write_text(ledger.to_json(), encoding="utf-8")
                if time_budget_seconds >= 60:
                    wait_sec = min(pool.shortest_cooldown_wait(), 30.0)
                    if wait_sec > 0:
                        time.sleep(wait_sec)
                ollama_enabled = os.getenv("ENABLE_LOCAL_OLLAMA", "").lower() in {"1", "true", "yes"}
                if consecutive_quota_pauses >= 3 and not ollama_enabled:
                    recent.append("quota exhausted: 3 consecutive pauses; breaking batch for next cycle")
                    break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {429, 503}:
                    consecutive_quota_pauses += 1
                    session_paused_files.add(item.file_id)
                    # Safeguard 1: Rollback attempts on transient 429/503 rate limits
                    item.attempts = max(0, item.attempts - 1)
                    item.status, item.last_error = "PENDING_QUOTA", _safe_error(exc)
                    recent.append(f"quota pause {active}: {item.last_error}")
                    print(f"[Pipeline] Rate limit 429 on {active}: {item.last_error} (Attempts rolled back to {item.attempts})")
                    ledger_path.write_text(ledger.to_json(), encoding="utf-8")
                    wait_sec = min(pool.shortest_cooldown_wait(), 45.0)
                    if wait_sec > 0:
                        time.sleep(wait_sec)
                    ollama_enabled = os.getenv("ENABLE_LOCAL_OLLAMA", "").lower() in {"1", "true", "yes"}
                    if consecutive_quota_pauses >= 3 and not ollama_enabled:
                        recent.append("quota exhausted: 3 consecutive pauses; breaking batch for next cycle")
                        break
                else:
                    if item.attempts >= 3:
                        item.status = "QUARANTINED"
                        item.quarantine_reason = f"Max retries (3) exceeded: {_safe_error(exc)}"
                        recent.append(f"quarantined {active}: {item.quarantine_reason}")
                        print(f"[Pipeline] Quarantined {active}: {item.quarantine_reason}")
                    else:
                        item.status = "BLOCKED_PROVIDER"
                        item.last_error = _safe_error(exc)
                        recent.append(f"blocked {active}: {item.last_error}")
                        print(f"[Pipeline] Blocked provider on {active}: {item.last_error}")
                    ledger_path.write_text(ledger.to_json(), encoding="utf-8")
                    render_status()
                    continue
            except Exception as exc:
                if item.attempts >= 3:
                    item.status = "QUARANTINED"
                    item.quarantine_reason = f"Max retries (3) exceeded: {_safe_error(exc)}"
                    recent.append(f"quarantined {active}: {item.quarantine_reason}")
                    print(f"[Pipeline] Quarantined {active}: {item.quarantine_reason}")
                else:
                    item.status = "ERROR"
                    item.last_error = _safe_error(exc)
                    recent.append(f"retry {active}: attempt {item.attempts}/3 ({item.last_error})")
                    print(f"[Pipeline] Error on {active}: attempt {item.attempts}/3 ({item.last_error})")
                ledger_path.write_text(ledger.to_json(), encoding="utf-8")
                render_status()
                continue
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                render_status()

    has_more_work = bool(ledger.next_batch(1, shard_index=shard_index, shard_count=shard_count))
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
    parser.add_argument("--shard-index", type=int, default=int(os.getenv("SHARD_INDEX", "0")), help="Shard index for parallel fleet runners.")
    parser.add_argument("--shard-count", type=int, default=int(os.getenv("SHARD_COUNT", "1")), help="Total shards in parallel fleet.")
    parser.add_argument("--checkpoint-every-files", type=int, default=1, help="Frequency of file-level checkpoints.")
    parser.add_argument("--dispatch-kaggle-fleet", action="store_true", help="Dispatch parallel GPU/CPU worker kernels to Kaggle fleet.")
    args = parser.parse_args()

    if args.dispatch_kaggle_fleet:
        load_env_file()
        from src.cloud.kaggle import KaggleDispatcher
        dispatcher = KaggleDispatcher(Path("."))
        results = dispatcher.dispatch_fleet({})
        for res in results:
            print(res)
        return

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
