from __future__ import annotations

import ast
import copy
from dataclasses import fields, replace
import importlib.util
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1
    as four_m5_ingestion_owner,
)
from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_cer_v1
    as cer_predecessor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_4m5_v1 as subject,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)


ROOT = Path(__file__).resolve().parents[1]
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
FORBIDDEN_FACT_ATTRIBUTES = (
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "role_profile",
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "boundary_bonds",
    "canonical_mask_applicability",
    "PRE_geometry",
    "PRE_topology",
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
    "tensor_target",
)
PREDECESSOR_FACT_COUNTS = (
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
    4,
    4,
)
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 103,
    "completed_positive_unit_count": 15,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 131,
    "completed_total_unit_count": 20,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 207,
    "unreviewed_unit_count": 111,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 107,
    "completed_positive_unit_count": 16,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 135,
    "completed_total_unit_count": 21,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 203,
    "unreviewed_unit_count": 110,
}
EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_4m5_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_4m5_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_4m5_v1.py",
    "docs/"
    "covapie_completed_human_decision_reconciliation_with_4m5_v1_guide.md",
)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return four_m5_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def source(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_4m5_binding_v1(bound)


@pytest.fixture(scope="module")
def historical() -> tuple[dict[str, str], ...]:
    return generic.load_real_historical_reconciliation_v1(ROOT)


@pytest.fixture(scope="module")
def adapted(
    historical: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    return (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )


@pytest.fixture(scope="module")
def predecessor_sources() -> tuple[generic.NormalizedDecisionSource, ...]:
    return cer_predecessor.load_real_completed_decision_sources_with_cer_v1(ROOT)


@pytest.fixture(scope="module")
def successor_sources() -> tuple[generic.NormalizedDecisionSource, ...]:
    return subject.load_real_completed_decision_sources_with_4m5_v1(ROOT)


@pytest.fixture(scope="module")
def predecessor_result() -> generic.ReconciliationResult:
    return cer_predecessor.reconcile_real_completed_human_decisions_with_cer_v1(ROOT)


@pytest.fixture(scope="module")
def successor_result() -> generic.ReconciliationResult:
    return subject.reconcile_real_completed_human_decisions_with_4m5_v1(ROOT)


@pytest.fixture(scope="module")
def checker():
    path = ROOT / EXACT4_PATHS[1]
    spec = importlib.util.spec_from_file_location("four_m5_reconciliation_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_api_is_exact4() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWith4M5Error",
        "project_4m5_completed_decision_v1",
        "load_real_completed_decision_sources_with_4m5_v1",
        "reconcile_real_completed_human_decisions_with_4m5_v1",
    )


def test_source_identities_are_derived_from_published_ingestion() -> None:
    assert four_m5_ingestion_owner.FORMAL_BINDINGS[0][2:] == (
        29089,
        "5e37540220ac44b281b20bfb796f5c2994d0ab402fb5f65acc03fb6f6b1febfb",
        False,
        "FOUR_M5_FROZEN_FORMAL_HUMAN_DECISION",
    )
    assert subject._FORMAL_DECISION_SCHEMA == (
        four_m5_ingestion_owner.FORMAL_DECISION_SCHEMA
    )
    assert subject._FORMAL_SEMANTIC_SHA256 == (
        four_m5_ingestion_owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    )


def test_runtime_graph_uses_published_owners_without_side_effects() -> None:
    path = ROOT / EXACT4_PATHS[0]
    payload = path.read_text(encoding="utf-8")
    tree = ast.parse(payload)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    assert imports == {
        "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1",
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_cer_v1",
        "covapie_completed_human_decision_reconciliation_with_onl_v1",
    }
    assert "validate_4m5_formal_human_decision_v1" not in payload
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not calls & {
        "write_bytes",
        "write_text",
        "mkdir",
        "materialize_artifacts",
        "refresh_census",
        "run",
        "Popen",
    }


def test_projector_calls_published_ingestion_owner_once(
    monkeypatch: pytest.MonkeyPatch, bound: dict[str, object]
) -> None:
    calls = 0

    def load(repo_root: Path) -> dict[str, object]:
        nonlocal calls
        assert repo_root == ROOT
        calls += 1
        return bound

    monkeypatch.setattr(
        four_m5_ingestion_owner, "load_frozen_formal_decision_v1", load
    )
    assert subject.project_4m5_completed_decision_v1(repo_root=ROOT) == (
        subject._project_validated_4m5_binding_v1(bound)
    )
    assert calls == 1


def test_projector_wraps_ingestion_owner_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise four_m5_ingestion_owner.FourM5IngestionSafetyError("SYNTHETIC")

    monkeypatch.setattr(
        four_m5_ingestion_owner, "load_frozen_formal_decision_v1", fail
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="FOUR_M5_INGESTION_OWNER_VALIDATION_FAILED:SYNTHETIC",
    ):
        subject.project_4m5_completed_decision_v1(repo_root=ROOT)


def test_rich_4m5_authority_is_validated_before_projection(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_4m5_semantics_v1(bound)
    assert tuple(event["canonical_event_id"] for event in events) == (
        four_m5_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert tuple(event["scaleup_rank"] for event in events) == (973, 974, 975, 976)
    assert all(event["protein_reactive_atom"] == "SG" for event in events)
    assert all(event["ligand_reactive_atom"] == "C15" for event in events)


def test_candidate0_exact25_b3_and_pre_boundaries_are_validated(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]  # type: ignore[assignment]
    role = formal["selected_role_partition"]  # type: ignore[index]
    tasks = formal["canonical_Exact5_and_sample_applicability"]  # type: ignore[index]
    pre = formal["PRE_POST_boundary"]  # type: ignore[index]
    assert role["selected_candidate_index_0based"] == 0
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["W_L_S_counts"] == [9, 0, 16]
    assert role["applicable_task_ids"] == [0, 3, 4]
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_present"] is False
    assert pre["PRE_source_graph_present"] is True
    assert pre["PRE_source_graph_count_per_event"] == 1
    assert pre["PRE_mapping_count_per_event"] == 0
    assert pre["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert pre["PRE_topology_authority"] is False
    assert pre["PRE_geometry_authority"] is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("D1_task_relevance", "NOT_RELEVANT"),
        ("D2_chemistry", "NEGATIVE"),
        ("D3_reactive_pair", "UNRESOLVED"),
        ("D4_role_candidate", "SELECT_CANDIDATE_1"),
        ("D5_training_use", "EXCLUDE_FROM_TRAINING_ONLY"),
    ),
)
def test_d1_d5_mutations_fail_closed(
    bound: dict[str, object], field: str, replacement: str
) -> None:
    changed = copy.deepcopy(bound)
    changed["formal"]["human_authorization"][field] = replacement  # type: ignore[index]
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="FOUR_M5_D1_D5_DECISIONS_INVALID",
    ):
        subject._project_validated_4m5_binding_v1(changed)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "extra"))
def test_exact4_missing_duplicate_and_extra_fail_closed(
    bound: dict[str, object], mutation: str
) -> None:
    changed = copy.deepcopy(bound)
    identity_ids = changed["formal"]["identity"][  # type: ignore[index]
        "canonical_event_ids"
    ]
    events = changed["formal"][  # type: ignore[index]
        "event_level_formal_human_decisions"
    ]
    if mutation == "missing":
        identity_ids.pop()  # type: ignore[union-attr]
        events.pop()  # type: ignore[union-attr]
    elif mutation == "duplicate":
        identity_ids[-1] = identity_ids[0]  # type: ignore[index]
        events[-1] = copy.deepcopy(events[0])  # type: ignore[index]
    else:
        identity_ids.append("SYNTHETIC_EXTRA")  # type: ignore[union-attr]
        extra = copy.deepcopy(events[-1])  # type: ignore[index]
        extra["canonical_event_id"] = "SYNTHETIC_EXTRA"
        events.append(extra)  # type: ignore[union-attr]
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="FOUR_M5_FORMAL_IDENTITY_NOT_EXACT4",
    ):
        subject._project_validated_4m5_binding_v1(changed)


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    (
        ("reactive_pair_authority", "reusable_pair_rule_created", True),
        ("chemistry_authority_boundary", "reaction_family_authority_created", True),
        ("selected_role_partition", "reusable_role_rule_created", True),
        ("training_use_boundary", "formal_training_admitted", True),
        ("PRE_POST_boundary", "PRE_source_graph_present", False),
        ("PRE_POST_boundary", "PRE_mapping_count_per_event", 1),
        ("PRE_POST_boundary", "PRE_geometry_authority", True),
        ("POST_evidence_boundary", "POST_geometry_training_authority", True),
        ("canonical_Exact5_and_sample_applicability", "B3_present", False),
        ("canonical_Exact5_and_sample_applicability", "sixth_task_present", True),
    ),
)
def test_rich_authority_boundary_mutations_fail_closed(
    bound: dict[str, object], section: str, field: str, replacement: object
) -> None:
    changed = copy.deepcopy(bound)
    changed["formal"][section][field] = replacement  # type: ignore[index]
    with pytest.raises(subject.CompletedDecisionReconciliationWith4M5Error):
        subject._project_validated_4m5_binding_v1(changed)


def test_generic_fact_schema_is_exact11_and_not_forked(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert (
        tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact))
        == EXPECTED_FACT_FIELDS
    )
    assert len(EXPECTED_FACT_FIELDS) == 11
    assert all(
        type(fact) is generic.NormalizedCompletedDecisionFact
        for fact in source.facts
    )
    assert all(
        not any(hasattr(fact, name) for name in FORBIDDEN_FACT_ATTRIBUTES)
        for fact in source.facts
    )


def test_rich_pre_role_pair_and_mask_fields_do_not_leak_into_generic_fact(
    source: generic.NormalizedDecisionSource,
) -> None:
    rich_names = {
        "protein_reactive_atom",
        "ligand_reactive_atom",
        "role_profile",
        "selected_candidate",
        "warhead_atoms",
        "linker_atoms",
        "scaffold_atoms",
        "boundary_bonds",
        "canonical_mask_applicability",
        "PRE_source_graph_present",
        "PRE_mapping_status",
        "PRE_status",
        "PRE_topology_authority",
        "PRE_geometry_authority",
        "POST_geometry",
        "training_admission",
    }
    assert all(not rich_names & set(fact.__dataclass_fields__) for fact in source.facts)


def test_4m5_generic_projection_and_provenance_are_exact(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert source.binding == generic.SourceBinding(
        source_path=four_m5_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=29089,
        sha256="5e37540220ac44b281b20bfb796f5c2994d0ab402fb5f65acc03fb6f6b1febfb",
        schema_version="covapie_4m5_exact4_formal_human_decision_v1",
        review_unit_id=four_m5_ingestion_owner.EXPECTED_REVIEW_UNIT_ID,
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == tuple(
        sorted(four_m5_ingestion_owner.EXPECTED_EVENT_IDS)
    )
    for fact in source.facts:
        assert fact.human_review_completed is True
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        assert fact.task_relevance_disposition == generic.TASK_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.training_disposition == generic.TRAINING_INCLUDE
        assert fact.human_training_excluded is False
        assert fact.source_decision_schema == four_m5_ingestion_owner.FORMAL_DECISION_SCHEMA
        assert fact.source_decision_sha256 == source.binding.sha256
        assert fact.source_binding_path == source.binding.source_path
        generic._validate_fact(fact, source.binding)


def test_generic_fact_rejection_is_wrapped(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
) -> None:
    def reject(_fact, _binding) -> None:
        raise generic.CompletedDecisionReconciliationError("SYNTHETIC_GENERIC_REJECT")

    monkeypatch.setattr(generic, "_validate_fact", reject)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="FOUR_M5_GENERIC_FACT_REJECTED:SYNTHETIC_GENERIC_REJECT",
    ):
        subject._validate_projected_4m5_source_v1(source)


def test_source_chain_16_to_17_and_107_to_111_is_append_only(
    predecessor_sources: tuple[generic.NormalizedDecisionSource, ...],
    successor_sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    assert tuple(len(source.facts) for source in predecessor_sources) == (
        PREDECESSOR_FACT_COUNTS
    )
    assert len(predecessor_sources) == 16
    assert sum(len(source.facts) for source in predecessor_sources) == 107
    assert len(successor_sources) == 17
    assert sum(len(source.facts) for source in successor_sources) == 111
    assert successor_sources[:-1] == predecessor_sources
    assert len({source.binding.review_unit_id for source in successor_sources}) == 17
    assert len({source.binding.stable_identity for source in successor_sources}) == 17
    event_ids = [
        fact.canonical_event_id
        for source in successor_sources
        for fact in source.facts
    ]
    assert len(event_ids) == len(set(event_ids)) == 111


def test_predecessor_source_count_and_fact_count_drift_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    predecessor_sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    monkeypatch.setattr(
        cer_predecessor,
        "load_real_completed_decision_sources_with_cer_v1",
        lambda _root: predecessor_sources[:-1],
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="PREDECESSOR_CER_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_4m5_v1(ROOT)


def test_event_collision_with_predecessor_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    predecessor_sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    first = predecessor_sources[0]
    changed_fact = replace(
        first.facts[0],
        canonical_event_id=four_m5_ingestion_owner.EXPECTED_EVENT_IDS[0],
    )
    changed_first = replace(first, facts=(changed_fact, *first.facts[1:]))
    changed = (changed_first, *predecessor_sources[1:])
    monkeypatch.setattr(
        cer_predecessor,
        "load_real_completed_decision_sources_with_cer_v1",
        lambda _root: changed,
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="FOUR_M5_EVENT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_4m5_v1(ROOT)


def test_historical_population_and_4m5_prior_are_exact(
    historical: tuple[dict[str, str], ...],
) -> None:
    assert len(historical) == 338
    assert len({row["raw_review_unit_id"] for row in historical}) == 131
    subject._prove_4m5_original_unreviewed_prior_v1(historical)
    target_ids = set(four_m5_ingestion_owner.EXPECTED_EVENT_IDS)
    target = [row for row in historical if row["canonical_event_id"] in target_ids]
    unit = [
        row
        for row in historical
        if row["raw_review_unit_id"]
        == four_m5_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    ]
    assert len(target) == len(unit) == 4
    assert {row["canonical_event_id"] for row in unit} == target_ids
    assert {row["raw_priority_rank"] for row in target} == {"20"}
    assert {row["raw_unit_event_count"] for row in target} == {"4"}
    assert {row["current_review_status"] for row in target} == {
        generic.CURRENTLY_UNREVIEWED
    }
    assert {row["calibration_eligible"] for row in target} == {"true"}
    assert {row["calibration_exclusion_reason"] for row in target} == {""}


def test_prior_mutation_uses_required_fail_closed_token(
    historical: tuple[dict[str, str], ...]
) -> None:
    changed = tuple(dict(row) for row in historical)
    for row in changed:
        if row["canonical_event_id"] == four_m5_ingestion_owner.EXPECTED_EVENT_IDS[0]:
            row["calibration_eligible"] = "false"
            break
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="^FOUR_M5_RECONCILIATION_PRECONDITION_FAILED$",
    ):
        subject._prove_4m5_original_unreviewed_prior_v1(changed)


def test_fifth_same_unit_event_fails_closed(
    historical: tuple[dict[str, str], ...]
) -> None:
    changed = tuple(dict(row) for row in historical)
    target_ids = set(four_m5_ingestion_owner.EXPECTED_EVENT_IDS)
    for row in changed:
        if row["canonical_event_id"] not in target_ids:
            row["raw_review_unit_id"] = four_m5_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
            break
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="FOUR_M5_RECONCILIATION_PRECONDITION_FAILED",
    ):
        subject._prove_4m5_original_unreviewed_prior_v1(changed)


def test_onl_adapter_does_not_mutate_input_or_change_4m5(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    snapshot = copy.deepcopy(historical)
    second = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    assert historical == snapshot
    assert adapted == second
    subject._prove_4m5_rows_unchanged_after_onl_normalization_v1(
        historical, adapted
    )


def test_onl_4m5_row_mutation_fails_closed(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    changed = tuple(dict(row) for row in adapted)
    for row in changed:
        if row["canonical_event_id"] == four_m5_ingestion_owner.EXPECTED_EVENT_IDS[0]:
            row["calibration_eligible"] = "false"
            break
    with pytest.raises(
        subject.CompletedDecisionReconciliationWith4M5Error,
        match="ONL_ADAPTER_CHANGED_FOUR_M5_ROW",
    ):
        subject._prove_4m5_rows_unchanged_after_onl_normalization_v1(
            historical, changed
        )


def test_reconciliation_exact_delta_and_summary(
    predecessor_result: generic.ReconciliationResult,
    successor_result: generic.ReconciliationResult,
) -> None:
    assert predecessor_result.review_summary == BEFORE_SUMMARY
    assert successor_result.review_summary == AFTER_SUMMARY
    subject._validate_reconciliation_delta_v1(predecessor_result, successor_result)
    assert len(predecessor_result.reconciled_rows) == 338
    assert len(successor_result.reconciled_rows) == 338
    assert tuple(
        row["canonical_event_id"] for row in predecessor_result.reconciled_rows
    ) == tuple(row["canonical_event_id"] for row in successor_result.reconciled_rows)


def test_non_4m5_334_rows_are_identical_and_targets_change_only_four_fields(
    predecessor_result: generic.ReconciliationResult,
    successor_result: generic.ReconciliationResult,
) -> None:
    before = {
        row["canonical_event_id"]: row
        for row in predecessor_result.reconciled_rows
    }
    after = {
        row["canonical_event_id"]: row for row in successor_result.reconciled_rows
    }
    target_ids = set(four_m5_ingestion_owner.EXPECTED_EVENT_IDS)
    non_target = set(before) - target_ids
    assert len(non_target) == 334
    assert all(before[event_id] == after[event_id] for event_id in non_target)
    allowed = {
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    }
    expected_authority = generic._canonical_json(
        [four_m5_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()]
    )
    for event_id in target_ids:
        assert {
            key
            for key in before[event_id]
            if before[event_id][key] != after[event_id][key]
        } == allowed
        assert before[event_id]["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        assert before[event_id]["calibration_eligible"] == "true"
        assert before[event_id]["calibration_exclusion_reason"] == ""
        assert (
            after[event_id]["current_review_status"]
            == generic.COMPLETED_HUMAN_POSITIVE
        )
        assert after[event_id]["current_status_authority_sources_json"] == (
            expected_authority
        )
        assert after[event_id]["calibration_eligible"] == "false"
        assert after[event_id]["calibration_exclusion_reason"] == (
            generic.COMPLETED_HUMAN_POSITIVE
        )


def test_summary_delta_is_exact_and_negative_counts_are_unchanged(
    predecessor_result: generic.ReconciliationResult,
    successor_result: generic.ReconciliationResult,
) -> None:
    old = predecessor_result.review_summary
    new = successor_result.review_summary
    assert new["completed_positive_event_count"] - old["completed_positive_event_count"] == 4
    assert new["completed_positive_unit_count"] - old["completed_positive_unit_count"] == 1
    assert new["completed_total_event_count"] - old["completed_total_event_count"] == 4
    assert new["completed_total_unit_count"] - old["completed_total_unit_count"] == 1
    assert new["unreviewed_event_count"] - old["unreviewed_event_count"] == -4
    assert new["unreviewed_unit_count"] - old["unreviewed_unit_count"] == -1
    assert new["completed_negative_event_count"] == old["completed_negative_event_count"]
    assert new["completed_negative_unit_count"] == old["completed_negative_unit_count"]
    assert new["in_progress_event_count"] == old["in_progress_event_count"] == 0
    assert new["in_progress_unit_count"] == old["in_progress_unit_count"] == 0


def test_d5_include_remains_non_admission_and_creates_no_rich_authority(
    bound: dict[str, object], source: generic.NormalizedDecisionSource
) -> None:
    training = bound["formal"]["training_use_boundary"]  # type: ignore[index]
    authority = bound["formal"]["authority_boundary"]  # type: ignore[index]
    assert training["D5_human_choice"] == "INCLUDE"  # type: ignore[index]
    assert training["formal_training_admitted"] is False  # type: ignore[index]
    assert training["training_materialization_allowed"] is False  # type: ignore[index]
    assert training["tensor_target_created"] is False  # type: ignore[index]
    assert authority["READY_FOR_TRAINING"] is False  # type: ignore[index]
    assert all(
        fact.training_disposition == generic.TRAINING_INCLUDE
        for fact in source.facts
    )
    assert all(
        not any(hasattr(fact, name) for name in FORBIDDEN_FACT_ATTRIBUTES)
        for fact in source.facts
    )


def test_generic_reconciliation_is_deterministic_and_idempotent(
    adapted: tuple[dict[str, str], ...],
    successor_sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    first = generic.reconcile_completed_human_decisions_v1(adapted, successor_sources)
    second = generic.reconcile_completed_human_decisions_v1(adapted, successor_sources)
    assert first == second


def test_production_reconciliation_delegates_to_generic_once(
    monkeypatch: pytest.MonkeyPatch,
    predecessor_result: generic.ReconciliationResult,
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
    successor_sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    calls = 0
    real = generic.reconcile_completed_human_decisions_v1

    def reconcile(rows, sources):
        nonlocal calls
        calls += 1
        return real(rows, sources)

    monkeypatch.setattr(
        cer_predecessor,
        "reconcile_real_completed_human_decisions_with_cer_v1",
        lambda _root: predecessor_result,
    )
    monkeypatch.setattr(
        generic, "load_real_historical_reconciliation_v1", lambda _root: historical
    )
    monkeypatch.setattr(
        onl_successor,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        lambda _rows: adapted,
    )
    monkeypatch.setattr(
        subject,
        "load_real_completed_decision_sources_with_4m5_v1",
        lambda _root: successor_sources,
    )
    monkeypatch.setattr(generic, "reconcile_completed_human_decisions_v1", reconcile)
    result = subject.reconcile_real_completed_human_decisions_with_4m5_v1(ROOT)
    assert result.review_summary == AFTER_SUMMARY
    assert calls == 1


def test_candidate_and_future_tracked_clean_lifecycle_profiles(checker) -> None:
    expected = tuple(sorted(EXACT4_PATHS))
    expected_set = set(expected)
    assert checker.classify_repository_profile(
        expected_paths=expected,
        tracked_paths=set(),
        ordinary_untracked=expected_set,
        status_lines=tuple("?? " + path for path in expected),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=expected,
        tracked_paths=expected_set,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN
    assert all(checker.check_lifecycle_simulations().values())


def test_future_tracked_clean_allows_unrelated_successors_and_multiple_commits(
    checker,
) -> None:
    expected = set(EXACT4_PATHS)
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=expected,
        head="synthetic-later-head",
        origin_main="synthetic-between-origin",
        ahead=2,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected
        | {"src/covalent_ext/synthetic_later_successor.py"},
    )


@pytest.mark.parametrize(
    "updates",
    (
        {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False},
        {"behind": 1},
        {"changed_since_baseline": set(EXACT4_PATHS[:-1])},
    ),
)
def test_invalid_future_tracked_relations_fail_closed(checker, updates) -> None:
    values = {
        "profile": checker.TRACKED_CLEAN,
        "expected_paths": set(EXACT4_PATHS),
        "head": "synthetic-head",
        "origin_main": checker.BASELINE_COMMIT,
        "ahead": 1,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": set(EXACT4_PATHS),
    }
    values.update(updates)
    with pytest.raises(ValueError):
        checker.validate_repository_relation_values(**values)


@pytest.mark.parametrize(
    "updates",
    (
        {
            "tracked_paths": {EXACT4_PATHS[0]},
            "ordinary_untracked": set(EXACT4_PATHS[1:]),
            "status_lines": tuple("?? " + path for path in EXACT4_PATHS[1:]),
        },
        {"working_diff": {EXACT4_PATHS[0]}},
        {"cached_diff": {EXACT4_PATHS[0]}},
        {
            "ordinary_untracked": {"synthetic-unrelated.txt"},
            "status_lines": ("?? synthetic-unrelated.txt",),
        },
    ),
)
def test_mixed_dirty_staged_and_unrelated_untracked_fail_closed(
    checker, updates
) -> None:
    values = {
        "expected_paths": EXACT4_PATHS,
        "tracked_paths": set(EXACT4_PATHS),
        "ordinary_untracked": set(),
        "status_lines": (),
        "working_diff": set(),
        "cached_diff": set(),
    }
    values.update(updates)
    with pytest.raises(ValueError):
        checker.classify_repository_profile(**values)


def test_exact4_inventory_has_no_forbidden_or_materialized_artifact() -> None:
    forbidden = (
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".pyc",
        ".tmp",
        ".part",
        ".log",
    )
    assert len(EXACT4_PATHS) == len(set(EXACT4_PATHS)) == 4
    assert not any(path.endswith(forbidden) for path in EXACT4_PATHS)
    assert not (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_completed_human_decision_reconciliation_with_4m5_v1"
    ).exists()


def test_authority_source_json_is_exact_canonical_single_path(
    successor_result: generic.ReconciliationResult,
) -> None:
    target_ids = set(four_m5_ingestion_owner.EXPECTED_EVENT_IDS)
    expected = generic._canonical_json(
        [four_m5_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()]
    )
    assert json.loads(expected) == [
        four_m5_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
    ]
    target = [
        row
        for row in successor_result.reconciled_rows
        if row["canonical_event_id"] in target_ids
    ]
    assert len(target) == 4
    assert {row["current_status_authority_sources_json"] for row in target} == {
        expected
    }
