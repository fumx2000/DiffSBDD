#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


ALLOWED_FINAL_ROLES = {"", "scaffold", "linker", "warhead", "unassigned"}


def check_annotation(path: str | Path) -> tuple[bool, list[str], list[str]]:
    path = Path(path)
    errors: list[str] = []
    info: list[str] = []
    if not path.exists():
        return False, [f"annotation template does not exist: {path}"], info

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    required = {"sdf_atom_index", "suggested_role", "final_role"}
    missing = sorted(required - set(fieldnames))
    if missing:
        errors.append(f"missing required columns: {missing}")
        return False, errors, info

    seen: set[int] = set()
    found_candidate = False
    for row_number, row in enumerate(rows, start=2):
        try:
            atom_idx = int(row["sdf_atom_index"])
        except ValueError:
            errors.append(f"row {row_number}: sdf_atom_index is not an integer")
            continue
        if atom_idx in seen:
            errors.append(f"row {row_number}: duplicate sdf_atom_index {atom_idx}")
        seen.add(atom_idx)

        final_role = row.get("final_role", "").strip()
        if final_role not in ALLOWED_FINAL_ROLES:
            errors.append(f"row {row_number}: invalid final_role {final_role!r}")

        if "ligand_reactive_atom_candidate" in row.get("suggested_role", ""):
            found_candidate = True
            info.append(f"ligand_reactive_atom_candidate: sdf_atom_index {atom_idx}")

    if not found_candidate:
        errors.append("no suggested_role contains ligand_reactive_atom_candidate")

    info.append(f"rows: {len(rows)}")
    return not errors, errors, info


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a ligand annotation template CSV.")
    parser.add_argument("--annotation", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ok, errors, info = check_annotation(args.annotation)
    print(f"annotation: {args.annotation}")
    for line in info:
        print(line)
    if ok:
        print("status: OK")
        return 0
    print("status: FAILED")
    for error in errors:
        print(f"error: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
