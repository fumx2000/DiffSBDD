#!/usr/bin/env python3
"""Check the Current11 Task 2 runtime-caller contract gate V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Mapping, NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_runtime_caller_contract_gate_v1 as gate,
)


_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1_CHECK_ERROR"
_STABLE_CONTRACT_DIGEST = (
    "098c66343e2e924ea75ce6619cac7aa9b46baabd7f0143e80e652764660a1c20"
)


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


def _identity(path: Path) -> tuple[object, ...]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    except OSError as error:
        raise ValueError(_ERROR) from error
    return (
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_ino),
        int(metadata.st_mtime_ns),
        None if payload is None else hashlib.sha256(payload).hexdigest(),
    )


def _snapshot(repo_root: Path, state_root: Path) -> tuple[object, ...]:
    paths = (
        *gate._REPOSITORY_EXACT4,
        *(str(spec["path"]) for spec in gate._OWNER_SPECS),
    )
    return (
        _run_git(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple((relative, _identity(repo_root / relative)) for relative in paths),
        _identity(state_root / gate._DESIGN_REPORT_RELATIVE),
    )


def _safe_exact4(repo_root: Path) -> list[dict[str, object]]:
    identities: list[dict[str, object]] = []
    for relative in gate._REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
            payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
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
        identities.append(
            {
                "path": relative,
                "mode": "0644",
                "bytes": len(payload),
                "LF": payload.count(b"\n"),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return identities


def _parse_artifacts(artifacts: object) -> dict[str, dict[str, object]]:
    if type(artifacts) is not dict or tuple(artifacts) != gate._ARTIFACT_NAMES:
        _fail()
    parsed: dict[str, dict[str, object]] = {}
    for name, payload in artifacts.items():
        if (
            type(name) is not str
            or type(payload) is not bytes
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or b"\0" in payload
            or b"\r" in payload
        ):
            _fail()
        try:
            value = json.loads(
                payload.decode("utf-8"), parse_constant=lambda unused: _fail()
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(_ERROR) from error
        expected = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        if type(value) is not dict or payload != expected:
            _fail()
        parsed[name] = value
    return parsed


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(
        b"COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1\0"
    )
    for name in gate._STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate(parsed: Mapping[str, Mapping[str, object]], stable: str) -> None:
    manifest = parsed[gate._MANIFEST]
    framework = parsed[gate._FRAMEWORK]
    schema = parsed[gate._RESULT_SCHEMA]
    routing = parsed[gate._ROUTING]
    lifecycle = parsed[gate._LIFECYCLE]
    acceptance = parsed[gate._ACCEPTANCE]
    report = parsed[gate._REPORT]
    readiness = lifecycle.get("readiness")
    snapshot = framework.get("corroborating_engineering_environment_snapshot", {})
    repository_lifecycle = manifest.get("repository_lifecycle_contract", {})
    programming = routing.get("programming_error", {})
    invariants = routing.get("status_failure_reason_invariants", {})
    compiler_failure = routing.get("compiler_failure", {})
    remap_failure = routing.get("remap_failure", {})
    if (
        stable != _STABLE_CONTRACT_DIGEST
        or report.get("stable_contract_digest") != stable
        or manifest.get("selected_architecture") != gate._ARCHITECTURE
        or manifest.get("repository_exact4") != list(gate._REPOSITORY_EXACT4)
        or framework.get("repository_declared_environment", {}).get(
            "pytorch_lightning"
        )
        != "1.8.4"
        or snapshot.get("pytorch_lightning") != "2.6.5"
        or snapshot.get("snapshot_scope") != "design_audit_observation_only"
        or snapshot.get("dependency_authority") is not False
        or snapshot.get("runtime_execution_environment_requirement") is not False
        or snapshot.get("checker_current_environment_claim") is not False
        or framework.get("current_environment_exact_version_required") is not False
        or framework.get("current_environment_not_required") is not True
        or framework.get("audited_order")
        != [
            "DataLoader_output",
            "on_before_batch_transfer",
            "transfer_batch_to_device",
            "on_after_batch_transfer",
            "training_validation_test_step",
        ]
        or framework.get("single_device_supported_scope") is not True
        or framework.get("DDP_supported_scope") is not True
        or framework.get("DataParallel_not_supported_by_this_v1") is not True
        or framework.get("current_predict_integration_proven") is not False
        or schema.get("field_order") != list(gate._RESULT_FIELDS)
        or schema.get("terminal_classes") != list(gate._TERMINAL_CLASSES)
        or routing.get("caller_programming_error_token") != gate._CALLER_ERROR
        or routing.get("compiler_overall_success_status")
        != gate._COMPILER_OVERALL_SUCCESS_STATUS
        or routing.get("compiler_component_only_non_overall_statuses")
        != list(gate._COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES)
        or routing.get("compiler_structured_failure_statuses")
        != list(gate._COMPILER_STRUCTURED_FAILURE_STATUSES)
        or routing.get("remap_overall_success_status")
        != gate._REMAP_OVERALL_SUCCESS_STATUS
        or routing.get("remap_non_overall_statuses")
        != list(gate._REMAP_NON_OVERALL_STATUSES)
        or routing.get("remap_structured_failure_statuses")
        != list(gate._REMAP_STRUCTURED_FAILURE_STATUSES)
        or routing.get("known_but_non_overall_status_seen_as_overall")
        != "programming_error"
        or compiler_failure.get("compiler_status_must_be_in")
        != list(gate._COMPILER_STRUCTURED_FAILURE_STATUSES)
        or remap_failure.get("remap_status_must_be_in")
        != list(gate._REMAP_STRUCTURED_FAILURE_STATUSES)
        or routing.get("compiler_success_exact18_field_order")
        != routing.get("remap_input_exact18_field_order")
        or invariants.get("compiler_success_failure_reason_required") != "NONE"
        or invariants.get("compiler_failure_reason_must_equal_compiler_status")
        is not True
        or invariants.get("remap_success_failure_reason_required") != "NONE"
        or invariants.get("remap_failure_reason_must_equal_remap_status") is not True
        or invariants.get("status_failure_reason_inconsistency")
        != "programming_error"
        or programming.get("caller_normalizes_Exception") is not True
        or programming.get("caller_catches_BaseException") is not False
        or programming.get("keyboard_interrupt_not_normalized_by_caller") is not True
        or repository_lifecycle.get(
            "clean_tracked_successor_requires_HEAD_equals_origin_main"
        )
        is not True
        or repository_lifecycle.get("committed_unpushed_successor_rejected")
        is not True
        or lifecycle.get("canonical_mask_count") != 5
        or lifecycle.get("canonical_masks", [])[3]
        != {"semantic_long_name": "scaffold_only", "display_alias": "B3"}
        or readiness != gate._READINESS
        or acceptance.get("all_passed") is not True
        or any(row.get("passed") is not True for row in acceptance.get("cases", ()))
        or report.get("Option_B_retained") is not True
        or report.get("persistent_artifacts_written") != 0
    ):
        _fail()


def _main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repo_root = gate._require_root(arguments.repo_root)
    state_root = gate._require_root(arguments.state_root)
    before = _snapshot(repo_root, state_root)
    exact4 = _safe_exact4(repo_root)
    artifacts = gate.build_covapie_current11_task2_runtime_caller_contract_gate_v1(
        repo_root=repo_root,
        state_root=state_root,
    )
    parsed = _parse_artifacts(artifacts)
    stable = _stable_digest(artifacts)
    _validate(parsed, stable)
    after = _snapshot(repo_root, state_root)
    if before != after:
        _fail()
    report = parsed[gate._REPORT]
    framework = parsed[gate._FRAMEWORK]
    snapshot = framework["corroborating_engineering_environment_snapshot"]
    result = {
        "status": report["status"],
        "repository_lifecycle": report["repository_lifecycle"],
        "stable_contract_digest": stable,
        "selected_architecture": gate._ARCHITECTURE,
        "selected_lightning_insertion_point": gate._INSERTION_POINT,
        "selected_insertion_point_claim": gate._INSERTION_CLAIM,
        "Option_B_retained": True,
        "repository_declared_pytorch_lightning": framework[
            "repository_declared_environment"
        ]["pytorch_lightning"],
        "corroborating_audit_snapshot_pytorch_lightning": snapshot[
            "pytorch_lightning"
        ],
        "current_environment_exact_version_required": False,
        "current_environment_not_required": True,
        "clean_tracked_successor_requires_HEAD_equals_origin_main": True,
        "committed_unpushed_successor_rejected": True,
        "compiler_status_failure_reason_invariant_frozen": True,
        "remap_status_failure_reason_invariant_frozen": True,
        "compiler_overall_status_eligibility_frozen": True,
        "remap_overall_status_eligibility_frozen": True,
        "known_but_non_overall_status_rejected": True,
        "caller_catches_BaseException": False,
        "KeyboardInterrupt_not_normalized": True,
        "single_device_supported_scope": True,
        "DDP_supported_scope": True,
        "DataParallel_not_supported_by_this_v1": True,
        "runtime_result_exact_field_count": 11,
        "terminal_class_count": 5,
        "repository_exact4_identities": exact4,
        **gate._READINESS,
        "persistent_artifacts_written": 0,
    }
    sys.stdout.buffer.write(
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        sys.stderr.write(_ERROR + "\n")
        raise SystemExit(1)
