"""Reconcile published 1N0 completion through the unchanged generic owner.

This metadata-only successor loads the rich 1N0 authority through its
published ingestion owner, proves the exact task-domain-negative authority
boundary, and projects only generic completed-decision facts.  It appends one
Exact4 source to the published with-I12 chain and performs one in-memory
generic reconciliation.  It creates no reconciliation artifact, census or
queue refresh, training admission, tensor target, or parameter update.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import (
    covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1
    as one_n0_ingestion_owner,
)
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import (
    covapie_completed_human_decision_reconciliation_with_i12_v1
    as i12_predecessor,
)
from . import (
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)


__all__ = (
    "CompletedDecisionReconciliationWith1N0Error",
    "project_1n0_completed_decision_v1",
    "load_real_completed_decision_sources_with_1n0_v1",
    "reconcile_real_completed_human_decisions_with_1n0_v1",
)


_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    one_n0_ingestion_owner.FORMAL_DECISION_RELATIVE
)
_FORMAL_DECISION_BYTE_COUNT = one_n0_ingestion_owner.FORMAL_BINDINGS[0][2]
_FORMAL_DECISION_SHA256 = one_n0_ingestion_owner.FORMAL_BINDINGS[0][3]
_FORMAL_DECISION_SCHEMA = one_n0_ingestion_owner.FORMAL_DECISION_SCHEMA
_FORMAL_SEMANTIC_SHA256 = (
    one_n0_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
)
_REVIEW_UNIT_ID = one_n0_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
_EVENT_IDS = one_n0_ingestion_owner.EXPECTED_EVENT_IDS
_RANKS = one_n0_ingestion_owner.EXPECTED_RANKS
_EXCLUDED_C2_RANKS = one_n0_ingestion_owner.EXCLUDED_C2_RANKS

_EVENT_COUNT = 4
_HISTORICAL_PRIORITY_RANK = "18"
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
)
_SUCCESSOR_SOURCE_FACT_COUNTS = (*_PREDECESSOR_SOURCE_FACT_COUNTS, 4)
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
_FORBIDDEN_GENERIC_FACT_ATTRIBUTES = (
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "second_endpoint",
    "role_profile",
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "boundary_bonds",
    "canonical_mask_applicability",
    "PRE_geometry",
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
)
_EXPECTED_DECISIONS = {
    "D1_task_relevance": "NOT_RELEVANT",
    "D2_chemistry": "UNRESOLVED",
    "D3_reactive_pair": "UNRESOLVED",
    "D4_role_candidate": "UNRESOLVED",
    "D5_training_use": "UNRESOLVED",
}
_EXPECTED_GENERIC_PROJECTION = {
    "human_review_completed": True,
    "legacy_completed_status": "COMPLETED_HUMAN_NEGATIVE",
    "task_relevance_disposition": "NOT_RELEVANT",
    "chemistry_disposition": "NOT_ESTABLISHED",
    "training_disposition": "NOT_APPLICABLE",
    "human_training_excluded": False,
}


class CompletedDecisionReconciliationWith1N0Error(ValueError):
    """Raised when the exact 1N0 reconciliation contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWith1N0Error(token)


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


def _validate_rich_1n0_semantics_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    """Independently prove the rich Exact4 boundary before projection."""

    formal = _require_mapping(bound.get("formal"), "ONE_N0_FORMAL_NOT_OBJECT")
    if (
        formal.get("schema_version") != _FORMAL_DECISION_SCHEMA
        or formal.get("formal_semantic_canonical_sha256")
        != _FORMAL_SEMANTIC_SHA256
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
        or formal.get("human_review_completed") is not True
        or formal.get("formal_authority_created") is not True
    ):
        _fail("ONE_N0_FORMAL_COMPLETION_OR_SEMANTIC_DIGEST_INVALID")

    human = _require_mapping(
        formal.get("human_authorization"),
        "ONE_N0_HUMAN_AUTHORIZATION_NOT_OBJECT",
    )
    unit = _require_mapping(
        formal.get("unit_human_decision"),
        "ONE_N0_UNIT_DECISION_NOT_OBJECT",
    )
    if any(
        human.get(key) != value or unit.get(key) != value
        for key, value in _EXPECTED_DECISIONS.items()
    ):
        _fail("ONE_N0_D1_D5_DECISIONS_INVALID")

    identity = _require_mapping(
        formal.get("identity"), "ONE_N0_IDENTITY_NOT_OBJECT"
    )
    if (
        identity.get("review_unit_id") != _REVIEW_UNIT_ID
        or identity.get("ligand_component_id") != "1N0"
        or identity.get("canonical_event_ids") != list(_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(_RANKS)
        or identity.get("separate_review_unit_C2_event_ranks")
        != list(_EXCLUDED_C2_RANKS)
        or identity.get("target_protein_atom") != "SG"
        or identity.get("target_ligand_atom") != "C16"
        or identity.get("exact_event_count") != _EVENT_COUNT
        or identity.get("unique_event_count") != _EVENT_COUNT
        or identity.get("duplicate_event_count") != 0
        or identity.get("missing_event_count") != 0
        or identity.get("extra_event_count") != 0
    ):
        _fail("ONE_N0_FORMAL_IDENTITY_NOT_EXACT4")
    if set(_RANKS) & set(_EXCLUDED_C2_RANKS):
        _fail("ONE_N0_C2_RANK_INCLUDED_IN_TARGET")

    projection = _require_mapping(
        formal.get("expected_downstream_normalized_projection"),
        "ONE_N0_EXPECTED_PROJECTION_NOT_OBJECT",
    )
    if any(
        projection.get(key) != value
        for key, value in _EXPECTED_GENERIC_PROJECTION.items()
    ):
        _fail("ONE_N0_EXPECTED_GENERIC_PROJECTION_INVALID")

    chemistry = _require_mapping(
        formal.get("chemistry_authority_boundary"),
        "ONE_N0_CHEMISTRY_BOUNDARY_NOT_OBJECT",
    )
    reactive = _require_mapping(
        formal.get("reactive_pair_boundary"),
        "ONE_N0_REACTIVE_PAIR_BOUNDARY_NOT_OBJECT",
    )
    role = _require_mapping(
        formal.get("role_authority_boundary"),
        "ONE_N0_ROLE_BOUNDARY_NOT_OBJECT",
    )
    training = _require_mapping(
        formal.get("training_boundary"),
        "ONE_N0_TRAINING_BOUNDARY_NOT_OBJECT",
    )
    prepost = _require_mapping(
        formal.get("PRE_POST_boundary"),
        "ONE_N0_PRE_POST_BOUNDARY_NOT_OBJECT",
    )
    authority = _require_mapping(
        formal.get("authority_boundary"),
        "ONE_N0_AUTHORITY_BOUNDARY_NOT_OBJECT",
    )
    if (
        chemistry.get("task_domain_negative") is not True
        or chemistry.get("negative_chemistry") is not False
        or chemistry.get("chemistry_positive_authority") is not False
        or chemistry.get("chemistry_negative_authority") is not False
        or chemistry.get("chemical_warhead_human_authority") is not False
        or chemistry.get("chemical_warhead_atom_ids") is not None
        or chemistry.get("reaction_family_authority") is not False
        or chemistry.get("warhead_family_authority") is not False
        or chemistry.get("warhead_rule_authority") is not False
        or chemistry.get("warhead_type_authority") is not False
        or chemistry.get("reusable_chemistry_authority") is not False
        or reactive.get("reactive_pair_raw_structural_evidence") is not True
        or reactive.get("reactive_pair_human_authority") is not False
        or role.get("role_partition_human_authority") is not False
        or role.get("canonical_mask_structural_labels_human_authority")
        is not False
        or role.get("sample_authoritative_applicable_task_ids") is not None
        or role.get("global_canonical_mask_task_count") != 5
        or role.get("B3_present") is not True
        or role.get("sixth_task_present") is not False
        or training.get("human_training_excluded") is not False
        or training.get("training_use_include") is not False
        or training.get("future_training_admission_candidate") is not False
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed_now") is not False
        or prepost.get("POST_source_evidence_available") is not True
        or prepost.get("POST_geometry_training_authority_created") is not False
        or prepost.get("PRE_geometry_authority_created") is not False
        or prepost.get("PRE_topology_authority_created") is not False
        or authority.get("sample_level_task_relevance_authority_created")
        is not True
        or authority.get("sample_level_task_domain_negative_authority_created")
        is not True
        or authority.get("training_only_exclusion_authority") is not False
        or authority.get("READY_FOR_TRAINING") is not False
    ):
        _fail("ONE_N0_RICH_NEGATIVE_AUTHORITY_BOUNDARY_INVALID")

    semantic_contract = _require_mapping(
        bound.get("semantic_contract"),
        "ONE_N0_SEMANTIC_CONTRACT_NOT_OBJECT",
    )
    if (
        semantic_contract.get("global_canonical_task_count") != 5
        or semantic_contract.get("B3_present") is not True
        or semantic_contract.get("sixth_task_present") is not False
        or semantic_contract.get("sample_authoritative_applicable_task_ids")
        is not None
        or semantic_contract.get("generic_completed_negative_projection")
        != one_n0_ingestion_owner.GENERIC_PROJECTION
    ):
        _fail("ONE_N0_SEMANTIC_CONTRACT_INVALID")

    events = _require_list(
        formal.get("event_level_human_decisions"),
        "ONE_N0_EVENT_DECISIONS_NOT_LIST",
    )
    if len(events) != _EVENT_COUNT:
        _fail("ONE_N0_FORMAL_EVENT_COUNT_NOT_EXACT4")
    typed_events = tuple(
        _require_mapping(event, "ONE_N0_FORMAL_EVENT_NOT_OBJECT")
        for event in events
    )
    for event, expected in zip(typed_events, one_n0_ingestion_owner.EXPECTED_EVENTS):
        if (
            event.get("canonical_event_id") != expected[0]
            or event.get("scaleup_rank") != expected[1]
            or event.get("pdb_id") != expected[2]
            or event.get("target_protein_asym") != expected[3]
            or event.get("target_cys_residue_id") != expected[4]
            or event.get("ligand_asym") != expected[5]
            or event.get("primary_connection_id") != expected[6]
            or event.get("ligand_component_id") != "1N0"
            or event.get("target_protein_atom") != "SG"
            or event.get("target_ligand_atom") != "C16"
            or event.get("second_endpoint_ligand_atom") != "C2"
            or event.get("task_relevance_decision") != "NOT_RELEVANT"
            or event.get("D2_chemistry") != "UNRESOLVED"
            or event.get("D3_reactive_pair") != "UNRESOLVED"
            or event.get("D4_role_candidate") != "UNRESOLVED"
            or event.get("D5_training_use") != "UNRESOLVED"
            or event.get("explicit_covalent_evidence") is not True
            or event.get("task_relevance_human_authoritative") is not True
            or event.get("chemistry_human_authoritative") is not False
            or event.get("reactive_pair_human_authoritative") is not False
            or event.get("role_partition_human_authoritative") is not False
            or event.get("training_only_exclusion_human_authoritative")
            is not False
            or event.get("formal_training_admitted") is not False
        ):
            event_id = event.get("canonical_event_id")
            _fail("ONE_N0_RICH_EVENT_SEMANTICS_INVALID:" + str(event_id))
    return typed_events


def _expected_binding_v1() -> generic.SourceBinding:
    return generic.SourceBinding(
        source_path=_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_FORMAL_DECISION_BYTE_COUNT,
        sha256=_FORMAL_DECISION_SHA256,
        schema_version=_FORMAL_DECISION_SCHEMA,
        review_unit_id=_REVIEW_UNIT_ID,
    )


def _validate_projected_1n0_source_v1(
    source: generic.NormalizedDecisionSource,
) -> None:
    """Reject any projection outside the frozen Exact4 negative contract."""

    _prove_generic_fact_schema_v1()
    expected_binding = _expected_binding_v1()
    if (
        type(source) is not generic.NormalizedDecisionSource
        or source.binding != expected_binding
        or len(source.facts) != _EVENT_COUNT
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(_EVENT_IDS))
    ):
        _fail("ONE_N0_SOURCE_PROJECTION_IDENTITY_INVALID")
    for fact in source.facts:
        if (
            type(fact) is not generic.NormalizedCompletedDecisionFact
            or tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or any(
                hasattr(fact, attribute)
                for attribute in _FORBIDDEN_GENERIC_FACT_ATTRIBUTES
            )
            or fact.review_unit_id != _REVIEW_UNIT_ID
            or fact.human_review_completed is not True
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition
            != generic.CHEMISTRY_NOT_ESTABLISHED
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
            or fact.source_decision_schema != _FORMAL_DECISION_SCHEMA
            or fact.source_decision_sha256 != _FORMAL_DECISION_SHA256
            or fact.source_binding_path != expected_binding.source_path
        ):
            _fail("ONE_N0_SOURCE_PROJECTION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWith1N0Error(
                "ONE_N0_GENERIC_FACT_REJECTED:" + str(error)
            ) from error


def _project_validated_1n0_binding_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    """Project Exact11 only after independently validating the rich boundary."""

    _prove_generic_fact_schema_v1()
    binding_value = _require_mapping(
        bound.get("formal_decision_binding"),
        "ONE_N0_FORMAL_DECISION_BINDING_NOT_OBJECT",
    )
    expected_owner_binding = {
        "path": _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": _FORMAL_DECISION_BYTE_COUNT,
        "SHA256": _FORMAL_DECISION_SHA256,
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "ONE_N0_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if dict(binding_value) != expected_owner_binding:
        _fail("ONE_N0_FORMAL_DECISION_BINDING_INVALID")

    events = _validate_rich_1n0_semantics_v1(bound)
    observed_ids: list[str] = []
    observed_ranks: list[int] = []
    facts: list[generic.NormalizedCompletedDecisionFact] = []
    for event in events:
        event_id = event.get("canonical_event_id")
        rank = event.get("scaleup_rank")
        if type(event_id) is not str or not event_id or type(rank) is not int:
            _fail("ONE_N0_FORMAL_EVENT_IDENTITY_INVALID")
        observed_ids.append(event_id)
        observed_ranks.append(rank)
        facts.append(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=_REVIEW_UNIT_ID,
                human_review_completed=True,
                legacy_completed_review_status=(
                    generic.COMPLETED_HUMAN_NEGATIVE
                ),
                task_relevance_disposition=generic.TASK_NOT_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_NOT_ESTABLISHED,
                training_disposition=generic.TRAINING_NOT_APPLICABLE,
                human_training_excluded=False,
                source_decision_schema=_FORMAL_DECISION_SCHEMA,
                source_decision_sha256=_FORMAL_DECISION_SHA256,
                source_binding_path=(
                    _FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
                ),
            )
        )
    if tuple(observed_ids) != _EVENT_IDS or len(set(observed_ids)) != _EVENT_COUNT:
        _fail("ONE_N0_FORMAL_EVENT_COVERAGE_NOT_EXACT4")
    if tuple(observed_ranks) != _RANKS:
        _fail("ONE_N0_FORMAL_RANK_COVERAGE_NOT_EXACT4")
    if set(observed_ranks) & set(_EXCLUDED_C2_RANKS):
        _fail("ONE_N0_EXCLUDED_C2_RANK_PROJECTED")

    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(),
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )
    _validate_projected_1n0_source_v1(source)
    return source


def project_1n0_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load through the ingestion owner and project its narrow Exact4."""

    try:
        bound = one_n0_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    except one_n0_ingestion_owner.OneN0IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith1N0Error(
            "ONE_N0_INGESTION_OWNER_VALIDATION_FAILED:" + str(error)
        ) from error
    return _project_validated_1n0_binding_v1(bound)


def _prove_1n0_original_unreviewed_prior_v1(
    historical_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove 1N0 is exactly one complete unreviewed historical unit."""

    if isinstance(historical_rows, (str, bytes)):
        _fail("HISTORICAL_ROWS_NOT_SEQUENCE")
    try:
        rows = list(historical_rows)
    except TypeError as error:
        raise CompletedDecisionReconciliationWith1N0Error(
            "HISTORICAL_ROWS_NOT_SEQUENCE"
        ) from error
    if any(
        type(row) is not dict
        or tuple(row) != generic.HISTORICAL_RECONCILIATION_HEADER
        for row in rows
    ):
        _fail("HISTORICAL_ROW_SCHEMA_INVALID")

    expected_ids = set(_EVENT_IDS)
    event_counts = Counter(row["canonical_event_id"] for row in rows)
    missing = [event_id for event_id in _EVENT_IDS if event_counts[event_id] == 0]
    if missing:
        _fail("ONE_N0_HISTORICAL_EVENT_MISSING:" + missing[0])
    duplicate = [
        event_id for event_id in _EVENT_IDS if event_counts[event_id] != 1
    ]
    if duplicate:
        _fail("ONE_N0_HISTORICAL_EVENT_DUPLICATE:" + duplicate[0])

    unit_event_ids = {
        row["canonical_event_id"]
        for row in rows
        if row["raw_review_unit_id"] == _REVIEW_UNIT_ID
    }
    if unit_event_ids != expected_ids:
        _fail("ONE_N0_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4")
    target_rows = [row for row in rows if row["canonical_event_id"] in expected_ids]
    if any(
        row["raw_review_unit_id"] != _REVIEW_UNIT_ID
        or row["raw_priority_rank"] != _HISTORICAL_PRIORITY_RANK
        or row["raw_unit_event_count"] != "4"
        for row in target_rows
    ):
        _fail("ONE_N0_HISTORICAL_IDENTITY_OR_PRIORITY_INVALID")
    if any(
        row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target_rows
    ):
        _fail("ONE_N0_PRIOR_STATE_NOT_EXACT4_UNREVIEWED")
    if len({row["current_review_status"] for row in target_rows}) != 1:
        _fail("ONE_N0_HISTORICAL_REVIEW_UNIT_STATUS_MIXED")
    generic._validate_historical_rows(rows)


def _prove_1n0_rows_unchanged_after_onl_normalization_v1(
    original_rows: Sequence[Mapping[str, str]],
    adapted_rows: Sequence[Mapping[str, str]],
) -> None:
    """Prove the published ONL normalizer changed no 1N0 target field."""

    expected_ids = set(_EVENT_IDS)
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
        _fail("ONE_N0_ORIGINAL_EVENT_SET_NOT_EXACT4")
    if set(adapted_by_event) != expected_ids:
        _fail("ONE_N0_ADAPTED_EVENT_SET_NOT_EXACT4")
    changed = [
        event_id
        for event_id in _EVENT_IDS
        if original_by_event[event_id] != adapted_by_event[event_id]
    ]
    if changed:
        _fail("ONL_ADAPTER_CHANGED_ONE_N0_ROW:" + changed[0])


def load_real_completed_decision_sources_with_1n0_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    """Load the published with-I12 chain and append one 1N0 source."""

    existing = i12_predecessor.load_real_completed_decision_sources_with_i12_v1(
        repo_root
    )
    if (
        len(existing) != 14
        or tuple(len(source.facts) for source in existing)
        != _PREDECESSOR_SOURCE_FACT_COUNTS
    ):
        _fail("PREDECESSOR_I12_SOURCE_COMPOSITION_INVALID")
    existing_event_ids = [
        fact.canonical_event_id for source in existing for fact in source.facts
    ]
    if (
        len(existing_event_ids) != 99
        or len(set(existing_event_ids)) != 99
        or len({source.binding.review_unit_id for source in existing}) != 14
        or len({source.binding.stable_identity for source in existing}) != 14
    ):
        _fail("PREDECESSOR_I12_SOURCE_CHAIN_NOT_EXACT14_99")

    one_n0_source = project_1n0_completed_decision_v1(repo_root=repo_root)
    _validate_projected_1n0_source_v1(one_n0_source)
    one_n0_event_ids = {
        fact.canonical_event_id for fact in one_n0_source.facts
    }
    overlap = one_n0_event_ids & set(existing_event_ids)
    if overlap:
        _fail("ONE_N0_EVENT_COLLISION_WITH_PREDECESSOR:" + sorted(overlap)[0])
    if one_n0_source.binding.review_unit_id in {
        source.binding.review_unit_id for source in existing
    }:
        _fail("ONE_N0_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR")
    if one_n0_source.binding.stable_identity in {
        source.binding.stable_identity for source in existing
    }:
        _fail("ONE_N0_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR")

    sources = (*existing, one_n0_source)
    if (
        len(sources) != 15
        or sources[:-1] != existing
        or tuple(len(source.facts) for source in sources)
        != _SUCCESSOR_SOURCE_FACT_COUNTS
        or len({source.binding.review_unit_id for source in sources}) != 15
        or len({source.binding.stable_identity for source in sources}) != 15
    ):
        _fail("REAL_SOURCE_CHAIN_NOT_EXACT15")
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(event_ids) != 103:
        _fail("REAL_NORMALIZED_FACT_COUNT_NOT_103")
    if len(set(event_ids)) != 103:
        _fail("REAL_NORMALIZED_FACT_EVENT_COLLISION")
    return sources


def reconcile_real_completed_human_decisions_with_1n0_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    """Reconcile Exact15 sources once through the generic owner in memory."""

    historical = generic.load_real_historical_reconciliation_v1(repo_root)
    _prove_1n0_original_unreviewed_prior_v1(historical)
    adapted_historical = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    _prove_1n0_rows_unchanged_after_onl_normalization_v1(
        historical, adapted_historical
    )
    sources = load_real_completed_decision_sources_with_1n0_v1(repo_root)
    return generic.reconcile_completed_human_decisions_v1(
        adapted_historical,
        sources,
    )
