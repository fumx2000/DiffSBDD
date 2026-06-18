#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.dataset import CovalentJsonlDataset


DATASET_PATH = Path("data/processed/covalent_debug.jsonl")


def main() -> int:
    dataset = CovalentJsonlDataset(DATASET_PATH)
    print(f"dataset: {DATASET_PATH}")
    print(f"samples: {len(dataset)}")

    for sample in dataset:
        num_atoms = dataset.num_ligand_atoms(sample)
        masks = dataset.build_all_masks(sample)
        print()
        print(f"sample_id: {sample['sample_id']}")
        print(f"  ligand_atoms: {num_atoms}")
        print(
            "  atom_groups: "
            f"scaffold={len(sample['scaffold_atoms'])}, "
            f"linker={len(sample['linker_atoms'])}, "
            f"warhead={len(sample['warhead_atoms'])}"
        )
        print(
            "  reactive_residue: "
            f"{sample['reactive_residue_type']} {sample['reactive_residue_id']} "
            f"{sample['reactive_atom_name']}"
        )
        print(f"  warhead_type: {sample['warhead_type']}")
        print(f"  ligand_reactive_atom: {sample['ligand_reactive_atom_id']}")
        print(f"  covalent_bond_atom_pair: {sample['covalent_bond_atom_pair']}")
        for mask_type in ("A", "B", "B2", "C"):
            result = masks[mask_type]
            print(
                f"  mask {mask_type}: "
                f"visible={len(result.visible_atoms)}, "
                f"masked={len(result.masked_atoms)}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
