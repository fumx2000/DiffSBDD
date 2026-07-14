#!/usr/bin/env python3
"""Fail-closed staged-index safety checks for CovaPIE commits."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import unicodedata


POLICY_EXIT = 1
ERROR_EXIT = 2
NORMAL_STATUSES = {b"A", b"M", b"D", b"T", b"U", b"X", b"B"}
FORBIDDEN_SUFFIXES = (
    b".pt",
    b".ckpt",
    b".pth",
    b".pkl",
    b".lmdb",
    b".tar",
    b".zip",
    b".tgz",
    b".npz",
    b".tmp",
    b".part",
)


class ParseError(ValueError):
    """Raised when Git's NUL-delimited name-status stream is malformed."""


class OperationalError(RuntimeError):
    """Raised when the checker cannot safely inspect the staged index."""


@dataclass(frozen=True)
class StagedChange:
    status: bytes
    paths: tuple[bytes, ...]


@dataclass(frozen=True)
class Violation:
    path: bytes
    reason_code: str
    reason_text: str
    reason_order: int


def parse_name_status_z(payload: bytes) -> list[StagedChange]:
    """Parse Git's --name-status -z output without converting path bytes."""
    if not payload:
        return []
    if not payload.endswith(b"\0"):
        raise ParseError("name-status stream is missing its final NUL delimiter")

    tokens = payload[:-1].split(b"\0")
    changes: list[StagedChange] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if not status:
            raise ParseError("name-status stream contains an empty status")

        if status in NORMAL_STATUSES:
            paths_needed = 1
        elif status[:1] in {b"R", b"C"}:
            score = status[1:]
            if not score or not score.isdigit() or int(score) > 100:
                raise ParseError("rename/copy status has an invalid similarity score")
            paths_needed = 2
        else:
            raise ParseError("name-status stream contains an unknown status")

        if len(tokens) - index < paths_needed:
            raise ParseError("name-status stream is missing a path token")
        paths = tuple(tokens[index : index + paths_needed])
        index += paths_needed
        if any(not path for path in paths):
            raise ParseError("name-status stream contains an empty path")
        changes.append(StagedChange(status=status, paths=paths))

    return changes


def _is_forbidden_directory(path: bytes, directory: bytes) -> bool:
    return path == directory or path.startswith(directory + b"/")


def classify_path(path: bytes) -> list[Violation]:
    """Return every permanent artifact-policy violation for one Git path."""
    violations: list[Violation] = []
    if _is_forbidden_directory(path, b"data/raw"):
        violations.append(
            Violation(
                path,
                "forbidden_path:data/raw",
                "staged changes under data/raw are forbidden",
                1,
            )
        )
    if _is_forbidden_directory(path, b"checkpoints"):
        violations.append(
            Violation(
                path,
                "forbidden_path:checkpoints",
                "staged changes under checkpoints are forbidden",
                2,
            )
        )

    basename = path.rsplit(b"/", 1)[-1].lower()
    for suffix in FORBIDDEN_SUFFIXES:
        if basename.endswith(suffix):
            suffix_text = suffix.decode("ascii")
            violations.append(
                Violation(
                    path,
                    "forbidden_suffix:" + suffix_text,
                    "staged files with " + suffix_text + " suffix are forbidden",
                    3,
                )
            )
    return violations


def collect_violations(changes: list[StagedChange]) -> list[Violation]:
    """Classify source and destination paths, de-duplicate, and sort stably."""
    unique: dict[tuple[bytes, str], Violation] = {}
    for change in changes:
        for path in change.paths:
            for violation in classify_path(path):
                unique[(violation.path, violation.reason_code)] = violation
    return sorted(
        unique.values(),
        key=lambda item: (item.path, item.reason_order, item.reason_code),
    )


def display_path(path: bytes) -> str:
    """Render path bytes readably while escaping controls and invalid UTF-8."""
    text = path.decode("utf-8", errors="surrogateescape")
    rendered: list[str] = []
    for character in text:
        codepoint = ord(character)
        if 0xDC80 <= codepoint <= 0xDCFF:
            rendered.append("\\x{0:02X}".format(codepoint - 0xDC00))
        elif character == "\\":
            rendered.append("\\\\")
        elif character == "\t":
            rendered.append("\\t")
        elif character == "\n":
            rendered.append("\\n")
        elif character == "\r":
            rendered.append("\\r")
        elif unicodedata.category(character).startswith("C"):
            rendered.extend("\\x{0:02X}".format(value) for value in character.encode("utf-8"))
        else:
            rendered.append(character)
    return "".join(rendered)


def format_violations(violations: list[Violation]) -> list[str]:
    return [
        "- {0}: {1}".format(display_path(violation.path), violation.reason_text)
        for violation in violations
    ]


def _run_git(repo_root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", os.fspath(repo_root), "-c", "color.ui=false", *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise OperationalError("unable to run Git") from error


def validate_repo_root(repo_root: str) -> Path:
    root = Path(repo_root)
    if not root.is_dir():
        raise OperationalError("repository root is not an existing directory")
    result = _run_git(root, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise OperationalError("repository root is not a Git worktree")
    git_root = result.stdout.decode("utf-8", errors="surrogateescape").rstrip("\n")
    if os.path.realpath(os.fspath(root)) != os.path.realpath(git_root):
        raise OperationalError("repository root is not the Git worktree root")
    return root


def _name_status(repo_root: Path) -> list[StagedChange]:
    result = _run_git(
        repo_root,
        [
            "diff",
            "--cached",
            "--no-ext-diff",
            "--no-textconv",
            "--name-status",
            "-z",
            "--find-renames=50%",
            "--find-copies=50%",
        ],
    )
    if result.returncode != 0:
        raise OperationalError("unable to inspect the staged name-status diff")
    return parse_name_status_z(result.stdout)


def _diff_check_output(repo_root: Path) -> bytes | None:
    result = _run_git(
        repo_root,
        ["diff", "--cached", "--no-ext-diff", "--no-textconv", "--check"],
    )
    if result.returncode == 0:
        return None
    if result.stdout:
        return result.stdout
    raise OperationalError("unable to inspect the staged diff check")


def run_checker(repo_root: Path) -> int:
    changes = _name_status(repo_root)
    violations = collect_violations(changes)
    diff_check_output = _diff_check_output(repo_root)

    if violations or diff_check_output is not None:
        print("CovaPIE staged commit safety check blocked:", file=sys.stderr)
        for line in format_violations(violations):
            print(line, file=sys.stderr)
        if diff_check_output is not None:
            print("- staged diff check reported:", file=sys.stderr)
            for line in diff_check_output.split(b"\n"):
                if line:
                    print("  " + display_path(line), file=sys.stderr)
        return POLICY_EXIT

    print("CovaPIE staged commit safety check passed.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check only CovaPIE staged commit safety rules.")
    parser.add_argument("--repo-root", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = parse_args(argv)
        return run_checker(validate_repo_root(arguments.repo_root))
    except (OperationalError, ParseError) as error:
        print("CovaPIE staged commit safety check error: {0}".format(error), file=sys.stderr)
        return ERROR_EXIT
    except Exception:
        print("CovaPIE staged commit safety check error: internal checker failure", file=sys.stderr)
        return ERROR_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
