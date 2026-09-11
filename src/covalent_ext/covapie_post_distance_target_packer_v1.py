"""Pure in-memory, event-ordered CovaPIE POST distance packing V1.

This module only represents numeric availability.  It does not grant sample
admission, authority, applicability, or permission to enable a loss.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import NoReturn

import torch


__all__ = (
    "COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR",
    "CovapiePostDistanceTargetPackV1",
    "pack_covapie_post_distance_targets_v1",
)


COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR = (
    "COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR"
)

_PRE_COMPONENT_INDEX_V1 = 0
_POST_COMPONENT_INDEX_V1 = 1
_GEOMETRY_COMPONENT_COUNT_V1 = 2


@dataclass(frozen=True)
class CovapiePostDistanceTargetPackV1:
    """An event-ordered POST-only geometry payload on CPU."""

    event_ids: tuple[str, ...]
    pre_post_geometry_target_angstrom: torch.Tensor
    pre_post_geometry_component_valid_mask: torch.Tensor
    pre_post_geometry_component_loss_mask: torch.Tensor


class _PackerInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _PackerInvariantError(reason)


def _event_order(event_ids: object) -> tuple[str, ...]:
    if type(event_ids) not in (list, tuple):
        _fail("EVENT_IDS_ORDERED_SEQUENCE_REQUIRED")
    ordered = tuple(event_ids)
    if not ordered:
        _fail("EVENT_IDS_EMPTY")
    if any(
        type(event_id) is not str
        or not event_id
        or event_id.strip() != event_id
        or not event_id.isprintable()
        for event_id in ordered
    ):
        _fail("EVENT_ID_INVALID")
    if len(set(ordered)) != len(ordered):
        _fail("EVENT_ID_DUPLICATE")
    return ordered  # type: ignore[return-value]


def _mapping_values(
    *,
    event_ids: tuple[str, ...],
    post_distance_by_event: object,
) -> tuple[int | float | None, ...]:
    if not isinstance(post_distance_by_event, Mapping):
        _fail("POST_DISTANCE_MAPPING_REQUIRED")
    try:
        mapping_keys = tuple(post_distance_by_event.keys())
        mapping_key_set = set(mapping_keys)
    except (AttributeError, TypeError):
        _fail("POST_DISTANCE_MAPPING_KEYS_INVALID")
    if len(mapping_keys) != len(mapping_key_set):
        _fail("POST_DISTANCE_MAPPING_KEY_DUPLICATE")
    event_key_set = set(event_ids)
    if event_key_set - mapping_key_set:
        _fail("POST_DISTANCE_EVENT_KEY_MISSING")
    if mapping_key_set - event_key_set:
        _fail("POST_DISTANCE_EVENT_KEY_EXTRA")
    try:
        return tuple(post_distance_by_event[event_id] for event_id in event_ids)
    except (KeyError, TypeError):
        _fail("POST_DISTANCE_EVENT_LOOKUP_FAILED")


def _positive_float32(value: object) -> float:
    if type(value) not in (int, float):
        _fail("POST_DISTANCE_PYTHON_NUMBER_REQUIRED")
    try:
        normalized = float(value)
    except (OverflowError, TypeError, ValueError):
        _fail("POST_DISTANCE_NOT_FINITE_POSITIVE")
    if not math.isfinite(normalized) or normalized <= 0.0:
        _fail("POST_DISTANCE_NOT_FINITE_POSITIVE")
    converted = torch.tensor(normalized, dtype=torch.float32, device="cpu")
    float32_value = float(converted.item())
    if not math.isfinite(float32_value) or float32_value <= 0.0:
        _fail("POST_DISTANCE_FLOAT32_NOT_FINITE_POSITIVE")
    return float32_value


def pack_covapie_post_distance_targets_v1(
    *,
    event_ids: Sequence[str],
    post_distance_by_event: Mapping[str, int | float | None],
) -> CovapiePostDistanceTargetPackV1:
    """Pack POST values by explicit event order without granting loss rights."""

    try:
        ordered_event_ids = _event_order(event_ids)
        raw_values = _mapping_values(
            event_ids=ordered_event_ids,
            post_distance_by_event=post_distance_by_event,
        )
        batch_size = len(ordered_event_ids)
        target = torch.full(
            (batch_size, _GEOMETRY_COMPONENT_COUNT_V1),
            float("nan"),
            dtype=torch.float32,
            device="cpu",
        )
        valid = torch.zeros(
            (batch_size, _GEOMETRY_COMPONENT_COUNT_V1),
            dtype=torch.bool,
            device="cpu",
        )
        loss = torch.zeros_like(valid)
        for row_index, raw_value in enumerate(raw_values):
            if raw_value is None:
                continue
            target[row_index, _POST_COMPONENT_INDEX_V1] = _positive_float32(
                raw_value
            )
            valid[row_index, _POST_COMPONENT_INDEX_V1] = True

        if (
            not bool(torch.isnan(target[:, _PRE_COMPONENT_INDEX_V1]).all().item())
            or bool(valid[:, _PRE_COMPONENT_INDEX_V1].any().item())
            or bool(loss.any().item())
        ):
            _fail("POST_ONLY_OUTPUT_INVARIANT_FAILED")
        return CovapiePostDistanceTargetPackV1(
            event_ids=ordered_event_ids,
            pre_post_geometry_target_angstrom=target,
            pre_post_geometry_component_valid_mask=valid,
            pre_post_geometry_component_loss_mask=loss,
        )
    except Exception as error:
        if isinstance(error, _PackerInvariantError):
            raise ValueError(
                f"{COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR}:"
                f"{error.reason}"
            ) from error
        if (
            type(error) is ValueError
            and str(error).startswith(
                COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR
            )
        ):
            raise
        raise ValueError(COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR) from error
