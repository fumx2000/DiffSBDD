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

import check_masked_loss_backward_smoke_v0 as smoke_script  # noqa: E402
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import PROTECTED_SOURCE_FILES  # noqa: E402
from covalent_ext.masked_loss_backward_smoke import (  # noqa: E402
    EXPECTED_CONTEXT_COUNTS,
    EXPECTED_TARGET_COUNTS,
    MASK_LEVELS,
    SAFETY_FALSE_FIELDS,
    run_masked_loss_backward_smoke_v0,
    summarize_masked_loss_gradients_v0,
    validate_step10m_outputs_v0,
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
def backward_smoke_result():
    return run_masked_loss_backward_smoke_v0(device="auto")


def test_validate_step10m_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10m_outputs_v0() is True


def test_gradient_summary_for_fake_model():
    model = torch.nn.Sequential(torch.nn.Linear(3, 4), torch.nn.SiLU(), torch.nn.Linear(4, 1))
    output = model(torch.ones(5, 3)).sum()
    output.backward()

    summary = summarize_masked_loss_gradients_v0(model)

    assert summary["parameter_count"] == sum(parameter.numel() for parameter in model.parameters())
    assert summary["trainable_parameter_count"] == summary["parameter_count"]
    assert summary["parameters_with_grad"] > 0
    assert summary["trainable_parameters_with_grad"] > 0
    assert summary["total_grad_norm"] > 0
    assert summary["max_grad_abs"] > 0
    assert summary["finite_gradients"] is True
    assert summary["nonzero_gradients"] is True
    assert summary["grad_nan_count"] == 0
    assert summary["grad_inf_count"] == 0


def test_backward_smoke_covers_all_mask_levels_and_global_flags(backward_smoke_result):
    rows = backward_smoke_result["rows"]
    summary = backward_smoke_result["summary"]

    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    assert summary["stage"] == "masked_loss_backward_smoke_without_optimizer_v0"
    assert summary["previous_stage"] == "masked_loss_dry_run_without_backward_v0"
    assert summary["step10m_masked_loss_dry_run_passed"] is True
    assert summary["mask_levels_checked"] == 4
    assert summary["mask_levels"] == MASK_LEVELS
    assert summary["all_mask_levels_passed"] is True
    assert summary["all_backward_success"] is True
    assert summary["all_gradients_finite"] is True
    assert summary["all_gradients_nonzero"] is True
    assert summary["all_grad_nan_count_zero"] is True
    assert summary["all_grad_inf_count_zero"] is True
    assert summary["all_expected_target_counts"] is True
    assert summary["all_expected_context_counts"] is True
    assert summary["all_sources_unmodified"] is True
    assert summary["all_safety_flags_false_except_backward_called"] is True
    assert summary["all_checks_passed"] is True
    assert summary["recommended_next_step"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint"
    assert summary["checkpoint_loaded"] is False
    assert summary["checkpoint_saved"] is False
    assert summary["training_step_called"] is False
    assert summary["backward_called"] is True
    assert summary["optimizer_step_executed"] is False
    assert summary["trainer_fit_called"] is False
    assert summary["training_executed"] is False
    assert summary["real_finetune_executed"] is False
    assert summary["checkpoint_written"] is False
    assert summary["archive_created"] is False
    assert summary["original_source_files_modified"] is False


def test_each_mask_level_backward_and_gradients_are_valid(backward_smoke_result):
    for row in backward_smoke_result["rows"]:
        mask_level = row["mask_level"]
        assert row["target_atom_count"] == EXPECTED_TARGET_COUNTS[mask_level]
        assert row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[mask_level]
        assert row["ligand_atom_count"] == 104
        assert row["loss_total_dry_finite"] is True
        assert row["loss_total_dry_requires_grad"] is True
        assert row["backward_called"] is True
        assert row["backward_success"] is True
        assert row["parameters_with_grad"] > 0
        assert row["trainable_parameters_with_grad"] > 0
        assert row["total_grad_norm"] > 0
        assert row["max_grad_abs"] > 0
        assert row["finite_gradients"] is True
        assert row["nonzero_gradients"] is True
        assert row["grad_nan_count"] == 0
        assert row["grad_inf_count"] == 0
        assert row["smoke_status"] == "passed"
        assert row["blocking_reasons"] == []
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] is False


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch, backward_smoke_result):
    _copy_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(smoke_script, "run_masked_loss_backward_smoke_v0", lambda device="auto": backward_smoke_result)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert smoke_script.run(device="auto") == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "masked_loss_backward_smoke_report.csv")
    assert len(rows) == 4
    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    for row in rows:
        mask_level = row["mask_level"]
        assert row["stage"] == "masked_loss_backward_smoke_without_optimizer_v0"
        assert row["previous_stage"] == "masked_loss_dry_run_without_backward_v0"
        assert row["step10m_masked_loss_dry_run_passed"] == "true"
        assert row["target_atom_count"] == str(EXPECTED_TARGET_COUNTS[mask_level])
        assert row["context_atom_count"] == str(EXPECTED_CONTEXT_COUNTS[mask_level])
        assert row["ligand_atom_count"] == "104"
        assert row["loss_total_dry_finite"] == "true"
        assert row["loss_total_dry_requires_grad"] == "true"
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
        assert row["smoke_status"] == "passed"
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] == "false"

    manifest = json.loads((root / "masked_loss_backward_smoke_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "masked_loss_backward_smoke_without_optimizer_v0"
    assert manifest["previous_stage"] == "masked_loss_dry_run_without_backward_v0"
    assert manifest["step10m_masked_loss_dry_run_passed"] is True
    assert manifest["mask_levels_checked"] == 4
    assert manifest["mask_levels"] == MASK_LEVELS
    assert manifest["all_mask_levels_passed"] is True
    assert manifest["all_backward_success"] is True
    assert manifest["all_gradients_finite"] is True
    assert manifest["all_gradients_nonzero"] is True
    assert manifest["all_grad_nan_count_zero"] is True
    assert manifest["all_grad_inf_count_zero"] is True
    assert manifest["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert manifest["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    assert manifest["backward_called"] is True
    assert manifest["optimizer_step_executed"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["training_executed"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint"

    assert Path("docs/masked_loss_backward_smoke_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before
