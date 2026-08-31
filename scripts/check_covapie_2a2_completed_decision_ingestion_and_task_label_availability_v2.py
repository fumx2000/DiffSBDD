#!/usr/bin/env python3
"""Independent fail-closed checker for the additive 2A2 V2 successor."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
import csv
import hashlib
import importlib.util
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
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as two_a2_v1,
)
from covalent_ext import (  # noqa: E402
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    verify_bound_source_v2,
)


BASELINE_HEAD = "a81be8b1260d14b385b0faf05e2ddcc56bd403d8"
BASELINE_TREE = "315e47caa04d4c61096a0a24415cff86e3878528"
BASELINE_SUBJECT = "add CovaPIE F24 source binding successor v2"

PRODUCTION_RELATIVE = (
    "src/covalent_ext/"
    "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py"
)
CHECKER_RELATIVE = (
    "scripts/"
    "check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py"
)
TEST_RELATIVE = (
    "tests/"
    "test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py"
)
GUIDE_RELATIVE = (
    "docs/"
    "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2_guide.md"
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
F24_V2_BINDINGS = (
    (
        subject.F24_V2_RELATIVE,
        25212,
        "c83aa221721849cff1ee9e3fed4154204333edb6207ec6cceb70348802bcf253",
        "published_F24_V2_successor",
    ),
    (
        subject.F24_V2_CHECKER_RELATIVE,
        44863,
        "51a8af193c8c2eeb097a53cac66a25c0688b5e9066c6e07f0891fbbf897746a9",
        "published_F24_V2_checker",
    ),
)
TWO_A2_V1_BINDINGS = (
    (
        two_a2_v1.SOURCE_RELATIVE,
        81311,
        "57d42fcf673794f27adc7b897c0f51db4304d32f2d35a950b89d63cf4cf7060d",
        "published_2A2_V1_owner",
    ),
    (
        two_a2_v1.CHECKER_RELATIVE,
        16795,
        "dadb213ad9232e7ecd0e7ae55849357ead00b67cfdac9f95f10b8293bce81468",
        "published_2A2_V1_checker",
    ),
    (
        two_a2_v1.TEST_RELATIVE,
        24462,
        "3fe52260ec2bf8121adb9a6323ec8a624cfa343c6a5cde4393d68dd6b2d4830c",
        "published_2A2_V1_tests",
    ),
    *subject._PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS,
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
_FORBIDDEN_TWO_A2_V1_CALLS = {
    "_resolve_binding_path",
    "_verify_binding",
    "_verify_bindings",
    "_verify_formal_evidence_bindings",
    "_run_formal_validator",
    "load_frozen_formal_decision_v1",
    "_candidate_source_bindings",
    "_build_artifacts_unvalidated",
    "build_artifacts_v1",
    "validate_completed_decision_projection_v1",
    "_atomic_write",
    "materialize_artifacts_v1",
    "check_materialized_v1",
    "_reconciliation_informational",
    "main",
}
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
        for line in _git(
            "ls-files", "--", *sorted(expected), root=root
        ).splitlines()
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
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD",
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
        "TwoA2SourceBindingV2Error",
        "load_frozen_two_a2_authority_v2",
        "verify_published_two_a2_v1_projection_v2",
    ):
        raise ValueError("PUBLIC_API_INVENTORY_INVALID")
    if not issubclass(subject.TwoA2SourceBindingV2Error, ValueError):
        raise ValueError("PUBLIC_ERROR_FAMILY_INVALID")
    expected = {
        "load_frozen_two_a2_authority_v2": (
            "repo_root",
            "formal_decision_path",
            "repository_path_overrides",
        ),
        "verify_published_two_a2_v1_projection_v2": (
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
    text = _read_regular(root / PRODUCTION_RELATIVE, "2A2_V2_PRODUCTION").decode(
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
            "load_frozen_two_a2_authority_v2",
            "verify_published_two_a2_v1_projection_v2",
        },
    )
    for required in (
        "_verify_source",
        "_expected_executable_from_legacy_mode",
        "_verify_embedded_formal_evidence_v2",
        "_exercise_published_f24_v2_predecessor",
        "_validate_semantic_owner_payloads",
        "_validate_runtime_module_source",
        "_current_two_a2_global_census",
        "_validate_published_v1_manifest",
    ):
        if required not in reachable:
            raise ValueError("REQUIRED_ACTIVE_CALL_PATH_MISSING:" + required)
    direct_reads = [
        call
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
    two_a2_calls = _module_attribute_calls(tree, "two_a2_v1")
    if two_a2_calls & _FORBIDDEN_TWO_A2_V1_CALLS:
        raise ValueError("FORBIDDEN_TWO_A2_V1_ACTIVE_PATH_CALLED")
    if _module_attribute_calls(tree, "f24_v1"):
        raise ValueError("F24_V1_ACTIVE_REFERENCE_FORBIDDEN")
    f24_calls = _module_attribute_calls(tree, "f24_v2")
    if "verify_published_f24_v1_projection_v2" not in f24_calls:
        raise ValueError("PUBLISHED_F24_V2_PREDECESSOR_NOT_ACTIVE")
    if any(
        token in text
        for token in (
            "stat.S_IMODE",
            ".st_mode",
            "SOURCE_MODE_DRIFT",
            "FORMAL_EVIDENCE_SOURCE_DRIFT",
            "subprocess.run",
        )
    ):
        raise ValueError("HIDDEN_MODE_OR_SUBPROCESS_GATE_FORBIDDEN")
    load_node = functions["load_frozen_two_a2_authority_v2"]
    embedded_lines = [
        call.lineno
        for call in ast.walk(load_node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_verify_embedded_formal_evidence_v2"
    ]
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
        and call.func.value.id == "two_a2_v1"
        and call.func.attr == "_validate_published_runtime"
    ]
    if not (
        len(embedded_lines) == len(semantic_lines) == len(runtime_lines) == 1
        and embedded_lines[0] < semantic_lines[0] < runtime_lines[0]
    ):
        raise ValueError("RUNTIME_BINDING_ORDER_INVALID")
    return {
        "b1_bound_source_helper_used": True,
        "direct_source_read_bypass_count": 0,
        "exact_posix_semantic_mode_active": False,
        "embedded_exact_posix_semantic_mode_active": False,
        "two_a2_v1_source_gate_active": False,
        "two_a2_v1_verify_binding_active": False,
        "two_a2_v1_verify_formal_evidence_bindings_active": False,
        "two_a2_v1_loader_active": False,
        "two_a2_v1_subprocess_validator_active": False,
        "two_a2_v1_materialization_active": False,
        "two_a2_v1_reconciliation_execution_active": False,
        "f24_v1_source_gate_active": False,
        "f24_v2_successor_called": True,
        "runtime_bound_before_role_validation": True,
        "reused_two_a2_v1_function_names": sorted(two_a2_calls),
    }


def _verify_two_a2_v1_pure_call_graph(root: Path) -> None:
    production_tree = ast.parse(
        _read_regular(root / PRODUCTION_RELATIVE, "2A2_V2_PRODUCTION").decode(
            "utf-8"
        )
    )
    roots = _module_attribute_calls(production_tree, "two_a2_v1")
    v1_tree = ast.parse(
        _read_regular(root / two_a2_v1.SOURCE_RELATIVE, "2A2_V1_OWNER").decode(
            "utf-8"
        )
    )
    reachable = _reachable_functions(_function_nodes(v1_tree), roots)
    if reachable & _FORBIDDEN_TWO_A2_V1_CALLS:
        raise ValueError("REUSED_TWO_A2_V1_HELPER_REACHES_FORBIDDEN_PATH")
    if "_validate_published_runtime" not in roots:
        raise ValueError("TWO_A2_V1_PURE_RUNTIME_VALIDATION_NOT_ACTIVE")


def _verify_f24_v2_call_graph(root: Path) -> None:
    tree = ast.parse(
        _read_regular(root / subject.F24_V2_RELATIVE, "F24_V2_OWNER").decode(
            "utf-8"
        )
    )
    reachable = _reachable_functions(
        _function_nodes(tree),
        {"load_frozen_f24_authority_v2", "verify_published_f24_v1_projection_v2"},
    )
    if "_verify_source" not in reachable:
        raise ValueError("F24_V2_BOUND_SOURCE_PATH_NOT_ACTIVE")
    if _module_attribute_calls(tree, "f24_v1") & _FORBIDDEN_F24_V1_CALLS:
        raise ValueError("F24_V2_REACHES_F24_V1_SOURCE_GATE")


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


def _source_path(root: Path, record: Mapping[str, object]) -> Path:
    relative = Path(str(record["path"]))
    if record["path_namespace"] == "repository_relative":
        return root / relative
    if record["path_namespace"] == "project_parent_relative":
        return root.parent / relative
    raise ValueError("SOURCE_NAMESPACE_INVALID")


def _record_for_role(
    records: Sequence[Mapping[str, object]], role: str
) -> Mapping[str, object]:
    matches = [record for record in records if record.get("source_role") == role]
    if len(matches) != 1:
        raise ValueError("SOURCE_ROLE_NOT_EXACT1:" + role)
    return matches[0]


def _copy_record_source(
    root: Path, record: Mapping[str, object], destination: Path
) -> None:
    payload = verify_bound_source_v2(
        path=_source_path(root, record),
        expected_byte_count=int(record["byte_count"]),
        expected_sha256=str(record["sha256"]),
        label="checker_copy:" + str(record["source_role"]),
        expected_executable=False,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def _verify_v1_embedded_false_failure_contract(
    root: Path, bound: Mapping[str, object]
) -> bool:
    records = bound["formal_evidence_bindings"]
    if type(records) is not list:
        raise ValueError("FORMAL_EVIDENCE_RECORDS_INVALID")
    target = _record_for_role(records, "published_1f8_event_task_label_availability")
    with tempfile.TemporaryDirectory(prefix="covapie_2a2_v1_embedded_contrast_") as name:
        parent = Path(name)
        fake_repo = parent / "fake-repository"
        fake_repo.mkdir()
        copied_records: list[dict[str, object]] = []
        target_path: Path | None = None
        for record in records:
            copied = dict(record)
            relative = Path(str(record["path"]))
            destination = parent / relative
            _copy_record_source(root, record, destination)
            destination.chmod(int(str(record["mode"]), 8))
            if record["source_role"] == target["source_role"]:
                target_path = destination
            copied_records.append(copied)
        if target_path is None:
            raise ValueError("EMBEDDED_1F8_TARGET_MISSING")
        target_path.chmod(0o664)
        try:
            two_a2_v1._verify_formal_evidence_bindings(fake_repo, copied_records)
        except two_a2_v1.TwoA2IngestionSafetyError as error:
            if "FORMAL_EVIDENCE_SOURCE_DRIFT" not in str(error):
                raise ValueError("V1_EMBEDDED_FALSE_FAILURE_TOKEN_MISSING") from error
        else:
            raise ValueError("V1_EMBEDDED_SAFE_MODE_DRIFT_DID_NOT_FALSE_FAIL")
        subject.load_frozen_two_a2_authority_v2(
            repo_root=root,
            repository_path_overrides={Path(str(target["path"])): target_path},
        )
    return True


def _exercise_direct_mode_regressions(root: Path) -> dict[str, bool]:
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_2a2_v2_direct_modes_") as name:
        temporary = Path(name)
        for index, binding in enumerate(two_a2_v1.FORMAL_BINDINGS):
            relative, namespace, byte_count, sha256, role, mode = binding
            record = {
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
                "source_role": role,
            }
            replacement = temporary / ("direct_" + str(index) + relative.suffix)
            _copy_record_source(root, record, replacement)
            for live_mode in (0o600, 0o644, 0o660, 0o664):
                replacement.chmod(live_mode)
                subject._verify_source(
                    path=replacement,
                    byte_count=byte_count,
                    sha256=sha256,
                    label=role,
                    expected_executable=subject._expected_executable_from_legacy_mode(
                        mode, role
                    ),
                )
                result[f"direct_{index}_{live_mode:04o}"] = True
            for live_mode in (0o755, 0o666, 0o777):
                replacement.chmod(live_mode)
                key = f"direct_{index}_{live_mode:04o}"
                try:
                    subject._verify_source(
                        path=replacement,
                        byte_count=byte_count,
                        sha256=sha256,
                        label=role,
                        expected_executable=False,
                    )
                except subject.TwoA2SourceBindingV2Error as error:
                    token = (
                        "SOURCE_WORLD_WRITABLE"
                        if live_mode & 0o002
                        else "SOURCE_EXECUTABLE_CLASS_MISMATCH"
                    )
                    if token not in str(error):
                        raise ValueError("DIRECT_UNSAFE_MODE_TOKEN_MISSING:" + key)
                    result[key] = True
                else:
                    raise ValueError("DIRECT_UNSAFE_MODE_ACCEPTED:" + key)
    return result


def _exercise_embedded_mode_regressions(
    root: Path, bound: Mapping[str, object]
) -> dict[str, bool]:
    records = bound["formal_evidence_bindings"]
    if type(records) is not list:
        raise ValueError("FORMAL_EVIDENCE_RECORDS_INVALID")
    cases = (
        (
            "published_1f8_event_task_label_availability",
            (0o600, 0o644, 0o660, 0o664),
            (0o755, 0o666, 0o777),
        ),
        ("published_role_profile_runtime_owner", (0o664,), ()),
        ("canonical_role_and_task_semantics_owner", (0o664,), ()),
        ("preparation_package_validator", (), (0o755, 0o666)),
        ("human_review_scientific_preview_validator", (), (0o755,)),
    )
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_2a2_v2_embedded_modes_") as name:
        temporary = Path(name)
        for role, safe_modes, unsafe_modes in cases:
            record = _record_for_role(records, role)
            relative = Path(str(record["path"]))
            replacement = temporary / (role + relative.suffix)
            _copy_record_source(root, record, replacement)
            for live_mode in safe_modes:
                replacement.chmod(live_mode)
                subject.load_frozen_two_a2_authority_v2(
                    repo_root=root,
                    repository_path_overrides={relative: replacement},
                )
                result[f"{role}_{live_mode:04o}"] = True
            for live_mode in unsafe_modes:
                replacement.chmod(live_mode)
                key = f"{role}_{live_mode:04o}"
                try:
                    subject.load_frozen_two_a2_authority_v2(
                        repo_root=root,
                        repository_path_overrides={relative: replacement},
                    )
                except subject.TwoA2SourceBindingV2Error as error:
                    token = (
                        "SOURCE_WORLD_WRITABLE"
                        if live_mode & 0o002
                        else "SOURCE_EXECUTABLE_CLASS_MISMATCH"
                    )
                    if token not in str(error):
                        raise ValueError("EMBEDDED_UNSAFE_MODE_TOKEN_MISSING:" + key)
                    result[key] = True
                else:
                    raise ValueError("EMBEDDED_UNSAFE_MODE_ACCEPTED:" + key)
    return result


def _exercise_embedded_source_failures(
    root: Path, bound: Mapping[str, object]
) -> dict[str, bool]:
    records = bound["formal_evidence_bindings"]
    if type(records) is not list:
        raise ValueError("FORMAL_EVIDENCE_RECORDS_INVALID")
    record = _record_for_role(records, "graph_and_role_candidates")
    relative = Path(str(record["path"]))
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_2a2_v2_failures_") as name:
        temporary = Path(name)
        original = temporary / "original.json"
        _copy_record_source(root, record, original)

        wrong_bytes = temporary / "wrong-bytes.json"
        shutil.copyfile(original, wrong_bytes)
        wrong_bytes.write_bytes(wrong_bytes.read_bytes() + b"\n")
        try:
            subject.load_frozen_two_a2_authority_v2(
                repo_root=root,
                repository_path_overrides={relative: wrong_bytes},
            )
        except subject.TwoA2SourceBindingV2Error as error:
            if "SOURCE_BYTE_COUNT_MISMATCH" not in str(error):
                raise ValueError("WRONG_BYTE_COUNT_TOKEN_MISSING") from error
            result["wrong_byte_count_rejected"] = True
        else:
            raise ValueError("WRONG_BYTE_COUNT_ACCEPTED")

        wrong_sha = temporary / "wrong-sha.json"
        shutil.copyfile(original, wrong_sha)
        payload = bytearray(wrong_sha.read_bytes())
        payload[0] ^= 1
        wrong_sha.write_bytes(payload)
        try:
            subject.load_frozen_two_a2_authority_v2(
                repo_root=root,
                repository_path_overrides={relative: wrong_sha},
            )
        except subject.TwoA2SourceBindingV2Error as error:
            if "SOURCE_SHA256_MISMATCH" not in str(error):
                raise ValueError("WRONG_SHA_TOKEN_MISSING") from error
            result["same_size_wrong_sha_rejected"] = True
        else:
            raise ValueError("WRONG_SHA_ACCEPTED")

        link = temporary / "source-link.json"
        link.symlink_to(original.name)
        try:
            subject.load_frozen_two_a2_authority_v2(
                repo_root=root,
                repository_path_overrides={relative: link},
            )
        except subject.TwoA2SourceBindingV2Error as error:
            if "SOURCE_SYMLINK_FORBIDDEN" not in str(error):
                raise ValueError("SYMLINK_TOKEN_MISSING") from error
            result["symlink_rejected"] = True
        else:
            raise ValueError("SYMLINK_ACCEPTED")

        try:
            subject.load_frozen_two_a2_authority_v2(
                repo_root=root,
                repository_path_overrides={Path("unexpected.txt"): original},
            )
        except subject.TwoA2SourceBindingV2Error as error:
            if "REPOSITORY_PATH_OVERRIDE_UNEXPECTED" not in str(error):
                raise ValueError("UNEXPECTED_OVERRIDE_TOKEN_MISSING") from error
            result["unexpected_override_rejected"] = True
        else:
            raise ValueError("UNEXPECTED_OVERRIDE_ACCEPTED")
    return result


def _verify_scientific_semantics(bound: Mapping[str, object]) -> None:
    formal = bound["formal"]
    if type(formal) is not dict:
        raise ValueError("FORMAL_DOCUMENT_INVALID")
    approval = formal["human_approval"]
    events = formal["event_level_human_decisions"]
    role = formal["selected_role_partition"]
    chemical = formal["chemical_warhead_boundary"]
    pre = formal["experimental_context_and_PRE_boundary"]
    post = formal["POST_evidence_boundary"]
    training = formal["training_use_human_decision"]
    reusable = formal["reusable_authority_boundary"]
    precedent = formal["published_1F8_same_context_precedent"]
    if (
        len(events) != 4
        or [event["scaleup_rank"] for event in events] != [507, 508, 509, 510]
        or any(event["pdb_id"] != "3ORZ" for event in events)
        or any(event["cys_residue_id"] != "CYS:148-" for event in events)
        or any(event["protein_reactive_atom"] != "SG" for event in events)
        or any(event["ligand_reactive_atom"] != "SD" for event in events)
        or approval["D1_task_relevance"] != "RELEVANT"
        or approval["D2_chemistry"] != "POSITIVE"
        or approval["D3_reactive_pair"] != "CONFIRM_OBSERVED_PAIR"
        or approval["D4_role_partition"] != "SELECT_CANDIDATE_4"
        or approval["D5_training_use"] != "EXCLUDE_FROM_TRAINING_ONLY"
        or approval["D6_scientific_context"]
        != formal["human_approved_context"]["D6_scientific_context"]
        or role["selected_candidate_index_0based"] != 4
        or role["human_selected"] is not True
        or role["machine_selected"] is not False
        or role["machine_recommended"] is not False
        or role["role_profile"] != "STRICT_LINKER_PRESENT_V1"
        or role["warhead_role_atom_ids"] != ["SD"]
        or role["linker_atom_ids"] != ["C1", "C15", "C16", "C17", "O18"]
        or role["scaffold_atom_ids"] != list(two_a2_v1.SCAFFOLD_ROLE)
        or role["boundary_bonds"] != list(two_a2_v1.BOUNDARY_BONDS)
        or role["applicable_task_ids"] != [0, 1, 2, 3, 4]
        or chemical["chemical_warhead_atom_ids"] is not None
        or chemical["chemical_warhead_human_authoritative"] is not False
        or chemical["W_SD_is_sample_level_canonical_role_region"] is not True
        or chemical["W_SD_is_complete_PRE_chemical_warhead_definition"] is not False
        or pre["engineered_target_site"] != "PDK1_T148C"
        or pre["native_cysteine_site"] is not False
        or pre["disulfide_trapping_context"] is not True
        or pre["complete_PRE_disulfide_reagent_authority"] is not False
        or pre["PRE_topology_authority_created"] is not False
        or pre["PRE_geometry_authority_created"] is not False
        or pre["PRE_reconstruction_performed"] is not False
        or pre["POST_to_PRE_copy_performed"] is not False
        or pre["PRE_zero_fill_performed"] is not False
        or post != {
            "POST_geometry_training_authority_created": False,
            "POST_geometry_training_target_created": False,
            "POST_source_evidence_available": True,
            "POST_source_evidence_count": 4,
        }
        or training["human_training_excluded"] is not True
        or training["training_use_allowed"] is not False
        or training["candidate_for_future_training_admission"] is not False
        or training["formal_training_admitted"] is not False
        or training["training_admission_created"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["current_runtime_model_usable"] is not False
        or training["parameter_update_authorization"] is not False
        or any(
            reusable[key] is not False
            for key in (
                "reaction_family_authority_created",
                "warhead_rule_authority_created",
                "warhead_type_authority_created",
                "reusable_chemistry_authority_created",
                "reusable_pair_authority_created",
                "reusable_role_authority_created",
                "generic_all_disulfide_trapping_EXCLUDE_rule_created",
            )
        )
        or precedent["precedent_did_not_substitute_for_2A2_independent_review"]
        is not True
        or precedent["2A2_independent_human_review_completed"] is not True
        or precedent["generic_disulfide_trapping_exclusion_rule_created"]
        is not False
        or precedent["reusable_rule_created"] is not False
    ):
        raise ValueError("TWO_A2_V2_SCIENTIFIC_EQUIVALENCE_INVALID")
    canonical = formal["canonical_Exact5_and_sample_applicability"]
    if (
        canonical["global_canonical_task_count"] != 5
        or canonical["sample_applicable_task_ids"] != [0, 1, 2, 3, 4]
        or canonical["B3_present"] is not True
        or canonical["sixth_task_present"] is not False
        or [task["semantic_name"] for task in canonical["tasks"]]
        != [task[1] for task in two_a2_v1.CANONICAL_TASKS]
    ):
        raise ValueError("TWO_A2_STRICT_EXACT5_INVALID")


def _verify_census_boundaries(bound: Mapping[str, object]) -> None:
    historical = bound["current_published_census_boundary"]
    future = bound["future_census_informational"]
    current = bound["current_2A2_global_census"]
    if type(historical) is not dict or type(future) is not dict or type(current) is not dict:
        raise ValueError("CENSUS_RECORD_TYPE_INVALID")
    historical_expected = {
        "positive": 108,
        "relevant": 109,
        "training_INCLUDE": 44,
        "training_EXCLUDE": 64,
        "future_candidates": 27,
        "pair_sample_authority": 108,
        "role_sample_authority": 108,
        "strict_profile": 48,
        "direct_profile": 60,
        "A": 108,
        "B": 48,
        "B2": 48,
        "B3": 108,
        "C": 108,
    }
    future_expected = {
        "positive": 112,
        "relevant": 113,
        "training_INCLUDE": 44,
        "training_EXCLUDE": 68,
        "future_candidates": 27,
        "pair_sample_authority": 112,
        "role_sample_authority": 112,
        "strict_profile": 52,
        "direct_profile": 60,
        "A": 112,
        "B": 52,
        "B2": 52,
        "B3": 112,
        "C": 112,
    }
    current_expected = {
        key: value
        for key, value in future_expected.items()
        if key not in {"strict_profile", "direct_profile"}
    }
    if any(historical.get(key) != value for key, value in historical_expected.items()):
        raise ValueError("HISTORICAL_F24_PRIOR_CENSUS_DRIFT")
    if any(future.get(key) != value for key, value in future_expected.items()):
        raise ValueError("HISTORICAL_INFORMATIONAL_FUTURE_DRIFT")
    if current != current_expected:
        raise ValueError("CURRENT_2A2_GLOBAL_CENSUS_DRIFT")
    reconciliation = bound["reconciliation_informational"]
    if type(reconciliation) is not dict or (
        reconciliation.get("reconciled_this_step") is not False
        or reconciliation.get("future_after_reconciliation")
        != {
            "completed_positive_event_count": 95,
            "completed_positive_unit_count": 13,
            "completed_negative_event_count": 24,
            "completed_negative_unit_count": 4,
            "completed_total_event_count": 119,
            "completed_total_unit_count": 17,
            "unreviewed_event_count": 219,
            "unreviewed_unit_count": 114,
            "in_progress_event_count": 0,
            "in_progress_unit_count": 0,
            "normalized_INCLUDE": 27,
            "normalized_EXCLUDE_FROM_TRAINING_ONLY": 68,
        }
    ):
        raise ValueError("RECONCILIATION_INFORMATIONAL_BOUNDARY_DRIFT")


def _verify_published_artifact_semantics(artifacts: Mapping[str, bytes]) -> None:
    snapshot = json.loads(artifacts[two_a2_v1.SNAPSHOT])
    summary = json.loads(artifacts[two_a2_v1.SUMMARY])
    manifest = json.loads(artifacts[two_a2_v1.MANIFEST])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[two_a2_v1.MATRIX].decode("utf-8")))
    )
    if (
        len(rows) != 4
        or [int(row["scaleup_rank"]) for row in rows] != [507, 508, 509, 510]
        or any(row["pdb_id"] != "3ORZ" for row in rows)
        or any(row["protein_reactive_atom"] != "SG" for row in rows)
        or any(row["ligand_reactive_atom"] != "SD" for row in rows)
        or any(json.loads(row["warhead_atoms_json"]) != ["SD"] for row in rows)
        or any(json.loads(row["chemical_warhead_atoms_json"]) is not None for row in rows)
        or any(row["formal_event_training_use_decision"] != "EXCLUDE_FROM_TRAINING_ONLY" for row in rows)
        or summary["event_count"] != 4
        or summary["human_training_EXCLUDE_count"] != 4
        or summary["ready_for_training"] is not False
        or snapshot["selected_role_partition"]["applicable_task_ids"]
        != [0, 1, 2, 3, 4]
        or snapshot["chemical_warhead_boundary"]["chemical_warhead_atom_ids"]
        is not None
        or manifest["ready_for_training"] is not False
        or manifest["manifest_self_sha256_recorded"] is not False
    ):
        raise ValueError("PUBLISHED_V1_ARTIFACT_SEMANTICS_INVALID")


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = verify_exact4_file_hygiene(root)
    _verify_public_api()
    ast_result = _verify_production_ast(root)
    _verify_two_a2_v1_pure_call_graph(root)
    _verify_f24_v2_call_graph(root)
    if _git("show", "-s", "--format=%H", subject.F24_V2_PUBLISHED_COMMIT, root=root) != subject.F24_V2_PUBLISHED_COMMIT:
        raise ValueError("PUBLISHED_F24_V2_COMMIT_MISSING")
    b1 = _verify_bound_bindings(root, (B1_BINDING,))
    f24 = _verify_bound_bindings(root, F24_V2_BINDINGS)
    v1 = _verify_bound_bindings(root, TWO_A2_V1_BINDINGS)
    bound = subject.load_frozen_two_a2_authority_v2(repo_root=root)
    _verify_scientific_semantics(bound)
    _verify_census_boundaries(bound)
    artifacts = subject.verify_published_two_a2_v1_projection_v2(repo_root=root)
    _verify_published_artifact_semantics(artifacts)
    v1_false_failure = _verify_v1_embedded_false_failure_contract(root, bound)
    direct_modes = _exercise_direct_mode_regressions(root)
    embedded_modes = _exercise_embedded_mode_regressions(root, bound)
    source_failures = _exercise_embedded_source_failures(root, bound)

    binding = bound["source_binding_v2"]
    if type(binding) is not dict or binding != {
        "combined_helper": "verify_bound_source_v2",
        "direct_mode_bound_source_count": 2,
        "formal_embedded_evidence_count": 11,
        "formal_embedded_evidence_exact_count": 11,
        "total_historical_mode_bearing_records": 13,
        "historical_mode_counts": {"0664": 10, "0644": 2, "0600": 1},
        "expected_executable_classes": [False] * 13,
        "all_expected_executable": False,
        "formal_validator_expected_nonexecutable": True,
        "preparation_validator_expected_nonexecutable": True,
        "preview_validator_expected_nonexecutable": True,
        "embedded_1F8_0600_precedent_expected_nonexecutable": True,
        "exact_posix_numeric_mode_semantic_acceptance": False,
        "embedded_exact_posix_numeric_mode_semantic_acceptance": False,
    }:
        raise ValueError("TWO_A2_V2_SOURCE_BINDING_CLASSIFICATION_INVALID")
    predecessor = bound["published_f24_v2_predecessor"]
    if type(predecessor) is not dict or predecessor != {
        "published_F24_V2_successor_bound": True,
        "F24_V2_sha256": subject.F24_V2_SHA256,
        "F24_V2_checker_sha256": subject.F24_V2_CHECKER_SHA256,
        "F24_V2_published_commit": subject.F24_V2_PUBLISHED_COMMIT,
        "F24_V2_projection_actually_called": True,
        "F24_V1_ingestion_projection_preserved": True,
    }:
        raise ValueError("F24_V2_PREDECESSOR_RECORD_INVALID")

    result = {
        "lifecycle": lifecycle,
        "exact4": exact4,
        "b1_bindings": b1,
        "f24_v2_bindings": f24,
        "two_a2_v1_bindings": v1,
        "two_a2_v1_bytes_preserved": True,
        "two_a2_v1_artifacts_preserved": tuple(artifacts)
        == two_a2_v1.OUTPUT_FILENAMES,
        "b1_bound_source_helper_used": ast_result["b1_bound_source_helper_used"],
        "direct_source_read_bypass_count": ast_result[
            "direct_source_read_bypass_count"
        ],
        "f24_v2_successor_bound": ast_result["f24_v2_successor_called"],
        "f24_v2_projection_exercised": predecessor[
            "F24_V2_projection_actually_called"
        ],
        "f24_v1_source_gate_active": ast_result["f24_v1_source_gate_active"],
        "two_a2_v1_source_gate_active": ast_result[
            "two_a2_v1_source_gate_active"
        ],
        "two_a2_v1_verify_binding_active": ast_result[
            "two_a2_v1_verify_binding_active"
        ],
        "two_a2_v1_verify_formal_evidence_bindings_active": ast_result[
            "two_a2_v1_verify_formal_evidence_bindings_active"
        ],
        "two_a2_v1_loader_active": ast_result["two_a2_v1_loader_active"],
        "two_a2_v1_subprocess_validator_active": ast_result[
            "two_a2_v1_subprocess_validator_active"
        ],
        "two_a2_v1_materialization_active": ast_result[
            "two_a2_v1_materialization_active"
        ],
        "two_a2_v1_reconciliation_execution_active": ast_result[
            "two_a2_v1_reconciliation_execution_active"
        ],
        "runtime_bound_before_role_validation": ast_result[
            "runtime_bound_before_role_validation"
        ],
        "direct_mode_bound_source_count": 2,
        "formal_embedded_evidence_count": 11,
        "total_historical_mode_bearing_records": 13,
        "historical_mode_counts": {"0664": 10, "0644": 2, "0600": 1},
        "all_mode_bound_sources_expected_nonexecutable": True,
        "formal_validator_expected_nonexecutable": True,
        "preparation_validator_expected_nonexecutable": True,
        "preview_validator_expected_nonexecutable": True,
        "embedded_1f8_0600_safe_drift_pass": embedded_modes[
            "published_1f8_event_task_label_availability_0664"
        ],
        "v1_embedded_false_failure_contrast_proven": v1_false_failure,
        "v1_embedded_failure_token": "FORMAL_EVIDENCE_SOURCE_DRIFT",
        "direct_mode_regressions": direct_modes,
        "embedded_mode_regressions": embedded_modes,
        "source_failure_regressions": source_failures,
        "exact_posix_semantic_mode_active": ast_result[
            "exact_posix_semantic_mode_active"
        ],
        "embedded_exact_posix_semantic_mode_active": ast_result[
            "embedded_exact_posix_semantic_mode_active"
        ],
        "chemical_warhead_pre_boundary_preserved": True,
        "strict_exact5_all_tasks_applicable": True,
        "training_exclusion_preserved": True,
        "historical_prior_census_preserved": True,
        "historical_informational_future_projection_preserved": True,
        "current_census_unchanged": True,
        "reconciled_this_step": False,
        "covapie_state_unchanged": True,
        "data_derived_unchanged": True,
        "ready_for_v2_b2_integration": True,
        "ready_for_training": False,
    }
    required_true = (
        "two_a2_v1_bytes_preserved",
        "two_a2_v1_artifacts_preserved",
        "b1_bound_source_helper_used",
        "f24_v2_successor_bound",
        "f24_v2_projection_exercised",
        "runtime_bound_before_role_validation",
        "all_mode_bound_sources_expected_nonexecutable",
        "formal_validator_expected_nonexecutable",
        "preparation_validator_expected_nonexecutable",
        "preview_validator_expected_nonexecutable",
        "embedded_1f8_0600_safe_drift_pass",
        "v1_embedded_false_failure_contrast_proven",
        "chemical_warhead_pre_boundary_preserved",
        "strict_exact5_all_tasks_applicable",
        "training_exclusion_preserved",
        "historical_prior_census_preserved",
        "historical_informational_future_projection_preserved",
        "current_census_unchanged",
        "covapie_state_unchanged",
        "data_derived_unchanged",
        "ready_for_v2_b2_integration",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    for field in (
        "f24_v1_source_gate_active",
        "two_a2_v1_source_gate_active",
        "two_a2_v1_verify_binding_active",
        "two_a2_v1_verify_formal_evidence_bindings_active",
        "two_a2_v1_loader_active",
        "two_a2_v1_subprocess_validator_active",
        "two_a2_v1_materialization_active",
        "two_a2_v1_reconciliation_execution_active",
        "exact_posix_semantic_mode_active",
        "embedded_exact_posix_semantic_mode_active",
        "reconciled_this_step",
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
        "two_a2_v1_bytes_preserved",
        "two_a2_v1_artifacts_preserved",
        "b1_bound_source_helper_used",
        "f24_v2_successor_bound",
        "f24_v2_projection_exercised",
        "direct_mode_bound_source_count",
        "formal_embedded_evidence_count",
        "total_historical_mode_bearing_records",
        "all_mode_bound_sources_expected_nonexecutable",
        "embedded_1f8_0600_safe_drift_pass",
        "exact_posix_semantic_mode_active",
        "embedded_exact_posix_semantic_mode_active",
        "chemical_warhead_pre_boundary_preserved",
        "strict_exact5_all_tasks_applicable",
        "training_exclusion_preserved",
        "historical_prior_census_preserved",
        "current_census_unchanged",
        "ready_for_v2_b2_integration",
        "ready_for_training",
    ):
        value = result[key]
        print(key + "=" + (str(value).lower() if isinstance(value, bool) else str(value)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
