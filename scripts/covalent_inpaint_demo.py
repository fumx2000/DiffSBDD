#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import torch
import torch.nn.functional as F
from Bio.PDB import PDBParser
from rdkit import Chem
from torch_scatter import scatter_mean

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from analysis.molecule_builder import build_molecule, process_molecule
from constants import FLOAT_TYPE, INT_TYPE
from covalent_ext.masking import build_four_level_mask
from lightning_modules import LigandPocketDDPM
import utils


def parse_atom_indices(value: str) -> list[int]:
    tokens = value.replace(",", " ").split()
    if not tokens:
        return []
    return [int(token) for token in tokens]


def read_ligand_sdf(ligand_sdf: Path, atom_encoder: dict[str, int]) -> tuple[torch.Tensor, torch.Tensor]:
    mol = Chem.SDMolSupplier(str(ligand_sdf), sanitize=False)[0]
    if mol is None:
        raise ValueError(f"Could not read ligand SDF: {ligand_sdf}")
    if mol.GetNumConformers() == 0:
        raise ValueError(f"Ligand SDF has no conformer coordinates: {ligand_sdf}")

    coords = torch.tensor(mol.GetConformer().GetPositions(), dtype=FLOAT_TYPE)
    atom_ids = []
    for atom in mol.GetAtoms():
        symbol = atom.GetSymbol()
        if symbol not in atom_encoder:
            raise ValueError(f"Atom symbol {symbol!r} is not supported by this checkpoint")
        atom_ids.append(atom_encoder[symbol])

    atom_types = torch.tensor(atom_ids, dtype=torch.long)
    one_hot = F.one_hot(atom_types, num_classes=len(atom_encoder)).to(FLOAT_TYPE)
    return coords, one_hot


def prepare_single_ligand(model: LigandPocketDDPM, ligand_sdf: Path) -> dict[str, torch.Tensor]:
    coords, one_hot = read_ligand_sdf(ligand_sdf, model.lig_type_encoder)
    num_atoms = coords.size(0)
    return {
        "x": coords.to(model.device),
        "one_hot": one_hot.to(model.device),
        "size": torch.tensor([num_atoms], device=model.device, dtype=INT_TYPE),
        "mask": torch.zeros(num_atoms, device=model.device, dtype=INT_TYPE),
    }


def prepare_single_pocket(model: LigandPocketDDPM, protein_pdb: Path, ligand_sdf: Path) -> dict[str, torch.Tensor]:
    pdb_model = PDBParser(QUIET=True).get_structure("", protein_pdb)[0]
    residues = utils.get_pocket_from_ligand(pdb_model, str(ligand_sdf))
    return model.prepare_pocket(residues, repeats=1)


def run_covalent_inpaint(
    model: LigandPocketDDPM,
    protein_pdb: Path,
    ligand_sdf: Path,
    scaffold_atoms: list[int],
    linker_atoms: list[int],
    warhead_atoms: list[int],
    mask_level: str,
    timesteps: int,
) -> tuple[list[Chem.Mol], object]:
    model.eval()
    ligand = prepare_single_ligand(model, ligand_sdf)
    pocket = prepare_single_pocket(model, protein_pdb, ligand_sdf)

    num_ligand_atoms = int(ligand["size"][0].item())
    mask_result = build_four_level_mask(
        mask_level,
        scaffold_atoms=scaffold_atoms,
        linker_atoms=linker_atoms,
        warhead_atoms=warhead_atoms,
        num_ligand_atoms=num_ligand_atoms,
    )
    lig_fixed = mask_result.lig_fixed.to(model.device)

    pocket_com_before = scatter_mean(pocket["x"], pocket["mask"], dim=0)

    with torch.no_grad():
        if mask_level == "C" and type(model.ddpm).__name__ in {"ConditionalDDPM", "SimpleConditionalDDPM"}:
            xh_lig, xh_pocket, lig_mask, pocket_mask = model.ddpm.sample_given_pocket(
                pocket, ligand["size"], timesteps=timesteps
            )
        elif type(model.ddpm).__name__ in {"ConditionalDDPM", "SimpleConditionalDDPM"}:
            xh_lig, xh_pocket, lig_mask, pocket_mask = model.ddpm.inpaint(
                ligand,
                pocket,
                lig_fixed,
                center="pocket",
                resamplings=1,
                timesteps=timesteps,
                return_frames=1,
            )
        else:
            pocket_fixed = torch.ones(len(pocket["mask"]), device=model.device, dtype=lig_fixed.dtype)
            xh_lig, xh_pocket, lig_mask, pocket_mask = model.ddpm.inpaint(
                ligand,
                pocket,
                lig_fixed,
                pocket_fixed,
                resamplings=1,
                timesteps=timesteps,
                return_frames=1,
            )

    pocket_com_after = scatter_mean(xh_pocket[:, : model.x_dims], pocket_mask, dim=0)
    xh_pocket[:, : model.x_dims] += (pocket_com_before - pocket_com_after)[pocket_mask]
    xh_lig[:, : model.x_dims] += (pocket_com_before - pocket_com_after)[lig_mask]

    x = xh_lig[:, : model.x_dims].detach().cpu()
    atom_type = xh_lig[:, model.x_dims :].argmax(1).detach().cpu()
    lig_mask = lig_mask.detach().cpu()

    molecules = []
    for mol_pc in zip(utils.batch_to_list(x, lig_mask), utils.batch_to_list(atom_type, lig_mask)):
        mol = build_molecule(*mol_pc, model.dataset_info, add_coords=True)
        mol = process_molecule(
            mol,
            add_hydrogens=False,
            sanitize=False,
            relax_iter=0,
            largest_frag=False,
        )
        if mol is not None:
            molecules.append(mol)

    return molecules, mask_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run covalent four-level mask inpainting with DiffSBDD.")
    parser.add_argument("--protein_pdb", type=Path, required=True)
    parser.add_argument("--ligand_sdf", type=Path, required=True)
    parser.add_argument("--scaffold_atoms", type=parse_atom_indices, required=True)
    parser.add_argument("--linker_atoms", type=parse_atom_indices, required=True)
    parser.add_argument("--warhead_atoms", type=parse_atom_indices, required=True)
    parser.add_argument("--mask_level", choices=["A", "B", "B2", "C"], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timesteps", type=int, default=1)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested with --device cuda, but torch.cuda.is_available() is false")

    device = torch.device(args.device)
    model = LigandPocketDDPM.load_from_checkpoint(args.checkpoint, map_location=device)
    model = model.to(device)

    molecules, mask_result = run_covalent_inpaint(
        model=model,
        protein_pdb=args.protein_pdb,
        ligand_sdf=args.ligand_sdf,
        scaffold_atoms=args.scaffold_atoms,
        linker_atoms=args.linker_atoms,
        warhead_atoms=args.warhead_atoms,
        mask_level=args.mask_level,
        timesteps=args.timesteps,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    utils.write_sdf_file(args.output, molecules)

    print(f"mask_level: {mask_result.mask_type}")
    print(f"visible_atoms: {list(mask_result.visible_atoms)}")
    print(f"masked_atoms: {list(mask_result.masked_atoms)}")
    print(f"lig_fixed: {mask_result.lig_fixed.tolist()}")
    print(f"molecules: {len(molecules)}")
    print(f"output: {args.output}")

    if not molecules:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
