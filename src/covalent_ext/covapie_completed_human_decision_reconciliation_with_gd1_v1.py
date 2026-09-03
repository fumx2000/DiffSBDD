"""Reconcile published GD1 completion through the unchanged generic owner.

This metadata-only successor loads the rich GD1 Exact4 authority through its
published ingestion owner, proves the narrow-projection and training-exclusion
boundaries, appends one source to the published with-4M5 chain, and reconciles
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
    covapie_completed_human_decision_reconciliation_with_4m5_v1
    as four_m5_predecessor,
)
from . import (
    covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1
    as gd1_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithGD1Error",
    "project_gd1_completed_decision_v1",
    "load_real_completed_decision_sources_with_gd1_v1",
    "reconcile_real_completed_human_decisions_with_gd1_v1",
)


_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    gd1_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_FORMAL_DECISION_BYTE_COUNT = gd1_ingestion_owner.FORMAL_BINDINGS[0][2]
_FORMAL_DECISION_SHA256 = gd1_ingestion_owner.FORMAL_BINDINGS[0][3]
_FORMAL_DECISION_SCHEMA = gd1_ingestion_owner.FORMAL_DECISION_SCHEMA
_FORMAL_SEMANTIC_SHA256 = (
    gd1_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_REVIEW_UNIT_ID = gd1_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_ROLE_PROFILE = gd1_ingestion_owner.EXPECTED_ROLE_PROFILE
_EVENT_IDS = gd1_ingestion_owner.EXPECTED_EVENT_IDS
_RANKS = gd1_ingestion_owner.EXPECTED_RANKS

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "21"
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
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
    "tensor_target",
    "training_use_allowed",
    "training_materialization_allowed",
    "current_runtime_model_usable",
)
_EXPECTED_DECISIONS = {
    "D1_task_relevance": "RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_candidate": "SELECT_CANDIDATE_0",
    "D5_training_use": "EXCLUDE_FROM_TRAINING_ONLY",
}
_BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 107,
    "completed_positive_unit_count": 16,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 135,
    "completed_total_unit_count": 21,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 203,
    "unreviewed_unit_count": 110,
}
_AFTER_SUMMARY = {
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
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    (
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    )
)


class CompletedDecisionReconciliationWithGD1Error(ValueError):
    """Raised when the exact GD1 reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithGD1Error(token)


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


def _validate_rich_gd1_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove published rich GD1 authority before projection."""

    if (
        bound.get("formal_semantics_independently_validated") is not True
        or bound.get("formal_validator_provenance_identity_only") is not True
        or bound.get("formal_validator_imported") is not False
        or bound.get("formal_validator_executed") is not False
        or bound.get("formal_validator_subprocess", False) is not False
    ):
        _fail("GD1_INGESTION_OWNER_OR_FORMAL_VALIDATOR_BOUNDARY_INVALID")

    formal = _require_mapping(bound.get("formal"), "GD1_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != _FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != gd1_ingestion_owner.FORMAL_RECORD_ROLE
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
        _fail("GD1_FORMAL_COMPLETION_OR_SEMANTIC_DIGEST_INVALID")

    human = _require_mapping(
        formal.get("human_authorization"),
        "GD1_HUMAN_AUTHORIZATION_NOT_OBJECT",
    )
    unit = _require_mapping(
        formal.get("unit_human_decision"),
        "GD1_UNIT_DECISION_NOT_OBJECT",
    )
    if any(
        human.get(key) != value or unit.get(key) != value
        for key, value in _EXPECTED_DECISIONS.items()
    ):
        _fail("GD1_D1_D5_DECISIONS_INVALID")
    if (
        human.get("human_selected_role_candidate_index_0based") != 0
        or human.get("human_selected_role_profile") != _ROLE_PROFILE
        or human.get("human_choices_externally_authorized") is not True
        or human.get("formal_decision_authority_is_human") is not True
        or human.get("machine_approval_claimed") is not False
        or unit.get("exact_event_count") != _EVENT_COUNT
        or unit.get("completed_human_review_event_count") != _EVENT_COUNT
        or unit.get("seventh_decision_present") is not False
    ):
        _fail("GD1_HUMAN_SELECTION_OR_UNIT_COMPLETION_INVALID")

    identity = _require_mapping(
        formal.get("identity"), "GD1_IDENTITY_NOT_OBJECT"
    )
    if (
        identity.get("review_unit_id") != _REVIEW_UNIT_ID
        or identity.get("canonical_event_ids") != list(_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_RANKS)
        or identity.get("pdb_ids") != ["4F8B"]
        or identity.get("ligand_component_id") != "GD1"
        or identity.get("protein_reactive_atom") != "SG"
        or identity.get("ligand_reactive_atom") != "C77"
        or identity.get("exact_event_count") != _EVENT_COUNT
        or identity.get("explicit_covalent_evidence") is not True
        or identity.get("distance_only_inference") is not False
        or identity.get("contexts_collapsed") is not False
    ):
        _fail("GD1_FORMAL_IDENTITY_NOT_EXACT4")

    pair = _require_mapping(
        formal.get("reactive_pair_authority"),
        "GD1_REACTIVE_PAIR_AUTHORITY_NOT_OBJECT",
    )
    if (
        pair.get("D3_human_choice") != "CONFIRM_OBSERVED_PAIR"
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "C77"
        or pair.get("authority_scope") != gd1_ingestion_owner.AUTHORITY_SCOPE
        or pair.get("observed_pair_authority_created") is not True
        or pair.get("reusable_pair_rule_created") is not False
        or pair.get("cross_structure_regiochemistry_generalization") is not False
    ):
        _fail("GD1_SG_C77_PAIR_AUTHORITY_INVALID")

    role = _require_mapping(
        formal.get("selected_role_partition"),
        "GD1_SELECTED_ROLE_PARTITION_NOT_OBJECT",
    )
    runtime = _require_mapping(
        role.get("published_DIRECT_runtime_validation"),
        "GD1_ROLE_RUNTIME_VALIDATION_NOT_OBJECT",
    )
    expected_boundary = [dict(gd1_ingestion_owner.BOUNDARY_BONDS[0])]
    if (
        role.get("D4_human_choice") != "SELECT_CANDIDATE_0"
        or role.get("selected_candidate_index_0based") != 0
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("candidate_index_is_recommendation") is not False
        or role.get("role_profile") != _ROLE_PROFILE
        or role.get("W") != list(gd1_ingestion_owner.WARHEAD_ROLE)
        or role.get("L") != []
        or role.get("S") != list(gd1_ingestion_owner.SCAFFOLD_ROLE)
        or role.get("W_L_S_counts") != [2, 0, 11]
        or role.get("boundary_bonds") != expected_boundary
        or role.get("applicable_task_ids") != [0, 3, 4]
        or role.get("current_review_unit_role_partition_human_authority")
        is not True
        or role.get("reusable_role_rule_created") is not False
        or role.get("role_authority_scope")
        != gd1_ingestion_owner.AUTHORITY_SCOPE
        or runtime.get("profile") != _ROLE_PROFILE
        or runtime.get("applicable_task_ids") != [0, 3, 4]
        or runtime.get("valid") is not True
        or runtime.get("warhead_count") != 2
        or runtime.get("linker_count") != 0
        or runtime.get("scaffold_count") != 11
        or runtime.get("direct_scaffold_warhead_boundary")
        != {
            "bond_order": "SING",
            "boundary_valid": True,
            "scaffold_atom_id": "C7",
            "warhead_atom_id": "C77",
        }
    ):
        _fail("GD1_CANDIDATE0_DIRECT_ROLE_PARTITION_INVALID")

    structural = _require_mapping(
        role.get("independent_structural_validation"),
        "GD1_STRUCTURAL_VALIDATION_NOT_OBJECT",
    )
    if (
        structural.get("Exact13_count") != 13
        or structural.get("W_count") != 2
        or structural.get("L_count") != 0
        or structural.get("S_count") != 11
        or structural.get("C77_in_W") is not True
        or structural.get("partition_pairwise_disjoint") is not True
        or structural.get("partition_exhaustive") is not True
        or structural.get("cross_role_boundary_bonds") != expected_boundary
    ):
        _fail("GD1_EXACT13_ROLE_VALIDATION_INVALID")

    canonical = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "GD1_CANONICAL_TASK_CONTRACT_NOT_OBJECT",
    )
    tasks = _require_list(
        canonical.get("global_canonical_Exact5"),
        "GD1_CANONICAL_TASKS_NOT_LIST",
    )
    expected_tasks = [
        {"display_alias": alias, "semantic_name": semantic, "task_id": task_id}
        for task_id, semantic, alias, _generated, _fixed
        in gd1_ingestion_owner.CANONICAL_TASKS
    ]
    if (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 3, 4]
        or canonical.get("role_profile") != _ROLE_PROFILE
        or canonical.get("authoritative_task_labels_created") is not False
        or canonical.get("event_task_label_rows_materialized") is not False
        or tasks != expected_tasks
    ):
        _fail("GD1_CANONICAL_EXACT5_APPLICABILITY_INVALID")

    training = _require_mapping(
        formal.get("training_use_boundary"),
        "GD1_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    expected_training = {
        "D5_human_choice": "EXCLUDE_FROM_TRAINING_ONLY",
        "training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded": True,
        "formal_training_admitted": False,
        "future_training_admission_candidate": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "READY_FOR_TRAINING": False,
    }
    derived_training = gd1_ingestion_owner._training_boundary()
    expected_derived_training = {
        "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
        "training_use_allowed": False,
        "human_training_excluded": True,
        "candidate_for_future_training_admission": False,
        "future_training_admission_candidate": False,
        "formal_training_admitted": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "model_supervision_usable": False,
        "current_runtime_model_usable": False,
        "READY_FOR_TRAINING": False,
    }
    if any(
        training.get(key) != value for key, value in expected_training.items()
    ) or any(
        derived_training.get(key) != value
        for key, value in expected_derived_training.items()
    ):
        _fail("GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID")

    pre = _require_mapping(
        formal.get("PRE_POST_boundary"), "GD1_PRE_BOUNDARY_NOT_OBJECT"
    )
    post = _require_mapping(
        formal.get("POST_evidence_boundary"),
        "GD1_POST_BOUNDARY_NOT_OBJECT",
    )
    if (
        pre.get("PRE_source_graph_present") is not False
        or pre.get("PRE_source_graph_count_per_event") != 0
        or pre.get("PRE_mapping_count_per_event") != 0
        or pre.get("PRE_mapping_status") != gd1_ingestion_owner.PRE_MAPPING_STATUS
        or pre.get("PRE_status") != gd1_ingestion_owner.PRE_STATUS
        or pre.get("PRE_topology_authority") is not False
        or pre.get("PRE_geometry_authority") is not False
        or pre.get("PRE_coordinates_authority") is not False
        or pre.get("POST_to_PRE_copy_performed") is not False
        or pre.get("PRE_zero_fill_performed") is not False
        or post.get("POST_source_evidence_available") is not True
        or post.get("POST_source_evidence_count") != 4
        or post.get("observed_distances_angstrom")
        != [row[5] for row in gd1_ingestion_owner.EXPECTED_EVENTS]
        or post.get("POST_geometry_training_authority") is not False
        or post.get("POST_geometry_training_target_created") is not False
    ):
        _fail("GD1_RICH_PRE_POST_BOUNDARY_INVALID")

    authority = _require_mapping(
        formal.get("authority_boundary"),
        "GD1_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    unauthorized_true = (
        "POST_geometry_training_authority_created",
        "PRE_geometry_authority_created",
        "PRE_topology_authority_created",
        "READY_FOR_TRAINING",
        "authoritative_task_labels_created",
        "current_runtime_model_usable",
        "event_task_label_rows_created",
        "formal_training_admitted",
        "machine_approval",
        "parameter_update_authorization",
        "reaction_family_authority_created",
        "reusable_chemistry_authority_created",
        "reusable_pair_authority_created",
        "reusable_role_authority_created",
        "tensor_target_created",
        "training_admission_created",
        "training_started",
        "warhead_rule_authority_created",
        "warhead_type_authority_created",
    )
    if any(authority.get(key) is not False for key in unauthorized_true):
        _fail("GD1_RICH_AUTHORITY_BOUNDARY_INVALID")
    reusable = _require_mapping(
        formal.get("reusable_authority_boundary"),
        "GD1_REUSABLE_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    if any(value is not False for value in reusable.values()):
        _fail("GD1_RICH_AUTHORITY_BOUNDARY_INVALID")

    semantic = _require_mapping(
        bound.get("semantic_contract"),
        "GD1_SEMANTIC_CONTRACT_NOT_OBJECT",
    )
    if dict(semantic) != {
        "role_profile": _ROLE_PROFILE,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "B3_present": True,
        "sixth_task_present": False,
    }:
        _fail("GD1_PUBLISHED_SEMANTIC_CONTRACT_INVALID")

    events = _require_list(
        formal.get("event_level_formal_human_decisions"),
        "GD1_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _EVENT_COUNT:
        _fail("GD1_FORMAL_EVENT_COUNT_NOT_EXACT4")
    typed_events = tuple(
        _require_mapping(event, "GD1_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    for event, expected in zip(
        typed_events, gd1_ingestion_owner.EXPECTED_EVENTS, strict=True
    ):
        event_id = event.get("canonical_event_id")
        rank = event.get("scaleup_rank")
        observed_ids.append(str(event_id))
        if type(rank) is int:
            observed_ranks.append(rank)
        projected = gd1_ingestion_owner._event_projection(expected)
        if (
            event_id != expected[0]
            or rank != expected[1]
            or event.get("protein_asym") != expected[2]
            or event.get("ligand_asym") != expected[3]
            or event.get("selected_connection_id") != expected[4]
            or event.get("POST_distance_angstrom") != expected[5]
            or event.get("protein_reactive_atom") != "SG"
            or event.get("ligand_component_id") != "GD1"
            or event.get("ligand_reactive_atom") != "C77"
            or any(
                event.get(key) != value
                for key, value in _EXPECTED_DECISIONS.items()
            )
            or event.get("human_training_excluded") is not True
            or event.get("sample_level_formal_authority") is not True
            or event.get("explicit_covalent_evidence") is not True
            or event.get("distance_only_inference") is not False
            or event.get("POST_geometry_training_authority") is not False
            or event.get("formal_training_admitted") is not False
            or projected.get("completed_lane")
            != gd1_ingestion_owner.EXPECTED_COMPLETED_LANE
            or projected.get("training_use_allowed") is not False
            or projected.get("future_training_admission_candidate") is not False
            or projected.get("model_supervision_usable") is not False
            or projected.get("current_runtime_model_usable") is not False
        ):
            _fail("GD1_RICH_EVENT_SEMANTICS_INVALID:" + str(event_id))
    if (
        tuple(observed_ids) != _EVENT_IDS
        or tuple(observed_ranks) != _RANKS
        or len(set(observed_ids)) != _EVENT_COUNT
        or set(observed_ids) != set(_EVENT_IDS)
    ):
        _fail("GD1_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
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


def _validate_projected_gd1_source_v1(
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
        _fail("GD1_SOURCE_PROJECTION_IDENTITY_INVALID")
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
            or fact.training_disposition != generic.TRAINING_EXCLUDE
            or fact.human_training_excluded is not True
            or fact.source_decision_schema != _FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _FORMAL_DECISION_SHA256
            or fact.source_binding_path != expected_binding.source_path
        ):
            _fail("GD1_SOURCE_PROJECTION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithGD1Error(
                "GD1_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_gd1_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic Exact11 facts from owner-validated GD1 authority."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "GD1_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_owner_binding = {
        "path": _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _FORMAL_DECISION_SHA256,
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "GD1_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if dict(binding_value) != expected_owner_binding:
        _fail("GD1_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_gd1_semantics_v1(bound)
    facts = tuple(
        generic.NormalizedCompletedDecisionFact(
            canonical_event_id=str(event["canonical_event_id"]),
            review_unit_id=_REVIEW_UNIT_ID,
            human_review_completed=True,
            legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
            task_relevance_disposition=generic.TASK_RELEVANT,
            chemistry_disposition=generic.CHEMISTRY_POSITIVE,
            training_disposition=generic.TRAINING_EXCLUDE,
            human_training_excluded=True,
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
    _validate_projected_gd1_source_v1(source)
    return source


def project_gd1_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the GD1 ingestion owner and project its narrow Exact4."""

    try:
        bound = gd1_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except gd1_ingestion_owner.GD1IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithGD1Error(
            "GD1_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_gd1_binding_v1(bound)


def _prove_gd1_predecessor_historical_state_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove GD1 is exactly one complete unreviewed predecessor unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithGD1Error(
            "GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT")

    expected_ids = set(_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    if any(event_counts[event_id] != 1 for event_id in _EVENT_IDS):
        _fail("GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT")
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
        _fail("GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT")
    try:
        generic._validate_historical_rows(rows)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithGD1Error(
            "GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT"
        ) from error


def load_real_completed_decision_sources_with_gd1_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published with-4M5 chain and append one GD1 source."""

    existing = (
        four_m5_predecessor.load_real_completed_decision_sources_with_4m5_v1(
            repo_root
        )
    )
    actual_composition = tuple(len(source.facts) for source in existing)
    if (
        len(existing) != 17
        or actual_composition != _PREDECESSOR_SOURCE_FACT_COUNTS
    ):
        _fail("PREDECESSOR_WITH_4M5_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 111
        or len(set(existing_event_ids)) != 111
        or len({source.binding.review_unit_id for source in existing}) != 17
        or len({source.binding.stable_identity for source in existing}) != 17
    ):
        _fail("PREDECESSOR_WITH_4M5_SOURCE_CHAIN_NOT_EXACT17_111")

    gd1_source = project_gd1_completed_decision_v1(repo_root=repo_root)
    _validate_projected_gd1_source_v1(gd1_source)
    gd1_event_ids = {fact.canonical_event_id for fact in gd1_source.facts}
    overlap = gd1_event_ids & set(existing_event_ids)
    if overlap:
        _fail("GD1_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])
    if gd1_source.binding.review_unit_id in {
        source.binding.review_unit_id for source in existing
    }:
        _fail("GD1_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR")
    if gd1_source.binding.stable_identity in {
        source.binding.stable_identity for source in existing
    }:
        _fail("GD1_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR")

    sources = (*existing, gd1_source)
    if (
        len(sources) != 18
        or sources[:-1] != existing
        or tuple(len(source.facts) for source in sources)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or len({source.binding.review_unit_id for source in sources}) != 18
        or len({source.binding.stable_identity for source in sources}) != 18
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT18")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 115:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_115")
    if len(set(event_ids)) != 115:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def _validate_reconciliation_delta_v1(
    predecessor: generic.ReconciliationResult,
    successor: generic.ReconciliationResult,
) -> None:
    """Prove the successor is exactly the four-row generic GD1 overlay."""

    if predecessor.review_summary != _BEFORE_SUMMARY:
        _fail("PREDECESSOR_WITH_4M5_REVIEW_SUMMARY_INVALID")
    if successor.review_summary != _AFTER_SUMMARY:
        _fail("GD1_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if (
        len(successor.source_bindings) != 18
        or len(successor.normalized_facts) != 115
    ):
        _fail("GD1_RECONCILIATION_SOURCE_CHAIN_INVALID")
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
        _fail("GD1_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED")

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
                _fail("GD1_NON_TARGET_ROW_CHANGED:" + event_id)
            unchanged_non_target_count += 1
            continue
        if changed_fields != _ALLOWED_RECONCILIATION_FIELDS:
            _fail("GD1_TARGET_CHANGED_FIELD_SET_INVALID:" + event_id)
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
            _fail("GD1_FINAL_RECONCILIATION_TRANSITION_INVALID:" + event_id)
        changed_target_count += 1
    if changed_target_count != 4 or unchanged_non_target_count != 334:
        _fail("GD1_RECONCILIATION_DELTA_NOT_EXACT4_OF_338")

    gd1_facts = [
        fact
        for fact in successor.normalized_facts
        if fact.canonical_event_id in target_ids
    ]
    if len(gd1_facts) != 4 or any(
        fact.training_disposition != generic.TRAINING_EXCLUDE
        or fact.human_training_excluded is not True
        or fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_POSITIVE
        for fact in gd1_facts
    ):
        _fail("GD1_TRAINING_EXCLUSION_OR_POSITIVE_STATUS_ORTHOGONALITY_INVALID")


def reconcile_real_completed_human_decisions_with_gd1_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact18 sources through the generic owner, entirely in memory."""

    predecessor = (
        four_m5_predecessor.reconcile_real_completed_human_decisions_with_4m5_v1(
            repo_root
        )
    )
    _prove_gd1_predecessor_historical_state_v1(predecessor.reconciled_rows)

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_gd1_predecessor_historical_state_v1(historical)
    original_snapshot = tuple(dict(row) for row in historical)
    adapted_historical = (
        four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != original_snapshot:
        _fail("ONL_ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    _prove_gd1_predecessor_historical_state_v1(adapted_historical)

    sources = load_real_completed_decision_sources_with_gd1_v1(repo_root)
    successor = generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
    _validate_reconciliation_delta_v1(predecessor, successor)
    return successor
