#!/usr/bin/env python3
"""Materialize the current-human-bound successor task-domain routing V1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as routing,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--verify-deterministic-replay", action="store_true")
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    summary = routing.materialize_v1(repo_root=repo_root)
    result: dict[str, object] = {
        "schema_version": summary["schema_version"],
        "snapshot_semantics": summary["snapshot_semantics"],
        "candidate_events": summary["candidate_events"],
        "candidate_units": summary["candidate_units"],
        "raw_gate_matched_events": summary["raw_gate_matched_events"],
        "raw_gate_matched_units": summary["raw_gate_matched_units"],
        "effective_new_auto_negative_events": summary[
            "effective_new_auto_negative_events"
        ],
        "effective_new_auto_negative_units": summary[
            "effective_new_auto_negative_units"
        ],
        "effective_task_domain_human_review_required_units": summary[
            "effective_task_domain_human_review_required_units"
        ],
        "total_rule_event_evaluation_count": summary[
            "total_rule_event_evaluation_count"
        ],
        "current_production_exact_positive_authority_event_count": summary[
            "current_production_exact_positive_authority_event_count"
        ],
        "live_routing_ready": summary["live_routing_ready"],
        "ready_for_gpt_review": summary["ready_for_gpt_review"],
    }
    if arguments.verify_deterministic_replay:
        result["deterministic_replay_sha256"] = (
            routing.verify_deterministic_replay_v1(repo_root)
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
