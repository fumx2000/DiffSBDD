#!/usr/bin/env python3
"""Materialize the read-only CovaPIE post-only CYS-SG triage artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import (
    covapie_bulk_post_only_cys_sg_training_candidate_triage_v1 as triage,
)


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
        else repo_root.parent / triage.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    summary = triage.materialize_v1(repo_root=repo_root, cache_root=cache_root)
    result = {
        "population": summary["population"],
        "post_supervision_readiness": summary["post_supervision_readiness"],
        "training_domain_relevance": summary["training_domain_relevance"],
        "human_review_workload": summary["human_review_workload"],
        "ready_for_gpt_review": summary["ready_for_gpt_review"],
    }
    if arguments.verify_deterministic_replay:
        result["deterministic_replay_sha256"] = triage.verify_deterministic_replay_v1(
            repo_root=repo_root, cache_root=cache_root
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
