from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import AtomwiseProbeCapture, atomwise_probe_context_v0
from covalent_ext.masked_loss_dry_run import compute_masked_loss_components_v0, summarize_loss_components_v0
from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0
from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import collect_gradient_stats_v0
from covalent_ext.pretrained_masked_loss_smoke import _count_nan_inf, _output0_and_info
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (
    BATCH_SIZE,
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_SOURCE,
    NUM_WORKERS,
    PROTECTED_SOURCE_PATHS,
    REQUESTED_DEVICE,
    RESOLVED_DEVICE,
    SELECTED_REAL_SAMPLE_INDEX,
    build_checkpoint_compatible_real_model_batch_v0,
    build_real_covalent_forward_loss_batch_bundle_v0,
    build_strict_loaded_real_size_checkpoint_compatible_model_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_backward_smoke_v0"
PREVIOUS_STAGE = "real_covalent_pretrained_forward_loss_smoke_v0"

STEP12D_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_pretrained_forward_loss_smoke_v0/"
    "real_covalent_pretrained_forward_loss_smoke_manifest.json"
)
STEP12D_LOSS_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_pretrained_forward_loss_smoke_v0/"
    "real_covalent_pretrained_forward_loss_smoke_loss_table.csv"
)
STEP12D_SUMMARY_MD = Path("docs/real_covalent_pretrained_forward_loss_smoke_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_backward_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_backward_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_backward_smoke_manifest.json"
GRAD_TABLE_CSV = OUTPUT_ROOT / "real_covalent_backward_smoke_grad_table.csv"
SUMMARY_MD = Path("docs/real_covalent_backward_smoke_v0_summary.md")

AGGREGATE_LOSS_REDUCTION = "mean"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _text_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
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


def _forbidden_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def validate_step12b_validator_behavior_v0() -> bool:
    expected_regions = {
        "A_warhead_only": "target",
        "B_linker_warhead": "target",
        "B2_scaffold_warhead": "target",
        "B3_scaffold_only": "context",
        "C_scaffold_linker_warhead": "target",
    }
    blockers: list[str] = []
    for mask_level, expected_region in expected_regions.items():
        _expect(
            expected_reactive_atom_region_for_mask_level_v0(mask_level) == expected_region,
            f"step12b_region_invalid:{mask_level}",
            blockers,
        )
    try:
        expected_reactive_atom_region_for_mask_level_v0("B3")
    except ValueError:
        short_b3_rejected = True
    else:
        short_b3_rejected = False
    _expect(short_b3_rejected, "step12b_short_alias_b3_accepted", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def validate_step12d_outputs_v0() -> bool:
    if not STEP12D_MANIFEST_JSON.is_file() or not STEP12D_LOSS_TABLE_CSV.is_file() or not STEP12D_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12D outputs are missing")
    manifest = _load_json(STEP12D_MANIFEST_JSON)
    rows = _read_csv(STEP12D_LOSS_TABLE_CSV)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_pretraining_smoke_design_v0",
        "step12c_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": REQUESTED_DEVICE,
        "resolved_device": RESOLVED_DEVICE,
        "batch_size": BATCH_SIZE,
        "num_workers": NUM_WORKERS,
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "attempted_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_strict_loaded_once": True,
        "model_forward_called": True,
        "model_forward_call_count": len(CANONICAL_MASK_LEVELS),
        "all_level_forward_call_count_exactly_one": True,
        "all_adapted_batches_valid": True,
        "all_model_inputs_valid": True,
        "all_diffsbdd_like_inputs_valid": True,
        "all_checkpoint_compatible_real_batches_constructed": True,
        "no_synthetic_fallback_used": True,
        "all_losses_computed": True,
        "all_losses_finite": True,
        "all_losses_require_grad": True,
        "selected_loss_key": "masked_loss_total_dry",
        "real_covalent_pretrained_forward_loss_smoke_passed": True,
        "real_covalent_forward_loss_contract_proven": True,
        "real_covalent_all_mask_levels_forward_loss_proven": True,
        "real_covalent_backward_smoke_allowed": True,
        "recommended_next_step": "real_covalent_backward_smoke",
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step12d_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(_finite_scalar(manifest.get("min_selected_loss_value")), "step12d_min_loss_not_finite", blockers)
    _expect(_finite_scalar(manifest.get("max_selected_loss_value")), "step12d_max_loss_not_finite", blockers)
    _expect(_finite_scalar(manifest.get("mean_selected_loss_value")), "step12d_mean_loss_not_finite", blockers)

    _expect(len(rows) == len(CANONICAL_MASK_LEVELS), f"step12d_loss_table_row_count_invalid:{len(rows)}", blockers)
    _expect([row.get("mask_level") for row in rows] == CANONICAL_MASK_LEVELS, "step12d_loss_table_mask_order_invalid", blockers)
    for row in rows:
        mask_level = row.get("mask_level", "")
        expected_region = "context" if mask_level == "B3_scaffold_only" else "target"
        checks = {
            "expected_reactive_atom_region": expected_region,
            "adapted_valid": "True",
            "model_input_valid": "True",
            "diffsbdd_like_valid": "True",
            "checkpoint_compatible_real_batch_constructed": "True",
            "no_synthetic_fallback_used": "True",
            "model_forward_called": "True",
            "forward_call_count": "1",
            "loss_computed": "True",
            "selected_loss_key": "masked_loss_total_dry",
            "loss_requires_grad": "True",
            "loss_finite": "True",
            "status": "passed",
        }
        for key, expected in checks.items():
            _expect(row.get(key) == expected, f"step12d_loss_table_{mask_level}_{key}_invalid:{row.get(key)!r}", blockers)
        _expect(_finite_scalar(row.get("selected_loss_value")), f"step12d_loss_table_{mask_level}_loss_not_finite", blockers)
        _expect(_text_bool(row.get("loss_requires_grad")), f"step12d_loss_table_{mask_level}_requires_grad_false", blockers)
        _expect(_text_bool(row.get("loss_finite")), f"step12d_loss_table_{mask_level}_loss_finite_false", blockers)

    summary = STEP12D_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "real covalent pretrained forward/loss smoke, not training",
        "recommended_next_step: real_covalent_backward_smoke",
    ]:
        _expect(snippet in summary, f"step12d_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _run_differentiable_forward_loss_for_level(
    model: Any,
    checkpoint_batch: dict[str, Any],
    mask_level: str,
    forward_seed: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    metadata = checkpoint_batch["metadata"]
    result: dict[str, Any] = {
        "row_type": "mask_level_loss",
        "mask_level": mask_level,
        "expected_reactive_atom_region": metadata["expected_reactive_atom_region"],
        "sample_ids": list(metadata["real_sample_ids"]),
        "batch_size": BATCH_SIZE,
        "adapted_valid": True,
        "model_input_valid": True,
        "diffsbdd_like_valid": True,
        "checkpoint_compatible_real_batch_constructed": metadata["checkpoint_compatible_batch_constructed"],
        "no_synthetic_fallback_used": metadata["no_synthetic_fallback_used"],
        "model_forward_called": False,
        "forward_call_count": 0,
        "loss_computed": False,
        "selected_loss_key": "masked_loss_total_dry",
        "selected_loss_value": math.nan,
        "loss_requires_grad": False,
        "loss_finite": False,
        "target_atom_count": metadata["target_atom_count"],
        "context_atom_count": metadata["context_atom_count"],
        "status": "blocked",
        "blocking_reasons": [],
        "loss_tensor": None,
    }
    if not metadata["checkpoint_compatible_batch_constructed"]:
        blockers.extend(metadata.get("blocking_reasons", []))
        blockers.append("checkpoint_compatible_real_model_batch_unavailable")
        result["blocking_reasons"] = sorted(set(blockers))
        return result

    torch.manual_seed(forward_seed)
    model.eval()
    capture = AtomwiseProbeCapture()
    try:
        with atomwise_probe_context_v0(model, capture):
            output = model(checkpoint_batch["data_batch"])
        result["model_forward_called"] = True
        result["forward_call_count"] = 1
        nan_inf = _count_nan_inf(output)
        blockers.extend(f"forward_output_{key}:{value}" for key, value in nan_inf.items() if int(value) > 0)
        output0, _info = _output0_and_info(output)
        if not torch.is_tensor(output0):
            blockers.append("output0_not_tensor")
        if capture.eps_t_lig is None or capture.net_out_lig is None:
            blockers.append("atomwise_probe_tensors_missing")
        if torch.is_tensor(output0) and capture.eps_t_lig is not None and capture.net_out_lig is not None:
            loss_components = compute_masked_loss_components_v0(
                output0,
                capture.eps_t_lig,
                capture.net_out_lig,
                checkpoint_batch["target_mask"],
            )
            loss_summary = summarize_loss_components_v0(loss_components)
            loss_tensor = loss_components.get("loss_total_dry")
            blockers.extend(loss_components.get("blocking_reasons", []))
            result["loss_computed"] = loss_components.get("dry_run_status") == "passed"
            result["selected_loss_value"] = float(loss_summary.get("loss_total_dry_scalar", math.nan))
            result["loss_requires_grad"] = bool(loss_summary.get("loss_total_dry_requires_grad"))
            result["loss_finite"] = bool(loss_summary.get("loss_total_dry_finite"))
            result["loss_tensor"] = loss_tensor
            if not result["loss_computed"]:
                blockers.append("masked_loss_not_computed")
            if not result["loss_requires_grad"]:
                blockers.append("selected_loss_does_not_require_grad")
            if not result["loss_finite"]:
                blockers.append("selected_loss_not_finite")
            if not torch.is_tensor(loss_tensor):
                blockers.append("selected_loss_tensor_missing")
    except Exception as exc:
        blockers.append(f"forward_loss_failed:{type(exc).__name__}:{exc}")

    result["status"] = "passed" if not blockers else "blocked"
    result["blocking_reasons"] = sorted(set(blockers))
    return result


def run_real_covalent_backward_smoke_v0(device: str = REQUESTED_DEVICE) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12d_validated = validate_step12d_outputs_v0()
    except Exception as exc:
        step12d_validated = False
        blockers.append(f"step12d_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")

    bundles: dict[str, dict[str, Any]] = {}
    for mask_level in CANONICAL_MASK_LEVELS:
        try:
            bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, device)
        except Exception as exc:
            bundle = {
                "mask_level": mask_level,
                "status": "blocked",
                "blocking_reasons": [f"real_batch_bundle_failed:{type(exc).__name__}:{exc}"],
            }
        bundles[mask_level] = bundle
        blockers.extend(f"{mask_level}:{reason}" for reason in bundle.get("blocking_reasons", []))

    load_bundle = build_strict_loaded_real_size_checkpoint_compatible_model_v0(bundles, device)
    blockers.extend(load_bundle.get("blocking_reasons", []))
    model = load_bundle.get("model")
    level_results: dict[str, dict[str, Any]] = {}
    selected_losses: list[torch.Tensor] = []
    backward_called = False
    backward_call_count = 0
    backward_success = False
    aggregate_loss = None
    grad_stats: dict[str, Any] = {
        "parameter_count": 0,
        "trainable_parameter_count": 0,
        "parameters_with_grad_count": 0,
        "parameters_with_nonzero_grad_count": 0,
        "parameters_with_finite_grad_count": 0,
        "zero_grad_parameter_count": 0,
        "none_grad_parameter_count": 0,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "total_grad_norm": 0.0,
        "max_abs_grad": 0.0,
        "mean_abs_grad": 0.0,
        "finite_nonzero_grad_exists": False,
    }

    if model is not None and load_bundle.get("strict_load_success"):
        model.zero_grad(set_to_none=True)
        for idx, mask_level in enumerate(CANONICAL_MASK_LEVELS):
            bundle = bundles[mask_level]
            if bundle.get("status") != "passed":
                result = {
                    "row_type": "mask_level_loss",
                    "mask_level": mask_level,
                    "expected_reactive_atom_region": expected_reactive_atom_region_for_mask_level_v0(mask_level),
                    "sample_ids": [],
                    "batch_size": BATCH_SIZE,
                    "adapted_valid": False,
                    "model_input_valid": False,
                    "diffsbdd_like_valid": False,
                    "checkpoint_compatible_real_batch_constructed": False,
                    "no_synthetic_fallback_used": False,
                    "model_forward_called": False,
                    "forward_call_count": 0,
                    "loss_computed": False,
                    "selected_loss_key": "masked_loss_total_dry",
                    "selected_loss_value": math.nan,
                    "loss_requires_grad": False,
                    "loss_finite": False,
                    "target_atom_count": 0,
                    "context_atom_count": 0,
                    "status": "blocked",
                    "blocking_reasons": bundle.get("blocking_reasons", []),
                    "loss_tensor": None,
                }
                level_results[mask_level] = result
                continue
            checkpoint_batch = build_checkpoint_compatible_real_model_batch_v0(
                bundle["diffsbdd_like"],
                load_bundle["input_contract"],
                mask_level,
                load_bundle["resolved_device"],
            )
            result = _run_differentiable_forward_loss_for_level(model, checkpoint_batch, mask_level, 7201 + idx)
            result["adapted_valid"] = bundle["adapted_valid"]
            result["model_input_valid"] = bundle["model_input_valid"]
            result["diffsbdd_like_valid"] = bundle["diffsbdd_like_valid"]
            level_results[mask_level] = result
            blockers.extend(f"{mask_level}:{reason}" for reason in result.get("blocking_reasons", []))
            loss_tensor = result.get("loss_tensor")
            if result.get("status") == "passed" and torch.is_tensor(loss_tensor):
                selected_losses.append(loss_tensor.reshape(()))
        if len(selected_losses) == len(CANONICAL_MASK_LEVELS):
            try:
                aggregate_loss = torch.stack(selected_losses).mean()
                if not bool(aggregate_loss.requires_grad):
                    blockers.append("aggregate_loss_does_not_require_grad")
                if not bool(torch.isfinite(aggregate_loss.detach()).all().item()):
                    blockers.append("aggregate_loss_not_finite")
                if not blockers:
                    aggregate_loss.backward()
                    backward_called = True
                    backward_call_count = 1
                    backward_success = True
                    grad_stats = collect_gradient_stats_v0(model)
            except Exception as exc:
                blockers.append(f"aggregate_backward_failed:{type(exc).__name__}:{exc}")
                backward_called = backward_call_count > 0
        else:
            blockers.append("not_all_selected_losses_available")
    else:
        blockers.append("strict_loaded_model_unavailable")
    del model

    return {
        "step12d_validated": step12d_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "load_bundle": {key: value for key, value in load_bundle.items() if key != "model"},
        "bundles": bundles,
        "level_results": level_results,
        "aggregate_loss_reduction": AGGREGATE_LOSS_REDUCTION,
        "aggregate_loss_value": float(aggregate_loss.detach().item()) if torch.is_tensor(aggregate_loss) else math.nan,
        "aggregate_loss_finite": bool(torch.is_tensor(aggregate_loss) and torch.isfinite(aggregate_loss.detach()).all().item()),
        "aggregate_loss_requires_grad": bool(torch.is_tensor(aggregate_loss) and aggregate_loss.requires_grad),
        "backward_called": backward_called,
        "backward_call_count": backward_call_count,
        "backward_exactly_once": backward_call_count == 1,
        "backward_success": backward_success,
        "grad_stats": grad_stats,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }


def build_real_covalent_backward_smoke_v0(device: str = REQUESTED_DEVICE) -> dict[str, Any]:
    run_result = run_real_covalent_backward_smoke_v0(device)
    level_results = run_result["level_results"]
    load_bundle = run_result["load_bundle"]
    grad_stats = run_result["grad_stats"]
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(run_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))

    passed_levels = [level for level, result in level_results.items() if result.get("status") == "passed"]
    failed_levels = [level for level in CANONICAL_MASK_LEVELS if level not in passed_levels]
    all_adapted = bool(level_results and all(result.get("adapted_valid") is True for result in level_results.values()))
    all_model_inputs = bool(level_results and all(result.get("model_input_valid") is True for result in level_results.values()))
    all_diffsbdd = bool(level_results and all(result.get("diffsbdd_like_valid") is True for result in level_results.values()))
    all_checkpoint_batches = bool(
        level_results
        and all(result.get("checkpoint_compatible_real_batch_constructed") is True for result in level_results.values())
    )
    no_synthetic_fallback = bool(
        level_results and all(result.get("no_synthetic_fallback_used") is True for result in level_results.values())
    )
    all_forward_once = bool(
        level_results
        and all(result.get("model_forward_called") is True and result.get("forward_call_count") == 1 for result in level_results.values())
    )
    all_losses_computed = bool(level_results and all(result.get("loss_computed") is True for result in level_results.values()))
    all_losses_finite = bool(level_results and all(result.get("loss_finite") is True for result in level_results.values()))
    all_losses_require_grad = bool(level_results and all(result.get("loss_requires_grad") is True for result in level_results.values()))
    model_forward_count = sum(int(result.get("forward_call_count", 0)) for result in level_results.values())
    smoke_passed = bool(
        run_result["step12d_validated"]
        and run_result["step12b_mask_level_aware_validator_validated"]
        and load_bundle.get("model_instantiated")
        and load_bundle.get("strict_load_success")
        and load_bundle.get("pretrained_weights_loaded")
        and load_bundle.get("pretrained_base_integration_proven")
        and load_bundle.get("model_strict_loaded_once")
        and len(level_results) == len(CANONICAL_MASK_LEVELS)
        and len(passed_levels) == len(CANONICAL_MASK_LEVELS)
        and all_adapted
        and all_model_inputs
        and all_diffsbdd
        and all_checkpoint_batches
        and no_synthetic_fallback
        and model_forward_count == len(CANONICAL_MASK_LEVELS)
        and all_forward_once
        and all_losses_computed
        and all_losses_finite
        and all_losses_require_grad
        and run_result["aggregate_loss_finite"]
        and run_result["aggregate_loss_requires_grad"]
        and run_result["backward_called"]
        and run_result["backward_call_count"] == 1
        and run_result["backward_exactly_once"]
        and run_result["backward_success"]
        and grad_stats.get("finite_nonzero_grad_exists")
        and int(grad_stats.get("grad_nan_count", 0)) == 0
        and int(grad_stats.get("grad_inf_count", 0)) == 0
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12d_validated": run_result["step12d_validated"],
        "step12b_mask_level_aware_validator_validated": run_result["step12b_mask_level_aware_validator_validated"],
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": device,
        "resolved_device": RESOLVED_DEVICE,
        "batch_size": BATCH_SIZE,
        "num_workers": NUM_WORKERS,
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "attempted_mask_level_count": len(level_results),
        "passed_mask_level_count": len(passed_levels),
        "failed_mask_level_count": len(failed_levels),
        "model_instantiated": bool(load_bundle.get("model_instantiated")),
        "strict_load_success": bool(load_bundle.get("strict_load_success")),
        "pretrained_weights_loaded": bool(load_bundle.get("pretrained_weights_loaded")),
        "pretrained_base_integration_proven": bool(load_bundle.get("pretrained_base_integration_proven")),
        "model_strict_loaded_once": bool(load_bundle.get("model_strict_loaded_once")),
        "model_forward_called": model_forward_count > 0,
        "model_forward_call_count": model_forward_count,
        "all_level_forward_call_count_exactly_one": all_forward_once,
        "all_adapted_batches_valid": all_adapted,
        "all_model_inputs_valid": all_model_inputs,
        "all_diffsbdd_like_inputs_valid": all_diffsbdd,
        "all_checkpoint_compatible_real_batches_constructed": all_checkpoint_batches,
        "no_synthetic_fallback_used": no_synthetic_fallback,
        "all_losses_computed": all_losses_computed,
        "all_losses_finite": all_losses_finite,
        "all_losses_require_grad": all_losses_require_grad,
        "selected_loss_key": "masked_loss_total_dry",
        "aggregate_loss_reduction": run_result["aggregate_loss_reduction"],
        "aggregate_loss_value": run_result["aggregate_loss_value"],
        "aggregate_loss_finite": run_result["aggregate_loss_finite"],
        "aggregate_loss_requires_grad": run_result["aggregate_loss_requires_grad"],
        "backward_called": run_result["backward_called"],
        "backward_call_count": run_result["backward_call_count"],
        "backward_exactly_once": run_result["backward_exactly_once"],
        "backward_success": run_result["backward_success"],
        "trainable_parameter_count": int(grad_stats.get("trainable_parameter_count", 0)),
        "parameters_with_grad_count": int(grad_stats.get("parameters_with_grad_count", 0)),
        "parameters_with_nonzero_grad_count": int(grad_stats.get("parameters_with_nonzero_grad_count", 0)),
        "finite_nonzero_gradients": bool(grad_stats.get("finite_nonzero_grad_exists")),
        "total_grad_norm": float(grad_stats.get("total_grad_norm", 0.0)),
        "max_abs_grad": float(grad_stats.get("max_abs_grad", 0.0)),
        "grad_nan_count": int(grad_stats.get("grad_nan_count", 0)),
        "grad_inf_count": int(grad_stats.get("grad_inf_count", 0)),
        "real_covalent_backward_smoke_passed": smoke_passed,
        "real_covalent_backward_contract_proven": smoke_passed,
        "real_covalent_single_optimizer_step_smoke_allowed": smoke_passed,
        "recommended_next_step": "real_covalent_single_optimizer_step_smoke"
        if smoke_passed
        else "real_covalent_backward_smoke_debug",
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": smoke_passed,
        "blocking_reasons": blockers,
    }

    grad_table_rows: list[dict[str, Any]] = []
    for level in CANONICAL_MASK_LEVELS:
        result = level_results.get(level, {"mask_level": level, "status": "blocked", "blocking_reasons": ["not_attempted"]})
        grad_table_rows.append(
            {
                "row_type": "mask_level_loss",
                "mask_level": level,
                "expected_reactive_atom_region": result.get(
                    "expected_reactive_atom_region", expected_reactive_atom_region_for_mask_level_v0(level)
                ),
                "sample_ids": result.get("sample_ids", []),
                "batch_size": result.get("batch_size", BATCH_SIZE),
                "adapted_valid": result.get("adapted_valid", False),
                "model_input_valid": result.get("model_input_valid", False),
                "diffsbdd_like_valid": result.get("diffsbdd_like_valid", False),
                "checkpoint_compatible_real_batch_constructed": result.get(
                    "checkpoint_compatible_real_batch_constructed", False
                ),
                "no_synthetic_fallback_used": result.get("no_synthetic_fallback_used", False),
                "model_forward_called": result.get("model_forward_called", False),
                "forward_call_count": result.get("forward_call_count", 0),
                "loss_computed": result.get("loss_computed", False),
                "selected_loss_key": result.get("selected_loss_key", "masked_loss_total_dry"),
                "selected_loss_value": result.get("selected_loss_value", ""),
                "loss_requires_grad": result.get("loss_requires_grad", False),
                "loss_finite": result.get("loss_finite", False),
                "target_atom_count": result.get("target_atom_count", 0),
                "context_atom_count": result.get("context_atom_count", 0),
                "aggregate_loss_reduction": "",
                "aggregate_loss_value": "",
                "aggregate_loss_requires_grad": "",
                "aggregate_loss_finite": "",
                "backward_called": "",
                "backward_call_count": "",
                "backward_success": "",
                "trainable_parameter_count": "",
                "parameters_with_grad_count": "",
                "parameters_with_nonzero_grad_count": "",
                "finite_nonzero_gradients": "",
                "total_grad_norm": "",
                "max_abs_grad": "",
                "grad_nan_count": "",
                "grad_inf_count": "",
                "status": result.get("status", "blocked"),
                "blocking_reasons": result.get("blocking_reasons", []),
            }
        )
    grad_table_rows.append(
        {
            "row_type": "aggregate_backward",
            "mask_level": "ALL",
            "expected_reactive_atom_region": "",
            "sample_ids": "",
            "batch_size": BATCH_SIZE,
            "adapted_valid": "",
            "model_input_valid": "",
            "diffsbdd_like_valid": "",
            "checkpoint_compatible_real_batch_constructed": "",
            "no_synthetic_fallback_used": no_synthetic_fallback,
            "model_forward_called": "",
            "forward_call_count": "",
            "loss_computed": "",
            "selected_loss_key": "masked_loss_total_dry",
            "selected_loss_value": "",
            "loss_requires_grad": "",
            "loss_finite": "",
            "target_atom_count": "",
            "context_atom_count": "",
            "aggregate_loss_reduction": run_result["aggregate_loss_reduction"],
            "aggregate_loss_value": run_result["aggregate_loss_value"],
            "aggregate_loss_requires_grad": run_result["aggregate_loss_requires_grad"],
            "aggregate_loss_finite": run_result["aggregate_loss_finite"],
            "backward_called": run_result["backward_called"],
            "backward_call_count": run_result["backward_call_count"],
            "backward_success": run_result["backward_success"],
            "trainable_parameter_count": manifest["trainable_parameter_count"],
            "parameters_with_grad_count": manifest["parameters_with_grad_count"],
            "parameters_with_nonzero_grad_count": manifest["parameters_with_nonzero_grad_count"],
            "finite_nonzero_gradients": manifest["finite_nonzero_gradients"],
            "total_grad_norm": manifest["total_grad_norm"],
            "max_abs_grad": manifest["max_abs_grad"],
            "grad_nan_count": manifest["grad_nan_count"],
            "grad_inf_count": manifest["grad_inf_count"],
            "status": "passed" if smoke_passed else "blocked",
            "blocking_reasons": blockers,
        }
    )
    return {
        "manifest": manifest,
        "grad_table_rows": grad_table_rows,
        "run_result": run_result,
        "report_sections": {
            "step12d_precondition": {
                "step12d_validated": run_result["step12d_validated"],
                "step12b_mask_level_aware_validator_validated": run_result[
                    "step12b_mask_level_aware_validator_validated"
                ],
            },
            "real_batch_loading": {
                "input_source": INPUT_SOURCE,
                "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
                "batch_size": BATCH_SIZE,
                "num_workers": NUM_WORKERS,
            },
            "mask_level_aware_model_input": {
                "all_model_inputs_valid": all_model_inputs,
                "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
            },
            "checkpoint_compatible_real_batch": {
                "all_checkpoint_compatible_real_batches_constructed": all_checkpoint_batches,
                "no_synthetic_fallback_used": no_synthetic_fallback,
            },
            "pretrained_strict_load": {
                "model_instantiated": manifest["model_instantiated"],
                "strict_load_success": manifest["strict_load_success"],
                "pretrained_weights_loaded": manifest["pretrained_weights_loaded"],
                "pretrained_base_integration_proven": manifest["pretrained_base_integration_proven"],
                "model_strict_loaded_once": manifest["model_strict_loaded_once"],
            },
            "forward_loss_by_mask_level": {
                "model_forward_call_count": model_forward_count,
                "all_level_forward_call_count_exactly_one": all_forward_once,
                "all_losses_computed": all_losses_computed,
                "all_losses_finite": all_losses_finite,
                "all_losses_require_grad": all_losses_require_grad,
            },
            "aggregate_backward": {
                "aggregate_loss_reduction": manifest["aggregate_loss_reduction"],
                "aggregate_loss_value": manifest["aggregate_loss_value"],
                "aggregate_loss_finite": manifest["aggregate_loss_finite"],
                "aggregate_loss_requires_grad": manifest["aggregate_loss_requires_grad"],
                "backward_called": manifest["backward_called"],
                "backward_call_count": manifest["backward_call_count"],
                "backward_success": manifest["backward_success"],
                "finite_nonzero_gradients": manifest["finite_nonzero_gradients"],
            },
            "safety_boundary": {
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "npz_created": False,
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
            "next_step_decision": {
                "real_covalent_backward_smoke_passed": smoke_passed,
                "real_covalent_single_optimizer_step_smoke_allowed": smoke_passed,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
