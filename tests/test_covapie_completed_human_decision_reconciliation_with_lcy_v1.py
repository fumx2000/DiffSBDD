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
    covapie_completed_human_decision_reconciliation_with_gve_v1
    as gve_predecessor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_lcy_v1 as subject,
)
from covalent_ext import (
    covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1
    as lcy_ingestion_owner,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_lcy_v1.py"
)
PREDECESSOR = (
    ROOT
    / "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_gve_v1.py"
)
INGESTION_OWNER = (
    ROOT
    / "src/covalent_ext/"
    "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1.py"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithLCYError",
    "project_lcy_completed_decision_v1",
    "load_real_completed_decision_sources_with_lcy_v1",
    "reconcile_real_completed_human_decisions_with_lcy_v1",
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
    "completed_negative_event_count": 32,
    "completed_negative_unit_count": 6,
    "completed_total_event_count": 147,
    "completed_total_unit_count": 24,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 191,
    "unreviewed_unit_count": 107,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 36,
    "completed_negative_unit_count": 7,
    "completed_total_event_count": 151,
    "completed_total_unit_count": 25,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 187,
    "unreviewed_unit_count": 106,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return lcy_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def projection(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_lcy_binding_v1(bound)


@pytest.fixture(scope="module")
def source_chains() -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    after = subject.load_real_completed_decision_sources_with_lcy_v1(ROOT)
    return after[:-1], after


@pytest.fixture(scope="module")
def predecessor() -> generic.ReconciliationResult:
    return gve_predecessor.reconcile_real_completed_human_decisions_with_gve_v1(
        ROOT
    )


@pytest.fixture(scope="module")
def reconciliations(
    predecessor: generic.ReconciliationResult,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> tuple[generic.ReconciliationResult, generic.ReconciliationResult]:
    _before_sources, after_sources = source_chains
    historical = generic.load_real_historical_reconciliation_v1(ROOT)
    adapted = (
        gve_predecessor.sr2_predecessor.gd1_predecessor.four_m5_predecessor
        .onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    after = generic.reconcile_completed_human_decisions_v1(
        adapted, after_sources
    )
    return predecessor, after


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
        "covapie_completed_human_decision_reconciliation_with_gve_v1",
        "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1",
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
    assert PREDECESSOR.stat().st_size == 34765
    assert _sha(PREDECESSOR) == (
        "a8c3eba54364b42fd5de918f65fec3273f7c8913c9cf9821fd5b4861d235d541"
    )
    assert INGESTION_OWNER.stat().st_size == 101342
    assert _sha(INGESTION_OWNER) == (
        "380d3f0c8000bb1c1af404620430039dd87e41a0f10018bb83ee68e98a83de7c"
    )


def test_rich_lcy_exact4_prevalidation(bound: dict[str, object]) -> None:
    events = subject._validate_rich_lcy_semantics_v1(bound)
    assert tuple(row["canonical_event_id"] for row in events) == (
        lcy_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert tuple(row["scaleup_rank"] for row in events) == (898, 899, 900, 901)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    inherited = formal["inherited_human_scientific_decision"]
    assert isinstance(inherited, dict)
    assert [
        inherited[f"D{index}_{name}"]
        for index, name in (
            (1, "task_relevance"),
            (2, "chemistry"),
            (3, "reactive_pair"),
            (4, "role_candidate"),
            (5, "training_use"),
        )
    ] == [
        "NOT_RELEVANT",
        "POSITIVE",
        "CONFIRM_OBSERVED_PAIR",
        "UNRESOLVED",
        "NOT_APPLICABLE",
    ]
    assert inherited["D6_utf8_byte_count"] == 1754
    assert inherited["D6_utf8_sha256"] == (
        "db6fdb1ca13c1bbbfce111e251c0ceba011a770317edd92ff12c8042a2ee884b"
    )
    assert bound["formal_validator_provenance_identity_only"] is True
    for key in (
        "formal_validator_imported",
        "formal_validator_parsed",
        "formal_validator_executed",
        "formal_validator_subprocessed",
        "formal_validator_runtime_dependency",
    ):
        assert bound[key] is False


def test_lcy_authority_d4_pre_post_and_3a2g_boundaries(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]
    assert isinstance(formal, dict)
    authority = formal["formal_authority_boundary"]
    role = formal["D4_role_boundary"]
    pair = formal["sample_reactive_pair"]
    pre = formal["PRE_boundary"]
    post = formal["POST_boundary"]
    same_component = formal["same_component_3A2G_boundary"]
    assert all(
        isinstance(item, dict)
        for item in (authority, role, pair, pre, post, same_component)
    )
    assert authority["formal_authority_true_set"] == [
        "formal_authority_created",
        "formal_authority_is_human",
        "human_training_use_disposition_authority",
        "sample_positive_chemistry_authority",
        "sample_reactive_pair_authority",
        "sample_task_relevance_authority",
    ]
    assert role["review_policy_candidate_count"] == 0
    assert role["formal_valid_singleton_diagnostic_count"] == 3
    assert role["role_partition_sample_authority"] is False
    assert pair["protein_reactive_atom"] == "SG"
    assert pair["ligand_reactive_atom"] == "C1"
    assert pair["observed_POST_distances_angstrom"] == [
        1.699831,
        1.696052,
        1.696490,
        1.700175,
    ]
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert post["POST_source_evidence_count"] == 4
    assert same_component["current_Exact4_authority"] is False
    assert same_component["decision_transferred"] is False


def test_generic_exact11_projection_and_namespace_translation(
    projection: generic.NormalizedDecisionSource,
) -> None:
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == (
        EXPECTED_FACT_FIELDS
    )
    assert len(projection.facts) == 4
    assert projection.binding.path_namespace == "repository_parent_relative"
    assert projection.binding.source_path == (
        lcy_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
    )
    assert projection.binding.byte_count == 32277
    assert projection.binding.sha256 == (
        "d7c7b427b87b13fa61188bd6b14a3e9dd3a37e4a170176222685065d419a3387"
    )
    assert projection.binding.schema_version == (
        "covapie_lcy_exact4_formal_human_decision_v1"
    )
    generic._validate_source_binding(projection.binding)
    for fact in projection.facts:
        assert tuple(fact.__dataclass_fields__) == EXPECTED_FACT_FIELDS
        assert fact.human_review_completed is True
        assert fact.legacy_completed_review_status == "COMPLETED_HUMAN_NEGATIVE"
        assert fact.task_relevance_disposition == "NOT_RELEVANT"
        assert fact.chemistry_disposition == "POSITIVE"
        assert fact.training_disposition == "NOT_APPLICABLE"
        assert fact.human_training_excluded is False
        generic._validate_fact(fact, projection.binding)


def test_no_rich_lcy_field_leaks_to_generic(
    bound: dict[str, object], projection: generic.NormalizedDecisionSource
) -> None:
    lane = bound["completed_lane_validation"]
    assert isinstance(lane, dict)
    assert lane["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    assert all(
        not hasattr(fact, field)
        for fact in projection.facts
        for field in subject._FORBIDDEN_GENERIC_FACT_ATTRIBUTES
    )


def test_source_chain_is_append_only_exact21_127(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, after = source_chains
    assert len(before) == 20
    assert len(after) == 21
    assert after[:-1] == before
    assert tuple(len(source.facts) for source in before) == (
        8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4
    )
    assert tuple(len(source.facts) for source in after) == (
        8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4
    )
    assert sum(len(source.facts) for source in before) == 123
    assert sum(len(source.facts) for source in after) == 127
    assert len({source.binding.review_unit_id for source in after}) == 21
    assert len({source.binding.stable_identity for source in after}) == 21
    assert len(
        {fact.canonical_event_id for source in after for fact in source.facts}
    ) == 127
    assert all(
        fact.canonical_event_id != subject._SAME_COMPONENT_3A2G_EVENT_ID
        for source in after
        for fact in source.facts
    )


def test_historical_rank24_exact4_and_3a2g_non_target(
    predecessor: generic.ReconciliationResult,
) -> None:
    subject._prove_lcy_predecessor_historical_state_v1(
        predecessor.reconciled_rows
    )
    target = [
        row
        for row in predecessor.reconciled_rows
        if row["raw_review_unit_id"] == lcy_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    ]
    assert len(target) == 4
    assert {row["canonical_event_id"] for row in target} == set(
        lcy_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert {row["raw_priority_rank"] for row in target} == {"24"}
    assert {row["raw_unit_event_count"] for row in target} == {"4"}
    context = [
        row
        for row in predecessor.reconciled_rows
        if row["canonical_event_id"] == subject._SAME_COMPONENT_3A2G_EVENT_ID
    ]
    assert len(context) == 1
    assert context[0]["raw_review_unit_id"] != (
        lcy_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    )


def test_reconciliation_summary_exact_delta_and_authority(
    reconciliations: tuple[
        generic.ReconciliationResult, generic.ReconciliationResult
    ],
) -> None:
    before, after = reconciliations
    assert before.review_summary == BEFORE_SUMMARY
    assert after.review_summary == AFTER_SUMMARY
    subject._validate_reconciliation_delta_v1(before, after)
    target_ids = set(lcy_ingestion_owner.EXPECTED_EVENT_IDS)
    changed = []
    unchanged = 0
    expected_authority = generic._canonical_json(
        [lcy_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()]
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
    assert len(after.source_bindings) == 21
    assert len(after.normalized_facts) == 127


def test_public_reconciler_uses_predecessor_and_returns_in_memory_result(
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
        gve_predecessor,
        "reconcile_real_completed_human_decisions_with_gve_v1",
        lambda _root: before,
    )
    monkeypatch.setattr(
        subject,
        "load_real_completed_decision_sources_with_lcy_v1",
        lambda _root: after_sources,
    )
    actual = subject.reconcile_real_completed_human_decisions_with_lcy_v1(ROOT)
    assert actual == expected_after
    assert not hasattr(actual, "write")
    assert not hasattr(actual, "materialize")


@pytest.mark.parametrize(
    ("section", "key", "value", "token"),
    (
        (
            "inherited_human_scientific_decision",
            "D1_task_relevance",
            "RELEVANT",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D2_chemistry",
            "NOT_ESTABLISHED",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D2_chemistry",
            "NEGATIVE",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D4_role_candidate",
            "SELECT_CANDIDATE_0",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D5_training_use",
            "INCLUDE",
            "LCY_D1_D5",
        ),
        (
            "sample_reactive_pair",
            "ligand_reactive_atom",
            "C2",
            "LCY_SG_C1",
        ),
        (
            "D4_role_boundary",
            "role_partition_sample_authority",
            True,
            "LCY_UNRESOLVED_ROLE",
        ),
        (
            "training_boundary",
            "human_training_excluded",
            True,
            "LCY_TRAINING_NOT_APPLICABLE",
        ),
        (
            "training_boundary",
            "training_use_disposition",
            "EXCLUDE_FROM_TRAINING_ONLY",
            "LCY_TRAINING_NOT_APPLICABLE",
        ),
        (
            "PRE_boundary",
            "PRE_status",
            "PRE_REACTION_RESOLVED",
            "LCY_PRE_UNRESOLVED",
        ),
        (
            "same_component_3A2G_boundary",
            "pair_promoted",
            True,
            "LCY_3A2G_AUTHORITY_TRANSFER",
        ),
        (
            "downstream_operations",
            "census_refresh",
            True,
            "LCY_UNAUTHORIZED_DOWNSTREAM",
        ),
        (
            "downstream_operations",
            "queue_refresh",
            True,
            "LCY_UNAUTHORIZED_DOWNSTREAM",
        ),
        (
            "downstream_operations",
            "training",
            True,
            "LCY_UNAUTHORIZED_DOWNSTREAM",
        ),
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
        subject.CompletedDecisionReconciliationWithLCYError, match=token
    ):
        subject._validate_rich_lcy_semantics_v1(
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
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_FORMAL_COMPLETION_OR_SEMANTICS_INVALID",
    ):
        subject._validate_rich_lcy_semantics_v1(wrong_schema)

    wrong_sha = copy.deepcopy(bound)
    binding = wrong_sha["formal_decision_binding"]
    assert isinstance(binding, dict)
    binding["SHA256"] = "0" * 64
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_FORMAL_DECISION_BINDING_INVALID",
    ):
        subject._project_validated_lcy_binding_v1(wrong_sha)

    wrong_namespace = replace(
        projection.binding, path_namespace="project_parent_relative"
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_SOURCE_PROJECTION_IDENTITY_INVALID",
    ):
        subject._validate_projected_lcy_source_v1(
            replace(projection, binding=wrong_namespace)
        )


def test_fifth_3a2g_and_ligand_wide_selection_fail_closed(
    bound: dict[str, object],
) -> None:
    fifth = copy.deepcopy(bound)
    formal = fifth["formal"]
    assert isinstance(formal, dict)
    events = formal["event_level_formal_decisions"]
    assert isinstance(events, list)
    extra = copy.deepcopy(events[-1])
    extra["canonical_event_id"] = subject._SAME_COMPONENT_3A2G_EVENT_ID
    events.append(extra)
    formal["event_level_formal_decision_count"] = 5
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_FORMAL_EVENT_COVERAGE_NOT_EXACT4",
    ):
        subject._validate_rich_lcy_semantics_v1(fifth)

    ligand_wide = _mutate_formal(
        bound, "target_Exact4", "ligand_wide_selection", True
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_FORMAL_IDENTITY_NOT_EXACT4",
    ):
        subject._validate_rich_lcy_semantics_v1(ligand_wide)


@pytest.mark.parametrize(
    "changes",
    (
        {"legacy_completed_review_status": "COMPLETED_TASK_DOMAIN_NEGATIVE"},
        {"legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE},
        {"task_relevance_disposition": generic.TASK_RELEVANT},
        {"chemistry_disposition": generic.CHEMISTRY_NOT_ESTABLISHED},
        {"chemistry_disposition": generic.CHEMISTRY_NEGATIVE},
        {"training_disposition": generic.TRAINING_INCLUDE},
        {"training_disposition": generic.TRAINING_EXCLUDE},
        {"human_training_excluded": True},
    ),
)
def test_generic_projection_semantic_drift_fails_closed(
    projection: generic.NormalizedDecisionSource,
    changes: dict[str, object],
) -> None:
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_SOURCE_PROJECTION_INVALID",
    ):
        subject._validate_projected_lcy_source_v1(
            _replace_source_fact(projection, **changes)
        )


@pytest.mark.parametrize(
    "extra_field",
    (
        "protein_reactive_atom",
        "PRE_status",
        "formal_valid_singleton_diagnostic_count",
    ),
)
def test_generic_schema_extra_rich_field_fails_closed(
    monkeypatch: pytest.MonkeyPatch, extra_field: str
) -> None:
    fields = [(name, object) for name in EXPECTED_FACT_FIELDS]
    fields.append((extra_field, object))
    monkeypatch.setattr(
        generic, "NormalizedCompletedDecisionFact", make_dataclass("BadFact", fields)
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11",
    ):
        subject._prove_generic_fact_schema_v1()


def test_ingestion_matrix_authority_path_fails_closed(
    projection: generic.NormalizedDecisionSource,
) -> None:
    matrix = (
        "data/derived/covalent_small/"
        "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_lcy_event_task_label_availability_v1.csv"
    )
    binding = replace(projection.binding, source_path=matrix)
    facts = tuple(
        replace(fact, source_binding_path=matrix) for fact in projection.facts
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_SOURCE_PROJECTION_IDENTITY_INVALID",
    ):
        subject._validate_projected_lcy_source_v1(
            replace(projection, binding=binding, facts=facts)
        )


def test_source_chain_count_and_collision_guards_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
    projection: generic.NormalizedDecisionSource,
) -> None:
    before, _after = source_chains
    monkeypatch.setattr(
        gve_predecessor,
        "load_real_completed_decision_sources_with_gve_v1",
        lambda _root: before[:-1],
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="PREDECESSOR_WITH_GVE_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_lcy_v1(ROOT)


def test_event_review_unit_and_stable_source_collisions_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
    projection: generic.NormalizedDecisionSource,
) -> None:
    before, _after = source_chains
    monkeypatch.setattr(
        subject,
        "project_lcy_completed_decision_v1",
        lambda **_kwargs: projection,
    )

    duplicate_event_fact = replace(
        before[0].facts[0],
        canonical_event_id=projection.facts[0].canonical_event_id,
    )
    duplicate_event_source = replace(
        before[0], facts=(duplicate_event_fact, *before[0].facts[1:])
    )
    event_collision_chain = (duplicate_event_source, *before[1:])
    monkeypatch.setattr(
        gve_predecessor,
        "load_real_completed_decision_sources_with_gve_v1",
        lambda _root: event_collision_chain,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_EVENT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_lcy_v1(ROOT)

    review_collision_source = replace(
        before[0],
        binding=replace(
            before[0].binding,
            review_unit_id=lcy_ingestion_owner.EXPECTED_REVIEW_UNIT_ID,
        ),
    )
    review_collision_chain = (review_collision_source, *before[1:])
    monkeypatch.setattr(
        gve_predecessor,
        "load_real_completed_decision_sources_with_gve_v1",
        lambda _root: review_collision_chain,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_REVIEW_UNIT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_lcy_v1(ROOT)

    stable_collision_source = replace(
        before[0],
        binding=replace(
            before[0].binding,
            source_path=projection.binding.source_path,
            path_namespace=projection.binding.path_namespace,
            sha256=projection.binding.sha256,
        ),
    )
    stable_collision_chain = (stable_collision_source, *before[1:])
    monkeypatch.setattr(
        gve_predecessor,
        "load_real_completed_decision_sources_with_gve_v1",
        lambda _root: stable_collision_chain,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_STABLE_SOURCE_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_lcy_v1(ROOT)

    monkeypatch.setattr(
        gve_predecessor,
        "load_real_completed_decision_sources_with_gve_v1",
        lambda _root: before,
    )
    monkeypatch.setattr(
        subject,
        "project_lcy_completed_decision_v1",
        lambda **_kwargs: replace(projection, facts=projection.facts[:-1]),
    )
    monkeypatch.setattr(subject, "_validate_projected_lcy_source_v1", lambda _x: None)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="REAL_SOURCE_CHAIN_NOT_EXACT21",
    ):
        subject.load_real_completed_decision_sources_with_lcy_v1(ROOT)


def test_historical_rank_unit_and_3a2g_collision_fail_closed(
    predecessor: generic.ReconciliationResult,
) -> None:
    rows = [dict(row) for row in predecessor.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == lcy_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["raw_priority_rank"] = "23"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_PREDECESSOR_HISTORICAL_STATE_DRIFT",
    ):
        subject._prove_lcy_predecessor_historical_state_v1(rows)

    rows = [dict(row) for row in predecessor.reconciled_rows]
    context = next(
        row
        for row in rows
        if row["canonical_event_id"] == subject._SAME_COMPONENT_3A2G_EVENT_ID
    )
    context["raw_review_unit_id"] = lcy_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_GENERIC_REVIEW_UNIT_COLLISION",
    ):
        subject._prove_lcy_predecessor_historical_state_v1(rows)


def test_non_lcy_fifth_field_positive_and_3a2g_delta_fail_closed(
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
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_NON_TARGET_ROW_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )

    changed_summary = dict(after.review_summary)
    changed_summary["completed_positive_event_count"] = 116
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_RECONCILIATION_REVIEW_SUMMARY_INVALID",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, review_summary=changed_summary)
        )

    rows = [dict(row) for row in after.reconciled_rows]
    rows[0]["fifth_reconciliation_field"] = "forbidden"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )

    rows = [dict(row) for row in after.reconciled_rows]
    rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )

    rows = [dict(row) for row in after.reconciled_rows]
    context = next(
        row
        for row in rows
        if row["canonical_event_id"] == subject._SAME_COMPONENT_3A2G_EVENT_ID
    )
    context["current_status_authority_sources_json"] = "[]"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithLCYError,
        match="LCY_NON_TARGET_ROW_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        )
