"""Public in-memory interface for Current11 multi-boundary ingestion."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)


IMPLEMENTATION_VERSION = (
    "covapie_current11_multi_boundary_human_review_ingestion_interface_v1"
)
DESIGN_COMMIT = "bccd85194fbd19a55a77e998f5b9bcab5465b751"
DESIGN_PRODUCTION_SHA256 = (
    "91899640e89cc462aac0a28245873da12ba573b8658a30e193da7ec9fac92771"
)
PUBLIC_FUNCTION_NAME = (
    "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1"
)

__all__ = (
    "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1",
)


_INVARIANT_ERROR = "INGESTION_RESPONSE_INVARIANT_INVALID"


def _mutable_object_ids(value: Any) -> set[int]:
    """Collect mutable container identities without following arbitrary APIs."""

    mutable_ids: set[int] = set()
    visited: set[int] = set()

    def visit(item: Any) -> None:
        identity = id(item)
        if identity in visited:
            return
        visited.add(identity)
        if type(item) is dict:
            mutable_ids.add(identity)
            for key, nested in item.items():
                visit(key)
                visit(nested)
        elif type(item) is list:
            mutable_ids.add(identity)
            for nested in item:
                visit(nested)
        elif type(item) is set:
            mutable_ids.add(identity)
            for nested in item:
                visit(nested)
        elif type(item) is bytearray:
            mutable_ids.add(identity)
        elif type(item) is tuple:
            for nested in item:
                visit(nested)

    visit(value)
    return mutable_ids


def evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
    existing_multi_boundary_authority_records: Sequence[
        Mapping[str, Any]
    ] = (),
) -> dict[str, Any]:
    """Evaluate ingestion in memory through the committed design semantics."""

    byte_inputs = (
        adapter_response_payload,
        source_multi_boundary_submission_bundle,
        source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle,
    )
    byte_snapshots = tuple(
        bytes(value) if type(value) is bytes else None
        for value in byte_inputs
    )
    try:
        existing_snapshot = copy.deepcopy(
            existing_multi_boundary_authority_records
        )
        existing_snapshot_available = True
    except (TypeError, ValueError, RecursionError):
        existing_snapshot = None
        existing_snapshot_available = False
        existing_for_evaluation = (
            existing_multi_boundary_authority_records
        )
    except Exception as error:
        raise ValueError(_INVARIANT_ERROR) from error
    else:
        # deepcopy preserves the singleton identity of the normal empty-tuple
        # default.  Use an equivalent independent Sequence root so that the
        # same isolation checks apply without changing design semantics.
        if (
            type(existing_multi_boundary_authority_records) is tuple
            and not existing_multi_boundary_authority_records
            and existing_snapshot
            is existing_multi_boundary_authority_records
        ):
            existing_snapshot = []
        try:
            existing_for_evaluation = copy.deepcopy(existing_snapshot)
        except Exception as error:
            raise ValueError(_INVARIANT_ERROR) from error
        caller_mutable_ids = _mutable_object_ids(
            existing_multi_boundary_authority_records
        )
        snapshot_mutable_ids = _mutable_object_ids(existing_snapshot)
        evaluation_mutable_ids = _mutable_object_ids(
            existing_for_evaluation
        )
        if (
            existing_snapshot
            is existing_multi_boundary_authority_records
            or existing_for_evaluation
            is existing_multi_boundary_authority_records
            or existing_for_evaluation is existing_snapshot
            or caller_mutable_ids & snapshot_mutable_ids
            or caller_mutable_ids & evaluation_mutable_ids
            or snapshot_mutable_ids & evaluation_mutable_ids
        ):
            raise ValueError(_INVARIANT_ERROR)

    try:
        private_response = (
            design
            ._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1(
                adapter_response_payload=adapter_response_payload,
                source_multi_boundary_submission_bundle=
                    source_multi_boundary_submission_bundle,
                source_v1_submission_bundle=source_v1_submission_bundle,
                source_v1_ingestion_execution_bundle=
                    source_v1_ingestion_execution_bundle,
                repo_root=repo_root,
                existing_multi_boundary_authority_records=
                    existing_for_evaluation,
            )
        )
        if any(
            snapshot is not None and value != snapshot
            for value, snapshot in zip(byte_inputs, byte_snapshots)
        ):
            raise ValueError(_INVARIANT_ERROR)
        if (
            existing_snapshot_available
            and (
                (
                    list(existing_multi_boundary_authority_records)
                    if (
                        type(
                            existing_multi_boundary_authority_records
                        ) is tuple
                        and type(existing_snapshot) is list
                    )
                    else existing_multi_boundary_authority_records
                )
                != existing_snapshot
                or existing_for_evaluation != existing_snapshot
            )
        ):
            raise ValueError(_INVARIANT_ERROR)
        if type(private_response) is not dict:
            raise ValueError(_INVARIANT_ERROR)

        response = copy.deepcopy(private_response)
        if (
            type(response) is not dict
            or response is private_response
            or response != private_response
            or _mutable_object_ids(response)
            & _mutable_object_ids(private_response)
        ):
            raise ValueError(_INVARIANT_ERROR)
        design._validate_interface_response(response)
    except Exception as error:
        if (
            type(error) is ValueError
            and str(error) == _INVARIANT_ERROR
        ):
            raise
        raise ValueError(_INVARIANT_ERROR) from error
    return response
