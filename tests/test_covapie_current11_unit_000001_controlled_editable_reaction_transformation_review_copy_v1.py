from __future__ import annotations

import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Iterator, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_reaction_transformation_evidence_overlay_contract_v1
    as overlay,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1
    as review,
)


STATE_ROOT = ROOT.parent / "covapie-state"
FORMAL_PARENT = STATE_ROOT / "manual-review"
FORMAL_TARGET = FORMAL_PARENT / review.WORKSPACE_NAME
SOURCE_CANONICAL = FORMAL_PARENT / review.SOURCE_WORKSPACE_NAME
SOURCE_OBJECT = FORMAL_PARENT / review.SOURCE_OBJECT_NAME
FAMILY_WORKSPACE = FORMAL_PARENT / overlay.WORKSPACE_NAME
DOSSIER = STATE_ROOT / overlay.DOSSIER_RELATIVE
SCRIPT = ROOT / review.SCRIPT_PATH


def _load_materializer():
    spec = importlib.util.spec_from_file_location(
        "controlled_editable_review_copy_materializer_test_module", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


materializer = _load_materializer()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    return tuple(reader.fieldnames or ()), list(reader)


def _csv_bytes(fields: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _tree_sha(directory: Path) -> dict[str, str]:
    return {
        path.name: _sha256(path.read_bytes())
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
    }


def _target_residue(output: Path) -> tuple[str, ...]:
    return tuple(sorted(
        path.name
        for path in output.parent.iterdir()
        if review.WORKSPACE_NAME in path.name
        and (
            ".tmp" in path.name
            or path.name.endswith(".part")
            or "probe" in path.name
            or "backup" in path.name
        )
    ))


def _editable_target_snapshot(output: Path) -> dict[str, object]:
    residue = _target_residue(output)
    if not os.path.lexists(output):
        return {
            "state": "absent",
            "target_lexists": False,
            "target_is_symlink": False,
            "residue": residue,
        }
    metadata = output.lstat()
    entries = tuple(sorted(output.iterdir(), key=lambda item: item.name))
    files: list[tuple[object, ...]] = []
    for path in entries:
        child = path.lstat()
        payload = path.read_bytes()
        files.append((
            path.name,
            child.st_dev,
            child.st_ino,
            stat.S_IFMT(child.st_mode),
            stat.S_IMODE(child.st_mode),
            len(payload),
            _sha256(payload),
        ))
    worklist = (output / review.WORKLIST_FILE).read_bytes()
    _fields, rows = _csv(worklist)
    return {
        "state": "published",
        "target_lexists": True,
        "target_is_symlink": output.is_symlink(),
        "target_identity": (metadata.st_dev, metadata.st_ino),
        "target_type": stat.S_IFMT(metadata.st_mode),
        "target_mode": stat.S_IMODE(metadata.st_mode),
        "entries": tuple(path.name for path in entries),
        "files": tuple(files),
        "worklist_sha256": _sha256(worklist),
        "future_nonblank_count": sum(
            rows[0][field] != "" for field in overlay.FUTURE_FIELDS
        ),
        "residue": residue,
    }


def _assert_editable_target_state_is_valid(
    *,
    state_root: Path,
    output: Path,
    expected_initial: Mapping[str, bytes],
    require_present: bool | None,
) -> dict[str, object]:
    assert require_present is None or type(require_present) is bool
    assert output == state_root / "manual-review" / review.WORKSPACE_NAME
    present = os.path.lexists(output)
    if require_present is not None:
        assert present is require_present
    residue = _target_residue(output)
    assert residue == ()
    if not present:
        assert not output.is_symlink()
        return {
            "state": "absent",
            "target_lexists": False,
            "target_is_symlink": False,
            "residue": (),
        }

    directory = output.lstat()
    assert stat.S_ISDIR(directory.st_mode)
    assert not output.is_symlink()
    assert stat.S_IMODE(directory.st_mode) == 0o755
    entries = tuple(sorted(output.iterdir(), key=lambda item: item.name))
    assert tuple(path.name for path in entries) == tuple(sorted(review.REVIEW_FILES))
    assert len(entries) == 6
    assert sum(path.is_dir() for path in entries) == 0
    assert sum(path.is_symlink() for path in entries) == 0
    assert sum(not stat.S_ISREG(path.lstat().st_mode) for path in entries) == 0
    payloads: dict[str, bytes] = {}
    for path in entries:
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\x00" not in payload
        payload.decode("utf-8")
        payloads[path.name] = payload
    for name in review.IMMUTABLE_REFERENCE_FILES:
        assert payloads[name] == expected_initial[name]
    fields, rows = _csv(payloads[review.WORKLIST_FILE])
    assert fields == overlay.ALL_FIELDS and len(fields) == 41
    assert len(rows) == 1
    assert {field: rows[0][field] for field in overlay.FROZEN_FIELDS} == (
        overlay._frozen_initial_values()
    )
    future_nonblank_count = sum(
        rows[0][field] != "" for field in overlay.FUTURE_FIELDS
    )
    before_check = _editable_target_snapshot(output)
    check_state = state_root.resolve() if state_root.is_symlink() else state_root
    check_output = check_state / "manual-review" / review.WORKSPACE_NAME
    report = materializer._check_review_copy(
        repo_root=ROOT,
        state_root=check_state,
        output_dir=check_output,
    )
    assert _editable_target_snapshot(output) == before_check
    assert report["future_nonblank_count"] == future_nonblank_count
    assert report["semantic_validation_performed"] is False
    assert report["ready_for_semantic_validation"] is False
    assert report["ready_for_direct_submission"] is False
    assert report["authority_changed"] is False
    assert report["ready_for_training"] is False
    return {
        **before_check,
        "future_nonblank_count": future_nonblank_count,
        "semantic_validation_performed": False,
        "ready_for_semantic_validation": False,
        "ready_for_direct_submission": False,
        "authority_changed": False,
        "ready_for_training": False,
    }


def _formal_snapshot() -> dict[str, object]:
    family_metadata = FAMILY_WORKSPACE.lstat()
    family_target = os.readlink(FAMILY_WORKSPACE)
    family_object = FAMILY_WORKSPACE.parent / family_target
    family_object_metadata = family_object.lstat()
    dossier_metadata = DOSSIER.lstat()
    source_metadata = SOURCE_CANONICAL.lstat()
    source_object_metadata = SOURCE_OBJECT.lstat()
    with (FAMILY_WORKSPACE / "family_rule_approval_worklist.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        family_rows = list(csv.DictReader(stream))
    questionnaire = (DOSSIER / "human_review_questionnaire.md").read_text(
        encoding="utf-8"
    )
    return {
        "family_canonical": (
            family_metadata.st_dev,
            family_metadata.st_ino,
            stat.S_IFMT(family_metadata.st_mode),
            family_target,
        ),
        "family_object": (
            family_object_metadata.st_dev,
            family_object_metadata.st_ino,
            stat.S_IMODE(family_object_metadata.st_mode),
            _tree_sha(family_object),
        ),
        "human_cells": len(family_rows) * len(overlay.HISTORICAL_HUMAN_FIELDS),
        "human_nonblank": sum(
            row[field] != ""
            for row in family_rows
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ),
        "dossier": (
            dossier_metadata.st_dev,
            dossier_metadata.st_ino,
            stat.S_IMODE(dossier_metadata.st_mode),
            _tree_sha(DOSSIER),
        ),
        "questionnaire_blank": sum(
            questionnaire.count(f"{field}:") == 1
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ),
        "source_canonical": (
            source_metadata.st_dev,
            source_metadata.st_ino,
            stat.S_IFMT(source_metadata.st_mode),
            os.readlink(SOURCE_CANONICAL),
        ),
        "source_object": (
            source_object_metadata.st_dev,
            source_object_metadata.st_ino,
            stat.S_IMODE(source_object_metadata.st_mode),
            _tree_sha(SOURCE_OBJECT),
        ),
        "editable_target": _editable_target_snapshot(FORMAL_TARGET),
    }


@pytest.fixture(scope="module", autouse=True)
def preserve_formal_state(source_payloads: dict[str, bytes]) -> Iterator[None]:
    expected_initial = review._build_payloads(source_payloads)
    before = _formal_snapshot()
    _assert_editable_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_initial=expected_initial,
        require_present=None,
    )
    yield
    after = _formal_snapshot()
    assert after == before
    _assert_editable_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_initial=expected_initial,
        require_present=None,
    )


@pytest.fixture(scope="module")
def source_payloads() -> dict[str, bytes]:
    return review._validate_source_template_tree(
        repo_root=ROOT, state_root=STATE_ROOT
    )


@pytest.fixture(scope="module")
def built() -> dict[str, bytes]:
    return review.build_covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )


def _temporary_state(tmp_path: Path) -> tuple[Path, Path]:
    state = tmp_path / "temporary-state"
    parent = state / "manual-review"
    parent.mkdir(parents=True)
    shutil.copytree(SOURCE_OBJECT, parent / review.SOURCE_OBJECT_NAME)
    os.symlink(review.SOURCE_OBJECT_NAME, parent / review.SOURCE_WORKSPACE_NAME)
    return state, parent / review.WORKSPACE_NAME


def _materialize(
    tmp_path: Path,
    built: Mapping[str, bytes],
    source_payloads: Mapping[str, bytes],
) -> tuple[Path, Path, dict[str, object]]:
    state, output = _temporary_state(tmp_path)
    report = materializer._materialize_review_copy(
        repo_root=ROOT,
        state_root=state,
        output_dir=output,
        payloads=built,
        source_payloads=source_payloads,
    )
    return state, output, report


def test_unique_keyword_only_public_api() -> None:
    assert review.__all__ == (
        "build_covapie_current11_unit_000001_controlled_editable_reaction_"
        "transformation_review_copy_v1",
    )
    functions = [
        name
        for name, value in inspect.getmembers(review, inspect.isfunction)
        if value.__module__ == review.__name__ and not name.startswith("_")
    ]
    assert functions == list(review.__all__)
    signature = inspect.signature(getattr(review, review.__all__[0]))
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError):
        getattr(review, review.__all__[0])(ROOT, STATE_ROOT)


def test_import_is_silent_and_has_no_output_side_effect(tmp_path: Path) -> None:
    code = (
        "import sys;"
        f"sys.path.insert(0,{str(SRC)!r});"
        "import covalent_ext."
        "covapie_current11_unit_000001_controlled_editable_reaction_"
        "transformation_review_copy_v1"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=tmp_path,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""
    assert tuple(tmp_path.iterdir()) == ()


def test_source_materializer_formal_commit_identity() -> None:
    review._validate_source_materializer_commit(ROOT)
    assert review.BASE_COMMIT == "dfc5dd59f4fff16b2bd85e321a277cdfe8aa9713"
    assert review.BASE_TREE == "f54d9c34a9a38c3e8a2650abf6ec184b61409508"
    assert review.BASE_PARENT == "767668bff04bb57021d16be0d2c0f002401993fc"
    assert review.SOURCE_CANDIDATE_PATHS == tuple(sorted(
        review.SOURCE_MATERIALIZER_SHA256
    ))


def test_immutable_template_canonical_and_object_identity() -> None:
    canonical = SOURCE_CANONICAL.lstat()
    object_metadata = SOURCE_OBJECT.lstat()
    assert stat.S_ISLNK(canonical.st_mode)
    assert (canonical.st_dev, canonical.st_ino) == review.SOURCE_CANONICAL_IDENTITY
    assert os.readlink(SOURCE_CANONICAL) == review.SOURCE_OBJECT_NAME
    assert not Path(review.SOURCE_OBJECT_NAME).is_absolute()
    assert "/" not in review.SOURCE_OBJECT_NAME
    assert ".." not in review.SOURCE_OBJECT_NAME
    assert stat.S_ISDIR(object_metadata.st_mode)
    assert not SOURCE_OBJECT.is_symlink()
    assert (object_metadata.st_dev, object_metadata.st_ino) == review.SOURCE_OBJECT_IDENTITY
    assert stat.S_IMODE(object_metadata.st_mode) == 0o755


def test_immutable_template_exact6_sha_bytes_lines_and_modes(
    source_payloads: dict[str, bytes],
) -> None:
    assert tuple(source_payloads) == review.SOURCE_FILES
    assert tuple(sorted(path.name for path in SOURCE_OBJECT.iterdir())) == tuple(
        sorted(review.SOURCE_FILES)
    )
    for name in review.SOURCE_FILES:
        path = SOURCE_OBJECT / name
        metadata = path.lstat()
        payload = source_payloads[name]
        assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) == review.SOURCE_FILE_BYTES[name]
        assert payload.count(b"\n") == review.SOURCE_FILE_LINES[name]
        assert _sha256(payload) == review.SOURCE_FILE_SHA256[name]


def test_immutable_template_frozen_semantics(
    source_payloads: dict[str, bytes],
) -> None:
    review._validate_source_semantics(source_payloads)
    fields, rows = _csv(source_payloads[review.WORKLIST_FILE])
    assert fields == overlay.ALL_FIELDS
    assert len(rows) == 1
    assert len(overlay.FROZEN_FIELDS) == 16
    assert len(overlay.FUTURE_FIELDS) == 25
    assert all(rows[0][field] == "" for field in overlay.FUTURE_FIELDS)
    manifest = json.loads(source_payloads[review.SOURCE_MANIFEST_FILE])
    assert manifest["ready_for_controlled_editable_copy"] is True
    assert manifest["ready_for_direct_submission"] is False
    assert manifest["ready_for_training"] is False


def test_builder_is_deterministic_read_only_exact6(
    built: dict[str, bytes],
) -> None:
    before = _formal_snapshot()
    second = review.build_covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    assert built == second
    assert tuple(built) == review.REVIEW_FILES
    assert all(type(payload) is bytes for payload in built.values())
    assert _formal_snapshot() == before


def test_initial_worklist_and_three_references_are_byte_copies(
    built: dict[str, bytes], source_payloads: dict[str, bytes],
) -> None:
    for name in (
        review.WORKLIST_FILE,
        review.SCHEMA_FILE,
        review.GAP_FILE,
        review.SOURCE_FILE,
    ):
        assert built[name] == source_payloads[name]
    assert _sha256(built[review.WORKLIST_FILE]) == review.SOURCE_FILE_SHA256[
        review.WORKLIST_FILE
    ]


def test_initial_worklist_exact41_exact16_and_exact25_blank(
    built: dict[str, bytes],
) -> None:
    fields, rows = _csv(built[review.WORKLIST_FILE])
    assert fields == overlay.ALL_FIELDS and len(fields) == 41
    assert len(rows) == 1
    assert {field: rows[0][field] for field in overlay.FROZEN_FIELDS} == (
        overlay._frozen_initial_values()
    )
    assert sum(rows[0][field] != "" for field in overlay.FUTURE_FIELDS) == 0


def test_editable_manifest_contract(
    built: dict[str, bytes],
) -> None:
    manifest = json.loads(built[review.MANIFEST_FILE])
    assert manifest["review_copy_version"] == review.REVIEW_COPY_VERSION
    assert manifest["base_commit"] == review.BASE_COMMIT
    assert manifest["source_template_version"] == review.SOURCE_TEMPLATE_VERSION
    assert manifest["source_template_manifest_sha256"] == review.SOURCE_MANIFEST_SHA256
    assert manifest["source_template_file_sha256"] == review.SOURCE_FILE_SHA256
    assert manifest["row_count"] == 1 and manifest["field_count"] == 41
    assert manifest["frozen_field_count"] == 16
    assert manifest["editable_field_count"] == 25
    assert manifest["frozen_fields"] == list(overlay.FROZEN_FIELDS)
    assert manifest["editable_fields"] == list(overlay.FUTURE_FIELDS)
    assert manifest["mutable_files"] == [review.WORKLIST_FILE]
    assert manifest["immutable_reference_files"] == list(
        review.IMMUTABLE_REFERENCE_FILES
    )
    assert manifest["initial_future_nonblank_count"] == 0
    assert manifest["initial_worklist_sha256"] == review.SOURCE_FILE_SHA256[
        review.WORKLIST_FILE
    ]


def test_manifest_readiness_and_non_generation_flags(
    built: dict[str, bytes],
) -> None:
    manifest = json.loads(built[review.MANIFEST_FILE])
    for field in (
        "human_answers_prefilled",
        "semantic_validation_performed",
        "identity_attestation_completed",
        "full_semantics_attestation_completed",
        "approval_decision_generated",
        "approved_smarts_generated",
        "post_state_generated",
        "atom_map_answers_generated",
        "formal_worklist_modified",
        "authority_changed",
        "review_submission_compiled",
        "review_ingested",
        "authority_bundle_generated",
        "role_or_seed_generated",
        "tensor_materialized",
        "model_changed",
        "training_used",
        "ready_for_semantic_validation",
        "ready_for_direct_submission",
        "ready_for_training",
    ):
        assert manifest[field] is False
    assert manifest["ready_for_human_evidence_entry"] is True
    assert manifest["feature_semantics_reaudit_required_before_training"] is True


def test_readme_states_controlled_boundaries_without_answers(
    built: dict[str, bytes],
) -> None:
    text = built[review.README_FILE].decode("utf-8")
    for phrase in (
        "controlled editable review copy",
        "formally published",
        "Only `transformation_evidence_worklist.csv` is editable",
        "Exact16 frozen",
        "Exact25 future",
        "empty string means unreviewed",
        "explicit canonical empty list",
        "not a submission or an authority",
        "does not prove a reaction mechanism",
        "gap signal only",
        "independent semantic validation",
        "feature-semantics audit",
        "ready_for_training=false",
    ):
        assert phrase in text


def test_formal_editable_target_state_is_valid(
    built: dict[str, bytes],
) -> None:
    _assert_editable_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_initial=built,
        require_present=None,
    )


def test_temporary_materialize_is_real_directory_exact6_and_modes(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, report = _materialize(tmp_path, built, source_payloads)
    metadata = output.lstat()
    assert stat.S_ISDIR(metadata.st_mode) and not output.is_symlink()
    assert stat.S_IMODE(metadata.st_mode) == 0o755
    assert report["publication_scheme"] == review.PUBLICATION_SCHEME
    assert report["canonical_entry_type"] == "real_directory"
    assert tuple(sorted(path.name for path in output.iterdir())) == tuple(
        sorted(review.REVIEW_FILES)
    )
    for path in output.iterdir():
        child = path.lstat()
        assert stat.S_ISREG(child.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(child.st_mode) == 0o644
    validated = _assert_editable_target_state_is_valid(
        state_root=state,
        output=output,
        expected_initial=built,
        require_present=True,
    )
    assert validated["state"] == "published"
    assert validated["future_nonblank_count"] == 0


def test_cli_materialize_and_check_twice_are_deterministic(
    tmp_path: Path,
) -> None:
    state, output = _temporary_state(tmp_path)
    base = (
        sys.executable,
        "-B",
        str(SCRIPT),
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(state),
        "--output-dir",
        str(output),
    )
    created = subprocess.run(
        base,
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert created.returncode == 0 and created.stderr == b""
    assert output.is_dir() and not output.is_symlink()
    before = _tree_sha(output)
    first = subprocess.run(
        (*base, "--check"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    second = subprocess.run(
        (*base, "--check"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert (first.returncode, second.returncode) == (0, 0)
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert _tree_sha(output) == before
    report = json.loads(first.stdout)
    assert report["future_nonblank_count"] == 0
    assert report["current_worklist_sha256"] == review.SOURCE_FILE_SHA256[
        review.WORKLIST_FILE
    ]


def test_two_initial_materializations_are_byte_identical(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    _first_state, first, _first_report = _materialize(
        tmp_path / "first", built, source_payloads
    )
    _second_state, second, _second_report = _materialize(
        tmp_path / "second", built, source_payloads
    )
    assert _tree_sha(first) == _tree_sha(second)
    assert {
        path.name: path.read_bytes()
        for path in sorted(first.iterdir(), key=lambda item: item.name)
    } == {
        path.name: path.read_bytes()
        for path in sorted(second.iterdir(), key=lambda item: item.name)
    }


def test_future_text_edit_passes_structural_check_but_not_semantic_gate(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    fields, rows = _csv((output / review.WORKLIST_FILE).read_bytes())
    rows[0]["review_notes"] = "human review pending validation"
    os.chmod(output / review.WORKLIST_FILE, 0o600)
    (output / review.WORKLIST_FILE).write_bytes(_csv_bytes(fields, rows))
    os.chmod(output / review.WORKLIST_FILE, 0o644)
    report = _assert_editable_target_state_is_valid(
        state_root=state,
        output=output,
        expected_initial=built,
        require_present=True,
    )
    assert report["state"] == "published"
    assert report["future_nonblank_count"] == 1
    assert report["semantic_validation_performed"] is False
    assert report["ready_for_semantic_validation"] is False
    assert report["ready_for_direct_submission"] is False
    assert report["authority_changed"] is False
    assert report["ready_for_training"] is False


def test_frozen_field_drift_fails_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    fields, rows = _csv((output / review.WORKLIST_FILE).read_bytes())
    rows[0][overlay.FROZEN_FIELDS[0]] += "_DRIFT"
    (output / review.WORKLIST_FILE).write_bytes(_csv_bytes(fields, rows))
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._check_review_copy(
            repo_root=ROOT, state_root=state, output_dir=output
        )


def test_second_row_fails_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    fields, rows = _csv((output / review.WORKLIST_FILE).read_bytes())
    rows.append(dict(rows[0]))
    (output / review.WORKLIST_FILE).write_bytes(_csv_bytes(fields, rows))
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._check_review_copy(
            repo_root=ROOT, state_root=state, output_dir=output
        )


def test_deleted_field_fails_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    fields, rows = _csv((output / review.WORKLIST_FILE).read_bytes())
    reduced = fields[:-1]
    reduced_rows = [{field: rows[0][field] for field in reduced}]
    (output / review.WORKLIST_FILE).write_bytes(_csv_bytes(reduced, reduced_rows))
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._check_review_copy(
            repo_root=ROOT, state_root=state, output_dir=output
        )


def test_reordered_fields_fail_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    fields, rows = _csv((output / review.WORKLIST_FILE).read_bytes())
    reordered = (fields[1], fields[0], *fields[2:])
    (output / review.WORKLIST_FILE).write_bytes(_csv_bytes(reordered, rows))
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._check_review_copy(
            repo_root=ROOT, state_root=state, output_dir=output
        )


@pytest.mark.parametrize(
    "name",
    (review.README_FILE, review.SCHEMA_FILE, review.GAP_FILE, review.SOURCE_FILE),
)
def test_immutable_reference_drift_fails_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
    name: str,
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    path = output / name
    path.write_bytes(path.read_bytes() + b"drift\n")
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._check_review_copy(
            repo_root=ROOT, state_root=state, output_dir=output
        )


def test_manifest_drift_fails_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output, _report = _materialize(tmp_path, built, source_payloads)
    path = output / review.MANIFEST_FILE
    manifest = json.loads(path.read_bytes())
    manifest["ready_for_training"] = True
    path.write_bytes(review._canonical_json_bytes(manifest))
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._check_review_copy(
            repo_root=ROOT, state_root=state, output_dir=output
        )


def test_existing_target_is_refused_and_preserved(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output = _temporary_state(tmp_path)
    output.mkdir()
    marker = output / "human-edit.txt"
    marker.write_text("preserve\n", encoding="utf-8")
    identity = materializer._identity(output)
    with pytest.raises(FileExistsError, match=review.ERROR):
        materializer._materialize_review_copy(
            repo_root=ROOT,
            state_root=state,
            output_dir=output,
            payloads=built,
            source_payloads=source_payloads,
        )
    assert materializer._identity(output) == identity
    assert marker.read_bytes() == b"preserve\n"


def test_partial_write_failure_cleans_only_created_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output = _temporary_state(tmp_path)
    original = materializer._write_payload
    calls = 0

    def fail_second(path: Path, payload: bytes) -> tuple[int, int]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected partial write failure")
        return original(path, payload)

    monkeypatch.setattr(materializer, "_write_payload", fail_second)
    with pytest.raises(OSError, match="injected partial write failure"):
        materializer._materialize_review_copy(
            repo_root=ROOT,
            state_root=state,
            output_dir=output,
            payloads=built,
            source_payloads=source_payloads,
        )
    assert not os.path.lexists(output)


def test_file_inode_replacement_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output = _temporary_state(tmp_path)
    original = materializer._write_payload
    first: Path | None = None
    calls = 0

    def replace_then_fail(path: Path, payload: bytes) -> tuple[int, int]:
        nonlocal first, calls
        calls += 1
        if calls == 1:
            first = path
            return original(path, payload)
        assert first is not None
        first.rename(tmp_path / "parked-owned-file")
        first.write_bytes(b"competitor\n")
        os.chmod(first, 0o644)
        raise OSError("trigger inode-safe cleanup")

    monkeypatch.setattr(materializer, "_write_payload", replace_then_fail)
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._materialize_review_copy(
            repo_root=ROOT,
            state_root=state,
            output_dir=output,
            payloads=built,
            source_payloads=source_payloads,
        )
    assert output.is_dir()
    assert (output / review.README_FILE).read_bytes() == b"competitor\n"


def test_directory_inode_replacement_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
) -> None:
    state, output = _temporary_state(tmp_path)
    original = materializer._validate_workspace_tree
    parked = tmp_path / "parked-owned-directory"

    def replace_directory(
        workspace: Path,
        expected_initial: Mapping[str, bytes],
        *,
        expected_directory_identity: tuple[int, int] | None = None,
    ) -> dict[str, object]:
        assert workspace == output and expected_directory_identity is not None
        workspace.rename(parked)
        workspace.mkdir()
        (workspace / "competitor.txt").write_text("preserve\n", encoding="utf-8")
        raise OSError("trigger directory inode-safe cleanup")

    monkeypatch.setattr(materializer, "_validate_workspace_tree", replace_directory)
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._materialize_review_copy(
            repo_root=ROOT,
            state_root=state,
            output_dir=output,
            payloads=built,
            source_payloads=source_payloads,
        )
    assert original is not None
    assert (output / "competitor.txt").read_bytes() == b"preserve\n"
    assert len(tuple(parked.iterdir())) == 6


@pytest.mark.parametrize("case", ("wrong_name", "external_parent", "symlink_parent"))
def test_output_parent_boundary_fails_closed(
    tmp_path: Path,
    built: dict[str, bytes],
    source_payloads: dict[str, bytes],
    case: str,
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    parent = state / "manual-review"
    if case == "symlink_parent":
        os.symlink(external, parent, target_is_directory=True)
        output = parent / review.WORKSPACE_NAME
    else:
        parent.mkdir()
        output = (
            parent / "wrong-name"
            if case == "wrong_name"
            else external / review.WORKSPACE_NAME
        )
    marker = external / "marker.txt"
    marker.write_text("preserve\n", encoding="utf-8")
    with pytest.raises(ValueError, match=review.ERROR):
        materializer._materialize_review_copy(
            repo_root=ROOT,
            state_root=state,
            output_dir=output,
            payloads=built,
            source_payloads=source_payloads,
        )
    assert marker.read_bytes() == b"preserve\n"
    assert not os.path.lexists(output)


def _assert_formal_candidate_identity(
    facts: Mapping[str, object],
    formal_candidate: str,
    *,
    published: bool,
) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", formal_candidate)
    path_commits = facts["path_commits"]
    assert isinstance(path_commits, list) and len(path_commits) == 1
    commit = path_commits[0]
    assert commit["commit"] == formal_candidate
    assert commit["parents"] == [review.BASE_COMMIT]
    assert commit["subject"] == review.FORMAL_COMMIT_SUBJECT
    assert commit["changed_paths"] == review.CANDIDATE_PATHS
    assert commit["changed_statuses"] == {
        path: "A" for path in review.CANDIDATE_PATHS
    }
    assert commit["path_modes"] == {
        path: "100644" for path in review.CANDIDATE_PATHS
    }
    assert commit["ancestor_head"] is True
    assert commit["ancestor_origin"] is published
    live_paths = facts["live_paths"]
    for path in review.CANDIDATE_PATHS:
        formal_blob = commit["path_blobs"][path]
        assert live_paths[path] == {
            "tracked": True,
            "mode": "100644",
            "index_blob": formal_blob,
            "blob": formal_blob,
        }


def test_current_repository_matches_current_lifecycle() -> None:
    facts = review._collect_lifecycle(ROOT)
    lifecycle = review._derive_lifecycle(facts)
    profile = lifecycle["lifecycle_profile"]
    candidate_paths = set(review.CANDIDATE_PATHS)
    assert facts["branch"] == review.BRANCH == "main"
    assert tuple(facts["live_paths"]) == review.CANDIDATE_PATHS
    for relative in review.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
    assert candidate_paths.isdisjoint(facts["tracked"])
    assert candidate_paths.isdisjoint(facts["staged"])
    assert lifecycle["origin_main"] == facts["origin"]
    assert lifecycle["ahead"] == facts["ahead"]
    assert lifecycle["behind"] == facts["behind"]
    assert profile in {
        "controlled_transformation_review_copy_precommit_candidate",
        "controlled_transformation_review_copy_committed_unpushed",
        "controlled_transformation_review_copy_published_successor",
    }

    if profile == "controlled_transformation_review_copy_precommit_candidate":
        assert facts["head"] == facts["origin"] == review.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (0, 0)
        assert lifecycle["formal_candidate_commit"] == ""
        assert facts["untracked"] == review.CANDIDATE_PATHS
        assert facts["porcelain"] == tuple(sorted(
            f"?? {path}" for path in review.CANDIDATE_PATHS
        ))
        assert facts["tracked"] == facts["staged"] == ()
        assert all(
            facts["live_paths"][path]["tracked"] is False
            for path in review.CANDIDATE_PATHS
        )
        return

    formal_candidate = lifecycle["formal_candidate_commit"]
    assert candidate_paths.isdisjoint(facts["untracked"])
    if profile == "controlled_transformation_review_copy_committed_unpushed":
        assert facts["head"] == formal_candidate
        assert facts["origin"] == review.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (1, 0)
        _assert_formal_candidate_identity(
            facts, formal_candidate, published=False
        )
        assert facts["tracked"] == facts["staged"] == facts["untracked"] == ()
        assert facts["porcelain"] == ()
        return

    assert profile == "controlled_transformation_review_copy_published_successor"
    _assert_formal_candidate_identity(facts, formal_candidate, published=True)


def _successor_facts(*, published: bool) -> dict[str, object]:
    facts = deepcopy(review._collect_lifecycle(ROOT))
    commit = "a" * 40
    blobs = {
        path: facts["live_paths"][path]["blob"]
        for path in review.CANDIDATE_PATHS
    }
    facts.update({
        "head": commit,
        "origin": commit if published else review.BASE_COMMIT,
        "ahead": 0 if published else 1,
        "behind": 0,
        "tracked": (),
        "staged": (),
        "untracked": (),
        "porcelain": (),
        "path_commits": [{
            "commit": commit,
            "parents": [review.BASE_COMMIT],
            "subject": review.FORMAL_COMMIT_SUBJECT,
            "changed_paths": review.CANDIDATE_PATHS,
            "changed_statuses": {path: "A" for path in review.CANDIDATE_PATHS},
            "path_modes": {path: "100644" for path in review.CANDIDATE_PATHS},
            "path_blobs": blobs,
            "ancestor_head": True,
            "ancestor_origin": published,
        }],
        "live_paths": {
            path: {
                "tracked": True,
                "mode": "100644",
                "index_blob": blobs[path],
                "blob": blobs[path],
            }
            for path in review.CANDIDATE_PATHS
        },
    })
    return facts


def test_committed_unpushed_lifecycle_contract() -> None:
    lifecycle = review._derive_lifecycle(_successor_facts(published=False))
    assert lifecycle["lifecycle_profile"] == (
        "controlled_transformation_review_copy_committed_unpushed"
    )
    assert lifecycle["ahead"] == 1 and lifecycle["behind"] == 0


def test_published_successor_lifecycle_contract() -> None:
    lifecycle = review._derive_lifecycle(_successor_facts(published=True))
    assert lifecycle["lifecycle_profile"] == (
        "controlled_transformation_review_copy_published_successor"
    )
    assert lifecycle["ahead"] == 0 and lifecycle["behind"] == 0


def test_repository_lifecycle_exact3_in_base_anchored_temp_git(
    tmp_path: Path,
) -> None:
    assert tuple(tmp_path.iterdir()) == ()
    repository = tmp_path / ROOT.name
    state_link = tmp_path / "covapie-state"
    node = (
        f"{review.TEST_PATH}::"
        "test_current_repository_matches_current_lifecycle"
    )

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *args),
            cwd=repository,
            check=check,
            capture_output=True,
            text=True,
        )

    def run_lifecycle_node() -> None:
        completed = subprocess.run(
            (
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                node,
            ),
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": "src",
            },
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "1 passed" in completed.stdout

    subprocess.run(
        (
            "git", "clone", "--no-hardlinks", "--quiet", str(ROOT),
            str(repository),
        ),
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    try:
        git("checkout", "-B", "main", review.BASE_COMMIT)
        git("update-ref", "refs/remotes/origin/main", review.BASE_COMMIT)
        for relative in review.CANDIDATE_PATHS:
            assert git(
                "cat-file", "-e", f"{review.BASE_COMMIT}:{relative}",
                check=False,
            ).returncode != 0
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
            os.chmod(destination, 0o644)
        os.symlink(STATE_ROOT, state_link, target_is_directory=True)

        run_lifecycle_node()

        git("add", "--", *review.CANDIDATE_PATHS)
        git(
            "-c", "user.name=CovaPIE Test", "-c",
            "user.email=covapie-test@example.invalid", "commit", "--quiet",
            "-m", review.FORMAL_COMMIT_SUBJECT,
        )
        formal_candidate = git("rev-parse", "HEAD").stdout.strip()
        assert re.fullmatch(r"[0-9a-f]{40}", formal_candidate)
        assert git("show", "-s", "--format=%P", formal_candidate).stdout.split() == [
            review.BASE_COMMIT
        ]
        assert git("show", "-s", "--format=%s", formal_candidate).stdout.strip() == (
            review.FORMAL_COMMIT_SUBJECT
        )
        run_lifecycle_node()

        git("update-ref", "refs/remotes/origin/main", formal_candidate)
        unrelated = repository / "UNRELATED_CONTROLLED_REVIEW_SUCCESSOR.txt"
        unrelated.write_text("unrelated successor\n", encoding="utf-8")
        git("add", "--", unrelated.name)
        git(
            "-c", "user.name=CovaPIE Test", "-c",
            "user.email=covapie-test@example.invalid", "commit", "--quiet",
            "-m", "add unrelated controlled review successor witness",
        )
        successor = git("rev-parse", "HEAD").stdout.strip()
        git("update-ref", "refs/remotes/origin/main", successor)
        successor_changes = git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", successor
        ).stdout.splitlines()
        assert successor_changes == [unrelated.name]
        run_lifecycle_node()

        for relative in review.CANDIDATE_PATHS:
            formal_blob = git("rev-parse", f"{formal_candidate}:{relative}").stdout.strip()
            index_blob = git("ls-files", "--stage", "--", relative).stdout.split()[1]
            worktree_blob = git("hash-object", "--no-filters", "--", relative).stdout.strip()
            assert formal_blob == index_blob == worktree_blob
    finally:
        if repository.exists():
            shutil.rmtree(repository)
        if os.path.lexists(state_link):
            state_link.unlink()
    assert tuple(tmp_path.iterdir()) == ()


def test_candidate_exact4_file_identity_and_safety() -> None:
    assert len(review.CANDIDATE_PATHS) == 4
    assert review.BASE_COMMIT == "dfc5dd59f4fff16b2bd85e321a277cdfe8aa9713"
    forbidden_suffixes = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
        ".tgz", ".npz", ".tmp", ".part",
    }
    protected_roots = {"data/raw", "checkpoints", "equivariant_diffusion"}
    protected_files = {
        "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
    }
    for relative in review.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert not any(
            relative == protected or relative.startswith(f"{protected}/")
            for protected in protected_roots
        )
        assert relative not in protected_files
        assert path.suffix not in forbidden_suffixes
        assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf") and b"\x00" not in payload
        payload.decode("utf-8")
        assert all(line.rstrip() == line for line in payload.decode().splitlines())


def test_no_forbidden_runtime_import_or_operation_tokens() -> None:
    implementation = (ROOT / review.MODULE_PATH).read_text(encoding="utf-8").lower()
    script = (ROOT / review.SCRIPT_PATH).read_text(encoding="utf-8").lower()
    for token in (
        "import torch",
        "import rdkit",
        "import openbabel",
        "requests.",
        "urllib.",
        "data/raw",
        "checkpoints/",
    ):
        assert token not in implementation
        assert token not in script


def test_family_workspace_dossier_and_formal_target_contract(
    built: dict[str, bytes],
) -> None:
    snapshot = _formal_snapshot()
    assert snapshot["family_canonical"] == (
        49,
        177964064880,
        stat.S_IFLNK,
        overlay.WORKSPACE_TARGET,
    )
    assert snapshot["family_object"] == (
        49,
        177964064865,
        0o755,
        overlay.WORKSPACE_SHA256,
    )
    assert snapshot["human_cells"] == 210
    assert snapshot["human_nonblank"] == 0
    assert snapshot["dossier"] == (
        49,
        177964065463,
        0o755,
        overlay.DOSSIER_SHA256,
    )
    assert snapshot["questionnaire_blank"] == 30
    _assert_editable_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_initial=built,
        require_present=None,
    )
