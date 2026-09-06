"""Append the published NWJ Exact4 to completed-decision reconciliation.

The NWJ ingestion owner remains the sole owner of the rich human decision.
This metadata-only successor independently validates the returned rich bound,
constructs generic Exact11 facts, appends one source to the published with-TP2
chain, and calls the unchanged generic reconciler.  It does not refresh a
census or queue, materialize task labels or masks, admit training, or train.
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
from . import covapie_completed_human_decision_reconciliation_with_tp2_v1 as predecessor_owner
from . import covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1 as ingestion


__all__ = (
    "CompletedDecisionReconciliationWithNWJError",
    "project_nwj_completed_decision_v1",
    "load_real_completed_decision_sources_with_nwj_v1",
    "reconcile_real_completed_human_decisions_with_nwj_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_nwj_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_nwj_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_completed_human_decision_reconciliation_with_nwj_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_completed_human_decision_reconciliation_with_nwj_v1"
)
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_nwj_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, OUTPUT_RELATIVE)

_HISTORICAL_PRIORITY_RANK = "28"
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
    "completed_positive_event_count": 119,
    "completed_positive_unit_count": 19,
    "completed_negative_event_count": 44,
    "completed_negative_unit_count": 9,
    "completed_total_event_count": 163,
    "completed_total_unit_count": 28,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 175,
    "unreviewed_unit_count": 103,
}
_SUCCESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 123,
    "completed_positive_unit_count": 20,
    "completed_negative_event_count": 44,
    "completed_negative_unit_count": 9,
    "completed_total_event_count": 167,
    "completed_total_unit_count": 29,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 171,
    "unreviewed_unit_count": 102,
}
PREDECESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 139,
    "accepted_review_unit_count": 24,
    "stable_source_identity_count": 24,
    "remaining_unreviewed_chemistry_event_count": 199,
    "remaining_unreviewed_review_unit_upper_bound": 107,
    "decision_category_distribution": {
        "chemistry_positive": 95,
        "chemistry_negative": 20,
        "task_domain_negative": 24,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 143,
    "accepted_review_unit_count": 25,
    "stable_source_identity_count": 25,
    "remaining_unreviewed_chemistry_event_count": 195,
    "remaining_unreviewed_review_unit_upper_bound": 106,
    "decision_category_distribution": {
        "chemistry_positive": 99,
        "chemistry_negative": 20,
        "task_domain_negative": 24,
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
        "pair_authority_scope",
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


class CompletedDecisionReconciliationWithNWJError(ValueError):
    """Raised when the exact additive NWJ contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWithNWJError(token)


def _mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _expected_binding_v1(bound: Mapping[str, object]) -> generic.SourceBinding:
    record = _mapping(
        bound.get("formal_decision_binding"), "NWJ_FORMAL_BINDING_NOT_OBJECT"
    )
    expected_record = {
        "path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": 24265,
        "SHA256": "1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff",
        "semantic_source_identity": (
            "project_parent_relative:"
            + ingestion.FORMAL_DECISION_RELATIVE.as_posix()
            + "@1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff"
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "NWJ_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }
    if record != expected_record:
        _fail("NWJ_FORMAL_SOURCE_BINDING_INVALID")
    validator = _mapping(
        bound.get("formal_validator_binding"), "NWJ_VALIDATOR_BINDING_NOT_OBJECT"
    )
    if (
        validator.get("path") != ingestion.FORMAL_VALIDATOR_RELATIVE.as_posix()
        or validator.get("validation_method")
        != "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        or validator.get("expected_executable_class") != "NON_EXECUTABLE"
    ):
        _fail("NWJ_FORMAL_VALIDATOR_BOUNDARY_INVALID")
    return generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=24265,
        sha256="1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff",
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )


def _validate_rich_nwj_boundary_v1(bound: Mapping[str, object]) -> None:
    """Independently prove rich NWJ facts as projection preconditions only."""

    formal = _mapping(bound.get("formal_document"), "NWJ_FORMAL_NOT_OBJECT")
    state = _mapping(formal.get("formal_state"), "NWJ_FORMAL_STATE_INVALID")
    identity = _mapping(formal.get("sample_identity"), "NWJ_IDENTITY_INVALID")
    decisions = _mapping(formal.get("formal_decisions"), "NWJ_DECISIONS_INVALID")
    role = _mapping(formal.get("selected_role_context"), "NWJ_ROLE_INVALID")
    alternative = _mapping(
        formal.get("retained_nonselected_alternative"),
        "NWJ_ALTERNATIVE_INVALID",
    )
    tasks = _mapping(formal.get("canonical_Exact5"), "NWJ_EXACT5_INVALID")
    pre = _mapping(formal.get("PRE_boundary"), "NWJ_PRE_INVALID")
    post = _mapping(formal.get("POST_boundary"), "NWJ_POST_INVALID")
    training = _mapping(formal.get("training_boundary"), "NWJ_TRAINING_INVALID")
    readiness = _mapping(formal.get("readiness"), "NWJ_READINESS_INVALID")
    operations = _mapping(
        formal.get("operation_boundary"), "NWJ_OPERATION_BOUNDARY_INVALID"
    )
    if (
        formal.get("schema_version") != ingestion.FORMAL_DECISION_SCHEMA
        or state.get("approved") is not True
        or state.get("unsigned") is not False
        or state.get("authorization_origin") != "EXTERNAL_HUMAN_CHAT_REVIEW"
        or state.get("decision_finalized") is not True
        or state.get("human_review_completed") is not True
        or state.get("formal_decision_created") is not True
        or identity.get("PDB") != "4CM5"
        or identity.get("ligand_component_id") != "NWJ"
        or identity.get("review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
        or identity.get("event_count") != 4
        or identity.get("canonical_event_ids") != list(ingestion.EXPECTED_EVENT_IDS)
        or identity.get("scaleup_event_ranks") != [674, 675, 676, 677]
        or identity.get("raw_priority_rank") != 28
        or identity.get("rank_systems_are_distinct") is not True
    ):
        _fail("NWJ_FORMAL_IDENTITY_OR_COMPLETION_INVALID")

    d1 = _mapping(
        decisions.get("D1_observed_covalent_chemistry"), "NWJ_D1_INVALID"
    )
    d2 = _mapping(
        decisions.get("D2_generation_domain_relevance"), "NWJ_D2_INVALID"
    )
    d3 = _mapping(decisions.get("D3_reactive_pair"), "NWJ_D3_INVALID")
    d4 = _mapping(decisions.get("D4_role_partition"), "NWJ_D4_INVALID")
    d5 = _mapping(
        decisions.get("D5_structural_task_applicability"), "NWJ_D5_INVALID"
    )
    d6 = _mapping(decisions.get("D6_later_training_use"), "NWJ_D6_INVALID")
    if (
        d1.get("decision") != "POSITIVE"
        or d1.get("chemistry_human_authoritative") is not True
        or d2.get("decision") != "IN_DOMAIN"
        or d2.get("task_relevance_human_authoritative") is not True
        or d3.get("decision") != "CONFIRM_OBSERVED_PAIR"
        or d3.get("protein_atom") != "SG"
        or d3.get("ligand_atom") != "CAV"
        or d3.get("reactive_pair_sample_authoritative") is not True
        or d3.get("reusable_pair_authority") is not False
        or d4.get("decision") != ingestion.SELECTED_CANDIDATE
        or d4.get("role_profile") != ingestion.EXPECTED_ROLE_PROFILE
        or d4.get("role_partition_sample_authoritative") is not True
        or d4.get("candidate_B_selected") is not False
        or d4.get("candidate_B_authoritative") is not False
        or d5.get("decision") != [0, 3, 4]
        or d5.get("task_label_authority") is not False
        or d5.get("event_task_label_rows_materialized") is not False
        or d5.get("mask_tensor_targets_created") is not False
        or d6.get("decision") != generic.TRAINING_INCLUDE
        or d6.get("human_training_use_disposition") != generic.TRAINING_INCLUDE
        or d6.get("formal_training_admitted") is not False
        or d6.get("training_admission_created") is not False
        or d6.get("training_materialization_allowed") is not False
        or d6.get("READY_FOR_TRAINING") is not False
        or d6.get("TRAINING_STARTED") is not False
    ):
        _fail("NWJ_D1_D6_BOUNDARY_INVALID")

    seed = _mapping(role.get("minimal_seed"), "NWJ_MINIMAL_SEED_INVALID")
    if (
        role.get("candidate_id") != ingestion.SELECTED_CANDIDATE
        or role.get("candidate_A_selected") is not True
        or role.get("candidate_A_authoritative") is not True
        or role.get("role_profile") != ingestion.EXPECTED_ROLE_PROFILE
        or role.get("warhead_atom_ids") != list(ingestion.WARHEAD_ATOMS)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids") != list(ingestion.SCAFFOLD_ATOMS)
        or role.get("task_ids") != [0, 3, 4]
        or seed.get("atom_ids") != list(ingestion.MINIMAL_SEED)
        or seed.get("primary_scaffold_side_anchor") != ingestion.PRIMARY_ANCHOR
        or seed.get("reusable_minimal_seed_authority") is not False
        or alternative.get("candidate_id") != ingestion.NONSELECTED_CANDIDATE
        or alternative.get("candidate_B_selected") is not False
        or alternative.get("candidate_B_authoritative") is not False
        or alternative.get("not_asserted_wrong") is not True
    ):
        _fail("NWJ_ROLE_OR_CANDIDATE_BOUNDARY_INVALID")

    expected_tasks = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "generated_roles": list(generated),
            "fixed_or_seed_roles": list(fixed),
            "minimal_seed_or_anchor_retained": task_id == 4,
            "task_label_authority": False,
        }
        for task_id, semantic, alias, generated, fixed in ingestion.CANONICAL_TASKS
    ]
    if (
        tasks.get("tasks") != expected_tasks
        or tasks.get("task_count") != 5
        or tasks.get("B3_present") is not True
        or tasks.get("sixth_task") is not False
        or tasks.get("selected_structural_applicability_task_ids") != [0, 3, 4]
        or tasks.get("task_label_authority") is not False
        or tasks.get("event_task_label_rows_materialized") is not False
        or tasks.get("mask_tensor_targets_created") is not False
    ):
        _fail("NWJ_EXACT5_OR_LABEL_BOUNDARY_INVALID")
    if (
        pre.get("PRE_source_mapping_status") != ingestion.PRE_MAPPING_STATUS
        or pre.get("final_PRE_reaction_status") != ingestion.PRE_STATUS
        or pre.get("source_mapping_count_per_event") != 0
        or pre.get("PRE_authority") is not False
        or pre.get("POST_to_PRE_copy") is not False
        or pre.get("PRE_zero_fill") is not False
        or post.get("Exact4_observed_POST_geometry") is not True
        or post.get("POST_geometry_training_authority") is not False
        or post.get("POST_geometry_training_target_created") is not False
    ):
        _fail("NWJ_PRE_POST_BOUNDARY_INVALID")
    if (
        training.get("human_training_use_disposition") != generic.TRAINING_INCLUDE
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed") is not False
        or training.get("task_label_authority") is not False
        or training.get("event_task_label_rows_materialized") is not False
        or training.get("mask_tensor_targets_created") is not False
        or training.get("READY_FOR_TRAINING") is not False
        or training.get("TRAINING_STARTED") is not False
        or readiness.get("FORMAL_TRAINING_ADMITTED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_PERFORMED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING")
        is not True
        or readiness.get("READY_FOR_TRAINING") is not False
        or readiness.get("TRAINING_STARTED") is not False
        or not operations
        or any(value is not False for value in operations.values())
    ):
        _fail("NWJ_TRAINING_OR_OPERATION_BOUNDARY_INVALID")
    reusable = _mapping(
        formal.get("reusable_authority_map"), "NWJ_REUSABLE_AUTHORITY_INVALID"
    )
    if not reusable or any(value is not False for value in reusable.values()):
        _fail("NWJ_REUSABLE_AUTHORITY_FORGED")
    census = _mapping(
        bound.get("current_census_boundary"), "NWJ_CENSUS_BOUNDARY_INVALID"
    )
    if (
        census.get("census_modified_by_ingestion") is not False
        or census.get("NWJ_event_count") != 4
        or census.get("raw_priority_rank") != 28
        or census.get("NWJ_current_global_status") != generic.CURRENTLY_UNREVIEWED
    ):
        _fail("NWJ_CURRENT_CENSUS_WAS_NOT_PRESERVED")
    _expected_binding_v1(bound)


def _projection_records_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    _validate_rich_nwj_boundary_v1(bound)
    binding = _expected_binding_v1(bound)
    records = tuple(
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE,
            "task_relevance_disposition": generic.TASK_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_INCLUDE,
            "human_training_excluded": False,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding.sha256,
            "source_binding_path": binding.source_path,
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    )
    if any(tuple(record) != _GENERIC_FACT_FIELDS for record in records):
        _fail("NWJ_GENERIC_PROJECTION_NOT_EXACT11")
    return records


def _validate_projected_nwj_source_v1(
    source: generic.NormalizedDecisionSource,
    records: Sequence[Mapping[str, object]],
) -> None:
    if tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) != (
        _GENERIC_FACT_FIELDS
    ):
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    if len(source.facts) != 4 or len(records) != 4:
        _fail("NWJ_SOURCE_PROJECTION_NOT_EXACT4")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithNWJError(
            "NWJ_GENERIC_SOURCE_BINDING_REJECTED:" + str(error)
        ) from error
    for fact, record in zip(source.facts, records, strict=True):
        actual = asdict(fact)
        if (
            tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or actual != dict(record)
            or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
        ):
            _fail("NWJ_GENERIC_PROJECTION_CLASSIFICATION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithNWJError(
                "NWJ_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_bound_nwj_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    records = _projection_records_v1(bound)
    try:
        facts = tuple(
            generic.NormalizedCompletedDecisionFact(**dict(record))
            for record in records
        )
    except TypeError as error:
        raise CompletedDecisionReconciliationWithNWJError(
            "NWJ_GENERIC_FACT_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(bound), facts=facts
    )
    _validate_projected_nwj_source_v1(source, records)
    return source


def project_nwj_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load NWJ through its published API and construct generic Exact11 facts."""

    try:
        bound = ingestion.load_frozen_formal_decision_v1(Path(repo_root).resolve())
    except ingestion.NWJIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithNWJError(
            "NWJ_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_bound_nwj_v1(bound)


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    records: Sequence[Mapping[str, object]],
) -> None:
    before, after = tuple(predecessor), tuple(successor)
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    if len(before) != 24 or len(before_facts) != 139:
        _fail("PREDECESSOR_WITH_TP2_SOURCE_CHAIN_NOT_EXACT24_139")
    if len(after) != 25 or after[:-1] != before or len(after_facts) != 143:
        _fail("NWJ_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT25_143")
    _validate_projected_nwj_source_v1(after[-1], records)
    if after_facts[:139] != before_facts or after_facts[139:] != after[-1].facts:
        _fail("NWJ_FACT_CHAIN_NOT_PREFIX_APPEND_EXACT139_PLUS4")
    before_events = [fact.canonical_event_id for fact in before_facts]
    after_events = [fact.canonical_event_id for fact in after_facts]
    if (
        any(event in set(before_events) for event in ingestion.EXPECTED_EVENT_IDS)
        or after_events[-4:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(before_events)) != 139
        or len(set(after_events)) != 143
    ):
        _fail("NWJ_EVENT_PREFIX_OR_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    before_ids = {source.binding.stable_identity for source in before}
    if (
        len(before_units) != 24
        or len(before_ids) != 24
        or len({source.binding.review_unit_id for source in after}) != 25
        or len({source.binding.stable_identity for source in after}) != 25
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(
            source.binding.path_namespace != "repository_parent_relative"
            for source in after
        )
    ):
        _fail("NWJ_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_nwj_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_tp2_v1(root)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    records = _projection_records_v1(bound)
    after = (*before, _project_bound_nwj_v1(bound))
    _validate_source_chain_v1(before, after, records)
    return after


def _prove_nwj_predecessor_historical_state_v1(
    rows: Sequence[Mapping[str, str]],
) -> None:
    targets = [
        row
        for row in rows
        if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS
    ]
    if (
        len(rows) != 338
        or len(targets) != 4
        or tuple(row["canonical_event_id"] for row in targets)
        != ingestion.EXPECTED_EVENT_IDS
        or any(
            row.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or row.get("raw_priority_rank") != _HISTORICAL_PRIORITY_RANK
            or row.get("raw_unit_event_count") != "4"
            or row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or row.get("calibration_eligible") != "true"
            or row.get("calibration_exclusion_reason") != ""
            for row in targets
        )
    ):
        _fail("NWJ_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_TP2_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("NWJ_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 139 or len(after.normalized_facts) != 143:
        _fail("NWJ_RECONCILIATION_FACT_COUNT_INVALID")
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
            or new["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
            or new["current_status_authority_sources_json"]
            != generic._canonical_json(
                [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
            )
            or old["calibration_eligible"] != "true"
            or new["calibration_eligible"] != "false"
            or old["calibration_exclusion_reason"] != ""
            or new["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            _fail("NWJ_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("NWJ_RECONCILIATION_DELTA_NOT_EXACT4_AND_334")


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
        predecessor_owner.load_real_completed_decision_sources_with_tp2_v1(root)
    )
    before_result = (
        predecessor_owner.reconcile_real_completed_human_decisions_with_tp2_v1(root)
    )
    _prove_nwj_predecessor_historical_state_v1(before_result.reconciled_rows)
    adapted = predecessor_owner._adapt_historical_v1(root)
    _prove_nwj_predecessor_historical_state_v1(adapted)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    records = _projection_records_v1(bound)
    after_sources = (*before_sources, _project_bound_nwj_v1(bound))
    _validate_source_chain_v1(before_sources, after_sources, records)
    after_result = generic.reconcile_completed_human_decisions_v1(
        adapted, after_sources
    )
    _validate_reconciliation_delta_v1(before_result, after_result)
    return before_sources, after_sources, before_result, after_result


def reconcile_real_completed_human_decisions_with_nwj_v1(
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
    artifact = _mapping(value, "NWJ_ARTIFACT_NOT_OBJECT")
    bindings = _list(artifact.get("source_bindings"), "NWJ_BINDINGS_NOT_LIST")
    facts = _list(artifact.get("normalized_facts"), "NWJ_FACTS_NOT_LIST")
    rows = _list(artifact.get("reconciled_rows"), "NWJ_ROWS_NOT_LIST")
    predecessor_facts = [
        asdict(fact) for source in predecessor_sources for fact in source.facts
    ]
    if (
        tuple(artifact) != _ARTIFACT_FIELDS
        or len(bindings) != 25
        or len(facts) != 143
        or len(rows) != 338
        or bindings != [asdict(source.binding) for source in successor_sources]
        or any(
            type(item) is not dict or set(item) != set(_SOURCE_BINDING_FIELDS)
            for item in bindings
        )
        or facts
        != [asdict(fact) for source in successor_sources for fact in source.facts]
        or facts[:139] != predecessor_facts
        or facts[139:] != [asdict(fact) for fact in successor_sources[-1].facts]
        or any(
            type(item) is not dict
            or set(item) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(item)
            for item in facts
        )
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("NWJ_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


def build_artifact_v1(repo_root: Path) -> bytes:
    """Build the sole deterministic reconciliation JSON without writing it."""

    before_sources, after_sources, _before_result, after_result = (
        _build_components_v1(repo_root)
    )
    mapping = _artifact_mapping_v1(after_sources, after_result)
    _validate_artifact_mapping_v1(
        mapping,
        predecessor_sources=before_sources,
        successor_sources=after_sources,
        reconciliation=after_result,
    )
    return (
        json.dumps(mapping, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def _validate_destination_v1(repo_root: Path, destination: Path) -> None:
    if destination.resolve() != (repo_root / OUTPUT_RELATIVE).resolve():
        _fail("NWJ_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("NWJ_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {item.name for item in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("NWJ_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    """Atomically write only the authorized reconciliation JSON."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".covapie_nwj_reconciliation_", dir=destination.parent
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
    """Rebuild and compare the one materialized artifact byte for byte."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    try:
        metadata, observed = destination.lstat(), destination.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWithNWJError(
            "NWJ_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_mode & 0o111
    ):
        _fail("NWJ_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    expected = build_artifact_v1(root)
    if observed != expected:
        _fail("NWJ_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 25,
        "accepted_fact_count": 143,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }
