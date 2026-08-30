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

from covalent_ext import covapie_completed_human_decision_reconciliation_with_2a2_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_f24_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_2a2_v1 as subject  # noqa: E402
from covalent_ext import covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWith2A2Error
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1",
    REPO / "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="session")
def frozen():
    return predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_f24_v1(
        REPO
    )


@pytest.fixture(scope="session")
def computation():
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
        REPO
    )


@pytest.fixture(scope="session")
def matrix_rows():
    payload = (REPO / subject.TWO_A2_EVENT_MATRIX_RELATIVE).read_bytes()
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


def _two_a2_predicate(row: dict[str, str]) -> bool:
    return row["canonical_event_id"] == subject.TWO_A2_EXACT4_EVENT_IDS_V1[0]


def test_public_api_is_minimal_and_reuses_predecessor_schema() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWith2A2Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1",
    )
    assert subject.CENSUS_COLUMNS_V1 is predecessor.CENSUS_COLUMNS_V1
    assert subject.CANONICAL_EXACT5_V1 is predecessor.CANONICAL_EXACT5_V1
    assert not {
        "chemical_warhead_atoms_json", "warhead_role_atoms_json", "D6",
        "beta_lactone_core",
    } & set(subject.CENSUS_COLUMNS_V1)


def test_frozen_predecessor_and_two_a2_bindings_are_exact() -> None:
    verified = checker.verify_frozen_bindings_v1(REPO)
    assert len(verified) == 7
    assert [item["sha256"] for item in verified] == [
        item[4] for item in checker.FROZEN_BINDINGS
    ]


def test_happy_path_source_derived_exact1000_and_validator(computation, frozen) -> None:
    assert type(computation) is subject.base.Cumulative1000CurrentGlobalReadinessComputationV1
    assert len(computation.rows) == 1000
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
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
        subject.predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_f24_v1
    )
    original_reconciliation = (
        subject.two_a2_reconciliation.reconcile_real_completed_human_decisions_with_2a2_v1
    )
    original_build = subject.two_a2_ingestion.build_artifacts_v1
    original_validate = subject.two_a2_ingestion.validate_completed_decision_projection_v1

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
        "compute_covapie_cumulative1000_current_global_readiness_census_with_f24_v1",
        wrapped_predecessor,
    )
    monkeypatch.setattr(
        subject.two_a2_reconciliation,
        "reconcile_real_completed_human_decisions_with_2a2_v1",
        wrapped_reconciliation,
    )
    monkeypatch.setattr(subject.two_a2_ingestion, "build_artifacts_v1", wrapped_build)
    monkeypatch.setattr(
        subject.two_a2_ingestion,
        "validate_completed_decision_projection_v1",
        wrapped_validate,
    )
    subject.compute_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
        REPO
    )
    assert calls == {
        "predecessor": 1,
        "reconciliation": 2,
        "ingestion_build": 1,
        "ingestion_validate": 1,
    }


def test_exact4_identity_ranks_pdbs_and_cys148(matrix_rows) -> None:
    validated = subject._validate_two_a2_matrix_rows_v1(matrix_rows)
    assert tuple(row["canonical_event_id"] for row in validated) == (
        subject.TWO_A2_EXACT4_EVENT_IDS_V1
    )
    assert tuple(int(row["scaleup_rank"]) for row in validated) == (
        507, 508, 509, 510,
    )
    assert Counter(row["pdb_id"] for row in validated) == Counter(
        {"3ORZ": 4}
    )
    assert {row["cys_residue_id"] for row in validated} == {"CYS:148-"}


def test_two_a2_matrix_d1_d5_role_chemical_and_exact5_semantics(matrix_rows) -> None:
    rows = subject._validate_two_a2_matrix_rows_v1(matrix_rows)
    for row in rows:
        tasks = json.loads(row["canonical_task_applicability_json"])
        assert row["human_task_relevance_decision"] == "RELEVANT"
        assert row["chemistry_known_positive"] == "true"
        assert row["protein_reactive_atom"] == "SG"
        assert row["ligand_reactive_atom"] == "SD"
        assert row["selected_role_candidate_index_0based"] == "4"
        assert row["role_profile"] == "STRICT_LINKER_PRESENT_V1"
        assert json.loads(row["warhead_atoms_json"]) == ["SD"]
        assert json.loads(row["chemical_warhead_atoms_json"]) is None
        assert json.loads(row["linker_atoms_json"]) == [
            "C1", "C15", "C16", "C17", "O18",
        ]
        assert json.loads(row["scaffold_atoms_json"]) == list(ingestion.SCAFFOLD_ROLE)
        assert [item["task_id"] for item in tasks] == [0, 1, 2, 3, 4]
        assert [
            item["task_id"] for item in tasks if item["structurally_applicable"]
        ] == [0, 1, 2, 3, 4]
        assert tasks[3]["semantic_long_name"] == "scaffold_only"
        assert row["formal_event_training_use_decision"] == "EXCLUDE_FROM_TRAINING_ONLY"
        assert row["human_training_excluded"] == "true"
        assert row["candidate_for_future_training_admission"] == "false"
        assert row["training_admitted"] == "false"
        assert row["minimal_seed_authority_available"] == "false"
        assert row["minimal_seed_atom_ids_json"] == "null"
        assert row["complete_PRE_disulfide_reagent_authority_available"] == "false"
        assert row["PRE_topology_authority_available"] == "false"
        assert row["PRE_geometry_authority_available"] == "false"
        assert row["POST_source_evidence_available"] == "true"
        assert row["POST_geometry_training_authority_available"] == "false"
        assert row["future_training_candidate_derived_by_ingestion"] == "false"
        assert row["training_admission_created"] == "false"


def test_exact4_delta_and_996_dict_equal(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == set(subject.TWO_A2_EXACT4_EVENT_IDS_V1)
    assert len(changed) == 4
    assert len(set(before) - changed) == 996
    assert all(before[event_id] == after[event_id] for event_id in set(before) - changed)
    assert all(
        {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        } == subject._AUTHORIZED_TWO_A2_OVERLAY_FIELDS_V1
        for event_id in changed
    )
    assert len(subject._AUTHORIZED_TWO_A2_OVERLAY_FIELDS_V1) == 17
    assert "human_training_excluded" in subject._AUTHORIZED_TWO_A2_OVERLAY_FIELDS_V1
    assert "training_use_include" not in subject._AUTHORIZED_TWO_A2_OVERLAY_FIELDS_V1
    assert "future_training_admission_candidate" not in subject._AUTHORIZED_TWO_A2_OVERLAY_FIELDS_V1


def test_predecessor_exact5_state_is_proven(frozen) -> None:
    subject._assert_predecessor_two_a2_state_v1(frozen)
    rows = [
        row for row in frozen.rows
        if row["canonical_event_id"] in set(subject.TWO_A2_EXACT4_EVENT_IDS_V1)
    ]
    assert all(row["current_review_status"] == "CURRENTLY_UNREVIEWED" for row in rows)
    assert all(row["chemistry_disposition"] == "UNRESOLVED" for row in rows)
    assert all(row["reactive_pair_raw_structural_evidence"] == "true" for row in rows)


def test_two_a2_refreshed_semantics_and_training_prohibitions(computation) -> None:
    rows = [
        row for row in computation.rows
        if row["canonical_event_id"] in set(subject.TWO_A2_EXACT4_EVENT_IDS_V1)
    ]
    assert len(rows) == 4
    assert all(
        row["current_global_status"] == "COMPLETED_HUMAN_POSITIVE"
        and row["human_review_completed"] == "true"
        and row["human_review_authority_source"] == subject.TWO_A2_HUMAN_DECISION_SOURCE
        and row["chemistry_disposition"] == "POSITIVE"
        and row["chemistry_authority_source"] == subject.TWO_A2_EVENT_MATRIX_SOURCE
        and row["positive_authority_source"] == subject.TWO_A2_EVENT_MATRIX_SOURCE
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


def test_two_a2_structural_fields_are_unchanged(computation, frozen) -> None:
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in computation.rows}
    assert all(
        before[event_id][field] == after[event_id][field]
        for event_id in subject.TWO_A2_EXACT4_EVENT_IDS_V1
        for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
    )
    for event_id in subject.TWO_A2_EXACT4_EVENT_IDS_V1:
        assert all(
            after[event_id][field] == value
            for field, value in subject._EXPECTED_TWO_A2_STRUCTURAL_CELLS_V1.items()
        )


def test_exact_set_algebra_keeps_include_future_admission_runtime(computation, frozen) -> None:
    before = subject._sets_for_algebra_v1(frozen.rows)
    after = subject._sets_for_algebra_v1(computation.rows)
    two_a2 = set(subject.TWO_A2_EXACT4_EVENT_IDS_V1)
    assert after["chemistry_positive"] == before["chemistry_positive"] | two_a2
    assert after["chemistry_unresolved"] == before["chemistry_unresolved"] - two_a2
    assert after["task_relevant"] == before["task_relevant"] | two_a2
    assert after["task_unresolved"] == before["task_unresolved"] - two_a2
    assert after["training_include"] == before["training_include"]
    assert after["training_exclude"] == before["training_exclude"] | two_a2
    assert after["future_candidate"] == before["future_candidate"]
    assert after["training_unresolved"] == before["training_unresolved"] - two_a2
    for key in (
        "chemistry_negative", "chemistry_not_established", "task_not_relevant",
        "training_not_applicable",
        "formal_split", "formal_admitted", "runtime_usable",
    ):
        assert after[key] == before[key]


def test_global_chemistry_task_training_and_status_counts(computation) -> None:
    assert Counter(row["chemistry_disposition"] for row in computation.rows) == Counter(
        {"POSITIVE": 112, "NOT_ESTABLISHED": 86, "UNRESOLVED": 802}
    )
    assert Counter(
        row["task_relevance_disposition"] for row in computation.rows
    ) == Counter({"RELEVANT": 113, "NOT_RELEVANT": 86, "UNRESOLVED": 801})
    assert Counter(row["training_use_disposition"] for row in computation.rows) == Counter(
        {
            "INCLUDE": 44, "EXCLUDE_FROM_TRAINING_ONLY": 68,
            "NOT_APPLICABLE": 86, "UNRESOLVED": 802,
        }
    )
    assert Counter(row["current_global_status"] for row in computation.rows) == Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    )


def test_human_review_counts_are_distinct_from_global_negative(computation) -> None:
    assert computation.summary["human_review"] == {
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 119,
        "completed_unit_count": 17,
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 219,
        "current_pending_review_unit_count": 114,
    }
    assert computation.summary["global_status_distribution"]["counts"][
        "COMPLETED_HUMAN_NEGATIVE"
    ] == 54


def test_pair_role_exact5_geometry_and_training_counts(computation) -> None:
    summary = computation.summary
    assert summary["reactive_pair"]["sample_level_authoritative_pair_count"] == 112
    assert summary["reactive_pair"]["published_model_bound_target_constructible_count"] == 41
    assert summary["reactive_pair"]["two_a2_sample_authority_contribution_count"] == 4
    assert summary["reactive_pair"]["two_a2_model_bound_target_contribution_count"] == 0
    assert summary["role"]["role_profile_counts"] == {
        "STRICT_LINKER_PRESENT_V1": 52,
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 60,
        "other": 0,
    }
    assert summary["role"]["unknown_role_row_count"] == 888
    assert [
        task["structurally_applicable_authoritative_role_count"]
        for task in summary["canonical_exact5"]["tasks"]
    ] == [112, 52, 52, 112, 112]
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
    assert summary["training_stage"]["future_training_admission_candidate_count"] == 27
    assert summary["training_stage"]["formal_training_admitted_count"] == 5
    assert summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_blocker_counts_are_exact_and_nonexclusive(computation) -> None:
    checker.independently_verify_counts_v1(list(computation.rows), computation.summary)
    blockers = computation.summary["blockers"]
    assert blockers["non_exclusive_counts_must_not_be_summed"] is True
    assert blockers["human_training_exclusion"] == {"within_positive_112": 68}
    assert blockers["missing_split_authority"] == {
        "within_positive_112": 71, "within_include_44": 19,
    }
    assert blockers["missing_tensor_integration"] == {
        "within_positive_112": 71,
        "within_include_44": 15,
        "all_missing_are_training_excluded_population": False,
        "missing_source_composition": {
            "G3H": 8, "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8,
            "YUN": 7, "NEQ": 6, "CHT": 5, "OZJ": 4, "F24": 4, "2A2": 4,
        },
    }
    assert blockers["missing_POST_training_authority"] == {
        "within_positive_112": 95, "within_include_44": 27,
    }
    assert blockers["missing_training_admission"] == {
        "within_positive_112": 107, "within_include_44": 39,
    }
    assert blockers["feature_semantics_pending"] == {"within_positive_112": 112}
    assert blockers["pair_authority_absent"] == {
        "all_1000": 888, "within_positive_112": 0,
    }
    assert blockers["role_authority_absent"] == {
        "all_1000": 888, "within_positive_112": 0,
    }


def test_refresh_delta_is_exact(computation) -> None:
    assert computation.summary["refresh_delta"] == {
        "frozen_predecessor_positive_count": 108,
        "two_a2_exact4_delta_count": 4,
        "refreshed_positive_count": 112,
        "frozen_predecessor_training_include_count": 44,
        "refreshed_training_include_count": 44,
        "frozen_predecessor_training_exclude_count": 64,
        "refreshed_training_exclude_count": 68,
        "frozen_predecessor_future_candidate_count": 27,
        "refreshed_future_candidate_count": 27,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "derived_refresh_not_new_authority": True,
    }


def test_reconciliation_and_dynamic_pending_queue_head(computation) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_2a2_v1(REPO)
    expected = checker.independently_compute_top10_v1(REPO, result.reconciled_rows)
    assert computation.summary["top_pending_review_units_by_event_yield"] == expected
    assert expected[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295"
    assert expected[0]["ligand_component_ids"] == ["I12"]
    assert expected[0]["pdb_ids"] == ["1WOF", "2AMP"]
    assert expected[0]["rank"] == 1
    assert expected[0]["raw_priority_rank"] == 17
    assert expected[0]["event_count"] == 4
    assert all(item["ligand_component_ids"] != ["2A2"] for item in expected)


def test_authority_boundary_and_non_actions(computation) -> None:
    boundary = computation.summary["authority_boundary"]
    assert boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is True
    assert boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is True
    assert boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is False
    assert boundary["READY_FOR_FORMAL_TRAINING"] is False
    assert boundary["HUMAN_REVIEW_DECISION_NOT_PERFORMED"] is True
    assert boundary["NEXT_RECOMMENDED_MAINLINE"] == "SOURCE_BINDING_FILESYSTEM_MODE_AUTHORITY_TECH_DEBT_V2"
    assert boundary["next_priority_review_ligand"] == "I12"
    assert boundary["next_priority_review_current_pending_rank"] == 1
    assert boundary["next_priority_review_raw_priority_rank"] == 17
    assert boundary["READY_FOR_TRAINING"] is False
    assert boundary["training_materialization_allowed"] is False
    assert boundary["future_candidate_is_not_training_admission"] is True
    assert boundary["next_review_started"] is False
    assert boundary["I12_REVIEW_STARTED"] is False
    assert boundary["training_started"] is False
    assert boundary["FILESYSTEM_MODE_AUTHORITY_TECH_DEBT"] == "PENDING_DEDICATED_V2_CLEANUP_AFTER_2A2_CENSUS_PUBLICATION"
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
    assert len(computation.semantic_source_bindings) == 108


def test_no_direct_formal_parse_binding_or_exact_source_mode_authority(computation) -> None:
    text = Path(subject.__file__).read_text(encoding="utf-8")
    assert "load_frozen_formal_decision_v1" not in text
    assert "FORMAL_BINDINGS" not in text
    assert all(item[2] == "repository_relative" for item in subject._ADDITIVE_SOURCE_SPECS_V1)
    assert all("FORMAL" not in item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1)
    assert all(
        set(binding) == {
            "artifact_role", "path", "path_namespace", "byte_count", "sha256"
        }
        for binding in computation.semantic_source_bindings
    )


def test_exact_posix_mode_cannot_be_added_to_semantic_binding(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings[-1]["mode"] = "0644"
    with pytest.raises(ERROR, match="SEMANTIC_SOURCE_BINDING_SCHEMA_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
            replace(computation, semantic_source_bindings=tuple(bindings)),
            predecessor_computation=frozen,
        )


def test_exact3_build_materialization_and_two_directory_determinism(tmp_path: Path) -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
        REPO
    )
    one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
        REPO, tmp_path / "one"
    )
    two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
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
    assert result["changed_event_count"] == 4
    assert result["unchanged_event_count"] == 996
    assert result["refreshed_positive_count"] == 112
    assert result["task_relevant_count"] == 113
    assert result["training_include_count"] == 44
    assert result["training_exclude_count"] == 68
    assert result["future_candidate_count"] == 27
    assert result["formal_training_admitted_count"] == 5
    assert result["current_runtime_model_usable_count"] == 17
    assert result["semantic_source_binding_count"] == 108
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


def test_predecessor_two_a2_row_not_unreviewed_rejected(frozen) -> None:
    rows = [dict(row) for row in frozen.rows]
    index = next(
        i for i, row in enumerate(rows)
        if row["canonical_event_id"] == subject.TWO_A2_EXACT4_EVENT_IDS_V1[0]
    )
    rows[index]["current_review_status"] = "CURRENTLY_IN_PROGRESS"
    with pytest.raises(ERROR):
        subject._assert_predecessor_two_a2_state_v1(replace(frozen, rows=tuple(rows)))


def test_predecessor_two_a2_wrong_review_unit_rejected(frozen) -> None:
    rows = [dict(row) for row in frozen.rows]
    index = next(
        i for i, row in enumerate(rows)
        if row["canonical_event_id"] == subject.TWO_A2_EXACT4_EVENT_IDS_V1[0]
    )
    rows[index]["review_unit_id"] = "WRONG_UNIT"
    with pytest.raises(ERROR):
        subject._assert_predecessor_two_a2_state_v1(replace(frozen, rows=tuple(rows)))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("current_global_status", "COMPLETED_HUMAN_POSITIVE"),
        ("chemistry_disposition", "POSITIVE"),
        ("role_partition_sample_authoritative", "true"),
        ("reactive_pair_sample_authoritative", "true"),
    ],
)
def test_predecessor_two_a2_already_authoritative_rejected(frozen, field, value) -> None:
    rows = [dict(row) for row in frozen.rows]
    index = next(
        i for i, row in enumerate(rows)
        if row["canonical_event_id"] == subject.TWO_A2_EXACT4_EVENT_IDS_V1[0]
    )
    rows[index][field] = value
    with pytest.raises(ERROR):
        subject._assert_predecessor_two_a2_state_v1(replace(frozen, rows=tuple(rows)))


def test_non_two_a2_output_row_change_rejected(computation, frozen) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["canonical_event_id"] not in set(subject.TWO_A2_EXACT4_EVENT_IDS_V1),
        current_global_status="CURRENTLY_IN_PROGRESS",
    )
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
            mutated, predecessor_computation=frozen
        )


@pytest.mark.parametrize(
    "label",
    [
        "PREDECESSOR_F24_CENSUS_OWNER",
        "PREDECESSOR_F24_MATERIALIZED_CENSUS",
        "PREDECESSOR_F24_MATERIALIZED_SUMMARY",
        "PREDECESSOR_F24_MANIFEST",
        "TWO_A2_RECONCILIATION_SUCCESSOR",
        "TWO_A2_INGESTION_OWNER",
        "TWO_A2_EVENT_TASK_LABEL_AVAILABILITY",
    ],
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
    result = reconciliation.reconcile_real_completed_human_decisions_with_2a2_v1(REPO)
    summary = dict(result.review_summary)
    summary["completed_positive_event_count"] = 82
    monkeypatch.setattr(
        subject.two_a2_reconciliation,
        "reconcile_real_completed_human_decisions_with_2a2_v1",
        lambda root: replace(result, review_summary=summary),
    )
    with pytest.raises(ERROR):
        subject._validate_two_a2_reconciliation_v1(REPO)


def test_matrix_must_be_source_derived(monkeypatch) -> None:
    built = ingestion.build_artifacts_v1(REPO)
    drifted = dict(built)
    drifted[ingestion.MATRIX] += b"x"
    monkeypatch.setattr(subject.two_a2_ingestion, "build_artifacts_v1", lambda root: drifted)
    with pytest.raises(ERROR):
        subject._load_and_validate_two_a2_event_matrix_v1(REPO)


def test_raw_priority_queue_byte_drift_rejected(monkeypatch) -> None:
    result = reconciliation.reconcile_real_completed_human_decisions_with_2a2_v1(REPO)
    original = subject._read_regular_file

    def drift(path, label):
        payload = original(path, label)
        return payload + b"x" if label == "PRIORITY_QUEUE" else payload

    monkeypatch.setattr(subject, "_read_regular_file", drift)
    with pytest.raises(ERROR):
        subject._top_pending_review_units_v1(REPO, result)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra"])
def test_matrix_event_coverage_mutations_rejected(matrix_rows, mutation) -> None:
    rows = [dict(row) for row in matrix_rows]
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[1]["canonical_event_id"] = rows[0]["canonical_event_id"]
    else:
        extra = dict(rows[-1])
        extra["canonical_event_id"] = "EXTRA_TWO_A2_EVENT"
        extra["scaleup_rank"] = "674"
        rows.append(extra)
    with pytest.raises(ERROR):
        subject._validate_two_a2_matrix_rows_v1(rows)


@pytest.mark.parametrize(
    "updates",
    [
        {"scaleup_rank": "506"},
        {"pdb_id": "9ZZZ"},
        {"cys_residue_id": "CYS:112-"},
        {"protein_chain_or_asym": "Z"},
        {"ligand_chain_or_asym": "Z"},
        {"protein_reactive_atom": "CA"},
        {"ligand_reactive_atom": "C7"},
        {"human_task_relevance_decision": "NOT_RELEVANT"},
        {"chemistry_known_positive": "false"},
        {"formal_event_training_use_decision": "INCLUDE"},
        {"human_training_excluded": "false"},
        {"candidate_for_future_training_admission": "true"},
        {"training_admitted": "true"},
        {"role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"},
        {"selected_role_candidate_index_0based": "3"},
        {"strict_profile_applicable_task_ids_json": "[0,3,4]"},
        {"warhead_atoms_json": "[\"SD\",\"C1\"]"},
        {"chemical_warhead_atoms_json": "[\"SD\"]"},
        {"PRE_topology_authority_available": "true"},
        {"POST_geometry_training_authority_available": "true"},
        {"minimal_seed_authority_available": "true"},
        {"current_runtime_model_usable": "true"},
    ],
)
def test_matrix_semantic_mutations_rejected(matrix_rows, updates) -> None:
    rows = [dict(row) for row in matrix_rows]
    rows[0].update(updates)
    with pytest.raises(ERROR):
        subject._validate_two_a2_matrix_rows_v1(rows)


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
        subject._validate_two_a2_matrix_rows_v1(rows)


@pytest.mark.parametrize(
    "updates",
    [
        {"task_relevance_disposition": "NOT_RELEVANT"},
        {"chemistry_disposition": "NEGATIVE"},
        {"training_use_disposition": "INCLUDE"},
        {"human_training_excluded": "false"},
        {"training_use_include": "true"},
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
        {"raw_structure_available": "false"},
    ],
)
def test_refreshed_row_semantic_mutations_rejected(computation, frozen, updates) -> None:
    mutated = _mutate_row(computation, _two_a2_predicate, **updates)
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
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
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
            replace(computation, summary=summary), predecessor_computation=frozen
        )


def test_source_binding_sha_drift_rejected(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings[-1]["sha256"] = "0" * 64
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
            replace(computation, semantic_source_bindings=tuple(bindings)),
            predecessor_computation=frozen,
        )


def test_duplicate_semantic_binding_rejected(computation, frozen) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings.append(dict(bindings[-1]))
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_2a2_v1(
            replace(computation, semantic_source_bindings=tuple(bindings)),
            predecessor_computation=frozen,
        )


def test_materialized_csv_byte_mutation_rejected_by_independent_checker() -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
        REPO
    )
    text = built[subject.CENSUS_FILE].decode("utf-8")
    mutated = text.replace("COMPLETED_HUMAN_POSITIVE", "CURRENTLY_UNREVIEWED", 1).encode()
    rows = checker._parse_census(mutated)
    with pytest.raises(ValueError):
        checker.independently_verify_delta_v1(REPO, rows)


def test_summary_mutation_rejected_by_independent_checker(computation) -> None:
    summary = deepcopy(computation.summary)
    summary["blockers"]["missing_tensor_integration"]["within_positive_112"] = 70
    with pytest.raises(ValueError):
        checker.independently_verify_counts_v1(list(computation.rows), summary)


@pytest.mark.parametrize("stale_key", ["within_positive_108", "within_include_40"])
def test_stale_predecessor_blocker_population_key_rejected(computation, stale_key) -> None:
    summary = deepcopy(computation.summary)
    summary["blockers"]["missing_split_authority"][stale_key] = 0
    with pytest.raises(ValueError):
        checker.independently_verify_counts_v1(list(computation.rows), summary)


def test_manifest_binding_mutation_rejected(computation) -> None:
    artifacts = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
        REPO
    )
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest["semantic_source_bindings"][-1]["sha256"] = "0" * 64
    mutated = dict(artifacts)
    mutated[subject.MANIFEST_FILE] = subject._json_bytes(manifest)
    with pytest.raises(ValueError):
        checker.verify_manifest_v1(mutated, computation)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timestamp", "2026-08-29T00:00:00Z"),
        ("hostname", "machine"),
        ("pid", 123),
        ("absolute_path", "/tmp/forbidden"),
    ],
)
def test_manifest_dynamic_metadata_rejected(computation, field, value) -> None:
    artifacts = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
        REPO
    )
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest[field] = value
    mutated = dict(artifacts)
    mutated[subject.MANIFEST_FILE] = subject._json_bytes(manifest)
    with pytest.raises(ValueError):
        checker.verify_manifest_v1(mutated, computation)


def test_manifest_self_sha_field_rejected(computation) -> None:
    artifacts = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_2a2_v1(
        REPO
    )
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    manifest["manifest_self_binding"]["sha256"] = "0" * 64
    mutated = dict(artifacts)
    mutated[subject.MANIFEST_FILE] = subject._json_bytes(manifest)
    with pytest.raises(ValueError):
        checker.verify_manifest_v1(mutated, computation)


def test_staged_exact7_cannot_be_tracked_clean(monkeypatch) -> None:
    def fake_git(root, *args):
        if args == ("diff", "--cached", "--name-only"):
            return list(subject.EXACT7_PATHS_V1)
        return []

    monkeypatch.setattr(checker, "_git", fake_git)
    with pytest.raises(ValueError, match="STAGED_CHANGE_PRESENT"):
        checker.verify_git_and_cache_safety_v1(REPO)


def test_predecessor_exact7_materialized_outputs_remain_exact() -> None:
    output = REPO / predecessor.OUTPUT_DIRECTORY_RELATIVE
    expected = {
        predecessor.CENSUS_FILE: (
            527918,
            "0660614ee950828cbb468cc72fdb776b26a6257e144cbae5df2a6d2a2c8f9b74",
        ),
        predecessor.SUMMARY_FILE: (
            16992,
            "4a75f817138379c25fc67186b3316e400c0850ecbb2611fa8d8158860cf39c9b",
        ),
        predecessor.MANIFEST_FILE: (
            44602,
            "eb8111311d984705d437f496e1cdd5e41899883203665d1f4b366c832bae3347",
        ),
    }
    for filename, (size, sha256) in expected.items():
        payload = (output / filename).read_bytes()
        assert len(payload) == size
        assert hashlib.sha256(payload).hexdigest() == sha256
