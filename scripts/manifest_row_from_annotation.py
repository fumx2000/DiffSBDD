#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


MANIFEST_COLUMNS = [
    "sample_id",
    "protein_pdb_path",
    "ligand_sdf_path",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "warhead_type",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
]

ROLE_COLUMNS = {
    "scaffold": "scaffold_atoms",
    "linker": "linker_atoms",
    "warhead": "warhead_atoms",
}


class ManifestRowError(ValueError):
    pass


def load_annotation(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def atoms_by_final_role(rows: list[dict[str, str]]) -> dict[str, list[int]]:
    atoms = {role: [] for role in ROLE_COLUMNS}
    for row_number, row in enumerate(rows, start=2):
        try:
            atom_idx = int(row.get("sdf_atom_index", ""))
        except ValueError as exc:
            raise ManifestRowError(f"row {row_number}: sdf_atom_index is not an integer") from exc

        role = row.get("final_role", "").strip().lower()
        if role in atoms:
            atoms[role].append(atom_idx)
        elif role not in {"", "unassigned"}:
            raise ManifestRowError(f"row {row_number}: unsupported final_role {role!r}")
    return atoms


def format_atom_indices(atom_indices: list[int]) -> str:
    return " ".join(str(atom_idx) for atom_idx in sorted(atom_indices))


def build_manifest_row(
    *,
    sample_id: str,
    protein_pdb_path: str,
    ligand_sdf_path: str,
    annotation: str | Path,
    reactive_residue_chain: str,
    reactive_residue_id: str,
    reactive_residue_type: str,
    reactive_atom_name: str,
    ligand_reactive_atom_id: int,
    warhead_type: str,
) -> dict[str, str]:
    atoms = atoms_by_final_role(load_annotation(annotation))
    missing = [role for role, indices in atoms.items() if not indices]
    if missing:
        raise ManifestRowError(
            "annotation final_role must include non-empty scaffold/linker/warhead groups; "
            f"missing: {', '.join(missing)}"
        )
    if ligand_reactive_atom_id not in atoms["warhead"]:
        raise ManifestRowError("ligand_reactive_atom_id is not in warhead_atoms")

    return {
        "sample_id": sample_id,
        "protein_pdb_path": protein_pdb_path,
        "ligand_sdf_path": ligand_sdf_path,
        "reactive_residue_chain": reactive_residue_chain,
        "reactive_residue_id": str(reactive_residue_id),
        "reactive_residue_type": reactive_residue_type,
        "reactive_atom_name": reactive_atom_name,
        "ligand_reactive_atom_id": str(ligand_reactive_atom_id),
        "warhead_type": warhead_type,
        "scaffold_atoms": format_atom_indices(atoms["scaffold"]),
        "linker_atoms": format_atom_indices(atoms["linker"]),
        "warhead_atoms": format_atom_indices(atoms["warhead"]),
    }


def write_manifest_row(row: dict[str, str]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
    writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print one manifest CSV row from a completed annotation CSV.")
    parser.add_argument("--sample_id", required=True)
    parser.add_argument("--protein_pdb_path", required=True)
    parser.add_argument("--ligand_sdf_path", required=True)
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--reactive_residue_chain", required=True)
    parser.add_argument("--reactive_residue_id", required=True)
    parser.add_argument("--reactive_residue_type", required=True)
    parser.add_argument("--reactive_atom_name", required=True)
    parser.add_argument("--ligand_reactive_atom_id", type=int, required=True)
    parser.add_argument("--warhead_type", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        row = build_manifest_row(
            sample_id=args.sample_id,
            protein_pdb_path=args.protein_pdb_path,
            ligand_sdf_path=args.ligand_sdf_path,
            annotation=args.annotation,
            reactive_residue_chain=args.reactive_residue_chain,
            reactive_residue_id=args.reactive_residue_id,
            reactive_residue_type=args.reactive_residue_type,
            reactive_atom_name=args.reactive_atom_name,
            ligand_reactive_atom_id=args.ligand_reactive_atom_id,
            warhead_type=args.warhead_type,
        )
    except ManifestRowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_manifest_row(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
