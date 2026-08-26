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

from covalent_ext import covapie_cumulative1000_current_global_readiness_census_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_onl_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_onl_v1 as reconciliation  # noqa: E402


ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithONLError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_onl_v1",
    REPO
    / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_onl_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="session")
def frozen() -> predecessor.Cumulative1000CurrentGlobalReadinessComputationV1:
    return predecessor.compute_covapie_cumulative1000_current_global_readiness_census_v1(
        REPO
    )


@pytest.fixture(scope="session")
def computation() -> predecessor.Cumulative1000CurrentGlobalReadinessComputationV1:
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
        REPO
    )


def _replace_rows(computation, rows):
    return replace(computation, rows=tuple(rows))


def _mutate_row(computation, predicate, **updates: str):
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if predicate(row))
    rows[index].update(updates)
    return _replace_rows(computation, rows)


def _onl_predicate(row: dict[str, str]) -> bool:
    return row["canonical_event_id"] == subject.ONL_EXACT9_EVENT_IDS_V1[0]


def test_public_api_is_minimal_and_reuses_predecessor_type() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithONLError",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 is predecessor.CENSUS_COLUMNS_V1
    assert subject.CANONICAL_EXACT5_V1 is predecessor.CANONICAL_EXACT5_V1


def test_frozen_predecessor_and_onl_bindings_are_exact() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 7
    assert [item["sha256"] for item in verified] == [
        "2c35400febf7a7e407614c0bc3aa7504db2117f40430f2e990d3d41ac4bef6fe",
        "f4f44058a68f8161969b84a7e6b5efde08d6cd1d59520010c4f742d78b171dc9",
        "569625aef3b22d12af528e2afe61ed5ebf381f84642a063a81970894b80dc74a",
        "f2c94ac8b4fe8f3706d0de288e2d5bb24ef211cf56d39e8362b43bdb17a2f475",
        "abbf2f2bbc5d144395f78b80ece5a7b52ebd2ddefd802b9cf023fe15beb23d7a",
        "175f2f070967fb33e0133501a488cf30022818dbbadcd4b85f3ab497afda969c",
        "eb68b63046b561e857ae84640843914960c974ce7807be1ee18aba3f107581d5",
    ]


def test_happy_path_exact1000_and_public_validator(computation, frozen) -> None:
    assert type(computation) is predecessor.Cumulative1000CurrentGlobalReadinessComputationV1
    assert len(computation.rows) == 1000
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
        computation, predecessor_computation=frozen
    )


def test_exact9_delta_and_991_dict_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == set(subject.ONL_EXACT9_EVENT_IDS_V1)
    assert len(changed) == 9
    assert all(before[event_id] == after[event_id] for event_id in set(before) - changed)
    assert len(set(before) - changed) == 991


def test_predecessor_exact9_state_is_proven(frozen) -> None:
    subject._assert_predecessor_onl_state_v1(frozen)
    rows = [
        row
        for row in frozen.rows
        if row["canonical_event_id"] in set(subject.ONL_EXACT9_EVENT_IDS_V1)
    ]
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (24, 25, 26, 27, 134, 434, 435, 436, 437)
    assert all(row["current_review_status"] == "CURRENTLY_IN_PROGRESS" for row in rows)
    assert all(row["chemistry_disposition"] == "UNRESOLVED" for row in rows)


def test_onl_refreshed_semantics_and_no_training_promotion(computation) -> None:
    rows = [
        row
        for row in computation.rows
        if row["canonical_event_id"] in set(subject.ONL_EXACT9_EVENT_IDS_V1)
    ]
    assert len(rows) == 9
    assert all(
        row["current_global_status"] == "COMPLETED_HUMAN_POSITIVE"
        and row["human_review_completed"] == "true"
        and row["human_review_authority_source"] == subject.ONL_FORMAL_DECISION_SOURCE
        and row["chemistry_disposition"] == "POSITIVE"
        and row["chemistry_authority_source"] == subject.ONL_EVENT_MATRIX_SOURCE
        and row["task_relevance_disposition"] == "RELEVANT"
        and row["training_use_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"
        and row["reactive_pair_sample_authoritative"] == "true"
        and row["reactive_pair_training_target_available"] == "false"
        and row["role_partition_sample_authoritative"] == "true"
        and row["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        and row["structurally_applicable_task_ids_json"] == "[0,3,4]"
        and row["post_geometry_training_target_available"] == "false"
        and row["pre_geometry_authoritative"] == "false"
        and row["future_training_admission_candidate"] == "false"
        and row["formal_training_admitted"] == "false"
        and row["current_runtime_model_usable"] == "false"
        for row in rows
    )


def test_onl_structural_fields_are_byte_for_field_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    assert all(
        before[event_id][field] == after[event_id][field]
        for event_id in subject.ONL_EXACT9_EVENT_IDS_V1
        for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
    )


def test_exact_set_algebra(computation, frozen) -> None:
    before = subject._sets_for_algebra_v1(frozen.rows)
    after = subject._sets_for_algebra_v1(computation.rows)
    onl = set(subject.ONL_EXACT9_EVENT_IDS_V1)
    assert before["chemistry_positive"].isdisjoint(onl)
    assert after["chemistry_positive"] == before["chemistry_positive"] | onl
    assert after["chemistry_unresolved"] == before["chemistry_unresolved"] - onl
    assert after["task_relevant"] == before["task_relevant"] | onl
    assert after["task_unresolved"] == before["task_unresolved"] - onl
    assert after["training_exclude"] == before["training_exclude"] | onl
    assert after["training_unresolved"] == before["training_unresolved"] - onl
    for key in (
        "chemistry_not_established",
        "task_not_relevant",
        "training_not_applicable",
        "training_include",
    ):
        assert after[key] == before[key]


def test_refreshed_exact11_and_disposition_counts(computation) -> None:
    assert Counter(row["current_global_status"] for row in computation.rows) == Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    )
    assert Counter(row["chemistry_disposition"] for row in computation.rows) == Counter(
        {"POSITIVE": 58, "NOT_ESTABLISHED": 86, "UNRESOLVED": 856}
    )
    assert Counter(row["task_relevance_disposition"] for row in computation.rows) == Counter(
        {"RELEVANT": 59, "NOT_RELEVANT": 86, "UNRESOLVED": 855}
    )
    assert Counter(row["training_use_disposition"] for row in computation.rows) == Counter(
        {"INCLUDE": 29, "EXCLUDE_FROM_TRAINING_ONLY": 29, "NOT_APPLICABLE": 86, "UNRESOLVED": 856}
    )


def test_pair_role_exact5_geometry_and_training_counts(computation) -> None:
    summary = computation.summary
    assert summary["reactive_pair"] == {
        "raw_structural_pair_evidence_count": 865,
        "sample_level_authoritative_pair_count": 58,
        "published_model_bound_target_constructible_count": 41,
        "current_runtime_bound_target_count": 17,
        "g3h_sample_authority_contribution_count": 8,
        "g3h_training_target_contribution_count": 0,
        "onl_sample_authority_contribution_count": 9,
        "onl_model_bound_target_contribution_count": 0,
        "positive_without_sample_pair_authority_count": 0,
    }
    assert summary["role"]["role_profile_counts"] == {
        "STRICT_LINKER_PRESENT_V1": 31,
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 27,
        "other": 0,
    }
    assert [
        task["structurally_applicable_authoritative_role_count"]
        for task in summary["canonical_exact5"]["tasks"]
    ] == [58, 31, 31, 58, 58]
    assert summary["geometry"]["POST_source_evidence_available_count"] == 867
    assert summary["geometry"]["POST_sample_authoritative_count"] == 21
    assert summary["geometry"]["POST_training_target_available_count"] == 17
    assert summary["geometry"]["PRE_sample_authoritative_count"] == 0
    assert summary["training_stage"]["future_training_admission_candidate_count"] == 12
    assert summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert summary["training_stage"]["formal_training_admitted_count"] == 5
    assert summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_refreshed_blockers_are_exact_and_old_misleading_key_is_absent(computation) -> None:
    blockers = computation.summary["blockers"]
    assert blockers == {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": 856},
        "pair_authority_absent": {"all_1000": 942, "within_positive_58": 0},
        "role_authority_absent": {"all_1000": 942, "within_positive_58": 0},
        "human_training_exclusion": {"within_positive_58": 29},
        "missing_split_authority": {"within_positive_58": 17, "within_include_29": 4},
        "missing_tensor_integration": {
            "within_positive_58": 17,
            "within_include_29": 0,
            "all_missing_are_training_excluded_population": True,
            "missing_source_composition": {"G3H": 8, "ONL": 9},
        },
        "missing_POST_training_authority": {"within_positive_58": 41, "within_include_29": 12},
        "missing_training_admission": {"within_positive_58": 53, "within_include_29": 24},
        "feature_semantics_pending": {"within_positive_58": 58},
    }
    assert "all_missing_are_g3h_excluded_population" not in json.dumps(blockers)


def test_reconciliation_summary_and_dynamic_full_queue_top10(computation) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_onl_v1(REPO)
    assert result.review_summary["completed_positive_event_count"] == 41
    assert result.review_summary["completed_negative_event_count"] == 24
    assert result.review_summary["completed_total_event_count"] == 65
    assert result.review_summary["unreviewed_event_count"] == 273
    assert result.review_summary["unreviewed_unit_count"] == 123
    expected = subject._top_pending_review_units_v1(REPO, result)
    assert computation.summary["top_pending_review_units_by_event_yield"] == expected
    assert len(expected) == 10
    assert expected[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58"
    assert expected[0]["event_count"] == 8
    assert expected[0]["pdb_ids"] == ["3S19", "3UXJ"]
    assert expected[0]["ligand_component_ids"] == ["PRF"]


def test_authority_boundary_and_non_actions(computation) -> None:
    boundary = computation.summary["authority_boundary"]
    assert boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is True
    assert boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is True
    assert boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is True
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["NEXT_RECOMMENDED_MAINLINE"] == "HIGH_YIELD_HUMAN_REVIEW_EXPANSION"
    assert boundary["next_priority_review_unit"] == "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58"
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
    assert subject._sha256(subject._csv_bytes(computation.rows)) == subject._EXPECTED_REFRESHED_CENSUS_SHA256_V1
    assert subject._sha256(subject._json_bytes(computation.summary)) == subject._EXPECTED_REFRESHED_SUMMARY_SHA256_V1
    assert subject._sha256(
        subject._canonical_json(list(computation.semantic_source_bindings)).encode("utf-8")
    ) == subject._EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1


def test_semantic_bindings_preserve_predecessor_and_add_exact7_inputs(computation, frozen) -> None:
    identities = {
        (binding["path_namespace"], binding["path"])
        for binding in computation.semantic_source_bindings
    }
    assert len(identities) == len(computation.semantic_source_bindings) == 46
    assert {
        (binding["path_namespace"], binding["path"])
        for binding in frozen.semantic_source_bindings
    } <= identities
    for _role, path, namespace, _size, _sha256 in subject._ADDITIVE_SOURCE_SPECS_V1:
        assert (namespace, path.as_posix()) in identities


def test_exact3_materialized_outputs_and_two_directory_determinism(tmp_path: Path) -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(REPO)
    assert tuple(built) == (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    first = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
        REPO, tmp_path / "one"
    )
    second = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
        REPO, tmp_path / "two"
    )
    assert first == second == built
    assert len(built[subject.CENSUS_FILE]) < 1024 * 1024


def test_materialized_exact7_inventory_and_checker() -> None:
    assert len(checker.verify_exact7_inventory_v1(REPO)) == 7
    result = checker.run_check_v1(REPO)
    assert result["changed_event_count"] == 9
    assert result["unchanged_event_count"] == 991
    assert result["refreshed_positive_count"] == 58
    assert result["ready_for_formal_training"] is False


def test_non_onl_row_change_rejected(computation, frozen) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["canonical_event_id"] not in set(subject.ONL_EXACT9_EVENT_IDS_V1),
        current_global_status="CURRENTLY_IN_PROGRESS",
    )
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            mutated, predecessor_computation=frozen
        )


def test_onl_missing_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows if row["canonical_event_id"] != subject.ONL_EXACT9_EVENT_IDS_V1[0]]
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


def test_onl_extra_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    rows.append(dict(rows[0]))
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


def test_onl_duplicate_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    first = next(index for index, row in enumerate(rows) if row["canonical_event_id"] == subject.ONL_EXACT9_EVENT_IDS_V1[0])
    second = next(index for index, row in enumerate(rows) if row["canonical_event_id"] == subject.ONL_EXACT9_EVENT_IDS_V1[1])
    rows[second]["canonical_event_id"] = rows[first]["canonical_event_id"]
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    "updates",
    [
        {"current_review_status": "CURRENTLY_IN_PROGRESS"},
        {"chemistry_disposition": "UNRESOLVED"},
        {"chemistry_disposition": "NEGATIVE"},
        {"training_use_disposition": "INCLUDE", "training_use_include": "true"},
        {"reactive_pair_sample_authoritative": "false"},
        {"reactive_pair_training_target_available": "true"},
        {"role_partition_sample_authoritative": "false"},
        {"role_profile": "STRICT_LINKER_PRESENT_V1"},
        {"structurally_applicable_task_ids_json": "[0,1,2,3,4]"},
        {"structurally_applicable_task_ids_json": "[0,4]"},
        {"structurally_applicable_task_ids_json": "[0,3,4,5]"},
        {"post_geometry_training_target_available": "true"},
        {"pre_geometry_authoritative": "true"},
        {"future_training_admission_candidate": "true"},
        {"formal_training_admitted": "true"},
        {"current_runtime_model_usable": "true"},
    ],
    ids=(
        "status_in_progress", "chemistry_unresolved", "chemistry_negative",
        "training_include", "pair_authority_false", "pair_target_true",
        "role_authority_false", "strict_profile", "all_five_applicability",
        "b3_omitted", "sixth_task", "post_training_true", "pre_authority_true",
        "future_candidate_true", "admitted_true", "runtime_usable_true",
    ),
)
def test_onl_semantic_drift_rejected(computation, frozen, updates) -> None:
    mutated = _mutate_row(computation, _onl_predicate, **updates)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            mutated, predecessor_computation=frozen
        )


def test_old_49_positive_projection_retained_rejected(computation, frozen) -> None:
    rows = [dict(row) for row in computation.rows]
    for row in rows:
        if row["canonical_event_id"] in set(subject.ONL_EXACT9_EVENT_IDS_V1):
            row["chemistry_disposition"] = "UNRESOLVED"
            row["chemistry_authority_source"] = ""
            row["positive_authority_source"] = ""
    assert Counter(row["chemistry_disposition"] for row in rows)["POSITIVE"] == 49
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            _replace_rows(computation, rows), predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda summary: summary["top_pending_review_units_by_event_yield"].insert(
            0,
            {
                "rank": 1,
                "review_unit_id": subject.ONL_REVIEW_UNIT_ID_V1,
                "event_count": 9,
            },
        ),
        lambda summary: summary["authority_boundary"].update(
            {"next_priority_review_unit": subject.ONL_REVIEW_UNIT_ID_V1}
        ),
        lambda summary: summary["blockers"]["missing_tensor_integration"][
            "missing_source_composition"
        ].update({"ONL": 0}),
    ],
    ids=("top_still_onl", "next_not_prf", "missing_tensor_omits_onl9"),
)
def test_summary_drift_rejected(computation, frozen, mutator) -> None:
    summary = deepcopy(computation.summary)
    mutator(summary)
    mutated = replace(computation, summary=summary)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            mutated, predecessor_computation=frozen
        )


def test_predecessor_materialized_outputs_remain_exact() -> None:
    census = REPO / predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.CENSUS_FILE
    summary = REPO / predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.SUMMARY_FILE
    assert hashlib.sha256(census.read_bytes()).hexdigest() == "f4f44058a68f8161969b84a7e6b5efde08d6cd1d59520010c4f742d78b171dc9"
    assert hashlib.sha256(summary.read_bytes()).hexdigest() == "569625aef3b22d12af528e2afe61ed5ebf381f84642a063a81970894b80dc74a"
