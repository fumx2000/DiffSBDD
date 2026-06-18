from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (SRC_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_covalent_real_small import build_from_manifest
from check_covalent_real_small import check_dataset
from covalent_ext.dataset import CovalentJsonlDataset


MANIFEST = REPO_ROOT / "data/raw/covalent_small/manifest_example.csv"


def test_manifest_exists():
    assert MANIFEST.exists()
    text = MANIFEST.read_text(encoding="utf-8")
    assert "sample_id" in text
    assert "pseudo_3rfm_cys28" in text


def test_builder_checker_dataset_and_masks(tmp_path):
    output = tmp_path / "covalent_real_small.jsonl"
    samples = build_from_manifest(MANIFEST, output)
    assert len(samples) == 1
    assert output.exists()

    assert check_dataset(output, verbose=False)

    dataset = CovalentJsonlDataset(output)
    assert len(dataset) == 1
    sample = dataset[0]
    assert sample["sample_id"] == "pseudo_3rfm_cys28"
    assert sample["ligand_reactive_atom_id"] in sample["warhead_atoms"]

    masks = dataset.build_all_masks(sample)
    assert set(masks) == {"A", "B", "B2", "C"}
    assert all(len(result.lig_fixed) == dataset.num_ligand_atoms(sample) for result in masks.values())
