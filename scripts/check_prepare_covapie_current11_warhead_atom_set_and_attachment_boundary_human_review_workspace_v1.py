#!/usr/bin/env python3
"""Checker for the external Current11 warhead-boundary review workspace v1."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

import pytest
import rdkit

import prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_human_review_workspace_v1 as workspace


ROOT = Path(__file__).resolve().parents[1]
BASE_IDENTITY = (
    "81f8d7904bfbcef0e324d577cf5943722f021adf",
    "84375060a0ddd9b281d17719331a316716bffd85",
    "bcead442605f95e6914198e5d1d1c70ecd8976a0",
    "add CovaPIE Current11 warhead atom set and attachment boundary review "
    "submission adapter v1",
)
SUCCESSOR_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary human "
    "review workspace v1"
)
EXACT4 = (
    "docs/covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_workspace_v1_guide.md",
    "scripts/check_prepare_covapie_current11_warhead_atom_set_and_attachment_"
    "boundary_human_review_workspace_v1.py",
    "scripts/prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_workspace_v1.py",
    "tests/test_prepare_covapie_current11_warhead_atom_set_and_attachment_"
    "boundary_human_review_workspace_v1.py",
)
README_MARKERS = (
    "11 samples",
    "sample_index_row_id",
    "candidate_option_row_start_0based",
    "select_admitted_candidate",
    "revise_atom_set_and_boundary",
    "quarantine",
    "`not_reviewed` means the review is unfinished",
    "reviewer_provenance_attested",
    "not a formal submission bundle",
    "compile_covapie_current11_real_human_review_submission_bundle_v1",
    "complete 200-row options file",
    "185 review-eligible options",
)


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return tuple(reader.fieldnames or ()), rows


def source_hashes() -> dict[str, str]:
    return {
        name: hashlib.sha256(
            (ROOT / workspace.PACKAGE_ROOT / name).read_bytes()
        ).hexdigest()
        for name in workspace.SOURCE_FILES
    }


def current_lifecycle() -> str:
    """Return the one allowed local lifecycle state, failing closed otherwise."""
    head = git("rev-parse", "HEAD").decode().strip()
    branch = git("branch", "--show-current").decode().strip()
    origin_main = git("rev-parse", "refs/remotes/origin/main").decode().strip()
    tracked_diff = git("diff", "--name-only")
    staged_diff = git("diff", "--cached", "--name-only")
    untracked = tuple(sorted(
        git("ls-files", "--others", "--exclude-standard").decode().splitlines()
    ))

    if head == BASE_IDENTITY[0]:
        assert branch == "main"
        assert origin_main == BASE_IDENTITY[0]
        assert git(
            "rev-list", "--left-right", "--count",
            "HEAD...refs/remotes/origin/main",
        ) == b"0\t0\n"
        assert tracked_diff == b""
        assert staged_diff == b""
        assert untracked == EXACT4
        return "pre_commit"

    raw_commit = git("cat-file", "commit", head)
    headers, separator, message = raw_commit.partition(b"\n\n")
    assert separator
    parents = tuple(
        line[7:].decode()
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    assert parents == (BASE_IDENTITY[0],)
    assert message == (SUCCESSOR_SUBJECT + "\n").encode()
    changed_paths = tuple(sorted(
        git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", head,
        ).decode().splitlines()
    ))
    assert changed_paths == EXACT4
    tree_entries = git("ls-tree", head, "--", *EXACT4).decode().splitlines()
    assert len(tree_entries) == 4
    modes = {
        line.split("\t", 1)[1]: line.split(None, 1)[0]
        for line in tree_entries
    }
    assert modes == {path: "100644" for path in EXACT4}
    assert git("status", "--porcelain=v1", "--untracked-files=all") == b""

    if branch == "":
        return "detached_candidate_post_commit"
    assert branch == "main"
    if origin_main == BASE_IDENTITY[0]:
        assert git(
            "rev-list", "--left-right", "--count",
            "HEAD...refs/remotes/origin/main",
        ) == b"1\t0\n"
        return "formal_main_post_commit_unpushed"
    if origin_main == head:
        assert git(
            "rev-list", "--left-right", "--count",
            "HEAD...refs/remotes/origin/main",
        ) == b"0\t0\n"
        return "formal_main_post_push"
    raise AssertionError("current Git state is outside the Exact4 lifecycle")


def assert_environment_and_base() -> str:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"
    identity = tuple(
        git(
            "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_IDENTITY[0],
        )
        .decode().splitlines()
    )
    assert identity == BASE_IDENTITY
    lifecycle = current_lifecycle()
    worktrees = [
        line for line in git("worktree", "list", "--porcelain").splitlines()
        if line.startswith(b"worktree ")
    ]
    assert len(worktrees) == 1
    return lifecycle


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        raise AssertionError("checker accepts no arguments")
    lifecycle = assert_environment_and_base()
    git_before = git("status", "--porcelain=v1", "--untracked-files=all")
    head_before = git("rev-parse", "HEAD")
    inputs_before = source_hashes()
    assert inputs_before == workspace.SOURCE_SHA256

    index_rows, all_options, template_rows = workspace.load_frozen_package(ROOT)
    eligible_count = sum(
        row["review_eligible"] == "true" for row in all_options
    )
    ineligible_count = sum(
        row["review_eligible"] == "false" for row in all_options
    )
    assert (len(index_rows), len(template_rows), len(all_options)) == (11, 11, 200)
    assert (eligible_count, ineligible_count) == (185, 15)

    with tempfile.TemporaryDirectory(
        prefix="covapie-current11-warhead-review-check-"
    ) as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        workspace.prepare_workspace(ROOT, first)
        workspace.prepare_workspace(ROOT, second)
        assert tuple(sorted(path.name for path in first.iterdir())) == tuple(
            sorted(workspace.WORKSPACE_FILES)
        )
        assert tuple(sorted(path.name for path in second.iterdir())) == tuple(
            sorted(workspace.WORKSPACE_FILES)
        )
        first_payloads = {
            name: (first / name).read_bytes()
            for name in workspace.WORKSPACE_FILES
        }
        second_payloads = {
            name: (second / name).read_bytes()
            for name in workspace.WORKSPACE_FILES
        }
        assert first_payloads == second_payloads

        work_fields, work_rows = read_csv(first / "review_worklist.csv")
        option_fields, eligible_options = read_csv(
            first / "eligible_candidate_options.csv"
        )
        assert work_fields == workspace.WORKLIST_FIELDS
        assert option_fields == workspace.OPTION_FIELDS
        assert len(work_rows) == 11
        assert len(eligible_options) == 185
        assert all(
            row["review_eligible"] == "true" for row in eligible_options
        )

        templates = {
            row["sample_index_row_id"]: row for row in template_rows
        }
        for package_row, work_row in zip(index_rows, work_rows):
            template = templates[package_row["sample_index_row_id"]]
            for field in workspace.WORKLIST_IDENTITY_FIELDS:
                source = (
                    package_row
                    if field in {
                        "package_item_order_0based",
                        "candidate_option_row_start_0based",
                        "candidate_option_row_end_exclusive",
                    }
                    else template
                )
                assert work_row[field] == source[field]
            assert {
                field: work_row[field]
                for field in workspace.WORKLIST_HUMAN_FIELDS
            } == workspace.INITIAL_HUMAN_VALUES

        readme = (first / "README.md").read_text(encoding="utf-8")
        assert all(marker in readme for marker in README_MARKERS)
        assert not any(
            token in path.name
            for path in first.iterdir()
            for token in ("submission", "authority", "digest", "manifest")
        )
        assert not workspace._is_within(first.resolve(), ROOT.resolve())

    assert source_hashes() == inputs_before
    assert git("status", "--porcelain=v1", "--untracked-files=all") == git_before
    assert git("rev-parse", "HEAD") == head_before

    print("checker=passed")
    print(f"current_lifecycle={lifecycle}")
    print(
        "samples=11 candidate_options=200 eligible_options=185 "
        "ineligible_options=15"
    )
    print("workspace_files=3")
    print("worklist_rows=11")
    print("all_reviews_completed=false")
    print("all_review_decisions=not_reviewed")
    print("identity_fields_preserved=true")
    print("human_fields_unfilled=true")
    print("deterministic=true")
    print("filesystem_scope=external_workspace_only")
    print("git_effects=0 input_effects=0")
    print("actual_reviews=0 submission_payloads=0 authorities=0")
    print(
        "recommended_next_step="
        "perform_covapie_current11_real_human_review_v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
