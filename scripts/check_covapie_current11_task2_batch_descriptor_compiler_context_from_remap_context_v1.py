#!/usr/bin/env python3
"""Check the compiler context bridged from a published remap context V1."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import inspect
import json
import pickle
import stat
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1
    as _historical_gate,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as _bridge,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_v1 as _compiler,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1
    as _adapter_context,
)
from scripts import (
    check_covapie_current11_task2_batch_index_remap_adapter_context_v1
    as _adapter_checker,
)


sys.dont_write_bytecode = True

_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "FROM_REMAP_CONTEXT_V1_CHECK_ERROR"
)
_BASE_COMMIT = "9f6c617e7e63252e69318396b7427f23f337b206"
_BASE_SUBJECT = (
    "add CovaPIE Current11 Task2 compiler remap context handoff contract v1"
)
_EXACT4 = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1.py",
    "scripts/"
    "check_covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1.py",
    "tests/"
    "test_covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1.py",
    "docs/"
    "covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1_guide.md",
)
_PROTECTED = (
    "src/covalent_ext/"
    "covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1.py",
    _bridge._ADAPTER_CONTEXT_OWNER_MODULE,
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_v1.py",
    _bridge._COMPILER_MODULE,
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_"
    "contract_gate_v1.py",
    "src/covalent_ext/covapie_current11_runtime_batch_observation_extractor_v1.py",
)
_OUTPUT_FIELDS = tuple(_compiler._OUTPUT_FIELDS)
_SUCCESS_IDS = ("canonical", "reversed", "subset_10_4_0", "singleton_10")
_FAILURE_IDS = (
    "source_contract_override",
    "duplicate_runtime_key",
    "wrong_ligand_length",
    "wrong_ligand_membership",
    "unknown_joint_descriptor",
)
_CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)


class _CheckError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise _CheckError()


def _fail() -> NoReturn:
    raise _CheckError()


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
        raise _CheckError() from error


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
        raise _CheckError() from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _require_root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _CheckError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _safe_file(path: Path) -> dict[str, object]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
        payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise _CheckError() from error
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
    return {
        "bytes": len(payload),
        "LF": payload.count(b"\n"),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "mode": "0644",
    }


def _repository_lifecycle(repo_root: Path) -> tuple[str, dict[str, object]]:
    branch = _run_git(repo_root, ("branch", "--show-current")).strip()
    head = _run_git(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _run_git(repo_root, ("rev-parse", "origin/main")).strip()
    relation = _run_git(
        repo_root, ("rev-list", "--left-right", "--count", "HEAD...origin/main")
    ).strip()
    subject = _run_git(repo_root, ("log", "-1", "--format=%s", "HEAD")).strip()
    if branch != "main" or relation.count("\t") != 1:
        _fail()
    ahead_text, behind_text = relation.split("\t")
    if not ahead_text.isdigit() or not behind_text.isdigit():
        _fail()
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(repo_root, ("ls-files", "--stage", "--", *_EXACT4)).splitlines()
    expected = {f"?? {relative}" for relative in _EXACT4}
    if set(status) == expected and len(status) == len(_EXACT4):
        if (
            index
            or head != _BASE_COMMIT
            or origin != _BASE_COMMIT
            or ahead_text != "0"
            or behind_text != "0"
            or subject != _BASE_SUBJECT
        ):
            _fail()
        lifecycle = "precommit-untracked"
    elif not status and len(index) == len(_EXACT4):
        _run_git(repo_root, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))
        seen: set[str] = set()
        for row in index:
            try:
                metadata, relative = row.split("\t", 1)
                mode, blob, stage = metadata.split()
            except ValueError as error:
                raise _CheckError() from error
            if (
                relative not in _EXACT4
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
        if seen != set(_EXACT4):
            _fail()
        lifecycle = "clean-tracked-successor"
    else:
        _fail()
    identities = {relative: _safe_file(repo_root / relative) for relative in _EXACT4}
    return lifecycle, {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "head_subject": subject,
        "exact4": identities,
    }


def _path_identity(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_ino),
        int(metadata.st_mtime_ns),
        None if payload is None else hashlib.sha256(payload).hexdigest(),
    )


def _snapshot(repo_root: Path, state_root: Path) -> tuple[object, ...]:
    return (
        _run_git(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple(
            (relative, _path_identity(repo_root / relative))
            for relative in (*_EXACT4, *_PROTECTED)
        ),
        _adapter_checker._state_snapshot(state_root),
    )


def _acquire_remap_context(
    *,
    lifecycle: str,
    repo_root: Path,
    state_root: Path,
) -> tuple[object, dict[str, object]]:
    if lifecycle == "clean-tracked-successor":
        remap, unused_reconciliation, unused_successor, evidence = (
            _adapter_checker._acquire_clean_public_context(
                repo_root=repo_root,
                state_root=state_root,
            )
        )
        del unused_reconciliation, unused_successor
        if (
            evidence.get("test_harness_only") is not False
            or evidence.get("predecessor_public_call_counts")
            != {"reconciliation": 1, "successor": 1, "B2": 1}
            or evidence.get("formal_before_after_call_count") != 2
            or evidence.get("patch_restoration_passed") is not True
            or evidence.get("counter_wrappers_delegated_originals") is not True
            or evidence.get("production_monkeypatch_used") is not False
        ):
            _fail()
        return remap, {
            **evidence,
            "real_public_remap_context_build_performed": True,
        }
    if lifecycle != "precommit-untracked":
        _fail()
    reconciliation, successor, evidence = (
        _adapter_checker._acquire_predecessor_fixture(
            repo_root=repo_root,
            state_root=state_root,
        )
    )
    original_formal = _adapter_context._adapter_owner._validate_formal
    formal_count = 0

    def formal(canonical: Path) -> dict[str, object]:
        nonlocal formal_count
        formal_count += 1
        return original_formal(canonical)

    try:
        _adapter_context._adapter_owner._validate_formal = formal
        remap = _adapter_context._build_context_from_verified_predecessor_artifacts_v1(
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation,
            successor_artifacts=successor,
        )
    finally:
        _adapter_context._adapter_owner._validate_formal = original_formal
    restored = _adapter_context._adapter_owner._validate_formal is original_formal
    if (
        type(remap) is not _adapter_context._AdapterContext
        or evidence.get("test_harness_only") is not True
        or evidence.get("predecessor_public_call_counts")
        != {"reconciliation": 1, "successor": 1, "B2": 1}
        or evidence.get("patch_restoration_passed") is not True
        or evidence.get("production_monkeypatch_used") is not False
        or formal_count != 2
        or not restored
    ):
        _fail()
    return remap, {
        **evidence,
        "formal_before_after_call_count": formal_count,
        "private_fixture_builder_patch_restoration_passed": restored,
        "real_public_remap_context_build_performed": False,
    }


def _forbidden_counter(
    counts: dict[str, int], name: str
) -> Callable[..., NoReturn]:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        del args, kwargs
        counts[name] += 1
        _fail()

    return forbidden


def _instrument_bridge_build(remap_context: object) -> tuple[object, dict[str, int]]:
    reconciliation = _adapter_checker._reconciliation
    successor = _adapter_checker._successor
    b2 = _adapter_checker._B2
    formal_owner = _adapter_context._adapter_owner
    historical_owner = _historical_gate
    counts = {
        "adapter_private_materializer_calls": 0,
        "public_remap_context_builder_calls": 0,
        "public_remap_fast_calls": 0,
        "old_compiler_authority_calls": 0,
        "stable5_parser_calls": 0,
        "reconciliation_calls": 0,
        "successor_calls": 0,
        "B2_calls": 0,
        "formal_validation_calls": 0,
        "historical_compiler_contract_public_build_calls": 0,
        "owner_source_reads": 0,
    }
    originals = {
        "materializer": _adapter_context._validate_context_and_materialize,
        "public_builder": _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1,
        "public_fast": _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1,
        "old_authority": _compiler._authority,
        "parser": _adapter_context._parse_successor_stable5_v1,
        "reconciliation": reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1,
        "successor": successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1,
        "B2": b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1,
        "formal": formal_owner._validate_formal,
        "historical": historical_owner.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1,
        "source_read": _bridge._read_owner_source_v1,
    }
    same_object = False

    def materializer(context: object) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
        nonlocal same_object
        counts["adapter_private_materializer_calls"] += 1
        same_object = context is remap_context
        return originals["materializer"](context)

    def source_read(*args: object, **kwargs: object) -> bytes:
        counts["owner_source_reads"] += 1
        return originals["source_read"](*args, **kwargs)

    try:
        _adapter_context._validate_context_and_materialize = materializer
        _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1 = _forbidden_counter(
            counts, "public_remap_context_builder_calls"
        )
        _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1 = _forbidden_counter(
            counts, "public_remap_fast_calls"
        )
        _compiler._authority = _forbidden_counter(counts, "old_compiler_authority_calls")
        _adapter_context._parse_successor_stable5_v1 = _forbidden_counter(
            counts, "stable5_parser_calls"
        )
        reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = _forbidden_counter(
            counts, "reconciliation_calls"
        )
        successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = _forbidden_counter(
            counts, "successor_calls"
        )
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = _forbidden_counter(
            counts, "B2_calls"
        )
        formal_owner._validate_formal = _forbidden_counter(
            counts, "formal_validation_calls"
        )
        historical_owner.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 = _forbidden_counter(
            counts, "historical_compiler_contract_public_build_calls"
        )
        _bridge._read_owner_source_v1 = source_read
        context = _bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context
        )
    finally:
        _adapter_context._validate_context_and_materialize = originals["materializer"]
        _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1 = originals["public_builder"]
        _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1 = originals["public_fast"]
        _compiler._authority = originals["old_authority"]
        _adapter_context._parse_successor_stable5_v1 = originals["parser"]
        reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = originals["reconciliation"]
        successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = originals["successor"]
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = originals["B2"]
        formal_owner._validate_formal = originals["formal"]
        historical_owner.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 = originals["historical"]
        _bridge._read_owner_source_v1 = originals["source_read"]
    restored = (
        _adapter_context._validate_context_and_materialize
        is originals["materializer"]
        and _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1
        is originals["public_builder"]
        and _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1
        is originals["public_fast"]
        and _compiler._authority is originals["old_authority"]
        and _adapter_context._parse_successor_stable5_v1 is originals["parser"]
        and reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
        is originals["reconciliation"]
        and successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1
        is originals["successor"]
        and b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
        is originals["B2"]
        and formal_owner._validate_formal is originals["formal"]
        and historical_owner.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1
        is originals["historical"]
        and _bridge._read_owner_source_v1 is originals["source_read"]
    )
    expected = {
        **{key: 0 for key in counts},
        "adapter_private_materializer_calls": 1,
        "owner_source_reads": 2,
    }
    if counts != expected or not same_object or not restored:
        _fail()
    return context, counts


def _reference_vectors(
    context: object,
) -> tuple[dict[str, object], dict[str, object]]:
    source, provider, readiness = _bridge._validate_context_and_materialize_v1(
        context
    )
    snapshot, components, digest = _historical_gate._authority_snapshot(
        source, provider, readiness
    )
    if (
        type(snapshot) is not dict
        or digest != _bridge._HISTORICAL_AUTHORITY_COMPATIBILITY_DIGEST
        or components
        != {
            "provenance_component_digest": (
                "fb07d38554cec596679ab00bd80d35d392bddd60d0d07e9310439501e498a109"
            ),
            "source_component_digest": _bridge._SOURCE_COMPONENT_DIGEST,
            "provider_component_digest": _bridge._PROVIDER_COMPONENT_DIGEST,
            "readiness_component_digest": _bridge._READINESS_COMPONENT_DIGEST,
        }
    ):
        _fail()
    vectors = _historical_gate._reference_vectors(
        source, provider, readiness, digest, components
    )
    return vectors, {
        "historical_authority_compatibility_digest": digest,
        **components,
    }


def _instrument_fast_calls(
    *, context: object, vectors: Mapping[str, object]
) -> tuple[dict[str, int], dict[str, bool]]:
    parity = vectors.get("output_parity_cases")
    failures = vectors.get("representative_runtime_hard_failures")
    if type(parity) is not list or type(failures) is not list:
        _fail()
    cases = [*parity, *failures]
    counts = {
        "fast_call_count": 0,
        "compiler_kernel_calls": 0,
        "adapter_private_materializer_calls": 0,
        "public_remap_context_builder_calls": 0,
        "public_remap_fast_calls": 0,
        "old_compiler_authority_calls": 0,
        "stable5_parser_calls": 0,
        "reconciliation_calls": 0,
        "successor_calls": 0,
        "B2_calls": 0,
        "formal_validation_calls": 0,
        "historical_compiler_contract_public_build_calls": 0,
        "owner_source_reads": 0,
        "context_rebuild_calls": 0,
        "subprocess_calls": 0,
    }
    reconciliation = _adapter_checker._reconciliation
    successor = _adapter_checker._successor
    b2 = _adapter_checker._B2
    formal_owner = _adapter_context._adapter_owner
    originals = {
        "kernel": _compiler._compile_with_verified_authority_v1,
        "materializer": _adapter_context._validate_context_and_materialize,
        "public_builder": _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1,
        "public_fast": _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1,
        "old_authority": _compiler._authority,
        "parser": _adapter_context._parse_successor_stable5_v1,
        "reconciliation": reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1,
        "successor": successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1,
        "B2": b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1,
        "formal": formal_owner._validate_formal,
        "historical": _historical_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1,
        "source_read": _bridge._read_owner_source_v1,
        "rebuild": _bridge._build_context_impl_v1,
        "subprocess": subprocess.run,
    }
    parity_results: dict[str, bool] = {}

    def kernel(*, authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]], observation: object) -> dict[str, object]:
        counts["compiler_kernel_calls"] += 1
        return originals["kernel"](authority=authority, observation=observation)

    try:
        _compiler._compile_with_verified_authority_v1 = kernel
        _adapter_context._validate_context_and_materialize = _forbidden_counter(
            counts, "adapter_private_materializer_calls"
        )
        _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1 = _forbidden_counter(
            counts, "public_remap_context_builder_calls"
        )
        _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1 = _forbidden_counter(
            counts, "public_remap_fast_calls"
        )
        _compiler._authority = _forbidden_counter(counts, "old_compiler_authority_calls")
        _adapter_context._parse_successor_stable5_v1 = _forbidden_counter(
            counts, "stable5_parser_calls"
        )
        reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = _forbidden_counter(
            counts, "reconciliation_calls"
        )
        successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = _forbidden_counter(
            counts, "successor_calls"
        )
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = _forbidden_counter(
            counts, "B2_calls"
        )
        formal_owner._validate_formal = _forbidden_counter(
            counts, "formal_validation_calls"
        )
        _historical_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 = _forbidden_counter(
            counts, "historical_compiler_contract_public_build_calls"
        )
        _bridge._read_owner_source_v1 = _forbidden_counter(counts, "owner_source_reads")
        _bridge._build_context_impl_v1 = _forbidden_counter(
            counts, "context_rebuild_calls"
        )
        subprocess.run = _forbidden_counter(counts, "subprocess_calls")
        for row in cases:
            if type(row) is not dict:
                _fail()
            case_id = row.get("case_id")
            observation = row.get("observation")
            expected = row.get("existing_slow_output")
            if type(case_id) is not str or type(expected) is not dict:
                _fail()
            counts["fast_call_count"] += 1
            output = _bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
                context=context,
                observation=observation,
            )
            parity_results[case_id] = (
                type(output) is dict
                and tuple(output) == _OUTPUT_FIELDS
                and output == expected
                and output.get("readiness") == dict(_bridge._READINESS_EXACT24)
                and set(output) == set(_OUTPUT_FIELDS)
            )
    finally:
        _compiler._compile_with_verified_authority_v1 = originals["kernel"]
        _adapter_context._validate_context_and_materialize = originals["materializer"]
        _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1 = originals["public_builder"]
        _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1 = originals["public_fast"]
        _compiler._authority = originals["old_authority"]
        _adapter_context._parse_successor_stable5_v1 = originals["parser"]
        reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = originals["reconciliation"]
        successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = originals["successor"]
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = originals["B2"]
        formal_owner._validate_formal = originals["formal"]
        _historical_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 = originals["historical"]
        _bridge._read_owner_source_v1 = originals["source_read"]
        _bridge._build_context_impl_v1 = originals["rebuild"]
        subprocess.run = originals["subprocess"]
    restored = (
        _compiler._compile_with_verified_authority_v1 is originals["kernel"]
        and _adapter_context._validate_context_and_materialize
        is originals["materializer"]
        and _adapter_context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1
        is originals["public_builder"]
        and _adapter_context.remap_covapie_current11_task2_batch_index_with_context_v1
        is originals["public_fast"]
        and _compiler._authority is originals["old_authority"]
        and _adapter_context._parse_successor_stable5_v1 is originals["parser"]
        and reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
        is originals["reconciliation"]
        and successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1
        is originals["successor"]
        and b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
        is originals["B2"]
        and formal_owner._validate_formal is originals["formal"]
        and _historical_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1
        is originals["historical"]
        and _bridge._read_owner_source_v1 is originals["source_read"]
        and _bridge._build_context_impl_v1 is originals["rebuild"]
        and subprocess.run is originals["subprocess"]
    )
    if (
        counts["fast_call_count"] != len(cases)
        or counts["compiler_kernel_calls"] != len(cases)
        or any(
            value != 0
            for key, value in counts.items()
            if key not in ("fast_call_count", "compiler_kernel_calls")
        )
        or set(parity_results) != set((*_SUCCESS_IDS, *_FAILURE_IDS))
        or not all(parity_results.values())
        or not restored
    ):
        _fail()
    return counts, parity_results


def _expect_bridge_error(action: Callable[[], object]) -> bool:
    try:
        action()
    except ValueError as error:
        return str(error) == _bridge._ERROR
    return False


def _forge_context(
    context: object,
    mutate: Callable[[dict[str, object]], None] | None = None,
    *,
    valid_token: bool = True,
) -> object:
    logical = _bridge._thaw_value_v1(context._semantic)
    if type(logical) is not dict:
        _fail()
    if mutate is not None:
        mutate(logical)
    forged = object.__new__(_bridge._BridgeContextV1)
    object.__setattr__(forged, "_semantic", _bridge._freeze_value_v1(logical))
    object.__setattr__(
        forged,
        "_construction_token",
        _bridge._CONSTRUCTION_TOKEN if valid_token else object(),
    )
    return forged


def _frozen_graph_properties(
    value: object,
    *,
    forbidden_target: object,
    seen: set[int] | None = None,
) -> tuple[bool, bool]:
    if value is forbidden_target:
        return False, True
    if value is None or type(value) in (str, bool, int, float):
        return True, False
    if type(value) in (dict, list):
        return False, False
    if value is _bridge._CONSTRUCTION_TOKEN:
        return True, False
    seen = set() if seen is None else seen
    marker = id(value)
    if marker in seen:
        return True, False
    seen.add(marker)
    if type(value) is _bridge._BridgeContextV1:
        children = (value._semantic, value._construction_token)
    elif type(value) is _bridge._FrozenMapV1:
        children = value.items
    elif type(value) is _bridge._FrozenMapEntryV1:
        children = (value.key, value.value)
    elif type(value) is _bridge._FrozenListV1:
        children = value.items
    elif type(value) is tuple:
        children = value
    else:
        return False, False
    child_results = [
        _frozen_graph_properties(
            child,
            forbidden_target=forbidden_target,
            seen=seen,
        )
        for child in children
    ]
    return (
        all(immutable for immutable, unused_retained in child_results),
        any(retained for unused_immutable, retained in child_results),
    )


def _tamper_and_opacity(context: object, remap_context: object) -> dict[str, bool]:
    observation: dict[str, object] = {}

    def mutation(field: str, value: object) -> Callable[[dict[str, object]], None]:
        def apply(logical: dict[str, object]) -> None:
            logical[field] = value

        return apply

    def source_mutation(logical: dict[str, object]) -> None:
        source = logical["source_exact10"]
        if type(source) is not dict:
            _fail()
        source["source_entry_validity_bool"][0] = False

    def provider_mutation(logical: dict[str, object]) -> None:
        provider = logical["identity_provider_exact11"]
        if type(provider) is not list:
            _fail()
        provider[0]["roles"]["pocket"]["row_count"] += 1

    def readiness_mutation(logical: dict[str, object]) -> None:
        readiness = logical["readiness_template"]
        if type(readiness) is not dict:
            _fail()
        readiness["ready_for_training"] = True

    def seal_mutation(logical: dict[str, object]) -> None:
        logical["construction_seal"] = "0" * 64

    tampered = {
        "wrong_type": object(),
        "schema_corruption": _forge_context(
            context, mutation("context_schema_version", "wrong")
        ),
        "contract_corruption": _forge_context(
            context, mutation("context_contract_version", "wrong")
        ),
        "adapter_owner_sha_corruption": _forge_context(
            context, mutation("adapter_context_owner_source_sha256", "0" * 64)
        ),
        "compiler_sha_corruption": _forge_context(
            context, mutation("compiler_source_sha256", "0" * 64)
        ),
        "source_corruption": _forge_context(context, source_mutation),
        "provider_corruption": _forge_context(context, provider_mutation),
        "readiness_corruption": _forge_context(context, readiness_mutation),
        "compatibility_digest_corruption": _forge_context(
            context,
            mutation("historical_authority_compatibility_digest", "0" * 64),
        ),
        "seal_corruption": _forge_context(context, seal_mutation),
        "construction_token_corruption": _forge_context(
            context, valid_token=False
        ),
        "reconstructed_context": _forge_context(context, valid_token=False),
    }
    results = {
        name: _expect_bridge_error(
            lambda candidate=candidate: _bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
                context=candidate,
                observation=observation,
            )
        )
        for name, candidate in tampered.items()
    }
    wrong_frozen = object.__new__(_bridge._BridgeContextV1)
    object.__setattr__(wrong_frozen, "_semantic", {})
    object.__setattr__(
        wrong_frozen, "_construction_token", _bridge._CONSTRUCTION_TOKEN
    )
    results["wrong_frozen_graph"] = _expect_bridge_error(
        lambda: _bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            context=wrong_frozen,
            observation=observation,
        )
    )
    results["adapter_context_wrong_type_builder_reject"] = _expect_bridge_error(
        lambda: _bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=object()
        )
    )
    for name, action in {
        "copy_rejected": lambda: copy.copy(context),
        "deepcopy_rejected": lambda: copy.deepcopy(context),
        "pickle_rejected": lambda: pickle.dumps(context),
        "reduce_rejected": lambda: context.__reduce__(),
        "reduce_ex_rejected": lambda: context.__reduce_ex__(4),
    }.items():
        try:
            action()
        except (TypeError, pickle.PickleError):
            results[name] = True
        else:
            results[name] = False
    results["public_context_class_absent"] = (
        all(not inspect.isclass(getattr(_bridge, name)) for name in _bridge.__all__)
        and "_BridgeContextV1" not in _bridge.__all__
    )
    results["logical_exact20"] = (
        tuple(_bridge._logical_context_value_v1(context))
        == _bridge._LOGICAL_FIELD_ORDER
    )
    immutable, retained = _frozen_graph_properties(
        context,
        forbidden_target=remap_context,
    )
    results["caller_remap_context_retained"] = retained
    results["reachable_builtin_mutable"] = not immutable
    if (
        results["caller_remap_context_retained"]
        or results["reachable_builtin_mutable"]
        or not all(
            value
            for key, value in results.items()
            if key not in (
                "caller_remap_context_retained",
                "reachable_builtin_mutable",
            )
        )
    ):
        _fail()
    return results


def _static_architecture(repo_root: Path) -> dict[str, bool]:
    source = (repo_root / _EXACT4[0]).read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=_EXACT4[0])
    except SyntaxError as error:
        raise _CheckError() from error
    covalent_imports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            covalent_imports.extend(alias.name for alias in node.names)
    allowed = {
        "covapie_current11_task2_batch_index_remap_adapter_context_v1",
        "covapie_current11_task2_batch_descriptor_compiler_v1",
    }
    functions = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    forbidden_fragments = (
        "compiler_remap_context_handoff_contract_gate_v1",
        "batch_descriptor_compiler_context_contract_gate_v1",
        "batch_descriptor_compiler_context_v1 as",
        "predecessor_successor",
        "semantic_reconciliation",
        "state_mount_device_transition",
        "DataLoader",
        "lightning_modules",
        "equivariant_diffusion",
    )
    result = {
        "only_two_covalent_owner_imports": (
            len(covalent_imports) == 2 and set(covalent_imports) == allowed
        ),
        "forbidden_imports_absent": not any(
            fragment in source for fragment in forbidden_fragments
        ),
        "old_authority_not_defined": "_authority" not in functions,
        "stable5_parser_not_defined": "_parse_successor_stable5_v1" not in functions,
        "global_cache_absent": (
            "lru_cache" not in source
            and "functools.cache" not in source
            and "_CACHE" not in source
        ),
        "builder_references_materializer": (
            "_adapter_context._validate_context_and_materialize" in source
        ),
        "fast_references_compiler_kernel": (
            "_compiler._compile_with_verified_authority_v1" in source
        ),
    }
    if not all(result.values()):
        _fail()
    return result


def _readiness_profile(
    lifecycle: str,
    *,
    acquisition: Mapping[str, object],
    bridge_counts: Mapping[str, int],
    fast_counts: Mapping[str, int],
    same_object_consumed: bool,
) -> dict[str, bool]:
    if lifecycle not in ("precommit-untracked", "clean-tracked-successor"):
        _fail()
    clean = lifecycle == "clean-tracked-successor"
    acquisition_counts = acquisition.get("predecessor_public_call_counts")
    runtime_proven = (
        clean
        and acquisition.get("real_public_remap_context_build_performed") is True
        and acquisition.get("test_harness_only") is False
        and acquisition_counts == {"reconciliation": 1, "successor": 1, "B2": 1}
        and acquisition.get("formal_before_after_call_count") == 2
        and same_object_consumed
        and bridge_counts.get("adapter_private_materializer_calls") == 1
        and all(
            bridge_counts.get(key) == 0
            for key in (
                "public_remap_context_builder_calls",
                "public_remap_fast_calls",
                "old_compiler_authority_calls",
                "stable5_parser_calls",
                "reconciliation_calls",
                "successor_calls",
                "B2_calls",
                "formal_validation_calls",
                "historical_compiler_contract_public_build_calls",
            )
        )
        and all(
            fast_counts.get(key) == 0
            for key in fast_counts
            if key not in ("fast_call_count", "compiler_kernel_calls")
        )
        and fast_counts.get("fast_call_count")
        == fast_counts.get("compiler_kernel_calls")
    )
    return {
        "device_identity_risk_resolution_contract_defined": True,
        "device_identity_risk_resolution_runtime_proven": runtime_proven,
        "ready_for_bridge_commit_review": not clean,
        "ready_for_bridge_publication": clean and runtime_proven,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _api_contract() -> dict[str, object]:
    build = _bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    compile_fast = _bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1
    if (
        _bridge.__all__ != (build.__name__, compile_fast.__name__)
        or str(inspect.signature(build))
        != "(*, remap_context: 'object') -> 'object'"
        or str(inspect.signature(compile_fast))
        != (
            "(*, context: 'object', observation: 'dict[str, object]') -> "
            "'dict[str, object]'"
        )
    ):
        _fail()
    return {
        "public_names": list(_bridge.__all__),
        "build_signature": str(inspect.signature(build)),
        "compile_signature": str(inspect.signature(compile_fast)),
        "error_token": _bridge._ERROR,
    }


def _audit(*, repo_root: Path, state_root: Path) -> dict[str, object]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    lifecycle, repository_evidence = _repository_lifecycle(repository)
    before = _snapshot(repository, state)
    api = _api_contract()
    architecture = _static_architecture(repository)
    remap_context, acquisition = _acquire_remap_context(
        lifecycle=lifecycle,
        repo_root=repository,
        state_root=state,
    )
    context, bridge_counts = _instrument_bridge_build(remap_context)
    vectors, compatibility = _reference_vectors(context)
    fast_counts, parity = _instrument_fast_calls(
        context=context,
        vectors=vectors,
    )
    tamper = _tamper_and_opacity(context, remap_context)
    peer = _bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
        remap_context=remap_context
    )
    logical = _bridge._logical_context_value_v1(context)
    peer_logical = _bridge._logical_context_value_v1(peer)
    deterministic = (
        peer is not context
        and peer_logical == logical
        and peer_logical["construction_seal"] == logical["construction_seal"]
    )
    if not deterministic or _snapshot(repository, state) != before:
        _fail()
    readiness = _readiness_profile(
        lifecycle,
        acquisition=acquisition,
        bridge_counts=bridge_counts,
        fast_counts=fast_counts,
        same_object_consumed=True,
    )
    expected_runtime_proven = lifecycle == "clean-tracked-successor"
    if (
        readiness["device_identity_risk_resolution_runtime_proven"]
        is not expected_runtime_proven
        or readiness["ready_for_bridge_publication"] is not expected_runtime_proven
        or readiness["ready_for_dataloader_integration"] is not False
        or readiness["ready_for_training"] is not False
    ):
        _fail()
    success_parity = {name: parity[name] for name in _SUCCESS_IDS}
    failure_parity = {name: parity[name] for name in _FAILURE_IDS}
    return {
        "status": (
            "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_PRECOMMIT_CANDIDATE_ONLY"
            if lifecycle == "precommit-untracked"
            else "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_RUNTIME_ONLY"
        ),
        "repository_lifecycle": lifecycle,
        "repository": repository_evidence,
        "bridge_implemented": True,
        "public_exact2_verified": True,
        "public_api": api,
        "production_dependencies_verified": architecture,
        "logical_exact20_verified": True,
        "seal_verified": True,
        "source_exact10_verified": True,
        "provider_exact11_verified": True,
        "readiness_exact24_verified": True,
        "authority_compatibility_verified": True,
        "authority_compatibility_evidence": compatibility,
        "real_public_remap_context_build_performed": acquisition[
            "real_public_remap_context_build_performed"
        ],
        "remap_context_acquisition_evidence": acquisition,
        "bridge_build_call_counts": bridge_counts,
        "fast_call_counts": fast_counts,
        "fast_compiler_kernel_calls_per_call": 1,
        "bridge_build_patch_restoration_passed": True,
        "fast_patch_restoration_passed": True,
        "success_parity_case_count": len(success_parity),
        "hard_failure_parity_case_count": len(failure_parity),
        "success_output10_parity": success_parity,
        "hard_failure_output10_parity": failure_parity,
        "whole_output10_parity": (
            all(success_parity.values()) and all(failure_parity.values())
        ),
        "output10_field_order": list(_OUTPUT_FIELDS),
        "output10_readiness_exact24": True,
        "output10_bridge_metadata_added": False,
        "caller_remap_context_retained": False,
        "context_deep_immutable": True,
        "construction_seal_deterministic": deterministic,
        "distinct_bridge_object_identity": peer is not context,
        "tamper_and_opacity": tamper,
        "device_identity_risk_resolution_contract_defined": readiness[
            "device_identity_risk_resolution_contract_defined"
        ],
        "device_identity_risk_resolution_runtime_proven": readiness[
            "device_identity_risk_resolution_runtime_proven"
        ],
        "production_monkeypatch_used": False,
        "ready_for_bridge_commit_review": readiness[
            "ready_for_bridge_commit_review"
        ],
        "ready_for_bridge_publication": readiness[
            "ready_for_bridge_publication"
        ],
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in _CANONICAL_MASKS
        ],
        "checkpoint_bytes_read": False,
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
        "repository_snapshot_unchanged": True,
        "state_formal_snapshot_unchanged": True,
        "commit_created": False,
        "push_performed": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    return parser


def _main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        result = _audit(
            repo_root=arguments.repo_root,
            state_root=arguments.state_root,
        )
        payload = _compact(result) + b"\n"
    except Exception:
        sys.stderr.write(_ERROR + "\n")
        return 1
    sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
