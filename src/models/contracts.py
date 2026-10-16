from __future__ import annotations

from enum import IntEnum
from typing import Literal
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

class Question(BaseModel):
    question_id: str
    source_file_id: str
    page_number: int = Field(ge=1)
    stem: str
    options: list[str] = Field(default_factory=list)
    status: Literal["ACTIVE", "QUARANTINED"] = "ACTIVE"
    quarantine_reason: str | None = None

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
