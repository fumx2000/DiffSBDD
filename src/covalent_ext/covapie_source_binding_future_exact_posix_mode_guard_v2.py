"""Fail-closed guard against future exact-POSIX source identity.

Unchanged history is governed by the published Phase-B3 immutability proof.
This module statically classifies only relevant paths added or changed after
that proof's commit, including relevant worktree and ordinary-untracked files.
It is read-only and deliberately does not materialize a report.
"""

from __future__ import annotations

import ast
from collections import Counter
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import NoReturn

from covalent_ext import (
    covapie_source_binding_historical_immutability_proof_v2 as historical_v2,
)
from covalent_ext import covapie_source_binding_policy_v2 as source_binding_v2


__all__ = (
    "SourceBindingFutureExactPosixModeGuardV2Error",
    "verify_covapie_source_binding_future_exact_posix_mode_guard_v2",
)


_ERROR_PREFIX = "COVAPIE_SOURCE_BINDING_FUTURE_EXACT_POSIX_MODE_GUARD_V2_ERROR"
_SCHEMA_VERSION = "covapie_source_binding_future_exact_posix_mode_guard_v2"
_FUTURE_GUARD_BASELINE_COMMIT = "54f98c41e2dc34d816a17242292ee2379e99783e"
_FUTURE_GUARD_BASELINE_TREE = "ba92ef88433c8290285dacf482ed17300753fbab"
_FUTURE_GUARD_BASELINE_SUBJECT = (
    "add CovaPIE source binding historical immutability proof v2"
)
_MAX_TEXT_BYTES = 1024 * 1024

_PRODUCTION_RELATIVE = (
    "src/covalent_ext/"
    "covapie_source_binding_future_exact_posix_mode_guard_v2.py"
)
_CHECKER_RELATIVE = (
    "scripts/check_covapie_source_binding_future_exact_posix_mode_guard_v2.py"
)
_LEGACY_CONTROL_RELATIVE = (
    "src/covalent_ext/"
    "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py"
)

_FROZEN_DEPENDENCIES = (
    (
        "SOURCE_BINDING_POLICY_V2",
        "src/covalent_ext/covapie_source_binding_policy_v2.py",
        3704,
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    ),
    (
        "SOURCE_BINDING_HISTORICAL_IMMUTABILITY_PROOF_V2",
        "src/covalent_ext/covapie_source_binding_historical_immutability_proof_v2.py",
        35903,
        "0457d641ba313021c481a5817fda8a04c76cdbf1aafe462044edbf2049e6f43d",
    ),
    (
        "SOURCE_BINDING_HISTORICAL_IMMUTABILITY_PROOF_V2_CHECKER",
        "scripts/check_covapie_source_binding_historical_immutability_proof_v2.py",
        43229,
        "e502eeb1e60ed25838101ab3a74cd7b2381727a40bf1a1437b790beb1cf26332",
    ),
)

_SEMANTIC_SOURCE_IDENTITY = "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
_SECURITY_HYGIENE = "SECURITY_HYGIENE_MODE_CHECK"
_CANDIDATE_HYGIENE = "CANDIDATE_ARTIFACT_MODE_HYGIENE"
_GIT_OR_EXECUTABLE_CLASS = "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT"
_REPORTING_DIAGNOSTIC = "REPORTING_OR_DIAGNOSTIC_MODE_METADATA"
_AMBIGUOUS = "AMBIGUOUS_REQUIRES_HUMAN_REVIEW"
_SEMANTIC_CLASSES = (
    _SEMANTIC_SOURCE_IDENTITY,
    _SECURITY_HYGIENE,
    _CANDIDATE_HYGIENE,
    _GIT_OR_EXECUTABLE_CLASS,
    _REPORTING_DIAGNOSTIC,
    _AMBIGUOUS,
)

_EXACT_MODE_INTS = frozenset({0o600, 0o644, 0o664, 0o755})
_CANDIDATE_SAFE_MODE_INTS = frozenset({0o644, 0o664})
_FULL_MODE_MASKS = frozenset({0o777, 0o7777})
_GIT_MODE_INTS = frozenset({100644, 100755})
_MODE_KEYS = frozenset({"mode", "expected_mode", "filesystem_mode", "posix_mode"})
_EXPECTED_MODE_AUTHORITY_KEYS = _MODE_KEYS | frozenset({"historical_mode"})
_IDENTITY_KEYS = frozenset({"path", "path_namespace", "byte_count", "sha256"})
_SECURITY_ATTRIBUTES = frozenset(
    {
        "S_IWOTH",
        "S_IRUSR",
        "S_ISREG",
        "S_ISLNK",
        "S_ISDIR",
        "S_IFMT",
    }
)
_GIT_CONTEXT_TERMS = (
    "git_mode",
    "git mode",
    "ls-tree",
    "ls_files",
    "ls-files",
    "path_modes",
    "file_class",
    "blob class",
)
_CANDIDATE_CONTEXT_TERMS = (
    "artifact_hygiene",
    "artifact hygiene",
    "file_hygiene",
    "file hygiene",
    "exact4_hygiene",
    "publication_hygiene",
    "output_hygiene",
)
_SOURCE_CONTEXT_TERMS = (
    "source_binding",
    "source binding",
    "source_identity",
    "source identity",
    "bound_source",
    "authority_binding",
    "binding[",
    "expected_mode",
    "source_mode_drift",
    "source_identity_invalid",
    "scientific_identity",
    "content_identity",
)
_OCTAL_POSIX_LITERAL_RE = re.compile(
    r"(?<![A-Za-z0-9_])0o([0-7]{3,4})(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_TEXT_MODE_SIGNAL = re.compile(
    r"S_IMODE|st_mode\s*&\s*0o?7777?|expected_mode|"
    r"(?:binding|record)\s*\[\s*[\"']mode[\"']\s*\]|"
    r"\b(?:0?[0-7]{3}|0o[0-7]{3,4})\b"
)


class SourceBindingFutureExactPosixModeGuardV2Error(ValueError):
    """Raised when the future guard cannot prove a clean, bounded state."""


def _fail(reason: str) -> NoReturn:
    raise SourceBindingFutureExactPosixModeGuardV2Error(
        f"{_ERROR_PREFIX}:{reason}"
    )


def _validate_relative_path(relative: str) -> None:
    pure = PurePosixPath(relative)
    if (
        not relative
        or pure.is_absolute()
        or ".." in pure.parts
        or "\x00" in relative
        or "\n" in relative
        or "\r" in relative
    ):
        _fail("PATH_INVALID:" + relative)


def _is_relevant(relative: str) -> bool:
    _validate_relative_path(relative)
    if relative.startswith("src/covalent_ext/") and relative.endswith(".py"):
        return True
    if "/" not in relative.removeprefix("scripts/") and relative.startswith(
        "scripts/check_covapie"
    ) and relative.endswith(".py"):
        return True
    if "/" not in relative.removeprefix("tests/") and relative.startswith(
        "tests/test_covapie"
    ) and relative.endswith(".py"):
        return True
    return relative.startswith("data/derived/covalent_small/") and relative.endswith(
        ".json"
    )


def _git(
    repo_root: Path,
    *arguments: str,
    binary: bool = False,
) -> str | bytes:
    allowed = {"rev-parse", "merge-base", "diff", "show", "ls-files"}
    if not arguments or arguments[0] not in allowed:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    if binary:
        return completed.stdout
    try:
        return completed.stdout.decode("utf-8").rstrip("\n")
    except UnicodeDecodeError as error:
        raise SourceBindingFutureExactPosixModeGuardV2Error(
            f"{_ERROR_PREFIX}:GIT_OUTPUT_DECODE_FAILED:{arguments[0]}"
        ) from error


def _verify_baseline_relationship(repo_root: Path) -> str:
    identity = str(
        _git(
            repo_root,
            "show",
            "-s",
            "--format=%T%n%s",
            _FUTURE_GUARD_BASELINE_COMMIT,
        )
    ).splitlines()
    if identity != [_FUTURE_GUARD_BASELINE_TREE, _FUTURE_GUARD_BASELINE_SUBJECT]:
        _fail("FUTURE_GUARD_BASELINE_IDENTITY_INVALID")
    _git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        _FUTURE_GUARD_BASELINE_COMMIT,
        "HEAD",
    )
    head = str(_git(repo_root, "rev-parse", "HEAD"))
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        _fail("HEAD_IDENTITY_INVALID")
    return head


def _decode_path(payload: bytes, label: str) -> str:
    try:
        relative = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceBindingFutureExactPosixModeGuardV2Error(
            f"{_ERROR_PREFIX}:GIT_PATH_DECODE_FAILED:{label}"
        ) from error
    _validate_relative_path(relative)
    return relative


def _parse_name_status(
    payload: bytes,
    *,
    label: str,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not payload:
        return ()
    fields = payload.split(b"\x00")
    if fields[-1] != b"":
        _fail("NAME_STATUS_TERMINATOR_MISSING:" + label)
    fields.pop()
    entries: list[tuple[str, tuple[str, ...]]] = []
    index = 0
    while index < len(fields):
        try:
            status = fields[index].decode("ascii")
        except UnicodeDecodeError as error:
            raise SourceBindingFutureExactPosixModeGuardV2Error(
                f"{_ERROR_PREFIX}:NAME_STATUS_DECODE_FAILED:{label}"
            ) from error
        index += 1
        if not re.fullmatch(r"[ACDMRT][0-9]{0,3}", status):
            _fail("NAME_STATUS_INVALID:" + label + ":" + status)
        path_count = 2 if status[0] in {"C", "R"} else 1
        if index + path_count > len(fields):
            _fail("NAME_STATUS_TRUNCATED:" + label)
        paths = tuple(
            _decode_path(fields[index + offset], label)
            for offset in range(path_count)
        )
        index += path_count
        entries.append((status, paths))
    return tuple(entries)


def _changed_relevant_paths(
    payload: bytes,
    *,
    label: str,
) -> tuple[set[str], set[str]]:
    changed: set[str] = set()
    current: set[str] = set()
    for status, paths in _parse_name_status(payload, label=label):
        for relative in paths:
            if _is_relevant(relative):
                changed.add(relative)
        if status[0] != "D" and _is_relevant(paths[-1]):
            current.add(paths[-1])
    return changed, current


def _ordinary_untracked_relevant_paths(payload: bytes) -> set[str]:
    if not payload:
        return set()
    fields = payload.split(b"\x00")
    if fields[-1] != b"":
        _fail("UNTRACKED_TERMINATOR_MISSING")
    return {
        relative
        for field in fields[:-1]
        if _is_relevant(relative := _decode_path(field, "UNTRACKED"))
    }


def _discover_future_scope(repo_root: Path) -> dict[str, set[str]]:
    committed_payload = _git(
        repo_root,
        "diff",
        "--name-status",
        "-z",
        _FUTURE_GUARD_BASELINE_COMMIT,
        "HEAD",
        binary=True,
    )
    working_payload = _git(
        repo_root,
        "diff",
        "--name-status",
        "-z",
        "HEAD",
        binary=True,
    )
    untracked_payload = _git(
        repo_root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        binary=True,
    )
    assert isinstance(committed_payload, bytes)
    assert isinstance(working_payload, bytes)
    assert isinstance(untracked_payload, bytes)
    committed_changed, committed_current = _changed_relevant_paths(
        committed_payload,
        label="POST_B3_COMMITTED",
    )
    working_changed, working_current = _changed_relevant_paths(
        working_payload,
        label="WORKING_TREE",
    )
    untracked = _ordinary_untracked_relevant_paths(untracked_payload)
    git_object_paths = committed_current - working_changed
    filesystem_paths = working_current | untracked
    return {
        "committed_changed": committed_changed,
        "working_changed": working_changed,
        "untracked": untracked,
        "git_object_paths": git_object_paths,
        "filesystem_paths": filesystem_paths,
    }


def _decode_text(payload: bytes, label: str) -> str:
    if len(payload) > _MAX_TEXT_BYTES:
        _fail("TEXT_FILE_OVERSIZED:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceBindingFutureExactPosixModeGuardV2Error(
            f"{_ERROR_PREFIX}:TEXT_DECODE_FAILED:{label}"
        ) from error
    if "\x00" in text:
        _fail("TEXT_NUL_FORBIDDEN:" + label)
    return text


def _read_git_text(repo_root: Path, head: str, relative: str) -> str:
    _validate_relative_path(relative)
    payload = _git(repo_root, "show", f"{head}:{relative}", binary=True)
    assert isinstance(payload, bytes)
    return _decode_text(payload, "GIT_OBJECT:" + relative)


def _filesystem_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_worktree_text(repo_root: Path, relative: str) -> str:
    _validate_relative_path(relative)
    path = repo_root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(repo_root)
    except (OSError, ValueError) as error:
        raise SourceBindingFutureExactPosixModeGuardV2Error(
            f"{_ERROR_PREFIX}:WORKTREE_PATH_ESCAPE_OR_MISSING:{relative}"
        ) from error
    if resolved != path:
        _fail("WORKTREE_SYMLINK_COMPONENT_FORBIDDEN:" + relative)
    source_binding_v2.verify_source_security_v2(
        path=path,
        label="B4_FUTURE_SOURCE:" + relative,
        expected_executable=None,
    )
    try:
        before = path.lstat()
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except OSError as error:
        raise SourceBindingFutureExactPosixModeGuardV2Error(
            f"{_ERROR_PREFIX}:WORKTREE_OPEN_FAILED:{relative}"
        ) from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            _fail("WORKTREE_NOT_REGULAR:" + relative)
        if opened.st_size > _MAX_TEXT_BYTES:
            _fail("TEXT_FILE_OVERSIZED:WORKTREE:" + relative)
        pieces: list[bytes] = []
        remaining = _MAX_TEXT_BYTES + 1
        while remaining:
            piece = os.read(descriptor, min(65536, remaining))
            if not piece:
                break
            pieces.append(piece)
            remaining -= len(piece)
        payload = b"".join(pieces)
        after = path.lstat()
    except OSError as error:
        raise SourceBindingFutureExactPosixModeGuardV2Error(
            f"{_ERROR_PREFIX}:WORKTREE_READ_FAILED:{relative}"
        ) from error
    finally:
        os.close(descriptor)
    if len(payload) > _MAX_TEXT_BYTES:
        _fail("TEXT_FILE_OVERSIZED:WORKTREE:" + relative)
    identities = {
        _filesystem_identity(before),
        _filesystem_identity(opened),
        _filesystem_identity(after),
    }
    if len(identities) != 1 or len(payload) != opened.st_size:
        _fail("WORKTREE_IDENTITY_UNSTABLE_DURING_READ:" + relative)
    return _decode_text(payload, "WORKTREE:" + relative)


def _call_name(node: ast.Call) -> str:
    parts: list[str] = []
    current: ast.AST = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _literal_mode(node: ast.AST) -> int | None:
    if isinstance(node, ast.Constant):
        if type(node.value) is int and node.value in _EXACT_MODE_INTS:
            return node.value
        if isinstance(node.value, str):
            value = node.value.lower()
            if value.startswith("0o"):
                value = value[2:]
            if re.fullmatch(r"0?[0-7]{3}", value):
                parsed = int(value, 8)
                if parsed in _EXACT_MODE_INTS:
                    return parsed
    return None


def _git_mode_literal(node: ast.AST) -> int | None:
    if isinstance(node, ast.Constant):
        if type(node.value) is int and node.value in _GIT_MODE_INTS:
            return node.value
        if isinstance(node.value, str) and node.value in {"100644", "100755"}:
            return int(node.value)
    return None


def _exact_modes_in(node: ast.AST) -> frozenset[int]:
    return frozenset(
        value
        for child in ast.walk(node)
        if (value := _literal_mode(child)) is not None
    )


def _posix_modes_in(node: ast.AST, text: str) -> frozenset[int]:
    """Return explicit octal-syntax or octal-string permission literals."""

    segment = ast.get_source_segment(text, node) or ""
    values = {int(match.group(1), 8) for match in _OCTAL_POSIX_LITERAL_RE.finditer(segment)}
    for child in ast.walk(node):
        if not isinstance(child, ast.Constant) or not isinstance(child.value, str):
            continue
        value = child.value.lower()
        if value.startswith("0o"):
            value = value[2:]
        if re.fullmatch(r"0?[0-7]{3}", value):
            values.add(int(value, 8))
    return frozenset(values)


def _git_modes_in(node: ast.AST) -> frozenset[int]:
    return frozenset(
        value
        for child in ast.walk(node)
        if (value := _git_mode_literal(child)) is not None
    )


def _contains_attribute(node: ast.AST, names: frozenset[str]) -> bool:
    return any(
        isinstance(child, ast.Attribute) and child.attr in names
        for child in ast.walk(node)
    )


def _contains_full_mode(node: ast.AST, full_names: set[str]) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and _call_name(child).lower().endswith(
            "s_imode"
        ):
            return True
        if isinstance(child, ast.BinOp) and isinstance(child.op, ast.BitAnd):
            if any(
                isinstance(side, ast.Constant)
                and type(side.value) is int
                and side.value in _FULL_MODE_MASKS
                for side in (child.left, child.right)
            ):
                return True
        if isinstance(child, ast.Name) and child.id in full_names:
            return True
    return False


def _contains_raw_mode(
    node: ast.AST,
    raw_names: set[str],
    full_names: set[str],
) -> bool:
    return _contains_full_mode(node, full_names) or any(
        isinstance(child, ast.Attribute) and child.attr == "st_mode"
        or isinstance(child, ast.Name) and child.id in raw_names
        for child in ast.walk(node)
    )


def _contains_exec_class(node: ast.AST, exec_names: set[str]) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in exec_names:
            return True
        if isinstance(child, ast.BinOp) and isinstance(child.op, ast.BitAnd):
            if any(
                isinstance(side, ast.Constant)
                and type(side.value) is int
                and side.value == 0o111
                for side in (child.left, child.right)
            ):
                return True
    return False


def _contains_expected_mode_authority(
    node: ast.AST,
    expected_names: set[str],
) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in expected_names:
            return True
        if isinstance(child, ast.Subscript):
            key = child.slice
            if (
                isinstance(key, ast.Constant)
                and key.value in _EXPECTED_MODE_AUTHORITY_KEYS
            ):
                return True
    return False


def _target_names(node: ast.AST) -> set[str]:
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
    }


def _mode_reference(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            name = child.id.lower()
            if name in {"mode", "actual_mode", "expected_mode", "required_mode"}:
                return True
            if name.endswith("_mode") and not name.startswith("git_"):
                return True
        if isinstance(child, ast.Subscript):
            key = child.slice
            if (
                isinstance(key, ast.Constant)
                and key.value in _EXPECTED_MODE_AUTHORITY_KEYS
            ):
                return True
    return False


def _string_keys(node: ast.Dict) -> set[str]:
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def _context_for(
    node: ast.AST,
    *,
    source_path: str,
    lines: list[str],
    parents: dict[ast.AST, ast.AST],
) -> str:
    names: list[str] = []
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(current.name)
            break
        current = parents.get(current)
    start = max(0, getattr(node, "lineno", 1) - 4)
    end = min(len(lines), getattr(node, "end_lineno", start + 1) + 3)
    names.extend(lines[start:end])
    return "\n".join(names).lower()


def _has_context(context: str, terms: tuple[str, ...]) -> bool:
    return any(term in context for term in terms)


def _scope_for(
    node: ast.AST,
    *,
    parents: dict[ast.AST, ast.AST],
    module: ast.Module,
) -> ast.AST:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return current
        current = parents.get(current)
    return module


def _occurrence(
    *,
    source_path: str,
    node: ast.AST,
    semantic_class: str,
    pattern: str,
    test_only: bool,
) -> dict[str, object]:
    if semantic_class not in _SEMANTIC_CLASSES:
        _fail("INTERNAL_SEMANTIC_CLASS_INVALID")
    return {
        "source_path": source_path,
        "line_start": int(getattr(node, "lineno", 1)),
        "line_end": int(getattr(node, "end_lineno", getattr(node, "lineno", 1))),
        "semantic_class": semantic_class,
        "matched_semantic_pattern": pattern,
        "context_class": "TEST_ONLY" if test_only else "PRODUCTION_CURRENT_AUTHORITY",
    }


def _classify_python_tree_v2(
    text: str,
    *,
    source_path: str,
    test_only: bool,
) -> tuple[dict[str, object], ...]:
    try:
        tree = ast.parse(text, filename=source_path)
    except SyntaxError as error:
        _fail("PYTHON_AST_PARSE_FAILED:" + source_path + f":{error.lineno}")
    lines = text.splitlines()
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    assignments: list[tuple[ast.AST, ast.AST, set[str], ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = set().union(*(_target_names(target) for target in node.targets))
            assignments.append(
                (
                    node,
                    node.value,
                    targets,
                    _scope_for(node, parents=parents, module=tree),
                )
            )
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append(
                (
                    node,
                    node.value,
                    _target_names(node.target),
                    _scope_for(node, parents=parents, module=tree),
                )
            )
    assignments_by_scope: dict[
        ast.AST,
        list[tuple[ast.AST, ast.AST, set[str], ast.AST]],
    ] = {}
    for assignment in assignments:
        assignments_by_scope.setdefault(assignment[3], []).append(assignment)
    taints_by_scope: dict[
        ast.AST,
        tuple[set[str], set[str], set[str], set[str]],
    ] = {}
    for scope, scoped_assignments in assignments_by_scope.items():
        full_names: set[str] = set()
        raw_names: set[str] = set()
        expected_names: set[str] = set()
        exec_names: set[str] = set()
        for _iteration in range(len(scoped_assignments) + 1):
            changed = False
            for _node, value, targets, _scope in scoped_assignments:
                exec_value = _contains_exec_class(value, exec_names)
                full_value = _contains_full_mode(value, full_names)
                raw_value = _contains_raw_mode(value, raw_names, full_names)
                expected_value = _contains_expected_mode_authority(
                    value,
                    expected_names,
                )
                if exec_value:
                    if not targets <= exec_names:
                        exec_names.update(targets)
                        changed = True
                elif full_value:
                    if not targets <= full_names:
                        full_names.update(targets)
                        changed = True
                elif raw_value and not targets <= raw_names:
                    raw_names.update(targets)
                    changed = True
                if expected_value and not targets <= expected_names:
                    expected_names.update(targets)
                    changed = True
            if not changed:
                break
        taints_by_scope[scope] = (
            full_names,
            raw_names,
            expected_names,
            exec_names,
        )

    occurrences: list[dict[str, object]] = []
    occupied: set[tuple[int, int, str]] = set()

    def add(node: ast.AST, semantic_class: str, pattern: str) -> None:
        key = (
            int(getattr(node, "lineno", 1)),
            int(getattr(node, "end_lineno", getattr(node, "lineno", 1))),
            pattern,
        )
        if key in occupied:
            return
        occupied.add(key)
        occurrences.append(
            _occurrence(
                source_path=source_path,
                node=node,
                semantic_class=semantic_class,
                pattern=pattern,
                test_only=test_only,
            )
        )

    compared_names: set[tuple[ast.AST, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        scope = _scope_for(node, parents=parents, module=tree)
        full_names, raw_names, expected_names, exec_names = taints_by_scope.get(
            scope,
            (set(), set(), set(), set()),
        )
        context = _context_for(
            node,
            source_path=source_path,
            lines=lines,
            parents=parents,
        )
        exact_modes = _exact_modes_in(node)
        posix_modes = _posix_modes_in(node, text)
        git_modes = _git_modes_in(node)
        full_mode = _contains_full_mode(node, full_names)
        raw_mode = _contains_raw_mode(node, raw_names, full_names)
        expected_authority = _contains_expected_mode_authority(
            node,
            expected_names,
        )
        exec_class = _contains_exec_class(node, exec_names)
        compared_names.update(
            (scope, child.id)
            for child in ast.walk(node)
            if isinstance(child, ast.Name)
            and child.id in full_names | raw_names | expected_names | exec_names
        )
        source_context = _has_context(context, _SOURCE_CONTEXT_TERMS)
        candidate_context = (
            _has_context(context, _CANDIDATE_CONTEXT_TERMS)
            and not source_context
            and not expected_authority
        )
        git_context = _has_context(context, _GIT_CONTEXT_TERMS)
        security_context = _contains_attribute(node, _SECURITY_ATTRIBUTES)
        if git_modes and git_context and not raw_mode and not expected_authority:
            add(node, _GIT_OR_EXECUTABLE_CLASS, "git_native_100644_100755_file_class")
        elif (
            raw_mode
            and posix_modes
            and posix_modes <= _CANDIDATE_SAFE_MODE_INTS
            and candidate_context
        ):
            add(node, _CANDIDATE_HYGIENE, "candidate_0644_0664_artifact_hygiene")
        elif (
            exec_class
            and not expected_authority
            and (not posix_modes or posix_modes == {0o111})
        ):
            add(node, _GIT_OR_EXECUTABLE_CLASS, "executable_bit_class_only")
        elif (
            security_context
            and not full_mode
            and not expected_authority
            and not posix_modes
        ):
            add(node, _SECURITY_HYGIENE, "filesystem_security_bit_or_file_type_check")
        elif full_mode and expected_authority:
            add(node, _SEMANTIC_SOURCE_IDENTITY, "live_full_mode_expected_authority_comparison")
        elif full_mode and posix_modes and source_context:
            add(node, _SEMANTIC_SOURCE_IDENTITY, "live_full_mode_exact_identity_comparison")
        elif full_mode and _mode_reference(node) and source_context:
            add(node, _SEMANTIC_SOURCE_IDENTITY, "live_full_mode_exact_identity_comparison")
        elif full_mode:
            add(node, _AMBIGUOUS, "full_mode_comparison_semantics_unresolved")
        elif raw_mode:
            add(node, _AMBIGUOUS, "raw_mode_comparison_semantics_unresolved")
        elif (exact_modes or posix_modes) and _mode_reference(node):
            if source_context:
                add(node, _SEMANTIC_SOURCE_IDENTITY, "exact_mode_source_acceptance")
            elif candidate_context and posix_modes <= _CANDIDATE_SAFE_MODE_INTS:
                add(node, _CANDIDATE_HYGIENE, "candidate_0644_0664_artifact_hygiene")
            else:
                add(node, _AMBIGUOUS, "exact_mode_acceptance_context_unresolved")
        elif security_context:
            add(node, _SECURITY_HYGIENE, "filesystem_security_bit_or_file_type_check")

    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.Assert)):
            expression = node.test
            if any(isinstance(child, ast.Compare) for child in ast.walk(expression)):
                continue
            scope = _scope_for(node, parents=parents, module=tree)
            _full_names, _raw_names, _expected_names, exec_names = taints_by_scope.get(
                scope,
                (set(), set(), set(), set()),
            )
            if _contains_exec_class(expression, exec_names):
                add(expression, _GIT_OR_EXECUTABLE_CLASS, "executable_bit_class_only")
            elif _contains_attribute(expression, _SECURITY_ATTRIBUTES):
                add(
                    expression,
                    _SECURITY_HYGIENE,
                    "filesystem_security_bit_or_file_type_check",
                )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = _string_keys(node)
        mode_keys = keys & _MODE_KEYS
        all_mode_keys = mode_keys | (keys & {"historical_mode"})
        context = _context_for(
            node,
            source_path=source_path,
            lines=lines,
            parents=parents,
        )
        source_context = _has_context(context, _SOURCE_CONTEXT_TERMS)
        candidate_context = (
            _has_context(context, _CANDIDATE_CONTEXT_TERMS)
            and not source_context
        )
        if "git_mode" in keys and _git_modes_in(node):
            add(node, _GIT_OR_EXECUTABLE_CLASS, "git_native_100644_100755_file_class")
        elif all_mode_keys and candidate_context:
            add(node, _CANDIDATE_HYGIENE, "candidate_mode_hygiene_metadata")
        elif mode_keys and {"path", "byte_count", "sha256"} <= keys:
            add(node, _SEMANTIC_SOURCE_IDENTITY, "python_binding_path_bytes_sha_exact_mode")
        elif "historical_mode" in keys and keys & _IDENTITY_KEYS:
            add(node, _AMBIGUOUS, "historical_mode_identity_metadata_unresolved")
        elif "historical_mode" in keys:
            add(node, _REPORTING_DIAGNOSTIC, "historical_mode_reporting_only")
        elif mode_keys and (_exact_modes_in(node) or keys & _IDENTITY_KEYS):
            add(node, _AMBIGUOUS, "python_mode_metadata_semantics_unresolved")

    for node, value, targets, scope in assignments:
        full_names, _raw_names, _expected_names, exec_names = taints_by_scope.get(
            scope,
            (set(), set(), set(), set()),
        )
        context = _context_for(
            node,
            source_path=source_path,
            lines=lines,
            parents=parents,
        )
        target_text = " ".join(sorted(targets)).lower()
        compared_in_scope = {
            name for compared_scope, name in compared_names if compared_scope is scope
        }
        used = any((scope, target) in compared_names for target in targets) or (
            bool(targets & full_names) and bool(compared_in_scope & full_names)
        )
        source_context = _has_context(context, _SOURCE_CONTEXT_TERMS)
        candidate_context = (
            _has_context(context, _CANDIDATE_CONTEXT_TERMS)
            and not source_context
        )
        if _git_modes_in(value) and (
            "git" in target_text or _has_context(context, _GIT_CONTEXT_TERMS)
        ):
            add(node, _GIT_OR_EXECUTABLE_CLASS, "git_native_100644_100755_file_class")
        elif _contains_exec_class(value, exec_names):
            add(node, _GIT_OR_EXECUTABLE_CLASS, "legacy_or_live_mode_to_executable_class")
        elif _contains_full_mode(value, full_names) and not used:
            if "historical" in target_text or "report" in target_text:
                add(node, _REPORTING_DIAGNOSTIC, "full_mode_reporting_only")
            elif candidate_context:
                add(node, _CANDIDATE_HYGIENE, "candidate_mode_hygiene_intermediate")
            else:
                add(node, _AMBIGUOUS, "unused_full_mode_extraction_semantics_unresolved")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        value = node.value
        if value is None or not _exact_modes_in(value):
            continue
        if isinstance(target, ast.Subscript):
            key = target.slice
            if isinstance(key, ast.Constant) and key.value == "historical_mode":
                add(node, _REPORTING_DIAGNOSTIC, "historical_mode_reporting_only")

    occurrences.sort(
        key=lambda item: (
            str(item["source_path"]),
            int(item["line_start"]),
            int(item["line_end"]),
            str(item["semantic_class"]),
            str(item["matched_semantic_pattern"]),
        )
    )
    return tuple(occurrences)


def _classify_python_text_v2(
    text: str,
    *,
    source_path: str,
    test_only: bool | None = None,
) -> tuple[dict[str, object], ...]:
    """Pure AST classifier used by the guard's static regressions."""

    _validate_relative_path(source_path)
    if test_only is None:
        test_only = source_path.startswith("tests/test_covapie")
    rows = list(
        _classify_python_tree_v2(
            text,
            source_path=source_path,
            test_only=test_only,
        )
    )
    if test_only:
        try:
            outer = ast.parse(text, filename=source_path)
        except SyntaxError:
            _fail("PYTHON_AST_PARSE_FAILED:" + source_path)
        for index, node in enumerate(ast.walk(outer)):
            if not (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and _TEXT_MODE_SIGNAL.search(node.value)
            ):
                continue
            try:
                nested = _classify_python_tree_v2(
                    node.value,
                    source_path=source_path,
                    test_only=True,
                )
            except SourceBindingFutureExactPosixModeGuardV2Error:
                continue
            for row in nested:
                copied = dict(row)
                copied["matched_semantic_pattern"] = (
                    "test_only_embedded_snippet:"
                    + str(copied["matched_semantic_pattern"])
                    + f":{index}"
                )
                rows.append(copied)
    rows.sort(
        key=lambda item: (
            str(item["source_path"]),
            int(item["line_start"]),
            int(item["line_end"]),
            str(item["semantic_class"]),
            str(item["matched_semantic_pattern"]),
        )
    )
    return tuple(rows)


def _json_reporting_context(parent: dict[str, object], key: str) -> bool:
    joined = json.dumps(parent, ensure_ascii=False, sort_keys=True).lower()
    return any(
        token in joined
        for token in (
            "reporting_only",
            "reporting/diagnostic",
            "historical provenance",
            "historical_provenance",
            "diagnostic_only",
        )
    )


def _classify_json_text_v2(
    text: str,
    *,
    source_path: str,
    test_only: bool = False,
) -> tuple[dict[str, object], ...]:
    """Pure recursive JSON classifier for future authority documents."""

    _validate_relative_path(source_path)
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        _fail("JSON_STATIC_PARSE_FAILED:" + source_path + f":{error.lineno}")
    occurrences: list[dict[str, object]] = []

    def add(
        semantic_class: str,
        pattern: str,
        json_path: str,
    ) -> None:
        synthetic = ast.Constant(value=json_path)
        synthetic.lineno = 1
        synthetic.end_lineno = 1
        occurrences.append(
            _occurrence(
                source_path=source_path,
                node=synthetic,
                semantic_class=semantic_class,
                pattern=pattern + ":" + json_path,
                test_only=test_only,
            )
        )

    def walk(value: object, json_path: str) -> None:
        if isinstance(value, dict):
            keys = {str(key) for key in value}
            for key, child in value.items():
                key_text = str(key)
                child_path = json_path + "." + key_text
                if key_text in _MODE_KEYS or key_text in {"git_mode", "historical_mode"}:
                    literal = str(child)
                    if key_text == "git_mode" or literal in {"100644", "100755"}:
                        add(
                            _GIT_OR_EXECUTABLE_CLASS,
                            "json_git_native_file_class",
                            child_path,
                        )
                    elif _json_reporting_context(value, key_text):
                        add(
                            _REPORTING_DIAGNOSTIC,
                            "json_historical_reporting_mode",
                            child_path,
                        )
                    elif {"path", "byte_count", "sha256"} <= keys:
                        add(
                            _SEMANTIC_SOURCE_IDENTITY,
                            "json_binding_path_bytes_sha_exact_mode",
                            child_path,
                        )
                    elif keys & _IDENTITY_KEYS:
                        add(
                            _AMBIGUOUS,
                            "json_partial_binding_mode_semantics_unresolved",
                            child_path,
                        )
                    else:
                        add(
                            _AMBIGUOUS,
                            "json_mode_metadata_semantics_unresolved",
                            child_path,
                        )
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{json_path}[{index}]")

    walk(document, "root")
    occurrences.sort(key=lambda item: str(item["matched_semantic_pattern"]))
    return tuple(occurrences)


def _verify_frozen_dependencies(repo_root: Path) -> None:
    for label, relative, byte_count, sha256 in _FROZEN_DEPENDENCIES:
        source_binding_v2.verify_bound_source_v2(
            path=repo_root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=False,
        )


def _verify_b3_result(repo_root: Path) -> dict[str, object]:
    result = historical_v2.verify_covapie_source_binding_historical_immutability_proof_v2(
        repo_root=repo_root
    )
    required = {
        "migration_commit_count": 8,
        "migration_added_path_count": 32,
        "migration_modified_path_count": 0,
        "migration_deleted_path_count": 0,
        "phase_a_scanned_source_binding_count": 1755,
        "all_phase_a_scanned_source_bytes_unchanged": True,
        "all_active_v1_migration_target_bytes_unchanged": True,
        "known_regression_reference_bytes_unchanged": True,
        "historical_exact_mode_metadata_preserved": True,
        "historical_exact_mode_metadata_rewritten": False,
        "historical_validator_rewrite_performed": False,
        "b2_integration_verified": True,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "v2_migration_phase_b3_historical_immutability_proven": True,
        "ready_for_training": False,
    }
    if type(result) is not dict:
        _fail("B3_RESULT_TYPE_INVALID")
    for key, expected in required.items():
        if result.get(key) != expected or type(result.get(key)) is not type(expected):
            _fail("B3_RESULT_INVALID:" + key)
    return result


def _verify_legacy_boundary(repo_root: Path) -> dict[str, bool]:
    payload = _git(
        repo_root,
        "show",
        f"{_FUTURE_GUARD_BASELINE_COMMIT}:{_LEGACY_CONTROL_RELATIVE}",
        binary=True,
    )
    assert isinstance(payload, bytes)
    text = _decode_text(payload, "LEGACY_CONTROL")
    rows = _classify_python_text_v2(
        text,
        source_path=_LEGACY_CONTROL_RELATIVE,
        test_only=False,
    )
    detected = any(
        row["semantic_class"] == _SEMANTIC_SOURCE_IDENTITY for row in rows
    )
    if not detected:
        _fail("LEGACY_NEGATIVE_CONTROL_NOT_DETECTED")
    return {
        "known_legacy_v1_contains_forbidden_pattern": True,
        "unchanged_legacy_v1_not_counted_as_future_violation": True,
        "same_legacy_bytes_simulated_as_future_modification_detected": True,
    }


def verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Verify B3 and reject exact-mode identity in every post-B3 scan surface."""

    if not isinstance(repo_root, Path):
        _fail("REPO_ROOT_TYPE_INVALID")
    repo_root = repo_root.resolve()
    if not (repo_root / ".git").exists():
        _fail("REPO_ROOT_NOT_GIT_WORKTREE")
    head = _verify_baseline_relationship(repo_root)
    _verify_frozen_dependencies(repo_root)
    b3 = _verify_b3_result(repo_root)
    legacy = _verify_legacy_boundary(repo_root)
    scope = _discover_future_scope(repo_root)

    scanned_paths = sorted(scope["git_object_paths"] | scope["filesystem_paths"])
    occurrences: list[dict[str, object]] = []
    python_paths: list[str] = []
    json_paths: list[str] = []
    for relative in scanned_paths:
        if relative in scope["filesystem_paths"]:
            text = _read_worktree_text(repo_root, relative)
        else:
            text = _read_git_text(repo_root, head, relative)
        if relative.endswith(".py"):
            python_paths.append(relative)
            occurrences.extend(
                _classify_python_text_v2(text, source_path=relative)
            )
        elif relative.endswith(".json"):
            json_paths.append(relative)
            occurrences.extend(
                _classify_json_text_v2(text, source_path=relative)
            )
        else:
            _fail("INTERNAL_SCAN_SUFFIX_INVALID:" + relative)

    production_occurrences = [
        row for row in occurrences if row["context_class"] != "TEST_ONLY"
    ]
    semantic_findings = [
        row
        for row in production_occurrences
        if row["semantic_class"] == _SEMANTIC_SOURCE_IDENTITY
    ]
    ambiguous_findings = [
        row
        for row in production_occurrences
        if row["semantic_class"] == _AMBIGUOUS
    ]
    if semantic_findings or ambiguous_findings:
        first = sorted(
            semantic_findings + ambiguous_findings,
            key=lambda row: (
                str(row["source_path"]),
                int(row["line_start"]),
                str(row["semantic_class"]),
            ),
        )[0]
        _fail(
            "FUTURE_MODE_OCCURRENCE_FORBIDDEN:"
            + str(first["source_path"])
            + ":"
            + str(first["line_start"])
            + ":"
            + str(first["semantic_class"])
        )

    counts = Counter(str(row["semantic_class"]) for row in production_occurrences)
    test_only_count = sum(
        row["context_class"] == "TEST_ONLY" for row in occurrences
    )
    production_clean = _PRODUCTION_RELATIVE in scanned_paths and not any(
        row["source_path"] == _PRODUCTION_RELATIVE
        and row["semantic_class"] in {_SEMANTIC_SOURCE_IDENTITY, _AMBIGUOUS}
        and row["context_class"] != "TEST_ONLY"
        for row in occurrences
    )
    checker_clean = _CHECKER_RELATIVE in scanned_paths and not any(
        row["source_path"] == _CHECKER_RELATIVE
        and row["semantic_class"] in {_SEMANTIC_SOURCE_IDENTITY, _AMBIGUOUS}
        and row["context_class"] != "TEST_ONLY"
        for row in occurrences
    )
    if not production_clean:
        _fail("B4_PRODUCTION_SELF_SCAN_FAILED")
    if not checker_clean:
        _fail("B4_CHECKER_SELF_SCAN_FAILED")

    return {
        "schema_version": _SCHEMA_VERSION,
        "future_guard_baseline_commit": _FUTURE_GUARD_BASELINE_COMMIT,
        "future_guard_baseline_is_ancestor": True,
        "post_b3_tracked_changed_relevant_path_count": len(
            scope["committed_changed"]
        ),
        "working_tree_modified_relevant_path_count": len(scope["working_changed"]),
        "ordinary_untracked_relevant_path_count": len(scope["untracked"]),
        "future_guard_scanned_python_file_count": len(python_paths),
        "future_guard_scanned_json_file_count": len(json_paths),
        "future_guard_scanned_total_file_count": len(scanned_paths),
        "future_guard_scanned_python_paths": tuple(python_paths),
        "future_guard_scanned_json_paths": tuple(json_paths),
        "new_semantic_exact_posix_mode_occurrence_count": len(semantic_findings),
        "new_ambiguous_mode_occurrence_count": len(ambiguous_findings),
        "security_hygiene_occurrence_count": counts[_SECURITY_HYGIENE],
        "executable_class_occurrence_count": sum(
            row["matched_semantic_pattern"]
            in {"executable_bit_class_only", "legacy_or_live_mode_to_executable_class"}
            for row in production_occurrences
        ),
        "candidate_hygiene_occurrence_count": counts[_CANDIDATE_HYGIENE],
        "git_file_class_occurrence_count": sum(
            "git_native" in str(row["matched_semantic_pattern"])
            for row in production_occurrences
        ),
        "reporting_diagnostic_occurrence_count": counts[_REPORTING_DIAGNOSTIC],
        "test_only_occurrence_count": test_only_count,
        "B4_PRODUCTION_SELF_SCAN_PASSED": True,
        "B4_CHECKER_SELF_SCAN_PASSED": True,
        "b3_historical_immutability_verified": True,
        "historical_exact_mode_occurrences_governed_by_b3": True,
        "historical_v1_rewrite_required": False,
        "historical_exact_mode_metadata_preserved": b3[
            "historical_exact_mode_metadata_preserved"
        ],
        "historical_exact_mode_metadata_propagated_into_future_identity": False,
        **legacy,
        "exact_numeric_posix_mode_semantic_identity_forbidden_for_future": True,
        "security_hygiene_mode_checks_allowed": True,
        "executable_class_checks_allowed": True,
        "git_file_class_checks_allowed": True,
        "candidate_artifact_hygiene_allowed": True,
        "historical_reporting_mode_metadata_allowed": True,
        "filesystem_source_acceptance_authority": "SOURCE_BINDING_POLICY_V2",
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "global_canonical_task_count": b3["global_canonical_task_count"],
        "B3_present": b3["B3_present"],
        "sixth_task_present": b3["sixth_task_present"],
        "v2_migration_phase_b4_future_guard_active": True,
        "ready_to_close_source_binding_filesystem_mode_v2_migration": True,
        "ready_for_training": False,
    }
