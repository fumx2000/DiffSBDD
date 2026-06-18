#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from Bio.PDB import PDBParser
from rdkit import Chem


def parse_atom_indices(value: str) -> list[int]:
    tokens = value.replace(",", " ").split()
    if not tokens:
        return []
    return [int(token) for token in tokens]


def resolve_manifest_path(path_value: str, manifest_path: Path) -> Path:
    path = Path(path_value)
    if path.exists():
        return path
    candidate = manifest_path.parent / path
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Could not resolve path from manifest: {path_value}")


def get_reactive_atom_coord(
    protein_pdb_path: Path,
    chain_id: str,
    residue_id: int,
    residue_type: str,
    atom_name: str,
) -> list[float]:
    model = PDBParser(QUIET=True).get_structure("", protein_pdb_path)[0]
    residue = model[chain_id][(" ", residue_id, " ")]
    if residue.get_resname() != residue_type:
        raise ValueError(
            f"Residue type mismatch for {chain_id}:{residue_id}: "
            f"manifest={residue_type}, pdb={residue.get_resname()}"
        )
    atom = residue[atom_name]
    return [round(float(x), 4) for x in atom.get_coord().tolist()]


def extract_reactive_residue_pocket(
    protein_pdb_path: Path,
    chain_id: str,
    residue_id: int,
) -> dict[str, Any]:
    model = PDBParser(QUIET=True).get_structure("", protein_pdb_path)[0]
    residue = model[chain_id][(" ", residue_id, " ")]
    residue_label = f"{chain_id}:{residue_id}"
    atoms = list(residue.get_atoms())
    return {
        "coords": [[round(float(x), 4) for x in atom.get_coord().tolist()] for atom in atoms],
        "atom_names": [atom.get_name() for atom in atoms],
        "residue_ids": [residue_label for _ in atoms],
        "residue_types": [residue.get_resname() for _ in atoms],
    }


def bond_type_to_string(bond: Chem.Bond) -> str:
    bond_type = bond.GetBondType()
    if bond_type == Chem.BondType.SINGLE:
        return "single"
    if bond_type == Chem.BondType.DOUBLE:
        return "double"
    if bond_type == Chem.BondType.TRIPLE:
        return "triple"
    if bond_type == Chem.BondType.AROMATIC:
        return "aromatic"
    return str(bond_type).lower()


def extract_ligand(ligand_sdf_path: Path) -> tuple[dict[str, Any], list[list[float]]]:
    mol = Chem.SDMolSupplier(str(ligand_sdf_path), sanitize=False)[0]
    if mol is None:
        raise ValueError(f"Could not read ligand SDF: {ligand_sdf_path}")
    if mol.GetNumConformers() == 0:
        raise ValueError(f"Ligand has no conformer coordinates: {ligand_sdf_path}")

    graph = {
        "atom_symbols": [atom.GetSymbol() for atom in mol.GetAtoms()],
        "atom_names": [f"L{atom.GetIdx()}" for atom in mol.GetAtoms()],
        "formal_charges": [int(atom.GetFormalCharge()) for atom in mol.GetAtoms()],
        "bonds": [
            {
                "atom1": int(bond.GetBeginAtomIdx()),
                "atom2": int(bond.GetEndAtomIdx()),
                "bond_type": bond_type_to_string(bond),
            }
            for bond in mol.GetBonds()
        ],
    }
    coords = [
        [round(float(x), 4) for x in mol.GetConformer().GetAtomPosition(i)]
        for i in range(mol.GetNumAtoms())
    ]
    return graph, coords


def build_sample(row: dict[str, str], manifest_path: Path) -> dict[str, Any]:
    protein_pdb_path = resolve_manifest_path(row["protein_pdb_path"], manifest_path)
    ligand_sdf_path = resolve_manifest_path(row["ligand_sdf_path"], manifest_path)
    chain_id = row["reactive_residue_chain"]
    residue_id = int(row["reactive_residue_id"])
    residue_type = row["reactive_residue_type"]
    atom_name = row["reactive_atom_name"]
    ligand_reactive_atom_id = int(row["ligand_reactive_atom_id"])

    graph, coords = extract_ligand(ligand_sdf_path)
    reactive_atom_coord = get_reactive_atom_coord(
        protein_pdb_path, chain_id, residue_id, residue_type, atom_name
    )
    reactive_residue_label = f"{chain_id}:{residue_id}"

    return {
        "sample_id": row["sample_id"],
        "protein_pocket": extract_reactive_residue_pocket(protein_pdb_path, chain_id, residue_id),
        "pre_reaction_ligand_graph": graph,
        "post_covalent_ligand_coords": coords,
        "reactive_residue_type": residue_type,
        "reactive_residue_id": reactive_residue_label,
        "reactive_atom_name": atom_name,
        "reactive_atom_coord": reactive_atom_coord,
        "warhead_type": row["warhead_type"],
        "ligand_reactive_atom_id": ligand_reactive_atom_id,
        "covalent_bond_atom_pair": [f"{reactive_residue_label}:{atom_name}", ligand_reactive_atom_id],
        "scaffold_atoms": parse_atom_indices(row["scaffold_atoms"]),
        "linker_atoms": parse_atom_indices(row["linker_atoms"]),
        "warhead_atoms": parse_atom_indices(row["warhead_atoms"]),
    }


def build_from_manifest(manifest_path: str | Path, output_path: str | Path) -> list[dict[str, Any]]:
    manifest_path = Path(manifest_path)
    output_path = Path(output_path)
    samples = []
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            samples.append(build_sample(row, manifest_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, sort_keys=True) + "\n")
    return samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a small covalent processed JSONL from a manual manifest.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    samples = build_from_manifest(args.manifest, args.output)
    print(f"wrote {len(samples)} samples to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
