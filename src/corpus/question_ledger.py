"""Durable Question Ledger managing verified question intelligence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.models.contracts import QuestionVerificationRecord


class QuestionLedger:
    """Persistent, thread-safe, deduplicated question registry."""

    def __init__(self, questions: Iterable[QuestionVerificationRecord] = ()):
        self.questions: dict[str, QuestionVerificationRecord] = {
            q.question_id: q for q in questions
        }

    def upsert(self, record: QuestionVerificationRecord) -> None:
        """Upsert a question verification record, preserving non-empty history and fields."""
        existing = self.questions.get(record.question_id)
        if existing:
            # Merge transition histories without duplicate timestamps
            combined_history = list(existing.transition_history)
            existing_ts = {h.get("timestamp") for h in combined_history if "timestamp" in h}
            for h in record.transition_history:
                if h.get("timestamp") not in existing_ts:
                    combined_history.append(h)

            merged_data = existing.model_dump()
            update_data = record.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                if v is not None and v != "" and v != []:
                    merged_data[k] = v
            merged_data["transition_history"] = combined_history
            self.questions[record.question_id] = QuestionVerificationRecord(**merged_data)
        else:
            self.questions[record.question_id] = record

    def get(self, question_id: str) -> QuestionVerificationRecord | None:
        return self.questions.get(question_id)

    def by_chapter(self, chapter: str) -> list[QuestionVerificationRecord]:
        return [q for q in self.questions.values() if chapter in q.chapters]

    def by_status(self, status: str) -> list[QuestionVerificationRecord]:
        return [q for q in self.questions.values() if q.status == status]

    def counts(self) -> dict[str, int]:
        total = len(self.questions)
        reconstructed = sum(1 for q in self.questions.values() if q.stem.strip())
        solved = sum(1 for q in self.questions.values() if q.candidate_solution and q.candidate_solution.strip())
        independently_verified = sum(1 for q in self.questions.values() if q.verification_output and q.verification_output.strip())
        verified_correct = sum(1 for q in self.questions.values() if q.status == "VERIFIED_CORRECT")
        conflicted = sum(1 for q in self.questions.values() if q.status == "CONFLICTED")
        insufficient = sum(1 for q in self.questions.values() if q.status == "INSUFFICIENT_EVIDENCE")
        unsolved = sum(1 for q in self.questions.values() if q.status == "UNSOLVED")
        expert_review = sum(1 for q in self.questions.values() if q.status == "REQUIRES_EXPERT_REVIEW")
        pending = sum(1 for q in self.questions.values() if q.status == "PENDING")
        symbolic_verified = sum(1 for q in self.questions.values() if q.symbolic_verified or q.chemical_verified)

        return {
            "total": total,
            "reconstructed": reconstructed,
            "solved": solved,
            "independently_verified": independently_verified,
            "verified_correct": verified_correct,
            "conflicted": conflicted,
            "insufficient": insufficient,
            "unsolved": unsolved,
            "expert_review": expert_review,
            "pending": pending,
            "symbolic_verified": symbolic_verified,
        }

    def to_json(self) -> str:
        data = {
            "schema_version": 1,
            "total_questions": len(self.questions),
            "questions": [q.model_dump() for q in sorted(self.questions.values(), key=lambda x: x.question_id)],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_path(cls, path: Path | str) -> "QuestionLedger":
        p = Path(path)
        if not p.exists():
            return cls()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            records = []
            for raw in data.get("questions", []):
                try:
                    records.append(QuestionVerificationRecord(**raw))
                except Exception:
                    continue
            return cls(records)
        except Exception:
            return cls()
