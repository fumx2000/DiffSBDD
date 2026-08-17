"""Create the reviewed K36 W1 family/rule authority payloads in memory.

The creator is intentionally narrow.  It accepts only the formally completed
K36 direct-attachment review, recompiles its submission with the published
compiler, and returns two deterministic payloads.  It does not write state,
update effective authority, ingest data, or establish PRE/mechanistic claims.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_recovered7_direct_attachment_completed_review_submission_successor_v1
    as review_successor,
)


__all__ = (
    "AuthorityCreationValidationError",
    "CREATOR_SCHEMA_VERSION",
    "REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION",
    "WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION",
    "K36_SOURCE_REVIEW_RECORD_SHA256_V1",
    "EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1",
    "canonical_authority_semantic_signature_json_v1",
    "authority_semantic_signature_sha256_v1",
    "authority_id_from_semantic_signature_v1",
    "validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1",
    "build_covapie_k36_w1_reaction_family_and_warhead_rule_authority_v1",
)


CREATOR_SCHEMA_VERSION = (
    "covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1"
)
REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION = (
    "covapie_cys_sg_reaction_family_authority_payload_v1"
)
WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION = (
    "covapie_cys_sg_warhead_rule_authority_payload_v1"
)
_REACTION_FAMILY_SIGNATURE_VERSION = (
    "covapie_k36_w1_reaction_family_semantic_signature_v1"
)
_WARHEAD_RULE_SIGNATURE_VERSION = (
    "covapie_k36_w1_warhead_rule_semantic_signature_v1"
)
K36_SOURCE_REVIEW_RECORD_SHA256_V1 = (
    "f27c918bab59eaa82473373f589cb083be925d26e48a34d7ac33990f6fa7a7ba"
)

_REVIEW_SCOPE = "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
_ACTIVE_WARHEAD_SEMANTICS = "REACTION_COMPETENT_ACTIVE_WARHEAD_V1"
_NOT_ESTABLISHED = "NOT_ESTABLISHED"
_NOT_CLAIMED = "NOT_CLAIMED"
_FAMILY_ID_PREFIX = "COVAPIE_CYS_SG_REACTION_FAMILY_"
_RULE_ID_PREFIX = "COVAPIE_CYS_SG_WARHEAD_RULE_"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_FAMILY_ID = re.compile(r"COVAPIE_CYS_SG_REACTION_FAMILY_[0-9A-F]{16}")
_RULE_ID = re.compile(r"COVAPIE_CYS_SG_WARHEAD_RULE_[0-9A-F]{16}")

# These are the locally published/effective Current11 sources inspected for the
# baseline named in the task.  Their conclusions deliberately do not promote
# candidate family/rule IDs carried by boundary authority into approved IDs.
EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1 = (
    {
        "source_path": (
            "data/derived/covalent_small/"
            "covapie_current11_reaction_family_and_approved_warhead_rule_"
            "authority_binding_v1/"
            "covapie_family_and_warhead_rule_authority_registry.csv"
        ),
        "source_sha256": (
            "4899d4664acf45d5ee90283e7977d62385b3a70fe41e082f4d060388be7e106b"
        ),
        "family_rule_authority_conclusion": (
            "CANDIDATE_ONLY_ZERO_APPROVED_FAMILY_OR_RULE"
        ),
    },
    {
        "source_path": (
            "covapie-state/manual-review/current11-family-rule-approval-v1/"
            "family_rule_approval_worklist.csv"
        ),
        "source_sha256": (
            "9a85c03384a09620a1c168b023d3a1de2ebb1fed57589e55449ec1672d6c3add"
        ),
        "family_rule_authority_conclusion": (
            "UNFILLED_ZERO_COMPLETED_FAMILY_OR_RULE_APPROVALS"
        ),
    },
    {
        "source_path": (
            "covapie-state/manual-review/"
            "covapie_current11_unified_effective_authority_view_v1.json"
        ),
        "source_sha256": (
            "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"
        ),
        "family_rule_authority_conclusion": (
            "BOUNDARY_AUTHORITY_ONLY_FAMILY_RULE_IDS_NOT_APPROVED_AUTHORITY"
        ),
    },
)
_BASELINE_REGISTRY_PATH = EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1[0][
    "source_path"
]
_BASELINE_APPROVAL_WORKLIST_PATH = (
    EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1[1]["source_path"]
)
_BASELINE_EFFECTIVE_VIEW_PATH = EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1[
    2
]["source_path"]

_RESULT_FIELDS = (
    "reaction_family_authority",
    "warhead_rule_authority",
    "creation_provenance_readiness_summary",
)
_AUTHORITY_PAYLOAD_FIELDS = (
    "authority_schema_version",
    "authority_kind",
    "authority_id",
    "semantic_name",
    "canonical_semantic_signature",
    "canonical_semantic_signature_sha256",
    "source_human_review_provenance",
)
_PROVENANCE_FIELDS = (
    "source_review_class_id",
    "source_chemistry_signature_sha256",
    "source_completed_review_record_sha256",
    "source_reviewer_id",
    "source_review_scope",
    "source_member_identities",
    "source_submission_schema_version",
)
_SUMMARY_FIELDS = (
    "creator_schema_version",
    "source_human_review_provenance",
    "existing_approved_authority_collision_check",
    "reaction_family_authority_payload_ready",
    "warhead_rule_authority_payload_ready",
    "reaction_family_authority_materialized",
    "warhead_rule_authority_materialized",
    "effective_authority_updated",
    "ingestion_executed",
    "training_supervision_authority_complete",
    "K2Z_principal_classification",
    "K2Z_status",
    "K2Z_confirmed_minimal_active_warhead_embedded_profile_count",
    "K2Z_current11_exact_two_boundary_structural_precedent_count",
    "K2Z_identical_active_warhead_authority_count_claimed",
    "1ZB_status",
    "exact10_feature_semantics_reopened",
    "network_request_executed",
    "raw_downloaded",
    "topology_downloaded",
    "distance_bond_inference_used",
    "PRE_geometry_reconstruction_executed",
    "model_forward",
    "backward",
    "optimizer_step",
    "Trainer.fit",
    "RL",
)


class AuthorityCreationValidationError(ValueError):
    """Raised when K36 authority creation cannot be proven safe."""


def _fail(reason: str) -> None:
    raise AuthorityCreationValidationError(reason)


def canonical_authority_semantic_signature_json_v1(value: object) -> str:
    """Return the deterministic JSON used for semantic authority identity."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise AuthorityCreationValidationError(
            "CANONICAL_SEMANTIC_SIGNATURE_JSON_INVALID"
        ) from error


def authority_semantic_signature_sha256_v1(value: object) -> str:
    """Hash one canonical semantic signature, excluding provenance wrappers."""

    payload = canonical_authority_semantic_signature_json_v1(value).encode(
        "ascii"
    )
    return hashlib.sha256(payload).hexdigest()


def authority_id_from_semantic_signature_v1(
    authority_kind: str, semantic_signature: object
) -> str:
    """Apply the published 16-uppercase-hex CovaPIE authority ID convention."""

    if authority_kind == "reaction_family":
        prefix = _FAMILY_ID_PREFIX
    elif authority_kind == "warhead_rule":
        prefix = _RULE_ID_PREFIX
    else:
        _fail("AUTHORITY_KIND_INVALID")
    digest = authority_semantic_signature_sha256_v1(semantic_signature)
    return prefix + digest[:16].upper()


def _expected_provenance() -> dict[str, Any]:
    return {
        "source_review_class_id": review_successor.K36_REVIEW_CLASS_ID_V1,
        "source_chemistry_signature_sha256": (
            review_successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
        ),
        "source_completed_review_record_sha256": (
            K36_SOURCE_REVIEW_RECORD_SHA256_V1
        ),
        "source_reviewer_id": "fmx",
        "source_review_scope": _REVIEW_SCOPE,
        "source_member_identities": list(
            review_successor.K36_MEMBER_IDENTITIES_V1
        ),
        "source_submission_schema_version": (
            review_successor.SUBMISSION_SCHEMA_VERSION
        ),
    }


def _reaction_family_semantic_signature() -> dict[str, Any]:
    return {
        "semantic_signature_version": _REACTION_FAMILY_SIGNATURE_VERSION,
        "authority_kind": "reaction_family",
        "applicability_scope": {
            "scope_kind": _REVIEW_SCOPE,
            "required_chemistry_signature_sha256": (
                review_successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
            ),
            "cross_signature_propagation_allowed": False,
        },
        "target_condition": {
            "residue_component_id": "CYS",
            "residue_atom_id": "SG",
            "residue_atom_element": "S",
        },
        "ligand_reactive_atom_contract": {
            "atom_element": "C",
            "atom_role": "LIGAND_REACTIVE_CARBON",
        },
        "formed_protein_ligand_event": {
            "edge_kind": "PROTEIN_LIGAND_FORMED_COVALENT_EVENT",
            "protein_endpoint": "CYS:SG",
            "ligand_endpoint_role": "LIGAND_REACTIVE_CARBON",
            "formed_bond_order_authority_status": _NOT_ESTABLISHED,
            "component_internal_topology_edge": False,
        },
        "active_warhead_semantics": _ACTIVE_WARHEAD_SEMANTICS,
        "active_warhead_atom_role_contract": [
            {
                "element": "C",
                "atom_role": "LIGAND_REACTIVE_CENTER",
            },
            {
                "element": "O",
                "atom_role": "ACTIVE_WARHEAD_OXYGEN",
            },
        ],
        "pre_reaction_graph_authority_status": _NOT_ESTABLISHED,
        "pre_reaction_bond_order_authority_status": _NOT_ESTABLISHED,
        "mechanism_claim_status": _NOT_CLAIMED,
        "reversibility_claim_status": _NOT_CLAIMED,
    }


def _warhead_rule_semantic_signature(
    reaction_family_id: str,
) -> dict[str, Any]:
    return {
        "semantic_signature_version": _WARHEAD_RULE_SIGNATURE_VERSION,
        "authority_kind": "warhead_rule",
        "reaction_family_authority_id": reaction_family_id,
        "applicability_scope": {
            "scope_kind": _REVIEW_SCOPE,
            "required_chemistry_signature_sha256": (
                review_successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
            ),
            "cross_signature_propagation_allowed": False,
        },
        "target_condition": {
            "residue_component_id": "CYS",
            "residue_atom_id": "SG",
            "residue_atom_element": "S",
        },
        "ligand_component_id": "K36",
        "ligand_reactive_atom": {
            "atom_id": "C21",
            "element": "C",
        },
        "active_warhead_semantics": _ACTIVE_WARHEAD_SEMANTICS,
        "active_warhead_atom_contract": [
            {
                "atom_id": "C21",
                "element": "C",
                "atom_role": "LIGAND_REACTIVE_CENTER",
            },
            {
                "atom_id": "O22",
                "element": "O",
                "atom_role": "ACTIVE_WARHEAD_OXYGEN",
            },
        ],
        "masked_precursor_provenance": {
            "atom_ids": list(
                review_successor.K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1
            ),
            "included_in_active_warhead": False,
            "establishes_pre_reaction_graph_authority": False,
        },
        "retained_role_profile": direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "retained_framework_boundary": {
            "edge_kind": "COMPONENT_INTERNAL_RETAINED_FRAMEWORK_BOUNDARY",
            "scaffold_side_atom_id": "C20",
            "warhead_side_atom_id": "C21",
            "bond_order": "single",
            "component_internal_topology_edge": True,
        },
        "formed_protein_ligand_event": {
            "edge_kind": "PROTEIN_LIGAND_FORMED_COVALENT_EVENT",
            "protein_endpoint": {
                "residue_component_id": "CYS",
                "atom_id": "SG",
            },
            "ligand_endpoint": {
                "ligand_component_id": "K36",
                "atom_id": "C21",
            },
            "formed_bond_order_authority_status": _NOT_ESTABLISHED,
            "component_internal_topology_edge": False,
        },
        "minimal_seed_supervision_provenance": {
            "atom_ids": ["C20", "N19"],
            "included_in_chemistry_rule_matching": False,
        },
        "pre_reaction_graph_authority_status": _NOT_ESTABLISHED,
        "pre_reaction_bond_order_authority_status": _NOT_ESTABLISHED,
        "mechanism_claim_status": _NOT_CLAIMED,
        "reversibility_claim_status": _NOT_CLAIMED,
    }


def _validate_exact_k36_inputs(
    completed_review_record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    sample_applicability: Sequence[Mapping[str, Any]],
    compiled_submission: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        review_successor.validate_completed_direct_attachment_review_record_v1(
            completed_review_record,
            review_class,
            applicability_records_or_signatures=sample_applicability,
        )
        canonical_submission = (
            review_successor.compile_recovered7_direct_attachment_review_submission_v1(
                completed_review_record,
                review_class,
                sample_applicability,
            )
        )
    except (TypeError, KeyError, ValueError) as error:
        raise AuthorityCreationValidationError(
            "COMPLETED_K36_DIRECT_REVIEW_VALIDATION_FAILED"
        ) from error

    if completed_review_record.get("reviewer_id") != "fmx":
        _fail("K36_SOURCE_REVIEWER_ID_MISMATCH")
    if (
        completed_review_record.get("review_record_sha256")
        != K36_SOURCE_REVIEW_RECORD_SHA256_V1
    ):
        _fail("K36_SOURCE_REVIEW_RECORD_SHA256_MISMATCH")
    if completed_review_record.get("review_status") != "COMPLETED":
        _fail("K36_COMPLETED_REVIEW_REQUIRED")
    if completed_review_record.get("review_scope") != _REVIEW_SCOPE:
        _fail("K36_REVIEW_SCOPE_MISMATCH")
    if (
        review_class.get("review_class_id")
        != review_successor.K36_REVIEW_CLASS_ID_V1
        or review_class.get("chemistry_review_signature_sha256")
        != review_successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
        or tuple(review_class.get("member_sample_identities", ()))
        != review_successor.K36_MEMBER_IDENTITIES_V1
    ):
        _fail("K36_PUBLISHED_REVIEW_CLASS_MISMATCH")

    try:
        signature = review_class["chemistry_review_signature"]
        event = signature["explicit_covalent_event"]
        topology_atoms_not_observed = tuple(
            signature["topology_heavy_atoms_not_observed"]
        )
    except (KeyError, TypeError) as error:
        raise AuthorityCreationValidationError(
            "K36_CHEMISTRY_SIGNATURE_CONTENT_INVALID"
        ) from error
    if (
        signature.get("ligand_component_id") != "K36"
        or signature.get("reactive_ligand_atom") != "C21"
        or signature.get("reactive_ligand_atom_element") != "C"
        or signature.get("reactive_residue") != "CYS"
        or signature.get("reactive_residue_atom") != "SG"
        or event.get("ligand_component_id") != "K36"
        or event.get("ligand_atom_id") != "C21"
        or event.get("ligand_atom_element") != "C"
        or event.get("residue_component_id") != "CYS"
        or event.get("residue_atom_id") != "SG"
        or event.get("component_internal_topology_edge") is not False
        or topology_atoms_not_observed
        != review_successor.K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1
    ):
        _fail("K36_APPROVED_CHEMISTRY_SIGNATURE_SEMANTICS_MISMATCH")

    if not isinstance(compiled_submission, Mapping):
        _fail("COMPILED_SUBMISSION_MAPPING_REQUIRED")
    if dict(compiled_submission) != canonical_submission:
        _fail("COMPILED_SUBMISSION_NOT_CANONICAL_COMPILER_OUTPUT")
    expected_submission = {
        "reaction_family_authority_creation_required": True,
        "warhead_rule_authority_creation_required": True,
        "training_supervision_authority_complete": False,
        "reviewed_warhead_atom_semantics": _ACTIVE_WARHEAD_SEMANTICS,
        "reviewed_warhead_atom_ids": ["C21", "O22"],
        "reviewed_warhead_attachment_atom_id": "C21",
        "reviewed_nonwarhead_boundary_atom_id": "C20",
        "reviewed_attachment_boundary_bond_order": "single",
        "role_profile": direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "reviewed_linker_atom_ids": [],
        "reviewed_warhead_role_atom_ids": ["C21", "O22"],
        "reviewed_minimal_seed_atom_ids": ["C20", "N19"],
        "source_review_record_sha256": K36_SOURCE_REVIEW_RECORD_SHA256_V1,
    }
    for field, expected in expected_submission.items():
        if canonical_submission.get(field) != expected:
            _fail(f"K36_CANONICAL_SUBMISSION_SEMANTICS_MISMATCH:{field}")
    if canonical_submission.get("direct_boundary_semantics") != {
        "boundary_profile": "DIRECT_SCAFFOLD_WARHEAD_SINGLE_BOUNDARY_V1",
        "boundary_count": 1,
        "scaffold_side_atom_id": "C20",
        "warhead_side_atom_id": "C21",
        "bond_order": "single",
        "linker_present": False,
    }:
        _fail("K36_DIRECT_BOUNDARY_SEMANTICS_MISMATCH")
    return canonical_submission


def _parse_baseline_csv_rows_v1(
    payload: bytes, *, source_path: str
) -> tuple[dict[str, str], ...]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        fieldnames = reader.fieldnames
        rows = tuple(dict(row) for row in reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise AuthorityCreationValidationError(
            f"BASELINE_AUTHORITY_SOURCE_CSV_INVALID:{source_path}"
        ) from error
    if (
        not fieldnames
        or len(fieldnames) != len(set(fieldnames))
        or any(
            None in row
            or any(value is None for value in row.values())
            for row in rows
        )
    ):
        _fail(f"BASELINE_AUTHORITY_SOURCE_CSV_INVALID:{source_path}")
    return rows


def _validate_registry_authority_source_v1(
    payload: bytes,
    *,
    generated_family_id: str,
    generated_rule_id: str,
) -> tuple[frozenset[str], frozenset[str]]:
    rows = _parse_baseline_csv_rows_v1(
        payload, source_path=_BASELINE_REGISTRY_PATH
    )
    required = (
        "reaction_family_id",
        "reaction_family_authority_status",
        "warhead_rule_id",
        "approval_status",
    )
    if len(rows) != 7 or any(field not in rows[0] for field in required):
        _fail("BASELINE_AUTHORITY_REGISTRY_CONTRACT_INVALID")
    family_ids: set[str] = set()
    rule_ids: set[str] = set()
    for row in rows:
        family_status = row["reaction_family_authority_status"]
        rule_status = row["approval_status"]
        family_id = row["reaction_family_id"]
        rule_id = row["warhead_rule_id"]
        if (
            family_id == generated_family_id
            and family_status != "candidate_only"
        ) or (rule_id == generated_rule_id and rule_status != "candidate_only"):
            _fail("BASELINE_GENERATED_AUTHORITY_ID_FORMAL_COLLISION")
        if family_status != "candidate_only" or rule_status != "candidate_only":
            _fail("BASELINE_AUTHORITY_REGISTRY_FORMAL_AUTHORITY_PRESENT")
        if (
            _FAMILY_ID.fullmatch(family_id) is None
            or _RULE_ID.fullmatch(rule_id) is None
        ):
            _fail("BASELINE_AUTHORITY_REGISTRY_IDENTITY_INVALID")
        family_ids.add(family_id)
        rule_ids.add(rule_id)
    if len(family_ids) != 7 or len(rule_ids) != 7:
        _fail("BASELINE_AUTHORITY_REGISTRY_IDENTITY_COUNT_INVALID")
    return frozenset(family_ids), frozenset(rule_ids)


def _validate_approval_worklist_authority_source_v1(payload: bytes) -> None:
    rows = _parse_baseline_csv_rows_v1(
        payload, source_path=_BASELINE_APPROVAL_WORKLIST_PATH
    )
    required = (
        "reaction_family_review_decision",
        "warhead_rule_review_decision",
        "review_completed",
    )
    if len(rows) != 7 or any(field not in rows[0] for field in required):
        _fail("BASELINE_AUTHORITY_APPROVAL_WORKLIST_CONTRACT_INVALID")
    if any(
        row["review_completed"]
        or row["reaction_family_review_decision"]
        or row["warhead_rule_review_decision"]
        for row in rows
    ):
        _fail("BASELINE_AUTHORITY_APPROVAL_WORKLIST_COMPLETED_DECISION_PRESENT")


def _reject_nonfinite_json_constant(value: str) -> None:
    _fail(f"BASELINE_AUTHORITY_EFFECTIVE_VIEW_NONFINITE_JSON:{value}")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"BASELINE_AUTHORITY_EFFECTIVE_VIEW_DUPLICATE_KEY:{key}")
        result[key] = value
    return result


def _validate_unified_effective_authority_source_v1(
    payload: bytes,
    *,
    candidate_family_ids: frozenset[str],
    candidate_rule_ids: frozenset[str],
) -> None:
    try:
        view = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise AuthorityCreationValidationError(
            "BASELINE_AUTHORITY_EFFECTIVE_VIEW_JSON_INVALID"
        ) from error
    if type(view) is not dict:
        _fail("BASELINE_AUTHORITY_EFFECTIVE_VIEW_CONTRACT_INVALID")
    records = view.get("effective_authority_records")
    if (
        type(records) is not list
        or len(records) != 11
        or view.get("effective_authority_record_count") != 11
    ):
        _fail("BASELINE_AUTHORITY_EFFECTIVE_VIEW_CONTRACT_INVALID")
    for record in records:
        if type(record) is not dict:
            _fail("BASELINE_AUTHORITY_EFFECTIVE_VIEW_RECORD_INVALID")
        effective = record.get("effective_authority_record")
        if type(effective) is not dict:
            _fail("BASELINE_AUTHORITY_EFFECTIVE_VIEW_RECORD_INVALID")
        for key in effective:
            if key not in ("reaction_family_id", "warhead_rule_id") and (
                "reaction_family" in key or "warhead_rule" in key
            ):
                _fail(
                    "BASELINE_AUTHORITY_EFFECTIVE_VIEW_FORMAL_"
                    "FAMILY_RULE_AUTHORITY_PRESENT"
                )
        if (
            effective.get("reaction_family_id") not in candidate_family_ids
            or effective.get("warhead_rule_id") not in candidate_rule_ids
        ):
            _fail("BASELINE_AUTHORITY_EFFECTIVE_VIEW_NONCANDIDATE_ID_PRESENT")


def _validate_baseline_authority_source_payloads_v1(
    source_payloads: Mapping[str, bytes],
    *,
    generated_family_id: str,
    generated_rule_id: str,
) -> None:
    if not isinstance(source_payloads, Mapping):
        _fail("BASELINE_AUTHORITY_SOURCE_PAYLOADS_MAPPING_REQUIRED")
    expected_paths = tuple(
        source["source_path"]
        for source in EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1
    )
    provided_paths = tuple(source_payloads)
    missing = sorted(set(expected_paths) - set(provided_paths))
    if missing:
        _fail(f"BASELINE_AUTHORITY_SOURCE_MISSING:{missing[0]}")
    extra = sorted(set(provided_paths) - set(expected_paths))
    if extra:
        _fail(f"BASELINE_AUTHORITY_SOURCE_EXTRA:{extra[0]}")
    if len(provided_paths) != len(expected_paths):
        _fail("BASELINE_AUTHORITY_SOURCE_PATH_INVENTORY_INVALID")

    for source in EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1:
        path = source["source_path"]
        payload = source_payloads[path]
        if type(payload) is not bytes:
            _fail(f"BASELINE_AUTHORITY_SOURCE_BYTES_REQUIRED:{path}")
        if hashlib.sha256(payload).hexdigest() != source["source_sha256"]:
            _fail(f"BASELINE_AUTHORITY_SOURCE_SHA256_MISMATCH:{path}")

    family_ids, rule_ids = _validate_registry_authority_source_v1(
        source_payloads[_BASELINE_REGISTRY_PATH],
        generated_family_id=generated_family_id,
        generated_rule_id=generated_rule_id,
    )
    _validate_approval_worklist_authority_source_v1(
        source_payloads[_BASELINE_APPROVAL_WORKLIST_PATH]
    )
    _validate_unified_effective_authority_source_v1(
        source_payloads[_BASELINE_EFFECTIVE_VIEW_PATH],
        candidate_family_ids=family_ids,
        candidate_rule_ids=rule_ids,
    )


def _validate_existing_authority_records(
    existing_authority_records: Sequence[Mapping[str, Any]],
    *,
    family_id: str,
    family_signature_sha256: str,
    rule_id: str,
    rule_signature_sha256: str,
) -> int:
    if type(existing_authority_records) not in (tuple, list):
        _fail("EXISTING_AUTHORITY_RECORD_SEQUENCE_REQUIRED")
    approved_count = 0
    expected = {
        "reaction_family": (family_id, family_signature_sha256, _FAMILY_ID),
        "warhead_rule": (rule_id, rule_signature_sha256, _RULE_ID),
    }
    for record in existing_authority_records:
        if not isinstance(record, Mapping):
            _fail("EXISTING_AUTHORITY_RECORD_MAPPING_REQUIRED")
        required = (
            "authority_kind",
            "authority_id",
            "canonical_semantic_signature_sha256",
            "authority_status",
            "authority_source",
        )
        if any(field not in record for field in required):
            _fail("EXISTING_AUTHORITY_RECORD_FIELD_MISSING")
        kind = record["authority_kind"]
        status = record["authority_status"]
        authority_id = record["authority_id"]
        signature_sha256 = record["canonical_semantic_signature_sha256"]
        if kind not in expected:
            _fail("EXISTING_AUTHORITY_KIND_INVALID")
        if status not in ("CANDIDATE_ONLY", "APPROVED", "EFFECTIVE"):
            _fail("EXISTING_AUTHORITY_STATUS_INVALID")
        if (
            type(authority_id) is not str
            or expected[kind][2].fullmatch(authority_id) is None
            or type(signature_sha256) is not str
            or _SHA256.fullmatch(signature_sha256) is None
            or type(record["authority_source"]) is not str
            or not record["authority_source"]
        ):
            _fail("EXISTING_AUTHORITY_IDENTITY_INVALID")
        if status == "CANDIDATE_ONLY":
            continue
        approved_count += 1
        generated_id, generated_sha256, _ = expected[kind]
        if signature_sha256 == generated_sha256:
            _fail(f"NEW_AUTHORITY_REQUIRED_STALE:{kind}")
        if authority_id == generated_id:
            _fail(f"AUTHORITY_ID_COLLISION_DIFFERENT_SEMANTICS:{kind}")
    return approved_count


def _validate_signature_scientific_boundaries(
    family: Mapping[str, Any], rule: Mapping[str, Any]
) -> None:
    for name, signature in (("family", family), ("rule", rule)):
        formed_event = signature.get("formed_protein_ligand_event")
        if (
            not isinstance(formed_event, Mapping)
            or formed_event.get("formed_bond_order_authority_status")
            != _NOT_ESTABLISHED
            or "formed_bond_order" in formed_event
            or "bond_order" in formed_event
        ):
            _fail(
                "PROTEIN_LIGAND_FORMED_BOND_ORDER_AUTHORITY_"
                f"NOT_ESTABLISHED_REQUIRED:{name}"
            )
        if signature.get("pre_reaction_graph_authority_status") != _NOT_ESTABLISHED:
            _fail(f"PRE_REACTION_GRAPH_AUTHORITY_NOT_ESTABLISHED_REQUIRED:{name}")
        if (
            signature.get("pre_reaction_bond_order_authority_status")
            != _NOT_ESTABLISHED
        ):
            _fail(
                "PRE_REACTION_BOND_ORDER_AUTHORITY_NOT_ESTABLISHED_REQUIRED:"
                + name
            )
        if signature.get("mechanism_claim_status") != _NOT_CLAIMED:
            _fail(f"MECHANISM_NOT_CLAIMED_REQUIRED:{name}")
        if signature.get("reversibility_claim_status") != _NOT_CLAIMED:
            _fail(f"REVERSIBILITY_NOT_CLAIMED_REQUIRED:{name}")

    if rule.get("active_warhead_atom_contract") != [
        {
            "atom_id": "C21",
            "element": "C",
            "atom_role": "LIGAND_REACTIVE_CENTER",
        },
        {
            "atom_id": "O22",
            "element": "O",
            "atom_role": "ACTIVE_WARHEAD_OXYGEN",
        },
    ]:
        _fail("K36_ACTIVE_WARHEAD_CONTRACT_NOT_EXACT_C21_O22")
    if rule.get("masked_precursor_provenance") != {
        "atom_ids": ["O1", "O2", "O3", "S1"],
        "included_in_active_warhead": False,
        "establishes_pre_reaction_graph_authority": False,
    }:
        _fail("K36_MASKED_PRECURSOR_PROVENANCE_NOT_EXACT")
    if rule.get("ligand_reactive_atom") != {
        "atom_id": "C21",
        "element": "C",
    }:
        _fail("K36_LIGAND_REACTIVE_ATOM_NOT_EXACT_C21")
    component_boundary = rule.get("retained_framework_boundary")
    if component_boundary != {
        "edge_kind": "COMPONENT_INTERNAL_RETAINED_FRAMEWORK_BOUNDARY",
        "scaffold_side_atom_id": "C20",
        "warhead_side_atom_id": "C21",
        "bond_order": "single",
        "component_internal_topology_edge": True,
    }:
        _fail("K36_COMPONENT_BOUNDARY_NOT_EXACT_C20_C21_SINGLE")
    protein_event = rule.get("formed_protein_ligand_event")
    if not isinstance(protein_event, Mapping) or (
        protein_event.get("protein_endpoint")
        != {"residue_component_id": "CYS", "atom_id": "SG"}
        or protein_event.get("ligand_endpoint")
        != {"ligand_component_id": "K36", "atom_id": "C21"}
        or protein_event.get("component_internal_topology_edge") is not False
    ):
        _fail("K36_PROTEIN_LIGAND_EVENT_NOT_EXACT_SG_C21")
    if component_boundary == protein_event:
        _fail("COMPONENT_AND_PROTEIN_BOUNDARY_CONFUSED")
    if rule.get("minimal_seed_supervision_provenance") != {
        "atom_ids": ["C20", "N19"],
        "included_in_chemistry_rule_matching": False,
    }:
        _fail("K36_MINIMAL_SEED_PROVENANCE_INVALID")


def validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
    result: Mapping[str, Any],
) -> None:
    """Fail closed unless a result is the exact deterministic K36 payload."""

    if type(result) is not dict or tuple(result) != _RESULT_FIELDS:
        _fail("K36_AUTHORITY_RESULT_FIELD_INVENTORY_INVALID")
    family_payload = result["reaction_family_authority"]
    rule_payload = result["warhead_rule_authority"]
    summary = result["creation_provenance_readiness_summary"]
    if (
        type(family_payload) is not dict
        or type(rule_payload) is not dict
        or tuple(family_payload) != _AUTHORITY_PAYLOAD_FIELDS
        or tuple(rule_payload) != _AUTHORITY_PAYLOAD_FIELDS
    ):
        _fail("K36_AUTHORITY_PAYLOAD_FIELD_INVENTORY_INVALID")
    if type(summary) is not dict or tuple(summary) != _SUMMARY_FIELDS:
        _fail("K36_AUTHORITY_SUMMARY_FIELD_INVENTORY_INVALID")

    family_signature = family_payload["canonical_semantic_signature"]
    rule_signature = rule_payload["canonical_semantic_signature"]
    if not isinstance(family_signature, Mapping) or not isinstance(
        rule_signature, Mapping
    ):
        _fail("K36_CANONICAL_SEMANTIC_SIGNATURE_MAPPING_REQUIRED")
    _validate_signature_scientific_boundaries(family_signature, rule_signature)

    expected_family_signature = _reaction_family_semantic_signature()
    expected_family_id = authority_id_from_semantic_signature_v1(
        "reaction_family", expected_family_signature
    )
    expected_rule_signature = _warhead_rule_semantic_signature(
        expected_family_id
    )
    expected_rule_id = authority_id_from_semantic_signature_v1(
        "warhead_rule", expected_rule_signature
    )
    expected = (
        (
            family_payload,
            "reaction_family",
            REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION,
            expected_family_signature,
            expected_family_id,
        ),
        (
            rule_payload,
            "warhead_rule",
            WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION,
            expected_rule_signature,
            expected_rule_id,
        ),
    )
    for payload, kind, schema, signature, authority_id in expected:
        digest = authority_semantic_signature_sha256_v1(signature)
        if (
            payload["authority_schema_version"] != schema
            or payload["authority_kind"] != kind
            or payload["authority_id"] != authority_id
            or payload["canonical_semantic_signature"] != signature
            or payload["canonical_semantic_signature_sha256"] != digest
            or tuple(payload["source_human_review_provenance"])
            != _PROVENANCE_FIELDS
            or payload["source_human_review_provenance"]
            != _expected_provenance()
        ):
            _fail(f"K36_{kind.upper()}_PAYLOAD_INVALID")
    if (
        rule_signature.get("reaction_family_authority_id")
        != family_payload["authority_id"]
    ):
        _fail("K36_FAMILY_RULE_LINKAGE_INVALID")

    collision = summary["existing_approved_authority_collision_check"]
    if (
        summary["creator_schema_version"] != CREATOR_SCHEMA_VERSION
        or summary["source_human_review_provenance"] != _expected_provenance()
        or type(collision) is not dict
        or collision.get("status") != "NO_APPROVED_AUTHORITY_COLLISION"
        or collision.get("baseline_sources_searched")
        != [dict(source) for source in EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1]
        or collision.get("baseline_approved_authority_count") != 0
        or collision.get("baseline_source_bytes_sha_bound") is not True
        or collision.get("baseline_sources_actually_parsed") is not True
        or collision.get("baseline_registry_candidate_only_verified") is not True
        or collision.get(
            "baseline_approval_worklist_zero_completed_verified"
        )
        is not True
        or collision.get(
            "baseline_effective_view_zero_family_rule_authority_verified"
        )
        is not True
        or type(collision.get("additional_approved_authority_count")) is not int
        or collision.get("additional_approved_authority_count") < 0
        or collision.get("candidate_only_authority_treated_as_approved") is not False
    ):
        _fail("K36_CREATION_PROVENANCE_OR_COLLISION_SUMMARY_INVALID")
    required_true = (
        "reaction_family_authority_payload_ready",
        "warhead_rule_authority_payload_ready",
    )
    required_false = (
        "reaction_family_authority_materialized",
        "warhead_rule_authority_materialized",
        "effective_authority_updated",
        "ingestion_executed",
        "training_supervision_authority_complete",
        "K2Z_identical_active_warhead_authority_count_claimed",
        "exact10_feature_semantics_reopened",
        "network_request_executed",
        "raw_downloaded",
        "topology_downloaded",
        "distance_bond_inference_used",
        "PRE_geometry_reconstruction_executed",
        "model_forward",
        "backward",
        "optimizer_step",
        "Trainer.fit",
        "RL",
    )
    if any(summary[field] is not True for field in required_true) or any(
        summary[field] is not False for field in required_false
    ):
        _fail("K36_READINESS_OR_EXECUTION_BOUNDARY_INVALID")
    if (
        summary["K2Z_principal_classification"]
        != "EMBEDDED_WARHEAD_IS_VALID_GENERAL_ROLE_PROFILE"
        or summary["K2Z_status"]
        != "PENDING_EMBEDDED_WARHEAD_MULTI_BOUNDARY_RUNTIME"
        or summary[
            "K2Z_confirmed_minimal_active_warhead_embedded_profile_count"
        ]
        != 1
        or summary[
            "K2Z_current11_exact_two_boundary_structural_precedent_count"
        ]
        != 5
        or summary["1ZB_status"] != "READY_FOR_HUMAN_APPROVAL"
    ):
        _fail("K36_FROZEN_ADJACENT_STATUS_INVALID")


def build_covapie_k36_w1_reaction_family_and_warhead_rule_authority_v1(
    *,
    completed_review_record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    sample_applicability: Sequence[Mapping[str, Any]],
    compiled_submission: Mapping[str, Any],
    existing_approved_authority_baseline_source_payloads: Mapping[
        str, bytes
    ],
    existing_authority_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build the exact reviewed K36 W1 authority payloads without disk I/O.

    ``existing_authority_records`` contains only additional records beyond the
    mandatory, byte-validated frozen baseline sources.
    """

    _validate_exact_k36_inputs(
        completed_review_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    family_signature = _reaction_family_semantic_signature()
    family_sha256 = authority_semantic_signature_sha256_v1(family_signature)
    family_id = authority_id_from_semantic_signature_v1(
        "reaction_family", family_signature
    )
    rule_signature = _warhead_rule_semantic_signature(family_id)
    rule_sha256 = authority_semantic_signature_sha256_v1(rule_signature)
    rule_id = authority_id_from_semantic_signature_v1(
        "warhead_rule", rule_signature
    )
    _validate_baseline_authority_source_payloads_v1(
        existing_approved_authority_baseline_source_payloads,
        generated_family_id=family_id,
        generated_rule_id=rule_id,
    )
    approved_count = _validate_existing_authority_records(
        existing_authority_records,
        family_id=family_id,
        family_signature_sha256=family_sha256,
        rule_id=rule_id,
        rule_signature_sha256=rule_sha256,
    )
    provenance = _expected_provenance()
    result = {
        "reaction_family_authority": {
            "authority_schema_version": REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION,
            "authority_kind": "reaction_family",
            "authority_id": family_id,
            "semantic_name": (
                "CYS_SG_TO_K36_C21_EXACT_CHEMISTRY_SIGNATURE_EVENT_V1"
            ),
            "canonical_semantic_signature": family_signature,
            "canonical_semantic_signature_sha256": family_sha256,
            "source_human_review_provenance": dict(provenance),
        },
        "warhead_rule_authority": {
            "authority_schema_version": WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION,
            "authority_kind": "warhead_rule",
            "authority_id": rule_id,
            "semantic_name": (
                "K36_C21_O22_ACTIVE_WARHEAD_EXACT_CHEMISTRY_SIGNATURE_RULE_V1"
            ),
            "canonical_semantic_signature": rule_signature,
            "canonical_semantic_signature_sha256": rule_sha256,
            "source_human_review_provenance": dict(provenance),
        },
        "creation_provenance_readiness_summary": {
            "creator_schema_version": CREATOR_SCHEMA_VERSION,
            "source_human_review_provenance": dict(provenance),
            "existing_approved_authority_collision_check": {
                "status": "NO_APPROVED_AUTHORITY_COLLISION",
                "baseline_sources_searched": [
                    dict(source)
                    for source in EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1
                ],
                "baseline_approved_authority_count": 0,
                "baseline_source_bytes_sha_bound": True,
                "baseline_sources_actually_parsed": True,
                "baseline_registry_candidate_only_verified": True,
                "baseline_approval_worklist_zero_completed_verified": True,
                "baseline_effective_view_zero_family_rule_authority_verified": True,
                "additional_approved_authority_count": approved_count,
                "candidate_only_authority_treated_as_approved": False,
            },
            "reaction_family_authority_payload_ready": True,
            "warhead_rule_authority_payload_ready": True,
            "reaction_family_authority_materialized": False,
            "warhead_rule_authority_materialized": False,
            "effective_authority_updated": False,
            "ingestion_executed": False,
            "training_supervision_authority_complete": False,
            "K2Z_principal_classification": (
                "EMBEDDED_WARHEAD_IS_VALID_GENERAL_ROLE_PROFILE"
            ),
            "K2Z_status": "PENDING_EMBEDDED_WARHEAD_MULTI_BOUNDARY_RUNTIME",
            "K2Z_confirmed_minimal_active_warhead_embedded_profile_count": 1,
            "K2Z_current11_exact_two_boundary_structural_precedent_count": 5,
            "K2Z_identical_active_warhead_authority_count_claimed": False,
            "1ZB_status": "READY_FOR_HUMAN_APPROVAL",
            "exact10_feature_semantics_reopened": False,
            "network_request_executed": False,
            "raw_downloaded": False,
            "topology_downloaded": False,
            "distance_bond_inference_used": False,
            "PRE_geometry_reconstruction_executed": False,
            "model_forward": False,
            "backward": False,
            "optimizer_step": False,
            "Trainer.fit": False,
            "RL": False,
        },
    }
    validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
        result
    )
    return result
