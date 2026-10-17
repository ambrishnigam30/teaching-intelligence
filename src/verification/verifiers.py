"""Mathematical and chemical verification using SymPy CAS and RDKit."""
from __future__ import annotations

import math
import re

def sympy_equivalent(left: str, right: str, tolerance: float = 1e-4) -> bool:
    """Rigorous CAS algebraic and numerical equivalence check with tolerance.
    
    Returns False for non-equivalent expressions (e.g. x+1 vs x+2) and syntax errors.
    """
    left_str = str(left).strip()
    right_str = str(right).strip()

    if not left_str or not right_str:
        return False

    # Exact string match (e.g. option keys 'A' == 'A')
    if left_str == right_str:
        return True

    # Check for direct floating point numerical equivalence
    try:
        val_l = float(left_str)
        val_r = float(right_str)
        if math.isclose(val_l, val_r, rel_tol=tolerance, abs_tol=tolerance):
            return True
        return False
    except ValueError:
        pass

    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication_application,
        )

        transformations = standard_transformations + (implicit_multiplication_application,)
        
        # Clean latex backslashes if present
        cleaned_l = re.sub(r"\\(?:frac|text|mathrm|left|right)", "", left_str)
        cleaned_r = re.sub(r"\\(?:frac|text|mathrm|left|right)", "", right_str)

        expr_l = parse_expr(cleaned_l, transformations=transformations, evaluate=False)
        expr_r = parse_expr(cleaned_r, transformations=transformations, evaluate=False)

        diff = expr_l - expr_r

        # 1. Direct simplification
        if sp.simplify(diff) == 0:
            return True

        # 2. Trigonometric simplification
        if sp.trigsimp(diff) == 0:
            return True

        # 3. Power / exponential simplification
        if sp.powsimp(diff) == 0:
            return True

        # 4. Numerical evaluation if expressions have no free symbols
        if not diff.free_symbols:
            val = complex(sp.N(diff))
            if abs(val) <= tolerance:
                return True

        return False
    except Exception:
        return False

def rdkit_valid_smiles(smiles: str) -> bool:
    """Validate chemical structure notation using RDKit."""
    s = str(smiles).strip()
    if not s or len(s) < 2:
        return False
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(s)
        return mol is not None
    except Exception:
        return False

def rdkit_canonical_smiles(smiles: str) -> str | None:
    """Return canonical SMILES string if valid, else None."""
    s = str(smiles).strip()
    if not s:
        return None
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(s)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, canonical=True)
    except Exception:
        return None

def rdkit_equivalent_molecules(smiles1: str, smiles2: str) -> bool:
    """Check if two SMILES represent the exact same chemical structure."""
    c1 = rdkit_canonical_smiles(smiles1)
    c2 = rdkit_canonical_smiles(smiles2)
    if c1 is None or c2 is None:
        return False
    return c1 == c2
