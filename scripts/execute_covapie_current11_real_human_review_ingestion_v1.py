#!/usr/bin/env python3
"""Execute one external Current11 submission into one external JSON bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from covalent_ext.covapie_current11_real_human_review_ingestion_execution_bundle_v1 import (
    build_covapie_current11_real_human_review_ingestion_execution_bundle_v1,
)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_paths(
    repo_root: Path,
    submission_file: Path,
    output_file: Path,
) -> tuple[Path, Path, Path]:
    root = repo_root.expanduser().resolve()
    source = Path(os.path.abspath(os.fspath(submission_file.expanduser())))
    destination = Path(os.path.abspath(os.fspath(output_file.expanduser())))
    if not root.is_dir() or not (root / ".git").exists():
        raise ValueError(f"repo root is not a Git repository directory: {root}")
    if source.is_symlink() or not source.is_file():
        raise ValueError(
            f"submission file must be an existing regular file: {source}"
        )
    if os.path.lexists(destination):
        if destination.is_symlink():
            raise FileExistsError(
                f"output file must not be a symlink: {destination}"
            )
        raise FileExistsError(
            f"output file already exists; refusing to overwrite: {destination}"
        )
    parent = destination.parent
    if parent.is_symlink() or not parent.exists() or not parent.is_dir():
        raise ValueError(
            "output-file parent must already exist as a regular directory"
        )
    resolved_destination = parent.resolve(strict=True) / destination.name
    if _is_within(destination, root) or _is_within(resolved_destination, root):
        raise ValueError("output file must be outside the Git repository")
    return root, source, destination


def _validate_published_destination(
    *,
    destination: Path,
    temporary_path: Path,
    temporary_identity: tuple[int, int],
    expected_size: int,
) -> None:
    destination_stat = os.stat(destination, follow_symlinks=False)
    temporary_stat = os.stat(temporary_path, follow_symlinks=False)
    destination_identity = (destination_stat.st_dev, destination_stat.st_ino)
    temporary_path_identity = (
        temporary_stat.st_dev,
        temporary_stat.st_ino,
    )
    if (
        destination_identity != temporary_identity
        or temporary_path_identity != temporary_identity
        or not stat.S_ISREG(destination_stat.st_mode)
        or stat.S_IMODE(destination_stat.st_mode) != 0o644
        or destination_stat.st_size != expected_size
    ):
        raise OSError("published output validation failed")


def _atomic_create_external_file(destination: Path, payload: bytes) -> None:
    if os.path.lexists(destination):
        raise FileExistsError(
            f"output file already exists; refusing to overwrite: {destination}"
        )
    descriptor = -1
    temporary_path: Path | None = None
    temporary_identity: tuple[int, int] | None = None
    try:
        descriptor, raw_temporary = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        temporary_path = Path(raw_temporary)
        temporary_stat = os.fstat(descriptor)
        temporary_identity = (temporary_stat.st_dev, temporary_stat.st_ino)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), 0o644)
        os.link(temporary_path, destination, follow_symlinks=False)
        _validate_published_destination(
            destination=destination,
            temporary_path=temporary_path,
            temporary_identity=temporary_identity,
            expected_size=len(payload),
        )
        temporary_path.unlink()
        temporary_path = None
    except BaseException:
        cleanup_errors: list[OSError] = []
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError as error:
                cleanup_errors.append(error)
            descriptor = -1
        if temporary_identity is not None:
            try:
                destination_stat = os.stat(
                    destination,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            except OSError as error:
                cleanup_errors.append(error)
            else:
                if (
                    destination_stat.st_dev,
                    destination_stat.st_ino,
                ) == temporary_identity:
                    try:
                        destination.unlink()
                    except FileNotFoundError:
                        pass
                    except OSError as error:
                        cleanup_errors.append(error)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                cleanup_errors.append(error)
        if cleanup_errors:
            raise OSError("atomic output cleanup failed") from cleanup_errors[0]
        raise


def execute_submission_to_file(
    *,
    repo_root: Path,
    submission_file: Path,
    output_file: Path,
) -> dict[str, object]:
    root, source, destination = _validate_paths(
        repo_root,
        submission_file,
        output_file,
    )
    source_stat_before = source.stat()
    source_payload = source.read_bytes()
    source_sha = hashlib.sha256(source_payload).hexdigest()
    execution_payload = (
        build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
            source_submission_bundle=source_payload,
            repo_root=root,
        )
    )
    source_stat_after = source.stat()
    if (
        (source_stat_after.st_dev, source_stat_after.st_ino)
        != (source_stat_before.st_dev, source_stat_before.st_ino)
        or source_stat_after.st_size != source_stat_before.st_size
        or hashlib.sha256(source.read_bytes()).hexdigest() != source_sha
    ):
        raise ValueError("submission file changed during execution")
    bundle = json.loads(execution_payload)
    results = bundle["ingestion_result_records"]
    authorities = bundle["new_authority_records"]
    active_count = sum(
        record["authority_status"] == "active" for record in authorities
    )
    quarantined_count = sum(
        record["authority_status"] == "quarantined" for record in authorities
    )
    _atomic_create_external_file(destination, execution_payload)
    return {
        "output_path": str(destination),
        "source_submission_bundle_sha256":
            bundle["source_submission_bundle_sha256"],
        "ingestion_execution_bundle_sha256":
            bundle["ingestion_execution_bundle_sha256"],
        "submission_batch_id": bundle["submission_batch_id"],
        "result_count": len(results),
        "authority_count": len(authorities),
        "active_authority_count": active_count,
        "quarantined_authority_count": quarantined_count,
        "batch_passed": bundle["batch_passed"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute a strict Current11 human-review submission into one "
            "durable external ingestion execution JSON bundle."
        )
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--submission-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = execute_submission_to_file(
            repo_root=args.repo_root,
            submission_file=args.submission_file,
            output_file=args.output_file,
        )
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"output_path={result['output_path']}")
    print(
        "source_submission_bundle_sha256="
        f"{result['source_submission_bundle_sha256']}"
    )
    print(
        "ingestion_execution_bundle_sha256="
        f"{result['ingestion_execution_bundle_sha256']}"
    )
    print(f"submission_batch_id={result['submission_batch_id']}")
    print(f"result_count={result['result_count']}")
    print(f"authority_count={result['authority_count']}")
    print(f"active_authority_count={result['active_authority_count']}")
    print(
        f"quarantined_authority_count="
        f"{result['quarantined_authority_count']}"
    )
    print(f"batch_passed={str(result['batch_passed']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
