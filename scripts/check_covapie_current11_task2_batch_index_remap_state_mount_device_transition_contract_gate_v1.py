#!/usr/bin/env python3
"""Check the Current11 remap state mount-device transition contract V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    as gate,
)


_ERROR = gate.ERROR_TOKEN
_STATUS = "PASS_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_ONLY"
_BASE_COMMIT = gate.BASE_COMMIT
_EXACT4 = gate.REPOSITORY_EXACT4
_EXACT5 = gate.ARTIFACT_NAMES
_STABLE4 = gate.STABLE_ARTIFACT_NAMES


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


def _run_git(repo: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo,
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


def _validate_repository_lineage(repo: Path) -> None:
    if _run_git(repo, ("branch", "--show-current")).strip() != "main":
        _fail()
    _run_git(repo, ("cat-file", "-e", f"{_BASE_COMMIT}^{{commit}}"))
    _run_git(repo, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))


def _repository_lifecycle(repo: Path) -> str:
    status = _run_git(
        repo, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(repo, ("ls-files", "--stage", "--", *_EXACT4)).splitlines()
    expected = {f"?? {path}" for path in _EXACT4}
    if set(status) == expected and len(status) == len(_EXACT4):
        if index:
            _fail()
        return "precommit-untracked"
    if status or len(index) != len(_EXACT4):
        _fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise ValueError(_ERROR) from error
        if (
            relative not in _EXACT4
            or relative in seen
            or mode != "100644"
            or stage != "0"
            or _run_git(
                repo, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != blob
            or _run_git(repo, ("rev-parse", f"HEAD:{relative}")).strip()
            != blob
        ):
            _fail()
        seen.add(relative)
    if seen != set(_EXACT4):
        _fail()
    return "clean-tracked-successor"


def _repository_snapshot(repo: Path) -> tuple[object, ...]:
    return gate._direct_repository_snapshot(repo)


def _state_snapshot(state: Path) -> tuple[object, ...]:
    return gate._direct_state_snapshot(state)


def _stable_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(gate.CONTRACT_DIGEST_DOMAIN)
    for name in _STABLE4:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _verify_artifacts(artifacts: object) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != _EXACT5:
        _fail()
    parsed: dict[str, object] = {}
    for name, payload in artifacts.items():
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
        ):
            _fail()
        try:
            value = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(_ERROR) from error
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
        parsed[name] = value

    manifest = parsed[_EXACT5[0]]
    transitions = parsed[_EXACT5[1]]
    lineage = parsed[_EXACT5[2]]
    negatives = parsed[_EXACT5[3]]
    report = parsed[_EXACT5[4]]
    if (
        type(manifest) is not dict
        or type(transitions) is not list
        or type(lineage) is not dict
        or type(negatives) is not list
        or type(report) is not dict
        or report.get("gate_status") != _STATUS
        or report.get("contract_digest") != _stable_digest(artifacts)
        or len(transitions) != 3
        or [row.get("object_id") for row in transitions]
        != list(gate.TRANSITION_OBJECT_IDS)
        or [row.get("historical_identity", {}).get("st_dev") for row in transitions]
        != [49, 49, 49]
        or [
            row.get("authorized_current_identity", {}).get("st_dev")
            for row in transitions
        ]
        != [50, 50, 50]
        or any(row.get("transition_authorized") is not True for row in transitions)
        or [row.get("case_id") for row in negatives]
        != list(gate.NEGATIVE_CASE_IDS)
        or any(row.get("expected_result") != "fail_closed" for row in negatives)
        or report.get("negative_case_count") != len(gate.NEGATIVE_CASE_IDS)
        or lineage.get(
            "current_mount_id_or_parent_mount_id_recorded_in_stable_evidence"
        )
        is not False
    ):
        _fail()
    diagnostics = report.get("mount_namespace_diagnostics")
    readiness = report.get("readiness")
    if (
        type(diagnostics) is not dict
        or diagnostics.get("diagnostic_only") is not True
        or diagnostics.get("stable_contract_digest_participation") is not False
        or diagnostics.get("gate_admission_semantic_identity") is not False
        or type(readiness) is not dict
        or readiness.get("state_mount_device_transition_contract_gate_passed")
        is not True
        or readiness.get("ready_for_remap_predecessor_successor_integration")
        is not True
        or readiness.get(
            "ready_for_public_remap_adapter_hot_loop_contract_implementation"
        )
        is not False
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get("ready_for_model_integration") is not False
        or readiness.get("ready_for_loss_integration") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
    ):
        _fail()
    return {
        "report": report,
        "contract_digest": report["contract_digest"],
        "transition_object_count": len(transitions),
        "transition_authorized_count": sum(
            row["transition_authorized"] is True for row in transitions
        ),
        "negative_case_count": len(negatives),
        "mount_namespace_diagnostics": diagnostics,
        "readiness": readiness,
    }


def _main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repository = _root(arguments.repo_root)
    state = _root(arguments.state_root)
    _validate_repository_lineage(repository)
    lifecycle = _repository_lifecycle(repository)
    before_repository = _repository_snapshot(repository)
    before_state = _state_snapshot(state)
    first = gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
        repo_root=repository,
        state_root=state,
    )
    second = gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
        repo_root=repository,
        state_root=state,
    )
    if first != second:
        _fail()
    verified = _verify_artifacts(first)
    if (
        verified["report"].get("repository_lifecycle") != lifecycle
        or _repository_snapshot(repository) != before_repository
        or _state_snapshot(state) != before_state
    ):
        _fail()
    readiness = verified["readiness"]
    if (
        readiness["ready_for_remap_predecessor_successor_integration"] is not True
        or readiness[
            "ready_for_public_remap_adapter_hot_loop_contract_implementation"
        ]
        is not False
        or readiness["ready_for_training"] is not False
    ):
        _fail()
    summary = {
        "status": _STATUS,
        "repository_lifecycle": lifecycle,
        "contract_digest": verified["contract_digest"],
        "artifact_file_count": 5,
        "transition_object_count": verified["transition_object_count"],
        "transition_authorized_count": verified["transition_authorized_count"],
        "negative_case_count": verified["negative_case_count"],
        "public_gate_build_count": 2,
        "double_build_byte_identical": True,
        "repository_unchanged": True,
        "state_unchanged": True,
        "historical_public_gates_called": False,
        "heavy_remap_contract_chain_called": False,
        "mount_namespace_diagnostics": verified["mount_namespace_diagnostics"],
        "readiness": readiness,
    }
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
