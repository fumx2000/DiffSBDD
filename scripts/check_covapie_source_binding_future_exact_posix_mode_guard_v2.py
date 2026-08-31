#!/usr/bin/env python3
"""Independently check the Phase-B4 future exact-POSIX mode guard."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
from pathlib import Path
import stat
import subprocess

from covalent_ext import (
    covapie_source_binding_future_exact_posix_mode_guard_v2 as subject,
)
from covalent_ext import covapie_source_binding_policy_v2 as source_binding_v2


ROOT = Path(__file__).resolve().parents[1]
BASELINE_HEAD = "54f98c41e2dc34d816a17242292ee2379e99783e"
BASELINE_TREE = "ba92ef88433c8290285dacf482ed17300753fbab"
BASELINE_SUBJECT = "add CovaPIE source binding historical immutability proof v2"
MAX_FILE_BYTES = 1024 * 1024

PRODUCTION_RELATIVE = (
    "src/covalent_ext/"
    "covapie_source_binding_future_exact_posix_mode_guard_v2.py"
)
CHECKER_RELATIVE = (
    "scripts/check_covapie_source_binding_future_exact_posix_mode_guard_v2.py"
)
TEST_RELATIVE = (
    "tests/test_covapie_source_binding_future_exact_posix_mode_guard_v2.py"
)
GUIDE_RELATIVE = (
    "docs/covapie_source_binding_future_exact_posix_mode_guard_v2_guide.md"
)
EXACT4_PATHS = (
    PRODUCTION_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    GUIDE_RELATIVE,
)

FROZEN_DEPENDENCIES = (
    (
        "SOURCE_BINDING_POLICY_V2",
        "src/covalent_ext/covapie_source_binding_policy_v2.py",
        3704,
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    ),
    (
        "SOURCE_BINDING_HISTORICAL_IMMUTABILITY_PROOF_V2",
        "src/covalent_ext/covapie_source_binding_historical_immutability_proof_v2.py",
        35903,
        "0457d641ba313021c481a5817fda8a04c76cdbf1aafe462044edbf2049e6f43d",
    ),
    (
        "SOURCE_BINDING_HISTORICAL_IMMUTABILITY_PROOF_V2_CHECKER",
        "scripts/check_covapie_source_binding_historical_immutability_proof_v2.py",
        43229,
        "e502eeb1e60ed25838101ab3a74cd7b2381727a40bf1a1437b790beb1cf26332",
    ),
)

SEMANTIC_SOURCE_IDENTITY = "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
SECURITY_HYGIENE = "SECURITY_HYGIENE_MODE_CHECK"
CANDIDATE_HYGIENE = "CANDIDATE_ARTIFACT_MODE_HYGIENE"
GIT_OR_EXECUTABLE_CLASS = "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT"
REPORTING_DIAGNOSTIC = "REPORTING_OR_DIAGNOSTIC_MODE_METADATA"
AMBIGUOUS = "AMBIGUOUS_REQUIRES_HUMAN_REVIEW"


def _git(root: Path, *arguments: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise ValueError("GIT_COMMAND_FAILED:" + arguments[0])
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").rstrip("\n")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def classify_lifecycle_from_facts(
    *,
    tracked_exact4: set[str],
    ordinary_untracked: set[str],
    status_entries: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    expected = set(EXACT4_PATHS)
    if (
        not tracked_exact4
        and ordinary_untracked == expected
        and tuple(sorted(status_entries))
        == tuple(f"?? {path}" for path in sorted(expected))
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


def validate_repository_relation_from_facts(
    *,
    profile: str,
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    parent_shas: tuple[str, ...],
    changed_paths: set[str],
) -> None:
    if profile == "CANDIDATE_UNTRACKED":
        if not (
            head == BASELINE_HEAD
            and origin_main == BASELINE_HEAD
            and (ahead, behind) == (0, 0)
            and not parent_shas
            and not changed_paths
        ):
            raise ValueError("CANDIDATE_REPOSITORY_RELATION_INVALID")
        return
    if profile != "TRACKED_CLEAN":
        raise ValueError("REPOSITORY_RELATION_PROFILE_INVALID")
    if (
        head == BASELINE_HEAD
        or parent_shas != (BASELINE_HEAD,)
        or changed_paths != set(EXACT4_PATHS)
    ):
        raise ValueError("TRACKED_CLEAN_COMMIT_IDENTITY_INVALID")
    if not (
        (origin_main == BASELINE_HEAD and (ahead, behind) == (1, 0))
        or (origin_main == head and (ahead, behind) == (0, 0))
    ):
        raise ValueError("TRACKED_CLEAN_REPOSITORY_RELATION_INVALID")


def verify_git_lifecycle(root: Path) -> str:
    baseline = str(
        _git(root, "show", "-s", "--format=%T%n%s", BASELINE_HEAD)
    ).splitlines()
    if baseline != [BASELINE_TREE, BASELINE_SUBJECT]:
        raise ValueError("BASELINE_TREE_OR_SUBJECT_INVALID")
    tracked = set(
        filter(
            None,
            str(_git(root, "ls-files", "--", *EXACT4_PATHS)).splitlines(),
        )
    )
    untracked = set(
        filter(
            None,
            str(_git(root, "ls-files", "--others", "--exclude-standard")).splitlines(),
        )
    )
    status = tuple(
        filter(
            None,
            str(
                _git(
                    root,
                    "status",
                    "--porcelain=v1",
                    "--untracked-files=all",
                )
            ).splitlines(),
        )
    )
    working = set(
        filter(None, str(_git(root, "diff", "--name-only")).splitlines())
    )
    cached = set(
        filter(
            None,
            str(_git(root, "diff", "--cached", "--name-only")).splitlines(),
        )
    )
    profile = classify_lifecycle_from_facts(
        tracked_exact4=tracked,
        ordinary_untracked=untracked,
        status_entries=status,
        working_diff=working,
        cached_diff=cached,
    )
    head = str(_git(root, "rev-parse", "HEAD"))
    origin_main = str(_git(root, "rev-parse", "origin/main"))
    relation = str(
        _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")
    ).split()
    if len(relation) != 2 or any(not item.isdigit() for item in relation):
        raise ValueError("REPOSITORY_RELATION_COUNT_INVALID")
    ahead, behind = (int(item) for item in relation)
    if profile == "TRACKED_CLEAN":
        parents = tuple(str(_git(root, "show", "-s", "--format=%P", "HEAD")).split())
        changed = set(
            filter(
                None,
                str(
                    _git(
                        root,
                        "diff-tree",
                        "--no-commit-id",
                        "--name-only",
                        "-r",
                        "HEAD",
                    )
                ).splitlines(),
            )
        )
    else:
        parents = ()
        changed = set()
    validate_repository_relation_from_facts(
        profile=profile,
        head=head,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        parent_shas=parents,
        changed_paths=changed,
    )
    return profile


def _verify_exact4_hygiene(root: Path) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for relative in EXACT4_PATHS:
        path = root / relative
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("EXACT4_NOT_REGULAR:" + relative)
        mode = stat.S_IMODE(metadata.st_mode)
        if mode not in {0o644, 0o664}:
            raise ValueError("EXACT4_MODE_INVALID:" + relative)
        if metadata.st_mode & 0o111:
            raise ValueError("EXACT4_EXECUTABLE_FORBIDDEN:" + relative)
        payload = path.read_bytes()
        if not payload or len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_SIZE_INVALID:" + relative)
        if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
            raise ValueError("EXACT4_ENCODING_BYTES_INVALID:" + relative)
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("EXACT4_UTF8_INVALID:" + relative) from error
        if not text.endswith("\n") or text.endswith("\n\n"):
            raise ValueError("EXACT4_FINAL_LF_INVALID:" + relative)
        if any(line.rstrip(" \t") != line for line in text.splitlines()):
            raise ValueError("EXACT4_TRAILING_WHITESPACE:" + relative)
        result[relative] = {
            "bytes": len(payload),
            "loc": len(text.splitlines()),
            "mode": format(mode, "04o"),
            "sha256": _sha256(payload),
        }
    return result


def _verify_frozen_dependencies(root: Path) -> None:
    for label, relative, byte_count, sha256 in FROZEN_DEPENDENCIES:
        source_binding_v2.verify_bound_source_v2(
            path=root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=False,
        )


def _verify_baseline_history(root: Path) -> None:
    identity = str(
        _git(root, "show", "-s", "--format=%H%n%T%n%s", BASELINE_HEAD)
    ).splitlines()
    if identity != [BASELINE_HEAD, BASELINE_TREE, BASELINE_SUBJECT]:
        raise ValueError("B3_PUBLISHED_COMMIT_IDENTITY_INVALID")
    _git(root, "merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD")


def _verify_public_api_and_static_safety(root: Path) -> None:
    if subject.__all__ != (
        "SourceBindingFutureExactPosixModeGuardV2Error",
        "verify_covapie_source_binding_future_exact_posix_mode_guard_v2",
    ):
        raise ValueError("PUBLIC_API_INVALID")
    signature = inspect.signature(
        subject.verify_covapie_source_binding_future_exact_posix_mode_guard_v2
    )
    if tuple(signature.parameters) != ("repo_root",):
        raise ValueError("PUBLIC_SIGNATURE_PARAMETERS_INVALID")
    parameter = signature.parameters["repo_root"]
    if parameter.kind is not inspect.Parameter.KEYWORD_ONLY:
        raise ValueError("PUBLIC_SIGNATURE_NOT_KEYWORD_ONLY")
    source = (root / PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=PRODUCTION_RELATIVE)
    imported_covapie_modules: set[str] = set()
    forbidden_calls = {
        "write_bytes",
        "write_text",
        "mkdir",
        "rename",
        "replace",
        "unlink",
        "chmod",
    }
    forbidden_git = {
        "add",
        "commit",
        "checkout",
        "switch",
        "restore",
        "reset",
        "clean",
        "stash",
        "rebase",
        "merge",
        "push",
        "pull",
        "fetch",
        "update-ref",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            imported_covapie_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls:
                raise ValueError("PRODUCTION_FILESYSTEM_MUTATION_API_PRESENT")
            for argument in node.args:
                if isinstance(argument, ast.Constant) and argument.value in forbidden_git:
                    raise ValueError("PRODUCTION_FORBIDDEN_GIT_SUBCOMMAND_PRESENT")
        if isinstance(node, ast.If):
            segment = ast.get_source_segment(source, node.test) or ""
            if "_v1" in segment.lower() and ("path" in segment or "relative" in segment):
                raise ValueError("V1_FILENAME_EXCLUSION_PRESENT")
    if imported_covapie_modules != {
        "covapie_source_binding_historical_immutability_proof_v2",
        "covapie_source_binding_policy_v2",
    }:
        raise ValueError("PRODUCTION_COVAPIE_IMPORT_BOUNDARY_INVALID")
    forbidden_tokens = ("torch", "optimizer", "trainer", "tensorization")
    if any(token in source.lower() for token in forbidden_tokens):
        raise ValueError("PRODUCTION_TRAINING_TOKEN_PRESENT")
    required_scope_literals = (
        "src/covalent_ext/",
        "scripts/check_covapie",
        "tests/test_covapie",
        "data/derived/covalent_small/",
    )
    if any(literal not in source for literal in required_scope_literals):
        raise ValueError("PRODUCTION_SCAN_SCOPE_LITERAL_MISSING")


def _classes(rows: tuple[dict[str, object], ...]) -> set[str]:
    return {str(row["semantic_class"]) for row in rows}


def _classify_python(snippet: str, label: str) -> tuple[dict[str, object], ...]:
    return subject._classify_python_text_v2(
        snippet,
        source_path="src/covalent_ext/synthetic_" + label + ".py",
        test_only=False,
    )


def _verify_python_classifier_controls() -> dict[str, bool]:
    bad_simode = """
import stat
def verify_source_binding(path, expected_mode):
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != expected_mode:
        _fail("SOURCE_MODE_DRIFT")
"""
    bad_mask = """
def verify_source_binding(path, binding):
    actual = format(path.stat().st_mode & 0o7777, "04o")
    if actual != binding["mode"]:
        raise ValueError("drift")
"""
    bad_membership = """
def verify_source_identity(source_mode):
    if source_mode not in {"0600", "0644", "0664", "0755"}:
        reject("SOURCE_IDENTITY_INVALID")
"""
    alias_binding = """
import stat
def verify_source_binding(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    expected = binding["mode"]
    if actual != expected:
        reject("SOURCE_MODE_DRIFT")
"""
    transitive_alias = """
import stat
def verify_source_binding(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    observed = actual
    expected = binding["mode"]
    required = expected
    if observed != required:
        reject("SOURCE_MODE_DRIFT")
"""
    unknown_full = """
import stat
def verify_policy(path, policy_value):
    observed = stat.S_IMODE(path.stat().st_mode)
    if observed != policy_value:
        reject("UNKNOWN_MODE_POLICY")
"""
    non_historical_mode = """
import stat
def verify_source_binding(path):
    actual = stat.S_IMODE(path.stat().st_mode)
    if actual != 0o640:
        reject("SOURCE_IDENTITY_INVALID")
"""
    candidate_source_collision = """
import stat
def verify_candidate_source_binding(path):
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o644:
        reject("SOURCE_IDENTITY_INVALID")
"""
    executable_name_collision = """
import stat
def verify_source_binding(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    executable_policy = binding["mode"]
    if actual != executable_policy:
        reject("SOURCE_MODE_DRIFT")
"""
    historical_mode_identity = """
import stat
def verify_source(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    expected = binding["historical_mode"]
    if actual != expected:
        reject("SOURCE_MODE_DRIFT")
"""
    world_write = """
import stat
def verify_source_security(path):
    mode = path.stat().st_mode
    if mode & stat.S_IWOTH:
        fail("WORLD_WRITABLE")
"""
    executable = """
def verify_executable_class(path, expected_executable):
    mode = path.stat().st_mode
    actual_executable = bool(mode & 0o111)
    if actual_executable != expected_executable:
        fail("EXEC_CLASS")
"""
    candidate = """
import stat
def verify_candidate_exact4_hygiene(path):
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode not in {0o644, 0o664}:
        fail("CANDIDATE_MODE")
"""
    git_class = """
def verify_git_file_class(path_modes):
    if path_modes["owner.py"] not in {"100644", "100755"}:
        fail("GIT_MODE")
"""
    reporting = """
def build_report(report):
    report["historical_mode"] = "0600"
"""
    legacy_exec = """
def legacy_provenance_to_exec(legacy_mode):
    expected_executable = bool(int(legacy_mode, 8) & 0o111)
    return expected_executable
"""
    bad1 = _classes(_classify_python(bad_simode, "bad_simode"))
    bad2 = _classes(_classify_python(bad_mask, "bad_mask"))
    bad3 = _classes(_classify_python(bad_membership, "bad_membership"))
    revised = {
        "alias_binding": _classes(_classify_python(alias_binding, "alias_binding")),
        "transitive_alias": _classes(
            _classify_python(transitive_alias, "transitive_alias")
        ),
        "unknown_full": _classes(_classify_python(unknown_full, "unknown_full")),
        "non_historical_mode": _classes(
            _classify_python(non_historical_mode, "non_historical_mode")
        ),
        "candidate_source_collision": _classes(
            _classify_python(candidate_source_collision, "candidate_source_collision")
        ),
        "executable_name_collision": _classes(
            _classify_python(executable_name_collision, "executable_name_collision")
        ),
        "historical_mode_identity": _classes(
            _classify_python(historical_mode_identity, "historical_mode_identity")
        ),
    }
    allowed = {
        "world_write": _classes(_classify_python(world_write, "world_write")),
        "executable": _classes(_classify_python(executable, "executable")),
        "candidate": _classes(_classify_python(candidate, "candidate")),
        "git_class": _classes(_classify_python(git_class, "git_class")),
        "reporting": _classes(_classify_python(reporting, "reporting")),
        "legacy_exec": _classes(_classify_python(legacy_exec, "legacy_exec")),
    }
    if SEMANTIC_SOURCE_IDENTITY not in bad1:
        raise ValueError("BAD_SIMODE_NOT_REJECTED")
    if SEMANTIC_SOURCE_IDENTITY not in bad2:
        raise ValueError("BAD_0O7777_NOT_REJECTED")
    if SEMANTIC_SOURCE_IDENTITY not in bad3:
        raise ValueError("BAD_EXACT_MEMBERSHIP_NOT_REJECTED")
    for label in (
        "alias_binding",
        "transitive_alias",
        "non_historical_mode",
        "candidate_source_collision",
    ):
        if SEMANTIC_SOURCE_IDENTITY not in revised[label]:
            raise ValueError("REVISED1_SEMANTIC_CONTROL_NOT_REJECTED:" + label)
    if AMBIGUOUS not in revised["unknown_full"]:
        raise ValueError("REVISED1_UNKNOWN_FULL_MODE_DID_NOT_FAIL_CLOSED")
    for label in ("executable_name_collision", "historical_mode_identity"):
        if not revised[label] & {SEMANTIC_SOURCE_IDENTITY, AMBIGUOUS}:
            raise ValueError("REVISED1_COLLISION_DID_NOT_FAIL_CLOSED:" + label)
    if GIT_OR_EXECUTABLE_CLASS in revised["executable_name_collision"]:
        raise ValueError("REVISED1_EXECUTABLE_NAME_COLLISION_ALLOWED")
    if CANDIDATE_HYGIENE in revised["candidate_source_collision"]:
        raise ValueError("REVISED1_CANDIDATE_SOURCE_COLLISION_ALLOWED")
    expected = {
        "world_write": SECURITY_HYGIENE,
        "executable": GIT_OR_EXECUTABLE_CLASS,
        "candidate": CANDIDATE_HYGIENE,
        "git_class": GIT_OR_EXECUTABLE_CLASS,
        "reporting": REPORTING_DIAGNOSTIC,
        "legacy_exec": GIT_OR_EXECUTABLE_CLASS,
    }
    for label, semantic_class in expected.items():
        if semantic_class not in allowed[label]:
            raise ValueError("ALLOWED_CONTROL_MISCLASSIFIED:" + label)
        if allowed[label] & {SEMANTIC_SOURCE_IDENTITY, AMBIGUOUS}:
            raise ValueError("ALLOWED_CONTROL_FAILED_CLOSED:" + label)
    return {
        "bad_S_IMODE_semantic_comparison_rejected": True,
        "bad_0o7777_semantic_comparison_rejected": True,
        "bad_exact_mode_membership_rejected": True,
        "alias_binding_mode_rejected": True,
        "transitive_alias_binding_mode_rejected": True,
        "unknown_full_mode_compare_failed_closed": True,
        "non_historical_exact_posix_mode_rejected": True,
        "candidate_source_identity_collision_rejected": True,
        "executable_name_only_collision_rejected": True,
        "historical_mode_live_identity_rejected": True,
        "world_write_security_allowed": True,
        "executable_class_allowed": True,
        "candidate_0644_0664_hygiene_allowed": True,
        "git_100644_100755_class_allowed": True,
        "historical_reporting_mode_allowed": True,
        "legacy_mode_to_exec_class_only_allowed": True,
    }


def _verify_json_classifier_controls() -> dict[str, bool]:
    bad = (
        '{"path":"source.csv","byte_count":12,'
        '"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
        '"mode":"0644"}'
    )
    reporting = '{"historical_mode":"0600","purpose":"reporting_only"}'
    ambiguous = '{"path":"source.csv","expected_mode":"0644"}'
    historical_identity = (
        '{"path":"source.csv","byte_count":12,'
        '"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
        '"historical_mode":"0644"}'
    )
    bad_classes = _classes(
        subject._classify_json_text_v2(
            bad,
            source_path="data/derived/covalent_small/synthetic_bad.json",
        )
    )
    reporting_classes = _classes(
        subject._classify_json_text_v2(
            reporting,
            source_path="data/derived/covalent_small/synthetic_reporting.json",
        )
    )
    ambiguous_classes = _classes(
        subject._classify_json_text_v2(
            ambiguous,
            source_path="data/derived/covalent_small/synthetic_ambiguous.json",
        )
    )
    historical_identity_classes = _classes(
        subject._classify_json_text_v2(
            historical_identity,
            source_path=(
                "data/derived/covalent_small/synthetic_historical_identity.json"
            ),
        )
    )
    if SEMANTIC_SOURCE_IDENTITY not in bad_classes:
        raise ValueError("BAD_JSON_BINDING_NOT_REJECTED")
    if reporting_classes != {REPORTING_DIAGNOSTIC}:
        raise ValueError("REPORTING_JSON_MISCLASSIFIED")
    if AMBIGUOUS not in ambiguous_classes:
        raise ValueError("AMBIGUOUS_JSON_NOT_FAIL_CLOSED")
    if not historical_identity_classes & {SEMANTIC_SOURCE_IDENTITY, AMBIGUOUS}:
        raise ValueError("HISTORICAL_MODE_JSON_IDENTITY_COLLISION_ALLOWED")
    return {
        "bad_JSON_path_bytes_sha_mode_binding_rejected": True,
        "reporting_only_historical_mode_JSON_allowed": True,
        "ambiguous_JSON_binding_failed_closed": True,
        "historical_mode_JSON_identity_collision_failed_closed": True,
    }


def _verify_subject_behavior(root: Path) -> tuple[dict[str, object], int]:
    calls = 0
    original = subject.historical_v2.verify_covapie_source_binding_historical_immutability_proof_v2

    def counted(*, repo_root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return original(repo_root=repo_root)

    subject.historical_v2.verify_covapie_source_binding_historical_immutability_proof_v2 = counted
    try:
        result = subject.verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
            repo_root=root
        )
    finally:
        subject.historical_v2.verify_covapie_source_binding_historical_immutability_proof_v2 = original
    if calls != 1:
        raise ValueError("B3_PUBLIC_PROOF_CALL_COUNT_INVALID")
    required = {
        "future_guard_baseline_commit": BASELINE_HEAD,
        "future_guard_baseline_is_ancestor": True,
        "b3_historical_immutability_verified": True,
        "historical_exact_mode_occurrences_governed_by_b3": True,
        "historical_v1_rewrite_required": False,
        "historical_exact_mode_metadata_preserved": True,
        "historical_exact_mode_metadata_propagated_into_future_identity": False,
        "exact_numeric_posix_mode_semantic_identity_forbidden_for_future": True,
        "security_hygiene_mode_checks_allowed": True,
        "executable_class_checks_allowed": True,
        "git_file_class_checks_allowed": True,
        "candidate_artifact_hygiene_allowed": True,
        "historical_reporting_mode_metadata_allowed": True,
        "new_semantic_exact_posix_mode_occurrence_count": 0,
        "new_ambiguous_mode_occurrence_count": 0,
        "filesystem_source_acceptance_authority": "SOURCE_BINDING_POLICY_V2",
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "B4_PRODUCTION_SELF_SCAN_PASSED": True,
        "B4_CHECKER_SELF_SCAN_PASSED": True,
        "v2_migration_phase_b4_future_guard_active": True,
        "ready_to_close_source_binding_filesystem_mode_v2_migration": True,
        "ready_for_training": False,
        "known_legacy_v1_contains_forbidden_pattern": True,
        "unchanged_legacy_v1_not_counted_as_future_violation": True,
        "same_legacy_bytes_simulated_as_future_modification_detected": True,
    }
    if type(result) is not dict:
        raise ValueError("PUBLIC_RESULT_TYPE_INVALID")
    for key, expected in required.items():
        if result.get(key) != expected or type(result.get(key)) is not type(expected):
            raise ValueError("PUBLIC_RESULT_INVALID:" + key)
    scanned = set(result["future_guard_scanned_python_paths"])
    if not {PRODUCTION_RELATIVE, CHECKER_RELATIVE} <= scanned:
        raise ValueError("B4_SELF_SCAN_PATHS_MISSING")
    return result, calls


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = _verify_exact4_hygiene(root)
    _verify_baseline_history(root)
    _verify_frozen_dependencies(root)
    _verify_public_api_and_static_safety(root)
    python_controls = _verify_python_classifier_controls()
    json_controls = _verify_json_classifier_controls()
    public_result, b3_calls = _verify_subject_behavior(root)
    if lifecycle == "CANDIDATE_UNTRACKED":
        expected_counts = {
            "post_b3_tracked_changed_relevant_path_count": 0,
            "working_tree_modified_relevant_path_count": 0,
            "ordinary_untracked_relevant_path_count": 3,
            "future_guard_scanned_python_file_count": 3,
            "future_guard_scanned_json_file_count": 0,
            "future_guard_scanned_total_file_count": 3,
        }
    else:
        expected_counts = {
            "post_b3_tracked_changed_relevant_path_count": 3,
            "working_tree_modified_relevant_path_count": 0,
            "ordinary_untracked_relevant_path_count": 0,
            "future_guard_scanned_python_file_count": 3,
            "future_guard_scanned_json_file_count": 0,
            "future_guard_scanned_total_file_count": 3,
        }
    for key, expected in expected_counts.items():
        if public_result.get(key) != expected:
            raise ValueError("LIFECYCLE_SCAN_COUNT_INVALID:" + key)
    return {
        "lifecycle": lifecycle,
        "exact4": exact4,
        "b3_public_proof_call_count": b3_calls,
        **python_controls,
        **json_controls,
        **public_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v2(parser.parse_args().repo_root)
    required_true = (
        "future_guard_baseline_is_ancestor",
        "b3_historical_immutability_verified",
        "historical_exact_mode_occurrences_governed_by_b3",
        "historical_exact_mode_metadata_preserved",
        "exact_numeric_posix_mode_semantic_identity_forbidden_for_future",
        "security_hygiene_mode_checks_allowed",
        "executable_class_checks_allowed",
        "git_file_class_checks_allowed",
        "candidate_artifact_hygiene_allowed",
        "historical_reporting_mode_metadata_allowed",
        "B4_PRODUCTION_SELF_SCAN_PASSED",
        "B4_CHECKER_SELF_SCAN_PASSED",
        "known_legacy_v1_contains_forbidden_pattern",
        "unchanged_legacy_v1_not_counted_as_future_violation",
        "same_legacy_bytes_simulated_as_future_modification_detected",
        "B3_present",
        "v2_migration_phase_b4_future_guard_active",
        "ready_to_close_source_binding_filesystem_mode_v2_migration",
        "bad_S_IMODE_semantic_comparison_rejected",
        "bad_0o7777_semantic_comparison_rejected",
        "bad_JSON_path_bytes_sha_mode_binding_rejected",
        "alias_binding_mode_rejected",
        "transitive_alias_binding_mode_rejected",
        "unknown_full_mode_compare_failed_closed",
        "non_historical_exact_posix_mode_rejected",
        "candidate_source_identity_collision_rejected",
        "executable_name_only_collision_rejected",
        "historical_mode_live_identity_rejected",
        "historical_mode_JSON_identity_collision_failed_closed",
        "world_write_security_allowed",
        "executable_class_allowed",
        "candidate_0644_0664_hygiene_allowed",
        "git_100644_100755_class_allowed",
        "historical_reporting_mode_allowed",
    )
    if any(result.get(key) is not True for key in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    required_false = (
        "historical_v1_rewrite_required",
        "historical_exact_mode_metadata_propagated_into_future_identity",
        "sixth_task_present",
        "ready_for_training",
    )
    if any(result.get(key) is not False for key in required_false):
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    if (
        result["new_semantic_exact_posix_mode_occurrence_count"] != 0
        or result["new_ambiguous_mode_occurrence_count"] != 0
        or result["global_canonical_task_count"] != 5
    ):
        raise ValueError("CHECKER_ZERO_OR_EXACT5_ASSERTION_FAILED")
    print("PASS")
    for key in (
        "lifecycle",
        "future_guard_baseline_commit",
        "b3_historical_immutability_verified",
        "historical_exact_mode_occurrences_governed_by_b3",
        "B4_PRODUCTION_SELF_SCAN_PASSED",
        "B4_CHECKER_SELF_SCAN_PASSED",
        "alias_binding_mode_rejected",
        "transitive_alias_binding_mode_rejected",
        "unknown_full_mode_compare_failed_closed",
        "non_historical_exact_posix_mode_rejected",
        "candidate_source_identity_collision_rejected",
        "executable_name_only_collision_rejected",
        "historical_mode_live_identity_rejected",
        "historical_mode_JSON_identity_collision_failed_closed",
        "post_b3_tracked_changed_relevant_path_count",
        "working_tree_modified_relevant_path_count",
        "ordinary_untracked_relevant_path_count",
        "future_guard_scanned_python_file_count",
        "future_guard_scanned_json_file_count",
        "future_guard_scanned_total_file_count",
        "new_semantic_exact_posix_mode_occurrence_count",
        "new_ambiguous_mode_occurrence_count",
        "security_hygiene_occurrence_count",
        "executable_class_occurrence_count",
        "git_file_class_occurrence_count",
        "candidate_hygiene_occurrence_count",
        "reporting_diagnostic_occurrence_count",
        "test_only_occurrence_count",
        "exact_numeric_posix_mode_semantic_identity_forbidden_for_future",
        "security_hygiene_mode_checks_allowed",
        "executable_class_checks_allowed",
        "git_file_class_checks_allowed",
        "candidate_artifact_hygiene_allowed",
        "historical_reporting_mode_metadata_allowed",
        "global_canonical_task_count",
        "B3_present",
        "sixth_task_present",
        "v2_migration_phase_b4_future_guard_active",
        "ready_to_close_source_binding_filesystem_mode_v2_migration",
        "ready_for_training",
    ):
        value = result[key]
        if isinstance(value, bool):
            value = str(value).lower()
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
