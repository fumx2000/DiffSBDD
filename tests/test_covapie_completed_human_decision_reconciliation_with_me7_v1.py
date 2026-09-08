from __future__ import annotations

import copy
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_me7_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_pyr_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_tp2_v1 as adapter  # noqa: E402
from covalent_ext import covapie_me7_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


EXPECTED_API = (
    "CompletedDecisionReconciliationWithME7Error",
    "project_me7_completed_decision_v1",
    "load_real_completed_decision_sources_with_me7_v1",
    "reconcile_real_completed_human_decisions_with_me7_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)
EXPECTED_PATHS = (
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_me7_v1.py",
    "scripts/check_covapie_completed_human_decision_reconciliation_with_me7_v1.py",
    "tests/test_covapie_completed_human_decision_reconciliation_with_me7_v1.py",
    "data/derived/covalent_small/covapie_completed_human_decision_reconciliation_with_me7_v1/covapie_completed_human_decision_reconciliation_with_me7_v1.json",
)
GENERIC_FIELDS = tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)


@pytest.fixture(scope="session")
def checker():
    path = ROOT / EXPECTED_PATHS[1]
    spec = importlib.util.spec_from_file_location("me7_reconciliation_checker_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def bound() -> dict[str, object]:
    return ingestion.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="session")
def projection(bound) -> list[dict[str, object]]:
    compatibility = bound["generic_Exact11_compatibility"]
    return copy.deepcopy(compatibility["facts"])


@pytest.fixture(scope="session")
def source_chain():
    before = predecessor.load_real_completed_decision_sources_with_pyr_v1(ROOT)
    after = subject.load_real_completed_decision_sources_with_me7_v1(ROOT)
    return before, after


@pytest.fixture(scope="session")
def results(source_chain, projection):
    before_sources, _after_sources = source_chain
    adapted = adapter._adapt_historical_v1(ROOT)
    before = generic.reconcile_completed_human_decisions_v1(adapted, before_sources)
    binding = generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=13344,
        sha256="9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407",
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )
    source = generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(
            generic.NormalizedCompletedDecisionFact(**fact) for fact in projection
        ),
    )
    after = generic.reconcile_completed_human_decisions_v1(
        adapted, (*before_sources, source)
    )
    return before, after


@pytest.fixture(scope="session")
def artifacts():
    old = json.loads((ROOT / predecessor.OUTPUT_RELATIVE).read_bytes())
    new = json.loads((ROOT / subject.OUTPUT_RELATIVE).read_bytes())
    return old, new


@pytest.fixture(scope="session")
def checker_report(checker):
    return checker.check(ROOT)


def test_public_api_and_exact4_inventory_are_exact() -> None:
    assert subject.__all__ == EXPECTED_API
    assert tuple(path.as_posix() for path in subject.EXACT4_PATHS) == EXPECTED_PATHS
    assert subject.ERROR_PREFIX == "COVAPIE_ME7_RECONCILIATION_V1_ERROR"


def test_projection_is_exact3_exact11_task_domain_negative(bound, projection) -> None:
    projected = subject.project_me7_completed_decision_v1(repo_root=ROOT)
    assert [asdict(fact) for fact in projected.facts] == projection
    assert len(projected.facts) == 3
    assert all(tuple(asdict(fact)) == GENERIC_FIELDS for fact in projected.facts)
    assert all(
        fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_NEGATIVE
        and fact.task_relevance_disposition == generic.TASK_NOT_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_NOT_APPLICABLE
        and fact.human_training_excluded is False
        for fact in projected.facts
    )
    assert bound["generic_Exact11_compatibility"]["facts"] == projection


def test_rich_null_and_context_firewalls_are_preserved(bound) -> None:
    formal = bound["formal_document"]
    decisions = formal["approved_D1_D6"]
    roles = formal["role_and_task_disposition"]
    assert decisions["D1_observation_record_judgment"]["decision"] == "POSITIVE"
    assert decisions["D2_project_domain_relevance"]["decision"] == "OUT_OF_DOMAIN"
    assert decisions["D3_recorded_endpoint_confirmation"]["pair"] == "SG:CAE"
    assert decisions["D3_recorded_endpoint_confirmation"][
        "target_pair_is_only_attachment_for_component_instance"
    ] is False
    assert decisions["D4_role_partition_and_retained_information"][
        "decision"
    ] == "CANNOT_DETERMINE"
    assert decisions["D5_structural_task_applicability"] == {
        "decision": "NOT_DETERMINABLE",
        "human_answered": True,
        "human_approved": True,
        "task_ids": None,
    }
    assert decisions["D6_later_use_disposition"]["decision"] == "NOT_APPLICABLE"
    assert roles["applicable_task_ids"] is None
    assert roles["selected_candidate_id"] is None
    assert roles["role_runtime_executed"] is False
    assert roles["task_runtime_executed"] is False
    assert roles["B3_present"] is True
    assert roles["sixth_task_created"] is False
    assert {row["scaleup_rank"] for row in bound["context_only_graph_records"]} == {
        527,
        530,
        533,
    }


def test_source_and_fact_chains_are_strict_prefix_append(source_chain) -> None:
    before, after = source_chain
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    assert (len(before), len(after)) == (27, 28)
    assert (len(before_facts), len(after_facts)) == (151, 154)
    assert after[:-1] == before
    assert after_facts[:151] == before_facts
    assert after_facts[151:] == after[-1].facts
    assert len({source.binding.stable_identity for source in after}) == 28
    assert len({fact.canonical_event_id for fact in after_facts}) == 154
    assert [fact.canonical_event_id for fact in after_facts[-3:]] == list(
        ingestion.EXPECTED_EVENT_IDS
    )


def test_published_adapter_reproduces_with_pyr_predecessor(results) -> None:
    before, _after = results
    published = predecessor.reconcile_real_completed_human_decisions_with_pyr_v1(
        ROOT
    )
    assert before == published
    assert before.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY


def test_reconciliation_changes_only_three_target_rows(results) -> None:
    before, after = results
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(before.reconciled_rows, after.reconciled_rows, strict=True):
        if old["canonical_event_id"] not in targets:
            changed_non_target += old != new
            continue
        assert old["raw_priority_rank"] == "32"
        assert old["raw_unit_event_count"] == "3"
        assert old["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        assert new["current_review_status"] == generic.COMPLETED_HUMAN_NEGATIVE
        assert new["current_status_authority_sources_json"] == generic._canonical_json(
            [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
        )
        assert new["calibration_eligible"] == "false"
        assert (
            new["calibration_exclusion_reason"]
            == generic.COMPLETED_HUMAN_NEGATIVE
        )
        assert {
            key for key in old if old[key] != new[key]
        } == subject._ALLOWED_RECONCILIATION_FIELDS
        changed_target += old != new
    assert (changed_target, changed_non_target) == (3, 0)


def test_review_summary_is_computed_negative_delta(results) -> None:
    before, after = results
    assert before.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY
    assert after.review_summary == subject._SUCCESSOR_REVIEW_SUMMARY
    assert after.review_summary["completed_positive_event_count"] == 127
    assert after.review_summary["completed_negative_event_count"] == 51
    assert after.review_summary["unreviewed_event_count"] == 160


def test_coverage_is_predecessor_aggregate_plus_local_task_negative(
    source_chain,
) -> None:
    before, after = source_chain
    assert subject.PREDECESSOR_COVERAGE_SUMMARY == predecessor.SUCCESSOR_COVERAGE_SUMMARY
    assert subject.SUCCESSOR_COVERAGE_SUMMARY == {
        "accepted_fact_count": 154,
        "accepted_review_unit_count": 28,
        "stable_source_identity_count": 28,
        "remaining_unreviewed_chemistry_event_count": 184,
        "remaining_unreviewed_review_unit_upper_bound": 103,
        "decision_category_distribution": {
            "chemistry_positive": 103,
            "chemistry_negative": 20,
            "task_domain_negative": 31,
            "task_domain_positive": 0,
        },
        "label_ready_event_count": 16,
        "training_mask_target_count": 0,
        "training_authority": False,
    }
    assert sum(len(source.facts) for source in before) == 151
    assert sum(len(source.facts) for source in after) == 154
    assert sum(
        subject.SUCCESSOR_COVERAGE_SUMMARY[
            "decision_category_distribution"
        ].values()
    ) == 154


def test_artifact_contract_prefix_and_materialized_bytes(artifacts, source_chain) -> None:
    old, new = artifacts
    before_sources, after_sources = source_chain
    assert tuple(new) == subject._ARTIFACT_FIELDS
    assert len(new["reconciled_rows"]) == 338
    assert new["source_bindings"][:27] == old["source_bindings"]
    assert new["normalized_facts"][:151] == old["normalized_facts"]
    assert new["source_bindings"] == [asdict(source.binding) for source in after_sources]
    assert new["normalized_facts"] == [
        asdict(fact) for source in after_sources for fact in source.facts
    ]
    assert old["source_bindings"] == [
        asdict(source.binding) for source in before_sources
    ]
    observed = (ROOT / subject.OUTPUT_RELATIVE).read_bytes()
    assert observed == subject.build_artifact_v1(ROOT)


def test_materialized_check_and_double_build() -> None:
    first = subject.build_artifact_v1(ROOT)
    second = subject.build_artifact_v1(ROOT)
    assert first == second
    assert subject.check_materialized_v1(ROOT) == {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 28,
        "accepted_fact_count": 154,
        "changed_target_rows": 3,
        "non_target_changed_rows": 0,
        "unchanged_rows": 335,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }


def test_real_checker_and_required_negative_probes(checker_report) -> None:
    assert checker_report["status"] == "PASS"
    assert checker_report["repository"]["profile"] in {
        "CANDIDATE_UNTRACKED",
        "TRACKED_CLEAN",
    }
    required = {
        "wrong_event",
        "wrong_unit",
        "wrong_schema",
        "wrong_digest",
        "wrong_formal_path",
        "legacy_positive",
        "normalized_relevant",
        "chemistry_negative",
        "training_exclude",
        "human_excluded_true",
        "pair_leak",
        "role_leak",
        "seed_leak",
        "task_ids_leak",
        "geometry_leak",
        "missing_target",
        "fourth_target",
        "duplicate_target",
        "context_only_added",
        "source_prefix_reordered",
        "fact_prefix_modified",
        "duplicate_source",
        "target_still_pending",
        "not_applicable_as_exclusion_reason",
        "non_target_changed",
        "positive_summary_plus3",
        "negative_summary_not_plus3",
        "coverage_double_count_chemistry",
        "coverage_task_negative_not_plus3",
        "coverage_wrong_population",
        "label_ready_increased",
        "training_mask_created",
        "training_authority_forged",
        "census_refresh_forged",
        "queue_refresh_forged",
        "next_review_started_forged",
        "task_label_authority_forged",
        "training_started_forged",
        "formal_D2_changed",
        "formal_D4_role_forged",
        "formal_D5_task_forged",
        "formal_review_incomplete",
        "raw_byte_corruption",
        "filesystem_executable_bit",
        "unexpected_fifth_file",
    }
    assert set(checker_report["tamper_probes"]) == required
    assert all(checker_report["tamper_probes"].values())
    assert checker_report["artifact"]["changed_target_rows"] == 3
    assert checker_report["artifact"]["non_target_changed_rows"] == 0
    assert checker_report["artifact"]["unchanged_rows"] == 335


def test_checker_tamper_helper_accepts_only_exact_prefixed_valueerror(checker) -> None:
    token = "PROBE_TOKEN"
    assert checker._expect_tamper(
        "probe", token, lambda: checker._fail(token)
    ) == token
    with pytest.raises(ValueError, match="WRONG_TOKEN"):
        checker._expect_tamper(
            "probe", token, lambda: checker._fail("WRONG_TOKEN")
        )
    for exception in (TypeError("x"), KeyError("x"), AssertionError("x")):
        with pytest.raises(type(exception)):
            checker._expect_tamper(
                "probe", token, lambda exception=exception: (_ for _ in ()).throw(exception)
            )


def test_checker_candidate_and_tracked_clean_profiles(checker) -> None:
    paths = EXPECTED_PATHS
    expected = set(paths)
    assert checker.classify_repository_profile(
        expected_paths=paths,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in reversed(paths)),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=paths,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN


def _assert_supported_repository_lifecycle(
    report: dict[str, object],
    status_lines: tuple[str, ...],
    checker,
) -> None:
    assert report.get("branch") == "main"
    assert report.get("tracked_modification_count") == 0
    assert report.get("staged_count") == 0
    assert report.get("conflicted_count") == 0
    assert report.get("expected_git_publication_mode") == "100644"
    assert len(status_lines) == len(set(status_lines))

    profile = report.get("profile")
    if profile == checker.CANDIDATE_UNTRACKED:
        paths = report.get("ordinary_untracked_paths")
        assert type(paths) is list
        assert report.get("ordinary_untracked_count") == 4
        assert len(paths) == len(set(paths)) == 4
        assert set(paths) == set(EXPECTED_PATHS)
        assert len(status_lines) == 4
        assert set(status_lines) == {"?? " + path for path in EXPECTED_PATHS}
        assert report.get("git_index_mode_checked") is False
        assert "git_index_modes" not in report
        assert "git_index_record_count" not in report
        return
    if profile == checker.TRACKED_CLEAN:
        assert report.get("ordinary_untracked_count") == 0
        assert report.get("ordinary_untracked_paths") == []
        assert status_lines == ()
        assert report.get("git_index_mode_checked") is True
        assert report.get("git_index_record_count") == 4
        modes = report.get("git_index_modes")
        assert type(modes) is dict
        assert len(modes) == 4
        assert set(modes) == set(EXPECTED_PATHS)
        assert set(modes.values()) == {"100644"}
        return
    raise AssertionError("unsupported repository lifecycle profile")


@pytest.mark.parametrize(
    "case,should_pass",
    [
        ("candidate_ok", True),
        ("tracked_ok", True),
        ("unknown_profile", False),
        ("candidate_extra_path", False),
        ("candidate_index_checked", False),
        ("tracked_untracked_residue", False),
        ("tracked_missing_mode", False),
        ("tracked_executable_mode", False),
    ],
)
def test_supported_repository_lifecycle_assertion_helper(
    checker, case, should_pass
) -> None:
    common = {
        "branch": "main",
        "tracked_modification_count": 0,
        "staged_count": 0,
        "conflicted_count": 0,
        "expected_git_publication_mode": "100644",
    }
    candidate = {
        **common,
        "profile": checker.CANDIDATE_UNTRACKED,
        "ordinary_untracked_count": 4,
        "ordinary_untracked_paths": list(reversed(EXPECTED_PATHS)),
        "git_index_mode_checked": False,
    }
    tracked = {
        **common,
        "profile": checker.TRACKED_CLEAN,
        "ordinary_untracked_count": 0,
        "ordinary_untracked_paths": [],
        "git_index_mode_checked": True,
        "git_index_record_count": 4,
        "git_index_modes": {path: "100644" for path in reversed(EXPECTED_PATHS)},
    }
    candidate_status = tuple("?? " + path for path in EXPECTED_PATHS)
    report, status = (
        (candidate, candidate_status)
        if case.startswith("candidate")
        else (tracked, ())
    )
    if case == "unknown_profile":
        report = {**candidate, "profile": "UNKNOWN"}
        status = candidate_status
    elif case == "candidate_extra_path":
        report = {
            **candidate,
            "ordinary_untracked_count": 5,
            "ordinary_untracked_paths": [*candidate["ordinary_untracked_paths"], "extra"],
        }
        status = (*candidate_status, "?? extra")
    elif case == "candidate_index_checked":
        report = {**candidate, "git_index_mode_checked": True}
    elif case == "tracked_untracked_residue":
        report = {
            **tracked,
            "ordinary_untracked_count": 1,
            "ordinary_untracked_paths": ["extra"],
        }
        status = ("?? extra",)
    elif case == "tracked_missing_mode":
        report = {
            **tracked,
            "git_index_modes": {
                path: "100644" for path in EXPECTED_PATHS[:-1]
            },
        }
    elif case == "tracked_executable_mode":
        modes = dict(tracked["git_index_modes"])
        modes[EXPECTED_PATHS[0]] = "100755"
        report = {**tracked, "git_index_modes": modes}

    if should_pass:
        _assert_supported_repository_lifecycle(report, status, checker)
    else:
        with pytest.raises(AssertionError):
            _assert_supported_repository_lifecycle(report, status, checker)


@pytest.mark.parametrize(
    "mutation,token",
    [
        ("missing", "TRACKED_GIT_INDEX_MODE_INVALID"),
        ("duplicate", "TRACKED_GIT_INDEX_MODE_INVALID"),
        ("executable", "TRACKED_GIT_INDEX_MODE_INVALID"),
        ("symlink", "TRACKED_GIT_INDEX_MODE_INVALID"),
        ("nonzero_stage", "TRACKED_GIT_INDEX_MODE_INVALID"),
    ],
)
def test_tracked_index_mode_parser_fails_closed(checker, mutation, token) -> None:
    expected = set(EXPECTED_PATHS)
    lines = [f"100644 {'0' * 40} 0\t{path}" for path in EXPECTED_PATHS]
    if mutation == "missing":
        lines.pop()
    elif mutation == "duplicate":
        lines[-1] = lines[0]
    elif mutation == "executable":
        lines[0] = lines[0].replace("100644", "100755", 1)
    elif mutation == "symlink":
        lines[0] = lines[0].replace("100644", "120000", 1)
    else:
        lines[0] = lines[0].replace(" 0\t", " 1\t", 1)
    with pytest.raises(ValueError, match=token):
        checker.validate_tracked_index_modes(tuple(lines), expected)


@pytest.mark.parametrize(
    "field,value",
    [
        ("legacy_completed_review_status", generic.COMPLETED_HUMAN_POSITIVE),
        ("task_relevance_disposition", generic.TASK_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("training_disposition", generic.TRAINING_EXCLUDE),
        ("human_training_excluded", True),
    ],
)
def test_projected_classification_tamper_fails_closed(
    bound, field, value
) -> None:
    source = subject._project_bound_me7_v1(bound)
    records = subject._projection_records_v1(bound)
    changed_fact = replace(source.facts[-1], **{field: value})
    changed = generic.NormalizedDecisionSource(
        binding=source.binding,
        facts=(*source.facts[:-1], changed_fact),
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithME7Error,
        match="ME7_GENERIC_PROJECTION_CLASSIFICATION_INVALID",
    ):
        subject._validate_projected_me7_source_v1(changed, records)


@pytest.mark.parametrize(
    "path,value,token",
    [
        (
            ("approved_D1_D6", "D2_project_domain_relevance", "decision"),
            "IN_DOMAIN",
            "ME7_D1_D6_BOUNDARY_INVALID",
        ),
        (
            ("approved_D1_D6", "D4_role_partition_and_retained_information", "selected_candidate_id"),
            "FORGED",
            "ME7_D1_D6_BOUNDARY_INVALID",
        ),
        (
            ("approved_D1_D6", "D5_structural_task_applicability", "task_ids"),
            [0],
            "ME7_D1_D6_BOUNDARY_INVALID",
        ),
        (
            ("sample_level_authority", "human_review_completed"),
            False,
            "ME7_APPROVAL_STATE_INVALID",
        ),
    ],
)
def test_rich_identity_null_and_authority_tampers_fail_closed(
    bound, path, value, token
) -> None:
    changed = copy.deepcopy(bound)
    target = changed["formal_document"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithME7Error, match=token
    ):
        subject._project_bound_me7_v1(changed)


def test_source_chain_missing_duplicate_and_reorder_fail_closed(
    bound, source_chain
) -> None:
    before, after = source_chain
    records = subject._projection_records_v1(bound)
    cases = (
        (after[:-1], "ME7_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT28_154"),
        ((*before, before[-1]), "ME7_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT28_154"),
        ((*before[:-1], before[-1], before[-2]), "ME7_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT28_154"),
    )
    for changed, token in cases:
        with pytest.raises(
            subject.CompletedDecisionReconciliationWithME7Error, match=token
        ):
            subject._validate_source_chain_v1(before, changed, records)


def test_live_repository_supported_lifecycle_and_index_contract(checker) -> None:
    report = checker._verify_repository(ROOT)
    process = subprocess.run(
        ("git", "status", "--short", "--untracked-files=all"),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0
    assert process.stderr == ""
    _assert_supported_repository_lifecycle(
        report, tuple(process.stdout.splitlines()), checker
    )
