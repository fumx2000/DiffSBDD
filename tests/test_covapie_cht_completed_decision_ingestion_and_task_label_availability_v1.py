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
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v1
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


def _remove_b(document: dict[str, object]) -> None:
    document["canonical_Exact5_and_sample_applicability"]["tasks"].pop(1)  # type: ignore[index,union-attr]


def _remove_b2(document: dict[str, object]) -> None:
    document["canonical_Exact5_and_sample_applicability"]["tasks"].pop(2)  # type: ignore[index,union-attr]


def _add_sixth_task(document: dict[str, object]) -> None:
    exact5 = document["canonical_Exact5_and_sample_applicability"]  # type: ignore[index]
    exact5["task_count"] = 6
    exact5["sixth_task_present"] = True
    exact5["tasks"].append(  # type: ignore[union-attr]
        {
            "task_id": 5,
            "semantic_name": "forbidden",
            "display_alias": "X",
            "structurally_applicable": True,
        }
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
    (
        "approval_timestamp",
        _path_mutation(
            ("human_approval", "approved_at_utc"),
            "2026-08-28T08:07:27Z",
        ),
    ),
    ("exact5_missing", _remove_event),
    ("exact5_duplicate", _duplicate_event),
    ("exact5_extra", _extra_event),
    (
        "canonical_event_id_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "canonical_event_id"),
            "wrong",
        ),
    ),
    (
        "rank_drift",
        _path_mutation(("event_level_human_decisions", 0, "scaleup_rank"), 596),
    ),
    (
        "pdb_drift",
        _path_mutation(("event_level_human_decisions", 0, "pdb_id"), "XXXX"),
    ),
    (
        "model_drift",
        _path_mutation(("event_level_human_decisions", 0, "model_number"), 2),
    ),
    (
        "protein_asym_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "protein_asym"),
            "Z",
        ),
    ),
    (
        "ligand_asym_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "ligand_asym"),
            "Z",
        ),
    ),
    (
        "protein_altloc_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "protein_altloc"),
            "B",
        ),
    ),
    (
        "ligand_altloc_drift",
        _path_mutation(("event_level_human_decisions", 0, "ligand_altloc"), "A"),
    ),
    (
        "CYS450_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "cys_residue_id"),
            "CYS:449-",
        ),
    ),
    (
        "second_CYS450_drift",
        _path_mutation(
            ("event_level_human_decisions", 1, "cys_residue_id"),
            "CYS:449-",
        ),
    ),
    (
        "event_context_count_collapse",
        _path_mutation(("event_context_inventory", "distinct_event_context_count"), 4),
    ),
    (
        "connection_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "selected_connection_id"),
            "covale999",
        ),
    ),
    (
        "post_distance_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "POST_distance_angstrom"),
            2.0,
        ),
    ),
    (
        "D1_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "D1"),
            "NOT_RELEVANT",
        ),
    ),
    (
        "D2_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "D2"),
            "NEGATIVE",
        ),
    ),
    (
        "negative_chemistry_true",
        _path_mutation(
            ("event_level_human_decisions", 0, "negative_chemistry"),
            True,
        ),
    ),
    (
        "task_domain_negative_true",
        _path_mutation(
            ("event_level_human_decisions", 0, "task_domain_negative"),
            True,
        ),
    ),
    (
        "D3_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "D3"),
            "OTHER",
        ),
    ),
    (
        "SG_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "protein_reactive_atom"),
            "CB",
        ),
    ),
    (
        "C4_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "ligand_reactive_atom"),
            "C2",
        ),
    ),
    (
        "C4_element_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "ligand_reactive_atom_element"),
            "N",
        ),
    ),
    (
        "D4_drift",
        _path_mutation(
            ("event_level_human_decisions", 0, "D4"),
            "SELECT_CANDIDATE_0",
        ),
    ),
    (
        "candidate2_drift",
        _path_mutation(
            ("selected_role_partition", "selected_candidate_index_0based"),
            0,
        ),
    ),
    (
        "warhead_drift",
        _path_mutation(("selected_role_partition", "warhead_atoms"), ["C4", "C5"]),
    ),
    (
        "source_warhead_order_drift",
        _path_mutation(
            ("selected_role_partition", "frozen_source_warhead_atoms_source_order"),
            ["O6", "C4"],
        ),
    ),
    (
        "linker_drift",
        _path_mutation(("selected_role_partition", "linker_atoms"), []),
    ),
    (
        "role_overlap",
        _path_mutation(("selected_role_partition", "linker_atoms"), ["C4"]),
    ),
    (
        "partition_non_exhaustive",
        _path_mutation(("selected_role_partition", "heavy_atom_exhaustive"), False),
    ),
    (
        "linker_disconnected",
        _path_mutation(("selected_role_partition", "linker_connected"), False),
    ),
    (
        "C4_outside_warhead",
        _path_mutation(("selected_role_partition", "warhead_atoms"), ["O6"]),
    ),
    (
        "scaffold_drift",
        _path_mutation(("selected_role_partition", "scaffold_atoms"), ["C6", "C7", "C8"]),
    ),
    (
        "boundary_drift",
        _path_mutation(
            ("selected_role_partition", "boundary_bonds", 0, "atom_id_1"),
            "C6",
        ),
    ),
    (
        "STRICT_to_DIRECT",
        _path_mutation(
            ("selected_role_partition", "role_profile"),
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        ),
    ),
    (
        "all_five_applicability",
        _path_mutation(
            ("selected_role_partition", "applicable_canonical_task_ids"),
            [0, 3, 4],
        ),
    ),
    ("B_missing", _remove_b),
    ("B2_missing", _remove_b2),
    ("B3_missing", _remove_b3),
    ("sixth_task", _add_sixth_task),
    (
        "D5_INCLUDE",
        _path_mutation(
            ("training_use_human_decision", "D5_human_choice"),
            "INCLUDE",
        ),
    ),
    (
        "human_training_excluded_false",
        _path_mutation(
            ("training_use_human_decision", "human_training_excluded"),
            False,
        ),
    ),
    (
        "training_use_include_true",
        _path_mutation(
            ("training_use_human_decision", "training_use_include"),
            True,
        ),
    ),
    (
        "training_use_allowed_true",
        _path_mutation(("training_use_human_decision", "training_use_allowed"), True),
    ),
    (
        "event_exception_true",
        _path_mutation(
            ("event_level_human_decisions", 0, "event_specific_disposition_exception"),
            True,
        ),
    ),
    (
        "D5_changes_applicability_true",
        _path_mutation(
            ("canonical_Exact5_and_sample_applicability", "D5_EXCLUDE_does_not_change_structural_applicability"),
            False,
        ),
    ),
    (
        "CCD_C4_O6_drift",
        _path_mutation(
            ("source_CCD_and_event_topology_boundary", "source_CCD_C4_O6_bond_order"),
            "DOUB",
        ),
    ),
    (
        "complete_POST_authority_true",
        _path_mutation(
            (
                "source_CCD_and_event_topology_boundary",
                "complete_POST_adduct_topology_authority_created",
            ),
            True,
        ),
    ),
    (
        "PRE_topology_true",
        _path_mutation(
            (
                "source_CCD_and_event_topology_boundary",
                "complete_PRE_topology_authority_created",
            ),
            True,
        ),
    ),
    (
        "PRE_C4_O6_true",
        _path_mutation(
            ("source_CCD_and_event_topology_boundary", "PRE_C4_O6_double_bond_authority_created"),
            True,
        ),
    ),
    (
        "PRE_reconstruction_true",
        _path_mutation(
            ("source_CCD_and_event_topology_boundary", "PRE_reconstruction_performed"),
            True,
        ),
    ),
    (
        "PRE_geometry_true",
        _path_mutation(("geometry_boundary", "PRE_geometry_authority_created"), True),
    ),
    (
        "POST_training_true",
        _path_mutation(
            ("geometry_boundary", "POST_geometry_training_authority_created"),
            True,
        ),
    ),
    (
        "reaction_family_true",
        _path_mutation(
            ("reaction_family_authority", "authority_created"),
            True,
        ),
    ),
    (
        "warhead_rule_true",
        _path_mutation(("warhead_rule_authority", "authority_created"), True),
    ),
    (
        "warhead_type_true",
        _path_mutation(("warhead_type_authority", "authority_created"), True),
    ),
    (
        "reusable_true",
        _path_mutation(
            ("reusable_authority_boundary", "reusable_chemistry_authority_created"),
            True,
        ),
    ),
    (
        "candidate_future_true",
        _path_mutation(
            ("training_use_human_decision", "future_training_admission_candidate"),
            True,
        ),
    ),
    (
        "training_admitted_true",
        _path_mutation(
            ("training_use_human_decision", "formal_training_admitted"),
            True,
        ),
    ),
    (
        "runtime_usable_true",
        _path_mutation(
            ("training_use_human_decision", "current_runtime_model_usable"),
            True,
        ),
    ),
)


def test_frozen_formal_binding_exact5_and_provenance() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    binding = bound["formal_decision_binding"]
    assert binding["path_namespace"] == "repository_parent_relative"
    assert binding["byte_count"] == 33307
    assert binding["sha256"] == subject.FORMAL_DECISION_SHA256
    assert binding["schema_version"] == subject.FORMAL_DECISION_SCHEMA
    assert binding["reviewer_id"] == binding["attestor_id"] == "fmx"
    assert binding["approved_at_utc"] == "2026-08-28T08:07:26Z"
    assert len(bound["frozen_review_package_bindings"]) == 6
    assert [row["mode"] for row in bound["frozen_review_package_bindings"]] == [
        "0644",
        "0644",
        "0644",
        "0644",
        "0644",
        "0755",
    ]
    assert len(bound["architecture_precedent_bindings"]) == 2
    assert len(bound["exclude_semantic_precedent_bindings"]) == 4
    events = bound["normalized"]["events"]
    assert len(events) == len({event["canonical_event_id"] for event in events}) == 5
    assert tuple(event["canonical_event_id"] for event in events) == subject.EXPECTED_EVENT_IDS


def test_candidate2_exact5_graph_science_and_topology_boundary() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    contexts = snapshot["event_context_inventory"]
    assert contexts["distinct_cys_residue_identities"] == ["CYS:450-"]
    assert contexts["distinct_event_context_count"] == 5
    assert contexts["contexts_collapsed"] is False
    role = snapshot["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 2
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["warhead_atoms"] == ["C4", "O6"]
    assert role["linker_atoms"] == ["C5"]
    assert role["scaffold_atoms"] == ["C6", "C7", "C8", "N1"]
    assert role["boundary_bonds"] == [
        {"atom_id_1": "C4", "atom_id_2": "C5", "bond_order": "SING", "boundary_between_roles": ["warhead", "linker"]},
        {"atom_id_1": "C5", "atom_id_2": "N1", "bond_order": "SING", "boundary_between_roles": ["linker", "scaffold"]},
    ]
    tasks = snapshot["canonical_task_contract"]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_created"] is False
    assert tasks["strict_profile_applicable_task_ids"] == [0, 1, 2, 3, 4]
    context = snapshot["scientific_context"]
    assert context["scope"] == "EXACT5_SAMPLE_LEVEL_HUMAN_APPROVED_CONTEXT_ONLY"
    assert context["target_directed_medicinal_covalent_inhibitor_context"] is False
    topology = snapshot["source_CCD_and_event_topology_boundary"]
    assert topology["source_CCD_C4_O6_bond_order"] == "SING"
    assert topology["explicit_observed_SG_C4_connection_event_count"] == 5
    assert topology["complete_POST_topology_authority_available"] is False
    assert topology["PRE_topology_authority_available"] is False
    assert topology["PRE_C4_O6_double_bond_authority_available"] is False


def test_EXCLUDE_is_separate_from_relevant_positive_and_admission() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    decisions = snapshot["unit_level_D1_D6"]
    training = snapshot["training_boundary"]
    assert decisions["D1"] == "RELEVANT"
    assert decisions["D2"] == "POSITIVE"
    assert decisions["D5"] == "EXCLUDE_FROM_TRAINING_ONLY"
    assert training["negative_chemistry"] is False
    assert training["task_domain_negative"] is False
    assert training["human_training_excluded"] is True
    assert training["training_use_allowed"] is False
    assert training["training_use_include"] is False
    assert training["candidate_for_future_training_admission"] is False
    assert training["future_training_admission_status"] is None
    assert training["training_admitted"] is False
    assert training["training_materialization_allowed_now"] is False
    assert training["current_runtime_model_usable"] is False
    assert training["ready_for_training"] is False


def test_matrix_summary_manifest_direct_evidence() -> None:
    artifacts = _artifacts()
    matrix = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode())))
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert len(matrix) == 5
    assert [int(row["scaleup_rank"]) for row in matrix] == list(subject.EXPECTED_RANKS)
    assert [row["cys_residue_id"] for row in matrix] == ["CYS:450-"] * 5
    assert all(row["protein_reactive_atom"] == "SG" for row in matrix)
    assert all(row["ligand_reactive_atom"] == "C4" for row in matrix)
    assert all(row["ligand_reactive_atom_element"] == "C" for row in matrix)
    assert all(
        row["formal_event_training_use_decision"]
        == "EXCLUDE_FROM_TRAINING_ONLY"
        for row in matrix
    )
    assert all(row["human_training_excluded"] == "true" for row in matrix)
    assert all(row["training_use_allowed"] == "false" for row in matrix)
    assert all(
        row["candidate_for_future_training_admission"] == "false"
        for row in matrix
    )
    assert all(row["training_admitted"] == "false" for row in matrix)
    assert summary["event_count"] == summary["chemistry_positive_count"] == 5
    assert summary["human_training_EXCLUDE_count"] == 5
    assert summary["future_training_admission_candidate_count"] == 0
    assert summary["training_admitted_count"] == 0
    assert summary["published_global_positive_count_remains"] == 95
    assert summary["published_task_relevant_count_remains"] == 96
    assert summary["published_training_EXCLUDE_count_remains"] == 59
    assert summary["published_training_INCLUDE_count_remains"] == 36
    assert summary["published_future_training_candidate_count_remains"] == 19
    assert len(manifest["exclude_semantic_precedent_bindings"]) == 4
    assert len(manifest["current_published_census_bindings"]) == 4
    assert "sha256" not in manifest


def test_exact4_outputs_are_deterministic_in_two_directories(tmp_path: Path) -> None:
    first = tmp_path / "a"
    second = tmp_path / "b"
    one = subject.materialize_artifacts_v1(ROOT, output_root=first)
    two = subject.materialize_artifacts_v1(ROOT, output_root=second)
    assert one == two
    assert all(
        (first / name).read_bytes() == (second / name).read_bytes()
        for name in subject.OUTPUT_FILENAMES
    )


def test_public_standalone_validator_accepts_exact_current_artifacts() -> None:
    subject.validate_completed_decision_projection_v1(_artifacts())


COORDINATED_OUTPUT_MUTATIONS = (
    ("D1", ("unit_level_D1_D6", "D1"), "NOT_RELEVANT"),
    ("D2", ("unit_level_D1_D6", "D2"), "NEGATIVE"),
    ("context_collapse", ("event_context_inventory", "contexts_collapsed"), True),
    ("context_count", ("event_context_inventory", "distinct_event_context_count"), 4),
    ("SG", ("reactive_pair", "protein_reactive_atom"), "CB"),
    ("C4", ("reactive_pair", "ligand_reactive_atom"), "C2"),
    ("C4_element", ("reactive_pair", "ligand_reactive_atom_element"), "N"),
    ("candidate2", ("selected_role_partition", "selected_candidate_index_0based"), 0),
    ("W", ("selected_role_partition", "warhead_atoms"), ["C4", "C5"]),
    ("L", ("selected_role_partition", "linker_atoms"), []),
    ("S", ("selected_role_partition", "scaffold_atoms"), ["C6", "C7", "C8"]),
    ("STRICT_DIRECT", ("selected_role_partition", "role_profile"), "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
    ("applicability", ("canonical_task_contract", "strict_profile_applicable_task_ids"), [0, 3, 4]),
    ("B3_missing", ("canonical_task_contract", "B3_present"), False),
    ("sixth_task", ("canonical_task_contract", "sixth_task_created"), True),
    ("D5", ("training_boundary", "formal_event_training_use_decision"), "INCLUDE"),
    ("human_excluded", ("training_boundary", "human_training_excluded"), False),
    ("training_allowed", ("training_boundary", "training_use_allowed"), True),
    ("candidate_future", ("training_boundary", "candidate_for_future_training_admission"), True),
    ("training_admitted", ("training_boundary", "training_admitted"), True),
    ("CCD_C4_O6", ("source_CCD_and_event_topology_boundary", "source_CCD_C4_O6_bond_order"), "DOUB"),
    ("complete_POST", ("source_CCD_and_event_topology_boundary", "complete_POST_topology_authority_available"), True),
    ("PRE_topology", ("source_CCD_and_event_topology_boundary", "PRE_topology_authority_available"), True),
    ("PRE_C4_O6", ("source_CCD_and_event_topology_boundary", "PRE_C4_O6_double_bond_authority_available"), True),
    ("PRE_geometry", ("source_CCD_and_event_topology_boundary", "PRE_geometry_authority_available"), True),
    ("reaction_family", ("auxiliary_and_reusable_boundary", "reaction_family_target_available"), True),
    ("warhead_rule", ("auxiliary_and_reusable_boundary", "warhead_rule_target_available"), True),
    ("warhead_type", ("auxiliary_and_reusable_boundary", "warhead_type_target_available"), True),
    ("reusable", ("auxiliary_and_reusable_boundary", "reusable_chemistry_authority_available"), True),
)


@pytest.mark.parametrize(
    "case,path,value",
    COORDINATED_OUTPUT_MUTATIONS,
    ids=[row[0] for row in COORDINATED_OUTPUT_MUTATIONS],
)
def test_standalone_rejects_coordinated_snapshot_and_manifest_sha_drift(
    case: str,
    path: tuple[object, ...],
    value: object,
) -> None:
    del case
    artifacts = _artifacts()
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set_path(snapshot, path, value)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = _sha(  # type: ignore[index]
        artifacts[subject.SNAPSHOT]
    )
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.CHTIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


EXCLUDE_OUTPUT_MUTATIONS = (
    ("negative_true", ("training_boundary", "negative_chemistry"), True),
    ("task_negative_true", ("training_boundary", "task_domain_negative"), True),
    ("training_allowed_true", ("training_boundary", "training_use_allowed"), True),
    ("candidate_true", ("training_boundary", "candidate_for_future_training_admission"), True),
    ("admitted_true", ("training_boundary", "training_admitted"), True),
    ("runtime_true", ("training_boundary", "current_runtime_model_usable"), True),
)


@pytest.mark.parametrize(
    "case,path,value",
    EXCLUDE_OUTPUT_MUTATIONS,
    ids=[row[0] for row in EXCLUDE_OUTPUT_MUTATIONS],
)
def test_EXCLUDE_specific_separation_mutations_fail_closed(
    case: str,
    path: tuple[object, ...],
    value: object,
) -> None:
    del case
    artifacts = _artifacts()
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set_path(snapshot, path, value)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = _sha(  # type: ignore[index]
        artifacts[subject.SNAPSHOT]
    )
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.CHTIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_frozen_derived_projection_digests_match_current_artifacts() -> None:
    artifacts = _artifacts()
    assert _sha(artifacts[subject.SNAPSHOT]) == subject._EXPECTED_SNAPSHOT_SHA256_V1
    assert _sha(artifacts[subject.MATRIX]) == subject._EXPECTED_MATRIX_SHA256_V1
    assert _sha(artifacts[subject.SUMMARY]) == subject._EXPECTED_SUMMARY_SHA256_V1


def test_formal_payload_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(FORMAL.read_bytes() + b"\n")
    with pytest.raises(subject.CHTIngestionSafetyError, match="BYTE_COUNT"):
        subject.load_frozen_formal_decision_v1(
            ROOT,
            formal_decision_path=mutated,
        )


def test_formal_payload_same_size_sha_mutation_fails_closed(tmp_path: Path) -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[-2] = 0x20 if payload[-2] != 0x20 else 0x09
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(payload)
    assert len(payload) == subject.FORMAL_DECISION_BYTE_COUNT
    with pytest.raises(subject.CHTIngestionSafetyError, match="SHA256"):
        subject.load_frozen_formal_decision_v1(
            ROOT,
            formal_decision_path=mutated,
        )


@pytest.mark.parametrize(
    "case,mutate",
    FORMAL_MUTATIONS,
    ids=[row[0] for row in FORMAL_MUTATIONS],
)
def test_formal_semantic_drift_fails_closed(case: str, mutate) -> None:
    del case
    formal = _formal_dict()
    mutate(formal)
    with pytest.raises(subject.CHTIngestionSafetyError):
        subject._validate_formal_decision_v1(formal)


def test_frozen_evidence_same_size_sha_drift_fails_closed(tmp_path: Path) -> None:
    relative = subject.FROZEN_REVIEW_PACKAGE_BINDINGS[0][0]
    source = ROOT.parent / relative
    payload = bytearray(source.read_bytes())
    payload[0] = 0x20 if payload[0] != 0x20 else 0x09
    mutated = tmp_path / source.name
    mutated.write_bytes(payload)
    assert len(payload) == subject.FROZEN_REVIEW_PACKAGE_BINDINGS[0][1]
    with pytest.raises(subject.CHTIngestionSafetyError, match="SHA256"):
        subject.load_frozen_formal_decision_v1(
            ROOT,
            repository_path_overrides={relative: mutated},
        )


@pytest.mark.parametrize(
    "path",
    (
        ("authority_boundary", "reaction_family_authority_created"),
        ("authority_boundary", "warhead_rule_authority_created"),
        ("authority_boundary", "warhead_type_authority_created"),
        ("authority_boundary", "reusable_chemistry_authority_created"),
        ("authority_boundary", "reusable_pair_authority_created"),
        ("authority_boundary", "reusable_role_authority_created"),
        ("authority_boundary", "complete_POST_topology_authority_created"),
        ("authority_boundary", "PRE_topology_authority_created"),
        ("authority_boundary", "PRE_geometry_authority_created"),
        ("authority_boundary", "POST_geometry_training_authority_created"),
        ("authority_boundary", "training_admission_created"),
        ("authority_boundary", "candidate_for_future_training_admission"),
        ("authority_boundary", "training_materialization_allowed_now"),
        ("authority_boundary", "current_runtime_model_usable"),
        ("authority_boundary", "formal_split_authority_created"),
        ("authority_boundary", "tensor_target_created"),
        ("authority_boundary", "parameter_update_authorization"),
        ("authority_boundary", "global_reconciliation_updated"),
        ("authority_boundary", "global_census_updated"),
    ),
)
def test_output_authority_non_action_mutations_fail_closed(
    path: tuple[object, ...],
) -> None:
    artifacts = _artifacts()
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set_path(snapshot, path, True)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = _sha(  # type: ignore[index]
        artifacts[subject.SNAPSHOT]
    )
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.CHTIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_dynamic_metadata_is_rejected() -> None:
    artifacts = _artifacts()
    summary = json.loads(artifacts[subject.SUMMARY])
    summary["generated_at_utc"] = "2026-08-28T03:37:02Z"
    artifacts[subject.SUMMARY] = subject._json_bytes(summary)
    with pytest.raises(subject.CHTIngestionSafetyError, match="DYNAMIC"):
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
        "__name__": "check_covapie_cht_ingestion_v1",
    }
    exec(compile(checker.read_bytes(), checker.as_posix(), "exec"), namespace)
    result = namespace["run_check_v1"](ROOT)  # type: ignore[operator]
    assert result["candidate_publication_file_count"] == 7
    assert result["exact5_unique_complete"] is True
    assert result["exclude_semantic_precedents_verified"] is True
    assert result["derived_projection_digests_verified"] is True
    assert result["current_census_preserved_and_bound"] is True
    assert result["published_global_positive_count_remains"] == 95
    assert result["published_task_relevant_count_remains"] == 96
    assert result["published_training_INCLUDE_count_remains"] == 36
    assert result["published_training_EXCLUDE_count_remains"] == 59
    assert result["published_future_training_candidate_count_remains"] == 19
    assert result["ready_for_CHT_reconciliation_successor"] is True
    assert result["ready_for_training"] is False
