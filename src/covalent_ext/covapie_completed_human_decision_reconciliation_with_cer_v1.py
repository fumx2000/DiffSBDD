"""Reconcile published CER completion through the unchanged generic owner.

This metadata-only successor loads the rich CER Exact4 authority through its
published ingestion owner, proves the narrow-projection boundary, appends one
source to the published with-1N0 chain, and reconciles the fixed historical
population in memory.  It writes no artifact and creates no census, queue,
tensor, training-admission, or model authority.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import (
    covapie_cer_completed_decision_ingestion_and_task_label_availability_v1
    as cer_ingestion_owner,
)
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_1n0_v1
    as one_n0_predecessor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)


__all__ = (
    "CompletedDecisionReconciliationWithCERError",
    "project_cer_completed_decision_v1",
    "load_real_completed_decision_sources_with_cer_v1",
    "reconcile_real_completed_human_decisions_with_cer_v1",
)


_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    cer_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_FORMAL_DECISION_BYTE_COUNT = cer_ingestion_owner.FORMAL_BINDINGS[0][2]
_FORMAL_DECISION_SHA256 = cer_ingestion_owner.FORMAL_BINDINGS[0][3]
_FORMAL_DECISION_SCHEMA = cer_ingestion_owner.FORMAL_DECISION_SCHEMA
_FORMAL_SEMANTIC_SHA256 = (
    cer_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_REVIEW_UNIT_ID = cer_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_ROLE_PROFILE = cer_ingestion_owner.EXPECTED_ROLE_PROFILE
_EVENT_IDS = cer_ingestion_owner.EXPECTED_EVENT_IDS
_RANKS = cer_ingestion_owner.EXPECTED_RANKS

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "19"
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
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
)
_EXPECTED_DECISIONS = {
    "D1_task_relevance": "RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_candidate": "SELECT_CANDIDATE_3",
    "D5_training_use": "INCLUDE",
}
_BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 99,
    "completed_positive_unit_count": 14,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 127,
    "completed_total_unit_count": 19,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 211,
    "unreviewed_unit_count": 112,
}
_AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 103,
    "completed_positive_unit_count": 15,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 131,
    "completed_total_unit_count": 20,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 207,
    "unreviewed_unit_count": 111,
}
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    (
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    )
)


class CompletedDecisionReconciliationWithCERError(ValueError):
    """Raised when the exact CER reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithCERError(token)


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


def _validate_rich_cer_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove the published rich CER boundary before projection."""

    if bound.get("formal_semantics_independently_validated") is not True:
        _fail("CER_INGESTION_OWNER_SEMANTIC_VALIDATION_NOT_PROVEN")
    formal = _require_mapping(bound.get("formal"), "CER_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != _FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != cer_ingestion_owner.FORMAL_RECORD_ROLE
        or formal.get("formal_semantic_canonical_sha256")
        != _FORMAL_SEMANTIC_SHA256
        or formal.get("unsigned") is not False
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
        or formal.get("human_review_completed") is not True
        or formal.get("human_decision_created") is not True
        or formal.get("formal_authority_created") is not True
    ):
        _fail("CER_FORMAL_COMPLETION_OR_SEMANTIC_DIGEST_INVALID")

    human = _require_mapping(
        formal.get("human_authorization"),
        "CER_HUMAN_AUTHORIZATION_NOT_OBJECT",
    )
    unit = _require_mapping(
        formal.get("unit_human_decision"),
        "CER_UNIT_DECISION_NOT_OBJECT",
    )
    if any(
        human.get(key) != value or unit.get(key) != value
        for key, value in _EXPECTED_DECISIONS.items()
    ):
        _fail("CER_D1_D5_DECISIONS_INVALID")
    if (
        human.get("human_selected_role_candidate_index_0based") != 3
        or human.get("human_selected_role_profile") != _ROLE_PROFILE
        or human.get("human_choices_externally_authorized") is not True
        or human.get("machine_approval_claimed") is not False
        or unit.get("exact_event_count") != _EVENT_COUNT
        or unit.get("completed_human_review_event_count") != _EVENT_COUNT
    ):
        _fail("CER_HUMAN_SELECTION_OR_UNIT_COMPLETION_INVALID")

    identity = _require_mapping(formal.get("identity"), "CER_IDENTITY_NOT_OBJECT")
    if (
        identity.get("review_unit_id") != _REVIEW_UNIT_ID
        or identity.get("canonical_event_ids") != list(_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_RANKS)
        or identity.get("pdb_ids") != ["1FJ8"]
        or identity.get("ligand_component_id") != "CER"
        or identity.get("protein_reactive_atom") != "SG"
        or identity.get("ligand_reactive_atom") != "C2"
        or identity.get("exact_event_count") != _EVENT_COUNT
        or identity.get("explicit_covalent_evidence") is not True
        or identity.get("distance_only_inference") is not False
    ):
        _fail("CER_FORMAL_IDENTITY_NOT_EXACT4")

    role = _require_mapping(
        formal.get("selected_role_partition"),
        "CER_SELECTED_ROLE_PARTITION_NOT_OBJECT",
    )
    runtime = _require_mapping(
        role.get("published_role_runtime_validation"),
        "CER_ROLE_RUNTIME_VALIDATION_NOT_OBJECT",
    )
    expected_boundary = [
        {
            "aromatic_flag": "N",
            "atom_id_1": "C4",
            "atom_id_2": "C5",
            "bond_order": "SING",
            "role_1": "W",
            "role_2": "S",
        }
    ]
    if (
        role.get("D4_human_choice") != "SELECT_CANDIDATE_3"
        or role.get("selected_candidate_index_0based") != 3
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("role_profile") != _ROLE_PROFILE
        or role.get("warhead_role_atom_ids")
        != list(cer_ingestion_owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids")
        != list(cer_ingestion_owner.SCAFFOLD_ROLE)
        or role.get("boundary_bonds") != expected_boundary
        or role.get("applicable_task_ids") != [0, 3, 4]
        or role.get("partition_pairwise_disjoint") is not True
        or role.get("partition_exhaustive") is not True
        or role.get("current_review_unit_role_partition_human_authority")
        is not True
        or role.get("reusable_role_rule_created") is not False
        or runtime.get("profile") != _ROLE_PROFILE
        or runtime.get("applicable_task_ids") != [0, 3, 4]
        or runtime.get("valid") is not True
    ):
        _fail("CER_CANDIDATE3_DIRECT_ROLE_PARTITION_INVALID")

    canonical = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "CER_CANONICAL_TASK_CONTRACT_NOT_OBJECT",
    )
    tasks = _require_list(
        canonical.get("global_canonical_Exact5"),
        "CER_CANONICAL_TASKS_NOT_LIST",
    )
    expected_tasks = [
        {"task_id": task_id, "semantic_name": semantic, "short_alias": alias}
        for task_id, semantic, alias, _generated, _fixed
        in cer_ingestion_owner.CANONICAL_TASKS
    ]
    if (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 3, 4]
        or canonical.get("sample_role_profile") != _ROLE_PROFILE
        or canonical.get("sample_applicability_scope")
        != "CURRENT_CER_EXACT4_REVIEW_UNIT_ONLY"
        or canonical.get("authoritative_task_labels_created") is not False
        or canonical.get("event_task_label_rows_materialized") is not False
        or tasks != expected_tasks
    ):
        _fail("CER_CANONICAL_EXACT5_APPLICABILITY_INVALID")

    pair = _require_mapping(
        formal.get("reactive_pair_authority"),
        "CER_REACTIVE_PAIR_AUTHORITY_NOT_OBJECT",
    )
    chemistry = _require_mapping(
        formal.get("chemistry_authority_boundary"),
        "CER_CHEMISTRY_BOUNDARY_NOT_OBJECT",
    )
    training = _require_mapping(
        formal.get("training_use_boundary"),
        "CER_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    pre = _require_mapping(
        formal.get("PRE_POST_boundary"),
        "CER_PRE_BOUNDARY_NOT_OBJECT",
    )
    post = _require_mapping(
        formal.get("POST_evidence_boundary"),
        "CER_POST_BOUNDARY_NOT_OBJECT",
    )
    authority = _require_mapping(
        formal.get("authority_boundary"),
        "CER_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    if (
        pair.get("D3_human_choice") != "CONFIRM_OBSERVED_PAIR"
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "C2"
        or pair.get("pair_scope") != cer_ingestion_owner.AUTHORITY_SCOPE
        or pair.get("observed_pair_authority_created") is not True
        or pair.get("cross_structure_regiochemistry_generalization") is not False
        or pair.get("reusable_pair_rule_created") is not False
        or chemistry.get("D2_human_choice") != "POSITIVE"
        or chemistry.get("current_review_unit_chemistry_positive_authority")
        is not True
        or chemistry.get("chemical_warhead_human_authority") is not False
        or chemistry.get("reaction_family_authority_created") is not False
        or chemistry.get("reusable_chemistry_authority_created") is not False
        or chemistry.get("reusable_chemistry_rule_created") is not False
        or chemistry.get("warhead_family_authority_created") is not False
        or chemistry.get("warhead_rule_authority_created") is not False
        or chemistry.get("warhead_type_reusable_authority_created") is not False
        or training.get("D5_human_choice") != "INCLUDE"
        or training.get("human_training_use_disposition") != "INCLUDE"
        or training.get("human_training_use_disposition_authority_created")
        is not True
        or training.get("future_training_admission_candidate") is not True
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed") is not False
        or training.get("tensor_target_created") is not False
        or pre.get("PRE_status") != cer_ingestion_owner.PRE_STATUS
        or pre.get("PRE_topology_authority") is not False
        or pre.get("PRE_geometry_authority") is not False
        or pre.get("POST_to_PRE_copy_performed") is not False
        or pre.get("PRE_zero_fill_performed") is not False
        or post.get("POST_source_evidence_available") is not True
        or post.get("POST_source_evidence_count") != _EVENT_COUNT
        or post.get("POST_geometry_training_authority") is not False
        or post.get("POST_geometry_training_target_created") is not False
    ):
        _fail("CER_RICH_PAIR_CHEMISTRY_GEOMETRY_OR_TRAINING_BOUNDARY_INVALID")

    required_true = (
        "sample_level_task_relevance_authority_created",
        "sample_level_chemistry_positive_authority_created",
        "sample_level_reactive_pair_authority_created",
        "sample_level_canonical_role_partition_authority_created",
        "sample_level_role_profile_task_applicability_determined",
        "sample_level_training_use_human_decision_authority_created",
    )
    required_false = (
        "reaction_family_authority_created",
        "reusable_chemistry_authority_created",
        "reusable_pair_authority_created",
        "reusable_role_authority_created",
        "warhead_family_authority_created",
        "warhead_rule_authority_created",
        "warhead_type_authority_created",
        "PRE_topology_authority_created",
        "PRE_geometry_authority_created",
        "POST_geometry_training_authority_created",
        "formal_training_admitted",
        "training_admission_created",
        "tensor_target_created",
        "training_started",
        "READY_FOR_TRAINING",
    )
    if any(authority.get(key) is not True for key in required_true) or any(
        authority.get(key) is not False for key in required_false
    ):
        _fail("CER_RICH_AUTHORITY_BOUNDARY_INVALID")

    semantic = _require_mapping(
        bound.get("semantic_contract"),
        "CER_SEMANTIC_CONTRACT_NOT_OBJECT",
    )
    if dict(semantic) != {
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "role_profile": _ROLE_PROFILE,
        "direct_profile_applicable_task_ids": [0, 3, 4],
    }:
        _fail("CER_PUBLISHED_SEMANTIC_CONTRACT_INVALID")

    derived_pair = cer_ingestion_owner._pair_authority_boundary()
    derived_reusable = cer_ingestion_owner._reusable_authority_boundary()
    derived_geometry = cer_ingestion_owner._geometry_boundary()
    derived_training = cer_ingestion_owner._training_boundary()
    if (
        derived_pair.get("protein_reactive_atom") != "SG"
        or derived_pair.get("ligand_reactive_atom") != "C2"
        or derived_pair.get("authority_scope")
        != cer_ingestion_owner.AUTHORITY_SCOPE
        or derived_pair.get("reusable_pair_rule_created") is not False
        or any(derived_reusable.get(key) is not False for key in derived_reusable)
        or derived_geometry.get("PRE_status") != cer_ingestion_owner.PRE_STATUS
        or derived_geometry.get("POST_geometry_training_authority") is not False
        or derived_training.get("formal_training_admitted") is not False
        or derived_training.get("training_materialization_allowed") is not False
        or derived_training.get("tensor_target_created") is not False
        or derived_training.get("READY_FOR_TRAINING") is not False
    ):
        _fail("CER_INGESTION_DERIVED_AUTHORITY_BOUNDARY_INVALID")

    events = _require_list(
        formal.get("event_level_human_decisions"),
        "CER_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _EVENT_COUNT:
        _fail("CER_FORMAL_EVENT_COUNT_NOT_EXACT4")
    typed_events = tuple(
        _require_mapping(event, "CER_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    for event, expected in zip(
        typed_events, cer_ingestion_owner.EXPECTED_EVENTS, strict=True
    ):
        event_id = event.get("canonical_event_id")
        observed_ids.append(str(event_id))
        rank = event.get("scaleup_rank")
        if type(rank) is int:
            observed_ranks.append(rank)
        if (
            event_id != expected[0]
            or rank != expected[1]
            or event.get("pdb_id") != "1FJ8"
            or event.get("protein_asym") != expected[2]
            or event.get("ligand_asym") != expected[3]
            or event.get("selected_connection_id") != expected[4]
            or event.get("protein_residue") != "CYS:163-"
            or event.get("protein_reactive_atom") != "SG"
            or event.get("ligand_component_id") != "CER"
            or event.get("ligand_reactive_atom") != "C2"
            or event.get("D1_task_relevance") != "RELEVANT"
            or event.get("D2_chemistry") != "POSITIVE"
            or event.get("D3_reactive_pair") != "CONFIRM_OBSERVED_PAIR"
            or event.get("D4_role_partition") != "SELECT_CANDIDATE_3"
            or event.get("D5_training_use") != "INCLUDE"
            or event.get("task_relevance_human_authoritative") is not True
            or event.get("chemistry_human_authoritative") is not True
            or event.get("reactive_pair_human_authoritative") is not True
            or event.get("role_partition_human_authoritative") is not True
            or event.get("training_use_human_authoritative") is not True
            or event.get("POST_sample_authority") is not False
            or event.get("POST_training_target_authority") is not False
            or event.get("formal_training_admitted") is not False
        ):
            _fail("CER_RICH_EVENT_SEMANTICS_INVALID:" + str(event_id))
    if (
        tuple(observed_ids) != _EVENT_IDS
        or tuple(observed_ranks) != _RANKS
        or len(set(observed_ids)) != _EVENT_COUNT
        or set(observed_ids) != set(_EVENT_IDS)
    ):
        _fail("CER_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
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


def _validate_projected_cer_source_v1(
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
        _fail("CER_SOURCE_PROJECTION_IDENTITY_INVALID")
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
            _fail("CER_SOURCE_PROJECTION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithCERError(
                "CER_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_cer_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic Exact11 facts from owner-validated CER authority."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "CER_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_owner_binding = {
        "path": _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _FORMAL_DECISION_SHA256,
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "CER_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if dict(binding_value) != expected_owner_binding:
        _fail("CER_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_cer_semantics_v1(bound)
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
    _validate_projected_cer_source_v1(source)
    return source


def project_cer_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the CER ingestion owner and project its narrow Exact4."""

    try:
        bound = cer_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except cer_ingestion_owner.CERIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithCERError(
            "CER_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_cer_binding_v1(bound)


def _prove_cer_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove CER is exactly one complete unreviewed historical unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("CER_RECONCILIATION_PRECONDITION_FAILED")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithCERError(
            "CER_RECONCILIATION_PRECONDITION_FAILED"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("CER_RECONCILIATION_PRECONDITION_FAILED")

    expected_ids = set(_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    if any(event_counts[event_id] != 1 for event_id in _EVENT_IDS):
        _fail("CER_RECONCILIATION_PRECONDITION_FAILED")
    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("CER_RECONCILIATION_PRECONDITION_FAILED")
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
        _fail("CER_RECONCILIATION_PRECONDITION_FAILED")
    try:
        generic._validate_historical_rows(rows)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithCERError(
            "CER_RECONCILIATION_PRECONDITION_FAILED"
        ) from error


def _prove_cer_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the published ONL normalizer changes zero CER row fields."""

    expected_ids = set(_EVENT_IDS)
    original_by_event = {
        row["canonical_event_id"]: row
        for row in original_rows
        if row["canonical_event_id"] in expected_ids
    }
    adapted_by_event = {
        row["canonical_event_id"]: row
        for row in adapted_rows
        if row["canonical_event_id"] in expected_ids
    }
    if set(original_by_event) != expected_ids or set(adapted_by_event) != expected_ids:
        _fail("CER_RECONCILIATION_PRECONDITION_FAILED")
    changed = [
        event_id
        for event_id in _EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_CER_ROW:" + changed[0])


def load_real_completed_decision_sources_with_cer_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published with-1N0 chain and append one CER source."""

    existing = (
        one_n0_predecessor.load_real_completed_decision_sources_with_1n0_v1(
            repo_root
        )
    )
    if (
        len(existing) != 15
        or tuple(len(source.facts) for source in existing)
        != _PREDECESSOR_SOURCE_FACT_COUNTS
    ):
        _fail("PREDECESSOR_1N0_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 103
        or len(set(existing_event_ids)) != 103
        or len({source.binding.review_unit_id for source in existing}) != 15
        or len({source.binding.stable_identity for source in existing}) != 15
    ):
        _fail("PREDECESSOR_1N0_SOURCE_CHAIN_NOT_EXACT15_103")

    cer_source = project_cer_completed_decision_v1(repo_root=repo_root)
    _validate_projected_cer_source_v1(cer_source)
    cer_event_ids = {fact.canonical_event_id for fact in cer_source.facts}
    overlap = cer_event_ids & set(existing_event_ids)
    if overlap:
        _fail("CER_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])
    if cer_source.binding.review_unit_id in {
        source.binding.review_unit_id for source in existing
    }:
        _fail("CER_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR")
    if cer_source.binding.stable_identity in {
        source.binding.stable_identity for source in existing
    }:
        _fail("CER_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR")

    sources = (*existing, cer_source)
    if (
        len(sources) != 16
        or sources[:-1] != existing
        or tuple(len(source.facts) for source in sources)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or len({source.binding.review_unit_id for source in sources}) != 16
        or len({source.binding.stable_identity for source in sources}) != 16
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT16")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 107:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_107")
    if len(set(event_ids)) != 107:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def _validate_reconciliation_delta_v1(
    predecessor: generic.ReconciliationResult,
    successor: generic.ReconciliationResult,
) -> None:
    """Prove the successor is exactly the four-row generic CER overlay."""

    if predecessor.review_summary != _BEFORE_SUMMARY:
        _fail("PREDECESSOR_1N0_REVIEW_SUMMARY_INVALID")
    if successor.review_summary != _AFTER_SUMMARY:
        _fail("CER_RECONCILIATION_REVIEW_SUMMARY_INVALID")
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
        _fail("CER_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED")

    target_ids = set(_EVENT_IDS)
    expected_authority = generic._canonical_json(
        [_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()]
    )
    changed_target_count = 0
    unchanged_non_target_count = 0
    for before, after in zip(before_rows, after_rows, strict=True):
        event_id = before["canonical_event_id"]
        changed_fields = {
            key for key in before if before[key] != after[key]
        }
        if event_id not in target_ids:
            if changed_fields:
                _fail("CER_NON_TARGET_ROW_CHANGED:" + event_id)
            unchanged_non_target_count += 1
            continue
        if changed_fields != _ALLOWED_RECONCILIATION_FIELDS:
            _fail("CER_TARGET_CHANGED_FIELD_SET_INVALID:" + event_id)
        if (
            before["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or after["current_review_status"]
            != generic.COMPLETED_HUMAN_POSITIVE
            or after["current_status_authority_sources_json"]
            != expected_authority
            or after["calibration_eligible"] != "false"
            or after["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            _fail("CER_FINAL_RECONCILIATION_TRANSITION_INVALID:" + event_id)
        changed_target_count += 1
    if changed_target_count != 4 or unchanged_non_target_count != 334:
        _fail("CER_RECONCILIATION_DELTA_NOT_EXACT4_OF_338")


def reconcile_real_completed_human_decisions_with_cer_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact16 sources through the generic owner, entirely in memory."""

    predecessor = (
        one_n0_predecessor.reconcile_real_completed_human_decisions_with_1n0_v1(
            repo_root
        )
    )
    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_cer_original_unreviewed_prior_v1(historical)
    original_snapshot = tuple(dict(row) for row in historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != original_snapshot:
        _fail("ONL_ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    _prove_cer_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_cer_v1(repo_root)
    successor = generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
    _validate_reconciliation_delta_v1(predecessor, successor)
    return successor
