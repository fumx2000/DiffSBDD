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

from check_training_tensor_batch_adapter_v0 import MASK_LEVELS, run  # noqa: E402
from covalent_ext.batch_adapter import (  # noqa: E402
    REQUIRED_ADAPTED_KEYS,
    adapt_covalent_batch_for_model_v0,
    validate_adapted_covalent_batch_v0,
)
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402


@pytest.fixture(autouse=True)
def _fixture_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _batch():
    dataset = CovalentNPZDataset("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    return next(iter(loader))


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        manifest_json=root / "manifest.json",
        sample_index_csv=root / "sample_index.csv",
        sanity_report_csv=root / "sanity_report.csv",
        dataloader_report_csv=root / "dataloader_sanity_report.csv",
        output_report_csv=root / "batch_adapter_sanity_report.csv",
        output_manifest_json=root / "batch_adapter_preview_manifest.json",
        output_md=Path("docs/training_tensor_batch_adapter_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_adapter_outputs_required_keys_for_all_mask_levels_and_validates():
    batch = _batch()
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        assert REQUIRED_ADAPTED_KEYS.issubset(adapted)
        assert adapted["coordinate_center"].shape == (3, 3)
        assert adapted["ligand_coords_centered"].shape == (3, 41, 3)
        assert adapted["protein_coords_centered"].shape == (3, 2306, 3)
        assert adapted["generation_mask"].shape == (3, 41)
        assert adapted["fixed_ligand_atom_mask"].shape == (3, 41)
        assert not (adapted["generation_mask"] & ~adapted["ligand_atom_mask"]).any()
        assert not (adapted["generation_mask"] & adapted["fixed_ligand_atom_mask"]).any()
        for idx, reactive_idx in enumerate(adapted["ligand_reactive_atom_index"].tolist()):
            assert adapted["generation_mask"][idx, reactive_idx]
        ok, reasons = validate_adapted_covalent_batch_v0(adapted)
        assert ok, reasons
        assert adapted["checkpoint_loaded"] is False
        assert adapted["model_initialized"] is False
        assert adapted["training_executed"] is False


def test_invalid_mask_level_raises():
    with pytest.raises(ValueError):
        adapt_covalent_batch_for_model_v0(_batch(), mask_level="bad")


def test_check_script_writes_reports_and_forbidden_outputs_absent():
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "batch_adapter_sanity_report.csv")
    assert len(rows) == 12
    assert all(row["adapter_sanity_status"] == "passed" for row in rows)
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    preview = json.loads((root / "batch_adapter_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "covalent_batch_adapter_sanity_v0"
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 12
    assert preview["adapted_ligand_coords_shape"] == [3, 41, 3]
    assert preview["adapted_protein_coords_shape"] == [3, 2306, 3]
    assert preview["coordinate_center_shape"] == [3, 3]
    assert preview["all_mask_levels_passed"] is True
    assert preview["checkpoint_loaded"] is False
    assert preview["model_initialized"] is False
    assert preview["training_executed"] is False
    assert Path("docs/training_tensor_batch_adapter_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
