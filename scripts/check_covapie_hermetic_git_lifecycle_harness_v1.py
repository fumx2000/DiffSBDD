"""Independent checker for the shared CovaPIE hermetic Git harness V1."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as harness


BASE = "fdbc79d8b5b6c9a9c8d85528321082cff73631a4"
BASE_PARENT = "a677414ffcfe30db463f6bed33d1fbbedb10e398"
BASE_TREE = "3cd390e4ff04d86eb6ef22746edeed7e0264070c"
BASE_SUBJECT = (
    "add CovaPIE stage-global rule evaluation orchestration runtime v1"
)
FORMAL_SUBJECT = "add CovaPIE shared hermetic Git lifecycle harness v1"
STAGE = "covapie_hermetic_git_lifecycle_harness_v1"
HELPER_PATH = (
    Path("src/covalent_ext")
    / "covapie_hermetic_git_lifecycle_harness_v1.py"
)
TEST_PATH = Path("tests") / "test_covapie_hermetic_git_lifecycle_harness_v1.py"
CHECKER_PATH = (
    Path("scripts") / "check_covapie_hermetic_git_lifecycle_harness_v1.py"
)
SUMMARY_PATH = Path("docs") / "covapie_hermetic_git_lifecycle_harness_v1_summary.md"
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
CONTRACT_PATH = (
    DERIVED_ROOT / "covapie_hermetic_git_lifecycle_harness_contract.csv"
)
MANIFEST_PATH = (
    DERIVED_ROOT / "covapie_hermetic_git_lifecycle_harness_manifest.json"
)
EXACT6 = (
    HELPER_PATH,
    TEST_PATH,
    CHECKER_PATH,
    SUMMARY_PATH,
    CONTRACT_PATH,
    MANIFEST_PATH,
)
SUPPORT_PATHS = EXACT6[:4]
FORBIDDEN_IMPORTS = {
    "requests",
    "urllib",
    "torch",
    "lightning",
    "dataset",
}
FORBIDDEN_SUFFIXES = {
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".tmp",
    ".part",
}
EXPECTED_CONTRACT_ROWS = (
    (
        "public_api",
        "exercise_hermetic_git_lifecycle_matrix",
        "requires source_repository|workspace_root|base_commit|formal_commit_subject|exact_paths",
        "true",
    ),
    (
        "base_seed",
        "explicit_base_commit",
        "temporary remote refs/heads/main is seeded only from explicit base_commit",
        "true",
    ),
    (
        "base_seed",
        "ambient_fallback",
        "ambient HEAD|main|origin/main never selects BASE",
        "true",
    ),
    (
        "clone_boundary",
        "clone_source",
        "temporary bare remote only",
        "true",
    ),
    (
        "lifecycle",
        "exact4",
        "pre_commit|detached_candidate_post_commit|formal_main_post_commit_unpushed|formal_main_post_push",
        "true",
    ),
    (
        "topology",
        "detached",
        "main at BASE plus one detached candidate worktree",
        "true",
    ),
    (
        "topology",
        "formal",
        "one main worktree for unpushed and pushed states",
        "true",
    ),
    (
        "candidate",
        "commit_contract",
        "parent=BASE|subject=exact|files=exact_paths|modes=100644",
        "true",
    ),
    (
        "source_safety",
        "snapshot_stability",
        "HEAD|index bytes|status bytes|refs|worktree list are byte-identical",
        "true",
    ),
    (
        "cleanup",
        "temporary_resources",
        "bare remote|clones|detached worktree|temporary refs are absent",
        "true",
    ),
    (
        "safety",
        "network",
        "network_used=false",
        "true",
    ),
    (
        "safety",
        "forbidden_suffixes",
        ".pt|.ckpt|.pth|.pkl|.lmdb|.tar|.zip|.tgz|.npz|.tmp|.part rejected",
        "true",
    ),
    (
        "push",
        "formal_main",
        "ordinary local git push only",
        "true",
    ),
    (
        "reuse_policy",
        "future_stages",
        "shared harness required; copied lifecycle Git fixtures forbidden",
        "true",
    ),
    (
        "readiness",
        "training",
        "ready_for_training=false",
        "true",
    ),
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _run(
    repository: Path,
    *arguments: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    }
    if extra_env:
        environment.update(extra_env)
    result = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            f"local Git command failed rc={result.returncode}: "
            f"{arguments!r}; stdout={result.stdout.strip()!r}; "
            f"stderr={result.stderr.strip()!r}"
        )
    return result


def _verify_base_identity() -> None:
    observed = _run(
        ROOT, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).stdout.splitlines()
    if observed != [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal BASE identity drift")


def _verify_exact6() -> None:
    if len(EXACT6) != 6 or len(set(EXACT6)) != 6:
        raise ValueError("Exact6 declaration drift")
    for relative in EXACT6:
        target = ROOT / relative
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"Exact6 regular-file invariant failed: {relative}")
        if stat.S_IMODE(target.stat(follow_symlinks=False).st_mode) & 0o111:
            raise ValueError(f"Exact6 executable bit forbidden: {relative}")
        if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"Exact6 forbidden suffix: {relative}")
        if target.stat(follow_symlinks=False).st_size > 100 * 1024 * 1024:
            raise ValueError(f"Exact6 file exceeds 100 MiB: {relative}")
    derived_names = tuple(
        sorted(
            path.relative_to(ROOT)
            for path in (ROOT / DERIVED_ROOT).iterdir()
            if path.is_file() or path.is_symlink()
        )
    )
    if derived_names != tuple(sorted((CONTRACT_PATH, MANIFEST_PATH))):
        raise ValueError("stage-derived Exact2 inventory drift")


def _verify_helper_source_and_api() -> None:
    source = (ROOT / HELPER_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
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
    if FORBIDDEN_IMPORTS & imported_roots:
        raise ValueError("helper safety import boundary drift")
    run_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    if len(run_calls) != 1:
        raise ValueError("subprocess call centralization drift")
    keywords = {item.arg: item.value for item in run_calls[0].keywords}
    if (
        not isinstance(run_calls[0].args[0], ast.Name)
        or not isinstance(keywords.get("shell"), ast.Constant)
        or keywords["shell"].value is not False
        or not isinstance(keywords.get("check"), ast.Constant)
        or keywords["check"].value is not False
        or not {"stdout", "stderr", "stdin"} <= set(keywords)
    ):
        raise ValueError("subprocess argument-vector or capture policy drift")
    if (
        "git init --bare" in source
        or "shell=True" in source
        or "clone source_repository" in source
    ):
        raise ValueError("helper forbidden command/source form detected")
    expected_all = (
        "HermeticLifecycleState",
        "HermeticLifecycleMatrixReport",
        "exercise_hermetic_git_lifecycle_matrix",
    )
    if harness.__all__ != expected_all:
        raise ValueError("helper __all__ drift")
    if (
        harness.HermeticLifecycleState.__dataclass_params__.frozen is not True
        or harness.HermeticLifecycleMatrixReport.__dataclass_params__.frozen
        is not True
    ):
        raise ValueError("public lifecycle dataclass is not frozen")
    signature = inspect.signature(
        harness.exercise_hermetic_git_lifecycle_matrix
    )
    parameters = tuple(signature.parameters.values())
    if (
        tuple(item.name for item in parameters)
        != (
            "source_repository",
            "workspace_root",
            "base_commit",
            "formal_commit_subject",
            "exact_paths",
        )
        or tuple(item.kind for item in parameters)
        != (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.KEYWORD_ONLY,
        )
        or any(item.default is not inspect.Parameter.empty for item in parameters)
    ):
        raise ValueError("public helper signature drift")
    hints = get_type_hints(harness.exercise_hermetic_git_lifecycle_matrix)
    if (
        hints.get("source_repository") is not Path
        or hints.get("workspace_root") is not Path
        or hints.get("base_commit") is not str
        or hints.get("formal_commit_subject") is not str
        or hints.get("exact_paths") != tuple[Path, ...]
        or hints.get("return") is not harness.HermeticLifecycleMatrixReport
    ):
        raise ValueError("public helper annotations drift")
    for sibling in (ROOT / "src/covalent_ext").glob("*.py"):
        if sibling == ROOT / HELPER_PATH:
            continue
        if HELPER_PATH.stem in sibling.read_text(encoding="utf-8"):
            raise ValueError(f"business/production helper import detected: {sibling}")


def _verify_report(
    report: harness.HermeticLifecycleMatrixReport,
    *,
    base_commit: str,
    exact_path_count: int,
) -> None:
    states = (
        report.pre_commit,
        report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed,
        report.formal_main_post_push,
    )
    if (
        report.base_commit != base_commit
        or report.candidate_parent != base_commit
        or report.candidate_subject != FORMAL_SUBJECT
        or report.exact_path_count != exact_path_count
        or report.cleanup_verified is not True
        or tuple(state.lifecycle for state in states) != harness.LIFECYCLES
    ):
        raise ValueError("lifecycle report identity drift")
    pre, detached, unpushed, pushed = states
    if (
        pre.head != base_commit
        or pre.main_oid != base_commit
        or pre.origin_main_oid != base_commit
        or pre.branch != "main"
        or pre.worktree_count != 1
        or pre.status_entry_count != exact_path_count
    ):
        raise ValueError("pre-commit matrix drift")
    if (
        detached.head != report.candidate_commit
        or detached.main_oid != base_commit
        or detached.origin_main_oid != base_commit
        or detached.branch != "DETACHED"
        or detached.worktree_count != 2
        or detached.status_entry_count != 0
    ):
        raise ValueError("detached matrix drift")
    if (
        unpushed.head != report.candidate_commit
        or unpushed.main_oid != report.candidate_commit
        or unpushed.origin_main_oid != base_commit
        or unpushed.branch != "main"
        or unpushed.worktree_count != 1
        or unpushed.status_entry_count != 0
    ):
        raise ValueError("formal unpushed matrix drift")
    if (
        pushed.head != report.candidate_commit
        or pushed.main_oid != report.candidate_commit
        or pushed.origin_main_oid != report.candidate_commit
        or pushed.origin_head_resolved_oid != report.candidate_commit
        or pushed.branch != "main"
        or pushed.worktree_count != 1
        or pushed.status_entry_count != 0
    ):
        raise ValueError("formal pushed matrix drift")
    if any(
        state.origin_head_symbolic_target != "refs/remotes/origin/main"
        for state in states
    ):
        raise ValueError("origin/HEAD matrix drift")
    if any(Path(state.repository_path).exists() for state in states):
        raise ValueError("temporary repository path survived cleanup")


def _commit_fixture(repository: Path, subject: str) -> str:
    _run(repository, "add", "--all")
    _run(
        repository,
        "-c",
        "user.name=CovaPIE Checker",
        "-c",
        "user.email=covapie-checker@example.invalid",
        "commit",
        "--no-gpg-sign",
        "-m",
        subject,
        extra_env={
            "GIT_AUTHOR_DATE": "2002-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2002-01-01T00:00:00+00:00",
        },
    )
    return _run(repository, "rev-parse", "HEAD").stdout.strip()


def _verify_guaranteed_ambient_independence(
    temporary_parent: Path,
) -> tuple[str, str]:
    source = temporary_parent / "ambient-source"
    workspace = temporary_parent / "ambient-workspace"
    source.mkdir()
    workspace.mkdir()
    _run(source, "init", "--initial-branch=main")
    (source / "base.txt").write_text("explicit checker base\n", encoding="utf-8")
    base = _commit_fixture(source, "checker explicit base")
    (source / "fixture.txt").write_text(
        "candidate fixture\n", encoding="utf-8"
    )
    (source / "ambient.txt").write_text("ambient drift\n", encoding="utf-8")
    ambient = _commit_fixture(source, "checker ambient commit")
    if (
        ambient == base
        or _run(source, "rev-parse", "HEAD").stdout.strip() != ambient
        or _run(source, "rev-parse", "main").stdout.strip() != ambient
    ):
        raise ValueError("ambient source construction failed")
    before = harness._source_snapshot(source)
    report = harness.exercise_hermetic_git_lifecycle_matrix(
        source,
        workspace,
        base_commit=base,
        formal_commit_subject=FORMAL_SUBJECT,
        exact_paths=(Path("fixture.txt"),),
    )
    _verify_report(report, base_commit=base, exact_path_count=1)
    if harness._source_snapshot(source) != before:
        raise ValueError("ambient source repository changed")
    return base, report.candidate_commit


def _verify_evidence() -> dict[str, object]:
    contract_payload = (ROOT / CONTRACT_PATH).read_bytes()
    reader = csv.DictReader(io.StringIO(contract_payload.decode("utf-8")))
    if reader.fieldnames != ["area", "item", "requirement", "verified"]:
        raise ValueError("contract CSV schema drift")
    rows = tuple(
        (
            row["area"],
            row["item"],
            row["requirement"],
            row["verified"],
        )
        for row in reader
    )
    if rows != EXPECTED_CONTRACT_ROWS:
        raise ValueError("contract CSV rows drift")
    manifest_payload = (ROOT / MANIFEST_PATH).read_bytes()
    manifest = json.loads(manifest_payload)
    required_true = (
        "all_checks_passed",
        "hermetic_base_seed_verified",
        "no_ambient_base_fallback",
        "ambient_head_independence_verified",
        "pre_commit_verified",
        "detached_candidate_post_commit_verified",
        "formal_main_post_commit_unpushed_verified",
        "formal_main_post_push_verified",
        "source_repository_unchanged",
        "temporary_resources_cleaned",
    )
    required_false = (
        "provider_used",
        "network_used",
        "download_used",
        "raw_data_used",
        "model_used",
        "checkpoint_used",
        "dataloader_used",
        "forward_loss_backward_used",
        "optimizer_or_parameter_update_used",
        "training_used",
        "ready_for_training",
    )
    if any(manifest.get(name) is not True for name in required_true):
        raise ValueError("manifest required-true drift")
    if any(manifest.get(name) is not False for name in required_false):
        raise ValueError("manifest required-false drift")
    if manifest.get("base_identity") != {
        "commit": BASE,
        "parent": BASE_PARENT,
        "tree": BASE_TREE,
        "subject": BASE_SUBJECT,
    }:
        raise ValueError("manifest BASE identity drift")
    if manifest.get("exact6_files") != [
        path.as_posix() for path in EXACT6
    ]:
        raise ValueError("manifest Exact6 inventory drift")
    if manifest.get("contract_row_count") != len(rows):
        raise ValueError("manifest contract row count drift")
    if manifest.get("contract_sha256") != _sha256(contract_payload):
        raise ValueError("manifest contract SHA256 drift")
    support_sha = {
        path.as_posix(): _sha256((ROOT / path).read_bytes())
        for path in SUPPORT_PATHS
    }
    if manifest.get("support_file_sha256") != support_sha:
        raise ValueError("manifest support SHA256 drift")
    if manifest.get("future_reuse_policy") != {
        "clone_from_ambient_root_main_or_head_forbidden": True,
        "copying_lifecycle_git_fixtures_forbidden": True,
        "expected_lifecycle_must_not_follow_ambient_state": True,
        "integration_smoke_must_reuse_shared_harness_first": True,
        "shared_harness_required": True,
    }:
        raise ValueError("manifest future reuse policy drift")
    if manifest.get("recommended_next_step") != (
        "run_covapie_stage_global_rule_evaluation_orchestration_"
        "in_memory_integration_smoke_v1"
    ):
        raise ValueError("manifest recommended next step drift")
    return {
        "contract_row_count": len(rows),
        "contract_sha256": _sha256(contract_payload),
        "manifest_sha256": _sha256(manifest_payload),
    }


def main() -> int:
    _verify_base_identity()
    _verify_exact6()
    _verify_helper_source_and_api()
    initial_source = harness._source_snapshot(ROOT)
    with tempfile.TemporaryDirectory(
        prefix="covapie-harness-checker-"
    ) as temporary_name:
        temporary_parent = Path(temporary_name)
        formal_workspace = temporary_parent / "formal-workspace"
        formal_workspace.mkdir()
        formal_report = harness.exercise_hermetic_git_lifecycle_matrix(
            ROOT,
            formal_workspace,
            base_commit=BASE,
            formal_commit_subject=FORMAL_SUBJECT,
            exact_paths=EXACT6,
        )
        _verify_report(formal_report, base_commit=BASE, exact_path_count=6)
        ambient_base, ambient_candidate = (
            _verify_guaranteed_ambient_independence(temporary_parent)
        )
    if harness._source_snapshot(ROOT) != initial_source:
        raise ValueError("formal source repository changed")
    evidence = _verify_evidence()
    report = {
        "all_checks_passed": True,
        "base_commit": BASE,
        "exact6_count": 6,
        "public_api_verified": True,
        "hermetic_base_seed_verified": True,
        "ambient_head_independence_verified": True,
        "ambient_fixture_base_commit": ambient_base,
        "ambient_fixture_candidate_commit": ambient_candidate,
        "pre_commit_verified": True,
        "detached_candidate_post_commit_verified": True,
        "formal_main_post_commit_unpushed_verified": True,
        "formal_main_post_push_verified": True,
        "candidate_commit": formal_report.candidate_commit,
        "candidate_parent": formal_report.candidate_parent,
        "candidate_subject": formal_report.candidate_subject,
        "candidate_changed_file_count": 6,
        "candidate_modes_100644": True,
        "detached_worktree_count": 2,
        "formal_worktree_count": 1,
        "source_repository_unchanged": True,
        "temporary_resources_cleaned": True,
        "network_used": False,
        "download_used": False,
        "training_used": False,
        "ready_for_training": False,
        "recommended_next_step": (
            "run_covapie_stage_global_rule_evaluation_orchestration_"
            "in_memory_integration_smoke_v1"
        ),
        **evidence,
    }
    if (
        report["source_repository_unchanged"] is not True
        or report["temporary_resources_cleaned"] is not True
        or report["ready_for_training"] is not False
    ):
        raise ValueError("checker final safety assertion failed")
    sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
