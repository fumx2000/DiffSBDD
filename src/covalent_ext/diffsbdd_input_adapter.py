from __future__ import annotations

from typing import Any

import torch


ATOM_ENCODER_CROSSDOCK_FULL = {
    "C": 0,
    "N": 1,
    "O": 2,
    "S": 3,
    "B": 4,
    "Br": 5,
    "Cl": 6,
    "P": 7,
    "I": 8,
    "F": 9,
    "others": 10,
}

ATOMIC_NUMBER_TO_SYMBOL = {
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    15: "P",
    16: "S",
    17: "Cl",
    35: "Br",
    53: "I",
}

COMMON_DIFFSBDD_LIKE_KEYS = {
    "sample_id",
    "batch_size",
    "mask_level",
    "ligand_x",
    "ligand_h",
    "ligand_mask",
    "protein_x",
    "protein_h",
    "protein_mask",
    "generation_mask",
    "fixed_ligand_atom_mask",
    "ligand_context_mask",
    "ligand_target_mask",
    "coordinate_center",
    "ligand_reactive_atom_index",
    "protein_reactive_residue_label",
    "warhead_type_label",
}

PREVIEW_DIFFSBDD_KEYS = {
    "ligand",
    "pocket",
    "lig_coords",
    "lig_one_hot",
    "lig_mask",
    "pocket_coords",
    "pocket_one_hot",
    "pocket_mask",
    "num_lig_atoms",
    "num_pocket_nodes",
    "xh_ligand",
    "xh_pocket",
    "lig_fixed",
    "generation_mask_flat",
    "ligand_context_mask_flat",
    "ligand_target_mask_flat",
    "edge_mask_required",
    "edge_index_constructed_by_dynamics",
    "checkpoint_loaded",
    "diffsbdd_model_initialized",
    "diffsbdd_model_called",
    "training_executed",
}

DIRECT_MAPPING_FIELDS = [
    "ligand.x <- model_input.ligand_x[ligand_mask]",
    "ligand.size <- ligand_mask.sum(dim=1)",
    "ligand.mask <- flattened ligand batch indices",
    "pocket.x <- model_input.protein_x[protein_mask]",
    "pocket.size <- protein_mask.sum(dim=1)",
    "pocket.mask <- flattened protein batch indices",
    "lig_fixed <- fixed_ligand_atom_mask flattened over ligand_mask",
    "generation_mask_flat <- generation_mask flattened over ligand_mask",
    "ligand_context_mask_flat <- ligand_context_mask flattened over ligand_mask",
    "ligand_target_mask_flat <- ligand_target_mask flattened over ligand_mask",
    "coordinate_center <- model_input.coordinate_center",
]

MISSING_OR_UNCERTAIN_FIELDS = [
    "exact DiffSBDD dataset config must choose crossdock vs crossdock_full pocket representation",
    "ligand one-hot vocabulary uses crossdock_full preview mapping and should be confirmed against the target checkpoint config later",
    "pocket one-hot vocabulary uses protein atom atomic numbers as crossdock_full atom types; CA residue mode would require residue encodings",
    "edge_mask is not a top-level LigandPocketDDPM/DDPM input; EGNNDynamics constructs edges internally from masks",
    "names/receptors metadata are needed for some sampling/evaluation utilities but not for forward loss",
    "virtual_nodes mode is not represented in this preview",
]


def _flatten_padded(values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return values[mask.to(dtype=torch.bool)]


def _flatten_batch_indices(mask: torch.Tensor) -> torch.Tensor:
    mask = mask.to(dtype=torch.bool)
    pieces = []
    for idx in range(mask.shape[0]):
        pieces.append(torch.full((int(mask[idx].sum().item()),), idx, dtype=torch.long, device=mask.device))
    return torch.cat(pieces, dim=0) if pieces else torch.empty(0, dtype=torch.long, device=mask.device)


def _one_hot_from_atomic_numbers(atomic_numbers: torch.Tensor) -> torch.Tensor:
    indices = []
    for value in atomic_numbers.detach().cpu().tolist():
        symbol = ATOMIC_NUMBER_TO_SYMBOL.get(int(value), "others")
        indices.append(ATOM_ENCODER_CROSSDOCK_FULL.get(symbol, ATOM_ENCODER_CROSSDOCK_FULL["others"]))
    index_tensor = torch.tensor(indices, dtype=torch.long, device=atomic_numbers.device)
    return torch.nn.functional.one_hot(index_tensor, num_classes=len(ATOM_ENCODER_CROSSDOCK_FULL)).to(dtype=torch.float32)


def build_diffsbdd_like_input_from_covalent_v0(model_input: dict[str, Any]) -> dict[str, Any]:
    ligand_mask = model_input["ligand_mask"].to(dtype=torch.bool)
    protein_mask = model_input["protein_mask"].to(dtype=torch.bool)
    lig_coords = _flatten_padded(model_input["ligand_x"], ligand_mask).to(dtype=torch.float32)
    lig_atomic = _flatten_padded(model_input["ligand_h"], ligand_mask).to(dtype=torch.long)
    pocket_coords = _flatten_padded(model_input["protein_x"], protein_mask).to(dtype=torch.float32)
    pocket_atomic = _flatten_padded(model_input["protein_h"], protein_mask).to(dtype=torch.long)
    lig_one_hot = _one_hot_from_atomic_numbers(lig_atomic)
    pocket_one_hot = _one_hot_from_atomic_numbers(pocket_atomic)
    lig_mask = _flatten_batch_indices(ligand_mask)
    pocket_mask = _flatten_batch_indices(protein_mask)
    generation_mask_flat = _flatten_padded(model_input["generation_mask"], ligand_mask).to(dtype=torch.bool)
    context_mask_flat = _flatten_padded(model_input["ligand_context_mask"], ligand_mask).to(dtype=torch.bool)
    target_mask_flat = _flatten_padded(model_input["ligand_target_mask"], ligand_mask).to(dtype=torch.bool)
    fixed_mask_flat = _flatten_padded(model_input["fixed_ligand_atom_mask"], ligand_mask).to(dtype=torch.float32).unsqueeze(1)
    ligand = {
        "x": lig_coords,
        "one_hot": lig_one_hot,
        "size": ligand_mask.sum(dim=1).to(dtype=torch.long),
        "mask": lig_mask,
    }
    pocket = {
        "x": pocket_coords,
        "one_hot": pocket_one_hot,
        "size": protein_mask.sum(dim=1).to(dtype=torch.long),
        "mask": pocket_mask,
    }
    return {
        "sample_id": list(model_input["sample_id"]),
        "batch_size": int(model_input["batch_size"]),
        "mask_level": model_input["mask_level"],
        "ligand_x": model_input["ligand_x"],
        "ligand_h": model_input["ligand_h"],
        "ligand_mask": ligand_mask,
        "protein_x": model_input["protein_x"],
        "protein_h": model_input["protein_h"],
        "protein_mask": protein_mask,
        "generation_mask": model_input["generation_mask"].to(dtype=torch.bool),
        "fixed_ligand_atom_mask": model_input["fixed_ligand_atom_mask"].to(dtype=torch.bool),
        "ligand_context_mask": model_input["ligand_context_mask"].to(dtype=torch.bool),
        "ligand_target_mask": model_input["ligand_target_mask"].to(dtype=torch.bool),
        "coordinate_center": model_input["coordinate_center"],
        "ligand_reactive_atom_index": model_input["ligand_reactive_atom_index"],
        "protein_reactive_residue_label": list(model_input["protein_reactive_residue_label"]),
        "warhead_type_label": list(model_input["warhead_type_label"]),
        "ligand": ligand,
        "pocket": pocket,
        "lig_coords": lig_coords,
        "lig_one_hot": lig_one_hot,
        "lig_mask": lig_mask,
        "pocket_coords": pocket_coords,
        "pocket_one_hot": pocket_one_hot,
        "pocket_mask": pocket_mask,
        "num_lig_atoms": ligand["size"],
        "num_pocket_nodes": pocket["size"],
        "xh_ligand": torch.cat([lig_coords, lig_one_hot], dim=1),
        "xh_pocket": torch.cat([pocket_coords, pocket_one_hot], dim=1),
        "lig_fixed": fixed_mask_flat,
        "generation_mask_flat": generation_mask_flat,
        "ligand_context_mask_flat": context_mask_flat,
        "ligand_target_mask_flat": target_mask_flat,
        "edge_mask_required": False,
        "edge_index_constructed_by_dynamics": True,
        "direct_mapping_fields": list(DIRECT_MAPPING_FIELDS),
        "missing_or_uncertain_fields": list(MISSING_OR_UNCERTAIN_FIELDS),
        "checkpoint_loaded": False,
        "diffsbdd_model_initialized": False,
        "diffsbdd_model_called": False,
        "training_executed": False,
    }


def validate_diffsbdd_like_input_v0(diffsbdd_like: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing_common = sorted(COMMON_DIFFSBDD_LIKE_KEYS - set(diffsbdd_like))
    missing_preview = sorted(PREVIEW_DIFFSBDD_KEYS - set(diffsbdd_like))
    if missing_common:
        reasons.append(f"missing_common:{','.join(missing_common)}")
    if missing_preview:
        reasons.append(f"missing_preview:{','.join(missing_preview)}")
    if reasons:
        return False, reasons
    ligand = diffsbdd_like["ligand"]
    pocket = diffsbdd_like["pocket"]
    ligand_mask = diffsbdd_like["ligand_mask"].to(dtype=torch.bool)
    protein_mask = diffsbdd_like["protein_mask"].to(dtype=torch.bool)
    generation_mask = diffsbdd_like["generation_mask"].to(dtype=torch.bool)
    context_mask = diffsbdd_like["ligand_context_mask"].to(dtype=torch.bool)
    target_mask = diffsbdd_like["ligand_target_mask"].to(dtype=torch.bool)
    if diffsbdd_like["ligand_x"].shape[-1] != 3 or diffsbdd_like["protein_x"].shape[-1] != 3:
        reasons.append("padded_coordinate_shape_invalid")
    if ligand["x"].ndim != 2 or ligand["x"].shape[1] != 3:
        reasons.append("ligand_x_flat_shape_invalid")
    if pocket["x"].ndim != 2 or pocket["x"].shape[1] != 3:
        reasons.append("pocket_x_flat_shape_invalid")
    if ligand["one_hot"].shape[0] != ligand["x"].shape[0] or ligand["one_hot"].shape[1] != len(ATOM_ENCODER_CROSSDOCK_FULL):
        reasons.append("ligand_one_hot_shape_invalid")
    if pocket["one_hot"].shape[0] != pocket["x"].shape[0] or pocket["one_hot"].shape[1] != len(ATOM_ENCODER_CROSSDOCK_FULL):
        reasons.append("pocket_one_hot_shape_invalid")
    if ligand["mask"].shape[0] != ligand["x"].shape[0] or pocket["mask"].shape[0] != pocket["x"].shape[0]:
        reasons.append("flat_mask_shape_invalid")
    if not torch.equal(ligand["size"], ligand_mask.sum(dim=1).to(dtype=torch.long)):
        reasons.append("ligand_size_mismatch")
    if not torch.equal(pocket["size"], protein_mask.sum(dim=1).to(dtype=torch.long)):
        reasons.append("pocket_size_mismatch")
    if diffsbdd_like["lig_coords"].shape != ligand["x"].shape or diffsbdd_like["pocket_coords"].shape != pocket["x"].shape:
        reasons.append("alias_coordinate_shape_mismatch")
    if diffsbdd_like["xh_ligand"].shape[0] != ligand["x"].shape[0] or diffsbdd_like["xh_ligand"].shape[1] != 3 + len(ATOM_ENCODER_CROSSDOCK_FULL):
        reasons.append("xh_ligand_shape_invalid")
    if diffsbdd_like["xh_pocket"].shape[0] != pocket["x"].shape[0] or diffsbdd_like["xh_pocket"].shape[1] != 3 + len(ATOM_ENCODER_CROSSDOCK_FULL):
        reasons.append("xh_pocket_shape_invalid")
    if (generation_mask & ~ligand_mask).any():
        reasons.append("generation_not_subset_ligand")
    if (context_mask & target_mask).any():
        reasons.append("context_target_overlap")
    if not torch.equal(generation_mask, target_mask):
        reasons.append("generation_target_mismatch")
    if diffsbdd_like["generation_mask_flat"].shape[0] != ligand["x"].shape[0]:
        reasons.append("generation_mask_flat_shape_invalid")
    if diffsbdd_like["lig_fixed"].shape != (ligand["x"].shape[0], 1):
        reasons.append("lig_fixed_shape_invalid")
    target_count = int(target_mask.sum().item())
    if target_count <= 0:
        reasons.append("target_atom_count_zero")
    if not torch.isfinite(ligand["x"]).all() or not torch.isfinite(pocket["x"]).all():
        reasons.append("coordinates_not_finite")
    if diffsbdd_like["checkpoint_loaded"] is not False:
        reasons.append("checkpoint_loaded")
    if diffsbdd_like["diffsbdd_model_initialized"] is not False:
        reasons.append("diffsbdd_model_initialized")
    if diffsbdd_like["diffsbdd_model_called"] is not False:
        reasons.append("diffsbdd_model_called")
    if diffsbdd_like["training_executed"] is not False:
        reasons.append("training_executed")
    return not reasons, reasons
