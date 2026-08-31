from __future__ import annotations

import ast
import copy
import csv
import io
import json
from pathlib import Path
import stat

import pytest

from covalent_ext import (
    covapie_i12_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


ROOT = Path(__file__).resolve().parents[1]


def _formal() -> dict[str, object]:
    return copy.deepcopy(subject.load_frozen_formal_decision_v1(ROOT)["formal"])


def _set_path(document: object, path: tuple[object, ...], value: object) -> None:
    current = document
    for key in path[:-1]:
        current = current[key]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]


def _mutated_formal(path: tuple[object, ...], value: object) -> dict[str, object]:
    document = _formal()
    _set_path(document, path, value)
    return document


def _mutated_json_artifact(
    artifacts: dict[str, bytes], name: str, path: tuple[object, ...], value: object
) -> dict[str, bytes]:
    mutated = dict(artifacts)
    document = json.loads(mutated[name])
    _set_path(document, path, value)
    mutated[name] = subject._json_bytes(document)
    return mutated


def _mutated_matrix_artifact(
    artifacts: dict[str, bytes], row_index: int, field: str, value: str
) -> dict[str, bytes]:
    mutated = dict(artifacts)
    rows = list(csv.DictReader(io.StringIO(mutated[subject.MATRIX].decode("utf-8"))))
    rows[row_index][field] = value
    mutated[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows)
    return mutated


def test_public_api_is_exact() -> None:
    assert subject.__all__ == (
        "I12IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_frozen_formal_exact2_and_semantic_digest_are_bound() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    decision = bound["formal_decision_binding"]
    validator = bound["formal_validator_binding"]
    assert decision == {
        "path": subject.FORMAL_DECISION_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 26474,
        "SHA256": "e117da5c10c45603450eaab26ea6093ef07e70c4bf2ec2f0c7908aa38f531fa0",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "I12_FROZEN_FORMAL_HUMAN_DECISION",
    }
    assert validator == {
        "path": subject.FORMAL_VALIDATOR_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 65800,
        "SHA256": "05e1c27216b9f1e05b1f7114ff86f3103679931207344e44fd585fe097270f85",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "I12_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
    }
    formal = bound["formal"]
    assert formal["formal_semantic_canonical_sha256"] == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert subject._semantic_digest(formal) == subject.FORMAL_SEMANTIC_CANONICAL_SHA256


def test_semantic_owners_prove_direct_profile_and_global_exact5() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    assert bound["semantic_contract"] == {
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "B3_present": True,
        "sixth_task_present": False,
    }
    assert len(bound["semantic_owner_bindings"]) == 2
    assert len(bound["current_census_bindings"]) == 4
    assert all("mode" not in record for record in bound["semantic_owner_bindings"])


def test_current_census_boundary_is_read_only_2a2_baseline() -> None:
    boundary = subject.load_frozen_formal_decision_v1(ROOT)["current_census_boundary"]
    assert boundary == {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_event_count": 119,
        "completed_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
        "I12_current_status": "CURRENTLY_UNREVIEWED",
        "I12_event_count": 4,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
    }


@pytest.mark.parametrize(
    "payload",
    (
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'[]',
    ),
)
def test_strict_json_rejects_duplicate_nonfinite_and_nonobject(payload: bytes) -> None:
    with pytest.raises(subject.I12IngestionSafetyError):
        subject._strict_json_loads(payload, "TAMPER")


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("human_approval", "D1_task_relevance"), "NOT_RELEVANT"),
        (("human_approval", "D2_chemistry"), "NEGATIVE"),
        (("human_approval", "D3_reactive_pair"), "REJECT_OBSERVED_PAIR"),
        (("human_approval", "D4_role_partition"), "SELECT_CANDIDATE_1"),
        (("human_approval", "D5_training_use"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (("human_approval", "D6_scientific_context"), "drift"),
        (("selected_role_partition", "selected_candidate_index_0based"), 1),
        (("selected_role_partition", "warhead_role_atom_ids", 0), "C99"),
        (("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "C19"),
        (("selected_role_partition", "role_profile"), "STRICT_LINKER_PRESENT_V1"),
        (("canonical_Exact5_and_sample_applicability", "sample_applicable_task_ids"), [0, 4]),
        (("canonical_Exact5_and_sample_applicability", "sixth_task_present"), True),
        (("chemical_warhead_boundary", "chemical_warhead_human_authoritative"), True),
        (("chemical_warhead_boundary", "chemical_warhead_atom_ids"), ["C21"]),
        (("chemical_warhead_boundary", "reaction_family_authority_created"), True),
        (("reusable_authority_boundary", "reusable_chemistry_authority_created"), True),
        (("experimental_context_and_PRE_boundary", "PRE_topology_authority_created"), True),
        (("experimental_context_and_PRE_boundary", "PRE_mapping_repair_performed"), True),
        (("experimental_context_and_PRE_boundary", "POST_to_PRE_copy_performed"), True),
        (("POST_evidence_boundary", "POST_geometry_training_authority_created"), True),
        (("training_use_human_decision", "formal_training_admitted"), True),
        (("training_use_human_decision", "training_admission_created"), True),
    ),
)
def test_formal_semantic_drift_fails_closed(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.I12IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_formal_exact4_candidate0_and_authority_boundary_are_exact() -> None:
    formal = _formal()
    subject._validate_formal_document(formal)
    assert formal["identity"]["canonical_event_ids"] == list(subject.EXPECTED_EVENT_IDS)
    assert formal["identity"]["scaleup_ranks"] == [187, 188, 222, 223]
    role = formal["selected_role_partition"]
    assert role["warhead_role_atom_ids"] == list(subject.WARHEAD_ROLE)
    assert role["linker_atom_ids"] == []
    assert role["scaffold_atom_ids"] == list(subject.SCAFFOLD_ROLE)
    assert role["independent_structural_validation"] == {
        "Exact44_count": 44,
        "L_connected_or_empty": True,
        "L_count": 0,
        "S_connected": True,
        "S_count": 37,
        "W_connected": True,
        "W_count": 7,
        "direct_boundary_exists": True,
        "exhaustive": True,
        "extra_atom_ids": [],
        "missing_atom_ids": [],
        "pairwise_disjoint": True,
        "reactive_C21_in_W": True,
    }


def test_formal_decision_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT.parent / subject.FORMAL_DECISION_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=tampered)


def test_formal_validator_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT.parent / subject.FORMAL_VALIDATOR_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, formal_validator_path=tampered)


@pytest.mark.parametrize("relative", (subject.FORMAL_DECISION_RELATIVE, subject.FORMAL_VALIDATOR_RELATIVE))
def test_formal_exact2_symlink_is_rejected(tmp_path: Path, relative: Path) -> None:
    source = ROOT.parent / relative
    symlink = tmp_path / source.name
    symlink.symlink_to(source)
    kwargs = (
        {"formal_decision_path": symlink}
        if relative == subject.FORMAL_DECISION_RELATIVE
        else {"formal_validator_path": symlink}
    )
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **kwargs)


@pytest.mark.parametrize("relative", (subject.FORMAL_DECISION_RELATIVE, subject.FORMAL_VALIDATOR_RELATIVE))
def test_formal_exact2_executable_class_drift_is_rejected(
    tmp_path: Path, relative: Path
) -> None:
    source = ROOT.parent / relative
    replacement = tmp_path / source.name
    replacement.write_bytes(source.read_bytes())
    replacement.chmod(replacement.stat().st_mode | stat.S_IXUSR)
    kwargs = (
        {"formal_decision_path": replacement}
        if relative == subject.FORMAL_DECISION_RELATIVE
        else {"formal_validator_path": replacement}
    )
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **kwargs)


def test_semantic_owner_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT / subject.DIRECT_RUNTIME_OWNER_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(
            ROOT,
            repository_path_overrides={subject.DIRECT_RUNTIME_OWNER_RELATIVE: tampered},
        )


def test_build_is_byte_deterministic_and_projection_is_exact() -> None:
    first = subject.build_artifacts_v1(ROOT)
    second = subject.build_artifacts_v1(ROOT)
    assert first == second
    assert tuple(first) == subject.OUTPUT_FILENAMES
    subject.validate_completed_decision_projection_v1(first, repo_root=ROOT)


def test_snapshot_exact4_candidate0_direct_include_and_nonauthority() -> None:
    snapshot = json.loads(subject.build_artifacts_v1(ROOT)[subject.SNAPSHOT])
    assert [row["canonical_event_id"] for row in snapshot["events"]] == list(subject.EXPECTED_EVENT_IDS)
    assert [row["POST_distance_angstrom"] for row in snapshot["events"]] == [
        1.810632, 1.803620, 1.810317, 1.821774,
    ]
    role = snapshot["selected_role_partition"]
    assert role["selected_role_candidate_index_0based"] == 0
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert (role["warhead_atom_count"], role["linker_atom_count"], role["scaffold_atom_count"]) == (7, 0, 37)
    assert role["boundary_bonds"] == [
        {
            "atom_id_1": "C20",
            "atom_id_2": "C21",
            "bond_order": "SING",
            "boundary_between_roles": ["scaffold", "warhead"],
        }
    ]
    assert role["chemical_warhead_human_authoritative"] is False
    assert role["chemical_warhead_atom_ids"] is None
    assert snapshot["canonical_task_contract"]["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert snapshot["training_boundary"]["candidate_for_future_training_admission"] is True
    assert snapshot["training_boundary"]["future_training_candidate_is_training_admission"] is False
    assert snapshot["training_boundary"]["training_admitted"] is False


def test_matrix_exact4_fields_and_task_applicability_are_exact() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    assert len(rows) == 4
    assert [row["POST_distance_angstrom"] for row in rows] == [
        "1.810632", "1.803620", "1.810317", "1.821774",
    ]
    for row in rows:
        assert row["protein_reactive_atom"] == "SG"
        assert row["ligand_reactive_atom"] == "C21"
        assert row["selected_role_candidate_index_0based"] == "0"
        assert json.loads(row["warhead_atoms_json"]) == list(subject.WARHEAD_ROLE)
        assert json.loads(row["linker_atoms_json"]) == []
        assert json.loads(row["scaffold_atoms_json"]) == list(subject.SCAFFOLD_ROLE)
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["formal_event_training_use_decision"] == "INCLUDE"
        assert row["training_use_include"] == "true"
        assert row["candidate_for_future_training_admission"] == "true"
        assert row["training_admitted"] == "false"
        assert row["chemical_warhead_human_authoritative"] == "false"
        assert json.loads(row["chemical_warhead_atoms_json"]) is None
        assert row["PRE_status"] == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        assert row["PRE_topology_authority_available"] == "false"
        assert row["POST_geometry_training_authority_available"] == "false"
        assert row["authority_created_by_this_ingestion"] == "false"


def test_summary_exact_counts_and_training_boundary() -> None:
    summary = json.loads(subject.build_artifacts_v1(ROOT)[subject.SUMMARY])
    assert summary["event_count"] == 4
    assert summary["D1_RELEVANT_count"] == 4
    assert summary["D2_POSITIVE_count"] == 4
    assert summary["D3_CONFIRMED_count"] == 4
    assert summary["DIRECT_event_count"] == 4
    assert [
        summary["applicable_warhead_only_count"],
        summary["applicable_linker_plus_warhead_count"],
        summary["applicable_scaffold_plus_warhead_count"],
        summary["applicable_scaffold_only_count"],
        summary["applicable_scaffold_plus_linker_plus_warhead_count"],
    ] == [4, 0, 0, 4, 4]
    assert summary["D5_INCLUDE_count"] == 4
    assert summary["future_training_admission_candidate_count"] == 4
    assert summary["training_admitted_count"] == 0
    assert summary["chemical_warhead_human_authority_count"] == 0
    assert summary["ready_for_training"] is False


@pytest.mark.parametrize(
    ("name", "path", "value"),
    (
        (subject.SNAPSHOT, ("chemical_authority_boundary", "chemical_warhead_human_authoritative"), True),
        (subject.SNAPSHOT, ("chemical_authority_boundary", "chemical_warhead_atom_ids"), ["C21"]),
        (subject.SNAPSHOT, ("reusable_authority_boundary", "reaction_family_authority"), True),
        (subject.SNAPSHOT, ("reusable_authority_boundary", "reusable_chemistry_authority"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "PRE_topology_authority_available"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "PRE_reconstruction_performed"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "POST_to_PRE_copy_performed"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "POST_geometry_training_authority_available"), True),
        (subject.SNAPSHOT, ("training_boundary", "training_admitted"), True),
        (subject.SNAPSHOT, ("training_boundary", "training_admission_created"), True),
        (subject.SNAPSHOT, ("training_boundary", "future_training_candidate_is_training_admission"), True),
        (subject.SNAPSHOT, ("authority_boundary", "authority_created_by_this_ingestion"), True),
        (subject.SUMMARY, ("event_count",), 5),
        (subject.MANIFEST, ("ready_for_training",), True),
    ),
)
def test_projection_authority_tamper_fails_closed(
    name: str, path: tuple[object, ...], value: object
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    tampered = _mutated_json_artifact(artifacts, name, path, value)
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("selected_role_candidate_index_0based", "1"),
        ("warhead_atoms_json", '["C22"]'),
        ("boundary_bonds_json", "[]"),
        ("role_profile", "STRICT_LINKER_PRESENT_V1"),
        ("direct_profile_applicable_task_ids_json", "[0,4]"),
        ("chemical_warhead_human_authoritative", "true"),
        ("chemical_warhead_atoms_json", '["C21"]'),
        ("PRE_topology_authority_available", "true"),
        ("POST_geometry_training_authority_available", "true"),
        ("training_admitted", "true"),
        ("future_training_candidate_is_training_admission", "true"),
        ("authority_created_by_this_ingestion", "true"),
    ),
)
def test_matrix_row_tamper_fails_closed(field: str, value: str) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    tampered = _mutated_matrix_artifact(artifacts, 0, field, value)
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_matrix_row_count_drift_fails_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    tampered = dict(artifacts)
    tampered[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows[:-1])
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_output_artifact_count_drift_fails_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    artifacts.pop(subject.SUMMARY)
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


@pytest.mark.parametrize(
    "forbidden_field",
    ("mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode"),
)
def test_numeric_posix_semantic_identity_field_is_rejected(forbidden_field: str) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["formal_decision_binding"][forbidden_field] = "0644"
    tampered = dict(artifacts)
    tampered[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.I12IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_manifest_binds_outputs_without_self_sha() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert subject.MANIFEST not in manifest["output_artifact_bindings"]
    for name in (subject.SNAPSHOT, subject.MATRIX, subject.SUMMARY):
        binding = manifest["output_artifact_bindings"][name]
        assert binding["byte_count"] == len(artifacts[name])
        assert binding["SHA256"] == subject._sha256(artifacts[name])
        assert binding["expected_executable_class"] == "NON_EXECUTABLE"
    assert manifest["numeric_POSIX_semantic_identity"] is False


def test_materialization_writes_exact4_only_and_is_deterministic(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = subject.materialize_artifacts_v1(ROOT, output_root=first_root)
    second = subject.materialize_artifacts_v1(ROOT, output_root=second_root)
    assert first == second
    assert {path.name for path in first_root.iterdir()} == set(subject.OUTPUT_FILENAMES)
    assert {path.name for path in second_root.iterdir()} == set(subject.OUTPUT_FILENAMES)
    for name in subject.OUTPUT_FILENAMES:
        assert (first_root / name).read_bytes() == first[name]
        assert (second_root / name).read_bytes() == second[name]


def test_materialization_rejects_unexpected_entry_before_write(
    tmp_path: Path,
) -> None:
    contaminated = tmp_path / "contaminated"
    contaminated.mkdir()
    sentinel = contaminated / "unexpected.txt"
    sentinel_payload = b"known sentinel bytes\n"
    sentinel.write_bytes(sentinel_payload)

    with pytest.raises(
        subject.I12IngestionSafetyError,
        match="OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES",
    ):
        subject.materialize_artifacts_v1(ROOT, output_root=contaminated)

    assert sentinel.read_bytes() == sentinel_payload
    assert {path.name for path in contaminated.iterdir()} == {sentinel.name}
    assert all(
        not (contaminated / name).exists() for name in subject.OUTPUT_FILENAMES
    )


def test_materialization_rejects_destination_symlink_before_write(
    tmp_path: Path,
) -> None:
    real_target = tmp_path / "real_target"
    real_target.mkdir()
    destination_symlink = tmp_path / "destination_symlink"
    try:
        destination_symlink.symlink_to(real_target, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"platform cannot create directory symlink: {error}")

    with pytest.raises(
        subject.I12IngestionSafetyError,
        match="OUTPUT_ROOT_SYMLINK_FORBIDDEN",
    ):
        subject.materialize_artifacts_v1(ROOT, output_root=destination_symlink)

    assert tuple(real_target.iterdir()) == ()


def test_existing_valid_exact4_rematerialization_is_idempotent(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "existing_exact4"
    first = subject.materialize_artifacts_v1(ROOT, output_root=output_root)
    before = {
        name: (output_root / name).read_bytes() for name in subject.OUTPUT_FILENAMES
    }

    second = subject.materialize_artifacts_v1(ROOT, output_root=output_root)
    after = {
        name: (output_root / name).read_bytes() for name in subject.OUTPUT_FILENAMES
    }

    assert first == second
    assert before == after == first
    assert {path.name for path in output_root.iterdir()} == set(
        subject.OUTPUT_FILENAMES
    )


def test_materialized_repository_outputs_match_fresh_build() -> None:
    report = subject.check_materialized_v1(ROOT)
    assert report == {
        "status": "PASS",
        "schema_version": subject.SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "deterministic": True,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "ready_for_training": False,
    }


def test_production_owner_never_imports_or_executes_formal_validator() -> None:
    source = (ROOT / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {"subprocess", "runpy", "importlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.split(".")[0] in forbidden_import_roots for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"exec", "eval", "compile", "__import__"}
    assert "execute_formal_validator" not in source
    assert "_run_formal_validator" not in source
    assert "BASELINE_COMMIT" not in source
    assert "git rev-parse" not in source
    assert "git status" not in source


def test_no_dynamic_metadata_or_absolute_host_paths() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    for name in (subject.SNAPSHOT, subject.SUMMARY, subject.MANIFEST):
        text = artifacts[name].decode("utf-8")
        assert '"created_at"' not in text
        assert '"generated_at"' not in text
        assert '"validated_at"' not in text
        assert "/cpfs" not in text
        assert "/tmp/" not in text
