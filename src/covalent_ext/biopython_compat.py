from __future__ import annotations


CANONICAL_RESIDUE_THREE_TO_ONE = {
    "ALA": "A",
    "ARG": "R",
    "ASN": "N",
    "ASP": "D",
    "CYS": "C",
    "GLN": "Q",
    "GLU": "E",
    "GLY": "G",
    "HIS": "H",
    "ILE": "I",
    "LEU": "L",
    "LYS": "K",
    "MET": "M",
    "PHE": "F",
    "PRO": "P",
    "SER": "S",
    "THR": "T",
    "TRP": "W",
    "TYR": "Y",
    "VAL": "V",
}


def residue_three_to_one(resname: str) -> str:
    normalized = str(resname or "").strip().upper()
    return CANONICAL_RESIDUE_THREE_TO_ONE.get(normalized, "X")


def patch_biopython_polypeptide_three_to_one() -> bool:
    import Bio.PDB.Polypeptide as polypeptide

    if not hasattr(polypeptide, "three_to_one"):
        polypeptide.three_to_one = residue_three_to_one
        return True
    return False
