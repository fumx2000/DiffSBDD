#!/usr/bin/env python
from __future__ import annotations

import json
from pathlib import Path


OUT_PATH = Path("data/processed/covalent_debug.jsonl")


def make_ligand_graph(num_atoms: int) -> dict:
    atom_cycle = ["C", "C", "N", "O", "C", "S", "C", "N", "O", "C"]
    atom_symbols = [atom_cycle[i % len(atom_cycle)] for i in range(num_atoms)]
    bonds = [
        {"atom1": atom_id, "atom2": atom_id + 1, "bond_type": "single"}
        for atom_id in range(num_atoms - 1)
    ]
    if num_atoms > 6:
        bonds.append({"atom1": 0, "atom2": 5, "bond_type": "single"})
    return {
        "atom_symbols": atom_symbols,
        "atom_names": [f"L{i}" for i in range(num_atoms)],
        "formal_charges": [0 for _ in range(num_atoms)],
        "bonds": bonds,
    }


def make_coords(sample_idx: int, num_atoms: int) -> list[list[float]]:
    coords = []
    offset = sample_idx * 0.15
    for atom_id in range(num_atoms):
        coords.append([
            round(offset + atom_id * 1.25, 3),
            round(((atom_id % 3) - 1) * 0.8, 3),
            round((atom_id % 2) * 0.45, 3),
        ])
    return coords


def make_pocket(sample_idx: int) -> dict:
    residue_id = f"A:{279 + sample_idx}"
    return {
        "coords": [
            [round(sample_idx * 0.2, 3), 0.0, 0.0],
            [round(sample_idx * 0.2 + 1.4, 3), 0.5, 0.2],
            [round(sample_idx * 0.2 + 2.8, 3), -0.4, 0.1],
        ],
        "one_hot": [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ],
        "atom_names": ["N", "CA", "SG"],
        "residue_ids": [residue_id, residue_id, residue_id],
        "residue_types": ["CYS", "CYS", "CYS"],
    }


def make_sample(sample_idx: int) -> dict:
    num_atoms = 9 + (sample_idx % 4)
    scaffold_end = 4 + (sample_idx % 2)
    linker_end = scaffold_end + 2 + (sample_idx % 2)

    scaffold_atoms = list(range(0, scaffold_end))
    linker_atoms = list(range(scaffold_end, linker_end))
    warhead_atoms = list(range(linker_end, num_atoms))
    ligand_reactive_atom_id = warhead_atoms[-1]
    residue_id = f"A:{279 + sample_idx}"

    return {
        "sample_id": f"covalent_debug_{sample_idx:03d}",
        "protein_pocket": make_pocket(sample_idx),
        "pre_reaction_ligand_graph": make_ligand_graph(num_atoms),
        "post_covalent_ligand_coords": make_coords(sample_idx, num_atoms),
        "reactive_residue_type": "CYS",
        "reactive_residue_id": residue_id,
        "reactive_atom_name": "SG",
        "reactive_atom_coord": [round(sample_idx * 0.2 + 2.8, 3), -0.4, 0.1],
        "warhead_type": "toy_acrylamide" if sample_idx % 2 == 0 else "toy_chloroacetamide",
        "ligand_reactive_atom_id": ligand_reactive_atom_id,
        "covalent_bond_atom_pair": [f"{residue_id}:SG", ligand_reactive_atom_id],
        "scaffold_atoms": scaffold_atoms,
        "linker_atoms": linker_atoms,
        "warhead_atoms": warhead_atoms,
    }


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    samples = [make_sample(i) for i in range(10)]
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, sort_keys=True) + "\n")
    print(f"wrote {len(samples)} samples to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
