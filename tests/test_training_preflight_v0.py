import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_training_preflight_v0 import MASK_LEVELS, run  # noqa: E402
from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.model_input_adapter import build_covalent_model_input_v0, validate_covalent_model_input_v0  # noqa: E402
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402
from covalent_ext.training_preflight import (  # noqa: E402
    move_model_input_to_device_v0,
    run_mock_training_preflight_step_v0,
    summarize_model_input_for_preflight_v0,
)


def setup_function():
    pass


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _batch():
    dataset = CovalentNPZDataset("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    return next(iter(loader))


def _model_input(mask_level="A_warhead_only"):
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level=mask_level)
    model_input = build_covalent_model_input_v0(adapted)
    ok, reasons = validate_covalent_model_input_v0(model_input)
    assert ok, reasons
    return model_input


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        manifest_json=root / "manifest.json",
        sample_index_csv=root / "sample_index.csv",
        sanity_report_csv=root / "sanity_report.csv",
        dataloader_report_csv=root / "dataloader_sanity_report.csv",
        adapter_report_csv=root / "batch_adapter_sanity_report.csv",
        model_input_mapping_report_csv=root / "model_input_mapping_sanity_report.csv",
        model_input_mapping_manifest_json=root / "model_input_mapping_preview_manifest.json",
        output_report_csv=root / "training_preflight_report.csv",
        output_manifest_json=root / "training_preflight_preview_manifest.json",
        output_md=Path("docs/training_preflight_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_move_model_input_to_cpu_preserves_non_tensor_fields(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    model_input = _model_input()
    moved = move_model_input_to_device_v0(model_input, device="cpu")
    tensor_keys = [key for key, value in moved.items() if isinstance(value, torch.Tensor)]
    assert tensor_keys
    assert all(moved[key].device.type == "cpu" for key in tensor_keys)
    assert moved["sample_id"] == model_input["sample_id"]
    assert moved["protein_reactive_residue_label"] == model_input["protein_reactive_residue_label"]
    assert moved["warhead_type_label"] == model_input["warhead_type_label"]
    assert moved["device"] == "cpu"
    assert moved["checkpoint_loaded"] is False
    assert moved["model_initialized"] is False
    assert moved["training_executed"] is False


def test_move_model_input_to_cuda_falls_back_to_cpu_when_unavailable(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    moved = move_model_input_to_device_v0(_model_input(), device="cuda:0")
    if torch.cuda.is_available():
        assert moved["device"].startswith("cuda")
    else:
        assert moved["device"] == "cpu"
        assert moved["device_transfer_error"].startswith("cuda_unavailable_fallback_to_cpu")


def test_four_mask_levels_complete_preflight_without_model_or_training(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    for mask_level in MASK_LEVELS:
        model_input = _model_input(mask_level=mask_level)
        moved = move_model_input_to_device_v0(model_input, device="cpu")
        summary = summarize_model_input_for_preflight_v0(moved)
        preflight = run_mock_training_preflight_step_v0(moved)
        assert summary["batch_size"] == 3
        assert summary["sample_count"] == 3
        assert summary["protein_x_shape"] == [3, 2306, 3]
        assert summary["ligand_x_shape"] == [3, 41, 3]
        assert summary["ligand_context_x_shape"] == [3, 41, 3]
        assert summary["ligand_target_x_shape"] == [3, 41, 3]
        assert summary["coordinate_center_shape"] == [3, 3]
        assert summary["target_atom_count_total"] > 0
        assert summary["reactive_atom_in_target_mask_all"] is True
        assert summary["context_target_no_overlap_all"] is True
        assert summary["finite_coords_all"] is True
        assert summary["no_nan"] is True
        assert summary["no_inf"] is True
        assert preflight["mock_total_loss_finite"] is True
        assert preflight["target_atom_count_positive"] is True
        assert preflight["checkpoint_loaded"] is False
        assert preflight["model_initialized"] is False
        assert preflight["training_executed"] is False


def test_check_script_writes_report_manifest_summary_and_no_forbidden_artifacts(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "training_preflight_report.csv")
    assert len(rows) == 4
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    assert all(row["preflight_status"] == "passed" for row in rows)
    assert all(row["mock_total_loss_finite"] == "true" for row in rows)
    assert all(int(row["target_atom_count_total"]) > 0 for row in rows)
    assert all(row["reactive_atom_in_target_mask_all"] == "true" for row in rows)
    assert all(row["context_target_no_overlap_all"] == "true" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["model_initialized"] == "false" for row in rows)
    assert all(row["training_executed"] == "false" for row in rows)
    preview = json.loads((root / "training_preflight_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "covalent_training_preflight_dry_run_v0"
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 4
    assert preview["all_mask_levels_passed"] is True
    assert preview["device"] == "cpu"
    assert preview["protein_x_shape"] == [3, 2306, 3]
    assert preview["ligand_x_shape"] == [3, 41, 3]
    assert preview["ligand_context_x_shape"] == [3, 41, 3]
    assert preview["ligand_target_x_shape"] == [3, 41, 3]
    assert preview["coordinate_center_shape"] == [3, 3]
    assert preview["mock_total_loss_all_finite"] is True
    assert preview["checkpoint_loaded"] is False
    assert preview["model_initialized"] is False
    assert preview["training_executed"] is False
    assert preview["archive_created"] is False
    assert preview["recommended_next_step"] == "diffSBDD_adapter_or_tiny_model_smoke_test"
    assert Path("docs/training_preflight_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
