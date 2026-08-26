"""Reconcile frozen 2VS completion through the unchanged generic owner.

2VS Exact8 already has the generic owner's required historical prior state,
``CURRENTLY_UNREVIEWED``.  This metadata-only successor projects the
owner-validated 2VS decision, reuses the PRF completed-source chain and the
published ONL transition owner, proves that transition leaves 2VS untouched,
and delegates the final in-memory overlay to the generic reconciler.
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
    covapie_completed_human_decision_reconciliation_with_prf_v1 as prf_successor,
)
from . import (
    covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1
    as two_vs_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWith2VSError",
    "project_2vs_completed_decision_v1",
    "load_real_completed_decision_sources_with_2vs_v1",
    "reconcile_real_completed_human_decisions_with_2vs_v1",
)


_2VS_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    two_vs_ingestion_owner.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
_2VS_FORMAL_DECISION_BYTE_COUNT = (
    two_vs_ingestion_owner.FORMAL_DECISION_BYTE_COUNT
)
_2VS_FORMAL_DECISION_SHA256 = two_vs_ingestion_owner.FORMAL_DECISION_SHA256
_2VS_FORMAL_DECISION_SCHEMA = two_vs_ingestion_owner.FORMAL_DECISION_SCHEMA
_2VS_REVIEW_UNIT_ID = two_vs_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_2VS_EVENT_IDS = two_vs_ingestion_owner.EXPECTED_EVENT_IDS

_2VS_EVENT_COUNT = 8
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8)
TWO_VS_TRANSITION_ADAPTER_CREATED = False


class CompletedDecisionReconciliationWith2VSError(ValueError):
    """Raised when the exact 2VS reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWith2VSError(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _project_validated_2vs_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only completed-decision fields from owner-validated 2VS data."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "2VS_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _2VS_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": _2VS_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _2VS_FORMAL_DECISION_SHA256,
        "schema_version": _2VS_FORMAL_DECISION_SCHEMA,
        "review_unit_id": _2VS_REVIEW_UNIT_ID,
        "verification_status": "MATCHED",
    }
    if any(
        binding_value.get(key) != value
        for key, value in expected_binding.items()
    ):
        _fail("2VS_FORMAL_DECISION_BINDING_INVALID")

    normalized = _require_mapping(
        bound.get("normalized"), "2VS_NORMALIZED_DECISION_NOT_OBJECT"
    )
    events = _require_list(
        normalized.get("events"), "2VS_NORMALIZED_EVENTS_NOT_LIST"
    )
    if len(events) != _2VS_EVENT_COUNT:
        _fail("2VS_NORMALIZED_EVENT_COUNT_NOT_EXACT8")

    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    for value in events:
        event = _require_mapping(value, "2VS_NORMALIZED_EVENT_NOT_OBJECT")
        event_id = event.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("2VS_NORMALIZED_EVENT_ID_INVALID")
        observed_ids.append(event_id)
        if (
            event.get("decision_finalized") is not True
            or event.get("D1_human_task_relevance_decision")
            != generic.TASK_RELEVANT
            or event.get("D2_human_chemistry_support_disposition")
            != generic.CHEMISTRY_POSITIVE
            or event.get("D5_human_training_use_disposition")
            != generic.TRAINING_EXCLUDE
            or event.get("human_training_excluded") is not True
            or event.get("training_admitted") is not False
        ):
            _fail("2VS_NORMALIZED_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_2VS_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=(
                    generic.COMPLETED_HUMAN_POSITIVE
                ),
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_EXCLUDE,
                human_training_excluded=True,
                source_decision_schema=_2VS_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_2VS_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _2VS_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _2VS_EVENT_COUNT:
        _fail("2VS_NORMALIZED_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _2VS_EVENT_IDS:
        _fail("2VS_NORMALIZED_EVENT_COVERAGE_NOT_EXACT8")

    binding = generic.SourceBinding(
        source_path=(
            _2VS_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=_2VS_FORMAL_DECISION_BYTE_COUNT,
        sha256=_2VS_FORMAL_DECISION_SHA256,
        schema_version=_2VS_FORMAL_DECISION_SCHEMA,
        review_unit_id=_2VS_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_2vs_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the 2VS ingestion owner and project its validated Exact8."""

    try:
        bound = two_vs_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except two_vs_ingestion_owner.TwoVSIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith2VSError(
            "2VS_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_2vs_binding_v1(bound)


def _prove_2vs_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the frozen original 2VS unit meets generic preconditions."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWith2VSError(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_2VS_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _2VS_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("2VS_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _2VS_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("2VS_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _2VS_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("2VS_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT8")
    two_vs_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if any(row["raw_review_unit_id"] != _2VS_REVIEW_UNIT_ID for row in two_vs_rows):
        _fail("2VS_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in two_vs_rows
    ):
        _fail("2VS_PRIOR_STATE_NOT_EXACT8_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_2vs_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove reuse of the ONL owner did not normalize any 2VS field."""

    expected_ids = set(_2VS_EVENT_IDS)
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
        _fail("2VS_ORIGINAL_EVENT_SET_NOT_EXACT8")
    if set(adapted_by_event) != expected_ids:
        _fail("2VS_ADAPTED_EVENT_SET_NOT_EXACT8")
    changed = [
        event_id
        for event_id in _2VS_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_2VS_ROW:" + changed[0])


def load_real_completed_decision_sources_with_2vs_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load frozen FFQ, POA, G3H, ONL, PRF, and 2VS completed decisions."""

    existing = prf_successor.load_real_completed_decision_sources_with_prf_v1(
        repo_root
    )
    if len(existing) != 5 or tuple(len(source.facts) for source in existing) != (
        _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_PRF_SOURCE_COMPOSITION_INVALID")
    source = project_2vs_completed_decision_v1(repo_root=repo_root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding.review_unit_id != _2VS_REVIEW_UNIT_ID
        or any(fact.review_unit_id != _2VS_REVIEW_UNIT_ID for fact in source.facts)
    ):
        _fail("2VS_SOURCE_REVIEW_UNIT_MISMATCH")
    sources = (*existing, source)
    if len(sources) != 6:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT6")
    if len({item.binding.review_unit_id for item in sources}) != 6:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT6")
    if len({item.binding.stable_identity for item in sources}) != 6:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT6")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 57:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_57")
    if len(set(event_ids)) != 57:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_2vs_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact6 sources through the generic owner, entirely in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_2vs_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_2vs_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_2vs_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
