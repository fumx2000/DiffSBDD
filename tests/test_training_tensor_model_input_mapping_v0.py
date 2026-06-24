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

from check_training_tensor_model_input_mapping_v0 import MASK_LEVELS, run  # noqa: E402
from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.model_input_adapter import (  # noqa: E402
    REQUIRED_MODEL_INPUT_KEYS,
    build_covalent_model_input_v0,
    compute_mock_reconstruction_loss_v0,
    validate_covalent_model_input_v0,
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
        adapter_report_csv=root / "batch_adapter_sanity_report.csv",
        output_report_csv=root / "model_input_mapping_sanity_report.csv",
        output_manifest_json=root / "model_input_mapping_preview_manifest.json",
        output_md=Path("docs/training_tensor_model_input_mapping_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_model_input_required_keys_shapes_masks_and_mock_loss_for_all_mask_levels():
    batch = _batch()
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        assert REQUIRED_MODEL_INPUT_KEYS.issubset(model_input)
        assert model_input["protein_x"].shape == (3, 2306, 3)
        assert model_input["protein_h"].shape == (3, 2306)
        assert model_input["protein_mask"].shape == (3, 2306)
        assert model_input["ligand_x"].shape == (3, 41, 3)
        assert model_input["ligand_h"].shape == (3, 41)
        assert model_input["ligand_mask"].shape == (3, 41)
        assert model_input["ligand_context_x"].shape == (3, 41, 3)
        assert model_input["ligand_context_h"].shape == (3, 41)
        assert model_input["ligand_context_mask"].shape == (3, 41)
        assert model_input["ligand_target_x"].shape == (3, 41, 3)
        assert model_input["ligand_target_h"].shape == (3, 41)
        assert model_input["ligand_target_mask"].shape == (3, 41)
        assert model_input["mock_target_x"].shape == (3, 41, 3)
        assert model_input["mock_target_h"].shape == (3, 41)
        assert model_input["coordinate_center"].shape == (3, 3)
        assert not (model_input["ligand_context_mask"] & model_input["ligand_target_mask"]).any()
        assert torch.equal(model_input["ligand_target_mask"], model_input["generation_mask"])
        assert torch.equal(model_input["ligand_context_mask"], model_input["fixed_ligand_atom_mask"])
        assert not model_input["ligand_context_x"][~model_input["ligand_context_mask"]].any()
        assert not model_input["ligand_target_x"][~model_input["ligand_target_mask"]].any()
        for idx, reactive_idx in enumerate(model_input["ligand_reactive_atom_index"].tolist()):
            assert model_input["ligand_target_mask"][idx, reactive_idx]
        ok, reasons = validate_covalent_model_input_v0(model_input)
        assert ok, reasons
        mock_loss = compute_mock_reconstruction_loss_v0(model_input)
        assert mock_loss["mock_loss_computed"] is True
        assert mock_loss["mock_loss_finite"] is True
        assert mock_loss["target_atom_count"] == int(model_input["ligand_target_mask"].sum().item())
        assert mock_loss["checkpoint_loaded"] is False
        assert mock_loss["model_initialized"] is False
        assert mock_loss["training_executed"] is False
        assert model_input["checkpoint_loaded"] is False
        assert model_input["model_initialized"] is False
        assert model_input["training_executed"] is False


def test_validation_catches_context_target_overlap():
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level="A_warhead_only")
    model_input = build_covalent_model_input_v0(adapted)
    model_input["ligand_context_mask"] = model_input["ligand_target_mask"].clone()
    ok, reasons = validate_covalent_model_input_v0(model_input)
    assert ok is False
    assert "context_target_overlap" in reasons


def test_validation_catches_checkpoint_model_and_training_flags():
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level="A_warhead_only")
    model_input = build_covalent_model_input_v0(adapted)
    model_input["checkpoint_loaded"] = True
    model_input["model_initialized"] = True
    model_input["training_executed"] = True
    ok, reasons = validate_covalent_model_input_v0(model_input)
    assert ok is False
    assert "checkpoint_loaded" in reasons
    assert "model_initialized" in reasons
    assert "training_executed" in reasons


def test_check_script_writes_report_manifest_summary_and_no_forbidden_artifacts():
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "model_input_mapping_sanity_report.csv")
    assert len(rows) == 12
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    assert all(row["model_input_mapping_status"] == "passed" for row in rows)
    assert all(row["reactive_atom_in_target_mask"] == "true" for row in rows)
    assert all(row["context_target_no_overlap"] == "true" for row in rows)
    assert all(row["model_input_shapes_valid"] == "true" for row in rows)
    assert all(row["centered_coords_finite"] == "true" for row in rows)
    assert all(row["mock_loss_computed"] == "true" for row in rows)
    assert all(row["mock_loss_finite"] == "true" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["model_initialized"] == "false" for row in rows)
    assert all(row["training_executed"] == "false" for row in rows)
    preview = json.loads((root / "model_input_mapping_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "covalent_model_input_mapping_mock_loss_v0"
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 12
    assert preview["protein_x_shape"] == [3, 2306, 3]
    assert preview["ligand_x_shape"] == [3, 41, 3]
    assert preview["ligand_context_x_shape"] == [3, 41, 3]
    assert preview["ligand_target_x_shape"] == [3, 41, 3]
    assert preview["coordinate_center_shape"] == [3, 3]
    assert preview["all_mask_levels_passed"] is True
    assert preview["mock_loss_all_finite"] is True
    assert preview["checkpoint_loaded"] is False
    assert preview["model_initialized"] is False
    assert preview["training_executed"] is False
    assert preview["archive_created"] is False
    assert Path("docs/training_tensor_model_input_mapping_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
