"""Test mathematical CAS equivalence, negative assertions, and RDKit chemical validation."""
from src.verification.verifiers import (
    rdkit_canonical_smiles,
    rdkit_equivalent_molecules,
    rdkit_valid_smiles,
    sympy_equivalent,
)

def test_sympy_algebraic_and_trigonometric_equivalence():
    # Trigonometric identity
    assert sympy_equivalent("sin(2*x)", "2*sin(x)*cos(x)")
    # Polynomial identity
    assert sympy_equivalent("(x + y)**2", "x**2 + 2*x*y + y**2")
    # Exponential / logarithmic laws
    assert sympy_equivalent("exp(a + b)", "exp(a) * exp(b)")

def test_sympy_negative_assertions_must_fail():
    # Basic inequality
    assert not sympy_equivalent("x + 1", "x + 2")
    assert not sympy_equivalent("sin(x)", "cos(x)")
    assert not sympy_equivalent("x**2 - 1", "x**2 + 1")
    assert not sympy_equivalent("2*x", "3*x")

def test_numerical_tolerance_handling():
    # Close within 1e-4 tolerance
    assert sympy_equivalent("4.50000", "4.50002", tolerance=1e-4)
    # Beyond tolerance
    assert not sympy_equivalent("4.50", "4.55", tolerance=1e-4)
    # Exact option match
    assert sympy_equivalent("A", "A")
    assert not sympy_equivalent("A", "B")

def test_rdkit_chemical_smiles_validation():
    # Valid organic molecules
    assert rdkit_valid_smiles("CCO")               # Ethanol
    assert rdkit_valid_smiles("c1ccccc1")           # Benzene
    assert rdkit_valid_smiles("CC(=O)O")            # Acetic acid

    # Invalid SMILES syntax
    assert not rdkit_valid_smiles("invalid_smiles_not_a_chem")
    assert not rdkit_valid_smiles("C=C=C=C=C=")

    # Chemical equivalence across different SMILES representations
    assert rdkit_equivalent_molecules("CCO", "OCC")
    assert rdkit_equivalent_molecules("c1ccccc1", "C1=CC=CC=C1")
    assert not rdkit_equivalent_molecules("CCO", "CC(=O)O")
