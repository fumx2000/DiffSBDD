"""Append published TP2 Exact4 facts to the published with-4LH chain.

The TP2 ingestion owner remains the sole owner of the rich human decision.
This metadata-only successor consumes its validated generic Exact11 projection,
appends one source, and calls the unchanged generic reconciler.
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
from . import covapie_completed_human_decision_reconciliation_with_4lh_v1 as predecessor_owner
from . import covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1 as ingestion

__all__ = (
    "CompletedDecisionReconciliationWithTP2Error",
    "project_tp2_completed_decision_v1",
    "load_real_completed_decision_sources_with_tp2_v1",
    "reconcile_real_completed_human_decisions_with_tp2_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)

SOURCE_RELATIVE = Path("src/covalent_ext/covapie_completed_human_decision_reconciliation_with_tp2_v1.py")
CHECKER_RELATIVE = Path("scripts/check_covapie_completed_human_decision_reconciliation_with_tp2_v1.py")
TEST_RELATIVE = Path("tests/test_covapie_completed_human_decision_reconciliation_with_tp2_v1.py")
OUTPUT_ROOT_RELATIVE = Path("data/derived/covalent_small/covapie_completed_human_decision_reconciliation_with_tp2_v1")
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_tp2_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, OUTPUT_RELATIVE)

_HISTORICAL_PRIORITY_RANK = "27"
_GENERIC_FACT_FIELDS = tuple(ingestion.GENERIC_FACT_FIELDS)
_SOURCE_BINDING_FIELDS = (
    "source_path", "path_namespace", "byte_count", "sha256",
    "schema_version", "review_unit_id",
)
_ARTIFACT_FIELDS = (
    "reconciled_rows", "source_bindings", "normalized_facts", "review_summary",
)
_PREDECESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338, "universe_review_unit_count": 131,
    "completed_positive_event_count": 119, "completed_positive_unit_count": 19,
    "completed_negative_event_count": 40, "completed_negative_unit_count": 8,
    "completed_total_event_count": 159, "completed_total_unit_count": 27,
    "in_progress_event_count": 0, "in_progress_unit_count": 0,
    "unreviewed_event_count": 179, "unreviewed_unit_count": 104,
}
_SUCCESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338, "universe_review_unit_count": 131,
    "completed_positive_event_count": 119, "completed_positive_unit_count": 19,
    "completed_negative_event_count": 44, "completed_negative_unit_count": 9,
    "completed_total_event_count": 163, "completed_total_unit_count": 28,
    "in_progress_event_count": 0, "in_progress_unit_count": 0,
    "unreviewed_event_count": 175, "unreviewed_unit_count": 103,
}
PREDECESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 135,
    "accepted_review_unit_count": 23,
    "stable_source_identity_count": 23,
    "remaining_unreviewed_chemistry_event_count": 203,
    "remaining_unreviewed_review_unit_upper_bound": 108,
    "decision_category_distribution": {
        "chemistry_positive": 95, "chemistry_negative": 20,
        "task_domain_negative": 20, "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 139,
    "accepted_review_unit_count": 24,
    "stable_source_identity_count": 24,
    "remaining_unreviewed_chemistry_event_count": 199,
    "remaining_unreviewed_review_unit_upper_bound": 107,
    "decision_category_distribution": {
        "chemistry_positive": 95, "chemistry_negative": 20,
        "task_domain_negative": 24, "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
_FORBIDDEN_RICH_FACT_FIELDS = frozenset({
    "completed_lane", "protein_reactive_atom", "ligand_reactive_atom",
    "pair_authority_scope", "role_partition", "role_profile", "seed",
    "minimal_seed", "task_ids", "applicable_task_ids", "PRE", "POST",
    "training_target", "training_mask_targets", "W", "L", "S",
    "boundary_bonds", "primary_anchor",
})
_ALLOWED_RECONCILIATION_FIELDS = frozenset({
    "current_review_status", "current_status_authority_sources_json",
    "calibration_eligible", "calibration_exclusion_reason",
})


class CompletedDecisionReconciliationWithTP2Error(ValueError):
    """Raised when the exact additive TP2 contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWithTP2Error(token)


def _mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _validate_rich_tp2_boundary_v1(bound: Mapping[str, object]) -> None:
    """Verify published rich facts only as projection preconditions."""

    formal = _mapping(bound.get("formal_document"), "TP2_FORMAL_NOT_OBJECT")
    state = _mapping(formal.get("formal_state"), "TP2_FORMAL_STATE_INVALID")
    decisions = _mapping(formal.get("formal_decisions"), "TP2_DECISIONS_INVALID")
    identity = _mapping(formal.get("sample_identity"), "TP2_IDENTITY_INVALID")
    role = _mapping(formal.get("selected_role_context"), "TP2_ROLE_INVALID")
    tasks = _mapping(formal.get("canonical_Exact5"), "TP2_EXACT5_INVALID")
    pre = _mapping(formal.get("PRE_boundary"), "TP2_PRE_INVALID")
    post = _mapping(formal.get("POST_boundary"), "TP2_POST_INVALID")
    training = _mapping(formal.get("training_boundary"), "TP2_TRAINING_INVALID")
    reusable = _mapping(formal.get("reusable_authority_map"), "TP2_AUTHORITY_INVALID")
    sample = _mapping(formal.get("sample_authority_map"), "TP2_SAMPLE_AUTHORITY_INVALID")
    if (
        formal.get("schema_version") != ingestion.FORMAL_DECISION_SCHEMA
        or state.get("approved") is not True
        or state.get("decision_finalized") is not True
        or state.get("human_review_completed") is not True
        or identity.get("review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
        or identity.get("canonical_event_ids") != list(ingestion.EXPECTED_EVENT_IDS)
        or identity.get("raw_priority_rank") != 27
        or identity.get("scaleup_ranks") != [42, 43, 44, 45]
        or identity.get("rank_systems_are_distinct") is not True
    ):
        _fail("TP2_FORMAL_IDENTITY_OR_COMPLETION_INVALID")
    d1 = _mapping(decisions.get("D1_task_relevance"), "TP2_D1_INVALID")
    d2 = _mapping(decisions.get("D2_chemistry"), "TP2_D2_INVALID")
    d3 = _mapping(decisions.get("D3_reactive_pair"), "TP2_D3_INVALID")
    d4 = _mapping(decisions.get("D4_role_candidate"), "TP2_D4_INVALID")
    d5 = _mapping(decisions.get("D5_training_use"), "TP2_D5_INVALID")
    if (
        d1.get("decision") != generic.TASK_NOT_RELEVANT
        or d2.get("decision") != generic.CHEMISTRY_POSITIVE
        or d3.get("protein_atom") != "SG" or d3.get("ligand_atom") != "S1"
        or d3.get("scope") != "CURRENT_TP2_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
        or d3.get("reactive_pair_sample_authoritative") is not True
        or d4.get("decision") != "SELECT_CANDIDATE_0"
        or d4.get("role_profile") != "STRICT_LINKER_PRESENT_V1"
        or d4.get("role_partition_sample_authoritative") is not True
        or d5.get("decision") != generic.TRAINING_NOT_APPLICABLE
        or d5.get("human_training_excluded") is not False
        or d5.get("future_training_admission_candidate") is not False
    ):
        _fail("TP2_D1_D5_BOUNDARY_INVALID")
    seed = _mapping(role.get("minimal_seed"), "TP2_MINIMAL_SEED_INVALID")
    if (
        role.get("role_profile") != "STRICT_LINKER_PRESENT_V1"
        or role.get("warhead_atom_ids") != list(ingestion.WARHEAD_ATOMS)
        or role.get("linker_atom_ids") != list(ingestion.LINKER_ATOMS)
        or role.get("scaffold_atom_ids") != list(ingestion.SCAFFOLD_ATOMS)
        or role.get("boundaries") != list(ingestion.BOUNDARY_BONDS)
        or seed.get("atom_ids") != list(ingestion.MINIMAL_SEED)
        or seed.get("primary_anchor") != ingestion.PRIMARY_ANCHOR
        or seed.get("reusable_minimal_seed_rule") is not False
    ):
        _fail("TP2_ROLE_BOUNDARY_INVALID")
    expected_tasks = [
        {"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias}
        for task_id, semantic, alias, _included, _excluded in ingestion.CANONICAL_TASKS
    ]
    if (
        tasks.get("tasks") != expected_tasks or tasks.get("task_count") != 5
        or tasks.get("role_derived_structural_applicability_task_ids") != [0, 1, 2, 3, 4]
        or tasks.get("B3_present") is not True or tasks.get("sixth_task") is not False
        or tasks.get("authoritative_task_labels_created") is not False
        or tasks.get("event_task_label_rows_materialized") is not False
        or tasks.get("training_mask_targets_available_now") is not False
    ):
        _fail("TP2_EXACT5_OR_LABEL_BOUNDARY_INVALID")
    if (
        pre.get("candidate_PRE_free_source_graph_count") != 0
        or pre.get("mapping_count") != 0
        or pre.get("PRE_MAPPING_STATUS") != ingestion.PRE_MAPPING_STATUS
        or pre.get("PRE_STATUS") != ingestion.PRE_STATUS
        or any(pre.get(key) is not False for key in (
            "PRE_topology_authority", "PRE_geometry_authority",
            "PRE_coordinates_authority", "POST_to_PRE_copy", "PRE_zero_fill",
        ))
        or post.get("POST_source_evidence_available") is not True
        or post.get("POST_geometry_training_authority") is not False
        or post.get("POST_geometry_training_target_created") is not False
    ):
        _fail("TP2_PRE_POST_BOUNDARY_INVALID")
    if (
        training.get("human_training_use") != generic.TRAINING_NOT_APPLICABLE
        or training.get("human_training_excluded") is not False
        or training.get("future_training_admission_candidate") is not False
        or any(training.get(key) is not False for key in (
            "formal_training_admitted", "training_materialization_allowed",
            "training_mask_targets_available_now", "current_runtime_model_usable",
            "parameter_update_authorization", "READY_FOR_TRAINING", "TRAINING_STARTED",
        ))
        or any(value is not False for value in reusable.values())
        or any(sample.get(key) is not True for key in (
            "chemistry_sample_authoritative", "reactive_pair_sample_authoritative",
            "role_partition_sample_authoritative", "role_profile_sample_authoritative",
        ))
    ):
        _fail("TP2_TRAINING_OR_AUTHORITY_BOUNDARY_INVALID")
    census = _mapping(bound.get("current_census_boundary"), "TP2_CENSUS_BOUNDARY_INVALID")
    if census.get("census_modified_by_ingestion") is not False:
        _fail("TP2_CURRENT_CENSUS_WAS_NOT_PRESERVED")


def _projection_parts_v1(
    bound: Mapping[str, object],
) -> tuple[generic.SourceBinding, tuple[Mapping[str, Any], ...]]:
    _validate_rich_tp2_boundary_v1(bound)
    compatibility = _mapping(
        bound.get("generic_Exact11_compatibility"), "TP2_GENERIC_COMPATIBILITY_INVALID"
    )
    binding_record = _mapping(
        compatibility.get("actual_source_binding"), "TP2_GENERIC_BINDING_INVALID"
    )
    records = tuple(
        _mapping(item, "TP2_GENERIC_FACT_NOT_OBJECT")
        for item in _list(compatibility.get("facts"), "TP2_GENERIC_FACTS_NOT_LIST")
    )
    if (
        compatibility.get("generic_exact11_compatibility_pass") is not True
        or compatibility.get("generic_fact_field_count") != 11
        or compatibility.get("generic_fact_fields") != list(_GENERIC_FACT_FIELDS)
        or compatibility.get("accepted_fact_count") != 4
        or compatibility.get("rich_fields_leaked") is not False
        or compatibility.get("reconciliation_performed") is not False
        or tuple(binding_record) != _SOURCE_BINDING_FIELDS
        or any(tuple(record) != _GENERIC_FACT_FIELDS for record in records)
    ):
        _fail("TP2_PUBLISHED_GENERIC_PROJECTION_NOT_EXACT11")
    try:
        binding = generic.SourceBinding(**dict(binding_record))
    except TypeError as error:
        raise CompletedDecisionReconciliationWithTP2Error(
            "TP2_GENERIC_BINDING_CONSTRUCTION_FAILED"
        ) from error
    return binding, records


def _validate_projected_tp2_source_v1(
    source: generic.NormalizedDecisionSource,
    records: Sequence[Mapping[str, object]],
) -> None:
    if tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) != _GENERIC_FACT_FIELDS:
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    if len(source.facts) != 4 or len(records) != 4:
        _fail("TP2_SOURCE_PROJECTION_NOT_EXACT4")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithTP2Error(
            "TP2_GENERIC_SOURCE_BINDING_REJECTED:" + str(error)
        ) from error
    for fact, record in zip(source.facts, records, strict=True):
        actual = asdict(fact)
        if (
            actual != dict(record) or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
        ):
            _fail("TP2_GENERIC_PROJECTION_CLASSIFICATION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithTP2Error(
                "TP2_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_bound_tp2_v1(bound: Mapping[str, object]) -> generic.NormalizedDecisionSource:
    binding, records = _projection_parts_v1(bound)
    try:
        facts = tuple(generic.NormalizedCompletedDecisionFact(**dict(row)) for row in records)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithTP2Error(
            "TP2_GENERIC_FACT_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(binding=binding, facts=facts)
    _validate_projected_tp2_source_v1(source, records)
    return source


def project_tp2_completed_decision_v1(*, repo_root: Path) -> generic.NormalizedDecisionSource:
    """Load and validate TP2 through its published ingestion public API."""

    try:
        bound = ingestion.load_frozen_formal_decision_v1(Path(repo_root).resolve())
    except ingestion.TP2IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithTP2Error(
            "TP2_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_bound_tp2_v1(bound)


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    records: Sequence[Mapping[str, object]],
) -> None:
    before, after = tuple(predecessor), tuple(successor)
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    if len(before) != 23 or len(before_facts) != 135:
        _fail("PREDECESSOR_WITH_4LH_SOURCE_CHAIN_NOT_EXACT23_135")
    if len(after) != 24 or after[:-1] != before or len(after_facts) != 139:
        _fail("TP2_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT24_139")
    _validate_projected_tp2_source_v1(after[-1], records)
    if after_facts[:135] != before_facts or after_facts[135:] != after[-1].facts:
        _fail("TP2_FACT_CHAIN_NOT_PREFIX_APPEND_EXACT135_PLUS4")
    before_events = [fact.canonical_event_id for fact in before_facts]
    after_events = [fact.canonical_event_id for fact in after_facts]
    if (
        any(event in set(before_events) for event in ingestion.EXPECTED_EVENT_IDS)
        or after_events[-4:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(before_events)) != 135 or len(set(after_events)) != 139
    ):
        _fail("TP2_EVENT_PREFIX_OR_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    before_ids = {source.binding.stable_identity for source in before}
    if (
        len(before_units) != 23 or len(before_ids) != 23
        or len({source.binding.review_unit_id for source in after}) != 24
        or len({source.binding.stable_identity for source in after}) != 24
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(source.binding.path_namespace != "repository_parent_relative" for source in after)
    ):
        _fail("TP2_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_tp2_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_4lh_v1(root)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    _binding, records = _projection_parts_v1(bound)
    after = (*before, _project_bound_tp2_v1(bound))
    _validate_source_chain_v1(before, after, records)
    return after


def _prove_tp2_predecessor_historical_state_v1(rows: Sequence[Mapping[str, str]]) -> None:
    targets = [row for row in rows if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS]
    if (
        len(rows) != 338 or len(targets) != 4
        or tuple(row["canonical_event_id"] for row in targets) != ingestion.EXPECTED_EVENT_IDS
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
        _fail("TP2_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_4LH_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("TP2_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 135 or len(after.normalized_facts) != 139:
        _fail("TP2_RECONCILIATION_FACT_COUNT_INVALID")
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
            != generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
            or new["calibration_eligible"] != "false"
            or new["calibration_exclusion_reason"] != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("TP2_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("TP2_RECONCILIATION_DELTA_NOT_EXACT4_AND_334")


def _adapt_historical_v1(repo_root: Path) -> tuple[dict[str, str], ...]:
    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    return (
        predecessor_owner.predecessor_owner.predecessor_owner.gve_predecessor
        .sr2_predecessor.gd1_predecessor.four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(historical)
    )


def _build_components_v1(
    repo_root: Path,
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
    generic.ReconciliationResult,
    generic.ReconciliationResult,
]:
    root = Path(repo_root).resolve()
    before_sources = predecessor_owner.load_real_completed_decision_sources_with_4lh_v1(root)
    adapted = _adapt_historical_v1(root)
    _prove_tp2_predecessor_historical_state_v1(adapted)
    before_result = generic.reconcile_completed_human_decisions_v1(adapted, before_sources)
    _prove_tp2_predecessor_historical_state_v1(before_result.reconciled_rows)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    _binding, records = _projection_parts_v1(bound)
    after_sources = (*before_sources, _project_bound_tp2_v1(bound))
    _validate_source_chain_v1(before_sources, after_sources, records)
    after_result = generic.reconcile_completed_human_decisions_v1(adapted, after_sources)
    _validate_reconciliation_delta_v1(before_result, after_result)
    return before_sources, after_sources, before_result, after_result


def reconcile_real_completed_human_decisions_with_tp2_v1(
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
        "normalized_facts": [asdict(fact) for source in sources for fact in source.facts],
        "review_summary": dict(reconciliation.review_summary),
    }


def _validate_artifact_mapping_v1(
    value: object,
    *,
    predecessor_sources: Sequence[generic.NormalizedDecisionSource],
    successor_sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> None:
    artifact = _mapping(value, "TP2_ARTIFACT_NOT_OBJECT")
    bindings = _list(artifact.get("source_bindings"), "TP2_BINDINGS_NOT_LIST")
    facts = _list(artifact.get("normalized_facts"), "TP2_FACTS_NOT_LIST")
    rows = _list(artifact.get("reconciled_rows"), "TP2_ROWS_NOT_LIST")
    predecessor_facts = [asdict(fact) for source in predecessor_sources for fact in source.facts]
    if (
        tuple(artifact) != _ARTIFACT_FIELDS
        or len(bindings) != 24 or len(facts) != 139 or len(rows) != 338
        or bindings != [asdict(source.binding) for source in successor_sources]
        or any(type(item) is not dict or set(item) != set(_SOURCE_BINDING_FIELDS) for item in bindings)
        or facts != [asdict(fact) for source in successor_sources for fact in source.facts]
        or facts[:135] != predecessor_facts or facts[135:] != [asdict(fact) for fact in successor_sources[-1].facts]
        or any(type(item) is not dict or set(item) != set(_GENERIC_FACT_FIELDS) or _FORBIDDEN_RICH_FACT_FIELDS & set(item) for item in facts)
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("TP2_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


def build_artifact_v1(repo_root: Path) -> bytes:
    before_sources, after_sources, _before_result, after_result = _build_components_v1(repo_root)
    mapping = _artifact_mapping_v1(after_sources, after_result)
    _validate_artifact_mapping_v1(
        mapping, predecessor_sources=before_sources,
        successor_sources=after_sources, reconciliation=after_result,
    )
    return (json.dumps(mapping, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _validate_destination_v1(repo_root: Path, destination: Path) -> None:
    if destination.resolve() != (repo_root / OUTPUT_RELATIVE).resolve():
        _fail("TP2_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("TP2_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {item.name for item in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("TP2_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_tp2_reconciliation_", dir=destination.parent)
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
    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    try:
        metadata = destination.lstat()
        observed = destination.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWithTP2Error(
            "TP2_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111:
        _fail("TP2_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    expected = build_artifact_v1(root)
    if observed != expected:
        _fail("TP2_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS", "artifact_count": 1, "source_count": 24,
        "accepted_fact_count": 139, "byte_identical_to_rebuild": True,
        "training_authority": False, "ready_for_training": False,
    }
