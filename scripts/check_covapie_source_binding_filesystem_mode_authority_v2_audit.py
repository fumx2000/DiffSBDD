#!/usr/bin/env python3
"""Independent fail-closed checker for the filesystem-mode V2 Phase-A audit."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_source_binding_filesystem_mode_authority_v2_audit as subject  # noqa: E402


BASELINE_HEAD = "89a8cf17a235cdca9eecad275794a5a86be2e01d"
BASELINE_TREE = "1fade78157312f44ef27232953d958453837bfb1"
BASELINE_SUBJECT = "add CovaPIE global readiness census with 2A2 v1"
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
SEMANTIC_CLASSES = {
    "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE",
    "SECURITY_HYGIENE_MODE_CHECK",
    "CANDIDATE_ARTIFACT_MODE_HYGIENE",
    "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT",
    "REPORTING_OR_DIAGNOSTIC_MODE_METADATA",
    "AMBIGUOUS_REQUIRES_HUMAN_REVIEW",
}
LIFECYCLE_CLASSES = {
    "HISTORICAL_IMMUTABLE_V1",
    "ACTIVE_CURRENT_DEPENDENCY",
    "NEW_CURRENT_V2_REFERENCE",
    "TEST_ONLY",
    "DOCUMENTATION_ONLY",
}
DEBT_DISPOSITIONS = {
    "V2_MIGRATION_REQUIRED",
    "PRESERVE_AS_IS",
    "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE",
    "REVIEW_REQUIRED",
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


def _read(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_NON_SYMLINK:" + label)
    return path.read_bytes()


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
    tracked_exact7: set[str],
    ordinary_untracked: set[str],
    status_entries: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    expected = set(subject.EXACT7_PATHS)
    expected_untracked_status = tuple(f"?? {path}" for path in sorted(expected))
    if (
        not tracked_exact7
        and ordinary_untracked == expected
        and tuple(sorted(status_entries)) == expected_untracked_status
        and not working_diff
        and not cached_diff
    ):
        return "CANDIDATE_UNTRACKED"
    if (
        tracked_exact7 == expected
        and not ordinary_untracked
        and not status_entries
        and not working_diff
        and not cached_diff
    ):
        return "TRACKED_CLEAN"
    raise ValueError("GIT_LIFECYCLE_PROFILE_INVALID")


def _validate_repository_relation_v1(
    *,
    profile: str,
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    parent_shas: tuple[str, ...],
    changed_paths: set[str],
) -> None:
    expected = set(subject.EXACT7_PATHS)
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
    exact = set(subject.EXACT7_PATHS)
    tracked = set(
        line
        for line in _git("ls-files", "--", *sorted(exact), root=root).splitlines()
        if line
    )
    untracked = set(
        line
        for line in _git(
            "ls-files", "--others", "--exclude-standard", root=root
        ).splitlines()
        if line
    )
    status = tuple(
        line
        for line in _git(
            "status", "--porcelain=v1", "--untracked-files=all", root=root
        ).splitlines()
        if line
    )
    working = set(
        line for line in _git("diff", "--name-only", root=root).splitlines() if line
    )
    cached = set(
        line
        for line in _git("diff", "--cached", "--name-only", root=root).splitlines()
        if line
    )
    profile = classify_lifecycle_from_facts(
        tracked_exact7=tracked,
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
        changed_paths = set(
            line
            for line in _git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", root=root
            ).splitlines()
            if line
        )
    else:
        parent_shas = ()
        changed_paths = set()
    _validate_repository_relation_v1(
        profile=profile,
        head=head,
        origin_main=origin,
        ahead=ahead,
        behind=behind,
        parent_shas=parent_shas,
        changed_paths=changed_paths,
    )
    return profile


def verify_exact7_file_hygiene(root: Path = ROOT) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if not output.is_dir() or output.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_INVALID")
    if {entry.name for entry in output.iterdir()} != {
        subject.INVENTORY_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }:
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")
    result: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS:
        path = root / relative
        payload = _read(path, "EXACT7:" + relative)
        _validate_text(payload, relative)
        metadata = path.stat(follow_symlinks=False)
        mode = stat.S_IMODE(metadata.st_mode)
        if not stat.S_ISREG(metadata.st_mode) or mode not in {0o644, 0o664}:
            raise ValueError("EXACT7_MODE_OR_FILE_CLASS_INVALID:" + relative)
        if mode & 0o111:
            raise ValueError("EXACT7_EXECUTABLE_FORBIDDEN:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT7_FORBIDDEN_SUFFIX:" + relative)
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


def _parse_inventory(root: Path = ROOT) -> list[dict[str, str]]:
    payload = _read(
        root / subject.OUTPUT_DIRECTORY_RELATIVE / subject.INVENTORY_FILE,
        "INVENTORY",
    )
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != subject.INVENTORY_COLUMNS:
        raise ValueError("INVENTORY_HEADER_INVALID")
    rows = [dict(row) for row in reader]
    if not rows or any(tuple(row) != subject.INVENTORY_COLUMNS for row in rows):
        raise ValueError("INVENTORY_ROWS_INVALID")
    if len({row["occurrence_id"] for row in rows}) != len(rows):
        raise ValueError("INVENTORY_OCCURRENCE_IDS_NOT_UNIQUE")
    for row in rows:
        if row["semantic_class"] not in SEMANTIC_CLASSES:
            raise ValueError("SEMANTIC_CLASS_INVALID")
        if row["lifecycle_class"] not in LIFECYCLE_CLASSES:
            raise ValueError("LIFECYCLE_CLASS_INVALID")
        if row["debt_disposition"] not in DEBT_DISPOSITIONS:
            raise ValueError("DEBT_DISPOSITION_INVALID")
        if PurePosixPath(row["source_path"]).is_absolute() or ".." in PurePosixPath(
            row["source_path"]
        ).parts:
            raise ValueError("INVENTORY_PATH_ESCAPE")
        identity = "|".join(
            row[key]
            for key in (
                "source_scope",
                "source_path_namespace",
                "source_path",
                "line_start",
                "line_end",
                "ast_node_type",
                "matched_semantic_pattern",
                "expected_or_literal_mode",
                "evidence_note",
            )
        )
        expected_id = "FMV2-" + _sha(identity.encode("utf-8"))[:20].upper()
        if row["occurrence_id"] != expected_id:
            raise ValueError("OCCURRENCE_ID_NOT_DETERMINISTIC")
    ordering = [
        (
            row["source_path_namespace"],
            row["source_path"],
            int(row["line_start"]),
            int(row["line_end"]),
            row["occurrence_id"],
        )
        for row in rows
    ]
    if ordering != sorted(ordering):
        raise ValueError("INVENTORY_ORDER_NOT_DETERMINISTIC")
    return rows


def _reject_dynamic_or_absolute(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in {"timestamp", "hostname", "pid"}:
                raise ValueError("DYNAMIC_MANIFEST_FIELD:" + path + "." + str(key))
            if (
                "manifest" in lowered
                and "sha256" in lowered
                and "self" in lowered
                and isinstance(child, str)
                and len(child) == 64
                and all(character in "0123456789abcdef" for character in child)
            ):
                raise ValueError("MANIFEST_SELF_SHA_FIELD:" + path + "." + str(key))
            _reject_dynamic_or_absolute(child, path + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_dynamic_or_absolute(child, f"{path}[{index}]")
    elif isinstance(value, str) and value.startswith("/"):
        raise ValueError("ABSOLUTE_PATH_IN_MANIFEST:" + path)


def _resolve_binding(root: Path, record: dict[str, object]) -> Path:
    relative = PurePosixPath(str(record["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("MANIFEST_BINDING_PATH_ESCAPE")
    if record["path_namespace"] == "repository_relative":
        return root / Path(relative.as_posix())
    if record["path_namespace"] == "repository_parent_relative":
        return root.parent / Path(relative.as_posix())
    raise ValueError("MANIFEST_BINDING_NAMESPACE_INVALID")


def _verify_binding_record(root: Path, record: dict[str, object]) -> None:
    if set(record) != GOOD_BINDING_FIELDS:
        raise ValueError("SEMANTIC_BINDING_SCHEMA_INVALID")
    path = _resolve_binding(root, record)
    payload = _read(path, str(record["artifact_role"]))
    if len(payload) != record["byte_count"] or _sha(payload) != record["sha256"]:
        raise ValueError("SEMANTIC_BINDING_CONTENT_DRIFT:" + str(record["path"]))


def _verify_good_reference(root: Path = ROOT) -> dict[str, object]:
    path = root / subject.CURRENT_CENSUS_MANIFEST_RELATIVE
    document = json.loads(_read(path, "CURRENT_CENSUS_MANIFEST"))
    bindings = document.get("semantic_source_bindings")
    if not isinstance(bindings, list) or len(bindings) != GOOD_BINDING_COUNT:
        raise ValueError("GOOD_REFERENCE_BINDING_COUNT_INVALID")
    if any(type(row) is not dict or set(row) != GOOD_BINDING_FIELDS for row in bindings):
        raise ValueError("GOOD_REFERENCE_BINDING_SCHEMA_INVALID")
    digest = _sha(_canonical_json(bindings).encode("utf-8"))
    if digest != GOOD_BINDING_DIGEST:
        raise ValueError("GOOD_REFERENCE_DIGEST_INVALID")
    forbidden = {"mode", "posix_mode", "filesystem_mode", "st_mode"}
    if any(forbidden & set(row) for row in bindings):
        raise ValueError("GOOD_REFERENCE_PROPAGATES_EXACT_POSIX_MODE")
    return {"count": len(bindings), "digest": digest, "mode_fields": 0}


def _verify_known_regression(
    rows: list[dict[str, str]], summary: dict[str, object], root: Path = ROOT
) -> None:
    validator = root.parent / subject.TWO_A2_FORMAL_VALIDATOR_RELATIVE
    text = _read(validator, "TWO_A2_FORMAL_VALIDATOR").decode("utf-8")
    for token in (
        "stat.S_IMODE(path.stat().st_mode)",
        "mode != expected_mode",
        "len(payload) != byte_count",
        "sha256(payload) != digest",
        "SOURCE_DRIFT",
        'role, "0644"',
        '"published_1f8_event_task_label_availability"',
        '"0600"',
    ):
        if token not in text:
            raise ValueError("KNOWN_REGRESSION_STATIC_TOKEN_MISSING:" + token)
    cases = summary.get("known_regression_cases")
    if not isinstance(cases, list) or len(cases) != 3:
        raise ValueError("KNOWN_REGRESSION_NOT_EXACT3")
    actual = {
        (case["source_role"], case["path"], case["expected_mode"])
        for case in cases
    }
    expected = set(subject.KNOWN_REGRESSION_EXPECTATIONS)
    if actual != expected:
        raise ValueError("KNOWN_REGRESSION_CASES_INVALID")
    external_exact = [
        row
        for row in rows
        if row["source_path"] == subject.TWO_A2_FORMAL_VALIDATOR_RELATIVE.as_posix()
        and row["semantic_class"]
        == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
    ]
    if not external_exact:
        raise ValueError("TWO_A2_FORMAL_VALIDATOR_NOT_CLASSIFIED_AS_EXACT_MODE_DEBT")
    if any(
        case["content_identity_contract"] != ["byte_count", "sha256"]
        or case["lifecycle_class"] != "HISTORICAL_IMMUTABLE_V1"
        or case["debt_disposition"]
        != "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE"
        for case in cases
    ):
        raise ValueError("KNOWN_REGRESSION_CLASSIFICATION_INVALID")


def verify_materialized_audit(root: Path = ROOT) -> dict[str, object]:
    rows = _parse_inventory(root)
    summary_path = root / subject.OUTPUT_DIRECTORY_RELATIVE / subject.SUMMARY_FILE
    manifest_path = root / subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE
    summary = json.loads(_read(summary_path, "SUMMARY"))
    manifest = json.loads(_read(manifest_path, "MANIFEST"))
    _reject_dynamic_or_absolute(manifest)

    semantic_counts = Counter(row["semantic_class"] for row in rows)
    lifecycle_counts = Counter(row["lifecycle_class"] for row in rows)
    disposition_counts = Counter(row["debt_disposition"] for row in rows)
    if summary["semantic_class_counts"] != {
        name: semantic_counts.get(name, 0) for name in subject.SEMANTIC_CLASSES
    }:
        raise ValueError("SUMMARY_SEMANTIC_COUNTS_NOT_DERIVED")
    if summary["lifecycle_class_counts"] != {
        name: lifecycle_counts.get(name, 0) for name in subject.LIFECYCLE_CLASSES
    }:
        raise ValueError("SUMMARY_LIFECYCLE_COUNTS_NOT_DERIVED")
    if summary["debt_disposition_counts"] != {
        name: disposition_counts.get(name, 0) for name in subject.DEBT_DISPOSITIONS
    }:
        raise ValueError("SUMMARY_DISPOSITION_COUNTS_NOT_DERIVED")
    if summary["inventory_counts"]["total_relevant_mode_occurrences"] != len(rows):
        raise ValueError("SUMMARY_TOTAL_NOT_DERIVED")

    scanned = manifest.get("scanned_source_bindings")
    current = manifest.get("current_good_reference_bindings")
    outputs = manifest.get("output_bindings_excluding_manifest_self")
    if not all(isinstance(group, list) for group in (scanned, current, outputs)):
        raise ValueError("MANIFEST_BINDING_GROUP_INVALID")
    if len(scanned) != manifest["scan_scope_counts"]["total_files_scanned"]:
        raise ValueError("MANIFEST_SCANNED_BINDING_COUNT_INVALID")
    for record in (*scanned, *current, *outputs):
        if type(record) is not dict:
            raise ValueError("MANIFEST_BINDING_NOT_OBJECT")
        _verify_binding_record(root, record)
        if {"mode", "posix_mode", "filesystem_mode", "st_mode"} & set(record):
            raise ValueError("NEW_MANIFEST_SEMANTIC_BINDING_HAS_POSIX_MODE")
    if manifest["semantic_binding_policy"] != {
        "allowed_fields": list(subject.CURRENT_CENSUS_BINDING_FIELDS),
        "exact_posix_mode_field_present": False,
        "manifest_self_sha256_recorded": False,
    }:
        raise ValueError("MANIFEST_SEMANTIC_POLICY_INVALID")

    expected_repository = {
        path
        for path in _git("ls-tree", "-r", "--name-only", BASELINE_HEAD, root=root).splitlines()
        if path.endswith(".py")
        and (
            path.startswith("src/covalent_ext/")
            or path.startswith("scripts/check_covapie")
            or path.startswith("tests/test_covapie")
        )
    }
    actual_repository = {
        str(record["path"])
        for record in scanned
        if record["artifact_role"].startswith("SCANNED_REPOSITORY_")
    }
    if actual_repository != expected_repository:
        raise ValueError("REPOSITORY_SCAN_SCOPE_INCOMPLETE")
    expected_derived = {
        path
        for path in _git("ls-tree", "-r", "--name-only", BASELINE_HEAD, root=root).splitlines()
        if path.startswith("data/derived/covalent_small/") and path.endswith(".json")
    }
    actual_derived = {
        str(record["path"])
        for record in scanned
        if record["artifact_role"] == "SCANNED_DERIVED_JSON"
    }
    if actual_derived != expected_derived:
        raise ValueError("DERIVED_JSON_SCAN_SCOPE_INCOMPLETE")

    good = _verify_good_reference(root)
    recorded_good = summary["current_good_reference"]
    if (
        recorded_good["semantic_binding_count"] != good["count"]
        or recorded_good["canonical_digest"] != good["digest"]
        or recorded_good["exact_posix_mode_field_count"] != 0
        or recorded_good[
            "CURRENT_2A2_CENSUS_PROPAGATES_EXACT_POSIX_MODE_AUTHORITY"
        ]
        is not False
    ):
        raise ValueError("SUMMARY_GOOD_REFERENCE_INVALID")
    _verify_known_regression(rows, summary, root)

    readiness = summary["readiness"]
    directly_ready = bool(
        disposition_counts["V2_MIGRATION_REQUIRED"]
        and len(summary["known_regression_cases"]) == 3
        and good["count"] == GOOD_BINDING_COUNT
    )
    if readiness != {
        "audit_scope_complete": True,
        "known_2a2_mode_regression_reproduced_by_static_contract": True,
        "current_2a2_census_negative_control_pass": True,
        "historical_authority_modification_required": False,
        "ready_for_v2_implementation": directly_ready,
    }:
        raise ValueError("READINESS_NOT_DIRECTLY_DERIVED")
    if manifest["authority_boundary"]["historical_authority_modified"] is not False:
        raise ValueError("HISTORICAL_MODIFICATION_CLAIM_INVALID")
    if manifest["authority_boundary"]["external_covapie_state_modified"] is not False:
        raise ValueError("EXTERNAL_MODIFICATION_CLAIM_INVALID")

    rebuilt = subject.build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
        root
    )
    for filename, payload in rebuilt.items():
        if _read(root / subject.OUTPUT_DIRECTORY_RELATIVE / filename, filename) != payload:
            raise ValueError("MATERIALIZED_ARTIFACT_NOT_DETERMINISTIC:" + filename)
    return {
        "inventory_rows": len(rows),
        "semantic_counts": dict(semantic_counts),
        "disposition_counts": dict(disposition_counts),
        "ready_for_v2_implementation": directly_ready,
        "good_reference": good,
    }


def _verify_repository_safety(profile: str, root: Path = ROOT) -> dict[str, int]:
    tracked = set(_git("ls-files", root=root).splitlines())
    staged = set(
        line
        for line in _git("diff", "--cached", "--name-only", root=root).splitlines()
        if line
    )
    if staged:
        raise ValueError("STAGED_INDEX_NOT_EMPTY")
    baseline_changed = set()
    if profile == "TRACKED_CLEAN":
        baseline_changed = set(
            _git("diff", "--name-only", BASELINE_HEAD + "..HEAD", root=root).splitlines()
        )
    if baseline_changed - set(subject.EXACT7_PATHS):
        raise ValueError("EXISTING_TRACKED_SOURCE_MODIFIED")
    forbidden = {path for path in tracked if path.endswith(FORBIDDEN_SUFFIXES)}
    new_forbidden = forbidden & set(subject.EXACT7_PATHS)
    if new_forbidden:
        raise ValueError("EXACT7_FORBIDDEN_TRACKED_FILE")
    raw_tracked = {path for path in tracked if path.startswith("data/raw/")}
    raw_staged = {path for path in staged if path.startswith("data/raw/")}
    protected = {
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    }
    if any(
        path in {"lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"}
        or path.startswith("equivariant_diffusion/")
        for path in baseline_changed
    ):
        raise ValueError("PROTECTED_SOURCE_MODIFIED")
    return {
        "raw_tracked_count": len(raw_tracked),
        "raw_staged_count": len(raw_staged),
        "new_forbidden_count": len(new_forbidden),
        "protected_source_change_count": 0,
    }


def main() -> int:
    if _git("rev-parse", BASELINE_HEAD + "^{tree}") != BASELINE_TREE:
        raise ValueError("BASELINE_TREE_MISMATCH")
    if _git("show", "-s", "--format=%s", BASELINE_HEAD) != BASELINE_SUBJECT:
        raise ValueError("BASELINE_SUBJECT_MISMATCH")
    profile = verify_git_lifecycle(ROOT)
    exact7 = verify_exact7_file_hygiene(ROOT)
    audit = verify_materialized_audit(ROOT)
    safety = _verify_repository_safety(profile, ROOT)
    print("PASS")
    print("lifecycle=" + profile)
    print("exact7_count=" + str(len(exact7)))
    print("inventory_rows=" + str(audit["inventory_rows"]))
    print(
        "exact_posix_semantic_debt="
        + str(
            audit["semantic_counts"].get(
                "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE", 0
            )
        )
    )
    print("good_reference_count=" + str(audit["good_reference"]["count"]))
    print("good_reference_digest=" + str(audit["good_reference"]["digest"]))
    print(
        "ready_for_v2_implementation="
        + str(audit["ready_for_v2_implementation"]).lower()
    )
    print("raw_tracked_count=" + str(safety["raw_tracked_count"]))
    print("raw_staged_count=" + str(safety["raw_staged_count"]))
    print("new_forbidden_count=" + str(safety["new_forbidden_count"]))
    print(
        "protected_source_change_count="
        + str(safety["protected_source_change_count"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
