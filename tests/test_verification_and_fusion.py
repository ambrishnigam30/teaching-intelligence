import pytest
from src.compiler.fusion import ChapterEvidence, ChapterFusionCompiler
from src.models.contracts import VerificationRecord
from src.verification.assurance import AssuranceEngine

def test_cross_family_verification_and_tiebreak_quarantine():
    record = VerificationRecord(question_id="q", transcription_provider="gemini_1", blind_solver_provider="groq_1", official_key="A", blind_answer="B", symbolic_verified=True, outcome="PENDING")
    assert AssuranceEngine().evaluate(record, tiebreak_agrees=False).outcome == "QUARANTINED"
    with pytest.raises(ValueError):
        VerificationRecord(question_id="q", transcription_provider="gemini_1", blind_solver_provider="gemini_2", outcome="PENDING")

def test_chapter_compiler_fuses_multiple_archetypes_and_contracts_18_capabilities():
    evidence = [
      ChapterEvidence(chapter="chemical_bonding", archetype="ALLEN_THEORY", artifact_id="theory", content={}, gate=3),
      ChapterEvidence(chapter="chemical_bonding", archetype="REFERENCE_TEXTBOOK", artifact_id="book", content={}, gate=3),
      ChapterEvidence(chapter="chemical_bonding", archetype="ALLEN_EXERCISE", artifact_id="exercise", content={}, gate=3),
    ]
    package = ChapterFusionCompiler().compile("chemical_bonding", evidence)
    assert len(package.capabilities) == 18
    assert {"theory", "book", "exercise"} == set(package.evidence_ids)
