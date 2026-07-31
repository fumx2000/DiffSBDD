"""Build the Current11 unified effective authority view in memory."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_authority_bundle_v1
    as multi_authority_bundle,
)
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
from covalent_ext import (
    covapie_current11_real_human_review_ingestion_execution_bundle_v1
    as legacy_execution_bundle,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)


UNIFIED_EFFECTIVE_VIEW_VERSION = (
    "covapie_current11_unified_effective_authority_view_v1"
)
EFFECTIVE_RECORD_VERSION = (
    "covapie_current11_unified_effective_authority_record_v1"
)
PRECEDENCE_DESIGN_COMMIT = "00c2471ca4fc855985989aea7f948ebbfa1b06f4"
PRECEDENCE_DESIGN_PRODUCTION_SHA256 = (
    "17ebcc1c9ca796fb6c7cdf8af0cccc0a96a6ba419760eccb6d4f85fb163e522c"
)
MULTI_BOUNDARY_AUTHORITY_BUNDLE_COMMIT = (
    "ddf3852519cac5eb0d0e50ef919c15ca36fc127a"
)
MULTI_BOUNDARY_AUTHORITY_BUNDLE_PRODUCTION_SHA256 = (
    "1c270d4a0402445220f5735ca875c065e6d5051c0317fa3ef96d74e2741d8d90"
)
EXACT10_EFFECTIVE_RECORD_FIELDS = (
    "unified_effective_authority_record_version",
    "sample_index_row_id",
    "effective_authority_namespace",
    "effective_boundary_cardinality",
    "precedence_reason",
    "source_resolution_record_sha256",
    "source_authority_record_sha256",
    "source_authority_record_version",
    "effective_authority_record",
    "unified_effective_authority_record_sha256",
)
EXACT16_VIEW_FIELDS = (
    "unified_effective_authority_view_version",
    "source_v1_submission_bundle_filesystem_sha256",
    "source_v1_ingestion_execution_bundle_filesystem_sha256",
    "source_v1_ingestion_execution_bundle_sha256",
    "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256",
    "source_multi_boundary_ingestion_execution_bundle_sha256",
    "source_multi_boundary_authority_bundle_filesystem_sha256",
    "source_multi_boundary_authority_bundle_sha256",
    "source_unified_precedence_design_version",
    "source_unified_precedence_design_response_sha256",
    "sample_order",
    "effective_authority_records",
    "effective_authority_record_count",
    "effective_legacy_exact_one_count",
    "effective_multi_boundary_exact_two_count",
    "unified_effective_authority_view_sha256",
)

__all__ = (
    "build_covapie_current11_unified_effective_authority_view_v1",
)


_ERROR = "CURRENT11_UNIFIED_EFFECTIVE_AUTHORITY_VIEW_INVALID"
_MAX_VIEW_BYTES = 2 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_MULTI_SAMPLES = _EXPECTED_SAMPLES[5:10]
_LEGACY_SAMPLES = (*_EXPECTED_SAMPLES[:5], _EXPECTED_SAMPLES[10])
_LEGACY_NAMESPACE = "legacy_exact_one_boundary_v1"
_MULTI_NAMESPACE = "exact_two_boundaries_multi_boundary_v1"
_LEGACY_REASON = "ACTIVE_LEGACY_EXACT_ONE_ONLY"
_MULTI_REASON = (
    "ACTIVE_EXACT_TWO_SELECTED_OVER_QUARANTINED_EXACT_ONE_FOR_EFFECTIVE_VIEW"
)


class _DuplicateKeyError(ValueError):
    pass


class _NonfiniteError(ValueError):
    pass


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


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise _NonfiniteError(value)


def _strict_json_object(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= _MAX_VIEW_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError(_ERROR)
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _DuplicateKeyError,
        _NonfiniteError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        raise ValueError(_ERROR)
    return value


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
        or type(response["resolution_records"]) is not tuple
        or len(response["resolution_records"]) != 11
        or response["effective_legacy_exact_one_count"] != 6
        or response["effective_multi_boundary_exact_two_count"] != 5
        or response[
            "ready_for_authority_and_unified_view_implementation"
        ] is not True
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
    ) != _EXPECTED_SAMPLES:
        raise ValueError(_ERROR)
    legacy_count = 0
    multi_count = 0
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
        sample = record["sample_index_row_id"]
        if sample in _LEGACY_SAMPLES:
            expected = (_LEGACY_NAMESPACE, 1, _LEGACY_REASON)
            legacy_count += 1
        elif sample in _MULTI_SAMPLES:
            expected = (_MULTI_NAMESPACE, 2, _MULTI_REASON)
            multi_count += 1
        else:
            raise ValueError(_ERROR)
        observed = (
            record["effective_authority_namespace"],
            record["effective_boundary_cardinality"],
            record["precedence_reason"],
        )
        if (
            observed != expected
            or _SHA256.fullmatch(
                record["effective_authority_record_sha256"]
            ) is None
        ):
            raise ValueError(_ERROR)
    if (legacy_count, multi_count) != (6, 5):
        raise ValueError(_ERROR)
    return records


def _validated_source_authorities(
    *,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    design_response: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
]:
    legacy_execution = _strict_json_object(
        source_v1_ingestion_execution_bundle
    )
    multi_execution_value = _strict_json_object(
        source_multi_boundary_ingestion_execution_bundle
    )
    if (
        tuple(legacy_execution) != legacy_execution_bundle._BUNDLE_FIELDS
        or legacy_execution["ingestion_execution_bundle_version"]
        != legacy_execution_bundle._BUNDLE_VERSION
        or legacy_execution["ingestion_execution_bundle_sha256"]
        != _record_sha256(
            legacy_execution,
            legacy_execution_bundle._BUNDLE_FIELDS,
            "ingestion_execution_bundle_sha256",
        )
        or legacy_execution["ingestion_execution_bundle_sha256"]
        != design_response["source_v1_ingestion_execution_bundle_sha256"]
        or type(legacy_execution["new_authority_records"]) is not list
        or len(legacy_execution["new_authority_records"]) != 11
        or tuple(multi_execution_value) != multi_execution.EXACT16_FIELDS
        or multi_execution_value[
            "multi_boundary_ingestion_execution_bundle_version"
        ] != multi_execution.EXECUTION_BUNDLE_VERSION
        or multi_execution_value[
            "multi_boundary_ingestion_execution_bundle_sha256"
        ] != _record_sha256(
            multi_execution_value,
            multi_execution.EXACT16_FIELDS,
            "multi_boundary_ingestion_execution_bundle_sha256",
        )
        or multi_execution_value[
            "multi_boundary_ingestion_execution_bundle_sha256"
        ] != design_response[
            "source_multi_boundary_ingestion_execution_bundle_sha256"
        ]
        or type(multi_execution_value["new_authority_records"]) is not list
        or len(multi_execution_value["new_authority_records"]) != 5
    ):
        raise ValueError(_ERROR)

    legacy_authorities = legacy_execution["new_authority_records"]
    multi_authorities = multi_execution_value["new_authority_records"]
    authority_snapshots = (
        copy.deepcopy(legacy_authorities),
        copy.deepcopy(multi_authorities),
    )
    try:
        for authority in legacy_authorities:
            legacy_design.validate_authority_record(authority)
        for authority in multi_authorities:
            multi_design._validate_authority_record(authority)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if (
        tuple(
            authority["sample_index_row_id"]
            for authority in legacy_authorities
        ) != _EXPECTED_SAMPLES
        or tuple(
            authority["sample_index_row_id"]
            for authority in multi_authorities
        ) != _MULTI_SAMPLES
        or authority_snapshots != (legacy_authorities, multi_authorities)
    ):
        raise ValueError(_ERROR)
    return (
        legacy_execution,
        multi_execution_value,
        tuple(legacy_authorities),
        tuple(multi_authorities),
    )


def _validate_authority_bundle(
    payload: bytes,
    *,
    design_response: Mapping[str, Any],
    resolutions: Sequence[Mapping[str, Any]],
    legacy_execution: Mapping[str, Any],
    multi_execution_value: Mapping[str, Any],
    multi_authorities: Sequence[Mapping[str, Any]],
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    bundle = _strict_json_object(payload)
    selected_resolutions = tuple(
        record for record in resolutions
        if record["effective_authority_namespace"] == _MULTI_NAMESPACE
    )
    if (
        tuple(bundle) != multi_authority_bundle.EXACT16_FIELDS
        or bundle["multi_boundary_authority_bundle_version"]
        != multi_authority_bundle.AUTHORITY_BUNDLE_VERSION
        or bundle["authority_namespace"] != _MULTI_NAMESPACE
        or bundle[
            "source_v1_ingestion_execution_bundle_filesystem_sha256"
        ] != _sha256(source_v1_ingestion_execution_bundle)
        or bundle["source_v1_ingestion_execution_bundle_sha256"]
        != legacy_execution["ingestion_execution_bundle_sha256"]
        or bundle[
            "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
        ] != _sha256(source_multi_boundary_ingestion_execution_bundle)
        or bundle["source_multi_boundary_ingestion_execution_bundle_sha256"]
        != multi_execution_value[
            "multi_boundary_ingestion_execution_bundle_sha256"
        ]
        or bundle["source_unified_precedence_design_version"]
        != design_response["unified_authority_precedence_design_version"]
        or bundle["source_unified_precedence_design_response_sha256"]
        != design_response[
            "unified_authority_precedence_design_response_sha256"
        ]
        or bundle["selected_resolution_record_sha256s"] != [
            record["unified_precedence_resolution_record_sha256"]
            for record in selected_resolutions
        ]
        or bundle["sample_order"] != list(_MULTI_SAMPLES)
        or type(bundle["authority_records"]) is not list
        or len(bundle["authority_records"]) != 5
        or bundle["authority_record_count"] != 5
        or bundle["active_authority_count"] != 5
        or bundle["exact_two_boundary_authority_count"] != 5
        or bundle["v1_quarantine_backlink_count"] != 5
        or bundle["multi_boundary_authority_bundle_sha256"]
        != _record_sha256(
            bundle,
            multi_authority_bundle.EXACT16_FIELDS,
            "multi_boundary_authority_bundle_sha256",
        )
    ):
        raise ValueError(_ERROR)
    authority_records = bundle["authority_records"]
    source_snapshot = copy.deepcopy(authority_records)
    try:
        for authority in authority_records:
            multi_design._validate_authority_record(authority)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if (
        tuple(
            authority["sample_index_row_id"]
            for authority in authority_records
        ) != _MULTI_SAMPLES
        or authority_records != list(multi_authorities)
        or source_snapshot != authority_records
    ):
        raise ValueError(_ERROR)
    return bundle, tuple(authority_records)


def _build_effective_records(
    *,
    resolutions: Sequence[Mapping[str, Any]],
    legacy_authorities: Sequence[Mapping[str, Any]],
    multi_authorities: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
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
        raise ValueError(_ERROR)

    effective_records: list[dict[str, Any]] = []
    source_sha256s: set[str] = set()
    for resolution in resolutions:
        sample = resolution["sample_index_row_id"]
        legacy_source = legacy_by_sample[sample]
        if (
            resolution["legacy_v1_authority_record_sha256"]
            != legacy_source["authority_record_sha256"]
            or resolution["legacy_v1_authority_status"]
            != legacy_source["authority_status"]
            or resolution["legacy_v1_sample_quarantined"]
            is not legacy_source["sample_quarantined"]
        ):
            raise ValueError(_ERROR)
        if sample in _LEGACY_SAMPLES:
            authority = legacy_source
            source_sha = authority["authority_record_sha256"]
            source_version = authority["authority_record_version"]
            expected = (_LEGACY_NAMESPACE, 1, _LEGACY_REASON)
            status_valid = (
                authority["authority_status"] == "active"
                and authority["sample_quarantined"] is False
                and authority[
                    "exact_one_attachment_boundary_authority_available"
                ] is True
                and resolution[
                    "multi_boundary_authority_record_sha256"
                ] == ""
                and resolution["multi_boundary_authority_status"] == ""
            )
        elif sample in _MULTI_SAMPLES:
            authority = multi_by_sample[sample]
            source_sha = authority[
                "multi_boundary_authority_record_sha256"
            ]
            source_version = authority[
                "multi_boundary_authority_record_version"
            ]
            expected = (_MULTI_NAMESPACE, 2, _MULTI_REASON)
            status_valid = (
                authority["authority_status"] == "active"
                and authority["sample_quarantined"] is False
                and authority[
                    "exact_two_attachment_boundaries_authority_available"
                ] is True
                and resolution[
                    "multi_boundary_authority_record_sha256"
                ] == source_sha
                and resolution["multi_boundary_authority_status"]
                == authority["authority_status"]
                and legacy_source["authority_status"] == "quarantined"
                and legacy_source["sample_quarantined"] is True
                and legacy_source[
                    "exact_one_attachment_boundary_authority_available"
                ] is False
            )
        else:
            raise ValueError(_ERROR)
        resolution_profile = (
            resolution["effective_authority_namespace"],
            resolution["effective_boundary_cardinality"],
            resolution["precedence_reason"],
        )
        if (
            not status_valid
            or resolution_profile != expected
            or authority["sample_index_row_id"] != sample
            or resolution["effective_authority_record_sha256"] != source_sha
            or _SHA256.fullmatch(source_sha) is None
            or source_sha in source_sha256s
        ):
            raise ValueError(_ERROR)
        source_sha256s.add(source_sha)
        record: dict[str, Any] = {
            "unified_effective_authority_record_version":
                EFFECTIVE_RECORD_VERSION,
            "sample_index_row_id": sample,
            "effective_authority_namespace": expected[0],
            "effective_boundary_cardinality": expected[1],
            "precedence_reason": expected[2],
            "source_resolution_record_sha256": resolution[
                "unified_precedence_resolution_record_sha256"
            ],
            "source_authority_record_sha256": source_sha,
            "source_authority_record_version": source_version,
            "effective_authority_record": copy.deepcopy(authority),
            "unified_effective_authority_record_sha256": "",
        }
        if tuple(record) != EXACT10_EFFECTIVE_RECORD_FIELDS:
            raise ValueError(_ERROR)
        record[
            "unified_effective_authority_record_sha256"
        ] = _record_sha256(
            record,
            EXACT10_EFFECTIVE_RECORD_FIELDS,
            "unified_effective_authority_record_sha256",
        )
        effective_records.append(record)
    if (
        len(effective_records) != 11
        or tuple(
            record["sample_index_row_id"] for record in effective_records
        ) != _EXPECTED_SAMPLES
    ):
        raise ValueError(_ERROR)
    return tuple(effective_records)


def _build_view(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    source_multi_boundary_authority_bundle: bytes,
    legacy_execution: Mapping[str, Any],
    multi_execution_value: Mapping[str, Any],
    authority_bundle: Mapping[str, Any],
    design_response: Mapping[str, Any],
    effective_records: Sequence[Mapping[str, Any]],
) -> bytes:
    record_copies = tuple(copy.deepcopy(record) for record in effective_records)
    view: dict[str, Any] = {
        "unified_effective_authority_view_version":
            UNIFIED_EFFECTIVE_VIEW_VERSION,
        "source_v1_submission_bundle_filesystem_sha256":
            _sha256(source_v1_submission_bundle),
        "source_v1_ingestion_execution_bundle_filesystem_sha256":
            _sha256(source_v1_ingestion_execution_bundle),
        "source_v1_ingestion_execution_bundle_sha256":
            legacy_execution["ingestion_execution_bundle_sha256"],
        "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256":
            _sha256(source_multi_boundary_ingestion_execution_bundle),
        "source_multi_boundary_ingestion_execution_bundle_sha256":
            multi_execution_value[
                "multi_boundary_ingestion_execution_bundle_sha256"
            ],
        "source_multi_boundary_authority_bundle_filesystem_sha256":
            _sha256(source_multi_boundary_authority_bundle),
        "source_multi_boundary_authority_bundle_sha256":
            authority_bundle["multi_boundary_authority_bundle_sha256"],
        "source_unified_precedence_design_version":
            design_response["unified_authority_precedence_design_version"],
        "source_unified_precedence_design_response_sha256":
            design_response[
                "unified_authority_precedence_design_response_sha256"
            ],
        "sample_order": _EXPECTED_SAMPLES,
        "effective_authority_records": record_copies,
        "effective_authority_record_count": len(record_copies),
        "effective_legacy_exact_one_count": sum(
            record["effective_authority_namespace"] == _LEGACY_NAMESPACE
            for record in record_copies
        ),
        "effective_multi_boundary_exact_two_count": sum(
            record["effective_authority_namespace"] == _MULTI_NAMESPACE
            for record in record_copies
        ),
        "unified_effective_authority_view_sha256": "",
    }
    if (
        tuple(view) != EXACT16_VIEW_FIELDS
        or view["effective_authority_record_count"] != 11
        or view["effective_legacy_exact_one_count"] != 6
        or view["effective_multi_boundary_exact_two_count"] != 5
    ):
        raise ValueError(_ERROR)
    view["unified_effective_authority_view_sha256"] = _record_sha256(
        view,
        EXACT16_VIEW_FIELDS,
        "unified_effective_authority_view_sha256",
    )
    payload = _ordered_json_bytes(view)
    if (
        not payload
        or len(payload) >= _MAX_VIEW_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\n" in payload
        or b"\r" in payload
        or payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError(_ERROR)
    decoded = _strict_json_object(payload)
    if (
        tuple(decoded) != EXACT16_VIEW_FIELDS
        or decoded != json.loads(payload)
        or decoded["sample_order"] != list(_EXPECTED_SAMPLES)
        or decoded["unified_effective_authority_view_sha256"]
        != _record_sha256(
            decoded,
            EXACT16_VIEW_FIELDS,
            "unified_effective_authority_view_sha256",
        )
        or any(
            tuple(record) != EXACT10_EFFECTIVE_RECORD_FIELDS
            or record["unified_effective_authority_record_sha256"]
            != _record_sha256(
                record,
                EXACT10_EFFECTIVE_RECORD_FIELDS,
                "unified_effective_authority_record_sha256",
            )
            for record in decoded["effective_authority_records"]
        )
    ):
        raise ValueError(_ERROR)
    return payload


def build_covapie_current11_unified_effective_authority_view_v1(
    *,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    source_multi_boundary_ingestion_execution_bundle: bytes,
    source_multi_boundary_authority_bundle: bytes,
    repo_root: Path,
) -> bytes:
    """Return deterministic Current11 effective authority view JSON bytes."""

    byte_inputs = (
        source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle,
        source_multi_boundary_ingestion_execution_bundle,
        source_multi_boundary_authority_bundle,
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
        resolutions = _validate_precedence_response(
            design_response,
            source_v1_ingestion_execution_bundle=
                source_v1_ingestion_execution_bundle,
            source_multi_boundary_ingestion_execution_bundle=
                source_multi_boundary_ingestion_execution_bundle,
        )
        (
            legacy_execution,
            multi_execution_value,
            legacy_authorities,
            validated_multi_authorities,
        ) = _validated_source_authorities(
            source_v1_ingestion_execution_bundle=
                source_v1_ingestion_execution_bundle,
            source_multi_boundary_ingestion_execution_bundle=
                source_multi_boundary_ingestion_execution_bundle,
            design_response=design_response,
        )
        source_authority_snapshots = (
            copy.deepcopy(legacy_authorities),
            copy.deepcopy(validated_multi_authorities),
        )
        authority_bundle, authority_bundle_records = (
            _validate_authority_bundle(
                source_multi_boundary_authority_bundle,
                design_response=design_response,
                resolutions=resolutions,
                legacy_execution=legacy_execution,
                multi_execution_value=multi_execution_value,
                multi_authorities=validated_multi_authorities,
                source_v1_ingestion_execution_bundle=
                    source_v1_ingestion_execution_bundle,
                source_multi_boundary_ingestion_execution_bundle=
                    source_multi_boundary_ingestion_execution_bundle,
            )
        )
        authority_bundle_snapshot = copy.deepcopy(authority_bundle_records)
        effective_records = _build_effective_records(
            resolutions=resolutions,
            legacy_authorities=legacy_authorities,
            multi_authorities=authority_bundle_records,
        )
        payload = _build_view(
            source_v1_submission_bundle=source_v1_submission_bundle,
            source_v1_ingestion_execution_bundle=
                source_v1_ingestion_execution_bundle,
            source_multi_boundary_ingestion_execution_bundle=
                source_multi_boundary_ingestion_execution_bundle,
            source_multi_boundary_authority_bundle=
                source_multi_boundary_authority_bundle,
            legacy_execution=legacy_execution,
            multi_execution_value=multi_execution_value,
            authority_bundle=authority_bundle,
            design_response=design_response,
            effective_records=effective_records,
        )
        if (
            input_snapshots != tuple(bytes(value) for value in byte_inputs)
            or source_authority_snapshots != (
                legacy_authorities,
                validated_multi_authorities,
            )
            or authority_bundle_snapshot != authority_bundle_records
        ):
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
