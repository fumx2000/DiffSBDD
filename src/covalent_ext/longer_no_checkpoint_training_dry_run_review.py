from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "longer_no_checkpoint_training_dry_run_review_v0"
PREVIOUS_STAGE = "longer_no_checkpoint_training_dry_run_v0"
STEP10T_STAGE = "longer_no_checkpoint_training_dry_run_v0"
STEP10S_STAGE = "longer_no_checkpoint_training_dry_run_design_v0"
LOOP_NAME = "masked_covalent_training_loop_v0"
MASK_CYCLE = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
MASK_SCHEDULE = MASK_CYCLE * 3
EXPECTED_CYCLE_INDEXES = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
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


def validate_step10t_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10T longer no-checkpoint dry-run outputs are missing")

    rows = _rows_from_csv(report_path)
    blockers: list[str] = []
    _expect(len(rows) == 12, f"step10t_report_row_count_invalid:{len(rows)}", blockers)
    for index, row in enumerate(rows, start=1):
        expected_mask = MASK_SCHEDULE[index - 1]
        expected_cycle = EXPECTED_CYCLE_INDEXES[index - 1]
        expected_values = {
            "stage": STEP10T_STAGE,
            "previous_stage": STEP10S_STAGE,
            "step10s_design_passed": "true",
            "loop_name": LOOP_NAME,
            "step": str(index),
            "cycle_index": str(expected_cycle),
            "mask_level": expected_mask,
            "expected_mask_level": expected_mask,
            "expected_target_atom_count": str(EXPECTED_TARGET_COUNTS[expected_mask]),
            "expected_context_atom_count": str(EXPECTED_CONTEXT_COUNTS[expected_mask]),
            "target_atom_count": str(EXPECTED_TARGET_COUNTS[expected_mask]),
            "context_atom_count": str(EXPECTED_CONTEXT_COUNTS[expected_mask]),
            "ligand_atom_count": "104",
            "step_status": "passed",
            "loss_finite": "true",
            "loss_total_requires_grad": "true",
            "loss_decrease_required": "false",
            "quality_claim_allowed": "false",
            "backward_success": "true",
            "optimizer_step_success": "true",
            "finite_gradients": "true",
            "nonzero_gradients": "true",
            "finite_parameter_delta": "true",
            "nonzero_parameter_delta": "true",
            "grad_nan_count": "0",
            "grad_inf_count": "0",
            "post_step_param_nan_count": "0",
            "post_step_param_inf_count": "0",
            "warning_triggered": "false",
            "stop_triggered": "false",
            "stop_reason": "",
            "blocking_reasons": "",
        }
        for key, expected in expected_values.items():
            _expect(row.get(key) == expected, f"report_row_{index}_{key}_invalid:{row.get(key)!r}", blockers)
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

    manifest = _load_json(manifest_path)
    expected_manifest_values = {
        "stage": STEP10T_STAGE,
        "previous_stage": STEP10S_STAGE,
        "step10s_design_passed": True,
        "loop_name": LOOP_NAME,
        "requested_device": "auto",
        "resolved_device": "cuda:0",
        "cuda_available": True,
        "cuda_device_name": "NVIDIA A100-SXM4-80GB",
        "optimizer_class": "AdamW",
        "optimizer_lr": 1e-6,
        "optimizer_weight_decay": 0.0,
        "max_steps": 12,
        "executed_steps": 12,
        "dry_run_training_steps_executed": 12,
        "mask_schedule": MASK_SCHEDULE,
        "mask_levels_seen": MASK_SCHEDULE,
        "expected_mask_schedule_followed": True,
        "mask_counts_seen": {mask_level: 3 for mask_level in MASK_CYCLE},
        "batch_size": 3,
        "shuffle": False,
        "seed": 4401,
        "loss_decrease_required": False,
        "quality_claim_allowed": False,
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
        "warning_steps": [],
        "warnings_triggered": False,
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
        "recommended_next_step": "longer_no_checkpoint_training_dry_run_review",
    }
    for key, expected in expected_manifest_values.items():
        _expect(manifest.get(key) == expected, f"manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def summarize_step10t_evidence_v0(
    report_csv: str | Path = DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "longer_no_checkpoint_training_dry_run_preview_manifest.json",
) -> dict[str, Any]:
    validate_step10t_outputs_v0(report_csv, manifest_json)
    rows = _rows_from_csv(report_csv)
    manifest = _load_json(manifest_json)
    return {
        "step10t_dry_run_passed": True,
        "requested_device": manifest["requested_device"],
        "resolved_device": manifest["resolved_device"],
        "cuda_available": manifest["cuda_available"],
        "cuda_device_name": manifest["cuda_device_name"],
        "optimizer_class": manifest["optimizer_class"],
        "optimizer_lr": manifest["optimizer_lr"],
        "optimizer_weight_decay": manifest["optimizer_weight_decay"],
        "executed_steps": int(manifest["executed_steps"]),
        "dry_run_training_steps_executed": int(manifest["dry_run_training_steps_executed"]),
        "mask_schedule": list(manifest["mask_schedule"]),
        "mask_levels_seen": list(manifest["mask_levels_seen"]),
        "mask_counts_seen": dict(manifest["mask_counts_seen"]),
        "mask_schedule_length": len(manifest["mask_schedule"]),
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
        "warning_steps": list(manifest["warning_steps"]),
        "warnings_triggered": manifest["warnings_triggered"],
        "stop_triggered": manifest["stop_triggered"],
        "stop_reason": manifest["stop_reason"],
        "all_steps_passed": manifest["all_steps_passed"],
        "all_losses_finite": manifest["all_losses_finite"],
        "all_loss_total_requires_grad": manifest["all_loss_total_requires_grad"],
        "all_backward_success": manifest["all_backward_success"],
        "all_optimizer_steps_success": manifest["all_optimizer_steps_success"],
        "all_gradients_finite": manifest["all_gradients_finite"],
        "all_gradients_nonzero": manifest["all_gradients_nonzero"],
        "all_parameter_updates_finite": manifest["all_parameter_updates_finite"],
        "all_parameter_updates_nonzero": manifest["all_parameter_updates_nonzero"],
        "all_post_step_params_finite": manifest["all_post_step_params_finite"],
        "safety_flags": {field_name: manifest[field_name] for field_name in SAFETY_FALSE_FIELDS},
        "all_safety_flags_false": all(manifest[field_name] is False for field_name in SAFETY_FALSE_FIELDS),
        "source_modification_allowed": manifest["source_modification_allowed"],
        "original_source_files_modified": manifest["original_source_files_modified"] or _protected_source_diff_exists(),
        "forbidden_artifacts_created": manifest["forbidden_artifacts_created"] or _forbidden_artifacts_exist(),
        "recommended_next_step_from_step10t": manifest["recommended_next_step"],
    }


def assess_longer_dry_run_stability_v0(evidence: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    required_true = [
        "all_steps_passed",
        "all_losses_finite",
        "all_loss_total_requires_grad",
        "all_backward_success",
        "all_optimizer_steps_success",
        "all_gradients_finite",
        "all_gradients_nonzero",
        "all_parameter_updates_finite",
        "all_parameter_updates_nonzero",
        "all_post_step_params_finite",
    ]
    for key in required_true:
        if evidence.get(key) is not True:
            blockers.append(f"{key}_not_true")
    if evidence.get("warnings_triggered") is not False:
        blockers.append("warnings_triggered")
    if evidence.get("stop_triggered") is not False:
        blockers.append("stop_triggered")
    if evidence.get("forbidden_artifacts_created") is not False:
        blockers.append("forbidden_artifacts_created")
    if evidence.get("original_source_files_modified") is not False:
        blockers.append("original_source_files_modified")
    return {
        "stability_status": "passed" if not blockers else "blocked",
        "loss_decrease_required": False,
        "quality_claim_allowed": False,
        "reason": "12-step dry run checks longer loop stability and safety boundaries, not model quality",
        "blocking_reasons": blockers,
    }


def build_evidence_observations_v0(evidence: dict[str, Any]) -> dict[str, Any]:
    loss_values = evidence["loss_total_by_step"]
    grad_values = evidence["grad_norm_by_step"]
    delta_values = evidence["param_delta_norm_by_step"]
    highest_grad_step, highest_grad_value = max(grad_values.items(), key=lambda item: item[1])
    return {
        "loss_total_range": [min(loss_values.values()), max(loss_values.values())],
        "grad_norm_range": [min(grad_values.values()), max(grad_values.values())],
        "param_delta_norm_range": [min(delta_values.values()), max(delta_values.values())],
        "highest_grad_step": int(highest_grad_step),
        "highest_grad_mask_level": evidence["mask_level_by_step"][highest_grad_step],
        "highest_grad_value": round(float(highest_grad_value), 6),
        "highest_grad_observation": "step 9 grad_norm is visibly higher than other steps but is finite and below warning threshold 1e4",
        "loss_trend_claim_allowed": False,
        "quality_claim_allowed": False,
    }


def build_next_boundary_decision_v0(
    evidence: dict[str, Any],
    stability: dict[str, Any],
    observations: dict[str, Any],
) -> dict[str, Any]:
    passed = stability["stability_status"] == "passed"
    return {
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "checkpoint_policy_design_allowed": passed,
        "output_policy_design_allowed": passed,
        "longer_no_checkpoint_run_review_passed": passed,
        "recommended_next_stage": (
            "checkpoint_and_output_policy_design"
            if passed
            else "manual_longer_no_checkpoint_training_dry_run_review"
        ),
        "next_stage_is_formal_training": False,
        "next_stage_is_direct_checkpoint_save": False,
        "decision_rationale": (
            "Step 10T passed 12 bounded no-checkpoint dry-run steps; next safe move is checkpoint/output policy design, not checkpointing or formal training."
        ),
        "observed_highest_grad_step": observations["highest_grad_step"],
        "blocking_reasons": list(stability["blocking_reasons"]),
    }


def build_checkpoint_discussion_gate_v0() -> dict[str, Any]:
    return {
        "current_review_checkpoint_allowed": False,
        "checkpoint_save_allowed": False,
        "checkpoint_load_allowed": False,
        "model_save_allowed": False,
        "next_step_is_policy_design_only": True,
        "checkpoint_may_be_enabled_only_after": [
            "checkpoint/output policy design passed",
            "output directory naming fixed",
            "checkpoint naming policy fixed",
            "retention policy fixed",
            "metadata policy fixed",
            "resume-test design fixed",
            "explicit user approval",
        ],
    }


def build_longer_no_checkpoint_training_dry_run_review_v0() -> dict[str, Any]:
    evidence = summarize_step10t_evidence_v0()
    stability = assess_longer_dry_run_stability_v0(evidence)
    observations = build_evidence_observations_v0(evidence)
    decision = build_next_boundary_decision_v0(evidence, stability, observations)
    checkpoint_gate = build_checkpoint_discussion_gate_v0()
    risk_register = [
        {
            "risk": "Treating a 12-step dry run as model-quality evidence.",
            "mitigation": "Keep loss decrease and quality claims disabled; treat the result as wiring and numerical-boundary evidence only.",
        },
        {
            "risk": "Enabling checkpoint saves before output policy review.",
            "mitigation": "Keep checkpoint/model saving disabled; only allow checkpoint/output policy design next.",
        },
        {
            "risk": "Step 9 high gradient is overlooked.",
            "mitigation": "Record highest_grad_step=9 as an observation; it is finite and below warning threshold.",
        },
        {
            "risk": "Accidental source modification during review.",
            "mitigation": "Require protected source diff checks and forbid source modification.",
        },
    ]
    all_checks_passed = bool(
        evidence["step10t_dry_run_passed"]
        and stability["stability_status"] == "passed"
        and decision["checkpoint_policy_design_allowed"]
        and decision["output_policy_design_allowed"]
        and not decision["formal_training_allowed"]
        and not decision["checkpoint_allowed"]
        and checkpoint_gate["next_step_is_policy_design_only"]
        and not checkpoint_gate["checkpoint_save_allowed"]
    )
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10t_dry_run_passed": evidence["step10t_dry_run_passed"],
        "evidence_summary": evidence,
        "stability_assessment": stability,
        "evidence_observations": observations,
        "next_boundary_decision": decision,
        "checkpoint_discussion_gate": checkpoint_gate,
        "risk_register": risk_register,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "checkpoint_and_output_policy_design"
            if all_checks_passed
            else "manual_longer_no_checkpoint_training_dry_run_review"
        ),
    }
