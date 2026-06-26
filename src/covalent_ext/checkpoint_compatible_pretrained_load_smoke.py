from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.checkpoint_compatible_model_instantiation import (
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    TEMP_DATASET_NAME,
    _constructor_config_from_compatible_config,
    _instantiate_model_with_temp_dataset,
    _resolve_device,
    _shape,
    _temporary_10d_dataset_info,
    build_checkpoint_compatible_config_v0,
    build_checkpoint_compatible_input_contract_v0,
    load_checkpoint_shape_reference_v0,
    load_config_preview_v0,
    optional_checkpoint_compatible_forward_smoke_v0,
)


STAGE = "checkpoint_compatible_pretrained_load_smoke_v0"
PREVIOUS_STAGE = "checkpoint_compatible_instantiation_wrapper_v0"
STEP11D_MANIFEST_JSON = Path(
    "data/derived/covalent_small/checkpoint_compatible_instantiation_wrapper_v0/checkpoint_compatible_instantiation_manifest.json"
)
STEP11D_SUMMARY_MD = Path("docs/checkpoint_compatible_instantiation_wrapper_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/checkpoint_compatible_pretrained_load_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "checkpoint_compatible_pretrained_load_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "checkpoint_compatible_pretrained_load_smoke_manifest.json"
DIAGNOSTICS_JSON = OUTPUT_ROOT / "checkpoint_compatible_pretrained_load_diagnostics.json"
SUMMARY_MD = Path("docs/checkpoint_compatible_pretrained_load_smoke_v0_summary.md")
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
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


def _shape_map_from_state_dict(state_dict: dict[str, Any]) -> dict[str, list[int]]:
    return {key: _shape(value) for key, value in state_dict.items() if torch.is_tensor(value)}


def _shape_counts(checkpoint_shape_map: dict[str, list[int]], model_shape_map: dict[str, list[int]]) -> dict[str, Any]:
    matched_keys = sorted(set(checkpoint_shape_map) & set(model_shape_map))
    shape_matched = [key for key in matched_keys if checkpoint_shape_map[key] == model_shape_map[key]]
    incompatible = [key for key in matched_keys if checkpoint_shape_map[key] != model_shape_map[key]]
    missing = [key for key in model_shape_map if key not in checkpoint_shape_map]
    unexpected = [key for key in checkpoint_shape_map if key not in model_shape_map]
    denominator = len(checkpoint_shape_map) or 1
    return {
        "matched_key_count": len(matched_keys),
        "pre_load_shape_matched_key_count": len(shape_matched),
        "pre_load_shape_matched_ratio": len(shape_matched) / denominator,
        "pre_load_incompatible_shape_count": len(incompatible),
        "pre_load_missing_key_count": len(missing),
        "pre_load_unexpected_key_count": len(unexpected),
        "pre_load_incompatible_shape_keys": incompatible,
    }


def _count_output_nan_inf(value: Any) -> dict[str, int]:
    tensors: list[torch.Tensor] = []

    def collect(child: Any) -> None:
        if torch.is_tensor(child):
            tensors.append(child)
        elif isinstance(child, dict):
            for item in child.values():
                collect(item)
        elif isinstance(child, (list, tuple)):
            for item in child:
                collect(item)

    collect(value)
    nan_count = 0
    inf_count = 0
    for tensor in tensors:
        if torch.is_floating_point(tensor) or torch.is_complex(tensor):
            nan_count += int(torch.isnan(tensor).sum().item())
            inf_count += int(torch.isinf(tensor).sum().item())
    return {"nan_count": nan_count, "inf_count": inf_count}


def validate_step11d_outputs_v0() -> bool:
    if not STEP11D_MANIFEST_JSON.is_file() or not STEP11D_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11D outputs are missing")
    manifest = _load_json(STEP11D_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "checkpoint_original_config_instantiation_design_v0",
        "step11c_validated": True,
        "compatible_config_built": True,
        "input_contract_built": True,
        "target_joint_nf": 32,
        "target_hidden_nf": 128,
        "target_n_layers": 5,
        "target_mode": "pocket_conditioning",
        "target_pocket_representation": "full-atom",
        "target_atom_feature_dim": 10,
        "target_residue_feature_dim": 10,
        "target_egnn_blocks": 5,
        "model_instantiation_attempted": True,
        "model_instantiated": True,
        "model_class": "LigandPocketDDPM",
        "model_state_dict_key_count": 122,
        "checkpoint_state_dict_key_count": 122,
        "matched_key_count": 122,
        "shape_matched_key_count": 122,
        "shape_matched_ratio": 1.0,
        "incompatible_shape_count": 0,
        "missing_key_count": 0,
        "unexpected_key_count": 0,
        "reached_shape_match_goal": True,
        "wrapper_status": "checkpoint_compatible_instantiation_proven",
        "forward_smoke_attempted": True,
        "forward_smoke_success": True,
        "output_finite": True,
        "instantiation_status": "checkpoint_compatible_model_instantiated",
        "checkpoint_load_smoke_allowed": True,
        "recommended_next_step": "checkpoint_compatible_pretrained_load_smoke",
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "masked_loss_smoke_allowed": False,
        "pretrained_masked_loss_smoke_allowed": False,
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
    }
    blockers = [f"step11d_{key}_invalid:{manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("checkpoint_load_smoke_allowed") is not True:
        blockers.append("step11d_does_not_allow_checkpoint_load_smoke")
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_checkpoint_state_dict_for_smoke_v0(checkpoint_path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    path = Path(checkpoint_path)
    result: dict[str, Any] = {
        "checkpoint_present": path.is_file(),
        "checkpoint_path": str(path),
        "checkpoint_sha256": _sha256(path) if path.is_file() else "",
        "checkpoint_size_bytes": path.stat().st_size if path.is_file() else 0,
        "checkpoint_loaded": False,
        "checkpoint_payload_type": "",
        "top_level_keys": [],
        "has_state_dict": False,
        "has_hyper_parameters": False,
        "state_dict_key_count": 0,
        "state_dict_keys_sample": [],
        "state_dict_shape_map": {},
        "hyper_parameters_keys": [],
        "checkpoint_target_fields": {},
        "state_dict": {},
        "blocking_reasons": [],
    }
    if not path.is_file():
        result["blocking_reasons"].append("checkpoint_missing")
        return result
    try:
        payload = torch.load(path, map_location="cpu")
    except Exception as exc:
        result["blocking_reasons"].append(f"checkpoint_read_failed:{type(exc).__name__}:{exc}")
        return result
    result["checkpoint_loaded"] = True
    result["checkpoint_payload_type"] = type(payload).__name__
    if not isinstance(payload, dict):
        result["blocking_reasons"].append("checkpoint_payload_not_dict")
        return result
    result["top_level_keys"] = list(payload.keys())
    state_dict = payload.get("state_dict")
    hparams = payload.get("hyper_parameters")
    result["has_state_dict"] = isinstance(state_dict, dict)
    result["has_hyper_parameters"] = isinstance(hparams, dict)
    if isinstance(hparams, dict):
        result["hyper_parameters_keys"] = list(hparams.keys())
    if not isinstance(state_dict, dict):
        result["blocking_reasons"].append("state_dict_missing")
        return result
    shape_reference = load_checkpoint_shape_reference_v0(path)
    result["state_dict"] = state_dict
    result["state_dict_key_count"] = len(state_dict)
    result["state_dict_keys_sample"] = list(state_dict.keys())[:20]
    result["state_dict_shape_map"] = _shape_map_from_state_dict(state_dict)
    result["checkpoint_target_fields"] = shape_reference.get("checkpoint_target_fields", {})
    return result


def instantiate_model_for_pretrained_load_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    requested_device = device
    resolved_device = _resolve_device(device)
    checkpoint_reference = load_checkpoint_shape_reference_v0(checkpoint_path)
    preview_result = load_config_preview_v0(config_preview_path)
    preview = preview_result.get("preview", {})
    compatible_config = (
        build_checkpoint_compatible_config_v0(preview)
        if preview
        else {"compatible_config_built": False, "blocking_reasons": ["config_preview_missing"]}
    )
    input_contract = (
        build_checkpoint_compatible_input_contract_v0(checkpoint_reference, preview, compatible_config)
        if compatible_config.get("compatible_config_built")
        else {"input_contract_built": False, "blocking_reasons": ["compatible_config_not_built"]}
    )
    blockers = []
    blockers.extend(checkpoint_reference.get("blocking_reasons", []))
    blockers.extend(preview_result.get("blocking_reasons", []))
    blockers.extend(compatible_config.get("blocking_reasons", []))
    blockers.extend(input_contract.get("blocking_reasons", []))
    result: dict[str, Any] = {
        "model_instantiation_attempted": False,
        "model_instantiated": False,
        "model_class": "LigandPocketDDPM",
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "model_state_dict_key_count": 0,
        "trainable_parameter_count": 0,
        "model_state_dict_shape_map": {},
        "shape_match_ratio_vs_checkpoint": 0.0,
        "pre_load_shape_counts": {},
        "model": None,
        "input_contract": input_contract,
        "blocking_reasons": blockers,
    }
    if not (
        checkpoint_reference.get("has_state_dict")
        and preview_result.get("config_preview_loaded")
        and compatible_config.get("compatible_config_built")
        and input_contract.get("input_contract_built")
    ):
        return result
    result["model_instantiation_attempted"] = True
    try:
        config_dict = _constructor_config_from_compatible_config(compatible_config, TEMP_DATASET_NAME, resolved_device)
        model = _instantiate_model_with_temp_dataset(config_dict, _temporary_10d_dataset_info(), resolved_device)
        model_state_shapes = _shape_map_from_state_dict(model.state_dict())
        shape_counts = _shape_counts(checkpoint_reference["checkpoint_shape_map"], model_state_shapes)
        result.update(
            {
                "model_instantiated": True,
                "model_state_dict_key_count": len(model_state_shapes),
                "trainable_parameter_count": int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)),
                "model_state_dict_shape_map": model_state_shapes,
                "shape_match_ratio_vs_checkpoint": shape_counts["pre_load_shape_matched_ratio"],
                "pre_load_shape_counts": shape_counts,
                "model": model,
            }
        )
    except Exception as exc:
        result["blocking_reasons"].append(f"model_instantiation_failed:{type(exc).__name__}:{exc}")
    return result


def strict_load_checkpoint_weights_v0(model: Any, checkpoint_state_dict: dict[str, Any]) -> dict[str, Any]:
    model_shape_map = _shape_map_from_state_dict(model.state_dict())
    checkpoint_shape_map = _shape_map_from_state_dict(checkpoint_state_dict)
    counts = _shape_counts(checkpoint_shape_map, model_shape_map)
    result: dict[str, Any] = {
        **counts,
        "strict_load_attempted": False,
        "strict_load_success": False,
        "missing_keys": [],
        "unexpected_keys": [],
        "missing_keys_count": 0,
        "unexpected_keys_count": 0,
        "incompatible_shape_count": counts["pre_load_incompatible_shape_count"],
        "loaded_parameter_key_count": 0,
        "loaded_parameter_tensor_count": 0,
        "loaded_parameter_numel_total": 0,
        "load_exception_type": "",
        "load_exception_message": "",
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "nonstrict_diagnostic_only": False,
        "blocking_reasons": [],
    }
    if counts["pre_load_incompatible_shape_count"] or counts["pre_load_missing_key_count"] or counts["pre_load_unexpected_key_count"]:
        result["blocking_reasons"].append("pre_load_shape_mismatch_detected")
        return result
    result["strict_load_attempted"] = True
    try:
        load_result = model.load_state_dict(checkpoint_state_dict, strict=True)
        missing = list(getattr(load_result, "missing_keys", []))
        unexpected = list(getattr(load_result, "unexpected_keys", []))
        result["missing_keys"] = missing
        result["unexpected_keys"] = unexpected
        result["missing_keys_count"] = len(missing)
        result["unexpected_keys_count"] = len(unexpected)
        result["strict_load_success"] = len(missing) == 0 and len(unexpected) == 0
    except Exception as exc:
        result["load_exception_type"] = type(exc).__name__
        result["load_exception_message"] = str(exc)
        result["blocking_reasons"].append(f"strict_load_failed:{type(exc).__name__}")
    if result["strict_load_success"]:
        tensor_values = [value for value in checkpoint_state_dict.values() if torch.is_tensor(value)]
        result["loaded_parameter_key_count"] = len(checkpoint_state_dict)
        result["loaded_parameter_tensor_count"] = len(tensor_values)
        result["loaded_parameter_numel_total"] = int(sum(value.numel() for value in tensor_values))
        result["pretrained_weights_loaded"] = True
        result["pretrained_base_integration_proven"] = True
    return result


def run_loaded_model_no_grad_forward_smoke_v0(model: Any, input_contract: dict[str, Any], device: str = "cpu") -> dict[str, Any]:
    forward = optional_checkpoint_compatible_forward_smoke_v0(model, input_contract, device)
    # The helper already executes a no-grad forward and reports shape/finiteness.
    # Recompute finite-error counts only from the helper status to avoid persisting tensors.
    nan_inf = {"nan_count": 0 if forward.get("output_finite") else -1, "inf_count": 0 if forward.get("output_finite") else -1}
    return {
        "forward_smoke_attempted": forward.get("forward_smoke_attempted", False),
        "forward_smoke_success": forward.get("forward_smoke_success", False),
        "output_finite": forward.get("output_finite", False),
        "nan_count": nan_inf["nan_count"],
        "inf_count": nan_inf["inf_count"],
        "output_shape_summary": forward.get("forward_tensor_output_shapes", {}),
        "blocking_reasons": [] if forward.get("forward_smoke_success") else [forward.get("forward_smoke_skip_reason", "forward_smoke_blocked")],
    }


def build_checkpoint_compatible_pretrained_load_decision_v0(
    load_result: dict[str, Any],
    forward_result: dict[str, Any],
) -> dict[str, Any]:
    if load_result.get("strict_load_success") and forward_result.get("forward_smoke_success"):
        status = "checkpoint_compatible_pretrained_load_proven"
        weights_loaded = True
        integration_proven = True
        pretrained_masked_loss_allowed = True
        next_step = "pretrained_masked_loss_smoke_on_checkpoint_compatible_model"
    elif load_result.get("strict_load_success"):
        status = "strict_load_passed_forward_smoke_blocked"
        weights_loaded = True
        integration_proven = False
        pretrained_masked_loss_allowed = False
        next_step = "loaded_model_forward_smoke_debug"
    else:
        status = "strict_load_blocked"
        weights_loaded = False
        integration_proven = False
        pretrained_masked_loss_allowed = False
        next_step = "checkpoint_compatible_strict_load_debug"
    return {
        "load_smoke_status": status,
        "pretrained_weights_loaded": weights_loaded,
        "pretrained_base_integration_proven": integration_proven,
        "pretrained_masked_loss_smoke_allowed": pretrained_masked_loss_allowed,
        "masked_loss_smoke_allowed": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "recommended_next_step": next_step,
    }


def build_checkpoint_compatible_pretrained_load_smoke_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11d_validated = validate_step11d_outputs_v0()
    except Exception as exc:
        step11d_validated = False
        blockers.append(f"step11d_validation_failed:{type(exc).__name__}:{exc}")
    checkpoint = load_checkpoint_state_dict_for_smoke_v0(checkpoint_path)
    model_result = instantiate_model_for_pretrained_load_v0(device, checkpoint_path, config_preview_path)
    blockers.extend(checkpoint.get("blocking_reasons", []))
    blockers.extend(model_result.get("blocking_reasons", []))

    load_result: dict[str, Any] = {
        "strict_load_attempted": False,
        "strict_load_success": False,
        "missing_keys_count": 0,
        "unexpected_keys_count": 0,
        "incompatible_shape_count": 0,
        "loaded_parameter_key_count": 0,
        "loaded_parameter_numel_total": 0,
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "blocking_reasons": ["model_or_state_dict_unavailable"],
    }
    if model_result.get("model_instantiated") and checkpoint.get("state_dict"):
        load_result = strict_load_checkpoint_weights_v0(model_result["model"], checkpoint["state_dict"])
    blockers.extend(load_result.get("blocking_reasons", []))

    forward_result = {
        "forward_smoke_attempted": False,
        "forward_smoke_success": False,
        "output_finite": False,
        "nan_count": 0,
        "inf_count": 0,
        "output_shape_summary": {},
        "blocking_reasons": ["strict_load_not_successful"],
    }
    if load_result.get("strict_load_success"):
        forward_result = run_loaded_model_no_grad_forward_smoke_v0(
            model_result["model"],
            model_result["input_contract"],
            model_result["resolved_device"],
        )
    blockers.extend(forward_result.get("blocking_reasons", []))
    decision = build_checkpoint_compatible_pretrained_load_decision_v0(load_result, forward_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        step11d_validated
        and checkpoint.get("checkpoint_loaded")
        and checkpoint.get("has_state_dict")
        and model_result.get("model_instantiated")
        and load_result.get("strict_load_success")
        and forward_result.get("forward_smoke_success")
        and decision["pretrained_weights_loaded"]
        and decision["pretrained_base_integration_proven"]
        and not source_modified
        and not forbidden_artifacts
    )
    pre_load_counts = model_result.get("pre_load_shape_counts", {})
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11d_validated": step11d_validated,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": checkpoint.get("checkpoint_sha256", ""),
        "checkpoint_size_bytes": checkpoint.get("checkpoint_size_bytes", 0),
        "checkpoint_loaded": checkpoint.get("checkpoint_loaded", False),
        "checkpoint_state_dict_key_count": checkpoint.get("state_dict_key_count", 0),
        "model_instantiated": model_result.get("model_instantiated", False),
        "model_class": model_result.get("model_class", "LigandPocketDDPM"),
        "requested_device": model_result.get("requested_device", device),
        "resolved_device": model_result.get("resolved_device", "cpu"),
        "model_state_dict_key_count": model_result.get("model_state_dict_key_count", 0),
        "pre_load_shape_matched_key_count": pre_load_counts.get("pre_load_shape_matched_key_count", 0),
        "pre_load_shape_matched_ratio": pre_load_counts.get("pre_load_shape_matched_ratio", 0.0),
        "pre_load_incompatible_shape_count": pre_load_counts.get("pre_load_incompatible_shape_count", 0),
        "strict_load_attempted": load_result.get("strict_load_attempted", False),
        "strict_load_success": load_result.get("strict_load_success", False),
        "missing_keys_count": load_result.get("missing_keys_count", 0),
        "unexpected_keys_count": load_result.get("unexpected_keys_count", 0),
        "incompatible_shape_count": load_result.get("incompatible_shape_count", 0),
        "loaded_parameter_key_count": load_result.get("loaded_parameter_key_count", 0),
        "loaded_parameter_numel_total": load_result.get("loaded_parameter_numel_total", 0),
        "pretrained_weights_loaded": decision["pretrained_weights_loaded"],
        "pretrained_base_integration_proven": decision["pretrained_base_integration_proven"],
        "forward_smoke_attempted": forward_result.get("forward_smoke_attempted", False),
        "forward_smoke_success": forward_result.get("forward_smoke_success", False),
        "output_finite": forward_result.get("output_finite", False),
        "nan_count": forward_result.get("nan_count", 0),
        "inf_count": forward_result.get("inf_count", 0),
        "output_shape_summary": forward_result.get("output_shape_summary", {}),
        **decision,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    diagnostics = {
        "checkpoint_top_level_keys": checkpoint.get("top_level_keys", []),
        "checkpoint_hyper_parameters_keys": checkpoint.get("hyper_parameters_keys", []),
        "state_dict_keys_sample": checkpoint.get("state_dict_keys_sample", []),
        "load_result_summary": {
            key: load_result.get(key)
            for key in [
                "strict_load_attempted",
                "strict_load_success",
                "missing_keys_count",
                "unexpected_keys_count",
                "incompatible_shape_count",
                "loaded_parameter_key_count",
                "loaded_parameter_tensor_count",
                "loaded_parameter_numel_total",
                "nonstrict_diagnostic_only",
            ]
        },
        "forward_output_shape_summary": forward_result.get("output_shape_summary", {}),
        "strict_load_exception": {
            "type": load_result.get("load_exception_type", ""),
            "message": load_result.get("load_exception_message", ""),
        },
        "nonstrict_diagnostic_only": load_result.get("nonstrict_diagnostic_only", False),
    }
    return {
        "manifest": manifest,
        "diagnostics": diagnostics,
        "report_sections": {
            "step11d": {"step11d_validated": step11d_validated},
            "checkpoint_state_dict": checkpoint,
            "model_instantiation": model_result,
            "pre_load_shape_match": pre_load_counts,
            "strict_load": load_result,
            "loaded_model_forward_smoke": forward_result,
            "decision": decision,
            "safety_boundary": {
                "backward_called": False,
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
