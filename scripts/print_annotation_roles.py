#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROLE_KEYS = ("scaffold", "linker", "warhead", "unassigned", "empty")


def normalize_final_role(value: str) -> str:
    role = value.strip().lower()
    return role if role else "empty"


def load_annotation(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def role_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        role = normalize_final_role(row.get("final_role", ""))
        if role not in ROLE_KEYS:
            counts["invalid"] += 1
        else:
            counts[role] += 1
    return counts


def print_annotation_roles(annotation: str | Path) -> None:
    rows = load_annotation(annotation)
    print(f"annotation: {annotation}")
    print("sdf_atom_index,pdb_atom_name,element,neighbors,suggested_role,final_role")
    for row in rows:
        print(
            ",".join(
                [
                    row.get("sdf_atom_index", ""),
                    row.get("pdb_atom_name", ""),
                    row.get("element", ""),
                    row.get("neighbors", ""),
                    row.get("suggested_role", ""),
                    row.get("final_role", ""),
                ]
            )
        )

    counts = role_counts(rows)
    print("role_counts:")
    for key in ROLE_KEYS:
        print(f"{key}: {counts.get(key, 0)}")
    if counts.get("invalid", 0):
        print(f"invalid: {counts['invalid']}")

    assigned = sum(counts.get(role, 0) for role in ("scaffold", "linker", "warhead"))
    if assigned == 0:
        print("manual_annotation_required: final_role is empty or unassigned for all atoms")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print ligand annotation roles and role counts.")
    parser.add_argument("--annotation", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print_annotation_roles(args.annotation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
