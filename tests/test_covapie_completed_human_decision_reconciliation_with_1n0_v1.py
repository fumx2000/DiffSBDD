from __future__ import annotations

import ast
import copy
from dataclasses import fields, replace
import importlib.util
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1
    as one_n0_ingestion_owner,
)
from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_i12_v1
    as i12_predecessor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_1n0_v1 as subject,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)


ROOT = Path(__file__).resolve().parents[1]
SUBJECT_PATH = (
    ROOT
    / "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_1n0_v1.py"
)
CHECKER_PATH = (
    ROOT
    / "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_1n0_v1.py"
)
EXPECTED_FACT_FIELDS = (
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
FORBIDDEN_RICH_FIELDS = (
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
PREDECESSOR_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4, 4)
SUCCESSOR_COUNTS = (*PREDECESSOR_COUNTS, 4)
CURRENT_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 99,
    "completed_positive_unit_count": 14,
    "completed_negative_event_count": 24,
    "completed_negative_unit_count": 4,
    "completed_total_event_count": 123,
    "completed_total_unit_count": 18,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 215,
    "unreviewed_unit_count": 113,
}
EXPECTED_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 99,
    "completed_positive_unit_count": 14,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 127,
    "completed_total_unit_count": 19,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 211,
    "unreviewed_unit_count": 112,
}


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "one_n0_reconciliation_checker", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return _load_checker()


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return one_n0_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def source(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_1n0_binding_v1(bound)


@pytest.fixture(scope="module")
def sources() -> tuple[generic.NormalizedDecisionSource, ...]:
    return subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)


@pytest.fixture(scope="module")
def historical() -> tuple[dict[str, str], ...]:
    return generic.load_real_historical_reconciliation_v1(ROOT)


@pytest.fixture(scope="module")
def adapted(
    historical: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    return onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )


@pytest.fixture(scope="module")
def current_result() -> generic.ReconciliationResult:
    return i12_predecessor.reconcile_real_completed_human_decisions_with_i12_v1(
        ROOT
    )


@pytest.fixture(scope="module")
def result() -> generic.ReconciliationResult:
    return subject.reconcile_real_completed_human_decisions_with_1n0_v1(ROOT)


def _drift(
    bound: dict[str, object], *path: str, value: object
) -> dict[str, object]:
    clone = copy.deepcopy(bound)
    cursor: object = clone
    for key in path[:-1]:
        assert isinstance(cursor, dict)
        cursor = cursor[key]
    assert isinstance(cursor, dict)
    cursor[path[-1]] = value
    return clone


def _replace_source_fact(
    source: generic.NormalizedDecisionSource,
    index: int,
    **changes: object,
) -> generic.NormalizedDecisionSource:
    facts = list(source.facts)
    facts[index] = replace(facts[index], **changes)
    return replace(source, facts=tuple(facts))


def test_public_api_is_exact4() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWith1N0Error",
        "project_1n0_completed_decision_v1",
        "load_real_completed_decision_sources_with_1n0_v1",
        "reconcile_real_completed_human_decisions_with_1n0_v1",
    )


def test_generic_fact_schema_is_exact11_and_not_forked() -> None:
    observed = tuple(
        field.name for field in fields(generic.NormalizedCompletedDecisionFact)
    )
    assert observed == EXPECTED_FACT_FIELDS
    assert len(observed) == 11
    assert (
        subject.generic.NormalizedCompletedDecisionFact
        is generic.NormalizedCompletedDecisionFact
    )
    assert subject.generic.NormalizedDecisionSource is generic.NormalizedDecisionSource
    assert subject.generic.SourceBinding is generic.SourceBinding
    assert subject.generic.ReconciliationResult is generic.ReconciliationResult


def test_production_runtime_graph_has_no_side_effect_or_validator_bypass() -> None:
    text = SUBJECT_PATH.read_text()
    tree = ast.parse(text)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    assert imports == {
        "covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1",
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_i12_v1",
        "covapie_completed_human_decision_reconciliation_with_onl_v1",
    }
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not calls & {
        "open",
        "write",
        "write_bytes",
        "write_text",
        "mkdir",
        "makedirs",
        "materialize_artifacts",
        "write_artifacts",
        "refresh_census",
        "run",
        "Popen",
        "urlopen",
    }
    assert "validate_1n0_formal_human_decision_v1" not in text


def test_projector_calls_published_ingestion_owner_once(
    monkeypatch: pytest.MonkeyPatch,
    bound: dict[str, object],
) -> None:
    calls = 0

    def load(root: Path) -> dict[str, object]:
        nonlocal calls
        assert root == ROOT
        calls += 1
        return bound

    monkeypatch.setattr(
        subject.one_n0_ingestion_owner,
        "load_frozen_formal_decision_v1",
        load,
    )
    projected = subject.project_1n0_completed_decision_v1(repo_root=ROOT)
    assert calls == 1
    assert len(projected.facts) == 4


def test_projector_wraps_ingestion_owner_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_root: Path) -> dict[str, object]:
        raise one_n0_ingestion_owner.OneN0IngestionSafetyError("owner failure")

    monkeypatch.setattr(
        subject.one_n0_ingestion_owner,
        "load_frozen_formal_decision_v1",
        fail,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_INGESTION_OWNER_VALIDATION_FAILED",
    ):
        subject.project_1n0_completed_decision_v1(repo_root=ROOT)


def test_rich_1n0_task_domain_negative_semantics_are_proven(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_1n0_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    human = formal["human_authorization"]
    chemistry = formal["chemistry_authority_boundary"]
    assert formal["identity"]["review_unit_id"] == (
        one_n0_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    )
    assert formal["identity"]["ligand_component_id"] == "1N0"
    assert human["D1_task_relevance"] == "NOT_RELEVANT"
    assert human["D2_chemistry"] == "UNRESOLVED"
    assert human["D3_reactive_pair"] == "UNRESOLVED"
    assert human["D4_role_candidate"] == "UNRESOLVED"
    assert human["D5_training_use"] == "UNRESOLVED"
    assert chemistry["task_domain_negative"] is True
    assert chemistry["negative_chemistry"] is False
    assert len(events) == 4


def test_rich_narrow_authority_boundary_is_complete(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]
    assert isinstance(formal, dict)
    chemistry = formal["chemistry_authority_boundary"]
    reactive = formal["reactive_pair_boundary"]
    role = formal["role_authority_boundary"]
    training = formal["training_boundary"]
    geometry = formal["PRE_POST_boundary"]
    authority = formal["authority_boundary"]
    assert authority["sample_level_task_relevance_authority_created"] is True
    assert authority["sample_level_task_domain_negative_authority_created"] is True
    assert chemistry["chemistry_positive_authority"] is False
    assert chemistry["chemistry_negative_authority"] is False
    assert chemistry["chemical_warhead_human_authority"] is False
    assert chemistry["reaction_family_authority"] is False
    assert chemistry["warhead_family_authority"] is False
    assert chemistry["warhead_rule_authority"] is False
    assert chemistry["warhead_type_authority"] is False
    assert chemistry["reusable_chemistry_authority"] is False
    assert reactive["reactive_pair_human_authority"] is False
    assert role["role_partition_human_authority"] is False
    assert role["canonical_mask_structural_labels_human_authority"] is False
    assert authority["training_only_exclusion_authority"] is False
    assert training["future_training_admission_candidate"] is False
    assert training["training_admission_created"] is False
    assert geometry["POST_source_evidence_available"] is True
    assert geometry["POST_geometry_training_authority_created"] is False
    assert geometry["PRE_geometry_authority_created"] is False
    assert geometry["PRE_topology_authority_created"] is False
    assert authority["READY_FOR_TRAINING"] is False
    subject._validate_rich_1n0_semantics_v1(bound)


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (
            ("formal", "human_authorization", "D1_task_relevance"),
            "RELEVANT",
            "ONE_N0_D1_D5_DECISIONS_INVALID",
        ),
        (
            ("formal", "human_authorization", "D2_chemistry"),
            "NEGATIVE",
            "ONE_N0_D1_D5_DECISIONS_INVALID",
        ),
        (
            ("formal", "human_authorization", "D3_reactive_pair"),
            "CONFIRM_OBSERVED_PAIR",
            "ONE_N0_D1_D5_DECISIONS_INVALID",
        ),
        (
            ("formal", "human_authorization", "D4_role_candidate"),
            "SELECT_CANDIDATE_0",
            "ONE_N0_D1_D5_DECISIONS_INVALID",
        ),
        (
            ("formal", "human_authorization", "D5_training_use"),
            "EXCLUDE_FROM_TRAINING_ONLY",
            "ONE_N0_D1_D5_DECISIONS_INVALID",
        ),
        (
            ("formal", "chemistry_authority_boundary", "negative_chemistry"),
            True,
            "ONE_N0_RICH_NEGATIVE_AUTHORITY_BOUNDARY_INVALID",
        ),
        (
            ("formal", "reactive_pair_boundary", "reactive_pair_human_authority"),
            True,
            "ONE_N0_RICH_NEGATIVE_AUTHORITY_BOUNDARY_INVALID",
        ),
        (
            ("formal", "role_authority_boundary", "role_partition_human_authority"),
            True,
            "ONE_N0_RICH_NEGATIVE_AUTHORITY_BOUNDARY_INVALID",
        ),
        (
            ("formal", "training_boundary", "training_admission_created"),
            True,
            "ONE_N0_RICH_NEGATIVE_AUTHORITY_BOUNDARY_INVALID",
        ),
    ),
)
def test_projector_rejects_rich_semantic_or_authority_drift(
    bound: dict[str, object],
    path: tuple[str, ...],
    value: object,
    token: str,
) -> None:
    drifted = _drift(bound, *path, value=value)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match=token,
    ):
        subject._project_validated_1n0_binding_v1(drifted)


def test_exact4_event_identity_and_target_ranks_are_frozen(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert one_n0_ingestion_owner.EXPECTED_RANKS == (775, 776, 778, 780)
    assert one_n0_ingestion_owner.EXCLUDED_C2_RANKS == (777, 779)
    assert tuple(fact.canonical_event_id for fact in source.facts) == tuple(
        sorted(one_n0_ingestion_owner.EXPECTED_EVENT_IDS)
    )
    assert len({fact.canonical_event_id for fact in source.facts}) == 4
    assert all(fact.canonical_event_id.endswith("1N0:C16") for fact in source.facts)


@pytest.mark.parametrize("excluded_rank", (777, 779))
def test_excluded_c2_rank_is_rejected_before_projection(
    bound: dict[str, object], excluded_rank: int
) -> None:
    drifted = copy.deepcopy(bound)
    event = drifted["formal"]["event_level_human_decisions"][0]  # type: ignore[index]
    event["scaleup_rank"] = excluded_rank
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_RICH_EVENT_SEMANTICS_INVALID",
    ):
        subject._project_validated_1n0_binding_v1(drifted)


def test_narrow_projection_exact4_and_namespace_transition(
    bound: dict[str, object],
    source: generic.NormalizedDecisionSource,
) -> None:
    ingestion_binding = bound["formal_decision_binding"]
    assert isinstance(ingestion_binding, dict)
    assert ingestion_binding["namespace"] == "project_parent_relative"
    assert source.binding.path_namespace == "repository_parent_relative"
    assert source.binding.byte_count == 26236
    assert source.binding.sha256 == (
        "45c337b2b8e0f85ea7a06eb16bd5f55ec729429285226a77bbb0c4a2f1301a34"
    )
    assert source.binding.schema_version == (
        "covapie_1n0_exact4_task_domain_negative_formal_human_decision_v1"
    )
    assert source.binding.review_unit_id == (
        "COVAPIE_BULK_REVIEW_UNIT_80FE8023FD901B01"
    )
    for fact in source.facts:
        assert fact.human_review_completed is True
        assert (
            fact.legacy_completed_review_status
            == generic.COMPLETED_HUMAN_NEGATIVE
        )
        assert fact.task_relevance_disposition == generic.TASK_NOT_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_NOT_ESTABLISHED
        assert fact.training_disposition == generic.TRAINING_NOT_APPLICABLE
        assert fact.human_training_excluded is False
        assert fact.source_decision_sha256 == source.binding.sha256
        assert fact.source_binding_path == source.binding.source_path


def test_raw_pair_role_mask_chemistry_and_training_fields_do_not_leak(
    source: generic.NormalizedDecisionSource,
) -> None:
    actual = tuple(
        field.name for field in fields(generic.NormalizedCompletedDecisionFact)
    )
    assert actual == EXPECTED_FACT_FIELDS
    assert not set(actual) & set(FORBIDDEN_RICH_FIELDS)
    for fact in source.facts:
        assert all(not hasattr(fact, name) for name in FORBIDDEN_RICH_FIELDS)
    with pytest.raises(TypeError):
        generic.NormalizedCompletedDecisionFact(
            **{name: getattr(source.facts[0], name) for name in actual},
            role_profile="FORBIDDEN",
        )


def test_generic_owner_accepts_not_established_for_not_relevant(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert generic.CHEMISTRY_NOT_ESTABLISHED != generic.CHEMISTRY_NEGATIVE
    assert generic.TRAINING_NOT_APPLICABLE != generic.TRAINING_EXCLUDE
    for fact in source.facts:
        generic._validate_fact(fact, source.binding)


@pytest.mark.parametrize(
    "changes",
    (
        {"chemistry_disposition": generic.CHEMISTRY_NEGATIVE},
        {"training_disposition": generic.TRAINING_EXCLUDE},
        {
            "training_disposition": generic.TRAINING_EXCLUDE,
            "human_training_excluded": True,
        },
        {"human_training_excluded": True},
    ),
)
def test_expected_1n0_source_rejects_negative_or_training_exclusion_projection(
    source: generic.NormalizedDecisionSource,
    changes: dict[str, object],
) -> None:
    drifted = _replace_source_fact(source, 0, **changes)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_SOURCE_PROJECTION_INVALID",
    ):
        subject._validate_projected_1n0_source_v1(drifted)


def test_source_binding_sha_drift_is_rejected(bound: dict[str, object]) -> None:
    drifted = copy.deepcopy(bound)
    drifted["formal_decision_binding"]["SHA256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_FORMAL_DECISION_BINDING_INVALID",
    ):
        subject._project_validated_1n0_binding_v1(drifted)


def test_generic_schema_drift_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DriftedFact:
        __dataclass_fields__ = {"canonical_event_id": object()}

    monkeypatch.setattr(subject.generic, "NormalizedCompletedDecisionFact", DriftedFact)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11",
    ):
        subject._prove_generic_fact_schema_v1()


def test_historical_exact4_rank18_is_complete_and_unreviewed(
    historical: tuple[dict[str, str], ...],
) -> None:
    subject._prove_1n0_original_unreviewed_prior_v1(historical)
    ids = set(one_n0_ingestion_owner.EXPECTED_EVENT_IDS)
    rows = [row for row in historical if row["canonical_event_id"] in ids]
    assert len(rows) == 4
    assert {row["raw_review_unit_id"] for row in rows} == {
        one_n0_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    }
    assert {row["raw_priority_rank"] for row in rows} == {"18"}
    assert {row["raw_unit_event_count"] for row in rows} == {"4"}
    assert {row["current_review_status"] for row in rows} == {
        generic.CURRENTLY_UNREVIEWED
    }
    assert {row["calibration_eligible"] for row in rows} == {"true"}
    assert {row["calibration_exclusion_reason"] for row in rows} == {""}


def test_historical_missing_event_is_rejected(
    historical: tuple[dict[str, str], ...],
) -> None:
    missing = tuple(
        row
        for row in historical
        if row["canonical_event_id"]
        != one_n0_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_HISTORICAL_EVENT_MISSING",
    ):
        subject._prove_1n0_original_unreviewed_prior_v1(missing)


def test_historical_duplicate_event_is_rejected(
    historical: tuple[dict[str, str], ...],
) -> None:
    row = next(
        row
        for row in historical
        if row["canonical_event_id"]
        == one_n0_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    duplicate = (*historical, dict(row))
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_HISTORICAL_EVENT_DUPLICATE",
    ):
        subject._prove_1n0_original_unreviewed_prior_v1(duplicate)


def test_historical_partial_or_extra_review_unit_is_rejected(
    historical: tuple[dict[str, str], ...],
) -> None:
    drifted = [dict(row) for row in historical]
    extra = next(
        row
        for row in drifted
        if row["canonical_event_id"]
        not in one_n0_ingestion_owner.EXPECTED_EVENT_IDS
    )
    extra["raw_review_unit_id"] = one_n0_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4",
    ):
        subject._prove_1n0_original_unreviewed_prior_v1(drifted)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        (
            "raw_priority_rank",
            "19",
            "ONE_N0_HISTORICAL_IDENTITY_OR_PRIORITY_INVALID",
        ),
        (
            "current_review_status",
            generic.COMPLETED_HUMAN_NEGATIVE,
            "ONE_N0_PRIOR_STATE_NOT_EXACT4_UNREVIEWED",
        ),
        (
            "calibration_eligible",
            "false",
            "ONE_N0_PRIOR_STATE_NOT_EXACT4_UNREVIEWED",
        ),
    ),
)
def test_historical_wrong_priority_or_prior_state_is_rejected(
    historical: tuple[dict[str, str], ...],
    field: str,
    value: str,
    token: str,
) -> None:
    drifted = [dict(row) for row in historical]
    row = next(
        row
        for row in drifted
        if row["canonical_event_id"]
        == one_n0_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    row[field] = value
    with pytest.raises(subject.CompletedDecisionReconciliationWith1N0Error, match=token):
        subject._prove_1n0_original_unreviewed_prior_v1(drifted)


def test_onl_normalization_changes_zero_1n0_rows(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    subject._prove_1n0_rows_unchanged_after_onl_normalization_v1(
        historical, adapted
    )
    ids = set(one_n0_ingestion_owner.EXPECTED_EVENT_IDS)
    before = {
        row["canonical_event_id"]: row
        for row in historical
        if row["canonical_event_id"] in ids
    }
    after = {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in ids
    }
    assert before == after


def test_onl_target_mutation_is_rejected(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    changed = [dict(row) for row in adapted]
    row = next(
        row
        for row in changed
        if row["canonical_event_id"]
        == one_n0_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["changed"]'
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONL_ADAPTER_CHANGED_ONE_N0_ROW",
    ):
        subject._prove_1n0_rows_unchanged_after_onl_normalization_v1(
            historical, changed
        )


def test_source_chain_14_to_15_is_append_only_and_collision_free(
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    existing = i12_predecessor.load_real_completed_decision_sources_with_i12_v1(
        ROOT
    )
    assert len(existing) == 14
    assert tuple(len(source.facts) for source in existing) == PREDECESSOR_COUNTS
    assert sum(len(source.facts) for source in existing) == 99
    assert len(sources) == 15
    assert sources[:-1] == existing
    assert tuple(len(source.facts) for source in sources) == SUCCESSOR_COUNTS
    event_ids = [fact.canonical_event_id for source in sources for fact in source.facts]
    assert len(event_ids) == len(set(event_ids)) == 103
    assert len({source.binding.review_unit_id for source in sources}) == 15
    assert len({source.binding.stable_identity for source in sources}) == 15


def test_predecessor_source_count_drift_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = i12_predecessor.load_real_completed_decision_sources_with_i12_v1(
        ROOT
    )
    monkeypatch.setattr(
        subject.i12_predecessor,
        "load_real_completed_decision_sources_with_i12_v1",
        lambda _root: existing[:-1],
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="PREDECESSOR_I12_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)


def test_predecessor_fact_count_drift_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = list(
        i12_predecessor.load_real_completed_decision_sources_with_i12_v1(ROOT)
    )
    existing[0] = replace(existing[0], facts=existing[0].facts[:-1])
    monkeypatch.setattr(
        subject.i12_predecessor,
        "load_real_completed_decision_sources_with_i12_v1",
        lambda _root: tuple(existing),
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="PREDECESSOR_I12_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)


def test_event_collision_with_predecessor_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
) -> None:
    existing = list(
        i12_predecessor.load_real_completed_decision_sources_with_i12_v1(ROOT)
    )
    existing[0] = _replace_source_fact(
        existing[0], 0, canonical_event_id=source.facts[0].canonical_event_id
    )
    monkeypatch.setattr(
        subject.i12_predecessor,
        "load_real_completed_decision_sources_with_i12_v1",
        lambda _root: tuple(existing),
    )
    monkeypatch.setattr(
        subject,
        "project_1n0_completed_decision_v1",
        lambda *, repo_root: source,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_EVENT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)


def test_review_unit_collision_with_predecessor_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
) -> None:
    existing = list(
        i12_predecessor.load_real_completed_decision_sources_with_i12_v1(ROOT)
    )
    existing[0] = replace(
        existing[0],
        binding=replace(
            existing[0].binding,
            review_unit_id=source.binding.review_unit_id,
        ),
    )
    monkeypatch.setattr(
        subject.i12_predecessor,
        "load_real_completed_decision_sources_with_i12_v1",
        lambda _root: tuple(existing),
    )
    monkeypatch.setattr(
        subject,
        "project_1n0_completed_decision_v1",
        lambda *, repo_root: source,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)


def test_stable_source_collision_with_predecessor_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
) -> None:
    existing = list(
        i12_predecessor.load_real_completed_decision_sources_with_i12_v1(ROOT)
    )
    existing[0] = replace(
        existing[0],
        binding=replace(
            existing[0].binding,
            source_path=source.binding.source_path,
            path_namespace=source.binding.path_namespace,
            sha256=source.binding.sha256,
        ),
    )
    monkeypatch.setattr(
        subject.i12_predecessor,
        "load_real_completed_decision_sources_with_i12_v1",
        lambda _root: tuple(existing),
    )
    monkeypatch.setattr(
        subject,
        "project_1n0_completed_decision_v1",
        lambda *, repo_root: source,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith1N0Error,
        match="ONE_N0_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)


def test_reconciliation_summary_and_exact4_transition_are_exact(
    current_result: generic.ReconciliationResult,
    result: generic.ReconciliationResult,
) -> None:
    assert current_result.review_summary == CURRENT_SUMMARY
    assert result.review_summary == EXPECTED_SUMMARY
    ids = set(one_n0_ingestion_owner.EXPECTED_EVENT_IDS)
    before = {
        row["canonical_event_id"]: row for row in current_result.reconciled_rows
    }
    after = {row["canonical_event_id"]: row for row in result.reconciled_rows}
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == ids
    expected_authority = json.dumps(
        [one_n0_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()],
        sort_keys=True,
        separators=(",", ":"),
    )
    for event_id in ids:
        assert before[event_id]["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        assert (
            after[event_id]["current_review_status"]
            == generic.COMPLETED_HUMAN_NEGATIVE
        )
        assert after[event_id]["calibration_eligible"] == "false"
        assert (
            after[event_id]["calibration_exclusion_reason"]
            == generic.COMPLETED_HUMAN_NEGATIVE
        )
        assert after[event_id]["current_status_authority_sources_json"] == (
            expected_authority
        )


def test_every_non_target_row_is_field_identical(
    current_result: generic.ReconciliationResult,
    result: generic.ReconciliationResult,
) -> None:
    target = set(one_n0_ingestion_owner.EXPECTED_EVENT_IDS)
    before = {
        row["canonical_event_id"]: row for row in current_result.reconciled_rows
    }
    after = {row["canonical_event_id"]: row for row in result.reconciled_rows}
    assert all(before[event_id] == after[event_id] for event_id in set(before) - target)


def test_source_order_is_semantically_deterministic(
    sources: tuple[generic.NormalizedDecisionSource, ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    normal = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_result = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    assert normal == reversed_result


def test_production_pipeline_delegates_to_generic_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    historical = generic.load_real_historical_reconciliation_v1(ROOT)
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    sources = subject.load_real_completed_decision_sources_with_1n0_v1(ROOT)
    expected = generic.reconcile_completed_human_decisions_v1(adapted, sources)

    def load_historical(root: Path):
        calls.append("historical")
        return historical

    def adapt_rows(rows: object):
        calls.append("onl")
        assert rows is historical
        return adapted

    def load_sources(root: Path):
        calls.append("sources")
        return sources

    def reconcile(rows: object, observed_sources: object):
        calls.append("generic")
        assert rows is adapted
        assert observed_sources is sources
        return expected

    monkeypatch.setattr(
        subject.generic,
        "load_real_historical_reconciliation_v1",
        load_historical,
    )
    monkeypatch.setattr(
        subject.onl_successor,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        adapt_rows,
    )
    monkeypatch.setattr(
        subject,
        "load_real_completed_decision_sources_with_1n0_v1",
        load_sources,
    )
    monkeypatch.setattr(
        subject.generic,
        "reconcile_completed_human_decisions_v1",
        reconcile,
    )
    assert subject.reconcile_real_completed_human_decisions_with_1n0_v1(ROOT) is expected
    assert calls == ["historical", "onl", "sources", "generic"]


def test_checker_profiles_accept_candidate_and_tracked_clean(checker) -> None:
    expected = set(checker.EXACT4_PATHS)
    assert checker._classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple(sorted("?? " + path for path in expected)),
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    ) == checker._CANDIDATE_UNTRACKED
    assert checker._classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    ) == checker._TRACKED_CLEAN


def test_candidate_lifecycle_relation_is_exact_baseline(checker) -> None:
    assert checker._validate_repository_relation_facts(
        profile=checker._CANDIDATE_UNTRACKED,
        branch="main",
        head=checker.BASELINE_COMMIT,
        origin=checker.BASELINE_COMMIT,
        relation="0\t0",
    ) == (0, 0)


def test_committed_unpushed_lifecycle_is_supported(checker) -> None:
    successor = "a" * 40
    assert checker._validate_repository_relation_facts(
        profile=checker._TRACKED_CLEAN,
        branch="main",
        head=successor,
        origin=checker.BASELINE_COMMIT,
        relation="1\t0",
        baseline_is_ancestor=True,
        commit_count=1,
        head_parents=(checker.BASELINE_COMMIT,),
        changed_paths=set(checker.EXACT4_PATHS),
    ) == (1, 0)


def test_published_lifecycle_is_supported_without_successor_sha(checker) -> None:
    successor = "b" * 40
    assert successor != checker.BASELINE_COMMIT
    assert checker._validate_repository_relation_facts(
        profile=checker._TRACKED_CLEAN,
        branch="main",
        head=successor,
        origin=successor,
        relation="0\t0",
        baseline_is_ancestor=True,
        commit_count=1,
        head_parents=(checker.BASELINE_COMMIT,),
        changed_paths=set(checker.EXACT4_PATHS),
    ) == (0, 0)


@pytest.mark.parametrize(
    "mutation",
    ("extra", "staged", "modified", "partial", "mixed"),
)
def test_checker_rejects_non_exact_candidate_profiles(
    checker, mutation: str
) -> None:
    expected = set(checker.EXACT4_PATHS)
    tracked: set[str] = set()
    untracked = set(expected)
    status = tuple(sorted("?? " + path for path in expected))
    working: tuple[str, ...] = ()
    cached: tuple[str, ...] = ()
    if mutation == "extra":
        untracked.add("extra.txt")
        status = (*status, "?? extra.txt")
    elif mutation == "staged":
        cached = (checker.EXACT4_PATHS[0],)
    elif mutation == "modified":
        working = ("tracked.py",)
    elif mutation == "partial":
        untracked.remove(checker.EXACT4_PATHS[0])
        status = tuple(
            line for line in status if checker.EXACT4_PATHS[0] not in line
        )
    else:
        tracked.add(checker.EXACT4_PATHS[0])
        untracked.remove(checker.EXACT4_PATHS[0])
        status = tuple(
            line for line in status if checker.EXACT4_PATHS[0] not in line
        )
    with pytest.raises(
        ValueError,
        match="REPOSITORY_PROFILE_NOT_EXACT_CANDIDATE_UNTRACKED_OR_TRACKED_CLEAN",
    ):
        checker._classify_repository_profile(
            expected_paths=checker.EXACT4_PATHS,
            tracked_paths=tracked,
            ordinary_untracked=untracked,
            status_lines=status,
            working_tree_diff_paths=working,
            cached_diff_paths=cached,
        )


def test_checker_runs_live_semantic_lifecycle_and_b4_gates(checker) -> None:
    report = checker.run_check_v1(ROOT)
    assert report["status"] == "PASS"
    assert report["repository"]["candidate_file_count"] == 4
    assert report["repository"]["lifecycle"] in {
        checker._CANDIDATE_UNTRACKED,
        checker._TRACKED_CLEAN,
    }
    assert report["architecture"]["public_api"] == checker.EXPECTED_PUBLIC_API
    assert report["projection"]["generic_fact_fields"] == EXPECTED_FACT_FIELDS
    assert report["projection"]["rich_field_leakage_count"] == 0
    assert report["predecessor_source_count"] == 14
    assert report["predecessor_fact_count"] == 99
    assert report["successor_source_count"] == 15
    assert report["successor_fact_count"] == 103
    assert report["event_collisions"] == 0
    assert report["one_n0_rows_changed_by_onl"] == 0
    assert report["target_exact4_changed"] is True
    assert report["non_target_rows_changed"] is False
    assert report["review_summary"] == EXPECTED_SUMMARY
    assert report["b4_core"]["new_semantic_exact_posix_mode_occurrence_count"] == 0
    assert report["b4_core"]["new_ambiguous_mode_occurrence_count"] == 0
    assert report["b4_core"]["global_canonical_task_count"] == 5
    assert report["b4_core"]["B3_present"] is True
    assert report["b4_core"]["sixth_task_present"] is False
    assert report["reconciliation_data_outputs_created"] == 0
    assert report["training_started"] is False
    assert report["ready_for_training"] is False


def test_exact4_inventory_contains_no_materialized_or_training_artifact(
    checker,
) -> None:
    assert len(checker.EXACT4_PATHS) == 4
    assert all(
        not path.startswith(("data/", "covapie-state/"))
        for path in checker.EXACT4_PATHS
    )
    assert all("manifest" not in path for path in checker.EXACT4_PATHS)
    assert all(
        "census" not in path and "queue" not in path
        for path in checker.EXACT4_PATHS
    )
    assert all(not path.endswith((".csv", ".json")) for path in checker.EXACT4_PATHS)
