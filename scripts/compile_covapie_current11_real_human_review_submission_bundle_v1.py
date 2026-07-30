#!/usr/bin/env python3
"""Compile one external Current11 review workspace to an external JSON file."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Sequence

from covalent_ext.covapie_current11_real_human_review_submission_bundle_compiler_v1 import (
    compile_covapie_current11_real_human_review_submission_bundle_v1,
)


PACKAGE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_v1"
)
PACKAGE_INDEX_FILE = (
    "covapie_current11_warhead_boundary_review_package_index.csv"
)
PACKAGE_OPTIONS_FILE = (
    "covapie_current11_warhead_boundary_candidate_review_options.csv"
)
REVIEW_TEMPLATES_FILE = (
    "covapie_current11_warhead_boundary_review_record_templates.csv"
)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_input_file(path: Path, *, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be an existing regular file: {path}")
    return path.read_bytes()


def _validate_paths(
    repo_root: Path,
    workspace_dir: Path,
    output_file: Path,
) -> tuple[Path, Path, Path]:
    root = repo_root.expanduser().resolve()
    workspace = workspace_dir.expanduser().resolve()
    destination = Path(
        os.path.abspath(os.fspath(output_file.expanduser()))
    )
    if not root.is_dir() or not (root / ".git").exists():
        raise ValueError(f"repo root is not a Git repository directory: {root}")
    if not workspace.is_dir():
        raise ValueError(f"workspace directory does not exist: {workspace}")
    if os.path.lexists(destination):
        if destination.is_symlink():
            raise FileExistsError(f"output file must not be a symlink: {destination}")
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
    return root, workspace, destination


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
            except OSError as exc:
                cleanup_errors.append(exc)
            descriptor = -1
        if temporary_identity is not None:
            try:
                destination_stat = os.stat(
                    destination,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(exc)
            else:
                if (
                    destination_stat.st_dev,
                    destination_stat.st_ino,
                ) == temporary_identity:
                    try:
                        destination.unlink()
                    except FileNotFoundError:
                        pass
                    except OSError as exc:
                        cleanup_errors.append(exc)
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(exc)
        if cleanup_errors:
            raise OSError("atomic output cleanup failed") from cleanup_errors[0]
        raise


def _validate_published_destination(
    *,
    destination: Path,
    temporary_path: Path,
    temporary_identity: tuple[int, int],
    expected_size: int,
) -> None:
    destination_stat = os.stat(destination, follow_symlinks=False)
    temporary_stat = os.stat(temporary_path, follow_symlinks=False)
    destination_identity = (
        destination_stat.st_dev,
        destination_stat.st_ino,
    )
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


def compile_workspace_to_file(
    *,
    repo_root: Path,
    workspace_dir: Path,
    output_file: Path,
    submission_batch_id: str,
) -> dict[str, object]:
    root, workspace, destination = _validate_paths(
        repo_root,
        workspace_dir,
        output_file,
    )
    worklist = _require_input_file(
        workspace / "review_worklist.csv",
        label="review worklist",
    )
    eligible = _require_input_file(
        workspace / "eligible_candidate_options.csv",
        label="eligible candidate options",
    )
    package_root = root / PACKAGE_ROOT
    package_index = _require_input_file(
        package_root / PACKAGE_INDEX_FILE,
        label="committed package index",
    )
    package_options = _require_input_file(
        package_root / PACKAGE_OPTIONS_FILE,
        label="committed full candidate options",
    )
    review_templates = _require_input_file(
        package_root / REVIEW_TEMPLATES_FILE,
        label="committed review templates",
    )
    compiled = compile_covapie_current11_real_human_review_submission_bundle_v1(
        review_worklist_csv=worklist,
        eligible_candidate_options_csv=eligible,
        package_index_csv=package_index,
        package_candidate_options_csv=package_options,
        review_record_templates_csv=review_templates,
        submission_batch_id=submission_batch_id,
    )
    bundle = json.loads(compiled)
    decisions = Counter(
        item["review_record_payload"]["review_decision"]
        for item in bundle["submission_items"]
    )
    _atomic_create_external_file(destination, compiled)
    return {
        "output_path": str(destination),
        "source_worklist_sha256": hashlib.sha256(worklist).hexdigest(),
        "bundle_sha256": hashlib.sha256(compiled).hexdigest(),
        "item_count": len(bundle["submission_items"]),
        "decision_counts": decisions,
        "adapter_passed": True,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a completed Current11 human-review workspace into one "
            "strict external submission JSON file."
        )
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--submission-batch-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = compile_workspace_to_file(
            repo_root=args.repo_root,
            workspace_dir=args.workspace_dir,
            output_file=args.output_file,
            submission_batch_id=args.submission_batch_id,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    decisions = result["decision_counts"]
    print(f"output_path={result['output_path']}")
    print(f"source_worklist_sha256={result['source_worklist_sha256']}")
    print(f"bundle_sha256={result['bundle_sha256']}")
    print(f"item_count={result['item_count']}")
    print(
        "decision_counts="
        f"select_admitted_candidate:"
        f"{decisions.get('select_admitted_candidate', 0)},"
        f"revise_atom_set_and_boundary:"
        f"{decisions.get('revise_atom_set_and_boundary', 0)},"
        f"quarantine:{decisions.get('quarantine', 0)}"
    )
    print("adapter_passed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
