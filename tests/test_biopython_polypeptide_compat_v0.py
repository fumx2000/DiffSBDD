from __future__ import annotations

import sys
from pathlib import Path

import Bio.PDB.Polypeptide as polypeptide


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
    residue_three_to_one,
)


def test_residue_three_to_one_canonical_and_unknown_residues() -> None:
    assert residue_three_to_one("ALA") == "A"
    assert residue_three_to_one("CYS") == "C"
    assert residue_three_to_one("MSE") == "X"
    assert residue_three_to_one("UNK") == "X"
    assert residue_three_to_one("") == "X"


def test_patch_restores_biopython_polypeptide_three_to_one_without_import_error() -> None:
    original = getattr(polypeptide, "three_to_one", None)
    if hasattr(polypeptide, "three_to_one"):
        delattr(polypeptide, "three_to_one")
    try:
        assert not hasattr(polypeptide, "three_to_one")
        assert patch_biopython_polypeptide_three_to_one() is True
        assert polypeptide.three_to_one("ALA") == "A"
        assert polypeptide.three_to_one("CYS") == "C"
        assert polypeptide.three_to_one("UNK") == "X"
    finally:
        if original is not None:
            polypeptide.three_to_one = original
        elif hasattr(polypeptide, "three_to_one"):
            delattr(polypeptide, "three_to_one")
        patch_biopython_polypeptide_three_to_one()


def test_lightning_modules_import_after_explicit_compatibility_patch() -> None:
    patch_biopython_polypeptide_three_to_one()

    import lightning_modules

    assert lightning_modules.three_to_one("ALA") == "A"
    assert lightning_modules.three_to_one("CYS") == "C"
    assert lightning_modules.three_to_one("MSE") == "X"
