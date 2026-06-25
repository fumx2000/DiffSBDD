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

from run_tiny_covalent_training_smoke_v0 import MASK_LEVELS, run  # noqa: E402
from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.model_input_adapter import build_covalent_model_input_v0, validate_covalent_model_input_v0  # noqa: E402
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402
from covalent_ext.tiny_covalent_model import (  # noqa: E402
    TinyCovalentDenoiserV0,
    compute_tiny_covalent_loss_v0,
    move_model_input_for_tiny_smoke_v0,
    resolve_training_smoke_device_v0,
    run_tiny_training_step_v0,
)


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


def _model_input(mask_level="A_warhead_only"):
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level=mask_level)
    model_input = build_covalent_model_input_v0(adapted)
    ok, reasons = validate_covalent_model_input_v0(model_input)
    assert ok, reasons
    return model_input


def _args(device="auto"):
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        device=device,
        lr=1e-3,
        seed=0,
        sample_index_csv=root / "sample_index.csv",
        training_preflight_report_csv=root / "training_preflight_report.csv",
        training_preflight_manifest_json=root / "training_preflight_preview_manifest.json",
        output_report_csv=root / "tiny_training_smoke_report.csv",
        output_manifest_json=root / "tiny_training_smoke_preview_manifest.json",
        output_md=Path("docs/tiny_covalent_training_smoke_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_resolve_auto_prefers_cuda_when_available_otherwise_cpu():
    device_info = resolve_training_smoke_device_v0("auto")
    assert device_info["requested_device"] == "auto"
    assert device_info["cuda_available"] is torch.cuda.is_available()
    if torch.cuda.is_available():
        assert device_info["resolved_device"] == "cuda:0"
        assert device_info["cuda_device_count"] >= 1
        assert device_info["cuda_device_name"]
    else:
        assert device_info["resolved_device"] == "cpu"
        assert device_info["cuda_device_count"] == 0
        assert device_info["device_fallback_reason"] == "cuda_unavailable_auto_fallback_to_cpu"


def test_move_model_input_moves_tensor_fields_and_preserves_labels():
    model_input = _model_input()
    moved = move_model_input_for_tiny_smoke_v0(model_input, torch.device("cpu"))
    tensor_keys = [key for key, value in moved.items() if isinstance(value, torch.Tensor)]
    assert tensor_keys
    assert all(moved[key].device.type == "cpu" for key in tensor_keys)
    assert moved["sample_id"] == model_input["sample_id"]
    assert moved["protein_reactive_residue_label"] == model_input["protein_reactive_residue_label"]
    assert moved["warhead_type_label"] == model_input["warhead_type_label"]


def test_tiny_forward_shapes_and_loss_finite():
    model_input = move_model_input_for_tiny_smoke_v0(_model_input(), torch.device("cpu"))
    model = TinyCovalentDenoiserV0(hidden_dim=32).to(torch.device("cpu"))
    output = model(model_input)
    assert output["pred_target_x"].shape == (3, 41, 3)
    assert output["pred_target_h"].shape == (3, 41)
    loss = compute_tiny_covalent_loss_v0(output, model_input)
    assert loss["target_atom_count"] > 0
    assert loss["total_loss_finite"] is True
    assert torch.isfinite(loss["total_loss"])


def test_run_tiny_training_step_completes_backward_and_optimizer_step():
    result = run_tiny_training_step_v0(_model_input(), seed=7, lr=1e-3, device="cpu")
    assert result["resolved_device"] == "cpu"
    assert result["initial_loss_finite"] is True
    assert result["post_step_loss_finite"] is True
    assert result["gradient_norm_finite"] is True
    assert result["gradient_norm"] > 0
    assert result["any_gradient_nonzero"] is True
    assert result["optimizer_step_executed"] is True
    assert result["tiny_model_initialized"] is True
    assert result["diffsbdd_model_initialized"] is False
    assert result["checkpoint_loaded"] is False
    assert result["checkpoint_saved"] is False
    assert result["real_training_executed"] is False
    assert result["tiny_training_step_executed"] is True


def test_four_mask_levels_pass_tiny_training_step_on_cpu():
    for index, mask_level in enumerate(MASK_LEVELS):
        result = run_tiny_training_step_v0(_model_input(mask_level=mask_level), seed=index, lr=1e-3, device="cpu")
        assert result["target_atom_count"] > 0
        assert result["initial_loss_finite"] is True
        assert result["post_step_loss_finite"] is True
        assert result["gradient_norm_finite"] is True
        assert result["any_gradient_nonzero"] is True
        assert result["optimizer_step_executed"] is True
        assert result["diffsbdd_model_initialized"] is False
        assert result["checkpoint_loaded"] is False
        assert result["checkpoint_saved"] is False
        assert result["real_training_executed"] is False


def test_check_script_writes_report_manifest_summary_and_no_forbidden_artifacts():
    assert run(_args(device="auto")) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "tiny_training_smoke_report.csv")
    assert len(rows) == 4
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    assert all(row["smoke_status"] == "passed" for row in rows)
    assert all(row["initial_loss_finite"] == "true" for row in rows)
    assert all(row["post_step_loss_finite"] == "true" for row in rows)
    assert all(row["gradient_norm_finite"] == "true" for row in rows)
    assert all(row["any_gradient_nonzero"] == "true" for row in rows)
    assert all(row["optimizer_step_executed"] == "true" for row in rows)
    assert all(row["tiny_model_initialized"] == "true" for row in rows)
    assert all(row["diffsbdd_model_initialized"] == "false" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["checkpoint_saved"] == "false" for row in rows)
    assert all(row["real_training_executed"] == "false" for row in rows)
    preview = json.loads((root / "tiny_training_smoke_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "tiny_covalent_model_training_smoke_v0"
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 4
    assert preview["all_mask_levels_passed"] is True
    assert preview["resolved_device"] == ("cuda:0" if torch.cuda.is_available() else "cpu")
    assert preview["cuda_available"] is torch.cuda.is_available()
    assert preview["all_losses_finite"] is True
    assert preview["all_gradients_finite"] is True
    assert preview["all_gradients_nonzero"] is True
    assert preview["optimizer_step_executed"] is True
    assert preview["tiny_model_initialized"] is True
    assert preview["diffsbdd_model_initialized"] is False
    assert preview["checkpoint_loaded"] is False
    assert preview["checkpoint_saved"] is False
    assert preview["real_training_executed"] is False
    assert preview["archive_created"] is False
    assert preview["recommended_next_step"] == "diffSBDD_input_interface_inspection_or_adapter"
    assert Path("docs/tiny_covalent_training_smoke_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
