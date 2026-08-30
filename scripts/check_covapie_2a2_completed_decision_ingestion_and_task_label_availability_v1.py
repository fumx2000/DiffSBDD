#!/usr/bin/env python3
"""Fail-closed checker for 2A2 completed-decision ingestion V1."""

from __future__ import annotations

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
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)


ERROR = "COVAPIE_2A2_INGESTION_CHECK_FAILED"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part", ".pyc", ".log",
)
PROTECTED_PREFIXES = (
    "data/raw/", "checkpoints/", "equivariant_diffusion/",
)
PROTECTED_FILES = {
    "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
}
_CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
_TRACKED_CLEAN = "TRACKED_CLEAN"


def fail(reason: str) -> None:
    raise SystemExit(f"{ERROR}:{reason}")


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + "_".join(args))
    return result.stdout


def check_text(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        fail("CANDIDATE_NOT_REGULAR:" + path.as_posix())
    payload = path.read_bytes()
    if (
        len(payload) == 0
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        fail("TEXT_HYGIENE_INVALID:" + path.as_posix())
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        fail("UTF8_INVALID:" + path.as_posix())
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        fail("TRAILING_WHITESPACE:" + path.as_posix())
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "bytes": len(payload),
        "loc": len(text.splitlines()),
        "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
        "sha256": sha(payload),
    }


def binding_path(record: dict[str, object]) -> Path:
    relative = Path(str(record["path"]))
    namespace = record["path_namespace"]
    if namespace == "repository_relative":
        return REPO_ROOT / relative
    if namespace == "project_parent_relative":
        return REPO_ROOT.parent / relative
    fail("BINDING_NAMESPACE_INVALID")


def verify_binding_records(records: object, expected_count: int) -> None:
    if type(records) is not list or len(records) != expected_count:
        fail("BINDING_COUNT_INVALID")
    for record in records:
        if type(record) is not dict:
            fail("BINDING_RECORD_INVALID")
        path = binding_path(record)
        if path.is_symlink() or not path.is_file():
            fail("BOUND_SOURCE_NOT_REGULAR:" + str(record.get("source_role")))
        payload = path.read_bytes()
        if len(payload) != record.get("byte_count"):
            fail("BOUND_SOURCE_BYTE_DRIFT:" + str(record.get("source_role")))
        if sha(payload) != record.get("sha256"):
            fail("BOUND_SOURCE_SHA_DRIFT:" + str(record.get("source_role")))
        if "mode" in record and f"{stat.S_IMODE(path.stat().st_mode):04o}" != record["mode"]:
            fail("BOUND_SOURCE_MODE_DRIFT:" + str(record.get("source_role")))


def _classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    status_lines: tuple[str, ...],
    working_tree_diff_paths: tuple[str, ...],
    cached_diff_paths: tuple[str, ...],
) -> str:
    """Classify only an untracked candidate or a clean tracked Exact7."""

    expected = set(expected_paths)
    if len(expected_paths) != 7 or len(expected) != 7:
        fail("EXPECTED_CANDIDATE_INVENTORY_NOT_EXACT7")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        fail("CANDIDATE_TRACKING_PROFILE_MIXED")
    if working_tree_diff_paths:
        fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff_paths:
        fail("STAGED_INDEX_CHANGE_PRESENT")
    actual_status = set(status_lines)
    if len(actual_status) != len(status_lines):
        fail("DUPLICATE_GIT_STATUS_ENTRY")
    if not tracked_candidate:
        expected_status = {"?? " + path for path in expected}
        if expected_status - actual_status:
            fail("CANDIDATE_UNTRACKED_STATUS_MISSING")
        if actual_status - expected_status:
            fail("CANDIDATE_UNTRACKED_STATUS_EXTRA")
        return _CANDIDATE_UNTRACKED
    if actual_status:
        fail("TRACKED_CLEAN_STATUS_NOT_EMPTY")
    return _TRACKED_CLEAN


def _observed_2a2_candidate_paths() -> set[str]:
    paths = [
        *(REPO_ROOT / "src/covalent_ext").glob("covapie_2a2_*"),
        *(REPO_ROOT / "scripts").glob("check_covapie_2a2_*"),
        *(REPO_ROOT / "tests").glob("test_covapie_2a2_*"),
    ]
    output_root = REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE
    if output_root.is_dir() and not output_root.is_symlink():
        paths.extend(output_root.iterdir())
    return {path.relative_to(REPO_ROOT).as_posix() for path in paths}


def check_candidate_inventory() -> tuple[list[dict[str, object]], str]:
    expected = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    expected_set = set(expected)
    missing = [
        relative
        for relative in expected
        if not (REPO_ROOT / relative).exists()
        and not (REPO_ROOT / relative).is_symlink()
    ]
    if missing:
        fail("CANDIDATE_FILE_MISSING")
    observed = _observed_2a2_candidate_paths()
    if observed - expected_set:
        fail("UNEXPECTED_2A2_CANDIDATE_FILE")
    if expected_set - observed:
        fail("CANDIDATE_FILESET_NOT_EXACT7")
    tracked = set(run_git("ls-files").splitlines())
    status_lines = tuple(
        run_git("status", "--short", "--untracked-files=all").splitlines()
    )
    working_tree_diff_paths = tuple(
        run_git("diff", "--name-only").splitlines()
    )
    cached_diff_paths = tuple(
        run_git("diff", "--cached", "--name-only").splitlines()
    )
    repository_profile = _classify_repository_profile(
        expected_paths=expected,
        tracked_paths=tracked,
        status_lines=status_lines,
        working_tree_diff_paths=working_tree_diff_paths,
        cached_diff_paths=cached_diff_paths,
    )
    records = [check_text(REPO_ROOT / relative) for relative in expected]
    if any(Path(relative).suffix.lower() in FORBIDDEN_SUFFIXES for relative in expected):
        fail("FORBIDDEN_CANDIDATE_SUFFIX")
    if any(
        relative in PROTECTED_FILES
        or any(relative.startswith(prefix) for prefix in PROTECTED_PREFIXES)
        for relative in expected
    ):
        fail("PROTECTED_CANDIDATE_PATH")
    transient = [
        path
        for root in {
            REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE,
            REPO_ROOT / "src/covalent_ext",
            REPO_ROOT / "scripts",
            REPO_ROOT / "tests",
        }
        for path in root.glob("*2a2*")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name == "__pycache__"
    ]
    if transient:
        fail("2A2_TRANSIENT_FILE_PRESENT")
    return records, repository_profile


def check_independent_semantics(artifacts: dict[str, bytes]) -> None:
    snapshot = json.loads(artifacts[owner.SNAPSHOT])
    summary = json.loads(artifacts[owner.SUMMARY])
    manifest = json.loads(artifacts[owner.MANIFEST])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8")))
    )
    if snapshot.get("schema_version") != owner.SNAPSHOT_SCHEMA_VERSION:
        fail("SNAPSHOT_SCHEMA_INVALID")
    approval = snapshot.get("human_approval", {})
    expected_d = {
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "D4_role_partition": "SELECT_CANDIDATE_4",
        "D5_training_use": "EXCLUDE_FROM_TRAINING_ONLY",
    }
    if (
        any(approval.get(key) != value for key, value in expected_d.items())
        or approval.get("reviewer_id") != "fmx"
        or approval.get("attestor_id") != "fmx"
        or approval.get("approved_at_utc") != "2026-08-30T07:29:33Z"
        or approval.get("authorization_source")
        != "EXTERNAL_EXPLICIT_HUMAN_APPROVAL"
    ):
        fail("SNAPSHOT_D1_D5_INVALID")
    precedent = snapshot.get("precedent_state", {})
    if (
        "2A2_independent_human_review_still_required" in precedent
        or precedent.get("2A2_independent_human_review_completed") is not True
        or precedent.get("precedent_did_not_substitute_for_2A2_independent_review")
        is not True
    ):
        fail("SNAPSHOT_REVISED1_PRECEDENT_STATE_INVALID")
    role = snapshot.get("selected_role_partition", {})
    if (
        role.get("chemical_warhead_atom_ids") is not None
        or role.get("chemical_warhead_human_authoritative") is not False
        or role.get("warhead_role_atom_ids") != ["SD"]
        or role.get("linker_atom_ids") != ["C1", "C15", "C16", "C17", "O18"]
        or role.get("scaffold_atom_ids")
        != ["C20", "C21", "C23", "C24", "C25", "C26", "C27", "C28", "C29", "C30", "CL99", "N19", "N22"]
        or role.get("selected_candidate_index_0based") != 4
        or role.get("role_profile") != "STRICT_LINKER_PRESENT_V1"
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("applicable_task_ids") != [0, 1, 2, 3, 4]
    ):
        fail("SNAPSHOT_CHEMICAL_ROLE_OR_SEED_INVALID")
    if len(rows) != 4 or [int(row["scaleup_rank"]) for row in rows] != [507, 508, 509, 510]:
        fail("MATRIX_EXACT4_INVALID")
    if len({row["canonical_event_id"] for row in rows}) != 4:
        fail("MATRIX_EVENT_COLLAPSE_OR_DUPLICATE")
    distances = ["2.022434", "2.025631", "2.020764", "2.024483"]
    for row, distance in zip(rows, distances):
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "SD"
            or row["POST_distance_angstrom"] != distance
            or row["selected_role_candidate_index_0based"] != "4"
            or json.loads(row["warhead_atoms_json"]) != ["SD"]
            or json.loads(row["chemical_warhead_atoms_json"]) is not None
            or [item["task_id"] for item in applicability if item["structurally_applicable"]] != [0, 1, 2, 3, 4]
            or row["minimal_seed_authority_available"] != "false"
            or row["formal_event_training_use_decision"]
            != "EXCLUDE_FROM_TRAINING_ONLY"
            or row["human_training_excluded"] != "true"
            or row["training_use_allowed"] != "false"
            or row["candidate_for_future_training_admission"] != "false"
            or row["training_admitted"] != "false"
            or row["training_materialization_allowed_now"] != "false"
            or row["current_runtime_model_usable"] != "false"
        ):
            fail("MATRIX_ROLE_TASK_OR_ADMISSION_INVALID")
    required_counts = {
        "event_count": 4,
        "completed_human_positive_count": 4,
        "chemistry_positive_count": 4,
        "task_relevant_count": 4,
        "reactive_pair_human_authority_count": 4,
        "role_partition_human_authority_count": 4,
        "chemical_warhead_human_authority_count": 0,
        "human_training_INCLUDE_count": 0,
        "human_training_EXCLUDE_count": 4,
        "direct_profile_count": 0,
        "strict_profile_count": 4,
        "future_training_admission_candidate_count": 0,
        "future_training_candidate_derived_by_ingestion_count": 0,
        "training_admitted_count": 0,
        "minimal_seed_authority_count": 0,
        "PRE_topology_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
    }
    if any(summary.get(key) != value for key, value in required_counts.items()):
        fail("SUMMARY_COUNTS_INVALID")
    census = manifest.get("current_published_census_boundary", {})
    if [
        census.get("positive"), census.get("relevant"),
        census.get("training_INCLUDE"), census.get("training_EXCLUDE"),
        census.get("future_candidates"), census.get("pair_sample_authority"),
        census.get("role_sample_authority"),
    ] != [108, 109, 44, 64, 27, 108, 108]:
        fail("PUBLISHED_CENSUS_BOUNDARY_INVALID")
    if census.get("current_2A2_status") != "CURRENTLY_UNREVIEWED":
        fail("PUBLISHED_CENSUS_2A2_STATUS_INVALID")
    output_bindings = manifest.get("output_artifact_bindings", {})
    for name in (owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY):
        if output_bindings.get(name, {}).get("sha256") != sha(artifacts[name]):
            fail("MANIFEST_OUTPUT_BINDING_INVALID:" + name)
    if (
        manifest.get("manifest_self_sha256_recorded") is not False
        or manifest.get("global_reconciliation_update_status") != "NOT_DONE_THIS_STEP"
        or manifest.get("global_census_update_status") != "NOT_DONE_THIS_STEP"
        or manifest.get("ready_for_training") is not False
    ):
        fail("MANIFEST_AUTHORITY_BOUNDARY_INVALID")
    verify_binding_records([manifest["formal_decision_binding"]], 1)
    verify_binding_records([manifest["formal_validator_binding"]], 1)
    verify_binding_records(manifest["formal_evidence_bindings"], 11)
    verify_binding_records(manifest["semantic_owner_bindings"], 2)
    verify_binding_records(manifest["precedent_bindings"], 4)
    verify_binding_records(manifest["current_published_census_bindings"], 4)
    verify_binding_records(manifest["current_reconciliation_bindings"], 1)


def check_determinism(live: dict[str, bytes]) -> None:
    in_memory_1 = owner.build_artifacts_v1(REPO_ROOT)
    in_memory_2 = owner.build_artifacts_v1(REPO_ROOT)
    if live != in_memory_1 or live != in_memory_2:
        fail("IN_MEMORY_DETERMINISM_FAILED")
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root = Path(first)
        second_root = Path(second)
        first_artifacts = owner.materialize_artifacts_v1(REPO_ROOT, output_root=first_root)
        second_artifacts = owner.materialize_artifacts_v1(REPO_ROOT, output_root=second_root)
        for name in owner.OUTPUT_FILENAMES:
            if (
                live[name] != first_artifacts[name]
                or live[name] != second_artifacts[name]
                or live[name] != (first_root / name).read_bytes()
                or live[name] != (second_root / name).read_bytes()
            ):
                fail("TEMP_MATERIALIZATION_DETERMINISM_FAILED:" + name)


def main() -> int:
    candidate_records, repository_profile = check_candidate_inventory()
    owner_report = owner.check_materialized_v1(REPO_ROOT)
    live = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    owner.validate_completed_decision_projection_v1(live, repo_root=REPO_ROOT)
    check_independent_semantics(live)
    check_determinism(live)
    formal_report = owner._run_formal_validator(
        REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    )
    if formal_report.get("status") != "PASS":
        fail("FORMAL_VALIDATOR_NOT_PASS")
    result = {
        "status": "PASS",
        "schema_version": owner.SCHEMA_VERSION,
        "repository_profile": repository_profile,
        "candidate_exact_file_count": 7,
        "candidate_files": candidate_records,
        "output_exact_file_count": 4,
        "event_count": 4,
        "formal_validator": "PASS",
        "published_runtime_validation": "PASS",
        "deterministic_live_temp1_temp2": True,
        "negative_contract_covered_by_targeted_tests": True,
        "tracked_modifications": 0,
        "staged_changes": 0,
        "ordinary_untracked_exact7": repository_profile == _CANDIDATE_UNTRACKED,
        "forbidden_new_files": 0,
        "cache_or_transient_files": 0,
        "protected_source_diffs": 0,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
        "ready_for_training": False,
        "owner_check": owner_report,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
