#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, deque
from pathlib import Path

from rdkit import Chem


REPORT_COLUMNS = [
    "sample_id",
    "extracted_atom_id",
    "extracted_element",
    "extracted_pdb_atom_name",
    "reference_candidate_atom_id",
    "reference_element",
    "element_match",
    "extracted_degree",
    "reference_degree",
    "degree_match",
    "graph_distance_to_reactive_atom",
    "final_role",
    "is_reactive_atom",
    "mapping_confidence",
    "mapping_warning",
]

CONFIDENCE_VALUES = {"high", "medium", "low", "unresolved"}


def load_molecule(path: str | Path, *, sanitize: bool) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=sanitize)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None and sanitize:
        print(f"warning: sanitized read failed for {path}; retrying sanitize=False")
        return load_molecule(path, sanitize=False)
    if mol is None:
        raise ValueError(f"could not read SDF: {path}")
    if not sanitize:
        try:
            Chem.SanitizeMol(mol)
        except Exception as exc:  # noqa: BLE001 - report generation should stay permissive.
            print(f"warning: RDKit sanitize failed for {path}: {exc}")
    return mol


def load_csv_by_atom_index(path: str | Path) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_atom_idx = row.get("sdf_atom_index", "")
            try:
                atom_idx = int(raw_atom_idx)
            except ValueError:
                continue
            rows[atom_idx] = row
    return rows


def graph_distances(mol: Chem.Mol, start_atom_idx: int) -> dict[int, int]:
    if start_atom_idx < 0 or start_atom_idx >= mol.GetNumAtoms():
        raise ValueError(f"reactive_atom_id out of range: {start_atom_idx}")

    distances = {start_atom_idx: 0}
    queue: deque[int] = deque([start_atom_idx])
    while queue:
        atom_idx = queue.popleft()
        for neighbor in mol.GetAtomWithIdx(atom_idx).GetNeighbors():
            neighbor_idx = neighbor.GetIdx()
            if neighbor_idx in distances:
                continue
            distances[neighbor_idx] = distances[atom_idx] + 1
            queue.append(neighbor_idx)
    return distances


def heavy_atom_order_map(extracted: Chem.Mol, reference: Chem.Mol) -> dict[int, int]:
    extracted_heavy = [atom.GetIdx() for atom in extracted.GetAtoms() if atom.GetSymbol() != "H"]
    reference_heavy = [atom.GetIdx() for atom in reference.GetAtoms() if atom.GetSymbol() != "H"]
    extracted_elements = [extracted.GetAtomWithIdx(atom_idx).GetSymbol() for atom_idx in extracted_heavy]
    reference_elements = [reference.GetAtomWithIdx(atom_idx).GetSymbol() for atom_idx in reference_heavy]
    if extracted_elements != reference_elements:
        return {}
    return dict(zip(extracted_heavy, reference_heavy))


def local_signature(mol: Chem.Mol, atom_idx: int) -> tuple[str, int, tuple[str, ...]]:
    atom = mol.GetAtomWithIdx(atom_idx)
    neighbor_elements = sorted(neighbor.GetSymbol() for neighbor in atom.GetNeighbors())
    return atom.GetSymbol(), atom.GetDegree(), tuple(neighbor_elements)


def exact_local_candidates(extracted: Chem.Mol, reference: Chem.Mol, extracted_atom_idx: int) -> list[int]:
    signature = local_signature(extracted, extracted_atom_idx)
    return [
        atom.GetIdx()
        for atom in reference.GetAtoms()
        if local_signature(reference, atom.GetIdx()) == signature
    ]


def element_candidates(reference: Chem.Mol, element: str) -> list[int]:
    return [atom.GetIdx() for atom in reference.GetAtoms() if atom.GetSymbol() == element]


def choose_reference_candidate(
    extracted: Chem.Mol,
    reference: Chem.Mol,
    extracted_atom_idx: int,
    order_map: dict[int, int],
) -> tuple[str, int | None, list[str]]:
    warnings: list[str] = []
    if extracted_atom_idx in order_map:
        candidate = order_map[extracted_atom_idx]
        return str(candidate), candidate, warnings

    local_candidates = exact_local_candidates(extracted, reference, extracted_atom_idx)
    if len(local_candidates) == 1:
        return str(local_candidates[0]), local_candidates[0], ["heavy_atom_order_mapping_unavailable"]
    if len(local_candidates) > 1:
        return " ".join(str(idx) for idx in local_candidates), None, [
            "multiple_reference_atoms_with_same_local_signature"
        ]

    element = extracted.GetAtomWithIdx(extracted_atom_idx).GetSymbol()
    candidates = element_candidates(reference, element)
    if candidates:
        return " ".join(str(idx) for idx in candidates), None, ["no_unique_local_graph_match"]
    return "", None, ["no_reference_atom_with_matching_element"]


def confidence_for_mapping(
    *,
    is_reactive_atom: bool,
    pdb_atom_name: str,
    element_match: bool,
    degree_match: bool,
    unique_candidate: bool,
) -> str:
    if not element_match:
        return "unresolved"
    if is_reactive_atom and unique_candidate and pdb_atom_name:
        return "high"
    if unique_candidate and degree_match:
        return "medium"
    if unique_candidate:
        return "low"
    return "low"


def build_report_rows(
    *,
    sample_id: str,
    extracted_sdf: str | Path,
    reference_sdf: str | Path,
    mapping_csv: str | Path,
    annotation: str | Path,
    reactive_atom_id: int,
) -> list[dict[str, str]]:
    extracted = load_molecule(extracted_sdf, sanitize=False)
    reference = load_molecule(reference_sdf, sanitize=True)
    mapping_rows = load_csv_by_atom_index(mapping_csv)
    annotation_rows = load_csv_by_atom_index(annotation)
    distances = graph_distances(extracted, reactive_atom_id)
    order_map = heavy_atom_order_map(extracted, reference)

    rows: list[dict[str, str]] = []
    for atom in extracted.GetAtoms():
        atom_idx = atom.GetIdx()
        extracted_element = atom.GetSymbol()
        mapping_row = mapping_rows.get(atom_idx, {})
        annotation_row = annotation_rows.get(atom_idx, {})
        pdb_atom_name = mapping_row.get("pdb_atom_name", annotation_row.get("pdb_atom_name", ""))
        candidate_text, candidate_idx, warnings = choose_reference_candidate(
            extracted,
            reference,
            atom_idx,
            order_map,
        )

        if candidate_idx is not None:
            reference_atom = reference.GetAtomWithIdx(candidate_idx)
            reference_element = reference_atom.GetSymbol()
            reference_degree = reference_atom.GetDegree()
            element_match = extracted_element == reference_element
            degree_match = atom.GetDegree() == reference_degree
            unique_candidate = True
        else:
            reference_element = ""
            reference_degree = ""
            element_match = False
            degree_match = False
            unique_candidate = False

        is_reactive_atom = atom_idx == reactive_atom_id
        confidence = confidence_for_mapping(
            is_reactive_atom=is_reactive_atom,
            pdb_atom_name=pdb_atom_name,
            element_match=element_match,
            degree_match=degree_match,
            unique_candidate=unique_candidate,
        )
        if confidence not in CONFIDENCE_VALUES:
            raise AssertionError(f"invalid confidence: {confidence}")

        rows.append(
            {
                "sample_id": sample_id,
                "extracted_atom_id": str(atom_idx),
                "extracted_element": extracted_element,
                "extracted_pdb_atom_name": pdb_atom_name,
                "reference_candidate_atom_id": candidate_text,
                "reference_element": reference_element,
                "element_match": str(element_match).lower(),
                "extracted_degree": str(atom.GetDegree()),
                "reference_degree": str(reference_degree),
                "degree_match": str(degree_match).lower(),
                "graph_distance_to_reactive_atom": str(distances.get(atom_idx, "")),
                "final_role": annotation_row.get("final_role", ""),
                "is_reactive_atom": str(is_reactive_atom).lower(),
                "mapping_confidence": confidence,
                "mapping_warning": "; ".join(warnings),
            }
        )
    return rows


def write_report(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict[str, str]], reactive_atom_id: int) -> None:
    counts = Counter(row["mapping_confidence"] for row in rows)
    print(
        "mapping_confidence_counts: "
        + " ".join(f"{key}={counts.get(key, 0)}" for key in ["high", "medium", "low", "unresolved"])
    )
    reactive_rows = [row for row in rows if row["extracted_atom_id"] == str(reactive_atom_id)]
    if reactive_rows:
        row = reactive_rows[0]
        print(
            "reactive_atom_mapping: "
            f"extracted_atom_id={row['extracted_atom_id']} "
            f"pdb_atom_name={row['extracted_pdb_atom_name']} "
            f"reference_candidate_atom_id={row['reference_candidate_atom_id']} "
            f"mapping_confidence={row['mapping_confidence']} "
            f"warning={row['mapping_warning']}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a non-destructive ligand graph repair report.")
    parser.add_argument("--sample_id", required=True)
    parser.add_argument("--extracted_sdf", type=Path, required=True)
    parser.add_argument("--reference_sdf", type=Path, required=True)
    parser.add_argument("--mapping_csv", type=Path, required=True)
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--reactive_atom_id", type=int, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: ideal/reference atom order must not be used directly for manifest indices.")
    print("warning: extracted SDF coordinates are retained as bound-pose geometry.")
    print("warning: this report does not repair bond orders.")
    print("warning: this report does not create pre-reaction graph.")
    rows = build_report_rows(
        sample_id=args.sample_id,
        extracted_sdf=args.extracted_sdf,
        reference_sdf=args.reference_sdf,
        mapping_csv=args.mapping_csv,
        annotation=args.annotation,
        reactive_atom_id=args.reactive_atom_id,
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_report(rows, args.output_csv)
    print(f"wrote graph repair report: {args.output_csv}")
    print(f"rows: {len(rows)}")
    print_summary(rows, args.reactive_atom_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
