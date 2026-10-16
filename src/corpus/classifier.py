from __future__ import annotations

import re

ARCHETYPES = {
    "ALLEN_THEORY": (r"allen", r"theory|module"),
    "ALLEN_EXERCISE": (r"allen", r"exercise|_ex\\."),
    "RESONANCE_SHEET": (r"resonance",),
    "TEST_SERIES_PAPER": (r"test|major|minor|paper",),
    "HANDBOOK_SHORT_NOTES": (r"handbook|short.?notes",),
    "SPECIALIST_CLASS_NOTES": (r"skm|class.?notes|specialist",),
    "REFERENCE_TEXTBOOK": (r"reference|sykes|textbook",),
}

def classify_file(name: str, path: str = "") -> str:
    value = f"{name} {path}".lower()
    for archetype, required in ARCHETYPES.items():
        if all(re.search(pattern, value) for pattern in required): return archetype
    return "UNCLASSIFIED"
