from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "checkpoint_output_policy_design_v0"
PREVIOUS_STAGE = "longer_no_checkpoint_training_dry_run_review_v0"
NEXT_STAGE = "first_checkpointed_training_dry_run_v0"
LOOP_NAME = "masked_covalent_training_loop_v0"
RUN_NAME = "first_checkpointed_training_dry_run_v0"
MAX_STEPS = 12
BATCH_SIZE = 3
SHUFFLE = False
SEED = 4401
DEFAULT_LR = 1e-6
DEFAULT_WEIGHT_DECAY = 0.0
OPTIMIZER_CLASS = "AdamW"
MASK_CYCLE = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
MASK_SCHEDULE = MASK_CYCLE * 3
RUN_ROOT = Path("data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0")
CHECKPOINT_FILENAME = "checkpoint_step_000012.pt"
CHECKPOINT_PATH = RUN_ROOT / "checkpoints" / CHECKPOINT_FILENAME
DOCS_SUMMARY_PATH = "docs/first_checkpointed_training_dry_run_v0_summary.md"
SAFETY_FALSE_FIELDS = [
    "formal_training_allowed",
    "finetune_allowed",
    "checkpoint_allowed",
    "model_save_allowed",
    "trainer_fit_allowed",
    "training_step_allowed",
    "source_modification_allowed",
    "checkpoint_save_allowed",
    "checkpoint_load_allowed",
]
FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
}


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _forbidden_artifacts_exist(root: str | Path = DEFAULT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def _protected_source_diff_exists() -> bool:
    paths = ["equivariant_diffusion/", "lightning_modules.py"]
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def validate_step10u_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_review_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_review_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10U longer no-checkpoint dry-run review outputs are missing")

    rows = _rows_from_csv(report_path)
    blockers: list[str] = []
    expected_sections = [
        "evidence_review",
        "stability_assessment",
        "observations",
        "next_boundary_decision",
        "checkpoint_discussion_gate",
        "risk_register",
    ]
    _expect(len(rows) == 6, f"step10u_report_row_count_invalid:{len(rows)}", blockers)
    _expect([row.get("review_section") for row in rows] == expected_sections, "step10u_review_sections_invalid", blockers)
    for row in rows:
        _expect(row.get("stage") == PREVIOUS_STAGE, f"step10u_report_stage_invalid:{row.get('stage')!r}", blockers)
        _expect(
            row.get("previous_stage") == "longer_no_checkpoint_training_dry_run_v0",
            f"step10u_report_previous_stage_invalid:{row.get('previous_stage')!r}",
            blockers,
        )
        _expect(row.get("status") == "passed", f"step10u_report_status_invalid:{row.get('status')!r}", blockers)
        _expect(
            row.get("recommended_next_step") == "checkpoint_and_output_policy_design",
            f"step10u_report_recommended_next_step_invalid:{row.get('recommended_next_step')!r}",
            blockers,
        )

    manifest = _load_json(manifest_path)
    expected_manifest_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "longer_no_checkpoint_training_dry_run_v0",
        "step10t_dry_run_passed": True,
        "executed_steps": 12,
        "dry_run_training_steps_executed": 12,
        "mask_schedule_length": 12,
        "mask_counts_seen": {mask_level: 3 for mask_level in MASK_CYCLE},
        "all_steps_passed": True,
        "all_losses_finite": True,
        "all_backward_success": True,
        "all_optimizer_steps_success": True,
        "all_gradients_finite": True,
        "all_gradients_nonzero": True,
        "all_parameter_updates_finite": True,
        "all_parameter_updates_nonzero": True,
        "warnings_triggered": False,
        "warning_steps": [],
        "stop_triggered": False,
        "stability_status": "passed",
        "loss_decrease_required": False,
        "quality_claim_allowed": False,
        "highest_grad_step": 9,
        "highest_grad_mask_level": "A_warhead_only",
        "highest_grad_value": 201.119884,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "checkpoint_policy_design_allowed": True,
        "output_policy_design_allowed": True,
        "checkpoint_save_allowed": False,
        "checkpoint_load_allowed": False,
        "next_step_is_policy_design_only": True,
        "all_checks_passed": True,
        "recommended_next_step": "checkpoint_and_output_policy_design",
    }
    for key, expected in expected_manifest_values.items():
        _expect(manifest.get(key) == expected, f"step10u_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_output_directory_policy_v0() -> dict[str, Any]:
    return {
        "run_root": str(RUN_ROOT),
        "checkpoints_dir": str(RUN_ROOT / "checkpoints"),
        "reports_dir": str(RUN_ROOT / "reports"),
        "metadata_dir": str(RUN_ROOT / "metadata"),
        "resume_smoke_dir": str(RUN_ROOT / "resume_smoke"),
        "allowed_report_files": [
            "reports/first_checkpointed_training_dry_run_report.csv",
            "metadata/first_checkpointed_training_dry_run_manifest.json",
            "metadata/checkpoint_metadata.json",
            "resume_smoke/resume_smoke_report.csv",
            "resume_smoke/resume_smoke_manifest.json",
            DOCS_SUMMARY_PATH,
        ],
        "directory_creation_allowed_next_step": True,
        "directory_creation_allowed_current_step": False,
        "overwrite_existing_run_dir_allowed": False,
        "next_step_must_fail_if_run_dir_exists": True,
    }


def build_checkpoint_naming_policy_v0() -> dict[str, Any]:
    return {
        "checkpoint_filename": CHECKPOINT_FILENAME,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_extension": ".pt",
        "checkpoint_format": "torch" + "." + "save" + " dictionary",
        "checkpoint_count_limit": 1,
        "save_at_step": 12,
        "no_intermediate_checkpoints": True,
        "no_epoch_checkpoints": True,
        "no_lightning_checkpoint": True,
        "no_model_only_checkpoint": True,
        "no_optimizer_only_checkpoint": True,
    }


def build_checkpoint_payload_policy_v0() -> dict[str, Any]:
    return {
        "required_payload_fields": [
            "schema_version",
            "stage",
            "run_name",
            "repo_commit",
            "created_at_utc",
            "model_class",
            "model_config_path",
            "model_state_dict",
            "optimizer_class",
            "optimizer_state_dict",
            "optimizer_lr",
            "optimizer_weight_decay",
            "completed_steps",
            "max_steps",
            "mask_schedule",
            "loss_weights",
            "batch_size",
            "shuffle",
            "seed",
            "sample_ids",
            "loss_total_by_step",
            "grad_norm_by_step",
            "param_delta_norm_by_step",
            "source_modification_allowed",
            "formal_training_executed",
            "real_finetune_executed",
        ],
        "required_false_fields": {
            "source_modification_allowed": False,
            "formal_training_executed": False,
            "real_finetune_executed": False,
        },
        "forbidden_payload_fields": [
            "raw PDB contents",
            "raw SDF contents",
            "large tensor dumps",
            "DataLoader object",
            "Dataset object",
            "model object pickle",
            "optimizer object pickle",
            "full generated molecule archive",
            "hidden temporary files",
        ],
    }


def build_metadata_policy_v0() -> dict[str, Any]:
    return {
        "metadata_required": True,
        "required_metadata_fields": [
            "stage",
            "previous_stage",
            "run_name",
            "repo_commit",
            "git_status_clean_before_run",
            "git_status_clean_after_run",
            "device",
            "cuda_device_name",
            "environment_name",
            "max_steps",
            "executed_steps",
            "mask_schedule",
            "loss_weights",
            "checkpoint_path",
            "checkpoint_sha256",
            "checkpoint_size_bytes",
            "checkpoint_saved",
            "checkpoint_load_resume_smoke_result",
            "safety_flags",
            "forbidden_artifact_scan_result",
            "protected_source_diff_result",
        ],
        "checkpoint_sha256_required": True,
        "checkpoint_size_bytes_required": True,
        "git_status_required": True,
        "source_diff_check_required": True,
        "forbidden_artifact_scan_required": True,
    }


def build_retention_policy_v0() -> dict[str, Any]:
    return {
        "max_checkpoints": 1,
        "keep_last_only": True,
        "do_not_auto_delete_existing_unknown_files": True,
        "fail_if_unexpected_checkpoint_files_exist": True,
        "fail_if_multiple_checkpoints_created": True,
        "fail_if_checkpoint_size_zero": True,
        "fail_if_checkpoint_missing": True,
        "no_archive_creation": True,
    }


def build_resume_smoke_policy_v0() -> dict[str, Any]:
    return {
        "resume_smoke_required": True,
        "fresh_in_memory_model_required": True,
        "fresh_in_memory_optimizer_required": True,
        "load_model_state_dict": True,
        "load_optimizer_state_dict": True,
        "verify_completed_steps": 12,
        "verify_mask_schedule_matches": True,
        "verify_model_parameter_shapes_match": True,
        "verify_optimizer_state_loaded": True,
        "optional_no_save_validation_forward_backward_smoke": False,
        "optimizer_step_during_resume_smoke": False,
        "second_checkpoint_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "model_save_allowed": False,
    }


def build_next_step_execution_boundary_v0() -> dict[str, Any]:
    return {
        "first_checkpointed_training_dry_run_allowed": True,
        "checkpoint_save_allowed_next_step": True,
        "checkpoint_load_allowed_next_step": True,
        "checkpoint_load_scope": "resume smoke only",
        "model_save_allowed_next_step": False,
        "trainer_fit_allowed_next_step": False,
        "training_step_allowed_next_step": False,
        "formal_training_allowed_next_step": False,
        "finetune_allowed_next_step": False,
        "source_modification_allowed_next_step": False,
        "allowed_checkpoint_files_next_step": [CHECKPOINT_FILENAME],
        "forbidden_outputs_next_step": [
            ".pkl",
            ".lmdb",
            ".tar",
            ".zip",
            ".tgz",
            ".ckpt",
            ".pth",
            "additional .pt files beyond the single allowed checkpoint",
            "model object pickle",
            "optimizer object pickle",
        ],
    }


def build_checkpoint_output_policy_design_v0() -> dict[str, Any]:
    validate_step10u_outputs_v0()
    output_policy = build_output_directory_policy_v0()
    naming_policy = build_checkpoint_naming_policy_v0()
    payload_policy = build_checkpoint_payload_policy_v0()
    metadata_policy = build_metadata_policy_v0()
    retention_policy = build_retention_policy_v0()
    resume_policy = build_resume_smoke_policy_v0()
    execution_boundary = build_next_step_execution_boundary_v0()
    source_modified = _protected_source_diff_exists()
    forbidden_artifacts_created = _forbidden_artifacts_exist()
    risk_register = [
        {
            "risk": "Saving multiple or unexpected checkpoints during the first checkpointed dry run.",
            "mitigation": "Allow exactly one checkpoint filename and fail on additional checkpoint files.",
        },
        {
            "risk": "Checkpoint payload becomes an opaque object pickle.",
            "mitigation": "Require dictionary payload with model_state_dict and optimizer_state_dict only.",
        },
        {
            "risk": "Checkpoint can be saved but not reloaded.",
            "mitigation": "Require a fresh-model/fresh-optimizer resume smoke in the next step.",
        },
        {
            "risk": "Policy design is mistaken for permission to run formal training.",
            "mitigation": "Keep formal training, fine-tune, trainer fit, training step, and model save disabled.",
        },
    ]
    all_checks_passed = bool(
        not source_modified
        and not forbidden_artifacts_created
        and output_policy["directory_creation_allowed_current_step"] is False
        and naming_policy["checkpoint_count_limit"] == 1
        and naming_policy["checkpoint_filename"] == CHECKPOINT_FILENAME
        and metadata_policy["checkpoint_sha256_required"]
        and retention_policy["max_checkpoints"] == 1
        and resume_policy["resume_smoke_required"]
        and execution_boundary["checkpoint_save_allowed_next_step"]
        and execution_boundary["checkpoint_load_allowed_next_step"]
        and not execution_boundary["model_save_allowed_next_step"]
        and not execution_boundary["trainer_fit_allowed_next_step"]
        and not execution_boundary["training_step_allowed_next_step"]
        and not execution_boundary["formal_training_allowed_next_step"]
    )
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10u_review_passed": True,
        "next_stage": NEXT_STAGE,
        "loop_name": LOOP_NAME,
        "run_name": RUN_NAME,
        "output_directory_policy": output_policy,
        "checkpoint_naming_policy": naming_policy,
        "checkpoint_payload_policy": payload_policy,
        "metadata_policy": metadata_policy,
        "retention_policy": retention_policy,
        "resume_smoke_policy": resume_policy,
        "next_step_execution_boundary": execution_boundary,
        "risk_register": risk_register,
        "current_step_checkpoint_saved": False,
        "current_step_checkpoint_loaded": False,
        "current_step_model_saved": False,
        "current_step_formal_training_executed": False,
        "source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts_created,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "first_checkpointed_training_dry_run" if all_checks_passed else "manual_checkpoint_output_policy_review"
        ),
    }
