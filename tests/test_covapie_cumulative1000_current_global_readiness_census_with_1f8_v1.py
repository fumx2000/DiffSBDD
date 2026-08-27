from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_with_1f8_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_2vs_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_1f8_v1 as subject  # noqa: E402


ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWith1F8Error
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1",
    REPO / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="session")
def frozen():
    return predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_2vs_v1(REPO)


@pytest.fixture(scope="session")
def computation():
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(REPO)


def _replace_rows(computation, rows):
    return replace(computation, rows=tuple(rows))


def _mutate_row(computation, predicate, **updates: str):
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if predicate(row))
    rows[index].update(updates)
    return _replace_rows(computation, rows)


def _one_f8_predicate(row: dict[str, str]) -> bool:
    return row["canonical_event_id"] == subject.ONE_F8_EXACT8_EVENT_IDS_V1[0]


def test_public_api_is_minimal_and_reuses_predecessor_type_and_schema() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWith1F8Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_1f8_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1f8_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 is predecessor.CENSUS_COLUMNS_V1
    assert subject.CANONICAL_EXACT5_V1 is predecessor.CANONICAL_EXACT5_V1


def test_frozen_predecessor_and_one_f8_bindings_are_exact() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 8
    assert [item["sha256"] for item in verified] == [item[4] for item in checker.FROZEN_BINDINGS]


def test_happy_path_exact1000_and_public_validator(computation, frozen) -> None:
    assert type(computation) is subject.base.Cumulative1000CurrentGlobalReadinessComputationV1
    assert len(computation.rows) == 1000
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(
        computation, predecessor_computation=frozen
    )


def test_exact8_delta_and_992_dict_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == set(subject.ONE_F8_EXACT8_EVENT_IDS_V1)
    assert len(changed) == 8
    assert len(set(before) - changed) == 992
    assert all(before[event_id] == after[event_id] for event_id in set(before) - changed)
    expected_changed_fields = {
        "current_global_status", "current_review_status", "human_review_completed",
        "human_review_authority_source", "chemistry_disposition",
        "chemistry_authority_source", "task_relevance_disposition",
        "task_relevance_authority_source", "training_use_disposition",
        "human_training_excluded", "reactive_pair_sample_authoritative",
        "role_partition_sample_authoritative", "role_profile",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
        "training_materialization_allowed_current_source", "positive_authority_source",
    }
    assert all(
        {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        } == expected_changed_fields
        for event_id in changed
    )


def test_predecessor_exact8_state_is_proven(frozen) -> None:
    subject._assert_predecessor_one_f8_state_v1(frozen)
    rows = [row for row in frozen.rows if row["canonical_event_id"] in set(subject.ONE_F8_EXACT8_EVENT_IDS_V1)]
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (499, 500, 501, 502, 503, 504, 505, 506)
    assert all(row["current_review_status"] == "CURRENTLY_UNREVIEWED" for row in rows)
    assert all(row["chemistry_disposition"] == "UNRESOLVED" for row in rows)
    assert all(row["reactive_pair_raw_structural_evidence"] == "true" for row in rows)


def test_one_f8_refreshed_semantics_and_no_training_promotion(computation) -> None:
    rows = [row for row in computation.rows if row["canonical_event_id"] in set(subject.ONE_F8_EXACT8_EVENT_IDS_V1)]
    assert len(rows) == 8
    assert all(
        row["current_global_status"] == "COMPLETED_HUMAN_POSITIVE"
        and row["human_review_completed"] == "true"
        and row["human_review_authority_source"] == subject.ONE_F8_FORMAL_DECISION_SOURCE
        and row["chemistry_disposition"] == "POSITIVE"
        and row["chemistry_authority_source"] == subject.ONE_F8_EVENT_MATRIX_SOURCE
        and row["task_relevance_disposition"] == "RELEVANT"
        and row["training_use_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"
        and row["reactive_pair_sample_authoritative"] == "true"
        and row["reactive_pair_training_target_available"] == "false"
        and row["role_partition_sample_authoritative"] == "true"
        and row["role_profile"] == "STRICT_LINKER_PRESENT_V1"
        and row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]"
        and row["post_geometry_training_target_available"] == "false"
        and row["pre_geometry_authoritative"] == "false"
        and row["future_training_admission_candidate"] == "false"
        and row["formal_split_authoritative"] == "false"
        and row["formal_training_admitted"] == "false"
        and row["current_runtime_model_usable"] == "false"
        for row in rows
    )


def test_one_f8_structural_fields_are_byte_for_field_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    assert all(
        before[event_id][field] == after[event_id][field]
        for event_id in subject.ONE_F8_EXACT8_EVENT_IDS_V1
        for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
    )
    exact8 = [after[event_id] for event_id in subject.ONE_F8_EXACT8_EVENT_IDS_V1]
    for field, expected in {
        "raw_structure_available": 8,
        "exact_cys_sg_event_recovered": 8,
        "explicit_covalent_evidence": 8,
        "distance_only_event_inference_used": 0,
        "full_coordinate_post_evidence_available": 8,
        "ccd_graph_complete": 8,
        "feature_compatible": 8,
        "structural_processing_success": 8,
        "post_geometry_source_evidence_available": 8,
    }.items():
        assert sum(row[field] == "true" for row in exact8) == expected


def test_exact_set_algebra(computation, frozen) -> None:
    before = subject._sets_for_algebra_v1(frozen.rows)
    after = subject._sets_for_algebra_v1(computation.rows)
    one_f8 = set(subject.ONE_F8_EXACT8_EVENT_IDS_V1)
    assert before["chemistry_positive"].isdisjoint(one_f8)
    assert after["chemistry_positive"] == before["chemistry_positive"] | one_f8
    assert after["chemistry_unresolved"] == before["chemistry_unresolved"] - one_f8
    assert after["task_relevant"] == before["task_relevant"] | one_f8
    assert after["task_unresolved"] == before["task_unresolved"] - one_f8
    assert after["training_exclude"] == before["training_exclude"] | one_f8
    assert after["training_unresolved"] == before["training_unresolved"] - one_f8
    for key in ("chemistry_not_established", "task_not_relevant", "training_not_applicable", "training_include"):
        assert after[key] == before[key]


def test_refreshed_exact11_and_disposition_counts(computation) -> None:
    assert Counter(row["current_global_status"] for row in computation.rows) == Counter(subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1)
    assert Counter(row["chemistry_disposition"] for row in computation.rows) == Counter({"POSITIVE": 82, "NOT_ESTABLISHED": 86, "UNRESOLVED": 832})
    assert Counter(row["task_relevance_disposition"] for row in computation.rows) == Counter({"RELEVANT": 83, "NOT_RELEVANT": 86, "UNRESOLVED": 831})
    assert Counter(row["training_use_disposition"] for row in computation.rows) == Counter({"INCLUDE": 29, "EXCLUDE_FROM_TRAINING_ONLY": 53, "NOT_APPLICABLE": 86, "UNRESOLVED": 832})


def test_pair_role_exact5_geometry_and_training_counts(computation) -> None:
    summary = computation.summary
    assert summary["reactive_pair"] == {
        "raw_structural_pair_evidence_count": 865,
        "sample_level_authoritative_pair_count": 82,
        "published_model_bound_target_constructible_count": 41,
        "current_runtime_bound_target_count": 17,
        "g3h_sample_authority_contribution_count": 8,
        "g3h_training_target_contribution_count": 0,
        "onl_sample_authority_contribution_count": 9,
        "onl_model_bound_target_contribution_count": 0,
        "prf_sample_authority_contribution_count": 8,
        "prf_model_bound_target_contribution_count": 0,
        "two_vs_sample_authority_contribution_count": 8,
        "two_vs_model_bound_target_contribution_count": 0,
        "one_f8_sample_authority_contribution_count": 8,
        "one_f8_model_bound_target_contribution_count": 0,
        "positive_without_sample_pair_authority_count": 0,
    }
    assert summary["role"]["role_profile_counts"] == {"STRICT_LINKER_PRESENT_V1": 39, "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 43, "other": 0}
    assert [task["structurally_applicable_authoritative_role_count"] for task in summary["canonical_exact5"]["tasks"]] == [82, 39, 39, 82, 82]
    assert summary["canonical_exact5"]["B3_present"] is True
    assert summary["canonical_exact5"]["sixth_task_present"] is False
    assert summary["geometry"]["POST_source_evidence_available_count"] == 867
    assert summary["geometry"]["POST_sample_authoritative_count"] == 21
    assert summary["geometry"]["POST_training_target_available_count"] == 17
    assert summary["geometry"]["PRE_sample_authoritative_count"] == 0
    assert summary["training_stage"]["future_training_admission_candidate_count"] == 12
    assert summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert summary["training_stage"]["formal_training_admitted_count"] == 5
    assert summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_refreshed_blockers_are_exact_and_obsolete_formulation_absent(computation) -> None:
    checker.independently_verify_counts_v1(list(computation.rows), computation.summary)
    blockers_text = json.dumps(computation.summary["blockers"], sort_keys=True)
    assert "all_missing_are_g3h_excluded_population" not in blockers_text
    assert computation.summary["blockers"]["missing_tensor_integration"]["missing_source_composition"] == {"G3H": 8, "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8}


def test_reconciliation_summary_and_dynamic_full_queue_top10(computation) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_1f8_v1(REPO)
    assert result.review_summary == {
        "universe_event_count": 338, "universe_review_unit_count": 131,
        "completed_positive_event_count": 65, "completed_positive_unit_count": 7,
        "completed_negative_event_count": 24, "completed_negative_unit_count": 4,
        "completed_total_event_count": 89, "completed_total_unit_count": 11,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "unreviewed_event_count": 249, "unreviewed_unit_count": 120,
    }
    expected = checker.independently_compute_top10_v1(REPO, result.reconciled_rows)
    assert computation.summary["top_pending_review_units_by_event_yield"] == expected
    assert len(expected) == 10
    assert expected[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D"
    assert expected[0]["ligand_component_ids"] == ["YUN"]
    assert expected[0]["pdb_ids"] == ["4LL0", "4LRM"]
    assert expected[0]["event_count"] == 7


def test_authority_boundary_and_non_actions(computation) -> None:
    boundary = computation.summary["authority_boundary"]
    assert boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is True
    assert boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is True
    assert boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is True
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["NEXT_RECOMMENDED_MAINLINE"] == "HIGH_YIELD_HUMAN_REVIEW_EXPANSION"
    assert boundary["next_priority_review_unit"] == "COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D"
    assert boundary["next_priority_review_ligand"] == "YUN"
    assert boundary["next_priority_review_event_count"] == 7
    assert boundary["HUMAN_REVIEW_DECISION_NOT_PERFORMED"] is True
    for key in (
        "new_human_authority_created", "new_chemistry_authority_created",
        "new_role_authority_created", "new_pair_authority_created",
        "new_reusable_authority_created", "tensor_integration_performed",
        "model_forward_performed", "backward_performed", "optimizer_step_performed",
        "training_admission_created", "training_performed", "parameter_update_performed",
        "feature_semantics_audit_performed",
    ):
        assert boundary[key] is False


def test_three_private_derived_contract_digests(computation) -> None:
    assert subject._sha256(subject._csv_bytes(computation.rows)) == "31d6add9d59d5eb9b40e8603eb9631230a75efa1f52590c3556827f62441175d"
    assert subject._sha256(subject._json_bytes(computation.summary)) == "9a341222ff0932603f900042579b47f6969c50259bfd0d89d75dffe55bf3641f"
    assert subject._sha256(subject._canonical_json(list(computation.semantic_source_bindings)).encode()) == "41c0579eeab164ae884cc3ba8afd358b54d97fe16ed324b0c84497940bfa72c5"


def test_semantic_bindings_preserve_predecessor_and_add_exact7_inputs(computation, frozen) -> None:
    checker.verify_semantic_bindings_v1(REPO, computation.semantic_source_bindings)
    identities = {(binding["path_namespace"], binding["path"]) for binding in computation.semantic_source_bindings}
    assert len(frozen.semantic_source_bindings) == 60
    assert len(identities) == len(computation.semantic_source_bindings) == 67
    assert {(binding["path_namespace"], binding["path"]) for binding in frozen.semantic_source_bindings} <= identities


def test_exact3_materialized_outputs_and_two_directory_determinism(tmp_path: Path) -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_1f8_v1(REPO)
    assert tuple(built) == (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1f8_v1(REPO, tmp_path / "one")
    two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1f8_v1(REPO, tmp_path / "two")
    assert one == two == built
    assert len(built[subject.CENSUS_FILE]) < 1024 * 1024


def test_materialized_exact7_inventory_and_checker() -> None:
    assert len(checker.verify_exact7_inventory_v1(REPO)) == 7
    result = checker.run_check_v1(REPO)
    assert result["changed_event_count"] == 8
    assert result["unchanged_event_count"] == 992
    assert result["refreshed_positive_count"] == 82
    assert result["semantic_source_binding_count"] == 67
    assert result["ready_for_formal_training"] is False


def test_non_one_f8_row_change_rejected(computation, frozen) -> None:
    mutated = _mutate_row(computation, lambda row: row["canonical_event_id"] not in set(subject.ONE_F8_EXACT8_EVENT_IDS_V1), current_global_status="CURRENTLY_IN_PROGRESS")
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(mutated, predecessor_computation=frozen)


def test_one_f8_missing_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows if row["canonical_event_id"] != subject.ONE_F8_EXACT8_EVENT_IDS_V1[0]]
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(_replace_rows(computation, rows), predecessor_computation=frozen)


def test_one_f8_extra_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    rows.append(dict(rows[0]))
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(_replace_rows(computation, rows), predecessor_computation=frozen)


def test_one_f8_duplicate_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    first = next(index for index, row in enumerate(rows) if row["canonical_event_id"] == subject.ONE_F8_EXACT8_EVENT_IDS_V1[0])
    second = next(index for index, row in enumerate(rows) if row["canonical_event_id"] == subject.ONE_F8_EXACT8_EVENT_IDS_V1[1])
    rows[second]["canonical_event_id"] = rows[first]["canonical_event_id"]
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(_replace_rows(computation, rows), predecessor_computation=frozen)


@pytest.mark.parametrize(
    "updates",
    [
        {"scaleup_rank": "540"},
        {"review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_DRIFT"},
        {"current_global_status": "CURRENTLY_UNREVIEWED", "current_review_status": "CURRENTLY_UNREVIEWED"},
        {"chemistry_disposition": "UNRESOLVED"},
        {"chemistry_disposition": "NEGATIVE"},
        {"training_use_disposition": "INCLUDE", "training_use_include": "true"},
        {"reactive_pair_sample_authoritative": "false"},
        {"reactive_pair_training_target_available": "true"},
        {"role_partition_sample_authoritative": "false"},
        {"role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"},
        {"structurally_applicable_task_ids_json": "[0,3,4]"},
        {"structurally_applicable_task_ids_json": "[0,1,2,4]"},
        {"structurally_applicable_task_ids_json": "[0,1,2,3,4,5]"},
        {"post_geometry_training_target_available": "true"},
        {"pre_geometry_authoritative": "true"},
        {"future_training_admission_candidate": "true"},
        {"formal_split_authoritative": "true"},
        {"formal_training_admitted": "true"},
        {"current_runtime_model_usable": "true"},
    ],
    ids=(
        "rank_drift", "review_unit_drift", "status_unreviewed",
        "chemistry_unresolved", "chemistry_negative", "training_include",
        "pair_authority_false", "pair_target_true", "role_authority_false",
        "direct_profile", "direct_applicability", "b3_omitted", "sixth_task",
        "post_training_true", "pre_authority_true", "future_candidate_true",
        "split_authority_true", "admitted_true", "runtime_usable_true",
    ),
)
def test_one_f8_semantic_drift_rejected(computation, frozen, updates) -> None:
    mutated = _mutate_row(computation, _one_f8_predicate, **updates)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(mutated, predecessor_computation=frozen)


def test_old_74_positive_projection_retained_rejected(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    rows = [dict(before.get(row["canonical_event_id"], row)) for row in computation.rows]
    assert Counter(row["chemistry_disposition"] for row in rows)["POSITIVE"] == 74
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(_replace_rows(computation, rows), predecessor_computation=frozen)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda summary: summary["top_pending_review_units_by_event_yield"].insert(0, {"rank": 1, "review_unit_id": subject.ONE_F8_REVIEW_UNIT_ID_V1, "event_count": 8}),
        lambda summary: summary["authority_boundary"].update({"next_priority_review_unit": subject.ONE_F8_REVIEW_UNIT_ID_V1}),
        lambda summary: summary["authority_boundary"].update({"next_priority_review_ligand": "1F8"}),
        lambda summary: summary["blockers"]["missing_tensor_integration"]["missing_source_composition"].update({"1F8": 0}),
    ],
    ids=("top_still_one_f8", "next_unit_not_yun", "next_ligand_not_yun", "missing_tensor_omits_one_f8_exact8"),
)
def test_summary_drift_rejected(computation, frozen, mutator) -> None:
    summary = deepcopy(computation.summary)
    mutator(summary)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(replace(computation, summary=summary), predecessor_computation=frozen)


def test_semantic_binding_drift_rejected(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings[-1]["sha256"] = "0" * 64
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(replace(computation, semantic_source_bindings=tuple(bindings)), predecessor_computation=frozen)


def test_predecessor_materialized_outputs_remain_exact() -> None:
    output = REPO / predecessor.OUTPUT_DIRECTORY_RELATIVE
    expected = {
        predecessor.CENSUS_FILE: (510436, "e0e4eb86d2961e2db2ca139ffe5492cfe9675b768826be85a3d0516b532ae24a"),
        predecessor.SUMMARY_FILE: (14888, "1b5cca68c2b81426cfae86921a666d8766dc40d31032c24ba90888f0b88588f7"),
        predecessor.MANIFEST_FILE: (28229, "ff6aaf5a9be58628dc859639f0558f970a50585213db4d2095012072940a031a"),
    }
    for filename, (size, sha256) in expected.items():
        payload = (output / filename).read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == sha256
