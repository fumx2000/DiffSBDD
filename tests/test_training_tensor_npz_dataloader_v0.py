import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import pytest
import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_training_tensor_npz_dataloader_v0 import run  # noqa: E402
from covalent_ext.npz_dataset import CovalentNPZDataset, NPZ_REQUIRED_KEYS, covalent_npz_collate_fn  # noqa: E402


@pytest.fixture(autouse=True)
def _fixture_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _sample_index():
    return Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        manifest_json=root / "manifest.json",
        sample_index_csv=root / "sample_index.csv",
        sanity_report_csv=root / "sanity_report.csv",
        output_report_csv=root / "dataloader_sanity_report.csv",
        output_manifest_json=root / "batch_preview_manifest.json",
        output_md=Path("docs/training_tensor_npz_dataloader_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_dataset_len_getitem_keys_and_dtypes():
    dataset = CovalentNPZDataset(_sample_index())
    assert len(dataset) == 3
    sample = dataset[0]
    assert set(NPZ_REQUIRED_KEYS).issubset(sample.keys())
    assert isinstance(sample["sample_id"], str)
    assert sample["ligand_atom_coords"].dtype == torch.float32
    assert sample["protein_atom_coords"].dtype == torch.float32
    assert sample["ligand_atomic_numbers"].dtype == torch.long
    assert sample["protein_atomic_numbers"].dtype == torch.long
    assert sample["ligand_bond_index"].dtype == torch.long
    assert sample["ligand_bond_type"].dtype == torch.long
    assert sample["scaffold_atom_mask"].dtype == torch.bool
    assert sample["ligand_reactive_atom_index"].dtype == torch.long
    assert isinstance(sample["protein_reactive_residue_label"], str)
    assert isinstance(sample["warhead_type_label"], str)


def test_collate_and_dataloader_batch_shapes_and_masks():
    dataset = CovalentNPZDataset(_sample_index())
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    assert batch["sample_id"] == [
        "BTK_C481_6DI9_pre_reaction",
        "KRAS_G12C_5F2E_pre_reaction",
        "KRAS_G12C_6OIM_pre_reaction",
    ]
    assert batch["ligand_atom_coords"].shape == (3, 41, 3)
    assert batch["protein_atom_coords"].shape == (3, 2306, 3)
    assert batch["ligand_atom_mask"].shape == (3, 41)
    assert batch["protein_atom_mask"].shape == (3, 2306)
    assert batch["ligand_atom_mask"].sum(dim=1).tolist() == [33, 30, 41]
    assert batch["protein_atom_mask"].sum(dim=1).tolist() == [2306, 1723, 1613]
    assert not batch["ligand_atom_mask"][0, 33:].any()
    assert not batch["ligand_atom_mask"][1, 30:].any()
    assert not batch["protein_atom_mask"][1, 1723:].any()
    assert not batch["protein_atom_mask"][2, 1613:].any()
    assert torch.isfinite(batch["ligand_atom_coords"]).all()
    assert torch.isfinite(batch["protein_atom_coords"]).all()
    for idx, reactive_idx in enumerate(batch["ligand_reactive_atom_index"].tolist()):
        assert batch["ligand_atom_mask"][idx, reactive_idx]
        assert batch["warhead_atom_mask"][idx, reactive_idx]
    for key in [
        "generation_mask_A_warhead_only",
        "generation_mask_B_linker_warhead",
        "generation_mask_B2_scaffold_warhead",
        "generation_mask_C_scaffold_linker_warhead",
    ]:
        assert batch[key].shape == (3, 41)
        assert batch[key].dtype == torch.bool


def test_check_script_writes_reports_and_does_not_create_forbidden_outputs():
    code = run(_args())
    assert code == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    report_rows = _read_csv(root / "dataloader_sanity_report.csv")
    assert len(report_rows) == 3
    assert all(row["dataloader_sanity_status"] == "passed" for row in report_rows)
    preview = json.loads((root / "batch_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["dataloader_created"] is True
    assert preview["dataset_created"] is True
    assert preview["checkpoint_loaded"] is False
    assert preview["model_initialized"] is False
    assert preview["training_executed"] is False
    assert preview["ligand_atom_coords_shape"] == [3, 41, 3]
    assert preview["protein_atom_coords_shape"] == [3, 2306, 3]
    assert Path("docs/training_tensor_npz_dataloader_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
