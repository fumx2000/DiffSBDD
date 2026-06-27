from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    AtomwiseProbeCapture,
    atomwise_probe_context_v0,
)
from covalent_ext.pretrained_masked_loss_microbatch_design import (  # noqa: E402
    MANIFEST_JSON as STEP11G_MANIFEST_JSON,
    PROTOCOL_JSON as STEP11G_PROTOCOL_JSON,
    SUMMARY_MD as STEP11G_SUMMARY_MD,
)
from covalent_ext.pretrained_masked_loss_smoke import (  # noqa: E402
    build_pretrained_masked_loss_candidate_inputs_v0,
    build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0,
)


STAGE = "pretrained_masked_loss_microbatch_backward_dry_run_v0"
PREVIOUS_STAGE = "pretrained_masked_loss_microbatch_design_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CONFIG_PREVIEW_PATH = Path(
    "data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_preview.json"
)
OUTPUT_ROOT = Path("data/derived/covalent_small/pretrained_masked_loss_microbatch_backward_dry_run_v0")
REPORT_CSV = OUTPUT_ROOT / "pretrained_masked_loss_microbatch_backward_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "pretrained_masked_loss_microbatch_backward_manifest.json"
GRADIENT_TABLE_CSV = OUTPUT_ROOT / "pretrained_masked_loss_microbatch_gradient_table.csv"
SUMMARY_MD = Path("docs/pretrained_masked_loss_microbatch_backward_dry_run_v0_summary.md")
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def validate_step11g_outputs_v0() -> bool:
    if not STEP11G_MANIFEST_JSON.is_file() or not STEP11G_PROTOCOL_JSON.is_file() or not STEP11G_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11G outputs are missing")
    manifest = _load_json(STEP11G_MANIFEST_JSON)
    protocol_doc = _load_json(STEP11G_PROTOCOL_JSON)
    protocol = protocol_doc.get("protocol", {})
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "pretrained_masked_loss_smoke_v0",
        "step11f_validated": True,
        "step11f_all_mask_levels_passed": True,
        "step11f_finite_loss_level_count": 4,
        "recommended_microbatch_input_source": "synthetic_10d_shape_contract",
        "synthetic_10d_contract_available": True,
        "protocol_written": True,
        "proposed_next_stage": "pretrained_masked_loss_microbatch_dry_run_v0",
        "microbatch_backward_policy": "isolated_backward_per_mask_level",
        "fresh_model_per_mask_level": True,
        "backward_allowed_next_step": True,
        "optimizer_allowed_next_step": False,
        "optimizer_step_allowed_next_step": False,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
        "design_status": "microbatch_dry_run_design_ready",
        "microbatch_backward_dry_run_allowed": True,
        "this_design_executes_backward": False,
        "this_design_creates_optimizer": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "optimizer_step_allowed": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "pretrained_masked_loss_microbatch_backward_dry_run",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11g_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(set(manifest.get("mask_levels_for_backward_dry_run", [])) == set(MASK_LEVELS), "step11g_mask_levels_invalid", blockers)
    expected_protocol = {
        "microbatch_backward_policy": "isolated_backward_per_mask_level",
        "fresh_model_per_mask_level": True,
        "strict_load_fresh_model_per_mask_level": True,
        "reverse_pass_invocations_per_mask_level": 1,
        "optimizer_allowed_next_step": False,
        "optimizer_step_allowed_next_step": False,
        "trainer_fit_allowed_next_step": False,
        "training_step_allowed_next_step": False,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
    }
    for key, expected in expected_protocol.items():
        _expect(protocol.get(key) == expected, f"step11g_protocol_{key}_invalid:{protocol.get(key)!r}", blockers)
    _expect(set(protocol.get("mask_levels_for_backward_dry_run", [])) == set(MASK_LEVELS), "step11g_protocol_masks_invalid", blockers)
    pass_conditions = set(protocol.get("pass_conditions", []))
    for condition in [
        "loss finite",
        "loss requires grad",
        "no optimizer object",
        "no optimizer step",
        "at least one parameter has finite nonzero grad",
    ]:
        _expect(condition in pass_conditions, f"step11g_protocol_missing_condition:{condition}", blockers)
    summary = STEP11G_SUMMARY_MD.read_text(encoding="utf-8")
    _expect("not training" in summary, "step11g_summary_training_boundary_missing", blockers)
    _expect("pretrained_masked_loss_microbatch_backward_dry_run" in summary, "step11g_summary_next_step_missing", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_fresh_strict_loaded_model_for_backward_level_v0(mask_level: str, device: str = "cpu") -> dict[str, Any]:
    if mask_level not in MASK_LEVELS:
        raise ValueError(f"Unsupported mask level: {mask_level}")
    bundle = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(
        device=device,
        checkpoint_path=CHECKPOINT_PATH,
        config_preview_path=CONFIG_PREVIEW_PATH,
    )
    return {
        **bundle,
        "mask_level": mask_level,
        "optimizer_created": False,
        "optimizer_step_called": False,
    }


def build_differentiable_masked_loss_for_level_v0(
    model: Any,
    mask_level: str,
    input_contract: dict[str, Any],
    device: str = "cpu",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "mask_level": mask_level,
        "candidate_inputs_built": False,
        "forward_attempted": False,
        "forward_success": False,
        "loss_tensor_built": False,
        "loss_requires_grad": False,
        "loss_finite": False,
        "selected_loss_key": "",
        "selected_loss_value": math.nan,
        "target_atom_count": 0,
        "context_atom_count": 0,
        "synthetic_shape_smoke_only": True,
        "feature_semantics_known": False,
        "loss_tensor": None,
        "blocking_reasons": [],
    }
    candidate = build_pretrained_masked_loss_candidate_inputs_v0(mask_level, input_contract, device)
    result["candidate_inputs_built"] = True
    metadata = candidate["metadata"]
    target_mask = metadata["target_mask"].to(dtype=torch.bool)
    result["target_atom_count"] = int(metadata["target_atom_count"])
    result["context_atom_count"] = int(metadata["context_atom_count"])
    capture = AtomwiseProbeCapture()
    model.eval()
    result["forward_attempted"] = True
    with atomwise_probe_context_v0(model, capture):
        _ = model(candidate["data_batch"])
    result["forward_success"] = True
    if capture.eps_t_lig is None or capture.net_out_lig is None:
        result["blocking_reasons"].append("atomwise_probe_tensors_missing")
        return result
    target_mask = target_mask.to(device=capture.net_out_lig.device)
    if int(target_mask.sum().item()) <= 0:
        result["blocking_reasons"].append("target_mask_empty")
        return result
    if capture.eps_t_lig.shape != capture.net_out_lig.shape:
        result["blocking_reasons"].append("captured_tensor_shape_mismatch")
        return result
    if target_mask.shape[0] != capture.net_out_lig.shape[0]:
        result["blocking_reasons"].append("target_mask_shape_mismatch")
        return result
    residual = capture.net_out_lig[target_mask] - capture.eps_t_lig[target_mask]
    loss_tensor = torch.mean(residual * residual)
    result["loss_tensor"] = loss_tensor
    result["loss_tensor_built"] = torch.is_tensor(loss_tensor)
    result["loss_requires_grad"] = bool(loss_tensor.requires_grad)
    result["loss_finite"] = bool(torch.isfinite(loss_tensor.detach()).all().item())
    result["selected_loss_key"] = "masked_loss_total_differentiable"
    result["selected_loss_value"] = float(loss_tensor.detach().item())
    for field_name in ["candidate_inputs_built", "forward_success", "loss_tensor_built", "loss_requires_grad", "loss_finite"]:
        if result.get(field_name) is not True:
            result["blocking_reasons"].append(f"{field_name}_not_true")
    return result


def collect_gradient_stats_v0(model: Any) -> dict[str, Any]:
    parameter_count = 0
    trainable_parameter_count = 0
    parameters_with_grad_count = 0
    parameters_with_nonzero_grad_count = 0
    parameters_with_finite_grad_count = 0
    none_grad_parameter_count = 0
    zero_grad_parameter_count = 0
    grad_nan_count = 0
    grad_inf_count = 0
    total_sq_norm = 0.0
    max_abs_grad = 0.0
    sum_abs_grad = 0.0
    grad_element_count = 0
    for parameter in model.parameters():
        parameter_count += int(parameter.numel())
        if not parameter.requires_grad:
            continue
        trainable_parameter_count += int(parameter.numel())
        grad = parameter.grad
        if grad is None:
            none_grad_parameter_count += 1
            continue
        parameters_with_grad_count += 1
        detached = grad.detach()
        nan_count = int(torch.isnan(detached).sum().item())
        inf_count = int(torch.isinf(detached).sum().item())
        grad_nan_count += nan_count
        grad_inf_count += inf_count
        finite_mask = torch.isfinite(detached)
        if bool(finite_mask.all().item()):
            parameters_with_finite_grad_count += 1
        finite_values = detached[finite_mask]
        if finite_values.numel() == 0:
            zero_grad_parameter_count += 1
            continue
        abs_values = torch.abs(finite_values)
        if bool(torch.any(abs_values > 0).item()):
            parameters_with_nonzero_grad_count += 1
        else:
            zero_grad_parameter_count += 1
        total_sq_norm += float(torch.sum(finite_values * finite_values).item())
        max_abs_grad = max(max_abs_grad, float(torch.max(abs_values).item()))
        sum_abs_grad += float(torch.sum(abs_values).item())
        grad_element_count += int(finite_values.numel())
    total_grad_norm = math.sqrt(total_sq_norm)
    mean_abs_grad = sum_abs_grad / grad_element_count if grad_element_count else 0.0
    return {
        "parameter_count": parameter_count,
        "trainable_parameter_count": trainable_parameter_count,
        "parameters_with_grad_count": parameters_with_grad_count,
        "parameters_with_nonzero_grad_count": parameters_with_nonzero_grad_count,
        "parameters_with_finite_grad_count": parameters_with_finite_grad_count,
        "zero_grad_parameter_count": zero_grad_parameter_count,
        "none_grad_parameter_count": none_grad_parameter_count,
        "grad_nan_count": grad_nan_count,
        "grad_inf_count": grad_inf_count,
        "total_grad_norm": total_grad_norm,
        "max_abs_grad": max_abs_grad,
        "mean_abs_grad": mean_abs_grad,
        "finite_nonzero_grad_exists": bool(
            parameters_with_nonzero_grad_count > 0
            and grad_nan_count == 0
            and grad_inf_count == 0
            and math.isfinite(total_grad_norm)
            and total_grad_norm > 0
        ),
    }


def run_isolated_backward_for_mask_level_v0(mask_level: str, device: str = "cpu") -> dict[str, Any]:
    result: dict[str, Any] = {
        "stage": STAGE,
        "mask_level": mask_level,
        "model_instantiated": False,
        "strict_load_success": False,
        "pretrained_weights_loaded": False,
        "candidate_inputs_built": False,
        "forward_success": False,
        "loss_tensor_built": False,
        "loss_requires_grad": False,
        "loss_finite": False,
        "selected_loss_key": "",
        "selected_loss_value": math.nan,
        "target_atom_count": 0,
        "context_atom_count": 0,
        "backward_attempted": False,
        "backward_called": False,
        "backward_call_count": 0,
        "backward_success": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "status": "blocked",
        "blocking_reasons": [],
    }
    try:
        bundle = build_fresh_strict_loaded_model_for_backward_level_v0(mask_level, device)
        model = bundle.get("model")
        result["model_instantiated"] = bool(bundle.get("model_instantiated"))
        result["strict_load_success"] = bool(bundle.get("strict_load_success"))
        result["pretrained_weights_loaded"] = bool(bundle.get("pretrained_weights_loaded"))
        if model is None or not result["strict_load_success"]:
            result["blocking_reasons"].append("fresh_strict_loaded_model_unavailable")
            return result
        model.zero_grad(set_to_none=True)
        loss_result = build_differentiable_masked_loss_for_level_v0(
            model,
            mask_level,
            bundle.get("input_contract", {}),
            bundle.get("resolved_device", device),
        )
        for key in [
            "candidate_inputs_built",
            "forward_success",
            "loss_tensor_built",
            "loss_requires_grad",
            "loss_finite",
            "selected_loss_key",
            "selected_loss_value",
            "target_atom_count",
            "context_atom_count",
        ]:
            result[key] = loss_result.get(key, result.get(key))
        result["blocking_reasons"].extend(loss_result.get("blocking_reasons", []))
        loss_tensor = loss_result.get("loss_tensor")
        if not torch.is_tensor(loss_tensor):
            result["blocking_reasons"].append("loss_tensor_missing")
            return result
        if not loss_tensor.requires_grad:
            result["blocking_reasons"].append("loss_tensor_does_not_require_grad")
            return result
        result["backward_attempted"] = True
        loss_tensor.backward()
        result["backward_called"] = True
        result["backward_call_count"] = 1
        result["backward_success"] = True
        grad_stats = collect_gradient_stats_v0(model)
        result.update(grad_stats)
        model.zero_grad(set_to_none=True)
        required_true = [
            "model_instantiated",
            "strict_load_success",
            "pretrained_weights_loaded",
            "candidate_inputs_built",
            "forward_success",
            "loss_tensor_built",
            "loss_requires_grad",
            "loss_finite",
            "backward_called",
            "backward_success",
            "finite_nonzero_grad_exists",
        ]
        for field_name in required_true:
            if result.get(field_name) is not True:
                result["blocking_reasons"].append(f"{field_name}_not_true")
        if result["backward_call_count"] != 1:
            result["blocking_reasons"].append("backward_call_count_not_one")
        if result.get("grad_nan_count", 0) != 0:
            result["blocking_reasons"].append("grad_nan_count_nonzero")
        if result.get("grad_inf_count", 0) != 0:
            result["blocking_reasons"].append("grad_inf_count_nonzero")
        if not math.isfinite(float(result.get("total_grad_norm", math.nan))):
            result["blocking_reasons"].append("total_grad_norm_not_finite")
        if not math.isfinite(float(result.get("max_abs_grad", math.nan))):
            result["blocking_reasons"].append("max_abs_grad_not_finite")
        if result["optimizer_created"] is not False or result["optimizer_step_called"] is not False:
            result["blocking_reasons"].append("optimizer_boundary_violated")
        result["blocking_reasons"] = sorted(set(reason for reason in result["blocking_reasons"] if reason))
        result["status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["blocking_reasons"].append(f"isolated_backward_failed:{type(exc).__name__}:{exc}")
        result["status"] = "blocked"
    return result


def run_pretrained_microbatch_backward_all_levels_v0(device: str = "cpu") -> dict[str, Any]:
    per_level_results = [run_isolated_backward_for_mask_level_v0(mask_level, device) for mask_level in MASK_LEVELS]
    mask_levels_passed = [row["mask_level"] for row in per_level_results if row["status"] == "passed"]
    failed_mask_levels = [row["mask_level"] for row in per_level_results if row["status"] != "passed"]
    gradient_table_rows = [
        {
            "stage": STAGE,
            "mask_level": row["mask_level"],
            "strict_load_success": row.get("strict_load_success", False),
            "loss_requires_grad": row.get("loss_requires_grad", False),
            "loss_finite": row.get("loss_finite", False),
            "selected_loss_key": row.get("selected_loss_key", ""),
            "selected_loss_value": row.get("selected_loss_value", ""),
            "backward_called": row.get("backward_called", False),
            "backward_call_count": row.get("backward_call_count", 0),
            "backward_success": row.get("backward_success", False),
            "parameter_count": row.get("parameter_count", 0),
            "trainable_parameter_count": row.get("trainable_parameter_count", 0),
            "parameters_with_grad_count": row.get("parameters_with_grad_count", 0),
            "parameters_with_nonzero_grad_count": row.get("parameters_with_nonzero_grad_count", 0),
            "parameters_with_finite_grad_count": row.get("parameters_with_finite_grad_count", 0),
            "none_grad_parameter_count": row.get("none_grad_parameter_count", 0),
            "zero_grad_parameter_count": row.get("zero_grad_parameter_count", 0),
            "grad_nan_count": row.get("grad_nan_count", 0),
            "grad_inf_count": row.get("grad_inf_count", 0),
            "total_grad_norm": row.get("total_grad_norm", ""),
            "max_abs_grad": row.get("max_abs_grad", ""),
            "mean_abs_grad": row.get("mean_abs_grad", ""),
            "finite_nonzero_grad_exists": row.get("finite_nonzero_grad_exists", False),
            "optimizer_created": row.get("optimizer_created", False),
            "optimizer_step_called": row.get("optimizer_step_called", False),
            "status": row.get("status", "blocked"),
            "blocking_reasons": ";".join(row.get("blocking_reasons", [])),
        }
        for row in per_level_results
    ]
    return {
        "per_level_results": per_level_results,
        "mask_levels_attempted": MASK_LEVELS,
        "mask_levels_passed": mask_levels_passed,
        "all_mask_levels_passed": len(mask_levels_passed) == len(MASK_LEVELS),
        "backward_level_count": len(per_level_results),
        "backward_success_level_count": sum(1 for row in per_level_results if row.get("backward_success")),
        "failed_mask_levels": failed_mask_levels,
        "gradient_table_rows": gradient_table_rows,
    }


def build_microbatch_backward_decision_v0(all_level_results: dict[str, Any]) -> dict[str, Any]:
    per_level = all_level_results.get("per_level_results", [])
    all_grad_finite = bool(per_level and all(row.get("grad_nan_count") == 0 and row.get("grad_inf_count") == 0 for row in per_level))
    all_nonzero = bool(per_level and all(row.get("finite_nonzero_grad_exists") is True for row in per_level))
    if all_level_results.get("all_mask_levels_passed") and all_grad_finite and all_nonzero:
        status = "pretrained_microbatch_backward_dry_run_passed"
        passed = True
        gradient_plumbing = True
        next_step = "optimizer_free_to_optimizer_smoke_design"
        optimizer_smoke_design_allowed = True
    elif per_level:
        status = "pretrained_microbatch_backward_partial"
        passed = False
        gradient_plumbing = False
        next_step = "failed_mask_level_backward_debug"
        optimizer_smoke_design_allowed = False
    else:
        status = "pretrained_model_unavailable"
        passed = False
        gradient_plumbing = False
        next_step = "pretrained_masked_loss_smoke_debug"
        optimizer_smoke_design_allowed = False
    return {
        "microbatch_backward_status": status,
        "microbatch_backward_dry_run_passed": passed,
        "gradient_plumbing_proven": gradient_plumbing,
        "optimizer_smoke_design_allowed": optimizer_smoke_design_allowed,
        "recommended_next_step": next_step,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "optimizer_step_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "checkpoint_saved": False,
        "model_saved": False,
    }


def build_pretrained_masked_loss_microbatch_backward_dry_run_v0(device: str = "cpu") -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11g_validated = validate_step11g_outputs_v0()
    except Exception as exc:
        step11g_validated = False
        blockers.append(f"step11g_validation_failed:{type(exc).__name__}:{exc}")
    all_levels = (
        run_pretrained_microbatch_backward_all_levels_v0(device)
        if step11g_validated
        else {
            "per_level_results": [],
            "mask_levels_attempted": MASK_LEVELS,
            "mask_levels_passed": [],
            "all_mask_levels_passed": False,
            "backward_level_count": 0,
            "backward_success_level_count": 0,
            "failed_mask_levels": MASK_LEVELS,
            "gradient_table_rows": [],
        }
    )
    decision = build_microbatch_backward_decision_v0(all_levels)
    for row in all_levels["per_level_results"]:
        blockers.extend(row.get("blocking_reasons", []))
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    per_level = all_levels["per_level_results"]
    grad_nan_count_total = sum(int(row.get("grad_nan_count", 0)) for row in per_level)
    grad_inf_count_total = sum(int(row.get("grad_inf_count", 0)) for row in per_level)
    max_total_grad_norm = max((float(row.get("total_grad_norm", 0.0)) for row in per_level), default=0.0)
    max_abs_grad_overall = max((float(row.get("max_abs_grad", 0.0)) for row in per_level), default=0.0)
    all_checks_passed = bool(
        step11g_validated
        and all_levels["all_mask_levels_passed"]
        and decision["microbatch_backward_dry_run_passed"]
        and not source_modified
        and not forbidden_artifacts
    )
    requested_device = device
    resolved_device = per_level[0].get("resolved_device", device) if per_level else device
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11g_validated": step11g_validated,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "pretrained_weights_loaded": bool(per_level and all(row.get("pretrained_weights_loaded") is True for row in per_level)),
        "pretrained_base_integration_proven": bool(per_level and all(row.get("strict_load_success") is True for row in per_level)),
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "microbatch_backward_policy": "isolated_backward_per_mask_level",
        "fresh_model_per_mask_level": True,
        "mask_levels_attempted": all_levels["mask_levels_attempted"],
        "mask_levels_passed": all_levels["mask_levels_passed"],
        "all_mask_levels_passed": all_levels["all_mask_levels_passed"],
        "backward_level_count": all_levels["backward_level_count"],
        "backward_success_level_count": all_levels["backward_success_level_count"],
        "failed_mask_levels": all_levels["failed_mask_levels"],
        "loss_requires_grad_all_levels": bool(per_level and all(row.get("loss_requires_grad") is True for row in per_level)),
        "finite_loss_all_levels": bool(per_level and all(row.get("loss_finite") is True for row in per_level)),
        "finite_nonzero_grad_all_levels": bool(per_level and all(row.get("finite_nonzero_grad_exists") is True for row in per_level)),
        "grad_nan_count_total": grad_nan_count_total,
        "grad_inf_count_total": grad_inf_count_total,
        "max_total_grad_norm": max_total_grad_norm,
        "max_abs_grad_overall": max_abs_grad_overall,
        "backward_called": bool(per_level and all(row.get("backward_called") is True for row in per_level)),
        "backward_call_count_total": sum(int(row.get("backward_call_count", 0)) for row in per_level),
        **decision,
        "training_step_called": False,
        "trainer_fit_called": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    return {
        "manifest": manifest,
        "gradient_table_rows": all_levels["gradient_table_rows"],
        "per_level_results": per_level,
        "report_sections": {
            "step11g_precondition": {"step11g_validated": step11g_validated},
            "mask_levels": per_level,
            "gradient_summary": {
                "grad_nan_count_total": grad_nan_count_total,
                "grad_inf_count_total": grad_inf_count_total,
                "max_total_grad_norm": max_total_grad_norm,
                "max_abs_grad_overall": max_abs_grad_overall,
            },
            "decision": decision,
            "safety_boundary": {
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
