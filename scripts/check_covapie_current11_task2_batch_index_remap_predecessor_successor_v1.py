#!/usr/bin/env python3
"""Check the Current11 Task2 remap predecessor successor V1."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_predecessor_successor_v1 as b3,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    as b2,
)


_ERROR = b3.ERROR_TOKEN
_PRECOMMIT_STATUS = (
    "PASS_REMAP_PREDECESSOR_SUCCESSOR_PRECOMMIT_CANDIDATE_ONLY"
)
_CLEAN_STATUS = b3.SUCCESSOR_STATUS
_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0"


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    return parser


def _root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise ValueError(_ERROR) from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _safe_exact4(repo_root: Path) -> None:
    for relative in b3.REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(_ERROR) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or any(
                line.rstrip(b"\r\n").endswith((b" ", b"\t"))
                for line in payload.splitlines(keepends=True)
            )
        ):
            _fail()
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(_ERROR) from error


def _repository_lifecycle(repo_root: Path) -> str:
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *b3.REPOSITORY_EXACT4)
    ).splitlines()
    expected = {f"?? {relative}" for relative in b3.REPOSITORY_EXACT4}
    if set(status) == expected and len(status) == len(b3.REPOSITORY_EXACT4):
        if index:
            _fail()
        _safe_exact4(repo_root)
        return "precommit-untracked"
    if status or len(index) != len(b3.REPOSITORY_EXACT4):
        _fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise ValueError(_ERROR) from error
        if (
            relative not in b3.REPOSITORY_EXACT4
            or relative in seen
            or mode != "100644"
            or stage != "0"
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != blob
            or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
            != blob
        ):
            _fail()
        seen.add(relative)
    if seen != set(b3.REPOSITORY_EXACT4):
        _fail()
    _safe_exact4(repo_root)
    return "clean-tracked-successor"


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _target_name(node.value)
        return None if left is None else f"{left}.{node.attr}"
    return None


def _static_product_validation(repo_root: Path) -> None:
    module_path = repo_root / b3.MODULE_PATH
    try:
        payload = module_path.read_bytes()
        tree = ast.parse(payload.decode("utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    function = (
        b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1
    )
    signature = inspect.signature(function)
    if (
        b3.__all__ != (function.__name__,)
        or tuple(signature.parameters) != ("repo_root", "state_root")
        or any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in signature.parameters.values()
        )
    ):
        _fail()
    forbidden_calls = {
        "build_covapie_current11_tensor_projection_payload_bundle_v1",
        "build_covapie_current11_tensor_projection_instance_v1",
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        "_build_impl",
        "_published_gate",
        "_payload_exact8",
        "_projection_exact2",
        "_contract_exact6",
        "setattr",
    }
    permitted_self_calls = {"_build_impl"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called = _target_name(node.func)
            leaf = None if called is None else called.rsplit(".", 1)[-1]
            if leaf in forbidden_calls and not (
                leaf in permitted_self_calls and called == "_build_impl"
            ):
                _fail()
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets: list[ast.AST]
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            else:
                targets = [node.target]
            if any(isinstance(target, ast.Attribute) for target in targets):
                _fail()


def _manual_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(_DOMAIN)
    for name in b3.STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _parse_canonical(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        _fail()
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if canonical != payload:
        _fail()
    return value


def _verify_artifacts(
    artifacts: object,
    *,
    expected_lifecycle: str,
) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != b3.ARTIFACT_NAMES:
        _fail()
    for name, identity in b3.REMAP_STABLE5_IDENTITIES.items():
        payload = artifacts.get(name)
        if (
            type(payload) is not bytes
            or len(payload) != identity[0]
            or payload.count(b"\n") != identity[1]
            or hashlib.sha256(payload).hexdigest() != identity[2]
        ):
            _fail()
    if _manual_digest(artifacts) != b3.REMAP_STABLE5_DIGEST:
        _fail()
    if b3.HISTORICAL_REPORT_NAME in artifacts:
        _fail()
    report_payload = artifacts[b3.SUCCESSOR_REPORT_NAME]
    if type(report_payload) is not bytes:
        _fail()
    report = _parse_canonical(report_payload)
    clean_live = expected_lifecycle == "clean-tracked-successor"
    if (
        report.get("schema_version") != b3.REPORT_SCHEMA
        or report.get("successor_status") != b3.SUCCESSOR_STATUS
        or report.get("artifact_names") != list(b3.ARTIFACT_NAMES)
        or report.get("repository_lifecycle") != expected_lifecycle
        or report.get("B2_transition_contract_call_count") != 1
        or report.get("B2_stable_digest") != b3.B2_STABLE_DIGEST
        or report.get("payload_stable7_digest") != b3.PAYLOAD_STABLE7_DIGEST
        or report.get("projection_instance_SHA256")
        != b3.PROJECTION_INSTANCE_IDENTITY[2]
        or report.get("projection_instance_digest")
        != b3.PROJECTION_INSTANCE_DIGEST
        or report.get("remap_stable5_digest") != b3.REMAP_STABLE5_DIGEST
        or report.get("production_monkeypatch_used") is not False
        or report.get("clean_successor_live_validation_pending") is clean_live
        or report.get("ready_for_one_heavy_parity_timing_probe") is not clean_live
        or report.get("ready_for_public_remap_adapter_hot_loop_contract_implementation")
        is not False
        or report.get("ready_for_training") is not False
    ):
        _fail()
    return report


def _b2_fixture(repo_root: Path, state_root: Path) -> dict[str, bytes]:
    original_lifecycle = b2._repository_lifecycle
    try:
        b2._repository_lifecycle = lambda unused: "clean-tracked-successor"
        artifacts = b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
    finally:
        b2._repository_lifecycle = original_lifecycle
    if type(artifacts) is not dict:
        _fail()
    b3._validate_b2_artifacts(artifacts)
    return artifacts


def _precommit_validation(
    repo_root: Path,
    state_root: Path,
) -> dict[str, object]:
    before_repository = b3._repository_snapshot(repo_root)
    before_formal = b3._formal_snapshot(state_root)
    b3._validate_repository_lineage(repo_root)
    b3._validate_b2_owner(repo_root)
    b3._validate_helper_owners(repo_root)
    signature_rows = b3._validate_helper_signatures()
    fixture = _b2_fixture(repo_root, state_root)
    first = b3._build_fixture_only(
        repo_root=repo_root,
        state_root=state_root,
        b2_artifacts=fixture,
    )
    second = b3._build_fixture_only(
        repo_root=repo_root,
        state_root=state_root,
        b2_artifacts=fixture,
    )
    if first != second:
        _fail()
    report = _verify_artifacts(first, expected_lifecycle="precommit-untracked")
    if (
        b3._repository_snapshot(repo_root) != before_repository
        or b3._formal_snapshot(state_root) != before_formal
    ):
        _fail()
    return {
        "status": _PRECOMMIT_STATUS,
        "repository_lifecycle": "precommit-untracked",
        "artifact_file_count": 6,
        "historical_stable5_digest": b3.REMAP_STABLE5_DIGEST,
        "payload_stable7_digest": b3.PAYLOAD_STABLE7_DIGEST,
        "projection_instance_digest": b3.PROJECTION_INSTANCE_DIGEST,
        "B2_stable_digest": b3.B2_STABLE_DIGEST,
        "B2_fixture_public_build_count": 1,
        "B2_transition_contract_call_count_per_fixture_reconstruction": 1,
        "fixture_reconstruction_count": 2,
        "fixture_double_build_byte_identical": True,
        "frozen_helper_signature_count": len(signature_rows),
        "real_public_B3_build_performed": False,
        "clean_successor_live_validation_pending": True,
        "test_harness_only": True,
        "production_path": False,
        "test_harness_monkeypatch_used": True,
        "production_monkeypatch_used": False,
        "repository_unchanged": True,
        "formal_unchanged": True,
        "ready_for_commit_review": True,
        "ready_for_one_heavy_parity_timing_probe": False,
        "ready_for_public_remap_adapter_hot_loop_contract_implementation": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "successor_fixture_report_status": report["successor_status"],
    }


def _clean_validation(repo_root: Path, state_root: Path) -> dict[str, object]:
    before_repository = b3._repository_snapshot(repo_root)
    before_formal = b3._formal_snapshot(state_root)
    first = b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
        repo_root=repo_root,
        state_root=state_root,
    )
    second = b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
        repo_root=repo_root,
        state_root=state_root,
    )
    if first != second:
        _fail()
    _verify_artifacts(first, expected_lifecycle="clean-tracked-successor")
    if (
        b3._repository_snapshot(repo_root) != before_repository
        or b3._formal_snapshot(state_root) != before_formal
    ):
        _fail()
    return {
        "status": _CLEAN_STATUS,
        "repository_lifecycle": "clean-tracked-successor",
        "artifact_file_count": 6,
        "historical_stable5_digest": b3.REMAP_STABLE5_DIGEST,
        "B2_transition_contract_call_count": 2,
        "public_B3_build_count": 2,
        "real_public_B3_build_performed": True,
        "double_build_byte_identical": True,
        "clean_successor_live_validation_pending": False,
        "production_monkeypatch_used": False,
        "repository_unchanged": True,
        "formal_unchanged": True,
        "ready_for_commit_review": True,
        "ready_for_one_heavy_parity_timing_probe": True,
        "ready_for_public_remap_adapter_hot_loop_contract_implementation": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repository = _root(arguments.repo_root)
    state = _root(arguments.state_root)
    _static_product_validation(repository)
    lifecycle = _repository_lifecycle(repository)
    if lifecycle == "precommit-untracked":
        summary = _precommit_validation(repository, state)
    elif lifecycle == "clean-tracked-successor":
        summary = _clean_validation(repository, state)
    else:
        _fail()
    if (
        summary["production_monkeypatch_used"] is not False
        or summary["ready_for_training"] is not False
        or (
            lifecycle == "precommit-untracked"
            and summary["ready_for_commit_review"] is not True
        )
        or (
            lifecycle == "clean-tracked-successor"
            and summary["ready_for_one_heavy_parity_timing_probe"] is not True
        )
    ):
        _fail()
    print(
        json.dumps(
            summary,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return _main(argv)
    except Exception:
        print(_ERROR, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
