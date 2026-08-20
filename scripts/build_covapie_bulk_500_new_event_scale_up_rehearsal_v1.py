#!/usr/bin/env python3
"""Materialize the deterministic 500-new-event scale-up rehearsal plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import covapie_bulk_500_new_event_scale_up_rehearsal_v1 as rehearsal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--verify-deterministic-replay", action="store_true")
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    rehearsal.verify_task_repository_baseline_v1(repo_root)
    summary = rehearsal.materialize_v1(repo_root=repo_root)
    observation = rehearsal.observe_current_cache_v1(repo_root=repo_root)
    result: dict[str, object] = {
        "schema_version": summary["schema_version"],
        "historical_250_exact_prefix_of_500": summary["cohort"][
            "historical_250_exact_prefix_of_500"
        ],
        "cumulative_new_event_count": summary["cohort"][
            "cumulative_new_event_count"
        ],
        "incremental_new_event_count": summary["cohort"][
            "incremental_new_event_count"
        ],
        "cumulative_500_unique_pdb_count": summary[
            "acquisition_identity_counts"
        ]["cumulative_500_unique_pdb_count"],
        "cumulative_500_unique_ccd_count": summary[
            "acquisition_identity_counts"
        ]["cumulative_500_unique_ccd_count"],
        "current_cache_observation": observation,
        "network_performed": summary["network_performed"],
        "ready_for_controlled_500_event_execution": summary[
            "ready_for_controlled_500_event_execution"
        ],
        "ready_for_gpt_review": summary["ready_for_gpt_review"],
    }
    if arguments.verify_deterministic_replay:
        result["deterministic_replay_sha256"] = (
            rehearsal.verify_deterministic_replay_v1(repo_root)
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
