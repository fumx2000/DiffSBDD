import argparse
from pathlib import Path

import torch
from openbabel import openbabel
openbabel.obErrorLog.StopLogging()  # suppress OpenBabel messages

import utils
from covalent_ext.covapie_target_residue_atom_condition_repository_cli_v1 import (
    add_covapie_target_residue_atom_condition_cli_arguments_v1,
    load_covapie_target_residue_conditioned_model_from_checkpoint_v1,
    resolve_covapie_target_residue_atom_condition_cli_args_v1,
)
from lightning_modules import LigandPocketDDPM


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('checkpoint', type=Path)
    parser.add_argument('--pdbfile', type=str)
    parser.add_argument('--resi_list', type=str, nargs='+', default=None)
    parser.add_argument('--ref_ligand', type=str, default=None)
    parser.add_argument('--outfile', type=Path)
    parser.add_argument('--n_samples', type=int, default=20)
    parser.add_argument('--batch_size', type=int, default=None)
    parser.add_argument('--num_nodes_lig', type=int, default=None)
    parser.add_argument('--all_frags', action='store_true')
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--relax', action='store_true')
    parser.add_argument('--resamplings', type=int, default=10)
    parser.add_argument('--jump_length', type=int, default=1)
    parser.add_argument('--timesteps', type=int, default=None)
    add_covapie_target_residue_atom_condition_cli_arguments_v1(
        parser=parser,
    )
    args = parser.parse_args()
    target_residue_atom_condition_spec = (
        resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=args,
        )
    )

    pdb_id = Path(args.pdbfile).stem

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    if args.batch_size is None:
        args.batch_size = args.n_samples
    assert args.n_samples % args.batch_size == 0

    # Load model
    if target_residue_atom_condition_spec is None:
        model = LigandPocketDDPM.load_from_checkpoint(
            args.checkpoint, map_location=device)
    else:
        model = (
            load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
                checkpoint_path=args.checkpoint,
                map_location=device,
            )
        )
    model = model.to(device)

    if args.num_nodes_lig is not None:
        num_nodes_lig = torch.ones(args.n_samples, dtype=int) * \
                        args.num_nodes_lig
    else:
        num_nodes_lig = None

    molecules = []
    for i in range(args.n_samples // args.batch_size):
        molecules_batch = model.generate_ligands(
            args.pdbfile, args.batch_size, args.resi_list, args.ref_ligand,
            num_nodes_lig, args.sanitize, largest_frag=not args.all_frags,
            relax_iter=(200 if args.relax else 0),
            resamplings=args.resamplings, jump_length=args.jump_length,
            timesteps=args.timesteps,
            target_residue_atom_condition_spec=(
                target_residue_atom_condition_spec
            ))
        molecules.extend(molecules_batch)

    # Make SDF files
    utils.write_sdf_file(args.outfile, molecules)
