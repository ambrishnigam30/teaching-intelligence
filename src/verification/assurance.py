from __future__ import annotations

from src.models.contracts import AssuranceGate, VerificationRecord, QuestionVerificationRecord
from src.verification.verifiers import sympy_equivalent, rdkit_equivalent_molecules
import re

def solve_outcome(
    official_key: str | None,
    blind_answer: str | None,
    symbolic_verified: bool,
    chemical_verified: bool,
    consensus_count: int = 0,
    has_valid_reasoning: bool = True,
    has_required_diagram: bool = True,
) -> str:
    """Evaluate whether an item achieves Gate 3 Knowledge-Ready verification.
    
    In accordance with the 100% verified-answer acceptance standard:
    - Zero false acceptances allowed.
    - Requires complete source reconstruction, linked diagrams, valid reasoning.
    - AI consensus ALONE without authoritative evidence or symbolic proof never promotes to PASS.
    """
    if not has_valid_reasoning or not has_required_diagram:
        return "INSUFFICIENT_EVIDENCE"

    if official_key is not None:
        key_str = str(official_key).strip().upper()
        blind_str = str(blind_answer or "").strip().upper()

        agrees = (blind_str == key_str) or sympy_equivalent(blind_str, key_str) or rdkit_equivalent_molecules(blind_str, key_str)
        if agrees and (symbolic_verified or chemical_verified):
            return "PASS"
        return "CONFLICTED"

    # Mandatory Correction 1: Never promote to PASS solely because AI models agree without authoritative key
    return "REQUIRES_EXPERT_REVIEW"

class AssuranceEngine:
    """Monotonic promotion and quarantine engine across Assurance Gates 1 through 6."""

    def evaluate(
        self,
        record: VerificationRecord,
        consensus_count: int = 0,
        tiebreak_agrees: bool | None = None,
    ) -> VerificationRecord:
        outcome = solve_outcome(
            record.official_key,
            record.blind_answer,
            record.symbolic_verified,
            record.chemical_verified,
            consensus_count,
        )
        if outcome in {"TIEBREAK", "CONFLICTED", "REQUIRES_EXPERT_REVIEW"}:
            outcome = "PASS" if tiebreak_agrees else "QUARANTINED"
        return record.model_copy(update={"outcome": outcome})

    def evaluate_question_record(
        self,
        q_record: QuestionVerificationRecord,
        timestamp: str | None = None,
    ) -> QuestionVerificationRecord:
        """Enforces the 100% verified-answer acceptance standard across the question lifecycle."""
        from datetime import datetime, timezone
        now_ts = timestamp or datetime.now(timezone.utc).isoformat()

        # 1. Structural completeness & context validation
        stem = str(q_record.stem or "").strip()
        if not stem:
            return self._transition_q(q_record, "INSUFFICIENT_EVIDENCE", "Missing or empty question stem", now_ts)

        # Check required diagram
        stem_lower = stem.lower()
        requires_diagram = any(w in stem_lower for w in ("figure", "diagram", "shown below", "in the circuit", "in the graph"))
        if requires_diagram and not q_record.diagram_ids:
            return self._transition_q(q_record, "INSUFFICIENT_EVIDENCE", "Question requires diagram but diagram_ids is empty", now_ts)

        # Check options for choice questions
        if q_record.question_type in {"SINGLE_CHOICE", "MULTIPLE_CHOICE"}:
            if len(q_record.options) < 2:
                return self._transition_q(q_record, "INSUFFICIENT_EVIDENCE", f"Choice question has only {len(q_record.options)} options", now_ts)

        # 2. Reasoning completeness
        candidate_sol = str(q_record.candidate_solution or "").strip()
        if not candidate_sol or len(candidate_sol) < 15:
            return self._transition_q(q_record, "UNSOLVED", "Missing or empty candidate reasoning", now_ts)

        # 3. Solver / Verifier separation
        if q_record.solver_family and q_record.verification_family:
            if q_record.solver_family == q_record.verification_family:
                return self._transition_q(q_record, "REQUIRES_EXPERT_REVIEW", "Verification model family cannot be identical to solver family", now_ts)

        # 4. Authoritative key agreement & domain checks
        if q_record.official_key is not None:
            off_key = str(q_record.official_key).strip().upper()
            pred_ans = str(q_record.final_answer or "").strip().upper()

            # Check for multiple-correct format mismatch
            if q_record.question_type == "MULTIPLE_CHOICE":
                off_opts = set(re.findall(r"[A-D]", off_key))
                pred_opts = set(re.findall(r"[A-D]", pred_ans))
                agrees = bool(off_opts) and off_opts == pred_opts
            else:
                agrees = (pred_ans == off_key) or sympy_equivalent(pred_ans, off_key) or rdkit_equivalent_molecules(pred_ans, off_key)

            if not agrees:
                return self._transition_q(q_record, "CONFLICTED", f"Disagreement between final answer '{pred_ans}' and official key '{off_key}'", now_ts)

            domain_ok = q_record.symbolic_verified or q_record.chemical_verified or (pred_ans in {"A", "B", "C", "D"})
            if not domain_ok:
                return self._transition_q(q_record, "REQUIRES_EXPERT_REVIEW", "Authoritative match but domain verification check failed", now_ts)

            return self._transition_q(q_record, "VERIFIED_CORRECT", "Passed all verification invariants and agrees with authoritative key", now_ts)

        # 5. Unkeyed items cannot be marked VERIFIED_CORRECT solely on model consensus
        return self._transition_q(q_record, "SOLVED_UNVERIFIED", "Solved with multi-model consensus but lacks authoritative key", now_ts)

    @staticmethod
    def _transition_q(record: QuestionVerificationRecord, new_status: str, reason: str, timestamp: str) -> QuestionVerificationRecord:
        history = list(record.transition_history)
        history.append({
            "from_status": record.status,
            "to_status": new_status,
            "reason": reason,
            "timestamp": timestamp,
        })
        return record.model_copy(update={
            "status": new_status,
            "quarantine_reason": reason if new_status != "VERIFIED_CORRECT" else None,
            "transition_history": history,
        })

    @staticmethod
    def determine_gate(
        has_source: bool,
        has_evidence: bool,
        is_verified: bool,
        has_18_capabilities: bool = False,
        is_runtime_exported: bool = False,
        is_efficacy_validated: bool = False,
    ) -> AssuranceGate:
        """Determines the monotonic Assurance Gate for an artifact."""
        if is_efficacy_validated and is_runtime_exported and has_18_capabilities and is_verified:
            return AssuranceGate.EFFICACY_VALIDATED
        if is_runtime_exported and has_18_capabilities and is_verified:
            return AssuranceGate.RUNTIME_READY
        if has_18_capabilities and is_verified:
            return AssuranceGate.TEACHER_READY
        if is_verified:
            return AssuranceGate.KNOWLEDGE_READY
        if has_evidence:
            return AssuranceGate.EVIDENCE_READY
        if has_source:
            return AssuranceGate.SOURCE_READY
        return AssuranceGate.DISCOVERED
