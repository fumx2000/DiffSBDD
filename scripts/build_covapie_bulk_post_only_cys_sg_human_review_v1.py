#!/usr/bin/env python3
"""Initialize an absent review workspace or verify an exact empty one."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import covapie_bulk_post_only_cys_sg_human_review_v1 as review


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--verify-deterministic-replay", action="store_true")
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    output_root = arguments.output_root.resolve() if arguments.output_root else None
    initialization = review.materialize_v1(repo_root, output_root)
    result: dict[str, object] = {
        "schema_version": review.SCHEMA_VERSION,
        "operation": "INITIALIZE_IF_ABSENT_OR_VERIFY_EXACT_INITIAL_WORKSPACE",
        "already_initialized": initialization["already_initialized"],
        "files": initialization["files"],
        "human_decisions_populated": 0,
        "force_reset_available": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
    }
    if arguments.verify_deterministic_replay:
        result["deterministic_replay_sha256"] = (
            review.verify_deterministic_replay_v1(repo_root)
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
