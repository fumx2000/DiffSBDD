import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_diffsbdd_backward_smoke_v0 import run as script_run  # noqa: E402
from covalent_ext.diffsbdd_backward_smoke import (  # noqa: E402
    collect_gradient_summary_v0,
    run_real_diffsbdd_backward_smoke_v0,
    validate_step10g_outputs_v0,
    zero_model_grads_v0,
)


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        device="auto",
        mask_level="A_warhead_only",
        output_report_csv=root / "diffsbdd_backward_smoke_report.csv",
        output_manifest_json=root / "diffsbdd_backward_smoke_preview_manifest.json",
        output_md=Path("docs/diffsbdd_backward_smoke_v0_summary.md"),
    )


def test_step10g_outputs_validate(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10g_outputs_v0() is True


def test_zero_model_grads_clears_gradients_and_gradient_summary_fields():
    model = torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.SiLU(), torch.nn.Linear(4, 1))
    loss = model(torch.ones(2, 3)).mean()
    loss.backward()
    before = collect_gradient_summary_v0(model)
    assert before["parameters_with_grad"] > 0
    assert before["nonzero_gradients"] is True
    zero_model_grads_v0(model)
    after = collect_gradient_summary_v0(model)
    required = {
        "parameter_count",
        "trainable_parameter_count",
        "parameters_with_grad",
        "trainable_parameters_with_grad",
        "total_grad_norm",
        "max_grad_abs",
        "finite_gradients",
        "nonzero_gradients",
        "grad_nan_count",
        "grad_inf_count",
        "top_grad_modules",
        "parameters_without_grad_count",
    }
    assert required.issubset(after)
    assert after["parameters_with_grad"] == 0
    assert after["nonzero_gradients"] is False


def test_run_real_backward_smoke_returns_complete_safety_contract(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    result = run_real_diffsbdd_backward_smoke_v0(device="auto", mask_level="A_warhead_only")
    required = {
        "requested_device",
        "resolved_device",
        "cuda_available",
        "cuda_device_count",
        "cuda_device_name",
        "mask_level",
        "batch_size",
        "model_class_name",
        "model_initialized",
        "model_mode",
        "parameter_count",
        "trainable_parameter_count",
        "forward_called",
        "forward_success",
        "output0_shape",
        "output0_is_loss_like",
        "loss_reduction",
        "scalar_loss",
        "scalar_loss_finite",
        "backward_called",
        "backward_success",
        "parameters_with_grad",
        "trainable_parameters_with_grad",
        "total_grad_norm",
        "max_grad_abs",
        "finite_gradients",
        "nonzero_gradients",
        "grad_nan_count",
        "grad_inf_count",
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
        "checkpoint_written",
        "smoke_status",
        "blocking_reasons",
    }
    assert required.issubset(result)
    assert result["mask_level"] == "A_warhead_only"
    assert result["model_mode"] == "train"
    assert result["loss_reduction"] == "mean"
    assert result["checkpoint_loaded"] is False
    assert result["checkpoint_saved"] is False
    assert result["training_step_called"] is False
    assert result["optimizer_step_executed"] is False
    assert result["trainer_fit_called"] is False
    assert result["training_executed"] is False
    assert result["real_finetune_executed"] is False
    assert result["checkpoint_written"] is False
    if result["backward_success"]:
        assert result["scalar_loss_finite"] is True
        assert result["finite_gradients"] is True
        assert result["nonzero_gradients"] is True
        assert result["parameters_with_grad"] > 0
        assert result["trainable_parameters_with_grad"] > 0
        assert result["total_grad_norm"] > 0
        assert result["max_grad_abs"] > 0
        assert result["grad_nan_count"] == 0
        assert result["grad_inf_count"] == 0
        assert result["smoke_status"] == "passed"
    else:
        assert result["smoke_status"] == "blocked"
        assert result["blocking_reasons"]


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert script_run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_backward_smoke_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "diffsbdd_backward_smoke_without_checkpoint_v0"
    assert row["model_initialized"] == "true"
    assert row["model_mode"] == "train"
    assert row["forward_called"] == "true"
    assert row["forward_success"] == "true"
    assert row["loss_reduction"] == "mean"
    assert row["scalar_loss_finite"] == "true"
    assert row["backward_called"] == "true"
    assert row["backward_success"] == "true"
    assert int(row["parameters_with_grad"]) > 0
    assert int(row["trainable_parameters_with_grad"]) > 0
    assert float(row["total_grad_norm"]) > 0
    assert float(row["max_grad_abs"]) > 0
    assert row["finite_gradients"] == "true"
    assert row["nonzero_gradients"] == "true"
    assert row["grad_nan_count"] == "0"
    assert row["grad_inf_count"] == "0"
    assert row["checkpoint_loaded"] == "false"
    assert row["checkpoint_saved"] == "false"
    assert row["training_step_called"] == "false"
    assert row["optimizer_step_executed"] == "false"
    assert row["trainer_fit_called"] == "false"
    assert row["training_executed"] == "false"
    assert row["real_finetune_executed"] == "false"
    assert row["checkpoint_written"] == "false"
    assert row["smoke_status"] == "passed"
    manifest = json.loads((root / "diffsbdd_backward_smoke_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "diffsbdd_backward_smoke_without_checkpoint_v0"
    assert manifest["previous_stage"] == "diffsbdd_forward_loss_semantics_review_without_backward_v0"
    assert manifest["step10g_loss_semantics_passed"] is True
    assert manifest["backward_success"] is True
    assert manifest["optimizer_step_executed"] is False
    assert manifest["training_step_called"] is False
    assert manifest["checkpoint_written"] is False
    assert manifest["archive_created"] is False
    assert manifest["recommended_next_step"] == "masked_loss_adapter_design_without_diffsbdd_modification"
    assert Path("docs/diffsbdd_backward_smoke_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not (REPO_ROOT / "equivariant_diffusion").joinpath("__definitely_modified_by_test__").exists()
