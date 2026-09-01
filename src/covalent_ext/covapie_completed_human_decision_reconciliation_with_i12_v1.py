"""Reconcile published I12 completion through the unchanged generic owner.

This metadata-only successor loads the rich I12 authority through its
published ingestion owner, proves the exact authority boundary, and projects
only the generic completed-decision fact.  It appends that source to the
published 2A2 Exact13 chain, reuses the ONL historical normalizer, and performs
one in-memory generic reconciliation.  It does not write artifacts, refresh a
census or queue, create training admission, tensorize data, or train a model.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import (
    covapie_i12_completed_decision_ingestion_and_task_label_availability_v1
    as i12_ingestion_owner,
)
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_2a2_v1
    as two_a2_successor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)


__all__ = (
    "CompletedDecisionReconciliationWithI12Error",
    "project_i12_completed_decision_v1",
    "load_real_completed_decision_sources_with_i12_v1",
    "reconcile_real_completed_human_decisions_with_i12_v1",
)


_I12_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    i12_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_I12_FORMAL_DECISION_BYTE_COUNT = i12_ingestion_owner.FORMAL_BINDINGS[0][2]
_I12_FORMAL_DECISION_SHA256 = i12_ingestion_owner.FORMAL_BINDINGS[0][3]
_I12_FORMAL_DECISION_SCHEMA = i12_ingestion_owner.FORMAL_DECISION_SCHEMA
_I12_FORMAL_SEMANTIC_SHA256 = (
    i12_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_I12_REVIEW_UNIT_ID = i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_I12_ROLE_PROFILE = i12_ingestion_owner.EXPECTED_ROLE_PROFILE
_I12_EVENT_IDS = i12_ingestion_owner.EXPECTED_EVENT_IDS
_I12_RANKS = i12_ingestion_owner.EXPECTED_RANKS

_I12_EVENT_COUNT = 4
_I12_HISTORICAL_PRIORITY_RANK = "17"
_EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4)
_FUTURE_SOURCE_FACT_COUNTS = (*_EXISTING_SOURCE_FACT_COUNTS, 4)
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
_EXPECTED_APPROVAL_DECISIONS = {
    "D1_task_relevance": "RELEVANT",
    "D2_chemistry": "POSITIVE",
    "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
    "D4_role_partition": "SELECT_CANDIDATE_0",
    "D5_training_use": "INCLUDE",
}
_EXPECTED_CONTEXTS = tuple(
    (
        row[0],
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
        row[6],
    )
    for row in i12_ingestion_owner.EXPECTED_EVENTS
)


class CompletedDecisionReconciliationWithI12Error(ValueError):
    """Raised when the exact I12 reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithI12Error(token)


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _prove_generic_fact_schema_v1() -> None:
    fields = tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)
    if fields != _GENERIC_FACT_FIELDS or len(fields) != 11:
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")


def _validate_rich_i12_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove the rich I12 facts required before projection."""

    formal = _require_mapping(bound.get("formal"), "I12_FORMAL_DECISION_NOT_OBJECT")
    if (
        formal.get("schema_version") != _I12_FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != i12_ingestion_owner.FORMAL_RECORD_ROLE
        or formal.get("formal_semantic_canonical_sha256")
        != _I12_FORMAL_SEMANTIC_SHA256
        or formal.get("human_review_completed") is not True
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
    ):
        _fail("I12_FORMAL_COMPLETION_OR_SEMANTIC_DIGEST_INVALID")

    approval = _require_mapping(
        formal.get("human_approval"), "I12_HUMAN_APPROVAL_NOT_OBJECT"
    )
    if any(
        approval.get(key) != value
        for key, value in _EXPECTED_APPROVAL_DECISIONS.items()
    ):
        _fail("I12_D1_D5_DECISIONS_INVALID")
    if (
        approval.get("approved_at_utc")
        != i12_ingestion_owner.EXPECTED_APPROVED_AT_UTC
        or approval.get("human_selected_role_candidate_index_0based") != 0
        or approval.get("human_selected_role_profile") != _I12_ROLE_PROFILE
        or approval.get("human_choices_externally_authorized") is not True
        or approval.get("machine_approval_claimed") is not False
    ):
        _fail("I12_APPROVAL_OR_SELECTED_CANDIDATE_INVALID")

    identity = _require_mapping(formal.get("identity"), "I12_IDENTITY_NOT_OBJECT")
    if (
        identity.get("review_unit_id") != _I12_REVIEW_UNIT_ID
        or identity.get("ligand_component_id") != "I12"
        or identity.get("canonical_event_ids") != list(_I12_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_I12_RANKS)
        or identity.get("pdb_ids") != ["1WOF", "2AMP"]
        or identity.get("exact_event_count") != _I12_EVENT_COUNT
        or identity.get("unique_event_count") != _I12_EVENT_COUNT
        or identity.get("duplicate_event_count") != 0
        or identity.get("missing_event_count") != 0
        or identity.get("extra_event_count") != 0
        or identity.get("event_contexts_collapsed") is not False
    ):
        _fail("I12_FORMAL_IDENTITY_NOT_EXACT4")

    role = _require_mapping(
        formal.get("selected_role_partition"),
        "I12_SELECTED_ROLE_PARTITION_NOT_OBJECT",
    )
    runtime_validation = _require_mapping(
        role.get("published_role_runtime_validation"),
        "I12_ROLE_RUNTIME_VALIDATION_NOT_OBJECT",
    )
    if (
        role.get("D4_human_choice") != "SELECT_CANDIDATE_0"
        or role.get("selected_candidate_index_0based") != 0
        or role.get("human_selected_role_candidate_index_0based") != 0
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("machine_recommended_candidate") is not None
        or role.get("role_profile") != _I12_ROLE_PROFILE
        or role.get("warhead_role_atom_ids")
        != list(i12_ingestion_owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids")
        != list(i12_ingestion_owner.SCAFFOLD_ROLE)
        or role.get("applicable_task_ids") != [0, 3, 4]
        or role.get("partition_pairwise_disjoint") is not True
        or role.get("partition_exhaustive") is not True
        or runtime_validation.get("profile") != _I12_ROLE_PROFILE
        or runtime_validation.get("applicable_task_ids") != [0, 3, 4]
        or runtime_validation.get("valid") is not True
    ):
        _fail("I12_CANDIDATE0_DIRECT_ROLE_PARTITION_INVALID")

    canonical = _require_mapping(
        formal.get("canonical_Exact5_and_sample_applicability"),
        "I12_CANONICAL_TASK_CONTRACT_NOT_OBJECT",
    )
    tasks = _require_list(canonical.get("tasks"), "I12_CANONICAL_TASKS_NOT_LIST")
    observed_tasks = tuple(
        (
            task.get("task_id"),
            task.get("semantic_name"),
            task.get("display_alias"),
            task.get("structurally_applicable_to_I12"),
        )
        for task in tasks
        if type(task) is dict
    )
    expected_tasks = tuple(
        (task_id, semantic, alias, task_id in {0, 3, 4})
        for task_id, semantic, alias, _generated, _fixed
        in i12_ingestion_owner.CANONICAL_TASKS
    )
    if (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 3, 4]
        or observed_tasks != expected_tasks
    ):
        _fail("I12_CANONICAL_EXACT5_APPLICABILITY_INVALID")

    chemical = _require_mapping(
        formal.get("chemical_warhead_boundary"),
        "I12_CHEMICAL_WARHEAD_BOUNDARY_NOT_OBJECT",
    )
    reusable = _require_mapping(
        formal.get("reusable_authority_boundary"),
        "I12_REUSABLE_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    if (
        chemical.get("chemical_warhead_human_authoritative") is not False
        or chemical.get("chemical_warhead_atom_ids") is not None
        or chemical.get("reaction_family_authority_created") is not False
        or chemical.get("warhead_family_authority_created") is not False
        or chemical.get("warhead_rule_authority_created") is not False
        or chemical.get("reusable_chemistry_rule_created") is not False
        or reusable.get("reaction_family_authority_created") is not False
        or reusable.get("warhead_family_authority_created") is not False
        or reusable.get("warhead_rule_authority_created") is not False
        or reusable.get("reusable_chemistry_authority_created") is not False
    ):
        _fail("I12_CHEMICAL_OR_REUSABLE_AUTHORITY_BOUNDARY_INVALID")

    pre = _require_mapping(
        formal.get("experimental_context_and_PRE_boundary"),
        "I12_PRE_BOUNDARY_NOT_OBJECT",
    )
    post = _require_mapping(
        formal.get("POST_evidence_boundary"), "I12_POST_BOUNDARY_NOT_OBJECT"
    )
    if (
        pre.get("PRE_status") != i12_ingestion_owner.PRE_STATUS
        or pre.get("PRE_topology_authority_created") is not False
        or pre.get("PRE_geometry_authority_created") is not False
        or post.get("POST_source_evidence_count") != 4
        or post.get("POST_sample_authority_created") is not False
        or post.get("POST_geometry_training_authority_created") is not False
    ):
        _fail("I12_PRE_OR_POST_AUTHORITY_BOUNDARY_INVALID")

    training = _require_mapping(
        formal.get("training_use_human_decision"),
        "I12_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    authority = _require_mapping(
        formal.get("authority_boundary"), "I12_AUTHORITY_BOUNDARY_NOT_OBJECT"
    )
    if (
        training.get("D5_human_choice") != "INCLUDE"
        or training.get("candidate_for_future_training_admission") is not True
        or training.get("human_training_excluded") is not False
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed_now") is not False
        or authority.get("warhead_type_authority_created") is not False
        or authority.get("formal_training_admitted") is not False
        or authority.get("READY_FOR_TRAINING") is not False
    ):
        _fail("I12_TRAINING_OR_AUTHORITY_BOUNDARY_INVALID")

    derived_chemical = i12_ingestion_owner._chemical_authority_boundary()
    derived_geometry = i12_ingestion_owner._geometry_boundary()
    derived_training = i12_ingestion_owner._training_boundary()
    if (
        derived_chemical.get("chemical_warhead_human_authoritative") is not False
        or derived_chemical.get("chemical_warhead_atom_ids") is not None
        or derived_chemical.get("reaction_family_authority") is not False
        or derived_chemical.get("warhead_family_authority") is not False
        or derived_chemical.get("warhead_rule_authority") is not False
        or derived_chemical.get("warhead_type_authority") is not False
        or derived_chemical.get("reusable_chemistry_authority") is not False
        or derived_geometry.get("PRE_status") != i12_ingestion_owner.PRE_STATUS
        or derived_geometry.get("PRE_topology_authority_available") is not False
        or derived_geometry.get("PRE_geometry_authority_available") is not False
        or derived_geometry.get("POST_source_evidence_count") != 4
        or derived_geometry.get("POST_sample_authority") is not False
        or derived_geometry.get("POST_geometry_training_authority_available")
        is not False
        or derived_training.get("candidate_for_future_training_admission")
        is not True
        or derived_training.get("future_training_candidate_is_training_admission")
        is not False
        or derived_training.get("training_admitted") is not False
        or derived_training.get("ready_for_training") is not False
    ):
        _fail("I12_INGESTION_DERIVED_AUTHORITY_BOUNDARY_INVALID")

    events = _require_list(
        formal.get("event_level_human_decisions"),
        "I12_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _I12_EVENT_COUNT:
        _fail("I12_FORMAL_EVENT_COUNT_NOT_EXACT4")
    return tuple(
        _require_mapping(event, "I12_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )


def _project_validated_i12_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project only generic Exact11 fields from owner-validated I12."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "I12_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_binding = {
        "path": _I12_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _I12_FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _I12_FORMAL_DECISION_SHA256,
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "I12_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if dict(binding_value) != expected_binding:
        _fail("I12_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_i12_semantics_v1(bound)
    facts: list[generic.NormalizedCompletedDecisionFact] = []
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    observed_contexts: list[tuple[str, int, str, str, str, str, str]] = []
    for event in events:
        event_id = event.get("canonical_event_id")
        rank = event.get("scaleup_rank")
        pdb_id = event.get("pdb_id")
        protein_asym = event.get("protein_asym")
        cys_residue_id = event.get("cys_residue_id")
        ligand_asym = event.get("ligand_asym")
        connection_id = event.get("selected_connection_id")
        if (
            type(event_id) is not str
            or not event_id
            or type(rank) is not int
            or not all(
                type(value) is str
                for value in (
                    pdb_id,
                    protein_asym,
                    cys_residue_id,
                    ligand_asym,
                    connection_id,
                )
            )
        ):
            _fail("I12_FORMAL_EVENT_CONTEXT_INVALID")
        observed_ids.append(event_id)
        observed_ranks.append(rank)
        observed_contexts.append(
            (
                event_id,
                rank,
                pdb_id,
                protein_asym,
                cys_residue_id,
                ligand_asym,
                connection_id,
            )
        )
        if (
            event.get("protein_reactive_atom") != "SG"
            or event.get("ligand_component_id") != "I12"
            or event.get("ligand_reactive_atom") != "C21"
        ):
            _fail("I12_FORMAL_EVENT_COVALENT_IDENTITY_INVALID:" + event_id)
        if (
            event.get("D1_task_relevance") != "RELEVANT"
            or event.get("D2_chemistry") != "POSITIVE"
            or event.get("D3_reactive_pair") != "CONFIRM_OBSERVED_PAIR"
            or event.get("D4_role_partition") != "SELECT_CANDIDATE_0"
            or event.get("D5_training_use") != "INCLUDE"
            or event.get("formal_training_admitted") is not False
        ):
            _fail("I12_FORMAL_EVENT_DECISION_INVALID:" + event_id)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_I12_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_INCLUDE,
                human_training_excluded=False,
                source_decision_schema=_I12_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_I12_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _I12_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )

    if len(set(observed_ids)) != _I12_EVENT_COUNT:
        _fail("I12_FORMAL_EVENT_ID_DUPLICATE")
    if tuple(observed_ids) != _I12_EVENT_IDS:
        _fail("I12_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    if tuple(observed_ranks) != _I12_RANKS:
        _fail("I12_FORMAL_RANK_COVERAGE_NOT_EXACT4")
    if tuple(observed_contexts) != _EXPECTED_CONTEXTS:
        _fail("I12_DISTINCT_EVENT_CONTEXTS_NOT_EXACT4")

    binding = generic.SourceBinding(
        source_path=_I12_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_I12_FORMAL_DECISION_BYTE_COUNT,
        sha256=_I12_FORMAL_DECISION_SHA256,
        schema_version=_I12_FORMAL_DECISION_SCHEMA,
        review_unit_id=_I12_REVIEW_UNIT_ID,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_i12_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the I12 ingestion owner and project its narrow Exact4."""

    try:
        bound = i12_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except i12_ingestion_owner.I12IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithI12Error(
            "I12_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_i12_binding_v1(bound)


def _prove_i12_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove I12 is exactly one complete unreviewed historical unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWithI12Error(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_I12_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _I12_EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("I12_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _I12_EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("I12_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _I12_REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("I12_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4")
    target_rows = [row for row in rows if row["canonical_event_id"] in expected_ids]
    if any(
        row["raw_review_unit_id"] != _I12_REVIEW_UNIT_ID
        or row["raw_priority_rank"] != _I12_HISTORICAL_PRIORITY_RANK
        or row["raw_unit_event_count"] != "4"
        for row in target_rows
    ):
        _fail("I12_HISTORICAL_IDENTITY_OR_PRIORITY_INVALID")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target_rows
    ):
        _fail("I12_PRIOR_STATE_NOT_EXACT4_UNREVIEWED")
    generic._validate_historical_rows(rows)


def _prove_i12_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the published ONL normalizer changed no I12 row field."""

    expected_ids = set(_I12_EVENT_IDS)
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
        _fail("I12_ORIGINAL_EVENT_SET_NOT_EXACT4")
    if set(adapted_by_event) != expected_ids:
        _fail("I12_ADAPTED_EVENT_SET_NOT_EXACT4")
    changed = [
        event_id
        for event_id in _I12_EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_I12_ROW:" + changed[0])


def _validate_projected_i12_source_v1(
    source: generic.NormalizedDecisionSource,
) -> None:
    expected_binding = generic.SourceBinding(
        source_path=_I12_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_I12_FORMAL_DECISION_BYTE_COUNT,
        sha256=_I12_FORMAL_DECISION_SHA256,
        schema_version=_I12_FORMAL_DECISION_SCHEMA,
        review_unit_id=_I12_REVIEW_UNIT_ID,
    )
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding != expected_binding
        or len(source.facts) != _I12_EVENT_COUNT
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_I12_EVENT_IDS))
        or any(
            type(fact) is not generic.NormalizedCompletedDecisionFact
            or tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or fact.review_unit_id != _I12_REVIEW_UNIT_ID
            or fact.human_review_completed is not True
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            or fact.source_decision_schema != _I12_FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _I12_FORMAL_DECISION_SHA256
            or fact.source_binding_path != source.binding.source_path
            for fact in source.facts
        )
    ):
        _fail("I12_SOURCE_PROJECTION_INVALID")


def load_real_completed_decision_sources_with_i12_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published Exact13 chain and append one I12 source."""

    existing = two_a2_successor.load_real_completed_decision_sources_with_2a2_v1(
        repo_root
    )
    if (
        len(existing) != 13
        or tuple(len(source.facts) for source in existing)
        != _EXISTING_SOURCE_FACT_COUNTS
    ):
        _fail("EXISTING_2A2_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 95
        or len(set(existing_event_ids)) != 95
        or len({source.binding.review_unit_id for source in existing}) != 13
        or len({source.binding.stable_identity for source in existing}) != 13
    ):
        _fail("EXISTING_2A2_SOURCE_CHAIN_NOT_EXACT13_95")

    source = project_i12_completed_decision_v1(repo_root=repo_root)
    _validate_projected_i12_source_v1(source)
    i12_event_ids = {fact.canonical_event_id for fact in source.facts}
    overlap = i12_event_ids & set(existing_event_ids)
    if overlap:
        _fail("I12_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])

    sources = (*existing, source)
    if (
        len(sources) != 14
        or tuple(len(item.facts) for item in sources) != _FUTURE_SOURCE_FACT_COUNTS
        or len({item.binding.review_unit_id for item in sources}) != 14
        or len({item.binding.stable_identity for item in sources}) != 14
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT14")
    event_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(event_ids) != 99:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_99")
    if len(set(event_ids)) != 99:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_i12_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact14 sources once through the generic owner in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_i12_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_i12_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_i12_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
