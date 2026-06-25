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
    AtomwiseProbeCapture,
    _build_candidate_inputs,
    atomwise_probe_context_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_shape_sweep import MASK_LEVELS  # noqa: E402
from covalent_ext.diffsbdd_forward_shape_smoke import (  # noqa: E402
    _instantiate_model_for_forward,
    move_diffsbdd_batch_to_device_v0,
    resolve_diffsbdd_forward_device_v0,
)


STAGE = "masked_loss_dry_run_without_backward_v0"
PREVIOUS_STAGE = "diffsbdd_atomwise_loss_hook_shape_sweep_without_backward_v0"
EXPECTED_TARGET_COUNTS = {
    "A_warhead_only": 12,
    "B_linker_warhead": 30,
    "B2_scaffold_warhead": 86,
    "C_scaffold_linker_warhead": 104,
}
EXPECTED_CONTEXT_COUNTS = {
    "A_warhead_only": 92,
    "B_linker_warhead": 74,
    "B2_scaffold_warhead": 18,
    "C_scaffold_linker_warhead": 0,
}
DEFAULT_WEIGHTS = {
    "w_original": 1.0,
    "w_x": 1.0,
    "w_h": 0.2,
}


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text_bool(value: Any) -> str:
    return str(value).strip().lower()


def _json_list(value: str) -> list[int]:
    loaded = json.loads(value)
    return [int(item) for item in loaded]


def validate_step10l_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_shape_sweep_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_shape_sweep_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10L atomwise hook shape sweep outputs are missing")
    rows = _rows_from_csv(report_path)
    if len(rows) != 4:
        raise ValueError(f"Step 10L report must contain exactly four rows, found {len(rows)}")
    if [row["mask_level"] for row in rows] != MASK_LEVELS:
        raise ValueError("Step 10L report mask levels do not match expected order")
    for row in rows:
        mask_level = row["mask_level"]
        expected = {
            "stage": PREVIOUS_STAGE,
            "previous_stage": "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0",
            "step10k_hook_prototype_passed": "true",
            "target_atom_count": str(EXPECTED_TARGET_COUNTS[mask_level]),
            "context_atom_count": str(EXPECTED_CONTEXT_COUNTS[mask_level]),
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
            "original_source_files_modified": "false",
            "smoke_status": "passed",
        }
        for key, expected_value in expected.items():
            if row.get(key) != expected_value:
                raise ValueError(f"Step 10L report invalid for {mask_level} {key}: {row.get(key)!r}")
        for key, expected_shape in {
            "eps_t_lig_shape": [104, 14],
            "net_out_lig_shape": [104, 14],
            "residual_x_shape": [104, 3],
            "residual_h_shape": [104, 11],
        }.items():
            if _json_list(row.get(key, "[]")) != expected_shape:
                raise ValueError(f"Step 10L report invalid shape for {mask_level} {key}: {row.get(key)!r}")
        for field_name in SAFETY_FALSE_FIELDS:
            if _text_bool(row.get(field_name, "")) != "false":
                raise ValueError(f"Step 10L report safety flag is not false: {field_name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0",
        "step10k_hook_prototype_passed": True,
        "mask_levels_checked": 4,
        "mask_levels": MASK_LEVELS,
        "all_mask_levels_passed": True,
        "all_default_behavior_preserved": True,
        "all_atomwise_tensors_captured": True,
        "all_residuals_finite": True,
        "all_targets_nonempty": True,
        "all_methods_restored": True,
        "all_sources_unmodified": True,
        "target_atom_count_by_mask_level": EXPECTED_TARGET_COUNTS,
        "context_atom_count_by_mask_level": EXPECTED_CONTEXT_COUNTS,
        "original_source_files_modified": False,
        "all_checks_passed": True,
        "recommended_next_step": "masked_loss_dry_run_without_backward",
    }
    for key, expected in expected_manifest_values.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Step 10L manifest invalid for {key}: {manifest.get(key)!r}")
    for mask_level in MASK_LEVELS:
        if manifest["can_compute_masked_x_loss_by_mask_level"].get(mask_level) is not True:
            raise ValueError(f"Step 10L manifest masked x readiness false for {mask_level}")
        if manifest["can_compute_masked_h_loss_by_mask_level"].get(mask_level) is not True:
            raise ValueError(f"Step 10L manifest masked h readiness false for {mask_level}")
    for field_name in SAFETY_FALSE_FIELDS:
        if manifest.get(field_name) is not False:
            raise ValueError(f"Step 10L manifest safety flag is not false: {field_name}")
    return True


def compute_masked_loss_components_v0(
    output0: torch.Tensor,
    eps_t_lig: torch.Tensor,
    net_out_lig: torch.Tensor,
    target_mask: torch.Tensor,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    blocking_reasons: list[str] = []
    if not torch.is_tensor(output0):
        blocking_reasons.append("output0_not_tensor")
    if eps_t_lig.shape != net_out_lig.shape:
        blocking_reasons.append("eps_t_lig_net_out_lig_shape_mismatch")
    if target_mask.ndim != 1 or target_mask.shape[0] != eps_t_lig.shape[0]:
        blocking_reasons.append("target_mask_shape_mismatch")
    target_mask = target_mask.to(device=eps_t_lig.device, dtype=torch.bool)
    if int(target_mask.sum().item()) <= 0:
        blocking_reasons.append("target_mask_empty")
    residual = eps_t_lig - net_out_lig
    residual_x = residual[:, :3]
    residual_h = residual[:, 3:]
    if residual_x.shape[1] != 3:
        blocking_reasons.append("residual_x_not_three_dimensional")
    if residual_h.ndim != 2 or residual_h.shape[1] <= 0:
        blocking_reasons.append("residual_h_feature_dim_empty")
    if blocking_reasons:
        return {
            "loss_original": None,
            "loss_masked_x": None,
            "loss_masked_h": None,
            "loss_total_dry": None,
            "residual_x": residual_x,
            "residual_h": residual_h,
            "dry_run_status": "blocked",
            "blocking_reasons": blocking_reasons,
        }
    loss_original = output0.mean()
    loss_masked_x = torch.mean(torch.sum(residual_x[target_mask] ** 2, dim=-1))
    loss_masked_h = torch.mean(torch.sum(residual_h[target_mask] ** 2, dim=-1))
    loss_total_dry = (
        weights["w_original"] * loss_original
        + weights["w_x"] * loss_masked_x
        + weights["w_h"] * loss_masked_h
    )
    return {
        "loss_original": loss_original,
        "loss_masked_x": loss_masked_x,
        "loss_masked_h": loss_masked_h,
        "loss_total_dry": loss_total_dry,
        "residual_x": residual_x,
        "residual_h": residual_h,
        "dry_run_status": "passed",
        "blocking_reasons": [],
    }


def _shape(value: torch.Tensor | None) -> list[int]:
    if value is None:
        return []
    return [int(dim) for dim in value.shape]


def _scalar(value: torch.Tensor | None) -> float | str:
    if value is None:
        return ""
    return float(value.detach().item())


def _finite(value: torch.Tensor | None) -> bool:
    return bool(value is not None and torch.isfinite(value.detach()).all().item())


def summarize_loss_components_v0(loss_components: dict[str, Any]) -> dict[str, Any]:
    loss_original = loss_components["loss_original"]
    loss_masked_x = loss_components["loss_masked_x"]
    loss_masked_h = loss_components["loss_masked_h"]
    loss_total_dry = loss_components["loss_total_dry"]
    residual_x = loss_components["residual_x"]
    residual_h = loss_components["residual_h"]
    return {
        "loss_original_scalar": _scalar(loss_original),
        "loss_masked_x_scalar": _scalar(loss_masked_x),
        "loss_masked_h_scalar": _scalar(loss_masked_h),
        "loss_total_dry_scalar": _scalar(loss_total_dry),
        "loss_original_finite": _finite(loss_original),
        "loss_masked_x_finite": _finite(loss_masked_x),
        "loss_masked_h_finite": _finite(loss_masked_h),
        "loss_total_dry_finite": _finite(loss_total_dry),
        "loss_total_dry_requires_grad": bool(loss_total_dry is not None and loss_total_dry.requires_grad),
        "loss_masked_x_requires_grad": bool(loss_masked_x is not None and loss_masked_x.requires_grad),
        "loss_masked_h_requires_grad": bool(loss_masked_h is not None and loss_masked_h.requires_grad),
        "residual_x_shape": _shape(residual_x),
        "residual_h_shape": _shape(residual_h),
        "residual_x_finite": bool(torch.isfinite(residual_x.detach()).all().item()),
        "residual_h_finite": bool(torch.isfinite(residual_h.detach()).all().item()),
    }


def _source_snapshots() -> dict[str, str]:
    return {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }


def _sources_modified(before: dict[str, str]) -> bool:
    return any((REPO_ROOT / rel_path).read_text(encoding="utf-8") != text for rel_path, text in before.items())


def _set_forward_seed(device_info: dict[str, Any]) -> None:
    torch.manual_seed(4101)
    if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
        torch.cuda.manual_seed_all(4101)


def _base_result(device_info: dict[str, Any], mask_level: str) -> dict[str, Any]:
    result = {
        **device_info,
        "mask_level": mask_level,
        "target_atom_count": 0,
        "context_atom_count": 0,
        "ligand_atom_count": 0,
        "model_initialized": False,
        "model_mode": "train",
        "eps_t_lig_shape": [],
        "net_out_lig_shape": [],
        "residual_x_shape": [],
        "residual_h_shape": [],
        "loss_original_scalar": "",
        "loss_masked_x_scalar": "",
        "loss_masked_h_scalar": "",
        "loss_total_dry_scalar": "",
        "loss_original_finite": False,
        "loss_masked_x_finite": False,
        "loss_masked_h_finite": False,
        "loss_total_dry_finite": False,
        "loss_total_dry_requires_grad": False,
        "loss_masked_x_requires_grad": False,
        "loss_masked_h_requires_grad": False,
        "target_mask_nonempty": False,
        "target_mask_matches_ligand_atoms": False,
        "used_target_mask_not_full_ligand": False,
        "c_level_full_ligand_target_expected": False,
        "dry_run_status": "blocked",
        "original_source_files_modified": False,
        "blocking_reasons": [],
    }
    for field_name in SAFETY_FALSE_FIELDS:
        result[field_name] = False
    return result


def run_masked_loss_dry_run_for_mask_level_v0(device: str, mask_level: str) -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    result = _base_result(device_info, mask_level)
    snapshots = _source_snapshots()
    try:
        candidate_inputs = _build_candidate_inputs(mask_level)
        metadata = candidate_inputs["metadata"]
        target_mask = metadata["ligand_target_mask_flat"].to(dtype=torch.bool)
        context_mask = metadata["ligand_context_mask_flat"].to(dtype=torch.bool)
        result["target_atom_count"] = int(target_mask.sum().item())
        result["context_atom_count"] = int(context_mask.sum().item())
        result["ligand_atom_count"] = int(candidate_inputs["data_batch"]["lig_coords"].shape[0])
        result["target_mask_nonempty"] = result["target_atom_count"] > 0
        result["target_mask_matches_ligand_atoms"] = target_mask.shape == (result["ligand_atom_count"],)
        result["used_target_mask_not_full_ligand"] = result["target_atom_count"] < result["ligand_atom_count"]
        result["c_level_full_ligand_target_expected"] = (
            mask_level == "C_scaffold_linker_warhead"
            and result["target_atom_count"] == result["ligand_atom_count"]
        )
        model, counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        result.update(counts)
        if model is None:
            result["blocking_reasons"].extend(reasons)
            return result
        model.train()
        result["model_mode"] = "train"
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
        result["eps_t_lig_shape"] = _shape(capture.eps_t_lig)
        result["net_out_lig_shape"] = _shape(capture.net_out_lig)
        result.update(summarize_loss_components_v0(loss_components))
        result["blocking_reasons"].extend(loss_components["blocking_reasons"])
        blockers = []
        expected_target = EXPECTED_TARGET_COUNTS[mask_level]
        expected_context = EXPECTED_CONTEXT_COUNTS[mask_level]
        if result["target_atom_count"] != expected_target:
            blockers.append("unexpected_target_atom_count")
        if result["context_atom_count"] != expected_context:
            blockers.append("unexpected_context_atom_count")
        for field_name in [
            "loss_original_finite",
            "loss_masked_x_finite",
            "loss_masked_h_finite",
            "loss_total_dry_finite",
            "loss_total_dry_requires_grad",
            "loss_masked_x_requires_grad",
            "loss_masked_h_requires_grad",
            "target_mask_nonempty",
            "target_mask_matches_ligand_atoms",
        ]:
            if result[field_name] is not True:
                blockers.append(f"{field_name}_not_true")
        if mask_level != "C_scaffold_linker_warhead" and result["used_target_mask_not_full_ligand"] is not True:
            blockers.append("target_subset_not_used_for_subset_mask_level")
        if mask_level == "C_scaffold_linker_warhead" and result["c_level_full_ligand_target_expected"] is not True:
            blockers.append("c_level_full_ligand_target_not_marked_expected")
        if any(result[field_name] is not False for field_name in SAFETY_FALSE_FIELDS):
            blockers.append("safety_flag_not_false")
        result["original_source_files_modified"] = _sources_modified(snapshots)
        if result["original_source_files_modified"]:
            blockers.append("original_source_files_modified")
        result["blocking_reasons"].extend(blockers)
        result["blocking_reasons"] = sorted(set(result["blocking_reasons"]))
        result["dry_run_status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["blocking_reasons"].append(f"masked_loss_dry_run_failed:{type(exc).__name__}:{exc}")
        result["original_source_files_modified"] = _sources_modified(snapshots)
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result


def run_masked_loss_dry_run_v0(device: str = "auto") -> dict[str, Any]:
    validate_step10l_outputs_v0()
    snapshots = _source_snapshots()
    rows = [run_masked_loss_dry_run_for_mask_level_v0(device=device, mask_level=mask_level) for mask_level in MASK_LEVELS]
    sources_modified = _sources_modified(snapshots)
    for row in rows:
        row["original_source_files_modified"] = bool(row["original_source_files_modified"] or sources_modified)
        if sources_modified:
            row["dry_run_status"] = "blocked"
            row["blocking_reasons"] = sorted(set(row["blocking_reasons"] + ["original_source_files_modified"]))
    first = rows[0]
    all_mask_levels_passed = all(row["dry_run_status"] == "passed" for row in rows)
    all_loss_scalars_finite = all(
        row["loss_original_finite"]
        and row["loss_masked_x_finite"]
        and row["loss_masked_h_finite"]
        and row["loss_total_dry_finite"]
        for row in rows
    )
    all_loss_total_requires_grad = all(row["loss_total_dry_requires_grad"] for row in rows)
    all_target_masks_nonempty = all(row["target_mask_nonempty"] for row in rows)
    all_expected_target_counts = all(
        row["target_atom_count"] == EXPECTED_TARGET_COUNTS[row["mask_level"]] for row in rows
    )
    all_expected_context_counts = all(
        row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[row["mask_level"]] for row in rows
    )
    all_sources_unmodified = not any(row["original_source_files_modified"] for row in rows)
    all_safety_flags_false = all(all(row[field_name] is False for field_name in SAFETY_FALSE_FIELDS) for row in rows)
    all_checks_passed = bool(
        all_mask_levels_passed
        and all_loss_scalars_finite
        and all_loss_total_requires_grad
        and all_target_masks_nonempty
        and all_expected_target_counts
        and all_expected_context_counts
        and all_sources_unmodified
        and all_safety_flags_false
    )
    summary = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10l_hook_shape_sweep_passed": True,
        "requested_device": first["requested_device"],
        "resolved_device": first["resolved_device"],
        "cuda_available": first["cuda_available"],
        "cuda_device_name": first["cuda_device_name"],
        "mask_levels_checked": len(MASK_LEVELS),
        "mask_levels": list(MASK_LEVELS),
        "all_mask_levels_passed": all_mask_levels_passed,
        "all_loss_scalars_finite": all_loss_scalars_finite,
        "all_loss_total_requires_grad": all_loss_total_requires_grad,
        "all_target_masks_nonempty": all_target_masks_nonempty,
        "all_expected_target_counts": all_expected_target_counts,
        "all_expected_context_counts": all_expected_context_counts,
        "all_sources_unmodified": all_sources_unmodified,
        "all_safety_flags_false": all_safety_flags_false,
        "target_atom_count_by_mask_level": {row["mask_level"]: row["target_atom_count"] for row in rows},
        "context_atom_count_by_mask_level": {row["mask_level"]: row["context_atom_count"] for row in rows},
        "loss_original_by_mask_level": {row["mask_level"]: row["loss_original_scalar"] for row in rows},
        "loss_masked_x_by_mask_level": {row["mask_level"]: row["loss_masked_x_scalar"] for row in rows},
        "loss_masked_h_by_mask_level": {row["mask_level"]: row["loss_masked_h_scalar"] for row in rows},
        "loss_total_dry_by_mask_level": {row["mask_level"]: row["loss_total_dry_scalar"] for row in rows},
        "loss_total_dry_requires_grad_by_mask_level": {
            row["mask_level"]: row["loss_total_dry_requires_grad"] for row in rows
        },
        "used_target_mask_not_full_ligand_by_mask_level": {
            row["mask_level"]: row["used_target_mask_not_full_ligand"] for row in rows
        },
        "c_level_full_ligand_target_expected": rows[-1]["c_level_full_ligand_target_expected"],
        "original_source_files_modified": not all_sources_unmodified,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": (
            "masked_loss_backward_smoke_without_optimizer"
            if all_checks_passed
            else "manual_masked_loss_dry_run_review"
        ),
    }
    for field_name in SAFETY_FALSE_FIELDS:
        summary[field_name] = False
    return {"rows": rows, "summary": summary}
