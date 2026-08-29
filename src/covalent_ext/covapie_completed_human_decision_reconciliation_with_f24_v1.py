"""Reconcile frozen F24 completion through the unchanged generic owner.

F24 Exact4 already has the generic owner's required historical prior state,
``CURRENTLY_UNREVIEWED``.  This metadata-only successor validates the rich
F24 authority through its published ingestion owner, projects only the
generic completed-decision fact, reuses the published OZJ source chain and
ONL transition owner, and delegates one in-memory reconciliation.

Chemical/role detail and future-admission candidacy remain owned by the F24
ingestion and census lineage.  They are validated here but deliberately not
copied into the generic fact.
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
    covapie_completed_human_decision_reconciliation_with_ozj_v1 as ozj_successor,
)
from . import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1
    as f24_ingestion_owner,
)


__all__ = (
    "CompletedDecisionReconciliationWithF24Error",
    "project_f24_completed_decision_v1",
    "load_real_completed_decision_sources_with_f24_v1",
    "reconcile_real_completed_human_decisions_with_f24_v1",
)


_F24_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    f24_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_F24_FORMAL_DECISION_BYTE_COUNT = f24_ingestion_owner.FORMAL_BINDINGS[0][2]
_F24_FORMAL_DECISION_SHA256 = f24_ingestion_owner.FORMAL_BINDINGS[0][3]
_F24_FORMAL_DECISION_SCHEMA = f24_ingestion_owner.FORMAL_DECISION_SCHEMA
_F24_REVIEW_UNIT_ID = f24_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_F24_APPROVED_AT_UTC = f24_ingestion_owner.EXPECTED_APPROVED_AT_UTC
_F24_EVENT_IDS = f24_ingestion_owner.EXPECTED_EVENT_IDS
_F24_RANKS = f24_ingestion_owner.EXPECTED_RANKS

_F24_EVENT_COUNT = 4
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4)
_EXPECTED_PDB_COUNTS = {"3V4X": 4}
_EXPECTED_CYS_RESIDUE_ID = "CYS:111-"
_EXPECTED_CONTEXTS = (
    (_F24_EVENT_IDS[0], "3V4X", "A", "E"),
    (_F24_EVENT_IDS[1], "3V4X", "B", "F"),
    (_F24_EVENT_IDS[2], "3V4X", "C", "G"),
    (_F24_EVENT_IDS[3], "3V4X", "D", "H"),
)
_EXPECTED_APPROVAL_DECISIONS = {
    "D1_task_relevance": "RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_partition": "REVISE_ROLE_PARTITION",
    "D5_training_use": "INCLUDE",
}
_EXPECTED_APPLICABLE_TASKS = (
    (0, "warhead_only", "A"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
F24_TRANSITION_ADAPTER_CREATED = False


class CompletedDecisionReconciliationWithF24Error(ValueError):
    """Raised when the exact F24 reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithF24Error(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _validate_rich_f24_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Prove rich owner-validated F24 semantics before narrow projection."""

    formal = _require_mapping(bound.get("formal"), "F24_FORMAL_DECISION_NOT_OBJECT")
    if (
        formal.get("schema_version") != _F24_FORMAL_DECISION_SCHEMA
        or formal.get("human_review_completed") is not True
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
    ):
        _fail("F24_FORMAL_COMPLETION_INVALID")

    approval = _require_mapping(
        formal.get("human_approval"), "F24_HUMAN_APPROVAL_NOT_OBJECT"
    )
    if any(approval.get(key) != value for key, value in _EXPECTED_APPROVAL_DECISIONS.items()):
        _fail("F24_D1_D5_DECISIONS_INVALID")
    if (
        approval.get("approved_at_utc") != _F24_APPROVED_AT_UTC
        or approval.get("human_selected_role_candidate_index_0based") is not None
        or approval.get("machine_auto_selection_performed") is not False
        or approval.get("machine_recommended_candidate") is not None
    ):
        _fail("F24_APPROVAL_OR_SELECTED_CANDIDATE_INVALID")

    identity = _require_mapping(formal.get("identity"), "F24_IDENTITY_NOT_OBJECT")
    if (
        identity.get("review_unit_id") != _F24_REVIEW_UNIT_ID
        or identity.get("canonical_event_ids") != list(_F24_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_F24_RANKS)
        or identity.get("exact_event_count") != _F24_EVENT_COUNT
        or identity.get("unique_event_count") != _F24_EVENT_COUNT
        or identity.get("duplicate_event_count") != 0
        or identity.get("omitted_event_count") != 0
        or identity.get("extra_event_count") != 0
        or identity.get("event_contexts_collapsed") is not False
        or identity.get("pdb_event_counts") != _EXPECTED_PDB_COUNTS
    ):
        _fail("F24_FORMAL_IDENTITY_NOT_EXACT4")

    role = _require_mapping(
        formal.get("selected_role_partition"), "F24_ROLE_PARTITION_NOT_OBJECT"
    )
    boundary = _require_mapping(
        role.get("direct_scaffold_warhead_boundary"),
        "F24_ROLE_BOUNDARY_NOT_OBJECT",
    )
    if (
        role.get("D4_human_choice") != "REVISE_ROLE_PARTITION"
        or role.get("selected_candidate_index_0based") is not None
        or role.get("human_selected_machine_candidate_index_0based") is not None
        or role.get("machine_candidate_selected") is not False
        or role.get("role_profile")
        != f24_ingestion_owner.EXPECTED_ROLE_PROFILE
        or role.get("warhead_role_atom_ids")
        != list(f24_ingestion_owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("partition_disjoint") is not True
        or boundary
        != {
            "bond_order": "SING",
            "boundary_valid": True,
            "scaffold_atom_id": "C5",
            "warhead_atom_id": "C2",
        }
    ):
        _fail("F24_REVISED_ROLE_PARTITION_INVALID")

    chemical = _require_mapping(
        formal.get("chemical_warhead_annotation"),
        "F24_CHEMICAL_WARHEAD_NOT_OBJECT",
    )
    distinction = _require_mapping(
        formal.get("chemical_warhead_vs_role_region_distinction"),
        "F24_CHEMICAL_ROLE_DISTINCTION_NOT_OBJECT",
    )
    if (
        chemical.get("chemical_warhead_atom_ids")
        != list(f24_ingestion_owner.CHEMICAL_WARHEAD)
        or chemical.get("human_authoritative") is not True
        or distinction.get("chemical_warhead_atom_ids")
        != list(f24_ingestion_owner.CHEMICAL_WARHEAD)
        or distinction.get("warhead_role_atom_ids")
        != list(f24_ingestion_owner.WARHEAD_ROLE)
        or distinction.get("sets_are_intentionally_distinct") is not True
        or set(f24_ingestion_owner.CHEMICAL_WARHEAD)
        == set(f24_ingestion_owner.WARHEAD_ROLE)
    ):
        _fail("F24_CHEMICAL_WARHEAD_ROLE_DISTINCTION_INVALID")

    canonical = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "F24_CANONICAL_TASK_CONTRACT_NOT_OBJECT",
    )
    tasks = _require_list(canonical.get("tasks"), "F24_CANONICAL_TASKS_NOT_LIST")
    applicable = tuple(
        (task.get("task_id"), task.get("semantic_name"), task.get("display_alias"))
        for task in tasks
        if type(task) is dict and task.get("structurally_applicable_to_F24") is True
    )
    if (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 3, 4]
        or applicable != _EXPECTED_APPLICABLE_TASKS
    ):
        _fail("F24_CANONICAL_TASK_APPLICABILITY_INVALID")

    training = _require_mapping(
        formal.get("training_use_human_decision"),
        "F24_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    if (
        training.get("D5_human_choice") != "INCLUDE"
        or training.get("human_training_excluded") is not False
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed_now") is not False
        or training.get("READY_FOR_TRAINING") is not False
    ):
        _fail("F24_TRAINING_DISPOSITION_OR_ADMISSION_BOUNDARY_INVALID")

    derived_training = f24_ingestion_owner._training_boundary()
    if (
        derived_training.get("candidate_for_future_training_admission") is not True
        or derived_training.get("future_training_candidate_derived_by_ingestion")
        is not True
        or derived_training.get("future_training_candidate_is_training_admission")
        is not False
        or derived_training.get("training_admitted") is not False
    ):
        _fail("F24_INGESTION_DERIVED_FUTURE_CANDIDACY_INVALID")

    events = _require_list(
        formal.get("event_level_human_decisions"),
        "F24_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _F24_EVENT_COUNT:
        _fail("F24_FORMAL_EVENT_COUNT_NOT_EXACT4")
    return tuple(
        _require_mapping(event, "F24_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )


def _project_validated_f24_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic completed-decision fields from validated F24."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "F24_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _F24_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": _F24_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _F24_FORMAL_DECISION_SHA256,
        "sha256_scope": "file_bytes",
        "source_role": "F24_FROZEN_FORMAL_HUMAN_DECISION",
        "mode": "0664",
    }
    if dict(binding_value) != expected_binding:
        _fail("F24_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_f24_semantics_v1(bound)
    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    observed_contexts: list[tuple[str, str, str, str]] = []
    pdb_counts: Counter[str] = Counter()
    for event in events:
        event_id = event.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("F24_FORMAL_EVENT_ID_INVALID")
        observed_ids.append(event_id)
        rank = event.get("scaleup_rank")
        if type(rank) is not int:
            _fail("F24_FORMAL_RANK_INVALID:" + event_id)
        observed_ranks.append(rank)
        pdb_id = event.get("pdb_id")
        protein_asym = event.get("protein_asym")
        ligand_asym = event.get("ligand_asym")
        if not all(type(value) is str for value in (pdb_id, protein_asym, ligand_asym)):
            _fail("F24_FORMAL_EVENT_CONTEXT_INVALID:" + event_id)
        pdb_counts[pdb_id] += 1  # type: ignore[index]
        observed_contexts.append((event_id, pdb_id, protein_asym, ligand_asym))  # type: ignore[arg-type]
        if (
            event.get("protein_residue") != _EXPECTED_CYS_RESIDUE_ID
            or event.get("protein_reactive_atom") != "SG"
            or event.get("ligand_component_id") != "F24"
            or event.get("ligand_reactive_atom") != "C8"
        ):
            _fail("F24_FORMAL_EVENT_COVALENT_IDENTITY_INVALID:" + event_id)
        if (
            event.get("D1_task_relevance") != "RELEVANT"
            or event.get("D2_chemistry") != "POSITIVE"
            or event.get("D3_reactive_pair") != "CONFIRM_OBSERVED_PAIR"
            or event.get("D4_role_partition") != "REVISE_ROLE_PARTITION"
            or event.get("D5_training_use") != "INCLUDE"
            or event.get("formal_training_admitted") is not False
        ):
            _fail("F24_FORMAL_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_F24_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_INCLUDE,
                human_training_excluded=False,
                source_decision_schema=_F24_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_F24_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _F24_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _F24_EVENT_COUNT:
        _fail("F24_FORMAL_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _F24_EVENT_IDS:
        _fail("F24_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    if tuple(observed_ranks) != _F24_RANKS:
        _fail("F24_FORMAL_RANK_COVERAGE_NOT_EXACT4")
    if dict(pdb_counts) != _EXPECTED_PDB_COUNTS:
        _fail("F24_PDB_CONTEXT_COUNTS_NOT_EXACT4_3V4X")
    if tuple(observed_contexts) != _EXPECTED_CONTEXTS:
        _fail("F24_DISTINCT_EVENT_CONTEXTS_NOT_EXACT4")

    binding = generic.SourceBinding(
        source_path=_F24_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_F24_FORMAL_DECISION_BYTE_COUNT,
        sha256=_F24_FORMAL_DECISION_SHA256,
        schema_version=_F24_FORMAL_DECISION_SCHEMA,
        review_unit_id=_F24_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_f24_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the F24 ingestion owner and project its validated Exact4."""

    try:
        bound = f24_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except f24_ingestion_owner.F24IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithF24Error(
            "F24_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_f24_binding_v1(bound)


def _prove_f24_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the frozen original F24 unit meets generic preconditions."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithF24Error(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_F24_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _F24_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("F24_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _F24_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("F24_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _F24_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("F24_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4")
    f24_rows = [row for row in rows if row["canonical_event_id"] in expected_ids]
    if any(row["raw_review_unit_id"] != _F24_REVIEW_UNIT_ID for row in f24_rows):
        _fail("F24_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in f24_rows
    ):
        _fail("F24_PRIOR_STATE_NOT_EXACT4_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_f24_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove reuse of the ONL owner did not normalize any F24 field."""

    expected_ids = set(_F24_EVENT_IDS)
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
        _fail("F24_ORIGINAL_EVENT_SET_NOT_EXACT4")
    if set(adapted_by_event) != expected_ids:
        _fail("F24_ADAPTED_EVENT_SET_NOT_EXACT4")
    changed = [
        event_id
        for event_id in _F24_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_F24_ROW:" + changed[0])


def load_real_completed_decision_sources_with_f24_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published Exact11 predecessor sources and append F24."""

    existing = ozj_successor.load_real_completed_decision_sources_with_ozj_v1(
        repo_root
    )
    if len(existing) != 11 or tuple(len(source.facts) for source in existing) != (
        _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_OZJ_SOURCE_COMPOSITION_INVALID")
    source = project_f24_completed_decision_v1(repo_root=repo_root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding
        != generic.SourceBinding(
            source_path=(
                _F24_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
            ),
            path_namespace="repository_parent_relative",
            byte_count=_F24_FORMAL_DECISION_BYTE_COUNT,
            sha256=_F24_FORMAL_DECISION_SHA256,
            schema_version=_F24_FORMAL_DECISION_SCHEMA,
            review_unit_id=_F24_REVIEW_UNIT_ID,
        )
        or len(source.facts) != _F24_EVENT_COUNT
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_F24_EVENT_IDS))
        or any(
            type(fact) is not generic.NormalizedCompletedDecisionFact
            or fact.review_unit_id != _F24_REVIEW_UNIT_ID
            or fact.human_review_completed is not True
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            or fact.source_decision_schema != _F24_FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _F24_FORMAL_DECISION_SHA256
            or fact.source_binding_path != source.binding.source_path
            for fact in source.facts
        )
    ):
        _fail("F24_SOURCE_PROJECTION_INVALID")
    sources = (*existing, source)
    if len(sources) != 12:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT12")
    if len({item.binding.review_unit_id for item in sources}) != 12:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT12")
    if len({item.binding.stable_identity for item in sources}) != 12:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT12")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 91:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_91")
    if len(set(event_ids)) != 91:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_f24_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact12 sources through the generic owner, entirely in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_f24_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_f24_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_f24_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
