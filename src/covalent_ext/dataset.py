from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from covalent_ext.masking import build_four_level_mask
from covalent_ext.schema import MaskResult, MaskType


class CovalentJsonlDataset:
    def __init__(self, jsonl_path: str | Path):
        self.jsonl_path = Path(jsonl_path)
        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"Covalent JSONL dataset not found: {self.jsonl_path}")

        self.samples: list[dict[str, Any]] = []
        with self.jsonl_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                sample = json.loads(stripped)
                self._validate_sample(sample, line_number)
                self.samples.append(sample)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        return self.samples[idx]

    def num_ligand_atoms(self, sample: dict[str, Any]) -> int:
        return len(sample["pre_reaction_ligand_graph"]["atom_symbols"])

    def build_mask(self, sample: dict[str, Any], mask_type: MaskType) -> MaskResult:
        return build_four_level_mask(
            mask_type=mask_type,
            scaffold_atoms=sample["scaffold_atoms"],
            linker_atoms=sample["linker_atoms"],
            warhead_atoms=sample["warhead_atoms"],
            num_ligand_atoms=self.num_ligand_atoms(sample),
        )

    def build_all_masks(self, sample: dict[str, Any]) -> dict[MaskType, MaskResult]:
        return {
            mask_type: self.build_mask(sample, mask_type)
            for mask_type in ("A", "B", "B2", "C")
        }

    @staticmethod
    def _validate_sample(sample: dict[str, Any], line_number: int) -> None:
        required_fields = {
            "sample_id",
            "protein_pocket",
            "pre_reaction_ligand_graph",
            "post_covalent_ligand_coords",
            "reactive_residue_type",
            "reactive_residue_id",
            "reactive_atom_name",
            "reactive_atom_coord",
            "warhead_type",
            "ligand_reactive_atom_id",
            "covalent_bond_atom_pair",
            "scaffold_atoms",
            "linker_atoms",
            "warhead_atoms",
        }
        missing = sorted(required_fields - sample.keys())
        if missing:
            raise ValueError(f"Line {line_number} is missing required fields: {missing}")

        graph = sample["pre_reaction_ligand_graph"]
        if "atom_symbols" not in graph:
            raise ValueError(f"Line {line_number} pre_reaction_ligand_graph is missing atom_symbols")

        num_atoms = len(graph["atom_symbols"])
        if len(sample["post_covalent_ligand_coords"]) != num_atoms:
            raise ValueError(
                f"Line {line_number} coordinate count does not match ligand atom count"
            )

