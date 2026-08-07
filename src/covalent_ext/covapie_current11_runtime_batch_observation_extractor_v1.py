"""Pure runtime transport into the Current11 compiler observation Exact14."""

from __future__ import annotations

import json
from typing import NoReturn

import numpy as np
import torch


__all__ = ("extract_covapie_current11_runtime_batch_observation_v1",)

_ERROR = "COVAPIE_CURRENT11_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_V1_ERROR"
_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_input_v1"
_RUNTIME_SCHEMA = "processed_ligand_pocket_dataset_collate_observation_no_virtual_v1"
_SAMPLE_KEY_SCHEMA = "covapie_sample_index_row_id_in_names_v1"
_VIRTUAL_POLICY = "no_virtual_nodes_v1"
_FIELDS = (
    "schema_version",
    "runtime_batch_schema_version",
    "sample_key_schema_version",
    "batch_sample_keys",
    "ligand_lengths",
    "pocket_lengths",
    "ligand_membership",
    "pocket_membership",
    "joint_layout_descriptor",
    "virtual_node_policy",
    "receptors",
    "consistency_buffer_lengths",
    "debug_coordinates",
    "debug_rank_metadata",
)
_BUFFER_SPECS = (
    ("lig_coords", "ligand_coords", "ligand"),
    ("lig_one_hot", "ligand_one_hot", "ligand"),
    ("pocket_coords", "pocket_coords", "pocket"),
    ("pocket_one_hot", "pocket_one_hot", "pocket"),
)


class _RuntimeBatchObservationExtractorError(ValueError):
    reason: str

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(_ERROR)


def _fail(reason: str) -> NoReturn:
    raise _RuntimeBatchObservationExtractorError(reason)


def _string_scalar(value: object, *, reason: str) -> str:
    if type(value) is str:
        return value
    if type(value) is np.str_:
        try:
            converted = value.item()
        except BaseException as error:
            raise _RuntimeBatchObservationExtractorError(reason) from error
        if type(converted) is str:
            return converted
    _fail(reason)


def _sample_keys(batch: dict[str, object]) -> list[str]:
    if "names" not in batch:
        _fail("missing_names")
    raw = batch["names"]
    if type(raw) is not list:
        _fail("invalid_sample_key_scalar")
    result: list[str] = []
    for value in raw:
        converted = _string_scalar(value, reason="invalid_sample_key_scalar")
        if not converted or converted.strip() != converted:
            _fail("invalid_sample_key_scalar")
        result.append(converted)
    return result


def _integral_tensor_list(
    value: object, *, batch_size: int, reason: str,
) -> list[int]:
    if (
        not isinstance(value, torch.Tensor)
        or value.device.type != "cpu"
        or value.ndim != 1
        or len(value) != batch_size
        or value.dtype is torch.bool
        or value.dtype.is_floating_point
        or value.dtype.is_complex
    ):
        _fail(reason)
    try:
        raw = value.tolist()
    except BaseException as error:
        raise _RuntimeBatchObservationExtractorError(reason) from error
    if (
        type(raw) is not list
        or any(type(item) is not int or item < 0 for item in raw)
    ):
        _fail(reason)
    return raw


def _role_lengths(
    batch: dict[str, object], *, field: str, batch_size: int,
) -> list[int]:
    if field not in batch:
        _fail("invalid_role_length")
    return _integral_tensor_list(
        batch[field], batch_size=batch_size, reason="invalid_role_length",
    )


def _receptors(batch: dict[str, object], *, batch_size: int) -> list[str]:
    raw = batch.get("receptors")
    if type(raw) is not list or len(raw) != batch_size:
        _fail("unsupported_runtime_type")
    return [
        _string_scalar(value, reason="unsupported_runtime_type") for value in raw
    ]


def _validate_virtual_nodes(
    batch: dict[str, object], *, batch_size: int,
) -> None:
    for key in batch:
        if (
            type(key) is str
            and "virtual" in key.lower()
            and key != "num_virtual_atoms"
        ):
            _fail("virtual_nodes_not_supported")
    if "num_virtual_atoms" not in batch:
        return
    values = _integral_tensor_list(
        batch["num_virtual_atoms"],
        batch_size=batch_size,
        reason="virtual_nodes_not_supported",
    )
    if any(value != 0 for value in values):
        _fail("virtual_nodes_not_supported")


def _membership(value: object, *, lengths: list[int]) -> list[int]:
    if (
        not isinstance(value, torch.Tensor)
        or value.device.type != "cpu"
        or value.ndim != 1
        or value.dtype is torch.bool
        or value.dtype.is_complex
        or value.numel() != sum(lengths)
    ):
        _fail("invalid_membership")
    floating = value.dtype.is_floating_point
    if floating:
        try:
            if (
                not bool(torch.isfinite(value).all().item())
                or not torch.equal(value, torch.trunc(value))
                or bool((value < 0).any().item())
            ):
                _fail("invalid_membership")
        except _RuntimeBatchObservationExtractorError:
            raise
        except BaseException as error:
            raise _RuntimeBatchObservationExtractorError(
                "invalid_membership"
            ) from error
    try:
        raw = value.tolist()
    except BaseException as error:
        raise _RuntimeBatchObservationExtractorError("invalid_membership") from error
    if type(raw) is not list:
        _fail("invalid_membership")
    converted: list[int] = []
    for item in raw:
        if floating:
            if type(item) is not float:
                _fail("invalid_membership")
            converted.append(int(item))
        else:
            if type(item) is not int or item < 0:
                _fail("invalid_membership")
            converted.append(item)
    expected = [
        ordinal
        for ordinal, length in enumerate(lengths)
        for _ in range(length)
    ]
    if converted != expected:
        _fail("invalid_membership")
    return converted


def _consistency_buffer_lengths(
    batch: dict[str, object], *, ligand_total: int, pocket_total: int,
) -> dict[str, int]:
    expected = {"ligand": ligand_total, "pocket": pocket_total}
    result: dict[str, int] = {}
    for runtime_field, output_field, role in _BUFFER_SPECS:
        if runtime_field not in batch:
            _fail("buffer_length_mismatch")
        value = batch[runtime_field]
        if not isinstance(value, torch.Tensor) or value.device.type != "cpu":
            _fail("unsupported_runtime_type")
        if value.ndim < 1:
            _fail("buffer_length_mismatch")
        leading = value.shape[0]
        if type(leading) is not int:
            leading = int(leading)
        if leading != expected[role]:
            _fail("buffer_length_mismatch")
        result[output_field] = leading
    return result


def _extract(batch: dict[str, object]) -> dict[str, object]:
    if type(batch) is not dict:
        _fail("unsupported_runtime_type")
    sample_keys = _sample_keys(batch)
    batch_size = len(sample_keys)
    if batch_size == 0:
        _fail("unsupported_empty_batch")
    ligand_lengths = _role_lengths(
        batch, field="num_lig_atoms", batch_size=batch_size,
    )
    pocket_lengths = _role_lengths(
        batch, field="num_pocket_nodes", batch_size=batch_size,
    )
    receptors = _receptors(batch, batch_size=batch_size)
    _validate_virtual_nodes(batch, batch_size=batch_size)
    if "lig_mask" not in batch or "pocket_mask" not in batch:
        _fail("invalid_membership")
    ligand_membership = _membership(
        batch["lig_mask"], lengths=ligand_lengths,
    )
    pocket_membership = _membership(
        batch["pocket_mask"], lengths=pocket_lengths,
    )
    buffer_lengths = _consistency_buffer_lengths(
        batch,
        ligand_total=sum(ligand_lengths),
        pocket_total=sum(pocket_lengths),
    )
    result: dict[str, object] = {
        "schema_version": _SCHEMA,
        "runtime_batch_schema_version": _RUNTIME_SCHEMA,
        "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
        "batch_sample_keys": sample_keys,
        "ligand_lengths": ligand_lengths,
        "pocket_lengths": pocket_lengths,
        "ligand_membership": ligand_membership,
        "pocket_membership": pocket_membership,
        "joint_layout_descriptor": None,
        "virtual_node_policy": _VIRTUAL_POLICY,
        "receptors": receptors,
        "consistency_buffer_lengths": buffer_lengths,
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }
    if tuple(result) != _FIELDS:
        _fail("unsupported_runtime_type")
    try:
        json.dumps(result, ensure_ascii=True, allow_nan=False)
    except BaseException as error:
        raise _RuntimeBatchObservationExtractorError(
            "unsupported_runtime_type"
        ) from error
    return result


def extract_covapie_current11_runtime_batch_observation_v1(
    *, batch: dict[str, object],
) -> dict[str, object]:
    """Extract one non-empty JSON-safe Current11 runtime observation."""
    try:
        return _extract(batch)
    except BaseException as error:
        if type(error) is _RuntimeBatchObservationExtractorError:
            raise
        raise _RuntimeBatchObservationExtractorError(
            "unsupported_runtime_type"
        ) from error
