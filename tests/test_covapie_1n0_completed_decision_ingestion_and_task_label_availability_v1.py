from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat

import pytest

from covalent_ext import (
    covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / subject.CHECKER_RELATIVE
SPEC = importlib.util.spec_from_file_location("check_1n0_ingestion_v1", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def _formal() -> dict[str, object]:
    return copy.deepcopy(subject.load_frozen_formal_decision_v1(ROOT)["formal"])


def _set_path(document: object, path: tuple[object, ...], value: object) -> None:
    current = document
    for key in path[:-1]:
        current = current[key]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]


def _refresh_semantic_digest(document: dict[str, object]) -> None:
    clone = copy.deepcopy(document)
    clone.pop("formal_semantic_canonical_sha256", None)
    document["formal_semantic_canonical_sha256"] = hashlib.sha256(
        subject._canonical_json(clone)
    ).hexdigest()


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


def test_public_api_is_exact6() -> None:
    assert subject.__all__ == (
        "OneN0IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_active_source_bindings_are_exact9_and_v2_clean() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    records = bound["active_source_bindings"]
    assert records == subject._binding_records(subject.ACTIVE_BINDINGS)
    assert len(records) == 9
    assert [record["path"] for record in records] == [
        binding[0].as_posix() for binding in subject.ACTIVE_BINDINGS
    ]
    for record in records:
        assert set(record) == {
            "path", "namespace", "byte_count", "SHA256",
            "expected_executable_class", "source_role",
        }
        assert record["expected_executable_class"] == "NON_EXECUTABLE"
        assert not ({"mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode"} & set(record))
    assert len(bound["semantic_owner_bindings"]) == 2
    assert len(bound["current_census_bindings"]) == 4


def test_active_binding_literals_match_audited_identities() -> None:
    assert [(item[2], item[3]) for item in subject.ACTIVE_BINDINGS] == [
        (26236, "45c337b2b8e0f85ea7a06eb16bd5f55ec729429285226a77bbb0c4a2f1301a34"),
        (53387, "3006362e511ae09beaab1e5c38d73e90961795b4bfcccb0740cb91b0b3a4c434"),
        (3704, "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"),
        (67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b"),
        (35925, "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548"),
        (71565, "42b01060024cf4c92e19bf3804c6440522019082ab6ec5fda89f5b7258e243b4"),
        (532022, "f659b6c9d9475c94aa4bf2234053627d28a58d4b7f6ae424f49a18924c1ac3bf"),
        (17549, "76d91f101898d8ba6c46de69be866e1408cbb9e630562906a52435a18e31d6b1"),
        (51041, "d22c388f7da5fecede11df15e3bc188196328e24009ad9363932bebc971da150"),
    ]


@pytest.mark.parametrize(
    "payload",
    (
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'[]',
        b'\xff',
    ),
)
def test_strict_json_rejects_duplicate_nonfinite_nonobject_and_nonutf8(
    payload: bytes,
) -> None:
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject._strict_json_loads(payload, "TAMPER")


def test_formal_semantic_digest_and_finalization_are_exact() -> None:
    formal = _formal()
    assert formal["formal_semantic_canonical_sha256"] == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert subject._semantic_digest(formal) == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert formal["schema_version"] == subject.FORMAL_DECISION_SCHEMA
    assert formal["approved"] is True
    assert formal["unsigned"] is False
    assert formal["decision_finalized"] is True
    assert formal["human_review_completed"] is True
    assert formal["human_decision_created"] is True
    assert formal["formal_authority_created"] is True


def test_exact_human_D1_D6_and_d6_identity() -> None:
    human = _formal()["human_authorization"]
    assert human["D1_task_relevance"] == "NOT_RELEVANT"
    assert [human[key] for key in (
        "D2_chemistry", "D3_reactive_pair", "D4_role_candidate", "D5_training_use"
    )] == ["UNRESOLVED"] * 4
    assert human["reviewer_id"] == human["attestor_id"] == "fmx"
    d6 = human["D6_scientific_context"]
    assert len(d6.encode("utf-8")) == 657
    assert hashlib.sha256(d6.encode("utf-8")).hexdigest() == (
        "d51bd3139a9ad85d285ce81e26caf4e6c9b45e447f8e3f90e6c6612d14c7d689"
    )


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("human_authorization", "D1_task_relevance"), "RELEVANT"),
        (("human_authorization", "D2_chemistry"), "POSITIVE"),
        (("human_authorization", "D2_chemistry"), "NEGATIVE"),
        (("human_authorization", "D3_reactive_pair"), "CONFIRM_OBSERVED_PAIR"),
        (("human_authorization", "D4_role_candidate"), "SELECT_CANDIDATE_0"),
        (("human_authorization", "D5_training_use"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (("approved",), False),
        (("authority_boundary", "reactive_pair_human_authority"), True),
        (("authority_boundary", "role_partition_human_authority"), True),
        (("authority_boundary", "chemistry_positive_authority"), True),
        (("authority_boundary", "chemistry_negative_authority"), True),
        (("training_boundary", "human_training_excluded"), True),
        (("training_boundary", "future_training_admission_candidate"), True),
        (("training_boundary", "formal_training_admitted"), True),
        (("training_boundary", "formal_split_authority"), True),
        (("PRE_POST_boundary", "POST_geometry_training_authority_created"), True),
        (("PRE_POST_boundary", "PRE_geometry_authority_created"), True),
    ),
)
def test_formal_semantic_tamper_fails_after_digest_is_refreshed(
    path: tuple[object, ...], value: object
) -> None:
    formal = _formal()
    _set_path(formal, path, value)
    _refresh_semantic_digest(formal)
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject._validate_formal_document(formal)


def test_formal_decision_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT.parent / subject.FORMAL_DECISION_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=tampered)


def test_formal_validator_provenance_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT.parent / subject.FORMAL_VALIDATOR_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, formal_validator_path=tampered)


@pytest.mark.parametrize(
    "relative", (subject.FORMAL_DECISION_RELATIVE, subject.FORMAL_VALIDATOR_RELATIVE)
)
def test_formal_exact2_symlink_is_rejected(tmp_path: Path, relative: Path) -> None:
    source = ROOT.parent / relative
    link = tmp_path / source.name
    link.symlink_to(source)
    kwargs = (
        {"formal_decision_path": link}
        if relative == subject.FORMAL_DECISION_RELATIVE
        else {"formal_validator_path": link}
    )
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **kwargs)


@pytest.mark.parametrize(
    "relative", (subject.FORMAL_DECISION_RELATIVE, subject.FORMAL_VALIDATOR_RELATIVE)
)
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
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **kwargs)


def test_semantic_owner_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT / subject.GENERIC_RECONCILIATION_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(
            ROOT,
            repository_path_overrides={subject.GENERIC_RECONCILIATION_RELATIVE: tampered},
        )


def test_current_census_boundary_proves_exact4_and_excludes_c2_rows() -> None:
    boundary = subject.load_frozen_formal_decision_v1(ROOT)["current_census_boundary"]
    assert boundary == {
        "universe_event_count": 1000,
        "one_n0_total_event_count": 6,
        "one_n0_target_review_unit_event_count": 4,
        "one_n0_separate_C2_review_unit_event_count": 2,
        "one_n0_target_prior_status": "CURRENTLY_UNREVIEWED",
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
    }


def test_build_is_byte_deterministic_and_output_set_is_exact4() -> None:
    first = subject.build_artifacts_v1(ROOT)
    second = subject.build_artifacts_v1(ROOT)
    assert first == second
    assert tuple(first) == subject.OUTPUT_FILENAMES
    subject.validate_completed_decision_projection_v1(first, repo_root=ROOT)


def test_snapshot_preserves_completed_negative_projection_and_authority_boundary() -> None:
    snapshot = json.loads(subject.build_artifacts_v1(ROOT)[subject.SNAPSHOT])
    assert snapshot["identity"]["canonical_event_ids"] == list(subject.EXPECTED_EVENT_IDS)
    assert snapshot["identity"]["scaleup_ranks"] == [775, 776, 778, 780]
    assert snapshot["identity"]["separate_review_unit_C2_event_ranks"] == [777, 779]
    assert snapshot["human_decision"]["approved"] is True
    assert snapshot["human_decision"]["approved_is_chemistry_approval"] is False
    assert snapshot["human_decision"]["D1_task_relevance"] == "NOT_RELEVANT"
    assert len(snapshot["normalized_completed_negative_facts"]) == 4
    for fact in snapshot["normalized_completed_negative_facts"]:
        assert {key: fact[key] for key in subject.GENERIC_PROJECTION} == subject.GENERIC_PROJECTION
    assert snapshot["raw_structural_evidence_boundary"] == {
        "raw_structural_evidence_available": True,
        "raw_structural_evidence_event_count": 4,
        "raw_structural_reactive_pair_evidence": True,
        "raw_evidence_promoted_to_human_authority": False,
        "POST_source_evidence_available": True,
    }
    assert snapshot["authority_boundary"]["authority_created_by_this_ingestion"] is False


def test_matrix_exact4_raw_pair_and_second_endpoint_context_are_preserved() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    assert len(rows) == 4
    assert [int(row["scaleup_rank"]) for row in rows] == [775, 776, 778, 780]
    assert not ({777, 779} & {int(row["scaleup_rank"]) for row in rows})
    assert [row["observed_POST_distance_angstrom"] for row in rows] == [
        "1.793126", "1.798644", "1.800281", "1.794709"
    ]
    assert [row["second_endpoint_protein_chemistry_class"] for row in rows] == [
        "HIS_NE2", "HIS_NE2", "CYS_SG", "CYS_SG"
    ]
    for row in rows:
        assert row["explicit_covalent_evidence"] == "true"
        assert row["raw_structural_reactive_pair_evidence"] == "true"
        assert row["observed_protein_reactive_atom"] == "SG"
        assert row["observed_ligand_reactive_atom"] == "C16"
        assert row["second_endpoint_present"] == "true"
        assert row["second_endpoint_ligand_atom"] == "C2"
        assert row["second_endpoint_is_target_event"] == "false"
        assert row["reactive_pair_human_authoritative"] == "false"


def test_matrix_human_authority_normalized_and_training_boundaries_are_exact() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    for row in rows:
        assert row["human_task_relevance_decision"] == "NOT_RELEVANT"
        assert row["task_relevance_human_authoritative"] == "true"
        assert row["task_domain_negative"] == "true"
        assert [row[f"D{number}_human_choice"] for number in (2, 3, 4, 5)] == [
            "UNRESOLVED"
        ] * 4
        assert row["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert row["task_relevance_disposition"] == "NOT_RELEVANT"
        assert row["chemistry_disposition"] == "NOT_ESTABLISHED"
        assert row["training_disposition"] == "NOT_APPLICABLE"
        assert row["human_training_excluded"] == "false"
        assert row["training_use_include"] == "false"
        assert row["future_training_admission_candidate"] == "false"
        assert row["training_admitted"] == "false"
        assert row["formal_split_authority_created"] == "false"
        assert row["ready_for_training"] == "false"


def test_role_and_exact5_authority_vector_are_negative_safe() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    null_fields = (
        "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
        "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
        "sample_authoritative_applicable_task_ids_json", "chemical_warhead_atoms_json",
    )
    for row in rows:
        assert all(row[field] == "null" and json.loads(row[field]) is None for field in null_fields)
        vector = json.loads(row["canonical_task_authority_availability_json"])
        assert [(item["task_id"], item["semantic_long_name"], item["display_alias"]) for item in vector] == [
            (0, "warhead_only", "A"),
            (1, "linker_plus_warhead", "B"),
            (2, "scaffold_plus_warhead", "B2"),
            (3, "scaffold_only", "B3"),
            (4, "scaffold_plus_linker_plus_warhead", "C"),
        ]
        assert all(item["authoritative_label_available"] is False for item in vector)
        assert row["global_canonical_task_count"] == "5"
        assert row["B3_present"] == "true"
        assert row["sixth_task_present"] == "false"


def test_chemistry_and_pre_post_authorities_fail_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    for row in rows:
        assert row["chemistry_known_positive"] == "false"
        assert row["negative_chemistry"] == "false"
        assert row["sample_level_chemistry_positive_authority"] == "false"
        assert row["sample_level_chemistry_negative_authority"] == "false"
        assert row["POST_source_evidence_available"] == "true"
        assert row["POST_geometry_training_authority_available"] == "false"
        assert row["PRE_status"] == subject.PRE_STATUS
        assert row["PRE_source_graph_mapping_count"] == "0"
        assert row["PRE_topology_authority_available"] == "false"
        assert row["PRE_geometry_authority_available"] == "false"


def test_summary_exact_negative_counts() -> None:
    summary = json.loads(subject.build_artifacts_v1(ROOT)[subject.SUMMARY])
    assert summary["event_count"] == 4
    assert summary["task_domain_negative"] is True
    assert summary["completed_negative_event_count"] == 4
    assert summary["task_relevance_authority_event_count"] == 4
    assert summary["task_relevant_event_count"] == 0
    assert summary["chemistry_positive_authority_count"] == 0
    assert summary["chemistry_negative_authority_count"] == 0
    assert summary["reactive_pair_human_authority_count"] == 0
    assert summary["role_partition_human_authority_count"] == 0
    assert summary["canonical_mask_label_authority_count"] == 0
    assert summary["training_include_count"] == 0
    assert summary["future_training_candidate_count"] == 0
    assert summary["normalized_disposition_counts"] == {
        "COMPLETED_HUMAN_NEGATIVE": 4,
        "NOT_RELEVANT": 4,
        "NOT_ESTABLISHED": 4,
        "NOT_APPLICABLE": 4,
    }


@pytest.mark.parametrize(
    ("name", "path", "value"),
    (
        (subject.SNAPSHOT, ("human_decision", "approved_is_chemistry_approval"), True),
        (subject.SNAPSHOT, ("normalized_completed_negative_facts", 0, "chemistry_disposition"), "NEGATIVE"),
        (subject.SNAPSHOT, ("normalized_completed_negative_facts", 0, "training_disposition"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (subject.SNAPSHOT, ("chemistry_authority_boundary", "sample_level_chemistry_positive_authority"), True),
        (subject.SNAPSHOT, ("role_authority_boundary", "role_partition_human_authoritative"), True),
        (subject.SNAPSHOT, ("role_authority_boundary", "selected_role_candidate_index_0based"), 0),
        (subject.SNAPSHOT, ("role_authority_boundary", "role_profile"), "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        (subject.SNAPSHOT, ("role_authority_boundary", "warhead_atom_ids"), []),
        (subject.SNAPSHOT, ("role_authority_boundary", "sample_authoritative_applicable_task_ids"), [0]),
        (subject.SNAPSHOT, ("canonical_task_contract", "B3_present"), False),
        (subject.SNAPSHOT, ("canonical_task_contract", "sixth_task_present"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "POST_geometry_training_authority_available"), True),
        (subject.SNAPSHOT, ("geometry_boundary", "PRE_geometry_authority_available"), True),
        (subject.SNAPSHOT, ("training_boundary", "training_use_include"), True),
        (subject.SNAPSHOT, ("training_boundary", "human_training_excluded"), True),
        (subject.SNAPSHOT, ("training_boundary", "future_training_admission_candidate"), True),
        (subject.SNAPSHOT, ("training_boundary", "training_admitted"), True),
        (subject.SNAPSHOT, ("training_boundary", "formal_split_authority_created"), True),
        (subject.SUMMARY, ("event_count",), 5),
        (subject.MANIFEST, ("ready_for_training",), True),
    ),
)
def test_json_projection_tamper_fails_closed(
    name: str, path: tuple[object, ...], value: object
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    tampered = _mutated_json_artifact(artifacts, name, path, value)
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("scaleup_rank", "777"),
        ("scaleup_rank", "779"),
        ("human_task_relevance_decision", "RELEVANT"),
        ("chemistry_disposition", "NEGATIVE"),
        ("training_disposition", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("reactive_pair_human_authoritative", "true"),
        ("role_partition_human_authoritative", "true"),
        ("selected_role_candidate_index_0based", "0"),
        ("role_profile", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        ("warhead_atoms_json", "[]"),
        ("linker_atoms_json", "[]"),
        ("scaffold_atoms_json", "[]"),
        ("sample_authoritative_applicable_task_ids_json", "[0]"),
        ("second_endpoint_present", "false"),
        ("second_endpoint_is_target_event", "true"),
        ("POST_geometry_training_authority_available", "true"),
        ("PRE_geometry_authority_available", "true"),
        ("training_use_include", "true"),
        ("human_training_excluded", "true"),
        ("future_training_admission_candidate", "true"),
        ("training_admitted", "true"),
        ("formal_split_authority_created", "true"),
    ),
)
def test_matrix_tamper_fails_closed(field: str, value: str) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    tampered = _mutated_matrix_artifact(artifacts, 0, field, value)
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_one_exact5_task_authority_true_is_rejected() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    vector = json.loads(rows[0]["canonical_task_authority_availability_json"])
    vector[3]["authoritative_label_available"] = True
    rows[0]["canonical_task_authority_availability_json"] = subject._json_cell(vector)
    tampered = dict(artifacts)
    tampered[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows)
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_sixth_exact5_task_is_rejected() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    vector = json.loads(rows[0]["canonical_task_authority_availability_json"])
    vector.append({
        "task_id": 5,
        "semantic_long_name": "forbidden_sixth",
        "display_alias": "X",
        "authoritative_label_available": False,
    })
    rows[0]["canonical_task_authority_availability_json"] = subject._json_cell(vector)
    tampered = dict(artifacts)
    tampered[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows)
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_manifest_exact9_candidate_exact7_and_nonrecursive_output_hashes() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert manifest["candidate_file_count"] == 7
    assert manifest["output_file_count"] == 4
    assert manifest["active_source_binding_count"] == 9
    assert len(manifest["candidate_source_bindings"]) == 3
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert subject.MANIFEST not in manifest["output_artifact_bindings"]
    assert manifest["source_binding_V2_clean_from_birth"] is True
    assert manifest["numeric_POSIX_semantic_identity"] is False
    assert manifest["formal_validator_runtime_dependency"] is False
    for name in (subject.SNAPSHOT, subject.MATRIX, subject.SUMMARY):
        binding = manifest["output_artifact_bindings"][name]
        assert binding["byte_count"] == len(artifacts[name])
        assert binding["SHA256"] == subject._sha256(artifacts[name])
        assert binding["expected_executable_class"] == "NON_EXECUTABLE"


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
    with pytest.raises(subject.OneN0IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(tampered)


def test_materialization_writes_exact4_and_is_deterministic(tmp_path: Path) -> None:
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "contaminated"
    output.mkdir()
    sentinel = output / "unexpected.txt"
    sentinel.write_bytes(b"sentinel\n")
    writes: list[Path] = []
    monkeypatch.setattr(subject, "_atomic_write", lambda path, payload: writes.append(path))
    with pytest.raises(subject.OneN0IngestionSafetyError, match="UNEXPECTED_ENTRIES"):
        subject.materialize_artifacts_v1(ROOT, output_root=output)
    assert writes == []
    assert sentinel.read_bytes() == b"sentinel\n"
    assert {path.name for path in output.iterdir()} == {"unexpected.txt"}


def test_materialization_rejects_root_symlink_without_resolving_it(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(subject.OneN0IngestionSafetyError, match="ROOT_SYMLINK"):
        subject.materialize_artifacts_v1(ROOT, output_root=link)
    assert tuple(real.iterdir()) == ()


def test_materialization_rejects_allowed_output_symlink_before_write(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    target = tmp_path / "target"
    target.write_bytes(b"target\n")
    (output / subject.SNAPSHOT).symlink_to(target)
    with pytest.raises(subject.OneN0IngestionSafetyError, match="ENTRY_NOT_REGULAR"):
        subject.materialize_artifacts_v1(ROOT, output_root=output)
    assert target.read_bytes() == b"target\n"
    assert {path.name for path in output.iterdir()} == {subject.SNAPSHOT}


def test_materialization_rejects_allowed_output_nonregular_before_write(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / subject.MATRIX).mkdir()
    with pytest.raises(subject.OneN0IngestionSafetyError, match="ENTRY_NOT_REGULAR"):
        subject.materialize_artifacts_v1(ROOT, output_root=output)
    assert {path.name for path in output.iterdir()} == {subject.MATRIX}


def test_partial_allowed_subset_and_complete_rematerialization_are_idempotent(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / subject.SUMMARY).write_bytes(b"old\n")
    first = subject.materialize_artifacts_v1(ROOT, output_root=output)
    before = {name: (output / name).read_bytes() for name in subject.OUTPUT_FILENAMES}
    second = subject.materialize_artifacts_v1(ROOT, output_root=output)
    after = {name: (output / name).read_bytes() for name in subject.OUTPUT_FILENAMES}
    assert first == second
    assert before == after == first


def test_materialized_repository_outputs_match_fresh_build() -> None:
    assert subject.check_materialized_v1(ROOT) == {
        "status": "PASS",
        "schema_version": subject.SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "task_domain_negative": True,
        "completed_negative_projection_exact": True,
        "raw_structural_evidence_preserved": True,
        "raw_evidence_promoted_to_human_authority": False,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
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
    assert "BASELINE_HEAD" not in source
    assert "git rev-parse" not in source
    assert "git status" not in source


def test_candidate_lifecycle_simulations_are_supported_without_successor_sha() -> None:
    paths = {path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS}
    checker.validate_relation_values(
        profile=checker.CANDIDATE_UNTRACKED,
        head=checker.BASELINE_HEAD,
        parent=None,
        origin_main=checker.BASELINE_HEAD,
        ahead=0,
        behind=0,
        changed_paths=set(),
        expected_paths=paths,
    )
    successor = "e" * 40
    checker.validate_relation_values(
        profile=checker.TRACKED_CLEAN,
        head=successor,
        parent=checker.BASELINE_HEAD,
        origin_main=checker.BASELINE_HEAD,
        ahead=1,
        behind=0,
        changed_paths=paths,
        expected_paths=paths,
    )
    checker.validate_relation_values(
        profile=checker.TRACKED_CLEAN,
        head=successor,
        parent=checker.BASELINE_HEAD,
        origin_main=successor,
        ahead=0,
        behind=0,
        changed_paths=paths,
        expected_paths=paths,
    )
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    assert successor not in checker_source


def test_lifecycle_rejects_non_direct_successor_and_wrong_relations() -> None:
    paths = {path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS}
    with pytest.raises(SystemExit, match="DIRECT_SUCCESSOR"):
        checker.validate_relation_values(
            profile=checker.TRACKED_CLEAN,
            head="e" * 40,
            parent="d" * 40,
            origin_main=checker.BASELINE_HEAD,
            ahead=1,
            behind=0,
            changed_paths=paths,
            expected_paths=paths,
        )
    with pytest.raises(SystemExit, match="ORIGIN_RELATION"):
        checker.validate_relation_values(
            profile=checker.TRACKED_CLEAN,
            head="e" * 40,
            parent=checker.BASELINE_HEAD,
            origin_main=checker.BASELINE_HEAD,
            ahead=2,
            behind=0,
            changed_paths=paths,
            expected_paths=paths,
        )


def test_no_dynamic_metadata_absolute_paths_or_output_side_effect_imports() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    for name in (subject.SNAPSHOT, subject.SUMMARY, subject.MANIFEST):
        text = artifacts[name].decode("utf-8")
        assert '"created_at"' not in text
        assert '"generated_at"' not in text
        assert '"validated_at"' not in text
        assert "/cpfs" not in text
        assert "/tmp/" not in text
