#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.masking import MASK_BUILDERS


def main() -> int:
    scaffold_atoms = [0, 1, 2]
    linker_atoms = [3, 4]
    warhead_atoms = [5, 6]
    num_ligand_atoms = 7

    print("Toy ligand atom groups")
    print(f"  scaffold_atoms: {scaffold_atoms}")
    print(f"  linker_atoms:   {linker_atoms}")
    print(f"  warhead_atoms:  {warhead_atoms}")
    print()

    for mask_type in ("A", "B", "B2", "C"):
        result = MASK_BUILDERS[mask_type](
            scaffold_atoms, linker_atoms, warhead_atoms, num_ligand_atoms
        )
        print(f"Mask {mask_type}")
        print(f"  visible_atoms: {list(result.visible_atoms)}")
        print(f"  masked_atoms:  {list(result.masked_atoms)}")
        print(f"  lig_fixed:     {result.lig_fixed.tolist()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
