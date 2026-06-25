from __future__ import annotations

from typing import Any

import torch


EXPECTED_DIFFSBDD_BATCH_FIELDS = [
    "lig_coords",
    "lig_one_hot",
    "lig_mask",
    "num_lig_atoms",
    "pocket_coords",
    "pocket_one_hot",
    "pocket_mask",
    "num_pocket_nodes",
    "lig_fixed",
    "generation_mask_flat",
    "ligand_context_mask_flat",
    "ligand_target_mask_flat",
    "coordinate_center",
    "sample_id",
    "mask_level",
    "batch_size",
]

EXPECTED_LIGAND_DICT_FIELDS = ["x", "one_hot", "size", "mask"]
EXPECTED_POCKET_DICT_FIELDS = ["x", "one_hot", "size", "mask"]

SHAPE_SMOKE_REQUIRED_KEYS = {
    "ligand",
    "pocket",
    "lig_fixed",
    "generation_mask_flat",
    "ligand_context_mask_flat",
    "ligand_target_mask_flat",
    "coordinate_center",
    "sample_id",
    "mask_level",
    "batch_size",
    "checkpoint_loaded",
    "checkpoint_saved",
    "diffsbdd_model_initialized",
    "diffsbdd_model_called",
    "training_executed",
}


def build_diffsbdd_batch_fields_v0(diffsbdd_like: dict[str, Any]) -> dict[str, Any]:
    return {
        "lig_coords": diffsbdd_like["lig_coords"],
        "lig_one_hot": diffsbdd_like["lig_one_hot"],
        "lig_mask": diffsbdd_like["lig_mask"],
        "num_lig_atoms": diffsbdd_like["num_lig_atoms"],
        "pocket_coords": diffsbdd_like["pocket_coords"],
        "pocket_one_hot": diffsbdd_like["pocket_one_hot"],
        "pocket_mask": diffsbdd_like["pocket_mask"],
        "num_pocket_nodes": diffsbdd_like["num_pocket_nodes"],
        "lig_fixed": diffsbdd_like["lig_fixed"],
        "generation_mask_flat": diffsbdd_like["generation_mask_flat"].to(dtype=torch.bool),
        "ligand_context_mask_flat": diffsbdd_like["ligand_context_mask_flat"].to(dtype=torch.bool),
        "ligand_target_mask_flat": diffsbdd_like["ligand_target_mask_flat"].to(dtype=torch.bool),
        "coordinate_center": diffsbdd_like["coordinate_center"],
        "sample_id": list(diffsbdd_like["sample_id"]),
        "mask_level": diffsbdd_like["mask_level"],
        "batch_size": int(diffsbdd_like["batch_size"]),
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "diffsbdd_model_initialized": False,
        "diffsbdd_model_called": False,
        "training_executed": False,
    }


def build_ligand_pocket_dicts_for_diffsbdd_v0(batch_fields: dict[str, Any]) -> dict[str, Any]:
    ligand = {
        "x": batch_fields["lig_coords"],
        "one_hot": batch_fields["lig_one_hot"],
        "size": batch_fields["num_lig_atoms"],
        "mask": batch_fields["lig_mask"],
    }
    pocket = {
        "x": batch_fields["pocket_coords"],
        "one_hot": batch_fields["pocket_one_hot"],
        "size": batch_fields["num_pocket_nodes"],
        "mask": batch_fields["pocket_mask"],
    }
    return {
        "ligand": ligand,
        "pocket": pocket,
        "lig_fixed": batch_fields["lig_fixed"],
        "generation_mask_flat": batch_fields["generation_mask_flat"],
        "ligand_context_mask_flat": batch_fields["ligand_context_mask_flat"],
        "ligand_target_mask_flat": batch_fields["ligand_target_mask_flat"],
        "coordinate_center": batch_fields["coordinate_center"],
        "batch_size": int(batch_fields["batch_size"]),
        "mask_level": batch_fields["mask_level"],
        "sample_id": list(batch_fields["sample_id"]),
        "checkpoint_loaded": bool(batch_fields["checkpoint_loaded"]),
        "checkpoint_saved": bool(batch_fields["checkpoint_saved"]),
        "diffsbdd_model_initialized": bool(batch_fields["diffsbdd_model_initialized"]),
        "diffsbdd_model_called": bool(batch_fields["diffsbdd_model_called"]),
        "training_executed": bool(batch_fields["training_executed"]),
    }


def _mask_indices_valid(mask: torch.Tensor, batch_size: int) -> bool:
    if mask.numel() == 0:
        return False
    return bool(mask.min().item() >= 0 and mask.max().item() < batch_size)


def _lig_fixed_matches_context(shape_smoke: dict[str, Any]) -> bool:
    fixed = shape_smoke["lig_fixed"]
    context = shape_smoke["ligand_context_mask_flat"].to(dtype=torch.bool)
    if fixed.ndim != 2 or fixed.shape[1] != 1 or fixed.shape[0] != context.shape[0]:
        return False
    return bool(torch.equal(fixed.squeeze(1).to(dtype=torch.bool), context))


def _shape_sanity_passed(shape_smoke: dict[str, Any]) -> bool:
    ligand = shape_smoke["ligand"]
    pocket = shape_smoke["pocket"]
    batch_size = int(shape_smoke["batch_size"])
    return (
        ligand["x"].ndim == 2
        and ligand["x"].shape[1] == 3
        and pocket["x"].ndim == 2
        and pocket["x"].shape[1] == 3
        and ligand["one_hot"].ndim == 2
        and pocket["one_hot"].ndim == 2
        and ligand["one_hot"].shape[0] == ligand["x"].shape[0]
        and pocket["one_hot"].shape[0] == pocket["x"].shape[0]
        and ligand["mask"].shape == (ligand["x"].shape[0],)
        and pocket["mask"].shape == (pocket["x"].shape[0],)
        and ligand["size"].shape == (batch_size,)
        and pocket["size"].shape == (batch_size,)
        and int(ligand["size"].sum().item()) == ligand["x"].shape[0]
        and int(pocket["size"].sum().item()) == pocket["x"].shape[0]
        and shape_smoke["generation_mask_flat"].shape == (ligand["x"].shape[0],)
        and shape_smoke["ligand_context_mask_flat"].shape == (ligand["x"].shape[0],)
        and shape_smoke["ligand_target_mask_flat"].shape == (ligand["x"].shape[0],)
        and shape_smoke["lig_fixed"].shape == (ligand["x"].shape[0], 1)
        and shape_smoke["coordinate_center"].shape == (batch_size, 3)
    )


def _mask_sanity_passed(shape_smoke: dict[str, Any]) -> bool:
    ligand = shape_smoke["ligand"]
    pocket = shape_smoke["pocket"]
    batch_size = int(shape_smoke["batch_size"])
    generation = shape_smoke["generation_mask_flat"].to(dtype=torch.bool)
    context = shape_smoke["ligand_context_mask_flat"].to(dtype=torch.bool)
    target = shape_smoke["ligand_target_mask_flat"].to(dtype=torch.bool)
    return (
        _mask_indices_valid(ligand["mask"], batch_size)
        and _mask_indices_valid(pocket["mask"], batch_size)
        and bool(torch.equal(generation, target))
        and not bool((context & target).any().item())
        and int(target.sum().item()) > 0
        and _lig_fixed_matches_context(shape_smoke)
    )


def validate_diffsbdd_adapter_shape_smoke_v0(shape_smoke: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing = sorted(SHAPE_SMOKE_REQUIRED_KEYS - set(shape_smoke))
    if missing:
        return False, [f"missing:{','.join(missing)}"]
    ligand = shape_smoke["ligand"]
    pocket = shape_smoke["pocket"]
    missing_ligand = sorted(set(EXPECTED_LIGAND_DICT_FIELDS) - set(ligand))
    missing_pocket = sorted(set(EXPECTED_POCKET_DICT_FIELDS) - set(pocket))
    if missing_ligand:
        reasons.append(f"missing_ligand:{','.join(missing_ligand)}")
    if missing_pocket:
        reasons.append(f"missing_pocket:{','.join(missing_pocket)}")
    if reasons:
        return False, reasons
    if not _shape_sanity_passed(shape_smoke):
        reasons.append("shape_sanity_failed")
    if not _mask_sanity_passed(shape_smoke):
        reasons.append("mask_sanity_failed")
    if not torch.isfinite(ligand["x"]).all() or not torch.isfinite(pocket["x"]).all():
        reasons.append("coords_not_finite")
    if not torch.isfinite(ligand["one_hot"]).all() or not torch.isfinite(pocket["one_hot"]).all():
        reasons.append("one_hot_not_finite")
    if shape_smoke["checkpoint_loaded"] is not False:
        reasons.append("checkpoint_loaded")
    if shape_smoke["checkpoint_saved"] is not False:
        reasons.append("checkpoint_saved")
    if shape_smoke["diffsbdd_model_initialized"] is not False:
        reasons.append("diffsbdd_model_initialized")
    if shape_smoke["diffsbdd_model_called"] is not False:
        reasons.append("diffsbdd_model_called")
    if shape_smoke["training_executed"] is not False:
        reasons.append("training_executed")
    return not reasons, reasons


def summarize_diffsbdd_shape_smoke_v0(shape_smoke: dict[str, Any]) -> dict[str, Any]:
    ligand = shape_smoke["ligand"]
    pocket = shape_smoke["pocket"]
    target = shape_smoke["ligand_target_mask_flat"].to(dtype=torch.bool)
    context = shape_smoke["ligand_context_mask_flat"].to(dtype=torch.bool)
    fixed = shape_smoke["lig_fixed"].squeeze(1).to(dtype=torch.bool)
    return {
        "batch_size": int(shape_smoke["batch_size"]),
        "mask_level": shape_smoke["mask_level"],
        "ligand_atom_total": int(ligand["x"].shape[0]),
        "pocket_atom_total": int(pocket["x"].shape[0]),
        "ligand_feature_dim": int(ligand["one_hot"].shape[1]),
        "pocket_feature_dim": int(pocket["one_hot"].shape[1]),
        "num_lig_atoms": [int(value) for value in ligand["size"].detach().cpu().tolist()],
        "num_pocket_nodes": [int(value) for value in pocket["size"].detach().cpu().tolist()],
        "target_atom_count": int(target.sum().item()),
        "context_atom_count": int(context.sum().item()),
        "lig_fixed_count": int(fixed.sum().item()),
        "ligand_x_shape": list(ligand["x"].shape),
        "ligand_one_hot_shape": list(ligand["one_hot"].shape),
        "pocket_x_shape": list(pocket["x"].shape),
        "pocket_one_hot_shape": list(pocket["one_hot"].shape),
        "ligand_mask_shape": list(ligand["mask"].shape),
        "pocket_mask_shape": list(pocket["mask"].shape),
        "coordinate_center_shape": list(shape_smoke["coordinate_center"].shape),
        "generation_mask_flat_shape": list(shape_smoke["generation_mask_flat"].shape),
        "ligand_context_mask_flat_shape": list(shape_smoke["ligand_context_mask_flat"].shape),
        "ligand_target_mask_flat_shape": list(shape_smoke["ligand_target_mask_flat"].shape),
        "generation_equals_target": bool(torch.equal(shape_smoke["generation_mask_flat"].to(dtype=torch.bool), target)),
        "context_target_no_overlap": not bool((context & target).any().item()),
        "lig_fixed_matches_context": _lig_fixed_matches_context(shape_smoke),
        "flattened_ligand_count_matches_size": int(ligand["size"].sum().item()) == int(ligand["x"].shape[0]),
        "flattened_pocket_count_matches_size": int(pocket["size"].sum().item()) == int(pocket["x"].shape[0]),
        "coords_finite": bool(torch.isfinite(ligand["x"]).all().item() and torch.isfinite(pocket["x"]).all().item()),
        "one_hot_finite": bool(torch.isfinite(ligand["one_hot"]).all().item() and torch.isfinite(pocket["one_hot"]).all().item()),
        "shape_sanity_passed": _shape_sanity_passed(shape_smoke),
        "mask_sanity_passed": _mask_sanity_passed(shape_smoke),
    }
