from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


FORMAL = ROOT.parent / subject.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _artifacts() -> dict[str, bytes]:
    return subject.build_artifacts_v1(ROOT)


def _formal_dict() -> dict[str, object]:
    return json.loads(FORMAL.read_bytes())


def _set_path(document: object, path: tuple[object, ...], value: object) -> None:
    cursor = document
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[path[-1]] = value  # type: ignore[index]


def _path_mutation(path: tuple[object, ...], value: object):
    def mutate(document: dict[str, object]) -> None:
        _set_path(document, path, value)

    return mutate


def _remove_event(document: dict[str, object]) -> None:
    document["event_level_human_decisions"].pop()  # type: ignore[union-attr]


def _duplicate_event(document: dict[str, object]) -> None:
    events = document["event_level_human_decisions"]
    events[1] = copy.deepcopy(events[0])  # type: ignore[index]


def _extra_event(document: dict[str, object]) -> None:
    events = document["event_level_human_decisions"]
    events.append(copy.deepcopy(events[-1]))  # type: ignore[union-attr,index]


def _remove_b3(document: dict[str, object]) -> None:
    document["canonical_Exact5_and_sample_applicability"]["tasks"].pop(3)  # type: ignore[index,union-attr]


def _add_sixth_task(document: dict[str, object]) -> None:
    exact5 = document["canonical_Exact5_and_sample_applicability"]  # type: ignore[index]
    exact5["task_count"] = 6
    exact5["sixth_task_present"] = True
    exact5["tasks"].append(
        {"task_id": 5, "semantic_name": "forbidden", "display_alias": "X", "structurally_applicable": True}
    )


FORMAL_MUTATIONS = (
    ("wrong_schema", _path_mutation(("schema_version",), "wrong")),
    ("wrong_record_role", _path_mutation(("record_role",), "wrong")),
    ("wrong_status", _path_mutation(("decision_status",), "wrong")),
    ("wrong_review_unit", _path_mutation(("review_unit_id",), "wrong")),
    ("wrong_ligand", _path_mutation(("ligand_component_id",), "XXX")),
    ("reviewer_drift", _path_mutation(("reviewer_id",), "other")),
    ("attestor_drift", _path_mutation(("attestor_id",), "other")),
    ("approval_false", _path_mutation(("approved",), False)),
    ("unsigned_true", _path_mutation(("unsigned",), True)),
    ("approval_timestamp", _path_mutation(("human_approval", "approved_at_utc"), "2026-08-27T13:43:04Z")),
    ("exact7_missing", _remove_event),
    ("exact7_duplicate", _duplicate_event),
    ("exact7_extra", _extra_event),
    ("rank_drift", _path_mutation(("event_level_human_decisions", 0, "scaleup_rank"), 782)),
    ("pdb_drift", _path_mutation(("event_level_human_decisions", 0, "pdb_id"), "XXXX")),
    ("CYS797_to_CYS800", _path_mutation(("event_level_human_decisions", 0, "cys_residue_id"), "CYS:800-")),
    ("CYS800_to_CYS797", _path_mutation(("event_level_human_decisions", 2, "cys_residue_id"), "CYS:797-")),
    ("model_drift", _path_mutation(("event_level_human_decisions", 0, "model_number"), 2)),
    ("protein_chain_drift", _path_mutation(("event_level_human_decisions", 0, "protein_chain_or_asym"), "Z")),
    ("ligand_chain_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_chain_or_asym"), "Z")),
    ("protein_altloc_drift", _path_mutation(("event_level_human_decisions", 0, "protein_altloc"), "A")),
    ("ligand_altloc_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_altloc"), "A")),
    ("connection_drift", _path_mutation(("event_level_human_decisions", 0, "selected_connection_id"), "covale999")),
    ("post_distance_drift", _path_mutation(("event_level_human_decisions", 0, "POST_distance_angstrom"), 2.0)),
    ("D1_drift", _path_mutation(("event_level_human_decisions", 0, "D1_task_relevance"), "NOT_RELEVANT")),
    ("D2_drift", _path_mutation(("event_level_human_decisions", 0, "D2_chemistry_support"), "NEGATIVE")),
    ("D3_drift", _path_mutation(("event_level_human_decisions", 0, "D3_reactive_pair"), "OTHER")),
    ("SG_drift", _path_mutation(("event_level_human_decisions", 0, "protein_reactive_atom"), "CB")),
    ("CAN_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_reactive_atom"), "CAO")),
    ("CAN_element_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_reactive_atom_element"), "N")),
    ("D4_drift", _path_mutation(("event_level_human_decisions", 0, "D4_role_partition"), "SELECT_CANDIDATE_0")),
    ("candidate_index_drift", _path_mutation(("selected_role_partition", "selected_candidate_index_0based"), 0)),
    ("warhead_drift", _path_mutation(("selected_role_partition", "warhead_atoms"), ["CAN"])),
    ("source_warhead_order_drift", _path_mutation(("selected_role_partition", "frozen_source_warhead_atoms_source_order"), ["NAS", "OAC", "CAW", "CAO", "CAN"])),
    ("linker_drift", _path_mutation(("selected_role_partition", "linker_atoms"), ["CAZ"])),
    ("scaffold_drift", _path_mutation(("selected_role_partition", "scaffold_atoms"), ["BR"])),
    ("boundary_drift", _path_mutation(("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "CAY")),
    ("DIRECT_to_STRICT", _path_mutation(("selected_role_partition", "role_profile"), "STRICT_LINKER_PRESENT_V1")),
    ("all_five_applicability", _path_mutation(("selected_role_partition", "applicable_canonical_task_ids"), [0, 1, 2, 3, 4])),
    ("B3_missing", _remove_b3),
    ("sixth_task", _add_sixth_task),
    ("D5_EXCLUDE", _path_mutation(("training_use_human_decision", "D5_human_choice"), "EXCLUDE_FROM_TRAINING_ONLY")),
    ("human_excluded_true", _path_mutation(("event_level_human_decisions", 0, "human_training_excluded"), True)),
    ("observed_product_false", _path_mutation(("observed_graph_pre_boundary", "observed_graph_is_post_covalent_product_state"), False)),
    ("CAO_CAN_DOUBLE", _path_mutation(("observed_graph_pre_boundary", "observed_CAO_CAN_bond_order"), "DOUBLE")),
    ("PRE_CAO_CAN_non_null", _path_mutation(("observed_graph_pre_boundary", "PRE_CAO_CAN_bond_order_authority"), "DOUBLE")),
    ("PRE_topology_true", _path_mutation(("observed_graph_pre_boundary", "PRE_precursor_topology_authority_created"), True)),
    ("PRE_geometry_true", _path_mutation(("geometry_boundary", "PRE_geometry_authority_created"), True)),
    ("PRE_reconstruction_true", _path_mutation(("observed_graph_pre_boundary", "PRE_reconstruction_performed"), True)),
    ("POST_training_true", _path_mutation(("geometry_boundary", "POST_geometry_training_authority_created"), True)),
    ("reaction_family_true", _path_mutation(("reaction_family_authority", "reaction_family_authority_created"), True)),
    ("warhead_rule_true", _path_mutation(("warhead_rule_authority", "warhead_rule_authority_created"), True)),
    ("warhead_type_true", _path_mutation(("warhead_type_authority", "warhead_type_authority_created"), True)),
    ("reusable_true", _path_mutation(("reusable_authority_boundary", "reusable_chemistry_authority_created"), True)),
    ("training_admitted_true", _path_mutation(("training_use_human_decision", "formal_training_admitted"), True)),
    ("formal_split_true", _path_mutation(("training_use_human_decision", "formal_split_authority_created"), True)),
    ("runtime_usable_true", _path_mutation(("training_use_human_decision", "runtime_model_usable"), True)),
    ("parameter_update_true", _path_mutation(("training_use_human_decision", "parameter_update_authorization"), True)),
)


def test_frozen_formal_binding_exact7_and_provenance() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    binding = bound["formal_decision_binding"]
    assert binding["path_namespace"] == "repository_parent_relative"
    assert binding["byte_count"] == 30722
    assert binding["sha256"] == subject.FORMAL_DECISION_SHA256
    assert binding["schema_version"] == subject.FORMAL_DECISION_SCHEMA
    assert binding["reviewer_id"] == binding["attestor_id"] == "fmx"
    assert binding["approved_at_utc"] == "2026-08-27T13:43:03Z"
    assert len(bound["frozen_review_package_bindings"]) == 6
    assert [row["mode"] for row in bound["frozen_review_package_bindings"]] == [
        "0644", "0644", "0644", "0644", "0644", "0755"
    ]
    events = bound["normalized"]["events"]
    assert len(events) == len({event["canonical_event_id"] for event in events}) == 7
    assert tuple(event["canonical_event_id"] for event in events) == subject.EXPECTED_EVENT_IDS


def test_candidate4_exact5_science_and_observed_PRE_boundary() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    role = snapshot["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 4
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_atoms"] == ["NAS", "CAW", "OAC", "CAO", "CAN"]
    assert role["frozen_source_warhead_atoms_source_order"] == ["CAN", "CAO", "CAW", "OAC", "NAS"]
    assert set(role["warhead_atoms"]) == set(role["frozen_source_warhead_atoms_source_order"])
    assert role["linker_atoms"] == []
    assert role["scaffold_atoms"] == list(subject.EXPECTED_SCAFFOLD)
    assert role["boundary_bonds"] == [{
        "atom_id_1": "CAZ", "atom_id_2": "NAS", "bond_order": "SING",
        "boundary_between_roles": ["scaffold", "warhead"],
    }]
    tasks = snapshot["canonical_task_contract"]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_created"] is False
    assert tasks["direct_profile_applicable_task_ids"] == [0, 3, 4]
    context = snapshot["scientific_context"]
    assert context["compound_context"] == "PD168393"
    assert context["target_context"] == "EGFR"
    assert context["engineered_cysteine_site"] is False
    observed = snapshot["observed_graph_PRE_boundary"]
    assert observed["observed_reactive_atom"] == "CAN"
    assert observed["observed_reactive_atom_element"] == "C"
    assert observed["observed_CAO_CAN_bond_order"] == "SING"
    assert observed["PRE_CAO_CAN_bond_order_authority"] is None


def test_INCLUDE_candidate_admission_materialization_runtime_separation() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    training = snapshot["training_boundary"]
    assert training["formal_event_training_use_decision"] == "INCLUDE"
    assert training["training_use_allowed"] is True
    assert training["candidate_for_future_training_admission"] is True
    assert training["future_training_admission_status"] == subject.FUTURE_STATUS
    assert training["future_training_candidate_derived_by_ingestion"] is True
    assert training["future_training_candidate_is_training_admission"] is False
    assert training["training_admitted"] is False
    assert training["training_materialization_allowed_now"] is False
    assert training["current_runtime_model_usable"] is False
    assert training["ready_for_training"] is False


def test_matrix_summary_manifest_direct_evidence() -> None:
    artifacts = _artifacts()
    matrix = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode())))
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert len(matrix) == 7
    assert [int(row["scaleup_rank"]) for row in matrix] == list(subject.EXPECTED_RANKS)
    assert [row["cys_residue_id"] for row in matrix] == [
        "CYS:797-", "CYS:797-", "CYS:800-", "CYS:800-", "CYS:800-", "CYS:800-", "CYS:800-"
    ]
    assert all(row["protein_reactive_atom"] == "SG" for row in matrix)
    assert all(row["ligand_reactive_atom"] == "CAN" for row in matrix)
    assert all(row["ligand_reactive_atom_element"] == "C" for row in matrix)
    assert all(row["formal_event_training_use_decision"] == "INCLUDE" for row in matrix)
    assert all(row["candidate_for_future_training_admission"] == "true" for row in matrix)
    assert all(row["training_admitted"] == "false" for row in matrix)
    assert summary["event_count"] == summary["chemistry_positive_count"] == 7
    assert summary["human_training_INCLUDE_count"] == 7
    assert summary["future_training_admission_candidate_count"] == 7
    assert summary["training_admitted_count"] == 0
    assert summary["published_global_positive_count_remains"] == 82
    assert summary["published_future_training_admission_candidate_count_remains"] == 12
    assert len(manifest["include_semantic_precedent_bindings"]) == 4
    assert len(manifest["current_published_census_bindings"]) == 4
    assert "sha256" not in manifest


def test_exact4_outputs_are_deterministic_in_two_directories(tmp_path: Path) -> None:
    first = tmp_path / "a"
    second = tmp_path / "b"
    one = subject.materialize_artifacts_v1(ROOT, output_root=first)
    two = subject.materialize_artifacts_v1(ROOT, output_root=second)
    assert one == two
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in subject.OUTPUT_FILENAMES)


def test_public_standalone_validator_accepts_exact_current_artifacts() -> None:
    subject.validate_completed_decision_projection_v1(_artifacts())


COORDINATED_OUTPUT_MUTATIONS = (
    ("D1", ("unit_level_D1_D6", "D1"), "NOT_RELEVANT"),
    ("SG", ("reactive_pair", "protein_reactive_atom"), "CB"),
    ("CAN", ("reactive_pair", "ligand_reactive_atom"), "CAO"),
    ("CAN_element", ("reactive_pair", "ligand_reactive_atom_element"), "N"),
    ("CYS797_800", ("events", 0, "cys_residue_id"), "CYS:800-"),
    ("candidate4", ("selected_role_partition", "selected_candidate_index_0based"), 0),
    ("W", ("selected_role_partition", "warhead_atoms"), ["CAN"]),
    ("DIRECT_STRICT", ("selected_role_partition", "role_profile"), "STRICT_LINKER_PRESENT_V1"),
    ("all_five", ("canonical_task_contract", "direct_profile_applicable_task_ids"), [0, 1, 2, 3, 4]),
    ("D5", ("training_boundary", "formal_event_training_use_decision"), "EXCLUDE_FROM_TRAINING_ONLY"),
    ("training_use_false", ("training_boundary", "training_use_allowed"), False),
    ("candidate_false", ("training_boundary", "candidate_for_future_training_admission"), False),
    ("future_status", ("training_boundary", "future_training_admission_status"), "ADMITTED"),
    ("training_admitted", ("training_boundary", "training_admitted"), True),
    ("materialization", ("training_boundary", "training_materialization_allowed_now"), True),
    ("runtime", ("training_boundary", "current_runtime_model_usable"), True),
    ("CAO_CAN_DOUBLE", ("observed_graph_PRE_boundary", "observed_CAO_CAN_bond_order"), "DOUBLE"),
    ("PRE_CAO_CAN", ("observed_graph_PRE_boundary", "PRE_CAO_CAN_bond_order_authority"), "DOUBLE"),
    ("warhead_type", ("auxiliary_and_reusable_boundary", "warhead_type_target_available"), True),
)


@pytest.mark.parametrize("case,path,value", COORDINATED_OUTPUT_MUTATIONS, ids=[row[0] for row in COORDINATED_OUTPUT_MUTATIONS])
def test_standalone_rejects_coordinated_snapshot_and_manifest_sha_drift(
    case: str, path: tuple[object, ...], value: object
) -> None:
    del case
    artifacts = _artifacts()
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set_path(snapshot, path, value)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = _sha(artifacts[subject.SNAPSHOT])
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.YUNIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


INCLUDE_OUTPUT_MUTATIONS = (
    ("candidate_false", ("training_boundary", "candidate_for_future_training_admission"), False),
    ("wrong_future_status", ("training_boundary", "future_training_admission_status"), "WRONG"),
    ("admitted_true", ("training_boundary", "training_admitted"), True),
    ("materialization_true", ("training_boundary", "training_materialization_allowed_now"), True),
    ("runtime_true", ("training_boundary", "current_runtime_model_usable"), True),
)


@pytest.mark.parametrize("case,path,value", INCLUDE_OUTPUT_MUTATIONS, ids=[row[0] for row in INCLUDE_OUTPUT_MUTATIONS])
def test_INCLUDE_specific_separation_mutations_fail_closed(
    case: str, path: tuple[object, ...], value: object
) -> None:
    del case
    artifacts = _artifacts()
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set_path(snapshot, path, value)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = _sha(artifacts[subject.SNAPSHOT])
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.YUNIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_frozen_derived_projection_digests_match_current_artifacts() -> None:
    artifacts = _artifacts()
    assert _sha(artifacts[subject.SNAPSHOT]) == subject._EXPECTED_SNAPSHOT_SHA256_V1
    assert _sha(artifacts[subject.MATRIX]) == subject._EXPECTED_MATRIX_SHA256_V1
    assert _sha(artifacts[subject.SUMMARY]) == subject._EXPECTED_SUMMARY_SHA256_V1


def test_formal_payload_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(FORMAL.read_bytes() + b"\n")
    with pytest.raises(subject.YUNIngestionSafetyError, match="BYTE_COUNT"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


def test_formal_payload_same_size_sha_mutation_fails_closed(tmp_path: Path) -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[-2] = 0x20 if payload[-2] != 0x20 else 0x09
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(payload)
    assert len(payload) == subject.FORMAL_DECISION_BYTE_COUNT
    with pytest.raises(subject.YUNIngestionSafetyError, match="SHA256"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


@pytest.mark.parametrize("case,mutate", FORMAL_MUTATIONS, ids=[row[0] for row in FORMAL_MUTATIONS])
def test_formal_semantic_drift_fails_closed(case: str, mutate) -> None:
    del case
    formal = _formal_dict()
    mutate(formal)
    with pytest.raises(subject.YUNIngestionSafetyError):
        subject._validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    "path",
    (
        ("authority_boundary", "reaction_family_authority_created"),
        ("authority_boundary", "warhead_rule_authority_created"),
        ("authority_boundary", "warhead_type_authority_created"),
        ("authority_boundary", "reusable_chemistry_authority_created"),
        ("authority_boundary", "reusable_pair_authority_created"),
        ("authority_boundary", "reusable_role_authority_created"),
        ("authority_boundary", "PRE_topology_authority_created"),
        ("authority_boundary", "PRE_geometry_authority_created"),
        ("authority_boundary", "POST_geometry_training_authority_created"),
        ("authority_boundary", "training_admission_created"),
        ("authority_boundary", "training_materialization_allowed_now"),
        ("authority_boundary", "current_runtime_model_usable"),
        ("authority_boundary", "formal_split_authority_created"),
        ("authority_boundary", "tensor_target_created"),
        ("authority_boundary", "parameter_update_authorization"),
        ("authority_boundary", "global_reconciliation_updated"),
        ("authority_boundary", "global_census_updated"),
    ),
)
def test_output_authority_non_action_mutations_fail_closed(path: tuple[object, ...]) -> None:
    artifacts = _artifacts()
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set_path(snapshot, path, True)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = _sha(artifacts[subject.SNAPSHOT])
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.YUNIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_dynamic_metadata_is_rejected() -> None:
    artifacts = _artifacts()
    summary = json.loads(artifacts[subject.SUMMARY])
    summary["generated_at_utc"] = "2026-08-27T13:43:03Z"
    artifacts[subject.SUMMARY] = subject._json_bytes(summary)
    with pytest.raises(subject.YUNIngestionSafetyError, match="DYNAMIC"):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_current_published_census_is_bound_and_unchanged() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    assert bound["current_published_census_bindings"] == subject._expected_census_bindings()
    for relative, byte_count, sha256, _role in subject.CURRENT_CENSUS_BINDINGS:
        payload = (ROOT / relative).read_bytes()
        assert len(payload) == byte_count
        assert _sha(payload) == sha256


def test_materialized_exact7_checker() -> None:
    checker = ROOT / subject.CHECKER_RELATIVE
    namespace: dict[str, object] = {
        "__file__": checker.as_posix(),
        "__name__": "check_covapie_yun_ingestion_v1",
    }
    exec(compile(checker.read_bytes(), checker.as_posix(), "exec"), namespace)
    result = namespace["run_check_v1"](ROOT)  # type: ignore[operator]
    assert result["candidate_publication_file_count"] == 7
    assert result["exact7_unique_complete"] is True
    assert result["include_semantic_precedent_verified"] is True
    assert result["derived_projection_digests_verified"] is True
    assert result["current_census_preserved_and_bound"] is True
    assert result["published_global_positive_count_remains"] == 82
    assert result["published_future_candidate_count_remains"] == 12
    assert result["ready_for_YUN_reconciliation_successor"] is True
    assert result["ready_for_training"] is False
