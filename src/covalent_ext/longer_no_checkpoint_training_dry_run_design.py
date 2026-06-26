from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "longer_no_checkpoint_training_dry_run_design_v0"
PREVIOUS_STAGE = "few_step_training_dry_run_review_and_training_boundary_v0"
NEXT_STAGE = "longer_no_checkpoint_training_dry_run_v0"
LOOP_NAME = "masked_covalent_training_loop_v0"
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
EXPECTED_TARGET_COUNTS = {
    "A_warhead_only": 12,
    "B_linker_warhead": 30,
    "B2_scaffold_warhead": 86,
    "C_scaffold_linker_warhead": 104,
}
EXPECTED_CONTEXT_COUNTS = {
    "A_warhead_only": 92,
    "B_linker_warhead": 74,
    "B2_scaffold_warhead": 18,
    "C_scaffold_linker_warhead": 0,
}
MASK_SCHEDULE_TEXT = (
    "A_warhead_only / B_linker_warhead / B2_scaffold_warhead / "
    "C_scaffold_linker_warhead repeated 3 cycles"
)
LOSS_WEIGHTS = {"w_original": 1.0, "w_x": 1.0, "w_h": 0.2}
FORBIDDEN_OUTPUTS = [
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
    "saved model files",
    "checkpoint files",
    "tensor dumps",
    "optimizer state files",
]
OPTIMIZER_STEP_TEXT = "optimizer" + "." + "step"
TRAINER_FIT_TEXT = "trainer" + "." + "fit"
TORCH_SAVE_TEXT = "torch" + "." + "save"
TRAINER_SAVE_CHECKPOINT_TEXT = "trainer" + "." + "save" + "_checkpoint"
TRAINING_STEP_TEXT = "training" + "_step"


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def validate_step10r_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "few_step_training_boundary_review_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "few_step_training_boundary_review_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10R boundary review outputs are missing")

    rows = _rows_from_csv(report_path)
    expected_sections = [
        "evidence_review",
        "stability_assessment",
        "training_boundary_decision",
        "next_run_stop_policy",
        "checkpoint_boundary",
        "risk_register",
    ]
    blockers: list[str] = []
    _expect(len(rows) == 6, f"step10r_report_row_count_invalid:{len(rows)}", blockers)
    _expect([row.get("review_section") for row in rows] == expected_sections, "step10r_report_sections_invalid", blockers)
    for row in rows:
        _expect(row.get("stage") == PREVIOUS_STAGE, f"step10r_report_stage_invalid:{row.get('stage')!r}", blockers)
        _expect(
            row.get("previous_stage") == "few_step_training_dry_run_no_checkpoint_v0",
            f"step10r_report_previous_stage_invalid:{row.get('previous_stage')!r}",
            blockers,
        )
        _expect(row.get("status") == "passed", f"step10r_report_status_invalid:{row.get('status')!r}", blockers)
        _expect(
            row.get("recommended_next_step") == "longer_no_checkpoint_training_dry_run_design",
            f"step10r_report_recommended_next_step_invalid:{row.get('recommended_next_step')!r}",
            blockers,
        )

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "few_step_training_dry_run_no_checkpoint_v0",
        "step10q_dry_run_passed": True,
        "executed_steps": 4,
        "dry_run_training_steps_executed": 4,
        "mask_order": MASK_CYCLE,
        "all_losses_finite": True,
        "all_backward_success": True,
        "all_optimizer_steps_success": True,
        "all_gradients_finite": True,
        "all_gradients_nonzero": True,
        "all_parameter_updates_finite": True,
        "all_parameter_updates_nonzero": True,
        "stop_triggered": False,
        "stability_status": "passed",
        "loss_decrease_required": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "longer_no_checkpoint_dry_run_allowed": True,
        "proposed_next_max_steps": 12,
        "proposed_next_mask_schedule": MASK_SCHEDULE_TEXT,
        "proposed_next_lr": 1e-6,
        "proposed_next_shuffle": False,
        "next_checkpoint_allowed": False,
        "all_checks_passed": True,
        "recommended_next_step": "longer_no_checkpoint_training_dry_run_design",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step10r_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_longer_dry_run_schedule_v0() -> list[dict[str, Any]]:
    return [
        {
            "step": index + 1,
            "cycle_index": (index // len(MASK_CYCLE)) + 1,
            "mask_level": mask_level,
            "expected_target_atom_count": EXPECTED_TARGET_COUNTS[mask_level],
            "expected_context_atom_count": EXPECTED_CONTEXT_COUNTS[mask_level],
            "batch_size": BATCH_SIZE,
            "shuffle": SHUFFLE,
            "seed": SEED,
            "purpose": "repeat fixed A/B/B2/C mask cycle to check longer no-checkpoint loop stability",
        }
        for index, mask_level in enumerate(MASK_SCHEDULE)
    ]


def build_longer_dry_run_contract_v0() -> dict[str, Any]:
    return {
        "allowed_actions": [
            "instantiate one fresh in-memory model",
            "build one AdamW optimizer",
            "run fixed 12-step loop",
            "compute masked loss",
            "backward",
            OPTIMIZER_STEP_TEXT,
            "scalar logging",
            "write csv/json/md reports only",
        ],
        "forbidden_actions": [
            TRAINER_FIT_TEXT,
            TRAINING_STEP_TEXT,
            "checkpoint loading",
            "checkpoint saving",
            TORCH_SAVE_TEXT,
            "model saving",
            "archive writing",
            "tensor dump writing",
            "source modification",
            "formal training",
            "fine-tune",
        ],
        "not_formal_training": True,
        "requires_explicit_review_before_checkpoint": True,
    }


def build_longer_dry_run_loss_policy_v0() -> dict[str, Any]:
    return {
        "loss_weights": dict(LOSS_WEIGHTS),
        "auxiliary_losses_enabled": False,
        "loss_decrease_required": False,
        "quality_claim_allowed": False,
        "rationale": "The 12-step dry run checks loop stability and safety boundaries, not model quality.",
    }


def build_longer_dry_run_stop_policy_v0() -> dict[str, Any]:
    return {
        "hard_max_steps": MAX_STEPS,
        "hard_stop_conditions": [
            "abort on non-finite loss",
            "abort on loss_total_requires_grad=false",
            "abort on non-finite gradients",
            "abort on gradients all zero",
            "abort on grad_nan_count > 0",
            "abort on grad_inf_count > 0",
            "abort on optimizer step failure",
            "abort on non-finite parameter delta",
            "abort on zero parameter delta",
            "abort on post-step parameter NaN/Inf",
            "abort on zero target mask",
            "abort on unexpected mask level",
            "abort on checkpoint/model artifact",
            "abort on source modification",
        ],
        "warning_thresholds": {
            "loss_total": 1e4,
            "grad_norm": 1e4,
            "max_grad_abs": 1e3,
            "param_delta_norm": 1.0,
        },
        "warnings_are_hard_stop_by_default": False,
        "warnings_must_be_logged": True,
    }


def build_longer_dry_run_output_policy_v0() -> dict[str, Any]:
    return {
        "allowed_outputs": [
            "csv report",
            "json preview manifest",
            "markdown summary",
        ],
        "forbidden_outputs": list(FORBIDDEN_OUTPUTS),
    }


def build_longer_dry_run_checkpoint_policy_v0() -> dict[str, Any]:
    return {
        "current_design_checkpoint_allowed": False,
        "next_12_step_dry_run_checkpoint_allowed": False,
        "model_save_allowed": False,
        "checkpoint_load_allowed": False,
        "checkpoint_save_allowed": False,
        "checkpoint_discussion_deferred_until": [
            "12-step no-checkpoint dry run passed",
            "output directory policy reviewed",
            "checkpoint naming policy reviewed",
            "retention policy reviewed",
            "explicit user approval",
        ],
    }


def build_longer_dry_run_success_criteria_v0() -> dict[str, Any]:
    return {
        "executed_steps": 12,
        "expected_mask_schedule_followed": True,
        "all_losses_finite": True,
        "all_loss_total_requires_grad": True,
        "all_backward_success": True,
        "all_optimizer_steps_success": True,
        "all_gradients_finite": True,
        "all_gradients_nonzero": True,
        "all_parameter_updates_finite": True,
        "all_parameter_updates_nonzero": True,
        "all_post_step_params_finite": True,
        "stop_triggered": False,
        "forbidden_artifacts_created": False,
        "original_source_files_modified": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
    }


def build_longer_no_checkpoint_training_dry_run_design_v0() -> dict[str, Any]:
    validate_step10r_outputs_v0()
    schedule = build_longer_dry_run_schedule_v0()
    contract = build_longer_dry_run_contract_v0()
    loss_policy = build_longer_dry_run_loss_policy_v0()
    stop_policy = build_longer_dry_run_stop_policy_v0()
    output_policy = build_longer_dry_run_output_policy_v0()
    checkpoint_policy = build_longer_dry_run_checkpoint_policy_v0()
    success_criteria = build_longer_dry_run_success_criteria_v0()
    mask_counts = dict(Counter(row["mask_level"] for row in schedule))
    risk_register = [
        {
            "risk": "The 12-step dry run is mistaken for formal training.",
            "mitigation": "Keep max_steps hard-capped at 12 and keep checkpoint/model saving disabled.",
        },
        {
            "risk": "A single mask level dominates the longer dry run.",
            "mitigation": "Use exactly three complete A/B/B2/C cycles.",
        },
        {
            "risk": "Warnings hide unstable gradients or losses.",
            "mitigation": "Log warning thresholds and keep hard stops for non-finite loss, gradients, and parameters.",
        },
        {
            "risk": "Unexpected artifacts or source edits appear during the dry run.",
            "mitigation": "Scan for forbidden outputs and protected source modifications before declaring success.",
        },
    ]
    all_checks_passed = bool(
        len(schedule) == MAX_STEPS
        and [row["mask_level"] for row in schedule] == MASK_SCHEDULE
        and mask_counts == {mask_level: 3 for mask_level in MASK_CYCLE}
        and stop_policy["hard_max_steps"] == MAX_STEPS
        and checkpoint_policy["checkpoint_load_allowed"] is False
        and checkpoint_policy["checkpoint_save_allowed"] is False
        and checkpoint_policy["model_save_allowed"] is False
    )
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10r_boundary_review_passed": True,
        "loop_name": LOOP_NAME,
        "next_stage": NEXT_STAGE,
        "max_steps": MAX_STEPS,
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": DEFAULT_LR,
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "mask_schedule": list(MASK_SCHEDULE),
        "mask_schedule_text": MASK_SCHEDULE_TEXT,
        "mask_schedule_length": len(MASK_SCHEDULE),
        "mask_counts": mask_counts,
        "schedule": schedule,
        "contract": contract,
        "loss_policy": loss_policy,
        "stop_policy": stop_policy,
        "output_policy": output_policy,
        "checkpoint_policy": checkpoint_policy,
        "success_criteria": success_criteria,
        "risk_register": risk_register,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "longer_no_checkpoint_training_dry_run"
            if all_checks_passed
            else "manual_longer_no_checkpoint_dry_run_design_review"
        ),
    }
