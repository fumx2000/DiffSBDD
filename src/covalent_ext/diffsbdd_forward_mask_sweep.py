from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from covalent_ext.diffsbdd_forward_shape_smoke import (
    DEFAULT_ROOT,
    SAFETY_FALSE_FIELDS,
    run_diffsbdd_single_batch_forward_shape_smoke_v0,
)


STAGE = "diffsbdd_forward_mask_level_sweep_without_checkpoint_v0"
PREVIOUS_STAGE = "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0"
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_step10e_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_single_batch_forward_shape_smoke_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_single_batch_forward_shape_smoke_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10E forward shape smoke outputs are missing")
    rows = _rows_from_csv(report_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(rows) != 1 or rows[0].get("smoke_status") != "passed":
        raise ValueError("Step 10E report is not a single passed row")
    expected_true = {
        "step10d_instantiation_passed",
        "model_initialized",
        "forward_called",
        "forward_success",
        "finite_tensor_outputs",
        "scalar_loss_like_output_finite",
        "all_checks_passed",
    }
    for key in expected_true:
        if manifest.get(key) is not True:
            raise ValueError(f"Step 10E manifest invalid for {key}: {manifest.get(key)!r}")
    expected_false = {
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
    }
    for key in expected_false:
        if manifest.get(key) is not False:
            raise ValueError(f"Step 10E manifest invalid for {key}: {manifest.get(key)!r}")
    if manifest.get("stage") != PREVIOUS_STAGE:
        raise ValueError("Step 10E manifest stage is invalid")
    if manifest.get("mask_level") != "A_warhead_only":
        raise ValueError("Step 10E manifest mask_level is not A_warhead_only")
    if manifest.get("selected_forward_call_style") != "LigandPocketDDPM.forward(data_batch)":
        raise ValueError("Step 10E selected forward call style is invalid")
    if manifest.get("recommended_next_step") != "diffsbdd_forward_mask_level_sweep_without_checkpoint":
        raise ValueError("Step 10E recommended next step is not mask-level sweep")
    return True


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _row_passed(row: dict[str, Any]) -> bool:
    return (
        row.get("smoke_status") == "passed"
        and row.get("model_initialized") is True
        and row.get("forward_called") is True
        and row.get("forward_success") is True
        and row.get("finite_tensor_outputs") is True
        and row.get("scalar_loss_like_output_finite") is True
        and all(row.get(field) is False for field in SAFETY_FALSE_FIELDS)
    )


def _collect_by_mask(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return {str(row["mask_level"]): row.get(key) for row in rows}


def _safety_any(rows: list[dict[str, Any]], key: str) -> bool:
    return any(_safe_bool(row.get(key)) for row in rows)


def run_diffsbdd_forward_mask_level_sweep_v0(device: str = "auto") -> dict[str, Any]:
    step10e_passed = validate_step10e_outputs_v0()
    rows: list[dict[str, Any]] = []
    for mask_level in MASK_LEVELS:
        result = run_diffsbdd_single_batch_forward_shape_smoke_v0(device=device, mask_level=mask_level)
        blockers = list(result.get("blocking_reasons", []))
        for safety_field in SAFETY_FALSE_FIELDS:
            if result.get(safety_field) is not False:
                blockers.append(safety_field)
        if blockers:
            result["blocking_reasons"] = sorted(set(str(reason) for reason in blockers))
            result["smoke_status"] = "blocked"
        rows.append(result)

    all_mask_levels_passed = len(rows) == len(MASK_LEVELS) and all(_row_passed(row) for row in rows)
    first = rows[0] if rows else {}
    sweep_status = "passed" if all_mask_levels_passed else "blocked"
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10e_single_forward_passed": step10e_passed,
        "requested_device": first.get("requested_device", device),
        "resolved_device": first.get("resolved_device", ""),
        "cuda_available": first.get("cuda_available", False),
        "cuda_device_count": first.get("cuda_device_count", 0),
        "cuda_device_name": first.get("cuda_device_name", ""),
        "model_class_name": first.get("model_class_name", "LigandPocketDDPM"),
        "selected_forward_call_style": first.get("selected_forward_call_style", ""),
        "mask_levels_checked": len(rows),
        "report_row_count": len(rows),
        "all_mask_levels_passed": all_mask_levels_passed,
        "sweep_status": sweep_status,
        "rows": rows,
        "target_atom_count_by_mask_level": _collect_by_mask(rows, "target_atom_count"),
        "context_atom_count_by_mask_level": _collect_by_mask(rows, "context_atom_count"),
        "forward_success_by_mask_level": _collect_by_mask(rows, "forward_success"),
        "finite_tensor_outputs_by_mask_level": _collect_by_mask(rows, "finite_tensor_outputs"),
        "scalar_loss_like_output_finite_by_mask_level": _collect_by_mask(rows, "scalar_loss_like_output_finite"),
        "output_type_by_mask_level": _collect_by_mask(rows, "output_type"),
        "tensor_output_shapes_by_mask_level": _collect_by_mask(rows, "tensor_output_shapes"),
        "checkpoint_loaded": _safety_any(rows, "checkpoint_loaded"),
        "checkpoint_saved": _safety_any(rows, "checkpoint_saved"),
        "training_step_called": _safety_any(rows, "training_step_called"),
        "backward_called": _safety_any(rows, "backward_called"),
        "optimizer_step_executed": _safety_any(rows, "optimizer_step_executed"),
        "trainer_fit_called": _safety_any(rows, "trainer_fit_called"),
        "training_executed": _safety_any(rows, "training_executed"),
        "real_finetune_executed": _safety_any(rows, "real_finetune_executed"),
        "archive_created": False,
        "all_checks_passed": all_mask_levels_passed,
        "recommended_next_step": (
            "diffsbdd_forward_loss_semantics_review_without_backward"
            if all_mask_levels_passed
            else "manual_forward_mask_sweep_review"
        ),
    }
