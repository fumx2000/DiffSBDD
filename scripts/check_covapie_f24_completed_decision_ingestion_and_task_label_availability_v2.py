#!/usr/bin/env python3
"""Independent fail-closed checker for the additive F24 V2 successor."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Sequence
import csv
import hashlib
import inspect
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1
    as f24_v1,
)
from covalent_ext import (  # noqa: E402
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    verify_bound_source_v2,
)


BASELINE_HEAD = "33d08ee6069592f0fe28ca53bed5615f578d10fc"
BASELINE_TREE = "6096cc682516dca829657b9710c021efc8accb4b"
BASELINE_SUBJECT = "add CovaPIE OZJ source binding successor v2"

PRODUCTION_RELATIVE = (
    "src/covalent_ext/"
    "covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
)
CHECKER_RELATIVE = (
    "scripts/"
    "check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
)
TEST_RELATIVE = (
    "tests/"
    "test_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
)
GUIDE_RELATIVE = (
    "docs/"
    "covapie_f24_completed_decision_ingestion_and_task_label_availability_v2_guide.md"
)
EXACT4_PATHS = (
    PRODUCTION_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    GUIDE_RELATIVE,
)

B1_BINDING = (
    Path("src/covalent_ext/covapie_source_binding_policy_v2.py"),
    3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    "published_source_binding_policy_v2",
)
DUAL_V2_BINDINGS = (
    (
        Path(
            "src/covalent_ext/"
            "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        30745,
        "51af9985cf4de28d48cc55eab71b536472220221d160ee6070677512ba22ef21",
        "published_OZJ_V2_successor",
    ),
    (
        Path(
            "scripts/"
            "check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        42913,
        "dec67ac8e86273d49b3da048a7286b900b1171f93ffe85a07a6c1830383dd825",
        "published_OZJ_V2_checker",
    ),
    (
        Path(
            "src/covalent_ext/"
            "covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        21294,
        "a10c929ea86258ac39bc787b3108d622b65c97617e62b19a44bf3711fbffbd52",
        "published_YUN_V2_successor",
    ),
    (
        Path(
            "scripts/"
            "check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        28382,
        "f0de27832eb557d1f1150ecddc00a023c7e1d81642cc1c92ef606b302c2a54b2",
        "published_YUN_V2_checker",
    ),
)
F24_V1_BINDINGS = (
    (
        f24_v1.SOURCE_RELATIVE,
        77160,
        "c67c88f83e535fd4319425459b97dcfc22f90a3b617b5ddbf1e8f315e2de0525",
        "published_F24_V1_owner",
    ),
    (
        f24_v1.CHECKER_RELATIVE,
        15600,
        "d057ff1695f9797fd2c54f9c91737fde6edd7580c471759350d179bb807565a7",
        "published_F24_V1_checker",
    ),
    (
        f24_v1.TEST_RELATIVE,
        23978,
        "f2c0a9c082178db596d98ec051251b71158bb791a2ec55eebecdf9f93bf0cc77",
        "published_F24_V1_tests",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.SNAPSHOT,
        22044,
        "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11",
        "published_F24_V1_snapshot",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.MATRIX,
        7641,
        "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c",
        "published_F24_V1_matrix",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.SUMMARY,
        3462,
        "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385",
        "published_F24_V1_summary",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.MANIFEST,
        16125,
        "02f56545297fb78c2b2cbd205115d9dca680a8446bfb753109428b698bdd5dfd",
        "published_F24_V1_manifest",
    ),
)

CURRENT_2A2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"
)
CURRENT_2A2_BINDINGS = (
    (
        CURRENT_2A2_ROOT
        / "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.csv",
        529994,
        "5b56422e9c8d0ec6c09fe71c49d51fff0c7e7a9720ccf3c4c20dc324e409c57d",
        "current_2A2_global_census_matrix",
    ),
    (
        CURRENT_2A2_ROOT
        / "covapie_cumulative1000_current_global_readiness_summary_with_2a2_v1.json",
        17389,
        "3217bf5e45de40e66f1af22d000a48fef81548c6431c3e6d9349c4824b1c80f3",
        "current_2A2_global_census_summary",
    ),
    (
        CURRENT_2A2_ROOT
        / "covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json",
        47068,
        "c30f8f52fc20495a06f7bead98ac80197f434eeb0b4776a1ef2c152f13d1e2b7",
        "current_2A2_global_census_manifest",
    ),
)

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
MAX_FILE_BYTES = 1024 * 1024
_FORBIDDEN_F24_V1_CALLS = {
    "_resolve_binding_path",
    "_verify_binding",
    "_verify_bindings",
    "_run_formal_validator",
    "load_frozen_formal_decision_v1",
    "_candidate_source_bindings",
    "_build_artifacts_unvalidated",
    "build_artifacts_v1",
    "validate_completed_decision_projection_v1",
    "_atomic_write",
    "materialize_artifacts_v1",
    "check_materialized_v1",
    "main",
}
_FORBIDDEN_OZJ_V1_CALLS = {
    "_verify_payload",
    "load_frozen_formal_decision_v1",
    "build_artifacts_v1",
    "_build_artifacts_unvalidated",
    "materialize_artifacts_v1",
    "check_materialized_v1",
}
_FORBIDDEN_YUN_V1_CALLS = {
    "_verify_payload",
    "load_frozen_formal_decision_v1",
    "build_artifacts_v1",
    "_build_artifacts_unvalidated",
    "materialize_artifacts_v1",
    "check_materialized_v1",
}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(*arguments: str, root: Path = ROOT) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        raise ValueError("GIT_COMMAND_FAILED:" + arguments[0])
    return completed.stdout.rstrip("\n")


def _read_regular(path: Path, label: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ValueError("SOURCE_LSTAT_FAILED:" + label) from error
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("SOURCE_NOT_REGULAR_NON_SYMLINK:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError("SOURCE_READ_FAILED:" + label) from error


def _validate_text(payload: bytes, label: str) -> None:
    if not payload or len(payload) >= MAX_FILE_BYTES:
        raise ValueError("FILE_SIZE_INVALID:" + label)
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("UTF8_INVALID:" + label) from error
    if "\x00" in text or "\r" in text:
        raise ValueError("NUL_OR_CR_FORBIDDEN:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("TERMINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def classify_lifecycle_from_facts(
    *,
    tracked_exact4: set[str],
    ordinary_untracked: set[str],
    status_entries: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    expected = set(EXACT4_PATHS)
    expected_status = tuple(f"?? {path}" for path in sorted(expected))
    if (
        not tracked_exact4
        and ordinary_untracked == expected
        and tuple(sorted(status_entries)) == expected_status
        and not working_diff
        and not cached_diff
    ):
        return "CANDIDATE_UNTRACKED"
    if (
        tracked_exact4 == expected
        and not ordinary_untracked
        and not status_entries
        and not working_diff
        and not cached_diff
    ):
        return "TRACKED_CLEAN"
    raise ValueError("GIT_LIFECYCLE_PROFILE_INVALID")


def _validate_repository_relation_v2(
    *,
    profile: str,
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    parent_shas: tuple[str, ...],
    changed_paths: set[str],
) -> None:
    expected = set(EXACT4_PATHS)
    if profile == "CANDIDATE_UNTRACKED":
        if not (
            head == BASELINE_HEAD
            and origin_main == BASELINE_HEAD
            and (ahead, behind) == (0, 0)
        ):
            raise ValueError("CANDIDATE_REPOSITORY_RELATION_INVALID")
        return
    if profile != "TRACKED_CLEAN":
        raise ValueError("REPOSITORY_RELATION_PROFILE_INVALID")
    if (
        head == BASELINE_HEAD
        or parent_shas != (BASELINE_HEAD,)
        or changed_paths != expected
    ):
        raise ValueError("TRACKED_CLEAN_COMMIT_IDENTITY_INVALID")
    committed_unpushed = (
        origin_main == BASELINE_HEAD and (ahead, behind) == (1, 0)
    )
    published_fast_forward = origin_main == head and (ahead, behind) == (0, 0)
    if not (committed_unpushed or published_fast_forward):
        raise ValueError("TRACKED_CLEAN_REPOSITORY_RELATION_INVALID")


def verify_git_lifecycle(root: Path = ROOT) -> str:
    identity = _git(
        "show", "-s", "--format=%T%n%s", BASELINE_HEAD, root=root
    ).splitlines()
    if identity != [BASELINE_TREE, BASELINE_SUBJECT]:
        raise ValueError("BASELINE_TREE_OR_SUBJECT_INVALID")
    expected = set(EXACT4_PATHS)
    tracked = {
        line
        for line in _git("ls-files", "--", *sorted(expected), root=root).splitlines()
        if line
    }
    untracked = {
        line
        for line in _git(
            "ls-files", "--others", "--exclude-standard", root=root
        ).splitlines()
        if line
    }
    status = tuple(
        line
        for line in _git(
            "status", "--porcelain=v1", "--untracked-files=all", root=root
        ).splitlines()
        if line
    )
    working = {
        line for line in _git("diff", "--name-only", root=root).splitlines() if line
    }
    cached = {
        line
        for line in _git("diff", "--cached", "--name-only", root=root).splitlines()
        if line
    }
    profile = classify_lifecycle_from_facts(
        tracked_exact4=tracked,
        ordinary_untracked=untracked,
        status_entries=status,
        working_diff=working,
        cached_diff=cached,
    )
    head = _git("rev-parse", "HEAD", root=root)
    origin = _git("rev-parse", "origin/main", root=root)
    relation = _git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main", root=root
    ).split()
    if len(relation) != 2 or any(not value.isdigit() for value in relation):
        raise ValueError("REPOSITORY_RELATION_COUNT_INVALID")
    ahead, behind = (int(value) for value in relation)
    if profile == "TRACKED_CLEAN":
        parent_shas = tuple(
            _git("show", "-s", "--format=%P", "HEAD", root=root).split()
        )
        changed_paths = {
            line
            for line in _git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD",
                root=root,
            ).splitlines()
            if line
        }
    else:
        parent_shas = ()
        changed_paths = set()
    _validate_repository_relation_v2(
        profile=profile,
        head=head,
        origin_main=origin,
        ahead=ahead,
        behind=behind,
        parent_shas=parent_shas,
        changed_paths=changed_paths,
    )
    return profile


def verify_exact4_file_hygiene(root: Path = ROOT) -> list[dict[str, object]]:
    if len(EXACT4_PATHS) != 4 or len(set(EXACT4_PATHS)) != 4:
        raise ValueError("EXACT4_INVENTORY_INVALID")
    if any(path.endswith((".json", ".csv")) for path in EXACT4_PATHS):
        raise ValueError("V2_DATA_ARTIFACT_FORBIDDEN")
    result: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular(path, "EXACT4:" + relative)
        _validate_text(payload, relative)
        mode = stat.S_IMODE(path.lstat().st_mode)
        if mode not in {0o644, 0o664} or mode & 0o111:
            raise ValueError("EXACT4_LIVE_MODE_INVALID:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT4_FORBIDDEN_SUFFIX:" + relative)
        result.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "line_count": len(payload.decode("utf-8").splitlines()),
                "mode": f"{mode:04o}",
                "sha256": _sha(payload),
            }
        )
    return result


def _function_nodes(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }


def _local_calls(node: ast.AST) -> set[str]:
    return {
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }


def _reachable_functions(
    functions: dict[str, ast.FunctionDef], roots: set[str]
) -> set[str]:
    reached: set[str] = set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in reached or name not in functions:
            continue
        reached.add(name)
        pending.extend(_local_calls(functions[name]) - reached)
    return reached


def _module_attribute_calls(tree: ast.AST, module_name: str) -> set[str]:
    return {
        call.func.attr
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == module_name
    }


def _verify_public_api() -> None:
    if subject.__all__ != (
        "F24SourceBindingV2Error",
        "load_frozen_f24_authority_v2",
        "verify_published_f24_v1_projection_v2",
    ):
        raise ValueError("PUBLIC_API_INVENTORY_INVALID")
    if not issubclass(subject.F24SourceBindingV2Error, ValueError):
        raise ValueError("PUBLIC_ERROR_FAMILY_INVALID")
    expected = {
        "load_frozen_f24_authority_v2": (
            "repo_root",
            "formal_decision_path",
            "repository_path_overrides",
        ),
        "verify_published_f24_v1_projection_v2": (
            "repo_root",
            "repository_path_overrides",
        ),
    }
    for name, parameter_names in expected.items():
        parameters = tuple(inspect.signature(getattr(subject, name)).parameters.values())
        if tuple(parameter.name for parameter in parameters) != parameter_names:
            raise ValueError("PUBLIC_SIGNATURE_INVALID:" + name)
        if any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in parameters
        ):
            raise ValueError("PUBLIC_SIGNATURE_NOT_KEYWORD_ONLY:" + name)
    public_names = {name for name in vars(subject) if not name.startswith("_")}
    forbidden = (
        "formal_validator_path",
        "execute_formal_validator",
        "materialize",
        "mutation",
        "registry",
        "resolver",
        "cache",
    )
    if any(token in name for token in forbidden for name in public_names):
        raise ValueError("FORBIDDEN_PUBLIC_FRAMEWORK_OR_MUTATION_API")


def _verify_production_ast(root: Path) -> dict[str, object]:
    text = _read_regular(root / PRODUCTION_RELATIVE, "F24_V2_PRODUCTION").decode(
        "utf-8"
    )
    tree = ast.parse(text)
    functions = _function_nodes(tree)
    wrapper = functions.get("_verify_source")
    if wrapper is None:
        raise ValueError("BOUND_SOURCE_WRAPPER_MISSING")
    calls = [
        call
        for call in ast.walk(wrapper)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "verify_bound_source_v2"
    ]
    if len(calls) != 1:
        raise ValueError("BOUND_SOURCE_HELPER_CALL_INVALID")
    reachable = _reachable_functions(
        functions,
        {
            "load_frozen_f24_authority_v2",
            "verify_published_f24_v1_projection_v2",
        },
    )
    for required in (
        "_verify_source",
        "_expected_executable_from_legacy_mode",
        "_exercise_published_ozj_v2_predecessor",
        "_exercise_published_yun_v2_predecessor",
        "_validate_semantic_owner_payloads",
        "_validate_runtime_module_source",
    ):
        if required not in reachable:
            raise ValueError("REQUIRED_ACTIVE_CALL_PATH_MISSING:" + required)
    direct_reads = [
        call.func.attr if isinstance(call.func, ast.Attribute) else call.func.id
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and (
            (
                isinstance(call.func, ast.Attribute)
                and call.func.attr in {"read_bytes", "read_text", "open"}
            )
            or (isinstance(call.func, ast.Name) and call.func.id == "open")
        )
    ]
    if direct_reads:
        raise ValueError("DIRECT_SOURCE_READ_BYPASSES_B1")
    f24_calls = _module_attribute_calls(tree, "f24_v1")
    if f24_calls & _FORBIDDEN_F24_V1_CALLS:
        raise ValueError("FORBIDDEN_F24_V1_ACTIVE_SOURCE_PATH_CALLED")
    if _module_attribute_calls(tree, "ozj_v1"):
        raise ValueError("OZJ_V1_ACTIVE_REFERENCE_FORBIDDEN")
    if _module_attribute_calls(tree, "yun_v1"):
        raise ValueError("YUN_V1_ACTIVE_REFERENCE_FORBIDDEN")
    ozj_calls = _module_attribute_calls(tree, "ozj_v2")
    yun_calls = _module_attribute_calls(tree, "yun_v2")
    if "verify_published_ozj_v1_projection_v2" not in ozj_calls:
        raise ValueError("PUBLISHED_OZJ_V2_PREDECESSOR_NOT_ACTIVE")
    if "verify_published_yun_v1_projection_v2" not in yun_calls:
        raise ValueError("PUBLISHED_YUN_V2_PREDECESSOR_NOT_ACTIVE")
    if any(
        token in text
        for token in (
            "stat.S_IMODE",
            ".st_mode",
            "SOURCE_MODE_DRIFT",
            "BOUND_SOURCE_MODE_MISMATCH",
            "subprocess.run",
        )
    ):
        raise ValueError("HIDDEN_MODE_OR_SUBPROCESS_GATE_FORBIDDEN")
    load_node = functions["load_frozen_f24_authority_v2"]
    semantic_lines = [
        call.lineno
        for call in ast.walk(load_node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_validate_semantic_owner_payloads"
    ]
    runtime_lines = [
        call.lineno
        for call in ast.walk(load_node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "f24_v1"
        and call.func.attr == "_validate_formal_decision_v1"
    ]
    if len(semantic_lines) != 1 or len(runtime_lines) != 1:
        raise ValueError("RUNTIME_BINDING_ORDER_CALLS_INVALID")
    if semantic_lines[0] >= runtime_lines[0]:
        raise ValueError("RUNTIME_OWNER_NOT_BOUND_BEFORE_ROLE_VALIDATION")
    return {
        "b1_bound_source_helper_used": True,
        "direct_source_read_bypass_count": 0,
        "exact_posix_semantic_mode_active": False,
        "f24_v1_source_gate_active": False,
        "f24_v1_verify_binding_active": False,
        "f24_v1_verify_bindings_active": False,
        "f24_v1_loader_active": False,
        "f24_v1_subprocess_validator_active": False,
        "f24_v1_materialization_active": False,
        "ozj_v1_source_gate_active": False,
        "yun_v1_source_gate_active": False,
        "ozj_v2_successor_called": True,
        "yun_v2_successor_called": True,
        "runtime_bound_before_role_validation": True,
        "reused_f24_v1_function_names": sorted(f24_calls),
    }


def _verify_f24_v1_pure_call_graph(root: Path) -> None:
    production_tree = ast.parse(
        _read_regular(root / PRODUCTION_RELATIVE, "F24_V2_PRODUCTION").decode(
            "utf-8"
        )
    )
    roots = _module_attribute_calls(production_tree, "f24_v1")
    v1_tree = ast.parse(
        _read_regular(root / f24_v1.SOURCE_RELATIVE, "F24_V1_OWNER").decode(
            "utf-8"
        )
    )
    reachable = _reachable_functions(_function_nodes(v1_tree), roots)
    if reachable & _FORBIDDEN_F24_V1_CALLS:
        raise ValueError("REUSED_F24_V1_HELPER_REACHES_FORBIDDEN_PATH")
    if "_validate_formal_decision_v1" in roots and (
        "_validate_published_runtime" not in reachable
    ):
        raise ValueError("F24_V1_RUNTIME_TRANSITIVE_DEPENDENCY_NOT_PROVEN")


def _verify_predecessor_call_graph(
    root: Path,
    relative: Path,
    module_name: str,
    public_roots: set[str],
    forbidden_v1_calls: set[str],
) -> None:
    tree = ast.parse(
        _read_regular(root / relative, module_name + "_V2_OWNER").decode("utf-8")
    )
    reachable = _reachable_functions(_function_nodes(tree), public_roots)
    if "_verify_source" not in reachable:
        raise ValueError(module_name + "_BOUND_SOURCE_PATH_NOT_ACTIVE")
    calls = _module_attribute_calls(tree, module_name.lower() + "_v1")
    if calls & forbidden_v1_calls:
        raise ValueError(module_name + "_V2_REACHES_V1_SOURCE_GATE")


def _verify_bound_bindings(
    root: Path, bindings: Sequence[tuple[Path, int, str, str]]
) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, byte_count, sha256, label in bindings:
        payload = verify_bound_source_v2(
            path=root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=False,
        )
        observed[relative.as_posix()] = _sha(payload)
    return observed


def _verify_published_commit_ancestry(root: Path) -> None:
    for commit in (
        subject.OZJ_V2_PUBLISHED_COMMIT,
        subject.YUN_V2_PUBLISHED_COMMIT,
    ):
        if _git("show", "-s", "--format=%H", commit, root=root) != commit:
            raise ValueError("PUBLISHED_PREDECESSOR_COMMIT_MISSING:" + commit)


def _verify_v1_false_failure_contract(root: Path) -> bool:
    text = _read_regular(root / f24_v1.SOURCE_RELATIVE, "F24_V1_OWNER").decode(
        "utf-8"
    )
    function = _function_nodes(ast.parse(text)).get("_verify_binding")
    if function is None:
        raise ValueError("F24_V1_VERIFY_BINDING_MISSING")
    segment = ast.get_source_segment(text, function) or ""
    if not all(
        token in segment
        for token in (
            "stat.S_IMODE",
            "metadata.st_mode",
            "SOURCE_MODE_DRIFT",
        )
    ):
        raise ValueError("F24_V1_EXACT_MODE_FALSE_FAILURE_NOT_PROVEN")
    binding = f24_v1.FORMAL_BINDINGS[0]
    with tempfile.TemporaryDirectory(prefix="covapie_f24_v1_contrast_") as name:
        replacement = Path(name) / binding[0].name
        shutil.copyfile(root.parent / binding[0], replacement)
        replacement.chmod(0o644)
        try:
            f24_v1._verify_binding(root, binding, {binding[0]: replacement})
        except f24_v1.F24IngestionSafetyError as error:
            if "SOURCE_MODE_DRIFT" not in str(error):
                raise ValueError("F24_V1_FALSE_FAILURE_TOKEN_MISSING") from error
        else:
            raise ValueError("F24_V1_SAFE_MODE_DRIFT_DID_NOT_FALSE_FAIL")
        subject.load_frozen_f24_authority_v2(
            repo_root=root,
            formal_decision_path=replacement,
        )
    return True


def _exercise_mode_regressions(root: Path) -> dict[str, bool]:
    mode_bound = (
        (f24_v1.FORMAL_BINDINGS[0], "formal_decision"),
        (f24_v1.FORMAL_BINDINGS[1], "formal_validator_py"),
        (f24_v1.PREPARATION_BINDINGS[-1], "review_validator_py"),
    )
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_f24_v2_modes_") as name:
        temporary = Path(name)
        for binding, label in mode_bound:
            relative = binding[0]
            replacement = temporary / (label + relative.suffix)
            shutil.copyfile(root.parent / relative, replacement)
            for mode in (0o600, 0o644, 0o660, 0o664):
                replacement.chmod(mode)
                key = f"{label}_{mode:04o}"
                subject.load_frozen_f24_authority_v2(
                    repo_root=root,
                    repository_path_overrides={relative: replacement},
                )
                result[key] = True
            for mode in (0o755, 0o666, 0o777):
                replacement.chmod(mode)
                key = f"{label}_{mode:04o}"
                try:
                    subject.load_frozen_f24_authority_v2(
                        repo_root=root,
                        repository_path_overrides={relative: replacement},
                    )
                except subject.F24SourceBindingV2Error as error:
                    token = (
                        "SOURCE_WORLD_WRITABLE"
                        if mode & 0o002
                        else "SOURCE_EXECUTABLE_CLASS_MISMATCH"
                    )
                    if token not in str(error):
                        raise ValueError(
                            "UNSAFE_MODE_FAILURE_TOKEN_MISSING:" + key
                        ) from error
                    result[key] = True
                else:
                    raise ValueError("UNSAFE_MODE_ACCEPTED:" + key)
    return result


def _exercise_source_failure_regressions(root: Path) -> dict[str, bool]:
    binding = f24_v1.FORMAL_BINDINGS[0]
    relative = binding[0]
    canonical = root.parent / relative
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_f24_v2_failures_") as name:
        temporary = Path(name)
        wrong_bytes = temporary / "wrong-bytes.json"
        shutil.copyfile(canonical, wrong_bytes)
        wrong_bytes.write_bytes(wrong_bytes.read_bytes() + b"\n")
        try:
            subject.load_frozen_f24_authority_v2(
                repo_root=root,
                formal_decision_path=wrong_bytes,
            )
        except subject.F24SourceBindingV2Error as error:
            if "SOURCE_BYTE_COUNT_MISMATCH" not in str(error):
                raise ValueError("WRONG_BYTE_COUNT_TOKEN_MISSING") from error
            result["wrong_byte_count_rejected"] = True
        else:
            raise ValueError("WRONG_BYTE_COUNT_ACCEPTED")

        wrong_sha = temporary / "wrong-sha.json"
        shutil.copyfile(canonical, wrong_sha)
        payload = bytearray(wrong_sha.read_bytes())
        payload[0] ^= 1
        wrong_sha.write_bytes(payload)
        try:
            subject.load_frozen_f24_authority_v2(
                repo_root=root,
                formal_decision_path=wrong_sha,
            )
        except subject.F24SourceBindingV2Error as error:
            if "SOURCE_SHA256_MISMATCH" not in str(error):
                raise ValueError("WRONG_SHA_TOKEN_MISSING") from error
            result["same_size_wrong_sha_rejected"] = True
        else:
            raise ValueError("WRONG_SHA_ACCEPTED")

        target = temporary / "target.json"
        shutil.copyfile(canonical, target)
        link = temporary / "source-link.json"
        link.symlink_to(target.name)
        try:
            subject.load_frozen_f24_authority_v2(
                repo_root=root,
                formal_decision_path=link,
            )
        except subject.F24SourceBindingV2Error as error:
            if "SOURCE_SYMLINK_FORBIDDEN" not in str(error):
                raise ValueError("SYMLINK_TOKEN_MISSING") from error
            result["symlink_rejected"] = True
        else:
            raise ValueError("SYMLINK_ACCEPTED")

        try:
            subject.load_frozen_f24_authority_v2(
                repo_root=root,
                repository_path_overrides={Path("unexpected.txt"): target},
            )
        except subject.F24SourceBindingV2Error as error:
            if "REPOSITORY_PATH_OVERRIDE_UNEXPECTED" not in str(error):
                raise ValueError("UNEXPECTED_OVERRIDE_TOKEN_MISSING") from error
            result["unexpected_override_rejected"] = True
        else:
            raise ValueError("UNEXPECTED_OVERRIDE_ACCEPTED")
    return result


def _verify_scientific_semantics(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    approval = formal["human_approval"]  # type: ignore[index]
    events = formal["event_level_human_decisions"]  # type: ignore[index]
    role = formal["selected_role_partition"]  # type: ignore[index]
    chemical = formal["chemical_warhead_annotation"]  # type: ignore[index]
    distinction = formal[  # type: ignore[index]
        "chemical_warhead_vs_role_region_distinction"
    ]
    training = f24_v1._training_boundary()
    geometry = f24_v1._geometry_boundary()
    reusable = f24_v1._reusable_boundary()
    tasks = f24_v1._canonical_task_contract()
    if (
        len(events) != 4
        or tuple(event["canonical_event_id"] for event in events)
        != f24_v1.EXPECTED_EVENT_IDS
        or [event["scaleup_rank"] for event in events]
        != list(f24_v1.EXPECTED_RANKS)
        or any(event["pdb_id"] != "3V4X" for event in events)
        or any(event["protein_residue"] != "CYS:111-" for event in events)
        or any(event["protein_reactive_atom"] != "SG" for event in events)
        or any(event["ligand_reactive_atom"] != "C8" for event in events)
        or approval["D1_task_relevance"] != "RELEVANT"
        or approval["D2_chemistry"] != "POSITIVE"
        or approval["D3_reactive_pair"] != "CONFIRM_OBSERVED_PAIR"
        or approval["D4_role_partition"] != "REVISE_ROLE_PARTITION"
        or approval["D5_training_use"] != "INCLUDE"
        or approval["D6_scientific_context"] != f24_v1.EXPECTED_D6
        or approval["human_selected_role_candidate_index_0based"] is not None
        or approval["machine_auto_selection_performed"] is not False
        or role["role_profile"] != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        or role["warhead_role_atom_ids"] != list(f24_v1.WARHEAD_ROLE)
        or role["linker_atom_ids"] != []
        or role["scaffold_atom_ids"] != list(f24_v1.SCAFFOLD_ROLE)
        or role["selected_candidate_index_0based"] is not None
        or role["machine_candidate_selected"] is not False
        or role["role_partition_source"]
        != "EXTERNAL_HUMAN_REVISED_ROLE_PARTITION"
        or role["direct_scaffold_warhead_boundary"]
        != {
            "bond_order": "SING",
            "boundary_valid": True,
            "scaffold_atom_id": "C5",
            "warhead_atom_id": "C2",
        }
        or chemical["chemical_warhead_atom_ids"]
        != list(f24_v1.CHEMICAL_WARHEAD)
        or chemical["human_authoritative"] is not True
        or distinction["sets_are_intentionally_distinct"] is not True
        or set(f24_v1.CHEMICAL_WARHEAD) == set(f24_v1.WARHEAD_ROLE)
        or {"C4", "O5"} & set(f24_v1.CHEMICAL_WARHEAD)
        or not {"C4", "O5"} <= set(f24_v1.WARHEAD_ROLE)
        or tasks["global_canonical_task_count"] != 5
        or tasks["direct_profile_applicable_task_ids"] != [0, 3, 4]
        or tasks["B3_present"] is not True
        or tasks["sixth_task_present"] is not False
        or training["human_training_excluded"] is not False
        or training["training_use_allowed"] is not True
        or training["training_use_include"] is not True
        or training["candidate_for_future_training_admission"] is not True
        or training["future_training_candidate_derived_by_ingestion"] is not True
        or training["future_training_candidate_is_training_admission"] is not False
        or training["training_admitted"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["current_runtime_model_usable"] is not False
        or training["ready_for_training"] is not False
        or geometry["POST_source_evidence_count"] != 4
        or geometry["POST_geometry_training_authority_created"] is not False
        or geometry["PRE_topology_authority_available"] is not False
        or geometry["PRE_geometry_authority_available"] is not False
        or geometry["PRE_reconstruction_performed"] is not False
        or geometry["POST_to_PRE_copy_performed"] is not False
        or geometry["PRE_zero_fill_performed"] is not False
        or set(reusable.values()) != {False}
    ):
        raise ValueError("F24_V2_SCIENTIFIC_EQUIVALENCE_INVALID")


def _verify_historical_census(bound: dict[str, object]) -> dict[str, int]:
    census = bound["current_published_census_boundary"]
    observed = {
        "positive": census["positive"],  # type: ignore[index]
        "relevant": census["relevant"],  # type: ignore[index]
        "include": census["training_INCLUDE"],  # type: ignore[index]
        "exclude": census["training_EXCLUDE"],  # type: ignore[index]
        "future": census["future_candidates"],  # type: ignore[index]
        "pair": census["pair_sample_authority"],  # type: ignore[index]
        "role": census["role_sample_authority"],  # type: ignore[index]
    }
    expected = {
        "positive": 104,
        "relevant": 105,
        "include": 40,
        "exclude": 64,
        "future": 23,
        "pair": 104,
        "role": 104,
    }
    if observed != expected or census["current_F24_status"] != "CURRENTLY_UNREVIEWED":  # type: ignore[index]
        raise ValueError("HISTORICAL_F24_PRIOR_CENSUS_DRIFT")
    return observed  # type: ignore[return-value]


def _verify_current_2a2_census(root: Path) -> dict[str, int]:
    payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, label in CURRENT_2A2_BINDINGS:
        payloads[relative] = verify_bound_source_v2(
            path=root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=False,
        )
    try:
        summary = json.loads(payloads[CURRENT_2A2_BINDINGS[1][0]])
    except json.JSONDecodeError as error:
        raise ValueError("CURRENT_2A2_SUMMARY_JSON_INVALID") from error
    tasks = {
        task["display_alias"]: task["structurally_applicable_authoritative_role_count"]
        for task in summary.get("canonical_exact5", {}).get("tasks", [])
    }
    observed = {
        "positive": summary.get("chemistry", {}).get("POSITIVE", {}).get("count"),
        "relevant": summary.get("task_relevance", {}).get("RELEVANT", {}).get(
            "count"
        ),
        "include": summary.get("training_use", {}).get("INCLUDE", {}).get("count"),
        "exclude": summary.get("training_use", {})
        .get("EXCLUDE_FROM_TRAINING_ONLY", {})
        .get("count"),
        "future": summary.get("training_stage", {}).get(
            "future_training_admission_candidate_count"
        ),
        "pair": summary.get("reactive_pair", {}).get(
            "sample_level_authoritative_pair_count"
        ),
        "role": summary.get("role", {}).get(
            "role_partition_sample_authoritative_count"
        ),
        "A": tasks.get("A"),
        "B": tasks.get("B"),
        "B2": tasks.get("B2"),
        "B3": tasks.get("B3"),
        "C": tasks.get("C"),
    }
    expected = {
        "positive": 112,
        "relevant": 113,
        "include": 44,
        "exclude": 68,
        "future": 27,
        "pair": 112,
        "role": 112,
        "A": 112,
        "B": 52,
        "B2": 52,
        "B3": 112,
        "C": 112,
    }
    if observed != expected:
        raise ValueError("CURRENT_2A2_GLOBAL_CENSUS_DRIFT")
    return observed  # type: ignore[return-value]


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = verify_exact4_file_hygiene(root)
    _verify_public_api()
    ast_result = _verify_production_ast(root)
    _verify_f24_v1_pure_call_graph(root)
    _verify_predecessor_call_graph(
        root,
        subject.OZJ_V2_RELATIVE,
        "OZJ",
        {"load_frozen_ozj_authority_v2", "verify_published_ozj_v1_projection_v2"},
        _FORBIDDEN_OZJ_V1_CALLS,
    )
    _verify_predecessor_call_graph(
        root,
        subject.YUN_V2_RELATIVE,
        "YUN",
        {"load_frozen_yun_authority_v2", "verify_published_yun_v1_projection_v2"},
        _FORBIDDEN_YUN_V1_CALLS,
    )
    _verify_published_commit_ancestry(root)
    b1 = _verify_bound_bindings(root, (B1_BINDING,))
    dual = _verify_bound_bindings(root, DUAL_V2_BINDINGS)
    v1 = _verify_bound_bindings(root, F24_V1_BINDINGS)
    bound = subject.load_frozen_f24_authority_v2(repo_root=root)
    _verify_scientific_semantics(bound)
    artifacts = subject.verify_published_f24_v1_projection_v2(repo_root=root)
    historical_census = _verify_historical_census(bound)
    current_census = _verify_current_2a2_census(root)
    v1_false_failure = _verify_v1_false_failure_contract(root)
    mode_regressions = _exercise_mode_regressions(root)
    source_failures = _exercise_source_failure_regressions(root)

    binding = bound["source_binding_v2"]
    expected_binding = {
        "combined_helper": "verify_bound_source_v2",
        "legacy_mode_metadata_classification": [
            "LEGACY_PROVENANCE_METADATA_PRESERVED",
            "SECURITY_EXECUTABLE_CLASS_INPUT",
        ],
        "historical_mode_bound_source_count": 8,
        "historical_modes": ["0664"] * 8,
        "expected_executable_classes": [False] * 8,
        "formal_validator_expected_executable": False,
        "review_package_validator_expected_executable": False,
        "exact_posix_numeric_mode_semantic_acceptance": False,
    }
    if binding != expected_binding:
        raise ValueError("F24_V2_SOURCE_BINDING_CLASSIFICATION_INVALID")
    predecessor = bound["dual_published_v2_predecessors"]
    expected_predecessor = {
        "published_OZJ_V2_successor_bound": True,
        "OZJ_V2_sha256": subject.OZJ_V2_SHA256,
        "OZJ_V2_published_commit": subject.OZJ_V2_PUBLISHED_COMMIT,
        "OZJ_V2_projection_actually_called": True,
        "OZJ_V1_ingestion_projection_preserved": True,
        "published_YUN_V2_successor_bound": True,
        "YUN_V2_sha256": subject.YUN_V2_SHA256,
        "YUN_V2_published_commit": subject.YUN_V2_PUBLISHED_COMMIT,
        "YUN_V2_projection_actually_called": True,
        "YUN_V1_DIRECT_INCLUDE_projection_preserved": True,
    }
    if predecessor != expected_predecessor:
        raise ValueError("DUAL_V2_PREDECESSOR_RECORD_INVALID")

    result = {
        "lifecycle": lifecycle,
        "exact4": exact4,
        "b1_bindings": b1,
        "dual_v2_bindings": dual,
        "f24_v1_bindings": v1,
        "f24_v1_bytes_preserved": True,
        "f24_v1_artifacts_preserved": tuple(artifacts) == f24_v1.OUTPUT_FILENAMES,
        "b1_bound_source_helper_used": ast_result["b1_bound_source_helper_used"],
        "direct_source_read_bypass_count": ast_result[
            "direct_source_read_bypass_count"
        ],
        "ozj_v2_successor_bound": ast_result["ozj_v2_successor_called"],
        "ozj_v2_projection_exercised": predecessor[
            "OZJ_V2_projection_actually_called"
        ],
        "yun_v2_successor_bound": ast_result["yun_v2_successor_called"],
        "yun_v2_projection_exercised": predecessor[
            "YUN_V2_projection_actually_called"
        ],
        "f24_v1_source_gate_active": ast_result["f24_v1_source_gate_active"],
        "f24_v1_verify_binding_active": ast_result[
            "f24_v1_verify_binding_active"
        ],
        "f24_v1_verify_bindings_active": ast_result[
            "f24_v1_verify_bindings_active"
        ],
        "f24_v1_loader_active": ast_result["f24_v1_loader_active"],
        "f24_v1_subprocess_validator_active": ast_result[
            "f24_v1_subprocess_validator_active"
        ],
        "f24_v1_materialization_active": ast_result[
            "f24_v1_materialization_active"
        ],
        "ozj_v1_source_gate_active": ast_result["ozj_v1_source_gate_active"],
        "yun_v1_source_gate_active": ast_result["yun_v1_source_gate_active"],
        "runtime_bound_before_role_validation": ast_result[
            "runtime_bound_before_role_validation"
        ],
        "exact_posix_semantic_mode_active": ast_result[
            "exact_posix_semantic_mode_active"
        ],
        "historical_mode_bound_source_count": 8,
        "all_mode_bound_sources_expected_nonexecutable": True,
        "formal_validator_expected_nonexecutable": True,
        "review_validator_expected_nonexecutable": True,
        "v1_false_failure_token": "SOURCE_MODE_DRIFT",
        "v1_false_failure_contrast_proven": v1_false_failure,
        "mode_regressions": mode_regressions,
        "source_failure_regressions": source_failures,
        "chemical_warhead_role_region_distinction_preserved": True,
        "direct_exact5_applicability_preserved": True,
        "include_future_candidate_preserved": True,
        "historical_prior_census": historical_census,
        "historical_prior_census_preserved": True,
        "current_global_census": current_census,
        "current_census_unchanged": True,
        "covapie_state_unchanged": True,
        "historical_validators_unchanged": True,
        "ready_for_v2_b2_6": True,
        "ready_for_training": False,
    }
    required_true = (
        "f24_v1_bytes_preserved",
        "f24_v1_artifacts_preserved",
        "b1_bound_source_helper_used",
        "ozj_v2_successor_bound",
        "ozj_v2_projection_exercised",
        "yun_v2_successor_bound",
        "yun_v2_projection_exercised",
        "runtime_bound_before_role_validation",
        "all_mode_bound_sources_expected_nonexecutable",
        "formal_validator_expected_nonexecutable",
        "review_validator_expected_nonexecutable",
        "v1_false_failure_contrast_proven",
        "chemical_warhead_role_region_distinction_preserved",
        "direct_exact5_applicability_preserved",
        "include_future_candidate_preserved",
        "historical_prior_census_preserved",
        "current_census_unchanged",
        "covapie_state_unchanged",
        "historical_validators_unchanged",
        "ready_for_v2_b2_6",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    for field in (
        "f24_v1_source_gate_active",
        "f24_v1_verify_binding_active",
        "f24_v1_verify_bindings_active",
        "f24_v1_loader_active",
        "f24_v1_subprocess_validator_active",
        "f24_v1_materialization_active",
        "ozj_v1_source_gate_active",
        "yun_v1_source_gate_active",
        "exact_posix_semantic_mode_active",
        "ready_for_training",
    ):
        if result[field] is not False:
            raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED:" + field)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v2(parser.parse_args().repo_root)
    print("PASS")
    print("lifecycle=" + str(result["lifecycle"]))
    for key in (
        "f24_v1_bytes_preserved",
        "f24_v1_artifacts_preserved",
        "b1_bound_source_helper_used",
        "ozj_v2_successor_bound",
        "ozj_v2_projection_exercised",
        "yun_v2_successor_bound",
        "yun_v2_projection_exercised",
        "exact_posix_semantic_mode_active",
        "historical_mode_bound_source_count",
        "all_mode_bound_sources_expected_nonexecutable",
        "formal_validator_expected_nonexecutable",
        "review_validator_expected_nonexecutable",
        "chemical_warhead_role_region_distinction_preserved",
        "direct_exact5_applicability_preserved",
        "include_future_candidate_preserved",
        "historical_prior_census_preserved",
        "current_census_unchanged",
        "ready_for_v2_b2_6",
        "ready_for_training",
    ):
        value = result[key]
        print(key + "=" + (str(value).lower() if isinstance(value, bool) else str(value)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
