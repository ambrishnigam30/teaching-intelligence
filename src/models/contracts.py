from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

class AssuranceGate(IntEnum):
    DISCOVERED = 0
    SOURCE_READY = 1
    EVIDENCE_READY = 2
    KNOWLEDGE_READY = 3
    TEACHER_READY = 4
    RUNTIME_READY = 5
    EFFICACY_VALIDATED = 6

class SourceFile(BaseModel):
    file_id: str
    name: str
    source_root_id: str
    virtual_paths: list[str] = Field(min_length=1)
    sha256: str | None = None
    rights_status: str
    archetype: str = "UNCLASSIFIED"
    chapters: list[str] = Field(default_factory=list)
    exam_scope: Literal["JEE_MAIN", "JEE_ADVANCED", "BOTH", "UNKNOWN"] = "UNKNOWN"

class Question(BaseModel):
    question_id: str
    source_file_id: str
    page_number: int = Field(ge=1)
    stem: str
    options: list[str] = Field(default_factory=list)
    bounding_box: list[float] | None = None  # [ymin, xmin, ymax, xmax] in 0..1000 scale
    diagram_ids: list[str] = Field(default_factory=list)
    question_type: str = "SINGLE_CHOICE"
    exam_scope: Literal["JEE_MAIN", "JEE_ADVANCED", "BOTH", "UNKNOWN"] = "UNKNOWN"
    official_key: str | None = None
    worked_solution: str | None = None
    passage_id: str | None = None
    exercise_id: str | None = None
    question_number: int | None = None
    skills: list[str] = Field(default_factory=list)  # S1 to S7
    status: Literal["ACTIVE", "QUARANTINED"] = "ACTIVE"
    quarantine_reason: str | None = None
    confidence: float = 0.85

    @field_validator("stem")
    @classmethod
    def no_empty_stem(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question stem is required")
        return value

class VerificationRecord(BaseModel):
    question_id: str
    transcription_provider: str
    blind_solver_provider: str
    official_key: str | None = None
    blind_answer: str | None = None
    symbolic_verified: bool = False
    chemical_verified: bool = False
    outcome: Literal["PASS", "TIEBREAK", "QUARANTINED", "PENDING"]

    @field_validator("blind_solver_provider")
    @classmethod
    def separate_families(cls, value: str, info):
        author = info.data.get("transcription_provider", "").split("_", 1)[0]
        solver = value.split("_", 1)[0]
        if author and author == solver:
            raise ValueError("blind solver must be a different provider family")
        return value


class QuestionVerificationRecord(BaseModel):
    question_id: str
    file_id: str
    source_hash: str | None = None
    page_numbers: list[int] = Field(default_factory=list)
    bounding_box: list[float] | None = None  # [ymin, xmin, ymax, xmax] in 0..1000
    stem: str
    options: list[str] = Field(default_factory=list)
    diagram_ids: list[str] = Field(default_factory=list)
    passage_id: str | None = None
    question_type: str = "SINGLE_CHOICE"
    exam_scope: Literal["JEE_MAIN", "JEE_ADVANCED", "BOTH", "UNKNOWN"] = "UNKNOWN"
    chapters: list[str] = Field(default_factory=list)
    candidate_solution: str | None = None
    final_answer: str | None = None
    solver_family: str | None = None
    solver_model: str | None = None
    verification_family: str | None = None
    verification_output: str | None = None
    symbolic_verified: bool = False
    chemical_verified: bool = False
    official_key: str | None = None
    key_source_location: str | None = None
    status: Literal[
        "PENDING",
        "SOLVED_UNVERIFIED",
        "VERIFIED_CORRECT",
        "CONFLICTED",
        "INSUFFICIENT_EVIDENCE",
        "UNSOLVED",
        "REQUIRES_EXPERT_REVIEW",
    ] = "PENDING"
    transition_history: list[dict[str, Any]] = Field(default_factory=list)
    quarantine_reason: str | None = None


class WorkedSolution5Phase(BaseModel):
    phase_1_dissect: str
    phase_2_select: str
    phase_3_execute: str
    phase_4_trap_audit: str
    phase_5_sanity_check: str

class GraduatedHint3Level(BaseModel):
    level_1_attention: str
    level_2_concept: str
    level_3_procedure: str
    smart_chips: list[str] = Field(default_factory=list)

class WhiteboardVectorCommand(BaseModel):
    command_id: str
    action: Literal["draw_axes", "vector", "spring", "draw_molecule", "reason_note", "highlight", "clear"]
    coordinates: list[float] = Field(default_factory=list)
    label: str | None = None
    color: str | None = None

class NinePointConceptStandard(BaseModel):
    canonical_definition: str
    first_principles_derivation: str
    governing_equations: list[str] = Field(default_factory=list)
    boundary_conditions: list[str] = Field(default_factory=list)
    jee_advanced_traps: list[str] = Field(default_factory=list)
    cross_concept_bridges: list[str] = Field(default_factory=list)
    visual_mental_models: list[str] = Field(default_factory=list)
    historical_coaching_insights: list[str] = Field(default_factory=list)
    dimensional_limiting_sanity_checks: list[str] = Field(default_factory=list)

class ConceptPackage(BaseModel):
    chapter: str
    evidence_ids: list[str]
    capabilities: dict[str, dict] = Field(min_length=18)
    nine_point_standard: NinePointConceptStandard | None = None
    worked_solutions: dict[str, WorkedSolution5Phase] = Field(default_factory=dict)
    graduated_hints: dict[str, GraduatedHint3Level] = Field(default_factory=dict)
    whiteboard_commands: list[WhiteboardVectorCommand] = Field(default_factory=list)
    bilingual_audio_cues: dict[str, str] = Field(default_factory=dict)
    assurance_gate: int = 4
