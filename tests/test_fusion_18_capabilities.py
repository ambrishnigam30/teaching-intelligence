"""Test ChapterFusionCompiler synthesis of 18 capabilities and TypeScript/Zod wire serialization."""
import json
from src.compiler.export_schemas import (
    export_concept_package_json,
    export_concept_package_to_wire,
    export_question_to_wire,
)
from src.compiler.fusion import ChapterEvidence, ChapterFusionCompiler
from src.models.contracts import Question

def test_chapter_fusion_compiler_18_capabilities_and_pedagogy():
    compiler = ChapterFusionCompiler()

    evidence = [
        ChapterEvidence(
            chapter="simple_harmonic_motion",
            archetype="ALLEN_THEORY",
            artifact_id="shm_theory_01",
            content={
                "equations": ["d2x/dt2 + omega^2 * x = 0", "T = 2*pi*sqrt(m/k)"],
                "derivation": "From Hooke's law F = -kx and Newton's second law m*d2x/dt2 = -kx.",
            },
            gate=3,
        ),
        ChapterEvidence(
            chapter="simple_harmonic_motion",
            archetype="ALLEN_EXERCISE",
            artifact_id="shm_exercise_01",
            content={
                "questions": [
                    {
                        "question_id": "shm_q1",
                        "stem": "A block of mass m is attached to a spring of spring constant k. Find the time period.",
                        "options": ["(A) 2*pi*sqrt(m/k)", "(B) 2*pi*sqrt(k/m)"],
                    }
                ]
            },
            gate=3,
        ),
    ]

    pkg = compiler.compile("simple_harmonic_motion", evidence)

    # 1. Assert all 18 capabilities present
    assert len(pkg.capabilities) == 18
    for cap_name in ChapterFusionCompiler.CAPABILITY_NAMES:
        assert cap_name in pkg.capabilities
        assert pkg.capabilities[cap_name]["status"] == "VALIDATED"

    # 2. Assert 9-point concept standard
    nps = pkg.nine_point_standard
    assert nps is not None
    assert "Simple Harmonic Motion" in nps.canonical_definition
    assert "Hooke's law" in nps.first_principles_derivation
    assert len(nps.governing_equations) >= 2
    assert len(nps.jee_advanced_traps) >= 1
    assert len(nps.boundary_conditions) >= 1

    # 3. Assert 5-phase worked solutions
    assert "shm_q1" in pkg.worked_solutions
    sol = pkg.worked_solutions["shm_q1"]
    assert sol.phase_1_dissect
    assert sol.phase_2_select
    assert sol.phase_3_execute
    assert sol.phase_4_trap_audit
    assert sol.phase_5_sanity_check

    # 4. Assert 3-level graduated hints
    assert "shm_q1" in pkg.graduated_hints
    hints = pkg.graduated_hints["shm_q1"]
    assert hints.level_1_attention
    assert hints.level_2_concept
    assert hints.level_3_procedure
    assert len(hints.smart_chips) >= 1

    # 5. Assert whiteboard vector commands
    assert len(pkg.whiteboard_commands) >= 3
    assert any(cmd.action == "draw_axes" for cmd in pkg.whiteboard_commands)
    assert any(cmd.action == "vector" for cmd in pkg.whiteboard_commands)

    # 6. Assert bilingual teacher cues
    assert "intro" in pkg.bilingual_audio_cues
    assert "trap_alert" in pkg.bilingual_audio_cues

    # 7. Test TypeScript wire serialization
    wire_dict = export_concept_package_to_wire(pkg)
    assert wire_dict["chapterId"] == "simple_harmonic_motion"
    assert wire_dict["assuranceGate"] == 4
    assert len(wire_dict["capabilities"]) == 18
    assert "shm_q1" in wire_dict["workedSolutions"]

    json_str = export_concept_package_json(pkg)
    parsed = json.loads(json_str)
    assert parsed["chapterId"] == "simple_harmonic_motion"

def test_export_question_to_wire():
    q = Question(
        question_id="q_101",
        source_file_id="src_doc_42",
        page_number=3,
        stem="What is the force?",
        options=["(A) 5 N", "(B) 10 N"],
        bounding_box=[100.0, 50.0, 300.0, 450.0],
        diagram_ids=["diag_101_01"],
        question_type="SINGLE_CHOICE",
        official_key="A",
        skills=["S1", "S3"],
    )
    wire = export_question_to_wire(q)
    assert wire["questionId"] == "q_101"
    assert wire["officialKey"] == "A"
    assert wire["diagramIds"] == ["diag_101_01"]
    assert wire["skills"] == ["S1", "S3"]
    assert wire["boundingBox"] == [100.0, 50.0, 300.0, 450.0]
