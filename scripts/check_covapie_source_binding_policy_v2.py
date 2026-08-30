#!/usr/bin/env python3
"""Independent fail-closed checker for the common source-binding V2 policy."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_source_binding_policy_v2 as subject  # noqa: E402


BASELINE_HEAD = "26555ff6240ee53c817726331c8353dcb62dc82e"
BASELINE_TREE = "24280fbf73dd8785268b64889193b4735b8ca875"
BASELINE_SUBJECT = "add CovaPIE source binding filesystem mode authority v2 audit"

PRODUCTION_RELATIVE = "src/covalent_ext/covapie_source_binding_policy_v2.py"
CHECKER_RELATIVE = "scripts/check_covapie_source_binding_policy_v2.py"
TEST_RELATIVE = "tests/test_covapie_source_binding_policy_v2.py"
GUIDE_RELATIVE = "docs/covapie_source_binding_policy_v2_guide.md"
EXACT4_PATHS = (
    PRODUCTION_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    GUIDE_RELATIVE,
)

AUDIT_OWNER_RELATIVE = (
    "src/covalent_ext/"
    "covapie_source_binding_filesystem_mode_authority_v2_audit.py"
)
AUDIT_SUMMARY_RELATIVE = (
    "data/derived/covalent_small/"
    "covapie_source_binding_filesystem_mode_authority_v2_audit/"
    "covapie_source_binding_filesystem_mode_authority_v2_summary.json"
)
AUDIT_OWNER_SHA256 = (
    "bafa328adce5084acd840b1e86d2f44227d3a403c8d68f86bc823efce691d2e9"
)
AUDIT_SUMMARY_SHA256 = (
    "fe27c9e9aadbad76f8c330bf19286b840038cc0576b1a2de96fcd0546b5d10b0"
)

CURRENT_CENSUS_MANIFEST_RELATIVE = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1/"
    "covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json"
)
CURRENT_CENSUS_MANIFEST_SHA256 = (
    "c30f8f52fc20495a06f7bead98ac80197f434eeb0b4776a1ef2c152f13d1e2b7"
)
GOOD_BINDING_COUNT = 108
GOOD_BINDING_DIGEST = (
    "964f4b3747d42a43d05d1adc6f432264ce546ef93f9faace23fa3379452bfd15"
)
GOOD_BINDING_FIELDS = {
    "artifact_role",
    "path",
    "path_namespace",
    "byte_count",
    "sha256",
}

ACTIVE_CONSUMER_SHA256 = {
    "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "dadb213ad9232e7ecd0e7ae55849357ead00b67cfdac9f95f10b8293bce81468"
    ),
    "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "d057ff1695f9797fd2c54f9c91737fde6edd7580c471759350d179bb807565a7"
    ),
    "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "57d42fcf673794f27adc7b897c0f51db4304d32f2d35a950b89d63cf4cf7060d"
    ),
    "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "7a5561f1cb35465a2dbe6af8121f06a07b7aea6d82051e3945352cf1c669aff7"
    ),
    "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "c67c88f83e535fd4319425459b97dcfc22f90a3b617b5ddbf1e8f315e2de0525"
    ),
    "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "dee80c8ce26e0be030d3063e8ab9831c1bc0650c6a2dc9798c3c21007faae290"
    ),
    "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "abb80e28e1e139c3515a01c53468530a815c5554b94053afb607053d14a84deb"
    ),
    "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py": (
        "8339aaa2c57fe1637ab4e4feb7db964fc76224957687d2e0752e28ba3b093928"
    ),
}

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


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


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
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if mode not in {0o644, 0o664}:
            raise ValueError("EXACT4_LIVE_MODE_INVALID:" + relative)
        if mode & 0o111:
            raise ValueError("EXACT4_EXECUTABLE_FORBIDDEN:" + relative)
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


def _verify_public_api() -> None:
    expected = (
        "SourceBindingPolicyV2Error",
        "verify_content_identity_v2",
        "verify_source_security_v2",
        "verify_bound_source_v2",
    )
    if subject.__all__ != expected:
        raise ValueError("PUBLIC_API_INVENTORY_INVALID")
    if not issubclass(subject.SourceBindingPolicyV2Error, ValueError):
        raise ValueError("PUBLIC_ERROR_FAMILY_INVALID")
    expected_parameters = {
        "verify_content_identity_v2": (
            "path",
            "expected_byte_count",
            "expected_sha256",
            "label",
        ),
        "verify_source_security_v2": (
            "path",
            "label",
            "expected_executable",
        ),
        "verify_bound_source_v2": (
            "path",
            "expected_byte_count",
            "expected_sha256",
            "label",
            "expected_executable",
        ),
    }
    for name, names in expected_parameters.items():
        function = getattr(subject, name)
        parameters = tuple(inspect.signature(function).parameters.values())
        if tuple(parameter.name for parameter in parameters) != names:
            raise ValueError("PUBLIC_SIGNATURE_NAMES_INVALID:" + name)
        if any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in parameters
        ):
            raise ValueError("PUBLIC_SIGNATURE_NOT_KEYWORD_ONLY:" + name)
        hints = get_type_hints(function)
        if hints.get("path") is not Path or hints.get("label") is not str:
            raise ValueError("PUBLIC_SIGNATURE_TYPES_INVALID:" + name)
    if inspect.signature(subject.verify_source_security_v2).parameters[
        "expected_executable"
    ].default is not None:
        raise ValueError("SECURITY_EXECUTABLE_DEFAULT_INVALID")
    if inspect.signature(subject.verify_bound_source_v2).parameters[
        "expected_executable"
    ].default is not None:
        raise ValueError("BOUND_EXECUTABLE_DEFAULT_INVALID")
    if get_type_hints(subject.verify_content_identity_v2).get("return") is not bytes:
        raise ValueError("CONTENT_RETURN_TYPE_INVALID")
    if get_type_hints(subject.verify_bound_source_v2).get("return") is not bytes:
        raise ValueError("BOUND_RETURN_TYPE_INVALID")
    if get_type_hints(subject.verify_source_security_v2).get("return") is not type(None):
        raise ValueError("SECURITY_RETURN_TYPE_INVALID")


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    node = next(
        (
            item
            for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name == name
        ),
        None,
    )
    if node is None:
        raise ValueError("PRODUCTION_FUNCTION_MISSING:" + name)
    return node


def _attribute_name(node: ast.Attribute) -> str:
    parts = [node.attr]
    value = node.value
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return ".".join(reversed(parts))


def _verify_ast_separation(root: Path = ROOT) -> None:
    payload = _read_regular(root / PRODUCTION_RELATIVE, "PRODUCTION")
    text = payload.decode("utf-8")
    tree = ast.parse(text, filename=PRODUCTION_RELATIVE)
    content = _function_node(tree, "verify_content_identity_v2")
    security = _function_node(tree, "_inspect_source_security_v2")
    combined = _function_node(tree, "verify_bound_source_v2")

    content_text = ast.get_source_segment(text, content) or ""
    forbidden_text = ("stat.S_IMODE", "0o600", "0o644", "0o664", "0600", "0644", "0664")
    if any(token in content_text for token in forbidden_text):
        raise ValueError("CONTENT_HELPER_HAS_EXACT_MODE_AUTHORITY")
    content_attributes = {
        _attribute_name(node) for node in ast.walk(content) if isinstance(node, ast.Attribute)
    }
    if any(name.startswith("stat.") or name.endswith(".st_mode") for name in content_attributes):
        raise ValueError("CONTENT_HELPER_INSPECTS_FILESYSTEM_MODE")
    content_names = {node.id for node in ast.walk(content) if isinstance(node, ast.Name)}
    if {"_inspect_source_security_v2", "verify_source_security_v2"} & content_names:
        raise ValueError("CONTENT_HELPER_CALLS_SECURITY_GATE")

    security_attributes = {
        _attribute_name(node) for node in ast.walk(security) if isinstance(node, ast.Attribute)
    }
    required_security = {
        "path.lstat",
        "stat.S_ISLNK",
        "stat.S_ISREG",
        "stat.S_IRUSR",
        "stat.S_IWOTH",
    }
    if not required_security <= security_attributes:
        raise ValueError("SECURITY_HELPER_BITS_INCOMPLETE")
    security_names = {node.id for node in ast.walk(security) if isinstance(node, ast.Name)}
    if "hashlib" in security_names or "expected_sha256" in security_names:
        raise ValueError("SECURITY_HELPER_IMPLEMENTS_CONTENT_IDENTITY")

    combined_names = {node.id for node in ast.walk(combined) if isinstance(node, ast.Name)}
    if not {"_inspect_source_security_v2", "verify_content_identity_v2"} <= combined_names:
        raise ValueError("COMBINED_HELPER_DOES_NOT_COMPOSE_GATES")
    combined_attributes = {
        _attribute_name(node) for node in ast.walk(combined) if isinstance(node, ast.Attribute)
    }
    if not {"before.st_dev", "before.st_ino", "after.st_dev", "after.st_ino"} <= combined_attributes:
        raise ValueError("COMBINED_HELPER_STABILITY_CHECK_INCOMPLETE")

    mutable_nodes = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is not None and isinstance(value, mutable_nodes):
                raise ValueError("PRODUCTION_GLOBAL_MUTABLE_STATE_FORBIDDEN")
    if any(isinstance(node, ast.Global) for node in ast.walk(tree)):
        raise ValueError("PRODUCTION_GLOBAL_STATEMENT_FORBIDDEN")
    if "cache" in {node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)}:
        raise ValueError("PRODUCTION_CACHE_FORBIDDEN")


def _expect_policy_error(token: str, operation: object) -> None:
    try:
        operation()
    except subject.SourceBindingPolicyV2Error as error:
        if token not in str(error):
            raise ValueError("RUNTIME_PROBE_ERROR_TOKEN_INVALID:" + token) from error
    else:
        raise ValueError("RUNTIME_PROBE_DID_NOT_FAIL:" + token)


def _verify_runtime_probes() -> dict[str, object]:
    payload = b"covapie-v2-content-identity\n"
    digest = _sha(payload)
    mode_results: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="covapie-v2-policy-") as directory:
        root = Path(directory)
        source = root / "source.bin"
        source.write_bytes(payload)
        for mode in (0o600, 0o644, 0o660, 0o664):
            source.chmod(mode)
            if subject.verify_content_identity_v2(
                path=source,
                expected_byte_count=len(payload),
                expected_sha256=digest,
                label="MODE_REGRESSION",
            ) != payload:
                raise ValueError("CONTENT_MODE_REGRESSION_FAILED")
            if subject.verify_bound_source_v2(
                path=source,
                expected_byte_count=len(payload),
                expected_sha256=digest,
                label="MODE_REGRESSION",
                expected_executable=False,
            ) != payload:
                raise ValueError("BOUND_MODE_REGRESSION_FAILED")
            mode_results[f"{mode:04o}"] = True

        source.chmod(0o644)
        first = subject.verify_content_identity_v2(
            path=source,
            expected_byte_count=len(payload),
            expected_sha256=digest,
            label="CHECKOUT_MODE_CHANGE",
        )
        source.chmod(0o664)
        second = subject.verify_content_identity_v2(
            path=source,
            expected_byte_count=len(payload),
            expected_sha256=digest,
            label="CHECKOUT_MODE_CHANGE",
        )
        if first != second:
            raise ValueError("CHECKOUT_MODE_CHANGE_ALTERED_IDENTITY")

        source.chmod(0o666)
        _expect_policy_error(
            "SOURCE_WORLD_WRITABLE",
            lambda: subject.verify_source_security_v2(
                path=source,
                label="WORLD_WRITABLE",
            ),
        )
        source.chmod(0o755)
        _expect_policy_error(
            "SOURCE_EXECUTABLE_CLASS_MISMATCH",
            lambda: subject.verify_source_security_v2(
                path=source,
                label="UNEXPECTED_EXECUTABLE",
                expected_executable=False,
            ),
        )
        source.chmod(0o750)
        subject.verify_source_security_v2(
            path=source,
            label="EXPECTED_EXECUTABLE",
            expected_executable=True,
        )
        source.chmod(0o664)
        _expect_policy_error(
            "SOURCE_SHA256_MISMATCH",
            lambda: subject.verify_content_identity_v2(
                path=source,
                expected_byte_count=len(payload),
                expected_sha256="0" * 64,
                label="WRONG_SHA",
            ),
        )
        symlink = root / "source-link"
        symlink.symlink_to(source.name)
        _expect_policy_error(
            "SOURCE_SYMLINK_FORBIDDEN",
            lambda: subject.verify_source_security_v2(
                path=symlink,
                label="SYMLINK",
            ),
        )
    return {
        "mode_results": mode_results,
        "mode_0600_to_0664_identity_preserved": True,
        "mode_0644_to_0664_identity_preserved": True,
        "world_writable_rejected": True,
        "unexpected_executable_rejected": True,
    }


def _verify_phase_a_dependency(root: Path = ROOT) -> dict[str, object]:
    owner_payload = _read_regular(root / AUDIT_OWNER_RELATIVE, "AUDIT_OWNER")
    summary_payload = _read_regular(root / AUDIT_SUMMARY_RELATIVE, "AUDIT_SUMMARY")
    if _sha(owner_payload) != AUDIT_OWNER_SHA256:
        raise ValueError("AUDIT_OWNER_SHA256_DRIFT")
    if _sha(summary_payload) != AUDIT_SUMMARY_SHA256:
        raise ValueError("AUDIT_SUMMARY_SHA256_DRIFT")
    summary = json.loads(summary_payload)
    counts = summary.get("inventory_counts", {})
    historical = summary.get("historical_compatibility_policy", {})
    readiness = summary.get("readiness", {})
    if readiness.get("ready_for_v2_implementation") is not True:
        raise ValueError("AUDIT_NOT_READY_FOR_V2_IMPLEMENTATION")
    if summary.get("debt_disposition_counts", {}).get("V2_MIGRATION_REQUIRED") != 12:
        raise ValueError("AUDIT_MIGRATION_OCCURRENCES_INVALID")
    if counts.get("active_v2_migration_target_file_count") != 8:
        raise ValueError("AUDIT_ACTIVE_TARGET_COUNT_INVALID")
    if set(counts.get("active_v2_migration_target_files", [])) != set(
        ACTIVE_CONSUMER_SHA256
    ):
        raise ValueError("AUDIT_ACTIVE_TARGET_INVENTORY_INVALID")
    if historical.get("historical_validator_rewrite_required") is not False:
        raise ValueError("AUDIT_HISTORICAL_REWRITE_POLICY_INVALID")
    proposed = summary.get("proposed_v2_policy", {})
    security = summary.get("security_hygiene_policy", {})
    if proposed.get("exact_runtime_posix_mode_is_semantic_identity") is not False:
        raise ValueError("AUDIT_EXACT_MODE_POLICY_INVALID")
    if proposed.get("semantic_identity_and_security_hygiene_are_separate") is not True:
        raise ValueError("AUDIT_SEPARATION_POLICY_INVALID")
    if security.get("group_write_0664_automatically_forbidden") is not False:
        raise ValueError("AUDIT_GROUP_WRITE_POLICY_INVALID")
    return {
        "published": True,
        "migration_occurrences": 12,
        "active_target_files": 8,
        "historical_rewrite_required": False,
    }


def _verify_good_reference(root: Path = ROOT) -> dict[str, object]:
    payload = _read_regular(root / CURRENT_CENSUS_MANIFEST_RELATIVE, "CURRENT_CENSUS")
    if _sha(payload) != CURRENT_CENSUS_MANIFEST_SHA256:
        raise ValueError("CURRENT_CENSUS_MANIFEST_SHA256_DRIFT")
    document = json.loads(payload)
    bindings = document.get("semantic_source_bindings")
    if not isinstance(bindings, list) or len(bindings) != GOOD_BINDING_COUNT:
        raise ValueError("GOOD_REFERENCE_BINDING_COUNT_INVALID")
    if any(type(row) is not dict or set(row) != GOOD_BINDING_FIELDS for row in bindings):
        raise ValueError("GOOD_REFERENCE_BINDING_SCHEMA_INVALID")
    digest = _sha(_canonical_json(bindings).encode("utf-8"))
    if digest != GOOD_BINDING_DIGEST:
        raise ValueError("GOOD_REFERENCE_BINDING_DIGEST_INVALID")
    forbidden = {"mode", "posix_mode", "filesystem_mode", "st_mode"}
    mode_fields = sum(len(forbidden & set(row)) for row in bindings)
    if mode_fields:
        raise ValueError("GOOD_REFERENCE_HAS_EXACT_POSIX_MODE")
    return {"count": len(bindings), "digest": digest, "mode_fields": mode_fields}


def _verify_active_consumers_untouched(root: Path = ROOT) -> int:
    for relative, expected_sha in ACTIVE_CONSUMER_SHA256.items():
        payload = _read_regular(root / relative, "ACTIVE_CONSUMER:" + relative)
        if _sha(payload) != expected_sha:
            raise ValueError("ACTIVE_CONSUMER_SHA256_DRIFT:" + relative)
    return len(ACTIVE_CONSUMER_SHA256)


def _verify_repository_safety(profile: str, root: Path = ROOT) -> dict[str, int]:
    tracked = set(_git("ls-files", root=root).splitlines())
    staged = {
        line
        for line in _git("diff", "--cached", "--name-only", root=root).splitlines()
        if line
    }
    if staged:
        raise ValueError("STAGED_INDEX_NOT_EMPTY")
    baseline_changed: set[str] = set()
    if profile == "TRACKED_CLEAN":
        baseline_changed = {
            line
            for line in _git(
                "diff", "--name-only", BASELINE_HEAD + "..HEAD", root=root
            ).splitlines()
            if line
        }
    if baseline_changed - set(EXACT4_PATHS):
        raise ValueError("NON_EXACT4_TRACKED_SOURCE_MODIFIED")
    new_forbidden = {path for path in EXACT4_PATHS if path.endswith(FORBIDDEN_SUFFIXES)}
    if new_forbidden:
        raise ValueError("EXACT4_FORBIDDEN_TRACKED_FILE")
    raw_tracked = {path for path in tracked if path.startswith("data/raw/")}
    raw_staged = {path for path in staged if path.startswith("data/raw/")}
    protected_changes = {
        path
        for path in baseline_changed
        if path in {"lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"}
        or path.startswith("equivariant_diffusion/")
        or path.startswith("checkpoints/")
    }
    if protected_changes:
        raise ValueError("PROTECTED_SOURCE_MODIFIED")
    return {
        "raw_tracked_count": len(raw_tracked),
        "raw_staged_count": len(raw_staged),
        "new_forbidden_count": len(new_forbidden),
        "protected_source_change_count": len(protected_changes),
    }


def main() -> int:
    if _git("rev-parse", BASELINE_HEAD + "^{tree}") != BASELINE_TREE:
        raise ValueError("BASELINE_TREE_MISMATCH")
    if _git("show", "-s", "--format=%s", BASELINE_HEAD) != BASELINE_SUBJECT:
        raise ValueError("BASELINE_SUBJECT_MISMATCH")
    profile = verify_git_lifecycle(ROOT)
    exact4 = verify_exact4_file_hygiene(ROOT)
    _verify_public_api()
    _verify_ast_separation(ROOT)
    runtime = _verify_runtime_probes()
    audit = _verify_phase_a_dependency(ROOT)
    good = _verify_good_reference(ROOT)
    active_count = _verify_active_consumers_untouched(ROOT)
    safety = _verify_repository_safety(profile, ROOT)
    ready_for_b2 = bool(
        audit["published"]
        and audit["migration_occurrences"] == 12
        and audit["active_target_files"] == active_count == 8
        and audit["historical_rewrite_required"] is False
        and good["count"] == GOOD_BINDING_COUNT
        and all(runtime["mode_results"].values())
        and safety["new_forbidden_count"] == 0
        and safety["protected_source_change_count"] == 0
    )
    if not ready_for_b2:
        raise ValueError("READY_FOR_V2_B2_NOT_PROVEN")
    print("PASS")
    print("lifecycle=" + profile)
    print("exact4_count=" + str(len(exact4)))
    print("public_api_count=4")
    print("content_modes_pass=0600,0644,0660,0664")
    print("mode_0600_to_0664_identity_preserved=true")
    print("mode_0644_to_0664_identity_preserved=true")
    print("audit_published=true")
    print("v2_migration_occurrences=" + str(audit["migration_occurrences"]))
    print("active_target_files=" + str(audit["active_target_files"]))
    print("historical_rewrite_required=false")
    print("good_reference_count=" + str(good["count"]))
    print("good_reference_exact_posix_fields=" + str(good["mode_fields"]))
    print("good_reference_digest=" + str(good["digest"]))
    print("active_consumers_modified=0")
    print("raw_tracked_count=" + str(safety["raw_tracked_count"]))
    print("raw_staged_count=" + str(safety["raw_staged_count"]))
    print("new_forbidden_count=" + str(safety["new_forbidden_count"]))
    print("protected_source_change_count=" + str(safety["protected_source_change_count"]))
    print("ready_for_v2_b2=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
