#!/usr/bin/env python3
"""Exclusively materialize or read-only check the transformation dossier."""

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

from covalent_ext.covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1 import (  # noqa: E402
    DOSSIER_FILES,
    DOSSIER_PARENT_RELATIVE,
    DOSSIER_RELATIVE,
    ERROR,
    MANIFEST_FILE,
    PUBLICATION_SCHEME,
    QUESTIONNAIRE_FILE,
    REVIEW_UNIT_ID,
    _derive_lifecycle,
    _collect_lifecycle,
    _editable_runtime_report,
    _sha256,
    _strict_json,
    _validate_editable,
    _validate_payloads,
    build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1,
)


def _identity(path: Path) -> tuple[int, int]:
    metadata = path.lstat()
    return metadata.st_dev, metadata.st_ino


def _validate_output_path(state_root: Path, output_dir: Path) -> tuple[Path, Path]:
    try:
        if not state_root.is_absolute() or state_root.is_symlink():
            raise ValueError(ERROR)
        state = state_root.resolve(strict=True)
        state_metadata = state.lstat()
        aids = state / "manual-review-aids"
        aids_metadata = aids.lstat()
        parent = state / DOSSIER_PARENT_RELATIVE
        parent_metadata = parent.lstat()
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        state != state_root
        or not stat.S_ISDIR(state_metadata.st_mode)
        or aids.is_symlink()
        or not stat.S_ISDIR(aids_metadata.st_mode)
        or aids.resolve(strict=True) != aids
        or parent.is_symlink()
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or parent.resolve(strict=True) != parent
    ):
        raise ValueError(ERROR)
    if (
        not output_dir.is_absolute()
        or output_dir.parent != parent
        or output_dir.name != REVIEW_UNIT_ID
    ):
        raise ValueError(ERROR)
    return parent, output_dir


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
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
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
            path.unlink()
        raise


def _safe_cleanup_created_directory(
    output: Path,
    directory_identity: tuple[int, int],
    created_files: Mapping[str, tuple[int, int]],
) -> None:
    try:
        metadata = output.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or (metadata.st_dev, metadata.st_ino) != directory_identity
    ):
        raise ValueError(ERROR)
    try:
        entries = tuple(sorted(output.iterdir(), key=lambda item: item.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if tuple(item.name for item in entries) != tuple(sorted(created_files)):
        raise ValueError(ERROR)
    for entry in entries:
        child = entry.lstat()
        if (
            not stat.S_ISREG(child.st_mode)
            or (child.st_dev, child.st_ino) != created_files[entry.name]
        ):
            raise ValueError(ERROR)
    for entry in entries:
        entry.unlink()
    output.rmdir()


def _validate_dossier_tree(
    output: Path,
    expected: Mapping[str, bytes],
    *,
    expected_directory_identity: tuple[int, int] | None = None,
) -> dict[str, object]:
    try:
        metadata = output.lstat()
        entries = tuple(sorted(output.iterdir(), key=lambda item: item.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or output.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o755
        or (
            expected_directory_identity is not None
            and (metadata.st_dev, metadata.st_ino) != expected_directory_identity
        )
        or tuple(item.name for item in entries) != tuple(sorted(DOSSIER_FILES))
        or tuple(expected) != DOSSIER_FILES
    ):
        raise ValueError(ERROR)
    payloads: dict[str, bytes] = {}
    records: list[dict[str, object]] = []
    for child in entries:
        child_metadata = child.lstat()
        payload = child.read_bytes()
        if (
            not stat.S_ISREG(child_metadata.st_mode)
            or child.is_symlink()
            or stat.S_IMODE(child_metadata.st_mode) != 0o644
            or child_metadata.st_size != len(payload)
            or payload != expected[child.name]
        ):
            raise ValueError(ERROR)
        payloads[child.name] = payload
        records.append({
            "name": child.name,
            "bytes": len(payload),
            "lines": payload.count(b"\n"),
            "sha256": _sha256(payload),
            "mode": "0644",
        })
    ordered = {name: payloads[name] for name in DOSSIER_FILES}
    _validate_payloads(ordered)
    manifest = _strict_json(ordered[MANIFEST_FILE], dict)
    questionnaire = ordered[QUESTIONNAIRE_FILE].decode("utf-8")
    if (
        manifest["prefilled_answer_count"] != 0
        or questionnaire.count("proposed_value:\n") != 25
    ):
        raise ValueError(ERROR)
    return {
        "approval_decision_generated": False,
        "atom_map_answers_generated": False,
        "authority_changed": False,
        "dossier_file_count": 8,
        "dossier_mode": "0755",
        "feature_semantics_reaudit_required_before_training": True,
        "files": records,
        "formal_worklist_modified": False,
        "human_answers_prefilled": False,
        "non_authoritative_review_aid": True,
        "post_state_generated": False,
        "prefilled_answer_count": 0,
        "publication_scheme": PUBLICATION_SCHEME,
        "question_count": 25,
        "ready_for_direct_submission": False,
        "ready_for_formal_worklist_update": False,
        "ready_for_human_evidence_acquisition": True,
        "ready_for_semantic_validation": False,
        "ready_for_training": False,
        "review_unit_id": REVIEW_UNIT_ID,
        "semantic_validation_performed": False,
        "subdirectory_count": 0,
    }


def _materialize_dossier(
    *,
    repo_root: Path,
    state_root: Path,
    output_dir: Path,
    payloads: Mapping[str, bytes] | None = None,
) -> dict[str, object]:
    _parent, output = _validate_output_path(state_root, output_dir)
    if os.path.lexists(output):
        raise FileExistsError(ERROR)
    built = (
        dict(payloads)
        if payloads is not None
        else build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
    )
    _validate_payloads(built)
    try:
        output.mkdir(mode=0o700)
    except FileExistsError as error:
        raise FileExistsError(ERROR) from error
    directory_identity = _identity(output)
    created: dict[str, tuple[int, int]] = {}
    try:
        os.chmod(output, 0o755, follow_symlinks=False)
        for name in DOSSIER_FILES:
            created[name] = _write_payload(output / name, built[name])
        return _validate_dossier_tree(
            output,
            built,
            expected_directory_identity=directory_identity,
        )
    except BaseException:
        _safe_cleanup_created_directory(output, directory_identity, created)
        raise


def _check_dossier(
    *, repo_root: Path, state_root: Path, output_dir: Path,
) -> dict[str, object]:
    _parent, output = _validate_output_path(state_root, output_dir)
    expected = build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=repo_root,
        state_root=state_root,
    )
    report = _validate_dossier_tree(output, expected)
    formal = state_root == repo_root.parent / "covapie-state"
    editable_payloads, _editable_identity = _validate_editable(
        repo_root, state_root, formal=formal
    )
    report.update(_editable_runtime_report(editable_payloads))
    lifecycle = _derive_lifecycle(_collect_lifecycle(repo_root))
    report.update({
        "base_commit": lifecycle["origin_main"] if not lifecycle["formal_candidate_commit"] else "9fbb1da5da504e6dadd89ace90a9e5959f1ba3de",
        "formal_candidate_commit": lifecycle["formal_candidate_commit"],
        "lifecycle_profile": lifecycle["lifecycle_profile"],
    })
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Exclusively materialize or read-only check the non-authoritative "
            "Current11 UNIT_000001 transformation review dossier."
        )
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repo_root = args.repo_root
        state_root = args.state_root
        output_dir = args.output_dir or state_root / DOSSIER_RELATIVE
        if args.check:
            report = _check_dossier(
                repo_root=repo_root,
                state_root=state_root,
                output_dir=output_dir,
            )
        else:
            report = _materialize_dossier(
                repo_root=repo_root,
                state_root=state_root,
                output_dir=output_dir,
            )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
