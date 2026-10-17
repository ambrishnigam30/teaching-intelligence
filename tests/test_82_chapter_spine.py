"""Test 82-chapter canonical spine mapping and coaching alias disambiguation."""
import pytest
from src.corpus.chapter_mapper import ChapterMapper, CANONICAL_CHAPTER_NAMES

def test_82_canonical_spine_count():
    assert len(CANONICAL_CHAPTER_NAMES) == 82
    # Verify key subject chapters exist
    assert "shm" in CANONICAL_CHAPTER_NAMES
    assert "thermodynamics_physics" in CANONICAL_CHAPTER_NAMES
    assert "thermodynamics_chemistry" in CANONICAL_CHAPTER_NAMES
    assert "general_organic_chemistry" in CANONICAL_CHAPTER_NAMES
    assert "complex_numbers" in CANONICAL_CHAPTER_NAMES
    assert "three_dimensional_geometry" in CANONICAL_CHAPTER_NAMES

def test_no_chemistry_solutions_poisoning_in_math_or_physics():
    mapper = ChapterMapper()
    # Complex numbers solutions should NOT map to chemistry solutions
    math_sol = mapper.map_file("Mathematics/Complex Numbers/Complex Number Exercise Solutions.pdf")
    assert "complex_numbers" in math_sol
    assert "solutions" not in math_sol

    # Physics kinematics solutions should NOT map to chemistry solutions
    phys_sol = mapper.map_file("Physics/Mechanics/Kinematics Advanced Solutions.pdf")
    assert "kinematics" in phys_sol
    assert "solutions" not in phys_sol

def test_coaching_acronyms_organic_chemistry():
    mapper = ChapterMapper()
    assert "general_organic_chemistry" in mapper.map_file("Allen_Chemistry/ORM-1_Notes.pdf")
    assert "hydrocarbons" in mapper.map_file("Allen_Chemistry/ORM-II_Alkyl_Halides.pdf")
    assert "alcohols_phenols_ethers" in mapper.map_file("Allen_Chemistry/ORM-III_Alcohols.pdf")
    assert "aldehydes_ketones_acids" in mapper.map_file("Allen_Chemistry/ORM-IV_Carbonyls.pdf")
    assert "general_organic_chemistry" in mapper.map_file("Resonance/GOC_Exercise_1.pdf")

def test_coaching_acronyms_mathematics():
    mapper = ChapterMapper()
    assert "application_of_derivatives" in mapper.map_file("Allen_Maths/MOD_Methods_of_Differentiation.pdf")
    three_d = mapper.map_file("Allen_Maths/3-D_Geometry_Sheet.pdf")
    assert "three_dimensional_geometry" in three_d
    assert "permutations_combinations" in mapper.map_file("Maths/P&C_Exercise.pdf")
    assert "inverse_trigonometry" in mapper.map_file("Maths/ITF_Module.pdf")

def test_true_chemistry_solutions_mapping():
    mapper = ChapterMapper()
    assert "solutions" in mapper.map_file("Chemistry/Physical/Liquid_Solutions_Colligative_Properties.pdf")
    assert "solutions" in mapper.map_file("Chemistry/Raoults_Law_Ideal_Solutions.pdf")
