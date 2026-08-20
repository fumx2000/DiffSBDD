#!/usr/bin/env python3
"""Fail-closed checker for the post-only CYS-SG review workspace V1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import covapie_bulk_post_only_cys_sg_human_review_v1 as review


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--require-initial", action="store_true")
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    output_root = arguments.output_root.resolve() if arguments.output_root else None
    result = review.check_workspace_v1(
        repo_root,
        output_root,
        require_initial=arguments.require_initial,
    )
    if result["workspace_valid"] is not True:
        raise AssertionError("workspace_valid was not asserted")
    if result["production_authority_created"] is not False:
        raise AssertionError("production authority safety assertion failed")
    if result["training_materialization_performed"] is not False:
        raise AssertionError("training materialization safety assertion failed")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
