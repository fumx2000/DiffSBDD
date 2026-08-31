#!/usr/bin/env python3
"""Fail-closed checker for the I12 completed-decision ingestion Exact7."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
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
    covapie_i12_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


ERROR = "COVAPIE_I12_INGESTION_CHECK_FAILED"
BASELINE_HEAD = "758c796b483a14f8b61a04f770b559c1aee98675"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part", ".pyc",
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
        "diff", "diff-tree", "ls-files", "merge-base", "rev-list",
        "rev-parse", "status",
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
            label="I12_EXACT7:" + relative,
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
        if not (
            head == BASELINE_HEAD
            and origin_main == BASELINE_HEAD
            and (ahead, behind) == (0, 0)
        ):
            fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        fail("REPOSITORY_PROFILE_INVALID")
    run_git("merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD")
    changed = set(
        filter(
            None,
            run_git("diff", "--name-only", BASELINE_HEAD + "..HEAD").splitlines(),
        )
    )
    if head == BASELINE_HEAD or changed != expected_paths:
        fail("TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID")
    if not (
        (origin_main == BASELINE_HEAD and behind == 0 and ahead >= 1)
        or (origin_main == head and (ahead, behind) == (0, 0))
    ):
        fail("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")


def observed_i12_candidate_paths() -> set[str]:
    paths = [
        *(REPO_ROOT / "src/covalent_ext").glob("covapie_i12_*"),
        *(REPO_ROOT / "scripts").glob("check_covapie_i12_*"),
        *(REPO_ROOT / "tests").glob("test_covapie_i12_*"),
    ]
    output_root = REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE
    if output_root.is_dir() and not output_root.is_symlink():
        paths.extend(output_root.iterdir())
    return {path.relative_to(REPO_ROOT).as_posix() for path in paths}


def check_candidate_inventory() -> tuple[list[dict[str, object]], str]:
    expected = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    expected_set = set(expected)
    if observed_i12_candidate_paths() != expected_set:
        fail("I12_CANDIDATE_FILESET_NOT_EXACT7")
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
    if any("reconciliation" in path or "census" in path or "queue" in path for path in expected):
        fail("FORBIDDEN_ADJACENT_ARTIFACT_IN_CANDIDATE")
    records = [check_text_file(path) for path in expected]
    return records, profile


def binding_path(record: MappingLike) -> Path:
    relative = Path(str(record["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        fail("BOUND_PATH_INVALID")
    namespace = record["namespace"]
    if namespace == "repository_relative":
        return REPO_ROOT / relative
    if namespace == "project_parent_relative":
        return REPO_ROOT.parent / relative
    fail("BOUND_NAMESPACE_INVALID")


MappingLike = dict[str, object]


def verify_binding_records(records: object, expected_count: int) -> None:
    if type(records) is not list or len(records) != expected_count:
        fail("BOUND_RECORD_COUNT_INVALID")
    for record in records:
        if type(record) is not dict:
            fail("BOUND_RECORD_INVALID")
        if set(record) != {
            "path", "namespace", "byte_count", "SHA256",
            "expected_executable_class", "source_role",
        }:
            fail("BOUND_RECORD_SHAPE_INVALID")
        expected_class = record["expected_executable_class"]
        if expected_class not in {"EXECUTABLE", "NON_EXECUTABLE"}:
            fail("BOUND_EXECUTABLE_CLASS_INVALID")
        try:
            verify_bound_source_v2(
                path=binding_path(record),
                expected_byte_count=int(record["byte_count"]),
                expected_sha256=str(record["SHA256"]),
                label="I12_CHECKER_BOUND_SOURCE:" + str(record["source_role"]),
                expected_executable=expected_class == "EXECUTABLE",
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
    if "execute_formal_validator" in source or "_run_formal_validator" in source:
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTION_HOOK")


def check_independent_semantics(artifacts: dict[str, bytes]) -> None:
    snapshot = json.loads(artifacts[owner.SNAPSHOT])
    summary = json.loads(artifacts[owner.SUMMARY])
    manifest = json.loads(artifacts[owner.MANIFEST])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8")))
    )
    approval = snapshot.get("human_approval", {})
    if [approval.get("D" + str(index) + suffix) for index, suffix in (
        (1, "_task_relevance"),
        (2, "_chemistry"),
        (3, "_reactive_pair"),
        (4, "_role_partition"),
        (5, "_training_use"),
    )] != [
        "RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_0", "INCLUDE",
    ]:
        fail("SNAPSHOT_D1_D5_INVALID")
    role = snapshot.get("selected_role_partition", {})
    if (
        role.get("selected_role_candidate_index_0based") != 0
        or role.get("role_profile") != owner.EXPECTED_ROLE_PROFILE
        or role.get("warhead_role_atom_ids") != list(owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids") != list(owner.SCAFFOLD_ROLE)
        or role.get("chemical_warhead_human_authoritative") is not False
        or role.get("chemical_warhead_atom_ids") is not None
    ):
        fail("SNAPSHOT_ROLE_OR_CHEMICAL_AUTHORITY_INVALID")
    if len(rows) != 4 or tuple(int(row["scaleup_rank"]) for row in rows) != owner.EXPECTED_RANKS:
        fail("MATRIX_EXACT4_INVALID")
    for row in rows:
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C21"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [item["task_id"] for item in applicability if item["structurally_applicable"]]
            != [0, 3, 4]
            or row["chemical_warhead_human_authoritative"] != "false"
            or json.loads(row["chemical_warhead_atoms_json"]) is not None
            or row["training_use_include"] != "true"
            or row["candidate_for_future_training_admission"] != "true"
            or row["future_training_candidate_is_training_admission"] != "false"
            or row["training_admitted"] != "false"
            or row["POST_geometry_training_authority_available"] != "false"
            or row["PRE_topology_authority_available"] != "false"
            or row["PRE_geometry_authority_available"] != "false"
            or row["authority_created_by_this_ingestion"] != "false"
        ):
            fail("MATRIX_AUTHORITY_BOUNDARY_INVALID")
    required_summary = {
        "review_unit": "I12",
        "event_count": 4,
        "D1_RELEVANT_count": 4,
        "D2_POSITIVE_count": 4,
        "D3_CONFIRMED_count": 4,
        "DIRECT_event_count": 4,
        "applicable_warhead_only_count": 4,
        "applicable_linker_plus_warhead_count": 0,
        "applicable_scaffold_plus_warhead_count": 0,
        "applicable_scaffold_only_count": 4,
        "applicable_scaffold_plus_linker_plus_warhead_count": 4,
        "D5_INCLUDE_count": 4,
        "future_training_admission_candidate_count": 4,
        "training_admitted_count": 0,
        "PRE_topology_authority_count": 0,
        "POST_geometry_training_authority_count": 0,
        "chemical_warhead_human_authority_count": 0,
        "reusable_chemistry_authority_count": 0,
        "ready_for_training": False,
    }
    if any(summary.get(key) != value for key, value in required_summary.items()):
        fail("SUMMARY_COUNTS_OR_BOUNDARY_INVALID")
    census = manifest.get("current_census_boundary", {})
    if [
        census.get("completed_positive_event_count"),
        census.get("completed_positive_unit_count"),
        census.get("completed_event_count"),
        census.get("completed_unit_count"),
        census.get("unreviewed_event_count"),
        census.get("unreviewed_unit_count"),
    ] != [95, 13, 119, 17, 219, 114]:
        fail("CURRENT_CENSUS_BASELINE_INVALID")
    if (
        manifest.get("candidate_publication_file_count") != 7
        or manifest.get("output_artifact_count") != 4
        or manifest.get("numeric_POSIX_semantic_identity") is not False
        or manifest.get("formal_validator_runtime_dependency") is not False
        or manifest.get("reconciliation_performed") is not False
        or manifest.get("census_refreshed") is not False
        or manifest.get("ready_for_training") is not False
    ):
        fail("MANIFEST_BOUNDARY_INVALID")
    verify_binding_records([manifest["formal_decision_binding"]], 1)
    verify_binding_records([manifest["formal_validator_binding"]], 1)
    verify_binding_records([manifest["source_binding_policy_binding"]], 1)
    verify_binding_records(manifest["semantic_owner_bindings"], 2)
    verify_binding_records(manifest["current_census_bindings"], 4)


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


def check_forbidden_files(expected_paths: set[str]) -> None:
    for relative in expected_paths:
        if Path(relative).suffix.lower() in FORBIDDEN_SUFFIXES:
            fail("FORBIDDEN_SUFFIX:" + relative)
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


def main() -> int:
    candidate_records, repository_profile = check_candidate_inventory()
    expected_paths = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    check_forbidden_files(expected_paths)
    check_formal_validator_lifecycle()
    owner_report = owner.check_materialized_v1(REPO_ROOT)
    live = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    owner.validate_completed_decision_projection_v1(live, repo_root=REPO_ROOT)
    check_independent_semantics(live)
    check_determinism(live)
    result = {
        "status": "PASS",
        "schema_version": owner.SCHEMA_VERSION,
        "repository_profile": repository_profile,
        "candidate_exact_file_count": 7,
        "candidate_files": candidate_records,
        "output_exact_file_count": 4,
        "event_count": 4,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocess_called": False,
        "deterministic_double_build": True,
        "tracked_modifications": 0,
        "staged_changes": 0,
        "ordinary_untracked_strict_exact7": repository_profile == CANDIDATE_UNTRACKED,
        "protected_source_diffs": 0,
        "forbidden_new_files": 0,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
        "ready_for_training": False,
        "owner_check": owner_report,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("PASS")
    print(repository_profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
