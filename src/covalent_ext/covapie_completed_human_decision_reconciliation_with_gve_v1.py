"""Reconcile published GVE completion through the unchanged generic owner.

This metadata-only successor loads the rich GVE Exact4 authority through its
published ingestion owner, proves the narrow-projection and training boundaries,
appends one source to the published with-SR2 chain, and reconciles the fixed
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
    covapie_completed_human_decision_reconciliation_with_sr2_v1
    as sr2_predecessor,
)
from . import (
    covapie_gve_completed_decision_ingestion_and_task_label_availability_v1
    as gve_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithGVEError",
    "project_gve_completed_decision_v1",
    "load_real_completed_decision_sources_with_gve_v1",
    "reconcile_real_completed_human_decisions_with_gve_v1",
)


_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    gve_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_FORMAL_DECISION_BYTE_COUNT = gve_ingestion_owner.FORMAL_BINDINGS[0][2]
_FORMAL_DECISION_SHA256 = gve_ingestion_owner.FORMAL_BINDINGS[0][3]
_FORMAL_DECISION_SCHEMA = gve_ingestion_owner.FORMAL_DECISION_SCHEMA
_FORMAL_SEMANTIC_SHA256 = (
    gve_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_REVIEW_UNIT_ID = gve_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_EVENT_IDS = gve_ingestion_owner.EXPECTED_EVENT_IDS
_RANKS = gve_ingestion_owner.EXPECTED_RANKS

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "23"
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
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "W",
    "L",
    "S",
    "boundary_bonds",
    "canonical_mask_applicability",
    "B3_applicability",
    "PRE_status",
    "PRE_topology",
    "PRE_geometry",
    "POST_distance",
    "POST_geometry",
    "legacy_1XD3_context",
    "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE",
    "future_training_admission_candidate",
    "training_use_include",
    "formal_training_admitted",
    "training_materialization_allowed",
    "tensor_target",
    "current_runtime_model_usable",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
    "census_crossfield_debt",
)
_EXPECTED_DECISIONS = {
    "D1_task_relevance": "NOT_RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_candidate": "UNRESOLVED",
    "D5_training_use": "NOT_APPLICABLE",
}
_EXPECTED_CANONICAL_TASKS = [
    {"display_alias": "A", "semantic_name": "warhead_only", "task_id": 0},
    {
        "display_alias": "B",
        "semantic_name": "linker_plus_warhead",
        "task_id": 1,
    },
    {
        "display_alias": "B2",
        "semantic_name": "scaffold_plus_warhead",
        "task_id": 2,
    },
    {"display_alias": "B3", "semantic_name": "scaffold_only", "task_id": 3},
    {
        "display_alias": "C",
        "semantic_name": "scaffold_plus_linker_plus_warhead",
        "task_id": 4,
    },
]
_BEFORE_SUMMARY = {
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
_AFTER_SUMMARY = {
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
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    (
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    )
)


class CompletedDecisionReconciliationWithGVEError(ValueError):
    """Raised when the exact GVE reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithGVEError(token)


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
    for index, row in enumerate(gve_ingestion_owner.EXPECTED_EVENTS):
        event_id, rank, pdb_id, protein_asym, _residue, ligand_asym = row[:6]
        expected.append(
            {
                **_EXPECTED_DECISIONS,
                "D6_inherited_exact": True,
                "canonical_event_id": event_id,
                "event_index": index,
                "formal_decision_applies": True,
                "ligand_asym": ligand_asym,
                "ligand_component_id": "GVE",
                "ligand_reactive_atom": "CB",
                "pdb_id": pdb_id,
                "protein_asym": protein_asym,
                "protein_reactive_atom": "SG",
                "recomputed_POST_distance_angstrom": float(row[7]),
                "role_partition_sample_authority": False,
                "sample_positive_chemistry_authority": True,
                "sample_reactive_pair_authority": True,
                "sample_task_relevance_authority": True,
                "scaleup_rank": rank,
            }
        )
    return expected


def _validate_rich_gve_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove published rich GVE authority before projection."""

    if (
        bound.get("formal_semantics_independently_validated") is not True
        or bound.get("formal_validator_provenance_identity_only") is not True
        or bound.get("formal_validator_imported") is not False
        or bound.get("formal_validator_parsed") is not False
        or bound.get("formal_validator_executed") is not False
        or bound.get("formal_validator_subprocessed") is not False
        or bound.get("formal_validator_runtime_dependency") is not False
    ):
        _fail("GVE_INGESTION_OWNER_OR_FORMAL_VALIDATOR_BOUNDARY_INVALID")

    formal = _require_mapping(bound.get("formal"), "GVE_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != _FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != gve_ingestion_owner.FORMAL_RECORD_ROLE
        or formal.get("formal_decision_semantic_canonical_sha256")
        != _FORMAL_SEMANTIC_SHA256
        or formal.get("approved") is not True
        or formal.get("unsigned") is not False
        or formal.get("decision_finalized") is not True
        or formal.get("human_review_completed") is not True
        or formal.get("human_decision_created") is not True
        or formal.get("formal_authority_created") is not True
        or formal.get("formal_authority_is_human") is not True
        or formal.get("machine_approval") is not False
    ):
        _fail("GVE_FORMAL_COMPLETION_OR_SEMANTICS_INVALID")

    inherited = _require_mapping(
        formal.get("inherited_human_decision"),
        "GVE_INHERITED_HUMAN_DECISION_NOT_OBJECT",
    )
    if any(inherited.get(key) != value for key, value in _EXPECTED_DECISIONS.items()):
        _fail("GVE_D1_D5_DECISIONS_INVALID")
    if (
        inherited.get("D6_scientific_context") != gve_ingestion_owner.EXPECTED_D6
        or inherited.get("D6_utf8_byte_count")
        != gve_ingestion_owner.EXPECTED_D6_BYTE_COUNT
        or inherited.get("D6_utf8_sha256")
        != gve_ingestion_owner.EXPECTED_D6_SHA256
        or inherited.get("inheritance_byte_exact") is not True
    ):
        _fail("GVE_D6_IDENTITY_INVALID")

    _require_exact_mapping(
        formal.get("identity"),
        {
            "canonical_event_ids": list(_EVENT_IDS),
            "event_count": 4,
            "legacy_rank189_in_target": False,
            "legacy_rank190_in_target": False,
            "ligand_component_id": "GVE",
            "ligand_wide_selection": False,
            "review_unit_id": _REVIEW_UNIT_ID,
            "scaleup_ranks": list(_RANKS),
            "selection": "CANONICAL_EVENT_ID_EXACT4_FROM_FROZEN_PRIORITY_QUEUE",
        },
        "GVE_FORMAL_IDENTITY_NOT_EXACT4",
    )
    lane = _require_mapping(
        bound.get("completed_lane_validation"),
        "GVE_COMPLETED_LANE_VALIDATION_NOT_OBJECT",
    )
    if lane.get("completed_lane") != gve_ingestion_owner.EXPECTED_COMPLETED_LANE:
        _fail("GVE_COMPLETED_LANE_INVALID")

    evidence = _require_mapping(
        bound.get("event_evidence_validation"),
        "GVE_EVENT_EVIDENCE_VALIDATION_NOT_OBJECT",
    )
    if (
        evidence.get("event_count") != 4
        or evidence.get("event_ids") != list(_EVENT_IDS)
        or evidence.get("scaleup_ranks") != list(_RANKS)
        or evidence.get("POST_source_evidence_event_count") != 4
        or evidence.get("PRE_source_graph_present_event_count") != 4
        or evidence.get("PRE_mapping_count") != 0
        or evidence.get("legacy_1XD3_included") is not False
    ):
        _fail("GVE_SUPPORTING_EVENT_EVIDENCE_INVALID")
    graph = _require_mapping(
        bound.get("graph_candidate_validation"),
        "GVE_GRAPH_CANDIDATE_VALIDATION_NOT_OBJECT",
    )
    if (
        graph.get("candidate_evidence_count") != 3
        or graph.get("candidate_indices_evidence_only") != [0, 1, 2]
        or graph.get("machine_candidate_selected") is not False
        or graph.get("human_candidate_selected_in_preparation") is not False
        or graph.get("role_authority_created") is not False
        or graph.get("task_applicability_authority_created") is not False
        or graph.get("PRE_mapping_count") != 0
    ):
        _fail("GVE_GRAPH_EVIDENCE_OR_ROLE_AUTHORITY_INVALID")

    events = _require_list(
        formal.get("event_level_formal_decisions"),
        "GVE_FORMAL_EVENT_DECISIONS_NOT_LIST",
    )
    if events != _expected_event_decisions_v1() or len(events) != 4:
        _fail("GVE_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    typed_events = tuple(
        _require_mapping(event, "GVE_FORMAL_EVENT_NOT_OBJECT") for event in events
    )

    _require_exact_mapping(
        formal.get("sample_task_relevance_authority"),
        {
            "authority_scope": "CURRENT_GVE_EXACT4_ONLY",
            "sample_task_relevance_authority": True,
            "task_domain_negative": True,
            "task_relevance_disposition": "NOT_RELEVANT",
            "universal_generalization_created": False,
        },
        "GVE_TASK_RELEVANCE_AUTHORITY_INVALID",
    )
    _require_exact_mapping(
        formal.get("sample_positive_chemistry_authority"),
        {
            "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
            "D1_NOT_RELEVANT_DOES_NOT_COLLAPSE_D2_POSITIVE": True,
            "chemistry_disposition": "POSITIVE",
            "reusable_chemistry_authority": False,
            "sample_positive_chemistry_authority": True,
        },
        "GVE_POSITIVE_CHEMISTRY_AUTHORITY_INVALID",
    )
    pair = _require_mapping(
        formal.get("sample_reactive_pair_authority"),
        "GVE_PAIR_AUTHORITY_NOT_OBJECT",
    )
    if (
        pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "CB"
        or pair.get("sample_reactive_pair_authority") is not True
        or pair.get("authority_scope") != "CURRENT_GVE_EXACT4_ONLY"
        or pair.get("all_GVE_CB_authority") is not False
        or pair.get("legacy_1XD3_pair_promoted") is not False
        or pair.get("reusable_pair_authority") is not False
    ):
        _fail("GVE_SG_CB_PAIR_AUTHORITY_INVALID")

    _require_exact_mapping(
        formal.get("sample_role_boundary"),
        {
            "D4": "UNRESOLVED",
            "candidate_evidence_count": 3,
            "candidate_indices_evidence_only": [0, 1, 2],
            "canonical_mask_structural_labels_sample_authority": False,
            "human_selected_role_candidate": None,
            "role_partition_sample_authority": False,
            "role_profile": "NOT_ESTABLISHED",
            "selected_role_partition": None,
            "structurally_applicable_task_ids": None,
            "task_applicability_sample_authority": False,
        },
        "GVE_UNRESOLVED_ROLE_BOUNDARY_INVALID",
    )
    derived_role = gve_ingestion_owner._role_boundary()
    if (
        derived_role.get("warhead_atoms") is not None
        or derived_role.get("linker_atoms") is not None
        or derived_role.get("scaffold_atoms") is not None
        or derived_role.get("W_L_S_counts") is not None
        or derived_role.get("boundary_bonds") is not None
        or derived_role.get("selected_candidate_index_0based") is not None
        or derived_role.get("role_partition_human_authoritative") is not False
    ):
        _fail("GVE_W_L_S_OR_ROLE_AUTHORITY_INVALID")

    _require_exact_mapping(
        formal.get("canonical_Exact5_and_sample_boundary"),
        {
            "B3_present": True,
            "canonical_mask_structural_labels_available_for_sample": False,
            "global_contract_modified": False,
            "sample_authoritative_role_partition": False,
            "sample_authoritative_task_applicability": False,
            "sixth_task": False,
            "task_count": 5,
            "tasks": _EXPECTED_CANONICAL_TASKS,
        },
        "GVE_CANONICAL_EXACT5_BOUNDARY_INVALID",
    )

    training = _require_mapping(
        formal.get("training_boundary"),
        "GVE_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    expected_training = {
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
        "current_runtime_model_usable": False,
        "formal_split_authority": False,
        "formal_training_admitted": False,
        "future_training_admission_candidate": False,
        "human_training_excluded": False,
        "human_training_use_disposition_authority": True,
        "not_equivalent_to_EXCLUDE_FROM_TRAINING_ONLY": True,
        "parameter_update_authorization": False,
        "tensor_target_created": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "training_use_disposition": "NOT_APPLICABLE",
        "training_use_include": False,
    }
    if dict(training) != expected_training:
        _fail("GVE_TRAINING_NOT_APPLICABLE_BOUNDARY_INVALID")
    derived_training = gve_ingestion_owner._training_boundary()
    if (
        derived_training.get("formal_event_training_use_decision")
        != "NOT_APPLICABLE"
        or derived_training.get("training_use_include") is not False
        or derived_training.get("human_training_excluded") is not False
        or derived_training.get("candidate_for_future_training_admission")
        is not False
        or derived_training.get("formal_training_admitted") is not False
        or derived_training.get("training_materialization_allowed") is not False
        or derived_training.get("tensor_target_created") is not False
        or derived_training.get("current_runtime_model_usable") is not False
        or derived_training.get("READY_FOR_TRAINING") is not False
    ):
        _fail("GVE_DERIVED_TRAINING_BOUNDARY_INVALID")

    pre = _require_mapping(formal.get("PRE_boundary"), "GVE_PRE_BOUNDARY_NOT_OBJECT")
    pre_events = _require_list(pre.get("per_event"), "GVE_PRE_EVENTS_NOT_LIST")
    if (
        pre.get("PRE_status") != gve_ingestion_owner.PRE_STATUS
        or pre.get("PRE_authority") is not False
        or pre.get("PRE_topology") is not None
        or pre.get("PRE_coordinates") is not None
        or pre.get("PRE_geometry_authority") is not False
        or pre.get("PRE_reconstruction") is not False
        or pre.get("POST_to_PRE_copy") is not False
        or pre.get("PRE_zero_fill") is not False
        or len(pre_events) != 4
        or tuple(row.get("canonical_event_id") for row in pre_events) != _EVENT_IDS
        or any(
            row.get("PRE_source_graph_count") != 1
            or row.get("PRE_mapping_count") != 0
            or row.get("PRE_mapping_status")
            != gve_ingestion_owner.PRE_MAPPING_STATUS
            or row.get("PRE_reaction_status") != gve_ingestion_owner.PRE_STATUS
            for row in pre_events
        )
    ):
        _fail("GVE_PRE_UNRESOLVED_BOUNDARY_INVALID")
    post = _require_mapping(
        formal.get("POST_boundary"), "GVE_POST_BOUNDARY_NOT_OBJECT"
    )
    if (
        post.get("POST_source_evidence_count") != 4
        or post.get("POST_geometry_training_authority") is not False
        or post.get("POST_geometry_training_target_created") is not False
    ):
        _fail("GVE_POST_EVIDENCE_BOUNDARY_INVALID")

    _require_exact_mapping(
        formal.get("future_generic_Exact11_projection"),
        {
            "chemistry_disposition": "POSITIVE",
            "generic_fact_materialized_now": False,
            "human_review_completed": True,
            "human_training_excluded": False,
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "reconciliation_performed_now": False,
            "task_relevance_disposition": "NOT_RELEVANT",
            "training_disposition": "NOT_APPLICABLE",
        },
        "GVE_GENERIC_EXACT11_PREVIEW_INVALID",
    )
    legacy = _require_mapping(
        formal.get("legacy_1XD3_boundary"), "GVE_LEGACY_1XD3_BOUNDARY_NOT_OBJECT"
    )
    if (
        legacy.get("legacy_events_in_current_Exact4") is not False
        or legacy.get("legacy_context_current_queue_authority") is not False
        or legacy.get("legacy_decision_transferred") is not False
        or legacy.get("legacy_pair_promoted") is not False
    ):
        _fail("GVE_LEGACY_1XD3_AUTHORITY_COLLISION")
    debt = _require_mapping(
        formal.get("downstream_census_compatibility_note"),
        "GVE_CENSUS_CROSSFIELD_DEBT_NOT_OBJECT",
    )
    if (
        debt.get("generic_exact11_accepts_current_combination") is not True
        or debt.get("legacy_base_census_negative_semantics_assumption_detected")
        is not True
        or debt.get("legacy_assumption_must_not_override_human_D2_POSITIVE")
        is not True
        or debt.get("dedicated_with_GVE_census_crossfield_audit_required_later")
        is not True
    ):
        _fail("GVE_CENSUS_CROSSFIELD_DEBT_INVALID")
    operations = _require_mapping(
        formal.get("downstream_operations"), "GVE_DOWNSTREAM_OPERATIONS_NOT_OBJECT"
    )
    if any(value is not False for value in operations.values()):
        _fail("GVE_UNAUTHORIZED_DOWNSTREAM_OPERATION")
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


def _validate_projected_gve_source_v1(
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
        _fail("GVE_SOURCE_PROJECTION_IDENTITY_INVALID")
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
            _fail("GVE_SOURCE_PROJECTION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithGVEError(
                "GVE_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_gve_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic Exact11 facts from owner-validated GVE authority."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "GVE_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_owner_binding = {
        "path": _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _FORMAL_DECISION_SHA256,
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "GVE_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_JSON_AND_INDEPENDENTLY_VALIDATED",
    }
    if dict(binding_value) != expected_owner_binding:
        _fail("GVE_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_gve_semantics_v1(bound)
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
    _validate_projected_gve_source_v1(source)
    return source


def project_gve_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the GVE ingestion owner and project its narrow Exact4."""

    try:
        bound = gve_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except gve_ingestion_owner.GVEIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithGVEError(
            "GVE_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_gve_binding_v1(bound)


def _prove_gve_predecessor_historical_state_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove GVE is exactly one complete unreviewed predecessor unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithGVEError(
            "GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT")

    expected_ids = set(_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _REVIEW_UNIT_ID
    }
    legacy_1xd3_gve = [
        row
        for row in rows
        if ":1XD3:" in row["canonical_event_id"]
        and ":GVE:" in row["canonical_event_id"]
    ]
    if unit_event_ids != expected_ids or legacy_1xd3_gve:
        _fail("GVE_GENERIC_REVIEW_UNIT_COLLISION")
    if any(event_counts[event_id] != 1 for event_id in _EVENT_IDS):
        _fail("GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT")
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
        _fail("GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        generic._validate_historical_rows(rows)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithGVEError(
            "GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error


def load_real_completed_decision_sources_with_gve_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published with-SR2 chain and append one GVE source."""

    existing = sr2_predecessor.load_real_completed_decision_sources_with_sr2_v1(
        repo_root
    )
    actual_composition = tuple(len(source.facts) for source in existing)
    if (
        len(existing) != 19
        or actual_composition != _PREDECESSOR_SOURCE_FACT_COUNTS
    ):
        _fail("PREDECESSOR_WITH_SR2_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 119
        or len(set(existing_event_ids)) != 119
        or len({source.binding.review_unit_id for source in existing}) != 19
        or len({source.binding.stable_identity for source in existing}) != 19
    ):
        _fail("PREDECESSOR_WITH_SR2_SOURCE_CHAIN_NOT_EXACT19_119")

    gve_source = project_gve_completed_decision_v1(repo_root=repo_root)
    _validate_projected_gve_source_v1(gve_source)
    gve_event_ids = {fact.canonical_event_id for fact in gve_source.facts}
    overlap = gve_event_ids & set(existing_event_ids)
    if overlap:
        _fail("GVE_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])
    if gve_source.binding.review_unit_id in {
        source.binding.review_unit_id for source in existing
    }:
        _fail("GVE_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR")
    if gve_source.binding.stable_identity in {
        source.binding.stable_identity for source in existing
    }:
        _fail("GVE_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR")

    sources = (*existing, gve_source)
    if (
        len(sources) != 20
        or sources[:-1] != existing
        or sources[-1] != gve_source
        or tuple(len(source.facts) for source in sources)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or len({source.binding.review_unit_id for source in sources}) != 20
        or len({source.binding.stable_identity for source in sources}) != 20
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT20")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 123:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_123")
    if len(set(event_ids)) != 123:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def _validate_reconciliation_delta_v1(
    predecessor: generic.ReconciliationResult,
    successor: generic.ReconciliationResult,
) -> None:
    """Prove the successor is exactly the four-row generic GVE overlay."""

    if predecessor.review_summary != _BEFORE_SUMMARY:
        _fail("PREDECESSOR_WITH_SR2_REVIEW_SUMMARY_INVALID")
    if successor.review_summary != _AFTER_SUMMARY:
        _fail("GVE_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if (
        len(successor.source_bindings) != 20
        or len(successor.normalized_facts) != 123
        or len({binding.stable_identity for binding in successor.source_bindings})
        != 20
    ):
        _fail("GVE_RECONCILIATION_SOURCE_CHAIN_INVALID")
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
        _fail("GVE_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED")

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
            if before != after or changed_fields:
                _fail("GVE_NON_TARGET_ROW_CHANGED:" + event_id)
            unchanged_non_target_count += 1
            continue
        if changed_fields != _ALLOWED_RECONCILIATION_FIELDS:
            _fail("GVE_TARGET_CHANGED_FIELD_SET_INVALID:" + event_id)
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
            _fail("GVE_FINAL_RECONCILIATION_TRANSITION_INVALID:" + event_id)
        changed_target_count += 1
    if changed_target_count != 4 or unchanged_non_target_count != 334:
        _fail("GVE_RECONCILIATION_DELTA_NOT_EXACT4_OF_338")

    gve_facts = [
        fact
        for fact in successor.normalized_facts
        if fact.canonical_event_id in target_ids
    ]
    if len(gve_facts) != 4 or any(
        fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_NEGATIVE
        or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        for fact in gve_facts
    ):
        _fail("GVE_TASK_NEGATIVE_CHEMISTRY_POSITIVE_ORTHOGONALITY_INVALID")


def reconcile_real_completed_human_decisions_with_gve_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact20 sources through the generic owner, entirely in memory."""

    predecessor = (
        sr2_predecessor.reconcile_real_completed_human_decisions_with_sr2_v1(
            repo_root
        )
    )
    _prove_gve_predecessor_historical_state_v1(predecessor.reconciled_rows)

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_gve_predecessor_historical_state_v1(historical)
    original_snapshot = tuple(dict(row) for row in historical)
    adapted_historical = (
        sr2_predecessor.gd1_predecessor.four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != original_snapshot:
        _fail("ONL_ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    _prove_gve_predecessor_historical_state_v1(adapted_historical)

    sources = load_real_completed_decision_sources_with_gve_v1(repo_root)
    successor = generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
    _validate_reconciliation_delta_v1(predecessor, successor)
    return successor
