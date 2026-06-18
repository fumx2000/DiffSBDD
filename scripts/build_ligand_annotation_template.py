#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from rdkit import Chem


FIELDNAMES = [
    "sdf_atom_index",
    "pdb_atom_name",
    "element",
    "x",
    "y",
    "z",
    "neighbors",
    "suggested_role",
    "final_role",
    "notes",
]


def read_mapping(mapping_csv: str | Path) -> dict[int, dict[str, str]]:
    with Path(mapping_csv).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {int(row["sdf_atom_index"]): row for row in rows}


def ligand_neighbors(ligand_sdf: str | Path) -> dict[int, str]:
    mol = Chem.SDMolSupplier(str(ligand_sdf), sanitize=False)[0]
    if mol is None:
        raise ValueError(f"Could not read ligand SDF: {ligand_sdf}")

    out: dict[int, str] = {}
    for atom in mol.GetAtoms():
        entries = []
        for bond in atom.GetBonds():
            other_idx = bond.GetOtherAtomIdx(atom.GetIdx())
            entries.append(f"{other_idx}:{str(bond.GetBondType()).lower()}")
        out[atom.GetIdx()] = ";".join(entries)
    return out


def build_annotation_template(
    ligand_sdf: str | Path,
    mapping_csv: str | Path,
    output: str | Path,
    ligand_reactive_atom_id: int,
) -> None:
    mapping = read_mapping(mapping_csv)
    neighbors = ligand_neighbors(ligand_sdf)

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for atom_idx in sorted(mapping):
            row = mapping[atom_idx]
            suggested_role = "unassigned"
            notes = ""
            if atom_idx == ligand_reactive_atom_id:
                suggested_role = "warhead_candidate / ligand_reactive_atom_candidate"
                notes = "PDB LINK identifies this atom as covalent partner candidate; confirm manually."
            writer.writerow(
                {
                    "sdf_atom_index": atom_idx,
                    "pdb_atom_name": row["pdb_atom_name"],
                    "element": row["element"],
                    "x": row["x"],
                    "y": row["y"],
                    "z": row["z"],
                    "neighbors": neighbors.get(atom_idx, ""),
                    "suggested_role": suggested_role,
                    "final_role": "",
                    "notes": notes,
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a ligand atom annotation template from SDF and atom mapping.")
    parser.add_argument("--ligand_sdf", type=Path, required=True)
    parser.add_argument("--mapping_csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ligand_reactive_atom_id", type=int, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    build_annotation_template(
        ligand_sdf=args.ligand_sdf,
        mapping_csv=args.mapping_csv,
        output=args.output,
        ligand_reactive_atom_id=args.ligand_reactive_atom_id,
    )
    print(f"wrote annotation template: {args.output}")
    print(f"ligand_reactive_atom_candidate: {args.ligand_reactive_atom_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
