from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.dataset import CovalentJsonlDataset


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


def test_four_level_masks_generate(dataset):
    for sample in dataset:
        masks = dataset.build_all_masks(sample)
        assert set(masks) == {"A", "B", "B2", "C"}


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

        assert len(masks["A"].visible_atoms) == n_scaffold + n_linker
        assert len(masks["A"].masked_atoms) == n_warhead

        assert len(masks["B"].visible_atoms) == n_scaffold
        assert len(masks["B"].masked_atoms) == n_linker + n_warhead

        assert len(masks["B2"].visible_atoms) == n_linker + n_warhead
        assert len(masks["B2"].masked_atoms) == n_scaffold

        assert len(masks["C"].visible_atoms) == 0
        assert len(masks["C"].masked_atoms) == num_atoms

        for result in masks.values():
            assert len(result.visible_atoms) + len(result.masked_atoms) == num_atoms

