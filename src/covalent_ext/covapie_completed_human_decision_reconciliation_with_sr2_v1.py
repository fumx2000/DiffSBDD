"""Reconcile published SR2 completion through the unchanged generic owner.

This metadata-only successor loads the rich SR2 Exact4 authority through its
published ingestion owner, proves the narrow-projection and training-admission
boundaries, appends one source to the published with-GD1 chain, and reconciles
the fixed historical population in memory. It writes no artifact and creates
no census, queue, task-label, tensor, training-admission, or model authority.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_gd1_v1
    as gd1_predecessor,
)
from . import (
    covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1
    as sr2_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithSR2Error",
    "project_sr2_completed_decision_v1",
    "load_real_completed_decision_sources_with_sr2_v1",
    "reconcile_real_completed_human_decisions_with_sr2_v1",
)


_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    sr2_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_FORMAL_DECISION_BYTE_COUNT = sr2_ingestion_owner.FORMAL_BINDINGS[0][2]
_FORMAL_DECISION_SHA256 = sr2_ingestion_owner.FORMAL_BINDINGS[0][3]
_FORMAL_DECISION_SCHEMA = sr2_ingestion_owner.FORMAL_DECISION_SCHEMA
_FORMAL_SEMANTIC_SHA256 = (
    sr2_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_REVIEW_UNIT_ID = sr2_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_ROLE_PROFILE = sr2_ingestion_owner.EXPECTED_ROLE_PROFILE
_EVENT_IDS = sr2_ingestion_owner.EXPECTED_EVENT_IDS
_RANKS = sr2_ingestion_owner.EXPECTED_RANKS

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "22"
_PREDECESSOR_SOURCE_FACT_COUNTS = (
    8,
    16,
    8,
    9,
    8,
    8,
    8,
    7,
    6,
    5,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
)
_SUCCESSOR_SOURCE_FACT_COUNTS = (*_PREDECESSOR_SOURCE_FACT_COUNTS, 4)
_GENERIC_FACT_FIELDS = (
    "canonical_event_id",
    "review_unit_id",
    "human_review_completed",
    "legacy_completed_review_status",
    "task_relevance_disposition",
    "chemistry_disposition",
    "training_disposition",
    "human_training_excluded",
    "source_decision_schema",
    "source_decision_sha256",
    "source_binding_path",
)
_FORBIDDEN_GENERIC_FACT_ATTRIBUTES = (
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "role_profile",
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "boundary_bonds",
    "canonical_mask_applicability",
    "PRE_geometry",
    "PRE_topology",
    "PRE_status",
    "POST_geometry",
    "POST_distance",
    "engineered_surrogate_context",
    "target_directed_medicinal_covalent_context",
    "future_training_candidate",
    "future_training_admission_candidate",
    "future_training_admission_status",
    "training_use_allowed",
    "training_admission",
    "formal_training_admitted",
    "training_materialization_allowed",
    "tensor_target",
    "current_runtime_model_usable",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
)
_EXPECTED_DECISIONS = {
    "D1_task_relevance": "RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_candidate": "SELECT_CANDIDATE_15",
    "D5_training_use": "INCLUDE",
}
_BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 111,
    "completed_positive_unit_count": 17,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 139,
    "completed_total_unit_count": 22,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 199,
    "unreviewed_unit_count": 109,
}
_AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 143,
    "completed_total_unit_count": 23,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 195,
    "unreviewed_unit_count": 108,
}
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    (
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    )
)


class CompletedDecisionReconciliationWithSR2Error(ValueError):
    """Raised when the exact SR2 reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithSR2Error(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _prove_generic_fact_schema_v1() -> None:
    fields = tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)
    if fields != _GENERIC_FACT_FIELDS or len(fields) != 11:
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")


def _validate_rich_sr2_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove published rich SR2 authority before projection."""

    if (
        bound.get("formal_semantics_independently_validated") is not True
        or bound.get("formal_validator_provenance_identity_only") is not True
        or bound.get("formal_validator_imported") is not False
        or bound.get("formal_validator_executed") is not False
        or bound.get("formal_validator_subprocess_called") is not False
        or bound.get("formal_validator_runtime_dependency") is not False
    ):
        _fail("SR2_INGESTION_OWNER_OR_FORMAL_VALIDATOR_BOUNDARY_INVALID")

    formal = _require_mapping(bound.get("formal"), "SR2_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != _FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != sr2_ingestion_owner.FORMAL_RECORD_ROLE
        or formal.get("formal_decision_semantic_canonical_sha256")
        != _FORMAL_SEMANTIC_SHA256
        or formal.get("unsigned") is not False
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
        or formal.get("human_review_completed") is not True
        or formal.get("human_decision_created") is not True
        or formal.get("formal_authority_created") is not True
        or formal.get("formal_authority_is_human") is not True
        or formal.get("machine_approval") is not False
    ):
        _fail("SR2_FORMAL_COMPLETION_OR_SEMANTIC_DIGEST_INVALID")

    human = _require_mapping(
        formal.get("human_authorization"),
        "SR2_HUMAN_AUTHORIZATION_NOT_OBJECT",
    )
    unit = _require_mapping(
        formal.get("unit_human_decision"),
        "SR2_UNIT_DECISION_NOT_OBJECT",
    )
    if any(
        human.get(key) != value or unit.get(key) != value
        for key, value in _EXPECTED_DECISIONS.items()
    ):
        _fail("SR2_D1_D5_DECISIONS_INVALID")
    if (
        human.get("human_selected_role_candidate_index_0based") != 15
        or human.get("human_selected_role_profile") != _ROLE_PROFILE
        or human.get("human_choices_externally_authorized") is not True
        or human.get("formal_decision_authority_is_human") is not True
        or human.get("machine_approval_claimed") is not False
        or human.get("machine_scientific_authority_created") is not False
        or unit.get("exact_event_count") != _EVENT_COUNT
        or unit.get("completed_human_review_event_count") != _EVENT_COUNT
        or unit.get("seventh_decision_present") is not False
    ):
        _fail("SR2_HUMAN_SELECTION_OR_UNIT_COMPLETION_INVALID")

    expected_d6 = sr2_ingestion_owner.EXPECTED_D6
    d6_payload = expected_d6.encode("utf-8")
    approved_context = _require_mapping(
        formal.get("human_approved_context"),
        "SR2_D6_CONTEXT_NOT_OBJECT",
    )
    if (
        len(d6_payload) != sr2_ingestion_owner.EXPECTED_D6_BYTE_COUNT
        or generic._sha256(d6_payload)
        != sr2_ingestion_owner.EXPECTED_D6_SHA256
        or human.get("D6_scientific_context") != expected_d6
        or unit.get("D6_scientific_context") != expected_d6
        or approved_context.get("D6_scientific_context") != expected_d6
        or approved_context.get("D6_utf8_byte_count")
        != sr2_ingestion_owner.EXPECTED_D6_BYTE_COUNT
        or approved_context.get("D6_utf8_sha256")
        != sr2_ingestion_owner.EXPECTED_D6_SHA256
        or approved_context.get("D6_human_reviewed_and_accepted") is not True
        or approved_context.get("D6_human_authorized") is not True
        or approved_context.get("formal_decision_authority_is_human") is not True
        or approved_context.get("machine_scientific_authority_created") is not False
    ):
        _fail("SR2_D6_IDENTITY_OR_AUTHORITY_INVALID")

    identity = _require_mapping(
        formal.get("identity"), "SR2_IDENTITY_NOT_OBJECT"
    )
    if (
        identity.get("review_unit_id") != _REVIEW_UNIT_ID
        or identity.get("canonical_event_ids") != list(_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_RANKS)
        or identity.get("pdb_ids") != ["2QLQ", "2QQ7"]
        or identity.get("ligand_component_id") != "SR2"
        or identity.get("protein_reactive_atom") != "SG"
        or identity.get("ligand_reactive_atom") != "C51"
        or identity.get("exact_event_count") != _EVENT_COUNT
        or identity.get("explicit_covalent_evidence") is not True
        or identity.get("distance_only_inference") is not False
        or identity.get("contexts_collapsed") is not False
    ):
        _fail("SR2_FORMAL_IDENTITY_NOT_EXACT4")
    context = _require_mapping(
        formal.get("context_preservation"),
        "SR2_CONTEXT_PRESERVATION_NOT_OBJECT",
    )
    contexts = _require_list(
        context.get("contexts"), "SR2_CONTEXTS_NOT_LIST"
    )
    if (
        context.get("contexts_collapsed") is not False
        or len(contexts) != _EVENT_COUNT
        or tuple(row.get("canonical_event_id") for row in contexts)
        != _EVENT_IDS
    ):
        _fail("SR2_CONTEXTS_COLLAPSED_OR_INCOMPLETE")

    pair = _require_mapping(
        formal.get("reactive_pair_authority"),
        "SR2_REACTIVE_PAIR_AUTHORITY_NOT_OBJECT",
    )
    if (
        pair.get("D3_human_choice") != "CONFIRM_OBSERVED_PAIR"
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "C51"
        or pair.get("authority_scope") != sr2_ingestion_owner.PAIR_AUTHORITY_SCOPE
        or pair.get("reactive_pair_sample_authority") is not True
        or pair.get("reusable_pair_rule_created") is not False
        or pair.get("cross_structure_regiochemistry_generalization") is not False
        or pair.get("all_SR2_uses_C51_authority") is not False
        or pair.get("all_engineered_Src_surrogates_use_C51_authority") is not False
        or pair.get("EGFR_C797_event_specific_authority") is not False
    ):
        _fail("SR2_SG_C51_PAIR_AUTHORITY_INVALID")

    role = _require_mapping(
        formal.get("selected_role_partition"),
        "SR2_SELECTED_ROLE_PARTITION_NOT_OBJECT",
    )
    runtime = _require_mapping(
        role.get("published_DIRECT_runtime_validation"),
        "SR2_ROLE_RUNTIME_VALIDATION_NOT_OBJECT",
    )
    independent = _require_mapping(
        role.get("independent_structural_validation"),
        "SR2_STRUCTURAL_VALIDATION_NOT_OBJECT",
    )
    bound_structural = _require_mapping(
        bound.get("structural_validation"),
        "SR2_BOUND_STRUCTURAL_VALIDATION_NOT_OBJECT",
    )
    bound_runtime = _require_mapping(
        bound.get("published_DIRECT_runtime_validation"),
        "SR2_BOUND_RUNTIME_VALIDATION_NOT_OBJECT",
    )
    expected_boundary = [dict(sr2_ingestion_owner.BOUNDARY_BONDS[0])]
    expected_runtime_boundary = {
        "bond_order": "SING",
        "boundary_valid": True,
        "scaffold_atom_id": "C9",
        "warhead_atom_id": "N11",
    }
    if (
        role.get("D4_human_choice") != "SELECT_CANDIDATE_15"
        or role.get("selected_candidate_index_0based") != 15
        or role.get("human_selected_candidate") != 15
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("candidate_index_is_recommendation") is not False
        or role.get("role_profile") != _ROLE_PROFILE
        or role.get("W") != list(sr2_ingestion_owner.WARHEAD_ROLE)
        or role.get("L") != []
        or role.get("S") != list(sr2_ingestion_owner.SCAFFOLD_ROLE)
        or role.get("W_L_S_counts") != [9, 0, 18]
        or role.get("boundary_bonds") != expected_boundary
        or role.get("applicable_task_ids") != [0, 3, 4]
        or role.get("canonical_role_partition_sample_authority") is not True
        or role.get("reusable_role_rule_created") is not False
        or role.get("role_authority_scope")
        != sr2_ingestion_owner.ROLE_AUTHORITY_SCOPE
        or runtime.get("profile") != _ROLE_PROFILE
        or runtime.get("applicable_task_ids") != [0, 3, 4]
        or runtime.get("valid") is not True
        or runtime.get("warhead_count") != 9
        or runtime.get("linker_count") != 0
        or runtime.get("scaffold_count") != 18
        or runtime.get("direct_scaffold_warhead_boundary")
        != expected_runtime_boundary
        or dict(bound_runtime) != dict(runtime)
    ):
        _fail("SR2_CANDIDATE15_DIRECT_ROLE_PARTITION_INVALID")
    if (
        independent.get("heavy_atom_count") != 27
        or independent.get("W_count") != 9
        or independent.get("L_count") != 0
        or independent.get("S_count") != 18
        or independent.get("C51_in_W") is not True
        or independent.get("partition_pairwise_disjoint") is not True
        or independent.get("partition_exhaustive") is not True
        or independent.get("cross_role_boundary_bonds") != expected_boundary
        or bound_structural.get("Exact27_count") != 27
        or bound_structural.get("boundary") != "C9-N11 SING S-W"
        or bound_structural.get("C51_in_W") is not True
    ):
        _fail("SR2_EXACT27_ROLE_VALIDATION_INVALID")

    canonical = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "SR2_CANONICAL_TASK_CONTRACT_NOT_OBJECT",
    )
    tasks = _require_list(
        canonical.get("global_canonical_Exact5"),
        "SR2_CANONICAL_TASKS_NOT_LIST",
    )
    expected_tasks = [
        {"display_alias": alias, "semantic_name": semantic, "task_id": task_id}
        for task_id, semantic, alias, _generated, _fixed
        in sr2_ingestion_owner.CANONICAL_TASKS
    ]
    if (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 3, 4]
        or canonical.get("sample_applicable_semantic_names")
        != [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ]
        or canonical.get("role_profile") != _ROLE_PROFILE
        or canonical.get("authoritative_task_labels_created") is not False
        or canonical.get("event_task_label_rows_materialized") is not False
        or tasks != expected_tasks
    ):
        _fail("SR2_CANONICAL_EXACT5_APPLICABILITY_INVALID")

    training = _require_mapping(
        formal.get("training_use_boundary"),
        "SR2_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    expected_training = {
        "D5_human_choice": "INCLUDE",
        "human_training_use_disposition": "INCLUDE",
        "human_training_excluded": False,
        "formal_training_admitted": False,
        "future_training_admission_candidate": True,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "READY_FOR_TRAINING": False,
    }
    derived_training = sr2_ingestion_owner._training_boundary()
    expected_derived_training = {
        "formal_event_training_use_decision": "INCLUDE",
        "training_use_allowed": True,
        "human_training_excluded": False,
        "candidate_for_future_training_admission": True,
        "future_training_admission_candidate": True,
        "future_training_admission_status": sr2_ingestion_owner.FUTURE_STATUS,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "READY_FOR_TRAINING": False,
    }
    if any(
        training.get(key) != value for key, value in expected_training.items()
    ) or any(
        derived_training.get(key) != value
        for key, value in expected_derived_training.items()
    ):
        _fail("SR2_RICH_TRAINING_INCLUDE_BOUNDARY_INVALID")

    pre = _require_mapping(
        formal.get("PRE_POST_boundary"), "SR2_PRE_BOUNDARY_NOT_OBJECT"
    )
    post = _require_mapping(
        formal.get("POST_evidence_boundary"),
        "SR2_POST_BOUNDARY_NOT_OBJECT",
    )
    if (
        pre.get("PRE_source_graph_present") is not True
        or pre.get("PRE_source_graph_count_per_event") != 1
        or pre.get("PRE_mapping_count_per_event") != 0
        or pre.get("PRE_mapping_status") != sr2_ingestion_owner.PRE_MAPPING_STATUS
        or pre.get("PRE_status") != sr2_ingestion_owner.PRE_STATUS
        or pre.get("PRE_topology_authority") is not False
        or pre.get("PRE_geometry_authority") is not False
        or pre.get("PRE_coordinates_authority") is not False
        or pre.get("POST_to_PRE_copy_performed") is not False
        or pre.get("PRE_zero_fill_performed") is not False
        or post.get("POST_source_evidence_available") is not True
        or post.get("POST_source_evidence_count") != 4
        or post.get("observed_distances_angstrom")
        != [row[6] for row in sr2_ingestion_owner.EXPECTED_EVENTS]
        or post.get("POST_geometry_training_authority") is not False
        or post.get("POST_geometry_training_target_created") is not False
    ):
        _fail("SR2_RICH_PRE_POST_BOUNDARY_INVALID")

    engineered = _require_mapping(
        formal.get("engineered_surrogate_caveat"),
        "SR2_ENGINEERED_SURROGATE_CAVEAT_NOT_OBJECT",
    )
    if dict(engineered) != sr2_ingestion_owner._engineered_surrogate_caveat():
        _fail("SR2_ENGINEERED_SURROGATE_CAVEAT_INVALID")

    authority = _require_mapping(
        formal.get("authority_boundary"),
        "SR2_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    required_true = (
        "canonical_role_partition_sample_authority",
        "formal_authority_created",
        "formal_authority_is_human",
        "human_decision_created",
        "human_review_completed",
        "human_training_use_disposition_authority",
        "positive_chemistry_sample_authority",
        "reactive_pair_sample_authority",
        "role_profile_task_applicability_sample_authority",
        "sample_level_formal_human_decision_authority_created",
        "task_relevance_sample_authority",
    )
    required_false = (
        "POST_geometry_training_authority",
        "PRE_geometry_authority",
        "PRE_topology_authority",
        "READY_FOR_TRAINING",
        "authoritative_task_labels_created",
        "chemical_warhead_reusable_authority",
        "cross_structure_regiochemistry_generalization",
        "current_runtime_model_usable",
        "event_task_label_rows_materialized",
        "formal_split_authority",
        "formal_training_admitted",
        "machine_approval",
        "machine_scientific_authority_created",
        "parameter_update_authorization",
        "reaction_family_authority",
        "reusable_chemistry_authority",
        "reusable_pair_authority",
        "reusable_role_authority",
        "tensor_target_created",
        "training_admission_created",
        "training_materialization_allowed",
        "training_started",
        "warhead_rule_authority",
        "warhead_type_authority",
    )
    if any(authority.get(key) is not True for key in required_true) or any(
        authority.get(key) is not False for key in required_false
    ):
        _fail("SR2_RICH_AUTHORITY_BOUNDARY_INVALID")

    semantic = _require_mapping(
        bound.get("semantic_contract"),
        "SR2_SEMANTIC_CONTRACT_NOT_OBJECT",
    )
    if dict(semantic) != {
        "role_profile": _ROLE_PROFILE,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "B3_present": True,
        "sixth_task_present": False,
        "completed_lane": sr2_ingestion_owner.EXPECTED_COMPLETED_LANE,
        "completed_lane_source_bound": True,
    }:
        _fail("SR2_PUBLISHED_SEMANTIC_CONTRACT_INVALID")

    events = _require_list(
        formal.get("event_level_formal_human_decisions"),
        "SR2_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _EVENT_COUNT:
        _fail("SR2_FORMAL_EVENT_COUNT_NOT_EXACT4")
    typed_events = tuple(
        _require_mapping(event, "SR2_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    for event, expected in zip(
        typed_events, sr2_ingestion_owner.EXPECTED_EVENTS, strict=True
    ):
        event_id = event.get("canonical_event_id")
        rank = event.get("scaleup_rank")
        observed_ids.append(str(event_id))
        if type(rank) is int:
            observed_ranks.append(rank)
        projected = sr2_ingestion_owner._event_projection(expected)
        if (
            event_id != expected[0]
            or rank != expected[1]
            or event.get("pdb_id") != expected[2]
            or event.get("protein_asym") != expected[3]
            or event.get("ligand_asym") != expected[4]
            or event.get("selected_connection_id") != expected[5]
            or event.get("POST_distance_angstrom") != expected[6]
            or event.get("protein_reactive_atom") != "SG"
            or event.get("ligand_component_id") != "SR2"
            or event.get("ligand_reactive_atom") != "C51"
            or any(
                event.get(key) != value
                for key, value in _EXPECTED_DECISIONS.items()
            )
            or event.get("sample_level_formal_authority") is not True
            or event.get("explicit_covalent_evidence") is not True
            or event.get("distance_only_inference") is not False
            or event.get("POST_geometry_training_authority") is not False
            or event.get("formal_training_admitted") is not False
            or projected.get("completed_lane")
            != sr2_ingestion_owner.EXPECTED_COMPLETED_LANE
            or projected.get("training_use_allowed") is not True
            or projected.get("human_training_excluded") is not False
            or projected.get("future_training_admission_candidate") is not True
            or projected.get("formal_training_admitted") is not False
            or projected.get("current_runtime_model_usable") is not False
        ):
            _fail("SR2_RICH_EVENT_SEMANTICS_INVALID:" + str(event_id))
    if (
        tuple(observed_ids) != _EVENT_IDS
        or tuple(observed_ranks) != _RANKS
        or len(set(observed_ids)) != _EVENT_COUNT
        or set(observed_ids) != set(_EVENT_IDS)
    ):
        _fail("SR2_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    return typed_events


def _expected_binding_v1() -> generic.SourceBinding:
    return generic.SourceBinding(
        source_path=_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_FORMAL_DECISION_BYTE_COUNT,
        sha256=_FORMAL_DECISION_SHA256,
        schema_version=_FORMAL_DECISION_SCHEMA,
        review_unit_id=_REVIEW_UNIT_ID,
    )


def _validate_projected_sr2_source_v1(
    source: generic.NormalizedDecisionSource,
) -> None:
    """Reject projection drift or any rich-authority field leakage."""

    _prove_generic_fact_schema_v1()
    expected_binding = _expected_binding_v1()
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding != expected_binding
        or len(source.facts) != _EVENT_COUNT
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_EVENT_IDS))
    ):
        _fail("SR2_SOURCE_PROJECTION_IDENTITY_INVALID")
    for fact in source.facts:
        if (
            type(fact) is not generic.NormalizedCompletedDecisionFact
            or tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or any(
                hasattr(fact, attribute)
                for attribute in _FORBIDDEN_GENERIC_FACT_ATTRIBUTES
            )
            or fact.review_unit_id != _REVIEW_UNIT_ID
            or fact.human_review_completed is not True
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            or fact.source_decision_schema != _FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _FORMAL_DECISION_SHA256
            or fact.source_binding_path != expected_binding.source_path
        ):
            _fail("SR2_SOURCE_PROJECTION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithSR2Error(
                "SR2_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_sr2_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic Exact11 facts from owner-validated SR2 authority."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "SR2_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_owner_binding = {
        "path": _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _FORMAL_DECISION_SHA256,
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "SR2_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if dict(binding_value) != expected_owner_binding:
        _fail("SR2_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_sr2_semantics_v1(bound)
    facts = tuple(
        generic.NormalizedCompletedDecisionFact(
            canonical_event_id=str(event["canonical_event_id"]),
            review_unit_id=_REVIEW_UNIT_ID,
            human_review_completed=True,
            legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
            task_relevance_disposition=generic.TASK_RELEVANT,
            chemistry_disposition=generic.CHEMISTRY_POSITIVE,
            training_disposition=generic.TRAINING_INCLUDE,
            human_training_excluded=False,
            source_decision_schema=_FORMAL_DECISION_SCHEMA,
            source_decision_sha256=_FORMAL_DECISION_SHA256,
            source_binding_path=(
                _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
            ),
        )
        for event in events
    )
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(),
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )
    _validate_projected_sr2_source_v1(source)
    return source


def project_sr2_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the SR2 ingestion owner and project its narrow Exact4."""

    try:
        bound = sr2_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except sr2_ingestion_owner.SR2IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithSR2Error(
            "SR2_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_sr2_binding_v1(bound)


def _prove_sr2_predecessor_historical_state_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove SR2 is exactly one complete unreviewed predecessor unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithSR2Error(
            "SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT")

    expected_ids = set(_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    if any(event_counts[event_id] != 1 for event_id in _EVENT_IDS):
        _fail("SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    target_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if len(target_rows) != _EVENT_COUNT or any(
        row["raw_review_unit_id"] != _REVIEW_UNIT_ID
        or row["raw_priority_rank"] != _HISTORICAL_PRIORITY_RANK
        or row["raw_unit_event_count"] != "4"
        or row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target_rows
    ):
        _fail("SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        generic._validate_historical_rows(rows)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithSR2Error(
            "SR2_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error


def load_real_completed_decision_sources_with_sr2_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published with-GD1 chain and append one SR2 source."""

    existing = gd1_predecessor.load_real_completed_decision_sources_with_gd1_v1(
        repo_root
    )
    actual_composition = tuple(len(source.facts) for source in existing)
    if (
        len(existing) != 18
        or actual_composition != _PREDECESSOR_SOURCE_FACT_COUNTS
    ):
        _fail("PREDECESSOR_WITH_GD1_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 115
        or len(set(existing_event_ids)) != 115
        or len({source.binding.review_unit_id for source in existing}) != 18
        or len({source.binding.stable_identity for source in existing}) != 18
    ):
        _fail("PREDECESSOR_WITH_GD1_SOURCE_CHAIN_NOT_EXACT18_115")

    sr2_source = project_sr2_completed_decision_v1(repo_root=repo_root)
    _validate_projected_sr2_source_v1(sr2_source)
    sr2_event_ids = {fact.canonical_event_id for fact in sr2_source.facts}
    overlap = sr2_event_ids & set(existing_event_ids)
    if overlap:
        _fail("SR2_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])
    if sr2_source.binding.review_unit_id in {
        source.binding.review_unit_id for source in existing
    }:
        _fail("SR2_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR")
    if sr2_source.binding.stable_identity in {
        source.binding.stable_identity for source in existing
    }:
        _fail("SR2_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR")

    sources = (*existing, sr2_source)
    if (
        len(sources) != 19
        or sources[:-1] != existing
        or tuple(len(source.facts) for source in sources)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or len({source.binding.review_unit_id for source in sources}) != 19
        or len({source.binding.stable_identity for source in sources}) != 19
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT19")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 119:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_119")
    if len(set(event_ids)) != 119:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def _validate_reconciliation_delta_v1(
    predecessor: generic.ReconciliationResult,
    successor: generic.ReconciliationResult,
) -> None:
    """Prove the successor is exactly the four-row generic SR2 overlay."""

    if predecessor.review_summary != _BEFORE_SUMMARY:
        _fail("PREDECESSOR_WITH_GD1_REVIEW_SUMMARY_INVALID")
    if successor.review_summary != _AFTER_SUMMARY:
        _fail("SR2_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if (
        len(successor.source_bindings) != 19
        or len(successor.normalized_facts) != 119
    ):
        _fail("SR2_RECONCILIATION_SOURCE_CHAIN_INVALID")
    before_rows = predecessor.reconciled_rows
    after_rows = successor.reconciled_rows
    if (
        len(before_rows) != 338
        or len(after_rows) != 338
        or any(
            tuple(before) != generic.HISTORICAL_RECONCILIATION_HEADER
            or tuple(after) != generic.HISTORICAL_RECONCILIATION_HEADER
            for before, after in zip(before_rows, after_rows, strict=True)
        )
        or tuple(row["canonical_event_id"] for row in before_rows)
        != tuple(row["canonical_event_id"] for row in after_rows)
    ):
        _fail("SR2_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED")

    target_ids = set(_EVENT_IDS)
    expected_authority = generic._canonical_json(
        [_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()]
    )
    changed_target_count = 0
    unchanged_non_target_count = 0
    for before, after in zip(before_rows, after_rows, strict=True):
        event_id = before["canonical_event_id"]
        changed_fields = {key for key in before if before[key] != after[key]}
        if event_id not in target_ids:
            if changed_fields:
                _fail("SR2_NON_TARGET_ROW_CHANGED:" + event_id)
            unchanged_non_target_count += 1
            continue
        if changed_fields != _ALLOWED_RECONCILIATION_FIELDS:
            _fail("SR2_TARGET_CHANGED_FIELD_SET_INVALID:" + event_id)
        if (
            before["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or before["calibration_eligible"] != "true"
            or before["calibration_exclusion_reason"] != ""
            or after["current_review_status"]
            != generic.COMPLETED_HUMAN_POSITIVE
            or after["current_status_authority_sources_json"]
            != expected_authority
            or after["calibration_eligible"] != "false"
            or after["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            _fail("SR2_FINAL_RECONCILIATION_TRANSITION_INVALID:" + event_id)
        changed_target_count += 1
    if changed_target_count != 4 or unchanged_non_target_count != 334:
        _fail("SR2_RECONCILIATION_DELTA_NOT_EXACT4_OF_338")

    sr2_facts = [
        fact
        for fact in successor.normalized_facts
        if fact.canonical_event_id in target_ids
    ]
    if len(sr2_facts) != 4 or any(
        fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        or fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_POSITIVE
        for fact in sr2_facts
    ):
        _fail("SR2_TRAINING_INCLUDE_OR_POSITIVE_STATUS_ORTHOGONALITY_INVALID")


def reconcile_real_completed_human_decisions_with_sr2_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact19 sources through the generic owner, entirely in memory."""

    predecessor = (
        gd1_predecessor.reconcile_real_completed_human_decisions_with_gd1_v1(
            repo_root
        )
    )
    _prove_sr2_predecessor_historical_state_v1(predecessor.reconciled_rows)

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_sr2_predecessor_historical_state_v1(historical)
    original_snapshot = tuple(dict(row) for row in historical)
    adapted_historical = (
        gd1_predecessor.four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != original_snapshot:
        _fail("ONL_ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    _prove_sr2_predecessor_historical_state_v1(adapted_historical)

    sources = load_real_completed_decision_sources_with_sr2_v1(repo_root)
    successor = generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
    _validate_reconciliation_delta_v1(predecessor, successor)
    return successor
