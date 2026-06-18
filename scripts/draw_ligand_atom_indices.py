#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor


DEFAULT_REACTIVE_ATOM_CANDIDATE = 29


def load_annotation(path: str | Path | None) -> dict[int, dict[str, str]]:
    if path is None:
        return {}
    rows: dict[int, dict[str, str]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                atom_idx = int(row.get("sdf_atom_index", ""))
            except ValueError:
                continue
            rows[atom_idx] = row
    return rows


def find_reactive_atom_candidate(annotation: dict[int, dict[str, str]]) -> int:
    for atom_idx, row in annotation.items():
        suggested_role = row.get("suggested_role", "")
        if "ligand_reactive_atom_candidate" in suggested_role:
            return atom_idx
    return DEFAULT_REACTIVE_ATOM_CANDIDATE


def load_molecule(ligand_sdf: str | Path) -> Chem.Mol:
    supplier = Chem.SDMolSupplier(str(ligand_sdf), removeHs=False, sanitize=False)
    mol = supplier[0] if supplier and len(supplier) else None
    if mol is None:
        raise ValueError(f"could not read ligand SDF: {ligand_sdf}")
    try:
        Chem.SanitizeMol(mol)
    except Exception as exc:  # noqa: BLE001 - keep smoke-test drawings permissive.
        print(f"warning: RDKit sanitize failed, drawing unsanitized molecule: {exc}")
    rdDepictor.Compute2DCoords(mol)
    return mol


def atom_labels(mol: Chem.Mol, annotation: dict[int, dict[str, str]]) -> dict[int, str]:
    labels: dict[int, str] = {}
    for atom in mol.GetAtoms():
        atom_idx = atom.GetIdx()
        pdb_atom_name = annotation.get(atom_idx, {}).get("pdb_atom_name", "").strip()
        if pdb_atom_name:
            labels[atom_idx] = f"{atom_idx}:{atom.GetSymbol()}({pdb_atom_name})"
        else:
            labels[atom_idx] = f"{atom_idx}:{atom.GetSymbol()}"
    return labels


def highlight_atoms(
    mol: Chem.Mol,
    annotation: dict[int, dict[str, str]],
    reactive_atom_candidate: int,
) -> tuple[list[int], dict[int, tuple[float, float, float]]]:
    colors = {
        "scaffold": (0.55, 0.72, 0.95),
        "linker": (0.95, 0.78, 0.42),
        "warhead": (0.96, 0.48, 0.48),
    }
    highlight: list[int] = []
    atom_colors: dict[int, tuple[float, float, float]] = {}
    for atom in mol.GetAtoms():
        atom_idx = atom.GetIdx()
        final_role = annotation.get(atom_idx, {}).get("final_role", "").strip().lower()
        if final_role in colors:
            highlight.append(atom_idx)
            atom_colors[atom_idx] = colors[final_role]

    if 0 <= reactive_atom_candidate < mol.GetNumAtoms():
        if reactive_atom_candidate not in highlight:
            highlight.append(reactive_atom_candidate)
        atom_colors[reactive_atom_candidate] = (1.0, 0.2, 0.2)
        mol.GetAtomWithIdx(reactive_atom_candidate).SetProp("atomNote", "reactive candidate")

    return highlight, atom_colors


def draw_svg(mol: Chem.Mol, output_svg: str | Path, annotation: dict[int, dict[str, str]]) -> None:
    reactive_atom_candidate = find_reactive_atom_candidate(annotation)
    labels = atom_labels(mol, annotation)
    highlight, atom_colors = highlight_atoms(mol, annotation, reactive_atom_candidate)

    drawer = Draw.MolDraw2DSVG(1200, 900)
    options = drawer.drawOptions()
    for atom_idx, label in labels.items():
        options.atomLabels[atom_idx] = label
    options.addAtomIndices = False
    options.legendFontSize = 20

    legend = (
        "Atom labels are zero-based SDF atom indices. "
        f"Reactive ligand atom candidate: {reactive_atom_candidate}."
    )
    drawer.DrawMolecule(
        mol,
        legend=legend,
        highlightAtoms=highlight,
        highlightAtomColors=atom_colors,
    )
    drawer.FinishDrawing()
    Path(output_svg).write_text(drawer.GetDrawingText(), encoding="utf-8")


def draw_png(mol: Chem.Mol, output_png: str | Path, annotation: dict[int, dict[str, str]]) -> bool:
    try:
        reactive_atom_candidate = find_reactive_atom_candidate(annotation)
        labels = atom_labels(mol, annotation)
        highlight, atom_colors = highlight_atoms(mol, annotation, reactive_atom_candidate)
        drawer = Draw.MolDraw2DCairo(1200, 900)
        options = drawer.drawOptions()
        for atom_idx, label in labels.items():
            options.atomLabels[atom_idx] = label
        drawer.DrawMolecule(
            mol,
            legend=f"Reactive ligand atom candidate: {reactive_atom_candidate}",
            highlightAtoms=highlight,
            highlightAtomColors=atom_colors,
        )
        drawer.FinishDrawing()
        Path(output_png).write_bytes(drawer.GetDrawingText())
        return True
    except Exception as exc:  # noqa: BLE001 - PNG is optional.
        print(f"warning: PNG generation failed; SVG was still generated: {exc}")
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Draw ligand atom indices for manual covalent annotation.")
    parser.add_argument("--ligand_sdf", type=Path, required=True)
    parser.add_argument("--annotation", type=Path)
    parser.add_argument("--output_svg", type=Path, required=True)
    parser.add_argument("--output_png", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(
        "warning: current SDF was extracted from PDB HETATM + CONECT; bond order may be unreliable. "
        "Use this drawing only as a manual annotation aid."
    )
    annotation = load_annotation(args.annotation)
    mol = load_molecule(args.ligand_sdf)
    draw_svg(mol, args.output_svg, annotation)
    reactive_atom_candidate = find_reactive_atom_candidate(annotation)
    print(f"wrote SVG: {args.output_svg}")
    print(f"reactive_ligand_atom_candidate: {reactive_atom_candidate}")

    if args.output_png:
        if draw_png(mol, args.output_png, annotation):
            print(f"wrote PNG: {args.output_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
