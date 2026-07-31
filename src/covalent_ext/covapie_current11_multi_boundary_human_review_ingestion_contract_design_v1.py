"""Freeze and exercise the Current11 multi-boundary ingestion contract V1.

This module is a design artifact.  Its private evaluator constructs candidate
records in memory only; it is not the future public ingestion interface.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as multi_boundary_adapter,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


__all__ = ()


FUTURE_PUBLIC_API_SIGNATURE = """def evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
    *,
    adapter_response_payload: bytes,
    source_multi_boundary_submission_bundle: bytes,
    source_v1_submission_bundle: bytes,
    source_v1_ingestion_execution_bundle: bytes,
    repo_root: Path,
    existing_multi_boundary_authority_records: Sequence[
        Mapping[str, Any]
    ] = (),
) -> dict[str, Any]:"""

MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_VERSION = (
    "covapie_current11_multi_boundary_human_review_"
    "ingestion_authority_context_v1"
)
MULTI_BOUNDARY_AUTHORITY_RECORD_VERSION = (
    "covapie_current11_reviewed_warhead_atom_set_and_"
    "exact_two_boundaries_authority_v1"
)
MULTI_BOUNDARY_INGESTION_RESULT_VERSION = (
    "covapie_current11_multi_boundary_human_review_ingestion_result_v1"
)
MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_VERSION = (
    "covapie_current11_multi_boundary_human_review_"
    "ingestion_interface_response_v1"
)

MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS = (
    "multi_boundary_ingestion_authority_context_version",
    "committed_single_boundary_authority_context_sha256",
    "source_v1_submission_bundle_sha256",
    "source_v1_ingestion_execution_bundle_filesystem_sha256",
    "source_v1_ingestion_execution_bundle_sha256",
    "source_multi_boundary_submission_bundle_filesystem_sha256",
    "source_multi_boundary_submission_bundle_sha256",
    "source_adapter_response_filesystem_sha256",
    "source_adapter_response_sha256",
    "multi_boundary_ingestion_authority_context_record_sha256",
)
MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS = (
    "multi_boundary_authority_record_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_multi_boundary_submission_bundle_sha256",
    "source_multi_boundary_submission_adapter_response_sha256",
    "source_multi_boundary_review_record_sha256",
    "source_ingestion_envelope_sha256",
    "source_evidence_record_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_v1_review_record_sha256",
    "review_decision",
    "reviewed_warhead_atom_ids",
    "reviewed_boundary_records",
    "reviewer_id",
    "review_rationale_sha256",
    "review_notes_sha256",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "authority_disposition",
    "complete_warhead_atom_set_authority_available",
    "exact_two_attachment_boundaries_authority_available",
    "sample_quarantined",
    "v1_quarantine_authority_unchanged",
    "authority_status",
    "multi_boundary_authority_record_sha256",
)
MULTI_BOUNDARY_INGESTION_RESULT_FIELDS = (
    "multi_boundary_ingestion_result_version",
    "submission_batch_id",
    "sample_index_row_id",
    "source_multi_boundary_review_record_sha256",
    "source_ingestion_envelope_sha256",
    "outcome",
    "passed",
    "blocks_batch",
    "reason",
    "review_decision",
    "review_completed",
    "authority_disposition",
    "authority_record_sha256",
    "idempotent_replay",
    "conflicting_existing_authority",
    "consumed_review_record",
    "consumed_ingestion_envelope",
    "multi_boundary_ingestion_result_sha256",
)
MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS = (
    "multi_boundary_ingestion_interface_response_version",
    "authority_context_record_sha256",
    "batch_passed",
    "ingestion_result_records",
    "new_authority_records",
    "multi_boundary_ingestion_interface_response_sha256",
)
BOUNDARY_RECORD_FIELDS = (
    "warhead_attachment_atom_id",
    "nonwarhead_boundary_atom_id",
    "boundary_bond_order",
    "boundary_bond_id",
)
INGESTION_REASON_VOCABULARY = (
    "PASSED",
    "IDEMPOTENT_REPLAY",
    "BATCH_SIZE_INVALID",
    "SUBMISSION_BATCH_ID_MISMATCH",
    "DUPLICATE_SAMPLE_IN_BATCH",
    "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
    "ADAPTER_RESPONSE_INVALID",
    "ADAPTER_RESPONSE_NOT_PASSED",
    "SOURCE_SUBMISSION_LINKAGE_MISMATCH",
    "SOURCE_V1_LINEAGE_MISMATCH",
    "INGESTION_AUTHORITY_CONTEXT_INVALID",
    "REVIEW_RECORD_DIGEST_INVALID",
    "INGESTION_ENVELOPE_DIGEST_INVALID",
    "ENVELOPE_REVIEW_LINKAGE_MISMATCH",
    "REVIEW_IDENTITY_LINKAGE_MISMATCH",
    "REVIEW_NOT_COMPLETED",
    "REVIEWER_PROVENANCE_INVALID",
    "REVIEW_DECISION_INVALID",
    "V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH",
    "PARENT_GRAPH_LINEAGE_MISMATCH",
    "REVIEWED_GRAPH_INVARIANT_INVALID",
    "EXISTING_AUTHORITY_SET_INVALID",
    "CONFLICTING_REVIEW_REINGESTION",
    "BATCH_ATOMICITY_ABORTED",
    "INGESTION_RESPONSE_INVARIANT_INVALID",
)
INGESTION_FAILURE_REASON_PRECEDENCE = (
    "adapter_response_and_source_bytes",
    "batch_identity_count_and_duplicates",
    "authority_context",
    "existing_authority_set",
    "v1_predecessor_lineage",
    "envelope_record_digest_and_identity",
    "completion_provenance_and_decision",
    "committed_graph",
    "conflict",
    "batch_atomicity",
    "response_invariant",
)
LEGACY_V1_COEXISTENCE = (
    "legacy_v1_authority_namespace=exact_one_boundary_v1",
    "new_authority_namespace=exact_two_boundaries_multi_boundary_v1",
    "legacy_v1_authority_records_are_immutable=true",
    "new_multi_boundary_ingestion_does_not_edit_or_delete_v1=true",
    "parallel_authority_namespaces_allowed=true",
    "future_unified_gold_view_precedence_not_implemented=true",
)

_TARGET_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
_V1_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_MAX_INPUT_BYTES = 1_048_576
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
_EXECUTION_VERSION = (
    "covapie_current11_real_human_review_ingestion_execution_bundle_v1"
)
_ACTIVE_DECISIONS = frozenset((
    "accept_verified_two_boundary_proposal",
    "revise_two_boundary_atom_set_and_boundaries",
))
_DECISIONS = frozenset((*_ACTIVE_DECISIONS, "quarantine"))


class _DuplicateKeyError(ValueError):
    pass


class _NonfiniteError(ValueError):
    pass


class _ContractFailure(ValueError):
    def __init__(self, reason: str, item_index: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.item_index = item_index


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
        raise ValueError("canonical JSON invalid") from error


def _digest(
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


def _strict_json_object(payload: object) -> tuple[bytes, dict[str, Any]]:
    if type(payload) is not bytes:
        raise ValueError("input must be exact bytes")
    exact_payload: bytes = payload
    if (
        not exact_payload
        or len(exact_payload) >= _MAX_INPUT_BYTES
        or exact_payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in exact_payload
        or exact_payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError("input byte contract invalid")
    try:
        text = exact_payload.decode("utf-8")
        value = json.loads(
            text,
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
        raise ValueError("input JSON invalid") from error
    if type(value) is not dict:
        raise ValueError("input JSON must be an object")
    return exact_payload, value


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as stream:
        return list(csv.DictReader(stream))


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def _meaningful_utf8_string(value: object) -> bool:
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


def _validate_multi_boundary_submission(
    payload: bytes,
) -> dict[str, Any]:
    try:
        _, bundle = multi_boundary_adapter._parse_source(payload)
        multi_boundary_adapter._validate_bundle(bundle)
        items = multi_boundary_adapter._validate_item_inventories(
            bundle["submission_items"]
        )
        multi_boundary_adapter._validate_item_types(items)
        multi_boundary_adapter._validate_item_identity(items)
        multi_boundary_adapter._validate_record_digests(items)
        multi_boundary_adapter._validate_completion_and_provenance(items)
        multi_boundary_adapter._validate_atoms_and_boundaries(items)
        multi_boundary_adapter._validate_decision_semantics(items)
    except Exception as error:
        reason = getattr(error, "reason", "")
        mapping = {
            "SUBMISSION_ITEM_COUNT_INVALID": "BATCH_SIZE_INVALID",
            "DUPLICATE_SAMPLE_IN_BUNDLE": "DUPLICATE_SAMPLE_IN_BATCH",
            "DUPLICATE_REVIEW_DIGEST_IN_BUNDLE":
                "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
            "REVIEW_RECORD_DIGEST_INVALID": "REVIEW_RECORD_DIGEST_INVALID",
            "REVIEW_COMPLETION_INVALID": "REVIEW_NOT_COMPLETED",
            "REVIEWER_PROVENANCE_INVALID": "REVIEWER_PROVENANCE_INVALID",
            "REVIEW_DECISION_INVALID": "REVIEW_DECISION_INVALID",
        }
        raise _ContractFailure(
            mapping.get(reason, "SOURCE_SUBMISSION_LINKAGE_MISMATCH")
        ) from error
    return bundle


def _validate_adapter_response(
    payload: bytes,
    *,
    source_payload: bytes,
    source_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        _, transport = _strict_json_object(payload)
        if (
            tuple(transport) != multi_boundary_adapter._RESPONSE_FIELDS
            or type(transport["adapter_result_records"]) is not list
            or type(transport["adapted_submissions"]) is not list
        ):
            raise ValueError("adapter transport Exact9 invalid")
        if transport[
            "multi_boundary_submission_adapter_response_sha256"
        ] != _digest(
            transport,
            multi_boundary_adapter._RESPONSE_FIELDS,
            "multi_boundary_submission_adapter_response_sha256",
        ):
            raise ValueError("adapter response digest invalid")
        for position, envelope in enumerate(
            transport["adapted_submissions"]
        ):
            if (
                type(envelope) is dict
                and tuple(envelope) == multi_boundary_adapter._ENVELOPE_FIELDS
                and envelope[
                    "multi_boundary_ingestion_envelope_sha256"
                ] != _digest(
                    envelope,
                    multi_boundary_adapter._ENVELOPE_FIELDS,
                    "multi_boundary_ingestion_envelope_sha256",
                )
            ):
                raise _ContractFailure(
                    "INGESTION_ENVELOPE_DIGEST_INVALID", position,
                )
        in_memory = copy.deepcopy(transport)
        in_memory["adapter_result_records"] = tuple(
            in_memory["adapter_result_records"]
        )
        in_memory["adapted_submissions"] = tuple(
            in_memory["adapted_submissions"]
        )
        multi_boundary_adapter._validate_response(in_memory)
    except _ContractFailure:
        raise
    except Exception as error:
        raise _ContractFailure("ADAPTER_RESPONSE_INVALID") from error
    if transport["adapter_passed"] is not True:
        raise _ContractFailure("ADAPTER_RESPONSE_NOT_PASSED")
    if (
        transport["source_payload_sha256"] != _sha256(source_payload)
        or transport["canonical_source_bundle_sha256"]
        != source_bundle["multi_boundary_submission_bundle_sha256"]
        or transport["submission_batch_id"]
        != source_bundle["submission_batch_id"]
    ):
        raise _ContractFailure("SOURCE_SUBMISSION_LINKAGE_MISMATCH")
    items = source_bundle["submission_items"]
    for position, (result, envelope, item) in enumerate(zip(
        transport["adapter_result_records"],
        transport["adapted_submissions"],
        items,
    )):
        if envelope["review_record_payload"] != item:
            raise _ContractFailure(
                "SOURCE_SUBMISSION_LINKAGE_MISMATCH", position,
            )
        if (
            result["source_multi_boundary_review_record_sha256"]
            != item["multi_boundary_review_record_sha256"]
            or envelope["source_multi_boundary_review_record_sha256"]
            != item["multi_boundary_review_record_sha256"]
        ):
            raise _ContractFailure(
                "ENVELOPE_REVIEW_LINKAGE_MISMATCH", position,
            )
    return transport


def _decode_v1_execution(
    payload: bytes,
    *,
    source_v1_submission_bundle: bytes,
    expected_authority_context_record_sha256: str,
) -> dict[str, Any]:
    try:
        _, parsed_v1_submission = _strict_json_object(
            source_v1_submission_bundle
        )
        expected_source_canonical_bundle_sha256 = _sha256(
            _canonical_json_bytes(parsed_v1_submission)
        )
        _, bundle = _strict_json_object(payload)
        if tuple(bundle) != _EXECUTION_FIELDS:
            raise ValueError("execution Exact12 invalid")
        if (
            bundle["ingestion_execution_bundle_version"] != _EXECUTION_VERSION
            or bundle["source_submission_bundle_sha256"]
            != _sha256(source_v1_submission_bundle)
            or _SHA256.fullmatch(
                bundle["source_canonical_bundle_sha256"]
            ) is None
            or bundle["source_canonical_bundle_sha256"]
            != expected_source_canonical_bundle_sha256
            or bundle["batch_passed"] is not True
            or bundle["authority_context_record_sha256"]
            != expected_authority_context_record_sha256
            or bundle["ingestion_interface_response_version"]
            != ingestion_interface.INTERFACE_RESPONSE_VERSION
            or _SHA256.fullmatch(
                bundle["submission_adapter_response_sha256"]
            ) is None
            or type(bundle["ingestion_result_records"]) is not list
            or type(bundle["new_authority_records"]) is not list
            or len(bundle["ingestion_result_records"]) != 11
            or len(bundle["new_authority_records"]) != 11
            or bundle["ingestion_execution_bundle_sha256"]
            != _digest(
                bundle,
                _EXECUTION_FIELDS,
                "ingestion_execution_bundle_sha256",
            )
        ):
            raise ValueError("execution lineage invalid")
        for result in bundle["ingestion_result_records"]:
            ingestion_design.validate_ingestion_result(result)
        for authority in bundle["new_authority_records"]:
            ingestion_design.validate_authority_record(authority)
        interface_response: dict[str, Any] = {
            "interface_response_version":
                bundle["ingestion_interface_response_version"],
            "authority_context_record_sha256":
                bundle["authority_context_record_sha256"],
            "batch_passed": bundle["batch_passed"],
            "ingestion_result_records":
                tuple(bundle["ingestion_result_records"]),
            "new_authority_records":
                tuple(bundle["new_authority_records"]),
            "interface_response_sha256":
                bundle["ingestion_interface_response_sha256"],
        }
        if (
            tuple(interface_response)
            != ingestion_interface.INTERFACE_RESPONSE_FIELDS
            or interface_response["interface_response_sha256"]
            != ingestion_interface.interface_response_sha256(
                interface_response
            )
        ):
            raise ValueError("execution interface response invalid")
        results = bundle["ingestion_result_records"]
        authorities = bundle["new_authority_records"]
        if (
            not _meaningful_utf8_string(bundle["submission_batch_id"])
            or any(
                result["submission_batch_id"]
                != bundle["submission_batch_id"]
                for result in results
            )
            or tuple(
                result["sample_index_row_id"] for result in results
            ) != _V1_EXPECTED_SAMPLES
            or tuple(
                authority["sample_index_row_id"]
                for authority in authorities
            ) != _V1_EXPECTED_SAMPLES
            or any(
                result["outcome"] != "passed"
                or result["passed"] is not True
                or result["blocks_batch"] is not False
                or result["reason"] != "PASSED"
                for result in results
            )
            or len({
                authority["authority_record_sha256"]
                for authority in authorities
            }) != 11
        ):
            raise ValueError("execution nested batch or sample mismatch")
        for result, authority in zip(results, authorities):
            if (
                result["authority_record_sha256"]
                != authority["authority_record_sha256"]
                or result["review_record_sha256"]
                != authority["source_review_record_sha256"]
                or result["ingestion_envelope_sha256"]
                != authority["source_ingestion_envelope_sha256"]
                or result["review_decision"] != authority["review_decision"]
                or result["authority_disposition"]
                != authority["authority_disposition"]
            ):
                raise ValueError(
                    "execution result authority linkage invalid"
                )
    except (KeyError, TypeError, ValueError) as error:
        raise _ContractFailure("SOURCE_V1_LINEAGE_MISMATCH") from error
    return bundle


def _v1_authorities(
    execution: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    authorities: dict[str, Mapping[str, Any]] = {}
    for authority in execution["new_authority_records"]:
        sample = authority["sample_index_row_id"]
        if sample in _TARGET_SAMPLES:
            if sample in authorities:
                raise _ContractFailure(
                    "V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH"
                )
            if (
                authority["authority_status"] != "quarantined"
                or authority["sample_quarantined"] is not True
                or authority[
                    "exact_one_attachment_boundary_authority_available"
                ] is not False
            ):
                raise _ContractFailure(
                    "V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH"
                )
            authorities[sample] = authority
    if tuple(authorities) != _TARGET_SAMPLES:
        raise _ContractFailure(
            "V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH"
        )
    return authorities


def _build_authority_context(
    *,
    single_boundary_context: ingestion_design.IngestionAuthorityContext,
    source_v1_submission_bundle: bytes,
    source_v1_execution_bundle: bytes,
    v1_execution: Mapping[str, Any],
    source_multi_boundary_submission_bundle: bytes,
    multi_boundary_bundle: Mapping[str, Any],
    adapter_response_payload: bytes,
    adapter_response: Mapping[str, Any],
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "multi_boundary_ingestion_authority_context_version":
            MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_VERSION,
        "committed_single_boundary_authority_context_sha256":
            single_boundary_context.context_record[
                "ingestion_authority_context_record_sha256"
            ],
        "source_v1_submission_bundle_sha256":
            _sha256(source_v1_submission_bundle),
        "source_v1_ingestion_execution_bundle_filesystem_sha256":
            _sha256(source_v1_execution_bundle),
        "source_v1_ingestion_execution_bundle_sha256":
            v1_execution["ingestion_execution_bundle_sha256"],
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
        "multi_boundary_ingestion_authority_context_record_sha256": "",
    }
    context[
        "multi_boundary_ingestion_authority_context_record_sha256"
    ] = _digest(
        context,
        MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS,
        "multi_boundary_ingestion_authority_context_record_sha256",
    )
    _validate_authority_context(context)
    return context


def _validate_authority_context(context: Mapping[str, Any]) -> None:
    if (
        type(context) is not dict
        or tuple(context)
        != MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS
        or any(type(context[field]) is not str for field in context)
        or context["multi_boundary_ingestion_authority_context_version"]
        != MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_VERSION
        or any(
            _SHA256.fullmatch(context[field]) is None
            for field in
            MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS[1:]
        )
        or context[
            "multi_boundary_ingestion_authority_context_record_sha256"
        ] != _digest(
            context,
            MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS,
            "multi_boundary_ingestion_authority_context_record_sha256",
        )
    ):
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")


def _parent_boundary_records(
    atom_ids: Sequence[str],
    parent_bonds: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, str]], set[str], dict[str, set[str]]]:
    atom_set = set(atom_ids)
    boundaries: list[dict[str, str]] = []
    internal_bond_ids: set[str] = set()
    adjacency = {atom: set() for atom in atom_ids}
    for row in parent_bonds:
        left = row["parent_ccd_atom_id_1"]
        right = row["parent_ccd_atom_id_2"]
        order = row["normalized_bond_order"]
        low, high = _utf8_sorted((left, right))
        bond_id = f"{low}|{high}|{order}"
        if left in atom_set and right in atom_set:
            adjacency[left].add(right)
            adjacency[right].add(left)
            internal_bond_ids.add(bond_id)
        elif (left in atom_set) != (right in atom_set):
            attachment = left if left in atom_set else right
            nonwarhead = right if attachment == left else left
            boundaries.append({
                "warhead_attachment_atom_id": attachment,
                "nonwarhead_boundary_atom_id": nonwarhead,
                "boundary_bond_order": order,
                "boundary_bond_id": bond_id,
            })
    boundaries.sort(
        key=lambda row: row["boundary_bond_id"].encode("utf-8")
    )
    return boundaries, internal_bond_ids, adjacency


def _validate_reviewed_graph(
    item: Mapping[str, Any],
    *,
    evidence: Mapping[str, str],
    package: Mapping[str, Any],
    proposal: Mapping[str, Any],
    assignment: Mapping[str, str],
    parent_atoms: Sequence[Mapping[str, str]],
    parent_bonds: Sequence[Mapping[str, str]],
) -> None:
    identity_fields = (
        "sample_index_row_id",
        "pdb_id",
        "ligand_comp_id",
        "warhead_type_candidate_class_id",
        "reaction_family_id",
        "warhead_rule_id",
    )
    if any(
        item[field] != evidence[field]
        or item[field] != proposal[field]
        or item[field] != package[field]
        for field in identity_fields
    ):
        raise _ContractFailure("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    if (
        evidence["source_proposal_record_sha256"]
        != proposal["proposal_record_sha256"]
        or evidence["source_assignment_record_sha256"]
        != assignment["assignment_record_sha256"]
        or proposal["source_assignment_record_sha256"]
        != assignment["assignment_record_sha256"]
        or assignment["candidate_reaction_family_id"]
        != item["reaction_family_id"]
        or assignment["candidate_warhead_rule_id"]
        != item["warhead_rule_id"]
        or proposal["component_parent_graph_sha256"]
        != assignment["component_parent_graph_sha256"]
        or any(
            row["component_parent_graph_sha256"]
            != proposal["component_parent_graph_sha256"]
            for row in (*parent_atoms, *parent_bonds)
        )
    ):
        raise _ContractFailure("PARENT_GRAPH_LINEAGE_MISMATCH")
    try:
        ingestion_design._validate_parent_graph(
            parent_atoms,
            parent_bonds,
            expected_sha=proposal["component_parent_graph_sha256"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise _ContractFailure("PARENT_GRAPH_LINEAGE_MISMATCH") from error
    if item["review_decision"] == "quarantine":
        if item["reviewed_warhead_atom_ids"] or item[
            "reviewed_boundary_records"
        ]:
            raise _ContractFailure("REVIEWED_GRAPH_INVARIANT_INVALID")
        return
    atoms = item["reviewed_warhead_atom_ids"]
    atom_set = set(atoms)
    parent_atom_ids = [row["ccd_atom_id"] for row in parent_atoms]
    parent_set = set(parent_atom_ids)
    if (
        type(atoms) is not list
        or any(type(atom) is not str for atom in atoms)
        or atoms != _utf8_sorted(atoms)
        or len(atoms) != len(atom_set)
        or not atom_set < parent_set
        or not set(proposal["local_reaction_center_atom_ids"]) <= atom_set
        or not set(proposal["required_leaving_group_atom_ids"]) <= atom_set
    ):
        raise _ContractFailure("REVIEWED_GRAPH_INVARIANT_INVALID")
    boundaries, internal_bonds, adjacency = _parent_boundary_records(
        atoms, parent_bonds,
    )
    reached: set[str] = set()
    queue = deque((atoms[0],))
    while queue:
        current = queue.popleft()
        if current in reached:
            continue
        reached.add(current)
        queue.extend(adjacency[current] - reached)
    if (
        reached != atom_set
        or not set(proposal["local_reaction_center_bond_ids"])
        <= internal_bonds
        or len(boundaries) != 2
        or boundaries != item["reviewed_boundary_records"]
    ):
        raise _ContractFailure("REVIEWED_GRAPH_INVARIANT_INVALID")
    for boundary in boundaries:
        if (
            boundary["warhead_attachment_atom_id"] not in atom_set
            or boundary["nonwarhead_boundary_atom_id"] in atom_set
        ):
            raise _ContractFailure("REVIEWED_GRAPH_INVARIANT_INVALID")
    if item["review_decision"] == "accept_verified_two_boundary_proposal":
        if (
            atoms != item["proposed_warhead_atom_ids"]
            or boundaries != item["proposed_boundary_records"]
        ):
            raise _ContractFailure("REVIEWED_GRAPH_INVARIANT_INVALID")
    elif (
        atoms == item["proposed_warhead_atom_ids"]
        and boundaries == item["proposed_boundary_records"]
    ):
        raise _ContractFailure("REVIEWED_GRAPH_INVARIANT_INVALID")


def _candidate_authority(
    item: Mapping[str, Any],
    envelope: Mapping[str, Any],
    *,
    source_bundle_sha256: str,
    adapter_response_sha256: str,
    evidence_sha256: str,
    v1_authority: Mapping[str, Any],
) -> dict[str, Any]:
    active = item["review_decision"] in _ACTIVE_DECISIONS
    authority: dict[str, Any] = {
        "multi_boundary_authority_record_version":
            MULTI_BOUNDARY_AUTHORITY_RECORD_VERSION,
        "sample_index_row_id": item["sample_index_row_id"],
        "pdb_id": item["pdb_id"],
        "ligand_comp_id": item["ligand_comp_id"],
        "warhead_type_candidate_class_id":
            item["warhead_type_candidate_class_id"],
        "reaction_family_id": item["reaction_family_id"],
        "warhead_rule_id": item["warhead_rule_id"],
        "source_multi_boundary_submission_bundle_sha256":
            source_bundle_sha256,
        "source_multi_boundary_submission_adapter_response_sha256":
            adapter_response_sha256,
        "source_multi_boundary_review_record_sha256":
            item["multi_boundary_review_record_sha256"],
        "source_ingestion_envelope_sha256":
            envelope["multi_boundary_ingestion_envelope_sha256"],
        "source_evidence_record_sha256": evidence_sha256,
        "source_v1_quarantine_authority_record_sha256":
            v1_authority["authority_record_sha256"],
        "source_v1_review_record_sha256":
            v1_authority["source_review_record_sha256"],
        "review_decision": item["review_decision"],
        "reviewed_warhead_atom_ids":
            copy.deepcopy(item["reviewed_warhead_atom_ids"]),
        "reviewed_boundary_records":
            copy.deepcopy(item["reviewed_boundary_records"]),
        "reviewer_id": item["reviewer_id"],
        "review_rationale_sha256":
            _sha256(item["review_rationale"].encode("utf-8")),
        "review_notes_sha256":
            _sha256(item["review_notes"].encode("utf-8")),
        "reviewer_provenance_attestor_id":
            item["reviewer_provenance_attestor_id"],
        "submission_source_label": item["submission_source_label"],
        "authority_disposition":
            "reviewed_multi_boundary_authority_materialized"
            if active
            else "reviewed_multi_boundary_quarantine_recorded",
        "complete_warhead_atom_set_authority_available": active,
        "exact_two_attachment_boundaries_authority_available": active,
        "sample_quarantined": not active,
        "v1_quarantine_authority_unchanged": True,
        "authority_status": "active" if active else "quarantined",
        "multi_boundary_authority_record_sha256": "",
    }
    authority["multi_boundary_authority_record_sha256"] = _digest(
        authority,
        MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS,
        "multi_boundary_authority_record_sha256",
    )
    _validate_authority_record(authority)
    return authority


def _validate_authority_record(record: Mapping[str, Any]) -> None:
    bool_fields = {
        "complete_warhead_atom_set_authority_available",
        "exact_two_attachment_boundaries_authority_available",
        "sample_quarantined",
        "v1_quarantine_authority_unchanged",
    }
    list_fields = {"reviewed_warhead_atom_ids", "reviewed_boundary_records"}
    sha_fields = {
        "source_multi_boundary_submission_bundle_sha256",
        "source_multi_boundary_submission_adapter_response_sha256",
        "source_multi_boundary_review_record_sha256",
        "source_ingestion_envelope_sha256",
        "source_evidence_record_sha256",
        "source_v1_quarantine_authority_record_sha256",
        "source_v1_review_record_sha256",
        "review_rationale_sha256",
        "review_notes_sha256",
        "multi_boundary_authority_record_sha256",
    }
    meaningful_fields = {
        "sample_index_row_id",
        "pdb_id",
        "ligand_comp_id",
        "warhead_type_candidate_class_id",
        "reaction_family_id",
        "warhead_rule_id",
        "review_decision",
        "reviewer_id",
        "reviewer_provenance_attestor_id",
        "submission_source_label",
        "authority_disposition",
        "authority_status",
    }
    if (
        type(record) is not dict
        or tuple(record) != MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        or any(type(record[field]) is not bool for field in bool_fields)
        or any(type(record[field]) is not list for field in list_fields)
        or any(
            type(record[field]) is not str
            for field in MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
            if field not in bool_fields and field not in list_fields
        )
        or record["multi_boundary_authority_record_version"]
        != MULTI_BOUNDARY_AUTHORITY_RECORD_VERSION
        or record["review_decision"] not in _DECISIONS
        or any(
            _SHA256.fullmatch(record[field]) is None
            for field in sha_fields
        )
        or any(
            not _meaningful_utf8_string(record[field])
            for field in meaningful_fields
        )
        or record["v1_quarantine_authority_unchanged"] is not True
        or record["multi_boundary_authority_record_sha256"]
        != _digest(
            record,
            MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS,
            "multi_boundary_authority_record_sha256",
        )
    ):
        raise ValueError("authority record invalid")
    atoms = record["reviewed_warhead_atom_ids"]
    boundaries = record["reviewed_boundary_records"]
    if (
        any(
            type(atom) is not str or not _meaningful_utf8_string(atom)
            for atom in atoms
        )
        or atoms != _utf8_sorted(atoms)
        or len(atoms) != len(set(atoms))
    ):
        raise ValueError("authority atom contract invalid")
    boundary_ids: set[str] = set()
    endpoint_pairs: set[frozenset[str]] = set()
    for boundary in boundaries:
        if (
            type(boundary) is not dict
            or tuple(boundary) != BOUNDARY_RECORD_FIELDS
            or any(
                type(boundary[field]) is not str
                or not _meaningful_utf8_string(boundary[field])
                for field in BOUNDARY_RECORD_FIELDS
            )
        ):
            raise ValueError("authority boundary contract invalid")
        attachment = boundary["warhead_attachment_atom_id"]
        nonwarhead = boundary["nonwarhead_boundary_atom_id"]
        order = boundary["boundary_bond_order"]
        identifier = boundary["boundary_bond_id"]
        low, high = _utf8_sorted((attachment, nonwarhead))
        endpoints = frozenset((attachment, nonwarhead))
        if (
            attachment == nonwarhead
            or order not in ingestion_design.PARENT_NORMALIZED_BOND_ORDERS
            or identifier != f"{low}|{high}|{order}"
            or identifier in boundary_ids
            or endpoints in endpoint_pairs
        ):
            raise ValueError("authority boundary contract invalid")
        boundary_ids.add(identifier)
        endpoint_pairs.add(endpoints)
    if boundaries != sorted(
        boundaries,
        key=lambda boundary:
            boundary["boundary_bond_id"].encode("utf-8"),
    ):
        raise ValueError("authority boundary order invalid")
    active = record["review_decision"] in _ACTIVE_DECISIONS
    expected = (
        "reviewed_multi_boundary_authority_materialized"
        if active
        else "reviewed_multi_boundary_quarantine_recorded",
        active,
        active,
        not active,
        "active" if active else "quarantined",
    )
    observed = (
        record["authority_disposition"],
        record["complete_warhead_atom_set_authority_available"],
        record["exact_two_attachment_boundaries_authority_available"],
        record["sample_quarantined"],
        record["authority_status"],
    )
    atom_set = set(atoms)
    if (
        observed != expected
        or (
            active
            and any(
                boundary["warhead_attachment_atom_id"] not in atom_set
                or boundary["nonwarhead_boundary_atom_id"] in atom_set
                for boundary in boundaries
            )
        )
        or (
            active
            and (
                not record["reviewed_warhead_atom_ids"]
                or len(record["reviewed_boundary_records"]) != 2
            )
        )
        or (
            not active
            and (
                record["reviewed_warhead_atom_ids"]
                or record["reviewed_boundary_records"]
            )
        )
    ):
        raise ValueError("authority decision effect invalid")


def _validated_existing_authorities(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(
        records, (str, bytes, bytearray)
    ):
        raise _ContractFailure("EXISTING_AUTHORITY_SET_INVALID")
    by_sample: dict[str, Mapping[str, Any]] = {}
    digests: set[str] = set()
    try:
        for source in records:
            record = copy.deepcopy(source)
            _validate_authority_record(record)
            sample = record["sample_index_row_id"]
            digest = record["multi_boundary_authority_record_sha256"]
            if sample in by_sample or digest in digests:
                raise ValueError("existing authority duplicate")
            by_sample[sample] = record
            digests.add(digest)
    except (KeyError, TypeError, ValueError) as error:
        raise _ContractFailure("EXISTING_AUTHORITY_SET_INVALID") from error
    return by_sample


def _result_record(
    *,
    submission_batch_id: str,
    sample_index_row_id: str,
    review_sha: str,
    envelope_sha: str,
    reason: str,
    review_decision: str,
    authority_disposition: str = "",
    authority_sha: str = "",
    idempotent_replay: bool = False,
    conflicting: bool = False,
) -> dict[str, Any]:
    passed = reason in {"PASSED", "IDEMPOTENT_REPLAY"}
    result: dict[str, Any] = {
        "multi_boundary_ingestion_result_version":
            MULTI_BOUNDARY_INGESTION_RESULT_VERSION,
        "submission_batch_id": submission_batch_id,
        "sample_index_row_id": sample_index_row_id,
        "source_multi_boundary_review_record_sha256": review_sha,
        "source_ingestion_envelope_sha256": envelope_sha,
        "outcome": "passed" if passed else "blocked",
        "passed": passed,
        "blocks_batch": not passed,
        "reason": reason,
        "review_decision": review_decision,
        "review_completed": True,
        "authority_disposition":
            authority_disposition if passed else "",
        "authority_record_sha256": authority_sha if passed else "",
        "idempotent_replay": idempotent_replay,
        "conflicting_existing_authority": conflicting,
        "consumed_review_record": passed,
        "consumed_ingestion_envelope": passed,
        "multi_boundary_ingestion_result_sha256": "",
    }
    result["multi_boundary_ingestion_result_sha256"] = _digest(
        result,
        MULTI_BOUNDARY_INGESTION_RESULT_FIELDS,
        "multi_boundary_ingestion_result_sha256",
    )
    _validate_result_record(result)
    return result


def _validate_result_record(record: Mapping[str, Any]) -> None:
    bool_fields = {
        "passed",
        "blocks_batch",
        "review_completed",
        "idempotent_replay",
        "conflicting_existing_authority",
        "consumed_review_record",
        "consumed_ingestion_envelope",
    }
    if (
        type(record) is not dict
        or tuple(record) != MULTI_BOUNDARY_INGESTION_RESULT_FIELDS
        or any(type(record[field]) is not bool for field in bool_fields)
        or any(
            type(record[field]) is not str
            for field in MULTI_BOUNDARY_INGESTION_RESULT_FIELDS
            if field not in bool_fields
        )
        or record["multi_boundary_ingestion_result_version"]
        != MULTI_BOUNDARY_INGESTION_RESULT_VERSION
        or record["reason"] not in INGESTION_REASON_VOCABULARY
        or record["multi_boundary_ingestion_result_sha256"]
        != _digest(
            record,
            MULTI_BOUNDARY_INGESTION_RESULT_FIELDS,
            "multi_boundary_ingestion_result_sha256",
        )
    ):
        raise ValueError("ingestion result invalid")
    passed = record["reason"] in {"PASSED", "IDEMPOTENT_REPLAY"}
    if (
        record["passed"] is not passed
        or record["blocks_batch"] is passed
        or record["outcome"] != ("passed" if passed else "blocked")
        or record["idempotent_replay"]
        is not (record["reason"] == "IDEMPOTENT_REPLAY")
        or record["conflicting_existing_authority"]
        is not (record["reason"] == "CONFLICTING_REVIEW_REINGESTION")
    ):
        raise ValueError("ingestion result semantics invalid")


def _interface_response(
    *,
    context_sha: str,
    batch_passed: bool,
    results: Sequence[Mapping[str, Any]],
    authorities: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "multi_boundary_ingestion_interface_response_version":
            MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_VERSION,
        "authority_context_record_sha256": context_sha,
        "batch_passed": batch_passed,
        "ingestion_result_records": tuple(
            copy.deepcopy(tuple(results))
        ),
        "new_authority_records": tuple(
            copy.deepcopy(tuple(authorities))
        ),
        "multi_boundary_ingestion_interface_response_sha256": "",
    }
    response[
        "multi_boundary_ingestion_interface_response_sha256"
    ] = _digest(
        response,
        MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
        "multi_boundary_ingestion_interface_response_sha256",
    )
    _validate_interface_response(response)
    return response


def _validate_interface_response(response: Mapping[str, Any]) -> None:
    if (
        type(response) is not dict
        or tuple(response)
        != MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS
        or response[
            "multi_boundary_ingestion_interface_response_version"
        ] != MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_VERSION
        or type(response["authority_context_record_sha256"]) is not str
        or type(response["batch_passed"]) is not bool
        or type(response["ingestion_result_records"]) is not tuple
        or type(response["new_authority_records"]) is not tuple
        or response[
            "multi_boundary_ingestion_interface_response_sha256"
        ] != _digest(
            response,
            MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
            "multi_boundary_ingestion_interface_response_sha256",
        )
    ):
        raise ValueError("interface response invalid")
    for result in response["ingestion_result_records"]:
        _validate_result_record(result)
    for authority in response["new_authority_records"]:
        _validate_authority_record(authority)
    if response["batch_passed"]:
        if (
            len(response["ingestion_result_records"]) != 5
            or any(
                result["passed"] is not True
                for result in response["ingestion_result_records"]
            )
        ):
            raise ValueError("passed response invalid")
    elif response["new_authority_records"]:
        raise ValueError("failed response materialized authority")


def _empty_failure_response(reason: str) -> dict[str, Any]:
    if reason not in INGESTION_REASON_VOCABULARY:
        reason = "INGESTION_RESPONSE_INVARIANT_INVALID"
    return _interface_response(
        context_sha="",
        batch_passed=False,
        results=(),
        authorities=(),
    )


def _identity_bearing_failure_response(
    *,
    reason: str,
    source_multi_boundary_submission_bundle: bytes,
    adapter_response_payload: bytes,
    item_index: int | None,
) -> dict[str, Any]:
    try:
        _, bundle = _strict_json_object(
            source_multi_boundary_submission_bundle
        )
        _, response = _strict_json_object(adapter_response_payload)
        items = bundle["submission_items"]
        envelopes = response["adapted_submissions"]
        if (
            type(items) is not list
            or type(envelopes) is not list
            or len(items) != 5
            or len(envelopes) != 5
            or any(
                type(item) is not dict
                or type(envelope) is not dict
                or type(item.get("multi_boundary_review_record_sha256"))
                is not str
                or type(item.get("review_decision")) is not str
                or type(envelope.get("submission_batch_id")) is not str
                or type(envelope.get("sample_index_row_id")) is not str
                or type(envelope.get(
                    "multi_boundary_ingestion_envelope_sha256"
                )) is not str
                for item, envelope in zip(items, envelopes)
            )
        ):
            raise ValueError("stable batch identity unavailable")
        return _interface_response(
            context_sha="",
            batch_passed=False,
            results=_atomic_failure_results(
                items=items,
                envelopes=envelopes,
                failure_index=item_index if item_index is not None else 0,
                failure_reason=reason,
            ),
            authorities=(),
        )
    except (KeyError, TypeError, ValueError):
        return _empty_failure_response(reason)


def _atomic_failure_results(
    *,
    items: Sequence[Mapping[str, Any]],
    envelopes: Sequence[Mapping[str, Any]],
    failure_index: int,
    failure_reason: str,
) -> tuple[dict[str, Any], ...]:
    results = []
    for position, (item, envelope) in enumerate(zip(items, envelopes)):
        results.append(_result_record(
            submission_batch_id=envelope["submission_batch_id"],
            sample_index_row_id=item["sample_index_row_id"],
            review_sha=item["multi_boundary_review_record_sha256"],
            envelope_sha=envelope[
                "multi_boundary_ingestion_envelope_sha256"
            ],
            reason=(
                failure_reason
                if position == failure_index
                else "BATCH_ATOMICITY_ABORTED"
            ),
            review_decision=item["review_decision"],
            conflicting=(
                position == failure_index
                and failure_reason == "CONFLICTING_REVIEW_REINGESTION"
            ),
        ))
    return tuple(results)


def _reference_evaluate_covapie_current11_multi_boundary_ingestion_v1(
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
    """Exercise the frozen contract without exposing or persisting ingestion."""

    byte_inputs = (
        adapter_response_payload,
        source_multi_boundary_submission_bundle,
        source_v1_submission_bundle,
        source_v1_ingestion_execution_bundle,
    )
    if any(type(value) is not bytes for value in byte_inputs):
        return _empty_failure_response("ADAPTER_RESPONSE_INVALID")
    if type(repo_root) is not type(Path()):
        return _empty_failure_response(
            "INGESTION_AUTHORITY_CONTEXT_INVALID"
        )
    snapshots = tuple(bytes(value) for value in byte_inputs)
    try:
        existing_snapshot = copy.deepcopy(
            existing_multi_boundary_authority_records
        )
    except (TypeError, ValueError, RecursionError):
        return _identity_bearing_failure_response(
            reason="EXISTING_AUTHORITY_SET_INVALID",
            source_multi_boundary_submission_bundle=
                source_multi_boundary_submission_bundle,
            adapter_response_payload=adapter_response_payload,
            item_index=0,
        )

    try:
        multi_bundle = _validate_multi_boundary_submission(
            source_multi_boundary_submission_bundle
        )
        adapter_response = _validate_adapter_response(
            adapter_response_payload,
            source_payload=source_multi_boundary_submission_bundle,
            source_bundle=multi_bundle,
        )
    except _ContractFailure as error:
        return _identity_bearing_failure_response(
            reason=error.reason,
            source_multi_boundary_submission_bundle=
                source_multi_boundary_submission_bundle,
            adapter_response_payload=adapter_response_payload,
            item_index=error.item_index,
        )

    items = multi_bundle["submission_items"]
    envelopes = adapter_response["adapted_submissions"]
    try:
        if len(items) != 5 or len(envelopes) != 5:
            raise _ContractFailure("BATCH_SIZE_INVALID")
        if any(
            envelope["submission_batch_id"] != multi_bundle[
                "submission_batch_id"
            ]
            for envelope in envelopes
        ):
            raise _ContractFailure("SUBMISSION_BATCH_ID_MISMATCH")
        samples = [item["sample_index_row_id"] for item in items]
        review_shas = [
            item["multi_boundary_review_record_sha256"] for item in items
        ]
        if len(set(samples)) != 5:
            raise _ContractFailure("DUPLICATE_SAMPLE_IN_BATCH")
        if len(set(review_shas)) != 5:
            raise _ContractFailure(
                "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH"
            )

        try:
            sidecar_outputs = (
                sidecar
                .build_covapie_current11_multi_boundary_human_review_sidecar_v1(
                    source_submission_bundle=source_v1_submission_bundle,
                    source_ingestion_execution_bundle=
                        source_v1_ingestion_execution_bundle,
                    repo_root=repo_root,
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise _ContractFailure(
                "SOURCE_V1_LINEAGE_MISMATCH"
            ) from error
        single_context = (
            ingestion_interface
            .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
                repo_root
            )
        )
        ingestion_design.validate_ingestion_authority_context(single_context)
        expected_single_boundary_authority_context_sha256 = (
            single_context.context_record[
                "ingestion_authority_context_record_sha256"
            ]
        )
        v1_execution = _decode_v1_execution(
            source_v1_ingestion_execution_bundle,
            source_v1_submission_bundle=source_v1_submission_bundle,
            expected_authority_context_record_sha256=
                expected_single_boundary_authority_context_sha256,
        )
        if (
            multi_bundle["source_submission_bundle_sha256"]
            != _sha256(source_v1_submission_bundle)
            or multi_bundle[
                "source_ingestion_execution_bundle_filesystem_sha256"
            ] != _sha256(source_v1_ingestion_execution_bundle)
            or multi_bundle["source_ingestion_execution_bundle_sha256"]
            != v1_execution["ingestion_execution_bundle_sha256"]
        ):
            raise _ContractFailure("SOURCE_V1_LINEAGE_MISMATCH")
        v1_authority_by_sample = _v1_authorities(v1_execution)

        context_payloads = sidecar._context_payloads(single_context)
        (
            package_by_sample,
            proposal_by_sample,
            assignment_by_sample,
            atoms_by_ligand,
            bonds_by_ligand,
        ) = sidecar._committed_sources(context_payloads)
        authority_context = _build_authority_context(
            single_boundary_context=single_context,
            source_v1_submission_bundle=source_v1_submission_bundle,
            source_v1_execution_bundle=
                source_v1_ingestion_execution_bundle,
            v1_execution=v1_execution,
            source_multi_boundary_submission_bundle=
                source_multi_boundary_submission_bundle,
            multi_boundary_bundle=multi_bundle,
            adapter_response_payload=adapter_response_payload,
            adapter_response=adapter_response,
        )
        evidence_rows = _csv_rows(
            sidecar_outputs["verified_multi_boundary_evidence.csv"]
        )
        if (
            len(evidence_rows) != 5
            or tuple(
                row["sample_index_row_id"] for row in evidence_rows
            ) != _TARGET_SAMPLES
        ):
            raise _ContractFailure("SOURCE_V1_LINEAGE_MISMATCH")
        evidence_by_sample = {
            row["sample_index_row_id"]: row for row in evidence_rows
        }
        existing_by_sample = _validated_existing_authorities(
            existing_multi_boundary_authority_records
        )
    except _ContractFailure as error:
        failure_index = error.item_index or 0
        return _interface_response(
            context_sha="",
            batch_passed=False,
            results=_atomic_failure_results(
                items=items,
                envelopes=envelopes,
                failure_index=failure_index,
                failure_reason=error.reason,
            ),
            authorities=(),
        )
    except (KeyError, TypeError, ValueError):
        return _interface_response(
            context_sha="",
            batch_passed=False,
            results=_atomic_failure_results(
                items=items,
                envelopes=envelopes,
                failure_index=0,
                failure_reason="INGESTION_AUTHORITY_CONTEXT_INVALID",
            ),
            authorities=(),
        )

    candidates: list[dict[str, Any]] = []
    result_modes: list[str] = []
    first_failure: tuple[int, str] | None = None
    for position, (item, envelope) in enumerate(zip(items, envelopes)):
        sample = item["sample_index_row_id"]
        try:
            if item != envelope["review_record_payload"]:
                raise _ContractFailure(
                    "ENVELOPE_REVIEW_LINKAGE_MISMATCH", position
                )
            if (
                item["review_completed"] is not True
                or item["review_decision"] not in _DECISIONS
            ):
                raise _ContractFailure("REVIEW_NOT_COMPLETED", position)
            if (
                item["reviewer_provenance_attested"] is not True
                or envelope["reviewer_provenance_attested"] is not True
                or item["reviewer_provenance_attestor_id"]
                != envelope["reviewer_provenance_attestor_id"]
                or item["submission_source_label"]
                != envelope["submission_source_label"]
            ):
                raise _ContractFailure(
                    "REVIEWER_PROVENANCE_INVALID", position
                )
            evidence = evidence_by_sample[sample]
            v1_authority = v1_authority_by_sample[sample]
            if (
                item["source_v1_quarantine_authority_record_sha256"]
                != v1_authority["authority_record_sha256"]
                or item["source_review_record_sha256"]
                != v1_authority["source_review_record_sha256"]
            ):
                raise _ContractFailure(
                    "V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH",
                    position,
                )
            if (
                item["source_evidence_record_sha256"]
                != evidence["evidence_record_sha256"]
                or item["source_v1_quarantine_authority_record_sha256"]
                != evidence[
                    "source_v1_quarantine_authority_record_sha256"
                ]
                or item["source_review_record_sha256"]
                != evidence["source_review_record_sha256"]
            ):
                raise _ContractFailure(
                    "REVIEW_IDENTITY_LINKAGE_MISMATCH", position
                )
            proposal = proposal_by_sample[sample]
            assignment = assignment_by_sample[sample]
            package = package_by_sample[sample]
            _validate_reviewed_graph(
                item,
                evidence=evidence,
                package=package,
                proposal=proposal,
                assignment=assignment,
                parent_atoms=atoms_by_ligand[item["ligand_comp_id"]],
                parent_bonds=bonds_by_ligand[item["ligand_comp_id"]],
            )
            candidate = _candidate_authority(
                item,
                envelope,
                source_bundle_sha256=multi_bundle[
                    "multi_boundary_submission_bundle_sha256"
                ],
                adapter_response_sha256=adapter_response[
                    "multi_boundary_submission_adapter_response_sha256"
                ],
                evidence_sha256=evidence["evidence_record_sha256"],
                v1_authority=v1_authority,
            )
            existing = existing_by_sample.get(sample)
            if existing is None:
                result_modes.append("PASSED")
                candidates.append(candidate)
            elif (
                existing["multi_boundary_authority_record_sha256"]
                == candidate["multi_boundary_authority_record_sha256"]
            ):
                result_modes.append("IDEMPOTENT_REPLAY")
                candidates.append(candidate)
            else:
                raise _ContractFailure(
                    "CONFLICTING_REVIEW_REINGESTION", position
                )
        except _ContractFailure as error:
            if first_failure is None:
                first_failure = (
                    error.item_index
                    if error.item_index is not None
                    else position,
                    error.reason,
                )
            result_modes.append("BATCH_ATOMICITY_ABORTED")
        except (KeyError, TypeError, ValueError):
            if first_failure is None:
                first_failure = (
                    position,
                    "REVIEWED_GRAPH_INVARIANT_INVALID",
                )
            result_modes.append("BATCH_ATOMICITY_ABORTED")

    context_sha = authority_context[
        "multi_boundary_ingestion_authority_context_record_sha256"
    ]
    if first_failure is not None:
        failure_index, failure_reason = first_failure
        return _interface_response(
            context_sha=context_sha,
            batch_passed=False,
            results=_atomic_failure_results(
                items=items,
                envelopes=envelopes,
                failure_index=failure_index,
                failure_reason=failure_reason,
            ),
            authorities=(),
        )

    results: list[dict[str, Any]] = []
    new_authorities: list[dict[str, Any]] = []
    for item, envelope, candidate, mode in zip(
        items, envelopes, candidates, result_modes
    ):
        replay = mode == "IDEMPOTENT_REPLAY"
        results.append(_result_record(
            submission_batch_id=multi_bundle["submission_batch_id"],
            sample_index_row_id=item["sample_index_row_id"],
            review_sha=item["multi_boundary_review_record_sha256"],
            envelope_sha=envelope[
                "multi_boundary_ingestion_envelope_sha256"
            ],
            reason=mode,
            review_decision=item["review_decision"],
            authority_disposition=candidate["authority_disposition"],
            authority_sha=candidate[
                "multi_boundary_authority_record_sha256"
            ],
            idempotent_replay=replay,
        ))
        if not replay:
            new_authorities.append(candidate)
    response = _interface_response(
        context_sha=context_sha,
        batch_passed=True,
        results=results,
        authorities=new_authorities,
    )
    if (
        byte_inputs != snapshots
        or existing_multi_boundary_authority_records != existing_snapshot
    ):
        return _interface_response(
            context_sha=context_sha,
            batch_passed=False,
            results=_atomic_failure_results(
                items=items,
                envelopes=envelopes,
                failure_index=0,
                failure_reason="INGESTION_RESPONSE_INVARIANT_INVALID",
            ),
            authorities=(),
        )
    return response
