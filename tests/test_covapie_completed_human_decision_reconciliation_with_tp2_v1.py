"""Targeted contract tests for the TP2 reconciliation Exact4."""

from __future__ import annotations

import copy
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import covapie_completed_human_decision_reconciliation_with_tp2_v1 as subject
from covalent_ext import covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1 as ingestion

CHECKER = ROOT / subject.CHECKER_RELATIVE
ERROR = subject.CompletedDecisionReconciliationWithTP2Error


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location("tp2_reconciliation_checker", CHECKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return ingestion.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def components():
    return subject._build_components_v1(ROOT)


@pytest.fixture(scope="module")
def predecessor_sources(components):
    return components[0]


@pytest.fixture(scope="module")
def sources(components):
    return components[1]


@pytest.fixture(scope="module")
def predecessor_result(components):
    return components[2]


@pytest.fixture(scope="module")
def reconciliation(components):
    return components[3]


@pytest.fixture(scope="module")
def artifact_mapping(sources, reconciliation) -> dict[str, object]:
    return subject._artifact_mapping_v1(sources, reconciliation)


@pytest.fixture(scope="module")
def checker_report(checker) -> dict[str, object]:
    return checker.check(ROOT)


def test_public_api_is_exact() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithTP2Error",
        "project_tp2_completed_decision_v1",
        "load_real_completed_decision_sources_with_tp2_v1",
        "reconcile_real_completed_human_decisions_with_tp2_v1",
        "build_artifact_v1",
        "materialize_artifact_v1",
        "check_materialized_v1",
    )


def test_published_generic_projection_is_exact11(bound: dict[str, object]) -> None:
    source = subject._project_bound_tp2_v1(bound)
    binding, records = subject._projection_parts_v1(bound)
    assert source.binding == binding
    assert len(records) == len(source.facts) == 4
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == subject._GENERIC_FACT_FIELDS
    assert [asdict(fact) for fact in source.facts] == [dict(row) for row in records]
    assert all(tuple(row) == subject._GENERIC_FACT_FIELDS for row in records)
    assert not any(subject._FORBIDDEN_RICH_FACT_FIELDS & set(row) for row in records)


def test_tp2_classification_and_binding_are_exact(bound: dict[str, object]) -> None:
    source = subject._project_bound_tp2_v1(bound)
    assert source.binding == generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=17825,
        sha256="95fc125eefe09dd7ed81c9e95f2b76a084b889ece239aed5eb96215409315dc0",
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )
    assert [fact.canonical_event_id for fact in source.facts] == list(ingestion.EXPECTED_EVENT_IDS)
    assert all(
        fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_NEGATIVE
        and fact.task_relevance_disposition == generic.TASK_NOT_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_NOT_APPLICABLE
        and fact.human_training_excluded is False
        for fact in source.facts
    )


def test_rich_boundary_exact5_b3_and_no_training_authority(bound: dict[str, object]) -> None:
    subject._validate_rich_tp2_boundary_v1(bound)
    formal = bound["formal_document"]
    assert isinstance(formal, dict)
    role, tasks = formal["selected_role_context"], formal["canonical_Exact5"]
    assert role["warhead_atom_ids"] == ["S1"]
    assert role["linker_atom_ids"] == ["C2", "C3", "N4"]
    assert role["scaffold_atom_ids"] == list(ingestion.SCAFFOLD_ATOMS)
    assert role["minimal_seed"]["atom_ids"] == ["C5", "O21", "C6"]
    assert role["minimal_seed"]["primary_anchor"] == "C5"
    assert [row["semantic_long_name"] for row in tasks["tasks"]] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    assert tasks["role_derived_structural_applicability_task_ids"] == [0, 1, 2, 3, 4]
    assert tasks["B3_present"] is True and tasks["sixth_task"] is False
    assert tasks["authoritative_task_labels_created"] is False
    assert tasks["event_task_label_rows_materialized"] is False
    assert tasks["training_mask_targets_available_now"] is False
    assert formal["training_boundary"]["formal_training_admitted"] is False
    assert formal["training_boundary"]["READY_FOR_TRAINING"] is False
    assert all(value is False for value in formal["reusable_authority_map"].values())


def test_source_and_fact_chains_are_strict_prefix_append(
    bound, predecessor_sources, sources,
) -> None:
    _binding, records = subject._projection_parts_v1(bound)
    subject._validate_source_chain_v1(predecessor_sources, sources, records)
    assert len(predecessor_sources) == 23 and len(sources) == 24
    assert sources[:-1] == predecessor_sources
    old_facts = tuple(fact for source in predecessor_sources for fact in source.facts)
    facts = tuple(fact for source in sources for fact in source.facts)
    assert len(old_facts) == 135 and len(facts) == 139
    assert facts[:135] == old_facts and facts[135:] == sources[-1].facts
    assert len({source.binding.stable_identity for source in sources}) == 24
    assert len({source.binding.review_unit_id for source in sources}) == 24


def test_reconciliation_changes_exact4_and_preserves_334(
    predecessor_result, reconciliation,
) -> None:
    assert predecessor_result.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY
    assert reconciliation.review_summary == subject._SUCCESSOR_REVIEW_SUMMARY
    target_ids = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(predecessor_result.reconciled_rows, reconciliation.reconciled_rows, strict=True):
        if old["canonical_event_id"] in target_ids:
            changed_target += old != new
            assert {key for key in old if old[key] != new[key]} == subject._ALLOWED_RECONCILIATION_FIELDS
            assert old["raw_priority_rank"] == "27"
            assert new["current_review_status"] == generic.COMPLETED_HUMAN_NEGATIVE
            assert new["calibration_eligible"] == "false"
            assert new["calibration_exclusion_reason"] == generic.COMPLETED_HUMAN_NEGATIVE
        else:
            changed_non_target += old != new
    assert (changed_target, changed_non_target) == (4, 0)


def test_review_and_coverage_statistics_are_distinct_and_exact(components) -> None:
    assert subject._PREDECESSOR_REVIEW_SUMMARY["completed_total_unit_count"] == 27
    assert subject._SUCCESSOR_REVIEW_SUMMARY == {
        "universe_event_count": 338, "universe_review_unit_count": 131,
        "completed_positive_event_count": 119, "completed_positive_unit_count": 19,
        "completed_negative_event_count": 44, "completed_negative_unit_count": 9,
        "completed_total_event_count": 163, "completed_total_unit_count": 28,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "unreviewed_event_count": 175, "unreviewed_unit_count": 103,
    }
    assert subject.PREDECESSOR_COVERAGE_SUMMARY == subject.predecessor_owner.SUCCESSOR_COVERAGE_SUMMARY
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["decision_category_distribution"] == {
        "chemistry_positive": 95, "chemistry_negative": 20,
        "task_domain_negative": 24, "task_domain_positive": 0,
    }
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["accepted_review_unit_count"] == 24
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["training_mask_target_count"] == 0
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False


def test_artifact_contract_prefix_and_materialized_bytes(
    artifact_mapping, predecessor_sources, sources, reconciliation,
) -> None:
    subject._validate_artifact_mapping_v1(
        artifact_mapping, predecessor_sources=predecessor_sources,
        successor_sources=sources, reconciliation=reconciliation,
    )
    observed = (ROOT / subject.OUTPUT_RELATIVE).read_bytes()
    assert json.loads(observed) == artifact_mapping
    assert tuple(json.loads(observed)) == subject._ARTIFACT_FIELDS
    assert subject.check_materialized_v1(ROOT)["status"] == "PASS"


def test_deterministic_double_build() -> None:
    first = subject.build_artifact_v1(ROOT)
    second = subject.build_artifact_v1(ROOT)
    assert first == second == (ROOT / subject.OUTPUT_RELATIVE).read_bytes()


def test_real_checker_and_lifecycle_profiles(checker, checker_report) -> None:
    assert checker_report["status"] == "PASS"
    assert checker_report["repository"]["lifecycle"] in {checker.CANDIDATE_UNTRACKED, checker.TRACKED_CLEAN}
    assert checker_report["artifact"] == {
        "source_count": 24, "accepted_fact_count": 139,
        "reconciled_row_count": 338, "changed_target_rows": 4,
        "unchanged_rows": 334, "non_target_changed_rows": 0,
        "duplicate_count": 0,
    }
    assert all(checker_report["lifecycle_simulations"].values())
    assert all(checker_report["tamper_probes"].values())
    assert checker_report["census_refresh"] is False
    assert checker_report["queue_refresh"] is False
    assert checker_report["next_review_started"] is False
    assert checker_report["training_started"] is False


def test_checker_candidate_and_tracked_clean_profiles(checker) -> None:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    expected = set(paths)
    assert checker.classify_repository_profile(
        expected_paths=paths, tracked_paths=set(), ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in paths), working_diff=set(), cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=paths, tracked_paths=expected, ordinary_untracked=set(),
        status_lines=(), working_diff=set(), cached_diff=set(),
    ) == checker.TRACKED_CLEAN


def test_checker_future_committed_pushed_and_descendant_profiles(checker) -> None:
    expected = {path.as_posix() for path in subject.EXACT4_PATHS}
    common = dict(
        profile=checker.TRACKED_CLEAN, expected_paths=expected, behind=0,
        baseline_is_ancestor_of_head=True, baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True, changed_since_baseline=expected,
    )
    checker.validate_repository_relation_values(**common, head="new", origin_main=checker.BASELINE_COMMIT, ahead=1)
    checker.validate_repository_relation_values(**common, head="new", origin_main="new", ahead=0)
    checker.validate_repository_relation_values(
        **{**common, "changed_since_baseline": {*expected, "docs/later.md"}},
        head="later", origin_main="new", ahead=1,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("chemistry_disposition", "NEGATIVE"),
        ("task_relevance_disposition", "RELEVANT"),
        ("training_disposition", "INCLUDE"),
        ("source_binding_path", "tampered/source.json"),
    ),
)
def test_projection_tamper_fails_closed(bound, field: str, value: object) -> None:
    source = subject._project_bound_tp2_v1(bound)
    _binding, records = subject._projection_parts_v1(bound)
    facts = list(source.facts)
    facts[0] = replace(facts[0], **{field: value})
    candidate = generic.NormalizedDecisionSource(binding=source.binding, facts=tuple(facts))
    with pytest.raises(ERROR, match="TP2_GENERIC_PROJECTION_CLASSIFICATION_INVALID"):
        subject._validate_projected_tp2_source_v1(candidate, records)


def test_duplicate_source_event_and_missing_fact_fail_closed(bound, predecessor_sources, sources) -> None:
    _binding, records = subject._projection_parts_v1(bound)
    duplicate_source = (*predecessor_sources, predecessor_sources[-1])
    with pytest.raises(ERROR, match="TP2_GENERIC_PROJECTION_CLASSIFICATION_INVALID|TP2_SOURCE"):
        subject._validate_source_chain_v1(predecessor_sources, duplicate_source, records)
    duplicate_fact_source = generic.NormalizedDecisionSource(
        binding=sources[-1].binding,
        facts=(sources[-1].facts[0], sources[-1].facts[0], *sources[-1].facts[2:]),
    )
    with pytest.raises(ERROR, match="TP2_GENERIC_PROJECTION_CLASSIFICATION_INVALID"):
        subject._validate_source_chain_v1(predecessor_sources, (*predecessor_sources, duplicate_fact_source), records)
    missing = generic.NormalizedDecisionSource(binding=sources[-1].binding, facts=sources[-1].facts[:-1])
    with pytest.raises(ERROR, match="PREFIX_APPEND_EXACT24_139"):
        subject._validate_source_chain_v1(predecessor_sources, (*predecessor_sources, missing), records)


def test_semantic_tampers_do_not_hide_behind_byte_guard(checker, artifact_mapping) -> None:
    old = json.loads((ROOT / subject.predecessor_owner.OUTPUT_RELATIVE).read_bytes())
    bound = ingestion.load_frozen_formal_decision_v1(ROOT)
    projection = checker._expected_projection_from_ingestion(bound)
    cases = []
    candidate = copy.deepcopy(artifact_mapping); candidate["normalized_facts"][0], candidate["normalized_facts"][1] = candidate["normalized_facts"][1], candidate["normalized_facts"][0]
    cases.append((candidate, "PREDECESSOR_FACT_PREFIX_INVALID"))
    candidate = copy.deepcopy(artifact_mapping); candidate["normalized_facts"][-1]["task_relevance_disposition"] = "RELEVANT"
    cases.append((candidate, "TP2_FACTS_NOT_EXACT_INGESTION_PROJECTION"))
    candidate = copy.deepcopy(artifact_mapping); candidate["normalized_facts"].pop()
    cases.append((candidate, "ARTIFACT_EXACT_COUNTS_INVALID"))
    candidate = copy.deepcopy(artifact_mapping); candidate["source_bindings"][-1] = copy.deepcopy(candidate["source_bindings"][0])
    cases.append((candidate, "ARTIFACT_SOURCE_IDENTITY_DUPLICATE"))
    candidate = copy.deepcopy(artifact_mapping); candidate["normalized_facts"][-1]["role_profile"] = "STRICT_LINKER_PRESENT_V1"
    cases.append((candidate, "ARTIFACT_GENERIC_FACT_NOT_EXACT11"))
    candidate = copy.deepcopy(artifact_mapping); candidate["reconciled_rows"][0]["raw_priority_rank"] = "999"
    cases.append((candidate, "RECONCILIATION_DELTA_NOT_EXACT4_ONLY"))
    candidate = copy.deepcopy(artifact_mapping); candidate["review_summary"]["completed_total_event_count"] = 162
    cases.append((candidate, "ARTIFACT_REVIEW_SUMMARY_INVALID"))
    for candidate, token in cases:
        with pytest.raises(ValueError, match=token) as caught:
            checker._verify_artifact_semantics(candidate, predecessor_artifact=old, expected_projection=projection)
        assert "MATERIALIZED_ARTIFACT_BYTES_MISMATCH" not in str(caught.value)


def test_raw_byte_corruption_probe_is_separate(checker) -> None:
    payload = (ROOT / subject.OUTPUT_RELATIVE).read_bytes()
    with pytest.raises(ValueError, match="MATERIALIZED_ARTIFACT_BYTES_MISMATCH"):
        checker._verify_byte_identity(payload, payload + b" ")


def test_destination_and_history_protection_fail_closed(checker) -> None:
    with pytest.raises(ERROR, match="ARTIFACT_DESTINATION_NOT_EXACT"):
        subject._validate_destination_v1(ROOT, ROOT / "unauthorized.json")
    for changed, token in (
        ({"data/raw/new.cif"}, "PROTECTED_PATH_CHANGED"),
        ({"equivariant_diffusion/new.py"}, "PROTECTED_PATH_CHANGED"),
        ({"dataset.py"}, "PROTECTED_PATH_CHANGED"),
        ({"docs/model.ckpt"}, "FORBIDDEN_SUFFIX_CHANGED"),
    ):
        with pytest.raises(ValueError, match=token):
            checker._validate_history_scope(changed)
