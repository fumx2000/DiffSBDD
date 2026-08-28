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

from covalent_ext import covapie_completed_human_decision_reconciliation_with_yun_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_1f8_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_yun_v1 as subject  # noqa: E402


ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithYUNError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_yun_v1",
    REPO / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_yun_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="session")
def frozen():
    return predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(
        REPO
    )


@pytest.fixture(scope="session")
def computation():
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
        REPO
    )


def _replace_rows(computation, rows):
    return replace(computation, rows=tuple(rows))


def _mutate_row(computation, predicate, **updates: str):
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if predicate(row))
    rows[index].update(updates)
    return _replace_rows(computation, rows)


def _yun_predicate(row: dict[str, str]) -> bool:
    return row["canonical_event_id"] == subject.YUN_EXACT7_EVENT_IDS_V1[0]


def test_public_api_is_minimal_and_reuses_predecessor_type_and_schema() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithYUNError",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_yun_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 is predecessor.CENSUS_COLUMNS_V1
    assert subject.CANONICAL_EXACT5_V1 is predecessor.CANONICAL_EXACT5_V1


def test_frozen_predecessor_and_yun_bindings_are_exact() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 8
    assert [item["sha256"] for item in verified] == [
        item[4] for item in checker.FROZEN_BINDINGS
    ]


def test_happy_path_exact1000_and_public_validator(computation, frozen) -> None:
    assert type(computation) is subject.base.Cumulative1000CurrentGlobalReadinessComputationV1
    assert len(computation.rows) == 1000
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
        computation, predecessor_computation=frozen
    )


def test_exact7_delta_and_993_dict_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    changed = {
        event_id for event_id in before if before[event_id] != after[event_id]
    }
    assert changed == set(subject.YUN_EXACT7_EVENT_IDS_V1)
    assert len(changed) == 7
    assert len(set(before) - changed) == 993
    assert all(before[event_id] == after[event_id] for event_id in set(before) - changed)
    assert all(
        {
            field
            for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        == subject._AUTHORIZED_YUN_OVERLAY_FIELDS_V1
        for event_id in changed
    )
    assert len(subject._AUTHORIZED_YUN_OVERLAY_FIELDS_V1) == 18


def test_predecessor_exact7_state_is_proven(frozen) -> None:
    subject._assert_predecessor_yun_state_v1(frozen)
    rows = [
        row
        for row in frozen.rows
        if row["canonical_event_id"] in set(subject.YUN_EXACT7_EVENT_IDS_V1)
    ]
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (
        783, 784, 786, 787, 788, 789, 790,
    )
    assert all(row["current_review_status"] == "CURRENTLY_UNREVIEWED" for row in rows)
    assert all(row["chemistry_disposition"] == "UNRESOLVED" for row in rows)
    assert all(row["reactive_pair_raw_structural_evidence"] == "true" for row in rows)


def test_yun_refreshed_semantics_and_no_training_promotion(computation) -> None:
    rows = [
        row
        for row in computation.rows
        if row["canonical_event_id"] in set(subject.YUN_EXACT7_EVENT_IDS_V1)
    ]
    assert len(rows) == 7
    assert all(
        row["current_global_status"] == "COMPLETED_HUMAN_POSITIVE"
        and row["human_review_completed"] == "true"
        and row["human_review_authority_source"] == subject.YUN_FORMAL_DECISION_SOURCE
        and row["chemistry_disposition"] == "POSITIVE"
        and row["chemistry_authority_source"] == subject.YUN_EVENT_MATRIX_SOURCE
        and row["task_relevance_disposition"] == "RELEVANT"
        and row["training_use_disposition"] == "INCLUDE"
        and row["human_training_excluded"] == "false"
        and row["training_use_include"] == "true"
        and row["future_training_admission_candidate"] == "true"
        and row["reactive_pair_sample_authoritative"] == "true"
        and row["reactive_pair_training_target_available"] == "false"
        and row["role_partition_sample_authoritative"] == "true"
        and row["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        and row["structurally_applicable_task_ids_json"] == "[0,3,4]"
        and row["post_geometry_training_target_available"] == "false"
        and row["pre_geometry_authoritative"] == "false"
        and row["formal_split_authoritative"] == "false"
        and row["formal_training_admitted"] == "false"
        and row["current_runtime_model_usable"] == "false"
        and row["training_materialization_allowed_current_source"] == "false"
        for row in rows
    )


def test_yun_structural_fields_are_byte_for_field_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    assert all(
        before[event_id][field] == after[event_id][field]
        for event_id in subject.YUN_EXACT7_EVENT_IDS_V1
        for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
    )
    exact7 = [after[event_id] for event_id in subject.YUN_EXACT7_EVENT_IDS_V1]
    for field, expected in {
        "raw_structure_available": 7,
        "exact_cys_sg_event_recovered": 7,
        "explicit_covalent_evidence": 7,
        "distance_only_event_inference_used": 0,
        "full_coordinate_post_evidence_available": 7,
        "ccd_graph_complete": 7,
        "feature_compatible": 7,
        "structural_processing_success": 7,
        "post_geometry_source_evidence_available": 7,
    }.items():
        assert sum(row[field] == "true" for row in exact7) == expected


def test_exact_set_algebra_including_future_candidates(computation, frozen) -> None:
    before = subject._sets_for_algebra_v1(frozen.rows)
    after = subject._sets_for_algebra_v1(computation.rows)
    yun = set(subject.YUN_EXACT7_EVENT_IDS_V1)
    assert before["chemistry_positive"].isdisjoint(yun)
    assert after["chemistry_positive"] == before["chemistry_positive"] | yun
    assert after["chemistry_unresolved"] == before["chemistry_unresolved"] - yun
    assert after["task_relevant"] == before["task_relevant"] | yun
    assert after["task_unresolved"] == before["task_unresolved"] - yun
    assert after["training_include"] == before["training_include"] | yun
    assert after["training_unresolved"] == before["training_unresolved"] - yun
    assert after["future_candidate"] == before["future_candidate"] | yun
    for key in (
        "chemistry_negative", "chemistry_not_established", "task_not_relevant",
        "training_exclude", "training_not_applicable", "formal_split",
        "formal_admitted", "runtime_usable",
    ):
        assert after[key] == before[key]


def test_refreshed_exact11_and_disposition_counts(computation) -> None:
    assert Counter(row["current_global_status"] for row in computation.rows) == Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    )
    assert Counter(row["chemistry_disposition"] for row in computation.rows) == Counter(
        {"POSITIVE": 89, "NOT_ESTABLISHED": 86, "UNRESOLVED": 825}
    )
    assert Counter(
        row["task_relevance_disposition"] for row in computation.rows
    ) == Counter({"RELEVANT": 90, "NOT_RELEVANT": 86, "UNRESOLVED": 824})
    assert Counter(row["training_use_disposition"] for row in computation.rows) == Counter(
        {
            "INCLUDE": 36, "EXCLUDE_FROM_TRAINING_ONLY": 53,
            "NOT_APPLICABLE": 86, "UNRESOLVED": 825,
        }
    )


def test_pair_role_exact5_geometry_and_training_counts(computation) -> None:
    summary = computation.summary
    assert summary["reactive_pair"]["sample_level_authoritative_pair_count"] == 89
    assert summary["reactive_pair"]["published_model_bound_target_constructible_count"] == 41
    assert summary["reactive_pair"]["yun_sample_authority_contribution_count"] == 7
    assert summary["reactive_pair"]["yun_model_bound_target_contribution_count"] == 0
    assert summary["role"]["role_profile_counts"] == {
        "STRICT_LINKER_PRESENT_V1": 39,
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 50,
        "other": 0,
    }
    assert [
        task["structurally_applicable_authoritative_role_count"]
        for task in summary["canonical_exact5"]["tasks"]
    ] == [89, 39, 39, 89, 89]
    assert summary["canonical_exact5"]["B3_present"] is True
    assert summary["canonical_exact5"]["sixth_task_present"] is False
    assert summary["geometry"]["POST_source_evidence_available_count"] == 867
    assert summary["geometry"]["POST_sample_authoritative_count"] == 21
    assert summary["geometry"]["POST_training_target_available_count"] == 17
    assert summary["geometry"]["PRE_source_evidence_available_count"] == 0
    assert summary["geometry"]["PRE_sample_authoritative_count"] == 0
    assert summary["geometry"]["PRE_training_target_available_count"] == 0
    assert summary["training_stage"]["future_training_admission_candidate_count"] == 19
    assert summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert summary["training_stage"]["formal_training_admitted_count"] == 5
    assert summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_refreshed_blockers_are_exact_and_old_wording_absent(computation) -> None:
    checker.independently_verify_counts_v1(list(computation.rows), computation.summary)
    blockers = computation.summary["blockers"]
    blockers_text = json.dumps(blockers, sort_keys=True)
    assert "within_positive_82" not in blockers_text
    assert "within_include_29" not in blockers_text
    assert blockers["missing_tensor_integration"] == {
        "within_positive_89": 48,
        "within_include_36": 7,
        "all_missing_are_training_excluded_population": False,
        "missing_source_composition": {
            "G3H": 8, "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8, "YUN": 7,
        },
    }


def test_reconciliation_summary_and_dynamic_full_queue_top10(computation) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_yun_v1(REPO)
    assert result.review_summary == {
        "universe_event_count": 338, "universe_review_unit_count": 131,
        "completed_positive_event_count": 72, "completed_positive_unit_count": 8,
        "completed_negative_event_count": 24, "completed_negative_unit_count": 4,
        "completed_total_event_count": 96, "completed_total_unit_count": 12,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "unreviewed_event_count": 242, "unreviewed_unit_count": 119,
    }
    expected = checker.independently_compute_top10_v1(REPO, result.reconciled_rows)
    assert computation.summary["top_pending_review_units_by_event_yield"] == expected
    assert len(expected) == 10
    assert expected[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62"
    assert expected[0]["ligand_component_ids"] == ["NEQ"]
    assert expected[0]["pdb_ids"] == ["3V61", "3V62"]
    assert expected[0]["event_count"] == 6


def test_authority_boundary_and_non_actions(computation) -> None:
    boundary = computation.summary["authority_boundary"]
    assert boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is True
    assert boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is True
    assert boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is True
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["NEXT_RECOMMENDED_MAINLINE"] == "HIGH_YIELD_HUMAN_REVIEW_EXPANSION"
    assert boundary["next_priority_review_unit"] == "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62"
    assert boundary["next_priority_review_ligand"] == "NEQ"
    assert boundary["next_priority_review_event_count"] == 6
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
    assert subject._sha256(subject._csv_bytes(computation.rows)) == (
        "28eaa9833d69f191bf7eee91956588324ea1a3d145ebe5a99a31752a42e962e3"
    )
    assert subject._sha256(subject._json_bytes(computation.summary)) == (
        "084d264f874547544a6b674cc1672298d2ac4eb08f61d139aa654f975d1c5767"
    )
    assert subject._sha256(
        subject._canonical_json(list(computation.semantic_source_bindings)).encode()
    ) == "07063135286c4756db628a79c9b668efa150ca89c68989b2ecb7b8d427ca94b2"


def test_semantic_bindings_preserve_predecessor_and_add_exact7_inputs(
    computation, frozen
) -> None:
    checker.verify_semantic_bindings_v1(REPO, computation.semantic_source_bindings)
    identities = {
        (binding["path_namespace"], binding["path"])
        for binding in computation.semantic_source_bindings
    }
    assert len(frozen.semantic_source_bindings) == 67
    assert len(identities) == len(computation.semantic_source_bindings) == 74
    assert {
        (binding["path_namespace"], binding["path"])
        for binding in frozen.semantic_source_bindings
    } <= identities


def test_exact3_materialized_outputs_and_two_directory_determinism(
    tmp_path: Path,
) -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1(
        REPO
    )
    assert tuple(built) == (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1(
        REPO, tmp_path / "one"
    )
    two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1(
        REPO, tmp_path / "two"
    )
    assert one == two == built
    assert len(built[subject.CENSUS_FILE]) < 1024 * 1024


def test_materialized_exact7_inventory_and_checker() -> None:
    assert len(checker.verify_exact7_inventory_v1(REPO)) == 7
    result = checker.run_check_v1(REPO)
    assert result["changed_event_count"] == 7
    assert result["unchanged_event_count"] == 993
    assert result["refreshed_positive_count"] == 89
    assert result["training_include_count"] == 36
    assert result["future_candidate_count"] == 19
    assert result["semantic_source_binding_count"] == 74
    assert result["ready_for_formal_training"] is False


def test_non_yun_row_change_rejected(computation, frozen) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["canonical_event_id"] not in set(subject.YUN_EXACT7_EVENT_IDS_V1),
        current_global_status="CURRENTLY_IN_PROGRESS",
    )
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            mutated, predecessor_computation=frozen
        )


def test_yun_missing_rejected(computation, frozen) -> None:
    rows = [
        dict(row)
        for row in computation.rows
        if row["canonical_event_id"] != subject.YUN_EXACT7_EVENT_IDS_V1[0]
    ]
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


def test_yun_extra_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    rows.append(dict(rows[0]))
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


def test_yun_duplicate_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    first = next(
        index
        for index, row in enumerate(rows)
        if row["canonical_event_id"] == subject.YUN_EXACT7_EVENT_IDS_V1[0]
    )
    second = next(
        index
        for index, row in enumerate(rows)
        if row["canonical_event_id"] == subject.YUN_EXACT7_EVENT_IDS_V1[1]
    )
    rows[second]["canonical_event_id"] = rows[first]["canonical_event_id"]
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    "updates",
    [
        {"scaleup_rank": "791"},
        {"review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_DRIFT"},
        {"current_global_status": "CURRENTLY_UNREVIEWED", "current_review_status": "CURRENTLY_UNREVIEWED"},
        {"chemistry_disposition": "UNRESOLVED"},
        {"chemistry_disposition": "NEGATIVE"},
        {"training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY"},
        {"training_use_include": "false"},
        {"future_training_admission_candidate": "false"},
        {"reactive_pair_sample_authoritative": "false"},
        {"reactive_pair_training_target_available": "true"},
        {"role_partition_sample_authoritative": "false"},
        {"role_profile": "STRICT_LINKER_PRESENT_V1"},
        {"structurally_applicable_task_ids_json": "[0,1,2,3,4]"},
        {"structurally_applicable_task_ids_json": "[0,4]"},
        {"structurally_applicable_task_ids_json": "[0,3,4,5]"},
        {"post_geometry_training_target_available": "true"},
        {"pre_geometry_authoritative": "true"},
        {"pre_geometry_training_target_available": "true"},
        {"formal_split_authoritative": "true"},
        {"formal_training_admitted": "true"},
        {"current_runtime_model_usable": "true"},
        {"training_materialization_allowed_current_source": "true"},
    ],
    ids=(
        "rank_drift", "review_unit_drift", "status_unreviewed",
        "chemistry_unresolved", "chemistry_negative", "training_exclude",
        "training_include_false", "future_candidate_false", "pair_authority_false",
        "pair_target_true", "role_authority_false", "strict_profile",
        "all_five_applicability", "b3_omitted", "sixth_task",
        "post_training_true", "pre_authority_true", "pre_training_true",
        "split_authority_true", "admitted_true", "runtime_usable_true",
        "training_materialized_true",
    ),
)
def test_yun_semantic_drift_rejected(computation, frozen, updates) -> None:
    mutated = _mutate_row(computation, _yun_predicate, **updates)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            mutated, predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    ("field", "old_value"),
    [
        ("chemistry_disposition", "UNRESOLVED"),
        ("training_use_disposition", "UNRESOLVED"),
        ("future_training_admission_candidate", "false"),
    ],
    ids=("positive_remains_82", "include_remains_29", "future_candidates_remain_12"),
)
def test_old_global_projection_rejected(computation, frozen, field, old_value) -> None:
    rows = [dict(row) for row in computation.rows]
    yun = set(subject.YUN_EXACT7_EVENT_IDS_V1)
    for row in rows:
        if row["canonical_event_id"] in yun:
            row[field] = old_value
            if field == "training_use_disposition":
                row["training_use_include"] = "false"
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda summary: summary["top_pending_review_units_by_event_yield"].insert(
            0, {"rank": 1, "review_unit_id": subject.YUN_REVIEW_UNIT_ID_V1, "event_count": 7}
        ),
        lambda summary: summary["authority_boundary"].update(
            {"next_priority_review_unit": subject.YUN_REVIEW_UNIT_ID_V1}
        ),
        lambda summary: summary["authority_boundary"].update(
            {"next_priority_review_ligand": "YUN"}
        ),
        lambda summary: summary["blockers"]["missing_tensor_integration"].update(
            {"within_positive_89": 41}
        ),
        lambda summary: summary["blockers"]["missing_tensor_integration"].update(
            {"within_include_36": 0}
        ),
        lambda summary: summary["blockers"]["missing_tensor_integration"].update(
            {"all_missing_are_training_excluded_population": True}
        ),
    ],
    ids=(
        "top_still_yun", "next_unit_not_neq", "next_ligand_not_neq",
        "missing_tensor_still_41", "missing_tensor_include_still_0",
        "all_missing_training_excluded",
    ),
)
def test_summary_drift_rejected(computation, frozen, mutator) -> None:
    summary = deepcopy(computation.summary)
    mutator(summary)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            replace(computation, summary=summary), predecessor_computation=frozen
        )


def test_semantic_binding_drift_rejected(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings[-1]["sha256"] = "0" * 64
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            replace(computation, semantic_source_bindings=tuple(bindings)),
            predecessor_computation=frozen,
        )


def test_predecessor_materialized_outputs_remain_exact() -> None:
    output = REPO / predecessor.OUTPUT_DIRECTORY_RELATIVE
    expected = {
        predecessor.CENSUS_FILE: (
            514588,
            "31d6add9d59d5eb9b40e8603eb9631230a75efa1f52590c3556827f62441175d",
        ),
        predecessor.SUMMARY_FILE: (
            15062,
            "9a341222ff0932603f900042579b47f6969c50259bfd0d89d75dffe55bf3641f",
        ),
        predecessor.MANIFEST_FILE: (
            30872,
            "e9c159fa53550d3fd0a62e9cad0017255bae23a1952f8066e92ca4a56b0b7602",
        ),
    }
    for filename, (size, sha256) in expected.items():
        payload = (output / filename).read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == sha256
