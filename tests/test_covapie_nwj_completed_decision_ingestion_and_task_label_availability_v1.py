from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_nwj_ingestion_v1_for_tests", REPO_ROOT / owner.CHECKER_RELATIVE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen_formal() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes()
    )


def mutate_path(document: dict[str, object], path: tuple[object, ...], value: object) -> None:
    cursor: object = document
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[path[-1]] = value  # type: ignore[index]


def json_artifact_mutation(
    artifacts: dict[str, bytes], filename: str, path: tuple[object, ...], value: object
) -> dict[str, bytes]:
    changed = dict(artifacts)
    document = json.loads(changed[filename])
    mutate_path(document, path, value)
    changed[filename] = owner._json_bytes(document)
    return changed


def test_public_api_is_exact_and_inventory_is_exact7() -> None:
    assert owner.__all__ == (
        "NWJIngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )
    assert owner.SCHEMA_VERSION == (
        "covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1"
    )
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert len(owner.OUTPUT_RELATIVE_PATHS) == 4
    assert {path.name for path in owner.OUTPUT_RELATIVE_PATHS} == set(
        owner.OUTPUT_FILENAMES
    )
    assert all((REPO_ROOT / path).is_file() for path in owner.CANDIDATE_PUBLICATION_PATHS)


def test_formal_exact2_source_identity_is_frozen() -> None:
    formal_path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    validator_path = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    formal = formal_path.read_bytes()
    validator = validator_path.read_bytes()
    assert len(formal) == 24265
    assert hashlib.sha256(formal).hexdigest() == (
        "1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff"
    )
    assert len(validator) == 68924
    assert hashlib.sha256(validator).hexdigest() == (
        "1cc1bb5ea615bcf662ac1410dc15ef3aa82991e6243dec461cb8ada20078336d"
    )
    assert owner.FORMAL_BINDINGS[0][6] == (
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY"
    )
    assert owner.FORMAL_BINDINGS[1][6] == (
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
    )


def test_formal_validator_is_never_imported_executed_or_subprocessed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = importlib.import_module

    def guarded_import(name: str, *args, **kwargs):
        assert "validate_nwj_formal_human_decision_v1" not in name
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(owner.importlib, "import_module", guarded_import)
    owner.load_frozen_formal_decision_v1(REPO_ROOT)
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "from subprocess" not in source
    assert "import validate_nwj_formal_human_decision_v1" not in source
    assert "from validate_nwj_formal_human_decision_v1" not in source


def test_formal_authority_and_exact4_identity(snapshot: dict[str, object]) -> None:
    assert snapshot["sample_identity"] == {
        "ligand": "NWJ",
        "PDB": "4CM5",
        "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
        "authority_scope": owner.EXPECTED_SCOPE,
        "event_count": 4,
        "scaleup_ranks": [674, 675, 676, 677],
        "canonical_event_ids": list(owner.EXPECTED_EVENT_IDS),
    }
    assert snapshot["formal_human_authority"] == {
        "approved": True,
        "unsigned": False,
        "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "human_authority_created": True,
        "human_decision_created": True,
        "human_review_completed": True,
        "formal_authority_created": True,
        "formal_decision_created": True,
    }
    assert snapshot["projection_of_frozen_formal_human_authority"] is True
    assert snapshot["new_human_authority_created_by_ingestion"] is False


def test_chemistry_mechanism_and_domain_context_are_exact(
    snapshot: dict[str, object],
) -> None:
    assert snapshot["chemistry_authority"] == {
        "D1": "POSITIVE",
        "sample_conclusion": "stable Cys168 thioester linkage",
        "initial_thioacetal_then_oxidation": (
            "AUTHOR_PROPOSED_PRESUMED_MECHANISM_ONLY"
        ),
        "asserted_as_proven_mechanism": False,
        "scope": owner.EXPECTED_SCOPE,
    }
    assert snapshot["domain_relevance_authority"] == {
        "D2": "IN_DOMAIN",
        "reason": (
            "target-directed small-molecule TbPTR1 inhibitor designed for covalent "
            "capture of native Cys168"
        ),
        "designed_for_covalent_capture_of": "native Cys168",
        "TbPTR1_Ki_app_micromolar": 0.2,
        "T_b_brucei_IC50_micromolar": 7.75,
        "scope": owner.EXPECTED_SCOPE,
    }
    assert snapshot["network_required"] is False


def test_pair_selected_A_and_candidate_B_provenance(snapshot: dict[str, object]) -> None:
    assert snapshot["reactive_pair_authority"] == {
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CAV",
        "pair_authority_scope": owner.EXPECTED_SCOPE,
        "sample_level_authoritative": True,
        "reusable_pair_authority": False,
        "ligand_wide_authority": False,
        "cross_structure_generalization": False,
    }
    role = snapshot["selected_role_partition"]
    assert role["selected_role_candidate"] == "CANDIDATE_A_DIRECT_FORMYL"
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_atom_ids"] == ["CAV", "OAE"]
    assert role["linker_atom_ids"] == []
    assert role["scaffold_atom_ids"] == list(owner.SCAFFOLD_ATOMS)
    assert role["counts"] == {"warhead": 2, "linker": 0, "scaffold": 23, "Exact": 25}
    assert role["minimal_seed_atom_ids"] == ["CAX", "CAI", "CAK"]
    assert role["primary_anchor"] == "CAX"
    assert role["boundary"] == {
        "scaffold_atom_id": "CAX",
        "warhead_atom_id": "CAV",
        "bond_order": "SING",
    }
    alternative = snapshot["retained_nonselected_alternative"]
    assert alternative["candidate_id"] == "CANDIDATE_B_PHENYL_LINKER"
    assert alternative["runtime_valid_nonselected_alternative"] is True
    assert alternative["selected"] is False
    assert alternative["authoritative"] is False
    assert alternative["event_labels_created"] is False


def frozen_graph_inputs() -> tuple[tuple[str, ...], tuple[tuple[str, str, str], ...]]:
    graph = json.loads(
        (REPO_ROOT.parent / owner.GRAPH_EVIDENCE_RELATIVE).read_bytes()
    )["CCD_complete_heavy_atom_graph"]
    atoms = tuple(sorted(row["atom_id"] for row in graph["atom_inventory"]))
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph["bond_inventory"]
    )
    return atoms, bonds


def test_graph_and_published_runtime_are_revalidated(snapshot: dict[str, object]) -> None:
    atoms, bonds = frozen_graph_inputs()
    proof = owner._validate_partition_graph(atoms, bonds)
    assert proof == {
        "Exact25_count": 25,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "reactive_CAV_in_W": True,
        "cross_role_boundary_count": 1,
        "cross_role_boundary": owner.BOUNDARY,
        "W_count": 2,
        "L_count": 0,
        "S_count": 23,
    }
    runtime = snapshot["selected_role_partition"]["published_runtime_validation"]
    assert runtime["valid"] is True
    assert runtime["reasons"] == []
    assert runtime["partition_validator"] == "validate_role_profile_v1"
    assert runtime["seed_validator"] == "validate_minimal_seed_for_role_profile_v1"
    assert runtime["task_applicability_owner"] == (
        "valid_canonical_task_ids_for_role_profile_v1"
    )
    assert runtime["applicable_task_ids"] == [0, 3, 4]


def test_graph_fail_closed_probes() -> None:
    atoms, bonds = frozen_graph_inputs()
    without_w = tuple(
        bond for bond in bonds if frozenset(bond[:2]) != frozenset(("CAV", "OAE"))
    )
    with pytest.raises(owner.NWJIngestionSafetyError, match="GRAPH_W_DISCONNECTED"):
        owner._validate_partition_graph(atoms, without_w)
    without_s = tuple(
        bond for bond in bonds if frozenset(bond[:2]) != frozenset(("CAY", "CBA"))
    )
    with pytest.raises(owner.NWJIngestionSafetyError, match="GRAPH_S_DISCONNECTED"):
        owner._validate_partition_graph(atoms, without_s)
    with pytest.raises(
        owner.NWJIngestionSafetyError, match="GRAPH_DIRECT_BOUNDARY_NOT_UNIQUE_EXACT"
    ):
        owner._validate_partition_graph(atoms, (*bonds, ("CAI", "OAE", "SING")))


def test_exact5_B3_no_sixth_and_availability_only(snapshot: dict[str, object]) -> None:
    contract = snapshot["canonical_task_contract"]
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [row["display_alias"] for row in contract["global_canonical_tasks"]] == [
        "A",
        "B",
        "B2",
        "B3",
        "C",
    ]
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert contract["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert contract["task_applicability"][1]["reason"] == (
        "not_applicable_empty_linker_redundant_with_A"
    )
    assert contract["task_applicability"][2]["reason"] == (
        "not_applicable_empty_non_C_fixed_context"
    )
    assert contract["task_label_authority"] is False
    assert contract["event_task_label_rows_materialized"] is False
    assert contract["mask_tensor_targets_created"] is False
    assert contract["training_mask_targets_available_now"] is False


def test_PRE_POST_and_training_boundaries(snapshot: dict[str, object]) -> None:
    assert snapshot["PRE_boundary"] == {
        "candidate_PRE_free_source_graph_count_per_event": 1,
        "source_mapping_count_per_event": 0,
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_authority": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        "PRE_coordinates_invented": False,
        "PRE_topology_invented": False,
        "leaving_group_invented": False,
        "reagent_invented": False,
        "reaction_edit_invented": False,
    }
    assert snapshot["POST_boundary"] == {
        "Exact4_observed_POST_geometry": True,
        "explicit_covalent_evidence": True,
        "distance_only": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
    }
    training = snapshot["training_boundary"]
    assert training["human_training_use_disposition"] == "INCLUDE"
    assert training["training_use_human_authoritative"] is True
    assert training["future_training_admission_candidate"] is True
    assert training["future_training_admission_candidate_semantics"] == owner.FUTURE_STATUS
    for key in (
        "formal_training_admitted",
        "training_admission_created",
        "training_materialization_allowed",
        "split_assignment_created",
        "task_label_authority",
        "event_task_label_rows_materialized",
        "mask_tensor_targets_created",
        "training_mask_targets_available_now",
        "parameter_update_authorization",
        "FEATURE_SEMANTICS_AUDIT_PERFORMED",
        "READY_FOR_TRAINING",
        "TRAINING_STARTED",
    ):
        assert training[key] is False
    assert training["FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING"] is True


def test_exact4_matrix_is_audit_complete(artifacts: dict[str, bytes]) -> None:
    rows = list(
        csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"), newline=""))
    )
    assert len(rows) == 4
    assert tuple(row["canonical_event_id"] for row in rows) == owner.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in rows) == owner.EXPECTED_RANKS
    assert [row["POST_distance_angstrom"] for row in rows] == [
        event[5] for event in owner.EXPECTED_EVENTS
    ]
    for row in rows:
        assert row["protein_reactive_atom"] == "SG"
        assert row["ligand_reactive_atom"] == "CAV"
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["canonical_task_count"] == "5"
        assert row["B3_present"] == "true"
        assert row["sixth_task"] == "false"
        assert row["PRE_source_mapping_status"] == (
            "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        )
        assert row["formal_training_admitted"] == "false"
        assert row["ready_for_training"] == "false"


def test_current_with_tp2_census_is_read_only_pre_ingestion_state(
    snapshot: dict[str, object],
) -> None:
    assert snapshot["current_census_boundary"] == {
        "row_count": 1000,
        "NWJ_event_count": 4,
        "NWJ_current_global_status": "CURRENTLY_UNREVIEWED",
        "NWJ_task_relevance": "UNRESOLVED",
        "NWJ_chemistry": "UNRESOLVED",
        "NWJ_training_use": "UNRESOLVED",
        "current_pending_rank": 1,
        "raw_priority_rank": 28,
        "next_priority_review_ligand": "NWJ",
        "census_modified_by_ingestion": False,
    }


def test_deterministic_double_build_and_manifest_closure(
    artifacts: dict[str, bytes],
) -> None:
    assert artifacts == owner.build_artifacts_v1(REPO_ROOT)
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["candidate_publication_paths"] == [
        path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS
    ]
    assert manifest["output_artifact_count"] == 4
    assert manifest["output_paths"] == [
        path.as_posix() for path in owner.OUTPUT_RELATIVE_PATHS
    ]
    assert manifest["formal_validator_provenance_identity_only"] is True
    assert manifest["formal_validator_imported"] is False
    assert manifest["formal_validator_executed_by_production"] is False
    assert manifest["formal_validator_subprocessed_by_production"] is False
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert all(not value.startswith("/") for value in manifest["output_paths"])


def test_materialized_equals_fresh_build() -> None:
    result = owner.check_materialized_v1(REPO_ROOT)
    assert result["status"] == "PASS"
    assert result["materialized_bytes_equal_fresh_build"] is True
    assert result["deterministic_double_build"] is True


def test_checker_independently_validates_sources_artifacts_and_lifecycle(
    artifacts: dict[str, bytes],
) -> None:
    checker = load_checker()
    sources = checker.independently_check_frozen_sources(REPO_ROOT)
    assert sources["formal_json_independently_validated"] is True
    assert sources["formal_validator_provenance_identity_only"] is True
    assert sources["formal_validator_imported"] is False
    assert sources["formal_validator_executed_by_production"] is False
    independent = checker.independently_check_artifacts(REPO_ROOT, artifacts)
    assert independent["independent_artifact_validation"] is True
    lifecycle = checker.check_git_lifecycle(REPO_ROOT)
    assert lifecycle["profile"] == checker.CANDIDATE_UNTRACKED
    assert lifecycle["ordinary_untracked_count"] == 7
    assert lifecycle["staged_count"] == 0
    assert lifecycle["tracked_modification_count"] == 0


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("sample_identity", "review_unit_id"), "WRONG"),
        (("sample_identity", "canonical_event_ids"), list(owner.EXPECTED_EVENT_IDS[:-1])),
        (
            ("sample_identity", "canonical_event_ids"),
            [owner.EXPECTED_EVENT_IDS[0], *owner.EXPECTED_EVENT_IDS[:3]],
        ),
        (("formal_decisions", "D1_observed_covalent_chemistry", "decision"), "NEGATIVE"),
        (("formal_decisions", "D2_generation_domain_relevance", "decision"), "OUT_OF_DOMAIN"),
        (("formal_decisions", "D3_reactive_pair", "protein_atom"), "CB"),
        (("formal_decisions", "D3_reactive_pair", "ligand_atom"), "OAE"),
        (("formal_decisions", "D3_reactive_pair", "scope"), "ALL_NWJ"),
        (("formal_decisions", "D4_role_partition", "selected_candidate"), "CANDIDATE_B_PHENYL_LINKER"),
        (("selected_role_context", "warhead_atom_ids"), ["CAV"]),
        (("selected_role_context", "linker_atom_ids"), ["CAX"]),
        (("selected_role_context", "scaffold_atom_ids"), list(owner.SCAFFOLD_ATOMS[:-1])),
        (("selected_role_context", "scaffold_atom_ids"), [*owner.SCAFFOLD_ATOMS, "CAV"]),
        (("selected_role_context", "minimal_seed", "atom_ids"), ["CAX", "CAI"]),
        (("selected_role_context", "minimal_seed", "primary_scaffold_side_anchor"), "CAI"),
        (("selected_role_context", "published_runtime", "direct_boundary", "bond_order"), "DOUB"),
        (("retained_nonselected_alternative", "candidate_B_authoritative"), True),
        (("canonical_Exact5", "B3_present"), False),
        (("canonical_Exact5", "sixth_task"), True),
        (("canonical_Exact5", "selected_structural_applicability_task_ids"), [0, 1, 2, 3, 4]),
        (("PRE_boundary", "source_mapping_count_per_event"), 1),
        (("PRE_boundary", "PRE_source_mapping_status"), "MAPPED"),
        (("PRE_boundary", "PRE_authority"), True),
        (("reusable_authority_map", "reusable_pair_authority"), True),
        (("reusable_authority_map", "reusable_role_authority"), True),
        (("canonical_Exact5", "task_label_authority"), True),
        (("canonical_Exact5", "mask_tensor_targets_created"), True),
        (("training_boundary", "formal_training_admitted"), True),
        (("training_boundary", "training_materialization_allowed"), True),
        (("training_boundary", "parameter_update_authorization"), True),
        (("training_boundary", "READY_FOR_TRAINING"), True),
        (("training_boundary", "TRAINING_STARTED"), True),
        (("POST_boundary", "POST_geometry_training_authority"), True),
        (("operation_boundary", "reconciliation_performed"), True),
        (("operation_boundary", "census_refresh_performed"), True),
        (("operation_boundary", "queue_refresh_performed"), True),
    ),
)
def test_formal_critical_semantic_mutations_fail_closed(
    path: tuple[object, ...], value: object
) -> None:
    changed = copy.deepcopy(frozen_formal())
    mutate_path(changed, path, value)
    with pytest.raises(owner.NWJIngestionSafetyError):
        owner._validate_formal(changed)


def test_formal_decision_and_validator_sha_drift_fail_closed(tmp_path: Path) -> None:
    formal = bytearray(
        (REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes()
    )
    formal[-2] = ord(" ")
    changed_formal = tmp_path / "formal.json"
    changed_formal.write_bytes(formal)
    with pytest.raises(owner.NWJIngestionSafetyError, match="SOURCE_BINDING_FAILED"):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT, formal_decision_path=changed_formal
        )

    validator = (
        REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    ).read_bytes() + b"\n"
    changed_validator = tmp_path / "validator.py"
    changed_validator.write_bytes(validator)
    with pytest.raises(owner.NWJIngestionSafetyError, match="SOURCE_BINDING_FAILED"):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT, formal_validator_path=changed_validator
        )


@pytest.mark.parametrize(
    ("filename", "path", "value"),
    (
        (owner.SNAPSHOT, ("sample_identity", "review_unit_id"), "WRONG"),
        (owner.SNAPSHOT, ("reactive_pair_authority", "ligand_reactive_atom"), "OAE"),
        (owner.SNAPSHOT, ("selected_role_partition", "selected_role_candidate"), "CANDIDATE_B_PHENYL_LINKER"),
        (owner.SNAPSHOT, ("selected_role_partition", "warhead_atom_ids"), ["CAV"]),
        (owner.SNAPSHOT, ("selected_role_partition", "linker_atom_ids"), ["CAX"]),
        (owner.SNAPSHOT, ("selected_role_partition", "minimal_seed_atom_ids"), ["CAX"]),
        (owner.SNAPSHOT, ("selected_role_partition", "primary_anchor"), "CAI"),
        (owner.SNAPSHOT, ("canonical_task_contract", "B3_present"), False),
        (owner.SNAPSHOT, ("canonical_task_contract", "sixth_task"), True),
        (owner.SNAPSHOT, ("canonical_task_contract", "direct_profile_applicable_task_ids"), [0, 1, 2, 3, 4]),
        (owner.SNAPSHOT, ("PRE_boundary", "PRE_authority"), True),
        (owner.SNAPSHOT, ("PRE_boundary", "source_mapping_count_per_event"), 1),
        (owner.SNAPSHOT, ("POST_boundary", "POST_geometry_training_target_created"), True),
        (owner.SNAPSHOT, ("training_boundary", "task_label_authority"), True),
        (owner.SNAPSHOT, ("training_boundary", "mask_tensor_targets_created"), True),
        (owner.SNAPSHOT, ("training_boundary", "formal_training_admitted"), True),
        (owner.SNAPSHOT, ("training_boundary", "training_materialization_allowed"), True),
        (owner.SNAPSHOT, ("training_boundary", "READY_FOR_TRAINING"), True),
        (owner.SNAPSHOT, ("training_boundary", "TRAINING_STARTED"), True),
        (owner.SUMMARY, ("reconciliation_performed",), True),
        (owner.SUMMARY, ("census_refresh_performed",), True),
        (owner.SUMMARY, ("queue_refresh_performed",), True),
        (owner.MANIFEST, ("formal_validator_executed_by_production",), True),
    ),
)
def test_owner_and_checker_reject_high_value_artifact_tamper(
    artifacts: dict[str, bytes], filename: str, path: tuple[object, ...], value: object
) -> None:
    changed = json_artifact_mutation(artifacts, filename, path, value)
    with pytest.raises(owner.NWJIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed, REPO_ROOT)
    checker = load_checker()
    with pytest.raises(RuntimeError, match="COVAPIE_NWJ_INGESTION_CHECK_V1_ERROR"):
        checker.independently_check_artifacts(REPO_ROOT, changed)


def test_owner_and_checker_reject_matrix_pair_and_training_tamper(
    artifacts: dict[str, bytes],
) -> None:
    for field, value in (
        ("ligand_reactive_atom", "OAE"),
        ("direct_profile_applicable_task_ids_json", "[0,1,2,3,4]"),
        ("PRE_source_mapping_status", "MAPPED"),
        ("task_label_authority", "true"),
        ("formal_training_admitted", "true"),
        ("ready_for_training", "true"),
    ):
        rows = list(
            csv.DictReader(
                io.StringIO(artifacts[owner.MATRIX].decode("utf-8"), newline="")
            )
        )
        rows[0][field] = value
        changed = dict(artifacts)
        changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, rows)
        with pytest.raises(owner.NWJIngestionSafetyError):
            owner.validate_completed_decision_projection_v1(changed, REPO_ROOT)
        checker = load_checker()
        with pytest.raises(RuntimeError, match="MATRIX_"):
            checker.independently_check_artifacts(REPO_ROOT, changed)
