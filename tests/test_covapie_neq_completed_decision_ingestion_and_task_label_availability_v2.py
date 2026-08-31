from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
import shutil

import pytest

from covalent_ext import (
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v1
    as neq_v1,
)
from covalent_ext import (
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py"
)
SPEC = importlib.util.spec_from_file_location("check_neq_v2", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return subject.load_frozen_neq_authority_v2(repo_root=ROOT)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.verify_published_neq_v1_projection_v2(repo_root=ROOT)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _temporary_binding(
    tmp_path: Path,
    binding: tuple[Path, int, str, str, str],
    mode: int,
) -> Path:
    path = tmp_path / binding[0].name
    shutil.copyfile(ROOT.parent / binding[0], path)
    path.chmod(mode)
    return path


def _load_with_mode(
    tmp_path: Path,
    binding: tuple[Path, int, str, str, str],
    mode: int,
) -> dict[str, object]:
    replacement = _temporary_binding(tmp_path, binding, mode)
    return subject.load_frozen_neq_authority_v2(
        repo_root=ROOT,
        repository_path_overrides={binding[0]: replacement},
    )


def test_minimal_public_api() -> None:
    checker._verify_public_api()
    assert subject.__all__ == (
        "NEQSourceBindingV2Error",
        "load_frozen_neq_authority_v2",
        "verify_published_neq_v1_projection_v2",
    )


def test_additive_successor_inventory_is_strict_exact4() -> None:
    assert checker.EXACT4_PATHS == (
        checker.PRODUCTION_RELATIVE,
        checker.CHECKER_RELATIVE,
        checker.TEST_RELATIVE,
        checker.GUIDE_RELATIVE,
    )
    assert len(set(checker.EXACT4_PATHS)) == 4
    assert all(path.endswith((".py", ".md")) for path in checker.EXACT4_PATHS)


def test_v1_owner_is_frozen_and_untouched() -> None:
    path = ROOT / neq_v1.SOURCE_RELATIVE
    assert path.stat().st_size == subject.NEQ_V1_OWNER_BYTE_COUNT == 96020
    assert _sha(path) == subject.NEQ_V1_OWNER_SHA256


def test_v1_checker_and_tests_are_frozen() -> None:
    assert (ROOT / neq_v1.CHECKER_RELATIVE).stat().st_size == 22964
    assert _sha(ROOT / neq_v1.CHECKER_RELATIVE) == subject.NEQ_V1_CHECKER_SHA256
    assert (ROOT / neq_v1.TEST_RELATIVE).stat().st_size == 27544
    assert _sha(ROOT / neq_v1.TEST_RELATIVE) == subject.NEQ_V1_TEST_SHA256


def test_b1_helper_identity_is_frozen() -> None:
    path = ROOT / subject.SOURCE_BINDING_POLICY_V2_RELATIVE
    assert path.stat().st_size == 3704
    assert _sha(path) == subject.SOURCE_BINDING_POLICY_V2_SHA256
    checker._verify_b1_dependency(ROOT)


def test_published_yun_v2_owner_and_checker_are_bound() -> None:
    assert (ROOT / subject.YUN_V2_RELATIVE).stat().st_size == 21294
    assert _sha(ROOT / subject.YUN_V2_RELATIVE) == subject.YUN_V2_SHA256
    assert (ROOT / subject.YUN_V2_CHECKER_RELATIVE).stat().st_size == 28382
    assert _sha(ROOT / subject.YUN_V2_CHECKER_RELATIVE) == subject.YUN_V2_CHECKER_SHA256
    checker._verify_yun_v2_dependency(ROOT)


def test_yun_v2_is_actually_used_as_precedent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = subject.yun_v2.verify_published_yun_v1_projection_v2
    calls: list[Path] = []

    def recording_precedent(**kwargs: object) -> dict[str, bytes]:
        calls.append(kwargs["repo_root"])  # type: ignore[arg-type]
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        subject.yun_v2,
        "verify_published_yun_v1_projection_v2",
        recording_precedent,
    )
    subject.load_frozen_neq_authority_v2(repo_root=ROOT)
    assert calls == [ROOT]


def test_verify_bound_source_v2_is_actually_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = subject.verify_bound_source_v2
    calls: list[Path] = []

    def recording_helper(**kwargs: object) -> bytes:
        calls.append(kwargs["path"])  # type: ignore[arg-type]
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "verify_bound_source_v2", recording_helper)
    subject.load_frozen_neq_authority_v2(repo_root=ROOT)
    assert len(calls) >= 24


def test_old_neq_v1_exact_mode_source_path_is_not_called() -> None:
    result = checker._verify_production_ast(ROOT)
    checker._verify_neq_v1_pure_call_graph(ROOT)
    assert result["neq_v1_active_source_gate_called"] is False
    assert "_verify_payload" not in result["reused_neq_v1_function_names"]


def test_old_yun_v1_source_gate_is_not_called() -> None:
    result = checker._verify_production_ast(ROOT)
    checker._verify_yun_v2_precedent_call_graph(ROOT)
    assert result["yun_v1_active_source_gate_called"] is False
    assert result["yun_v2_successor_called"] is True


def test_no_materialization_or_mutation_api() -> None:
    production = (ROOT / checker.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(production)
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    assert public_functions == {
        "load_frozen_neq_authority_v2",
        "verify_published_neq_v1_projection_v2",
    }
    assert "materialize_artifacts_v1" not in production


def test_no_direct_read_or_exact_numeric_mode_gate() -> None:
    result = checker._verify_production_ast(ROOT)
    assert result["b1_bound_source_helper_used"] is True
    assert result["exact_posix_semantic_mode_active"] is False


def test_mode_is_used_only_to_derive_executable_class() -> None:
    assert subject._expected_executable_from_legacy_mode("0644") is False
    assert subject._expected_executable_from_legacy_mode("0755") is True
    with pytest.raises(subject.NEQSourceBindingV2Error, match="LEGACY_MODE"):
        subject._expected_executable_from_legacy_mode("invalid")


@pytest.mark.parametrize("mode", [0o644, 0o664, 0o600, 0o660])
def test_nonexecutable_review_source_safe_modes_pass(
    tmp_path: Path, mode: int, bound: dict[str, object]
) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    assert _load_with_mode(tmp_path, binding, mode) == bound


def test_nonexecutable_review_source_world_writable_fails(tmp_path: Path) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    with pytest.raises(
        subject.NEQSourceBindingV2Error, match="SOURCE_WORLD_WRITABLE"
    ):
        _load_with_mode(tmp_path, binding, 0o666)


@pytest.mark.parametrize("mode", [0o755, 0o775, 0o750, 0o700])
def test_executable_validator_safe_executable_modes_pass(
    tmp_path: Path, mode: int, bound: dict[str, object]
) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[-1]
    assert _load_with_mode(tmp_path, binding, mode) == bound


def test_executable_validator_without_executable_class_fails(
    tmp_path: Path,
) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[-1]
    with pytest.raises(
        subject.NEQSourceBindingV2Error,
        match="SOURCE_EXECUTABLE_CLASS_MISMATCH",
    ):
        _load_with_mode(tmp_path, binding, 0o644)


def test_executable_validator_world_writable_fails(tmp_path: Path) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[-1]
    with pytest.raises(
        subject.NEQSourceBindingV2Error, match="SOURCE_WORLD_WRITABLE"
    ):
        _load_with_mode(tmp_path, binding, 0o777)


def test_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    replacement = _temporary_binding(tmp_path, binding, 0o644)
    replacement.write_bytes(replacement.read_bytes() + b"\n")
    with pytest.raises(
        subject.NEQSourceBindingV2Error, match="SOURCE_BYTE_COUNT_MISMATCH"
    ):
        subject.load_frozen_neq_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={binding[0]: replacement},
        )


def test_wrong_sha_same_size_fails_closed(tmp_path: Path) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    replacement = _temporary_binding(tmp_path, binding, 0o644)
    payload = bytearray(replacement.read_bytes())
    payload[0] ^= 1
    replacement.write_bytes(payload)
    replacement.chmod(0o644)
    assert len(payload) == binding[1]
    with pytest.raises(
        subject.NEQSourceBindingV2Error, match="SOURCE_SHA256_MISMATCH"
    ):
        subject.load_frozen_neq_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={binding[0]: replacement},
        )


def test_symlink_source_fails_closed(tmp_path: Path) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    target = _temporary_binding(tmp_path, binding, 0o644)
    link = tmp_path / "review-link"
    link.symlink_to(target.name)
    with pytest.raises(
        subject.NEQSourceBindingV2Error, match="SOURCE_SYMLINK_FORBIDDEN"
    ):
        subject.load_frozen_neq_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={binding[0]: link},
        )


def test_unexpected_override_path_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "unrelated"
    path.write_text("unrelated\n", encoding="utf-8")
    with pytest.raises(
        subject.NEQSourceBindingV2Error,
        match="REPOSITORY_PATH_OVERRIDE_UNEXPECTED",
    ):
        subject.load_frozen_neq_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={Path("unrelated.txt"): path},
        )


def test_formal_decision_exact6_event_ids(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert len(events) == 6
    assert tuple(event["canonical_event_id"] for event in events) == (
        neq_v1.EXPECTED_EVENT_IDS
    )


def test_formal_decision_exact6_ranks_and_pdb_sites(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert tuple(event["scaleup_rank"] for event in events) == neq_v1.EXPECTED_RANKS
    assert [event["pdb_id"] for event in events] == [
        "3V61",
        "3V61",
        "3V62",
        "3V62",
        "3V62",
        "3V62",
    ]


def test_site_distribution_remains_three_and_three(bound: dict[str, object]) -> None:
    inventory = bound["normalized"]["site_inventory"]  # type: ignore[index]
    assert inventory["CYS22_event_count"] == 3
    assert inventory["CYS81_event_count"] == 3


def test_D1_remains_relevant(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert {event["D1_task_relevance"] for event in events} == {"RELEVANT"}


def test_D2_remains_positive(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert {event["D2_chemistry_support"] for event in events} == {"POSITIVE"}
    assert {event["chemistry_known_positive"] for event in events} == {True}


def test_D3_remains_confirmed_sg_to_c3_pair(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert {event["D3_reactive_pair"] for event in events} == {
        "CONFIRM_OBSERVED_PAIR"
    }
    assert {
        (event["protein_reactive_atom"], event["ligand_reactive_atom"])
        for event in events
    } == {("SG", "C3")}


def test_D4_remains_candidate7(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert {event["D4_role_partition"] for event in events} == {
        "SELECT_CANDIDATE_7"
    }
    assert {event["selected_role_candidate_index_0based"] for event in events} == {7}


def test_D5_remains_exclude_without_negating_chemistry(
    bound: dict[str, object],
) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert {event["D5_training_use"] for event in events} == {
        "EXCLUDE_FROM_TRAINING_ONLY"
    }
    assert {event["negative_chemistry"] for event in events} == {False}


def test_D6_remains_exact(bound: dict[str, object]) -> None:
    context = bound["normalized"]["scientific_context"]  # type: ignore[index]
    assert context["D6_exact_choice"] == neq_v1.EXPECTED_D6


def test_direct_profile_remains_exact(bound: dict[str, object]) -> None:
    role = bound["normalized"]["role"]  # type: ignore[index]
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"


def test_role_partition_atoms_remain_exact(bound: dict[str, object]) -> None:
    role = bound["normalized"]["role"]  # type: ignore[index]
    assert role["warhead_atoms"] == ["C1", "C2", "C3", "C4", "N1", "O1", "O2"]
    assert role["linker_atoms"] == []
    assert role["linker_empty"] is True
    assert role["scaffold_atoms"] == ["C5", "C6"]


def test_canonical_exact5_has_b3_and_no_sixth_task() -> None:
    tasks = neq_v1._canonical_task_contract()
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["global_canonical_tasks"][3]["semantic_long_name"] == "scaffold_only"
    assert tasks["sixth_task_created"] is False


def test_direct_applicable_tasks_remain_0_3_4_despite_exclude() -> None:
    tasks = neq_v1._canonical_task_contract()
    assert tasks["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert tasks["D5_EXCLUDE_does_not_change_structural_applicability"] is True


def test_training_exclusion_boundary_remains_exact(bound: dict[str, object]) -> None:
    training = bound["normalized"]["training_boundary"]  # type: ignore[index]
    assert training["human_training_excluded"] is True
    assert training["training_use_allowed"] is False
    assert training["candidate_for_future_training_admission"] is False


def test_formal_admission_materialization_and_runtime_remain_false(
    bound: dict[str, object],
) -> None:
    training = bound["normalized"]["training_boundary"]  # type: ignore[index]
    assert training["training_admitted"] is False
    assert training["training_admission_created"] is False
    assert training["training_materialization_allowed_now"] is False
    assert training["current_runtime_model_usable"] is False


def test_pre_authority_and_reconstruction_remain_zero(
    bound: dict[str, object],
) -> None:
    geometry = bound["normalized"]["geometry_boundary"]  # type: ignore[index]
    assert geometry["PRE_geometry_authority_count"] == 0
    assert geometry["PRE_precursor_topology_authority_count"] == 0
    assert geometry["PRE_reconstruction_count"] == 0
    assert geometry["POST_to_PRE_copy_performed"] is False
    assert geometry["PRE_zero_fill_performed"] is False


def test_post_source_remains_evidence_not_training_authority(
    bound: dict[str, object],
) -> None:
    geometry = bound["normalized"]["geometry_boundary"]  # type: ignore[index]
    topology = bound["normalized"][  # type: ignore[index]
        "source_ccd_and_event_topology_boundary"
    ]
    assert geometry["POST_source_evidence_count"] == 6
    assert geometry["POST_geometry_training_authority_count"] == 0
    assert geometry["POST_geometry_training_target_count"] == 0
    assert topology["POST_bond_order_reconstruction_performed"] is False


def test_ready_for_training_remains_false(bound: dict[str, object]) -> None:
    training = bound["normalized"]["training_boundary"]  # type: ignore[index]
    assert training["ready_for_training"] is False


def test_legacy_mode_metadata_is_preserved(bound: dict[str, object]) -> None:
    rows = bound["frozen_review_package_bindings"]
    assert [row["mode"] for row in rows] == [  # type: ignore[index]
        "0644",
        "0644",
        "0644",
        "0644",
        "0644",
        "0755",
    ]
    assert bound["source_binding_v2"][  # type: ignore[index]
        "legacy_mode_metadata_classification"
    ] == [
        "LEGACY_PROVENANCE_METADATA_PRESERVED",
        "SECURITY_EXECUTABLE_CLASS_INPUT",
    ]


@pytest.mark.parametrize(
    ("name", "expected_sha"),
    [
        (neq_v1.SNAPSHOT, subject._PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[0][2]),
        (neq_v1.MATRIX, subject._PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[1][2]),
        (neq_v1.SUMMARY, subject._PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[2][2]),
        (neq_v1.MANIFEST, subject._PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[3][2]),
    ],
)
def test_published_v1_artifact_is_unchanged(
    name: str, expected_sha: str, artifacts: dict[str, bytes]
) -> None:
    assert hashlib.sha256(artifacts[name]).hexdigest() == expected_sha


def test_published_v1_projection_exact4_order(
    artifacts: dict[str, bytes],
) -> None:
    assert tuple(artifacts) == neq_v1.OUTPUT_FILENAMES


def test_published_yun_v2_predecessor_and_v1_matrix_are_preserved(
    bound: dict[str, object],
) -> None:
    precedent = bound["upstream_v2_migration_precedent"]
    assert precedent["published_YUN_V2_successor_bound"] is True  # type: ignore[index]
    assert precedent["YUN_V2_sha256"] == subject.YUN_V2_SHA256  # type: ignore[index]
    assert precedent["YUN_V2_source_binding_acceptance_active"] is True  # type: ignore[index]
    assert precedent["YUN_V1_scientific_matrix_preserved"] is True  # type: ignore[index]


def test_current_2a2_global_census_is_unchanged() -> None:
    assert checker._verify_current_2a2_census(ROOT) == {
        "positive": 112,
        "relevant": 113,
        "include": 44,
        "exclude": 68,
        "future": 27,
        "pair": 112,
        "role": 112,
        "A": 112,
        "B": 52,
        "B2": 52,
        "B3": 112,
        "C": 112,
    }


def test_v1_exact_mode_false_failure_static_contrast_is_proven() -> None:
    assert checker._verify_v1_static_false_failure_contract(ROOT) is True


def test_v2_mode_only_drift_preserves_authority(
    tmp_path: Path, bound: dict[str, object]
) -> None:
    binding = neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    assert _load_with_mode(tmp_path, binding, 0o664) == bound


def test_candidate_and_tracked_clean_are_only_success_lifecycle_profiles() -> None:
    expected = set(checker.EXACT4_PATHS)
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=set(),
        ordinary_untracked=expected,
        status_entries=tuple(f"?? {path}" for path in sorted(expected)),
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


def test_published_baseline_tree_and_subject_are_bound() -> None:
    assert checker._git(
        "show", "-s", "--format=%T%n%s", checker.BASELINE_HEAD, root=ROOT
    ).splitlines() == [checker.BASELINE_TREE, checker.BASELINE_SUBJECT]


def test_committed_and_published_tracked_clean_relations_pass() -> None:
    changed = set(checker.EXACT4_PATHS)
    checker._validate_repository_relation_v2(
        profile="TRACKED_CLEAN",
        head="a" * 40,
        origin_main=checker.BASELINE_HEAD,
        ahead=1,
        behind=0,
        parent_shas=(checker.BASELINE_HEAD,),
        changed_paths=changed,
    )
    checker._validate_repository_relation_v2(
        profile="TRACKED_CLEAN",
        head="a" * 40,
        origin_main="a" * 40,
        ahead=0,
        behind=0,
        parent_shas=(checker.BASELINE_HEAD,),
        changed_paths=changed,
    )


@pytest.mark.parametrize(
    ("tracked", "untracked", "status", "working", "cached"),
    [
        (set(), set(checker.EXACT4_PATHS[1:]), (), set(), set()),
        (set(), set(checker.EXACT4_PATHS) | {"extra.txt"}, (), set(), set()),
        (
            set(),
            set(checker.EXACT4_PATHS),
            (" M existing.py",),
            {"existing.py"},
            set(),
        ),
        (
            set(),
            set(checker.EXACT4_PATHS),
            ("A  staged.py",),
            set(),
            {"staged.py"},
        ),
        ({checker.EXACT4_PATHS[0]}, set(checker.EXACT4_PATHS[1:]), (), set(), set()),
    ],
)
def test_partial_extra_dirty_staged_and_mixed_lifecycle_fail_closed(
    tracked: set[str],
    untracked: set[str],
    status: tuple[str, ...],
    working: set[str],
    cached: set[str],
) -> None:
    with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
        checker.classify_lifecycle_from_facts(
            tracked_exact4=tracked,
            ordinary_untracked=untracked,
            status_entries=status,
            working_diff=working,
            cached_diff=cached,
        )


def test_wrong_tracked_clean_changed_paths_fail_closed() -> None:
    with pytest.raises(ValueError, match="TRACKED_CLEAN_COMMIT_IDENTITY_INVALID"):
        checker._validate_repository_relation_v2(
            profile="TRACKED_CLEAN",
            head="a" * 40,
            origin_main=checker.BASELINE_HEAD,
            ahead=1,
            behind=0,
            parent_shas=(checker.BASELINE_HEAD,),
            changed_paths=set(checker.EXACT4_PATHS[1:]),
        )


def test_actual_candidate_lifecycle_and_file_hygiene() -> None:
    assert checker.verify_git_lifecycle(ROOT) in {
        "CANDIDATE_UNTRACKED",
        "TRACKED_CLEAN",
    }
    rows = checker.verify_exact4_file_hygiene(ROOT)
    assert [row["path"] for row in rows] == list(checker.EXACT4_PATHS)
    assert all(row["mode"] in {"0644", "0664"} for row in rows)


def test_independent_checker_passes_candidate() -> None:
    result = checker.run_check_v2(ROOT)
    assert result["lifecycle"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert result["neq_v1_bytes_preserved"] is True
    assert result["neq_v1_artifacts_preserved"] is True
    assert result["b1_bound_source_helper_used"] is True
    assert result["yun_v2_successor_bound"] is True
    assert result["neq_v1_source_gate_active"] is False
    assert result["yun_v1_source_gate_active"] is False
    assert result["exact_posix_semantic_mode_active"] is False
    assert result["ready_for_v2_b2_3"] is True
    assert result["ready_for_training"] is False
