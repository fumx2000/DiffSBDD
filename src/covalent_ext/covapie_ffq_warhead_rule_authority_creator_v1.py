"""Compile the approved FFQ project-level warhead-rule authority in memory.

The sole accepted input is the byte-exact project-level human-decision record.
The creator validates the complete approved component-bound rule, copies its
exact17 semantic object, derives the SHA-based final identity, and returns a
deterministic V2 wrapper.  It performs no filesystem, registry, runtime, or
training operation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping


__all__ = (
    "FFQWarheadRuleAuthorityValidationError",
    "ERROR_TOKEN",
    "CREATOR_SCHEMA_VERSION",
    "WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION",
    "HUMAN_DECISION_BYTE_COUNT",
    "HUMAN_DECISION_SHA256",
    "SOURCE_CANDIDATE_WARHEAD_RULE_ID",
    "CANDIDATE_CANONICAL_LOCAL_RULE_SHA256",
    "FINAL_REACTION_FAMILY_AUTHORITY_ID",
    "APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256",
    "FINAL_AUTHORITY_ID",
    "SEMANTIC_NAME",
    "canonical_authority_semantic_signature_json_v1",
    "authority_semantic_signature_sha256_v1",
    "authority_id_from_semantic_signature_v1",
    "validate_covapie_ffq_project_level_warhead_rule_human_decision_v1",
    "validate_covapie_ffq_warhead_rule_authority_payload_v2",
    "build_covapie_ffq_warhead_rule_authority_v1",
)


ERROR_TOKEN = "COVAPIE_FFQ_WARHEAD_RULE_AUTHORITY_CREATOR_V1_ERROR"
CREATOR_SCHEMA_VERSION = "covapie_ffq_warhead_rule_authority_creator_v1"
WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION = (
    "covapie_cys_sg_warhead_rule_authority_payload_v2"
)
HUMAN_DECISION_BYTE_COUNT = 37455
HUMAN_DECISION_SHA256 = (
    "d03d2d3d3d414beb195c8bddb0d11835661d88a43f813f1e3d86787b852737ea"
)
SOURCE_CANDIDATE_WARHEAD_RULE_ID = (
    "COVAPIE_CYS_SG_WARHEAD_RULE_B96D4E846C704691"
)
CANDIDATE_CANONICAL_LOCAL_RULE_SHA256 = (
    "b96d4e846c7046912da5b98b1bab6034785a3a4204ddf99e73ba4ce8f43522ff"
)
SOURCE_CANDIDATE_REACTION_FAMILY_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304"
)
FINAL_REACTION_FAMILY_AUTHORITY_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
)
FAMILY_AUTHORITY_FILE_SHA256 = (
    "d79658a33d910e7ca828247706d2690697c9e988f66fac53c8265fae020b7f62"
)
FAMILY_AUTHORITY_RECEIPT_SHA256 = (
    "e8d2b03ddde42cc60bb2833861e1f7f26e7f87c751e4486bc16d9af48bde3780"
)
FAMILY_AUTHORITY_SEMANTIC_SIGNATURE_SHA256 = (
    "2fef2eddfc385c78f9386b5973984fd6df992416a950d5fa9cdfd6a07d485bc7"
)
APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256 = (
    "8162eff17624bd4a080e24e0a2537a840baa68c6c2f28cd78a91fbf23cc8998a"
)
FINAL_AUTHORITY_ID = "COVAPIE_CYS_SG_WARHEAD_RULE_8162EFF17624BD4A"
SEMANTIC_NAME = "CYS_SG_FFQ_FCN_EXACT_COMPONENT_ATOM_WARHEAD_RULE_V1"

_HUMAN_DECISION_SCHEMA_VERSION = (
    "covapie_ffq_project_level_warhead_rule_human_decision_v1"
)
_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
_DECISION_STATUS = "HUMAN_APPROVED_PROJECT_LEVEL_WARHEAD_RULE_DECISION"
_DECISION_ROLE = (
    "PROJECT_LEVEL_WARHEAD_RULE_HUMAN_APPROVAL_RECORD_NOT_AUTHORITY_PAYLOAD"
)
_OVERALL_DECISION = (
    "APPROVE_ALL_RECOMMENDED_PROJECT_LEVEL_WARHEAD_RULE_DECISIONS"
)
_APPROVAL_SCOPE = "PROJECT_LEVEL_WARHEAD_RULE_ONLY"
_ATTESTATION = "A–N 全部批准，按推荐值执行"
_APPROVED_AT_UTC = "2026-08-24T05:35:00Z"
_SEMANTIC_SIGNATURE_VERSION = (
    "covapie_cys_sg_warhead_rule_authority_semantic_signature_v1"
)
_LOCAL_SIGNATURE_VERSION = (
    "covapie_cys_sg_canonical_local_reaction_signature_v1"
)
_SCOPE_KIND = (
    "EXACT_CANONICAL_WARHEAD_RULE_SIGNATURE_PLUS_EXACT_COMPONENT_ATOM_CONTRACT"
)
_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
_ACTIVE_WARHEAD_SEMANTICS = "REACTION_COMPETENT_ACTIVE_WARHEAD_V1"
_NOT_ESTABLISHED = "NOT_ESTABLISHED"
_NOT_CLAIMED = "NOT_CLAIMED"
_SOURCE_WARHEAD_RULE_CANDIDATE_EVIDENCE_SHA256 = (
    "43ec40ab9d11adf9c28278cc3986103f02f8b5144aac968951c0c2bab7c30d5a"
)
_SOURCE_FORMAL_SAMPLE_HUMAN_DECISION_SHA256 = (
    "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149"
)

_SEMANTIC_FIELDS = (
    "semantic_signature_version",
    "authority_kind",
    "reaction_family_authority_id",
    "applicability_scope",
    "target_condition",
    "ligand_reactive_atom_contract",
    "active_warhead_semantics",
    "active_warhead_atom_contract",
    "canonical_local_warhead_rule_contract",
    "precursor_local_reaction_evidence_contract",
    "retained_role_profile",
    "retained_framework_boundary",
    "formed_protein_ligand_event",
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
    "source_candidate_warhead_rule_id",
    "candidate_canonical_local_rule_sha256",
    "final_warhead_rule_authority_id",
    "warhead_rule_authority_semantic_signature_sha256",
    "source_candidate_reaction_family_id",
    "final_reaction_family_authority_id",
    "source_warhead_rule_candidate_evidence_sha256",
    "source_formal_sample_human_decision_sha256",
    "source_materialized_family_authority_file_sha256",
    "source_materialized_family_authority_receipt_sha256",
    "project_level_warhead_rule_human_decision_record_sha256",
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
    "warhead_rule_authority",
    "creation_readiness_summary",
)
_SUMMARY_FIELDS = (
    "creator_schema_version",
    "source_human_decision_sha256",
    "project_level_warhead_rule_human_decision_consumed",
    "human_decision_modified",
    "reaction_family_authority_dependency_verified",
    "reaction_family_registration_performed",
    "warhead_rule_authority_payload_ready",
    "warhead_rule_authority_payload_built_in_memory",
    "warhead_rule_creator_implemented",
    "persisted_warhead_rule_authority_created",
    "warhead_rule_authority_created",
    "warhead_rule_registration_performed",
    "authority_file_materialized",
    "effective_authority_updated",
    "runtime_authority_created",
    "runtime_auto_admission_authorized",
    "generic_warhead_rule_identity_policy_published",
    "generic_warhead_rule_scope_contract_published",
    "SMARTS_generation_performed",
    "reusable_chemistry_authority_created",
    "reconciliation_changed",
    "tensorizer_integration_performed",
    "training_admission_created",
    "training_dataset_changed",
    "runtime_admission_changed",
    "split_changed",
    "feature_semantics_audit_required_before_formal_training",
    "feature_semantics_audit_performed",
    "ready_for_training",
    "training_performed",
    "commit_performed",
    "push_performed",
    "network_performed",
)

_SOURCE_BINDING_EXPECTATIONS = {
    "MATERIALIZED_FINAL_REACTION_FAMILY_AUTHORITY": (7778, FAMILY_AUTHORITY_FILE_SHA256),
    "MATERIALIZED_FINAL_REACTION_FAMILY_AUTHORITY_RECEIPT": (
        3581,
        FAMILY_AUTHORITY_RECEIPT_SHA256,
    ),
    "SOURCE_WARHEAD_RULE_CANDIDATE_EVIDENCE": (
        53581,
        _SOURCE_WARHEAD_RULE_CANDIDATE_EVIDENCE_SHA256,
    ),
    "SOURCE_SAMPLE_LEVEL_HUMAN_DECISION": (
        14197,
        _SOURCE_FORMAL_SAMPLE_HUMAN_DECISION_SHA256,
    ),
}


class FFQWarheadRuleAuthorityValidationError(ValueError):
    """Raised when the frozen FFQ warhead-rule contract is not exact."""


def _fail(reason: str) -> None:
    raise FFQWarheadRuleAuthorityValidationError(f"{ERROR_TOKEN}:{reason}")


def canonical_authority_semantic_signature_json_v1(value: object) -> str:
    """Return the K36-compatible canonical semantic JSON representation."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise FFQWarheadRuleAuthorityValidationError(
            f"{ERROR_TOKEN}:CANONICAL_JSON_INVALID"
        ) from error


def authority_semantic_signature_sha256_v1(value: object) -> str:
    """Hash only the canonical authority semantic signature."""

    canonical = canonical_authority_semantic_signature_json_v1(value)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def authority_id_from_semantic_signature_v1(value: object) -> str:
    """Derive the final warhead-rule ID from the approved semantics."""

    digest = authority_semantic_signature_sha256_v1(value)
    return "COVAPIE_CYS_SG_WARHEAD_RULE_" + digest[:16].upper()


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"HUMAN_DECISION_DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    _fail(f"HUMAN_DECISION_NONFINITE_JSON:{value}")


def _exact_dict_keys(
    value: object, fields: tuple[str, ...], reason: str
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(fields) or len(value) != len(fields):
        _fail(reason)
    return value


def _exact_ordered_dict(
    value: object, fields: tuple[str, ...], reason: str
) -> dict[str, Any]:
    if type(value) is not dict or tuple(value) != fields:
        _fail(reason)
    return value


def _expected_target() -> dict[str, object]:
    return {
        "residue_component_id": "CYS",
        "residue_atom_id": "SG",
        "residue_atom_element": "S",
    }


def _expected_ligand_reactive_atom() -> dict[str, object]:
    return {
        "atom_id": "C1",
        "atom_role": "LIGAND_REACTIVE_CENTER",
        "element": "C",
        "ligand_component_id": "FFQ",
    }


def _expected_active_warhead_atoms() -> list[dict[str, object]]:
    return [
        {
            "atom_id": "C1",
            "atom_role": "LIGAND_REACTIVE_CENTER",
            "element": "C",
            "ligand_component_id": "FFQ",
        },
        {
            "atom_id": "C2",
            "atom_role": "ACTIVE_WARHEAD_RETAINED_MEMBER",
            "element": "C",
            "ligand_component_id": "FFQ",
        },
        {
            "atom_id": "C3",
            "atom_role": "ACTIVE_WARHEAD_RETAINED_MEMBER",
            "element": "C",
            "ligand_component_id": "FFQ",
        },
        {
            "atom_id": "O1",
            "atom_role": "ACTIVE_WARHEAD_RETAINED_MEMBER",
            "element": "O",
            "ligand_component_id": "FFQ",
        },
    ]


def _expected_boundary(*, include_edge_kind: bool) -> dict[str, object]:
    result: dict[str, object] = {}
    if include_edge_kind:
        result["edge_kind"] = "COMPONENT_INTERNAL_RETAINED_FRAMEWORK_BOUNDARY"
    result.update(
        {
            "ligand_component_id": "FFQ",
            "scaffold_side_atom_id": "P1",
            "warhead_side_atom_id": "C2",
            "bond_order": "single",
            "component_internal_topology_edge": True,
        }
    )
    return result


def _expected_local_atoms() -> list[dict[str, object]]:
    return [
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


def _expected_local_bonds() -> list[dict[str, object]]:
    return [
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
            "projected_disposition": "removed_precursor_internal_heavy_bond",
        },
        {
            "canonical_endpoint_1": "local_atom_002",
            "canonical_endpoint_2": "local_atom_003",
            "normalized_bond_order": "single",
            "projected_disposition": "retained_observed_bond",
        },
    ]


def _expected_local_rule() -> dict[str, object]:
    return {
        "canonical_signature_version": _LOCAL_SIGNATURE_VERSION,
        "center_atom": {
            "canonical_local_atom_id": "center",
            "element": "C",
            "formal_charge": 0,
            "reactive": True,
        },
        "local_atoms": _expected_local_atoms(),
        "local_bonds": _expected_local_bonds(),
        "reaction_delta": {
            "leaving_group_count": 0,
            "leaving_group_elements": [],
            "reaction_delta_class": "intact_parent_atom_inventory_match",
        },
        "rule_kind": "canonical_local_graph_exact_match_v1",
        "selected_signature_radius": 1,
        "target_condition": {
            "formed_bond_order": "single",
            "residue": "CYS",
            "residue_atom": "SG",
        },
    }


def _expected_local_contract() -> dict[str, object]:
    return {
        "canonical_local_rule": _expected_local_rule(),
        "canonical_local_rule_sha256": CANDIDATE_CANONICAL_LOCAL_RULE_SHA256,
        "contract_kind": "EXACT_CANONICAL_LOCAL_WARHEAD_RULE_SIGNATURE_MATCH_V1",
        "exact_match_required": True,
    }


def _expected_applicability_scope() -> dict[str, object]:
    return {
        "all_applicability_constraints_conjunctive": True,
        "canonical_local_rule_signature_alone_sufficient": False,
        "component_identity_alone_sufficient": False,
        "cross_signature_propagation_allowed": False,
        "exact_component_atom_contract_required": True,
        "exact_local_rule_signature_required": True,
        "require_exact_precursor_local_reaction_evidence_contract": True,
        "required_active_warhead_atom_ids": ["C1", "C2", "C3", "O1"],
        "required_canonical_local_rule_sha256": (
            CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        ),
        "required_canonical_local_rule_signature_version": (
            _LOCAL_SIGNATURE_VERSION
        ),
        "required_ligand_component_id": "FFQ",
        "required_ligand_reactive_atom_id": "C1",
        "required_precursor_component_id": "FCN",
        "required_precursor_reactive_atom_id": "C2",
        "required_retained_framework_boundary": _expected_boundary(
            include_edge_kind=False
        ),
        "required_retained_role_profile": _ROLE_PROFILE,
        "scope_kind": _SCOPE_KIND,
    }


def _expected_precursor_contract() -> dict[str, object]:
    return {
        "all_precursor_heavy_atoms_retained": True,
        "establishes_mechanism_authority": False,
        "establishes_pre_reaction_bond_order_authority": False,
        "establishes_pre_reaction_graph_authority": False,
        "mapped_post_ligand_atom": {
            "atom_id": "C1",
            "element": "C",
            "ligand_component_id": "FFQ",
        },
        "mapping_status_requirement": (
            "UNIQUE_REACTIVE_CENTER_MAPPING_WITH_SYMMETRY_EQUIVALENT_"
            "FULL_ATOM_MAPPINGS"
        ),
        "precursor_component_id": "FCN",
        "precursor_reactive_atom": {
            "atom_id": "C2",
            "element": "C",
            "formal_charge": 0,
        },
        "reaction_delta": {
            "added_post_internal_heavy_bond_count": 0,
            "bond_order_change_count": 0,
            "formal_charge_change_count": 0,
            "heavy_atom_addition_count": 0,
            "heavy_atom_removal_count": 0,
            "leaving_group_count": 0,
            "leaving_group_elements": [],
            "reaction_delta_class": "intact_parent_atom_inventory_match",
            "removed_precursor_internal_heavy_bond_count": 1,
            "removed_precursor_internal_heavy_bonds": [
                {
                    "mapped_absent_post_atom_id_1": "C1",
                    "mapped_absent_post_atom_id_2": "O1",
                    "normalized_bond_order": "single",
                    "precursor_atom_id_1": "C2",
                    "precursor_atom_id_2": "O",
                }
            ],
        },
    }


def _expected_formed_event() -> dict[str, object]:
    return {
        "component_internal_topology_edge": False,
        "edge_kind": "PROTEIN_LIGAND_FORMED_COVALENT_EVENT",
        "formed_bond_order_authority_status": _NOT_ESTABLISHED,
        "ligand_endpoint": {
            "atom_id": "C1",
            "ligand_component_id": "FFQ",
        },
        "protein_endpoint": {
            "atom_id": "SG",
            "residue_component_id": "CYS",
        },
    }


def _validate_authority_semantics_v1(
    semantic: object, *, require_order: bool
) -> dict[str, Any]:
    if require_order:
        semantic = _exact_ordered_dict(
            semantic, _SEMANTIC_FIELDS, "SEMANTIC_FIELD_INVENTORY_INVALID"
        )
    else:
        semantic = _exact_dict_keys(
            semantic, _SEMANTIC_FIELDS, "SEMANTIC_FIELD_INVENTORY_INVALID"
        )
    if (
        semantic["semantic_signature_version"] != _SEMANTIC_SIGNATURE_VERSION
        or semantic["authority_kind"] != "warhead_rule"
        or semantic["reaction_family_authority_id"]
        != FINAL_REACTION_FAMILY_AUTHORITY_ID
        or semantic["applicability_scope"] != _expected_applicability_scope()
        or semantic["target_condition"] != _expected_target()
        or semantic["ligand_reactive_atom_contract"]
        != _expected_ligand_reactive_atom()
        or semantic["active_warhead_semantics"] != _ACTIVE_WARHEAD_SEMANTICS
        or semantic["active_warhead_atom_contract"]
        != _expected_active_warhead_atoms()
        or semantic["canonical_local_warhead_rule_contract"]
        != _expected_local_contract()
        or semantic["precursor_local_reaction_evidence_contract"]
        != _expected_precursor_contract()
        or semantic["retained_role_profile"] != _ROLE_PROFILE
        or semantic["retained_framework_boundary"]
        != _expected_boundary(include_edge_kind=True)
        or semantic["formed_protein_ligand_event"] != _expected_formed_event()
        or semantic["pre_reaction_graph_authority_status"] != _NOT_ESTABLISHED
        or semantic["pre_reaction_bond_order_authority_status"]
        != _NOT_ESTABLISHED
        or semantic["mechanism_claim_status"] != _NOT_CLAIMED
        or semantic["reversibility_claim_status"] != _NOT_CLAIMED
    ):
        _fail("APPROVED_EXACT17_SEMANTICS_INVALID")

    local_rule = semantic["canonical_local_warhead_rule_contract"][
        "canonical_local_rule"
    ]
    local_sha = authority_semantic_signature_sha256_v1(local_rule)
    if (
        local_sha != CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        or local_sha
        != semantic["canonical_local_warhead_rule_contract"][
            "canonical_local_rule_sha256"
        ]
        or local_sha
        != semantic["applicability_scope"][
            "required_canonical_local_rule_sha256"
        ]
    ):
        _fail("B96D_CANONICAL_LOCAL_RULE_SHA256_MISMATCH")

    digest = authority_semantic_signature_sha256_v1(semantic)
    if digest != APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256:
        _fail("APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256_MISMATCH")
    if authority_id_from_semantic_signature_v1(semantic) != FINAL_AUTHORITY_ID:
        _fail("FINAL_AUTHORITY_ID_DERIVATION_MISMATCH")
    canonical = canonical_authority_semantic_signature_json_v1(semantic)
    forbidden = (
        SOURCE_CANDIDATE_WARHEAD_RULE_ID,
        SOURCE_CANDIDATE_REACTION_FAMILY_ID,
        "source_candidate",
        "provenance",
        "SMARTS",
        "reusable_chemistry_authority",
    )
    if any(value in canonical for value in forbidden):
        _fail("PROVENANCE_OR_UNAUTHORIZED_AUTHORITY_INSIDE_SEMANTIC_HASH")
    return semantic


def _expected_candidate_provenance() -> dict[str, object]:
    return {
        "source_candidate_warhead_rule_id": SOURCE_CANDIDATE_WARHEAD_RULE_ID,
        "candidate_canonical_local_rule_sha256": (
            CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        ),
        "final_warhead_rule_authority_id": FINAL_AUTHORITY_ID,
        "warhead_rule_authority_semantic_signature_sha256": (
            APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        ),
        "source_candidate_reaction_family_id": (
            SOURCE_CANDIDATE_REACTION_FAMILY_ID
        ),
        "final_reaction_family_authority_id": (
            FINAL_REACTION_FAMILY_AUTHORITY_ID
        ),
        "source_warhead_rule_candidate_evidence_sha256": (
            _SOURCE_WARHEAD_RULE_CANDIDATE_EVIDENCE_SHA256
        ),
        "source_formal_sample_human_decision_sha256": (
            _SOURCE_FORMAL_SAMPLE_HUMAN_DECISION_SHA256
        ),
        "source_materialized_family_authority_file_sha256": (
            FAMILY_AUTHORITY_FILE_SHA256
        ),
        "source_materialized_family_authority_receipt_sha256": (
            FAMILY_AUTHORITY_RECEIPT_SHA256
        ),
        "project_level_warhead_rule_human_decision_record_sha256": (
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
        "project_level_warhead_rule_human_decision_consumed": True,
        "human_decision_modified": False,
        "reaction_family_authority_dependency_verified": True,
        "reaction_family_registration_performed": False,
        "warhead_rule_authority_payload_ready": True,
        "warhead_rule_authority_payload_built_in_memory": True,
        "warhead_rule_creator_implemented": True,
        "persisted_warhead_rule_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_rule_registration_performed": False,
        "authority_file_materialized": False,
        "effective_authority_updated": False,
        "runtime_authority_created": False,
        "runtime_auto_admission_authorized": False,
        "generic_warhead_rule_identity_policy_published": False,
        "generic_warhead_rule_scope_contract_published": False,
        "SMARTS_generation_performed": False,
        "reusable_chemistry_authority_created": False,
        "reconciliation_changed": False,
        "tensorizer_integration_performed": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "runtime_admission_changed": False,
        "split_changed": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "feature_semantics_audit_performed": False,
        "ready_for_training": False,
        "training_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "network_performed": False,
    }


def _validate_source_bindings_v1(bindings: object) -> None:
    if type(bindings) is not dict or len(bindings) != 11:
        _fail("SOURCE_BINDING_INVENTORY_INVALID")
    seen_roles: dict[str, Mapping[str, Any]] = {}
    fields = (
        "byte_count",
        "consumed_read_only",
        "path",
        "path_namespace",
        "sha256",
        "sha256_scope",
        "source_role",
    )
    for binding in bindings.values():
        binding = _exact_dict_keys(
            binding, fields, "SOURCE_BINDING_FIELD_INVENTORY_INVALID"
        )
        role = binding["source_role"]
        if type(role) is not str or role in seen_roles:
            _fail("SOURCE_BINDING_ROLE_INVALID")
        if (
            type(binding["byte_count"]) is not int
            or binding["byte_count"] <= 0
            or binding["consumed_read_only"] is not True
            or type(binding["path"]) is not str
            or not binding["path"]
            or binding["path_namespace"]
            not in ("covapie_state_relative", "repository_relative")
            or binding["sha256_scope"] != "file_bytes"
            or type(binding["sha256"]) is not str
            or len(binding["sha256"]) != 64
        ):
            _fail("SOURCE_BINDING_VALUE_INVALID")
        seen_roles[role] = binding
    for role, (byte_count, sha256) in _SOURCE_BINDING_EXPECTATIONS.items():
        if role not in seen_roles or (
            seen_roles[role]["byte_count"], seen_roles[role]["sha256"]
        ) != (byte_count, sha256):
            _fail(f"SOURCE_BINDING_MISMATCH:{role}")


def _validate_human_decision_document_v1(decision: object) -> dict[str, Any]:
    if type(decision) is not dict:
        _fail("HUMAN_DECISION_OBJECT_REQUIRED")
    if (
        decision.get("schema_version") != _HUMAN_DECISION_SCHEMA_VERSION
        or decision.get("decision_status") != _DECISION_STATUS
        or decision.get("decision_role") != _DECISION_ROLE
        or decision.get("review_unit_id") != _REVIEW_UNIT_ID
        or decision.get("project_level_warhead_rule_approval_created") is not True
        or decision.get("warhead_rule_authority_created") is not False
        or decision.get("warhead_rule_registration_performed") is not False
    ):
        _fail("HUMAN_DECISION_HEADER_OR_AUTHORITY_BOUNDARY_INVALID")
    _validate_source_bindings_v1(decision.get("source_bindings"))

    if decision.get("source_candidate_identity") != {
        "candidate_canonical_local_rule_sha256": (
            CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        ),
        "candidate_identity_role": (
            "SOURCE_PROVENANCE_ONLY_NOT_FINAL_AUTHORITY_IDENTITY"
        ),
        "candidate_status": "HUMAN_ACCEPTED_CANDIDATE_NOT_REGISTERED",
        "source_candidate_warhead_rule_id": SOURCE_CANDIDATE_WARHEAD_RULE_ID,
    }:
        _fail("SOURCE_CANDIDATE_IDENTITY_INVALID")

    family = decision.get("approved_family_authority_linkage")
    if family != {
        "effective_authority_updated": False,
        "family_linkage_human_approved": True,
        "materialized_family_authority_file_sha256": FAMILY_AUTHORITY_FILE_SHA256,
        "materialized_family_authority_receipt_sha256": (
            FAMILY_AUTHORITY_RECEIPT_SHA256
        ),
        "materialized_family_authority_semantic_sha256": (
            FAMILY_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        ),
        "reaction_family_authority_id_human_approved_for_rule_linkage": (
            FINAL_REACTION_FAMILY_AUTHORITY_ID
        ),
        "reaction_family_registration_performed": False,
        "runtime_authority_created": False,
        "source_candidate_reaction_family_id": (
            SOURCE_CANDIDATE_REACTION_FAMILY_ID
        ),
        "source_candidate_reaction_family_id_role": "PROVENANCE_ONLY",
    }:
        _fail("APPROVED_FAMILY_AUTHORITY_LINKAGE_INVALID")

    raw_semantic = _exact_dict_keys(
        decision.get("approved_canonical_warhead_rule_semantic_signature"),
        _SEMANTIC_FIELDS,
        "HUMAN_DECISION_SEMANTIC_FIELD_INVENTORY_INVALID",
    )
    semantic = {field: copy.deepcopy(raw_semantic[field]) for field in _SEMANTIC_FIELDS}
    _validate_authority_semantics_v1(semantic, require_order=True)
    if (
        decision.get("approved_warhead_rule_semantic_signature_sha256")
        != APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        or decision.get("approved_future_final_warhead_rule_authority_id")
        != FINAL_AUTHORITY_ID
        or decision.get(
            "final_warhead_rule_ID_human_approved_for_future_materialization"
        )
        is not True
        or decision.get("final_warhead_rule_authority_id_created") is not False
        or FINAL_AUTHORITY_ID == SOURCE_CANDIDATE_WARHEAD_RULE_ID
    ):
        _fail("APPROVED_SEMANTIC_IDENTITY_INVALID")

    semantic_contract = decision.get("approved_semantic_signature_contract")
    if (
        not isinstance(semantic_contract, Mapping)
        or semantic_contract.get("approved_semantic_signature_version")
        != _SEMANTIC_SIGNATURE_VERSION
        or semantic_contract.get("exact_top_level_field_count") != 17
        or semantic_contract.get("exact_top_level_fields") != list(_SEMANTIC_FIELDS)
        or semantic_contract.get("hash_algorithm") != "SHA256"
        or semantic_contract.get("hashed_object")
        != "approved_canonical_warhead_rule_semantic_signature"
        or semantic_contract.get("semantic_signature_human_approved") is not True
        or semantic_contract.get("semantic_signature_version_human_approved")
        is not True
        or semantic_contract.get("generic_semantic_contract_published") is not False
    ):
        _fail("APPROVED_SEMANTIC_SIGNATURE_CONTRACT_INVALID")

    if decision.get("approved_rule_identity_policy") != {
        "candidate_provenance_fields_outside_canonical_semantic_hash": True,
        "candidate_to_final_authority_linkage_required": True,
        "final_warhead_rule_authority_ID_policy_human_decision": (
            "DERIVE_FINAL_AUTHORITY_ID_FROM_CANONICAL_AUTHORITY_SEMANTIC_SIGNATURE"
        ),
        "generic_warhead_rule_identity_policy_published": False,
        "identity_policy_human_approved": True,
        "source_candidate_ID_is_final_authority_ID_by_definition": False,
        "source_candidate_identity_preserved_as_provenance": True,
    }:
        _fail("APPROVED_RULE_IDENTITY_POLICY_INVALID")

    if decision.get("approved_candidate_to_authority_provenance") != {
        "approved_warhead_rule_semantic_signature_sha256": (
            APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        ),
        "candidate_canonical_local_rule_sha256": (
            CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        ),
        "candidate_to_final_rule_provenance_human_approved": True,
        "final_reaction_family_authority_id": FINAL_REACTION_FAMILY_AUTHORITY_ID,
        "future_final_warhead_rule_authority_id": FINAL_AUTHORITY_ID,
        "provenance_fields_outside_semantic_hash": True,
        "source_candidate_reaction_family_id": (
            SOURCE_CANDIDATE_REACTION_FAMILY_ID
        ),
        "source_candidate_warhead_rule_id": SOURCE_CANDIDATE_WARHEAD_RULE_ID,
    }:
        _fail("APPROVED_CANDIDATE_TO_AUTHORITY_PROVENANCE_INVALID")

    approved_scope = decision.get("approved_component_bound_applicability_scope")
    if not isinstance(approved_scope, Mapping) or dict(approved_scope) != {
        **_expected_applicability_scope(),
        "another_component_with_same_B96D_local_graph_automatically_in_scope": False,
        "component_and_rule_contract_both_required": True,
        "reusable_chemistry_authority_created": False,
        "runtime_matching_authorized": False,
        "same_component_identity_without_exact_B96D_rule_sufficient": False,
        "scope_human_approved": True,
    }:
        _fail("APPROVED_COMPONENT_BOUND_APPLICABILITY_SCOPE_INVALID")

    local_approval = decision.get("approved_local_warhead_rule_contract")
    if not isinstance(local_approval, Mapping) or dict(local_approval) != {
        **_expected_local_contract(),
        "applicability_scope_required_SHA256_matches": True,
        "canonical_local_rule_SHA256_independently_recomputed": (
            CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        ),
        "complete_B96D_local_rule_human_approved": True,
    }:
        _fail("APPROVED_LOCAL_WARHEAD_RULE_CONTRACT_INVALID")

    if decision.get("approved_atom_exact_warhead_contract") != {
        "active_warhead_atom_ids": ["C1", "C2", "C3", "O1"],
        "active_warhead_semantics": _ACTIVE_WARHEAD_SEMANTICS,
        "applicability_required_exact_atom_contract": True,
        "atom_exact_warhead_contract_human_approved": True,
        "generalized_to_all_epoxides": False,
        "generalized_to_all_fosfomycin_like_components": False,
        "generalized_to_all_phosphonates": False,
        "ligand_component_id": "FFQ",
        "reactive_atom": "C1",
    }:
        _fail("APPROVED_ATOM_EXACT_WARHEAD_CONTRACT_INVALID")

    precursor_approval = decision.get(
        "approved_precursor_and_reaction_delta_contract"
    )
    if not isinstance(precursor_approval, Mapping) or dict(precursor_approval) != {
        **_expected_precursor_contract(),
        "applicability_required_exact_source_bound_contract": True,
        "precursor_local_reaction_contract_human_approved": True,
    }:
        _fail("APPROVED_PRECURSOR_REACTION_DELTA_CONTRACT_INVALID")

    if decision.get("approved_retained_role_and_boundary_contract") != {
        "applicability_required_exact_component_bound_contract": True,
        "boundary": _expected_boundary(include_edge_kind=False),
        "linker_atom_ids": [],
        "retained_role_and_boundary_contract_human_approved": True,
        "role_profile": _ROLE_PROFILE,
        "scaffold_atom_ids": ["O2", "O3", "O4", "P1"],
        "warhead_atom_ids": ["C1", "C2", "C3", "O1"],
    }:
        _fail("APPROVED_RETAINED_ROLE_AND_BOUNDARY_INVALID")

    if decision.get("approved_formed_bond_scope_semantics") != {
        "formed_bond_order_independent_project_authority_status": _NOT_ESTABLISHED,
        "formed_bond_order_scope_discriminator_human_approved": True,
        "formed_bond_order_scope_match_required": True,
        "formed_bond_order_scope_match_role": (
            "NON_AUTHORITATIVE_CLASSIFICATION_DISCRIMINATOR"
        ),
        "formed_bond_order_scope_match_value": "single",
        "independent_formed_bond_order_authority_created": False,
    }:
        _fail("APPROVED_FORMED_BOND_SCOPE_SEMANTICS_INVALID")
    if decision.get("approved_PRE_authority_status") != {
        "PRE_authority_created": False,
        "PRE_status_human_approved": True,
        "pre_reaction_bond_order_authority_status": _NOT_ESTABLISHED,
        "pre_reaction_graph_authority_status": _NOT_ESTABLISHED,
    }:
        _fail("APPROVED_PRE_AUTHORITY_STATUS_INVALID")
    if decision.get("approved_mechanism_reversibility_status") != {
        "mechanism_claim_status": _NOT_CLAIMED,
        "mechanism_reversibility_status_human_approved": True,
        "reversibility_claim_status": _NOT_CLAIMED,
    }:
        _fail("APPROVED_MECHANISM_REVERSIBILITY_STATUS_INVALID")

    items = decision.get("human_review_items")
    if type(items) is not list or len(items) != 14:
        _fail("HUMAN_REVIEW_ITEM_INVENTORY_INVALID")
    if [item.get("item_id") for item in items if isinstance(item, Mapping)] != list(
        "ABCDEFGHIJKLMN"
    ) or any(
        type(item) is not dict
        or set(item)
        != {"human_approval_required", "human_response", "item_id", "question"}
        or item["human_approval_required"] is not True
        or item["human_response"] != "APPROVE"
        or type(item["question"]) is not str
        or not item["question"]
        for item in items
    ):
        _fail("HUMAN_REVIEW_EXACT14_APPROVAL_INVALID")
    approval = decision.get("human_approval")
    if (
        not isinstance(approval, Mapping)
        or approval.get("human_approval_required") is not True
        or approval.get("human_approval_recorded") is not True
        or approval.get("human_reviewer_id") != "fmx"
        or approval.get("human_attestation") != _ATTESTATION
        or approval.get("overall_project_warhead_rule_decision")
        != _OVERALL_DECISION
        or approval.get("approval_scope") != _APPROVAL_SCOPE
        or approval.get("approved_item_ids") != list("ABCDEFGHIJKLMN")
        or approval.get("approved_at_utc") != _APPROVED_AT_UTC
        or approval.get("approval_time_source")
        != "EXPLICIT_CHAT_APPROVAL_TURN_FROZEN_TIMESTAMP"
    ):
        _fail("HUMAN_APPROVAL_INVARIANTS_INVALID")

    mask = decision.get("canonical_V1_mask_boundary")
    if mask != {
        "FFQ_direct_profile_applicable_aliases": ["A", "B3", "C"],
        "FFQ_direct_profile_retained_not_applicable_aliases": ["B", "B2"],
        "mask_changed": False,
        "new_mask_added": False,
        "semantic_long_names": [
            "warhead_only",
            "linker_plus_warhead",
            "scaffold_plus_warhead",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "task_count": 5,
    }:
        _fail("CANONICAL_V1_MASK_BOUNDARY_INVALID")
    training = decision.get("training_boundary")
    if training != {
        "Step12D": "SMOKE_LEGALITY_CHECK_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "feature_semantics_audit_performed": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_training": False,
        "training_performed": False,
    }:
        _fail("TRAINING_BOUNDARY_INVALID")

    deferrals = decision.get("approved_downstream_deferrals")
    if not isinstance(deferrals, Mapping) or any(
        deferrals.get(field) is not expected
        for field, expected in {
            "SMARTS_generation_performed": False,
            "effective_authority_updated": False,
            "reusable_chemistry_authority_created": False,
            "runtime_authority_created": False,
            "training_performed": False,
            "family_rule_registration_deferred": True,
            "tensorizer_integration_deferred": True,
            "training_admission_deferred": True,
            "feature_semantics_audit_deferred_in_this_step": True,
        }.items()
    ):
        _fail("APPROVED_DOWNSTREAM_DEFERRALS_INVALID")
    materialization = decision.get("materialization_readiness_after_human_decision")
    if (
        not isinstance(materialization, Mapping)
        or materialization.get("principal_remaining_materialization_blocker")
        != "WARHEAD_RULE_AUTHORITY_CREATOR_NOT_IMPLEMENTED"
        or materialization.get("ready_for_warhead_rule_authority_creator_implementation")
        is not True
        or materialization.get("warhead_rule_authority_materialized") is not False
        or materialization.get("warhead_rule_creator_implemented") is not False
        or materialization.get("ready_for_training") is not False
    ):
        _fail("HUMAN_DECISION_MATERIALIZATION_READINESS_INVALID")
    boundary = decision.get("authority_boundary")
    if not isinstance(boundary, Mapping) or any(
        boundary.get(field) is not expected
        for field, expected in {
            "persisted_reaction_family_authority_created": True,
            "reaction_family_authority_created": True,
            "reaction_family_authority_file_consumed_read_only": True,
            "reaction_family_registration_performed": False,
            "project_level_warhead_rule_approval_created": True,
            "warhead_rule_authority_created": False,
            "warhead_rule_creator_implemented": False,
            "warhead_rule_registration_performed": False,
            "final_warhead_rule_authority_id_created": False,
            "effective_authority_updated": False,
            "runtime_authority_created": False,
            "SMARTS_generation_performed": False,
            "reusable_chemistry_authority_created": False,
            "reconciliation_changed": False,
            "tensorizer_integration_performed": False,
            "training_admission_created": False,
            "training_dataset_changed": False,
            "runtime_admission_changed": False,
            "split_changed": False,
            "training_performed": False,
            "commit_performed": False,
            "push_performed": False,
            "network_performed": False,
        }.items()
    ):
        _fail("HUMAN_DECISION_AUTHORITY_BOUNDARY_INVALID")
    return decision


def validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
    payload: bytes,
) -> dict[str, object]:
    """Validate and parse only the frozen byte-exact FFQ human decision."""

    if type(payload) is not bytes:
        _fail("HUMAN_DECISION_BYTES_REQUIRED")
    if len(payload) != HUMAN_DECISION_BYTE_COUNT:
        _fail("HUMAN_DECISION_BYTE_COUNT_MISMATCH")
    if hashlib.sha256(payload).hexdigest() != HUMAN_DECISION_SHA256:
        _fail("HUMAN_DECISION_SHA256_MISMATCH")
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        _fail("HUMAN_DECISION_TEXT_SAFETY_INVALID")
    try:
        decision = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonfinite,
        )
    except FFQWarheadRuleAuthorityValidationError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise FFQWarheadRuleAuthorityValidationError(
            f"{ERROR_TOKEN}:HUMAN_DECISION_JSON_INVALID"
        ) from error
    validated = _validate_human_decision_document_v1(decision)
    return copy.deepcopy(validated)


def validate_covapie_ffq_warhead_rule_authority_payload_v2(
    payload: object,
) -> None:
    """Fail closed unless ``payload`` is the exact approved V2 wrapper."""

    payload = _exact_dict_keys(
        payload,
        _AUTHORITY_PAYLOAD_FIELDS,
        "AUTHORITY_PAYLOAD_FIELD_INVENTORY_INVALID",
    )
    semantic = _validate_authority_semantics_v1(
        payload["canonical_semantic_signature"], require_order=False
    )
    candidate_provenance = _exact_dict_keys(
        payload["source_candidate_to_authority_provenance"],
        _CANDIDATE_PROVENANCE_FIELDS,
        "CANDIDATE_PROVENANCE_FIELD_INVENTORY_INVALID",
    )
    human_provenance = _exact_dict_keys(
        payload["source_human_review_provenance"],
        _HUMAN_PROVENANCE_FIELDS,
        "HUMAN_PROVENANCE_FIELD_INVENTORY_INVALID",
    )
    if (
        payload["authority_schema_version"]
        != WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION
        or payload["authority_kind"] != "warhead_rule"
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
        or candidate_provenance["source_candidate_warhead_rule_id"]
        == payload["authority_id"]
        or semantic["reaction_family_authority_id"]
        != candidate_provenance["final_reaction_family_authority_id"]
    ):
        _fail("AUTHORITY_PAYLOAD_IDENTITY_OR_PROVENANCE_INVALID")


def _validate_build_result_v1(result: object) -> None:
    result = _exact_ordered_dict(
        result, _RESULT_FIELDS, "BUILD_RESULT_FIELD_INVENTORY_INVALID"
    )
    validate_covapie_ffq_warhead_rule_authority_payload_v2(
        result["warhead_rule_authority"]
    )
    summary = _exact_ordered_dict(
        result["creation_readiness_summary"],
        _SUMMARY_FIELDS,
        "CREATION_SUMMARY_FIELD_INVENTORY_INVALID",
    )
    if summary != _expected_summary():
        _fail("CREATION_READINESS_SUMMARY_INVALID")


def build_covapie_ffq_warhead_rule_authority_v1(
    human_decision_payload: bytes,
) -> dict[str, object]:
    """Build and validate the approved FFQ rule entirely in memory."""

    decision = validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
        human_decision_payload
    )
    raw_semantic = decision[
        "approved_canonical_warhead_rule_semantic_signature"
    ]
    semantic = {
        field: copy.deepcopy(raw_semantic[field]) for field in _SEMANTIC_FIELDS
    }
    result = {
        "warhead_rule_authority": {
            "authority_schema_version": WARHEAD_RULE_AUTHORITY_SCHEMA_VERSION,
            "authority_kind": "warhead_rule",
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
