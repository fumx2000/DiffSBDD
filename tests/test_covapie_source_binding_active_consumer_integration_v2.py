from __future__ import annotations

import copy
import importlib.util
import inspect
from pathlib import Path
import subprocess

import pytest

from covalent_ext import (
    covapie_source_binding_active_consumer_integration_v2 as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT / "scripts/check_covapie_source_binding_active_consumer_integration_v2.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_source_binding_active_consumer_integration_v2",
    CHECKER_PATH,
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="session")
def verified_integration():
    result, captured = checker._verify_behavioral_order(ROOT)
    inventories = checker._verify_projection_artifacts(captured)
    census = checker._verify_census(ROOT)
    assert checker._verify_result(
        result,
        projections=inventories,
        census=census,
    ) is True
    return result, captured, inventories, census


def test_strict_exact4_inventory_and_actual_lifecycle() -> None:
    assert checker.EXACT4_PATHS == (
        "src/covalent_ext/covapie_source_binding_active_consumer_integration_v2.py",
        "scripts/check_covapie_source_binding_active_consumer_integration_v2.py",
        "tests/test_covapie_source_binding_active_consumer_integration_v2.py",
        "docs/covapie_source_binding_active_consumer_integration_v2_guide.md",
    )
    assert checker.verify_git_lifecycle(ROOT) in {
        "CANDIDATE_UNTRACKED",
        "TRACKED_CLEAN",
    }
    assert set(checker._verify_exact4_hygiene(ROOT)) == set(checker.EXACT4_PATHS)


def test_exact_public_api_and_no_mutation_api() -> None:
    assert subject.__all__ == (
        "SourceBindingActiveConsumerIntegrationV2Error",
        "verify_covapie_source_binding_active_consumer_integration_v2",
    )
    signature = inspect.signature(
        subject.verify_covapie_source_binding_active_consumer_integration_v2
    )
    parameter = tuple(signature.parameters.values())
    assert len(parameter) == 1
    assert parameter[0].name == "repo_root"
    assert parameter[0].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter[0].annotation == "Path"
    assert signature.return_annotation == "dict[str, object]"
    assert all(
        token not in name.lower()
        for name in subject.__all__
        for token in ("override", "write", "materialize", "reconcile", "refresh")
    )


def test_production_ast_call_graph_and_safety_restrictions() -> None:
    checker._verify_public_api()
    checker._verify_production_ast(ROOT)


def test_all_published_dependencies_are_b1_bound_and_reachable() -> None:
    dependencies = checker._verify_published_dependencies(ROOT)
    assert tuple(dependencies) == checker.CONSUMERS
    for consumer, record in dependencies.items():
        assert record["bound"] is True
        completed = subprocess.run(
            (
                "git",
                "merge-base",
                "--is-ancestor",
                str(record["published_commit"]),
                "HEAD",
            ),
            cwd=ROOT,
            check=False,
        )
        assert completed.returncode == 0, consumer


def test_all_six_projection_wrappers_execute_exact_published_exact4(
    verified_integration,
) -> None:
    result, captured, inventories, _census = verified_integration
    assert tuple(captured) == checker.CONSUMERS
    assert tuple(inventories) == checker.CONSUMERS
    assert sum(len(artifacts) for artifacts in captured.values()) == 24
    assert result["active_consumer_order"] == list(checker.CONSUMERS)
    assert result["active_consumer_count"] == 6
    assert result["artifact_projection_count"] == 24
    assert result["all_V2_projections_executed"] is True
    assert result["all_V1_scientific_projections_preserved"] is True


@pytest.mark.parametrize("consumer", checker.CONSUMERS)
def test_each_consumer_returns_exact_four_artifact_inventory(
    verified_integration,
    consumer: str,
) -> None:
    _result, captured, inventories, _census = verified_integration
    expected = dict(checker.PROJECTION_SPECS)[consumer]
    assert tuple(captured[consumer]) == tuple(item[0] for item in expected)
    assert len(inventories[consumer]) == 4
    for filename, byte_count, sha256 in expected:
        assert inventories[consumer][filename] == {
            "byte_count": byte_count,
            "sha256": sha256,
        }


def test_projection_validation_fails_closed_on_byte_drift(
    verified_integration,
) -> None:
    _result, captured, _inventories, _census = verified_integration
    projections = []
    for consumer in checker.CONSUMERS:
        artifacts = dict(captured[consumer])
        if consumer == "YUN":
            filename = next(iter(artifacts))
            artifacts[filename] += b"x"
        projections.append((consumer, artifacts))
    with pytest.raises(
        subject.SourceBindingActiveConsumerIntegrationV2Error,
        match="V1_ARTIFACT_BYTE_COUNT_MISMATCH",
    ):
        subject._verify_projection_digests(tuple(projections))


def test_public_verifier_binds_before_each_wrapper_and_calls_each_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def bind(_repo_root: Path) -> dict[str, bytes]:
        events.append("bind")
        return {}

    def projection(consumer: str):
        def wrapper(*, repo_root: Path) -> dict[str, bytes]:
            assert repo_root == ROOT
            events.append(consumer)
            return {}

        return wrapper

    monkeypatch.setattr(subject, "_bind_all_published_sources", bind)
    for consumer, wrapper_name in (
        ("YUN", "_project_yun_v2"),
        ("NEQ", "_project_neq_v2"),
        ("CHT", "_project_cht_v2"),
        ("OZJ", "_project_ozj_v2"),
        ("F24", "_project_f24_v2"),
        ("2A2", "_project_two_a2_v2"),
    ):
        monkeypatch.setattr(subject, wrapper_name, projection(consumer))

    def projection_digests(_projections):
        events.append("digests")
        return {}

    def census(_bound):
        events.append("census")
        return {
            "global_counts": {},
            "canonical_tasks": {},
            "human_review_counts": {},
            "training_runtime_counts": {},
            "geometry_counts": {},
        }

    monkeypatch.setattr(subject, "_verify_projection_digests", projection_digests)
    monkeypatch.setattr(subject, "_verify_current_census", census)
    subject.verify_covapie_source_binding_active_consumer_integration_v2(
        repo_root=ROOT
    )
    assert events == [
        "bind",
        "YUN",
        "NEQ",
        "CHT",
        "OZJ",
        "F24",
        "2A2",
        "digests",
        "census",
    ]


def test_source_binding_failure_stops_before_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def reject(_repo_root: Path) -> dict[str, bytes]:
        raise subject.SourceBindingActiveConsumerIntegrationV2Error("rejected")

    def projection(*, repo_root: Path) -> dict[str, bytes]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(subject, "_bind_all_published_sources", reject)
    monkeypatch.setattr(subject, "_project_yun_v2", projection)
    with pytest.raises(subject.SourceBindingActiveConsumerIntegrationV2Error):
        subject.verify_covapie_source_binding_active_consumer_integration_v2(
            repo_root=ROOT
        )
    assert called is False


def test_current_2a2_census_direct_evidence_and_exact_five_tasks() -> None:
    census = checker._verify_census(ROOT)
    assert census["global_counts"] == {
        "positive": 112,
        "relevant": 113,
        "INCLUDE": 44,
        "EXCLUDE_FROM_TRAINING_ONLY": 68,
        "future_training_admission_candidate": 27,
        "sample_level_pair_authority": 112,
        "sample_level_role_authority": 112,
    }
    assert census["task_counts"] == {0: 112, 1: 52, 2: 52, 3: 112, 4: 112}
    assert census["canonical_tasks"] == {
        "warhead_only": {
            "display_alias": "A",
            "structurally_applicable_authoritative_role_count": 112,
        },
        "linker_plus_warhead": {
            "display_alias": "B",
            "structurally_applicable_authoritative_role_count": 52,
        },
        "scaffold_plus_warhead": {
            "display_alias": "B2",
            "structurally_applicable_authoritative_role_count": 52,
        },
        "scaffold_only": {
            "display_alias": "B3",
            "structurally_applicable_authoritative_role_count": 112,
        },
        "scaffold_plus_linker_plus_warhead": {
            "display_alias": "C",
            "structurally_applicable_authoritative_role_count": 112,
        },
    }
    assert census["human_review_counts"] == {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_event_count": 119,
        "completed_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
    }
    assert census["training_runtime_counts"] == {
        "formal_training_admitted_count": 5,
        "current_runtime_model_usable_count": 17,
    }
    assert census["geometry_counts"] == {
        "POST_source_evidence_available_count": 867,
        "POST_sample_authoritative_count": 21,
        "POST_training_target_available_count": 17,
        "PRE_source_evidence_available_count": 0,
        "PRE_sample_authoritative_count": 0,
        "PRE_training_target_available_count": 0,
    }
    assert "pre_geometry_source_evidence_available" not in census["csv_header"]
    assert "pre_geometry_authoritative" in census["csv_header"]
    assert "pre_geometry_training_target_available" in census["csv_header"]
    assert (
        census["pre_source_evidence_semantics_distinct_from_sample_authority"]
        is True
    )
    assert {
        "geometry.PRE_source_evidence_available_count",
        "geometry.PRE_sample_authoritative_count",
        "geometry.PRE_training_target_available_count",
        "geometry.POST_to_PRE_promotion_performed",
        "geometry.PRE_zero_fill_performed",
        "geometry.PRE_is_v1_hard_requirement",
    }.issubset(census["summary_field_paths_verified"])


def test_authority_separation_and_non_training_boundary(
    verified_integration,
) -> None:
    result, _captured, inventories, census = verified_integration
    assert tuple(result) == checker.PUBLIC_RESULT_KEYS
    assert len(result) == 29
    assert result["schema_version"] == "covapie_source_binding_active_consumer_integration_v2"
    assert result["per_consumer_projection_digests"] == inventories
    assert result["current_global_counts"] == census["global_counts"]
    assert result["current_canonical_tasks"] == census["canonical_tasks"]
    assert result["current_human_review_counts"] == census["human_review_counts"]
    assert result["current_training_runtime_counts"] == census["training_runtime_counts"]
    assert result["current_geometry_counts"] == census["geometry_counts"]
    assert "PRE_source_evidence_available_count" in result["current_geometry_counts"]
    assert "PRE_source_authority_count" not in result["current_geometry_counts"]
    assert result["filesystem_source_acceptance_authority"] == "SOURCE_BINDING_POLICY_V2"
    assert result["sample_scientific_projection_authority"] == "PUBLISHED_V1_ARTIFACTS"
    assert result["current_global_state_authority"] == "PUBLISHED_2A2_V1_GLOBAL_CENSUS"
    assert result["global_canonical_task_count"] == 5
    assert result["B3_present"] is True
    assert result["sixth_task_present"] is False
    assert result["scientific_authority_reinterpreted"] is False
    assert result["global_census_refreshed"] is False
    assert result["reconciliation_executed"] is False
    assert result["training_admission_created"] is False
    assert result["data_materialized"] is False
    assert result["v2_migration_phase_b2_effective_state_integrated"] is True
    assert result["ready_for_training"] is False


@pytest.mark.parametrize(
    "drift",
    (
        "schema_version",
        "projection_digests",
        "pre_source_evidence_value",
        "pre_source_evidence_key",
        "central_integration_flag",
    ),
)
def test_checker_rejects_public_effective_state_result_drift(
    verified_integration,
    drift: str,
) -> None:
    result, _captured, inventories, census = verified_integration
    drifted = copy.deepcopy(result)
    if drift == "schema_version":
        drifted["schema_version"] = "wrong"
    elif drift == "projection_digests":
        artifact = next(iter(drifted["per_consumer_projection_digests"]["YUN"]))
        drifted["per_consumer_projection_digests"]["YUN"][artifact]["sha256"] = (
            "0" * 64
        )
    elif drift == "pre_source_evidence_value":
        drifted["current_geometry_counts"][
            "PRE_source_evidence_available_count"
        ] = 1
    elif drift == "pre_source_evidence_key":
        geometry = drifted["current_geometry_counts"]
        geometry["PRE_source_authority_count"] = geometry.pop(
            "PRE_source_evidence_available_count"
        )
    elif drift == "central_integration_flag":
        drifted["v2_migration_phase_b2_effective_state_integrated"] = False
    else:
        raise AssertionError(drift)
    with pytest.raises(ValueError, match="INTEGRATION_RESULT"):
        checker._verify_result(
            drifted,
            projections=inventories,
            census=census,
        )


def test_invalid_repo_root_type_fails_closed() -> None:
    with pytest.raises(
        subject.SourceBindingActiveConsumerIntegrationV2Error,
        match="REPO_ROOT_TYPE_INVALID",
    ):
        subject.verify_covapie_source_binding_active_consumer_integration_v2(
            repo_root=str(ROOT)  # type: ignore[arg-type]
        )


def test_lifecycle_fact_profiles_and_fail_closed_negatives() -> None:
    expected = set(checker.EXACT4_PATHS)
    candidate_status = tuple(f"?? {path}" for path in sorted(expected))
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=set(),
        ordinary_untracked=expected,
        status_entries=candidate_status,
        working_diff=set(),
        cached_diff=set(),
    ) == "CANDIDATE_UNTRACKED"
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=expected,
        ordinary_untracked=set(),
        status_entries=(),
        working_diff=set(),
        cached_diff=set(),
    ) == "TRACKED_CLEAN"
    bad_facts = (
        ({next(iter(expected))}, set(), (), set(), set()),
        (set(), expected | {"extra.txt"}, candidate_status, set(), set()),
        (set(), expected, candidate_status, {"tracked.py"}, set()),
        (set(), expected, candidate_status, set(), {next(iter(expected))}),
    )
    for tracked, untracked, status, working, cached in bad_facts:
        with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
            checker.classify_lifecycle_from_facts(
                tracked_exact4=tracked,
                ordinary_untracked=untracked,
                status_entries=status,
                working_diff=working,
                cached_diff=cached,
            )


def test_only_two_repository_relations_are_accepted() -> None:
    checker.validate_repository_relation_from_facts(
        profile="CANDIDATE_UNTRACKED",
        head=checker.BASELINE_HEAD,
        origin_main=checker.BASELINE_HEAD,
        ahead=0,
        behind=0,
        parent_shas=(),
        changed_paths=set(),
    )
    child = "f" * 40
    checker.validate_repository_relation_from_facts(
        profile="TRACKED_CLEAN",
        head=child,
        origin_main=checker.BASELINE_HEAD,
        ahead=1,
        behind=0,
        parent_shas=(checker.BASELINE_HEAD,),
        changed_paths=set(checker.EXACT4_PATHS),
    )
    checker.validate_repository_relation_from_facts(
        profile="TRACKED_CLEAN",
        head=child,
        origin_main=child,
        ahead=0,
        behind=0,
        parent_shas=(checker.BASELINE_HEAD,),
        changed_paths=set(checker.EXACT4_PATHS),
    )
    with pytest.raises(ValueError, match="TRACKED_CLEAN_REPOSITORY_RELATION_INVALID"):
        checker.validate_repository_relation_from_facts(
            profile="TRACKED_CLEAN",
            head=child,
            origin_main=checker.BASELINE_HEAD,
            ahead=2,
            behind=0,
            parent_shas=(checker.BASELINE_HEAD,),
            changed_paths=set(checker.EXACT4_PATHS),
        )
