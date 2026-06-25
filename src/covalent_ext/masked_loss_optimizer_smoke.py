from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    PROTECTED_SOURCE_FILES,
    AtomwiseProbeCapture,
    _build_candidate_inputs,
    atomwise_probe_context_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_shape_sweep import MASK_LEVELS  # noqa: E402
from covalent_ext.diffsbdd_forward_shape_smoke import (  # noqa: E402
    DEFAULT_ROOT,
    _instantiate_model_for_forward,
    move_diffsbdd_batch_to_device_v0,
    resolve_diffsbdd_forward_device_v0,
)
from covalent_ext.masked_loss_backward_smoke import (  # noqa: E402
    STAGE as STEP10N_STAGE,
    summarize_masked_loss_gradients_v0,
)
from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    EXPECTED_CONTEXT_COUNTS,
    EXPECTED_TARGET_COUNTS,
    compute_masked_loss_components_v0,
    summarize_loss_components_v0,
)


STAGE = "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
PREVIOUS_STAGE = "masked_loss_backward_smoke_without_optimizer_v0"
DEFAULT_LR = 1e-6
DEFAULT_WEIGHT_DECAY = 0.0
OPTIMIZER_CLASS = "AdamW"
SAFETY_FALSE_FIELDS = [
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "archive_created",
    "model_saved",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _source_snapshots() -> dict[str, str]:
    return {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }


def _sources_modified(before: dict[str, str]) -> bool:
    return any((REPO_ROOT / rel_path).read_text(encoding="utf-8") != text for rel_path, text in before.items())


def validate_step10n_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "masked_loss_backward_smoke_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "masked_loss_backward_smoke_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10N masked loss backward smoke outputs are missing")

    rows = _rows_from_csv(report_path)
    if len(rows) != 4:
        raise ValueError(f"Step 10N report must contain exactly four rows, found {len(rows)}")
    if [row.get("mask_level") for row in rows] != MASK_LEVELS:
        raise ValueError("Step 10N report mask levels do not match expected order")

    for row in rows:
        mask_level = row["mask_level"]
        expected = {
            "stage": STEP10N_STAGE,
            "previous_stage": "masked_loss_dry_run_without_backward_v0",
            "step10m_masked_loss_dry_run_passed": "true",
            "target_atom_count": str(EXPECTED_TARGET_COUNTS[mask_level]),
            "context_atom_count": str(EXPECTED_CONTEXT_COUNTS[mask_level]),
            "ligand_atom_count": "104",
            "loss_total_dry_finite": "true",
            "loss_total_dry_requires_grad": "true",
            "backward_called": "true",
            "backward_success": "true",
            "finite_gradients": "true",
            "nonzero_gradients": "true",
            "grad_nan_count": "0",
            "grad_inf_count": "0",
            "checkpoint_loaded": "false",
            "checkpoint_saved": "false",
            "training_step_called": "false",
            "optimizer_step_executed": "false",
            "trainer_fit_called": "false",
            "training_executed": "false",
            "real_finetune_executed": "false",
            "checkpoint_written": "false",
            "archive_created": "false",
            "original_source_files_modified": "false",
            "smoke_status": "passed",
            "blocking_reasons": "",
        }
        for key, expected_value in expected.items():
            if row.get(key) != expected_value:
                raise ValueError(f"Step 10N report invalid for {mask_level} {key}: {row.get(key)!r}")
        for key in ["parameters_with_grad", "trainable_parameters_with_grad"]:
            if int(row.get(key, "0")) <= 0:
                raise ValueError(f"Step 10N report invalid for {mask_level} {key}: {row.get(key)!r}")
        for key in ["total_grad_norm", "max_grad_abs"]:
            if float(row.get(key, "0")) <= 0:
                raise ValueError(f"Step 10N report invalid for {mask_level} {key}: {row.get(key)!r}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": STEP10N_STAGE,
        "previous_stage": "masked_loss_dry_run_without_backward_v0",
        "step10m_masked_loss_dry_run_passed": True,
        "mask_levels_checked": 4,
        "mask_levels": MASK_LEVELS,
        "all_mask_levels_passed": True,
        "all_backward_success": True,
        "all_gradients_finite": True,
        "all_gradients_nonzero": True,
        "all_grad_nan_count_zero": True,
        "all_grad_inf_count_zero": True,
        "all_expected_target_counts": True,
        "all_expected_context_counts": True,
        "all_sources_unmodified": True,
        "all_safety_flags_false_except_backward_called": True,
        "target_atom_count_by_mask_level": EXPECTED_TARGET_COUNTS,
        "context_atom_count_by_mask_level": EXPECTED_CONTEXT_COUNTS,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": True,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "archive_created": False,
        "original_source_files_modified": False,
        "all_checks_passed": True,
        "recommended_next_step": "masked_loss_optimizer_smoke_one_step_no_checkpoint",
    }
    for key, expected in expected_manifest_values.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Step 10N manifest invalid for {key}: {manifest.get(key)!r}")
    return True


def snapshot_trainable_parameters_v0(model: torch.nn.Module) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "shape": [int(dim) for dim in parameter.shape],
            "before": parameter.detach().clone(),
        }
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }


def summarize_parameter_update_v0(
    model: torch.nn.Module,
    before_snapshot: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    parameters_compared = 0
    trainable_parameters_compared = 0
    parameters_changed = 0
    trainable_parameters_changed = 0
    total_delta_norm_sq = 0.0
    max_param_delta_abs = 0.0
    finite_parameter_delta = True
    nonzero_parameter_delta = False
    post_step_param_nan_count = 0
    post_step_param_inf_count = 0

    for name, parameter in model.named_parameters():
        if name not in before_snapshot:
            continue
        parameters_compared += 1
        if parameter.requires_grad:
            trainable_parameters_compared += 1
        before = before_snapshot[name]["before"].to(device=parameter.device)
        current = parameter.detach()
        delta = current - before
        nan_count = int(torch.isnan(current).sum().item())
        inf_count = int(torch.isinf(current).sum().item())
        post_step_param_nan_count += nan_count
        post_step_param_inf_count += inf_count
        delta_nan_count = int(torch.isnan(delta).sum().item())
        delta_inf_count = int(torch.isinf(delta).sum().item())
        finite_parameter_delta = (
            finite_parameter_delta
            and nan_count == 0
            and inf_count == 0
            and delta_nan_count == 0
            and delta_inf_count == 0
        )
        if delta.numel():
            delta_norm = float(torch.linalg.vector_norm(delta).item())
            delta_abs = float(delta.abs().max().item())
        else:
            delta_norm = 0.0
            delta_abs = 0.0
        total_delta_norm_sq += delta_norm * delta_norm
        max_param_delta_abs = max(max_param_delta_abs, delta_abs)
        changed = delta_abs > 0.0
        if changed:
            parameters_changed += 1
            if parameter.requires_grad:
                trainable_parameters_changed += 1
        nonzero_parameter_delta = nonzero_parameter_delta or changed

    return {
        "parameters_compared": parameters_compared,
        "trainable_parameters_compared": trainable_parameters_compared,
        "parameters_changed": parameters_changed,
        "trainable_parameters_changed": trainable_parameters_changed,
        "total_param_delta_norm": math.sqrt(total_delta_norm_sq),
        "max_param_delta_abs": max_param_delta_abs,
        "finite_parameter_delta": bool(finite_parameter_delta),
        "nonzero_parameter_delta": bool(nonzero_parameter_delta),
        "post_step_param_nan_count": post_step_param_nan_count,
        "post_step_param_inf_count": post_step_param_inf_count,
    }


def build_optimizer_v0(model: torch.nn.Module, lr: float = DEFAULT_LR) -> torch.optim.Optimizer:
    return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=DEFAULT_WEIGHT_DECAY)


def _set_forward_seed(device_info: dict[str, Any]) -> None:
    torch.manual_seed(4401)
    if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
        torch.cuda.manual_seed_all(4401)


def _base_result(device_info: dict[str, Any], mask_level: str, lr: float) -> dict[str, Any]:
    result = {
        **device_info,
        "mask_level": mask_level,
        "target_atom_count": 0,
        "context_atom_count": 0,
        "ligand_atom_count": 0,
        "loss_original_scalar": "",
        "loss_masked_x_scalar": "",
        "loss_masked_h_scalar": "",
        "loss_total_dry_scalar": "",
        "loss_total_dry_finite": False,
        "loss_total_dry_requires_grad": False,
        "backward_called": False,
        "backward_success": False,
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": float(lr),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "optimizer_step_executed": False,
        "optimizer_step_success": False,
        "parameter_count": 0,
        "trainable_parameter_count": 0,
        "parameters_with_grad": 0,
        "trainable_parameters_with_grad": 0,
        "total_grad_norm": 0.0,
        "max_grad_abs": 0.0,
        "finite_gradients": False,
        "nonzero_gradients": False,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "parameters_compared": 0,
        "trainable_parameters_compared": 0,
        "parameters_changed": 0,
        "trainable_parameters_changed": 0,
        "total_param_delta_norm": 0.0,
        "max_param_delta_abs": 0.0,
        "finite_parameter_delta": False,
        "nonzero_parameter_delta": False,
        "post_step_param_nan_count": 0,
        "post_step_param_inf_count": 0,
        "original_source_files_modified": False,
        "smoke_status": "blocked",
        "blocking_reasons": [],
    }
    for field_name in SAFETY_FALSE_FIELDS:
        result[field_name] = False
    return result


def run_masked_loss_optimizer_smoke_for_mask_level_v0(
    device: str,
    mask_level: str,
    lr: float = DEFAULT_LR,
) -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    result = _base_result(device_info, mask_level, lr)
    snapshots = _source_snapshots()
    try:
        candidate_inputs = _build_candidate_inputs(mask_level)
        metadata = candidate_inputs["metadata"]
        target_mask = metadata["ligand_target_mask_flat"].to(dtype=torch.bool)
        context_mask = metadata["ligand_context_mask_flat"].to(dtype=torch.bool)
        result["target_atom_count"] = int(target_mask.sum().item())
        result["context_atom_count"] = int(context_mask.sum().item())
        result["ligand_atom_count"] = int(candidate_inputs["data_batch"]["lig_coords"].shape[0])

        model, counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        result.update(counts)
        if model is None:
            result["blocking_reasons"].extend(reasons)
            return result
        model.train()
        optimizer = build_optimizer_v0(model, lr=lr)
        optimizer.zero_grad(set_to_none=True)
        before_snapshot = snapshot_trainable_parameters_v0(model)

        data_batch = move_diffsbdd_batch_to_device_v0(
            candidate_inputs["data_batch"], torch.device(device_info["resolved_device"])
        )
        _set_forward_seed(device_info)
        capture = AtomwiseProbeCapture()
        with atomwise_probe_context_v0(model, capture):
            output = model(data_batch)
        output0 = output[0] if isinstance(output, tuple) and output else output
        if capture.eps_t_lig is None or capture.net_out_lig is None:
            result["blocking_reasons"].append("atomwise_probe_capture_missing")
            return result

        loss_components = compute_masked_loss_components_v0(
            output0=output0,
            eps_t_lig=capture.eps_t_lig,
            net_out_lig=capture.net_out_lig,
            target_mask=target_mask.to(device=capture.eps_t_lig.device),
        )
        result.update(summarize_loss_components_v0(loss_components))
        result["blocking_reasons"].extend(loss_components["blocking_reasons"])
        loss_total_dry = loss_components["loss_total_dry"]

        blockers = []
        if result["target_atom_count"] != EXPECTED_TARGET_COUNTS[mask_level]:
            blockers.append("unexpected_target_atom_count")
        if result["context_atom_count"] != EXPECTED_CONTEXT_COUNTS[mask_level]:
            blockers.append("unexpected_context_atom_count")
        if result["ligand_atom_count"] != 104:
            blockers.append("unexpected_ligand_atom_count")
        if result["loss_total_dry_finite"] is not True:
            blockers.append("loss_total_dry_not_finite")
        if result["loss_total_dry_requires_grad"] is not True:
            blockers.append("loss_total_dry_requires_grad_not_true")
        if loss_total_dry is None:
            blockers.append("loss_total_dry_missing")
        if blockers:
            result["blocking_reasons"].extend(blockers)
            return result

        result["backward_called"] = True
        loss_total_dry.backward()
        result["backward_success"] = True
        result.update(summarize_masked_loss_gradients_v0(model))
        result["optimizer_step_executed"] = True
        optimizer.step()
        result["optimizer_step_success"] = True
        result.update(summarize_parameter_update_v0(model, before_snapshot))
        optimizer.zero_grad(set_to_none=True)

        if result["parameters_with_grad"] <= 0:
            blockers.append("parameters_with_grad_zero")
        if result["trainable_parameters_with_grad"] <= 0:
            blockers.append("trainable_parameters_with_grad_zero")
        if result["total_grad_norm"] <= 0:
            blockers.append("total_grad_norm_not_positive")
        if result["max_grad_abs"] <= 0:
            blockers.append("max_grad_abs_not_positive")
        if result["finite_gradients"] is not True:
            blockers.append("gradients_not_finite")
        if result["nonzero_gradients"] is not True:
            blockers.append("gradients_all_zero")
        if result["grad_nan_count"] != 0:
            blockers.append("grad_nan_count_nonzero")
        if result["grad_inf_count"] != 0:
            blockers.append("grad_inf_count_nonzero")
        if result["optimizer_step_executed"] is not True or result["optimizer_step_success"] is not True:
            blockers.append("optimizer_step_not_successful")
        if result["parameters_changed"] <= 0:
            blockers.append("parameters_changed_zero")
        if result["trainable_parameters_changed"] <= 0:
            blockers.append("trainable_parameters_changed_zero")
        if result["total_param_delta_norm"] <= 0:
            blockers.append("total_param_delta_norm_not_positive")
        if result["max_param_delta_abs"] <= 0:
            blockers.append("max_param_delta_abs_not_positive")
        if result["finite_parameter_delta"] is not True:
            blockers.append("parameter_delta_not_finite")
        if result["nonzero_parameter_delta"] is not True:
            blockers.append("parameter_delta_all_zero")
        if result["post_step_param_nan_count"] != 0:
            blockers.append("post_step_param_nan_count_nonzero")
        if result["post_step_param_inf_count"] != 0:
            blockers.append("post_step_param_inf_count_nonzero")
        if any(result[field_name] is not False for field_name in SAFETY_FALSE_FIELDS):
            blockers.append("safety_flag_not_false")

        result["original_source_files_modified"] = _sources_modified(snapshots)
        if result["original_source_files_modified"]:
            blockers.append("original_source_files_modified")
        result["blocking_reasons"].extend(blockers)
        result["blocking_reasons"] = sorted(set(result["blocking_reasons"]))
        result["smoke_status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["blocking_reasons"].append(f"masked_loss_optimizer_smoke_failed:{type(exc).__name__}:{exc}")
        result["original_source_files_modified"] = _sources_modified(snapshots)
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result


def run_masked_loss_optimizer_smoke_v0(device: str = "auto", lr: float = DEFAULT_LR) -> dict[str, Any]:
    validate_step10n_outputs_v0()
    snapshots = _source_snapshots()
    rows = [
        run_masked_loss_optimizer_smoke_for_mask_level_v0(device=device, mask_level=mask_level, lr=lr)
        for mask_level in MASK_LEVELS
    ]
    sources_modified = _sources_modified(snapshots)
    for row in rows:
        row["original_source_files_modified"] = bool(row["original_source_files_modified"] or sources_modified)
        if sources_modified:
            row["smoke_status"] = "blocked"
            row["blocking_reasons"] = sorted(set(row["blocking_reasons"] + ["original_source_files_modified"]))

    first = rows[0]
    all_mask_levels_passed = all(row["smoke_status"] == "passed" for row in rows)
    all_backward_success = all(row["backward_called"] and row["backward_success"] for row in rows)
    all_optimizer_steps_success = all(
        row["optimizer_step_executed"] and row["optimizer_step_success"] for row in rows
    )
    all_gradients_finite = all(row["finite_gradients"] for row in rows)
    all_gradients_nonzero = all(row["nonzero_gradients"] for row in rows)
    all_parameter_updates_finite = all(row["finite_parameter_delta"] for row in rows)
    all_parameter_updates_nonzero = all(row["nonzero_parameter_delta"] for row in rows)
    all_post_step_params_finite = all(
        row["post_step_param_nan_count"] == 0 and row["post_step_param_inf_count"] == 0 for row in rows
    )
    all_expected_target_counts = all(
        row["target_atom_count"] == EXPECTED_TARGET_COUNTS[row["mask_level"]] for row in rows
    )
    all_expected_context_counts = all(
        row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[row["mask_level"]] for row in rows
    )
    all_sources_unmodified = not any(row["original_source_files_modified"] for row in rows)
    all_safety_flags_false_except_backward_and_optimizer = all(
        all(row[field_name] is False for field_name in SAFETY_FALSE_FIELDS) for row in rows
    )
    all_checks_passed = bool(
        all_mask_levels_passed
        and all_backward_success
        and all_optimizer_steps_success
        and all_gradients_finite
        and all_gradients_nonzero
        and all_parameter_updates_finite
        and all_parameter_updates_nonzero
        and all_post_step_params_finite
        and all_expected_target_counts
        and all_expected_context_counts
        and all_sources_unmodified
        and all_safety_flags_false_except_backward_and_optimizer
    )
    summary = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10n_backward_smoke_passed": True,
        "requested_device": first["requested_device"],
        "resolved_device": first["resolved_device"],
        "cuda_available": first["cuda_available"],
        "cuda_device_count": first["cuda_device_count"],
        "cuda_device_name": first["cuda_device_name"],
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": float(lr),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "mask_levels_checked": len(MASK_LEVELS),
        "mask_levels": list(MASK_LEVELS),
        "all_mask_levels_passed": all_mask_levels_passed,
        "all_backward_success": all_backward_success,
        "all_optimizer_steps_success": all_optimizer_steps_success,
        "all_gradients_finite": all_gradients_finite,
        "all_gradients_nonzero": all_gradients_nonzero,
        "all_parameter_updates_finite": all_parameter_updates_finite,
        "all_parameter_updates_nonzero": all_parameter_updates_nonzero,
        "all_post_step_params_finite": all_post_step_params_finite,
        "all_expected_target_counts": all_expected_target_counts,
        "all_expected_context_counts": all_expected_context_counts,
        "all_sources_unmodified": all_sources_unmodified,
        "target_atom_count_by_mask_level": {row["mask_level"]: row["target_atom_count"] for row in rows},
        "context_atom_count_by_mask_level": {row["mask_level"]: row["context_atom_count"] for row in rows},
        "loss_total_dry_by_mask_level": {row["mask_level"]: row["loss_total_dry_scalar"] for row in rows},
        "total_grad_norm_by_mask_level": {row["mask_level"]: row["total_grad_norm"] for row in rows},
        "max_grad_abs_by_mask_level": {row["mask_level"]: row["max_grad_abs"] for row in rows},
        "parameters_changed_by_mask_level": {row["mask_level"]: row["parameters_changed"] for row in rows},
        "trainable_parameters_changed_by_mask_level": {
            row["mask_level"]: row["trainable_parameters_changed"] for row in rows
        },
        "total_param_delta_norm_by_mask_level": {
            row["mask_level"]: row["total_param_delta_norm"] for row in rows
        },
        "max_param_delta_abs_by_mask_level": {row["mask_level"]: row["max_param_delta_abs"] for row in rows},
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": True,
        "optimizer_step_executed": True,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "archive_created": False,
        "model_saved": False,
        "original_source_files_modified": not all_sources_unmodified,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "training_loop_design_without_checkpoint"
            if all_checks_passed
            else "manual_masked_loss_optimizer_smoke_review"
        ),
    }
    return {"rows": rows, "summary": summary}
