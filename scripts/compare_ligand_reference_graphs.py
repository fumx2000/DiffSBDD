#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from rdkit import Chem


SUMMARY_COLUMNS = ["section", "key", "value", "note"]


@dataclass(frozen=True)
class GraphSummary:
    atom_count: int
    element_count: Counter[str]
    bond_count: int
    bond_order_summary: Counter[str]
    ring_atom_count: int | None
    aromatic_atom_count: int | None


def load_mol(path: str | Path, *, sanitize: bool) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=sanitize)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None and sanitize:
        print(f"warning: sanitized read failed for {path}; retrying sanitize=False")
        return load_mol(path, sanitize=False)
    if mol is None:
        raise ValueError(f"could not read SDF: {path}")
    if not sanitize:
        try:
            Chem.SanitizeMol(mol)
        except Exception as exc:  # noqa: BLE001
            print(f"warning: RDKit sanitize failed for {path}: {exc}")
    return mol


def bond_order_name(bond: Chem.Bond) -> str:
    return str(bond.GetBondType()).lower()


def summarize_graph(mol: Chem.Mol) -> GraphSummary:
    ring_atom_count: int | None
    aromatic_atom_count: int | None
    try:
        ring_atom_count = sum(1 for atom in mol.GetAtoms() if atom.IsInRing())
    except Exception as exc:  # noqa: BLE001
        print(f"warning: ring summary failed: {exc}")
        ring_atom_count = None
    try:
        aromatic_atom_count = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    except Exception as exc:  # noqa: BLE001
        print(f"warning: aromatic summary failed: {exc}")
        aromatic_atom_count = None

    return GraphSummary(
        atom_count=mol.GetNumAtoms(),
        element_count=Counter(atom.GetSymbol() for atom in mol.GetAtoms()),
        bond_count=mol.GetNumBonds(),
        bond_order_summary=Counter(bond_order_name(bond) for bond in mol.GetBonds()),
        ring_atom_count=ring_atom_count,
        aromatic_atom_count=aromatic_atom_count,
    )


def load_mapping(path: str | Path) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows[int(row["sdf_atom_index"])] = row
    return rows


def atom_signature(mol: Chem.Mol, atom_idx: int) -> tuple[str, int, tuple[str, ...], tuple[str, ...]]:
    atom = mol.GetAtomWithIdx(atom_idx)
    neighbor_elements = sorted(neighbor.GetSymbol() for neighbor in atom.GetNeighbors())
    bond_orders = sorted(bond_order_name(bond) for bond in atom.GetBonds())
    return atom.GetSymbol(), atom.GetDegree(), tuple(neighbor_elements), tuple(bond_orders)


def candidate_reference_atoms(
    extracted: Chem.Mol,
    reference: Chem.Mol,
    extracted_atom_idx: int,
) -> tuple[list[int], tuple[str, int, tuple[str, ...], tuple[str, ...]]]:
    signature = atom_signature(extracted, extracted_atom_idx)
    candidates = [
        atom.GetIdx()
        for atom in reference.GetAtoms()
        if atom_signature(reference, atom.GetIdx()) == signature
    ]
    return candidates, signature


def heavy_atom_order_candidate(
    extracted: Chem.Mol,
    reference: Chem.Mol,
    extracted_atom_idx: int,
) -> int | None:
    extracted_heavy = [atom.GetIdx() for atom in extracted.GetAtoms() if atom.GetSymbol() != "H"]
    reference_heavy = [atom.GetIdx() for atom in reference.GetAtoms() if atom.GetSymbol() != "H"]
    extracted_elements = [extracted.GetAtomWithIdx(atom_idx).GetSymbol() for atom_idx in extracted_heavy]
    reference_elements = [reference.GetAtomWithIdx(atom_idx).GetSymbol() for atom_idx in reference_heavy]
    if extracted_elements != reference_elements:
        return None
    try:
        heavy_position = extracted_heavy.index(extracted_atom_idx)
    except ValueError:
        return None
    return reference_heavy[heavy_position]


def atom_local_graph_summary(mol: Chem.Mol, atom_idx: int) -> str:
    atom = mol.GetAtomWithIdx(atom_idx)
    parts = []
    for bond in atom.GetBonds():
        other_idx = bond.GetOtherAtomIdx(atom_idx)
        other = mol.GetAtomWithIdx(other_idx)
        parts.append(f"{other_idx}:{other.GetSymbol()}:{bond_order_name(bond)}")
    return "; ".join(parts)


def append_summary(rows: list[dict[str, str]], section: str, key: str, value: object, note: str = "") -> None:
    rows.append({"section": section, "key": key, "value": str(value), "note": note})


def format_counter(counter: Counter[str]) -> str:
    return "; ".join(f"{key}:{counter[key]}" for key in sorted(counter))


def compare_graphs(
    extracted_sdf: str | Path,
    reference_sdf: str | Path,
    mapping_csv: str | Path,
    reactive_atom_id: int,
) -> tuple[list[dict[str, str]], list[str]]:
    extracted = load_mol(extracted_sdf, sanitize=False)
    reference = load_mol(reference_sdf, sanitize=True)
    extracted_summary = summarize_graph(extracted)
    reference_summary = summarize_graph(reference)
    mapping = load_mapping(mapping_csv)

    rows: list[dict[str, str]] = []
    warnings: list[str] = []
    for name, summary in (("extracted", extracted_summary), ("reference", reference_summary)):
        append_summary(rows, name, "atom_count", summary.atom_count)
        append_summary(rows, name, "element_count", format_counter(summary.element_count))
        append_summary(rows, name, "bond_count", summary.bond_count)
        append_summary(rows, name, "bond_order_summary", format_counter(summary.bond_order_summary))
        append_summary(rows, name, "ring_atom_count", summary.ring_atom_count)
        append_summary(rows, name, "aromatic_atom_count", summary.aromatic_atom_count)

    append_summary(rows, "difference", "atom_count_delta", extracted_summary.atom_count - reference_summary.atom_count)
    append_summary(rows, "difference", "bond_count_delta", extracted_summary.bond_count - reference_summary.bond_count)
    append_summary(
        rows,
        "difference",
        "extracted_minus_reference_elements",
        format_counter(extracted_summary.element_count - reference_summary.element_count),
    )
    append_summary(
        rows,
        "difference",
        "reference_minus_extracted_elements",
        format_counter(reference_summary.element_count - extracted_summary.element_count),
    )

    pdb_atom_name = mapping.get(reactive_atom_id, {}).get("pdb_atom_name", "")
    candidates, signature = candidate_reference_atoms(extracted, reference, reactive_atom_id)
    heavy_order_candidate = heavy_atom_order_candidate(extracted, reference, reactive_atom_id)
    note = (
        "final manifest atom indices must use the final selected ligand_sdf atom order; "
        "do not copy ideal SDF atom indices directly"
    )
    append_summary(rows, "reactive_atom", "extracted_atom_id", reactive_atom_id, note)
    append_summary(rows, "reactive_atom", "pdb_atom_name", pdb_atom_name, note)
    append_summary(rows, "reactive_atom", "extracted_signature", signature, note)
    append_summary(rows, "reactive_atom", "extracted_local_graph", atom_local_graph_summary(extracted, reactive_atom_id), note)
    append_summary(rows, "reactive_atom", "reference_candidate_atom_indices", " ".join(map(str, candidates)), note)
    append_summary(
        rows,
        "reactive_atom",
        "tentative_reference_atom_by_heavy_atom_order",
        "" if heavy_order_candidate is None else heavy_order_candidate,
        "tentative only; valid only because the extracted and reference heavy-atom element sequences match",
    )
    if heavy_order_candidate is not None:
        append_summary(
            rows,
            "reactive_atom",
            "tentative_reference_local_graph",
            atom_local_graph_summary(reference, heavy_order_candidate),
            "tentative only; reference SDF has explicit hydrogens and reliable bond orders",
        )
    if len(candidates) != 1:
        warnings.append(
            "could not map extracted reactive atom to a unique reference atom from simple element+graph signature; "
            f"candidates={candidates}"
        )
    if heavy_order_candidate is None:
        warnings.append("heavy-atom order between extracted and reference SDF does not provide a tentative mapping")
    return rows, warnings


def write_rows(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare an extracted ligand graph against a reference ligand SDF.")
    parser.add_argument("--extracted_sdf", type=Path, required=True)
    parser.add_argument("--reference_sdf", type=Path, required=True)
    parser.add_argument("--mapping_csv", type=Path, required=True)
    parser.add_argument("--reactive_atom_id", type=int, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(
        "warning: final manifest atom indices must use the final selected ligand_sdf atom order; "
        "ideal/reference SDF atom order may differ."
    )
    rows, warnings = compare_graphs(
        args.extracted_sdf,
        args.reference_sdf,
        args.mapping_csv,
        args.reactive_atom_id,
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_rows(rows, args.output_csv)
    print(f"wrote graph comparison: {args.output_csv}")
    for row in rows:
        if row["section"] in {"extracted", "reference", "difference", "reactive_atom"}:
            print(f"{row['section']}.{row['key']}: {row['value']}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
