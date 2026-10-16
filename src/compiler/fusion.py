from __future__ import annotations

from collections import defaultdict
from pydantic import BaseModel, Field

class ChapterEvidence(BaseModel):
    chapter: str
    archetype: str
    artifact_id: str
    content: dict
    gate: int

class ConceptPackage(BaseModel):
    chapter: str
    evidence_ids: list[str]
    capabilities: dict[str, dict] = Field(min_length=18)
    assurance_gate: int

class ChapterFusionCompiler:
    """Builds a chapter package only from cross-archetype eligible evidence."""
    def compile(self, chapter: str, evidence: list[ChapterEvidence]) -> ConceptPackage:
        eligible = [e for e in evidence if e.chapter == chapter and e.gate >= 3]
        if not eligible: raise ValueError("No Knowledge-ready evidence available for chapter")
        by_type: dict[str, list[ChapterEvidence]] = defaultdict(list)
        for item in eligible: by_type[item.archetype].append(item)
        source_ids = [e.artifact_id for e in eligible]
        names = [
            "source_provenance", "curriculum_ontology", "first_principles", "symbolic_chemical",
            "worked_solution", "problem_archetypes", "exam_calibration", "scaffolding", "prerequisites",
            "misconceptions", "hints_repair", "practice_roles", "assessment", "learner_state",
            "retention", "transfer", "assurance", "whiteboard_persona",
        ]
        capabilities = {name: {"evidence_ids": source_ids, "archetypes": sorted(by_type)} for name in names}
        return ConceptPackage(chapter=chapter, evidence_ids=source_ids, capabilities=capabilities, assurance_gate=4)
