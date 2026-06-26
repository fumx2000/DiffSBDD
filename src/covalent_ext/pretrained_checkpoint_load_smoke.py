from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

import torch

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import _build_candidate_inputs
from covalent_ext.diffsbdd_forward_shape_smoke import (
    _collect_tensors,
    _instantiate_model_for_forward,
    _inspect_forward_output,
    move_diffsbdd_batch_to_device_v0,
    resolve_diffsbdd_forward_device_v0,
)
from covalent_ext.diffsbdd_model_instantiation import MODEL_CLASS_NAME


STAGE = "pretrained_checkpoint_load_smoke_v0"
PREVIOUS_STAGE = "first_checkpointed_training_dry_run_review_v0"
FULL_ARCHITECTURE_COMPATIBILITY_RATIO_THRESHOLD = 0.8
MASKED_LOSS_NEXT_STEP = "pretrained_masked_loss_smoke"
RECONCILIATION_NEXT_STEP = "pretrained_checkpoint_architecture_config_reconciliation"
DEBUG_NEXT_STEP = "manual_pretrained_checkpoint_load_debug"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
MODEL_CONFIG_PATH = "configs/crossdock_fullatom_cond.yml"
OUTPUT_ROOT = Path("data/derived/covalent_small/pretrained_checkpoint_load_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "pretrained_checkpoint_load_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "pretrained_checkpoint_load_smoke_manifest.json"
SUMMARY_MD = Path("docs/pretrained_checkpoint_load_smoke_v0_summary.md")
STEP10X_REVIEW_MANIFEST_JSON = Path(
    "data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0/metadata/first_checkpointed_training_dry_run_review_manifest.json"
)
STEP10X_LOCAL_ARTIFACT_JSON = Path(
    "data/derived/covalent_small/training_runs/first_checkpointed_training_dry_run_v0/metadata/local_checkpoint_artifact_review.json"
)
MASK_LEVEL = "A_warhead_only"
MASK_SCHEDULE = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
] * 3
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
SAFETY_FALSE_FIELDS = {
    "backward_called": False,
    "optimizer_created": False,
    "optimizer_step_called": False,
    "training_step_called": False,
    "trainer_fit_called": False,
    "checkpoint_saved": False,
    "model_saved": False,
    "formal_training_executed": False,
    "real_finetune_executed": False,
    "source_modification_allowed": False,
}
STATE_PREFIXES = [
    ("raw", ""),
    ("strip_model_prefix", "model."),
    ("strip_module_prefix", "module."),
    ("strip_dynamics_prefix", "dynamics."),
    ("strip_model_dynamics_prefix", "model.dynamics."),
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_diff_exists() -> bool:
    import subprocess

    paths = ["equivariant_diffusion/", "lightning_modules.py"]
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *paths],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
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


def validate_step10x_outputs_v0() -> bool:
    blockers: list[str] = []
    if not STEP10X_REVIEW_MANIFEST_JSON.is_file() or not STEP10X_LOCAL_ARTIFACT_JSON.is_file():
        raise FileNotFoundError("Step 10X review outputs are missing")
    manifest = _load_json(STEP10X_REVIEW_MANIFEST_JSON)
    local_artifact = _load_json(STEP10X_LOCAL_ARTIFACT_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "first_checkpointed_training_dry_run_v0",
        "step10w_run_passed": True,
        "review_status": "passed",
        "checkpoint_artifact_status": "passed",
        "resume_smoke_status": "passed",
        "training_boundary_status": "passed",
        "checkpoint_git_commit_allowed": False,
        "future_clean_run_recommended": True,
        "all_checks_passed": True,
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step10x_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(local_artifact.get("local_checkpoint_review_passed") is True, "step10x_local_artifact_not_passed", blockers)
    _expect(local_artifact.get("checkpoint_git_commit_allowed") is False, "step10x_checkpoint_git_commit_allowed", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def locate_pretrained_checkpoint_v0(path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    checkpoint_path = Path(path)
    present = checkpoint_path.is_file()
    result = {
        "checkpoint_path": str(checkpoint_path),
        "pretrained_checkpoint_present": present,
        "checkpoint_suffix": checkpoint_path.suffix,
        "checkpoint_size_bytes": int(checkpoint_path.stat().st_size) if present else 0,
        "checkpoint_sha256": _sha256(checkpoint_path) if present else "",
        "status": "blocked",
        "blocking_reasons": [],
    }
    if not present:
        result["blocking_reasons"].append("pretrained_checkpoint_missing")
    if present and checkpoint_path.suffix != ".ckpt":
        result["blocking_reasons"].append("checkpoint_suffix_not_ckpt")
    if present and result["checkpoint_size_bytes"] <= 0:
        result["blocking_reasons"].append("checkpoint_size_zero")
    if not result["blocking_reasons"]:
        result["status"] = "passed"
    return result


def _looks_like_state_dict(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    tensor_values = [child for child in value.values() if torch.is_tensor(child)]
    return len(tensor_values) > 0


def load_pretrained_checkpoint_payload_v0(path: str | Path = CHECKPOINT_PATH, map_location: str = "cpu") -> dict[str, Any]:
    result: dict[str, Any] = {
        "checkpoint_loaded": False,
        "checkpoint_payload_type": "",
        "checkpoint_top_level_keys": [],
        "has_state_dict": False,
        "has_hyper_parameters": False,
        "state_dict_key_count": 0,
        "sample_state_dict_keys": [],
        "raw_state_dict": {},
        "blocking_reasons": [],
    }
    try:
        payload = torch.load(Path(path), map_location=map_location)
        result["checkpoint_loaded"] = True
        result["checkpoint_payload_type"] = type(payload).__name__
        if isinstance(payload, dict):
            result["checkpoint_top_level_keys"] = list(payload.keys())
            result["has_hyper_parameters"] = "hyper_parameters" in payload
            if isinstance(payload.get("state_dict"), dict):
                raw_state_dict = payload["state_dict"]
                result["has_state_dict"] = True
            elif _looks_like_state_dict(payload):
                raw_state_dict = payload
                result["has_state_dict"] = False
            else:
                raw_state_dict = {}
                result["blocking_reasons"].append("state_dict_not_found")
        else:
            raw_state_dict = {}
            result["blocking_reasons"].append("payload_not_dict")
        result["raw_state_dict"] = raw_state_dict
        result["state_dict_key_count"] = len(raw_state_dict)
        result["sample_state_dict_keys"] = list(raw_state_dict.keys())[:20]
        if not raw_state_dict:
            result["blocking_reasons"].append("state_dict_empty")
    except Exception as exc:
        result["blocking_reasons"].append(f"checkpoint_load_failed:{type(exc).__name__}:{exc}")
    return result


def _strip_prefix_from_state_dict(raw_state_dict: dict[str, Any], prefix: str) -> OrderedDict[str, Any]:
    normalized: OrderedDict[str, Any] = OrderedDict()
    for key, value in raw_state_dict.items():
        new_key = key[len(prefix) :] if prefix and key.startswith(prefix) else key
        normalized[new_key] = value
    return normalized


def normalize_pretrained_state_dict_keys_v0(raw_state_dict: dict[str, Any]) -> dict[str, Any]:
    variants = []
    seen_names = set()
    for variant_name, prefix in STATE_PREFIXES:
        if variant_name in seen_names:
            continue
        state_dict = _strip_prefix_from_state_dict(raw_state_dict, prefix)
        variants.append(
            {
                "variant_name": variant_name,
                "key_count": len(state_dict),
                "sample_keys": list(state_dict.keys())[:20],
                "stripped_prefix": prefix,
                "state_dict": state_dict,
            }
        )
        seen_names.add(variant_name)
    return {"candidate_variants": variants}


def instantiate_model_for_pretrained_load_v0(device: str = "auto") -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    result: dict[str, Any] = {
        **device_info,
        "model_instantiated": False,
        "model_class": MODEL_CLASS_NAME,
        "trainable_parameter_count": 0,
        "state_dict_key_count": 0,
        "sample_model_state_keys": [],
        "model": None,
        "blocking_reasons": [],
    }
    try:
        candidate_inputs = _build_candidate_inputs(MASK_LEVEL)
        model, counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        if model is None:
            result["blocking_reasons"].extend(reasons or ["model_initialization_failed"])
            return result
        state_keys = list(model.state_dict().keys())
        result.update(
            {
                "model_instantiated": True,
                "model_class": MODEL_CLASS_NAME,
                "trainable_parameter_count": counts["trainable_parameter_count"],
                "state_dict_key_count": len(state_keys),
                "sample_model_state_keys": state_keys[:20],
                "model": model,
            }
        )
    except Exception as exc:
        result["blocking_reasons"].append(f"model_instantiation_failed:{type(exc).__name__}:{exc}")
    return result


def _shape(value: Any) -> list[int] | None:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else None


def _variant_compatibility(model_state: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    state_dict = variant["state_dict"]
    model_keys = set(model_state.keys())
    variant_keys = set(state_dict.keys())
    matched = sorted(model_keys.intersection(variant_keys))
    shape_matched = []
    incompatible = []
    for key in matched:
        if torch.is_tensor(model_state[key]) and torch.is_tensor(state_dict[key]) and model_state[key].shape == state_dict[key].shape:
            shape_matched.append(key)
        else:
            incompatible.append(key)
    return {
        "variant_name": variant["variant_name"],
        "matched_key_count": len(matched),
        "shape_matched_key_count": len(shape_matched),
        "missing_keys": sorted(model_keys - variant_keys),
        "unexpected_keys": sorted(variant_keys - model_keys),
        "incompatible_shapes": incompatible,
        "compatible_state_dict": OrderedDict((key, state_dict[key]) for key in shape_matched),
    }


def attempt_load_pretrained_state_dict_v0(model: torch.nn.Module, candidate_variants: list[dict[str, Any]]) -> dict[str, Any]:
    model_state = model.state_dict()
    compatibilities = [_variant_compatibility(model_state, variant) for variant in candidate_variants]
    best = max(compatibilities, key=lambda item: (item["shape_matched_key_count"], item["matched_key_count"]))
    best_variant = next(variant for variant in candidate_variants if variant["variant_name"] == best["variant_name"])
    best_variant_key_count = len(best_variant["state_dict"])
    shape_matched_ratio = (
        best["shape_matched_key_count"] / best_variant_key_count if best_variant_key_count else 0.0
    )
    result: dict[str, Any] = {
        "load_attempted": True,
        "best_variant_name": best["variant_name"],
        "strict_load_success": False,
        "nonstrict_load_success": False,
        "matched_key_count": best["matched_key_count"],
        "shape_matched_key_count": best["shape_matched_key_count"],
        "shape_matched_ratio": shape_matched_ratio,
        "missing_key_count": len(best["missing_keys"]),
        "unexpected_key_count": len(best["unexpected_keys"]),
        "incompatible_shape_count": len(best["incompatible_shapes"]),
        "missing_keys_sample": best["missing_keys"][:20],
        "unexpected_keys_sample": best["unexpected_keys"][:20],
        "incompatible_shapes_sample": [
            {
                "key": key,
                "model_shape": _shape(model_state[key]),
                "checkpoint_shape": _shape(next(v["state_dict"] for v in candidate_variants if v["variant_name"] == best["variant_name"])[key]),
            }
            for key in best["incompatible_shapes"][:20]
        ],
        "pretrained_partial_shape_load_success": False,
        "pretrained_full_architecture_compatible": False,
        "shape_mismatch_detected": bool(best["incompatible_shapes"]),
        "architecture_config_mismatch_suspected": bool(
            best["incompatible_shapes"]
            or best["missing_keys"]
            or best["unexpected_keys"]
            or shape_matched_ratio < FULL_ARCHITECTURE_COMPATIBILITY_RATIO_THRESHOLD
        ),
        "pretrained_weights_loaded": False,
        "variant_summaries": [
            {
                "variant_name": item["variant_name"],
                "matched_key_count": item["matched_key_count"],
                "shape_matched_key_count": item["shape_matched_key_count"],
                "missing_key_count": len(item["missing_keys"]),
                "unexpected_key_count": len(item["unexpected_keys"]),
                "incompatible_shape_count": len(item["incompatible_shapes"]),
            }
            for item in compatibilities
        ],
        "blocking_reasons": [],
    }
    if best["shape_matched_key_count"] == 0:
        result["blocking_reasons"].append("shape_matched_key_count_zero")
        return result

    if (
        not best["missing_keys"]
        and not best["unexpected_keys"]
        and not best["incompatible_shapes"]
        and len(best_variant["state_dict"]) == len(model_state)
    ):
        try:
            model.load_state_dict(best_variant["state_dict"], strict=True)
            result["strict_load_success"] = True
        except Exception:
            result["strict_load_success"] = False
    try:
        model.load_state_dict(best["compatible_state_dict"], strict=False)
        result["nonstrict_load_success"] = True
        result["pretrained_partial_shape_load_success"] = True
        result["pretrained_full_architecture_compatible"] = bool(
            shape_matched_ratio >= FULL_ARCHITECTURE_COMPATIBILITY_RATIO_THRESHOLD
            and (result["strict_load_success"] or result["nonstrict_load_success"])
        )
        result["pretrained_weights_loaded"] = result["pretrained_full_architecture_compatible"]
    except Exception as exc:
        result["blocking_reasons"].append(f"nonstrict_load_failed:{type(exc).__name__}:{exc}")
    return result


def run_no_grad_forward_smoke_v0(model: torch.nn.Module, device_info: dict[str, Any]) -> dict[str, Any]:
    result = {
        "forward_smoke_attempted": False,
        "forward_smoke_success": False,
        "output_shape_summary": {},
        "output_finite": False,
        "nan_count": 0,
        "inf_count": 0,
        "blocking_reasons": [],
    }
    try:
        model.eval()
        candidate_inputs = _build_candidate_inputs(MASK_LEVEL)
        data_batch = move_diffsbdd_batch_to_device_v0(
            candidate_inputs["data_batch"], torch.device(device_info["resolved_device"])
        )
        result["forward_smoke_attempted"] = True
        with torch.no_grad():
            output = model(data_batch)
        output_info = _inspect_forward_output(output)
        tensors = _collect_tensors(output)
        nan_count = 0
        inf_count = 0
        for tensor in tensors.values():
            if torch.is_floating_point(tensor) or torch.is_complex(tensor):
                nan_count += int(torch.isnan(tensor).sum().item())
                inf_count += int(torch.isinf(tensor).sum().item())
        result["output_shape_summary"] = output_info["tensor_output_shapes"]
        result["output_finite"] = bool(output_info["finite_tensor_outputs"])
        result["nan_count"] = nan_count
        result["inf_count"] = inf_count
        result["forward_smoke_success"] = bool(result["output_finite"] and nan_count == 0 and inf_count == 0)
        if not result["forward_smoke_success"]:
            result["blocking_reasons"].append("forward_output_not_finite")
    except Exception as exc:
        result["blocking_reasons"].append(f"forward_smoke_failed:{type(exc).__name__}:{exc}")
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result


def build_pretrained_checkpoint_load_smoke_v0(
    device: str = "auto",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
) -> dict[str, Any]:
    section_results: dict[str, Any] = {}
    blockers: list[str] = []
    try:
        validate_step10x_outputs_v0()
        step10x_passed = True
    except Exception as exc:
        step10x_passed = False
        blockers.append(f"step10x_validation_failed:{type(exc).__name__}:{exc}")
    section_results["step10x"] = {"step10x_review_passed": step10x_passed, "blocking_reasons": blockers[:]}

    location = locate_pretrained_checkpoint_v0(checkpoint_path)
    section_results["location"] = location
    if location["status"] != "passed":
        blockers.extend(location["blocking_reasons"])

    payload = load_pretrained_checkpoint_payload_v0(checkpoint_path) if location["status"] == "passed" else {}
    section_results["payload"] = payload
    raw_state_dict = payload.get("raw_state_dict", {}) if payload else {}
    if payload and payload["blocking_reasons"]:
        blockers.extend(payload["blocking_reasons"])

    variants = normalize_pretrained_state_dict_keys_v0(raw_state_dict) if raw_state_dict else {"candidate_variants": []}
    section_results["normalization"] = {
        "candidate_variant_count": len(variants["candidate_variants"]),
        "candidate_variant_summaries": [
            {
                "variant_name": variant["variant_name"],
                "key_count": variant["key_count"],
                "sample_keys": variant["sample_keys"],
                "stripped_prefix": variant["stripped_prefix"],
            }
            for variant in variants["candidate_variants"]
        ],
    }

    instantiation = instantiate_model_for_pretrained_load_v0(device=device) if step10x_passed and raw_state_dict else {}
    section_results["instantiation"] = instantiation
    model = instantiation.get("model") if instantiation else None
    if instantiation and instantiation["blocking_reasons"]:
        blockers.extend(instantiation["blocking_reasons"])

    load_result = (
        attempt_load_pretrained_state_dict_v0(model, variants["candidate_variants"])
        if model is not None and variants["candidate_variants"]
        else {
            "load_attempted": False,
            "best_variant_name": "",
            "strict_load_success": False,
            "nonstrict_load_success": False,
            "matched_key_count": 0,
            "shape_matched_key_count": 0,
            "shape_matched_ratio": 0.0,
            "missing_key_count": 0,
            "unexpected_key_count": 0,
            "incompatible_shape_count": 0,
            "missing_keys_sample": [],
            "unexpected_keys_sample": [],
            "incompatible_shapes_sample": [],
            "pretrained_partial_shape_load_success": False,
            "pretrained_full_architecture_compatible": False,
            "shape_mismatch_detected": False,
            "architecture_config_mismatch_suspected": False,
            "pretrained_weights_loaded": False,
            "variant_summaries": [],
            "blocking_reasons": ["load_not_attempted"],
        }
    )
    section_results["load"] = load_result
    blockers.extend(load_result["blocking_reasons"])

    device_info = {
        key: instantiation.get(key, "")
        for key in ["requested_device", "resolved_device", "cuda_available", "cuda_device_count", "cuda_device_name"]
    }
    forward = (
        run_no_grad_forward_smoke_v0(model, instantiation)
        if model is not None and load_result["pretrained_partial_shape_load_success"]
        else {
            "forward_smoke_attempted": False,
            "forward_smoke_success": False,
            "output_shape_summary": {},
            "output_finite": False,
            "nan_count": 0,
            "inf_count": 0,
            "blocking_reasons": ["forward_not_attempted"],
        }
    )
    section_results["forward"] = forward
    blockers.extend(forward["blocking_reasons"])

    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    all_checks_passed = bool(
        step10x_passed
        and location.get("status") == "passed"
        and payload.get("checkpoint_loaded") is True
        and instantiation.get("model_instantiated") is True
        and load_result["pretrained_partial_shape_load_success"]
        and forward["forward_smoke_success"]
        and not source_modified
        and not forbidden_artifacts
    )
    if all_checks_passed and load_result["pretrained_weights_loaded"]:
        recommended_next_step = MASKED_LOSS_NEXT_STEP
    elif all_checks_passed and load_result["pretrained_partial_shape_load_success"]:
        recommended_next_step = RECONCILIATION_NEXT_STEP
    else:
        recommended_next_step = DEBUG_NEXT_STEP
    if all_checks_passed and load_result["shape_mismatch_detected"]:
        all_checks_passed_meaning = "smoke_completed_and_mismatch_detected"
    elif all_checks_passed:
        all_checks_passed_meaning = "smoke_completed_and_pretrained_architecture_compatible"
    else:
        all_checks_passed_meaning = "smoke_blocked"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10x_review_passed": step10x_passed,
        "pretrained_checkpoint_path": str(checkpoint_path),
        "pretrained_checkpoint_present": location.get("pretrained_checkpoint_present", False),
        "pretrained_checkpoint_sha256": location.get("checkpoint_sha256", ""),
        "pretrained_checkpoint_size_bytes": location.get("checkpoint_size_bytes", 0),
        "pretrained_checkpoint_readable": payload.get("checkpoint_loaded", False),
        "pretrained_state_dict_extracted": bool(raw_state_dict),
        "checkpoint_loaded": payload.get("checkpoint_loaded", False),
        "checkpoint_payload_type": payload.get("checkpoint_payload_type", ""),
        "checkpoint_top_level_keys": payload.get("checkpoint_top_level_keys", []),
        "has_state_dict": payload.get("has_state_dict", False),
        "state_dict_key_count": payload.get("state_dict_key_count", 0),
        "candidate_variant_count": section_results["normalization"]["candidate_variant_count"],
        "model_instantiated": instantiation.get("model_instantiated", False),
        "model_class": instantiation.get("model_class", MODEL_CLASS_NAME),
        "requested_device": device_info.get("requested_device", device),
        "resolved_device": device_info.get("resolved_device", ""),
        "cuda_available": device_info.get("cuda_available", False),
        "cuda_device_name": device_info.get("cuda_device_name", ""),
        "load_attempted": load_result["load_attempted"],
        "best_variant_name": load_result["best_variant_name"],
        "strict_load_success": load_result["strict_load_success"],
        "nonstrict_load_success": load_result["nonstrict_load_success"],
        "matched_key_count": load_result["matched_key_count"],
        "shape_matched_key_count": load_result["shape_matched_key_count"],
        "shape_matched_ratio": load_result["shape_matched_ratio"],
        "missing_key_count": load_result["missing_key_count"],
        "unexpected_key_count": load_result["unexpected_key_count"],
        "incompatible_shape_count": load_result["incompatible_shape_count"],
        "missing_keys_sample": load_result["missing_keys_sample"],
        "unexpected_keys_sample": load_result["unexpected_keys_sample"],
        "incompatible_shapes_sample": load_result["incompatible_shapes_sample"],
        "pretrained_partial_shape_load_success": load_result["pretrained_partial_shape_load_success"],
        "pretrained_full_architecture_compatible": load_result["pretrained_full_architecture_compatible"],
        "pretrained_effective_load_status": (
            "architecture_compatible"
            if load_result["pretrained_weights_loaded"]
            else "partial_shape_compatible_only"
            if load_result["pretrained_partial_shape_load_success"]
            else "not_loaded"
        ),
        "shape_mismatch_detected": load_result["shape_mismatch_detected"],
        "architecture_config_mismatch_suspected": load_result["architecture_config_mismatch_suspected"],
        "pretrained_weights_loaded": load_result["pretrained_weights_loaded"],
        "forward_smoke_attempted": forward["forward_smoke_attempted"],
        "forward_smoke_success": forward["forward_smoke_success"],
        "output_shape_summary": forward["output_shape_summary"],
        "output_finite": forward["output_finite"],
        "nan_count": forward["nan_count"],
        "inf_count": forward["inf_count"],
        **SAFETY_FALSE_FIELDS,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "all_checks_passed": all_checks_passed,
        "all_checks_passed_meaning": all_checks_passed_meaning,
        "recommended_next_step": recommended_next_step,
        "blocking_reasons": sorted(set(blockers)),
    }
    model_for_return = instantiation.pop("model", None) if instantiation else None
    if model_for_return is not None:
        del model_for_return
    if device_info.get("resolved_device", "").startswith("cuda") and torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"manifest": manifest, "sections": section_results}
