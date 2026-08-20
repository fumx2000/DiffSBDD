#!/usr/bin/env python3
"""Show one concise machine-evidence card plus current overlay state."""

from __future__ import annotations

import argparse
from pathlib import Path

from covalent_ext import covapie_bulk_post_only_cys_sg_human_review_v1 as review


def main() -> None:
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--next", action="store_true")
    selection.add_argument("--unit-id")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    arguments = parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    output_root = arguments.output_root.resolve() if arguments.output_root else None
    unit_id = (
        review.next_review_unit_id_v1(repo_root, output_root)
        if arguments.next
        else str(arguments.unit_id)
    )
    print("next_review_unit_id=" + unit_id if arguments.next else "review_unit_id=" + unit_id)
    print(review.render_review_card_v1(repo_root, unit_id, output_root), end="")


if __name__ == "__main__":
    main()
