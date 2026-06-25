from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    DEFAULT_ROOT,
    PROTECTED_SOURCE_FILES,
    SAFETY_FALSE_FIELDS,
    _build_candidate_inputs,
    run_atomwise_loss_hook_prototype_v0,
)


STAGE = "diffsbdd_atomwise_loss_hook_shape_sweep_without_backward_v0"
PREVIOUS_STAGE = "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0"
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text_bool(value: Any) -> str:
    return str(value).strip().lower()


def _json_list(value: str) -> list[int]:
    loaded = json.loads(value)
    return [int(item) for item in loaded]


def validate_step10k_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_prototype_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_prototype_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10K atomwise hook prototype outputs are missing")
    rows = _rows_from_csv(report_path)
    if len(rows) != 1:
        raise ValueError(f"Step 10K report must contain exactly one row, found {len(rows)}")
    row = rows[0]
    expected_row_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0",
        "step10j_hook_design_passed": "true",
        "model_initialized": "true",
        "model_mode": "train",
        "forward_no_probe_success": "true",
        "forward_probe_success": "true",
        "default_behavior_preserved": "true",
        "output0_allclose": "true",
        "output1_scalar_allclose": "true",
        "eps_t_lig_captured": "true",
        "net_out_lig_captured": "true",
        "ligand_mask_flat_available": "true",
        "net_out_lig_requires_grad": "true",
        "tensor_first_dim_matches_ligand_atoms": "true",
        "target_mask_nonempty": "true",
        "target_mask_matches_ligand_atoms": "true",
        "residual_x_finite": "true",
        "residual_h_finite": "true",
        "can_compute_masked_x_loss_later": "true",
        "can_compute_masked_h_loss_later": "true",
        "original_methods_restored": "true",
        "smoke_status": "passed",
    }
    for key, expected in expected_row_values.items():
        if row.get(key) != expected:
            raise ValueError(f"Step 10K report invalid for {key}: {row.get(key)!r}")
    expected_shapes = {
        "eps_t_lig_shape": [104, 14],
        "net_out_lig_shape": [104, 14],
        "ligand_mask_flat_shape": [104],
        "residual_x_shape": [104, 3],
        "residual_h_shape": [104, 11],
    }
    for key, expected in expected_shapes.items():
        if _json_list(row.get(key, "[]")) != expected:
            raise ValueError(f"Step 10K report invalid shape for {key}: {row.get(key)!r}")
    for field_name in SAFETY_FALSE_FIELDS:
        if _text_bool(row.get(field_name, "")) != "false":
            raise ValueError(f"Step 10K report safety flag is not false: {field_name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0",
        "step10j_hook_design_passed": True,
        "model_initialized": True,
        "model_mode": "train",
        "default_behavior_preserved": True,
        "output0_allclose": True,
        "output1_scalar_allclose": True,
        "net_out_lig_requires_grad": True,
        "tensor_first_dim_matches_ligand_atoms": True,
        "target_mask_nonempty": True,
        "target_mask_matches_ligand_atoms": True,
        "residual_x_finite": True,
        "residual_h_finite": True,
        "can_compute_masked_x_loss_later": True,
        "can_compute_masked_h_loss_later": True,
        "original_methods_restored": True,
        "original_source_files_modified": False,
        "all_checks_passed": True,
        "recommended_next_step": "atomwise_loss_hook_shape_sweep_without_backward",
    }
    for key, expected in expected_manifest_values.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Step 10K manifest invalid for {key}: {manifest.get(key)!r}")
    for key, expected in expected_shapes.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Step 10K manifest invalid shape for {key}: {manifest.get(key)!r}")
    for field_name in SAFETY_FALSE_FIELDS:
        if manifest.get(field_name) is not False:
            raise ValueError(f"Step 10K manifest safety flag is not false: {field_name}")
    return True


def _source_snapshots() -> dict[str, str]:
    return {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }


def _sources_modified(before: dict[str, str]) -> bool:
    return any((REPO_ROOT / rel_path).read_text(encoding="utf-8") != text for rel_path, text in before.items())


def _mask_counts(mask_level: str) -> dict[str, int]:
    candidate_inputs = _build_candidate_inputs(mask_level)
    metadata = candidate_inputs["metadata"]
    target = metadata["ligand_target_mask_flat"].to(dtype=torch.bool)
    context = metadata["ligand_context_mask_flat"].to(dtype=torch.bool)
    ligand_atom_count = int(candidate_inputs["data_batch"]["lig_coords"].shape[0])
    return {
        "target_atom_count": int(target.sum().item()),
        "context_atom_count": int(context.sum().item()),
        "ligand_atom_count": ligand_atom_count,
    }


def _row_passed(row: dict[str, Any]) -> bool:
    required_true = [
        "forward_no_probe_success",
        "forward_probe_success",
        "default_behavior_preserved",
        "output0_allclose",
        "output1_scalar_allclose",
        "eps_t_lig_captured",
        "net_out_lig_captured",
        "ligand_mask_flat_available",
        "net_out_lig_requires_grad",
        "tensor_first_dim_matches_ligand_atoms",
        "target_mask_nonempty",
        "target_mask_matches_ligand_atoms",
        "residual_x_finite",
        "residual_h_finite",
        "can_compute_masked_x_loss_later",
        "can_compute_masked_h_loss_later",
        "original_methods_restored",
    ]
    return row["smoke_status"] == "passed" and all(row.get(field_name) is True for field_name in required_true)


def run_atomwise_loss_hook_shape_sweep_v0(device: str = "auto") -> dict[str, Any]:
    validate_step10k_outputs_v0()
    snapshots = _source_snapshots()
    rows: list[dict[str, Any]] = []
    for mask_level in MASK_LEVELS:
        counts = _mask_counts(mask_level)
        result = run_atomwise_loss_hook_prototype_v0(device=device, mask_level=mask_level)
        result.update(counts)
        rows.append(result)
    original_source_files_modified = _sources_modified(snapshots)
    for row in rows:
        row["original_source_files_modified"] = bool(row["original_source_files_modified"] or original_source_files_modified)
        if original_source_files_modified and "original_source_files_modified" not in row["blocking_reasons"]:
            row["blocking_reasons"].append("original_source_files_modified")
            row["smoke_status"] = "blocked"

    first = rows[0]
    all_mask_levels_passed = all(_row_passed(row) for row in rows)
    all_default_behavior_preserved = all(row["default_behavior_preserved"] for row in rows)
    all_atomwise_tensors_captured = all(
        row["eps_t_lig_captured"] and row["net_out_lig_captured"] and row["ligand_mask_flat_available"]
        for row in rows
    )
    all_residuals_finite = all(row["residual_x_finite"] and row["residual_h_finite"] for row in rows)
    all_targets_nonempty = all(row["target_mask_nonempty"] for row in rows)
    all_methods_restored = all(row["original_methods_restored"] for row in rows)
    all_sources_unmodified = not any(row["original_source_files_modified"] for row in rows)
    safety_flags_false = all(all(row[field_name] is False for field_name in SAFETY_FALSE_FIELDS) for row in rows)
    all_checks_passed = bool(
        all_mask_levels_passed
        and all_default_behavior_preserved
        and all_atomwise_tensors_captured
        and all_residuals_finite
        and all_targets_nonempty
        and all_methods_restored
        and all_sources_unmodified
        and safety_flags_false
    )
    summary = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10k_hook_prototype_passed": True,
        "requested_device": first["requested_device"],
        "resolved_device": first["resolved_device"],
        "cuda_available": first["cuda_available"],
        "cuda_device_name": first["cuda_device_name"],
        "mask_levels_checked": len(MASK_LEVELS),
        "mask_levels": list(MASK_LEVELS),
        "all_mask_levels_passed": all_mask_levels_passed,
        "all_default_behavior_preserved": all_default_behavior_preserved,
        "all_atomwise_tensors_captured": all_atomwise_tensors_captured,
        "all_residuals_finite": all_residuals_finite,
        "all_targets_nonempty": all_targets_nonempty,
        "all_methods_restored": all_methods_restored,
        "all_sources_unmodified": all_sources_unmodified,
        "target_atom_count_by_mask_level": {row["mask_level"]: row["target_atom_count"] for row in rows},
        "context_atom_count_by_mask_level": {row["mask_level"]: row["context_atom_count"] for row in rows},
        "eps_t_lig_shape_by_mask_level": {row["mask_level"]: row["eps_t_lig_shape"] for row in rows},
        "net_out_lig_shape_by_mask_level": {row["mask_level"]: row["net_out_lig_shape"] for row in rows},
        "residual_x_shape_by_mask_level": {row["mask_level"]: row["residual_x_shape"] for row in rows},
        "residual_h_shape_by_mask_level": {row["mask_level"]: row["residual_h_shape"] for row in rows},
        "can_compute_masked_x_loss_by_mask_level": {
            row["mask_level"]: row["can_compute_masked_x_loss_later"] for row in rows
        },
        "can_compute_masked_h_loss_by_mask_level": {
            row["mask_level"]: row["can_compute_masked_h_loss_later"] for row in rows
        },
        "original_source_files_modified": not all_sources_unmodified,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "masked_loss_dry_run_without_backward"
            if all_checks_passed
            else "manual_atomwise_hook_shape_sweep_review"
        ),
    }
    for field_name in SAFETY_FALSE_FIELDS:
        summary[field_name] = False
    return {"rows": rows, "summary": summary}
