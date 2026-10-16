from __future__ import annotations

def sympy_equivalent(left: str, right: str) -> bool:
    try:
        import sympy as sp
        return bool(sp.simplify(sp.sympify(left) - sp.sympify(right)) == 0)
    except (ImportError, TypeError, ValueError, SyntaxError):
        return False

def rdkit_valid_smiles(smiles: str) -> bool:
    try:
        from rdkit import Chem
        return Chem.MolFromSmiles(smiles) is not None
    except ImportError:
        return False
