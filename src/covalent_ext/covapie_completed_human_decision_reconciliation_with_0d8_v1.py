"""Append the published 0D8 Exact4 to generic completed-decision facts.

This metadata-only successor consumes the already-published 0D8 ingestion
projection, appends it to the LCY source chain, and invokes the unchanged
generic reconciliation owner.  Rich 0D8 chemistry, role, task, and geometry
metadata are validation preconditions only; generic records remain Exact11.
The sole materialized output is a deterministic JSON representation of the
existing generic ``ReconciliationResult`` contract.
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

from . import covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_lcy_v1 as predecessor_owner


__all__ = (
    "CompletedDecisionReconciliationWith0D8Error",
    "project_0d8_completed_decision_v1",
    "load_real_completed_decision_sources_with_0d8_v1",
    "reconcile_real_completed_human_decisions_with_0d8_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)


SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_0d8_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_0d8_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_completed_human_decision_reconciliation_with_0d8_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_completed_human_decision_reconciliation_with_0d8_v1"
)
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_0d8_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    OUTPUT_RELATIVE,
)

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "25"
_GENERIC_FACT_FIELDS = ingestion.GENERIC_FACT_FIELDS
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
    4,
)
_SUCCESSOR_SOURCE_FACT_COUNTS = (*_PREDECESSOR_SOURCE_FACT_COUNTS, 4)
_PREDECESSOR_REVIEW_SUMMARY = {
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
_SUCCESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 40,
    "completed_negative_unit_count": 8,
    "completed_total_event_count": 155,
    "completed_total_unit_count": 26,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 183,
    "unreviewed_unit_count": 105,
}

# These are the frozen completed-decision coverage metrics requested for this
# successor.  They are deliberately separate from the generic owner's
# historical review_summary (which also includes earlier historical state).
PREDECESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 127,
    "accepted_review_unit_count": 21,
    "stable_source_identity_count": 21,
    "remaining_unreviewed_chemistry_event_count": 211,
    "remaining_unreviewed_review_unit_upper_bound": 110,
    "decision_category_distribution": {
        "chemistry_positive": 91,
        "chemistry_negative": 20,
        "task_domain_negative": 16,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 131,
    "accepted_review_unit_count": 22,
    "stable_source_identity_count": 22,
    "remaining_unreviewed_chemistry_event_count": 207,
    "remaining_unreviewed_review_unit_upper_bound": 109,
    "decision_category_distribution": {
        "chemistry_positive": 91,
        "chemistry_negative": 20,
        "task_domain_negative": 20,
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
        "pair_authority_scope",
        "role_partition",
        "role_profile",
        "selected_candidate_index_0based",
        "warhead_atoms",
        "linker_atoms",
        "scaffold_atoms",
        "W",
        "L",
        "S",
        "boundary_bonds",
        "canonical_task_applicability",
        "applicable_task_ids",
        "authoritative_task_labels_created",
        "event_task_label_rows_materialized",
        "training_mask_targets",
        "PRE_source_graph",
        "PRE_mapping",
        "PRE_status",
        "PRE_geometry",
        "POST_geometry",
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


class CompletedDecisionReconciliationWith0D8Error(ValueError):
    """Raised when the exact additive 0D8 contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWith0D8Error(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _expected_binding_v1() -> generic.SourceBinding:
    formal_binding = ingestion.FORMAL_BINDINGS[0]
    return generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=formal_binding[2],
        sha256=formal_binding[3],
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )


def _validate_rich_0d8_boundary_v1(bound: Mapping[str, object]) -> None:
    """Prove the narrow scientific and non-training boundary before projection."""

    formal = _require_mapping(bound.get("formal"), "0D8_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != ingestion.FORMAL_DECISION_SCHEMA
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
        or formal.get("human_review_completed") is not True
        or formal.get("formal_decision_semantic_canonical_sha256")
        != ingestion.FORMAL_SEMANTIC_CANONICAL_SHA256
    ):
        _fail("0D8_FORMAL_IDENTITY_OR_COMPLETION_INVALID")

    d1 = _require_mapping(formal.get("D1_formal_task_relevance"), "0D8_D1_INVALID")
    d2 = _require_mapping(formal.get("D2_formal_chemistry"), "0D8_D2_INVALID")
    d3 = _require_mapping(formal.get("D3_formal_reactive_pair"), "0D8_D3_INVALID")
    d4 = _require_mapping(formal.get("D4_formal_role_partition"), "0D8_D4_INVALID")
    d5 = _require_mapping(formal.get("D5_formal_training_use"), "0D8_D5_INVALID")
    tasks = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "0D8_EXACT5_INVALID",
    )
    pre = _require_mapping(formal.get("PRE_boundary"), "0D8_PRE_INVALID")
    if (
        d1.get("D1") != "NOT_RELEVANT"
        or d1.get("sample_task_relevance_authority") is not True
        or d2.get("D2") != "POSITIVE"
        or d2.get("sample_positive_chemistry_authority") is not True
        or d3.get("D3") != "CONFIRM_OBSERVED_PAIR"
        or d3.get("protein_atom") != "SG"
        or d3.get("ligand_atom") != "C8"
        or d3.get("sample_reactive_pair_authority") is not True
        or d4.get("D4") != "SELECT_CANDIDATE_0"
        or d4.get("role_profile") != ingestion.EXPECTED_ROLE_PROFILE
        or d4.get("W_atom_ids") != list(ingestion.WARHEAD_ATOMS)
        or d4.get("L_atom_ids") != []
        or d4.get("S_atom_ids") != list(ingestion.SCAFFOLD_ATOMS)
        or d4.get("sample_role_partition_authority") is not True
        or d5.get("D5") != "NOT_APPLICABLE"
        or d5.get("human_training_excluded") is not False
        or d5.get("formal_training_admitted") is not False
        or d5.get("tensor_target_created") is not False
        or d5.get("training_materialization_allowed") is not False
        or d5.get("parameter_update_authorization") is not False
    ):
        _fail("0D8_FROZEN_D1_D5_OR_ROLE_BOUNDARY_INVALID")

    task_rows = _require_list(tasks.get("tasks"), "0D8_EXACT5_TASKS_NOT_LIST")
    expected_tasks = [
        {"display_alias": alias, "semantic_long_name": semantic, "task_id": task_id}
        for task_id, semantic, alias, _generated, _fixed in ingestion.CANONICAL_TASKS
    ]
    if (
        tasks.get("global_task_count") != 5
        or tasks.get("B3_present") is not True
        or tasks.get("sixth_task") is not False
        or tasks.get("sample_applicable_task_ids") != [0, 3, 4]
        or tasks.get("authoritative_task_labels_created") is not False
        or tasks.get("event_task_label_rows_materialized") is not False
        or task_rows != expected_tasks
    ):
        _fail("0D8_CANONICAL_EXACT5_OR_LABEL_BOUNDARY_INVALID")

    per_event = _require_list(pre.get("per_event"), "0D8_PRE_EVENTS_NOT_LIST")
    if len(per_event) != 4 or any(
        type(row) is not dict
        or row.get("PRE_source_graph_count") != 0
        or row.get("PRE_mapping_count") != 0
        or row.get("PRE_mapping_status") != ingestion.PRE_MAPPING_STATUS
        or row.get("PRE_status") != ingestion.PRE_STATUS
        for row in per_event
    ):
        _fail("0D8_PRE_UNRESOLVED_BOUNDARY_INVALID")

    census = _require_mapping(
        bound.get("current_census_boundary"), "0D8_CENSUS_BOUNDARY_INVALID"
    )
    if (
        census.get("census_refresh_performed") is not False
        or census.get("current_census_modified") is not False
        or census.get("target_event_count") != 4
        or census.get("current_global_status") != generic.CURRENTLY_UNREVIEWED
    ):
        _fail("0D8_CURRENT_CENSUS_WAS_NOT_PRESERVED")


def _projection_records_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    compatibility = _require_mapping(
        bound.get("generic_owner_compatibility"),
        "0D8_GENERIC_COMPATIBILITY_NOT_OBJECT",
    )
    records = _require_list(
        compatibility.get("facts"), "0D8_GENERIC_PROJECTION_NOT_LIST"
    )
    expected_binding = asdict(_expected_binding_v1())
    if (
        compatibility.get("generic_exact11_compatibility_pass") is not True
        or compatibility.get("generic_fact_field_count") != 11
        or compatibility.get("generic_fact_fields") != list(_GENERIC_FACT_FIELDS)
        or compatibility.get("accepted_fact_count") != 4
        or compatibility.get("actual_source_binding") != expected_binding
        or compatibility.get("rich_fields_leaked") is not False
        or compatibility.get("reconciliation_performed") is not False
        or len(records) != 4
    ):
        _fail("0D8_INGESTION_GENERIC_EXACT11_CONTRACT_INVALID")
    typed = tuple(
        _require_mapping(record, "0D8_GENERIC_PROJECTION_FACT_NOT_OBJECT")
        for record in records
    )
    if tuple(str(record.get("canonical_event_id")) for record in typed) != tuple(
        ingestion.EXPECTED_EVENT_IDS
    ):
        _fail("0D8_GENERIC_PROJECTION_EVENT_ORDER_INVALID")
    return typed


def _validate_projected_0d8_source_v1(
    source: generic.NormalizedDecisionSource,
    projection_records: Sequence[Mapping[str, object]],
) -> None:
    if tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) != tuple(
        _GENERIC_FACT_FIELDS
    ):
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    expected_binding = _expected_binding_v1()
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding != expected_binding
        or len(source.facts) != 4
        or len(projection_records) != 4
    ):
        _fail("0D8_SOURCE_PROJECTION_IDENTITY_INVALID")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWith0D8Error(
            "0D8_GENERIC_SOURCE_BINDING_REJECTED:" + str(error)
        ) from error
    for fact, projection in zip(source.facts, projection_records, strict=True):
        actual = asdict(fact)
        if (
            tuple(fact.__dataclass_fields__) != tuple(_GENERIC_FACT_FIELDS)
            or actual != dict(projection)
            or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
        ):
            _fail("0D8_GENERIC_PROJECTION_NOT_EXACT_OWNER_PROJECTION")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWith0D8Error(
                "0D8_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_0d8_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    _validate_rich_0d8_boundary_v1(bound)
    records = _projection_records_v1(bound)
    try:
        facts = tuple(
            generic.NormalizedCompletedDecisionFact(**dict(record))
            for record in records
        )
    except TypeError as error:
        raise CompletedDecisionReconciliationWith0D8Error(
            "0D8_GENERIC_PROJECTION_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(), facts=facts
    )
    _validate_projected_0d8_source_v1(source, records)
    return source


def project_0d8_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load 0D8 through its published ingestion owner and copy Exact11 facts."""

    try:
        bound = ingestion.load_frozen_formal_decision_v1(Path(repo_root).resolve())
    except ingestion.ZeroD8IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith0D8Error(
            "0D8_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_0d8_binding_v1(bound)


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    projection_records: Sequence[Mapping[str, object]],
) -> None:
    before = tuple(predecessor)
    after = tuple(successor)
    if (
        len(before) != 21
        or tuple(len(source.facts) for source in before)
        != _PREDECESSOR_SOURCE_FACT_COUNTS
        or sum(len(source.facts) for source in before) != 127
    ):
        _fail("PREDECESSOR_WITH_LCY_SOURCE_CHAIN_NOT_EXACT21_127")
    if (
        len(after) != 22
        or after[:-1] != before
        or tuple(len(source.facts) for source in after)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or sum(len(source.facts) for source in after) != 131
    ):
        _fail("0D8_SUCCESSOR_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT22_131")
    _validate_projected_0d8_source_v1(after[-1], projection_records)
    before_events = [fact.canonical_event_id for source in before for fact in source.facts]
    after_events = [fact.canonical_event_id for source in after for fact in source.facts]
    if (
        len(set(before_events)) != 127
        or after_events[:-4] != before_events
        or after_events[-4:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(after_events)) != 131
    ):
        _fail("0D8_GENERIC_FACT_PREFIX_OR_EVENT_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    after_units = {source.binding.review_unit_id for source in after}
    before_ids = {source.binding.stable_identity for source in before}
    after_ids = {source.binding.stable_identity for source in after}
    if (
        len(before_units) != 21
        or len(before_ids) != 21
        or len(after_units) != 22
        or len(after_ids) != 22
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(source.binding.path_namespace != "repository_parent_relative" for source in after)
    ):
        _fail("0D8_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_0d8_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Return the published LCY chain plus exactly one 0D8 source."""

    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_lcy_v1(root)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    projection_records = _projection_records_v1(bound)
    source = _project_validated_0d8_binding_v1(bound)
    after = (*before, source)
    _validate_source_chain_v1(before, after, projection_records)
    return after


def _prove_0d8_predecessor_historical_state_v1(
    rows: Sequence[Mapping[str, str]],
) -> None:
    target_ids = set(ingestion.EXPECTED_EVENT_IDS)
    targets = [row for row in rows if row.get("canonical_event_id") in target_ids]
    if (
        len(rows) != 338
        or len(targets) != 4
        or {row["canonical_event_id"] for row in targets} != target_ids
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
        _fail("0D8_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_LCY_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("0D8_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 127 or len(after.normalized_facts) != 131:
        _fail("0D8_RECONCILIATION_FACT_COUNT_INVALID")
    target_ids = set(ingestion.EXPECTED_EVENT_IDS)
    changed = 0
    for old, new in zip(before.reconciled_rows, after.reconciled_rows, strict=True):
        if old.get("canonical_event_id") not in target_ids:
            if old != new:
                _fail("0D8_NON_TARGET_RECONCILIATION_ROW_CHANGED")
            continue
        changed_fields = {key for key in old if old[key] != new[key]}
        if (
            changed_fields != _ALLOWED_RECONCILIATION_FIELDS
            or old["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or new["current_review_status"] != generic.COMPLETED_HUMAN_NEGATIVE
            or new["current_status_authority_sources_json"]
            != generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
            or new["calibration_eligible"] != "false"
            or new["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("0D8_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed += 1
    if changed != 4:
        _fail("0D8_RECONCILIATION_DELTA_NOT_EXACT4")
    new_facts = [
        fact for fact in after.normalized_facts if fact.canonical_event_id in target_ids
    ]
    if len(new_facts) != 4 or any(
        fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        for fact in new_facts
    ):
        _fail("0D8_TASK_NEGATIVE_CHEMISTRY_POSITIVE_BOUNDARY_INVALID")


def reconcile_real_completed_human_decisions_with_0d8_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact22 sources through the unchanged generic owner in memory."""

    root = Path(repo_root).resolve()
    before = predecessor_owner.reconcile_real_completed_human_decisions_with_lcy_v1(root)
    _prove_0d8_predecessor_historical_state_v1(before.reconciled_rows)
    historical = generic.load_real_historical_reconciliation_v1(root)
    adapted = (
        predecessor_owner.gve_predecessor.sr2_predecessor.gd1_predecessor
        .four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(historical)
    )
    _prove_0d8_predecessor_historical_state_v1(adapted)
    after = generic.reconcile_completed_human_decisions_v1(
        adapted, load_real_completed_decision_sources_with_0d8_v1(root)
    )
    _validate_reconciliation_delta_v1(before, after)
    return after


def _validate_artifact_mapping_v1(
    value: object,
    *,
    predecessor_sources: Sequence[generic.NormalizedDecisionSource],
    successor_sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> None:
    artifact = _require_mapping(value, "0D8_ARTIFACT_NOT_OBJECT")
    if tuple(artifact) != _ARTIFACT_FIELDS:
        _fail("0D8_ARTIFACT_RESULT_SCHEMA_INVALID")
    bindings = _require_list(artifact.get("source_bindings"), "0D8_BINDINGS_NOT_LIST")
    facts = _require_list(artifact.get("normalized_facts"), "0D8_FACTS_NOT_LIST")
    rows = _require_list(artifact.get("reconciled_rows"), "0D8_ROWS_NOT_LIST")
    if (
        bindings != [asdict(source.binding) for source in successor_sources]
        or any(type(binding) is not dict or set(binding) != set(_SOURCE_BINDING_FIELDS) for binding in bindings)
        or facts != [asdict(fact) for source in successor_sources for fact in source.facts]
        or any(
            type(fact) is not dict
            or set(fact) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(fact)
            for fact in facts
        )
        or facts[:127]
        != [asdict(fact) for source in predecessor_sources for fact in source.facts]
        or facts[127:] != [asdict(fact) for fact in successor_sources[-1].facts]
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("0D8_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


def build_artifact_v1(repo_root: Path) -> bytes:
    """Build the sole deterministic reconciliation JSON without writing it."""

    root = Path(repo_root).resolve()
    predecessor_result = (
        predecessor_owner.reconcile_real_completed_human_decisions_with_lcy_v1(root)
    )
    predecessor_sources = predecessor_owner.load_real_completed_decision_sources_with_lcy_v1(
        root
    )
    bound = ingestion.load_frozen_formal_decision_v1(root)
    projection_records = _projection_records_v1(bound)
    successor_sources = (
        *predecessor_sources,
        _project_validated_0d8_binding_v1(bound),
    )
    _validate_source_chain_v1(
        predecessor_sources, successor_sources, projection_records
    )
    historical = generic.load_real_historical_reconciliation_v1(root)
    adapted = (
        predecessor_owner.gve_predecessor.sr2_predecessor.gd1_predecessor
        .four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(historical)
    )
    reconciliation = generic.reconcile_completed_human_decisions_v1(
        adapted, successor_sources
    )
    _validate_reconciliation_delta_v1(predecessor_result, reconciliation)
    mapping = {
        "reconciled_rows": [dict(row) for row in reconciliation.reconciled_rows],
        "source_bindings": [asdict(source.binding) for source in successor_sources],
        "normalized_facts": [
            asdict(fact) for source in successor_sources for fact in source.facts
        ],
        "review_summary": dict(reconciliation.review_summary),
    }
    _validate_artifact_mapping_v1(
        mapping,
        predecessor_sources=predecessor_sources,
        successor_sources=successor_sources,
        reconciliation=reconciliation,
    )
    return (
        json.dumps(
            mapping,
            ensure_ascii=False,
            sort_keys=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _validate_destination_v1(repo_root: Path, destination: Path) -> None:
    expected = (repo_root / OUTPUT_RELATIVE).resolve()
    if destination.resolve() != expected:
        _fail("0D8_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("0D8_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {path.name for path in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("0D8_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    """Atomically write only the authorized reconciliation JSON."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".covapie_0d8_reconciliation_", dir=destination.parent
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
        metadata = destination.lstat()
        observed = destination.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWith0D8Error(
            "0D8_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ):
        _fail("0D8_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    expected = build_artifact_v1(root)
    if observed != expected:
        _fail("0D8_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 22,
        "accepted_fact_count": 131,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }
