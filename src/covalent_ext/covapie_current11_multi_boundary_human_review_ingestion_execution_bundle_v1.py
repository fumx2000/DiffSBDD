"""Build the Current11 multi-boundary ingestion execution bundle in memory."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_interface_v1
    as public_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as predecessor_ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as predecessor_ingestion_interface,
)


EXECUTION_BUNDLE_VERSION = (
    "covapie_current11_multi_boundary_human_review_"
    "ingestion_execution_bundle_v1"
)
PUBLIC_INTERFACE_COMMIT = "653bacfb31e69ccfd37f29dcffd77116c9305370"
PUBLIC_INTERFACE_PRODUCTION_SHA256 = (
    "f17a33e52ede082e5a28f20b8a70e4b3d40ca30b69823b4050b2104a3545b0d5"
)
EXACT16_FIELDS = (
    "multi_boundary_ingestion_execution_bundle_version",
    "source_v1_submission_bundle_sha256",
    "source_v1_ingestion_execution_bundle_filesystem_sha256",
    "source_v1_ingestion_execution_bundle_sha256",
    "source_multi_boundary_submission_bundle_filesystem_sha256",
    "source_multi_boundary_submission_bundle_sha256",
    "source_adapter_response_filesystem_sha256",
    "source_adapter_response_sha256",
    "submission_batch_id",
    "ingestion_interface_response_version",
    "authority_context_record_sha256",
    "batch_passed",
    "ingestion_result_records",
    "new_authority_records",
    "ingestion_interface_response_sha256",
    "multi_boundary_ingestion_execution_bundle_sha256",
)

__all__ = (
    "build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1",
)


_ERROR = "MULTI_BOUNDARY_INGESTION_EXECUTION_RESPONSE_INVALID"
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_MAX_BUNDLE_BYTES = 1024 * 1024


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _ordered_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _record_sha256(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    return _sha256(_canonical_json_bytes({
        field: record[field] for field in fields if field != digest_field
    }))


def _validate_sources(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    multi_boundary_bundle = design._validate_multi_boundary_submission(
        source_multi_boundary_submission_bundle
    )
    adapter_response = design._validate_adapter_response(
        adapter_response_payload,
        source_payload=source_multi_boundary_submission_bundle,
        source_bundle=multi_boundary_bundle,
    )
    single_boundary_context = (
        predecessor_ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            repo_root
        )
    )
    predecessor_ingestion_design.validate_ingestion_authority_context(
        single_boundary_context
    )
    expected_predecessor_authority_context_sha256 = (
        single_boundary_context.context_record[
            "ingestion_authority_context_record_sha256"
        ]
    )
    predecessor_execution = design._decode_v1_execution(
        source_v1_ingestion_execution_bundle,
        source_v1_submission_bundle=source_v1_submission_bundle,
        expected_authority_context_record_sha256=
            expected_predecessor_authority_context_sha256,
    )
    if (
        multi_boundary_bundle["source_submission_bundle_sha256"]
        != _sha256(source_v1_submission_bundle)
        or multi_boundary_bundle[
            "source_ingestion_execution_bundle_filesystem_sha256"
        ] != _sha256(source_v1_ingestion_execution_bundle)
        or multi_boundary_bundle[
            "source_ingestion_execution_bundle_sha256"
        ] != predecessor_execution["ingestion_execution_bundle_sha256"]
    ):
        raise ValueError(_ERROR)
    return multi_boundary_bundle, adapter_response, predecessor_execution


def _validate_embedded_authority_source_lineage(
    *,
    authorities: Sequence[Mapping[str, Any]],
    multi_boundary_bundle: Mapping[str, Any],
    adapter_response: Mapping[str, Any],
    predecessor_execution: Mapping[str, Any],
) -> None:
    expected_multi_boundary_submission_sha256 = (
        multi_boundary_bundle[
            "multi_boundary_submission_bundle_sha256"
        ]
    )
    expected_adapter_response_sha256 = adapter_response[
        "multi_boundary_submission_adapter_response_sha256"
    ]
    v1_authorities_by_sample = design._v1_authorities(
        predecessor_execution
    )
    for authority in authorities:
        v1_predecessor = v1_authorities_by_sample[
            authority["sample_index_row_id"]
        ]
        if (
            authority[
                "source_multi_boundary_submission_bundle_sha256"
            ] != expected_multi_boundary_submission_sha256
            or authority[
                "source_multi_boundary_submission_adapter_response_sha256"
            ] != expected_adapter_response_sha256
            or authority[
                "source_v1_quarantine_authority_record_sha256"
            ] != v1_predecessor["authority_record_sha256"]
            or authority["source_v1_review_record_sha256"]
            != v1_predecessor["source_review_record_sha256"]
        ):
            raise ValueError(_ERROR)


def _validate_fresh_response(
    response: object,
) -> tuple[
    dict[str, Any],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
]:
    if type(response) is not dict:
        raise ValueError(_ERROR)
    design._validate_interface_response(response)
    response_view = {
        field: response[field]
        for field in design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS
    }
    if (
        tuple(response_view)
        != design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS
        or response_view[
            "multi_boundary_ingestion_interface_response_sha256"
        ] != _record_sha256(
            response_view,
            design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
            "multi_boundary_ingestion_interface_response_sha256",
        )
    ):
        raise ValueError(_ERROR)

    results = response["ingestion_result_records"]
    authorities = response["new_authority_records"]
    if (
        response["batch_passed"] is not True
        or len(results) != 5
        or len(authorities) != 5
        or tuple(result["sample_index_row_id"] for result in results)
        != _EXPECTED_SAMPLES
        or tuple(authority["sample_index_row_id"] for authority in authorities)
        != _EXPECTED_SAMPLES
        or _SHA256.fullmatch(response["authority_context_record_sha256"])
        is None
    ):
        raise ValueError(_ERROR)

    batch_ids = tuple(result["submission_batch_id"] for result in results)
    if (
        type(batch_ids[0]) is not str
        or not batch_ids[0]
        or batch_ids != (batch_ids[0],) * 5
    ):
        raise ValueError(_ERROR)

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
    authority_shas: set[str] = set()
    for result, authority in zip(results, authorities):
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
            )
            != expected_result_effect
            or result["sample_index_row_id"]
            != authority["sample_index_row_id"]
            or result["source_multi_boundary_review_record_sha256"]
            != authority["source_multi_boundary_review_record_sha256"]
            or result["source_ingestion_envelope_sha256"]
            != authority["source_ingestion_envelope_sha256"]
            or result["review_decision"] != authority["review_decision"]
            or result["authority_disposition"]
            != authority["authority_disposition"]
            or result["authority_record_sha256"]
            != authority["multi_boundary_authority_record_sha256"]
            or authority["multi_boundary_authority_record_sha256"]
            in authority_shas
            or authority["authority_status"] != "active"
            or authority["sample_quarantined"] is not False
            or authority[
                "complete_warhead_atom_set_authority_available"
            ] is not True
            or authority[
                "exact_two_attachment_boundaries_authority_available"
            ] is not True
            or authority["v1_quarantine_authority_unchanged"] is not True
        ):
            raise ValueError(_ERROR)
        authority_shas.add(
            authority["multi_boundary_authority_record_sha256"]
        )

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
        raise ValueError(_ERROR)
    return response_view, results, authorities


def _build_bundle(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    multi_boundary_bundle: Mapping[str, Any],
    adapter_response: Mapping[str, Any],
    predecessor_execution: Mapping[str, Any],
    response_view: Mapping[str, Any],
    results: Sequence[Mapping[str, Any]],
    authorities: Sequence[Mapping[str, Any]],
) -> bytes:
    bundle: dict[str, Any] = {
        "multi_boundary_ingestion_execution_bundle_version":
            EXECUTION_BUNDLE_VERSION,
        "source_v1_submission_bundle_sha256":
            _sha256(source_v1_submission_bundle),
        "source_v1_ingestion_execution_bundle_filesystem_sha256":
            _sha256(source_v1_ingestion_execution_bundle),
        "source_v1_ingestion_execution_bundle_sha256":
            predecessor_execution["ingestion_execution_bundle_sha256"],
        "source_multi_boundary_submission_bundle_filesystem_sha256":
            _sha256(source_multi_boundary_submission_bundle),
        "source_multi_boundary_submission_bundle_sha256":
            multi_boundary_bundle[
                "multi_boundary_submission_bundle_sha256"
            ],
        "source_adapter_response_filesystem_sha256":
            _sha256(adapter_response_payload),
        "source_adapter_response_sha256":
            adapter_response[
                "multi_boundary_submission_adapter_response_sha256"
            ],
        "submission_batch_id": results[0]["submission_batch_id"],
        "ingestion_interface_response_version":
            response_view[
                "multi_boundary_ingestion_interface_response_version"
            ],
        "authority_context_record_sha256":
            response_view["authority_context_record_sha256"],
        "batch_passed": response_view["batch_passed"],
        "ingestion_result_records": [
            copy.deepcopy({
                field: record[field]
                for field in design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS
            })
            for record in results
        ],
        "new_authority_records": [
            copy.deepcopy({
                field: record[field]
                for field in design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
            })
            for record in authorities
        ],
        "ingestion_interface_response_sha256":
            response_view[
                "multi_boundary_ingestion_interface_response_sha256"
            ],
        "multi_boundary_ingestion_execution_bundle_sha256": "",
    }
    if (
        tuple(bundle) != EXACT16_FIELDS
        or bundle["submission_batch_id"]
        != multi_boundary_bundle["submission_batch_id"]
        or bundle["submission_batch_id"]
        != adapter_response["submission_batch_id"]
    ):
        raise ValueError(_ERROR)
    bundle[
        "multi_boundary_ingestion_execution_bundle_sha256"
    ] = _record_sha256(
        bundle,
        EXACT16_FIELDS,
        "multi_boundary_ingestion_execution_bundle_sha256",
    )
    payload = _ordered_json_bytes(bundle)
    if (
        not payload
        or len(payload) >= _MAX_BUNDLE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\n" in payload
        or _SHA256.fullmatch(
            bundle[
                "multi_boundary_ingestion_execution_bundle_sha256"
            ]
        ) is None
    ):
        raise ValueError(_ERROR)
    _, decoded = design._strict_json_object(payload)
    if tuple(decoded) != EXACT16_FIELDS or decoded != bundle:
        raise ValueError(_ERROR)
    return payload


def build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> bytes:
    """Return deterministic fresh-ingestion Exact16 JSON bytes."""

    byte_inputs = (
        adapter_response_payload,
        source_multi_boundary_submission_bundle,
        source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle,
    )
    if any(type(value) is not bytes for value in byte_inputs):
        raise ValueError(_ERROR)
    if type(repo_root) is not type(Path()):
        raise ValueError(_ERROR)
    snapshots = tuple(bytes(value) for value in byte_inputs)

    try:
        response = (
            public_interface
            .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
                adapter_response_payload=adapter_response_payload,
                source_multi_boundary_submission_bundle=
                    source_multi_boundary_submission_bundle,
                source_v1_submission_bundle=source_v1_submission_bundle,
                source_v1_ingestion_execution_bundle=
                    source_v1_ingestion_execution_bundle,
                repo_root=repo_root,
            )
        )
        if byte_inputs != snapshots:
            raise ValueError(_ERROR)
        response_view, results, authorities = _validate_fresh_response(
            response
        )
        (
            multi_boundary_bundle,
            adapter_response,
            predecessor_execution,
        ) = _validate_sources(
            adapter_response_payload=adapter_response_payload,
            source_multi_boundary_submission_bundle=
                source_multi_boundary_submission_bundle,
            source_v1_submission_bundle=source_v1_submission_bundle,
            source_v1_ingestion_execution_bundle=
                source_v1_ingestion_execution_bundle,
            repo_root=repo_root,
        )
        _validate_embedded_authority_source_lineage(
            authorities=authorities,
            multi_boundary_bundle=multi_boundary_bundle,
            adapter_response=adapter_response,
            predecessor_execution=predecessor_execution,
        )
        payload = _build_bundle(
            adapter_response_payload=adapter_response_payload,
            source_multi_boundary_submission_bundle=
                source_multi_boundary_submission_bundle,
            source_v1_submission_bundle=source_v1_submission_bundle,
            source_v1_ingestion_execution_bundle=
                source_v1_ingestion_execution_bundle,
            multi_boundary_bundle=multi_boundary_bundle,
            adapter_response=adapter_response,
            predecessor_execution=predecessor_execution,
            response_view=response_view,
            results=results,
            authorities=authorities,
        )
        if byte_inputs != snapshots:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
