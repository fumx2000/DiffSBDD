from __future__ import annotations

import ast
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as harness


SUBJECT = "add synthetic hermetic lifecycle candidate v1"
COMMIT_ENV = {
    "GIT_AUTHOR_DATE": "2001-01-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2001-01-01T00:00:00+00:00",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _git(repository: Path, *arguments: str, env=None, check=True):
    merged_env = dict(COMMIT_ENV)
    if env:
        merged_env.update(env)
    result = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        env=merged_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git {arguments!r} failed: {result.stdout!r} {result.stderr!r}"
        )
    return result


def _commit(repository: Path, subject: str) -> str:
    _git(repository, "add", "--all")
    _git(
        repository,
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=covapie-test@example.invalid",
        "commit",
        "--no-gpg-sign",
        "-m",
        subject,
    )
    return _git(repository, "rev-parse", "HEAD").stdout.strip()


def _make_source(tmp_path: Path, suffix: str = ".txt"):
    source = tmp_path / "source"
    workspace = tmp_path / "workspace"
    source.mkdir()
    workspace.mkdir()
    _git(source, "init", "--initial-branch=main")
    (source / "base.txt").write_text("explicit base\n", encoding="utf-8")
    base = _commit(source, "synthetic explicit base")
    relative = Path(f"candidate{suffix}")
    (source / relative).write_text("candidate payload\n", encoding="utf-8")
    (source / "ambient.txt").write_text("ambient only\n", encoding="utf-8")
    ambient = _commit(source, "synthetic ambient commit")
    assert ambient != base
    assert _git(source, "rev-parse", "main").stdout.strip() == ambient
    return source, workspace, base, ambient, (relative,)


def _exercise(source, workspace, base, paths):
    return harness.exercise_hermetic_git_lifecycle_matrix(
        source,
        workspace,
        base_commit=base,
        formal_commit_subject=SUBJECT,
        exact_paths=paths,
    )


def _status_bytes(repository: Path) -> bytes:
    return subprocess.run(
        (
            "git",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=no",
        ),
        cwd=repository,
        env={
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def test_public_api_frozen_dataclasses_and_exact_signature():
    assert harness.__all__ == (
        "HermeticLifecycleState",
        "HermeticLifecycleMatrixReport",
        "exercise_hermetic_git_lifecycle_matrix",
    )
    assert harness.HermeticLifecycleState.__dataclass_params__.frozen is True
    assert harness.HermeticLifecycleMatrixReport.__dataclass_params__.frozen is True
    tree = ast.parse(Path(harness.__file__).read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "exercise_hermetic_git_lifecycle_matrix"
    )
    assert [item.arg for item in function.args.args] == [
        "source_repository",
        "workspace_root",
    ]
    assert [item.arg for item in function.args.kwonlyargs] == [
        "base_commit",
        "formal_commit_subject",
        "exact_paths",
    ]
    assert function.args.defaults == []
    assert all(item is None for item in function.args.kw_defaults)


def test_explicit_base_ambient_independence_exact4_and_cleanup(tmp_path):
    source, workspace, base, ambient, paths = _make_source(tmp_path)
    before = harness._source_snapshot(source)
    report = _exercise(source, workspace, base, paths)
    after = harness._source_snapshot(source)

    assert ambient != base
    assert report.base_commit == base
    assert report.candidate_parent == base
    assert report.candidate_subject == SUBJECT
    assert report.exact_path_count == 1
    assert report.cleanup_verified is True
    assert before == after
    assert tuple(workspace.iterdir()) == ()

    states = (
        report.pre_commit,
        report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed,
        report.formal_main_post_push,
    )
    assert tuple(state.lifecycle for state in states) == harness.LIFECYCLES
    assert report.pre_commit.head == base
    assert report.pre_commit.main_oid == base
    assert report.pre_commit.origin_main_oid == base
    assert report.pre_commit.branch == "main"
    assert report.pre_commit.worktree_count == 1
    assert report.pre_commit.status_entry_count == 1
    assert report.detached_candidate_post_commit.head == report.candidate_commit
    assert report.detached_candidate_post_commit.main_oid == base
    assert report.detached_candidate_post_commit.origin_main_oid == base
    assert report.detached_candidate_post_commit.branch == "DETACHED"
    assert report.detached_candidate_post_commit.worktree_count == 2
    assert report.formal_main_post_commit_unpushed.main_oid == report.candidate_commit
    assert report.formal_main_post_commit_unpushed.origin_main_oid == base
    assert report.formal_main_post_commit_unpushed.worktree_count == 1
    assert report.formal_main_post_push.main_oid == report.candidate_commit
    assert (
        report.formal_main_post_push.origin_main_oid
        == report.candidate_commit
    )
    assert (
        report.formal_main_post_push.origin_head_resolved_oid
        == report.candidate_commit
    )
    assert all(state.origin_head_symbolic_target == "refs/remotes/origin/main" for state in states)
    assert all(
        state.status_entry_count == 0
        for state in states[1:]
    )
    assert all(not Path(state.repository_path).exists() for state in states)


@pytest.mark.parametrize("value", [None, 7, b"0" * 40, "0" * 39, "A" * 40, "g" * 40])
def test_base_commit_type_and_grammar_fail_closed(tmp_path, value):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    expected = TypeError if not isinstance(value, str) else ValueError
    with pytest.raises(expected):
        harness.exercise_hermetic_git_lifecycle_matrix(
            source,
            workspace,
            base_commit=value,
            formal_commit_subject=SUBJECT,
            exact_paths=paths,
        )


def test_nonexistent_explicit_base_fails_closed(tmp_path):
    source, workspace, _base, _ambient, paths = _make_source(tmp_path)
    with pytest.raises(ValueError, match="does not exist"):
        _exercise(source, workspace, "0" * 40, paths)


class _TupleSubclass(tuple):
    pass


@pytest.mark.parametrize(
    "factory,expected_error",
    [
        (lambda path: [path], TypeError),
        (lambda path: _TupleSubclass((path,)), TypeError),
        (lambda path: (), ValueError),
        (lambda path: (path, path), ValueError),
        (lambda path: (Path("/absolute"),), ValueError),
        (lambda path: (Path("nested/../candidate.txt"),), ValueError),
        (lambda path: (Path(),), ValueError),
        (lambda path: (Path(".git/config"),), ValueError),
    ],
)
def test_exact_tuple_and_path_grammar_fail_closed(
    tmp_path, factory, expected_error
):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    with pytest.raises(expected_error):
        _exercise(source, workspace, base, factory(paths[0]))


def test_source_file_missing_fails_closed(tmp_path):
    source, workspace, base, _ambient, _paths = _make_source(tmp_path)
    with pytest.raises(ValueError, match="missing or not regular"):
        _exercise(source, workspace, base, (Path("missing.txt"),))


def test_source_symlink_fails_closed(tmp_path):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    target = source / paths[0]
    target.unlink()
    try:
        target.symlink_to("ambient.txt")
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="symlink"):
        _exercise(source, workspace, base, paths)


def test_source_executable_fails_closed(tmp_path):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    target = source / paths[0]
    target.chmod(stat.S_IMODE(target.stat().st_mode) | stat.S_IXUSR)
    with pytest.raises(ValueError, match="executable"):
        _exercise(source, workspace, base, paths)


def test_forbidden_suffix_fails_closed(tmp_path):
    source, workspace, base, _ambient, paths = _make_source(tmp_path, ".pt")
    with pytest.raises(ValueError, match="forbidden"):
        _exercise(source, workspace, base, paths)


def test_exact_path_present_at_base_fails_closed(tmp_path):
    source, workspace, base, _ambient, _paths = _make_source(tmp_path)
    with pytest.raises(ValueError, match="already exists"):
        _exercise(source, workspace, base, (Path("base.txt"),))


def test_remote_seeded_from_ambient_head_fails_closed(tmp_path, monkeypatch):
    source, workspace, base, ambient, paths = _make_source(tmp_path)
    original = harness._seed_bare_remote

    def wrong_seed(source_repository, bare_remote, _base_commit):
        original(source_repository, bare_remote, ambient)

    monkeypatch.setattr(harness, "_seed_bare_remote", wrong_seed)
    before = harness._source_snapshot(source)
    with pytest.raises(RuntimeError, match="explicit BASE"):
        _exercise(source, workspace, base, paths)
    assert harness._source_snapshot(source) == before
    assert tuple(workspace.iterdir()) == ()


def _amend_candidate(repository: Path, mutation: str, paths: tuple[Path, ...]):
    if mutation == "parent":
        (repository / "unexpected-parent.txt").write_text(
            "parent drift\n", encoding="utf-8"
        )
        _git(repository, "add", "unexpected-parent.txt")
        _git(
            repository,
            "-c",
            "user.name=CovaPIE Test",
            "-c",
            "user.email=covapie-test@example.invalid",
            "commit",
            "--no-gpg-sign",
            "-m",
            "unexpected parent",
        )
        return
    if mutation == "extra":
        (repository / "unexpected.txt").write_text("extra\n", encoding="utf-8")
        _git(repository, "add", "unexpected.txt")
    elif mutation == "mode":
        target = repository / paths[0]
        target.chmod(0o755)
        _git(repository, "add", "--", paths[0].as_posix())
    elif mutation != "subject":
        raise AssertionError(mutation)
    arguments = [
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=covapie-test@example.invalid",
        "commit",
        "--amend",
        "--no-gpg-sign",
    ]
    if mutation == "subject":
        arguments.extend(("-m", "wrong subject"))
    else:
        arguments.append("--no-edit")
    _git(repository, *arguments)


@pytest.mark.parametrize(
    "mutation,message",
    [
        ("parent", "parent"),
        ("subject", "subject"),
        ("extra", "changed-file"),
        ("mode", "mode"),
    ],
)
def test_candidate_commit_corruption_fails_closed(
    tmp_path, monkeypatch, mutation, message
):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    original = harness._commit_exact_paths

    def corrupt(repository, **kwargs):
        if mutation == "parent":
            _amend_candidate(repository, mutation, paths)
            return original(repository, **kwargs)
        candidate = original(repository, **kwargs)
        _amend_candidate(repository, mutation, paths)
        return _git(repository, "rev-parse", "HEAD").stdout.strip()

    monkeypatch.setattr(harness, "_commit_exact_paths", corrupt)
    before = harness._source_snapshot(source)
    with pytest.raises(RuntimeError, match=message):
        _exercise(source, workspace, base, paths)
    assert harness._source_snapshot(source) == before
    assert tuple(workspace.iterdir()) == ()


@pytest.mark.parametrize("mutation", ["origin_head", "extra_ref"])
def test_clone_ref_corruption_fails_closed(
    tmp_path, monkeypatch, mutation
):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    original = harness._capture_state
    mutated = False

    def corrupt(repository, **kwargs):
        nonlocal mutated
        if not mutated:
            mutated = True
            if mutation == "origin_head":
                _git(
                    repository,
                    "symbolic-ref",
                    "refs/remotes/origin/HEAD",
                    "refs/remotes/origin/missing",
                )
            else:
                _git(
                    repository,
                    "update-ref",
                    "refs/tags/unexpected",
                    kwargs["expected_main"],
                )
        return original(repository, **kwargs)

    monkeypatch.setattr(harness, "_capture_state", corrupt)
    with pytest.raises(RuntimeError):
        _exercise(source, workspace, base, paths)
    assert tuple(workspace.iterdir()) == ()


def test_cleanup_failure_fails_closed_and_source_is_unchanged(
    tmp_path, monkeypatch
):
    source, workspace, base, _ambient, paths = _make_source(tmp_path)
    original = harness._remove_tree

    def remove_then_fail(path):
        original(path)
        raise RuntimeError("injected cleanup failure")

    monkeypatch.setattr(harness, "_remove_tree", remove_then_fail)
    before_snapshot = harness._source_snapshot(source)
    before_status = _status_bytes(source)
    with pytest.raises(RuntimeError, match="cleanup"):
        _exercise(source, workspace, base, paths)
    assert harness._source_snapshot(source) == before_snapshot
    assert _status_bytes(source) == before_status
    assert tuple(workspace.iterdir()) == ()


def test_subprocess_calls_are_argument_vectors_and_never_shell_true():
    source = Path(harness.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    assert len(calls) == 1
    keywords = {item.arg: item.value for item in calls[0].keywords}
    assert isinstance(calls[0].args[0], ast.Name)
    assert isinstance(keywords["shell"], ast.Constant)
    assert keywords["shell"].value is False
    assert isinstance(keywords["check"], ast.Constant)
    assert keywords["check"].value is False
    assert {"stdout", "stderr", "stdin"} <= set(keywords)


def test_safety_import_boundary_and_no_business_module_imports_harness():
    source_path = Path(harness.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not {
        "requests",
        "urllib",
        "torch",
        "lightning",
        "dataset",
    } & imported_roots
    for sibling in source_path.parent.glob("*.py"):
        if sibling == source_path:
            continue
        assert source_path.stem not in sibling.read_text(
            encoding="utf-8", errors="strict"
        )


def test_isolated_helper_import_has_no_output():
    code = (
        "import importlib.util;"
        f"p={str(Path(harness.__file__))!r};"
        "s=importlib.util.spec_from_file_location('isolated_harness',p);"
        "m=importlib.util.module_from_spec(s);"
        "import sys;sys.modules[s.name]=m;"
        "s.loader.exec_module(m)"
    )
    result = subprocess.run(
        (sys.executable, "-c", code),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_checker_runs_shared_harness_and_reports_closed_readiness():
    checker = (
        ROOT
        / "scripts"
        / "check_covapie_hermetic_git_lifecycle_harness_v1.py"
    )
    source = checker.read_text(encoding="utf-8")
    assert '"init", "--bare"' not in source
    assert '"clone"' not in source
    assert '"worktree", "add"' not in source
    result = subprocess.run(
        (sys.executable, str(checker)),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    report = json.loads(result.stdout)
    assert report["all_checks_passed"] is True
    assert report["ambient_head_independence_verified"] is True
    assert report["source_repository_unchanged"] is True
    assert report["temporary_resources_cleaned"] is True
    assert report["ready_for_training"] is False
