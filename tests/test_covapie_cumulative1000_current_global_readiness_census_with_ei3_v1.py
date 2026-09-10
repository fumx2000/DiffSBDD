from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
import re

import pytest

from covalent_ext import (
    covapie_cumulative1000_current_global_readiness_census_with_ei3_v1 as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / subject.CHECKER_RELATIVE


def _load_checker():
    spec = importlib.util.spec_from_file_location("covapie_with_ei3_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


@pytest.fixture(scope="session")
def live_report() -> dict[str, object]:
    return checker.check(ROOT)


def test_public_api_is_exact_five_and_signatures_match_family() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithEI3Error",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1",
    )
    assert str(inspect.signature(subject.compute_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1)) == "(repo_root: 'Path') -> 'base.Cumulative1000CurrentGlobalReadinessComputationV1'"
    assert "predecessor_computation" in inspect.signature(subject.validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1).parameters
    assert str(inspect.signature(subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1)) == "(repo_root: 'Path') -> 'dict[str, bytes]'"
    assert "output_directory" in inspect.signature(subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1).parameters


def test_exact7_and_exact3_inventory(live_report: dict[str, object]) -> None:
    assert len(subject.EXACT7_PATHS_V1) == 7
    assert len(set(subject.EXACT7_PATHS_V1)) == 7
    output = ROOT / subject.OUTPUT_DIRECTORY_RELATIVE
    assert {path.name for path in output.iterdir()} == {
        subject.CENSUS_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }
    assert len(live_report["Exact7_files"]) == 7


def test_live_repository_profile_is_real_branch_profile(live_report: dict[str, object]) -> None:
    repository = live_report["repository"]
    assert repository["profile"] in {checker.CANDIDATE_UNTRACKED, checker.TRACKED_CLEAN}
    if repository["profile"] == checker.CANDIDATE_UNTRACKED:
        assert repository["HEAD"] == repository["origin_main"] == subject.BASELINE_COMMIT
        assert (repository["ahead"], repository["behind"]) == (0, 0)
        assert repository["ordinary_untracked_paths"] == sorted(subject.EXACT7_PATHS_V1)
        assert repository["git_index_mode_checked"] is False
    else:
        assert repository["ordinary_untracked_count"] == 0
        assert repository["git_index_mode_checked"] is True
        assert repository["git_index_record_count"] == 7
        assert set(repository["git_index_modes"].values()) == {"100644"}


def test_exact3_overlay_and_997_unchanged(live_report: dict[str, object]) -> None:
    assert live_report["refresh"] == {
        "row_count": 1000,
        "column_count": 47,
        "ei3_overlay_event_count": 3,
        "non_ei3_changed_row_count": 0,
        "unchanged_row_count": 997,
        "authorized_overlay_field_count": 19,
        "authorized_but_unchanged_field_count": 7,
        "actual_changed_field_count": 12,
    }
    assert subject.EI3_EXACT3_RANKS_V1 == (967, 968, 969)
    assert len(set(subject.EI3_EXACT3_EVENT_IDS_V1)) == 3


def test_ei3_matrix_uses_explicit_81_column_adapter_and_preserves_nulls() -> None:
    rows = checker._read_csv(
        ROOT / subject.EI3_EVENT_MATRIX_RELATIVE, subject.ingestion.MATRIX_HEADER, 3
    )
    validated = subject._validate_ei3_matrix_rows_v1(rows)
    assert len(subject.ingestion.MATRIX_HEADER) == 81
    assert all(row["role_profile_raw_json"] == "null" for row in validated)
    assert all(row["role_profile_derived_state"] == "NOT_ESTABLISHED" for row in validated)
    assert all(row["structurally_applicable_task_ids_json"] == "null" for row in validated)
    assert all(row["training_disposition"] == "NOT_APPLICABLE" for row in validated)
    assert [row["target_covalent_connection_count"] for row in validated] == ["1", "1", "1"]
    assert [row["metal_context_connection_count"] for row in validated] == ["0", "0", "2"]
    nullable = (
        "selected_role_candidate_json",
        "role_profile_raw_json",
        "warhead_atom_ids_json",
        "linker_atom_ids_json",
        "scaffold_atom_ids_json",
        "minimal_seed_json",
        "minimal_seed_atom_ids_json",
        "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    )
    assert all(row[field] == "null" for row in validated for field in nullable)
    for forbidden in (
        "role_sample_authority",
        "task_applicability_sample_authority",
        "role_profile",
        "training_use_allowed",
    ):
        assert forbidden not in subject.ingestion.MATRIX_HEADER


def test_summary_deltas_are_rows_derived(live_report: dict[str, object]) -> None:
    assert live_report["counts"] == {
        "global_unreviewed": 157,
        "global_negative": 84,
        "chemistry_positive": 170,
        "task_not_relevant": 116,
        "training_not_applicable": 116,
        "pair_authority": 170,
        "role_authority": 156,
        "structural_labels": 156,
    }
    review = live_report["human_review"]
    assert (review["completed_event_count"], review["completed_unit_count"]) == (181, 33)
    assert (review["completed_negative_event_count"], review["completed_negative_unit_count"]) == (54, 12)
    assert (review["completed_positive_event_count"], review["completed_positive_unit_count"]) == (127, 21)
    assert (review["unreviewed_event_count"], review["unreviewed_unit_count"]) == (157, 98)


def test_canonical_exact5_keeps_b3_and_no_sixth_task() -> None:
    assert len(subject.CANONICAL_EXACT5_V1) == 5
    assert [item[1] for item in subject.CANONICAL_EXACT5_V1] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert subject.CANONICAL_EXACT5_V1[3][2] == "B3"


def test_orthogonal_population_is_predecessor_exact23_union_exact3(live_report: dict[str, object]) -> None:
    orthogonal = live_report["orthogonal"]
    assert orthogonal["task_negative_chemistry_positive_population_count"] == 26
    assert orthogonal["historical_exact23_population_count"] == 23
    assert orthogonal["ei3_orthogonal_population_count"] == 3
    assert orthogonal["population_equals_historical_exact23_union_ei3_exact3"] is True
    assert "orthogonal_population_frozen_exact20" not in orthogonal


def test_semantic_bindings_are_exact_prefix_plus_six(live_report: dict[str, object]) -> None:
    assert live_report["semantic_source_bindings"] == {
        "predecessor": 198,
        "successor": 204,
        "prefix_preserved": True,
        "additive": 6,
    }
    manifest = json.loads(
        (ROOT / subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE).read_text()
    )
    new = manifest["semantic_source_bindings"][198:]
    assert len({item["artifact_role"] for item in new}) == 6
    assert len({(item["path_namespace"], item["path"]) for item in manifest["semantic_source_bindings"]}) == 204


def test_next_pending_is_full_ei3_identity(live_report: dict[str, object]) -> None:
    next_pending = live_report["next_priority_review"]
    assert next_pending["review_unit_id"] == subject.NEXT_PENDING_REVIEW_UNIT_ID_V1
    assert next_pending["ligand_component_ids"] == ["AZP"]
    assert next_pending["pdb_ids"] == ["2A5I", "2A5K"]
    assert next_pending["event_count"] == 3
    assert next_pending["raw_priority_rank"] == 34
    assert next_pending["rank"] == 1


def test_materialized_fresh_and_double_build(live_report: dict[str, object]) -> None:
    assert live_report["materialized_equals_fresh_build"] is True
    assert live_report["deterministic_double_build"] is True
    assert live_report["independent_fresh_build_count"] == 2
    assert live_report["semantic_artifact_validation"] is True
    assert live_report["normal_and_raw_paths_share_comparator"] is True


def _synthetic_exact3_bytes() -> dict[str, bytes]:
    return {
        subject.CENSUS_FILE: b"census\n",
        subject.SUMMARY_FILE: b"summary\n",
        subject.MANIFEST_FILE: b"manifest\n",
    }


def test_shared_artifact_comparator_accepts_identical_exact3() -> None:
    payloads = _synthetic_exact3_bytes()
    assert checker._verify_artifact_byte_identity_v1(payloads, dict(payloads)) is None


@pytest.mark.parametrize(
    "name",
    (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE),
)
def test_shared_artifact_comparator_rejects_each_changed_payload(name: str) -> None:
    expected = _synthetic_exact3_bytes()
    observed = dict(expected)
    observed[name] += b"changed"
    with pytest.raises(
        ValueError,
        match=re.escape(
            checker.ERROR_TOKEN + ":MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH"
        )
        + "$",
    ):
        checker._verify_artifact_byte_identity_v1(observed, expected)


@pytest.mark.parametrize("mutation", ("missing", "extra"))
def test_shared_artifact_comparator_rejects_inventory_drift(mutation: str) -> None:
    expected = _synthetic_exact3_bytes()
    observed = dict(expected)
    if mutation == "missing":
        observed.pop(subject.SUMMARY_FILE)
    else:
        observed["unexpected.json"] = b"extra\n"
    with pytest.raises(ValueError, match="MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH$"):
        checker._verify_artifact_byte_identity_v1(observed, expected)


def test_normal_and_raw_paths_call_the_shared_comparator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = _synthetic_exact3_bytes()
    real = checker._verify_artifact_byte_identity_v1
    calls: list[tuple[dict[str, bytes], dict[str, bytes]]] = []

    def spy(observed: dict[str, bytes], expected: dict[str, bytes]) -> None:
        calls.append((dict(observed), dict(expected)))
        real(observed, expected)

    monkeypatch.setattr(checker, "_verify_artifact_byte_identity_v1", spy)
    checker._verify_materialized_and_double_build_v1(payloads, payloads, payloads)
    assert len(calls) == 2
    assert all(observed == expected == payloads for observed, expected in calls)
    assert checker._run_raw_byte_probe_v1(payloads) == (
        "MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH"
    )
    assert len(calls) == 3
    observed, expected = calls[-1]
    assert observed[subject.CENSUS_FILE] != expected[subject.CENSUS_FILE]
    assert observed[subject.SUMMARY_FILE] == expected[subject.SUMMARY_FILE]
    assert observed[subject.MANIFEST_FILE] == expected[subject.MANIFEST_FILE]


def test_noop_comparator_makes_raw_probe_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        checker, "_verify_artifact_byte_identity_v1", lambda _observed, _expected: None
    )
    with pytest.raises(ValueError, match="TAMPER_DID_NOT_FAIL:raw_bytes$"):
        checker._run_raw_byte_probe_v1(_synthetic_exact3_bytes())


@pytest.mark.parametrize("failure_kind", ("wrong_token", "type_error"))
def test_raw_probe_does_not_accept_unexpected_comparator_failure(
    monkeypatch: pytest.MonkeyPatch, failure_kind: str
) -> None:
    def wrong_token(_observed: dict[str, bytes], _expected: dict[str, bytes]) -> None:
        raise ValueError(checker.ERROR_TOKEN + ":WRONG_TOKEN")

    def type_error(_observed: dict[str, bytes], _expected: dict[str, bytes]) -> None:
        raise TypeError("unexpected")

    monkeypatch.setattr(
        checker,
        "_verify_artifact_byte_identity_v1",
        wrong_token if failure_kind == "wrong_token" else type_error,
    )
    expected = (
        "TAMPER_WRONG_TOKEN:raw_bytes"
        if failure_kind == "wrong_token"
        else "TAMPER_UNEXPECTED_EXCEPTION:raw_bytes:TypeError"
    )
    with pytest.raises(ValueError, match=re.escape(expected)):
        checker._run_raw_byte_probe_v1(_synthetic_exact3_bytes())


def test_high_value_tamper_probes_reach_semantic_validators(live_report: dict[str, object]) -> None:
    probes = live_report["tamper_probes"]
    expected = {
        "target_missing",
        "target_duplicate",
        "fourth_event",
        "non_target_997",
        "d2_relevant",
        "chemistry_negative",
        "na_to_exclude",
        "na_to_include",
        "pair_authority_lost",
        "pair_promoted_to_training_target",
        "role_authority_fabricated",
        "task_ids_empty_array",
        "task_ids_nonempty",
        "role_profile_promoted",
        "training_admission_promoted",
        "future_candidate_promoted",
        "rank_changed",
        "event_identity_changed",
        "column_order_changed",
        "event_set_digest",
        "source_composition",
        "global_negative_population",
        "orthogonal_old23",
        "next_pending_completed_ei3",
        "next_pending_pdb_truncated",
        "historical_admission_zeroed",
        "ready_promoted",
        "b3_omitted",
        "sixth_task",
        "binding_missing",
        "binding_duplicate",
        "binding_namespace",
        "binding_permission_semantics",
        "binding_prefix_changed",
        "binding_role_collision",
        "matrix_79_columns",
        "nullable_role_became_array",
        "metal_context_became_covalent",
        "pre_hard_prerequisite_reversed",
        "semantic_task_relevance_with_synced_manifest",
        "semantic_chemistry_with_synced_manifest",
        "semantic_training_with_synced_manifest",
        "semantic_role_authority_with_synced_manifest",
        "semantic_task_ids_with_synced_manifest",
        "semantic_non_target_with_synced_manifest",
        "manifest_self_reference",
        "raw_bytes",
    }
    assert set(probes) == expected
    assert live_report["tamper_probe_count"] == len(expected) == 47
    assert all(isinstance(token, str) and token for token in probes.values())
    assert probes["raw_bytes"] == "MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH"


def test_lifecycle_success_and_failure_paths(live_report: dict[str, object]) -> None:
    assert live_report["lifecycle_simulations"] == {
        "candidate_untracked_supported": True,
        "tracked_clean_supported": True,
        "missing_mixed_extra_rejected": True,
        "executable_symlink_nonzero_stage_rejected": True,
    }
    with pytest.raises(ValueError, match="UNKNOWN_REPOSITORY_PROFILE$"):
        checker.classify_repository_profile(
            expected_paths=("a", "b"),
            tracked_paths={"a"},
            ordinary_untracked={"b"},
            status_lines=("?? b",),
            working_diff=set(),
            cached_diff=set(),
        )


def test_manifest_preserves_authority_and_training_stop_boundary() -> None:
    manifest = json.loads(
        (ROOT / subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE).read_text()
    )
    contract = manifest["refresh_contract"]
    assert contract["ei3_review_completed"] is True
    assert contract["review_state_created_by_this_refresh"] is False
    assert contract["new_human_authority_created"] is False
    assert contract["new_scientific_authority_created"] is False
    assert contract["task_label_authority"] is False
    assert contract["historical_formal_training_admitted_count"] == 5
    assert contract["formal_training_admitted_by_refresh"] is False
    assert contract["feature_semantics_audit_performed"] is False
    assert contract["feature_semantics_audit_required_before_training"] is True
    assert contract["ready_for_training"] is False
    assert contract["training_started"] is False


def test_cli_success_contract_uses_report_then_markers(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], live_report: dict[str, object]) -> None:
    monkeypatch.setattr(checker, "check", lambda _root: live_report)
    assert checker.main() == 0
    stdout = capsys.readouterr().out
    report, end = json.JSONDecoder().raw_decode(stdout.lstrip())
    tail = stdout.lstrip()[end:]
    assert report["status"] == "PASS"
    assert "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1_PASS=true" in tail.splitlines()
    assert "lifecycle=" + live_report["repository"]["profile"] in tail.splitlines()
    assert "NEXT_PRIORITY_REVIEW_PDB_IDS=[\"2A5I\",\"2A5K\"]" in tail.splitlines()


def test_cli_failure_contract_is_fail_closed(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def fail(_root: Path) -> dict[str, object]:
        raise ValueError("EXPECTED_FAILURE")

    monkeypatch.setattr(checker, "check", fail)
    assert checker.main() == 1
    stdout = capsys.readouterr().out
    assert stdout.splitlines() == [
        "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1_PASS=false",
        "ERROR=EXPECTED_FAILURE",
    ]
