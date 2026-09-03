from __future__ import annotations

import ast
import copy
import csv
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_gve_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _json_artifact(artifacts: dict[str, bytes], name: str) -> dict[str, object]:
    value = json.loads(artifacts[name])
    assert type(value) is dict
    return value


def _matrix(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))


def _mutate_snapshot(
    artifacts: dict[str, bytes], mutation: callable
) -> dict[str, bytes]:
    changed = dict(artifacts)
    snapshot = _json_artifact(changed, owner.SNAPSHOT)
    mutation(snapshot)
    changed[owner.SNAPSHOT] = owner._json_bytes(snapshot)
    return changed


def _set_path(value: dict[str, object], path: tuple[str, ...], replacement: object) -> None:
    target: dict[str, object] = value
    for key in path[:-1]:
        child = target[key]
        assert type(child) is dict
        target = child
    target[path[-1]] = replacement


def test_public_api_is_exact6() -> None:
    assert owner.__all__ == (
        "GVEIngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_frozen_formal_sources_and_semantics_are_bound_without_validator_execution() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    formal_binding = bound["formal_decision_binding"]
    validator_binding = bound["formal_validator_binding"]
    assert formal_binding["byte_count"] == 26844
    assert formal_binding["SHA256"] == (
        "0df008d9fe2e142120a22ce6797aaf633725d4627eb6ca8e1be9f869ad0896e2"
    )
    assert validator_binding["byte_count"] == 74026
    assert validator_binding["SHA256"] == (
        "8b640f5e8305d8ded1d01efac304fd0d73f5fec2b4a57e72ee19b65e8297862c"
    )
    assert bound["formal_semantics_independently_validated"] is True
    assert bound["formal_validator_provenance_identity_only"] is True
    for key in (
        "formal_validator_imported",
        "formal_validator_parsed",
        "formal_validator_executed",
        "formal_validator_subprocessed",
        "formal_validator_runtime_dependency",
    ):
        assert bound[key] is False
    formal = bound["formal"]
    assert formal["schema_version"] == owner.FORMAL_DECISION_SCHEMA
    assert formal["record_role"] == owner.FORMAL_RECORD_ROLE
    assert owner._semantic_digest(formal) == owner.FORMAL_SEMANTIC_CANONICAL_SHA256
    decision = formal["inherited_human_decision"]
    assert [decision[f"D{index}_{name}"] for index, name in (
        (1, "task_relevance"),
        (2, "chemistry"),
        (3, "reactive_pair"),
        (4, "role_candidate"),
        (5, "training_use"),
    )] == [
        "NOT_RELEVANT",
        "POSITIVE",
        "CONFIRM_OBSERVED_PAIR",
        "UNRESOLVED",
        "NOT_APPLICABLE",
    ]
    assert len(decision["D6_scientific_context"].encode("utf-8")) == 1332
    assert decision["D6_utf8_sha256"] == owner.EXPECTED_D6_SHA256


def test_owner_source_cannot_import_parse_or_execute_formal_validator() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = "validate_gve_formal_human_decision_v1"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(forbidden not in alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert forbidden not in (node.module or "")
            assert all(forbidden not in alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            strings = {
                child.value
                for child in ast.walk(node)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)
            }
            assert not any(forbidden in value for value in strings)
    assert "import subprocess" not in source
    assert "from subprocess" not in source


def test_exact4_supporting_sources_and_read_only_census_are_validated() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    evidence = bound["event_evidence_validation"]
    graph = bound["graph_candidate_validation"]
    census = bound["current_census_boundary"]
    assert evidence == {
        "event_count": 4,
        "event_ids": list(owner.EXPECTED_EVENT_IDS),
        "scaleup_ranks": list(owner.EXPECTED_RANKS),
        "POST_source_evidence_event_count": 4,
        "PRE_source_graph_present_event_count": 4,
        "PRE_mapping_count": 0,
        "legacy_1XD3_included": False,
    }
    assert graph["candidate_indices_evidence_only"] == [0, 1, 2]
    assert graph["machine_candidate_selected"] is False
    assert graph["role_authority_created"] is False
    assert census["source_SHA256"] == (
        "f1657449f758d2e2f6ebcd76c5dfc955fac2568edb2623809497a8a1b1ea6d81"
    )
    assert census["current_global_status"] == "CURRENTLY_UNREVIEWED"
    assert census["human_review_completed"] is False
    assert census["chemistry"] == "UNRESOLVED"
    assert census["task_relevance"] == "UNRESOLVED"
    assert census["training_use"] == "UNRESOLVED"
    assert census["CENSUS_REFRESH"] is False


def test_build_is_deterministic_and_projection_is_exact() -> None:
    first = owner.build_artifacts_v1(REPO_ROOT)
    second = owner.build_artifacts_v1(REPO_ROOT)
    assert tuple(first) == owner.OUTPUT_FILENAMES
    assert first == second
    owner.validate_completed_decision_projection_v1(first, repo_root=REPO_ROOT)

    snapshot = _json_artifact(first, owner.SNAPSHOT)
    rows = _matrix(first)
    assert snapshot["completed"] is True
    assert snapshot["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    assert snapshot["task_relevance"] == "NOT_RELEVANT"
    assert snapshot["chemistry"] == "POSITIVE"
    assert snapshot["CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE"] is True
    assert snapshot["reactive_pair_sample_authority"] is True
    assert snapshot["role_partition_sample_authority"] is False
    assert snapshot["task_applicability_sample_authority"] is False
    assert snapshot["training_use"] == "NOT_APPLICABLE"
    assert snapshot["human_training_excluded"] is False
    assert snapshot["READY_FOR_TRAINING"] is False
    assert len(rows) == 4
    assert tuple(row["canonical_event_id"] for row in rows) == owner.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in rows) == owner.EXPECTED_RANKS


def test_matrix_preserves_positive_chemistry_pair_authority_and_unresolved_roles() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    rows = _matrix(artifacts)
    for row in rows:
        assert row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
        assert row["task_relevance"] == "NOT_RELEVANT"
        assert row["chemistry"] == "POSITIVE"
        assert row["positive_generative_supervision_eligible"] == "false"
        assert row["reactive_pair_human_decision_available"] == "true"
        assert row["reactive_pair_human_authoritative"] == "true"
        assert (row["protein_reactive_atom"], row["ligand_reactive_atom"]) == (
            "SG",
            "CB",
        )
        assert row["pair_authority_scope"] == "CURRENT_GVE_EXACT4_ONLY"
        assert row["role_partition_human_decision_available"] == "false"
        assert row["role_partition_human_authoritative"] == "false"
        assert row["selected_candidate_index_0based"] == "null"
        assert row["role_profile"] == "NOT_ESTABLISHED"
        for field in (
            "warhead_atoms_json",
            "linker_atoms_json",
            "scaffold_atoms_json",
            "W_L_S_counts_json",
            "boundary_bonds_json",
            "direct_profile_applicable_task_ids_json",
        ):
            assert row[field] == "null"
        applicability = json.loads(row["canonical_task_applicability_json"])
        assert [item["semantic_long_name"] for item in applicability] == [
            "warhead_only",
            "linker_plus_warhead",
            "scaffold_plus_warhead",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ]
        assert all(item["structurally_applicable"] is None for item in applicability)
        assert all(
            item["training_mask_target_available_now"] is False
            for item in applicability
        )
        assert row["task_applicability_determined"] == "false"
        assert row["training_mask_targets_available_now"] == "false"


def test_training_pre_post_and_reusable_authority_boundaries_are_closed() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    snapshot = _json_artifact(artifacts, owner.SNAPSHOT)
    training = snapshot["training_boundary"]
    assert training["formal_event_training_use_decision"] == "NOT_APPLICABLE"
    assert training["event_training_use_human_decision_available"] is True
    for key in (
        "training_use_allowed",
        "human_training_excluded",
        "future_training_admission_candidate",
        "formal_training_admitted",
        "training_materialization_allowed",
        "tensor_target_created",
        "model_supervision_usable",
        "current_runtime_model_usable",
        "parameter_update_authorization",
        "READY_FOR_TRAINING",
    ):
        assert training[key] is False
    assert snapshot["PRE_boundary"]["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert snapshot["PRE_boundary"]["PRE_mapping_count_per_event"] == 0
    assert snapshot["POST_boundary"]["POST_source_evidence_count"] == 4
    assert snapshot["POST_boundary"]["POST_geometry_training_authority"] is False
    assert not any(snapshot["reusable_authority_boundary"].values())


def test_generic_exact11_accepts_positive_chemistry_task_negative_combination() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    snapshot = _json_artifact(artifacts, owner.SNAPSHOT)
    generic = snapshot["generic_Exact11_projection_preview"]
    assert generic["synthetic_fact_count_validated"] == 4
    assert generic["generic_exact11_accepts_GVE_combination"] is True
    assert generic["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
    assert generic["task_relevance_disposition"] == "NOT_RELEVANT"
    assert generic["chemistry_disposition"] == "POSITIVE"
    assert generic["training_disposition"] == "NOT_APPLICABLE"
    assert generic["human_training_excluded"] is False
    assert generic["reconciliation_performed"] is False
    assert generic["generic_fact_materialized"] is False


def test_summary_counts_are_source_derived_and_exact() -> None:
    summary = _json_artifact(owner.build_artifacts_v1(REPO_ROOT), owner.SUMMARY)
    expected = {
        "formal_completed_event_count": 4,
        "task_NOT_RELEVANT_event_count": 4,
        "chemistry_POSITIVE_event_count": 4,
        "chemistry_negative_event_count": 0,
        "pair_sample_authority_event_count": 4,
        "role_sample_authority_event_count": 0,
        "task_applicability_authority_event_count": 0,
        "sample_mask_label_authority_event_count": 0,
        "training_NOT_APPLICABLE_event_count": 4,
        "training_INCLUDE_event_count": 0,
        "training_EXCLUDE_event_count": 0,
        "human_training_excluded_event_count": 0,
        "future_training_candidate_event_count": 0,
        "formal_training_admitted_event_count": 0,
        "tensor_target_event_count": 0,
        "runtime_usable_event_count": 0,
        "POST_source_evidence_event_count": 4,
        "POST_training_authority_event_count": 0,
        "POST_training_target_event_count": 0,
        "PRE_source_graph_present_event_count": 4,
        "PRE_compatible_mapping_event_count": 0,
        "PRE_resolved_event_count": 0,
        "PRE_training_authority_event_count": 0,
    }
    assert {key: summary[key] for key in expected} == expected
    assert summary["global_canonical_task_count"] == 5
    assert summary["B3_present"] is True
    assert summary["sixth_task"] is False
    assert summary["READY_FOR_TRAINING"] is False


def test_manifest_has_only_actual_sources_no_self_sha_and_no_dynamic_metadata() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    manifest = _json_artifact(artifacts, owner.MANIFEST)
    assert manifest["active_source_binding_count"] == 9
    assert len(manifest["active_source_bindings"]) == 9
    assert manifest["formal_validator_provenance_identity_only"] is True
    assert manifest["formal_validator_imported"] is False
    assert manifest["formal_validator_parsed"] is False
    assert manifest["formal_validator_executed"] is False
    assert manifest["formal_semantics_independently_validated"] is True
    assert manifest["metadata_only"] is True
    assert manifest["new_human_authority_created_by_ingestion"] is False
    for key in (
        "dataset_mutated",
        "training_dataset_changed",
        "tensorization",
        "model_forward",
        "loss",
        "backward",
        "optimizer",
        "parameter_update",
        "training",
    ):
        assert manifest[key] is False
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert owner.MANIFEST not in manifest["output_artifact_bindings"]
    rendered = json.dumps(manifest).lower()
    for token in ('"timestamp"', '"hostname"', '"pid"', '"uuid"'):
        assert token not in rendered


FORMAL_MUTATIONS = (
    ("D1_task_relevance", "RELEVANT"),
    ("D2_chemistry", "NOT_ESTABLISHED"),
    ("D2_chemistry", "NEGATIVE"),
    ("D3_reactive_pair", "UNRESOLVED"),
    ("D4_role_candidate", "SELECT_CANDIDATE_0"),
    ("D4_role_candidate", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
    ("D5_training_use", "INCLUDE"),
    ("D5_training_use", "EXCLUDE_FROM_TRAINING_ONLY"),
    ("D6_scientific_context", "mutated"),
)


@pytest.mark.parametrize(("field", "replacement"), FORMAL_MUTATIONS)
def test_formal_D1_through_D6_mutations_fail_closed(
    field: str, replacement: object
) -> None:
    formal = copy.deepcopy(owner.load_frozen_formal_decision_v1(REPO_ROOT)["formal"])
    formal["inherited_human_decision"][field] = replacement
    with pytest.raises(owner.GVEIngestionSafetyError):
        owner._validate_formal_document(formal)


PROJECTION_MUTATIONS = (
    (("completed_lane",), "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"),
    (("chemistry",), "NOT_ESTABLISHED"),
    (("reactive_pair_authority", "reactive_pair_human_authoritative"), False),
    (("role_partition_boundary", "role_partition_human_authoritative"), True),
    (("role_partition_boundary", "selected_candidate_index_0based"), 0),
    (("role_partition_boundary", "role_profile"), "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
    (("role_partition_boundary", "W_L_S_counts"), [3, 0, 5]),
    (("canonical_task_contract", "sample_authoritative_applicable_task_ids"), [0, 3, 4]),
    (("canonical_task_contract", "B3_present"), False),
    (("training_boundary", "human_training_excluded"), True),
    (("training_boundary", "future_training_admission_candidate"), True),
    (("training_boundary", "formal_training_admitted"), True),
    (("PRE_boundary", "PRE_status"), "PRE_REACTION_RESOLVED"),
    (("POST_boundary", "POST_geometry_training_authority"), True),
    (("legacy_1XD3_boundary", "legacy_events_in_current_Exact4"), True),
    (("current_census_boundary", "CENSUS_REFRESH"), True),
    (("census_crossfield_debt", "INGESTION_DOES_NOT_FIX_CENSUS_CROSSFIELD_RULE"), False),
    (("READY_FOR_TRAINING",), True),
)


@pytest.mark.parametrize(("path", "replacement"), PROJECTION_MUTATIONS)
def test_critical_projection_mutations_fail_closed(
    path: tuple[str, ...], replacement: object
) -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    changed = _mutate_snapshot(
        artifacts, lambda snapshot: _set_path(snapshot, path, replacement)
    )
    with pytest.raises(owner.GVEIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_sixth_task_and_machine_candidate_applicability_fail_closed() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)

    def add_sixth(snapshot: dict[str, object]) -> None:
        contract = snapshot["canonical_task_contract"]
        contract["global_canonical_tasks"].append(
            {
                "task_id": 5,
                "semantic_long_name": "forbidden_sixth",
                "display_alias": "D",
                "generated_roles": [],
                "fixed_or_seed_roles": [],
            }
        )
        contract["global_canonical_task_count"] = 6
        contract["sixth_task"] = True

    with pytest.raises(owner.GVEIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(
            _mutate_snapshot(artifacts, add_sixth)
        )

    rows = _matrix(artifacts)
    rows[0]["direct_profile_applicable_task_ids_json"] = "[0,3,4]"
    changed = dict(artifacts)
    changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, rows)
    with pytest.raises(owner.GVEIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(changed)


def test_pair_role_training_and_census_matrix_mutations_fail_closed() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    for field, replacement in (
        ("reactive_pair_human_authoritative", "false"),
        ("role_partition_human_authoritative", "true"),
        ("selected_candidate_index_0based", "0"),
        ("W_L_S_counts_json", "[3,0,5]"),
        ("formal_event_training_use_decision", "INCLUDE"),
        ("human_training_excluded", "true"),
        ("future_training_admission_candidate", "true"),
        ("formal_training_admitted", "true"),
        ("PRE_status", "PRE_REACTION_RESOLVED"),
        ("POST_geometry_training_authority", "true"),
        ("READY_FOR_TRAINING", "true"),
    ):
        rows = _matrix(artifacts)
        rows[0][field] = replacement
        changed = dict(artifacts)
        changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, rows)
        with pytest.raises(owner.GVEIngestionSafetyError):
            owner.validate_completed_decision_projection_v1(changed)


def test_mutated_formal_binding_and_unauthorized_source_override_fail_closed(
    tmp_path: Path,
) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    mutated = tmp_path / "gve_formal_human_decision_v1.json"
    payload = bytearray(source.read_bytes())
    payload[-2] = ord(" ") if payload[-2] != ord(" ") else ord("\t")
    mutated.write_bytes(payload)
    with pytest.raises(owner.GVEIngestionSafetyError):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT, formal_decision_path=mutated
        )
    with pytest.raises(owner.GVEIngestionSafetyError):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT,
            repository_path_overrides={Path("not/authorized"): mutated},
        )


def test_materialization_is_restricted_to_authorized_output_root(tmp_path: Path) -> None:
    with pytest.raises(owner.GVEIngestionSafetyError):
        owner.materialize_artifacts_v1(REPO_ROOT, target_root=tmp_path)


def test_materialized_exact4_matches_rebuild() -> None:
    result = owner.check_materialized_v1(REPO_ROOT)
    assert result == {
        "status": "PASS",
        "output_artifact_count": 4,
        "byte_identical_to_rebuild": True,
        "READY_FOR_TRAINING": False,
        "READY_FOR_EXTERNAL_REVIEW": True,
    }
