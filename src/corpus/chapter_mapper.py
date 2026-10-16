from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import re

class ChapterPriority(IntEnum):
    TIER_1 = 1
    TIER_2 = 2

# Canonical JEE Main/Advanced spine. IDs are stable artifact keys, not display labels.
SPINE: tuple[str, ...] = (
    "units_dimensions", "kinematics", "laws_of_motion_friction", "work_energy_power",
    "circular_motion", "com_collisions", "rotational_mechanics", "shm", "gravitation",
    "properties_of_matter", "elasticity", "fluid_mechanics", "thermal_properties", "thermodynamics_physics",
    "kinetic_theory", "waves_sound", "electrostatics", "capacitors", "current_electricity",
    "magnetism", "emi_ac", "electromagnetic_waves", "ray_optics", "wave_optics", "modern_physics", "semiconductors",
    "experimental_physics", "mole_concept", "atomic_structure", "periodic_properties",
    "chemical_bonding", "states_of_matter", "thermodynamics_chemistry", "equilibrium",
    "redox_reactions", "solutions", "electrochemistry", "chemical_kinetics", "surface_chemistry",
    "metallurgy", "hydrogen", "s_block", "p_block", "d_f_block", "coordination_compounds",
    "environmental_chemistry", "general_organic_chemistry", "hydrocarbons", "haloalkanes",
    "alcohols_phenols_ethers", "aldehydes_ketones_acids", "amines", "biomolecules_polymers",
    "chemistry_everyday_life", "solid_state", "purification_analysis", "qualitative_analysis", "sets_relations",
    "functions", "complex_numbers", "quadratic_equations", "sequences_series", "binomial_theorem",
    "permutations_combinations", "mathematical_induction", "matrices_determinants", "probability",
    "statistics", "trigonometry", "inverse_trigonometry", "straight_lines", "circles", "conics",
    "vectors", "three_dimensional_geometry", "limits_continuity_differentiability", "application_of_derivatives",
    "integrals", "differential_equations", "area_under_curve", "mathematical_reasoning", "linear_programming",
)

TIER_1: frozenset[str] = frozenset({
    "chemical_bonding", "atomic_structure", "complex_numbers", "application_of_derivatives", "shm",
    "units_dimensions", "kinematics", "laws_of_motion_friction", "work_energy_power", "circular_motion",
    "com_collisions", "rotational_mechanics", "mole_concept", "periodic_properties", "thermodynamics_chemistry",
    "quadratic_equations", "sequences_series", "permutations_combinations", "binomial_theorem", "sets_relations",
})

ALIASES = {
    "simple harmonic motion": "shm", "shm": "shm", "chemical bonding": "chemical_bonding",
    "atomic structure": "atomic_structure", "complex number": "complex_numbers",
    "application of derivatives": "application_of_derivatives", "units and dimensions": "units_dimensions",
    "units & dimensions": "units_dimensions", "laws of motion": "laws_of_motion_friction",
    "friction": "laws_of_motion_friction", "work energy power": "work_energy_power",
    "centre of mass": "com_collisions", "center of mass": "com_collisions",
    "rotational mechanics": "rotational_mechanics", "mole concept": "mole_concept",
    "periodic properties": "periodic_properties", "thermodynamics": "thermodynamics_chemistry",
    "quadratic equations": "quadratic_equations", "sequences and series": "sequences_series",
    "p&c": "permutations_combinations", "permutation": "permutations_combinations",
    "binomial theorem": "binomial_theorem", "sets and relations": "sets_relations",
}

@dataclass(frozen=True)
class ChapterMapper:
    spine: tuple[str, ...] = SPINE

    def priority(self, chapter: str) -> ChapterPriority:
        if chapter not in self.spine:
            raise KeyError(f"Unknown canonical chapter: {chapter}")
        return ChapterPriority.TIER_1 if chapter in TIER_1 else ChapterPriority.TIER_2

    def syllabus_order(self, chapter: str) -> int:
        return self.spine.index(chapter)

    def map_text(self, text: str) -> list[str]:
        normalized = re.sub(r"[_-]+", " ", text.lower())
        matches = {chapter for alias, chapter in ALIASES.items() if alias in normalized}
        return sorted(matches, key=self.syllabus_order)

    def work_key(self, chapters: list[str]) -> tuple[int, int]:
        if not chapters:
            return (int(ChapterPriority.TIER_2), len(self.spine))
        return min((int(self.priority(c)), self.syllabus_order(c)) for c in chapters)
