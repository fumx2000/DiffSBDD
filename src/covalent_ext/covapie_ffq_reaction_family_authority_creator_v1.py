"""Compile the approved FFQ project-level reaction-family authority in memory.

The sole accepted input is the byte-exact human-decision record frozen for
FFQ.  The creator validates that record, copies its approved semantic object,
derives the published SHA-based authority identity, and returns a deterministic
V2 wrapper.  It has no filesystem, registry, runtime, or training side effects.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping


__all__ = (
    "FFQReactionFamilyAuthorityValidationError",
    "ERROR_TOKEN",
    "CREATOR_SCHEMA_VERSION",
    "REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION",
    "HUMAN_DECISION_BYTE_COUNT",
    "HUMAN_DECISION_SHA256",
    "SOURCE_CANDIDATE_REACTION_FAMILY_ID",
    "CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256",
    "APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256",
    "FINAL_AUTHORITY_ID",
    "SEMANTIC_NAME",
    "canonical_authority_semantic_signature_json_v1",
    "authority_semantic_signature_sha256_v1",
    "authority_id_from_semantic_signature_v1",
    "validate_covapie_ffq_project_level_reaction_family_human_decision_v1",
    "validate_covapie_ffq_reaction_family_authority_payload_v2",
    "build_covapie_ffq_reaction_family_authority_v1",
)


ERROR_TOKEN = "COVAPIE_FFQ_REACTION_FAMILY_AUTHORITY_CREATOR_V1_ERROR"
CREATOR_SCHEMA_VERSION = "covapie_ffq_reaction_family_authority_creator_v1"
REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION = (
    "covapie_cys_sg_reaction_family_authority_payload_v2"
)
HUMAN_DECISION_BYTE_COUNT = 32668
HUMAN_DECISION_SHA256 = (
    "eb2e98e25459759b4b40588310ad16a42cb280f1155d599e340f5863574d0d51"
)
SOURCE_CANDIDATE_REACTION_FAMILY_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304"
)
CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256 = (
    "b1fd795d4d4423046be748d3421a2f1cfceb1f4dfbc4b44924afbb8de52d87de"
)
APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256 = (
    "2fef2eddfc385c78f9386b5973984fd6df992416a950d5fa9cdfd6a07d485bc7"
)
FINAL_AUTHORITY_ID = "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
SEMANTIC_NAME = (
    "CYS_SG_TO_LIGAND_REACTIVE_CARBON_"
    "EXACT_CANONICAL_REACTION_FAMILY_SIGNATURE_ONLY_V1"
)

_HUMAN_DECISION_SCHEMA_VERSION = (
    "covapie_ffq_project_level_reaction_family_human_decision_v1"
)
_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
_DECISION_STATUS = "HUMAN_APPROVED_PROJECT_LEVEL_REACTION_FAMILY_DECISION"
_DECISION_ROLE = (
    "PROJECT_LEVEL_REACTION_FAMILY_HUMAN_APPROVAL_RECORD_"
    "NOT_AUTHORITY_PAYLOAD"
)
_OVERALL_DECISION = (
    "APPROVE_ALL_RECOMMENDED_PROJECT_LEVEL_REACTION_FAMILY_DECISIONS"
)
_APPROVAL_SCOPE = "PROJECT_LEVEL_REACTION_FAMILY_ONLY"
_ATTESTATION = "A–M 全部批准，按推荐值执行"
_APPROVED_AT_UTC = "2026-08-24T03:19:00Z"
_SCOPE_KIND = "EXACT_CANONICAL_REACTION_FAMILY_SIGNATURE_ONLY"
_LOCAL_SIGNATURE_VERSION = (
    "covapie_cys_sg_canonical_local_reaction_signature_v1"
)
_SEMANTIC_SIGNATURE_VERSION = (
    "covapie_cys_sg_reaction_family_authority_semantic_signature_v1"
)
_NOT_ESTABLISHED = "NOT_ESTABLISHED"
_NOT_CLAIMED = "NOT_CLAIMED"
_SOURCE_CANDIDATE_EVIDENCE_SHA256 = (
    "18ec837b93ac2271ccf99509417fc5c2fef699c9d7f0c36fffcedf6f4ab69193"
)
_SOURCE_FORMAL_SAMPLE_HUMAN_DECISION_SHA256 = (
    "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149"
)
_SOURCE_FFQ_INGESTION_SNAPSHOT_SHA256 = (
    "6b7c7f4f4c93782d4b61b43cc698372981ec078000fd28207b97294a3694f977"
)

_SEMANTIC_FIELDS = (
    "semantic_signature_version",
    "authority_kind",
    "applicability_scope",
    "target_condition",
    "ligand_reactive_atom_contract",
    "formed_protein_ligand_event",
    "canonical_local_reaction_family_scope_contract",
    "pre_reaction_graph_authority_status",
    "pre_reaction_bond_order_authority_status",
    "mechanism_claim_status",
    "reversibility_claim_status",
)
_AUTHORITY_PAYLOAD_FIELDS = (
    "authority_schema_version",
    "authority_kind",
    "authority_id",
    "semantic_name",
    "canonical_semantic_signature",
    "canonical_semantic_signature_sha256",
    "source_candidate_to_authority_provenance",
    "source_human_review_provenance",
)
_CANDIDATE_PROVENANCE_FIELDS = (
    "source_candidate_reaction_family_id",
    "candidate_canonical_family_signature_sha256",
    "final_authority_id",
    "authority_semantic_signature_sha256",
    "source_candidate_evidence_sha256",
    "source_formal_sample_human_decision_sha256",
    "source_FFQ_ingestion_snapshot_sha256",
    "project_level_family_human_decision_record_sha256",
)
_HUMAN_PROVENANCE_FIELDS = (
    "source_review_unit_id",
    "source_project_level_human_decision_sha256",
    "source_reviewer_id",
    "source_attestation",
    "source_overall_decision",
    "source_approval_scope",
    "source_approved_at_utc",
)
_RESULT_FIELDS = (
    "reaction_family_authority",
    "creation_readiness_summary",
)
_SUMMARY_FIELDS = (
    "creator_schema_version",
    "source_human_decision_sha256",
    "project_level_reaction_family_human_decision_consumed",
    "human_decision_modified",
    "reaction_family_authority_payload_ready",
    "reaction_family_authority_payload_built_in_memory",
    "persisted_reaction_family_authority_created",
    "reaction_family_registration_performed",
    "effective_authority_updated",
    "runtime_authority_created",
    "authority_file_materialized",
    "runtime_auto_admission_authorized",
    "generic_creator_implemented",
    "generic_identity_policy_published",
    "generic_scope_contract_published",
    "warhead_rule_authority_created",
    "warhead_rule_review_started",
    "reusable_chemistry_authority_created",
    "SMARTS_generation_performed",
    "reconciliation_changed",
    "tensorizer_integration_performed",
    "training_admission_created",
    "training_dataset_changed",
    "runtime_admission_changed",
    "split_changed",
    "feature_semantics_audit_required_before_formal_training",
    "ready_for_training",
    "training_performed",
    "commit_performed",
    "push_performed",
    "network_performed",
)

_SOURCE_BINDING_SHA256 = {
    "FFQ_REACTION_FAMILY_CANDIDATE_EVIDENCE": (
        _SOURCE_CANDIDATE_EVIDENCE_SHA256
    ),
    "FORMAL_SAMPLE_LEVEL_HUMAN_DECISION": (
        _SOURCE_FORMAL_SAMPLE_HUMAN_DECISION_SHA256
    ),
    "PUBLISHED_FFQ_INGESTION_SNAPSHOT": (
        _SOURCE_FFQ_INGESTION_SNAPSHOT_SHA256
    ),
}


class FFQReactionFamilyAuthorityValidationError(ValueError):
    """Raised when the frozen FFQ authority contract is not exact."""


def _fail(reason: str) -> None:
    raise FFQReactionFamilyAuthorityValidationError(
        f"{ERROR_TOKEN}:{reason}"
    )


def canonical_authority_semantic_signature_json_v1(value: object) -> str:
    """Return the K36-compatible canonical JSON identity representation."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise FFQReactionFamilyAuthorityValidationError(
            f"{ERROR_TOKEN}:CANONICAL_JSON_INVALID"
        ) from error


def authority_semantic_signature_sha256_v1(value: object) -> str:
    """Hash only the canonical authority semantic signature."""

    canonical = canonical_authority_semantic_signature_json_v1(value)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def authority_id_from_semantic_signature_v1(value: object) -> str:
    """Derive the final reaction-family ID from approved semantics."""

    digest = authority_semantic_signature_sha256_v1(value)
    return "COVAPIE_CYS_SG_REACTION_FAMILY_" + digest[:16].upper()


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"HUMAN_DECISION_DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    _fail(f"HUMAN_DECISION_NONFINITE_JSON:{value}")


def _exact_dict(
    value: object, fields: tuple[str, ...], reason: str
) -> dict[str, Any]:
    if type(value) is not dict or tuple(value) != fields:
        _fail(reason)
    return value


def _expected_candidate_provenance() -> dict[str, object]:
    return {
        "source_candidate_reaction_family_id": (
            SOURCE_CANDIDATE_REACTION_FAMILY_ID
        ),
        "candidate_canonical_family_signature_sha256": (
            CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256
        ),
        "final_authority_id": FINAL_AUTHORITY_ID,
        "authority_semantic_signature_sha256": (
            APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        ),
        "source_candidate_evidence_sha256": (
            _SOURCE_CANDIDATE_EVIDENCE_SHA256
        ),
        "source_formal_sample_human_decision_sha256": (
            _SOURCE_FORMAL_SAMPLE_HUMAN_DECISION_SHA256
        ),
        "source_FFQ_ingestion_snapshot_sha256": (
            _SOURCE_FFQ_INGESTION_SNAPSHOT_SHA256
        ),
        "project_level_family_human_decision_record_sha256": (
            HUMAN_DECISION_SHA256
        ),
    }


def _expected_human_provenance() -> dict[str, object]:
    return {
        "source_review_unit_id": _REVIEW_UNIT_ID,
        "source_project_level_human_decision_sha256": HUMAN_DECISION_SHA256,
        "source_reviewer_id": "fmx",
        "source_attestation": _ATTESTATION,
        "source_overall_decision": _OVERALL_DECISION,
        "source_approval_scope": _APPROVAL_SCOPE,
        "source_approved_at_utc": _APPROVED_AT_UTC,
    }


def _expected_summary() -> dict[str, object]:
    return {
        "creator_schema_version": CREATOR_SCHEMA_VERSION,
        "source_human_decision_sha256": HUMAN_DECISION_SHA256,
        "project_level_reaction_family_human_decision_consumed": True,
        "human_decision_modified": False,
        "reaction_family_authority_payload_ready": True,
        "reaction_family_authority_payload_built_in_memory": True,
        "persisted_reaction_family_authority_created": False,
        "reaction_family_registration_performed": False,
        "effective_authority_updated": False,
        "runtime_authority_created": False,
        "authority_file_materialized": False,
        "runtime_auto_admission_authorized": False,
        "generic_creator_implemented": True,
        "generic_identity_policy_published": False,
        "generic_scope_contract_published": False,
        "warhead_rule_authority_created": False,
        "warhead_rule_review_started": False,
        "reusable_chemistry_authority_created": False,
        "SMARTS_generation_performed": False,
        "reconciliation_changed": False,
        "tensorizer_integration_performed": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "runtime_admission_changed": False,
        "split_changed": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_training": False,
        "training_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "network_performed": False,
    }


def _validate_local_family_scope_v1(scope: object) -> None:
    scope = _exact_dict(
        scope,
        (
            "contract_kind",
            "exact_match_required",
            "required_canonical_family_signature_object",
            "material_scope_match_dimensions",
        ),
        "LOCAL_SCOPE_FIELD_INVENTORY_INVALID",
    )
    if (
        scope["contract_kind"]
        != "EXACT_CANONICAL_LOCAL_REACTION_FAMILY_SIGNATURE_MATCH_V1"
        or scope["exact_match_required"] is not True
    ):
        _fail("LOCAL_SCOPE_CONTRACT_INVALID")

    required = _exact_dict(
        scope["required_canonical_family_signature_object"],
        (
            "canonical_signature_version",
            "leaving_group_disposition",
            "local_parent_graph_exact_match_rule",
            "observed_parent_delta",
            "selected_signature_radius",
            "target_condition",
        ),
        "REQUIRED_CANONICAL_FAMILY_FIELD_INVENTORY_INVALID",
    )
    required_sha = authority_semantic_signature_sha256_v1(required)
    if required_sha != CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256:
        _fail("REQUIRED_CANONICAL_FAMILY_SIGNATURE_SHA256_MISMATCH")

    rule = _exact_dict(
        required["local_parent_graph_exact_match_rule"],
        (
            "canonical_signature_version",
            "center_atom",
            "local_atoms",
            "local_bonds",
            "reaction_delta",
            "rule_kind",
            "selected_signature_radius",
            "target_condition",
        ),
        "LOCAL_EXACT_MATCH_RULE_FIELD_INVENTORY_INVALID",
    )
    center = {
        "canonical_local_atom_id": "center",
        "element": "C",
        "formal_charge": 0,
        "reactive": True,
    }
    local_atoms = [
        {
            "canonical_local_atom_id": "center",
            "element": "C",
            "formal_charge": 0,
            "is_leaving_group": False,
            "is_retained_observed": True,
            "relative_graph_distance": 0,
        },
        {
            "canonical_local_atom_id": "local_atom_001",
            "element": "C",
            "formal_charge": 0,
            "is_leaving_group": False,
            "is_retained_observed": True,
            "relative_graph_distance": 1,
        },
        {
            "canonical_local_atom_id": "local_atom_002",
            "element": "C",
            "formal_charge": 0,
            "is_leaving_group": False,
            "is_retained_observed": True,
            "relative_graph_distance": 1,
        },
        {
            "canonical_local_atom_id": "local_atom_003",
            "element": "O",
            "formal_charge": 0,
            "is_leaving_group": False,
            "is_retained_observed": True,
            "relative_graph_distance": 1,
        },
    ]
    local_bonds = [
        {
            "canonical_endpoint_1": "center",
            "canonical_endpoint_2": "local_atom_001",
            "normalized_bond_order": "single",
            "projected_disposition": "retained_observed_bond",
        },
        {
            "canonical_endpoint_1": "center",
            "canonical_endpoint_2": "local_atom_002",
            "normalized_bond_order": "single",
            "projected_disposition": "retained_observed_bond",
        },
        {
            "canonical_endpoint_1": "center",
            "canonical_endpoint_2": "local_atom_003",
            "normalized_bond_order": "single",
            "projected_disposition": (
                "removed_precursor_internal_heavy_bond"
            ),
        },
        {
            "canonical_endpoint_1": "local_atom_002",
            "canonical_endpoint_2": "local_atom_003",
            "normalized_bond_order": "single",
            "projected_disposition": "retained_observed_bond",
        },
    ]
    delta = {
        "leaving_group_count": 0,
        "leaving_group_elements": [],
        "reaction_delta_class": "intact_parent_atom_inventory_match",
    }
    target = {
        "formed_bond_order": "single",
        "residue": "CYS",
        "residue_atom": "SG",
    }
    leaving = {"allowed_elements": [], "required_count": 0}
    if (
        required["canonical_signature_version"] != _LOCAL_SIGNATURE_VERSION
        or required["selected_signature_radius"] != 1
        or required["target_condition"] != target
        or required["observed_parent_delta"] != delta
        or required["leaving_group_disposition"] != leaving
        or rule["canonical_signature_version"] != _LOCAL_SIGNATURE_VERSION
        or rule["rule_kind"] != "canonical_local_graph_exact_match_v1"
        or rule["selected_signature_radius"] != 1
        or rule["center_atom"] != center
        or rule["local_atoms"] != local_atoms
        or rule["local_bonds"] != local_bonds
        or rule["reaction_delta"] != delta
        or rule["target_condition"] != target
    ):
        _fail("REQUIRED_CANONICAL_FAMILY_EXACT_OBJECT_INVALID")

    material = _exact_dict(
        scope["material_scope_match_dimensions"],
        (
            "canonical_signature_version",
            "rule_kind",
            "selected_signature_radius",
            "center_reactive_atom",
            "radius_1_local_atoms",
            "radius_1_neighbor_element_multiset",
            "local_bonds",
            "formed_bond_order_scope_match_value",
            "formed_bond_order_scope_match_role",
            "formed_bond_order_scope_match_required",
            "formed_bond_order_independent_project_authority_status",
            "reaction_delta",
            "observed_parent_delta",
            "removed_precursor_internal_heavy_bond_count",
            "leaving_group_disposition",
            "target_condition",
        ),
        "MATERIAL_SCOPE_FIELD_INVENTORY_INVALID",
    )
    removed_count = sum(
        bond["projected_disposition"]
        == "removed_precursor_internal_heavy_bond"
        for bond in local_bonds
    )
    if (
        material["canonical_signature_version"] != _LOCAL_SIGNATURE_VERSION
        or material["rule_kind"] != "canonical_local_graph_exact_match_v1"
        or material["selected_signature_radius"] != 1
        or material["center_reactive_atom"] != center
        or material["radius_1_local_atoms"] != local_atoms
        or material["radius_1_neighbor_element_multiset"] != ["C", "C", "O"]
        or material["local_bonds"] != local_bonds
        or material["formed_bond_order_scope_match_value"] != "single"
        or material["formed_bond_order_scope_match_role"]
        != "NON_AUTHORITATIVE_CLASSIFICATION_DISCRIMINATOR"
        or material["formed_bond_order_scope_match_required"] is not True
        or material["formed_bond_order_independent_project_authority_status"]
        != _NOT_ESTABLISHED
        or material["reaction_delta"] != delta
        or material["observed_parent_delta"] != delta
        or material["removed_precursor_internal_heavy_bond_count"]
        != removed_count
        or removed_count != 1
        or material["leaving_group_disposition"] != leaving
        or material["target_condition"] != target
    ):
        _fail("MATERIAL_SCOPE_EXACT_OBJECT_INVALID")


def _validate_authority_semantics_v1(semantic: object) -> dict[str, Any]:
    semantic = _exact_dict(
        semantic, _SEMANTIC_FIELDS, "SEMANTIC_FIELD_INVENTORY_INVALID"
    )
    applicability = _exact_dict(
        semantic["applicability_scope"],
        (
            "scope_kind",
            "required_canonical_family_signature_version",
            "required_canonical_family_signature_sha256",
            "cross_signature_propagation_allowed",
        ),
        "APPLICABILITY_SCOPE_FIELD_INVENTORY_INVALID",
    )
    if (
        semantic["semantic_signature_version"] != _SEMANTIC_SIGNATURE_VERSION
        or semantic["authority_kind"] != "reaction_family"
        or applicability["scope_kind"] != _SCOPE_KIND
        or applicability["required_canonical_family_signature_version"]
        != _LOCAL_SIGNATURE_VERSION
        or applicability["required_canonical_family_signature_sha256"]
        != CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256
        or applicability["cross_signature_propagation_allowed"] is not False
    ):
        _fail("AUTHORITY_SCOPE_OR_SIGNATURE_VERSION_INVALID")
    if semantic["target_condition"] != {
        "residue_component_id": "CYS",
        "residue_atom_id": "SG",
        "residue_atom_element": "S",
    } or semantic["ligand_reactive_atom_contract"] != {
        "atom_element": "C",
        "atom_role": "LIGAND_REACTIVE_CARBON",
    }:
        _fail("TARGET_OR_LIGAND_REACTIVE_ATOM_CONTRACT_INVALID")
    if semantic["formed_protein_ligand_event"] != {
        "edge_kind": "PROTEIN_LIGAND_FORMED_COVALENT_EVENT",
        "protein_endpoint": "CYS:SG",
        "ligand_endpoint_role": "LIGAND_REACTIVE_CARBON",
        "formed_bond_order_authority_status": _NOT_ESTABLISHED,
        "component_internal_topology_edge": False,
    }:
        _fail("FORMED_PROTEIN_LIGAND_EVENT_INVALID")
    _validate_local_family_scope_v1(
        semantic["canonical_local_reaction_family_scope_contract"]
    )
    if (
        semantic["pre_reaction_graph_authority_status"] != _NOT_ESTABLISHED
        or semantic["pre_reaction_bond_order_authority_status"]
        != _NOT_ESTABLISHED
        or semantic["mechanism_claim_status"] != _NOT_CLAIMED
        or semantic["reversibility_claim_status"] != _NOT_CLAIMED
    ):
        _fail("PRE_MECHANISM_OR_REVERSIBILITY_BOUNDARY_INVALID")
    digest = authority_semantic_signature_sha256_v1(semantic)
    if digest != APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256:
        _fail("APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256_MISMATCH")
    if authority_id_from_semantic_signature_v1(semantic) != FINAL_AUTHORITY_ID:
        _fail("FINAL_AUTHORITY_ID_DERIVATION_MISMATCH")
    canonical = canonical_authority_semantic_signature_json_v1(semantic)
    if (
        SOURCE_CANDIDATE_REACTION_FAMILY_ID in canonical
        or "source_candidate" in canonical
        or "provenance" in canonical
        or "FFQ" in canonical
        or "FCN" in canonical
    ):
        _fail("PROVENANCE_OR_COMPONENT_IDENTITY_INSIDE_SEMANTIC_HASH")
    return semantic


def _validate_source_bindings_v1(bindings: object) -> None:
    if type(bindings) is not list or len(bindings) != 7:
        _fail("SOURCE_BINDING_INVENTORY_INVALID")
    roles: dict[str, Mapping[str, Any]] = {}
    fields = (
        "source_role",
        "path",
        "path_namespace",
        "byte_count",
        "sha256",
        "sha256_scope",
        "verification_status",
    )
    for item in bindings:
        item = _exact_dict(item, fields, "SOURCE_BINDING_FIELD_INVENTORY_INVALID")
        role = item["source_role"]
        if type(role) is not str or role in roles:
            _fail("SOURCE_BINDING_ROLE_INVALID")
        if (
            type(item["path"]) is not str
            or not item["path"]
            or item["path_namespace"]
            not in ("project_parent_relative", "repository_relative")
            or type(item["byte_count"]) is not int
            or item["byte_count"] <= 0
            or item["sha256_scope"] != "file_bytes"
            or item["verification_status"] != "MATCHED"
        ):
            _fail("SOURCE_BINDING_VALUE_INVALID")
        roles[role] = item
    for role, expected_sha in _SOURCE_BINDING_SHA256.items():
        if role not in roles or roles[role]["sha256"] != expected_sha:
            _fail(f"SOURCE_BINDING_SHA256_MISMATCH:{role}")


def _validate_human_decision_document_v1(
    decision: object,
) -> dict[str, Any]:
    if type(decision) is not dict:
        _fail("HUMAN_DECISION_OBJECT_REQUIRED")
    if (
        decision.get("schema_version") != _HUMAN_DECISION_SCHEMA_VERSION
        or decision.get("decision_status") != _DECISION_STATUS
        or decision.get("decision_role") != _DECISION_ROLE
        or decision.get("review_unit_id") != _REVIEW_UNIT_ID
        or decision.get("reaction_family_project_level_approval_created")
        is not True
        or decision.get("reaction_family_authority_created") is not False
        or decision.get("reaction_family_registration_performed") is not False
    ):
        _fail("HUMAN_DECISION_HEADER_OR_AUTHORITY_BOUNDARY_INVALID")
    _validate_source_bindings_v1(decision.get("source_bindings"))

    candidate = decision.get("source_candidate_identity")
    if candidate != {
        "source_candidate_reaction_family_id": (
            SOURCE_CANDIDATE_REACTION_FAMILY_ID
        ),
        "candidate_canonical_family_signature_sha256": (
            CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256
        ),
        "candidate_status": "HUMAN_ACCEPTED_CANDIDATE_NOT_REGISTERED",
        "source_candidate_is_final_authority": False,
        "candidate_renamed": False,
    }:
        _fail("SOURCE_CANDIDATE_IDENTITY_INVALID")

    identity_policy = decision.get("approved_identity_policy")
    if (
        not isinstance(identity_policy, Mapping)
        or identity_policy.get(
            "candidate_to_final_authority_ID_policy_human_decision"
        )
        != "DERIVE_FINAL_AUTHORITY_ID_FROM_CANONICAL_AUTHORITY_SEMANTIC_SIGNATURE"
        or identity_policy.get("identity_policy_human_approved") is not True
        or identity_policy.get(
            "source_candidate_ID_is_final_authority_ID_by_definition"
        )
        is not False
        or identity_policy.get(
            "source_candidate_identity_preserved_as_provenance"
        )
        is not True
        or identity_policy.get(
            "candidate_identity_and_final_authority_identity_are_distinct_namespaces"
        )
        is not True
        or identity_policy.get("candidate_to_authority_linkage_required")
        is not True
        or identity_policy.get(
            "candidate_provenance_fields_are_outside_authority_semantic_hash"
        )
        is not True
        or identity_policy.get("generic_identity_policy_published") is not False
    ):
        _fail("APPROVED_IDENTITY_POLICY_INVALID")

    semantic = _validate_authority_semantics_v1(
        decision.get("approved_canonical_authority_semantic_signature")
    )
    if (
        decision.get("human_approved_semantic_signature_version") is not True
        or decision.get("semantic_signature_human_approved") is not True
        or decision.get("approved_authority_semantic_signature_sha256")
        != APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        or decision.get("approved_future_final_authority_id")
        != FINAL_AUTHORITY_ID
        or FINAL_AUTHORITY_ID == SOURCE_CANDIDATE_REACTION_FAMILY_ID
    ):
        _fail("APPROVED_SEMANTIC_IDENTITY_INVALID")
    boundary = decision.get("approved_authority_semantic_hash_boundary")
    if (
        not isinstance(boundary, Mapping)
        or boundary.get("hash_algorithm") != "SHA256"
        or boundary.get("hashed_object")
        != "approved_canonical_authority_semantic_signature"
        or boundary.get("exact_top_level_field_count") != 11
        or boundary.get("exact_top_level_fields") != list(_SEMANTIC_FIELDS)
        or boundary.get(
            "candidate_provenance_fields_are_outside_authority_semantic_hash"
        )
        is not True
    ):
        _fail("APPROVED_SEMANTIC_HASH_BOUNDARY_INVALID")

    approved_link = decision.get("approved_candidate_to_authority_provenance")
    if approved_link != {
        "source_candidate_reaction_family_id": (
            SOURCE_CANDIDATE_REACTION_FAMILY_ID
        ),
        "candidate_canonical_family_signature_sha256": (
            CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256
        ),
        "future_final_authority_id": FINAL_AUTHORITY_ID,
        "approved_authority_semantic_signature_sha256": (
            APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        ),
        "candidate_to_final_authority_provenance_human_approved": True,
        "provenance_fields_outside_semantic_hash": True,
    }:
        _fail("APPROVED_CANDIDATE_TO_AUTHORITY_LINK_INVALID")

    approved_scope = decision.get("approved_applicability_scope")
    if not isinstance(approved_scope, Mapping) or dict(approved_scope) != {
        **semantic["applicability_scope"],
        "scope_human_approved": True,
        "reusable_chemistry_authority_created": False,
        "runtime_auto_admission_authorized": False,
    }:
        _fail("APPROVED_APPLICABILITY_SCOPE_INVALID")
    if decision.get("approved_local_scope_contract") != semantic[
        "canonical_local_reaction_family_scope_contract"
    ] or decision.get("complete_local_scope_object_human_approved") is not True:
        _fail("APPROVED_LOCAL_SCOPE_LINKAGE_INVALID")

    material = semantic[
        "canonical_local_reaction_family_scope_contract"
    ]["material_scope_match_dimensions"]
    formed = decision.get("approved_formed_bond_scope_semantics")
    if (
        not isinstance(formed, Mapping)
        or formed.get("formed_bond_order_scope_match_value")
        != material["formed_bond_order_scope_match_value"]
        or formed.get("formed_bond_order_scope_match_role")
        != material["formed_bond_order_scope_match_role"]
        or formed.get("formed_bond_order_scope_match_required") is not True
        or formed.get("formed_bond_order_scope_discriminator_human_approved")
        is not True
        or formed.get(
            "formed_bond_order_independent_project_authority_status"
        )
        != _NOT_ESTABLISHED
        or formed.get("independent_formed_bond_order_authority_created")
        is not False
    ):
        _fail("APPROVED_FORMED_BOND_SCOPE_SEMANTICS_INVALID")

    target = decision.get("approved_target_condition")
    if (
        not isinstance(target, Mapping)
        or target.get("target_condition_human_approved") is not True
        or target.get("family_target") != semantic["target_condition"]
        or target.get("ligand_reactive_atom_contract")
        != semantic["ligand_reactive_atom_contract"]
        or target.get(
            "FFQ_specific_atom_ID_included_in_canonical_family_authority_semantics"
        )
        is not False
    ):
        _fail("APPROVED_TARGET_CONDITION_INVALID")
    pre = decision.get("approved_PRE_authority_status")
    if (
        not isinstance(pre, Mapping)
        or pre.get("pre_reaction_graph_authority_status") != _NOT_ESTABLISHED
        or pre.get("pre_reaction_bond_order_authority_status")
        != _NOT_ESTABLISHED
        or pre.get("PRE_status_human_approved") is not True
        or pre.get("PRE_authority_created") is not False
    ):
        _fail("APPROVED_PRE_AUTHORITY_STATUS_INVALID")
    claims = decision.get("approved_mechanism_reversibility_status")
    if claims != {
        "mechanism_claim_status": _NOT_CLAIMED,
        "reversibility_claim_status": _NOT_CLAIMED,
        "mechanism_reversibility_status_human_approved": True,
    }:
        _fail("APPROVED_MECHANISM_REVERSIBILITY_STATUS_INVALID")

    items = decision.get("human_review_items")
    if type(items) is not list or len(items) != 13:
        _fail("HUMAN_REVIEW_ITEM_INVENTORY_INVALID")
    if [item.get("item_id") for item in items if isinstance(item, Mapping)] != list(
        "ABCDEFGHIJKLM"
    ) or any(
        type(item) is not dict
        or tuple(item) != ("item_id", "question", "human_response")
        or item["human_response"] != "APPROVE"
        for item in items
    ):
        _fail("HUMAN_REVIEW_EXACT13_APPROVAL_INVALID")
    approval = decision.get("human_approval")
    if (
        not isinstance(approval, Mapping)
        or approval.get("human_approval_required") is not True
        or approval.get("human_approval_recorded") is not True
        or approval.get("human_reviewer_id") != "fmx"
        or approval.get("human_attestation") != _ATTESTATION
        or approval.get("overall_project_family_decision") != _OVERALL_DECISION
        or approval.get("approval_scope") != _APPROVAL_SCOPE
        or approval.get("approved_item_ids") != list("ABCDEFGHIJKLM")
        or approval.get("approved_at_utc") != _APPROVED_AT_UTC
    ):
        _fail("HUMAN_APPROVAL_INVARIANTS_INVALID")

    deferrals = decision.get("approved_downstream_deferrals")
    if not isinstance(deferrals, Mapping) or any(
        deferrals.get(field) is not expected
        for field, expected in {
            "warhead_rule_review_deferred": True,
            "warhead_rule_authority_created": False,
            "warhead_rule_review_started": False,
            "SMARTS_deferred": True,
            "reusable_chemistry_authority_deferred": True,
            "runtime_auto_admission_deferred": True,
            "reconciliation_deferred": True,
            "tensorizer_integration_deferred": True,
            "training_admission_deferred": True,
            "SMARTS_generation_performed": False,
            "reusable_chemistry_authority_created": False,
            "runtime_auto_admission_authorized": False,
        }.items()
    ):
        _fail("APPROVED_DOWNSTREAM_DEFERRALS_INVALID")
    mask = decision.get("canonical_V1_mask_boundary")
    if mask != {
        "semantic_long_names": [
            "warhead_only",
            "linker_plus_warhead",
            "scaffold_plus_warhead",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "task_count": 5,
        "FFQ_direct_profile_applicable_aliases": ["A", "B3", "C"],
        "FFQ_direct_profile_retained_not_applicable_aliases": ["B", "B2"],
        "mask_changed": False,
        "new_mask_added": False,
    }:
        _fail("CANONICAL_V1_MASK_BOUNDARY_INVALID")
    materialization = decision.get(
        "materialization_readiness_after_human_decision"
    )
    if (
        not isinstance(materialization, Mapping)
        or materialization.get("reaction_family_authority_materialized")
        is not False
        or materialization.get("ready_for_training") is not False
        or materialization.get("generic_identity_policy_published") is not False
        or materialization.get("generic_scope_contract_published") is not False
        or materialization.get("generic_materializer_implemented") is not False
    ):
        _fail("HUMAN_DECISION_MATERIALIZATION_BOUNDARY_INVALID")
    authority_boundary = decision.get("authority_boundary")
    if not isinstance(authority_boundary, Mapping) or any(
        authority_boundary.get(field) is not False
        for field in (
            "reaction_family_authority_created",
            "reaction_family_registration_performed",
            "final_authority_id_created",
            "generic_identity_policy_published",
            "generic_scope_contract_published",
            "generic_materializer_implemented",
            "warhead_rule_authority_created",
            "warhead_rule_review_started",
            "reusable_chemistry_authority_created",
            "SMARTS_generation_performed",
            "reconciliation_changed",
            "tensorizer_integration_performed",
            "training_admission_created",
            "training_dataset_changed",
            "split_changed",
            "runtime_admission_changed",
            "training_performed",
            "commit_performed",
            "push_performed",
            "network_performed",
        )
    ):
        _fail("HUMAN_DECISION_AUTHORITY_BOUNDARY_INVALID")
    return decision


def validate_covapie_ffq_project_level_reaction_family_human_decision_v1(
    payload: bytes,
) -> dict[str, object]:
    """Validate and parse only the frozen byte-exact FFQ human decision."""

    if type(payload) is not bytes:
        _fail("HUMAN_DECISION_BYTES_REQUIRED")
    if len(payload) != HUMAN_DECISION_BYTE_COUNT:
        _fail("HUMAN_DECISION_BYTE_COUNT_MISMATCH")
    if hashlib.sha256(payload).hexdigest() != HUMAN_DECISION_SHA256:
        _fail("HUMAN_DECISION_SHA256_MISMATCH")
    try:
        text = payload.decode("utf-8")
        decision = json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonfinite,
        )
    except FFQReactionFamilyAuthorityValidationError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise FFQReactionFamilyAuthorityValidationError(
            f"{ERROR_TOKEN}:HUMAN_DECISION_JSON_INVALID"
        ) from error
    validated = _validate_human_decision_document_v1(decision)
    return copy.deepcopy(validated)


def validate_covapie_ffq_reaction_family_authority_payload_v2(
    payload: object,
) -> None:
    """Fail closed unless ``payload`` is the exact approved V2 wrapper."""

    payload = _exact_dict(
        payload,
        _AUTHORITY_PAYLOAD_FIELDS,
        "AUTHORITY_PAYLOAD_FIELD_INVENTORY_INVALID",
    )
    semantic = _validate_authority_semantics_v1(
        payload["canonical_semantic_signature"]
    )
    candidate_provenance = _exact_dict(
        payload["source_candidate_to_authority_provenance"],
        _CANDIDATE_PROVENANCE_FIELDS,
        "CANDIDATE_PROVENANCE_FIELD_INVENTORY_INVALID",
    )
    human_provenance = _exact_dict(
        payload["source_human_review_provenance"],
        _HUMAN_PROVENANCE_FIELDS,
        "HUMAN_PROVENANCE_FIELD_INVENTORY_INVALID",
    )
    if (
        payload["authority_schema_version"]
        != REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION
        or payload["authority_kind"] != "reaction_family"
        or payload["authority_id"] != FINAL_AUTHORITY_ID
        or payload["semantic_name"] != SEMANTIC_NAME
        or payload["canonical_semantic_signature_sha256"]
        != APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        or authority_semantic_signature_sha256_v1(semantic)
        != payload["canonical_semantic_signature_sha256"]
        or authority_id_from_semantic_signature_v1(semantic)
        != payload["authority_id"]
        or candidate_provenance != _expected_candidate_provenance()
        or human_provenance != _expected_human_provenance()
        or candidate_provenance["source_candidate_reaction_family_id"]
        == payload["authority_id"]
    ):
        _fail("AUTHORITY_PAYLOAD_IDENTITY_OR_PROVENANCE_INVALID")


def _validate_build_result_v1(result: object) -> None:
    result = _exact_dict(
        result, _RESULT_FIELDS, "BUILD_RESULT_FIELD_INVENTORY_INVALID"
    )
    validate_covapie_ffq_reaction_family_authority_payload_v2(
        result["reaction_family_authority"]
    )
    summary = _exact_dict(
        result["creation_readiness_summary"],
        _SUMMARY_FIELDS,
        "CREATION_SUMMARY_FIELD_INVENTORY_INVALID",
    )
    if summary != _expected_summary():
        _fail("CREATION_READINESS_SUMMARY_INVALID")


def build_covapie_ffq_reaction_family_authority_v1(
    human_decision_payload: bytes,
) -> dict[str, object]:
    """Build and validate the approved FFQ authority entirely in memory."""

    decision = (
        validate_covapie_ffq_project_level_reaction_family_human_decision_v1(
            human_decision_payload
        )
    )
    semantic = copy.deepcopy(
        decision["approved_canonical_authority_semantic_signature"]
    )
    result = {
        "reaction_family_authority": {
            "authority_schema_version": (
                REACTION_FAMILY_AUTHORITY_SCHEMA_VERSION
            ),
            "authority_kind": "reaction_family",
            "authority_id": FINAL_AUTHORITY_ID,
            "semantic_name": SEMANTIC_NAME,
            "canonical_semantic_signature": semantic,
            "canonical_semantic_signature_sha256": (
                APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
            ),
            "source_candidate_to_authority_provenance": (
                _expected_candidate_provenance()
            ),
            "source_human_review_provenance": _expected_human_provenance(),
        },
        "creation_readiness_summary": _expected_summary(),
    }
    _validate_build_result_v1(result)
    return result
