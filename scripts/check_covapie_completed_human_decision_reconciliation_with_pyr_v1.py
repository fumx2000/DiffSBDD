#!/usr/bin/env python3
"""Independent fail-closed checker for the PYR reconciliation Exact4."""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, Callable, NoReturn

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_6oa_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_pyr_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_tp2_v1 as adapter  # noqa: E402
from covalent_ext import covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


BASELINE_COMMIT = "74ffc990b5c0d41650f17327a2a885ebb9542390"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
DEPENDENCY_BINDINGS = (
    (
        "GENERIC_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "WITH_6OA_PREDECESSOR_OWNER",
        predecessor.SOURCE_RELATIVE.as_posix(),
        38355,
        "bc9183796e973366b1edb6764ec79750d31d55685f366a855b5728c5f1316559",
    ),
    (
        "WITH_6OA_PREDECESSOR_ARTIFACT",
        predecessor.OUTPUT_RELATIVE.as_posix(),
        344196,
        "b050f0c49f4f7ce017b97051e80ac9bb4d2471198229ec4d79154486f29146e6",
    ),
    (
        "HISTORICAL_ADAPTER_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_tp2_v1.py",
        26679,
        "d9bd34e780323535056100b5a11956bf9c6965ed5d58c8aa2c20f8f33a6938fe",
    ),
    (
        "PYR_INGESTION_OWNER",
        ingestion.SOURCE_RELATIVE.as_posix(),
        114638,
        "efc3903c59c8f6de06708914e136c2494f5e4655524456bd453974cd403df140",
    ),
    (
        "PYR_INGESTION_SNAPSHOT",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SNAPSHOT).as_posix(),
        32389,
        "d780983cdb174f76a3d1643dbc3f3e28ae044f2be6ddff87f9dac5df8074bc56",
    ),
    (
        "PYR_INGESTION_MATRIX",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX).as_posix(),
        5468,
        "1b0bf73ea9cb01188402ea8bd5c2dfbf7436ecfbae833ae6505767d24f993d93",
    ),
    (
        "PYR_INGESTION_SUMMARY",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SUMMARY).as_posix(),
        6428,
        "71d2620db80c887e3a4a8ab5747e6484d2e3430a5d4a683b4e109d721ccfac12",
    ),
    (
        "PYR_INGESTION_MANIFEST",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MANIFEST).as_posix(),
        26813,
        "3f5119c00d32c328065fe3836e58baf27868b89f6151888c6ba03fe863b22969",
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
PROTECTED_PREFIXES = (
    "data/raw/",
    "checkpoints/",
    "equivariant_diffusion/",
    "covapie-state/",
)
PROTECTED_FILES = {
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
    ingestion.SOURCE_RELATIVE.as_posix(),
    predecessor.SOURCE_RELATIVE.as_posix(),
    predecessor.OUTPUT_RELATIVE.as_posix(),
    ingestion.CENSUS_OWNER_RELATIVE.as_posix(),
    ingestion.CENSUS_MATRIX_RELATIVE.as_posix(),
    ingestion.CENSUS_SUMMARY_RELATIVE.as_posix(),
    ingestion.CENSUS_MANIFEST_RELATIVE.as_posix(),
}
_GENERIC_FACT_FIELDS = (
    "canonical_event_id",
    "review_unit_id",
    "human_review_completed",
    "legacy_completed_review_status",
    "task_relevance_disposition",
    "chemistry_disposition",
    "training_disposition",
    "human_training_excluded",
    "source_decision_schema",
    "source_decision_sha256",
    "source_binding_path",
)
_SOURCE_BINDING_FIELDS = (
    "source_path",
    "path_namespace",
    "byte_count",
    "sha256",
    "schema_version",
    "review_unit_id",
)
_ARTIFACT_FIELDS = (
    "reconciled_rows",
    "source_bindings",
    "normalized_facts",
    "review_summary",
)
_EXPECTED_PREDECESSOR_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 123,
    "completed_positive_unit_count": 20,
    "completed_negative_event_count": 48,
    "completed_negative_unit_count": 10,
    "completed_total_event_count": 171,
    "completed_total_unit_count": 30,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 167,
    "unreviewed_unit_count": 101,
}
_EXPECTED_SUCCESSOR_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 127,
    "completed_positive_unit_count": 21,
    "completed_negative_event_count": 48,
    "completed_negative_unit_count": 10,
    "completed_total_event_count": 175,
    "completed_total_unit_count": 31,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 163,
    "unreviewed_unit_count": 100,
}
_OPERATION_BOUNDARY = {
    "reconciliation_performed": True,
    "census_refresh_performed": False,
    "queue_refresh_performed": False,
    "next_review_started": False,
    "task_label_authority": False,
    "event_task_label_rows_materialized": False,
    "mask_tensor_targets_created": False,
    "formal_training_admitted": False,
    "training_admission_created": False,
    "training_materialization_allowed": False,
    "parameter_update_authorization": False,
    "feature_semantics_audit_performed": False,
    "feature_semantics_audit_required_before_training": True,
    "ready_for_training": False,
    "training_started": False,
}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_PYR_RECONCILIATION_V1_ERROR:" + token)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular(path: Path, label: str) -> bytes:
    try:
        metadata, payload = path.lstat(), path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail("NOT_REGULAR_FILE:" + label)
    return payload


def _git(root: Path, *arguments: str) -> str:
    if not arguments or arguments[0] not in {
        "diff",
        "ls-files",
        "merge-base",
        "rev-list",
        "rev-parse",
        "status",
    }:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    process = subprocess.run(
        ("git", *arguments), cwd=root, text=True, capture_output=True, check=False
    )
    if process.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return process.stdout.rstrip("\n")


def _ancestor(root: Path, older: str, newer: str) -> bool:
    process = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=root,
        capture_output=True,
        check=False,
    )
    if process.returncode not in (0, 1):
        _fail("GIT_ANCESTRY_CHECK_FAILED")
    return process.returncode == 0


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
    if len(expected_paths) != 4 or len(expected) != 4:
        _fail("EXPECTED_INVENTORY_NOT_EXACT4")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        _fail("MIXED_TRACKING_STATE")
    if working_diff:
        _fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        _fail("STAGED_INDEX_CHANGE_PRESENT")
    if not tracked_candidate:
        if ordinary_untracked != expected or set(status_lines) != {
            "?? " + path for path in expected
        }:
            _fail("CANDIDATE_UNTRACKED_NOT_STRICT_EXACT4")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        _fail("TRACKED_CLEAN_STATE_DIRTY")
    return TRACKED_CLEAN


def validate_repository_relation_values(
    *,
    profile: str,
    expected_paths: set[str],
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    baseline_is_ancestor_of_head: bool,
    baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool,
    changed_since_baseline: set[str],
) -> None:
    if profile == CANDIDATE_UNTRACKED:
        if not (
            head == origin_main == BASELINE_COMMIT
            and (ahead, behind) == (0, 0)
            and baseline_is_ancestor_of_head
            and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head
            and not changed_since_baseline
        ):
            _fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        _fail("REPOSITORY_PROFILE_INVALID")
    if (
        not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or head == BASELINE_COMMIT
        or behind != 0
        or ahead < 0
        or not expected_paths <= changed_since_baseline
        or ((ahead == 0) != (origin_main == head))
    ):
        _fail("TRACKED_CLEAN_PUBLICATION_RELATION_INVALID")


def validate_tracked_index_modes(
    stage_lines: tuple[str, ...], expected_paths: set[str]
) -> dict[str, str]:
    if len(expected_paths) != 4 or len(stage_lines) != 4:
        _fail("TRACKED_GIT_INDEX_MODE_INVALID")
    modes: dict[str, str] = {}
    for line in stage_lines:
        parts = line.split(None, 3)
        if len(parts) != 4:
            _fail("TRACKED_GIT_INDEX_MODE_INVALID")
        mode, object_id, stage_number, path = parts
        if (
            path in modes
            or path not in expected_paths
            or mode != "100644"
            or stage_number != "0"
            or len(object_id) not in {40, 64}
            or any(character not in "0123456789abcdef" for character in object_id)
        ):
            _fail("TRACKED_GIT_INDEX_MODE_INVALID")
        modes[path] = mode
    if set(modes) != expected_paths:
        _fail("TRACKED_GIT_INDEX_MODE_INVALID")
    return modes


def _validate_history_scope(changed: set[str]) -> None:
    for path in sorted(changed):
        if path in PROTECTED_FILES or any(
            path.startswith(prefix) for prefix in PROTECTED_PREFIXES
        ):
            _fail("PROTECTED_PATH_CHANGED_SINCE_BASELINE:" + path)
        if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail("FORBIDDEN_SUFFIX_CHANGED_SINCE_BASELINE:" + path)


def _verify_repository(root: Path) -> dict[str, object]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    tracked = set(filter(None, _git(root, "ls-files").splitlines()))
    untracked = set(
        filter(
            None,
            _git(root, "ls-files", "--others", "--exclude-standard").splitlines(),
        )
    )
    status_lines = tuple(
        filter(
            None,
            _git(root, "status", "--short", "--untracked-files=all").splitlines(),
        )
    )
    working = set(filter(None, _git(root, "diff", "--name-only").splitlines()))
    cached = set(
        filter(None, _git(root, "diff", "--cached", "--name-only").splitlines())
    )
    profile = classify_repository_profile(
        expected_paths=paths,
        tracked_paths=tracked,
        ordinary_untracked=untracked,
        status_lines=status_lines,
        working_diff=working,
        cached_diff=cached,
    )
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "origin/main")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    relation = _git(
        root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    if branch != "main" or len(relation) != 2 or any(
        not part.isdigit() for part in relation
    ):
        _fail("REPOSITORY_IDENTITY_INVALID")
    ahead, behind = map(int, relation)
    changed = (
        set()
        if profile == CANDIDATE_UNTRACKED
        else set(
            filter(
                None,
                _git(
                    root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD"
                ).splitlines(),
            )
        )
    )
    validate_repository_relation_values(
        profile=profile,
        expected_paths=set(paths),
        head=head,
        origin_main=origin,
        ahead=ahead,
        behind=behind,
        baseline_is_ancestor_of_head=(
            True
            if profile == CANDIDATE_UNTRACKED
            else _ancestor(root, BASELINE_COMMIT, "HEAD")
        ),
        baseline_is_ancestor_of_origin=(
            True
            if profile == CANDIDATE_UNTRACKED
            else _ancestor(root, BASELINE_COMMIT, "origin/main")
        ),
        origin_is_ancestor_of_head=(
            True
            if profile == CANDIDATE_UNTRACKED
            else _ancestor(root, "origin/main", "HEAD")
        ),
        changed_since_baseline=changed,
    )
    _validate_history_scope(changed)
    report: dict[str, object] = {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "lifecycle": profile,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(untracked),
        "expected_git_publication_mode": "100644",
    }
    if profile == CANDIDATE_UNTRACKED:
        report["git_index_mode_checked"] = False
    else:
        stage_lines = tuple(
            filter(
                None,
                _git(root, "ls-files", "--stage", "--", *paths).splitlines(),
            )
        )
        report["git_index_mode_checked"] = True
        report["git_index_modes"] = validate_tracked_index_modes(
            stage_lines, set(paths)
        )
    return report


def _verify_dependencies(root: Path) -> list[dict[str, object]]:
    reports = []
    for role, relative, byte_count, digest in DEPENDENCY_BINDINGS:
        payload = _read_regular(root / relative, role)
        if len(payload) != byte_count or _sha256(payload) != digest:
            _fail("PUBLISHED_DEPENDENCY_DRIFT:" + role)
        reports.append(
            {
                "role": role,
                "path": relative,
                "bytes": len(payload),
                "SHA256": digest,
            }
        )
    return reports


def _verify_external_formal_sources(root: Path) -> list[dict[str, object]]:
    expected = (
        (
            "PYR_FORMAL_JSON",
            ingestion.FORMAL_DECISION_RELATIVE,
            17975,
            "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d",
        ),
        (
            "PYR_FORMAL_VALIDATOR_PROVENANCE_ONLY",
            ingestion.FORMAL_VALIDATOR_RELATIVE,
            75613,
            "003a1e6f85616bc8d5f255bd2333f0b61ee0144afaed32a3e7ba64114cdc543c",
        ),
    )
    reports = []
    for role, relative, byte_count, digest in expected:
        path = root.parent / relative
        payload = _read_regular(path, role)
        mode = stat.S_IMODE(path.lstat().st_mode)
        if len(payload) != byte_count or _sha256(payload) != digest or mode & 0o111:
            _fail("FORMAL_PROVENANCE_DRIFT:" + role)
        reports.append(
            {
                "role": role,
                "path": relative.as_posix(),
                "bytes": len(payload),
                "SHA256": digest,
                "executed": False,
                "imported": False,
                "subprocessed": False,
            }
        )
    return reports


def _validate_text_payload(payload: bytes, mode: int, label: str) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("EXACT4_NOT_UTF8:" + label) from error
    if (
        len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\r" in payload
        or b"\x00" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or mode not in {0o644, 0o664}
        or mode & 0o111
        or any(line.rstrip(" \t") != line for line in text.splitlines())
    ):
        _fail("EXACT4_TEXT_SIZE_OR_MODE_INVALID:" + label)
    return text


def _verify_exact4_files(root: Path) -> list[dict[str, object]]:
    output_parent = root / subject.OUTPUT_ROOT_RELATIVE
    if (
        not output_parent.is_dir()
        or output_parent.is_symlink()
        or {item.name for item in output_parent.iterdir()} != {subject.OUTPUT_NAME}
    ):
        _fail("RECONCILIATION_OUTPUT_INVENTORY_NOT_EXACT1")
    reports = []
    for relative in subject.EXACT4_PATHS:
        path = root / relative
        payload = _read_regular(path, relative.as_posix())
        mode = stat.S_IMODE(path.lstat().st_mode)
        text = _validate_text_payload(payload, mode, relative.as_posix())
        reports.append(
            {
                "path": relative.as_posix(),
                "bytes": len(payload),
                "LOC": len(text.splitlines()),
                "SHA256": _sha256(payload),
                "filesystem_mode": format(mode, "04o"),
                "expected_git_publication_mode": "100644",
            }
        )
    return reports


def _strict_json(payload: bytes, label: str) -> dict[str, Any]:
    try:
        return generic._strict_json_object(payload, label)
    except generic.CompletedDecisionReconciliationError as error:
        raise ValueError(label + "_INVALID:" + str(error)) from error


def _mapping(value: object, token: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _independent_expected_projection(
    bound: dict[str, object],
) -> list[dict[str, object]]:
    formal = _mapping(bound.get("formal_document"), "PYR_FORMAL_NOT_OBJECT")
    identity = _mapping(formal.get("sample_identity"), "PYR_IDENTITY_INVALID")
    authority = _mapping(
        formal.get("sample_level_authority"), "PYR_AUTHORITY_INVALID"
    )
    decisions = _mapping(formal.get("approved_D1_D6"), "PYR_D1_D6_INVALID")
    d1 = _mapping(decisions.get("D1_observed_covalent_chemistry"), "PYR_D1_INVALID")
    d2 = _mapping(
        decisions.get("D2_task_generation_domain_relevance"), "PYR_D2_INVALID"
    )
    d3 = _mapping(decisions.get("D3_reactive_atom_pair"), "PYR_D3_INVALID")
    d4 = _mapping(
        decisions.get("D4_role_partition_and_minimal_seed"), "PYR_D4_INVALID"
    )
    d5 = _mapping(
        decisions.get("D5_structural_task_applicability"), "PYR_D5_INVALID"
    )
    d6 = _mapping(
        decisions.get("D6_later_training_use_disposition"), "PYR_D6_INVALID"
    )
    non_created = _mapping(
        formal.get("non_created_authority"), "PYR_FALSE_BOUNDARY_INVALID"
    )
    readiness = _mapping(formal.get("readiness"), "PYR_READINESS_INVALID")
    operations = _mapping(
        formal.get("operation_boundary"), "PYR_FORMAL_OPERATION_INVALID"
    )
    task_selection = _mapping(
        formal.get("selected_task_ids"), "PYR_TASK_SELECTION_INVALID"
    )
    exact5 = _mapping(
        task_selection.get("canonical_V1_contract"), "PYR_EXACT5_INVALID"
    )
    binding = _mapping(
        bound.get("formal_decision_binding"), "PYR_FORMAL_BINDING_INVALID"
    )
    validator = _mapping(
        bound.get("formal_validator_binding"), "PYR_VALIDATOR_BINDING_INVALID"
    )
    compatibility = _mapping(
        bound.get("generic_Exact11_compatibility"), "PYR_GENERIC_BOUND_INVALID"
    )
    census = _mapping(
        bound.get("current_census_boundary"), "PYR_CENSUS_BOUND_INVALID"
    )
    tasks = exact5.get("tasks")
    false_keys = {
        "task_label_authority",
        "event_task_label_rows_materialized",
        "mask_tensor_targets_created",
        "formal_training_admitted",
        "training_admission_created",
        "training_materialization_allowed",
        "parameter_update_authorization",
    }
    source_path = ingestion.FORMAL_DECISION_RELATIVE.as_posix()
    if (
        formal.get("schema_version") != ingestion.FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != ingestion.FORMAL_RECORD_ROLE
        or identity.get("PDB") != "1F8M"
        or identity.get("ligand_component_id") != "PYR"
        or identity.get("review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
        or identity.get("event_count") != 4
        or identity.get("canonical_event_ids") != list(ingestion.EXPECTED_EVENT_IDS)
        or identity.get("scaleup_event_ranks") != list(ingestion.EXPECTED_RANKS)
        or authority.get("approved") is not True
        or authority.get("human_review_completed") is not True
        or authority.get("formal_sample_level_authority_created") is not True
        or d1 != {"decision": "POSITIVE", "human_approved": True}
        or d2 != {"decision": "IN_DOMAIN", "human_approved": True}
        or d3.get("pair") != "SG:CB"
        or d3.get("protein_atom") != "SG"
        or d3.get("component_atom") != "CB"
        or d3.get("human_approved") is not True
        or d4.get("selected_candidate_id") != ingestion.SELECTED_CANDIDATE
        or d4.get("human_approved") is not True
        or d5.get("selected_task_ids") != [0, 3, 4]
        or d5.get("human_approved") is not True
        or d6.get("decision") != "EXCLUDE"
        or d6.get("human_training_excluded") is not True
        or d6.get("future_training_admission_candidate") is not False
        or d6.get("formal_training_admitted") is not False
        or any(non_created.get(key) is not False for key in false_keys)
        or readiness.get("READY_FOR_TRAINING") is not False
        or readiness.get("TRAINING_STARTED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_PERFORMED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING")
        is not True
        or readiness.get("STEP12D_STATUS")
        != "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
        or operations.get("census_performed") is not False
        or operations.get("reconciliation_performed") is not False
        or operations.get("task_label_materialization_performed") is not False
        or operations.get("parameter_update_performed") is not False
        or exact5.get("task_count") != 5
        or exact5.get("B3_present") is not True
        or exact5.get("sixth_task") is not False
        or type(tasks) is not list
        or [row.get("semantic_long_name") for row in tasks if type(row) is dict]
        != [row[1] for row in ingestion.CANONICAL_TASKS]
        or binding.get("path") != source_path
        or binding.get("path_namespace") != "project_parent_relative"
        or binding.get("byte_count") != 17975
        or binding.get("SHA256")
        != "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d"
        or validator.get("byte_count") != 75613
        or validator.get("SHA256")
        != "003a1e6f85616bc8d5f255bd2333f0b61ee0144afaed32a3e7ba64114cdc543c"
        or validator.get("validation_method")
        != "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        or compatibility.get("source_formal_generation_domain_decision")
        != "IN_DOMAIN"
        or compatibility.get("normalized_task_relevance_disposition")
        != generic.TASK_RELEVANT
        or compatibility.get("source_formal_training_use_decision") != "EXCLUDE"
        or compatibility.get("normalized_training_disposition")
        != generic.TRAINING_EXCLUDE
        or compatibility.get("accepted_fact_count") != 4
        or compatibility.get("rich_fields_leaked") is not False
        or census.get("PYR_current_review_status") != generic.CURRENTLY_UNREVIEWED
        or census.get("PYR_human_review_completed") is not False
        or census.get("raw_priority_rank") != 30
    ):
        _fail("PYR_INDEPENDENT_PROJECTION_BOUNDARY_INVALID")
    expected = [
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE,
            "task_relevance_disposition": generic.TASK_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_EXCLUDE,
            "human_training_excluded": True,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding["SHA256"],
            "source_binding_path": source_path,
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    ]
    if any(tuple(fact) != _GENERIC_FACT_FIELDS for fact in expected):
        _fail("PYR_INDEPENDENT_PROJECTION_NOT_EXACT11")
    return expected


def _review_summary(rows: list[dict[str, str]]) -> dict[str, int]:
    event_counts = Counter(row["current_review_status"] for row in rows)
    units: dict[str, set[str]] = defaultdict(set)
    status_units: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        unit = row["raw_review_unit_id"]
        status = row["current_review_status"]
        units[unit].add(status)
        status_units[status].add(unit)
    if any(len(statuses) != 1 for statuses in units.values()):
        _fail("REVIEW_UNIT_MIXED_STATUS")
    completed_units = (
        status_units[generic.COMPLETED_HUMAN_POSITIVE]
        | status_units[generic.COMPLETED_HUMAN_NEGATIVE]
    )
    return {
        "universe_event_count": len(rows),
        "universe_review_unit_count": len(units),
        "completed_positive_event_count": event_counts[
            generic.COMPLETED_HUMAN_POSITIVE
        ],
        "completed_positive_unit_count": len(
            status_units[generic.COMPLETED_HUMAN_POSITIVE]
        ),
        "completed_negative_event_count": event_counts[
            generic.COMPLETED_HUMAN_NEGATIVE
        ],
        "completed_negative_unit_count": len(
            status_units[generic.COMPLETED_HUMAN_NEGATIVE]
        ),
        "completed_total_event_count": event_counts[
            generic.COMPLETED_HUMAN_POSITIVE
        ]
        + event_counts[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_total_unit_count": len(completed_units),
        "in_progress_event_count": event_counts[generic.CURRENTLY_IN_PROGRESS],
        "in_progress_unit_count": len(
            status_units[generic.CURRENTLY_IN_PROGRESS]
        ),
        "unreviewed_event_count": event_counts[generic.CURRENTLY_UNREVIEWED],
        "unreviewed_unit_count": len(status_units[generic.CURRENTLY_UNREVIEWED]),
    }


def _independent_reconciliations(
    root: Path, projection: list[dict[str, object]]
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    generic.ReconciliationResult,
    generic.ReconciliationResult,
]:
    before_sources = predecessor.load_real_completed_decision_sources_with_6oa_v1(
        root
    )
    if len(before_sources) != 26:
        _fail("PREDECESSOR_SOURCE_API_NOT_EXACT26")
    binding = generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=17975,
        sha256="58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d",
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )
    pyr_source = generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(
            generic.NormalizedCompletedDecisionFact(**fact) for fact in projection
        ),
    )
    adapted = adapter._adapt_historical_v1(root)
    before = generic.reconcile_completed_human_decisions_v1(adapted, before_sources)
    after = generic.reconcile_completed_human_decisions_v1(
        adapted, (*before_sources, pyr_source)
    )
    return before_sources, before, after


def _verify_artifact_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    projection: list[dict[str, object]],
    independent_before: generic.ReconciliationResult,
    independent_after: generic.ReconciliationResult,
) -> dict[str, object]:
    if tuple(artifact) != _ARTIFACT_FIELDS:
        _fail("ARTIFACT_TOP_LEVEL_FIELDS_INVALID")
    for value, label in (
        (artifact.get("reconciled_rows"), "ROWS"),
        (artifact.get("source_bindings"), "BINDINGS"),
        (artifact.get("normalized_facts"), "FACTS"),
    ):
        if type(value) is not list:
            _fail("ARTIFACT_" + label + "_NOT_LIST")
    rows = artifact["reconciled_rows"]
    bindings = artifact["source_bindings"]
    facts = artifact["normalized_facts"]
    old_rows = predecessor_artifact.get("reconciled_rows")
    old_bindings = predecessor_artifact.get("source_bindings")
    old_facts = predecessor_artifact.get("normalized_facts")
    if (
        type(old_rows) is not list
        or type(old_bindings) is not list
        or type(old_facts) is not list
        or len(rows) != 338
        or len(bindings) != 27
        or len(facts) != 151
        or len(old_rows) != 338
        or len(old_bindings) != 26
        or len(old_facts) != 147
    ):
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if bindings[:26] != old_bindings:
        _fail("PREDECESSOR_SOURCE_PREFIX_INVALID")
    expected_binding = {
        "source_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": 17975,
        "sha256": "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d",
        "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
    }
    if bindings[26] != expected_binding or any(
        type(item) is not dict or tuple(item) != _SOURCE_BINDING_FIELDS
        for item in bindings
    ):
        _fail("PYR_SOURCE_BINDING_INVALID")
    identities = [
        f"{item['path_namespace']}:{item['source_path']}@{item['sha256']}"
        for item in bindings
    ]
    review_units = [item["review_unit_id"] for item in bindings]
    if len(set(identities)) != 27 or len(set(review_units)) != 27:
        _fail("ARTIFACT_SOURCE_IDENTITY_DUPLICATE")
    if facts[:147] != old_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if any(
        type(item) is not dict or tuple(item) != _GENERIC_FACT_FIELDS
        for item in facts
    ):
        _fail("ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    if facts[147:] != projection:
        _fail("PYR_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION")
    event_ids = [fact["canonical_event_id"] for fact in facts]
    if (
        len(set(event_ids)) != 151
        or event_ids[-4:] != list(ingestion.EXPECTED_EVENT_IDS)
        or any(event in set(event_ids[:147]) for event in ingestion.EXPECTED_EVENT_IDS)
    ):
        _fail("ARTIFACT_EVENT_UNIQUENESS_OR_APPEND_INVALID")
    predecessor_sources = (
        predecessor.load_real_completed_decision_sources_with_6oa_v1(ROOT)
    )
    expected_old_bindings = [asdict(source.binding) for source in predecessor_sources]
    expected_old_facts = [
        asdict(fact)
        for source in predecessor_sources
        for fact in source.facts
    ]
    if (
        predecessor_artifact.get("reconciled_rows")
        != [dict(row) for row in independent_before.reconciled_rows]
        or predecessor_artifact.get("review_summary")
        != independent_before.review_summary
        or predecessor_artifact.get("source_bindings") != expected_old_bindings
        or predecessor_artifact.get("normalized_facts") != expected_old_facts
    ):
        _fail("PREDECESSOR_ARTIFACT_NOT_REPRODUCED")
    if (
        rows != [dict(row) for row in independent_after.reconciled_rows]
        or artifact.get("review_summary") != independent_after.review_summary
    ):
        _fail("PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH")

    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(old_rows, rows, strict=True):
        event_id = old.get("canonical_event_id")
        if event_id not in targets:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old.get(key) != new.get(key)}
        if (
            old.get("raw_priority_rank") != "30"
            or old.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or old.get("raw_unit_event_count") != "4"
            or old.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or old.get("calibration_eligible") != "true"
            or old.get("calibration_exclusion_reason") != ""
            or changed != subject._ALLOWED_RECONCILIATION_FIELDS
            or new.get("current_review_status")
            != generic.COMPLETED_HUMAN_POSITIVE
            or new.get("current_status_authority_sources_json")
            != generic._canonical_json(
                [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
            )
            or new.get("calibration_eligible") != "false"
            or new.get("calibration_exclusion_reason")
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            _fail("PYR_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("RECONCILIATION_DELTA_NOT_EXACT4_ONLY")
    if (
        predecessor_artifact.get("review_summary")
        != _EXPECTED_PREDECESSOR_SUMMARY
        or artifact.get("review_summary") != _EXPECTED_SUCCESSOR_SUMMARY
        or _review_summary(rows) != _EXPECTED_SUCCESSOR_SUMMARY
    ):
        _fail("ARTIFACT_REVIEW_SUMMARY_INVALID")
    return {
        "source_count": 27,
        "accepted_fact_count": 151,
        "reconciled_row_count": 338,
        "generic_fact_field_count": 11,
        "rich_fields_leaked": False,
        "changed_target_rows": 4,
        "unchanged_rows": 334,
        "non_target_changed_rows": 0,
        "duplicate_count": 0,
    }


def _verify_coverage_contract(
    predecessor_facts: list[dict[str, object]],
    successor_facts: list[dict[str, object]],
    *,
    predecessor_coverage: dict[str, object] | None = None,
    successor_coverage: dict[str, object] | None = None,
) -> dict[str, dict[str, object]]:
    before = (
        subject.PREDECESSOR_COVERAGE_SUMMARY
        if predecessor_coverage is None
        else predecessor_coverage
    )
    after = (
        subject.SUCCESSOR_COVERAGE_SUMMARY
        if successor_coverage is None
        else successor_coverage
    )
    if (
        before != subject.PREDECESSOR_COVERAGE_SUMMARY
        or subject.PREDECESSOR_COVERAGE_SUMMARY
        != predecessor.SUCCESSOR_COVERAGE_SUMMARY
    ):
        _fail("PREDECESSOR_COVERAGE_DRIFT")
    if after != subject.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("SUCCESSOR_COVERAGE_DRIFT")
    before_distribution = before.get("decision_category_distribution")
    after_distribution = after.get("decision_category_distribution")
    if type(before_distribution) is not dict or type(after_distribution) is not dict:
        _fail("COVERAGE_DISTRIBUTION_NOT_OBJECT")
    for coverage, facts, source_count in (
        (before, predecessor_facts, 26),
        (after, successor_facts, 27),
    ):
        if (
            coverage.get("accepted_fact_count") != len(facts)
            or coverage.get("accepted_review_unit_count") != source_count
            or coverage.get("stable_source_identity_count") != source_count
            or coverage.get("remaining_unreviewed_chemistry_event_count")
            != 338 - len(facts)
            or coverage.get("remaining_unreviewed_review_unit_upper_bound")
            != 131 - source_count
            or coverage.get("label_ready_event_count") != 16
            or coverage.get("training_mask_target_count") != 0
            or coverage.get("training_authority") is not False
        ):
            _fail("COVERAGE_DIRECT_EVIDENCE_MISMATCH")
    appended = successor_facts[147:]
    if (
        sum(before_distribution.values()) != len(predecessor_facts)
        or sum(after_distribution.values()) != len(successor_facts)
        or after_distribution["chemistry_positive"]
        - before_distribution["chemistry_positive"]
        != 4
        or any(
            after_distribution[key] != before_distribution[key]
            for key in (
                "chemistry_negative",
                "task_domain_negative",
                "task_domain_positive",
            )
        )
        or successor_facts[:147] != predecessor_facts
        or len(appended) != 4
        or [fact.get("canonical_event_id") for fact in appended]
        != list(ingestion.EXPECTED_EVENT_IDS)
        or any(
            fact.get("legacy_completed_review_status")
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.get("task_relevance_disposition") != generic.TASK_RELEVANT
            or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
            or fact.get("training_disposition") != generic.TRAINING_EXCLUDE
            or fact.get("human_training_excluded") is not True
            for fact in appended
        )
        or after["label_ready_event_count"] != before["label_ready_event_count"]
        or after["training_mask_target_count"]
        != before["training_mask_target_count"]
    ):
        _fail("PYR_COVERAGE_DELTA_INVALID")
    return {"predecessor": before, "successor": after}


def _verify_operation_boundary(boundary: dict[str, object]) -> None:
    if boundary != _OPERATION_BOUNDARY:
        _fail("OPERATION_OR_TRAINING_BOUNDARY_INVALID")


def _verify_full_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    projection: list[dict[str, object]],
    independent_before: generic.ReconciliationResult,
    independent_after: generic.ReconciliationResult,
    operation_boundary: dict[str, object] | None = None,
    predecessor_coverage: dict[str, object] | None = None,
    successor_coverage: dict[str, object] | None = None,
) -> dict[str, object]:
    report = _verify_artifact_semantics(
        artifact,
        predecessor_artifact=predecessor_artifact,
        projection=projection,
        independent_before=independent_before,
        independent_after=independent_after,
    )
    _verify_coverage_contract(
        predecessor_artifact["normalized_facts"],
        artifact["normalized_facts"],
        predecessor_coverage=predecessor_coverage,
        successor_coverage=successor_coverage,
    )
    _verify_operation_boundary(
        copy.deepcopy(_OPERATION_BOUNDARY)
        if operation_boundary is None
        else operation_boundary
    )
    return report


def _verify_byte_identity(expected: bytes, observed: bytes) -> None:
    if expected != observed:
        _fail("MATERIALIZED_ARTIFACT_BYTES_MISMATCH")


def _expect_tamper(
    name: str, expected_token: str, callback: Callable[[], object]
) -> str:
    try:
        callback()
    except ValueError as error:
        text = str(error)
        required = "COVAPIE_PYR_RECONCILIATION_V1_ERROR:" + expected_token
        if required not in text:
            raise
        if (
            expected_token != "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"
            and "MATERIALIZED_ARTIFACT_BYTES_MISMATCH" in text
        ):
            raise
        return expected_token
    _fail("TAMPER_PROBE_DID_NOT_FAIL:" + name)


def _tamper_probes(
    artifact: dict[str, Any],
    old: dict[str, Any],
    projection: list[dict[str, object]],
    bound: dict[str, object],
    observed_payload: bytes,
    independent_before: generic.ReconciliationResult,
    independent_after: generic.ReconciliationResult,
) -> dict[str, str]:
    probes: dict[str, str] = {}

    def semantic(
        candidate: dict[str, Any],
        *,
        operations: dict[str, object] | None = None,
        before_coverage: dict[str, object] | None = None,
        after_coverage: dict[str, object] | None = None,
    ) -> None:
        _verify_full_semantics(
            candidate,
            predecessor_artifact=old,
            projection=projection,
            independent_before=independent_before,
            independent_after=independent_after,
            operation_boundary=operations,
            predecessor_coverage=before_coverage,
            successor_coverage=after_coverage,
        )

    def fact_probe(name: str, index: int, key: str, value: object, token: str) -> None:
        candidate = copy.deepcopy(artifact)
        candidate["normalized_facts"][index][key] = value
        probes[name] = _expect_tamper(name, token, lambda: semantic(candidate))

    def row_probe(name: str, index: int, key: str, value: str, token: str) -> None:
        candidate = copy.deepcopy(artifact)
        candidate["reconciled_rows"][index][key] = value
        probes[name] = _expect_tamper(name, token, lambda: semantic(candidate))

    def rich_probe(
        name: str, token: str, mutate: Callable[[dict[str, Any]], None]
    ) -> None:
        candidate = copy.deepcopy(bound)
        mutate(candidate)
        probes[name] = _expect_tamper(
            name, token, lambda: subject._project_bound_pyr_v1(candidate)
        )

    fact_token = "PYR_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION"
    fact_probe("legacy_status_negative", -1, "legacy_completed_review_status", generic.COMPLETED_HUMAN_NEGATIVE, fact_token)
    fact_probe("task_relevance_not_relevant", -1, "task_relevance_disposition", generic.TASK_NOT_RELEVANT, fact_token)
    fact_probe("chemistry_negative", -1, "chemistry_disposition", generic.CHEMISTRY_NEGATIVE, fact_token)
    fact_probe("training_include", -1, "training_disposition", generic.TRAINING_INCLUDE, fact_token)
    fact_probe("training_not_applicable", -1, "training_disposition", generic.TRAINING_NOT_APPLICABLE, fact_token)
    fact_probe("human_training_excluded_false", -1, "human_training_excluded", False, fact_token)
    fact_probe("wrong_authority_binding_path", -1, "source_binding_path", "wrong.json", fact_token)
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"].pop()
    probes["missing_pyr_event"] = _expect_tamper(
        "missing_pyr_event", "ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"].append(copy.deepcopy(candidate["normalized_facts"][-1]))
    probes["fifth_pyr_event"] = _expect_tamper(
        "fifth_pyr_event", "ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate)
    )
    fact_probe("duplicate_pyr_event", -1, "canonical_event_id", ingestion.EXPECTED_EVENT_IDS[0], fact_token)
    for name, field in (
        ("generic_schema_11_to_12", "twelfth_field"),
        ("pair_leak", "reactive_pair"),
        ("role_leak", "role_profile"),
        ("seed_leak", "minimal_seed"),
        ("task_id_leak", "applicable_task_ids"),
        ("geometry_leak", "geometry"),
    ):
        fact_probe(name, -1, field, "FORGED", "ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1], candidate["source_bindings"][-2] = (
        candidate["source_bindings"][-2],
        candidate["source_bindings"][-1],
    )
    probes["source_append_reordered"] = _expect_tamper(
        "source_append_reordered", "PREDECESSOR_SOURCE_PREFIX_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1] = copy.deepcopy(candidate["source_bindings"][0])
    probes["duplicate_source_identity"] = _expect_tamper(
        "duplicate_source_identity", "PYR_SOURCE_BINDING_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"][0]["source_decision_sha256"] = "0" * 64
    probes["predecessor_fact_modified"] = _expect_tamper(
        "predecessor_fact_modified", "PREDECESSOR_FACT_PREFIX_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"][-1], candidate["normalized_facts"][-2] = (
        candidate["normalized_facts"][-2],
        candidate["normalized_facts"][-1],
    )
    probes["fact_append_reordered"] = _expect_tamper(
        "fact_append_reordered", fact_token, lambda: semantic(candidate)
    )

    target_indices = [
        index
        for index, row in enumerate(artifact["reconciled_rows"])
        if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS
    ]
    if len(target_indices) != 4:
        _fail("TAMPER_TARGET_DISCOVERY_INVALID")
    non_target = next(
        index
        for index, row in enumerate(artifact["reconciled_rows"])
        if row.get("canonical_event_id") not in ingestion.EXPECTED_EVENT_IDS
    )
    row_probe("pyr_still_unreviewed", target_indices[0], "current_review_status", generic.CURRENTLY_UNREVIEWED, "PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH")
    row_probe("wrong_authority_source", target_indices[0], "current_status_authority_sources_json", "[]", "PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH")
    row_probe("calibration_still_eligible", target_indices[0], "calibration_eligible", "true", "PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH")
    row_probe("wrong_exclusion_reason", target_indices[0], "calibration_exclusion_reason", generic.TRAINING_EXCLUDE, "PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH")
    row_probe("non_target_changed", non_target, "raw_priority_rank", "999", "PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH")

    rich_probe(
        "source_D2_wrong",
        "PYR_D1_D6_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D2_task_generation_domain_relevance"
        ].__setitem__("decision", "OUT_OF_DOMAIN"),
    )
    rich_probe(
        "source_D2_missing",
        "PYR_D2_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"].pop(
            "D2_task_generation_domain_relevance"
        ),
    )
    rich_probe(
        "source_D6_include",
        "PYR_D1_D6_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D6_later_training_use_disposition"
        ].__setitem__("decision", "INCLUDE"),
    )
    rich_probe(
        "source_D6_not_applicable",
        "PYR_D1_D6_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D6_later_training_use_disposition"
        ].__setitem__("decision", "NOT_APPLICABLE"),
    )
    rich_probe(
        "source_D6_missing",
        "PYR_D6_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"].pop(
            "D6_later_training_use_disposition"
        ),
    )
    rich_probe(
        "source_human_training_excluded_false",
        "PYR_D1_D6_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D6_later_training_use_disposition"
        ].__setitem__("human_training_excluded", False),
    )
    rich_probe(
        "task_label_authority_forged",
        "PYR_NON_CREATED_AUTHORITY_INVALID",
        lambda value: value["formal_document"]["non_created_authority"].__setitem__(
            "task_label_authority", True
        ),
    )
    rich_probe(
        "formal_training_admitted_forged",
        "PYR_NON_CREATED_AUTHORITY_INVALID",
        lambda value: value["formal_document"]["non_created_authority"].__setitem__(
            "formal_training_admitted", True
        ),
    )
    rich_probe(
        "B3_missing",
        "PYR_EXACT5_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["selected_task_ids"][
            "canonical_V1_contract"
        ].__setitem__("B3_present", False),
    )
    rich_probe(
        "sixth_task_forged",
        "PYR_EXACT5_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["selected_task_ids"][
            "canonical_V1_contract"
        ].__setitem__("sixth_task", True),
    )

    for name, field, value in (
        ("positive_count_not_plus4", "completed_positive_event_count", 123),
        ("negative_count_wrong_plus4", "completed_negative_event_count", 52),
    ):
        candidate = copy.deepcopy(artifact)
        candidate["review_summary"][field] = value
        probes[name] = _expect_tamper(
            name, "PYR_GENERIC_RECONCILIATION_RESULT_MISMATCH", lambda candidate=candidate: semantic(candidate)
        )
    for name, field, value in (
        ("coverage_positive_not_plus4", "chemistry_positive", 99),
        ("coverage_task_domain_negative_wrong_plus4", "task_domain_negative", 32),
    ):
        coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
        coverage["decision_category_distribution"][field] = value
        probes[name] = _expect_tamper(
            name, "SUCCESSOR_COVERAGE_DRIFT", lambda coverage=coverage: semantic(artifact, after_coverage=coverage)
        )
    for name, field, value in (
        ("label_ready_increased", "label_ready_event_count", 20),
        ("training_mask_target_created", "training_mask_target_count", 4),
        ("training_authority_forged", "training_authority", True),
    ):
        coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
        coverage[field] = value
        probes[name] = _expect_tamper(
            name, "SUCCESSOR_COVERAGE_DRIFT", lambda coverage=coverage: semantic(artifact, after_coverage=coverage)
        )
    for name, field in (
        ("census_refresh_forged", "census_refresh_performed"),
        ("queue_refresh_forged", "queue_refresh_performed"),
        ("next_review_started_forged", "next_review_started"),
        ("event_task_labels_forged", "event_task_label_rows_materialized"),
        ("training_started_forged", "training_started"),
    ):
        operations = copy.deepcopy(_OPERATION_BOUNDARY)
        operations[field] = True
        probes[name] = _expect_tamper(
            name, "OPERATION_OR_TRAINING_BOUNDARY_INVALID", lambda operations=operations: semantic(artifact, operations=operations)
        )
    probes["raw_byte_corruption"] = _expect_tamper(
        "raw_byte_corruption",
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
        lambda: _verify_byte_identity(observed_payload, observed_payload + b" "),
    )
    probes["filesystem_executable_bit"] = _expect_tamper(
        "filesystem_executable_bit",
        "EXACT4_TEXT_SIZE_OR_MODE_INVALID",
        lambda: _validate_text_payload(b"ok\n", 0o755, "probe"),
    )
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    probes["unexpected_fifth_file"] = _expect_tamper(
        "unexpected_fifth_file",
        "CANDIDATE_UNTRACKED_NOT_STRICT_EXACT4",
        lambda: classify_repository_profile(
            expected_paths=paths,
            tracked_paths=set(),
            ordinary_untracked={*paths, "unexpected.txt"},
            status_lines=tuple([*("?? " + path for path in paths), "?? unexpected.txt"]),
            working_diff=set(),
            cached_diff=set(),
        ),
    )
    stage_lines = tuple(f"100644 {'0' * 40} 0\t{path}" for path in paths)
    bad_mode = list(stage_lines)
    bad_mode[0] = bad_mode[0].replace("100644", "100755", 1)
    probes["tracked_executable_mode"] = _expect_tamper(
        "tracked_executable_mode",
        "TRACKED_GIT_INDEX_MODE_INVALID",
        lambda: validate_tracked_index_modes(tuple(bad_mode), set(paths)),
    )
    bad_stage = list(stage_lines)
    bad_stage[0] = bad_stage[0].replace(" 0\t", " 1\t", 1)
    probes["tracked_nonzero_stage"] = _expect_tamper(
        "tracked_nonzero_stage",
        "TRACKED_GIT_INDEX_MODE_INVALID",
        lambda: validate_tracked_index_modes(tuple(bad_stage), set(paths)),
    )
    return probes


def _lifecycle_simulations() -> dict[str, bool]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    expected = set(paths)
    if (
        classify_repository_profile(
            expected_paths=paths,
            tracked_paths=set(),
            ordinary_untracked=expected,
            status_lines=tuple("?? " + path for path in paths),
            working_diff=set(),
            cached_diff=set(),
        )
        != CANDIDATE_UNTRACKED
    ):
        _fail("CANDIDATE_SIMULATION_FAILED")
    if (
        classify_repository_profile(
            expected_paths=paths,
            tracked_paths=expected,
            ordinary_untracked=set(),
            status_lines=(),
            working_diff=set(),
            cached_diff=set(),
        )
        != TRACKED_CLEAN
    ):
        _fail("TRACKED_SIMULATION_FAILED")
    stage_lines = tuple(f"100644 {'0' * 40} 0\t{path}" for path in paths)
    if validate_tracked_index_modes(stage_lines, expected) != {
        path: "100644" for path in paths
    }:
        _fail("TRACKED_GIT_INDEX_MODE_SIMULATION_FAILED")
    common = dict(
        profile=TRACKED_CLEAN,
        expected_paths=expected,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected,
    )
    validate_repository_relation_values(
        **common,
        head="successor",
        origin_main=BASELINE_COMMIT,
        ahead=1,
    )
    validate_repository_relation_values(
        **common, head="successor", origin_main="successor", ahead=0
    )
    validate_repository_relation_values(
        **{**common, "changed_since_baseline": {*expected, "docs/later.md"}},
        head="later",
        origin_main="successor",
        ahead=1,
    )
    return {
        "candidate_untracked": True,
        "tracked_clean": True,
        "committed_unpushed": True,
        "published_successor": True,
        "later_clean_descendant": True,
        "tracked_git_index_mode_100644": True,
    }


def check(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    repository = _verify_repository(root)
    dependencies = _verify_dependencies(root)
    formal_sources = _verify_external_formal_sources(root)
    exact4 = _verify_exact4_files(root)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    projection = _independent_expected_projection(bound)
    old = _strict_json(
        _read_regular(root / predecessor.OUTPUT_RELATIVE, "PREDECESSOR_ARTIFACT"),
        "PREDECESSOR_ARTIFACT",
    )
    observed_payload = _read_regular(root / subject.OUTPUT_RELATIVE, "PYR_ARTIFACT")
    artifact = _strict_json(observed_payload, "PYR_ARTIFACT")
    _before_sources, independent_before, independent_after = (
        _independent_reconciliations(root, projection)
    )
    artifact_report = _verify_full_semantics(
        artifact,
        predecessor_artifact=old,
        projection=projection,
        independent_before=independent_before,
        independent_after=independent_after,
    )
    coverage = _verify_coverage_contract(
        old["normalized_facts"], artifact["normalized_facts"]
    )
    first_build = subject.build_artifact_v1(root)
    second_build = subject.build_artifact_v1(root)
    _verify_byte_identity(first_build, observed_payload)
    if first_build != second_build:
        _fail("DETERMINISTIC_DOUBLE_BUILD_MISMATCH")
    materialized = subject.check_materialized_v1(root)
    tamper = _tamper_probes(
        artifact,
        old,
        projection,
        bound,
        observed_payload,
        independent_before,
        independent_after,
    )
    lifecycle = _lifecycle_simulations()
    if not (
        materialized.get("status") == "PASS"
        and subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False
        and repository["lifecycle"] in {CANDIDATE_UNTRACKED, TRACKED_CLEAN}
        and repository["expected_git_publication_mode"] == "100644"
        and (
            repository["git_index_mode_checked"] is False
            if repository["lifecycle"] == CANDIDATE_UNTRACKED
            else repository["git_index_mode_checked"] is True
        )
    ):
        _fail("FINAL_READINESS_BOUNDARY_INVALID")
    return {
        "status": "PASS",
        "repository": repository,
        "dependencies": dependencies,
        "formal_sources": formal_sources,
        "Exact4_files": exact4,
        "artifact": artifact_report,
        "source_chain": {
            "predecessor_sources": 26,
            "successor_sources": 27,
            "predecessor_facts": 147,
            "successor_facts": 151,
            "prefix_preserved": True,
        },
        "PYR_boundary": {
            "event_count": 4,
            "source_D2": "IN_DOMAIN",
            "normalized_task_relevance": generic.TASK_RELEVANT,
            "source_D6": "EXCLUDE",
            "normalized_training_disposition": generic.TRAINING_EXCLUDE,
            "legacy_status": generic.COMPLETED_HUMAN_POSITIVE,
            "chemistry": generic.CHEMISTRY_POSITIVE,
            "human_training_excluded": True,
            "pair": "SG:CB",
            "B3_present": True,
            "sixth_task": False,
            "task_label_authority": False,
            "formal_training_admitted": False,
        },
        "review_summary": {
            "predecessor": old["review_summary"],
            "successor": artifact["review_summary"],
        },
        "coverage": coverage,
        "materialized_check": materialized,
        "tamper_probes": tamper,
        "lifecycle_simulations": lifecycle,
        "materialized_equals_fresh_build": observed_payload == first_build,
        "deterministic_double_build": first_build == second_build,
        "operation_boundary": copy.deepcopy(_OPERATION_BOUNDARY),
        "Step12D_status": (
            "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
        ),
    }


def main() -> int:
    try:
        report = check(ROOT)
    except Exception as error:
        print("COVAPIE_PYR_COMPLETED_DECISION_RECONCILIATION_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("COVAPIE_PYR_COMPLETED_DECISION_RECONCILIATION_V1_PASS=true")
    print("lifecycle=" + str(report["repository"]["lifecycle"]))
    print("PREDECESSOR_SOURCE_COUNT=26")
    print("SUCCESSOR_SOURCE_COUNT=27")
    print("PREDECESSOR_ACCEPTED_FACT_COUNT=147")
    print("SUCCESSOR_ACCEPTED_FACT_COUNT=151")
    print("CHANGED_TARGET_ROWS=4")
    print("NON_TARGET_CHANGED_ROWS=0")
    print("UNCHANGED_ROWS=334")
    print("LEGACY_COMPLETED_REVIEW_STATUS=COMPLETED_HUMAN_POSITIVE")
    print("NORMALIZED_TRAINING_DISPOSITION=EXCLUDE_FROM_TRAINING_ONLY")
    print("HUMAN_TRAINING_EXCLUDED=true")
    print("RECONCILIATION_PERFORMED=true")
    print("CENSUS_REFRESH_PERFORMED=false")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("NEXT_REVIEW_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
