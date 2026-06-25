from __future__ import annotations

import math
from typing import Any

import torch

from covalent_ext.model_input_adapter import compute_mock_reconstruction_loss_v0


def _resolve_device(device: str) -> tuple[torch.device, str]:
    try:
        requested = torch.device(device)
    except (RuntimeError, TypeError) as exc:
        return torch.device("cpu"), f"invalid_device_fallback_to_cpu:{device}:{exc}"
    if requested.type == "cuda" and not torch.cuda.is_available():
        return torch.device("cpu"), f"cuda_unavailable_fallback_to_cpu:{device}"
    return requested, ""


def move_model_input_to_device_v0(model_input: dict[str, Any], device: str = "cpu") -> dict[str, Any]:
    resolved_device, device_transfer_error = _resolve_device(device)
    moved: dict[str, Any] = {}
    for key, value in model_input.items():
        if isinstance(value, torch.Tensor):
            moved[key] = value.to(resolved_device)
        else:
            moved[key] = value
    moved["device"] = str(resolved_device)
    moved["requested_device"] = str(device)
    moved["device_transfer_error"] = device_transfer_error
    return moved


def summarize_model_input_for_preflight_v0(model_input: dict[str, Any]) -> dict[str, Any]:
    ligand_mask = model_input["ligand_mask"].to(dtype=torch.bool)
    protein_mask = model_input["protein_mask"].to(dtype=torch.bool)
    target_mask = model_input["ligand_target_mask"].to(dtype=torch.bool)
    context_mask = model_input["ligand_context_mask"].to(dtype=torch.bool)
    ligand_x = model_input["ligand_x"]
    protein_x = model_input["protein_x"]
    reactive = model_input["ligand_reactive_atom_index"]
    reactive_in_target = []
    for idx in range(int(model_input["batch_size"])):
        atom_idx = int(reactive[idx].item())
        in_range = 0 <= atom_idx < target_mask.shape[1]
        reactive_in_target.append(bool(in_range and target_mask[idx, atom_idx].item()))
    valid_ligand_x = ligand_x[ligand_mask]
    valid_protein_x = protein_x[protein_mask]
    tensors_for_nan_inf = [
        valid_ligand_x,
        valid_protein_x,
        model_input["ligand_context_x"],
        model_input["ligand_target_x"],
        model_input["mock_target_x"],
        model_input["coordinate_center"],
    ]
    no_nan = all(not bool(torch.isnan(tensor).any().item()) for tensor in tensors_for_nan_inf)
    no_inf = all(not bool(torch.isinf(tensor).any().item()) for tensor in tensors_for_nan_inf)
    finite_coords_all = bool(torch.isfinite(valid_ligand_x).all().item() and torch.isfinite(valid_protein_x).all().item())
    return {
        "batch_size": int(model_input["batch_size"]),
        "mask_level": model_input["mask_level"],
        "sample_count": len(model_input["sample_id"]),
        "protein_x_shape": list(model_input["protein_x"].shape),
        "ligand_x_shape": list(model_input["ligand_x"].shape),
        "ligand_context_x_shape": list(model_input["ligand_context_x"].shape),
        "ligand_target_x_shape": list(model_input["ligand_target_x"].shape),
        "protein_mask_shape": list(model_input["protein_mask"].shape),
        "ligand_mask_shape": list(model_input["ligand_mask"].shape),
        "ligand_target_mask_shape": list(model_input["ligand_target_mask"].shape),
        "coordinate_center_shape": list(model_input["coordinate_center"].shape),
        "target_atom_count_total": int(target_mask.sum().item()),
        "target_atom_count_per_sample": [int(value) for value in target_mask.sum(dim=1).tolist()],
        "context_atom_count_total": int(context_mask.sum().item()),
        "context_atom_count_per_sample": [int(value) for value in context_mask.sum(dim=1).tolist()],
        "reactive_atom_in_target_mask_all": all(reactive_in_target),
        "context_target_no_overlap_all": not bool((context_mask & target_mask).any().item()),
        "finite_coords_all": finite_coords_all,
        "no_nan": no_nan,
        "no_inf": no_inf,
    }


def run_mock_training_preflight_step_v0(model_input: dict[str, Any]) -> dict[str, Any]:
    mock_loss = compute_mock_reconstruction_loss_v0(model_input)
    x_mse = float(mock_loss["x_mse_on_target"])
    h_mse = float(mock_loss["h_mse_on_target"])
    total_loss = x_mse + 0.01 * h_mse
    target_atom_count = int(mock_loss["target_atom_count"])
    return {
        "x_mse_on_target": x_mse,
        "h_mse_on_target": h_mse,
        "mock_total_loss": total_loss,
        "target_atom_count": target_atom_count,
        "target_atom_count_positive": target_atom_count > 0,
        "mock_total_loss_finite": math.isfinite(total_loss),
        "mock_loss_computed": bool(mock_loss["mock_loss_computed"]),
        "mock_loss_finite": bool(mock_loss["mock_loss_finite"]),
        "checkpoint_loaded": bool(model_input["checkpoint_loaded"]),
        "model_initialized": bool(model_input["model_initialized"]),
        "training_executed": bool(model_input["training_executed"]),
    }
