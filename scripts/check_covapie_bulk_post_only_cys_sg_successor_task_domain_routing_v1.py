#!/usr/bin/env python3
"""Fail-closed checker for successor task-domain routing V1."""

from __future__ import annotations

from collections import Counter
import csv
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as routing,
)

DTT_S1_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_A3782D89BDEF47C1"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _csv(path: Path, header: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _assert(tuple(reader.fieldnames or ()) == tuple(header), path.name + " header")
        rows = list(reader)
    _assert(
        all(
            tuple(row) == tuple(header)
            and all(value is not None for value in row.values())
            for row in rows
        ),
        path.name + " row schema",
    )
    return rows


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return os.path.isabs(value)
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


def _contains_key(value: object, forbidden: str) -> bool:
    if isinstance(value, Mapping):
        return forbidden in value or any(
            _contains_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


def check_v1(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_root = repo_root / routing.OUTPUT_ROOT_RELATIVE
    _assert(output_root.is_dir(), "output directory missing")
    _assert(
        {path.name for path in output_root.iterdir() if path.is_file()}
        == set(routing.OUTPUT_FILENAMES),
        "output file set mismatch",
    )
    _assert(
        not any(
            path.is_file() and path.suffix in {".tmp", ".part"}
            for path in output_root.iterdir()
        ),
        "temporary output remains",
    )

    routing.verify_repository_binding_v1(repo_root)
    bindings = routing.verify_predecessor_bindings_v1(repo_root)
    routing.verify_current_snapshot_v1(repo_root)
    expected = routing.build_artifacts_v1(repo_root=repo_root)
    for name in routing.OUTPUT_FILENAMES:
        _assert(
            (output_root / name).read_bytes() == expected[name],
            "deterministic replay mismatch: " + name,
        )

    manifest = json.loads((output_root / routing.MANIFEST).read_bytes())
    summary = json.loads((output_root / routing.SUMMARY).read_bytes())
    event_rows = _csv(output_root / routing.EVENT_INVENTORY, routing.EVENT_HEADER)
    unit_rows = _csv(output_root / routing.UNIT_INVENTORY, routing.UNIT_HEADER)
    _assert(not _contains_absolute_path(manifest), "manifest absolute path")
    _assert(not _contains_absolute_path(summary), "summary absolute path")
    for artifact in (manifest, summary):
        for forbidden in (
            "head",
            "origin_main",
            "ahead",
            "behind",
            "timestamp",
            "execution_timestamp",
        ):
            _assert(
                not _contains_key(artifact, forbidden),
                "runtime Git/timestamp key persisted: " + forbidden,
            )
    _assert(manifest["schema_version"] == routing.SCHEMA_VERSION, "manifest schema")
    _assert(manifest["stage"] == routing.STAGE, "manifest stage")
    _assert(
        manifest["snapshot_semantics"] == routing.SNAPSHOT_SEMANTICS,
        "manifest snapshot semantics",
    )
    _assert(
        manifest["base_successor_commit_ancestor"]
        == routing.BASE_SUCCESSOR_COMMIT_ANCESTOR,
        "base successor ancestor",
    )
    _assert(
        manifest["legacy_candidate_input_bindings"] == bindings["legacy"],
        "legacy bindings",
    )
    _assert(
        manifest["published_ts_dump_gate_artifact_bindings"]
        == bindings["published_gate"],
        "gate bindings",
    )
    _assert(
        manifest["published_dtt_gate_artifact_bindings"]
        == bindings["published_dtt_gate"],
        "DTT gate bindings",
    )
    _assert(
        manifest["dtt_gate_publication"]
        == {
            "commit": routing.DTT_GATE_PUBLICATION_COMMIT,
            "subject": routing.DTT_GATE_PUBLICATION_SUBJECT,
            "required_as_ancestor_of_synchronized_head_and_origin_main": True,
        },
        "DTT publication provenance",
    )
    _assert(
        manifest["current_human_snapshot_binding"]
        == bindings["current_human_snapshot"],
        "human bindings",
    )
    inputs = routing._load_routing_inputs_v1(repo_root, bindings)
    production_context = routing.build_current_production_positive_context_v1(
        bindings=bindings,
        event_by_id=inputs["event_by_id"],
        outcome_by_id=inputs["outcome_by_id"],
    )
    _assert(
        manifest["current_production_exact_positive_authority_binding"]
        == {
            **bindings["current_production_authority_binding"],
            **production_context["audit"],
        },
        "current production-positive authority binding",
    )
    _assert(
        manifest["integrated_auto_negative_rule_ids"]
        == [routing.gate.RULE_ID, routing.dtt_gate.RULE_ID],
        "integrated rule registry",
    )
    rule_ids = tuple(manifest["integrated_auto_negative_rule_ids"])
    _assert(
        routing.HUMAN_DEFERRED_DECISION
        in manifest["human_vocabulary"]["training_domain_relevance_decisions"],
        "official deferred vocabulary",
    )
    _assert(
        "EVERY_EVENT" in manifest["unit_aggregation_policy"],
        "all-event policy",
    )
    _assert(
        manifest["production_authority_created"] is False
        and manifest["training_materialization_performed"] is False
        and manifest["current_production_positive_integration_safe"] is True
        and manifest["live_routing_ready"] is True,
        "manifest safety flags",
    )

    _assert(len(event_rows) == 123 * len(rule_ids), "rule-event row count")
    _assert(len(unit_rows) == 36, "unit row count")
    _assert(
        len({(row["canonical_event_id"], row["rule_id"]) for row in event_rows})
        == len(event_rows),
        "rule-event uniqueness",
    )
    event_rule_coverage: dict[str, list[str]] = {}
    event_route: dict[str, str] = {}
    for row in event_rows:
        event_rule_coverage.setdefault(row["canonical_event_id"], []).append(
            row["rule_id"]
        )
        prior = event_route.setdefault(
            row["canonical_event_id"], row["unit_final_task_domain_route"]
        )
        _assert(prior == row["unit_final_task_domain_route"], "event route drift")
    _assert(
        len(event_rule_coverage) == 123
        and all(tuple(values) == rule_ids for values in event_rule_coverage.values()),
        "ordered rule-event Cartesian coverage",
    )
    _assert(
        len({row["review_unit_id"] for row in unit_rows}) == 36,
        "unit uniqueness",
    )
    _assert(
        Counter(event_route.values())
        == Counter(
            {
                routing.HUMAN_NOT_RELEVANT_FINAL: 30,
                routing.HUMAN_RELEVANT_FINAL: 5,
                routing.AUTO_NEGATIVE_EXACT_FINAL: 32,
                routing.HUMAN_REVIEW_REQUIRED: 56,
            }
        ),
        "123-event route reconciliation",
    )
    _assert(
        Counter(row["final_task_domain_route"] for row in unit_rows)
        == Counter(
            {
                routing.HUMAN_NOT_RELEVANT_FINAL: 7,
                routing.HUMAN_RELEVANT_FINAL: 3,
                routing.AUTO_NEGATIVE_EXACT_FINAL: 2,
                routing.HUMAN_REVIEW_REQUIRED: 24,
            }
        ),
        "36-unit route reconciliation",
    )
    _assert(
        sum(
            row["rule_id"] == routing.gate.RULE_ID
            and row["gate_event_status"]
            == routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
            for row in event_rows
        )
        == 47,
        "raw TS/dUMP gate matched events",
    )
    _assert(
        sum(
            row["rule_id"] == routing.dtt_gate.RULE_ID
            and row["gate_event_status"]
            == routing.gate.MATCHED_AUTO_NEGATIVE_EXACT
            for row in event_rows
        )
        == 2,
        "raw DTT gate matched events",
    )
    _assert(
        sum(value == routing.AUTO_NEGATIVE_EXACT_FINAL for value in event_route.values())
        == 32,
        "effective auto-negative events",
    )
    _assert(
        sum(
            row["total_gate_invalid_evaluation_count"] != "0"
            for row in unit_rows
        )
        == 0,
        "gate invalid units",
    )
    for row in unit_rows:
        evidence = json.loads(row["per_rule_evidence_json"])
        _assert(
            [item["rule_id"] for item in evidence] == list(rule_ids),
            "unit per-rule evidence order",
        )
        _assert(
            all(
                item["matched_event_count"]
                + item["not_matched_event_count"]
                + item["invalid_event_count"]
                == int(row["event_count"])
                for item in evidence
            ),
            "unit per-rule evidence reconciliation",
        )
        _assert(
            sum(item["invalid_event_count"] for item in evidence)
            == int(row["total_gate_invalid_evaluation_count"]),
            "unit total invalid evidence",
        )
    unit_by_id = {row["review_unit_id"]: row for row in unit_rows}
    eb1c0 = unit_by_id[routing.gate.SIBLING_UNIT_ID]
    calibration = unit_by_id[routing.gate.CALIBRATION_UNIT_ID]
    dtt_s1 = unit_by_id[DTT_S1_UNIT_ID]
    dtt_s4 = unit_by_id[routing.dtt_gate.CALIBRATION_UNIT_ID]
    dtu = unit_by_id[routing.dtt_gate.DTU_COUNTEREXAMPLE_UNIT_ID]
    _assert(
        eb1c0["selected_auto_negative_rule_id"] == routing.gate.RULE_ID
        and eb1c0["selected_rule_matched_event_count"] == "31"
        and eb1c0["selected_rule_all_events_match"] == "true"
        and eb1c0["final_task_domain_route"]
        == routing.AUTO_NEGATIVE_EXACT_FINAL,
        "EB1C0 selected-rule integration",
    )
    calibration_evidence = json.loads(calibration["per_rule_evidence_json"])
    _assert(
        calibration["selected_auto_negative_rule_id"] == ""
        and calibration["final_task_domain_route"]
        == routing.HUMAN_NOT_RELEVANT_FINAL
        and calibration_evidence[0]["matched_event_count"] == 16
        and calibration_evidence[0]["all_events_match"] is True,
        "2AAZ human-negative precedence with raw rule evidence",
    )
    dtt_s1_evidence = json.loads(dtt_s1["per_rule_evidence_json"])
    _assert(
        dtt_s1["selected_auto_negative_rule_id"] == routing.dtt_gate.RULE_ID
        and dtt_s1["selected_rule_matched_event_count"] == "1"
        and dtt_s1["selected_rule_all_events_match"] == "true"
        and dtt_s1["final_task_domain_route"]
        == routing.AUTO_NEGATIVE_EXACT_FINAL
        and dtt_s1_evidence[0]["matched_event_count"] == 0
        and dtt_s1_evidence[1]["matched_event_count"] == 1,
        "DTT-S1 selected-rule integration",
    )
    dtt_s4_evidence = json.loads(dtt_s4["per_rule_evidence_json"])
    _assert(
        dtt_s4["selected_auto_negative_rule_id"] == ""
        and dtt_s4["final_task_domain_route"]
        == routing.HUMAN_NOT_RELEVANT_FINAL
        and dtt_s4_evidence[1]["matched_event_count"] == 1
        and dtt_s4_evidence[1]["all_events_match"] is True,
        "DTT-S4 human-negative precedence",
    )
    dtu_evidence = json.loads(dtu["per_rule_evidence_json"])
    _assert(
        dtu["selected_auto_negative_rule_id"] == ""
        and dtu["final_task_domain_route"] == routing.HUMAN_REVIEW_REQUIRED
        and dtu_evidence[1]["matched_event_count"] == 0
        and dtu_evidence[1]["all_events_match"] is False,
        "DTU DTT-rule safety",
    )
    _assert(
        all(row["human_overlay_mutated"] == "false" for row in unit_rows),
        "human overlay mutation marker",
    )

    expected_summary = {
        "candidate_events": 123,
        "candidate_units": 36,
        "human_overlay_reviewed_units": 10,
        "human_overlay_unreviewed_units": 26,
        "human_not_relevant_final_units": 7,
        "human_relevant_final_units": 3,
        "raw_gate_matched_events": 47,
        "raw_gate_matched_units": 2,
        "effective_new_auto_negative_events": 32,
        "effective_new_auto_negative_units": 2,
        "effective_task_domain_resolved_units": 12,
        "effective_task_domain_human_review_required_units": 24,
        "effective_task_domain_human_review_required_events": 56,
        "gate_invalid_units": 0,
        "total_rule_event_evaluation_count": 246,
        "matched_rule_event_evaluation_count": 49,
        "invalid_rule_event_evaluation_count": 0,
        "fully_matched_rule_unit_pairs": 4,
        "multiple_full_match_conflict_units": 0,
        "ts_dump_effective_auto_negative_events": 31,
        "ts_dump_effective_auto_negative_units": 1,
        "dtt_incremental_effective_auto_negative_events": 1,
        "dtt_incremental_effective_auto_negative_units": 1,
        "current_production_exact_positive_authority_event_count": 0,
    }
    for field, expected_value in expected_summary.items():
        _assert(summary.get(field) == expected_value, "summary field: " + field)
    _assert(
        summary["raw_gate_metric_semantics"] == "LEGACY_TS_DUMP_RULE_ONLY"
        and summary["raw_rule_metrics_by_rule"]
        == {
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
        },
        "per-rule raw metrics",
    )
    _assert(
        summary["effective_auto_negative_metrics_by_rule"]
        == {
            routing.gate.RULE_ID: {"events": 31, "units": 1},
            routing.dtt_gate.RULE_ID: {"events": 1, "units": 1},
        },
        "per-rule effective metrics",
    )
    for field in (
        "human_overlay_modified",
        "legacy_triage_modified",
        "gate_artifacts_modified",
        "ts_dump_shadow_artifacts_modified",
        "dtt_shadow_artifacts_modified",
        "production_authority_created",
        "training_materialization_performed",
        "production_materialization_performed",
    ):
        _assert(summary[field] is False, "summary safety field: " + field)
    _assert(summary["ready_for_gpt_review"] is True, "readiness false")
    _assert(summary["live_routing_ready"] is True, "live routing readiness false")
    _assert(
        summary["current_production_positive_integration_safe"] is True,
        "current production-positive integration",
    )
    _assert(
        summary["recommended_next_step_exactly"]
        == (
            "gpt_audit_DTT_successor_integration_then_commit_push_two_rule_"
            "successor_snapshot"
        ),
        "next step",
    )
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    result = check_v1(arguments.repo_root)
    _assert(result["ready_for_gpt_review"] is True, "readiness assertion")
    print(
        json.dumps(
            {
                "check": "PASS",
                "raw_gate_matched_events": result["raw_gate_matched_events"],
                "effective_new_auto_negative_events": result[
                    "effective_new_auto_negative_events"
                ],
                "effective_task_domain_human_review_required_units": result[
                    "effective_task_domain_human_review_required_units"
                ],
                "total_rule_event_evaluation_count": result[
                    "total_rule_event_evaluation_count"
                ],
                "current_production_exact_positive_authority_event_count": result[
                    "current_production_exact_positive_authority_event_count"
                ],
                "live_routing_ready": result["live_routing_ready"],
                "ready_for_gpt_review": result["ready_for_gpt_review"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
