from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import collect_gradient_stats_v0
from covalent_ext.single_optimizer_step_smoke import (
    build_adamw_optimizer_for_smoke_v0,
    build_fresh_strict_loaded_model_for_optimizer_step_smoke_v0,
    build_optimizer_smoke_differentiable_loss_v0,
    capture_parameter_snapshot_summary_v0,
    compute_parameter_delta_summary_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "tiny_training_dry_run_v0"
PREVIOUS_STAGE = "tiny_training_dry_run_design_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CONFIG_PREVIEW_PATH = Path(
    "data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_preview.json"
)
STEP11K_MANIFEST_JSON = Path(
    "data/derived/covalent_small/tiny_training_dry_run_design_v0/tiny_training_dry_run_design_manifest.json"
)
STEP11K_PROTOCOL_JSON = Path(
    "data/derived/covalent_small/tiny_training_dry_run_design_v0/tiny_training_dry_run_protocol.json"
)
STEP11K_SUMMARY_MD = Path("docs/tiny_training_dry_run_design_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/tiny_training_dry_run_v0")
REPORT_CSV = OUTPUT_ROOT / "tiny_training_dry_run_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "tiny_training_dry_run_manifest.json"
STEP_TABLE_CSV = OUTPUT_ROOT / "tiny_training_dry_run_step_table.csv"
SUMMARY_MD = Path("docs/tiny_training_dry_run_v0_summary.md")
SELECTED_MASK_LEVEL = "A_warhead_only"
MAX_STEPS = 3
BATCH_SIZE = 1
OPTIMIZER_CLASS = "AdamW"
OPTIMIZER_LR = 1e-6
OPTIMIZER_WEIGHT_DECAY = 0.0
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _source_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def validate_step11k_outputs_v0() -> bool:
    if not STEP11K_MANIFEST_JSON.is_file() or not STEP11K_PROTOCOL_JSON.is_file() or not STEP11K_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11K outputs are missing")
    manifest = _load_json(STEP11K_MANIFEST_JSON)
    protocol_document = _load_json(STEP11K_PROTOCOL_JSON)
    protocol = protocol_document.get("protocol", {})
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "single_optimizer_step_smoke_v0",
        "step11j_validated": True,
        "optimizer_plumbing_proven": True,
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": OPTIMIZER_LR,
        "optimizer_weight_decay": OPTIMIZER_WEIGHT_DECAY,
        "single_step_delta_positive": True,
        "protocol_written": True,
        "proposed_next_stage": STAGE,
        "tiny_training_dry_run_step_count": MAX_STEPS,
        "selected_mask_levels": [SELECTED_MASK_LEVEL],
        "input_source": "synthetic_10d_shape_contract",
        "reuse_optimizer_across_steps": True,
        "tiny_training_dry_run_allowed": True,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
        "tensor_dump_allowed_next_step": False,
        "design_status": "tiny_training_dry_run_design_ready",
        "this_design_runs_training_loop": False,
        "this_design_runs_backward": False,
        "this_design_creates_optimizer": False,
        "this_design_runs_optimizer_step": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "tiny_training_dry_run",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11k_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    expected_protocol = {
        "proposed_next_stage": STAGE,
        "input_source": "synthetic_10d_shape_contract",
        "selected_mask_levels": [SELECTED_MASK_LEVEL],
        "max_steps": MAX_STEPS,
        "batch_size": BATCH_SIZE,
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": OPTIMIZER_LR,
        "optimizer_weight_decay": OPTIMIZER_WEIGHT_DECAY,
        "reuse_optimizer_across_steps": True,
    }
    for key, expected in expected_protocol.items():
        _expect(protocol.get(key) == expected, f"step11k_protocol_{key}_invalid:{protocol.get(key)!r}", blockers)
    loss_rule = protocol.get("loss_trajectory_rule", {})
    _expect(loss_rule.get("loss_decrease_required") is False, "step11k_protocol_loss_decrease_required_invalid", blockers)
    _expect(loss_rule.get("allow_loss_up_down_or_flat") is True, "step11k_protocol_loss_direction_invalid", blockers)
    _expect(loss_rule.get("nan_or_inf_loss_fails") is True, "step11k_protocol_nan_inf_rule_invalid", blockers)
    pass_conditions = set(protocol.get("pass_conditions", []))
    for condition in [
        "step_count equals 3",
        "each step loss finite",
        "each step loss requires grad",
        "each step backward success",
        "each step optimizer.step success",
        "each step grad_nan_count equals 0",
        "each step grad_inf_count equals 0",
        "each step parameter_delta_l2_total finite positive",
        "no NaN/Inf in parameter deltas",
        "no checkpoint/model/tensor dump saved",
        "final status passed",
    ]:
        _expect(condition in pass_conditions, f"step11k_protocol_missing_pass_condition:{condition}", blockers)
    summary = STEP11K_SUMMARY_MD.read_text(encoding="utf-8")
    _expect("not training" in summary, "step11k_summary_training_boundary_missing", blockers)
    _expect("tiny_training_dry_run" in summary, "step11k_summary_next_step_missing", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def run_one_tiny_training_step_v0(
    model: Any,
    optimizer: Any,
    input_contract: dict[str, Any],
    step_index: int,
    device: str = "cpu",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "stage": STAGE,
        "step_index": step_index,
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "loss_value": math.nan,
        "loss_requires_grad": False,
        "loss_finite": False,
        "backward_called": False,
        "backward_call_count": 0,
        "backward_success": False,
        "optimizer_step_called": False,
        "optimizer_step_call_count": 0,
        "optimizer_step_success": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "status": "blocked",
        "blocking_reasons": [],
    }
    try:
        optimizer.zero_grad(set_to_none=True)
        loss_result = build_optimizer_smoke_differentiable_loss_v0(model, input_contract, device)
        result["loss_requires_grad"] = bool(loss_result.get("loss_requires_grad"))
        result["loss_finite"] = bool(loss_result.get("loss_finite"))
        result["loss_value"] = float(loss_result.get("selected_loss_value", math.nan))
        result["blocking_reasons"].extend(loss_result.get("blocking_reasons", []))
        loss_tensor = loss_result.get("loss_tensor")
        if not torch.is_tensor(loss_tensor):
            result["blocking_reasons"].append("loss_tensor_missing")
            return result
        if not loss_tensor.requires_grad:
            result["blocking_reasons"].append("loss_tensor_does_not_require_grad")
            return result
        if not bool(torch.isfinite(loss_tensor.detach()).all().item()):
            result["blocking_reasons"].append("loss_tensor_not_finite")
            return result
        loss_tensor.backward()
        result["backward_called"] = True
        result["backward_call_count"] = 1
        result["backward_success"] = True
        grad_stats = collect_gradient_stats_v0(model)
        result.update(grad_stats)
        snapshot = capture_parameter_snapshot_summary_v0(model)
        result["sampled_parameter_count"] = int(snapshot.get("sampled_parameter_count", 0))
        optimizer.step()
        result["optimizer_step_called"] = True
        result["optimizer_step_call_count"] = 1
        result["optimizer_step_success"] = True
        result.update(compute_parameter_delta_summary_v0(snapshot, model))
        optimizer.zero_grad(set_to_none=True)
        required_true = [
            "loss_requires_grad",
            "loss_finite",
            "backward_called",
            "backward_success",
            "optimizer_step_called",
            "optimizer_step_success",
            "finite_nonzero_grad_exists",
            "finite_parameter_delta",
        ]
        for field_name in required_true:
            if result.get(field_name) is not True:
                result["blocking_reasons"].append(f"{field_name}_not_true")
        expected_values = {
            "backward_call_count": 1,
            "optimizer_step_call_count": 1,
            "grad_nan_count": 0,
            "grad_inf_count": 0,
            "delta_nan_count": 0,
            "delta_inf_count": 0,
            "checkpoint_saved": False,
            "model_saved": False,
            "tensor_dump_saved": False,
        }
        for key, expected in expected_values.items():
            if result.get(key) != expected:
                result["blocking_reasons"].append(f"{key}_invalid:{result.get(key)!r}")
        for key in ["loss_value", "total_grad_norm", "max_abs_grad", "parameter_delta_l2_total", "parameter_delta_max_abs"]:
            value = float(result.get(key, 0.0))
            if not math.isfinite(value) or value <= 0.0:
                result["blocking_reasons"].append(f"{key}_not_positive_finite")
        if int(result.get("changed_parameter_count", 0)) <= 0:
            result["blocking_reasons"].append("changed_parameter_count_not_positive")
        result["blocking_reasons"] = sorted(set(reason for reason in result["blocking_reasons"] if reason))
        result["status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["blocking_reasons"].append(f"tiny_training_step_failed:{type(exc).__name__}:{exc}")
        result["status"] = "blocked"
    return result


def run_tiny_training_dry_run_v0(device: str = "cpu") -> dict[str, Any]:
    result: dict[str, Any] = {
        "step11k_validated": False,
        "requested_device": device,
        "resolved_device": device,
        "model_instantiated": False,
        "strict_load_success": False,
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "optimizer_created": False,
        "optimizer_class": "",
        "optimizer_lr": 0.0,
        "optimizer_weight_decay": 0.0,
        "optimizer_param_group_count": 0,
        "optimizer_parameter_count": 0,
        "step_rows": [],
        "blocking_reasons": [],
    }
    model = None
    optimizer = None
    try:
        result["step11k_validated"] = validate_step11k_outputs_v0()
        bundle = build_fresh_strict_loaded_model_for_optimizer_step_smoke_v0(device)
        model = bundle.get("model")
        result["resolved_device"] = bundle.get("resolved_device", device)
        result["model_instantiated"] = bool(bundle.get("model_instantiated"))
        result["strict_load_success"] = bool(bundle.get("strict_load_success"))
        result["pretrained_weights_loaded"] = bool(bundle.get("pretrained_weights_loaded"))
        result["pretrained_base_integration_proven"] = bool(bundle.get("pretrained_base_integration_proven"))
        if model is None or not result["strict_load_success"]:
            result["blocking_reasons"].append("fresh_strict_loaded_model_unavailable")
            return result
        optimizer_bundle = build_adamw_optimizer_for_smoke_v0(model)
        optimizer = optimizer_bundle["optimizer"]
        for key in [
            "optimizer_created",
            "optimizer_class",
            "optimizer_lr",
            "optimizer_weight_decay",
            "optimizer_param_group_count",
            "optimizer_parameter_count",
        ]:
            result[key] = optimizer_bundle.get(key, result.get(key))
        result["blocking_reasons"].extend(optimizer_bundle.get("blocking_reasons", []))
        input_contract = bundle.get("input_contract", {})
        resolved_device = bundle.get("resolved_device", device)
        step_rows = [
            run_one_tiny_training_step_v0(model, optimizer, input_contract, step_index, resolved_device)
            for step_index in range(1, MAX_STEPS + 1)
        ]
        result["step_rows"] = step_rows
        result["blocking_reasons"].extend(reason for row in step_rows for reason in row.get("blocking_reasons", []))
        return result
    except Exception as exc:
        result["blocking_reasons"].append(f"tiny_training_dry_run_failed:{type(exc).__name__}:{exc}")
        return result
    finally:
        del optimizer
        del model


def build_tiny_training_dry_run_decision_v0(run_result: dict[str, Any]) -> dict[str, Any]:
    step_rows = run_result.get("step_rows", [])
    all_steps_passed = bool(len(step_rows) == MAX_STEPS and all(row.get("status") == "passed" for row in step_rows))
    if all_steps_passed:
        status = "tiny_training_dry_run_passed"
        passed = True
        plumbing = True
        real_gate = True
        b3_allowed = True
        next_step = "b3_scaffold_only_mask_design"
    elif run_result.get("step11k_validated"):
        status = "tiny_training_step_failed"
        passed = False
        plumbing = False
        real_gate = False
        b3_allowed = False
        next_step = "tiny_training_step_debug"
    else:
        status = "step11k_precondition_failed"
        passed = False
        plumbing = False
        real_gate = False
        b3_allowed = False
        next_step = "tiny_training_dry_run_design_debug"
    return {
        "tiny_training_dry_run_status": status,
        "tiny_training_dry_run_passed": passed,
        "tiny_training_loop_plumbing_proven": plumbing,
        "real_covalent_loader_gate_allowed": real_gate,
        "b3_scaffold_only_mask_design_allowed": b3_allowed,
        "recommended_next_step": next_step,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
    }


def build_tiny_training_dry_run_v0(device: str = "cpu") -> dict[str, Any]:
    run_result = run_tiny_training_dry_run_v0(device)
    step_rows = run_result.get("step_rows", [])
    decision = build_tiny_training_dry_run_decision_v0(run_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(run_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    loss_values = [float(row.get("loss_value", math.nan)) for row in step_rows]
    finite_loss_all_steps = bool(step_rows and all(row.get("loss_finite") is True for row in step_rows))
    finite_grad_all_steps = bool(
        step_rows
        and all(row.get("grad_nan_count") == 0 and row.get("grad_inf_count") == 0 and row.get("finite_nonzero_grad_exists") for row in step_rows)
    )
    finite_parameter_delta_all_steps = bool(
        step_rows
        and all(
            row.get("delta_nan_count") == 0 and row.get("delta_inf_count") == 0 and row.get("finite_parameter_delta")
            for row in step_rows
        )
    )
    initial_loss_value = loss_values[0] if loss_values else math.nan
    final_loss_value = loss_values[-1] if loss_values else math.nan
    loss_decreased_optional = bool(math.isfinite(initial_loss_value) and math.isfinite(final_loss_value) and final_loss_value < initial_loss_value)
    loss_increased_warning = bool(math.isfinite(initial_loss_value) and math.isfinite(final_loss_value) and final_loss_value > initial_loss_value)
    all_checks_passed = bool(decision["tiny_training_dry_run_passed"] and not source_modified and not forbidden_artifacts and not blockers)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11k_validated": run_result.get("step11k_validated", False),
        "selected_mask_levels": [SELECTED_MASK_LEVEL],
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "input_source": "synthetic_10d_shape_contract",
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": run_result.get("requested_device", device),
        "resolved_device": run_result.get("resolved_device", device),
        "model_instantiated": run_result.get("model_instantiated", False),
        "strict_load_success": run_result.get("strict_load_success", False),
        "pretrained_weights_loaded": run_result.get("pretrained_weights_loaded", False),
        "pretrained_base_integration_proven": run_result.get("pretrained_base_integration_proven", False),
        "optimizer_created": run_result.get("optimizer_created", False),
        "optimizer_class": run_result.get("optimizer_class", ""),
        "optimizer_lr": run_result.get("optimizer_lr", 0.0),
        "optimizer_weight_decay": run_result.get("optimizer_weight_decay", 0.0),
        "reuse_optimizer_across_steps": True,
        "tiny_training_dry_run_step_count": MAX_STEPS,
        "step_count": len(step_rows),
        "all_steps_passed": bool(len(step_rows) == MAX_STEPS and all(row.get("status") == "passed" for row in step_rows)),
        "step_indices": [int(row.get("step_index", 0)) for row in step_rows],
        "loss_values": loss_values,
        "initial_loss_value": initial_loss_value,
        "final_loss_value": final_loss_value,
        "finite_loss_all_steps": finite_loss_all_steps,
        "loss_decreased_optional": loss_decreased_optional,
        "loss_increased_warning": loss_increased_warning,
        "loss_decrease_required": False,
        "backward_call_count_total": sum(int(row.get("backward_call_count", 0)) for row in step_rows),
        "optimizer_step_call_count_total": sum(int(row.get("optimizer_step_call_count", 0)) for row in step_rows),
        "finite_grad_all_steps": finite_grad_all_steps,
        "grad_nan_count_total": sum(int(row.get("grad_nan_count", 0)) for row in step_rows),
        "grad_inf_count_total": sum(int(row.get("grad_inf_count", 0)) for row in step_rows),
        "finite_parameter_delta_all_steps": finite_parameter_delta_all_steps,
        "delta_nan_count_total": sum(int(row.get("delta_nan_count", 0)) for row in step_rows),
        "delta_inf_count_total": sum(int(row.get("delta_inf_count", 0)) for row in step_rows),
        "max_total_grad_norm": max((float(row.get("total_grad_norm", 0.0)) for row in step_rows), default=0.0),
        "max_abs_grad_overall": max((float(row.get("max_abs_grad", 0.0)) for row in step_rows), default=0.0),
        "max_parameter_delta_l2": max((float(row.get("parameter_delta_l2_total", 0.0)) for row in step_rows), default=0.0),
        "max_parameter_delta_abs": max((float(row.get("parameter_delta_max_abs", 0.0)) for row in step_rows), default=0.0),
        **decision,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    step_table_rows = [
        {
            "stage": STAGE,
            "step_index": row.get("step_index", ""),
            "selected_mask_level": row.get("selected_mask_level", ""),
            "loss_value": row.get("loss_value", ""),
            "loss_requires_grad": row.get("loss_requires_grad", False),
            "loss_finite": row.get("loss_finite", False),
            "backward_called": row.get("backward_called", False),
            "backward_call_count": row.get("backward_call_count", 0),
            "backward_success": row.get("backward_success", False),
            "optimizer_step_called": row.get("optimizer_step_called", False),
            "optimizer_step_call_count": row.get("optimizer_step_call_count", 0),
            "optimizer_step_success": row.get("optimizer_step_success", False),
            "grad_nan_count": row.get("grad_nan_count", 0),
            "grad_inf_count": row.get("grad_inf_count", 0),
            "total_grad_norm": row.get("total_grad_norm", ""),
            "max_abs_grad": row.get("max_abs_grad", ""),
            "finite_nonzero_grad_exists": row.get("finite_nonzero_grad_exists", False),
            "sampled_parameter_count": row.get("sampled_parameter_count", 0),
            "changed_parameter_count": row.get("changed_parameter_count", 0),
            "unchanged_parameter_count": row.get("unchanged_parameter_count", 0),
            "parameter_delta_l2_total": row.get("parameter_delta_l2_total", ""),
            "parameter_delta_max_abs": row.get("parameter_delta_max_abs", ""),
            "parameter_delta_mean_abs": row.get("parameter_delta_mean_abs", ""),
            "finite_parameter_delta": row.get("finite_parameter_delta", False),
            "delta_nan_count": row.get("delta_nan_count", 0),
            "delta_inf_count": row.get("delta_inf_count", 0),
            "status": row.get("status", "blocked"),
            "blocking_reasons": ";".join(row.get("blocking_reasons", [])),
        }
        for row in step_rows
    ]
    return {
        "manifest": manifest,
        "step_table_rows": step_table_rows,
        "run_result": run_result,
        "decision": decision,
        "report_sections": {
            "step11k_precondition": {"step11k_validated": run_result.get("step11k_validated", False)},
            "pretrained_model_and_optimizer": {
                "model_instantiated": manifest["model_instantiated"],
                "strict_load_success": manifest["strict_load_success"],
                "optimizer_created": manifest["optimizer_created"],
                "optimizer_class": manifest["optimizer_class"],
                "optimizer_lr": manifest["optimizer_lr"],
            },
            "tiny_steps": step_table_rows,
            "decision": decision,
            "safety_boundary": {
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
