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

from covalent_ext import covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_cer_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_4m5_v1 as subject  # noqa: E402


CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1",
    REPO / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)
ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWith4M5Error


@pytest.fixture(scope="module")
def frozen_bundle():
    """One cached source-derived pipeline; only determinism performs build #2."""

    root = REPO.resolve()
    additive = subject._verify_additive_sources(root)
    predecessor_computation = (
        predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_cer_v1(root)
    )
    subject._assert_predecessor_four_m5_state_v1(predecessor_computation)
    subject._verify_predecessor_semantic_bindings_v1(
        root, predecessor_computation.semantic_source_bindings
    )
    reconciliation = subject._validate_four_m5_reconciliation_v1(root)
    matrix_rows = subject._load_and_validate_four_m5_event_matrix_v1(root)
    rows = subject._overlay_four_m5_exact4_v1(
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
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1(
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
        "Cumulative1000CurrentGlobalReadinessCensusWith4M5Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_4m5_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_4m5_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 == predecessor.CENSUS_COLUMNS_V1
    assert len(subject.CENSUS_COLUMNS_V1) == 47
    assert not {
        "PRE_source_graph_present", "PRE_source_graph_count",
        "PRE_mapping_status", "PRE_mapping_count",
    } & set(subject.CENSUS_COLUMNS_V1)
    assert len(subject.EXACT7_PATHS_V1) == len(set(subject.EXACT7_PATHS_V1)) == 7


def test_frozen_bindings_are_exact_and_with_cer_is_direct_predecessor() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 7
    assert verified[0]["path"] == predecessor.PRODUCTION_RELATIVE.as_posix()
    assert [item["sha256"] for item in verified] == [item[4] for item in checker.FROZEN_BINDINGS]


def test_cached_pipeline_is_exact1000_and_source_derived(frozen_bundle) -> None:
    computation = frozen_bundle["computation"]
    assert len(computation.rows) == 1000
    assert len(computation.semantic_source_bindings) == 132
    assert tuple(computation.semantic_source_bindings[:126]) == frozen_bundle["predecessor"].semantic_source_bindings
    assert len(frozen_bundle["matrix_rows"]) == 4
    assert len(frozen_bundle["reconciliation"].normalized_facts) == 111


def test_exact4_identity_and_rich_ingestion_boundary(frozen_bundle) -> None:
    rows = frozen_bundle["matrix_rows"]
    assert tuple(row["canonical_event_id"] for row in rows) == ingestion.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (973, 974, 975, 976)
    assert Counter(row["pdb_id"] for row in rows) == Counter({"5AZT": 2, "5AZV": 2})
    assert {row["cys_residue_id"] for row in rows} == {"CYS:275-", "CYS:285-"}
    for row in rows:
        assert row["human_review_completed"] == "true"
        assert row["human_task_relevance_decision"] == "RELEVANT"
        assert row["human_chemistry_decision"] == "POSITIVE"
        assert (row["protein_reactive_atom"], row["ligand_reactive_atom"]) == ("SG", "C15")
        assert row["selected_role_candidate_index_0based"] == "0"
        assert row["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        assert row["W_L_S_counts_json"] == "[9,0,16]"
        assert json.loads(row["boundary_bonds_json"]) == list(ingestion.BOUNDARY_BONDS)
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["authoritative_task_labels_created"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
        assert row["formal_training_admitted"] == "false"


def test_upstream_pre_graph_present_but_global_usable_pre_stays_zero(frozen_bundle) -> None:
    for row in frozen_bundle["matrix_rows"]:
        assert row["supporting_PRE_source_graph_count_per_event"] == "1"
        assert row["PRE_source_graph_present"] == "true"
        assert row["PRE_source_graph_count_per_event"] == "1"
        assert row["PRE_mapping_count_per_event"] == "0"
        assert row["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        assert row["PRE_status"] == "PRE_REACTION_UNRESOLVED"
        for field in (
            "PRE_topology_authority", "PRE_geometry_authority",
            "PRE_coordinates_authority", "PRE_reconstruction_performed",
            "POST_to_PRE_copy_performed", "PRE_zero_fill_performed",
        ):
            assert row[field] == "false"
    geometry = frozen_bundle["computation"].summary["geometry"]
    assert geometry["PRE_source_evidence_available_count"] == 0
    assert geometry["PRE_sample_authoritative_count"] == 0
    assert geometry["PRE_training_target_available_count"] == 0
    assert geometry["PRE_is_v1_hard_requirement"] is False
    assert geometry["POST_to_PRE_promotion_performed"] is False
    assert geometry["PRE_zero_fill_performed"] is False


def test_reconciliation_exact17_111_and_status_counts(frozen_bundle) -> None:
    result = frozen_bundle["reconciliation"]
    assert len({fact.source_binding_path for fact in result.normalized_facts}) == 17
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 107,
        "completed_positive_unit_count": 16,
        "completed_negative_event_count": 28,
        "completed_negative_unit_count": 5,
        "completed_total_event_count": 135,
        "completed_total_unit_count": 21,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 203,
        "unreviewed_unit_count": 110,
    }
    exact4 = set(subject.FOUR_M5_EXACT4_EVENT_IDS_V1)
    assert {
        row["current_review_status"]
        for row in result.reconciled_rows
        if row["canonical_event_id"] in exact4
    } == {"COMPLETED_HUMAN_POSITIVE"}


def test_exact18_overlay_and_non_target_996_dict_equal(frozen_bundle) -> None:
    before = {row["canonical_event_id"]: row for row in frozen_bundle["predecessor"].rows}
    after = {row["canonical_event_id"]: row for row in frozen_bundle["computation"].rows}
    exact4 = set(subject.FOUR_M5_EXACT4_EVENT_IDS_V1)
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == exact4
    assert sum(before[event_id] == after[event_id] for event_id in set(before) - exact4) == 996
    for event_id in exact4:
        assert {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        } == subject._AUTHORIZED_FOUR_M5_OVERLAY_FIELDS_V1
        assert after[event_id]["human_review_authority_source"] == subject.FOUR_M5_HUMAN_DECISION_SOURCE
        assert after[event_id]["positive_authority_source"] == subject.FOUR_M5_EVENT_MATRIX_SOURCE
        assert after[event_id]["training_materialization_allowed_current_source"] == "false"


def test_overlay_selector_is_exact_event_ids_not_ligand_wide() -> None:
    source = (REPO / subject.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    overlay = source[source.index("def _overlay_four_m5_exact4_v1"):source.index("def _top_pending_review_units_v1")]
    assert 'event_id not in matrix_by_event' in overlay
    assert 'row["ligand_component_id"] == "4M5"' not in overlay


def test_global_distributions_authority_and_role_counts(frozen_bundle) -> None:
    rows = frozen_bundle["computation"].rows
    assert Counter(row["current_global_status"] for row in rows) == Counter(subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1)
    assert Counter(row["chemistry_disposition"] for row in rows) == Counter({"POSITIVE": 124, "NOT_ESTABLISHED": 90, "UNRESOLVED": 786})
    assert Counter(row["task_relevance_disposition"] for row in rows) == Counter({"RELEVANT": 125, "NOT_RELEVANT": 90, "UNRESOLVED": 785})
    assert Counter(row["training_use_disposition"] for row in rows) == Counter({"INCLUDE": 56, "EXCLUDE_FROM_TRAINING_ONLY": 68, "NOT_APPLICABLE": 90, "UNRESOLVED": 786})
    assert sum(row["reactive_pair_sample_authoritative"] == "true" for row in rows) == 124
    assert sum(row["role_partition_sample_authoritative"] == "true" for row in rows) == 124
    assert sum(row["future_training_admission_candidate"] == "true" for row in rows) == 39
    assert sum(row["formal_training_admitted"] == "true" for row in rows) == 5
    assert Counter(row["role_profile"] for row in rows if row["role_partition_sample_authoritative"] == "true") == Counter({"DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 72, "STRICT_LINKER_PRESENT_V1": 52})


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
        "warhead_only": 124,
        "linker_plus_warhead": 52,
        "scaffold_plus_warhead": 52,
        "scaffold_only": 124,
        "scaffold_plus_linker_plus_warhead": 124,
    }


def test_blocker_counts_are_source_derived_and_nonexclusive(frozen_bundle) -> None:
    blockers = frozen_bundle["computation"].summary["blockers"]
    assert blockers["non_exclusive_counts_must_not_be_summed"] is True
    assert blockers["chemistry_unresolved"] == {"all_1000": 786}
    assert blockers["feature_semantics_pending"] == {"within_positive_124": 124}
    assert blockers["human_training_exclusion"] == {"within_positive_124": 68}
    assert blockers["missing_POST_training_authority"] == {"within_positive_124": 107, "within_include_56": 39}
    assert blockers["missing_split_authority"] == {"within_positive_124": 83, "within_include_56": 31}
    assert blockers["missing_training_admission"] == {"within_positive_124": 119, "within_include_56": 51}
    assert blockers["pair_authority_absent"] == {"all_1000": 876, "within_positive_124": 0}
    assert blockers["role_authority_absent"] == {"all_1000": 876, "within_positive_124": 0}
    assert blockers["missing_tensor_integration"]["within_positive_124"] == 83
    assert blockers["missing_tensor_integration"]["within_include_56"] == 27
    assert blockers["missing_tensor_integration"]["missing_source_composition"]["4M5"] == 4


def test_dynamic_next_pending_and_queue_boundary(frozen_bundle) -> None:
    top = frozen_bundle["top"]
    assert top[0]["rank"] == 1
    assert all(item["review_unit_id"] != subject.FOUR_M5_REVIEW_UNIT_ID_V1 for item in top)
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
        "FOUR_M5_REVIEW_COMPLETED", "CENSUS_REFRESH",
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
    assert len(manifest["semantic_source_bindings"]) == 132
    assert manifest["predecessor_manifest_validation_binding"]["artifact_role"] == "PREDECESSOR_WITH_CER_MANIFEST_VALIDATION_IDENTITY"
    assert manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is False
    assert "sha256" not in manifest["manifest_self_binding"]
    checker._reject_dynamic_manifest_metadata(manifest)
    assert all("mode" not in binding and "exact_posix_mode" not in binding for binding in manifest["semantic_source_bindings"])


def test_deterministic_second_full_build_only(frozen_bundle) -> None:
    rebuilt = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_4m5_v1(REPO)
    assert rebuilt == frozen_bundle["artifacts"]
    assert set(rebuilt) == {subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE}


def test_materialization_rejects_unexpected_entry_before_build(tmp_path: Path) -> None:
    output = tmp_path / "contaminated"
    output.mkdir()
    sentinel = output / "sentinel.txt"
    sentinel.write_bytes(b"unchanged")
    with pytest.raises(ERROR, match="OUTPUT_DIRECTORY_UNEXPECTED_ENTRY"):
        subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_4m5_v1(REPO, output)
    assert sentinel.read_bytes() == b"unchanged"
    assert list(output.iterdir()) == [sentinel]


def test_non_four_m5_mutation_fails_closed(frozen_bundle) -> None:
    computation = frozen_bundle["computation"]
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if row["canonical_event_id"] not in set(subject.FOUR_M5_EXACT4_EVENT_IDS_V1))
    rows[index]["current_runtime_model_usable"] = "true" if rows[index]["current_runtime_model_usable"] == "false" else "false"
    mutated = _replace_rows(computation, rows)
    with pytest.raises(ERROR, match="PREDECESSOR_DELTA_NOT_EXACT_FOUR_M5_EXACT4"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_4m5_v1(
            mutated,
            predecessor_computation=frozen_bundle["predecessor"],
            reconciliation_result=frozen_bundle["reconciliation"],
            matrix_rows=frozen_bundle["matrix_rows"],
        )


def test_pre_mapping_authority_mutation_fails_closed(frozen_bundle) -> None:
    rows = [dict(row) for row in frozen_bundle["matrix_rows"]]
    rows[0]["PRE_geometry_authority"] = "true"
    with pytest.raises(ERROR, match="FOUR_M5_EVENT_MATRIX_SEMANTICS_INVALID"):
        subject._validate_four_m5_matrix_rows_v1(rows)


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
