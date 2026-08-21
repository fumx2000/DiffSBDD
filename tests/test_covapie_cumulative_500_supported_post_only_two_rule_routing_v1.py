from __future__ import annotations

import ast
from collections import Counter
import csv
import hashlib
import inspect
import io
import json
import os
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cumulative_500_supported_post_only_two_rule_routing_v1 as cumulative,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / cumulative.OUTPUT_ROOT_RELATIVE
RANK_493_ID = "COVAPIE_CYS_SG_EVENT_V1:3NPL:B:CYS:97-:SG:F:RU8:C49"


def _csv(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _repository_observation(**overrides: object) -> dict[str, object]:
    baseline = cumulative.PUBLISHED_CUMULATIVE_ROUTING_BASELINE_ANCESTOR
    observation: dict[str, object] = {
        "branch": "main",
        "head": baseline,
        "origin_main": baseline,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "modified_tracked_paths": (),
        "staged_paths": (),
        "untracked_paths": tuple(sorted(cumulative.AUTHORIZED_PUBLICATION_PATHS)),
    }
    observation.update(overrides)
    return observation


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return cumulative.build_artifacts_v1(repo_root=ROOT)


@pytest.fixture(scope="module")
def state(artifacts: dict[str, bytes]) -> dict[str, object]:
    return {
        "manifest": json.loads(artifacts[cumulative.MANIFEST]),
        "summary": json.loads(artifacts[cumulative.SUMMARY]),
        "events": _csv(artifacts[cumulative.EVENT_INVENTORY]),
        "units": _csv(artifacts[cumulative.REVIEW_UNIT_INVENTORY]),
    }


def test_current_exact_precommit_candidate_observation_is_accepted() -> None:
    assert cumulative.validate_repository_observation_v1(
        _repository_observation()
    ) == cumulative.CUMULATIVE_ROUTING_PRECOMMIT_CANDIDATE


def test_synthetic_synchronized_clean_descendant_is_accepted() -> None:
    descendant = "d" * 40
    assert cumulative.validate_repository_observation_v1(
        _repository_observation(
            head=descendant,
            origin_main=descendant,
            untracked_paths=(),
        )
    ) == cumulative.CUMULATIVE_ROUTING_PUBLISHED_CLEAN_DESCENDANT


def test_head_origin_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="HEAD_ORIGIN_MISMATCH"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(origin_main="e" * 40)
        )


def test_ahead_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="AHEAD_BEHIND_MISMATCH"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(ahead=1)
        )


def test_behind_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="AHEAD_BEHIND_MISMATCH"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(behind=1)
        )


def test_baseline_not_ancestor_of_head_is_rejected() -> None:
    with pytest.raises(ValueError, match="BASELINE_NOT_ANCESTOR_OF_HEAD"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(baseline_ancestor_of_head=False)
        )


def test_baseline_not_ancestor_of_origin_main_is_rejected() -> None:
    with pytest.raises(ValueError, match="BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(baseline_ancestor_of_origin_main=False)
        )


def test_modified_tracked_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="MODIFIED_TRACKED_FILES_PRESENT"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(modified_tracked_paths=("tracked.py",))
        )


def test_staged_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="STAGED_FILES_PRESENT"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(staged_paths=("staged.py",))
        )


def test_extra_untracked_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="UNTRACKED_PATH_PROFILE_INVALID"):
        cumulative.validate_repository_observation_v1(
            _repository_observation(
                untracked_paths=tuple(
                    sorted(
                        cumulative.AUTHORIZED_PUBLICATION_PATHS
                        | {"unexpected.txt"}
                    )
                )
            )
        )


def test_current_repository_has_one_of_two_exact_profiles() -> None:
    assert cumulative.verify_repository_state_v1(ROOT) in {
        cumulative.CUMULATIVE_ROUTING_PRECOMMIT_CANDIDATE,
        cumulative.CUMULATIVE_ROUTING_PUBLISHED_CLEAN_DESCENDANT,
    }


def test_runtime_descendant_sha_does_not_change_artifact_bytes(
    artifacts: dict[str, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    descendant = "f" * 40
    synthetic = _repository_observation(
        head=descendant,
        origin_main=descendant,
        untracked_paths=(),
    )
    monkeypatch.setattr(
        cumulative,
        "observe_repository_state_v1",
        lambda _repo_root: synthetic,
    )
    assert cumulative.build_artifacts_v1(repo_root=ROOT) == artifacts


def test_exact_two_rule_registry_only() -> None:
    assert cumulative.routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS == (
        "NEG_V1_TS_DUMP_CATALYTIC_ADDUCT_EXACT",
        "NEG_V2_DTT_CRYSTALLIZATION_REDUCING_ADDUCT_EXACT",
    )


def test_exact_four_output_contract() -> None:
    assert cumulative.OUTPUT_FILENAMES == (
        cumulative.MANIFEST,
        cumulative.EVENT_INVENTORY,
        cumulative.REVIEW_UNIT_INVENTORY,
        cumulative.SUMMARY,
    )
    assert {path.name for path in OUTPUT.iterdir() if path.is_file()} == set(
        cumulative.OUTPUT_FILENAMES
    )


def test_persisted_outputs_equal_in_memory_build(artifacts: dict[str, bytes]) -> None:
    for name in cumulative.OUTPUT_FILENAMES:
        assert (OUTPUT / name).read_bytes() == artifacts[name]


def test_attempt_001_exact_bytes_and_sha_bindings() -> None:
    root = ROOT.parent / cumulative.ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    for name, expected in cumulative.ATTEMPT_BINDINGS.items():
        payload = (root / name).read_bytes()
        assert len(payload) == expected["byte_count"]
        assert hashlib.sha256(payload).hexdigest() == expected["sha256"]


def test_canonical_cache_stable_binding(state: dict[str, object]) -> None:
    cache = state["manifest"]["canonical_cache_read_only_binding"]
    assert cache["ledger"]["sha256"] == cumulative.CACHE_LEDGER_SHA256
    assert cache["valid_pdb_hits"] == 290
    assert cache["missing_pdb_count"] == 0
    assert cache["valid_ccd_hits"] == 224
    assert cache["missing_ccd_ids"] == ["RU8"]
    assert cache["cache_integrity_failure_count"] == 0
    assert cache["cache_modified"] is False


def test_executor_rules_and_human_snapshot_have_direct_manifest_bindings(
    state: dict[str, object],
) -> None:
    manifest = state["manifest"]
    assert set(manifest["published_executor_baseline_bindings"]) == {
        "published_rehearsal",
        "canonical_event_manifest",
        "historical_processing_outcomes",
    }
    assert manifest["published_ts_dump_gate_artifact_bindings"]
    assert manifest["published_dtt_gate_artifact_bindings"]
    assert manifest["current_human_snapshot_binding"]["decisions"]["sha256"] == (
        "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441"
    )
    assert manifest["current_human_snapshot_binding"]["progress"]["sha256"] == (
        "e1e93ff28e823c1f52b306623bbf20c06f2c0c95cca90bb1e61ee4d1b7cea216"
    )


def test_exact_500_rank_and_identity_inventory(state: dict[str, object]) -> None:
    events = state["events"]
    assert len(events) == 500
    assert [int(row["scaleup_rank"]) for row in events] == list(range(1, 501))
    assert len({row["canonical_event_id"] for row in events}) == 500


def test_historical_123_identity_set_is_exact(state: dict[str, object]) -> None:
    events = state["events"]
    actual = {
        row["canonical_event_id"]
        for row in events
        if row["candidate_lane"] == "HISTORICAL_PREDECESSOR_CANDIDATE"
    }
    triage_path = ROOT / cumulative.triage.OUTPUT_ROOT_RELATIVE / cumulative.triage.EVENT_INVENTORY
    with triage_path.open("r", encoding="utf-8", newline="") as handle:
        expected = {
            row["canonical_event_id"]
            for row in csv.DictReader(handle)
            if row["post_only_partition"] == cumulative.triage.POST_ONLY_CANDIDATE
        }
    assert actual == expected
    assert len(actual) == 123


def test_incremental_87_candidates_are_only_ranks_251_to_500(
    state: dict[str, object],
) -> None:
    rows = [
        row
        for row in state["events"]
        if row["candidate_lane"] == "NEW_INCREMENTAL_CANDIDATE"
    ]
    assert len(rows) == 87
    assert all(251 <= int(row["scaleup_rank"]) <= 500 for row in rows)


def test_cumulative_eligibility_partition_reconciles_500(
    state: dict[str, object],
) -> None:
    assert Counter(row["post_only_partition"] for row in state["events"]) == {
        cumulative.triage.POST_ONLY_CANDIDATE: 210,
        cumulative.triage.BLOCKED_LEAKAGE: 196,
        cumulative.triage.OUTSIDE_STRUCTURAL: 63,
        cumulative.triage.BLOCKED_REPRESENTATION: 31,
    }


def test_cumulative_raw_terminal_routes_are_immutable(
    state: dict[str, object],
) -> None:
    assert Counter(row["raw_terminal_outcome"] for row in state["events"]) == {
        "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY": 210,
        "LEAKAGE_EXISTING_GROUP_CONFLICT": 196,
        "STRUCTURAL_EVIDENCE_INCOMPLETE": 61,
        "QUARANTINE_REPRESENTATION_GAP": 31,
        "REJECTED_FEATURE_INCOMPATIBLE": 2,
    }


def test_rank_493_is_naturally_ineligible(state: dict[str, object]) -> None:
    row = state["events"][492]
    assert row["canonical_event_id"] == RANK_493_ID
    assert row["raw_terminal_outcome"] == "STRUCTURAL_EVIDENCE_INCOMPLETE"
    assert json.loads(row["raw_terminal_reasons_json"]) == [
        "REQUIRED_CCD_PAYLOAD_UNAVAILABLE"
    ]
    assert row["feature_compatibility_stage_status"] == "NOT_REACHED"
    assert row["post_only_candidate_eligibility"] == "false"
    assert row["post_only_partition"] == cumulative.triage.OUTSIDE_STRUCTURAL


def test_generic_candidate_selection_and_routing_have_no_rank493_component_dispatch() -> None:
    for function in (
        cumulative.supported_post_only_partition_v1,
        cumulative._build_incremental_rule_state,
    ):
        source = inspect.getsource(function)
        tree = ast.parse(source)
        string_literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert "RU8" not in string_literals
        assert RANK_493_ID not in string_literals


@pytest.mark.parametrize(
    ("stage", "route", "expected"),
    [
        ("NOT_REACHED", "STRUCTURAL_EVIDENCE_INCOMPLETE", cumulative.triage.OUTSIDE_STRUCTURAL),
        ("FAILED_CLOSED", "REJECTED_FEATURE_INCOMPATIBLE", cumulative.triage.OUTSIDE_STRUCTURAL),
        ("PASSED", "QUARANTINE_REPRESENTATION_GAP", cumulative.triage.BLOCKED_REPRESENTATION),
        ("PASSED", "LEAKAGE_EXISTING_GROUP_CONFLICT", cumulative.triage.BLOCKED_LEAKAGE),
        ("PASSED", "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY", cumulative.triage.POST_ONLY_CANDIDATE),
    ],
)
def test_published_generic_eligibility_semantics(
    stage: str, route: str, expected: str
) -> None:
    outcome = {
        "stage_statuses": {"BULK_09_MODEL_AND_FEATURE_COMPATIBILITY": stage},
        "terminal_outcome": route,
    }
    assert cumulative.supported_post_only_partition_v1(outcome) == expected


def test_structurally_eligible_unknown_route_fails_closed() -> None:
    outcome = {
        "stage_statuses": {"BULK_09_MODEL_AND_FEATURE_COMPATIBILITY": "PASSED"},
        "terminal_outcome": "UNPUBLISHED_ROUTE",
    }
    with pytest.raises(ValueError, match="PARTITION_UNRESOLVED"):
        cumulative.supported_post_only_partition_v1(outcome)


def test_new_ts_and_dtt_rule_results_are_data_derived_not_matched(
    state: dict[str, object],
) -> None:
    rows = [
        row
        for row in state["events"]
        if row["candidate_lane"] == "NEW_INCREMENTAL_CANDIDATE"
    ]
    assert Counter(row["ts_dump_rule_status"] for row in rows) == {
        cumulative.routing.gate.NOT_MATCHED: 87
    }
    assert Counter(row["dtt_rule_status"] for row in rows) == {
        cumulative.routing.gate.NOT_MATCHED: 87
    }
    assert all(row["selected_effective_rule_id"] == "" for row in rows)


def test_new_candidates_default_to_human_review_without_propagation(
    state: dict[str, object],
) -> None:
    rows = [
        row
        for row in state["events"]
        if row["candidate_lane"] == "NEW_INCREMENTAL_CANDIDATE"
    ]
    assert {row["effective_route"] for row in rows} == {
        cumulative.routing.HUMAN_REVIEW_REQUIRED
    }
    assert {row["human_authority_lane"] for row in rows} == {
        "NO_NEW_HUMAN_AUTHORITY"
    }
    assert {row["human_decision_propagated_to_new_event"] for row in rows} == {
        "false"
    }


def test_historical_two_rule_event_routes_have_exact_semantic_parity(
    state: dict[str, object],
) -> None:
    actual = {
        row["canonical_event_id"]: row["effective_route"]
        for row in state["events"]
        if row["candidate_lane"] == "HISTORICAL_PREDECESSOR_CANDIDATE"
    }
    predecessor_path = ROOT / cumulative.routing.OUTPUT_ROOT_RELATIVE / cumulative.routing.EVENT_INVENTORY
    with predecessor_path.open("r", encoding="utf-8", newline="") as handle:
        expected = {
            row["canonical_event_id"]: row["unit_final_task_domain_route"]
            for row in csv.DictReader(handle)
        }
    assert actual == expected
    assert Counter(actual.values()) == {
        cumulative.routing.AUTO_NEGATIVE_EXACT_FINAL: 32,
        cumulative.routing.HUMAN_NOT_RELEVANT_FINAL: 30,
        cumulative.routing.HUMAN_RELEVANT_FINAL: 5,
        cumulative.routing.HUMAN_REVIEW_REQUIRED: 56,
    }


def test_historical_rule_match_identity_sets_have_exact_parity(
    state: dict[str, object],
) -> None:
    actual_by_rule = {
        cumulative.routing.gate.RULE_ID: {
            row["canonical_event_id"]
            for row in state["events"]
            if row["candidate_lane"] == "HISTORICAL_PREDECESSOR_CANDIDATE"
            and row["ts_dump_rule_status"]
            == cumulative.routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
        },
        cumulative.routing.dtt_gate.RULE_ID: {
            row["canonical_event_id"]
            for row in state["events"]
            if row["candidate_lane"] == "HISTORICAL_PREDECESSOR_CANDIDATE"
            and row["dtt_rule_status"]
            == cumulative.routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
        },
    }
    predecessor_path = ROOT / cumulative.routing.OUTPUT_ROOT_RELATIVE / cumulative.routing.EVENT_INVENTORY
    with predecessor_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_by_rule = {
        rule_id: {
            row["canonical_event_id"]
            for row in rows
            if row["rule_id"] == rule_id
            and row["gate_event_status"]
            == cumulative.routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
        }
        for rule_id in cumulative.routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS
    }
    assert actual_by_rule == expected_by_rule


def test_workload_reconciliation_56_plus_87_equals_143(
    state: dict[str, object],
) -> None:
    workload = state["summary"]["human_review_workload"]
    assert workload["historical_unresolved_event_count"] == 56
    assert workload["new_unresolved_event_count"] == 87
    assert workload["cumulative_unresolved_event_count"] == 143
    assert sum(int(row["event_count"]) for row in state["units"]) == 143


def test_workload_units_24_plus_33_new_equals_57(
    state: dict[str, object],
) -> None:
    workload = state["summary"]["human_review_workload"]
    assert workload["historical_unresolved_review_unit_count"] == 24
    assert workload["new_unresolved_review_unit_count"] == 34
    assert workload["new_units_joining_existing_workload_equivalent_unit_count"] == 1
    assert workload["new_genuinely_new_unit_count"] == 33
    assert workload["cumulative_unresolved_review_unit_count"] == 57
    assert len(state["units"]) == 57


def test_exact_workload_join_is_organization_not_authority(
    state: dict[str, object],
) -> None:
    joining = [
        row
        for row in state["units"]
        if row["new_events_join_existing_workload_equivalent_unit"] == "true"
    ]
    assert len(joining) == 1
    row = joining[0]
    assert row["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74"
    assert int(row["historical_unresolved_event_count"]) == 5
    assert int(row["new_unresolved_event_count"]) == 4
    assert row["human_decision_propagated"] == "false"
    assert row["grouping_semantics"].endswith("WORKLOAD_ONLY")


def test_summary_scientific_metrics(state: dict[str, object]) -> None:
    summary = state["summary"]
    assert summary["population"]["historical_post_only_candidate_count"] == 123
    assert summary["population"]["incremental_post_only_candidate_count"] == 87
    assert summary["population"]["cumulative_post_only_candidate_count"] == 210
    assert summary["historical_two_rule_routing"]["effective_auto_negative_events"] == 32
    assert summary["incremental_two_rule_routing"]["new_TS_auto_negative_event_count"] == 0
    assert summary["incremental_two_rule_routing"]["new_DTT_auto_negative_event_count"] == 0
    assert summary["cumulative_two_rule_routing"]["effective_auto_negative_event_count"] == 32
    assert summary["ready_for_gpt_review"] is True


def test_summary_safety_and_no_new_authority(state: dict[str, object]) -> None:
    safety = state["summary"]["safety"]
    assert safety["abandoned_transition_metal_policy_files_removed"] is True
    for field in (
        "RU8_retry_performed",
        "attempt_002_created",
        "RU8_special_case_used",
        "historical_two_rule_routing_modified",
        "human_overlay_modified",
        "production_authority_created",
        "canonical_bulk_cache_modified",
        "network_performed",
        "training_materialization_performed",
    ):
        assert safety[field] is False


def test_no_runtime_git_timestamp_absolute_path_or_cache_stat_tree_persisted(
    state: dict[str, object],
) -> None:
    forbidden_keys = {
        "head",
        "origin_main",
        "ahead",
        "behind",
        "timestamp",
        "execution_timestamp",
        "stat_tree_sha256",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert not (set(value) & forbidden_keys)
            for key, item in value.items():
                assert not (isinstance(key, str) and os.path.isabs(key))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            assert not os.path.isabs(value)

    walk(state["manifest"])
    walk(state["summary"])


def test_manifest_does_not_record_its_own_sha(state: dict[str, object]) -> None:
    manifest = state["manifest"]
    assert cumulative.MANIFEST not in manifest[
        "output_sha256_excluding_manifest_and_summary"
    ]
    assert cumulative.SUMMARY not in manifest[
        "output_sha256_excluding_manifest_and_summary"
    ]


def test_network_blocked_replay_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("NETWORK_OR_CONTROLLED_EXECUTION_CALLED")

    for name in (
        "official_network_backend_v1",
        "acquire_required_payloads_v1",
        "execute_controlled_network_v1",
        "run_v1",
    ):
        monkeypatch.setattr(cumulative.executor, name, forbidden)
    before = cumulative.executor.snapshot_cache_tree_v1(
        cumulative.executor.canonical_controlled_cache_root_v1(ROOT)
    )
    replay = cumulative.build_artifacts_v1(repo_root=ROOT)
    after = cumulative.executor.snapshot_cache_tree_v1(
        cumulative.executor.canonical_controlled_cache_root_v1(ROOT)
    )
    assert before == after
    assert replay[cumulative.SUMMARY] == (OUTPUT / cumulative.SUMMARY).read_bytes()
