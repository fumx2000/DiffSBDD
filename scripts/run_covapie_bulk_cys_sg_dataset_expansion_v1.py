#!/usr/bin/env python3
"""Run the bounded, review-only CovaPIE bulk CYS-SG pilot V1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--verify-deterministic-replay", action="store_true")
    parser.add_argument(
        "--regressions-passed",
        action="store_true",
        help="assert the required focused and predecessor regressions passed before materialization",
    )
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    repo_root = arguments.repo_root.resolve()
    configured = os.environ.get("COVAPIE_BULK_CACHE_ROOT")
    cache_root = (
        arguments.cache_root.resolve()
        if arguments.cache_root is not None
        else Path(configured).resolve()
        if configured
        else repo_root.parent / "covapie-state" / "bulk-multisource-cys-sg-v1"
    )
    summary = bulk.materialize_covapie_bulk_cys_sg_dataset_expansion_v1(
        repo_root=repo_root,
        cache_root=cache_root,
        regressions_pass=arguments.regressions_passed,
    )
    if arguments.verify_deterministic_replay:
        summary["deterministic_replay_sha256"] = (
            bulk.verify_repository_output_determinism_v1(
                repo_root=repo_root, cache_root=cache_root,
                regressions_pass=arguments.regressions_passed,
            )
        )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
