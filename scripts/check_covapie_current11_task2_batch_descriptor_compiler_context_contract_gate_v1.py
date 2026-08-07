#!/usr/bin/env python3
"""Check the Current11 Task 2 compiler-context contract gate V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 as gate  # noqa: E402


_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "CONTRACT_GATE_V1_ERROR"
)
_BASE_COMMIT = "463c481b65a68442f19b9f1b417ce2325434785f"
_CARRIER_RELATIVE = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1"
)
_ROUTING_RELATIVE = Path(
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_CARRIER_AGGREGATE = (
    "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
)
_NPZ = "current11_runtime_sample_and_role_order_carrier.npz"
_NPZ_SHA256 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)
_ROUTING_SNAPSHOT = (
    "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
)
_ROUTING_AGGREGATE = (
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
)
_EXACT4 = gate._REPOSITORY_EXACT4
_EXACT6 = gate._ARTIFACT_NAMES


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        raise ValueError(_ERROR)
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if resolved != path or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(_ERROR)
    return path


def _run_git(repo: Path, arguments: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if completed.returncode != 0 or completed.stderr:
        raise ValueError(_ERROR)
    return completed.stdout


def _validate_repository_lineage(repo: Path) -> None:
    if _run_git(repo, ("branch", "--show-current")).strip() != "main":
        raise ValueError(_ERROR)
    _run_git(repo, ("cat-file", "-e", f"{_BASE_COMMIT}^{{commit}}"))
    _run_git(repo, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))


def _repository_lifecycle(repo: Path) -> str:
    status = _run_git(
        repo, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(repo, ("ls-files", "--stage", "--", *_EXACT4)).splitlines()
    expected_untracked = {f"?? {path}" for path in _EXACT4}
    if set(status) == expected_untracked and len(status) == len(_EXACT4):
        if index:
            raise ValueError(_ERROR)
        return "precommit-untracked"
    if status:
        raise ValueError(_ERROR)
    if len(index) != len(_EXACT4):
        raise ValueError(_ERROR)
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
            or _run_git(repo, ("hash-object", "--no-filters", relative)).strip() != blob
            or _run_git(repo, ("rev-parse", f"HEAD:{relative}")).strip() != blob
        ):
            raise ValueError(_ERROR)
        seen.add(relative)
    if seen != set(_EXACT4):
        raise ValueError(_ERROR)
    return "clean-tracked-successor"


def _repository_snapshot(repo: Path) -> tuple[str, ...]:
    return (
        _run_git(repo, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo, ("diff", "--name-status")),
        _run_git(repo, ("diff", "--cached", "--name-status")),
        _run_git(repo, ("rev-parse", "HEAD")),
        _run_git(repo, ("rev-parse", "origin/main")),
    )


def _path_identity(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    if stat.S_ISREG(metadata.st_mode):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        digest = None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        digest,
    )


def _alias_snapshot(canonical: Path) -> tuple[object, ...]:
    try:
        link = os.readlink(canonical)
        target = canonical.parent / link
        inventory = tuple(sorted(os.listdir(target)))
        return (
            _path_identity(canonical),
            link,
            _path_identity(target),
            inventory,
            tuple((name, _path_identity(target / name)) for name in inventory),
        )
    except OSError as error:
        raise ValueError(_ERROR) from error


def _formal_snapshot(state: Path) -> tuple[object, ...]:
    carrier = state / _CARRIER_RELATIVE
    routing = state / _ROUTING_RELATIVE
    carrier_snapshot = _alias_snapshot(carrier)
    routing_snapshot = _alias_snapshot(routing)
    if (
        _CARRIER_AGGREGATE not in str(carrier_snapshot[1])
        or _ROUTING_AGGREGATE not in str(routing_snapshot[1])
        or hashlib.sha256((carrier / _NPZ).read_bytes()).hexdigest() != _NPZ_SHA256
    ):
        raise ValueError(_ERROR)
    return carrier_snapshot, routing_snapshot


def _verify_artifacts(artifacts: object) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != _EXACT6:
        raise ValueError(_ERROR)
    parsed: dict[str, dict[str, object]] = {}
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
            raise ValueError(_ERROR)
        parsed[name] = gate._strict_json(payload)
    manifest = parsed[gate._MANIFEST]
    schema = parsed[gate._SCHEMA]
    api = parsed[gate._API]
    vectors = parsed[gate._VECTORS]
    acceptance = parsed[gate._ACCEPTANCE]
    report = parsed[gate._REPORT]
    snapshot = schema.get("canonical_semantic_snapshot")
    if (
        report.get("gate_status") != "PASS_CONTRACT_ONLY"
        or report.get("contract_digest") != gate._stable_digest(artifacts)
        or type(snapshot) is not dict
        or report.get("authority_snapshot_digest")
        != gate._framed_semantic_digest(gate._AUTHORITY_DOMAIN, snapshot)
        or manifest.get("predecessor_base_commit") != _BASE_COMMIT
        or manifest.get("repository_lifecycle_contract", {}).get(
            "origin_main_used_for_admission"
        )
        is not False
        or schema.get("context_schema_version") != gate._CONTEXT_SCHEMA
        or schema.get("reachable_builtin_dict_or_list_allowed") is not False
        or api.get("future_context_module", {}).get("__all__")
        != [gate._BUILD_API, gate._FAST_API]
        or api.get("existing_compiler_module", {}).get("__all__")
        != [gate._SLOW_API]
        or [row.get("case_id") for row in vectors.get("output_parity_cases", [])]
        != list(gate._PARITY_CASE_IDS)
        or [
            row.get("case_id")
            for row in vectors.get("representative_runtime_hard_failures", [])
        ]
        != list(gate._HARD_FAILURE_CASE_IDS)
        or acceptance.get("acceptance_count") != 16
        or report.get("live_authority_build_count") != 1
        or report.get("live_authority_verified") is not True
        or report.get("identity_provider_sample_count") != 11
        or report.get("identity_provider_role_count") != 22
    ):
        raise ValueError(_ERROR)
    readiness = report.get("readiness")
    if (
        type(readiness) is not dict
        or readiness.get(
            "ready_for_compiler_hot_loop_authority_context_implementation"
        )
        is not True
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get(
            "public_remap_adapter_hot_loop_audit_required_before_dataloader_integration"
        )
        is not True
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
    ):
        raise ValueError(_ERROR)
    return report


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    repo = _root(namespace.repo_root)
    state = _root(namespace.state_root)
    _validate_repository_lineage(repo)
    lifecycle_before = _repository_lifecycle(repo)
    repository_before = _repository_snapshot(repo)
    formal_before = _formal_snapshot(state)
    started = time.perf_counter()
    artifacts = gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
        repo_root=repo, state_root=state
    )
    live_authority_single_run_seconds = time.perf_counter() - started
    report = _verify_artifacts(artifacts)
    repository_unchanged = _repository_snapshot(repo) == repository_before
    formal_unchanged = _formal_snapshot(state) == formal_before
    lifecycle_after = _repository_lifecycle(repo)
    if (
        lifecycle_after != lifecycle_before
        or repository_unchanged is not True
        or formal_unchanged is not True
    ):
        raise ValueError(_ERROR)
    summary = {
        "status": "PASS_CONTRACT_ONLY",
        "contract_digest": report["contract_digest"],
        "authority_snapshot_digest": report["authority_snapshot_digest"],
        "provenance_component_digest": report["provenance_component_digest"],
        "source_component_digest": report["source_component_digest"],
        "provider_component_digest": report["provider_component_digest"],
        "readiness_component_digest": report["readiness_component_digest"],
        "provider_digest": report["provider_digest"],
        "source_contract_digest": report["source_contract_digest"],
        "formal_carrier_aggregate": report["formal_carrier_aggregate"],
        "formal_npz_sha256": report["formal_npz_sha256"],
        "artifact_identities": report["artifact_identities"],
        "live_authority_build_count": report["live_authority_build_count"],
        "live_authority_verified": report["live_authority_verified"],
        "live_authority_single_run_seconds": live_authority_single_run_seconds,
        "repository_lifecycle": lifecycle_after,
        "repository_unchanged": repository_unchanged,
        "formal_carrier_and_routing_unchanged": formal_unchanged,
        "formal_routing_snapshot": _ROUTING_SNAPSHOT,
        "formal_routing_aggregate": _ROUTING_AGGREGATE,
        "readiness": report["readiness"],
    }
    sys.stdout.write(
        json.dumps(
            summary,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except BaseException as error:
        if type(error) is SystemExit and type(error.code) is int and error.code == 0:
            raise
        sys.stderr.write(_ERROR + "\n")
        raise SystemExit(1) from None
