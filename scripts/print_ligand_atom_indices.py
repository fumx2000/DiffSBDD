#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from rdkit import Chem


def format_bond_type(bond: Chem.Bond) -> str:
    return str(bond.GetBondType()).lower()


def describe_ligand(ligand_sdf: str | Path) -> list[str]:
    ligand_sdf = Path(ligand_sdf)
    mol = Chem.SDMolSupplier(str(ligand_sdf), sanitize=False)[0]
    if mol is None:
        raise ValueError(f"Could not read ligand SDF: {ligand_sdf}")

    lines = [f"ligand_sdf: {ligand_sdf}", f"atoms: {mol.GetNumAtoms()}", "index symbol degree charge neighbors bonds"]
    for atom in mol.GetAtoms():
        neighbors = []
        bonds = []
        for bond in atom.GetBonds():
            other = bond.GetOtherAtomIdx(atom.GetIdx())
            neighbors.append(str(other))
            bonds.append(f"{other}:{format_bond_type(bond)}")
        lines.append(
            " ".join(
                [
                    str(atom.GetIdx()),
                    atom.GetSymbol(),
                    str(atom.GetDegree()),
                    str(atom.GetFormalCharge()),
                    ",".join(neighbors) if neighbors else "-",
                    ",".join(bonds) if bonds else "-",
                ]
            )
        )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print zero-based ligand atom indices and local bonding.")
    parser.add_argument("--ligand_sdf", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    for line in describe_ligand(args.ligand_sdf):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
