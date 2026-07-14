from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts" / "check_covapie_staged_commit_safety.py"
WRAPPER_PATH = REPO_ROOT / ".githooks" / "pre-commit"


def _load_checker():
    spec = importlib.util.spec_from_file_location("covapie_staged_commit_safety", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


def git(repo: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "--local", "user.name", "CovaPIE Test")
    git(repo, "config", "--local", "user.email", "covapie-test@example.invalid")
    return repo


def write_bytes(repo: Path, relative_path: str, content: bytes = b"content\n") -> Path:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def stage(repo: Path, *relative_paths: str) -> None:
    git(repo, "add", "--", *relative_paths)


def commit(repo: Path, message: str = "test commit") -> None:
    git(repo, "commit", "-q", "-m", message)


def run_checker(repo: Path) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(CHECKER_PATH), "--repo-root", str(repo)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )


def install_hook_into_temp_repo(repo: Path) -> Path:
    hook_dir = repo / ".githooks"
    script_dir = repo / "scripts"
    hook_dir.mkdir()
    script_dir.mkdir()
    wrapper = hook_dir / "pre-commit"
    shutil.copy2(WRAPPER_PATH, wrapper)
    wrapper.chmod(0o755)
    shutil.copy2(CHECKER_PATH, script_dir / CHECKER_PATH.name)
    return wrapper


def worktree_files(repo: Path) -> set[Path]:
    return {path.relative_to(repo) for path in repo.rglob("*") if ".git" not in path.parts}


def test_parser_accepts_empty_payload() -> None:
    assert checker.parse_name_status_z(b"") == []


@pytest.mark.parametrize("status", [b"A", b"M", b"D", b"T", b"U", b"X", b"B"])
def test_parser_accepts_single_path_statuses(status: bytes) -> None:
    assert checker.parse_name_status_z(status + b"\0file.txt\0") == [
        checker.StagedChange(status, (b"file.txt",))
    ]


@pytest.mark.parametrize(
    ("status", "paths"),
    [
        (b"R100", (b"old name.txt", b"new\tname.txt")),
        (b"C075", ("old-\u00e9.txt".encode(), "new-\u6d4b\u8bd5.txt".encode())),
    ],
)
def test_parser_accepts_rename_and_copy_statuses(status: bytes, paths: tuple[bytes, bytes]) -> None:
    payload = status + b"\0" + paths[0] + b"\0" + paths[1] + b"\0"
    assert checker.parse_name_status_z(payload) == [checker.StagedChange(status, paths)]


@pytest.mark.parametrize(
    "payload",
    [
        b"A\0file.txt",
        b"Q\0file.txt\0",
        b"R100\0old.txt\0",
        b"Cbad\0old.txt\0new.txt\0",
        b"R101\0old.txt\0new.txt\0",
        b"A\0\0",
    ],
)
def test_parser_fails_closed_on_malformed_input(payload: bytes) -> None:
    with pytest.raises(checker.ParseError):
        checker.parse_name_status_z(payload)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (b"data/raw/x.cif", {"forbidden_path:data/raw"}),
        (b"data/raw", {"forbidden_path:data/raw"}),
        (b"data/rawness/x.cif", set()),
        (b"checkpoints/model.bin", {"forbidden_path:checkpoints"}),
        (b"mycheckpoints/model.bin", set()),
        (b"ordinary.py", set()),
        (b"notes.md", set()),
    ],
)
def test_directory_classification(path: bytes, expected: set[str]) -> None:
    assert {item.reason_code for item in checker.classify_path(path)} == expected


@pytest.mark.parametrize("suffix", checker.FORBIDDEN_SUFFIXES)
def test_all_forbidden_suffixes_are_blocked(suffix: bytes) -> None:
    reasons = checker.classify_path(b"output" + suffix)
    assert [item.reason_code for item in reasons] == ["forbidden_suffix:" + suffix.decode("ascii")]


def test_suffix_matching_is_case_insensitive_and_combines_reasons() -> None:
    violations = checker.classify_path(b"data/raw/MODEL.CKPT")
    assert [item.reason_code for item in violations] == [
        "forbidden_path:data/raw",
        "forbidden_suffix:.ckpt",
    ]


def test_violation_collection_deduplicates_and_sorts_by_raw_path() -> None:
    changes = [
        checker.StagedChange(b"A", (b"z.zip",)),
        checker.StagedChange(b"M", (b"data/raw/x.npz",)),
        checker.StagedChange(b"D", (b"data/raw/x.npz",)),
    ]
    violations = checker.collect_violations(changes)
    assert [(item.path, item.reason_code) for item in violations] == [
        (b"data/raw/x.npz", "forbidden_path:data/raw"),
        (b"data/raw/x.npz", "forbidden_suffix:.npz"),
        (b"z.zip", "forbidden_suffix:.zip"),
    ]


def test_display_path_escapes_controls_and_invalid_utf8_but_keeps_unicode() -> None:
    assert checker.display_path(b"space name\tline\ncarriage\r\\") == "space name\\tline\\ncarriage\\r\\\\"
    assert checker.display_path("\u6d4b\u8bd5-\u00e9.txt".encode("utf-8")) == "\u6d4b\u8bd5-\u00e9.txt"
    assert checker.display_path(b"bad-\xff-name") == "bad-\\xFF-name"


def test_formatted_policy_output_is_relative_and_stable() -> None:
    violations = checker.collect_violations([checker.StagedChange(b"A", (b"data/raw/x.npz",))])
    rendered = "\n".join(checker.format_violations(violations))
    assert "/home/" not in rendered
    assert "202" not in rendered
    assert rendered.splitlines() == [
        "- data/raw/x.npz: staged changes under data/raw are forbidden",
        "- data/raw/x.npz: staged files with .npz suffix are forbidden",
    ]


def test_empty_index_and_safe_staged_files_pass(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    assert run_checker(repo).returncode == 0
    write_bytes(repo, "safe.py")
    write_bytes(repo, "README.md")
    stage(repo, "safe.py", "README.md")
    result = run_checker(repo)
    assert result.returncode == 0
    assert result.stdout == b"CovaPIE staged commit safety check passed.\n"
    assert result.stderr == b""


@pytest.mark.parametrize("history_path", ["data/raw/historical.cif", "data/historical.npz"])
def test_unchanged_historical_artifacts_do_not_block_a_new_safe_change(tmp_path: Path, history_path: str) -> None:
    repo = init_repo(tmp_path)
    write_bytes(repo, history_path)
    stage(repo, history_path)
    commit(repo, "historical artifact")
    write_bytes(repo, "safe.txt")
    stage(repo, "safe.txt")
    assert run_checker(repo).returncode == 0


@pytest.mark.parametrize(
    "operation",
    ["add", "modify", "delete", "rename_to", "rename_from"],
)
def test_raw_changes_are_rejected(tmp_path: Path, operation: str) -> None:
    repo = init_repo(tmp_path)
    if operation == "add":
        write_bytes(repo, "data/raw/new.cif")
        stage(repo, "data/raw/new.cif")
    elif operation == "modify":
        write_bytes(repo, "data/raw/old.cif")
        stage(repo, "data/raw/old.cif")
        commit(repo)
        write_bytes(repo, "data/raw/old.cif", b"changed\n")
        stage(repo, "data/raw/old.cif")
    elif operation == "delete":
        write_bytes(repo, "data/raw/old.cif")
        stage(repo, "data/raw/old.cif")
        commit(repo)
        (repo / "data/raw/old.cif").unlink()
        git(repo, "add", "-u", "--", "data/raw/old.cif")
    elif operation == "rename_to":
        write_bytes(repo, "ordinary.txt")
        stage(repo, "ordinary.txt")
        commit(repo)
        (repo / "data/raw").mkdir(parents=True)
        git(repo, "mv", "ordinary.txt", "data/raw/renamed.txt")
    else:
        write_bytes(repo, "data/raw/old.cif")
        stage(repo, "data/raw/old.cif")
        commit(repo)
        git(repo, "mv", "data/raw/old.cif", "ordinary.txt")

    result = run_checker(repo)
    assert result.returncode == 1
    assert b"data/raw" in result.stderr


@pytest.mark.parametrize("operation", ["add", "modify", "delete"])
def test_checkpoint_changes_are_rejected(tmp_path: Path, operation: str) -> None:
    repo = init_repo(tmp_path)
    path = "checkpoints/model.bin"
    if operation == "add":
        write_bytes(repo, path)
        stage(repo, path)
    else:
        write_bytes(repo, path)
        stage(repo, path)
        commit(repo)
        if operation == "modify":
            write_bytes(repo, path, b"changed\n")
            stage(repo, path)
        else:
            (repo / path).unlink()
            git(repo, "add", "-u", "--", path)
    assert run_checker(repo).returncode == 1


@pytest.mark.parametrize(
    "operation",
    ["add_pt", "add_upper_ckpt", "add_npz", "modify_npz", "delete_npz", "rename_to_zip", "rename_from_zip", "tmp", "part"],
)
def test_forbidden_suffix_changes_are_rejected(tmp_path: Path, operation: str) -> None:
    repo = init_repo(tmp_path)
    if operation == "add_pt":
        write_bytes(repo, "model.pt")
        stage(repo, "model.pt")
    elif operation == "add_upper_ckpt":
        write_bytes(repo, "MODEL.CKPT")
        stage(repo, "MODEL.CKPT")
    elif operation == "add_npz":
        write_bytes(repo, "output.npz")
        stage(repo, "output.npz")
    elif operation in {"modify_npz", "delete_npz"}:
        write_bytes(repo, "historic.npz")
        stage(repo, "historic.npz")
        commit(repo)
        if operation == "modify_npz":
            write_bytes(repo, "historic.npz", b"changed\n")
            stage(repo, "historic.npz")
        else:
            (repo / "historic.npz").unlink()
            git(repo, "add", "-u", "--", "historic.npz")
    elif operation == "rename_to_zip":
        write_bytes(repo, "ordinary.txt")
        stage(repo, "ordinary.txt")
        commit(repo)
        git(repo, "mv", "ordinary.txt", "archive.zip")
    elif operation == "rename_from_zip":
        write_bytes(repo, "archive.zip")
        stage(repo, "archive.zip")
        commit(repo)
        git(repo, "mv", "archive.zip", "ordinary.txt")
    else:
        suffix = ".tmp" if operation == "tmp" else ".part"
        write_bytes(repo, "output" + suffix)
        stage(repo, "output" + suffix)
    assert run_checker(repo).returncode == 1


def test_rename_diff_record_is_parsed_and_checks_both_paths(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write_bytes(repo, "old.txt")
    stage(repo, "old.txt")
    commit(repo)
    (repo / "data/raw").mkdir(parents=True)
    git(repo, "mv", "old.txt", "data/raw/new.txt")
    payload = git(
        repo,
        "diff",
        "--cached",
        "--name-status",
        "-z",
        "--find-renames=50%",
    ).stdout
    changes = checker.parse_name_status_z(payload)
    assert changes[0].status == b"R100"
    assert changes[0].paths == (b"old.txt", b"data/raw/new.txt")
    assert run_checker(repo).returncode == 1


def test_diff_check_violations_are_policy_failures(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write_bytes(repo, "trailing.txt", b"trailing space \n")
    stage(repo, "trailing.txt")
    result = run_checker(repo)
    assert result.returncode == checker.POLICY_EXIT
    assert result.returncode == 1
    assert b"staged diff check reported" in result.stderr
    assert b"staged commit safety check error" not in result.stderr


def test_diff_check_operational_failure_raises_operational_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def simulated_run_git(repo_root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
        assert "--check" in arguments
        return subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout=b"",
            stderr=b"fatal: simulated Git operational failure\n",
        )

    monkeypatch.setattr(checker, "_run_git", simulated_run_git)
    with pytest.raises(checker.OperationalError, match="unable to inspect the staged diff check"):
        checker._diff_check_output(tmp_path)


def test_diff_check_operational_failure_maps_to_error_exit_without_leaking_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = init_repo(tmp_path)
    original_run_git = checker._run_git

    def simulated_run_git(repo_root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
        if "--check" in arguments:
            return subprocess.CompletedProcess(
                args=[],
                returncode=128,
                stdout=b"",
                stderr=b"fatal: /home/private/index failure\n",
            )
        return original_run_git(repo_root, arguments)

    monkeypatch.setattr(checker, "_run_git", simulated_run_git)
    rc = checker.main(["--repo-root", str(repo)])
    captured = capsys.readouterr()
    assert rc == checker.ERROR_EXIT
    assert rc == 2
    assert captured.out == ""
    assert captured.err == (
        "CovaPIE staged commit safety check error: "
        "unable to inspect the staged diff check\n"
    )
    assert "/home/" not in captured.err
    assert "fatal:" not in captured.err
    assert "staged commit safety check blocked" not in captured.err
    assert "staged diff check reported" not in captured.err


def test_conflict_markers_detected_by_diff_check_are_policy_failures(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write_bytes(repo, "conflict.txt", b"<<<<<<< HEAD\n=======\n>>>>>>> branch\n")
    stage(repo, "conflict.txt")
    result = run_checker(repo)
    assert result.returncode == 1
    assert b"staged diff check reported" in result.stderr


def test_checker_policy_output_is_deterministic(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write_bytes(repo, "z.zip")
    write_bytes(repo, "data/raw/x.npz")
    stage(repo, "z.zip", "data/raw/x.npz")
    first = run_checker(repo)
    second = run_checker(repo)
    assert first.returncode == second.returncode == 1
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr


def test_wrapper_is_executable_and_runs_checker_in_temp_repo(tmp_path: Path) -> None:
    assert WRAPPER_PATH.stat().st_mode & stat.S_IXUSR
    repo = init_repo(tmp_path)
    wrapper = install_hook_into_temp_repo(repo)
    result = subprocess.run([str(wrapper)], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout == b"CovaPIE staged commit safety check passed.\n"
    assert result.stderr == b""


def test_wrapper_propagates_policy_failure_and_does_not_create_worktree_files(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    wrapper = install_hook_into_temp_repo(repo)
    write_bytes(repo, "blocked.ckpt")
    stage(repo, "blocked.ckpt")
    before = worktree_files(repo)
    result = subprocess.run([str(wrapper)], cwd=repo, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 1
    assert b"blocked.ckpt" in result.stderr
    assert worktree_files(repo) == before


def test_enabled_temp_hook_allows_safe_commit_and_rejects_without_mutation(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    install_hook_into_temp_repo(repo)
    git(repo, "config", "--local", "core.hooksPath", ".githooks")
    write_bytes(repo, "safe.txt")
    stage(repo, "safe.txt")
    commit(repo, "safe commit")
    head_before = git(repo, "rev-parse", "HEAD").stdout
    write_bytes(repo, "blocked.npz")
    stage(repo, "blocked.npz")
    result = git(repo, "commit", "-m", "blocked commit", check=False)
    assert result.returncode != 0
    assert git(repo, "rev-parse", "HEAD").stdout == head_before
    assert git(repo, "diff", "--cached", "--name-only").stdout == b"blocked.npz\n"
    assert (repo / "blocked.npz").read_bytes() == b"content\n"
