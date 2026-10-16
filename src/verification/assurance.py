from __future__ import annotations

from src.models.contracts import VerificationRecord

def solve_outcome(official_key: str | None, blind_answer: str | None, symbolic_verified: bool, chemical_verified: bool, consensus_count: int = 0) -> str:
    if official_key is not None:
        if blind_answer == official_key and (symbolic_verified or chemical_verified): return "PASS"
        return "TIEBREAK"
    return "PASS" if consensus_count >= 3 and symbolic_verified else "TIEBREAK"

class AssuranceEngine:
    def evaluate(self, record: VerificationRecord, consensus_count: int = 0, tiebreak_agrees: bool | None = None) -> VerificationRecord:
        outcome = solve_outcome(record.official_key, record.blind_answer, record.symbolic_verified, record.chemical_verified, consensus_count)
        if outcome == "TIEBREAK": outcome = "PASS" if tiebreak_agrees else "QUARANTINED"
        return record.model_copy(update={"outcome": outcome})
