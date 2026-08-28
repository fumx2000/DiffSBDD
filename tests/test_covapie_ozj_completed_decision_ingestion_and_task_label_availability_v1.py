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
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
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


def _remove_task(index: int):
    def mutate(document: dict[str, object]) -> None:
        document["canonical_Exact5_and_sample_applicability"]["tasks"].pop(  # type: ignore[index,union-attr]
            index
        )

    return mutate


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
    ("schema", _path_mutation(("schema_version",), "wrong")),
    ("review_unit", _path_mutation(("review_unit_id",), "wrong")),
    ("reviewer", _path_mutation(("reviewer_id",), "other")),
    ("attestor", _path_mutation(("attestor_id",), "other")),
    (
        "approval_timestamp",
        _path_mutation(
            ("human_approval", "approved_at_utc"),
            "2026-08-28T14:03:17Z",
        ),
    ),
    ("approved_false", _path_mutation(("approved",), False)),
    ("unsigned_true", _path_mutation(("unsigned",), True)),
    ("missing_event", _remove_event),
    ("duplicate_event", _duplicate_event),
    ("extra_event", _extra_event),
    (
        "event_id",
        _path_mutation(
            ("event_level_human_decisions", 0, "canonical_event_id"), "wrong"
        ),
    ),
    (
        "rank",
        _path_mutation(
            ("event_level_human_decisions", 0, "scaleup_rank"), 999
        ),
    ),
    (
        "pdb",
        _path_mutation(
            ("event_level_human_decisions", 0, "pdb_id"), "XXXX"
        ),
    ),
    (
        "model",
        _path_mutation(
            ("event_level_human_decisions", 0, "model_number"), 2
        ),
    ),
    (
        "protein_asym",
        _path_mutation(
            ("event_level_human_decisions", 0, "protein_asym"), "Z"
        ),
    ),
    (
        "ligand_asym",
        _path_mutation(
            ("event_level_human_decisions", 0, "ligand_asym"), "Z"
        ),
    ),
    (
        "protein_altloc",
        _path_mutation(
            ("event_level_human_decisions", 0, "protein_altloc"), "A"
        ),
    ),
    (
        "ligand_altloc",
        _path_mutation(
            ("event_level_human_decisions", 0, "ligand_altloc"), "A"
        ),
    ),
    (
        "connection",
        _path_mutation(
            ("event_level_human_decisions", 0, "selected_connection_id"),
            "covale999",
        ),
    ),
    (
        "distance",
        _path_mutation(
            ("event_level_human_decisions", 0, "POST_distance_angstrom"), 2.0
        ),
    ),
    (
        "D1",
        _path_mutation(
            ("event_level_human_decisions", 0, "D1_task_relevance"),
            "NOT_RELEVANT",
        ),
    ),
    (
        "D2",
        _path_mutation(
            ("event_level_human_decisions", 0, "D2_chemistry"), "NEGATIVE"
        ),
    ),
    (
        "D3",
        _path_mutation(
            ("event_level_human_decisions", 0, "D3_reactive_pair"), "OTHER"
        ),
    ),
    (
        "D4",
        _path_mutation(
            ("event_level_human_decisions", 0, "D4_role_partition"),
            "SELECT_CANDIDATE_0",
        ),
    ),
    (
        "D5",
        _path_mutation(
            ("event_level_human_decisions", 0, "D5_training_use"),
            "EXCLUDE_FROM_TRAINING_ONLY",
        ),
    ),
    (
        "SG",
        _path_mutation(
            ("event_level_human_decisions", 0, "protein_reactive_atom"), "CB"
        ),
    ),
    (
        "CAF",
        _path_mutation(
            ("event_level_human_decisions", 0, "ligand_reactive_atom"), "C2"
        ),
    ),
    (
        "CAF_element",
        _path_mutation(
            (
                "event_level_human_decisions",
                0,
                "ligand_reactive_atom_element",
            ),
            "N",
        ),
    ),
    (
        "candidate1",
        _path_mutation(
            ("selected_role_partition", "selected_candidate_index_0based"), 0
        ),
    ),
    (
        "warhead",
        _path_mutation(
            ("selected_role_partition", "warhead_atoms"), ["CAF", "CAP"]
        ),
    ),
    (
        "linker",
        _path_mutation(("selected_role_partition", "linker_atoms"), []),
    ),
    (
        "scaffold",
        _path_mutation(
            ("selected_role_partition", "scaffold_atoms"), ["C2"]
        ),
    ),
    (
        "role_overlap",
        _path_mutation(
            ("selected_role_partition", "linker_atoms"), ["CAF"]
        ),
    ),
    (
        "non_exhaustive",
        _path_mutation(
            ("selected_role_partition", "heavy_atom_exhaustive"), False
        ),
    ),
    (
        "fake_boundary",
        _path_mutation(
            ("selected_role_partition", "boundary_bonds", 0, "atom_id_1"),
            "C2",
        ),
    ),
    (
        "CAF_outside_W",
        _path_mutation(
            ("selected_role_partition", "CAF_in_warhead"), False
        ),
    ),
    (
        "STRICT_to_DIRECT",
        _path_mutation(
            ("selected_role_partition", "role_profile"),
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        ),
    ),
    ("missing_B", _remove_task(1)),
    ("missing_B2", _remove_task(2)),
    ("missing_B3", _remove_task(3)),
    ("sixth_task", _add_sixth_task),
    (
        "formal_future_false",
        _path_mutation(
            (
                "training_use_human_decision",
                "future_training_admission_candidate",
            ),
            False,
        ),
    ),
    (
        "formal_future_true",
        _path_mutation(
            (
                "training_use_human_decision",
                "future_training_admission_candidate",
            ),
            True,
        ),
    ),
    (
        "formal_future_wrong_status",
        _path_mutation(
            (
                "training_use_human_decision",
                "future_training_admission_candidate_status",
            ),
            "WRONG",
        ),
    ),
    (
        "include_allowed_false",
        _path_mutation(
            ("training_use_human_decision", "training_use_allowed"), False
        ),
    ),
    (
        "formal_admitted",
        _path_mutation(
            ("training_use_human_decision", "formal_training_admitted"), True
        ),
    ),
    (
        "CAF_OAD",
        _path_mutation(
            (
                "source_CCD_and_event_topology_boundary",
                "source_CAF_OAD_bond_order",
            ),
            "SING",
        ),
    ),
    (
        "complete_POST",
        _path_mutation(
            (
                "source_CCD_and_event_topology_boundary",
                "complete_POST_adduct_topology_authority_created",
            ),
            True,
        ),
    ),
    (
        "PRE_topology",
        _path_mutation(
            (
                "source_CCD_and_event_topology_boundary",
                "PRE_precursor_topology_authority_created",
            ),
            True,
        ),
    ),
    (
        "PRE_geometry",
        _path_mutation(
            ("geometry_boundary", "PRE_geometry_authority_created"), True
        ),
    ),
    (
        "POST_training",
        _path_mutation(
            (
                "geometry_boundary",
                "POST_geometry_training_authority_created",
            ),
            True,
        ),
    ),
    (
        "reaction_family",
        _path_mutation(
            ("reaction_family_authority", "authority_created"), True
        ),
    ),
    (
        "warhead_rule",
        _path_mutation(
            ("warhead_rule_authority", "authority_created"), True
        ),
    ),
    (
        "warhead_type",
        _path_mutation(
            ("warhead_type_authority", "authority_created"), True
        ),
    ),
    (
        "reusable",
        _path_mutation(
            (
                "reusable_authority_boundary",
                "reusable_chemistry_authority_created",
            ),
            True,
        ),
    ),
    (
        "runtime",
        _path_mutation(
            ("training_use_human_decision", "runtime_model_usable"), True
        ),
    ),
)


def test_frozen_formal_binding_exact4_and_provenance() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    binding = bound["formal_decision_binding"]
    assert binding["path_namespace"] == "repository_parent_relative"
    assert binding["byte_count"] == 28914
    assert binding["sha256"] == subject.FORMAL_DECISION_SHA256
    assert binding["schema_version"] == subject.FORMAL_DECISION_SCHEMA
    assert binding["reviewer_id"] == binding["attestor_id"] == "fmx"
    assert binding["approved_at_utc"] == "2026-08-28T14:03:16Z"
    assert len(bound["frozen_review_package_bindings"]) == 6
    assert [row["mode"] for row in bound["frozen_review_package_bindings"]] == [
        "0664"
    ] * 6
    assert len(bound["architecture_precedent_bindings"]) == 2
    assert len(bound["include_semantic_precedent_bindings"]) == 3
    events = bound["normalized"]["events"]
    assert len(events) == len({event["canonical_event_id"] for event in events}) == 4
    assert tuple(event["canonical_event_id"] for event in events) == (
        subject.EXPECTED_EVENT_IDS
    )


def test_candidate1_strict_exact5_graph_science_and_topology() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    role = snapshot["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 1
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["warhead_atoms"] == ["CAF", "OAD"]
    assert role["linker_atoms"] == [
        "CAG", "CAH", "CAI", "CAJ", "CAP", "CAQ"
    ]
    assert role["scaffold_atoms"] == [
        "C2", "C4", "C5", "C6", "CAE", "CAR", "CAS",
        "N1", "N3", "NAA", "NAB", "NAC", "NAM",
    ]
    assert role["boundary_bonds"] == [
        {
            "atom_id_1": "CAF", "atom_id_2": "CAP",
            "bond_order": "SING",
            "boundary_between_roles": ["warhead", "linker"],
        },
        {
            "atom_id_1": "CAQ", "atom_id_2": "CAS",
            "bond_order": "SING",
            "boundary_between_roles": ["linker", "scaffold"],
        },
    ]
    tasks = snapshot["canonical_task_contract"]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_created"] is False
    assert tasks["strict_profile_applicable_task_ids"] == [0, 1, 2, 3, 4]
    context = snapshot["scientific_context"]
    assert context["scope"] == "EXACT4_SAMPLE_LEVEL_HUMAN_APPROVED_CONTEXT_ONLY"
    assert context["target_directed_TbPTR1_context"] is True
    topology = snapshot["source_CCD_and_event_topology_boundary"]
    assert topology["source_CAF_OAD_bond_order"] == "DOUB"
    assert topology["explicit_observed_SG_CAF_connection_event_count"] == 4
    assert topology["complete_POST_topology_authority_available"] is False
    assert topology["PRE_topology_authority_available"] is False
    assert topology["PRE_geometry_authority_available"] is False


def test_include_formal_null_becomes_ingestion_candidate_not_admission() -> None:
    snapshot = json.loads(_artifacts()[subject.SNAPSHOT])
    formal = snapshot["formal_training_use_source_boundary"]
    ingestion = snapshot["downstream_ingestion_boundary"]
    assert formal["formal_event_training_use_decision"] == "INCLUDE"
    assert formal["future_training_admission_candidate"] is None
    assert (
        formal["future_training_admission_candidate_status"]
        == subject.FORMAL_FUTURE_STATUS
    )
    assert formal["formal_training_admitted"] is False
    assert ingestion["human_training_excluded"] is False
    assert ingestion["training_use_allowed"] is True
    assert ingestion["training_use_include"] is True
    assert ingestion["candidate_for_future_training_admission"] is True
    assert ingestion["future_training_admission_status"] == subject.FUTURE_STATUS
    assert ingestion["future_training_candidate_derived_by_ingestion"] is True
    assert (
        ingestion["future_training_candidate_is_training_admission"] is False
    )
    assert ingestion["training_admitted"] is False
    assert ingestion["training_materialization_allowed_now"] is False
    assert ingestion["current_runtime_model_usable"] is False
    assert ingestion["ready_for_training"] is False


def test_matrix_summary_manifest_direct_evidence() -> None:
    artifacts = _artifacts()
    matrix = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode()))
    )
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert len(matrix) == 4
    assert [int(row["scaleup_rank"]) for row in matrix] == list(
        subject.EXPECTED_RANKS
    )
    assert all(row["protein_reactive_atom"] == "SG" for row in matrix)
    assert all(row["ligand_reactive_atom"] == "CAF" for row in matrix)
    assert all(
        row["formal_future_training_admission_candidate"] == "null"
        for row in matrix
    )
    assert all(
        row["candidate_for_future_training_admission"] == "true"
        for row in matrix
    )
    assert all(row["training_admitted"] == "false" for row in matrix)
    assert summary["event_count"] == summary["chemistry_positive_count"] == 4
    assert summary["human_training_INCLUDE_count"] == 4
    assert summary["future_training_admission_candidate_count"] == 4
    assert summary["training_admitted_count"] == 0
    assert summary["published_global_positive_count_remains"] == 100
    assert summary["published_task_relevant_count_remains"] == 101
    assert summary["published_training_INCLUDE_count_remains"] == 36
    assert summary["published_training_EXCLUDE_count_remains"] == 64
    assert summary["published_future_training_candidate_count_remains"] == 19
    assert len(manifest["include_semantic_precedent_bindings"]) == 3
    assert len(manifest["current_published_census_bindings"]) == 4
    assert "sha256" not in manifest


def test_exact4_outputs_are_deterministic_in_two_directories(
    tmp_path: Path,
) -> None:
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
    ("SG", ("reactive_pair", "protein_reactive_atom"), "CB"),
    ("CAF", ("reactive_pair", "ligand_reactive_atom"), "C2"),
    (
        "candidate1",
        ("selected_role_partition", "selected_candidate_index_0based"),
        0,
    ),
    ("W", ("selected_role_partition", "warhead_atoms"), ["CAF", "CAP"]),
    ("L", ("selected_role_partition", "linker_atoms"), []),
    ("S", ("selected_role_partition", "scaffold_atoms"), ["C2"]),
    (
        "boundary",
        ("selected_role_partition", "boundary_bonds", 0, "atom_id_1"),
        "C2",
    ),
    (
        "STRICT_DIRECT",
        ("selected_role_partition", "role_profile"),
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
    ),
    (
        "B3_missing",
        ("canonical_task_contract", "B3_present"),
        False,
    ),
    (
        "sixth_task",
        ("canonical_task_contract", "sixth_task_created"),
        True,
    ),
    (
        "D5",
        ("formal_training_use_source_boundary", "formal_event_training_use_decision"),
        "EXCLUDE_FROM_TRAINING_ONLY",
    ),
    (
        "formal_future_false",
        ("formal_training_use_source_boundary", "future_training_admission_candidate"),
        False,
    ),
    (
        "formal_future_true",
        ("formal_training_use_source_boundary", "future_training_admission_candidate"),
        True,
    ),
    (
        "deferred_status",
        (
            "formal_training_use_source_boundary",
            "future_training_admission_candidate_status",
        ),
        "WRONG",
    ),
    (
        "derived_future_false",
        (
            "downstream_ingestion_boundary",
            "candidate_for_future_training_admission",
        ),
        False,
    ),
    (
        "future_status",
        ("downstream_ingestion_boundary", "future_training_admission_status"),
        "WRONG",
    ),
    (
        "future_is_admission",
        (
            "downstream_ingestion_boundary",
            "future_training_candidate_is_training_admission",
        ),
        True,
    ),
    (
        "training_admitted",
        ("downstream_ingestion_boundary", "training_admitted"),
        True,
    ),
    (
        "CAF_OAD",
        ("source_CCD_and_event_topology_boundary", "source_CAF_OAD_bond_order"),
        "SING",
    ),
    (
        "complete_POST",
        (
            "source_CCD_and_event_topology_boundary",
            "complete_POST_topology_authority_available",
        ),
        True,
    ),
    (
        "PRE_topology",
        (
            "source_CCD_and_event_topology_boundary",
            "PRE_topology_authority_available",
        ),
        True,
    ),
    (
        "PRE_geometry",
        (
            "source_CCD_and_event_topology_boundary",
            "PRE_geometry_authority_available",
        ),
        True,
    ),
    (
        "warhead_type",
        ("auxiliary_and_reusable_boundary", "warhead_type_target_available"),
        True,
    ),
    (
        "reaction_family",
        ("auxiliary_and_reusable_boundary", "reaction_family_target_available"),
        True,
    ),
    (
        "reusable",
        (
            "auxiliary_and_reusable_boundary",
            "reusable_chemistry_authority_available",
        ),
        True,
    ),
)


@pytest.mark.parametrize(
    "case,path,value",
    COORDINATED_OUTPUT_MUTATIONS,
    ids=[row[0] for row in COORDINATED_OUTPUT_MUTATIONS],
)
def test_standalone_rejects_coordinated_snapshot_and_manifest_sha_drift(
    case: str, path: tuple[object, ...], value: object
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
    with pytest.raises(
        subject.OZJIngestionSafetyError,
        match="SNAPSHOT_EXACT_SOURCE_PROJECTION_INVALID",
    ):
        subject.validate_completed_decision_projection_v1(artifacts)


INCLUDE_OUTPUT_MUTATIONS = (
    (
        "candidate_false",
        ("downstream_ingestion_boundary", "candidate_for_future_training_admission"),
        False,
    ),
    (
        "status_wrong",
        ("downstream_ingestion_boundary", "future_training_admission_status"),
        "WRONG",
    ),
    (
        "is_admission_true",
        (
            "downstream_ingestion_boundary",
            "future_training_candidate_is_training_admission",
        ),
        True,
    ),
    (
        "admitted_true",
        ("downstream_ingestion_boundary", "training_admitted"),
        True,
    ),
    (
        "allowed_false",
        ("downstream_ingestion_boundary", "training_use_allowed"),
        False,
    ),
)


@pytest.mark.parametrize(
    "case,path,value",
    INCLUDE_OUTPUT_MUTATIONS,
    ids=[row[0] for row in INCLUDE_OUTPUT_MUTATIONS],
)
def test_include_specific_output_mutations_fail_closed(
    case: str, path: tuple[object, ...], value: object
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
    with pytest.raises(subject.OZJIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_frozen_derived_projection_digests_match_current_artifacts() -> None:
    artifacts = _artifacts()
    assert (
        _sha(artifacts[subject.SNAPSHOT])
        == subject._EXPECTED_SNAPSHOT_SHA256_V1
    )
    assert (
        _sha(artifacts[subject.MATRIX])
        == subject._EXPECTED_MATRIX_SHA256_V1
    )
    assert (
        _sha(artifacts[subject.SUMMARY])
        == subject._EXPECTED_SUMMARY_SHA256_V1
    )


def test_formal_payload_wrong_byte_count_fails_closed(
    tmp_path: Path,
) -> None:
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(FORMAL.read_bytes() + b"\n")
    with pytest.raises(subject.OZJIngestionSafetyError, match="BYTE_COUNT"):
        subject.load_frozen_formal_decision_v1(
            ROOT, formal_decision_path=mutated
        )


def test_formal_payload_same_size_sha_mutation_fails_closed(
    tmp_path: Path,
) -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[-2] = 0x20 if payload[-2] != 0x20 else 0x09
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(payload)
    assert len(payload) == subject.FORMAL_DECISION_BYTE_COUNT
    with pytest.raises(subject.OZJIngestionSafetyError, match="SHA256"):
        subject.load_frozen_formal_decision_v1(
            ROOT, formal_decision_path=mutated
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
    with pytest.raises(subject.OZJIngestionSafetyError):
        subject._validate_formal_decision_v1(formal)


def test_frozen_evidence_same_size_sha_drift_fails_closed(
    tmp_path: Path,
) -> None:
    relative = subject.FROZEN_REVIEW_PACKAGE_BINDINGS[0][0]
    source = ROOT.parent / relative
    payload = bytearray(source.read_bytes())
    payload[0] = 0x20 if payload[0] != 0x20 else 0x09
    mutated = tmp_path / source.name
    mutated.write_bytes(payload)
    assert len(payload) == subject.FROZEN_REVIEW_PACKAGE_BINDINGS[0][1]
    with pytest.raises(subject.OZJIngestionSafetyError, match="SHA256"):
        subject.load_frozen_formal_decision_v1(
            ROOT, repository_path_overrides={relative: mutated}
        )


def test_dynamic_metadata_is_rejected() -> None:
    artifacts = _artifacts()
    summary = json.loads(artifacts[subject.SUMMARY])
    summary["generated_at_utc"] = "2026-08-28T14:03:16Z"
    artifacts[subject.SUMMARY] = subject._json_bytes(summary)
    with pytest.raises(subject.OZJIngestionSafetyError, match="DYNAMIC"):
        subject.validate_completed_decision_projection_v1(artifacts)


def test_current_published_census_is_bound_and_unchanged() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    assert (
        bound["current_published_census_bindings"]
        == subject._expected_census_bindings()
    )
    for relative, byte_count, sha256, _role in subject.CURRENT_CENSUS_BINDINGS:
        payload = (ROOT / relative).read_bytes()
        assert len(payload) == byte_count
        assert _sha(payload) == sha256


def test_materialized_exact7_checker() -> None:
    checker = ROOT / subject.CHECKER_RELATIVE
    namespace: dict[str, object] = {
        "__file__": checker.as_posix(),
        "__name__": "check_covapie_ozj_ingestion_v1",
    }
    exec(compile(checker.read_bytes(), checker.as_posix(), "exec"), namespace)
    result = namespace["run_check_v1"](ROOT)  # type: ignore[operator]
    assert result["candidate_publication_file_count"] == 7
    assert result["exact4_unique_complete"] is True
    assert result["include_semantic_precedent_verified"] is True
    assert result["derived_projection_digests_verified"] is True
    assert result["current_census_preserved_and_bound"] is True
    assert result["published_global_positive_count_remains"] == 100
    assert result["published_task_relevant_count_remains"] == 101
    assert result["published_training_INCLUDE_count_remains"] == 36
    assert result["published_training_EXCLUDE_count_remains"] == 64
    assert result["published_future_training_candidate_count_remains"] == 19
    assert result["ready_for_OZJ_reconciliation_successor"] is True
    assert result["ready_for_training"] is False
