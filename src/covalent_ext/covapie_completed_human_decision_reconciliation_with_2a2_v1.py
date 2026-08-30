"""Reconcile the published 2A2 Exact4 through the unchanged generic owner.

This metadata-only successor validates the rich 2A2 completion through its
published ingestion owner, projects only the generic completed-decision fact,
appends that source to the published F24 Exact12 source chain, reuses the ONL
historical transition owner, and performs one generic in-memory
reconciliation.  Rich role, chemical, PRE/POST, seed, census, and training
admission semantics remain upstream and are not copied into the generic fact.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import (
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as two_a2_ingestion_owner,
)
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_f24_v1 as f24_successor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)


__all__ = (
    "CompletedDecisionReconciliationWith2A2Error",
    "project_2a2_completed_decision_v1",
    "load_real_completed_decision_sources_with_2a2_v1",
    "reconcile_real_completed_human_decisions_with_2a2_v1",
)


_TWO_A2_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    two_a2_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_TWO_A2_FORMAL_DECISION_BYTE_COUNT = two_a2_ingestion_owner.FORMAL_BINDINGS[0][2]
_TWO_A2_FORMAL_DECISION_SHA256 = two_a2_ingestion_owner.FORMAL_BINDINGS[0][3]
_TWO_A2_FORMAL_DECISION_SCHEMA = two_a2_ingestion_owner.FORMAL_DECISION_SCHEMA
_TWO_A2_FORMAL_SEMANTIC_SHA256 = (
    two_a2_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_TWO_A2_REVIEW_UNIT_ID = two_a2_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_TWO_A2_EVENT_IDS = two_a2_ingestion_owner.EXPECTED_EVENT_IDS
_TWO_A2_RANKS = two_a2_ingestion_owner.EXPECTED_RANKS

_TWO_A2_EVENT_COUNT = 4
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4)
_EXPECTED_CONTEXTS = (
    (_TWO_A2_EVENT_IDS[0], 507, "A", "E", "covale1"),
    (_TWO_A2_EVENT_IDS[1], 508, "B", "G", "covale3"),
    (_TWO_A2_EVENT_IDS[2], 509, "C", "I", "covale6"),
    (_TWO_A2_EVENT_IDS[3], 510, "D", "K", "covale8"),
)
_EXPECTED_APPROVAL_DECISIONS = {
    "D1_task_relevance": "RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_partition": "SELECT_CANDIDATE_4",
    "D5_training_use": "EXCLUDE_FROM_TRAINING_ONLY",
}
_EXPECTED_CURRENT_CENSUS = {
    "positive": 108,
    "relevant": 109,
    "training_INCLUDE": 44,
    "training_EXCLUDE": 64,
    "future_candidates": 27,
    "pair_sample_authority": 108,
    "role_sample_authority": 108,
    "strict_profile": 48,
    "direct_profile": 60,
    "A": 108,
    "B": 48,
    "B2": 48,
    "B3": 108,
    "C": 108,
    "current_2A2_status": "CURRENTLY_UNREVIEWED",
    "current_2A2_human_review_completed": False,
    "global_reconciliation_updated": False,
    "global_census_updated": False,
    "priority_queue_updated": False,
}
_EXPECTED_FUTURE_CENSUS_INFORMATIONAL = {
    "status": "INFORMATIONAL_ONLY",
    "current_global_state": False,
    "materialized_this_step": False,
    "positive": 112,
    "relevant": 113,
    "training_INCLUDE": 44,
    "training_EXCLUDE": 68,
    "future_candidates": 27,
    "pair_sample_authority": 112,
    "role_sample_authority": 112,
    "strict_profile": 52,
    "direct_profile": 60,
    "A": 112,
    "B": 52,
    "B2": 52,
    "B3": 112,
    "C": 112,
}
TWO_A2_TRANSITION_ADAPTER_CREATED = False


class CompletedDecisionReconciliationWith2A2Error(ValueError):
    """Raised when the exact 2A2 reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWith2A2Error(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _validate_rich_2a2_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Prove owner-validated rich 2A2 semantics before narrow projection."""

    formal = _require_mapping(bound.get("formal"), "2A2_FORMAL_DECISION_NOT_OBJECT")
    if (
        formal.get("schema_version") != _TWO_A2_FORMAL_DECISION_SCHEMA
        or formal.get("record_role")
        != two_a2_ingestion_owner.FORMAL_RECORD_ROLE
        or formal.get("formal_semantic_canonical_sha256")
        != _TWO_A2_FORMAL_SEMANTIC_SHA256
        or formal.get("human_review_completed") is not True
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
    ):
        _fail("2A2_FORMAL_COMPLETION_OR_SEMANTIC_DIGEST_INVALID")

    approval = _require_mapping(
        formal.get("human_approval"), "2A2_HUMAN_APPROVAL_NOT_OBJECT"
    )
    if any(approval.get(key) != value for key, value in _EXPECTED_APPROVAL_DECISIONS.items()):
        _fail("2A2_D1_D5_DECISIONS_INVALID")
    if (
        approval.get("approved_at_utc")
        != two_a2_ingestion_owner.EXPECTED_APPROVED_AT_UTC
        or approval.get("human_selected_role_candidate_index_0based") != 4
        or approval.get("human_choices_externally_authorized") is not True
        or approval.get("machine_approval_claimed") is not False
    ):
        _fail("2A2_APPROVAL_OR_SELECTED_CANDIDATE_INVALID")

    identity = _require_mapping(formal.get("identity"), "2A2_IDENTITY_NOT_OBJECT")
    if (
        identity.get("review_unit_id") != _TWO_A2_REVIEW_UNIT_ID
        or identity.get("ligand_component_id") != "2A2"
        or identity.get("canonical_event_ids") != list(_TWO_A2_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_TWO_A2_RANKS)
        or identity.get("pdb_ids") != ["3ORZ"]
        or identity.get("exact_event_count") != _TWO_A2_EVENT_COUNT
        or identity.get("unique_event_count") != _TWO_A2_EVENT_COUNT
        or identity.get("duplicate_event_count") != 0
        or identity.get("missing_event_count") != 0
        or identity.get("extra_event_count") != 0
        or identity.get("event_contexts_collapsed") is not False
    ):
        _fail("2A2_FORMAL_IDENTITY_NOT_EXACT4")

    pair = _require_mapping(
        formal.get("reactive_pair_human_decision"),
        "2A2_REACTIVE_PAIR_NOT_OBJECT",
    )
    if (
        pair.get("D3_human_choice") != "CONFIRM_OBSERVED_PAIR"
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "SD"
        or pair.get("reactive_pair_human_authoritative") is not True
        or pair.get("reactive_pair_human_authoritative_event_count") != 4
        or pair.get("cross_sample_reusable_pair_authority_created") is not False
    ):
        _fail("2A2_CONFIRMED_PAIR_INVALID")

    role = _require_mapping(
        formal.get("selected_role_partition"),
        "2A2_SELECTED_ROLE_PARTITION_NOT_OBJECT",
    )
    if (
        role.get("D4_human_choice") != "SELECT_CANDIDATE_4"
        or role.get("selected_candidate_index_0based") != 4
        or role.get("human_selected_role_candidate_index_0based") != 4
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("role_profile")
        != two_a2_ingestion_owner.EXPECTED_ROLE_PROFILE
        or role.get("warhead_role_atom_ids")
        != list(two_a2_ingestion_owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids")
        != list(two_a2_ingestion_owner.LINKER_ROLE)
        or role.get("scaffold_atom_ids")
        != list(two_a2_ingestion_owner.SCAFFOLD_ROLE)
        or role.get("boundary_bonds")
        != list(two_a2_ingestion_owner.BOUNDARY_BONDS)
        or role.get("partition_pairwise_disjoint") is not True
        or role.get("partition_exhaustive") is not True
        or role.get("applicable_task_ids") != [0, 1, 2, 3, 4]
    ):
        _fail("2A2_CANDIDATE4_STRICT_ROLE_PARTITION_INVALID")

    canonical = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "2A2_CANONICAL_TASK_CONTRACT_NOT_OBJECT",
    )
    tasks = _require_list(canonical.get("tasks"), "2A2_CANONICAL_TASKS_NOT_LIST")
    expected_tasks = tuple(
        (task_id, semantic, alias, True)
        for task_id, semantic, alias, _generated, _fixed
        in two_a2_ingestion_owner.CANONICAL_TASKS
    )
    observed_tasks = tuple(
        (
            task.get("task_id"),
            task.get("semantic_name"),
            task.get("display_alias"),
            task.get("structurally_applicable_to_2A2"),
        )
        for task in tasks
        if type(task) is dict
    )
    if (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 1, 2, 3, 4]
        or observed_tasks != expected_tasks
    ):
        _fail("2A2_CANONICAL_EXACT5_APPLICABILITY_INVALID")

    chemical = _require_mapping(
        formal.get("chemical_warhead_boundary"),
        "2A2_CHEMICAL_WARHEAD_BOUNDARY_NOT_OBJECT",
    )
    if (
        chemical.get("chemical_warhead_atom_ids") is not None
        or chemical.get("chemical_warhead_human_authoritative") is not False
        or chemical.get("W_SD_is_complete_PRE_chemical_warhead_definition")
        is not False
    ):
        _fail("2A2_CHEMICAL_WARHEAD_BOUNDARY_INVALID")

    pre = _require_mapping(
        formal.get("experimental_context_and_PRE_boundary"),
        "2A2_PRE_BOUNDARY_NOT_OBJECT",
    )
    if (
        pre.get("engineered_target_site") != "PDK1_T148C"
        or pre.get("native_cysteine_site") is not False
        or pre.get("disulfide_trapping_context") is not True
        or pre.get("complete_PRE_disulfide_reagent_authority") is not False
        or pre.get("observed_graph_is_complete_authoritative_PRE_reagent")
        is not False
        or pre.get("PRE_topology_authority_created") is not False
        or pre.get("PRE_geometry_authority_created") is not False
        or pre.get("PRE_reconstruction_performed") is not False
        or pre.get("POST_to_PRE_copy_performed") is not False
        or pre.get("PRE_zero_fill_performed") is not False
    ):
        _fail("2A2_PRE_AUTHORITY_BOUNDARY_INVALID")

    if formal.get("POST_evidence_boundary") != {
        "POST_geometry_training_authority_created": False,
        "POST_geometry_training_target_created": False,
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
    }:
        _fail("2A2_POST_TRAINING_AUTHORITY_BOUNDARY_INVALID")
    if formal.get("minimal_seed") != {
        "minimal_seed_atom_ids": None,
        "minimal_seed_authority_created": False,
    }:
        _fail("2A2_MINIMAL_SEED_AUTHORITY_BOUNDARY_INVALID")

    training = _require_mapping(
        formal.get("training_use_human_decision"),
        "2A2_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    if (
        training.get("D5_human_choice") != "EXCLUDE_FROM_TRAINING_ONLY"
        or training.get("task_relevance") != "RELEVANT"
        or training.get("chemistry") != "POSITIVE"
        or training.get("human_training_excluded") is not True
        or training.get("training_use_allowed") is not False
        or training.get("candidate_for_future_training_admission") is not False
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed_now") is not False
        or training.get("formal_split_authority_created") is not False
        or training.get("tensor_target_created") is not False
        or training.get("current_runtime_model_usable") is not False
        or training.get("parameter_update_authorization") is not False
    ):
        _fail("2A2_EXCLUDE_OR_TRAINING_ADMISSION_BOUNDARY_INVALID")

    derived_training = two_a2_ingestion_owner._training_boundary()
    derived_geometry = two_a2_ingestion_owner._geometry_boundary()
    derived_reusable = two_a2_ingestion_owner._reusable_boundary()
    if (
        derived_training.get("candidate_for_future_training_admission") is not False
        or derived_training.get("future_training_candidate_derived_by_ingestion")
        is not False
        or derived_training.get("training_admitted") is not False
        or derived_training.get("current_runtime_model_usable") is not False
        or derived_training.get("ready_for_training") is not False
        or derived_geometry.get("complete_PRE_disulfide_reagent_authority_available")
        is not False
        or derived_geometry.get("PRE_topology_authority_available") is not False
        or derived_geometry.get("PRE_geometry_authority_available") is not False
        or derived_geometry.get("POST_geometry_training_authority_created")
        is not False
        or any(value is not False for value in derived_reusable.values())
    ):
        _fail("2A2_INGESTION_DERIVED_AUTHORITY_BOUNDARY_INVALID")

    precedent = _require_mapping(
        formal.get("published_1F8_same_context_precedent"),
        "2A2_PRECEDENT_STATE_NOT_OBJECT",
    )
    if (
        "2A2_independent_human_review_still_required" in precedent
        or precedent.get("precedent_did_not_substitute_for_2A2_independent_review")
        is not True
        or precedent.get("2A2_independent_human_review_completed") is not True
        or precedent.get("generic_disulfide_trapping_exclusion_rule_created")
        is not False
        or precedent.get("reusable_rule_created") is not False
    ):
        _fail("2A2_REVISED_PRECEDENT_STATE_INVALID")

    if bound.get("current_published_census_boundary") != _EXPECTED_CURRENT_CENSUS:
        _fail("2A2_CURRENT_PUBLISHED_CENSUS_BOUNDARY_INVALID")
    if (
        bound.get("future_census_informational")
        != _EXPECTED_FUTURE_CENSUS_INFORMATIONAL
    ):
        _fail("2A2_FUTURE_CENSUS_INFORMATIONAL_BOUNDARY_INVALID")

    events = _require_list(
        formal.get("event_level_human_decisions"),
        "2A2_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _TWO_A2_EVENT_COUNT:
        _fail("2A2_FORMAL_EVENT_COUNT_NOT_EXACT4")
    return tuple(
        _require_mapping(event, "2A2_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )


def _project_validated_2a2_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic completed-decision fields from validated 2A2."""

    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "2A2_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _TWO_A2_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": _TWO_A2_FORMAL_DECISION_BYTE_COUNT,
        "sha256": _TWO_A2_FORMAL_DECISION_SHA256,
        "sha256_scope": "file_bytes",
        "source_role": "2A2_FROZEN_REVISED1_FORMAL_HUMAN_DECISION",
        "mode": "0664",
    }
    if dict(binding_value) != expected_binding:
        _fail("2A2_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_2a2_semantics_v1(bound)
    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_contexts: list[tuple[str, int, str, str, str]] = []
    observed_ids: list[str] = []
    for event in events:
        event_id = event.get("canonical_event_id")
        rank = event.get("scaleup_rank")
        protein_asym = event.get("protein_asym")
        ligand_asym = event.get("ligand_asym")
        connection_id = event.get("selected_connection_id")
        if (
            type(event_id) is not str
            or not event_id
            or type(rank) is not int
            or not all(
                type(value) is str
                for value in (protein_asym, ligand_asym, connection_id)
            )
        ):
            _fail("2A2_FORMAL_EVENT_CONTEXT_INVALID")
        observed_ids.append(event_id)
        observed_contexts.append(
            (event_id, rank, protein_asym, ligand_asym, connection_id)
        )
        if (
            event.get("pdb_id") != "3ORZ"
            or event.get("cys_residue_id") != "CYS:148-"
            or event.get("protein_reactive_atom") != "SG"
            or event.get("ligand_component_id") != "2A2"
            or event.get("ligand_reactive_atom") != "SD"
        ):
            _fail("2A2_FORMAL_EVENT_COVALENT_IDENTITY_INVALID:" + event_id)
        if (
            event.get("D1_task_relevance") != "RELEVANT"
            or event.get("D2_chemistry") != "POSITIVE"
            or event.get("D3_reactive_pair") != "CONFIRM_OBSERVED_PAIR"
            or event.get("D4_role_partition") != "SELECT_CANDIDATE_4"
            or event.get("D5_training_use") != "EXCLUDE_FROM_TRAINING_ONLY"
            or event.get("formal_training_admitted") is not False
        ):
            _fail("2A2_FORMAL_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_TWO_A2_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_EXCLUDE,
                human_training_excluded=True,
                source_decision_schema=_TWO_A2_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_TWO_A2_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _TWO_A2_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _TWO_A2_EVENT_COUNT:
        _fail("2A2_FORMAL_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _TWO_A2_EVENT_IDS:
        _fail("2A2_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    if tuple(observed_contexts) != _EXPECTED_CONTEXTS:
        _fail("2A2_DISTINCT_EVENT_CONTEXTS_NOT_EXACT4")

    binding = generic.SourceBinding(
        source_path=(
            _TWO_A2_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=_TWO_A2_FORMAL_DECISION_BYTE_COUNT,
        sha256=_TWO_A2_FORMAL_DECISION_SHA256,
        schema_version=_TWO_A2_FORMAL_DECISION_SCHEMA,
        review_unit_id=_TWO_A2_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_2a2_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the 2A2 ingestion owner and project its validated Exact4."""

    try:
        bound = two_a2_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except two_a2_ingestion_owner.TwoA2IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith2A2Error(
            "2A2_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_2a2_binding_v1(bound)


def _prove_2a2_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the original 2A2 unit meets the generic prior preconditions."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWith2A2Error(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_TWO_A2_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _TWO_A2_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("2A2_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _TWO_A2_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("2A2_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _TWO_A2_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("2A2_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4")
    target_rows = [
        row for row in rows if row["canonical_event_id"] in expected_ids
    ]
    if any(
        row["raw_review_unit_id"] != _TWO_A2_REVIEW_UNIT_ID
        for row in target_rows
    ):
        _fail("2A2_HISTORICAL_REVIEW_UNIT_ID_MISMATCH")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target_rows
    ):
        _fail("2A2_PRIOR_STATE_NOT_EXACT4_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_2a2_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the ONL normalization did not change any 2A2 field."""

    expected_ids = set(_TWO_A2_EVENT_IDS)
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
        _fail("2A2_ORIGINAL_EVENT_SET_NOT_EXACT4")
    if set(adapted_by_event) != expected_ids:
        _fail("2A2_ADAPTED_EVENT_SET_NOT_EXACT4")
    changed = [
        event_id
        for event_id in _TWO_A2_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_2A2_ROW:" + changed[0])


def load_real_completed_decision_sources_with_2a2_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published F24 Exact12 sources and append one 2A2 source."""

    existing = f24_successor.load_real_completed_decision_sources_with_f24_v1(
        repo_root
    )
    if len(existing) != 12 or tuple(len(source.facts) for source in existing) != (
        _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_F24_SOURCE_COMPOSITION_INVALID")
    source = project_2a2_completed_decision_v1(repo_root=repo_root)
    expected_binding = generic.SourceBinding(
        source_path=(
            _TWO_A2_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=_TWO_A2_FORMAL_DECISION_BYTE_COUNT,
        sha256=_TWO_A2_FORMAL_DECISION_SHA256,
        schema_version=_TWO_A2_FORMAL_DECISION_SCHEMA,
        review_unit_id=_TWO_A2_REVIEW_UNIT_ID,
    )
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding != expected_binding
        or len(source.facts) != _TWO_A2_EVENT_COUNT
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_TWO_A2_EVENT_IDS))
        or any(
            type(fact) is not generic.NormalizedCompletedDecisionFact
            or fact.review_unit_id != _TWO_A2_REVIEW_UNIT_ID
            or fact.human_review_completed is not True
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_EXCLUDE
            or fact.human_training_excluded is not True
            or fact.source_decision_schema != _TWO_A2_FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _TWO_A2_FORMAL_DECISION_SHA256
            or fact.source_binding_path != source.binding.source_path
            for fact in source.facts
        )
    ):
        _fail("2A2_SOURCE_PROJECTION_INVALID")

    sources = (*existing, source)
    if len(sources) != 13:
        _fail("REAL_SOURCE_COUNT_NOT_EXACT13")
    if len({item.binding.review_unit_id for item in sources}) != 13:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT13")
    if len({item.binding.stable_identity for item in sources}) != 13:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT13")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 95:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_95")
    if len(set(event_ids)) != 95:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_2a2_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact13 sources once through the generic owner in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_2a2_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_2a2_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_2a2_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
