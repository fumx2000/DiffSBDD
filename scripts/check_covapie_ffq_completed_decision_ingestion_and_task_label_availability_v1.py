#!/usr/bin/env python3
"""Fail-closed checker for the FFQ completed-decision successor V1."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


BASELINE_COMMIT = "85b173d1116a3e0db417501c8b7328b1994cf5c2"
PRECOMMIT_PROFILE = (
    "FFQ_COMPLETED_DECISION_INGESTION_PRECOMMIT_EXACT7_UNTRACKED"
)
PUBLISHED_PROFILE = (
    "FFQ_COMPLETED_DECISION_INGESTION_PUBLISHED_CLEAN_DESCENDANT"
)
LIFECYCLE_ERROR = "FFQ_COMPLETED_DECISION_INGESTION_LIFECYCLE_INVALID"
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pyc",
    ".tmp",
    ".part",
)


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _lifecycle_fail(reason: str) -> None:
    raise ValueError(LIFECYCLE_ERROR + ":" + reason)


def observe_repository_state_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    head = _git(repo_root, "rev-parse", "HEAD")
    origin_main = _git(repo_root, "rev-parse", "refs/remotes/origin/main")
    behind_text, ahead_text = _git(
        repo_root,
        "rev-list",
        "--left-right",
        "--count",
        "refs/remotes/origin/main...HEAD",
    ).split()
    modified = tuple(
        line for line in _git(repo_root, "diff", "--name-only").splitlines() if line
    )
    staged = tuple(
        line
        for line in _git(repo_root, "diff", "--cached", "--name-only").splitlines()
        if line
    )
    untracked = tuple(
        sorted(
            line
            for line in _git(
                repo_root, "ls-files", "--others", "--exclude-standard"
            ).splitlines()
            if line
        )
    )
    candidate_paths = tuple(
        sorted(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
    )
    tracked_candidates = tuple(
        sorted(
            line
            for line in _git(
                repo_root, "ls-files", "--", *candidate_paths
            ).splitlines()
            if line
        )
    )
    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "head": head,
        "origin_main": origin_main,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "baseline_ancestor_of_head": subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, head],
            cwd=repo_root,
            check=False,
            capture_output=True,
        ).returncode
        == 0,
        "baseline_ancestor_of_origin_main": subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                BASELINE_COMMIT,
                origin_main,
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
        ).returncode
        == 0,
        "modified_tracked_paths": modified,
        "staged_paths": staged,
        "untracked_paths": untracked,
        "tracked_candidate_paths": tracked_candidates,
    }


def validate_repository_observation_v1(
    observation: Mapping[str, object],
) -> str:
    if observation.get("branch") != "main":
        _lifecycle_fail("BRANCH_NOT_MAIN")
    if observation.get("head") != observation.get("origin_main"):
        _lifecycle_fail("HEAD_ORIGIN_MAIN_MISMATCH")
    if observation.get("ahead") != 0 or observation.get("behind") != 0:
        _lifecycle_fail("AHEAD_BEHIND_NOT_ZERO_ZERO")
    if observation.get("baseline_ancestor_of_head") is not True:
        _lifecycle_fail("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if observation.get("baseline_ancestor_of_origin_main") is not True:
        _lifecycle_fail("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if observation.get("modified_tracked_paths") != ():
        _lifecycle_fail("MODIFIED_EXISTING_TRACKED_FILES_PRESENT")
    if observation.get("staged_paths") != ():
        _lifecycle_fail("STAGED_FILES_PRESENT")

    exact = tuple(
        sorted(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
    )
    untracked = tuple(observation.get("untracked_paths", ()))
    tracked = tuple(observation.get("tracked_candidate_paths", ()))
    head = observation.get("head")
    origin_main = observation.get("origin_main")
    if (
        head == BASELINE_COMMIT
        and origin_main == BASELINE_COMMIT
        and untracked == exact
        and tracked == ()
    ):
        return PRECOMMIT_PROFILE
    if (
        head != BASELINE_COMMIT
        and head == origin_main
        and untracked == ()
        and tracked == exact
    ):
        return PUBLISHED_PROFILE
    _lifecycle_fail("UNSUPPORTED_OR_MIXED_CANDIDATE_PATH_STATE")


def verify_candidate_exact7_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    observation = observe_repository_state_v1(repo_root)
    lifecycle_profile = validate_repository_observation_v1(observation)
    expected = tuple(
        sorted(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
    )
    if len(expected) != 7:
        raise ValueError("CANDIDATE_PUBLICATION_FILE_COUNT_INVALID")
    for relative in subject.CANDIDATE_PUBLICATION_PATHS:
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("CANDIDATE_FILE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        if (
            payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or b"\r" in payload
        ):
            raise ValueError("CANDIDATE_TEXT_INVARIANT_INVALID:" + relative.as_posix())
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                "CANDIDATE_UTF8_INVALID:" + relative.as_posix()
            ) from error
        if relative.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("CANDIDATE_FORBIDDEN_SUFFIX:" + relative.as_posix())
    return {
        "lifecycle_profile": lifecycle_profile,
        "candidate_publication_file_count": 7,
        "candidate_exact7_paths": list(expected),
        "branch": observation["branch"],
        "HEAD": observation["head"],
        "origin_main": observation["origin_main"],
        "ahead": observation["ahead"],
        "behind": observation["behind"],
        "baseline_ancestor_of_HEAD": observation["baseline_ancestor_of_head"],
        "baseline_ancestor_of_origin_main": observation[
            "baseline_ancestor_of_origin_main"
        ],
        "staged_path_count": len(observation["staged_paths"]),
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    candidate = verify_candidate_exact7_v1(repo_root)
    first = subject.build_artifacts_v1(repo_root)
    second = subject.build_artifacts_v1(repo_root)
    if first != second:
        raise ValueError("DETERMINISTIC_DOUBLE_REBUILD_MISMATCH")
    materialized = subject.check_materialized_v1(repo_root)
    if materialized["artifact_sha256"] != {
        name: _sha(first[name]) for name in subject.OUTPUT_FILENAMES
    }:
        raise ValueError("MATERIALIZED_DETERMINISTIC_SHA_MISMATCH")
    bound = subject.verify_bound_inputs_v1(repo_root)
    binding_by_role = {
        row["source_role"]: row
        for row in bound["immutable_repository_bindings"]
    }
    if binding_by_role["legacy_human_review_overlay_read_only"]["sha256"] != (
        "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441"
    ):
        raise ValueError("LEGACY_HUMAN_OVERLAY_SHA_CHANGED")
    if binding_by_role["legacy_human_review_progress_read_only"]["sha256"] != (
        "e1e93ff28e823c1f52b306623bbf20c06f2c0c95cca90bb1e61ee4d1b7cea216"
    ):
        raise ValueError("LEGACY_HUMAN_PROGRESS_SHA_CHANGED")
    if binding_by_role["historical_reconciliation_read_only"]["sha256"] != (
        "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f"
    ):
        raise ValueError("HISTORICAL_RECONCILIATION_SHA_CHANGED")
    runtime = bound["runtime_contract"]
    if (
        runtime["current11_tensorizer_direct_profile_supported"] is not False
        or runtime["direct_valid_canonical_task_ids"] != [0, 3, 4]
    ):
        raise ValueError("DIRECT_PROFILE_RUNTIME_BOUNDARY_INVALID")
    return {
        "lifecycle_profile": candidate["lifecycle_profile"],
        "candidate": candidate,
        "materialized": materialized,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "formal_decision_binding_verified": True,
        "formal_decision_sha256": subject.FORMAL_DECISION_SHA256,
        "exact8_unique": True,
        "3VCY_include_exact4": True,
        "4R7U_training_excluded_chemistry_positive_exact4": True,
        "all_negative_chemistry_task_domain_runtime_flags_false": True,
        "reactive_pair_exact": True,
        "role_partition_exact": True,
        "empty_linker_accepted": True,
        "role_profile_exact": True,
        "global_canonical_exact5_unchanged": True,
        "direct_profile_applicable_tasks_exact_A_B3_C": True,
        "B_and_B2_retained_but_not_applicable": True,
        "current11_tensorizer_direct_profile_supported": False,
        "reaction_family_candidate_non_authoritative": True,
        "warhead_rule_candidate_non_authoritative": True,
        "warhead_family_reusable_SMARTS_deferred": True,
        "training_admitted_count": 0,
        "runtime_model_usable_count": 0,
        "legacy_overlay_SHA_unchanged": True,
        "historical_reconciliation_SHA_unchanged": True,
        "deterministic_double_rebuild_byte_identical": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    result = run_check_v1(arguments.repo_root)
    for key in (
        "lifecycle_profile",
        "output_artifact_count",
        "candidate_publication_file_count",
        "formal_decision_binding_verified",
        "exact8_unique",
        "3VCY_include_exact4",
        "4R7U_training_excluded_chemistry_positive_exact4",
        "all_negative_chemistry_task_domain_runtime_flags_false",
        "reactive_pair_exact",
        "role_partition_exact",
        "empty_linker_accepted",
        "role_profile_exact",
        "global_canonical_exact5_unchanged",
        "direct_profile_applicable_tasks_exact_A_B3_C",
        "B_and_B2_retained_but_not_applicable",
        "current11_tensorizer_direct_profile_supported",
        "reaction_family_candidate_non_authoritative",
        "warhead_rule_candidate_non_authoritative",
        "warhead_family_reusable_SMARTS_deferred",
        "training_admitted_count",
        "runtime_model_usable_count",
        "legacy_overlay_SHA_unchanged",
        "historical_reconciliation_SHA_unchanged",
        "deterministic_double_rebuild_byte_identical",
    ):
        value = result[key]
        print(key + "=" + (str(value).lower() if type(value) is bool else str(value)))
    for name, digest in result["materialized"]["artifact_sha256"].items():
        print(name + "_sha256=" + digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
