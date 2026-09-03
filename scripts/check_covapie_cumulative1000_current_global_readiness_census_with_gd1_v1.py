#!/usr/bin/env python3
"""Independent fail-closed checker for the cumulative1000 GD1 refresh V1."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_gd1_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_gd1_v1 as subject  # noqa: E402


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part", ".log",
)
MAX_FILE_BYTES = 1024 * 1024
BASELINE_COMMIT = "5d86db98a993ade9b787845c834f6cca6062f542"
EXPECTED_CENSUS_SHA256 = "90b8038047e08b0c43537ec8738a46b741468ee7a66633a863f244039485264c"
EXPECTED_SUMMARY_SHA256 = "6b96964f77321ffa07504d8a6c06b974ba6525bba2d5acb3bc3298c697d4058c"
EXPECTED_BINDINGS_SHA256 = "7bd1f4dc6521962a183b066b7f993f580d0a0288c4d2e316f80097026111b066"
AUTHORIZED_OVERLAY_FIELDS = subject._AUTHORIZED_GD1_OVERLAY_FIELDS_V1
EXPECTED_CHANGED_FIELDS = AUTHORIZED_OVERLAY_FIELDS - {
    "training_use_include", "future_training_admission_candidate"
}
FROZEN_BINDINGS = (
    *subject._ADDITIVE_SOURCE_SPECS_V1,
    (
        "PREDECESSOR_WITH_4M5_MATERIALIZED_MANIFEST",
        subject.PREDECESSOR_MANIFEST_RELATIVE,
        "repository_relative",
        subject._PREDECESSOR_MANIFEST_SPEC_V1[0],
        subject._PREDECESSOR_MANIFEST_SPEC_V1[1],
        subject._PREDECESSOR_MANIFEST_SPEC_V1[2],
    ),
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )


def _read(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    return path.read_bytes()


def _validate_text(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_FORBIDDEN:" + label)
    text = payload.decode("utf-8")
    if "\x00" in text or "\r" in text:
        raise ValueError("TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def _parse_census(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    rows = [dict(row) for row in reader]
    if (
        tuple(reader.fieldnames or ()) != subject.CENSUS_COLUMNS_V1
        or len(subject.CENSUS_COLUMNS_V1) != 47
        or len(rows) != 1000
        or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows)
    ):
        raise ValueError("CENSUS_NOT_EXACT1000_SCHEMA47")
    return rows


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if not output.is_dir() or output.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if sorted(path.name for path in output.iterdir()) != sorted(
        (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    ):
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")
    bindings: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, "EXACT7:" + relative)
        _validate_text(payload, relative)
        mode = path.lstat().st_mode
        executable = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if (
            not stat.S_ISREG(mode)
            or not mode & stat.S_IRUSR
            or mode & stat.S_IWOTH
            or mode & executable
            or path.name.endswith(FORBIDDEN_SUFFIXES)
            or len(payload) > MAX_FILE_BYTES
        ):
            raise ValueError("EXACT7_FILE_CLASS_INVALID:" + relative)
        bindings.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "executable_class": "NON_EXECUTABLE",
            }
        )
    return bindings


def verify_frozen_bindings_v1(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, sha256, executable in FROZEN_BINDINGS:
        if namespace != "repository_relative":
            raise ValueError("FROZEN_BINDING_NAMESPACE_INVALID:" + role)
        try:
            subject.verify_bound_source_v2(
                path=root / relative,
                expected_byte_count=byte_count,
                expected_sha256=sha256,
                label=role + ":" + relative.as_posix(),
                expected_executable=executable,
            )
        except subject.SourceBindingPolicyV2Error as error:
            raise ValueError("FROZEN_BINDING_INVALID:" + role) from error
        result.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
                "expected_executable": executable,
            }
        )
    return result


def independently_verify_matrix_v1(root: Path) -> list[dict[str, str]]:
    payload = _read(root / subject.GD1_EVENT_MATRIX_RELATIVE, "GD1_MATRIX")
    built = ingestion.build_artifacts_v1(root)
    if built[ingestion.MATRIX] != payload:
        raise ValueError("GD1_MATRIX_NOT_SOURCE_DERIVED")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    rows = [dict(row) for row in reader]
    if (
        tuple(reader.fieldnames or ()) != ingestion.MATRIX_HEADER
        or tuple(row["canonical_event_id"] for row in rows) != ingestion.EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in rows] != [691, 692, 693, 694]
    ):
        raise ValueError("GD1_MATRIX_IDENTITY_INVALID")
    expected = {
        "human_review_completed": "true",
        "human_task_relevance_decision": "RELEVANT",
        "human_chemistry_decision": "POSITIVE",
        "reactive_pair_human_authoritative": "true",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C77",
        "role_partition_human_authoritative": "true",
        "selected_candidate_index_0based": "0",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "W_L_S_counts_json": "[2,0,11]",
        "direct_profile_applicable_task_ids_json": "[0,3,4]",
        "authoritative_task_labels_created": "false",
        "event_task_label_rows_materialized": "false",
        "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
        "training_use_allowed": "false",
        "human_training_excluded": "true",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "supporting_PRE_source_graph_count_per_event": "0",
        "PRE_source_graph_present": "false",
        "PRE_source_graph_count_per_event": "0",
        "PRE_mapping_count_per_event": "0",
        "PRE_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
        "PRE_status": "PRE_REACTION_UNRESOLVED",
        "PRE_topology_authority": "false",
        "PRE_geometry_authority": "false",
        "PRE_coordinates_authority": "false",
        "PRE_reconstruction": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "POST_source_evidence_available": "true",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
    }
    for row in rows:
        if any(row[field] != value for field, value in expected.items()):
            raise ValueError("GD1_MATRIX_SEMANTICS_INVALID:" + row["canonical_event_id"])
        tasks = json.loads(row["canonical_task_applicability_json"])
        if (
            [item["task_id"] for item in tasks] != [0, 1, 2, 3, 4]
            or [item["semantic_long_name"] for item in tasks]
            != ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
            or [item["task_id"] for item in tasks if item["structurally_applicable"]] != [0, 3, 4]
            or json.loads(row["boundary_bonds_json"]) != list(ingestion.BOUNDARY_BONDS)
        ):
            raise ValueError("GD1_MATRIX_EXACT5_INVALID")
    return rows


def independently_verify_delta_v1(
    root: Path, rows: Sequence[dict[str, str]]
) -> dict[str, object]:
    predecessor_payload = _read(root / subject.PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS")
    before_rows = _parse_census(predecessor_payload)
    before = {row["canonical_event_id"]: row for row in before_rows}
    after = {row["canonical_event_id"]: row for row in rows}
    exact4 = set(ingestion.EXPECTED_EVENT_IDS)
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    if set(before) != set(after) or changed != exact4:
        raise ValueError("DELTA_NOT_EXACT_GD1_EXACT4")
    if any(before[event_id] != after[event_id] for event_id in set(before) - exact4):
        raise ValueError("NON_GD1_ROW_CHANGED")
    for event_id in exact4:
        fields = {field for field in subject.CENSUS_COLUMNS_V1 if before[event_id][field] != after[event_id][field]}
        if fields != EXPECTED_CHANGED_FIELDS:
            raise ValueError("GD1_CHANGED_FIELD_SET_INVALID:" + event_id)
        expected = {
            "current_global_status": "COMPLETED_HUMAN_POSITIVE",
            "current_review_status": "COMPLETED_HUMAN_POSITIVE",
            "human_review_completed": "true",
            "human_review_authority_source": subject.GD1_HUMAN_DECISION_SOURCE,
            "chemistry_disposition": "POSITIVE",
            "chemistry_authority_source": subject.GD1_EVENT_MATRIX_SOURCE,
            "positive_authority_source": subject.GD1_EVENT_MATRIX_SOURCE,
            "task_relevance_disposition": "RELEVANT",
            "task_relevance_authority_source": subject.GD1_EVENT_MATRIX_SOURCE,
            "training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "human_training_excluded": "true",
            "reactive_pair_sample_authoritative": "true",
            "role_partition_sample_authoritative": "true",
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "canonical_mask_structural_labels_available": "true",
            "structurally_applicable_task_ids_json": "[0,3,4]",
            "training_use_include": "false",
            "future_training_admission_candidate": "false",
            "training_materialization_allowed_current_source": "false",
            "reactive_pair_training_target_available": "false",
            "post_geometry_sample_authoritative": "false",
            "post_geometry_training_target_available": "false",
            "pre_geometry_authoritative": "false",
            "pre_geometry_training_target_available": "false",
            "formal_split_authoritative": "false",
            "formal_training_admitted": "false",
            "current_runtime_model_usable": "false",
        }
        if any(after[event_id][field] != value for field, value in expected.items()):
            raise ValueError("GD1_AFTER_SEMANTICS_INVALID:" + event_id)
    return {
        "row_count": len(rows),
        "column_count": len(subject.CENSUS_COLUMNS_V1),
        "changed_event_count": len(changed),
        "unchanged_event_count": len(rows) - len(changed),
        "authorized_overlay_field_count": len(AUTHORIZED_OVERLAY_FIELDS),
        "actual_changed_field_count_per_event": len(EXPECTED_CHANGED_FIELDS),
    }


def independently_verify_counts_v1(
    rows: Sequence[dict[str, str]], summary: dict[str, object]
) -> None:
    if Counter(row["current_global_status"] for row in rows) != Counter(subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1):
        raise ValueError("GLOBAL_STATUS_COUNTS_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter({"POSITIVE": 128, "NOT_ESTABLISHED": 90, "UNRESOLVED": 782}):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter({"RELEVANT": 129, "NOT_RELEVANT": 90, "UNRESOLVED": 781}):
        raise ValueError("TASK_RELEVANCE_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter({"INCLUDE": 56, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 90, "UNRESOLVED": 782}):
        raise ValueError("TRAINING_USE_COUNTS_INVALID")
    for field, expected in subject._EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            raise ValueError("BOOLEAN_COUNT_INVALID:" + field)
    profiles = Counter(row["role_profile"] for row in rows if row["role_partition_sample_authoritative"] == "true")
    if profiles != Counter({"DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 76, "STRICT_LINKER_PRESENT_V1": 52}):
        raise ValueError("ROLE_PROFILE_COUNTS_INVALID")
    applicability: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    if applicability != Counter({0: 128, 1: 52, 2: 52, 3: 128, 4: 128}):
        raise ValueError("EXACT5_COUNTS_INVALID")
    geometry = summary["geometry"]  # type: ignore[index]
    if (
        geometry["POST_source_evidence_available_count"] != 867
        or geometry["POST_sample_authoritative_count"] != 21
        or geometry["POST_training_target_available_count"] != 17
        or geometry["PRE_source_evidence_available_count"] != 0
        or geometry["PRE_sample_authoritative_count"] != 0
        or geometry["PRE_training_target_available_count"] != 0
        or geometry["POST_to_PRE_promotion_performed"] is not False
        or geometry["PRE_zero_fill_performed"] is not False
    ):
        raise ValueError("PRE_POST_GEOMETRY_COUNTS_INVALID")
    blockers = summary["blockers"]  # type: ignore[index]
    expected_blockers = {
        "chemistry_unresolved": {"all_1000": 782},
        "pair_authority_absent": {"all_1000": 872, "within_positive_128": 0},
        "role_authority_absent": {"all_1000": 872, "within_positive_128": 0},
        "human_training_exclusion": {"within_positive_128": 72},
        "missing_split_authority": {"within_positive_128": 87, "within_include_56": 31},
        "missing_POST_training_authority": {"within_positive_128": 111, "within_include_56": 39},
        "missing_training_admission": {"within_positive_128": 123, "within_include_56": 51},
        "feature_semantics_pending": {"within_positive_128": 128},
    }
    for key, expected in expected_blockers.items():
        if blockers[key] != expected:
            raise ValueError("BLOCKER_COUNT_INVALID:" + key)
    tensor = blockers["missing_tensor_integration"]
    if (
        tensor["within_positive_128"] != 87
        or tensor["within_include_56"] != 27
        or tensor["missing_source_composition"].get("GD1") != 4
    ):
        raise ValueError("TENSOR_BLOCKER_INVALID")


def independently_compute_top10_v1(
    root: Path, reconciled_rows: Sequence[dict[str, str]]
) -> list[dict[str, object]]:
    queue_payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "FROZEN_PRIORITY_QUEUE")
    if len(queue_payload) != 50116 or _sha(queue_payload) != "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2":
        raise ValueError("PRIORITY_QUEUE_BINDING_INVALID")
    queue = list(csv.DictReader(io.StringIO(queue_payload.decode("utf-8"), newline="")))
    statuses: dict[str, set[str]] = defaultdict(set)
    for row in reconciled_rows:
        statuses[row["raw_review_unit_id"]].add(row["current_review_status"])
    candidates: list[tuple[int, int, str, dict[str, str], str]] = []
    for row in queue:
        unit_statuses = statuses[row["review_unit_id"]]
        if len(unit_statuses) != 1:
            raise ValueError("QUEUE_STATUS_NOT_UNIQUE")
        status = next(iter(unit_statuses))
        if status in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            candidates.append((-int(row["event_count"]), int(row["priority_rank"]), row["review_unit_id"], row, status))
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 109 or any(item[2] == subject.GD1_REVIEW_UNIT_ID_V1 for item in candidates):
        raise ValueError("GD1_PENDING_OR_PENDING_COUNT_INVALID")
    return [
        {
            "rank": rank,
            "raw_priority_rank": priority,
            "review_unit_id": unit,
            "event_count": int(row["event_count"]),
            "pdb_ids": json.loads(row["pdb_ids_json"]),
            "ligand_component_ids": json.loads(row["ligand_component_ids_json"]),
            "full_coordinate_count": int(row["full_coordinate_event_count"]),
            "exact_pair_count": int(row["exact_reactive_pair_event_count"]),
            "ccd_complete_count": int(row["CCD_graph_complete_event_count"]),
            "post_source_evidence_count": int(row["POST_geometry_available_event_count"]),
            "current_review_status": status,
        }
        for rank, (_negative, priority, unit, row, status) in enumerate(candidates[:10], 1)
    ]


def _reject_dynamic_manifest_metadata(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"timestamp", "hostname", "pid", "head", "commit_subject", "ahead", "behind", "lifecycle_profile"}:
                raise ValueError("MANIFEST_DYNAMIC_FIELD_FORBIDDEN:" + path + "." + str(key))
            _reject_dynamic_manifest_metadata(child, path + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_dynamic_manifest_metadata(child, f"{path}[{index}]")
    elif isinstance(value, str) and value.startswith("/"):
        raise ValueError("MANIFEST_ABSOLUTE_PATH_FORBIDDEN:" + path)


def verify_manifest_v1(manifest: dict[str, object], computation: object) -> None:
    _reject_dynamic_manifest_metadata(manifest)
    if (
        manifest["candidate_inventory"] != {"exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)}
        or manifest["semantic_source_bindings"] != list(computation.semantic_source_bindings)
        or len(manifest["semantic_source_bindings"]) != 138
        or manifest["predecessor_manifest_validation_binding"]["path"] != subject.PREDECESSOR_MANIFEST_RELATIVE.as_posix()
        or manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is not False
        or manifest["refresh_contract"]["column_count"] != 47
        or manifest["refresh_contract"]["authorized_overlay_field_count"] != 19
        or manifest["refresh_contract"]["actual_changed_field_count_per_gd1_row"] != 17
        or manifest["refresh_contract"]["queue_refreshed"] is not False
        or manifest["refresh_contract"]["next_review_started"] is not False
    ):
        raise ValueError("MANIFEST_CONTRACT_INVALID")
    for binding in manifest["semantic_source_bindings"]:
        if "mode" in binding or "exact_posix_mode" in binding:
            raise ValueError("NUMERIC_POSIX_MODE_SEMANTIC_IDENTITY_FORBIDDEN")
    if "sha256" in manifest["manifest_self_binding"]:
        raise ValueError("MANIFEST_SELF_SHA_FORBIDDEN")


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ("git", *args), cwd=root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _classify_exact7_artifact_placement_v1(
    tracked_paths: Sequence[str], ordinary_untracked_paths: Sequence[str]
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    if not tracked_paths and len(ordinary_untracked_paths) == 7 and set(ordinary_untracked_paths) == expected:
        return "CANDIDATE_UNTRACKED"
    if len(tracked_paths) == 7 and set(tracked_paths) == expected and not ordinary_untracked_paths:
        return "TRACKED_CLEAN"
    raise ValueError("EXACT7_ARTIFACT_PLACEMENT_INVALID")


def _classify_repository_lifecycle_v1(
    *,
    placement: str,
    head: str,
    origin: str,
    ahead: int,
    behind: int,
    baseline_is_ancestor_of_head: bool,
    baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool,
    baseline_to_head_changed_paths: Sequence[str],
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    changed = set(baseline_to_head_changed_paths)
    if placement == "CANDIDATE_UNTRACKED":
        if not (
            head == origin == BASELINE_COMMIT
            and ahead == behind == 0
            and baseline_is_ancestor_of_head
            and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head
            and not changed
        ):
            raise ValueError("CANDIDATE_UNTRACKED_LIFECYCLE_INVALID")
        return placement
    if placement != "TRACKED_CLEAN":
        raise ValueError("LIFECYCLE_PROFILE_UNSUPPORTED")
    if (
        head == BASELINE_COMMIT
        or behind != 0
        or ahead < 0
        or not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or not expected <= changed
        or ((ahead == 0) != (origin == head))
    ):
        raise ValueError("TRACKED_CLEAN_LIFECYCLE_INVALID")
    return placement


def check_lifecycle_simulations_v1() -> dict[str, bool]:
    expected = set(subject.EXACT7_PATHS_V1)
    future = {"docs/future-successor.md", "src/covalent_ext/future_successor.py"}
    candidate = dict(
        placement="CANDIDATE_UNTRACKED", head=BASELINE_COMMIT,
        origin=BASELINE_COMMIT, ahead=0, behind=0,
        baseline_is_ancestor_of_head=True, baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True, baseline_to_head_changed_paths=(),
    )
    tracked = dict(
        placement="TRACKED_CLEAN", head="synthetic-head",
        origin="synthetic-origin-between", ahead=2, behind=0,
        baseline_is_ancestor_of_head=True, baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=tuple(expected | future),
    )
    _classify_repository_lifecycle_v1(**candidate)
    _classify_repository_lifecycle_v1(**tracked)
    _classify_repository_lifecycle_v1(**{**tracked, "origin": "synthetic-head", "ahead": 0})
    for updates in (
        {"behind": 1},
        {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False},
        {"baseline_to_head_changed_paths": tuple(expected - {next(iter(expected))})},
    ):
        try:
            _classify_repository_lifecycle_v1(**{**tracked, **updates})
        except ValueError:
            continue
        raise ValueError("LIFECYCLE_FAIL_CLOSED_SIMULATION_ACCEPTED")
    return {
        "candidate_untracked": True,
        "tracked_clean": True,
        "multiple_commits_allowed": True,
        "unrelated_successors_allowed": True,
        "origin_between_baseline_and_head_allowed": True,
        "fail_closed_cases": True,
    }


def _git_is_ancestor(root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer), cwd=root,
        check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise ValueError("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def verify_git_and_cache_safety_v1(root: Path) -> dict[str, object]:
    working = _git(root, "diff", "--name-only")
    staged = _git(root, "diff", "--cached", "--name-only")
    status = _git(root, "status", "--short", "--untracked-files=all")
    if working or staged:
        raise ValueError("TRACKED_OR_STAGED_CHANGE_PRESENT")
    tracked_exact7 = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    placement = _classify_exact7_artifact_placement_v1(tracked_exact7, untracked)
    if placement == "CANDIDATE_UNTRACKED" and set(status) != {"?? " + path for path in subject.EXACT7_PATHS_V1}:
        raise ValueError("CANDIDATE_UNTRACKED_STATUS_NOT_EXACT7")
    if placement == "TRACKED_CLEAN" and status:
        raise ValueError("TRACKED_CLEAN_STATUS_NOT_EMPTY")
    head = _git(root, "rev-parse", "HEAD")[0]
    origin = _git(root, "rev-parse", "origin/main")[0]
    behind_text, ahead_text = _git(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")[0].split()
    if placement == "CANDIDATE_UNTRACKED":
        committed: list[str] = []
    else:
        committed = _git(root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD")
    lifecycle = _classify_repository_lifecycle_v1(
        placement=placement,
        head=head,
        origin=origin,
        ahead=int(ahead_text),
        behind=int(behind_text),
        baseline_is_ancestor_of_head=_git_is_ancestor(root, BASELINE_COMMIT, "HEAD"),
        baseline_is_ancestor_of_origin=_git_is_ancestor(root, BASELINE_COMMIT, "origin/main"),
        origin_is_ancestor_of_head=_git_is_ancestor(root, "origin/main", "HEAD"),
        baseline_to_head_changed_paths=committed,
    )
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in untracked):
        raise ValueError("UNTRACKED_FORBIDDEN_SUFFIX")
    caches: list[str] = []
    for directory, names, files in os.walk(root):
        relative = Path(directory).relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            names[:] = []
            continue
        for name in names:
            if name in {"__pycache__", ".pytest_cache"} and any((Path(directory) / name).iterdir()):
                caches.append((Path(relative) / name).as_posix())
        if any(name.endswith((".pyc", ".tmp", ".part", ".log")) for name in files):
            caches.append(relative)
    if caches:
        raise ValueError("CACHE_OR_TRANSIENT_FILE_PRESENT")
    protected = ("data/raw/", "checkpoints/", "equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py")
    if any(any(path == item.rstrip("/") or path.startswith(item) for item in protected) for path in set(working) | set(staged)):
        raise ValueError("PROTECTED_SOURCE_DIFF_PRESENT")
    return {
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(untracked),
        "exact7_artifact_placement_profile": placement,
        "repository_lifecycle_profile": lifecycle,
        "head": head,
        "origin_main": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "forbidden_artifact_count": 0,
        "cache_count": 0,
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    exact7 = verify_exact7_inventory_v1(root)
    frozen = verify_frozen_bindings_v1(root)
    independently_verify_matrix_v1(root)
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {
        name: _read(output / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    for name, payload in materialized.items():
        _validate_text(payload, name)
    rows = _parse_census(materialized[subject.CENSUS_FILE])
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    manifest = json.loads(materialized[subject.MANIFEST_FILE])
    delta = independently_verify_delta_v1(root, rows)
    independently_verify_counts_v1(rows, summary)

    # Full source-derived build #1, followed by exactly one deterministic rebuild.
    computation = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(root)
    built = subject._build_artifacts_from_computation_v1(root, computation)
    rebuilt = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_gd1_v1(root)
    if materialized != built or built != rebuilt:
        raise ValueError("MATERIALIZED_FRESH_OR_DETERMINISTIC_BUILD_MISMATCH")
    if (
        _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256
        or _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256
        or _sha(_canonical_json(list(computation.semantic_source_bindings)).encode("utf-8")) != EXPECTED_BINDINGS_SHA256
    ):
        raise ValueError("DERIVED_PROJECTION_DIGEST_INVALID")
    verify_manifest_v1(manifest, computation)

    reconciled = reconciliation.reconcile_real_completed_human_decisions_with_gd1_v1(root)
    if (
        len(reconciled.normalized_facts) != 115
        or len({fact.source_binding_path for fact in reconciled.normalized_facts}) != 18
        or reconciled.review_summary["completed_positive_event_count"] != 111
        or reconciled.review_summary["unreviewed_event_count"] != 199
    ):
        raise ValueError("RECONCILIATION_EXACT18_115_COUNTS_INVALID")
    top = independently_compute_top10_v1(root, reconciled.reconciled_rows)
    if summary["top_pending_review_units_by_event_yield"] != top or top[0]["rank"] != 1:
        raise ValueError("DYNAMIC_NEXT_PENDING_INVALID")
    boundary = summary["authority_boundary"]
    required_true = (
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE",
        "CURRENT_GLOBAL_RECONCILIATION_COMPLETE",
        "GD1_REVIEW_COMPLETED",
        "CENSUS_REFRESH",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    )
    required_false = (
        "QUEUE_REFRESH", "NEXT_REVIEW_STARTED", "TRAINING_STARTED",
        "READY_FOR_TRAINING", "formal_decision_read_directly",
        "formal_validator_executed", "new_human_authority_created",
        "new_chemistry_authority_created", "new_pair_authority_created",
        "new_role_authority_created", "new_reusable_authority_created",
        "reaction_family_authority", "warhead_rule_authority",
        "warhead_type_authority", "training_admission_created",
        "priority_queue_file_modified", "priority_queue_file_created",
    )
    if any(boundary[key] is not True for key in required_true) or any(boundary[key] is not False for key in required_false):
        raise ValueError("AUTHORITY_BOUNDARY_INVALID")
    lifecycle_simulations = check_lifecycle_simulations_v1()
    safety = verify_git_and_cache_safety_v1(root)
    return {
        "candidate_file_count": len(exact7),
        "frozen_binding_count": len(frozen),
        "semantic_source_binding_count": len(computation.semantic_source_bindings),
        **delta,
        "full_build_count_in_checker": 2,
        "two_full_builds_byte_identical": True,
        "gd1_pending": False,
        "pending_review_unit_count": 109,
        "next_pending": top[0],
        "lifecycle_simulations": lifecycle_simulations,
        **safety,
        "ready_for_training": False,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    if result["ready_for_training"] is not False:
        raise ValueError("READY_FOR_TRAINING_MUST_BE_FALSE")
    print("PASS")
    print(result["repository_lifecycle_profile"])
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
