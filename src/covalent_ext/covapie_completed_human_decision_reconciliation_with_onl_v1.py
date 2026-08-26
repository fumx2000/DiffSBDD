"""Reconcile frozen ONL completion through the unchanged generic owner.

ONL Exact9 is different from the earlier completed-decision sources: its
historical prior state is ``CURRENTLY_IN_PROGRESS``.  This additive successor
first proves that exact frozen transition, normalizes only a private in-memory
copy to the generic precondition, and then delegates all reconciliation work
to the unchanged generic predecessor.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_g3h_v1 as g3h_successor,
)
from . import (
    covapie_onl_completed_decision_ingestion_and_task_label_availability_v1
    as onl_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithONLError",
    "project_onl_completed_decision_v1",
    "load_real_completed_decision_sources_with_onl_v1",
    "reconcile_real_completed_human_decisions_with_onl_v1",
)


_ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    onl_ingestion_owner.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
_ONL_FORMAL_DECISION_BYTE_COUNT = onl_ingestion_owner.FORMAL_DECISION_BYTE_COUNT
_ONL_FORMAL_DECISION_SHA256 = onl_ingestion_owner.FORMAL_DECISION_SHA256
_ONL_FORMAL_DECISION_SCHEMA = onl_ingestion_owner.FORMAL_DECISION_SCHEMA
_ONL_REVIEW_UNIT_ID = onl_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_ONL_EVENT_IDS = onl_ingestion_owner.EXPECTED_EVENT_IDS

_HISTORICAL_EVENT_COUNT = 338
_HISTORICAL_REVIEW_UNIT_COUNT = 131
_ONL_EVENT_COUNT = 9
_ALLOWED_TRANSITION_FIELDS = frozenset(
    (
        "current_review_status",
        "calibration_eligible",
        "calibration_exclusion_reason",
    )
)


class CompletedDecisionReconciliationWithONLError(ValueError):
    """Raised when the exact ONL completion transition cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithONLError(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _project_validated_onl_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only completed-decision fields from owner-validated ONL data."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "ONL_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": _ONL_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _ONL_FORMAL_DECISION_SHA256,
        "schema_version": _ONL_FORMAL_DECISION_SCHEMA,
        "review_unit_id": _ONL_REVIEW_UNIT_ID,
        "verification_status": "MATCHED",
    }
    if any(binding_value.get(key) != value for key, value in expected_binding.items()):
        _fail("ONL_FORMAL_DECISION_BINDING_INVALID")

    normalized = _require_mapping(
        bound.get("normalized"), "ONL_NORMALIZED_DECISION_NOT_OBJECT"
    )
    events = _require_list(
        normalized.get("events"), "ONL_NORMALIZED_EVENTS_NOT_LIST"
    )
    if len(events) != _ONL_EVENT_COUNT:
        _fail("ONL_NORMALIZED_EVENT_COUNT_NOT_EXACT9")

    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    for value in events:
        event = _require_mapping(value, "ONL_NORMALIZED_EVENT_NOT_OBJECT")
        event_id = event.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("ONL_NORMALIZED_EVENT_ID_INVALID")
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
            _fail("ONL_NORMALIZED_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_ONL_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=(
                    generic.COMPLETED_HUMAN_POSITIVE
                ),
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_EXCLUDE,
                human_training_excluded=True,
                source_decision_schema=_ONL_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_ONL_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _ONL_EVENT_COUNT:
        _fail("ONL_NORMALIZED_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _ONL_EVENT_IDS:
        _fail("ONL_NORMALIZED_EVENT_COVERAGE_NOT_EXACT9")

    binding = generic.SourceBinding(
        source_path=_ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_ONL_FORMAL_DECISION_BYTE_COUNT,
        sha256=_ONL_FORMAL_DECISION_SHA256,
        schema_version=_ONL_FORMAL_DECISION_SCHEMA,
        review_unit_id=_ONL_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_onl_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the ONL ingestion owner and project its validated Exact9."""

    try:
        bound = onl_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except onl_ingestion_owner.ONLIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithONLError(
            "ONL_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_onl_binding_v1(bound)


def _adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    """Normalize only proven ONL Exact9 prior state on a private deep copy.

    The generic invariant remains unchanged: every source it consumes must
    overlay a ``CURRENTLY_UNREVIEWED`` row.  ONL is admitted to that algorithm
    only after this successor proves that the entire frozen Exact9 unit is the
    historical population's complete ``CURRENTLY_IN_PROGRESS`` inventory and
    has a frozen finalized human decision.  The temporary state is neither an
    authority nor an artifact and can never appear in the returned overlay.
    """

    original_snapshot = deepcopy(historical_rows)
    working_values = deepcopy(historical_rows)
    if isinstance(working_values, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        working = list(working_values)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithONLError(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in working
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_ONL_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in working)
    missing = [event_id for event_id in _ONL_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("ONL_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _ONL_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("ONL_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    onl_unit_ids = {
        row["canonical_event_id"]
        for row in working
        if row["raw_review_unit_id"] == _ONL_REVIEW_UNIT_ID
    }
    if onl_unit_ids != expected_ids:
        _fail("ONL_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT9")
    onl_rows = [
        row for row in working if row["canonical_event_id"] in expected_ids
    ]
    if any(row["raw_review_unit_id"] != _ONL_REVIEW_UNIT_ID for row in onl_rows):
        _fail("ONL_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_IN_PROGRESS
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"]
        != generic.CURRENTLY_IN_PROGRESS
        for row in onl_rows
    ):
        _fail("ONL_PRIOR_STATE_NOT_EXACT9_IN_PROGRESS")

    if len(working) != _HISTORICAL_EVENT_COUNT:
        _fail("HISTORICAL_EVENT_COUNT_NOT_338")
    unit_ids = {row["raw_review_unit_id"] for row in working}
    if len(unit_ids) != _HISTORICAL_REVIEW_UNIT_COUNT:
        _fail("HISTORICAL_REVIEW_UNIT_COUNT_NOT_131")
    in_progress_rows = [
        row
        for row in working
        if row["current_review_status"] == generic.CURRENTLY_IN_PROGRESS
    ]
    if len(in_progress_rows) != _ONL_EVENT_COUNT:
        _fail("HISTORICAL_IN_PROGRESS_EVENT_COUNT_NOT_EXACT9")
    in_progress_units = {row["raw_review_unit_id"] for row in in_progress_rows}
    if len(in_progress_units) != 1:
        _fail("HISTORICAL_IN_PROGRESS_UNIT_COUNT_NOT_EXACT1")
    if (
        {row["canonical_event_id"] for row in in_progress_rows} != expected_ids
        or in_progress_units != {_ONL_REVIEW_UNIT_ID}
    ):
        _fail("HISTORICAL_IN_PROGRESS_INVENTORY_NOT_EXACT_ONL")

    validated = generic._validate_historical_rows(working)
    adapted = [dict(row) for row in validated]
    for row in adapted:
        if row["canonical_event_id"] not in expected_ids:
            continue
        row["current_review_status"] = generic.CURRENTLY_UNREVIEWED
        row["calibration_eligible"] = "true"
        row["calibration_exclusion_reason"] = ""

    for before, after in zip(validated, adapted, strict=True):
        event_id = before["canonical_event_id"]
        changed = {key for key in before if before[key] != after[key]}
        if event_id not in expected_ids:
            if changed:
                _fail("ADAPTER_CHANGED_NON_ONL_ROW:" + event_id)
            continue
        if changed != _ALLOWED_TRANSITION_FIELDS:
            _fail("ADAPTER_CHANGED_ONL_FIELD_BOUNDARY:" + event_id)
        if (
            after["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or after["calibration_eligible"] != "true"
            or after["calibration_exclusion_reason"] != ""
        ):
            _fail("ADAPTER_ONL_NORMALIZATION_INVALID:" + event_id)

    if historical_rows != original_snapshot:
        _fail("ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    generic._validate_historical_rows(adapted)
    return tuple(adapted)


def load_real_completed_decision_sources_with_onl_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load frozen FFQ, POA, G3H, and ONL completed-decision sources."""

    sources = (
        *g3h_successor.load_real_completed_decision_sources_with_g3h_v1(
            repo_root
        ),
        project_onl_completed_decision_v1(repo_root=repo_root),
    )
    if len(sources) != 4:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT4")
    if len({source.binding.review_unit_id for source in sources}) != 4:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT4")
    if len({source.binding.stable_identity for source in sources}) != 4:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT4")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 41:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_41")
    if len(set(event_ids)) != 41:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_onl_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact4 sources through the generic owner, entirely in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    adapted_historical = (
        _adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    sources = load_real_completed_decision_sources_with_onl_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
