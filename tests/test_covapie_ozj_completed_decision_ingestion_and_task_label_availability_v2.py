from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
import shutil

import pytest

from covalent_ext import (
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
    as ozj_v1,
)
from covalent_ext import (
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
)
SPEC = importlib.util.spec_from_file_location("check_ozj_v2", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return subject.load_frozen_ozj_authority_v2(repo_root=ROOT)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.verify_published_ozj_v1_projection_v2(repo_root=ROOT)


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
    return subject.load_frozen_ozj_authority_v2(
        repo_root=ROOT,
        repository_path_overrides={binding[0]: replacement},
    )


def test_minimal_public_api() -> None:
    checker._verify_public_api()
    assert subject.__all__ == (
        "OZJSourceBindingV2Error",
        "load_frozen_ozj_authority_v2",
        "verify_published_ozj_v1_projection_v2",
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
    assert not any(path.endswith((".json", ".csv")) for path in checker.EXACT4_PATHS)


def test_exact4_file_hygiene() -> None:
    rows = checker.verify_exact4_file_hygiene(ROOT)
    assert [row["path"] for row in rows] == list(checker.EXACT4_PATHS)
    assert all(row["mode"] in {"0644", "0664"} for row in rows)


def test_v1_owner_checker_and_tests_are_frozen() -> None:
    expected = (
        (ozj_v1.SOURCE_RELATIVE, 106888, subject.OZJ_V1_OWNER_SHA256),
        (ozj_v1.CHECKER_RELATIVE, 22027, subject.OZJ_V1_CHECKER_SHA256),
        (ozj_v1.TEST_RELATIVE, 26659, subject.OZJ_V1_TEST_SHA256),
    )
    for relative, byte_count, digest in expected:
        path = ROOT / relative
        assert path.stat().st_size == byte_count
        assert _sha(path) == digest


def test_v1_artifact_identities_are_frozen() -> None:
    for relative, byte_count, digest, _label in (
        subject._PUBLISHED_OZJ_V1_OUTPUT_BINDINGS
    ):
        path = ROOT / relative
        assert path.stat().st_size == byte_count
        assert _sha(path) == digest


def test_b1_helper_identity_is_frozen() -> None:
    path = ROOT / subject.SOURCE_BINDING_POLICY_V2_RELATIVE
    assert path.stat().st_size == 3704
    assert _sha(path) == subject.SOURCE_BINDING_POLICY_V2_SHA256
    assert checker._verify_bound_bindings(ROOT, (checker.B1_BINDING,))


def test_published_cht_v2_owner_and_checker_are_bound() -> None:
    assert (ROOT / subject.CHT_V2_RELATIVE).stat().st_size == 27636
    assert _sha(ROOT / subject.CHT_V2_RELATIVE) == subject.CHT_V2_SHA256
    assert (ROOT / subject.CHT_V2_CHECKER_RELATIVE).stat().st_size == 38205
    assert _sha(ROOT / subject.CHT_V2_CHECKER_RELATIVE) == subject.CHT_V2_CHECKER_SHA256


def test_published_yun_v2_owner_and_checker_are_bound() -> None:
    assert (ROOT / subject.YUN_V2_RELATIVE).stat().st_size == 21294
    assert _sha(ROOT / subject.YUN_V2_RELATIVE) == subject.YUN_V2_SHA256
    assert (ROOT / subject.YUN_V2_CHECKER_RELATIVE).stat().st_size == 28382
    assert _sha(ROOT / subject.YUN_V2_CHECKER_RELATIVE) == subject.YUN_V2_CHECKER_SHA256


def test_dual_v2_bindings_are_independently_verified() -> None:
    observed = checker._verify_bound_bindings(ROOT, checker.DUAL_V2_BINDINGS)
    assert observed[subject.CHT_V2_RELATIVE.as_posix()] == subject.CHT_V2_SHA256
    assert observed[subject.YUN_V2_RELATIVE.as_posix()] == subject.YUN_V2_SHA256


def test_cht_v2_projection_is_actually_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = subject.cht_v2.verify_published_cht_v1_projection_v2
    calls: list[Path] = []

    def recording_precedent(**kwargs: object) -> dict[str, bytes]:
        calls.append(kwargs["repo_root"])  # type: ignore[arg-type]
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        subject.cht_v2,
        "verify_published_cht_v1_projection_v2",
        recording_precedent,
    )
    subject.load_frozen_ozj_authority_v2(repo_root=ROOT)
    assert calls == [ROOT]


def test_yun_v2_projection_is_actually_called(
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
    subject.load_frozen_ozj_authority_v2(repo_root=ROOT)
    # Once transitively through CHT V2 -> NEQ V2 and once directly from OZJ V2.
    assert calls == [ROOT, ROOT]


def test_verify_bound_source_v2_is_actually_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = subject.verify_bound_source_v2
    calls: list[Path] = []

    def recording_helper(**kwargs: object) -> bytes:
        calls.append(kwargs["path"])  # type: ignore[arg-type]
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(subject, "verify_bound_source_v2", recording_helper)
    subject.load_frozen_ozj_authority_v2(repo_root=ROOT)
    assert len(calls) == 26


def test_old_ozj_v1_source_and_mutation_gates_are_inactive() -> None:
    result = checker._verify_production_ast(ROOT)
    checker._verify_ozj_v1_pure_call_graph(ROOT)
    assert result["ozj_v1_source_gate_active"] is False
    assert not checker._FORBIDDEN_OZJ_V1_CALLS.intersection(
        result["reused_ozj_v1_function_names"]
    )


def test_cht_and_yun_v1_active_loaders_are_inactive() -> None:
    result = checker._verify_production_ast(ROOT)
    assert result["cht_v1_source_gate_active"] is False
    assert result["yun_v1_source_gate_active"] is False
    checker._verify_predecessor_call_graph(
        ROOT,
        subject.CHT_V2_RELATIVE,
        "CHT",
        {"load_frozen_cht_authority_v2", "verify_published_cht_v1_projection_v2"},
        checker._FORBIDDEN_CHT_V1_CALLS,
    )
    checker._verify_predecessor_call_graph(
        ROOT,
        subject.YUN_V2_RELATIVE,
        "YUN",
        {"load_frozen_yun_authority_v2", "verify_published_yun_v1_projection_v2"},
        checker._FORBIDDEN_YUN_V1_CALLS,
    )


def test_no_materialization_or_mutation_api() -> None:
    production = (ROOT / checker.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(production)
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    assert public_functions == {
        "load_frozen_ozj_authority_v2",
        "verify_published_ozj_v1_projection_v2",
    }
    assert "materialize_artifacts_v1" not in production
    assert "build_artifacts_v1" not in production


def test_no_direct_read_or_exact_numeric_mode_gate() -> None:
    result = checker._verify_production_ast(ROOT)
    assert result["b1_bound_source_helper_used"] is True
    assert result["exact_posix_semantic_mode_active"] is False


def test_mode_is_used_only_to_derive_executable_class() -> None:
    assert subject._expected_executable_from_legacy_mode("0664") is False
    assert subject._expected_executable_from_legacy_mode("0755") is True
    with pytest.raises(subject.OZJSourceBindingV2Error, match="LEGACY_MODE"):
        subject._expected_executable_from_legacy_mode("invalid")


def test_historical_mode_inventory_is_exactly_0664_times_six(
    bound: dict[str, object],
) -> None:
    rows = bound["frozen_review_package_bindings"]
    assert [row["mode"] for row in rows] == ["0664"] * 6  # type: ignore[index]
    source_binding = bound["source_binding_v2"]
    assert source_binding["historical_review_modes"] == ["0664"] * 6  # type: ignore[index]
    assert source_binding["review_source_expected_executable_classes"] == [  # type: ignore[index]
        False
    ] * 6


def test_python_validator_is_explicitly_nonexecutable_class(
    bound: dict[str, object],
) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[-1]
    assert binding[0].suffix == ".py"
    assert binding[4] == "0664"
    assert subject._expected_executable_from_legacy_mode(binding[4]) is False
    assert bound["source_binding_v2"][  # type: ignore[index]
        "review_package_validator_expected_executable"
    ] is False


@pytest.mark.parametrize("binding_index", [0, -1], ids=["ordinary", "validator_py"])
@pytest.mark.parametrize("mode", [0o600, 0o644, 0o660, 0o664])
def test_nonexecutable_review_sources_safe_modes_pass(
    tmp_path: Path,
    binding_index: int,
    mode: int,
    bound: dict[str, object],
) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[binding_index]
    assert _load_with_mode(tmp_path, binding, mode) == bound


@pytest.mark.parametrize("binding_index", [0, -1], ids=["ordinary", "validator_py"])
@pytest.mark.parametrize("mode", [0o755, 0o775])
def test_nonexecutable_review_sources_executable_modes_fail(
    tmp_path: Path, binding_index: int, mode: int
) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[binding_index]
    with pytest.raises(
        subject.OZJSourceBindingV2Error,
        match="SOURCE_EXECUTABLE_CLASS_MISMATCH",
    ):
        _load_with_mode(tmp_path, binding, mode)


@pytest.mark.parametrize("binding_index", [0, -1], ids=["ordinary", "validator_py"])
@pytest.mark.parametrize("mode", [0o666, 0o777])
def test_nonexecutable_review_sources_world_writable_modes_fail(
    tmp_path: Path, binding_index: int, mode: int
) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[binding_index]
    with pytest.raises(
        subject.OZJSourceBindingV2Error,
        match="SOURCE_WORLD_WRITABLE",
    ):
        _load_with_mode(tmp_path, binding, mode)


def test_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    replacement = _temporary_binding(tmp_path, binding, 0o644)
    replacement.write_bytes(replacement.read_bytes() + b"\n")
    with pytest.raises(
        subject.OZJSourceBindingV2Error, match="SOURCE_BYTE_COUNT_MISMATCH"
    ):
        subject.load_frozen_ozj_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={binding[0]: replacement},
        )


def test_wrong_sha_same_size_fails_closed(tmp_path: Path) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    replacement = _temporary_binding(tmp_path, binding, 0o644)
    payload = bytearray(replacement.read_bytes())
    payload[0] ^= 1
    replacement.write_bytes(payload)
    replacement.chmod(0o644)
    assert len(payload) == binding[1]
    with pytest.raises(subject.OZJSourceBindingV2Error, match="SOURCE_SHA256_MISMATCH"):
        subject.load_frozen_ozj_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={binding[0]: replacement},
        )


def test_symlink_fails_closed(tmp_path: Path) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    target = _temporary_binding(tmp_path, binding, 0o644)
    link = tmp_path / "review-link.json"
    link.symlink_to(target.name)
    with pytest.raises(subject.OZJSourceBindingV2Error, match="SOURCE_SYMLINK_FORBIDDEN"):
        subject.load_frozen_ozj_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={binding[0]: link},
        )


def test_unexpected_override_fails_closed(tmp_path: Path) -> None:
    replacement = tmp_path / "unexpected.txt"
    replacement.write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(
        subject.OZJSourceBindingV2Error,
        match="REPOSITORY_PATH_OVERRIDE_UNEXPECTED",
    ):
        subject.load_frozen_ozj_authority_v2(
            repo_root=ROOT,
            repository_path_overrides={Path("unexpected.txt"): replacement},
        )


def test_formal_path_and_override_ambiguity_fails_closed(tmp_path: Path) -> None:
    formal_relative = ozj_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    with pytest.raises(subject.OZJSourceBindingV2Error, match="AMBIGUOUS"):
        subject.load_frozen_ozj_authority_v2(
            repo_root=ROOT,
            formal_decision_path=tmp_path / "formal.json",
            repository_path_overrides={formal_relative: tmp_path / "other.json"},
        )


def test_exact4_event_ids_ranks_and_structure_identity(
    bound: dict[str, object],
) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert len(events) == 4
    assert tuple(event["canonical_event_id"] for event in events) == ozj_v1.EXPECTED_EVENT_IDS
    assert [event["scaleup_rank"] for event in events] == list(ozj_v1.EXPECTED_RANKS)
    assert {event["pdb_id"] for event in events} == {"4CL8"}
    assert {event["cys_residue_id"] for event in events} == {"CYS:168-"}


def test_d1_through_d6_are_exact(bound: dict[str, object]) -> None:
    approval = bound["formal"]["human_approval"]  # type: ignore[index]
    assert approval["D1_task_relevance"] == "RELEVANT"
    assert approval["D2_chemistry"] == "POSITIVE"
    assert approval["D3_reactive_pair"] == "CONFIRM_OBSERVED_PAIR"
    assert approval["D4_role_partition"] == "SELECT_CANDIDATE_1"
    assert approval["D5_training_use"] == "INCLUDE"
    assert approval["D6_scientific_context"] == ozj_v1.EXPECTED_D6
    assert "target-directed, structure-based-designed TbPTR1" in ozj_v1.EXPECTED_D6
    assert "native Cys168" in ozj_v1.EXPECTED_D6
    assert "medicinal antiparasitic covalent-inhibitor context" in ozj_v1.EXPECTED_D6


def test_positive_nonnegative_chemistry_semantics(bound: dict[str, object]) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    assert all(event["task_relevant"] is True for event in events)
    assert all(event["chemistry_known_positive"] is True for event in events)
    assert all(event["negative_chemistry"] is False for event in events)
    assert all(event["task_domain_negative"] is False for event in events)


def test_reactive_pair_and_strict_role_partition_are_exact(
    bound: dict[str, object],
) -> None:
    events = bound["normalized"]["events"]  # type: ignore[index]
    role = bound["normalized"]["role"]  # type: ignore[index]
    assert {(event["protein_reactive_atom"], event["ligand_reactive_atom"]) for event in events} == {("SG", "CAF")}
    assert role["selected_candidate_index_0based"] == 1
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["exact_heavy_atom_ids"] == list(ozj_v1.EXPECTED_HEAVY_ATOMS)
    assert role["warhead_atoms"] == ["CAF", "OAD"]
    assert role["linker_atoms"] == ["CAG", "CAH", "CAI", "CAJ", "CAP", "CAQ"]
    assert role["scaffold_atoms"] == list(ozj_v1.EXPECTED_SCAFFOLD)


@pytest.mark.parametrize(
    ("task_id", "semantic", "alias"),
    [
        (0, "warhead_only", "A"),
        (1, "linker_plus_warhead", "B"),
        (2, "scaffold_plus_warhead", "B2"),
        (3, "scaffold_only", "B3"),
        (4, "scaffold_plus_linker_plus_warhead", "C"),
    ],
)
def test_each_canonical_exact5_task_is_applicable(
    task_id: int, semantic: str, alias: str
) -> None:
    tasks = ozj_v1._canonical_task_contract()
    item = tasks["strict_profile_task_applicability"][task_id]
    assert item == {
        "task_id": task_id,
        "semantic_long_name": semantic,
        "display_alias": alias,
        "structurally_applicable": True,
        "role_profile": "STRICT_LINKER_PRESENT_V1",
    }


def test_canonical_exact5_inventory_has_b3_and_no_sixth_task() -> None:
    tasks = ozj_v1._canonical_task_contract()
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["strict_profile_applicable_task_count"] == 5
    assert tasks["strict_profile_applicable_task_ids"] == [0, 1, 2, 3, 4]
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_created"] is False


def test_include_future_candidate_is_not_training_admission(
    bound: dict[str, object],
) -> None:
    training = bound["normalized"]["training_boundary"]  # type: ignore[index]
    assert training["formal_event_training_use_decision"] == "INCLUDE"
    assert training["human_training_excluded"] is False
    assert training["training_use_allowed"] is True
    assert training["training_use_include"] is True
    assert training["candidate_for_future_training_admission"] is True
    assert training["future_training_candidate_derived_by_ingestion"] is True
    assert training["future_training_candidate_is_training_admission"] is False
    assert training["training_admitted"] is False
    assert training["training_admission_created"] is False


def test_training_materialization_runtime_and_readiness_remain_false(
    bound: dict[str, object],
) -> None:
    training = bound["normalized"]["training_boundary"]  # type: ignore[index]
    assert training["training_materialization_allowed_now"] is False
    assert training["current_runtime_model_usable"] is False
    assert training["parameter_update_authorization"] is False
    assert training["ready_for_training"] is False


def test_post_source_evidence_boundary_is_preserved(bound: dict[str, object]) -> None:
    topology = bound["normalized"][  # type: ignore[index]
        "source_ccd_and_event_topology_boundary"
    ]
    geometry = bound["normalized"]["geometry_boundary"]  # type: ignore[index]
    assert geometry["POST_source_evidence_count"] == 4
    assert topology["explicit_observed_SG_CAF_connection_available"] is True
    assert topology["explicit_observed_SG_CAF_connection_event_count"] == 4
    assert topology["source_CAF_OAD_bond_order"] == "DOUB"
    assert topology["complete_POST_topology_authority_available"] is False
    assert geometry["POST_geometry_training_authority_count"] == 0


def test_pre_and_reconstruction_boundaries_are_preserved(
    bound: dict[str, object],
) -> None:
    topology = bound["normalized"][  # type: ignore[index]
        "source_ccd_and_event_topology_boundary"
    ]
    geometry = bound["normalized"]["geometry_boundary"]  # type: ignore[index]
    assert topology["PRE_topology_authority_available"] is False
    assert topology["PRE_geometry_authority_available"] is False
    assert geometry["PRE_precursor_topology_authority_count"] == 0
    assert geometry["PRE_reconstruction_count"] == 0
    assert topology["POST_bond_order_reconstruction_performed"] is False
    assert geometry["POST_to_PRE_copy_performed"] is False
    assert geometry["PRE_zero_fill_performed"] is False


def test_dual_predecessor_record_is_exact(bound: dict[str, object]) -> None:
    dual = bound["dual_published_v2_predecessors"]
    assert dual["published_CHT_V2_successor_bound"] is True  # type: ignore[index]
    assert dual["CHT_V2_sha256"] == subject.CHT_V2_SHA256  # type: ignore[index]
    assert dual["CHT_V2_published_commit"] == subject.CHT_V2_PUBLISHED_COMMIT  # type: ignore[index]
    assert dual["CHT_V2_projection_actually_called"] is True  # type: ignore[index]
    assert dual["CHT_V1_scientific_matrix_preserved"] is True  # type: ignore[index]
    assert dual["published_YUN_V2_successor_bound"] is True  # type: ignore[index]
    assert dual["YUN_V2_sha256"] == subject.YUN_V2_SHA256  # type: ignore[index]
    assert dual["YUN_V2_published_commit"] == subject.YUN_V2_PUBLISHED_COMMIT  # type: ignore[index]
    assert dual["YUN_V2_projection_actually_called"] is True  # type: ignore[index]
    assert dual["YUN_V1_INCLUDE_projection_preserved"] is True  # type: ignore[index]


def test_v1_snapshot_matrix_summary_and_manifest_are_preserved(
    artifacts: dict[str, bytes],
) -> None:
    assert tuple(artifacts) == ozj_v1.OUTPUT_FILENAMES
    expected = {
        relative.name: (byte_count, digest)
        for relative, byte_count, digest, _label in (
            subject._PUBLISHED_OZJ_V1_OUTPUT_BINDINGS
        )
    }
    for name, payload in artifacts.items():
        assert (len(payload), hashlib.sha256(payload).hexdigest()) == expected[name]


def test_v1_safe_mode_false_failure_and_v2_pass_contrast(tmp_path: Path) -> None:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    replacement = _temporary_binding(tmp_path, binding, 0o644)
    with pytest.raises(ozj_v1.OZJIngestionSafetyError, match="BOUND_SOURCE_MODE_MISMATCH"):
        ozj_v1._verify_payload(
            replacement,
            binding[1],
            binding[2],
            binding[3],
            binding[4],
        )
    observed = subject.load_frozen_ozj_authority_v2(
        repo_root=ROOT,
        repository_path_overrides={binding[0]: replacement},
    )
    assert observed["source_binding_v2"][  # type: ignore[index]
        "exact_posix_numeric_mode_semantic_acceptance"
    ] is False


def test_current_global_census_is_unchanged() -> None:
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


def test_candidate_lifecycle_facts_are_accepted() -> None:
    exact = set(checker.EXACT4_PATHS)
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=set(),
        ordinary_untracked=exact,
        status_entries=tuple(f"?? {path}" for path in sorted(exact)),
        working_diff=set(),
        cached_diff=set(),
    ) == "CANDIDATE_UNTRACKED"


def test_tracked_clean_lifecycle_facts_are_accepted() -> None:
    exact = set(checker.EXACT4_PATHS)
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=exact,
        ordinary_untracked=set(),
        status_entries=(),
        working_diff=set(),
        cached_diff=set(),
    ) == "TRACKED_CLEAN"


@pytest.mark.parametrize(
    ("tracked", "untracked", "status", "working", "cached"),
    [
        (set(), set(checker.EXACT4_PATHS[:-1]), (), set(), set()),
        (set(), set(checker.EXACT4_PATHS) | {"extra.txt"}, (), set(), set()),
        ({checker.PRODUCTION_RELATIVE}, set(), (), set(), set()),
        (set(checker.EXACT4_PATHS), set(), (" M extra.txt",), set(), set()),
        (set(checker.EXACT4_PATHS), set(), (), {"extra.txt"}, set()),
        (set(checker.EXACT4_PATHS), set(), (), set(), {"extra.txt"}),
    ],
)
def test_partial_dirty_staged_or_extra_lifecycle_facts_are_rejected(
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


def test_live_lifecycle_is_one_of_the_two_exact_profiles() -> None:
    assert checker.verify_git_lifecycle(ROOT) in {
        "CANDIDATE_UNTRACKED",
        "TRACKED_CLEAN",
    }


def test_independent_checker_covers_complete_contract() -> None:
    result = checker.run_check_v2(ROOT)
    assert result["lifecycle"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert result["ozj_v1_bytes_preserved"] is True
    assert result["ozj_v1_artifacts_preserved"] is True
    assert result["cht_v2_projection_exercised"] is True
    assert result["yun_v2_projection_exercised"] is True
    assert result["all_review_sources_expected_nonexecutable"] is True
    assert result["scientific_semantics_unchanged"] is True
    assert result["strict_exact5_all_tasks_applicable"] is True
    assert result["include_future_candidate_preserved"] is True
    assert result["current_census_unchanged"] is True
    assert result["ready_for_v2_b2_5"] is True
    assert result["ready_for_training"] is False
