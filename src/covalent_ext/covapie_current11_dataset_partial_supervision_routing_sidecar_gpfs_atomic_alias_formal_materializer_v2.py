"""Publish the Current11 routing sidecar through a GPFS-safe relative alias."""

from __future__ import annotations

import copy
import errno
import hashlib
import os
import re
import secrets
import stat
import subprocess
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1 as _v1


__all__ = (
    "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2",
)

SCHEMA_VERSION = (
    "covapie_current11_dataset_partial_supervision_routing_sidecar_"
    "gpfs_atomic_alias_formal_materializer_v2"
)
ERROR_TOKEN = (
    "COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_"
    "GPFS_ATOMIC_ALIAS_FORMAL_MATERIALIZER_V2_ERROR"
)
CLEANUP_ERROR_TOKEN = f"{ERROR_TOKEN}_CLEANUP_FAILED"
BASE_COMMIT = "6f3444df7e62517e2e9dfca646a8d8ce9ddc2e56"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 GPFS atomic alias routing sidecar materializer v2"
)
BRANCH = "main"
SOURCE_BUILDER_SCHEMA_VERSION = _v1.SOURCE_BUILDER_SCHEMA_VERSION
SOURCE_BUILDER_COMMIT = _v1.SOURCE_BUILDER_COMMIT
SOURCE_BUILDER_SHA256 = _v1.SOURCE_BUILDER_SHA256
SOURCE_V1_MATERIALIZER_COMMIT = BASE_COMMIT
SOURCE_V1_MATERIALIZER_SHA256 = (
    "5d189c0451a1aad515932bd4e537de9378b79fcbc2987f671d069e0db857aada"
)
SOURCE_V1_MATERIALIZER_PATH = (
    "src/covalent_ext/"
    "covapie_current11_dataset_partial_supervision_routing_sidecar_"
    "formal_materializer_v1.py"
)
MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_dataset_partial_supervision_routing_sidecar_"
    "gpfs_atomic_alias_formal_materializer_v2.py"
)
SCRIPT_PATH = (
    "scripts/materialize_covapie_current11_dataset_partial_supervision_"
    "routing_sidecar_gpfs_atomic_alias_v2.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_dataset_partial_supervision_routing_"
    "sidecar_gpfs_atomic_alias_formal_materializer_v2.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_dataset_partial_supervision_routing_sidecar_"
    "gpfs_atomic_alias_formal_materializer_v2_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))
ARTIFACT_NAMES = _v1.ARTIFACT_NAMES
CANONICAL_BASENAME = "current11-dataset-partial-supervision-routing-sidecar-v1"
OBJECT_PREFIX = ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
AGGREGATE_DOMAIN_TAG = (
    b"COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_"
    b"GPFS_ATOMIC_ALIAS_V2\0"
)
OBJECT_BASENAME_PATTERN = re.compile(
    r"^\.current11-dataset-partial-supervision-routing-sidecar-v2\."
    r"object-sha256-([0-9a-f]{64})-([0-9a-f]{32})$"
)
MAX_OBJECT_CREATE_ATTEMPTS = 64
_PATH_TYPE = type(Path())
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
_WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC


class _CleanupFailure(ValueError):
    pass


def _fail() -> NoReturn:
    raise ValueError(ERROR_TOKEN)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _identity(item: os.stat_result) -> tuple[int, int]:
    return int(item.st_dev), int(item.st_ino)


def _identity_json(identity: tuple[int, int]) -> dict[str, int]:
    return {"st_dev": identity[0], "st_ino": identity[1]}


def _same_identity(item: os.stat_result, expected: tuple[int, int]) -> bool:
    return _identity(item) == expected


def _stat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _listdir_fd(directory_fd: int) -> tuple[str, ...]:
    return tuple(os.listdir(directory_fd))


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
    for component in path.parts[1:]:
        current = current / component
        try:
            metadata = current.lstat()
        except OSError as error:
            raise ValueError(ERROR_TOKEN) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            _fail()
    try:
        if path.resolve(strict=True) != path:
            _fail()
    except (OSError, RuntimeError) as error:
        raise ValueError(ERROR_TOKEN) from error


def _validate_paths(
    repo_root: Path,
    state_root: Path,
    output_path: Path,
    *,
    require_canonical: bool,
) -> tuple[Path, Path, Path, os.stat_result]:
    repository = _require_absolute_real_directory(repo_root)
    state = _require_absolute_real_directory(state_root)
    if (
        type(output_path) is not _PATH_TYPE
        or not output_path.is_absolute()
        or output_path.name != CANONICAL_BASENAME
    ):
        _fail()
    parent = output_path.parent
    _assert_real_chain(parent)
    if output_path != parent / CANONICAL_BASENAME:
        _fail()
    if output_path == repository or repository in output_path.parents:
        _fail()
    try:
        output_path.lstat()
    except FileNotFoundError:
        if require_canonical:
            _fail()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    else:
        if not require_canonical:
            _fail()
    try:
        parent_metadata = parent.lstat()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
        _fail()
    return repository, state, output_path, parent_metadata


def _assert_parent_identity(
    parent_fd: int,
    parent_path: Path,
    expected_identity: tuple[int, int],
    expected_mode: int,
) -> None:
    try:
        lexical = parent_path.lstat()
        resolved = parent_path.resolve(strict=True)
        descriptor = os.fstat(parent_fd)
    except (OSError, RuntimeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        resolved != parent_path
        or stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or not stat.S_ISDIR(descriptor.st_mode)
        or stat.S_IMODE(lexical.st_mode) != expected_mode
        or stat.S_IMODE(descriptor.st_mode) != expected_mode
        or not _same_identity(lexical, expected_identity)
        or not _same_identity(descriptor, expected_identity)
    ):
        _fail()


def _assert_absent(parent_fd: int, canonical_basename: str) -> None:
    try:
        _stat_at(parent_fd, canonical_basename)
    except FileNotFoundError:
        return
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    _fail()


def _validate_v1_materializer_source(repo_root: Path) -> None:
    path = repo_root / SOURCE_V1_MATERIALIZER_PATH
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or _sha256(payload) != SOURCE_V1_MATERIALIZER_SHA256
    ):
        _fail()


def _build_and_validate(
    repo_root: Path, state_root: Path
) -> tuple[dict[str, bytes], dict[str, object]]:
    _validate_v1_materializer_source(repo_root)
    return _v1._build_and_validate(repo_root, state_root)


def _aggregate_sha256(artifacts: Mapping[str, bytes]) -> str:
    if type(artifacts) is not dict or set(artifacts) != set(ARTIFACT_NAMES):
        _fail()
    digest = hashlib.sha256()
    digest.update(AGGREGATE_DOMAIN_TAG)
    for name in ARTIFACT_NAMES:
        payload = artifacts[name]
        if type(payload) is not bytes:
            _fail()
        encoded_name = name.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(8, "big", signed=False))
        digest.update(encoded_name)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _parse_object_basename(name: object) -> tuple[str, str]:
    if (
        type(name) is not str
        or not name
        or os.path.isabs(name)
        or "/" in name
        or name in (".", "..")
        or ".." in name
    ):
        _fail()
    match = OBJECT_BASENAME_PATTERN.fullmatch(name)
    if match is None:
        _fail()
    return match.group(1), match.group(2)


def _read_fd(file_fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(file_fd, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _write_all(file_fd: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        count = os.write(file_fd, payload[offset:])
        if type(count) is not int or count <= 0:
            raise OSError(errno.EIO, "short object write")
        offset += count


def _assert_object_identity(
    parent_fd: int,
    object_fd: int,
    object_basename: str,
    object_identity: tuple[int, int],
    expected_mode: int,
) -> None:
    try:
        lexical = _stat_at(parent_fd, object_basename)
        descriptor = os.fstat(object_fd)
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or not stat.S_ISDIR(descriptor.st_mode)
        or stat.S_IMODE(lexical.st_mode) != expected_mode
        or stat.S_IMODE(descriptor.st_mode) != expected_mode
        or not _same_identity(lexical, object_identity)
        or not _same_identity(descriptor, object_identity)
    ):
        _fail()


def _read_leaf(
    object_fd: int,
    name: str,
    expected_identity: tuple[int, int],
    expected_mode: int = 0o644,
) -> bytes:
    try:
        before = _stat_at(object_fd, name)
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != expected_mode
        or not _same_identity(before, expected_identity)
    ):
        _fail()
    file_fd = os.open(name, _READ_FLAGS, dir_fd=object_fd)
    try:
        descriptor_before = os.fstat(file_fd)
        if (
            stat.S_IMODE(descriptor_before.st_mode) != expected_mode
            or not _same_identity(descriptor_before, expected_identity)
        ):
            _fail()
        payload = _read_fd(file_fd)
        descriptor_after = os.fstat(file_fd)
        after = _stat_at(object_fd, name)
        if (
            stat.S_IMODE(descriptor_after.st_mode) != expected_mode
            or stat.S_IMODE(after.st_mode) != expected_mode
            or not _same_identity(descriptor_after, expected_identity)
            or not _same_identity(after, expected_identity)
        ):
            _fail()
        return payload
    finally:
        os.close(file_fd)


def _write_artifacts(
    object_fd: int,
    artifacts: Mapping[str, bytes],
    leaf_identities: dict[str, tuple[int, int]],
) -> None:
    for name in ARTIFACT_NAMES:
        payload = artifacts[name]
        file_fd = os.open(name, _WRITE_FLAGS, 0o600, dir_fd=object_fd)
        try:
            metadata = os.fstat(file_fd)
            identity = _identity(metadata)
            leaf_identities[name] = identity
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                _fail()
            _write_all(file_fd, payload)
            os.fchmod(file_fd, 0o644)
            os.fsync(file_fd)
            final = os.fstat(file_fd)
            if (
                not _same_identity(final, identity)
                or stat.S_IMODE(final.st_mode) != 0o644
            ):
                _fail()
        finally:
            os.close(file_fd)
        actual = _read_leaf(object_fd, name, identity)
        if actual != payload or _sha256(actual) != _sha256(payload):
            _fail()
    if set(_listdir_fd(object_fd)) != set(ARTIFACT_NAMES) or len(_listdir_fd(object_fd)) != 4:
        _fail()


def _read_object_artifacts(
    *,
    parent_fd: int,
    object_fd: int,
    object_basename: str,
    object_identity: tuple[int, int],
    leaf_identities: Mapping[str, tuple[int, int]],
    object_mode: int,
) -> dict[str, bytes]:
    _assert_object_identity(
        parent_fd, object_fd, object_basename, object_identity, object_mode
    )
    inventory = _listdir_fd(object_fd)
    if set(inventory) != set(ARTIFACT_NAMES) or len(inventory) != 4:
        _fail()
    if set(leaf_identities) != set(ARTIFACT_NAMES):
        _fail()
    artifacts = {
        name: _read_leaf(object_fd, name, leaf_identities[name]) for name in ARTIFACT_NAMES
    }
    _assert_object_identity(
        parent_fd, object_fd, object_basename, object_identity, object_mode
    )
    return artifacts


def _validate_stored_exact4(
    stored_artifacts: dict[str, bytes],
    fresh_artifacts: dict[str, bytes],
    repo_root: Path,
    *,
    allow_lifecycle_drift: bool,
) -> dict[str, object]:
    if allow_lifecycle_drift:
        return _v1._compare_formal_target_with_fresh_builder(
            target_artifacts=stored_artifacts,
            fresh_artifacts=fresh_artifacts,
            repo_root=repo_root,
        )
    manifest = _v1._validate_builder_artifacts(stored_artifacts, repo_root)
    if stored_artifacts != fresh_artifacts or any(
        _sha256(stored_artifacts[name]) != _sha256(fresh_artifacts[name])
        for name in ARTIFACT_NAMES
    ):
        _fail()
    return manifest


def _canonical_relation(
    parent_fd: int, canonical_basename: str, object_basename: str
) -> str:
    try:
        metadata = _stat_at(parent_fd, canonical_basename)
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "ambiguous"
    if not stat.S_ISLNK(metadata.st_mode):
        return "unrelated"
    try:
        target = os.readlink(canonical_basename, dir_fd=parent_fd)
    except OSError:
        return "ambiguous"
    return "owned" if target == object_basename else "unrelated"


def _validate_cleanup_inventory(
    parent_fd: int,
    object_fd: int,
    object_basename: str,
    object_identity: tuple[int, int],
    remaining: Mapping[str, tuple[int, int]],
) -> None:
    lexical = _stat_at(parent_fd, object_basename)
    descriptor = os.fstat(object_fd)
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or not stat.S_ISDIR(descriptor.st_mode)
        or not _same_identity(lexical, object_identity)
        or not _same_identity(descriptor, object_identity)
        or set(_listdir_fd(object_fd)) != set(remaining)
    ):
        raise OSError(errno.ESTALE, "object cleanup identity mismatch")
    for name, identity in remaining.items():
        item = _stat_at(object_fd, name)
        if (
            stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or not _same_identity(item, identity)
        ):
            raise OSError(errno.ESTALE, "leaf cleanup identity mismatch")


def _cleanup_object(
    *,
    parent_fd: int,
    parent_path: Path,
    parent_identity: tuple[int, int],
    parent_mode: int,
    object_fd: int | None,
    object_basename: str,
    object_identity: tuple[int, int],
    leaf_identities: Mapping[str, tuple[int, int]],
) -> None:
    cleanup_fd = object_fd
    opened_for_cleanup = False
    try:
        _assert_parent_identity(parent_fd, parent_path, parent_identity, parent_mode)
        if cleanup_fd is None:
            cleanup_fd = os.open(object_basename, _DIRECTORY_FLAGS, dir_fd=parent_fd)
            opened_for_cleanup = True
        remaining = dict(leaf_identities)
        _validate_cleanup_inventory(
            parent_fd,
            cleanup_fd,
            object_basename,
            object_identity,
            remaining,
        )
        for name in ARTIFACT_NAMES:
            if name not in remaining:
                continue
            _assert_parent_identity(parent_fd, parent_path, parent_identity, parent_mode)
            _validate_cleanup_inventory(
                parent_fd,
                cleanup_fd,
                object_basename,
                object_identity,
                remaining,
            )
            os.unlink(name, dir_fd=cleanup_fd)
            del remaining[name]
        _assert_parent_identity(parent_fd, parent_path, parent_identity, parent_mode)
        _validate_cleanup_inventory(
            parent_fd,
            cleanup_fd,
            object_basename,
            object_identity,
            remaining,
        )
        if opened_for_cleanup:
            os.close(cleanup_fd)
            cleanup_fd = None
        os.rmdir(object_basename, dir_fd=parent_fd)
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
        "gpfs_atomic_alias_materializer_v2_implemented": True,
        "formal_sidecar_materialized": True,
        "canonical_entry_is_relative_symlink": True,
        "runtime_consumer_available": False,
        "training_loss_authorized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_performed": False,
        "ready_for_formal_sidecar_materialization_execution": True,
        "ready_for_tensor_projection_contract_design": False,
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
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail()
    if stat.S_IMODE(metadata.st_mode) != 0o644:
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
        repo_root,
        ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"),
    ).split()
    revisions = set(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines())
    revisions.update(
        _run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines()
    )
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        statuses: dict[str, str] = {}
        lines = _run_git(
            repo_root,
            ("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit),
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
                "parents": _run_git(
                    repo_root, ("show", "-s", "--format=%P", commit)
                ).split(),
                "subject": _run_git(
                    repo_root, ("show", "-s", "--format=%s", commit)
                ).strip(),
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
        "staged": tuple(
            sorted(_run_git(repo_root, ("diff", "--cached", "--name-only")).splitlines())
        ),
        "untracked": tuple(
            sorted(
                _run_git(repo_root, ("ls-files", "--others", "--exclude-standard")).splitlines()
            )
        ),
        "porcelain": tuple(
            sorted(
                _run_git(
                    repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
                ).splitlines()
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
            or facts["porcelain"]
            != tuple(sorted(f"?? {path}" for path in CANDIDATE_PATHS))
            or any(item["tracked"] is not False for item in facts["live_paths"].values())
        ):
            _fail()
        return {
            "base_commit": BASE_COMMIT,
            "future_formal_subject": FORMAL_COMMIT_SUBJECT,
            "candidate_paths": list(CANDIDATE_PATHS),
            "lifecycle_profile": (
                "dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_"
                "precommit_candidate"
            ),
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
            "lifecycle_profile": (
                "dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_"
                "published_successor"
            ),
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
        "lifecycle_profile": (
            "dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_"
            "committed_unpushed"
        ),
        "origin_main": BASE_COMMIT,
        "ahead": 1,
        "behind": 0,
    }


def _summary(
    *,
    operation: str,
    output_path: Path,
    canonical_identity: tuple[int, int],
    canonical_symlink_target: str,
    object_identity: tuple[int, int],
    aggregate_sha256: str,
    stored_artifacts: Mapping[str, bytes],
    stored_manifest: Mapping[str, object],
    lifecycle: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "output_path": str(output_path),
        "canonical_entry_type": "relative_symlink",
        "canonical_symlink_target": canonical_symlink_target,
        "canonical_identity": _identity_json(canonical_identity),
        "object_directory_name": canonical_symlink_target,
        "object_identity": _identity_json(object_identity),
        "aggregate_sha256": aggregate_sha256,
        "artifact_file_count": 4,
        "artifacts": {
            name: {
                "bytes": len(stored_artifacts[name]),
                "lines": stored_artifacts[name].count(b"\n"),
                "sha256": _sha256(stored_artifacts[name]),
            }
            for name in ARTIFACT_NAMES
        },
        "source_builder_schema_version": SOURCE_BUILDER_SCHEMA_VERSION,
        "source_builder_commit": SOURCE_BUILDER_COMMIT,
        "source_builder_sha256": SOURCE_BUILDER_SHA256,
        "source_v1_materializer_commit": SOURCE_V1_MATERIALIZER_COMMIT,
        "source_v1_materializer_sha256": SOURCE_V1_MATERIALIZER_SHA256,
        "sample_count": stored_manifest["sample_count"],
        "semantic_task_count": stored_manifest["semantic_task_count"],
        "routing_record_count": stored_manifest["routing_record_count"],
        "global_state_counts": copy.deepcopy(stored_manifest["global_state_counts"]),
        "unit_000001_parity_passed": stored_manifest["unit_000001_parity"]["passed"],
        "repository_lifecycle": dict(lifecycle),
        "readiness": _readiness(),
    }


def _verify_existing_impl(
    *, repo_root: Path, state_root: Path, output_path: Path
) -> dict[str, object]:
    fresh_artifacts, _fresh_manifest = _build_and_validate(repo_root, state_root)
    repository, _state, canonical, parent_metadata = _validate_paths(
        repo_root, state_root, output_path, require_canonical=True
    )
    parent_fd = os.open(os.fspath(canonical.parent), _DIRECTORY_FLAGS)
    object_fd: int | None = None
    try:
        parent_identity = _identity(parent_metadata)
        parent_mode = stat.S_IMODE(parent_metadata.st_mode)
        _assert_parent_identity(
            parent_fd, canonical.parent, parent_identity, parent_mode
        )
        alias_metadata = _stat_at(parent_fd, canonical.name)
        alias_identity = _identity(alias_metadata)
        if not stat.S_ISLNK(alias_metadata.st_mode):
            _fail()
        link_text = os.readlink(canonical.name, dir_fd=parent_fd)
        aggregate, _nonce = _parse_object_basename(link_text)
        expected_object = canonical.parent / link_text
        try:
            if canonical.resolve(strict=True) != expected_object:
                _fail()
        except (OSError, RuntimeError) as error:
            raise ValueError(ERROR_TOKEN) from error
        object_metadata = _stat_at(parent_fd, link_text)
        if (
            stat.S_ISLNK(object_metadata.st_mode)
            or not stat.S_ISDIR(object_metadata.st_mode)
            or stat.S_IMODE(object_metadata.st_mode) != 0o755
        ):
            _fail()
        object_fd = os.open(link_text, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        object_identity = _identity(object_metadata)
        _assert_object_identity(
            parent_fd, object_fd, link_text, object_identity, 0o755
        )
        inventory = _listdir_fd(object_fd)
        if set(inventory) != set(ARTIFACT_NAMES) or len(inventory) != 4:
            _fail()
        leaf_identities: dict[str, tuple[int, int]] = {}
        for name in ARTIFACT_NAMES:
            item = _stat_at(object_fd, name)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
                or stat.S_IMODE(item.st_mode) != 0o644
            ):
                _fail()
            leaf_identities[name] = _identity(item)
        stored_artifacts = _read_object_artifacts(
            parent_fd=parent_fd,
            object_fd=object_fd,
            object_basename=link_text,
            object_identity=object_identity,
            leaf_identities=leaf_identities,
            object_mode=0o755,
        )
        stored_manifest = _validate_stored_exact4(
            stored_artifacts,
            fresh_artifacts,
            repository,
            allow_lifecycle_drift=True,
        )
        if _aggregate_sha256(stored_artifacts) != aggregate:
            _fail()
        lifecycle = _derive_lifecycle(_collect_lifecycle(repository))
        _assert_parent_identity(
            parent_fd, canonical.parent, parent_identity, parent_mode
        )
        final_alias = _stat_at(parent_fd, canonical.name)
        if (
            not stat.S_ISLNK(final_alias.st_mode)
            or not _same_identity(final_alias, alias_identity)
            or os.readlink(canonical.name, dir_fd=parent_fd) != link_text
        ):
            _fail()
        _assert_object_identity(
            parent_fd, object_fd, link_text, object_identity, 0o755
        )
        for name, identity in leaf_identities.items():
            item = _stat_at(object_fd, name)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
                or stat.S_IMODE(item.st_mode) != 0o644
                or not _same_identity(item, identity)
            ):
                _fail()
        return _summary(
            operation="check",
            output_path=canonical,
            canonical_identity=alias_identity,
            canonical_symlink_target=link_text,
            object_identity=object_identity,
            aggregate_sha256=aggregate,
            stored_artifacts=stored_artifacts,
            stored_manifest=stored_manifest,
            lifecycle=lifecycle,
        )
    finally:
        if object_fd is not None:
            os.close(object_fd)
        os.close(parent_fd)


def _verify_existing(
    *, repo_root: Path, state_root: Path, output_path: Path
) -> dict[str, object]:
    try:
        return _verify_existing_impl(
            repo_root=repo_root, state_root=state_root, output_path=output_path
        )
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
    *, repo_root: Path, state_root: Path, output_path: Path
) -> dict[str, object]:
    """Materialize immutable Exact4 and publish one relative canonical symlink."""

    parent_fd: int | None = None
    object_fd: int | None = None
    parent_path: Path | None = None
    parent_identity: tuple[int, int] | None = None
    parent_mode: int | None = None
    object_basename: str | None = None
    object_identity: tuple[int, int] | None = None
    leaf_identities: dict[str, tuple[int, int]] = {}
    publication_succeeded = False
    try:
        fresh_artifacts, _fresh_manifest = _build_and_validate(repo_root, state_root)
        aggregate = _aggregate_sha256(fresh_artifacts)
        repository, _state, canonical, parent_metadata = _validate_paths(
            repo_root, state_root, output_path, require_canonical=False
        )
        parent_path = canonical.parent
        parent_identity = _identity(parent_metadata)
        parent_mode = stat.S_IMODE(parent_metadata.st_mode)
        parent_fd = os.open(os.fspath(parent_path), _DIRECTORY_FLAGS)
        _assert_parent_identity(parent_fd, parent_path, parent_identity, parent_mode)
        _assert_absent(parent_fd, canonical.name)
        for _attempt in range(MAX_OBJECT_CREATE_ATTEMPTS):
            nonce = secrets.token_hex(16)
            if type(nonce) is not str or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
                _fail()
            candidate = f"{OBJECT_PREFIX}{aggregate}-{nonce}"
            _parse_object_basename(candidate)
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
            object_basename = candidate
            break
        if object_basename is None:
            _fail()
        object_metadata = _stat_at(parent_fd, object_basename)
        object_identity = _identity(object_metadata)
        if (
            stat.S_ISLNK(object_metadata.st_mode)
            or not stat.S_ISDIR(object_metadata.st_mode)
            or stat.S_IMODE(object_metadata.st_mode) != 0o700
        ):
            _fail()
        object_fd = os.open(object_basename, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        _assert_object_identity(
            parent_fd, object_fd, object_basename, object_identity, 0o700
        )
        if _listdir_fd(object_fd):
            _fail()
        _write_artifacts(object_fd, fresh_artifacts, leaf_identities)
        stored_artifacts = _read_object_artifacts(
            parent_fd=parent_fd,
            object_fd=object_fd,
            object_basename=object_basename,
            object_identity=object_identity,
            leaf_identities=leaf_identities,
            object_mode=0o700,
        )
        stored_manifest = _validate_stored_exact4(
            stored_artifacts,
            fresh_artifacts,
            repository,
            allow_lifecycle_drift=False,
        )
        if _aggregate_sha256(stored_artifacts) != aggregate:
            _fail()
        os.fchmod(object_fd, 0o755)
        os.fsync(object_fd)
        _assert_object_identity(
            parent_fd, object_fd, object_basename, object_identity, 0o755
        )
        for name, identity in leaf_identities.items():
            item = _stat_at(object_fd, name)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
                or stat.S_IMODE(item.st_mode) != 0o644
                or not _same_identity(item, identity)
            ):
                _fail()
        _assert_absent(parent_fd, canonical.name)
        _assert_parent_identity(parent_fd, parent_path, parent_identity, parent_mode)
        os.symlink(
            object_basename,
            canonical.name,
            target_is_directory=True,
            dir_fd=parent_fd,
        )
        publication_succeeded = True
        alias_metadata = _stat_at(parent_fd, canonical.name)
        alias_identity = _identity(alias_metadata)
        if (
            not stat.S_ISLNK(alias_metadata.st_mode)
            or os.readlink(canonical.name, dir_fd=parent_fd) != object_basename
        ):
            _fail()
        os.fsync(parent_fd)
        stored_artifacts = _read_object_artifacts(
            parent_fd=parent_fd,
            object_fd=object_fd,
            object_basename=object_basename,
            object_identity=object_identity,
            leaf_identities=leaf_identities,
            object_mode=0o755,
        )
        stored_manifest = _validate_stored_exact4(
            stored_artifacts,
            fresh_artifacts,
            repository,
            allow_lifecycle_drift=False,
        )
        if _aggregate_sha256(stored_artifacts) != aggregate:
            _fail()
        lifecycle = _derive_lifecycle(_collect_lifecycle(repository))
        _assert_parent_identity(parent_fd, parent_path, parent_identity, parent_mode)
        final_alias = _stat_at(parent_fd, canonical.name)
        if (
            not stat.S_ISLNK(final_alias.st_mode)
            or not _same_identity(final_alias, alias_identity)
            or os.readlink(canonical.name, dir_fd=parent_fd) != object_basename
        ):
            _fail()
        _assert_object_identity(
            parent_fd, object_fd, object_basename, object_identity, 0o755
        )
        for name, identity in leaf_identities.items():
            item = _stat_at(object_fd, name)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
                or stat.S_IMODE(item.st_mode) != 0o644
                or not _same_identity(item, identity)
            ):
                _fail()
        return _summary(
            operation="materialize",
            output_path=canonical,
            canonical_identity=alias_identity,
            canonical_symlink_target=object_basename,
            object_identity=object_identity,
            aggregate_sha256=aggregate,
            stored_artifacts=stored_artifacts,
            stored_manifest=stored_manifest,
            lifecycle=lifecycle,
        )
    except BaseException as original:
        should_cleanup = False
        if (
            not publication_succeeded
            and parent_fd is not None
            and object_basename is not None
        ):
            relation = _canonical_relation(parent_fd, CANONICAL_BASENAME, object_basename)
            should_cleanup = relation in ("absent", "unrelated")
        if should_cleanup:
            if (
                parent_path is None
                or parent_identity is None
                or parent_mode is None
                or object_identity is None
            ):
                raise _CleanupFailure(CLEANUP_ERROR_TOKEN) from original
            try:
                _cleanup_object(
                    parent_fd=parent_fd,
                    parent_path=parent_path,
                    parent_identity=parent_identity,
                    parent_mode=parent_mode,
                    object_fd=object_fd,
                    object_basename=object_basename,
                    object_identity=object_identity,
                    leaf_identities=leaf_identities,
                )
            except BaseException:
                raise _CleanupFailure(CLEANUP_ERROR_TOKEN) from original
        if isinstance(original, _CleanupFailure):
            raise
        if type(original) is ValueError and str(original) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from original
    finally:
        if object_fd is not None:
            try:
                os.close(object_fd)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass
