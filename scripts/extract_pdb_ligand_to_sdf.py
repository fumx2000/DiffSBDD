#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point3D


@dataclass(frozen=True)
class PdbLigandAtom:
    serial: int
    atom_name: str
    res_name: str
    chain: str
    residue_id: int
    element: str
    x: float
    y: float
    z: float


def normalize_element(element: str, atom_name: str) -> str:
    raw = (element or "").strip()
    if not raw:
        raw = "".join(ch for ch in atom_name if ch.isalpha())[:2]
    raw = raw.strip()
    if len(raw) == 1:
        return raw.upper()
    return raw[0].upper() + raw[1:].lower()


def parse_hetatm(line: str) -> PdbLigandAtom:
    atom_name = line[12:16].strip()
    element = normalize_element(line[76:78], atom_name)
    return PdbLigandAtom(
        serial=int(line[6:11]),
        atom_name=atom_name,
        res_name=line[17:20].strip(),
        chain=line[21].strip(),
        residue_id=int(line[22:26]),
        element=element,
        x=float(line[30:38]),
        y=float(line[38:46]),
        z=float(line[46:54]),
    )


def parse_conect(line: str) -> tuple[int, list[int]]:
    serial = int(line[6:11])
    neighbors = []
    for start in range(11, len(line), 5):
        token = line[start : start + 5].strip()
        if token:
            neighbors.append(int(token))
    return serial, neighbors


def read_ligand_atoms_and_conect(
    protein_pdb: Path,
    ligand_resname: str,
    chain: str,
    residue_id: int,
) -> tuple[list[PdbLigandAtom], set[tuple[int, int]]]:
    atoms: list[PdbLigandAtom] = []
    conect_rows: list[tuple[int, list[int]]] = []

    with protein_pdb.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("HETATM"):
                atom = parse_hetatm(line)
                if atom.res_name == ligand_resname and atom.chain == chain and atom.residue_id == residue_id:
                    atoms.append(atom)
            elif line.startswith("CONECT"):
                conect_rows.append(parse_conect(line))

    if not atoms:
        raise ValueError(f"Could not find ligand {ligand_resname} {chain}:{residue_id} in {protein_pdb}")

    ligand_serials = {atom.serial for atom in atoms}
    bonds: set[tuple[int, int]] = set()
    for serial, neighbors in conect_rows:
        if serial not in ligand_serials:
            continue
        for neighbor in neighbors:
            if neighbor in ligand_serials:
                bonds.add(tuple(sorted((serial, neighbor))))

    return atoms, bonds


def build_rdkit_mol(atoms: list[PdbLigandAtom], bonds: set[tuple[int, int]]) -> Chem.Mol:
    rw_mol = Chem.RWMol()
    serial_to_idx: dict[int, int] = {}
    conformer = Chem.Conformer(len(atoms))

    for idx, pdb_atom in enumerate(atoms):
        atom = Chem.Atom(pdb_atom.element)
        atom.SetProp("pdb_atom_name", pdb_atom.atom_name)
        atom.SetNoImplicit(True)
        serial_to_idx[pdb_atom.serial] = rw_mol.AddAtom(atom)
        conformer.SetAtomPosition(idx, Point3D(pdb_atom.x, pdb_atom.y, pdb_atom.z))

    for serial_a, serial_b in sorted(bonds):
        rw_mol.AddBond(serial_to_idx[serial_a], serial_to_idx[serial_b], Chem.BondType.SINGLE)

    mol = rw_mol.GetMol()
    mol.AddConformer(conformer, assignId=True)
    mol.SetProp("_Name", f"{atoms[0].res_name}_{atoms[0].chain}_{atoms[0].residue_id}")
    return mol


def write_mapping_csv(atoms: list[PdbLigandAtom], output_mapping_csv: Path) -> None:
    output_mapping_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_mapping_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sdf_atom_index", "pdb_atom_name", "element", "x", "y", "z"],
        )
        writer.writeheader()
        for idx, atom in enumerate(atoms):
            writer.writerow(
                {
                    "sdf_atom_index": idx,
                    "pdb_atom_name": atom.atom_name,
                    "element": atom.element,
                    "x": f"{atom.x:.4f}",
                    "y": f"{atom.y:.4f}",
                    "z": f"{atom.z:.4f}",
                }
            )


def extract_ligand_to_sdf(
    protein_pdb: str | Path,
    ligand_resname: str,
    chain: str,
    residue_id: int,
    output_sdf: str | Path,
    output_mapping_csv: str | Path,
) -> tuple[int, int]:
    protein_pdb = Path(protein_pdb)
    output_sdf = Path(output_sdf)
    output_mapping_csv = Path(output_mapping_csv)
    atoms, bonds = read_ligand_atoms_and_conect(protein_pdb, ligand_resname, chain, residue_id)
    mol = build_rdkit_mol(atoms, bonds)

    output_sdf.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(output_sdf))
    writer.write(mol)
    writer.close()

    write_mapping_csv(atoms, output_mapping_csv)
    return len(atoms), len(bonds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract one PDB HETATM ligand residue to SDF and atom mapping CSV.")
    parser.add_argument("--protein_pdb", type=Path, required=True)
    parser.add_argument("--ligand_resname", required=True)
    parser.add_argument("--chain", required=True)
    parser.add_argument("--residue_id", type=int, required=True)
    parser.add_argument("--output_sdf", type=Path, required=True)
    parser.add_argument("--output_mapping_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    atom_count, bond_count = extract_ligand_to_sdf(
        protein_pdb=args.protein_pdb,
        ligand_resname=args.ligand_resname,
        chain=args.chain,
        residue_id=args.residue_id,
        output_sdf=args.output_sdf,
        output_mapping_csv=args.output_mapping_csv,
    )
    print(f"extracted {args.ligand_resname} {args.chain}:{args.residue_id}")
    print(f"atoms: {atom_count}")
    print(f"intra-ligand CONECT bonds written as single bonds: {bond_count}")
    print(f"output_sdf: {args.output_sdf}")
    print(f"output_mapping_csv: {args.output_mapping_csv}")
    print("warning: SDF atom order was constructed from PDB HETATM order; use the mapping CSV as the source of PDB atom name to SDF atom index.")
    print("warning: bond orders from PDB CONECT are not reliable; downstream scientific use may require a curated pre-reaction ligand graph.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
