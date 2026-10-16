from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class LocalQuestion:
    part: str
    section: str
    local_number: int

class MockSectionStitcher:
    """Maps section-reset test numbers to continuous answer-key numbers in reading order."""
    def __init__(self): self._mapping: dict[LocalQuestion, int] = {}
    def add_section(self, part: str, section: str, local_numbers: list[int]) -> None:
        start = len(self._mapping) + 1
        for offset, number in enumerate(local_numbers):
            key = LocalQuestion(part, section, number)
            if key in self._mapping: raise ValueError(f"duplicate local question {key}")
            self._mapping[key] = start + offset
    def global_number(self, part: str, section: str, local_number: int) -> int:
        return self._mapping[LocalQuestion(part, section, local_number)]
    def local_question(self, global_number: int) -> LocalQuestion:
        return next(key for key, value in self._mapping.items() if value == global_number)

class ExerciseKeyBinder:
    """Binds explicit Allen tracking codes to banner context and answer-key cells."""
    def __init__(self): self.questions: dict[str, dict] = {}; self.keys: dict[str, str] = {}
    def add_question(self, tracking_code: str, subtopic: str, page: int) -> None:
        if tracking_code in self.questions: raise ValueError(f"duplicate tracking code {tracking_code}")
        self.questions[tracking_code] = {"subtopic": subtopic, "page": page}
    def add_answer_key(self, tracking_code: str, answer: str) -> None: self.keys[tracking_code] = answer
    def bound(self, tracking_code: str) -> dict:
        if tracking_code not in self.questions or tracking_code not in self.keys: raise KeyError(f"unbound question {tracking_code}")
        return {"tracking_code": tracking_code, **self.questions[tracking_code], "official_key": self.keys[tracking_code]}
