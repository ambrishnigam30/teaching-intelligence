"""Mandatory adversarial verification tests covering all 11 failure modes.

Enforces the 100% verified-answer acceptance invariant:
Zero false acceptances among questions promoted to VERIFIED_CORRECT.
"""
from __future__ import annotations

import pytest
from src.models.contracts import QuestionVerificationRecord
from src.verification.assurance import AssuranceEngine


@pytest.fixture
def engine():
    return AssuranceEngine()


def test_adversarial_01_off_by_one_or_incorrect_official_answer_binding(engine):
    """Failure Mode 1: Solver predicts 'B' based on off-by-one key binding when official answer is 'A'."""
    record = QuestionVerificationRecord(
        question_id="adv_01",
        file_id="allen_sheet_01",
        stem="Find the angular frequency of the given oscillator.",
        options=["(A) 10 rad/s", "(B) 20 rad/s", "(C) 30 rad/s", "(D) 40 rad/s"],
        candidate_solution="By equation of motion, omega = sqrt(k/m) = 10 rad/s.",
        final_answer="B",  # Incorrectly mapped to B due to off-by-one index
        official_key="A",
        solver_family="gemini",
        verification_family="groq",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "CONFLICTED"
    assert "Disagreement" in str(evaluated.quarantine_reason)
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_02_mathematically_plausible_but_incorrect_solution(engine):
    """Failure Mode 2: Solution reasoning contains sign error resulting in wrong numerical value."""
    record = QuestionVerificationRecord(
        question_id="adv_02",
        file_id="reso_math_02",
        stem="Evaluate the integral \\int_0^1 (2x - 3) dx.",
        options=["(A) -2", "(B) 2", "(C) -1", "(D) 1"],
        candidate_solution="[x^2 - 3x]_0^1 = 1 - 3 = -2.",
        final_answer="B",  # Plausible error (sign flip)
        official_key="A",
        solver_family="groq",
        verification_family="openrouter",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "CONFLICTED"
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_03_missing_negative_signs_exponents_or_boundary_conditions(engine):
    """Failure Mode 3: Disagreement due to missing negative sign or exponent mismatch."""
    record = QuestionVerificationRecord(
        question_id="adv_03",
        file_id="physics_pot_03",
        stem="Find the electrostatic potential at distance r from charge -Q.",
        options=["(A) -kQ/r", "(B) kQ/r", "(C) -kQ/r^2", "(D) kQ/r^2"],
        candidate_solution="V = kQ/r (dropped negative sign).",
        final_answer="B",
        official_key="A",
        solver_family="gemini",
        verification_family="groq",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "CONFLICTED"
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_04_truncated_multipage_question_or_missing_options(engine):
    """Failure Mode 4: Question text is truncated across page boundary; options missing."""
    record = QuestionVerificationRecord(
        question_id="adv_04",
        file_id="trunc_pdf_04",
        stem="A block of mass m is released from the top of an inclined plane...",
        options=["(A) Only option A captured"],  # Truncated, missing B, C, D
        candidate_solution="Assuming standard incline, acceleration is g sin(theta).",
        final_answer="A",
        official_key="A",
        solver_family="gemini",
        verification_family="groq",
        question_type="SINGLE_CHOICE",
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "INSUFFICIENT_EVIDENCE"
    assert "only 1 options" in str(evaluated.quarantine_reason)
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_05_missing_or_incorrectly_bound_required_diagram(engine):
    """Failure Mode 5: Question explicitly depends on figure, but diagram asset is missing."""
    record = QuestionVerificationRecord(
        question_id="adv_05",
        file_id="circuits_05",
        stem="In the circuit diagram shown below, find the current through the 5 ohm resistor.",
        options=["(A) 1 A", "(B) 2 A", "(C) 3 A", "(D) 4 A"],
        diagram_ids=[],  # Missing diagram asset!
        candidate_solution="Applying KVL around the loop gives I = 2 A.",
        final_answer="B",
        official_key="B",
        solver_family="gemini",
        verification_family="groq",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "INSUFFICIENT_EVIDENCE"
    assert "requires diagram" in str(evaluated.quarantine_reason)
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_06_multiple_correct_evaluated_as_single_correct(engine):
    """Failure Mode 6: Multi-correct JEE Advanced question (A, C, D) incorrectly answered with only (A)."""
    record = QuestionVerificationRecord(
        question_id="adv_06",
        file_id="adv_paper_06",
        stem="Which of the following statements are true for an ideal gas undergoing isothermal expansion?",
        options=["(A) Internal energy is constant", "(B) Work done is zero", "(C) Heat is absorbed", "(D) Temperature remains constant"],
        question_type="MULTIPLE_CHOICE",
        candidate_solution="Since temperature is constant, delta U = 0, so statement A is true.",
        final_answer="A",  # Missing C and D!
        official_key="A, C, D",
        solver_family="groq",
        verification_family="gemini",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "CONFLICTED"
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_07_conflicting_answer_keys_and_companion_solutions(engine):
    """Failure Mode 7: Solution predicts answer contradicting authoritative key."""
    record = QuestionVerificationRecord(
        question_id="adv_07",
        file_id="conflict_07",
        stem="Find the order of acidity of the given phenols.",
        options=["(A) I > II > III", "(B) III > II > I", "(C) II > I > III", "(D) I > III > II"],
        candidate_solution="Electron withdrawing groups increase acidity, leading to III > II > I.",
        final_answer="B",
        official_key="A",  # Conflicting key from companion solution
        solver_family="gemini",
        verification_family="groq",
        chemical_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "CONFLICTED"
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_08_corrupted_ocr_and_malformed_equations(engine):
    """Failure Mode 8: Stem corrupted by bad OCR or encoding errors producing empty stem."""
    record = QuestionVerificationRecord(
        question_id="adv_08",
        file_id="corrupt_08",
        stem="   ",  # Blank/corrupt stem
        options=["(A) 1", "(B) 2", "(C) 3", "(D) 4"],
        candidate_solution="Cannot solve without valid stem.",
        final_answer="A",
        official_key="A",
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "INSUFFICIENT_EVIDENCE"
    assert "Missing or empty" in str(evaluated.quarantine_reason)
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_09_multiple_solvers_agreeing_on_wrong_answer(engine):
    """Failure Mode 9: Three LLMs hallucinate answer 'A', but authoritative key is 'C'.
    Must NOT promote solely on model consensus!"""
    record = QuestionVerificationRecord(
        question_id="adv_09",
        file_id="hallucination_09",
        stem="A subtle JEE Advanced trap on rolling without slipping on an accelerated cart...",
        options=["(A) 2 m/s^2", "(B) 3 m/s^2", "(C) 4 m/s^2", "(D) 5 m/s^2"],
        candidate_solution="All models incorrectly ignore pseudo force and conclude a = 2 m/s^2.",
        final_answer="A",
        official_key="C",  # Authoritative ground truth
        solver_family="gemini",
        verification_family="groq",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    # The models agree on A, but the authoritative key is C. Must be CONFLICTED!
    assert evaluated.status == "CONFLICTED"
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_10_identical_solver_and_verification_family(engine):
    """Failure Mode 10: Tautological self-verification where verifier is the same family as solver."""
    record = QuestionVerificationRecord(
        question_id="adv_10",
        file_id="tautology_10",
        stem="Find the period of oscillation.",
        options=["(A) 2 pi", "(B) pi", "(C) 4 pi", "(D) pi / 2"],
        candidate_solution="T = 2 pi sqrt(L/g) = 2 pi.",
        final_answer="A",
        official_key="A",
        solver_family="gemini",
        verification_family="gemini",  # Tautological self-verification!
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "REQUIRES_EXPERT_REVIEW"
    assert "cannot be identical" in str(evaluated.quarantine_reason)
    assert evaluated.status != "VERIFIED_CORRECT"


def test_adversarial_11_correct_final_answer_with_invalid_or_empty_reasoning(engine):
    """Failure Mode 11: Correct final answer guessed with empty or trivial reasoning."""
    record = QuestionVerificationRecord(
        question_id="adv_11",
        file_id="empty_reasoning_11",
        stem="A difficult 8-step organic synthesis problem...",
        options=["(A) Benzoic acid", "(B) Acetophenone", "(C) Benzophenone", "(D) Toluene"],
        candidate_solution="Answer is A.",  # Empty/trivial non-reasoning (< 15 chars)
        final_answer="A",
        official_key="A",
        solver_family="gemini",
        verification_family="groq",
        chemical_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "UNSOLVED"
    assert "Missing or empty candidate reasoning" in str(evaluated.quarantine_reason)
    assert evaluated.status != "VERIFIED_CORRECT"


def test_happy_path_verified_correct_promotion(engine):
    """Verify that a legitimate item passing all invariants is promoted to VERIFIED_CORRECT."""
    record = QuestionVerificationRecord(
        question_id="happy_01",
        file_id="genuine_01",
        stem="Find the kinetic energy of a 2 kg block moving at 3 m/s.",
        options=["(A) 9 J", "(B) 18 J", "(C) 6 J", "(D) 12 J"],
        candidate_solution="Kinetic energy is given by KE = 1/2 * m * v^2 = 0.5 * 2 * (3)^2 = 9 J.",
        final_answer="A",
        official_key="A",
        solver_family="gemini",
        verification_family="groq",
        symbolic_verified=True,
    )
    evaluated = engine.evaluate_question_record(record)
    assert evaluated.status == "VERIFIED_CORRECT"
    assert evaluated.quarantine_reason is None
    assert len(evaluated.transition_history) == 1
    assert evaluated.transition_history[0]["to_status"] == "VERIFIED_CORRECT"
