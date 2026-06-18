from pathlib import Path
import sys

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.masking import (
    build_four_level_mask,
    mask_linker_and_warhead,
    mask_scaffold,
    mask_warhead,
    mask_whole_ligand,
)


SCAFFOLD = [0, 1, 2]
LINKER = [3, 4]
WARHEAD = [5, 6]
NUM_ATOMS = 7


def assert_mask(result, mask_type, visible, masked, lig_fixed):
    assert result.mask_type == mask_type
    assert result.visible_atoms == tuple(visible)
    assert result.masked_atoms == tuple(masked)
    assert torch.equal(result.lig_fixed, torch.tensor(lig_fixed, dtype=torch.long))


def test_mask_a_masks_warhead():
    result = mask_warhead(SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    assert_mask(result, "A", [0, 1, 2, 3, 4], [5, 6], [1, 1, 1, 1, 1, 0, 0])


def test_mask_b_masks_linker_and_warhead():
    result = mask_linker_and_warhead(SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    assert_mask(result, "B", [0, 1, 2], [3, 4, 5, 6], [1, 1, 1, 0, 0, 0, 0])


def test_mask_b2_masks_scaffold():
    result = mask_scaffold(SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    assert_mask(result, "B2", [3, 4, 5, 6], [0, 1, 2], [0, 0, 0, 1, 1, 1, 1])


def test_mask_c_masks_whole_ligand():
    result = mask_whole_ligand(SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    assert_mask(result, "C", [], [0, 1, 2, 3, 4, 5, 6], [0, 0, 0, 0, 0, 0, 0])


def test_dispatch_matches_named_function():
    result = build_four_level_mask("A", SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    assert_mask(result, "A", [0, 1, 2, 3, 4], [5, 6], [1, 1, 1, 1, 1, 0, 0])


def test_overlapping_groups_raise():
    with pytest.raises(ValueError, match="disjoint"):
        mask_warhead([0, 1], [1, 2], [3], 4)


def test_out_of_range_atom_raises():
    with pytest.raises(ValueError, match="outside"):
        mask_warhead([0, 9], [1], [2], 3)
