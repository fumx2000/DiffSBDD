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
    covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
_SPEC = importlib.util.spec_from_file_location("covapie_sr2_ingestion_checker_v1", CHECKER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8") + b"\n"


def _json_mutation(
    artifacts: dict[str, bytes], name: str, mutate
) -> dict[str, bytes]:
    changed = dict(artifacts)
    value = json.loads(changed[name])
    mutate(value)
    changed[name] = _json_bytes(value)
    return changed


def _matrix_mutation(
    artifacts: dict[str, bytes], field: str, value: str
) -> dict[str, bytes]:
    changed = dict(artifacts)
    rows = list(csv.DictReader(io.StringIO(changed[owner.MATRIX].decode("utf-8"))))
    rows[0][field] = value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=owner.MATRIX_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    changed[owner.MATRIX] = stream.getvalue().encode("utf-8")
    return changed


def _set_path(document: dict[str, object], path: tuple[str, ...], value: object) -> None:
    target: dict[str, object] = document
    for key in path[:-1]:
        child = target[key]
        assert type(child) is dict
        target = child
    target[path[-1]] = value


@pytest.fixture(scope="module")
def formal() -> dict[str, object]:
    path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    return json.loads(path.read_bytes())


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


@pytest.fixture(scope="module")
def summary(artifacts) -> dict[str, object]:
    return json.loads(artifacts[owner.SUMMARY])


@pytest.fixture(scope="module")
def manifest(artifacts) -> dict[str, object]:
    return json.loads(artifacts[owner.MANIFEST])


@pytest.fixture(scope="module")
def matrix(artifacts) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))


def test_public_api_is_modern_exact6() -> None:
    assert owner.__all__ == (
        "SR2IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_candidate_inventory_is_exact7() -> None:
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert owner.CANDIDATE_PUBLICATION_PATHS == (
        owner.SOURCE_RELATIVE,
        owner.CHECKER_RELATIVE,
        owner.TEST_RELATIVE,
        *owner.OUTPUT_RELATIVE_PATHS,
    )


def test_frozen_formal_json_and_validator_identity() -> None:
    expected = (
        (
            owner.FORMAL_DECISION_RELATIVE,
            34106,
            "b41c84d6519efce267410d5e95b017366c9b5b8820a6f5878c9a893404b6defa",
        ),
        (
            owner.FORMAL_VALIDATOR_RELATIVE,
            86374,
            "5526d2205c5cc2da494e0263d33d2bf5a275fa9c5e18d51c3b3e1ec918b89e57",
        ),
    )
    for relative, byte_count, digest in expected:
        payload = (REPO_ROOT.parent / relative).read_bytes()
        assert len(payload) == byte_count
        assert _sha256(payload) == digest


def test_bound_structural_graph_exact_identity() -> None:
    payload = (REPO_ROOT.parent / owner.STRUCTURAL_GRAPH_RELATIVE).read_bytes()
    assert len(payload) == 142747
    assert _sha256(payload) == (
        "a370deed014ec8a304b74ea0120e0c3615e72a4f391f8854c96e6a4284290ea4"
    )


def test_formal_semantic_digest_independently_recomputed(formal) -> None:
    clone = copy.deepcopy(formal)
    literal = clone.pop("formal_decision_semantic_canonical_sha256")
    assert _sha256(owner._canonical_json(clone)) == literal
    assert literal == owner.FORMAL_SEMANTIC_CANONICAL_SHA256


def test_formal_validator_is_provenance_only(monkeypatch) -> None:
    real_import = owner.importlib.import_module

    def guarded_import(name: str, *args, **kwargs):
        assert "validate_sr2_formal_human_decision_v1" not in name
        return real_import(name, *args, **kwargs)

    def subprocess_forbidden(*args, **kwargs):
        raise AssertionError("formal validator subprocess is forbidden")

    monkeypatch.setattr(owner.importlib, "import_module", guarded_import)
    monkeypatch.setattr(subprocess, "run", subprocess_forbidden)
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert bound["formal_validator_provenance_identity_only"] is True
    assert bound["formal_validator_imported"] is False
    assert bound["formal_validator_executed"] is False
    assert bound["formal_validator_subprocess_called"] is False
    assert bound["formal_validator_runtime_dependency"] is False


def test_owner_ast_has_no_formal_validator_import_or_subprocess() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
            imports.extend(alias.name for alias in node.names)
    assert not any("validate_sr2_formal_human_decision_v1" in name for name in imports)
    assert "subprocess" not in imports


def test_d1_through_d6_exact(formal) -> None:
    human = formal["human_authorization"]
    assert human["D1_task_relevance"] == "RELEVANT"
    assert human["D2_chemistry"] == "POSITIVE"
    assert human["D3_reactive_pair"] == "CONFIRM_OBSERVED_PAIR"
    assert human["D4_role_candidate"] == "SELECT_CANDIDATE_15"
    assert human["D5_training_use"] == "INCLUDE"
    assert human["D6_scientific_context"] == owner.EXPECTED_D6
    assert len(owner.EXPECTED_D6.encode()) == 1236
    assert _sha256(owner.EXPECTED_D6.encode()) == owner.EXPECTED_D6_SHA256


def test_finalization_and_human_authority_exact(formal) -> None:
    assert formal["approved"] is True
    assert formal["unsigned"] is False
    assert formal["decision_finalized"] is True
    assert formal["human_review_completed"] is True
    assert formal["human_decision_created"] is True
    assert formal["formal_authority_created"] is True
    assert formal["formal_authority_is_human"] is True
    assert formal["machine_approval"] is False
    assert formal["human_authorization"]["reviewer_id"] == "fmx"
    assert formal["human_authorization"]["attestor_id"] == "fmx"


def test_exact4_identity_order_contexts_and_distances(formal) -> None:
    identity = formal["identity"]
    assert tuple(identity["canonical_event_ids"]) == owner.EXPECTED_EVENT_IDS
    assert tuple(identity["scaleup_ranks"]) == owner.EXPECTED_RANKS
    assert identity["contexts_collapsed"] is False
    assert len(formal["event_level_formal_human_decisions"]) == 4
    assert [event["POST_distance_angstrom"] for event in formal["event_level_formal_human_decisions"]] == [
        1.676815, 1.867313, 1.856140, 1.864642,
    ]


def test_sample_sg_c51_pair_authority_is_not_reusable(formal) -> None:
    pair = formal["reactive_pair_authority"]
    assert pair["protein_reactive_atom"] == "SG"
    assert pair["ligand_reactive_atom"] == "C51"
    assert pair["reactive_pair_sample_authority"] is True
    assert pair["reusable_pair_rule_created"] is False
    assert pair["cross_structure_regiochemistry_generalization"] is False


def test_candidate15_role_partition_exact(formal) -> None:
    role = formal["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 15
    assert role["role_profile"] == owner.EXPECTED_ROLE_PROFILE
    assert role["W"] == list(owner.WARHEAD_ROLE)
    assert role["L"] == []
    assert role["S"] == list(owner.SCAFFOLD_ROLE)
    assert role["W_L_S_counts"] == [9, 0, 18]
    assert role["boundary_bonds"] == list(owner.BOUNDARY_BONDS)
    assert role["applicable_task_ids"] == [0, 3, 4]


def test_published_direct_runtime_revalidation() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    result = bound["published_DIRECT_runtime_validation"]
    assert result["valid"] is True
    assert result["reasons"] == []
    assert result["profile"] == owner.EXPECTED_ROLE_PROFILE
    assert [result["warhead_count"], result["linker_count"], result["scaffold_count"]] == [9, 0, 18]
    assert result["applicable_task_ids"] == [0, 3, 4]
    assert result["direct_scaffold_warhead_boundary"] == {
        "scaffold_atom_id": "C9",
        "warhead_atom_id": "N11",
        "bond_order": "SING",
        "boundary_valid": True,
    }


def test_completed_lane_and_training_use_allowed_are_published_semantics(snapshot, manifest) -> None:
    assert owner.EXPECTED_COMPLETED_LANE == "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
    assert snapshot["completed_lane_source_bound"] is True
    lane_binding = manifest["completed_lane_source_binding"]
    assert lane_binding["path"] == owner.COMPLETED_LANE_OWNER_RELATIVE.as_posix()
    assert lane_binding["byte_count"] == 66788
    assert lane_binding["SHA256"] == (
        "2e71c3132a15f500d54430075688c37dc79469b096328943795c98a728fca7ce"
    )
    assert snapshot["training_boundary"]["training_use_allowed"] is True


def test_canonical_exact5_b3_and_no_sixth(snapshot) -> None:
    contract = snapshot["canonical_task_contract"]
    assert [task["semantic_long_name"] for task in contract["global_canonical_tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert contract["direct_profile_applicable_task_ids"] == [0, 3, 4]


def test_event_matrix_exact4_order_and_modern_generic_schema(matrix) -> None:
    assert len(matrix) == 4
    assert tuple(matrix[0]) == owner.MATRIX_HEADER
    assert tuple(row["canonical_event_id"] for row in matrix) == owner.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in matrix) == owner.EXPECTED_RANKS
    assert "ENGINEERED_SURROGATE_CONTEXT" not in owner.MATRIX_HEADER
    assert "related_4FGC_context_only" not in owner.MATRIX_HEADER


def test_matrix_rows_project_positive_include_future_candidate_only(matrix) -> None:
    for row in matrix:
        assert row["completed_lane"] == owner.EXPECTED_COMPLETED_LANE
        assert row["task_relevance"] == "RELEVANT"
        assert row["chemistry"] == "POSITIVE"
        assert row["formal_event_training_use_decision"] == "INCLUDE"
        assert row["training_use_allowed"] == "true"
        assert row["human_training_excluded"] == "false"
        assert row["candidate_for_future_training_admission"] == "true"
        assert row["future_training_admission_candidate"] == "true"
        assert row["future_training_admission_status"] == owner.FUTURE_STATUS
        assert row["formal_training_admitted"] == "false"
        assert row["training_materialization_allowed"] == "false"
        assert row["tensor_target_created"] == "false"
        assert row["current_runtime_model_usable"] == "false"
        assert row["READY_FOR_TRAINING"] == "false"


def test_future_candidate_is_explicitly_not_admission(snapshot) -> None:
    training = snapshot["training_boundary"]
    assert training["future_training_admission_inclusion_reason"] == owner.FUTURE_INCLUSION_REASON
    assert training["future_training_admission_candidate_is_not_training_admission"] is True
    assert training["D5_INCLUDE_DOES_NOT_GRANT_TRAINING_ADMISSION"] is True
    assert training["D5_INCLUDE_DOES_NOT_GRANT_PARAMETER_UPDATE_AUTHORIZATION"] is True
    for field in (
        "training_admitted", "formal_training_admitted", "training_admission_created",
        "training_materialization_allowed_now", "training_materialization_allowed",
        "tensor_target_created", "model_supervision_usable",
        "training_mask_targets_available_now", "current_runtime_model_usable",
        "parameter_update_authorization", "READY_FOR_TRAINING",
    ):
        assert training[field] is False


def test_post_source_evidence_does_not_create_training_target(matrix, summary) -> None:
    assert summary["POST_source_evidence_event_count"] == 4
    assert summary["POST_training_authority_event_count"] == 0
    assert summary["POST_training_target_event_count"] == 0
    for row in matrix:
        assert row["POST_source_evidence_available"] == "true"
        assert row["POST_geometry_training_authority"] == "false"
        assert row["POST_geometry_training_target_created"] == "false"
        assert row["POST_geometry_training_label_available_now"] == "false"


def test_pre_source_graph_is_incompatible_and_never_synthesized(matrix, summary) -> None:
    assert summary["PRE_source_graph_present_event_count"] == 4
    assert summary["PRE_mapping_available_event_count"] == 0
    assert summary["PRE_training_target_event_count"] == 0
    for row in matrix:
        assert row["PRE_source_graph_present"] == "true"
        assert row["PRE_source_graph_count_per_event"] == "1"
        assert row["PRE_mapping_count_per_event"] == "0"
        assert row["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        assert row["PRE_status"] == "PRE_REACTION_UNRESOLVED"
        assert row["PRE_topology_authority"] == "false"
        assert row["PRE_geometry_authority"] == "false"
        assert row["PRE_coordinates_authority"] == "false"
        assert row["POST_to_PRE_copy"] == "false"
        assert row["PRE_zero_fill"] == "false"


def test_engineered_surrogate_caveat_is_retained_without_promotion(snapshot, summary, manifest) -> None:
    expected = owner._engineered_surrogate_caveat()
    assert snapshot["engineered_surrogate_caveat"] == expected
    assert summary["engineered_surrogate_caveat"] == expected
    assert manifest["engineered_surrogate_caveat"] == expected
    assert expected["ENGINEERED_SURROGATE_CONTEXT"] is True
    assert expected["TARGET_DIRECTED_MEDICINAL_COVALENT_CONTEXT"] is True
    for field in (
        "native_Src_S345_authority", "native_Src_site_training_authority",
        "EGFR_C797_event_specific_authority",
        "EGFR_T790M_event_specific_structure_authority",
        "cross_target_transfer_authority",
    ):
        assert expected[field] is False


def test_no_reusable_or_class_authority(matrix, summary) -> None:
    false_fields = (
        "reusable_pair_rule_created", "cross_structure_regiochemistry_generalization",
        "reusable_role_authority", "reusable_chemistry_authority",
        "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority",
        "reaction_family_training_class_target_available",
        "warhead_rule_training_class_target_available", "warhead_type_target_available",
        "reusable_authority_label_available",
    )
    for row in matrix:
        assert all(row[field] == "false" for field in false_fields)
    assert summary["reusable_chemistry_authority_event_count"] == 0
    assert summary["reusable_pair_authority_event_count"] == 0
    assert summary["reusable_role_authority_event_count"] == 0


def test_current_census_is_bound_read_only_and_pre_sr2(snapshot, manifest) -> None:
    boundary = snapshot["current_census_boundary"]
    assert boundary["SR2_current_global_status"] == "CURRENTLY_UNREVIEWED"
    assert boundary["SR2_current_review_status"] == "CURRENTLY_UNREVIEWED"
    assert boundary["SR2_human_review_completed"] is False
    assert boundary["SR2_chemistry_disposition"] == "UNRESOLVED"
    assert boundary["SR2_task_relevance_disposition"] == "UNRESOLVED"
    assert boundary["SR2_training_use_disposition"] == "UNRESOLVED"
    assert boundary["SR2_formal_training_admitted"] is False
    assert manifest["current_census_boundary"] == boundary


def test_current_census_manifest_binding_is_separate_from_boundary(snapshot, manifest) -> None:
    assert manifest["current_census_boundary"] == snapshot["current_census_boundary"]
    assert len(manifest["current_census_bindings"]) == 4
    assert manifest["current_census_bindings"][1]["SHA256"] == (
        "90b8038047e08b0c43537ec8738a46b741468ee7a66633a863f244039485264c"
    )


def test_metadata_only_boundary_is_exact(snapshot, summary, manifest) -> None:
    expected = owner._metadata_only_boundary()
    assert snapshot["metadata_only_boundary"] == expected
    assert summary["metadata_only_boundary"] == expected
    assert manifest["metadata_only_boundary"] == expected
    assert expected["metadata_only"] is True
    assert all(value is False for key, value in expected.items() if key != "metadata_only")


def test_matrix_states_the_metadata_only_boundary(matrix) -> None:
    expected = owner._metadata_only_boundary()
    for row in matrix:
        assert row["metadata_only"] == "true"
        for key, value in expected.items():
            if key != "metadata_only":
                assert value is False
                assert row[key] == "false"


def test_manifest_binds_sources_outputs_and_has_no_self_hash(artifacts, manifest) -> None:
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
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
        assert binding["SHA256"] == _sha256(artifacts[name])


def test_candidate_source_bindings_are_live_exact(manifest) -> None:
    records = manifest["candidate_source_bindings"]
    assert [record["path"] for record in records] == [
        owner.SOURCE_RELATIVE.as_posix(),
        owner.CHECKER_RELATIVE.as_posix(),
        owner.TEST_RELATIVE.as_posix(),
    ]
    for record in records:
        payload = (REPO_ROOT / record["path"]).read_bytes()
        assert record["byte_count"] == len(payload)
        assert record["SHA256"] == _sha256(payload)


def test_double_build_is_byte_identical(artifacts) -> None:
    assert owner.build_artifacts_v1(REPO_ROOT) == artifacts
    assert owner.build_artifacts_v1(REPO_ROOT) == artifacts


def test_materialization_is_exact_and_deterministic(tmp_path) -> None:
    first = owner.materialize_artifacts_v1(REPO_ROOT, output_root=tmp_path / "out")
    second = owner.materialize_artifacts_v1(REPO_ROOT, output_root=tmp_path / "out")
    assert first == second
    assert tuple(sorted(path.name for path in (tmp_path / "out").iterdir())) == tuple(
        sorted(owner.OUTPUT_FILENAMES)
    )


def test_live_materialized_outputs_match_fresh_build() -> None:
    result = owner.check_materialized_v1(REPO_ROOT)
    assert result["status"] == "PASS"
    assert result["exact_output_count"] == 4
    assert result["event_count"] == 4


def test_materialization_rejects_unexpected_destination_entry(tmp_path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    (output / "extra.txt").write_text("not authorized\n")
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.materialize_artifacts_v1(REPO_ROOT, output_root=output)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("human_training_excluded", "true"),
        ("candidate_for_future_training_admission", "false"),
        ("future_training_admission_candidate", "false"),
        ("formal_training_admitted", "true"),
        ("training_materialization_allowed", "true"),
        ("tensor_target_created", "true"),
        ("current_runtime_model_usable", "true"),
        ("parameter_update_authorization", "true"),
        ("READY_FOR_TRAINING", "true"),
        ("protein_reactive_atom", "NZ"),
        ("ligand_reactive_atom", "C10"),
        ("selected_candidate_index_0based", "14"),
        ("W_L_S_counts_json", "[8,0,19]"),
        ("boundary_bonds_json", "[]"),
        ("B3_present", "false"),
        ("sixth_task", "true"),
        ("PRE_mapping_status", "MAPPED"),
        ("PRE_topology_authority", "true"),
        ("PRE_geometry_authority", "true"),
        ("POST_geometry_training_target_created", "true"),
        ("reusable_chemistry_authority", "true"),
        ("reaction_family_authority", "true"),
        ("warhead_rule_authority", "true"),
        ("warhead_type_authority", "true"),
    ],
)
def test_matrix_authority_promotions_fail_closed(artifacts, field, value) -> None:
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(
            _matrix_mutation(artifacts, field, value)
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("training_admission_created", True),
        ("training_materialization_allowed", True),
        ("tensor_target_created", True),
        ("current_runtime_model_usable", True),
        ("parameter_update_authorization", True),
        ("READY_FOR_TRAINING", True),
    ],
)
def test_snapshot_training_promotions_fail_closed(artifacts, field, value) -> None:
    changed = _json_mutation(
        artifacts,
        owner.SNAPSHOT,
        lambda doc: doc["training_boundary"].__setitem__(field, value),
    )
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


@pytest.mark.parametrize(
    "field",
    [
        "native_Src_S345_authority",
        "native_Src_site_training_authority",
        "EGFR_C797_event_specific_authority",
        "EGFR_T790M_event_specific_structure_authority",
        "cross_target_transfer_authority",
    ],
)
def test_engineered_surrogate_promotions_fail_closed(artifacts, field) -> None:
    changed = _json_mutation(
        artifacts,
        owner.SNAPSHOT,
        lambda doc: doc["engineered_surrogate_caveat"].__setitem__(field, True),
    )
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_candidate_partition_mutations_fail_closed(artifacts) -> None:
    mutations = (
        lambda doc: doc["selected_role_partition"]["W"].pop(),
        lambda doc: doc["selected_role_partition"].__setitem__("L", ["C9"]),
        lambda doc: doc["selected_role_partition"]["S"].pop(),
        lambda doc: doc["selected_role_partition"].__setitem__("boundary_bonds", []),
    )
    for mutate in mutations:
        changed = _json_mutation(artifacts, owner.SNAPSHOT, mutate)
        with pytest.raises(owner.SR2IngestionSafetyError):
            owner.validate_completed_decision_projection_v1(changed)


def test_manifest_validator_execution_mutations_fail_closed(artifacts) -> None:
    for field in (
        "frozen_formal_validator_imported",
        "frozen_formal_validator_executed",
        "frozen_formal_validator_subprocess_called",
        "formal_validator_runtime_dependency",
    ):
        changed = _json_mutation(
            artifacts, owner.MANIFEST, lambda doc, key=field: doc.__setitem__(key, True)
        )
        with pytest.raises(owner.SR2IngestionSafetyError):
            owner.validate_completed_decision_projection_v1(changed)


def test_output_inventory_order_and_count_fail_closed(artifacts) -> None:
    missing = dict(artifacts)
    missing.pop(owner.SUMMARY)
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(missing)
    reordered = dict(reversed(list(artifacts.items())))
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(reordered)


def test_mutated_formal_json_bytes_fail_binding(tmp_path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    target = tmp_path / "formal.json"
    target.write_bytes(source.read_bytes().replace(b'"INCLUDE"', b'"EXCLUDE"', 1))
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.load_frozen_formal_decision_v1(REPO_ROOT, formal_decision_path=target)


def test_mutated_formal_validator_bytes_fail_binding(tmp_path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    target = tmp_path / "validator.py"
    target.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.load_frozen_formal_decision_v1(REPO_ROOT, formal_validator_path=target)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("human_authorization", "D5_training_use"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (("human_authorization", "D4_role_candidate"), "SELECT_CANDIDATE_14"),
        (("identity", "protein_reactive_atom"), "NZ"),
        (("identity", "ligand_reactive_atom"), "C10"),
        (("selected_role_partition", "W"), ["C51"]),
        (("selected_role_partition", "L"), ["C9"]),
        (("selected_role_partition", "boundary_bonds"), []),
        (("canonical_Exact5_and_sample_applicability", "B3_present"), False),
        (("canonical_Exact5_and_sample_applicability", "sixth_task_present"), True),
        (("training_use_boundary", "human_training_excluded"), True),
        (("training_use_boundary", "future_training_admission_candidate"), False),
        (("training_use_boundary", "formal_training_admitted"), True),
        (("training_use_boundary", "training_admission_created"), True),
        (("training_use_boundary", "training_materialization_allowed"), True),
        (("training_use_boundary", "tensor_target_created"), True),
        (("training_use_boundary", "current_runtime_model_usable"), True),
        (("training_use_boundary", "parameter_update_authorization"), True),
        (("training_use_boundary", "READY_FOR_TRAINING"), True),
        (("PRE_POST_boundary", "PRE_mapping_status"), "MAPPED"),
        (("PRE_POST_boundary", "PRE_topology_authority"), True),
        (("PRE_POST_boundary", "PRE_geometry_authority"), True),
        (("PRE_POST_boundary", "POST_to_PRE_copy_performed"), True),
        (("POST_evidence_boundary", "POST_geometry_training_target_created"), True),
        (("engineered_surrogate_caveat", "native_Src_S345_authority"), True),
        (("engineered_surrogate_caveat", "EGFR_C797_event_specific_authority"), True),
        (("engineered_surrogate_caveat", "cross_target_transfer_authority"), True),
        (("authority_boundary", "reusable_chemistry_authority"), True),
        (("authority_boundary", "reusable_pair_authority"), True),
        (("authority_boundary", "reusable_role_authority"), True),
        (("authority_boundary", "reaction_family_authority"), True),
        (("authority_boundary", "warhead_rule_authority"), True),
        (("authority_boundary", "warhead_type_authority"), True),
    ],
)
def test_recomputed_formal_semantic_mutations_still_fail_closed(formal, path, value) -> None:
    changed = copy.deepcopy(formal)
    _set_path(changed, path, value)
    digest_input = copy.deepcopy(changed)
    digest_input.pop("formal_decision_semantic_canonical_sha256")
    changed["formal_decision_semantic_canonical_sha256"] = _sha256(
        owner._canonical_json(digest_input)
    )
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner._validate_formal_document(changed)


@pytest.mark.parametrize(
    "payload",
    [b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'{"a":Infinity}\n'],
)
def test_strict_json_rejects_duplicate_keys_and_nonfinite(payload) -> None:
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner._strict_json_loads(payload, "TEST")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timestamp", "2026-09-03T00:00:00Z"),
        ("hostname", "builder-1"),
        ("PID", 123),
        ("random_UUID", "00000000-0000-0000-0000-000000000000"),
        ("path", "/machine/private/path"),
    ],
)
def test_dynamic_or_machine_metadata_fails_closed(artifacts, field, value) -> None:
    changed = _json_mutation(
        artifacts, owner.SNAPSHOT, lambda doc: doc.__setitem__(field, value)
    )
    with pytest.raises(owner.SR2IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_candidate_and_future_tracked_lifecycle_profiles() -> None:
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


def test_lifecycle_rejects_baseline_drift_staging_behind_and_missing_exact7() -> None:
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
    with pytest.raises(SystemExit):
        checker.classify_repository_profile(
            head=checker.BASELINE_HEAD,
            origin=checker.BASELINE_HEAD,
            tracked_modifications=set(),
            staged_paths={next(iter(expected))},
            untracked_paths=expected,
            expected_paths=expected,
        )
    case = {
        "profile": checker.TRACKED_CLEAN,
        "head": "3" * 40,
        "origin": "2" * 40,
        "ahead": 2,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin": True,
        "origin_ancestor_of_head": True,
        "changed_paths": expected,
        "expected_paths": expected,
    }
    for mutation in ({"behind": 1}, {"changed_paths": set()}):
        changed = dict(case)
        changed.update(mutation)
        with pytest.raises(SystemExit):
            checker.validate_repository_relation_values(**changed)


def test_no_forbidden_candidate_suffix_or_protected_path() -> None:
    expected = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    checker.check_forbidden_files(expected)
    assert not any(path.endswith(checker.FORBIDDEN_SUFFIXES) for path in expected)
    assert not any(path.startswith(checker.PROTECTED_PREFIXES) for path in expected)


def test_small_published_include_and_exclude_semantic_regressions() -> None:
    four_m5 = json.loads(
        (
            REPO_ROOT
            / "data/derived/covalent_small/"
            "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1/"
            "covapie_4m5_completed_decision_ingestion_summary_v1.json"
        ).read_bytes()
    )
    gd1 = json.loads(
        (
            REPO_ROOT
            / "data/derived/covalent_small/"
            "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1/"
            "covapie_gd1_completed_decision_ingestion_summary_v1.json"
        ).read_bytes()
    )
    assert four_m5["training_use_INCLUDE_event_count"] == 4
    assert four_m5["future_training_admission_candidate_count"] == 4
    assert four_m5["formal_training_admitted_count"] == 0
    assert gd1["training_use_EXCLUDE_FROM_TRAINING_ONLY_event_count"] == 4
    assert gd1["human_training_excluded_event_count"] == 4
    assert gd1["future_training_admission_candidate_count"] == 0
