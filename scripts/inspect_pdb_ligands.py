#!/usr/bin/env python
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HetAtom:
    atom_name: str
    res_name: str
    chain: str
    res_id: int
    x: float
    y: float
    z: float
    element: str


def parse_hetatm(line: str) -> HetAtom:
    return HetAtom(
        atom_name=line[12:16].strip(),
        res_name=line[17:20].strip(),
        chain=line[21].strip(),
        res_id=int(line[22:26]),
        x=float(line[30:38]),
        y=float(line[38:46]),
        z=float(line[46:54]),
        element=line[76:78].strip() or line[12:16].strip()[0],
    )


def is_cys12_sg_related(line: str) -> bool:
    upper = line.upper()
    return "CYS A  12" in upper and "SG" in upper


def inspect_pdb(protein_pdb: str | Path, atom_preview: int = 8) -> list[str]:
    protein_pdb = Path(protein_pdb)
    hetatm_by_residue: dict[tuple[str, str, int], list[HetAtom]] = defaultdict(list)
    link_records: list[str] = []
    conect_records: list[str] = []

    with protein_pdb.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.startswith("HETATM"):
                atom = parse_hetatm(line)
                hetatm_by_residue[(atom.chain, atom.res_name, atom.res_id)].append(atom)
            elif line.startswith("LINK"):
                link_records.append(line)
            elif line.startswith("CONECT"):
                conect_records.append(line)

    lines = [f"protein_pdb: {protein_pdb}"]
    lines.append("HETATM residues:")
    if not hetatm_by_residue:
        lines.append("  none")
    for (chain, res_name, res_id), atoms in sorted(hetatm_by_residue.items(), key=lambda item: item[0]):
        element_counts = Counter(atom.element for atom in atoms)
        element_summary = ",".join(f"{element}:{count}" for element, count in sorted(element_counts.items()))
        lines.append(
            f"  chain={chain or '-'} res_name={res_name} res_id={res_id} "
            f"atom_count={len(atoms)} elements={element_summary}"
        )
        lines.append("    atom preview:")
        for atom in atoms[:atom_preview]:
            lines.append(
                f"      {atom.atom_name} {atom.element} "
                f"{atom.x:.3f} {atom.y:.3f} {atom.z:.3f}"
            )

    lines.append(f"LINK records: {len(link_records)}")
    for record in link_records:
        prefix = "  **CYS12/SG** " if is_cys12_sg_related(record) else "  "
        lines.append(prefix + record)

    highlighted_conect = [record for record in conect_records if is_cys12_sg_related(record)]
    lines.append(f"CONECT records: {len(conect_records)}")
    if highlighted_conect:
        lines.append("CYS12/SG-related CONECT records:")
        for record in highlighted_conect:
            lines.append("  **CYS12/SG** " + record)
    else:
        lines.append("CYS12/SG-related CONECT records: none detected by text match")

    ligand_like = [
        (key, atoms)
        for key, atoms in sorted(hetatm_by_residue.items(), key=lambda item: item[0])
        if key[1] not in {"HOH", "WAT"}
    ]
    lines.append("Ligand-like HETATM residues:")
    if not ligand_like:
        lines.append("  none")
    for (chain, res_name, res_id), atoms in ligand_like:
        lines.append(f"  {res_name} {chain}:{res_id} atom_count={len(atoms)}")
        for atom in atoms[:atom_preview]:
            lines.append(
                f"    {atom.atom_name} {atom.element} "
                f"{atom.x:.3f} {atom.y:.3f} {atom.z:.3f}"
            )

    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect HETATM, LINK, and CONECT records in one PDB file.")
    parser.add_argument("--protein_pdb", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    for line in inspect_pdb(args.protein_pdb):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
