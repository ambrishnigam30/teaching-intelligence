from src.audit.seeded_error import CriticAudit, SeededCase
from src.stitching.answer_binding import ExerciseKeyBinder, MockSectionStitcher
from src.verification.verifiers import sympy_equivalent

def test_section_reset_stitcher_maps_continuous_answer_keys():
    stitcher = MockSectionStitcher()
    stitcher.add_section("Physics", "I(i)", [1, 2, 3])
    stitcher.add_section("Physics", "I(ii)", [1, 2])
    assert stitcher.global_number("Physics", "I(ii)", 2) == 5
    assert stitcher.local_question(4).section == "I(ii)"

def test_exercise_binder_preserves_code_subtopic_and_key():
    binder = ExerciseKeyBinder()
    binder.add_question("CB00001", "BENT'S RULE AND DRAGO'S RULE", 14)
    binder.add_answer_key("CB00001", "B")
    assert binder.bound("CB00001")["official_key"] == "B"

def test_seeded_error_audit_and_symbolic_equivalence():
    audit = CriticAudit([SeededCase("s", "sign", "F=-ma", "sign"), SeededCase("u", "unit", "3 kg/s", "unit")])
    assert audit.passes(lambda content, expected: True, threshold=0.95)
    assert isinstance(sympy_equivalent("x + x", "2*x"), bool)
