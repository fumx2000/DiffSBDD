from __future__ import annotations

from collections import Counter
from dataclasses import replace
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_4m5_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_gd1_v1 as subject  # noqa: E402


CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1",
    REPO / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)
ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithGD1Error


@pytest.fixture(scope="module")
def frozen_bundle():
    """One cached source-derived pipeline; only determinism performs build #2."""

    root = REPO.resolve()
    additive = subject._verify_additive_sources(root)
    predecessor_computation = (
        predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1(root)
    )
    subject._assert_predecessor_gd1_state_v1(predecessor_computation)
    subject._verify_predecessor_semantic_bindings_v1(
        root, predecessor_computation.semantic_source_bindings
    )
    reconciliation = subject._validate_gd1_reconciliation_v1(root)
    matrix_rows = subject._load_and_validate_gd1_event_matrix_v1(root)
    rows = subject._overlay_gd1_exact4_v1(
        predecessor_computation.rows, matrix_rows
    )
    top = subject._top_pending_review_units_v1(root, reconciliation)
    summary = subject._build_summary_v1(rows, top)
    bindings = subject._merge_semantic_bindings_v1(
        predecessor_computation.semantic_source_bindings, additive
    )
    computation = subject.base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows, summary=summary, semantic_source_bindings=bindings
    )
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(
        computation,
        predecessor_computation=predecessor_computation,
        reconciliation_result=reconciliation,
        matrix_rows=matrix_rows,
    )
    artifacts = subject._build_artifacts_from_computation_v1(root, computation)
    return {
        "predecessor": predecessor_computation,
        "reconciliation": reconciliation,
        "matrix_rows": matrix_rows,
        "computation": computation,
        "artifacts": artifacts,
        "top": top,
    }


def _replace_rows(computation, rows):
    return replace(computation, rows=tuple(rows))


def test_public_api_schema_and_exact7_contract() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithGD1Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_gd1_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_gd1_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 == predecessor.CENSUS_COLUMNS_V1
    assert len(subject.CENSUS_COLUMNS_V1) == 47
    assert not {
        "PRE_source_graph_present", "PRE_source_graph_count",
        "PRE_mapping_status", "PRE_mapping_count",
    } & set(subject.CENSUS_COLUMNS_V1)
    assert len(subject.EXACT7_PATHS_V1) == len(set(subject.EXACT7_PATHS_V1)) == 7


def test_frozen_bindings_are_exact_and_with_4m5_is_direct_predecessor() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 7
    assert verified[0]["path"] == predecessor.PRODUCTION_RELATIVE.as_posix()
    assert [item["sha256"] for item in verified] == [item[4] for item in checker.FROZEN_BINDINGS]


def test_cached_pipeline_is_exact1000_and_source_derived(frozen_bundle) -> None:
    computation = frozen_bundle["computation"]
    assert len(computation.rows) == 1000
    assert len(computation.semantic_source_bindings) == 138
    assert tuple(computation.semantic_source_bindings[:132]) == frozen_bundle["predecessor"].semantic_source_bindings
    assert len(frozen_bundle["matrix_rows"]) == 4
    assert len(frozen_bundle["reconciliation"].normalized_facts) == 115


def test_exact4_identity_and_rich_ingestion_boundary(frozen_bundle) -> None:
    rows = frozen_bundle["matrix_rows"]
    assert tuple(row["canonical_event_id"] for row in rows) == ingestion.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (691, 692, 693, 694)
    assert Counter(row["pdb_id"] for row in rows) == Counter({"4F8B": 4})
    assert {row["cys_residue_id"] for row in rows} == {"CYS:55-"}
    for row in rows:
        assert row["human_review_completed"] == "true"
        assert row["human_task_relevance_decision"] == "RELEVANT"
        assert row["human_chemistry_decision"] == "POSITIVE"
        assert (row["protein_reactive_atom"], row["ligand_reactive_atom"]) == ("SG", "C77")
        assert row["selected_candidate_index_0based"] == "0"
        assert row["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        assert row["W_L_S_counts_json"] == "[2,0,11]"
        assert json.loads(row["boundary_bonds_json"]) == list(ingestion.BOUNDARY_BONDS)
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["authoritative_task_labels_created"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
        assert row["formal_training_admitted"] == "false"


def test_formal_pre_graph_absent_and_global_usable_pre_stays_zero(frozen_bundle) -> None:
    for row in frozen_bundle["matrix_rows"]:
        assert row["supporting_PRE_source_graph_count_per_event"] == "0"
        assert row["PRE_source_graph_present"] == "false"
        assert row["PRE_source_graph_count_per_event"] == "0"
        assert row["PRE_mapping_count_per_event"] == "0"
        assert row["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
        assert row["PRE_status"] == "PRE_REACTION_UNRESOLVED"
        for field in (
            "PRE_topology_authority", "PRE_geometry_authority",
            "PRE_coordinates_authority", "PRE_reconstruction",
            "POST_to_PRE_copy", "PRE_zero_fill",
        ):
            assert row[field] == "false"
    geometry = frozen_bundle["computation"].summary["geometry"]
    assert geometry["PRE_source_evidence_available_count"] == 0
    assert geometry["PRE_sample_authoritative_count"] == 0
    assert geometry["PRE_training_target_available_count"] == 0
    assert geometry["PRE_is_v1_hard_requirement"] is False
    assert geometry["POST_to_PRE_promotion_performed"] is False
    assert geometry["PRE_zero_fill_performed"] is False


def test_reconciliation_exact18_115_and_status_counts(frozen_bundle) -> None:
    result = frozen_bundle["reconciliation"]
    assert len({fact.source_binding_path for fact in result.normalized_facts}) == 18
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 111,
        "completed_positive_unit_count": 17,
        "completed_negative_event_count": 28,
        "completed_negative_unit_count": 5,
        "completed_total_event_count": 139,
        "completed_total_unit_count": 22,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 199,
        "unreviewed_unit_count": 109,
    }
    exact4 = set(subject.GD1_EXACT4_EVENT_IDS_V1)
    assert {
        row["current_review_status"]
        for row in result.reconciled_rows
        if row["canonical_event_id"] in exact4
    } == {"COMPLETED_HUMAN_POSITIVE"}


def test_authorized_exact19_actual_exact17_and_non_target_996_dict_equal(frozen_bundle) -> None:
    before = {row["canonical_event_id"]: row for row in frozen_bundle["predecessor"].rows}
    after = {row["canonical_event_id"]: row for row in frozen_bundle["computation"].rows}
    exact4 = set(subject.GD1_EXACT4_EVENT_IDS_V1)
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == exact4
    assert sum(before[event_id] == after[event_id] for event_id in set(before) - exact4) == 996
    for event_id in exact4:
        actual = {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        assert len(subject._AUTHORIZED_GD1_OVERLAY_FIELDS_V1) == 19
        assert actual == subject._AUTHORIZED_GD1_OVERLAY_FIELDS_V1 - {
            "training_use_include", "future_training_admission_candidate"
        }
        assert len(actual) == 17
        assert after[event_id]["human_review_authority_source"] == subject.GD1_HUMAN_DECISION_SOURCE
        assert after[event_id]["positive_authority_source"] == subject.GD1_EVENT_MATRIX_SOURCE
        assert after[event_id]["training_materialization_allowed_current_source"] == "false"
        assert after[event_id]["human_training_excluded"] == "true"
        assert after[event_id]["training_use_include"] == "false"
        assert after[event_id]["future_training_admission_candidate"] == "false"


def test_overlay_selector_is_exact_event_ids_not_ligand_wide() -> None:
    source = (REPO / subject.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    overlay = source[source.index("def _overlay_gd1_exact4_v1"):source.index("def _top_pending_review_units_v1")]
    assert 'event_id not in matrix_by_event' in overlay
    assert 'row["ligand_component_id"] == "GD1"' not in overlay


def test_global_distributions_authority_and_role_counts(frozen_bundle) -> None:
    rows = frozen_bundle["computation"].rows
    assert Counter(row["current_global_status"] for row in rows) == Counter(subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1)
    assert Counter(row["current_global_status"] for row in rows)["COMPLETED_HUMAN_POSITIVE"] == 111
    assert Counter(row["current_global_status"] for row in rows)["CURRENTLY_UNREVIEWED"] == 199
    assert Counter(row["chemistry_disposition"] for row in rows) == Counter({"POSITIVE": 128, "NOT_ESTABLISHED": 90, "UNRESOLVED": 782})
    assert Counter(row["task_relevance_disposition"] for row in rows) == Counter({"RELEVANT": 129, "NOT_RELEVANT": 90, "UNRESOLVED": 781})
    assert Counter(row["training_use_disposition"] for row in rows) == Counter({"INCLUDE": 56, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 90, "UNRESOLVED": 782})
    assert sum(row["reactive_pair_sample_authoritative"] == "true" for row in rows) == 128
    assert sum(row["role_partition_sample_authoritative"] == "true" for row in rows) == 128
    assert sum(row["future_training_admission_candidate"] == "true" for row in rows) == 39
    assert sum(row["formal_training_admitted"] == "true" for row in rows) == 5
    assert sum(row["current_runtime_model_usable"] == "true" for row in rows) == 17
    assert sum(row["human_training_excluded"] == "true" for row in rows) == 72
    assert Counter(row["role_profile"] for row in rows if row["role_partition_sample_authoritative"] == "true") == Counter({"DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 76, "STRICT_LINKER_PRESENT_V1": 52})


def test_structural_and_post_geometry_counts_are_unchanged(frozen_bundle) -> None:
    summary = frozen_bundle["computation"].summary
    assert summary["structural"] == frozen_bundle["predecessor"].summary["structural"]
    assert summary["geometry"] == frozen_bundle["predecessor"].summary["geometry"]
    assert summary["geometry"]["POST_source_evidence_available_count"] == 867
    assert summary["geometry"]["POST_sample_authoritative_count"] == 21
    assert summary["geometry"]["POST_training_target_available_count"] == 17


def test_canonical_exact5_counts_b3_and_no_sixth(frozen_bundle) -> None:
    exact5 = frozen_bundle["computation"].summary["canonical_exact5"]
    assert exact5["task_count"] == 5
    assert exact5["B3_present"] is True
    assert exact5["sixth_task_present"] is False
    assert {
        task["semantic_name"]: task["structurally_applicable_authoritative_role_count"]
        for task in exact5["tasks"]
    } == {
        "warhead_only": 128,
        "linker_plus_warhead": 52,
        "scaffold_plus_warhead": 52,
        "scaffold_only": 128,
        "scaffold_plus_linker_plus_warhead": 128,
    }


def test_blocker_counts_are_source_derived_and_nonexclusive(frozen_bundle) -> None:
    blockers = frozen_bundle["computation"].summary["blockers"]
    assert blockers["non_exclusive_counts_must_not_be_summed"] is True
    assert blockers["chemistry_unresolved"] == {"all_1000": 782}
    assert blockers["feature_semantics_pending"] == {"within_positive_128": 128}
    assert blockers["human_training_exclusion"] == {"within_positive_128": 72}
    assert blockers["missing_POST_training_authority"] == {"within_positive_128": 111, "within_include_56": 39}
    assert blockers["missing_split_authority"] == {"within_positive_128": 87, "within_include_56": 31}
    assert blockers["missing_training_admission"] == {"within_positive_128": 123, "within_include_56": 51}
    assert blockers["pair_authority_absent"] == {"all_1000": 872, "within_positive_128": 0}
    assert blockers["role_authority_absent"] == {"all_1000": 872, "within_positive_128": 0}
    assert blockers["missing_tensor_integration"]["within_positive_128"] == 87
    assert blockers["missing_tensor_integration"]["within_include_56"] == 27
    assert blockers["missing_tensor_integration"]["missing_source_composition"]["GD1"] == 4


def test_dynamic_next_pending_and_queue_boundary(frozen_bundle) -> None:
    top = frozen_bundle["top"]
    assert top[0]["rank"] == 1
    assert top[0] == {
        "rank": 1,
        "raw_priority_rank": 22,
        "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08",
        "event_count": 4,
        "pdb_ids": ["2QLQ", "2QQ7"],
        "ligand_component_ids": ["SR2"],
        "full_coordinate_count": 4,
        "exact_pair_count": 4,
        "ccd_complete_count": 4,
        "post_source_evidence_count": 4,
        "current_review_status": "CURRENTLY_UNREVIEWED",
    }
    assert all(item["review_unit_id"] != subject.GD1_REVIEW_UNIT_ID_V1 for item in top)
    sr2_events = [
        row["canonical_event_id"]
        for row in frozen_bundle["computation"].rows
        if row["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08"
    ]
    assert sr2_events == [
        "COVAPIE_CYS_SG_EVENT_V1:2QLQ:A:CYS:345-:SG:C:SR2:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2QLQ:B:CYS:345-:SG:E:SR2:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2QQ7:A:CYS:345-:SG:C:SR2:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2QQ7:B:CYS:345-:SG:D:SR2:C51",
    ]
    independently_derived = checker.independently_compute_top10_v1(
        REPO, frozen_bundle["reconciliation"].reconciled_rows
    )
    assert top == independently_derived
    boundary = frozen_bundle["computation"].summary["authority_boundary"]
    assert boundary["next_priority_review_unit"] == top[0]["review_unit_id"]
    assert boundary["next_priority_review_ligand"] == top[0]["ligand_component_ids"][0]
    assert boundary["QUEUE_REFRESH"] is False
    assert boundary["NEXT_REVIEW_STARTED"] is False
    assert boundary["priority_queue_file_modified"] is False
    assert boundary["priority_queue_file_created"] is False


def test_authority_boundary_and_training_prohibitions(frozen_bundle) -> None:
    boundary = frozen_bundle["computation"].summary["authority_boundary"]
    for key in (
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE",
        "CURRENT_GLOBAL_RECONCILIATION_COMPLETE",
        "GD1_REVIEW_COMPLETED", "CENSUS_REFRESH",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    ):
        assert boundary[key] is True
    for key in (
        "QUEUE_REFRESH", "NEXT_REVIEW_STARTED", "TRAINING_STARTED",
        "READY_FOR_TRAINING", "formal_decision_read_directly",
        "formal_validator_executed", "new_human_authority_created",
        "new_chemistry_authority_created", "new_pair_authority_created",
        "new_role_authority_created", "new_reusable_authority_created",
        "training_admission_created", "reaction_family_authority",
        "warhead_rule_authority", "warhead_type_authority",
    ):
        assert boundary[key] is False
    assert boundary["Step12D"] == "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT"


def test_manifest_lineage_and_no_self_or_dynamic_identity(frozen_bundle) -> None:
    manifest = json.loads(frozen_bundle["artifacts"][subject.MANIFEST_FILE])
    assert manifest["semantic_source_bindings"] == list(frozen_bundle["computation"].semantic_source_bindings)
    assert len(manifest["semantic_source_bindings"]) == 138
    assert manifest["predecessor_manifest_validation_binding"]["artifact_role"] == "PREDECESSOR_WITH_4M5_MANIFEST_VALIDATION_IDENTITY"
    assert manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is False
    assert "sha256" not in manifest["manifest_self_binding"]
    checker._reject_dynamic_manifest_metadata(manifest)
    assert all("mode" not in binding and "exact_posix_mode" not in binding for binding in manifest["semantic_source_bindings"])
    refresh = manifest["refresh_contract"]
    assert refresh["authorized_overlay_field_count"] == 19
    assert refresh["actual_changed_field_count_per_gd1_row"] == 17


def test_gd1_contribution_and_zero_future_candidate_composition(frozen_bundle) -> None:
    summary = frozen_bundle["computation"].summary
    assert summary["reactive_pair"]["gd1_sample_authority_contribution_count"] == 4
    assert summary["reactive_pair"]["gd1_training_target_contribution_count"] == 0
    assert summary["training_stage"]["future_candidate_source_composition"]["GD1"] == 0
    assert summary["refresh_delta"] == {
        "frozen_predecessor_positive_count": 124,
        "gd1_exact4_delta_count": 4,
        "refreshed_positive_count": 128,
        "frozen_predecessor_training_include_count": 56,
        "refreshed_training_include_count": 56,
        "frozen_predecessor_training_exclude_count": 68,
        "refreshed_training_exclude_count": 72,
        "frozen_predecessor_future_candidate_count": 39,
        "refreshed_future_candidate_count": 39,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "derived_refresh_not_new_authority": True,
    }


def test_deterministic_second_full_build_only(frozen_bundle) -> None:
    rebuilt = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_gd1_v1(REPO)
    assert rebuilt == frozen_bundle["artifacts"]
    assert set(rebuilt) == {subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE}


def test_materialization_rejects_unexpected_entry_before_build(tmp_path: Path) -> None:
    output = tmp_path / "contaminated"
    output.mkdir()
    sentinel = output / "sentinel.txt"
    sentinel.write_bytes(b"unchanged")
    with pytest.raises(ERROR, match="OUTPUT_DIRECTORY_UNEXPECTED_ENTRY"):
        subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_gd1_v1(REPO, output)
    assert sentinel.read_bytes() == b"unchanged"
    assert list(output.iterdir()) == [sentinel]


def test_non_gd1_mutation_fails_closed(frozen_bundle) -> None:
    computation = frozen_bundle["computation"]
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if row["canonical_event_id"] not in set(subject.GD1_EXACT4_EVENT_IDS_V1))
    rows[index]["current_runtime_model_usable"] = "true" if rows[index]["current_runtime_model_usable"] == "false" else "false"
    mutated = _replace_rows(computation, rows)
    with pytest.raises(ERROR, match="PREDECESSOR_DELTA_NOT_EXACT_GD1_EXACT4"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(
            mutated,
            predecessor_computation=frozen_bundle["predecessor"],
            reconciliation_result=frozen_bundle["reconciliation"],
            matrix_rows=frozen_bundle["matrix_rows"],
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("training_use_include", "true"),
        ("future_training_admission_candidate", "true"),
        ("human_training_excluded", "false"),
        ("current_global_status", "COMPLETED_HUMAN_NEGATIVE"),
        ("post_geometry_training_target_available", "true"),
        ("pre_geometry_authoritative", "true"),
    ),
)
def test_critical_gd1_row_mutations_fail_closed(frozen_bundle, field, value) -> None:
    rows = [dict(row) for row in frozen_bundle["computation"].rows]
    index = next(
        index for index, row in enumerate(rows)
        if row["canonical_event_id"] in set(subject.GD1_EXACT4_EVENT_IDS_V1)
    )
    rows[index][field] = value
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(
            _replace_rows(frozen_bundle["computation"], rows),
            predecessor_computation=frozen_bundle["predecessor"],
            reconciliation_result=frozen_bundle["reconciliation"],
            matrix_rows=frozen_bundle["matrix_rows"],
        )


def test_authorized_overlay_missing_human_training_excluded_fails_closed(
    frozen_bundle, monkeypatch
) -> None:
    monkeypatch.setattr(
        subject,
        "_AUTHORIZED_GD1_OVERLAY_FIELDS_V1",
        subject._AUTHORIZED_GD1_OVERLAY_FIELDS_V1 - {"human_training_excluded"},
    )
    with pytest.raises(ERROR, match="GD1_CHANGED_FIELD_SET_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(
            frozen_bundle["computation"],
            predecessor_computation=frozen_bundle["predecessor"],
            reconciliation_result=frozen_bundle["reconciliation"],
            matrix_rows=frozen_bundle["matrix_rows"],
        )


@pytest.mark.parametrize(
    "contract",
    (
        subject.CANONICAL_EXACT5_V1[:3] + subject.CANONICAL_EXACT5_V1[4:],
        subject.CANONICAL_EXACT5_V1 + ((5, "sixth_task", "D"),),
    ),
)
def test_b3_removal_or_sixth_task_fails_closed(frozen_bundle, monkeypatch, contract) -> None:
    monkeypatch.setattr(subject, "CANONICAL_EXACT5_V1", contract)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(
            frozen_bundle["computation"],
            predecessor_computation=frozen_bundle["predecessor"],
            reconciliation_result=frozen_bundle["reconciliation"],
            matrix_rows=frozen_bundle["matrix_rows"],
        )


def test_pre_mapping_authority_mutation_fails_closed(frozen_bundle) -> None:
    rows = [dict(row) for row in frozen_bundle["matrix_rows"]]
    rows[0]["PRE_geometry_authority"] = "true"
    with pytest.raises(ERROR, match="GD1_EVENT_MATRIX_SEMANTICS_INVALID"):
        subject._validate_gd1_matrix_rows_v1(rows)


def test_candidate_and_future_tracked_lifecycle_profiles() -> None:
    expected = set(subject.EXACT7_PATHS_V1)
    assert checker._classify_exact7_artifact_placement_v1([], tuple(expected)) == "CANDIDATE_UNTRACKED"
    assert checker._classify_exact7_artifact_placement_v1(tuple(expected), []) == "TRACKED_CLEAN"
    simulations = checker.check_lifecycle_simulations_v1()
    assert all(simulations.values())


def test_materialized_exact7_inventory_without_running_full_checker() -> None:
    inventory = checker.verify_exact7_inventory_v1(REPO)
    assert len(inventory) == 7
    assert all(item["byte_count"] < 1024 * 1024 for item in inventory)
