import csv
import json
import shutil
import sys
from pathlib import Path

import pytest
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_masked_loss_optimizer_smoke_v0 as smoke_script  # noqa: E402
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import PROTECTED_SOURCE_FILES  # noqa: E402
from covalent_ext.masked_loss_optimizer_smoke import (  # noqa: E402
    DEFAULT_LR,
    DEFAULT_WEIGHT_DECAY,
    EXPECTED_CONTEXT_COUNTS,
    EXPECTED_TARGET_COUNTS,
    MASK_LEVELS,
    OPTIMIZER_CLASS,
    SAFETY_FALSE_FIELDS,
    build_optimizer_v0,
    run_masked_loss_optimizer_smoke_v0,
    snapshot_trainable_parameters_v0,
    summarize_parameter_update_v0,
    validate_step10n_outputs_v0,
)


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def optimizer_smoke_result():
    return run_masked_loss_optimizer_smoke_v0(device="auto", lr=DEFAULT_LR)


def test_validate_step10n_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10n_outputs_v0() is True


def test_parameter_snapshot_and_update_summary_for_fake_model():
    model = torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.SiLU(), torch.nn.Linear(4, 1))
    optimizer = build_optimizer_v0(model, lr=1e-3)
    before = snapshot_trainable_parameters_v0(model)
    loss = model(torch.ones(5, 3)).sum()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

    summary = summarize_parameter_update_v0(model, before)

    assert summary["parameters_compared"] == len(before)
    assert summary["trainable_parameters_compared"] == len(before)
    assert summary["parameters_changed"] > 0
    assert summary["trainable_parameters_changed"] > 0
    assert summary["total_param_delta_norm"] > 0
    assert summary["max_param_delta_abs"] > 0
    assert summary["finite_parameter_delta"] is True
    assert summary["nonzero_parameter_delta"] is True
    assert summary["post_step_param_nan_count"] == 0
    assert summary["post_step_param_inf_count"] == 0


def test_optimizer_smoke_covers_all_mask_levels_and_global_flags(optimizer_smoke_result):
    rows = optimizer_smoke_result["rows"]
    summary = optimizer_smoke_result["summary"]

    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    assert summary["stage"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
    assert summary["previous_stage"] == "masked_loss_backward_smoke_without_optimizer_v0"
    assert summary["step10n_backward_smoke_passed"] is True
    assert summary["optimizer_class"] == OPTIMIZER_CLASS
    assert summary["optimizer_lr"] == DEFAULT_LR
    assert summary["optimizer_weight_decay"] == DEFAULT_WEIGHT_DECAY
    assert summary["mask_levels_checked"] == 4
    assert summary["mask_levels"] == MASK_LEVELS
    assert summary["all_mask_levels_passed"] is True
    assert summary["all_backward_success"] is True
    assert summary["all_optimizer_steps_success"] is True
    assert summary["all_gradients_finite"] is True
    assert summary["all_gradients_nonzero"] is True
    assert summary["all_parameter_updates_finite"] is True
    assert summary["all_parameter_updates_nonzero"] is True
    assert summary["all_post_step_params_finite"] is True
    assert summary["all_expected_target_counts"] is True
    assert summary["all_expected_context_counts"] is True
    assert summary["all_sources_unmodified"] is True
    assert summary["all_checks_passed"] is True
    assert summary["checkpoint_loaded"] is False
    assert summary["checkpoint_saved"] is False
    assert summary["training_step_called"] is False
    assert summary["backward_called"] is True
    assert summary["optimizer_step_executed"] is True
    assert summary["trainer_fit_called"] is False
    assert summary["training_executed"] is False
    assert summary["real_finetune_executed"] is False
    assert summary["checkpoint_written"] is False
    assert summary["archive_created"] is False
    assert summary["model_saved"] is False
    assert summary["original_source_files_modified"] is False
    assert summary["recommended_next_step"] == "training_loop_design_without_checkpoint"


def test_each_mask_level_optimizer_step_and_parameter_updates_are_valid(optimizer_smoke_result):
    for row in optimizer_smoke_result["rows"]:
        mask_level = row["mask_level"]
        assert row["target_atom_count"] == EXPECTED_TARGET_COUNTS[mask_level]
        assert row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[mask_level]
        assert row["ligand_atom_count"] == 104
        assert row["loss_total_dry_finite"] is True
        assert row["loss_total_dry_requires_grad"] is True
        assert row["backward_called"] is True
        assert row["backward_success"] is True
        assert row["optimizer_class"] == OPTIMIZER_CLASS
        assert row["optimizer_lr"] == DEFAULT_LR
        assert row["optimizer_weight_decay"] == DEFAULT_WEIGHT_DECAY
        assert row["optimizer_step_executed"] is True
        assert row["optimizer_step_success"] is True
        assert row["parameters_with_grad"] > 0
        assert row["trainable_parameters_with_grad"] > 0
        assert row["total_grad_norm"] > 0
        assert row["max_grad_abs"] > 0
        assert row["finite_gradients"] is True
        assert row["nonzero_gradients"] is True
        assert row["grad_nan_count"] == 0
        assert row["grad_inf_count"] == 0
        assert row["parameters_compared"] > 0
        assert row["trainable_parameters_compared"] > 0
        assert row["parameters_changed"] > 0
        assert row["trainable_parameters_changed"] > 0
        assert row["total_param_delta_norm"] > 0
        assert row["max_param_delta_abs"] > 0
        assert row["finite_parameter_delta"] is True
        assert row["nonzero_parameter_delta"] is True
        assert row["post_step_param_nan_count"] == 0
        assert row["post_step_param_inf_count"] == 0
        assert row["smoke_status"] == "passed"
        assert row["blocking_reasons"] == []
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] is False


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch, optimizer_smoke_result):
    _copy_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(
        smoke_script,
        "run_masked_loss_optimizer_smoke_v0",
        lambda device="auto", lr=DEFAULT_LR: optimizer_smoke_result,
    )
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert smoke_script.run(device="auto", lr=DEFAULT_LR) == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "masked_loss_optimizer_smoke_report.csv")
    assert len(rows) == 4
    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    for row in rows:
        mask_level = row["mask_level"]
        assert row["stage"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
        assert row["previous_stage"] == "masked_loss_backward_smoke_without_optimizer_v0"
        assert row["step10n_backward_smoke_passed"] == "true"
        assert row["target_atom_count"] == str(EXPECTED_TARGET_COUNTS[mask_level])
        assert row["context_atom_count"] == str(EXPECTED_CONTEXT_COUNTS[mask_level])
        assert row["ligand_atom_count"] == "104"
        assert row["loss_total_dry_finite"] == "true"
        assert row["loss_total_dry_requires_grad"] == "true"
        assert row["backward_called"] == "true"
        assert row["backward_success"] == "true"
        assert row["optimizer_class"] == OPTIMIZER_CLASS
        assert row["optimizer_lr"] == str(DEFAULT_LR)
        assert row["optimizer_weight_decay"] == str(DEFAULT_WEIGHT_DECAY)
        assert row["optimizer_step_executed"] == "true"
        assert row["optimizer_step_success"] == "true"
        assert int(row["parameters_with_grad"]) > 0
        assert int(row["trainable_parameters_with_grad"]) > 0
        assert float(row["total_grad_norm"]) > 0
        assert float(row["max_grad_abs"]) > 0
        assert row["finite_gradients"] == "true"
        assert row["nonzero_gradients"] == "true"
        assert row["grad_nan_count"] == "0"
        assert row["grad_inf_count"] == "0"
        assert int(row["parameters_changed"]) > 0
        assert int(row["trainable_parameters_changed"]) > 0
        assert float(row["total_param_delta_norm"]) > 0
        assert float(row["max_param_delta_abs"]) > 0
        assert row["finite_parameter_delta"] == "true"
        assert row["nonzero_parameter_delta"] == "true"
        assert row["post_step_param_nan_count"] == "0"
        assert row["post_step_param_inf_count"] == "0"
        assert row["smoke_status"] == "passed"
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] == "false"

    manifest = json.loads((root / "masked_loss_optimizer_smoke_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
    assert manifest["previous_stage"] == "masked_loss_backward_smoke_without_optimizer_v0"
    assert manifest["step10n_backward_smoke_passed"] is True
    assert manifest["optimizer_class"] == OPTIMIZER_CLASS
    assert manifest["optimizer_lr"] == DEFAULT_LR
    assert manifest["optimizer_weight_decay"] == DEFAULT_WEIGHT_DECAY
    assert manifest["mask_levels_checked"] == 4
    assert manifest["mask_levels"] == MASK_LEVELS
    assert manifest["all_optimizer_steps_success"] is True
    assert manifest["all_parameter_updates_finite"] is True
    assert manifest["all_parameter_updates_nonzero"] is True
    assert manifest["all_post_step_params_finite"] is True
    assert manifest["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert manifest["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    assert manifest["backward_called"] is True
    assert manifest["optimizer_step_executed"] is True
    assert manifest["trainer_fit_called"] is False
    assert manifest["training_executed"] is False
    assert manifest["checkpoint_loaded"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["checkpoint_written"] is False
    assert manifest["archive_created"] is False
    assert manifest["model_saved"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "training_loop_design_without_checkpoint"

    assert Path("docs/masked_loss_optimizer_smoke_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before
