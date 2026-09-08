"""Append the published ME7 Exact3 to completed-decision reconciliation.

The ME7 ingestion owner remains the owner of the rich approved human decision.
This metadata-only successor validates the published no-write projection,
converts its formal binding to the generic repository-parent namespace, appends
one source to the published with-PYR chain, and invokes the unchanged generic
reconciler over the same historical adapter.  It does not refresh census or
queue state, create task labels or tensors, admit training, update parameters,
or train.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, NoReturn

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_pyr_v1 as predecessor_owner
from . import covapie_completed_human_decision_reconciliation_with_tp2_v1 as historical_adapter_owner
from . import covapie_me7_completed_decision_ingestion_and_task_label_availability_v1 as ingestion


__all__ = (
    "CompletedDecisionReconciliationWithME7Error",
    "project_me7_completed_decision_v1",
    "load_real_completed_decision_sources_with_me7_v1",
    "reconcile_real_completed_human_decisions_with_me7_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_me7_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_me7_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_completed_human_decision_reconciliation_with_me7_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_completed_human_decision_reconciliation_with_me7_v1"
)
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_me7_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, OUTPUT_RELATIVE)

ERROR_PREFIX = "COVAPIE_ME7_RECONCILIATION_V1_ERROR"
_HISTORICAL_PRIORITY_RANK = "32"
_FORMAL_BYTES = 13344
_FORMAL_SHA256 = "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407"
_FORMAL_VALIDATOR_BYTES = 52865
_FORMAL_VALIDATOR_SHA256 = (
    "67a68f9b1c14cb90591a6e377c4fc680cc816c53e138995adf0c1544eaf91009"
)
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
_SOURCE_BINDING_FIELDS = (
    "source_path",
    "path_namespace",
    "byte_count",
    "sha256",
    "schema_version",
    "review_unit_id",
)
_ARTIFACT_FIELDS = (
    "reconciled_rows",
    "source_bindings",
    "normalized_facts",
    "review_summary",
)
_PREDECESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 127,
    "completed_positive_unit_count": 21,
    "completed_negative_event_count": 48,
    "completed_negative_unit_count": 10,
    "completed_total_event_count": 175,
    "completed_total_unit_count": 31,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 163,
    "unreviewed_unit_count": 100,
}
_SUCCESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 127,
    "completed_positive_unit_count": 21,
    "completed_negative_event_count": 51,
    "completed_negative_unit_count": 11,
    "completed_total_event_count": 178,
    "completed_total_unit_count": 32,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 160,
    "unreviewed_unit_count": 99,
}
PREDECESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 151,
    "accepted_review_unit_count": 27,
    "stable_source_identity_count": 27,
    "remaining_unreviewed_chemistry_event_count": 187,
    "remaining_unreviewed_review_unit_upper_bound": 104,
    "decision_category_distribution": {
        "chemistry_positive": 103,
        "chemistry_negative": 20,
        "task_domain_negative": 28,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 154,
    "accepted_review_unit_count": 28,
    "stable_source_identity_count": 28,
    "remaining_unreviewed_chemistry_event_count": 184,
    "remaining_unreviewed_review_unit_upper_bound": 103,
    "decision_category_distribution": {
        "chemistry_positive": 103,
        "chemistry_negative": 20,
        "task_domain_negative": 31,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
_FORBIDDEN_RICH_FACT_FIELDS = frozenset(
    {
        "completed_lane",
        "protein_reactive_atom",
        "ligand_reactive_atom",
        "reactive_pair",
        "observed_pair",
        "role_partition",
        "role_profile",
        "selected_candidate",
        "warhead_atoms",
        "linker_atoms",
        "scaffold_atoms",
        "W",
        "L",
        "S",
        "seed",
        "minimal_seed",
        "primary_anchor",
        "task_ids",
        "applicable_task_ids",
        "PRE",
        "POST",
        "geometry",
        "geometry_outlier",
        "training_target",
        "training_tensor",
        "training_mask_targets",
    }
)
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    {
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    }
)


class CompletedDecisionReconciliationWithME7Error(ValueError):
    """Raised when the exact additive ME7 contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWithME7Error(f"{ERROR_PREFIX}:{token}")


def _mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _expect_fields(
    value: object, expected: Mapping[str, object], token: str
) -> Mapping[str, Any]:
    observed = _mapping(value, token + ":NOT_OBJECT")
    if any(
        type(observed.get(key)) is not type(expected_value)
        or observed.get(key) != expected_value
        for key, expected_value in expected.items()
    ):
        _fail(token)
    return observed


def _expected_binding_v1(bound: Mapping[str, object]) -> generic.SourceBinding:
    path = ingestion.FORMAL_DECISION_RELATIVE.as_posix()
    record = _mapping(
        bound.get("formal_decision_binding"), "ME7_FORMAL_BINDING_NOT_OBJECT"
    )
    if record != {
        "path": path,
        "path_namespace": "project_parent_relative",
        "byte_count": _FORMAL_BYTES,
        "SHA256": _FORMAL_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:" + path + "@" + _FORMAL_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "ME7_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }:
        _fail("ME7_FORMAL_SOURCE_BINDING_INVALID")
    validator_path = ingestion.FORMAL_VALIDATOR_RELATIVE.as_posix()
    validator = _mapping(
        bound.get("formal_validator_binding"), "ME7_VALIDATOR_BINDING_NOT_OBJECT"
    )
    if validator != {
        "path": validator_path,
        "path_namespace": "project_parent_relative",
        "byte_count": _FORMAL_VALIDATOR_BYTES,
        "SHA256": _FORMAL_VALIDATOR_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:"
            + validator_path
            + "@"
            + _FORMAL_VALIDATOR_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "ME7_FROZEN_FORMAL_VALIDATOR",
        "validation_method": (
            "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        ),
    }:
        _fail("ME7_FORMAL_VALIDATOR_PROVENANCE_BOUNDARY_INVALID")
    binding = generic.SourceBinding(
        source_path=path,
        path_namespace="repository_parent_relative",
        byte_count=_FORMAL_BYTES,
        sha256=_FORMAL_SHA256,
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )
    try:
        generic._validate_source_binding(binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithME7Error(
            f"{ERROR_PREFIX}:ME7_GENERIC_SOURCE_BINDING_REJECTED:{error}"
        ) from error
    return binding


def _validate_rich_me7_boundary_v1(bound: Mapping[str, object]) -> None:
    """Validate only the approved fields needed for the Exact11 projection."""

    formal = _mapping(bound.get("formal_document"), "ME7_FORMAL_NOT_OBJECT")
    _expect_fields(
        formal,
        {
            "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
            "record_role": ingestion.FORMAL_RECORD_ROLE,
        },
        "ME7_FORMAL_ROOT_INVALID",
    )
    _expect_fields(
        formal.get("sample_identity"),
        {
            "ligand_component_id": "ME7",
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "scope": ingestion.EXPECTED_SCOPE,
            "target_event_count": 3,
            "canonical_target_event_ids": list(ingestion.EXPECTED_EVENT_IDS),
            "target_scaleup_ranks": list(ingestion.EXPECTED_RANKS),
            "pdb_ids": ["3QVY", "3QVZ"],
            "ligand_wide_authority": False,
            "cross_structure_authority": False,
        },
        "ME7_FORMAL_IDENTITY_INVALID",
    )
    _expect_fields(
        formal.get("sample_level_authority"),
        {
            "approved": True,
            "human_review_completed": True,
            "human_decision_created": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "sample_chemistry_authority": True,
            "sample_task_domain_authority": True,
            "sample_pair_authority": True,
            "sample_D6_disposition_authority": True,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "unsigned": False,
        },
        "ME7_APPROVAL_STATE_INVALID",
    )
    decisions = _mapping(formal.get("approved_D1_D6"), "ME7_D1_D6_NOT_OBJECT")
    d1 = _mapping(
        decisions.get("D1_observation_record_judgment"), "ME7_D1_INVALID"
    )
    d2 = _mapping(decisions.get("D2_project_domain_relevance"), "ME7_D2_INVALID")
    d3 = _mapping(
        decisions.get("D3_recorded_endpoint_confirmation"), "ME7_D3_INVALID"
    )
    d4 = _mapping(
        decisions.get("D4_role_partition_and_retained_information"),
        "ME7_D4_INVALID",
    )
    d5 = _mapping(
        decisions.get("D5_structural_task_applicability"), "ME7_D5_INVALID"
    )
    d6 = _mapping(
        decisions.get("D6_later_use_disposition"), "ME7_D6_INVALID"
    )
    if (
        d1
        != {
            "chemistry_positive": True,
            "decision": "POSITIVE",
            "human_answered": True,
            "human_approved": True,
        }
        or d2
        != {
            "chemistry_negative": False,
            "chemistry_positive_is_preserved": True,
            "decision": "OUT_OF_DOMAIN",
            "human_answered": True,
            "human_approved": True,
            "scope": "CURRENT_UNIT_AND_CURRENT_PROJECT_TASK_DEFINITION_ONLY",
        }
        or d3
        != {
            "component_atom": "CAE",
            "decision": "CONFIRM_OBSERVED_PAIR",
            "human_answered": True,
            "human_approved": True,
            "pair": "SG:CAE",
            "protein_atom": "SG",
            "target_pair_is_only_attachment_for_component_instance": False,
        }
        or d4
        != {
            "decision": "CANNOT_DETERMINE",
            "formal_question_field": "D4_role_partition_and_retained_information",
            "human_answered": True,
            "human_approved": True,
            "role_candidate_count": 0,
            "selected_candidate_id": None,
            "source_proposal_field": "D4_role_partition_and_minimal_seed",
        }
        or d5
        != {
            "decision": "NOT_DETERMINABLE",
            "human_answered": True,
            "human_approved": True,
            "task_ids": None,
        }
        or d6
        != {
            "chemistry_negative": False,
            "decision": "NOT_APPLICABLE",
            "formal_training_admitted": False,
            "future_training_admission_candidate": False,
            "human_answered": True,
            "human_approved": True,
            "human_training_excluded": False,
        }
    ):
        _fail("ME7_D1_D6_BOUNDARY_INVALID")

    roles = _expect_fields(
        formal.get("role_and_task_disposition"),
        {
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "role_candidate_count": 0,
            "selected_candidate_id": None,
            "selected_role_candidate": None,
            "role_profile": None,
            "warhead_atom_ids": None,
            "linker_atom_ids": None,
            "scaffold_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "applicable_task_ids": None,
            "role_runtime_executed": False,
            "task_runtime_executed": False,
            "canonical_v1_task_count": 5,
            "B3_present": True,
            "sixth_task_created": False,
        },
        "ME7_NULL_ROLE_TASK_BOUNDARY_INVALID",
    )
    tasks = _list(roles.get("canonical_v1_tasks"), "ME7_EXACT5_TASKS_INVALID")
    if (
        len(tasks) != 5
        or [row.get("semantic_long_name") for row in tasks if type(row) is dict]
        != [row[1] for row in ingestion.CANONICAL_TASKS]
        or not any(
            type(row) is dict
            and row.get("semantic_long_name") == "scaffold_only"
            and row.get("display_alias") == "B3"
            for row in tasks
        )
    ):
        _fail("ME7_EXACT5_LONG_NAMES_OR_B3_INVALID")

    non_created = _mapping(
        formal.get("non_created_authority"), "ME7_NON_CREATED_AUTHORITY_INVALID"
    )
    if any(
        non_created.get(key) is not False
        for key in (
            "TASK_LABEL_AUTHORITY",
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED",
            "MASK_TENSOR_TARGETS_CREATED",
            "FORMAL_TRAINING_ADMITTED",
            "TRAINING_MATERIALIZATION_ALLOWED",
            "PARAMETER_UPDATE_AUTHORIZATION",
            "READY_FOR_TRAINING",
            "TRAINING_STARTED",
            "PRE_authority",
            "POST_geometry_training_authority",
            "reusable_authority_created",
        )
    ):
        _fail("ME7_NON_CREATED_AUTHORITY_INVALID")
    _expect_fields(
        formal.get("readiness"),
        {
            "AUTHORIZATION_COMPLETE": True,
            "HUMAN_REVIEW_COMPLETED": True,
            "FORMAL_TRAINING_ADMITTED": False,
            "TASK_LABEL_AUTHORITY": False,
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
            "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
        },
        "ME7_READINESS_BOUNDARY_INVALID",
    )
    operations = _mapping(
        formal.get("operation_boundary"), "ME7_OPERATION_BOUNDARY_INVALID"
    )
    if any(
        operations.get(key) is not False
        for key in (
            "census_refresh_performed",
            "queue_refresh_performed",
            "reconciliation_performed",
            "task_label_materialization_performed",
            "mask_tensor_materialization_performed",
            "training_preparation_performed",
            "parameter_update_performed",
            "training_performed",
            "repository_modified",
            "commit_performed",
            "push_performed",
        )
    ):
        _fail("ME7_OPERATION_BOUNDARY_INVALID")

    compatibility = _expect_fields(
        bound.get("generic_Exact11_compatibility"),
        {
            "generic_exact11_compatibility_pass": True,
            "generic_fact_field_count": 11,
            "accepted_fact_count": 3,
            "completed_lane": ingestion.EXPECTED_COMPLETED_LANE,
            "source_formal_D2": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "source_formal_D6": "NOT_APPLICABLE",
            "normalized_training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "rich_fields_leaked": False,
            "NormalizedDecisionSource_constructed": True,
            "reconciliation_performed": False,
        },
        "ME7_GENERIC_COMPATIBILITY_BOUNDARY_INVALID",
    )
    facts = _list(compatibility.get("facts"), "ME7_GENERIC_FACTS_INVALID")
    if len(facts) != 3 or any(
        type(fact) is not dict or tuple(fact) != _GENERIC_FACT_FIELDS
        for fact in facts
    ):
        _fail("ME7_GENERIC_COMPATIBILITY_NOT_EXACT3_EXACT11")
    census = _expect_fields(
        bound.get("current_census_and_queue_boundary"),
        {
            "ME7_event_count": 3,
            "ME7_current_global_status": generic.CURRENTLY_UNREVIEWED,
            "ME7_current_review_status": generic.CURRENTLY_UNREVIEWED,
            "ME7_human_review_completed": False,
            "ME7_structurally_applicable_task_ids": None,
            "ME7_priority_rank": 32,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
            "historical_pending_state_is_expected_until_refresh": True,
        },
        "ME7_CURRENT_CENSUS_QUEUE_BOUNDARY_INVALID",
    )
    if not census:
        _fail("ME7_CURRENT_CENSUS_QUEUE_BOUNDARY_INVALID")

    events = _list(bound.get("events"), "ME7_EVENTS_NOT_LIST")
    actual_event_triplets = [
        (row.get("canonical_event_id"), row.get("scaleup_rank"), row.get("pdb_id"))
        for row in events
        if type(row) is dict
    ]
    expected_event_triplets = list(
        zip(ingestion.EXPECTED_EVENT_IDS, ingestion.EXPECTED_RANKS, ("3QVY", "3QVY", "3QVZ"), strict=True)
    )
    if len(events) != 3 or actual_event_triplets != expected_event_triplets:
        _fail("ME7_TARGET_EVENT_IDENTITY_INVALID")
    context = _list(
        bound.get("context_only_graph_records"), "ME7_CONTEXT_ONLY_NOT_LIST"
    )
    context_ids = {
        row.get("canonical_event_id") for row in context if type(row) is dict
    }
    if (
        len(context) != 3
        or {row.get("scaleup_rank") for row in context if type(row) is dict}
        != {527, 530, 533}
        or any(
            type(row) is not dict
            or row.get("supporting_context_only") is not True
            or row.get("target_event") is not False
            for row in context
        )
        or context_ids & set(ingestion.EXPECTED_EVENT_IDS)
    ):
        _fail("ME7_CONTEXT_ONLY_BOUNDARY_INVALID")
    _expected_binding_v1(bound)


def _projection_records_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    _validate_rich_me7_boundary_v1(bound)
    binding = _expected_binding_v1(bound)
    records = tuple(
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": False,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding.sha256,
            "source_binding_path": binding.source_path,
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    )
    compatibility = _mapping(
        bound.get("generic_Exact11_compatibility"), "ME7_GENERIC_FACTS_INVALID"
    )
    if (
        any(tuple(record) != _GENERIC_FACT_FIELDS for record in records)
        or compatibility.get("facts") != [dict(record) for record in records]
    ):
        _fail("ME7_GENERIC_PROJECTION_NOT_VALIDATED_EXACT3_EXACT11")
    return records


def _validate_projected_me7_source_v1(
    source: generic.NormalizedDecisionSource,
    records: Sequence[Mapping[str, object]],
) -> None:
    if (
        tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)
        != _GENERIC_FACT_FIELDS
    ):
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    if len(source.facts) != 3 or len(records) != 3:
        _fail("ME7_SOURCE_PROJECTION_NOT_EXACT3")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithME7Error(
            f"{ERROR_PREFIX}:ME7_GENERIC_SOURCE_BINDING_REJECTED:{error}"
        ) from error
    for fact, record in zip(source.facts, records, strict=True):
        actual = asdict(fact)
        if (
            tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or actual != dict(record)
            or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
        ):
            _fail("ME7_GENERIC_PROJECTION_CLASSIFICATION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithME7Error(
                f"{ERROR_PREFIX}:ME7_GENERIC_FACT_REJECTED:{error}"
            ) from error


def _project_bound_me7_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    records = _projection_records_v1(bound)
    try:
        facts = tuple(
            generic.NormalizedCompletedDecisionFact(**dict(record))
            for record in records
        )
    except TypeError as error:
        raise CompletedDecisionReconciliationWithME7Error(
            f"{ERROR_PREFIX}:ME7_GENERIC_FACT_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(bound), facts=facts
    )
    _validate_projected_me7_source_v1(source, records)
    return source


def _load_bound_v1(repo_root: Path) -> Mapping[str, object]:
    root = Path(repo_root).resolve()
    try:
        return ingestion.load_frozen_formal_decision_v1(root)
    except ingestion.ME7IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithME7Error(
            f"{ERROR_PREFIX}:ME7_INGESTION_OWNER_VALIDATION_FAILED:{error}"
        ) from error


def project_me7_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load ME7 through published no-write APIs and emit three Exact11 facts."""

    return _project_bound_me7_v1(_load_bound_v1(repo_root))


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    records: Sequence[Mapping[str, object]],
) -> None:
    before, after = tuple(predecessor), tuple(successor)
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    if len(before) != 27 or len(before_facts) != 151:
        _fail("PREDECESSOR_WITH_PYR_SOURCE_CHAIN_NOT_EXACT27_151")
    if len(after) != 28 or after[:-1] != before or len(after_facts) != 154:
        _fail("ME7_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT28_154")
    _validate_projected_me7_source_v1(after[-1], records)
    if after_facts[:151] != before_facts or after_facts[151:] != after[-1].facts:
        _fail("ME7_FACT_CHAIN_NOT_PREFIX_APPEND_EXACT151_PLUS3")
    before_events = [fact.canonical_event_id for fact in before_facts]
    after_events = [fact.canonical_event_id for fact in after_facts]
    target_events = set(ingestion.EXPECTED_EVENT_IDS)
    if (
        target_events & set(before_events)
        or after_events[-3:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(before_events)) != 151
        or len(set(after_events)) != 154
    ):
        _fail("ME7_EVENT_PREFIX_OR_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    before_ids = {source.binding.stable_identity for source in before}
    if (
        len(before_units) != 27
        or len(before_ids) != 27
        or len({source.binding.review_unit_id for source in after}) != 28
        or len({source.binding.stable_identity for source in after}) != 28
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(
            source.binding.path_namespace != "repository_parent_relative"
            for source in after
        )
        or sum(
            source.binding.review_unit_id == ingestion.EXPECTED_REVIEW_UNIT_ID
            for source in after
        )
        != 1
    ):
        _fail("ME7_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_me7_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_pyr_v1(root)
    bound = _load_bound_v1(root)
    records = _projection_records_v1(bound)
    after = (*before, _project_bound_me7_v1(bound))
    _validate_source_chain_v1(before, after, records)
    return after


def _prove_me7_predecessor_historical_state_v1(
    rows: Sequence[Mapping[str, str]],
) -> None:
    targets = [
        row
        for row in rows
        if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS
    ]
    if (
        len(rows) != 338
        or len(targets) != 3
        or tuple(row["canonical_event_id"] for row in targets)
        != ingestion.EXPECTED_EVENT_IDS
        or any(
            row.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or row.get("raw_priority_rank") != _HISTORICAL_PRIORITY_RANK
            or row.get("raw_unit_event_count") != "3"
            or row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or row.get("calibration_eligible") != "true"
            or row.get("calibration_exclusion_reason") != ""
            for row in targets
        )
    ):
        _fail("ME7_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_PYR_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("ME7_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 151 or len(after.normalized_facts) != 154:
        _fail("ME7_RECONCILIATION_FACT_COUNT_INVALID")
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(before.reconciled_rows, after.reconciled_rows, strict=True):
        if old.get("canonical_event_id") not in targets:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old[key] != new[key]}
        if (
            changed != _ALLOWED_RECONCILIATION_FIELDS
            or old["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or new["current_review_status"] != generic.COMPLETED_HUMAN_NEGATIVE
            or new["current_status_authority_sources_json"]
            != generic._canonical_json(
                [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
            )
            or old["calibration_eligible"] != "true"
            or new["calibration_eligible"] != "false"
            or old["calibration_exclusion_reason"] != ""
            or new["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("ME7_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (3, 0):
        _fail("ME7_RECONCILIATION_DELTA_NOT_EXACT3_AND_335")


def _validate_coverage_contract_v1(
    before_sources: Sequence[generic.NormalizedDecisionSource],
    after_sources: Sequence[generic.NormalizedDecisionSource],
) -> None:
    if PREDECESSOR_COVERAGE_SUMMARY != predecessor_owner.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("PREDECESSOR_WITH_PYR_COVERAGE_DRIFT")
    before_facts = [fact for source in before_sources for fact in source.facts]
    after_facts = [fact for source in after_sources for fact in source.facts]
    before_distribution = PREDECESSOR_COVERAGE_SUMMARY[
        "decision_category_distribution"
    ]
    after_distribution = SUCCESSOR_COVERAGE_SUMMARY[
        "decision_category_distribution"
    ]
    if (
        len(before_facts) != 151
        or len(after_facts) != 154
        or after_facts[:151] != before_facts
        or after_facts[151:] != list(after_sources[-1].facts)
        or SUCCESSOR_COVERAGE_SUMMARY["accepted_review_unit_count"]
        != len(after_sources)
        or SUCCESSOR_COVERAGE_SUMMARY["stable_source_identity_count"]
        != len({source.binding.stable_identity for source in after_sources})
        or SUCCESSOR_COVERAGE_SUMMARY["remaining_unreviewed_chemistry_event_count"]
        != 338 - len(after_facts)
        or SUCCESSOR_COVERAGE_SUMMARY[
            "remaining_unreviewed_review_unit_upper_bound"
        ]
        != 131 - len(after_sources)
        or sum(before_distribution.values()) != len(before_facts)
        or sum(after_distribution.values()) != len(after_facts)
        or after_distribution["task_domain_negative"]
        - before_distribution["task_domain_negative"]
        != 3
        or any(
            after_distribution[key] != before_distribution[key]
            for key in (
                "chemistry_positive",
                "chemistry_negative",
                "task_domain_positive",
            )
        )
        or any(
            fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
            for fact in after_facts[151:]
        )
        or SUCCESSOR_COVERAGE_SUMMARY["label_ready_event_count"] != 16
        or SUCCESSOR_COVERAGE_SUMMARY["training_mask_target_count"] != 0
        or SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is not False
    ):
        _fail("ME7_COVERAGE_DELTA_INVALID")


def _build_components_v1(
    repo_root: Path,
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
    generic.ReconciliationResult,
    generic.ReconciliationResult,
]:
    root = Path(repo_root).resolve()
    before_sources = (
        predecessor_owner.load_real_completed_decision_sources_with_pyr_v1(root)
    )
    adapted = historical_adapter_owner._adapt_historical_v1(root)
    _prove_me7_predecessor_historical_state_v1(adapted)
    reproduced_before = generic.reconcile_completed_human_decisions_v1(
        adapted, before_sources
    )
    published_before = (
        predecessor_owner.reconcile_real_completed_human_decisions_with_pyr_v1(root)
    )
    if reproduced_before != published_before:
        _fail("PREDECESSOR_WITH_PYR_RESULT_NOT_REPRODUCED_FROM_ADAPTED_BASE")
    _prove_me7_predecessor_historical_state_v1(reproduced_before.reconciled_rows)
    bound = _load_bound_v1(root)
    records = _projection_records_v1(bound)
    after_sources = (*before_sources, _project_bound_me7_v1(bound))
    _validate_source_chain_v1(before_sources, after_sources, records)
    _validate_coverage_contract_v1(before_sources, after_sources)
    after_result = generic.reconcile_completed_human_decisions_v1(
        adapted, after_sources
    )
    _validate_reconciliation_delta_v1(reproduced_before, after_result)
    return before_sources, after_sources, reproduced_before, after_result


def reconcile_real_completed_human_decisions_with_me7_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    return _build_components_v1(repo_root)[-1]


def _artifact_mapping_v1(
    sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> dict[str, object]:
    return {
        "reconciled_rows": [dict(row) for row in reconciliation.reconciled_rows],
        "source_bindings": [asdict(source.binding) for source in sources],
        "normalized_facts": [
            asdict(fact) for source in sources for fact in source.facts
        ],
        "review_summary": dict(reconciliation.review_summary),
    }


def _validate_artifact_mapping_v1(
    value: object,
    *,
    predecessor_sources: Sequence[generic.NormalizedDecisionSource],
    successor_sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> None:
    artifact = _mapping(value, "ME7_ARTIFACT_NOT_OBJECT")
    bindings = _list(artifact.get("source_bindings"), "ME7_BINDINGS_NOT_LIST")
    facts = _list(artifact.get("normalized_facts"), "ME7_FACTS_NOT_LIST")
    rows = _list(artifact.get("reconciled_rows"), "ME7_ROWS_NOT_LIST")
    predecessor_facts = [
        asdict(fact) for source in predecessor_sources for fact in source.facts
    ]
    if (
        tuple(artifact) != _ARTIFACT_FIELDS
        or len(bindings) != 28
        or len(facts) != 154
        or len(rows) != 338
        or bindings != [asdict(source.binding) for source in successor_sources]
        or any(
            type(item) is not dict or tuple(item) != _SOURCE_BINDING_FIELDS
            for item in bindings
        )
        or facts
        != [asdict(fact) for source in successor_sources for fact in source.facts]
        or facts[:151] != predecessor_facts
        or facts[151:]
        != [asdict(fact) for fact in successor_sources[-1].facts]
        or any(
            type(item) is not dict
            or tuple(item) != _GENERIC_FACT_FIELDS
            or _FORBIDDEN_RICH_FACT_FIELDS & set(item)
            for item in facts
        )
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("ME7_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


def build_artifact_v1(repo_root: Path) -> bytes:
    """Build the sole deterministic reconciliation JSON without writing it."""

    before_sources, after_sources, _before, after = _build_components_v1(repo_root)
    mapping = _artifact_mapping_v1(after_sources, after)
    _validate_artifact_mapping_v1(
        mapping,
        predecessor_sources=before_sources,
        successor_sources=after_sources,
        reconciliation=after,
    )
    return (
        json.dumps(mapping, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def _validate_destination_v1(repo_root: Path, destination: Path) -> None:
    if destination.resolve() != (repo_root / OUTPUT_RELATIVE).resolve():
        _fail("ME7_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("ME7_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {item.name for item in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("ME7_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    """Atomically write only the authorized reconciliation JSON."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".covapie_me7_reconciliation_", dir=destination.parent
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, destination)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
    return payload


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Rebuild twice and compare the materialized artifact byte for byte."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    try:
        metadata, observed = destination.lstat(), destination.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWithME7Error(
            f"{ERROR_PREFIX}:ME7_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_mode & 0o111
    ):
        _fail("ME7_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    first = build_artifact_v1(root)
    second = build_artifact_v1(root)
    if observed != first or first != second:
        _fail("ME7_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 28,
        "accepted_fact_count": 154,
        "changed_target_rows": 3,
        "non_target_changed_rows": 0,
        "unchanged_rows": 335,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }
