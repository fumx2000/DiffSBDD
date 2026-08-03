"""Central repository CLI support for target-residue conditioning V1."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import os
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any


__all__ = (
    "add_covapie_target_residue_atom_condition_cli_arguments_v1",
    "resolve_covapie_target_residue_atom_condition_cli_args_v1",
    "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_INVALID"
_TARGET_ARGUMENT_NAMES = {
    "target_residue_atom_conditioning",
    "target_chain_id",
    "target_residue_sequence_number",
}
_TARGET_OPTION_STRINGS = (
    "--target_residue_atom_conditioning",
    "--target_chain_id",
    "--target_residue_sequence_number",
)
_CHECKPOINT_SIZE = 17_861_341
_CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
_EXPECTED_HYPER_PARAMETER_KEYS = {
    "augment_noise",
    "augment_rotation",
    "auxiliary_loss",
    "batch_size",
    "clip_grad",
    "datadir",
    "dataset",
    "diffusion_params",
    "egnn_params",
    "eval_epochs",
    "eval_params",
    "loss_params",
    "lr",
    "mode",
    "node_histogram",
    "num_workers",
    "outdir",
    "pocket_representation",
    "virtual_nodes",
    "visualize_chain_epoch",
    "visualize_sample_epoch",
}
_NEW_STATE_KEY = "ddpm.dynamics.target_residue_atom_condition_embedding"


def _raise_invalid(error: BaseException | None = None) -> None:
    if error is None:
        raise ValueError(_ERROR)
    raise ValueError(_ERROR) from error


def _remove_added_parser_actions(
    parser: argparse.ArgumentParser,
    original_actions: tuple[argparse.Action, ...],
) -> None:
    original_action_ids = {id(action) for action in original_actions}
    for action in tuple(parser._actions):
        if id(action) in original_action_ids:
            continue
        for option_string in action.option_strings:
            parser._option_string_actions.pop(option_string, None)
        action.container._remove_action(action)


def add_covapie_target_residue_atom_condition_cli_arguments_v1(
    *,
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Add the three central target-residue arguments to ``parser``."""

    try:
        if not isinstance(parser, argparse.ArgumentParser) or any(
            option in parser._option_string_actions
            for option in _TARGET_OPTION_STRINGS
        ):
            _raise_invalid()
        original_actions = tuple(parser._actions)
        try:
            parser.add_argument(
                "--target_residue_atom_conditioning",
                action="store_true",
                default=False,
            )
            parser.add_argument(
                "--target_chain_id",
                type=str,
                default=None,
            )
            parser.add_argument(
                "--target_residue_sequence_number",
                type=int,
                default=None,
            )
        except Exception:
            _remove_added_parser_actions(parser, original_actions)
            raise
        return parser
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def resolve_covapie_target_residue_atom_condition_cli_args_v1(
    *,
    arguments: argparse.Namespace | Mapping[str, Any],
) -> dict[str, Any] | None:
    """Compile central CLI values to an Exact6 selector or legacy ``None``."""

    try:
        if isinstance(arguments, argparse.Namespace):
            values = dict(vars(arguments))
        elif isinstance(arguments, Mapping):
            values = dict(arguments.items())
        else:
            _raise_invalid()
        if any(type(key) is not str for key in values) or any(
            key.startswith("target_") and key not in _TARGET_ARGUMENT_NAMES
            for key in values
        ):
            _raise_invalid()

        missing = object()
        enabled = values.get("target_residue_atom_conditioning", missing)
        chain = values.get("target_chain_id")
        residue_number = values.get("target_residue_sequence_number")
        if enabled is not missing and type(enabled) is not bool:
            _raise_invalid()
        if (
            (enabled is missing or enabled is False)
            and chain is None
            and residue_number is None
        ):
            return None
        if (
            enabled is not True
            or type(chain) is not str
            or not chain
            or chain != chain.strip()
            or type(residue_number) is not int
        ):
            _raise_invalid()
        return {
            "chain_id": chain,
            "residue_sequence_number": residue_number,
            "residue_insertion_code": " ",
            "residue_name": "CYS",
            "atom_name": "SG",
            "element": "S",
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _read_frozen_checkpoint(checkpoint_path: str | Path) -> tuple[Path, bytes]:
    if type(checkpoint_path) not in (str, type(Path())):
        _raise_invalid()
    path = Path(checkpoint_path)
    try:
        file_stat = os.lstat(path)
        if (
            stat.S_ISLNK(file_stat.st_mode)
            or not stat.S_ISREG(file_stat.st_mode)
            or file_stat.st_size != _CHECKPOINT_SIZE
        ):
            _raise_invalid()
        checkpoint_bytes = path.read_bytes()
        if (
            len(checkpoint_bytes) != _CHECKPOINT_SIZE
            or hashlib.sha256(checkpoint_bytes).hexdigest() != _CHECKPOINT_SHA256
        ):
            _raise_invalid()
        return path, checkpoint_bytes
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
    *,
    checkpoint_path: str | Path,
    map_location: object = "cpu",
):
    """Load the frozen base checkpoint as the conditioned model profile."""

    try:
        path, checkpoint_bytes = _read_frozen_checkpoint(checkpoint_path)
        import torch

        entry_rng = torch.random.get_rng_state().clone()
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                from covalent_ext.covapie_target_residue_atom_condition_checkpoint_migration_v1 import (
                    load_covapie_base_state_dict_into_target_residue_conditioned_model_v1,
                )
                from lightning_modules import LigandPocketDDPM

                payload = torch.load(
                    io.BytesIO(checkpoint_bytes),
                    map_location=map_location,
                    weights_only=False,
                )
                if type(payload) is not dict:
                    _raise_invalid()
                hyper_parameters = payload.get("hyper_parameters")
                state_dict = payload.get("state_dict")
                if (
                    type(hyper_parameters) is not dict
                    or set(hyper_parameters) != _EXPECTED_HYPER_PARAMETER_KEYS
                    or not isinstance(state_dict, Mapping)
                    or len(state_dict) != 122
                    or any(
                        type(key) is not str
                        or not isinstance(value, torch.Tensor)
                        for key, value in state_dict.items()
                    )
                    or hyper_parameters.get("mode") != "pocket_conditioning"
                    or hyper_parameters.get("pocket_representation") != "full-atom"
                    or getattr(hyper_parameters.get("egnn_params"), "joint_nf", None)
                    != 32
                    or "target_residue_atom_conditioning" in hyper_parameters
                ):
                    _raise_invalid()

                base_keys = list(state_dict)
                base_tensor_ids = {
                    key: id(state_dict[key]) for key in base_keys
                }
                base_tensor_versions = {
                    key: state_dict[key]._version for key in base_keys
                }
                base_tensor_values = {
                    key: state_dict[key].detach().clone() for key in base_keys
                }
                constructor_arguments = dict(hyper_parameters)
                constructor_arguments["target_residue_atom_conditioning"] = True
                model = LigandPocketDDPM(**constructor_arguments)
                migration_report = load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
                    model=model,
                    base_state_dict=state_dict,
                )

                dynamics = getattr(getattr(model, "ddpm", None), "dynamics", None)
                new_parameter = getattr(
                    dynamics,
                    "target_residue_atom_condition_embedding",
                    None,
                )
                model_state_dict = model.state_dict()
                if (
                    not isinstance(model, LigandPocketDDPM)
                    or model.target_residue_atom_conditioning is not True
                    or getattr(dynamics, "target_residue_atom_conditioning", None)
                    is not True
                    or not isinstance(new_parameter, torch.nn.Parameter)
                    or list(new_parameter.shape) != [32]
                    or int(torch.count_nonzero(new_parameter).item()) != 0
                    or len(model_state_dict) != 123
                    or _NEW_STATE_KEY not in model_state_dict
                    or migration_report.get("base_state_key_count") != 122
                    or migration_report.get("model_state_key_count") != 123
                    or migration_report.get("filled_state_keys") != [_NEW_STATE_KEY]
                    or migration_report.get("missing_keys") != []
                    or migration_report.get("unexpected_keys") != []
                    or migration_report.get("strict_load") is not True
                    or migration_report.get("base_state_dict_modified") is not False
                    or list(state_dict) != base_keys
                    or any(
                        id(state_dict[key]) != base_tensor_ids[key]
                        or state_dict[key]._version != base_tensor_versions[key]
                        or not torch.equal(state_dict[key], base_tensor_values[key])
                        for key in base_keys
                    )
                ):
                    _raise_invalid()

            final_stat = os.lstat(path)
            final_bytes = path.read_bytes()
            if (
                stat.S_ISLNK(final_stat.st_mode)
                or not stat.S_ISREG(final_stat.st_mode)
                or final_stat.st_size != _CHECKPOINT_SIZE
                or final_bytes != checkpoint_bytes
            ):
                _raise_invalid()
            return model
        finally:
            torch.random.set_rng_state(entry_rng)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)
