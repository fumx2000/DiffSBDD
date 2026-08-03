from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.dataset import CovalentJsonlDataset
from covalent_ext.masking import (
    CANONICAL_MASK_SEMANTICS,
    CANONICAL_MASK_SEMANTIC_TO_LEVEL,
)


DATASET_PATH = REPO_ROOT / "data/processed/covalent_debug.jsonl"


@pytest.fixture(scope="module")
def dataset():
    return CovalentJsonlDataset(DATASET_PATH)


def test_dataset_reads_ten_samples(dataset):
    assert len(dataset) == 10


def test_atom_groups_are_nonempty(dataset):
    for sample in dataset:
        assert sample["scaffold_atoms"]
        assert sample["linker_atoms"]
        assert sample["warhead_atoms"]


def test_atom_groups_are_disjoint(dataset):
    for sample in dataset:
        groups = [
            set(sample["scaffold_atoms"]),
            set(sample["linker_atoms"]),
            set(sample["warhead_atoms"]),
        ]
        assert groups[0].isdisjoint(groups[1])
        assert groups[0].isdisjoint(groups[2])
        assert groups[1].isdisjoint(groups[2])


def test_canonical_five_level_masks_generate(dataset):
    for sample in dataset:
        masks = dataset.build_all_masks(sample)
        assert tuple(masks) == CANONICAL_MASK_SEMANTICS
        assert len(masks) == 5
        assert [
            masks[semantic].mask_type
            for semantic in CANONICAL_MASK_SEMANTICS
        ] == [
            CANONICAL_MASK_SEMANTIC_TO_LEVEL[semantic]
            for semantic in CANONICAL_MASK_SEMANTICS
        ]
        assert "scaffold_plus_warhead" in masks
        assert "scaffold_only" in masks
        assert (
            masks["scaffold_plus_warhead"].visible_atoms
            != masks["scaffold_only"].visible_atoms
        )
        assert (
            masks["scaffold_plus_warhead"].masked_atoms
            != masks["scaffold_only"].masked_atoms
        )


def test_lig_fixed_length_equals_ligand_atom_count(dataset):
    for sample in dataset:
        num_atoms = dataset.num_ligand_atoms(sample)
        for result in dataset.build_all_masks(sample).values():
            assert len(result.lig_fixed) == num_atoms


def test_mask_counts_match_expected_semantics(dataset):
    for sample in dataset:
        num_atoms = dataset.num_ligand_atoms(sample)
        n_scaffold = len(sample["scaffold_atoms"])
        n_linker = len(sample["linker_atoms"])
        n_warhead = len(sample["warhead_atoms"])
        masks = dataset.build_all_masks(sample)

        warhead_only = masks["warhead_only"]
        assert len(warhead_only.visible_atoms) == n_scaffold + n_linker
        assert len(warhead_only.masked_atoms) == n_warhead
        assert warhead_only.mask_type == "A_warhead_only"

        linker_plus_warhead = masks["linker_plus_warhead"]
        assert len(linker_plus_warhead.visible_atoms) == n_scaffold
        assert len(linker_plus_warhead.masked_atoms) == n_linker + n_warhead
        assert linker_plus_warhead.mask_type == "B_linker_warhead"

        scaffold_plus_warhead = masks["scaffold_plus_warhead"]
        assert len(scaffold_plus_warhead.visible_atoms) == n_linker
        assert len(scaffold_plus_warhead.masked_atoms) == n_scaffold + n_warhead
        assert scaffold_plus_warhead.mask_type == "B2_scaffold_warhead"

        scaffold_only = masks["scaffold_only"]
        assert len(scaffold_only.visible_atoms) == n_linker + n_warhead
        assert len(scaffold_only.masked_atoms) == n_scaffold
        assert scaffold_only.mask_type == "B3_scaffold_only"

        whole_ligand = masks["scaffold_plus_linker_plus_warhead"]
        assert len(whole_ligand.visible_atoms) == 0
        assert len(whole_ligand.masked_atoms) == num_atoms
        assert whole_ligand.mask_type == "C_scaffold_linker_warhead"

        for result in masks.values():
            assert len(result.visible_atoms) + len(result.masked_atoms) == num_atoms
            assert len(result.lig_fixed) == num_atoms
