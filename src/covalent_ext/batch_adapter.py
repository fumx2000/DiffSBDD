from __future__ import annotations

from typing import Any

import torch


MASK_LEVEL_TO_BATCH_KEY = {
    "A_warhead_only": "generation_mask_A_warhead_only",
    "B_linker_warhead": "generation_mask_B_linker_warhead",
    "B2_scaffold_warhead": "generation_mask_B2_scaffold_warhead",
    "B3_scaffold_only": "generation_mask_B3_scaffold_only",
    "C_scaffold_linker_warhead": "generation_mask_C_scaffold_linker_warhead",
}

REQUIRED_ADAPTED_KEYS = {
    "sample_id",
    "batch_size",
    "mask_level",
    "ligand_coords",
    "ligand_coords_centered",
    "ligand_atomic_numbers",
    "ligand_atom_mask",
    "ligand_bond_index",
    "ligand_bond_type",
    "protein_coords",
    "protein_coords_centered",
    "protein_atomic_numbers",
    "protein_atom_mask",
    "protein_residue_ids",
    "protein_chain_ids",
    "scaffold_atom_mask",
    "linker_atom_mask",
    "warhead_atom_mask",
    "generation_mask",
    "fixed_ligand_atom_mask",
    "ligand_context_mask",
    "ligand_target_mask",
    "ligand_reactive_atom_index",
    "protein_reactive_residue_label",
    "warhead_type_label",
    "coordinate_center",
    "valid_ligand_atom_count",
    "valid_protein_atom_count",
    "checkpoint_loaded",
    "model_initialized",
    "training_executed",
}


def _coordinate_center(batch: dict[str, Any]) -> torch.Tensor:
    ligand_coords = batch["ligand_atom_coords"]
    protein_coords = batch["protein_atom_coords"]
    ligand_mask = batch["ligand_atom_mask"]
    protein_mask = batch["protein_atom_mask"]
    centers = []
    for idx in range(ligand_coords.shape[0]):
        valid_ligand = ligand_coords[idx][ligand_mask[idx]]
        valid_protein = protein_coords[idx][protein_mask[idx]]
        combined = torch.cat([valid_ligand, valid_protein], dim=0)
        centers.append(combined.mean(dim=0))
    return torch.stack(centers, dim=0).to(dtype=torch.float32)


def adapt_covalent_batch_for_model_v0(batch: dict[str, Any], mask_level: str = "A_warhead_only") -> dict[str, Any]:
    if mask_level not in MASK_LEVEL_TO_BATCH_KEY:
        raise ValueError(f"unsupported mask_level: {mask_level}")
    ligand_mask = batch["ligand_atom_mask"].to(dtype=torch.bool)
    protein_mask = batch["protein_atom_mask"].to(dtype=torch.bool)
    generation_mask_key = MASK_LEVEL_TO_BATCH_KEY[mask_level]
    if mask_level == "B3_scaffold_only" and generation_mask_key not in batch:
        generation_mask = batch["scaffold_atom_mask"].to(dtype=torch.bool) & ligand_mask
    else:
        generation_mask = batch[generation_mask_key].to(dtype=torch.bool) & ligand_mask
    fixed_ligand_atom_mask = ligand_mask & ~generation_mask
    center = _coordinate_center(batch)
    ligand_coords = batch["ligand_atom_coords"].to(dtype=torch.float32)
    protein_coords = batch["protein_atom_coords"].to(dtype=torch.float32)
    return {
        "sample_id": list(batch["sample_id"]),
        "batch_size": len(batch["sample_id"]),
        "mask_level": mask_level,
        "ligand_coords": ligand_coords,
        "ligand_coords_centered": ligand_coords - center[:, None, :],
        "ligand_atomic_numbers": batch["ligand_atomic_numbers"].to(dtype=torch.long),
        "ligand_atom_mask": ligand_mask,
        "ligand_bond_index": batch["ligand_bond_index"],
        "ligand_bond_type": batch["ligand_bond_type"],
        "protein_coords": protein_coords,
        "protein_coords_centered": protein_coords - center[:, None, :],
        "protein_atomic_numbers": batch["protein_atomic_numbers"].to(dtype=torch.long),
        "protein_atom_mask": protein_mask,
        "protein_residue_ids": batch["protein_residue_ids"].to(dtype=torch.long),
        "protein_chain_ids": batch["protein_chain_ids"],
        "scaffold_atom_mask": batch["scaffold_atom_mask"].to(dtype=torch.bool) & ligand_mask,
        "linker_atom_mask": batch["linker_atom_mask"].to(dtype=torch.bool) & ligand_mask,
        "warhead_atom_mask": batch["warhead_atom_mask"].to(dtype=torch.bool) & ligand_mask,
        "generation_mask": generation_mask,
        "fixed_ligand_atom_mask": fixed_ligand_atom_mask,
        "ligand_context_mask": fixed_ligand_atom_mask.clone(),
        "ligand_target_mask": generation_mask.clone(),
        "ligand_reactive_atom_index": batch["ligand_reactive_atom_index"].to(dtype=torch.long),
        "protein_reactive_residue_label": list(batch["protein_reactive_residue_label"]),
        "warhead_type_label": list(batch["warhead_type_label"]),
        "coordinate_center": center,
        "valid_ligand_atom_count": ligand_mask.sum(dim=1).to(dtype=torch.long),
        "valid_protein_atom_count": protein_mask.sum(dim=1).to(dtype=torch.long),
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_executed": False,
    }


def validate_adapted_covalent_batch_v0(adapted: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_ADAPTED_KEYS - set(adapted))
    if missing:
        return False, [f"missing:{','.join(missing)}"]
    batch_size = adapted["batch_size"]
    ligand_coords = adapted["ligand_coords"]
    protein_coords = adapted["protein_coords"]
    ligand_mask = adapted["ligand_atom_mask"]
    protein_mask = adapted["protein_atom_mask"]
    generation_mask = adapted["generation_mask"]
    fixed_mask = adapted["fixed_ligand_atom_mask"]
    if batch_size != len(adapted["sample_id"]):
        reasons.append("batch_size_mismatch")
    if ligand_coords.ndim != 3 or ligand_coords.shape[-1] != 3:
        reasons.append("ligand_coords_shape_invalid")
    if protein_coords.ndim != 3 or protein_coords.shape[-1] != 3:
        reasons.append("protein_coords_shape_invalid")
    if adapted["ligand_coords_centered"].shape != ligand_coords.shape:
        reasons.append("ligand_centered_shape_invalid")
    if adapted["protein_coords_centered"].shape != protein_coords.shape:
        reasons.append("protein_centered_shape_invalid")
    if ligand_mask.shape != ligand_coords.shape[:2] or protein_mask.shape != protein_coords.shape[:2]:
        reasons.append("atom_mask_shape_invalid")
    for key in [
        "scaffold_atom_mask",
        "linker_atom_mask",
        "warhead_atom_mask",
        "generation_mask",
        "fixed_ligand_atom_mask",
        "ligand_context_mask",
        "ligand_target_mask",
    ]:
        if adapted[key].shape != ligand_mask.shape:
            reasons.append(f"{key}_shape_invalid")
    if adapted["coordinate_center"].shape != (batch_size, 3):
        reasons.append("coordinate_center_shape_invalid")
    if not torch.isfinite(ligand_coords[ligand_mask]).all():
        reasons.append("ligand_coords_not_finite")
    if not torch.isfinite(protein_coords[protein_mask]).all():
        reasons.append("protein_coords_not_finite")
    if torch.isnan(ligand_coords[ligand_mask]).any() or torch.isnan(protein_coords[protein_mask]).any():
        reasons.append("nan_in_valid_coords")
    if torch.isinf(ligand_coords[ligand_mask]).any() or torch.isinf(protein_coords[protein_mask]).any():
        reasons.append("inf_in_valid_coords")
    if (generation_mask & ~ligand_mask).any():
        reasons.append("generation_not_subset_ligand")
    if (fixed_mask & ~ligand_mask).any():
        reasons.append("fixed_not_subset_ligand")
    if (generation_mask & fixed_mask).any():
        reasons.append("generation_fixed_overlap")
    if not torch.equal(adapted["ligand_context_mask"], fixed_mask):
        reasons.append("context_not_fixed")
    if not torch.equal(adapted["ligand_target_mask"], generation_mask):
        reasons.append("target_not_generation")
    if not torch.equal(adapted["valid_ligand_atom_count"], ligand_mask.sum(dim=1).to(dtype=torch.long)):
        reasons.append("valid_ligand_count_mismatch")
    if not torch.equal(adapted["valid_protein_atom_count"], protein_mask.sum(dim=1).to(dtype=torch.long)):
        reasons.append("valid_protein_count_mismatch")
    reactive = adapted["ligand_reactive_atom_index"]
    for idx in range(batch_size):
        atom_idx = int(reactive[idx].item())
        if atom_idx < 0 or atom_idx >= ligand_mask.shape[1] or not bool(ligand_mask[idx, atom_idx].item()):
            reasons.append(f"reactive_not_in_ligand_mask:{idx}")
        if adapted["mask_level"] == "B3_scaffold_only":
            if atom_idx < 0 or atom_idx >= fixed_mask.shape[1] or not bool(fixed_mask[idx, atom_idx].item()):
                reasons.append(f"reactive_not_in_context_mask:{idx}")
            if atom_idx < 0 or atom_idx >= adapted["warhead_atom_mask"].shape[1] or not bool(
                adapted["warhead_atom_mask"][idx, atom_idx].item()
            ):
                reasons.append(f"reactive_not_in_warhead_mask:{idx}")
        elif atom_idx < 0 or atom_idx >= generation_mask.shape[1] or not bool(generation_mask[idx, atom_idx].item()):
            reasons.append(f"reactive_not_in_generation_mask:{idx}")
    if (generation_mask.sum(dim=1) == 0).any():
        reasons.append("empty_generation_mask")
    if adapted["checkpoint_loaded"] is not False:
        reasons.append("checkpoint_loaded")
    if adapted["model_initialized"] is not False:
        reasons.append("model_initialized")
    if adapted["training_executed"] is not False:
        reasons.append("training_executed")
    return not reasons, reasons
