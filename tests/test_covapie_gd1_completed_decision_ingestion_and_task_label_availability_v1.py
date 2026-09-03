from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess

import pytest

from covalent_ext import (
    covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PUBLIC_API = (
    "GD1IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


def _checker_module():
    path = REPO_ROOT / owner.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("gd1_ingestion_checker_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


@pytest.fixture(scope="module")
def matrix(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))


@pytest.fixture(scope="module")
def summary(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SUMMARY])


@pytest.fixture(scope="module")
def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.MANIFEST])


@pytest.fixture()
def formal() -> dict[str, object]:
    return copy.deepcopy(owner.load_frozen_formal_decision_v1(REPO_ROOT)["formal"])


def _assert_formal_rejected(formal: dict[str, object]) -> None:
    formal["formal_decision_semantic_canonical_sha256"] = owner._semantic_digest(formal)
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner._validate_formal_document(formal)


def _json_mutation(
    artifacts: dict[str, bytes], name: str, mutate
) -> dict[str, bytes]:
    changed = dict(artifacts)
    value = json.loads(changed[name])
    mutate(value)
    changed[name] = owner._json_bytes(value)
    return changed


def _matrix_mutation(
    artifacts: dict[str, bytes], field: str, value: str
) -> dict[str, bytes]:
    changed = dict(artifacts)
    rows = list(csv.DictReader(io.StringIO(changed[owner.MATRIX].decode("utf-8"))))
    rows[0][field] = value
    changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, rows)
    return changed


def test_public_api_is_modern_exact6() -> None:
    assert owner.__all__ == EXPECTED_PUBLIC_API


def test_candidate_inventory_is_exact7() -> None:
    paths = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    assert len(paths) == len(set(paths)) == 7
    assert paths[:3] == (
        owner.SOURCE_RELATIVE.as_posix(),
        owner.CHECKER_RELATIVE.as_posix(),
        owner.TEST_RELATIVE.as_posix(),
    )
    assert paths[3:] == tuple(path.as_posix() for path in owner.OUTPUT_RELATIVE_PATHS)


def test_formal_json_and_validator_exact_identity() -> None:
    expected = (
        (
            owner.FORMAL_DECISION_RELATIVE,
            33315,
            "ffb8b0c237be2065908d2da6e041fdc57fb2706f19f91ce87d1524bd3aaa9068",
        ),
        (
            owner.FORMAL_VALIDATOR_RELATIVE,
            79560,
            "2658eaf3427d4c0d24160e689c71ddc169f84e297a1e9394eee59c97a8b991ae",
        ),
    )
    for relative, byte_count, digest in expected:
        payload = (REPO_ROOT.parent / relative).read_bytes()
        assert len(payload) == byte_count
        assert hashlib.sha256(payload).hexdigest() == digest


def test_bound_structural_graph_exact_identity() -> None:
    payload = (REPO_ROOT.parent / owner.STRUCTURAL_GRAPH_RELATIVE).read_bytes()
    assert len(payload) == 18253
    assert hashlib.sha256(payload).hexdigest() == (
        "0cf8ce971370b55521f41104b26e936ab27ed530e6f0aa9de17f96623b0f0520"
    )
    validated = owner._validate_structural_graph(payload)
    assert validated["atom_ids"] == owner.HEAVY_ATOMS
    assert validated["bonds"] == owner.HEAVY_BONDS
    assert validated["boundary"] == "C7-C77 SING S-W"


def test_formal_semantic_digest_independently_recomputed(formal) -> None:
    assert owner._semantic_digest(formal) == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert formal["formal_decision_semantic_canonical_sha256"] == owner.FORMAL_SEMANTIC_CANONICAL_SHA256


def test_formal_validator_lifecycle_exact(formal) -> None:
    assert formal["validator_lifecycle"] == {
        "baseline_commit": owner.BASELINE_COMMIT,
        "future_ingestion_must_bind_formal_JSON_and_validator_bytes_SHA256": True,
        "future_ingestion_must_independently_validate_formal_semantics": True,
        "future_ingestion_must_not_execute_this_validator_after_HEAD_advances": True,
        "validator_baseline_locked_creation_and_self_test_only": True,
        "validator_postbaseline_runtime_dependency_allowed": False,
    }


def test_formal_validator_is_never_imported_or_executed(monkeypatch) -> None:
    imported: list[str] = []
    real_import = owner.importlib.import_module

    def guarded_import(name: str, *args, **kwargs):
        assert "validate_gd1_formal_human_decision_v1" not in name
        imported.append(name)
        return real_import(name, *args, **kwargs)

    def subprocess_forbidden(*args, **kwargs):
        raise AssertionError("production owner must not create a subprocess")

    monkeypatch.setattr(owner.importlib, "import_module", guarded_import)
    monkeypatch.setattr(subprocess, "run", subprocess_forbidden)
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert imported == ["covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"]
    assert bound["formal_validator_provenance_identity_only"] is True
    assert bound["formal_validator_imported"] is False
    assert bound["formal_validator_executed"] is False


def test_owner_ast_has_no_formal_validator_import_or_subprocess() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any("validate_gd1_formal_human_decision_v1" in name for name in imported)
    assert "subprocess" not in imported


def test_d1_through_d6_exact(formal) -> None:
    decision = formal["unit_human_decision"]
    assert [decision[f"D{i}_{suffix}"] for i, suffix in (
        (1, "task_relevance"),
        (2, "chemistry"),
        (3, "reactive_pair"),
        (4, "role_candidate"),
        (5, "training_use"),
        (6, "scientific_context"),
    )] == [
        "RELEVANT",
        "POSITIVE",
        "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_0",
        "EXCLUDE_FROM_TRAINING_ONLY",
        owner.EXPECTED_D6,
    ]
    d6 = owner.EXPECTED_D6.encode("utf-8")
    assert len(d6) == 1022
    assert hashlib.sha256(d6).hexdigest() == owner.EXPECTED_D6_SHA256


def test_finalization_and_human_authority_exact(formal) -> None:
    assert formal["unsigned"] is False
    assert formal["approved"] is True
    assert formal["decision_finalized"] is True
    assert formal["human_review_completed"] is True
    assert formal["formal_authority_created"] is True
    assert formal["formal_authority_is_human"] is True
    assert formal["machine_approval"] is False
    assert formal["human_authorization"]["reviewer_id"] == "fmx"
    assert formal["human_authorization"]["attestor_id"] == "fmx"


def test_exact4_identity_ranks_contexts_and_distances(formal) -> None:
    identity = formal["identity"]
    assert identity["canonical_event_ids"] == list(owner.EXPECTED_EVENT_IDS)
    assert identity["scaleup_ranks"] == [691, 692, 693, 694]
    assert identity["contexts_collapsed"] is False
    assert len(set(identity["canonical_event_ids"])) == 4
    assert formal["POST_evidence_boundary"]["observed_distances_angstrom"] == [
        1.873494, 1.888634, 1.881354, 1.907766,
    ]


def test_sample_sg_c77_pair_authority_is_not_reusable(formal) -> None:
    pair = formal["reactive_pair_authority"]
    assert pair["protein_reactive_atom"] == "SG"
    assert pair["ligand_reactive_atom"] == "C77"
    assert pair["authority_scope"] == owner.AUTHORITY_SCOPE
    assert pair["observed_pair_authority_created"] is True
    assert pair["reusable_pair_rule_created"] is False
    assert pair["cross_structure_regiochemistry_generalization"] is False


def test_candidate0_role_partition_exact(formal) -> None:
    role = formal["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 0
    assert role["role_profile"] == owner.EXPECTED_ROLE_PROFILE
    assert role["W"] == ["C77", "N77"]
    assert role["L"] == []
    assert role["S"] == ["C2", "C4", "C5", "C6", "C7", "C8", "N1", "N2", "N3", "N9", "O6"]
    assert role["W_L_S_counts"] == [2, 0, 11]
    assert role["boundary_bonds"] == list(owner.BOUNDARY_BONDS)
    assert role["reusable_role_rule_created"] is False


def test_published_direct_runtime_revalidation() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    result = bound["published_DIRECT_runtime_validation"]
    assert result == owner._expected_runtime_validation()
    assert result["valid"] is True
    assert result["direct_scaffold_warhead_boundary"] == {
        "scaffold_atom_id": "C7",
        "warhead_atom_id": "C77",
        "bond_order": "SING",
        "boundary_valid": True,
    }
    assert bound["structural_validation"] == {
        "Exact13_count": 13,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "missing_atom_ids": [],
        "extra_atom_ids": [],
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "C77_in_W": True,
        "boundary": "C7-C77 SING S-W",
    }


def test_canonical_exact5_and_structural_applicability(snapshot) -> None:
    contract = snapshot["canonical_task_contract"]
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [row["display_alias"] for row in contract["global_canonical_tasks"]] == [
        "A", "B", "B2", "B3", "C",
    ]
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert contract["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert contract["task_applicability_determined"] is True
    assert contract["authoritative_task_labels_created"] is False
    assert contract["event_task_label_rows_materialized"] is False
    assert all(
        row["training_mask_target_available_now"] is False
        for row in contract["task_applicability"]
    )


def test_snapshot_distinguishes_authority_from_training_eligibility(snapshot) -> None:
    assert snapshot["completed_lane"] == owner.EXPECTED_COMPLETED_LANE
    assert snapshot["scientific_sample_authority_available"] is True
    assert snapshot["training_eligibility"] is False
    assert snapshot["task_relevance"] == "RELEVANT"
    assert snapshot["chemistry"] == "POSITIVE"
    assert snapshot["human_training_excluded"] is True
    assert snapshot["future_training_admission_candidate"] is False


def test_event_matrix_exact4_order_and_contexts(matrix) -> None:
    assert len(matrix) == 4
    assert tuple(row["canonical_event_id"] for row in matrix) == owner.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in matrix) == owner.EXPECTED_RANKS
    assert tuple(row["protein_chain_or_asym"] for row in matrix) == ("B", "C", "D", "E")
    assert tuple(row["ligand_chain_or_asym"] for row in matrix) == ("F", "I", "K", "N")
    assert tuple(row["POST_distance_angstrom"] for row in matrix) == (
        "1.873494", "1.888634", "1.881354", "1.907766",
    )


def test_all_matrix_rows_preserve_positive_sample_authority(matrix) -> None:
    for row in matrix:
        assert row["completed_lane"] == owner.EXPECTED_COMPLETED_LANE
        assert row["human_review_completed"] == "true"
        assert row["task_relevance"] == "RELEVANT"
        assert row["task_relevance_human_authority"] == "true"
        assert row["human_task_relevance_decision"] == "RELEVANT"
        assert row["task_relevance_human_authoritative"] == "true"
        assert row["chemistry"] == "POSITIVE"
        assert row["chemistry_known_positive"] == "true"
        assert row["chemistry_human_authority"] == "true"
        assert row["human_chemistry_decision"] == "POSITIVE"
        assert row["chemistry_human_authoritative"] == "true"
        assert row["negative_chemistry"] == "false"
        assert row["task_domain_negative"] == "false"
        assert row["distance_only_rejection"] == "false"
        assert row["reactive_pair_human_authoritative"] == "true"
        assert row["role_partition_human_authoritative"] == "true"


def test_all_matrix_rows_fail_closed_for_training(matrix) -> None:
    false_fields = (
        "training_use_allowed",
        "candidate_for_future_training_admission",
        "future_training_admission_candidate",
        "training_admitted",
        "formal_training_admitted",
        "training_materialization_allowed_now",
        "training_materialization_allowed",
        "tensor_target_created",
        "model_supervision_usable",
        "training_mask_targets_available_now",
        "current_runtime_model_usable",
        "parameter_update_authorization",
        "READY_FOR_TRAINING",
    )
    for row in matrix:
        assert row["formal_event_training_use_decision"] == "EXCLUDE_FROM_TRAINING_ONLY"
        assert row["event_training_use_human_decision_available"] == "true"
        assert row["human_training_excluded"] == "true"
        assert row["training_exclusion_reason"] == owner.TRAINING_EXCLUSION_REASON
        assert row["future_training_admission_status"] == "HUMAN_EXCLUDE_FROM_TRAINING_ONLY"
        assert all(row[field] == "false" for field in false_fields)


def test_post_source_evidence_does_not_create_training_targets(matrix, summary) -> None:
    assert summary["POST_source_evidence_event_count"] == 4
    assert summary["POST_training_authority_event_count"] == 0
    assert summary["POST_training_target_event_count"] == 0
    for row in matrix:
        assert row["POST_source_evidence_available"] == "true"
        assert row["explicit_covalent_evidence"] == "true"
        assert row["distance_only_inference"] == "false"
        assert row["POST_geometry_training_authority"] == "false"
        assert row["POST_geometry_training_target_created"] == "false"
        assert row["POST_geometry_training_label_available_now"] == "false"


def test_pre_is_unavailable_unresolved_and_not_synthesized(matrix, summary) -> None:
    assert summary["PRE_source_graph_present_event_count"] == 0
    assert summary["PRE_mapping_available_event_count"] == 0
    assert summary["PRE_authority_event_count"] == 0
    for row in matrix:
        assert row["supporting_PRE_source_graph_count_per_event"] == "0"
        assert row["PRE_source_graph_present"] == "false"
        assert row["PRE_source_graph_count_per_event"] == "0"
        assert row["PRE_mapping_count_per_event"] == "0"
        assert row["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
        assert row["PRE_status"] == "PRE_REACTION_UNRESOLVED"
        assert all(
            row[field] == "false"
            for field in (
                "PRE_topology_authority", "PRE_geometry_authority",
                "PRE_coordinates_authority", "PRE_reconstruction",
                "POST_to_PRE_copy", "PRE_zero_fill", "leaving_group_inferred",
                "reagent_inferred", "bond_edit_inferred",
            )
        )


def test_bound_form_and_4fgc_boundary(matrix) -> None:
    for row in matrix:
        assert row["BOUND_FORM_REPRESENTATION"] == "true"
        assert row["BOUND_CCD_NOT_EQUAL_FREE_PRE_GRAPH"] == "true"
        assert row["FREE_PREQ0_PRE_TOPOLOGY_NOT_ESTABLISHED_BY_GD1_CCD"] == "true"
        assert row["related_4FGC_context_only"] == "true"
        assert row["4FGC_current_Exact4_PRE_authority"] == "false"
        assert row["4FGC_event_specific_mapping"] == "false"
        assert row["4FGC_coordinates_imported"] == "false"


def test_no_reusable_or_class_target_authority(matrix, summary) -> None:
    false_fields = (
        "reusable_chemistry_authority", "reusable_pair_rule_created",
        "reusable_role_authority", "reaction_family_authority",
        "warhead_rule_authority", "warhead_type_authority",
        "reaction_family_training_class_target_available",
        "warhead_rule_training_class_target_available", "warhead_type_target_available",
        "reusable_authority_label_available",
    )
    assert all(row[field] == "false" for row in matrix for field in false_fields)
    assert summary["reusable_chemistry_authority_event_count"] == 0
    assert summary["reusable_pair_authority_event_count"] == 0
    assert summary["reusable_role_authority_event_count"] == 0
    assert summary["reaction_family_target_count"] == 0
    assert summary["warhead_rule_target_count"] == 0
    assert summary["warhead_type_target_count"] == 0


def test_current_census_is_bound_read_only_and_preformal(snapshot, manifest) -> None:
    boundary = snapshot["current_census_boundary"]
    assert boundary["GD1_current_status"] == "CURRENTLY_UNREVIEWED"
    assert boundary["GD1_human_review_completed"] is False
    assert boundary["GD1_chemistry_disposition"] == "UNRESOLVED"
    assert boundary["reconciliation_performed"] is False
    assert boundary["current_census_changed"] is False
    assert boundary["census_refreshed"] is False
    assert boundary["queue_updated"] is False
    assert len(manifest["current_census_bindings"]) == 4
    for binding in manifest["current_census_bindings"]:
        payload = (REPO_ROOT / binding["path"]).read_bytes()
        assert len(payload) == binding["byte_count"]
        assert hashlib.sha256(payload).hexdigest() == binding["SHA256"]


def test_manifest_binds_sources_outputs_and_no_self_hash(artifacts, manifest) -> None:
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    structural = manifest["structural_graph_binding"]
    assert structural["byte_count"] == 18253
    assert structural["SHA256"] == (
        "0cf8ce971370b55521f41104b26e936ab27ed530e6f0aa9de17f96623b0f0520"
    )
    assert manifest["formal_validator_runtime_dependency"] is False
    assert manifest["frozen_formal_validator_provenance_identity_only"] is True
    assert manifest["frozen_formal_validator_imported"] is False
    assert manifest["frozen_formal_validator_executed"] is False
    assert manifest["frozen_formal_validator_subprocess_called"] is False
    assert manifest["NEVER_IMPORT_FORMAL_VALIDATOR"] is True
    assert manifest["NEVER_EXECUTE_FORMAL_VALIDATOR"] is True
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert owner.MANIFEST not in manifest["output_artifact_bindings"]
    for name in (owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY):
        binding = manifest["output_artifact_bindings"][name]
        assert binding["byte_count"] == len(artifacts[name])
        assert binding["SHA256"] == hashlib.sha256(artifacts[name]).hexdigest()


def test_candidate_source_bindings_are_live_exact(manifest) -> None:
    bindings = manifest["candidate_source_bindings"]
    assert [row["path"] for row in bindings] == [
        owner.SOURCE_RELATIVE.as_posix(),
        owner.CHECKER_RELATIVE.as_posix(),
        owner.TEST_RELATIVE.as_posix(),
    ]
    for row in bindings:
        payload = (REPO_ROOT / row["path"]).read_bytes()
        assert row["byte_count"] == len(payload)
        assert row["SHA256"] == hashlib.sha256(payload).hexdigest()
        assert row["expected_executable_class"] == "NON_EXECUTABLE"


def test_double_build_is_byte_identical(artifacts) -> None:
    assert owner.build_artifacts_v1(REPO_ROOT) == artifacts
    assert owner.build_artifacts_v1(REPO_ROOT) == artifacts


def test_materialization_is_exact_and_deterministic(tmp_path) -> None:
    target = tmp_path / "outputs"
    first = owner.materialize_artifacts_v1(REPO_ROOT, output_root=target)
    second = owner.materialize_artifacts_v1(REPO_ROOT, output_root=target)
    assert first == second
    assert {path.name for path in target.iterdir()} == set(owner.OUTPUT_FILENAMES)
    assert all((target / name).read_bytes() == payload for name, payload in first.items())


def test_materialization_rejects_unexpected_destination_entry(tmp_path) -> None:
    target = tmp_path / "outputs"
    target.mkdir()
    (target / "unexpected.txt").write_text("x\n", encoding="utf-8")
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.materialize_artifacts_v1(REPO_ROOT, output_root=target)


def test_live_materialized_outputs_match_fresh_build() -> None:
    result = owner.check_materialized_v1(REPO_ROOT)
    assert result["status"] == "PASS"
    assert result["GD1_HUMAN_TRAINING_EXCLUDED"] is True
    assert result["GD1_FUTURE_TRAINING_ADMISSION_CANDIDATE"] is False
    assert result["READY_FOR_TRAINING"] is False


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("unit_human_decision", "D5_training_use"), "INCLUDE"),
        (("training_use_boundary", "human_training_excluded"), False),
        (("training_use_boundary", "future_training_admission_candidate"), True),
        (("training_use_boundary", "formal_training_admitted"), True),
        (("training_use_boundary", "training_materialization_allowed"), True),
        (("training_use_boundary", "tensor_target_created"), True),
        (("training_use_boundary", "current_runtime_model_usable"), True),
        (("training_use_boundary", "READY_FOR_TRAINING"), True),
        (("identity", "contexts_collapsed"), True),
        (("selected_role_partition", "selected_candidate_index_0based"), 1),
        (("canonical_Exact5_and_sample_applicability", "B3_present"), False),
    ),
)
def test_formal_semantic_mutations_fail_closed(formal, path, value) -> None:
    formal[path[0]][path[1]] = value
    _assert_formal_rejected(formal)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("formal_event_training_use_decision", "INCLUDE"),
        ("human_training_excluded", "false"),
        ("future_training_admission_candidate", "true"),
        ("training_admitted", "true"),
        ("formal_training_admitted", "true"),
        ("training_materialization_allowed", "true"),
        ("tensor_target_created", "true"),
        ("current_runtime_model_usable", "true"),
        ("chemistry", "NEGATIVE"),
        ("task_relevance", "NOT_RELEVANT"),
    ),
)
def test_matrix_mutations_fail_closed(artifacts, field, value) -> None:
    changed = _matrix_mutation(artifacts, field, value)
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_snapshot_future_candidate_mutation_fails_closed(artifacts) -> None:
    changed = _json_mutation(
        artifacts,
        owner.SNAPSHOT,
        lambda value: value.__setitem__("future_training_admission_candidate", True),
    )
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_summary_training_count_mutation_fails_closed(artifacts) -> None:
    changed = _json_mutation(
        artifacts,
        owner.SUMMARY,
        lambda value: value.__setitem__("training_use_allowed_event_count", 4),
    )
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_manifest_validator_execution_mutation_fails_closed(artifacts) -> None:
    changed = _json_mutation(
        artifacts,
        owner.MANIFEST,
        lambda value: value.__setitem__("frozen_formal_validator_executed", True),
    )
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_output_inventory_order_and_count_fail_closed(artifacts) -> None:
    reordered = dict(reversed(tuple(artifacts.items())))
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(reordered)
    missing = dict(artifacts)
    missing.pop(owner.MATRIX)
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(missing)


def test_mutated_formal_json_bytes_fail_binding(tmp_path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    target = tmp_path / source.name
    target.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.load_frozen_formal_decision_v1(REPO_ROOT, formal_decision_path=target)


def test_mutated_formal_validator_bytes_fail_binding(tmp_path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    target = tmp_path / source.name
    payload = bytearray(source.read_bytes())
    payload[-1] ^= 1
    target.write_bytes(payload)
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner.load_frozen_formal_decision_v1(REPO_ROOT, formal_validator_path=target)


def test_strict_json_rejects_duplicate_keys_and_nonfinite() -> None:
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner._strict_json_loads(b'{"x":1,"x":2}\n', "DUPLICATE")
    with pytest.raises(owner.GD1IngestionSafetyError):
        owner._strict_json_loads(b'{"x":NaN}\n', "NONFINITE")


def test_dynamic_or_machine_metadata_fails_closed() -> None:
    for value in (
        {"timestamp": "2026-01-01"},
        {"hostname": "host"},
        {"absolute": "/cpfs/example"},
        {"mode": 420},
    ):
        with pytest.raises(owner.GD1IngestionSafetyError):
            owner._reject_dynamic_or_forbidden_metadata(value)


def test_candidate_and_future_tracked_lifecycle_profiles() -> None:
    checker = _checker_module()
    expected = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    assert checker.classify_repository_profile(
        head=checker.BASELINE_HEAD,
        origin=checker.BASELINE_HEAD,
        tracked_modifications=set(),
        staged_paths=set(),
        untracked_paths=expected,
        expected_paths=expected,
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        head="1" * 40,
        origin=checker.BASELINE_HEAD,
        tracked_modifications=set(),
        staged_paths=set(),
        untracked_paths=set(),
        expected_paths=expected,
    ) == checker.TRACKED_CLEAN
    result = checker.check_lifecycle_simulations(expected)
    assert all(result.values())


def test_lifecycle_rejects_baseline_drift_behind_and_missing_exact7() -> None:
    checker = _checker_module()
    expected = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    with pytest.raises(SystemExit):
        checker.classify_repository_profile(
            head="1" * 40,
            origin=checker.BASELINE_HEAD,
            tracked_modifications=set(),
            staged_paths=set(),
            untracked_paths=expected,
            expected_paths=expected,
        )
    base = {
        "profile": checker.TRACKED_CLEAN,
        "head": "2" * 40,
        "origin": "1" * 40,
        "ahead": 2,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin": True,
        "origin_ancestor_of_head": True,
        "changed_paths": expected,
        "expected_paths": expected,
    }
    for mutation in ({"behind": 1}, {"changed_paths": set()}):
        case = dict(base)
        case.update(mutation)
        with pytest.raises(SystemExit):
            checker.validate_repository_relation_values(**case)


def test_no_forbidden_candidate_suffix_or_protected_path() -> None:
    checker = _checker_module()
    expected = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    assert not any(path.endswith(checker.FORBIDDEN_SUFFIXES) for path in expected)
    assert not any(path.startswith(checker.PROTECTED_PREFIXES) for path in expected)
    assert not (expected & checker.PROTECTED_FILES)
