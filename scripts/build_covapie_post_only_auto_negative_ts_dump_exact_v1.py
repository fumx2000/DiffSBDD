#!/usr/bin/env python3
"""Materialize the exact TS/dUMP task-domain negative shadow gate V1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import covapie_post_only_auto_negative_ts_dump_exact_v1 as gate


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--verify-deterministic-replay", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    repo_root = arguments.repo_root.resolve()
    cache_root = (
        arguments.cache_root.resolve()
        if arguments.cache_root is not None
        else repo_root.parent / gate.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    summary = gate.materialize_v1(repo_root=repo_root, cache_root=cache_root)
    result: dict[str, object] = {
        "rule_id": summary["rule_id"],
        "implementation_mode": summary["implementation_mode"],
        "candidate_event_count": summary["candidate_event_count"],
        "observed_shadow_matched_event_count": summary[
            "observed_shadow_matched_event_count"
        ],
        "observed_shadow_matched_unit_count": summary[
            "observed_shadow_matched_unit_count"
        ],
        "readiness_mode": summary["readiness_mode"],
        "live_integration_ready": summary["live_integration_ready"],
        "invalid_evidence_count": summary["invalid_evidence_count"],
        "ready_for_gpt_review": summary["ready_for_gpt_review"],
    }
    if arguments.verify_deterministic_replay:
        result["deterministic_replay_sha256"] = gate.verify_deterministic_replay_v1(
            repo_root, cache_root
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
