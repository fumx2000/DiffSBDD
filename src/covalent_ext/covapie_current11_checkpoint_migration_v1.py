"""Exact legacy checkpoint validation and bounded Current11 migration V1."""

from __future__ import annotations

import hashlib
import math
import stat
from argparse import Namespace
from pathlib import Path
from typing import NoReturn

import torch
from torch import nn


__all__ = (
    "COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR",
    "COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1",
    "COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1",
    "LEGACY_ALLOWED_NEW_EXACT_KEYS_V1",
    "LEGACY_ALLOWED_NEW_PREFIXES_V1",
    "load_covapie_current11_legacy_checkpoint_v1",
    "migrate_covapie_current11_legacy_checkpoint_state_dict_v1",
)


COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR = (
    "COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR"
)
COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
LEGACY_ALLOWED_NEW_EXACT_KEYS_V1 = (
    "ddpm.dynamics.target_residue_atom_condition_embedding",
)
LEGACY_ALLOWED_NEW_PREFIXES_V1 = (
    "covapie_current11_auxiliary_model_v1.",
)

_EXPECTED_LEGACY_STATE_KEY_COUNT_V1 = 122
_EXPECTED_HISTORICAL_HPARAMETER_KEYS_V1 = frozenset((
    "outdir",
    "dataset",
    "datadir",
    "batch_size",
    "lr",
    "egnn_params",
    "diffusion_params",
    "num_workers",
    "augment_noise",
    "augment_rotation",
    "clip_grad",
    "eval_epochs",
    "eval_params",
    "visualize_sample_epoch",
    "visualize_chain_epoch",
    "auxiliary_loss",
    "loss_params",
    "mode",
    "node_histogram",
    "pocket_representation",
    "virtual_nodes",
))
_EXPECTED_EGNN_PARAMS_V1 = {
    "device": "cuda",
    "edge_cutoff_ligand": None,
    "edge_cutoff_pocket": 5.0,
    "edge_cutoff_interaction": 5.0,
    "reflection_equivariant": False,
    "joint_nf": 32,
    "hidden_nf": 128,
    "n_layers": 5,
    "attention": True,
    "tanh": True,
    "norm_constant": 1,
    "inv_sublayers": 1,
    "sin_embedding": False,
    "aggregation_method": "sum",
    "normalization_factor": 100,
}
_EXPECTED_DIFFUSION_PARAMS_V1 = {
    "diffusion_steps": 500,
    "diffusion_noise_schedule": "polynomial_2",
    "diffusion_noise_precision": 0.0005,
    "diffusion_loss_type": "l2",
    "normalize_factors": [1, 4],
}
_EXPECTED_EVAL_PARAMS_V1 = {
    "n_eval_samples": 100,
    "eval_batch_size": 100,
    "smiles_file": None,
    "n_visualize_samples": 5,
    "keep_frames": 100,
}
_EXPECTED_LOSS_PARAMS_V1 = {
    "max_weight": 0.001,
    "schedule": "linear",
    "clamp_lj": 3.0,
}
_EXPECTED_SCALAR_HPARAMETERS_V1 = {
    "outdir": "",
    "dataset": "crossdock",
    "datadir": "",
    "batch_size": 16,
    "lr": 0.001,
    "num_workers": 0,
    "augment_noise": 0,
    "augment_rotation": False,
    "clip_grad": True,
    "eval_epochs": 50,
    "visualize_sample_epoch": 50,
    "visualize_chain_epoch": 50,
    "auxiliary_loss": False,
    "mode": "pocket_conditioning",
    "pocket_representation": "full-atom",
    "virtual_nodes": False,
}
_EXPECTED_NODE_HISTOGRAM_ROWS_V1 = 107
_EXPECTED_NODE_HISTOGRAM_COLUMNS_V1 = 1671
_AUXILIARY_ZERO_DELTA_KEYS_V1 = (
    "covapie_current11_auxiliary_model_v1.role_embedding.weight",
    "covapie_current11_auxiliary_model_v1.task_embedding.weight",
    "covapie_current11_auxiliary_model_v1.generation_state_embedding.weight",
    "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.weight",
    "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.2.weight",
    "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.2.bias",
)


class _CheckpointMigrationInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _CheckpointMigrationInvariantError()


def _public_error(error: BaseException) -> NoReturn:
    if (
        type(error) is ValueError
        and str(error) == COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR
    ):
        raise error
    raise ValueError(COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR) from error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise _CheckpointMigrationInvariantError() from error
    return digest.hexdigest()


def _safe_regular_file(path: Path) -> tuple[int, str]:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise _CheckpointMigrationInvariantError() from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail()
    return metadata.st_size, _sha256(path)


def _is_tensor_dictionary(value: object) -> bool:
    return isinstance(value, dict) and all(
        type(key) is str and isinstance(item, torch.Tensor)
        for key, item in value.items()
    )


def _plain_mapping(value: object) -> dict[str, object]:
    if type(value) is Namespace:
        source = vars(value)
    elif type(value) is dict:
        source = value
    else:
        _fail()
    if any(type(key) is not str for key in source):
        _fail()
    return {key: _plain_value(item) for key, item in source.items()}


def _plain_value(value: object) -> object:
    if value is None or type(value) in (bool, int, float, str):
        if type(value) is float and not math.isfinite(value):
            _fail()
        return value
    if type(value) in (list, tuple):
        return [_plain_value(item) for item in value]
    if type(value) in (dict, Namespace):
        return _plain_mapping(value)
    _fail()


def _same_exact_value(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return (
            tuple(actual) == tuple(expected)
            and all(
                _same_exact_value(actual[key], expected[key])
                for key in expected
            )
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _same_exact_value(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return bool(actual == expected)


def _validated_node_histogram(value: object) -> list[list[float]]:
    normalized = _plain_value(value)
    if (
        type(normalized) is not list
        or len(normalized) != _EXPECTED_NODE_HISTOGRAM_ROWS_V1
    ):
        _fail()
    result: list[list[float]] = []
    positive = False
    for row in normalized:
        if (
            type(row) is not list
            or len(row) != _EXPECTED_NODE_HISTOGRAM_COLUMNS_V1
        ):
            _fail()
        normalized_row: list[float] = []
        for item in row:
            if type(item) is not float or not math.isfinite(item) or item < 0.0:
                _fail()
            normalized_row.append(item)
            positive = positive or item > 0.0
        result.append(normalized_row)
    if not positive:
        _fail()
    return result


def _validated_legacy_constructor_contract_v1(
    hyper_parameters: object,
) -> dict[str, object]:
    if (
        type(hyper_parameters) is not dict
        or set(hyper_parameters) != _EXPECTED_HISTORICAL_HPARAMETER_KEYS_V1
    ):
        _fail()
    normalized = {
        key: _plain_value(value) for key, value in hyper_parameters.items()
    }
    for key, expected in _EXPECTED_SCALAR_HPARAMETERS_V1.items():
        if not _same_exact_value(normalized.get(key), expected):
            _fail()
    expected_mappings = {
        "egnn_params": _EXPECTED_EGNN_PARAMS_V1,
        "diffusion_params": _EXPECTED_DIFFUSION_PARAMS_V1,
        "eval_params": _EXPECTED_EVAL_PARAMS_V1,
        "loss_params": _EXPECTED_LOSS_PARAMS_V1,
    }
    for key, expected in expected_mappings.items():
        if not _same_exact_value(normalized.get(key), expected):
            _fail()
    normalized["node_histogram"] = _validated_node_histogram(
        normalized.get("node_histogram")
    )
    normalized["schema_version"] = (
        "covapie_current11_validated_legacy_constructor_contract_v1"
    )
    normalized["node_histogram_source"] = (
        "exact_legacy_checkpoint_hyperparameters"
    )
    normalized["synthetic_node_histogram_used"] = False
    return normalized


def load_covapie_current11_legacy_checkpoint_v1(
    *, checkpoint_path: Path,
) -> dict[str, object]:
    """Load the sole authorized legacy checkpoint and normalized constructor."""

    try:
        if type(checkpoint_path) is not type(Path()) or not checkpoint_path.is_absolute():
            _fail()
        size, digest = _safe_regular_file(checkpoint_path)
        if (
            size != COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
            or digest != COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
        ):
            _fail()
        payload = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
        if type(payload) is not dict:
            _fail()
        state_dict = payload.get("state_dict")
        hyper_parameters = payload.get("hyper_parameters")
        if (
            not _is_tensor_dictionary(state_dict)
            or len(state_dict) != _EXPECTED_LEGACY_STATE_KEY_COUNT_V1
        ):
            _fail()
        constructor = _validated_legacy_constructor_contract_v1(
            hyper_parameters
        )
        if any(
            key in LEGACY_ALLOWED_NEW_EXACT_KEYS_V1
            or key.startswith(LEGACY_ALLOWED_NEW_PREFIXES_V1)
            for key in state_dict
        ):
            _fail()
        return {
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": digest,
            "checkpoint_size_bytes": size,
            "checkpoint_payload_type": type(payload).__name__,
            "checkpoint_top_level_keys": tuple(payload),
            "checkpoint_state_dict_key_count": len(state_dict),
            "checkpoint_hyper_parameter_keys": tuple(hyper_parameters),
            "historical_pytorch_lightning_version": payload.get(
                "pytorch-lightning_version"
            ),
            "legacy_constructor": constructor,
            "state_dict": state_dict,
        }
    except BaseException as error:
        _public_error(error)


def _all_zero(tensor: torch.Tensor) -> bool:
    return bool(torch.equal(tensor, torch.zeros_like(tensor)))


def _migrate_impl(
    *, model: nn.Module, checkpoint_state_dict: object,
) -> dict[str, object]:
    if not isinstance(model, nn.Module) or not _is_tensor_dictionary(
        checkpoint_state_dict
    ):
        _fail()
    target_state = model.state_dict()
    if not _is_tensor_dictionary(target_state):
        _fail()
    target_keys = set(target_state)
    checkpoint_keys = set(checkpoint_state_dict)
    allowed_exact = set(LEGACY_ALLOWED_NEW_EXACT_KEYS_V1)
    target_auxiliary_keys = {
        key
        for key in target_keys
        if key.startswith(LEGACY_ALLOWED_NEW_PREFIXES_V1)
    }
    if (
        not allowed_exact <= target_keys
        or not target_auxiliary_keys
        or any(
            key in allowed_exact
            or key.startswith(LEGACY_ALLOWED_NEW_PREFIXES_V1)
            for key in checkpoint_keys
        )
    ):
        _fail()

    shared_keys = target_keys & checkpoint_keys
    target_only_keys = target_keys - checkpoint_keys
    checkpoint_only_keys = checkpoint_keys - target_keys
    target_only_auxiliary_keys = {
        key
        for key in target_only_keys
        if key.startswith(LEGACY_ALLOWED_NEW_PREFIXES_V1)
    }
    target_only_exact_keys = target_only_keys - target_only_auxiliary_keys
    shape_mismatches = {
        key
        for key in shared_keys
        if (
            target_state[key].shape != checkpoint_state_dict[key].shape
            or target_state[key].dtype != checkpoint_state_dict[key].dtype
        )
    }
    if (
        checkpoint_only_keys
        or shape_mismatches
        or target_only_exact_keys != allowed_exact
        or target_only_auxiliary_keys != target_auxiliary_keys
        or shared_keys != target_keys - allowed_exact - target_auxiliary_keys
    ):
        _fail()

    fresh_target_only = {
        key: target_state[key].detach().clone() for key in target_only_keys
    }
    if (
        any(key not in target_state for key in _AUXILIARY_ZERO_DELTA_KEYS_V1)
        or not _all_zero(target_state[LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]])
        or any(
            not _all_zero(target_state[key])
            for key in _AUXILIARY_ZERO_DELTA_KEYS_V1
        )
    ):
        _fail()

    complete_target_state = {
        key: checkpoint_state_dict[key] if key in shared_keys else target_state[key]
        for key in target_state
    }
    load_result = model.load_state_dict(complete_target_state, strict=True)
    missing_keys = tuple(load_result.missing_keys)
    unexpected_keys = tuple(load_result.unexpected_keys)
    if missing_keys or unexpected_keys:
        _fail()

    migrated_state = model.state_dict()
    if any(
        not torch.equal(migrated_state[key], fresh_target_only[key])
        for key in target_only_keys
    ):
        _fail()
    shared_equal = sum(
        int(torch.equal(
            migrated_state[key].detach().cpu(),
            checkpoint_state_dict[key].detach().cpu(),
        ))
        for key in shared_keys
    )
    if shared_equal != len(shared_keys):
        _fail()
    if (
        not _all_zero(migrated_state[LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]])
        or any(
            not _all_zero(migrated_state[key])
            for key in _AUXILIARY_ZERO_DELTA_KEYS_V1
        )
    ):
        _fail()
    return {
        "checkpoint_key_count": len(checkpoint_keys),
        "target_model_key_count": len(target_keys),
        "shared_key_count": len(shared_keys),
        "target_only_key_count": len(target_only_keys),
        "checkpoint_only_key_count": len(checkpoint_only_keys),
        "shared_shape_mismatch_count": len(shape_mismatches),
        "target_only_exact_keys": tuple(sorted(target_only_exact_keys)),
        "target_only_auxiliary_keys": tuple(sorted(target_only_auxiliary_keys)),
        "legacy_migration_policy_exact": True,
        "full_target_strict_load": True,
        "migration_missing_keys": missing_keys,
        "migration_unexpected_keys": unexpected_keys,
        "shared_checkpoint_tensor_equality_count": shared_equal,
        "target_residue_embedding_preserved_zero_after_migration": True,
        "auxiliary_zero_delta_initialization_preserved": True,
    }


def migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
    *, model: nn.Module, checkpoint_state_dict: object,
) -> dict[str, object]:
    """Strictly merge only the exact bounded legacy-to-Current11 delta."""

    try:
        return _migrate_impl(
            model=model, checkpoint_state_dict=checkpoint_state_dict
        )
    except BaseException as error:
        _public_error(error)
