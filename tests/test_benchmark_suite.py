"""Unit tests for the 8-Axis Evidence-Based Benchmark Suite.

Verifies strict non-proxy-inflation rules, exact numerator/denominator math,
and proper emission of NOT MEASURED for missing reference sets.
"""
from __future__ import annotations

import pytest
from src.corpus.ledger import CorpusLedger, WorkItem
from src.evaluation.benchmark_suite import BenchmarkSuite, BenchmarkAxisResult
from src.models.contracts import ConceptPackage, QuestionVerificationRecord


@pytest.fixture
def suite():
    return BenchmarkSuite()


def test_empty_ledger_handles_gracefully(suite):
    ledger = CorpusLedger([])
    res = suite.evaluate_corpus_coverage(ledger)
    assert res.status == "INSUFFICIENT SAMPLE"
    assert res.denominator == 0


def test_corpus_coverage_calculates_exact_ratio(suite):
    items = [
        WorkItem("pdf_1", ["shm"], gate=1, status="EXTRACTED"),
        WorkItem("pdf_2", ["shm"], gate=1, status="PARTIAL"),
        WorkItem("pdf_3", ["shm"], gate=1, status="PENDING"),
        WorkItem("pdf_4", ["shm"], gate=0, status="DISCOVERED"),
    ]
    ledger = CorpusLedger(items)
    res = suite.evaluate_corpus_coverage(ledger)
    # Accounted: pdf_1 (gate 1), pdf_2 (gate 1), pdf_3 (gate 1) -> 3/4 = 0.75
    assert res.numerator == 3
    assert res.denominator == 4
    assert res.measured_score == 0.75
    assert res.proxy_score == 0.25  # 1/4 extracted
    assert res.status == "FAIL"  # < 0.95


def test_missing_ground_truth_emits_not_measured_with_proxy(suite):
    records = [
        QuestionVerificationRecord(
            question_id="q1",
            file_id="f1",
            stem="Calculate force.",
            options=["A", "B"],
            candidate_solution="F = ma",
            final_answer="A",
            official_key="A",
            symbolic_verified=True,
        ),
        QuestionVerificationRecord(
            question_id="q2",
            file_id="f1",
            stem="Calculate acceleration.",
            options=["A", "B"],
            candidate_solution="a = F/m",
            final_answer="B",
            symbolic_verified=False,
        ),
    ]
    res = suite.evaluate_extraction_fidelity(records, ground_truth=None)
    assert res.status == "NOT MEASURED"
    assert res.measured_score is None
    assert res.proxy_score == 0.5  # 1 of 2 symbolically verified
    assert "NOT YET ADJUDICATED" in res.reference_set_quality


def test_solution_correctness_strictly_requires_authoritative_keys(suite):
    records = [
        # Keyed and verified
        QuestionVerificationRecord(
            question_id="q1",
            file_id="f1",
            stem="Q1",
            candidate_solution="sol1",
            final_answer="A",
            official_key="A",
            status="VERIFIED_CORRECT",
        ),
        # Keyed and conflicted
        QuestionVerificationRecord(
            question_id="q2",
            file_id="f1",
            stem="Q2",
            candidate_solution="sol2",
            final_answer="B",
            official_key="A",
            status="CONFLICTED",
        ),
        # Unkeyed (must be excluded from solution correctness denominator)
        QuestionVerificationRecord(
            question_id="q3",
            file_id="f1",
            stem="Q3",
            candidate_solution="sol3",
            final_answer="C",
            official_key=None,
            status="SOLVED_UNVERIFIED",
        ),
    ]
    res = suite.evaluate_solution_correctness(records)
    # Only q1 and q2 have official keys: total = 2, correct = 1 -> 50%
    assert res.numerator == 1
    assert res.denominator == 2
    assert res.measured_score == 0.50
    assert res.status == "FAIL"


def test_uncertainty_calibration_detects_false_acceptances(suite):
    # If a record with missing reasoning or mismatched key is marked VERIFIED_CORRECT, calibration fails
    bad_record = QuestionVerificationRecord(
        question_id="q_bad",
        file_id="f1",
        stem="Bad item",
        candidate_solution="",  # Empty reasoning
        final_answer="A",
        official_key="B",
        status="VERIFIED_CORRECT",  # False acceptance!
    )
    good_record = QuestionVerificationRecord(
        question_id="q_good",
        file_id="f1",
        stem="Good item",
        candidate_solution="Valid step by step proof",
        final_answer="A",
        official_key="A",
        status="VERIFIED_CORRECT",
    )
    res = suite.evaluate_uncertainty_calibration([bad_record, good_record])
    assert res.status == "FAIL"
    assert res.measured_score == 0.5  # 1 false acceptance out of 2


def test_full_suite_runs_all_8_axes(suite):
    ledger = CorpusLedger([WorkItem("f1", ["shm"], gate=1, status="EXTRACTED")])
    records = [
        QuestionVerificationRecord(
            question_id="q1",
            file_id="f1",
            page_numbers=[1],
            stem="Stem",
            candidate_solution="Reasoning here is solid",
            final_answer="A",
            official_key="A",
            solver_family="gemini",
            status="VERIFIED_CORRECT",
            transition_history=[{"from": "PENDING", "to": "VERIFIED_CORRECT"}],
        )
    ]
    all_results = suite.run_all(ledger, records)
    expected_axes = {
        "corpus_coverage",
        "extraction_fidelity",
        "relationship_accuracy",
        "curriculum_mapping",
        "solution_correctness",
        "pedagogical_quality",
        "uncertainty_calibration",
        "provenance_and_reproducibility",
    }
    assert set(all_results.keys()) == expected_axes
    for k, v in all_results.items():
        assert isinstance(v, BenchmarkAxisResult)
