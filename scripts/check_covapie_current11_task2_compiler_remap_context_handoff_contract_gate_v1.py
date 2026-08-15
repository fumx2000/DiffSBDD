#!/usr/bin/env python3
"""Check the Current11 Task 2 compiler/remap-context handoff contract gate V1."""

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
    covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1
    as gate,
)


_ERROR = (
    "COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
    "CONTRACT_GATE_V1_ERROR"
)
_STABLE_CONTRACT_DIGEST = (
    "7de09322699eb9529486f49f5e5c1367317d63143e967f6223b010a4ef972c78"
)
_KNOWN_VECTOR_DIGEST = (
    "bae265a068b9c7b3fcedd7edcee5946b881e1000d82b21debb22202332ac0ce5"
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


def _path_identity(path: Path) -> tuple[object, ...]:
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
    repository_paths = (
        *gate._REPOSITORY_EXACT4,
        *(str(spec["path"]) for spec in gate._OWNER_SPECS),
    )
    design = state_root / gate._DESIGN_REPORT_RELATIVE
    return (
        _run_git(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple(
            (relative, _path_identity(repo_root / relative))
            for relative in repository_paths
        ),
        _path_identity(design),
    )


def _safe_exact4(repo_root: Path) -> None:
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


def _manual_stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(
        b"COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
        b"CONTRACT_GATE_V1\0"
    )
    for name in gate._STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _compact(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _manual_known_digest(value: object) -> str:
    payload = _compact(value)
    digest = hashlib.sha256(
        b"COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
        b"KNOWN_VECTOR_V1\0"
    )
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _parse_artifacts(
    artifacts: object,
) -> dict[str, dict[str, object]]:
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
                payload.decode("utf-8"), parse_constant=lambda _value: _fail()
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
        if type(value) is not dict or expected != payload:
            _fail()
        parsed[name] = value
    return parsed


def _result(
    artifacts: dict[str, bytes], parsed: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    report = parsed[gate._REPORT]
    vectors = parsed[gate._REFERENCE_VECTORS]
    manifest = parsed[gate._MANIFEST]
    api = parsed[gate._API_AND_ERROR]
    semantic = vectors.get("known_vector_semantic")
    stable = _manual_stable_digest(artifacts)
    known = _manual_known_digest(semantic)
    readiness = report.get("readiness")
    heavy = report.get("real_heavy_call_counts")
    lifecycle = report.get("repository_lifecycle")
    if lifecycle == "precommit-untracked":
        expected_status = (
            "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_"
            "PRECOMMIT_CANDIDATE_ONLY"
        )
        expected_commit_review = True
        expected_publication = False
        expected_handoff_implementation = False
        expected_blocker = "handoff_contract_gate_not_published"
    elif lifecycle == "clean-tracked-successor":
        expected_status = (
            "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_"
            "CLEAN_TRACKED_SUCCESSOR"
        )
        expected_commit_review = False
        expected_publication = True
        expected_handoff_implementation = True
        expected_blocker = "NONE"
    else:
        _fail()
    if (
        report.get("gate_status") != expected_status
        or report.get("stable_contract_digest") != stable
        or report.get("known_vector_digest") != known
        or stable != _STABLE_CONTRACT_DIGEST
        or known != _KNOWN_VECTOR_DIGEST
        or vectors.get("known_vector_digest") != known
        or manifest.get("known_vector_digest") != known
        or report.get("design_report_identity_verified") is not True
        or report.get("predecessor_identities_verified") is not True
        or report.get("source_mapping_contract_passed") is not True
        or report.get("provider_mapping_contract_passed") is not True
        or report.get("readiness_contract_passed") is not True
        or report.get("authority_compatibility_digest_passed") is not True
        or report.get("opaque_private_handoff_contract_passed") is not True
        or report.get("single_authority_snapshot_contract_passed") is not True
        or report.get("no_old_chain_contract_passed") is not True
        or report.get("output10_parity_contract_frozen") is not True
        or report.get("device_identity_risk_resolution_contract_defined") is not True
        or report.get("device_identity_risk_resolution_runtime_proven") is not False
        or report.get("canonical_mask_exact5_passed") is not True
        or type(heavy) is not dict
        or heavy != gate._REAL_HEAVY_CALL_COUNTS
        or any(value != 0 or type(value) is not int for value in heavy.values())
        or type(readiness) is not dict
        or readiness.get(
            "ready_for_compiler_remap_context_handoff_contract_gate_commit_review"
        )
        is not expected_commit_review
        or readiness.get(
            "ready_for_compiler_remap_context_handoff_contract_gate_publication"
        )
        is not expected_publication
        or readiness.get("ready_for_compiler_remap_context_handoff_implementation")
        is not expected_handoff_implementation
        or readiness.get("compiler_remap_context_handoff_implementation_blocker")
        != expected_blocker
        or readiness.get("device_identity_risk_resolution_runtime_proven") is not False
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get("ready_for_model_integration") is not False
        or readiness.get("ready_for_loss_integration") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
        or [row.get("name") for row in api.get("future_public_exact2", [])]
        != list(gate._FUTURE_PUBLIC_EXACT2)
    ):
        _fail()
    return {
        "gate_status": report["gate_status"],
        "repository_lifecycle": report["repository_lifecycle"],
        "stable_contract_digest": stable,
        "known_vector_digest": known,
        "design_report_identity_verified": True,
        "predecessor_identities_verified": True,
        "source_mapping_contract_passed": True,
        "provider_mapping_contract_passed": True,
        "readiness_contract_passed": True,
        "authority_compatibility_digest_passed": True,
        "opaque_private_handoff_contract_passed": True,
        "single_authority_snapshot_contract_passed": True,
        "no_old_chain_contract_passed": True,
        "output10_parity_contract_frozen": True,
        "device_identity_risk_resolution_contract_defined": True,
        "device_identity_risk_resolution_runtime_proven": False,
        "canonical_mask_exact5_passed": True,
        "ready_for_compiler_remap_context_handoff_implementation": (
            readiness["ready_for_compiler_remap_context_handoff_implementation"]
        ),
        "compiler_remap_context_handoff_implementation_blocker": (
            readiness["compiler_remap_context_handoff_implementation_blocker"]
        ),
        "real_heavy_call_counts": dict(heavy),
        "readiness": dict(readiness),
    }


def _main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        repo_root = arguments.repo_root
        state_root = arguments.state_root
        _safe_exact4(repo_root)
        before = _snapshot(repo_root, state_root)
        artifacts = gate.build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
        parsed = _parse_artifacts(artifacts)
        result = _result(artifacts, parsed)
        after = _snapshot(repo_root, state_root)
        if before != after:
            _fail()
        payload = _compact(result) + b"\n"
    except Exception:
        sys.stderr.write(_ERROR + "\n")
        return 1
    sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
