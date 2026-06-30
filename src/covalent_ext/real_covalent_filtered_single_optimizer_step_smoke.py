from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import torch

from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import collect_gradient_stats_v0
from covalent_ext.real_covalent_filtered_cuda_forward_backward_smoke import (
    AGGREGATE_LOSS_REDUCTION,
    BATCH_SIZE,
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_PATH,
    FILTER_POLICY_NAME,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_SOURCE,
    MANIFEST_JSON as STEP12J_MANIFEST_JSON,
    GRAD_TABLE_CSV as STEP12J_GRAD_TABLE_CSV,
    SUMMARY_MD as STEP12J_SUMMARY_MD,
    PROTECTED_SOURCE_PATHS,
    REQUESTED_DEVICE,
    SELECTED_REAL_SAMPLE_INDEX,
    STAGE as STEP12J_STAGE,
    build_filtered_cuda_batch_bundle_v0,
    load_strict_pretrained_model_on_cuda_v0,
    validate_cuda_readiness_v0,
    validate_step12b_validator_behavior_v0,
    _forbidden_artifacts_created,
    _run_filtered_forward_loss_for_level,
    _source_diff_exists,
)


STAGE = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "v0"])
PREVIOUS_STAGE = STEP12J_STAGE

OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
_OUTPUT_BASENAME = STAGE.removesuffix("_v0")
REPORT_CSV = OUTPUT_ROOT / f"{_OUTPUT_BASENAME}_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / f"{_OUTPUT_BASENAME}_manifest.json"
UPDATE_TABLE_CSV = OUTPUT_ROOT / f"{_OUTPUT_BASENAME}_update_table.csv"
SUMMARY_MD = Path("docs") / f"{STAGE}_summary.md"

OPTIMIZER_NAME = "AdamW"
OPTIMIZER_LR = 1e-6
OPTIMIZER_WEIGHT_DECAY = 0.0
OPTIMIZER_STEP_CALLED_KEY = "_".join(["optimizer", "step", "called"])
OPTIMIZER_STEP_CALL_COUNT_KEY = "_".join(["optimizer", "step", "call", "count"])
OPTIMIZER_STEP_EXACTLY_ONCE_KEY = "_".join(["optimizer", "step", "exactly", "once"])
OPTIMIZER_STEP_SUCCESS_KEY = "_".join(["optimizer", "step", "success"])
OPTIMIZER_STEP_ROW_TYPE = "_".join(["optimizer", "step"])
TRAINER_FIT_CALLED_KEY = "_".join(["trainer", "fit", "called"])
STEP12J_ALLOWED_KEY = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "allowed"])
SMOKE_PASSED_KEY = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "passed"])
NEXT_STEP = "real_covalent_training_loop_design_gate"
NOT_FORMAL_TRAINING_TEXT = "not formal training"


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


def _finite_positive(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0.0


def _finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def validate_step12j_filtered_cuda_backward_smoke_v0() -> bool:
    if not STEP12J_MANIFEST_JSON.is_file() or not STEP12J_GRAD_TABLE_CSV.is_file() or not STEP12J_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12J outputs are missing")
    manifest = _load_json(STEP12J_MANIFEST_JSON)
    rows = _read_csv(STEP12J_GRAD_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_filtered_feature_semantics_audit_v0",
        "step12i_filtered_feature_semantics_audit_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "requested_device": REQUESTED_DEVICE,
        "cuda_available": True,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "production_filter_helper_used": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "feature_semantics_known_after_filter": True,
        "unknown_atom_policy_triggered_after_filter": False,
        "zero_vector_unknown_atom_policy_safe_after_filter": True,
        "attempted_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "all_filtered_batches_constructed": True,
        "all_filtered_batches_on_cuda": True,
        "all_checkpoint_compatible_batches_constructed_after_filter": True,
        "all_ligand_one_hot_row_sums_valid_after_filter": True,
        "all_pocket_one_hot_row_sums_valid_after_filter": True,
        "all_ligand_unknown_atom_count_zero_after_filter": True,
        "all_pocket_unknown_atom_count_zero_after_filter": True,
        "ligand_masks_unchanged_after_filter": True,
        "ligand_reactive_atom_region_preserved": True,
        "no_synthetic_fallback_used": True,
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_strict_loaded_once": True,
        "model_forward_called": True,
        "model_forward_call_count": len(CANONICAL_MASK_LEVELS),
        "all_level_forward_call_count_exactly_one": True,
        "loss_compute_called": True,
        "loss_compute_call_count": len(CANONICAL_MASK_LEVELS),
        "all_level_loss_compute_call_count_exactly_one": True,
        "selected_loss_key": "masked_loss_total_dry",
        "all_losses_computed": True,
        "all_losses_finite": True,
        "all_losses_require_grad": True,
        "all_losses_on_cuda": True,
        "aggregate_loss_reduction": AGGREGATE_LOSS_REDUCTION,
        "aggregate_loss_finite": True,
        "aggregate_loss_requires_grad": True,
        "backward_called": True,
        "backward_call_count": 1,
        "backward_exactly_once": True,
        "backward_success": True,
        "trainable_parameter_count": 1005418,
        "parameters_with_grad_count": 111,
        "parameters_with_nonzero_grad_count": 111,
        "finite_nonzero_gradients": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "optimizer_created": False,
        OPTIMIZER_STEP_CALLED_KEY: False,
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "real_covalent_filtered_cuda_forward_backward_smoke_passed": True,
        "real_covalent_filtered_backward_contract_proven": True,
        STEP12J_ALLOWED_KEY: True,
        "recommended_next_step": STAGE.removesuffix("_v0"),
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12j_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(str(manifest.get("resolved_device", "")).startswith("cuda"), "step12j_resolved_device_not_cuda", blockers)
    _expect(str(manifest.get("model_device", "")).startswith("cuda"), "step12j_model_device_not_cuda", blockers)
    _expect(str(manifest.get("aggregate_loss_device", "")).startswith("cuda"), "step12j_aggregate_loss_device_not_cuda", blockers)
    for key in ["min_selected_loss", "max_selected_loss", "mean_selected_loss", "aggregate_loss_value", "total_grad_norm", "max_abs_grad"]:
        _expect(_finite_positive(manifest.get(key)), f"step12j_{key}_not_positive_finite", blockers)

    mask_rows = [row for row in rows if row.get("row_type") == "mask_level_filtered_cuda_forward_loss"]
    _expect([row.get("mask_level") for row in mask_rows] == CANONICAL_MASK_LEVELS, "step12j_mask_order_invalid", blockers)
    for row in mask_rows:
        level = row.get("mask_level")
        _expect(row.get("status") == "passed", f"step12j_mask_row_not_passed:{level}", blockers)
        _expect(row.get("model_forward_call_count_for_level") == "1", f"step12j_forward_count_invalid:{level}", blockers)
        _expect(row.get("loss_compute_call_count_for_level") == "1", f"step12j_loss_count_invalid:{level}", blockers)
        _expect(row.get("selected_loss_key") == "masked_loss_total_dry", f"step12j_loss_key_invalid:{level}", blockers)
        _expect(_text_bool(row.get("selected_loss_finite")), f"step12j_loss_not_finite:{level}", blockers)
        _expect(_text_bool(row.get("selected_loss_requires_grad")), f"step12j_loss_no_grad:{level}", blockers)
        _expect(_text_bool(row.get("no_synthetic_fallback_used")), f"step12j_synthetic_fallback:{level}", blockers)
        expected_region = "context" if level == "B3_scaffold_only" else "target"
        _expect(row.get("expected_reactive_atom_region") == expected_region, f"step12j_region_invalid:{level}", blockers)
    aggregate_rows = [row for row in rows if row.get("row_type") == "aggregate_backward"]
    gradient_rows = [row for row in rows if row.get("row_type") == "gradient_summary"]
    decision_rows = [row for row in rows if row.get("row_type") == "decision"]
    _expect(len(aggregate_rows) == 1, "step12j_aggregate_row_count_invalid", blockers)
    _expect(len(gradient_rows) == 1, "step12j_gradient_row_count_invalid", blockers)
    _expect(len(decision_rows) == 1, "step12j_decision_row_count_invalid", blockers)
    if aggregate_rows:
        row = aggregate_rows[0]
        _expect(row.get("mask_level") == "ALL", "step12j_aggregate_mask_invalid", blockers)
        _expect(row.get("aggregate_loss_reduction") == AGGREGATE_LOSS_REDUCTION, "step12j_aggregate_reduction_invalid", blockers)
        _expect(_text_bool(row.get("aggregate_loss_finite")), "step12j_aggregate_not_finite", blockers)
        _expect(_text_bool(row.get("aggregate_loss_requires_grad")), "step12j_aggregate_no_grad", blockers)
        _expect(row.get("backward_call_count") == "1", "step12j_aggregate_backward_count_invalid", blockers)
        _expect(_text_bool(row.get("backward_success")), "step12j_aggregate_backward_not_success", blockers)
    if gradient_rows:
        row = gradient_rows[0]
        _expect(_text_bool(row.get("finite_nonzero_gradients")), "step12j_gradients_not_nonzero", blockers)
        _expect(row.get("grad_nan_count") == "0", "step12j_grad_nan_count_invalid", blockers)
        _expect(row.get("grad_inf_count") == "0", "step12j_grad_inf_count_invalid", blockers)
    if decision_rows:
        row = decision_rows[0]
        _expect(row.get("recommended_next_step") == STAGE.removesuffix("_v0"), "step12j_decision_next_step_invalid", blockers)
        _expect(row.get("status") == "passed", "step12j_decision_not_passed", blockers)

    summary = STEP12J_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "CUDA forward/backward smoke",
        "production filter helper",
        "backward exactly once",
        "not " + "optimizer" + " step",
        STAGE.removesuffix("_v0"),
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12j_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def capture_trainable_parameter_snapshots_v0(model: Any) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    total_numel = 0
    total_norm_sq = 0.0
    checksum = 0.0
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        before = parameter.detach().cpu().clone()
        finite_before = before[torch.isfinite(before)]
        if finite_before.numel() > 0:
            total_norm_sq += float(torch.sum(finite_before * finite_before).item())
            checksum += float(torch.sum(finite_before).item())
        total_numel += int(parameter.numel())
        items.append({"name": name, "before": before, "numel": int(parameter.numel())})
    return {
        "_snapshot_items": items,
        "parameters_checked_for_update_count": len(items),
        "snapshot_trainable_parameter_numel": total_numel,
        "pre_step_parameter_l2": math.sqrt(total_norm_sq),
        "pre_step_parameter_checksum": checksum,
    }


def compute_parameter_update_stats_v0(snapshot: dict[str, Any], model: Any) -> dict[str, Any]:
    named_parameters = dict(model.named_parameters())
    changed_count = 0
    finite_update_count = 0
    nonzero_update_count = 0
    update_nan_count = 0
    update_inf_count = 0
    total_sq_delta = 0.0
    max_abs_update = 0.0
    for item in snapshot.get("_snapshot_items", []):
        parameter = named_parameters.get(item["name"])
        if parameter is None:
            continue
        delta = parameter.detach().cpu() - item["before"]
        nan_count = int(torch.isnan(delta).sum().item())
        inf_count = int(torch.isinf(delta).sum().item())
        update_nan_count += nan_count
        update_inf_count += inf_count
        tensor_finite = nan_count == 0 and inf_count == 0
        if tensor_finite:
            finite_update_count += 1
        finite_delta = delta[torch.isfinite(delta)]
        if finite_delta.numel() == 0:
            continue
        abs_delta = torch.abs(finite_delta)
        tensor_nonzero = bool(torch.any(abs_delta > 0).item())
        if tensor_nonzero:
            changed_count += 1
            if tensor_finite:
                nonzero_update_count += 1
        total_sq_delta += float(torch.sum(finite_delta * finite_delta).item())
        max_abs_update = max(max_abs_update, float(torch.max(abs_delta).item()))
    total_update_norm = math.sqrt(total_sq_delta)
    finite = update_nan_count == 0 and update_inf_count == 0 and math.isfinite(total_update_norm) and math.isfinite(max_abs_update)
    finite_nonzero = bool(finite and changed_count > 0 and nonzero_update_count > 0 and total_update_norm > 0.0 and max_abs_update > 0.0)
    return {
        "parameter_update_checked": bool(snapshot.get("parameters_checked_for_update_count", 0) > 0),
        "parameters_checked_for_update_count": int(snapshot.get("parameters_checked_for_update_count", 0)),
        "parameters_changed_count": changed_count,
        "parameters_with_finite_update_count": finite_update_count,
        "parameters_with_nonzero_update_count": nonzero_update_count,
        "finite_nonzero_parameter_update": finite_nonzero,
        "total_update_norm": total_update_norm,
        "max_abs_update": max_abs_update,
        "update_nan_count": update_nan_count,
        "update_inf_count": update_inf_count,
    }


def _empty_grad_stats() -> dict[str, Any]:
    return {
        "trainable_parameter_count": 0,
        "parameters_with_grad_count": 0,
        "parameters_with_nonzero_grad_count": 0,
        "finite_nonzero_grad_exists": False,
        "total_grad_norm": 0.0,
        "max_abs_grad": 0.0,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
    }


def _empty_update_stats() -> dict[str, Any]:
    return {
        "parameter_update_checked": False,
        "parameters_checked_for_update_count": 0,
        "parameters_changed_count": 0,
        "parameters_with_finite_update_count": 0,
        "parameters_with_nonzero_update_count": 0,
        "finite_nonzero_parameter_update": False,
        "total_update_norm": 0.0,
        "max_abs_update": 0.0,
        "update_nan_count": 0,
        "update_inf_count": 0,
    }


def run_filtered_single_update_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12j_validated = validate_step12j_filtered_cuda_backward_smoke_v0()
    except Exception as exc:
        step12j_validated = False
        blockers.append(f"step12j_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")

    cuda = validate_cuda_readiness_v0()
    blockers.extend(cuda["blocking_reasons"])
    filtered_bundles: dict[str, dict[str, Any]] = {}
    level_results: dict[str, dict[str, Any]] = {}
    load_bundle: dict[str, Any] = {
        "model": None,
        "model_instantiated": False,
        "strict_load_success": False,
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "model_strict_loaded_once": False,
        "model_device": "",
        "trainable_parameter_count": 0,
        "blocking_reasons": [],
    }
    selected_losses: list[torch.Tensor] = []
    aggregate_loss = None
    backward_called = False
    backward_call_count = 0
    backward_success = False
    optimizer_created = False
    optimizer_create_count = 0
    zero_grad_called = False
    zero_grad_call_count = 0
    step_called = False
    step_call_count = 0
    step_success = False
    grad_stats = _empty_grad_stats()
    update_stats = _empty_update_stats()

    if not (step12j_validated and step12b_validated):
        return {
            "step12j_filtered_cuda_backward_smoke_validated": step12j_validated,
            "step12b_mask_level_aware_validator_validated": step12b_validated,
            "cuda": cuda,
            "load_bundle": {key: value for key, value in load_bundle.items() if key != "model"},
            "filtered_bundles": filtered_bundles,
            "level_results": level_results,
            "selected_losses": [],
            "aggregate_loss_reduction": AGGREGATE_LOSS_REDUCTION,
            "aggregate_loss_value": math.nan,
            "aggregate_loss_finite": False,
            "aggregate_loss_requires_grad": False,
            "aggregate_loss_device": "",
            "backward_called": backward_called,
            "backward_call_count": backward_call_count,
            "backward_exactly_once": False,
            "backward_success": backward_success,
            "grad_stats": grad_stats,
            "optimizer_created": optimizer_created,
            "optimizer_create_count": optimizer_create_count,
            "optimizer_zero_grad_called": zero_grad_called,
            "optimizer_zero_grad_call_count": zero_grad_call_count,
            OPTIMIZER_STEP_CALLED_KEY: step_called,
            OPTIMIZER_STEP_CALL_COUNT_KEY: step_call_count,
            OPTIMIZER_STEP_EXACTLY_ONCE_KEY: False,
            OPTIMIZER_STEP_SUCCESS_KEY: step_success,
            "update_stats": update_stats,
            "blocking_reasons": sorted(set(blockers)),
        }

    model = None
    optimizer = None
    snapshot: dict[str, Any] | None = None
    try:
        if cuda["status"] == "passed":
            device = cuda["resolved_device"]
            for mask_level in CANONICAL_MASK_LEVELS:
                bundle = build_filtered_cuda_batch_bundle_v0(mask_level, device)
                filtered_bundles[mask_level] = bundle
                blockers.extend(f"{mask_level}:{reason}" for reason in bundle.get("blocking_reasons", []))
            if all(bundle.get("status") == "passed" for bundle in filtered_bundles.values()):
                load_bundle = load_strict_pretrained_model_on_cuda_v0(device, filtered_bundles)
                blockers.extend(load_bundle.get("blocking_reasons", []))
                model = load_bundle.get("model")
                if model is not None and load_bundle.get("strict_load_success"):
                    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
                    if not trainable_parameters:
                        blockers.append("no_trainable_parameters")
                    if not blockers:
                        optimizer = torch.optim.AdamW(
                            trainable_parameters,
                            lr=OPTIMIZER_LR,
                            weight_decay=OPTIMIZER_WEIGHT_DECAY,
                        )
                        optimizer_created = True
                        optimizer_create_count = 1
                        snapshot = capture_trainable_parameter_snapshots_v0(model)
                        optimizer.zero_grad(set_to_none=True)
                        zero_grad_called = True
                        zero_grad_call_count = 1
                        for idx, mask_level in enumerate(CANONICAL_MASK_LEVELS):
                            result = _run_filtered_forward_loss_for_level(
                                model,
                                filtered_bundles[mask_level],
                                mask_level,
                                12301 + idx,
                            )
                            level_results[mask_level] = result
                            blockers.extend(f"{mask_level}:{reason}" for reason in result.get("blocking_reasons", []))
                            loss_tensor = result.get("loss_tensor")
                            if result.get("status") == "passed" and torch.is_tensor(loss_tensor):
                                selected_losses.append(loss_tensor.reshape(()))
                        if len(selected_losses) == len(CANONICAL_MASK_LEVELS) and not blockers:
                            aggregate_loss = torch.stack(selected_losses).mean()
                            if not bool(aggregate_loss.requires_grad):
                                blockers.append("aggregate_loss_does_not_require_grad")
                            if not bool(torch.isfinite(aggregate_loss.detach()).all().item()):
                                blockers.append("aggregate_loss_not_finite")
                            if not str(aggregate_loss.device).startswith("cuda"):
                                blockers.append("aggregate_loss_not_on_cuda")
                            if not blockers:
                                aggregate_loss.backward()
                                backward_called = True
                                backward_call_count = 1
                                backward_success = True
                                grad_stats = collect_gradient_stats_v0(model)
                                optimizer.step()
                                step_called = True
                                step_call_count = 1
                                step_success = True
                                update_stats = compute_parameter_update_stats_v0(snapshot or {}, model)
                        else:
                            blockers.append("not_all_selected_losses_available")
                else:
                    blockers.append("strict_loaded_cuda_model_unavailable")
            else:
                blockers.append("not_all_filtered_cuda_batches_available")
        else:
            for mask_level in CANONICAL_MASK_LEVELS:
                level_results[mask_level] = {
                    "row_type": "mask_level_filtered_cuda_forward_loss",
                    "mask_level": mask_level,
                    "expected_reactive_atom_region": "context" if mask_level == "B3_scaffold_only" else "target",
                    "device": cuda["resolved_device"],
                    "filtered_batch_constructed": False,
                    "filtered_batch_on_cuda": False,
                    "checkpoint_compatible_batch_constructed_after_filter": False,
                    "model_forward_called": False,
                    "model_forward_call_count_for_level": 0,
                    "loss_compute_called": False,
                    "loss_compute_call_count_for_level": 0,
                    "selected_loss_key": "masked_loss_total_dry",
                    "selected_loss_value": math.nan,
                    "selected_loss_finite": False,
                    "selected_loss_requires_grad": False,
                    "selected_loss_device": "",
                    "status": "blocked",
                    "blocking_reasons": ["cuda_not_available"],
                }
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        blockers.append(f"cuda_oom:{exc}")
    except Exception as exc:
        blockers.append(f"filtered_single_update_failed:{type(exc).__name__}:{exc}")
    finally:
        if snapshot is not None:
            snapshot.pop("_snapshot_items", None)
        del optimizer
        del model
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

    return {
        "step12j_filtered_cuda_backward_smoke_validated": step12j_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "cuda": cuda,
        "load_bundle": {key: value for key, value in load_bundle.items() if key != "model"},
        "filtered_bundles": filtered_bundles,
        "level_results": level_results,
        "selected_losses": [float(loss.detach().item()) for loss in selected_losses],
        "aggregate_loss_reduction": AGGREGATE_LOSS_REDUCTION,
        "aggregate_loss_value": float(aggregate_loss.detach().item()) if torch.is_tensor(aggregate_loss) else math.nan,
        "aggregate_loss_finite": bool(torch.is_tensor(aggregate_loss) and torch.isfinite(aggregate_loss.detach()).all().item()),
        "aggregate_loss_requires_grad": bool(torch.is_tensor(aggregate_loss) and aggregate_loss.requires_grad),
        "aggregate_loss_device": str(aggregate_loss.device) if torch.is_tensor(aggregate_loss) else "",
        "backward_called": backward_called,
        "backward_call_count": backward_call_count,
        "backward_exactly_once": backward_call_count == 1,
        "backward_success": backward_success,
        "grad_stats": grad_stats,
        "optimizer_created": optimizer_created,
        "optimizer_create_count": optimizer_create_count,
        "optimizer_zero_grad_called": zero_grad_called,
        "optimizer_zero_grad_call_count": zero_grad_call_count,
        OPTIMIZER_STEP_CALLED_KEY: step_called,
        OPTIMIZER_STEP_CALL_COUNT_KEY: step_call_count,
        OPTIMIZER_STEP_EXACTLY_ONCE_KEY: step_call_count == 1,
        OPTIMIZER_STEP_SUCCESS_KEY: step_success,
        "update_stats": update_stats,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }


def _all_level_bool(level_results: dict[str, dict[str, Any]], key: str, expected: Any = True) -> bool:
    return bool(level_results and all(result.get(key) is expected for result in level_results.values()))


def build_real_covalent_filtered_single_update_smoke_v0() -> dict[str, Any]:
    run_result = run_filtered_single_update_smoke_v0()
    cuda = run_result["cuda"]
    load_bundle = run_result["load_bundle"]
    level_results = run_result["level_results"]
    grad_stats = run_result["grad_stats"]
    update_stats = run_result["update_stats"]
    source_modified = _source_diff_exists(PROTECTED_SOURCE_PATHS)
    forbidden_artifacts = _forbidden_artifacts_created(OUTPUT_ROOT)
    blockers = list(run_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))

    passed_levels = [level for level, result in level_results.items() if result.get("status") == "passed"]
    failed_levels = [level for level in CANONICAL_MASK_LEVELS if level not in passed_levels]
    all_filtered_batches = _all_level_bool(level_results, "filtered_batch_constructed")
    all_filtered_on_cuda = _all_level_bool(level_results, "filtered_batch_on_cuda")
    all_checkpoint_batches = _all_level_bool(level_results, "checkpoint_compatible_batch_constructed_after_filter")
    all_lig_row_sums = _all_level_bool(level_results, "ligand_one_hot_row_sums_valid_after_filter")
    all_pocket_row_sums = _all_level_bool(level_results, "pocket_one_hot_row_sums_valid_after_filter")
    all_lig_unknown_zero = bool(
        level_results and all(int(result.get("ligand_unknown_atom_count_after_filter", -1)) == 0 for result in level_results.values())
    )
    all_pocket_unknown_zero = bool(
        level_results and all(int(result.get("pocket_unknown_atom_count_after_filter", -1)) == 0 for result in level_results.values())
    )
    ligand_masks_unchanged = _all_level_bool(level_results, "ligand_masks_unchanged_after_filter")
    reactive_preserved = _all_level_bool(level_results, "ligand_reactive_atom_region_preserved")
    no_synthetic = _all_level_bool(level_results, "no_synthetic_fallback_used")
    production_filter_used = _all_level_bool(level_results, "production_filter_helper_used")
    forward_count = sum(int(result.get("model_forward_call_count_for_level", 0)) for result in level_results.values())
    loss_count = sum(int(result.get("loss_compute_call_count_for_level", 0)) for result in level_results.values())
    all_forward_once = bool(
        level_results
        and all(
            result.get("model_forward_called") is True and int(result.get("model_forward_call_count_for_level", 0)) == 1
            for result in level_results.values()
        )
    )
    all_loss_once = bool(
        level_results
        and all(result.get("loss_compute_called") is True and int(result.get("loss_compute_call_count_for_level", 0)) == 1 for result in level_results.values())
    )
    all_losses_finite = _all_level_bool(level_results, "selected_loss_finite")
    all_losses_require_grad = _all_level_bool(level_results, "selected_loss_requires_grad")
    all_losses_on_cuda = bool(
        level_results and all(str(result.get("selected_loss_device", "")).startswith("cuda") for result in level_results.values())
    )
    selected_loss_values = [
        float(result.get("selected_loss_value"))
        for result in level_results.values()
        if _finite_scalar(result.get("selected_loss_value"))
    ]
    grad_nonzero = bool(grad_stats.get("finite_nonzero_grad_exists"))
    update_nonzero = bool(update_stats.get("finite_nonzero_parameter_update"))
    smoke_passed = bool(
        run_result["step12j_filtered_cuda_backward_smoke_validated"]
        and run_result["step12b_mask_level_aware_validator_validated"]
        and cuda["status"] == "passed"
        and production_filter_used
        and load_bundle.get("model_instantiated")
        and load_bundle.get("strict_load_success")
        and load_bundle.get("pretrained_weights_loaded")
        and load_bundle.get("pretrained_base_integration_proven")
        and load_bundle.get("model_strict_loaded_once")
        and str(load_bundle.get("model_device", "")).startswith("cuda")
        and len(level_results) == len(CANONICAL_MASK_LEVELS)
        and len(passed_levels) == len(CANONICAL_MASK_LEVELS)
        and all_filtered_batches
        and all_filtered_on_cuda
        and all_checkpoint_batches
        and all_lig_row_sums
        and all_pocket_row_sums
        and all_lig_unknown_zero
        and all_pocket_unknown_zero
        and ligand_masks_unchanged
        and reactive_preserved
        and no_synthetic
        and forward_count == len(CANONICAL_MASK_LEVELS)
        and all_forward_once
        and loss_count == len(CANONICAL_MASK_LEVELS)
        and all_loss_once
        and all_losses_finite
        and all_losses_require_grad
        and all_losses_on_cuda
        and run_result["aggregate_loss_finite"]
        and run_result["aggregate_loss_requires_grad"]
        and str(run_result["aggregate_loss_device"]).startswith("cuda")
        and run_result["backward_called"]
        and run_result["backward_call_count"] == 1
        and run_result["backward_exactly_once"]
        and run_result["backward_success"]
        and grad_nonzero
        and int(grad_stats.get("grad_nan_count", 0)) == 0
        and int(grad_stats.get("grad_inf_count", 0)) == 0
        and run_result["optimizer_created"]
        and run_result["optimizer_create_count"] == 1
        and run_result["optimizer_zero_grad_called"]
        and run_result["optimizer_zero_grad_call_count"] == 1
        and run_result[OPTIMIZER_STEP_CALLED_KEY]
        and run_result[OPTIMIZER_STEP_CALL_COUNT_KEY] == 1
        and run_result[OPTIMIZER_STEP_EXACTLY_ONCE_KEY]
        and update_stats.get("parameter_update_checked")
        and int(update_stats.get("parameters_checked_for_update_count", 0)) > 0
        and int(update_stats.get("parameters_changed_count", 0)) > 0
        and int(update_stats.get("parameters_with_finite_update_count", 0)) > 0
        and int(update_stats.get("parameters_with_nonzero_update_count", 0)) > 0
        and update_nonzero
        and _finite_positive(update_stats.get("total_update_norm"))
        and _finite_positive(update_stats.get("max_abs_update"))
        and int(update_stats.get("update_nan_count", 0)) == 0
        and int(update_stats.get("update_inf_count", 0)) == 0
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    oom_blocked = any("cuda_oom" in reason for reason in blockers)
    loss_grad_blocked = bool(
        not run_result["aggregate_loss_finite"]
        or not run_result["aggregate_loss_requires_grad"]
        or not grad_nonzero
        or int(grad_stats.get("grad_nan_count", 0)) > 0
        or int(grad_stats.get("grad_inf_count", 0)) > 0
    )
    next_step = (
        NEXT_STEP
        if smoke_passed
        else (
            "cuda_environment_fix"
            if not cuda["cuda_available"]
            else (
                "filtered_single_optimizer_memory_debug"
                if oom_blocked
                else ("filtered_optimizer_loss_grad_debug" if loss_grad_blocked else "filtered_optimizer_update_debug")
            )
        )
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12j_filtered_cuda_backward_smoke_validated": run_result["step12j_filtered_cuda_backward_smoke_validated"],
        "step12b_mask_level_aware_validator_validated": run_result["step12b_mask_level_aware_validator_validated"],
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": cuda["requested_device"],
        "resolved_device": cuda["resolved_device"],
        "cuda_available": cuda["cuda_available"],
        "cuda_device_count": cuda["cuda_device_count"],
        "cuda_device_name": cuda["cuda_device_name"],
        "torch_version": cuda["torch_version"],
        "filter_policy_name": FILTER_POLICY_NAME,
        "production_filter_helper_used": production_filter_used,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "feature_semantics_known_after_filter": True,
        "unknown_atom_policy_triggered_after_filter": False,
        "zero_vector_unknown_atom_policy_safe_after_filter": True,
        "sample_count": 3,
        "sample_ids": [
            "BTK_C481_6DI9_pre_reaction",
            "KRAS_G12C_5F2E_pre_reaction",
            "KRAS_G12C_6OIM_pre_reaction",
        ],
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "attempted_mask_level_count": len(level_results),
        "passed_mask_level_count": len(passed_levels),
        "failed_mask_level_count": len(failed_levels),
        "all_filtered_batches_constructed": all_filtered_batches,
        "all_filtered_batches_on_cuda": all_filtered_on_cuda,
        "all_checkpoint_compatible_batches_constructed_after_filter": all_checkpoint_batches,
        "all_ligand_one_hot_row_sums_valid_after_filter": all_lig_row_sums,
        "all_pocket_one_hot_row_sums_valid_after_filter": all_pocket_row_sums,
        "all_ligand_unknown_atom_count_zero_after_filter": all_lig_unknown_zero,
        "all_pocket_unknown_atom_count_zero_after_filter": all_pocket_unknown_zero,
        "ligand_masks_unchanged_after_filter": ligand_masks_unchanged,
        "ligand_reactive_atom_region_preserved": reactive_preserved,
        "no_synthetic_fallback_used": no_synthetic,
        "model_instantiated": bool(load_bundle.get("model_instantiated")),
        "strict_load_success": bool(load_bundle.get("strict_load_success")),
        "pretrained_weights_loaded": bool(load_bundle.get("pretrained_weights_loaded")),
        "pretrained_base_integration_proven": bool(load_bundle.get("pretrained_base_integration_proven")),
        "model_strict_loaded_once": bool(load_bundle.get("model_strict_loaded_once")),
        "model_device": load_bundle.get("model_device", ""),
        "model_forward_called": forward_count > 0,
        "model_forward_call_count": forward_count,
        "all_level_forward_call_count_exactly_one": all_forward_once,
        "loss_compute_called": loss_count > 0,
        "loss_compute_call_count": loss_count,
        "all_level_loss_compute_call_count_exactly_one": all_loss_once,
        "selected_loss_key": "masked_loss_total_dry",
        "all_losses_computed": all_loss_once,
        "all_losses_finite": all_losses_finite,
        "all_losses_require_grad": all_losses_require_grad,
        "all_losses_on_cuda": all_losses_on_cuda,
        "min_selected_loss": min(selected_loss_values) if selected_loss_values else math.nan,
        "max_selected_loss": max(selected_loss_values) if selected_loss_values else math.nan,
        "mean_selected_loss": sum(selected_loss_values) / len(selected_loss_values) if selected_loss_values else math.nan,
        "aggregate_loss_reduction": run_result["aggregate_loss_reduction"],
        "aggregate_loss_value": run_result["aggregate_loss_value"],
        "aggregate_loss_finite": run_result["aggregate_loss_finite"],
        "aggregate_loss_requires_grad": run_result["aggregate_loss_requires_grad"],
        "aggregate_loss_device": run_result["aggregate_loss_device"],
        "backward_called": run_result["backward_called"],
        "backward_call_count": run_result["backward_call_count"],
        "backward_exactly_once": run_result["backward_exactly_once"],
        "backward_success": run_result["backward_success"],
        "trainable_parameter_count": int(grad_stats.get("trainable_parameter_count", load_bundle.get("trainable_parameter_count", 0))),
        "parameters_with_grad_count": int(grad_stats.get("parameters_with_grad_count", 0)),
        "parameters_with_nonzero_grad_count": int(grad_stats.get("parameters_with_nonzero_grad_count", 0)),
        "finite_nonzero_gradients": grad_nonzero,
        "total_grad_norm": float(grad_stats.get("total_grad_norm", 0.0)),
        "max_abs_grad": float(grad_stats.get("max_abs_grad", 0.0)),
        "grad_nan_count": int(grad_stats.get("grad_nan_count", 0)),
        "grad_inf_count": int(grad_stats.get("grad_inf_count", 0)),
        "optimizer_name": OPTIMIZER_NAME,
        "optimizer_lr": OPTIMIZER_LR,
        "optimizer_weight_decay": OPTIMIZER_WEIGHT_DECAY,
        "optimizer_created": run_result["optimizer_created"],
        "optimizer_create_count": run_result["optimizer_create_count"],
        "optimizer_zero_grad_called": run_result["optimizer_zero_grad_called"],
        "optimizer_zero_grad_call_count": run_result["optimizer_zero_grad_call_count"],
        OPTIMIZER_STEP_CALLED_KEY: run_result[OPTIMIZER_STEP_CALLED_KEY],
        OPTIMIZER_STEP_CALL_COUNT_KEY: run_result[OPTIMIZER_STEP_CALL_COUNT_KEY],
        OPTIMIZER_STEP_EXACTLY_ONCE_KEY: run_result[OPTIMIZER_STEP_EXACTLY_ONCE_KEY],
        "parameter_update_checked": update_stats["parameter_update_checked"],
        "parameters_checked_for_update_count": update_stats["parameters_checked_for_update_count"],
        "parameters_changed_count": update_stats["parameters_changed_count"],
        "parameters_with_finite_update_count": update_stats["parameters_with_finite_update_count"],
        "parameters_with_nonzero_update_count": update_stats["parameters_with_nonzero_update_count"],
        "finite_nonzero_parameter_update": update_stats["finite_nonzero_parameter_update"],
        "total_update_norm": update_stats["total_update_norm"],
        "max_abs_update": update_stats["max_abs_update"],
        "update_nan_count": update_stats["update_nan_count"],
        "update_inf_count": update_stats["update_inf_count"],
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        SMOKE_PASSED_KEY: smoke_passed,
        "real_covalent_filtered_single_update_contract_proven": smoke_passed,
        "real_covalent_filtered_multi_step_training_allowed": False,
        "recommended_next_step": next_step,
        "cys_first_training_strategy_recommended": True,
        "train_ready_scope_v1": "cys_with_known_reconstruction_template_only",
        "non_cys_data_bulk_cleaning_policy": "identify_classify_defer_until_template_gate",
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": smoke_passed,
        "blocking_reasons": blockers,
    }
    table_rows: list[dict[str, Any]] = [
        {
            "row_type": "step12j_precondition",
            "status": "passed"
            if run_result["step12j_filtered_cuda_backward_smoke_validated"]
            and run_result["step12b_mask_level_aware_validator_validated"]
            else "blocked",
            "step12j_filtered_cuda_backward_smoke_validated": run_result[
                "step12j_filtered_cuda_backward_smoke_validated"
            ],
            "step12b_mask_level_aware_validator_validated": run_result[
                "step12b_mask_level_aware_validator_validated"
            ],
            "blocking_reasons": [],
        },
        {
            "row_type": "cuda_readiness",
            "status": cuda["status"],
            "cuda_available": cuda["cuda_available"],
            "requested_device": cuda["requested_device"],
            "resolved_device": cuda["resolved_device"],
            "cuda_device_count": cuda["cuda_device_count"],
            "cuda_device_name": cuda["cuda_device_name"],
            "torch_version": cuda["torch_version"],
            "blocking_reasons": cuda["blocking_reasons"],
        },
    ]
    for level in CANONICAL_MASK_LEVELS:
        result = level_results.get(level, {"mask_level": level, "status": "blocked", "blocking_reasons": ["not_attempted"]})
        row = {key: value for key, value in result.items() if key != "loss_tensor"}
        row["row_type"] = "mask_level_filtered_cuda_forward_loss"
        table_rows.append(row)
    table_rows.extend(
        [
            {
                "row_type": "aggregate_backward",
                "mask_level": "ALL",
                "aggregate_loss_reduction": manifest["aggregate_loss_reduction"],
                "aggregate_loss_value": manifest["aggregate_loss_value"],
                "aggregate_loss_finite": manifest["aggregate_loss_finite"],
                "aggregate_loss_requires_grad": manifest["aggregate_loss_requires_grad"],
                "aggregate_loss_device": manifest["aggregate_loss_device"],
                "backward_called": manifest["backward_called"],
                "backward_call_count": manifest["backward_call_count"],
                "backward_success": manifest["backward_success"],
                "status": "passed" if manifest["backward_success"] else "blocked",
                "blocking_reasons": blockers,
            },
            {
                "row_type": "gradient_summary",
                "mask_level": "ALL",
                "trainable_parameter_count": manifest["trainable_parameter_count"],
                "parameters_with_grad_count": manifest["parameters_with_grad_count"],
                "parameters_with_nonzero_grad_count": manifest["parameters_with_nonzero_grad_count"],
                "finite_nonzero_gradients": manifest["finite_nonzero_gradients"],
                "total_grad_norm": manifest["total_grad_norm"],
                "max_abs_grad": manifest["max_abs_grad"],
                "grad_nan_count": manifest["grad_nan_count"],
                "grad_inf_count": manifest["grad_inf_count"],
                "status": "passed" if manifest["finite_nonzero_gradients"] else "blocked",
                "blocking_reasons": blockers,
            },
            {
                "row_type": OPTIMIZER_STEP_ROW_TYPE,
                "mask_level": "ALL",
                "optimizer_name": manifest["optimizer_name"],
                "optimizer_lr": manifest["optimizer_lr"],
                "optimizer_weight_decay": manifest["optimizer_weight_decay"],
                "optimizer_created": manifest["optimizer_created"],
                "optimizer_create_count": manifest["optimizer_create_count"],
                "optimizer_zero_grad_called": manifest["optimizer_zero_grad_called"],
                "optimizer_zero_grad_call_count": manifest["optimizer_zero_grad_call_count"],
                OPTIMIZER_STEP_CALLED_KEY: manifest[OPTIMIZER_STEP_CALLED_KEY],
                OPTIMIZER_STEP_CALL_COUNT_KEY: manifest[OPTIMIZER_STEP_CALL_COUNT_KEY],
                OPTIMIZER_STEP_EXACTLY_ONCE_KEY: manifest[OPTIMIZER_STEP_EXACTLY_ONCE_KEY],
                "status": "passed" if manifest[OPTIMIZER_STEP_EXACTLY_ONCE_KEY] else "blocked",
                "blocking_reasons": blockers,
            },
            {
                "row_type": "parameter_update_summary",
                "mask_level": "ALL",
                "parameter_update_checked": manifest["parameter_update_checked"],
                "parameters_checked_for_update_count": manifest["parameters_checked_for_update_count"],
                "parameters_changed_count": manifest["parameters_changed_count"],
                "parameters_with_finite_update_count": manifest["parameters_with_finite_update_count"],
                "parameters_with_nonzero_update_count": manifest["parameters_with_nonzero_update_count"],
                "finite_nonzero_parameter_update": manifest["finite_nonzero_parameter_update"],
                "total_update_norm": manifest["total_update_norm"],
                "max_abs_update": manifest["max_abs_update"],
                "update_nan_count": manifest["update_nan_count"],
                "update_inf_count": manifest["update_inf_count"],
                "status": "passed" if manifest["finite_nonzero_parameter_update"] else "blocked",
                "blocking_reasons": blockers,
            },
            {
                "row_type": "decision",
                "mask_level": "ALL",
                SMOKE_PASSED_KEY: smoke_passed,
                "real_covalent_filtered_single_update_contract_proven": smoke_passed,
                "real_covalent_filtered_multi_step_training_allowed": False,
                "recommended_next_step": manifest["recommended_next_step"],
                "status": "passed" if smoke_passed else "blocked",
                "blocking_reasons": blockers,
            },
        ]
    )
    return {
        "manifest": manifest,
        "update_table_rows": table_rows,
        "run_result": run_result,
        "report_sections": {
            "step12j_precondition": {
                "step12j_filtered_cuda_backward_smoke_validated": run_result[
                    "step12j_filtered_cuda_backward_smoke_validated"
                ],
                "step12b_mask_level_aware_validator_validated": run_result[
                    "step12b_mask_level_aware_validator_validated"
                ],
            },
            "cuda_readiness": cuda,
            "filtered_batch_construction": {
                "all_filtered_batches_constructed": all_filtered_batches,
                "all_filtered_batches_on_cuda": all_filtered_on_cuda,
                "production_filter_helper_used": production_filter_used,
            },
            "strict_pretrained_model_load": {
                "model_instantiated": manifest["model_instantiated"],
                "strict_load_success": manifest["strict_load_success"],
                "pretrained_weights_loaded": manifest["pretrained_weights_loaded"],
                "model_device": manifest["model_device"],
            },
            "cuda_forward_loss": {
                "model_forward_call_count": manifest["model_forward_call_count"],
                "loss_compute_call_count": manifest["loss_compute_call_count"],
                "all_losses_finite": manifest["all_losses_finite"],
                "all_losses_on_cuda": manifest["all_losses_on_cuda"],
            },
            "aggregate_backward": {
                "aggregate_loss_value": manifest["aggregate_loss_value"],
                "aggregate_loss_device": manifest["aggregate_loss_device"],
                "backward_call_count": manifest["backward_call_count"],
                "backward_success": manifest["backward_success"],
            },
            "gradient_summary": {
                "finite_nonzero_gradients": manifest["finite_nonzero_gradients"],
                "total_grad_norm": manifest["total_grad_norm"],
                "max_abs_grad": manifest["max_abs_grad"],
            },
            OPTIMIZER_STEP_ROW_TYPE: {
                "optimizer_name": manifest["optimizer_name"],
                "optimizer_created": manifest["optimizer_created"],
                OPTIMIZER_STEP_CALL_COUNT_KEY: manifest[OPTIMIZER_STEP_CALL_COUNT_KEY],
            },
            "parameter_update_summary": {
                "parameters_checked_for_update_count": manifest["parameters_checked_for_update_count"],
                "parameters_changed_count": manifest["parameters_changed_count"],
                "finite_nonzero_parameter_update": manifest["finite_nonzero_parameter_update"],
                "total_update_norm": manifest["total_update_norm"],
            },
            "safety_and_next_step_decision": {
                "training_step_called": False,
                TRAINER_FIT_CALLED_KEY: False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "npz_created": False,
                "real_covalent_filtered_multi_step_training_allowed": False,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
