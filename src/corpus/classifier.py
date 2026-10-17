from __future__ import annotations

import re

ARCHETYPES = {
    "ALLEN_THEORY": (r"allen", r"theory|module"),
    "ALLEN_EXERCISE": (r"allen", r"exercise|_ex\\."),
    "RESONANCE_SHEET": (r"resonance",),
    "QUESTION_BANK_PYQ": (r"pyq|previous.?year|question.?bank|\b202\d\b",),
    "SOLUTIONS_ANSWER_KEY": (r"solution|hints.?&.?solutions|answer.?key|\bkey\b|\bsol\b",),
    "TEST_SERIES_PAPER": (r"test|major|minor|paper|aits|mock",),
    "HANDBOOK_SHORT_NOTES": (r"handbook|short.?notes|formula|summary|revision",),
    "SPECIALIST_CLASS_NOTES": (r"skm|class.?notes|specialist|handwritten",),
    "REFERENCE_TEXTBOOK": (r"reference|sykes|textbook|irodov|cengage|pandey",),
    "THEORY_MODULE": (r"theory|module|concept|study.?material",),
    "EXERCISE_DRILL": (r"exercise|drill|dpp|sheet|practice|apsp",),
}

def classify_file(name: str, path: str = "") -> str:
    value = f"{name} {path}".lower()
    for archetype, required in ARCHETYPES.items():
        if all(re.search(pattern, value) for pattern in required):
            return archetype
    return "UNCLASSIFIED"

def classify_exam_scope(name: str, path: str = "") -> str:
    val = f"{name} {path}".lower()
    has_adv = bool(re.search(r"\b(?:advanced|adv|jee\s*adv|ja|olympiad)\b", val))
    has_main = bool(re.search(r"\b(?:mains?|jee\s*main|jm|aieee)\b", val))
    if has_adv and not has_main:
        return "JEE_ADVANCED"
    if has_main and not has_adv:
        return "JEE_MAIN"
    return "BOTH"
