from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import pytest

from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_pyr_v1 as subject


REPO_ROOT = Path(__file__).resolve().parents[1]
ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithPYRError
TARGET = set(subject.PYR_EXACT4_EVENT_IDS_V1)

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_with_pyr", REPO_ROOT / subject.CHECKER_RELATIVE
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _parse(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as stream:
        return tuple(dict(row) for row in csv.DictReader(stream))


@pytest.fixture(scope="session")
def bundle():
    computation, frozen, reconciliation, matrix = subject._compute_components_v1(REPO_ROOT)
    return {
        "tuple": (computation, frozen, reconciliation, matrix),
        "computation": computation,
        "frozen": frozen,
        "reconciliation": reconciliation,
        "matrix": matrix,
    }


def _validate(bundle, computation) -> bool:
    return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_pyr_v1(
        computation,
        repo_root=REPO_ROOT,
        predecessor_computation=bundle["frozen"],
        reconciliation_result=bundle["reconciliation"],
        matrix_rows=bundle["matrix"],
    )


def _mutate(bundle, event_id: str, **changes: str):
    rows = deepcopy(list(bundle["computation"].rows))
    next(row for row in rows if row["canonical_event_id"] == event_id).update(changes)
    return replace(bundle["computation"], rows=tuple(rows))


def _materialized_exact3() -> dict[str, bytes]:
    output = REPO_ROOT / subject.OUTPUT_DIRECTORY_RELATIVE
    return {
        name: (output / name).read_bytes()
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }


def test_public_api_and_exact7_are_exact() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithPYRError",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_pyr_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_pyr_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_pyr_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_pyr_v1",
    )
    records = checker.verify_exact7_inventory_v1(REPO_ROOT)
    assert [record["path"] for record in records] == list(subject.EXACT7_PATHS_V1)
    assert len(records) == 7
    assert all(record["mode"] in {0o644, 0o664} for record in records)


def test_output_inventory_and_raw_byte_comparator_fail_closed() -> None:
    exact3 = (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    checker._validate_output_inventory_names_v1(exact3)
    with pytest.raises(ValueError, match="OUTPUT_DIRECTORY_NOT_EXACT3"):
        checker._validate_output_inventory_names_v1((*exact3, "extra.json"))
    built = _materialized_exact3()
    checker._verify_materialized_output_bytes_v1(built, dict(built))
    corrupted = dict(built)
    payload = bytearray(corrupted[subject.CENSUS_FILE])
    payload[-2] ^= 1
    corrupted[subject.CENSUS_FILE] = bytes(payload)
    with pytest.raises(ValueError, match="MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED"):
        checker._verify_materialized_output_bytes_v1(built, corrupted)


def test_strict_tamper_helper_rejects_wrong_exception_and_token() -> None:
    assert checker._expect_tamper(
        "expected", "EXPECTED_TOKEN", lambda: subject._fail("EXPECTED_TOKEN")
    ) == "EXPECTED_TOKEN"
    with pytest.raises(ValueError, match="TAMPER_WRONG_ERROR_CLASS_OR_PREFIX"):
        checker._expect_tamper(
            "plain", "EXPECTED_TOKEN",
            lambda: (_ for _ in ()).throw(ValueError("EXPECTED_TOKEN")),
        )
    with pytest.raises(TypeError):
        checker._expect_tamper(
            "type", "EXPECTED_TOKEN", lambda: (_ for _ in ()).throw(TypeError())
        )
    with pytest.raises(ValueError, match="TAMPER_WRONG_SEMANTIC_TOKEN"):
        checker._expect_tamper("wrong", "EXPECTED_TOKEN", lambda: subject._fail("OTHER"))
    with pytest.raises(ValueError, match="TAMPER_ACCEPTED"):
        checker._expect_tamper("accepted", "EXPECTED_TOKEN", lambda: None)


def test_predecessor_pyr_state_is_exactly_unreviewed(bundle) -> None:
    subject._assert_predecessor_pyr_state_v1(bundle["frozen"], REPO_ROOT)
    rows = [row for row in bundle["frozen"].rows if row["canonical_event_id"] in TARGET]
    assert len(rows) == 4
    assert all(
        (
            row["current_global_status"], row["human_review_completed"],
            row["chemistry_disposition"], row["task_relevance_disposition"],
            row["training_use_disposition"], row["human_training_excluded"],
            row["role_profile"], row["structurally_applicable_task_ids_json"],
        )
        == (
            "CURRENTLY_UNREVIEWED", "false", "UNRESOLVED", "UNRESOLVED",
            "UNRESOLVED", "false", "NOT_ESTABLISHED", "null",
        )
        for row in rows
    )


def test_reconciliation_and_matrix_published_semantics(bundle) -> None:
    publication = checker.independently_verify_pyr_publications_v1(
        bundle["reconciliation"], bundle["matrix"]
    )
    assert publication == {"sources": 27, "facts": 151, "matrix_rows": 4, "matrix_columns": 75}
    assert tuple(row["canonical_event_id"] for row in bundle["matrix"]) == subject.PYR_EXACT4_EVENT_IDS_V1
    assert tuple(int(row["scaleup_rank"]) for row in bundle["matrix"]) == (46, 47, 48, 49)
    assert all(
        (
            row["source_formal_generation_domain_decision"],
            row["normalized_task_relevance_disposition"],
            row["source_formal_training_use_decision"],
            row["normalized_training_disposition"],
        ) == ("IN_DOMAIN", "RELEVANT", "EXCLUDE", "EXCLUDE_FROM_TRAINING_ONLY")
        for row in bundle["matrix"]
    )


def test_exact4_delta_is_19_2_17_and_4_0_996(bundle) -> None:
    delta = checker.independently_verify_delta_v1(
        bundle["frozen"].rows, bundle["computation"].rows
    )
    assert delta == {
        "pyr_changed_row_count": 4,
        "non_pyr_changed_row_count": 0,
        "unchanged_row_count": 996,
        "authorized_overlay_field_count": 19,
        "authorized_but_unchanged_field_count": 2,
        "actual_changed_field_count": 17,
    }
    assert subject._AUTHORIZED_BUT_UNCHANGED_PYR_FIELDS_V1 == {
        "training_use_include", "future_training_admission_candidate",
    }


def test_target_projection_is_positive_relevant_but_training_excluded(bundle) -> None:
    rows = [row for row in bundle["computation"].rows if row["canonical_event_id"] in TARGET]
    assert len(rows) == 4
    assert all(
        (
            row["current_review_status"], row["chemistry_disposition"],
            row["task_relevance_disposition"], row["training_use_disposition"],
            row["human_training_excluded"], row["training_use_include"],
            row["future_training_admission_candidate"],
            row["training_materialization_allowed_current_source"],
        )
        == (
            "COMPLETED_HUMAN_POSITIVE", "POSITIVE", "RELEVANT",
            "EXCLUDE_FROM_TRAINING_ONLY", "true", "false", "false", "false",
        )
        for row in rows
    )
    assert all(row["human_review_authority_source"] == subject.PYR_HUMAN_DECISION_SOURCE for row in rows)
    assert all(row["positive_authority_source"] == subject.PYR_EVENT_MATRIX_SOURCE for row in rows)


def test_summary_counts_digests_blockers_and_exact5(bundle) -> None:
    summary = bundle["computation"].summary
    counts = checker.independently_verify_counts_v1(bundle["computation"].rows, summary)
    assert counts["applicability"] == [156, 56, 56, 156, 156]
    assert summary["global_status_distribution"]["counts"]["CURRENTLY_UNREVIEWED"] == 163
    assert summary["global_status_distribution"]["counts"]["COMPLETED_HUMAN_POSITIVE"] == 127
    assert summary["human_review"] == {
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 175,
        "completed_unit_count": 31,
        "completed_positive_event_count": 127,
        "completed_positive_unit_count": 21,
        "completed_negative_event_count": 48,
        "completed_negative_unit_count": 10,
        "unreviewed_event_count": 163,
        "unreviewed_unit_count": 100,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 163,
        "current_pending_review_unit_count": 100,
    }
    assert summary["canonical_exact5"]["task_count"] == 5
    assert summary["canonical_exact5"]["B3_present"] is True
    assert summary["canonical_exact5"]["sixth_task_present"] is False
    assert summary["canonical_exact5"]["tasks"][3]["semantic_name"] == "scaffold_only"


def test_orthogonal_population_stays_exact20_and_pyr_contributes_zero(bundle) -> None:
    section = bundle["computation"].summary["orthogonal_task_negative_chemistry_positive"]
    assert section == {
        "task_negative_chemistry_positive_population_count": 20,
        "gve_orthogonal_population_count": 4,
        "lcy_orthogonal_population_count": 4,
        "0d8_orthogonal_population_count": 4,
        "tp2_orthogonal_population_count": 4,
        "6oa_orthogonal_population_count": 4,
        "pyr_orthogonal_population_count": 0,
        "population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20": True,
    }


def test_geometry_runtime_and_historical_training_counts_stay_frozen(bundle) -> None:
    rows = bundle["computation"].rows
    counts = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "post_geometry_sample_authoritative", "post_geometry_training_target_available",
            "pre_geometry_authoritative", "pre_geometry_training_target_available",
            "current_runtime_model_usable", "formal_training_admitted",
        )
    }
    assert counts == {
        "post_geometry_sample_authoritative": 21,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
        "current_runtime_model_usable": 17,
        "formal_training_admitted": 5,
    }
    assert bundle["computation"].summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_next_pending_is_me7_exact3_with_both_pdb_ids(bundle) -> None:
    observed = checker.independently_verify_next_pending_v1(
        REPO_ROOT, bundle["reconciliation"], bundle["computation"].summary
    )
    assert observed == {
        "unit": "COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129",
        "raw_priority_rank": 32,
        "event_count": 3,
        "ligands": ["ME7"],
        "pdb_ids": ["3QVY", "3QVZ"],
        "event_ids": list(subject.NEXT_PENDING_EVENT_IDS_V1),
    }
    boundary = bundle["computation"].summary["authority_boundary"]
    assert "next_priority_review_pdb" not in boundary
    assert "PYR_REVIEW_STATE_CREATED" not in boundary
    assert boundary["review_state_created_by_this_refresh"] is False


def test_semantic_lineage_is_predecessor_exact186_plus_unique6(bundle) -> None:
    bindings = bundle["computation"].semantic_source_bindings
    assert len(bundle["frozen"].semantic_source_bindings) == 186
    assert bindings[:186] == bundle["frozen"].semantic_source_bindings
    assert len(bindings) == 192
    assert [item["artifact_role"] for item in bindings[186:]] == [
        "PREDECESSOR_WITH_6OA_CENSUS_OWNER",
        "PREDECESSOR_WITH_6OA_MATERIALIZED_CENSUS",
        "PREDECESSOR_WITH_6OA_MATERIALIZED_SUMMARY",
        "PYR_RECONCILIATION_OWNER",
        "PYR_INGESTION_OWNER",
        "PYR_EVENT_TASK_LABEL_AVAILABILITY",
    ]
    assert len({(item["path_namespace"], item["path"]) for item in bindings}) == 192
    predecessor_roles = {item["artifact_role"] for item in bindings[:186]}
    additive_roles = [item["artifact_role"] for item in bindings[186:]]
    assert len(additive_roles) == len(set(additive_roles)) == 6
    assert predecessor_roles.isdisjoint(additive_roles)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("current_review_status", "CURRENTLY_UNREVIEWED", "PYR_CHANGED_FIELD_SET_NOT_EXACT17"),
        ("task_relevance_disposition", "NOT_RELEVANT", "PYR_REFRESHED_SEMANTICS_INVALID"),
        ("training_use_disposition", "INCLUDE", "PYR_REFRESHED_SEMANTICS_INVALID"),
        ("training_use_disposition", "NOT_APPLICABLE", "PYR_REFRESHED_SEMANTICS_INVALID"),
        ("human_training_excluded", "false", "PYR_CHANGED_FIELD_SET_NOT_EXACT17"),
        ("future_training_admission_candidate", "true", "PYR_CHANGED_FIELD_SET_NOT_EXACT17"),
        ("reactive_pair_sample_authoritative", "false", "PYR_CHANGED_FIELD_SET_NOT_EXACT17"),
        ("role_partition_sample_authoritative", "false", "PYR_CHANGED_FIELD_SET_NOT_EXACT17"),
    ),
)
def test_target_semantic_tampers_fail_closed(bundle, field: str, value: str, token: str) -> None:
    with pytest.raises(ERROR, match=token):
        _validate(bundle, _mutate(bundle, subject.PYR_EXACT4_EVENT_IDS_V1[0], **{field: value}))


def test_missing_duplicate_and_non_target_change_fail_closed(bundle) -> None:
    rows = deepcopy(list(bundle["computation"].rows))
    rows[0]["canonical_event_id"] = rows[1]["canonical_event_id"]
    with pytest.raises(ERROR, match="CENSUS_EVENT_ID_EMPTY_OR_DUPLICATE"):
        _validate(bundle, replace(bundle["computation"], rows=tuple(rows)))
    non_target = next(row for row in rows if row["canonical_event_id"] not in TARGET)
    with pytest.raises(ERROR, match="PREDECESSOR_DELTA_NOT_EXACT_PYR_EXACT4"):
        _validate(bundle, _mutate(bundle, non_target["canonical_event_id"], feature_semantics_status="TAMPER"))


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("source_formal_generation_domain_decision", "OUT_OF_DOMAIN", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("normalized_task_relevance_disposition", "NOT_RELEVANT", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("source_formal_training_use_decision", "INCLUDE", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("normalized_training_disposition", "INCLUDE", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("human_training_excluded", "false", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("training_use_allowed", "true", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("future_training_admission_candidate", "true", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("training_materialization_allowed", "true", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("B3_present", "false", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
        ("sixth_task", "true", "PYR_EVENT_MATRIX_SEMANTICS_INVALID"),
    ),
)
def test_matrix_semantic_tampers_fail_closed(bundle, field: str, value: str, token: str) -> None:
    matrix = deepcopy(list(bundle["matrix"]))
    matrix[0][field] = value
    with pytest.raises(ERROR, match=token):
        subject._validate_pyr_matrix_rows_v1(matrix)


def test_matrix_missing_duplicate_and_fifth_event_fail_closed(bundle) -> None:
    for mutation in (
        list(bundle["matrix"])[1:],
        [*bundle["matrix"], deepcopy(bundle["matrix"][0])],
        [deepcopy(bundle["matrix"][0]), *bundle["matrix"][1:]],
    ):
        if len(mutation) == 4:
            mutation[0]["canonical_event_id"] = mutation[1]["canonical_event_id"]
        with pytest.raises(ERROR, match="PYR_EVENT_MATRIX_IDENTITY_NOT_EXACT4"):
            subject._validate_pyr_matrix_rows_v1(mutation)


def test_summary_pending_digest_binding_and_authority_tampers_fail_closed(bundle) -> None:
    mutations = []
    wrong_count = deepcopy(bundle["computation"].summary)
    wrong_count["blockers"]["chemistry_unresolved"]["all_1000"] = 747
    mutations.append(wrong_count)
    wrong_digest = deepcopy(bundle["computation"].summary)
    wrong_digest["chemistry"]["POSITIVE"]["event_set_sha256"] = "0" * 64
    mutations.append(wrong_digest)
    wrong_next = deepcopy(bundle["computation"].summary)
    wrong_next["top_pending_review_units_by_event_yield"][0]["review_unit_id"] = subject.PYR_REVIEW_UNIT_ID_V1
    mutations.append(wrong_next)
    missing_pdb = deepcopy(bundle["computation"].summary)
    missing_pdb["authority_boundary"]["next_priority_review_pdb_ids"] = ["3QVY"]
    mutations.append(missing_pdb)
    training = deepcopy(bundle["computation"].summary)
    training["authority_boundary"]["TRAINING_STARTED"] = True
    mutations.append(training)
    for summary in mutations:
        with pytest.raises(ERROR, match="SUMMARY_NOT_EXACTLY_SOURCE_DERIVED"):
            _validate(bundle, replace(bundle["computation"], summary=summary))


def test_stale_summary_keys_are_rejected_directly(bundle) -> None:
    for key, value in (
        ("next_priority_review_pdb", "3QVY"),
        ("PYR_REVIEW_STATE_CREATED", False),
    ):
        summary = deepcopy(bundle["computation"].summary)
        summary["authority_boundary"][key] = value
        with pytest.raises(ERROR, match="SUMMARY_STALE_KEY"):
            subject._assert_no_stale_summary_keys(summary)


def test_source_binding_duplicate_and_count_drift_fail_closed(bundle) -> None:
    bindings = list(bundle["computation"].semantic_source_bindings)
    for drift in (tuple(bindings[:-1]), tuple([*bindings[:-1], bindings[-2]])):
        with pytest.raises(ERROR, match="SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6"):
            _validate(bundle, replace(bundle["computation"], semantic_source_bindings=drift))


def test_materialized_outputs_manifest_and_double_build(bundle) -> None:
    first = subject._build_artifacts_from_computation_v1(REPO_ROOT, bundle["computation"])
    second = subject._build_artifacts_from_computation_v1(REPO_ROOT, bundle["computation"])
    assert first == second == _materialized_exact3()
    manifest = json.loads(first[subject.MANIFEST_FILE])
    checker.verify_manifest_v1(REPO_ROOT, manifest, first)
    assert manifest["semantic_source_binding_count"] == 192
    assert manifest["manifest_self_SHA256_recorded"] is False


def test_materialization_outside_authorized_root_fails(tmp_path: Path) -> None:
    with pytest.raises(ERROR, match="OUTPUT_DIRECTORY_NOT_AUTHORIZED"):
        subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_pyr_v1(
            REPO_ROOT, tmp_path
        )


def test_lifecycle_index_parser_and_simulations_fail_closed() -> None:
    paths = list(subject.EXACT7_PATHS_V1)
    digest = "0" * 40
    good = [f"100644 {digest} 0 {path}" for path in paths]
    parsed = checker._parse_git_index_entries_v1(good, paths)
    assert [item["path"] for item in parsed] == paths
    for lines, token in (
        ([good[0].replace("100644", "100755", 1), *good[1:]], "TRACKED_GIT_INDEX_MODE_INVALID"),
        ([good[0].replace("100644", "120000", 1), *good[1:]], "TRACKED_GIT_INDEX_MODE_INVALID"),
        ([good[0].replace(" 0 ", " 1 ", 1), *good[1:]], "TRACKED_GIT_INDEX_STAGE_NOT_ZERO"),
        (good[:-1], "TRACKED_GIT_INDEX_PATH_SET_INVALID"),
        ([*good, good[0]], "TRACKED_GIT_INDEX_PATH_DUPLICATE"),
    ):
        with pytest.raises(ValueError, match=token):
            checker._parse_git_index_entries_v1(lines, paths)
    assert checker.check_lifecycle_simulations_v1() == {
        "candidate_untracked": True,
        "committed_unpushed": True,
        "published_successor": True,
        "legal_descendant": True,
    }


def test_checker_live_integration_accepts_candidate_or_tracked_clean(bundle, monkeypatch) -> None:
    monkeypatch.setattr(subject, "_compute_components_v1", lambda _root: bundle["tuple"])
    result = checker.run_check_v1(REPO_ROOT)
    assert result["status"] == "PASS"
    assert result["git"]["lifecycle"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert result["git"]["git_index_mode_checked"] == (
        result["git"]["lifecycle"] == "TRACKED_CLEAN"
    )
    assert result["materialized_equals_fresh_build"] is True
    assert result["deterministic_double_build"] is True
    assert set(result["semantic_probes"]) == {
        "pyr_still_unreviewed", "training_include", "training_not_applicable",
        "human_exclusion_false", "future_candidate_true", "pair_authority_false",
        "non_target_change", "duplicate_event", "wrong_population_count",
        "stale_single_pdb", "b3_missing", "sixth_task", "raw_output_bytes",
    }
