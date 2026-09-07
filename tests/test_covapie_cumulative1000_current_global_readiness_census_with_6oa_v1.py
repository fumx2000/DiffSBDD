from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import pytest

from covalent_ext import covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_6oa_v1 as subject


REPO_ROOT = Path(__file__).resolve().parents[1]
ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWith6OAError
TARGET = set(subject.SIX_OA_EXACT4_EVENT_IDS_V1)

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_with_6oa", REPO_ROOT / subject.CHECKER_RELATIVE
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _parse(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as stream:
        return tuple(dict(row) for row in csv.DictReader(stream))


@pytest.fixture(scope="session")
def bundle():
    computation, frozen, reconciled, matrix = subject._compute_components_v1(REPO_ROOT)
    return {
        "computation": computation,
        "frozen": frozen,
        "reconciliation": reconciled,
        "matrix": matrix,
    }


def _validate(bundle, computation) -> bool:
    return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1(
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


def test_public_api_is_exact() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWith6OAError",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1",
    )


def test_exact7_inventory_is_exact() -> None:
    records = checker.verify_exact7_inventory_v1(REPO_ROOT)
    assert [record["path"] for record in records] == list(subject.EXACT7_PATHS_V1)
    assert len(records) == 7
    assert all(record["mode"] in {0o644, 0o664} for record in records)
    assert all(record["mode"] & 0o111 == 0 for record in records)


def test_output_directory_inventory_exact3_is_fail_closed() -> None:
    exact3 = (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    checker._validate_output_inventory_names_v1(exact3)
    with pytest.raises(ValueError, match="OUTPUT_DIRECTORY_NOT_EXACT3"):
        checker._validate_output_inventory_names_v1((*exact3, "extra.json"))
    with pytest.raises(ValueError, match="OUTPUT_DIRECTORY_NOT_EXACT3"):
        checker._validate_output_inventory_names_v1(exact3[:-1])


def test_materialized_output_byte_gate_accepts_identical_mapping() -> None:
    exact3 = _materialized_exact3()
    checker._verify_materialized_output_bytes_v1(exact3, dict(exact3))


@pytest.mark.parametrize(
    "filename", (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE),
)
def test_materialized_output_byte_gate_rejects_each_corrupted_output(filename: str) -> None:
    exact3 = _materialized_exact3()
    observed = dict(exact3)
    corrupted = bytearray(observed[filename])
    corrupted[-2] ^= 1
    observed[filename] = bytes(corrupted)
    with pytest.raises(ValueError) as caught:
        checker._verify_materialized_output_bytes_v1(exact3, observed)
    assert str(caught.value) == (
        subject.ERROR_TOKEN + ":MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED"
    )


def test_raw_byte_probe_detects_noop_comparator(monkeypatch) -> None:
    exact3 = _materialized_exact3()
    monkeypatch.setattr(checker, "_verify_materialized_output_bytes_v1", lambda *_args: None)
    with pytest.raises(ValueError) as caught:
        checker._probe_materialized_raw_byte_rejection_v1(exact3)
    assert str(caught.value) == "TAMPER_ACCEPTED:raw_byte_corruption"


def test_tamper_helper_accepts_only_prefixed_expected_valueerror() -> None:
    assert checker._expect_tamper(
        "expected", "EXPECTED_TOKEN", lambda: subject._fail("EXPECTED_TOKEN")
    ) == "EXPECTED_TOKEN"
    with pytest.raises(ValueError, match="TAMPER_WRONG_ERROR_PREFIX"):
        checker._expect_tamper(
            "plain_valueerror", "EXPECTED_TOKEN",
            lambda: (_ for _ in ()).throw(ValueError("EXPECTED_TOKEN")),
        )
    with pytest.raises((TypeError, KeyError, AssertionError)):
        checker._expect_tamper(
            "wrong_exception_class", "EXPECTED_TOKEN",
            lambda: (_ for _ in ()).throw(TypeError("EXPECTED_TOKEN")),
        )
    with pytest.raises(ValueError, match="TAMPER_WRONG_SEMANTIC_TOKEN"):
        checker._expect_tamper(
            "wrong_token", "EXPECTED_TOKEN", lambda: subject._fail("OTHER_TOKEN")
        )
    with pytest.raises(ValueError, match="TAMPER_ACCEPTED"):
        checker._expect_tamper("callback_passed", "EXPECTED_TOKEN", lambda: None)


def test_actual_git_index_mode_parser_is_fail_closed() -> None:
    paths = list(subject.EXACT7_PATHS_V1)
    digest = "0" * 40
    good = [f"100644 {digest} 0 {path}" for path in paths]
    parsed = checker._parse_git_index_entries_v1(good, paths)
    assert [item["path"] for item in parsed] == paths
    assert all(item["mode"] == "100644" and item["stage"] == "0" for item in parsed)
    probes = (
        ([good[0].replace("100644", "100755", 1), *good[1:]], "TRACKED_GIT_INDEX_MODE_INVALID"),
        ([good[0].replace("100644", "120000", 1), *good[1:]], "TRACKED_GIT_INDEX_MODE_INVALID"),
        ([good[0].replace(" 0 ", " 1 ", 1), *good[1:]], "TRACKED_GIT_INDEX_STAGE_NOT_ZERO"),
        (good[:-1], "TRACKED_GIT_INDEX_PATH_SET_INVALID"),
        ([*good, good[0]], "TRACKED_GIT_INDEX_PATH_DUPLICATE"),
    )
    for lines, token in probes:
        with pytest.raises(ValueError, match=token):
            checker._parse_git_index_entries_v1(lines, paths)


def test_predecessor_binding_and_unresolved_6oa_state(bundle) -> None:
    subject._assert_predecessor_6oa_state_v1(bundle["frozen"], REPO_ROOT)
    subject._verify_predecessor_bindings(
        REPO_ROOT, bundle["frozen"].semantic_source_bindings
    )
    assert len(bundle["frozen"].semantic_source_bindings) == 180
    rows = [row for row in bundle["frozen"].rows if row["canonical_event_id"] in TARGET]
    assert len(rows) == 4
    assert all(
        (
            row["current_review_status"], row["chemistry_disposition"],
            row["task_relevance_disposition"], row["training_use_disposition"],
            row["role_partition_sample_authoritative"],
        ) == ("CURRENTLY_UNREVIEWED", "UNRESOLVED", "UNRESOLVED", "UNRESOLVED", "false")
        for row in rows
    )


def test_reconciliation_exact26_147_and_review_summary(bundle) -> None:
    result = bundle["reconciliation"]
    assert len(result.source_bindings) == 26
    assert len(result.normalized_facts) == 147
    assert len({binding.stable_identity for binding in result.source_bindings}) == 26
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 123,
        "completed_positive_unit_count": 20,
        "completed_negative_event_count": 48,
        "completed_negative_unit_count": 10,
        "completed_total_event_count": 171,
        "completed_total_unit_count": 30,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 167,
        "unreviewed_unit_count": 101,
    }
    assert checker.reconciliation.SUCCESSOR_COVERAGE_SUMMARY == {
        "accepted_fact_count": 147,
        "accepted_review_unit_count": 26,
        "stable_source_identity_count": 26,
        "remaining_unreviewed_chemistry_event_count": 191,
        "remaining_unreviewed_review_unit_upper_bound": 105,
        "decision_category_distribution": {
            "chemistry_positive": 99,
            "chemistry_negative": 20,
            "task_domain_negative": 28,
            "task_domain_positive": 0,
        },
        "label_ready_event_count": 16,
        "training_mask_target_count": 0,
        "training_authority": False,
    }


def test_matrix_exact4_role_pair_pre_post_and_training_boundary(bundle) -> None:
    rows = subject._validate_6oa_matrix_rows_v1(bundle["matrix"])
    assert tuple(row["canonical_event_id"] for row in rows) == ingestion.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (855, 856, 857, 858)
    assert [row["geometry_outlier"] for row in rows] == ["false", "false", "true", "false"]
    for row in rows:
        assert row["human_review_completed"] == "true"
        assert row["source_formal_generation_domain_decision"] == "OUT_OF_DOMAIN"
        assert row["normalized_task_relevance_disposition"] == "NOT_RELEVANT"
        assert row["chemistry_disposition"] == "POSITIVE"
        assert row["task_domain_negative"] == "true"
        assert (row["protein_reactive_atom"], row["ligand_reactive_atom"]) == ("SG", "C5")
        assert row["pair_sample_authority"] == "true"
        assert row["role_sample_authority"] == "true"
        assert row["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        assert row["structurally_applicable_task_ids_json"] == "[0,3,4]"
        assert json.loads(row["warhead_atom_ids_json"]) == ["C5", "O3"]
        assert json.loads(row["linker_atom_ids_json"]) == []
        assert json.loads(row["minimal_seed_atom_ids_json"]) == ["C3", "C4"]
        assert row["primary_anchor"] == "C4"
        assert row["task_label_authority"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
        assert row["mask_tensor_targets_created"] == "false"
        assert row["formal_event_training_use_decision"] == "NOT_APPLICABLE"
        assert row["future_training_admission_candidate"] == "false"
        assert row["PRE_authority"] == "false"
        assert row["final_PRE_reaction_status"] == "PRE_REACTION_UNRESOLVED"
        assert row["POST_geometry_training_authority"] == "false"
        assert row["POST_geometry_training_target_created"] == "false"
        assert row["formal_training_admitted"] == "false"
        assert row["READY_FOR_TRAINING"] == "false"
        assert row["TRAINING_STARTED"] == "false"

def test_schema_exact4_delta_and_overlay_sets(bundle) -> None:
    before = {row["canonical_event_id"]: row for row in bundle["frozen"].rows}
    after = {row["canonical_event_id"]: row for row in bundle["computation"].rows}
    assert len(after) == 1000
    assert len(subject.CENSUS_COLUMNS_V1) == 47
    assert {event for event in before if before[event] != after[event]} == TARGET
    assert sum(before[event] == after[event] for event in set(before) - TARGET) == 996
    assert len(subject._AUTHORIZED_6OA_OVERLAY_FIELDS_V1) == 19
    assert len(subject._AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1) == 3
    assert len(subject._ACTUAL_CHANGED_6OA_FIELDS_V1) == 16
    for event in TARGET:
        changed = {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event][field] != after[event][field]
        }
        unchanged = {
            field for field in subject._AUTHORIZED_6OA_OVERLAY_FIELDS_V1
            if before[event][field] == after[event][field]
        }
        assert changed == subject._ACTUAL_CHANGED_6OA_FIELDS_V1
        assert unchanged == subject._AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1


def test_target_projection_semantics(bundle) -> None:
    rows = [row for row in bundle["computation"].rows if row["canonical_event_id"] in TARGET]
    for row in rows:
        assert row["current_global_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert row["human_review_authority_source"] == subject.SIX_OA_HUMAN_DECISION_SOURCE
        assert row["chemistry_disposition"] == "POSITIVE"
        assert row["task_relevance_disposition"] == "NOT_RELEVANT"
        assert row["training_use_disposition"] == "NOT_APPLICABLE"
        assert row["reactive_pair_sample_authoritative"] == "true"
        assert row["reactive_pair_training_target_available"] == "false"
        assert row["role_partition_sample_authoritative"] == "true"
        assert row["canonical_mask_structural_labels_available"] == "true"
        assert row["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        assert row["structurally_applicable_task_ids_json"] == "[0,3,4]"
        assert row["training_use_include"] == "false"
        assert row["future_training_admission_candidate"] == "false"
        assert row["formal_training_admitted"] == "false"
        assert row["current_runtime_model_usable"] == "false"
        assert row["training_materialization_allowed_current_source"] == "false"


def test_global_distributions_review_delta_and_authority_counts(bundle) -> None:
    rows = bundle["computation"].rows
    assert Counter(row["current_global_status"] for row in rows)["CURRENTLY_UNREVIEWED"] == 167
    assert Counter(row["current_global_status"] for row in rows)["COMPLETED_HUMAN_POSITIVE"] == 123
    assert Counter(row["current_global_status"] for row in rows)["COMPLETED_HUMAN_NEGATIVE"] == 78
    assert Counter(row["chemistry_disposition"] for row in rows) == Counter(
        {"POSITIVE": 160, "NOT_ESTABLISHED": 90, "UNRESOLVED": 750}
    )
    assert Counter(row["task_relevance_disposition"] for row in rows) == Counter(
        {"RELEVANT": 141, "NOT_RELEVANT": 110, "UNRESOLVED": 749}
    )
    assert Counter(row["training_use_disposition"] for row in rows) == Counter(
        {"INCLUDE": 68, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 110, "UNRESOLVED": 750}
    )
    assert sum(row["reactive_pair_sample_authoritative"] == "true" for row in rows) == 160
    assert sum(row["role_partition_sample_authoritative"] == "true" for row in rows) == 152
    assert sum(row["canonical_mask_structural_labels_available"] == "true" for row in rows) == 152


def test_exact5_b3_no_sixth_and_applicability_counts(bundle) -> None:
    assert len(subject.CANONICAL_EXACT5_V1) == 5
    assert subject.CANONICAL_EXACT5_V1[3] == (3, "scaffold_only", "B3")
    applicability = Counter()
    for row in bundle["computation"].rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    assert applicability == Counter({0: 152, 1: 56, 2: 56, 3: 152, 4: 152})
    assert bundle["computation"].summary["role"]["direct_profile_A_B3_C_count"] == 96
    assert bundle["computation"].summary["role"]["all_five_structurally_applicable_count"] == 56


def test_orthogonal_population_exact20(bundle) -> None:
    rows = bundle["computation"].rows
    orthogonal = {
        row["canonical_event_id"] for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == ("NOT_RELEVANT", "POSITIVE", "NOT_APPLICABLE")
    }
    assert orthogonal == (
        set(subject.GVE_EXACT4_EVENT_IDS_V1)
        | set(subject.LCY_EXACT4_EVENT_IDS_V1)
        | set(subject.ZERO_D8_EXACT4_EVENT_IDS_V1)
        | set(subject.TP2_EXACT4_EVENT_IDS_V1)
        | set(subject.SIX_OA_EXACT4_EVENT_IDS_V1)
    )
    assert len(orthogonal) == 20
    assert bundle["computation"].summary["orthogonal_task_negative_chemistry_positive"] == {
        "task_negative_chemistry_positive_population_count": 20,
        "gve_orthogonal_population_count": 4,
        "lcy_orthogonal_population_count": 4,
        "0d8_orthogonal_population_count": 4,
        "tp2_orthogonal_population_count": 4,
        "6oa_orthogonal_population_count": 4,
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20": True,
    }


def test_geometry_training_counts_and_boundary_stay_frozen(bundle) -> None:
    rows = bundle["computation"].rows
    assert sum(row["post_geometry_source_evidence_available"] == "true" for row in rows) == 867
    assert sum(row["post_geometry_sample_authoritative"] == "true" for row in rows) == 21
    assert sum(row["post_geometry_training_target_available"] == "true" for row in rows) == 17
    assert sum(row["pre_geometry_authoritative"] == "true" for row in rows) == 0
    assert sum(row["pre_geometry_training_target_available"] == "true" for row in rows) == 0
    assert sum(row["training_use_include"] == "true" for row in rows) == 68
    assert sum(row["future_training_admission_candidate"] == "true" for row in rows) == 51
    assert sum(row["formal_training_admitted"] == "true" for row in rows) == 5
    assert sum(row["current_runtime_model_usable"] == "true" for row in rows) == 17


def test_summary_blockers_and_6oa_source_composition(bundle) -> None:
    summary = bundle["computation"].summary
    blockers = summary["blockers"]
    assert blockers["population_sizes"] == {
        "chemistry_positive_population_count": 160,
        "training_include_population_count": 68,
    }
    assert blockers["chemistry_unresolved"] == {"all_1000": 750}
    assert blockers["pair_authority_absent"] == {"all_1000": 840, "within_chemistry_positive": 0}
    assert blockers["role_authority_absent"] == {"all_1000": 848, "within_chemistry_positive": 8}
    assert blockers["missing_split_authority"] == {
        "within_chemistry_positive": 119, "within_training_include": 43,
    }
    assert blockers["missing_tensor_integration"]["within_chemistry_positive"] == 119
    assert blockers["missing_tensor_integration"]["within_training_include"] == 39
    assert blockers["missing_tensor_integration"]["missing_source_composition"]["6OA"] == 4
    assert blockers["missing_POST_training_authority"] == {
        "within_chemistry_positive": 143, "within_training_include": 51,
    }
    assert blockers["missing_training_admission"] == {
        "within_chemistry_positive": 155, "within_training_include": 63,
    }
    assert blockers["feature_semantics_pending"] == {"within_chemistry_positive": 160}
    assert "6OA" not in summary["training_stage"]["future_candidate_source_composition"]


def test_next_pending_pyr_and_authority_boundary(bundle) -> None:
    summary = bundle["computation"].summary
    assert summary["human_review"]["completed_event_count"] == 171
    assert summary["human_review"]["completed_unit_count"] == 30
    assert summary["human_review"]["completed_negative_event_count"] == 48
    assert summary["human_review"]["completed_negative_unit_count"] == 10
    assert summary["human_review"]["unreviewed_event_count"] == 167
    assert summary["human_review"]["unreviewed_unit_count"] == 101
    top = summary["top_pending_review_units_by_event_yield"][0]
    assert top == {
        "rank": 1, "raw_priority_rank": 30,
        "review_unit_id": subject.NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "event_count": 4, "pdb_ids": ["1F8M"], "ligand_component_ids": ["PYR"],
        "full_coordinate_count": 4, "exact_pair_count": 4, "ccd_complete_count": 4,
        "post_source_evidence_count": 4, "current_review_status": "CURRENTLY_UNREVIEWED",
    }
    boundary = summary["authority_boundary"]
    assert boundary["6OA_REVIEW_COMPLETED"] is True
    assert boundary["6OA_RECONCILIATION_CONSUMED"] is True
    assert boundary["6OA_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH"] is True
    assert boundary["NEXT_REVIEW_STARTED"] is False
    assert boundary["QUEUE_REFRESH_PERFORMED"] is False
    assert boundary["PYR_REVIEW_STATE_CREATED"] is False
    assert boundary["READY_FOR_TRAINING"] is False
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"] is True
    assert boundary["feature_semantics_audit_performed"] is False


def test_semantic_lineage_exact186_without_collisions(bundle) -> None:
    bindings = bundle["computation"].semantic_source_bindings
    assert len(bindings) == 186
    assert tuple(bindings[:180]) == bundle["frozen"].semantic_source_bindings
    assert [item["artifact_role"] for item in bindings[180:]] == [
        item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1
    ]
    assert len({(item["path_namespace"], item["path"]) for item in bindings}) == 186
    predecessor_roles = {item["artifact_role"] for item in bindings[:180]}
    additive_roles = [item["artifact_role"] for item in bindings[180:]]
    assert len(additive_roles) == len(set(additive_roles))
    assert not predecessor_roles & set(additive_roles)
    materialized_manifest = json.loads(
        (
            REPO_ROOT / subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE
        ).read_text(encoding="utf-8")
    )
    assert materialized_manifest["6oa_reconciliation_artifact_validation_binding"][
        "computational_source"
    ] is False


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_event_id", subject.SIX_OA_EXACT4_EVENT_IDS_V1[0] + ":TAMPER"),
        ("current_global_status", "CURRENTLY_UNREVIEWED"),
        ("current_review_status", "COMPLETED_HUMAN_POSITIVE"),
        ("task_relevance_disposition", "RELEVANT"),
        ("chemistry_disposition", "NEGATIVE"),
        ("reactive_pair_sample_authoritative", "false"),
        ("role_partition_sample_authoritative", "false"),
        ("role_profile", "STRICT_LINKER_PRESENT_V1"),
        ("structurally_applicable_task_ids_json", "[0,1,2,3,4]"),
        ("structurally_applicable_task_ids_json", "[0,4]"),
        ("training_use_disposition", "INCLUDE"),
        ("training_use_include", "true"),
        ("human_training_excluded", "true"),
        ("future_training_admission_candidate", "true"),
        ("training_materialization_allowed_current_source", "true"),
        ("formal_training_admitted", "true"),
        ("reactive_pair_training_target_available", "true"),
        ("post_geometry_sample_authoritative", "true"),
        ("post_geometry_training_target_available", "true"),
        ("pre_geometry_authoritative", "true"),
        ("pre_geometry_training_target_available", "true"),
        ("current_runtime_model_usable", "true"),
    ),
)
def test_target_semantic_tampers_fail_closed(bundle, field: str, value: str) -> None:
    with pytest.raises(ERROR):
        _validate(bundle, _mutate(bundle, subject.SIX_OA_EXACT4_EVENT_IDS_V1[0], **{field: value}))


def test_non_target_row_change_fails_closed(bundle) -> None:
    with pytest.raises(ERROR):
        _validate(
            bundle,
            _mutate(bundle, subject.LCY_EXACT4_EVENT_IDS_V1[0], current_review_status="CURRENTLY_IN_PROGRESS"),
        )


def test_duplicate_6oa_event_fails_closed(bundle) -> None:
    rows = deepcopy(list(bundle["computation"].rows))
    targets = [row for row in rows if row["canonical_event_id"] in TARGET]
    targets[1]["canonical_event_id"] = targets[0]["canonical_event_id"]
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], rows=tuple(rows)))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_event_id", "TAMPER"),
        ("source_formal_generation_domain_decision", "IN_DOMAIN"),
        ("normalized_task_relevance_disposition", "RELEVANT"),
        ("chemistry_disposition", "NEGATIVE"),
        ("ligand_reactive_atom", "WRONG"),
        ("role_profile", "STRICT_LINKER_PRESENT_V1"),
        ("structurally_applicable_task_ids_json", "[0,1,2,3,4]"),
        ("formal_event_training_use_decision", "INCLUDE"),
        ("B3_present", "false"),
        ("sixth_task", "true"),
        ("pair_sample_authority", "false"),
        ("role_sample_authority", "false"),
        ("task_label_authority", "true"),
        ("event_task_label_rows_materialized", "true"),
        ("mask_tensor_targets_created", "true"),
        ("training_materialization_allowed", "true"),
        ("formal_training_admitted", "true"),
        ("POST_geometry_training_target_created", "true"),
        ("PRE_authority", "true"),
        ("READY_FOR_TRAINING", "true"),
        ("TRAINING_STARTED", "true"),
    ),
)
def test_matrix_semantic_tampers_fail_closed(bundle, field: str, value: str) -> None:
    rows = deepcopy(list(bundle["matrix"]))
    rows[0][field] = value
    with pytest.raises(ERROR):
        subject._validate_6oa_matrix_rows_v1(rows)


def test_summary_next_pending_and_binding_collision_fail_closed(bundle) -> None:
    summary = deepcopy(bundle["computation"].summary)
    summary["human_review"]["completed_event_count"] = 166
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))
    summary = deepcopy(bundle["computation"].summary)
    orthogonal = summary["orthogonal_task_negative_chemistry_positive"]
    orthogonal.pop(
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20"
    )
    orthogonal["task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_exact12"] = True
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))
    summary = deepcopy(bundle["computation"].summary)
    summary["top_pending_review_units_by_event_yield"][0]["raw_priority_rank"] = 29
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))
    bindings = list(deepcopy(bundle["computation"].semantic_source_bindings))
    bindings[-1]["path"] = bindings[-2]["path"]
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], semantic_source_bindings=tuple(bindings)))


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("top_pending_review_units_by_event_yield", 0, "review_unit_id"), subject.SIX_OA_REVIEW_UNIT_ID_V1),
        (("top_pending_review_units_by_event_yield", 0, "raw_priority_rank"), 29),
        (("authority_boundary", "QUEUE_REFRESH_PERFORMED"), True),
        (("authority_boundary", "NEXT_REVIEW_STARTED"), True),
        (("authority_boundary", "TRAINING_STARTED"), True),
    ),
)
def test_summary_queue_next_review_and_training_tampers_fail_closed(bundle, path, value) -> None:
    summary = deepcopy(bundle["computation"].summary)
    cursor = summary
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))


def test_published_6oa_source_digest_tampers_fail_closed(monkeypatch) -> None:
    spec = list(subject._ADDITIVE_SOURCE_SPECS_V1)
    matrix_index = next(
        index for index, item in enumerate(spec)
        if item[0] == "6OA_EVENT_TASK_LABEL_AVAILABILITY"
    )
    item = spec[matrix_index]
    spec[matrix_index] = (*item[:4], "0" * 64, item[5])
    monkeypatch.setattr(subject, "_ADDITIVE_SOURCE_SPECS_V1", tuple(spec))
    with pytest.raises(ValueError, match="FROZEN_SOURCE_BINDING_INVALID"):
        checker.verify_frozen_bindings_v1(REPO_ROOT)


def test_published_6oa_reconciliation_digest_tamper_fails_closed(monkeypatch) -> None:
    byte_count, _digest, executable = subject._SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1
    monkeypatch.setattr(
        subject, "_SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1",
        (byte_count, "0" * 64, executable),
    )
    with pytest.raises(ValueError, match="6OA_RECONCILIATION_ARTIFACT_BINDING_INVALID"):
        checker.verify_frozen_bindings_v1(REPO_ROOT)


def test_materialized_outputs_are_exact_and_double_build_is_deterministic(bundle) -> None:
    materialized = _materialized_exact3()
    once = subject._build_artifacts_from_computation_v1(REPO_ROOT, bundle["computation"])
    twice = subject._build_artifacts_from_computation_v1(REPO_ROOT, bundle["computation"])
    assert materialized == once == twice
    assert checker._sha(materialized[subject.CENSUS_FILE]) == checker.EXPECTED_CENSUS_SHA256
    assert checker._sha(materialized[subject.SUMMARY_FILE]) == checker.EXPECTED_SUMMARY_SHA256


def test_materialization_outside_authorized_root_fails(tmp_path: Path) -> None:
    with pytest.raises(ERROR, match="OUTPUT_DIRECTORY_NOT_AUTHORIZED"):
        subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1(
            REPO_ROOT, output_directory=tmp_path
        )


def test_lifecycle_candidate_tracked_and_fail_closed_simulations() -> None:
    simulations = checker.check_lifecycle_simulations_v1()
    assert all(simulations.values())
    assert simulations["branch_main_accepted"] is True
    assert simulations["branch_non_main_rejected"] is True
    assert simulations["committed_unpushed"] is True
    assert simulations["pushed_successor"] is True
    assert simulations["later_clean_descendant"] is True
    assert simulations["protected_history_rejected"] is True
    assert simulations["forbidden_history_rejected"] is True
    expected = list(subject.EXACT7_PATHS_V1)
    assert checker._classify_exact7_artifact_placement_v1([], expected) == "CANDIDATE_UNTRACKED"
    assert checker._classify_exact7_artifact_placement_v1(expected, []) == "TRACKED_CLEAN"
    with pytest.raises(ValueError):
        checker._classify_exact7_artifact_placement_v1(expected[:1], expected[1:])
    candidate = dict(
        branch="main", placement="CANDIDATE_UNTRACKED",
        head=checker.BASELINE_COMMIT, origin=checker.BASELINE_COMMIT,
        ahead=0, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=[],
    )
    assert checker._classify_repository_lifecycle_v1(**candidate) == "CANDIDATE_UNTRACKED"
    with pytest.raises(ValueError, match="BRANCH_NOT_MAIN"):
        checker._classify_repository_lifecycle_v1(**{**candidate, "branch": "feature/test"})
    committed = dict(
        branch="main", placement="TRACKED_CLEAN",
        head="successor", origin=checker.BASELINE_COMMIT, ahead=1, behind=0,
        baseline_is_ancestor_of_head=True, baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True, baseline_to_head_changed_paths=expected,
    )
    assert checker._classify_repository_lifecycle_v1(**committed) == "TRACKED_CLEAN"
    pushed = {**committed, "origin": "successor", "ahead": 0}
    assert checker._classify_repository_lifecycle_v1(**pushed) == "TRACKED_CLEAN"
    descendant = {**pushed, "head": "later-head", "origin": "later-head"}
    assert checker._classify_repository_lifecycle_v1(**descendant) == "TRACKED_CLEAN"
    for update in (
        {"tracked_modification_count": 1}, {"staged_count": 1}, {"behind": 1},
        {"baseline_is_ancestor_of_head": False}, {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False}, {"baseline_to_head_changed_paths": expected[:-1]},
        {"head": "impossible", "origin": "different", "ahead": 0},
    ):
        with pytest.raises(ValueError):
            checker._classify_repository_lifecycle_v1(**{**committed, **update})
    checker._validate_history_scope_v1(expected)
    with pytest.raises(ValueError, match="PROTECTED_HISTORY_PATH"):
        checker._validate_history_scope_v1((*expected, "data/raw/tamper.cif"))
    with pytest.raises(ValueError, match="FORBIDDEN_HISTORY_SUFFIX"):
        checker._validate_history_scope_v1((*expected, "artifacts/tamper.pyc"))


def test_checker_integration_accepts_candidate_or_tracked_clean(bundle, monkeypatch) -> None:
    real_comparator = checker._verify_materialized_output_bytes_v1
    comparisons: list[tuple[dict[str, bytes], dict[str, bytes]]] = []

    def spy(expected, observed) -> None:
        comparisons.append((dict(expected), dict(observed)))
        real_comparator(expected, observed)

    monkeypatch.setattr(checker, "_verify_materialized_output_bytes_v1", spy)
    monkeypatch.setattr(
        checker.subject,
        "_compute_components_v1",
        lambda _root: (
            bundle["computation"], bundle["frozen"],
            bundle["reconciliation"], bundle["matrix"],
        ),
    )
    report = checker.run_check_v1(REPO_ROOT)
    assert report["git"]["branch"] == "main"
    assert report["git"]["lifecycle"] in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    if report["git"]["lifecycle"] == "CANDIDATE_UNTRACKED":
        assert report["git"]["git_index_mode_checked"] is False
        assert report["git"]["git_index_entries"] == []
    else:
        assert report["git"]["git_index_mode_checked"] is True
        assert {item["mode"] for item in report["git"]["git_index_entries"]} == {"100644"}
    assert len(comparisons) == 2
    assert comparisons[0][0] == comparisons[0][1]
    assert comparisons[1][0] != comparisons[1][1]
    assert report["semantic_probes"]["raw_output_bytes"] == "MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED"
    assert "FAIL_CLOSED" not in set(report["semantic_probes"].values())
