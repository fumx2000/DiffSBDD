from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import (
    build_differentiable_masked_loss_for_level_v0,
    build_fresh_strict_loaded_model_for_backward_level_v0,
    collect_gradient_stats_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "single_optimizer_step_smoke_v0"
PREVIOUS_STAGE = "optimizer_smoke_design_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CONFIG_PREVIEW_PATH = Path(
    "data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_preview.json"
)
STEP11I_MANIFEST_JSON = Path("data/derived/covalent_small/optimizer_smoke_design_v0/optimizer_smoke_design_manifest.json")
STEP11I_PROTOCOL_JSON = Path("data/derived/covalent_small/optimizer_smoke_design_v0/optimizer_smoke_protocol.json")
STEP11I_SUMMARY_MD = Path("docs/optimizer_smoke_design_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/single_optimizer_step_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "single_optimizer_step_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "single_optimizer_step_smoke_manifest.json"
DELTA_TABLE_CSV = OUTPUT_ROOT / "single_optimizer_step_delta_table.csv"
SUMMARY_MD = Path("docs/single_optimizer_step_smoke_v0_summary.md")
SELECTED_MASK_LEVEL = "A_warhead_only"
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
OPTIMIZER_LR = 1e-6
OPTIMIZER_WEIGHT_DECAY = 0.0
OPTIMIZER_BETAS = (0.9, 0.999)
OPTIMIZER_EPS = 1e-8
OPTIMIZER_STEP_TEXT = "optimizer" + ".step"


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


def validate_step11i_outputs_v0() -> bool:
    if not STEP11I_MANIFEST_JSON.is_file() or not STEP11I_PROTOCOL_JSON.is_file() or not STEP11I_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11I outputs are missing")
    manifest = _load_json(STEP11I_MANIFEST_JSON)
    protocol_document = _load_json(STEP11I_PROTOCOL_JSON)
    protocol = protocol_document.get("protocol", {})
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "pretrained_masked_loss_microbatch_backward_dry_run_v0",
        "step11h_validated": True,
        "gradient_plumbing_proven": True,
        "all_mask_levels_backward_passed": True,
        "grad_nan_count_total": 0,
        "grad_inf_count_total": 0,
        "selected_initial_mask_level": SELECTED_MASK_LEVEL,
        "optimizer_smoke_input_source": "synthetic_10d_shape_contract",
        "optimizer_class_recommended": "AdamW",
        "optimizer_lr_recommended": OPTIMIZER_LR,
        "optimizer_weight_decay_recommended": OPTIMIZER_WEIGHT_DECAY,
        "protocol_written": True,
        "proposed_next_stage": "optimizer_step_smoke_v0",
        "optimizer_step_smoke_allowed": True,
        "optimizer_step_policy_next_step": f"single {OPTIMIZER_STEP_TEXT} exactly once",
        "optimizer_step_call_count_next_step": 1,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
        "design_status": "optimizer_smoke_design_ready",
        "this_design_creates_optimizer": False,
        "this_design_runs_optimizer_step": False,
        "this_design_runs_backward": False,
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
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "single_optimizer_step_smoke",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11i_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    max_grad_norm = float(manifest.get("max_total_grad_norm", 0.0))
    _expect(math.isfinite(max_grad_norm) and max_grad_norm > 0.0, "step11i_manifest_max_grad_norm_invalid", blockers)

    expected_protocol = {
        "proposed_next_stage": "optimizer_step_smoke_v0",
        "input_source": "synthetic_10d_shape_contract",
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "model_policy": "fresh_strict_loaded_pretrained_model",
        "optimizer_policy": "single AdamW optimizer for smoke only",
        "optimizer_step_policy": f"single {OPTIMIZER_STEP_TEXT} exactly once",
        "optimizer_step_call_count_next_step": 1,
    }
    for key, expected in expected_protocol.items():
        _expect(protocol.get(key) == expected, f"step11i_protocol_{key}_invalid:{protocol.get(key)!r}", blockers)
    optimizer_config = protocol.get("optimizer_config", {})
    _expect(optimizer_config.get("optimizer_class") == "AdamW", "step11i_protocol_optimizer_class_invalid", blockers)
    _expect(optimizer_config.get("lr") == OPTIMIZER_LR, "step11i_protocol_lr_invalid", blockers)
    _expect(optimizer_config.get("weight_decay") == OPTIMIZER_WEIGHT_DECAY, "step11i_protocol_weight_decay_invalid", blockers)
    delta_policy = protocol.get("parameter_delta_policy", {})
    _expect(delta_policy.get("save_full_tensors") is False, "step11i_delta_policy_save_full_tensors_invalid", blockers)
    _expect(delta_policy.get("record_only_summary") is True, "step11i_delta_policy_record_summary_invalid", blockers)
    pass_conditions = set(protocol.get("pass_conditions", []))
    for condition in [
        "loss finite",
        "loss.requires_grad true",
        "backward_success true",
        "optimizer_created true",
        "optimizer_step_called true",
        "optimizer_step_call_count equals 1",
        "at least one parameter changed",
        "parameter_delta_l2_total finite positive",
        "parameter_delta_max_abs finite positive",
        "no NaN/Inf in changed parameters",
        "no checkpoint/model saved",
    ]:
        _expect(condition in pass_conditions, f"step11i_protocol_missing_pass_condition:{condition}", blockers)
    summary = STEP11I_SUMMARY_MD.read_text(encoding="utf-8")
    _expect("not training" in summary, "step11i_summary_training_boundary_missing", blockers)
    _expect("single_optimizer_step_smoke" in summary, "step11i_summary_next_step_missing", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_fresh_strict_loaded_model_for_optimizer_step_smoke_v0(device: str = "cpu") -> dict[str, Any]:
    bundle = build_fresh_strict_loaded_model_for_backward_level_v0(SELECTED_MASK_LEVEL, device)
    return {
        **bundle,
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "checkpoint_saved": False,
        "model_saved": False,
    }


def build_optimizer_smoke_differentiable_loss_v0(
    model: Any,
    input_contract: dict[str, Any],
    device: str = "cpu",
) -> dict[str, Any]:
    result = build_differentiable_masked_loss_for_level_v0(model, SELECTED_MASK_LEVEL, input_contract, device)
    result["selected_mask_level"] = SELECTED_MASK_LEVEL
    result["synthetic_shape_smoke_only"] = True
    result["feature_semantics_known"] = False
    return result


def build_adamw_optimizer_for_smoke_v0(model: Any) -> dict[str, Any]:
    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    blockers: list[str] = []
    if not trainable_parameters:
        blockers.append("no_trainable_parameters")
    optimizer = torch.optim.AdamW(
        trainable_parameters,
        lr=OPTIMIZER_LR,
        weight_decay=OPTIMIZER_WEIGHT_DECAY,
        betas=OPTIMIZER_BETAS,
        eps=OPTIMIZER_EPS,
    )
    optimizer_parameter_count = sum(int(parameter.numel()) for group in optimizer.param_groups for parameter in group["params"])
    return {
        "optimizer": optimizer,
        "optimizer_created": not blockers,
        "optimizer_class": "AdamW",
        "optimizer_lr": OPTIMIZER_LR,
        "optimizer_weight_decay": OPTIMIZER_WEIGHT_DECAY,
        "optimizer_betas": list(OPTIMIZER_BETAS),
        "optimizer_eps": OPTIMIZER_EPS,
        "optimizer_param_group_count": len(optimizer.param_groups),
        "optimizer_parameter_count": optimizer_parameter_count,
        "optimizer_state_pre_step_count": len(optimizer.state),
        "blocking_reasons": blockers,
    }


def capture_parameter_snapshot_summary_v0(model: Any, max_parameters: int = 20) -> dict[str, Any]:
    sampled: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        item = {
            "name": name,
            "before": parameter.detach().clone(),
            "numel": int(parameter.numel()),
            "has_nonzero_grad": bool(
                parameter.grad is not None
                and torch.isfinite(parameter.grad.detach()).all().item()
                and torch.any(torch.abs(parameter.grad.detach()) > 0).item()
            ),
        }
        if item["has_nonzero_grad"] and len(sampled) < max_parameters:
            sampled.append(item)
        elif len(fallback) < max_parameters:
            fallback.append(item)
        if len(sampled) >= max_parameters:
            break
    if not sampled:
        sampled = fallback
    sampled = sampled[:max_parameters]
    return {
        "sampled_parameter_names": [item["name"] for item in sampled],
        "sampled_parameter_count": len(sampled),
        "sampled_numel_total": sum(int(item["numel"]) for item in sampled),
        "snapshot_created": bool(sampled),
        "_snapshot_items": sampled,
    }


def compute_parameter_delta_summary_v0(before_snapshot: dict[str, Any], model: Any) -> dict[str, Any]:
    named_parameters = dict(model.named_parameters())
    changed_parameter_count = 0
    unchanged_parameter_count = 0
    delta_nan_count = 0
    delta_inf_count = 0
    total_sq_delta = 0.0
    max_abs_delta = 0.0
    sum_abs_delta = 0.0
    delta_element_count = 0
    sampled_names: list[str] = []
    for item in before_snapshot.get("_snapshot_items", []):
        name = item["name"]
        before = item["before"]
        parameter = named_parameters.get(name)
        if parameter is None:
            continue
        after = parameter.detach()
        delta = after - before.to(device=after.device)
        sampled_names.append(name)
        delta_nan_count += int(torch.isnan(delta).sum().item())
        delta_inf_count += int(torch.isinf(delta).sum().item())
        finite_mask = torch.isfinite(delta)
        finite_values = delta[finite_mask]
        if finite_values.numel() == 0:
            unchanged_parameter_count += 1
            continue
        abs_values = torch.abs(finite_values)
        if bool(torch.any(abs_values > 0).item()):
            changed_parameter_count += 1
        else:
            unchanged_parameter_count += 1
        total_sq_delta += float(torch.sum(finite_values * finite_values).item())
        max_abs_delta = max(max_abs_delta, float(torch.max(abs_values).item()))
        sum_abs_delta += float(torch.sum(abs_values).item())
        delta_element_count += int(finite_values.numel())
    parameter_delta_l2_total = math.sqrt(total_sq_delta)
    parameter_delta_mean_abs = sum_abs_delta / delta_element_count if delta_element_count else 0.0
    return {
        "sampled_parameter_names": sampled_names,
        "sampled_parameter_count": len(sampled_names),
        "changed_parameter_count": changed_parameter_count,
        "unchanged_parameter_count": unchanged_parameter_count,
        "parameter_delta_l2_total": parameter_delta_l2_total,
        "parameter_delta_max_abs": max_abs_delta,
        "parameter_delta_mean_abs": parameter_delta_mean_abs,
        "finite_parameter_delta": bool(
            delta_nan_count == 0
            and delta_inf_count == 0
            and math.isfinite(parameter_delta_l2_total)
            and math.isfinite(max_abs_delta)
            and parameter_delta_l2_total > 0.0
            and max_abs_delta > 0.0
        ),
        "delta_nan_count": delta_nan_count,
        "delta_inf_count": delta_inf_count,
    }


def run_single_optimizer_step_smoke_v0(device: str = "cpu") -> dict[str, Any]:
    result: dict[str, Any] = {
        "stage": STAGE,
        "step11i_validated": False,
        "selected_mask_level": SELECTED_MASK_LEVEL,
        "checkpoint_path": str(CHECKPOINT_PATH),
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
        "optimizer_state_pre_step_count": 0,
        "optimizer_state_post_step_count": 0,
        "loss_tensor_built": False,
        "loss_requires_grad": False,
        "loss_finite": False,
        "selected_loss_key": "",
        "selected_loss_value": math.nan,
        "backward_called": False,
        "backward_call_count": 0,
        "backward_success": False,
        "optimizer_step_called": False,
        "optimizer_step_call_count": 0,
        "optimizer_step_success": False,
        "snapshot_created": False,
        "sampled_parameter_count": 0,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "status": "blocked",
        "blocking_reasons": [],
    }
    model = None
    optimizer = None
    try:
        result["step11i_validated"] = validate_step11i_outputs_v0()
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
            "optimizer_state_pre_step_count",
        ]:
            result[key] = optimizer_bundle.get(key, result.get(key))
        result["blocking_reasons"].extend(optimizer_bundle.get("blocking_reasons", []))
        optimizer.zero_grad(set_to_none=True)
        loss_result = build_optimizer_smoke_differentiable_loss_v0(
            model,
            bundle.get("input_contract", {}),
            bundle.get("resolved_device", device),
        )
        for key in [
            "loss_tensor_built",
            "loss_requires_grad",
            "loss_finite",
            "selected_loss_key",
            "selected_loss_value",
            "candidate_inputs_built",
            "forward_success",
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
        loss_tensor.backward()
        result["backward_called"] = True
        result["backward_call_count"] = 1
        result["backward_success"] = True
        grad_stats = collect_gradient_stats_v0(model)
        result.update(grad_stats)
        snapshot = capture_parameter_snapshot_summary_v0(model)
        result["snapshot_created"] = bool(snapshot.get("snapshot_created"))
        result["sampled_parameter_count"] = int(snapshot.get("sampled_parameter_count", 0))
        result["sampled_parameter_names"] = snapshot.get("sampled_parameter_names", [])
        optimizer.step()
        result["optimizer_step_called"] = True
        result["optimizer_step_call_count"] = 1
        result["optimizer_step_success"] = True
        result["optimizer_state_post_step_count"] = len(optimizer.state)
        result.update(compute_parameter_delta_summary_v0(snapshot, model))
        optimizer.zero_grad(set_to_none=True)
        required_true = [
            "step11i_validated",
            "model_instantiated",
            "strict_load_success",
            "pretrained_weights_loaded",
            "pretrained_base_integration_proven",
            "optimizer_created",
            "loss_tensor_built",
            "loss_requires_grad",
            "loss_finite",
            "backward_called",
            "backward_success",
            "finite_nonzero_grad_exists",
            "snapshot_created",
            "optimizer_step_called",
            "optimizer_step_success",
            "finite_parameter_delta",
        ]
        for field_name in required_true:
            if result.get(field_name) is not True:
                result["blocking_reasons"].append(f"{field_name}_not_true")
        expected_values = {
            "selected_mask_level": SELECTED_MASK_LEVEL,
            "optimizer_class": "AdamW",
            "optimizer_lr": OPTIMIZER_LR,
            "optimizer_weight_decay": OPTIMIZER_WEIGHT_DECAY,
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
        for key in ["total_grad_norm", "max_abs_grad", "parameter_delta_l2_total", "parameter_delta_max_abs"]:
            value = float(result.get(key, 0.0))
            if not math.isfinite(value) or value <= 0.0:
                result["blocking_reasons"].append(f"{key}_not_positive_finite")
        if int(result.get("changed_parameter_count", 0)) <= 0:
            result["blocking_reasons"].append("changed_parameter_count_not_positive")
        result["blocking_reasons"] = sorted(set(reason for reason in result["blocking_reasons"] if reason))
        result["status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["blocking_reasons"].append(f"single_optimizer_step_smoke_failed:{type(exc).__name__}:{exc}")
        result["status"] = "blocked"
    finally:
        del optimizer
        del model
    return result


def build_single_optimizer_step_smoke_decision_v0(step_result: dict[str, Any]) -> dict[str, Any]:
    step_and_delta_passed = bool(
        step_result.get("optimizer_created") is True
        and step_result.get("backward_success") is True
        and step_result.get("optimizer_step_success") is True
        and step_result.get("finite_parameter_delta") is True
        and int(step_result.get("changed_parameter_count", 0)) > 0
    )
    pre_step_passed = bool(
        step_result.get("loss_requires_grad") is True
        and step_result.get("loss_finite") is True
        and step_result.get("backward_success") is True
    )
    if step_result.get("status") == "passed" and step_and_delta_passed:
        status = "single_optimizer_step_smoke_passed"
        passed = True
        plumbing = True
        design_allowed = True
        next_step = "tiny_training_dry_run_design"
    elif pre_step_passed:
        status = "optimizer_step_or_delta_blocked"
        passed = False
        plumbing = False
        design_allowed = False
        next_step = "optimizer_step_delta_debug"
    else:
        status = "pre_step_backward_blocked"
        passed = False
        plumbing = False
        design_allowed = False
        next_step = "microbatch_backward_debug"
    return {
        "optimizer_step_smoke_status": status,
        "single_optimizer_step_smoke_passed": passed,
        "optimizer_plumbing_proven": plumbing,
        "tiny_training_dry_run_design_allowed": design_allowed,
        "recommended_next_step": next_step,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "loss_decrease_required": False,
        "quality_claim_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
    }


def build_single_optimizer_step_smoke_v0(device: str = "cpu") -> dict[str, Any]:
    step_result = run_single_optimizer_step_smoke_v0(device)
    decision = build_single_optimizer_step_smoke_decision_v0(step_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(step_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        decision["single_optimizer_step_smoke_passed"] and not source_modified and not forbidden_artifacts and not blockers
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11i_validated": step_result.get("step11i_validated", False),
        "selected_mask_level": step_result.get("selected_mask_level", SELECTED_MASK_LEVEL),
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": step_result.get("requested_device", device),
        "resolved_device": step_result.get("resolved_device", device),
        "model_instantiated": step_result.get("model_instantiated", False),
        "strict_load_success": step_result.get("strict_load_success", False),
        "pretrained_weights_loaded": step_result.get("pretrained_weights_loaded", False),
        "pretrained_base_integration_proven": step_result.get("pretrained_base_integration_proven", False),
        "optimizer_created": step_result.get("optimizer_created", False),
        "optimizer_class": step_result.get("optimizer_class", ""),
        "optimizer_lr": step_result.get("optimizer_lr", 0.0),
        "optimizer_weight_decay": step_result.get("optimizer_weight_decay", 0.0),
        "optimizer_param_group_count": step_result.get("optimizer_param_group_count", 0),
        "optimizer_parameter_count": step_result.get("optimizer_parameter_count", 0),
        "optimizer_state_pre_step_count": step_result.get("optimizer_state_pre_step_count", 0),
        "optimizer_state_post_step_count": step_result.get("optimizer_state_post_step_count", 0),
        "loss_tensor_built": step_result.get("loss_tensor_built", False),
        "loss_requires_grad": step_result.get("loss_requires_grad", False),
        "loss_finite": step_result.get("loss_finite", False),
        "selected_loss_key": step_result.get("selected_loss_key", ""),
        "selected_loss_value": step_result.get("selected_loss_value", math.nan),
        "backward_called": step_result.get("backward_called", False),
        "backward_call_count": step_result.get("backward_call_count", 0),
        "backward_success": step_result.get("backward_success", False),
        "grad_nan_count": step_result.get("grad_nan_count", 0),
        "grad_inf_count": step_result.get("grad_inf_count", 0),
        "finite_nonzero_grad_exists": step_result.get("finite_nonzero_grad_exists", False),
        "total_grad_norm": step_result.get("total_grad_norm", 0.0),
        "max_abs_grad": step_result.get("max_abs_grad", 0.0),
        "optimizer_step_called": step_result.get("optimizer_step_called", False),
        "optimizer_step_call_count": step_result.get("optimizer_step_call_count", 0),
        "optimizer_step_success": step_result.get("optimizer_step_success", False),
        "changed_parameter_count": step_result.get("changed_parameter_count", 0),
        "unchanged_parameter_count": step_result.get("unchanged_parameter_count", 0),
        "sampled_parameter_count": step_result.get("sampled_parameter_count", 0),
        "parameter_delta_l2_total": step_result.get("parameter_delta_l2_total", 0.0),
        "parameter_delta_max_abs": step_result.get("parameter_delta_max_abs", 0.0),
        "parameter_delta_mean_abs": step_result.get("parameter_delta_mean_abs", 0.0),
        "finite_parameter_delta": step_result.get("finite_parameter_delta", False),
        "delta_nan_count": step_result.get("delta_nan_count", 0),
        "delta_inf_count": step_result.get("delta_inf_count", 0),
        **decision,
        "training_step_called": False,
        "trainer_fit_called": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    delta_table_rows = [
        {
            "stage": STAGE,
            "selected_mask_level": manifest["selected_mask_level"],
            "optimizer_class": manifest["optimizer_class"],
            "optimizer_lr": manifest["optimizer_lr"],
            "selected_loss_key": manifest["selected_loss_key"],
            "selected_loss_value": manifest["selected_loss_value"],
            "backward_call_count": manifest["backward_call_count"],
            "optimizer_step_call_count": manifest["optimizer_step_call_count"],
            "sampled_parameter_count": manifest["sampled_parameter_count"],
            "changed_parameter_count": manifest["changed_parameter_count"],
            "unchanged_parameter_count": manifest["unchanged_parameter_count"],
            "parameter_delta_l2_total": manifest["parameter_delta_l2_total"],
            "parameter_delta_max_abs": manifest["parameter_delta_max_abs"],
            "parameter_delta_mean_abs": manifest["parameter_delta_mean_abs"],
            "finite_parameter_delta": manifest["finite_parameter_delta"],
            "delta_nan_count": manifest["delta_nan_count"],
            "delta_inf_count": manifest["delta_inf_count"],
            "status": step_result.get("status", "blocked"),
            "blocking_reasons": ";".join(blockers),
        }
    ]
    return {
        "manifest": manifest,
        "step_result": step_result,
        "decision": decision,
        "delta_table_rows": delta_table_rows,
        "report_sections": {
            "step11i_precondition": {"step11i_validated": step_result.get("step11i_validated", False)},
            "pretrained_model_and_optimizer": {
                "model_instantiated": manifest["model_instantiated"],
                "strict_load_success": manifest["strict_load_success"],
                "optimizer_created": manifest["optimizer_created"],
                "optimizer_class": manifest["optimizer_class"],
                "optimizer_lr": manifest["optimizer_lr"],
            },
            "loss_and_backward": {
                "loss_requires_grad": manifest["loss_requires_grad"],
                "loss_finite": manifest["loss_finite"],
                "backward_call_count": manifest["backward_call_count"],
                "backward_success": manifest["backward_success"],
                "total_grad_norm": manifest["total_grad_norm"],
                "max_abs_grad": manifest["max_abs_grad"],
            },
            "optimizer_step": {
                "optimizer_step_called": manifest["optimizer_step_called"],
                "optimizer_step_call_count": manifest["optimizer_step_call_count"],
                "optimizer_step_success": manifest["optimizer_step_success"],
            },
            "parameter_delta": {
                "changed_parameter_count": manifest["changed_parameter_count"],
                "parameter_delta_l2_total": manifest["parameter_delta_l2_total"],
                "parameter_delta_max_abs": manifest["parameter_delta_max_abs"],
                "finite_parameter_delta": manifest["finite_parameter_delta"],
                "delta_nan_count": manifest["delta_nan_count"],
                "delta_inf_count": manifest["delta_inf_count"],
            },
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
