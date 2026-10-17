from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

@dataclass(frozen=True)
class LocalQuestion:
    part: str
    section: str
    local_number: int

class MockSectionStitcher:
    """Maps section-reset test numbers to continuous answer-key numbers in reading order."""
    def __init__(self):
        self._mapping: dict[LocalQuestion, int] = {}
    def add_section(self, part: str, section: str, local_numbers: list[int]) -> None:
        start = len(self._mapping) + 1
        for offset, number in enumerate(local_numbers):
            key = LocalQuestion(part, section, number)
            if key in self._mapping:
                raise ValueError(f"duplicate local question {key}")
            self._mapping[key] = start + offset
    def global_number(self, part: str, section: str, local_number: int) -> int:
        return self._mapping[LocalQuestion(part, section, local_number)]
    def local_question(self, global_number: int) -> LocalQuestion:
        return next(key for key, value in self._mapping.items() if value == global_number)

class ExerciseKeyBinder:
    """Binds explicit Allen tracking codes to banner context and answer-key cells."""
    def __init__(self):
        self.questions: dict[str, dict] = {}
        self.keys: dict[str, str] = {}
    def add_question(self, tracking_code: str, subtopic: str, page: int) -> None:
        if tracking_code in self.questions:
            raise ValueError(f"duplicate tracking code {tracking_code}")
        self.questions[tracking_code] = {"subtopic": subtopic, "page": page}
    def add_answer_key(self, tracking_code: str, answer: str) -> None:
        self.keys[tracking_code] = answer
    def bound(self, tracking_code: str) -> dict:
        if tracking_code not in self.questions or tracking_code not in self.keys:
            raise KeyError(f"unbound question {tracking_code}")
        return {"tracking_code": tracking_code, **self.questions[tracking_code], "official_key": self.keys[tracking_code]}


class DocumentRelationshipBinder:
    """Production binder associating questions to answer key grids and companion solution documents."""

    def __init__(self):
        # Maps (exercise_id, question_number) -> official_key
        self.key_map: dict[tuple[str, int], str] = {}
        # Maps (exercise_id, question_number) -> worked_solution
        self.solution_map: dict[tuple[str, int], str] = {}

    @staticmethod
    def parse_answer_key_text(text: str, default_exercise: str = "default") -> dict[tuple[str, int], str]:
        """Parses dense tabular answer key grids into key mappings."""
        keys: dict[tuple[str, int], str] = {}
        current_ex = default_exercise

        # Common format: "1. (A)" or "1. (A, B)" or "1. A" or "1. 42" or "1. (1)"
        # Also supports Allen section banners e.g. "EXERCISE-I", "EXERCISE-II"
        lines = text.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check for exercise banner (e.g. EXERCISE-I, EXERCISE 2, EXERCISE A)
            banner_match = re.search(r"\bEXERCISE\s*[-–—:]*\s*(?:NO\.?)?\s*([0-9IVX]+|[A-D])\b", line_str, re.IGNORECASE)
            if banner_match:
                current_ex = banner_match.group(0).strip()
                continue

            # Find all Q-A pairs on this line: e.g. "1. (A) 2. (C) 3. (B)"
            pairs = re.findall(
                r"(?:^|[\s\t,;|])([0-9]{1,3})[\s.:–-]+(?:\(?([A-D](?:\s*,\s*[A-D])*|[1-4]|-?[0-9]+(?:\.[0-9]+)?)\)?)",
                line_str
            )
            for q_str, ans_str in pairs:
                q_num = int(q_str)
                ans = ans_str.strip().upper()
                # Normalize numeric options 1->A, 2->B, 3->C, 4->D if single digit 1-4 in MCQ context
                if ans == "1":
                    ans = "A"
                elif ans == "2":
                    ans = "B"
                elif ans == "3":
                    ans = "C"
                elif ans == "4":
                    ans = "D"
                keys[(current_ex, q_num)] = ans

        return keys

    def ingest_answer_keys(self, text: str, default_exercise: str = "default") -> int:
        """Ingests answer key text into binder."""
        parsed = self.parse_answer_key_text(text, default_exercise)
        self.key_map.update(parsed)
        return len(parsed)

    def ingest_companion_solutions(self, companion_pdf_path: Path, default_exercise: str = "default") -> int:
        """Ingests worked solutions from companion solution PDF."""
        try:
            import fitz
        except ImportError:
            return 0

        if not companion_pdf_path.exists():
            return 0

        count = 0
        current_ex = default_exercise
        doc = fitz.open(companion_pdf_path)
        try:
            full_text = ""
            for page in doc:
                full_text += page.get_text("text") + "\n"

            # Parse questions and solutions
            # Pattern: "1. Sol." or "Q.1 " or "1. Explanation:" or "1. " followed by text
            chunks = re.split(r"(?:\n|^)(?:Q\.?\s*)?([0-9]{1,3})[.)]\s*(?:Sol(?:ution)?\.?|Explanation:)?\s*", full_text)
            # chunks[0] is preamble; then alternating q_num, solution_text
            i = 1
            while i < len(chunks) - 1:
                q_num = int(chunks[i])
                sol_text = chunks[i+1].strip()
                # Extract solution up to 4000 characters
                sol_clean = sol_text[:4000].strip()
                if sol_clean:
                    self.solution_map[(current_ex, q_num)] = sol_clean
                    count += 1
                i += 2
        finally:
            doc.close()
        return count

    def bind_question(self, question: dict[str, Any], default_exercise: str = "default") -> dict[str, Any]:
        """Binds official answer key and companion solution to a question dictionary."""
        q_num = question.get("question_number")
        if q_num is None:
            num_match = re.match(r"^(?:Q(?:uestion)?\s*)?([0-9]+)[.)\s]", str(question.get("stem", "")), re.IGNORECASE)
            if num_match:
                q_num = int(num_match.group(1))

        exercise = question.get("exercise_id") or default_exercise

        # Attempt lookup by (exercise, q_num), fallback to any exercise with q_num
        official_key = None
        if q_num is not None:
            official_key = self.key_map.get((exercise, q_num))
            if official_key is None:
                # Fallback to ("default", q_num) or first matching q_num
                official_key = self.key_map.get(("default", q_num))
                if official_key is None:
                    for (ex, q), key in self.key_map.items():
                        if q == q_num:
                            official_key = key
                            break

        worked_solution = None
        if q_num is not None:
            worked_solution = self.solution_map.get((exercise, q_num))
            if worked_solution is None:
                worked_solution = self.solution_map.get(("default", q_num))
                if worked_solution is None:
                    for (ex, q), sol in self.solution_map.items():
                        if q == q_num:
                            worked_solution = sol
                            break

        bound = dict(question)
        if official_key is not None:
            bound["official_key"] = official_key
        if worked_solution is not None:
            bound["worked_solution"] = worked_solution

        return bound
