from __future__ import annotations

import ast
import copy
from dataclasses import fields, replace
import importlib.util
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_i12_completed_decision_ingestion_and_task_label_availability_v1
    as i12_ingestion_owner,
)
from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_2a2_v1
    as two_a2_successor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_i12_v1 as subject,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_i12_v1.py"
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
    "chemical_warhead_atom_ids",
    "warhead_role_atom_ids",
    "linker_atom_ids",
    "scaffold_atom_ids",
    "role_profile",
    "role_boundaries",
    "selected_candidate",
    "canonical_task_applicability",
    "minimal_seed",
    "POST_geometry",
    "PRE_topology",
    "PRE_geometry",
    "future_training_candidate",
    "training_admitted",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
)
EXPECTED_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4, 4)
EXPECTED_SUMMARY = {
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


def _load_checker():
    spec = importlib.util.spec_from_file_location("i12_reconciliation_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return _load_checker()


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return i12_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def source(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_i12_binding_v1(bound)


@pytest.fixture(scope="module")
def sources() -> tuple[generic.NormalizedDecisionSource, ...]:
    return subject.load_real_completed_decision_sources_with_i12_v1(ROOT)


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
def result() -> generic.ReconciliationResult:
    return subject.reconcile_real_completed_human_decisions_with_i12_v1(ROOT)


def _drift(bound: dict[str, object], *path: str, value: object) -> dict[str, object]:
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
        "CompletedDecisionReconciliationWithI12Error",
        "project_i12_completed_decision_v1",
        "load_real_completed_decision_sources_with_i12_v1",
        "reconcile_real_completed_human_decisions_with_i12_v1",
    )


def test_generic_fact_schema_is_exact11_and_not_forked() -> None:
    observed = tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact))
    assert observed == EXPECTED_FACT_FIELDS
    assert len(observed) == 11
    assert subject.generic.NormalizedCompletedDecisionFact is generic.NormalizedCompletedDecisionFact
    assert subject.generic.NormalizedDecisionSource is generic.NormalizedDecisionSource
    assert subject.generic.SourceBinding is generic.SourceBinding
    assert subject.generic.ReconciliationResult is generic.ReconciliationResult


def test_production_runtime_graph_and_side_effect_boundary_are_narrow() -> None:
    text = (ROOT / "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_i12_v1.py").read_text()
    tree = ast.parse(text)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    assert imports == {
        "covapie_i12_completed_decision_ingestion_and_task_label_availability_v1",
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_2a2_v1",
        "covapie_completed_human_decision_reconciliation_with_onl_v1",
    }
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not calls & {
        "open", "write", "write_bytes", "write_text", "mkdir", "makedirs",
        "materialize_artifacts", "write_artifacts", "refresh_census", "run",
        "Popen", "urlopen",
    }
    assert "formal_validator" not in text.lower()


def test_projector_enters_only_through_published_ingestion_owner_once(
    monkeypatch: pytest.MonkeyPatch,
    bound: dict[str, object],
) -> None:
    calls = 0

    def load(root: Path) -> dict[str, object]:
        nonlocal calls
        assert root == ROOT
        calls += 1
        return bound

    monkeypatch.setattr(subject.i12_ingestion_owner, "load_frozen_formal_decision_v1", load)
    projected = subject.project_i12_completed_decision_v1(repo_root=ROOT)
    assert calls == 1
    assert len(projected.facts) == 4


def test_projector_wraps_ingestion_safety_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_root: Path) -> dict[str, object]:
        raise i12_ingestion_owner.I12IngestionSafetyError("owner failure")

    monkeypatch.setattr(subject.i12_ingestion_owner, "load_frozen_formal_decision_v1", fail)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="I12_INGESTION_OWNER_VALIDATION_FAILED",
    ):
        subject.project_i12_completed_decision_v1(repo_root=ROOT)


def test_projector_does_not_wrap_unrelated_base_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_root: Path) -> dict[str, object]:
        raise RuntimeError("base error")

    monkeypatch.setattr(subject.i12_ingestion_owner, "load_frozen_formal_decision_v1", fail)
    with pytest.raises(RuntimeError, match="base error"):
        subject.project_i12_completed_decision_v1(repo_root=ROOT)


def test_rich_i12_identity_decisions_and_candidate0_are_validated(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_i12_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    assert formal["human_review_completed"] is True
    assert formal["approved"] is True
    assert formal["decision_finalized"] is True
    assert formal["identity"]["review_unit_id"] == i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    assert formal["identity"]["canonical_event_ids"] == list(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    assert formal["identity"]["scaleup_ranks"] == [187, 188, 222, 223]
    assert formal["human_approval"]["D1_task_relevance"] == "RELEVANT"
    assert formal["human_approval"]["D2_chemistry"] == "POSITIVE"
    assert formal["human_approval"]["D3_reactive_pair"] == "CONFIRM_OBSERVED_PAIR"
    assert formal["human_approval"]["D4_role_partition"] == "SELECT_CANDIDATE_0"
    assert formal["human_approval"]["D5_training_use"] == "INCLUDE"
    role = formal["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 0
    assert role["human_selected"] is True
    assert role["machine_selected"] is False
    assert role["machine_recommended"] is False
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["applicable_task_ids"] == [0, 3, 4]
    assert len(events) == 4


def test_rich_authority_boundaries_are_proven_before_projection(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]
    assert isinstance(formal, dict)
    chemical = formal["chemical_warhead_boundary"]
    pre = formal["experimental_context_and_PRE_boundary"]
    post = formal["POST_evidence_boundary"]
    training = formal["training_use_human_decision"]
    authority = formal["authority_boundary"]
    assert chemical["chemical_warhead_human_authoritative"] is False
    assert chemical["chemical_warhead_atom_ids"] is None
    assert chemical["reaction_family_authority_created"] is False
    assert chemical["warhead_family_authority_created"] is False
    assert chemical["warhead_rule_authority_created"] is False
    assert pre["PRE_status"] == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
    assert pre["PRE_topology_authority_created"] is False
    assert pre["PRE_geometry_authority_created"] is False
    assert post["POST_source_evidence_count"] == 4
    assert post["POST_sample_authority_created"] is False
    assert post["POST_geometry_training_authority_created"] is False
    assert training["candidate_for_future_training_admission"] is True
    assert training["formal_training_admitted"] is False
    assert authority["warhead_type_authority_created"] is False
    assert authority["READY_FOR_TRAINING"] is False
    subject._validate_rich_i12_semantics_v1(bound)


def test_narrow_projection_exact4_and_namespace_distinction(
    bound: dict[str, object],
    source: generic.NormalizedDecisionSource,
) -> None:
    ingestion_binding = bound["formal_decision_binding"]
    assert isinstance(ingestion_binding, dict)
    assert ingestion_binding["namespace"] == "project_parent_relative"
    assert source.binding.path_namespace == "repository_parent_relative"
    assert source.binding.source_path == i12_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
    assert source.binding.byte_count == 26474
    assert source.binding.sha256 == "e117da5c10c45603450eaab26ea6093ef07e70c4bf2ec2f0c7908aa38f531fa0"
    assert tuple(fact.canonical_event_id for fact in source.facts) == tuple(
        sorted(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    )
    for fact in source.facts:
        assert fact.review_unit_id == i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
        assert fact.human_review_completed is True
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        assert fact.task_relevance_disposition == generic.TASK_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.training_disposition == generic.TRAINING_INCLUDE
        assert fact.human_training_excluded is False
        assert fact.source_decision_schema == "covapie_i12_exact4_formal_human_decision_v1"
        assert fact.source_decision_sha256 == source.binding.sha256
        assert fact.source_binding_path == source.binding.source_path


def test_generic_dataclass_and_facts_have_no_rich_field_leakage(
    source: generic.NormalizedDecisionSource,
) -> None:
    actual_fields = tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact))
    assert actual_fields == EXPECTED_FACT_FIELDS
    assert not set(actual_fields) & set(FORBIDDEN_RICH_FIELDS)
    for fact in source.facts:
        assert all(not hasattr(fact, name) for name in FORBIDDEN_RICH_FIELDS)
    with pytest.raises(TypeError):
        generic.NormalizedCompletedDecisionFact(
            **{name: getattr(source.facts[0], name) for name in actual_fields},
            role_profile="DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        )


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (("formal", "identity", "review_unit_id"), "WRONG", "I12_FORMAL_IDENTITY_NOT_EXACT4"),
        (("formal", "human_approval", "D1_task_relevance"), "NOT_RELEVANT", "I12_D1_D5_DECISIONS_INVALID"),
        (("formal", "human_approval", "D2_chemistry"), "NEGATIVE", "I12_D1_D5_DECISIONS_INVALID"),
        (("formal", "human_approval", "D3_reactive_pair"), "REJECT", "I12_D1_D5_DECISIONS_INVALID"),
        (("formal", "human_approval", "D4_role_partition"), "SELECT_CANDIDATE_1", "I12_D1_D5_DECISIONS_INVALID"),
        (("formal", "human_approval", "D5_training_use"), "EXCLUDE_FROM_TRAINING_ONLY", "I12_D1_D5_DECISIONS_INVALID"),
        (("formal", "selected_role_partition", "selected_candidate_index_0based"), 1, "I12_CANDIDATE0_DIRECT_ROLE_PARTITION_INVALID"),
        (("formal", "selected_role_partition", "role_profile"), "WRONG", "I12_CANDIDATE0_DIRECT_ROLE_PARTITION_INVALID"),
        (("formal", "training_use_human_decision", "formal_training_admitted"), True, "I12_TRAINING_OR_AUTHORITY_BOUNDARY_INVALID"),
    ),
)
def test_projector_rejects_rich_semantic_drift(
    bound: dict[str, object],
    path: tuple[str, ...],
    value: object,
    token: str,
) -> None:
    drifted = _drift(bound, *path, value=value)
    with pytest.raises(subject.CompletedDecisionReconciliationWithI12Error, match=token):
        subject._project_validated_i12_binding_v1(drifted)


def test_projector_rejects_wrong_event_id(bound: dict[str, object]) -> None:
    drifted = copy.deepcopy(bound)
    event = drifted["formal"]["event_level_human_decisions"][0]  # type: ignore[index]
    event["canonical_event_id"] = "WRONG_EVENT"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="I12_FORMAL_EVENT_COVERAGE_NOT_EXACT4",
    ):
        subject._project_validated_i12_binding_v1(drifted)


def test_projector_rejects_wrong_rank(bound: dict[str, object]) -> None:
    drifted = copy.deepcopy(bound)
    event = drifted["formal"]["event_level_human_decisions"][0]  # type: ignore[index]
    event["scaleup_rank"] = 999
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="I12_FORMAL_RANK_COVERAGE_NOT_EXACT4",
    ):
        subject._project_validated_i12_binding_v1(drifted)


def test_projector_rejects_source_formal_sha_drift(bound: dict[str, object]) -> None:
    drifted = copy.deepcopy(bound)
    drifted["formal_decision_binding"]["SHA256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="I12_FORMAL_DECISION_BINDING_INVALID",
    ):
        subject._project_validated_i12_binding_v1(drifted)


def test_historical_i12_prior_exact4_rank17_and_unreviewed(
    historical: tuple[dict[str, str], ...],
) -> None:
    subject._prove_i12_original_unreviewed_prior_v1(historical)
    expected = set(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    rows = [row for row in historical if row["canonical_event_id"] in expected]
    assert len(rows) == 4
    assert {row["raw_review_unit_id"] for row in rows} == {
        i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    }
    assert {row["raw_priority_rank"] for row in rows} == {"17"}
    assert {row["current_review_status"] for row in rows} == {generic.CURRENTLY_UNREVIEWED}
    assert {row["calibration_eligible"] for row in rows} == {"true"}
    assert {row["calibration_exclusion_reason"] for row in rows} == {""}


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("raw_review_unit_id", "WRONG", "I12_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT4"),
        ("raw_priority_rank", "18", "I12_HISTORICAL_IDENTITY_OR_PRIORITY_INVALID"),
        ("current_review_status", generic.COMPLETED_HUMAN_POSITIVE, "I12_PRIOR_STATE_NOT_EXACT4_UNREVIEWED"),
        ("calibration_eligible", "false", "I12_PRIOR_STATE_NOT_EXACT4_UNREVIEWED"),
        ("calibration_exclusion_reason", "WRONG", "I12_PRIOR_STATE_NOT_EXACT4_UNREVIEWED"),
    ),
)
def test_historical_proof_rejects_identity_or_prior_drift(
    historical: tuple[dict[str, str], ...],
    field: str,
    value: str,
    token: str,
) -> None:
    drifted = [dict(row) for row in historical]
    row = next(
        row
        for row in drifted
        if row["canonical_event_id"] == i12_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    row[field] = value
    with pytest.raises(subject.CompletedDecisionReconciliationWithI12Error, match=token):
        subject._prove_i12_original_unreviewed_prior_v1(drifted)


def test_onl_normalization_changes_zero_i12_rows(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    subject._prove_i12_rows_unchanged_after_onl_normalization_v1(historical, adapted)
    ids = set(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    before = {row["canonical_event_id"]: row for row in historical if row["canonical_event_id"] in ids}
    after = {row["canonical_event_id"]: row for row in adapted if row["canonical_event_id"] in ids}
    assert len(before) == len(after) == 4
    assert before == after


def test_onl_mutation_of_any_i12_field_fails_closed(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    changed = [dict(row) for row in adapted]
    row = next(
        row
        for row in changed
        if row["canonical_event_id"] == i12_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["changed"]'
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="ONL_ADAPTER_CHANGED_I12_ROW",
    ):
        subject._prove_i12_rows_unchanged_after_onl_normalization_v1(historical, changed)


def test_exact13_to_exact14_source_chain_is_append_only_and_collision_free(
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    existing = two_a2_successor.load_real_completed_decision_sources_with_2a2_v1(ROOT)
    assert len(existing) == 13
    assert [len(source.facts) for source in existing] == list(EXPECTED_COUNTS[:-1])
    assert sum(len(source.facts) for source in existing) == 95
    assert len(sources) == 14
    assert sources[:-1] == existing
    assert [len(source.facts) for source in sources] == list(EXPECTED_COUNTS)
    event_ids = [fact.canonical_event_id for source in sources for fact in source.facts]
    assert len(event_ids) == len(set(event_ids)) == 99
    assert len({source.binding.review_unit_id for source in sources}) == 14
    assert len({source.binding.stable_identity for source in sources}) == 14


@pytest.mark.parametrize(
    ("changes", "token"),
    (
        ({"training_disposition": generic.TRAINING_EXCLUDE}, "I12_SOURCE_PROJECTION_INVALID"),
        ({"human_training_excluded": True}, "I12_SOURCE_PROJECTION_INVALID"),
    ),
)
def test_source_loader_rejects_generic_fact_semantic_drift(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
    changes: dict[str, object],
    token: str,
) -> None:
    drifted = _replace_source_fact(source, 0, **changes)
    monkeypatch.setattr(subject, "project_i12_completed_decision_v1", lambda *, repo_root: drifted)
    with pytest.raises(subject.CompletedDecisionReconciliationWithI12Error, match=token):
        subject.load_real_completed_decision_sources_with_i12_v1(ROOT)


def test_source_loader_rejects_i12_event_collision_with_predecessor(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
) -> None:
    existing = list(two_a2_successor.load_real_completed_decision_sources_with_2a2_v1(ROOT))
    collision_id = source.facts[0].canonical_event_id
    existing[0] = _replace_source_fact(existing[0], 0, canonical_event_id=collision_id)
    monkeypatch.setattr(
        subject.two_a2_successor,
        "load_real_completed_decision_sources_with_2a2_v1",
        lambda _root: tuple(existing),
    )
    monkeypatch.setattr(subject, "project_i12_completed_decision_v1", lambda *, repo_root: source)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="I12_EVENT_COLLISION_WITH_PREDECESSOR",
    ):
        subject.load_real_completed_decision_sources_with_i12_v1(ROOT)


def test_source_loader_rejects_duplicate_stable_source_identity(
    monkeypatch: pytest.MonkeyPatch,
    source: generic.NormalizedDecisionSource,
) -> None:
    existing = list(two_a2_successor.load_real_completed_decision_sources_with_2a2_v1(ROOT))
    existing[0] = replace(existing[0], binding=source.binding)
    monkeypatch.setattr(
        subject.two_a2_successor,
        "load_real_completed_decision_sources_with_2a2_v1",
        lambda _root: tuple(existing),
    )
    monkeypatch.setattr(subject, "project_i12_completed_decision_v1", lambda *, repo_root: source)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithI12Error,
        match="REAL_SOURCE_CHAIN_NOT_EXACT14",
    ):
        subject.load_real_completed_decision_sources_with_i12_v1(ROOT)


def test_real_reconciliation_exact_summary_and_i12_transition(
    result: generic.ReconciliationResult,
) -> None:
    assert result.review_summary == EXPECTED_SUMMARY
    ids = set(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in ids]
    rows = [row for row in result.reconciled_rows if row["canonical_event_id"] in ids]
    assert len(facts) == len(rows) == 4
    assert all(fact.task_relevance_disposition == generic.TASK_RELEVANT for fact in facts)
    assert all(fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE for fact in facts)
    assert all(fact.training_disposition == generic.TRAINING_INCLUDE for fact in facts)
    assert all(fact.human_training_excluded is False for fact in facts)
    assert all(row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE for row in rows)


def test_source_order_remains_semantically_deterministic(
    sources: tuple[generic.NormalizedDecisionSource, ...],
    adapted: tuple[dict[str, str], ...],
) -> None:
    normal = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_result = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    assert normal == reversed_result


def test_production_pipeline_uses_historical_onl_sources_and_generic_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    historical = generic.load_real_historical_reconciliation_v1(ROOT)
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    sources = subject.load_real_completed_decision_sources_with_i12_v1(ROOT)
    expected = generic.reconcile_completed_human_decisions_v1(adapted, sources)

    def load_historical(root: Path):
        calls.append("historical")
        return historical

    def adapt(rows: object):
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

    monkeypatch.setattr(subject.generic, "load_real_historical_reconciliation_v1", load_historical)
    monkeypatch.setattr(
        subject.onl_successor,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        adapt,
    )
    monkeypatch.setattr(subject, "load_real_completed_decision_sources_with_i12_v1", load_sources)
    monkeypatch.setattr(subject.generic, "reconcile_completed_human_decisions_v1", reconcile)
    assert subject.reconcile_real_completed_human_decisions_with_i12_v1(ROOT) is expected
    assert calls == ["historical", "onl", "sources", "generic"]


def test_checker_repository_profiles_accept_only_exact_success_states(checker) -> None:
    expected = set(checker.EXACT4_PATHS)
    candidate = checker._classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple(sorted("?? " + path for path in expected)),
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    )
    tracked = checker._classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    )
    assert candidate == checker._CANDIDATE_UNTRACKED
    assert tracked == checker._TRACKED_CLEAN
    assert checker._SUPPORTED_REPOSITORY_PROFILES == (
        checker._CANDIDATE_UNTRACKED,
        checker._TRACKED_CLEAN,
    )


def test_candidate_repository_relation_accepts_only_published_baseline(checker) -> None:
    assert checker._validate_repository_relation_facts(
        profile=checker._CANDIDATE_UNTRACKED,
        branch="main",
        head=checker.BASELINE_COMMIT,
        origin=checker.BASELINE_COMMIT,
        relation="0\t0",
    ) == (0, 0)


def test_tracked_clean_committed_unpushed_relation_is_accepted(checker) -> None:
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


def test_tracked_clean_pushed_successor_relation_is_accepted(checker) -> None:
    successor = "a" * 40
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
    (
        "ahead_two",
        "behind_one",
        "diverged",
        "commit_count_two",
        "scope_extra",
        "scope_missing",
        "head_is_baseline",
        "origin_unrelated",
        "baseline_not_ancestor",
        "parent_not_baseline",
    ),
)
def test_tracked_clean_repository_relation_rejects_nonpublication_facts(
    checker, mutation: str
) -> None:
    successor = "a" * 40
    facts: dict[str, object] = {
        "profile": checker._TRACKED_CLEAN,
        "branch": "main",
        "head": successor,
        "origin": checker.BASELINE_COMMIT,
        "relation": "1\t0",
        "baseline_is_ancestor": True,
        "commit_count": 1,
        "head_parents": (checker.BASELINE_COMMIT,),
        "changed_paths": set(checker.EXACT4_PATHS),
    }
    if mutation == "ahead_two":
        facts["relation"] = "2\t0"
    elif mutation == "behind_one":
        facts["relation"] = "0\t1"
    elif mutation == "diverged":
        facts["relation"] = "1\t1"
    elif mutation == "commit_count_two":
        facts["commit_count"] = 2
    elif mutation == "scope_extra":
        facts["changed_paths"] = {*checker.EXACT4_PATHS, "extra.py"}
    elif mutation == "scope_missing":
        facts["changed_paths"] = set(checker.EXACT4_PATHS[:-1])
    elif mutation == "head_is_baseline":
        facts["head"] = checker.BASELINE_COMMIT
    elif mutation == "origin_unrelated":
        facts["origin"] = "b" * 40
    elif mutation == "baseline_not_ancestor":
        facts["baseline_is_ancestor"] = False
    else:
        facts["head_parents"] = ("b" * 40,)
    with pytest.raises(ValueError):
        checker._validate_repository_relation_facts(**facts)


@pytest.mark.parametrize("mutation", ("head", "relation"))
def test_candidate_repository_relation_rejects_nonbaseline_facts(
    checker, mutation: str
) -> None:
    facts = {
        "profile": checker._CANDIDATE_UNTRACKED,
        "branch": "main",
        "head": checker.BASELINE_COMMIT,
        "origin": checker.BASELINE_COMMIT,
        "relation": "0\t0",
    }
    if mutation == "head":
        facts["head"] = "a" * 40
    else:
        facts["relation"] = "1\t0"
    with pytest.raises(ValueError, match="CANDIDATE_REPOSITORY_RELATION_INVALID"):
        checker._validate_repository_relation_facts(**facts)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("branch", "topic", "REPOSITORY_BRANCH_INVALID"),
        ("head", "short", "REPOSITORY_COMMIT_IDENTITY_INVALID"),
        ("origin", "z" * 40, "REPOSITORY_COMMIT_IDENTITY_INVALID"),
        ("relation", "-1\t0", "REPOSITORY_AHEAD_BEHIND_INVALID"),
        ("relation", "1/0", "REPOSITORY_AHEAD_BEHIND_INVALID"),
    ),
)
def test_repository_relation_global_fact_parsing_fails_closed(
    checker, field: str, value: str, token: str
) -> None:
    facts = {
        "profile": checker._CANDIDATE_UNTRACKED,
        "branch": "main",
        "head": checker.BASELINE_COMMIT,
        "origin": checker.BASELINE_COMMIT,
        "relation": "0\t0",
    }
    facts[field] = value
    with pytest.raises(ValueError, match=token):
        checker._validate_repository_relation_facts(**facts)


def test_verify_repository_relation_wires_exact_tracked_clean_git_facts(
    checker, monkeypatch: pytest.MonkeyPatch
) -> None:
    successor = "a" * 40
    responses = {
        ("branch", "--show-current"): "main",
        ("rev-parse", "HEAD"): successor,
        ("rev-parse", "origin/main"): checker.BASELINE_COMMIT,
        ("rev-list", "--left-right", "--count", "HEAD...origin/main"): "1\t0",
        (
            "rev-list",
            "--count",
            checker.BASELINE_COMMIT + ".." + successor,
        ): "1",
        ("rev-list", "--parents", "-n", "1", successor): (
            successor + " " + checker.BASELINE_COMMIT
        ),
    }

    def fake_git(_root: Path, *arguments: str, binary: bool = False):
        assert binary is False
        return responses[arguments]

    def fake_git_nul(_root: Path, *arguments: str):
        assert arguments == (
            "diff",
            "--name-only",
            "-z",
            checker.BASELINE_COMMIT,
            successor,
        )
        return checker.EXACT4_PATHS

    monkeypatch.setattr(checker, "_git", fake_git)
    monkeypatch.setattr(checker, "_git_nul", fake_git_nul)
    monkeypatch.setattr(checker, "_git_is_ancestor", lambda *_args: True)
    assert checker._verify_repository_relation(ROOT, checker._TRACKED_CLEAN) == {
        "branch": "main",
        "HEAD": successor,
        "origin_main": checker.BASELINE_COMMIT,
        "ahead_behind": "1/0",
    }


@pytest.mark.parametrize(
    "mutation",
    ("extra", "staged", "modified", "partial", "mixed"),
)
def test_checker_repository_profile_rejects_mixed_or_dirty_states(
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
        status = tuple(line for line in status if checker.EXACT4_PATHS[0] not in line)
    else:
        tracked.add(checker.EXACT4_PATHS[0])
        untracked.remove(checker.EXACT4_PATHS[0])
        status = tuple(line for line in status if checker.EXACT4_PATHS[0] not in line)
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


def test_checker_runs_all_live_repository_semantic_and_b4_gates(checker) -> None:
    report = checker.run_check_v1(ROOT)
    assert report["status"] == "PASS"
    assert report["repository"]["candidate_file_count"] == 4
    # Live integration is neutral across the two separately proven profiles.
    assert report["repository"]["lifecycle"] in checker._SUPPORTED_REPOSITORY_PROFILES
    assert report["architecture"]["public_api"] == checker.EXPECTED_PUBLIC_API
    assert report["projection"]["generic_fact_fields"] == EXPECTED_FACT_FIELDS
    assert report["projection"]["rich_field_leakage_count"] == 0
    assert report["current_source_count"] == 13
    assert report["current_fact_count"] == 95
    assert report["future_source_count"] == 14
    assert report["future_fact_count"] == 99
    assert report["event_collisions"] == 0
    assert report["i12_prior_exact4_valid"] is True
    assert report["i12_rows_changed_by_onl"] == 0
    assert report["transition_adapter_created"] is False
    assert report["review_summary"] == EXPECTED_SUMMARY
    assert report["b4_core"]["new_semantic_exact_posix_mode_occurrence_count"] == 0
    assert report["b4_core"]["new_ambiguous_mode_occurrence_count"] == 0
    assert report["b4_core"]["new_reconciliation_files_scanned"] is True
    assert report["reconciliation_data_outputs_created"] == 0
    assert report["census_refresh"] is False
    assert report["queue_refresh"] is False
    assert report["training_started"] is False
    assert report["ready_for_training"] is False


def test_exact4_contains_no_data_census_queue_manifest_or_training_file(checker) -> None:
    assert len(checker.EXACT4_PATHS) == 4
    assert all(not path.startswith(("data/", "covapie-state/")) for path in checker.EXACT4_PATHS)
    assert all("manifest" not in path for path in checker.EXACT4_PATHS)
    assert all("census" not in path and "queue" not in path for path in checker.EXACT4_PATHS)
    assert all(not path.endswith((".csv", ".json")) for path in checker.EXACT4_PATHS)
