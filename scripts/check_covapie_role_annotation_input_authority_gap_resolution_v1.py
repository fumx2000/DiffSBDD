#!/usr/bin/env python3
"""Check the Current11 role-annotation input-authority resolution gate."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_role_annotation_input_authority_gap_resolution_v1 import (  # noqa: E402
    evaluate_covapie_role_annotation_input_authority_gap_resolution_v1,
)


def main() -> int:
    repo_root = ROOT
    first = evaluate_covapie_role_annotation_input_authority_gap_resolution_v1(
        repo_root=repo_root
    )
    second = evaluate_covapie_role_annotation_input_authority_gap_resolution_v1(
        repo_root=repo_root
    )
    first_bytes = json.dumps(
        first, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    second_bytes = json.dumps(
        second, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    profile = first["authority_lifecycle_profile"]
    commit = first["authority_commit"]
    origin = first["origin_main"]
    ahead = first["ahead"]
    behind = first["behind"]
    lifecycle_valid = False
    if profile == "authority_precommit_candidate":
        lifecycle_valid = (
            commit is None
            and first["authority_committed"] is False
            and first["authority_published"] is False
            and first["ready_for_authority_commit_review"] is True
            and origin == "e206a732d1a72ac1a45002a3bf9c5ae8d659f692"
            and (ahead, behind) == (0, 0)
        )
    elif profile == "authority_committed_unpushed":
        lifecycle_valid = (
            isinstance(commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and first["authority_committed"] is True
            and first["authority_published"] is False
            and first["ready_for_authority_commit_review"] is False
            and origin == "e206a732d1a72ac1a45002a3bf9c5ae8d659f692"
            and (ahead, behind) == (1, 0)
        )
    elif profile == "authority_published_successor":
        lifecycle_valid = (
            isinstance(commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and first["authority_committed"] is True
            and first["authority_published"] is True
            and first["ready_for_authority_commit_review"] is False
            and isinstance(origin, str)
            and re.fullmatch(r"[0-9a-f]{40}", origin) is not None
            and type(ahead) is int and ahead >= 0
            and type(behind) is int and behind >= 0
        )
    if (
        first_bytes != second_bytes
        or not lifecycle_valid
        or first["current11_role_proposal_input_ready_count"] != 0
        or first["current11_minimal_seed_input_ready_count"] != 0
        or first["warhead_boundary_human_review_completed_count"] != 11
        or first["role_seed_human_gold_review_completed_count"] != 0
        or first["ready_for_current11_role_annotation_proposal_generation"] is not False
        or first["ready_for_current11_minimal_seed_proposal_generation"] is not False
        or first["ready_for_training"] is not False
        or first["commit_created"] is not False
        or first["push_performed"] is not False
    ):
        raise SystemExit(1)
    print(first_bytes.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
