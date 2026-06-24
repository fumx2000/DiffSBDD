from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import Dataset


NPZ_REQUIRED_KEYS = [
    "sample_id",
    "ligand_atom_coords",
    "ligand_atomic_numbers",
    "ligand_bond_index",
    "ligand_bond_type",
    "scaffold_atom_mask",
    "linker_atom_mask",
    "warhead_atom_mask",
    "generation_mask_A_warhead_only",
    "generation_mask_B_linker_warhead",
    "generation_mask_B2_scaffold_warhead",
    "generation_mask_C_scaffold_linker_warhead",
    "ligand_reactive_atom_index",
    "protein_atom_coords",
    "protein_atomic_numbers",
    "protein_residue_ids",
    "protein_chain_ids",
    "protein_reactive_residue_label",
    "warhead_type_label",
]

LIGAND_MASK_KEYS = [
    "scaffold_atom_mask",
    "linker_atom_mask",
    "warhead_atom_mask",
    "generation_mask_A_warhead_only",
    "generation_mask_B_linker_warhead",
    "generation_mask_B2_scaffold_warhead",
    "generation_mask_C_scaffold_linker_warhead",
]


class CovalentNPZDataset(Dataset):
    def __init__(self, sample_index_csv: str | Path):
        self.sample_index_csv = Path(sample_index_csv)
        if not self.sample_index_csv.is_file():
            raise FileNotFoundError(f"sample index not found: {self.sample_index_csv}")
        with self.sample_index_csv.open(newline="", encoding="utf-8") as handle:
            self.rows = list(csv.DictReader(handle))
        if not self.rows:
            raise ValueError("sample index contains no rows")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.rows[idx]
        npz_path = Path(row["npz_path"])
        if not npz_path.is_file():
            raise FileNotFoundError(f"npz not found: {npz_path}")
        with np.load(npz_path, allow_pickle=False) as data:
            missing = sorted(set(NPZ_REQUIRED_KEYS) - set(data.files))
            if missing:
                raise ValueError(f"{npz_path} missing keys: {missing}")
            sample: dict[str, Any] = {
                "sample_id": str(data["sample_id"].item()),
                "ligand_atom_coords": torch.as_tensor(np.array(data["ligand_atom_coords"]), dtype=torch.float32),
                "ligand_atomic_numbers": torch.as_tensor(np.array(data["ligand_atomic_numbers"]), dtype=torch.long),
                "ligand_bond_index": torch.as_tensor(np.array(data["ligand_bond_index"]), dtype=torch.long),
                "ligand_bond_type": torch.as_tensor(np.array(data["ligand_bond_type"]), dtype=torch.long),
                "ligand_reactive_atom_index": torch.as_tensor(int(data["ligand_reactive_atom_index"]), dtype=torch.long),
                "protein_atom_coords": torch.as_tensor(np.array(data["protein_atom_coords"]), dtype=torch.float32),
                "protein_atomic_numbers": torch.as_tensor(np.array(data["protein_atomic_numbers"]), dtype=torch.long),
                "protein_residue_ids": torch.as_tensor(np.array(data["protein_residue_ids"]), dtype=torch.long),
                "protein_chain_ids": [str(value) for value in data["protein_chain_ids"].tolist()],
                "protein_reactive_residue_label": str(data["protein_reactive_residue_label"].item()),
                "warhead_type_label": str(data["warhead_type_label"].item()),
            }
            for key in LIGAND_MASK_KEYS:
                sample[key] = torch.as_tensor(np.array(data[key]), dtype=torch.bool)
        return sample


def _pad_tensor_1d(values: list[torch.Tensor], pad_value: int | bool, dtype: torch.dtype) -> torch.Tensor:
    batch_size = len(values)
    max_len = max(value.shape[0] for value in values)
    output = torch.full((batch_size, max_len), pad_value, dtype=dtype)
    for idx, value in enumerate(values):
        output[idx, : value.shape[0]] = value.to(dtype=dtype)
    return output


def _pad_coords(values: list[torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    batch_size = len(values)
    max_len = max(value.shape[0] for value in values)
    output = torch.zeros((batch_size, max_len, 3), dtype=torch.float32)
    mask = torch.zeros((batch_size, max_len), dtype=torch.bool)
    for idx, value in enumerate(values):
        output[idx, : value.shape[0], :] = value.to(dtype=torch.float32)
        mask[idx, : value.shape[0]] = True
    return output, mask


def covalent_npz_collate_fn(samples: list[dict[str, Any]]) -> dict[str, Any]:
    ligand_coords, ligand_atom_mask = _pad_coords([sample["ligand_atom_coords"] for sample in samples])
    protein_coords, protein_atom_mask = _pad_coords([sample["protein_atom_coords"] for sample in samples])
    batch: dict[str, Any] = {
        "sample_id": [sample["sample_id"] for sample in samples],
        "ligand_atom_coords": ligand_coords,
        "ligand_atomic_numbers": _pad_tensor_1d([sample["ligand_atomic_numbers"] for sample in samples], 0, torch.long),
        "ligand_atom_mask": ligand_atom_mask,
        "ligand_reactive_atom_index": torch.stack([sample["ligand_reactive_atom_index"] for sample in samples]).to(dtype=torch.long),
        "protein_atom_coords": protein_coords,
        "protein_atomic_numbers": _pad_tensor_1d([sample["protein_atomic_numbers"] for sample in samples], 0, torch.long),
        "protein_atom_mask": protein_atom_mask,
        "protein_residue_ids": _pad_tensor_1d([sample["protein_residue_ids"] for sample in samples], 0, torch.long),
        "protein_chain_ids": [sample["protein_chain_ids"] for sample in samples],
        "protein_reactive_residue_label": [sample["protein_reactive_residue_label"] for sample in samples],
        "warhead_type_label": [sample["warhead_type_label"] for sample in samples],
        "ligand_bond_index": [sample["ligand_bond_index"] for sample in samples],
        "ligand_bond_type": [sample["ligand_bond_type"] for sample in samples],
    }
    for key in LIGAND_MASK_KEYS:
        batch[key] = _pad_tensor_1d([sample[key] for sample in samples], False, torch.bool)
    return batch
