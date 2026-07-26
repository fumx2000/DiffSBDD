"""Shared hermetic Git lifecycle test harness for CovaPIE stages."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


__all__ = (
    "HermeticLifecycleState",
    "HermeticLifecycleMatrixReport",
    "exercise_hermetic_git_lifecycle_matrix",
)

LIFECYCLES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".tmp",
    ".part",
)
_OID_PATTERN = re.compile(r"[0-9a-f]{40}")
_PATH_TYPE = type(Path())
_COMMIT_ENV = {
    "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
}
_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "LC_ALL": "C",
}


@dataclass(frozen=True)
class HermeticLifecycleState:
    """A closed observation of one generated Git lifecycle."""

    lifecycle: str
    repository_path: str
    head: str
    main_oid: str
    origin_main_oid: str
    origin_head_symbolic_target: str
    origin_head_resolved_oid: str
    branch: str
    worktree_count: int
    status_entry_count: int


@dataclass(frozen=True)
class HermeticLifecycleMatrixReport:
    """Evidence returned after the complete Exact4 matrix is cleaned."""

    base_commit: str
    pre_commit: HermeticLifecycleState
    detached_candidate_post_commit: HermeticLifecycleState
    formal_main_post_commit_unpushed: HermeticLifecycleState
    formal_main_post_push: HermeticLifecycleState
    candidate_commit: str
    candidate_parent: str
    candidate_subject: str
    exact_path_count: int
    cleanup_verified: bool


@dataclass(frozen=True)
class _SourceRepositorySnapshot:
    head: bytes
    index: bytes
    status: bytes
    refs: bytes
    worktrees: bytes


def _raise_git_failure(
    args: tuple[str, ...],
    cwd: Path,
    result: subprocess.CompletedProcess[bytes],
) -> NoReturn:
    stdout = result.stdout.decode("utf-8", "backslashreplace").strip()
    stderr = result.stderr.decode("utf-8", "backslashreplace").strip()
    detail = "; ".join(
        item
        for item in (
            f"stdout={stdout!r}" if stdout else "",
            f"stderr={stderr!r}" if stderr else "",
        )
        if item
    )
    suffix = f" ({detail})" if detail else ""
    raise RuntimeError(
        f"Git command failed with rc={result.returncode} in {cwd}: "
        f"{args!r}{suffix}"
    )


def _git_bytes(
    repository: Path,
    *arguments: str,
    extra_env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    args = ("git", *arguments)
    environment = dict(_GIT_ENV)
    if extra_env is not None:
        environment.update(extra_env)
    try:
        result = subprocess.run(
            args,
            cwd=repository,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(
            f"unable to execute local Git command in {repository}: {args!r}"
        ) from exc
    if check and result.returncode != 0:
        _raise_git_failure(args, repository, result)
    return result


def _git_text(
    repository: Path,
    *arguments: str,
    extra_env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = _git_bytes(
        repository,
        *arguments,
        extra_env=extra_env,
        check=check,
    )
    return subprocess.CompletedProcess(
        result.args,
        result.returncode,
        result.stdout.decode("utf-8", "strict"),
        result.stderr.decode("utf-8", "strict"),
    )


def _git_scalar(repository: Path, *arguments: str) -> str:
    lines = _git_text(repository, *arguments).stdout.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise RuntimeError(f"Git scalar query was not singular: {arguments!r}")
    return lines[0]


def _validate_path_argument(name: str, value: object) -> Path:
    if type(value) is not _PATH_TYPE:
        raise TypeError(f"{name} must be an exact {_PATH_TYPE.__name__}")
    path = value
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"{name} must be an existing non-symlink directory")
    return path.resolve(strict=True)


def _validate_inputs(
    source_repository: object,
    workspace_root: object,
    base_commit: object,
    formal_commit_subject: object,
    exact_paths: object,
) -> tuple[Path, Path, str, str, tuple[Path, ...]]:
    source = _validate_path_argument("source_repository", source_repository)
    workspace = _validate_path_argument("workspace_root", workspace_root)
    if workspace == source or source in workspace.parents:
        raise ValueError("workspace_root must be outside source_repository")
    if type(base_commit) is not str:
        raise TypeError("base_commit must be an exact str")
    if _OID_PATTERN.fullmatch(base_commit) is None:
        raise ValueError("base_commit must be exactly 40 lowercase hex digits")
    if type(formal_commit_subject) is not str:
        raise TypeError("formal_commit_subject must be an exact str")
    if (
        not formal_commit_subject
        or "\n" in formal_commit_subject
        or "\r" in formal_commit_subject
        or "\0" in formal_commit_subject
    ):
        raise ValueError("formal_commit_subject must be a nonempty single line")
    if type(exact_paths) is not tuple:
        raise TypeError("exact_paths must be an exact tuple")
    if not exact_paths:
        raise ValueError("exact_paths must be nonempty")

    normalized: list[Path] = []
    names: set[str] = set()
    for item in exact_paths:
        if type(item) is not _PATH_TYPE:
            raise TypeError("every exact_paths item must be an exact path")
        if (
            item.is_absolute()
            or item == Path()
            or any(part in ("", ".", "..") for part in item.parts)
            or ".git" in item.parts
        ):
            raise ValueError(f"unsafe exact path: {item!s}")
        if any(ord(character) < 32 for character in item.as_posix()):
            raise ValueError(f"control character in exact path: {item!s}")
        name = item.as_posix()
        if name in names:
            raise ValueError(f"duplicate exact path: {name}")
        if item.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"forbidden exact-path suffix: {name}")
        names.add(name)
        normalized.append(item)

    probe = _git_text(source, "rev-parse", "--show-toplevel", check=False)
    if probe.returncode != 0:
        raise ValueError("source_repository is not a Git worktree")
    if Path(probe.stdout.strip()).resolve(strict=True) != source:
        raise ValueError("source_repository must be the Git worktree root")
    base_probe = _git_text(
        source,
        "cat-file",
        "-e",
        f"{base_commit}^{{commit}}",
        check=False,
    )
    if base_probe.returncode != 0:
        raise ValueError("explicit BASE commit does not exist in source")

    for relative in normalized:
        target = source / relative
        current = source
        for component in relative.parts:
            current = current / component
            if current.is_symlink():
                raise ValueError(f"source path crosses a symlink: {relative}")
        if not target.exists() or not target.is_file():
            raise ValueError(f"source file is missing or not regular: {relative}")
        mode = stat.S_IMODE(target.stat(follow_symlinks=False).st_mode)
        if mode & 0o111:
            raise ValueError(f"source file is executable: {relative}")
        present_at_base = _git_text(
            source,
            "cat-file",
            "-e",
            f"{base_commit}:{relative.as_posix()}",
            check=False,
        )
        if present_at_base.returncode == 0:
            raise ValueError(f"exact path already exists at explicit BASE: {relative}")
    return source, workspace, base_commit, formal_commit_subject, tuple(normalized)


def _source_snapshot(repository: Path) -> _SourceRepositorySnapshot:
    status = _git_bytes(
        repository,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    ).stdout
    index_name = _git_scalar(repository, "rev-parse", "--git-path", "index")
    index_path = Path(index_name)
    if not index_path.is_absolute():
        index_path = repository / index_path
    index = index_path.read_bytes() if index_path.exists() else b""
    symbolic = _git_bytes(
        repository,
        "symbolic-ref",
        "--quiet",
        "HEAD",
        check=False,
    )
    head = (
        _git_bytes(repository, "rev-parse", "--verify", "HEAD").stdout
        + b"\0"
        + symbolic.stdout
    )
    refs = _git_bytes(
        repository,
        "for-each-ref",
        "--sort=refname",
        "--format=%(refname)%09%(objectname)%09%(objecttype)",
    ).stdout
    worktrees = _git_bytes(repository, "worktree", "list", "--porcelain").stdout
    return _SourceRepositorySnapshot(head, index, status, refs, worktrees)


def _copy_exact_paths(
    source_repository: Path,
    destination_repository: Path,
    exact_paths: tuple[Path, ...],
) -> None:
    for relative in exact_paths:
        source = source_repository / relative
        destination = destination_repository / relative
        if destination.exists() or destination.is_symlink():
            raise RuntimeError(f"destination exact path already exists: {relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
        destination.chmod(0o644)


def _ref_inventory(repository: Path) -> tuple[tuple[str, str, str], ...]:
    rows = []
    for line in _git_text(
        repository,
        "for-each-ref",
        "--sort=refname",
        "--format=%(refname)%09%(objectname)%09%(objecttype)",
    ).stdout.splitlines():
        pieces = line.split("\t")
        if len(pieces) != 3:
            raise RuntimeError("malformed Git ref inventory")
        rows.append((pieces[0], pieces[1], pieces[2]))
    return tuple(rows)


def _assert_bare_remote(remote: Path, expected_base: str) -> None:
    if _git_scalar(remote, "rev-parse", "--is-bare-repository") != "true":
        raise RuntimeError("temporary remote is not bare")
    if _git_scalar(remote, "symbolic-ref", "HEAD") != "refs/heads/main":
        raise RuntimeError("temporary remote HEAD drift")
    expected = (("refs/heads/main", expected_base, "commit"),)
    if _ref_inventory(remote) != expected:
        raise RuntimeError("temporary remote was not seeded only from explicit BASE")


def _assert_clone_refs(
    repository: Path,
    *,
    expected_main: str,
    expected_origin_main: str,
    remote: Path,
) -> None:
    expected = (
        ("refs/heads/main", expected_main, "commit"),
        ("refs/remotes/origin/HEAD", expected_origin_main, "commit"),
        ("refs/remotes/origin/main", expected_origin_main, "commit"),
    )
    if _ref_inventory(repository) != expected:
        raise RuntimeError("clone persistent-ref closure drift")
    if (
        _git_scalar(repository, "symbolic-ref", "refs/remotes/origin/HEAD")
        != "refs/remotes/origin/main"
        or _git_scalar(repository, "rev-parse", "refs/remotes/origin/HEAD")
        != expected_origin_main
    ):
        raise RuntimeError("origin/HEAD symbolic or resolved OID drift")
    observed_url = Path(
        _git_scalar(repository, "remote", "get-url", "origin")
    ).resolve(strict=True)
    if observed_url != remote.resolve(strict=True):
        raise RuntimeError("clone source is not the temporary bare remote")


def _worktree_count(repository: Path) -> int:
    return len(_worktree_records(repository))


def _worktree_records(
    repository: Path,
) -> tuple[tuple[Path, str, str, bool], ...]:
    payload = _git_text(repository, "worktree", "list", "--porcelain").stdout
    records = []
    for block in tuple(
        item for item in payload.strip().split("\n\n") if item
    ):
        values: dict[str, str] = {}
        detached = False
        for line in block.splitlines():
            key, separator, value = line.partition(" ")
            if key == "detached" and not separator:
                detached = True
            elif not separator:
                raise RuntimeError("malformed worktree record")
            else:
                values[key] = value
        if not {"worktree", "HEAD"} <= set(values):
            raise RuntimeError("incomplete worktree record")
        records.append(
            (
                Path(values["worktree"]).resolve(strict=True),
                values["HEAD"],
                values.get("branch", ""),
                detached,
            )
        )
    return tuple(records)


def _status_entries(repository: Path) -> tuple[bytes, ...]:
    payload = _git_bytes(
        repository,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    ).stdout
    return tuple(item for item in payload.split(b"\0") if item)


def _capture_state(
    repository: Path,
    *,
    lifecycle: str,
    expected_main: str,
    expected_origin_main: str,
    expected_worktree_count: int,
    expected_status_entries: tuple[bytes, ...],
    remote: Path,
) -> HermeticLifecycleState:
    if lifecycle not in LIFECYCLES:
        raise RuntimeError("unsupported lifecycle label")
    _assert_clone_refs(
        repository,
        expected_main=expected_main,
        expected_origin_main=expected_origin_main,
        remote=remote,
    )
    head = _git_scalar(repository, "rev-parse", "HEAD")
    main_oid = _git_scalar(repository, "rev-parse", "refs/heads/main")
    origin_main_oid = _git_scalar(
        repository, "rev-parse", "refs/remotes/origin/main"
    )
    symbolic = _git_scalar(
        repository, "symbolic-ref", "refs/remotes/origin/HEAD"
    )
    resolved = _git_scalar(
        repository, "rev-parse", "refs/remotes/origin/HEAD"
    )
    branch_query = _git_text(
        repository,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        check=False,
    )
    branch = branch_query.stdout.strip() if branch_query.returncode == 0 else "DETACHED"
    worktrees = _worktree_records(repository)
    count = len(worktrees)
    entries = _status_entries(repository)
    if count != expected_worktree_count:
        raise RuntimeError(f"{lifecycle} worktree topology drift")
    if (
        len(entries) != len(expected_status_entries)
        or set(entries) != set(expected_status_entries)
    ):
        raise RuntimeError(f"{lifecycle} status inventory drift")
    expected_head = expected_main if branch == "main" else head
    if main_oid != expected_main or origin_main_oid != expected_origin_main:
        raise RuntimeError(f"{lifecycle} formal ref OID drift")
    if branch not in ("main", "DETACHED") or head != expected_head:
        raise RuntimeError(f"{lifecycle} HEAD/branch topology drift")
    current_path = repository.resolve(strict=True)
    if branch == "main":
        expected_worktrees = (
            (current_path, head, "refs/heads/main", False),
        )
        if worktrees != expected_worktrees:
            raise RuntimeError(f"{lifecycle} single-main-worktree drift")
    else:
        detached_rows = tuple(
            row
            for row in worktrees
            if row == (current_path, head, "", True)
        )
        main_rows = tuple(
            row
            for row in worktrees
            if (
                row[0] != current_path
                and row[1:] == (expected_main, "refs/heads/main", False)
            )
        )
        if len(detached_rows) != 1 or len(main_rows) != 1:
            raise RuntimeError(f"{lifecycle} detached-two-worktree drift")
    return HermeticLifecycleState(
        lifecycle=lifecycle,
        repository_path=str(repository),
        head=head,
        main_oid=main_oid,
        origin_main_oid=origin_main_oid,
        origin_head_symbolic_target=symbolic,
        origin_head_resolved_oid=resolved,
        branch=branch,
        worktree_count=count,
        status_entry_count=len(entries),
    )


def _commit_exact_paths(
    repository: Path,
    *,
    base_commit: str,
    formal_commit_subject: str,
    exact_paths: tuple[Path, ...],
) -> str:
    names = tuple(path.as_posix() for path in exact_paths)
    _git_text(repository, "add", "--", *names)
    staged = tuple(
        item.decode("utf-8", "strict")
        for item in _git_bytes(
            repository,
            "diff",
            "--cached",
            "--name-only",
            "-z",
        ).stdout.split(b"\0")
        if item
    )
    if len(staged) != len(names) or set(staged) != set(names):
        raise RuntimeError("candidate staged-file inventory drift")
    _git_text(
        repository,
        "-c",
        "user.name=CovaPIE Hermetic Harness",
        "-c",
        "user.email=covapie-hermetic@example.invalid",
        "commit",
        "--no-gpg-sign",
        "-m",
        formal_commit_subject,
        extra_env=_COMMIT_ENV,
    )
    candidate = _git_scalar(repository, "rev-parse", "HEAD")
    _assert_candidate_commit(
        repository,
        base_commit=base_commit,
        candidate_commit=candidate,
        formal_commit_subject=formal_commit_subject,
        exact_paths=exact_paths,
    )
    return candidate


def _assert_candidate_commit(
    repository: Path,
    *,
    base_commit: str,
    candidate_commit: str,
    formal_commit_subject: str,
    exact_paths: tuple[Path, ...],
) -> None:
    parent = _git_scalar(
        repository, "show", "-s", "--format=%P", candidate_commit
    )
    subject = _git_scalar(
        repository, "show", "-s", "--format=%s", candidate_commit
    )
    if parent != base_commit:
        raise RuntimeError("candidate parent is not explicit BASE")
    if subject != formal_commit_subject:
        raise RuntimeError("candidate subject drift")
    changed = tuple(
        item.decode("utf-8", "strict")
        for item in _git_bytes(
            repository,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            candidate_commit,
        ).stdout.split(b"\0")
        if item
    )
    expected = tuple(path.as_posix() for path in exact_paths)
    if len(changed) != len(expected) or set(changed) != set(expected):
        raise RuntimeError("candidate changed-file inventory drift")
    tree_rows = _git_text(
        repository, "ls-tree", "-r", candidate_commit, "--", *expected
    ).stdout.splitlines()
    observed_names = []
    for row in tree_rows:
        metadata, separator, name = row.partition("\t")
        if not separator or not metadata.startswith("100644 blob "):
            raise RuntimeError("candidate exact-path Git mode drift")
        observed_names.append(name)
    if (
        len(observed_names) != len(expected)
        or set(observed_names) != set(expected)
    ):
        raise RuntimeError("candidate exact-path tree inventory drift")


def _seed_bare_remote(
    source_repository: Path,
    bare_remote: Path,
    base_commit: str,
) -> None:
    _git_text(
        source_repository,
        "push",
        "--no-verify",
        str(bare_remote),
        f"{base_commit}:refs/heads/main",
    )
    _git_text(bare_remote, "symbolic-ref", "HEAD", "refs/heads/main")


def _clone_remote(remote: Path, destination: Path) -> None:
    _git_text(remote.parent, "clone", str(remote), str(destination))


def _remove_tree(path: Path) -> None:
    shutil.rmtree(path)


def _cleanup(
    temporary_root: Path,
    resource_paths: tuple[Path, ...],
    source_repository: Path,
    initial_source_snapshot: _SourceRepositorySnapshot,
) -> None:
    removal_error: BaseException | None = None
    if temporary_root.exists():
        try:
            _remove_tree(temporary_root)
        except BaseException as exc:
            removal_error = exc
    residue = tuple(path for path in resource_paths if path.exists())
    source_changed = (
        _source_snapshot(source_repository) != initial_source_snapshot
    )
    if removal_error is not None:
        raise RuntimeError(
            "temporary lifecycle cleanup removal failed; "
            f"residue_count={len(residue)}; source_changed={source_changed}"
        ) from removal_error
    if temporary_root.exists() or residue:
        raise RuntimeError(
            f"temporary lifecycle resource cleanup failed: {len(residue)} residues"
        )
    if source_changed:
        raise RuntimeError("source repository changed during hermetic lifecycle")


def exercise_hermetic_git_lifecycle_matrix(
    source_repository: Path,
    workspace_root: Path,
    *,
    base_commit: str,
    formal_commit_subject: str,
    exact_paths: tuple[Path, ...],
) -> HermeticLifecycleMatrixReport:
    """Build, verify, and clean a four-state lifecycle from an explicit BASE."""

    source, workspace, base, subject, paths = _validate_inputs(
        source_repository,
        workspace_root,
        base_commit,
        formal_commit_subject,
        exact_paths,
    )
    initial_snapshot = _source_snapshot(source)
    temporary_root = Path(
        tempfile.mkdtemp(prefix="covapie-hermetic-git-", dir=workspace)
    )
    bare_remote = temporary_root / "remote.git"
    pre_repository = temporary_root / "pre"
    detached_repository = temporary_root / "detached"
    formal_repository = temporary_root / "formal"
    resources = (
        bare_remote,
        pre_repository,
        detached_repository,
        formal_repository,
        temporary_root,
    )
    matrix_values: tuple[
        HermeticLifecycleState,
        HermeticLifecycleState,
        HermeticLifecycleState,
        HermeticLifecycleState,
        str,
    ] | None = None
    primary_error: BaseException | None = None
    try:
        _git_text(temporary_root, "init", "--bare", str(bare_remote))
        _seed_bare_remote(source, bare_remote, base)
        _assert_bare_remote(bare_remote, base)

        _clone_remote(bare_remote, pre_repository)
        _assert_clone_refs(
            pre_repository,
            expected_main=base,
            expected_origin_main=base,
            remote=bare_remote,
        )
        _copy_exact_paths(source, pre_repository, paths)
        expected_untracked = tuple(
            f"?? {path.as_posix()}".encode("utf-8") for path in paths
        )
        pre_state = _capture_state(
            pre_repository,
            lifecycle="pre_commit",
            expected_main=base,
            expected_origin_main=base,
            expected_worktree_count=1,
            expected_status_entries=expected_untracked,
            remote=bare_remote,
        )
        if _git_bytes(
            pre_repository,
            "ls-files",
            "--stage",
            "-z",
            "--",
            *(path.as_posix() for path in paths),
        ).stdout:
            raise RuntimeError("pre-commit exact paths are staged")

        _git_text(
            pre_repository,
            "worktree",
            "add",
            "--detach",
            str(detached_repository),
            base,
        )
        _copy_exact_paths(source, detached_repository, paths)
        detached_candidate = _commit_exact_paths(
            detached_repository,
            base_commit=base,
            formal_commit_subject=subject,
            exact_paths=paths,
        )
        _assert_candidate_commit(
            detached_repository,
            base_commit=base,
            candidate_commit=detached_candidate,
            formal_commit_subject=subject,
            exact_paths=paths,
        )
        detached_state = _capture_state(
            detached_repository,
            lifecycle="detached_candidate_post_commit",
            expected_main=base,
            expected_origin_main=base,
            expected_worktree_count=2,
            expected_status_entries=(),
            remote=bare_remote,
        )

        _clone_remote(bare_remote, formal_repository)
        _copy_exact_paths(source, formal_repository, paths)
        formal_candidate = _commit_exact_paths(
            formal_repository,
            base_commit=base,
            formal_commit_subject=subject,
            exact_paths=paths,
        )
        _assert_candidate_commit(
            formal_repository,
            base_commit=base,
            candidate_commit=formal_candidate,
            formal_commit_subject=subject,
            exact_paths=paths,
        )
        if formal_candidate != detached_candidate:
            raise RuntimeError("independent candidate commit OIDs differ")
        formal_unpushed_state = _capture_state(
            formal_repository,
            lifecycle="formal_main_post_commit_unpushed",
            expected_main=formal_candidate,
            expected_origin_main=base,
            expected_worktree_count=1,
            expected_status_entries=(),
            remote=bare_remote,
        )
        divergence = _git_scalar(
            formal_repository,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...refs/remotes/origin/main",
        )
        if divergence != "1\t0":
            raise RuntimeError("formal unpushed ahead/behind drift")

        _git_text(
            formal_repository,
            "push",
            "--no-verify",
            "origin",
            "refs/heads/main:refs/heads/main",
        )
        _assert_bare_remote(bare_remote, formal_candidate)
        formal_pushed_state = _capture_state(
            formal_repository,
            lifecycle="formal_main_post_push",
            expected_main=formal_candidate,
            expected_origin_main=formal_candidate,
            expected_worktree_count=1,
            expected_status_entries=(),
            remote=bare_remote,
        )
        divergence = _git_scalar(
            formal_repository,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...refs/remotes/origin/main",
        )
        if divergence != "0\t0":
            raise RuntimeError("formal pushed ahead/behind drift")
        matrix_values = (
            pre_state,
            detached_state,
            formal_unpushed_state,
            formal_pushed_state,
            formal_candidate,
        )
    except BaseException as exc:
        primary_error = exc

    try:
        _cleanup(temporary_root, resources, source, initial_snapshot)
    except BaseException as cleanup_error:
        if primary_error is not None:
            raise RuntimeError(
                "hermetic lifecycle failed and cleanup verification also failed"
            ) from cleanup_error
        raise
    if primary_error is not None:
        raise primary_error
    if matrix_values is None:
        raise RuntimeError("hermetic lifecycle matrix did not complete")
    pre, detached, unpushed, pushed, candidate = matrix_values
    return HermeticLifecycleMatrixReport(
        base_commit=base,
        pre_commit=pre,
        detached_candidate_post_commit=detached,
        formal_main_post_commit_unpushed=unpushed,
        formal_main_post_push=pushed,
        candidate_commit=candidate,
        candidate_parent=base,
        candidate_subject=subject,
        exact_path_count=len(paths),
        cleanup_verified=True,
    )
