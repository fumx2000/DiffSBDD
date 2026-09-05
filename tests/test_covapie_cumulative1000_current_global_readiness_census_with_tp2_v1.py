from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import pytest

from covalent_ext import covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_tp2_v1 as subject


REPO_ROOT = Path(__file__).resolve().parents[1]
ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithTP2Error
TARGET = set(subject.TP2_EXACT4_EVENT_IDS_V1)

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_with_tp2", REPO_ROOT / subject.CHECKER_RELATIVE
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
    return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_tp2_v1(
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
        "Cumulative1000CurrentGlobalReadinessCensusWithTP2Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_tp2_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_tp2_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_tp2_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_tp2_v1",
    )


def test_exact7_inventory_is_exact() -> None:
    records = checker.verify_exact7_inventory_v1(REPO_ROOT)
    assert [record["path"] for record in records] == list(subject.EXACT7_PATHS_V1)
    assert len(records) == 7
    assert all(record["mode"] == 0o644 for record in records)


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
    assert str(caught.value) == "MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED"


def test_raw_byte_probe_detects_noop_comparator(monkeypatch) -> None:
    exact3 = _materialized_exact3()
    monkeypatch.setattr(checker, "_verify_materialized_output_bytes_v1", lambda *_args: None)
    with pytest.raises(ValueError) as caught:
        checker._probe_materialized_raw_byte_rejection_v1(exact3)
    assert str(caught.value) == "RAW_BYTE_PROBE_DID_NOT_FAIL"


def test_predecessor_binding_and_unresolved_tp2_state(bundle) -> None:
    subject._assert_predecessor_tp2_state_v1(bundle["frozen"], REPO_ROOT)
    subject._verify_predecessor_bindings(
        REPO_ROOT, bundle["frozen"].semantic_source_bindings
    )
    assert len(bundle["frozen"].semantic_source_bindings) == 168
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


def test_reconciliation_exact24_139_and_review_summary(bundle) -> None:
    result = bundle["reconciliation"]
    assert len(result.source_bindings) == 24
    assert len(result.normalized_facts) == 139
    assert len({binding.stable_identity for binding in result.source_bindings}) == 24
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 119,
        "completed_positive_unit_count": 19,
        "completed_negative_event_count": 44,
        "completed_negative_unit_count": 9,
        "completed_total_event_count": 163,
        "completed_total_unit_count": 28,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 175,
        "unreviewed_unit_count": 103,
    }
    assert checker.reconciliation.SUCCESSOR_COVERAGE_SUMMARY == {
        "accepted_fact_count": 139,
        "accepted_review_unit_count": 24,
        "stable_source_identity_count": 24,
        "remaining_unreviewed_chemistry_event_count": 199,
        "remaining_unreviewed_review_unit_upper_bound": 107,
        "decision_category_distribution": {
            "chemistry_positive": 95,
            "chemistry_negative": 20,
            "task_domain_negative": 24,
            "task_domain_positive": 0,
        },
        "label_ready_event_count": 16,
        "training_mask_target_count": 0,
        "training_authority": False,
    }


def test_matrix_exact4_role_pair_pre_post_and_training_boundary(bundle) -> None:
    rows = subject._validate_tp2_matrix_rows_v1(bundle["matrix"])
    assert tuple(row["canonical_event_id"] for row in rows) == ingestion.EXPECTED_EVENT_IDS
    assert tuple(int(row["scaleup_rank"]) for row in rows) == (42, 43, 44, 45)
    for row in rows:
        assert row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
        assert row["task_relevance"] == "NOT_RELEVANT"
        assert row["chemistry"] == "POSITIVE"
        assert row["reactive_pair_human_authoritative"] == "true"
        assert (row["protein_reactive_atom"], row["ligand_reactive_atom"]) == ("SG", "S1")
        assert row["role_partition_human_authoritative"] == "true"
        assert row["role_profile"] == "STRICT_LINKER_PRESENT_V1"
        assert row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]"
        assert row["strict_profile_applicable_task_ids_json"] == "[0,1,2,3,4]"
        assert json.loads(row["warhead_atoms_json"]) == ["S1"]
        assert json.loads(row["linker_atoms_json"]) == ["C2", "C3", "N4"]
        assert json.loads(row["minimal_seed_atoms_json"]) == ["C5", "O21", "C6"]
        assert row["primary_anchor_atom_id"] == "C5"
        assert row["authoritative_task_labels_created"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
        assert row["training_mask_targets_available_now"] == "false"
        assert row["PRE_status"] == "PRE_REACTION_UNRESOLVED"
        assert row["POST_geometry_training_target_created"] == "false"


def test_schema_exact4_delta_and_overlay_sets(bundle) -> None:
    before = {row["canonical_event_id"]: row for row in bundle["frozen"].rows}
    after = {row["canonical_event_id"]: row for row in bundle["computation"].rows}
    assert len(after) == 1000
    assert len(subject.CENSUS_COLUMNS_V1) == 47
    assert {event for event in before if before[event] != after[event]} == TARGET
    assert sum(before[event] == after[event] for event in set(before) - TARGET) == 996
    assert len(subject._AUTHORIZED_TP2_OVERLAY_FIELDS_V1) == 19
    assert len(subject._AUTHORIZED_BUT_UNCHANGED_TP2_FIELDS_V1) == 3
    assert len(subject._ACTUAL_CHANGED_TP2_FIELDS_V1) == 16
    for event in TARGET:
        changed = {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event][field] != after[event][field]
        }
        unchanged = {
            field for field in subject._AUTHORIZED_TP2_OVERLAY_FIELDS_V1
            if before[event][field] == after[event][field]
        }
        assert changed == subject._ACTUAL_CHANGED_TP2_FIELDS_V1
        assert unchanged == subject._AUTHORIZED_BUT_UNCHANGED_TP2_FIELDS_V1


def test_target_projection_semantics(bundle) -> None:
    rows = [row for row in bundle["computation"].rows if row["canonical_event_id"] in TARGET]
    for row in rows:
        assert row["current_global_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert row["human_review_authority_source"] == subject.TP2_HUMAN_DECISION_SOURCE
        assert row["chemistry_disposition"] == "POSITIVE"
        assert row["task_relevance_disposition"] == "NOT_RELEVANT"
        assert row["training_use_disposition"] == "NOT_APPLICABLE"
        assert row["reactive_pair_sample_authoritative"] == "true"
        assert row["reactive_pair_training_target_available"] == "false"
        assert row["role_partition_sample_authoritative"] == "true"
        assert row["canonical_mask_structural_labels_available"] == "true"
        assert row["role_profile"] == "STRICT_LINKER_PRESENT_V1"
        assert row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]"
        assert row["formal_training_admitted"] == "false"
        assert row["current_runtime_model_usable"] == "false"
        assert row["training_materialization_allowed_current_source"] == "false"


def test_global_distributions_review_delta_and_authority_counts(bundle) -> None:
    rows = bundle["computation"].rows
    assert Counter(row["current_global_status"] for row in rows)["CURRENTLY_UNREVIEWED"] == 175
    assert Counter(row["current_global_status"] for row in rows)["COMPLETED_HUMAN_NEGATIVE"] == 74
    assert Counter(row["chemistry_disposition"] for row in rows) == Counter(
        {"POSITIVE": 152, "NOT_ESTABLISHED": 90, "UNRESOLVED": 758}
    )
    assert Counter(row["task_relevance_disposition"] for row in rows) == Counter(
        {"RELEVANT": 137, "NOT_RELEVANT": 106, "UNRESOLVED": 757}
    )
    assert Counter(row["training_use_disposition"] for row in rows) == Counter(
        {"INCLUDE": 64, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 106, "UNRESOLVED": 758}
    )
    assert sum(row["reactive_pair_sample_authoritative"] == "true" for row in rows) == 152
    assert sum(row["role_partition_sample_authoritative"] == "true" for row in rows) == 144
    assert sum(row["canonical_mask_structural_labels_available"] == "true" for row in rows) == 144


def test_exact5_b3_no_sixth_and_applicability_counts(bundle) -> None:
    assert len(subject.CANONICAL_EXACT5_V1) == 5
    assert subject.CANONICAL_EXACT5_V1[3] == (3, "scaffold_only", "B3")
    applicability = Counter()
    for row in bundle["computation"].rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    assert applicability == Counter({0: 144, 1: 56, 2: 56, 3: 144, 4: 144})
    assert bundle["computation"].summary["role"]["direct_profile_A_B3_C_count"] == 88
    assert bundle["computation"].summary["role"]["all_five_structurally_applicable_count"] == 56


def test_orthogonal_population_exact16(bundle) -> None:
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
        | TARGET
    )
    assert len(orthogonal) == 16
    assert bundle["computation"].summary["orthogonal_task_negative_chemistry_positive"] == {
        "task_negative_chemistry_positive_population_count": 16,
        "gve_orthogonal_population_count": 4,
        "lcy_orthogonal_population_count": 4,
        "0d8_orthogonal_population_count": 4,
        "tp2_orthogonal_population_count": 4,
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_exact16": True,
    }


def test_geometry_training_counts_and_boundary_stay_frozen(bundle) -> None:
    rows = bundle["computation"].rows
    assert sum(row["post_geometry_source_evidence_available"] == "true" for row in rows) == 867
    assert sum(row["post_geometry_sample_authoritative"] == "true" for row in rows) == 21
    assert sum(row["post_geometry_training_target_available"] == "true" for row in rows) == 17
    assert sum(row["pre_geometry_authoritative"] == "true" for row in rows) == 0
    assert sum(row["pre_geometry_training_target_available"] == "true" for row in rows) == 0
    assert sum(row["training_use_include"] == "true" for row in rows) == 64
    assert sum(row["future_training_admission_candidate"] == "true" for row in rows) == 47
    assert sum(row["formal_training_admitted"] == "true" for row in rows) == 5
    assert sum(row["current_runtime_model_usable"] == "true" for row in rows) == 17


def test_summary_blockers_and_tp2_source_composition(bundle) -> None:
    summary = bundle["computation"].summary
    blockers = summary["blockers"]
    assert blockers["population_sizes"] == {
        "chemistry_positive_population_count": 152,
        "training_include_population_count": 64,
    }
    assert blockers["chemistry_unresolved"] == {"all_1000": 758}
    assert blockers["pair_authority_absent"] == {"all_1000": 848, "within_chemistry_positive": 0}
    assert blockers["role_authority_absent"] == {"all_1000": 856, "within_chemistry_positive": 8}
    assert blockers["missing_split_authority"] == {
        "within_chemistry_positive": 111, "within_training_include": 39,
    }
    assert blockers["missing_tensor_integration"]["within_chemistry_positive"] == 111
    assert blockers["missing_tensor_integration"]["within_training_include"] == 35
    assert blockers["missing_tensor_integration"]["missing_source_composition"]["TP2"] == 4
    assert blockers["missing_POST_training_authority"] == {
        "within_chemistry_positive": 135, "within_training_include": 47,
    }
    assert blockers["missing_training_admission"] == {
        "within_chemistry_positive": 147, "within_training_include": 59,
    }
    assert blockers["feature_semantics_pending"] == {"within_chemistry_positive": 152}


def test_next_pending_nwj_and_authority_boundary(bundle) -> None:
    summary = bundle["computation"].summary
    assert summary["human_review"]["completed_event_count"] == 163
    assert summary["human_review"]["completed_unit_count"] == 28
    assert summary["human_review"]["unreviewed_event_count"] == 175
    assert summary["human_review"]["unreviewed_unit_count"] == 103
    top = summary["top_pending_review_units_by_event_yield"][0]
    assert top == {
        "rank": 1, "raw_priority_rank": 28,
        "review_unit_id": subject.NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "event_count": 4, "pdb_ids": ["4CM5"], "ligand_component_ids": ["NWJ"],
        "full_coordinate_count": 4, "exact_pair_count": 4, "ccd_complete_count": 4,
        "post_source_evidence_count": 4, "current_review_status": "CURRENTLY_UNREVIEWED",
    }
    boundary = summary["authority_boundary"]
    assert boundary["TP2_REVIEW_COMPLETED"] is True
    assert boundary["TP2_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH"] is True
    assert boundary["NEXT_REVIEW_STARTED"] is False
    assert boundary["QUEUE_REFRESH"] is False
    assert boundary["READY_FOR_TRAINING"] is False
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"] is True
    assert boundary["feature_semantics_audit_performed"] is False


def test_semantic_lineage_exact174_without_collisions(bundle) -> None:
    bindings = bundle["computation"].semantic_source_bindings
    assert len(bindings) == 174
    assert tuple(bindings[:168]) == bundle["frozen"].semantic_source_bindings
    assert [item["artifact_role"] for item in bindings[168:]] == [
        item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1
    ]
    assert len({(item["path_namespace"], item["path"]) for item in bindings}) == 174
    predecessor_roles = {item["artifact_role"] for item in bindings[:168]}
    additive_roles = [item["artifact_role"] for item in bindings[168:]]
    assert len(additive_roles) == len(set(additive_roles))
    assert not predecessor_roles & set(additive_roles)
    materialized_manifest = json.loads(
        (
            REPO_ROOT / subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE
        ).read_text(encoding="utf-8")
    )
    assert materialized_manifest["tp2_reconciliation_artifact_validation_binding"][
        "computational_source"
    ] is False


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_event_id", subject.TP2_EXACT4_EVENT_IDS_V1[0] + ":TAMPER"),
        ("task_relevance_disposition", "RELEVANT"),
        ("chemistry_disposition", "NEGATIVE"),
        ("reactive_pair_sample_authoritative", "false"),
        ("role_partition_sample_authoritative", "false"),
        ("role_profile", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        ("structurally_applicable_task_ids_json", "[0,4]"),
        ("training_use_disposition", "INCLUDE"),
        ("training_use_include", "true"),
        ("formal_training_admitted", "true"),
        ("reactive_pair_training_target_available", "true"),
        ("post_geometry_training_target_available", "true"),
        ("pre_geometry_authoritative", "true"),
    ),
)
def test_target_semantic_tampers_fail_closed(bundle, field: str, value: str) -> None:
    with pytest.raises(ERROR):
        _validate(bundle, _mutate(bundle, subject.TP2_EXACT4_EVENT_IDS_V1[0], **{field: value}))


def test_non_target_row_change_fails_closed(bundle) -> None:
    with pytest.raises(ERROR):
        _validate(
            bundle,
            _mutate(bundle, subject.LCY_EXACT4_EVENT_IDS_V1[0], current_review_status="CURRENTLY_IN_PROGRESS"),
        )


def test_duplicate_tp2_event_fails_closed(bundle) -> None:
    rows = deepcopy(list(bundle["computation"].rows))
    targets = [row for row in rows if row["canonical_event_id"] in TARGET]
    targets[1]["canonical_event_id"] = targets[0]["canonical_event_id"]
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], rows=tuple(rows)))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_event_id", "TAMPER"),
        ("role_partition_human_authoritative", "false"),
        ("role_profile", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        ("strict_profile_applicable_task_ids_json", "[0,3,4]"),
        ("chemistry", "NEGATIVE"),
        ("formal_event_training_use_decision", "INCLUDE"),
        ("B3_present", "false"),
        ("sixth_task", "true"),
        ("training_mask_targets_available_now", "true"),
    ),
)
def test_matrix_semantic_tampers_fail_closed(bundle, field: str, value: str) -> None:
    rows = deepcopy(list(bundle["matrix"]))
    rows[0][field] = value
    with pytest.raises(ERROR):
        subject._validate_tp2_matrix_rows_v1(rows)


def test_summary_next_pending_and_binding_collision_fail_closed(bundle) -> None:
    summary = deepcopy(bundle["computation"].summary)
    summary["human_review"]["completed_event_count"] = 154
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))
    summary = deepcopy(bundle["computation"].summary)
    orthogonal = summary["orthogonal_task_negative_chemistry_positive"]
    orthogonal.pop(
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_exact16"
    )
    orthogonal["task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_exact12"] = True
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))
    summary = deepcopy(bundle["computation"].summary)
    summary["top_pending_review_units_by_event_yield"][0]["raw_priority_rank"] = 27
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], summary=summary))
    bindings = list(deepcopy(bundle["computation"].semantic_source_bindings))
    bindings[-1]["path"] = bindings[-2]["path"]
    with pytest.raises(ERROR):
        _validate(bundle, replace(bundle["computation"], semantic_source_bindings=tuple(bindings)))


def test_materialized_outputs_are_exact_and_double_build_is_deterministic(bundle) -> None:
    materialized = _materialized_exact3()
    once = subject._build_artifacts_from_computation_v1(REPO_ROOT, bundle["computation"])
    twice = subject._build_artifacts_from_computation_v1(REPO_ROOT, bundle["computation"])
    assert materialized == once == twice
    assert checker._sha(materialized[subject.CENSUS_FILE]) == checker.EXPECTED_CENSUS_SHA256
    assert checker._sha(materialized[subject.SUMMARY_FILE]) == checker.EXPECTED_SUMMARY_SHA256


def test_materialization_outside_authorized_root_fails(tmp_path: Path) -> None:
    with pytest.raises(ERROR, match="OUTPUT_DIRECTORY_NOT_AUTHORIZED"):
        subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_tp2_v1(
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
    assert len(comparisons) == 2
    assert comparisons[0][0] == comparisons[0][1]
    assert comparisons[1][0] != comparisons[1][1]
    assert report["semantic_probes"]["raw_output_bytes"] is True
