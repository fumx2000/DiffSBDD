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
    covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1
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


def _reverse_boundaries(document: dict[str, object]) -> None:
    document["selected_role_partition"]["boundary_bonds"].reverse()  # type: ignore[index,union-attr]


def _remove_b3(document: dict[str, object]) -> None:
    document["selected_role_partition"]["global_canonical_Exact5"]["tasks"].pop(3)  # type: ignore[index,union-attr]


def _add_sixth_task(document: dict[str, object]) -> None:
    exact5 = document["selected_role_partition"]["global_canonical_Exact5"]  # type: ignore[index]
    exact5["sixth_task_present"] = True
    exact5["task_count"] = 6
    exact5["tasks"].append({"display_alias": "X", "semantic_name": "forbidden", "task_id": 5})


FORMAL_MUTATIONS = (
    ("wrong_schema", _path_mutation(("schema_version",), "wrong")),
    ("wrong_review_unit", _path_mutation(("review_unit_id",), "wrong")),
    ("wrong_ligand", _path_mutation(("ligand_component_id",), "XXX")),
    ("reviewer_drift", _path_mutation(("reviewer_id",), "other")),
    ("attestor_drift", _path_mutation(("attestor_id",), "other")),
    ("approval_false", _path_mutation(("approved",), False)),
    ("unsigned_true", _path_mutation(("unsigned",), True)),
    ("approval_timestamp", _path_mutation(("human_approval", "approved_at_utc"), "2026-08-26T15:39:37Z")),
    ("exact8_missing", _remove_event),
    ("exact8_duplicate", _duplicate_event),
    ("exact8_extra", _extra_event),
    ("rank_drift", _path_mutation(("event_level_human_decisions", 0, "scaleup_rank"), 498)),
    ("pdb_drift", _path_mutation(("event_level_human_decisions", 0, "pdb_id"), "XXXX")),
    ("model_drift", _path_mutation(("event_level_human_decisions", 0, "model_number"), 2)),
    ("protein_chain_drift", _path_mutation(("event_level_human_decisions", 0, "protein_chain_or_asym"), "Z")),
    ("ligand_chain_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_chain_or_asym"), "Z")),
    ("protein_altloc_drift", _path_mutation(("event_level_human_decisions", 0, "protein_altloc"), "A")),
    ("ligand_altloc_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_altloc"), "A")),
    ("connection_drift", _path_mutation(("event_level_human_decisions", 0, "selected_connection_id"), "covale999")),
    ("post_numeric_drift", _path_mutation(("event_level_human_decisions", 0, "POST_distance_angstrom"), 2.0)),
    ("post_lexeme_drift", _path_mutation(("event_level_human_decisions", 0, "POST_distance_frozen_lexeme"), "2.013128")),
    ("D1_drift", _path_mutation(("event_level_human_decisions", 0, "D1_human_task_relevance_decision"), "NOT_RELEVANT")),
    ("D2_drift", _path_mutation(("event_level_human_decisions", 0, "D2_human_chemistry_support_disposition"), "NEGATIVE")),
    ("negative_chemistry_true", _path_mutation(("event_level_human_decisions", 0, "negative_chemistry"), True)),
    ("task_domain_negative_true", _path_mutation(("event_level_human_decisions", 0, "task_domain_negative"), True)),
    ("D3_drift", _path_mutation(("event_level_human_decisions", 0, "D3_human_reactive_pair_decision"), "OTHER")),
    ("SG_drift", _path_mutation(("event_level_human_decisions", 0, "protein_reactive_atom"), "CB")),
    ("SD_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_reactive_atom"), "C15")),
    ("SD_element_drift", _path_mutation(("event_level_human_decisions", 0, "ligand_reactive_atom_element"), "C")),
    ("D4_drift", _path_mutation(("event_level_human_decisions", 0, "D4_human_role_partition_choice"), "SELECT_CANDIDATE_0")),
    ("candidate_index_drift", _path_mutation(("selected_role_partition", "candidate_index_0based"), 0)),
    ("role_profile_drift", _path_mutation(("selected_role_partition", "role_profile"), "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1")),
    ("warhead_drift", _path_mutation(("selected_role_partition", "warhead_atoms"), ["C15"])),
    ("linker_drift", _path_mutation(("selected_role_partition", "linker_atoms"), ["C16", "N17"])),
    ("scaffold_drift", _path_mutation(("selected_role_partition", "scaffold_atoms"), ["C18"])),
    ("boundary_C15_SD_drift", _path_mutation(("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "C16")),
    ("boundary_C18_N17_drift", _path_mutation(("selected_role_partition", "boundary_bonds", 1, "atom_id_1"), "C20")),
    ("boundary_order_drift", _reverse_boundaries),
    ("applicability_not_all_five", _path_mutation(("selected_role_partition", "applicable_canonical_task_ids"), [0, 3, 4])),
    ("B3_missing", _remove_b3),
    ("sixth_task", _add_sixth_task),
    ("D5_include", _path_mutation(("training_use_human_decision", "D5_human_choice"), "INCLUDE")),
    ("human_excluded_false", _path_mutation(("event_level_human_decisions", 0, "human_training_excluded"), False)),
    ("future_candidate_true", _path_mutation(("training_use_human_decision", "future_training_admission_candidate_count"), 1)),
    ("training_admitted_true", _path_mutation(("event_level_human_decisions", 0, "training_admitted"), True)),
    ("event_exception_true", _path_mutation(("event_level_human_decisions", 0, "event_specific_disposition_exception"), True)),
    ("engineered_site_drift", _path_mutation(("human_approved_context", "engineered_target_site"), "PDK1_T148")),
    ("native_cysteine_true", _path_mutation(("human_approved_context", "native_cysteine_site"), True)),
    ("medicinal_context_false", _path_mutation(("human_approved_context", "medicinal_covalent_inhibitor_context"), False)),
    ("allosteric_context_false", _path_mutation(("human_approved_context", "allosteric_inhibitor_context"), False)),
    ("disulfide_context_false", _path_mutation(("human_approved_context", "disulfide_trapping_context"), False)),
    ("retained_fragment_context_false", _path_mutation(("human_approved_context", "observed_retained_fragment_context"), False)),
    ("observed_complete_PRE_true", _path_mutation(("observed_graph_pre_boundary", "observed_graph_is_complete_authoritative_PRE_reagent"), True)),
    ("PRE_geometry_true", _path_mutation(("geometry_boundary", "PRE_geometry_authority_created"), True)),
    ("PRE_topology_true", _path_mutation(("observed_graph_pre_boundary", "PRE_precursor_topology_authority_created"), True)),
    ("complete_PRE_disulfide_true", _path_mutation(("observed_graph_pre_boundary", "PRE_complete_disulfide_reagent_authority_created"), True)),
    ("PRE_reconstruction_true", _path_mutation(("observed_graph_pre_boundary", "PRE_precursor_reconstruction_performed"), True)),
    ("POST_training_true", _path_mutation(("geometry_boundary", "POST_geometry_training_authority_created"), True)),
    ("reaction_family_true", _path_mutation(("reaction_family_authority", "authority_created"), True)),
    ("warhead_rule_true", _path_mutation(("warhead_rule_authority", "authority_created"), True)),
    ("warhead_type_true", _path_mutation(("warhead_type_authority", "authority_created"), True)),
    ("reusable_chemistry_true", _path_mutation(("reusable_authority_boundary", "reusable_chemistry_authority_created"), True)),
    ("reusable_pair_true", _path_mutation(("reusable_authority_boundary", "reusable_reactive_pair_authority_created"), True)),
    ("reusable_role_true", _path_mutation(("reusable_authority_boundary", "reusable_role_authority_created"), True)),
)


def test_frozen_formal_binding_namespaces_and_exact8_ingestion() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    binding = bound["formal_decision_binding"]
    assert binding["path_namespace"] == "repository_parent_relative"
    assert binding["byte_count"] == 31063
    assert binding["sha256"] == subject.FORMAL_DECISION_SHA256
    assert binding["schema_version"] == subject.FORMAL_DECISION_SCHEMA
    assert binding["reviewer_id"] == binding["attestor_id"] == "fmx"
    assert binding["approved_at_utc"] == "2026-08-26T15:39:36Z"
    assert len(bound["frozen_review_package_bindings"]) == 6
    assert all(
        row["path_namespace"] == "project_parent_relative"
        for row in bound["frozen_review_package_bindings"]
    )
    events = bound["normalized"]["events"]
    assert len(events) == len({event["canonical_event_id"] for event in events}) == 8
    assert tuple(event["canonical_event_id"] for event in events) == subject.EXPECTED_EVENT_IDS


def test_candidate7_exact5_context_and_PRE_boundary() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    role = snapshot["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 7
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["warhead_atoms"] == ["SD"]
    assert role["linker_atoms"] == ["C15", "C16", "N17"]
    assert role["scaffold_atoms"] == list(subject.EXPECTED_SCAFFOLD)
    assert [bond["bond_order"] for bond in role["boundary_bonds"]] == ["SING", "SING"]
    tasks = snapshot["canonical_task_contract"]
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_created"] is False
    assert tasks["strict_profile_applicable_task_ids"] == [0, 1, 2, 3, 4]
    assert tasks["global_canonical_tasks"][3]["semantic_long_name"] == "scaffold_only"
    context = snapshot["scientific_context"]
    assert context["engineered_target_site"] == "PDK1_T148C"
    assert context["native_cysteine_site"] is False
    assert context["disulfide_trapping_context"] is True
    observed = snapshot["observed_graph_PRE_boundary"]
    assert observed["observed_reactive_atom"] == "SD"
    assert observed["observed_reactive_atom_element"] == "S"
    assert observed["observed_graph_represents_retained_fragment"] is True
    assert observed["observed_graph_is_complete_authoritative_PRE_reagent"] is False
    assert observed["authoritative_complete_PRE_disulfide_reagent_topology"] is None


def test_matrix_summary_manifest_direct_evidence() -> None:
    artifacts = _artifacts()
    matrix = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode())))
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert len(matrix) == 8
    assert [int(row["scaleup_rank"]) for row in matrix] == list(range(499, 507))
    assert all(row["protein_reactive_atom"] == "SG" for row in matrix)
    assert all(row["ligand_reactive_atom"] == "SD" for row in matrix)
    assert all(row["ligand_reactive_atom_element"] == "S" for row in matrix)
    assert all(row["strict_profile_applicable_task_ids_json"] == "[0,1,2,3,4]" for row in matrix)
    assert summary["event_count"] == summary["chemistry_positive_count"] == 8
    assert summary["training_excluded_positive_count"] == 8
    assert summary["training_include_count"] == 0
    assert summary["published_global_positive_count_remains"] == 74
    assert summary["ready_for_training"] is False
    assert len(manifest["current_published_census_bindings"]) == 4
    assert manifest["global_reconciliation_update_status"] == "NOT_DONE_THIS_STEP"
    assert manifest["global_census_update_status"] == "NOT_DONE_THIS_STEP"
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
    ("snapshot_D1", ("unit_level_D1_D6", "D1"), "NOT_RELEVANT"),
    ("snapshot_SG", ("reactive_pair", "protein_reactive_atom"), "CB"),
    ("snapshot_SD", ("reactive_pair", "ligand_reactive_atom"), "C15"),
    ("snapshot_SD_element", ("reactive_pair", "ligand_reactive_atom_element"), "C"),
    ("snapshot_candidate7", ("selected_role_partition", "selected_candidate_index_0based"), 0),
    ("snapshot_STRICT", ("selected_role_partition", "role_profile"), "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
    ("snapshot_complete_PRE", ("observed_graph_PRE_boundary", "observed_graph_is_complete_authoritative_PRE_reagent"), True),
    ("snapshot_D5", ("training_boundary", "formal_event_training_use_decision"), "INCLUDE"),
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
    with pytest.raises(subject.OneF8IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_frozen_derived_projection_digests_match_current_artifacts() -> None:
    artifacts = _artifacts()
    assert _sha(artifacts[subject.SNAPSHOT]) == subject._EXPECTED_SNAPSHOT_SHA256_V1
    assert _sha(artifacts[subject.MATRIX]) == subject._EXPECTED_MATRIX_SHA256_V1
    assert _sha(artifacts[subject.SUMMARY]) == subject._EXPECTED_SUMMARY_SHA256_V1


def test_formal_payload_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(FORMAL.read_bytes() + b"\n")
    with pytest.raises(subject.OneF8IngestionSafetyError, match="BYTE_COUNT"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


def test_formal_payload_same_size_sha_mutation_fails_closed(tmp_path: Path) -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[-2] = 0x20 if payload[-2] != 0x20 else 0x09
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(payload)
    assert len(payload) == subject.FORMAL_DECISION_BYTE_COUNT
    with pytest.raises(subject.OneF8IngestionSafetyError, match="SHA256"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


@pytest.mark.parametrize("case,mutate", FORMAL_MUTATIONS, ids=[row[0] for row in FORMAL_MUTATIONS])
def test_formal_semantic_drift_fails_closed(case: str, mutate) -> None:
    del case
    formal = _formal_dict()
    mutate(formal)
    with pytest.raises(subject.OneF8IngestionSafetyError):
        subject._validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    "path",
    (
        ("authority_boundary", "reaction_family_authority_created"),
        ("authority_boundary", "warhead_rule_authority_created"),
        ("authority_boundary", "warhead_type_authority_created"),
        ("authority_boundary", "reusable_chemistry_authority_created"),
        ("authority_boundary", "reusable_reactive_pair_authority_created"),
        ("authority_boundary", "reusable_role_authority_created"),
        ("authority_boundary", "complete_PRE_disulfide_reagent_authority_created"),
        ("authority_boundary", "PRE_geometry_authority_created"),
        ("authority_boundary", "POST_geometry_training_authority_created"),
        ("authority_boundary", "training_admission_created"),
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
    with pytest.raises(subject.OneF8IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_dynamic_metadata_is_rejected() -> None:
    artifacts = _artifacts()
    summary = json.loads(artifacts[subject.SUMMARY])
    summary["generated_at_utc"] = "2026-08-26T15:39:36Z"
    artifacts[subject.SUMMARY] = subject._json_bytes(summary)
    with pytest.raises(subject.OneF8IngestionSafetyError, match="DYNAMIC"):
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
        "__name__": "check_covapie_1f8_ingestion_v1",
    }
    exec(compile(checker.read_bytes(), checker.as_posix(), "exec"), namespace)
    result = namespace["run_check_v1"](ROOT)  # type: ignore[operator]
    assert result["candidate_publication_file_count"] == 7
    assert result["exact8_unique_complete"] is True
    assert result["derived_projection_digests_verified"] is True
    assert result["current_census_preserved_and_bound"] is True
    assert result["ready_for_1F8_reconciliation_successor"] is True
    assert result["ready_for_training"] is False
