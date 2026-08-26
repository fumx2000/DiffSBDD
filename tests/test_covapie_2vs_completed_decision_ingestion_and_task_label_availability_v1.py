from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


FORMAL = ROOT.parent / subject.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT


def _checker_module():
    path = ROOT / subject.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("check_covapie_2vs_ingestion_v1", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _formal() -> dict[str, object]:
    value = json.loads(FORMAL.read_bytes())
    assert type(value) is dict
    return value


def _set(
    value: dict[str, object], path: tuple[object, ...], replacement: object
) -> None:
    target: object = value
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = replacement  # type: ignore[index]


def _missing_event(value: dict[str, object]) -> None:
    events = value["event_level_human_decisions"]
    canonical = value["canonical_event_ids"]
    assert type(events) is list and type(canonical) is list
    events.pop()
    canonical.pop()


def _duplicate_event(value: dict[str, object]) -> None:
    events = value["event_level_human_decisions"]
    assert type(events) is list
    events[1]["canonical_event_id"] = events[0]["canonical_event_id"]


def _extra_event(value: dict[str, object]) -> None:
    events = value["event_level_human_decisions"]
    canonical = value["canonical_event_ids"]
    assert type(events) is list and type(canonical) is list
    extra = copy.deepcopy(events[-1])
    extra["canonical_event_id"] = "COVAPIE_CYS_SG_EVENT_V1:EXTRA"
    events.append(extra)
    canonical.append(extra["canonical_event_id"])


SEMANTIC_MUTATIONS = (
    ("wrong_schema", lambda value: _set(value, ("schema_version",), "mutated")),
    ("wrong_review_unit", lambda value: _set(value, ("review_unit_id",), "mutated")),
    ("wrong_ligand", lambda value: _set(value, ("ligand_component_id",), "PRF")),
    ("reviewer_drift", lambda value: _set(value, ("reviewer_id",), "other")),
    ("attestor_drift", lambda value: _set(value, ("attestor_id",), "other")),
    ("approval_false", lambda value: _set(value, ("approved",), False)),
    ("unsigned_true", lambda value: _set(value, ("unsigned",), True)),
    ("approval_timestamp", lambda value: _set(value, ("human_approval", "approved_at_utc"), "2026-08-26T12:21:57Z")),
    ("missing_event", _missing_event),
    ("duplicate_event", _duplicate_event),
    ("extra_event", _extra_event),
    ("rank_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "scaleup_rank"), 847)),
    ("pdb_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "pdb_id"), "4OUB")),
    ("model_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "model_number"), 2)),
    ("protein_chain_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "protein_chain_or_asym"), "B")),
    ("ligand_chain_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "ligand_chain_or_asym"), "J")),
    ("protein_altloc_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "protein_altloc"), "A")),
    ("ligand_altloc_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "ligand_altloc"), "A")),
    ("connection_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "selected_connection_id"), "covale2")),
    ("POST_distance_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "POST_distance_angstrom"), 1.0)),
    ("POST_lexeme_drift", lambda value: _set(value, ("event_level_human_decisions", 1, "POST_distance_frozen_lexeme"), "1.81187")),
    ("D1_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "D1_human_task_relevance_decision"), "NOT_RELEVANT")),
    ("D2_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "D2_human_chemistry_support_disposition"), "NEGATIVE")),
    ("negative_chemistry_true", lambda value: _set(value, ("event_level_human_decisions", 0, "negative_chemistry"), True)),
    ("task_domain_negative_true", lambda value: _set(value, ("event_level_human_decisions", 0, "task_domain_negative"), True)),
    ("D3_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "D3_human_reactive_pair_decision"), "REJECT")),
    ("SG_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "protein_reactive_atom"), "CB")),
    ("CA6_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "ligand_reactive_atom"), "OA4")),
    ("D4_drift", lambda value: _set(value, ("event_level_human_decisions", 0, "D4_human_role_partition_choice"), "SELECT_CANDIDATE_1")),
    ("candidate_index_drift", lambda value: _set(value, ("selected_role_partition", "candidate_index_0based"), 1)),
    ("role_profile_drift", lambda value: _set(value, ("selected_role_partition", "role_profile"), "STRICT_SCAFFOLD_LINKER_WARHEAD_V1")),
    ("warhead_drift", lambda value: _set(value, ("selected_role_partition", "warhead_atoms"), ["CA6"])),
    ("nonempty_linker", lambda value: _set(value, ("selected_role_partition", "linker_atoms"), ["CA5"])),
    ("scaffold_drift", lambda value: _set(value, ("selected_role_partition", "scaffold_atoms"), ["CA1"])),
    ("boundary_drift", lambda value: _set(value, ("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "CA4")),
    ("boundary_order_drift", lambda value: _set(value, ("selected_role_partition", "boundary_bonds", 0, "bond_order"), "DOUB")),
    ("D5_include", lambda value: _set(value, ("event_level_human_decisions", 0, "D5_human_training_use_disposition"), "INCLUDE")),
    ("human_training_excluded_false", lambda value: _set(value, ("event_level_human_decisions", 0, "human_training_excluded"), False)),
    ("training_admitted_true", lambda value: _set(value, ("event_level_human_decisions", 0, "training_admitted"), True)),
    ("event_exception_true", lambda value: _set(value, ("event_level_human_decisions", 0, "event_specific_disposition_exception"), True)),
    ("4NPI_context_drift", lambda value: _set(value, ("human_approved_context", "pdb_context", "4NPI"), "MUTATED")),
    ("4OUB_context_drift", lambda value: _set(value, ("human_approved_context", "pdb_context", "4OUB"), "MUTATED")),
    ("medicinal_context_true", lambda value: _set(value, ("human_approved_context", "medicinal_covalent_inhibitor_design_context"), True)),
    ("PRE_geometry_authority_true", lambda value: _set(value, ("geometry_boundary", "PRE_geometry_authority_created"), True)),
    ("PRE_topology_authority_true", lambda value: _set(value, ("observed_graph_pre_boundary", "PRE_precursor_topology_authority_created"), True)),
    ("PRE_reconstruction_true", lambda value: _set(value, ("observed_graph_pre_boundary", "PRE_precursor_reconstruction_performed"), True)),
    ("observed_PRE_topology_authority", lambda value: _set(value, ("observed_graph_pre_boundary", "observed_graph_is_authoritative_PRE_precursor_topology"), True)),
    ("POST_training_authority_true", lambda value: _set(value, ("geometry_boundary", "POST_geometry_training_authority_created"), True)),
    ("reaction_family_authority_true", lambda value: _set(value, ("reaction_family_authority", "authority_created"), True)),
    ("warhead_rule_authority_true", lambda value: _set(value, ("warhead_rule_authority", "authority_created"), True)),
    ("warhead_type_authority_true", lambda value: _set(value, ("warhead_type_authority", "authority_created"), True)),
    ("reusable_chemistry_true", lambda value: _set(value, ("reusable_authority_boundary", "reusable_chemistry_authority_created"), True)),
    ("reusable_pair_true", lambda value: _set(value, ("reusable_authority_boundary", "reusable_reactive_pair_authority_created"), True)),
    ("reusable_role_true", lambda value: _set(value, ("reusable_authority_boundary", "reusable_role_authority_created"), True)),
)


def test_frozen_formal_binding_namespaces_and_exact8_ingestion() -> None:
    payload = FORMAL.read_bytes()
    assert len(payload) == 28640
    assert hashlib.sha256(payload).hexdigest() == subject.FORMAL_DECISION_SHA256
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    binding = bound["formal_decision_binding"]
    assert binding == subject._formal_binding()
    assert binding["path_namespace"] == "repository_parent_relative"
    provenance = bound["frozen_review_package_bindings"]
    assert len(provenance) == 6
    assert {item["path_namespace"] for item in provenance} == {
        "project_parent_relative"
    }
    events = bound["normalized"]["events"]
    assert len(events) == 8
    assert tuple(event["canonical_event_id"] for event in events) == subject.EXPECTED_EVENT_IDS
    assert [event["scaleup_rank"] for event in events] == list(subject.EXPECTED_RANKS)
    assert [event["POST_distance_angstrom"] for event in events] == [row[10] for row in subject.EXPECTED_EVENTS]
    assert [event["POST_distance_frozen_lexeme"] for event in events] == [row[11] for row in subject.EXPECTED_EVENTS]
    assert all(event["task_relevant"] for event in events)
    assert all(event["chemistry_known_positive"] for event in events)
    assert all(event["reactive_pair_human_authoritative"] for event in events)
    assert all(event["role_partition_human_authoritative"] for event in events)
    assert all(event["authority_source"] == subject.AUTHORITY_SOURCE for event in events)
    assert all(event["authority_created_by_this_ingestion"] is False for event in events)


def test_candidate0_exact5_scientific_context_and_PRE_boundary() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    snapshot = subject._snapshot(bound)
    role = snapshot["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 0
    assert role["selected_candidate_id"] == "2VS_GRAPH_LOCAL_CANDIDATE_00"
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_atoms"] == ["CA6", "OA4"]
    assert role["linker_atoms"] == []
    assert role["scaffold_atoms"] == list(subject.EXPECTED_SCAFFOLD)
    assert role["boundary_bonds"] == [{"atom_id_1": "CA5", "atom_id_2": "CA6", "bond_order": "SING", "boundary_between_roles": ["scaffold", "warhead"]}]
    assert role["heavy_atom_disjoint"] is True
    assert role["heavy_atom_exhaustive"] is True
    assert role["warhead_connected"] is True
    assert role["linker_empty"] is True
    assert role["scaffold_connected"] is True
    tasks = snapshot["canonical_task_contract"]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_created"] is False
    assert tasks["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert [task["structurally_applicable"] for task in tasks["direct_profile_task_applicability"]] == [True, False, False, True, True]
    context = snapshot["scientific_context"]
    assert context["pdb_context"] == {"4NPI": "WILD_TYPE_THIOACYL_INTERMEDIATE", "4OUB": "E268A_THIOACYL_INTERMEDIATE"}
    assert context["medicinal_covalent_inhibitor_design_context"] is False
    observed = snapshot["observed_graph_PRE_boundary"]
    assert observed["observed_reactive_motif"] == "CA6=OA4"
    assert observed["observed_reactive_motif_bond_order"] == "DOUB"
    assert observed["observed_graph_is_authoritative_PRE_geometry"] is False
    assert observed["observed_graph_is_authoritative_PRE_precursor_topology"] is False
    assert observed["authoritative_PRE_precursor_topology"] is None


def test_matrix_summary_manifest_direct_evidence() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    assert len(rows) == 8
    assert [int(row["scaleup_rank"]) for row in rows] == list(subject.EXPECTED_RANKS)
    assert [row["POST_distance_angstrom"] for row in rows] == [str(item[10]) for item in subject.EXPECTED_EVENTS]
    assert [row["POST_distance_frozen_lexeme"] for row in rows] == [item[11] for item in subject.EXPECTED_EVENTS]
    assert all(row["protein_reactive_atom"] == "SG" for row in rows)
    assert all(row["ligand_reactive_atom"] == "CA6" for row in rows)
    assert all(row["formal_event_training_use_decision"] == "EXCLUDE_FROM_TRAINING_ONLY" for row in rows)
    assert sum(row["POST_source_evidence_available"] == "true" for row in rows) == 8
    for field in (
        "POST_geometry_training_label_available_now",
        "PRE_geometry_authority_available",
        "PRE_geometry_training_label_available_now",
        "PRE_precursor_topology_authority_available",
        "PRE_precursor_reconstruction_performed",
        "reaction_family_target_available", "warhead_rule_target_available",
        "warhead_type_target_available", "candidate_for_future_training_admission",
        "training_admitted", "training_materialization_allowed_now",
        "current_runtime_model_usable",
    ):
        assert all(row[field] == "false" for row in rows)
    summary = json.loads(artifacts[subject.SUMMARY])
    assert summary == subject._summary()
    assert summary["published_global_positive_count_remains"] == 66
    assert summary["2VS_source_local_positive_count"] == 8
    assert summary["global_reconciliation_update_status"] == "NOT_DONE_THIS_STEP"
    assert summary["global_census_update_status"] == "NOT_DONE_THIS_STEP"
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert "sha256" not in manifest
    assert manifest["manifest_self_sha256_recorded"] is False
    assert len(manifest["candidate_source_bindings"]) == 3
    assert len(manifest["frozen_formal_evidence_provenance"]) == 6
    assert len(manifest["immutable_semantic_owner_bindings"]) == 2
    assert manifest["output_artifact_bindings"] == {
        subject.SNAPSHOT: {"sha256": hashlib.sha256(artifacts[subject.SNAPSHOT]).hexdigest()},
        subject.MATRIX: {"sha256": hashlib.sha256(artifacts[subject.MATRIX]).hexdigest()},
        subject.SUMMARY: {"sha256": hashlib.sha256(artifacts[subject.SUMMARY]).hexdigest()},
    }


def test_exact4_outputs_are_deterministic_in_two_directories(tmp_path: Path) -> None:
    first = subject.materialize_artifacts_v1(ROOT, output_root=tmp_path / "one")
    second = subject.materialize_artifacts_v1(ROOT, output_root=tmp_path / "two")
    assert first == second
    assert tuple(first) == subject.OUTPUT_FILENAMES
    for name in subject.OUTPUT_FILENAMES:
        assert (tmp_path / "one" / name).read_bytes() == (tmp_path / "two" / name).read_bytes()
        assert (tmp_path / "one" / name).read_bytes() == first[name]


def test_public_standalone_validator_accepts_exact_current_artifacts() -> None:
    subject.validate_completed_decision_projection_v1(subject.build_artifacts_v1(ROOT))


@pytest.mark.parametrize(
    ("path", "replacement"),
    (
        (("events", 0, "D1_human_task_relevance_decision"), "NOT_RELEVANT"),
        (("events", 0, "protein_reactive_atom"), "CB"),
        (("events", 0, "ligand_reactive_atom"), "OA4"),
        (("selected_role_partition", "selected_candidate_index_0based"), 1),
        (("observed_graph_PRE_boundary", "observed_graph_is_authoritative_PRE_precursor_topology"), True),
        (("events", 0, "D5_human_training_use_disposition"), "INCLUDE"),
    ),
    ids=("D1", "SG", "CA6", "candidate0_to_1", "observed_PRE_authority", "D5_include"),
)
def test_standalone_rejects_coordinated_snapshot_and_manifest_sha_drift(
    path: tuple[object, ...], replacement: object
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set(snapshot, path, replacement)
    mutated = dict(artifacts)
    mutated[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(mutated[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = hashlib.sha256(mutated[subject.SNAPSHOT]).hexdigest()
    mutated[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.TwoVSIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(mutated)


def test_frozen_derived_projection_digests_match_current_artifacts() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    assert hashlib.sha256(artifacts[subject.SNAPSHOT]).hexdigest() == subject._EXPECTED_SNAPSHOT_SHA256_V1
    assert hashlib.sha256(artifacts[subject.MATRIX]).hexdigest() == subject._EXPECTED_MATRIX_SHA256_V1
    assert hashlib.sha256(artifacts[subject.SUMMARY]).hexdigest() == subject._EXPECTED_SUMMARY_SHA256_V1


def test_formal_payload_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(FORMAL.read_bytes() + b" ")
    with pytest.raises(subject.TwoVSIngestionSafetyError, match="BYTE_COUNT_MISMATCH"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


def test_formal_payload_same_size_sha_mutation_fails_closed(tmp_path: Path) -> None:
    payload = FORMAL.read_bytes()
    mutated_payload = payload.replace(b'"approved": true', b'"approved": fals', 1)
    assert len(mutated_payload) == len(payload) and mutated_payload != payload
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(mutated_payload)
    with pytest.raises(subject.TwoVSIngestionSafetyError, match="SHA256_MISMATCH"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


@pytest.mark.parametrize(
    ("case", "mutate"),
    SEMANTIC_MUTATIONS,
    ids=[case for case, _mutate in SEMANTIC_MUTATIONS],
)
def test_formal_semantic_drift_fails_closed(case: str, mutate) -> None:
    formal = copy.deepcopy(_formal())
    mutate(formal)
    with pytest.raises(subject.TwoVSIngestionSafetyError):
        subject._validate_formal_decision_v1(formal)


def test_output_dynamic_metadata_and_non_action_mutations_fail_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["generated_at_utc"] = subject.EXPECTED_APPROVED_AT_UTC
    dynamic = dict(artifacts)
    dynamic[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.TwoVSIngestionSafetyError, match="DYNAMIC_OR_LIFECYCLE"):
        subject.validate_completed_decision_projection_v1(dynamic)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    snapshot["authority_boundary"]["training_admission_created"] = True
    non_action = dict(artifacts)
    non_action[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    with pytest.raises(subject.TwoVSIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(non_action)


def test_materialized_exact7_checker() -> None:
    result = _checker_module().run_check_v1(ROOT)
    assert result["candidate_publication_file_count"] == 7
    assert result["output_artifact_count"] == 4
    assert result["exact8_unique_complete"] is True
    assert result["completed_human_positive_count"] == 8
    assert result["reactive_pair_human_authority_count"] == 8
    assert result["role_partition_human_authority_count"] == 8
    assert result["training_excluded_positive_count"] == 8
    assert result["training_include_count"] == 0
    assert result["future_training_admission_candidate_count"] == 0
    assert result["training_admitted_count"] == 0
    assert result["training_materialization_allowed_count"] == 0
    assert result["current_runtime_model_usable_count"] == 0
    assert result["published_global_positive_count_remains"] == 66
    assert result["global_reconciliation_update_done"] is False
    assert result["global_census_update_done"] is False
    assert result["ready_for_training"] is False
