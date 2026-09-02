from __future__ import annotations

import ast
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import stat

import pytest

from covalent_ext import (
    covapie_cer_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / subject.CHECKER_RELATIVE
CHECKER_SPEC = importlib.util.spec_from_file_location("cer_ingestion_checker", CHECKER_PATH)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _formal() -> dict[str, object]:
    return copy.deepcopy(subject.load_frozen_formal_decision_v1(ROOT)["formal"])


def _set_path(document: object, path: tuple[object, ...], value: object) -> None:
    current = document
    for key in path[:-1]:
        current = current[key]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]


def _mutated_formal(
    path: tuple[object, ...], value: object, *, refresh_digest: bool = True
) -> dict[str, object]:
    document = _formal()
    _set_path(document, path, value)
    if refresh_digest:
        clone = copy.deepcopy(document)
        clone.pop("formal_semantic_canonical_sha256", None)
        document["formal_semantic_canonical_sha256"] = subject._sha256(
            subject._canonical_json(clone)
        )
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


def _expected_paths() -> tuple[str, ...]:
    return tuple(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)


def test_public_api_is_exact() -> None:
    assert subject.__all__ == (
        "CERIngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_schema_versions_and_exact7_inventory_are_exact() -> None:
    assert subject.SCHEMA_VERSION == (
        "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1"
    )
    assert subject.SNAPSHOT_SCHEMA_VERSION == "covapie_cer_completed_human_decision_snapshot_v1"
    assert subject.MATRIX_SCHEMA_VERSION == "covapie_cer_event_task_label_availability_v1"
    assert subject.SUMMARY_SCHEMA_VERSION == "covapie_cer_completed_decision_ingestion_summary_v1"
    assert subject.MANIFEST_SCHEMA_VERSION == "covapie_cer_completed_decision_ingestion_manifest_v1"
    assert len(subject.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(subject.CANDIDATE_PUBLICATION_PATHS)) == 7


def test_frozen_formal_exact2_and_semantic_digest_are_bound() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    assert bound["formal_decision_binding"] == {
        "path": subject.FORMAL_DECISION_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 26123,
        "SHA256": "380d54ba35cf8eff1760d540e0874c8a7e920dac9473a002dac156812164fb2c",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "CER_FROZEN_FORMAL_HUMAN_DECISION",
    }
    assert bound["formal_validator_binding"] == {
        "path": subject.FORMAL_VALIDATOR_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 72368,
        "SHA256": "db4236586eb97bfd6d9486056f955d545de5d552f814a2c91a61596813d2da5a",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "CER_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
    }
    formal = bound["formal"]
    assert formal["formal_semantic_canonical_sha256"] == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert subject._semantic_digest(formal) == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert bound["formal_semantics_independently_validated"] is True


def test_human_authorization_and_revised_d6_provenance_are_exact() -> None:
    formal = _formal()
    human = formal["human_authorization"]
    assert human["human_authorization_origin"] == "EXTERNAL_HUMAN_CHAT_AUTHORIZATION"
    assert human["reviewer_id"] == human["attestor_id"] == "fmx"
    assert human["human_choices_externally_authorized"] is True
    assert human["machine_approval_claimed"] is False
    context = formal["human_approved_context"]
    assert context["D6_draft_origin"] == "ASSISTANT_DRAFT_ACCEPTED_BY_HUMAN"
    assert context["D6_human_reviewed_and_accepted"] is True
    assert context["D6_human_authorized"] is True
    assert context["D6_human_authored"] is False
    assert context["formal_decision_authority_is_human"] is True
    assert context["machine_scientific_authority_created"] is False
    assert context["assistant_draft_does_not_create_authority"] is True
    assert context["human_authorization_remains_authority_source"] is True
    assert len(context["D6_scientific_context"].encode("utf-8")) == 325
    assert subject._sha256(context["D6_scientific_context"].encode("utf-8")) == (
        "bb7720e708c13833dcd0bd5f55135130a21269e077f4ef386b7bb86e3b272242"
    )


@pytest.mark.parametrize(
    "payload",
    (
        b'\xef\xbb\xbf{"x":1}',
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'[]',
    ),
)
def test_strict_json_rejects_bom_duplicate_nonfinite_and_nonobject(payload: bytes) -> None:
    with pytest.raises(subject.CERIngestionSafetyError):
        subject._strict_json_loads(payload, "TAMPER")


@pytest.mark.parametrize("field", ("human_authored_free_text", "machine_generated_token"))
def test_old_ambiguous_provenance_fields_fail_closed(field: str) -> None:
    formal = _formal()
    formal["human_approved_context"][field] = "forbidden"
    with pytest.raises(subject.CERIngestionSafetyError, match="AMBIGUOUS_PROVENANCE_FIELD"):
        subject._validate_formal_document(formal)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("human_authorization", "D1_task_relevance"), "NOT_RELEVANT"),
        (("human_authorization", "D2_chemistry"), "NEGATIVE"),
        (("human_authorization", "D3_reactive_pair"), "REJECT_OBSERVED_PAIR"),
        (("human_authorization", "D4_role_candidate"), "SELECT_CANDIDATE_2"),
        (("human_authorization", "D5_training_use"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (("human_approved_context", "D6_human_authored"), True),
        (("identity", "scaleup_ranks"), [52, 53, 54]),
        (("event_level_human_decisions", 0, "canonical_event_id"), "wrong"),
        (("selected_role_partition", "selected_candidate_index_0based"), 2),
        (("selected_role_partition", "warhead_role_atom_ids", 0), "C99"),
        (("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "C3"),
        (("selected_role_partition", "role_profile"), "STRICT_LINKER_PRESENT_V1"),
        (("canonical_Exact5_and_sample_applicability", "sample_applicable_task_ids"), [0, 4]),
        (("canonical_Exact5_and_sample_applicability", "B3_present"), False),
        (("canonical_Exact5_and_sample_applicability", "sixth_task_present"), True),
        (("reactive_pair_authority", "cross_structure_regiochemistry_generalization"), True),
        (("reactive_pair_authority", "reusable_pair_rule_created"), True),
        (("chemistry_authority_boundary", "reusable_chemistry_authority_created"), True),
        (("selected_role_partition", "reusable_role_rule_created"), True),
        (("PRE_POST_boundary", "PRE_topology_authority"), True),
        (("PRE_POST_boundary", "POST_to_PRE_copy_performed"), True),
        (("POST_evidence_boundary", "POST_geometry_training_authority"), True),
        (("training_use_boundary", "formal_training_admitted"), True),
        (("training_use_boundary", "training_materialization_allowed"), True),
    ),
)
def test_independent_formal_semantic_validation_rejects_mutation_even_with_new_digest(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.CERIngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_formal_exact4_pair_candidate3_and_direct_role_are_exact() -> None:
    formal = _formal()
    subject._validate_formal_document(formal)
    assert formal["identity"]["canonical_event_ids"] == list(subject.EXPECTED_EVENT_IDS)
    assert formal["identity"]["scaleup_ranks"] == [52, 53, 54, 55]
    assert len(set(formal["identity"]["canonical_event_ids"])) == 4
    assert formal["reactive_pair_authority"]["pair_scope"] == subject.AUTHORITY_SCOPE
    role = formal["selected_role_partition"]
    assert role["D4_human_choice"] == "SELECT_CANDIDATE_3"
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_role_atom_ids"] == list(subject.WARHEAD_ROLE)
    assert role["linker_atom_ids"] == []
    assert role["scaffold_atom_ids"] == list(subject.SCAFFOLD_ROLE)
    assert role["W_L_S_counts"] == [8, 0, 8]
    assert role["boundary_bonds"] == [
        {
            "aromatic_flag": "N", "atom_id_1": "C4", "atom_id_2": "C5",
            "bond_order": "SING", "role_1": "W", "role_2": "S",
        }
    ]


def test_formal_exact5_b3_no_sixth_and_sample_applicability_are_exact() -> None:
    tasks = _formal()["canonical_Exact5_and_sample_applicability"]
    assert [row["task_id"] for row in tasks["global_canonical_Exact5"]] == [0, 1, 2, 3, 4]
    assert [row["semantic_name"] for row in tasks["global_canonical_Exact5"]] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_present"] is False
    assert tasks["sample_applicable_task_ids"] == [0, 3, 4]
    assert tasks["authoritative_task_labels_created"] is False
    assert tasks["event_task_label_rows_materialized"] is False


def test_current_census_boundary_is_read_only_with_1n0_baseline() -> None:
    boundary = subject.load_frozen_formal_decision_v1(ROOT)["current_census_boundary"]
    assert boundary == {
        "completed_positive_event_count": 99,
        "completed_positive_unit_count": 14,
        "completed_event_count": 127,
        "completed_unit_count": 19,
        "unreviewed_event_count": 211,
        "unreviewed_unit_count": 112,
        "CER_current_status": "CURRENTLY_UNREVIEWED",
        "CER_human_review_completed": False,
        "CER_event_count": 4,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
    }


def test_current_census_selection_uses_frozen_event_identity_not_ligand_shortcut() -> None:
    source = (ROOT / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    assert 'row.get("canonical_event_id") in expected_set' in source
    assert 'row.get("ligand_component_id") == "CER"' not in source


def test_formal_decision_and_validator_byte_drift_are_rejected(tmp_path: Path) -> None:
    for relative, argument in (
        (subject.FORMAL_DECISION_RELATIVE, "formal_decision_path"),
        (subject.FORMAL_VALIDATOR_RELATIVE, "formal_validator_path"),
    ):
        source = ROOT.parent / relative
        tampered = tmp_path / source.name
        tampered.write_bytes(source.read_bytes() + b"\n")
        with pytest.raises(subject.CERIngestionSafetyError):
            subject.load_frozen_formal_decision_v1(ROOT, **{argument: tampered})


@pytest.mark.parametrize(
    "relative", (subject.FORMAL_DECISION_RELATIVE, subject.FORMAL_VALIDATOR_RELATIVE)
)
def test_formal_exact2_symlink_and_executable_class_drift_fail_closed(
    tmp_path: Path, relative: Path
) -> None:
    source = ROOT.parent / relative
    argument = (
        "formal_decision_path"
        if relative == subject.FORMAL_DECISION_RELATIVE
        else "formal_validator_path"
    )
    symlink = tmp_path / ("link-" + source.name)
    symlink.symlink_to(source)
    with pytest.raises(subject.CERIngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **{argument: symlink})
    replacement = tmp_path / ("exec-" + source.name)
    replacement.write_bytes(source.read_bytes())
    replacement.chmod(replacement.stat().st_mode | stat.S_IXUSR)
    with pytest.raises(subject.CERIngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **{argument: replacement})


def test_semantic_owner_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT / subject.DIRECT_RUNTIME_OWNER_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.CERIngestionSafetyError):
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


def test_snapshot_exact4_authority_provenance_and_boundaries() -> None:
    snapshot = json.loads(subject.build_artifacts_v1(ROOT)[subject.SNAPSHOT])
    assert snapshot["schema_version"] == subject.SNAPSHOT_SCHEMA_VERSION
    assert snapshot["review_unit_id"] == subject.EXPECTED_REVIEW_UNIT_ID
    assert snapshot["formal_semantic_canonical_sha256"] == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert [row["canonical_event_id"] for row in snapshot["events"]] == list(subject.EXPECTED_EVENT_IDS)
    assert [row["scaleup_rank"] for row in snapshot["events"]] == [52, 53, 54, 55]
    assert snapshot["reactive_pair_authority"] == subject._pair_authority_boundary()
    assert snapshot["selected_role_partition"] == subject._role_projection()
    assert snapshot["canonical_task_contract"]["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert snapshot["canonical_task_contract"]["authoritative_task_labels_created"] is False
    assert snapshot["geometry_boundary"]["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert snapshot["geometry_boundary"]["POST_geometry_training_authority"] is False
    assert snapshot["training_boundary"]["future_training_admission_candidate"] is True
    assert snapshot["training_boundary"]["formal_training_admitted"] is False
    assert snapshot["authority_boundary"]["new_human_authority_created_by_ingestion"] is False


def test_matrix_exact4_fields_and_task_availability_are_exact() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    assert len(rows) == 4
    assert [row["POST_distance_angstrom"] for row in rows] == [
        "1.902635", "1.889924", "1.860698", "1.899047",
    ]
    for row in rows:
        assert row["review_unit_id"] == subject.EXPECTED_REVIEW_UNIT_ID
        assert row["human_review_completed"] == "true"
        assert row["human_task_relevance_decision"] == "RELEVANT"
        assert row["human_chemistry_decision"] == "POSITIVE"
        assert row["protein_reactive_atom"] == "SG"
        assert row["ligand_reactive_atom"] == "C2"
        assert row["selected_role_candidate_index_0based"] == "3"
        assert json.loads(row["warhead_atoms_json"]) == list(subject.WARHEAD_ROLE)
        assert json.loads(row["linker_atoms_json"]) == []
        assert json.loads(row["scaffold_atoms_json"]) == list(subject.SCAFFOLD_ROLE)
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["task_applicability_determined"] == "true"
        assert row["authoritative_task_labels_created"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
        assert row["human_training_use_disposition"] == "INCLUDE"
        assert row["formal_training_admitted"] == "false"
        assert row["PRE_status"] == "PRE_REACTION_UNRESOLVED"
        assert row["POST_geometry_training_authority"] == "false"


def test_summary_exact_counts_and_operation_boundary() -> None:
    summary = json.loads(subject.build_artifacts_v1(ROOT)[subject.SUMMARY])
    assert [summary[key] for key in (
        "event_count", "human_review_completed_count", "task_relevant_count",
        "chemistry_positive_count", "reactive_pair_human_authoritative_count",
        "role_partition_human_authoritative_count", "DIRECT_event_count",
    )] == [4, 4, 4, 4, 4, 4, 4]
    assert summary["STRICT_event_count"] == 0
    assert summary["training_use_INCLUDE_count"] == 4
    assert summary["applicable_task_set_counts"] == {"[0,3,4]": 4}
    assert summary["PRE_topology_authority_count"] == 0
    assert summary["POST_geometry_training_authority_count"] == 0
    assert summary["formal_training_admitted_count"] == 0
    assert summary["reusable_chemistry_authority_count"] == 0
    assert summary["reusable_pair_authority_count"] == 0
    assert summary["reusable_role_authority_count"] == 0
    assert summary["INGESTION_COMPLETE"] is True
    assert summary["RECONCILIATION"] is False
    assert summary["CENSUS_REFRESH"] is False
    assert summary["QUEUE_REFRESH"] is False
    assert summary["READY_FOR_TRAINING"] is False


@pytest.mark.parametrize(
    ("name", "path", "value"),
    (
        (subject.SNAPSHOT, ("D6_provenance", "D6_human_authored"), True),
        (subject.SNAPSHOT, ("reactive_pair_authority", "reusable_pair_rule_created"), True),
        (subject.SNAPSHOT, ("selected_role_partition", "reusable"), True),
        (subject.SNAPSHOT, ("canonical_task_contract", "B3_present"), False),
        (subject.SNAPSHOT, ("canonical_task_contract", "authoritative_task_labels_created"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "PRE_topology_authority"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "POST_geometry_training_authority"), True),
        (subject.SNAPSHOT, ("training_boundary", "formal_training_admitted"), True),
        (subject.SNAPSHOT, ("training_boundary", "training_materialization_allowed"), True),
        (subject.SNAPSHOT, ("authority_boundary", "new_human_authority_created_by_ingestion"), True),
        (subject.SUMMARY, ("event_count",), 5),
        (subject.MANIFEST, ("frozen_formal_validator_executed",), True),
        (subject.MANIFEST, ("READY_FOR_TRAINING",), True),
    ),
)
def test_projection_authority_tamper_fails_closed(
    name: str, path: tuple[object, ...], value: object
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    with pytest.raises(subject.CERIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(
            _mutated_json_artifact(artifacts, name, path, value)
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_event_id", "wrong"),
        ("selected_role_candidate_index_0based", "2"),
        ("warhead_atoms_json", '["C2"]'),
        ("boundary_bonds_json", "[]"),
        ("role_profile", "STRICT_LINKER_PRESENT_V1"),
        ("direct_profile_applicable_task_ids_json", "[0,4]"),
        ("authoritative_task_labels_created", "true"),
        ("event_task_label_rows_materialized", "true"),
        ("cross_structure_regiochemistry_generalization", "true"),
        ("reusable_pair_rule_created", "true"),
        ("reusable_role_authority", "true"),
        ("PRE_topology_authority", "true"),
        ("POST_geometry_training_authority", "true"),
        ("formal_training_admitted", "true"),
        ("training_materialization_allowed", "true"),
        ("new_human_authority_created_by_ingestion", "true"),
    ),
)
def test_matrix_row_tamper_fails_closed(field: str, value: str) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    with pytest.raises(subject.CERIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(
            _mutated_matrix_artifact(artifacts, 0, field, value)
        )


def test_matrix_row_count_and_output_inventory_drift_fail_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    row_drift = dict(artifacts)
    row_drift[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows[:-1])
    with pytest.raises(subject.CERIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(row_drift)
    inventory_drift = dict(artifacts)
    inventory_drift.pop(subject.SUMMARY)
    with pytest.raises(subject.CERIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(inventory_drift)


@pytest.mark.parametrize(
    "forbidden_field", ("mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode")
)
def test_b4_exact_posix_semantic_identity_field_is_rejected(forbidden_field: str) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["formal_decision_binding"][forbidden_field] = "0644"
    tampered = dict(artifacts)
    tampered[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.CERIngestionSafetyError, match="NUMERIC_POSIX"):
        subject.validate_completed_decision_projection_v1(tampered)


def test_manifest_closes_sources_outputs_and_boundaries_without_self_sha() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["candidate_publication_paths"] == list(_expected_paths())
    assert manifest["formal_semantics_independently_validated"] is True
    assert manifest["frozen_formal_validator_provenance_identity_only"] is True
    assert manifest["frozen_formal_validator_imported"] is False
    assert manifest["frozen_formal_validator_executed"] is False
    assert manifest["new_human_authority_created_by_ingestion"] is False
    assert manifest["projection_of_frozen_formal_human_authority"] is True
    assert manifest["MANIFEST_SELF_SHA256_PROHIBITED"] is True
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert subject.MANIFEST not in manifest["output_artifact_bindings"]
    for name in (subject.SNAPSHOT, subject.MATRIX, subject.SUMMARY):
        binding = manifest["output_artifact_bindings"][name]
        assert binding["byte_count"] == len(artifacts[name])
        assert binding["SHA256"] == subject._sha256(artifacts[name])
        assert binding["expected_executable_class"] == "NON_EXECUTABLE"


def test_materialization_exact4_double_run_and_contamination_fail_closed(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = subject.materialize_artifacts_v1(ROOT, output_root=first_root)
    second = subject.materialize_artifacts_v1(ROOT, output_root=second_root)
    assert first == second
    assert {path.name for path in first_root.iterdir()} == set(subject.OUTPUT_FILENAMES)
    assert {path.name for path in second_root.iterdir()} == set(subject.OUTPUT_FILENAMES)
    subject.materialize_artifacts_v1(ROOT, output_root=first_root)
    contaminated = tmp_path / "contaminated"
    contaminated.mkdir()
    sentinel = contaminated / "unexpected.txt"
    sentinel.write_bytes(b"sentinel\n")
    with pytest.raises(
        subject.CERIngestionSafetyError,
        match="OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES",
    ):
        subject.materialize_artifacts_v1(ROOT, output_root=contaminated)
    assert sentinel.read_bytes() == b"sentinel\n"


def test_materialization_destination_symlink_fails_before_write(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"platform cannot create directory symlink: {error}")
    with pytest.raises(subject.CERIngestionSafetyError, match="OUTPUT_ROOT_SYMLINK_FORBIDDEN"):
        subject.materialize_artifacts_v1(ROOT, output_root=link)
    assert tuple(target.iterdir()) == ()


def test_materialized_repository_outputs_match_fresh_build() -> None:
    assert subject.check_materialized_v1(ROOT) == {
        "status": "PASS",
        "schema_version": subject.SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "deterministic": True,
        "CER_COMPLETED_DECISION_INGESTED": True,
        "new_human_authority_created_by_ingestion": False,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
    }


def test_production_owner_never_imports_or_executes_frozen_validator() -> None:
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
    assert "subprocess_formal_validator" not in source
    assert "git rev-parse" not in source
    assert "git status" not in source


def _validate_tracked_relation(**overrides: object) -> None:
    expected_set = set(_expected_paths())
    facts: dict[str, object] = {
        "profile": checker.TRACKED_CLEAN,
        "expected_paths": expected_set,
        "head": "synthetic-cer-local-commit",
        "origin_main": checker.BASELINE_HEAD,
        "ahead": 1,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": expected_set,
    }
    facts.update(overrides)
    checker.validate_repository_relation_values(**facts)  # type: ignore[arg-type]


def test_candidate_profile_passes_strictly() -> None:
    expected = _expected_paths()
    expected_set = set(expected)
    assert checker.classify_repository_profile(
        expected_paths=expected,
        tracked_paths=set(),
        ordinary_untracked=expected_set,
        status_lines=tuple("?? " + path for path in expected),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=expected,
        tracked_paths=expected_set,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN
    checker.validate_repository_relation_values(
        profile=checker.CANDIDATE_UNTRACKED,
        expected_paths=expected_set,
        head=checker.BASELINE_HEAD,
        origin_main=checker.BASELINE_HEAD,
        ahead=0,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=set(),
    )


def test_tracked_clean_immediate_unpushed_and_pushed_pass() -> None:
    _validate_tracked_relation()
    _validate_tracked_relation(
        head="synthetic-immediate-publication",
        origin_main="synthetic-immediate-publication",
        ahead=0,
    )


def test_tracked_clean_allows_multiple_unpushed_commits() -> None:
    _validate_tracked_relation(
        head="synthetic-third-descendant",
        ahead=3,
    )


def test_tracked_clean_allows_unrelated_future_successor_paths() -> None:
    expected_set = set(_expected_paths())
    future_successor_paths = {
        "src/covalent_ext/synthetic_future_reconciliation_v1.py",
        "data/derived/covalent_small/synthetic_future_census_v1.json",
    }
    _validate_tracked_relation(
        head="synthetic-future-successor-descendant",
        ahead=5,
        changed_since_baseline=expected_set | future_successor_paths,
    )


def test_tracked_clean_allows_unpushed_successor_after_prior_publication() -> None:
    expected_set = set(_expected_paths())
    future_reconciliation_paths = {
        "src/covalent_ext/synthetic_future_reconciliation_v1.py",
        "data/derived/covalent_small/synthetic_future_reconciliation_v1.json",
    }
    _validate_tracked_relation(
        head="synthetic-reconciliation-local-descendant",
        origin_main="synthetic-cer-published-descendant",
        ahead=1,
        changed_since_baseline=expected_set | future_reconciliation_paths,
    )


def test_tracked_clean_missing_one_exact7_path_fails_with_successor_paths() -> None:
    expected = _expected_paths()
    expected_set = set(expected)
    future_successor_paths = {
        "src/covalent_ext/synthetic_future_reconciliation_v1.py",
        "data/derived/covalent_small/synthetic_future_census_v1.json",
    }
    with pytest.raises(SystemExit, match="TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID"):
        _validate_tracked_relation(
            head="synthetic-incomplete-publication-descendant",
            ahead=4,
            changed_since_baseline=(expected_set - {expected[0]}) | future_successor_paths,
        )


@pytest.mark.parametrize(
    "overrides",
    (
        {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False},
        {"behind": 1},
    ),
)
def test_tracked_clean_invalid_ancestry_and_behind_remote_fail_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(SystemExit, match="TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID"):
        _validate_tracked_relation(**overrides)


def test_mixed_lifecycle_fails_closed() -> None:
    expected = _expected_paths()
    with pytest.raises(SystemExit, match="MIXED_TRACKING_STATE"):
        checker.classify_repository_profile(
            expected_paths=expected,
            tracked_paths={expected[0]},
            ordinary_untracked=set(expected[1:]),
            status_lines=tuple("?? " + path for path in expected[1:]),
            working_diff=set(),
            cached_diff=set(),
        )


def test_tracked_clean_dirty_worktree_staged_and_untracked_fail_closed() -> None:
    expected = _expected_paths()
    expected_set = set(expected)
    cases = (
        (set(), (), {expected[0]}, set(), "TRACKED_WORKTREE_MODIFICATION_PRESENT"),
        (set(), (), set(), {expected[0]}, "STAGED_INDEX_CHANGE_PRESENT"),
        ({"synthetic-unrelated.txt"}, ("?? synthetic-unrelated.txt",), set(), set(), "TRACKED_CLEAN_STATE_DIRTY"),
    )
    for ordinary_untracked, status_lines, working_diff, cached_diff, message in cases:
        with pytest.raises(SystemExit, match=message):
            checker.classify_repository_profile(
                expected_paths=expected,
                tracked_paths=expected_set,
                ordinary_untracked=ordinary_untracked,
                status_lines=status_lines,
                working_diff=working_diff,
                cached_diff=cached_diff,
            )


def test_no_dynamic_metadata_absolute_paths_or_forbidden_suffixes() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    for name in (subject.SNAPSHOT, subject.SUMMARY, subject.MANIFEST):
        text = artifacts[name].decode("utf-8")
        assert '"created_at"' not in text
        assert '"generated_at"' not in text
        assert '"validated_at"' not in text
        assert "/cpfs" not in text
        assert "/tmp/" not in text
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part", ".pyc", ".log"}
    assert not any(path.suffix.lower() in forbidden for path in subject.CANDIDATE_PUBLICATION_PATHS)
