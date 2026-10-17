"""Two-pass document layout segmentation and structural mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Literal

ScopeType = Literal["JEE_MAIN", "JEE_ADVANCED", "BOTH", "UNKNOWN"]

@dataclass
class ExerciseSection:
    name: str
    start_page: int  # 0-indexed
    end_page: int    # 0-indexed, inclusive
    exam_scope: ScopeType = "UNKNOWN"
    section_type: str = "EXERCISE"  # EXERCISE, THEORY, ANSWER_KEY, SOLUTIONS

@dataclass
class DocumentStructuralMap:
    file_path: Path
    page_count: int
    exercise_sections: list[ExerciseSection] = field(default_factory=list)
    answer_key_pages: list[int] = field(default_factory=list)
    solution_pages: list[int] = field(default_factory=list)
    companion_solution_files: list[Path] = field(default_factory=list)
    page_categories: dict[int, str] = field(default_factory=dict)

class LayoutSegmenter:
    """Pass 1: Fast PyMuPDF scan to detect exercise boundaries, trailing answer keys, and companion files."""

    ANSWER_KEY_PATTERNS = [
        re.compile(r"\bANSWER\s*KEY\b", re.IGNORECASE),
        re.compile(r"\bANSWERS\b", re.IGNORECASE),
        re.compile(r"\bKEY\s*&\s*HINTS\b", re.IGNORECASE),
    ]

    SOLUTION_PATTERNS = [
        re.compile(r"\bHINTS\s*&\s*SOLUTIONS\b", re.IGNORECASE),
        re.compile(r"\bDETAILED\s*SOLUTIONS\b", re.IGNORECASE),
        re.compile(r"\bSOLUTIONS\b", re.IGNORECASE),
    ]

    EXERCISE_PATTERNS = [
        re.compile(r"\bEXERCISE\s*[-–—:]*\s*(?:NO\.?)?\s*([0-9IVX]+|[A-D])\b", re.IGNORECASE),
        re.compile(r"\b(JEE\s*MAIN|JEE\s*ADVANCED)\s*(?:EXERCISE|ARCHIVE|PYQ|CORNER)?\b", re.IGNORECASE),
        re.compile(r"\b(PREVIOUS\s*YEARS?\s*QUESTIONS?|PYQ)\b", re.IGNORECASE),
        re.compile(r"\b(BEGINNER'?S\s*BOX|IN-CHAPTER\s*EXERCISE)\s*[-–—:]*\s*([0-9]+)?\b", re.IGNORECASE),
    ]

    @staticmethod
    def find_companion_files(pdf_path: Path) -> list[Path]:
        """Detect companion solution or answer key PDFs in the same directory."""
        if not pdf_path.exists():
            return []
        parent = pdf_path.parent
        stem = pdf_path.stem.lower()
        # Remove common exercise suffixes to get the core chapter/topic name
        base = re.sub(r"[\s_-]*(?:exercise|ex|module|sheet|theory|qs|questions)[\s_-]*\d*$", "", stem, flags=re.IGNORECASE).strip()
        companions: list[Path] = []
        try:
            for sibling in parent.iterdir():
                if sibling == pdf_path or sibling.suffix.lower() != ".pdf":
                    continue
                s_name = sibling.stem.lower()
                # Check if sibling has solution/key indicators and shares base
                is_solution = any(k in s_name for k in ["solution", "sol", "ans", "answer_key", "hint"])
                if is_solution:
                    if base and (base in s_name or s_name in base):
                        companions.append(sibling)
                    elif len(stem) > 4 and stem[:8] in s_name:
                        companions.append(sibling)
        except (PermissionError, OSError):
            pass
        return sorted(companions)

    def scan_document(self, pdf_path: Path) -> DocumentStructuralMap:
        """Scan a PDF document to construct a structural map without rendering 300-DPI images."""
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF (fitz) is required for LayoutSegmenter") from exc

        if not pdf_path.exists():
            return DocumentStructuralMap(file_path=pdf_path, page_count=0)

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        smap = DocumentStructuralMap(file_path=pdf_path, page_count=page_count)
        smap.companion_solution_files = self.find_companion_files(pdf_path)

        current_exercise: ExerciseSection | None = None

        for page_idx in range(page_count):
            page = doc[page_idx]
            # Fast text extraction (first 1000 characters is usually enough for headers)
            text = page.get_text("text")[:2500]
            first_lines = "\n".join(text.splitlines()[:15])

            is_ans_key = any(p.search(first_lines) for p in self.ANSWER_KEY_PATTERNS)
            is_solution = any(p.search(first_lines) for p in self.SOLUTION_PATTERNS)

            # Check if page is dense tabular key (many patterns like "1. (A) 2. (B)" or "1.(1) 2.(3)")
            key_density = len(re.findall(r"\b\d+[\s.:–-]+(?:\([A-D1-4]\)|[A-D])\b", text))
            if key_density >= 10:
                is_ans_key = True

            if is_ans_key:
                smap.answer_key_pages.append(page_idx)
                smap.page_categories[page_idx] = "ANSWER_KEY"
                if current_exercise:
                    current_exercise.end_page = max(current_exercise.start_page, page_idx - 1)
                    smap.exercise_sections.append(current_exercise)
                    current_exercise = None
                continue

            if is_solution:
                smap.solution_pages.append(page_idx)
                smap.page_categories[page_idx] = "SOLUTIONS"
                if current_exercise:
                    current_exercise.end_page = max(current_exercise.start_page, page_idx - 1)
                    smap.exercise_sections.append(current_exercise)
                    current_exercise = None
                continue

            # Check exercise patterns
            ex_match = None
            for p in self.EXERCISE_PATTERNS:
                m = p.search(first_lines)
                if m:
                    ex_match = m.group(0).strip()
                    break

            if ex_match:
                if current_exercise:
                    current_exercise.end_page = page_idx - 1
                    smap.exercise_sections.append(current_exercise)
                
                # Determine scope
                scope: ScopeType = "UNKNOWN"
                upper_text = first_lines.upper()
                if "JEE ADVANCED" in upper_text or "ADVANCED" in upper_text or "EXERCISE 2" in upper_text or "EXERCISE II" in upper_text:
                    scope = "JEE_ADVANCED"
                elif "JEE MAIN" in upper_text or "MAIN" in upper_text or "EXERCISE 1" in upper_text or "EXERCISE I" in upper_text:
                    scope = "JEE_MAIN"

                current_exercise = ExerciseSection(
                    name=ex_match,
                    start_page=page_idx,
                    end_page=page_idx,
                    exam_scope=scope,
                    section_type="EXERCISE",
                )
                smap.page_categories[page_idx] = "EXERCISE"
            else:
                if current_exercise:
                    current_exercise.end_page = page_idx
                    smap.page_categories[page_idx] = "EXERCISE"
                else:
                    smap.page_categories[page_idx] = "THEORY"

        if current_exercise:
            current_exercise.end_page = page_count - 1
            smap.exercise_sections.append(current_exercise)

        doc.close()
        return smap
