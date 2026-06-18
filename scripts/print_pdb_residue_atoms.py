#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from Bio.PDB import PDBParser


def describe_residue(protein_pdb: str | Path, chain_id: str, residue_id: int) -> tuple[list[str], bool]:
    protein_pdb = Path(protein_pdb)
    model = PDBParser(QUIET=True).get_structure("", protein_pdb)[0]
    if chain_id not in model:
        chains = ", ".join(chain.id for chain in model)
        return ([f"protein_pdb: {protein_pdb}", f"chain {chain_id} not found", f"available_chains: {chains}"], False)

    chain = model[chain_id]
    key = (" ", residue_id, " ")
    if key not in chain:
        residue_ids = [str(res.id[1]) for res in chain.get_residues() if res.id[0] == " "]
        preview = ", ".join(residue_ids[:20])
        return (
            [
                f"protein_pdb: {protein_pdb}",
                f"residue {chain_id}:{residue_id} not found",
                f"first_available_residue_ids: {preview}",
            ],
            False,
        )

    residue = chain[key]
    lines = [
        f"protein_pdb: {protein_pdb}",
        f"residue: {chain_id}:{residue_id} {residue.get_resname()}",
        "atom_name x y z element",
    ]
    for atom in residue.get_atoms():
        x, y, z = atom.get_coord()
        lines.append(f"{atom.get_name()} {x:.4f} {y:.4f} {z:.4f} {atom.element}")
    return lines, True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print atom names and coordinates for one PDB residue.")
    parser.add_argument("--protein_pdb", type=Path, required=True)
    parser.add_argument("--chain", required=True)
    parser.add_argument("--residue_id", type=int, required=True)
    parser.add_argument("--strict", action="store_true", help="Return non-zero if the chain or residue is missing.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    lines, found = describe_residue(args.protein_pdb, args.chain, args.residue_id)
    for line in lines:
        print(line)
    return 0 if found or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
