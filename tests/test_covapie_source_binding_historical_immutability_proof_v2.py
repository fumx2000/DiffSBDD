from __future__ import annotations

import hashlib
import importlib.util
import inspect
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_source_binding_historical_immutability_proof_v2 as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT / "scripts/check_covapie_source_binding_historical_immutability_proof_v2.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_source_binding_historical_immutability_proof_v2",
    CHECKER_PATH,
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


EXACT32 = (
    "docs/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_source_binding_active_consumer_integration_v2_guide.md",
    "docs/covapie_source_binding_policy_v2_guide.md",
    "docs/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_source_binding_active_consumer_integration_v2.py",
    "scripts/check_covapie_source_binding_policy_v2.py",
    "scripts/check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_source_binding_active_consumer_integration_v2.py",
    "src/covalent_ext/covapie_source_binding_policy_v2.py",
    "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_source_binding_active_consumer_integration_v2.py",
    "tests/test_covapie_source_binding_policy_v2.py",
    "tests/test_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
)


@pytest.fixture(scope="session")
def checked() -> dict[str, object]:
    return checker.run_check_v2(ROOT)


def test_strict_exact4_inventory_lifecycle_and_hygiene(
    checked: dict[str, object],
) -> None:
    assert checker.EXACT4_PATHS == (
        "src/covalent_ext/covapie_source_binding_historical_immutability_proof_v2.py",
        "scripts/check_covapie_source_binding_historical_immutability_proof_v2.py",
        "tests/test_covapie_source_binding_historical_immutability_proof_v2.py",
        "docs/covapie_source_binding_historical_immutability_proof_v2_guide.md",
    )
    assert checked["lifecycle"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert set(checked["exact4"]) == set(checker.EXACT4_PATHS)


def test_exact_public_api_and_no_mutation_api() -> None:
    assert subject.__all__ == (
        "SourceBindingHistoricalImmutabilityProofV2Error",
        "verify_covapie_source_binding_historical_immutability_proof_v2",
    )
    signature = inspect.signature(
        subject.verify_covapie_source_binding_historical_immutability_proof_v2
    )
    parameters = tuple(signature.parameters.values())
    assert len(parameters) == 1
    assert parameters[0].name == "repo_root"
    assert parameters[0].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters[0].annotation == "Path"
    assert signature.return_annotation == "dict[str, object]"
    assert all(
        token not in name.lower()
        for name in subject.__all__
        for token in (
            "override",
            "write",
            "materialize",
            "registry",
            "cache",
            "reconcile",
            "refresh",
        )
    )
    checker._verify_public_api_and_ast(ROOT)


def test_exact_frozen_commit_chain_and_exact32_literals(
    checked: dict[str, object],
) -> None:
    assert subject._MIGRATION_EXACT32_PATHS == EXACT32
    assert checker.MIGRATION_EXACT32_PATHS == EXACT32
    assert tuple(commit for commit, _subject in checker.MIGRATION_COMMITS) == (
        "94a59fef2922b8a450fe06538111ca62a0b78190",
        "5a34e260e57598ab62905f0171e43a67acc188e2",
        "baab1358bcc8f776df20d8dc76ed476d51ba27f3",
        "9e7d520de0baa5e5f107985f45b97f576bbd8fc0",
        "33d08ee6069592f0fe28ca53bed5615f578d10fc",
        "a81be8b1260d14b385b0faf05e2ddcc56bd403d8",
        "1e77d93929e491e589060269416b34fe47c0fb15",
        "049d446e0fa854fab9986a9e2fb302d0b9547231",
    )
    assert checked["migration_commit_count"] == 8
    assert checked["exact_chain"] is True
    assert checked["single_parent_linear"] is True
    assert checked["migration_added_path_count"] == 32
    assert checked["migration_modified_path_count"] == 0
    assert checked["migration_deleted_path_count"] == 0
    assert checked["migration_renamed_path_count"] == 0
    assert checked["exact32"] is True


def test_phase_a_frozen_provenance_and_all_1755_sources(
    checked: dict[str, object],
) -> None:
    assert checked["phase_a_scanned_source_binding_count"] == 1755
    assert checked["repository_scanned_source_binding_count"] == 1727
    assert checked["external_covapie_state_scanned_source_binding_count"] == 28
    assert checked["all_phase_a_scanned_source_bytes_unchanged"] is True
    assert checked["all_repository_scanned_source_bytes_unchanged"] is True
    assert checked["all_external_covapie_state_scanned_source_bytes_unchanged"] is True
    assert checked["phase_a_audit_artifacts_unchanged"] is True


def test_historical_inventory_counts_and_source_coverage(
    checked: dict[str, object],
) -> None:
    assert checked["historical_immutable_occurrence_count"] == 261
    assert checked["preserve_historical_do_not_propagate_occurrence_count"] == 180
    assert checked["phase_a_v2_migration_required_occurrence_count"] == 12
    assert checked["ambiguous_review_required_occurrence_count"] == 0
    assert checked["historical_occurrence_source_unmapped_count"] == 0
    assert checked["preserve_historical_source_unmapped_count"] == 0
    assert checked["all_historical_immutable_occurrence_sources_unchanged"] is True


def test_exact8_and_exact3_protected_historical_bytes(
    checked: dict[str, object],
) -> None:
    assert checker.ACTIVE_V1_TARGETS == (
        "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
        "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
        "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
        "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py",
        "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
        "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
        "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py",
        "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
    )
    assert checked["active_v1_migration_target_file_count"] == 8
    assert checked["known_regression_reference_count"] == 3
    assert checked["all_active_v1_migration_target_bytes_unchanged"] is True
    assert checked["known_regression_reference_bytes_unchanged"] is True
    assert checked["historical_exact_mode_metadata_preserved"] is True
    assert checked["historical_exact_mode_metadata_rewritten"] is False
    assert checked["historical_validator_rewrite_performed"] is False


@pytest.mark.parametrize("safe_mode", (0o644, 0o664))
def test_historical_0600_byte_binding_accepts_safe_mode_drift(
    tmp_path: Path,
    safe_mode: int,
) -> None:
    _role, relative, byte_count, sha256, historical_mode = (
        checker.KNOWN_REGRESSION_SPECS[2]
    )
    assert historical_mode == "0600"
    payload = (ROOT / relative).read_bytes()
    copy = tmp_path / "historical_1f8.csv"
    copy.write_bytes(payload)
    copy.chmod(safe_mode)
    assert subject._verify_bound_bytes(
        path=copy,
        expected_byte_count=byte_count,
        expected_sha256=sha256,
        label="SAFE_MODE_DRIFT_NEGATIVE_CONTROL",
        expected_executable=None,
    ) == payload


def test_world_writable_historical_copy_is_rejected(tmp_path: Path) -> None:
    _role, relative, byte_count, sha256, _historical_mode = (
        checker.KNOWN_REGRESSION_SPECS[2]
    )
    copy = tmp_path / "unsafe_historical_1f8.csv"
    copy.write_bytes((ROOT / relative).read_bytes())
    copy.chmod(0o666)
    with pytest.raises(
        subject.SourceBindingHistoricalImmutabilityProofV2Error,
        match="BOUND_SOURCE_REJECTED",
    ):
        subject._verify_bound_bytes(
            path=copy,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label="WORLD_WRITABLE_NEGATIVE_CONTROL",
            expected_executable=None,
        )


def test_byte_drift_is_rejected_even_at_safe_mode(tmp_path: Path) -> None:
    _role, relative, byte_count, sha256, _historical_mode = (
        checker.KNOWN_REGRESSION_SPECS[2]
    )
    payload = (ROOT / relative).read_bytes()
    copy = tmp_path / "drifted_historical_1f8.csv"
    copy.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    copy.chmod(0o644)
    assert len(copy.read_bytes()) == byte_count
    assert hashlib.sha256(copy.read_bytes()).hexdigest() != sha256
    with pytest.raises(
        subject.SourceBindingHistoricalImmutabilityProofV2Error,
        match="BOUND_SOURCE_REJECTED",
    ):
        subject._verify_bound_bytes(
            path=copy,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label="BYTE_DRIFT_NEGATIVE_CONTROL",
            expected_executable=None,
        )


def test_path_escape_and_unexpected_namespace_fail_closed() -> None:
    with pytest.raises(
        subject.SourceBindingHistoricalImmutabilityProofV2Error,
        match="FROZEN_SOURCE_PATH_ESCAPE",
    ):
        subject._resolve_frozen_path(
            ROOT,
            path_namespace="repository_relative",
            relative_path="../escape.py",
        )
    with pytest.raises(
        subject.SourceBindingHistoricalImmutabilityProofV2Error,
        match="FROZEN_SOURCE_NAMESPACE_INVALID",
    ):
        subject._resolve_frozen_path(
            ROOT,
            path_namespace="project_parent_relative",
            relative_path="DiffSBDD-base/file.py",
        )
    with pytest.raises(
        subject.SourceBindingHistoricalImmutabilityProofV2Error,
        match="FROZEN_SOURCE_ROOT_ESCAPE",
    ):
        subject._resolve_frozen_path(
            ROOT,
            path_namespace="repository_parent_relative",
            relative_path="unexpected-external/file.py",
        )


def test_b1_dependencies_bound_and_published_b2_actually_called(
    checked: dict[str, object],
) -> None:
    assert checked["b2_integration_call_count"] == 1
    assert checked["b2_integration_verified"] is True
    assert checked["active_consumer_count"] == 6
    assert checked["artifact_projection_count"] == 24
    assert checked["all_V1_scientific_projections_preserved"] is True
    assert checked["current_2A2_census_unchanged"] is True
    assert checked["global_canonical_task_count"] == 5
    assert checked["B3_present"] is True
    assert checked["sixth_task_present"] is False


def test_authority_and_readiness_boundary(checked: dict[str, object]) -> None:
    assert checked["v2_migration_phase_b3_historical_immutability_proven"] is True
    assert checked["ready_for_v2_migration_phase_b4_future_guard"] is True
    assert checked["ready_for_training"] is False


def test_lifecycle_fact_profiles_and_partial_dirty_extra_rejected() -> None:
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


def test_only_candidate_and_tracked_clean_repository_relations_are_accepted() -> None:
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


def test_invalid_repo_root_type_fails_closed() -> None:
    with pytest.raises(
        subject.SourceBindingHistoricalImmutabilityProofV2Error,
        match="REPO_ROOT_TYPE_INVALID",
    ):
        subject.verify_covapie_source_binding_historical_immutability_proof_v2(
            repo_root=str(ROOT)  # type: ignore[arg-type]
        )
