"""Validate and adapt a Current11 multi-boundary submission in memory."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


__all__ = (
    "adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1",
)


_MAX_SOURCE_BYTES = 1_048_576
_BUNDLE_VERSION = (
    "covapie_current11_multi_boundary_human_review_submission_bundle_v1"
)
_RESPONSE_VERSION = (
    "covapie_current11_multi_boundary_human_review_submission_"
    "adapter_response_v1"
)
_RESULT_VERSION = (
    "covapie_current11_multi_boundary_human_review_submission_"
    "adapter_result_v1"
)
_ENVELOPE_VERSION = (
    "covapie_current11_multi_boundary_human_review_ingestion_envelope_v1"
)
_TARGET_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
_BUNDLE_FIELDS = (
    "multi_boundary_submission_bundle_version",
    "source_submission_bundle_sha256",
    "source_ingestion_execution_bundle_filesystem_sha256",
    "source_ingestion_execution_bundle_sha256",
    "source_verified_multi_boundary_evidence_csv_sha256",
    "source_multi_boundary_review_worklist_csv_sha256",
    "source_readme_sha256",
    "submission_batch_id",
    "submission_items",
    "multi_boundary_submission_bundle_sha256",
)
_BUNDLE_SOURCE_SHA_FIELDS = _BUNDLE_FIELDS[1:7]
_RECORD_FIELDS = (
    "multi_boundary_review_record_version",
    "item_index_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_evidence_record_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_review_record_sha256",
    "proposed_warhead_atom_ids",
    "proposed_boundary_records",
    "scope_caveat",
    "review_decision",
    "reviewed_warhead_atom_ids",
    "reviewed_boundary_records",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "review_completed",
    "multi_boundary_review_record_sha256",
)
_BOUNDARY_FIELDS = (
    "warhead_attachment_atom_id",
    "nonwarhead_boundary_atom_id",
    "boundary_bond_order",
    "boundary_bond_id",
)
_RESPONSE_FIELDS = (
    "multi_boundary_submission_adapter_response_version",
    "source_payload_sha256",
    "canonical_source_bundle_sha256",
    "submission_batch_id",
    "adapter_passed",
    "reason",
    "adapter_result_records",
    "adapted_submissions",
    "multi_boundary_submission_adapter_response_sha256",
)
_RESULT_FIELDS = (
    "multi_boundary_submission_adapter_result_version",
    "item_index_0based",
    "submission_batch_id",
    "sample_index_row_id",
    "outcome",
    "passed",
    "reason",
    "source_multi_boundary_review_record_sha256",
    "ingestion_envelope_sha256",
    "consumed_submission_item",
    "ready_for_ingestion",
    "multi_boundary_submission_adapter_result_sha256",
)
_ENVELOPE_FIELDS = (
    "multi_boundary_ingestion_envelope_version",
    "submission_batch_id",
    "item_index_0based",
    "sample_index_row_id",
    "source_multi_boundary_submission_bundle_sha256",
    "source_multi_boundary_review_record_sha256",
    "review_record_payload",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "ready_for_ingestion",
    "multi_boundary_ingestion_envelope_sha256",
)
_DECISIONS = frozenset((
    "accept_verified_two_boundary_proposal",
    "revise_two_boundary_atom_set_and_boundaries",
    "quarantine",
))
_NORMALIZED_BOND_ORDERS = frozenset(("aromatic", "double", "single"))
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ITEM_LIST_FIELDS = frozenset((
    "proposed_warhead_atom_ids",
    "proposed_boundary_records",
    "reviewed_warhead_atom_ids",
    "reviewed_boundary_records",
))
_ITEM_BOOL_FIELDS = frozenset((
    "reviewer_provenance_attested",
    "review_completed",
))
_ITEM_SOURCE_SHA_FIELDS = (
    "source_evidence_record_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_review_record_sha256",
)
_ITEM_MEANINGFUL_FIELDS = (
    "multi_boundary_review_record_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    *_ITEM_SOURCE_SHA_FIELDS,
)
_REASONS = frozenset((
    "PASSED",
    "SOURCE_PAYLOAD_EXACT_TYPE_INVALID",
    "SOURCE_PAYLOAD_SIZE_INVALID",
    "SOURCE_PAYLOAD_UTF8_INVALID",
    "SOURCE_PAYLOAD_BOM_FORBIDDEN",
    "SOURCE_PAYLOAD_NUL_FORBIDDEN",
    "SOURCE_PAYLOAD_TRAILING_NEWLINE_FORBIDDEN",
    "SOURCE_PAYLOAD_JSON_INVALID",
    "SOURCE_PAYLOAD_DUPLICATE_KEY",
    "SOURCE_PAYLOAD_NONFINITE_INVALID",
    "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
    "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
    "SUBMISSION_BUNDLE_VERSION_MISMATCH",
    "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
    "SUBMISSION_ITEM_COUNT_INVALID",
    "SUBMISSION_BUNDLE_DIGEST_INVALID",
    "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH",
    "SUBMISSION_ITEM_EXACT_TYPE_INVALID",
    "SUBMISSION_ITEM_ORDER_INVALID",
    "SUBMISSION_SAMPLE_ORDER_INVALID",
    "DUPLICATE_SAMPLE_IN_BUNDLE",
    "REVIEW_RECORD_DIGEST_INVALID",
    "DUPLICATE_REVIEW_DIGEST_IN_BUNDLE",
    "REVIEW_DECISION_INVALID",
    "REVIEW_COMPLETION_INVALID",
    "REVIEWER_PROVENANCE_INVALID",
    "ATOM_SET_INVALID",
    "BOUNDARY_RECORDS_INVALID",
    "ACCEPT_SEMANTICS_INVALID",
    "REVISION_SEMANTICS_INVALID",
    "QUARANTINE_SEMANTICS_INVALID",
    "ADAPTER_RESPONSE_INVARIANT_INVALID",
))


class _ValidationError(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


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
        raise _ValidationError("SUBMISSION_BUNDLE_DIGEST_INVALID") from error


def _digest(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    return _sha256(_canonical_json_bytes({
        field: record[field] for field in fields if field != digest_field
    }))


def _meaningful(value: object) -> bool:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or "\x00" in value
    ):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    try:
        return sorted(values, key=lambda value: value.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise _ValidationError("ATOM_SET_INVALID") from error


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise _NonfiniteError(value)


def _parse_source(source_payload: object) -> tuple[bytes, dict[str, Any]]:
    if type(source_payload) is not bytes:
        raise _ValidationError("SOURCE_PAYLOAD_EXACT_TYPE_INVALID")
    payload: bytes = source_payload
    if not payload or len(payload) >= _MAX_SOURCE_BYTES:
        raise _ValidationError("SOURCE_PAYLOAD_SIZE_INVALID")
    if payload.startswith(b"\xef\xbb\xbf"):
        raise _ValidationError("SOURCE_PAYLOAD_BOM_FORBIDDEN")
    if b"\x00" in payload:
        raise _ValidationError("SOURCE_PAYLOAD_NUL_FORBIDDEN")
    if payload.endswith((b"\n", b"\r")):
        raise _ValidationError("SOURCE_PAYLOAD_TRAILING_NEWLINE_FORBIDDEN")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _ValidationError("SOURCE_PAYLOAD_UTF8_INVALID") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except _DuplicateKeyError as error:
        raise _ValidationError("SOURCE_PAYLOAD_DUPLICATE_KEY") from error
    except _NonfiniteError as error:
        raise _ValidationError("SOURCE_PAYLOAD_NONFINITE_INVALID") from error
    except (
        json.JSONDecodeError,
        ValueError,
        RecursionError,
        OverflowError,
    ) as error:
        raise _ValidationError("SOURCE_PAYLOAD_JSON_INVALID") from error
    if type(value) is not dict:
        raise _ValidationError("SUBMISSION_BUNDLE_EXACT_TYPE_INVALID")
    return payload, value


def _validate_bundle(bundle: dict[str, Any]) -> str:
    if tuple(bundle) != _BUNDLE_FIELDS:
        raise _ValidationError("SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH")
    if (
        any(type(bundle[field]) is not str for field in _BUNDLE_FIELDS[:8])
        or type(bundle["submission_items"]) is not list
        or type(bundle["multi_boundary_submission_bundle_sha256"]) is not str
        or any(
            _SHA256.fullmatch(bundle[field]) is None
            for field in _BUNDLE_SOURCE_SHA_FIELDS
        )
    ):
        raise _ValidationError("SUBMISSION_BUNDLE_EXACT_TYPE_INVALID")
    if bundle["multi_boundary_submission_bundle_version"] != _BUNDLE_VERSION:
        raise _ValidationError("SUBMISSION_BUNDLE_VERSION_MISMATCH")
    if not _meaningful(bundle["submission_batch_id"]):
        raise _ValidationError("SUBMISSION_BATCH_ID_NOT_MEANINGFUL")
    if len(bundle["submission_items"]) != 5:
        raise _ValidationError("SUBMISSION_ITEM_COUNT_INVALID")
    stored = bundle["multi_boundary_submission_bundle_sha256"]
    if (
        _SHA256.fullmatch(stored) is None
        or stored != _digest(
            bundle,
            _BUNDLE_FIELDS,
            "multi_boundary_submission_bundle_sha256",
        )
    ):
        raise _ValidationError("SUBMISSION_BUNDLE_DIGEST_INVALID")
    return stored


def _validate_item_inventories(items: list[Any]) -> list[dict[str, Any]]:
    for item in items:
        if type(item) is not dict or tuple(item) != _RECORD_FIELDS:
            raise _ValidationError(
                "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH"
            )
    return items


def _validate_item_types(items: Sequence[dict[str, Any]]) -> None:
    for item in items:
        if (
            type(item["item_index_0based"]) is not int
            or any(type(item[field]) is not list for field in _ITEM_LIST_FIELDS)
            or any(type(item[field]) is not bool for field in _ITEM_BOOL_FIELDS)
            or any(
                type(item[field]) is not str
                for field in _RECORD_FIELDS
                if field != "item_index_0based"
                and field not in _ITEM_LIST_FIELDS
                and field not in _ITEM_BOOL_FIELDS
            )
            or any(not _meaningful(item[field]) for field in _ITEM_MEANINGFUL_FIELDS)
            or any(
                _SHA256.fullmatch(item[field]) is None
                for field in _ITEM_SOURCE_SHA_FIELDS
            )
            or (
                item["scope_caveat"] != ""
                and not _meaningful(item["scope_caveat"])
            )
        ):
            raise _ValidationError("SUBMISSION_ITEM_EXACT_TYPE_INVALID")


def _validate_item_identity(items: Sequence[dict[str, Any]]) -> None:
    for position, item in enumerate(items):
        if item["item_index_0based"] != position:
            raise _ValidationError("SUBMISSION_ITEM_ORDER_INVALID")
    samples = [item["sample_index_row_id"] for item in items]
    if len(set(samples)) != len(samples):
        raise _ValidationError("DUPLICATE_SAMPLE_IN_BUNDLE")
    if tuple(samples) != _TARGET_SAMPLES:
        raise _ValidationError("SUBMISSION_SAMPLE_ORDER_INVALID")


def _validate_record_digests(items: Sequence[dict[str, Any]]) -> None:
    digests = [
        item["multi_boundary_review_record_sha256"] for item in items
    ]
    if len(set(digests)) != len(digests):
        raise _ValidationError("DUPLICATE_REVIEW_DIGEST_IN_BUNDLE")
    for item in items:
        stored = item["multi_boundary_review_record_sha256"]
        if (
            _SHA256.fullmatch(stored) is None
            or stored != _digest(
                item,
                _RECORD_FIELDS,
                "multi_boundary_review_record_sha256",
            )
        ):
            raise _ValidationError("REVIEW_RECORD_DIGEST_INVALID")


def _validate_completion_and_provenance(
    items: Sequence[dict[str, Any]],
) -> None:
    for item in items:
        if item["review_decision"] not in _DECISIONS:
            raise _ValidationError("REVIEW_DECISION_INVALID")
    for item in items:
        if item["review_completed"] is not True:
            raise _ValidationError("REVIEW_COMPLETION_INVALID")
    for item in items:
        if (
            item["reviewer_provenance_attested"] is not True
            or any(not _meaningful(item[field]) for field in (
                "reviewer_id",
                "review_rationale",
                "review_notes",
                "reviewer_provenance_attestor_id",
                "submission_source_label",
            ))
        ):
            raise _ValidationError("REVIEWER_PROVENANCE_INVALID")


def _validate_atom_list(value: object) -> None:
    if type(value) is not list:
        raise _ValidationError("ATOM_SET_INVALID")
    atoms: list[str] = value
    if (
        any(not _meaningful(atom) for atom in atoms)
        or atoms != _utf8_sorted(atoms)
        or len(atoms) != len(set(atoms))
    ):
        raise _ValidationError("ATOM_SET_INVALID")


def _validate_boundary_list(value: object) -> None:
    if type(value) is not list:
        raise _ValidationError("BOUNDARY_RECORDS_INVALID")
    records: list[Any] = value
    for record in records:
        if (
            type(record) is not dict
            or tuple(record) != _BOUNDARY_FIELDS
            or any(type(record[field]) is not str for field in _BOUNDARY_FIELDS)
            or any(not _meaningful(record[field]) for field in _BOUNDARY_FIELDS)
        ):
            raise _ValidationError("BOUNDARY_RECORDS_INVALID")
    try:
        ordered = sorted(
            records,
            key=lambda record: record["boundary_bond_id"].encode("utf-8"),
        )
    except UnicodeEncodeError as error:
        raise _ValidationError("BOUNDARY_RECORDS_INVALID") from error
    if records != ordered:
        raise _ValidationError("BOUNDARY_RECORDS_INVALID")
    ids: set[str] = set()
    endpoints: set[tuple[str, str]] = set()
    for record in records:
        attachment = record["warhead_attachment_atom_id"]
        nonwarhead = record["nonwarhead_boundary_atom_id"]
        order = record["boundary_bond_order"]
        try:
            low, high = sorted(
                (attachment, nonwarhead),
                key=lambda value: value.encode("utf-8"),
            )
        except UnicodeEncodeError as error:
            raise _ValidationError("BOUNDARY_RECORDS_INVALID") from error
        endpoint = (low, high)
        identifier = record["boundary_bond_id"]
        if (
            attachment == nonwarhead
            or order not in _NORMALIZED_BOND_ORDERS
            or identifier != f"{low}|{high}|{order}"
            or identifier in ids
            or endpoint in endpoints
        ):
            raise _ValidationError("BOUNDARY_RECORDS_INVALID")
        ids.add(identifier)
        endpoints.add(endpoint)


def _validate_atoms_and_boundaries(
    items: Sequence[dict[str, Any]],
) -> None:
    for item in items:
        _validate_atom_list(item["proposed_warhead_atom_ids"])
        _validate_atom_list(item["reviewed_warhead_atom_ids"])
    for item in items:
        _validate_boundary_list(item["proposed_boundary_records"])
        _validate_boundary_list(item["reviewed_boundary_records"])


def _validate_decision_semantics(
    items: Sequence[dict[str, Any]],
) -> None:
    for item in items:
        decision = item["review_decision"]
        proposed_atoms = item["proposed_warhead_atom_ids"]
        proposed_boundaries = item["proposed_boundary_records"]
        reviewed_atoms = item["reviewed_warhead_atom_ids"]
        reviewed_boundaries = item["reviewed_boundary_records"]
        if decision == "accept_verified_two_boundary_proposal":
            if (
                not proposed_atoms
                or len(proposed_boundaries) != 2
                or not reviewed_atoms
                or len(reviewed_boundaries) != 2
                or reviewed_atoms != proposed_atoms
                or reviewed_boundaries != proposed_boundaries
            ):
                raise _ValidationError("ACCEPT_SEMANTICS_INVALID")
        elif decision == "revise_two_boundary_atom_set_and_boundaries":
            if (
                not proposed_atoms
                or len(proposed_boundaries) != 2
                or not reviewed_atoms
                or len(reviewed_boundaries) != 2
                or (
                    reviewed_atoms == proposed_atoms
                    and reviewed_boundaries == proposed_boundaries
                )
            ):
                raise _ValidationError("REVISION_SEMANTICS_INVALID")
        elif reviewed_atoms or reviewed_boundaries:
            raise _ValidationError("QUARANTINE_SEMANTICS_INVALID")


def _success_response(
    *,
    source_payload_sha256: str,
    canonical_source_bundle_sha256: str,
    submission_batch_id: str,
    items: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    envelopes: list[dict[str, Any]] = []
    for item in items:
        envelope: dict[str, Any] = {
            "multi_boundary_ingestion_envelope_version": _ENVELOPE_VERSION,
            "submission_batch_id": submission_batch_id,
            "item_index_0based": item["item_index_0based"],
            "sample_index_row_id": item["sample_index_row_id"],
            "source_multi_boundary_submission_bundle_sha256":
                canonical_source_bundle_sha256,
            "source_multi_boundary_review_record_sha256":
                item["multi_boundary_review_record_sha256"],
            "review_record_payload": copy.deepcopy(item),
            "reviewer_provenance_attested":
                item["reviewer_provenance_attested"],
            "reviewer_provenance_attestor_id":
                item["reviewer_provenance_attestor_id"],
            "submission_source_label": item["submission_source_label"],
            "ready_for_ingestion": True,
            "multi_boundary_ingestion_envelope_sha256": "",
        }
        envelope["multi_boundary_ingestion_envelope_sha256"] = _digest(
            envelope,
            _ENVELOPE_FIELDS,
            "multi_boundary_ingestion_envelope_sha256",
        )
        envelopes.append(envelope)
    results: list[dict[str, Any]] = []
    for item, envelope in zip(items, envelopes):
        result: dict[str, Any] = {
            "multi_boundary_submission_adapter_result_version":
                _RESULT_VERSION,
            "item_index_0based": item["item_index_0based"],
            "submission_batch_id": submission_batch_id,
            "sample_index_row_id": item["sample_index_row_id"],
            "outcome": "adapted",
            "passed": True,
            "reason": "PASSED",
            "source_multi_boundary_review_record_sha256":
                item["multi_boundary_review_record_sha256"],
            "ingestion_envelope_sha256":
                envelope["multi_boundary_ingestion_envelope_sha256"],
            "consumed_submission_item": True,
            "ready_for_ingestion": True,
            "multi_boundary_submission_adapter_result_sha256": "",
        }
        result["multi_boundary_submission_adapter_result_sha256"] = _digest(
            result,
            _RESULT_FIELDS,
            "multi_boundary_submission_adapter_result_sha256",
        )
        results.append(result)
    return _response(
        source_payload_sha256=source_payload_sha256,
        canonical_source_bundle_sha256=canonical_source_bundle_sha256,
        submission_batch_id=submission_batch_id,
        adapter_passed=True,
        reason="PASSED",
        adapter_result_records=tuple(results),
        adapted_submissions=tuple(envelopes),
    )


def _response(
    *,
    source_payload_sha256: str,
    canonical_source_bundle_sha256: str,
    submission_batch_id: str,
    adapter_passed: bool,
    reason: str,
    adapter_result_records: tuple[dict[str, Any], ...],
    adapted_submissions: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "multi_boundary_submission_adapter_response_version":
            _RESPONSE_VERSION,
        "source_payload_sha256": source_payload_sha256,
        "canonical_source_bundle_sha256": canonical_source_bundle_sha256,
        "submission_batch_id": submission_batch_id,
        "adapter_passed": adapter_passed,
        "reason": reason,
        "adapter_result_records": adapter_result_records,
        "adapted_submissions": adapted_submissions,
        "multi_boundary_submission_adapter_response_sha256": "",
    }
    try:
        response["multi_boundary_submission_adapter_response_sha256"] = (
            _digest(
                response,
                _RESPONSE_FIELDS,
                "multi_boundary_submission_adapter_response_sha256",
            )
        )
        _validate_response(response)
    except (KeyError, TypeError, _ValidationError) as error:
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID") from error
    return response


def _validate_response(response: dict[str, Any]) -> None:
    if (
        type(response) is not dict
        or tuple(response) != _RESPONSE_FIELDS
        or response[
            "multi_boundary_submission_adapter_response_version"
        ] != _RESPONSE_VERSION
        or type(response["source_payload_sha256"]) is not str
        or type(response["canonical_source_bundle_sha256"]) is not str
        or type(response["submission_batch_id"]) is not str
        or type(response["adapter_passed"]) is not bool
        or response["reason"] not in _REASONS
        or type(response["adapter_result_records"]) is not tuple
        or type(response["adapted_submissions"]) is not tuple
        or _SHA256.fullmatch(
            response["multi_boundary_submission_adapter_response_sha256"]
        ) is None
        or response["multi_boundary_submission_adapter_response_sha256"]
        != _digest(
            response,
            _RESPONSE_FIELDS,
            "multi_boundary_submission_adapter_response_sha256",
        )
    ):
        raise _ValidationError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    passed = response["adapter_passed"]
    results = response["adapter_result_records"]
    envelopes = response["adapted_submissions"]
    if not passed:
        if (
            response["reason"] == "PASSED"
            or results
            or envelopes
            or (
                response["source_payload_sha256"] != ""
                and _SHA256.fullmatch(
                    response["source_payload_sha256"]
                ) is None
            )
            or (
                response["canonical_source_bundle_sha256"] != ""
                and _SHA256.fullmatch(
                    response["canonical_source_bundle_sha256"]
                ) is None
            )
            or (
                response["submission_batch_id"] != ""
                and not _meaningful(response["submission_batch_id"])
            )
        ):
            raise _ValidationError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        return
    if (
        response["reason"] != "PASSED"
        or len(results) != 5
        or len(envelopes) != 5
        or not _meaningful(response["submission_batch_id"])
        or _SHA256.fullmatch(response["source_payload_sha256"]) is None
        or _SHA256.fullmatch(
            response["canonical_source_bundle_sha256"]
        ) is None
    ):
        raise _ValidationError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    envelope_shas: set[str] = set()
    for position, envelope in enumerate(envelopes):
        if (
            type(envelope) is not dict
            or tuple(envelope) != _ENVELOPE_FIELDS
            or envelope["multi_boundary_ingestion_envelope_version"]
            != _ENVELOPE_VERSION
            or envelope["item_index_0based"] != position
            or envelope["sample_index_row_id"] != _TARGET_SAMPLES[position]
            or envelope["submission_batch_id"]
            != response["submission_batch_id"]
            or envelope[
                "source_multi_boundary_submission_bundle_sha256"
            ] != response["canonical_source_bundle_sha256"]
            or envelope["reviewer_provenance_attested"] is not True
            or envelope["ready_for_ingestion"] is not True
            or type(envelope["review_record_payload"]) is not dict
            or tuple(envelope["review_record_payload"]) != _RECORD_FIELDS
            or envelope["review_record_payload"]["item_index_0based"]
            != position
            or envelope["review_record_payload"]["sample_index_row_id"]
            != _TARGET_SAMPLES[position]
            or envelope["source_multi_boundary_review_record_sha256"]
            != envelope["review_record_payload"][
                "multi_boundary_review_record_sha256"
            ]
            or envelope["reviewer_provenance_attested"]
            != envelope["review_record_payload"][
                "reviewer_provenance_attested"
            ]
            or envelope["reviewer_provenance_attestor_id"]
            != envelope["review_record_payload"][
                "reviewer_provenance_attestor_id"
            ]
            or envelope["submission_source_label"]
            != envelope["review_record_payload"]["submission_source_label"]
            or envelope["multi_boundary_ingestion_envelope_sha256"]
            != _digest(
                envelope,
                _ENVELOPE_FIELDS,
                "multi_boundary_ingestion_envelope_sha256",
            )
        ):
            raise _ValidationError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        envelope_shas.add(
            envelope["multi_boundary_ingestion_envelope_sha256"]
        )
    if len(envelope_shas) != 5:
        raise _ValidationError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    for position, result in enumerate(results):
        envelope = envelopes[position]
        if (
            type(result) is not dict
            or tuple(result) != _RESULT_FIELDS
            or result[
                "multi_boundary_submission_adapter_result_version"
            ] != _RESULT_VERSION
            or result["item_index_0based"] != position
            or result["submission_batch_id"] != response["submission_batch_id"]
            or result["sample_index_row_id"] != _TARGET_SAMPLES[position]
            or result["outcome"] != "adapted"
            or result["passed"] is not True
            or result["reason"] != "PASSED"
            or result["source_multi_boundary_review_record_sha256"]
            != envelope["source_multi_boundary_review_record_sha256"]
            or result["ingestion_envelope_sha256"]
            != envelope["multi_boundary_ingestion_envelope_sha256"]
            or result["consumed_submission_item"] is not True
            or result["ready_for_ingestion"] is not True
            or result["multi_boundary_submission_adapter_result_sha256"]
            != _digest(
                result,
                _RESULT_FIELDS,
                "multi_boundary_submission_adapter_result_sha256",
            )
        ):
            raise _ValidationError("ADAPTER_RESPONSE_INVARIANT_INVALID")


def adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
    *,
    source_payload: bytes,
) -> dict[str, Any]:
    """Return an atomic Exact9 response for strict Exact10 JSON bytes."""

    source_payload_sha256 = ""
    canonical_source_bundle_sha256 = ""
    submission_batch_id = ""
    try:
        payload, bundle = _parse_source(source_payload)
        source_payload_sha256 = _sha256(payload)
        if (
            tuple(bundle) == _BUNDLE_FIELDS
            and _meaningful(bundle.get("submission_batch_id"))
        ):
            submission_batch_id = bundle["submission_batch_id"]
        canonical_source_bundle_sha256 = _validate_bundle(bundle)
        items = _validate_item_inventories(bundle["submission_items"])
        _validate_item_types(items)
        _validate_item_identity(items)
        _validate_record_digests(items)
        _validate_completion_and_provenance(items)
        _validate_atoms_and_boundaries(items)
        _validate_decision_semantics(items)
        return _success_response(
            source_payload_sha256=source_payload_sha256,
            canonical_source_bundle_sha256=
                canonical_source_bundle_sha256,
            submission_batch_id=submission_batch_id,
            items=items,
        )
    except _ValidationError as error:
        if type(source_payload) is bytes and not source_payload_sha256:
            source_payload_sha256 = _sha256(source_payload)
        return _response(
            source_payload_sha256=source_payload_sha256,
            canonical_source_bundle_sha256=
                canonical_source_bundle_sha256,
            submission_batch_id=submission_batch_id,
            adapter_passed=False,
            reason=error.reason,
            adapter_result_records=(),
            adapted_submissions=(),
        )
