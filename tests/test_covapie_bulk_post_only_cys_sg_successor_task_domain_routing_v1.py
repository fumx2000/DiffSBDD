from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as routing,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / routing.OUTPUT_ROOT_RELATIVE
EB1C0 = "COVAPIE_BULK_REVIEW_UNIT_EB1C0FF8712C32A9"
CALIBRATION = "COVAPIE_BULK_REVIEW_UNIT_5184266C4D495D18"
DTT_S1 = "COVAPIE_BULK_REVIEW_UNIT_A3782D89BDEF47C1"
DTT_S4 = "COVAPIE_BULK_REVIEW_UNIT_2EBCD325E1CD2081"
DTU = "COVAPIE_BULK_REVIEW_UNIT_024EEB356034F83D"
EIP = "COVAPIE_BULK_REVIEW_UNIT_07BD3B72031BD7CC"
AJ3 = "COVAPIE_BULK_REVIEW_UNIT_5662273FCD38234C"
FIVE_X = "COVAPIE_BULK_REVIEW_UNIT_59100AAB78E957D9"
UFP_UNITS = {
    "COVAPIE_BULK_REVIEW_UNIT_1E58101A3E611294",
    "COVAPIE_BULK_REVIEW_UNIT_CF6D3ADC970757BA",
}
PYR = "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4"


def _csv(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return routing.build_artifacts_v1(repo_root=ROOT)


@pytest.fixture(scope="module")
def state() -> dict[str, object]:
    bindings = routing.verify_predecessor_bindings_v1(ROOT)
    inputs = routing._load_routing_inputs_v1(ROOT, bindings)
    production_context = routing.build_current_production_positive_context_v1(
        bindings=bindings,
        event_by_id=inputs["event_by_id"],
        outcome_by_id=inputs["outcome_by_id"],
    )
    override = routing.gate.build_runtime_positive_override_context_v1(
        current_human_overlay=bindings["current_human"],
        current_human_overlay_sha256=bindings["current_human_snapshot"][
            "decisions"
        ]["sha256"],
        outcome_by_id=production_context["outcome_by_id"],
    )
    return {
        "bindings": bindings,
        "inputs": inputs,
        "override": override,
        "production_context": production_context,
        "context": bindings["gate_manifest"]["scientific_rule_context"],
        "dtt_context": bindings["dtt_gate_manifest"][
            "scientific_rule_context"
        ],
    }


def _unit_evaluations(
    state: dict[str, object], unit_id: str
) -> tuple[routing.TaskDomainAutoNegativeEventEvaluation, ...]:
    inputs = state["inputs"]
    unit = inputs["unit_by_id"][unit_id]
    result: list[routing.TaskDomainAutoNegativeEventEvaluation] = []
    for event_id in unit["canonical_event_ids"]:
        result.extend(
            routing.dispatch_exact_auto_negative_rules_v1(
                event=inputs["event_by_id"][event_id],
                outcome=inputs["outcome_by_id"][event_id],
                rule_context_by_id={
                    routing.gate.RULE_ID: state["context"],
                    routing.dtt_gate.RULE_ID: state["dtt_context"],
                },
                override_context_by_id={
                    routing.gate.RULE_ID: state["override"],
                    routing.dtt_gate.RULE_ID: state["override"],
                },
            )
        )
    return tuple(result)


def _route(state: dict[str, object], unit_id: str):
    inputs = state["inputs"]
    return routing.route_successor_task_domain_review_unit_v1(
        review_unit=inputs["unit_by_id"][unit_id],
        event_evaluations=_unit_evaluations(state, unit_id),
        human_unit_state=inputs["human_unit_by_id"][unit_id],
    )


def test_ordered_real_registry_is_exact_ts_then_dtt() -> None:
    assert routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS == (
        routing.gate.RULE_ID,
        routing.dtt_gate.RULE_ID,
    )
    assert routing.dtt_gate.AutoNegativeEvaluationResult is (
        routing.gate.AutoNegativeEvaluationResult
    )


def test_published_dtt_artifacts_and_scientific_context_are_sha_bound(
    artifacts: dict[str, bytes], state: dict[str, object]
) -> None:
    manifest = json.loads(artifacts[routing.MANIFEST])
    assert manifest["published_dtt_gate_artifact_bindings"] == state[
        "bindings"
    ]["published_dtt_gate"]
    assert manifest["dtt_gate_publication"] == {
        "commit": routing.DTT_GATE_PUBLICATION_COMMIT,
        "subject": routing.DTT_GATE_PUBLICATION_SUBJECT,
        "required_as_ancestor_of_synchronized_head_and_origin_main": True,
    }
    source = manifest["integrated_scientific_rule_context_sources"][
        routing.dtt_gate.RULE_ID
    ]
    assert source["path"] == routing.DTT_GATE_MANIFEST_RELATIVE.as_posix()
    assert source["sha256"] == routing.DTT_GATE_ARTIFACT_BINDINGS[
        routing.DTT_GATE_MANIFEST_RELATIVE
    ]["sha256"]
    assert source["external_cache_reconstruction_used"] is False


def test_default_build_uses_published_dtt_context_without_cache_rebuild(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("DTT_EXTERNAL_CACHE_RECONSTRUCTION_CALLED")

    for name in (
        "build_static_rule_context_v1",
        "_build_static_rule_context_v1",
        "_read_sha_bound_cache_file",
        "_parse_official_ccd",
        "_build_independent_1fvg_reagent_context",
    ):
        monkeypatch.setattr(routing.dtt_gate, name, forbidden)
    built = routing.build_artifacts_v1(repo_root=ROOT)
    assert json.loads(built[routing.SUMMARY])[
        "total_rule_event_evaluation_count"
    ] == 246


def test_default_build_shares_one_current_runtime_override_between_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = routing.dispatch_exact_auto_negative_rules_v1
    observed_calls = 0

    def wrapped(**kwargs: object):
        nonlocal observed_calls
        override_by_id = kwargs["override_context_by_id"]
        assert override_by_id[routing.gate.RULE_ID] is override_by_id[
            routing.dtt_gate.RULE_ID
        ]
        observed_calls += 1
        return original(**kwargs)

    monkeypatch.setattr(routing, "dispatch_exact_auto_negative_rules_v1", wrapped)
    routing.build_artifacts_v1(repo_root=ROOT)
    assert observed_calls == 123


def test_exact_36_unit_and_123_event_reconciliation(
    artifacts: dict[str, bytes],
) -> None:
    units = _csv(artifacts[routing.UNIT_INVENTORY])
    events = _csv(artifacts[routing.EVENT_INVENTORY])
    assert len(units) == 36
    assert len(events) == 246
    assert Counter(row["final_task_domain_route"] for row in units) == {
        routing.HUMAN_NOT_RELEVANT_FINAL: 7,
        routing.HUMAN_RELEVANT_FINAL: 3,
        routing.AUTO_NEGATIVE_EXACT_FINAL: 2,
        routing.HUMAN_REVIEW_REQUIRED: 24,
    }
    route_by_event = {
        row["canonical_event_id"]: row["unit_final_task_domain_route"]
        for row in events
    }
    assert Counter(route_by_event.values()) == {
        routing.HUMAN_NOT_RELEVANT_FINAL: 30,
        routing.HUMAN_RELEVANT_FINAL: 5,
        routing.AUTO_NEGATIVE_EXACT_FINAL: 32,
        routing.HUMAN_REVIEW_REQUIRED: 56,
    }


def test_per_rule_raw_metrics_are_distinct_from_effective_new_32(
    artifacts: dict[str, bytes],
) -> None:
    summary = json.loads(artifacts[routing.SUMMARY])
    events = _csv(artifacts[routing.EVENT_INVENTORY])
    units = _csv(artifacts[routing.UNIT_INVENTORY])
    assert sum(
        row["gate_event_status"] == routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
        for row in events
    ) == 49
    assert len(
        {
            row["canonical_event_id"]
            for row in events
            if row["effective_auto_negative"] == "true"
        }
    ) == 32
    assert sum(
        any(item["all_events_match"] for item in json.loads(row["per_rule_evidence_json"]))
        for row in units
    ) == 4
    assert sum(row["effective_new_auto_negative"] == "true" for row in units) == 2
    assert summary["raw_gate_matched_events"] == 47
    assert summary["raw_gate_matched_units"] == 2
    assert summary["raw_gate_metric_semantics"] == "LEGACY_TS_DUMP_RULE_ONLY"
    assert summary["raw_rule_metrics_by_rule"] == {
        routing.gate.RULE_ID: {
            "matched_events": 47,
            "fully_matched_units": 2,
            "invalid_events": 0,
        },
        routing.dtt_gate.RULE_ID: {
            "matched_events": 2,
            "fully_matched_units": 2,
            "invalid_events": 0,
        },
    }
    assert summary["effective_new_auto_negative_events"] == 32
    assert summary["effective_new_auto_negative_units"] == 2
    assert summary["total_rule_event_evaluation_count"] == 246
    assert summary["matched_rule_event_evaluation_count"] == 49
    assert summary["invalid_rule_event_evaluation_count"] == 0
    assert summary["fully_matched_rule_unit_pairs"] == 4
    assert summary["multiple_full_match_conflict_units"] == 0
    assert summary["effective_auto_negative_metrics_by_rule"] == {
        routing.gate.RULE_ID: {"events": 31, "units": 1},
        routing.dtt_gate.RULE_ID: {"events": 1, "units": 1},
    }


def test_2aaz_human_negative_precedes_raw_gate_match(
    state: dict[str, object],
) -> None:
    route = _route(state, CALIBRATION)
    assert route.event_count == 16
    assert route.auto_negative_rule_id == ""
    assert route.auto_negative_event_match_count == 0
    assert route.gate_unit_all_events_match is False
    assert route.rule_evidence == (
        routing.ExactRuleUnitEvidence(
            rule_id=routing.gate.RULE_ID,
            matched_event_count=16,
            not_matched_event_count=0,
            invalid_event_count=0,
            all_events_match=True,
        ),
        routing.ExactRuleUnitEvidence(
            rule_id=routing.dtt_gate.RULE_ID,
            matched_event_count=0,
            not_matched_event_count=16,
            invalid_event_count=0,
            all_events_match=False,
        ),
    )
    assert route.route_status == routing.HUMAN_NOT_RELEVANT_FINAL
    assert route.effective_new_auto_negative is False
    assert route.human_precedence_applied is True
    assert route.downstream_chemistry_review_required is False


def test_eb1c0_exact_live_integration_and_no_human_write(
    state: dict[str, object],
) -> None:
    decisions_path = ROOT / routing.gate.HUMAN_DECISIONS_RELATIVE
    progress_path = ROOT / routing.HUMAN_PROGRESS_RELATIVE
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (decisions_path, progress_path)
    }
    human = state["inputs"]["human_unit_by_id"][EB1C0]
    assert human["workflow_status"] == "UNREVIEWED"
    assert human["training_domain_relevance_decision"] == ""
    assert all(
        event["post_geometry_training_usable"] == ""
        and event["event_training_use_decision"] == ""
        and event["event_exclusion_reason"] == ""
        for event in human["events"]
    )
    route = _route(state, EB1C0)
    assert route.event_count == 31
    assert route.auto_negative_event_match_count == 31
    assert route.total_gate_invalid_evaluation_count == 0
    assert route.gate_unit_all_events_match is True
    assert route.route_status == routing.AUTO_NEGATIVE_EXACT_FINAL
    assert route.effective_new_auto_negative is True
    assert route.auto_negative_rule_id == routing.gate.RULE_ID
    assert route.rule_evidence[0].matched_event_count == 31
    assert route.rule_evidence[0].all_events_match is True
    assert route.rule_evidence[1] == routing.ExactRuleUnitEvidence(
        routing.dtt_gate.RULE_ID, 0, 31, 0, False
    )
    assert before == {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (decisions_path, progress_path)
    }


def test_dtt_s1_exact_live_integration_uses_second_registry_rule(
    state: dict[str, object],
) -> None:
    human = state["inputs"]["human_unit_by_id"][DTT_S1]
    assert human["workflow_status"] == "UNREVIEWED"
    assert human["training_domain_relevance_decision"] == ""
    route = _route(state, DTT_S1)
    assert route.event_count == 1
    assert route.rule_evidence == (
        routing.ExactRuleUnitEvidence(routing.gate.RULE_ID, 0, 1, 0, False),
        routing.ExactRuleUnitEvidence(
            routing.dtt_gate.RULE_ID, 1, 0, 0, True
        ),
    )
    assert route.total_gate_invalid_evaluation_count == 0
    assert route.auto_negative_rule_id == routing.dtt_gate.RULE_ID
    assert route.auto_negative_event_match_count == 1
    assert route.gate_unit_all_events_match is True
    assert route.route_status == routing.AUTO_NEGATIVE_EXACT_FINAL
    assert route.effective_new_auto_negative is True


def test_dtt_s4_raw_match_preserves_human_negative_precedence(
    state: dict[str, object],
) -> None:
    route = _route(state, DTT_S4)
    assert route.rule_evidence == (
        routing.ExactRuleUnitEvidence(routing.gate.RULE_ID, 0, 1, 0, False),
        routing.ExactRuleUnitEvidence(
            routing.dtt_gate.RULE_ID, 1, 0, 0, True
        ),
    )
    assert route.auto_negative_rule_id == ""
    assert route.route_status == routing.HUMAN_NOT_RELEVANT_FINAL
    assert route.human_precedence_applied is True
    assert route.effective_new_auto_negative is False


def test_dtu_remains_outside_dtt_rule_and_requires_human_review(
    state: dict[str, object],
) -> None:
    route = _route(state, DTU)
    assert route.rule_evidence == (
        routing.ExactRuleUnitEvidence(routing.gate.RULE_ID, 0, 1, 0, False),
        routing.ExactRuleUnitEvidence(
            routing.dtt_gate.RULE_ID, 0, 1, 0, False
        ),
    )
    assert route.auto_negative_rule_id == ""
    assert route.route_status == routing.HUMAN_REVIEW_REQUIRED


def test_current_human_relevant_units_have_first_precedence_and_aj3_remains(
    state: dict[str, object],
) -> None:
    eip = _route(state, EIP)
    aj3 = _route(state, AJ3)
    five_x = _route(state, FIVE_X)
    assert {eip.route_status, aj3.route_status, five_x.route_status} == {
        routing.HUMAN_RELEVANT_FINAL
    }
    assert all(
        route.effective_new_auto_negative is False
        and route.human_precedence_applied is True
        for route in (eip, aj3, five_x)
    )
    assert eip.downstream_chemistry_review_required is False
    assert five_x.downstream_chemistry_review_required is False
    assert aj3.human_workflow_status == "IN_PROGRESS"
    assert aj3.downstream_chemistry_review_required is True


def test_ufp_and_pyr_boundaries_remain_human_review(
    state: dict[str, object],
) -> None:
    for unit_id in sorted(UFP_UNITS | {PYR}):
        route = _route(state, unit_id)
        assert route.route_status == routing.HUMAN_REVIEW_REQUIRED
        assert route.auto_negative_event_match_count == 0
        assert route.effective_new_auto_negative is False


def test_human_deferred_decision_never_auto_negatives(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    deferred = deepcopy(inputs["human_unit_by_id"][EB1C0])
    deferred["workflow_status"] = "DEFERRED"
    deferred["training_domain_relevance_decision"] = (
        routing.HUMAN_DEFERRED_DECISION
    )
    route = routing.route_successor_task_domain_review_unit_v1(
        review_unit=inputs["unit_by_id"][EB1C0],
        event_evaluations=_unit_evaluations(state, EB1C0),
        human_unit_state=deferred,
    )
    assert route.rule_evidence[0].all_events_match is True
    assert route.gate_unit_all_events_match is False
    assert route.route_status == routing.HUMAN_REVIEW_REQUIRED_DEFERRED
    assert route.effective_new_auto_negative is False


def test_unknown_malformed_missing_and_invalid_gate_evidence_fail_closed(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    unit = inputs["unit_by_id"][EB1C0]
    human = inputs["human_unit_by_id"][EB1C0]
    valid = list(_unit_evaluations(state, EB1C0))
    cases = [
        valid[:-1],
        [
            routing.TaskDomainAutoNegativeEventEvaluation(
                canonical_event_id=valid[0].canonical_event_id,
                rule_id="UNKNOWN_RULE",
                status=routing.gate.MATCHED_AUTO_NEGATIVE_EXACT,
                reason="synthetic",
            ),
            *valid[1:],
        ],
        [
            routing.TaskDomainAutoNegativeEventEvaluation(
                canonical_event_id=valid[0].canonical_event_id,
                rule_id=routing.gate.RULE_ID,
                status=routing.gate.INVALID_EVIDENCE,
                reason="INVALID_EVIDENCE:synthetic",
            ),
            *valid[1:],
        ],
    ]
    for evaluations in cases:
        route = routing.route_successor_task_domain_review_unit_v1(
            review_unit=unit,
            event_evaluations=evaluations,
            human_unit_state=human,
        )
        assert route.route_status == routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID
        assert route.effective_new_auto_negative is False


def test_partial_unit_gate_match_retains_human_review(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    evaluations = list(_unit_evaluations(state, EB1C0))
    first = evaluations[0]
    evaluations[0] = routing.TaskDomainAutoNegativeEventEvaluation(
        canonical_event_id=first.canonical_event_id,
        rule_id=first.rule_id,
        status=routing.gate.NOT_MATCHED,
        reason="PREDICATE_MISMATCH:synthetic_boundary",
    )
    route = routing.route_successor_task_domain_review_unit_v1(
        review_unit=inputs["unit_by_id"][EB1C0],
        event_evaluations=evaluations,
        human_unit_state=inputs["human_unit_by_id"][EB1C0],
    )
    assert route.auto_negative_event_match_count == 0
    assert route.rule_evidence[0].matched_event_count == 30
    assert route.route_status == routing.HUMAN_REVIEW_REQUIRED
    assert route.effective_new_auto_negative is False


def test_current_human_sha_bound_and_synthetic_change_is_stale(
    artifacts: dict[str, bytes],
) -> None:
    manifest = json.loads(artifacts[routing.MANIFEST])
    payload = (ROOT / routing.gate.HUMAN_DECISIONS_RELATIVE).read_bytes()
    binding = manifest["current_human_snapshot_binding"]["decisions"]
    assert binding["sha256"] == hashlib.sha256(payload).hexdigest()
    assert routing.verify_human_snapshot_payload_binding_v1(manifest, payload)
    with pytest.raises(ValueError, match="SNAPSHOT_STALE"):
        routing.verify_human_snapshot_payload_binding_v1(
            manifest, payload + b" "
        )


def test_published_dtt_artifact_drift_stales_successor_snapshot(
    artifacts: dict[str, bytes],
) -> None:
    manifest = json.loads(artifacts[routing.MANIFEST])
    payloads = {
        path.as_posix(): (ROOT / path).read_bytes()
        for path in routing.DTT_GATE_ARTIFACT_BINDINGS
    }
    assert routing.verify_published_dtt_gate_snapshot_payload_bindings_v1(
        manifest, payloads
    )
    drifted = dict(payloads)
    manifest_path = routing.DTT_GATE_MANIFEST_RELATIVE.as_posix()
    drifted[manifest_path] += b" "
    with pytest.raises(ValueError, match="DTT_GATE_ROUTING_SNAPSHOT_STALE"):
        routing.verify_published_dtt_gate_snapshot_payload_bindings_v1(
            manifest, drifted
        )


def test_artifacts_embed_no_runtime_git_identity_or_timestamp(
    artifacts: dict[str, bytes],
) -> None:
    combined = b"\n".join(artifacts.values()).lower()
    for forbidden in (
        b'"head"',
        b'"origin_main"',
        b'"ahead"',
        b'"behind"',
        b'"execution_timestamp"',
        b'"timestamp"',
    ):
        assert forbidden not in combined


def test_build_does_not_mutate_human_legacy_or_gate_inputs() -> None:
    protected = [
        ROOT / routing.gate.HUMAN_DECISIONS_RELATIVE,
        ROOT / routing.HUMAN_PROGRESS_RELATIVE,
        *[ROOT / path for path in routing.LEGACY_INPUT_SHA256],
        *[ROOT / path for path in routing.GATE_ARTIFACT_BINDINGS],
        *[ROOT / path for path in routing.DTT_GATE_ARTIFACT_BINDINGS],
        ROOT / routing.CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE,
        ROOT / routing.CURRENT_PRODUCTION_AUTHORITY_PUBLICATION_RELATIVE,
    ]
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected
    }
    routing.build_artifacts_v1(repo_root=ROOT)
    assert before == {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected
    }


def _synthetic_rule_evaluations(
    *,
    event_ids: list[str],
    rule_id: str,
    status: str,
) -> list[routing.TaskDomainAutoNegativeEventEvaluation]:
    return [
        routing.TaskDomainAutoNegativeEventEvaluation(
            canonical_event_id=event_id,
            rule_id=rule_id,
            status=status,
            reason=(
                "ALL_EXACT_PREDICATES_MATCHED"
                if status == routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
                else (
                    "INVALID_EVIDENCE:synthetic"
                    if status == routing.gate.INVALID_EVIDENCE
                    else "PREDICATE_MISMATCH:synthetic"
                )
            ),
        )
        for event_id in event_ids
    ]


def test_future_rule_only_full_match_selects_that_rule_with_consistent_audit(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    unit = inputs["unit_by_id"][EB1C0]
    human = inputs["human_unit_by_id"][EB1C0]
    event_ids = unit["canonical_event_ids"]
    rule_a = _synthetic_rule_evaluations(
        event_ids=event_ids, rule_id="RULE_A", status=routing.gate.NOT_MATCHED
    )
    rule_b = _synthetic_rule_evaluations(
        event_ids=event_ids,
        rule_id="RULE_B",
        status=routing.gate.MATCHED_AUTO_NEGATIVE_EXACT,
    )
    route = routing.route_successor_task_domain_review_unit_v1(
        review_unit=unit,
        event_evaluations=[*rule_a, *rule_b],
        human_unit_state=human,
        registered_rule_ids=("RULE_A", "RULE_B"),
    )
    assert route.route_status == routing.AUTO_NEGATIVE_EXACT_FINAL
    assert route.auto_negative_rule_id == "RULE_B"
    assert route.auto_negative_event_match_count == 31
    assert route.gate_unit_all_events_match is True
    assert route.effective_new_auto_negative is True
    assert route.rule_evidence == (
        routing.ExactRuleUnitEvidence("RULE_A", 0, 31, 0, False),
        routing.ExactRuleUnitEvidence("RULE_B", 31, 0, 0, True),
    )


def test_full_match_plus_nonmatching_rule_selects_unique_full_rule(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    unit = inputs["unit_by_id"][EB1C0]
    event_ids = unit["canonical_event_ids"]
    rule_a = _synthetic_rule_evaluations(
        event_ids=event_ids,
        rule_id="RULE_A",
        status=routing.gate.MATCHED_AUTO_NEGATIVE_EXACT,
    )
    rule_b = _synthetic_rule_evaluations(
        event_ids=event_ids, rule_id="RULE_B", status=routing.gate.NOT_MATCHED
    )
    route = routing.route_successor_task_domain_review_unit_v1(
        review_unit=unit,
        event_evaluations=[*rule_a, *rule_b],
        human_unit_state=inputs["human_unit_by_id"][EB1C0],
        registered_rule_ids=("RULE_A", "RULE_B"),
    )
    assert route.route_status == routing.AUTO_NEGATIVE_EXACT_FINAL
    assert route.auto_negative_rule_id == "RULE_A"
    assert route.auto_negative_event_match_count == 31
    assert route.total_gate_invalid_evaluation_count == 0


def test_multiple_full_match_rules_fail_closed_with_explicit_reason(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    unit = inputs["unit_by_id"][EB1C0]
    event_ids = unit["canonical_event_ids"]
    rule_a = _synthetic_rule_evaluations(
        event_ids=event_ids,
        rule_id="RULE_A",
        status=routing.gate.MATCHED_AUTO_NEGATIVE_EXACT,
    )
    rule_b = _synthetic_rule_evaluations(
        event_ids=event_ids,
        rule_id="RULE_B",
        status=routing.gate.MATCHED_AUTO_NEGATIVE_EXACT,
    )
    conflict = routing.route_successor_task_domain_review_unit_v1(
        review_unit=unit,
        event_evaluations=[*rule_a, *rule_b],
        human_unit_state=inputs["human_unit_by_id"][EB1C0],
        registered_rule_ids=("RULE_A", "RULE_B"),
    )
    assert conflict.route_status == routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID
    assert conflict.effective_new_auto_negative is False
    assert "MULTIPLE_EXACT_RULES_FULL_MATCH" in conflict.route_reason


def test_full_match_plus_invalid_secondary_rule_fails_closed(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    unit = inputs["unit_by_id"][EB1C0]
    event_ids = unit["canonical_event_ids"]
    rule_a = _synthetic_rule_evaluations(
        event_ids=event_ids,
        rule_id="RULE_A",
        status=routing.gate.MATCHED_AUTO_NEGATIVE_EXACT,
    )
    rule_b = _synthetic_rule_evaluations(
        event_ids=event_ids, rule_id="RULE_B", status=routing.gate.NOT_MATCHED
    )
    rule_b[0] = routing.TaskDomainAutoNegativeEventEvaluation(
        canonical_event_id=event_ids[0],
        rule_id="RULE_B",
        status=routing.gate.INVALID_EVIDENCE,
        reason="INVALID_EVIDENCE:synthetic",
    )
    route = routing.route_successor_task_domain_review_unit_v1(
        review_unit=unit,
        event_evaluations=[*rule_a, *rule_b],
        human_unit_state=inputs["human_unit_by_id"][EB1C0],
        registered_rule_ids=("RULE_A", "RULE_B"),
    )
    assert route.route_status == routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID
    assert route.total_gate_invalid_evaluation_count == 1
    assert route.effective_new_auto_negative is False


def _synthetic_registration(
    rule_id: str, status: str
) -> routing.ExactAutoNegativeRuleRegistration:
    def evaluator(**_kwargs: object) -> routing.gate.AutoNegativeEvaluationResult:
        return routing.gate.AutoNegativeEvaluationResult(
            rule_id=rule_id,
            status=status,
            reason=(
                "ALL_EXACT_PREDICATES_MATCHED"
                if status == routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
                else "PREDICATE_MISMATCH:synthetic_builder_rule"
            ),
            matched_predicates=(),
        )

    return routing.ExactAutoNegativeRuleRegistration(
        rule_id=rule_id, evaluator=evaluator
    )


def test_builder_and_artifact_schema_support_two_rule_registry() -> None:
    registry = (
        _synthetic_registration("RULE_A", routing.gate.NOT_MATCHED),
        _synthetic_registration("RULE_B", routing.gate.NOT_MATCHED),
    )
    built = routing.build_artifacts_v1(
        repo_root=ROOT,
        registry=registry,
        rule_context_by_id={"RULE_A": {}, "RULE_B": {}},
        override_context_by_id={"RULE_A": object(), "RULE_B": object()},
    )
    manifest = json.loads(built[routing.MANIFEST])
    summary = json.loads(built[routing.SUMMARY])
    event_rows = _csv(built[routing.EVENT_INVENTORY])
    unit_rows = _csv(built[routing.UNIT_INVENTORY])
    assert manifest["integrated_auto_negative_rule_ids"] == ["RULE_A", "RULE_B"]
    assert summary["integrated_auto_negative_rule_count"] == 2
    assert summary["total_rule_event_evaluation_count"] == 246
    assert len(event_rows) == 246
    assert Counter(row["canonical_event_id"] for row in event_rows) == {
        event_id: 2 for event_id in {row["canonical_event_id"] for row in event_rows}
    }
    assert all(
        [row["rule_id"] for row in event_rows[index : index + 2]]
        == ["RULE_A", "RULE_B"]
        for index in range(0, len(event_rows), 2)
    )
    assert len(unit_rows) == 36
    assert all(
        [item["rule_id"] for item in json.loads(row["per_rule_evidence_json"])]
        == ["RULE_A", "RULE_B"]
        for row in unit_rows
    )


def test_actual_current_production_positive_authority_is_bound_and_used(
    state: dict[str, object], artifacts: dict[str, bytes]
) -> None:
    binding = state["bindings"]["current_production_authority_binding"]
    production = state["production_context"]
    manifest = json.loads(artifacts[routing.MANIFEST])
    assert binding["path"] == (
        routing.CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE.as_posix()
    )
    assert binding["schema"] == (
        "covapie_cys_sg_reusable_chemistry_authority_registry_v1"
    )
    assert binding["sha256"] == (
        "c6f150bd82b1ea45121aa96e1fefb6af3be64584117cc462f74b2e10fd1913e9"
    )
    assert binding["authority_count"] == 3
    assert production["audit"]["rule_event_authority_evaluation_count"] == 369
    assert production["positive_event_ids"] == ()
    assert state["override"].current_production_exact_positive_event_ids == frozenset()
    persisted = manifest["current_production_exact_positive_authority_binding"]
    assert persisted["sha256"] == binding["sha256"]
    assert persisted[
        "current_production_exact_positive_authority_event_count"
    ] == 0
    assert persisted["registry_coverage_complete"] is True
    assert persisted["current_production_positive_integration_safe"] is True


def test_frozen_outcome_boolean_alone_is_not_accepted_as_current_authority(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    tampered = deepcopy(inputs["outcome_by_id"])
    event_id = inputs["unit_by_id"][EB1C0]["canonical_event_ids"][0]
    tampered[event_id]["existing_exact_authority_match"] = True
    with pytest.raises(ValueError, match="AUTHORITY_BOOLEAN_MISMATCH"):
        routing.build_current_production_positive_context_v1(
            bindings=state["bindings"],
            event_by_id=inputs["event_by_id"],
            outcome_by_id=tampered,
        )


def test_current_production_authority_drift_stales_snapshot(
    artifacts: dict[str, bytes],
) -> None:
    manifest = json.loads(artifacts[routing.MANIFEST])
    payload = (
        ROOT / routing.CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE
    ).read_bytes()
    assert routing.verify_current_production_positive_snapshot_binding_v1(
        manifest, payload
    )
    with pytest.raises(ValueError, match="PRODUCTION_POSITIVE_ROUTING_SNAPSHOT_STALE"):
        routing.verify_current_production_positive_snapshot_binding_v1(
            manifest, payload + b" "
        )


def test_current_human_positive_runtime_override_blocks_exact_match(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    human = deepcopy(state["bindings"]["current_human"])
    unit = next(item for item in human["units"] if item["review_unit_id"] == EB1C0)
    unit["workflow_status"] = "IN_PROGRESS"
    unit["training_domain_relevance_decision"] = routing.HUMAN_RELEVANT_DECISION
    override = routing.gate.build_runtime_positive_override_context_v1(
        current_human_overlay=human,
        current_human_overlay_sha256="a" * 64,
        outcome_by_id=inputs["outcome_by_id"],
    )
    event_id = unit["events"][0]["canonical_event_id"]
    result = routing.gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=inputs["event_by_id"][event_id],
        outcome=inputs["outcome_by_id"][event_id],
        rule_context=state["context"],
        override_context=override,
    )
    assert result.status == routing.gate.NOT_MATCHED
    assert "no_runtime_positive_override" in routing.gate._reason_failed_predicates(
        result.reason
    )


def test_evaluator_honors_supplied_production_and_explicit_positive_overrides(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    event_id = inputs["unit_by_id"][EB1C0]["canonical_event_ids"][0]
    human = state["bindings"]["current_human"]
    production_outcomes = deepcopy(inputs["outcome_by_id"])
    production_outcomes[event_id]["existing_exact_authority_match"] = True
    contexts = [
        routing.gate.build_runtime_positive_override_context_v1(
            current_human_overlay=human,
            current_human_overlay_sha256="b" * 64,
            outcome_by_id=production_outcomes,
        ),
        routing.gate.build_runtime_positive_override_context_v1(
            current_human_overlay=human,
            current_human_overlay_sha256="c" * 64,
            outcome_by_id=inputs["outcome_by_id"],
            explicit_positive_override_event_ids=(event_id,),
        ),
    ]
    for override in contexts:
        result = routing.gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
            event=inputs["event_by_id"][event_id],
            outcome=inputs["outcome_by_id"][event_id],
            rule_context=state["context"],
            override_context=override,
        )
        assert result.status == routing.gate.NOT_MATCHED


def test_malformed_runtime_override_never_matches(
    state: dict[str, object],
) -> None:
    inputs = state["inputs"]
    event_id = inputs["unit_by_id"][EB1C0]["canonical_event_ids"][0]
    result = routing.gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
        event=inputs["event_by_id"][event_id],
        outcome=inputs["outcome_by_id"][event_id],
        rule_context=state["context"],
        override_context={},  # type: ignore[arg-type]
    )
    assert result.status == routing.gate.INVALID_EVIDENCE


@pytest.mark.parametrize("exception", [KeyboardInterrupt, SystemExit])
def test_dispatch_propagates_base_exceptions(exception: type[BaseException]) -> None:
    def evaluator(**_kwargs: object):
        raise exception()

    registration = routing.ExactAutoNegativeRuleRegistration(
        rule_id="NEG_SYNTHETIC",
        evaluator=evaluator,
    )
    with pytest.raises(exception):
        routing.dispatch_exact_auto_negative_rules_v1(
            event={"canonical_event_id": "EVENT"},
            outcome={},
            rule_context_by_id={"NEG_SYNTHETIC": {}},
            override_context_by_id={"NEG_SYNTHETIC": object()},
            registry=(registration,),
        )


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    routing.materialize_v1(repo_root=ROOT, output_root=first)
    routing.materialize_v1(repo_root=ROOT, output_root=second)
    assert {
        name: (first / name).read_bytes() for name in routing.OUTPUT_FILENAMES
    } == {name: (second / name).read_bytes() for name in routing.OUTPUT_FILENAMES}


def test_materialized_repository_artifacts_match_builder(
    artifacts: dict[str, bytes],
) -> None:
    assert {name: (OUTPUT / name).read_bytes() for name in routing.OUTPUT_FILENAMES} == artifacts
