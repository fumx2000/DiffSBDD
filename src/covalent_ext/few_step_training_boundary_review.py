from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "few_step_training_dry_run_review_and_training_boundary_v0"
PREVIOUS_STAGE = "few_step_training_dry_run_no_checkpoint_v0"
STEP10Q_STAGE = "few_step_training_dry_run_no_checkpoint_v0"
STEP10P_STAGE = "training_loop_design_without_checkpoint_v0"
LOOP_NAME = "masked_covalent_training_loop_v0"
MASK_ORDER = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
NEXT_MASK_SCHEDULE = MASK_ORDER * 3
NEXT_MASK_SCHEDULE_TEXT = "A_warhead_only / B_linker_warhead / B2_scaffold_warhead / C_scaffold_linker_warhead repeated 3 cycles"
PROPOSED_NEXT_MAX_STEPS = 12
PROPOSED_NEXT_BATCH_SIZE = 3
PROPOSED_NEXT_LR = 1e-6
PROPOSED_NEXT_SHUFFLE = False
PROTECTED_SOURCE_PATHS = [
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/conditional_model.py",
    "equivariant_diffusion/dynamics.py",
    "lightning_modules.py",
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
SAFETY_FALSE_FIELDS = [
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "trainer_fit_called",
    "checkpoint_written",
    "archive_created",
    "model_saved",
    "formal_training_executed",
    "real_finetune_executed",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _forbidden_artifacts_exist(root: str | Path = DEFAULT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def _protected_source_diff_exists() -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0


def validate_step10q_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "few_step_training_dry_run_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "few_step_training_dry_run_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10Q few-step training dry-run outputs are missing")

    rows = _rows_from_csv(report_path)
    if len(rows) != 4:
        raise ValueError(f"Step 10Q report must contain exactly four rows, found {len(rows)}")
    blockers: list[str] = []
    for index, row in enumerate(rows, start=1):
        mask_level = MASK_ORDER[index - 1]
        expected = {
            "stage": STEP10Q_STAGE,
            "previous_stage": STEP10P_STAGE,
            "step10p_training_loop_design_passed": "true",
            "loop_name": LOOP_NAME,
            "step": str(index),
            "mask_level": mask_level,
            "step_status": "passed",
            "loss_finite": "true",
            "loss_total_requires_grad": "true",
            "backward_success": "true",
            "optimizer_step_success": "true",
            "finite_gradients": "true",
            "nonzero_gradients": "true",
            "finite_parameter_delta": "true",
            "nonzero_parameter_delta": "true",
            "stop_triggered": "false",
            "stop_reason": "",
            "blocking_reasons": "",
        }
        for key, expected_value in expected.items():
            _expect(row.get(key) == expected_value, f"report_row_{index}_{key}_invalid:{row.get(key)!r}", blockers)
        for field_name in SAFETY_FALSE_FIELDS:
            _expect(row.get(field_name) == "false", f"report_row_{index}_{field_name}_not_false:{row.get(field_name)!r}", blockers)
        for numeric_key in ["loss_original", "loss_masked_x", "loss_masked_h", "loss_total"]:
            try:
                float(row.get(numeric_key, "nan"))
            except ValueError:
                blockers.append(f"report_row_{index}_{numeric_key}_not_float")
        for positive_key in ["grad_norm", "max_grad_abs", "param_delta_norm", "max_param_delta_abs"]:
            try:
                _expect(float(row.get(positive_key, "0")) > 0, f"report_row_{index}_{positive_key}_not_positive", blockers)
            except ValueError:
                blockers.append(f"report_row_{index}_{positive_key}_not_float")
        for zero_key in ["grad_nan_count", "grad_inf_count", "post_step_param_nan_count", "post_step_param_inf_count"]:
            _expect(row.get(zero_key) == "0", f"report_row_{index}_{zero_key}_not_zero:{row.get(zero_key)!r}", blockers)

    manifest = _load_json(manifest_path)
    expected_manifest_values = {
        "stage": STEP10Q_STAGE,
        "previous_stage": STEP10P_STAGE,
        "step10p_training_loop_design_passed": True,
        "loop_name": LOOP_NAME,
        "max_steps": 4,
        "executed_steps": 4,
        "dry_run_training_steps_executed": 4,
        "mask_order": MASK_ORDER,
        "mask_levels_seen": MASK_ORDER,
        "expected_mask_order_followed": True,
        "all_steps_passed": True,
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
        "stop_reason": "",
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_written": False,
        "archive_created": False,
        "model_saved": False,
        "formal_training_executed": False,
        "real_finetune_executed": False,
        "source_modification_allowed": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "few_step_training_dry_run_review_and_training_boundary",
    }
    for key, expected in expected_manifest_values.items():
        _expect(manifest.get(key) == expected, f"manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def summarize_step10q_evidence_v0(
    report_csv: str | Path = DEFAULT_ROOT / "few_step_training_dry_run_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "few_step_training_dry_run_preview_manifest.json",
) -> dict[str, Any]:
    validate_step10q_outputs_v0(report_csv, manifest_json)
    rows = _rows_from_csv(report_csv)
    manifest = _load_json(manifest_json)
    evidence = {
        "step10q_dry_run_passed": True,
        "executed_steps": int(manifest["executed_steps"]),
        "dry_run_training_steps_executed": int(manifest["dry_run_training_steps_executed"]),
        "mask_order": list(manifest["mask_order"]),
        "mask_levels_seen": list(manifest["mask_levels_seen"]),
        "loss_total_by_step": {row["step"]: float(row["loss_total"]) for row in rows},
        "loss_original_by_step": {row["step"]: float(row["loss_original"]) for row in rows},
        "loss_masked_x_by_step": {row["step"]: float(row["loss_masked_x"]) for row in rows},
        "loss_masked_h_by_step": {row["step"]: float(row["loss_masked_h"]) for row in rows},
        "grad_norm_by_step": {row["step"]: float(row["grad_norm"]) for row in rows},
        "max_grad_abs_by_step": {row["step"]: float(row["max_grad_abs"]) for row in rows},
        "param_delta_norm_by_step": {row["step"]: float(row["param_delta_norm"]) for row in rows},
        "max_param_delta_abs_by_step": {row["step"]: float(row["max_param_delta_abs"]) for row in rows},
        "step_status_by_step": {row["step"]: row["step_status"] for row in rows},
        "mask_level_by_step": {row["step"]: row["mask_level"] for row in rows},
        "target_atom_count_by_step": {row["step"]: int(row["target_atom_count"]) for row in rows},
        "context_atom_count_by_step": {row["step"]: int(row["context_atom_count"]) for row in rows},
        "all_safety_flags_false": all(manifest[field_name] is False for field_name in SAFETY_FALSE_FIELDS),
        "safety_flags": {field_name: manifest[field_name] for field_name in SAFETY_FALSE_FIELDS},
        "all_losses_finite": manifest["all_losses_finite"],
        "all_loss_total_requires_grad": manifest["all_loss_total_requires_grad"],
        "all_backward_success": manifest["all_backward_success"],
        "all_optimizer_steps_success": manifest["all_optimizer_steps_success"],
        "all_gradients_finite": manifest["all_gradients_finite"],
        "all_gradients_nonzero": manifest["all_gradients_nonzero"],
        "all_parameter_updates_finite": manifest["all_parameter_updates_finite"],
        "all_parameter_updates_nonzero": manifest["all_parameter_updates_nonzero"],
        "all_post_step_params_finite": manifest["all_post_step_params_finite"],
        "stop_triggered": manifest["stop_triggered"],
        "stop_reason": manifest["stop_reason"],
        "forbidden_artifacts_created": manifest["forbidden_artifacts_created"] or _forbidden_artifacts_exist(),
        "source_modification_allowed": manifest["source_modification_allowed"],
        "original_source_files_modified": manifest["original_source_files_modified"] or _protected_source_diff_exists(),
        "recommended_next_step_from_step10q": manifest["recommended_next_step"],
    }
    return evidence


def assess_dry_run_stability_v0(evidence: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    required_true = [
        "all_losses_finite",
        "all_backward_success",
        "all_optimizer_steps_success",
        "all_gradients_finite",
        "all_parameter_updates_finite",
        "all_post_step_params_finite",
    ]
    for key in required_true:
        if evidence.get(key) is not True:
            blockers.append(f"{key}_not_true")
    if evidence.get("stop_triggered") is not False:
        blockers.append("stop_triggered")
    if evidence.get("forbidden_artifacts_created") is not False:
        blockers.append("forbidden_artifacts_created")
    if evidence.get("original_source_files_modified") is not False:
        blockers.append("original_source_files_modified")
    return {
        "stability_status": "passed" if not blockers else "blocked",
        "loss_decrease_required": False,
        "reason": "4-step dry run checks wiring and stability, not model quality",
        "blocking_reasons": blockers,
    }


def build_training_boundary_decision_v0(evidence: dict[str, Any], stability: dict[str, Any]) -> dict[str, Any]:
    passed = stability["stability_status"] == "passed"
    return {
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "longer_no_checkpoint_dry_run_allowed": passed,
        "recommended_next_stage": (
            "longer_no_checkpoint_training_dry_run_design"
            if passed
            else "manual_few_step_training_dry_run_review"
        ),
        "next_run_type": "longer_no_checkpoint_dry_run",
        "proposed_max_steps": PROPOSED_NEXT_MAX_STEPS,
        "proposed_mask_schedule": list(NEXT_MASK_SCHEDULE),
        "proposed_mask_schedule_text": NEXT_MASK_SCHEDULE_TEXT,
        "proposed_batch_size": PROPOSED_NEXT_BATCH_SIZE,
        "proposed_shuffle": PROPOSED_NEXT_SHUFFLE,
        "proposed_lr": PROPOSED_NEXT_LR,
        "checkpoint_remains_forbidden": True,
        "model_saving_remains_forbidden": True,
        "decision_rationale": (
            "Step 10Q passed a bounded four-step wiring dry run, so the next safe move is designing a longer no-checkpoint dry run, not formal training."
        ),
        "blocking_reasons": list(stability["blocking_reasons"]),
    }


def build_next_run_stop_policy_v0() -> dict[str, Any]:
    return {
        "hard_max_steps": PROPOSED_NEXT_MAX_STEPS,
        "hard_stop_conditions": [
            "abort on non-finite loss",
            "abort on non-finite gradients",
            "abort on grad_nan_count > 0",
            "abort on grad_inf_count > 0",
            "abort on non-finite post-step params",
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
        "warning_policy": "warnings do not necessarily fail unless configured as hard stop; record them",
    }


def build_checkpoint_boundary_v0() -> dict[str, Any]:
    return {
        "current_review_checkpoint_allowed": False,
        "next_12_step_dry_run_checkpoint_allowed": False,
        "next_checkpoint_allowed": False,
        "first_checkpoint_discussion_requires": [
            "12-step no-checkpoint dry run passed",
            "output directory policy reviewed",
            "checkpoint naming policy reviewed",
            "retention policy reviewed",
            "explicit user approval",
        ],
        "checkpoint_save_patterns_forbidden": [
            "torch" + "." + "save",
            ".pt",
            ".pth",
            ".ckpt",
            "trainer" + "." + "save" + "_checkpoint",
            "ModelCheckpoint",
        ],
    }


def build_few_step_training_boundary_review_v0() -> dict[str, Any]:
    evidence = summarize_step10q_evidence_v0()
    stability = assess_dry_run_stability_v0(evidence)
    decision = build_training_boundary_decision_v0(evidence, stability)
    stop_policy = build_next_run_stop_policy_v0()
    checkpoint_boundary = build_checkpoint_boundary_v0()
    risk_register = [
        {
            "risk": "Treating four dry-run optimizer steps as evidence of model quality.",
            "mitigation": "Keep formal training disabled; the dry run only verifies loop wiring and numerical stability.",
        },
        {
            "risk": "Introducing checkpoint or model artifacts before output policy review.",
            "mitigation": "Keep checkpoint/model saving forbidden for the next 12-step dry run.",
        },
        {
            "risk": "Longer dry run hides unstable mask-level behavior.",
            "mitigation": "Cycle A/B/B2/C three times and abort on non-finite loss, gradients, parameters, unexpected masks, or artifacts.",
        },
        {
            "risk": "Accidental source modification during dry-run iteration.",
            "mitigation": "Require protected source diff checks and abort on source modification.",
        },
    ]
    all_checks_passed = bool(
        evidence["step10q_dry_run_passed"]
        and stability["stability_status"] == "passed"
        and decision["longer_no_checkpoint_dry_run_allowed"]
        and not decision["formal_training_allowed"]
        and not decision["checkpoint_allowed"]
        and not checkpoint_boundary["next_checkpoint_allowed"]
    )
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10q_dry_run_passed": evidence["step10q_dry_run_passed"],
        "evidence_summary": evidence,
        "stability_assessment": stability,
        "training_boundary_decision": decision,
        "next_run_stop_policy": stop_policy,
        "checkpoint_boundary": checkpoint_boundary,
        "risk_register": risk_register,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "longer_no_checkpoint_training_dry_run_design"
            if all_checks_passed
            else "manual_few_step_training_dry_run_review"
        ),
    }
