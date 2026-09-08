#!/usr/bin/env python3
"""Independent fail-closed checker for the ME7 reconciliation Exact4."""

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
from covalent_ext import covapie_completed_human_decision_reconciliation_with_me7_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_pyr_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_tp2_v1 as adapter  # noqa: E402
from covalent_ext import covapie_me7_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


BASELINE_COMMIT = "64806eb163fcb944e9ad6940f0729c832c60695f"
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
        "WITH_PYR_PREDECESSOR_OWNER",
        predecessor.SOURCE_RELATIVE.as_posix(),
        35637,
        "a25fbeb8d467481ce45b7d652380e094d153c46963d30a1a10fcc2e0036f0e0a",
    ),
    (
        "WITH_PYR_PREDECESSOR_ARTIFACT",
        predecessor.OUTPUT_RELATIVE.as_posix(),
        348380,
        "6af7efb056f136b7c55f5a5e520f8bfd907992f3758d1b9516694959dab117d2",
    ),
    (
        "HISTORICAL_ADAPTER_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_tp2_v1.py",
        26679,
        "d9bd34e780323535056100b5a11956bf9c6965ed5d58c8aa2c20f8f33a6938fe",
    ),
    (
        "ME7_INGESTION_OWNER",
        ingestion.SOURCE_RELATIVE.as_posix(),
        128401,
        "57902f3218578171313f69b236ba2e0f5ddec981c0297b6f4e3c67f74f2a68f8",
    ),
    (
        "ME7_INGESTION_SNAPSHOT",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SNAPSHOT).as_posix(),
        59322,
        "f9ff426a2c821bfd0272ed5e06854a5217f27eece1bf4b6a97ebc96e7b80da86",
    ),
    (
        "ME7_INGESTION_MATRIX",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX).as_posix(),
        4698,
        "29051be7afbc5aaa3c681e42d9f537234be1b5d67d503c795c612c1af9187c6e",
    ),
    (
        "ME7_INGESTION_SUMMARY",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SUMMARY).as_posix(),
        6954,
        "9ec118403bf158de59c4ae954d8b3d590f3d1f43b4f3e6b73e1e1399cbfa9895",
    ),
    (
        "ME7_INGESTION_MANIFEST",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MANIFEST).as_posix(),
        28528,
        "2cadebe59c4cc5f356f11464858e45366be1b0395cd54c59fb82ed63c3ec041a",
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
)
PROTECTED_FILES = {
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
    *(relative for _role, relative, _size, _digest in DEPENDENCY_BINDINGS),
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
_FORBIDDEN_RICH_FIELDS = subject._FORBIDDEN_RICH_FACT_FIELDS
_EXPECTED_PREDECESSOR_SUMMARY = {
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
_EXPECTED_SUCCESSOR_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 127,
    "completed_positive_unit_count": 21,
    "completed_negative_event_count": 51,
    "completed_negative_unit_count": 11,
    "completed_total_event_count": 178,
    "completed_total_unit_count": 32,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 160,
    "unreviewed_unit_count": 99,
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
    "training_materialization_allowed": False,
    "feature_semantics_audit_performed": False,
    "feature_semantics_audit_required_before_training": True,
    "step12d_is_only_smoke_legality_check": True,
    "ready_for_training": False,
    "training_started": False,
    "commit_performed": False,
    "push_performed": False,
}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_ME7_RECONCILIATION_V1_ERROR:" + token)


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


def _git_process(root: Path, *arguments: str) -> subprocess.CompletedProcess[Any]:
    if not arguments or arguments[0] not in {
        "diff",
        "ls-files",
        "merge-base",
        "rev-list",
        "rev-parse",
        "show",
        "status",
    }:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    return subprocess.run(
        ("git", *arguments), cwd=root, capture_output=True, check=False
    )


def _git(root: Path, *arguments: str) -> str:
    process = _git_process(root, *arguments)
    if process.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    try:
        return process.stdout.decode("utf-8").rstrip("\n")
    except UnicodeDecodeError as error:
        raise ValueError("GIT_STDOUT_NOT_UTF8:" + arguments[0]) from error


def _git_bytes(root: Path, *arguments: str) -> bytes:
    process = _git_process(root, *arguments)
    if process.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return process.stdout


def _ancestor(root: Path, older: str, newer: str) -> bool:
    process = _git_process(root, "merge-base", "--is-ancestor", older, newer)
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
    if _git(root, "diff", "--check") or _git(root, "diff", "--cached", "--check"):
        _fail("GIT_DIFF_CHECK_FAILED")
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
        "profile": profile,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "conflicted_count": 0,
        "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": sorted(untracked),
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
        report["git_index_record_count"] = len(stage_lines)
        report["git_index_modes"] = validate_tracked_index_modes(
            stage_lines, set(paths)
        )
    return report


def _verify_dependencies(root: Path) -> list[dict[str, object]]:
    reports = []
    for role, relative, byte_count, digest in DEPENDENCY_BINDINGS:
        payload = _read_regular(root / relative, role)
        baseline_payload = _git_bytes(root, "show", f"{BASELINE_COMMIT}:{relative}")
        if (
            len(payload) != byte_count
            or _sha256(payload) != digest
            or baseline_payload != payload
        ):
            _fail("PUBLISHED_DEPENDENCY_OR_BASELINE_BLOB_DRIFT:" + role)
        reports.append(
            {
                "role": role,
                "path": relative,
                "bytes": len(payload),
                "SHA256": digest,
                "working_equals_baseline_blob": True,
            }
        )
    return reports


def _verify_external_formal_sources(root: Path) -> list[dict[str, object]]:
    expected = (
        (
            "ME7_FORMAL_JSON",
            ingestion.FORMAL_DECISION_RELATIVE,
            13344,
            "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407",
        ),
        (
            "ME7_FORMAL_VALIDATOR_PROVENANCE_ONLY",
            ingestion.FORMAL_VALIDATOR_RELATIVE,
            52865,
            "67a68f9b1c14cb90591a6e377c4fc680cc816c53e138995adf0c1544eaf91009",
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
    formal = _mapping(bound.get("formal_document"), "ME7_FORMAL_NOT_OBJECT")
    identity = _mapping(formal.get("sample_identity"), "ME7_IDENTITY_INVALID")
    authority = _mapping(
        formal.get("sample_level_authority"), "ME7_AUTHORITY_INVALID"
    )
    decisions = _mapping(formal.get("approved_D1_D6"), "ME7_D1_D6_INVALID")
    d1 = _mapping(
        decisions.get("D1_observation_record_judgment"), "ME7_D1_INVALID"
    )
    d2 = _mapping(decisions.get("D2_project_domain_relevance"), "ME7_D2_INVALID")
    d3 = _mapping(
        decisions.get("D3_recorded_endpoint_confirmation"), "ME7_D3_INVALID"
    )
    d4 = _mapping(
        decisions.get("D4_role_partition_and_retained_information"),
        "ME7_D4_INVALID",
    )
    d5 = _mapping(
        decisions.get("D5_structural_task_applicability"), "ME7_D5_INVALID"
    )
    d6 = _mapping(decisions.get("D6_later_use_disposition"), "ME7_D6_INVALID")
    roles = _mapping(
        formal.get("role_and_task_disposition"), "ME7_ROLE_TASK_INVALID"
    )
    non_created = _mapping(
        formal.get("non_created_authority"), "ME7_NON_CREATED_INVALID"
    )
    readiness = _mapping(formal.get("readiness"), "ME7_READINESS_INVALID")
    operations = _mapping(
        formal.get("operation_boundary"), "ME7_FORMAL_OPERATION_INVALID"
    )
    binding = _mapping(
        bound.get("formal_decision_binding"), "ME7_FORMAL_BINDING_INVALID"
    )
    validator = _mapping(
        bound.get("formal_validator_binding"), "ME7_VALIDATOR_BINDING_INVALID"
    )
    compatibility = _mapping(
        bound.get("generic_Exact11_compatibility"), "ME7_GENERIC_BOUND_INVALID"
    )
    census = _mapping(
        bound.get("current_census_and_queue_boundary"),
        "ME7_CENSUS_QUEUE_BOUND_INVALID",
    )
    events = bound.get("events")
    context = bound.get("context_only_graph_records")
    all_scope = bound.get("all_me7_scope_rows")
    source_path = ingestion.FORMAL_DECISION_RELATIVE.as_posix()
    false_authority_keys = {
        "TASK_LABEL_AUTHORITY",
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED",
        "MASK_TENSOR_TARGETS_CREATED",
        "FORMAL_TRAINING_ADMITTED",
        "TRAINING_MATERIALIZATION_ALLOWED",
        "PARAMETER_UPDATE_AUTHORIZATION",
        "READY_FOR_TRAINING",
        "TRAINING_STARTED",
    }
    null_role_keys = {
        "applicable_task_ids",
        "selected_candidate_id",
        "selected_role_candidate",
        "role_profile",
        "warhead_atom_ids",
        "linker_atom_ids",
        "scaffold_atom_ids",
        "minimal_seed",
        "minimal_seed_atom_ids",
        "primary_anchor",
    }
    if (
        formal.get("schema_version") != ingestion.FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != ingestion.FORMAL_RECORD_ROLE
        or identity.get("ligand_component_id") != "ME7"
        or identity.get("review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
        or identity.get("scope") != ingestion.EXPECTED_SCOPE
        or identity.get("target_event_count") != 3
        or identity.get("canonical_target_event_ids")
        != list(ingestion.EXPECTED_EVENT_IDS)
        or identity.get("target_scaleup_ranks") != list(ingestion.EXPECTED_RANKS)
        or identity.get("pdb_ids") != ["3QVY", "3QVZ"]
        or authority.get("approved") is not True
        or authority.get("human_review_completed") is not True
        or authority.get("sample_chemistry_authority") is not True
        or authority.get("sample_task_domain_authority") is not True
        or authority.get("sample_pair_authority") is not True
        or authority.get("role_partition_sample_authoritative") is not False
        or authority.get("task_applicability_sample_authoritative") is not False
        or d1.get("decision") != "POSITIVE"
        or d1.get("human_approved") is not True
        or d2.get("decision") != "OUT_OF_DOMAIN"
        or d2.get("chemistry_positive_is_preserved") is not True
        or d2.get("human_approved") is not True
        or d3.get("decision") != "CONFIRM_OBSERVED_PAIR"
        or d3.get("pair") != "SG:CAE"
        or d3.get("protein_atom") != "SG"
        or d3.get("component_atom") != "CAE"
        or d3.get("target_pair_is_only_attachment_for_component_instance")
        is not False
        or d4.get("decision") != "CANNOT_DETERMINE"
        or d4.get("selected_candidate_id") is not None
        or d4.get("role_candidate_count") != 0
        or d5.get("decision") != "NOT_DETERMINABLE"
        or d5.get("task_ids") is not None
        or d6.get("decision") != "NOT_APPLICABLE"
        or d6.get("human_training_excluded") is not False
        or d6.get("formal_training_admitted") is not False
        or d6.get("future_training_admission_candidate") is not False
        or any(roles.get(key) is not None for key in null_role_keys)
        or roles.get("role_candidate_count") != 0
        or roles.get("role_runtime_executed") is not False
        or roles.get("task_runtime_executed") is not False
        or roles.get("canonical_v1_task_count") != 5
        or roles.get("B3_present") is not True
        or roles.get("sixth_task_created") is not False
        or [
            row.get("semantic_long_name")
            for row in roles.get("canonical_v1_tasks", [])
            if type(row) is dict
        ]
        != [row[1] for row in ingestion.CANONICAL_TASKS]
        or any(non_created.get(key) is not False for key in false_authority_keys)
        or readiness.get("FEATURE_SEMANTICS_AUDIT_PERFORMED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING")
        is not True
        or readiness.get("STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK") is not True
        or operations.get("reconciliation_performed") is not False
        or operations.get("census_refresh_performed") is not False
        or operations.get("queue_refresh_performed") is not False
        or operations.get("training_performed") is not False
        or binding.get("path") != source_path
        or binding.get("path_namespace") != "project_parent_relative"
        or binding.get("byte_count") != 13344
        or binding.get("SHA256")
        != "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407"
        or validator.get("byte_count") != 52865
        or validator.get("SHA256")
        != "67a68f9b1c14cb90591a6e377c4fc680cc816c53e138995adf0c1544eaf91009"
        or validator.get("validation_method")
        != "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        or compatibility.get("completed_lane")
        != "COMPLETED_TASK_DOMAIN_NEGATIVE"
        or compatibility.get("source_formal_D2") != "OUT_OF_DOMAIN"
        or compatibility.get("normalized_task_relevance_disposition")
        != generic.TASK_NOT_RELEVANT
        or compatibility.get("source_formal_D6") != "NOT_APPLICABLE"
        or compatibility.get("normalized_training_disposition")
        != generic.TRAINING_NOT_APPLICABLE
        or compatibility.get("accepted_fact_count") != 3
        or compatibility.get("rich_fields_leaked") is not False
        or census.get("ME7_priority_rank") != 32
        or census.get("ME7_current_review_status") != generic.CURRENTLY_UNREVIEWED
        or census.get("ME7_human_review_completed") is not False
        or census.get("ME7_structurally_applicable_task_ids") is not None
        or type(events) is not list
        or [
            (row.get("canonical_event_id"), row.get("scaleup_rank"), row.get("pdb_id"))
            for row in events
            if type(row) is dict
        ]
        != list(
            zip(
                ingestion.EXPECTED_EVENT_IDS,
                ingestion.EXPECTED_RANKS,
                ("3QVY", "3QVY", "3QVZ"),
                strict=True,
            )
        )
        or type(context) is not list
        or len(context) != 3
        or {row.get("scaleup_rank") for row in context if type(row) is dict}
        != {527, 530, 533}
        or any(
            type(row) is not dict
            or row.get("target_event") is not False
            or row.get("supporting_context_only") is not True
            for row in context
        )
        or type(all_scope) is not list
        or [
            row.get("canonical_event_id")
            for row in all_scope
            if type(row) is dict and row.get("target_event") is True
        ]
        != list(ingestion.EXPECTED_EVENT_IDS)
    ):
        _fail("ME7_INDEPENDENT_PROJECTION_BOUNDARY_INVALID")
    expected = [
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": False,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding["SHA256"],
            "source_binding_path": source_path,
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    ]
    if (
        any(tuple(fact) != _GENERIC_FACT_FIELDS for fact in expected)
        or compatibility.get("facts") != expected
    ):
        _fail("ME7_INDEPENDENT_PROJECTION_NOT_VALIDATED_EXACT3_EXACT11")
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
        "in_progress_unit_count": len(status_units[generic.CURRENTLY_IN_PROGRESS]),
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
    before_sources = predecessor.load_real_completed_decision_sources_with_pyr_v1(
        root
    )
    before_facts = tuple(
        fact for source in before_sources for fact in source.facts
    )
    if len(before_sources) != 27 or len(before_facts) != 151:
        _fail("PREDECESSOR_SOURCE_API_NOT_EXACT27_151")
    binding = generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=13344,
        sha256="9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407",
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )
    me7_source = generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(
            generic.NormalizedCompletedDecisionFact(**fact) for fact in projection
        ),
    )
    adapted = adapter._adapt_historical_v1(root)
    before = generic.reconcile_completed_human_decisions_v1(adapted, before_sources)
    published_before = (
        predecessor.reconcile_real_completed_human_decisions_with_pyr_v1(root)
    )
    if before != published_before:
        _fail("PREDECESSOR_NOT_REPRODUCED_FROM_ADAPTED_HISTORICAL_ROWS")
    after = generic.reconcile_completed_human_decisions_v1(
        adapted, (*before_sources, me7_source)
    )
    return before_sources, before, after


def _verify_artifact_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    projection: list[dict[str, object]],
    predecessor_sources: tuple[generic.NormalizedDecisionSource, ...],
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
        or len(bindings) != 28
        or len(facts) != 154
        or len(old_rows) != 338
        or len(old_bindings) != 27
        or len(old_facts) != 151
    ):
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if bindings[:27] != old_bindings:
        _fail("PREDECESSOR_SOURCE_PREFIX_INVALID")
    expected_binding = {
        "source_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": 13344,
        "sha256": "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407",
        "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
    }
    if bindings[27] != expected_binding or any(
        type(item) is not dict or tuple(item) != _SOURCE_BINDING_FIELDS
        for item in bindings
    ):
        _fail("ME7_SOURCE_BINDING_INVALID")
    identities = [
        f"{item['path_namespace']}:{item['source_path']}@{item['sha256']}"
        for item in bindings
    ]
    units = [item["review_unit_id"] for item in bindings]
    if len(set(identities)) != 28 or len(set(units)) != 28:
        _fail("ARTIFACT_SOURCE_IDENTITY_DUPLICATE")
    if facts[:151] != old_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if any(
        type(item) is not dict or tuple(item) != _GENERIC_FACT_FIELDS
        for item in facts
    ):
        _fail("ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    if any(_FORBIDDEN_RICH_FIELDS & set(item) for item in facts):
        _fail("ARTIFACT_RICH_FIELD_LEAKED")
    if facts[151:] != projection:
        _fail("ME7_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION")
    event_ids = [fact["canonical_event_id"] for fact in facts]
    if (
        len(set(event_ids)) != 154
        or event_ids[-3:] != list(ingestion.EXPECTED_EVENT_IDS)
        or set(event_ids[:151]) & set(ingestion.EXPECTED_EVENT_IDS)
    ):
        _fail("ARTIFACT_EVENT_UNIQUENESS_OR_APPEND_INVALID")
    expected_old_bindings = [asdict(source.binding) for source in predecessor_sources]
    expected_old_facts = [
        asdict(fact) for source in predecessor_sources for fact in source.facts
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
        _fail("ME7_GENERIC_RECONCILIATION_RESULT_MISMATCH")

    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(old_rows, rows, strict=True):
        if old.get("canonical_event_id") not in targets:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old.get(key) != new.get(key)}
        if (
            old.get("raw_priority_rank") != "32"
            or old.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or old.get("raw_unit_event_count") != "3"
            or old.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or old.get("calibration_eligible") != "true"
            or old.get("calibration_exclusion_reason") != ""
            or changed != subject._ALLOWED_RECONCILIATION_FIELDS
            or new.get("current_review_status")
            != generic.COMPLETED_HUMAN_NEGATIVE
            or new.get("current_status_authority_sources_json")
            != generic._canonical_json(
                [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
            )
            or new.get("calibration_eligible") != "false"
            or new.get("calibration_exclusion_reason")
            != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("ME7_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (3, 0):
        _fail("RECONCILIATION_DELTA_NOT_EXACT3_ONLY")
    if (
        predecessor_artifact.get("review_summary")
        != _EXPECTED_PREDECESSOR_SUMMARY
        or artifact.get("review_summary") != _EXPECTED_SUCCESSOR_SUMMARY
        or _review_summary(rows) != _EXPECTED_SUCCESSOR_SUMMARY
    ):
        _fail("ARTIFACT_REVIEW_SUMMARY_INVALID")
    return {
        "source_count": 28,
        "accepted_fact_count": 154,
        "reconciled_row_count": 338,
        "generic_fact_field_count": 11,
        "rich_fields_leaked": False,
        "changed_target_rows": 3,
        "unchanged_rows": 335,
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
        (before, predecessor_facts, 27),
        (after, successor_facts, 28),
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
    appended = successor_facts[151:]
    if (
        sum(before_distribution.values()) != len(predecessor_facts)
        or sum(after_distribution.values()) != len(successor_facts)
        or after_distribution["task_domain_negative"]
        - before_distribution["task_domain_negative"]
        != 3
        or any(
            after_distribution[key] != before_distribution[key]
            for key in (
                "chemistry_positive",
                "chemistry_negative",
                "task_domain_positive",
            )
        )
        or successor_facts[:151] != predecessor_facts
        or len(appended) != 3
        or [fact.get("canonical_event_id") for fact in appended]
        != list(ingestion.EXPECTED_EVENT_IDS)
        or any(
            fact.get("legacy_completed_review_status")
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.get("task_relevance_disposition")
            != generic.TASK_NOT_RELEVANT
            or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
            or fact.get("training_disposition")
            != generic.TRAINING_NOT_APPLICABLE
            or fact.get("human_training_excluded") is not False
            for fact in appended
        )
        or after["label_ready_event_count"] != before["label_ready_event_count"]
        or after["training_mask_target_count"]
        != before["training_mask_target_count"]
    ):
        _fail("ME7_COVERAGE_DELTA_INVALID")
    return {"predecessor": before, "successor": after}


def _verify_operation_boundary(boundary: dict[str, object]) -> None:
    if boundary != _OPERATION_BOUNDARY:
        _fail("OPERATION_OR_TRAINING_BOUNDARY_INVALID")


def _verify_full_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    projection: list[dict[str, object]],
    predecessor_sources: tuple[generic.NormalizedDecisionSource, ...],
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
        predecessor_sources=predecessor_sources,
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
        expected = "COVAPIE_ME7_RECONCILIATION_V1_ERROR:" + expected_token
        if str(error) != expected:
            raise
        return expected_token
    _fail("TAMPER_PROBE_DID_NOT_FAIL:" + name)


def _tamper_probes(
    artifact: dict[str, Any],
    old: dict[str, Any],
    projection: list[dict[str, object]],
    bound: dict[str, object],
    observed_payload: bytes,
    predecessor_sources: tuple[generic.NormalizedDecisionSource, ...],
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
            predecessor_sources=predecessor_sources,
            independent_before=independent_before,
            independent_after=independent_after,
            operation_boundary=operations,
            predecessor_coverage=before_coverage,
            successor_coverage=after_coverage,
        )

    def fact_probe(name: str, key: str, value: object, token: str) -> None:
        candidate = copy.deepcopy(artifact)
        candidate["normalized_facts"][-1][key] = value
        probes[name] = _expect_tamper(name, token, lambda: semantic(candidate))

    def rich_probe(
        name: str, token: str, mutate: Callable[[dict[str, Any]], None]
    ) -> None:
        candidate = copy.deepcopy(bound)
        mutate(candidate)
        probes[name] = _expect_tamper(
            name, token, lambda: _independent_expected_projection(candidate)
        )

    fact_token = "ME7_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION"
    for name, key, value in (
        ("wrong_event", "canonical_event_id", "WRONG_EVENT"),
        ("wrong_unit", "review_unit_id", "WRONG_UNIT"),
        ("wrong_schema", "source_decision_schema", "wrong_schema"),
        ("wrong_digest", "source_decision_sha256", "0" * 64),
        ("wrong_formal_path", "source_binding_path", "wrong.json"),
        (
            "legacy_positive",
            "legacy_completed_review_status",
            generic.COMPLETED_HUMAN_POSITIVE,
        ),
        ("normalized_relevant", "task_relevance_disposition", generic.TASK_RELEVANT),
        ("chemistry_negative", "chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("training_exclude", "training_disposition", generic.TRAINING_EXCLUDE),
        ("human_excluded_true", "human_training_excluded", True),
    ):
        fact_probe(name, key, value, fact_token)
    for name, key in (
        ("pair_leak", "reactive_pair"),
        ("role_leak", "role_profile"),
        ("seed_leak", "minimal_seed"),
        ("task_ids_leak", "applicable_task_ids"),
        ("geometry_leak", "geometry"),
    ):
        fact_probe(name, key, "FORGED", "ARTIFACT_GENERIC_FACT_NOT_EXACT11")

    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"].pop()
    probes["missing_target"] = _expect_tamper(
        "missing_target", "ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"].append(
        copy.deepcopy(candidate["normalized_facts"][-1])
    )
    probes["fourth_target"] = _expect_tamper(
        "fourth_target", "ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"][-1] = copy.deepcopy(
        candidate["normalized_facts"][-2]
    )
    probes["duplicate_target"] = _expect_tamper(
        "duplicate_target", fact_token, lambda: semantic(candidate)
    )
    context_id = bound["context_only_graph_records"][0]["canonical_event_id"]
    fact_probe("context_only_added", "canonical_event_id", context_id, fact_token)
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1], candidate["source_bindings"][-2] = (
        candidate["source_bindings"][-2],
        candidate["source_bindings"][-1],
    )
    probes["source_prefix_reordered"] = _expect_tamper(
        "source_prefix_reordered",
        "PREDECESSOR_SOURCE_PREFIX_INVALID",
        lambda: semantic(candidate),
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"][0]["source_decision_sha256"] = "0" * 64
    probes["fact_prefix_modified"] = _expect_tamper(
        "fact_prefix_modified",
        "PREDECESSOR_FACT_PREFIX_INVALID",
        lambda: semantic(candidate),
    )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1] = copy.deepcopy(
        candidate["source_bindings"][0]
    )
    probes["duplicate_source"] = _expect_tamper(
        "duplicate_source", "ME7_SOURCE_BINDING_INVALID", lambda: semantic(candidate)
    )

    target_index = next(
        index
        for index, row in enumerate(artifact["reconciled_rows"])
        if row["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS
    )
    non_target_index = next(
        index
        for index, row in enumerate(artifact["reconciled_rows"])
        if row["canonical_event_id"] not in ingestion.EXPECTED_EVENT_IDS
    )
    for name, index, key, value in (
        (
            "target_still_pending",
            target_index,
            "current_review_status",
            generic.CURRENTLY_UNREVIEWED,
        ),
        (
            "not_applicable_as_exclusion_reason",
            target_index,
            "calibration_exclusion_reason",
            generic.TRAINING_NOT_APPLICABLE,
        ),
        ("non_target_changed", non_target_index, "raw_priority_rank", "999"),
    ):
        candidate = copy.deepcopy(artifact)
        candidate["reconciled_rows"][index][key] = value
        probes[name] = _expect_tamper(
            name,
            "ME7_GENERIC_RECONCILIATION_RESULT_MISMATCH",
            lambda candidate=candidate: semantic(candidate),
        )

    for name, field, value in (
        ("positive_summary_plus3", "completed_positive_event_count", 130),
        ("negative_summary_not_plus3", "completed_negative_event_count", 48),
    ):
        candidate = copy.deepcopy(artifact)
        candidate["review_summary"][field] = value
        probes[name] = _expect_tamper(
            name,
            "ME7_GENERIC_RECONCILIATION_RESULT_MISMATCH",
            lambda candidate=candidate: semantic(candidate),
        )
    for name, field, value in (
        ("coverage_double_count_chemistry", "chemistry_positive", 106),
        ("coverage_task_negative_not_plus3", "task_domain_negative", 28),
    ):
        coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
        coverage["decision_category_distribution"][field] = value
        probes[name] = _expect_tamper(
            name,
            "SUCCESSOR_COVERAGE_DRIFT",
            lambda coverage=coverage: semantic(artifact, after_coverage=coverage),
        )
    for name, field, value in (
        ("coverage_wrong_population", "remaining_unreviewed_chemistry_event_count", 160),
        ("label_ready_increased", "label_ready_event_count", 19),
        ("training_mask_created", "training_mask_target_count", 3),
        ("training_authority_forged", "training_authority", True),
    ):
        coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
        coverage[field] = value
        probes[name] = _expect_tamper(
            name,
            "SUCCESSOR_COVERAGE_DRIFT",
            lambda coverage=coverage: semantic(artifact, after_coverage=coverage),
        )
    for name, field in (
        ("census_refresh_forged", "census_refresh_performed"),
        ("queue_refresh_forged", "queue_refresh_performed"),
        ("next_review_started_forged", "next_review_started"),
        ("task_label_authority_forged", "task_label_authority"),
        ("training_started_forged", "training_started"),
    ):
        operations = copy.deepcopy(_OPERATION_BOUNDARY)
        operations[field] = True
        probes[name] = _expect_tamper(
            name,
            "OPERATION_OR_TRAINING_BOUNDARY_INVALID",
            lambda operations=operations: semantic(artifact, operations=operations),
        )

    rich_probe(
        "formal_D2_changed",
        "ME7_INDEPENDENT_PROJECTION_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D2_project_domain_relevance"
        ].__setitem__("decision", "IN_DOMAIN"),
    )
    rich_probe(
        "formal_D4_role_forged",
        "ME7_INDEPENDENT_PROJECTION_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D4_role_partition_and_retained_information"
        ].__setitem__("selected_candidate_id", "FORGED"),
    )
    rich_probe(
        "formal_D5_task_forged",
        "ME7_INDEPENDENT_PROJECTION_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["approved_D1_D6"][
            "D5_structural_task_applicability"
        ].__setitem__("task_ids", [0]),
    )
    rich_probe(
        "formal_review_incomplete",
        "ME7_INDEPENDENT_PROJECTION_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["sample_level_authority"].__setitem__(
            "human_review_completed", False
        ),
    )
    probes["raw_byte_corruption"] = _expect_tamper(
        "raw_byte_corruption",
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
        lambda: _verify_byte_identity(observed_payload, observed_payload + b" "),
    )
    probes["filesystem_executable_bit"] = _expect_tamper(
        "filesystem_executable_bit",
        "EXACT4_TEXT_SIZE_OR_MODE_INVALID:probe",
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
            status_lines=tuple(
                [*("?? " + path for path in paths), "?? unexpected.txt"]
            ),
            working_diff=set(),
            cached_diff=set(),
        ),
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
        or classify_repository_profile(
            expected_paths=paths,
            tracked_paths=expected,
            ordinary_untracked=set(),
            status_lines=(),
            working_diff=set(),
            cached_diff=set(),
        )
        != TRACKED_CLEAN
    ):
        _fail("LIFECYCLE_PROFILE_SIMULATION_FAILED")
    stage_lines = tuple(f"100644 {'0' * 40} 0\t{path}" for path in reversed(paths))
    if validate_tracked_index_modes(stage_lines, expected) != {
        path: "100644" for path in paths
    }:
        _fail("TRACKED_GIT_INDEX_MODE_SIMULATION_FAILED")
    for name, bad_lines in (
        ("missing", stage_lines[:-1]),
        ("duplicate", (*stage_lines[:-1], stage_lines[0])),
        ("executable", (stage_lines[0].replace("100644", "100755", 1), *stage_lines[1:])),
        ("symlink", (stage_lines[0].replace("100644", "120000", 1), *stage_lines[1:])),
        ("nonzero_stage", (stage_lines[0].replace(" 0\t", " 1\t", 1), *stage_lines[1:])),
    ):
        _expect_tamper(
            "index_" + name,
            "TRACKED_GIT_INDEX_MODE_INVALID",
            lambda bad_lines=bad_lines: validate_tracked_index_modes(
                tuple(bad_lines), expected
            ),
        )
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
        "tracked_index_order_independent": True,
        "tracked_index_fail_closed": True,
    }


def check(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    repository = _verify_repository(root)
    dependencies = _verify_dependencies(root)
    formal_sources = _verify_external_formal_sources(root)
    exact4 = _verify_exact4_files(root)
    ingestion_materialized = ingestion.check_materialized_v1(root)
    if not (
        ingestion_materialized.get("status") == "PASS"
        and ingestion_materialized.get("output_artifact_count") == 4
        and ingestion_materialized.get("generic_exact11_fact_count") == 3
        and ingestion_materialized.get("materialized_bytes_equal_fresh_build")
        is True
        and ingestion_materialized.get("deterministic_double_build") is True
    ):
        _fail("ME7_INGESTION_MATERIALIZED_CHECK_INVALID")
    bound = ingestion.load_frozen_formal_decision_v1(root)
    projection = _independent_expected_projection(bound)
    old = _strict_json(
        _read_regular(root / predecessor.OUTPUT_RELATIVE, "PREDECESSOR_ARTIFACT"),
        "PREDECESSOR_ARTIFACT",
    )
    observed_payload = _read_regular(root / subject.OUTPUT_RELATIVE, "ME7_ARTIFACT")
    artifact = _strict_json(observed_payload, "ME7_ARTIFACT")
    predecessor_sources, independent_before, independent_after = (
        _independent_reconciliations(root, projection)
    )
    artifact_report = _verify_full_semantics(
        artifact,
        predecessor_artifact=old,
        projection=projection,
        predecessor_sources=predecessor_sources,
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
        predecessor_sources,
        independent_before,
        independent_after,
    )
    lifecycle = _lifecycle_simulations()
    if not (
        materialized.get("status") == "PASS"
        and subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False
        and repository["profile"] in {CANDIDATE_UNTRACKED, TRACKED_CLEAN}
        and repository["expected_git_publication_mode"] == "100644"
        and (
            repository["git_index_mode_checked"] is False
            if repository["profile"] == CANDIDATE_UNTRACKED
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
            "predecessor_sources": 27,
            "successor_sources": 28,
            "predecessor_facts": 151,
            "successor_facts": 154,
            "source_prefix_preserved": True,
            "fact_prefix_preserved": True,
        },
        "ME7_boundary": {
            "event_count": 3,
            "source_D2": "OUT_OF_DOMAIN",
            "normalized_task_relevance": generic.TASK_NOT_RELEVANT,
            "legacy_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "chemistry": generic.CHEMISTRY_POSITIVE,
            "source_D6": "NOT_APPLICABLE",
            "normalized_training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": False,
            "pair": "SG:CAE",
            "target_pair_is_only_attachment": False,
            "role_partition_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "structurally_applicable_task_ids": None,
            "B3_present": True,
            "sixth_task": False,
        },
        "review_summary": {
            "predecessor": old["review_summary"],
            "successor": artifact["review_summary"],
        },
        "coverage": coverage,
        "ingestion_materialized_check": ingestion_materialized,
        "materialized_check": materialized,
        "tamper_probes": tamper,
        "lifecycle_simulations": lifecycle,
        "materialized_equals_fresh_build": observed_payload == first_build,
        "deterministic_double_build": first_build == second_build,
        "operation_boundary": copy.deepcopy(_OPERATION_BOUNDARY),
    }


def main() -> int:
    try:
        report = check(ROOT)
    except Exception as error:
        print("COVAPIE_ME7_COMPLETED_DECISION_RECONCILIATION_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("COVAPIE_ME7_COMPLETED_DECISION_RECONCILIATION_V1_PASS=true")
    print("lifecycle=" + str(report["repository"]["profile"]))
    print("PREDECESSOR_SOURCE_COUNT=27")
    print("SUCCESSOR_SOURCE_COUNT=28")
    print("PREDECESSOR_ACCEPTED_FACT_COUNT=151")
    print("SUCCESSOR_ACCEPTED_FACT_COUNT=154")
    print("CHANGED_TARGET_ROWS=3")
    print("NON_TARGET_CHANGED_ROWS=0")
    print("UNCHANGED_ROWS=335")
    print("FORMAL_SOURCE_D2=OUT_OF_DOMAIN")
    print("NORMALIZED_TASK_RELEVANCE=NOT_RELEVANT")
    print("LEGACY_COMPLETED_REVIEW_STATUS=COMPLETED_HUMAN_NEGATIVE")
    print("CHEMISTRY_DISPOSITION=POSITIVE")
    print("TRAINING_DISPOSITION=NOT_APPLICABLE")
    print("HUMAN_TRAINING_EXCLUDED=false")
    print("GENERIC_FACT_FIELD_COUNT=11")
    print("RICH_FIELDS_LEAKED=false")
    print("RECONCILIATION_PERFORMED=true")
    print("CENSUS_REFRESH_PERFORMED=false")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("TASK_LABEL_AUTHORITY=false")
    print("FORMAL_TRAINING_ADMITTED=false")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
