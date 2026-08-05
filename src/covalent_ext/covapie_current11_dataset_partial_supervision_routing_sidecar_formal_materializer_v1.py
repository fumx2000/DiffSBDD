"""Atomically materialize the Current11 routing sidecar Exact4."""

from __future__ import annotations

import copy
import csv
import ctypes
import errno
import hashlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
from collections import Counter
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_dataset_partial_supervision_routing_sidecar_v1 as _builder


__all__ = (
    "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
)

SCHEMA_VERSION = (
    "covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1"
)
ERROR_TOKEN = (
    "COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_"
    "FORMAL_MATERIALIZER_V1_ERROR"
)
CLEANUP_ERROR_TOKEN = f"{ERROR_TOKEN}_CLEANUP_FAILED"
BASE_COMMIT = "903c074805a22d7c899fd23c22ebfb3ac2e811e5"
FORMAL_COMMIT_SUBJECT = "add CovaPIE Current11 dataset routing sidecar materializer v1"
BRANCH = "main"
SOURCE_BUILDER_SCHEMA_VERSION = (
    "covapie_current11_dataset_partial_supervision_routing_sidecar_v1"
)
SOURCE_BUILDER_COMMIT = BASE_COMMIT
SOURCE_BUILDER_SHA256 = (
    "1be932e473107a2944cf916c288580b614c7b6710556ca54c099d742971344a5"
)
SOURCE_BUILDER_PATH = (
    "src/covalent_ext/"
    "covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"
)
MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1.py"
)
SCRIPT_PATH = (
    "scripts/"
    "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"
)
TEST_PATH = (
    "tests/"
    "test_covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1.py"
)
GUIDE_PATH = (
    "docs/"
    "covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))
ARTIFACT_NAMES = (
    "current11_dataset_partial_supervision_routing_records.csv",
    "current11_dataset_partial_supervision_task_coverage.csv",
    "current11_dataset_partial_supervision_sample_coverage.csv",
    "current11_dataset_partial_supervision_routing_manifest.json",
)
EXPECTED_LINE_COUNTS = {
    ARTIFACT_NAMES[0]: 276,
    ARTIFACT_NAMES[1]: 26,
    ARTIFACT_NAMES[2]: 12,
}
EXPECTED_GLOBAL_COUNTS = {
    "admissible_now": 44,
    "admissible_as_observed_geometry_only": 11,
    "candidate_only_not_authoritative": 55,
    "blocked_missing_evidence": 103,
    "blocked_state_ambiguity": 7,
    "blocked_missing_human_approval": 55,
    "not_applicable": 0,
}
EXPECTED_UNIT_COUNTS = {
    "admissible_now": 8,
    "admissible_as_observed_geometry_only": 2,
    "candidate_only_not_authoritative": 10,
    "blocked_missing_evidence": 13,
    "blocked_state_ambiguity": 7,
    "blocked_missing_human_approval": 10,
    "not_applicable": 0,
}
EXPECTED_MASKS = (
    {"semantic_name": "warhead_only", "display_alias": "A"},
    {"semantic_name": "linker_plus_warhead", "display_alias": "B"},
    {"semantic_name": "scaffold_plus_warhead", "display_alias": "B2"},
    {"semantic_name": "scaffold_only", "display_alias": "B3"},
    {"semantic_name": "scaffold_plus_linker_plus_warhead", "display_alias": "C"},
)
BUILDER_LIFECYCLE_FIELDS = frozenset(
    {
        "base_commit",
        "future_formal_subject",
        "candidate_paths",
        "lifecycle_profile",
        "formal_candidate_commit",
        "origin_main",
        "ahead",
        "behind",
    }
)
BUILDER_LIFECYCLE_DYNAMIC_FIELDS = frozenset({"origin_main", "ahead", "behind"})
SOURCE_BUILDER_BASE_COMMIT = "05a86e7f293d75a2e890850208ee49b9d1c821f6"
SOURCE_BUILDER_FORMAL_SUBJECT = (
    "add CovaPIE Current11 dataset partial supervision routing sidecar v1"
)
SOURCE_BUILDER_LIFECYCLE_PROFILE = (
    "dataset_partial_supervision_sidecar_published_successor"
)
_PATH_TYPE = type(Path())
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
_WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
_RENAME_NOREPLACE = 1

try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None


class _CleanupFailure(ValueError):
    pass


def _fail() -> NoReturn:
    raise ValueError(ERROR_TOKEN)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _identity(item: os.stat_result) -> tuple[int, int]:
    return int(item.st_dev), int(item.st_ino)


def _same_identity(item: os.stat_result, expected: tuple[int, int]) -> bool:
    return _identity(item) == expected


def _stat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _listdir_fd(directory_fd: int) -> tuple[str, ...]:
    return tuple(os.listdir(directory_fd))


def _assert_parent_identity(
    parent_fd: int, parent_path: Path, expected: tuple[int, int]
) -> None:
    try:
        lexical = parent_path.lstat()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        not _same_identity(os.fstat(parent_fd), expected)
        or not _same_identity(lexical, expected)
        or stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or parent_path.resolve(strict=True) != parent_path
    ):
        _fail()


def _require_absolute_real_directory(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        resolved = path.resolve(strict=True)
        metadata = path.lstat()
    except (OSError, RuntimeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return resolved


def _assert_real_chain(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as error:
            raise ValueError(ERROR_TOKEN) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail()
    if path.resolve(strict=True) != path:
        _fail()


def _validate_roots_and_output(
    repo_root: Path, state_root: Path, output_dir: Path, *, require_target: bool
) -> tuple[Path, Path, Path, os.stat_result]:
    repository = _require_absolute_real_directory(repo_root)
    state = _require_absolute_real_directory(state_root)
    if type(output_dir) is not _PATH_TYPE or not output_dir.is_absolute() or not output_dir.name:
        _fail()
    parent = output_dir.parent
    _assert_real_chain(parent)
    if output_dir != parent / output_dir.name:
        _fail()
    if output_dir == repository or repository in output_dir.parents:
        _fail()
    try:
        target_metadata = output_dir.lstat()
    except FileNotFoundError:
        if require_target:
            _fail()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    else:
        if not require_target:
            _fail()
        if stat.S_ISLNK(target_metadata.st_mode) or not stat.S_ISDIR(target_metadata.st_mode):
            _fail()
        if output_dir.resolve(strict=True) != output_dir:
            _fail()
    parent_metadata = parent.lstat()
    if stat.S_IMODE(parent_metadata.st_mode) & 0o200 == 0 and not require_target:
        _fail()
    return repository, state, output_dir, parent_metadata


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            _fail()
        return list(reader)
    except (UnicodeError, csv.Error) as error:
        raise ValueError(ERROR_TOKEN) from error


def _validate_builder_source(repo_root: Path) -> None:
    path = repo_root / SOURCE_BUILDER_PATH
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or _sha256(payload) != SOURCE_BUILDER_SHA256
    ):
        _fail()


def _validate_builder_lifecycle_contract(lifecycle: object) -> dict[str, object]:
    if (
        type(lifecycle) is not dict
        or set(lifecycle) != BUILDER_LIFECYCLE_FIELDS
        or lifecycle.get("base_commit") != SOURCE_BUILDER_BASE_COMMIT
        or lifecycle.get("future_formal_subject") != SOURCE_BUILDER_FORMAL_SUBJECT
        or lifecycle.get("candidate_paths") != list(_builder.CANDIDATE_PATHS)
        or lifecycle.get("lifecycle_profile") != SOURCE_BUILDER_LIFECYCLE_PROFILE
        or lifecycle.get("formal_candidate_commit") != SOURCE_BUILDER_COMMIT
        or type(lifecycle.get("origin_main")) is not str
        or re.fullmatch(r"[0-9a-f]{40}", lifecycle["origin_main"]) is None
        or type(lifecycle.get("ahead")) is not int
        or lifecycle["ahead"] < 0
        or type(lifecycle.get("behind")) is not int
        or lifecycle["behind"] < 0
    ):
        _fail()
    return lifecycle


def _stable_builder_manifest_projection(manifest: object) -> dict[str, object]:
    if type(manifest) is not dict:
        _fail()
    _validate_builder_lifecycle_contract(manifest.get("repository_lifecycle"))
    projected = copy.deepcopy(manifest)
    lifecycle = projected["repository_lifecycle"]
    for field in BUILDER_LIFECYCLE_DYNAMIC_FIELDS:
        del lifecycle[field]
    return projected


def _validate_builder_artifacts(
    artifacts: Mapping[str, bytes], repo_root: Path
) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_NAMES or len(artifacts) != 4:
        _fail()
    for name, payload in artifacts.items():
        if (
            type(name) is not str
            or type(payload) is not bytes
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
        ):
            _fail()
        try:
            payload.decode("utf-8")
        except UnicodeError as error:
            raise ValueError(ERROR_TOKEN) from error
    if any(artifacts[name].count(b"\n") != count for name, count in EXPECTED_LINE_COUNTS.items()):
        _fail()

    records = _csv_rows(artifacts[ARTIFACT_NAMES[0]])
    tasks = _csv_rows(artifacts[ARTIFACT_NAMES[1]])
    samples = _csv_rows(artifacts[ARTIFACT_NAMES[2]])
    try:
        manifest = json.loads(artifacts[ARTIFACT_NAMES[3]])
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        type(manifest) is not dict
        or len(records) != 275
        or len(tasks) != 25
        or len(samples) != 11
        or manifest.get("schema_version") != SOURCE_BUILDER_SCHEMA_VERSION
        or manifest.get("sample_count") != 11
        or manifest.get("semantic_task_count") != 25
        or manifest.get("routing_record_count") != 275
        or manifest.get("global_state_counts") != EXPECTED_GLOBAL_COUNTS
        or tuple(manifest.get("canonical_mask_semantics", ())) != EXPECTED_MASKS
    ):
        _fail()
    unit = manifest.get("unit_000001_parity")
    lifecycle = manifest.get("repository_lifecycle")
    readiness = manifest.get("readiness")
    if (
        type(unit) is not dict
        or unit.get("passed") is not True
        or unit.get("routing_record_count") != 50
        or unit.get("state_counts") != EXPECTED_UNIT_COUNTS
        or type(readiness) is not dict
        or readiness.get("unit_000001_parity_passed") is not True
        or readiness.get("runtime_consumer_available") is not False
        or readiness.get("training_loss_authorized") is not False
        or readiness.get("tensor_materialized") is not False
        or readiness.get("ready_for_tensor_materialization") is not False
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get("ready_for_model_integration") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training") is not True
        or readiness.get("ready_for_training") is not False
    ):
        _fail()
    _validate_builder_lifecycle_contract(lifecycle)
    counts = Counter(record.get("eligibility_state") for record in records)
    if {name: counts[name] for name in EXPECTED_GLOBAL_COUNTS} != EXPECTED_GLOBAL_COUNTS:
        _fail()
    unit_ids = set(unit.get("sample_index_row_ids", ()))
    unit_provenance = 0
    other_provenance = 0
    for record in records:
        try:
            sources = json.loads(record["supporting_source_ids_json"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(ERROR_TOKEN) from error
        count = sources.count("published_unit_000001_gate") if type(sources) is list else -1
        if (
            record.get("availability_mask_required") != "true"
            or record.get("current_runtime_consumer_available") != "false"
            or record.get("training_loss_authorized") != "false"
            or count != (1 if record.get("sample_index_row_id") in unit_ids else 0)
        ):
            _fail()
        if record.get("sample_index_row_id") in unit_ids:
            unit_provenance += 1
        else:
            other_provenance += 1
    if (unit_provenance, other_provenance) != (50, 225):
        _fail()
    _validate_builder_source(repo_root)
    return manifest


def _compare_formal_target_with_fresh_builder(
    *,
    target_artifacts: Mapping[str, bytes],
    fresh_artifacts: Mapping[str, bytes],
    repo_root: Path,
) -> dict[str, object]:
    target_manifest = _validate_builder_artifacts(target_artifacts, repo_root)
    fresh_manifest = _validate_builder_artifacts(fresh_artifacts, repo_root)
    if any(
        target_artifacts[name] != fresh_artifacts[name]
        or _sha256(target_artifacts[name]) != _sha256(fresh_artifacts[name])
        for name in ARTIFACT_NAMES[:3]
    ):
        _fail()
    if _stable_builder_manifest_projection(target_manifest) != _stable_builder_manifest_projection(
        fresh_manifest
    ):
        _fail()
    return target_manifest


def _build_and_validate(repo_root: Path, state_root: Path) -> tuple[dict[str, bytes], dict[str, object]]:
    artifacts = _builder.build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
        repo_root=repo_root, state_root=state_root
    )
    return artifacts, _validate_builder_artifacts(artifacts, repo_root)


def _read_fd(file_fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(file_fd, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _read_leaf(directory_fd: int, name: str, identity: tuple[int, int]) -> bytes:
    item = _stat_at(directory_fd, name)
    if (
        not _same_identity(item, identity)
        or stat.S_ISLNK(item.st_mode)
        or not stat.S_ISREG(item.st_mode)
    ):
        _fail()
    file_fd = os.open(name, _READ_FLAGS, dir_fd=directory_fd)
    try:
        if not _same_identity(os.fstat(file_fd), identity):
            _fail()
        payload = _read_fd(file_fd)
        if (
            not _same_identity(os.fstat(file_fd), identity)
            or not _same_identity(_stat_at(directory_fd, name), identity)
        ):
            _fail()
        return payload
    finally:
        os.close(file_fd)


def _write_all(file_fd: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        count = os.write(file_fd, payload[offset:])
        if type(count) is not int or count <= 0:
            raise OSError(errno.EIO, "short staged write")
        offset += count


def _stage_artifacts(
    staging_fd: int, artifacts: Mapping[str, bytes], identities: dict[str, tuple[int, int]]
) -> None:
    for name, payload in artifacts.items():
        file_fd = os.open(name, _WRITE_FLAGS, 0o600, dir_fd=staging_fd)
        try:
            identity = _identity(os.fstat(file_fd))
            identities[name] = identity
            _write_all(file_fd, payload)
            os.fsync(file_fd)
            os.fchmod(file_fd, 0o644)
        finally:
            os.close(file_fd)
        item = _stat_at(staging_fd, name)
        if (
            not _same_identity(item, identity)
            or stat.S_IMODE(item.st_mode) != 0o644
            or _read_leaf(staging_fd, name, identity) != payload
            or _sha256(_read_leaf(staging_fd, name, identity)) != _sha256(payload)
        ):
            _fail()
    if set(_listdir_fd(staging_fd)) != set(ARTIFACT_NAMES):
        _fail()
    os.fsync(staging_fd)
    os.fchmod(staging_fd, 0o755)


def _rename_noreplace_at(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        _fail()
    if _RENAMEAT2(
        parent_fd,
        os.fsencode(source),
        parent_fd,
        os.fsencode(target),
        _RENAME_NOREPLACE,
    ) != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), f"{source}->{target}")


def _verify_directory_fd(
    directory_fd: int,
    directory_identity: tuple[int, int],
    artifacts: Mapping[str, bytes],
    repo_root: Path,
    *,
    allow_manifest_lifecycle_drift: bool = False,
) -> tuple[dict[str, bytes], dict[str, object]]:
    metadata = os.fstat(directory_fd)
    if (
        not _same_identity(metadata, directory_identity)
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o755
        or set(_listdir_fd(directory_fd)) != set(ARTIFACT_NAMES)
        or len(_listdir_fd(directory_fd)) != 4
    ):
        _fail()
    target_artifacts: dict[str, bytes] = {}
    for name in ARTIFACT_NAMES:
        item = _stat_at(directory_fd, name)
        if (
            stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or stat.S_IMODE(item.st_mode) != 0o644
        ):
            _fail()
        actual = _read_leaf(directory_fd, name, _identity(item))
        target_artifacts[name] = actual
    if allow_manifest_lifecycle_drift:
        target_manifest = _compare_formal_target_with_fresh_builder(
            target_artifacts=target_artifacts,
            fresh_artifacts=artifacts,
            repo_root=repo_root,
        )
    else:
        target_manifest = _validate_builder_artifacts(target_artifacts, repo_root)
        if target_artifacts != artifacts or any(
            _sha256(target_artifacts[name]) != _sha256(artifacts[name]) for name in ARTIFACT_NAMES
        ):
            _fail()
    return target_artifacts, target_manifest


def _cleanup_staging(
    parent_fd: int,
    staging_fd: int | None,
    staging_name: str,
    staging_identity: tuple[int, int],
    leaf_identities: Mapping[str, tuple[int, int]],
) -> None:
    cleanup_fd = staging_fd
    opened_for_cleanup = False
    try:
        if cleanup_fd is None:
            cleanup_fd = os.open(staging_name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
            opened_for_cleanup = True
        if (
            not _same_identity(os.fstat(cleanup_fd), staging_identity)
            or not _same_identity(_stat_at(parent_fd, staging_name), staging_identity)
            or set(_listdir_fd(cleanup_fd)) != set(leaf_identities)
        ):
            raise OSError(errno.ESTALE, "staging cleanup identity mismatch")
        for name, identity in leaf_identities.items():
            item = _stat_at(cleanup_fd, name)
            if (
                not _same_identity(item, identity)
                or stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
            ):
                raise OSError(errno.ESTALE, "staged leaf cleanup identity mismatch")
        for name, identity in leaf_identities.items():
            if not _same_identity(_stat_at(cleanup_fd, name), identity):
                raise OSError(errno.ESTALE, "staged leaf changed before cleanup")
            os.unlink(name, dir_fd=cleanup_fd)
        if _listdir_fd(cleanup_fd):
            raise OSError(errno.ENOTEMPTY, "staging cleanup inventory changed")
        if opened_for_cleanup:
            os.close(cleanup_fd)
            cleanup_fd = None
        os.rmdir(staging_name, dir_fd=parent_fd)
    except BaseException as error:
        raise _CleanupFailure(CLEANUP_ERROR_TOKEN) from error
    finally:
        if opened_for_cleanup and cleanup_fd is not None:
            try:
                os.close(cleanup_fd)
            except OSError:
                pass


def _readiness() -> dict[str, bool]:
    return {
        "sidecar_formal_materializer_implemented": True,
        "formal_sidecar_materialized": True,
        "runtime_consumer_available": False,
        "training_loss_authorized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_performed": False,
        "ready_for_formal_sidecar_materialization_execution": True,
        "ready_for_tensor_materialization": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        _fail()
    try:
        return result.stdout.decode("utf-8")
    except UnicodeError as error:
        raise ValueError(ERROR_TOKEN) from error


def _is_hex(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ancestor, descendant),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        _fail()
    return result.returncode == 0


def _live_identity(repo_root: Path, relative: str) -> dict[str, object]:
    path = repo_root / relative
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o644:
        _fail()
    blob = _run_git(repo_root, ("hash-object", "--no-filters", "--", relative)).strip()
    line = _run_git(repo_root, ("ls-files", "--stage", "--", relative)).strip()
    if not _is_hex(blob):
        _fail()
    if not line:
        return {"tracked": False, "mode": "100644", "blob": blob}
    metadata_text, listed = line.split("\t", 1)
    mode, index_blob, stage = metadata_text.split()
    if listed != relative or stage != "0" or not _is_hex(index_blob):
        _fail()
    return {"tracked": True, "mode": mode, "index_blob": index_blob, "blob": blob}


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _run_git(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _run_git(repo_root, ("rev-parse", "refs/remotes/origin/main")).strip()
    ahead, behind = _run_git(
        repo_root, ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main")
    ).split()
    revisions = set(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines())
    revisions.update(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        statuses: dict[str, str] = {}
        lines = _run_git(
            repo_root, ("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit)
        ).splitlines()
        for line in lines:
            parts = line.split("\t")
            if len(parts) == 2:
                statuses[parts[1]] = parts[0]
        if not set(statuses).intersection(CANDIDATE_PATHS):
            continue
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for relative in CANDIDATE_PATHS:
            line = _run_git(repo_root, ("ls-tree", commit, "--", relative)).strip()
            if line:
                tree_text, listed = line.split("\t", 1)
                mode, kind, blob = tree_text.split()
                if listed != relative or kind != "blob":
                    _fail()
                modes[relative] = mode
                blobs[relative] = blob
        path_commits.append(
            {
                "commit": commit,
                "parents": _run_git(repo_root, ("show", "-s", "--format=%P", commit)).split(),
                "subject": _run_git(repo_root, ("show", "-s", "--format=%s", commit)).strip(),
                "changed_paths": tuple(sorted(statuses)),
                "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
                "path_modes": modes,
                "path_blobs": blobs,
                "ancestor_head": _is_ancestor(repo_root, commit, head),
                "ancestor_origin": _is_ancestor(repo_root, commit, origin),
            }
        )
    return {
        "head": head,
        "origin": origin,
        "ahead": int(ahead),
        "behind": int(behind),
        "branch": _run_git(repo_root, ("branch", "--show-current")).strip(),
        "base_ancestor_head": _is_ancestor(repo_root, BASE_COMMIT, head),
        "base_ancestor_origin": _is_ancestor(repo_root, BASE_COMMIT, origin),
        "tracked": tuple(sorted(_run_git(repo_root, ("diff", "--name-only")).splitlines())),
        "staged": tuple(sorted(_run_git(repo_root, ("diff", "--cached", "--name-only")).splitlines())),
        "untracked": tuple(
            sorted(_run_git(repo_root, ("ls-files", "--others", "--exclude-standard")).splitlines())
        ),
        "porcelain": tuple(
            sorted(
                _run_git(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")).splitlines()
            )
        ),
        "path_commits": path_commits,
        "live_paths": {path: _live_identity(repo_root, path) for path in CANDIDATE_PATHS},
    }


def _derive_lifecycle(facts: object) -> dict[str, object]:
    if (
        type(facts) is not dict
        or facts.get("branch") != BRANCH
        or facts.get("base_ancestor_head") is not True
        or facts.get("base_ancestor_origin") is not True
        or type(facts.get("path_commits")) is not list
        or len(facts["path_commits"]) > 1
        or tuple(facts.get("live_paths", {})) != CANDIDATE_PATHS
    ):
        _fail()
    commits = facts["path_commits"]
    if not commits:
        if (
            facts["head"] != BASE_COMMIT
            or facts["origin"] != BASE_COMMIT
            or (facts["ahead"], facts["behind"]) != (0, 0)
            or facts["tracked"]
            or facts["staged"]
            or facts["untracked"] != CANDIDATE_PATHS
            or facts["porcelain"] != tuple(sorted(f"?? {path}" for path in CANDIDATE_PATHS))
            or any(item["tracked"] is not False for item in facts["live_paths"].values())
        ):
            _fail()
        return {
            "base_commit": BASE_COMMIT,
            "future_formal_subject": FORMAL_COMMIT_SUBJECT,
            "candidate_paths": list(CANDIDATE_PATHS),
            "lifecycle_profile": "dataset_routing_sidecar_materializer_precommit_candidate",
            "formal_candidate_commit": "",
            "origin_main": BASE_COMMIT,
            "ahead": 0,
            "behind": 0,
        }
    commit = commits[0]
    if (
        not _is_hex(commit.get("commit"))
        or commit.get("parents") != [BASE_COMMIT]
        or commit.get("subject") != FORMAL_COMMIT_SUBJECT
        or commit.get("changed_paths") != CANDIDATE_PATHS
        or commit.get("changed_statuses") != {path: "A" for path in CANDIDATE_PATHS}
        or any(commit["path_modes"].get(path) != "100644" for path in CANDIDATE_PATHS)
        or commit.get("ancestor_head") is not True
        or any(
            facts["live_paths"][path]
            != {
                "tracked": True,
                "mode": "100644",
                "index_blob": commit["path_blobs"].get(path),
                "blob": commit["path_blobs"].get(path),
            }
            for path in CANDIDATE_PATHS
        )
        or any(
            path in facts["tracked"] or path in facts["staged"] or path in facts["untracked"]
            for path in CANDIDATE_PATHS
        )
    ):
        _fail()
    common = {
        "base_commit": BASE_COMMIT,
        "future_formal_subject": FORMAL_COMMIT_SUBJECT,
        "candidate_paths": list(CANDIDATE_PATHS),
        "formal_candidate_commit": commit["commit"],
    }
    if commit.get("ancestor_origin") is True:
        return {
            **common,
            "lifecycle_profile": "dataset_routing_sidecar_materializer_published_successor",
            "origin_main": facts["origin"],
            "ahead": facts["ahead"],
            "behind": facts["behind"],
        }
    if (
        facts["head"] != commit["commit"]
        or facts["origin"] != BASE_COMMIT
        or (facts["ahead"], facts["behind"]) != (1, 0)
        or facts["tracked"]
        or facts["staged"]
        or facts["untracked"]
        or facts["porcelain"]
    ):
        _fail()
    return {
        **common,
        "lifecycle_profile": "dataset_routing_sidecar_materializer_committed_unpushed",
        "origin_main": BASE_COMMIT,
        "ahead": 1,
        "behind": 0,
    }


def _summary(
    operation: str,
    output_dir: Path,
    artifacts: Mapping[str, bytes],
    manifest: Mapping[str, object],
    lifecycle: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "output_dir": str(output_dir),
        "artifact_file_count": 4,
        "artifacts": {
            name: {
                "bytes": len(payload),
                "lines": payload.count(b"\n"),
                "sha256": _sha256(payload),
            }
            for name, payload in artifacts.items()
        },
        "source_builder_schema_version": SOURCE_BUILDER_SCHEMA_VERSION,
        "source_builder_commit": SOURCE_BUILDER_COMMIT,
        "source_builder_sha256": SOURCE_BUILDER_SHA256,
        "sample_count": manifest["sample_count"],
        "semantic_task_count": manifest["semantic_task_count"],
        "routing_record_count": manifest["routing_record_count"],
        "global_state_counts": manifest["global_state_counts"],
        "unit_000001_parity_passed": manifest["unit_000001_parity"]["passed"],
        "repository_lifecycle": dict(lifecycle),
        "readiness": _readiness(),
    }


def _verify_existing_impl(
    *, repo_root: Path, state_root: Path, output_dir: Path
) -> dict[str, object]:
    artifacts, _manifest = _build_and_validate(repo_root, state_root)
    repository, _state, target, parent_metadata = _validate_roots_and_output(
        repo_root, state_root, output_dir, require_target=True
    )
    parent_fd = os.open(os.fspath(target.parent), _DIRECTORY_FLAGS)
    target_fd: int | None = None
    try:
        parent_identity = _identity(parent_metadata)
        _assert_parent_identity(parent_fd, target.parent, parent_identity)
        item = _stat_at(parent_fd, target.name)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            _fail()
        target_fd = os.open(target.name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        target_identity = _identity(os.fstat(target_fd))
        if not _same_identity(item, target_identity):
            _fail()
        target_artifacts, target_manifest = _verify_directory_fd(
            target_fd,
            target_identity,
            artifacts,
            repository,
            allow_manifest_lifecycle_drift=True,
        )
        _assert_parent_identity(parent_fd, target.parent, parent_identity)
        if not _same_identity(_stat_at(parent_fd, target.name), target_identity):
            _fail()
        lifecycle = _derive_lifecycle(_collect_lifecycle(repository))
        return _summary("check", target, target_artifacts, target_manifest, lifecycle)
    finally:
        if target_fd is not None:
            os.close(target_fd)
        os.close(parent_fd)


def _verify_existing(
    *, repo_root: Path, state_root: Path, output_dir: Path
) -> dict[str, object]:
    try:
        return _verify_existing_impl(
            repo_root=repo_root, state_root=state_root, output_dir=output_dir
        )
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
    *, repo_root: Path, state_root: Path, output_dir: Path
) -> dict[str, object]:
    """Publish fresh builder Exact4 bytes without ever replacing a target."""

    parent_fd: int | None = None
    staging_fd: int | None = None
    staging_name: str | None = None
    staging_identity: tuple[int, int] | None = None
    leaf_identities: dict[str, tuple[int, int]] = {}
    try:
        artifacts, _manifest = _build_and_validate(repo_root, state_root)
        repository, _state, target, parent_metadata = _validate_roots_and_output(
            repo_root, state_root, output_dir, require_target=False
        )
        parent_fd = os.open(os.fspath(target.parent), _DIRECTORY_FLAGS)
        parent_identity = _identity(parent_metadata)
        _assert_parent_identity(parent_fd, target.parent, parent_identity)
        try:
            _stat_at(parent_fd, target.name)
        except FileNotFoundError:
            pass
        else:
            _fail()
        for _attempt in range(64):
            candidate = f".covapie-current11-routing-stage-{secrets.token_hex(16)}"
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
            staging_name = candidate
            break
        if staging_name is None:
            _fail()
        staging_metadata = _stat_at(parent_fd, staging_name)
        staging_identity = _identity(staging_metadata)
        if (
            stat.S_ISLNK(staging_metadata.st_mode)
            or not stat.S_ISDIR(staging_metadata.st_mode)
            or stat.S_IMODE(staging_metadata.st_mode) != 0o700
        ):
            _fail()
        staging_fd = os.open(staging_name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        staging_metadata = os.fstat(staging_fd)
        if (
            not _same_identity(staging_metadata, staging_identity)
            or stat.S_IMODE(staging_metadata.st_mode) != 0o700
            or not _same_identity(_stat_at(parent_fd, staging_name), staging_identity)
            or _listdir_fd(staging_fd)
        ):
            _fail()
        _stage_artifacts(staging_fd, artifacts, leaf_identities)
        if (
            not _same_identity(os.fstat(staging_fd), staging_identity)
            or not _same_identity(_stat_at(parent_fd, staging_name), staging_identity)
        ):
            _fail()
        try:
            _stat_at(parent_fd, target.name)
        except FileNotFoundError:
            pass
        else:
            _fail()
        _assert_parent_identity(parent_fd, target.parent, parent_identity)
        _rename_noreplace_at(parent_fd, staging_name, target.name)
        if not _same_identity(_stat_at(parent_fd, target.name), staging_identity):
            _fail()
        staging_name = None
        os.fsync(parent_fd)
        target_artifacts, target_manifest = _verify_directory_fd(
            staging_fd, staging_identity, artifacts, repository
        )
        _assert_parent_identity(parent_fd, target.parent, parent_identity)
        if not _same_identity(_stat_at(parent_fd, target.name), staging_identity):
            _fail()
        lifecycle = _derive_lifecycle(_collect_lifecycle(repository))
        return _summary("materialize", target, target_artifacts, target_manifest, lifecycle)
    except BaseException as original:
        if (
            parent_fd is not None
            and staging_name is not None
        ):
            if staging_identity is None:
                raise _CleanupFailure(CLEANUP_ERROR_TOKEN) from original
            try:
                _cleanup_staging(
                    parent_fd,
                    staging_fd,
                    staging_name,
                    staging_identity,
                    leaf_identities,
                )
            except BaseException:
                raise _CleanupFailure(CLEANUP_ERROR_TOKEN) from original
        if isinstance(original, _CleanupFailure):
            raise
        if type(original) is ValueError and str(original) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from original
    finally:
        if staging_fd is not None:
            try:
                os.close(staging_fd)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass
