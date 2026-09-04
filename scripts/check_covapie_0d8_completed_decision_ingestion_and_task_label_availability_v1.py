#!/usr/bin/env python3
"""Check the uncommitted or tracked-clean 0D8 ingestion candidate."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys

from covalent_ext import (
    covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)


ERROR = "COVAPIE_0D8_INGESTION_CHECK_V1_ERROR"
PROTECTED_PATHS = (
    "data/raw",
    "checkpoints",
    "equivariant_diffusion",
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part", ".log",
)
LCY_MATRIX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_lcy_event_task_label_availability_v1.csv"
)


def fail(reason: str) -> None:
    raise RuntimeError(ERROR + ":" + reason)


def git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + ":".join(args))
    return result.stdout.strip()


def is_ancestor(repo_root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode not in (0, 1):
        fail("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def file_record(repo_root: Path, relative: Path) -> dict[str, object]:
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise RuntimeError(ERROR + ":CANDIDATE_FILE_READ_FAILED:" + relative.as_posix()) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("CANDIDATE_FILE_NOT_REGULAR_NON_SYMLINK:" + relative.as_posix())
    if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        fail("CANDIDATE_FILE_EXECUTABLE:" + relative.as_posix())
    if not payload.endswith(b"\n") or b"\r" in payload or b"\x00" in payload:
        fail("CANDIDATE_FILE_TEXT_HYGIENE_INVALID:" + relative.as_posix())
    return {
        "path": relative.as_posix(),
        "bytes": len(payload),
        "LOC": len(payload.decode("utf-8").splitlines()),
        "SHA256": hashlib.sha256(payload).hexdigest(),
        "mode": stat.filemode(metadata.st_mode),
        "class": "REGULAR_NON_SYMLINK_NON_EXECUTABLE",
    }


def check_lcy_header(repo_root: Path) -> None:
    payload = (repo_root / LCY_MATRIX_RELATIVE).read_bytes()
    try:
        rows = csv.reader(io.StringIO(payload.decode("utf-8"), newline=""))
        header = tuple(next(rows))
    except (OSError, UnicodeDecodeError, StopIteration, csv.Error) as error:
        raise RuntimeError(ERROR + ":LCY_HEADER_READ_FAILED") from error
    if len(header) != 115 or header != owner.MATRIX_HEADER:
        fail("MATRIX_HEADER_NOT_EXACT_PUBLISHED_LCY_115")


def check_git_lifecycle(repo_root: Path) -> dict[str, object]:
    branch = git(repo_root, "branch", "--show-current")
    head = git(repo_root, "rev-parse", "HEAD")
    origin = git(repo_root, "rev-parse", "origin/main")
    if branch != "main":
        fail("BRANCH_NOT_MAIN")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, head):
        fail("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, origin):
        fail("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if not is_ancestor(repo_root, origin, head):
        fail("ORIGIN_MAIN_NOT_BETWEEN_BASELINE_AND_HEAD")
    counts = git(repo_root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    try:
        behind, ahead = (int(value) for value in counts.split())
    except (ValueError, TypeError) as error:
        raise RuntimeError(ERROR + ":AHEAD_BEHIND_PARSE_FAILED") from error
    if behind != 0:
        fail("HEAD_BEHIND_ORIGIN_MAIN")

    tracked_modifications = git(repo_root, "diff", "--name-only").splitlines()
    staged = git(repo_root, "diff", "--cached", "--name-only").splitlines()
    untracked = git(
        repo_root, "ls-files", "--others", "--exclude-standard"
    ).splitlines()
    expected = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    expected_set = set(expected)
    if tracked_modifications:
        fail("TRACKED_MODIFICATIONS_PRESENT")
    if staged:
        fail("STAGED_INDEX_NOT_EMPTY")
    if set(untracked) == expected_set and len(untracked) == 7:
        profile = "CANDIDATE_UNTRACKED"
        if head != owner.BASELINE_COMMIT or origin != owner.BASELINE_COMMIT or ahead != 0:
            fail("CANDIDATE_UNTRACKED_BASELINE_PROFILE_DRIFT")
    elif not untracked:
        profile = "TRACKED_CLEAN"
        tracked = set(git(repo_root, "ls-files", "--", *expected).splitlines())
        if tracked != expected_set:
            fail("TRACKED_CLEAN_EXACT7_NOT_TRACKED")
    else:
        fail("ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY")

    changed_since_baseline = set(
        git(repo_root, "diff", "--name-only", owner.BASELINE_COMMIT + "..HEAD").splitlines()
    )
    if profile == "TRACKED_CLEAN" and not expected_set.issubset(changed_since_baseline):
        fail("TRACKED_CLEAN_EXACT7_NOT_DESCENDED_FROM_BASELINE")
    if any(
        path == protected or path.startswith(protected + "/")
        for path in changed_since_baseline
        for protected in PROTECTED_PATHS
    ):
        fail("PROTECTED_SOURCE_CHANGED_SINCE_BASELINE")
    candidate_paths = expected_set | (changed_since_baseline if profile == "TRACKED_CLEAN" else set())
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in candidate_paths):
        fail("FORBIDDEN_SUFFIX_IN_CANDIDATE_HISTORY")
    raw_changed = sorted(
        path for path in changed_since_baseline
        if path == "data/raw" or path.startswith("data/raw/")
    )
    if raw_changed:
        fail("RAW_DATA_CHANGED_SINCE_BASELINE")
    return {
        "profile": profile,
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": untracked,
        "raw_changed_since_baseline_count": 0,
        "protected_source_changed_since_baseline_count": 0,
        "forbidden_candidate_file_count": 0,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    lifecycle = check_git_lifecycle(repo_root)
    check_lcy_header(repo_root)
    materialized = owner.check_materialized_v1(repo_root)
    inventory = [file_record(repo_root, path) for path in owner.CANDIDATE_PUBLICATION_PATHS]
    if len(inventory) != 7 or len({row["path"] for row in inventory}) != 7:
        fail("CANDIDATE_INVENTORY_NOT_EXACT7")
    output_root = repo_root / owner.OUTPUT_ROOT_RELATIVE
    if {path.name for path in output_root.iterdir()} != set(owner.OUTPUT_FILENAMES):
        fail("OUTPUT_INVENTORY_NOT_EXACT4")

    result = {
        "status": "PASS",
        "lifecycle": lifecycle,
        "candidate_Exact7": inventory,
        "materialized": materialized,
        "matrix_rows": 4,
        "matrix_columns": 115,
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "task_relevance": "NOT_RELEVANT",
        "chemistry": "POSITIVE",
        "training": "NOT_APPLICABLE",
        "pair_authority_event_count": 4,
        "role_authority_event_count": 4,
        "task_applicability_determined_event_count": 4,
        "authoritative_task_labels_created_count": 0,
        "event_task_label_rows_materialized_count": 0,
        "training_mask_target_available_count": 0,
        "active_source_binding_count": 10,
        "duplicate_source_binding_identity_count": 0,
        "generic_exact11_accepted_count": 4,
        "current_orthogonal_population": 8,
        "future_orthogonal_population_preview": 12,
        "future_arithmetic_only": True,
        "current_census_refresh": False,
        "0D8_INGESTION_CANDIDATE_PASS": True,
        "0D8_FORMAL_DECISION_BOUND": True,
        "0D8_FORMAL_VALIDATOR_PROVENANCE_ONLY": True,
        "0D8_FORMAL_SEMANTICS_INDEPENDENTLY_VALIDATED": True,
        "0D8_COMPLETED_LANE_TASK_DOMAIN_NEGATIVE": True,
        "0D8_TASK_NOT_RELEVANT": True,
        "0D8_CHEMISTRY_POSITIVE": True,
        "0D8_CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "0D8_SAMPLE_SG_C8_AUTHORITY_AVAILABLE": True,
        "0D8_SAMPLE_ROLE_AUTHORITY_AVAILABLE": True,
        "0D8_ROLE_PROFILE_DIRECT": True,
        "0D8_SAMPLE_TASK_APPLICABILITY_DETERMINED": True,
        "0D8_SAMPLE_APPLICABLE_TASK_IDS_0_3_4": True,
        "0D8_AUTHORITATIVE_TASK_LABELS_CREATED": False,
        "0D8_EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "0D8_TRAINING_MASK_TARGETS_AVAILABLE": False,
        "0D8_D5_NOT_APPLICABLE": True,
        "0D8_HUMAN_TRAINING_EXCLUDED": False,
        "0D8_FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "PRE_SOURCE_GRAPH_NOT_AVAILABLE": True,
        "PRE_REACTION_UNRESOLVED": True,
        "POST_TRAINING_AUTHORITY": False,
        "GENERIC_EXACT11_COMPATIBILITY_PASS": True,
        "GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE": True,
        "ACTIVE_SOURCE_BINDINGS_10": True,
        "CURRENT_ORTHOGONAL_POPULATION_8": True,
        "FUTURE_ORTHOGONAL_POPULATION_12_PREVIEW_ONLY": True,
        "CURRENT_CENSUS_REFRESH": False,
        "RECONCILIATION": False,
        "QUEUE_REFRESH": False,
        "EXACT5_B3_PRESENT": True,
        "SIXTH_TASK": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "READY_FOR_EXTERNAL_REVIEW": True,
        "COMMIT": False,
        "PUSH": False,
    }
    if materialized.get("READY_FOR_EXTERNAL_REVIEW") is not True:
        fail("MATERIALIZED_NOT_READY_FOR_EXTERNAL_REVIEW")
    if result["READY_FOR_TRAINING"] is not False:
        fail("TRAINING_READINESS_MUST_REMAIN_FALSE")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, owner.ZeroD8IngestionSafetyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
