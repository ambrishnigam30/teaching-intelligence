"""Test cross-page question reconstruction, comprehension passage buffering, and answer key binding."""
from src.stitching.answer_binding import DocumentRelationshipBinder
from src.stitching.passage_buffer import PassageBuffer

def test_split_question_across_pages_buffered_and_merged():
    buf = PassageBuffer("doc_kinematics")

    # Page 1: Incomplete question ending with dangling stem and only 2 options
    page_1_raw = [
        {
            "question_number": 14,
            "stem": "A particle of mass m moves in a central field where the potential energy is given by",
            "options": ["(A) U(r) = -k/r", "(B) U(r) = kr^2"],
            "question_type": "SINGLE_CHOICE",
        }
    ]
    emitted_p1 = buf.process_page_items(1, page_1_raw, page_markdown="Some text on page 1")
    # Should be held in buffer, not emitted yet
    assert len(emitted_p1) == 0

    # Page 2: Continuation options
    page_2_raw = [
        {
            "stem": "",
            "options": ["(C) U(r) = k*ln(r)", "(D) U(r) = 0"],
            "question_type": "SINGLE_CHOICE",
        }
    ]
    emitted_p2 = buf.process_page_items(2, page_2_raw, page_markdown="Top of page 2")
    assert len(emitted_p2) == 1
    merged_q = emitted_p2[0]
    assert merged_q["question_number"] == 14
    assert len(merged_q["options"]) == 4
    assert "(C)" in merged_q["options"][2]
    assert "(D)" in merged_q["options"][3]

def test_multi_question_comprehension_passage_association():
    buf = PassageBuffer("doc_thermo")

    passage_text = "Paragraph for Questions 21 to 23: An ideal monoatomic gas undergoes a cycle ABCDA."
    p1_items = [
        {"question_number": 21, "stem": "The work done in path AB is", "options": ["(A) W0", "(B) 2W0", "(C) 3W0", "(D) 4W0"]},
        {"question_number": 22, "stem": "The heat absorbed in path BC is", "options": ["(A) Q0", "(B) 3Q0", "(C) 4Q0", "(D) 5Q0"]},
        {"question_number": 23, "stem": "The total efficiency is", "options": ["(A) 25%", "(B) 50%", "(C) 75%", "(D) 10%"]},
        {"question_number": 24, "stem": "An independent question on entropy", "options": ["(A) 0", "(B) 1", "(C) 2", "(D) 3"]},
    ]

    emitted = buf.process_page_items(1, p1_items, page_markdown=passage_text)
    assert len(emitted) == 4

    p21, p22, p23, p24 = emitted
    # Q21-23 should share common passage_id
    assert p21["passage_id"] is not None
    assert p21["passage_id"] == p22["passage_id"] == p23["passage_id"]
    # Q24 is outside the range 21 to 23
    assert p24["passage_id"] is None

def test_document_relationship_binder_dense_key_grid():
    binder = DocumentRelationshipBinder()
    key_text = """
    ANSWER KEY
    EXERCISE-I
    1. (A) 2. (C) 3. (B) 4. (D) 5. (A)
    6. (C) 7. (B) 8. (D) 9. (A) 10. (C)
    EXERCISE-II
    1. (B, D) 2. (A, C) 3. 4.50
    """
    count = binder.ingest_answer_keys(key_text)
    assert count >= 12

    # Bind question from Exercise I
    q1 = {"question_number": 2, "exercise_id": "EXERCISE-I", "stem": "What is acceleration?"}
    bound_q1 = binder.bind_question(q1)
    assert bound_q1["official_key"] == "C"

    # Bind question from Exercise II (multi-correct)
    q2 = {"question_number": 1, "exercise_id": "EXERCISE-II", "stem": "Select correct statements"}
    bound_q2 = binder.bind_question(q2)
    assert "B" in bound_q2["official_key"] and "D" in bound_q2["official_key"]
