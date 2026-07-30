#!/usr/bin/env python3
"""Materialize the Current11 Exact5 multi-boundary review sidecar externally."""

from __future__ import annotations

import argparse
import csv
import io
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Sequence

from covalent_ext.covapie_current11_multi_boundary_human_review_sidecar_v1 import (
    build_covapie_current11_multi_boundary_human_review_sidecar_v1,
)


_OUTPUT_NAMES = (
    "verified_multi_boundary_evidence.csv",
    "multi_boundary_review_worklist.csv",
    "README.md",
)
_FileIdentity = tuple[int, int]


def _regular_file_bytes(path: Path, label: str) -> bytes:
    try:
        info = path.lstat()
    except OSError as error:
        raise ValueError(f"{label} must be an existing regular file") from error
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise ValueError(f"{label} must be an existing regular file")
    return path.read_bytes()


def _outside_repository_output(
    repo_root: Path,
    output_dir: Path,
) -> tuple[Path, Path]:
    try:
        resolved_repo = repo_root.resolve(strict=True)
        parent = output_dir.parent.resolve(strict=True)
    except OSError as error:
        raise ValueError(
            "repo root and output-dir parent must already exist"
        ) from error
    if not resolved_repo.is_dir() or not parent.is_dir():
        raise ValueError(
            "repo root and output-dir parent must be directories"
        )
    resolved_output = parent / output_dir.name
    if resolved_output == resolved_repo or resolved_repo in resolved_output.parents:
        raise ValueError("output-dir must be outside the Git repository")
    if os.path.lexists(resolved_output):
        raise FileExistsError("refusing to overwrite existing output-dir")
    return resolved_repo, resolved_output


def _regular_file_identity(path: Path) -> _FileIdentity:
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise OSError(f"owned path is not a regular file: {path.name}")
    return info.st_dev, info.st_ino


def _write_exact_file(path: Path, payload: bytes) -> _FileIdentity:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(0o644)
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise
    return _regular_file_identity(path)


def _unlink_if_owned(
    path: Path,
    expected_identity: _FileIdentity,
) -> OSError | None:
    try:
        observed_identity = _regular_file_identity(path)
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    if observed_identity != expected_identity:
        return OSError(f"owned path inode changed: {path.name}")
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    except OSError as error:
        return error
    return None


def _cleanup_exact_directory(
    directory: Path,
    owned_files: Mapping[str, _FileIdentity],
) -> None:
    errors: list[OSError] = []
    for name in _OUTPUT_NAMES:
        identity = owned_files.get(name)
        if identity is None:
            continue
        error = _unlink_if_owned(directory / name, identity)
        if error is not None:
            errors.append(error)
    try:
        remaining = tuple(path.name for path in directory.iterdir())
    except FileNotFoundError:
        remaining = ()
    except OSError as error:
        errors.append(error)
        remaining = ()
    if remaining:
        errors.append(OSError(
            "owned directory contains unowned entries: "
            + ",".join(sorted(remaining))
        ))
    else:
        try:
            directory.rmdir()
        except FileNotFoundError:
            pass
        except OSError as error:
            errors.append(error)
    if errors:
        raise OSError("; ".join(str(error) for error in errors))


def _cleanup_temporary_directory(
    temporary_dir: Path,
    temporary_files: Mapping[str, _FileIdentity],
) -> None:
    try:
        _cleanup_exact_directory(temporary_dir, temporary_files)
    except OSError as error:
        raise OSError(
            f"sidecar temporary sibling cleanup failed: {error}"
        ) from error


def _cleanup_publication_after_failure(
    output_dir: Path,
    published_files: Mapping[str, _FileIdentity],
    original_error: BaseException,
) -> None:
    try:
        _cleanup_exact_directory(output_dir, published_files)
    except OSError as cleanup_error:
        raise OSError(
            "sidecar workspace publication cleanup failed: "
            f"{cleanup_error}"
        ) from original_error


def _publish_no_clobber_directory(
    temporary_dir: Path,
    output_dir: Path,
) -> dict[str, _FileIdentity]:
    output_created = False
    published_files: dict[str, _FileIdentity] = {}
    try:
        os.mkdir(output_dir, 0o755)
        output_created = True
        for name in _OUTPUT_NAMES:
            source = temporary_dir / name
            source_identity = _regular_file_identity(source)
            os.link(source, output_dir / name)
            target_identity = _regular_file_identity(output_dir / name)
            if target_identity != source_identity:
                raise OSError(f"published hard-link identity mismatch: {name}")
            published_files[name] = source_identity
        observed = tuple(sorted(path.name for path in output_dir.iterdir()))
        if observed != tuple(sorted(_OUTPUT_NAMES)):
            raise ValueError("published workspace file inventory invalid")
        for name in _OUTPUT_NAMES:
            (output_dir / name).chmod(0o644)
    except BaseException as publication_error:
        if output_created:
            _cleanup_publication_after_failure(
                output_dir,
                published_files,
                publication_error,
            )
        raise
    return published_files


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as stream:
        return list(csv.DictReader(stream))


def prepare_sidecar_workspace(
    *,
    repo_root: Path,
    submission_file: Path,
    execution_file: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Build in a temporary sibling and publish an external Exact3 directory."""

    if any(
        type(value) is not type(Path())
        for value in (
            repo_root,
            submission_file,
            execution_file,
            output_dir,
        )
    ):
        raise ValueError("all path arguments must be exact Paths")
    resolved_repo, resolved_output = _outside_repository_output(
        repo_root, output_dir,
    )
    submission = _regular_file_bytes(submission_file, "submission-file")
    execution = _regular_file_bytes(execution_file, "execution-file")
    submission_snapshot = bytes(submission)
    execution_snapshot = bytes(execution)
    payloads = build_covapie_current11_multi_boundary_human_review_sidecar_v1(
        source_submission_bundle=submission,
        source_ingestion_execution_bundle=execution,
        repo_root=resolved_repo,
    )
    if tuple(payloads) != _OUTPUT_NAMES:
        raise ValueError("builder output file inventory invalid")
    temporary = Path(tempfile.mkdtemp(
        prefix=f".{resolved_output.name}.tmp-",
        dir=resolved_output.parent,
    ))
    temporary_files: dict[str, _FileIdentity] = {}
    published_files: dict[str, _FileIdentity] = {}
    operation_error: BaseException | None = None
    try:
        for name in _OUTPUT_NAMES:
            temporary_files[name] = _write_exact_file(
                temporary / name, payloads[name],
            )
        if tuple(sorted(path.name for path in temporary.iterdir())) != tuple(
            sorted(_OUTPUT_NAMES)
        ):
            raise ValueError("temporary workspace file inventory invalid")
        published_files = _publish_no_clobber_directory(
            temporary, resolved_output,
        )
    except BaseException as error:
        operation_error = error
        raise
    finally:
        try:
            _cleanup_temporary_directory(temporary, temporary_files)
        except OSError as cleanup_error:
            if operation_error is not None:
                raise OSError(str(cleanup_error)) from operation_error
            if published_files:
                _cleanup_publication_after_failure(
                    resolved_output,
                    published_files,
                    cleanup_error,
                )
            raise
    try:
        if (
            submission != submission_snapshot
            or execution != execution_snapshot
            or _regular_file_bytes(submission_file, "submission-file")
            != submission_snapshot
            or _regular_file_bytes(execution_file, "execution-file")
            != execution_snapshot
            or tuple(sorted(path.name for path in resolved_output.iterdir()))
            != tuple(sorted(_OUTPUT_NAMES))
            or any(
                stat.S_IMODE((resolved_output / name).stat().st_mode) != 0o644
                for name in _OUTPUT_NAMES
            )
        ):
            raise ValueError("published workspace invariant invalid")
    except BaseException as validation_error:
        _cleanup_publication_after_failure(
            resolved_output,
            published_files,
            validation_error,
        )
        raise
    evidence = _csv_rows(payloads["verified_multi_boundary_evidence.csv"])
    worklist = _csv_rows(payloads["multi_boundary_review_worklist.csv"])
    return {
        "output_dir": str(resolved_output),
        "source_submission_bundle_sha256":
            evidence[0]["source_submission_bundle_sha256"],
        "source_execution_bundle_filesystem_sha256":
            evidence[0][
                "source_ingestion_execution_bundle_filesystem_sha256"
            ],
        "evidence_count": len(evidence),
        "worklist_count": len(worklist),
        "exact_two_boundary_verified_count": sum(
            row["exact_two_boundaries_verified"] == "true"
            for row in evidence
        ),
        "pending_human_review_count": sum(
            row["review_decision"] == "not_reviewed"
            and row["review_completed"] == "false"
            for row in worklist
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the CovaPIE Current11 Exact5 multi-boundary human-review "
            "sidecar outside the Git repository."
        )
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--submission-file", required=True, type=Path)
    parser.add_argument("--execution-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    try:
        options = _parser().parse_args(arguments)
        summary = prepare_sidecar_workspace(
            repo_root=options.repo_root,
            submission_file=options.submission_file,
            execution_file=options.execution_file,
            output_dir=options.output_dir,
        )
    except (OSError, TypeError, ValueError) as error:
        print(f"error={type(error).__name__}:{error}", file=sys.stderr)
        return 1
    for field in (
        "output_dir",
        "source_submission_bundle_sha256",
        "source_execution_bundle_filesystem_sha256",
        "evidence_count",
        "worklist_count",
        "exact_two_boundary_verified_count",
        "pending_human_review_count",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
