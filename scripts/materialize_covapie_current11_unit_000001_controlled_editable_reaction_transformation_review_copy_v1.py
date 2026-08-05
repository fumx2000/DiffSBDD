#!/usr/bin/env python3
"""Materialize or read-only check the controlled editable review copy."""

from __future__ import annotations

import argparse
import errno
import json
import os
import stat
import sys
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1 import (  # noqa: E402
    ERROR,
    IMMUTABLE_REFERENCE_FILES,
    MANIFEST_FILE,
    PUBLICATION_SCHEME,
    REVIEW_FILES,
    WORKLIST_FILE,
    WORKSPACE_NAME,
    _build_payloads,
    _collect_lifecycle,
    _derive_lifecycle,
    _sha256,
    _strict_csv,
    _validate_initial_payloads,
    _validate_source_materializer_commit,
    _validate_source_template_tree,
    build_covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_reaction_transformation_evidence_overlay_contract_v1
    as overlay,
)


def _identity(path: Path) -> tuple[int, int]:
    metadata = path.lstat()
    return metadata.st_dev, metadata.st_ino


def _validate_output_path(
    state_root: Path, output_dir: Path,
) -> tuple[Path, Path, Path]:
    """Validate the exact state-owned editable-workspace path."""

    try:
        state = state_root.resolve(strict=True)
        state_metadata = state_root.lstat()
        formal_parent = state / "manual-review"
        resolved_formal_parent = formal_parent.resolve(strict=True)
        parent_metadata = formal_parent.lstat()
        output = output_dir.absolute()
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not state_root.is_absolute()
        or state != state_root
        or state_root.is_symlink()
        or not stat.S_ISDIR(state_metadata.st_mode)
        or resolved_formal_parent != formal_parent
        or formal_parent.is_symlink()
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or not output_dir.is_absolute()
        or output.parent != formal_parent
        or output.name != WORKSPACE_NAME
    ):
        raise ValueError(ERROR)
    return state, formal_parent, output


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
        os.fchmod(descriptor, 0o644)
        os.close(descriptor)
        descriptor = -1
        metadata = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino) != created_identity
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or metadata.st_size != len(payload)
            or path.read_bytes() != payload
        ):
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
            if (
                not stat.S_ISREG(metadata.st_mode)
                or (metadata.st_dev, metadata.st_ino) != created_identity
            ):
                raise ValueError(ERROR)
            try:
                path.unlink()
            except OSError as error:
                raise ValueError(ERROR) from error
        raise


def _safe_cleanup_created_directory(
    workspace: Path,
    directory_identity: tuple[int, int],
    created_files: Mapping[str, tuple[int, int]],
) -> None:
    """Remove only exact file and directory inodes created by this call."""

    try:
        metadata = workspace.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or workspace.is_symlink()
        or (metadata.st_dev, metadata.st_ino) != directory_identity
    ):
        raise ValueError(ERROR)
    try:
        entries = tuple(sorted(workspace.iterdir(), key=lambda item: item.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if tuple(item.name for item in entries) != tuple(sorted(created_files)):
        raise ValueError(ERROR)
    for entry in entries:
        try:
            child = entry.lstat()
        except OSError as error:
            raise ValueError(ERROR) from error
        if (
            not stat.S_ISREG(child.st_mode)
            or entry.is_symlink()
            or (child.st_dev, child.st_ino) != created_files[entry.name]
        ):
            raise ValueError(ERROR)
    for entry in entries:
        try:
            entry.unlink()
        except OSError as error:
            raise ValueError(ERROR) from error
    try:
        workspace.rmdir()
    except OSError as error:
        raise ValueError(ERROR) from error


def _validate_workspace_tree(
    workspace: Path,
    expected_initial: Mapping[str, bytes],
    *,
    expected_directory_identity: tuple[int, int] | None = None,
) -> dict[str, object]:
    try:
        directory = workspace.lstat()
        entries = tuple(sorted(workspace.iterdir(), key=lambda item: item.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not stat.S_ISDIR(directory.st_mode)
        or workspace.is_symlink()
        or stat.S_IMODE(directory.st_mode) != 0o755
        or (
            expected_directory_identity is not None
            and (directory.st_dev, directory.st_ino) != expected_directory_identity
        )
        or tuple(path.name for path in entries) != tuple(sorted(REVIEW_FILES))
    ):
        raise ValueError(ERROR)
    payloads: dict[str, bytes] = {}
    records: list[dict[str, object]] = []
    for path in entries:
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
            payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise ValueError(ERROR) from error
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or metadata.st_size != len(payload)
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or (
                path.name in IMMUTABLE_REFERENCE_FILES
                and payload != expected_initial[path.name]
            )
        ):
            raise ValueError(ERROR)
        payloads[path.name] = payload
        records.append({
            "name": path.name,
            "bytes": len(payload),
            "lines": payload.count(b"\n"),
            "sha256": _sha256(payload),
            "mode": "0644",
        })
    worklist = payloads[WORKLIST_FILE]
    rows = _strict_csv(worklist, overlay.ALL_FIELDS)
    if (
        len(rows) != 1
        or {field: rows[0][field] for field in overlay.FROZEN_FIELDS}
        != overlay._frozen_initial_values()
    ):
        raise ValueError(ERROR)
    future_nonblank_count = sum(
        rows[0][field] != "" for field in overlay.FUTURE_FIELDS
    )
    return {
        "approval_decision_generated": False,
        "approved_smarts_generated": False,
        "atom_map_answers_generated": False,
        "authority_changed": False,
        "canonical_entry_type": "real_directory",
        "current_worklist_sha256": _sha256(worklist),
        "editable_field_count": 25,
        "feature_semantics_reaudit_required_before_training": True,
        "file_count": 6,
        "files": records,
        "formal_worklist_modified": False,
        "future_nonblank_count": future_nonblank_count,
        "immutable_reference_file_count": 5,
        "publication_scheme": PUBLICATION_SCHEME,
        "ready_for_direct_submission": False,
        "ready_for_human_evidence_entry": True,
        "ready_for_semantic_validation": False,
        "ready_for_training": False,
        "row_count": 1,
        "semantic_validation_performed": False,
        "subdirectory_count": 0,
        "workspace_mode": "0755",
        "workspace_name": WORKSPACE_NAME,
    }


def _materialize_review_copy(
    *,
    repo_root: Path,
    state_root: Path,
    output_dir: Path,
    payloads: Mapping[str, bytes] | None = None,
    source_payloads: Mapping[str, bytes] | None = None,
) -> dict[str, object]:
    state, _parent, output = _validate_output_path(state_root, output_dir)
    if os.path.lexists(output):
        raise FileExistsError(ERROR)
    if payloads is None:
        built = build_covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1(
            repo_root=repo_root, state_root=state
        )
        source = _validate_source_template_tree(
            repo_root=repo_root, state_root=state
        )
    else:
        built = dict(payloads)
        if source_payloads is None:
            raise ValueError(ERROR)
        source = dict(source_payloads)
    _validate_initial_payloads(built, source)
    os.mkdir(output, 0o700)
    directory_identity = _identity(output)
    created_files: dict[str, tuple[int, int]] = {}
    try:
        os.chmod(output, 0o755, follow_symlinks=False)
        for name in REVIEW_FILES:
            created_files[name] = _write_payload(output / name, built[name])
        return _validate_workspace_tree(
            output,
            built,
            expected_directory_identity=directory_identity,
        )
    except BaseException:
        _safe_cleanup_created_directory(
            output, directory_identity, created_files
        )
        raise


def _check_review_copy(
    *, repo_root: Path, state_root: Path, output_dir: Path,
) -> dict[str, object]:
    state, _parent, output = _validate_output_path(state_root, output_dir)
    _validate_source_materializer_commit(repo_root)
    source = _validate_source_template_tree(repo_root=repo_root, state_root=state)
    expected = _build_payloads(source)
    _validate_initial_payloads(expected, source)
    report = _validate_workspace_tree(output, expected)
    lifecycle = _derive_lifecycle(_collect_lifecycle(repo_root))
    report["lifecycle_profile"] = lifecycle["lifecycle_profile"]
    report["formal_candidate_commit"] = lifecycle["formal_candidate_commit"]
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize or read-only check the CovaPIE Current11 UNIT_000001 "
            "controlled editable reaction-transformation review copy v1."
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
    state_root = args.state_root
    output_dir = (
        args.output_dir
        if args.output_dir is not None
        else state_root / "manual-review" / WORKSPACE_NAME
    )
    try:
        if args.check:
            report = _check_review_copy(
                repo_root=repo_root,
                state_root=state_root,
                output_dir=output_dir,
            )
        else:
            report = _materialize_review_copy(
                repo_root=repo_root,
                state_root=state_root,
                output_dir=output_dir,
            )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(
        report,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
