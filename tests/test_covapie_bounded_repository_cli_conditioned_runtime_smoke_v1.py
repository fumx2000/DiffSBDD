from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bounded_repository_cli_conditioned_runtime_smoke_v1 as implementation,
)


ROOT = Path(__file__).resolve().parents[1]
ERROR = "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_INVALID"
CONSUMED_ERROR = (
    "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_"
    "EXECUTION_AUTHORIZATION_CONSUMED"
)
PYTHON = Path(sys.executable).resolve()
TERMINAL_COMMIT = "a" * 40
SUCCESSOR_COMMIT = "b" * 40


@pytest.fixture(scope="session")
def response() -> dict[str, object]:
    return implementation.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1(
        repo_root=ROOT
    )


@pytest.fixture()
def valid_evidence() -> dict[str, object]:
    empty_sha = hashlib.sha256(b"").hexdigest()
    state_sha = "1" * 64
    values: dict[str, object] = {
        "evidence_schema_version": implementation._EVIDENCE_VERSION,
        "caller": "generate_ligands.py",
        "argv": implementation._expected_cli_argv(Path("/tmp/workspace")),
        "environment": dict(implementation._CHILD_ENVIRONMENT),
        "child_returncode": 0,
        "resolved_device": "cpu",
        "cuda_available": False,
        "stdout_byte_count": 0,
        "stdout_sha256": empty_sha,
        "stderr_byte_count": 0,
        "stderr_sha256": empty_sha,
        "resolver_call_count": 1,
        "selector": dict(implementation._EXACT6_SELECTOR),
        "conditioned_loader_call_count": 1,
        "legacy_loader_call_count": 0,
        "checkpoint_path": implementation._CHECKPOINT_RELATIVE_PATH,
        "map_location": "cpu",
        "model_target_residue_atom_conditioning": True,
        "dynamics_target_residue_atom_conditioning": True,
        "condition_embedding_shape": [32],
        "condition_embedding_all_zero": True,
        "state_key_count": 123,
        "prepare_pocket_call_count": 1,
        "pocket_size": [6],
        "indicator_field_present": True,
        "indicator_dtype": "bool",
        "indicator_shape": [6],
        "indicator_true_count": 1,
        "indicator_true_atom": dict(implementation._EXACT6_SELECTOR),
        "generate_ligands_call_count": 1,
        "n_samples": 1,
        "pocket_ids": ["A:1"],
        "ref_ligand": None,
        "timesteps": 1,
        "selector_object_is_resolver_output": True,
        "ddpm_type": "ConditionalDDPM",
        "dynamics_forward_call_count": 2,
        "model_forward_executed": True,
        "real_generation_path_executed": True,
        "training_step_executed": False,
        "backward_executed": False,
        "optimizer_created": False,
        "optimizer_step_executed": False,
        "scheduler_step_executed": False,
        "all_parameter_grads_none": True,
        "model_state_digest_before": state_sha,
        "model_state_digest_after": state_sha,
        "parameter_values_modified": False,
        "parameter_versions_modified": False,
        "checkpoint_size_before": implementation._CHECKPOINT_SIZE,
        "checkpoint_size_after": implementation._CHECKPOINT_SIZE,
        "checkpoint_mtime_ns_before": 123,
        "checkpoint_mtime_ns_after": 123,
        "checkpoint_sha256_before": implementation._CHECKPOINT_SHA256,
        "checkpoint_sha256_after": implementation._CHECKPOINT_SHA256,
        "checkpoint_bytes_unchanged": True,
        "forbidden_save_api_call_count": 0,
        "generated_molecule_count": 0,
        "output_sdf_exists": True,
        "output_sdf_regular": True,
        "output_sdf_symlink": False,
        "output_sdf_size": 0,
        "output_sdf_record_count": 0,
        "chemical_generation_quality_validated": False,
        "workspace_st_dev": 11,
        "workspace_st_ino": 22,
        "workspace_allowed_relative_paths": list(
            implementation._ALLOWED_WORKSPACE_FILES
        ),
    }
    return {field: values[field] for field in implementation._EVIDENCE_FIELDS}


def _validate(evidence: dict[str, object]) -> bool:
    return implementation._validate_runtime_evidence(
        evidence=evidence,
        required_fields=implementation._EVIDENCE_FIELDS,
        expected_argv=implementation._expected_cli_argv(Path("/tmp/workspace")),
        expected_environment=implementation._CHILD_ENVIRONMENT,
        workspace_identity={"st_dev": 11, "st_ino": 22},
    )


def _terminal_candidate() -> dict[str, object]:
    exact_paths = sorted(implementation._IMPLEMENTATION_FILES)
    return {
        "commit": TERMINAL_COMMIT,
        "subject": implementation._TERMINAL_COMMIT_SUBJECT,
        "parent": implementation._DESIGN_COMMIT,
        "body_empty": True,
        "single_parent": True,
        "path_scope": exact_paths,
        "path_statuses": {path: "A" for path in exact_paths},
        "path_modes": {path: "100644" for path in exact_paths},
        "commit_blobs_bound": True,
        "live_bytes_match_commit": True,
        "files_ordinary_regular": True,
        "files_non_symlink": True,
        "files_non_executable": True,
        "worktree_drift_paths": [],
        "staged_drift_paths": [],
        "ancestor_of_HEAD": True,
        "ancestor_of_origin_main": False,
    }


def _terminal_lifecycle_facts(profile: str) -> dict[str, object]:
    exact_paths = sorted(implementation._IMPLEMENTATION_FILES)
    common: dict[str, object] = {
        "branch": "main",
        "real_remote_main": None,
        "tracked_modifications": [],
        "staged_index": [],
    }
    if profile == "terminal_precommit_candidate":
        return {
            **common,
            "HEAD": implementation._DESIGN_COMMIT,
            "origin_main": implementation._DESIGN_COMMIT,
            "ahead": 0,
            "behind": 0,
            "ordinary_untracked": exact_paths,
            "ordinary_untracked_count": 4,
            "terminal_candidates": [],
        }
    candidate = _terminal_candidate()
    if profile == "terminal_committed_unpushed":
        return {
            **common,
            "HEAD": TERMINAL_COMMIT,
            "origin_main": implementation._DESIGN_COMMIT,
            "ahead": 1,
            "behind": 0,
            "ordinary_untracked": [],
            "ordinary_untracked_count": 0,
            "terminal_candidates": [candidate],
        }
    candidate["ancestor_of_origin_main"] = True
    current = TERMINAL_COMMIT if profile == "terminal_published_successor" else SUCCESSOR_COMMIT
    return {
        **common,
        "HEAD": current,
        "origin_main": current,
        "ahead": 0,
        "behind": 0,
        "ordinary_untracked": [],
        "ordinary_untracked_count": 0,
        "terminal_candidates": [candidate],
    }


def test_public_apis_are_exact_and_keyword_only() -> None:
    assert implementation.__all__ == (
        "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1",
        "execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1",
    )
    for name, parameters in (
        (implementation.__all__[0], ["repo_root"]),
        (implementation.__all__[1], ["repo_root", "python_executable"]),
    ):
        signature = inspect.signature(getattr(implementation, name))
        assert list(signature.parameters) == parameters
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in signature.parameters.values()
        )


def test_import_is_silent_and_does_not_import_torch() -> None:
    code = """
import contextlib, importlib, io, sys
before = set(sys.modules)
stdout = io.StringIO()
stderr = io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    module = importlib.import_module(
        'covalent_ext.covapie_bounded_repository_cli_conditioned_runtime_smoke_v1'
    )
assert stdout.getvalue() == ''
assert stderr.getvalue() == ''
assert 'torch' not in set(sys.modules) - before
assert len(module.__all__) == 2
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".:src:scripts",
        },
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""


def test_module_has_no_top_level_torch_import_or_runtime_call() -> None:
    source = Path(implementation.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    top_imports = {
        alias.name.split(".")[0]
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    }
    assert "torch" not in top_imports
    assert "torch.load" not in source


def test_static_response_is_ordered_json_safe_and_digest_bound(
    response: dict[str, object],
) -> None:
    fields = implementation._IMPLEMENTATION_RESPONSE_FIELDS
    assert tuple(response) == fields
    assert len(response) == len(fields) == 36
    unsigned = {field: response[field] for field in fields[:-1]}
    assert response[fields[-1]] == hashlib.sha256(
        implementation._canonical_json_bytes(unsigned)
    ).hexdigest()
    assert json.loads(implementation._canonical_json_bytes(response)) == response
    assert implementation._validate_implementation_response(response)


def test_terminal_response_and_next_step_are_exact(
    response: dict[str, object],
) -> None:
    assert response["one_time_execution_authorization_consumed"] is True
    assert response["exact67_runtime_evidence_available"] is False
    assert response["ready_for_one_time_bounded_runtime_smoke_execution"] is False
    assert response["reexecution_requires_new_explicit_user_authorization"] is True
    assert response["failure_establishes_model_runtime_failure"] is False
    assert response["failure_establishes_conditioned_plumbing_failure"] is False
    assert response["recommended_next_step"] == (
        "audit_covapie_five_module_training_path_completion_gaps_v1"
    )


@pytest.mark.parametrize(
    ("requested_profile", "expected_profile", "published"),
    [
        ("terminal_precommit_candidate", "terminal_precommit_candidate", False),
        ("terminal_committed_unpushed", "terminal_committed_unpushed", False),
        ("terminal_published_successor", "terminal_published_successor", True),
        ("future_unrelated_successor", "terminal_published_successor", True),
    ],
)
def test_terminal_lifecycle_valid_profiles_and_future_successor(
    requested_profile: str,
    expected_profile: str,
    published: bool,
) -> None:
    lifecycle = implementation._terminal_lifecycle_from_facts(
        _terminal_lifecycle_facts(requested_profile)
    )
    assert lifecycle["profile"] == expected_profile
    assert lifecycle["terminal_published"] is published
    assert implementation._validate_terminal_lifecycle_evidence(lifecycle)
    if requested_profile == "future_unrelated_successor":
        assert lifecycle["current_HEAD"] == SUCCESSOR_COMMIT
        assert lifecycle["terminal_commit"] == TERMINAL_COMMIT


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_parent",
        "wrong_subject",
        "nonempty_body",
        "wrong_path_scope",
        "wrong_mode",
        "commit_blob_drift",
        "live_bytes_drift",
        "worktree_drift",
        "staged_drift",
        "multiple_candidates",
        "precommit_extra_untracked",
    ],
)
def test_terminal_lifecycle_invalid_facts_fail_closed(mutation: str) -> None:
    if mutation == "precommit_extra_untracked":
        facts = _terminal_lifecycle_facts("terminal_precommit_candidate")
        facts["ordinary_untracked"] = [
            *facts["ordinary_untracked"],
            "unexpected.txt",
        ]
        facts["ordinary_untracked_count"] = 5
    else:
        facts = _terminal_lifecycle_facts("terminal_committed_unpushed")
        candidate = facts["terminal_candidates"][0]
        if mutation == "wrong_parent":
            candidate["parent"] = "c" * 40
        elif mutation == "wrong_subject":
            candidate["subject"] = "wrong terminal subject"
        elif mutation == "nonempty_body":
            candidate["body_empty"] = False
        elif mutation == "wrong_path_scope":
            candidate["path_scope"] = candidate["path_scope"][:-1]
        elif mutation == "wrong_mode":
            path = candidate["path_scope"][0]
            candidate["path_modes"][path] = "100755"
        elif mutation == "commit_blob_drift":
            candidate["commit_blobs_bound"] = False
        elif mutation == "live_bytes_drift":
            candidate["live_bytes_match_commit"] = False
        elif mutation == "worktree_drift":
            candidate["worktree_drift_paths"] = [candidate["path_scope"][0]]
        elif mutation == "staged_drift":
            candidate["staged_drift_paths"] = [candidate["path_scope"][0]]
        else:
            facts["terminal_candidates"].append(copy.deepcopy(candidate))
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        implementation._terminal_lifecycle_from_facts(facts)


def test_current_terminal_lifecycle_matches_live_repository_state(
    response: dict[str, object],
) -> None:
    lifecycle = response["git_precondition"]
    assert implementation._validate_terminal_lifecycle_evidence(lifecycle)

    def git_text(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            timeout=30,
        )
        assert completed.returncode == 0
        assert completed.stderr == b""
        return completed.stdout.decode("utf-8", errors="strict").strip()

    actual_head = git_text("rev-parse", "HEAD")
    actual_origin = git_text("rev-parse", "origin/main")
    assert lifecycle["current_HEAD"] == actual_head
    assert lifecycle["current_origin_main"] == actual_origin
    assert lifecycle["exact_path_scope"] == list(implementation._IMPLEMENTATION_FILES)
    assert lifecycle["one_time_execution_authorization_consumed"] is True

    profile = lifecycle["profile"]
    if profile == "terminal_precommit_candidate":
        assert lifecycle["terminal_commit"] is None
        assert lifecycle["terminal_committed"] is False
        assert lifecycle["terminal_published"] is False
        assert lifecycle["ready_for_terminalized_implementation_commit_review"] is True
        assert actual_head == implementation._DESIGN_COMMIT
        assert actual_origin == implementation._DESIGN_COMMIT
        assert lifecycle["ahead"] == 0
        assert lifecycle["behind"] == 0
    elif profile == "terminal_committed_unpushed":
        assert lifecycle["terminal_commit"] == actual_head
        assert lifecycle["terminal_committed"] is True
        assert lifecycle["terminal_published"] is False
        assert lifecycle["ready_for_terminalized_implementation_commit_review"] is False
        assert actual_origin == implementation._DESIGN_COMMIT
        assert lifecycle["ahead"] == 1
        assert lifecycle["behind"] == 0
    elif profile == "terminal_published_successor":
        terminal_commit = lifecycle["terminal_commit"]
        assert isinstance(terminal_commit, str)
        assert len(terminal_commit) == 40
        int(terminal_commit, 16)
        assert lifecycle["terminal_committed"] is True
        assert lifecycle["terminal_published"] is True
        assert lifecycle["ready_for_terminalized_implementation_commit_review"] is False
        for descendant in (actual_head, actual_origin):
            completed = subprocess.run(
                ["git", "merge-base", "--is-ancestor", terminal_commit, descendant],
                cwd=ROOT,
                check=False,
                capture_output=True,
                timeout=30,
            )
            assert completed.returncode == 0
            assert completed.stdout == b""
            assert completed.stderr == b""
    else:
        pytest.fail(f"unexpected terminal lifecycle profile: {profile}")


def test_one_time_execution_record_binds_executed_sources_and_failure(
    response: dict[str, object],
) -> None:
    record = response["one_time_execution_record"]
    assert record["one_time_execution_authorization_consumed"] is True
    assert record["bounded_runtime_smoke_execution_count"] == 1
    assert record["bounded_runtime_smoke_passed"] is False
    assert record["automatic_retry_performed"] is False
    assert record["architecture_expansion_authorized"] is False
    assert record["Exact67_evidence"] == {
        "field_count": 0,
        "bytes": 0,
        "sha256": None,
        "available": False,
    }
    assert record["failure"]["first_failure_stage"] == (
        "child_internal_stderr_gate_before_exact67_evidence"
    )
    assert record["failure"]["observed_warning"] == {
        "category": "UserWarning",
        "message": (
            '"import openbabel" is deprecated, instead use '
            '"from openbabel import openbabel"'
        ),
    }
    assert record["failure"][
        "direct_generate_ligands_source_line_attribution_proven"
    ] is False
    expected_executed = {
        path: {"sha256": sha, "size": size, "lines": lines, "mode": mode}
        for path, sha, size, lines, mode in implementation._EXECUTED_SOURCE_IDENTITIES
    }
    assert record["executed_source_identities"] == expected_executed
    assert record["current_terminalized_source_identities"] == response[
        "implementation_file_identities"
    ]


def test_one_time_execution_safety_record_is_exact(
    response: dict[str, object],
) -> None:
    safety = response["one_time_execution_record"]["safety"]
    assert safety["checkpoint_unchanged"] is True
    assert safety["git_unchanged"] is True
    assert safety["workspace"] == {
        "st_dev": 66_307,
        "st_ino": 7_380_511_365,
        "inode_guard_matched": True,
        "removed": True,
        "exists_after": False,
        "competitor_path_deleted": False,
    }
    assert safety["checkpoint_identity"] == {
        "st_dev": 49,
        "st_ino": 195_679_527_872,
        "st_mode": 33_188,
        "mode_octal": "0644",
        "size": 17_861_341,
        "mtime_ns": 1_785_552_510_663_618_359,
        "sha256": implementation._CHECKPOINT_SHA256,
    }
    assert safety["training_or_parameter_update"] is False
    assert safety["RL_implementation_started"] is False
    assert safety["commit_created"] is False
    assert safety["push_performed"] is False


def test_static_evaluator_is_deterministic_for_reconstructed_values(
    response: dict[str, object],
) -> None:
    reconstructed = json.loads(implementation._canonical_json_bytes(response))
    assert reconstructed == response
    assert implementation._canonical_json_bytes(reconstructed) == (
        implementation._canonical_json_bytes(response)
    )


def test_static_evaluator_fails_closed_for_invalid_root() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        implementation.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1(
            repo_root=Path(".")
        )


def test_design_commit_files_and_published_response_are_bound(
    response: dict[str, object],
) -> None:
    commit = response["source_design_commit_identity"]
    assert commit == {
        "commit": implementation._DESIGN_COMMIT,
        "parent": implementation._DESIGN_PARENT,
        "subject": implementation._DESIGN_SUBJECT,
        "exact_path_count": 4,
        "ancestor_of_HEAD": True,
        "ancestor_of_origin_main": True,
    }
    assert len(response["source_design_file_identities"]) == 4
    published = response["published_design_response_binding"]
    assert published["current_response_exact_field_count"] == 50
    assert published["published_snapshot_response_sha256"] == (
        implementation._DESIGN_RESPONSE_SHA256
    )
    assert len(published["current_response_sha256"]) == 64
    assert published["design_commit"] == implementation._DESIGN_COMMIT
    assert published["design_commit_is_ancestor_of_HEAD"] is True
    assert published["design_commit_is_ancestor_of_origin_main"] is True
    assert published["ready_for_bounded_runtime_smoke_implementation"] is True


def test_dynamic_design_response_sha_binding_across_lifecycle_profiles() -> None:
    design_response, _ = implementation._bind_design(ROOT)
    ref_pairs = (
        (implementation._DESIGN_COMMIT, implementation._DESIGN_COMMIT),
        (TERMINAL_COMMIT, implementation._DESIGN_COMMIT),
        (TERMINAL_COMMIT, TERMINAL_COMMIT),
    )
    bindings = []
    for head, origin in ref_pairs:
        synthetic = copy.deepcopy(design_response)
        synthetic["runtime_source_bindings"]["current_HEAD"] = head
        synthetic["runtime_source_bindings"]["current_origin_main"] = origin
        unsigned = {
            field: value
            for field, value in synthetic.items()
            if field != "bounded_runtime_smoke_design_response_sha256"
        }
        synthetic["bounded_runtime_smoke_design_response_sha256"] = hashlib.sha256(
            implementation._canonical_json_bytes(unsigned)
        ).hexdigest()
        bindings.append(
            implementation._published_design_response_binding(
                synthetic,
                design_commit_is_ancestor_of_HEAD=True,
                design_commit_is_ancestor_of_origin_main=True,
            )
        )
    assert len({binding["current_response_sha256"] for binding in bindings}) == 3
    assert {
        binding["published_snapshot_response_sha256"] for binding in bindings
    } == {implementation._DESIGN_RESPONSE_SHA256}
    assert [(item["current_HEAD"], item["current_origin_main"]) for item in bindings] == list(
        ref_pairs
    )


def test_fresh_runtime_sources_and_checkpoint_are_revalidated(
    response: dict[str, object],
) -> None:
    runtime = response["fresh_runtime_source_revalidation"]
    assert runtime["snapshot_commit"] == implementation._RUNTIME_SNAPSHOT
    assert runtime["snapshot_is_ancestor_of_HEAD"] is True
    assert runtime["snapshot_is_ancestor_of_origin_main"] is True
    assert runtime["source_count"] == 3
    assert runtime["all_live_bytes_match_snapshot"] is True
    checkpoint = response["checkpoint_binding"]
    assert checkpoint["size"] == implementation._CHECKPOINT_SIZE
    assert checkpoint["sha256"] == implementation._CHECKPOINT_SHA256
    assert checkpoint["deserialized_by_static_evaluator"] is False


def test_exact67_field_order_is_directly_bound_to_design(
    response: dict[str, object],
) -> None:
    schema = response["runtime_evidence_schema"]
    assert schema["required_fields"] == list(implementation._EVIDENCE_FIELDS)
    assert schema["required_field_count"] == len(implementation._EVIDENCE_FIELDS) == 67
    assert len(set(schema["required_fields"])) == 67


def test_canonical_evidence_validator_accepts_valid_facts(
    valid_evidence: dict[str, object],
) -> None:
    assert _validate(valid_evidence)
    encoded = implementation._canonical_json_bytes(valid_evidence)
    assert not encoded.endswith(b"\n")
    assert implementation._canonical_json_bytes(json.loads(encoded)) == encoded


@pytest.mark.parametrize("mutation", ["missing", "extra", "nan"])
def test_canonical_evidence_validator_fails_closed_on_shape_or_nan(
    valid_evidence: dict[str, object], mutation: str
) -> None:
    tampered = copy.deepcopy(valid_evidence)
    if mutation == "missing":
        tampered.pop("selector")
    elif mutation == "extra":
        tampered["extra"] = False
    else:
        tampered["output_sdf_size"] = float("nan")
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(tampered)


def test_wrong_selector_fails_closed(valid_evidence: dict[str, object]) -> None:
    valid_evidence["selector"]["atom_name"] = "CB"
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(valid_evidence)


def test_wrong_forward_count_fails_closed(valid_evidence: dict[str, object]) -> None:
    valid_evidence["dynamics_forward_call_count"] = 1
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(valid_evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("indicator_true_count", 0),
        ("indicator_shape", [5]),
        ("indicator_dtype", "torch.bool"),
        ("indicator_true_atom", None),
    ],
)
def test_wrong_indicator_fails_closed(
    valid_evidence: dict[str, object], field: str, value: object
) -> None:
    valid_evidence[field] = value
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(valid_evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("parameter_values_modified", True),
        ("parameter_versions_modified", True),
        ("all_parameter_grads_none", False),
        ("backward_executed", True),
        ("optimizer_created", True),
    ],
)
def test_parameter_or_training_drift_fails_closed(
    valid_evidence: dict[str, object], field: str, value: object
) -> None:
    valid_evidence[field] = value
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(valid_evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("checkpoint_size_after", 1),
        ("checkpoint_mtime_ns_after", 124),
        ("checkpoint_sha256_after", "2" * 64),
        ("checkpoint_bytes_unchanged", False),
    ],
)
def test_checkpoint_drift_fails_closed(
    valid_evidence: dict[str, object], field: str, value: object
) -> None:
    valid_evidence[field] = value
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(valid_evidence)


def test_stderr_nonempty_fails_closed(valid_evidence: dict[str, object]) -> None:
    valid_evidence["stderr_byte_count"] = 1
    valid_evidence["stderr_sha256"] = hashlib.sha256(b"x").hexdigest()
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate(valid_evidence)


def _make_allowed_workspace(path: Path) -> None:
    for name in implementation._ALLOWED_WORKSPACE_DIRECTORIES:
        (path / name).mkdir()
    for relative in implementation._ALLOWED_WORKSPACE_FILES:
        (path / relative).write_bytes(b"")


def test_workspace_closed_allowlist_accepts_exact_paths(tmp_path: Path) -> None:
    _make_allowed_workspace(tmp_path)
    assert implementation._validate_workspace_contents(
        tmp_path, require_success_files=True
    )


def test_workspace_closed_allowlist_rejects_extra_path(tmp_path: Path) -> None:
    _make_allowed_workspace(tmp_path)
    (tmp_path / "logs" / "extra.bin").write_bytes(b"x")
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        implementation._validate_workspace_contents(
            tmp_path, require_success_files=True
        )


def test_inode_competitor_guard_does_not_delete(tmp_path: Path) -> None:
    workspace = tmp_path / "guarded"
    workspace.mkdir()
    metadata = os.lstat(workspace)
    calls: list[Path] = []
    result = implementation._safe_cleanup_workspace(
        workspace,
        expected_st_dev=metadata.st_dev,
        expected_st_ino=metadata.st_ino + 1,
        remover=lambda path: calls.append(path),
    )
    assert result["inode_guard_matched"] is False
    assert result["removed"] is False
    assert result["competitor_path_deleted"] is False
    assert calls == []
    assert workspace.is_dir()


def test_timeout_result_is_fail_closed_and_workspace_is_cleanable(
    tmp_path: Path,
) -> None:
    def timeout_runner(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise subprocess.TimeoutExpired(cmd=["child"], timeout=300)

    facts = implementation._run_child_process(
        command=["child"],
        repo_root=ROOT,
        environment={},
        runner=timeout_runner,
    )
    assert facts == {
        "timeout": True,
        "returncode": None,
        "stdout": b"",
        "stderr": b"",
    }
    workspace = tmp_path / "timeout_workspace"
    workspace.mkdir()
    metadata = os.lstat(workspace)
    cleanup = implementation._safe_cleanup_workspace(
        workspace,
        expected_st_dev=metadata.st_dev,
        expected_st_ino=metadata.st_ino,
    )
    assert cleanup["removed"] is True
    assert cleanup["exists_after"] is False


def test_child_command_and_cli_contract_are_exact(tmp_path: Path) -> None:
    command = implementation._child_command(ROOT, PYTHON, tmp_path)
    assert command == [
        str(PYTHON),
        "-B",
        "-m",
        "covalent_ext.covapie_bounded_repository_cli_conditioned_runtime_smoke_v1",
        "--child",
        "--repo-root",
        str(ROOT),
        "--workspace",
        str(tmp_path),
    ]
    argv = implementation._expected_cli_argv(tmp_path)
    assert argv[0] == "generate_ligands.py"
    assert argv[1] == implementation._CHECKPOINT_RELATIVE_PATH
    assert "--timesteps" in argv and argv[argv.index("--timesteps") + 1] == "1"
    assert all(
        excluded not in argv
        for excluded in ("--ref_ligand", "--sanitize", "--relax", "--all_frags")
    )


def test_child_environment_is_cpu_bounded() -> None:
    assert implementation._CHILD_ENVIRONMENT == {
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": ".:src:scripts",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
    }


def test_transparent_observer_source_contract() -> None:
    source = Path(implementation.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    assert "register_forward_hook" in {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "generate_ligands.py" in strings
    assert "strict=False" not in source
    assert "torch.save(" not in source


def test_transparent_observers_install_and_restore_without_model_construction() -> None:
    import torch
    from covalent_ext import covapie_target_residue_atom_condition_repository_cli_v1 as cli
    from lightning_modules import LigandPocketDDPM

    originals = (
        cli.resolve_covapie_target_residue_atom_condition_cli_args_v1,
        cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1,
        LigandPocketDDPM.prepare_pocket,
        LigandPocketDDPM.generate_ligands,
        torch.Tensor.backward,
        torch.save,
    )
    assert "load_from_checkpoint" not in vars(LigandPocketDDPM)
    with implementation._installed_observers(
        implementation._initial_observations(), torch
    ):
        assert "load_from_checkpoint" in vars(LigandPocketDDPM)
        replacements = (
            cli.resolve_covapie_target_residue_atom_condition_cli_args_v1,
            cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1,
            LigandPocketDDPM.prepare_pocket,
            LigandPocketDDPM.generate_ligands,
            torch.Tensor.backward,
            torch.save,
        )
        assert all(
            original is not replacement
            for original, replacement in zip(originals, replacements)
        )
    assert "load_from_checkpoint" not in vars(LigandPocketDDPM)
    restored = (
        cli.resolve_covapie_target_residue_atom_condition_cli_args_v1,
        cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1,
        LigandPocketDDPM.prepare_pocket,
        LigandPocketDDPM.generate_ligands,
        torch.Tensor.backward,
        torch.save,
    )
    assert all(
        original is restored_value
        for original, restored_value in zip(originals, restored)
    )

    class DummyState:
        def state_dict(self) -> dict[str, object]:
            return {
                "scalar": torch.tensor(1),
                "vector": torch.tensor([1.0, 2.0]),
            }

    first_digest = implementation._state_digest(DummyState(), torch)
    second_digest = implementation._state_digest(DummyState(), torch)
    assert first_digest == second_digest
    assert len(first_digest) == 64


def test_default_checker_does_not_execute_smoke(
    response: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    import check_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1 as checker

    monkeypatch.setattr(
        checker.implementation,
        "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1",
        lambda **kwargs: response,
    )

    def forbidden_execute(**kwargs: object) -> object:
        del kwargs
        raise AssertionError("default mode executed the real smoke")

    monkeypatch.setattr(
        checker.implementation,
        "execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1",
        forbidden_execute,
    )
    monkeypatch.setattr(checker, "_emit", lambda *args: None)
    assert checker.main([]) == 0


def test_execute_api_consumed_guard_is_first_and_has_no_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("consumed guard did not run first")

    for name in (
        "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1",
        "_git_snapshot",
        "_terminal_lifecycle_evidence",
        "_file_identity",
        "_make_workspace",
        "_run_child_process",
    ):
        monkeypatch.setattr(implementation, name, forbidden)
    with pytest.raises(ValueError, match=f"^{CONSUMED_ERROR}$"):
        implementation.execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1(
            repo_root=Path("not-absolute"),
            python_executable=Path("not-absolute"),
        )


def test_execute_api_ast_guard_is_first_executable_statement() -> None:
    source = Path(implementation.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    execute = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1"
    )
    assert isinstance(execute.body[0], ast.Expr)
    assert isinstance(execute.body[0].value, ast.Constant)
    assert isinstance(execute.body[1], ast.Expr)
    assert isinstance(execute.body[1].value, ast.Call)
    assert isinstance(execute.body[1].value.func, ast.Name)
    assert execute.body[1].value.func.id == "_guard_one_time_execution_authorization_v1"


def test_private_child_entry_guard_precedes_argument_parsing() -> None:
    source = Path(implementation.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    module_main = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_module_main"
    )
    assert isinstance(module_main.body[0], ast.Expr)
    assert isinstance(module_main.body[0].value, ast.Call)
    assert isinstance(module_main.body[0].value.func, ast.Name)
    assert module_main.body[0].value.func.id == (
        "_guard_one_time_execution_authorization_v1"
    )


def test_execute_once_flag_fails_consumed_before_static_or_execute_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import check_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1 as checker

    def forbidden(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("checker performed forbidden work")

    monkeypatch.setattr(
        checker.implementation,
        "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1",
        forbidden,
    )
    monkeypatch.setattr(
        checker.implementation,
        "execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1",
        forbidden,
    )
    with pytest.raises(ValueError, match=f"^{CONSUMED_ERROR}$"):
        checker.main(["--execute-once"])


def test_static_tests_never_load_checkpoint_or_run_generate_ligands() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_attribute_calls = {
        (node.func.value.id, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    }
    assert ("torch", "load") not in forbidden_attribute_calls
    assert ("runpy", "run_path") not in forbidden_attribute_calls
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_child_main"
        for node in ast.walk(tree)
    )


def test_output_acceptance_never_claims_chemical_quality(
    valid_evidence: dict[str, object],
) -> None:
    assert valid_evidence["generated_molecule_count"] in (0, 1)
    assert valid_evidence["chemical_generation_quality_validated"] is False
    assert _validate(valid_evidence)
