"""Export compiler packages and question items to TypeScript/Zod-compatible wire JSON schemas."""
from __future__ import annotations

import json
from typing import Any

from src.models.contracts import ConceptPackage, Question

def export_question_to_wire(question: Question) -> dict[str, Any]:
    """Serializes a Question model to a TypeScript/Zod runtime contract."""
    return {
        "questionId": question.question_id,
        "sourceFileId": question.source_file_id,
        "pageNumber": question.page_number,
        "stem": question.stem,
        "options": question.options,
        "boundingBox": question.bounding_box,
        "diagramIds": question.diagram_ids,
        "questionType": question.question_type,
        "examScope": question.exam_scope,
        "officialKey": question.official_key,
        "workedSolution": question.worked_solution,
        "passageId": question.passage_id,
        "exerciseId": question.exercise_id,
        "questionNumber": question.question_number,
        "skills": question.skills,
        "status": question.status,
        "quarantineReason": question.quarantine_reason,
        "confidence": question.confidence,
    }

def export_concept_package_to_wire(pkg: ConceptPackage) -> dict[str, Any]:
    """Serializes a ConceptPackage to a TypeScript/Zod runtime contract."""
    nine_point = None
    if pkg.nine_point_standard:
        nps = pkg.nine_point_standard
        nine_point = {
            "canonicalDefinition": nps.canonical_definition,
            "firstPrinciplesDerivation": nps.first_principles_derivation,
            "governingEquations": nps.governing_equations,
            "boundaryConditions": nps.boundary_conditions,
            "jeeAdvancedTraps": nps.jee_advanced_traps,
            "crossConceptBridges": nps.cross_concept_bridges,
            "visualMentalModels": nps.visual_mental_models,
            "historicalCoachingInsights": nps.historical_coaching_insights,
            "dimensionalLimitingSanityChecks": nps.dimensional_limiting_sanity_checks,
        }

    solutions: dict[str, dict[str, str]] = {}
    for qid, sol in pkg.worked_solutions.items():
        solutions[qid] = {
            "phase1Dissect": sol.phase_1_dissect,
            "phase2Select": sol.phase_2_select,
            "phase3Execute": sol.phase_3_execute,
            "phase4TrapAudit": sol.phase_4_trap_audit,
            "phase5SanityCheck": sol.phase_5_sanity_check,
        }

    hints: dict[str, dict[str, Any]] = {}
    for qid, h in pkg.graduated_hints.items():
        hints[qid] = {
            "level1Attention": h.level_1_attention,
            "level2Concept": h.level_2_concept,
            "level3Procedure": h.level_3_procedure,
            "smartChips": h.smart_chips,
        }

    commands = [
        {
            "commandId": cmd.command_id,
            "action": cmd.action,
            "coordinates": cmd.coordinates,
            "label": cmd.label,
            "color": cmd.color,
        }
        for cmd in pkg.whiteboard_commands
    ]

    return {
        "chapterId": pkg.chapter,
        "assuranceGate": pkg.assurance_gate,
        "evidenceIds": pkg.evidence_ids,
        "capabilities": pkg.capabilities,
        "ninePointStandard": nine_point,
        "workedSolutions": solutions,
        "graduatedHints": hints,
        "whiteboardCommands": commands,
        "bilingualAudioCues": pkg.bilingual_audio_cues,
    }

def export_concept_package_json(pkg: ConceptPackage, indent: int = 2) -> str:
    """Exports ConceptPackage as formatted JSON string."""
    return json.dumps(export_concept_package_to_wire(pkg), indent=indent, ensure_ascii=False)
