#!/usr/bin/env python3
"""Atomically materialize or check the Current11 family/rule review workspace."""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1 import (  # noqa: E402
    ERROR,
    HUMAN_FIELDS,
    OBJECT_DIRECTORY_PREFIX,
    PUBLICATION_SCHEME,
    SAMPLE_SUPPORT_FIELDS,
    WORKLIST_FIELDS,
    WORKSPACE_FILES,
    WORKSPACE_NAME,
    _build_for_validation,
    _sha256,
    _strict_csv,
    _strict_json,
    build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1,
)


def _identity(path: Path) -> tuple[int, int]:
    metadata = path.lstat()
    return metadata.st_dev, metadata.st_ino


def _validate_output_path(state_root: Path, output_dir: Path) -> tuple[Path, Path]:
    try:
        state = state_root.resolve(strict=True)
        state_meta = state.lstat()
        parent = state / "manual-review"
        parent_meta = parent.lstat()
    except OSError as error:
        raise ValueError(ERROR) from error
    if (not stat.S_ISDIR(state_meta.st_mode) or not stat.S_ISDIR(parent_meta.st_mode)
            or state_root.is_symlink() or parent.is_symlink()):
        raise ValueError(ERROR)
    output = output_dir.absolute()
    try:
        resolved_parent = output.parent.resolve(strict=True)
    except OSError as error:
        raise ValueError(ERROR) from error
    if resolved_parent != parent or output.name != WORKSPACE_NAME:
        raise ValueError(ERROR)
    return parent, output


def _write_payload(path: Path, payload: bytes) -> tuple[int, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    opened = os.fstat(descriptor)
    created_identity = (opened.st_dev, opened.st_ino)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError(errno.EIO, "short write")
            view = view[written:]
        os.close(descriptor)
        descriptor = -1
        os.chmod(path, 0o644, follow_symlinks=False)
        metadata = path.lstat()
        if (not stat.S_ISREG(metadata.st_mode)
                or (metadata.st_dev, metadata.st_ino) != created_identity
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or metadata.st_size != len(payload)
                or path.read_bytes() != payload):
            raise ValueError(ERROR)
        return created_identity
    except BaseException:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            pass
        except OSError as error:
            raise ValueError(ERROR) from error
        else:
            if (not stat.S_ISREG(metadata.st_mode)
                    or (metadata.st_dev, metadata.st_ino) != created_identity):
                raise ValueError(ERROR)
            try:
                path.unlink()
            except OSError as error:
                raise ValueError(ERROR) from error
        raise


def _safe_cleanup_created_directory(
    temporary: Path,
    directory_identity: tuple[int, int],
    created_files: Mapping[str, tuple[int, int]],
) -> None:
    """Remove only the exact inodes created by this invocation."""

    try:
        metadata = temporary.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ValueError(ERROR) from error
    if ((metadata.st_dev, metadata.st_ino) != directory_identity
            or not stat.S_ISDIR(metadata.st_mode)):
        raise ValueError(ERROR)
    try:
        entries = tuple(sorted(temporary.iterdir(), key=lambda item: item.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if tuple(item.name for item in entries) != tuple(sorted(created_files)):
        raise ValueError(ERROR)
    for entry in entries:
        try:
            child = entry.lstat()
        except OSError as error:
            raise ValueError(ERROR) from error
        if (not stat.S_ISREG(child.st_mode)
                or (child.st_dev, child.st_ino) != created_files[entry.name]):
            raise ValueError(ERROR)
    for entry in entries:
        try:
            entry.unlink()
        except OSError as error:
            raise ValueError(ERROR) from error
    try:
        temporary.rmdir()
    except OSError as error:
        raise ValueError(ERROR) from error


def _validate_workspace_object_tree_v1(
    object_directory: Path,
    expected: Mapping[str, bytes] | None,
    *,
    expected_object_identity: tuple[int, int] | None = None,
) -> dict[str, object]:
    try:
        directory = object_directory.lstat()
        entries = tuple(sorted(object_directory.iterdir(), key=lambda item: item.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if (not stat.S_ISDIR(directory.st_mode) or object_directory.is_symlink()
            or (expected_object_identity is not None
                and (directory.st_dev, directory.st_ino) != expected_object_identity)
            or stat.S_IMODE(directory.st_mode) != 0o755
            or tuple(item.name for item in entries) != tuple(sorted(WORKSPACE_FILES))):
        raise ValueError(ERROR)
    file_records: list[dict[str, object]] = []
    payloads: dict[str, bytes] = {}
    for path in entries:
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(ERROR) from error
        if (not stat.S_ISREG(metadata.st_mode) or path.is_symlink()
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or metadata.st_size != len(payload)
                or (expected is not None and payload != expected[path.name])):
            raise ValueError(ERROR)
        payloads[path.name] = payload
        file_records.append({
            "name": path.name,
            "bytes": len(payload),
            "lines": payload.count(b"\n"),
            "sha256": _sha256(payload),
            "mode": "0644",
        })
    worklist = _strict_csv(payloads["family_rule_approval_worklist.csv"], WORKLIST_FIELDS)
    samples = _strict_csv(payloads["sample_support_evidence.csv"], SAMPLE_SUPPORT_FIELDS)
    evidence = _strict_json(payloads["family_rule_candidate_evidence.json"], list)
    manifest = _strict_json(payloads["review_package_manifest.json"], dict)
    if (len(worklist) != 7 or len(samples) != 11 or len(evidence) != 7
            or any(row[field] != "" for row in worklist for field in HUMAN_FIELDS)
            or manifest["pending_review_unit_count"] != 7
            or manifest["completed_review_unit_count"] != 0
            or manifest["family_approved_count"] != 0
            or manifest["rule_approved_count"] != 0):
        raise ValueError(ERROR)
    return {
        "workspace_name": WORKSPACE_NAME,
        "object_directory_name": object_directory.name,
        "object_directory_mode": "0755",
        "file_count": 5,
        "subdirectory_count": 0,
        "workspace_internal_symlink_count": 0,
        "review_unit_count": 7,
        "sample_support_count": 11,
        "human_fields_blank": True,
        "files": file_records,
    }


def _validate_relative_object_name_v1(relative_target: object) -> str:
    if (type(relative_target) is not str or not relative_target
            or Path(relative_target).is_absolute() or "/" in relative_target
            or relative_target in {".", ".."} or ".." in relative_target
            or not relative_target.startswith(OBJECT_DIRECTORY_PREFIX)
            or not relative_target.removeprefix(OBJECT_DIRECTORY_PREFIX)
            or re.fullmatch(
                rf"{re.escape(OBJECT_DIRECTORY_PREFIX)}[A-Za-z0-9_-]+",
                relative_target,
            ) is None):
        raise ValueError(ERROR)
    return relative_target


def _validate_canonical_workspace_entry_v1(
    canonical_entry: Path,
    expected: Mapping[str, bytes] | None,
    *,
    expected_canonical_identity: tuple[int, int] | None = None,
    expected_object_identity: tuple[int, int] | None = None,
) -> dict[str, object]:
    try:
        canonical_metadata = canonical_entry.lstat()
        relative_target = os.readlink(canonical_entry)
    except OSError as error:
        raise ValueError(ERROR) from error
    if (not stat.S_ISLNK(canonical_metadata.st_mode)
            or (expected_canonical_identity is not None
                and (canonical_metadata.st_dev, canonical_metadata.st_ino)
                != expected_canonical_identity)):
        raise ValueError(ERROR)
    relative_target = _validate_relative_object_name_v1(relative_target)
    object_directory = canonical_entry.parent / relative_target
    report = _validate_workspace_object_tree_v1(
        object_directory,
        expected,
        expected_object_identity=expected_object_identity,
    )
    if os.readlink(canonical_entry) != relative_target:
        raise ValueError(ERROR)
    return {
        "publication_scheme": PUBLICATION_SCHEME,
        "canonical_entry_type": "symlink",
        "canonical_symlink_target": relative_target,
        **report,
    }


def _materialize_review_workspace(
    *, repo_root: Path, state_root: Path, output_dir: Path,
    payloads: Mapping[str, bytes] | None = None,
) -> dict[str, object]:
    parent, output = _validate_output_path(state_root, output_dir)
    if os.path.lexists(output):
        raise FileExistsError(ERROR)
    built = (
        dict(payloads) if payloads is not None
        else build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1(
            repo_root=repo_root,
        )
    )
    if tuple(built) != WORKSPACE_FILES:
        raise ValueError(ERROR)
    object_directory = Path(tempfile.mkdtemp(
        prefix=OBJECT_DIRECTORY_PREFIX,
        dir=parent,
    ))
    directory_identity = _identity(object_directory)
    created: dict[str, tuple[int, int]] = {}
    canonical_created = False
    try:
        os.chmod(object_directory, 0o755, follow_symlinks=False)
        for name in WORKSPACE_FILES:
            created[name] = _write_payload(object_directory / name, built[name])
        _validate_workspace_object_tree_v1(
            object_directory,
            built,
            expected_object_identity=directory_identity,
        )
        os.symlink(object_directory.name, output, target_is_directory=True)
        canonical_created = True
        canonical_identity = _identity(output)
        return _validate_canonical_workspace_entry_v1(
            output,
            built,
            expected_canonical_identity=canonical_identity,
            expected_object_identity=directory_identity,
        )
    except BaseException:
        if not canonical_created:
            _safe_cleanup_created_directory(
                object_directory, directory_identity, created,
            )
        raise


def _check_review_workspace(
    *, repo_root: Path, state_root: Path, output_dir: Path,
) -> dict[str, object]:
    _parent, output = _validate_output_path(state_root, output_dir)
    expected = build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1(
        repo_root=repo_root,
    )
    report = _validate_canonical_workspace_entry_v1(output, expected)
    _payloads, _state, response = _build_for_validation(repo_root, validate_candidate=True)
    report["lifecycle_profile"] = response["review_package_lifecycle_profile"]
    report["response_sha256"] = response["response_sha256"]
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Atomically materialize or read-only check the CovaPIE Current11 "
            "family/rule approval review workspace v1."
        )
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    state_root = args.state_root.resolve()
    output_dir = args.output_dir or state_root / "manual-review" / WORKSPACE_NAME
    try:
        if args.check:
            report = _check_review_workspace(
                repo_root=repo_root, state_root=state_root, output_dir=output_dir,
            )
        else:
            report = _materialize_review_workspace(
                repo_root=repo_root, state_root=state_root, output_dir=output_dir,
            )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
