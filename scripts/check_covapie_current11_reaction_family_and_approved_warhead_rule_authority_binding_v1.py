#!/usr/bin/env python3
"""Check the Current11 reaction-family and approved-rule binding gate."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1 import (  # noqa: E402
    evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1,
)


BASE = "0e36e3131750dcb99f806ec635afeae2b0b0dc88"


def main() -> int:
    first = evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
        repo_root=ROOT,
    )
    second = evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
        repo_root=ROOT,
    )
    first_bytes = json.dumps(
        first, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    second_bytes = json.dumps(
        second, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    profile = first["binding_lifecycle_profile"]
    commit = first["binding_commit"]
    origin = first["origin_main"]
    ahead, behind = first["ahead"], first["behind"]
    lifecycle_valid = False
    if profile == "binding_precommit_candidate":
        lifecycle_valid = (
            commit is None
            and first["binding_committed"] is False
            and first["binding_published"] is False
            and first["ready_for_binding_commit_review"] is True
            and origin == BASE and (ahead, behind) == (0, 0)
        )
    elif profile == "binding_committed_unpushed":
        lifecycle_valid = (
            isinstance(commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and commit != BASE and first["binding_committed"] is True
            and first["binding_published"] is False
            and first["ready_for_binding_commit_review"] is False
            and origin == BASE and (ahead, behind) == (1, 0)
        )
    elif profile == "binding_published_successor":
        lifecycle_valid = (
            isinstance(commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and commit != BASE and first["binding_committed"] is True
            and first["binding_published"] is True
            and first["ready_for_binding_commit_review"] is False
            and isinstance(origin, str)
            and re.fullmatch(r"[0-9a-f]{40}", origin) is not None
            and type(ahead) is int and ahead >= 0
            and type(behind) is int and behind >= 0
        )
    if (
        first_bytes != second_bytes
        or not lifecycle_valid
        or first["current11_sample_count"] != 11
        or first["reaction_family_authority_bound_count"] != 0
        or first["approved_warhead_rule_authority_bound_count"] != 0
        or first["boundary_review_completed_count"] != 11
        or first["reaction_family_identity_explicitly_attested_count"] != 0
        or first["warhead_rule_full_semantics_explicitly_attested_count"] != 0
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
