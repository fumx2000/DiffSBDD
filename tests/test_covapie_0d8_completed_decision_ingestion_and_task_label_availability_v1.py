from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import stat
import sys

import pytest

from covalent_ext import (
    covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
LCY_MATRIX = (
    REPO_ROOT
    / "data/derived/covalent_small/"
    "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_lcy_event_task_label_availability_v1.csv"
)


def strict_json(payload: bytes) -> dict[str, object]:
    return json.loads(payload.decode("utf-8"))


def matrix_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    assert reader.fieldnames is not None
    return tuple(reader.fieldnames), list(reader)


def json_payload(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def set_path(value: object, path: tuple[object, ...], replacement: object) -> None:
    current = value
    for key in path[:-1]:
        current = current[key]  # type: ignore[index]
    current[path[-1]] = replacement  # type: ignore[index]


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return strict_json(artifacts[owner.SNAPSHOT])


def test_public_api_is_exact_and_compact() -> None:
    assert owner.__all__ == (
        "ZeroD8IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )
    assert issubclass(owner.ZeroD8IngestionSafetyError, ValueError)


def test_candidate_exact7_inventory_and_security() -> None:
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert owner.CANDIDATE_PUBLICATION_PATHS == (
        owner.SOURCE_RELATIVE,
        owner.CHECKER_RELATIVE,
        owner.TEST_RELATIVE,
        *owner.OUTPUT_RELATIVE_PATHS,
    )
    for relative in owner.CANDIDATE_PUBLICATION_PATHS:
        path = REPO_ROOT / relative
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)
        assert not metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    assert {path.name for path in (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE).iterdir()} == set(
        owner.OUTPUT_FILENAMES
    )


def test_formal_json_and_validator_identity_and_lifecycle(snapshot: dict[str, object]) -> None:
    formal_path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    validator_path = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    formal_payload = formal_path.read_bytes()
    validator_payload = validator_path.read_bytes()
    assert len(formal_payload) == 36906
    assert hashlib.sha256(formal_payload).hexdigest() == owner.FORMAL_BINDINGS[0][3]
    assert len(formal_payload.decode("utf-8").splitlines()) == 807
    assert len(validator_payload) == 88809
    assert hashlib.sha256(validator_payload).hexdigest() == owner.FORMAL_BINDINGS[1][3]
    validator_metadata = validator_path.lstat()
    assert stat.S_ISREG(validator_metadata.st_mode)
    assert not stat.S_ISLNK(validator_metadata.st_mode)
    assert not validator_metadata.st_mode & (
        stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    lifecycle = snapshot["formal_validator_lifecycle"]
    assert lifecycle == {
        "lifecycle": "PROVENANCE_IDENTITY_ONLY",
        "imported": False,
        "executed": False,
        "subprocessed": False,
        "parsed": False,
        "ast_parsed": False,
        "runtime_dependency": False,
    }
    assert not any(name.endswith("validate_0d8_formal_human_decision_v1") for name in sys.modules)


def test_formal_semantic_digest_d1_d6_and_exact7_authority(snapshot: dict[str, object]) -> None:
    formal = strict_json((REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes())
    clone = copy.deepcopy(formal)
    literal = clone.pop("formal_decision_semantic_canonical_sha256")
    observed = hashlib.sha256(
        json.dumps(
            clone,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert literal == observed == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    d6 = snapshot["formal_D1_D6"]
    assert [d6[f"D{i}"] for i in range(1, 6)] == [
        "NOT_RELEVANT",
        "POSITIVE",
        "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_0",
        "NOT_APPLICABLE",
    ]
    assert len(d6["D6"].encode("utf-8")) == 1575
    assert hashlib.sha256(d6["D6"].encode("utf-8")).hexdigest() == owner.EXPECTED_D6_SHA256
    authority = snapshot["formal_core_authority"]
    assert authority["true_count"] == 7
    assert authority["true_set"] == [
        "formal_authority_created",
        "formal_authority_is_human",
        "sample_task_relevance_authority",
        "sample_positive_chemistry_authority",
        "sample_reactive_pair_authority",
        "sample_role_partition_authority",
        "human_training_use_disposition_authority",
    ]
    assert authority["eighth_authority"] is False
    assert authority["reusable_authority_created"] is False


def test_exact4_identity_lane_and_post_distances(snapshot: dict[str, object]) -> None:
    target = snapshot["target_Exact4"]
    assert target["canonical_event_ids"] == list(owner.EXPECTED_EVENT_IDS)
    assert target["scaleup_ranks"] == [909, 910, 911, 912]
    assert target["review_unit_id"] == owner.EXPECTED_REVIEW_UNIT_ID
    assert target["pdb_id"] == "4V37"
    assert target["ligand_component_id"] == "0D8"
    assert target["ligand_wide_selector"] is False
    events = snapshot["events"]
    assert [event["POST_distance_frozen_lexeme"] for event in events] == [
        "1.708043", "1.730046", "1.722747", "1.703643"
    ]
    assert {event["completed_lane"] for event in events} == {
        "COMPLETED_TASK_DOMAIN_NEGATIVE"
    }
    assert all(event["task_relevance"] == "NOT_RELEVANT" for event in events)
    assert all(event["chemistry"] == "POSITIVE" for event in events)
    assert all(event["negative_chemistry"] is False for event in events)


def test_matrix_is_exact_lcy_modern_4_by_115(artifacts: dict[str, bytes]) -> None:
    header, rows = matrix_rows(artifacts[owner.MATRIX])
    lcy_header, _ = matrix_rows(LCY_MATRIX.read_bytes())
    assert header == lcy_header == owner.MATRIX_HEADER
    assert len(header) == 115
    assert len(rows) == 4
    assert [int(row["scaleup_rank"]) for row in rows] == [909, 910, 911, 912]
    assert all(row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE" for row in rows)
    assert all(row["task_relevance"] == "NOT_RELEVANT" for row in rows)
    assert all(row["chemistry"] == "POSITIVE" for row in rows)


def test_pair_role_direct_runtime_and_applicability(snapshot: dict[str, object]) -> None:
    pair = snapshot["reactive_pair_authority"]
    assert pair["protein_reactive_atom"] == "SG"
    assert pair["ligand_reactive_atom"] == "C8"
    assert pair["reactive_pair_human_authoritative"] is True
    assert pair["pair_authority_scope"] == owner.PAIR_AUTHORITY_SCOPE
    assert pair["reusable_pair_rule_created"] is False
    role = snapshot["selected_role_partition"]
    assert role == {
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "selected_candidate_index_0based": 0,
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "warhead_atoms": ["C8", "OH"],
        "linker_atoms": [],
        "scaffold_atoms": ["C7", "CA3", "N3"],
        "W_L_S_counts": [2, 0, 3],
        "boundary_bonds": [
            {
                "atom_id_1": "C7",
                "atom_id_2": "C8",
                "bond_order": "SING",
                "role_1": "S",
                "role_2": "W",
            }
        ],
        "role_authority_scope": owner.ROLE_AUTHORITY_SCOPE,
        "reusable_role_authority": False,
        "independent_mask_authority_created": False,
    }
    runtime = snapshot["published_DIRECT_runtime_revalidation"]
    assert runtime["runtime_import_path_exact"] is True
    assert runtime["call_count_for_selected_partition"] == 1
    assert runtime["valid"] is True
    assert runtime["reasons"] == []
    assert runtime["sample_applicable_task_ids"] == [0, 3, 4]


def test_exact5_b3_and_no_materialized_training_targets(snapshot: dict[str, object]) -> None:
    contract = snapshot["canonical_task_contract"]
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert [task["semantic_long_name"] for task in contract["tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [task["structurally_applicable"] for task in contract["tasks"]] == [
        True, False, False, True, True
    ]
    assert contract["sample_applicable_task_ids"] == [0, 3, 4]
    assert contract["task_applicability_determined"] is True
    assert contract["authoritative_task_labels_created"] is False
    assert contract["event_task_label_rows_materialized"] is False
    assert all(task["training_mask_target_available_now"] is False for task in contract["tasks"])


def test_d5_pre_post_and_reusable_boundaries(snapshot: dict[str, object]) -> None:
    training = snapshot["training_boundary"]
    assert training["formal_event_training_use_decision"] == "NOT_APPLICABLE"
    assert training["human_training_excluded"] is False
    assert training["future_training_admission_candidate"] is False
    assert training["training_materialization_allowed"] is False
    assert training["READY_FOR_TRAINING"] is False
    pre = snapshot["PRE_boundary"]
    assert pre["supporting_PRE_source_graph_count_per_event"] == 0
    assert pre["PRE_source_graph_present"] is False
    assert pre["PRE_mapping_count_per_event"] == 0
    assert pre["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    post = snapshot["POST_boundary"]
    assert post["POST_source_evidence_available"] is True
    assert post["explicit_covalent_evidence"] is True
    assert post["distance_only_inference"] is False
    assert post["POST_geometry_training_authority"] is False
    assert post["POST_geometry_training_label_available_now"] is False
    assert all(value is False for value in snapshot["reusable_authority_boundary"].values())


def test_generic_actual_exact11_and_rich_field_firewall(snapshot: dict[str, object]) -> None:
    generic = snapshot["generic_Exact11_compatibility"]
    assert generic["generic_exact11_compatibility_pass"] is True
    assert generic["generic_fact_field_count"] == 11
    assert generic["generic_fact_fields"] == list(owner.GENERIC_FACT_FIELDS)
    assert generic["accepted_fact_count"] == 4
    source = generic["actual_source_binding"]
    assert source["path_namespace"] == "repository_parent_relative"
    assert source["source_path"] == owner.FORMAL_DECISION_RELATIVE.as_posix()
    assert source["sha256"] == owner.FORMAL_BINDINGS[0][3]
    assert generic["scientific_synthetic_probe_used"] is False
    assert generic["reconciliation_performed"] is False
    rich = {
        "protein_reactive_atom", "ligand_reactive_atom", "selected_candidate_index_0based",
        "role_profile", "W_L_S_counts", "boundary_bonds", "task_applicability",
        "PRE", "POST", "CCD", "Q", "reaction_family", "warhead_rule",
        "warhead_type", "training_admission", "tensor_target",
    }
    for fact in generic["facts"]:
        assert len(fact) == 11
        assert set(fact) == set(owner.GENERIC_FACT_FIELDS)
        assert not rich.intersection(fact)
        assert fact["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert fact["task_relevance_disposition"] == "NOT_RELEVANT"
        assert fact["chemistry_disposition"] == "POSITIVE"
        assert fact["training_disposition"] == "NOT_APPLICABLE"


def test_active_bindings_are_unique_exact10_without_precedent_owners(snapshot: dict[str, object]) -> None:
    bindings = snapshot["active_source_binding_count"]
    assert bindings == 10
    manifest_bindings = owner._standalone_bound()["active_source_bindings"]
    identities = [record["semantic_source_identity"] for record in manifest_bindings]
    assert len(identities) == len(set(identities)) == 10
    paths = {record["path"] for record in manifest_bindings}
    assert owner.DIRECT_RUNTIME_OWNER_RELATIVE.as_posix() in paths
    assert owner.GENERIC_OWNER_RELATIVE.as_posix() in paths
    assert not any("covapie_lcy_completed_decision_ingestion" in path for path in paths)
    assert not any("covapie_4m5_completed_decision_ingestion" in path for path in paths)


def test_current_census_is_preformal_8_and_future_12_is_arithmetic_only(
    snapshot: dict[str, object], artifacts: dict[str, bytes]
) -> None:
    census_path = REPO_ROOT / owner.CENSUS_MATRIX_RELATIVE
    before = hashlib.sha256(census_path.read_bytes()).hexdigest()
    census = snapshot["current_with_LCY_census_preformal_boundary"]
    assert census["current_global_status"] == "CURRENTLY_UNREVIEWED"
    assert census["human_review_completed"] is False
    assert census["chemistry"] == "UNRESOLVED"
    assert census["task_relevance"] == "UNRESOLVED"
    assert census["training_use"] == "UNRESOLVED"
    assert census["pair_authority"] is False
    assert census["role_authority"] is False
    assert census["role_profile"] == "NOT_ESTABLISHED"
    assert census["mask_labels_available"] is False
    assert census["current_orthogonal_population"] == 8
    assert census["current_orthogonal_breakdown"] == {"GVE": 4, "LCY": 4}
    assert census["future_with_0D8_orthogonal_count_preview"] == 12
    assert census["future_arithmetic_only"] is True
    assert census["census_refresh_performed"] is False
    owner.validate_completed_decision_projection_v1(artifacts)
    assert hashlib.sha256(census_path.read_bytes()).hexdigest() == before == owner.CENSUS_BINDING[3]


def test_summary_manifest_and_operation_boundaries(artifacts: dict[str, bytes]) -> None:
    summary = strict_json(artifacts[owner.SUMMARY])
    expected_counts = {
        "event_count": 4,
        "completed_review_unit_count": 1,
        "task_not_relevant_count": 4,
        "chemistry_positive_count": 4,
        "negative_chemistry_count": 0,
        "pair_authority_event_count": 4,
        "role_authority_event_count": 4,
        "task_applicability_determined_event_count": 4,
        "authoritative_task_label_event_count": 0,
        "event_task_label_rows_materialized_count": 0,
        "training_not_applicable_count": 4,
        "human_training_excluded_count": 0,
        "future_training_candidate_count": 0,
        "formal_training_admitted_count": 0,
        "tensor_target_count": 0,
        "runtime_usable_count": 0,
        "PRE_source_graph_present_count": 0,
        "PRE_mapping_count": 0,
        "PRE_resolved_count": 0,
        "POST_source_evidence_count": 4,
        "POST_training_authority_count": 0,
        "generic_exact11_accepted_count": 4,
        "active_source_binding_count": 10,
        "current_orthogonal_population": 8,
        "future_orthogonal_population_preview": 12,
    }
    for key, expected in expected_counts.items():
        assert summary[key] == expected
    manifest = strict_json(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert len(manifest["candidate_source_bindings"]) == 3
    assert len(manifest["active_source_bindings"]) == 10
    assert set(manifest["output_artifact_bindings"]) == {
        owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY
    }
    assert owner.MANIFEST not in manifest["output_artifact_bindings"]
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert manifest["MANIFEST_SELF_SHA256_PROHIBITED"] is True
    operation = manifest["operation_boundary"]
    assert operation["metadata_only"] is True
    assert operation["projection_of_frozen_formal_human_authority"] is True
    assert operation["new_human_authority_created_by_ingestion"] is False
    for key in (
        "dataset_mutated", "training_dataset_changed", "tensorization", "loader_modified",
        "batch_modified", "model_forward", "loss", "backward", "optimizer",
        "parameter_update", "training", "reconciliation", "census_refresh", "queue_refresh",
    ):
        assert operation[key] is False


def test_deterministic_double_build_and_materialized_closure(artifacts: dict[str, bytes]) -> None:
    second = owner.build_artifacts_v1(REPO_ROOT)
    assert artifacts == second
    owner.validate_completed_decision_projection_v1(artifacts, repo_root=REPO_ROOT)
    observed = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    assert observed == artifacts
    result = owner.check_materialized_v1(REPO_ROOT)
    assert result["status"] == "PASS"
    assert result["byte_identical_to_rebuild"] is True
    assert result["READY_FOR_EXTERNAL_REVIEW"] is True
    assert result["READY_FOR_TRAINING"] is False


def test_formal_sha_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    mutated = tmp_path / source.name
    payload = bytearray(source.read_bytes())
    payload[-2] = ord(" ") if payload[-2] != ord(" ") else ord("\t")
    mutated.write_bytes(payload)
    with pytest.raises(owner.ZeroD8IngestionSafetyError, match="SOURCE_BINDING_FAILED"):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT,
            source_overrides={owner.FORMAL_DECISION_RELATIVE: mutated},
        )


def test_formal_validator_executable_class_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    mutated = tmp_path / source.name
    mutated.write_bytes(source.read_bytes())
    mutated.chmod(0o755)
    with pytest.raises(owner.ZeroD8IngestionSafetyError, match="SOURCE_BINDING_FAILED"):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT,
            source_overrides={owner.FORMAL_VALIDATOR_RELATIVE: mutated},
        )


FORMAL_MUTATIONS = (
    (("D1_formal_task_relevance", "D1"), "RELEVANT"),
    (("D2_formal_chemistry", "D2"), "NOT_ESTABLISHED"),
    (("D3_formal_reactive_pair", "D3"), "UNRESOLVED"),
    (("D4_formal_role_partition", "D4"), "UNRESOLVED"),
    (("D4_formal_role_partition", "sample_role_partition_authority"), False),
    (("D4_formal_role_partition", "selected_candidate_index_0based"), 1),
    (("D4_formal_role_partition", "W_L_S_counts"), [1, 1, 3]),
    (("D4_formal_role_partition", "boundary", "atom_id_1"), "CA3"),
    (("canonical_Exact5_and_sample_applicability", "sample_applicable_task_ids"), [0, 4]),
    (("canonical_Exact5_and_sample_applicability", "authoritative_task_labels_created"), True),
    (("canonical_Exact5_and_sample_applicability", "event_task_label_rows_materialized"), True),
    (("D5_formal_training_use", "D5"), "INCLUDE"),
    (("D5_formal_training_use", "D5"), "EXCLUDE_FROM_TRAINING_ONLY"),
    (("D5_formal_training_use", "human_training_excluded"), True),
    (("PRE_boundary", "per_event", 0, "PRE_source_graph_present"), True),
    (("PRE_boundary", "per_event", 0, "PRE_mapping_status"), "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"),
    (("PRE_boundary", "per_event", 0, "PRE_status"), "PRE_REACTION_RESOLVED"),
    (("POST_boundary", "POST_geometry_training_authority"), True),
    (("same_structure_Q_boundary", "Q_current_target"), True),
    (("target_selection", "ligand_wide_selection"), True),
    (("D2_formal_chemistry", "reaction_family_authority"), True),
    (("D2_formal_chemistry", "warhead_rule_authority"), True),
    (("D2_formal_chemistry", "warhead_type_authority"), True),
    (("readiness", "READY_FOR_TRAINING"), True),
    (("operation_boundary", "training"), True),
    (("operation_boundary", "reconciliation"), True),
    (("operation_boundary", "census_refresh"), True),
)


@pytest.mark.parametrize(("path", "replacement"), FORMAL_MUTATIONS)
def test_formal_semantic_mutations_fail_closed(
    path: tuple[object, ...], replacement: object
) -> None:
    formal = strict_json((REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes())
    set_path(formal, path, replacement)
    semantic = copy.deepcopy(formal)
    semantic.pop("formal_decision_semantic_canonical_sha256")
    formal["formal_decision_semantic_canonical_sha256"] = hashlib.sha256(
        json.dumps(
            semantic,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner._validate_formal_document(formal)


MATRIX_MUTATIONS = (
    ("task_relevance", "RELEVANT"),
    ("chemistry", "NOT_ESTABLISHED"),
    ("role_partition_human_authoritative", "false"),
    ("selected_candidate_index_0based", "1"),
    ("W_L_S_counts_json", "[1,1,3]"),
    ("boundary_bonds_json", "[]"),
    ("direct_profile_applicable_task_ids_json", "[0,4]"),
    ("authoritative_task_labels_created", "true"),
    ("event_task_label_rows_materialized", "true"),
    ("training_mask_targets_available_now", "true"),
    ("formal_event_training_use_decision", "INCLUDE"),
    ("formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"),
    ("human_training_excluded", "true"),
    ("PRE_source_graph_present", "true"),
    ("PRE_mapping_status", "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"),
    ("PRE_status", "PRE_REACTION_RESOLVED"),
    ("POST_geometry_training_authority", "true"),
    ("reaction_family_authority", "true"),
    ("warhead_rule_authority", "true"),
    ("warhead_type_authority", "true"),
    ("training", "true"),
    ("READY_FOR_TRAINING", "true"),
)


@pytest.mark.parametrize(("field", "replacement"), MATRIX_MUTATIONS)
def test_matrix_mutations_fail_closed(
    artifacts: dict[str, bytes], field: str, replacement: str
) -> None:
    changed = dict(artifacts)
    _header, rows = matrix_rows(changed[owner.MATRIX])
    rows[0][field] = replacement
    changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, rows)
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


SNAPSHOT_MUTATIONS = (
    (("formal_validator_lifecycle", "executed"), True),
    (("formal_validator_lifecycle", "imported"), True),
    (("same_structure_Q_boundary", "Q_row_materialized"), True),
    (("generic_Exact11_compatibility", "actual_source_binding", "path_namespace"), "project_parent_relative"),
    (("generic_Exact11_compatibility", "actual_source_binding", "source_path"), "synthetic/scientific-probe.json"),
    (("generic_Exact11_compatibility", "facts", 0, "legacy_completed_review_status"), "COMPLETED_HUMAN_POSITIVE"),
    (("current_with_LCY_census_preformal_boundary", "current_census_modified"), True),
    (("current_with_LCY_census_preformal_boundary", "current_orthogonal_population"), 12),
    (("operation_boundary", "queue_refresh"), True),
)


@pytest.mark.parametrize(("path", "replacement"), SNAPSHOT_MUTATIONS)
def test_snapshot_boundary_mutations_fail_closed(
    artifacts: dict[str, bytes], path: tuple[object, ...], replacement: object
) -> None:
    changed = dict(artifacts)
    value = strict_json(changed[owner.SNAPSHOT])
    set_path(value, path, replacement)
    changed[owner.SNAPSHOT] = json_payload(value)
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_generic_rich_role_field_leak_fails_closed(artifacts: dict[str, bytes]) -> None:
    changed = dict(artifacts)
    value = strict_json(changed[owner.SNAPSHOT])
    value["generic_Exact11_compatibility"]["facts"][0]["role_profile"] = (
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    )
    changed[owner.SNAPSHOT] = json_payload(value)
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_q_fifth_matrix_row_fails_closed(artifacts: dict[str, bytes]) -> None:
    changed = dict(artifacts)
    _header, rows = matrix_rows(changed[owner.MATRIX])
    fifth = dict(rows[0])
    fifth["canonical_event_id"] = fifth["canonical_event_id"].replace(":F:", ":Q:")
    fifth["ligand_chain_or_asym"] = "Q"
    changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, [*rows, fifth])
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_manifest_self_sha_and_unapproved_eighth_file_fail_closed(
    artifacts: dict[str, bytes]
) -> None:
    changed = dict(artifacts)
    manifest = strict_json(changed[owner.MANIFEST])
    manifest["self_sha256"] = "0" * 64
    changed[owner.MANIFEST] = json_payload(manifest)
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)
    changed = dict(artifacts)
    changed["guide.md"] = b"forbidden eighth file\n"
    with pytest.raises(owner.ZeroD8IngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)
