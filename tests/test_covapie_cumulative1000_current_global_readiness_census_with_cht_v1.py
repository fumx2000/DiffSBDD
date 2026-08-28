from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_with_cht_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_neq_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_cht_v1 as subject  # noqa: E402
from covalent_ext import covapie_cht_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithCHTError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_cht_v1",
    REPO / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_cht_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="session")
def frozen():
    return predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_neq_v1(
        REPO
    )


@pytest.fixture(scope="session")
def computation():
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
        REPO
    )


@pytest.fixture(scope="session")
def matrix_rows():
    payload = (REPO / subject.CHT_EVENT_MATRIX_RELATIVE).read_bytes()
    return [
        dict(row)
        for row in csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    ]


def _replace_rows(computation, rows):
    return replace(computation, rows=tuple(rows))


def _mutate_row(computation, predicate, **updates: str):
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if predicate(row))
    rows[index].update(updates)
    return _replace_rows(computation, rows)


def _cht_predicate(row: dict[str, str]) -> bool:
    return row["canonical_event_id"] == subject.CHT_EXACT5_EVENT_IDS_V1[0]


def test_public_api_is_minimal_and_reuses_predecessor_schema() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithCHTError",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_cht_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 is predecessor.CENSUS_COLUMNS_V1
    assert subject.CANONICAL_EXACT5_V1 is predecessor.CANONICAL_EXACT5_V1


def test_frozen_predecessor_and_cht_bindings_are_exact() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 8
    assert [item["sha256"] for item in verified] == [
        item[4] for item in checker.FROZEN_BINDINGS
    ]


def test_happy_path_source_derived_exact1000_and_validator(computation, frozen) -> None:
    assert type(computation) is subject.base.Cumulative1000CurrentGlobalReadinessComputationV1
    assert len(computation.rows) == 1000
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
        computation, predecessor_computation=frozen
    )


def test_compute_architecture_call_counts(monkeypatch) -> None:
    calls = {
        "predecessor": 0,
        "reconciliation": 0,
        "ingestion_build": 0,
        "ingestion_validate": 0,
    }
    original_predecessor = (
        subject.predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_neq_v1
    )
    original_reconciliation = (
        subject.cht_reconciliation.reconcile_real_completed_human_decisions_with_cht_v1
    )
    original_build = subject.cht_ingestion.build_artifacts_v1
    original_validate = subject.cht_ingestion.validate_completed_decision_projection_v1

    def wrapped_predecessor(root):
        calls["predecessor"] += 1
        return original_predecessor(root)

    def wrapped_reconciliation(root):
        calls["reconciliation"] += 1
        return original_reconciliation(root)

    def wrapped_build(root):
        calls["ingestion_build"] += 1
        return original_build(root)

    def wrapped_validate(artifacts, *, repo_root=None):
        calls["ingestion_validate"] += 1
        return original_validate(artifacts, repo_root=repo_root)

    monkeypatch.setattr(
        subject.predecessor,
        "compute_covapie_cumulative1000_current_global_readiness_census_with_neq_v1",
        wrapped_predecessor,
    )
    monkeypatch.setattr(
        subject.cht_reconciliation,
        "reconcile_real_completed_human_decisions_with_cht_v1",
        wrapped_reconciliation,
    )
    monkeypatch.setattr(subject.cht_ingestion, "build_artifacts_v1", wrapped_build)
    monkeypatch.setattr(
        subject.cht_ingestion,
        "validate_completed_decision_projection_v1",
        wrapped_validate,
    )
    subject.compute_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
        REPO
    )
    assert calls == {
        "predecessor": 1,
        "reconciliation": 2,
        "ingestion_build": 1,
        "ingestion_validate": 1,
    }


def test_exact5_identity_ranks_pdbs_and_cys450(matrix_rows) -> None:
    validated = subject._validate_cht_matrix_rows_v1(matrix_rows)
    assert tuple(row["canonical_event_id"] for row in validated) == (
        subject.CHT_EXACT5_EVENT_IDS_V1
    )
    assert tuple(int(row["scaleup_rank"]) for row in validated) == (
        913, 914, 915, 958, 959,
    )
    assert Counter(row["pdb_id"] for row in validated) == Counter(
        {"4V3F": 3, "5A2D": 2}
    )
    assert {row["cys_residue_id"] for row in validated} == {"CYS:450-"}


def test_exact5_delta_and_995_dict_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == set(subject.CHT_EXACT5_EVENT_IDS_V1)
    assert len(changed) == 5
    assert len(set(before) - changed) == 995
    assert all(before[event_id] == after[event_id] for event_id in set(before) - changed)
    assert all(
        {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        } == subject._AUTHORIZED_CHT_OVERLAY_FIELDS_V1
        for event_id in changed
    )
    assert len(subject._AUTHORIZED_CHT_OVERLAY_FIELDS_V1) == 17


def test_predecessor_exact5_state_is_proven(frozen) -> None:
    subject._assert_predecessor_cht_state_v1(frozen)
    rows = [
        row for row in frozen.rows
        if row["canonical_event_id"] in set(subject.CHT_EXACT5_EVENT_IDS_V1)
    ]
    assert all(row["current_review_status"] == "CURRENTLY_UNREVIEWED" for row in rows)
    assert all(row["chemistry_disposition"] == "UNRESOLVED" for row in rows)
    assert all(row["reactive_pair_raw_structural_evidence"] == "true" for row in rows)


def test_cht_refreshed_semantics_and_training_prohibitions(computation) -> None:
    rows = [
        row for row in computation.rows
        if row["canonical_event_id"] in set(subject.CHT_EXACT5_EVENT_IDS_V1)
    ]
    assert len(rows) == 5
    assert all(
        row["current_global_status"] == "COMPLETED_HUMAN_POSITIVE"
        and row["human_review_completed"] == "true"
        and row["human_review_authority_source"] == subject.CHT_FORMAL_DECISION_SOURCE
        and row["chemistry_disposition"] == "POSITIVE"
        and row["chemistry_authority_source"] == subject.CHT_EVENT_MATRIX_SOURCE
        and row["positive_authority_source"] == subject.CHT_EVENT_MATRIX_SOURCE
        and row["task_relevance_disposition"] == "RELEVANT"
        and row["training_use_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"
        and row["human_training_excluded"] == "true"
        and row["training_use_include"] == "false"
        and row["future_training_admission_candidate"] == "false"
        and row["reactive_pair_sample_authoritative"] == "true"
        and row["reactive_pair_training_target_available"] == "false"
        and row["role_partition_sample_authoritative"] == "true"
        and row["role_profile"] == "STRICT_LINKER_PRESENT_V1"
        and row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]"
        and row["post_geometry_sample_authoritative"] == "false"
        and row["post_geometry_training_target_available"] == "false"
        and row["pre_geometry_authoritative"] == "false"
        and row["pre_geometry_training_target_available"] == "false"
        and row["formal_split_authoritative"] == "false"
        and row["formal_split"] == ""
        and row["formal_training_admitted"] == "false"
        and row["current_runtime_model_usable"] == "false"
        and row["training_materialization_allowed_current_source"] == "false"
        for row in rows
    )


def test_cht_structural_fields_are_unchanged(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    assert all(
        before[event_id][field] == after[event_id][field]
        for event_id in subject.CHT_EXACT5_EVENT_IDS_V1
        for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
    )
    for event_id in subject.CHT_EXACT5_EVENT_IDS_V1:
        assert all(
            after[event_id][field] == value
            for field, value in subject._EXPECTED_CHT_STRUCTURAL_CELLS_V1.items()
        )


def test_exact_set_algebra_keeps_include_future_admission_runtime(computation, frozen) -> None:
    before = subject._sets_for_algebra_v1(frozen.rows)
    after = subject._sets_for_algebra_v1(computation.rows)
    cht = set(subject.CHT_EXACT5_EVENT_IDS_V1)
    assert after["chemistry_positive"] == before["chemistry_positive"] | cht
    assert after["chemistry_unresolved"] == before["chemistry_unresolved"] - cht
    assert after["task_relevant"] == before["task_relevant"] | cht
    assert after["task_unresolved"] == before["task_unresolved"] - cht
    assert after["training_exclude"] == before["training_exclude"] | cht
    assert after["training_unresolved"] == before["training_unresolved"] - cht
    for key in (
        "chemistry_negative", "chemistry_not_established", "task_not_relevant",
        "training_include", "training_not_applicable", "future_candidate",
        "formal_split", "formal_admitted", "runtime_usable",
    ):
        assert after[key] == before[key]


def test_global_chemistry_task_training_and_status_counts(computation) -> None:
    assert Counter(row["chemistry_disposition"] for row in computation.rows) == Counter(
        {"POSITIVE": 100, "NOT_ESTABLISHED": 86, "UNRESOLVED": 814}
    )
    assert Counter(
        row["task_relevance_disposition"] for row in computation.rows
    ) == Counter({"RELEVANT": 101, "NOT_RELEVANT": 86, "UNRESOLVED": 813})
    assert Counter(row["training_use_disposition"] for row in computation.rows) == Counter(
        {
            "INCLUDE": 36, "EXCLUDE_FROM_TRAINING_ONLY": 64,
            "NOT_APPLICABLE": 86, "UNRESOLVED": 814,
        }
    )
    assert Counter(row["current_global_status"] for row in computation.rows) == Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    )


def test_human_review_counts_are_distinct_from_global_negative(computation) -> None:
    assert computation.summary["human_review"] == {
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 107,
        "completed_unit_count": 14,
        "completed_positive_event_count": 83,
        "completed_positive_unit_count": 10,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "unreviewed_event_count": 231,
        "unreviewed_unit_count": 117,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 231,
        "current_pending_review_unit_count": 117,
    }
    assert computation.summary["global_status_distribution"]["counts"][
        "COMPLETED_HUMAN_NEGATIVE"
    ] == 54


def test_pair_role_exact5_geometry_and_training_counts(computation) -> None:
    summary = computation.summary
    assert summary["reactive_pair"]["sample_level_authoritative_pair_count"] == 100
    assert summary["reactive_pair"]["published_model_bound_target_constructible_count"] == 41
    assert summary["reactive_pair"]["cht_sample_authority_contribution_count"] == 5
    assert summary["reactive_pair"]["cht_model_bound_target_contribution_count"] == 0
    assert summary["role"]["role_profile_counts"] == {
        "STRICT_LINKER_PRESENT_V1": 44,
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 56,
        "other": 0,
    }
    assert summary["role"]["unknown_role_row_count"] == 900
    assert [
        task["structurally_applicable_authoritative_role_count"]
        for task in summary["canonical_exact5"]["tasks"]
    ] == [100, 44, 44, 100, 100]
    assert summary["canonical_exact5"]["B3_present"] is True
    assert summary["canonical_exact5"]["sixth_task_present"] is False
    assert summary["structural"] == {
        "raw_structure_available_count": 997,
        "exact_cys_sg_event_recovered_count": 867,
        "explicit_covalent_evidence_count": 867,
        "distance_only_event_inference_used_count": 0,
        "full_coordinate_post_evidence_available_count": 867,
        "ccd_graph_complete_count": 865,
        "feature_compatible_count": 865,
        "structural_processing_success_count": 865,
        "post_geometry_source_evidence_available_count": 867,
        "representation_gap_count": 78,
        "feature_incompatible_count": 2,
    }
    assert summary["geometry"]["POST_source_evidence_available_count"] == 867
    assert summary["geometry"]["POST_sample_authoritative_count"] == 21
    assert summary["geometry"]["POST_training_target_available_count"] == 17
    assert summary["geometry"]["PRE_source_evidence_available_count"] == 0
    assert summary["geometry"]["PRE_sample_authoritative_count"] == 0
    assert summary["geometry"]["PRE_training_target_available_count"] == 0
    assert summary["training_stage"]["future_training_admission_candidate_count"] == 19
    assert summary["training_stage"]["formal_training_admitted_count"] == 5
    assert summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_blocker_counts_are_exact_and_nonexclusive(computation) -> None:
    checker.independently_verify_counts_v1(list(computation.rows), computation.summary)
    blockers = computation.summary["blockers"]
    assert blockers["non_exclusive_counts_must_not_be_summed"] is True
    assert blockers["human_training_exclusion"] == {"within_positive_100": 64}
    assert blockers["missing_split_authority"] == {
        "within_positive_100": 59, "within_include_36": 11,
    }
    assert blockers["missing_tensor_integration"] == {
        "within_positive_100": 59,
        "within_include_36": 7,
        "all_missing_are_training_excluded_population": False,
        "missing_source_composition": {
            "G3H": 8, "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8,
            "YUN": 7, "NEQ": 6, "CHT": 5,
        },
    }
    assert blockers["missing_POST_training_authority"] == {
        "within_positive_100": 83, "within_include_36": 19,
    }
    assert blockers["missing_training_admission"] == {
        "within_positive_100": 95, "within_include_36": 31,
    }
    assert blockers["feature_semantics_pending"] == {"within_positive_100": 100}
    assert blockers["pair_authority_absent"] == {
        "all_1000": 900, "within_positive_100": 0,
    }
    assert blockers["role_authority_absent"] == {
        "all_1000": 900, "within_positive_100": 0,
    }


def test_refresh_delta_is_exact(computation) -> None:
    assert computation.summary["refresh_delta"] == {
        "frozen_predecessor_positive_count": 95,
        "cht_exact5_delta_count": 5,
        "refreshed_positive_count": 100,
        "frozen_predecessor_training_include_count": 36,
        "refreshed_training_include_count": 36,
        "frozen_predecessor_training_exclude_count": 59,
        "refreshed_training_exclude_count": 64,
        "frozen_predecessor_future_candidate_count": 19,
        "refreshed_future_candidate_count": 19,
        "changed_event_count": 5,
        "unchanged_event_count": 995,
        "derived_refresh_not_new_authority": True,
    }


def test_reconciliation_and_dynamic_pending_queue_head(computation) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_cht_v1(REPO)
    expected = checker.independently_compute_top10_v1(REPO, result.reconciled_rows)
    assert computation.summary["top_pending_review_units_by_event_yield"] == expected
    assert expected[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450"
    assert expected[0]["ligand_component_ids"] == ["OZJ"]
    assert expected[0]["pdb_ids"] == ["4CL8"]
    assert expected[0]["event_count"] == 4
    assert all(item["ligand_component_ids"] != ["CHT"] for item in expected)


def test_authority_boundary_and_non_actions(computation) -> None:
    boundary = computation.summary["authority_boundary"]
    assert boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is True
    assert boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is True
    assert boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is True
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["HUMAN_REVIEW_DECISION_NOT_PERFORMED"] is True
    assert boundary["NEXT_RECOMMENDED_MAINLINE"] == "HIGH_YIELD_HUMAN_REVIEW_EXPANSION"
    assert boundary["next_priority_review_ligand"] == "OZJ"
    assert boundary["feature_semantics_status"] == "AUDIT_REQUIRED_LATER"
    assert boundary["tensor_status"] == "NOT_STARTED"
    assert boundary["training_admission_status"] == "NOT_STARTED"
    assert boundary["training_status"] == "NOT_STARTED"
    for key in (
        "new_human_authority_created", "new_chemistry_authority_created",
        "new_pair_authority_created", "new_role_authority_created",
        "new_reusable_authority_created", "training_dataset_changed",
        "feature_semantics_audit_performed", "tensor_integration_performed",
        "model_forward_performed", "backward_performed",
        "optimizer_step_performed", "parameter_update_performed",
    ):
        assert boundary[key] is False


def test_projection_digests_and_semantic_bindings(computation, frozen) -> None:
    assert subject._sha256(subject._csv_bytes(computation.rows)) == checker.EXPECTED_CENSUS_SHA256
    assert subject._sha256(subject._json_bytes(computation.summary)) == checker.EXPECTED_SUMMARY_SHA256
    assert subject._sha256(
        subject._canonical_json(list(computation.semantic_source_bindings)).encode()
    ) == checker.EXPECTED_BINDINGS_SHA256
    checker.verify_semantic_bindings_v1(REPO, computation.semantic_source_bindings)
    predecessor_identities = {
        (item["path_namespace"], item["path"])
        for item in frozen.semantic_source_bindings
    }
    assert tuple(
        item for item in computation.semantic_source_bindings
        if (item["path_namespace"], item["path"]) in predecessor_identities
    ) == frozen.semantic_source_bindings
    assert len(computation.semantic_source_bindings) == 88


def test_exact3_build_materialization_and_two_directory_determinism(tmp_path: Path) -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1(
        REPO
    )
    one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1(
        REPO, tmp_path / "one"
    )
    two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1(
        REPO, tmp_path / "two"
    )
    assert one == two == built
    assert tuple(built) == (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    manifest = json.loads(built[subject.MANIFEST_FILE])
    assert manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is False


def test_exact7_placement_candidate_untracked_accepted() -> None:
    assert checker._classify_exact7_artifact_placement_v1(
        [], list(subject.EXACT7_PATHS_V1)
    ) == "CANDIDATE_UNTRACKED"


def test_exact7_placement_tracked_clean_accepted() -> None:
    assert checker._classify_exact7_artifact_placement_v1(
        list(subject.EXACT7_PATHS_V1), []
    ) == "TRACKED_CLEAN"


@pytest.mark.parametrize(
    ("tracked", "untracked"),
    [
        (list(subject.EXACT7_PATHS_V1[:3]), list(subject.EXACT7_PATHS_V1[3:])),
        ([], [*subject.EXACT7_PATHS_V1, "extra.txt"]),
        (list(subject.EXACT7_PATHS_V1[:-1]), []),
        (list(subject.EXACT7_PATHS_V1), ["extra.txt"]),
        ([], [*subject.EXACT7_PATHS_V1, subject.EXACT7_PATHS_V1[0]]),
        ([*subject.EXACT7_PATHS_V1[:-1], "wrong-path.txt"], []),
    ],
)
def test_exact7_placement_invalid_shapes_rejected(tracked, untracked) -> None:
    with pytest.raises(ValueError):
        checker._classify_exact7_artifact_placement_v1(tracked, untracked)


@pytest.mark.parametrize(
    ("tracked", "untracked", "expected"),
    [
        ([], list(reversed(subject.EXACT7_PATHS_V1)), "CANDIDATE_UNTRACKED"),
        (list(reversed(subject.EXACT7_PATHS_V1)), [], "TRACKED_CLEAN"),
    ],
)
def test_exact7_placement_is_order_independent(tracked, untracked, expected) -> None:
    assert checker._classify_exact7_artifact_placement_v1(tracked, untracked) == expected


def test_materialized_exact7_inventory_and_independent_checker() -> None:
    assert len(checker.verify_exact7_inventory_v1(REPO)) == 7
    result = checker.run_check_v1(REPO)
    assert result["changed_event_count"] == 5
    assert result["unchanged_event_count"] == 995
    assert result["refreshed_positive_count"] == 100
    assert result["task_relevant_count"] == 101
    assert result["training_include_count"] == 36
    assert result["training_exclude_count"] == 64
    assert result["future_candidate_count"] == 19
    assert result["semantic_source_binding_count"] == 88
    profile = result["exact7_artifact_placement_profile"]
    expected_counts_by_profile = {
        "CANDIDATE_UNTRACKED": (0, 7),
        "TRACKED_CLEAN": (7, 0),
    }
    assert profile in expected_counts_by_profile
    assert (
        result["tracked_exact7_count"], result["ordinary_untracked_count"],
    ) == expected_counts_by_profile[profile]
    assert result["ready_for_formal_training"] is False


def test_predecessor_cht_row_not_unreviewed_rejected(frozen) -> None:
    rows = [dict(row) for row in frozen.rows]
    index = next(
        i for i, row in enumerate(rows)
        if row["canonical_event_id"] == subject.CHT_EXACT5_EVENT_IDS_V1[0]
    )
    rows[index]["current_review_status"] = "CURRENTLY_IN_PROGRESS"
    with pytest.raises(ERROR):
        subject._assert_predecessor_cht_state_v1(replace(frozen, rows=tuple(rows)))


def test_predecessor_cht_wrong_review_unit_rejected(frozen) -> None:
    rows = [dict(row) for row in frozen.rows]
    index = next(
        i for i, row in enumerate(rows)
        if row["canonical_event_id"] == subject.CHT_EXACT5_EVENT_IDS_V1[0]
    )
    rows[index]["review_unit_id"] = "WRONG_UNIT"
    with pytest.raises(ERROR):
        subject._assert_predecessor_cht_state_v1(replace(frozen, rows=tuple(rows)))


def test_non_cht_output_row_change_rejected(computation, frozen) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["canonical_event_id"] not in set(subject.CHT_EXACT5_EVENT_IDS_V1),
        current_global_status="CURRENTLY_IN_PROGRESS",
    )
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
            mutated, predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    "label",
    ["PREDECESSOR_NEQ_CENSUS_OWNER", "CHT_RECONCILIATION_SUCCESSOR"],
)
def test_frozen_source_byte_drift_rejected(monkeypatch, label) -> None:
    original = subject._read_regular_file

    def corrupt(path, observed_label):
        payload = original(path, observed_label)
        return payload + b"x" if observed_label == label else payload

    monkeypatch.setattr(subject, "_read_regular_file", corrupt)
    with pytest.raises(ERROR):
        subject._verify_additive_sources(REPO)


def test_reconciliation_contract_drift_rejected(monkeypatch) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_cht_v1(REPO)
    summary = dict(result.review_summary)
    summary["completed_positive_event_count"] = 82
    monkeypatch.setattr(
        subject.cht_reconciliation,
        "reconcile_real_completed_human_decisions_with_cht_v1",
        lambda root: replace(result, review_summary=summary),
    )
    with pytest.raises(ERROR):
        subject._validate_cht_reconciliation_v1(REPO)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra"])
def test_matrix_event_coverage_mutations_rejected(matrix_rows, mutation) -> None:
    rows = [dict(row) for row in matrix_rows]
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[1]["canonical_event_id"] = rows[0]["canonical_event_id"]
    else:
        extra = dict(rows[-1])
        extra["canonical_event_id"] = "EXTRA_CHT_EVENT"
        extra["scaleup_rank"] = "960"
        rows.append(extra)
    with pytest.raises(ERROR):
        subject._validate_cht_matrix_rows_v1(rows)


@pytest.mark.parametrize(
    "updates",
    [
        {"scaleup_rank": "912"},
        {"pdb_id": "9ZZZ"},
        {"human_task_relevance_decision": "NOT_RELEVANT"},
        {"chemistry_known_positive": "false"},
        {"formal_event_training_use_decision": "INCLUDE"},
        {"human_training_excluded": "false"},
        {"training_use_allowed": "true"},
        {"candidate_for_future_training_admission": "true"},
        {"training_admitted": "true"},
        {"role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"},
        {"selected_role_candidate_index_0based": "3"},
        {"strict_profile_applicable_task_ids_json": "[0,3,4]"},
        {"POST_geometry_training_label_available_now": "true"},
        {"PRE_geometry_authority_available": "true"},
        {"formal_split_authority_created": "true"},
        {"current_runtime_model_usable": "true"},
    ],
)
def test_matrix_semantic_mutations_rejected(matrix_rows, updates) -> None:
    rows = [dict(row) for row in matrix_rows]
    rows[0].update(updates)
    with pytest.raises(ERROR):
        subject._validate_cht_matrix_rows_v1(rows)


@pytest.mark.parametrize("mutation", ["b3_removed", "sixth_task", "tasks_drift"])
def test_matrix_exact5_mutations_rejected(matrix_rows, mutation) -> None:
    rows = [dict(row) for row in matrix_rows]
    tasks = json.loads(rows[0]["canonical_task_applicability_json"])
    if mutation == "b3_removed":
        tasks.pop(3)
    elif mutation == "sixth_task":
        extra = dict(tasks[-1])
        extra["task_id"] = 5
        extra["semantic_long_name"] = "sixth_task"
        tasks.append(extra)
    else:
        tasks[1]["structurally_applicable"] = False
    rows[0]["canonical_task_applicability_json"] = json.dumps(
        tasks, sort_keys=True, separators=(",", ":")
    )
    with pytest.raises(ERROR):
        subject._validate_cht_matrix_rows_v1(rows)


@pytest.mark.parametrize(
    "updates",
    [
        {"task_relevance_disposition": "NOT_RELEVANT"},
        {"chemistry_disposition": "NEGATIVE"},
        {"training_use_disposition": "INCLUDE"},
        {"human_training_excluded": "false"},
        {"future_training_admission_candidate": "true"},
        {"formal_training_admitted": "true"},
        {"role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"},
        {"structurally_applicable_task_ids_json": "[0,3,4]"},
        {"structurally_applicable_task_ids_json": "[0,1,2,4]"},
        {"structurally_applicable_task_ids_json": "[0,1,2,3,4,5]"},
        {"reactive_pair_training_target_available": "true"},
        {"post_geometry_sample_authoritative": "true"},
        {"post_geometry_training_target_available": "true"},
        {"pre_geometry_authoritative": "true"},
        {"pre_geometry_training_target_available": "true"},
        {"formal_split_authoritative": "true"},
        {"formal_split": "train"},
        {"current_runtime_model_usable": "true"},
        {"training_materialization_allowed_current_source": "true"},
    ],
)
def test_refreshed_row_semantic_mutations_rejected(computation, frozen, updates) -> None:
    mutated = _mutate_row(computation, _cht_predicate, **updates)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
            mutated, predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("structural", "exact_cys_sg_event_recovered_count", 872),
        ("structural", "post_geometry_source_evidence_available_count", 872),
        ("geometry", "POST_source_evidence_available_count", 872),
        ("geometry", "POST_sample_authoritative_count", 26),
        ("geometry", "PRE_sample_authoritative_count", 5),
    ],
)
def test_structural_or_geometry_summary_mutation_rejected(
    computation, frozen, section, field, value
) -> None:
    summary = deepcopy(computation.summary)
    summary[section][field] = value
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
            replace(computation, summary=summary), predecessor_computation=frozen
        )


def test_source_binding_sha_drift_rejected(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings[-1]["sha256"] = "0" * 64
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
            replace(computation, semantic_source_bindings=tuple(bindings)),
            predecessor_computation=frozen,
        )


def test_duplicate_semantic_binding_rejected(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings.append(dict(bindings[-1]))
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
            replace(computation, semantic_source_bindings=tuple(bindings)),
            predecessor_computation=frozen,
        )


def test_materialized_csv_byte_mutation_rejected_by_independent_checker() -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1(
        REPO
    )
    text = built[subject.CENSUS_FILE].decode("utf-8")
    mutated = text.replace("COMPLETED_HUMAN_POSITIVE", "CURRENTLY_UNREVIEWED", 1).encode()
    rows = checker._parse_census(mutated)
    with pytest.raises(ValueError):
        checker.independently_verify_delta_v1(REPO, rows)


def test_summary_mutation_rejected_by_independent_checker(computation) -> None:
    summary = deepcopy(computation.summary)
    summary["blockers"]["missing_tensor_integration"]["within_positive_100"] = 58
    with pytest.raises(ValueError):
        checker.independently_verify_counts_v1(list(computation.rows), summary)


def test_manifest_binding_mutation_rejected(computation) -> None:
    artifacts = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_cht_v1(
        REPO
    )
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest["semantic_source_bindings"][-1]["sha256"] = "0" * 64
    mutated = dict(artifacts)
    mutated[subject.MANIFEST_FILE] = subject._json_bytes(manifest)
    with pytest.raises(ValueError):
        checker.verify_manifest_v1(mutated, computation)


def test_predecessor_exact7_materialized_outputs_remain_exact() -> None:
    output = REPO / predecessor.OUTPUT_DIRECTORY_RELATIVE
    expected = {
        predecessor.CENSUS_FILE: (
            521299,
            "8ffbb6df299321393b0aeba8945ed6a4de7f74ed659253d874494a7757e782f2",
        ),
        predecessor.SUMMARY_FILE: (
            15641,
            "08f61b61014658a51be184285aae478989717f67808ef0fe8e0dc09d068312d9",
        ),
        predecessor.MANIFEST_FILE: (
            36162,
            "c317ae71d6b0d8879538a7ca83d5f2ca427b4111d9c95a3e7d32eecb835c1309",
        ),
    }
    for filename, (size, sha256) in expected.items():
        payload = (output / filename).read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == sha256
