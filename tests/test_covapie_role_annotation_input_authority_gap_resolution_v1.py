from __future__ import annotations

import copy
import importlib
import inspect
import json
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from covalent_ext import (  # noqa: E402
    covapie_role_annotation_input_authority_gap_resolution_v1 as subject,
)
import check_covapie_role_annotation_input_authority_gap_resolution_v1 as checker_subject  # noqa: E402


def _evaluate() -> dict[str, object]:
    return subject.evaluate_covapie_role_annotation_input_authority_gap_resolution_v1(
        repo_root=REPO_ROOT
    )


def _expected_lifecycle_from_valid_response(
    response: Mapping[str, object],
) -> dict[str, object]:
    witness = subject._response_lifecycle_projection_v1(response)
    subject._validate_response_lifecycle_v1(witness)
    return witness


def _different_sha(current: object) -> str:
    candidate = "a" * 40
    if current == candidate:
        candidate = "b" * 40
    return candidate


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, check=False,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return result.stdout


def test_public_api_is_keyword_only_and_authority_semantics_pass() -> None:
    with pytest.raises(TypeError):
        subject.evaluate_covapie_role_annotation_input_authority_gap_resolution_v1(REPO_ROOT)
    response = _evaluate()
    assert response["authority_gap_resolution_completed"] is False
    assert response["unresolved_dimensions"] == (
        "reaction_family_label", "approved_warhead_rule",
    )
    assert all(
        row["retained_heavy_atom_mapping_status"] == "authoritative_resolved"
        and row["ligand_reactive_atom_status"] == "authoritative_resolved"
        and row["residue_reactive_atom_status"] == "authoritative_resolved"
        and row["pre_reaction_connectivity_status"] == "authoritative_resolved"
        and row["pre_reaction_bond_order_status"] == "authoritative_resolved"
        and row["reaction_family_status"] == "candidate_only"
        and row["approved_warhead_rule_status"] == "candidate_only"
        for row in response["current11_authority_matrix"]
    )


def _assert_formal_commit_identity(authority_commit: str) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", authority_commit)
    assert _git("show", "-s", "--format=%s", authority_commit).strip() == subject._FORMAL_COMMIT_SUBJECT
    assert _git("show", "-s", "--format=%P", authority_commit).split() == [subject._BASE]
    changed_lines = _git(
        "diff-tree", "--root", "--no-commit-id", "--name-status", "-r",
        authority_commit,
    ).splitlines()
    changed = {parts[1]: parts[0] for parts in (line.split("\t") for line in changed_lines)}
    assert tuple(sorted(changed)) == subject._CANDIDATE_PATHS
    assert changed == {path: "A" for path in subject._CANDIDATE_PATHS}
    for path in subject._CANDIDATE_PATHS:
        tree_line = _git("ls-tree", authority_commit, "--", path).strip()
        metadata, listed = tree_line.split("\t", 1)
        mode, kind, commit_blob = metadata.split()
        assert listed == path
        assert (mode, kind) == ("100644", "blob")
        index_line = _git("ls-files", "--stage", "--", path).strip()
        index_metadata, index_path = index_line.split("\t", 1)
        index_mode, index_blob, stage = index_metadata.split()
        assert index_path == path
        assert (index_mode, stage) == ("100644", "0")
        actual_blob = _git("hash-object", "--no-filters", "--", path).strip()
        assert commit_blob == index_blob == actual_blob
    assert _git("diff", "--name-only", "--", *subject._CANDIDATE_PATHS) == ""
    assert _git("diff", "--cached", "--name-only", "--", *subject._CANDIDATE_PATHS) == ""


def test_live_tree_authority_lifecycle_matches_repository_state() -> None:
    response = _evaluate()
    profile = response["authority_lifecycle_profile"]
    head = _git("rev-parse", "HEAD").strip()
    origin = _git("rev-parse", "refs/remotes/origin/main").strip()
    ahead_text, behind_text = _git(
        "rev-list", "--left-right", "--count",
        "HEAD...refs/remotes/origin/main",
    ).split()
    ahead, behind = int(ahead_text), int(behind_text)
    tracked = tuple(sorted(_git("diff", "--name-only").splitlines()))
    staged = tuple(sorted(_git("diff", "--cached", "--name-only").splitlines()))
    untracked = tuple(sorted(_git("ls-files", "--others", "--exclude-standard").splitlines()))
    porcelain = tuple(sorted(_git(
        "status", "--porcelain=v1", "--untracked-files=all",
    ).splitlines()))
    if profile == "authority_precommit_candidate":
        assert head == origin == subject._BASE
        assert (ahead, behind) == (0, 0)
        assert tracked == staged == ()
        assert untracked == subject._CANDIDATE_PATHS
        assert porcelain == tuple(f"?? {path}" for path in subject._CANDIDATE_PATHS)
        assert all(
            stat.S_IMODE((REPO_ROOT / path).stat().st_mode) == 0o644
            for path in subject._CANDIDATE_PATHS
        )
    elif profile == "authority_committed_unpushed":
        authority_commit = response["authority_commit"]
        assert head == authority_commit
        assert origin == subject._BASE
        assert (ahead, behind) == (1, 0)
        assert tracked == staged == untracked == porcelain == ()
        _assert_formal_commit_identity(authority_commit)
    elif profile == "authority_published_successor":
        authority_commit = response["authority_commit"]
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", authority_commit, head],
            cwd=REPO_ROOT, check=False,
        ).returncode == 0
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", authority_commit, origin],
            cwd=REPO_ROOT, check=False,
        ).returncode == 0
        _assert_formal_commit_identity(authority_commit)
        assert not set(subject._CANDIDATE_PATHS).intersection(tracked + staged + untracked)
    else:
        pytest.fail(f"unknown authority lifecycle profile: {profile}")


def test_response_is_deterministic_and_has_fixed_field_order() -> None:
    first = _evaluate()
    second = _evaluate()
    assert first == second
    assert tuple(first) == subject._RESPONSE_FIELDS
    assert first["response_field_count"] == len(subject._RESPONSE_FIELDS)
    assert subject._canonical_json_bytes(first) == subject._canonical_json_bytes(second)


def test_current11_matrix_and_coverage_are_evidence_derived() -> None:
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    assert len(matrix) == 11
    assert tuple(row["sample_index_row_id"] for row in matrix) == subject._EXPECTED_SAMPLES
    for dimension in subject._DIMENSIONS:
        coverage = response["authority_dimension_coverage"][dimension]
        if dimension in ("reaction_family_label", "approved_warhead_rule"):
            assert coverage["candidate_only"] == 11
            assert coverage["authoritative_resolved"] == 0
        else:
            assert coverage["authoritative_resolved"] == 11
            assert coverage["candidate_only"] == 0


def test_graph_and_mapping_contract_is_explicit() -> None:
    response = _evaluate()
    for row in response["current11_authority_matrix"]:
        assert row["pre_reaction_connectivity_index_space"] == "retained_heavy_local_index_0based"
        assert int(row["retained_heavy_atom_count"]) > 0
        assert int(row["pre_reaction_edge_count"]) > 0
        assert set(row["bond_order_vocabulary"].split("|")) <= {
            "single", "double", "triple", "aromatic"
        }
        assert row["ligand_reactive_atom_id"].startswith("retained_heavy_local_index_0based:")
        assert row["residue_reactive_atom_id"].startswith("atom_site_id:")


def test_candidate_family_and_rule_do_not_open_readiness() -> None:
    response = _evaluate()
    assert response["unresolved_dimensions"] == (
        "reaction_family_label", "approved_warhead_rule"
    )
    assert response["current11_role_proposal_input_ready_count"] == 0
    assert response["current11_minimal_seed_input_ready_count"] == 0
    assert response["recommended_next_increment"] == subject._RECOMMENDED_NEXT


def test_warhead_review_is_not_role_seed_gold_review() -> None:
    response = _evaluate()
    assert response["warhead_boundary_human_review_completed_count"] == 11
    assert response["role_seed_human_gold_review_completed_count"] == 0
    assert all(
        row["warhead_boundary_human_review_completed"] == "true"
        and row["role_seed_human_gold_review_completed"] == "false"
        for row in response["current11_authority_matrix"]
    )


def test_murcko_and_brics_inputs_ready_without_execution() -> None:
    response = _evaluate()
    assert response["murcko_proposal_method_ready_count"] == 11
    assert response["brics_support_method_ready_count"] == 11
    assert response["murcko_executed"] is False
    assert response["brics_executed"] is False
    assert response["rdkit_imported"] is False


def test_materialization_training_and_execution_boundaries_stay_closed() -> None:
    response = _evaluate()
    for field in (
        "role_proposal_generated", "minimal_seed_proposal_generated",
        "role_annotation_materialized", "minimal_seed_materialized",
        "tensor_materialized", "review_package_generated", "ready_for_training",
        "raw_structure_read", "network_accessed", "rdkit_imported",
        "topology_restoration_executed", "murcko_executed", "brics_executed",
        "checkpoint_accessed", "forward_executed", "training_executed",
        "reward_or_rl_executed", "commit_created", "push_performed",
    ):
        assert response[field] is False


@pytest.mark.parametrize("case_id", [row[0] for row in subject._FAILURES], ids=[row[0] for row in subject._FAILURES])
def test_failure_matrix_case_fails_closed(case_id: str) -> None:
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    expected_lifecycle = _expected_lifecycle_from_valid_response(response)
    item = subject._FAILURE_MUTATIONS[case_id]
    target = item["validator_target"]
    baseline = subject._failure_baseline_v1(
        target, response, matrix, expected_lifecycle=expected_lifecycle,
    )
    subject._validate_failure_target_v1(
        target, baseline, matrix, expected_lifecycle=expected_lifecycle,
    )
    baseline_bytes = subject._canonical_json_bytes(baseline)
    mutated = copy.deepcopy(baseline)
    subject._apply_failure_mutation_v1(case_id, mutated)
    assert subject._canonical_json_bytes(mutated) != baseline_bytes
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._validate_failure_target_v1(
            target, mutated, matrix, expected_lifecycle=expected_lifecycle,
        )


_CRITICAL_RESPONSE_FIELDS = (
    "origin_main", "ahead", "behind", "authority_lifecycle_profile",
    "authority_commit", "authority_committed", "authority_published",
    "ready_for_authority_commit_review", "source_records",
    "authority_dimensions", "authority_status_vocabulary",
    "current11_authority_matrix", "authority_dimension_coverage",
    "warhead_boundary_human_review_completed_count",
    "role_seed_human_gold_review_completed_count",
    "current11_role_proposal_input_ready_count",
    "current11_minimal_seed_input_ready_count", "murcko_proposal_method_ready_count",
    "brics_support_method_ready_count", "unresolved_dimensions",
    "authority_gap_resolution_completed", "failure_matrix_case_count",
    "failure_matrix_cases", "generated_evidence_files", "recommended_next_increment",
    "ready_for_training",
)


def _tamper_critical_response_field(response: dict[str, object], field: str) -> None:
    if field == "authority_lifecycle_profile":
        profiles = subject._LIFECYCLE_PROFILES
        response[field] = profiles[(profiles.index(response[field]) + 1) % len(profiles)]
    elif field == "authority_commit":
        response[field] = _different_sha(response[field])
    elif field == "origin_main":
        response[field] = _different_sha(response[field])
    elif field in (
        "authority_committed", "authority_published",
        "ready_for_authority_commit_review", "authority_gap_resolution_completed",
        "ready_for_training",
    ):
        response[field] = not response[field]
    elif field in (
        "source_records", "authority_dimensions", "authority_status_vocabulary",
        "failure_matrix_cases", "generated_evidence_files", "unresolved_dimensions",
    ):
        response[field] = response[field][:-1]
    elif field == "current11_authority_matrix":
        changed = list(copy.deepcopy(response[field]))
        changed[0]["pdb_id"] = "WRONG"
        response[field] = tuple(changed)
    elif field == "authority_dimension_coverage":
        response[field]["retained_heavy_atom_mapping"]["authoritative_resolved"] = 10
    elif field == "recommended_next_increment":
        response[field] = "wrong"
    else:
        response[field] += 1


@pytest.mark.parametrize("field", _CRITICAL_RESPONSE_FIELDS, ids=_CRITICAL_RESPONSE_FIELDS)
def test_critical_response_tampering_fails_even_with_recomputed_digest(field: str) -> None:
    assert len(_CRITICAL_RESPONSE_FIELDS) == 26
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    expected_lifecycle = _expected_lifecycle_from_valid_response(response)
    tampered = copy.deepcopy(response)
    original_bytes = subject._canonical_json_bytes(response)
    _tamper_critical_response_field(tampered, field)
    assert subject._canonical_json_bytes(tampered) != original_bytes
    subject._rehash_response_v1(tampered)
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._validate_response_v1(
            tampered, matrix, expected_lifecycle=expected_lifecycle,
        )


def _lifecycle_facts(profile: str) -> dict[str, object]:
    return subject._synthetic_lifecycle_facts_v1(profile)


@pytest.mark.parametrize("profile", (
    "authority_precommit_candidate", "authority_committed_unpushed",
    "authority_published_successor",
))
def test_authority_lifecycle_profiles_are_commit_survivable(profile: str) -> None:
    result = subject._derive_authority_lifecycle_v1(_lifecycle_facts(profile))
    assert result["authority_lifecycle_profile"] == profile
    assert result["authority_committed"] is (profile != "authority_precommit_candidate")
    assert result["authority_published"] is (profile == "authority_published_successor")


def _apply_response_lifecycle_profile(
    response: dict[str, object], profile: str,
) -> None:
    if profile == "authority_precommit_candidate":
        lifecycle = {
            "origin_main": subject._BASE, "ahead": 0, "behind": 0,
            "authority_lifecycle_profile": profile, "authority_commit": None,
            "authority_committed": False, "authority_published": False,
            "ready_for_authority_commit_review": True,
        }
    elif profile == "authority_committed_unpushed":
        lifecycle = {
            "origin_main": subject._BASE, "ahead": 1, "behind": 0,
            "authority_lifecycle_profile": profile, "authority_commit": "f" * 40,
            "authority_committed": True, "authority_published": False,
            "ready_for_authority_commit_review": False,
        }
    else:
        lifecycle = {
            "origin_main": "d" * 40, "ahead": 2, "behind": 3,
            "authority_lifecycle_profile": profile, "authority_commit": "f" * 40,
            "authority_committed": True, "authority_published": True,
            "ready_for_authority_commit_review": False,
        }
    if profile not in subject._LIFECYCLE_PROFILES:
        raise AssertionError(profile)
    response.update(lifecycle)


@pytest.mark.parametrize("profile", subject._LIFECYCLE_PROFILES)
def test_response_lifecycle_profiles_are_cross_field_valid(profile: str) -> None:
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    _apply_response_lifecycle_profile(response, profile)
    subject._rehash_response_v1(response)
    expected_lifecycle = _expected_lifecycle_from_valid_response(response)
    subject._validate_response_v1(
        response, matrix, expected_lifecycle=expected_lifecycle,
    )


@pytest.mark.parametrize("profile", subject._LIFECYCLE_PROFILES)
def test_checker_accepts_exact3_lifecycle_response_profiles(
    profile: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    response = _evaluate()
    _apply_response_lifecycle_profile(response, profile)
    subject._rehash_response_v1(response)

    def evaluate_stub(*, repo_root: Path) -> dict[str, object]:
        assert repo_root == REPO_ROOT
        return copy.deepcopy(response)

    monkeypatch.setattr(
        checker_subject,
        "evaluate_covapie_role_annotation_input_authority_gap_resolution_v1",
        evaluate_stub,
    )
    assert checker_subject.main() == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == json.loads(subject._canonical_json_bytes(response))


def test_response_lifecycle_witness_is_exact_ordered_typed_and_required() -> None:
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    expected_lifecycle = _expected_lifecycle_from_valid_response(response)
    assert tuple(expected_lifecycle) == subject._RESPONSE_LIFECYCLE_FIELDS
    derived = {
        field: expected_lifecycle[field]
        for field in subject._DERIVED_LIFECYCLE_FIELDS
    }
    assert subject._build_expected_response_lifecycle_v1(
        origin_main=expected_lifecycle["origin_main"],
        ahead=expected_lifecycle["ahead"], behind=expected_lifecycle["behind"],
        lifecycle=derived,
    ) == expected_lifecycle
    parameter = inspect.signature(subject._validate_response_v1).parameters[
        "expected_lifecycle"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        subject._validate_response_v1(response, matrix)
    for invalid in (
        {key: value for key, value in expected_lifecycle.items() if key != "behind"},
        {**expected_lifecycle, "extra": False},
        {**expected_lifecycle, "ahead": False},
    ):
        with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
            subject._validate_response_v1(
                response, matrix, expected_lifecycle=invalid,
            )


@pytest.mark.parametrize("profile", (
    "authority_committed_unpushed", "authority_published_successor",
))
def test_valid_looking_authority_commit_sha_substitution_fails_external_witness(
    profile: str,
) -> None:
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    _apply_response_lifecycle_profile(response, profile)
    subject._rehash_response_v1(response)
    expected_lifecycle = _expected_lifecycle_from_valid_response(response)
    original_bytes = subject._canonical_json_bytes(response)
    response["authority_commit"] = _different_sha(response["authority_commit"])
    assert subject._canonical_json_bytes(response) != original_bytes
    subject._rehash_response_v1(response)
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._validate_response_v1(
            response, matrix, expected_lifecycle=expected_lifecycle,
        )


@pytest.mark.parametrize("profile", (
    "authority_committed_unpushed", "authority_published_successor",
))
def test_committed_and_published_lifecycle_reject_base_as_authority_commit(
    profile: str,
) -> None:
    response = _evaluate()
    _apply_response_lifecycle_profile(response, profile)
    response["authority_commit"] = subject._BASE
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._validate_response_lifecycle_v1(response)


@pytest.mark.parametrize("field", ("origin_main", "ahead", "behind"))
def test_valid_looking_published_git_fact_substitution_fails_external_witness(
    field: str,
) -> None:
    response = _evaluate()
    matrix = response["current11_authority_matrix"]
    _apply_response_lifecycle_profile(response, "authority_published_successor")
    subject._rehash_response_v1(response)
    expected_lifecycle = _expected_lifecycle_from_valid_response(response)
    original_bytes = subject._canonical_json_bytes(response)
    if field == "origin_main":
        response[field] = _different_sha(response[field])
    else:
        response[field] += 1
    assert subject._canonical_json_bytes(response) != original_bytes
    subject._rehash_response_v1(response)
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._validate_response_v1(
            response, matrix, expected_lifecycle=expected_lifecycle,
        )


def test_future_unrelated_successor_is_allowed() -> None:
    facts = _lifecycle_facts("authority_published_successor")
    facts["head"] = "c" * 40
    facts["origin"] = "b" * 40
    result = subject._derive_authority_lifecycle_v1(facts)
    assert result["authority_lifecycle_profile"] == "authority_published_successor"


_LIFECYCLE_NEGATIVE_CASES = (
    "wrong_parent", "wrong_subject", "extra_candidate_path_commit",
    "one_status_not_A", "mode_100755", "index_blob_drift",
    "actual_worktree_blob_drift", "committed_state_not_1_0",
    "published_commit_not_ancestor_of_origin",
)


def _mutate_lifecycle_negative(facts: dict[str, object], case: str) -> None:
    first = subject._CANDIDATE_PATHS[0]
    if case == "wrong_parent":
        facts["path_commits"][0]["parents"] = ["0" * 40]
    elif case == "wrong_subject":
        facts["path_commits"][0]["subject"] = "wrong"
    elif case == "extra_candidate_path_commit":
        extra = "docs/unrelated.md"
        facts["path_commits"][0]["changed_paths"] += (extra,)
        facts["path_commits"][0]["changed_statuses"][extra] = "A"
    elif case == "one_status_not_A":
        facts["path_commits"][0]["changed_statuses"][first] = "M"
    elif case == "mode_100755":
        facts["path_commits"][0]["path_modes"][first] = "100755"
    elif case == "index_blob_drift":
        facts["live_paths"][first]["index_blob"] = "a" * 40
    elif case == "actual_worktree_blob_drift":
        facts["live_paths"][first]["blob"] = "a" * 40
    elif case == "committed_state_not_1_0":
        facts["ahead"] = 2
    elif case == "published_commit_not_ancestor_of_origin":
        facts["path_commits"][0]["ancestor_origin"] = False
    else:
        raise AssertionError(case)


@pytest.mark.parametrize("case", _LIFECYCLE_NEGATIVE_CASES, ids=_LIFECYCLE_NEGATIVE_CASES)
def test_lifecycle_negative_states_fail_closed(case: str) -> None:
    profile = (
        "authority_published_successor"
        if case == "published_commit_not_ancestor_of_origin"
        else "authority_committed_unpushed"
    )
    baseline = _lifecycle_facts(profile)
    subject._derive_authority_lifecycle_v1(baseline)
    baseline_bytes = subject._canonical_json_bytes(baseline)
    mutated = copy.deepcopy(baseline)
    _mutate_lifecycle_negative(mutated, case)
    assert subject._canonical_json_bytes(mutated) != baseline_bytes
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._derive_authority_lifecycle_v1(mutated)


def test_import_is_silent_and_does_not_import_torch_or_rdkit() -> None:
    code = (
        f"import sys; sys.path.insert(0, {str(SRC)!r}); "
        "import covalent_ext.covapie_role_annotation_input_authority_gap_resolution_v1; "
        "assert 'torch' not in sys.modules; assert 'rdkit' not in sys.modules"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT,
                            check=False, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_failure_matrix_binds_every_registered_case_to_this_test() -> None:
    rows = subject._strict_csv((REPO_ROOT / subject._FAILURE_PATH).read_bytes(), subject._FAILURE_COLUMNS)
    assert len(rows) == 36
    assert tuple(row["case_id"] for row in rows) == tuple(subject._FAILURE_MUTATIONS)
    assert len({row["mutation_signature"] for row in rows}) == 36
    assert all(
        row["mutation_signature"] == subject._FAILURE_MUTATIONS[row["case_id"]]["mutation_signature"]
        and row["validator_target"] == subject._FAILURE_MUTATIONS[row["case_id"]]["validator_target"]
        for row in rows
    )
    assert all("test_failure_matrix_case_fails_closed" in row["test_node_id"] for row in rows)


def test_module_has_exactly_one_public_api() -> None:
    assert subject.__all__ == (
        "evaluate_covapie_role_annotation_input_authority_gap_resolution_v1",
    )
    reloaded = importlib.reload(subject)
    assert reloaded.__all__ == subject.__all__
