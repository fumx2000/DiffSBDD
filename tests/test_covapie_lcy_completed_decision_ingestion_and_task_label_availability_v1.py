from __future__ import annotations

import ast
import copy
import csv
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1
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
        "LCYIngestionSafetyError",
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
    assert formal_binding["byte_count"] == 32277
    assert formal_binding["SHA256"] == (
        "d7c7b427b87b13fa61188bd6b14a3e9dd3a37e4a170176222685065d419a3387"
    )
    assert validator_binding["byte_count"] == 84087
    assert validator_binding["SHA256"] == (
        "b8e33358c80ebb1356a9af8ab2cd9db86033adfdb31fc05f32061b57eab68c85"
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
    decision = formal["inherited_human_scientific_decision"]
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
    assert len(decision["D6_scientific_context"].encode("utf-8")) == 1754
    assert decision["D6_utf8_sha256"] == owner.EXPECTED_D6_SHA256
    assert formal["formal_authority_boundary"]["formal_authority_true_set"] == [
        "formal_authority_created",
        "formal_authority_is_human",
        "human_training_use_disposition_authority",
        "sample_positive_chemistry_authority",
        "sample_reactive_pair_authority",
        "sample_task_relevance_authority",
    ]


def test_owner_source_cannot_import_parse_or_execute_formal_validator() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = "validate_lcy_formal_human_decision_v1"
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
        "same_component_3A2G_included": False,
    }
    assert graph["review_policy_candidate_count"] == 0
    assert graph["review_policy_selectable_candidate_indices"] == []
    assert graph["formal_valid_singleton_diagnostic_count"] == 3
    assert graph["formal_valid_singleton_diagnostics_are_selectable"] is False
    assert graph["machine_candidate_selected"] is False
    assert graph["role_authority_created"] is False
    assert census["source_SHA256"] == (
        "540b072d45924688a640e5ca16484500b3815bc66267d73ceead81246b226557"
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
    assert len(rows[0]) == 115
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
            "C1",
        )
        assert row["pair_authority_scope"] == "CURRENT_LCY_4R0O_EXACT4_ONLY"
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


def test_lcy_role_diagnostics_are_explicit_nonselectable_snapshot_metadata_only() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    snapshot = _json_artifact(artifacts, owner.SNAPSHOT)
    role = snapshot["role_partition_boundary"]
    assert role["review_policy_candidate_count"] == 0
    assert role["review_policy_selectable_candidate_indices"] == []
    assert role["formal_valid_singleton_diagnostic_count"] == 3
    assert role["formal_valid_singleton_diagnostic_indices"] == [0, 1, 2]
    assert role["formal_valid_singleton_diagnostics_are_selectable"] is False
    assert "candidate_evidence_count" not in role
    assert "candidate_indices_are_machine_evidence_only" not in role
    assert [item["cut_bond"] for item in role["formal_valid_singleton_diagnostics"]] == [
        {"atom_id_1": "C3", "atom_id_2": "O2"},
        {"atom_id_1": "C4", "atom_id_2": "O1"},
        {"atom_id_1": "C5", "atom_id_2": "N1"},
    ]
    assert [item["S_atom_ids"] for item in role["formal_valid_singleton_diagnostics"]] == [
        ["O2"], ["O1"], ["C5"]
    ]
    assert all(item["S_count"] == 1 for item in role["formal_valid_singleton_diagnostics"])
    assert all(item["published_runtime_valid"] is True for item in role["formal_valid_singleton_diagnostics"])
    assert all(item["review_policy_eligible"] is False for item in role["formal_valid_singleton_diagnostics"])
    assert all(item["selected"] is False for item in role["formal_valid_singleton_diagnostics"])
    assert len(owner.MATRIX_HEADER) == 115
    assert "formal_valid_singleton_diagnostic_count" not in owner.MATRIX_HEADER


def test_same_component_3a2g_is_context_only_with_no_transfer() -> None:
    snapshot = _json_artifact(owner.build_artifacts_v1(REPO_ROOT), owner.SNAPSHOT)
    boundary = snapshot["same_component_3A2G_boundary"]
    assert boundary["canonical_event_id"] == (
        "COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1"
    )
    assert all(value is False for key, value in boundary.items() if key != "canonical_event_id")
    assert all("3A2G" not in event["canonical_event_id"] for event in snapshot["events"])


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
    assert generic["generic_exact11_accepts_LCY_combination"] is True
    assert generic["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
    assert generic["task_relevance_disposition"] == "NOT_RELEVANT"
    assert generic["chemistry_disposition"] == "POSITIVE"
    assert generic["training_disposition"] == "NOT_APPLICABLE"
    assert generic["human_training_excluded"] is False
    assert generic["reconciliation_performed"] is False
    assert generic["generic_fact_materialized"] is False
    assert generic["source_binding_path_namespace"] == "repository_parent_relative"
    assert generic["GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE"] is True


def test_crossfield_compatibility_and_future_arithmetic_create_no_current_operation() -> None:
    snapshot = _json_artifact(owner.build_artifacts_v1(REPO_ROOT), owner.SNAPSHOT)
    compatibility = snapshot["census_crossfield_compatibility"]
    assert compatibility == {
        "CURRENT_WITH_GVE_CENSUS_SUPPORTS_ORTHOGONAL_COMBINATION": True,
        "LEGACY_BASE_CENSUS_ASSUMPTION_HISTORICAL_ONLY": True,
        "NEW_CROSSFIELD_DEBT_CREATED": False,
        "NEW_CENSUS_CROSSFIELD_AUDIT_REQUIRED": False,
        "47_COLUMN_SCHEMA_CHANGE_REQUIRED": False,
        "GENERIC_SCHEMA_CHANGE_REQUIRED": False,
        "HUMAN_D2_POSITIVE_PRESERVED": True,
        "INGESTION_DOES_NOT_MODIFY_CENSUS": True,
    }
    arithmetic = snapshot["future_reconciliation_arithmetic"]
    assert arithmetic["future_arithmetic_only"] is True
    assert arithmetic["reconciliation_performed"] is False
    assert arithmetic["reconciliation_output_files"] == 0
    assert (arithmetic["current"]["source_count"], arithmetic["current"]["fact_count"]) == (20, 123)
    future = arithmetic["expected_future_with_LCY"]
    assert (future["source_count"], future["fact_count"]) == (21, 127)
    assert (future["completed_total_events"], future["completed_total_units"]) == (151, 25)
    assert (future["unreviewed_events"], future["unreviewed_units"]) == (187, 106)
    assert snapshot["operation_boundary"]["RECONCILIATION"] is False


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
    assert summary["review_policy_candidate_count"] == 0
    assert summary["formal_valid_singleton_diagnostic_count"] == 3
    assert summary["selectable_role_candidate_count"] == 0
    assert summary["READY_FOR_TRAINING"] is False


def test_manifest_has_only_actual_sources_no_self_sha_and_no_dynamic_metadata() -> None:
    artifacts = owner.build_artifacts_v1(REPO_ROOT)
    manifest = _json_artifact(artifacts, owner.MANIFEST)
    assert manifest["active_source_binding_count"] == 9
    assert len(manifest["active_source_bindings"]) == 9
    assert manifest["duplicate_source_binding_identity_count"] == 0
    identities = {
        (record["namespace"], record["path"], record["SHA256"])
        for record in manifest["active_source_bindings"]
    }
    assert len(identities) == 9
    assert all(
        record["expected_executable_class"] == "NON_EXECUTABLE"
        for record in manifest["active_source_bindings"]
    )
    assert manifest["formal_validator_provenance_identity_only"] is True
    assert manifest["formal_validator_imported"] is False
    assert manifest["formal_validator_parsed"] is False
    assert manifest["formal_validator_executed"] is False
    assert manifest["formal_semantics_independently_validated"] is True
    assert manifest["metadata_only"] is True
    assert manifest["new_human_authority_created_by_ingestion"] is False
    assert all(
        value is False
        for value in manifest["GVE_implementation_precedent_only"].values()
    )
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
    formal["inherited_human_scientific_decision"][field] = replacement
    with pytest.raises(owner.LCYIngestionSafetyError):
        owner._validate_formal_document(formal)


FORMAL_PATH_MUTATIONS = (
    (("target_Exact4", "ligand_wide_selection"), True),
    (("target_Exact4", "3A2G_event_included"), True),
    (("target_Exact4", "event_count"), 5),
    (("formal_decision_semantic_canonical_sha256",), "0" * 64),
    (("event_level_formal_decisions", "0", "ligand_reactive_atom"), "C2"),
    (("event_level_formal_decisions", "0", "sample_reactive_pair_authority"), False),
    (("D4_role_boundary", "D4_human_choice"), "DIRECT"),
    (("D4_role_boundary", "review_policy_candidate_count"), 3),
    (("D4_role_boundary", "formal_valid_singleton_diagnostics_are_selectable"), True),
    (("D4_role_boundary", "role_partition_sample_authority"), True),
    (("D4_role_boundary", "task_applicability_sample_authority"), True),
    (("D4_role_boundary", "canonical_mask_structural_labels_sample_authority"), True),
    (("canonical_Exact5", "B3_present"), False),
    (("canonical_Exact5", "sixth_task"), True),
    (("training_boundary", "human_training_excluded"), True),
    (("training_boundary", "future_training_admission_candidate"), True),
    (("PRE_boundary", "PRE_status"), "PRE_REACTION_RESOLVED"),
    (("PRE_boundary", "PRE_authority"), True),
    (("POST_boundary", "POST_geometry_training_authority"), True),
    (("formal_authority_boundary", "reaction_family_authority"), True),
    (("census_crossfield_compatibility", "NEW_CROSSFIELD_DEBT_CREATED"), True),
)


@pytest.mark.parametrize(("path", "replacement"), FORMAL_PATH_MUTATIONS)
def test_lcy_specific_formal_mutations_fail_closed(
    path: tuple[str, ...], replacement: object
) -> None:
    formal = copy.deepcopy(owner.load_frozen_formal_decision_v1(REPO_ROOT)["formal"])
    target: object = formal
    for key in path[:-1]:
        target = target[int(key)] if isinstance(target, list) else target[key]
    if isinstance(target, list):
        target[int(path[-1])] = replacement
    else:
        target[path[-1]] = replacement
    with pytest.raises(owner.LCYIngestionSafetyError):
        owner._validate_formal_document(formal)


def test_fifth_target_and_3a2g_target_insertion_fail_closed() -> None:
    for inserted_id in (
        "COVAPIE_CYS_SG_EVENT_V1:4R0O:E:CYS:45-:SG:N:LCY:C1",
        "COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1",
    ):
        formal = copy.deepcopy(owner.load_frozen_formal_decision_v1(REPO_ROOT)["formal"])
        formal["target_Exact4"]["canonical_event_ids"].append(inserted_id)
        formal["target_Exact4"]["event_count"] = 5
        with pytest.raises(owner.LCYIngestionSafetyError):
            owner._validate_formal_document(formal)


PROJECTION_MUTATIONS = (
    (("completed_lane",), "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"),
    (("chemistry",), "NOT_ESTABLISHED"),
    (("reactive_pair_authority", "reactive_pair_human_authoritative"), False),
    (("role_partition_boundary", "role_partition_human_authoritative"), True),
    (("role_partition_boundary", "selected_candidate_index_0based"), 0),
    (("role_partition_boundary", "role_profile"), "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
    (("role_partition_boundary", "W_L_S_counts"), [3, 0, 5]),
    (("role_partition_boundary", "review_policy_candidate_count"), 3),
    (("role_partition_boundary", "formal_valid_singleton_diagnostics_are_selectable"), True),
    (("canonical_task_contract", "sample_authoritative_applicable_task_ids"), [0, 3, 4]),
    (("canonical_task_contract", "task_applicability_determined"), True),
    (("canonical_task_contract", "authoritative_task_labels_created"), True),
    (("canonical_task_contract", "B3_present"), False),
    (("training_boundary", "human_training_excluded"), True),
    (("training_boundary", "future_training_admission_candidate"), True),
    (("training_boundary", "formal_training_admitted"), True),
    (("PRE_boundary", "PRE_status"), "PRE_REACTION_RESOLVED"),
    (("PRE_boundary", "PRE_geometry_authority"), True),
    (("POST_boundary", "POST_geometry_training_authority"), True),
    (("reusable_authority_boundary", "reaction_family_authority"), True),
    (("reusable_authority_boundary", "warhead_rule_authority"), True),
    (("reusable_authority_boundary", "warhead_type_authority"), True),
    (("generic_Exact11_projection_preview", "source_binding_path_namespace"), "project_parent_relative"),
    (("generic_Exact11_projection_preview", "chemistry_disposition"), "NOT_ESTABLISHED"),
    (("generic_Exact11_projection_preview", "legacy_completed_review_status"), "COMPLETED_HUMAN_POSITIVE"),
    (("same_component_3A2G_boundary", "decision_transfer"), True),
    (("current_census_boundary", "CENSUS_REFRESH"), True),
    (("census_crossfield_compatibility", "NEW_CROSSFIELD_DEBT_CREATED"), True),
    (("census_crossfield_compatibility", "INGESTION_DOES_NOT_MODIFY_CENSUS"), False),
    (("operation_boundary", "RECONCILIATION"), True),
    (("operation_boundary", "training"), True),
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
    with pytest.raises(owner.LCYIngestionSafetyError):
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

    with pytest.raises(owner.LCYIngestionSafetyError):
        owner.validate_completed_decision_projection_v1(
            _mutate_snapshot(artifacts, add_sixth)
        )

    rows = _matrix(artifacts)
    rows[0]["direct_profile_applicable_task_ids_json"] = "[0,3,4]"
    changed = dict(artifacts)
    changed[owner.MATRIX] = owner._csv_bytes(owner.MATRIX_HEADER, rows)
    with pytest.raises(owner.LCYIngestionSafetyError):
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
        with pytest.raises(owner.LCYIngestionSafetyError):
            owner.validate_completed_decision_projection_v1(changed)


def test_mutated_formal_binding_and_unauthorized_source_override_fail_closed(
    tmp_path: Path,
) -> None:
    source = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    mutated = tmp_path / "lcy_formal_human_decision_v1.json"
    payload = bytearray(source.read_bytes())
    payload[-2] = ord(" ") if payload[-2] != ord(" ") else ord("\t")
    mutated.write_bytes(payload)
    with pytest.raises(owner.LCYIngestionSafetyError):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT, formal_decision_path=mutated
        )
    with pytest.raises(owner.LCYIngestionSafetyError):
        owner.load_frozen_formal_decision_v1(
            REPO_ROOT,
            repository_path_overrides={Path("not/authorized"): mutated},
        )


def test_materialization_is_restricted_to_authorized_output_root(tmp_path: Path) -> None:
    with pytest.raises(owner.LCYIngestionSafetyError):
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
