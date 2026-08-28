"""Reconcile frozen NEQ completion through the unchanged generic owner.

NEQ Exact6 already has the generic owner's required historical prior state,
``CURRENTLY_UNREVIEWED``.  This metadata-only successor projects the
owner-validated NEQ decision, reuses the published YUN source chain and ONL
transition owner, proves that transition leaves NEQ untouched, and delegates
the final in-memory overlay to the generic reconciler.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_yun_v1 as yun_successor,
)
from . import (
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v1
    as neq_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithNEQError",
    "project_neq_completed_decision_v1",
    "load_real_completed_decision_sources_with_neq_v1",
    "reconcile_real_completed_human_decisions_with_neq_v1",
)


_NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    neq_ingestion_owner.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
_NEQ_FORMAL_DECISION_BYTE_COUNT = neq_ingestion_owner.FORMAL_DECISION_BYTE_COUNT
_NEQ_FORMAL_DECISION_SHA256 = neq_ingestion_owner.FORMAL_DECISION_SHA256
_NEQ_FORMAL_DECISION_SCHEMA = neq_ingestion_owner.FORMAL_DECISION_SCHEMA
_NEQ_REVIEW_UNIT_ID = neq_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_NEQ_EVENT_IDS = neq_ingestion_owner.EXPECTED_EVENT_IDS

_NEQ_EVENT_COUNT = 6
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7)
_EXPECTED_SITE_COUNTS = {"CYS:22-": 3, "CYS:81-": 3}
NEQ_TRANSITION_ADAPTER_CREATED = False


class CompletedDecisionReconciliationWithNEQError(ValueError):
    """Raised when the exact NEQ reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithNEQError(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _project_validated_neq_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only completed-decision fields from owner-validated NEQ data."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "NEQ_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": _NEQ_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _NEQ_FORMAL_DECISION_SHA256,
        "schema_version": _NEQ_FORMAL_DECISION_SCHEMA,
        "review_unit_id": _NEQ_REVIEW_UNIT_ID,
        "verification_status": "MATCHED",
    }
    if any(
        binding_value.get(key) != value
        for key, value in expected_binding.items()
    ):
        _fail("NEQ_FORMAL_DECISION_BINDING_INVALID")

    normalized = _require_mapping(
        bound.get("normalized"), "NEQ_NORMALIZED_DECISION_NOT_OBJECT"
    )
    events = _require_list(
        normalized.get("events"), "NEQ_NORMALIZED_EVENTS_NOT_LIST"
    )
    if len(events) != _NEQ_EVENT_COUNT:
        _fail("NEQ_NORMALIZED_EVENT_COUNT_NOT_EXACT6")

    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    site_counts: Counter[str] = Counter()
    for value in events:
        event = _require_mapping(value, "NEQ_NORMALIZED_EVENT_NOT_OBJECT")
        event_id = event.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("NEQ_NORMALIZED_EVENT_ID_INVALID")
        observed_ids.append(event_id)
        site_id = event.get("cys_residue_id")
        if type(site_id) is not str:
            _fail("NEQ_NORMALIZED_SITE_ID_INVALID:" + event_id)
        site_counts[site_id] += 1
        if (
            event.get("decision_finalized") is not True
            or event.get("D1_task_relevance") != generic.TASK_RELEVANT
            or event.get("D2_chemistry_support")
            != generic.CHEMISTRY_POSITIVE
            or event.get("D5_training_use") != generic.TRAINING_EXCLUDE
            or event.get("human_training_excluded") is not True
            or event.get("training_admitted") is not False
        ):
            _fail("NEQ_NORMALIZED_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_NEQ_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=(
                    generic.COMPLETED_HUMAN_POSITIVE
                ),
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_EXCLUDE,
                human_training_excluded=True,
                source_decision_schema=_NEQ_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_NEQ_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _NEQ_EVENT_COUNT:
        _fail("NEQ_NORMALIZED_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _NEQ_EVENT_IDS:
        _fail("NEQ_NORMALIZED_EVENT_COVERAGE_NOT_EXACT6")
    if dict(site_counts) != _EXPECTED_SITE_COUNTS:
        _fail("NEQ_DUAL_SITE_IDENTITY_NOT_EXACT_3_PLUS_3")

    site_inventory = _require_mapping(
        normalized.get("site_inventory"), "NEQ_SITE_INVENTORY_NOT_OBJECT"
    )
    if (
        site_inventory.get("distinct_cys_residue_identities")
        != ["CYS:22-", "CYS:81-"]
        or site_inventory.get("distinct_cys_residue_identity_count") != 2
        or site_inventory.get("CYS22_event_count") != 3
        or site_inventory.get("CYS81_event_count") != 3
    ):
        _fail("NEQ_SITE_INVENTORY_IDENTITY_INVALID")

    binding = generic.SourceBinding(
        source_path=(
            _NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=_NEQ_FORMAL_DECISION_BYTE_COUNT,
        sha256=_NEQ_FORMAL_DECISION_SHA256,
        schema_version=_NEQ_FORMAL_DECISION_SCHEMA,
        review_unit_id=_NEQ_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_neq_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the NEQ ingestion owner and project its validated Exact6."""

    try:
        bound = neq_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except neq_ingestion_owner.NEQIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithNEQError(
            "NEQ_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_neq_binding_v1(bound)


def _prove_neq_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the frozen original NEQ unit meets generic preconditions."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithNEQError(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_NEQ_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _NEQ_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("NEQ_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _NEQ_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("NEQ_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _NEQ_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("NEQ_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT6")
    neq_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if any(row["raw_review_unit_id"] != _NEQ_REVIEW_UNIT_ID for row in neq_rows):
        _fail("NEQ_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in neq_rows
    ):
        _fail("NEQ_PRIOR_STATE_NOT_EXACT6_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_neq_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove reuse of the ONL owner did not normalize any NEQ field."""

    expected_ids = set(_NEQ_EVENT_IDS)
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
    if set(original_by_event) != expected_ids:
        _fail("NEQ_ORIGINAL_EVENT_SET_NOT_EXACT6")
    if set(adapted_by_event) != expected_ids:
        _fail("NEQ_ADAPTED_EVENT_SET_NOT_EXACT6")
    changed = [
        event_id
        for event_id in _NEQ_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_NEQ_ROW:" + changed[0])


def load_real_completed_decision_sources_with_neq_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load FFQ, POA, G3H, ONL, PRF, 2VS, 1F8, YUN, and NEQ decisions."""

    existing = yun_successor.load_real_completed_decision_sources_with_yun_v1(
        repo_root
    )
    if len(existing) != 8 or tuple(len(source.facts) for source in existing) != (
        _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_YUN_SOURCE_COMPOSITION_INVALID")
    source = project_neq_completed_decision_v1(repo_root=repo_root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding.review_unit_id != _NEQ_REVIEW_UNIT_ID
        or any(fact.review_unit_id != _NEQ_REVIEW_UNIT_ID for fact in source.facts)
    ):
        _fail("NEQ_SOURCE_REVIEW_UNIT_MISMATCH")
    sources = (*existing, source)
    if len(sources) != 9:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT9")
    if len({item.binding.review_unit_id for item in sources}) != 9:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT9")
    if len({item.binding.stable_identity for item in sources}) != 9:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT9")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 78:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_78")
    if len(set(event_ids)) != 78:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_neq_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact9 sources through the generic owner, entirely in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_neq_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_neq_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_neq_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
