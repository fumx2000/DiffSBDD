"""Build a durable Current11 human-review ingestion execution bundle."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_design_v1
    as adapter_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as submission_adapter,
)


__all__ = (
    "build_covapie_current11_real_human_review_ingestion_execution_bundle_v1",
)


_BUNDLE_VERSION = (
    "covapie_current11_real_human_review_ingestion_execution_bundle_v1"
)
_BUNDLE_FIELDS = (
    "ingestion_execution_bundle_version",
    "source_submission_bundle_sha256",
    "source_canonical_bundle_sha256",
    "submission_batch_id",
    "submission_adapter_response_sha256",
    "ingestion_interface_response_version",
    "authority_context_record_sha256",
    "batch_passed",
    "ingestion_result_records",
    "new_authority_records",
    "ingestion_interface_response_sha256",
    "ingestion_execution_bundle_sha256",
)
_EXPECTED_SAMPLE_ORDER = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_ACTIVE_SAMPLES = frozenset(
    (*_EXPECTED_SAMPLE_ORDER[:5], _EXPECTED_SAMPLE_ORDER[10])
)
_QUARANTINED_SAMPLES = frozenset(_EXPECTED_SAMPLE_ORDER[5:10])
_SAMPLE_000011 = "CYS_SG_SAMPLE_INDEX_000011"
_SAMPLE_000011_ATOMS = ["C2", "C4", "C5", "C6", "F5", "N1", "N3", "O2", "O4"]
_AUTHORITY_REVIEW_DIRECT_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_assignment_record_sha256",
    "source_proposal_record_sha256",
    "source_candidate_set_sha256",
    "review_decision",
    "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order",
    "reviewed_boundary_bond_id",
    "reviewer_id",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_MAX_BUNDLE_BYTES = 1024 * 1024


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
        raise ValueError("EXECUTION_BUNDLE_CANONICAL_JSON_INVALID") from error


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
        raise ValueError("EXECUTION_BUNDLE_JSON_INVALID") from error


def _meaningful(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and "\x00" not in value
    )


def _record_hash(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    return _sha256(_canonical_json_bytes({
        field: record[field] for field in fields if field != digest_field
    }))


def _validate_adapter_response(
    response: object,
    *,
    source_submission_bundle: bytes,
) -> tuple[tuple[dict[str, Any], dict[str, Any]], ...]:
    if (
        type(response) is not dict
        or tuple(response) != tuple(adapter_design.ADAPTER_RESPONSE_FIELDS)
    ):
        raise ValueError("SUBMISSION_ADAPTER_RESPONSE_INVALID")
    exact_types = (
        type(response["submission_adapter_response_version"]) is str,
        type(response["source_payload_sha256"]) is str,
        type(response["canonical_bundle_sha256"]) is str,
        type(response["submission_batch_id"]) is str,
        type(response["adapter_passed"]) is bool,
        type(response["reason"]) is str,
        type(response["adapter_result_records"]) is tuple,
        type(response["adapted_submissions"]) is tuple,
        type(response["submission_adapter_response_sha256"]) is str,
    )
    if not all(exact_types):
        raise ValueError("SUBMISSION_ADAPTER_RESPONSE_INVALID")
    if response["adapter_passed"] is not True:
        raise ValueError("SUBMISSION_ADAPTER_REJECTED")
    try:
        parsed_source = json.loads(source_submission_bundle)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("SUBMISSION_ADAPTER_SOURCE_INVALID") from error
    if (
        response["submission_adapter_response_version"]
        != adapter_design.SUBMISSION_ADAPTER_RESPONSE_VERSION
        or response["reason"] != "PASSED"
        or not _meaningful(response["submission_batch_id"])
        or response["source_payload_sha256"]
        != _sha256(source_submission_bundle)
        or response["canonical_bundle_sha256"]
        != _sha256(_canonical_json_bytes(parsed_source))
        or _SHA256.fullmatch(response["canonical_bundle_sha256"]) is None
        or _SHA256.fullmatch(
            response["submission_adapter_response_sha256"]
        ) is None
    ):
        raise ValueError("SUBMISSION_ADAPTER_REJECTED")
    expected_response_sha = _record_hash(
        response,
        adapter_design.ADAPTER_RESPONSE_FIELDS,
        "submission_adapter_response_sha256",
    )
    if response["submission_adapter_response_sha256"] != expected_response_sha:
        raise ValueError("SUBMISSION_ADAPTER_RESPONSE_SHA_MISMATCH")

    results = response["adapter_result_records"]
    submissions = response["adapted_submissions"]
    if not submissions or len(results) != len(submissions):
        raise ValueError("SUBMISSION_ADAPTER_COUNT_MISMATCH")
    validated_submissions: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for position, (result, submission) in enumerate(zip(results, submissions)):
        if (
            type(result) is not dict
            or tuple(result) != tuple(adapter_design.ADAPTER_RESULT_FIELDS)
            or type(submission) is not tuple
            or len(submission) != 2
            or type(submission[0]) is not dict
            or type(submission[1]) is not dict
        ):
            raise ValueError("SUBMISSION_ADAPTER_RECORD_INVALID")
        review, envelope = submission
        if (
            result["submission_adapter_result_version"]
            != adapter_design.SUBMISSION_ADAPTER_RESULT_VERSION
            or type(result["item_index_0based"]) is not int
            or result["item_index_0based"] != position
            or result["outcome"] != "adapted"
            or result["passed"] is not True
            or result["reason"] != "PASSED"
            or result["consumed_submission_item"] is not True
            or result["ready_for_interface_evaluation"] is not True
            or result["submission_batch_id"] != response["submission_batch_id"]
            or result["sample_index_row_id"] != review.get("sample_index_row_id")
            or result["review_record_sha256"]
            != review.get("review_record_sha256")
            or result["ingestion_envelope_sha256"]
            != envelope.get("ingestion_envelope_sha256")
            or envelope.get("submission_batch_id")
            != response["submission_batch_id"]
            or envelope.get("sample_index_row_id")
            != review.get("sample_index_row_id")
            or envelope.get("review_record_sha256")
            != review.get("review_record_sha256")
            or _SHA256.fullmatch(
                result.get("submission_adapter_result_sha256", "")
            ) is None
            or result["submission_adapter_result_sha256"]
            != _record_hash(
                result,
                adapter_design.ADAPTER_RESULT_FIELDS,
                "submission_adapter_result_sha256",
            )
        ):
            raise ValueError("SUBMISSION_ADAPTER_LINKAGE_INVALID")
        try:
            if (
                tuple(review) != tuple(ingestion_design.REVIEW_RECORD_FIELDS)
                or review["review_record_sha256"]
                != ingestion_design.review_record_sha256(review)
            ):
                raise ValueError("review record invalid")
            ingestion_design.validate_ingestion_envelope(
                envelope,
                review_record=review,
                valid_sample_ids=(review["sample_index_row_id"],),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("SUBMISSION_ADAPTER_LINKAGE_INVALID") from error
        validated_submissions.append((review, envelope))
    return tuple(validated_submissions)


def _validate_current11_execution_semantics(
    response: Mapping[str, Any],
    *,
    submissions: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> None:
    results = response["ingestion_result_records"]
    authorities = response["new_authority_records"]
    if (
        response["batch_passed"] is not True
        or len(submissions) != 11
        or len(results) != 11
        or len(authorities) != 11
    ):
        raise ValueError("CURRENT11_INGESTION_BATCH_INVALID")
    submission_samples = tuple(review["sample_index_row_id"] for review, _ in submissions)
    result_samples = tuple(record["sample_index_row_id"] for record in results)
    authority_samples = tuple(
        record["sample_index_row_id"] for record in authorities
    )
    if (
        submission_samples != _EXPECTED_SAMPLE_ORDER
        or result_samples != _EXPECTED_SAMPLE_ORDER
        or authority_samples != _EXPECTED_SAMPLE_ORDER
    ):
        raise ValueError("CURRENT11_SAMPLE_ORDER_INVALID")

    authority_shas: set[str] = set()
    for position, (submission, result, authority) in enumerate(
        zip(submissions, results, authorities)
    ):
        review, envelope = submission
        try:
            ingestion_design.validate_ingestion_result(result)
            ingestion_design.validate_authority_record(authority)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("CURRENT11_INGESTION_RECORD_INVALID") from error
        sample = review["sample_index_row_id"]
        expected_decision = (
            "select_admitted_candidate"
            if sample in _ACTIVE_SAMPLES
            else "quarantine"
            if sample in _QUARANTINED_SAMPLES
            else None
        )
        if (
            expected_decision is None
            or review["review_decision"] != expected_decision
            or result["review_decision"] != expected_decision
            or authority["review_decision"] != expected_decision
        ):
            raise ValueError("CURRENT11_REVIEW_DECISION_PROFILE_INVALID")
        if (
            tuple(result) != tuple(ingestion_design.INGESTION_RESULT_FIELDS)
            or tuple(authority) != tuple(ingestion_design.AUTHORITY_RECORD_FIELDS)
            or result["submission_batch_id"]
            != envelope["submission_batch_id"]
            or result["sample_index_row_id"] != review["sample_index_row_id"]
            or result["review_record_sha256"] != review["review_record_sha256"]
            or result["ingestion_envelope_sha256"]
            != envelope["ingestion_envelope_sha256"]
            or result["review_decision"] != review["review_decision"]
            or result["outcome"] != "passed"
            or result["passed"] is not True
            or result["blocks_batch"] is not False
            or result["reason"] != "PASSED"
            or result["review_completed"] is not True
            or result["idempotent_replay"] is not False
            or result["conflicting_existing_authority"] is not False
            or result["consumed_review_record"] is not True
            or result["consumed_ingestion_envelope"] is not True
            or authority["sample_index_row_id"] != result["sample_index_row_id"]
            or authority["source_review_record_sha256"]
            != result["review_record_sha256"]
            or authority["source_ingestion_envelope_sha256"]
            != result["ingestion_envelope_sha256"]
            or authority["review_decision"] != result["review_decision"]
            or authority["authority_disposition"]
            != result["authority_disposition"]
            or authority["authority_record_sha256"]
            != result["authority_record_sha256"]
            or authority["authority_record_sha256"] in authority_shas
        ):
            raise ValueError(
                f"CURRENT11_RESULT_AUTHORITY_LINKAGE_INVALID:{position}"
            )
        authority_shas.add(authority["authority_record_sha256"])

        if (
            any(
                authority[field] != review[field]
                for field in _AUTHORITY_REVIEW_DIRECT_FIELDS
            )
            or authority["source_review_record_sha256"]
            != review["review_record_sha256"]
            or authority["source_ingestion_envelope_sha256"]
            != envelope["ingestion_envelope_sha256"]
            or authority["review_rationale_sha256"]
            != _sha256(review["review_rationale"].encode("utf-8"))
            or authority["supersedes_authority_record_sha256"] != ""
        ):
            raise ValueError(
                f"CURRENT11_AUTHORITY_REVIEW_LINKAGE_INVALID:{position}"
            )

        sample = authority["sample_index_row_id"]
        if sample in _ACTIVE_SAMPLES:
            expected_effect = (
                "reviewed_authority_materialized",
                "active",
                True,
                True,
                False,
            )
            observed_effect = (
                authority["authority_disposition"],
                authority["authority_status"],
                authority["complete_warhead_atom_set_authority_available"],
                authority["exact_one_attachment_boundary_authority_available"],
                authority["sample_quarantined"],
            )
            boundary_complete = (
                bool(authority["reviewed_warhead_atom_ids"])
                and _meaningful(
                    authority["reviewed_warhead_attachment_atom_id"]
                )
                and _meaningful(
                    authority["reviewed_nonwarhead_boundary_atom_id"]
                )
                and _meaningful(
                    authority["reviewed_attachment_boundary_bond_order"]
                )
                and _meaningful(authority["reviewed_boundary_bond_id"])
            )
            if observed_effect != expected_effect or not boundary_complete:
                raise ValueError("CURRENT11_ACTIVE_AUTHORITY_INVALID")
        elif sample in _QUARANTINED_SAMPLES:
            expected_effect = (
                "reviewed_quarantine_no_authority",
                "quarantined",
                False,
                False,
                True,
            )
            observed_effect = (
                authority["authority_disposition"],
                authority["authority_status"],
                authority["complete_warhead_atom_set_authority_available"],
                authority["exact_one_attachment_boundary_authority_available"],
                authority["sample_quarantined"],
            )
            boundary_blank = (
                authority["reviewed_warhead_atom_ids"] == []
                and authority["reviewed_warhead_attachment_atom_id"] == ""
                and authority["reviewed_nonwarhead_boundary_atom_id"] == ""
                and authority["reviewed_attachment_boundary_bond_order"] == ""
                and authority["reviewed_boundary_bond_id"] == ""
            )
            review_boundary_blank = (
                review["reviewed_warhead_atom_ids"] == []
                and review["reviewed_warhead_attachment_atom_id"] == ""
                and review["reviewed_nonwarhead_boundary_atom_id"] == ""
                and review["reviewed_attachment_boundary_bond_order"] == ""
                and review["reviewed_boundary_bond_id"] == ""
            )
            if (
                observed_effect != expected_effect
                or not boundary_blank
                or not review_boundary_blank
            ):
                raise ValueError("CURRENT11_QUARANTINE_AUTHORITY_INVALID")
        else:
            raise ValueError("CURRENT11_AUTHORITY_SAMPLE_INVALID")

    authority_000011 = authorities[-1]
    if (
        authority_000011["sample_index_row_id"] != _SAMPLE_000011
        or authority_000011["review_decision"] != "select_admitted_candidate"
        or authority_000011["reviewed_warhead_atom_ids"]
        != _SAMPLE_000011_ATOMS
        or authority_000011["reviewed_warhead_attachment_atom_id"] != "N1"
        or authority_000011["reviewed_nonwarhead_boundary_atom_id"] != "C1'"
        or authority_000011["reviewed_attachment_boundary_bond_order"]
        != "single"
        or authority_000011["reviewed_boundary_bond_id"] != "C1'|N1|single"
        or authority_000011["authority_status"] != "active"
        or authority_000011["sample_quarantined"] is not False
    ):
        raise ValueError("CURRENT11_SAMPLE_000011_AUTHORITY_DRIFT")


def _build_execution_bundle(
    adapter_response: Mapping[str, Any],
    interface_response: Mapping[str, Any],
) -> bytes:
    bundle: dict[str, Any] = {
        "ingestion_execution_bundle_version": _BUNDLE_VERSION,
        "source_submission_bundle_sha256":
            adapter_response["source_payload_sha256"],
        "source_canonical_bundle_sha256":
            adapter_response["canonical_bundle_sha256"],
        "submission_batch_id": adapter_response["submission_batch_id"],
        "submission_adapter_response_sha256":
            adapter_response["submission_adapter_response_sha256"],
        "ingestion_interface_response_version":
            interface_response["interface_response_version"],
        "authority_context_record_sha256":
            interface_response["authority_context_record_sha256"],
        "batch_passed": interface_response["batch_passed"],
        "ingestion_result_records": [
            {field: record[field] for field in ingestion_design.INGESTION_RESULT_FIELDS}
            for record in interface_response["ingestion_result_records"]
        ],
        "new_authority_records": [
            {field: record[field] for field in ingestion_design.AUTHORITY_RECORD_FIELDS}
            for record in interface_response["new_authority_records"]
        ],
        "ingestion_interface_response_sha256":
            interface_response["interface_response_sha256"],
        "ingestion_execution_bundle_sha256": "",
    }
    if tuple(bundle) != _BUNDLE_FIELDS:
        raise AssertionError("execution bundle field order drifted")
    bundle["ingestion_execution_bundle_sha256"] = _sha256(
        _canonical_json_bytes({
            field: bundle[field]
            for field in _BUNDLE_FIELDS
            if field != "ingestion_execution_bundle_sha256"
        })
    )
    payload = _ordered_json_bytes(bundle)
    if (
        not payload
        or len(payload) >= _MAX_BUNDLE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\n" in payload
        or _SHA256.fullmatch(
            bundle["ingestion_execution_bundle_sha256"]
        ) is None
    ):
        raise ValueError("EXECUTION_BUNDLE_BYTE_CONTRACT_INVALID")
    try:
        decoded = json.loads(payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("EXECUTION_BUNDLE_ROUND_TRIP_INVALID") from error
    if (
        type(decoded) is not dict
        or tuple(decoded) != _BUNDLE_FIELDS
        or decoded != bundle
    ):
        raise ValueError("EXECUTION_BUNDLE_ROUND_TRIP_INVALID")
    return payload


def build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
    *,
    source_submission_bundle: bytes,
    repo_root: Path,
) -> bytes:
    """Execute first-ingestion semantics and return deterministic Exact12 JSON."""

    if type(source_submission_bundle) is not bytes:
        raise ValueError("source_submission_bundle must be exact bytes")
    if not isinstance(repo_root, Path):
        raise ValueError("repo_root must be an exact Path")
    source_snapshot = bytes(source_submission_bundle)

    adapter_response = (
        submission_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=source_submission_bundle,
        )
    )
    submissions = _validate_adapter_response(
        adapter_response,
        source_submission_bundle=source_submission_bundle,
    )
    authority_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            repo_root
        )
    )
    interface_response = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1(
            submissions=adapter_response["adapted_submissions"],
            authority_context=authority_context,
            existing_authorities=(),
        )
    )
    ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
        interface_response,
        submissions=adapter_response["adapted_submissions"],
        authority_context=authority_context,
        existing_authorities=(),
    )
    _validate_current11_execution_semantics(
        interface_response,
        submissions=submissions,
    )
    payload = _build_execution_bundle(adapter_response, interface_response)
    if source_submission_bundle != source_snapshot:
        raise ValueError("source submission bundle mutation detected")
    return payload
