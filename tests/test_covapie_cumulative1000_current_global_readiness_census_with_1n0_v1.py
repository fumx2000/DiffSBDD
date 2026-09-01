"""Targeted contract tests for the cumulative1000 1N0 refresh V1."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
import io
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import covapie_completed_human_decision_reconciliation_with_1n0_v1 as reconciliation
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_i12_v1 as predecessor
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_1n0_v1 as subject

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1",
    REPO
    / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)
TARGET = set(subject.ONE_N0_EXACT4_EVENT_IDS_V1)


@pytest.fixture(scope="session")
def frozen():
    return predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_i12_v1(
        REPO
    )


@pytest.fixture(scope="session")
def computation():
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
        REPO
    )


@pytest.fixture(scope="session")
def artifacts():
    return subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        REPO
    )


@pytest.fixture(scope="session")
def matrix_rows():
    payload = (
        REPO / ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX
    ).read_bytes()
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))


def _mutated_computation(computation, *, rows=None, summary=None, bindings=None):
    return subject.base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=computation.rows if rows is None else tuple(rows),
        summary=computation.summary if summary is None else summary,
        semantic_source_bindings=(
            computation.semantic_source_bindings
            if bindings is None
            else tuple(bindings)
        ),
    )


def _rows_by_event(rows):
    return {row["canonical_event_id"]: row for row in rows}


def test_public_api_is_exact_and_minimal() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWith1N0Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1",
    )


def test_predecessor_schema_objects_are_reused() -> None:
    assert subject.CENSUS_COLUMNS_V1 is predecessor.CENSUS_COLUMNS_V1
    assert subject.CANONICAL_EXACT5_V1 is predecessor.CANONICAL_EXACT5_V1
    assert subject.base is predecessor.base
    assert len(subject.CENSUS_COLUMNS_V1) == 47


def test_authority_layering_does_not_bypass_ingestion() -> None:
    text = (REPO / subject.PRODUCTION_RELATIVE).read_text()
    assert "load_frozen_formal_decision_v1" not in text
    assert "if row[\"ligand_component_id\"] == \"1N0\"" not in text
    assert "covapie_completed_human_decision_reconciliation_with_1n0_v1" in text
    assert "covapie_1n0_completed_decision_ingestion" in text


def test_source_derived_exact1000_and_validation(computation) -> None:
    assert len(computation.rows) == 1000
    assert all(tuple(row) == subject.CENSUS_COLUMNS_V1 for row in computation.rows)
    assert [int(row["scaleup_rank"]) for row in computation.rows] == list(
        range(1, 1001)
    )
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
        computation
    )


def test_target_identity_is_exact4(computation) -> None:
    rows = [row for row in computation.rows if row["canonical_event_id"] in TARGET]
    assert len(rows) == 4
    assert len({row["canonical_event_id"] for row in rows}) == 4
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (775, 776, 778, 780)
    assert {row["review_unit_id"] for row in rows} == {
        "COVAPIE_BULK_REVIEW_UNIT_80FE8023FD901B01"
    }
    assert tuple(row["canonical_event_id"] for row in rows) == (
        "COVAPIE_CYS_SG_EVENT_V1:4JWS:C:CYS:73-:SG:G:1N0:C16",
        "COVAPIE_CYS_SG_EVENT_V1:4JWS:D:CYS:73-:SG:J:1N0:C16",
        "COVAPIE_CYS_SG_EVENT_V1:4JWU:C:CYS:19-:SG:G:1N0:C16",
        "COVAPIE_CYS_SG_EVENT_V1:4JX1:G:CYS:19-:SG:U:1N0:C16",
    )


def test_predecessor_target_state_is_fail_closed(frozen) -> None:
    subject._assert_predecessor_one_n0_state_v1(frozen)
    rows = [row for row in frozen.rows if row["canonical_event_id"] in TARGET]
    assert all(
        row["current_global_status"] == "CURRENTLY_UNREVIEWED"
        and row["priority_review_in_scope"] == "true"
        and row["current_review_status"] == "CURRENTLY_UNREVIEWED"
        and row["human_review_completed"] == "false"
        and row["chemistry_disposition"] == "UNRESOLVED"
        and row["task_relevance_disposition"] == "UNRESOLVED"
        and row["training_use_disposition"] == "UNRESOLVED"
        and row["reactive_pair_sample_authoritative"] == "false"
        and row["role_partition_sample_authoritative"] == "false"
        and row["canonical_mask_structural_labels_available"] == "false"
        for row in rows
    )


def test_exact9_delta_and_996_rows_equal(computation, frozen) -> None:
    before = _rows_by_event(frozen.rows)
    after = _rows_by_event(computation.rows)
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == TARGET
    assert len(set(before) - changed) == 996
    assert all(before[event_id] == after[event_id] for event_id in set(before) - TARGET)
    changed_sets = {
        frozenset(
            field
            for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        )
        for event_id in TARGET
    }
    assert changed_sets == {subject._AUTHORIZED_1N0_OVERLAY_FIELDS_V1}
    assert len(subject._AUTHORIZED_1N0_OVERLAY_FIELDS_V1) == 9


def test_target_non_exact9_fields_are_unchanged(computation, frozen) -> None:
    before = _rows_by_event(frozen.rows)
    after = _rows_by_event(computation.rows)
    assert all(
        before[event_id][field] == after[event_id][field]
        for event_id in TARGET
        for field in subject.CENSUS_COLUMNS_V1
        if field not in subject._AUTHORIZED_1N0_OVERLAY_FIELDS_V1
    )


@pytest.mark.parametrize("rank", [777, 779])
def test_ligand_wide_negative_control_entire_row_unchanged(
    rank, computation, frozen
) -> None:
    before = next(row for row in frozen.rows if int(row["scaleup_rank"]) == rank)
    after = next(row for row in computation.rows if int(row["scaleup_rank"]) == rank)
    assert after == before
    assert after["ligand_component_id"] == "1N0"
    assert after["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_D60E67E860A87B24"
    assert after["current_review_status"] == "CURRENTLY_UNREVIEWED"
    assert after["chemistry_disposition"] == "UNRESOLVED"
    assert after["task_relevance_disposition"] == "UNRESOLVED"
    assert after["training_use_disposition"] == "UNRESOLVED"


def test_exact9_post_refresh_semantics(computation) -> None:
    rows = [row for row in computation.rows if row["canonical_event_id"] in TARGET]
    assert all(
        row["current_global_status"] == "COMPLETED_HUMAN_NEGATIVE"
        and row["current_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
        and row["human_review_completed"] == "true"
        and row["human_review_authority_source"]
        == subject.ONE_N0_HUMAN_DECISION_SOURCE
        and row["chemistry_disposition"] == "NOT_ESTABLISHED"
        and row["chemistry_authority_source"]
        == subject.ONE_N0_EVENT_MATRIX_SOURCE
        and row["task_relevance_disposition"] == "NOT_RELEVANT"
        and row["task_relevance_authority_source"]
        == subject.ONE_N0_EVENT_MATRIX_SOURCE
        and row["training_use_disposition"] == "NOT_APPLICABLE"
        for row in rows
    )


def test_chemistry_not_established_is_not_negative_authority(computation) -> None:
    assert generic.CHEMISTRY_NOT_ESTABLISHED != generic.CHEMISTRY_NEGATIVE
    rows = [row for row in computation.rows if row["canonical_event_id"] in TARGET]
    assert all(
        row["positive_authority_source"] == ""
        and row["human_training_excluded"] == "false"
        and row["reactive_pair_sample_authoritative"] == "false"
        and row["role_partition_sample_authoritative"] == "false"
        and row["canonical_mask_structural_labels_available"] == "false"
        and row["post_geometry_sample_authoritative"] == "false"
        and row["post_geometry_training_target_available"] == "false"
        for row in rows
    )


def test_global_disposition_and_status_counts(computation) -> None:
    assert Counter(row["current_global_status"] for row in computation.rows) == (
        checker.EXPECTED_GLOBAL_COUNTS
    )
    assert Counter(row["chemistry_disposition"] for row in computation.rows) == Counter(
        {"POSITIVE": 116, "NOT_ESTABLISHED": 90, "UNRESOLVED": 794}
    )
    assert Counter(
        row["task_relevance_disposition"] for row in computation.rows
    ) == Counter({"RELEVANT": 117, "NOT_RELEVANT": 90, "UNRESOLVED": 793})
    assert Counter(row["training_use_disposition"] for row in computation.rows) == Counter(
        {
            "INCLUDE": 48, "EXCLUDE_FROM_TRAINING_ONLY": 68,
            "NOT_APPLICABLE": 90, "UNRESOLVED": 794,
        }
    )


def test_human_review_counts_are_distinct_from_global_negative(computation) -> None:
    assert computation.summary["human_review"] == checker.EXPECTED_HUMAN_REVIEW
    assert computation.summary["global_status_distribution"]["counts"][
        "COMPLETED_HUMAN_NEGATIVE"
    ] == 58
    assert computation.summary["human_review"][
        "completed_negative_event_count"
    ] == 28


def test_refresh_delta_is_negative_specific(computation) -> None:
    assert computation.summary["refresh_delta"] == checker.EXPECTED_REFRESH_DELTA
    assert "refreshed_positive_count" not in computation.summary["refresh_delta"]


def test_pair_role_exact5_geometry_and_training_are_unchanged(
    computation, frozen
) -> None:
    for key in (
        "structural", "geometry", "reactive_pair", "role",
        "canonical_exact5", "training_stage",
    ):
        assert computation.summary[key] == frozen.summary[key]
    exact5 = computation.summary["canonical_exact5"]
    assert exact5["task_count"] == 5
    assert exact5["B3_present"] is True
    assert exact5["sixth_task_present"] is False
    assert [
        item["structurally_applicable_authoritative_role_count"]
        for item in exact5["tasks"]
    ] == [116, 52, 52, 116, 116]
    assert computation.summary["role"]["unknown_role_row_count"] == 884
    assert computation.summary["training_stage"][
        "future_training_admission_candidate_count"
    ] == 31
    assert computation.summary["training_stage"]["formal_training_admitted_count"] == 5
    assert computation.summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert computation.summary["training_stage"][
        "ready_for_formal_training_event_count"
    ] == 0


def test_dynamic_pending_head_is_cer_and_d60e_remains_pending(computation) -> None:
    top, pending = checker.independently_compute_top10_v1(REPO)
    assert computation.summary["top_pending_review_units_by_event_yield"] == top
    assert pending == 112
    assert top[0]["rank"] == 1
    assert top[0]["raw_priority_rank"] == 19
    assert top[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A"
    assert top[0]["ligand_component_ids"] == ["CER"]
    assert top[0]["event_count"] == 4
    assert all(
        item["review_unit_id"] != subject.ONE_N0_REVIEW_UNIT_ID_V1 for item in top
    )


def test_source_bindings_are_exact_114_plus_6(computation, frozen) -> None:
    checker.independently_verify_bindings_v1(
        computation.semantic_source_bindings, frozen.semantic_source_bindings
    )
    assert computation.semantic_source_bindings[:114] == frozen.semantic_source_bindings
    assert len(computation.semantic_source_bindings) == 120
    assert [
        item["artifact_role"] for item in computation.semantic_source_bindings[114:]
    ] == [
        "PREDECESSOR_I12_CENSUS_OWNER",
        "PREDECESSOR_I12_MATERIALIZED_CENSUS",
        "PREDECESSOR_I12_MATERIALIZED_SUMMARY",
        "ONE_N0_RECONCILIATION_OWNER",
        "ONE_N0_INGESTION_OWNER",
        "ONE_N0_EVENT_TASK_LABEL_AVAILABILITY",
    ]


def test_materialized_exact3_is_source_derived(artifacts) -> None:
    live = {
        name: (REPO / subject.OUTPUT_DIRECTORY_RELATIVE / name).read_bytes()
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    assert live == artifacts


def test_manifest_contract_and_separate_predecessor_binding(artifacts, computation) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    checker.verify_manifest_v1(
        REPO, manifest, artifacts, computation.semantic_source_bindings
    )
    assert manifest["predecessor_manifest_validation_binding"]["byte_count"] == 51041
    assert manifest["predecessor_manifest_validation_binding"]["sha256"] == (
        "d22c388f7da5fecede11df15e3bc188196328e24009ad9363932bebc971da150"
    )
    assert manifest["predecessor_manifest_validation_binding"] not in (
        manifest["semantic_source_bindings"]
    )


def test_authority_boundary_forbids_training(computation) -> None:
    checker.verify_authority_boundary_v1(computation.summary)
    boundary = computation.summary["authority_boundary"]
    assert boundary["QUEUE_REFRESH"] is False
    assert boundary["training_started"] is False
    assert boundary["READY_FOR_TRAINING"] is False
    assert boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"] is True


def test_reconciliation_is_exact15_103_and_negative() -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_1n0_v1(
        REPO
    )
    assert len(result.source_bindings) == 15
    assert len(result.normalized_facts) == 103
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in TARGET]
    assert len(facts) == 4
    assert all(
        fact.task_relevance_disposition == "NOT_RELEVANT"
        and fact.chemistry_disposition == "NOT_ESTABLISHED"
        and fact.training_disposition == "NOT_APPLICABLE"
        for fact in facts
    )


def test_matrix_owner_projection_is_exact4(matrix_rows) -> None:
    validated = subject._validate_one_n0_matrix_rows_v1(matrix_rows)
    assert len(validated) == 4
    assert tuple(row["canonical_event_id"] for row in validated) == (
        subject.ONE_N0_EXACT4_EVENT_IDS_V1
    )


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "identity", "semantics"])
def test_matrix_coverage_and_semantic_mutations_fail_closed(
    matrix_rows, mutation
) -> None:
    rows = deepcopy(matrix_rows)
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = deepcopy(rows[0])
    elif mutation == "identity":
        rows[0]["canonical_event_id"] = "WRONG"
    else:
        rows[0]["chemistry_known_positive"] = "true"
    with pytest.raises(subject.Cumulative1000CurrentGlobalReadinessCensusWith1N0Error):
        subject._validate_one_n0_matrix_rows_v1(rows)


def test_exact9_semantic_mutation_fails_closed(computation) -> None:
    rows = deepcopy(list(computation.rows))
    target = next(row for row in rows if row["canonical_event_id"] in TARGET)
    target["positive_authority_source"] = subject.ONE_N0_EVENT_MATRIX_SOURCE
    with pytest.raises(
        subject.Cumulative1000CurrentGlobalReadinessCensusWith1N0Error,
        match="ONE_N0_CHANGED_FIELD_SET_INVALID|ONE_N0_REFRESHED_SEMANTICS_INVALID",
    ):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
            _mutated_computation(computation, rows=rows)
        )


def test_non_target_row_mutation_fails_closed(computation) -> None:
    rows = deepcopy(list(computation.rows))
    row = next(row for row in rows if row["canonical_event_id"] not in TARGET)
    row["feature_semantics_status"] = "WRONG"
    with pytest.raises(
        subject.Cumulative1000CurrentGlobalReadinessCensusWith1N0Error,
        match="PREDECESSOR_DELTA_NOT_EXACT_ONE_N0_EXACT4",
    ):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
            _mutated_computation(computation, rows=rows)
        )


def test_summary_mutation_fails_closed(computation) -> None:
    summary = deepcopy(computation.summary)
    summary["human_review"]["completed_event_count"] = 126
    with pytest.raises(
        subject.Cumulative1000CurrentGlobalReadinessCensusWith1N0Error,
        match="SUMMARY_NOT_EXACTLY_DERIVED",
    ):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
            _mutated_computation(computation, summary=summary)
        )


def test_duplicate_source_identity_fails_closed(computation) -> None:
    bindings = list(deepcopy(computation.semantic_source_bindings))
    bindings[-1]["path"] = bindings[-2]["path"]
    bindings[-1]["path_namespace"] = bindings[-2]["path_namespace"]
    with pytest.raises(
        subject.Cumulative1000CurrentGlobalReadinessCensusWith1N0Error,
        match="SEMANTIC_SOURCE_BINDING_DUPLICATE",
    ):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
            _mutated_computation(computation, bindings=bindings)
        )


def test_source_sha_drift_is_rejected(monkeypatch) -> None:
    specs = list(subject._ADDITIVE_SOURCE_SPECS_V1)
    first = list(specs[0])
    first[4] = "0" * 64
    specs[0] = tuple(first)
    monkeypatch.setattr(subject, "_ADDITIVE_SOURCE_SPECS_V1", tuple(specs))
    with pytest.raises(
        subject.Cumulative1000CurrentGlobalReadinessCensusWith1N0Error,
        match="BOUND_SOURCE_REJECTED",
    ):
        subject._verify_additive_sources(REPO)


def test_materialized_csv_mutation_is_rejected(artifacts) -> None:
    rows = checker._parse_census(artifacts[subject.CENSUS_FILE])
    row = next(row for row in rows if row["canonical_event_id"] not in TARGET)
    row["current_global_status"] = "COMPLETED_HUMAN_NEGATIVE"
    with pytest.raises(ValueError, match="DELTA_NOT_EXACT_ONE_N0_EXACT4"):
        checker.independently_verify_delta_v1(REPO, rows)


def test_manifest_dynamic_metadata_is_rejected(artifacts, computation) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest["timestamp"] = "forbidden"
    with pytest.raises(ValueError, match="DYNAMIC_METADATA"):
        checker.verify_manifest_v1(
            REPO, manifest, artifacts, computation.semantic_source_bindings
        )


def test_manifest_self_sha_is_rejected(artifacts, computation) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest["manifest_self_binding"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="MANIFEST_SELF_BINDING_INVALID"):
        checker.verify_manifest_v1(
            REPO, manifest, artifacts, computation.semantic_source_bindings
        )


def test_manifest_digest_mutation_is_rejected(artifacts, computation) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest["derived_projection_contract_digests"][
        "refreshed_summary_sha256"
    ] = "0" * 64
    with pytest.raises(ValueError, match="MANIFEST_DERIVED_DIGESTS_INVALID"):
        checker.verify_manifest_v1(
            REPO, manifest, artifacts, computation.semantic_source_bindings
        )


def test_two_builds_and_two_temp_materializations_are_identical(
    artifacts, tmp_path
) -> None:
    second = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        REPO
    )
    assert second == artifacts
    left = tmp_path / "left"
    right = tmp_path / "right"
    one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        REPO, left
    )
    two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        REPO, right
    )
    assert one == two == artifacts
    assert {path.name: path.read_bytes() for path in left.iterdir()} == artifacts
    assert {path.name: path.read_bytes() for path in right.iterdir()} == artifacts


def test_b4_source_binding_v2_clean_from_birth() -> None:
    result = checker.verify_b4_core_v1(REPO)
    assert result["new_semantic_exact_posix_mode_occurrence_count"] == 0
    assert result["new_ambiguous_mode_occurrence_count"] == 0
    assert result["B4_PRODUCTION_SELF_SCAN_PASSED"] is True
    assert result["B4_CHECKER_SELF_SCAN_PASSED"] is True


def test_candidate_lifecycle_and_exact7_safety() -> None:
    result = checker.verify_exact7_inventory_v1(REPO)
    assert result["profile"] in {
        "CANDIDATE_UNTRACKED",
        "TRACKED_CLEAN",
    }
    assert len(result["records"]) == 7
    assert all(item["expected_executable"] is False for item in result["records"])


def test_simulated_tracked_clean_lifecycle_is_supported(monkeypatch) -> None:
    exact7 = list(subject.EXACT7_PATHS_V1)

    def fake_git(_root: Path, *arguments: str) -> list[str]:
        if arguments in {
            ("diff", "--name-only"),
            ("diff", "--cached", "--name-only"),
            ("ls-files", "--others", "--exclude-standard"),
        }:
            return []
        if arguments == ("ls-files", "--", *subject.EXACT7_PATHS_V1):
            return exact7
        raise AssertionError("unexpected git observation:" + repr(arguments))

    def fake_run(command, **kwargs):
        assert command == (
            "git",
            "merge-base",
            "--is-ancestor",
            checker.BASELINE_COMMIT,
            "HEAD",
        )
        assert kwargs["cwd"] == REPO
        assert kwargs["check"] is False
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(checker, "_git", fake_git)
    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    result = checker.verify_exact7_inventory_v1(REPO)
    assert result["profile"] == "TRACKED_CLEAN"
    assert len(result["records"]) == 7


def test_simulated_mixed_lifecycle_fails_closed(monkeypatch) -> None:
    exact7 = list(subject.EXACT7_PATHS_V1)

    def fake_git(_root: Path, *arguments: str) -> list[str]:
        if arguments in {
            ("diff", "--name-only"),
            ("diff", "--cached", "--name-only"),
        }:
            return []
        if arguments == ("ls-files", "--others", "--exclude-standard"):
            return exact7[3:]
        if arguments == ("ls-files", "--", *subject.EXACT7_PATHS_V1):
            return exact7[:3]
        raise AssertionError("unexpected git observation:" + repr(arguments))

    monkeypatch.setattr(checker, "_git", fake_git)
    with pytest.raises(
        ValueError,
        match="EXACT7_PLACEMENT_OR_UNRELATED_UNTRACKED_INVALID",
    ):
        checker.verify_exact7_inventory_v1(REPO)


def test_checker_independent_delta_matches_production(computation) -> None:
    result = checker.independently_verify_delta_v1(REPO, computation.rows)
    assert result["changed_event_count"] == 4
    assert result["unchanged_event_count"] == 996
    assert result["rank777_changed"] is False
    assert result["rank779_changed"] is False
    assert result["changed_fields"] == sorted(
        subject._AUTHORIZED_1N0_OVERLAY_FIELDS_V1
    )
