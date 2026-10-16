from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class SeededCase:
    identifier: str
    error_type: str
    corrupted: str
    expected_signal: str

class CriticAudit:
    def __init__(self, cases: list[SeededCase]): self.cases = cases
    def score(self, critic) -> float:
        if not self.cases: raise ValueError("At least one seeded case is required")
        caught = sum(bool(critic(case.corrupted, case.expected_signal)) for case in self.cases)
        return caught / len(self.cases)
    def passes(self, critic, threshold: float = 0.95) -> bool:
        return self.score(critic) >= threshold
