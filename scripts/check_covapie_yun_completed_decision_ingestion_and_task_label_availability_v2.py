#!/usr/bin/env python3
"""Independent fail-closed checker for the additive YUN V2 successor."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
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
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v1
    as yun_v1,
)
from covalent_ext import (  # noqa: E402
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    verify_bound_source_v2,
)


BASELINE_HEAD = "94a59fef2922b8a450fe06538111ca62a0b78190"
BASELINE_TREE = "dbd175a0a9f236011238fa4542133fba9837b1e7"
BASELINE_SUBJECT = "add CovaPIE source binding policy v2"

PRODUCTION_RELATIVE = (
    "src/covalent_ext/"
    "covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
)
CHECKER_RELATIVE = (
    "scripts/"
    "check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
)
TEST_RELATIVE = (
    "tests/"
    "test_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
)
GUIDE_RELATIVE = (
    "docs/"
    "covapie_yun_completed_decision_ingestion_and_task_label_availability_v2_guide.md"
)
EXACT4_PATHS = (
    PRODUCTION_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    GUIDE_RELATIVE,
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
_FORBIDDEN_V1_CALLS = {
    "_verify_payload",
    "load_frozen_formal_decision_v1",
    "_semantic_owner_bindings",
    "_frozen_review_bindings",
    "_include_precedent_bindings",
    "_current_census_bindings",
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
    if len(payload) >= MAX_FILE_BYTES:
        raise ValueError("FILE_AT_OR_ABOVE_1MIB:" + label)
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
    baseline_identity = _git(
        "show", "-s", "--format=%T%n%s", BASELINE_HEAD, root=root
    ).splitlines()
    if baseline_identity != [BASELINE_TREE, BASELINE_SUBJECT]:
        raise ValueError("BASELINE_TREE_OR_SUBJECT_INVALID")
    exact = set(EXACT4_PATHS)
    tracked = {
        line
        for line in _git("ls-files", "--", *sorted(exact), root=root).splitlines()
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
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", root=root
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
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
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


def _verify_public_api() -> None:
    if subject.__all__ != (
        "YUNSourceBindingV2Error",
        "load_frozen_yun_authority_v2",
        "verify_published_yun_v1_projection_v2",
    ):
        raise ValueError("PUBLIC_API_INVENTORY_INVALID")
    if not issubclass(subject.YUNSourceBindingV2Error, ValueError):
        raise ValueError("PUBLIC_ERROR_FAMILY_INVALID")
    expected = {
        "load_frozen_yun_authority_v2": (
            "repo_root",
            "formal_decision_path",
            "repository_path_overrides",
        ),
        "verify_published_yun_v1_projection_v2": (
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
    if any(
        token in public_names
        for token in ("materialize", "registry", "resolver", "cache")
    ):
        raise ValueError("FORBIDDEN_PUBLIC_FRAMEWORK_OR_MUTATION_API")


def _verify_production_ast(root: Path) -> dict[str, object]:
    production = root / PRODUCTION_RELATIVE
    text = _read_regular(production, "YUN_V2_PRODUCTION").decode("utf-8")
    tree = ast.parse(text)
    functions = _function_nodes(tree)
    if "_verify_source" not in functions:
        raise ValueError("BOUND_SOURCE_WRAPPER_MISSING")
    bound_calls = [
        call
        for call in ast.walk(functions["_verify_source"])
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "verify_bound_source_v2"
    ]
    if len(bound_calls) != 1:
        raise ValueError("BOUND_SOURCE_HELPER_CALL_INVALID")
    public_reachable = _reachable_functions(
        functions,
        {
            "load_frozen_yun_authority_v2",
            "verify_published_yun_v1_projection_v2",
        },
    )
    if "_verify_source" not in public_reachable:
        raise ValueError("BOUND_SOURCE_WRAPPER_NOT_ACTIVE")
    forbidden_reads = []
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr in {"read_bytes", "read_text", "open"}:
            forbidden_reads.append(call.func.attr)
    if forbidden_reads:
        raise ValueError("DIRECT_SOURCE_READ_BYPASSES_B1")
    v1_calls = {
        call.func.attr
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "yun_v1"
    }
    if v1_calls & _FORBIDDEN_V1_CALLS:
        raise ValueError("FORBIDDEN_V1_ACTIVE_SOURCE_PATH_CALLED")
    exact_mode_literals = {"0600", "0644", "0664", "0755"}
    for comparison in (
        node for node in ast.walk(tree) if isinstance(node, ast.Compare)
    ):
        values = [comparison.left, *comparison.comparators]
        if any(
            isinstance(value, ast.Constant) and value.value in exact_mode_literals
            for value in values
        ):
            raise ValueError("EXACT_NUMERIC_MODE_COMPARISON_FORBIDDEN")
    forbidden_tokens = (
        "stat.S_IMODE",
        "st_mode",
        "0o7777",
        "BOUND_SOURCE_MODE_MISMATCH",
    )
    if any(token in text for token in forbidden_tokens):
        raise ValueError("HIDDEN_EXACT_MODE_GATE_FORBIDDEN")
    return {
        "v2_bound_source_helper_used": True,
        "exact_posix_semantic_mode_active": False,
        "v1_active_source_gate_called": False,
        "reused_v1_function_names": sorted(v1_calls),
    }


def _verify_v1_pure_call_graph(root: Path) -> None:
    production_tree = ast.parse(
        _read_regular(root / PRODUCTION_RELATIVE, "YUN_V2_PRODUCTION").decode(
            "utf-8"
        )
    )
    roots = {
        call.func.attr
        for call in ast.walk(production_tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "yun_v1"
    }
    v1_tree = ast.parse(
        _read_regular(root / yun_v1.SOURCE_RELATIVE, "YUN_V1_OWNER").decode(
            "utf-8"
        )
    )
    reachable = _reachable_functions(_function_nodes(v1_tree), roots)
    if reachable & _FORBIDDEN_V1_CALLS:
        raise ValueError("REUSED_V1_HELPER_REACHES_EXACT_MODE_GATE")


def _verify_v1_static_false_failure_contract(root: Path) -> bool:
    text = _read_regular(root / yun_v1.SOURCE_RELATIVE, "YUN_V1_OWNER").decode(
        "utf-8"
    )
    tree = ast.parse(text)
    function = _function_nodes(tree).get("_verify_payload")
    if function is None:
        raise ValueError("V1_VERIFY_PAYLOAD_MISSING")
    segment = ast.get_source_segment(text, function) or ""
    if not all(
        token in segment
        for token in (
            "expected_mode",
            "path.stat().st_mode",
            "0o7777",
            "BOUND_SOURCE_MODE_MISMATCH",
        )
    ):
        raise ValueError("V1_EXACT_MODE_FALSE_FAILURE_CONTRACT_NOT_PROVEN")
    return True


def _verify_frozen_v1_bytes(root: Path) -> dict[str, str]:
    bindings = (
        *subject._FROZEN_V1_CODE_BINDINGS,
        *subject._PUBLISHED_YUN_V1_OUTPUT_BINDINGS,
    )
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


def _verify_b1_dependency(root: Path) -> None:
    verify_bound_source_v2(
        path=root / subject.SOURCE_BINDING_POLICY_V2_RELATIVE,
        expected_byte_count=subject.SOURCE_BINDING_POLICY_V2_BYTE_COUNT,
        expected_sha256=subject.SOURCE_BINDING_POLICY_V2_SHA256,
        label="published_source_binding_policy_v2",
        expected_executable=False,
    )


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
    task_counts = {
        task["display_alias"]: task["structurally_applicable_authoritative_role_count"]
        for task in summary.get("canonical_exact5", {}).get("tasks", [])
    }
    observed = {
        "positive": summary.get("chemistry", {}).get("POSITIVE", {}).get("count"),
        "relevant": summary.get("task_relevance", {}).get("RELEVANT", {}).get("count"),
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
        "A": task_counts.get("A"),
        "B": task_counts.get("B"),
        "B2": task_counts.get("B2"),
        "B3": task_counts.get("B3"),
        "C": task_counts.get("C"),
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


def _copy_binding_source(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)


def _exercise_mode_regressions(root: Path) -> dict[str, bool]:
    nonexec = yun_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    executable = yun_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[-1]
    baseline = subject.load_frozen_yun_authority_v2(repo_root=root)
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_yun_v2_modes_") as name:
        temporary = Path(name)
        for binding, modes, pass_modes, label in (
            (
                nonexec,
                (0o644, 0o664, 0o600, 0o660, 0o666),
                {0o644, 0o664, 0o600, 0o660},
                "nonexec",
            ),
            (
                executable,
                (0o755, 0o775, 0o750, 0o700, 0o644, 0o777),
                {0o755, 0o775, 0o750, 0o700},
                "executable",
            ),
        ):
            relative = binding[0]
            replacement = temporary / (label + relative.suffix)
            _copy_binding_source(root.parent / relative, replacement)
            for mode in modes:
                replacement.chmod(mode)
                key = f"{label}_{mode:04o}"
                if mode in pass_modes:
                    observed = subject.load_frozen_yun_authority_v2(
                        repo_root=root,
                        repository_path_overrides={relative: replacement},
                    )
                    if observed != baseline:
                        raise ValueError("MODE_ONLY_AUTHORITY_RESULT_DRIFT:" + key)
                    result[key] = True
                else:
                    try:
                        subject.load_frozen_yun_authority_v2(
                            repo_root=root,
                            repository_path_overrides={relative: replacement},
                        )
                    except subject.YUNSourceBindingV2Error as error:
                        if mode & 0o002 and "SOURCE_WORLD_WRITABLE" not in str(error):
                            raise ValueError("WORLD_WRITABLE_FAILURE_TOKEN_MISSING") from error
                        if not mode & 0o111 and label == "executable" and (
                            "SOURCE_EXECUTABLE_CLASS_MISMATCH" not in str(error)
                        ):
                            raise ValueError("EXECUTABLE_FAILURE_TOKEN_MISSING") from error
                        result[key] = True
                    else:
                        raise ValueError("UNSAFE_MODE_ACCEPTED:" + key)
    return result


def _verify_scientific_semantics(bound: dict[str, object]) -> None:
    normalized = bound["normalized"]
    events = normalized["events"]  # type: ignore[index]
    role = normalized["role"]  # type: ignore[index]
    geometry = normalized["geometry_boundary"]  # type: ignore[index]
    training = normalized["training_boundary"]  # type: ignore[index]
    if (
        len(events) != 7
        or tuple(event["canonical_event_id"] for event in events)
        != yun_v1.EXPECTED_EVENT_IDS
        or [event["scaleup_rank"] for event in events] != list(yun_v1.EXPECTED_RANKS)
        or any(event["D1_task_relevance"] != "RELEVANT" for event in events)
        or any(event["D2_chemistry_support"] != "POSITIVE" for event in events)
        or any(event["D3_reactive_pair"] != "CONFIRM_OBSERVED_PAIR" for event in events)
        or any(event["D4_role_partition"] != "SELECT_CANDIDATE_4" for event in events)
        or any(event["D5_training_use"] != "INCLUDE" for event in events)
        or role["role_profile"] != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        or role["warhead_atoms"] != ["NAS", "CAW", "OAC", "CAO", "CAN"]
        or role["linker_atoms"] != []
        or geometry["POST_source_evidence_count"] != 7
        or geometry["POST_geometry_training_authority_count"] != 0
        or geometry["PRE_geometry_authority_count"] != 0
        or geometry["PRE_precursor_topology_authority_count"] != 0
        or geometry["PRE_reconstruction_count"] != 0
        or training["candidate_for_future_training_admission"] is not True
        or training["training_admitted"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["current_runtime_model_usable"] is not False
        or training["ready_for_training"] is not False
    ):
        raise ValueError("YUN_V2_SCIENTIFIC_EQUIVALENCE_INVALID")
    tasks = yun_v1._canonical_task_contract()
    if (
        tasks["global_canonical_task_count"] != 5
        or tasks["B3_present"] is not True
        or tasks["sixth_task_created"] is not False
        or tasks["direct_profile_applicable_task_ids"] != [0, 3, 4]
    ):
        raise ValueError("YUN_V2_CANONICAL_EXACT5_INVALID")


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = verify_exact4_file_hygiene(root)
    _verify_public_api()
    ast_result = _verify_production_ast(root)
    _verify_v1_pure_call_graph(root)
    v1_false_failure = _verify_v1_static_false_failure_contract(root)
    _verify_b1_dependency(root)
    v1_bindings = _verify_frozen_v1_bytes(root)
    bound = subject.load_frozen_yun_authority_v2(repo_root=root)
    _verify_scientific_semantics(bound)
    artifacts = subject.verify_published_yun_v1_projection_v2(repo_root=root)
    mode_regressions = _exercise_mode_regressions(root)
    census = _verify_current_2a2_census(root)
    legacy_modes = [
        row["mode"] for row in bound["frozen_review_package_bindings"]
    ]
    if legacy_modes != ["0644", "0644", "0644", "0644", "0644", "0755"]:
        raise ValueError("LEGACY_MODE_PROVENANCE_NOT_PRESERVED")
    if bound["source_binding_v2"] != {
        "combined_helper": "verify_bound_source_v2",
        "legacy_mode_metadata_classification": [
            "LEGACY_PROVENANCE_METADATA_PRESERVED",
            "SECURITY_EXECUTABLE_CLASS_INPUT",
        ],
        "exact_posix_numeric_mode_semantic_acceptance": False,
    }:
        raise ValueError("V2_SOURCE_BINDING_CLASSIFICATION_INVALID")
    result = {
        "lifecycle": lifecycle,
        "exact4": exact4,
        "yun_v1_bindings": v1_bindings,
        "yun_v1_bytes_preserved": True,
        "yun_v1_artifacts_preserved": tuple(artifacts) == yun_v1.OUTPUT_FILENAMES,
        "v2_bound_source_helper_used": ast_result["v2_bound_source_helper_used"],
        "exact_posix_semantic_mode_active": ast_result[
            "exact_posix_semantic_mode_active"
        ],
        "legacy_mode_metadata_preserved": True,
        "mode_used_only_for_executable_class": True,
        "v1_false_failure_static_contrast_proven": v1_false_failure,
        "mode_regressions": mode_regressions,
        "scientific_semantics_unchanged": True,
        "event_count": 7,
        "canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "current_global_census": census,
        "current_census_unchanged": True,
        "covapie_state_unchanged": True,
        "historical_validators_unchanged": True,
        "ready_for_v2_b2_2": True,
        "ready_for_training": False,
    }
    required_true = (
        "yun_v1_bytes_preserved",
        "yun_v1_artifacts_preserved",
        "v2_bound_source_helper_used",
        "legacy_mode_metadata_preserved",
        "mode_used_only_for_executable_class",
        "v1_false_failure_static_contrast_proven",
        "scientific_semantics_unchanged",
        "B3_present",
        "current_census_unchanged",
        "covapie_state_unchanged",
        "historical_validators_unchanged",
        "ready_for_v2_b2_2",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if result["exact_posix_semantic_mode_active"] is not False:
        raise ValueError("EXACT_POSIX_SEMANTIC_MODE_STILL_ACTIVE")
    if result["sixth_task_present"] is not False:
        raise ValueError("SIXTH_TASK_CREATED")
    if result["ready_for_training"] is not False:
        raise ValueError("TRAINING_READINESS_BOUNDARY_INVALID")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v2(parser.parse_args().repo_root)
    print("PASS")
    print("lifecycle=" + str(result["lifecycle"]))
    for key in (
        "yun_v1_bytes_preserved",
        "yun_v1_artifacts_preserved",
        "v2_bound_source_helper_used",
        "exact_posix_semantic_mode_active",
        "legacy_mode_metadata_preserved",
        "mode_used_only_for_executable_class",
        "scientific_semantics_unchanged",
        "current_census_unchanged",
        "ready_for_v2_b2_2",
        "ready_for_training",
    ):
        print(key + "=" + str(result[key]).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
