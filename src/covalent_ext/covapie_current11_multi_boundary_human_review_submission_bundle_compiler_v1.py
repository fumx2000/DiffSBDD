"""Compile a completed Current11 multi-boundary review workspace in memory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


__all__ = (
    "compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1",
)


_BUNDLE_VERSION = (
    "covapie_current11_multi_boundary_human_review_submission_bundle_v1"
)
_TARGET_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
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
_FROZEN_WORKLIST_FIELDS = _WORKLIST_FIELDS[:14]
_BOUNDARY_FIELDS = (
    "warhead_attachment_atom_id",
    "nonwarhead_boundary_atom_id",
    "boundary_bond_order",
    "boundary_bond_id",
)
_COMPILED_RECORD_FIELDS = (
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
_DECISIONS = frozenset((
    "accept_verified_two_boundary_proposal",
    "revise_two_boundary_atom_set_and_boundaries",
    "quarantine",
))
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
        raise ValueError("MULTI_BOUNDARY_CANONICAL_JSON_INVALID") from error


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
        raise ValueError("MULTI_BOUNDARY_OUTPUT_JSON_INVALID") from error


def _meaningful(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and "\x00" not in value
    )


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    try:
        return sorted(values, key=lambda value: value.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ValueError("MULTI_BOUNDARY_UTF8_TOKEN_INVALID") from error


def _record_sha(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    if type(record) is not dict or tuple(record) != tuple(fields):
        raise ValueError("MULTI_BOUNDARY_RECORD_FIELD_INVENTORY_INVALID")
    return _sha256(_canonical_json_bytes({
        field: record[field] for field in fields if field != digest_field
    }))


def _csv_rows(
    payload: bytes,
    *,
    fields: Sequence[str],
    label: str,
) -> list[dict[str, str]]:
    if (
        not payload
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
    ):
        raise ValueError(f"{label}_BYTE_CONTRACT_INVALID")
    try:
        with io.StringIO(payload.decode("utf-8"), newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if tuple(reader.fieldnames or ()) != tuple(fields):
                raise ValueError(f"{label}_FIELD_INVENTORY_INVALID")
            rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(f"{label}_CSV_INVALID") from error
    if any(
        type(row) is not dict
        or tuple(row) != tuple(fields)
        or None in row
        or any(type(row[field]) is not str for field in fields)
        for row in rows
    ):
        raise ValueError(f"{label}_ROW_INVALID")
    return rows


def _exact_list_str(cell: str, *, field: str) -> list[str]:
    try:
        value = json.loads(cell)
    except (
        TypeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError(f"MULTI_BOUNDARY_LIST_INVALID:{field}") from error
    if (
        type(value) is not list
        or any(type(item) is not str or not _meaningful(item) for item in value)
    ):
        raise ValueError(f"MULTI_BOUNDARY_LIST_INVALID:{field}")
    return value


def _atom_ids(cell: str, *, field: str, allow_empty: bool) -> list[str]:
    atoms = _exact_list_str(cell, field=field)
    if (
        (not allow_empty and not atoms)
        or len(atoms) != len(set(atoms))
        or atoms != _utf8_sorted(atoms)
    ):
        raise ValueError(f"MULTI_BOUNDARY_ATOM_SET_INVALID:{field}")
    return atoms


def _boundary_records(
    cell: str,
    *,
    field: str,
    expected_count: int,
) -> list[dict[str, str]]:
    try:
        value = json.loads(cell)
    except (
        TypeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError(f"MULTI_BOUNDARY_BOUNDARIES_INVALID:{field}") from error
    if (
        type(value) is not list
        or len(value) != expected_count
        or any(
            type(record) is not dict
            or tuple(record) != _BOUNDARY_FIELDS
            or any(
                type(record[name]) is not str
                or not _meaningful(record[name])
                for name in _BOUNDARY_FIELDS
            )
            for record in value
        )
    ):
        raise ValueError(f"MULTI_BOUNDARY_BOUNDARIES_INVALID:{field}")
    records: list[dict[str, str]] = value
    try:
        sorted_records = sorted(
            records,
            key=lambda record: record["boundary_bond_id"].encode("utf-8"),
        )
    except UnicodeEncodeError as error:
        raise ValueError("MULTI_BOUNDARY_UTF8_TOKEN_INVALID") from error
    if records != sorted_records:
        raise ValueError(f"MULTI_BOUNDARY_BOUNDARY_ORDER_INVALID:{field}")
    ids: set[str] = set()
    endpoints: set[frozenset[str]] = set()
    for record in records:
        attachment = record["warhead_attachment_atom_id"]
        nonwarhead = record["nonwarhead_boundary_atom_id"]
        order = record["boundary_bond_order"]
        low, high = _utf8_sorted((attachment, nonwarhead))
        endpoint = frozenset((attachment, nonwarhead))
        if (
            attachment == nonwarhead
            or len(endpoint) != 2
            or order not in ingestion_design.PARENT_NORMALIZED_BOND_ORDERS
            or record["boundary_bond_id"] != f"{low}|{high}|{order}"
            or record["boundary_bond_id"] in ids
            or endpoint in endpoints
        ):
            raise ValueError(f"MULTI_BOUNDARY_BOUNDARY_RECORD_INVALID:{field}")
        ids.add(record["boundary_bond_id"])
        endpoints.add(endpoint)
    return records


def _execution_internal_sha(
    payload: bytes,
    *,
    source_submission_sha: str,
) -> str:
    try:
        bundle = json.loads(payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("MULTI_BOUNDARY_EXECUTION_JSON_INVALID") from error
    if (
        type(bundle) is not dict
        or tuple(bundle) != _EXECUTION_FIELDS
        or type(bundle["ingestion_execution_bundle_sha256"]) is not str
        or bundle["source_submission_bundle_sha256"] != source_submission_sha
        or bundle["ingestion_execution_bundle_sha256"]
        != _record_sha(
            bundle,
            _EXECUTION_FIELDS,
            "ingestion_execution_bundle_sha256",
        )
        or _SHA256.fullmatch(
            bundle["ingestion_execution_bundle_sha256"]
        ) is None
    ):
        raise ValueError("MULTI_BOUNDARY_EXECUTION_LINEAGE_INVALID")
    for result in bundle["ingestion_result_records"]:
        try:
            ingestion_design.validate_ingestion_result(result)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "MULTI_BOUNDARY_EXECUTION_RESULT_INVALID"
            ) from error
    for authority in bundle["new_authority_records"]:
        try:
            ingestion_design.validate_authority_record(authority)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "MULTI_BOUNDARY_EXECUTION_AUTHORITY_INVALID"
            ) from error
    return bundle["ingestion_execution_bundle_sha256"]


def _validate_evidence(
    rows: Sequence[dict[str, str]],
    *,
    source_submission_sha: str,
    source_execution_filesystem_sha: str,
    source_execution_internal_sha: str,
) -> dict[str, dict[str, Any]]:
    if (
        len(rows) != 5
        or tuple(row["sample_index_row_id"] for row in rows)
        != _TARGET_SAMPLES
    ):
        raise ValueError("MULTI_BOUNDARY_EVIDENCE_EXACT5_INVALID")
    evidence_shas: set[str] = set()
    authority_shas: set[str] = set()
    typed: dict[str, dict[str, Any]] = {}
    for position, row in enumerate(rows):
        if (
            row["sidecar_item_order_0based"] != str(position)
            or row["source_submission_bundle_sha256"]
            != source_submission_sha
            or row["source_ingestion_execution_bundle_filesystem_sha256"]
            != source_execution_filesystem_sha
            or row["source_ingestion_execution_bundle_sha256"]
            != source_execution_internal_sha
            or row["graph_derived_boundary_count"] != "2"
            or any(row[field] != "true" for field in (
                "warhead_subgraph_connected",
                "contains_local_reaction_center",
                "contains_required_leaving_groups",
                "notes_match_parent_graph",
                "exact_two_boundaries_verified",
            ))
            or _SHA256.fullmatch(row["evidence_record_sha256"]) is None
            or row["evidence_record_sha256"]
            != _record_sha(
                row, _EVIDENCE_FIELDS, "evidence_record_sha256",
            )
            or _SHA256.fullmatch(
                row["source_v1_quarantine_authority_record_sha256"]
            ) is None
        ):
            raise ValueError("MULTI_BOUNDARY_EVIDENCE_RECORD_INVALID")
        atoms = _atom_ids(
            row["proposed_warhead_atom_ids_json"],
            field="proposed_warhead_atom_ids_json",
            allow_empty=False,
        )
        proposed = _boundary_records(
            row["proposed_boundary_records_json"],
            field="proposed_boundary_records_json",
            expected_count=2,
        )
        derived = _boundary_records(
            row["graph_derived_boundary_records_json"],
            field="graph_derived_boundary_records_json",
            expected_count=2,
        )
        _atom_ids(
            row["local_reaction_center_atom_ids_json"],
            field="local_reaction_center_atom_ids_json",
            allow_empty=False,
        )
        _atom_ids(
            row["required_leaving_group_atom_ids_json"],
            field="required_leaving_group_atom_ids_json",
            allow_empty=True,
        )
        if proposed != derived:
            raise ValueError("MULTI_BOUNDARY_EVIDENCE_GRAPH_MISMATCH")
        evidence_shas.add(row["evidence_record_sha256"])
        authority_shas.add(
            row["source_v1_quarantine_authority_record_sha256"]
        )
        typed[row["sample_index_row_id"]] = {
            "atoms": atoms,
            "boundaries": proposed,
            "row": row,
        }
    if len(evidence_shas) != 5 or len(authority_shas) != 5:
        raise ValueError("MULTI_BOUNDARY_EVIDENCE_DIGEST_UNIQUENESS_INVALID")
    return typed


def _typed_proposal(row: Mapping[str, str]) -> dict[str, Any]:
    if type(row) is not dict or tuple(row) != ingestion_design.PROPOSAL_FIELDS:
        raise ValueError("MULTI_BOUNDARY_PROPOSAL_FIELDS_INVALID")
    list_fields = {
        "local_reaction_center_atom_ids",
        "local_reaction_center_bond_ids",
        "proposed_pre_reaction_warhead_atom_ids",
        "required_leaving_group_atom_ids",
        "ambiguity_reasons",
    }
    result: dict[str, Any] = {}
    for field in ingestion_design.PROPOSAL_FIELDS:
        value = row[field]
        if field == "warhead_type_candidate_class_index_0based":
            if (
                not value.isdecimal()
                or (len(value) > 1 and value.startswith("0"))
            ):
                raise ValueError("MULTI_BOUNDARY_PROPOSAL_INDEX_INVALID")
            result[field] = int(value)
        elif field in list_fields:
            result[field] = _exact_list_str(value, field=field)
        else:
            result[field] = value
    if (
        result["proposal_record_sha256"]
        != _record_sha(
            result,
            ingestion_design.PROPOSAL_FIELDS,
            "proposal_record_sha256",
        )
    ):
        raise ValueError("MULTI_BOUNDARY_PROPOSAL_SHA_INVALID")
    return result


def _committed_revision_sources(
    repo_root: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, list[dict[str, str]]],
    dict[str, list[dict[str, str]]],
]:
    context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            repo_root
        )
    )
    try:
        ingestion_design.validate_ingestion_authority_context(context)
        payloads = {
            Path(path): payload for path, payload in context.source_payloads
        }
        proposal_rows = _csv_rows(
            payloads[ingestion_design.PROPOSALS],
            fields=ingestion_design.PROPOSAL_FIELDS,
            label="MULTI_BOUNDARY_COMMITTED_PROPOSALS",
        )
        atom_rows = _csv_rows(
            payloads[ingestion_design.PARENT_ATOMS],
            fields=ingestion_design.PARENT_ATOM_FIELDS,
            label="MULTI_BOUNDARY_COMMITTED_PARENT_ATOMS",
        )
        bond_rows = _csv_rows(
            payloads[ingestion_design.PARENT_BONDS],
            fields=ingestion_design.PARENT_BOND_FIELDS,
            label="MULTI_BOUNDARY_COMMITTED_PARENT_BONDS",
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "MULTI_BOUNDARY_AUTHORITY_CONTEXT_INVALID"
        ) from error
    proposals: dict[str, dict[str, Any]] = {}
    for row in proposal_rows:
        proposal = _typed_proposal(row)
        sample = proposal["sample_index_row_id"]
        if sample in proposals:
            raise ValueError("MULTI_BOUNDARY_PROPOSAL_SAMPLE_DUPLICATE")
        proposals[sample] = proposal
    atoms_by_ligand: dict[str, list[dict[str, str]]] = {}
    bonds_by_ligand: dict[str, list[dict[str, str]]] = {}
    for row in atom_rows:
        atoms_by_ligand.setdefault(row["ligand_comp_id"], []).append(row)
    for row in bond_rows:
        bonds_by_ligand.setdefault(row["ligand_comp_id"], []).append(row)
    return proposals, atoms_by_ligand, bonds_by_ligand


def _validate_revision_graph(
    *,
    worklist_row: Mapping[str, str],
    evidence_row: Mapping[str, str],
    reviewed_atoms: Sequence[str],
    reviewed_boundaries: Sequence[Mapping[str, str]],
    proposal: Mapping[str, Any],
    parent_atom_rows: Sequence[Mapping[str, str]],
    parent_bond_rows: Sequence[Mapping[str, str]],
) -> None:
    if (
        proposal["sample_index_row_id"] != worklist_row["sample_index_row_id"]
        or proposal["pdb_id"] != worklist_row["pdb_id"]
        or proposal["ligand_comp_id"] != worklist_row["ligand_comp_id"]
        or proposal["warhead_type_candidate_class_id"]
        != worklist_row["warhead_type_candidate_class_id"]
        or proposal["reaction_family_id"] != worklist_row["reaction_family_id"]
        or proposal["warhead_rule_id"] != worklist_row["warhead_rule_id"]
        or proposal["proposal_record_sha256"]
        != evidence_row["source_proposal_record_sha256"]
        or not parent_atom_rows
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
        raise ValueError("MULTI_BOUNDARY_REVISION_SOURCE_LINEAGE_INVALID")
    expected_graph_sha = proposal["component_parent_graph_sha256"]
    if any(
        row["component_parent_graph_sha256"] != expected_graph_sha
        or row["verified"] != "true"
        for row in (*parent_atom_rows, *parent_bond_rows)
    ):
        raise ValueError("MULTI_BOUNDARY_REVISION_PARENT_GRAPH_INVALID")
    parent_ids = [row["ccd_atom_id"] for row in parent_atom_rows]
    parent_set = set(parent_ids)
    atom_set = set(reviewed_atoms)
    if (
        len(parent_ids) != len(parent_set)
        or not atom_set < parent_set
        or not set(proposal["local_reaction_center_atom_ids"]) <= atom_set
        or not set(proposal["required_leaving_group_atom_ids"]) <= atom_set
    ):
        raise ValueError("MULTI_BOUNDARY_REVISION_ATOM_SET_INVALID")
    adjacency = {atom: set() for atom in reviewed_atoms}
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
            raise ValueError("MULTI_BOUNDARY_REVISION_PARENT_BOND_INVALID")
        parent_edges[edge] = (left, right, order)
        if left in atom_set and right in atom_set:
            adjacency[left].add(right)
            adjacency[right].add(left)
        elif (left in atom_set) != (right in atom_set):
            attachment = left if left in atom_set else right
            nonwarhead = right if attachment == left else left
            low, high = _utf8_sorted((attachment, nonwarhead))
            derived.append({
                "warhead_attachment_atom_id": attachment,
                "nonwarhead_boundary_atom_id": nonwarhead,
                "boundary_bond_order": order,
                "boundary_bond_id": f"{low}|{high}|{order}",
            })
    reached: set[str] = set()
    queue: deque[str] = deque((reviewed_atoms[0],))
    while queue:
        atom = queue.popleft()
        if atom in reached:
            continue
        reached.add(atom)
        queue.extend(adjacency[atom] - reached)
    if reached != atom_set:
        raise ValueError("MULTI_BOUNDARY_REVISION_DISCONNECTED")
    for bond_id in proposal["local_reaction_center_bond_ids"]:
        try:
            left, right, order = bond_id.split("|")
        except ValueError as error:
            raise ValueError(
                "MULTI_BOUNDARY_REVISION_LOCAL_CENTER_BOND_INVALID"
            ) from error
        low, high = _utf8_sorted((left, right))
        parent = parent_edges.get(frozenset((left, right)))
        if (
            bond_id != f"{low}|{high}|{order}"
            or parent is None
            or parent[2] != order
            or left not in atom_set
            or right not in atom_set
        ):
            raise ValueError(
                "MULTI_BOUNDARY_REVISION_LOCAL_CENTER_BOND_CUT"
            )
    derived.sort(
        key=lambda record: record["boundary_bond_id"].encode("utf-8")
    )
    if len(derived) != 2 or derived != list(reviewed_boundaries):
        raise ValueError("MULTI_BOUNDARY_REVISION_GRAPH_BOUNDARY_MISMATCH")
    for record in reviewed_boundaries:
        if (
            record["warhead_attachment_atom_id"] not in atom_set
            or record["nonwarhead_boundary_atom_id"] in atom_set
            or parent_edges.get(frozenset((
                record["warhead_attachment_atom_id"],
                record["nonwarhead_boundary_atom_id"],
            )), ("", "", ""))[2] != record["boundary_bond_order"]
        ):
            raise ValueError("MULTI_BOUNDARY_REVISION_BOUNDARY_INVALID")


def _compiled_record(
    *,
    row: dict[str, str],
    proposed_atoms: list[str],
    proposed_boundaries: list[dict[str, str]],
    reviewed_atoms: list[str],
    reviewed_boundaries: list[dict[str, str]],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "multi_boundary_review_record_version":
            row["multi_boundary_review_record_version"],
        "item_index_0based": int(row["sidecar_item_order_0based"]),
        "sample_index_row_id": row["sample_index_row_id"],
        "pdb_id": row["pdb_id"],
        "ligand_comp_id": row["ligand_comp_id"],
        "warhead_type_candidate_class_id":
            row["warhead_type_candidate_class_id"],
        "reaction_family_id": row["reaction_family_id"],
        "warhead_rule_id": row["warhead_rule_id"],
        "source_evidence_record_sha256":
            row["source_evidence_record_sha256"],
        "source_v1_quarantine_authority_record_sha256":
            row["source_v1_quarantine_authority_record_sha256"],
        "source_review_record_sha256": row["source_review_record_sha256"],
        "proposed_warhead_atom_ids": proposed_atoms,
        "proposed_boundary_records": proposed_boundaries,
        "scope_caveat": row["scope_caveat"],
        "review_decision": row["review_decision"],
        "reviewed_warhead_atom_ids": reviewed_atoms,
        "reviewed_boundary_records": reviewed_boundaries,
        "reviewer_id": row["reviewer_id"],
        "review_rationale": row["review_rationale"],
        "review_notes": row["review_notes"],
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id":
            row["reviewer_provenance_attestor_id"],
        "submission_source_label": row["submission_source_label"],
        "review_completed": True,
        "multi_boundary_review_record_sha256": "",
    }
    record["multi_boundary_review_record_sha256"] = _record_sha(
        record,
        _COMPILED_RECORD_FIELDS,
        "multi_boundary_review_record_sha256",
    )
    return record


def _validate_compiled_bundle(
    payload: bytes,
    *,
    expected: Mapping[str, Any],
) -> None:
    if (
        not payload
        or len(payload) >= _MAX_BUNDLE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or payload.endswith(b"\n")
    ):
        raise ValueError("MULTI_BOUNDARY_OUTPUT_BYTE_CONTRACT_INVALID")
    try:
        bundle = json.loads(payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError("MULTI_BOUNDARY_OUTPUT_ROUND_TRIP_INVALID") from error
    if (
        type(bundle) is not dict
        or tuple(bundle) != _BUNDLE_FIELDS
        or any(bundle[field] != expected[field] for field in _BUNDLE_FIELDS[:8])
        or type(bundle["submission_items"]) is not list
        or len(bundle["submission_items"]) != 5
        or bundle["multi_boundary_submission_bundle_sha256"]
        != _record_sha(
            bundle,
            _BUNDLE_FIELDS,
            "multi_boundary_submission_bundle_sha256",
        )
        or _SHA256.fullmatch(
            bundle["multi_boundary_submission_bundle_sha256"]
        ) is None
    ):
        raise ValueError("MULTI_BOUNDARY_OUTPUT_BUNDLE_INVALID")
    record_shas: set[str] = set()
    decision_count = 0
    for position, record in enumerate(bundle["submission_items"]):
        if (
            type(record) is not dict
            or tuple(record) != _COMPILED_RECORD_FIELDS
            or type(record["item_index_0based"]) is not int
            or record["item_index_0based"] != position
            or record["sample_index_row_id"] != _TARGET_SAMPLES[position]
            or type(record["proposed_warhead_atom_ids"]) is not list
            or type(record["proposed_boundary_records"]) is not list
            or type(record["reviewed_warhead_atom_ids"]) is not list
            or type(record["reviewed_boundary_records"]) is not list
            or type(record["reviewer_provenance_attested"]) is not bool
            or record["reviewer_provenance_attested"] is not True
            or type(record["review_completed"]) is not bool
            or record["review_completed"] is not True
            or any(
                type(record[field]) is not str
                for field in _COMPILED_RECORD_FIELDS
                if field not in {
                    "item_index_0based",
                    "proposed_warhead_atom_ids",
                    "proposed_boundary_records",
                    "reviewed_warhead_atom_ids",
                    "reviewed_boundary_records",
                    "reviewer_provenance_attested",
                    "review_completed",
                }
            )
            or record["review_decision"] not in _DECISIONS
            or record["multi_boundary_review_record_sha256"]
            != _record_sha(
                record,
                _COMPILED_RECORD_FIELDS,
                "multi_boundary_review_record_sha256",
            )
            or _SHA256.fullmatch(
                record["multi_boundary_review_record_sha256"]
            ) is None
        ):
            raise ValueError("MULTI_BOUNDARY_OUTPUT_RECORD_INVALID")
        record_shas.add(record["multi_boundary_review_record_sha256"])
        decision_count += 1
    if len(record_shas) != 5 or decision_count != 5:
        raise ValueError("MULTI_BOUNDARY_OUTPUT_COUNTS_INVALID")


def compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
    *,
    verified_multi_boundary_evidence_csv: bytes,
    multi_boundary_review_worklist_csv: bytes,
    readme_md: bytes,
    source_submission_bundle: bytes,
    source_ingestion_execution_bundle: bytes,
    repo_root: Path,
    submission_batch_id: str,
) -> bytes:
    """Return strict hashed Exact10 JSON bytes without writing any files."""

    byte_inputs = (
        verified_multi_boundary_evidence_csv,
        multi_boundary_review_worklist_csv,
        readme_md,
        source_submission_bundle,
        source_ingestion_execution_bundle,
    )
    if any(type(payload) is not bytes for payload in byte_inputs):
        raise ValueError("all payload inputs must be exact bytes")
    if type(repo_root) is not type(Path()):
        raise ValueError("repo_root must be an exact Path")
    if not _meaningful(submission_batch_id):
        raise ValueError("submission_batch_id must be an exact meaningful str")
    snapshots = tuple(bytes(payload) for payload in byte_inputs)
    reference = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=source_submission_bundle,
            source_ingestion_execution_bundle=
                source_ingestion_execution_bundle,
            repo_root=repo_root,
        )
    )
    if (
        type(reference) is not dict
        or tuple(reference) != (
            "verified_multi_boundary_evidence.csv",
            "multi_boundary_review_worklist.csv",
            "README.md",
        )
        or verified_multi_boundary_evidence_csv
        != reference["verified_multi_boundary_evidence.csv"]
        or readme_md != reference["README.md"]
    ):
        raise ValueError("MULTI_BOUNDARY_EXACT3_REFERENCE_MISMATCH")

    evidence_rows = _csv_rows(
        verified_multi_boundary_evidence_csv,
        fields=_EVIDENCE_FIELDS,
        label="MULTI_BOUNDARY_EVIDENCE",
    )
    worklist_rows = _csv_rows(
        multi_boundary_review_worklist_csv,
        fields=_WORKLIST_FIELDS,
        label="MULTI_BOUNDARY_WORKLIST",
    )
    blank_rows = _csv_rows(
        reference["multi_boundary_review_worklist.csv"],
        fields=_WORKLIST_FIELDS,
        label="MULTI_BOUNDARY_BLANK_WORKLIST",
    )
    if (
        len(worklist_rows) != 5
        or len(blank_rows) != 5
        or tuple(row["sample_index_row_id"] for row in worklist_rows)
        != _TARGET_SAMPLES
        or any(
            tuple(row[field] for field in _FROZEN_WORKLIST_FIELDS)
            != tuple(blank[field] for field in _FROZEN_WORKLIST_FIELDS)
            for row, blank in zip(worklist_rows, blank_rows)
        )
    ):
        raise ValueError("MULTI_BOUNDARY_WORKLIST_FROZEN_LINEAGE_INVALID")

    submission_sha = _sha256(source_submission_bundle)
    execution_filesystem_sha = _sha256(
        source_ingestion_execution_bundle
    )
    execution_internal_sha = _execution_internal_sha(
        source_ingestion_execution_bundle,
        source_submission_sha=submission_sha,
    )
    evidence = _validate_evidence(
        evidence_rows,
        source_submission_sha=submission_sha,
        source_execution_filesystem_sha=execution_filesystem_sha,
        source_execution_internal_sha=execution_internal_sha,
    )

    parsed_rows: list[
        tuple[
            dict[str, str],
            list[str],
            list[dict[str, str]],
            list[str],
            list[dict[str, str]],
        ]
    ] = []
    has_revision = False
    for position, row in enumerate(worklist_rows):
        sample = row["sample_index_row_id"]
        evidence_item = evidence[sample]
        if (
            row["sidecar_item_order_0based"] != str(position)
            or row["multi_boundary_review_record_sha256"] != ""
            or row["review_decision"] not in _DECISIONS
            or row["review_completed"] != "true"
            or row["reviewer_provenance_attested"] != "true"
            or any(not _meaningful(row[field]) for field in (
                "reviewer_id",
                "review_rationale",
                "review_notes",
                "reviewer_provenance_attestor_id",
                "submission_source_label",
            ))
            or row["source_evidence_record_sha256"]
            != evidence_item["row"]["evidence_record_sha256"]
            or row["source_v1_quarantine_authority_record_sha256"]
            != evidence_item["row"][
                "source_v1_quarantine_authority_record_sha256"
            ]
            or row["source_review_record_sha256"]
            != evidence_item["row"]["source_review_record_sha256"]
        ):
            raise ValueError("MULTI_BOUNDARY_WORKLIST_COMPLETION_INVALID")
        proposed_atoms = _atom_ids(
            row["proposed_warhead_atom_ids_json"],
            field="proposed_warhead_atom_ids_json",
            allow_empty=False,
        )
        proposed_boundaries = _boundary_records(
            row["proposed_boundary_records_json"],
            field="proposed_boundary_records_json",
            expected_count=2,
        )
        if (
            proposed_atoms != evidence_item["atoms"]
            or proposed_boundaries != evidence_item["boundaries"]
        ):
            raise ValueError("MULTI_BOUNDARY_WORKLIST_PROPOSAL_MISMATCH")
        quarantine = row["review_decision"] == "quarantine"
        reviewed_atoms = _atom_ids(
            row["reviewed_warhead_atom_ids_json"],
            field="reviewed_warhead_atom_ids_json",
            allow_empty=quarantine,
        )
        reviewed_boundaries = _boundary_records(
            row["reviewed_boundary_records_json"],
            field="reviewed_boundary_records_json",
            expected_count=0 if quarantine else 2,
        )
        if quarantine:
            if reviewed_atoms or reviewed_boundaries:
                raise ValueError(
                    "MULTI_BOUNDARY_QUARANTINE_EVIDENCE_NOT_EMPTY"
                )
        elif row["review_decision"] == (
            "accept_verified_two_boundary_proposal"
        ):
            if (
                reviewed_atoms != proposed_atoms
                or reviewed_boundaries != proposed_boundaries
            ):
                raise ValueError("MULTI_BOUNDARY_ACCEPT_SEMANTICS_INVALID")
        else:
            if (
                reviewed_atoms == proposed_atoms
                and reviewed_boundaries == proposed_boundaries
            ):
                raise ValueError("MULTI_BOUNDARY_REVISION_UNCHANGED")
            has_revision = True
        parsed_rows.append((
            row,
            proposed_atoms,
            proposed_boundaries,
            reviewed_atoms,
            reviewed_boundaries,
        ))

    if has_revision:
        proposals, atoms_by_ligand, bonds_by_ligand = (
            _committed_revision_sources(repo_root)
        )
        for (
            row,
            _proposed_atoms,
            _proposed_boundaries,
            reviewed_atoms,
            reviewed_boundaries,
        ) in parsed_rows:
            if row["review_decision"] != (
                "revise_two_boundary_atom_set_and_boundaries"
            ):
                continue
            sample = row["sample_index_row_id"]
            ligand = row["ligand_comp_id"]
            try:
                proposal = proposals[sample]
                parent_atoms = atoms_by_ligand[ligand]
                parent_bonds = bonds_by_ligand[ligand]
            except KeyError as error:
                raise ValueError(
                    "MULTI_BOUNDARY_REVISION_SOURCE_MISSING"
                ) from error
            _validate_revision_graph(
                worklist_row=row,
                evidence_row=evidence[sample]["row"],
                reviewed_atoms=reviewed_atoms,
                reviewed_boundaries=reviewed_boundaries,
                proposal=proposal,
                parent_atom_rows=parent_atoms,
                parent_bond_rows=parent_bonds,
            )

    records = [
        _compiled_record(
            row=row,
            proposed_atoms=proposed_atoms,
            proposed_boundaries=proposed_boundaries,
            reviewed_atoms=reviewed_atoms,
            reviewed_boundaries=reviewed_boundaries,
        )
        for (
            row,
            proposed_atoms,
            proposed_boundaries,
            reviewed_atoms,
            reviewed_boundaries,
        ) in parsed_rows
    ]
    if len({
        record["multi_boundary_review_record_sha256"]
        for record in records
    }) != 5:
        raise ValueError("MULTI_BOUNDARY_COMPILED_RECORD_SHA_NOT_UNIQUE")
    bundle: dict[str, Any] = {
        "multi_boundary_submission_bundle_version": _BUNDLE_VERSION,
        "source_submission_bundle_sha256": submission_sha,
        "source_ingestion_execution_bundle_filesystem_sha256":
            execution_filesystem_sha,
        "source_ingestion_execution_bundle_sha256": execution_internal_sha,
        "source_verified_multi_boundary_evidence_csv_sha256":
            _sha256(verified_multi_boundary_evidence_csv),
        "source_multi_boundary_review_worklist_csv_sha256":
            _sha256(multi_boundary_review_worklist_csv),
        "source_readme_sha256": _sha256(readme_md),
        "submission_batch_id": submission_batch_id,
        "submission_items": records,
        "multi_boundary_submission_bundle_sha256": "",
    }
    bundle["multi_boundary_submission_bundle_sha256"] = _record_sha(
        bundle,
        _BUNDLE_FIELDS,
        "multi_boundary_submission_bundle_sha256",
    )
    payload = _ordered_json_bytes(bundle)
    expected = {
        field: bundle[field] for field in _BUNDLE_FIELDS[:8]
    }
    _validate_compiled_bundle(payload, expected=expected)
    if tuple(byte_inputs) != snapshots:
        raise ValueError("MULTI_BOUNDARY_INPUT_MUTATION_DETECTED")
    return payload
