from __future__ import annotations

from src.models.contracts import AssuranceGate, VerificationRecord
from src.verification.verifiers import sympy_equivalent, rdkit_equivalent_molecules

def solve_outcome(
    official_key: str | None,
    blind_answer: str | None,
    symbolic_verified: bool,
    chemical_verified: bool,
    consensus_count: int = 0,
) -> str:
    """Evaluate whether an item achieves Gate 3 Knowledge-Ready verification."""
    if official_key is not None:
        key_str = str(official_key).strip().upper()
        blind_str = str(blind_answer or "").strip().upper()

        agrees = (blind_str == key_str) or sympy_equivalent(blind_str, key_str) or rdkit_equivalent_molecules(blind_str, key_str)
        if agrees and (symbolic_verified or chemical_verified):
            return "PASS"
        return "TIEBREAK"

    # Unkeyed drills require three-way consensus plus symbolic verification
    if consensus_count >= 3 and (symbolic_verified or chemical_verified):
        return "PASS"
    return "TIEBREAK"

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
        if outcome == "TIEBREAK":
            outcome = "PASS" if tiebreak_agrees else "QUARANTINED"
        return record.model_copy(update={"outcome": outcome})

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
