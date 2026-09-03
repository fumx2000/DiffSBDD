from __future__ import annotations

import ast
import copy
from dataclasses import make_dataclass, replace
import hashlib
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_gve_v1 as subject,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_sr2_v1
    as sr2_predecessor,
)
from covalent_ext import (
    covapie_gve_completed_decision_ingestion_and_task_label_availability_v1
    as gve_ingestion_owner,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_gve_v1.py"
)
PREDECESSOR = (
    ROOT
    / "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_sr2_v1.py"
)
INGESTION_OWNER = (
    ROOT
    / "src/covalent_ext/"
    "covapie_gve_completed_decision_ingestion_and_task_label_availability_v1.py"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithGVEError",
    "project_gve_completed_decision_v1",
    "load_real_completed_decision_sources_with_gve_v1",
    "reconcile_real_completed_human_decisions_with_gve_v1",
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
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 143,
    "completed_total_unit_count": 23,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 195,
    "unreviewed_unit_count": 108,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 32,
    "completed_negative_unit_count": 6,
    "completed_total_event_count": 147,
    "completed_total_unit_count": 24,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 191,
    "unreviewed_unit_count": 107,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return gve_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def projection(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_gve_binding_v1(bound)


@pytest.fixture(scope="module")
def source_chains() -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    after = subject.load_real_completed_decision_sources_with_gve_v1(ROOT)
    return after[:-1], after


@pytest.fixture(scope="module")
def reconciliations(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> tuple[generic.ReconciliationResult, generic.ReconciliationResult]:
    before_sources, after_sources = source_chains
    historical = generic.load_real_historical_reconciliation_v1(ROOT)
    adapted = (
        sr2_predecessor.gd1_predecessor.four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    before = generic.reconcile_completed_human_decisions_v1(
        adapted, before_sources
    )
    after = generic.reconcile_completed_human_decisions_v1(
        adapted, after_sources
    )
    return before, after


def _mutate_formal(
    bound: dict[str, object], section: str, key: str, value: object
) -> dict[str, object]:
    candidate = copy.deepcopy(bound)
    formal = candidate["formal"]
    assert isinstance(formal, dict)
    target = formal[section]
    assert isinstance(target, dict)
    target[key] = value
    return candidate


def _replace_source_fact(
    source: generic.NormalizedDecisionSource, **changes: object
) -> generic.NormalizedDecisionSource:
    fact = replace(source.facts[0], **changes)
    return replace(source, facts=(fact, *source.facts[1:]))


def test_public_api_direct_dependencies_and_no_materializer() -> None:
    assert subject.__all__ == EXPECTED_PUBLIC_API
    tree = ast.parse(SOURCE.read_bytes())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    assert imported == {
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_sr2_v1",
        "covapie_gve_completed_decision_ingestion_and_task_label_availability_v1",
    }
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not calls & {
        "write",
        "write_bytes",
        "write_text",
        "mkdir",
        "materialize_artifacts_v1",
        "refresh_census",
        "run",
        "Popen",
    }
    assert not any(
        token in subject.__all__
        for token in ("write", "materialize", "cache", "registry")
    )


def test_published_predecessor_and_ingestion_owner_identities() -> None:
    assert PREDECESSOR.stat().st_size == 37793
    assert _sha(PREDECESSOR) == (
        "19401cb0aeec3c138aace9093b58dfd61386bd87395a1b53cf83164583ffbe93"
    )
    assert INGESTION_OWNER.stat().st_size == 92981
    assert _sha(INGESTION_OWNER) == (
        "c2266d58001cdcbac9f9f7ba4a2a4142d72e97a35f7ed132e694a91b79a2ea0a"
    )


def test_rich_gve_exact4_prevalidation(bound: dict[str, object]) -> None:
    events = subject._validate_rich_gve_semantics_v1(bound)
    assert tuple(row["canonical_event_id"] for row in events) == (
        gve_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert tuple(row["scaleup_rank"] for row in events) == (295, 296, 480, 986)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    inherited = formal["inherited_human_decision"]
    assert isinstance(inherited, dict)
    assert [inherited[f"D{index}_{name}"] for index, name in (
        (1, "task_relevance"),
        (2, "chemistry"),
        (3, "reactive_pair"),
        (4, "role_candidate"),
        (5, "training_use"),
    )] == [
        "NOT_RELEVANT",
        "POSITIVE",
        "CONFIRM_OBSERVED_PAIR",
        "UNRESOLVED",
        "NOT_APPLICABLE",
    ]
    assert bound["formal_validator_provenance_identity_only"] is True
    for key in (
        "formal_validator_imported",
        "formal_validator_parsed",
        "formal_validator_executed",
        "formal_validator_subprocessed",
        "formal_validator_runtime_dependency",
    ):
        assert bound[key] is False


def test_generic_exact11_projection_and_namespace_translation(
    projection: generic.NormalizedDecisionSource,
) -> None:
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == (
        EXPECTED_FACT_FIELDS
    )
    assert len(projection.facts) == 4
    assert projection.binding.path_namespace == "repository_parent_relative"
    assert projection.binding.source_path == (
        gve_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
    )
    assert projection.binding.byte_count == 26844
    assert projection.binding.sha256 == (
        "0df008d9fe2e142120a22ce6797aaf633725d4627eb6ca8e1be9f869ad0896e2"
    )
    assert projection.binding.schema_version == (
        "covapie_gve_exact4_formal_human_decision_v1"
    )
    for fact in projection.facts:
        assert tuple(fact.__dataclass_fields__) == EXPECTED_FACT_FIELDS
        assert fact.human_review_completed is True
        assert fact.legacy_completed_review_status == "COMPLETED_HUMAN_NEGATIVE"
        assert fact.task_relevance_disposition == "NOT_RELEVANT"
        assert fact.chemistry_disposition == "POSITIVE"
        assert fact.training_disposition == "NOT_APPLICABLE"
        assert fact.human_training_excluded is False
        generic._validate_fact(fact, projection.binding)


def test_completed_lane_does_not_leak_to_generic_legacy_status(
    bound: dict[str, object], projection: generic.NormalizedDecisionSource
) -> None:
    lane = bound["completed_lane_validation"]
    assert isinstance(lane, dict)
    assert lane["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    assert {
        fact.legacy_completed_review_status for fact in projection.facts
    } == {"COMPLETED_HUMAN_NEGATIVE"}
    assert all(
        not hasattr(fact, field)
        for fact in projection.facts
        for field in subject._FORBIDDEN_GENERIC_FACT_ATTRIBUTES
    )


def test_source_chain_is_append_only_exact20_123(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, after = source_chains
    assert len(before) == 19
    assert len(after) == 20
    assert after[:-1] == before
    assert tuple(len(source.facts) for source in before) == (
        8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4
    )
    assert tuple(len(source.facts) for source in after) == (
        8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4
    )
    assert sum(len(source.facts) for source in before) == 119
    assert sum(len(source.facts) for source in after) == 123
    assert len({source.binding.stable_identity for source in after}) == 20
    assert len(
        {fact.canonical_event_id for source in after for fact in source.facts}
    ) == 123
    assert after[-1].binding.review_unit_id == (
        gve_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    )


def test_historical_rank23_exact4_and_no_1xd3_collision(
    reconciliations: tuple[
        generic.ReconciliationResult, generic.ReconciliationResult
    ],
) -> None:
    before, _after = reconciliations
    subject._prove_gve_predecessor_historical_state_v1(before.reconciled_rows)
    target = [
        row
        for row in before.reconciled_rows
        if row["raw_review_unit_id"] == gve_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    ]
    assert len(target) == 4
    assert {row["canonical_event_id"] for row in target} == set(
        gve_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert {row["raw_priority_rank"] for row in target} == {"23"}
    assert {row["raw_unit_event_count"] for row in target} == {"4"}
    assert not [
        row
        for row in before.reconciled_rows
        if ":1XD3:" in row["canonical_event_id"]
        and ":GVE:" in row["canonical_event_id"]
    ]


def test_reconciliation_summary_exact_delta_and_authority(
    reconciliations: tuple[
        generic.ReconciliationResult, generic.ReconciliationResult
    ],
) -> None:
    before, after = reconciliations
    assert before.review_summary == BEFORE_SUMMARY
    assert after.review_summary == AFTER_SUMMARY
    subject._validate_reconciliation_delta_v1(before, after)
    target_ids = set(gve_ingestion_owner.EXPECTED_EVENT_IDS)
    changed = []
    unchanged = 0
    expected_authority = generic._canonical_json(
        [gve_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()]
    )
    for old, new in zip(
        before.reconciled_rows, after.reconciled_rows, strict=True
    ):
        fields = {key for key in old if old[key] != new[key]}
        if old["canonical_event_id"] in target_ids:
            changed.append(fields)
            assert new["current_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
            assert new["current_status_authority_sources_json"] == expected_authority
            assert new["calibration_eligible"] == "false"
            assert new["calibration_exclusion_reason"] == (
                "COMPLETED_HUMAN_NEGATIVE"
            )
        else:
            assert old == new
            unchanged += 1
    assert len(changed) == 4
    assert unchanged == 334
    assert set.union(*changed) == {
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    }
    assert len(after.source_bindings) == 20
    assert len(after.normalized_facts) == 123


def test_public_reconciler_returns_validated_in_memory_result(
    monkeypatch: pytest.MonkeyPatch,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
    reconciliations: tuple[
        generic.ReconciliationResult, generic.ReconciliationResult
    ],
) -> None:
    before, expected_after = reconciliations
    _before_sources, after_sources = source_chains
    monkeypatch.setattr(
        sr2_predecessor,
        "reconcile_real_completed_human_decisions_with_sr2_v1",
        lambda _root: before,
    )
    monkeypatch.setattr(
        subject,
        "load_real_completed_decision_sources_with_gve_v1",
        lambda _root: after_sources,
    )
    actual = subject.reconcile_real_completed_human_decisions_with_gve_v1(ROOT)
    assert actual == expected_after
    assert not hasattr(actual, "write")
    assert not hasattr(actual, "materialize")


@pytest.mark.parametrize(
    ("section", "key", "value", "token"),
    (
        ("inherited_human_decision", "D1_task_relevance", "RELEVANT", "GVE_D1_D5"),
        ("inherited_human_decision", "D2_chemistry", "NEGATIVE", "GVE_D1_D5"),
        ("inherited_human_decision", "D3_reactive_pair", "REJECT", "GVE_D1_D5"),
        ("inherited_human_decision", "D4_role_candidate", "SELECT_CANDIDATE_0", "GVE_D1_D5"),
        ("inherited_human_decision", "D5_training_use", "INCLUDE", "GVE_D1_D5"),
        ("sample_reactive_pair_authority", "ligand_reactive_atom", "CA", "GVE_SG_CB"),
        ("sample_role_boundary", "role_partition_sample_authority", True, "GVE_UNRESOLVED_ROLE"),
        ("training_boundary", "human_training_excluded", True, "GVE_TRAINING_NOT_APPLICABLE"),
        ("training_boundary", "future_training_admission_candidate", True, "GVE_TRAINING_NOT_APPLICABLE"),
        ("PRE_boundary", "PRE_status", "PRE_REACTION_RESOLVED", "GVE_PRE_UNRESOLVED"),
        ("downstream_operations", "census_refresh", True, "GVE_UNAUTHORIZED_DOWNSTREAM"),
    ),
)
def test_rich_semantic_drift_fails_closed(
    bound: dict[str, object],
    section: str,
    key: str,
    value: object,
    token: str,
) -> None:
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError, match=token
    ):
        subject._validate_rich_gve_semantics_v1(
            _mutate_formal(bound, section, key, value)
        )


def test_formal_binding_schema_sha_and_namespace_drift_fail_closed(
    bound: dict[str, object], projection: generic.NormalizedDecisionSource
) -> None:
    wrong_schema = copy.deepcopy(bound)
    formal = wrong_schema["formal"]
    assert isinstance(formal, dict)
    formal["schema_version"] = "wrong"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_FORMAL_COMPLETION_OR_SEMANTICS_INVALID",
    ):
        subject._validate_rich_gve_semantics_v1(wrong_schema)

    wrong_sha = copy.deepcopy(bound)
    binding = wrong_sha["formal_decision_binding"]
    assert isinstance(binding, dict)
    binding["SHA256"] = "0" * 64
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_FORMAL_DECISION_BINDING_INVALID",
    ):
        subject._project_validated_gve_binding_v1(wrong_sha)

    wrong_namespace = replace(
        projection.binding, path_namespace="project_parent_relative"
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_SOURCE_PROJECTION_IDENTITY_INVALID",
    ):
        subject._validate_projected_gve_source_v1(
            replace(projection, binding=wrong_namespace)
        )


def test_missing_fifth_and_rank_drift_fail_closed(bound: dict[str, object]) -> None:
    missing = copy.deepcopy(bound)
    formal = missing["formal"]
    assert isinstance(formal, dict)
    events = formal["event_level_formal_decisions"]
    assert isinstance(events, list)
    events.pop()
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_FORMAL_EVENT_COVERAGE_NOT_EXACT4",
    ):
        subject._validate_rich_gve_semantics_v1(missing)

    fifth = copy.deepcopy(bound)
    formal = fifth["formal"]
    assert isinstance(formal, dict)
    events = formal["event_level_formal_decisions"]
    assert isinstance(events, list)
    events.append(copy.deepcopy(events[-1]))
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_FORMAL_EVENT_COVERAGE_NOT_EXACT4",
    ):
        subject._validate_rich_gve_semantics_v1(fifth)

    rank = copy.deepcopy(bound)
    formal = rank["formal"]
    assert isinstance(formal, dict)
    identity = formal["identity"]
    assert isinstance(identity, dict)
    identity["scaleup_ranks"] = [295, 296, 480, 985]
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_FORMAL_IDENTITY_NOT_EXACT4",
    ):
        subject._validate_rich_gve_semantics_v1(rank)


@pytest.mark.parametrize(
    ("changes", "token"),
    (
        ({"legacy_completed_review_status": "COMPLETED_TASK_DOMAIN_NEGATIVE"}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"task_relevance_disposition": generic.TASK_RELEVANT}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"chemistry_disposition": generic.CHEMISTRY_NOT_ESTABLISHED}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"chemistry_disposition": generic.CHEMISTRY_NEGATIVE}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"training_disposition": generic.TRAINING_INCLUDE}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"training_disposition": generic.TRAINING_EXCLUDE}, "GVE_SOURCE_PROJECTION_INVALID"),
        ({"human_training_excluded": True}, "GVE_SOURCE_PROJECTION_INVALID"),
    ),
)
def test_generic_projection_semantic_drift_fails_closed(
    projection: generic.NormalizedDecisionSource,
    changes: dict[str, object],
    token: str,
) -> None:
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError, match=token
    ):
        subject._validate_projected_gve_source_v1(
            _replace_source_fact(projection, **changes)
        )


def test_generic_schema_extra_rich_field_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fields = [(name, object) for name in EXPECTED_FACT_FIELDS]
    fields.append(("protein_reactive_atom", object))
    monkeypatch.setattr(
        generic, "NormalizedCompletedDecisionFact", make_dataclass("BadFact", fields)
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11",
    ):
        subject._prove_generic_fact_schema_v1()


def test_ingestion_matrix_authority_path_fails_closed(
    projection: generic.NormalizedDecisionSource,
) -> None:
    matrix = (
        "data/derived/covalent_small/"
        "covapie_gve_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_gve_event_task_label_availability_v1.csv"
    )
    binding = replace(projection.binding, source_path=matrix)
    facts = tuple(
        replace(fact, source_binding_path=matrix) for fact in projection.facts
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_SOURCE_PROJECTION_IDENTITY_INVALID",
    ):
        subject._validate_projected_gve_source_v1(
            replace(projection, binding=binding, facts=facts)
        )


def test_historical_rank_unit_and_1xd3_collision_fail_closed(
    reconciliations: tuple[
        generic.ReconciliationResult, generic.ReconciliationResult
    ],
) -> None:
    before, _after = reconciliations
    rows = [dict(row) for row in before.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == gve_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["raw_priority_rank"] = "22"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_PREDECESSOR_HISTORICAL_STATE_DRIFT",
    ):
        subject._prove_gve_predecessor_historical_state_v1(rows)

    rows = [dict(row) for row in before.reconciled_rows]
    rows[0]["raw_review_unit_id"] = gve_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_GENERIC_REVIEW_UNIT_COLLISION",
    ):
        subject._prove_gve_predecessor_historical_state_v1(rows)

    rows = [dict(row) for row in before.reconciled_rows]
    rows[0]["canonical_event_id"] = (
        "COVAPIE_CYS_SG_EVENT_V1:1XD3:A:CYS:1-:SG:X:GVE:CB"
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_GENERIC_REVIEW_UNIT_COLLISION",
    ):
        subject._prove_gve_predecessor_historical_state_v1(rows)


def test_source_count_and_fact_count_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
    projection: generic.NormalizedDecisionSource,
) -> None:
    before, _after = source_chains
    monkeypatch.setattr(
        sr2_predecessor,
        "load_real_completed_decision_sources_with_sr2_v1",
        lambda _root: before[:-1],
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="PREDECESSOR_WITH_SR2_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_gve_v1(ROOT)

    monkeypatch.setattr(
        sr2_predecessor,
        "load_real_completed_decision_sources_with_sr2_v1",
        lambda _root: before,
    )
    monkeypatch.setattr(
        subject,
        "project_gve_completed_decision_v1",
        lambda **_kwargs: replace(projection, facts=projection.facts[:-1]),
    )
    monkeypatch.setattr(subject, "_validate_projected_gve_source_v1", lambda _x: None)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="REAL_SOURCE_CHAIN_NOT_EXACT20",
    ):
        subject.load_real_completed_decision_sources_with_gve_v1(ROOT)


def test_non_gve_fifth_field_and_calibration_drift_fail_closed(
    reconciliations: tuple[
        generic.ReconciliationResult, generic.ReconciliationResult
    ],
) -> None:
    before, after = reconciliations
    rows = [dict(row) for row in after.reconciled_rows]
    rows[0]["calibration_eligible"] = (
        "true" if rows[0]["calibration_eligible"] == "false" else "false"
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_NON_TARGET_ROW_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )

    rows = [dict(row) for row in after.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == gve_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["calibration_eligible"] = "true"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_TARGET_CHANGED_FIELD_SET_INVALID",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )

    rows = [dict(row) for row in after.reconciled_rows]
    rows[0]["fifth_reconciliation_field"] = "forbidden"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGVEError,
        match="GVE_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )
