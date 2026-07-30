"""Tests for the external Current11 warhead-boundary review workspace v1."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import rdkit


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / (
    "scripts/"
    "prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_workspace_v1.py"
)
SPEC = importlib.util.spec_from_file_location("current11_workspace_v1", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
workspace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspace)

BASE_COMMIT = "81f8d7904bfbcef0e324d577cf5943722f021adf"
BASE_PARENT = "84375060a0ddd9b281d17719331a316716bffd85"
BASE_TREE = "bcead442605f95e6914198e5d1d1c70ecd8976a0"
BASE_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary review "
    "submission adapter v1"
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


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result.stdout


def csv_rows(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return tuple(reader.fieldnames or ()), rows


def source_paths() -> tuple[Path, ...]:
    return tuple(
        REPO_ROOT / workspace.PACKAGE_ROOT / name
        for name in workspace.SOURCE_FILES
    )


def source_hashes() -> dict[Path, str]:
    return {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths()
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

    if head == BASE_COMMIT:
        assert branch == "main"
        assert origin_main == BASE_COMMIT
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
    assert parents == (BASE_COMMIT,)
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
    if origin_main == BASE_COMMIT:
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


def test_fixed_python_pytest_and_rdkit_versions() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"


def test_formal_base_exact4_and_single_main_worktree() -> None:
    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    assert identity == [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    lifecycle = current_lifecycle()
    assert lifecycle in {
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    }
    worktrees = [
        line for line in git("worktree", "list", "--porcelain").splitlines()
        if line.startswith(b"worktree ")
    ]
    assert len(worktrees) == 1
    for relative in EXACT4:
        info = (REPO_ROOT / relative).lstat()
        assert stat.S_ISREG(info.st_mode)
        assert stat.S_IMODE(info.st_mode) in {0o644, 0o664}
        assert info.st_size < 5 * 1024 * 1024


def test_four_frozen_sources_exist_with_exact_hashes_and_counts() -> None:
    assert len(source_paths()) == 4
    assert all(path.is_file() for path in source_paths())
    assert source_hashes() == {
        REPO_ROOT / workspace.PACKAGE_ROOT / name: digest
        for name, digest in workspace.SOURCE_SHA256.items()
    }
    index_rows, option_rows, template_rows = workspace.load_frozen_package(
        REPO_ROOT
    )
    manifest = json.loads(source_paths()[0].read_bytes())
    assert len(index_rows) == manifest["package_index_count"] == 11
    assert len(template_rows) == manifest["review_template_count"] == 11
    assert len(option_rows) == manifest["package_option_record_count"] == 200
    assert sum(row["review_eligible"] == "true" for row in option_rows) == 185
    assert sum(row["review_eligible"] == "false" for row in option_rows) == 15
    assert manifest["ready_for_warhead_boundary_human_review"] is True
    assert manifest["warhead_boundary_human_review_completed_count"] == 0


def test_temp_workspace_is_exact3_with_required_row_counts(tmp_path: Path) -> None:
    output = tmp_path / "workspace"
    result = workspace.prepare_workspace(REPO_ROOT, output)
    assert result["workspace_files"] == workspace.WORKSPACE_FILES
    assert tuple(sorted(path.name for path in output.iterdir())) == tuple(
        sorted(workspace.WORKSPACE_FILES)
    )
    work_fields, work_rows = csv_rows(output / "review_worklist.csv")
    option_fields, option_rows = csv_rows(
        output / "eligible_candidate_options.csv"
    )
    assert work_fields == workspace.WORKLIST_FIELDS
    assert option_fields == workspace.OPTION_FIELDS
    assert len(work_rows) == 11
    assert len(option_rows) == 185
    assert all(row["review_eligible"] == "true" for row in option_rows)
    _, source_options, _ = workspace.load_frozen_package(REPO_ROOT)
    assert option_rows == [
        row for row in source_options if row["review_eligible"] == "true"
    ]


def test_worklist_identity_fields_are_exact_source_copies(tmp_path: Path) -> None:
    output = tmp_path / "workspace"
    workspace.prepare_workspace(REPO_ROOT, output)
    _, actual = csv_rows(output / "review_worklist.csv")
    index_rows, _, template_rows = workspace.load_frozen_package(REPO_ROOT)
    templates = {row["sample_index_row_id"]: row for row in template_rows}
    assert [row["package_item_order_0based"] for row in actual] == [
        str(value) for value in range(11)
    ]
    for package_row, output_row in zip(index_rows, actual):
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
            assert output_row[field] == source[field]


def test_all_human_fields_remain_unfilled_and_uncompleted(
    tmp_path: Path,
) -> None:
    output = tmp_path / "workspace"
    workspace.prepare_workspace(REPO_ROOT, output)
    _, rows = csv_rows(output / "review_worklist.csv")
    assert len(rows) == 11
    for row in rows:
        assert {
            field: row[field] for field in workspace.WORKLIST_HUMAN_FIELDS
        } == workspace.INITIAL_HUMAN_VALUES
    assert all(row["review_decision"] == "not_reviewed" for row in rows)
    assert all(row["review_completed"] == "false" for row in rows)
    assert all(row["reviewer_id"] == "" for row in rows)
    assert all(row["review_rationale"] == "" for row in rows)


def test_readme_explains_manual_decisions_and_submission_boundary(
    tmp_path: Path,
) -> None:
    output = tmp_path / "workspace"
    workspace.prepare_workspace(REPO_ROOT, output)
    readme = (output / "README.md").read_text(encoding="utf-8")
    for text in (
        "11 samples",
        "sample_index_row_id",
        "candidate_option_row_start_0based",
        "select_admitted_candidate",
        "revise_atom_set_and_boundary",
        "quarantine",
        "`not_reviewed` means the review is unfinished",
        "reviewer_id",
        "review_rationale",
        "reviewer_provenance_attested",
        "review_completed",
        "not a formal submission bundle",
        "compile_covapie_current11_real_human_review_submission_bundle_v1",
        "complete 200-row options file",
        "185 review-eligible options",
    ):
        assert text in readme
    assert "has passed review" not in readme


def test_nonempty_output_directory_is_rejected_without_overwrite(
    tmp_path: Path,
) -> None:
    output = tmp_path / "workspace"
    output.mkdir()
    sentinel = output / "human-notes.txt"
    sentinel.write_bytes(b"preserve real human content\n")
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError, match="non-empty.*refusing to overwrite"):
        workspace.prepare_workspace(REPO_ROOT, output)
    after = {path.name: path.read_bytes() for path in output.iterdir()}
    assert after == before


def test_two_empty_destinations_are_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    workspace.prepare_workspace(REPO_ROOT, first)
    workspace.prepare_workspace(REPO_ROOT, second)
    assert {
        name: (first / name).read_bytes() for name in workspace.WORKSPACE_FILES
    } == {
        name: (second / name).read_bytes() for name in workspace.WORKSPACE_FILES
    }


def test_generation_has_no_git_input_submission_or_authority_effects(
    tmp_path: Path,
) -> None:
    git_before = git("status", "--porcelain=v1", "--untracked-files=all")
    head_before = git("rev-parse", "HEAD")
    inputs_before = source_hashes()
    output = tmp_path / "workspace"
    workspace.prepare_workspace(REPO_ROOT, output)
    assert git("status", "--porcelain=v1", "--untracked-files=all") == git_before
    assert git("rev-parse", "HEAD") == head_before
    assert source_hashes() == inputs_before
    assert tuple(sorted(path.name for path in output.iterdir())) == tuple(
        sorted(workspace.WORKSPACE_FILES)
    )
    assert not any(
        token in path.name
        for path in output.iterdir()
        for token in ("submission", "authority", "digest", "manifest")
    )
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "review_submission_adapter_v1 import" not in source
    assert "review_ingestion_interface_v1 import" not in source
