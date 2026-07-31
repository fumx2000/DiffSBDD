"""Design the Current11 authority materialization precondition and precedence."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as multi_design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
    as multi_execution,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as legacy_interface,
)


__all__ = ()


_DESIGN_VERSION = (
    "covapie_current11_multi_boundary_authority_materialization_"
    "and_unified_precedence_design_v1"
)
_FUTURE_ACTION_NAMES = (
    "implement_covapie_current11_multi_boundary_authority_bundle_v1",
    "implement_covapie_current11_unified_effective_authority_view_v1",
)
_LEGACY_NAMESPACE = "legacy_exact_one_boundary_v1"
_MULTI_NAMESPACE = "exact_two_boundaries_multi_boundary_v1"
_LEGACY_REASON = "ACTIVE_LEGACY_EXACT_ONE_ONLY"
_MULTI_REASON = (
    "ACTIVE_EXACT_TWO_SELECTED_OVER_QUARANTINED_EXACT_ONE_FOR_EFFECTIVE_VIEW"
)
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_MULTI_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
_LEGACY_ONLY_SAMPLES = (
    *_EXPECTED_SAMPLES[:5],
    _EXPECTED_SAMPLES[10],
)
_RESOLUTION_FIELDS = (
    "sample_index_row_id",
    "legacy_v1_authority_record_sha256",
    "legacy_v1_authority_status",
    "legacy_v1_sample_quarantined",
    "multi_boundary_authority_record_sha256",
    "multi_boundary_authority_status",
    "effective_authority_namespace",
    "effective_authority_record_sha256",
    "effective_boundary_cardinality",
    "precedence_reason",
    "source_authorities_unchanged",
    "unified_precedence_resolution_record_sha256",
)
_RESPONSE_FIELDS = (
    "unified_authority_precedence_design_version",
    "source_v1_ingestion_execution_bundle_filesystem_sha256",
    "source_v1_ingestion_execution_bundle_sha256",
    "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256",
    "source_multi_boundary_ingestion_execution_bundle_sha256",
    "resolution_records",
    "effective_legacy_exact_one_count",
    "effective_multi_boundary_exact_two_count",
    "ready_for_authority_and_unified_view_implementation",
    "unified_authority_precedence_design_response_sha256",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ERROR = "CURRENT11_UNIFIED_AUTHORITY_PRECEDENCE_DESIGN_INVALID"


def _fail(reason: str) -> None:
    raise ValueError(f"{_ERROR}:{reason}")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (
        TypeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError(f"{_ERROR}:CANONICAL_JSON_INVALID") from error


def _record_sha256(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    return _sha256(_canonical_json_bytes({
        field: record[field] for field in fields if field != digest_field
    }))


def _validate_legacy_execution(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    try:
        committed_context = (
            legacy_interface
            .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
                repo_root
            )
        )
        legacy_design.validate_ingestion_authority_context(committed_context)
        expected_context_sha256 = committed_context.context_record[
            "ingestion_authority_context_record_sha256"
        ]
        execution = multi_design._decode_v1_execution(
            source_v1_ingestion_execution_bundle,
            source_v1_submission_bundle=source_v1_submission_bundle,
            expected_authority_context_record_sha256=expected_context_sha256,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{_ERROR}:LEGACY_V1_EXECUTION_INVALID") from error

    authorities = execution["new_authority_records"]
    results = execution["ingestion_result_records"]
    if (
        tuple(authority["sample_index_row_id"] for authority in authorities)
        != _EXPECTED_SAMPLES
        or tuple(result["sample_index_row_id"] for result in results)
        != _EXPECTED_SAMPLES
        or any(
            authority["supersedes_authority_record_sha256"] != ""
            for authority in authorities
        )
    ):
        _fail("LEGACY_V1_NAMESPACE_INVALID")
    return execution


def _validate_multi_execution(
    *,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    legacy_execution: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        _, execution = multi_design._strict_json_object(
            source_multi_boundary_ingestion_execution_bundle
        )
        if tuple(execution) != multi_execution.EXACT16_FIELDS:
            _fail("MULTI_EXECUTION_EXACT16_INVALID")
        if (
            execution[
                "multi_boundary_ingestion_execution_bundle_version"
            ] != multi_execution.EXECUTION_BUNDLE_VERSION
            or execution["source_v1_submission_bundle_sha256"]
            != _sha256(source_v1_submission_bundle)
            or execution[
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
            ] != _sha256(source_v1_ingestion_execution_bundle)
            or execution["source_v1_ingestion_execution_bundle_sha256"]
            != legacy_execution["ingestion_execution_bundle_sha256"]
            or execution["batch_passed"] is not True
            or type(execution["ingestion_result_records"]) is not list
            or type(execution["new_authority_records"]) is not list
            or len(execution["ingestion_result_records"]) != 5
            or len(execution["new_authority_records"]) != 5
            or execution[
                "multi_boundary_ingestion_execution_bundle_sha256"
            ] != _record_sha256(
                execution,
                multi_execution.EXACT16_FIELDS,
                "multi_boundary_ingestion_execution_bundle_sha256",
            )
        ):
            _fail("MULTI_EXECUTION_LINEAGE_OR_DIGEST_INVALID")

        results = execution["ingestion_result_records"]
        authorities = execution["new_authority_records"]
        for result in results:
            multi_design._validate_result_record(result)
        for authority in authorities:
            multi_design._validate_authority_record(authority)

        response: dict[str, Any] = {
            "multi_boundary_ingestion_interface_response_version":
                execution["ingestion_interface_response_version"],
            "authority_context_record_sha256":
                execution["authority_context_record_sha256"],
            "batch_passed": execution["batch_passed"],
            "ingestion_result_records": tuple(results),
            "new_authority_records": tuple(authorities),
            "multi_boundary_ingestion_interface_response_sha256":
                execution["ingestion_interface_response_sha256"],
        }
        multi_design._validate_interface_response(response)
        if (
            tuple(result["sample_index_row_id"] for result in results)
            != _MULTI_SAMPLES
            or tuple(
                authority["sample_index_row_id"]
                for authority in authorities
            ) != _MULTI_SAMPLES
        ):
            _fail("MULTI_EXECUTION_SAMPLE_ORDER_INVALID")

        decisions = tuple(
            authority["review_decision"] for authority in authorities
        )
        if (
            decisions.count("accept_verified_two_boundary_proposal") != 4
            or decisions.count(
                "revise_two_boundary_atom_set_and_boundaries"
            ) != 1
            or decisions.count("quarantine") != 0
        ):
            _fail("MULTI_EXECUTION_DECISION_PROFILE_INVALID")

        legacy_by_sample = {
            authority["sample_index_row_id"]: authority
            for authority in legacy_execution["new_authority_records"]
        }
        observed_authority_shas: set[str] = set()
        expected_result_effect = (
            "passed",
            True,
            False,
            "PASSED",
            True,
            False,
            False,
            True,
            True,
        )
        for result, authority in zip(results, authorities):
            sample = authority["sample_index_row_id"]
            predecessor = legacy_by_sample[sample]
            authority_sha = authority[
                "multi_boundary_authority_record_sha256"
            ]
            if (
                (
                    result["outcome"],
                    result["passed"],
                    result["blocks_batch"],
                    result["reason"],
                    result["review_completed"],
                    result["idempotent_replay"],
                    result["conflicting_existing_authority"],
                    result["consumed_review_record"],
                    result["consumed_ingestion_envelope"],
                ) != expected_result_effect
                or result["submission_batch_id"]
                != execution["submission_batch_id"]
                or result["sample_index_row_id"] != sample
                or result["source_multi_boundary_review_record_sha256"]
                != authority["source_multi_boundary_review_record_sha256"]
                or result["source_ingestion_envelope_sha256"]
                != authority["source_ingestion_envelope_sha256"]
                or result["review_decision"] != authority["review_decision"]
                or result["authority_disposition"]
                != authority["authority_disposition"]
                or result["authority_record_sha256"] != authority_sha
                or authority_sha in observed_authority_shas
                or authority[
                    "source_multi_boundary_submission_bundle_sha256"
                ] != execution[
                    "source_multi_boundary_submission_bundle_sha256"
                ]
                or authority[
                    "source_multi_boundary_submission_adapter_response_sha256"
                ] != execution["source_adapter_response_sha256"]
                or authority[
                    "source_v1_quarantine_authority_record_sha256"
                ] != predecessor["authority_record_sha256"]
                or authority["source_v1_review_record_sha256"]
                != predecessor["source_review_record_sha256"]
                or authority["v1_quarantine_authority_unchanged"] is not True
                or authority["authority_status"] != "active"
                or authority["sample_quarantined"] is not False
                or authority[
                    "complete_warhead_atom_set_authority_available"
                ] is not True
                or authority[
                    "exact_two_attachment_boundaries_authority_available"
                ] is not True
            ):
                _fail("MULTI_EXECUTION_FRESH_AUTHORITY_LINKAGE_INVALID")
            observed_authority_shas.add(authority_sha)
    except ValueError as error:
        if str(error).startswith(_ERROR):
            raise
        raise ValueError(f"{_ERROR}:MULTI_EXECUTION_INVALID") from error
    except (KeyError, TypeError) as error:
        raise ValueError(f"{_ERROR}:MULTI_EXECUTION_INVALID") from error
    return execution


def _build_resolution_records(
    *,
    legacy_execution: Mapping[str, Any],
    multi_execution_bundle: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    legacy_authorities = legacy_execution["new_authority_records"]
    multi_authorities = multi_execution_bundle["new_authority_records"]
    legacy_by_sample = {
        authority["sample_index_row_id"]: authority
        for authority in legacy_authorities
    }
    multi_by_sample = {
        authority["sample_index_row_id"]: authority
        for authority in multi_authorities
    }
    if (
        tuple(legacy_by_sample) != _EXPECTED_SAMPLES
        or tuple(multi_by_sample) != _MULTI_SAMPLES
        or len(legacy_by_sample) != 11
        or len(multi_by_sample) != 5
    ):
        _fail("AUTHORITY_NAMESPACE_COVERAGE_INVALID")

    records: list[dict[str, Any]] = []
    for sample in _EXPECTED_SAMPLES:
        legacy = legacy_by_sample[sample]
        multi = multi_by_sample.get(sample)
        if sample in _MULTI_SAMPLES:
            if multi is None:
                _fail("MULTI_AUTHORITY_MISSING")
            if (
                legacy["authority_status"] == "active"
                and multi["authority_status"] == "active"
            ):
                _fail("ACTIVE_ACTIVE_AMBIGUITY")
            if (
                legacy["authority_status"] != "quarantined"
                or legacy["sample_quarantined"] is not True
                or legacy[
                    "exact_one_attachment_boundary_authority_available"
                ] is not False
            ):
                _fail("LEGACY_V1_QUARANTINE_STATUS_DRIFT")
            if (
                multi["authority_status"] != "active"
                or multi["sample_quarantined"] is not False
                or multi[
                    "exact_two_attachment_boundaries_authority_available"
                ] is not True
            ):
                _fail("MULTI_AUTHORITY_ACTIVE_STATUS_DRIFT")
            effective_namespace = _MULTI_NAMESPACE
            effective_sha = multi[
                "multi_boundary_authority_record_sha256"
            ]
            effective_cardinality = 2
            reason = _MULTI_REASON
        else:
            if multi is not None:
                _fail("UNEXPECTED_MULTI_AUTHORITY_ON_LEGACY_SAMPLE")
            if (
                legacy["authority_status"] != "active"
                or legacy["sample_quarantined"] is not False
                or legacy[
                    "exact_one_attachment_boundary_authority_available"
                ] is not True
            ):
                _fail("LEGACY_V1_ACTIVE_STATUS_DRIFT")
            effective_namespace = _LEGACY_NAMESPACE
            effective_sha = legacy["authority_record_sha256"]
            effective_cardinality = 1
            reason = _LEGACY_REASON

        record: dict[str, Any] = {
            "sample_index_row_id": sample,
            "legacy_v1_authority_record_sha256":
                legacy["authority_record_sha256"],
            "legacy_v1_authority_status": legacy["authority_status"],
            "legacy_v1_sample_quarantined":
                legacy["sample_quarantined"],
            "multi_boundary_authority_record_sha256":
                (
                    multi["multi_boundary_authority_record_sha256"]
                    if multi is not None
                    else ""
                ),
            "multi_boundary_authority_status":
                multi["authority_status"] if multi is not None else "",
            "effective_authority_namespace": effective_namespace,
            "effective_authority_record_sha256": effective_sha,
            "effective_boundary_cardinality": effective_cardinality,
            "precedence_reason": reason,
            "source_authorities_unchanged": True,
            "unified_precedence_resolution_record_sha256": "",
        }
        if tuple(record) != _RESOLUTION_FIELDS:
            _fail("RESOLUTION_EXACT12_INVALID")
        record[
            "unified_precedence_resolution_record_sha256"
        ] = _record_sha256(
            record,
            _RESOLUTION_FIELDS,
            "unified_precedence_resolution_record_sha256",
        )
        records.append(record)

    selected_counts = {
        namespace: sum(
            record["effective_authority_namespace"] == namespace
            for record in records
        )
        for namespace in (_LEGACY_NAMESPACE, _MULTI_NAMESPACE)
    }
    if (
        len(records) != 11
        or selected_counts[_LEGACY_NAMESPACE] != 6
        or selected_counts[_MULTI_NAMESPACE] != 5
        or any(
            type(record["effective_boundary_cardinality"]) is not int
            or record["effective_boundary_cardinality"] not in (1, 2)
            or _SHA256.fullmatch(
                record[
                    "unified_precedence_resolution_record_sha256"
                ]
            ) is None
            for record in records
        )
    ):
        _fail("EFFECTIVE_AUTHORITY_SELECTION_INVALID")
    return tuple(records)


def _reference_design_covapie_current11_unified_authority_precedence_v1(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic in-memory materialization precondition report."""

    byte_inputs = (
        source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle,
        source_multi_boundary_ingestion_execution_bundle,
    )
    if any(type(value) is not bytes for value in byte_inputs):
        _fail("INPUT_MUST_BE_EXACT_BYTES")
    if type(repo_root) is not type(Path()):
        _fail("REPO_ROOT_MUST_BE_EXACT_PATH")
    input_snapshots = tuple(bytes(value) for value in byte_inputs)

    legacy_execution = _validate_legacy_execution(
        source_v1_submission_bundle=source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle=
            source_v1_ingestion_execution_bundle,
        repo_root=repo_root,
    )
    multi_execution_bundle = _validate_multi_execution(
        source_multi_boundary_ingestion_execution_bundle=
            source_multi_boundary_ingestion_execution_bundle,
        source_v1_submission_bundle=source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle=
            source_v1_ingestion_execution_bundle,
        legacy_execution=legacy_execution,
    )
    source_authority_snapshots = (
        copy.deepcopy(legacy_execution["new_authority_records"]),
        copy.deepcopy(multi_execution_bundle["new_authority_records"]),
    )
    resolution_records = _build_resolution_records(
        legacy_execution=legacy_execution,
        multi_execution_bundle=multi_execution_bundle,
    )
    if (
        input_snapshots != tuple(bytes(value) for value in byte_inputs)
        or source_authority_snapshots != (
            legacy_execution["new_authority_records"],
            multi_execution_bundle["new_authority_records"],
        )
    ):
        _fail("SOURCE_MUTATION_DETECTED")

    response: dict[str, Any] = {
        "unified_authority_precedence_design_version": _DESIGN_VERSION,
        "source_v1_ingestion_execution_bundle_filesystem_sha256":
            _sha256(source_v1_ingestion_execution_bundle),
        "source_v1_ingestion_execution_bundle_sha256":
            legacy_execution["ingestion_execution_bundle_sha256"],
        "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256":
            _sha256(source_multi_boundary_ingestion_execution_bundle),
        "source_multi_boundary_ingestion_execution_bundle_sha256":
            multi_execution_bundle[
                "multi_boundary_ingestion_execution_bundle_sha256"
            ],
        "resolution_records": resolution_records,
        "effective_legacy_exact_one_count": 6,
        "effective_multi_boundary_exact_two_count": 5,
        "ready_for_authority_and_unified_view_implementation": True,
        "unified_authority_precedence_design_response_sha256": "",
    }
    if tuple(response) != _RESPONSE_FIELDS:
        _fail("DESIGN_RESPONSE_EXACT10_INVALID")
    response[
        "unified_authority_precedence_design_response_sha256"
    ] = _record_sha256(
        response,
        _RESPONSE_FIELDS,
        "unified_authority_precedence_design_response_sha256",
    )
    return response
