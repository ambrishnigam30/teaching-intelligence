"""High-fidelity JEE/NEET question reconstruction from page text and markdown."""
from __future__ import annotations

import re
from typing import Any


def parse_questions_from_text(
    text: str,
    page_number: int = 1,
    source_file_id: str = "doc",
) -> list[dict[str, Any]]:
    """Reconstruct complete structured questions from page markdown or raw text.
    
    Extracts numbered questions, complete problem statements (stems), options (A-D),
    LaTeX equations, and classifies question types.
    """
    if not text or not text.strip():
        return []

    # Clean non-printable characters while preserving newlines and math
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Pattern for question headers: 1., Q.1, Q1., Question 1:, Example 1., Problem 1.
    q_marker = re.compile(
        r"(?:^|[\n\s])(?:Q(?:uestion)?\s*[-.:]?\s*|Problem\s*[-.:]?\s*|Example\s*[-.:]?\s*|\b)([0-9]{1,3})[.)]\s+",
        re.IGNORECASE,
    )
    matches = list(q_marker.finditer(cleaned))
    if not matches:
        return []

    # Filter false positives: ignore if numbers are not ascending or if density is suspicious (e.g. table of contents)
    valid_matches = []
    last_num = 0
    for m in matches:
        num = int(m.group(1))
        # Questions typically start from 1 or follow sequentially up to ~100
        if 1 <= num <= 200:
            if not valid_matches or num >= last_num or (num == 1 and last_num > 5):
                valid_matches.append(m)
                last_num = num

    if not valid_matches:
        valid_matches = matches

    results: list[dict[str, Any]] = []

    for i, m in enumerate(valid_matches):
        start = m.end()
        end = valid_matches[i + 1].start() if i + 1 < len(valid_matches) else len(cleaned)
        q_num = int(m.group(1))
        raw_body = cleaned[start:end].strip()

        if len(raw_body) < 8:
            # Skip noise or empty numbers
            continue

        # Option pattern: (A), (B), (C), (D) or (a), (b), (c), (d) or (1), (2), (3), (4) or A., B., C., D.
        opt_marker = re.compile(
            r"(?:^|[\n\s])(?:\(([A-Da-d1-4])\)|([A-Da-d])[.)])\s+",
            re.IGNORECASE,
        )
        opt_matches = list(opt_marker.finditer(raw_body))

        if opt_matches and len(opt_matches) >= 2:
            stem = raw_body[: opt_matches[0].start()].strip()
            options: list[str] = []
            for j, om in enumerate(opt_matches):
                ostart = om.end()
                oend = opt_matches[j + 1].start() if j + 1 < len(opt_matches) else len(raw_body)
                raw_lbl = (om.group(1) or om.group(2)).upper()
                # Normalize numeric 1-4 to A-D if needed
                lbl_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
                lbl = lbl_map.get(raw_lbl, raw_lbl)
                opt_text = raw_body[ostart:oend].strip()
                options.append(f"{lbl}: {opt_text}")
            q_type = "SINGLE_CHOICE"
            lower_body = raw_body.lower()
            if any(k in lower_body for k in ("one or more than one", "multiple correct", "may be correct", "more than one option")):
                q_type = "MULTIPLE_CHOICE"
        else:
            stem = raw_body
            options = []
            q_type = "NUMERICAL" if any(w in raw_body.lower() for w in ("find the value", "determine", "calculate", "equal to", "value of")) else "DESCRIPTIVE"

        # Check for stem validity
        if not stem or len(stem) < 8:
            continue

        qid = f"{source_file_id}_p{page_number}_q{q_num}"
        results.append({
            "question_id": qid,
            "source_file_id": source_file_id,
            "question_number": q_num,
            "page_number": page_number,
            "stem": stem,
            "options": options,
            "bounding_box": None,
            "diagram_ids": [],
            "question_type": q_type,
            "passage_id": None,
            "status": "ACTIVE",
        })

    return results
