"""Tests for QuestionLedger, QuestionParser, and ForwardProgressAssertion."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.corpus.question_ledger import QuestionLedger
from src.extraction.question_parser import parse_questions_from_text
from src.models.contracts import QuestionVerificationRecord
from src.verification.assurance import AssuranceEngine


def test_question_parser_extracts_complete_stem_and_options():
    sample_md = """
    ## Section 1: Objective Questions
    1. Percentage of s-character in $\\text{sp}^3$ hybrid orbital is
    (A) 25
    (B) 50
    (C) 66
    (D) 75

    2. Which of the following has maximum bond angle?
    (1) $\\text{sp}^2$
    (2) $\\text{sp}$
    (3) $\\text{sp}^3$
    (4) $\\text{dsp}^3$
    """
    questions = parse_questions_from_text(sample_md, page_number=1, source_file_id="doc_test")
    assert len(questions) == 2

    q1 = questions[0]
    assert q1["question_number"] == 1
    assert "Percentage of s-character" in q1["stem"]
    assert len(q1["options"]) == 4
    assert q1["options"][0].startswith("A: 25")
    assert q1["question_type"] == "SINGLE_CHOICE"

    q2 = questions[1]
    assert q2["question_number"] == 2
    assert "maximum bond angle" in q2["stem"]
    assert len(q2["options"]) == 4
    assert q2["options"][1].startswith("B:")


def test_question_ledger_upsert_and_counts():
    with TemporaryDirectory() as td:
        ledger_file = Path(td) / "question_ledger.json"
        ql = QuestionLedger()

        rec1 = QuestionVerificationRecord(
            question_id="q1",
            file_id="f1",
            stem="Calculate the radius of curvature.",
            options=["A: 1m", "B: 2m"],
            candidate_solution="Phase 1: Dissect...",
            final_answer="A",
            solver_family="gemini",
            verification_family="groq",
            official_key="A",
            symbolic_verified=True,
            status="SOLVED_UNVERIFIED",
        )
        engine = AssuranceEngine()
        eval1 = engine.evaluate_question_verification(rec1)
        assert eval1.status == "VERIFIED_CORRECT"

        ql.upsert(eval1)
        counts = ql.counts()
        assert counts["total"] == 1
        assert counts["reconstructed"] == 1
        assert counts["verified_correct"] == 1

        ql.save(ledger_file)
        assert ledger_file.exists()

        loaded = QuestionLedger.from_path(ledger_file)
        assert len(loaded.questions) == 1
        assert loaded.get("q1") is not None
        assert loaded.get("q1").status == "VERIFIED_CORRECT"


def test_unkeyed_question_cannot_be_verified_correct():
    rec = QuestionVerificationRecord(
        question_id="q_unkeyed",
        file_id="f1",
        stem="Derive the equation of state.",
        question_type="SUBJECTIVE",
        candidate_solution="Detailed reasoning steps...",
        final_answer="PV=nRT",
        solver_family="gemini",
        verification_family="groq",
        official_key=None,
        status="SOLVED_UNVERIFIED",
    )
    engine = AssuranceEngine()
    evaluated = engine.evaluate_question_verification(rec)
    # Mandate: unkeyed items cannot promote to VERIFIED_CORRECT solely on consensus
    assert evaluated.status != "VERIFIED_CORRECT"
    assert evaluated.status == "SOLVED_UNVERIFIED"
