from pathlib import Path
import sys

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.masking import (
    LONG_FORM_MASK_BUILDERS,
    build_long_form_mask,
    build_four_level_mask,
    mask_linker_and_warhead,
    mask_scaffold,
    mask_scaffold_and_warhead_long_form,
    mask_scaffold_only_long_form,
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


def test_long_form_b2_masks_scaffold_and_warhead_with_linker_context():
    result = mask_scaffold_and_warhead_long_form(SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)

    assert_mask(result, "B2_scaffold_warhead", [3, 4], [0, 1, 2, 5, 6], [0, 0, 0, 1, 1, 0, 0])


def test_long_form_b3_masks_scaffold_only_with_linker_warhead_context():
    result = mask_scaffold_only_long_form(SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)

    assert_mask(result, "B3_scaffold_only", [3, 4, 5, 6], [0, 1, 2], [0, 0, 0, 1, 1, 1, 1])


def test_long_form_b2_and_b3_are_distinct_while_legacy_short_b2_is_preserved():
    legacy_b2 = build_four_level_mask("B2", SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    long_b2 = build_long_form_mask("B2_scaffold_warhead", SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)
    long_b3 = build_long_form_mask("B3_scaffold_only", SCAFFOLD, LINKER, WARHEAD, NUM_ATOMS)

    assert set(long_b2.masked_atoms) >= set(SCAFFOLD)
    assert set(long_b2.masked_atoms) >= set(WARHEAD)
    assert set(long_b2.visible_atoms) >= set(LINKER)
    assert not set(long_b2.visible_atoms).intersection(WARHEAD)
    assert set(long_b3.masked_atoms) >= set(SCAFFOLD)
    assert not set(long_b3.masked_atoms).intersection(WARHEAD)
    assert set(long_b3.visible_atoms) >= set(LINKER)
    assert set(long_b3.visible_atoms) >= set(WARHEAD)
    assert not set(long_b3.visible_atoms).intersection(SCAFFOLD)
    assert long_b2.masked_atoms != long_b3.masked_atoms
    assert long_b2.visible_atoms != long_b3.visible_atoms
    assert legacy_b2.visible_atoms == long_b3.visible_atoms
    assert legacy_b2.masked_atoms == long_b3.masked_atoms


def test_long_form_mask_dispatch_includes_b3_without_short_alias():
    assert "B3_scaffold_only" in LONG_FORM_MASK_BUILDERS
    assert "B3" not in LONG_FORM_MASK_BUILDERS
    assert "B3" not in {"A", "B", "B2", "C"}


@pytest.mark.parametrize(
    ("scaffold", "linker", "warhead", "message"),
    [
        (None, LINKER, WARHEAD, "scaffold_atoms is missing"),
        (SCAFFOLD, None, WARHEAD, "linker_atoms is missing"),
        (SCAFFOLD, LINKER, None, "warhead_atoms is missing"),
        ([], LINKER, WARHEAD, "scaffold_atoms"),
        (SCAFFOLD, [], WARHEAD, "linker_atoms"),
        (SCAFFOLD, LINKER, [], "warhead_atoms"),
    ],
)
def test_long_form_b3_fails_safely_on_missing_or_empty_regions(scaffold, linker, warhead, message):
    with pytest.raises(ValueError, match=message):
        build_long_form_mask("B3_scaffold_only", scaffold, linker, warhead, NUM_ATOMS)
