import csv
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_longer_no_checkpoint_training_dry_run_v0 as dry_run_script  # noqa: E402
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import PROTECTED_SOURCE_FILES  # noqa: E402
from covalent_ext.longer_no_checkpoint_training_dry_run import (  # noqa: E402
    BATCH_SIZE,
    DEFAULT_LR,
    DEFAULT_WEIGHT_DECAY,
    LOOP_NAME,
    MASK_CYCLE,
    MASK_SCHEDULE,
    MAX_STEPS,
    OPTIMIZER_CLASS,
    PREVIOUS_STAGE,
    SEED,
    SHUFFLE,
    STAGE,
    run_longer_no_checkpoint_training_dry_run_v0,
    validate_step10s_outputs_v0,
)
from covalent_ext.masked_loss_dry_run import EXPECTED_CONTEXT_COUNTS, EXPECTED_TARGET_COUNTS  # noqa: E402


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def longer_dry_run_result():
    return run_longer_no_checkpoint_training_dry_run_v0(device="auto", lr=DEFAULT_LR, max_steps=MAX_STEPS)


def test_validate_step10s_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10s_outputs_v0() is True


def test_max_steps_must_remain_twelve():
    result = run_longer_no_checkpoint_training_dry_run_v0(device="auto", lr=DEFAULT_LR, max_steps=11)

    assert result["rows"] == []
    summary = result["summary"]
    assert summary["stage"] == STAGE
    assert summary["previous_stage"] == PREVIOUS_STAGE
    assert summary["max_steps"] == 11
    assert summary["executed_steps"] == 0
    assert summary["dry_run_training_steps_executed"] == 0
    assert summary["stop_triggered"] is True
    assert summary["stop_reason"] == "max_steps_must_equal_12"
    assert summary["all_checks_passed"] is False
    assert summary["checkpoint_loaded"] is False
    assert summary["checkpoint_saved"] is False
    assert summary["training_step_called"] is False
    assert summary["trainer_fit_called"] is False
    assert summary["model_saved"] is False


def test_schedule_is_fixed_three_cycle_sequence():
    assert MASK_SCHEDULE == MASK_CYCLE * 3
    assert len(MASK_SCHEDULE) == 12
    assert Counter(MASK_SCHEDULE) == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert MASK_SCHEDULE[0:4] == MASK_CYCLE
    assert MASK_SCHEDULE[4:8] == MASK_CYCLE
    assert MASK_SCHEDULE[8:12] == MASK_CYCLE


def test_longer_dry_run_global_manifest_fields(longer_dry_run_result):
    summary = longer_dry_run_result["summary"]

    assert summary["stage"] == STAGE
    assert summary["previous_stage"] == PREVIOUS_STAGE
    assert summary["step10s_design_passed"] is True
    assert summary["loop_name"] == LOOP_NAME
    assert summary["optimizer_class"] == OPTIMIZER_CLASS
    assert summary["optimizer_lr"] == DEFAULT_LR
    assert summary["optimizer_weight_decay"] == DEFAULT_WEIGHT_DECAY
    assert summary["max_steps"] == MAX_STEPS
    assert summary["executed_steps"] == MAX_STEPS
    assert summary["dry_run_training_steps_executed"] == MAX_STEPS
    assert summary["mask_schedule"] == MASK_SCHEDULE
    assert summary["mask_levels_seen"] == MASK_SCHEDULE
    assert summary["expected_mask_schedule_followed"] is True
    assert summary["mask_counts_seen"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert summary["batch_size"] == BATCH_SIZE
    assert summary["shuffle"] == SHUFFLE
    assert summary["seed"] == SEED
    assert summary["loss_decrease_required"] is False
    assert summary["quality_claim_allowed"] is False
    assert summary["all_steps_passed"] is True
    assert summary["all_losses_finite"] is True
    assert summary["all_loss_total_requires_grad"] is True
    assert summary["all_backward_success"] is True
    assert summary["all_optimizer_steps_success"] is True
    assert summary["all_gradients_finite"] is True
    assert summary["all_gradients_nonzero"] is True
    assert summary["all_parameter_updates_finite"] is True
    assert summary["all_parameter_updates_nonzero"] is True
    assert summary["all_post_step_params_finite"] is True
    assert summary["stop_triggered"] is False
    assert summary["stop_reason"] == ""
    assert summary["checkpoint_loaded"] is False
    assert summary["checkpoint_saved"] is False
    assert summary["training_step_called"] is False
    assert summary["trainer_fit_called"] is False
    assert summary["checkpoint_written"] is False
    assert summary["archive_created"] is False
    assert summary["model_saved"] is False
    assert summary["formal_training_executed"] is False
    assert summary["real_finetune_executed"] is False
    assert summary["source_modification_allowed"] is False
    assert summary["original_source_files_modified"] is False
    assert summary["forbidden_artifacts_created"] is False
    assert summary["all_checks_passed"] is True
    assert summary["recommended_next_step"] == "longer_no_checkpoint_training_dry_run_review"


def test_longer_dry_run_rows_cover_schedule_and_step_invariants(longer_dry_run_result):
    rows = longer_dry_run_result["rows"]

    assert len(rows) == 12
    assert [row["step"] for row in rows] == list(range(1, 13))
    assert [row["cycle_index"] for row in rows] == [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
    assert [row["mask_level"] for row in rows] == MASK_SCHEDULE
    assert [row["expected_mask_level"] for row in rows] == MASK_SCHEDULE
    assert Counter(row["mask_level"] for row in rows) == {mask_level: 3 for mask_level in MASK_CYCLE}
    for row in rows:
        mask_level = row["mask_level"]
        assert row["sample_ids"] == [
            "BTK_C481_6DI9_pre_reaction",
            "KRAS_G12C_5F2E_pre_reaction",
            "KRAS_G12C_6OIM_pre_reaction",
        ]
        assert row["expected_target_atom_count"] == EXPECTED_TARGET_COUNTS[mask_level]
        assert row["expected_context_atom_count"] == EXPECTED_CONTEXT_COUNTS[mask_level]
        assert row["target_atom_count"] == EXPECTED_TARGET_COUNTS[mask_level]
        assert row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[mask_level]
        assert row["ligand_atom_count"] == 104
        assert row["loss_finite"] is True
        assert row["loss_total_requires_grad"] is True
        assert float(row["loss_original"]) == pytest.approx(float(row["loss_original"]))
        assert float(row["loss_masked_x"]) == pytest.approx(float(row["loss_masked_x"]))
        assert float(row["loss_masked_h"]) == pytest.approx(float(row["loss_masked_h"]))
        assert float(row["loss_total"]) == pytest.approx(float(row["loss_total"]))
        assert row["loss_decrease_required"] is False
        assert row["quality_claim_allowed"] is False
        assert row["backward_called"] is True
        assert row["backward_success"] is True
        assert row["optimizer_class"] == OPTIMIZER_CLASS
        assert row["learning_rate"] == DEFAULT_LR
        assert row["optimizer_step_executed"] is True
        assert row["optimizer_step_success"] is True
        assert row["grad_norm"] > 0
        assert row["max_grad_abs"] > 0
        assert row["finite_gradients"] is True
        assert row["nonzero_gradients"] is True
        assert row["grad_nan_count"] == 0
        assert row["grad_inf_count"] == 0
        assert row["param_delta_norm"] > 0
        assert row["max_param_delta_abs"] > 0
        assert row["finite_parameter_delta"] is True
        assert row["nonzero_parameter_delta"] is True
        assert row["post_step_param_nan_count"] == 0
        assert row["post_step_param_inf_count"] == 0
        assert row["checkpoint_loaded"] is False
        assert row["checkpoint_saved"] is False
        assert row["training_step_called"] is False
        assert row["trainer_fit_called"] is False
        assert row["checkpoint_written"] is False
        assert row["archive_created"] is False
        assert row["model_saved"] is False
        assert row["formal_training_executed"] is False
        assert row["real_finetune_executed"] is False
        assert row["original_source_files_modified"] is False
        assert row["forbidden_artifacts_created"] is False
        assert row["stop_triggered"] is False
        assert row["stop_reason"] == ""
        assert row["step_status"] == "passed"
        assert row["blocking_reasons"] == []


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch, longer_dry_run_result):
    _copy_workspace(tmp_path, monkeypatch)
    monkeypatch.setattr(
        dry_run_script,
        "run_longer_no_checkpoint_training_dry_run_v0",
        lambda device="auto", lr=DEFAULT_LR, max_steps=MAX_STEPS: longer_dry_run_result,
    )
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert dry_run_script.run(device="auto", lr=DEFAULT_LR, max_steps=MAX_STEPS) == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "longer_no_checkpoint_training_dry_run_report.csv")
    assert len(rows) == 12
    assert [row["mask_level"] for row in rows] == MASK_SCHEDULE
    for index, row in enumerate(rows, start=1):
        mask_level = row["mask_level"]
        assert row["stage"] == STAGE
        assert row["previous_stage"] == PREVIOUS_STAGE
        assert row["step10s_design_passed"] == "true"
        assert row["loop_name"] == LOOP_NAME
        assert row["step"] == str(index)
        assert row["cycle_index"] == str(((index - 1) // 4) + 1)
        assert row["expected_mask_level"] == mask_level
        assert row["target_atom_count"] == str(EXPECTED_TARGET_COUNTS[mask_level])
        assert row["context_atom_count"] == str(EXPECTED_CONTEXT_COUNTS[mask_level])
        assert row["ligand_atom_count"] == "104"
        assert row["loss_finite"] == "true"
        assert row["loss_total_requires_grad"] == "true"
        assert row["loss_decrease_required"] == "false"
        assert row["quality_claim_allowed"] == "false"
        assert row["backward_called"] == "true"
        assert row["backward_success"] == "true"
        assert row["optimizer_class"] == OPTIMIZER_CLASS
        assert row["learning_rate"] == str(DEFAULT_LR)
        assert row["optimizer_step_executed"] == "true"
        assert row["optimizer_step_success"] == "true"
        assert float(row["grad_norm"]) > 0
        assert float(row["max_grad_abs"]) > 0
        assert row["finite_gradients"] == "true"
        assert row["nonzero_gradients"] == "true"
        assert row["grad_nan_count"] == "0"
        assert row["grad_inf_count"] == "0"
        assert float(row["param_delta_norm"]) > 0
        assert float(row["max_param_delta_abs"]) > 0
        assert row["finite_parameter_delta"] == "true"
        assert row["nonzero_parameter_delta"] == "true"
        assert row["post_step_param_nan_count"] == "0"
        assert row["post_step_param_inf_count"] == "0"
        assert row["checkpoint_loaded"] == "false"
        assert row["checkpoint_saved"] == "false"
        assert row["training_step_called"] == "false"
        assert row["trainer_fit_called"] == "false"
        assert row["checkpoint_written"] == "false"
        assert row["archive_created"] == "false"
        assert row["model_saved"] == "false"
        assert row["formal_training_executed"] == "false"
        assert row["real_finetune_executed"] == "false"
        assert row["original_source_files_modified"] == "false"
        assert row["forbidden_artifacts_created"] == "false"
        assert row["stop_triggered"] == "false"
        assert row["stop_reason"] == ""
        assert row["step_status"] == "passed"
        assert row["blocking_reasons"] == ""

    manifest = json.loads(
        (root / "longer_no_checkpoint_training_dry_run_preview_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == PREVIOUS_STAGE
    assert manifest["step10s_design_passed"] is True
    assert manifest["loop_name"] == LOOP_NAME
    assert manifest["optimizer_class"] == OPTIMIZER_CLASS
    assert manifest["optimizer_lr"] == DEFAULT_LR
    assert manifest["optimizer_weight_decay"] == DEFAULT_WEIGHT_DECAY
    assert manifest["max_steps"] == MAX_STEPS
    assert manifest["executed_steps"] == MAX_STEPS
    assert manifest["dry_run_training_steps_executed"] == MAX_STEPS
    assert manifest["mask_schedule"] == MASK_SCHEDULE
    assert manifest["mask_levels_seen"] == MASK_SCHEDULE
    assert manifest["mask_counts_seen"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert manifest["all_checks_passed"] is True
    assert manifest["checkpoint_loaded"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_written"] is False
    assert manifest["archive_created"] is False
    assert manifest["model_saved"] is False
    assert manifest["formal_training_executed"] is False
    assert manifest["real_finetune_executed"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["recommended_next_step"] == "longer_no_checkpoint_training_dry_run_review"
    assert Path("docs/longer_no_checkpoint_training_dry_run_v0_summary.md").is_file()

    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not list(root.rglob("*.ckpt"))
    assert not list(root.rglob("*.pth"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before


def test_sources_do_not_call_checkpoint_trainer_or_model_save_apis():
    source_paths = [
        REPO_ROOT / "src" / "covalent_ext" / "longer_no_checkpoint_training_dry_run.py",
        REPO_ROOT / "scripts" / "check_longer_no_checkpoint_training_dry_run_v0.py",
        REPO_ROOT / "tests" / "test_longer_no_checkpoint_training_dry_run_v0.py",
    ]
    forbidden_call_tokens = [
        "trainer" + "." + "fit" + "(",
        "." + "fit" + "(",
        "training" + "_step" + "(",
        "torch" + "." + "save" + "(",
        "torch" + "." + "load" + "(",
        "save" + "_checkpoint" + "(",
        "load" + "_from" + "_checkpoint" + "(",
    ]
    for source_path in source_paths:
        text = source_path.read_text(encoding="utf-8")
        for token in forbidden_call_tokens:
            assert token not in text
