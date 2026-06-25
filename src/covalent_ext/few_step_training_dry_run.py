from __future__ import annotations

import csv
import json
import sys
import time
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
from covalent_ext.diffsbdd_forward_shape_smoke import (  # noqa: E402
    DEFAULT_ROOT,
    _instantiate_model_for_forward,
    move_diffsbdd_batch_to_device_v0,
    resolve_diffsbdd_forward_device_v0,
)
from covalent_ext.masked_loss_backward_smoke import summarize_masked_loss_gradients_v0  # noqa: E402
from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    EXPECTED_CONTEXT_COUNTS,
    EXPECTED_TARGET_COUNTS,
    compute_masked_loss_components_v0,
    summarize_loss_components_v0,
)
from covalent_ext.masked_loss_optimizer_smoke import (  # noqa: E402
    DEFAULT_WEIGHT_DECAY,
    OPTIMIZER_CLASS,
    build_optimizer_v0,
    snapshot_trainable_parameters_v0,
    summarize_parameter_update_v0,
)


STAGE = "few_step_training_dry_run_no_checkpoint_v0"
PREVIOUS_STAGE = "training_loop_design_without_checkpoint_v0"
LOOP_NAME = "masked_covalent_training_loop_v0"
MASK_ORDER = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
MAX_STEPS = 4
BATCH_SIZE = 3
SHUFFLE = False
SEED = 4401
DEFAULT_LR = 1e-6
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


def _source_snapshots() -> dict[str, str]:
    return {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }


def _sources_modified(before: dict[str, str]) -> bool:
    return any((REPO_ROOT / rel_path).read_text(encoding="utf-8") != text for rel_path, text in before.items())


def _forbidden_artifacts_created(root: str | Path = DEFAULT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def validate_step10p_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "training_loop_design_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "training_loop_design_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10P training loop design outputs are missing")
    rows = _rows_from_csv(report_path)
    if len(rows) != 12:
        raise ValueError(f"Step 10P design report must contain exactly 12 rows, found {len(rows)}")
    for row in rows:
        expected = {
            "stage": "training_loop_design_without_checkpoint_v0",
            "previous_stage": "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0",
            "step10o_optimizer_smoke_passed": "true",
            "checkpoint_allowed": "false",
            "model_save_allowed": "false",
            "trainer_fit_allowed": "false",
            "training_step_allowed": "false",
            "source_modification_allowed": "false",
            "design_status": "passed",
            "blocking_reasons": "",
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise ValueError(f"Step 10P design report invalid for {key}: {row.get(key)!r}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": "training_loop_design_without_checkpoint_v0",
        "previous_stage": "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0",
        "step10o_optimizer_smoke_passed": True,
        "loop_name": LOOP_NAME,
        "intended_next_stage": "few_step_training_dry_run_no_checkpoint",
        "mask_schedule_name": "balanced_A_B_B2_C_cycle",
        "mask_order": MASK_ORDER,
        "max_steps_initial_dry_run": MAX_STEPS,
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "loss_weights": {"w_original": 1.0, "w_x": 1.0, "w_h": 0.2},
        "checkpoint_allowed": False,
        "model_save_allowed": False,
        "trainer_fit_allowed": False,
        "training_step_allowed": False,
        "source_modification_allowed": False,
        "all_checks_passed": True,
        "recommended_next_step": "few_step_training_dry_run_no_checkpoint",
    }
    for key, value in expected_manifest_values.items():
        if manifest.get(key) != value:
            raise ValueError(f"Step 10P manifest invalid for {key}: {manifest.get(key)!r}")
    forbidden_outputs = set(manifest.get("forbidden_outputs", []))
    for expected in [".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", "checkpoint files", "saved model files"]:
        if expected not in forbidden_outputs:
            raise ValueError(f"Step 10P manifest missing forbidden output: {expected}")
    stop_conditions = " ".join(manifest.get("stop_conditions", []))
    for expected in ["max_steps hard cap", "finite loss", "finite gradients", "finite parameters", "NaN/Inf", "unexpected mask level", "missing target mask"]:
        if expected not in stop_conditions:
            raise ValueError(f"Step 10P manifest missing stop condition concept: {expected}")
    logging_fields = set(manifest.get("required_logging_fields", []))
    for expected in [
        "step",
        "mask_level",
        "sample_ids",
        "loss_original",
        "loss_masked_x",
        "loss_masked_h",
        "loss_total",
        "target_atom_count",
        "context_atom_count",
        "grad_norm",
        "max_grad_abs",
        "param_delta_norm",
        "max_param_delta_abs",
        "learning_rate",
        "optimizer_class",
        "cuda_device",
        "elapsed_seconds",
    ]:
        if expected not in logging_fields:
            raise ValueError(f"Step 10P manifest missing logging field: {expected}")
    return True


def _set_step_seed(device_info: dict[str, Any], step_index: int) -> None:
    torch.manual_seed(SEED + int(step_index))
    if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED + int(step_index))


def _base_step_row(device_info: dict[str, Any], mask_level: str, step_index: int, lr: float) -> dict[str, Any]:
    row = {
        "step": int(step_index),
        "mask_level": mask_level,
        "sample_ids": [],
        "target_atom_count": 0,
        "context_atom_count": 0,
        "ligand_atom_count": 0,
        "loss_original": "",
        "loss_masked_x": "",
        "loss_masked_h": "",
        "loss_total": "",
        "loss_finite": False,
        "loss_total_requires_grad": False,
        "backward_called": False,
        "backward_success": False,
        "optimizer_step_executed": False,
        "optimizer_step_success": False,
        "grad_norm": 0.0,
        "max_grad_abs": 0.0,
        "finite_gradients": False,
        "nonzero_gradients": False,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "param_delta_norm": 0.0,
        "max_param_delta_abs": 0.0,
        "finite_parameter_delta": False,
        "nonzero_parameter_delta": False,
        "post_step_param_nan_count": 0,
        "post_step_param_inf_count": 0,
        "learning_rate": float(lr),
        "optimizer_class": OPTIMIZER_CLASS,
        "cuda_device": device_info["cuda_device_name"],
        "elapsed_seconds": 0.0,
        "stop_triggered": False,
        "stop_reason": "",
        "step_status": "blocked",
        "blocking_reasons": [],
    }
    for field_name in SAFETY_FALSE_FIELDS:
        row[field_name] = False
    row["original_source_files_modified"] = False
    return row


def _loss_scalar(summary: dict[str, Any], key: str) -> float | str:
    value = summary.get(key, "")
    return value if value == "" else float(value)


def run_one_dry_step_v0(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    device_info: dict[str, Any],
    mask_level: str,
    step_index: int,
    lr: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    row = _base_step_row(device_info, mask_level, step_index, lr)
    try:
        candidate_inputs = _build_candidate_inputs(mask_level)
        metadata = candidate_inputs["metadata"]
        row["sample_ids"] = list(metadata.get("sample_id", []))
        target_mask = metadata["ligand_target_mask_flat"].to(dtype=torch.bool)
        context_mask = metadata["ligand_context_mask_flat"].to(dtype=torch.bool)
        row["target_atom_count"] = int(target_mask.sum().item())
        row["context_atom_count"] = int(context_mask.sum().item())
        row["ligand_atom_count"] = int(candidate_inputs["data_batch"]["lig_coords"].shape[0])

        blockers: list[str] = []
        if mask_level not in MASK_ORDER:
            blockers.append("unexpected_mask_level")
        if row["target_atom_count"] <= 0:
            blockers.append("missing_target_mask")
        if row["target_atom_count"] != EXPECTED_TARGET_COUNTS[mask_level]:
            blockers.append("unexpected_target_atom_count")
        if row["context_atom_count"] != EXPECTED_CONTEXT_COUNTS[mask_level]:
            blockers.append("unexpected_context_atom_count")
        if row["ligand_atom_count"] != 104:
            blockers.append("unexpected_ligand_atom_count")
        if blockers:
            row["blocking_reasons"].extend(blockers)
            row["stop_triggered"] = True
            row["stop_reason"] = blockers[0]
            return row

        optimizer.zero_grad(set_to_none=True)
        data_batch = move_diffsbdd_batch_to_device_v0(
            candidate_inputs["data_batch"], torch.device(device_info["resolved_device"])
        )
        _set_step_seed(device_info, step_index)
        capture = AtomwiseProbeCapture()
        with atomwise_probe_context_v0(model, capture):
            output = model(data_batch)
        output0 = output[0] if isinstance(output, tuple) and output else output
        if capture.eps_t_lig is None or capture.net_out_lig is None:
            row["blocking_reasons"].append("atomwise_probe_capture_missing")
            row["stop_triggered"] = True
            row["stop_reason"] = "atomwise_probe_capture_missing"
            return row

        loss_components = compute_masked_loss_components_v0(
            output0=output0,
            eps_t_lig=capture.eps_t_lig,
            net_out_lig=capture.net_out_lig,
            target_mask=target_mask.to(device=capture.eps_t_lig.device),
        )
        loss_summary = summarize_loss_components_v0(loss_components)
        row["loss_original"] = _loss_scalar(loss_summary, "loss_original_scalar")
        row["loss_masked_x"] = _loss_scalar(loss_summary, "loss_masked_x_scalar")
        row["loss_masked_h"] = _loss_scalar(loss_summary, "loss_masked_h_scalar")
        row["loss_total"] = _loss_scalar(loss_summary, "loss_total_dry_scalar")
        row["loss_finite"] = bool(
            loss_summary["loss_original_finite"]
            and loss_summary["loss_masked_x_finite"]
            and loss_summary["loss_masked_h_finite"]
            and loss_summary["loss_total_dry_finite"]
        )
        row["loss_total_requires_grad"] = bool(loss_summary["loss_total_dry_requires_grad"])
        row["blocking_reasons"].extend(loss_components["blocking_reasons"])
        loss_total = loss_components["loss_total_dry"]
        if not row["loss_finite"]:
            row["blocking_reasons"].append("loss_not_finite")
        if row["loss_total_requires_grad"] is not True:
            row["blocking_reasons"].append("loss_total_requires_grad_not_true")
        if loss_total is None:
            row["blocking_reasons"].append("loss_total_missing")
        if row["blocking_reasons"]:
            row["stop_triggered"] = True
            row["stop_reason"] = row["blocking_reasons"][0]
            return row

        before_snapshot = snapshot_trainable_parameters_v0(model)
        row["backward_called"] = True
        loss_total.backward()
        row["backward_success"] = True
        grad_summary = summarize_masked_loss_gradients_v0(model)
        row["grad_norm"] = grad_summary["total_grad_norm"]
        row["max_grad_abs"] = grad_summary["max_grad_abs"]
        row["finite_gradients"] = grad_summary["finite_gradients"]
        row["nonzero_gradients"] = grad_summary["nonzero_gradients"]
        row["grad_nan_count"] = grad_summary["grad_nan_count"]
        row["grad_inf_count"] = grad_summary["grad_inf_count"]
        if row["finite_gradients"] is not True:
            row["blocking_reasons"].append("gradients_not_finite")
        if row["nonzero_gradients"] is not True:
            row["blocking_reasons"].append("gradients_all_zero")
        if row["grad_nan_count"] != 0:
            row["blocking_reasons"].append("grad_nan_count_nonzero")
        if row["grad_inf_count"] != 0:
            row["blocking_reasons"].append("grad_inf_count_nonzero")
        if row["grad_norm"] <= 0:
            row["blocking_reasons"].append("grad_norm_not_positive")
        if row["max_grad_abs"] <= 0:
            row["blocking_reasons"].append("max_grad_abs_not_positive")
        if row["blocking_reasons"]:
            row["stop_triggered"] = True
            row["stop_reason"] = row["blocking_reasons"][0]
            return row

        row["optimizer_step_executed"] = True
        optimizer.step()
        row["optimizer_step_success"] = True
        param_summary = summarize_parameter_update_v0(model, before_snapshot)
        row["param_delta_norm"] = param_summary["total_param_delta_norm"]
        row["max_param_delta_abs"] = param_summary["max_param_delta_abs"]
        row["finite_parameter_delta"] = param_summary["finite_parameter_delta"]
        row["nonzero_parameter_delta"] = param_summary["nonzero_parameter_delta"]
        row["post_step_param_nan_count"] = param_summary["post_step_param_nan_count"]
        row["post_step_param_inf_count"] = param_summary["post_step_param_inf_count"]
        optimizer.zero_grad(set_to_none=True)
        if row["finite_parameter_delta"] is not True:
            row["blocking_reasons"].append("parameter_delta_not_finite")
        if row["nonzero_parameter_delta"] is not True:
            row["blocking_reasons"].append("parameter_delta_all_zero")
        if row["post_step_param_nan_count"] != 0:
            row["blocking_reasons"].append("post_step_param_nan_count_nonzero")
        if row["post_step_param_inf_count"] != 0:
            row["blocking_reasons"].append("post_step_param_inf_count_nonzero")
        if row["param_delta_norm"] <= 0:
            row["blocking_reasons"].append("param_delta_norm_not_positive")
        if row["max_param_delta_abs"] <= 0:
            row["blocking_reasons"].append("max_param_delta_abs_not_positive")
        if row["blocking_reasons"]:
            row["stop_triggered"] = True
            row["stop_reason"] = row["blocking_reasons"][0]
            return row
        row["step_status"] = "passed"
    except Exception as exc:
        row["blocking_reasons"].append(f"few_step_dry_run_step_failed:{type(exc).__name__}:{exc}")
        row["stop_triggered"] = True
        row["stop_reason"] = f"few_step_dry_run_step_failed:{type(exc).__name__}"
    finally:
        row["elapsed_seconds"] = time.perf_counter() - started
    return row


def _blocked_summary(
    device_info: dict[str, Any],
    max_steps: int,
    stop_reason: str,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = [] if rows is None else rows
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10p_training_loop_design_passed": True,
        "loop_name": LOOP_NAME,
        "intended_next_stage": "few_step_training_dry_run_no_checkpoint",
        "requested_device": device_info["requested_device"],
        "resolved_device": device_info["resolved_device"],
        "cuda_available": device_info["cuda_available"],
        "cuda_device_count": device_info["cuda_device_count"],
        "cuda_device_name": device_info["cuda_device_name"],
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": DEFAULT_LR,
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "max_steps": max_steps,
        "executed_steps": len(rows),
        "dry_run_training_steps_executed": len(rows),
        "mask_order": list(MASK_ORDER),
        "mask_levels_seen": [row["mask_level"] for row in rows],
        "expected_mask_order_followed": False,
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "all_steps_passed": False,
        "all_losses_finite": False,
        "all_loss_total_requires_grad": False,
        "all_backward_success": False,
        "all_optimizer_steps_success": False,
        "all_gradients_finite": False,
        "all_gradients_nonzero": False,
        "all_parameter_updates_finite": False,
        "all_parameter_updates_nonzero": False,
        "all_post_step_params_finite": False,
        "stop_triggered": True,
        "stop_reason": stop_reason,
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
        "forbidden_artifacts_created": _forbidden_artifacts_created(),
        "all_checks_passed": False,
        "recommended_next_step": "manual_few_step_training_dry_run_review",
    }


def run_few_step_training_dry_run_v0(
    device: str = "auto",
    lr: float = DEFAULT_LR,
    max_steps: int = MAX_STEPS,
) -> dict[str, Any]:
    validate_step10p_outputs_v0()
    device_info = resolve_diffsbdd_forward_device_v0(device)
    if max_steps != MAX_STEPS:
        return {"rows": [], "summary": _blocked_summary(device_info, max_steps, "max_steps_must_equal_4")}
    if MASK_ORDER != ["A_warhead_only", "B_linker_warhead", "B2_scaffold_warhead", "C_scaffold_linker_warhead"]:
        return {"rows": [], "summary": _blocked_summary(device_info, max_steps, "mask_order_invalid")}

    snapshots = _source_snapshots()
    rows: list[dict[str, Any]] = []
    try:
        first_candidate_inputs = _build_candidate_inputs(MASK_ORDER[0])
        model, _counts, reasons = _instantiate_model_for_forward(device_info, first_candidate_inputs)
        if model is None:
            return {"rows": [], "summary": _blocked_summary(device_info, max_steps, ";".join(reasons) or "model_init_failed")}
        model.train()
        optimizer = build_optimizer_v0(model, lr=lr)
        for step_index, mask_level in enumerate(MASK_ORDER[:max_steps], start=1):
            row = run_one_dry_step_v0(
                model=model,
                optimizer=optimizer,
                device_info=device_info,
                mask_level=mask_level,
                step_index=step_index,
                lr=lr,
            )
            rows.append(row)
            if row["step_status"] != "passed" or row["stop_triggered"]:
                break
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()

    sources_modified = _sources_modified(snapshots)
    forbidden_artifacts_created = _forbidden_artifacts_created()
    for row in rows:
        row["original_source_files_modified"] = bool(row["original_source_files_modified"] or sources_modified)
        if sources_modified:
            row["blocking_reasons"] = sorted(set(row["blocking_reasons"] + ["original_source_files_modified"]))
            row["step_status"] = "blocked"
            row["stop_triggered"] = True
            row["stop_reason"] = row["stop_reason"] or "original_source_files_modified"
        if forbidden_artifacts_created:
            row["blocking_reasons"] = sorted(set(row["blocking_reasons"] + ["forbidden_artifacts_created"]))
            row["step_status"] = "blocked"
            row["stop_triggered"] = True
            row["stop_reason"] = row["stop_reason"] or "forbidden_artifacts_created"

    executed_steps = len(rows)
    mask_levels_seen = [row["mask_level"] for row in rows]
    expected_mask_order_followed = mask_levels_seen == MASK_ORDER[:executed_steps]
    all_steps_passed = executed_steps == MAX_STEPS and all(row["step_status"] == "passed" for row in rows)
    all_losses_finite = all(row["loss_finite"] for row in rows) and executed_steps == MAX_STEPS
    all_loss_total_requires_grad = all(row["loss_total_requires_grad"] for row in rows) and executed_steps == MAX_STEPS
    all_backward_success = all(row["backward_called"] and row["backward_success"] for row in rows) and executed_steps == MAX_STEPS
    all_optimizer_steps_success = (
        all(row["optimizer_step_executed"] and row["optimizer_step_success"] for row in rows)
        and executed_steps == MAX_STEPS
    )
    all_gradients_finite = all(row["finite_gradients"] for row in rows) and executed_steps == MAX_STEPS
    all_gradients_nonzero = all(row["nonzero_gradients"] for row in rows) and executed_steps == MAX_STEPS
    all_parameter_updates_finite = all(row["finite_parameter_delta"] for row in rows) and executed_steps == MAX_STEPS
    all_parameter_updates_nonzero = all(row["nonzero_parameter_delta"] for row in rows) and executed_steps == MAX_STEPS
    all_post_step_params_finite = (
        all(row["post_step_param_nan_count"] == 0 and row["post_step_param_inf_count"] == 0 for row in rows)
        and executed_steps == MAX_STEPS
    )
    stop_triggered = any(row["stop_triggered"] for row in rows) or executed_steps != MAX_STEPS
    stop_reason = ""
    if stop_triggered:
        stop_reason = next((row["stop_reason"] for row in rows if row["stop_reason"]), "loop_did_not_complete_4_steps")
    all_checks_passed = bool(
        all_steps_passed
        and all_losses_finite
        and all_loss_total_requires_grad
        and all_backward_success
        and all_optimizer_steps_success
        and all_gradients_finite
        and all_gradients_nonzero
        and all_parameter_updates_finite
        and all_parameter_updates_nonzero
        and all_post_step_params_finite
        and expected_mask_order_followed
        and not stop_triggered
        and not sources_modified
        and not forbidden_artifacts_created
    )
    summary = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10p_training_loop_design_passed": True,
        "loop_name": LOOP_NAME,
        "intended_next_stage": "few_step_training_dry_run_no_checkpoint",
        "requested_device": device_info["requested_device"],
        "resolved_device": device_info["resolved_device"],
        "cuda_available": device_info["cuda_available"],
        "cuda_device_count": device_info["cuda_device_count"],
        "cuda_device_name": device_info["cuda_device_name"],
        "optimizer_class": OPTIMIZER_CLASS,
        "optimizer_lr": float(lr),
        "optimizer_weight_decay": DEFAULT_WEIGHT_DECAY,
        "max_steps": max_steps,
        "executed_steps": executed_steps,
        "dry_run_training_steps_executed": executed_steps,
        "mask_order": list(MASK_ORDER),
        "mask_levels_seen": mask_levels_seen,
        "expected_mask_order_followed": expected_mask_order_followed,
        "batch_size": BATCH_SIZE,
        "shuffle": SHUFFLE,
        "seed": SEED,
        "all_steps_passed": all_steps_passed,
        "all_losses_finite": all_losses_finite,
        "all_loss_total_requires_grad": all_loss_total_requires_grad,
        "all_backward_success": all_backward_success,
        "all_optimizer_steps_success": all_optimizer_steps_success,
        "all_gradients_finite": all_gradients_finite,
        "all_gradients_nonzero": all_gradients_nonzero,
        "all_parameter_updates_finite": all_parameter_updates_finite,
        "all_parameter_updates_nonzero": all_parameter_updates_nonzero,
        "all_post_step_params_finite": all_post_step_params_finite,
        "stop_triggered": stop_triggered,
        "stop_reason": stop_reason,
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
        "original_source_files_modified": sources_modified,
        "forbidden_artifacts_created": forbidden_artifacts_created,
        "loss_total_by_step": {str(row["step"]): row["loss_total"] for row in rows},
        "mask_level_by_step": {str(row["step"]): row["mask_level"] for row in rows},
        "grad_norm_by_step": {str(row["step"]): row["grad_norm"] for row in rows},
        "param_delta_norm_by_step": {str(row["step"]): row["param_delta_norm"] for row in rows},
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "few_step_training_dry_run_review_and_training_boundary"
            if all_checks_passed
            else "manual_few_step_training_dry_run_review"
        ),
    }
    return {"rows": rows, "summary": summary}
