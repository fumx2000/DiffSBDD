from __future__ import annotations

from typing import Any

import torch


REQUIRED_MODEL_INPUT_KEYS = {
    "sample_id",
    "batch_size",
    "mask_level",
    "protein_x",
    "protein_h",
    "protein_mask",
    "ligand_x",
    "ligand_h",
    "ligand_mask",
    "ligand_context_x",
    "ligand_context_h",
    "ligand_context_mask",
    "ligand_target_x",
    "ligand_target_h",
    "ligand_target_mask",
    "generation_mask",
    "fixed_ligand_atom_mask",
    "ligand_reactive_atom_index",
    "protein_reactive_residue_label",
    "warhead_type_label",
    "coordinate_center",
    "mock_target_x",
    "mock_target_h",
    "checkpoint_loaded",
    "model_initialized",
    "training_executed",
}

CANONICAL_MASK_LEVEL_REACTIVE_REGION = {
    "A_warhead_only": "target",
    "B_linker_warhead": "target",
    "B2_scaffold_warhead": "target",
    "B3_scaffold_only": "context",
    "C_scaffold_linker_warhead": "target",
}


def _mask_coords(coords: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return coords * mask.to(dtype=coords.dtype).unsqueeze(-1)


def _mask_features(features: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return torch.where(mask, features, torch.zeros_like(features))


def build_covalent_model_input_v0(adapted_batch: dict[str, Any]) -> dict[str, Any]:
    ligand_x = adapted_batch["ligand_coords_centered"].to(dtype=torch.float32)
    protein_x = adapted_batch["protein_coords_centered"].to(dtype=torch.float32)
    ligand_h = adapted_batch["ligand_atomic_numbers"].to(dtype=torch.long)
    protein_h = adapted_batch["protein_atomic_numbers"].to(dtype=torch.long)
    ligand_mask = adapted_batch["ligand_atom_mask"].to(dtype=torch.bool)
    protein_mask = adapted_batch["protein_atom_mask"].to(dtype=torch.bool)
    context_mask = adapted_batch["fixed_ligand_atom_mask"].to(dtype=torch.bool)
    target_mask = adapted_batch["generation_mask"].to(dtype=torch.bool)
    return {
        "sample_id": list(adapted_batch["sample_id"]),
        "batch_size": int(adapted_batch["batch_size"]),
        "mask_level": adapted_batch["mask_level"],
        "protein_x": protein_x,
        "protein_h": protein_h,
        "protein_mask": protein_mask,
        "ligand_x": ligand_x,
        "ligand_h": ligand_h,
        "ligand_mask": ligand_mask,
        "ligand_context_x": _mask_coords(ligand_x, context_mask),
        "ligand_context_h": _mask_features(ligand_h, context_mask),
        "ligand_context_mask": context_mask,
        "ligand_target_x": _mask_coords(ligand_x, target_mask),
        "ligand_target_h": _mask_features(ligand_h, target_mask),
        "ligand_target_mask": target_mask,
        "generation_mask": target_mask,
        "fixed_ligand_atom_mask": context_mask,
        "ligand_reactive_atom_index": adapted_batch["ligand_reactive_atom_index"].to(dtype=torch.long),
        "protein_reactive_residue_label": list(adapted_batch["protein_reactive_residue_label"]),
        "warhead_type_label": list(adapted_batch["warhead_type_label"]),
        "coordinate_center": adapted_batch["coordinate_center"].to(dtype=torch.float32),
        "mock_target_x": _mask_coords(ligand_x, target_mask),
        "mock_target_h": _mask_features(ligand_h, target_mask),
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
    }


def expected_reactive_atom_region_for_mask_level_v0(mask_level: str) -> str:
    if mask_level not in CANONICAL_MASK_LEVEL_REACTIVE_REGION:
        raise ValueError(f"unsupported_mask_level:{mask_level}")
    return CANONICAL_MASK_LEVEL_REACTIVE_REGION[mask_level]


def validate_reactive_atom_region_for_mask_level_v0(model_input: dict[str, Any], mask_level: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    try:
        expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
    except ValueError:
        return False, [f"unsupported_mask_level:{mask_level}"]
    ligand_mask = model_input["ligand_mask"].to(dtype=torch.bool)
    context_mask = model_input["ligand_context_mask"].to(dtype=torch.bool)
    target_mask = model_input["ligand_target_mask"].to(dtype=torch.bool)
    reactive = model_input["ligand_reactive_atom_index"]
    batch_size = int(model_input["batch_size"])
    for idx in range(batch_size):
        atom_idx = int(reactive[idx].item())
        if atom_idx < 0 or atom_idx >= ligand_mask.shape[1] or not bool(ligand_mask[idx, atom_idx].item()):
            reasons.append(f"reactive_not_in_ligand:{idx}")
            continue
        in_target = bool(target_mask[idx, atom_idx].item())
        in_context = bool(context_mask[idx, atom_idx].item())
        if expected_region == "target":
            if not in_target:
                reasons.append(f"reactive_not_in_expected_target:{idx}")
            if in_context:
                reasons.append(f"reactive_unexpectedly_in_context:{idx}")
        elif expected_region == "context":
            if not in_context:
                reasons.append(f"reactive_not_in_expected_context:{idx}")
            if in_target:
                reasons.append(f"reactive_unexpectedly_in_target:{idx}")
        else:
            reasons.append(f"unsupported_expected_reactive_region:{expected_region}")
    return not reasons, reasons


def validate_covalent_model_input_v0(model_input: dict[str, Any], mask_level: str | None = None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_MODEL_INPUT_KEYS - set(model_input))
    if missing:
        return False, [f"missing:{','.join(missing)}"]
    batch_size = model_input["batch_size"]
    ligand_x = model_input["ligand_x"]
    protein_x = model_input["protein_x"]
    ligand_mask = model_input["ligand_mask"]
    protein_mask = model_input["protein_mask"]
    context_mask = model_input["ligand_context_mask"]
    target_mask = model_input["ligand_target_mask"]
    if batch_size != len(model_input["sample_id"]):
        reasons.append("batch_size_mismatch")
    if protein_x.ndim != 3 or protein_x.shape[-1] != 3:
        reasons.append("protein_x_shape_invalid")
    if ligand_x.ndim != 3 or ligand_x.shape[-1] != 3:
        reasons.append("ligand_x_shape_invalid")
    if model_input["protein_h"].shape != protein_x.shape[:2]:
        reasons.append("protein_h_shape_invalid")
    if model_input["protein_mask"].shape != protein_x.shape[:2]:
        reasons.append("protein_mask_shape_invalid")
    if model_input["ligand_h"].shape != ligand_x.shape[:2]:
        reasons.append("ligand_h_shape_invalid")
    if model_input["ligand_mask"].shape != ligand_x.shape[:2]:
        reasons.append("ligand_mask_shape_invalid")
    for key in ["ligand_context_x", "ligand_target_x", "mock_target_x"]:
        if model_input[key].shape != ligand_x.shape:
            reasons.append(f"{key}_shape_invalid")
    for key in ["ligand_context_h", "ligand_target_h", "mock_target_h"]:
        if model_input[key].shape != model_input["ligand_h"].shape:
            reasons.append(f"{key}_shape_invalid")
    for key in ["ligand_context_mask", "ligand_target_mask", "generation_mask", "fixed_ligand_atom_mask"]:
        if model_input[key].shape != ligand_mask.shape:
            reasons.append(f"{key}_shape_invalid")
    if model_input["coordinate_center"].shape != (batch_size, 3):
        reasons.append("coordinate_center_shape_invalid")
    if (context_mask & target_mask).any():
        reasons.append("context_target_overlap")
    if ((context_mask | target_mask) & ~ligand_mask).any():
        reasons.append("context_target_not_subset_ligand")
    if (target_mask.sum(dim=1) == 0).any():
        reasons.append("empty_target_mask")
    if mask_level is None:
        reactive = model_input["ligand_reactive_atom_index"]
        for idx in range(batch_size):
            atom_idx = int(reactive[idx].item())
            if atom_idx < 0 or atom_idx >= ligand_mask.shape[1] or not bool(target_mask[idx, atom_idx].item()):
                reasons.append(f"reactive_not_in_target:{idx}")
    else:
        reactive_valid, reactive_reasons = validate_reactive_atom_region_for_mask_level_v0(model_input, mask_level)
        if not reactive_valid:
            reasons.extend(reactive_reasons)
    if not torch.isfinite(ligand_x[ligand_mask]).all():
        reasons.append("ligand_x_not_finite")
    if not torch.isfinite(protein_x[protein_mask]).all():
        reasons.append("protein_x_not_finite")
    if not torch.isfinite(model_input["mock_target_x"]).all():
        reasons.append("mock_target_x_not_finite")
    if torch.isnan(ligand_x[ligand_mask]).any() or torch.isnan(protein_x[protein_mask]).any() or torch.isnan(model_input["mock_target_x"]).any():
        reasons.append("nan_present")
    if torch.isinf(ligand_x[ligand_mask]).any() or torch.isinf(protein_x[protein_mask]).any() or torch.isinf(model_input["mock_target_x"]).any():
        reasons.append("inf_present")
    if model_input["checkpoint_loaded"] is not False:
        reasons.append("checkpoint_loaded")
    if model_input["model_initialized"] is not False:
        reasons.append("model_initialized")
    if model_input["training_executed"] is not False:
        reasons.append("training_executed")
    return not reasons, reasons


def compute_mock_reconstruction_loss_v0(model_input: dict[str, Any]) -> dict[str, Any]:
    target_mask = model_input["ligand_target_mask"]
    target_atom_count = int(target_mask.sum().item())
    if target_atom_count == 0:
        x_mse = torch.tensor(float("nan"), dtype=torch.float32)
        h_mse = torch.tensor(float("nan"), dtype=torch.float32)
    else:
        pred_x = torch.zeros_like(model_input["mock_target_x"])
        pred_h = torch.zeros_like(model_input["mock_target_h"].to(dtype=torch.float32))
        x_delta = pred_x[target_mask] - model_input["mock_target_x"][target_mask]
        h_delta = pred_h[target_mask] - model_input["mock_target_h"].to(dtype=torch.float32)[target_mask]
        x_mse = (x_delta.square()).mean()
        h_mse = (h_delta.square()).mean()
    finite = bool(torch.isfinite(x_mse).item() and torch.isfinite(h_mse).item())
    return {
        "x_mse_on_target": float(x_mse.item()),
        "h_mse_on_target": float(h_mse.item()),
        "target_atom_count": target_atom_count,
        "mock_loss_finite": finite,
        "mock_loss_computed": True,
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
    }
