#!/usr/bin/env python3
"""Independent fail-closed checker for the additive OZJ V2 successor."""

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
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
    as ozj_v1,
)
from covalent_ext import (  # noqa: E402
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2
    as subject,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    verify_bound_source_v2,
)


BASELINE_HEAD = "9e7d520de0baa5e5f107985f45b97f576bbd8fc0"
BASELINE_TREE = "84d0f20b7ca89a196c0d31660a60ab4d8e0fed2b"
BASELINE_SUBJECT = "add CovaPIE CHT source binding successor v2"

PRODUCTION_RELATIVE = (
    "src/covalent_ext/"
    "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
)
CHECKER_RELATIVE = (
    "scripts/"
    "check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
)
TEST_RELATIVE = (
    "tests/"
    "test_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
)
GUIDE_RELATIVE = (
    "docs/"
    "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2_guide.md"
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
            "covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        27636,
        "e163f77de8bb03f107efc955ce8662291f9b39deb0ba341b72494d07b97cf87a",
        "published_CHT_V2_successor",
    ),
    (
        Path(
            "scripts/"
            "check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        38205,
        "9642786fb9807da59f189a4a9023b0e9310c06780b357054b464179ddc5a226d",
        "published_CHT_V2_checker",
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
OZJ_V1_BINDINGS = (
    (
        ozj_v1.SOURCE_RELATIVE,
        106888,
        "abb80e28e1e139c3515a01c53468530a815c5554b94053afb607053d14a84deb",
        "published_OZJ_V1_owner",
    ),
    (
        ozj_v1.CHECKER_RELATIVE,
        22027,
        "84289cd412b31c8baecc5bf777adde17341c0e6a37caf85de48ab6a926378e15",
        "published_OZJ_V1_checker",
    ),
    (
        ozj_v1.TEST_RELATIVE,
        26659,
        "e4a6e6b32624427c36e2b2ed970615bc8b78b9d4151c5634fb0078fdde0984cc",
        "published_OZJ_V1_tests",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.SNAPSHOT,
        31404,
        "3458c3559963b09f69495ffe8cf43511a1e84b7de5ad0c84279ccdcd100a4b25",
        "published_OZJ_V1_snapshot",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.MATRIX,
        9031,
        "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3",
        "published_OZJ_V1_matrix",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.SUMMARY,
        4803,
        "305bb814c97a450e8dc95961433daf1e9aca942537469153a89d7e322c6c3214",
        "published_OZJ_V1_summary",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.MANIFEST,
        18554,
        "ca1e305920afd724c138ed572764bd3147039345034ebd172dfb1e274a4a1468",
        "published_OZJ_V1_manifest",
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
_FORBIDDEN_OZJ_V1_CALLS = {
    "_verify_payload",
    "_literal_assignments",
    "load_frozen_formal_decision_v1",
    "_semantic_owner_bindings",
    "_frozen_review_bindings",
    "_architecture_precedent_bindings",
    "_include_precedent_bindings",
    "_current_census_bindings",
    "build_artifacts_v1",
    "_build_artifacts_unvalidated",
    "validate_completed_decision_projection_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
}
_FORBIDDEN_CHT_V1_CALLS = {
    "_verify_payload",
    "_literal_assignments",
    "load_frozen_formal_decision_v1",
    "_semantic_owner_bindings",
    "_frozen_review_bindings",
    "_architecture_precedent_bindings",
    "_exclude_precedent_bindings",
    "_current_census_bindings",
    "build_artifacts_v1",
    "_build_artifacts_unvalidated",
    "validate_completed_decision_projection_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
}
_FORBIDDEN_YUN_V1_CALLS = {
    "_verify_payload",
    "_literal_assignments",
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
        "OZJSourceBindingV2Error",
        "load_frozen_ozj_authority_v2",
        "verify_published_ozj_v1_projection_v2",
    ):
        raise ValueError("PUBLIC_API_INVENTORY_INVALID")
    if not issubclass(subject.OZJSourceBindingV2Error, ValueError):
        raise ValueError("PUBLIC_ERROR_FAMILY_INVALID")
    expected = {
        "load_frozen_ozj_authority_v2": (
            "repo_root",
            "formal_decision_path",
            "repository_path_overrides",
        ),
        "verify_published_ozj_v1_projection_v2": (
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
    forbidden = ("materialize", "mutation", "registry", "resolver", "cache")
    if any(token in name for token in forbidden for name in public_names):
        raise ValueError("FORBIDDEN_PUBLIC_FRAMEWORK_OR_MUTATION_API")


def _verify_production_ast(root: Path) -> dict[str, object]:
    text = _read_regular(root / PRODUCTION_RELATIVE, "OZJ_V2_PRODUCTION").decode(
        "utf-8"
    )
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
    reachable = _reachable_functions(
        functions,
        {
            "load_frozen_ozj_authority_v2",
            "verify_published_ozj_v1_projection_v2",
        },
    )
    for required in (
        "_verify_source",
        "_expected_executable_from_legacy_mode",
        "_exercise_published_cht_v2_precedent",
        "_exercise_published_yun_v2_precedent",
    ):
        if required not in reachable:
            raise ValueError("REQUIRED_ACTIVE_CALL_PATH_MISSING:" + required)
    direct_reads = [
        call.func.attr
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr in {"read_bytes", "read_text", "open"}
    ]
    if direct_reads:
        raise ValueError("DIRECT_SOURCE_READ_BYPASSES_B1")
    ozj_v1_calls = _module_attribute_calls(tree, "ozj_v1")
    if ozj_v1_calls & _FORBIDDEN_OZJ_V1_CALLS:
        raise ValueError("FORBIDDEN_OZJ_V1_ACTIVE_SOURCE_PATH_CALLED")
    if _module_attribute_calls(tree, "cht_v1"):
        raise ValueError("CHT_V1_ACTIVE_REFERENCE_FORBIDDEN")
    if _module_attribute_calls(tree, "yun_v1"):
        raise ValueError("YUN_V1_ACTIVE_REFERENCE_FORBIDDEN")
    cht_v2_calls = _module_attribute_calls(tree, "cht_v2")
    yun_v2_calls = _module_attribute_calls(tree, "yun_v2")
    if "verify_published_cht_v1_projection_v2" not in cht_v2_calls:
        raise ValueError("PUBLISHED_CHT_V2_PREDECESSOR_NOT_ACTIVE")
    if "verify_published_yun_v1_projection_v2" not in yun_v2_calls:
        raise ValueError("PUBLISHED_YUN_V2_PREDECESSOR_NOT_ACTIVE")
    forbidden_tokens = (
        "stat.S_IMODE",
        "st_mode",
        "0o7777",
        "BOUND_SOURCE_MODE_MISMATCH",
    )
    if any(token in text for token in forbidden_tokens):
        raise ValueError("HIDDEN_EXACT_MODE_GATE_FORBIDDEN")
    exact_mode_literals = {"0600", "0644", "0660", "0664", "0755", "0777"}
    for comparison in (
        node for node in ast.walk(tree) if isinstance(node, ast.Compare)
    ):
        values = [comparison.left, *comparison.comparators]
        if any(
            isinstance(value, ast.Constant) and value.value in exact_mode_literals
            for value in values
        ):
            raise ValueError("EXACT_NUMERIC_MODE_COMPARISON_FORBIDDEN")
    return {
        "b1_bound_source_helper_used": True,
        "exact_posix_semantic_mode_active": False,
        "ozj_v1_source_gate_active": False,
        "cht_v1_source_gate_active": False,
        "yun_v1_source_gate_active": False,
        "cht_v2_successor_called": True,
        "yun_v2_successor_called": True,
        "reused_ozj_v1_function_names": sorted(ozj_v1_calls),
    }


def _verify_ozj_v1_pure_call_graph(root: Path) -> None:
    production_tree = ast.parse(
        _read_regular(root / PRODUCTION_RELATIVE, "OZJ_V2_PRODUCTION").decode(
            "utf-8"
        )
    )
    roots = _module_attribute_calls(production_tree, "ozj_v1")
    v1_tree = ast.parse(
        _read_regular(root / ozj_v1.SOURCE_RELATIVE, "OZJ_V1_OWNER").decode(
            "utf-8"
        )
    )
    reachable = _reachable_functions(_function_nodes(v1_tree), roots)
    if reachable & _FORBIDDEN_OZJ_V1_CALLS:
        raise ValueError("REUSED_OZJ_V1_HELPER_REACHES_SOURCE_OR_MUTATION_GATE")


def _verify_predecessor_call_graph(
    root: Path,
    relative: Path,
    module_name: str,
    public_roots: set[str],
    forbidden_v1_calls: set[str],
) -> None:
    tree = ast.parse(
        _read_regular(root / relative, module_name + "_OWNER").decode("utf-8")
    )
    functions = _function_nodes(tree)
    reachable = _reachable_functions(functions, public_roots)
    if "_verify_source" not in reachable:
        raise ValueError(module_name + "_BOUND_SOURCE_PATH_NOT_ACTIVE")
    v1_calls = _module_attribute_calls(tree, module_name.lower() + "_v1")
    if v1_calls & forbidden_v1_calls:
        raise ValueError(module_name + "_V2_REACHES_V1_SOURCE_GATE")


def _verify_v1_static_false_failure_contract(root: Path) -> bool:
    text = _read_regular(root / ozj_v1.SOURCE_RELATIVE, "OZJ_V1_OWNER").decode(
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
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    with tempfile.TemporaryDirectory(prefix="covapie_ozj_v1_contrast_") as name:
        replacement = Path(name) / binding[0].name
        shutil.copyfile(root.parent / binding[0], replacement)
        replacement.chmod(0o644)
        try:
            ozj_v1._verify_payload(
                replacement,
                binding[1],
                binding[2],
                binding[3],
                binding[4],
            )
        except ozj_v1.OZJIngestionSafetyError as error:
            if "BOUND_SOURCE_MODE_MISMATCH" not in str(error):
                raise ValueError("V1_FALSE_FAILURE_TOKEN_MISSING") from error
        else:
            raise ValueError("V1_SAFE_MODE_DRIFT_DID_NOT_FALSE_FAIL")
        subject.load_frozen_ozj_authority_v2(
            repo_root=root,
            repository_path_overrides={binding[0]: replacement},
        )
    return True


def _verify_bound_bindings(
    root: Path, bindings: tuple[tuple[Path, int, str, str], ...]
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
    for commit in (subject.CHT_V2_PUBLISHED_COMMIT, subject.YUN_V2_PUBLISHED_COMMIT):
        if _git("show", "-s", "--format=%H", commit, root=root) != commit:
            raise ValueError("PUBLISHED_PREDECESSOR_COMMIT_MISSING:" + commit)


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
        task["display_alias"]: task[
            "structurally_applicable_authoritative_role_count"
        ]
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


def _exercise_mode_regressions(root: Path) -> dict[str, bool]:
    ordinary = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    validator = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[-1]
    baseline = subject.load_frozen_ozj_authority_v2(repo_root=root)
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_ozj_v2_modes_") as name:
        temporary = Path(name)
        for binding, label in ((ordinary, "ordinary"), (validator, "validator_py")):
            relative = binding[0]
            replacement = temporary / (label + relative.suffix)
            shutil.copyfile(root.parent / relative, replacement)
            for mode in (0o600, 0o644, 0o660, 0o664):
                replacement.chmod(mode)
                key = f"{label}_{mode:04o}"
                observed = subject.load_frozen_ozj_authority_v2(
                    repo_root=root,
                    repository_path_overrides={relative: replacement},
                )
                if observed != baseline:
                    raise ValueError("MODE_ONLY_AUTHORITY_RESULT_DRIFT:" + key)
                result[key] = True
            for mode in (0o755, 0o775, 0o666, 0o777):
                replacement.chmod(mode)
                key = f"{label}_{mode:04o}"
                try:
                    subject.load_frozen_ozj_authority_v2(
                        repo_root=root,
                        repository_path_overrides={relative: replacement},
                    )
                except subject.OZJSourceBindingV2Error as error:
                    expected_token = (
                        "SOURCE_WORLD_WRITABLE"
                        if mode & 0o002
                        else "SOURCE_EXECUTABLE_CLASS_MISMATCH"
                    )
                    if expected_token not in str(error):
                        raise ValueError(
                            "UNSAFE_MODE_FAILURE_TOKEN_MISSING:" + key
                        ) from error
                    result[key] = True
                else:
                    raise ValueError("UNSAFE_MODE_ACCEPTED:" + key)
    return result


def _exercise_source_failure_regressions(root: Path) -> dict[str, bool]:
    binding = ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS[0]
    relative = binding[0]
    result: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie_ozj_v2_failures_") as name:
        temporary = Path(name)
        canonical = root.parent / relative

        wrong_bytes = temporary / "wrong-bytes.json"
        shutil.copyfile(canonical, wrong_bytes)
        wrong_bytes.write_bytes(wrong_bytes.read_bytes() + b"\n")
        try:
            subject.load_frozen_ozj_authority_v2(
                repo_root=root,
                repository_path_overrides={relative: wrong_bytes},
            )
        except subject.OZJSourceBindingV2Error as error:
            if "SOURCE_BYTE_COUNT_MISMATCH" not in str(error):
                raise ValueError("WRONG_BYTE_COUNT_FAILURE_TOKEN_MISSING") from error
            result["wrong_byte_count_rejected"] = True
        else:
            raise ValueError("WRONG_BYTE_COUNT_ACCEPTED")

        wrong_sha = temporary / "wrong-sha.json"
        shutil.copyfile(canonical, wrong_sha)
        payload = bytearray(wrong_sha.read_bytes())
        payload[0] ^= 1
        wrong_sha.write_bytes(payload)
        try:
            subject.load_frozen_ozj_authority_v2(
                repo_root=root,
                repository_path_overrides={relative: wrong_sha},
            )
        except subject.OZJSourceBindingV2Error as error:
            if "SOURCE_SHA256_MISMATCH" not in str(error):
                raise ValueError("WRONG_SHA_FAILURE_TOKEN_MISSING") from error
            result["same_size_wrong_sha_rejected"] = True
        else:
            raise ValueError("WRONG_SHA_ACCEPTED")

        target = temporary / "target.json"
        shutil.copyfile(canonical, target)
        link = temporary / "source-link.json"
        link.symlink_to(target.name)
        try:
            subject.load_frozen_ozj_authority_v2(
                repo_root=root,
                repository_path_overrides={relative: link},
            )
        except subject.OZJSourceBindingV2Error as error:
            if "SOURCE_SYMLINK_FORBIDDEN" not in str(error):
                raise ValueError("SYMLINK_FAILURE_TOKEN_MISSING") from error
            result["symlink_rejected"] = True
        else:
            raise ValueError("SYMLINK_ACCEPTED")

        try:
            subject.load_frozen_ozj_authority_v2(
                repo_root=root,
                repository_path_overrides={Path("unexpected.txt"): target},
            )
        except subject.OZJSourceBindingV2Error as error:
            if "REPOSITORY_PATH_OVERRIDE_UNEXPECTED" not in str(error):
                raise ValueError("UNEXPECTED_OVERRIDE_FAILURE_TOKEN_MISSING") from error
            result["unexpected_override_rejected"] = True
        else:
            raise ValueError("UNEXPECTED_OVERRIDE_ACCEPTED")
    return result


def _verify_scientific_semantics(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    normalized = bound["normalized"]
    events = normalized["events"]  # type: ignore[index]
    role = normalized["role"]  # type: ignore[index]
    geometry = normalized["geometry_boundary"]  # type: ignore[index]
    topology = normalized[  # type: ignore[index]
        "source_ccd_and_event_topology_boundary"
    ]
    training = normalized["training_boundary"]  # type: ignore[index]
    approval = formal["human_approval"]  # type: ignore[index]
    if (
        len(events) != 4
        or tuple(event["canonical_event_id"] for event in events)
        != ozj_v1.EXPECTED_EVENT_IDS
        or [event["scaleup_rank"] for event in events]
        != list(ozj_v1.EXPECTED_RANKS)
        or any(event["pdb_id"] != "4CL8" for event in events)
        or any(event["cys_residue_id"] != "CYS:168-" for event in events)
        or any(event["task_relevant"] is not True for event in events)
        or any(event["chemistry_known_positive"] is not True for event in events)
        or any(event["negative_chemistry"] is not False for event in events)
        or any(event["task_domain_negative"] is not False for event in events)
        or any(event["protein_reactive_atom"] != "SG" for event in events)
        or any(event["ligand_reactive_atom"] != "CAF" for event in events)
        or any(event["selected_role_candidate_index_0based"] != 1 for event in events)
        or any(event["formal_event_training_use_decision"] != "INCLUDE" for event in events)
        or approval["D1_task_relevance"] != "RELEVANT"
        or approval["D2_chemistry"] != "POSITIVE"
        or approval["D3_reactive_pair"] != "CONFIRM_OBSERVED_PAIR"
        or approval["D4_role_partition"] != "SELECT_CANDIDATE_1"
        or approval["D5_training_use"] != "INCLUDE"
        or approval["D6_scientific_context"] != ozj_v1.EXPECTED_D6
        or role["role_profile"] != "STRICT_LINKER_PRESENT_V1"
        or role["exact_heavy_atom_ids"] != list(ozj_v1.EXPECTED_HEAVY_ATOMS)
        or role["warhead_atoms"] != ["CAF", "OAD"]
        or role["linker_atoms"] != ["CAG", "CAH", "CAI", "CAJ", "CAP", "CAQ"]
        or role["scaffold_atoms"] != list(ozj_v1.EXPECTED_SCAFFOLD)
        or geometry["POST_source_evidence_count"] != 4
        or geometry["POST_geometry_training_authority_count"] != 0
        or geometry["PRE_geometry_authority_count"] != 0
        or geometry["PRE_precursor_topology_authority_count"] != 0
        or geometry["PRE_reconstruction_count"] != 0
        or geometry["POST_to_PRE_copy_performed"] is not False
        or geometry["PRE_zero_fill_performed"] is not False
        or topology["source_CAF_OAD_bond_order"] != "DOUB"
        or topology["explicit_observed_SG_CAF_connection_event_count"] != 4
        or topology["complete_POST_topology_authority_available"] is not False
        or topology["PRE_topology_authority_available"] is not False
        or topology["PRE_geometry_authority_available"] is not False
        or topology["PRE_reconstruction_performed"] is not False
        or topology["POST_bond_order_reconstruction_performed"] is not False
        or training["human_training_excluded"] is not False
        or training["training_use_allowed"] is not True
        or training["training_use_include"] is not True
        or training["candidate_for_future_training_admission"] is not True
        or training["future_training_candidate_derived_by_ingestion"] is not True
        or training["future_training_candidate_is_training_admission"] is not False
        or training["training_admitted"] is not False
        or training["training_admission_created"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["current_runtime_model_usable"] is not False
        or training["ready_for_training"] is not False
    ):
        raise ValueError("OZJ_V2_SCIENTIFIC_EQUIVALENCE_INVALID")
    tasks = ozj_v1._canonical_task_contract()
    applicability = tasks["strict_profile_task_applicability"]
    if (
        tasks["global_canonical_task_count"] != 5
        or tasks["B3_present"] is not True
        or tasks["sixth_task_created"] is not False
        or tasks["strict_profile_applicable_task_ids"] != [0, 1, 2, 3, 4]
        or len(applicability) != 5
        or any(item["structurally_applicable"] is not True for item in applicability)
        or [item["display_alias"] for item in applicability]
        != ["A", "B", "B2", "B3", "C"]
        or applicability[3]["semantic_long_name"] != "scaffold_only"
    ):
        raise ValueError("OZJ_V2_CANONICAL_EXACT5_INVALID")


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = verify_exact4_file_hygiene(root)
    _verify_public_api()
    ast_result = _verify_production_ast(root)
    _verify_ozj_v1_pure_call_graph(root)
    _verify_predecessor_call_graph(
        root,
        subject.CHT_V2_RELATIVE,
        "CHT",
        {"load_frozen_cht_authority_v2", "verify_published_cht_v1_projection_v2"},
        _FORBIDDEN_CHT_V1_CALLS,
    )
    _verify_predecessor_call_graph(
        root,
        subject.YUN_V2_RELATIVE,
        "YUN",
        {"load_frozen_yun_authority_v2", "verify_published_yun_v1_projection_v2"},
        _FORBIDDEN_YUN_V1_CALLS,
    )
    _verify_published_commit_ancestry(root)
    b1_bindings = _verify_bound_bindings(root, (B1_BINDING,))
    dual_v2_bindings = _verify_bound_bindings(root, DUAL_V2_BINDINGS)
    v1_bindings = _verify_bound_bindings(root, OZJ_V1_BINDINGS)
    bound = subject.load_frozen_ozj_authority_v2(repo_root=root)
    _verify_scientific_semantics(bound)
    artifacts = subject.verify_published_ozj_v1_projection_v2(repo_root=root)
    v1_false_failure = _verify_v1_static_false_failure_contract(root)
    mode_regressions = _exercise_mode_regressions(root)
    source_failures = _exercise_source_failure_regressions(root)
    census = _verify_current_2a2_census(root)

    source_binding = bound["source_binding_v2"]
    if source_binding != {
        "combined_helper": "verify_bound_source_v2",
        "legacy_mode_metadata_classification": [
            "LEGACY_PROVENANCE_METADATA_PRESERVED",
            "SECURITY_EXECUTABLE_CLASS_INPUT",
        ],
        "historical_review_modes": ["0664"] * 6,
        "review_source_expected_executable_classes": [False] * 6,
        "review_package_validator_expected_executable": False,
        "exact_posix_numeric_mode_semantic_acceptance": False,
    }:
        raise ValueError("OZJ_V2_SOURCE_BINDING_CLASSIFICATION_INVALID")
    legacy_modes = [
        row["mode"] for row in bound["frozen_review_package_bindings"]
    ]
    if legacy_modes != ["0664"] * 6:
        raise ValueError("LEGACY_MODE_PROVENANCE_NOT_PRESERVED")
    dual = bound["dual_published_v2_predecessors"]
    expected_dual = {
        "published_CHT_V2_successor_bound": True,
        "CHT_V2_sha256": subject.CHT_V2_SHA256,
        "CHT_V2_published_commit": subject.CHT_V2_PUBLISHED_COMMIT,
        "CHT_V2_source_binding_migration_active": True,
        "CHT_V2_projection_actually_called": True,
        "CHT_V1_scientific_matrix_preserved": True,
        "published_YUN_V2_successor_bound": True,
        "YUN_V2_sha256": subject.YUN_V2_SHA256,
        "YUN_V2_published_commit": subject.YUN_V2_PUBLISHED_COMMIT,
        "YUN_V2_source_binding_migration_active": True,
        "YUN_V2_projection_actually_called": True,
        "YUN_V1_INCLUDE_projection_preserved": True,
    }
    if dual != expected_dual:
        raise ValueError("DUAL_V2_PREDECESSOR_RECORD_INVALID")

    result = {
        "lifecycle": lifecycle,
        "exact4": exact4,
        "b1_bindings": b1_bindings,
        "dual_v2_bindings": dual_v2_bindings,
        "ozj_v1_bindings": v1_bindings,
        "ozj_v1_bytes_preserved": True,
        "ozj_v1_artifacts_preserved": tuple(artifacts) == ozj_v1.OUTPUT_FILENAMES,
        "b1_bound_source_helper_used": ast_result["b1_bound_source_helper_used"],
        "cht_v2_successor_bound": ast_result["cht_v2_successor_called"],
        "cht_v2_projection_exercised": dual["CHT_V2_projection_actually_called"],
        "yun_v2_successor_bound": ast_result["yun_v2_successor_called"],
        "yun_v2_projection_exercised": dual["YUN_V2_projection_actually_called"],
        "cht_v1_scientific_matrix_preserved": dual[
            "CHT_V1_scientific_matrix_preserved"
        ],
        "yun_v1_include_projection_preserved": dual[
            "YUN_V1_INCLUDE_projection_preserved"
        ],
        "ozj_v1_source_gate_active": ast_result["ozj_v1_source_gate_active"],
        "cht_v1_source_gate_active": ast_result["cht_v1_source_gate_active"],
        "yun_v1_source_gate_active": ast_result["yun_v1_source_gate_active"],
        "exact_posix_semantic_mode_active": ast_result[
            "exact_posix_semantic_mode_active"
        ],
        "legacy_mode_metadata_preserved": True,
        "all_review_sources_expected_nonexecutable": True,
        "review_package_validator_expected_nonexecutable": True,
        "v1_false_failure_static_contrast_proven": v1_false_failure,
        "mode_regressions": mode_regressions,
        "source_failure_regressions": source_failures,
        "scientific_semantics_unchanged": True,
        "strict_exact5_all_tasks_applicable": True,
        "include_future_candidate_preserved": True,
        "event_count": 4,
        "canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "current_global_census": census,
        "current_census_unchanged": True,
        "covapie_state_unchanged": True,
        "historical_validators_unchanged": True,
        "ready_for_v2_b2_5": True,
        "ready_for_training": False,
    }
    required_true = (
        "ozj_v1_bytes_preserved",
        "ozj_v1_artifacts_preserved",
        "b1_bound_source_helper_used",
        "cht_v2_successor_bound",
        "cht_v2_projection_exercised",
        "yun_v2_successor_bound",
        "yun_v2_projection_exercised",
        "cht_v1_scientific_matrix_preserved",
        "yun_v1_include_projection_preserved",
        "legacy_mode_metadata_preserved",
        "all_review_sources_expected_nonexecutable",
        "review_package_validator_expected_nonexecutable",
        "v1_false_failure_static_contrast_proven",
        "scientific_semantics_unchanged",
        "strict_exact5_all_tasks_applicable",
        "include_future_candidate_preserved",
        "B3_present",
        "current_census_unchanged",
        "covapie_state_unchanged",
        "historical_validators_unchanged",
        "ready_for_v2_b2_5",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    for field in (
        "ozj_v1_source_gate_active",
        "cht_v1_source_gate_active",
        "yun_v1_source_gate_active",
        "exact_posix_semantic_mode_active",
        "sixth_task_present",
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
        "ozj_v1_bytes_preserved",
        "ozj_v1_artifacts_preserved",
        "b1_bound_source_helper_used",
        "cht_v2_successor_bound",
        "cht_v2_projection_exercised",
        "yun_v2_successor_bound",
        "yun_v2_projection_exercised",
        "exact_posix_semantic_mode_active",
        "legacy_mode_metadata_preserved",
        "all_review_sources_expected_nonexecutable",
        "scientific_semantics_unchanged",
        "strict_exact5_all_tasks_applicable",
        "include_future_candidate_preserved",
        "current_census_unchanged",
        "ready_for_v2_b2_5",
        "ready_for_training",
    ):
        print(key + "=" + str(result[key]).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
