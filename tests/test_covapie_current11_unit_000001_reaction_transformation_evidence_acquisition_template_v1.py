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
    covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1
    as template,
)


STATE_ROOT = ROOT.parent / "covapie-state"
SCRIPT_PATH = ROOT / template.SCRIPT_PATH
FORMAL_PARENT = STATE_ROOT / "manual-review"
FORMAL_TARGET = FORMAL_PARENT / template.WORKSPACE_NAME
WORKSPACE = FORMAL_PARENT / overlay.WORKSPACE_NAME
DOSSIER = STATE_ROOT / overlay.DOSSIER_RELATIVE


def _load_materializer():
    spec = importlib.util.spec_from_file_location(
        "covapie_current11_transformation_template_materializer_test_module",
        SCRIPT_PATH,
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


def _tree_sha(directory: Path) -> dict[str, str]:
    return {
        path.name: _sha256(path.read_bytes())
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
    }


def _formal_state_snapshot() -> dict[str, object]:
    canonical = WORKSPACE.lstat()
    workspace_target = os.readlink(WORKSPACE)
    workspace_object = WORKSPACE.parent / workspace_target
    object_metadata = workspace_object.lstat()
    dossier_metadata = DOSSIER.lstat()
    with (WORKSPACE / "family_rule_approval_worklist.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        worklist = list(csv.DictReader(stream))
    with (WORKSPACE / "sample_support_evidence.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        support = list(csv.DictReader(stream))
    evidence = json.loads(
        (WORKSPACE / "family_rule_candidate_evidence.json").read_text(
            encoding="utf-8"
        )
    )
    questionnaire = (
        DOSSIER / "human_review_questionnaire.md"
    ).read_text(encoding="utf-8").splitlines()
    return {
        "workspace_canonical": (
            canonical.st_dev,
            canonical.st_ino,
            stat.S_IFMT(canonical.st_mode),
        ),
        "workspace_target": workspace_target,
        "workspace_object": (
            object_metadata.st_dev,
            object_metadata.st_ino,
            stat.S_IMODE(object_metadata.st_mode),
        ),
        "workspace_sha": _tree_sha(workspace_object),
        "review_units": len(worklist),
        "support_rows": len(support),
        "human_cells": len(worklist) * len(overlay.HISTORICAL_HUMAN_FIELDS),
        "human_nonblank": sum(
            row[field] != ""
            for row in worklist
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ),
        "family_approved": sum(
            row["reaction_family_review_decision"]
            == "approve_reaction_family_identity"
            for row in worklist
        ),
        "rule_approved": sum(
            row["warhead_rule_review_decision"] == "approve_complete_warhead_rule"
            for row in worklist
        ),
        "approved_authority_true": sum(
            row["approved_authority"] is True for row in evidence
        ),
        "dossier": (
            dossier_metadata.st_dev,
            dossier_metadata.st_ino,
            stat.S_IMODE(dossier_metadata.st_mode),
        ),
        "dossier_sha": _tree_sha(DOSSIER),
        "questionnaire_blank": sum(
            questionnaire.count(f"{field}:") == 1
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ),
    }


def _assert_template_target_state_is_valid(
    *,
    state_root: Path,
    output: Path,
    expected_payloads: Mapping[str, bytes],
    require_present: bool | None,
) -> dict[str, object]:
    assert require_present is None or type(require_present) is bool
    assert output == state_root / "manual-review" / template.WORKSPACE_NAME
    parent = output.parent
    objects = tuple(sorted(
        parent.glob(f"{template.OBJECT_DIRECTORY_PREFIX}*"),
        key=lambda path: path.name,
    ))
    temporary = tuple(sorted(
        path.name
        for path in parent.iterdir()
        if template.WORKSPACE_NAME in path.name
        and (".tmp" in path.name or path.name.endswith(".part"))
    ))
    probe = tuple(sorted(
        path.name
        for path in parent.iterdir()
        if template.WORKSPACE_NAME in path.name and "probe" in path.name
    ))
    present = os.path.lexists(output)
    if require_present is not None:
        assert present is require_present
    if not present:
        assert not output.is_symlink()
        assert objects == ()
        assert temporary == ()
        assert probe == ()
        return {
            "state": "absent",
            "canonical_lexists": False,
            "canonical_is_symlink": False,
            "objects": (),
            "temporary": (),
            "probe": (),
        }

    canonical = output.lstat()
    assert stat.S_ISLNK(canonical.st_mode)
    relative_target = os.readlink(output)
    assert relative_target
    assert not Path(relative_target).is_absolute()
    assert "/" not in relative_target
    assert ".." not in relative_target
    assert relative_target.startswith(template.OBJECT_DIRECTORY_PREFIX)
    assert len(objects) == 1
    object_directory = parent / relative_target
    assert object_directory == objects[0]
    object_metadata = object_directory.lstat()
    assert stat.S_ISDIR(object_metadata.st_mode)
    assert not object_directory.is_symlink()
    assert stat.S_IMODE(object_metadata.st_mode) == 0o755
    entries = tuple(sorted(
        object_directory.iterdir(), key=lambda path: path.name,
    ))
    assert tuple(path.name for path in entries) == tuple(
        sorted(template.TEMPLATE_FILES)
    )
    assert len(entries) == 6
    assert sum(path.is_dir() for path in entries) == 0
    assert sum(path.is_symlink() for path in entries) == 0
    assert sum(
        not stat.S_ISREG(path.lstat().st_mode) for path in entries
    ) == 0
    file_snapshot: list[tuple[object, ...]] = []
    for path in entries:
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        payload = path.read_bytes()
        assert payload == expected_payloads[path.name]
        file_snapshot.append((
            path.name,
            metadata.st_dev,
            metadata.st_ino,
            stat.S_IMODE(metadata.st_mode),
            len(payload),
            _sha256(payload),
        ))
    assert temporary == ()
    assert probe == ()
    check = materializer._check_template(
        repo_root=ROOT,
        state_root=state_root,
        output_dir=output,
    )
    assert check["canonical_entry_type"] == "symlink"
    assert check["canonical_symlink_target"] == relative_target
    return {
        "state": "published",
        "canonical_identity": (canonical.st_dev, canonical.st_ino),
        "canonical_target": relative_target,
        "object_identity": (
            object_metadata.st_dev,
            object_metadata.st_ino,
        ),
        "object_mode": stat.S_IMODE(object_metadata.st_mode),
        "files": tuple(file_snapshot),
        "temporary": (),
        "probe": (),
    }


@pytest.fixture(scope="module")
def built() -> dict[str, bytes]:
    return template.build_covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )


def _temporary_output(tmp_path: Path) -> tuple[Path, Path]:
    temporary_state = tmp_path / "temporary-state"
    parent = temporary_state / "manual-review"
    parent.mkdir(parents=True)
    return temporary_state, parent / template.WORKSPACE_NAME


def _object_directories(output: Path) -> list[Path]:
    return sorted(output.parent.glob(f"{template.OBJECT_DIRECTORY_PREFIX}*"))


def _direct_directory_snapshot(directory: Path) -> tuple[object, ...]:
    metadata = directory.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        return (
            metadata.st_dev,
            metadata.st_ino,
            stat.S_IFMT(metadata.st_mode),
            os.readlink(directory),
        )
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IMODE(metadata.st_mode),
        tuple(
            (
                path.name,
                path.lstat().st_dev,
                path.lstat().st_ino,
                stat.S_IFMT(path.lstat().st_mode),
            )
            for path in sorted(directory.iterdir(), key=lambda item: item.name)
        ),
    )


def test_unique_public_api_is_keyword_only() -> None:
    assert template.__all__ == (
        "build_covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1",
    )
    functions = [
        name
        for name, value in inspect.getmembers(template, inspect.isfunction)
        if value.__module__ == template.__name__ and not name.startswith("_")
    ]
    assert functions == list(template.__all__)
    signature = inspect.signature(getattr(template, template.__all__[0]))
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError):
        getattr(template, template.__all__[0])(ROOT, STATE_ROOT)


def test_import_is_silent_and_side_effect_free(tmp_path: Path) -> None:
    before = tuple(tmp_path.iterdir())
    code = (
        "import sys;"
        f"sys.path.insert(0,{str(SRC)!r});"
        "import covalent_ext."
        "covapie_current11_unit_000001_reaction_transformation_evidence_"
        "acquisition_template_v1"
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
    assert tuple(tmp_path.iterdir()) == before


def test_overlay_formal_commit_exact9_and_five_sha() -> None:
    artifacts = template._validate_overlay_commit_identity(ROOT)
    assert template.OVERLAY_FORMAL_COMMIT == template.BASE_COMMIT
    assert template.OVERLAY_CANDIDATE_PATHS == overlay.CANDIDATE_PATHS
    assert tuple(artifacts) == overlay.ARTIFACT_PATHS
    assert {
        path: _sha256(payload) for path, payload in artifacts.items()
    } == template.OVERLAY_ARTIFACT_SHA256
    template._validate_overlay_artifacts(artifacts)


def test_overlay_published_lifecycle_and_semantics() -> None:
    response = overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )
    template._validate_overlay_response(response)
    assert response["lifecycle_profile"] == "transformation_overlay_published_successor"
    assert response["formal_candidate_commit"] == template.BASE_COMMIT
    assert response["formal_post_reaction_authority_count"] == 0
    assert response["complete_rule_evidence_ready"] is False
    assert response["feature_semantics_reaudit_required_before_training"] is True
    assert response["ready_for_training"] is False


def test_builder_is_deterministic_exact6_and_read_only(
    built: dict[str, bytes],
) -> None:
    before_state = _formal_state_snapshot()
    before_target = _assert_template_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    second = template.build_covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1(
        repo_root=ROOT,
        state_root=STATE_ROOT,
    )
    assert built == second
    assert tuple(built) == template.TEMPLATE_FILES
    assert all(type(payload) is bytes for payload in built.values())
    assert _formal_state_snapshot() == before_state
    after_target = _assert_template_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    assert after_target == before_target


def test_frozen_workspace_and_dossier_identity() -> None:
    snapshot = _formal_state_snapshot()
    assert snapshot["workspace_canonical"] == (
        49, 177964064880, stat.S_IFLNK,
    )
    assert snapshot["workspace_target"] == overlay.WORKSPACE_TARGET
    assert snapshot["workspace_object"] == (49, 177964064865, 0o755)
    assert snapshot["workspace_sha"] == overlay.WORKSPACE_SHA256
    assert snapshot["review_units"] == 7
    assert snapshot["support_rows"] == 11
    assert snapshot["human_cells"] == 210
    assert snapshot["human_nonblank"] == 0
    assert snapshot["family_approved"] == 0
    assert snapshot["rule_approved"] == 0
    assert snapshot["approved_authority_true"] == 0
    assert snapshot["dossier"] == (49, 177964065463, 0o755)
    assert snapshot["dossier_sha"] == overlay.DOSSIER_SHA256
    assert snapshot["questionnaire_blank"] == 30


def test_worklist_exact41_order_exact16_and_exact25_blank(
    built: dict[str, bytes],
) -> None:
    fields, rows = _csv(built[template.WORKLIST_FILE])
    assert fields == overlay.ALL_FIELDS
    assert len(fields) == 41
    assert len(overlay.FROZEN_FIELDS) == 16
    assert len(overlay.FUTURE_FIELDS) == 25
    assert len(rows) == 1
    row = rows[0]
    assert {field: row[field] for field in overlay.FROZEN_FIELDS} == (
        overlay._frozen_initial_values()
    )
    assert all(row[field] == "" for field in overlay.FUTURE_FIELDS)
    assert row["candidate_local_graph_rule_sha256"] == (
        "106441a31fa4f9516c174c5a0fa89709e820ebeeff419ba30883ea34a1c26bb6"
    )
    assert row["candidate_formed_bond_order"] == "single"
    assert row["pre_reaction_center_bond_order_sum"] == "4"
    assert row[
        "conditional_post_bond_order_sum_if_internal_bonds_unchanged"
    ] == "5"
    assert row["post_reaction_authority_status"] == "absent"
    assert row["schema_gap_detected"] == "true"


def test_decision_attestation_and_reviewer_fields_are_blank(
    built: dict[str, bytes],
) -> None:
    _fields, rows = _csv(built[template.WORKLIST_FILE])
    row = rows[0]
    assert row["transformation_review_decision"] == ""
    assert row["transformation_identity_explicitly_attested"] == ""
    assert row["transformation_full_semantics_explicitly_attested"] == ""
    assert row["reviewer_id"] == ""
    assert row["attestor_id"] == ""
    assert row["review_completed"] == ""


def _placeholder_leaves(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from _placeholder_leaves(child)
    elif isinstance(value, list):
        for child in value:
            yield from _placeholder_leaves(child)
    elif isinstance(value, str):
        yield value
    else:
        raise AssertionError(type(value))


def test_structured_schema_exact8_placeholder_only_and_complete(
    built: dict[str, bytes],
) -> None:
    schemas = json.loads(built[template.SCHEMA_FILE])
    assert schemas == overlay.STRUCTURED_JSON_SCHEMAS
    assert len(schemas) == 8
    overlay._validate_structured_json_schema_contracts_v1()
    attachment = schemas[
        "reviewed_attachment_boundary_map_numbers_by_sample_json"
    ]["samples"]["<sample_id>"]
    assert len(attachment) == 2
    assert all(type(record) is dict for record in attachment)
    leaving = schemas["reviewed_leaving_group_contract_json"]["samples"][
        "<sample_id>"
    ]
    assert set(leaving) == {"status", "leaving_group_records"}
    assert set(leaving["leaving_group_records"][0]) == {
        "leaving_atom_map_numbers", "broken_edge",
    }
    assert all(
        leaf == "..." or (leaf.startswith("<") and leaf.endswith(">"))
        for leaf in _placeholder_leaves(schemas)
    )


def test_gap_matrix_exact2_is_byte_copy_and_still_blocked(
    built: dict[str, bytes],
) -> None:
    formal = template._git_blob(
        ROOT, template.BASE_COMMIT, overlay.GAP_MATRIX_PATH
    )
    assert built[template.GAP_FILE] == formal
    fields, rows = _csv(built[template.GAP_FILE])
    assert fields == overlay.GAP_MATRIX_COLUMNS
    assert [row["sample_index_row_id"] for row in rows] == list(overlay.SAMPLE_IDS)
    assert len(rows) == 2
    assert {row["pre_reaction_center_bond_order_sum"] for row in rows} == {"4"}
    assert {
        row["conditional_post_bond_order_sum_if_internal_bonds_unchanged"]
        for row in rows
    } == {"5"}
    assert {row["effective_boundary_cardinality"] for row in rows} == {"2"}
    assert {row["post_reaction_graph_authority"] for row in rows} == {"missing"}
    assert {row["post_internal_bond_delta_authority"] for row in rows} == {"missing"}
    assert {row["post_formal_charge_authority"] for row in rows} == {"missing"}
    assert {row["post_protonation_authority"] for row in rows} == {"missing"}
    assert {
        row["complete_rule_evidence_ready_for_human_decision"] for row in rows
    } == {"false"}
    assert rows == list(overlay._gap_rows())


def test_source_inventory_exact35_is_byte_copy_and_non_authoritative(
    built: dict[str, bytes],
) -> None:
    formal = template._git_blob(
        ROOT, template.BASE_COMMIT, overlay.SOURCE_INVENTORY_PATH
    )
    assert built[template.SOURCE_FILE] == formal
    fields, rows = _csv(built[template.SOURCE_FILE])
    assert fields == overlay.SOURCE_INVENTORY_COLUMNS
    assert len(rows) == 35
    assert all(row["authoritative_for_transformation"] == "false" for row in rows)
    assert sum(
        row["authority_scope"]
        == "formal_post_reaction_transformation_authority"
        for row in rows
    ) == 0
    dossier_rows = [
        row for row in rows if row["source_namespace"] == "non_authoritative_state_aid"
    ]
    assert len(dossier_rows) == 6
    assert all(
        row["lineage_note"] == "non_authoritative_human_review_aid_crosscheck"
        for row in dossier_rows
    )
    geometry_rows = [
        row
        for row in rows
        if row["authority_scope"] == "formal_pair_geometry_only"
    ]
    assert geometry_rows
    assert all(
        row["lineage_note"] == "geometry only; not bond order or transformation"
        for row in geometry_rows
    )


def test_manifest_binds_sources_and_other_five_files(
    built: dict[str, bytes],
) -> None:
    manifest = json.loads(built[template.MANIFEST_FILE])
    assert manifest == template._manifest({
        name: built[name] for name in template.TEMPLATE_FILES[:-1]
    })
    assert manifest["base_commit"] == template.BASE_COMMIT
    assert manifest["overlay_formal_commit"] == template.BASE_COMMIT
    assert manifest["sample_count"] == 2
    assert manifest["field_count"] == 41
    assert manifest["frozen_field_count"] == 16
    assert manifest["future_field_count"] == 25
    assert manifest["future_nonblank_count"] == 0
    assert manifest["schema_template_count"] == 8
    assert manifest["gap_evidence_row_count"] == 2
    assert manifest["source_inventory_row_count"] == 35
    assert manifest["template_file_count"] == 6
    assert manifest["formal_post_reaction_authority_count"] == 0
    assert tuple(manifest["template_file_sha256"]) == tuple(sorted(
        template.TEMPLATE_FILES[:-1]
    ))
    assert template.MANIFEST_FILE not in manifest["template_file_sha256"]
    assert manifest["source_overlay_artifact_sha256"] == (
        template._source_overlay_sha_witness()
    )


@pytest.mark.parametrize(
    "field,expected",
    (
        ("human_answers_prefilled", False),
        ("post_state_generated", False),
        ("atom_map_answers_generated", False),
        ("approved_smarts_generated", False),
        ("approval_decision_generated", False),
        ("formal_worklist_modified", False),
        ("authority_changed", False),
        ("review_submission_compiled", False),
        ("review_ingested", False),
        ("authority_bundle_generated", False),
        ("role_or_seed_generated", False),
        ("tensor_materialized", False),
        ("model_changed", False),
        ("training_used", False),
        ("feature_semantics_reaudit_required_before_training", True),
        ("ready_for_training", False),
        ("ready_for_controlled_editable_copy", True),
        ("ready_for_direct_submission", False),
    ),
)
def test_manifest_execution_boundaries(
    built: dict[str, bytes], field: str, expected: bool,
) -> None:
    manifest = json.loads(built[template.MANIFEST_FILE])
    assert manifest[field] is expected


def test_readme_states_immutable_empty_and_training_boundaries(
    built: dict[str, bytes],
) -> None:
    readme = built[template.README_FILE].decode("utf-8")
    normalized = " ".join(readme.split())
    for phrase in (
        "immutable initial acquisition template",
        "not an editable review submission",
        "contains no transformation answers",
        "All 25 future",
        "An empty string means unreviewed",
        "explicit canonical empty list",
        "gap signal only",
        "does not prove a reaction mechanism",
        "does not generate",
        "must not be used directly as a submission",
        "controlled process may create an editable copy",
        "feature-semantics successor audit",
        "ready_for_training=false",
    ):
        assert phrase in normalized


def test_payload_has_no_answer_or_authority_generation(
    built: dict[str, bytes],
) -> None:
    worklist = _csv(built[template.WORKLIST_FILE])[1][0]
    assert all(worklist[field] == "" for field in overlay.FUTURE_FIELDS)
    schemas = json.loads(built[template.SCHEMA_FILE])
    schema_text = json.dumps(schemas, sort_keys=True)
    assert "C=O" not in schema_text
    assert "C-O" not in schema_text
    assert "approve_reaction_transformation_contract" not in schema_text
    assert not any(
        isinstance(leaf, int) for leaf in _placeholder_leaves(schemas)
    )


def test_temporary_materialize_and_cli_check_twice(
    tmp_path: Path, built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    materialized_report = materializer._materialize_template(
        repo_root=ROOT,
        state_root=temporary_state,
        output_dir=output,
        payloads=built,
    )
    assert materialized_report["publication_scheme"] == template.PUBLICATION_SCHEME
    assert materialized_report["canonical_entry_type"] == "symlink"
    command = (
        sys.executable,
        "-B",
        str(SCRIPT_PATH),
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(temporary_state),
        "--output-dir",
        str(output),
        "--check",
    )
    assert output.is_symlink()
    relative_target = os.readlink(output)
    assert "/" not in relative_target and ".." not in relative_target
    assert relative_target.startswith(template.OBJECT_DIRECTORY_PREFIX)
    object_directory = output.parent / relative_target
    assert stat.S_IMODE(object_directory.lstat().st_mode) == 0o755
    assert tuple(sorted(path.name for path in object_directory.iterdir())) == (
        tuple(sorted(template.TEMPLATE_FILES))
    )
    published_snapshot = _assert_template_target_state_is_valid(
        state_root=temporary_state,
        output=output,
        expected_payloads=built,
        require_present=True,
    )
    assert published_snapshot["state"] == "published"
    first = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    before = _tree_sha(object_directory)
    second = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert (first.returncode, second.returncode) == (0, 0)
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert _tree_sha(object_directory) == before


@pytest.mark.parametrize(
    "case",
    (
        "state_internal_wrong_parent",
        "external_parent",
        "symlinked_manual_review_parent",
    ),
)
def test_output_dir_must_be_exact_state_manual_review_child(
    tmp_path: Path,
    built: dict[str, bytes],
    case: str,
) -> None:
    temporary_state = tmp_path / "temporary-state"
    temporary_state.mkdir()
    formal_parent = temporary_state / "manual-review"
    external_parent = tmp_path / "external-manual-review"
    external_parent.mkdir()
    external_marker = external_parent / "outside-marker.txt"
    external_marker.write_text("outside-preserve\n", encoding="utf-8")

    watched_directories = [temporary_state, external_parent]
    markers = [external_marker]
    if case == "symlinked_manual_review_parent":
        os.symlink(
            external_parent,
            formal_parent,
            target_is_directory=True,
        )
        output_parent = formal_parent
    else:
        formal_parent.mkdir()
        legal_marker = formal_parent / "legal-marker.txt"
        legal_marker.write_text("legal-preserve\n", encoding="utf-8")
        watched_directories.append(formal_parent)
        markers.append(legal_marker)
        if case == "state_internal_wrong_parent":
            output_parent = temporary_state / "other"
            output_parent.mkdir()
            watched_directories.append(output_parent)
        else:
            assert case == "external_parent"
            output_parent = external_parent

    competitor = output_parent / "competitor-marker.txt"
    competitor.write_text("competitor-preserve\n", encoding="utf-8")
    markers.append(competitor)
    output = output_parent / template.WORKSPACE_NAME
    watched_directories.append(formal_parent)
    watched_directories = list(dict.fromkeys(watched_directories))

    formal_state_before = _formal_state_snapshot()
    formal_target_before = _assert_template_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    directory_before = {
        path: _direct_directory_snapshot(path)
        for path in watched_directories
    }
    marker_before = {
        path: (
            path.lstat().st_dev,
            path.lstat().st_ino,
            path.read_bytes(),
        )
        for path in markers
    }

    with pytest.raises(ValueError, match=template.ERROR):
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )

    assert not os.path.lexists(output)
    for parent in (formal_parent, output_parent, external_parent):
        assert not any(
            path.name.startswith(template.OBJECT_DIRECTORY_PREFIX)
            or (
                template.WORKSPACE_NAME in path.name
                and (
                    ".tmp" in path.name
                    or path.name.endswith(".part")
                    or "probe" in path.name
                )
            )
            for path in parent.iterdir()
        )
    assert {
        path: _direct_directory_snapshot(path)
        for path in watched_directories
    } == directory_before
    assert {
        path: (
            path.lstat().st_dev,
            path.lstat().st_ino,
            path.read_bytes(),
        )
        for path in markers
    } == marker_before
    assert _formal_state_snapshot() == formal_state_before
    assert _assert_template_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    ) == formal_target_before


def test_post_publication_canonical_disappearance_cleans_owned_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    observed: dict[str, object] = {}

    def disappear_after_publication(
        canonical_entry: Path,
        expected: Mapping[str, bytes] | None,
        *,
        expected_canonical_identity: tuple[int, int] | None = None,
        expected_object_identity: tuple[int, int] | None = None,
    ) -> dict[str, object]:
        assert canonical_entry == output
        assert expected == built
        canonical = canonical_entry.lstat()
        assert stat.S_ISLNK(canonical.st_mode)
        assert (canonical.st_dev, canonical.st_ino) == (
            expected_canonical_identity
        )
        relative_target = os.readlink(canonical_entry)
        object_directory = canonical_entry.parent / relative_target
        object_metadata = object_directory.lstat()
        assert stat.S_ISDIR(object_metadata.st_mode)
        assert (object_metadata.st_dev, object_metadata.st_ino) == (
            expected_object_identity
        )
        assert tuple(sorted(path.name for path in object_directory.iterdir())) == (
            tuple(sorted(template.TEMPLATE_FILES))
        )
        observed.update({
            "canonical_created": True,
            "relative_target": relative_target,
            "object_identity": expected_object_identity,
        })
        canonical_entry.unlink()
        assert not os.path.lexists(canonical_entry)
        raise RuntimeError("injected post-publication validation failure")

    monkeypatch.setattr(
        materializer,
        "_validate_canonical_entry",
        disappear_after_publication,
    )
    with pytest.raises(
        RuntimeError, match="injected post-publication validation failure"
    ):
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )
    assert observed["canonical_created"] is True
    assert str(observed["relative_target"]).startswith(
        template.OBJECT_DIRECTORY_PREFIX
    )
    absent = _assert_template_target_state_is_valid(
        state_root=temporary_state,
        output=output,
        expected_payloads=built,
        require_present=False,
    )
    assert absent["state"] == "absent"
    assert tuple(output.parent.iterdir()) == ()


def test_existing_target_is_preserved(
    tmp_path: Path, built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    output.mkdir()
    marker = output / "human-edit.txt"
    marker.write_text("preserve\n", encoding="utf-8")
    identity = (output.lstat().st_dev, output.lstat().st_ino)
    with pytest.raises(FileExistsError, match=template.ERROR):
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )
    assert (output.lstat().st_dev, output.lstat().st_ino) == identity
    assert marker.read_text(encoding="utf-8") == "preserve\n"
    assert _object_directories(output) == []


def test_partial_write_cleanup_removes_only_created_inodes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
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
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )
    assert not os.path.lexists(output)
    assert _object_directories(output) == []


def test_symlink_publication_collision_preserves_competitor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    original_symlink = materializer.os.symlink
    competitor_identity: tuple[int, int] | None = None

    def collide(
        source: str, destination: Path, *, target_is_directory: bool,
    ) -> None:
        nonlocal competitor_identity
        Path(destination).mkdir()
        (Path(destination) / "human-edit.txt").write_text(
            "preserve\n", encoding="utf-8"
        )
        competitor_identity = materializer._identity(Path(destination))
        original_symlink(
            source, destination, target_is_directory=target_is_directory
        )

    monkeypatch.setattr(materializer.os, "symlink", collide)
    with pytest.raises(FileExistsError):
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )
    assert competitor_identity is not None
    assert materializer._identity(output) == competitor_identity
    assert (output / "human-edit.txt").read_text(encoding="utf-8") == "preserve\n"
    assert _object_directories(output) == []


def test_file_inode_replacement_is_not_deleted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    original = materializer._write_payload
    first_path: Path | None = None
    calls = 0

    def replace_then_fail(path: Path, payload: bytes) -> tuple[int, int]:
        nonlocal first_path, calls
        calls += 1
        if calls == 1:
            first_path = path
            return original(path, payload)
        assert first_path is not None
        first_path.rename(tmp_path / "parked-original-file")
        first_path.write_bytes(b"competitor\n")
        os.chmod(first_path, 0o644)
        raise OSError("trigger inode-safe cleanup")

    monkeypatch.setattr(materializer, "_write_payload", replace_then_fail)
    with pytest.raises(ValueError, match=template.ERROR):
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )
    leftovers = _object_directories(output)
    assert len(leftovers) == 1
    assert (leftovers[0] / template.README_FILE).read_bytes() == b"competitor\n"
    assert not os.path.lexists(output)


def test_object_inode_replacement_is_not_deleted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    parked = tmp_path / "parked-original-object"

    def replace_object(
        source: str, destination: Path, *, target_is_directory: bool,
    ) -> None:
        object_directory = Path(destination).parent / source
        object_directory.rename(parked)
        object_directory.mkdir()
        raise OSError("trigger object inode replacement")

    monkeypatch.setattr(materializer.os, "symlink", replace_object)
    with pytest.raises(ValueError, match=template.ERROR):
        materializer._materialize_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
            payloads=built,
        )
    replacements = _object_directories(output)
    assert len(replacements) == 1 and replacements[0].is_dir()
    assert parked.is_dir()
    assert len(tuple(parked.iterdir())) == 6
    assert not os.path.lexists(output)


def test_check_rejects_modified_direct_evidence(
    tmp_path: Path, built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    materializer._materialize_template(
        repo_root=ROOT,
        state_root=temporary_state,
        output_dir=output,
        payloads=built,
    )
    object_directory = output.parent / os.readlink(output)
    gap = object_directory / template.GAP_FILE
    gap.write_bytes(gap.read_bytes() + b"\n")
    with pytest.raises(ValueError, match=template.ERROR):
        materializer._check_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
        )


def test_check_rejects_semantically_equivalent_noncanonical_worklist_bytes(
    tmp_path: Path, built: dict[str, bytes],
) -> None:
    temporary_state, output = _temporary_output(tmp_path)
    materializer._materialize_template(
        repo_root=ROOT,
        state_root=temporary_state,
        output_dir=output,
        payloads=built,
    )
    canonical_before = output.lstat()
    object_directory = output.parent / os.readlink(output)
    object_before = object_directory.lstat()
    worklist_path = object_directory / template.WORKLIST_FILE
    original_worklist = worklist_path.read_bytes()
    original_fields, original_rows = _csv(original_worklist)
    assert len(original_rows) == 1

    serialized = io.StringIO(newline="")
    writer = csv.DictWriter(
        serialized,
        fieldnames=original_fields,
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(original_rows)
    modified_worklist = serialized.getvalue().encode("utf-8")
    modified_fields, modified_rows = _csv(modified_worklist)
    assert modified_worklist != original_worklist
    assert modified_fields == original_fields
    assert modified_rows == original_rows
    assert all(
        modified_rows[0][field] == "" for field in overlay.FUTURE_FIELDS
    )
    assert {
        field: modified_rows[0][field] for field in overlay.FROZEN_FIELDS
    } == {
        field: original_rows[0][field] for field in overlay.FROZEN_FIELDS
    }
    worklist_path.write_bytes(modified_worklist)

    manifest_path = object_directory / template.MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["template_file_sha256"][template.WORKLIST_FILE] = _sha256(
        modified_worklist
    )
    manifest_path.write_bytes(template._canonical_json_bytes(manifest))
    modified_payloads = {
        name: (object_directory / name).read_bytes()
        for name in template.TEMPLATE_FILES
    }
    template._validate_payloads(modified_payloads)

    file_bytes_before_check = {
        name: (object_directory / name).read_bytes()
        for name in template.TEMPLATE_FILES
    }
    with pytest.raises(ValueError, match=template.ERROR):
        materializer._check_template(
            repo_root=ROOT,
            state_root=temporary_state,
            output_dir=output,
        )
    command = (
        sys.executable,
        "-B",
        str(SCRIPT_PATH),
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(temporary_state),
        "--output-dir",
        str(output),
        "--check",
    )
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert template.ERROR.encode("utf-8") in completed.stderr
    canonical_after = output.lstat()
    object_after = object_directory.lstat()
    assert (canonical_after.st_dev, canonical_after.st_ino) == (
        canonical_before.st_dev,
        canonical_before.st_ino,
    )
    assert (object_after.st_dev, object_after.st_ino) == (
        object_before.st_dev,
        object_before.st_ino,
    )
    assert {
        name: (object_directory / name).read_bytes()
        for name in template.TEMPLATE_FILES
    } == file_bytes_before_check


def _run_current_lifecycle_node(repository: Path) -> str:
    node = (
        f"{template.TEST_PATH}::"
        "test_current_repository_matches_current_lifecycle"
    )
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
    assert completed.stderr == ""
    assert "1 passed" in completed.stdout
    return completed.stdout


def test_repository_lifecycle_exact3_in_base_anchored_temp_git(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "lifecycle-repository"
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        check=True,
        capture_output=True,
    )
    try:
        subprocess.run(
            ("git", "checkout", "-B", template.BRANCH, template.BASE_COMMIT),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            (
                "git", "update-ref", "refs/remotes/origin/main",
                template.BASE_COMMIT,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        assert subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip() == template.BASE_COMMIT
        for relative in template.CANDIDATE_PATHS:
            absent = subprocess.run(
                (
                    "git", "cat-file", "-e",
                    f"{template.BASE_COMMIT}:{relative}",
                ),
                cwd=repository,
                check=False,
                capture_output=True,
            )
            assert absent.returncode != 0
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
            os.chmod(destination, 0o644)

        precommit_stdout = _run_current_lifecycle_node(repository)
        assert "1 passed" in precommit_stdout
        precommit = template._derive_lifecycle(
            template._collect_lifecycle(repository)
        )
        assert precommit["lifecycle_profile"] == (
            "transformation_template_materializer_precommit_candidate"
        )

        subprocess.run(
            ("git", "add", "--", *template.CANDIDATE_PATHS),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            (
                "git",
                "-c", "user.name=CovaPIE Test",
                "-c", "user.email=covapie-test@example.invalid",
                "commit", "-m", template.FORMAL_COMMIT_SUBJECT,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        committed_stdout = _run_current_lifecycle_node(repository)
        assert "1 passed" in committed_stdout
        committed_facts = template._collect_lifecycle(repository)
        committed = template._derive_lifecycle(committed_facts)
        formal_commit = committed["formal_candidate_commit"]
        assert committed["lifecycle_profile"] == (
            "transformation_template_materializer_committed_unpushed"
        )
        assert isinstance(formal_commit, str)
        assert re.fullmatch(r"[0-9a-f]{40}", formal_commit) is not None
        formal_facts = committed_facts["path_commits"][0]
        assert formal_facts["commit"] == formal_commit
        assert formal_facts["parents"] == [template.BASE_COMMIT]
        assert formal_facts["subject"] == template.FORMAL_COMMIT_SUBJECT
        assert formal_facts["changed_paths"] == template.CANDIDATE_PATHS
        assert formal_facts["changed_statuses"] == {
            path: "A" for path in template.CANDIDATE_PATHS
        }
        assert formal_facts["path_modes"] == {
            path: "100644" for path in template.CANDIDATE_PATHS
        }

        subprocess.run(
            (
                "git", "update-ref", "refs/remotes/origin/main",
                formal_commit,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        unrelated = repository / "UNRELATED_SUCCESSOR.txt"
        unrelated.write_text("unrelated successor\n", encoding="utf-8")
        subprocess.run(
            ("git", "add", "--", unrelated.name),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            (
                "git",
                "-c", "user.name=CovaPIE Test",
                "-c", "user.email=covapie-test@example.invalid",
                "commit", "-m", "add unrelated successor",
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        successor = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        successor_paths = subprocess.run(
            (
                "git", "diff-tree", "--no-commit-id", "--name-only", "-r",
                successor,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        assert successor_paths == [unrelated.name]
        subprocess.run(
            ("git", "update-ref", "refs/remotes/origin/main", successor),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        published_stdout = _run_current_lifecycle_node(repository)
        assert "1 passed" in published_stdout
        published_facts = template._collect_lifecycle(repository)
        published = template._derive_lifecycle(published_facts)
        assert published["lifecycle_profile"] == (
            "transformation_template_materializer_published_successor"
        )
        assert published["formal_candidate_commit"] == formal_commit
        assert published_facts["head"] == successor
        assert published_facts["origin"] == successor
        assert len(published_facts["path_commits"]) == 1
        published_formal = published_facts["path_commits"][0]
        assert published_formal["commit"] == formal_commit
        for relative in template.CANDIDATE_PATHS:
            assert published_facts["live_paths"][relative] == {
                "tracked": True,
                "mode": "100644",
                "index_blob": published_formal["path_blobs"][relative],
                "blob": published_formal["path_blobs"][relative],
            }
    finally:
        shutil.rmtree(repository)
        assert not os.path.lexists(repository)
        assert tuple(tmp_path.iterdir()) == ()


def test_repository_lifecycle_fails_closed_on_candidate_drift(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "drift-repository"
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        check=True,
        capture_output=True,
    )
    try:
        subprocess.run(
            ("git", "checkout", "-B", template.BRANCH, template.BASE_COMMIT),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            (
                "git", "update-ref", "refs/remotes/origin/main",
                template.BASE_COMMIT,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        assert subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip() == template.BASE_COMMIT
        for relative in template.CANDIDATE_PATHS:
            absent = subprocess.run(
                (
                    "git", "cat-file", "-e",
                    f"{template.BASE_COMMIT}:{relative}",
                ),
                cwd=repository,
                check=False,
                capture_output=True,
            )
            assert absent.returncode != 0
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
            os.chmod(destination, 0o644)
        subprocess.run(
            ("git", "add", "--", *template.CANDIDATE_PATHS),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            (
                "git",
                "-c", "user.name=CovaPIE Test",
                "-c", "user.email=covapie-test@example.invalid",
                "commit", "-m", template.FORMAL_COMMIT_SUBJECT,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        committed = template._collect_lifecycle(repository)
        assert len(committed["path_commits"]) == 1
        formal = committed["path_commits"][0]
        assert formal["parents"] == [template.BASE_COMMIT]
        assert formal["subject"] == template.FORMAL_COMMIT_SUBJECT
        assert formal["changed_paths"] == template.CANDIDATE_PATHS
        assert formal["changed_statuses"] == {
            path: "A" for path in template.CANDIDATE_PATHS
        }
        assert formal["path_modes"] == {
            path: "100644" for path in template.CANDIDATE_PATHS
        }
        (repository / template.GUIDE_PATH).write_text(
            "drift\n", encoding="utf-8"
        )
        facts = template._collect_lifecycle(repository)
        with pytest.raises(ValueError, match=template.ERROR):
            template._derive_lifecycle(facts)
    finally:
        shutil.rmtree(repository)
        assert not os.path.lexists(repository)
        assert tuple(tmp_path.iterdir()) == ()


def test_candidate_exact4_files_and_safety_boundary() -> None:
    assert template.CANDIDATE_PATHS == tuple(sorted((
        template.GUIDE_PATH,
        template.SCRIPT_PATH,
        template.MODULE_PATH,
        template.TEST_PATH,
    )))
    for relative in template.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\x00" not in payload
        payload.decode("utf-8")
        assert all(line.rstrip() == line for line in payload.decode().splitlines())
    assert all(
        not relative.startswith((
            "data/raw/", "checkpoints/", "equivariant_diffusion/",
        ))
        for relative in template.CANDIDATE_PATHS
    )
    assert not any(
        relative.endswith((
            ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
            ".tgz", ".npz", ".tmp", ".part",
        ))
        for relative in template.CANDIDATE_PATHS
    )


def test_current_repository_matches_current_lifecycle() -> None:
    facts = template._collect_lifecycle(ROOT)
    lifecycle = template._derive_lifecycle(facts)
    profiles = {
        "transformation_template_materializer_precommit_candidate",
        "transformation_template_materializer_committed_unpushed",
        "transformation_template_materializer_published_successor",
    }
    profile = lifecycle["lifecycle_profile"]
    assert profile in profiles
    assert facts["branch"] == template.BRANCH == "main"
    assert tuple(facts["live_paths"]) == template.CANDIDATE_PATHS
    for relative in template.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert relative not in facts["tracked"]
        assert relative not in facts["staged"]
    actual_origin = subprocess.run(
        ("git", "rev-parse", "refs/remotes/origin/main"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    actual_ahead, actual_behind = (
        int(value)
        for value in subprocess.run(
            (
                "git", "rev-list", "--left-right", "--count",
                "HEAD...refs/remotes/origin/main",
            ),
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
    )
    assert lifecycle["origin_main"] == facts["origin"] == actual_origin
    assert (lifecycle["ahead"], lifecycle["behind"]) == (
        facts["ahead"], facts["behind"]
    ) == (actual_ahead, actual_behind)

    if profile == "transformation_template_materializer_precommit_candidate":
        assert facts["head"] == facts["origin"] == template.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (0, 0)
        assert facts["tracked"] == facts["staged"] == ()
        assert facts["untracked"] == template.CANDIDATE_PATHS
        assert facts["porcelain"] == tuple(
            sorted(f"?? {path}" for path in template.CANDIDATE_PATHS)
        )
        assert all(
            facts["live_paths"][path]["tracked"] is False
            for path in template.CANDIDATE_PATHS
        )
        assert lifecycle["formal_candidate_commit"] == ""
        return

    formal_commit = lifecycle["formal_candidate_commit"]
    assert type(formal_commit) is str
    assert re.fullmatch(r"[0-9a-f]{40}", formal_commit) is not None
    assert formal_commit != template.BASE_COMMIT
    assert len(facts["path_commits"]) == 1
    formal = facts["path_commits"][0]
    assert formal["commit"] == formal_commit
    assert formal["parents"] == [template.BASE_COMMIT]
    assert formal["subject"] == template.FORMAL_COMMIT_SUBJECT
    assert formal["changed_paths"] == template.CANDIDATE_PATHS
    assert formal["changed_statuses"] == {
        path: "A" for path in template.CANDIDATE_PATHS
    }
    assert formal["path_modes"] == {
        path: "100644" for path in template.CANDIDATE_PATHS
    }
    for relative in template.CANDIDATE_PATHS:
        assert facts["live_paths"][relative] == {
            "tracked": True,
            "mode": "100644",
            "index_blob": formal["path_blobs"][relative],
            "blob": formal["path_blobs"][relative],
        }
        assert relative not in facts["untracked"]

    if profile == "transformation_template_materializer_committed_unpushed":
        assert facts["head"] == formal_commit
        assert facts["origin"] == template.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (1, 0)
        assert facts["tracked"] == facts["staged"] == facts["untracked"] == ()
        assert facts["porcelain"] == ()
        return

    assert profile == "transformation_template_materializer_published_successor"
    assert formal["ancestor_head"] is True
    assert formal["ancestor_origin"] is True


def test_formal_state_and_target_remain_unchanged_after_all_module_tests(
    built: dict[str, bytes],
) -> None:
    before = _formal_state_snapshot()
    target_before = _assert_template_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    template._validate_payloads(built)
    after = _formal_state_snapshot()
    target_after = _assert_template_target_state_is_valid(
        state_root=STATE_ROOT,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    assert after == before
    assert target_after == target_before
