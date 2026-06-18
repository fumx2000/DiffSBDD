#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.dataset import CovalentJsonlDataset


def check_dataset(input_path: str | Path, verbose: bool = True) -> bool:
    dataset = CovalentJsonlDataset(input_path)
    failures: list[str] = []

    if verbose:
        print(f"input: {input_path}")
        print(f"samples: {len(dataset)}")

    if len(dataset) == 0:
        failures.append("dataset is empty")

    for sample in dataset:
        sample_id = sample["sample_id"]
        num_atoms = dataset.num_ligand_atoms(sample)
        scaffold = set(sample["scaffold_atoms"])
        linker = set(sample["linker_atoms"])
        warhead = set(sample["warhead_atoms"])

        if not scaffold or not linker or not warhead:
            failures.append(f"{sample_id}: scaffold/linker/warhead must be non-empty")
        if not scaffold.isdisjoint(linker) or not scaffold.isdisjoint(warhead) or not linker.isdisjoint(warhead):
            failures.append(f"{sample_id}: scaffold/linker/warhead atom sets overlap")
        all_group_atoms = scaffold | linker | warhead
        invalid_atoms = sorted(atom for atom in all_group_atoms if atom < 0 or atom >= num_atoms)
        if invalid_atoms:
            failures.append(f"{sample_id}: atom indices outside ligand range: {invalid_atoms}")
        if sample["ligand_reactive_atom_id"] not in warhead:
            failures.append(f"{sample_id}: ligand_reactive_atom_id is not in warhead_atoms")
        if len(sample.get("reactive_atom_coord", [])) != 3:
            failures.append(f"{sample_id}: reactive_atom_coord is missing or not length 3")
        if not sample.get("covalent_bond_atom_pair"):
            failures.append(f"{sample_id}: covalent_bond_atom_pair is missing")

        try:
            masks = dataset.build_all_masks(sample)
        except Exception as exc:
            failures.append(f"{sample_id}: mask generation failed: {exc}")
            masks = {}

        if verbose:
            print()
            print(f"sample_id: {sample_id}")
            print(f"  ligand_atoms: {num_atoms}")
            print(
                "  groups: "
                f"scaffold={len(scaffold)}, linker={len(linker)}, warhead={len(warhead)}"
            )
            print(
                "  reactive: "
                f"{sample['reactive_residue_type']} {sample['reactive_residue_id']} "
                f"{sample['reactive_atom_name']} -> ligand {sample['ligand_reactive_atom_id']}"
            )
            print(f"  covalent_bond_atom_pair: {sample['covalent_bond_atom_pair']}")
            for mask_type in ("A", "B", "B2", "C"):
                if mask_type in masks:
                    result = masks[mask_type]
                    print(
                        f"  mask {mask_type}: "
                        f"visible={len(result.visible_atoms)}, masked={len(result.masked_atoms)}"
                    )

    if failures:
        print()
        print("QA FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print()
    print("QA PASSED")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA a small covalent processed JSONL.")
    parser.add_argument("--input", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return 0 if check_dataset(args.input, verbose=True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
