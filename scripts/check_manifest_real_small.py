#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_COLUMNS = [
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


@dataclass
class ManifestCheckResult:
    rows: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_template(self) -> bool:
        return self.rows == 0 and not self.errors

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_atom_indices(value: str) -> list[int]:
    tokens = value.replace(",", " ").split()
    if not tokens:
        return []
    return [int(token) for token in tokens]


def _path_exists_or_warn(path_value: str, manifest_path: Path, label: str, warnings: list[str], row_id: str) -> None:
    if not path_value.strip():
        return
    path = Path(path_value)
    if path.exists() or (manifest_path.parent / path).exists():
        return
    warnings.append(f"{row_id}: {label} does not exist yet: {path_value}")


def check_manifest(manifest_path: str | Path) -> ManifestCheckResult:
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return ManifestCheckResult(rows=0, errors=[f"manifest does not exist: {manifest_path}"])

    errors: list[str] = []
    warnings: list[str] = []
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            return ManifestCheckResult(
                rows=0,
                errors=[f"manifest is missing required columns: {missing_columns}"],
            )

        rows = list(reader)

    sample_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        row_id = row.get("sample_id", "").strip() or f"row {row_number}"
        sample_id = row.get("sample_id", "").strip()
        if not sample_id:
            errors.append(f"row {row_number}: sample_id is empty")
        elif sample_id in sample_ids:
            errors.append(f"{row_id}: duplicate sample_id")
        sample_ids.add(sample_id)

        for field_name in (
            "protein_pdb_path",
            "ligand_sdf_path",
            "reactive_residue_chain",
            "reactive_residue_id",
            "reactive_residue_type",
            "reactive_atom_name",
        ):
            if not row.get(field_name, "").strip():
                errors.append(f"{row_id}: {field_name} is empty")

        _path_exists_or_warn(row.get("protein_pdb_path", ""), manifest_path, "protein_pdb_path", warnings, row_id)
        _path_exists_or_warn(row.get("ligand_sdf_path", ""), manifest_path, "ligand_sdf_path", warnings, row_id)

        try:
            ligand_reactive_atom_id = int(row.get("ligand_reactive_atom_id", ""))
        except ValueError:
            errors.append(f"{row_id}: ligand_reactive_atom_id is not an integer")
            ligand_reactive_atom_id = None

        try:
            scaffold_atoms = parse_atom_indices(row.get("scaffold_atoms", ""))
            linker_atoms = parse_atom_indices(row.get("linker_atoms", ""))
            warhead_atoms = parse_atom_indices(row.get("warhead_atoms", ""))
        except ValueError as exc:
            errors.append(f"{row_id}: atom index parsing failed: {exc}")
            continue

        if not scaffold_atoms:
            errors.append(f"{row_id}: scaffold_atoms is empty")
        if not linker_atoms:
            errors.append(f"{row_id}: linker_atoms is empty")
        if not warhead_atoms:
            errors.append(f"{row_id}: warhead_atoms is empty")

        groups = {
            "scaffold_atoms": set(scaffold_atoms),
            "linker_atoms": set(linker_atoms),
            "warhead_atoms": set(warhead_atoms),
        }
        for left_name, right_name in (
            ("scaffold_atoms", "linker_atoms"),
            ("scaffold_atoms", "warhead_atoms"),
            ("linker_atoms", "warhead_atoms"),
        ):
            overlap = sorted(groups[left_name] & groups[right_name])
            if overlap:
                errors.append(f"{row_id}: {left_name} overlaps {right_name}: {overlap}")

        if ligand_reactive_atom_id is not None and ligand_reactive_atom_id not in groups["warhead_atoms"]:
            errors.append(f"{row_id}: ligand_reactive_atom_id is not in warhead_atoms")

    return ManifestCheckResult(rows=len(rows), errors=errors, warnings=warnings)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a small real covalent manifest without reading structures.")
    parser.add_argument("--manifest", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = check_manifest(args.manifest)
    print(f"manifest: {args.manifest}")
    print(f"rows: {result.rows}")
    if result.is_template:
        print("status: TEMPLATE_OK")
    elif result.ok:
        print("status: OK")
    else:
        print("status: FAILED")

    for warning in result.warnings:
        print(f"warning: {warning}")
    for error in result.errors:
        print(f"error: {error}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
