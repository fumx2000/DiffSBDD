#!/usr/bin/env python3
"""Independent fail-closed checker for the 6OA reconciliation Exact4."""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
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

from covalent_ext import covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_6oa_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_nwj_v1 as predecessor  # noqa: E402


BASELINE_COMMIT = "122ba4e3909a83a872e07aa74eabd20840fc7ec4"
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
        "WITH_NWJ_PREDECESSOR_OWNER",
        predecessor.SOURCE_RELATIVE.as_posix(),
        32335,
        "caacf56f4becda795e21c93bb29123cd1e1a02b118e1d794dbe88a3851015f4c",
    ),
    (
        "WITH_NWJ_PREDECESSOR_ARTIFACT",
        predecessor.OUTPUT_RELATIVE.as_posix(),
        340039,
        "e3913f514f88c8bbc85fe2c02894fb445cc6c53258c87dd9e17e889cffd90c56",
    ),
    (
        "HISTORICAL_ADAPTER_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_tp2_v1.py",
        26679,
        "d9bd34e780323535056100b5a11956bf9c6965ed5d58c8aa2c20f8f33a6938fe",
    ),
    (
        "6OA_INGESTION_OWNER",
        ingestion.SOURCE_RELATIVE.as_posix(),
        101282,
        "7cf21daa63459b7e6f2552ad0ba6371a88a39dfa7fa0aa1b1d9bbf448cbfaff4",
    ),
    (
        "6OA_INGESTION_SNAPSHOT",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SNAPSHOT).as_posix(),
        24009,
        "421d3dccab93e5b75c19b60e68d13faaa09c59f9210ed2fc5b2d1269d2f4ba7a",
    ),
    (
        "6OA_INGESTION_MATRIX",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX).as_posix(),
        9391,
        "1b74de80ea1cd1c9e030c9602a3b8925b523e826b67db9e21d07d2e7f856fcfa",
    ),
    (
        "6OA_INGESTION_SUMMARY",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SUMMARY).as_posix(),
        5350,
        "79c8d863612e8b6137ea5b5c22a005108b568f52bd39001a33447f1c0887521a",
    ),
    (
        "6OA_INGESTION_MANIFEST",
        (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MANIFEST).as_posix(),
        23834,
        "62335218c39a3a3c5ddac6ccaf7329e7944766ee556ed8f4cd40209ab9f37844",
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
    "parameter_update_authorization": False,
    "feature_semantics_audit_performed": False,
    "feature_semantics_audit_required_before_training": True,
    "ready_for_training": False,
    "training_started": False,
}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_6OA_RECONCILIATION_V1_ERROR:" + token)


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
    """Parse real ``git ls-files --stage`` output and require Exact4 mode 100644."""

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
        if path in PROTECTED_FILES or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            _fail("PROTECTED_PATH_CHANGED_SINCE_BASELINE:" + path)
        if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail("FORBIDDEN_SUFFIX_CHANGED_SINCE_BASELINE:" + path)


def _verify_repository(root: Path) -> dict[str, object]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    tracked = set(filter(None, _git(root, "ls-files").splitlines()))
    untracked = set(
        filter(None, _git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    )
    status_lines = tuple(
        filter(None, _git(root, "status", "--short", "--untracked-files=all").splitlines())
    )
    working = set(filter(None, _git(root, "diff", "--name-only").splitlines()))
    cached = set(filter(None, _git(root, "diff", "--cached", "--name-only").splitlines()))
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
    relation = _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main").split()
    if branch != "main" or len(relation) != 2 or any(not part.isdigit() for part in relation):
        _fail("REPOSITORY_IDENTITY_INVALID")
    ahead, behind = map(int, relation)
    changed = set() if profile == CANDIDATE_UNTRACKED else set(
        filter(None, _git(root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD").splitlines())
    )
    validate_repository_relation_values(
        profile=profile,
        expected_paths=set(paths),
        head=head,
        origin_main=origin,
        ahead=ahead,
        behind=behind,
        baseline_is_ancestor_of_head=True if profile == CANDIDATE_UNTRACKED else _ancestor(root, BASELINE_COMMIT, "HEAD"),
        baseline_is_ancestor_of_origin=True if profile == CANDIDATE_UNTRACKED else _ancestor(root, BASELINE_COMMIT, "origin/main"),
        origin_is_ancestor_of_head=True if profile == CANDIDATE_UNTRACKED else _ancestor(root, "origin/main", "HEAD"),
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
        reports.append({"role": role, "path": relative, "bytes": len(payload), "SHA256": digest})
    return reports


def _verify_external_formal_sources(root: Path) -> list[dict[str, object]]:
    expected = (
        (
            "6OA_FORMAL_JSON",
            ingestion.FORMAL_DECISION_RELATIVE,
            33043,
            "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
        ),
        (
            "6OA_FORMAL_VALIDATOR_PROVENANCE_ONLY",
            ingestion.FORMAL_VALIDATOR_RELATIVE,
            96246,
            "77800ac2056df2b0770967be15bb89c67d2be089d6c54180361f4922ee73731e",
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
    reports = []
    output_parent = root / subject.OUTPUT_ROOT_RELATIVE
    if {item.name for item in output_parent.iterdir()} != {subject.OUTPUT_NAME}:
        _fail("RECONCILIATION_OUTPUT_INVENTORY_NOT_EXACT1")
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


def _independent_expected_projection(bound: dict[str, object]) -> list[dict[str, object]]:
    """Validate the rich 6OA projection without invoking the subject owner."""

    formal = _mapping(bound.get("formal_document"), "6OA_FORMAL_NOT_OBJECT")
    state = _mapping(formal.get("formal_state"), "6OA_FORMAL_STATE_INVALID")
    identity = _mapping(formal.get("sample_identity"), "6OA_IDENTITY_INVALID")
    decisions = _mapping(formal.get("formal_decisions"), "6OA_DECISIONS_INVALID")
    role = _mapping(formal.get("selected_role_context"), "6OA_ROLE_INVALID")
    seed = _mapping(role.get("minimal_seed"), "6OA_SEED_INVALID")
    tasks = _mapping(formal.get("canonical_Exact5"), "6OA_EXACT5_INVALID")
    pre = _mapping(formal.get("PRE_boundary"), "6OA_PRE_INVALID")
    geometry = _mapping(formal.get("geometry_boundary"), "6OA_GEOMETRY_INVALID")
    training = _mapping(formal.get("training_boundary"), "6OA_TRAINING_INVALID")
    readiness = _mapping(formal.get("readiness"), "6OA_READINESS_INVALID")
    binding = _mapping(bound.get("formal_decision_binding"), "6OA_FORMAL_BINDING_INVALID")
    validator = _mapping(bound.get("formal_validator_binding"), "6OA_VALIDATOR_BINDING_INVALID")
    compatibility = _mapping(bound.get("generic_Exact11_compatibility"), "6OA_GENERIC_BOUND_INVALID")
    census = _mapping(bound.get("current_census_boundary"), "6OA_CENSUS_BOUND_INVALID")
    d1 = _mapping(decisions.get("D1_observed_covalent_chemistry"), "6OA_D1_INVALID")
    d2 = _mapping(decisions.get("D2_task_generation_domain_relevance"), "6OA_D2_INVALID")
    d3 = _mapping(decisions.get("D3_reactive_atom_pair_confirmation_or_revision"), "6OA_D3_INVALID")
    d4 = _mapping(decisions.get("D4_role_partition_and_minimal_seed"), "6OA_D4_INVALID")
    d5 = _mapping(decisions.get("D5_structural_task_applicability"), "6OA_D5_INVALID")
    d6 = _mapping(decisions.get("D6_later_training_use_disposition"), "6OA_D6_INVALID")
    expected_geometry = [float(row[5]) for row in ingestion.EXPECTED_EVENTS]
    geometry_events = geometry.get("events")
    long_names = [row[1] for row in ingestion.CANONICAL_TASKS]
    actual_tasks = tasks.get("tasks")
    if (
        formal.get("schema_version") != ingestion.FORMAL_DECISION_SCHEMA
        or state.get("approved") is not True
        or state.get("unsigned") is not False
        or state.get("authorization_origin") != "EXTERNAL_HUMAN_CHAT_REVIEW"
        or state.get("human_review_completed") is not True
        or state.get("formal_decision_created") is not True
        or identity.get("PDB") != "4OU2"
        or identity.get("ligand_component_id") != "6OA"
        or identity.get("review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
        or identity.get("event_count") != 4
        or identity.get("canonical_event_ids") != list(ingestion.EXPECTED_EVENT_IDS)
        or identity.get("scaleup_event_ranks") != list(ingestion.EXPECTED_RANKS)
        or identity.get("raw_priority_rank") != 29
        or d1.get("decision") != generic.CHEMISTRY_POSITIVE
        or d1.get("chemistry_negative") is not False
        or d2.get("decision") != "OUT_OF_DOMAIN"
        or d2.get("chemistry_positive_preserved") is not True
        or d3.get("decision") != "CONFIRM_OBSERVED_PAIR"
        or d3.get("protein_reactive_atom") != "SG"
        or d3.get("ligand_reactive_atom") != "C5"
        or d3.get("observed_pair") != "SG:C5"
        or d3.get("reactive_pair_sample_authoritative") is not True
        or d3.get("reusable_pair_authority") is not False
        or d4.get("selected_candidate") != ingestion.SELECTED_CANDIDATE
        or d4.get("role_profile") != ingestion.EXPECTED_ROLE_PROFILE
        or d4.get("role_partition_sample_authoritative") is not True
        or d4.get("minimal_seed_sample_authoritative") is not True
        or d5.get("applicable_task_ids") != [0, 3, 4]
        or d5.get("task_applicability_sample_authoritative") is not True
        or d5.get("task_label_authority") is not False
        or d5.get("event_task_label_rows_materialized") is not False
        or d5.get("mask_tensor_targets_created") is not False
        or d6.get("decision") != generic.TRAINING_NOT_APPLICABLE
        or d6.get("consistent_with_D2") != "OUT_OF_DOMAIN"
        or d6.get("chemistry_negative") is not False
        or role.get("warhead_atom_ids") != ["C5", "O3"]
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids") != ["C", "C1", "C2", "C3", "C4", "O", "O1", "O2"]
        or role.get("boundary") != "C4--C5/SING"
        or role.get("task_ids") != [0, 3, 4]
        or seed.get("atom_ids") != ["C3", "C4"]
        or seed.get("primary_scaffold_side_anchor") != "C4"
        or tasks.get("task_count") != 5
        or tasks.get("B3_present") is not True
        or tasks.get("sixth_task") is not False
        or type(actual_tasks) is not list
        or [row.get("semantic_long_name") for row in actual_tasks if type(row) is dict] != long_names
        or pre.get("PRE_source_mapping_status") != ingestion.PRE_MAPPING_STATUS
        or pre.get("final_PRE_reaction_status") != ingestion.PRE_STATUS
        or pre.get("PRE_authority") is not False
        or type(geometry_events) is not list
        or [row.get("exact_POST_distance_angstrom") for row in geometry_events if type(row) is dict] != expected_geometry
        or geometry.get("POST_geometry_training_authority") is not False
        or training.get("human_training_use_disposition") != generic.TRAINING_NOT_APPLICABLE
        or training.get("formal_training_admitted") is not False
        or training.get("task_label_authority") is not False
        or training.get("READY_FOR_TRAINING") is not False
        or training.get("TRAINING_STARTED") is not False
        or readiness.get("FORMAL_TRAINING_ADMITTED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_PERFORMED") is not False
        or readiness.get("FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING") is not True
        or readiness.get("READY_FOR_TRAINING") is not False
        or readiness.get("TRAINING_STARTED") is not False
        or compatibility.get("source_formal_generation_domain_decision") != "OUT_OF_DOMAIN"
        or compatibility.get("normalized_task_relevance_disposition") != generic.TASK_NOT_RELEVANT
        or compatibility.get("generic_fact_field_count") != 11
        or compatibility.get("rich_fields_leaked") is not False
        or census.get("census_modified_by_ingestion") is not False
        or census.get("6OA_current_global_status") != generic.CURRENTLY_UNREVIEWED
    ):
        _fail("6OA_RICH_BOUNDARY_INVALID")
    expected_binding = {
        "path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": 33043,
        "SHA256": "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
        "semantic_source_identity": (
            "project_parent_relative:"
            + ingestion.FORMAL_DECISION_RELATIVE.as_posix()
            + "@c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218"
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "6OA_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }
    if binding != expected_binding:
        _fail("6OA_FORMAL_SOURCE_BINDING_INVALID")
    if (
        validator.get("byte_count") != 96246
        or validator.get("SHA256") != "77800ac2056df2b0770967be15bb89c67d2be089d6c54180361f4922ee73731e"
        or validator.get("validation_method") != "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        or validator.get("expected_executable_class") != "NON_EXECUTABLE"
    ):
        _fail("6OA_VALIDATOR_EXECUTION_BOUNDARY_INVALID")
    return [
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
            "source_decision_sha256": "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
            "source_binding_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    ]


def _stable_identity(binding: dict[str, object]) -> str:
    return f"{binding.get('path_namespace')}:{binding.get('source_path')}@{binding.get('sha256')}"


def _computed_review_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    status_events: Counter[str] = Counter()
    status_units: dict[str, set[str]] = defaultdict(set)
    unit_statuses: dict[str, set[str]] = defaultdict(set)
    all_units: set[str] = set()
    for row in rows:
        status, unit = row.get("current_review_status"), row.get("raw_review_unit_id")
        if type(status) is not str or type(unit) is not str:
            _fail("REVIEW_SUMMARY_ROW_INVALID")
        status_events[status] += 1
        status_units[status].add(unit)
        unit_statuses[unit].add(status)
        all_units.add(unit)
    if any(len(statuses) != 1 for statuses in unit_statuses.values()):
        _fail("REVIEW_UNIT_MIXED_STATUS")
    completed_units = status_units[generic.COMPLETED_HUMAN_POSITIVE] | status_units[generic.COMPLETED_HUMAN_NEGATIVE]
    return {
        "universe_event_count": len(rows),
        "universe_review_unit_count": len(all_units),
        "completed_positive_event_count": status_events[generic.COMPLETED_HUMAN_POSITIVE],
        "completed_positive_unit_count": len(status_units[generic.COMPLETED_HUMAN_POSITIVE]),
        "completed_negative_event_count": status_events[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_negative_unit_count": len(status_units[generic.COMPLETED_HUMAN_NEGATIVE]),
        "completed_total_event_count": status_events[generic.COMPLETED_HUMAN_POSITIVE] + status_events[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_total_unit_count": len(completed_units),
        "in_progress_event_count": status_events[generic.CURRENTLY_IN_PROGRESS],
        "in_progress_unit_count": len(status_units[generic.CURRENTLY_IN_PROGRESS]),
        "unreviewed_event_count": status_events[generic.CURRENTLY_UNREVIEWED],
        "unreviewed_unit_count": len(status_units[generic.CURRENTLY_UNREVIEWED]),
    }


def _verify_artifact_semantics(
    artifact: dict[str, Any],
    *,
    predecessor_artifact: dict[str, Any],
    expected_projection: list[dict[str, object]],
) -> dict[str, object]:
    if tuple(artifact) != subject._ARTIFACT_FIELDS:
        _fail("ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    if tuple(predecessor_artifact) != subject._ARTIFACT_FIELDS:
        _fail("PREDECESSOR_ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    bindings, facts, rows = artifact.get("source_bindings"), artifact.get("normalized_facts"), artifact.get("reconciled_rows")
    old_bindings = predecessor_artifact.get("source_bindings")
    old_facts = predecessor_artifact.get("normalized_facts")
    old_rows = predecessor_artifact.get("reconciled_rows")
    if not all(type(value) is list for value in (bindings, facts, rows, old_bindings, old_facts, old_rows)):
        _fail("ARTIFACT_COLLECTION_TYPE_INVALID")
    assert isinstance(bindings, list) and isinstance(facts, list) and isinstance(rows, list)
    assert isinstance(old_bindings, list) and isinstance(old_facts, list) and isinstance(old_rows, list)
    old_summary, new_summary = _computed_review_summary(old_rows), _computed_review_summary(rows)
    if (
        len(old_bindings) != 25
        or len(old_facts) != 143
        or len(old_rows) != 338
        or old_summary != subject._PREDECESSOR_REVIEW_SUMMARY
        or predecessor_artifact.get("review_summary") != old_summary
    ):
        _fail("PUBLISHED_PREDECESSOR_ARTIFACT_INVALID")
    if len(bindings) != 26 or len(facts) != 147 or len(rows) != 338:
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if any(
        type(item) is not dict
        or set(item) != set(subject._SOURCE_BINDING_FIELDS)
        or item.get("path_namespace") != "repository_parent_relative"
        or str(item.get("source_path", "")).startswith("/")
        for item in bindings
    ):
        _fail("ARTIFACT_SOURCE_BINDING_SCHEMA_INVALID")
    if len({_stable_identity(item) for item in bindings}) != 26 or len({item["review_unit_id"] for item in bindings}) != 26:
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
        "byte_count": 33043,
        "sha256": "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
        "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
    }
    if bindings[-1] != expected_binding:
        _fail("6OA_SOURCE_BINDING_INVALID")
    if facts[:143] != old_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if facts[143:] != expected_projection:
        _fail("6OA_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION")
    if len({item.get("canonical_event_id") for item in facts}) != 147:
        _fail("CANONICAL_EVENT_ID_DUPLICATE")
    if any(
        item.get("legacy_completed_review_status") != generic.COMPLETED_HUMAN_NEGATIVE
        or item.get("task_relevance_disposition") != generic.TASK_NOT_RELEVANT
        or item.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
        or item.get("training_disposition") != generic.TRAINING_NOT_APPLICABLE
        or item.get("human_training_excluded") is not False
        for item in facts[143:]
    ):
        _fail("6OA_CLASSIFICATION_INVALID")
    if new_summary != subject._SUCCESSOR_REVIEW_SUMMARY or artifact.get("review_summary") != new_summary:
        _fail("ARTIFACT_REVIEW_SUMMARY_INVALID")
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(old_rows, rows, strict=True):
        if old.get("canonical_event_id") not in targets:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old[key] != new[key]}
        if (
            old.get("raw_priority_rank") != "29"
            or old.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or old.get("raw_unit_event_count") != "4"
            or old.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or old.get("calibration_eligible") != "true"
            or old.get("calibration_exclusion_reason") != ""
            or changed != subject._ALLOWED_RECONCILIATION_FIELDS
            or new.get("current_review_status") != generic.COMPLETED_HUMAN_NEGATIVE
            or new.get("current_status_authority_sources_json") != generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
            or new.get("calibration_eligible") != "false"
            or new.get("calibration_exclusion_reason") != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("6OA_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("RECONCILIATION_DELTA_NOT_EXACT4_ONLY")
    return {
        "source_count": 26,
        "accepted_fact_count": 147,
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
    before = subject.PREDECESSOR_COVERAGE_SUMMARY if predecessor_coverage is None else predecessor_coverage
    after = subject.SUCCESSOR_COVERAGE_SUMMARY if successor_coverage is None else successor_coverage
    if before != subject.PREDECESSOR_COVERAGE_SUMMARY or subject.PREDECESSOR_COVERAGE_SUMMARY != predecessor.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("PREDECESSOR_COVERAGE_DRIFT")
    if after != subject.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("SUCCESSOR_COVERAGE_DRIFT")
    before_distribution, after_distribution = before.get("decision_category_distribution"), after.get("decision_category_distribution")
    if type(before_distribution) is not dict or type(after_distribution) is not dict:
        _fail("COVERAGE_DISTRIBUTION_NOT_OBJECT")
    for coverage, facts, source_count in ((before, predecessor_facts, 25), (after, successor_facts, 26)):
        if (
            coverage.get("accepted_fact_count") != len(facts)
            or coverage.get("accepted_review_unit_count") != source_count
            or coverage.get("stable_source_identity_count") != source_count
            or coverage.get("remaining_unreviewed_chemistry_event_count") != 338 - len(facts)
            or coverage.get("remaining_unreviewed_review_unit_upper_bound") != 131 - source_count
            or coverage.get("label_ready_event_count") != 16
            or coverage.get("training_mask_target_count") != 0
            or coverage.get("training_authority") is not False
        ):
            _fail("COVERAGE_DIRECT_EVIDENCE_MISMATCH")
    appended = successor_facts[143:]
    if (
        sum(before_distribution.values()) != len(predecessor_facts)
        or sum(after_distribution.values()) != len(successor_facts)
        or after_distribution["task_domain_negative"] - before_distribution["task_domain_negative"] != 4
        or any(after_distribution[key] != before_distribution[key] for key in ("chemistry_positive", "chemistry_negative", "task_domain_positive"))
        or successor_facts[:143] != predecessor_facts
        or len(appended) != 4
        or [fact.get("canonical_event_id") for fact in appended] != list(ingestion.EXPECTED_EVENT_IDS)
        or any(
            fact.get("legacy_completed_review_status") != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.get("task_relevance_disposition") != generic.TASK_NOT_RELEVANT
            or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
            or fact.get("training_disposition") != generic.TRAINING_NOT_APPLICABLE
            or fact.get("human_training_excluded") is not False
            for fact in appended
        )
        or after["label_ready_event_count"] != before["label_ready_event_count"]
        or after["training_mask_target_count"] != before["training_mask_target_count"]
    ):
        _fail("6OA_COVERAGE_DELTA_INVALID")
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
    _verify_operation_boundary(copy.deepcopy(_OPERATION_BOUNDARY) if operation_boundary is None else operation_boundary)
    return report


def _verify_byte_identity(expected: bytes, observed: bytes) -> None:
    if expected != observed:
        _fail("MATERIALIZED_ARTIFACT_BYTES_MISMATCH")


def _review_summary_probe_candidate(
    artifact: dict[str, Any], field: str, value: int
) -> dict[str, Any]:
    candidate = copy.deepcopy(artifact)
    candidate["review_summary"][field] = value
    return candidate


def _coverage_probe_candidate(
    field: str, value: object, *, decision_category: bool = False
) -> dict[str, object]:
    coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY)
    target = coverage["decision_category_distribution"] if decision_category else coverage
    assert isinstance(target, dict)
    target[field] = value
    return coverage


def _raw_byte_corruption_probe(observed_payload: bytes) -> None:
    _verify_byte_identity(observed_payload, observed_payload + b" ")


def _expect_tamper(
    name: str,
    expected_token: str,
    callback: Callable[[], object],
) -> str:
    try:
        callback()
    except ValueError as error:
        text = str(error)
        required = "COVAPIE_6OA_RECONCILIATION_V1_ERROR:" + expected_token
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

    def fact_probe(
        name: str,
        index: int,
        key: str,
        value: object,
        expected_token: str,
    ) -> None:
        candidate = copy.deepcopy(artifact)
        candidate["normalized_facts"][index][key] = value
        probes[name] = _expect_tamper(
            name, expected_token, lambda: semantic(candidate)
        )

    def row_probe(
        name: str,
        index: int,
        key: str,
        value: object,
        expected_token: str,
    ) -> None:
        candidate = copy.deepcopy(artifact)
        candidate["reconciled_rows"][index][key] = value
        probes[name] = _expect_tamper(
            name, expected_token, lambda: semantic(candidate)
        )

    def rich_probe(
        name: str,
        expected_token: str,
        mutate: Callable[[dict[str, Any]], None],
    ) -> None:
        candidate = copy.deepcopy(bound)
        mutate(candidate)
        probes[name] = _expect_tamper(
            name,
            expected_token,
            lambda: subject._project_bound_6oa_v1(candidate),
        )

    fact_projection_token = "6OA_FACTS_NOT_EXACT_INDEPENDENT_PROJECTION"
    fact_probe(
        "wrong_review_unit", -1, "review_unit_id", "WRONG_UNIT", fact_projection_token
    )
    candidate = copy.deepcopy(artifact)
    candidate["normalized_facts"].pop()
    probes["missing_6oa_event"] = _expect_tamper(
        "missing_6oa_event", "ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate)
    )
    fact_probe(
        "duplicate_6oa_event",
        -1,
        "canonical_event_id",
        ingestion.EXPECTED_EVENT_IDS[0],
        fact_projection_token,
    )
    for name, key, value in (
        ("normalized_relevant", "task_relevance_disposition", generic.TASK_RELEVANT),
        ("chemistry_negative", "chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("legacy_positive", "legacy_completed_review_status", generic.COMPLETED_HUMAN_POSITIVE),
        ("training_include", "training_disposition", generic.TRAINING_INCLUDE),
        ("training_exclude_only", "training_disposition", generic.TRAINING_EXCLUDE),
        ("human_training_excluded_true", "human_training_excluded", True),
        ("formal_source_sha_drift", "source_decision_sha256", "0" * 64),
    ):
        fact_probe(name, -1, key, value, fact_projection_token)
    for name, field in (
        ("generic_schema_11_to_12", "twelfth_field"),
        ("pair_leak", "reactive_pair"),
        ("role_leak", "role_profile"),
        ("seed_leak", "minimal_seed"),
        ("task_id_leak", "applicable_task_ids"),
        ("geometry_outlier_leak", "geometry_outlier"),
        ("PRE_leak", "PRE"),
    ):
        fact_probe(name, -1, field, "FORGED", "ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1], candidate["source_bindings"][-2] = candidate["source_bindings"][-2], candidate["source_bindings"][-1]
    probes["source_append_reordered"] = _expect_tamper(
        "source_append_reordered",
        "PREDECESSOR_SOURCE_PREFIX_INVALID",
        lambda: semantic(candidate),
    )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][-1] = copy.deepcopy(candidate["source_bindings"][0])
    probes["duplicate_source_identity"] = _expect_tamper(
        "duplicate_source_identity",
        "ARTIFACT_SOURCE_IDENTITY_DUPLICATE",
        lambda: semantic(candidate),
    )
    fact_probe(
        "predecessor_fact_modified",
        0,
        "source_decision_sha256",
        "0" * 64,
        "PREDECESSOR_FACT_PREFIX_INVALID",
    )
    candidate = copy.deepcopy(artifact)
    candidate["source_bindings"][0]["sha256"] = "0" * 64
    probes["predecessor_binding_modified"] = _expect_tamper(
        "predecessor_binding_modified",
        "PREDECESSOR_SOURCE_PREFIX_INVALID",
        lambda: semantic(candidate),
    )

    target_indices = [index for index, row in enumerate(artifact["reconciled_rows"]) if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS]
    if len(target_indices) != 4:
        _fail("TAMPER_TARGET_DISCOVERY_INVALID")
    non_target = next(index for index, row in enumerate(artifact["reconciled_rows"]) if row.get("canonical_event_id") not in ingestion.EXPECTED_EVENT_IDS)
    for name, index, field, value, expected_token in (
        (
            "6oa_row_remains_unreviewed",
            target_indices[0],
            "current_review_status",
            generic.CURRENTLY_UNREVIEWED,
            "REVIEW_UNIT_MIXED_STATUS",
        ),
        (
            "wrong_authority_source",
            target_indices[0],
            "current_status_authority_sources_json",
            "[]",
            "6OA_RECONCILIATION_TRANSITION_INVALID",
        ),
        (
            "calibration_remains_eligible",
            target_indices[0],
            "calibration_eligible",
            "true",
            "6OA_RECONCILIATION_TRANSITION_INVALID",
        ),
        (
            "wrong_exclusion_reason",
            target_indices[0],
            "calibration_exclusion_reason",
            "WRONG",
            "6OA_RECONCILIATION_TRANSITION_INVALID",
        ),
        (
            "fifth_row_changes",
            non_target,
            "calibration_exclusion_reason",
            "FORGED",
            "RECONCILIATION_DELTA_NOT_EXACT4_ONLY",
        ),
        (
            "non_target_row_changes",
            non_target,
            "raw_priority_rank",
            "999",
            "RECONCILIATION_DELTA_NOT_EXACT4_ONLY",
        ),
    ):
        row_probe(name, index, field, value, expected_token)
    old_rank = copy.deepcopy(old)
    old_target = next(row for row in old_rank["reconciled_rows"] if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS)
    old_target["raw_priority_rank"] = "30"
    probes["wrong_raw_priority_rank"] = _expect_tamper(
        "wrong_raw_priority_rank",
        "6OA_RECONCILIATION_TRANSITION_INVALID",
        lambda: _verify_artifact_semantics(artifact, predecessor_artifact=old_rank, expected_projection=projection),
    )

    rich_probe(
        "OUT_OF_DOMAIN_source_value_lost",
        "6OA_D1_D6_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["formal_decisions"][
            "D2_task_generation_domain_relevance"
        ].__setitem__("decision", "NOT_RELEVANT"),
    )
    rich_probe(
        "sixth_task_drift",
        "6OA_EXACT5_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["canonical_Exact5"].__setitem__(
            "sixth_task", True
        ),
    )
    rich_probe(
        "B3_drift",
        "6OA_EXACT5_BOUNDARY_INVALID",
        lambda value: value["formal_document"]["canonical_Exact5"].__setitem__(
            "B3_present", False
        ),
    )

    for name, field, value in (
        ("completed_positive_incorrectly_plus4", "completed_positive_event_count", 127),
        ("completed_negative_not_plus4", "completed_negative_event_count", 44),
    ):
        candidate = _review_summary_probe_candidate(artifact, field, value)
        probes[name] = _expect_tamper(
            name,
            "ARTIFACT_REVIEW_SUMMARY_INVALID",
            lambda candidate=candidate: semantic(candidate),
        )
    for name, field, value in (
        ("task_domain_negative_not_plus4", "task_domain_negative", 27),
        ("chemistry_positive_coverage_plus4", "chemistry_positive", 103),
    ):
        coverage = _coverage_probe_candidate(
            field, value, decision_category=True
        )
        probes[name] = _expect_tamper(
            name,
            "SUCCESSOR_COVERAGE_DRIFT",
            lambda coverage=coverage: semantic(artifact, after_coverage=coverage),
        )
    for name, field, value in (
        ("label_ready_count_changed", "label_ready_event_count", 17),
        ("training_mask_target_positive", "training_mask_target_count", 1),
        ("training_authority_forged", "training_authority", True),
    ):
        coverage = _coverage_probe_candidate(field, value)
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
    probes["raw_byte_corruption"] = _expect_tamper(
        "raw_byte_corruption",
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
        lambda: _raw_byte_corruption_probe(observed_payload),
    )
    probes["filesystem_executable_bit"] = _expect_tamper(
        "filesystem_executable_bit",
        "EXACT4_TEXT_SIZE_OR_MODE_INVALID",
        lambda: _validate_text_payload(b"ok\n", 0o755, "probe"),
    )
    probes["unexpected_fifth_file"] = _expect_tamper(
        "unexpected_fifth_file",
        "CANDIDATE_UNTRACKED_NOT_STRICT_EXACT4",
        lambda: classify_repository_profile(
            expected_paths=tuple(path.as_posix() for path in subject.EXACT4_PATHS),
            tracked_paths=set(),
            ordinary_untracked={*(path.as_posix() for path in subject.EXACT4_PATHS), "unexpected.txt"},
            status_lines=tuple([*("?? " + path.as_posix() for path in subject.EXACT4_PATHS), "?? unexpected.txt"]),
            working_diff=set(),
            cached_diff=set(),
        ),
    )
    stage_lines = tuple(
        f"100644 {'0' * 40} 0\t{path.as_posix()}" for path in subject.EXACT4_PATHS
    )
    bad_mode_lines = list(stage_lines)
    bad_mode_lines[0] = bad_mode_lines[0].replace("100644", "100755", 1)
    probes["tracked_git_mode_not_100644"] = _expect_tamper(
        "tracked_git_mode_not_100644",
        "TRACKED_GIT_INDEX_MODE_INVALID",
        lambda: validate_tracked_index_modes(
            tuple(bad_mode_lines),
            {path.as_posix() for path in subject.EXACT4_PATHS},
        ),
    )
    return probes


def _lifecycle_simulations() -> dict[str, bool]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    expected = set(paths)
    if classify_repository_profile(
        expected_paths=paths,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in paths),
        working_diff=set(),
        cached_diff=set(),
    ) != CANDIDATE_UNTRACKED:
        _fail("CANDIDATE_SIMULATION_FAILED")
    if classify_repository_profile(
        expected_paths=paths,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) != TRACKED_CLEAN:
        _fail("TRACKED_SIMULATION_FAILED")
    stage_lines = tuple(
        f"100644 {'0' * 40} 0\t{path}" for path in paths
    )
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
    validate_repository_relation_values(**common, head="successor", origin_main=BASELINE_COMMIT, ahead=1)
    validate_repository_relation_values(**common, head="successor", origin_main="successor", ahead=0)
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
    observed_payload = _read_regular(root / subject.OUTPUT_RELATIVE, "6OA_ARTIFACT")
    artifact = _strict_json(observed_payload, "6OA_ARTIFACT")
    artifact_report = _verify_full_semantics(
        artifact,
        predecessor_artifact=old,
        expected_projection=projection,
    )
    coverage = _verify_coverage_contract(old["normalized_facts"], artifact["normalized_facts"])
    first_build, second_build = subject.build_artifact_v1(root), subject.build_artifact_v1(root)
    _verify_byte_identity(first_build, observed_payload)
    if first_build != second_build:
        _fail("DETERMINISTIC_DOUBLE_BUILD_MISMATCH")
    materialized = subject.check_materialized_v1(root)
    tamper = _tamper_probes(
        artifact, old, projection, bound, observed_payload
    )
    lifecycle = _lifecycle_simulations()
    if not (
        materialized.get("status") == "PASS"
        and subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False
        and bound["formal_document"]["canonical_Exact5"]["B3_present"] is True
        and bound["formal_document"]["canonical_Exact5"]["sixth_task"] is False
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
            "predecessor_sources": 25,
            "successor_sources": 26,
            "predecessor_facts": 143,
            "successor_facts": 147,
            "prefix_preserved": True,
        },
        "6OA_boundary": {
            "event_count": 4,
            "source_formal_generation_domain_decision": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "normalization_mapping": "OUT_OF_DOMAIN_TO_NOT_RELEVANT",
            "legacy_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "chemistry": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": False,
            "pair": "SG:C5",
            "B3_present": True,
            "sixth_task": False,
            "task_label_authority": False,
            "formal_training_admitted": False,
        },
        "review_summary": {"predecessor": old["review_summary"], "successor": artifact["review_summary"]},
        "coverage": coverage,
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
        print("COVAPIE_6OA_RECONCILIATION_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("COVAPIE_6OA_RECONCILIATION_V1_PASS=true")
    print("lifecycle=" + str(report["repository"]["lifecycle"]))
    print("source_count=26")
    print("accepted_fact_count=147")
    print("reconciled_row_count=338")
    print("generic_fact_field_count=11")
    print("rich_fields_leaked=false")
    print("changed_target_rows=4")
    print("non_target_changed_rows=0")
    print("unchanged_rows=334")
    print("completed_negative_event_count=48")
    print("completed_negative_unit_count=10")
    print("task_domain_negative_coverage=28")
    print("census_refresh=false")
    print("queue_refresh=false")
    print("ready_for_training=false")
    print("training_started=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
