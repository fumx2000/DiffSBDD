import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_first_checkpointed_training_dry_run_v0 as checkpoint_script  # noqa: E402
from covalent_ext.first_checkpointed_training_dry_run import (  # noqa: E402
    CHECKPOINT_FILENAME,
    CHECKPOINT_PATH,
    DEFAULT_LR,
    DEFAULT_WEIGHT_DECAY,
    FORBIDDEN_PAYLOAD_KEYS,
    LOSS_WEIGHTS,
    MASK_CYCLE,
    MASK_SCHEDULE,
    MAX_STEPS,
    OPTIMIZER_CLASS,
    REQUIRED_PAYLOAD_FIELDS,
    RUN_NAME,
    RUN_ROOT,
    SEED,
    SHUFFLE,
    STAGE,
    validate_checkpoint_payload_schema_v0,
    prepare_run_root_v0,
    run_first_checkpointed_training_dry_run_v0,
    validate_step10v_outputs_v0,
)
from covalent_ext.masked_loss_dry_run import EXPECTED_CONTEXT_COUNTS, EXPECTED_TARGET_COUNTS  # noqa: E402


PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_validate_step10v_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)

    assert validate_step10v_outputs_v0() is True


def test_max_steps_must_remain_twelve_and_does_not_create_run_root(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)

    result = run_first_checkpointed_training_dry_run_v0(device="auto", lr=DEFAULT_LR, max_steps=11)

    assert result["rows"] == []
    summary = result["summary"]
    assert summary["stage"] == STAGE
    assert summary["step10v_policy_passed"] is True
    assert summary["max_steps"] == 11
    assert summary["executed_steps"] == 0
    assert summary["checkpoint_saved"] is False
    assert summary["checkpoint_loaded_for_resume_smoke"] is False
    assert summary["stop_triggered"] is True
    assert summary["stop_reason"] == "max_steps_must_equal_12"
    assert not RUN_ROOT.exists()


def test_existing_run_root_blocks_without_overwrite(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    RUN_ROOT.mkdir(parents=True)

    result = run_first_checkpointed_training_dry_run_v0(device="auto", lr=DEFAULT_LR, max_steps=MAX_STEPS)

    assert result["rows"] == []
    summary = result["summary"]
    assert summary["step10v_policy_passed"] is True
    assert summary["checkpoint_saved"] is False
    assert summary["stop_reason"] == "run_root_exists"
    assert not CHECKPOINT_PATH.exists()


def test_prepare_run_root_overwrite_refuses_unknown_files(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    unknown = RUN_ROOT / "unexpected.txt"
    unknown.parent.mkdir(parents=True)
    unknown.write_text("unknown", encoding="utf-8")

    result = prepare_run_root_v0(overwrite=True)

    assert result["prepared"] is False
    assert result["blocking_reasons"]
    assert unknown.exists()


def test_checkpoint_payload_schema_rejects_missing_or_forbidden_objects():
    payload = {field: None for field in REQUIRED_PAYLOAD_FIELDS}
    payload.update(
        {
            "schema_version": STAGE,
            "stage": STAGE,
            "run_name": RUN_NAME,
            "model_config_path": "configs/crossdock_fullatom_cond.yml",
            "model_state_dict": {"weight": torch.zeros(1)},
            "optimizer_state_dict": {"state": {0: {"step": torch.tensor(1.0)}}},
            "optimizer_class": OPTIMIZER_CLASS,
            "optimizer_lr": DEFAULT_LR,
            "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
            "completed_steps": MAX_STEPS,
            "max_steps": MAX_STEPS,
            "mask_schedule": MASK_SCHEDULE,
            "loss_weights": LOSS_WEIGHTS,
            "batch_size": 3,
            "shuffle": SHUFFLE,
            "seed": SEED,
            "sample_ids": ["sample"],
            "loss_total_by_step": {str(index): float(index) for index in range(1, 13)},
            "grad_norm_by_step": {str(index): float(index) for index in range(1, 13)},
            "param_delta_norm_by_step": {str(index): float(index) for index in range(1, 13)},
            "source_modification_allowed": False,
            "formal_training_executed": False,
            "real_finetune_executed": False,
        }
    )

    assert validate_checkpoint_payload_schema_v0(payload)["valid"] is True
    forbidden = dict(payload)
    forbidden["model"] = object()
    rejected = validate_checkpoint_payload_schema_v0(forbidden)
    assert rejected["valid"] is False
    assert any(reason.startswith("forbidden_payload_field:model") for reason in rejected["blocking_reasons"])
    assert "model" in FORBIDDEN_PAYLOAD_KEYS


def test_script_run_writes_single_checkpoint_metadata_resume_reports_and_summary(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)

    assert checkpoint_script.run(device="auto", lr=DEFAULT_LR, max_steps=MAX_STEPS) == 0

    report_path = RUN_ROOT / "reports" / "first_checkpointed_training_dry_run_report.csv"
    manifest_path = RUN_ROOT / "metadata" / "first_checkpointed_training_dry_run_manifest.json"
    metadata_path = RUN_ROOT / "metadata" / "checkpoint_metadata.json"
    resume_report_path = RUN_ROOT / "resume_smoke" / "resume_smoke_report.csv"
    resume_manifest_path = RUN_ROOT / "resume_smoke" / "resume_smoke_manifest.json"
    summary_path = Path("docs/first_checkpointed_training_dry_run_v0_summary.md")

    for path in [report_path, manifest_path, metadata_path, resume_report_path, resume_manifest_path, summary_path]:
        assert path.is_file()

    rows = _read_csv(report_path)
    assert len(rows) == 12
    assert [row["step"] for row in rows] == [str(index) for index in range(1, 13)]
    assert [row["mask_level"] for row in rows] == MASK_SCHEDULE
    assert [row["cycle_index"] for row in rows] == ["1", "1", "1", "1", "2", "2", "2", "2", "3", "3", "3", "3"]
    assert [row["checkpoint_saved"] for row in rows[:-1]] == ["false"] * 11
    assert rows[-1]["checkpoint_saved"] == "true"
    assert rows[-1]["checkpoint_written"] == "true"
    assert rows[-1]["checkpoint_path"] == str(CHECKPOINT_PATH)
    assert rows[-1]["resume_smoke_passed"] == "true"
    assert rows[-1]["checkpoint_loaded_for_resume_smoke"] == "true"
    assert rows[-1]["model_state_loaded"] == "true"
    assert rows[-1]["optimizer_state_loaded"] == "true"
    assert rows[-1]["second_checkpoint_saved"] == "false"
    for row in rows:
        mask_level = row["mask_level"]
        assert row["stage"] == STAGE
        assert row["step10v_policy_passed"] == "true"
        assert row["run_name"] == RUN_NAME
        assert row["target_atom_count"] == str(EXPECTED_TARGET_COUNTS[mask_level])
        assert row["context_atom_count"] == str(EXPECTED_CONTEXT_COUNTS[mask_level])
        assert row["ligand_atom_count"] == "104"
        assert row["loss_finite"] == "true"
        assert row["backward_called"] == "true"
        assert row["backward_success"] == "true"
        assert row["optimizer_step_executed"] == "true"
        assert row["optimizer_step_success"] == "true"
        assert float(row["loss_total"]) > 0
        assert float(row["grad_norm"]) > 0
        assert float(row["param_delta_norm"]) > 0
        assert row["finite_gradients"] == "true"
        assert row["nonzero_gradients"] == "true"
        assert row["finite_parameter_delta"] == "true"
        assert row["nonzero_parameter_delta"] == "true"
        assert row["training_step_called"] == "false"
        assert row["trainer_fit_called"] == "false"
        assert row["archive_created"] == "false"
        assert row["model_saved"] == "false"
        assert row["formal_training_executed"] == "false"
        assert row["real_finetune_executed"] == "false"
        assert row["step_status"] == "passed"
        assert row["blocking_reasons"] == ""

    manifest = _load_json(manifest_path)
    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == "checkpoint_output_policy_design_v0"
    assert manifest["step10v_policy_passed"] is True
    assert manifest["run_name"] == RUN_NAME
    assert manifest["run_root"] == str(RUN_ROOT)
    assert manifest["max_steps"] == 12
    assert manifest["executed_steps"] == 12
    assert manifest["dry_run_training_steps_executed"] == 12
    assert manifest["mask_schedule"] == MASK_SCHEDULE
    assert manifest["mask_counts_seen"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert manifest["all_steps_passed"] is True
    assert manifest["all_losses_finite"] is True
    assert manifest["all_backward_success"] is True
    assert manifest["all_optimizer_steps_success"] is True
    assert manifest["all_gradients_finite"] is True
    assert manifest["all_gradients_nonzero"] is True
    assert manifest["all_parameter_updates_finite"] is True
    assert manifest["all_parameter_updates_nonzero"] is True
    assert manifest["checkpoint_saved"] is True
    assert manifest["checkpoint_path"] == str(CHECKPOINT_PATH)
    assert manifest["checkpoint_filename"] == CHECKPOINT_FILENAME
    assert manifest["checkpoint_count"] == 1
    assert len(manifest["checkpoint_sha256"]) == 64
    assert manifest["checkpoint_size_bytes"] > 0
    assert manifest["checkpoint_payload_schema_valid"] is True
    assert manifest["checkpoint_metadata_written"] is True
    assert manifest["checkpoint_loaded_for_resume_smoke"] is True
    assert manifest["resume_smoke_passed"] is True
    assert manifest["model_state_loaded"] is True
    assert manifest["optimizer_state_loaded"] is True
    assert manifest["completed_steps_verified"] is True
    assert manifest["mask_schedule_verified"] is True
    assert manifest["parameter_shapes_verified"] is True
    assert manifest["optimizer_step_during_resume_smoke"] is False
    assert manifest["second_checkpoint_saved"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["model_saved"] is False
    assert manifest["formal_training_executed"] is False
    assert manifest["real_finetune_executed"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["unexpected_checkpoint_files_created"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "first_checkpointed_training_dry_run_review"

    checkpoint_metadata = _load_json(metadata_path)
    assert checkpoint_metadata["checkpoint_saved"] is True
    assert checkpoint_metadata["checkpoint_path"] == str(CHECKPOINT_PATH)
    assert checkpoint_metadata["checkpoint_filename"] == CHECKPOINT_FILENAME
    assert checkpoint_metadata["checkpoint_sha256"] == manifest["checkpoint_sha256"]
    assert checkpoint_metadata["checkpoint_size_bytes"] == manifest["checkpoint_size_bytes"]
    assert checkpoint_metadata["checkpoint_payload_schema_valid"] is True
    assert checkpoint_metadata["completed_steps"] == 12
    assert checkpoint_metadata["max_steps"] == 12
    assert checkpoint_metadata["mask_schedule"] == MASK_SCHEDULE
    assert checkpoint_metadata["source_modification_allowed"] is False
    assert checkpoint_metadata["formal_training_executed"] is False
    assert checkpoint_metadata["real_finetune_executed"] is False

    resume_rows = _read_csv(resume_report_path)
    assert len(resume_rows) == 1
    resume_row = resume_rows[0]
    assert resume_row["checkpoint_loaded"] == "true"
    assert resume_row["model_state_loaded"] == "true"
    assert resume_row["optimizer_state_loaded"] == "true"
    assert resume_row["completed_steps_verified"] == "true"
    assert resume_row["mask_schedule_verified"] == "true"
    assert resume_row["parameter_shapes_verified"] == "true"
    assert resume_row["optimizer_step_during_resume_smoke"] == "false"
    assert resume_row["second_checkpoint_saved"] == "false"
    assert resume_row["trainer_fit_called"] == "false"
    assert resume_row["training_step_called"] == "false"
    assert resume_row["model_saved"] == "false"
    assert resume_row["resume_smoke_passed"] == "true"
    assert resume_row["blocking_reasons"] == ""

    resume_manifest = _load_json(resume_manifest_path)
    assert resume_manifest["resume_smoke_passed"] is True
    assert resume_manifest["checkpoint_loaded"] is True
    assert resume_manifest["optimizer_step_during_resume_smoke"] is False
    assert resume_manifest["second_checkpoint_saved"] is False

    checkpoint_files = sorted(RUN_ROOT.rglob("*.pt"))
    assert checkpoint_files == [CHECKPOINT_PATH]
    assert not list(RUN_ROOT.rglob("*.pkl"))
    assert not list(RUN_ROOT.rglob("*.lmdb"))
    assert not list(RUN_ROOT.rglob("*.tar"))
    assert not list(RUN_ROOT.rglob("*.zip"))
    assert not list(RUN_ROOT.rglob("*.tgz"))
    assert not list(RUN_ROOT.rglob("*.ckpt"))
    assert not list(RUN_ROOT.rglob("*.pth"))

    payload = torch.load(CHECKPOINT_PATH, map_location="cpu")
    assert validate_checkpoint_payload_schema_v0(payload)["valid"] is True
    assert payload["schema_version"] == STAGE
    assert payload["stage"] == STAGE
    assert payload["completed_steps"] == 12
    assert payload["mask_schedule"] == MASK_SCHEDULE
    assert payload["loss_weights"] == LOSS_WEIGHTS
    assert payload["source_modification_allowed"] is False
    assert payload["formal_training_executed"] is False
    assert payload["real_finetune_executed"] is False
    assert set(FORBIDDEN_PAYLOAD_KEYS).isdisjoint(payload)
    assert len(payload["model_state_dict"]) > 0
    assert len(payload["optimizer_state_dict"]["state"]) > 0
    assert len(payload["loss_total_by_step"]) == 12
    assert len(payload["grad_norm_by_step"]) == 12
    assert len(payload["param_delta_norm_by_step"]) == 12

    assert "first checkpointed dry run" in summary_path.read_text(encoding="utf-8")


def test_source_text_does_not_use_forbidden_training_or_checkpoint_helpers():
    paths = [
        REPO_ROOT / "src" / "covalent_ext" / "first_checkpointed_training_dry_run.py",
        REPO_ROOT / "scripts" / "check_first_checkpointed_training_dry_run_v0.py",
        REPO_ROOT / "tests" / "test_first_checkpointed_training_dry_run_v0.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    forbidden_tokens = [
        "load_from" + "_checkpoint",
        "save" + "_checkpoint",
        "trainer" + "." + "fit",
        "." + "fit(",
        "training" + "_step(",
    ]
    for forbidden in forbidden_tokens:
        assert forbidden not in text


def test_protected_diffsbdd_sources_are_unmodified():
    result = subprocess.run(
        ["git", "diff", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.stdout == ""
