#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import deque
from pathlib import Path

from rdkit import Chem


REPORT_COLUMNS = [
    "sdf_atom_index",
    "pdb_atom_name",
    "element",
    "x",
    "y",
    "z",
    "degree",
    "formal_charge",
    "neighbors",
    "bonds",
    "graph_distance_to_reactive_atom",
    "is_ring_atom",
    "is_aromatic",
    "suggested_role",
    "final_role",
    "annotation_hint",
    "notes",
]


def load_csv_by_atom_index(path: str | Path) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                atom_idx = int(row.get("sdf_atom_index", ""))
            except ValueError:
                continue
            rows[atom_idx] = row
    return rows


def load_molecule(ligand_sdf: str | Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(ligand_sdf), removeHs=False, sanitize=False)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None:
        raise ValueError(f"could not read ligand SDF: {ligand_sdf}")

    try:
        Chem.SanitizeMol(mol)
    except Exception as exc:  # noqa: BLE001 - keep curation report generation permissive.
        print(f"warning: RDKit sanitize failed; ring/aromatic hints may be incomplete: {exc}")
    return mol


def graph_distances(mol: Chem.Mol, start_atom_idx: int) -> dict[int, int]:
    if start_atom_idx < 0 or start_atom_idx >= mol.GetNumAtoms():
        raise ValueError(f"reactive_atom_id out of range: {start_atom_idx}")

    distances = {start_atom_idx: 0}
    queue: deque[int] = deque([start_atom_idx])
    while queue:
        atom_idx = queue.popleft()
        atom = mol.GetAtomWithIdx(atom_idx)
        for neighbor in atom.GetNeighbors():
            neighbor_idx = neighbor.GetIdx()
            if neighbor_idx in distances:
                continue
            distances[neighbor_idx] = distances[atom_idx] + 1
            queue.append(neighbor_idx)
    return distances


def bond_type_name(bond: Chem.Bond) -> str:
    return str(bond.GetBondType()).lower()


def atom_neighbors_and_bonds(atom: Chem.Atom) -> tuple[str, str]:
    neighbors: list[str] = []
    bonds: list[str] = []
    for bond in atom.GetBonds():
        other_idx = bond.GetOtherAtomIdx(atom.GetIdx())
        neighbors.append(str(other_idx))
        bonds.append(f"{other_idx}:{bond_type_name(bond)}")
    return ";".join(neighbors), ";".join(bonds)


def safe_is_ring_atom(atom: Chem.Atom) -> bool:
    try:
        return bool(atom.IsInRing())
    except Exception as exc:  # noqa: BLE001
        print(f"warning: ring membership failed for atom {atom.GetIdx()}: {exc}")
        return False


def safe_is_aromatic(atom: Chem.Atom) -> bool:
    try:
        return bool(atom.GetIsAromatic())
    except Exception as exc:  # noqa: BLE001
        print(f"warning: aromaticity check failed for atom {atom.GetIdx()}: {exc}")
        return False


def build_annotation_hint(
    atom_idx: int,
    distance: int | None,
    is_ring_atom: bool,
    is_aromatic: bool,
    reactive_atom_id: int,
) -> str:
    hints: list[str] = []
    if atom_idx == reactive_atom_id:
        hints.append("ligand_reactive_atom_candidate; must be warhead in final annotation")
    elif distance in {1, 2}:
        hints.append("near_reactive_atom; inspect for warhead")

    if is_ring_atom or is_aromatic:
        hints.append("possible_scaffold_core")
    return "; ".join(hints)


def build_report_rows(
    ligand_sdf: str | Path,
    annotation: str | Path,
    mapping_csv: str | Path,
    reactive_atom_id: int,
) -> list[dict[str, str]]:
    mol = load_molecule(ligand_sdf)
    annotation_rows = load_csv_by_atom_index(annotation)
    mapping_rows = load_csv_by_atom_index(mapping_csv)
    distances = graph_distances(mol, reactive_atom_id)

    rows: list[dict[str, str]] = []
    for atom in mol.GetAtoms():
        atom_idx = atom.GetIdx()
        mapping = mapping_rows.get(atom_idx, {})
        annotation_row = annotation_rows.get(atom_idx, {})
        neighbors, bonds = atom_neighbors_and_bonds(atom)
        distance = distances.get(atom_idx)
        is_ring_atom = safe_is_ring_atom(atom)
        is_aromatic = safe_is_aromatic(atom)

        rows.append(
            {
                "sdf_atom_index": str(atom_idx),
                "pdb_atom_name": mapping.get("pdb_atom_name", annotation_row.get("pdb_atom_name", "")),
                "element": mapping.get("element", atom.GetSymbol()),
                "x": mapping.get("x", annotation_row.get("x", "")),
                "y": mapping.get("y", annotation_row.get("y", "")),
                "z": mapping.get("z", annotation_row.get("z", "")),
                "degree": str(atom.GetDegree()),
                "formal_charge": str(atom.GetFormalCharge()),
                "neighbors": neighbors,
                "bonds": bonds,
                "graph_distance_to_reactive_atom": "" if distance is None else str(distance),
                "is_ring_atom": str(is_ring_atom),
                "is_aromatic": str(is_aromatic),
                "suggested_role": annotation_row.get("suggested_role", ""),
                "final_role": annotation_row.get("final_role", ""),
                "annotation_hint": build_annotation_hint(
                    atom_idx,
                    distance,
                    is_ring_atom,
                    is_aromatic,
                    reactive_atom_id,
                ),
                "notes": annotation_row.get("notes", ""),
            }
        )
    return rows


def write_report(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a ligand annotation report for manual final_role curation.")
    parser.add_argument("--ligand_sdf", type=Path, required=True)
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--mapping_csv", type=Path, required=True)
    parser.add_argument("--reactive_atom_id", type=int, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(
        "warning: current SDF was extracted from PDB HETATM + CONECT; "
        "it is post-covalent-compatible bound geometry and bond order may be unreliable. "
        "annotation_hint is for manual review only and does not modify final_role."
    )
    rows = build_report_rows(args.ligand_sdf, args.annotation, args.mapping_csv, args.reactive_atom_id)
    write_report(rows, args.output_csv)
    print(f"wrote annotation report: {args.output_csv}")
    print(f"rows: {len(rows)}")
    print(f"reactive_atom_id: {args.reactive_atom_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
