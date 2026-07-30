"""Build the Current11 Exact5 two-boundary human-review sidecar in memory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

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
    "build_covapie_current11_multi_boundary_human_review_sidecar_v1",
)


_EVIDENCE_VERSION = (
    "covapie_current11_verified_multi_boundary_evidence_v1"
)
_REVIEW_VERSION = (
    "covapie_current11_multi_boundary_human_review_record_v1"
)
_EXECUTION_VERSION = (
    "covapie_current11_real_human_review_ingestion_execution_bundle_v1"
)
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_TARGET_SAMPLES = _EXPECTED_SAMPLES[5:10]
_EXECUTION_FIELDS = (
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
_EVIDENCE_FIELDS = (
    "multi_boundary_evidence_version",
    "sidecar_item_order_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_submission_bundle_sha256",
    "source_ingestion_execution_bundle_filesystem_sha256",
    "source_ingestion_execution_bundle_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_review_record_sha256",
    "source_ingestion_envelope_sha256",
    "source_proposal_record_sha256",
    "source_assignment_record_sha256",
    "source_candidate_set_sha256",
    "source_review_notes_sha256",
    "covalent_ligand_atom_id",
    "local_reaction_center_atom_ids_json",
    "required_leaving_group_atom_ids_json",
    "proposed_warhead_atom_ids_json",
    "proposed_boundary_records_json",
    "graph_derived_boundary_records_json",
    "graph_derived_boundary_count",
    "warhead_subgraph_connected",
    "contains_local_reaction_center",
    "contains_required_leaving_groups",
    "notes_match_parent_graph",
    "exact_two_boundaries_verified",
    "scope_caveat",
    "evidence_record_sha256",
)
_WORKLIST_FIELDS = (
    "multi_boundary_review_record_version",
    "sidecar_item_order_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_evidence_record_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_review_record_sha256",
    "proposed_warhead_atom_ids_json",
    "proposed_boundary_records_json",
    "scope_caveat",
    "review_decision",
    "reviewed_warhead_atom_ids_json",
    "reviewed_boundary_records_json",
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
_SHA = re.compile(r"[0-9a-f]{64}")
_MAX_SOURCE_BYTES = 1024 * 1024
_INDEPENDENT_CORE_CAVEAT = (
    "final multi-boundary gold core requires independent human review"
)


@dataclass(frozen=True)
class _FrozenBoundary:
    warhead_attachment_atom_id: str
    nonwarhead_boundary_atom_id: str
    boundary_bond_order: str
    boundary_bond_id: str


@dataclass(frozen=True)
class _FrozenProposalSeed:
    sample_index_row_id: str
    pdb_id: str
    ligand_comp_id: str
    proposed_warhead_atom_ids: tuple[str, ...]
    boundaries: tuple[_FrozenBoundary, _FrozenBoundary]
    scope_caveat: str = ""


_FROZEN_PROPOSAL_SEEDS = (
    _FrozenProposalSeed(
        "CYS_SG_SAMPLE_INDEX_000006",
        "1AU3",
        "PCM",
        ("C19", "C21", "C22", "C42", "N18", "N41", "O23"),
        (
            _FrozenBoundary("N18", "C16", "single", "C16|N18|single"),
            _FrozenBoundary("N41", "C39", "single", "C39|N41|single"),
        ),
    ),
    _FrozenProposalSeed(
        "CYS_SG_SAMPLE_INDEX_000007",
        "1AU4",
        "INP",
        ("C15", "C16", "C17", "C18", "N14", "N23", "O42"),
        (
            _FrozenBoundary("N14", "C13", "single", "C13|N14|single"),
            _FrozenBoundary("N23", "C24", "single", "C24|N23|single"),
        ),
    ),
    _FrozenProposalSeed(
        "CYS_SG_SAMPLE_INDEX_000008",
        "1AYU",
        "INA",
        ("C21", "N18", "N19", "N40", "N41", "O22"),
        (
            _FrozenBoundary("N18", "C16", "single", "C16|N18|single"),
            _FrozenBoundary("N40", "C38", "single", "C38|N40|single"),
        ),
    ),
    _FrozenProposalSeed(
        "CYS_SG_SAMPLE_INDEX_000009",
        "1AYV",
        "IN6",
        (
            "C17", "C20", "C21", "C42", "CH'", "N19", "NJ'", "NK'",
            "O22", "OI'", "S18",
        ),
        (
            _FrozenBoundary("C17", "C11", "single", "C11|C17|single"),
            _FrozenBoundary("CH'", "CB'", "single", "CB'|CH'|single"),
        ),
        _INDEPENDENT_CORE_CAVEAT,
    ),
    _FrozenProposalSeed(
        "CYS_SG_SAMPLE_INDEX_000010",
        "1AYW",
        "IN3",
        (
            "C17", "C21", "CH'", "N19", "N20", "NJ'", "NK'", "O18",
            "O22", "OI'",
        ),
        (
            _FrozenBoundary("C17", "C11", "single", "C11|C17|single"),
            _FrozenBoundary("CH'", "CB'", "single", "CB'|CH'|single"),
        ),
        _INDEPENDENT_CORE_CAVEAT,
    ),
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (
        TypeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("SIDECAR_CANONICAL_JSON_INVALID") from error


def _ordered_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (
        TypeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("SIDECAR_ORDERED_JSON_INVALID") from error


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def _meaningful(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and "\x00" not in value
    )


def _record_sha(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    if type(record) is not dict or tuple(record) != tuple(fields):
        raise ValueError("SIDECAR_RECORD_FIELD_INVENTORY_INVALID")
    return _sha256(_canonical_json({
        field: record[field] for field in fields if field != digest_field
    }).encode("utf-8"))


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        with io.StringIO(payload.decode("utf-8"), newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise ValueError("SIDECAR_COMMITTED_CSV_HEADER_MISSING")
            return list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("SIDECAR_COMMITTED_CSV_INVALID") from error


def _csv_bytes(
    fields: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if type(row) is not dict or tuple(row) != tuple(fields):
            raise ValueError("SIDECAR_OUTPUT_ROW_FIELD_INVENTORY_INVALID")
        if any(type(row[field]) is not str for field in fields):
            raise ValueError("SIDECAR_OUTPUT_ROW_TYPE_INVALID")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _parse_exact_list(cell: str, field: str) -> list[str]:
    try:
        value = json.loads(cell)
    except (TypeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"SIDECAR_COMMITTED_LIST_INVALID:{field}") from error
    if (
        type(value) is not list
        or any(type(item) is not str or not _meaningful(item) for item in value)
    ):
        raise ValueError(f"SIDECAR_COMMITTED_LIST_INVALID:{field}")
    return value


def _parse_nonnegative_int(cell: str, field: str) -> int:
    if (
        type(cell) is not str
        or not cell.isdecimal()
        or (len(cell) > 1 and cell.startswith("0"))
    ):
        raise ValueError(f"SIDECAR_COMMITTED_INT_INVALID:{field}")
    return int(cell)


def _validate_adapter_response(
    response: object,
    *,
    source_submission_bundle: bytes,
) -> tuple[tuple[dict[str, Any], dict[str, Any]], ...]:
    if (
        type(response) is not dict
        or tuple(response) != tuple(adapter_design.ADAPTER_RESPONSE_FIELDS)
    ):
        raise ValueError("SIDECAR_SUBMISSION_ADAPTER_RESPONSE_INVALID")
    if (
        type(response["submission_adapter_response_version"]) is not str
        or type(response["source_payload_sha256"]) is not str
        or type(response["canonical_bundle_sha256"]) is not str
        or type(response["submission_batch_id"]) is not str
        or type(response["adapter_passed"]) is not bool
        or type(response["reason"]) is not str
        or type(response["adapter_result_records"]) is not tuple
        or type(response["adapted_submissions"]) is not tuple
        or type(response["submission_adapter_response_sha256"]) is not str
    ):
        raise ValueError("SIDECAR_SUBMISSION_ADAPTER_RESPONSE_INVALID")
    try:
        decoded_source = json.loads(source_submission_bundle)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("SIDECAR_SUBMISSION_SOURCE_INVALID") from error
    if (
        response["submission_adapter_response_version"]
        != adapter_design.SUBMISSION_ADAPTER_RESPONSE_VERSION
        or response["adapter_passed"] is not True
        or response["reason"] != "PASSED"
        or response["source_payload_sha256"]
        != _sha256(source_submission_bundle)
        or response["canonical_bundle_sha256"]
        != _sha256(_canonical_json(decoded_source).encode("utf-8"))
        or not _meaningful(response["submission_batch_id"])
        or _SHA.fullmatch(
            response["submission_adapter_response_sha256"]
        ) is None
        or response["submission_adapter_response_sha256"]
        != _record_sha(
            response,
            adapter_design.ADAPTER_RESPONSE_FIELDS,
            "submission_adapter_response_sha256",
        )
    ):
        raise ValueError("SIDECAR_SUBMISSION_ADAPTER_RESPONSE_INVALID")
    results = response["adapter_result_records"]
    submissions = response["adapted_submissions"]
    if len(results) != 11 or len(submissions) != 11:
        raise ValueError("SIDECAR_SUBMISSION_COUNT_INVALID")
    validated: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for position, (result, submission) in enumerate(zip(results, submissions)):
        if (
            type(result) is not dict
            or tuple(result) != tuple(adapter_design.ADAPTER_RESULT_FIELDS)
            or type(submission) is not tuple
            or len(submission) != 2
            or type(submission[0]) is not dict
            or type(submission[1]) is not dict
        ):
            raise ValueError("SIDECAR_ADAPTED_SUBMISSION_INVALID")
        review, envelope = submission
        sample = _EXPECTED_SAMPLES[position]
        if (
            result["submission_adapter_result_version"]
            != adapter_design.SUBMISSION_ADAPTER_RESULT_VERSION
            or result["item_index_0based"] != position
            or type(result["item_index_0based"]) is not int
            or result["outcome"] != "adapted"
            or result["passed"] is not True
            or result["reason"] != "PASSED"
            or result["consumed_submission_item"] is not True
            or result["ready_for_interface_evaluation"] is not True
            or result["submission_batch_id"]
            != response["submission_batch_id"]
            or result["sample_index_row_id"] != sample
            or review.get("sample_index_row_id") != sample
            or envelope.get("sample_index_row_id") != sample
            or envelope.get("submission_batch_id")
            != response["submission_batch_id"]
            or result["review_record_sha256"]
            != review.get("review_record_sha256")
            or result["ingestion_envelope_sha256"]
            != envelope.get("ingestion_envelope_sha256")
            or result["submission_adapter_result_sha256"]
            != _record_sha(
                result,
                adapter_design.ADAPTER_RESULT_FIELDS,
                "submission_adapter_result_sha256",
            )
        ):
            raise ValueError("SIDECAR_ADAPTED_SUBMISSION_LINEAGE_INVALID")
        try:
            if (
                review["review_record_sha256"]
                != ingestion_design.review_record_sha256(review)
            ):
                raise ValueError("review record SHA mismatch")
            ingestion_design.validate_ingestion_envelope(
                envelope,
                review_record=review,
                valid_sample_ids=(sample,),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("SIDECAR_ADAPTED_SUBMISSION_INVALID") from error
        if (
            sample in _TARGET_SAMPLES
            and (
                review["review_decision"] != "quarantine"
                or not _meaningful(review["reviewer_id"])
                or not _meaningful(review["review_rationale"])
                or not _meaningful(review["review_notes"])
                or _SHA.fullmatch(review["review_record_sha256"]) is None
                or _SHA.fullmatch(envelope["ingestion_envelope_sha256"]) is None
            )
        ):
            raise ValueError("SIDECAR_TARGET_REVIEW_INVALID")
        validated.append((review, envelope))
    return tuple(validated)


def _decode_execution_bundle(
    payload: bytes,
    *,
    source_submission_bundle: bytes,
    adapter_response: Mapping[str, Any],
    submissions: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    authority_context: ingestion_design.IngestionAuthorityContext,
) -> dict[str, Any]:
    if (
        not payload
        or len(payload) >= _MAX_SOURCE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\n" in payload
    ):
        raise ValueError("SIDECAR_EXECUTION_BYTE_CONTRACT_INVALID")
    try:
        bundle = json.loads(payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("SIDECAR_EXECUTION_JSON_INVALID") from error
    if type(bundle) is not dict or tuple(bundle) != _EXECUTION_FIELDS:
        raise ValueError("SIDECAR_EXECUTION_EXACT12_INVALID")
    if (
        type(bundle["ingestion_execution_bundle_version"]) is not str
        or type(bundle["source_submission_bundle_sha256"]) is not str
        or type(bundle["source_canonical_bundle_sha256"]) is not str
        or type(bundle["submission_batch_id"]) is not str
        or type(bundle["submission_adapter_response_sha256"]) is not str
        or type(bundle["ingestion_interface_response_version"]) is not str
        or type(bundle["authority_context_record_sha256"]) is not str
        or type(bundle["batch_passed"]) is not bool
        or type(bundle["ingestion_result_records"]) is not list
        or type(bundle["new_authority_records"]) is not list
        or type(bundle["ingestion_interface_response_sha256"]) is not str
        or type(bundle["ingestion_execution_bundle_sha256"]) is not str
    ):
        raise ValueError("SIDECAR_EXECUTION_EXACT12_INVALID")
    expected_bundle_sha = _sha256(_canonical_json({
        field: bundle[field]
        for field in _EXECUTION_FIELDS
        if field != "ingestion_execution_bundle_sha256"
    }).encode("utf-8"))
    context_sha = authority_context.context_record[
        "ingestion_authority_context_record_sha256"
    ]
    if (
        bundle["ingestion_execution_bundle_version"] != _EXECUTION_VERSION
        or bundle["ingestion_execution_bundle_sha256"] != expected_bundle_sha
        or _SHA.fullmatch(expected_bundle_sha) is None
        or bundle["source_submission_bundle_sha256"]
        != _sha256(source_submission_bundle)
        or bundle["source_submission_bundle_sha256"]
        != adapter_response["source_payload_sha256"]
        or bundle["source_canonical_bundle_sha256"]
        != adapter_response["canonical_bundle_sha256"]
        or bundle["submission_batch_id"]
        != adapter_response["submission_batch_id"]
        or bundle["submission_adapter_response_sha256"]
        != adapter_response["submission_adapter_response_sha256"]
        or bundle["authority_context_record_sha256"] != context_sha
        or bundle["batch_passed"] is not True
        or len(bundle["ingestion_result_records"]) != 11
        or len(bundle["new_authority_records"]) != 11
    ):
        raise ValueError("SIDECAR_EXECUTION_LINEAGE_INVALID")
    interface_response: dict[str, Any] = {
        "interface_response_version":
            bundle["ingestion_interface_response_version"],
        "authority_context_record_sha256":
            bundle["authority_context_record_sha256"],
        "batch_passed": bundle["batch_passed"],
        "ingestion_result_records":
            tuple(bundle["ingestion_result_records"]),
        "new_authority_records": tuple(bundle["new_authority_records"]),
        "interface_response_sha256":
            bundle["ingestion_interface_response_sha256"],
    }
    try:
        ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
            interface_response,
            submissions=submissions,
            authority_context=authority_context,
            existing_authorities=(),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("SIDECAR_EXECUTION_INTERFACE_INVALID") from error
    results = bundle["ingestion_result_records"]
    authorities = bundle["new_authority_records"]
    if (
        tuple(record.get("sample_index_row_id") for record in results)
        != _EXPECTED_SAMPLES
        or tuple(record.get("sample_index_row_id") for record in authorities)
        != _EXPECTED_SAMPLES
    ):
        raise ValueError("SIDECAR_EXECUTION_SAMPLE_ORDER_INVALID")
    for position, (submission, result, authority) in enumerate(
        zip(submissions, results, authorities)
    ):
        review, envelope = submission
        try:
            ingestion_design.validate_ingestion_result(result)
            ingestion_design.validate_authority_record(authority)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("SIDECAR_EXECUTION_RECORD_INVALID") from error
        if (
            result["submission_batch_id"] != bundle["submission_batch_id"]
            or result["sample_index_row_id"] != review["sample_index_row_id"]
            or result["review_record_sha256"] != review["review_record_sha256"]
            or result["ingestion_envelope_sha256"]
            != envelope["ingestion_envelope_sha256"]
            or result["review_decision"] != review["review_decision"]
            or result["outcome"] != "passed"
            or result["passed"] is not True
            or result["reason"] != "PASSED"
            or result["authority_record_sha256"]
            != authority["authority_record_sha256"]
            or authority["source_review_record_sha256"]
            != review["review_record_sha256"]
            or authority["source_ingestion_envelope_sha256"]
            != envelope["ingestion_envelope_sha256"]
            or authority["review_decision"] != review["review_decision"]
            or authority["authority_disposition"]
            != result["authority_disposition"]
            or authority["review_rationale_sha256"]
            != _sha256(review["review_rationale"].encode("utf-8"))
        ):
            raise ValueError(
                f"SIDECAR_EXECUTION_RECORD_LINEAGE_INVALID:{position}"
            )
        if authority["sample_index_row_id"] in _TARGET_SAMPLES:
            if (
                result["review_decision"] != "quarantine"
                or result["authority_disposition"]
                != "reviewed_quarantine_no_authority"
                or authority["review_decision"] != "quarantine"
                or authority["authority_status"] != "quarantined"
                or authority["authority_disposition"]
                != "reviewed_quarantine_no_authority"
                or authority["sample_quarantined"] is not True
                or authority["complete_warhead_atom_set_authority_available"]
                is not False
                or authority[
                    "exact_one_attachment_boundary_authority_available"
                ] is not False
                or authority["reviewed_warhead_atom_ids"] != []
                or authority["reviewed_warhead_attachment_atom_id"] != ""
                or authority["reviewed_nonwarhead_boundary_atom_id"] != ""
                or authority["reviewed_attachment_boundary_bond_order"] != ""
                or authority["reviewed_boundary_bond_id"] != ""
            ):
                raise ValueError("SIDECAR_TARGET_QUARANTINE_AUTHORITY_INVALID")
    return bundle


def _context_payloads(
    context: ingestion_design.IngestionAuthorityContext,
) -> Mapping[Path, bytes]:
    try:
        ingestion_design.validate_ingestion_authority_context(context)
        payloads = {
            Path(path): payload for path, payload in context.source_payloads
        }
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("SIDECAR_AUTHORITY_CONTEXT_INVALID") from error
    required = {
        ingestion_design.PACKAGE_INDEX,
        ingestion_design.PACKAGE_TEMPLATES,
        ingestion_design.PROPOSALS,
        ingestion_design.ASSIGNMENTS,
        ingestion_design.PARENT_ATOMS,
        ingestion_design.PARENT_BONDS,
    }
    if not required <= set(payloads):
        raise ValueError("SIDECAR_AUTHORITY_CONTEXT_SOURCE_MISSING")
    return MappingProxyType(payloads)


def _typed_proposal(row: Mapping[str, str]) -> dict[str, Any]:
    if type(row) is not dict or tuple(row) != ingestion_design.PROPOSAL_FIELDS:
        raise ValueError("SIDECAR_PROPOSAL_FIELD_INVENTORY_INVALID")
    list_fields = {
        "local_reaction_center_atom_ids",
        "local_reaction_center_bond_ids",
        "proposed_pre_reaction_warhead_atom_ids",
        "required_leaving_group_atom_ids",
        "ambiguity_reasons",
    }
    proposal: dict[str, Any] = {}
    for field in ingestion_design.PROPOSAL_FIELDS:
        if field == "warhead_type_candidate_class_index_0based":
            proposal[field] = _parse_nonnegative_int(row[field], field)
        elif field in list_fields:
            proposal[field] = _parse_exact_list(row[field], field)
        else:
            proposal[field] = row[field]
    if (
        proposal["proposal_record_sha256"]
        != _record_sha(
            proposal,
            ingestion_design.PROPOSAL_FIELDS,
            "proposal_record_sha256",
        )
    ):
        raise ValueError("SIDECAR_PROPOSAL_SHA_INVALID")
    return proposal


def _validate_assignment(row: Mapping[str, str]) -> None:
    if (
        type(row) is not dict
        or "assignment_record_sha256" not in row
        or any(field not in row for field in ingestion_design.ASSIGNMENT_HASH_FIELDS)
    ):
        raise ValueError("SIDECAR_ASSIGNMENT_FIELD_INVENTORY_INVALID")
    payload = {
        field: (
            _parse_nonnegative_int(row[field], field)
            if field == "warhead_type_candidate_class_index_0based"
            else row[field]
        )
        for field in ingestion_design.ASSIGNMENT_HASH_FIELDS
    }
    if (
        row["assignment_record_sha256"]
        != _sha256(_canonical_json(payload).encode("utf-8"))
        or row.get("candidate_rule_assignment_exact_one") != "true"
        or row.get("candidate_family_assignment_exact_one") != "true"
        or row.get("class_vocabulary_join_exact_one") != "true"
        or row.get("verified") != "true"
    ):
        raise ValueError("SIDECAR_ASSIGNMENT_INVALID")


def _boundary_record(
    *,
    attachment: str,
    nonwarhead: str,
    order: str,
) -> dict[str, str]:
    low, high = _utf8_sorted((attachment, nonwarhead))
    return {
        "warhead_attachment_atom_id": attachment,
        "nonwarhead_boundary_atom_id": nonwarhead,
        "boundary_bond_order": order,
        "boundary_bond_id": f"{low}|{high}|{order}",
    }


def _frozen_boundary_records(
    seed: _FrozenProposalSeed,
) -> list[dict[str, str]]:
    records = [
        {
            "warhead_attachment_atom_id":
                boundary.warhead_attachment_atom_id,
            "nonwarhead_boundary_atom_id":
                boundary.nonwarhead_boundary_atom_id,
            "boundary_bond_order": boundary.boundary_bond_order,
            "boundary_bond_id": boundary.boundary_bond_id,
        }
        for boundary in seed.boundaries
    ]
    if (
        any(tuple(record) != _BOUNDARY_FIELDS for record in records)
        or records != sorted(
            records,
            key=lambda record: record["boundary_bond_id"].encode("utf-8"),
        )
    ):
        raise ValueError("SIDECAR_FROZEN_BOUNDARY_ORDER_INVALID")
    return records


def _validate_graph_seed(
    seed: _FrozenProposalSeed,
    *,
    proposal: Mapping[str, Any],
    parent_atom_rows: Sequence[Mapping[str, str]],
    parent_bond_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    atoms = list(seed.proposed_warhead_atom_ids)
    if (
        not atoms
        or any(not _meaningful(atom) for atom in atoms)
        or len(atoms) != len(set(atoms))
        or atoms != _utf8_sorted(atoms)
    ):
        raise ValueError("SIDECAR_FROZEN_ATOM_SET_INVALID")
    if (
        not parent_atom_rows
        or not parent_bond_rows
        or any(
            tuple(row) != ingestion_design.PARENT_ATOM_FIELDS
            for row in parent_atom_rows
        )
        or any(
            tuple(row) != ingestion_design.PARENT_BOND_FIELDS
            for row in parent_bond_rows
        )
    ):
        raise ValueError("SIDECAR_PARENT_GRAPH_FIELD_INVENTORY_INVALID")
    parent_atoms = [row["ccd_atom_id"] for row in parent_atom_rows]
    parent_set = set(parent_atoms)
    atom_set = set(atoms)
    if (
        any(not _meaningful(atom) for atom in parent_atoms)
        or len(parent_atoms) != len(parent_set)
        or not atom_set <= parent_set
        or not atom_set < parent_set
    ):
        raise ValueError("SIDECAR_PARENT_ATOM_SET_INVALID")
    local_atoms = proposal["local_reaction_center_atom_ids"]
    leaving_atoms = proposal["required_leaving_group_atom_ids"]
    if (
        not set(local_atoms) <= atom_set
        or not set(leaving_atoms) <= atom_set
    ):
        raise ValueError("SIDECAR_REQUIRED_PROPOSAL_ATOMS_MISSING")
    internal_adjacency: dict[str, set[str]] = {
        atom: set() for atom in atoms
    }
    parent_edges: dict[frozenset[str], tuple[str, str, str]] = {}
    derived: list[dict[str, str]] = []
    for row in parent_bond_rows:
        left = row["parent_ccd_atom_id_1"]
        right = row["parent_ccd_atom_id_2"]
        order = row["normalized_bond_order"]
        edge = frozenset((left, right))
        if (
            not _meaningful(left)
            or not _meaningful(right)
            or left == right
            or left not in parent_set
            or right not in parent_set
            or len(edge) != 2
            or edge in parent_edges
            or order not in ingestion_design.PARENT_NORMALIZED_BOND_ORDERS
        ):
            raise ValueError("SIDECAR_PARENT_BOND_INVALID")
        parent_edges[edge] = (left, right, order)
        if left in atom_set and right in atom_set:
            internal_adjacency[left].add(right)
            internal_adjacency[right].add(left)
        elif (left in atom_set) != (right in atom_set):
            attachment = left if left in atom_set else right
            nonwarhead = right if attachment == left else left
            derived.append(_boundary_record(
                attachment=attachment,
                nonwarhead=nonwarhead,
                order=order,
            ))
    reached: set[str] = set()
    queue: deque[str] = deque((atoms[0],))
    while queue:
        atom = queue.popleft()
        if atom in reached:
            continue
        reached.add(atom)
        queue.extend(internal_adjacency[atom] - reached)
    if reached != atom_set:
        raise ValueError("SIDECAR_WARHEAD_SUBGRAPH_DISCONNECTED")
    for bond_id in proposal["local_reaction_center_bond_ids"]:
        try:
            left, right, order = bond_id.split("|")
        except ValueError as error:
            raise ValueError("SIDECAR_LOCAL_CENTER_BOND_INVALID") from error
        low, high = _utf8_sorted((left, right))
        parent = parent_edges.get(frozenset((left, right)))
        if (
            f"{low}|{high}|{order}" != bond_id
            or parent is None
            or parent[2] != order
            or left not in atom_set
            or right not in atom_set
        ):
            raise ValueError("SIDECAR_LOCAL_CENTER_INTERNAL_BOND_CUT")
    derived.sort(key=lambda record: record["boundary_bond_id"].encode("utf-8"))
    frozen = _frozen_boundary_records(seed)
    if (
        len(derived) != 2
        or derived != frozen
        or len({record["boundary_bond_id"] for record in derived}) != 2
        or len({
            frozenset((
                record["warhead_attachment_atom_id"],
                record["nonwarhead_boundary_atom_id"],
            ))
            for record in derived
        }) != 2
    ):
        raise ValueError("SIDECAR_EXACT_TWO_BOUNDARY_GRAPH_MISMATCH")
    for record in derived:
        if (
            tuple(record) != _BOUNDARY_FIELDS
            or record["warhead_attachment_atom_id"] not in atom_set
            or record["nonwarhead_boundary_atom_id"] in atom_set
            or record != _boundary_record(
                attachment=record["warhead_attachment_atom_id"],
                nonwarhead=record["nonwarhead_boundary_atom_id"],
                order=record["boundary_bond_order"],
            )
            or parent_edges.get(frozenset((
                record["warhead_attachment_atom_id"],
                record["nonwarhead_boundary_atom_id"],
            )), ("", "", ""))[2] != record["boundary_bond_order"]
        ):
            raise ValueError("SIDECAR_BOUNDARY_RECORD_INVALID")
    return derived


def _notes_contain_exact_token(notes: str, token: str) -> bool:
    atom_character = r"A-Za-z0-9_'"
    return re.search(
        rf"(?<![{atom_character}]){re.escape(token)}(?![{atom_character}])",
        notes,
    ) is not None


def _notes_match(
    notes: str,
    *,
    atoms: Sequence[str],
    boundaries: Sequence[Mapping[str, str]],
) -> bool:
    return (
        _meaningful(notes)
        and all(_notes_contain_exact_token(notes, atom) for atom in atoms)
        and all(
            boundary["boundary_bond_id"] in notes
            for boundary in boundaries
        )
    )


def _committed_sources(
    payloads: Mapping[Path, bytes],
) -> tuple[
    Mapping[str, Mapping[str, Any]],
    Mapping[str, Mapping[str, Any]],
    Mapping[str, Mapping[str, str]],
    Mapping[str, Sequence[Mapping[str, str]]],
    Mapping[str, Sequence[Mapping[str, str]]],
]:
    index_rows = _csv_rows(payloads[ingestion_design.PACKAGE_INDEX])
    template_rows_raw = _csv_rows(
        payloads[ingestion_design.PACKAGE_TEMPLATES]
    )
    proposal_rows = _csv_rows(payloads[ingestion_design.PROPOSALS])
    assignment_rows = _csv_rows(payloads[ingestion_design.ASSIGNMENTS])
    parent_atom_rows = _csv_rows(payloads[ingestion_design.PARENT_ATOMS])
    parent_bond_rows = _csv_rows(payloads[ingestion_design.PARENT_BONDS])
    try:
        template_rows = [
            ingestion_design.parse_review_record_csv(row)
            for row in template_rows_raw
        ]
        package_by_sample = ingestion_design.build_package_identity_by_sample(
            index_rows, template_rows,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("SIDECAR_PACKAGE_IDENTITY_INVALID") from error
    proposals = [_typed_proposal(row) for row in proposal_rows]
    proposal_by_sample = {
        row["sample_index_row_id"]: row for row in proposals
    }
    assignment_by_sample: dict[str, Mapping[str, str]] = {}
    for row in assignment_rows:
        _validate_assignment(row)
        sample = row["sample_index_row_id"]
        if sample in assignment_by_sample:
            raise ValueError("SIDECAR_ASSIGNMENT_SAMPLE_DUPLICATE")
        assignment_by_sample[sample] = row
    if (
        len(package_by_sample) != 11
        or len(proposal_by_sample) != 11
        or len(assignment_by_sample) != 11
    ):
        raise ValueError("SIDECAR_COMMITTED_CURRENT11_COUNT_INVALID")
    atoms_by_ligand: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    bonds_by_ligand: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in parent_atom_rows:
        atoms_by_ligand[row.get("ligand_comp_id", "")].append(row)
    for row in parent_bond_rows:
        bonds_by_ligand[row.get("ligand_comp_id", "")].append(row)
    return (
        MappingProxyType(package_by_sample),
        MappingProxyType(proposal_by_sample),
        MappingProxyType(assignment_by_sample),
        MappingProxyType(atoms_by_ligand),
        MappingProxyType(bonds_by_ligand),
    )


def _validate_committed_lineage(
    *,
    seed: _FrozenProposalSeed,
    review: Mapping[str, Any],
    authority: Mapping[str, Any],
    package: Mapping[str, Any],
    proposal: Mapping[str, Any],
    assignment: Mapping[str, str],
) -> None:
    try:
        ingestion_design.validate_completed_review_package_identity(
            review,
            package_identity_by_sample={
                seed.sample_index_row_id: package,
            },
        )
        ingestion_design.validate_authority_package_lineage(
            authority,
            package_identity_by_sample={
                seed.sample_index_row_id: package,
            },
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("SIDECAR_PACKAGE_LINEAGE_INVALID") from error
    identity = (
        seed.sample_index_row_id,
        seed.pdb_id,
        seed.ligand_comp_id,
        package["warhead_type_candidate_class_id"],
        package["reaction_family_id"],
        package["warhead_rule_id"],
        package["source_proposal_record_sha256"],
        package["source_assignment_record_sha256"],
    )
    proposal_identity = (
        proposal["sample_index_row_id"],
        proposal["pdb_id"],
        proposal["ligand_comp_id"],
        proposal["warhead_type_candidate_class_id"],
        proposal["reaction_family_id"],
        proposal["warhead_rule_id"],
        proposal["proposal_record_sha256"],
        proposal["source_assignment_record_sha256"],
    )
    assignment_identity = (
        assignment["sample_index_row_id"],
        assignment["pdb_id"],
        assignment["ligand_comp_id"],
        assignment["warhead_type_candidate_class_id"],
        assignment["candidate_reaction_family_id"],
        assignment["candidate_warhead_rule_id"],
        proposal["proposal_record_sha256"],
        assignment["assignment_record_sha256"],
    )
    if (
        identity != proposal_identity
        or identity != assignment_identity
        or proposal["component_parent_graph_sha256"]
        != assignment["component_parent_graph_sha256"]
    ):
        raise ValueError("SIDECAR_PROPOSAL_ASSIGNMENT_LINEAGE_INVALID")


def _readme_bytes() -> bytes:
    return (
        "# CovaPIE Current11 multi-boundary human-review sidecar V1\n"
        "\n"
        "This workspace contains exactly five samples (000006–000010). "
        "`verified_multi_boundary_evidence.csv` contains graph-verified "
        "candidate evidence, not a human decision; do not edit that file. "
        "The frozen fields in `multi_boundary_review_worklist.csv` must not "
        "be edited.\n"
        "\n"
        "A human reviewer must explicitly fill the decision, reviewed atom "
        "set, exactly two reviewed boundary records, rationale, reviewer "
        "identity, and provenance fields. Samples 000009 and 000010 require "
        "an independent human core determination. Completing this sidecar "
        "does not create authority: the V1 quarantine authority remains "
        "valid and is not superseded. A future compiler/ingestion step has "
        "not been implemented.\n"
        "\n"
        "This workspace is not training input and creates no SMARTS, masks, "
        "or labels. The canonical masks remain exactly: `warhead_only`, "
        "`linker_plus_warhead`, `scaffold_plus_warhead`, `scaffold_only`, "
        "and `scaffold_plus_linker_plus_warhead`. Formal training still "
        "requires a feature-semantics audit. Step12D remains only a smoke "
        "legality check, not a final training-feature contract.\n"
    ).encode("utf-8")


def build_covapie_current11_multi_boundary_human_review_sidecar_v1(
    *,
    source_submission_bundle: bytes,
    source_ingestion_execution_bundle: bytes,
    repo_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic Exact3 sidecar workspace without writing it."""

    if type(source_submission_bundle) is not bytes:
        raise ValueError("source_submission_bundle must be exact bytes")
    if type(source_ingestion_execution_bundle) is not bytes:
        raise ValueError(
            "source_ingestion_execution_bundle must be exact bytes"
        )
    if type(repo_root) is not type(Path()):
        raise ValueError("repo_root must be an exact Path")
    submission_snapshot = bytes(source_submission_bundle)
    execution_snapshot = bytes(source_ingestion_execution_bundle)

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
    payloads = _context_payloads(authority_context)
    bundle = _decode_execution_bundle(
        source_ingestion_execution_bundle,
        source_submission_bundle=source_submission_bundle,
        adapter_response=adapter_response,
        submissions=submissions,
        authority_context=authority_context,
    )
    (
        package_by_sample,
        proposal_by_sample,
        assignment_by_sample,
        atoms_by_ligand,
        bonds_by_ligand,
    ) = _committed_sources(payloads)
    authorities = {
        record["sample_index_row_id"]: record
        for record in bundle["new_authority_records"]
    }
    evidence_rows: list[dict[str, str]] = []
    worklist_rows: list[dict[str, str]] = []
    evidence_shas: set[str] = set()
    for position, seed in enumerate(_FROZEN_PROPOSAL_SEEDS):
        if seed.sample_index_row_id != _TARGET_SAMPLES[position]:
            raise ValueError("SIDECAR_FROZEN_PROPOSAL_SAMPLE_ORDER_INVALID")
        sample = seed.sample_index_row_id
        review, envelope = submissions[position + 5]
        try:
            package = package_by_sample[sample]
            proposal = proposal_by_sample[sample]
            assignment = assignment_by_sample[sample]
            authority = authorities[sample]
            parent_atoms = atoms_by_ligand[seed.ligand_comp_id]
            parent_bonds = bonds_by_ligand[seed.ligand_comp_id]
        except KeyError as error:
            raise ValueError("SIDECAR_TARGET_COMMITTED_SOURCE_MISSING") from error
        _validate_committed_lineage(
            seed=seed,
            review=review,
            authority=authority,
            package=package,
            proposal=proposal,
            assignment=assignment,
        )
        if (
            proposal["ligand_comp_id"] != seed.ligand_comp_id
            or any(
                row["component_parent_graph_sha256"]
                != proposal["component_parent_graph_sha256"]
                for row in (*parent_atoms, *parent_bonds)
            )
        ):
            raise ValueError("SIDECAR_PARENT_GRAPH_LINEAGE_INVALID")
        derived_boundaries = _validate_graph_seed(
            seed,
            proposal=proposal,
            parent_atom_rows=parent_atoms,
            parent_bond_rows=parent_bonds,
        )
        frozen_boundaries = _frozen_boundary_records(seed)
        notes_match = _notes_match(
            review["review_notes"],
            atoms=seed.proposed_warhead_atom_ids,
            boundaries=frozen_boundaries,
        )
        if not notes_match:
            raise ValueError("SIDECAR_REVIEW_NOTES_GRAPH_EVIDENCE_MISMATCH")
        atoms_json = _ordered_json(list(seed.proposed_warhead_atom_ids))
        boundaries_json = _ordered_json(frozen_boundaries)
        derived_json = _ordered_json(derived_boundaries)
        evidence: dict[str, str] = {
            "multi_boundary_evidence_version": _EVIDENCE_VERSION,
            "sidecar_item_order_0based": str(position),
            "sample_index_row_id": sample,
            "pdb_id": seed.pdb_id,
            "ligand_comp_id": seed.ligand_comp_id,
            "warhead_type_candidate_class_id":
                package["warhead_type_candidate_class_id"],
            "reaction_family_id": package["reaction_family_id"],
            "warhead_rule_id": package["warhead_rule_id"],
            "source_submission_bundle_sha256":
                _sha256(source_submission_bundle),
            "source_ingestion_execution_bundle_filesystem_sha256":
                _sha256(source_ingestion_execution_bundle),
            "source_ingestion_execution_bundle_sha256":
                bundle["ingestion_execution_bundle_sha256"],
            "source_v1_quarantine_authority_record_sha256":
                authority["authority_record_sha256"],
            "source_review_record_sha256": review["review_record_sha256"],
            "source_ingestion_envelope_sha256":
                envelope["ingestion_envelope_sha256"],
            "source_proposal_record_sha256":
                proposal["proposal_record_sha256"],
            "source_assignment_record_sha256":
                assignment["assignment_record_sha256"],
            "source_candidate_set_sha256":
                package["source_candidate_set_sha256"],
            "source_review_notes_sha256":
                _sha256(review["review_notes"].encode("utf-8")),
            "covalent_ligand_atom_id":
                proposal["ligand_reactive_parent_atom_id"],
            "local_reaction_center_atom_ids_json":
                _ordered_json(proposal["local_reaction_center_atom_ids"]),
            "required_leaving_group_atom_ids_json":
                _ordered_json(proposal["required_leaving_group_atom_ids"]),
            "proposed_warhead_atom_ids_json": atoms_json,
            "proposed_boundary_records_json": boundaries_json,
            "graph_derived_boundary_records_json": derived_json,
            "graph_derived_boundary_count": "2",
            "warhead_subgraph_connected": "true",
            "contains_local_reaction_center": "true",
            "contains_required_leaving_groups": "true",
            "notes_match_parent_graph": "true",
            "exact_two_boundaries_verified": "true",
            "scope_caveat": seed.scope_caveat,
            "evidence_record_sha256": "",
        }
        evidence["evidence_record_sha256"] = _record_sha(
            evidence, _EVIDENCE_FIELDS, "evidence_record_sha256",
        )
        if evidence["evidence_record_sha256"] in evidence_shas:
            raise ValueError("SIDECAR_EVIDENCE_SHA_NOT_UNIQUE")
        evidence_shas.add(evidence["evidence_record_sha256"])
        evidence_rows.append(evidence)
        worklist_rows.append({
            "multi_boundary_review_record_version": _REVIEW_VERSION,
            "sidecar_item_order_0based": str(position),
            "sample_index_row_id": sample,
            "pdb_id": seed.pdb_id,
            "ligand_comp_id": seed.ligand_comp_id,
            "warhead_type_candidate_class_id":
                package["warhead_type_candidate_class_id"],
            "reaction_family_id": package["reaction_family_id"],
            "warhead_rule_id": package["warhead_rule_id"],
            "source_evidence_record_sha256":
                evidence["evidence_record_sha256"],
            "source_v1_quarantine_authority_record_sha256":
                authority["authority_record_sha256"],
            "source_review_record_sha256": review["review_record_sha256"],
            "proposed_warhead_atom_ids_json": atoms_json,
            "proposed_boundary_records_json": boundaries_json,
            "scope_caveat": seed.scope_caveat,
            "review_decision": "not_reviewed",
            "reviewed_warhead_atom_ids_json": "[]",
            "reviewed_boundary_records_json": "[]",
            "reviewer_id": "",
            "review_rationale": "",
            "review_notes": "",
            "reviewer_provenance_attested": "false",
            "reviewer_provenance_attestor_id": "",
            "submission_source_label": "",
            "review_completed": "false",
            "multi_boundary_review_record_sha256": "",
        })
    if (
        len(evidence_rows) != 5
        or len(worklist_rows) != 5
        or len(evidence_shas) != 5
    ):
        raise ValueError("SIDECAR_EXACT5_OUTPUT_INVALID")
    outputs = {
        "verified_multi_boundary_evidence.csv":
            _csv_bytes(_EVIDENCE_FIELDS, evidence_rows),
        "multi_boundary_review_worklist.csv":
            _csv_bytes(_WORKLIST_FIELDS, worklist_rows),
        "README.md": _readme_bytes(),
    }
    if (
        type(outputs) is not dict
        or tuple(outputs) != (
            "verified_multi_boundary_evidence.csv",
            "multi_boundary_review_worklist.csv",
            "README.md",
        )
        or any(type(key) is not str for key in outputs)
        or any(type(value) is not bytes for value in outputs.values())
        or source_submission_bundle != submission_snapshot
        or source_ingestion_execution_bundle != execution_snapshot
    ):
        raise ValueError("SIDECAR_OUTPUT_OR_INPUT_INVARIANT_INVALID")
    return outputs
