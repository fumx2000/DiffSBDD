"""Reconcile frozen OZJ completion through the unchanged generic owner.

OZJ Exact4 already has the generic owner's required historical prior state,
``CURRENTLY_UNREVIEWED``.  This metadata-only successor projects the
owner-validated OZJ decision, reuses the published CHT source chain and ONL
transition owner, proves that transition leaves OZJ untouched, and delegates
the final in-memory overlay to the generic reconciler.

Future-admission candidacy remains owned by the OZJ ingestion and census
projection lineage.  It is deliberately absent from the generic fact.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_cht_v1 as cht_successor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from . import (
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
    as ozj_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithOZJError",
    "project_ozj_completed_decision_v1",
    "load_real_completed_decision_sources_with_ozj_v1",
    "reconcile_real_completed_human_decisions_with_ozj_v1",
)


_OZJ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    ozj_ingestion_owner.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
_OZJ_FORMAL_DECISION_BYTE_COUNT = ozj_ingestion_owner.FORMAL_DECISION_BYTE_COUNT
_OZJ_FORMAL_DECISION_SHA256 = ozj_ingestion_owner.FORMAL_DECISION_SHA256
_OZJ_FORMAL_DECISION_SCHEMA = ozj_ingestion_owner.FORMAL_DECISION_SCHEMA
_OZJ_REVIEW_UNIT_ID = ozj_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_OZJ_APPROVED_AT_UTC = ozj_ingestion_owner.EXPECTED_APPROVED_AT_UTC
_OZJ_EVENT_IDS = ozj_ingestion_owner.EXPECTED_EVENT_IDS
_OZJ_RANKS = ozj_ingestion_owner.EXPECTED_RANKS

_OZJ_EVENT_COUNT = 4
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5)
_EXPECTED_PDB_COUNTS = {"4CL8": 4}
_EXPECTED_CYS_RESIDUE_ID = "CYS:168-"
_EXPECTED_CONTEXTS = (
    (_OZJ_EVENT_IDS[0], "4CL8", "A", "E"),
    (_OZJ_EVENT_IDS[1], "4CL8", "B", "I"),
    (_OZJ_EVENT_IDS[2], "4CL8", "C", "L"),
    (_OZJ_EVENT_IDS[3], "4CL8", "D", "O"),
)
OZJ_TRANSITION_ADAPTER_CREATED = False


class CompletedDecisionReconciliationWithOZJError(ValueError):
    """Raised when the exact OZJ reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithOZJError(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _project_validated_ozj_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only completed-decision fields from owner-validated OZJ data."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "OZJ_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _OZJ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": _OZJ_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _OZJ_FORMAL_DECISION_SHA256,
        "schema_version": _OZJ_FORMAL_DECISION_SCHEMA,
        "review_unit_id": _OZJ_REVIEW_UNIT_ID,
        "approved_at_utc": _OZJ_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }
    if any(
        binding_value.get(key) != value
        for key, value in expected_binding.items()
    ):
        _fail("OZJ_FORMAL_DECISION_BINDING_INVALID")

    normalized = _require_mapping(
        bound.get("normalized"), "OZJ_NORMALIZED_DECISION_NOT_OBJECT"
    )
    events = _require_list(
        normalized.get("events"), "OZJ_NORMALIZED_EVENTS_NOT_LIST"
    )
    if len(events) != _OZJ_EVENT_COUNT:
        _fail("OZJ_NORMALIZED_EVENT_COUNT_NOT_EXACT4")

    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    observed_contexts: list[tuple[str, str, str, str]] = []
    pdb_counts: Counter[str] = Counter()
    for value in events:
        event = _require_mapping(value, "OZJ_NORMALIZED_EVENT_NOT_OBJECT")
        event_id = event.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("OZJ_NORMALIZED_EVENT_ID_INVALID")
        observed_ids.append(event_id)
        rank = event.get("scaleup_rank")
        if type(rank) is not int:
            _fail("OZJ_NORMALIZED_RANK_INVALID:" + event_id)
        observed_ranks.append(rank)
        pdb_id = event.get("pdb_id")
        if type(pdb_id) is not str:
            _fail("OZJ_NORMALIZED_PDB_ID_INVALID:" + event_id)
        pdb_counts[pdb_id] += 1
        protein_chain = event.get("protein_chain_or_asym")
        ligand_chain = event.get("ligand_chain_or_asym")
        if type(protein_chain) is not str or type(ligand_chain) is not str:
            _fail("OZJ_NORMALIZED_EVENT_CONTEXT_INVALID:" + event_id)
        observed_contexts.append(
            (event_id, pdb_id, protein_chain, ligand_chain)
        )
        if event.get("cys_residue_id") != _EXPECTED_CYS_RESIDUE_ID:
            _fail("OZJ_NORMALIZED_CYS_RESIDUE_ID_INVALID:" + event_id)
        if (
            event.get("task_relevant") is not True
            or event.get("chemistry_known_positive") is not True
            or event.get("formal_event_training_use_decision")
            != generic.TRAINING_INCLUDE
            or event.get("human_training_excluded") is not False
        ):
            _fail("OZJ_NORMALIZED_EVENT_DECISION_INVALID:" + event_id)
        if (
            event.get("candidate_for_future_training_admission") is not True
            or event.get("future_training_admission_status")
            != ozj_ingestion_owner.FUTURE_STATUS
            or event.get("future_training_candidate_is_training_admission")
            is not False
            or event.get("training_admitted") is not False
        ):
            _fail("OZJ_NORMALIZED_FUTURE_ADMISSION_BOUNDARY_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_OZJ_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=(
                    generic.COMPLETED_HUMAN_POSITIVE
                ),
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_INCLUDE,
                human_training_excluded=False,
                source_decision_schema=_OZJ_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_OZJ_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _OZJ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _OZJ_EVENT_COUNT:
        _fail("OZJ_NORMALIZED_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _OZJ_EVENT_IDS:
        _fail("OZJ_NORMALIZED_EVENT_COVERAGE_NOT_EXACT4")
    if tuple(observed_ranks) != _OZJ_RANKS:
        _fail("OZJ_NORMALIZED_RANK_COVERAGE_NOT_EXACT4")
    if dict(pdb_counts) != _EXPECTED_PDB_COUNTS:
        _fail("OZJ_PDB_CONTEXT_COUNTS_NOT_EXACT4_4CL8")
    if tuple(observed_contexts) != _EXPECTED_CONTEXTS:
        _fail("OZJ_DISTINCT_EVENT_CONTEXTS_NOT_EXACT4")

    inventory = _require_list(
        normalized.get("event_context_inventory"),
        "OZJ_EVENT_CONTEXT_INVENTORY_NOT_LIST",
    )
    inventory_contexts = tuple(
        (
            context.get("canonical_event_id"),
            context.get("pdb_id"),
            context.get("protein_asym"),
            context.get("ligand_asym"),
        )
        if type(context) is dict
        else (None, None, None, None)
        for context in inventory
    )
    if (
        len(inventory) != _OZJ_EVENT_COUNT
        or inventory_contexts != _EXPECTED_CONTEXTS
        or any(
            type(context) is not dict
            or context.get("cys_residue_id") != _EXPECTED_CYS_RESIDUE_ID
            for context in inventory
        )
    ):
        _fail("OZJ_EVENT_CONTEXT_INVENTORY_INVALID")

    binding = generic.SourceBinding(
        source_path=(
            _OZJ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=_OZJ_FORMAL_DECISION_BYTE_COUNT,
        sha256=_OZJ_FORMAL_DECISION_SHA256,
        schema_version=_OZJ_FORMAL_DECISION_SCHEMA,
        review_unit_id=_OZJ_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_ozj_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the OZJ ingestion owner and project its validated Exact4."""

    try:
        bound = ozj_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except ozj_ingestion_owner.OZJIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithOZJError(
            "OZJ_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_ozj_binding_v1(bound)


def _prove_ozj_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the frozen original OZJ unit meets generic preconditions."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithOZJError(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_OZJ_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _OZJ_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("OZJ_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _OZJ_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("OZJ_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _OZJ_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("OZJ_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4")
    ozj_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if any(row["raw_review_unit_id"] != _OZJ_REVIEW_UNIT_ID for row in ozj_rows):
        _fail("OZJ_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in ozj_rows
    ):
        _fail("OZJ_PRIOR_STATE_NOT_EXACT4_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_ozj_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove reuse of the ONL owner did not normalize any OZJ field."""

    expected_ids = set(_OZJ_EVENT_IDS)
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
        _fail("OZJ_ORIGINAL_EVENT_SET_NOT_EXACT4")
    if set(adapted_by_event) != expected_ids:
        _fail("OZJ_ADAPTED_EVENT_SET_NOT_EXACT4")
    changed = [
        event_id
        for event_id in _OZJ_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_OZJ_ROW:" + changed[0])


def load_real_completed_decision_sources_with_ozj_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load FFQ, POA, G3H, ONL, PRF, 2VS, 1F8, YUN, NEQ, CHT, and OZJ."""

    existing = cht_successor.load_real_completed_decision_sources_with_cht_v1(
        repo_root
    )
    if len(existing) != 10 or tuple(len(source.facts) for source in existing) != (
        _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_CHT_SOURCE_COMPOSITION_INVALID")
    source = project_ozj_completed_decision_v1(repo_root=repo_root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding
        != generic.SourceBinding(
            source_path=(
                _OZJ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
            ),
            path_namespace="repository_parent_relative",
            byte_count=_OZJ_FORMAL_DECISION_BYTE_COUNT,
            sha256=_OZJ_FORMAL_DECISION_SHA256,
            schema_version=_OZJ_FORMAL_DECISION_SCHEMA,
            review_unit_id=_OZJ_REVIEW_UNIT_ID,
        )
        or len(source.facts) != _OZJ_EVENT_COUNT
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_OZJ_EVENT_IDS))
        or any(
            type(fact) is not generic.NormalizedCompletedDecisionFact
            or fact.review_unit_id != _OZJ_REVIEW_UNIT_ID
            or fact.human_review_completed is not True
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            or fact.source_decision_schema != _OZJ_FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _OZJ_FORMAL_DECISION_SHA256
            or fact.source_binding_path != source.binding.source_path
            for fact in source.facts
        )
    ):
        _fail("OZJ_SOURCE_PROJECTION_INVALID")
    sources = (*existing, source)
    if len(sources) != 11:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT11")
    if len({item.binding.review_unit_id for item in sources}) != 11:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT11")
    if len({item.binding.stable_identity for item in sources}) != 11:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT11")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 87:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_87")
    if len(set(event_ids)) != 87:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_ozj_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact11 sources through the generic owner, entirely in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_ozj_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_ozj_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_ozj_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
