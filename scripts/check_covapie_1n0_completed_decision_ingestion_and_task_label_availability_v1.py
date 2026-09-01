#!/usr/bin/env python3
"""Fail-closed checker for the 1N0 completed-decision ingestion Exact7."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)
from covalent_ext import (  # noqa: E402
    covapie_source_binding_future_exact_posix_mode_guard_v2 as b4_guard,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


ERROR = "COVAPIE_1N0_INGESTION_CHECK_FAILED"
BASELINE_HEAD = "27404b915ca74c1c3196c2dee7ce35f1d0d7ba96"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part", ".log",
)
PROTECTED_PREFIXES = (
    "data/raw/", "checkpoints/", "equivariant_diffusion/", "covapie-state/",
)
PROTECTED_FILES = {
    "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
}


def fail(reason: str) -> None:
    raise SystemExit(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run_git(*arguments: str) -> str:
    allowed = {
        "diff", "ls-files", "merge-base", "rev-list", "rev-parse", "status",
    }
    if not arguments or arguments[0] not in allowed:
        fail("GIT_SUBCOMMAND_FORBIDDEN")
    result = subprocess.run(
        ("git", *arguments),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + arguments[0])
    return result.stdout.rstrip("\n")


def check_text_file(relative: str) -> dict[str, object]:
    path = REPO_ROOT / relative
    try:
        payload = path.read_bytes()
    except OSError:
        fail("CANDIDATE_READ_FAILED:" + relative)
    if (
        not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        fail("TEXT_HYGIENE_INVALID:" + relative)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        fail("UTF8_INVALID:" + relative)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        fail("TRAILING_WHITESPACE:" + relative)
    digest = sha256(payload)
    try:
        verified = verify_bound_source_v2(
            path=path,
            expected_byte_count=len(payload),
            expected_sha256=digest,
            label="ONE_N0_EXACT7:" + relative,
            expected_executable=False,
        )
    except SourceBindingPolicyV2Error:
        fail("CANDIDATE_SECURITY_OR_EXECUTABLE_CLASS_INVALID:" + relative)
    if verified != payload:
        fail("CANDIDATE_UNSTABLE:" + relative)
    return {
        "path": relative,
        "byte_count": len(payload),
        "SHA256": digest,
        "executable_class": "NON_EXECUTABLE",
    }


def classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    expected = set(expected_paths)
    if len(expected_paths) != 7 or len(expected) != 7:
        fail("EXPECTED_INVENTORY_NOT_EXACT7")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        fail("MIXED_TRACKING_STATE")
    if working_diff:
        fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        fail("STAGED_INDEX_CHANGE_PRESENT")
    if len(status_lines) != len(set(status_lines)):
        fail("DUPLICATE_STATUS_ENTRY")
    if not tracked_candidate:
        if ordinary_untracked != expected:
            fail("ORDINARY_UNTRACKED_NOT_STRICT_EXACT7")
        if set(status_lines) != {"?? " + path for path in expected}:
            fail("CANDIDATE_STATUS_NOT_STRICT_EXACT7")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        fail("TRACKED_CLEAN_STATE_DIRTY")
    return TRACKED_CLEAN


def validate_relation_values(
    *,
    profile: str,
    head: str,
    parent: str | None,
    origin_main: str,
    ahead: int,
    behind: int,
    changed_paths: set[str],
    expected_paths: set[str],
) -> None:
    if profile == CANDIDATE_UNTRACKED:
        if not (
            head == BASELINE_HEAD
            and origin_main == BASELINE_HEAD
            and (ahead, behind) == (0, 0)
            and not changed_paths
        ):
            fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        fail("REPOSITORY_PROFILE_INVALID")
    if parent != BASELINE_HEAD or changed_paths != expected_paths:
        fail("TRACKED_CLEAN_DIRECT_SUCCESSOR_SCOPE_INVALID")
    if not (
        (origin_main == BASELINE_HEAD and (ahead, behind) == (1, 0))
        or (origin_main == head and (ahead, behind) == (0, 0))
    ):
        fail("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")


def verify_repository_relation(profile: str, expected_paths: set[str]) -> None:
    head = run_git("rev-parse", "HEAD")
    origin_main = run_git("rev-parse", "origin/main")
    relation = run_git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    if len(relation) != 2 or any(not item.isdigit() for item in relation):
        fail("REPOSITORY_RELATION_INVALID")
    ahead, behind = (int(item) for item in relation)
    if profile == CANDIDATE_UNTRACKED:
        changed: set[str] = set()
        parent = None
    else:
        run_git("merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD")
        commit_count = run_git("rev-list", "--count", BASELINE_HEAD + "..HEAD")
        if commit_count != "1":
            fail("TRACKED_CLEAN_COMMIT_COUNT_NOT_ONE")
        parent = run_git("rev-parse", "HEAD^")
        changed = set(
            filter(
                None,
                run_git("diff", "--name-only", BASELINE_HEAD + "..HEAD").splitlines(),
            )
        )
    validate_relation_values(
        profile=profile,
        head=head,
        parent=parent,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        changed_paths=changed,
        expected_paths=expected_paths,
    )


def observed_candidate_paths() -> set[str]:
    paths = [
        *(REPO_ROOT / "src/covalent_ext").glob("covapie_1n0_*"),
        *(REPO_ROOT / "scripts").glob("check_covapie_1n0_*"),
        *(REPO_ROOT / "tests").glob("test_covapie_1n0_*"),
    ]
    output_root = REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE
    if output_root.is_dir() and not output_root.is_symlink():
        paths.extend(output_root.iterdir())
    return {path.relative_to(REPO_ROOT).as_posix() for path in paths}


def check_candidate_inventory() -> tuple[list[dict[str, object]], str]:
    expected = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    expected_set = set(expected)
    if observed_candidate_paths() != expected_set:
        fail("ONE_N0_CANDIDATE_FILESET_NOT_EXACT7")
    tracked = set(filter(None, run_git("ls-files").splitlines()))
    ordinary_untracked = set(
        filter(
            None,
            run_git("ls-files", "--others", "--exclude-standard").splitlines(),
        )
    )
    status_lines = tuple(
        filter(
            None,
            run_git("status", "--short", "--untracked-files=all").splitlines(),
        )
    )
    working_diff = set(filter(None, run_git("diff", "--name-only").splitlines()))
    cached_diff = set(
        filter(None, run_git("diff", "--cached", "--name-only").splitlines())
    )
    profile = classify_repository_profile(
        expected_paths=expected,
        tracked_paths=tracked,
        ordinary_untracked=ordinary_untracked,
        status_lines=status_lines,
        working_diff=working_diff,
        cached_diff=cached_diff,
    )
    verify_repository_relation(profile, expected_set)
    if any(Path(path).suffix.lower() in FORBIDDEN_SUFFIXES for path in expected):
        fail("FORBIDDEN_CANDIDATE_SUFFIX")
    if any(
        path in PROTECTED_FILES
        or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
        for path in expected
    ):
        fail("PROTECTED_CANDIDATE_PATH")
    if any(
        token in path
        for path in expected
        for token in ("reconciliation", "census", "queue")
    ):
        fail("FORBIDDEN_ADJACENT_ARTIFACT_IN_CANDIDATE")
    return [check_text_file(path) for path in expected], profile


def binding_path(record: dict[str, object]) -> Path:
    relative = Path(str(record["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        fail("BOUND_PATH_INVALID")
    namespace = record["namespace"]
    if namespace == "repository_relative":
        return REPO_ROOT / relative
    if namespace == "project_parent_relative":
        return REPO_ROOT.parent / relative
    fail("BOUND_NAMESPACE_INVALID")


def verify_binding_records(records: object, expected_count: int) -> None:
    if type(records) is not list or len(records) != expected_count:
        fail("BOUND_RECORD_COUNT_INVALID")
    fields = {
        "path", "namespace", "byte_count", "SHA256",
        "expected_executable_class", "source_role",
    }
    for record in records:
        if type(record) is not dict or set(record) != fields:
            fail("BOUND_RECORD_SHAPE_INVALID")
        if record["expected_executable_class"] != "NON_EXECUTABLE":
            fail("BOUND_EXECUTABLE_CLASS_INVALID")
        try:
            verify_bound_source_v2(
                path=binding_path(record),
                expected_byte_count=int(record["byte_count"]),
                expected_sha256=str(record["SHA256"]),
                label="ONE_N0_CHECKER_BOUND_SOURCE:" + str(record["source_role"]),
                expected_executable=False,
            )
        except (SourceBindingPolicyV2Error, ValueError):
            fail("BOUND_SOURCE_VERIFICATION_FAILED:" + str(record["source_role"]))


def check_formal_validator_lifecycle() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=owner.SOURCE_RELATIVE.as_posix())
    forbidden_imports = {"subprocess", "runpy", "importlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in forbidden_imports for alias in node.names):
                fail("PRODUCTION_FORBIDDEN_IMPORT")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in forbidden_imports:
                fail("PRODUCTION_FORBIDDEN_IMPORT_FROM")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {
                "exec", "eval", "compile", "__import__",
            }:
                fail("PRODUCTION_DYNAMIC_EXECUTION_CALL")
    forbidden_hooks = (
        "execute_formal_validator", "_run_formal_validator",
        "subprocess_formal_validator",
    )
    if any(token in source for token in forbidden_hooks):
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTION_HOOK")


def check_independent_semantics(artifacts: dict[str, bytes]) -> None:
    snapshot = json.loads(artifacts[owner.SNAPSHOT])
    summary = json.loads(artifacts[owner.SUMMARY])
    manifest = json.loads(artifacts[owner.MANIFEST])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8")))
    )
    if len(rows) != 4 or tuple(int(row["scaleup_rank"]) for row in rows) != owner.EXPECTED_RANKS:
        fail("MATRIX_EXACT4_INVALID")
    if any(int(row["scaleup_rank"]) in owner.EXCLUDED_C2_RANKS for row in rows):
        fail("MATRIX_C2_EVENT_LEAKAGE")
    for row in rows:
        vector = json.loads(row["canonical_task_authority_availability_json"])
        if (
            row["human_task_relevance_decision"] != "NOT_RELEVANT"
            or row["task_relevance_human_authoritative"] != "true"
            or row["chemistry_disposition"] != "NOT_ESTABLISHED"
            or row["training_disposition"] != "NOT_APPLICABLE"
            or row["human_training_excluded"] != "false"
            or row["raw_structural_reactive_pair_evidence"] != "true"
            or row["reactive_pair_human_authoritative"] != "false"
            or row["role_partition_human_authoritative"] != "false"
            or any(row[field] != "null" for field in (
                "selected_role_candidate_index_0based", "role_profile",
                "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
                "boundary_bonds_json", "sample_authoritative_applicable_task_ids_json",
            ))
            or len(vector) != 5
            or any(item["authoritative_label_available"] is not False for item in vector)
            or vector[3]["semantic_long_name"] != "scaffold_only"
            or row["POST_source_evidence_available"] != "true"
            or row["POST_geometry_training_authority_available"] != "false"
            or row["PRE_geometry_authority_available"] != "false"
            or row["training_use_include"] != "false"
            or row["future_training_admission_candidate"] != "false"
            or row["authority_created_by_this_ingestion"] != "false"
        ):
            fail("MATRIX_NEGATIVE_AUTHORITY_BOUNDARY_INVALID")
    human = snapshot["human_decision"]
    if (
        human["approved"] is not True
        or human["approved_is_chemistry_approval"] is not False
        or human["D1_task_relevance"] != "NOT_RELEVANT"
        or [human[key] for key in (
            "D2_chemistry", "D3_reactive_pair", "D4_role_candidate", "D5_training_use"
        )] != ["UNRESOLVED"] * 4
        or len(human["D6_scientific_context"].encode("utf-8")) != 657
        or sha256(human["D6_scientific_context"].encode("utf-8"))
        != "d51bd3139a9ad85d285ce81e26caf4e6c9b45e447f8e3f90e6c6612d14c7d689"
    ):
        fail("SNAPSHOT_HUMAN_DECISION_INVALID")
    facts = snapshot["normalized_completed_negative_facts"]
    if len(facts) != 4 or any(
        {
            key: fact[key]
            for key in owner.GENERIC_PROJECTION
        } != owner.GENERIC_PROJECTION
        for fact in facts
    ):
        fail("GENERIC_COMPLETED_NEGATIVE_PROJECTION_INVALID")
    required_summary = {
        "event_count": 4,
        "task_domain_negative": True,
        "completed_negative_event_count": 4,
        "task_relevance_authority_event_count": 4,
        "chemistry_positive_authority_count": 0,
        "chemistry_negative_authority_count": 0,
        "reactive_pair_human_authority_count": 0,
        "role_partition_human_authority_count": 0,
        "canonical_mask_label_authority_count": 0,
        "training_include_count": 0,
        "future_training_candidate_count": 0,
        "POST_source_evidence_count": 4,
        "raw_evidence_preserved": True,
        "raw_evidence_promoted_to_human_authority": False,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "ready_for_training": False,
    }
    if any(summary.get(key) != value for key, value in required_summary.items()):
        fail("SUMMARY_NEGATIVE_COUNTS_INVALID")
    if (
        manifest.get("candidate_file_count") != 7
        or manifest.get("output_file_count") != 4
        or manifest.get("active_source_binding_count") != 9
        or manifest.get("source_binding_V2_clean_from_birth") is not True
        or manifest.get("numeric_POSIX_semantic_identity") is not False
        or manifest.get("formal_validator_runtime_dependency") is not False
        or manifest.get("ready_for_training") is not False
    ):
        fail("MANIFEST_BOUNDARY_INVALID")
    verify_binding_records(manifest["active_source_bindings"], 9)


def check_determinism(live: dict[str, bytes]) -> None:
    first = owner.build_artifacts_v1(REPO_ROOT)
    second = owner.build_artifacts_v1(REPO_ROOT)
    if live != first or first != second:
        fail("DETERMINISTIC_DOUBLE_BUILD_FAILED")
    with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
        first_root = Path(first_dir)
        second_root = Path(second_dir)
        first_written = owner.materialize_artifacts_v1(REPO_ROOT, output_root=first_root)
        second_written = owner.materialize_artifacts_v1(REPO_ROOT, output_root=second_root)
        for name in owner.OUTPUT_FILENAMES:
            if not (
                live[name]
                == first_written[name]
                == second_written[name]
                == (first_root / name).read_bytes()
                == (second_root / name).read_bytes()
            ):
                fail("TEMP_MATERIALIZATION_DRIFT:" + name)


def check_prewrite_boundary() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as temporary_dir:
        base = Path(temporary_dir)

        real = base / "real"
        real.mkdir()
        link = base / "root_link"
        link.symlink_to(real, target_is_directory=True)
        try:
            owner.materialize_artifacts_v1(REPO_ROOT, output_root=link)
        except owner.OneN0IngestionSafetyError:
            pass
        else:
            fail("ROOT_SYMLINK_ACCEPTED")
        if tuple(real.iterdir()):
            fail("ROOT_SYMLINK_TARGET_MODIFIED")

        unexpected = base / "unexpected"
        unexpected.mkdir()
        sentinel = unexpected / "sentinel.txt"
        sentinel.write_bytes(b"sentinel\n")
        try:
            owner.materialize_artifacts_v1(REPO_ROOT, output_root=unexpected)
        except owner.OneN0IngestionSafetyError:
            pass
        else:
            fail("UNEXPECTED_ENTRY_ACCEPTED")
        if {entry.name for entry in unexpected.iterdir()} != {"sentinel.txt"}:
            fail("UNEXPECTED_ENTRY_DIRECTORY_MODIFIED")

        allowed_link_root = base / "allowed_link"
        allowed_link_root.mkdir()
        target = base / "link_target"
        target.write_bytes(b"target\n")
        (allowed_link_root / owner.SNAPSHOT).symlink_to(target)
        try:
            owner.materialize_artifacts_v1(REPO_ROOT, output_root=allowed_link_root)
        except owner.OneN0IngestionSafetyError:
            pass
        else:
            fail("ALLOWED_OUTPUT_SYMLINK_ACCEPTED")
        if target.read_bytes() != b"target\n":
            fail("ALLOWED_OUTPUT_SYMLINK_TARGET_MODIFIED")

        nonregular_root = base / "nonregular"
        nonregular_root.mkdir()
        (nonregular_root / owner.MATRIX).mkdir()
        try:
            owner.materialize_artifacts_v1(REPO_ROOT, output_root=nonregular_root)
        except owner.OneN0IngestionSafetyError:
            pass
        else:
            fail("ALLOWED_OUTPUT_NONREGULAR_ACCEPTED")
        if {entry.name for entry in nonregular_root.iterdir()} != {owner.MATRIX}:
            fail("ALLOWED_OUTPUT_NONREGULAR_DIRECTORY_MODIFIED")

        partial = base / "partial"
        partial.mkdir()
        (partial / owner.SUMMARY).write_bytes(b"old\n")
        first = owner.materialize_artifacts_v1(REPO_ROOT, output_root=partial)
        before = {name: (partial / name).read_bytes() for name in owner.OUTPUT_FILENAMES}
        second = owner.materialize_artifacts_v1(REPO_ROOT, output_root=partial)
        after = {name: (partial / name).read_bytes() for name in owner.OUTPUT_FILENAMES}
        if first != second or before != after or before != first:
            fail("VALID_REMATERIALIZATION_NOT_IDEMPOTENT")
    return {
        "root_symlink_rejected_before_write": True,
        "unexpected_entry_rejected_before_write": True,
        "allowed_output_symlink_rejected_before_write": True,
        "allowed_output_nonregular_rejected_before_write": True,
        "partial_valid_subset_allowed": True,
        "valid_exact4_rematerialization_idempotent": True,
    }


def check_lifecycle_simulations(expected_paths: set[str]) -> dict[str, bool]:
    validate_relation_values(
        profile=CANDIDATE_UNTRACKED,
        head=BASELINE_HEAD,
        parent=None,
        origin_main=BASELINE_HEAD,
        ahead=0,
        behind=0,
        changed_paths=set(),
        expected_paths=expected_paths,
    )
    successor = "f" * 40
    validate_relation_values(
        profile=TRACKED_CLEAN,
        head=successor,
        parent=BASELINE_HEAD,
        origin_main=BASELINE_HEAD,
        ahead=1,
        behind=0,
        changed_paths=expected_paths,
        expected_paths=expected_paths,
    )
    validate_relation_values(
        profile=TRACKED_CLEAN,
        head=successor,
        parent=BASELINE_HEAD,
        origin_main=successor,
        ahead=0,
        behind=0,
        changed_paths=expected_paths,
        expected_paths=expected_paths,
    )
    return {
        "candidate_lifecycle_supported": True,
        "committed_unpushed_lifecycle_supported": True,
        "pushed_lifecycle_supported": True,
        "future_successor_SHA_not_hardcoded": True,
    }


def check_b4_core() -> dict[str, object]:
    result = b4_guard.verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
        repo_root=REPO_ROOT
    )
    required = {
        "new_semantic_exact_posix_mode_occurrence_count": 0,
        "new_ambiguous_mode_occurrence_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "ready_for_training": False,
    }
    if any(result.get(key) != value for key, value in required.items()):
        fail("B4_FUTURE_GUARD_RESULT_INVALID")
    scanned_python = set(result.get("future_guard_scanned_python_paths", ()))
    scanned_json = set(result.get("future_guard_scanned_json_paths", ()))
    required_python = {
        owner.SOURCE_RELATIVE.as_posix(),
        owner.CHECKER_RELATIVE.as_posix(),
        owner.TEST_RELATIVE.as_posix(),
    }
    required_json = {
        (owner.OUTPUT_ROOT_RELATIVE / owner.SNAPSHOT).as_posix(),
        (owner.OUTPUT_ROOT_RELATIVE / owner.SUMMARY).as_posix(),
        (owner.OUTPUT_ROOT_RELATIVE / owner.MANIFEST).as_posix(),
    }
    if not required_python <= scanned_python or not required_json <= scanned_json:
        fail("B4_NEW_RELEVANT_FILES_NOT_ALL_SCANNED")
    return {**required, "all_relevant_new_python_json_scanned": True}


def check_forbidden_files(expected_paths: set[str]) -> None:
    transient = [
        path
        for root in (
            REPO_ROOT / "src/covalent_ext",
            REPO_ROOT / "scripts",
            REPO_ROOT / "tests",
            REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE,
        )
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
        and (
            path.suffix.lower() in FORBIDDEN_SUFFIXES
            or "__pycache__" in path.parts
        )
    ]
    if transient:
        fail("TRANSIENT_OR_FORBIDDEN_FILE_PRESENT")
    if any(Path(path).suffix.lower() in FORBIDDEN_SUFFIXES for path in expected_paths):
        fail("FORBIDDEN_EXPECTED_PATH")


def main() -> int:
    candidate_records, profile = check_candidate_inventory()
    expected_paths = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    check_forbidden_files(expected_paths)
    check_formal_validator_lifecycle()
    report = owner.check_materialized_v1(REPO_ROOT)
    live = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    owner.validate_completed_decision_projection_v1(live, repo_root=REPO_ROOT)
    check_independent_semantics(live)
    check_determinism(live)
    prewrite = check_prewrite_boundary()
    lifecycle = check_lifecycle_simulations(expected_paths)
    b4 = check_b4_core()
    result = {
        "status": "PASS",
        "schema_version": owner.SCHEMA_VERSION,
        "repository_profile": profile,
        "candidate_file_count": 7,
        "candidate_files": candidate_records,
        "output_file_count": 4,
        "event_count": 4,
        "active_source_binding_count": 9,
        "task_domain_negative": True,
        "completed_negative_projection_exact": True,
        "raw_structural_evidence_preserved": True,
        "raw_evidence_promoted_to_human_authority": False,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocess_called": False,
        "deterministic_double_build": True,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "source_binding_V2_clean_from_birth": True,
        "numeric_POSIX_semantic_identity": False,
        "tracked_modifications": 0,
        "staged_changes": 0,
        "ordinary_untracked_strict_exact7": profile == CANDIDATE_UNTRACKED,
        "protected_source_diffs": 0,
        "forbidden_new_files": 0,
        "prewrite": prewrite,
        "lifecycle": lifecycle,
        "b4": b4,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
        "ready_for_training": False,
        "owner_check": report,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("PASS")
    print(profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
