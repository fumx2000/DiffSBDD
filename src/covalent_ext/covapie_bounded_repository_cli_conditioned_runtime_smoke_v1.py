"""Implement one bounded real repository CLI conditioned runtime smoke V1.

The public evaluator is static: it binds the published design and inspects the
implementation without importing Torch or executing the runtime.  Only the
explicit execution API starts the single CPU child used by the smoke.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import datetime as _datetime
import functools
import hashlib
import io
import json
import os
import random
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Callable, Iterator, Mapping, Sequence


__all__ = (
    "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1",
    "execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1",
)


_ERROR = "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_INVALID"
_VERSION = "covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1"
_EVIDENCE_VERSION = "covapie_bounded_repository_cli_conditioned_runtime_smoke_evidence_v1"
_DESIGN_COMMIT = "0206b54dd77283ad01acf0305183bd2090f81f4b"
_DESIGN_PARENT = "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
_DESIGN_SUBJECT = "add CovaPIE bounded repository CLI conditioned runtime smoke design v1"
_DESIGN_RESPONSE_SHA256 = (
    "db3ff4f7dd5be74efbcaf700c044b4bc7a9931a0520127f4a782cf07967aaeeb"
)
_CHECKPOINT_RELATIVE_PATH = "checkpoints/crossdocked_fullatom_cond.ckpt"
_CHECKPOINT_SIZE = 17_861_341
_CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
_RUNTIME_SNAPSHOT = "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
_TERMINAL_COMMIT_SUBJECT = (
    "record CovaPIE bounded repository CLI conditioned smoke terminal result v1"
)
_TIMEOUT_SECONDS = 300
_MAX_SOURCE_BYTES = 8 * 1024 * 1024
_WORKSPACE_PREFIX = "covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_"
_POST_SMOKE_MAINLINE = "audit_covapie_five_module_training_path_completion_gaps_v1"
_EXECUTION_AUTHORIZATION_CONSUMED_ERROR = (
    "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_"
    "EXECUTION_AUTHORIZATION_CONSUMED"
)
_ONE_TIME_EXECUTION_AUTHORIZATION_CONSUMED = True

_EXECUTED_SOURCE_IDENTITIES = (
    (
        "src/covalent_ext/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
        "ca192e4618aba47717cb66b96350a00fa44595d8e9bd7c3947f5368052bb5add",
        81_177,
        1_976,
        "0644",
    ),
    (
        "tests/test_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
        "380b9ec142d65907640a470554433df6bcb836d25bf8b4e95daca965cc2325ae",
        21_641,
        611,
        "0644",
    ),
    (
        "scripts/check_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
        "fc4f7e8e0e44af9230e7bb0cbbac168a24ec52ce140f160ec3ea0428686eeafc",
        4_668,
        134,
        "0644",
    ),
    (
        "docs/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_guide.md",
        "cdee2df4a2a51c43964b6a4d98e75d4f4f55c4edd5f9c859925d62cacf307ded",
        5_663,
        113,
        "0644",
    ),
)

_ONE_TIME_EXECUTION_RECORD = MappingProxyType(
    {
        "one_time_execution_authorization_consumed": True,
        "bounded_runtime_smoke_execution_count": 1,
        "bounded_runtime_smoke_passed": False,
        "automatic_retry_performed": False,
        "architecture_expansion_authorized": False,
        "command": (
            "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
            "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10",
            "-B",
            "scripts/check_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
            "--execute-once",
        ),
        "start_UTC": "2026-08-03T12:13:21.812077Z",
        "end_UTC": "2026-08-03T12:16:06.786532Z",
        "checker_returncode": 1,
        "checker_stdout_bytes": 4_850,
        "checker_stdout_sha256": (
            "7ad6b9c7313fb40a35450eabaa7dffbc1a8836e644209b681ac515ecaeccbae5"
        ),
        "checker_stderr_bytes": 0,
        "checker_stderr_sha256": (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
        "child_returncode": 1,
        "timeout": False,
        "evidence_field_count": 0,
        "evidence_bytes": 0,
        "evidence_sha256": None,
        "exact67_runtime_evidence_available": False,
        "first_failure_stage": "child_internal_stderr_gate_before_exact67_evidence",
        "warning_category": "UserWarning",
        "warning_message": (
            '"import openbabel" is deprecated, instead use '
            '"from openbabel import openbabel"'
        ),
        "checkpoint_unchanged": True,
        "git_unchanged": True,
        "training_or_parameter_update": False,
        "RL_implementation_started": False,
        "commit_created": False,
        "push_performed": False,
    }
)

_DESIGN_FILES = {
    "src/covalent_ext/covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1.py": {
        "sha256": "e38f6dc1d2c833b9f55671d25a6966c099d2eb27aac046badf16016b5aa86c3d",
        "git_blob": "54c162014b1be09c35416697aaad643cab0a9589",
    },
    "tests/test_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1.py": {
        "sha256": "757e5138f140344ce389d0c22e6d01c16834bf9fb7fae63931c7e503f9966feb",
        "git_blob": "01c87b0cd9df8637d5c8c00ab799ca57e066913a",
    },
    "scripts/check_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1.py": {
        "sha256": "6e693f67c316328bd80e7602fcd1fce1b15e41c5a48e58f52dff8c774284192b",
        "git_blob": "6b4c5bc1fcd16e59d97e2a13e021e9e49646cc59",
    },
    "docs/covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1_guide.md": {
        "sha256": "dfcd06adc34c997b7233ecb0eb206baef78cbb24175338164c5af89a7e8c5f1b",
        "git_blob": "17c9c9117112ba38951fbc99b825e492e9e9c52f",
    },
}

_IMPLEMENTATION_FILES = (
    "src/covalent_ext/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
    "tests/test_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
    "scripts/check_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py",
    "docs/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_guide.md",
)

_EXACT6_SELECTOR = {
    "chain_id": "A",
    "residue_sequence_number": 1,
    "residue_insertion_code": " ",
    "residue_name": "CYS",
    "atom_name": "SG",
    "element": "S",
}

_CHILD_ENVIRONMENT = {
    "CUDA_VISIBLE_DEVICES": "",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": ".:src:scripts",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
}

_ALLOWED_WORKSPACE_FILES = (
    "input/minimal_cys_sg.pdb",
    "output/generated.sdf",
    "evidence/runtime_smoke_evidence.json",
    "logs/stdout.bin",
    "logs/stderr.bin",
)
_ALLOWED_WORKSPACE_DIRECTORIES = ("input", "output", "evidence", "logs")

_EVIDENCE_FIELDS = (
    "evidence_schema_version",
    "caller",
    "argv",
    "environment",
    "child_returncode",
    "resolved_device",
    "cuda_available",
    "stdout_byte_count",
    "stdout_sha256",
    "stderr_byte_count",
    "stderr_sha256",
    "resolver_call_count",
    "selector",
    "conditioned_loader_call_count",
    "legacy_loader_call_count",
    "checkpoint_path",
    "map_location",
    "model_target_residue_atom_conditioning",
    "dynamics_target_residue_atom_conditioning",
    "condition_embedding_shape",
    "condition_embedding_all_zero",
    "state_key_count",
    "prepare_pocket_call_count",
    "pocket_size",
    "indicator_field_present",
    "indicator_dtype",
    "indicator_shape",
    "indicator_true_count",
    "indicator_true_atom",
    "generate_ligands_call_count",
    "n_samples",
    "pocket_ids",
    "ref_ligand",
    "timesteps",
    "selector_object_is_resolver_output",
    "ddpm_type",
    "dynamics_forward_call_count",
    "model_forward_executed",
    "real_generation_path_executed",
    "training_step_executed",
    "backward_executed",
    "optimizer_created",
    "optimizer_step_executed",
    "scheduler_step_executed",
    "all_parameter_grads_none",
    "model_state_digest_before",
    "model_state_digest_after",
    "parameter_values_modified",
    "parameter_versions_modified",
    "checkpoint_size_before",
    "checkpoint_size_after",
    "checkpoint_mtime_ns_before",
    "checkpoint_mtime_ns_after",
    "checkpoint_sha256_before",
    "checkpoint_sha256_after",
    "checkpoint_bytes_unchanged",
    "forbidden_save_api_call_count",
    "generated_molecule_count",
    "output_sdf_exists",
    "output_sdf_regular",
    "output_sdf_symlink",
    "output_sdf_size",
    "output_sdf_record_count",
    "chemical_generation_quality_validated",
    "workspace_st_dev",
    "workspace_st_ino",
    "workspace_allowed_relative_paths",
)

_IMPLEMENTATION_RESPONSE_FIELDS = (
    "bounded_runtime_smoke_implementation_version",
    "bounded_runtime_smoke_implementation_error_contract",
    "bounded_runtime_smoke_implementation_complete",
    "public_APIs",
    "public_APIs_keyword_only",
    "authorized_repository_file_scope",
    "implementation_file_identities",
    "source_design_commit_identity",
    "source_design_file_identities",
    "published_design_response_binding",
    "fresh_runtime_source_revalidation",
    "runtime_evidence_schema",
    "canonical_evidence_contract",
    "checkpoint_binding",
    "child_command_contract",
    "child_environment_contract",
    "transparent_observer_contract",
    "parameter_immutability_contract",
    "temporary_workspace_contract",
    "checker_modes",
    "default_checker_real_runtime_smoke_executed",
    "training_or_parameter_update",
    "RL_implementation_started",
    "one_time_execution_only",
    "repeat_without_new_user_authorization",
    "ready_for_one_time_bounded_runtime_smoke_execution",
    "post_smoke_mainline_priority",
    "git_precondition",
    "one_time_execution_authorization_consumed",
    "one_time_execution_record",
    "exact67_runtime_evidence_available",
    "reexecution_requires_new_explicit_user_authorization",
    "failure_establishes_model_runtime_failure",
    "failure_establishes_conditioned_plumbing_failure",
    "recommended_next_step",
    "bounded_runtime_smoke_implementation_response_sha256",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _raise_invalid(error: BaseException | None = None) -> None:
    if error is None:
        raise ValueError(_ERROR)
    raise ValueError(_ERROR) from error


def _canonical_relative_path(relative_path: str) -> PurePosixPath:
    try:
        parsed = PurePosixPath(relative_path)
        if (
            type(relative_path) is not str
            or not relative_path
            or "\x00" in relative_path
            or parsed.is_absolute()
            or ".." in parsed.parts
            or parsed.as_posix() != relative_path
            or relative_path.startswith("./")
        ):
            _raise_invalid()
        return parsed
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _read_regular_file(
    repo_root: Path,
    relative_path: str,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
    maximum_size: int | None = _MAX_SOURCE_BYTES,
) -> tuple[bytes, os.stat_result]:
    try:
        parsed = _canonical_relative_path(relative_path)
        path = repo_root.joinpath(*parsed.parts)
        before = os.lstat(path)
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or bool(before.st_mode & 0o111)
            or (maximum_size is not None and before.st_size > maximum_size)
            or (expected_size is not None and before.st_size != expected_size)
        ):
            _raise_invalid()
        payload = path.read_bytes()
        after = os.lstat(path)
        if (
            (before.st_dev, before.st_ino, before.st_mode, before.st_size)
            != (after.st_dev, after.st_ino, after.st_mode, after.st_size)
            or len(payload) != after.st_size
            or (expected_sha256 is not None and _sha256(payload) != expected_sha256)
        ):
            _raise_invalid()
        return payload, after
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _git_bytes(repo_root: Path, arguments: Sequence[str], *, timeout: int = 60) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=False,
            capture_output=True,
            timeout=timeout,
        )
        if completed.returncode != 0 or completed.stderr:
            _raise_invalid()
        return completed.stdout
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _git_text(repo_root: Path, arguments: Sequence[str], *, timeout: int = 60) -> str:
    try:
        return _git_bytes(repo_root, arguments, timeout=timeout).decode(
            "utf-8", errors="strict"
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _git_snapshot(repo_root: Path, *, include_remote: bool) -> dict[str, object]:
    try:
        branch = _git_text(repo_root, ["branch", "--show-current"]).strip()
        head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
        origin = _git_text(repo_root, ["rev-parse", "origin/main"]).strip()
        ahead_behind_text = _git_text(
            repo_root, ["rev-list", "--left-right", "--count", "origin/main...HEAD"]
        ).strip()
        match = re.fullmatch(r"([0-9]+)\s+([0-9]+)", ahead_behind_text)
        if match is None:
            _raise_invalid()
        status_payload = _git_bytes(
            repo_root,
            ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
        )
        records = [record for record in status_payload.split(b"\0") if record]
        decoded = [record.decode("utf-8", errors="strict") for record in records]
        if any(len(record) < 4 for record in decoded):
            _raise_invalid()
        untracked = sorted(record[3:] for record in decoded if record.startswith("?? "))
        tracked = sorted(record[3:] for record in decoded if not record.startswith("?? "))
        staged = sorted(
            record[3:]
            for record in decoded
            if not record.startswith("?? ") and record[0] != " "
        )
        ordinary_untracked = []
        for relative_path in untracked:
            parsed = _canonical_relative_path(relative_path)
            metadata = os.lstat(repo_root.joinpath(*parsed.parts))
            if stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
                ordinary_untracked.append(relative_path)
        real_remote_main: str | None = None
        if include_remote:
            remote = _git_text(
                repo_root, ["ls-remote", "origin", "refs/heads/main"], timeout=60
            )
            remote_match = re.fullmatch(
                r"([0-9a-f]{40})\trefs/heads/main\n", remote
            )
            if remote_match is None:
                _raise_invalid()
            real_remote_main = remote_match.group(1)
        return {
            "branch": branch,
            "HEAD": head,
            "origin_main": origin,
            "real_remote_main": real_remote_main,
            "ahead": int(match.group(2)),
            "behind": int(match.group(1)),
            "tracked_modifications": tracked,
            "staged_index": staged,
            "ordinary_untracked": ordinary_untracked,
            "ordinary_untracked_count": len(ordinary_untracked),
            "status_sha256": _sha256(status_payload),
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _git_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=repo_root,
            check=False,
            capture_output=True,
            timeout=60,
        )
        if completed.returncode not in (0, 1) or completed.stdout or completed.stderr:
            _raise_invalid()
        return completed.returncode == 0
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _terminal_lifecycle_from_facts(facts: Mapping[str, object]) -> dict[str, object]:
    try:
        if type(facts) is not dict:
            _raise_invalid()
        head = facts.get("HEAD")
        origin = facts.get("origin_main")
        remote = facts.get("real_remote_main")
        ahead = facts.get("ahead")
        behind = facts.get("behind")
        tracked = facts.get("tracked_modifications")
        staged = facts.get("staged_index")
        untracked = facts.get("ordinary_untracked")
        candidates = facts.get("terminal_candidates")
        if (
            facts.get("branch") != "main"
            or type(head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", head) is None
            or type(origin) is not str
            or re.fullmatch(r"[0-9a-f]{40}", origin) is None
            or remote is not None
            and (
                type(remote) is not str
                or re.fullmatch(r"[0-9a-f]{40}", remote) is None
                or remote != origin
            )
            or type(ahead) is not int
            or ahead < 0
            or type(behind) is not int
            or behind < 0
            or type(tracked) is not list
            or type(staged) is not list
            or type(untracked) is not list
            or untracked != sorted(untracked)
            or facts.get("ordinary_untracked_count") != len(untracked)
            or type(candidates) is not list
        ):
            _raise_invalid()

        exact_paths = sorted(_IMPLEMENTATION_FILES)
        if not candidates:
            if (
                head != _DESIGN_COMMIT
                or origin != _DESIGN_COMMIT
                or ahead != 0
                or behind != 0
                or tracked != []
                or staged != []
                or untracked != exact_paths
            ):
                _raise_invalid()
            return {
                "profile": "terminal_precommit_candidate",
                "terminal_commit": None,
                "terminal_subject": _TERMINAL_COMMIT_SUBJECT,
                "terminal_parent": _DESIGN_COMMIT,
                "terminal_committed": False,
                "terminal_published": False,
                "ready_for_terminalized_implementation_commit_review": True,
                "current_HEAD": head,
                "current_origin_main": origin,
                "ahead": ahead,
                "behind": behind,
                "exact_path_scope": list(_IMPLEMENTATION_FILES),
                "exact_path_scope_count": len(_IMPLEMENTATION_FILES),
                "terminal_candidate_count": 0,
                "terminal_commit_body_empty": None,
                "terminal_commit_single_parent": None,
                "terminal_commit_exact_statuses_bound": False,
                "terminal_commit_modes_bound": False,
                "terminal_commit_blobs_bound": False,
                "terminal_live_bytes_match_commit": False,
                "terminal_files_ordinary_regular": True,
                "terminal_files_non_symlink": True,
                "terminal_files_non_executable": True,
                "terminal_self_worktree_clean": True,
                "terminal_self_staged_clean": True,
                "one_time_execution_authorization_consumed": True,
            }

        if len(candidates) != 1 or type(candidates[0]) is not dict:
            _raise_invalid()
        candidate = candidates[0]
        commit = candidate.get("commit")
        if (
            type(commit) is not str
            or re.fullmatch(r"[0-9a-f]{40}", commit) is None
            or commit == _DESIGN_COMMIT
            or candidate.get("subject") != _TERMINAL_COMMIT_SUBJECT
            or candidate.get("parent") != _DESIGN_COMMIT
            or candidate.get("body_empty") is not True
            or candidate.get("single_parent") is not True
            or candidate.get("path_scope") != exact_paths
            or candidate.get("path_statuses")
            != {path: "A" for path in exact_paths}
            or candidate.get("path_modes")
            != {path: "100644" for path in exact_paths}
            or candidate.get("commit_blobs_bound") is not True
            or candidate.get("live_bytes_match_commit") is not True
            or candidate.get("files_ordinary_regular") is not True
            or candidate.get("files_non_symlink") is not True
            or candidate.get("files_non_executable") is not True
            or candidate.get("worktree_drift_paths") != []
            or candidate.get("staged_drift_paths") != []
            or candidate.get("ancestor_of_HEAD") is not True
        ):
            _raise_invalid()

        if (
            head == commit
            and origin == _DESIGN_COMMIT
            and ahead == 1
            and behind == 0
            and candidate.get("ancestor_of_origin_main") is False
        ):
            if tracked != [] or staged != [] or untracked != []:
                _raise_invalid()
            profile = "terminal_committed_unpushed"
            published = False
        elif candidate.get("ancestor_of_origin_main") is True:
            profile = "terminal_published_successor"
            published = True
        else:
            _raise_invalid()

        return {
            "profile": profile,
            "terminal_commit": commit,
            "terminal_subject": _TERMINAL_COMMIT_SUBJECT,
            "terminal_parent": _DESIGN_COMMIT,
            "terminal_committed": True,
            "terminal_published": published,
            "ready_for_terminalized_implementation_commit_review": False,
            "current_HEAD": head,
            "current_origin_main": origin,
            "ahead": ahead,
            "behind": behind,
            "exact_path_scope": list(_IMPLEMENTATION_FILES),
            "exact_path_scope_count": len(_IMPLEMENTATION_FILES),
            "terminal_candidate_count": 1,
            "terminal_commit_body_empty": True,
            "terminal_commit_single_parent": True,
            "terminal_commit_exact_statuses_bound": True,
            "terminal_commit_modes_bound": True,
            "terminal_commit_blobs_bound": True,
            "terminal_live_bytes_match_commit": True,
            "terminal_files_ordinary_regular": True,
            "terminal_files_non_symlink": True,
            "terminal_files_non_executable": True,
            "terminal_self_worktree_clean": True,
            "terminal_self_staged_clean": True,
            "one_time_execution_authorization_consumed": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _terminal_commit_facts(
    repo_root: Path,
    commit: str,
    snapshot: Mapping[str, object],
) -> dict[str, object]:
    try:
        raw_commit = _git_bytes(repo_root, ["cat-file", "commit", commit])
        headers, message = raw_commit.split(b"\n\n", 1)
        header_lines = headers.decode("utf-8", errors="strict").splitlines()
        parents = [line[7:] for line in header_lines if line.startswith("parent ")]
        subject = _git_text(repo_root, ["show", "-s", "--format=%s", commit]).strip()
        parent = parents[0] if len(parents) == 1 else None
        diff_rows: list[str] = []
        if parent is not None:
            diff_rows = _git_text(
                repo_root,
                ["diff-tree", "--no-commit-id", "--name-status", "-r", parent, commit],
            ).splitlines()
        path_statuses: dict[str, str] = {}
        for row in diff_rows:
            match = re.fullmatch(r"([A-Z])\t(.+)", row)
            if match is None:
                _raise_invalid()
            path_statuses[match.group(2)] = match.group(1)

        path_modes: dict[str, str] = {}
        commit_blobs: dict[str, str] = {}
        index_blobs: dict[str, str] = {}
        live_blobs: dict[str, str] = {}
        ordinary = True
        non_symlink = True
        non_executable = True
        for relative_path in _IMPLEMENTATION_FILES:
            tree_row = _git_text(repo_root, ["ls-tree", commit, "--", relative_path])
            tree_match = re.fullmatch(
                rf"([0-9]{{6}}) blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n",
                tree_row,
            )
            if tree_match is None:
                _raise_invalid()
            path_modes[relative_path] = tree_match.group(1)
            commit_blobs[relative_path] = tree_match.group(2)
            index_row = _git_text(repo_root, ["ls-files", "--stage", "--", relative_path])
            index_match = re.fullmatch(
                rf"100644 ([0-9a-f]{{40}}) 0\t{re.escape(relative_path)}\n",
                index_row,
            )
            if index_match is None:
                _raise_invalid()
            index_blobs[relative_path] = index_match.group(1)
            live_blobs[relative_path] = _git_text(
                repo_root, ["hash-object", "--no-filters", "--", relative_path]
            ).strip()
            parsed = _canonical_relative_path(relative_path)
            metadata = os.lstat(repo_root.joinpath(*parsed.parts))
            ordinary = ordinary and stat.S_ISREG(metadata.st_mode)
            non_symlink = non_symlink and not stat.S_ISLNK(metadata.st_mode)
            non_executable = non_executable and not bool(metadata.st_mode & 0o111)

        exact_set = set(_IMPLEMENTATION_FILES)
        tracked_drift = sorted(
            path for path in snapshot["tracked_modifications"] if path in exact_set
        )
        staged_drift = sorted(
            path for path in snapshot["staged_index"] if path in exact_set
        )
        untracked_drift = sorted(
            path for path in snapshot["ordinary_untracked"] if path in exact_set
        )
        return {
            "commit": commit,
            "subject": subject,
            "parent": parent,
            "body_empty": message.decode("utf-8", errors="strict")
            == f"{subject}\n",
            "single_parent": len(parents) == 1,
            "path_scope": sorted(path_statuses),
            "path_statuses": {path: path_statuses[path] for path in sorted(path_statuses)},
            "path_modes": {path: path_modes[path] for path in sorted(path_modes)},
            "commit_blobs_bound": commit_blobs == index_blobs,
            "live_bytes_match_commit": commit_blobs == live_blobs,
            "files_ordinary_regular": ordinary,
            "files_non_symlink": non_symlink,
            "files_non_executable": non_executable,
            "worktree_drift_paths": sorted(set(tracked_drift + untracked_drift)),
            "staged_drift_paths": staged_drift,
            "ancestor_of_HEAD": _git_is_ancestor(repo_root, commit, snapshot["HEAD"]),
            "ancestor_of_origin_main": _git_is_ancestor(
                repo_root, commit, snapshot["origin_main"]
            ),
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _terminal_lifecycle_evidence(
    repo_root: Path,
    *,
    include_remote: bool = False,
) -> dict[str, object]:
    try:
        snapshot = _git_snapshot(repo_root, include_remote=include_remote)
        candidate_output = _git_text(
            repo_root,
            [
                "log",
                "--all",
                "--format=%H",
                "--fixed-strings",
                f"--grep={_TERMINAL_COMMIT_SUBJECT}",
            ],
        )
        candidate_hashes = sorted(set(candidate_output.splitlines()))
        candidates = []
        for commit in candidate_hashes:
            subject = _git_text(
                repo_root, ["show", "-s", "--format=%s", commit]
            ).strip()
            if subject == _TERMINAL_COMMIT_SUBJECT:
                candidates.append(_terminal_commit_facts(repo_root, commit, snapshot))
        return _terminal_lifecycle_from_facts(
            {**snapshot, "terminal_candidates": candidates}
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _validate_terminal_lifecycle_evidence(evidence: Mapping[str, object]) -> bool:
    try:
        if type(evidence) is not dict:
            _raise_invalid()
        profile = evidence.get("profile")
        common = (
            evidence.get("terminal_subject") == _TERMINAL_COMMIT_SUBJECT
            and evidence.get("terminal_parent") == _DESIGN_COMMIT
            and evidence.get("exact_path_scope") == list(_IMPLEMENTATION_FILES)
            and evidence.get("exact_path_scope_count") == 4
            and evidence.get("one_time_execution_authorization_consumed") is True
            and evidence.get("terminal_files_ordinary_regular") is True
            and evidence.get("terminal_files_non_symlink") is True
            and evidence.get("terminal_files_non_executable") is True
            and evidence.get("terminal_self_worktree_clean") is True
            and evidence.get("terminal_self_staged_clean") is True
        )
        if not common:
            _raise_invalid()
        if profile == "terminal_precommit_candidate":
            valid = (
                evidence.get("terminal_commit") is None
                and evidence.get("terminal_committed") is False
                and evidence.get("terminal_published") is False
                and evidence.get("ready_for_terminalized_implementation_commit_review")
                is True
                and evidence.get("current_HEAD") == _DESIGN_COMMIT
                and evidence.get("current_origin_main") == _DESIGN_COMMIT
                and evidence.get("ahead") == 0
                and evidence.get("behind") == 0
                and evidence.get("terminal_candidate_count") == 0
            )
        elif profile in (
            "terminal_committed_unpushed",
            "terminal_published_successor",
        ):
            valid = (
                type(evidence.get("terminal_commit")) is str
                and re.fullmatch(
                    r"[0-9a-f]{40}", str(evidence.get("terminal_commit"))
                )
                is not None
                and evidence.get("terminal_committed") is True
                and evidence.get("terminal_published")
                is (profile == "terminal_published_successor")
                and evidence.get("ready_for_terminalized_implementation_commit_review")
                is False
                and evidence.get("terminal_candidate_count") == 1
                and evidence.get("terminal_commit_body_empty") is True
                and evidence.get("terminal_commit_single_parent") is True
                and evidence.get("terminal_commit_exact_statuses_bound") is True
                and evidence.get("terminal_commit_modes_bound") is True
                and evidence.get("terminal_commit_blobs_bound") is True
                and evidence.get("terminal_live_bytes_match_commit") is True
            )
        else:
            valid = False
        if not valid:
            _raise_invalid()
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _file_identity(path: Path) -> dict[str, object]:
    try:
        before = os.lstat(path)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            _raise_invalid()
        payload = path.read_bytes()
        after = os.lstat(path)
        if (
            (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns)
            or len(payload) != after.st_size
        ):
            _raise_invalid()
        return {
            "st_dev": after.st_dev,
            "st_ino": after.st_ino,
            "st_mode": after.st_mode,
            "mode_octal": format(stat.S_IMODE(after.st_mode), "04o"),
            "size": after.st_size,
            "mtime_ns": after.st_mtime_ns,
            "sha256": _sha256(payload),
            "ordinary_regular": True,
            "symlink": False,
            "executable": bool(after.st_mode & 0o111),
            "mode_stable_during_read": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _validate_checkpoint_identity(identity: Mapping[str, object]) -> bool:
    try:
        if (
            type(identity) is not dict
            or identity.get("size") != _CHECKPOINT_SIZE
            or identity.get("sha256") != _CHECKPOINT_SHA256
            or identity.get("ordinary_regular") is not True
            or identity.get("symlink") is not False
            or identity.get("executable") is not False
            or identity.get("mode_stable_during_read") is not True
        ):
            _raise_invalid()
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _source_identity(repo_root: Path, relative_path: str) -> dict[str, object]:
    payload, metadata = _read_regular_file(repo_root, relative_path)
    if stat.S_IMODE(metadata.st_mode) != 0o644:
        _raise_invalid()
    return {
        "sha256": _sha256(payload),
        "size": len(payload),
        "lines": len(payload.splitlines()),
        "mode": "100644",
        "ordinary_regular": True,
        "symlink": False,
        "executable": False,
    }


def _published_design_response_binding(
    response: Mapping[str, object],
    *,
    design_commit_is_ancestor_of_HEAD: bool,
    design_commit_is_ancestor_of_origin_main: bool,
) -> dict[str, object]:
    try:
        if type(response) is not dict or len(response) != 50:
            _raise_invalid()
        current_sha256 = response.get(
            "bounded_runtime_smoke_design_response_sha256"
        )
        unsigned = {
            field: value
            for field, value in response.items()
            if field != "bounded_runtime_smoke_design_response_sha256"
        }
        runtime = response.get("runtime_source_bindings")
        subprocess_contract = response.get("subprocess_execution_contract")
        if (
            type(current_sha256) is not str
            or current_sha256 != _sha256(_canonical_json_bytes(unsigned))
            or response.get("bounded_runtime_smoke_design_complete") is not True
            or response.get("bounded_runtime_smoke_implementation_deferred") is not False
            or response.get(
                "fresh_runtime_source_revalidation_required_before_implementation"
            )
            is not True
            or response.get("ready_for_bounded_runtime_smoke_implementation") is not True
            or response.get("recommended_next_step")
            != "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
            or type(runtime) is not dict
            or runtime.get("snapshot_commit") != _RUNTIME_SNAPSHOT
            or runtime.get("snapshot_is_ancestor_of_HEAD") is not True
            or runtime.get("snapshot_is_ancestor_of_origin_main") is not True
            or runtime.get("source_count") != 3
            or runtime.get("all_live_bytes_match_snapshot") is not True
            or type(runtime.get("current_HEAD")) is not str
            or re.fullmatch(r"[0-9a-f]{40}", runtime.get("current_HEAD", ""))
            is None
            or type(runtime.get("current_origin_main")) is not str
            or re.fullmatch(
                r"[0-9a-f]{40}", runtime.get("current_origin_main", "")
            )
            is None
            or type(subprocess_contract) is not dict
            or subprocess_contract.get("one_time_execution_only") is not True
            or subprocess_contract.get("repeat_without_new_user_authorization")
            is not False
            or response.get("runtime_evidence_schema", {}).get("required_fields")
            != list(_EVIDENCE_FIELDS)
            or design_commit_is_ancestor_of_HEAD is not True
            or design_commit_is_ancestor_of_origin_main is not True
        ):
            _raise_invalid()
        return {
            "published_snapshot_response_sha256": _DESIGN_RESPONSE_SHA256,
            "current_response_sha256": current_sha256,
            "current_response_exact_field_count": len(response),
            "design_commit": _DESIGN_COMMIT,
            "design_commit_is_ancestor_of_HEAD": True,
            "design_commit_is_ancestor_of_origin_main": True,
            "current_HEAD": runtime["current_HEAD"],
            "current_origin_main": runtime["current_origin_main"],
            "bounded_runtime_smoke_design_complete": True,
            "bounded_runtime_smoke_implementation_deferred": False,
            "fresh_runtime_source_revalidation_required_before_implementation": True,
            "ready_for_bounded_runtime_smoke_implementation": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _bind_design(repo_root: Path) -> tuple[dict[str, object], dict[str, object]]:
    try:
        commit = _git_text(
            repo_root, ["show", "-s", "--format=%H%n%P%n%s", _DESIGN_COMMIT]
        ).splitlines()
        if commit != [_DESIGN_COMMIT, _DESIGN_PARENT, _DESIGN_SUBJECT]:
            _raise_invalid()
        identities: dict[str, object] = {}
        for relative_path, expected in _DESIGN_FILES.items():
            row = _git_text(repo_root, ["ls-tree", _DESIGN_COMMIT, "--", relative_path])
            match = re.fullmatch(
                rf"100644 blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n", row
            )
            payload, metadata = _read_regular_file(
                repo_root, relative_path, expected_sha256=expected["sha256"]
            )
            if (
                match is None
                or match.group(1) != expected["git_blob"]
                or stat.S_IMODE(metadata.st_mode) != 0o644
            ):
                _raise_invalid()
            identities[relative_path] = {
                "sha256": _sha256(payload),
                "git_blob": match.group(1),
                "git_mode": "100644",
                "ordinary_regular": True,
                "symlink": False,
                "executable": False,
            }

        from covalent_ext import (
            covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1 as design,
        )

        response = design.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1(
            repo_root=repo_root
        )
        ancestor_of_head = _git_is_ancestor(
            repo_root, _DESIGN_COMMIT, _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
        )
        ancestor_of_origin = _git_is_ancestor(
            repo_root,
            _DESIGN_COMMIT,
            _git_text(repo_root, ["rev-parse", "origin/main"]).strip(),
        )
        if (
            type(response) is not dict
            or len(response) != 50
            or response.get("bounded_runtime_smoke_design_complete") is not True
            or response.get("bounded_runtime_smoke_implementation_deferred") is not False
            or response.get("fresh_runtime_source_revalidation_required_before_implementation")
            is not True
            or response.get("ready_for_bounded_runtime_smoke_implementation") is not True
            or response.get("recommended_next_step")
            != "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
            or response.get("subprocess_execution_contract", {}).get(
                "one_time_execution_only"
            )
            is not True
            or response.get("subprocess_execution_contract", {}).get(
                "repeat_without_new_user_authorization"
            )
            is not False
            or response.get("runtime_evidence_schema", {}).get("required_fields")
            != list(_EVIDENCE_FIELDS)
            or not ancestor_of_head
            or not ancestor_of_origin
        ):
            _raise_invalid()
        _published_design_response_binding(
            response,
            design_commit_is_ancestor_of_HEAD=ancestor_of_head,
            design_commit_is_ancestor_of_origin_main=ancestor_of_origin,
        )
        return response, {
            "commit": _DESIGN_COMMIT,
            "parent": _DESIGN_PARENT,
            "subject": _DESIGN_SUBJECT,
            "exact_path_count": 4,
            "ancestor_of_HEAD": ancestor_of_head,
            "ancestor_of_origin_main": ancestor_of_origin,
            "files": identities,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _implementation_ast_contract(repo_root: Path) -> dict[str, object]:
    try:
        payloads: dict[str, bytes] = {}
        identities: dict[str, object] = {}
        for relative_path in _IMPLEMENTATION_FILES:
            payload, _ = _read_regular_file(repo_root, relative_path)
            payloads[relative_path] = payload
            identities[relative_path] = _source_identity(repo_root, relative_path)

        module_path, test_path, checker_path, guide_path = _IMPLEMENTATION_FILES
        module_tree = ast.parse(payloads[module_path].decode("utf-8", errors="strict"))
        checker_tree = ast.parse(payloads[checker_path].decode("utf-8", errors="strict"))
        top_imports = {
            alias.name.split(".")[0]
            for node in module_tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in module_tree.body
            if isinstance(node, ast.ImportFrom)
        }
        assignments = {
            target.id: node.value
            for node in module_tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        exports = ast.literal_eval(assignments["__all__"])
        functions = {
            node.name: node
            for node in module_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        expected_exports = __all__
        if exports != expected_exports or "torch" in top_imports:
            _raise_invalid()
        expected_kwonly = {
            expected_exports[0]: ("repo_root",),
            expected_exports[1]: ("repo_root", "python_executable"),
        }
        for name, keyword_names in expected_kwonly.items():
            node = functions.get(name)
            if (
                not isinstance(node, ast.FunctionDef)
                or node.args.posonlyargs
                or node.args.args
                or tuple(argument.arg for argument in node.args.kwonlyargs)
                != keyword_names
            ):
                _raise_invalid()
        calls = {
            node.func.attr
            for node in ast.walk(module_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        string_literals = {
            node.value
            for node in ast.walk(module_tree)
            if isinstance(node, ast.Constant) and type(node.value) is str
        }
        checker_strings = {
            node.value
            for node in ast.walk(checker_tree)
            if isinstance(node, ast.Constant) and type(node.value) is str
        }
        if (
            "run_path" not in calls
            or "register_forward_hook" not in calls
            or "--child" not in string_literals
            or "--execute-once" not in checker_strings
            or b"does not establish training readiness" not in payloads[guide_path]
            or b"test_default_checker_does_not_execute_smoke" not in payloads[test_path]
        ):
            _raise_invalid()
        return {
            "identities": identities,
            "silent_import_required": True,
            "top_level_torch_imported": False,
            "public_exports": list(expected_exports),
            "public_APIs_keyword_only": True,
            "child_private_entry_present": True,
            "runpy_generate_ligands_present": True,
            "dynamics_forward_hook_present": True,
            "checker_execute_once_gate_present": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _executed_source_identity_mapping() -> dict[str, dict[str, object]]:
    return {
        path: {
            "sha256": sha256,
            "size": size,
            "lines": lines,
            "mode": mode,
        }
        for path, sha256, size, lines, mode in _EXECUTED_SOURCE_IDENTITIES
    }


def _materialize_one_time_execution_record(
    current_terminalized_source_identities: Mapping[str, object],
) -> dict[str, object]:
    try:
        if (
            type(current_terminalized_source_identities) is not dict
            or set(current_terminalized_source_identities) != set(_IMPLEMENTATION_FILES)
        ):
            _raise_invalid()
        frozen = _ONE_TIME_EXECUTION_RECORD
        return {
            "one_time_execution_authorization_consumed": frozen[
                "one_time_execution_authorization_consumed"
            ],
            "bounded_runtime_smoke_execution_count": frozen[
                "bounded_runtime_smoke_execution_count"
            ],
            "bounded_runtime_smoke_passed": frozen[
                "bounded_runtime_smoke_passed"
            ],
            "automatic_retry_performed": frozen["automatic_retry_performed"],
            "architecture_expansion_authorized": frozen[
                "architecture_expansion_authorized"
            ],
            "command": list(frozen["command"]),
            "start_UTC": frozen["start_UTC"],
            "end_UTC": frozen["end_UTC"],
            "checker": {
                "returncode": frozen["checker_returncode"],
                "stdout_bytes": frozen["checker_stdout_bytes"],
                "stdout_sha256": frozen["checker_stdout_sha256"],
                "stderr_bytes": frozen["checker_stderr_bytes"],
                "stderr_sha256": frozen["checker_stderr_sha256"],
            },
            "child": {
                "returncode": frozen["child_returncode"],
                "timeout": frozen["timeout"],
            },
            "Exact67_evidence": {
                "field_count": frozen["evidence_field_count"],
                "bytes": frozen["evidence_bytes"],
                "sha256": frozen["evidence_sha256"],
                "available": frozen["exact67_runtime_evidence_available"],
            },
            "failure": {
                "first_failure_stage": frozen["first_failure_stage"],
                "observed_warning": {
                    "category": frozen["warning_category"],
                    "message": frozen["warning_message"],
                },
                "observation_boundary": (
                    "child_import_stage_openbabel_related_deprecation_warning"
                ),
                "direct_generate_ligands_source_line_attribution_proven": False,
                "strict_stderr_gate_triggered": True,
            },
            "executed_source_identities": _executed_source_identity_mapping(),
            "current_terminalized_source_identities": {
                path: dict(identity)
                for path, identity in current_terminalized_source_identities.items()
            },
            "safety": {
                "checkpoint_unchanged": frozen["checkpoint_unchanged"],
                "git_unchanged": frozen["git_unchanged"],
                "workspace": {
                    "st_dev": 66_307,
                    "st_ino": 7_380_511_365,
                    "inode_guard_matched": True,
                    "removed": True,
                    "exists_after": False,
                    "competitor_path_deleted": False,
                },
                "checkpoint_identity": {
                    "st_dev": 49,
                    "st_ino": 195_679_527_872,
                    "st_mode": 33_188,
                    "mode_octal": "0644",
                    "size": _CHECKPOINT_SIZE,
                    "mtime_ns": 1_785_552_510_663_618_359,
                    "sha256": _CHECKPOINT_SHA256,
                },
                "training_or_parameter_update": frozen[
                    "training_or_parameter_update"
                ],
                "RL_implementation_started": frozen["RL_implementation_started"],
                "commit_created": frozen["commit_created"],
                "push_performed": frozen["push_performed"],
            },
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _validate_implementation_response(response: Mapping[str, Any]) -> bool:
    try:
        if (
            type(response) is not dict
            or tuple(response) != _IMPLEMENTATION_RESPONSE_FIELDS
            or len(response) != len(_IMPLEMENTATION_RESPONSE_FIELDS)
        ):
            _raise_invalid()
        unsigned = {field: response[field] for field in _IMPLEMENTATION_RESPONSE_FIELDS[:-1]}
        if response[_IMPLEMENTATION_RESPONSE_FIELDS[-1]] != _sha256(
            _canonical_json_bytes(unsigned)
        ):
            _raise_invalid()
        evidence = response["runtime_evidence_schema"]
        git_state = response["git_precondition"]
        runtime = response["fresh_runtime_source_revalidation"]
        execution_record = response["one_time_execution_record"]
        design_binding = response["published_design_response_binding"]
        if (
            response["bounded_runtime_smoke_implementation_version"] != _VERSION
            or response["bounded_runtime_smoke_implementation_error_contract"] != _ERROR
            or response["bounded_runtime_smoke_implementation_complete"] is not True
            or response["public_APIs"] != list(__all__)
            or response["public_APIs_keyword_only"] is not True
            or response["authorized_repository_file_scope"] != list(_IMPLEMENTATION_FILES)
            or response["source_design_commit_identity"]["commit"] != _DESIGN_COMMIT
            or design_binding.get("published_snapshot_response_sha256")
            != _DESIGN_RESPONSE_SHA256
            or design_binding.get("current_response_exact_field_count") != 50
            or type(design_binding.get("current_response_sha256")) is not str
            or re.fullmatch(
                r"[0-9a-f]{64}", design_binding.get("current_response_sha256", "")
            )
            is None
            or design_binding.get("design_commit") != _DESIGN_COMMIT
            or design_binding.get("design_commit_is_ancestor_of_HEAD") is not True
            or design_binding.get("design_commit_is_ancestor_of_origin_main")
            is not True
            or design_binding.get("bounded_runtime_smoke_design_complete") is not True
            or design_binding.get("bounded_runtime_smoke_implementation_deferred")
            is not False
            or design_binding.get(
                "fresh_runtime_source_revalidation_required_before_implementation"
            )
            is not True
            or design_binding.get("ready_for_bounded_runtime_smoke_implementation")
            is not True
            or design_binding.get("current_HEAD") != runtime.get("current_HEAD")
            or design_binding.get("current_origin_main")
            != runtime.get("current_origin_main")
            or git_state.get("current_HEAD") != runtime.get("current_HEAD")
            or git_state.get("current_origin_main")
            != runtime.get("current_origin_main")
            or runtime.get("snapshot_commit") != _RUNTIME_SNAPSHOT
            or runtime.get("all_live_bytes_match_snapshot") is not True
            or runtime.get("source_count") != 3
            or evidence.get("required_fields") != list(_EVIDENCE_FIELDS)
            or evidence.get("required_field_count") != 67
            or response["default_checker_real_runtime_smoke_executed"] is not False
            or response["training_or_parameter_update"] is not False
            or response["RL_implementation_started"] is not False
            or response["one_time_execution_only"] is not True
            or response["repeat_without_new_user_authorization"] is not False
            or response["ready_for_one_time_bounded_runtime_smoke_execution"] is not False
            or response["post_smoke_mainline_priority"] != _POST_SMOKE_MAINLINE
            or response["one_time_execution_authorization_consumed"] is not True
            or type(execution_record) is not dict
            or execution_record
            != _materialize_one_time_execution_record(
                response["implementation_file_identities"]
            )
            or response["exact67_runtime_evidence_available"] is not False
            or response["reexecution_requires_new_explicit_user_authorization"]
            is not True
            or response["failure_establishes_model_runtime_failure"] is not False
            or response["failure_establishes_conditioned_plumbing_failure"]
            is not False
            or response["recommended_next_step"] != _POST_SMOKE_MAINLINE
            or not _validate_terminal_lifecycle_evidence(git_state)
        ):
            _raise_invalid()
        _canonical_json_bytes(response)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Statically validate the implementation without executing the smoke."""

    try:
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_absolute()
            or not repo_root.is_dir()
            or repo_root.is_symlink()
        ):
            _raise_invalid()
        design_response, design_identity = _bind_design(repo_root)
        ast_contract = _implementation_ast_contract(repo_root)
        git_state = _terminal_lifecycle_evidence(repo_root)
        _validate_terminal_lifecycle_evidence(git_state)
        checkpoint = _file_identity(repo_root / _CHECKPOINT_RELATIVE_PATH)
        _validate_checkpoint_identity(checkpoint)
        runtime_sources = design_response["runtime_source_bindings"]
        design_binding = _published_design_response_binding(
            design_response,
            design_commit_is_ancestor_of_HEAD=design_identity["ancestor_of_HEAD"],
            design_commit_is_ancestor_of_origin_main=design_identity[
                "ancestor_of_origin_main"
            ],
        )
        execution_record = _materialize_one_time_execution_record(
            ast_contract["identities"]
        )
        values: dict[str, object] = {
            "bounded_runtime_smoke_implementation_version": _VERSION,
            "bounded_runtime_smoke_implementation_error_contract": _ERROR,
            "bounded_runtime_smoke_implementation_complete": True,
            "public_APIs": list(__all__),
            "public_APIs_keyword_only": ast_contract["public_APIs_keyword_only"],
            "authorized_repository_file_scope": list(_IMPLEMENTATION_FILES),
            "implementation_file_identities": ast_contract["identities"],
            "source_design_commit_identity": {
                key: design_identity[key]
                for key in (
                    "commit",
                    "parent",
                    "subject",
                    "exact_path_count",
                    "ancestor_of_HEAD",
                    "ancestor_of_origin_main",
                )
            },
            "source_design_file_identities": design_identity["files"],
            "published_design_response_binding": design_binding,
            "fresh_runtime_source_revalidation": runtime_sources,
            "runtime_evidence_schema": design_response["runtime_evidence_schema"],
            "canonical_evidence_contract": {
                "sort_keys": True,
                "ensure_ascii": True,
                "allow_nan": False,
                "separators": [",", ":"],
                "terminal_newline": False,
            },
            "checkpoint_binding": {
                "path": _CHECKPOINT_RELATIVE_PATH,
                "size": checkpoint["size"],
                "sha256": checkpoint["sha256"],
                "ordinary_regular": checkpoint["ordinary_regular"],
                "symlink": checkpoint["symlink"],
                "executable": checkpoint["executable"],
                "deserialized_by_static_evaluator": False,
            },
            "child_command_contract": {
                "private_module_entry": (
                    "covalent_ext.covapie_bounded_repository_cli_conditioned_runtime_smoke_v1"
                ),
                "private_flag": "--child",
                "working_directory": "repository_root",
                "timeout_seconds": _TIMEOUT_SECONDS,
                "runpy_path": "generate_ligands.py",
                "runpy_run_name": "__main__",
                "single_child": True,
            },
            "child_environment_contract": dict(_CHILD_ENVIRONMENT),
            "transparent_observer_contract": {
                "required_target_count": 5,
                "arguments_modified": False,
                "return_values_modified": False,
                "model_replaced": False,
                "sampling_mocked": False,
                "PDB_mocked": False,
                "SDF_mocked": False,
                "forward_hook_target": "model.ddpm.dynamics",
                "forward_hook_API": "register_forward_hook",
                "expected_forward_count": 2,
            },
            "parameter_immutability_contract": design_response[
                "parameter_immutability_contract"
            ],
            "temporary_workspace_contract": design_response[
                "temporary_workspace_contract"
            ],
            "checker_modes": {
                "default": "static_implementation_only",
                "explicit_flag_recognized": "--execute-once",
                "explicit_result": _EXECUTION_AUTHORIZATION_CONSUMED_ERROR,
                "mutually_exclusive": True,
                "default_repeatable": True,
                "explicit_repeat_without_new_authorization": False,
            },
            "default_checker_real_runtime_smoke_executed": False,
            "training_or_parameter_update": False,
            "RL_implementation_started": False,
            "one_time_execution_only": True,
            "repeat_without_new_user_authorization": False,
            "ready_for_one_time_bounded_runtime_smoke_execution": False,
            "post_smoke_mainline_priority": _POST_SMOKE_MAINLINE,
            "git_precondition": git_state,
            "one_time_execution_authorization_consumed": True,
            "one_time_execution_record": execution_record,
            "exact67_runtime_evidence_available": False,
            "reexecution_requires_new_explicit_user_authorization": True,
            "failure_establishes_model_runtime_failure": False,
            "failure_establishes_conditioned_plumbing_failure": False,
            "recommended_next_step": _POST_SMOKE_MAINLINE,
        }
        response = {
            field: values[field]
            for field in _IMPLEMENTATION_RESPONSE_FIELDS[:-1]
        }
        response[_IMPLEMENTATION_RESPONSE_FIELDS[-1]] = _sha256(
            _canonical_json_bytes(response)
        )
        _validate_implementation_response(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _expected_cli_argv(workspace: Path) -> list[str]:
    return [
        "generate_ligands.py",
        _CHECKPOINT_RELATIVE_PATH,
        "--pdbfile",
        str(workspace / "input" / "minimal_cys_sg.pdb"),
        "--resi_list",
        "A:1",
        "--outfile",
        str(workspace / "output" / "generated.sdf"),
        "--n_samples",
        "1",
        "--batch_size",
        "1",
        "--num_nodes_lig",
        "4",
        "--timesteps",
        "1",
        "--target_residue_atom_conditioning",
        "--target_chain_id",
        "A",
        "--target_residue_sequence_number",
        "1",
    ]


def _child_command(repo_root: Path, python_executable: Path, workspace: Path) -> list[str]:
    return [
        str(python_executable),
        "-B",
        "-m",
        "covalent_ext.covapie_bounded_repository_cli_conditioned_runtime_smoke_v1",
        "--child",
        "--repo-root",
        str(repo_root),
        "--workspace",
        str(workspace),
    ]


def _validate_runtime_evidence(
    *,
    evidence: Mapping[str, Any],
    required_fields: Sequence[str],
    expected_argv: Sequence[str],
    expected_environment: Mapping[str, str],
    workspace_identity: Mapping[str, int],
) -> bool:
    try:
        if (
            type(evidence) is not dict
            or tuple(required_fields) != _EVIDENCE_FIELDS
            or len(required_fields) != 67
            or len(set(required_fields)) != 67
            or len(evidence) != 67
            or set(evidence) != set(required_fields)
        ):
            _raise_invalid()
        _canonical_json_bytes(evidence)
        hashes = (
            "stdout_sha256",
            "stderr_sha256",
            "model_state_digest_before",
            "model_state_digest_after",
            "checkpoint_sha256_before",
            "checkpoint_sha256_after",
        )
        if any(
            type(evidence[field]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", evidence[field]) is None
            for field in hashes
        ):
            _raise_invalid()
        expected_false = (
            "cuda_available",
            "parameter_values_modified",
            "parameter_versions_modified",
            "training_step_executed",
            "backward_executed",
            "optimizer_created",
            "optimizer_step_executed",
            "scheduler_step_executed",
            "chemical_generation_quality_validated",
            "output_sdf_symlink",
        )
        expected_true = (
            "model_target_residue_atom_conditioning",
            "dynamics_target_residue_atom_conditioning",
            "condition_embedding_all_zero",
            "indicator_field_present",
            "selector_object_is_resolver_output",
            "model_forward_executed",
            "real_generation_path_executed",
            "all_parameter_grads_none",
            "checkpoint_bytes_unchanged",
        )
        if any(evidence[field] is not False for field in expected_false) or any(
            evidence[field] is not True for field in expected_true
        ):
            _raise_invalid()
        if (
            evidence["evidence_schema_version"] != _EVIDENCE_VERSION
            or evidence["caller"] != "generate_ligands.py"
            or evidence["argv"] != list(expected_argv)
            or evidence["environment"] != dict(expected_environment)
            or evidence["child_returncode"] != 0
            or evidence["resolved_device"] != "cpu"
            or evidence["stdout_byte_count"] < 0
            or evidence["stderr_byte_count"] != 0
            or evidence["stderr_sha256"] != _sha256(b"")
            or evidence["resolver_call_count"] != 1
            or evidence["selector"] != _EXACT6_SELECTOR
            or evidence["conditioned_loader_call_count"] != 1
            or evidence["legacy_loader_call_count"] != 0
            or evidence["checkpoint_path"] != _CHECKPOINT_RELATIVE_PATH
            or evidence["map_location"] != "cpu"
            or evidence["condition_embedding_shape"] != [32]
            or evidence["state_key_count"] != 123
            or evidence["prepare_pocket_call_count"] != 1
            or evidence["pocket_size"] != [6]
            or evidence["indicator_dtype"] != "bool"
            or evidence["indicator_shape"] != [6]
            or evidence["indicator_true_count"] != 1
            or evidence["indicator_true_atom"] != _EXACT6_SELECTOR
            or evidence["generate_ligands_call_count"] != 1
            or evidence["n_samples"] != 1
            or evidence["pocket_ids"] != ["A:1"]
            or evidence["ref_ligand"] is not None
            or evidence["timesteps"] != 1
            or evidence["ddpm_type"] != "ConditionalDDPM"
            or evidence["dynamics_forward_call_count"] != 2
            or evidence["model_state_digest_before"]
            != evidence["model_state_digest_after"]
            or evidence["checkpoint_size_before"] != _CHECKPOINT_SIZE
            or evidence["checkpoint_size_after"] != _CHECKPOINT_SIZE
            or evidence["checkpoint_mtime_ns_before"]
            != evidence["checkpoint_mtime_ns_after"]
            or evidence["checkpoint_sha256_before"] != _CHECKPOINT_SHA256
            or evidence["checkpoint_sha256_after"] != _CHECKPOINT_SHA256
            or evidence["forbidden_save_api_call_count"] != 0
            or type(evidence["generated_molecule_count"]) is not int
            or evidence["generated_molecule_count"] not in (0, 1)
            or evidence["output_sdf_exists"] is not True
            or evidence["output_sdf_regular"] is not True
            or type(evidence["output_sdf_size"]) is not int
            or evidence["output_sdf_size"] < 0
            or type(evidence["output_sdf_record_count"]) is not int
            or evidence["output_sdf_record_count"] < 0
            or evidence["workspace_st_dev"] != workspace_identity.get("st_dev")
            or evidence["workspace_st_ino"] != workspace_identity.get("st_ino")
            or evidence["workspace_allowed_relative_paths"]
            != list(_ALLOWED_WORKSPACE_FILES)
        ):
            _raise_invalid()
        numeric_fields = (
            "stdout_byte_count",
            "stderr_byte_count",
            "resolver_call_count",
            "conditioned_loader_call_count",
            "legacy_loader_call_count",
            "state_key_count",
            "prepare_pocket_call_count",
            "indicator_true_count",
            "generate_ligands_call_count",
            "n_samples",
            "timesteps",
            "dynamics_forward_call_count",
            "forbidden_save_api_call_count",
            "generated_molecule_count",
            "output_sdf_size",
            "output_sdf_record_count",
            "workspace_st_dev",
            "workspace_st_ino",
        )
        if any(type(evidence[field]) is not int for field in numeric_fields):
            _raise_invalid()
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _state_digest(model: object, torch_module: object) -> str:
    try:
        state = model.state_dict()  # type: ignore[attr-defined]
        digest = hashlib.sha256()
        for key in sorted(state):
            tensor = state[key]
            if not isinstance(tensor, torch_module.Tensor):  # type: ignore[attr-defined]
                _raise_invalid()
            value = tensor.detach().cpu().contiguous()
            key_bytes = key.encode("utf-8")
            dtype_bytes = str(value.dtype).encode("ascii")
            shape_bytes = _canonical_json_bytes(list(value.shape))
            tensor_bytes = value.reshape(-1).view(  # type: ignore[attr-defined]
                torch_module.uint8  # type: ignore[attr-defined]
            ).numpy().tobytes()
            for payload in (key_bytes, dtype_bytes, shape_bytes, tensor_bytes):
                digest.update(len(payload).to_bytes(8, "big"))
                digest.update(payload)
        return digest.hexdigest()
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _atom_identity(atom: object) -> dict[str, object]:
    try:
        residue = atom.get_parent()  # type: ignore[attr-defined]
        chain = residue.get_parent()
        residue_id = residue.id
        return {
            "chain_id": chain.id,
            "residue_sequence_number": residue_id[1],
            "residue_insertion_code": residue_id[2],
            "residue_name": residue.get_resname(),
            "atom_name": atom.get_name(),  # type: ignore[attr-defined]
            "element": atom.element,  # type: ignore[attr-defined]
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


@contextlib.contextmanager
def _installed_observers(observations: dict[str, Any], torch_module: object) -> Iterator[None]:
    patches: list[tuple[object, str, bool, object]] = []

    def patch(owner: object, name: str, replacement: object) -> None:
        had_own_attribute = not isinstance(owner, type) or name in vars(owner)
        original = (
            vars(owner)[name]
            if isinstance(owner, type) and had_own_attribute
            else getattr(owner, name)
        )
        patches.append((owner, name, had_own_attribute, original))
        setattr(owner, name, replacement)

    try:
        from covalent_ext import covapie_target_residue_atom_condition_repository_cli_v1 as cli
        from lightning_modules import LigandPocketDDPM
        import pytorch_lightning as pl

        original_resolver = cli.resolve_covapie_target_residue_atom_condition_cli_args_v1
        original_loader = cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1
        original_legacy_loader = LigandPocketDDPM.load_from_checkpoint
        original_prepare = LigandPocketDDPM.prepare_pocket
        original_generate = LigandPocketDDPM.generate_ligands
        original_training_step = LigandPocketDDPM.training_step

        @functools.wraps(original_resolver)
        def resolver_wrapper(*args: object, **kwargs: object) -> object:
            observations["resolver_call_count"] += 1
            result = original_resolver(*args, **kwargs)
            observations["selector_object"] = result
            observations["selector"] = dict(result) if type(result) is dict else result
            return result

        @functools.wraps(original_loader)
        def loader_wrapper(*args: object, **kwargs: object) -> object:
            observations["conditioned_loader_call_count"] += 1
            bound = __import__("inspect").signature(original_loader).bind(*args, **kwargs)
            bound.apply_defaults()
            observations["checkpoint_path"] = str(bound.arguments["checkpoint_path"])
            observations["map_location"] = str(bound.arguments["map_location"])
            model = original_loader(*args, **kwargs)
            dynamics = model.ddpm.dynamics
            embedding = dynamics.target_residue_atom_condition_embedding
            observations["model_target_residue_atom_conditioning"] = (
                model.target_residue_atom_conditioning is True
            )
            observations["dynamics_target_residue_atom_conditioning"] = (
                dynamics.target_residue_atom_conditioning is True
            )
            observations["condition_embedding_shape"] = list(embedding.shape)
            observations["condition_embedding_all_zero"] = (
                int(torch_module.count_nonzero(embedding).item()) == 0  # type: ignore[attr-defined]
            )
            observations["state_key_count"] = len(model.state_dict())
            observations["loaded_model_object"] = model
            return model

        @classmethod
        def legacy_loader_wrapper(cls: type, *args: object, **kwargs: object) -> object:
            del cls
            observations["legacy_loader_call_count"] += 1
            return original_legacy_loader(*args, **kwargs)

        @functools.wraps(original_prepare)
        def prepare_wrapper(self: object, *args: object, **kwargs: object) -> object:
            observations["prepare_pocket_call_count"] += 1
            bound = __import__("inspect").signature(original_prepare).bind(
                self, *args, **kwargs
            )
            bound.apply_defaults()
            residues = bound.arguments["biopython_residues"]
            result = original_prepare(self, *args, **kwargs)
            indicator = result.get(
                "pocket_target_residue_atom_condition_indicator"
            )
            observations["pocket_size"] = result["size"].detach().cpu().tolist()
            observations["indicator_field_present"] = indicator is not None
            if indicator is not None:
                indicator_cpu = indicator.detach().cpu()
                observations["indicator_dtype"] = (
                    "bool" if indicator_cpu.dtype == torch_module.bool else str(indicator_cpu.dtype)  # type: ignore[attr-defined]
                )
                observations["indicator_shape"] = list(indicator_cpu.shape)
                observations["indicator_true_count"] = int(indicator_cpu.sum().item())
                true_indices = indicator_cpu.nonzero(as_tuple=False).view(-1).tolist()
                pocket_atoms = [
                    atom
                    for residue in residues
                    for atom in residue.get_atoms()
                    if (
                        atom.element.capitalize() in self.pocket_type_encoder
                        or atom.element != "H"
                    )
                ]
                observations["indicator_true_atom"] = (
                    _atom_identity(pocket_atoms[true_indices[0]])
                    if len(true_indices) == 1 and true_indices[0] < len(pocket_atoms)
                    else None
                )
            return result

        @functools.wraps(original_generate)
        def generate_wrapper(self: object, *args: object, **kwargs: object) -> object:
            observations["generate_ligands_call_count"] += 1
            bound = __import__("inspect").signature(original_generate).bind(
                self, *args, **kwargs
            )
            bound.apply_defaults()
            observations["n_samples"] = bound.arguments["n_samples"]
            observations["pocket_ids"] = list(bound.arguments["pocket_ids"])
            observations["ref_ligand"] = bound.arguments["ref_ligand"]
            observations["timesteps"] = bound.arguments["timesteps"]
            observations["selector_object_is_resolver_output"] = (
                bound.arguments["target_residue_atom_condition_spec"]
                is observations.get("selector_object")
            )
            observations["ddpm_type"] = type(self.ddpm).__name__
            before_digest = _state_digest(self, torch_module)
            named_parameters = list(self.named_parameters())
            before_versions = {name: parameter._version for name, parameter in named_parameters}
            before_values = {
                name: parameter.detach().cpu().clone()
                for name, parameter in named_parameters
            }
            observations["model_state_digest_before"] = before_digest

            def forward_hook(module: object, inputs: object, output: object) -> None:
                del module, inputs, output
                observations["dynamics_forward_call_count"] += 1
                return None

            handle = self.ddpm.dynamics.register_forward_hook(forward_hook)
            try:
                with torch_module.no_grad():  # type: ignore[attr-defined]
                    result = original_generate(self, *args, **kwargs)
            finally:
                handle.remove()
                after_digest = _state_digest(self, torch_module)
                observations["model_state_digest_after"] = after_digest
                observations["parameter_versions_modified"] = any(
                    parameter._version != before_versions[name]
                    for name, parameter in named_parameters
                )
                observations["parameter_values_modified"] = any(
                    not torch_module.equal(  # type: ignore[attr-defined]
                        parameter.detach().cpu(), before_values[name]
                    )
                    for name, parameter in named_parameters
                )
                observations["all_parameter_grads_none"] = all(
                    parameter.grad is None for _, parameter in named_parameters
                )
            observations["generated_molecule_count"] = len(result)
            observations["model_forward_executed"] = (
                observations["dynamics_forward_call_count"] == 2
            )
            observations["real_generation_path_executed"] = True
            return result

        @functools.wraps(original_training_step)
        def training_step_wrapper(*args: object, **kwargs: object) -> object:
            observations["training_step_executed"] = True
            return original_training_step(*args, **kwargs)

        patch(cli, "resolve_covapie_target_residue_atom_condition_cli_args_v1", resolver_wrapper)
        patch(cli, "load_covapie_target_residue_conditioned_model_from_checkpoint_v1", loader_wrapper)
        patch(LigandPocketDDPM, "load_from_checkpoint", legacy_loader_wrapper)
        patch(LigandPocketDDPM, "prepare_pocket", prepare_wrapper)
        patch(LigandPocketDDPM, "generate_ligands", generate_wrapper)
        patch(LigandPocketDDPM, "training_step", training_step_wrapper)

        original_tensor_backward = torch_module.Tensor.backward  # type: ignore[attr-defined]

        @functools.wraps(original_tensor_backward)
        def tensor_backward_wrapper(*args: object, **kwargs: object) -> object:
            observations["backward_executed"] = True
            return original_tensor_backward(*args, **kwargs)

        patch(torch_module.Tensor, "backward", tensor_backward_wrapper)  # type: ignore[attr-defined]

        original_autograd_backward = torch_module.autograd.backward  # type: ignore[attr-defined]

        @functools.wraps(original_autograd_backward)
        def autograd_backward_wrapper(*args: object, **kwargs: object) -> object:
            observations["backward_executed"] = True
            return original_autograd_backward(*args, **kwargs)

        patch(torch_module.autograd, "backward", autograd_backward_wrapper)  # type: ignore[attr-defined]

        original_optimizer_init = torch_module.optim.Optimizer.__init__  # type: ignore[attr-defined]
        original_optimizer_step = torch_module.optim.Optimizer.step  # type: ignore[attr-defined]

        @functools.wraps(original_optimizer_init)
        def optimizer_init_wrapper(*args: object, **kwargs: object) -> object:
            observations["optimizer_created"] = True
            return original_optimizer_init(*args, **kwargs)

        @functools.wraps(original_optimizer_step)
        def optimizer_step_wrapper(*args: object, **kwargs: object) -> object:
            observations["optimizer_step_executed"] = True
            return original_optimizer_step(*args, **kwargs)

        patch(torch_module.optim.Optimizer, "__init__", optimizer_init_wrapper)  # type: ignore[attr-defined]
        patch(torch_module.optim.Optimizer, "step", optimizer_step_wrapper)  # type: ignore[attr-defined]

        scheduler_types = []
        for name in ("LRScheduler", "_LRScheduler"):
            scheduler_type = getattr(torch_module.optim.lr_scheduler, name, None)  # type: ignore[attr-defined]
            if isinstance(scheduler_type, type) and scheduler_type not in scheduler_types:
                scheduler_types.append(scheduler_type)
        for scheduler_type in scheduler_types:
            original_scheduler_step = scheduler_type.step

            def make_scheduler_wrapper(original: Callable[..., object]) -> Callable[..., object]:
                @functools.wraps(original)
                def scheduler_step_wrapper(*args: object, **kwargs: object) -> object:
                    observations["scheduler_step_executed"] = True
                    return original(*args, **kwargs)

                return scheduler_step_wrapper

            patch(scheduler_type, "step", make_scheduler_wrapper(original_scheduler_step))

        original_torch_save = torch_module.save  # type: ignore[attr-defined]

        @functools.wraps(original_torch_save)
        def torch_save_wrapper(*args: object, **kwargs: object) -> object:
            observations["forbidden_save_api_call_count"] += 1
            return original_torch_save(*args, **kwargs)

        patch(torch_module, "save", torch_save_wrapper)

        original_trainer_save = pl.Trainer.save_checkpoint

        @functools.wraps(original_trainer_save)
        def trainer_save_wrapper(*args: object, **kwargs: object) -> object:
            observations["forbidden_save_api_call_count"] += 1
            return original_trainer_save(*args, **kwargs)

        patch(pl.Trainer, "save_checkpoint", trainer_save_wrapper)
        yield
    finally:
        for owner, name, had_own_attribute, original in reversed(patches):
            if isinstance(owner, type) and not had_own_attribute:
                delattr(owner, name)
            else:
                setattr(owner, name, original)


def _initial_observations() -> dict[str, Any]:
    return {
        "resolver_call_count": 0,
        "selector": None,
        "selector_object": None,
        "conditioned_loader_call_count": 0,
        "legacy_loader_call_count": 0,
        "checkpoint_path": None,
        "map_location": None,
        "model_target_residue_atom_conditioning": False,
        "dynamics_target_residue_atom_conditioning": False,
        "condition_embedding_shape": None,
        "condition_embedding_all_zero": False,
        "state_key_count": 0,
        "prepare_pocket_call_count": 0,
        "pocket_size": None,
        "indicator_field_present": False,
        "indicator_dtype": None,
        "indicator_shape": None,
        "indicator_true_count": 0,
        "indicator_true_atom": None,
        "generate_ligands_call_count": 0,
        "n_samples": None,
        "pocket_ids": None,
        "ref_ligand": None,
        "timesteps": None,
        "selector_object_is_resolver_output": False,
        "ddpm_type": None,
        "dynamics_forward_call_count": 0,
        "model_forward_executed": False,
        "real_generation_path_executed": False,
        "training_step_executed": False,
        "backward_executed": False,
        "optimizer_created": False,
        "optimizer_step_executed": False,
        "scheduler_step_executed": False,
        "all_parameter_grads_none": False,
        "model_state_digest_before": None,
        "model_state_digest_after": None,
        "parameter_values_modified": True,
        "parameter_versions_modified": True,
        "forbidden_save_api_call_count": 0,
        "generated_molecule_count": None,
    }


def _output_sdf_metadata(output_path: Path) -> dict[str, object]:
    try:
        metadata = os.lstat(output_path)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _raise_invalid()
        payload = output_path.read_bytes()
        final = os.lstat(output_path)
        if (
            (metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_size)
            != (final.st_dev, final.st_ino, final.st_mode, final.st_size)
            or len(payload) != final.st_size
        ):
            _raise_invalid()
        return {
            "output_sdf_exists": True,
            "output_sdf_regular": True,
            "output_sdf_symlink": False,
            "output_sdf_size": len(payload),
            "output_sdf_record_count": payload.count(b"$$$$"),
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _build_child_evidence(
    *,
    observations: Mapping[str, Any],
    argv: Sequence[str],
    stdout_bytes: bytes,
    stderr_bytes: bytes,
    checkpoint_before: Mapping[str, object],
    checkpoint_after: Mapping[str, object],
    output_metadata: Mapping[str, object],
    workspace_identity: Mapping[str, int],
) -> dict[str, object]:
    values: dict[str, object] = {
        "evidence_schema_version": _EVIDENCE_VERSION,
        "caller": "generate_ligands.py",
        "argv": list(argv),
        "environment": dict(_CHILD_ENVIRONMENT),
        "child_returncode": 0,
        "resolved_device": "cpu",
        "cuda_available": False,
        "stdout_byte_count": len(stdout_bytes),
        "stdout_sha256": _sha256(stdout_bytes),
        "stderr_byte_count": len(stderr_bytes),
        "stderr_sha256": _sha256(stderr_bytes),
        "resolver_call_count": observations["resolver_call_count"],
        "selector": observations["selector"],
        "conditioned_loader_call_count": observations["conditioned_loader_call_count"],
        "legacy_loader_call_count": observations["legacy_loader_call_count"],
        "checkpoint_path": observations["checkpoint_path"],
        "map_location": observations["map_location"],
        "model_target_residue_atom_conditioning": observations[
            "model_target_residue_atom_conditioning"
        ],
        "dynamics_target_residue_atom_conditioning": observations[
            "dynamics_target_residue_atom_conditioning"
        ],
        "condition_embedding_shape": observations["condition_embedding_shape"],
        "condition_embedding_all_zero": observations["condition_embedding_all_zero"],
        "state_key_count": observations["state_key_count"],
        "prepare_pocket_call_count": observations["prepare_pocket_call_count"],
        "pocket_size": observations["pocket_size"],
        "indicator_field_present": observations["indicator_field_present"],
        "indicator_dtype": observations["indicator_dtype"],
        "indicator_shape": observations["indicator_shape"],
        "indicator_true_count": observations["indicator_true_count"],
        "indicator_true_atom": observations["indicator_true_atom"],
        "generate_ligands_call_count": observations["generate_ligands_call_count"],
        "n_samples": observations["n_samples"],
        "pocket_ids": observations["pocket_ids"],
        "ref_ligand": observations["ref_ligand"],
        "timesteps": observations["timesteps"],
        "selector_object_is_resolver_output": observations[
            "selector_object_is_resolver_output"
        ],
        "ddpm_type": observations["ddpm_type"],
        "dynamics_forward_call_count": observations["dynamics_forward_call_count"],
        "model_forward_executed": observations["model_forward_executed"],
        "real_generation_path_executed": observations[
            "real_generation_path_executed"
        ],
        "training_step_executed": observations["training_step_executed"],
        "backward_executed": observations["backward_executed"],
        "optimizer_created": observations["optimizer_created"],
        "optimizer_step_executed": observations["optimizer_step_executed"],
        "scheduler_step_executed": observations["scheduler_step_executed"],
        "all_parameter_grads_none": observations["all_parameter_grads_none"],
        "model_state_digest_before": observations["model_state_digest_before"],
        "model_state_digest_after": observations["model_state_digest_after"],
        "parameter_values_modified": observations["parameter_values_modified"],
        "parameter_versions_modified": observations["parameter_versions_modified"],
        "checkpoint_size_before": checkpoint_before["size"],
        "checkpoint_size_after": checkpoint_after["size"],
        "checkpoint_mtime_ns_before": checkpoint_before["mtime_ns"],
        "checkpoint_mtime_ns_after": checkpoint_after["mtime_ns"],
        "checkpoint_sha256_before": checkpoint_before["sha256"],
        "checkpoint_sha256_after": checkpoint_after["sha256"],
        "checkpoint_bytes_unchanged": checkpoint_before == checkpoint_after,
        "forbidden_save_api_call_count": observations[
            "forbidden_save_api_call_count"
        ],
        "generated_molecule_count": observations["generated_molecule_count"],
        **dict(output_metadata),
        "chemical_generation_quality_validated": False,
        "workspace_st_dev": workspace_identity["st_dev"],
        "workspace_st_ino": workspace_identity["st_ino"],
        "workspace_allowed_relative_paths": list(_ALLOWED_WORKSPACE_FILES),
    }
    return {field: values[field] for field in _EVIDENCE_FIELDS}


def _child_main(*, repo_root: Path, workspace: Path) -> int:
    stdout_text = io.StringIO()
    stderr_text = io.StringIO()
    success = False
    evidence_payload: bytes | None = None
    try:
        workspace_metadata = os.lstat(workspace)
        if (
            not stat.S_ISDIR(workspace_metadata.st_mode)
            or stat.S_ISLNK(workspace_metadata.st_mode)
            or workspace.parent != Path("/tmp")
            or not workspace.name.startswith(_WORKSPACE_PREFIX)
            or repo_root.is_symlink()
            or not repo_root.is_dir()
        ):
            _raise_invalid()
        workspace_identity = {
            "st_dev": workspace_metadata.st_dev,
            "st_ino": workspace_metadata.st_ino,
        }
        argv = _expected_cli_argv(workspace)
        observations = _initial_observations()
        checkpoint_path = repo_root / _CHECKPOINT_RELATIVE_PATH
        checkpoint_before = _file_identity(checkpoint_path)
        _validate_checkpoint_identity(checkpoint_before)

        with contextlib.redirect_stdout(stdout_text), contextlib.redirect_stderr(stderr_text):
            try:
                import numpy
                import torch

                random.seed(0)
                numpy.random.seed(0)
                torch.manual_seed(0)
                torch.set_num_threads(1)
                if hasattr(torch, "set_num_interop_threads"):
                    try:
                        torch.set_num_interop_threads(1)
                    except RuntimeError:
                        pass
                if torch.cuda.is_available() is not False:
                    _raise_invalid()
                original_argv = sys.argv
                try:
                    with _installed_observers(observations, torch):
                        sys.argv = list(argv)
                        with torch.no_grad():
                            runpy.run_path("generate_ligands.py", run_name="__main__")
                finally:
                    sys.argv = original_argv
            except BaseException:
                traceback.print_exc()

        stdout_bytes = stdout_text.getvalue().encode("utf-8")
        stderr_bytes = stderr_text.getvalue().encode("utf-8")
        (workspace / "logs" / "stdout.bin").write_bytes(stdout_bytes)
        (workspace / "logs" / "stderr.bin").write_bytes(stderr_bytes)
        if stderr_bytes:
            return 1

        checkpoint_after = _file_identity(checkpoint_path)
        _validate_checkpoint_identity(checkpoint_after)
        output_metadata = _output_sdf_metadata(workspace / "output" / "generated.sdf")
        evidence = _build_child_evidence(
            observations=observations,
            argv=argv,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            checkpoint_before=checkpoint_before,
            checkpoint_after=checkpoint_after,
            output_metadata=output_metadata,
            workspace_identity=workspace_identity,
        )
        _validate_runtime_evidence(
            evidence=evidence,
            required_fields=_EVIDENCE_FIELDS,
            expected_argv=argv,
            expected_environment=_CHILD_ENVIRONMENT,
            workspace_identity=workspace_identity,
        )
        evidence_payload = _canonical_json_bytes(evidence)
        evidence_path = workspace / "evidence" / "runtime_smoke_evidence.json"
        with evidence_path.open("xb") as handle:
            handle.write(evidence_payload)
        success = True
        return 0
    except BaseException:
        if not stderr_text.getvalue():
            traceback.print_exc(file=stderr_text)
        try:
            (workspace / "logs" / "stdout.bin").write_bytes(
                stdout_text.getvalue().encode("utf-8")
            )
            (workspace / "logs" / "stderr.bin").write_bytes(
                stderr_text.getvalue().encode("utf-8")
            )
        except Exception:
            pass
        return 1
    finally:
        del evidence_payload, success


def _workspace_entries(workspace: Path) -> tuple[list[str], list[str], bool]:
    files: list[str] = []
    directories: list[str] = []
    symlink_found = False
    for root, dirnames, filenames in os.walk(workspace, topdown=True, followlinks=False):
        root_path = Path(root)
        for name in sorted(dirnames):
            path = root_path / name
            relative = path.relative_to(workspace).as_posix()
            metadata = os.lstat(path)
            if stat.S_ISLNK(metadata.st_mode):
                symlink_found = True
                dirnames.remove(name)
            directories.append(relative)
        for name in sorted(filenames):
            path = root_path / name
            relative = path.relative_to(workspace).as_posix()
            metadata = os.lstat(path)
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                symlink_found = True
            files.append(relative)
    return sorted(files), sorted(directories), symlink_found


def _validate_workspace_contents(workspace: Path, *, require_success_files: bool) -> bool:
    try:
        files, directories, symlink_found = _workspace_entries(workspace)
        allowed_files = set(_ALLOWED_WORKSPACE_FILES)
        required_files = set(_ALLOWED_WORKSPACE_FILES) if require_success_files else {
            "input/minimal_cys_sg.pdb",
            "logs/stdout.bin",
            "logs/stderr.bin",
        }
        if (
            symlink_found
            or not set(files).issubset(allowed_files)
            or not required_files.issubset(files)
            or set(directories) != set(_ALLOWED_WORKSPACE_DIRECTORIES)
        ):
            _raise_invalid()
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _safe_cleanup_workspace(
    workspace: Path,
    *,
    expected_st_dev: int,
    expected_st_ino: int,
    remover: Callable[[Path], object] = shutil.rmtree,
) -> dict[str, object]:
    result: dict[str, object] = {
        "attempted": True,
        "inode_guard_matched": False,
        "removed": False,
        "competitor_path_deleted": False,
        "exists_after": os.path.lexists(workspace),
    }
    try:
        metadata = os.lstat(workspace)
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_dev != expected_st_dev
            or metadata.st_ino != expected_st_ino
        ):
            result["exists_after"] = os.path.lexists(workspace)
            return result
        result["inode_guard_matched"] = True
        remover(workspace)
        result["removed"] = not os.path.lexists(workspace)
        result["exists_after"] = os.path.lexists(workspace)
        return result
    except FileNotFoundError:
        result["exists_after"] = False
        return result
    except Exception as error:
        result["cleanup_error"] = f"{type(error).__name__}:{error}"
        result["exists_after"] = os.path.lexists(workspace)
        return result


def _run_child_process(
    *,
    command: Sequence[str],
    repo_root: Path,
    environment: Mapping[str, str],
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> dict[str, object]:
    try:
        completed = runner(
            list(command),
            cwd=repo_root,
            env=dict(environment),
            check=False,
            capture_output=True,
            timeout=_TIMEOUT_SECONDS,
        )
        return {
            "timeout": False,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "timeout": True,
            "returncode": None,
            "stdout": error.stdout or b"",
            "stderr": error.stderr or b"",
        }


def _utc_now() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _make_workspace() -> tuple[Path, dict[str, int]]:
    timestamp = _datetime.datetime.now(_datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    workspace = Path(
        tempfile.mkdtemp(prefix=f"{_WORKSPACE_PREFIX}{timestamp}_", dir="/tmp")
    )
    metadata = os.lstat(workspace)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _raise_invalid()
    for name in _ALLOWED_WORKSPACE_DIRECTORIES:
        (workspace / name).mkdir(mode=0o700)
    return workspace, {"st_dev": metadata.st_dev, "st_ino": metadata.st_ino}


def _failure_summary(error: BaseException) -> str:
    return f"{type(error).__name__}:{error}"


def _guard_one_time_execution_authorization_v1() -> None:
    if _ONE_TIME_EXECUTION_AUTHORIZATION_CONSUMED is True:
        raise ValueError(_EXECUTION_AUTHORIZATION_CONSUMED_ERROR)


def execute_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1(
    *,
    repo_root: Path,
    python_executable: Path,
) -> dict[str, object]:
    """Reject execution because the one-time authorization is consumed."""

    _guard_one_time_execution_authorization_v1()
    start_utc = _utc_now()
    workspace: Path | None = None
    workspace_identity: dict[str, int] | None = None
    cleanup: dict[str, object] = {
        "attempted": False,
        "inode_guard_matched": False,
        "removed": False,
        "competitor_path_deleted": False,
        "exists_after": False,
    }
    result: dict[str, object] = {
        "bounded_runtime_smoke_execution_count": 1,
        "bounded_runtime_smoke_passed": False,
        "automatic_retry_performed": False,
        "architecture_expansion_authorized": False,
        "command": [],
        "start_UTC": start_utc,
        "end_UTC": None,
        "timeout": False,
        "child_returncode": None,
        "parent_stdout_byte_count": 0,
        "parent_stdout_sha256": _sha256(b""),
        "parent_stderr_byte_count": 0,
        "parent_stderr_sha256": _sha256(b""),
        "evidence_byte_count": 0,
        "evidence_sha256": None,
        "evidence_field_count": 0,
        "evidence": None,
        "checkpoint_before": None,
        "checkpoint_after": None,
        "checkpoint_unchanged": False,
        "git_before": None,
        "git_after": None,
        "git_unchanged": False,
        "workspace_path": None,
        "workspace_identity": None,
        "workspace_allowed_paths_valid": False,
        "cleanup": cleanup,
        "repository_runtime_outputs_created": False,
        "training_or_parameter_update": False,
        "RL_implementation_started": False,
        "chemical_generation_quality_validated": False,
        "commit_created": False,
        "push_performed": False,
        "post_smoke_mainline_priority": _POST_SMOKE_MAINLINE,
        "failure_reason": None,
    }
    try:
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_absolute()
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(python_executable) is not type(Path())
            or not python_executable.is_absolute()
        ):
            _raise_invalid()
        python_metadata = os.lstat(python_executable)
        if (
            stat.S_ISLNK(python_metadata.st_mode)
            or not stat.S_ISREG(python_metadata.st_mode)
            or not bool(python_metadata.st_mode & 0o111)
        ):
            _raise_invalid()

        implementation = (
            evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1(
                repo_root=repo_root
            )
        )
        if implementation["ready_for_one_time_bounded_runtime_smoke_execution"] is not True:
            _raise_invalid()
        git_before = _terminal_lifecycle_evidence(repo_root, include_remote=True)
        _validate_terminal_lifecycle_evidence(git_before)
        checkpoint_path = repo_root / _CHECKPOINT_RELATIVE_PATH
        checkpoint_before = _file_identity(checkpoint_path)
        _validate_checkpoint_identity(checkpoint_before)
        result["git_before"] = git_before
        result["checkpoint_before"] = checkpoint_before

        workspace, workspace_identity = _make_workspace()
        result["workspace_path"] = str(workspace)
        result["workspace_identity"] = dict(workspace_identity)
        design_response, _ = _bind_design(repo_root)
        if design_response["ready_for_bounded_runtime_smoke_implementation"] is not True:
            _raise_invalid()
        checkpoint_immediately_before = _file_identity(checkpoint_path)
        _validate_checkpoint_identity(checkpoint_immediately_before)
        if checkpoint_immediately_before != checkpoint_before:
            _raise_invalid()
        git_immediately_before = _terminal_lifecycle_evidence(
            repo_root, include_remote=True
        )
        _validate_terminal_lifecycle_evidence(git_immediately_before)
        if git_immediately_before != git_before:
            _raise_invalid()

        pdb_contract = design_response["temporary_PDB_contract"]
        pdb_payload = pdb_contract["pdb_text"].encode("utf-8")
        if (
            len(pdb_payload) != 505
            or _sha256(pdb_payload)
            != "ccad2ee5cd8cc2459003790d837bbdc68fede63cdb5ea575f433250048f302c3"
            or pdb_contract["model_count"] != 1
            or pdb_contract["residue_count"] != 1
            or pdb_contract["atom_count"] != 6
            or pdb_contract["SG_count"] != 1
        ):
            _raise_invalid()
        pdb_path = workspace / "input" / "minimal_cys_sg.pdb"
        with pdb_path.open("xb") as handle:
            handle.write(pdb_payload)
        written_pdb = pdb_path.read_bytes()
        if written_pdb != pdb_payload:
            _raise_invalid()

        command = _child_command(repo_root, python_executable, workspace)
        result["command"] = command
        child_environment = {**os.environ, **_CHILD_ENVIRONMENT}
        child = _run_child_process(
            command=command,
            repo_root=repo_root,
            environment=child_environment,
        )
        child_stdout = child["stdout"]
        child_stderr = child["stderr"]
        if not isinstance(child_stdout, bytes) or not isinstance(child_stderr, bytes):
            _raise_invalid()
        result["timeout"] = child["timeout"]
        result["child_returncode"] = child["returncode"]
        result["parent_stdout_byte_count"] = len(child_stdout)
        result["parent_stdout_sha256"] = _sha256(child_stdout)
        result["parent_stderr_byte_count"] = len(child_stderr)
        result["parent_stderr_sha256"] = _sha256(child_stderr)

        evidence: dict[str, object] | None = None
        evidence_payload: bytes | None = None
        evidence_path = workspace / "evidence" / "runtime_smoke_evidence.json"
        if evidence_path.exists() and not evidence_path.is_symlink():
            evidence_payload = evidence_path.read_bytes()
            parsed = json.loads(evidence_payload.decode("utf-8", errors="strict"))
            if type(parsed) is not dict or _canonical_json_bytes(parsed) != evidence_payload:
                _raise_invalid()
            evidence = parsed
            _validate_runtime_evidence(
                evidence=evidence,
                required_fields=design_response["runtime_evidence_schema"][
                    "required_fields"
                ],
                expected_argv=_expected_cli_argv(workspace),
                expected_environment=_CHILD_ENVIRONMENT,
                workspace_identity=workspace_identity,
            )
            stdout_log = (workspace / "logs" / "stdout.bin").read_bytes()
            stderr_log = (workspace / "logs" / "stderr.bin").read_bytes()
            if (
                len(stdout_log) != evidence["stdout_byte_count"]
                or _sha256(stdout_log) != evidence["stdout_sha256"]
                or len(stderr_log) != evidence["stderr_byte_count"]
                or _sha256(stderr_log) != evidence["stderr_sha256"]
            ):
                _raise_invalid()
            result["evidence"] = evidence
            result["evidence_byte_count"] = len(evidence_payload)
            result["evidence_sha256"] = _sha256(evidence_payload)
            result["evidence_field_count"] = len(evidence)

        require_success = (
            child["timeout"] is False
            and child["returncode"] == 0
            and child_stderr == b""
            and evidence is not None
        )
        _validate_workspace_contents(
            workspace, require_success_files=require_success
        )
        result["workspace_allowed_paths_valid"] = True

        checkpoint_after = _file_identity(checkpoint_path)
        _validate_checkpoint_identity(checkpoint_after)
        git_after = _terminal_lifecycle_evidence(repo_root, include_remote=True)
        _validate_terminal_lifecycle_evidence(git_after)
        result["checkpoint_after"] = checkpoint_after
        result["git_after"] = git_after
        result["checkpoint_unchanged"] = checkpoint_after == checkpoint_before
        result["git_unchanged"] = git_after == git_before

        if not require_success:
            internal_stderr = b""
            stderr_log_path = workspace / "logs" / "stderr.bin"
            if stderr_log_path.exists() and not stderr_log_path.is_symlink():
                internal_stderr = stderr_log_path.read_bytes()
            diagnostic = internal_stderr.decode("utf-8", errors="replace")[-4000:]
            result["failure_reason"] = (
                "child_failed:"
                f"timeout={child['timeout']}:returncode={child['returncode']}:"
                f"parent_stderr_bytes={len(child_stderr)}:internal_stderr_tail={diagnostic}"
            )
        elif checkpoint_after != checkpoint_before:
            result["failure_reason"] = "checkpoint_identity_drift"
        elif git_after != git_before:
            result["failure_reason"] = "git_state_drift"
    except BaseException as error:
        result["failure_reason"] = _failure_summary(error)
        if workspace is not None and workspace.exists():
            try:
                checkpoint_path = repo_root / _CHECKPOINT_RELATIVE_PATH
                if result["checkpoint_after"] is None:
                    result["checkpoint_after"] = _file_identity(checkpoint_path)
                if result["git_after"] is None:
                    result["git_after"] = _terminal_lifecycle_evidence(
                        repo_root, include_remote=True
                    )
            except Exception:
                pass
    finally:
        if workspace is not None and workspace_identity is not None:
            cleanup = _safe_cleanup_workspace(
                workspace,
                expected_st_dev=workspace_identity["st_dev"],
                expected_st_ino=workspace_identity["st_ino"],
            )
            result["cleanup"] = cleanup
        result["end_UTC"] = _utc_now()

    smoke_passed = (
        result["failure_reason"] is None
        and result["timeout"] is False
        and result["child_returncode"] == 0
        and result["parent_stderr_byte_count"] == 0
        and result["evidence_field_count"] == 67
        and result["checkpoint_unchanged"] is True
        and result["git_unchanged"] is True
        and result["workspace_allowed_paths_valid"] is True
        and result["cleanup"].get("removed") is True
        and result["cleanup"].get("inode_guard_matched") is True
        and result["cleanup"].get("exists_after") is False
        and result["repository_runtime_outputs_created"] is False
    )
    result["bounded_runtime_smoke_passed"] = smoke_passed
    if not smoke_passed and result["failure_reason"] is None:
        result["failure_reason"] = "parent_final_acceptance_failed"
    _canonical_json_bytes(result)
    return result


def _parse_child_arguments(arguments: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parsed = parser.parse_args(list(arguments))
    if parsed.child is not True:
        _raise_invalid()
    return parsed


def _module_main(arguments: Sequence[str] | None = None) -> int:
    _guard_one_time_execution_authorization_v1()
    parsed = _parse_child_arguments(sys.argv[1:] if arguments is None else arguments)
    return _child_main(
        repo_root=parsed.repo_root.resolve(),
        workspace=parsed.workspace,
    )


if __name__ == "__main__":
    raise SystemExit(_module_main())
