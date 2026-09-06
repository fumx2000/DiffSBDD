#!/usr/bin/env python3
"""Independent fail-closed checker for the NWJ reconciliation Exact4."""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, NoReturn

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_nwj_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_tp2_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


BASELINE_COMMIT = "7edf5bba269559d8d23a4b2eccf007ca2380f6f8"
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
        "WITH_TP2_PREDECESSOR_OWNER",
        predecessor.SOURCE_RELATIVE.as_posix(),
        26679,
        "d9bd34e780323535056100b5a11956bf9c6965ed5d58c8aa2c20f8f33a6938fe",
    ),
    (
        "WITH_TP2_PREDECESSOR_ARTIFACT",
        predecessor.OUTPUT_RELATIVE.as_posix(),
        335923,
        "0869d55d446202d3d8464f69a6482e83d0994b6eccac0af3a8b01b3d9d5497eb",
    ),
    (
        "NWJ_INGESTION_OWNER",
        ingestion.SOURCE_RELATIVE.as_posix(),
        83372,
        "256ed54e0ff8a58a641f117960be21a2d1a9793c6a4fc1ac8f388b1a36332996",
    ),
    (
        "NWJ_INGESTION_SNAPSHOT",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SNAPSHOT).as_posix(),
        11298,
        "b651cf7c6b8555e71ccfc98da0355cee8a10f8fad1eec29e7594e29f9a8a7c0f",
    ),
    (
        "NWJ_INGESTION_MATRIX",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX).as_posix(),
        9527,
        "11d71fcc1e693d824df5fcd907ed57b7bafe38ad321cf22ff8a6ef84d55bf2b4",
    ),
    (
        "NWJ_INGESTION_SUMMARY",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SUMMARY).as_posix(),
        1583,
        "440783a936ca8a564a04492b06eec0293a86ff7d099f5a02a8bab68b27890bb8",
    ),
    (
        "NWJ_INGESTION_MANIFEST",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MANIFEST).as_posix(),
        18035,
        "3ac51c52b1fb904f9a99e6e8cacb55d2dae45a13e4438aff1dd49526118311dd",
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
    "feature_semantics_audit_performed": False,
    "feature_semantics_audit_required_before_training": True,
    "ready_for_training": False,
    "training_started": False,
}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_NWJ_RECONCILIATION_V1_ERROR:" + token)


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
    allowed = {
        "diff",
        "ls-files",
        "merge-base",
        "rev-list",
        "rev-parse",
        "status",
    }
    if not arguments or arguments[0] not in allowed:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    process = subprocess.run(
        ("git", *arguments),
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
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
                    root,
                    "diff",
                    "--name-only",
                    BASELINE_COMMIT + "..HEAD",
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
    return {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "lifecycle": profile,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(untracked),
    }


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


def _verify_exact4_files(root: Path) -> list[dict[str, object]]:
    reports = []
    for relative in subject.EXACT4_PATHS:
        path = root / relative
        payload = _read_regular(path, relative.as_posix())
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("EXACT4_NOT_UTF8:" + relative.as_posix()) from error
        mode = stat.S_IMODE(path.lstat().st_mode)
        if (
            len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\r" in payload
            or b"\x00" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or mode not in {0o644, 0o664}
            or mode & 0o111
        ):
            _fail("EXACT4_TEXT_SIZE_OR_MODE_INVALID:" + relative.as_posix())
        reports.append(
            {
                "path": relative.as_posix(),
                "bytes": len(payload),
                "LOC": len(text.splitlines()),
                "SHA256": _sha256(payload),
                "filesystem_mode": format(mode, "04o"),
                "git_mode": "100644",
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
    """Validate NWJ's rich boundary without invoking the subject owner."""

    formal = _mapping(bound.get("formal_document"), "NWJ_FORMAL_NOT_OBJECT")
    state = _mapping(formal.get("formal_state"), "NWJ_FORMAL_STATE_INVALID")
    identity = _mapping(formal.get("sample_identity"), "NWJ_IDENTITY_INVALID")
    decisions = _mapping(formal.get("formal_decisions"), "NWJ_DECISIONS_INVALID")
    role = _mapping(formal.get("selected_role_context"), "NWJ_ROLE_INVALID")
    seed = _mapping(role.get("minimal_seed"), "NWJ_SEED_INVALID")
    alternative = _mapping(
        formal.get("retained_nonselected_alternative"), "NWJ_ALTERNATIVE_INVALID"
    )
    tasks = _mapping(formal.get("canonical_Exact5"), "NWJ_EXACT5_INVALID")
    pre = _mapping(formal.get("PRE_boundary"), "NWJ_PRE_INVALID")
    training = _mapping(formal.get("training_boundary"), "NWJ_TRAINING_INVALID")
    readiness = _mapping(formal.get("readiness"), "NWJ_READINESS_INVALID")
    binding = _mapping(
        bound.get("formal_decision_binding"), "NWJ_FORMAL_BINDING_INVALID"
    )
    validator = _mapping(
        bound.get("formal_validator_binding"), "NWJ_VALIDATOR_BINDING_INVALID"
    )
    d1 = _mapping(
        decisions.get("D1_observed_covalent_chemistry"), "NWJ_D1_INVALID"
    )
    d2 = _mapping(
        decisions.get("D2_generation_domain_relevance"), "NWJ_D2_INVALID"
    )
    d3 = _mapping(decisions.get("D3_reactive_pair"), "NWJ_D3_INVALID")
    d4 = _mapping(decisions.get("D4_role_partition"), "NWJ_D4_INVALID")
    d5 = _mapping(
        decisions.get("D5_structural_task_applicability"), "NWJ_D5_INVALID"
    )
    d6 = _mapping(decisions.get("D6_later_training_use"), "NWJ_D6_INVALID")
    if (
        formal.get("schema_version") != "covapie_nwj_exact4_formal_human_decision_v1"
        or state.get("approved") is not True
        or state.get("unsigned") is not False
        or state.get("authorization_origin") != "EXTERNAL_HUMAN_CHAT_REVIEW"
        or state.get("human_review_completed") is not True
        or state.get("formal_decision_created") is not True
        or identity.get("PDB") != "4CM5"
        or identity.get("ligand_component_id") != "NWJ"
        or identity.get("review_unit_id")
        != "COVAPIE_BULK_REVIEW_UNIT_DE7AFABE9D079CDF"
        or identity.get("event_count") != 4
        or identity.get("canonical_event_ids") != list(ingestion.EXPECTED_EVENT_IDS)
        or identity.get("scaleup_event_ranks") != [674, 675, 676, 677]
        or identity.get("raw_priority_rank") != 28
        or d1.get("decision") != "POSITIVE"
        or d2.get("decision") != "IN_DOMAIN"
        or d3.get("protein_atom") != "SG"
        or d3.get("ligand_atom") != "CAV"
        or d4.get("selected_candidate") != "CANDIDATE_A_DIRECT_FORMYL"
        or d4.get("role_profile") != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        or d4.get("candidate_B_selected") is not False
        or d4.get("candidate_B_authoritative") is not False
        or d5.get("decision") != [0, 3, 4]
        or d5.get("task_label_authority") is not False
        or d6.get("decision") != "INCLUDE"
        or role.get("warhead_atom_ids") != ["CAV", "OAE"]
        or role.get("linker_atom_ids") != []
        or seed.get("atom_ids") != ["CAX", "CAI", "CAK"]
        or seed.get("primary_scaffold_side_anchor") != "CAX"
        or alternative.get("candidate_B_selected") is not False
        or alternative.get("candidate_B_authoritative") is not False
        or tasks.get("task_count") != 5
        or tasks.get("B3_present") is not True
        or tasks.get("sixth_task") is not False
        or tasks.get("selected_structural_applicability_task_ids") != [0, 3, 4]
        or tasks.get("task_label_authority") is not False
        or tasks.get("event_task_label_rows_materialized") is not False
        or tasks.get("mask_tensor_targets_created") is not False
        or pre.get("PRE_source_mapping_status")
        != "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        or training.get("formal_training_admitted") is not False
        or training.get("task_label_authority") is not False
        or training.get("READY_FOR_TRAINING") is not False
        or training.get("TRAINING_STARTED") is not False
        or readiness.get("FORMAL_TRAINING_ADMITTED") is not False
        or readiness.get("READY_FOR_TRAINING") is not False
        or readiness.get("TRAINING_STARTED") is not False
    ):
        _fail("NWJ_RICH_BOUNDARY_INVALID")
    expected_binding = {
        "path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": 24265,
        "SHA256": "1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff",
        "semantic_source_identity": (
            "project_parent_relative:"
            + ingestion.FORMAL_DECISION_RELATIVE.as_posix()
            + "@1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff"
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "NWJ_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }
    if binding != expected_binding:
        _fail("NWJ_FORMAL_SOURCE_BINDING_INVALID")
    if (
        validator.get("validation_method")
        != "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        or validator.get("expected_executable_class") != "NON_EXECUTABLE"
    ):
        _fail("NWJ_VALIDATOR_EXECUTION_BOUNDARY_INVALID")
    return [
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE,
            "task_relevance_disposition": generic.TASK_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_INCLUDE,
            "human_training_excluded": False,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": expected_binding["SHA256"],
            "source_binding_path": expected_binding["path"],
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    ]


def _stable_identity(binding: dict[str, object]) -> str:
    return (
        f"{binding.get('path_namespace')}:"
        f"{binding.get('source_path')}@{binding.get('sha256')}"
    )


def _computed_review_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    status_events: Counter[str] = Counter()
    status_units: dict[str, set[str]] = defaultdict(set)
    unit_statuses: dict[str, set[str]] = defaultdict(set)
    all_units: set[str] = set()
    for row in rows:
        status = row.get("current_review_status")
        unit = row.get("raw_review_unit_id")
        if type(status) is not str or type(unit) is not str:
            _fail("REVIEW_SUMMARY_ROW_INVALID")
        status_events[status] += 1
        status_units[status].add(unit)
        unit_statuses[unit].add(status)
        all_units.add(unit)
    if any(len(statuses) != 1 for statuses in unit_statuses.values()):
        _fail("REVIEW_UNIT_MIXED_STATUS")
    completed_units = (
        status_units[generic.COMPLETED_HUMAN_POSITIVE]
        | status_units[generic.COMPLETED_HUMAN_NEGATIVE]
    )
    return {
        "universe_event_count": len(rows),
        "universe_review_unit_count": len(all_units),
        "completed_positive_event_count": status_events[
            generic.COMPLETED_HUMAN_POSITIVE
        ],
        "completed_positive_unit_count": len(
            status_units[generic.COMPLETED_HUMAN_POSITIVE]
        ),
        "completed_negative_event_count": status_events[
            generic.COMPLETED_HUMAN_NEGATIVE
        ],
        "completed_negative_unit_count": len(
            status_units[generic.COMPLETED_HUMAN_NEGATIVE]
        ),
        "completed_total_event_count": (
            status_events[generic.COMPLETED_HUMAN_POSITIVE]
            + status_events[generic.COMPLETED_HUMAN_NEGATIVE]
        ),
        "completed_total_unit_count": len(completed_units),
        "in_progress_event_count": status_events[generic.CURRENTLY_IN_PROGRESS],
        "in_progress_unit_count": len(
            status_units[generic.CURRENTLY_IN_PROGRESS]
        ),
        "unreviewed_event_count": status_events[generic.CURRENTLY_UNREVIEWED],
        "unreviewed_unit_count": len(status_units[generic.CURRENTLY_UNREVIEWED]),
    }


def _verify_artifact_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    expected_projection: list[dict[str, object]],
) -> dict[str, object]:
    """Verify direct serialized evidence before comparing owner-built bytes."""

    if tuple(artifact) != subject._ARTIFACT_FIELDS:
        _fail("ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    if tuple(predecessor_artifact) != subject._ARTIFACT_FIELDS:
        _fail("PREDECESSOR_ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    bindings = artifact.get("source_bindings")
    facts = artifact.get("normalized_facts")
    rows = artifact.get("reconciled_rows")
    old_bindings = predecessor_artifact.get("source_bindings")
    old_facts = predecessor_artifact.get("normalized_facts")
    old_rows = predecessor_artifact.get("reconciled_rows")
    if not all(
        type(value) is list
        for value in (bindings, facts, rows, old_bindings, old_facts, old_rows)
    ):
        _fail("ARTIFACT_COLLECTION_TYPE_INVALID")
    assert isinstance(bindings, list) and isinstance(facts, list)
    assert isinstance(rows, list) and isinstance(old_bindings, list)
    assert isinstance(old_facts, list) and isinstance(old_rows, list)
    old_summary = _computed_review_summary(old_rows)
    new_summary = _computed_review_summary(rows)
    if (
        len(old_bindings) != 24
        or len(old_facts) != 139
        or len(old_rows) != 338
        or old_summary != subject._PREDECESSOR_REVIEW_SUMMARY
        or predecessor_artifact.get("review_summary") != old_summary
    ):
        _fail("PUBLISHED_PREDECESSOR_ARTIFACT_INVALID")
    if len(bindings) != 25 or len(facts) != 143 or len(rows) != 338:
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if any(
        type(item) is not dict
        or set(item) != set(subject._SOURCE_BINDING_FIELDS)
        or item.get("path_namespace") != "repository_parent_relative"
        or str(item.get("source_path", "")).startswith("/")
        for item in bindings
    ):
        _fail("ARTIFACT_SOURCE_BINDING_SCHEMA_INVALID")
    if (
        len({_stable_identity(item) for item in bindings}) != 25
        or len({item["review_unit_id"] for item in bindings}) != 25
    ):
        _fail("ARTIFACT_SOURCE_IDENTITY_DUPLICATE")
    if any(
        type(item) is not dict
        or tuple(item) != subject._GENERIC_FACT_FIELDS
        or len(item) != 11
        or subject._FORBIDDEN_RICH_FACT_FIELDS & set(item)
        for item in facts
    ):
        _fail("ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    if bindings[:-1] != old_bindings:
        _fail("PREDECESSOR_SOURCE_PREFIX_INVALID")
    expected_binding = {
        "source_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": 24265,
        "sha256": "1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff",
        "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
    }
    if bindings[-1] != expected_binding:
        _fail("NWJ_SOURCE_BINDING_INVALID")
    if facts[:139] != old_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if facts[139:] != expected_projection:
        _fail("NWJ_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION")
    if len({item.get("canonical_event_id") for item in facts}) != 143:
        _fail("CANONICAL_EVENT_ID_DUPLICATE")
    if any(
        item.get("legacy_completed_review_status")
        != generic.COMPLETED_HUMAN_POSITIVE
        or item.get("task_relevance_disposition") != generic.TASK_RELEVANT
        or item.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
        or item.get("training_disposition") != generic.TRAINING_INCLUDE
        or item.get("human_training_excluded") is not False
        for item in facts[139:]
    ):
        _fail("NWJ_CLASSIFICATION_INVALID")
    if (
        new_summary != subject._SUCCESSOR_REVIEW_SUMMARY
        or artifact.get("review_summary") != new_summary
    ):
        _fail("ARTIFACT_REVIEW_SUMMARY_INVALID")
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(old_rows, rows, strict=True):
        if old.get("canonical_event_id") not in targets:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old[key] != new[key]}
        if (
            old.get("raw_priority_rank") != "28"
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
            _fail("NWJ_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("RECONCILIATION_DELTA_NOT_EXACT4_ONLY")
    return {
        "source_count": 25,
        "accepted_fact_count": 143,
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
        (before, predecessor_facts, 24),
        (after, successor_facts, 25),
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
    appended = successor_facts[139:]
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
        or successor_facts[:139] != predecessor_facts
        or len(appended) != 4
        or [fact.get("canonical_event_id") for fact in appended]
        != list(ingestion.EXPECTED_EVENT_IDS)
        or any(
            fact.get("review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or fact.get("human_review_completed") is not True
            or fact.get("legacy_completed_review_status")
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.get("task_relevance_disposition") != generic.TASK_RELEVANT
            or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
            or fact.get("training_disposition") != generic.TRAINING_INCLUDE
            or fact.get("human_training_excluded") is not False
            for fact in appended
        )
        or after["label_ready_event_count"] != before["label_ready_event_count"]
        or after["training_mask_target_count"]
        != before["training_mask_target_count"]
        or after["training_authority"] is not False
        or before["training_authority"] is not False
    ):
        _fail("NWJ_COVERAGE_DELTA_INVALID")
    return {"predecessor": before, "successor": after}


def _verify_operation_boundary(boundary: dict[str, object]) -> None:
    if boundary != _OPERATION_BOUNDARY:
        _fail("OPERATION_OR_TRAINING_BOUNDARY_INVALID")


def _verify_full_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    expected_projection: list[dict[str, object]],
    operation_boundary: dict[str, object] | None = None,
    predecessor_coverage: dict[str, object] | None = None,
    successor_coverage: dict[str, object] | None = None,
) -> dict[str, object]:
    report = _verify_artifact_semantics(
        artifact,
        predecessor_artifact=predecessor_artifact,
        expected_projection=expected_projection,
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


def _expect_tamper(token: str, callback) -> str:
    try:
        callback()
    except ValueError as error:
        if token not in str(error) or (
            token != "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"
            and "MATERIALIZED_ARTIFACT_BYTES_MISMATCH" in str(error)
        ):
            raise
        return token
    _fail("TAMPER_PROBE_DID_NOT_FAIL:" + token)


def _tamper_probes(
    artifact: dict[str, Any],
    old: dict[str, Any],
    projection: list[dict[str, object]],
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
            expected_projection=projection,
            operation_boundary=operations,
            predecessor_coverage=before_coverage,
            successor_coverage=after_coverage,
        )

    def mutate_fact(name: str, index: int, key: str, value: object, token: str) -> None:
        candidate = copy.deepcopy(artifact)
        candidate["normalized_facts"][index][key] = value
        probes[name] = _expect_tamper(token, lambda: semantic(candidate))

    mutate_fact(
        "wrong_review_unit",
        -1,
        "review_unit_id",
        "WRONG_UNIT",
        "NWJ_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION",
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"].pop()
    probes["missing_nwj_event"] = _expect_tamper(
        "ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate)
    )
    mutate_fact(
        "duplicate_nwj_event",
        -1,
        "canonical_event_id",
        ingestion.EXPECTED_EVENT_IDS[0],
        "NWJ_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION",
    )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1]["sha256"] = "0" * 64
    probes["formal_source_sha_drift"] = _expect_tamper(
        "NWJ_SOURCE_BINDING_INVALID", lambda: semantic(candidate)
    )
    for name, field in (
        ("generic_schema_11_to_12", "twelfth_field"),
        ("rich_pair_leak", "reactive_pair"),
        ("role_leak", "role_profile"),
        ("seed_leak", "minimal_seed"),
        ("task_id_leak", "applicable_task_ids"),
    ):
        mutate_fact(name, -1, field, "FORGED", "ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    for name, field, value in (
        (
            "legacy_positive_to_negative",
            "legacy_completed_review_status",
            generic.COMPLETED_HUMAN_NEGATIVE,
        ),
        (
            "relevant_to_not_relevant",
            "task_relevance_disposition",
            generic.TASK_NOT_RELEVANT,
        ),
        (
            "chemistry_positive_to_negative",
            "chemistry_disposition",
            generic.CHEMISTRY_NEGATIVE,
        ),
        ("training_include_drift", "training_disposition", "EXCLUDE"),
        ("human_training_excluded_true", "human_training_excluded", True),
    ):
        mutate_fact(
            name,
            -1,
            field,
            value,
            "NWJ_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION",
        )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1], candidate["source_bindings"][-2] = (
        candidate["source_bindings"][-2],
        candidate["source_bindings"][-1],
    )
    probes["source_append_reordered"] = _expect_tamper(
        "PREDECESSOR_SOURCE_PREFIX_INVALID", lambda: semantic(candidate)
    )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1] = copy.deepcopy(
        candidate["source_bindings"][0]
    )
    probes["duplicate_source_identity"] = _expect_tamper(
        "ARTIFACT_SOURCE_IDENTITY_DUPLICATE", lambda: semantic(candidate)
    )
    mutate_fact(
        "predecessor_fact_modified",
        0,
        "source_decision_sha256",
        "0" * 64,
        "PREDECESSOR_FACT_PREFIX_INVALID",
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
    for name, index, field, value, token in (
        (
            "non_nwj_row_modified",
            non_target,
            "raw_priority_rank",
            "999",
            "RECONCILIATION_DELTA_NOT_EXACT4_ONLY",
        ),
        (
            "wrong_authority_source",
            target_indices[0],
            "current_status_authority_sources_json",
            "[]",
            "NWJ_RECONCILIATION_TRANSITION_INVALID",
        ),
        (
            "calibration_remains_eligible",
            target_indices[0],
            "calibration_eligible",
            "true",
            "NWJ_RECONCILIATION_TRANSITION_INVALID",
        ),
        (
            "wrong_exclusion_reason",
            target_indices[0],
            "calibration_exclusion_reason",
            "WRONG",
            "NWJ_RECONCILIATION_TRANSITION_INVALID",
        ),
        (
            "fifth_row_changes",
            non_target,
            "calibration_exclusion_reason",
            "FORGED",
            "RECONCILIATION_DELTA_NOT_EXACT4_ONLY",
        ),
    ):
        candidate = copy.deepcopy(artifact)
        candidate["reconciled_rows"][index][field] = value
        probes[name] = _expect_tamper(token, lambda candidate=candidate: semantic(candidate))
    forged_coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
    forged_coverage["training_authority"] = True
    probes["training_authority_forged"] = _expect_tamper(
        "SUCCESSOR_COVERAGE_DRIFT",
        lambda: semantic(artifact, after_coverage=forged_coverage),
    )
    forged_coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
    forged_coverage["training_mask_target_count"] = 1
    probes["training_mask_target_count_positive"] = _expect_tamper(
        "SUCCESSOR_COVERAGE_DRIFT",
        lambda: semantic(artifact, after_coverage=forged_coverage),
    )
    for name, field in (
        ("census_refresh_forged", "census_refresh_performed"),
        ("queue_refresh_forged", "queue_refresh_performed"),
        ("next_review_started_forged", "next_review_started"),
        ("training_started_forged", "training_started"),
    ):
        operations = copy.deepcopy(_OPERATION_BOUNDARY)
        operations[field] = True
        probes[name] = _expect_tamper(
            "OPERATION_OR_TRAINING_BOUNDARY_INVALID",
            lambda operations=operations: semantic(artifact, operations=operations),
        )
    payload = json.dumps(artifact).encode()
    probes["raw_byte_corruption"] = _expect_tamper(
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
        lambda: _verify_byte_identity(payload, payload + b" "),
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
        **common, head="successor", origin_main=BASELINE_COMMIT, ahead=1
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
    }


def check(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    repository = _verify_repository(root)
    dependencies = _verify_dependencies(root)
    exact4 = _verify_exact4_files(root)
    ingestion_report = ingestion.check_materialized_v1(root)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    projection = _independent_expected_projection(bound)
    old = _strict_json(
        _read_regular(root / predecessor.OUTPUT_RELATIVE, "PREDECESSOR_ARTIFACT"),
        "PREDECESSOR_ARTIFACT",
    )
    observed_payload = _read_regular(root / subject.OUTPUT_RELATIVE, "NWJ_ARTIFACT")
    artifact = _strict_json(observed_payload, "NWJ_ARTIFACT")
    artifact_report = _verify_full_semantics(
        artifact,
        predecessor_artifact=old,
        expected_projection=projection,
    )
    coverage = _verify_coverage_contract(
        old["normalized_facts"], artifact["normalized_facts"]
    )
    first_build = subject.build_artifact_v1(root)
    second_build = subject.build_artifact_v1(root)
    _verify_byte_identity(first_build, observed_payload)
    _verify_byte_identity(first_build, second_build)
    materialized = subject.check_materialized_v1(root)
    tamper = _tamper_probes(artifact, old, projection)
    lifecycle = _lifecycle_simulations()
    if not (
        ingestion_report.get("status") == "PASS"
        and materialized.get("status") == "PASS"
        and subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False
        and bound["formal_document"]["canonical_Exact5"]["B3_present"] is True
        and bound["formal_document"]["canonical_Exact5"]["sixth_task"] is False
    ):
        _fail("FINAL_READINESS_BOUNDARY_INVALID")
    return {
        "status": "PASS",
        "repository": repository,
        "dependencies": dependencies,
        "Exact4_files": exact4,
        "artifact": artifact_report,
        "source_chain": {
            "predecessor_sources": 24,
            "successor_sources": 25,
            "predecessor_facts": 139,
            "successor_facts": 143,
            "prefix_preserved": True,
        },
        "NWJ_boundary": {
            "event_count": 4,
            "legacy_status": generic.COMPLETED_HUMAN_POSITIVE,
            "task_relevance": generic.TASK_RELEVANT,
            "chemistry": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_INCLUDE,
            "human_training_excluded": False,
            "pair": "SG-CAV",
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
        "ingestion_check": ingestion_report,
        "materialized_check": materialized,
        "tamper_probes": tamper,
        "lifecycle_simulations": lifecycle,
        "materialized_equals_fresh_build": observed_payload == first_build,
        "deterministic_double_build": first_build == second_build,
        "operation_boundary": copy.deepcopy(_OPERATION_BOUNDARY),
        "Step12D_status": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def main() -> int:
    try:
        report = check(ROOT)
    except Exception as error:
        print("NWJ_COMPLETED_DECISION_RECONCILIATION_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("NWJ_COMPLETED_DECISION_RECONCILIATION_V1_PASS=true")
    print("PREDECESSOR_SOURCE_COUNT=24")
    print("SUCCESSOR_SOURCE_COUNT=25")
    print("PREDECESSOR_ACCEPTED_FACT_COUNT=139")
    print("SUCCESSOR_ACCEPTED_FACT_COUNT=143")
    print("NWJ_GENERIC_FACT_CLASSIFICATION=COMPLETED_HUMAN_POSITIVE/RELEVANT/POSITIVE/INCLUDE")
    print("CHANGED_TARGET_ROWS=4")
    print("NON_TARGET_CHANGED_ROWS=0")
    print("UNCHANGED_ROWS=334")
    print("CENSUS_REFRESH_PERFORMED=false")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("NEXT_REVIEW_STARTED=false")
    print("TASK_LABEL_AUTHORITY=false")
    print("FORMAL_TRAINING_ADMITTED=false")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
