from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import re

class ChapterPriority(IntEnum):
    TIER_0 = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3

# Canonical JEE Main/Advanced spine (82 chapters). IDs are stable artifact keys, not display labels.
SPINE: tuple[str, ...] = (
    # Physics (27)
    "units_dimensions", "kinematics", "laws_of_motion_friction", "work_energy_power",
    "circular_motion", "com_collisions", "rotational_mechanics", "shm", "gravitation",
    "properties_of_matter", "elasticity", "fluid_mechanics", "thermal_properties", "thermodynamics_physics",
    "kinetic_theory", "waves_sound", "electrostatics", "capacitors", "current_electricity",
    "magnetism", "emi_ac", "electromagnetic_waves", "ray_optics", "wave_optics", "modern_physics", "semiconductors",
    "experimental_physics",
    # Chemistry (30)
    "mole_concept", "atomic_structure", "periodic_properties",
    "chemical_bonding", "states_of_matter", "thermodynamics_chemistry", "equilibrium",
    "redox_reactions", "solutions", "electrochemistry", "chemical_kinetics", "surface_chemistry",
    "metallurgy", "hydrogen", "s_block", "p_block", "d_f_block", "coordination_compounds",
    "environmental_chemistry", "general_organic_chemistry", "hydrocarbons", "haloalkanes",
    "alcohols_phenols_ethers", "aldehydes_ketones_acids", "amines", "biomolecules_polymers",
    "chemistry_everyday_life", "solid_state", "purification_analysis", "qualitative_analysis",
    # Mathematics (25)
    "sets_relations", "functions", "complex_numbers", "quadratic_equations", "sequences_series", "binomial_theorem",
    "permutations_combinations", "mathematical_induction", "matrices_determinants", "probability",
    "statistics", "trigonometry", "inverse_trigonometry", "straight_lines", "circles", "conics",
    "vectors", "three_dimensional_geometry", "limits_continuity_differentiability", "application_of_derivatives",
    "integrals", "differential_equations", "area_under_curve", "mathematical_reasoning", "linear_programming",
)

CANONICAL_CHAPTER_NAMES = SPINE

TIER_0: frozenset[str] = frozenset({
    "shm", "chemical_bonding", "quadratic_equations"
})

TIER_1: frozenset[str] = frozenset({
    "units_dimensions", "kinematics", "laws_of_motion_friction", "work_energy_power",
    "circular_motion", "com_collisions", "rotational_mechanics", "mole_concept",
    "atomic_structure", "periodic_properties", "thermodynamics_chemistry", "complex_numbers",
    "sequences_series", "permutations_combinations", "binomial_theorem", "sets_relations"
})

TIER_2: frozenset[str] = frozenset({
    "gravitation", "properties_of_matter", "elasticity", "fluid_mechanics", "thermal_properties",
    "thermodynamics_physics", "kinetic_theory", "waves_sound", "equilibrium", "redox_reactions",
    "general_organic_chemistry", "hydrocarbons", "s_block", "p_block", "trigonometry", "straight_lines",
    "circles", "conics", "limits_continuity_differentiability", "statistics", "electrostatics",
    "capacitors", "current_electricity", "magnetism", "emi_ac", "solutions", "electrochemistry",
    "chemical_kinetics", "d_f_block", "coordination_compounds", "functions", "inverse_trigonometry",
    "integrals", "area_under_curve", "differential_equations", "electromagnetic_waves", "ray_optics",
    "wave_optics", "modern_physics", "semiconductors", "experimental_physics", "haloalkanes",
    "alcohols_phenols_ethers", "aldehydes_ketones_acids", "amines", "biomolecules_polymers",
    "purification_analysis", "qualitative_analysis", "matrices_determinants", "vectors",
    "three_dimensional_geometry", "probability"
})

TIER_3: frozenset[str] = frozenset({
    "states_of_matter", "surface_chemistry", "metallurgy", "hydrogen", "environmental_chemistry",
    "chemistry_everyday_life", "solid_state", "mathematical_induction", "mathematical_reasoning",
    "linear_programming"
})

# Comprehensive aliases, abbreviations, folder names and coaching codes across all 82 chapters
ALIASES: dict[str, str] = {
    # Physics
    "units and dimensions": "units_dimensions", "units & dimensions": "units_dimensions", "units dimensions": "units_dimensions", "unit and dimension": "units_dimensions", "dimensional analysis": "units_dimensions", "error analysis": "units_dimensions", "vernier caliper": "units_dimensions", "screw gauge": "units_dimensions",
    "kinematics": "kinematics", "motion in a straight line": "kinematics", "motion in 1d": "kinematics", "motion in 2d": "kinematics", "projectile motion": "kinematics", "relative motion": "kinematics", "rectilinear": "kinematics", "motion in a plane": "kinematics",
    "laws of motion": "laws_of_motion_friction", "newton s laws": "laws_of_motion_friction", "newtons laws": "laws_of_motion_friction", "nlm": "laws_of_motion_friction", "friction": "laws_of_motion_friction", "pseudo force": "laws_of_motion_friction", "constraint motion": "laws_of_motion_friction",
    "work energy power": "work_energy_power", "work power energy": "work_energy_power", "wep": "work_energy_power", "work and energy": "work_energy_power",
    "circular motion": "circular_motion", "banking of roads": "circular_motion", "centripetal": "circular_motion",
    "centre of mass": "com_collisions", "center of mass": "com_collisions", "com": "com_collisions", "collisions": "com_collisions", "collision": "com_collisions", "impulse": "com_collisions",
    "rotational mechanics": "rotational_mechanics", "rotational motion": "rotational_mechanics", "rigid body dynamics": "rotational_mechanics", "rbd": "rotational_mechanics", "moment of inertia": "rotational_mechanics", "angular momentum": "rotational_mechanics", "rolling motion": "rotational_mechanics",
    "simple harmonic motion": "shm", "shm": "shm", "oscillations": "shm", "oscillation": "shm", "spring mass": "shm",
    "gravitation": "gravitation", "gravity": "gravitation", "kepler": "gravitation",
    "properties of matter": "properties_of_matter", "mechanical properties of matter": "properties_of_matter", "surface tension": "properties_of_matter", "viscosity": "properties_of_matter", "capillarity": "properties_of_matter",
    "elasticity": "elasticity", "stress strain": "elasticity", "hooke s law": "elasticity", "young s modulus": "elasticity",
    "fluid mechanics": "fluid_mechanics", "fluids": "fluid_mechanics", "fluid statics": "fluid_mechanics", "fluid dynamics": "fluid_mechanics", "bernoulli": "fluid_mechanics", "buoyancy": "fluid_mechanics",
    "thermal properties": "thermal_properties", "calorimetry": "thermal_properties", "thermal expansion": "thermal_properties", "heat transfer": "thermal_properties", "conduction": "thermal_properties", "radiation": "thermal_properties",
    "thermodynamics physics": "thermodynamics_physics", "heat and thermodynamics": "thermodynamics_physics", "heat thermodynamics": "thermodynamics_physics", "thermal physics": "thermodynamics_physics", "carnot engine": "thermodynamics_physics", "first law of thermodynamics": "thermodynamics_physics", "second law of thermodynamics": "thermodynamics_physics",
    "kinetic theory": "kinetic_theory", "ktg": "kinetic_theory", "kinetic theory of gases": "kinetic_theory",
    "waves and sound": "waves_sound", "sound waves": "waves_sound", "wave optics": "wave_optics", "string waves": "waves_sound", "doppler effect": "waves_sound", "organ pipe": "waves_sound", "standing waves": "waves_sound", "beats": "waves_sound", "wave on a string": "waves_sound",
    "electrostatics": "electrostatics", "electric field": "electrostatics", "electric potential": "electrostatics", "coulomb": "electrostatics", "gauss law": "electrostatics",
    "capacitors": "capacitors", "capacitor": "capacitors", "capacitance": "capacitors", "dielectrics": "capacitors",
    "current electricity": "current_electricity", "electric current": "current_electricity", "kirchhoff": "current_electricity", "potentiometer": "current_electricity", "wheatstone": "current_electricity", "drift velocity": "current_electricity", "emf": "current_electricity",
    "magnetism": "magnetism", "magnetic effects of current": "magnetism", "moving charges": "magnetism", "moving charges and magnetism": "magnetism", "magnetic field": "magnetism", "biot savart": "magnetism", "ampere s law": "magnetism", "earth magnetism": "magnetism",
    "emi and ac": "emi_ac", "emi": "emi_ac", "electromagnetic induction": "emi_ac", "alternating current": "emi_ac", "ac circuits": "emi_ac", "faraday": "emi_ac", "lenz": "emi_ac",
    "electromagnetic waves": "electromagnetic_waves", "em waves": "electromagnetic_waves", "displacement current": "electromagnetic_waves",
    "ray optics": "ray_optics", "geometrical optics": "ray_optics", "reflection": "ray_optics", "refraction": "ray_optics", "prism": "ray_optics", "optical instruments": "ray_optics", "lenses": "ray_optics",
    "modern physics": "modern_physics", "photoelectric": "modern_physics", "dual nature": "modern_physics", "nuclear physics": "modern_physics", "radioactivity": "modern_physics", "atoms and nuclei": "modern_physics",
    "semiconductors": "semiconductors", "semiconductor": "semiconductors", "logic gates": "semiconductors", "transistor": "semiconductors", "p n junction": "semiconductors", "zener diode": "semiconductors", "principal of communication": "semiconductors", "principles of communication": "semiconductors", "communication systems": "semiconductors",
    "experimental physics": "experimental_physics", "practical physics": "experimental_physics",

    # Chemistry
    "mole concept": "mole_concept", "stoichiometry": "mole_concept", "concentration terms": "mole_concept", "equivalent concept": "mole_concept", "molarity": "mole_concept",
    "atomic structure": "atomic_structure", "structure of atom": "atomic_structure", "bohr model": "atomic_structure", "quantum numbers": "atomic_structure",
    "periodic properties": "periodic_properties", "periodic table": "periodic_properties", "classification of elements": "periodic_properties", "periodicity": "periodic_properties",
    "chemical bonding": "chemical_bonding", "molecular structure": "chemical_bonding", "vsepr": "chemical_bonding", "hybridization": "chemical_bonding", "bent s rule": "chemical_bonding",
    "states of matter": "states_of_matter", "gaseous state": "states_of_matter", "gas laws": "states_of_matter", "van der waals": "states_of_matter",
    "thermodynamics chemistry": "thermodynamics_chemistry", "chemical thermodynamics": "thermodynamics_chemistry", "thermochemistry": "thermodynamics_chemistry", "enthalpy": "thermodynamics_chemistry",
    "equilibrium": "equilibrium", "chemical equilibrium": "equilibrium", "ionic equilibrium": "equilibrium", "ph calculation": "equilibrium", "buffer solution": "equilibrium", "solubility product": "equilibrium",
    "redox reactions": "redox_reactions", "redox": "redox_reactions", "oxidation reduction": "redox_reactions",
    # Specific chemistry solutions aliases (generic "solutions" removed to avoid corrupting Math/Physics solution sheets)
    "liquid solutions": "solutions", "liquid solution": "solutions", "colligative properties": "solutions", "colligative property": "solutions", "raoult": "solutions", "raoults law": "solutions", "ideal solutions": "solutions", "ideal solution": "solutions", "osmotic pressure": "solutions", "van t hoff": "solutions", "depression in freezing": "solutions", "elevation in boiling": "solutions", "henrys law": "solutions",
    "electrochemistry": "electrochemistry", "galvanic cell": "electrochemistry", "electrolytic cell": "electrochemistry", "nernst": "electrochemistry",
    "chemical kinetics": "chemical_kinetics", "rate of reaction": "chemical_kinetics", "order of reaction": "chemical_kinetics", "activation energy": "chemical_kinetics",
    "surface chemistry": "surface_chemistry", "adsorption": "surface_chemistry", "colloids": "surface_chemistry", "catalysis": "surface_chemistry",
    "metallurgy": "metallurgy", "extraction of metals": "metallurgy", "isolation of elements": "metallurgy",
    "hydrogen": "hydrogen", "hydrogen and its compounds": "hydrogen", "heavy water": "hydrogen",
    "s block": "s_block", "s block elements": "s_block", "alkali metals": "s_block", "alkaline earth": "s_block",
    "p block": "p_block", "p block elements": "p_block", "boron carbon": "p_block", "nitrogen oxygen": "p_block", "halogens": "p_block", "noble gases": "p_block",
    "d and f block": "d_f_block", "d & f block": "d_f_block", "d f block": "d_f_block", "transition elements": "d_f_block",
    "coordination compounds": "coordination_compounds", "coordination chemistry": "coordination_compounds", "complex compounds": "coordination_compounds",
    "environmental chemistry": "environmental_chemistry", "pollution": "environmental_chemistry",
    # Organic Reaction Mechanism & Named Reactions
    "general organic chemistry": "general_organic_chemistry", "goc": "general_organic_chemistry", "isomerism": "general_organic_chemistry", "reaction mechanism": "general_organic_chemistry", "resonance effect": "general_organic_chemistry", "resonance structures": "general_organic_chemistry", "hyperconjugation": "general_organic_chemistry", "stereochemistry": "general_organic_chemistry", "orm 1": "general_organic_chemistry", "orm i": "general_organic_chemistry", "orm1": "general_organic_chemistry", "ormi": "general_organic_chemistry",
    "abc": "general_organic_chemistry", "all basic concepts of organic chemistry": "general_organic_chemistry", "grignard": "general_organic_chemistry", "grignard reagent": "general_organic_chemistry", "beckmann": "general_organic_chemistry", "curtius": "general_organic_chemistry", "fries": "general_organic_chemistry", "fries rearrangement": "general_organic_chemistry",
    "hydrocarbons": "hydrocarbons", "alkanes": "hydrocarbons", "alkenes": "hydrocarbons", "alkynes": "hydrocarbons", "aromatic hydrocarbons": "hydrocarbons", "aromatic compounds": "hydrocarbons", "benzene": "hydrocarbons", "orm 2": "hydrocarbons", "orm ii": "hydrocarbons", "orm2": "hydrocarbons", "ormii": "hydrocarbons", "kolbe": "hydrocarbons", "kolbe electrolytic": "hydrocarbons", "wurtz": "hydrocarbons",
    "haloalkanes": "haloalkanes", "haloalkanes and haloarenes": "haloalkanes", "alkyl halides": "haloalkanes", "aryl halides": "haloalkanes", "darzen": "haloalkanes", "darzens": "haloalkanes", "hunsdiecker": "haloalkanes", "finkelstein": "haloalkanes", "swarts": "haloalkanes",
    "alcohols phenols ethers": "alcohols_phenols_ethers", "alcohols": "alcohols_phenols_ethers", "phenols": "alcohols_phenols_ethers", "ethers": "alcohols_phenols_ethers", "orm 3": "alcohols_phenols_ethers", "orm iii": "alcohols_phenols_ethers", "orm3": "alcohols_phenols_ethers", "ormiii": "alcohols_phenols_ethers", "reimer tiemann": "alcohols_phenols_ethers", "reimer": "alcohols_phenols_ethers", "williamson": "alcohols_phenols_ethers", "williamson synthesis": "alcohols_phenols_ethers", "pinacol": "alcohols_phenols_ethers",
    "carbonyl compounds": "aldehydes_ketones_acids", "aldehydes ketones": "aldehydes_ketones_acids", "aldehydes": "aldehydes_ketones_acids", "ketones": "aldehydes_ketones_acids", "carboxylic acids": "aldehydes_ketones_acids", "aldehydes ketones and carboxylic acids": "aldehydes_ketones_acids", "orm 4": "aldehydes_ketones_acids", "orm iv": "aldehydes_ketones_acids", "orm4": "aldehydes_ketones_acids", "ormiv": "aldehydes_ketones_acids",
    "aldol": "aldehydes_ketones_acids", "aldol condensation": "aldehydes_ketones_acids", "cannizzaro": "aldehydes_ketones_acids", "wittig": "aldehydes_ketones_acids", "rosenmund": "aldehydes_ketones_acids", "rosenmund reduction": "aldehydes_ketones_acids", "claisen": "aldehydes_ketones_acids", "claisen condensation": "aldehydes_ketones_acids", "hell volhard": "aldehydes_ketones_acids", "hvz": "aldehydes_ketones_acids", "etard": "aldehydes_ketones_acids", "etard reaction": "aldehydes_ketones_acids", "stephen": "aldehydes_ketones_acids", "stephen reduction": "aldehydes_ketones_acids", "perkin": "aldehydes_ketones_acids", "perkin reaction": "aldehydes_ketones_acids", "baeyer villiger": "aldehydes_ketones_acids", "clemmensen": "aldehydes_ketones_acids", "wolff kishner": "aldehydes_ketones_acids",
    "amines": "amines", "diazonium": "amines", "organic compounds containing nitrogen": "amines", "gabriel": "amines", "gabriel synthesis": "amines", "gabriel phthalimide": "amines", "schmidt": "amines", "schmidt reaction": "amines", "schotten baumann": "amines", "hoffmann bromamide": "amines", "carbylamine": "amines",
    "biomolecules": "biomolecules_polymers", "polymers": "biomolecules_polymers", "carbohydrates": "biomolecules_polymers", "amino acids": "biomolecules_polymers", "proteins": "biomolecules_polymers", "nucleic acids": "biomolecules_polymers",
    "chemistry in everyday life": "chemistry_everyday_life",
    "solid state": "solid_state", "crystal lattice": "solid_state", "unit cell": "solid_state",
    "purification": "purification_analysis", "characterisation of organic": "purification_analysis", "purification of organic": "purification_analysis", "poc": "purification_analysis", "structural identification": "purification_analysis", "sip": "purification_analysis",
    "qualitative analysis": "qualitative_analysis", "salt analysis": "qualitative_analysis", "cation analysis": "qualitative_analysis", "anion analysis": "qualitative_analysis",
    "gst": "states_of_matter", "gas state theory": "states_of_matter", "ideal gases": "states_of_matter", "real gases": "states_of_matter",
    "itc": "mole_concept", "introduction to chemistry": "mole_concept",
    "bin": "periodic_properties", "basic inorganic nomenclature": "periodic_properties",

    # Mathematics
    "sets and relations": "sets_relations", "sets relations": "sets_relations", "sets": "sets_relations", "relations": "sets_relations", "fundamental of mathematics": "sets_relations", "fundamentals of mathematics": "sets_relations", "fom": "sets_relations",
    "functions": "functions", "domain and range": "functions", "relations and functions": "functions",
    "complex numbers": "complex_numbers", "complex number": "complex_numbers", "argand plane": "complex_numbers",
    "quadratic equations": "quadratic_equations", "quadratic equation": "quadratic_equations", "theory of equations": "quadratic_equations",
    "sequences and series": "sequences_series", "sequences series": "sequences_series", "sequence and series": "sequences_series", "sequence series": "sequences_series", "arithmetic progression": "sequences_series", "geometric progression": "sequences_series", "progression": "sequences_series", "progressions": "sequences_series", "ap gp": "sequences_series",
    "binomial theorem": "binomial_theorem", "binomial": "binomial_theorem", "bt": "binomial_theorem",
    "permutations and combinations": "permutations_combinations", "permutations": "permutations_combinations", "combinations": "permutations_combinations", "p&c": "permutations_combinations", "p and c": "permutations_combinations", "permutation": "permutations_combinations",
    "mathematical induction": "mathematical_induction", "pmi": "mathematical_induction",
    "matrices and determinants": "matrices_determinants", "matrices": "matrices_determinants", "determinants": "matrices_determinants", "matrix": "matrices_determinants",
    "probability": "probability", "bayes theorem": "probability",
    "statistics": "statistics", "mean and variance": "statistics",
    "trigonometry": "trigonometry", "trigonometric functions": "trigonometry", "trigonometric equations": "trigonometry", "solution of triangles": "trigonometry", "solution of triangle": "trigonometry", "sot": "trigonometry",
    "inverse trigonometric": "inverse_trigonometry", "inverse trigonometry": "inverse_trigonometry", "itf": "inverse_trigonometry",
    "straight lines": "straight_lines", "straight line": "straight_lines", "pair of straight lines": "straight_lines", "2d coordinate": "straight_lines", "coordinate geometry": "straight_lines",
    "circles": "circles", "circle": "circles",
    "conic sections": "conics", "conic section": "conics", "conics": "conics", "conic": "conics", "parabola": "conics", "ellipse": "conics", "hyperbola": "conics",
    "vectors": "vectors", "vector algebra": "vectors",
    "three dimensional geometry": "three_dimensional_geometry", "3d geometry": "three_dimensional_geometry", "3 d geometry": "three_dimensional_geometry", "3d": "three_dimensional_geometry", "planes and lines": "three_dimensional_geometry", "vector and 3 d": "three_dimensional_geometry", "vector and 3d": "three_dimensional_geometry",
    "limits continuity": "limits_continuity_differentiability", "limits": "limits_continuity_differentiability", "continuity and differentiability": "limits_continuity_differentiability", "lcd": "limits_continuity_differentiability", "continuity & differentiability": "limits_continuity_differentiability", "derivability": "limits_continuity_differentiability",
    "application of derivatives": "application_of_derivatives", "aod": "application_of_derivatives", "maxima and minima": "application_of_derivatives", "tangents and normals": "application_of_derivatives", "tangent & normal": "application_of_derivatives", "tangents": "application_of_derivatives", "monotonocity": "application_of_derivatives", "monotonicity": "application_of_derivatives", "monotoncity": "application_of_derivatives", "mean value theorem": "application_of_derivatives", "lmvt": "application_of_derivatives", "mod": "application_of_derivatives", "methods of differentiation": "application_of_derivatives", "method of differentiation": "application_of_derivatives",
    "indefinite integration": "integrals", "definite integration": "integrals", "integrals": "integrals", "integration": "integrals", "definite integration and its application": "integrals",
    "differential equations": "differential_equations", "differential equation": "differential_equations", "de": "differential_equations",
    "area under curve": "area_under_curve", "area under curves": "area_under_curve", "auc": "area_under_curve", "application of integrals": "area_under_curve",
    "mathematical reasoning": "mathematical_reasoning",
    "linear programming": "linear_programming", "lpp": "linear_programming",
    "mathematical tools": "units_dimensions",
}

@dataclass(frozen=True)
class ChapterMapper:
    spine: tuple[str, ...] = SPINE

    def priority(self, chapter: str) -> ChapterPriority:
        if chapter not in self.spine:
            raise KeyError(f"Unknown canonical chapter: {chapter}")
        if chapter in TIER_0:
            return ChapterPriority.TIER_0
        if chapter in TIER_1:
            return ChapterPriority.TIER_1
        if chapter in TIER_2:
            return ChapterPriority.TIER_2
        return ChapterPriority.TIER_3

    def syllabus_order(self, chapter: str) -> int:
        return self.spine.index(chapter)

    def map_text(self, text: str) -> list[str]:
        normalized = re.sub(r"[_\-./\\]+", " ", text.lower())
        matches = set()
        for alias, chapter in ALIASES.items():
            if len(alias) <= 4:
                if re.search(rf"\b{re.escape(alias)}\b", normalized):
                    matches.add(chapter)
            else:
                if alias in normalized:
                    matches.add(chapter)
        return sorted(matches, key=self.syllabus_order)

    def map_file(self, file_path: str) -> list[str]:
        """Convenience method to map a file path to its canonical chapter IDs."""
        return self.map_text(file_path)

    def work_key(self, chapters: list[str]) -> tuple[int, int]:
        if not chapters:
            return (int(ChapterPriority.TIER_3) + 1, len(self.spine))
        return min((int(self.priority(c)), self.syllabus_order(c)) for c in chapters)
