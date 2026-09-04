"""Reconcile published LCY completion through the unchanged generic owner.

This metadata-only successor loads the rich LCY Exact4 authority through its
published ingestion owner, proves the narrow Exact11 projection boundary,
appends one source to the published with-GVE chain, and reconciles the fixed
historical population in memory. It writes no artifact and creates no census,
queue, role, mask, tensor, training-admission, or model authority.
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
    covapie_completed_human_decision_reconciliation_with_gve_v1
    as gve_predecessor,
)
from . import (
    covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1
    as lcy_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithLCYError",
    "project_lcy_completed_decision_v1",
    "load_real_completed_decision_sources_with_lcy_v1",
    "reconcile_real_completed_human_decisions_with_lcy_v1",
)


_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    lcy_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_FORMAL_DECISION_BYTE_COUNT = lcy_ingestion_owner.FORMAL_BINDINGS[0][2]
_FORMAL_DECISION_SHA256 = lcy_ingestion_owner.FORMAL_BINDINGS[0][3]
_FORMAL_DECISION_SCHEMA = lcy_ingestion_owner.FORMAL_DECISION_SCHEMA
_FORMAL_SEMANTIC_SHA256 = (
    lcy_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_REVIEW_UNIT_ID = lcy_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_EVENT_IDS = lcy_ingestion_owner.EXPECTED_EVENT_IDS
_RANKS = lcy_ingestion_owner.EXPECTED_RANKS
_SAME_COMPONENT_3A2G_EVENT_ID = (
    "COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1"
)

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "24"
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
    "completed_lane",
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "pair_authority_scope",
    "D4",
    "role_profile",
    "review_policy_candidate_count",
    "formal_valid_singleton_diagnostic_count",
    "selected_candidate",
    "selected_role_partition",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "W",
    "L",
    "S",
    "W_L_S_counts",
    "boundary_bonds",
    "canonical_mask_applicability",
    "mask_applicability",
    "B3_applicability",
    "PRE_status",
    "PRE_topology",
    "PRE_geometry",
    "POST_distance",
    "POST_geometry",
    "same_component_3A2G_boundary",
    "future_training_admission_candidate",
    "training_use_include",
    "formal_training_admitted",
    "training_materialization",
    "tensor_target",
    "runtime_usable",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
    "crossfield_compatibility",
)
_EXPECTED_DECISIONS = {
    "D1_task_relevance": "NOT_RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_candidate": "UNRESOLVED",
    "D5_training_use": "NOT_APPLICABLE",
}
_EXPECTED_CANONICAL_TASKS = {
    "B3_present": True,
    "canonical_mask_structural_labels_available_for_sample": False,
    "global_contract_modified": False,
    "sample_authoritative_role_partition": False,
    "sample_authoritative_task_applicability": False,
    "sixth_task": False,
    "task_count": 5,
    "tasks": [
        {
            "display_alias": "A",
            "semantic_long_name": "warhead_only",
            "task_id": 0,
        },
        {
            "display_alias": "B",
            "semantic_long_name": "linker_plus_warhead",
            "task_id": 1,
        },
        {
            "display_alias": "B2",
            "semantic_long_name": "scaffold_plus_warhead",
            "task_id": 2,
        },
        {
            "display_alias": "B3",
            "semantic_long_name": "scaffold_only",
            "task_id": 3,
        },
        {
            "display_alias": "C",
            "semantic_long_name": "scaffold_plus_linker_plus_warhead",
            "task_id": 4,
        },
    ],
}
_BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 32,
    "completed_negative_unit_count": 6,
    "completed_total_event_count": 147,
    "completed_total_unit_count": 24,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 191,
    "unreviewed_unit_count": 107,
}
_AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 36,
    "completed_negative_unit_count": 7,
    "completed_total_event_count": 151,
    "completed_total_unit_count": 25,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 187,
    "unreviewed_unit_count": 106,
}
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    (
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    )
)


class CompletedDecisionReconciliationWithLCYError(ValueError):
    """Raised when the exact LCY reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithLCYError(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _require_exact_mapping(
    value: object, expected: Mapping[str, object], token: str
) -> Mapping[str, Any]:
    actual = _require_mapping(value, token)
    if dict(actual) != dict(expected):
        _fail(token)
    return actual


def _prove_generic_fact_schema_v1() -> None:
    fields = tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)
    if fields != _GENERIC_FACT_FIELDS or len(fields) != 11:
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")


def _expected_event_decisions_v1() -> list[dict[str, object]]:
    expected: list[dict[str, object]] = []
    for index, row in enumerate(lcy_ingestion_owner.EXPECTED_EVENTS):
        event_id, rank = row[:2]
        expected.append(
            {
                **_EXPECTED_DECISIONS,
                "D6_inherited_exact": True,
                "canonical_event_id": event_id,
                "event_exception": False,
                "event_index_0based": index,
                "formal_decision_applies": True,
                "ligand_reactive_atom": "C1",
                "protein_reactive_atom": "SG",
                "role_partition_sample_authority": False,
                "sample_positive_chemistry_authority": True,
                "sample_reactive_pair_authority": True,
                "sample_task_relevance_authority": True,
                "scaleup_rank": rank,
            }
        )
    return expected


def _expected_pre_events_v1() -> list[dict[str, object]]:
    return [
        {
            "PRE_mapping_status": lcy_ingestion_owner.PRE_MAPPING_STATUS,
            "candidate_PRE_free_graph_count": 1,
            "canonical_event_id": event_id,
            "compatible_mapping_count": 0,
            "final_PRE_reaction_status": lcy_ingestion_owner.PRE_STATUS,
            "supporting_adduct_graph_count": 1,
        }
        for event_id in _EVENT_IDS
    ]


def _validate_rich_lcy_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove published rich LCY authority before projection."""

    if (
        bound.get("formal_semantics_independently_validated") is not True
        or bound.get("formal_validator_provenance_identity_only") is not True
        or bound.get("formal_validator_imported") is not False
        or bound.get("formal_validator_parsed") is not False
        or bound.get("formal_validator_executed") is not False
        or bound.get("formal_validator_subprocessed") is not False
        or bound.get("formal_validator_runtime_dependency") is not False
    ):
        _fail("LCY_INGESTION_OWNER_OR_FORMAL_VALIDATOR_BOUNDARY_INVALID")

    formal = _require_mapping(bound.get("formal"), "LCY_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != _FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != lcy_ingestion_owner.FORMAL_RECORD_ROLE
        or formal.get("formal_decision_semantic_canonical_sha256")
        != _FORMAL_SEMANTIC_SHA256
        or formal.get("approved") is not True
        or formal.get("unsigned") is not False
        or formal.get("decision_finalized") is not True
        or formal.get("human_review_completed") is not True
        or formal.get("formal_decision_created") is not True
        or formal.get("formal_authority_created") is not True
        or formal.get("formal_authority_is_human") is not True
        or formal.get("machine_approval") is not False
    ):
        _fail("LCY_FORMAL_COMPLETION_OR_SEMANTICS_INVALID")

    inherited = _require_mapping(
        formal.get("inherited_human_scientific_decision"),
        "LCY_INHERITED_HUMAN_DECISION_NOT_OBJECT",
    )
    if any(inherited.get(key) != value for key, value in _EXPECTED_DECISIONS.items()):
        _fail("LCY_D1_D5_DECISIONS_INVALID")
    if (
        inherited.get("D6_scientific_context") != lcy_ingestion_owner.EXPECTED_D6
        or inherited.get("D6_utf8_byte_count")
        != lcy_ingestion_owner.EXPECTED_D6_BYTE_COUNT
        or inherited.get("D6_utf8_sha256")
        != lcy_ingestion_owner.EXPECTED_D6_SHA256
        or inherited.get("inheritance_byte_exact") is not True
    ):
        _fail("LCY_D6_IDENTITY_INVALID")

    _require_exact_mapping(
        formal.get("target_Exact4"),
        {
            "3A2G_event_included": False,
            "canonical_event_ids": list(_EVENT_IDS),
            "event_count": 4,
            "ligand_wide_selection": False,
            "raw_priority_rank": 24,
            "review_unit_id": _REVIEW_UNIT_ID,
            "scaleup_ranks": list(_RANKS),
        },
        "LCY_FORMAL_IDENTITY_NOT_EXACT4",
    )
    events = _require_list(
        formal.get("event_level_formal_decisions"),
        "LCY_FORMAL_EVENT_DECISIONS_NOT_LIST",
    )
    if (
        formal.get("event_level_formal_decision_count") != 4
        or len(events) != 4
        or events != _expected_event_decisions_v1()
    ):
        _fail("LCY_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    typed_events = tuple(
        _require_mapping(event, "LCY_FORMAL_EVENT_NOT_OBJECT") for event in events
    )

    lane = _require_mapping(
        bound.get("completed_lane_validation"),
        "LCY_COMPLETED_LANE_VALIDATION_NOT_OBJECT",
    )
    if lane.get("completed_lane") != lcy_ingestion_owner.EXPECTED_COMPLETED_LANE:
        _fail("LCY_COMPLETED_LANE_INVALID")
    evidence = _require_mapping(
        bound.get("event_evidence_validation"),
        "LCY_EVENT_EVIDENCE_VALIDATION_NOT_OBJECT",
    )
    if (
        evidence.get("event_count") != 4
        or evidence.get("event_ids") != list(_EVENT_IDS)
        or evidence.get("scaleup_ranks") != list(_RANKS)
        or evidence.get("POST_source_evidence_event_count") != 4
        or evidence.get("PRE_source_graph_present_event_count") != 4
        or evidence.get("PRE_mapping_count") != 0
        or evidence.get("same_component_3A2G_included") is not False
    ):
        _fail("LCY_SUPPORTING_EVENT_EVIDENCE_INVALID")
    graph = _require_mapping(
        bound.get("graph_candidate_validation"),
        "LCY_GRAPH_CANDIDATE_VALIDATION_NOT_OBJECT",
    )
    if (
        graph.get("review_policy_candidate_count") != 0
        or graph.get("review_policy_selectable_candidate_indices") != []
        or graph.get("formal_valid_singleton_diagnostic_count") != 3
        or graph.get("formal_valid_singleton_diagnostic_indices") != [0, 1, 2]
        or graph.get("formal_valid_singleton_diagnostics_are_selectable")
        is not False
        or graph.get("machine_candidate_selected") is not False
        or graph.get("human_candidate_selected_in_preparation") is not False
        or graph.get("role_authority_created") is not False
        or graph.get("task_applicability_authority_created") is not False
        or graph.get("PRE_mapping_count") != 0
        or graph.get("same_component_3A2G_included") is not False
    ):
        _fail("LCY_GRAPH_EVIDENCE_OR_ROLE_AUTHORITY_INVALID")

    _require_exact_mapping(
        formal.get("sample_task_relevance"),
        {
            "all_LCY_rule_created": False,
            "authority_scope": lcy_ingestion_owner.PAIR_AUTHORITY_SCOPE,
            "sample_task_relevance_authority": True,
            "task_domain_negative": True,
            "task_relevance_disposition": "NOT_RELEVANT",
            "universal_generalization_created": False,
        },
        "LCY_TASK_RELEVANCE_AUTHORITY_INVALID",
    )
    _require_exact_mapping(
        formal.get("sample_chemistry"),
        {
            "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
            "D1_NOT_RELEVANT_DOES_NOT_COLLAPSE_D2_POSITIVE": True,
            "chemistry_disposition": "POSITIVE",
            "reusable_chemistry_authority": False,
            "sample_positive_chemistry_authority": True,
        },
        "LCY_POSITIVE_CHEMISTRY_AUTHORITY_INVALID",
    )
    _require_exact_mapping(
        formal.get("sample_reactive_pair"),
        {
            "3A2G_pair_promoted": False,
            "all_LCY_C1_authority": False,
            "authority_scope": lcy_ingestion_owner.PAIR_AUTHORITY_SCOPE,
            "ligand_reactive_atom": "C1",
            "observed_POST_distances_angstrom": [
                float(row[7]) for row in lcy_ingestion_owner.EXPECTED_EVENTS
            ],
            "protein_reactive_atom": "SG",
            "reusable_pair_authority": False,
            "sample_reactive_pair_authority": True,
        },
        "LCY_SG_C1_PAIR_AUTHORITY_INVALID",
    )

    role = _require_mapping(
        formal.get("D4_role_boundary"), "LCY_D4_ROLE_BOUNDARY_NOT_OBJECT"
    )
    required_role = {
        "D4_human_choice": "UNRESOLVED",
        "canonical_mask_structural_labels_sample_authority": False,
        "formal_valid_singleton_diagnostic_count": 3,
        "formal_valid_singleton_diagnostic_indices": [0, 1, 2],
        "formal_valid_singleton_diagnostics_are_selectable": False,
        "human_selected_role_candidate": None,
        "review_policy_candidate_count": 0,
        "review_policy_selectable_candidate_indices": [],
        "role_partition_sample_authority": False,
        "role_profile": "NOT_ESTABLISHED",
        "selected_role_partition": None,
        "structurally_applicable_task_ids": None,
        "task_applicability_sample_authority": False,
    }
    if any(role.get(key) != value for key, value in required_role.items()):
        _fail("LCY_UNRESOLVED_ROLE_BOUNDARY_INVALID")
    diagnostics = _require_list(
        role.get("formal_valid_singleton_diagnostics"),
        "LCY_ROLE_DIAGNOSTICS_NOT_LIST",
    )
    if len(diagnostics) != 3 or any(
        type(item) is not dict
        or item.get("diagnostic_index") != index
        or item.get("S_count") != 1
        or item.get("published_runtime_valid") is not True
        or item.get("minimal_seed_2_or_3_possible") is not False
        or item.get("review_policy_eligible") is not False
        or item.get("selected") is not False
        for index, item in enumerate(diagnostics)
    ):
        _fail("LCY_SINGLETON_DIAGNOSTICS_INVALID")
    derived_role = lcy_ingestion_owner._role_boundary()
    if (
        derived_role.get("warhead_atoms") is not None
        or derived_role.get("linker_atoms") is not None
        or derived_role.get("scaffold_atoms") is not None
        or derived_role.get("W_L_S_counts") is not None
        or derived_role.get("boundary_bonds") is not None
        or derived_role.get("selected_candidate_index_0based") is not None
        or derived_role.get("role_partition_human_authoritative") is not False
    ):
        _fail("LCY_W_L_S_OR_ROLE_AUTHORITY_INVALID")
    _require_exact_mapping(
        formal.get("canonical_Exact5"),
        _EXPECTED_CANONICAL_TASKS,
        "LCY_CANONICAL_EXACT5_BOUNDARY_INVALID",
    )

    _require_exact_mapping(
        formal.get("training_boundary"),
        {
            "NOT_APPLICABLE_is_EXCLUDE_FROM_TRAINING_ONLY": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
            "current_runtime_model_usable": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": False,
            "human_training_excluded": False,
            "human_training_use_disposition_authority": True,
            "parameter_update_authorization": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "training_use_disposition": "NOT_APPLICABLE",
            "training_use_include": False,
        },
        "LCY_TRAINING_NOT_APPLICABLE_BOUNDARY_INVALID",
    )
    derived_training = lcy_ingestion_owner._training_boundary()
    if (
        derived_training.get("formal_event_training_use_decision")
        != "NOT_APPLICABLE"
        or derived_training.get("training_use_include") is not False
        or derived_training.get("human_training_excluded") is not False
        or derived_training.get("future_training_admission_candidate") is not False
        or derived_training.get("formal_training_admitted") is not False
        or derived_training.get("training_materialization_allowed") is not False
        or derived_training.get("tensor_target_created") is not False
        or derived_training.get("current_runtime_model_usable") is not False
        or derived_training.get("READY_FOR_TRAINING") is not False
    ):
        _fail("LCY_DERIVED_TRAINING_BOUNDARY_INVALID")

    _require_exact_mapping(
        formal.get("PRE_boundary"),
        {
            "POST_to_PRE_copy": False,
            "PRE_authority": False,
            "PRE_coordinates": None,
            "PRE_geometry_authority": False,
            "PRE_reconstruction": False,
            "PRE_status": lcy_ingestion_owner.PRE_STATUS,
            "PRE_topology": None,
            "PRE_zero_fill": False,
            "bond_edit_inference": False,
            "leaving_group_inference": False,
            "literature_derived_PRE_graph": False,
            "per_event": _expected_pre_events_v1(),
            "reagent_inference": False,
        },
        "LCY_PRE_UNRESOLVED_BOUNDARY_INVALID",
    )
    _require_exact_mapping(
        formal.get("POST_boundary"),
        {
            "D3_formalizes_only_sample_reactive_pair": True,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
            "POST_source_evidence_count": 4,
            "observed_distances_angstrom": [
                float(row[7]) for row in lcy_ingestion_owner.EXPECTED_EVENTS
            ],
        },
        "LCY_POST_EVIDENCE_BOUNDARY_INVALID",
    )
    _require_exact_mapping(
        formal.get("future_generic_Exact11_projection"),
        {
            "chemistry_disposition": "POSITIVE",
            "generic_fact_materialized_now": False,
            "generic_facts_created": False,
            "generic_owner_import_path_exact": True,
            "generic_reconciliation_outputs_created": False,
            "human_review_completed": True,
            "human_training_excluded": False,
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "reconciliation_performed_now": False,
            "synthetic_future_Exact11_accepted": True,
            "task_relevance_disposition": "NOT_RELEVANT",
            "training_disposition": "NOT_APPLICABLE",
        },
        "LCY_GENERIC_EXACT11_PREVIEW_INVALID",
    )
    _require_exact_mapping(
        formal.get("same_component_3A2G_boundary"),
        {
            "PRE_transferred": False,
            "canonical_event_id": _SAME_COMPONENT_3A2G_EVENT_ID,
            "current_Exact4_authority": False,
            "decision_transferred": False,
            "pair_promoted": False,
            "role_transferred": False,
            "same_component_context_scientifically_relevant": True,
            "training_transferred": False,
        },
        "LCY_3A2G_AUTHORITY_TRANSFER_INVALID",
    )
    operations = _require_mapping(
        formal.get("downstream_operations"), "LCY_DOWNSTREAM_OPERATIONS_NOT_OBJECT"
    )
    if not operations or any(value is not False for value in operations.values()):
        _fail("LCY_UNAUTHORIZED_DOWNSTREAM_OPERATION")

    authority = _require_mapping(
        formal.get("formal_authority_boundary"),
        "LCY_FORMAL_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    true_set = [
        "formal_authority_created",
        "formal_authority_is_human",
        "human_training_use_disposition_authority",
        "sample_positive_chemistry_authority",
        "sample_reactive_pair_authority",
        "sample_task_relevance_authority",
    ]
    observed_true = sorted(
        key
        for key, value in authority.items()
        if value is True and key != "formal_authority_true_set"
    )
    if (
        authority.get("formal_authority_true_set") != true_set
        or observed_true != sorted(true_set)
        or any(
            value is not False
            for key, value in authority.items()
            if key not in (*true_set, "formal_authority_true_set")
        )
    ):
        _fail("LCY_FORMAL_AUTHORITY_TRUE_SET_NOT_EXACT6")
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


def _validate_projected_lcy_source_v1(
    source: generic.NormalizedDecisionSource,
) -> None:
    """Reject projection drift or any rich-authority field leakage."""

    _prove_generic_fact_schema_v1()
    expected_binding = _expected_binding_v1()
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding != expected_binding
        or len(source.facts) != 4
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_EVENT_IDS))
    ):
        _fail("LCY_SOURCE_PROJECTION_IDENTITY_INVALID")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithLCYError(
            "LCY_GENERIC_SOURCE_BINDING_REJECTED:" + str(error)
        ) from error
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
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
            or fact.source_decision_schema != _FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _FORMAL_DECISION_SHA256
            or fact.source_binding_path != expected_binding.source_path
        ):
            _fail("LCY_SOURCE_PROJECTION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithLCYError(
                "LCY_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_lcy_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic Exact11 facts from owner-validated LCY authority."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "LCY_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_owner_binding = {
        "path": _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _FORMAL_DECISION_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:"
            + _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
            + "@"
            + _FORMAL_DECISION_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "LCY_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_JSON_AND_INDEPENDENTLY_VALIDATED",
    }
    if dict(binding_value) != expected_owner_binding:
        _fail("LCY_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_lcy_semantics_v1(bound)
    facts = tuple(
        generic.NormalizedCompletedDecisionFact(
            canonical_event_id=str(event["canonical_event_id"]),
            review_unit_id=_REVIEW_UNIT_ID,
            human_review_completed=True,
            legacy_completed_review_status=generic.COMPLETED_HUMAN_NEGATIVE,
            task_relevance_disposition=generic.TASK_NOT_RELEVANT,
            chemistry_disposition=generic.CHEMISTRY_POSITIVE,
            training_disposition=generic.TRAINING_NOT_APPLICABLE,
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
    _validate_projected_lcy_source_v1(source)
    return source


def project_lcy_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the LCY ingestion owner and project its narrow Exact4."""

    try:
        bound = lcy_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except lcy_ingestion_owner.LCYIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithLCYError(
            "LCY_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_lcy_binding_v1(bound)


def _prove_lcy_predecessor_historical_state_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove LCY is exactly one complete unreviewed predecessor unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithLCYError(
            "LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT")

    expected_ids = set(_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("LCY_GENERIC_REVIEW_UNIT_COLLISION")
    if any(event_counts[event_id] != 1 for event_id in _EVENT_IDS):
        _fail("LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    target_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if len(target_rows) != 4 or any(
        row["raw_review_unit_id"] != _REVIEW_UNIT_ID
        or row["raw_priority_rank"] != _HISTORICAL_PRIORITY_RANK
        or row["raw_unit_event_count"] != "4"
        or row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target_rows
    ):
        _fail("LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    same_component = [
        row
        for row in rows
        if row["canonical_event_id"] == _SAME_COMPONENT_3A2G_EVENT_ID
    ]
    if len(same_component) > 1 or (
        same_component
        and (
            same_component[0]["raw_review_unit_id"] == _REVIEW_UNIT_ID
            or same_component[0]["canonical_event_id"] in expected_ids
        )
    ):
        _fail("LCY_3A2G_HISTORICAL_NON_TARGET_GUARD_INVALID")
    try:
        generic._validate_historical_rows(rows)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithLCYError(
            "LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error


def load_real_completed_decision_sources_with_lcy_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published with-GVE chain and append one LCY source."""

    existing = gve_predecessor.load_real_completed_decision_sources_with_gve_v1(
        repo_root
    )
    actual_composition = tuple(len(source.facts) for source in existing)
    if (
        len(existing) != 20
        or actual_composition != _PREDECESSOR_SOURCE_FACT_COUNTS
    ):
        _fail("PREDECESSOR_WITH_GVE_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 123
        or len(set(existing_event_ids)) != 123
        or len({source.binding.review_unit_id for source in existing}) != 20
        or len({source.binding.stable_identity for source in existing}) != 20
    ):
        _fail("PREDECESSOR_WITH_GVE_SOURCE_CHAIN_NOT_EXACT20_123")

    lcy_source = project_lcy_completed_decision_v1(repo_root=repo_root)
    _validate_projected_lcy_source_v1(lcy_source)
    lcy_event_ids = {fact.canonical_event_id for fact in lcy_source.facts}
    overlap = lcy_event_ids & set(existing_event_ids)
    if overlap:
        _fail("LCY_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])
    if lcy_source.binding.review_unit_id in {
        source.binding.review_unit_id for source in existing
    }:
        _fail("LCY_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR")
    if lcy_source.binding.stable_identity in {
        source.binding.stable_identity for source in existing
    }:
        _fail("LCY_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR")

    sources = (*existing, lcy_source)
    if (
        len(sources) != 21
        or sources[:-1] != existing
        or sources[-1] != lcy_source
        or tuple(len(source.facts) for source in sources)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or len({source.binding.review_unit_id for source in sources}) != 21
        or len({source.binding.stable_identity for source in sources}) != 21
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT21")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 127:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_127")
    if len(set(event_ids)) != 127:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    if _SAME_COMPONENT_3A2G_EVENT_ID in event_ids:
        _fail("LCY_3A2G_AUTHORITY_TRANSFERRED")
    return sources


def _validate_reconciliation_delta_v1(
    predecessor: generic.ReconciliationResult,
    successor: generic.ReconciliationResult,
) -> None:
    """Prove the successor is exactly the four-row generic LCY overlay."""

    if predecessor.review_summary != _BEFORE_SUMMARY:
        _fail("PREDECESSOR_WITH_GVE_REVIEW_SUMMARY_INVALID")
    if successor.review_summary != _AFTER_SUMMARY:
        _fail("LCY_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if (
        successor.review_summary["completed_positive_event_count"]
        != predecessor.review_summary["completed_positive_event_count"]
        or successor.review_summary["completed_positive_unit_count"]
        != predecessor.review_summary["completed_positive_unit_count"]
    ):
        _fail("LCY_COMPLETED_POSITIVE_SUMMARY_CHANGED")
    if (
        len(successor.source_bindings) != 21
        or len(successor.normalized_facts) != 127
        or len({binding.stable_identity for binding in successor.source_bindings})
        != 21
    ):
        _fail("LCY_RECONCILIATION_SOURCE_CHAIN_INVALID")
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
        _fail("LCY_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED")

    target_ids = set(_EVENT_IDS)
    expected_authority = generic._canonical_json(
        [_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()]
    )
    changed_target_count = 0
    unchanged_non_target_count = 0
    same_component_count = 0
    for before, after in zip(before_rows, after_rows, strict=True):
        event_id = before["canonical_event_id"]
        changed_fields = {key for key in before if before[key] != after[key]}
        if event_id not in target_ids:
            if before != after or changed_fields:
                _fail("LCY_NON_TARGET_ROW_CHANGED:" + event_id)
            if event_id == _SAME_COMPONENT_3A2G_EVENT_ID:
                same_component_count += 1
                if before["raw_review_unit_id"] == _REVIEW_UNIT_ID:
                    _fail("LCY_3A2G_AUTHORITY_TRANSFERRED")
            unchanged_non_target_count += 1
            continue
        if changed_fields != _ALLOWED_RECONCILIATION_FIELDS:
            _fail("LCY_TARGET_CHANGED_FIELD_SET_INVALID:" + event_id)
        if (
            before["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or before["calibration_eligible"] != "true"
            or before["calibration_exclusion_reason"] != ""
            or after["current_review_status"]
            != generic.COMPLETED_HUMAN_NEGATIVE
            or after["current_status_authority_sources_json"]
            != expected_authority
            or after["calibration_eligible"] != "false"
            or after["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("LCY_FINAL_RECONCILIATION_TRANSITION_INVALID:" + event_id)
        changed_target_count += 1
    if changed_target_count != 4 or unchanged_non_target_count != 334:
        _fail("LCY_RECONCILIATION_DELTA_NOT_EXACT4_OF_338")
    if same_component_count not in (0, 1):
        _fail("LCY_3A2G_HISTORICAL_NON_TARGET_GUARD_INVALID")

    lcy_facts = [
        fact
        for fact in successor.normalized_facts
        if fact.canonical_event_id in target_ids
    ]
    if len(lcy_facts) != 4 or any(
        fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_NEGATIVE
        or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        for fact in lcy_facts
    ):
        _fail("LCY_TASK_NEGATIVE_CHEMISTRY_POSITIVE_ORTHOGONALITY_INVALID")


def reconcile_real_completed_human_decisions_with_lcy_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact21 sources through the generic owner, entirely in memory."""

    predecessor = (
        gve_predecessor.reconcile_real_completed_human_decisions_with_gve_v1(
            repo_root
        )
    )
    _prove_lcy_predecessor_historical_state_v1(predecessor.reconciled_rows)

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_lcy_predecessor_historical_state_v1(historical)
    original_snapshot = tuple(dict(row) for row in historical)
    adapted_historical = (
        gve_predecessor.sr2_predecessor.gd1_predecessor.four_m5_predecessor
        .onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != original_snapshot:
        _fail("ONL_ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    _prove_lcy_predecessor_historical_state_v1(adapted_historical)

    sources = load_real_completed_decision_sources_with_lcy_v1(repo_root)
    successor = generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
    _validate_reconciliation_delta_v1(predecessor, successor)
    return successor
