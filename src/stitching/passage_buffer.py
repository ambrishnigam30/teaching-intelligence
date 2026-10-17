"""Stateful sliding window passage buffer and cross-page question reconstruction."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

PASSAGE_HEADER_PATTERNS = [
    re.compile(r"(?:Paragraph|Passage|Comprehension)\s*(?:for\s*)?(?:Question[s]?|Q\.?)?\s*([0-9]+)\s*(?:to|[-–—])\s*([0-9]+)", re.IGNORECASE),
    re.compile(r"Read\s+the\s+following\s+passage\s+and\s+answer\s+(?:questions?|Q\.?)?\s*([0-9]+)\s*(?:to|[-–—])\s*([0-9]+)", re.IGNORECASE),
]

DANGLING_STEM_PATTERNS = [
    re.compile(r"[,:;=+\-*/]\s*$", re.DOTALL),
    re.compile(r"\b(?:is|are|the|then|and|if|where|when|such\s+that|equals|given\s+by)\s*$", re.IGNORECASE),
    re.compile(r"\b(?:Column\s*[-–—I]+)\s*$", re.IGNORECASE),
]

@dataclass
class ActivePassage:
    passage_id: str
    text: str
    start_q: int
    end_q: int
    diagram_ids: list[str] = field(default_factory=list)

@dataclass
class PendingQuestion:
    source_file_id: str
    question_number: int | None
    stem: str
    options: list[str] = field(default_factory=list)
    page_number: int = 1
    bounding_box: list[float] | None = None
    diagram_ids: list[str] = field(default_factory=list)
    question_type: str = "SINGLE_CHOICE"
    passage_id: str | None = None
    is_complete: bool = False

class PassageBuffer:
    """Buffers questions across column and page boundaries to reconstruct split items and comprehension passages."""

    def __init__(self, source_file_id: str):
        self.source_file_id = source_file_id
        self.active_passage: ActivePassage | None = None
        self.pending_question: PendingQuestion | None = None
        self.finalized_questions: list[dict[str, Any]] = []

    def _is_stem_dangling(self, stem: str) -> bool:
        s = stem.strip()
        if not s:
            return True
        return any(p.search(s) for p in DANGLING_STEM_PATTERNS)

    def _detect_passage(self, text: str, page_number: int) -> ActivePassage | None:
        for p in PASSAGE_HEADER_PATTERNS:
            m = p.search(text)
            if m:
                start_q, end_q = int(m.group(1)), int(m.group(2))
                passage_id = f"{self.source_file_id}_passage_p{page_number}_{start_q}_{end_q}"
                return ActivePassage(
                    passage_id=passage_id,
                    text=text.strip(),
                    start_q=start_q,
                    end_q=end_q,
                )
        return None

    def process_page_items(self, page_number: int, raw_questions: list[dict[str, Any]], page_markdown: str = "") -> list[dict[str, Any]]:
        """Process extracted questions from a single page, merging with pending state."""
        # 1. Check for passage headers in page markdown or question stems
        new_passage = self._detect_passage(page_markdown, page_number)
        if new_passage:
            self.active_passage = new_passage

        emitted: list[dict[str, Any]] = []

        for item in raw_questions:
            stem = str(item.get("stem", "")).strip()
            options = list(item.get("options", []))
            q_num = item.get("question_number")
            if q_num is None:
                # Try to extract leading question number from stem
                num_match = re.match(r"^(?:Q(?:uestion)?\s*)?([0-9]+)[.)\s]", stem, re.IGNORECASE)
                if num_match:
                    q_num = int(num_match.group(1))

            diagram_ids = list(item.get("diagram_ids", []))
            bbox = item.get("bounding_box")
            q_type = item.get("question_type", "SINGLE_CHOICE")

            # Check if this item is a continuation of a pending question
            if self.pending_question is not None:
                # If this item has no explicit question number, or starts with continuation options
                is_continuation = False
                if q_num is None:
                    is_continuation = True
                elif options and not stem:
                    # Options-only block from split page
                    is_continuation = True
                elif re.match(r"^\s*(?:\([C-D]\)|[C-D][.)])", stem):
                    is_continuation = True

                if is_continuation:
                    # Merge with pending
                    if stem:
                        self.pending_question.stem += " " + stem
                    for opt in options:
                        if opt not in self.pending_question.options:
                            self.pending_question.options.append(opt)
                    for did in diagram_ids:
                        if did not in self.pending_question.diagram_ids:
                            self.pending_question.diagram_ids.append(did)
                    # Check if now complete
                    if len(self.pending_question.options) >= 4 or not self._is_stem_dangling(self.pending_question.stem):
                        self.pending_question.is_complete = True
                        finalized = self._finalize_pending()
                        if finalized:
                            emitted.append(finalized)
                    continue
                else:
                    # Previous pending was not continued, finalize it as-is
                    finalized = self._finalize_pending()
                    if finalized:
                        emitted.append(finalized)

            # Assign active passage if applicable
            passage_id = None
            if self.active_passage:
                if q_num is not None:
                    if self.active_passage.start_q <= q_num <= self.active_passage.end_q:
                        passage_id = self.active_passage.passage_id
                    elif q_num > self.active_passage.end_q:
                        self.active_passage = None  # Passed end of passage

            # Check if current item appears dangling
            appears_dangling = self._is_stem_dangling(stem) or (q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE") and len(options) in (1, 2))

            if appears_dangling:
                self.pending_question = PendingQuestion(
                    source_file_id=self.source_file_id,
                    question_number=q_num,
                    stem=stem,
                    options=options,
                    page_number=page_number,
                    bounding_box=bbox,
                    diagram_ids=diagram_ids,
                    question_type=q_type,
                    passage_id=passage_id,
                    is_complete=False,
                )
            else:
                qid = f"{self.source_file_id}_p{page_number}_q{q_num if q_num is not None else len(self.finalized_questions) + 1}"
                q_dict = {
                    "question_id": qid,
                    "source_file_id": self.source_file_id,
                    "question_number": q_num,
                    "page_number": page_number,
                    "stem": stem,
                    "options": options,
                    "bounding_box": bbox,
                    "diagram_ids": diagram_ids,
                    "question_type": q_type,
                    "passage_id": passage_id,
                    "status": "ACTIVE",
                }
                self.finalized_questions.append(q_dict)
                emitted.append(q_dict)

        return emitted

    def _finalize_pending(self) -> dict[str, Any] | None:
        if self.pending_question is None:
            return None
        pq = self.pending_question
        qid = f"{pq.source_file_id}_p{pq.page_number}_q{pq.question_number if pq.question_number is not None else len(self.finalized_questions) + 1}"
        q_dict = {
            "question_id": qid,
            "source_file_id": pq.source_file_id,
            "question_number": pq.question_number,
            "page_number": pq.page_number,
            "stem": pq.stem,
            "options": pq.options,
            "bounding_box": pq.bounding_box,
            "diagram_ids": pq.diagram_ids,
            "question_type": pq.question_type,
            "passage_id": pq.passage_id,
            "status": "ACTIVE",
        }
        self.finalized_questions.append(q_dict)
        self.pending_question = None
        return q_dict

    def flush(self) -> list[dict[str, Any]]:
        """Flush any remaining pending question at the end of the document."""
        emitted: list[dict[str, Any]] = []
        finalized = self._finalize_pending()
        if finalized:
            emitted.append(finalized)
        return emitted
