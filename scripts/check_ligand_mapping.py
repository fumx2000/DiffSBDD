#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def find_mapping(mapping_csv: str | Path, pdb_atom_name: str) -> list[dict[str, str]]:
    mapping_csv = Path(mapping_csv)
    with mapping_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["pdb_atom_name"] == pdb_atom_name]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find SDF atom index for a PDB ligand atom name.")
    parser.add_argument("--mapping_csv", type=Path, required=True)
    parser.add_argument("--pdb_atom_name", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    matches = find_mapping(args.mapping_csv, args.pdb_atom_name)
    if not matches:
        print(f"PDB atom {args.pdb_atom_name} -> SDF atom index NOT FOUND")
        return 1
    for row in matches:
        print(
            f"PDB atom {args.pdb_atom_name} -> SDF atom index {row['sdf_atom_index']} "
            f"({row['element']} {row['x']} {row['y']} {row['z']})"
        )
    if len(matches) > 1:
        print(f"warning: multiple rows matched PDB atom name {args.pdb_atom_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
