"""Build the Current11 multi-boundary authority bundle in memory."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_authority_materialization_and_unified_precedence_design_v1
    as precedence_design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as multi_design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
    as multi_execution,
)


AUTHORITY_BUNDLE_VERSION = (
    "covapie_current11_multi_boundary_authority_bundle_v1"
)
AUTHORITY_NAMESPACE = "exact_two_boundaries_multi_boundary_v1"
PRECEDENCE_DESIGN_COMMIT = "00c2471ca4fc855985989aea7f948ebbfa1b06f4"
PRECEDENCE_DESIGN_PRODUCTION_SHA256 = (
    "17ebcc1c9ca796fb6c7cdf8af0cccc0a96a6ba419760eccb6d4f85fb163e522c"
)
EXACT16_FIELDS = (
    "multi_boundary_authority_bundle_version",
    "authority_namespace",
    "source_v1_ingestion_execution_bundle_filesystem_sha256",
    "source_v1_ingestion_execution_bundle_sha256",
    "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256",
    "source_multi_boundary_ingestion_execution_bundle_sha256",
    "source_unified_precedence_design_version",
    "source_unified_precedence_design_response_sha256",
    "selected_resolution_record_sha256s",
    "sample_order",
    "authority_records",
    "authority_record_count",
    "active_authority_count",
    "exact_two_boundary_authority_count",
    "v1_quarantine_backlink_count",
    "multi_boundary_authority_bundle_sha256",
)

__all__ = (
    "build_covapie_current11_multi_boundary_authority_bundle_v1",
)


_ERROR = "CURRENT11_MULTI_BOUNDARY_AUTHORITY_BUNDLE_INVALID"
_MAX_BUNDLE_BYTES = 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
_PRECEDENCE_REASON = (
    "ACTIVE_EXACT_TWO_SELECTED_OVER_QUARANTINED_EXACT_ONE_FOR_EFFECTIVE_VIEW"
)


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
        raise ValueError(_ERROR) from error


def _ordered_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
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
        raise ValueError(_ERROR) from error


def _record_sha256(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    return _sha256(_canonical_json_bytes({
        field: record[field] for field in fields if field != digest_field
    }))


def _validate_precedence_response(
    response: object,
    *,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
) -> tuple[dict[str, Any], ...]:
    if (
        type(response) is not dict
        or tuple(response) != precedence_design._RESPONSE_FIELDS
        or response["unified_authority_precedence_design_version"]
        != precedence_design._DESIGN_VERSION
        or response[
            "source_v1_ingestion_execution_bundle_filesystem_sha256"
        ] != _sha256(source_v1_ingestion_execution_bundle)
        or response[
            "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
        ] != _sha256(source_multi_boundary_ingestion_execution_bundle)
        or response["effective_legacy_exact_one_count"] != 6
        or response["effective_multi_boundary_exact_two_count"] != 5
        or response[
            "ready_for_authority_and_unified_view_implementation"
        ] is not True
        or type(response["resolution_records"]) is not tuple
        or len(response["resolution_records"]) != 11
        or response[
            "unified_authority_precedence_design_response_sha256"
        ] != _record_sha256(
            response,
            precedence_design._RESPONSE_FIELDS,
            "unified_authority_precedence_design_response_sha256",
        )
    ):
        raise ValueError(_ERROR)

    records = response["resolution_records"]
    if tuple(
        record.get("sample_index_row_id")
        if type(record) is dict else None
        for record in records
    ) != precedence_design._EXPECTED_SAMPLES:
        raise ValueError(_ERROR)
    for record in records:
        if (
            type(record) is not dict
            or tuple(record) != precedence_design._RESOLUTION_FIELDS
            or record["source_authorities_unchanged"] is not True
            or record[
                "unified_precedence_resolution_record_sha256"
            ] != _record_sha256(
                record,
                precedence_design._RESOLUTION_FIELDS,
                "unified_precedence_resolution_record_sha256",
            )
        ):
            raise ValueError(_ERROR)

    selected = tuple(
        record for record in records
        if record["effective_authority_namespace"] == AUTHORITY_NAMESPACE
    )
    if (
        len(selected) != 5
        or tuple(record["sample_index_row_id"] for record in selected)
        != _EXPECTED_SAMPLES
        or any(
            record["effective_boundary_cardinality"] != 2
            or record["precedence_reason"] != _PRECEDENCE_REASON
            or record["multi_boundary_authority_status"] != "active"
            or _SHA256.fullmatch(
                record["multi_boundary_authority_record_sha256"]
            ) is None
            or record["effective_authority_record_sha256"]
            != record["multi_boundary_authority_record_sha256"]
            for record in selected
        )
        or len({
            record["unified_precedence_resolution_record_sha256"]
            for record in selected
        }) != 5
    ):
        raise ValueError(_ERROR)
    return selected


def _validate_multi_execution(
    payload: bytes,
    *,
    design_response: Mapping[str, Any],
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    _, execution = multi_design._strict_json_object(payload)
    if (
        tuple(execution) != multi_execution.EXACT16_FIELDS
        or execution[
            "multi_boundary_ingestion_execution_bundle_version"
        ] != multi_execution.EXECUTION_BUNDLE_VERSION
        or execution[
            "multi_boundary_ingestion_execution_bundle_sha256"
        ] != _record_sha256(
            execution,
            multi_execution.EXACT16_FIELDS,
            "multi_boundary_ingestion_execution_bundle_sha256",
        )
        or execution[
            "multi_boundary_ingestion_execution_bundle_sha256"
        ] != design_response[
            "source_multi_boundary_ingestion_execution_bundle_sha256"
        ]
        or type(execution["new_authority_records"]) is not list
        or len(execution["new_authority_records"]) != 5
    ):
        raise ValueError(_ERROR)

    authorities = execution["new_authority_records"]
    source_snapshot = copy.deepcopy(authorities)
    for authority in authorities:
        multi_design._validate_authority_record(authority)
    if (
        tuple(authority["sample_index_row_id"] for authority in authorities)
        != _EXPECTED_SAMPLES
        or source_snapshot != authorities
    ):
        raise ValueError(_ERROR)
    return execution, tuple(authorities)


def _validate_linkage_and_profile(
    selected_resolutions: Sequence[Mapping[str, Any]],
    authorities: Sequence[Mapping[str, Any]],
) -> None:
    authority_shas: set[str] = set()
    decisions: list[str] = []
    for resolution, authority in zip(selected_resolutions, authorities):
        authority_sha = authority["multi_boundary_authority_record_sha256"]
        if (
            resolution["sample_index_row_id"]
            != authority["sample_index_row_id"]
            or resolution["effective_authority_namespace"]
            != AUTHORITY_NAMESPACE
            or resolution["multi_boundary_authority_record_sha256"]
            != authority_sha
            or resolution["effective_authority_record_sha256"]
            != authority_sha
            or resolution["multi_boundary_authority_status"]
            != authority["authority_status"]
            or authority["authority_status"] != "active"
            or resolution["effective_boundary_cardinality"] != 2
            or authority_sha in authority_shas
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
        authority_shas.add(authority_sha)
        decisions.append(authority["review_decision"])
    if (
        len(authorities) != 5
        or len(selected_resolutions) != 5
        or decisions.count("accept_verified_two_boundary_proposal") != 4
        or decisions.count(
            "revise_two_boundary_atom_set_and_boundaries"
        ) != 1
        or decisions.count("quarantine") != 0
    ):
        raise ValueError(_ERROR)


def _build_bundle(
    *,
    design_response: Mapping[str, Any],
    selected_resolutions: Sequence[Mapping[str, Any]],
    authorities: Sequence[Mapping[str, Any]],
) -> bytes:
    authority_copies = tuple(
        copy.deepcopy({
            field: authority[field]
            for field in multi_design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        })
        for authority in authorities
    )
    bundle: dict[str, Any] = {
        "multi_boundary_authority_bundle_version":
            AUTHORITY_BUNDLE_VERSION,
        "authority_namespace": AUTHORITY_NAMESPACE,
        "source_v1_ingestion_execution_bundle_filesystem_sha256":
            design_response[
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_v1_ingestion_execution_bundle_sha256":
            design_response["source_v1_ingestion_execution_bundle_sha256"],
        "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256":
            design_response[
                "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_multi_boundary_ingestion_execution_bundle_sha256":
            design_response[
                "source_multi_boundary_ingestion_execution_bundle_sha256"
            ],
        "source_unified_precedence_design_version":
            design_response[
                "unified_authority_precedence_design_version"
            ],
        "source_unified_precedence_design_response_sha256":
            design_response[
                "unified_authority_precedence_design_response_sha256"
            ],
        "selected_resolution_record_sha256s": tuple(
            record["unified_precedence_resolution_record_sha256"]
            for record in selected_resolutions
        ),
        "sample_order": tuple(
            authority["sample_index_row_id"]
            for authority in authority_copies
        ),
        "authority_records": authority_copies,
        "authority_record_count": len(authority_copies),
        "active_authority_count": sum(
            authority["authority_status"] == "active"
            for authority in authority_copies
        ),
        "exact_two_boundary_authority_count": sum(
            authority[
                "exact_two_attachment_boundaries_authority_available"
            ] is True
            and len(authority["reviewed_boundary_records"]) == 2
            for authority in authority_copies
        ),
        "v1_quarantine_backlink_count": sum(
            authority["v1_quarantine_authority_unchanged"] is True
            and _SHA256.fullmatch(
                authority[
                    "source_v1_quarantine_authority_record_sha256"
                ]
            ) is not None
            and _SHA256.fullmatch(
                authority["source_v1_review_record_sha256"]
            ) is not None
            for authority in authority_copies
        ),
        "multi_boundary_authority_bundle_sha256": "",
    }
    if (
        tuple(bundle) != EXACT16_FIELDS
        or bundle["authority_record_count"] != 5
        or bundle["active_authority_count"] != 5
        or bundle["exact_two_boundary_authority_count"] != 5
        or bundle["v1_quarantine_backlink_count"] != 5
    ):
        raise ValueError(_ERROR)
    bundle["multi_boundary_authority_bundle_sha256"] = _record_sha256(
        bundle,
        EXACT16_FIELDS,
        "multi_boundary_authority_bundle_sha256",
    )
    payload = _ordered_json_bytes(bundle)
    if (
        not payload
        or len(payload) >= _MAX_BUNDLE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\n" in payload
    ):
        raise ValueError(_ERROR)
    _, decoded = multi_design._strict_json_object(payload)
    if (
        tuple(decoded) != EXACT16_FIELDS
        or decoded != json.loads(payload)
        or decoded["multi_boundary_authority_bundle_sha256"]
        != _record_sha256(
            decoded,
            EXACT16_FIELDS,
            "multi_boundary_authority_bundle_sha256",
        )
    ):
        raise ValueError(_ERROR)
    return payload


def build_covapie_current11_multi_boundary_authority_bundle_v1(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> bytes:
    """Return deterministic Current11 exact-two authority JSON bytes."""

    byte_inputs = (
        source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle,
        source_multi_boundary_ingestion_execution_bundle,
    )
    if (
        any(type(value) is not bytes for value in byte_inputs)
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    input_snapshots = tuple(bytes(value) for value in byte_inputs)

    try:
        design_response = (
            precedence_design
            ._reference_design_covapie_current11_unified_authority_precedence_v1(
                source_v1_submission_bundle=source_v1_submission_bundle,
                source_v1_ingestion_execution_bundle=
                    source_v1_ingestion_execution_bundle,
                source_multi_boundary_ingestion_execution_bundle=
                    source_multi_boundary_ingestion_execution_bundle,
                repo_root=repo_root,
            )
        )
        selected_resolutions = _validate_precedence_response(
            design_response,
            source_v1_ingestion_execution_bundle=
                source_v1_ingestion_execution_bundle,
            source_multi_boundary_ingestion_execution_bundle=
                source_multi_boundary_ingestion_execution_bundle,
        )
        execution, authorities = _validate_multi_execution(
            source_multi_boundary_ingestion_execution_bundle,
            design_response=design_response,
        )
        authority_snapshot = copy.deepcopy(
            execution["new_authority_records"]
        )
        _validate_linkage_and_profile(selected_resolutions, authorities)
        payload = _build_bundle(
            design_response=design_response,
            selected_resolutions=selected_resolutions,
            authorities=authorities,
        )
        if (
            input_snapshots != tuple(bytes(value) for value in byte_inputs)
            or authority_snapshot != execution["new_authority_records"]
        ):
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
