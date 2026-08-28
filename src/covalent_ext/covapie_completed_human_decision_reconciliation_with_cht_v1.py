"""Reconcile frozen CHT completion through the unchanged generic owner.

CHT Exact5 already has the generic owner's required historical prior state,
``CURRENTLY_UNREVIEWED``.  This metadata-only successor projects the
owner-validated CHT decision, reuses the published NEQ source chain and ONL
transition owner, proves that transition leaves CHT untouched, and delegates
the final in-memory overlay to the generic reconciler.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_neq_v1 as neq_successor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from . import (
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v1
    as cht_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithCHTError",
    "project_cht_completed_decision_v1",
    "load_real_completed_decision_sources_with_cht_v1",
    "reconcile_real_completed_human_decisions_with_cht_v1",
)


_CHT_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    cht_ingestion_owner.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
_CHT_FORMAL_DECISION_BYTE_COUNT = cht_ingestion_owner.FORMAL_DECISION_BYTE_COUNT
_CHT_FORMAL_DECISION_SHA256 = cht_ingestion_owner.FORMAL_DECISION_SHA256
_CHT_FORMAL_DECISION_SCHEMA = cht_ingestion_owner.FORMAL_DECISION_SCHEMA
_CHT_REVIEW_UNIT_ID = cht_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_CHT_APPROVED_AT_UTC = cht_ingestion_owner.EXPECTED_APPROVED_AT_UTC
_CHT_EVENT_IDS = cht_ingestion_owner.EXPECTED_EVENT_IDS
_CHT_RANKS = cht_ingestion_owner.EXPECTED_RANKS

_CHT_EVENT_COUNT = 5
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6)
_EXPECTED_PDB_COUNTS = {"4V3F": 3, "5A2D": 2}
_EXPECTED_CYS_RESIDUE_ID = "CYS:450-"
CHT_TRANSITION_ADAPTER_CREATED = False


class CompletedDecisionReconciliationWithCHTError(ValueError):
    """Raised when the exact CHT reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithCHTError(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _project_validated_cht_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only completed-decision fields from owner-validated CHT data."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "CHT_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _CHT_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": _CHT_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _CHT_FORMAL_DECISION_SHA256,
        "schema_version": _CHT_FORMAL_DECISION_SCHEMA,
        "review_unit_id": _CHT_REVIEW_UNIT_ID,
        "approved_at_utc": _CHT_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }
    if any(
        binding_value.get(key) != value
        for key, value in expected_binding.items()
    ):
        _fail("CHT_FORMAL_DECISION_BINDING_INVALID")

    normalized = _require_mapping(
        bound.get("normalized"), "CHT_NORMALIZED_DECISION_NOT_OBJECT"
    )
    events = _require_list(
        normalized.get("events"), "CHT_NORMALIZED_EVENTS_NOT_LIST"
    )
    if len(events) != _CHT_EVENT_COUNT:
        _fail("CHT_NORMALIZED_EVENT_COUNT_NOT_EXACT5")

    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    pdb_counts: Counter[str] = Counter()
    for value in events:
        event = _require_mapping(value, "CHT_NORMALIZED_EVENT_NOT_OBJECT")
        event_id = event.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("CHT_NORMALIZED_EVENT_ID_INVALID")
        observed_ids.append(event_id)
        rank = event.get("scaleup_rank")
        if type(rank) is not int:
            _fail("CHT_NORMALIZED_RANK_INVALID:" + event_id)
        observed_ranks.append(rank)
        pdb_id = event.get("pdb_id")
        if type(pdb_id) is not str:
            _fail("CHT_NORMALIZED_PDB_ID_INVALID:" + event_id)
        pdb_counts[pdb_id] += 1
        if event.get("cys_residue_id") != _EXPECTED_CYS_RESIDUE_ID:
            _fail("CHT_NORMALIZED_CYS_RESIDUE_ID_INVALID:" + event_id)
        if (
            event.get("task_relevant") is not True
            or event.get("chemistry_known_positive") is not True
            or event.get("formal_event_training_use_decision")
            != generic.TRAINING_EXCLUDE
            or event.get("human_training_excluded") is not True
            or event.get("training_admitted") is not False
        ):
            _fail("CHT_NORMALIZED_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_CHT_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=(
                    generic.COMPLETED_HUMAN_POSITIVE
                ),
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_EXCLUDE,
                human_training_excluded=True,
                source_decision_schema=_CHT_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_CHT_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _CHT_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _CHT_EVENT_COUNT:
        _fail("CHT_NORMALIZED_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _CHT_EVENT_IDS:
        _fail("CHT_NORMALIZED_EVENT_COVERAGE_NOT_EXACT5")
    if tuple(observed_ranks) != _CHT_RANKS:
        _fail("CHT_NORMALIZED_RANK_COVERAGE_NOT_EXACT5")
    if dict(pdb_counts) != _EXPECTED_PDB_COUNTS:
        _fail("CHT_PDB_CONTEXT_COUNTS_NOT_3_PLUS_2")

    inventory = _require_mapping(
        normalized.get("event_context_inventory"),
        "CHT_EVENT_CONTEXT_INVENTORY_NOT_OBJECT",
    )
    contexts = _require_list(
        inventory.get("contexts"), "CHT_EVENT_CONTEXTS_NOT_LIST"
    )
    if (
        inventory.get("distinct_event_context_count") != 5
        or inventory.get("distinct_cys_residue_identities")
        != [_EXPECTED_CYS_RESIDUE_ID]
        or inventory.get("distinct_cys_residue_identity_count") != 1
        or inventory.get("pdb_context_count") != 2
        or inventory.get("contexts_collapsed") is not False
        or len(contexts) != 5
        or tuple(context.get("canonical_event_id") for context in contexts)
        != _CHT_EVENT_IDS
    ):
        _fail("CHT_EVENT_CONTEXT_INVENTORY_INVALID")

    binding = generic.SourceBinding(
        source_path=(
            _CHT_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=_CHT_FORMAL_DECISION_BYTE_COUNT,
        sha256=_CHT_FORMAL_DECISION_SHA256,
        schema_version=_CHT_FORMAL_DECISION_SCHEMA,
        review_unit_id=_CHT_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_cht_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the CHT ingestion owner and project its validated Exact5."""

    try:
        bound = cht_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except cht_ingestion_owner.CHTIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithCHTError(
            "CHT_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_cht_binding_v1(bound)


def _prove_cht_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the frozen original CHT unit meets generic preconditions."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithCHTError(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_CHT_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _CHT_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("CHT_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _CHT_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("CHT_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _CHT_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("CHT_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT5")
    cht_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if any(row["raw_review_unit_id"] != _CHT_REVIEW_UNIT_ID for row in cht_rows):
        _fail("CHT_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in cht_rows
    ):
        _fail("CHT_PRIOR_STATE_NOT_EXACT5_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_cht_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove reuse of the ONL owner did not normalize any CHT field."""

    expected_ids = set(_CHT_EVENT_IDS)
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
        _fail("CHT_ORIGINAL_EVENT_SET_NOT_EXACT5")
    if set(adapted_by_event) != expected_ids:
        _fail("CHT_ADAPTED_EVENT_SET_NOT_EXACT5")
    changed = [
        event_id
        for event_id in _CHT_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_CHT_ROW:" + changed[0])


def load_real_completed_decision_sources_with_cht_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load FFQ, POA, G3H, ONL, PRF, 2VS, 1F8, YUN, NEQ, and CHT."""

    existing = neq_successor.load_real_completed_decision_sources_with_neq_v1(
        repo_root
    )
    if len(existing) != 9 or tuple(len(source.facts) for source in existing) != (
        _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_NEQ_SOURCE_COMPOSITION_INVALID")
    source = project_cht_completed_decision_v1(repo_root=repo_root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding.review_unit_id != _CHT_REVIEW_UNIT_ID
        or len(source.facts) != _CHT_EVENT_COUNT
        or any(fact.review_unit_id != _CHT_REVIEW_UNIT_ID for fact in source.facts)
    ):
        _fail("CHT_SOURCE_REVIEW_UNIT_OR_FACT_COUNT_MISMATCH")
    sources = (*existing, source)
    if len(sources) != 10:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT10")
    if len({item.binding.review_unit_id for item in sources}) != 10:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT10")
    if len({item.binding.stable_identity for item in sources}) != 10:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT10")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 83:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_83")
    if len(set(event_ids)) != 83:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_cht_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact10 sources through the generic owner, entirely in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_cht_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_cht_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_cht_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
