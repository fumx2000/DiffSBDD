#!/usr/bin/env python3
"""Independent fail-closed checker for the cumulative1000 1N0 refresh V1."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_1n0_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_i12_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_1n0_v1 as subject  # noqa: E402
from covalent_ext import covapie_source_binding_future_exact_posix_mode_guard_v2 as b4_guard  # noqa: E402


BASELINE_COMMIT = "39b5ab6d9314e2779e25e0c2727caa76d0e7e994"
BASELINE_SUBJECT = "add CovaPIE 1N0 completed decision reconciliation v1"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part", ".log",
)
DYNAMIC_KEYS = {
    "generated_at", "created_at", "validated_at", "timestamp", "hostname",
    "host", "pid", "uuid", "cwd", "temporary_directory", "temporary_path",
    "output_path", "live_git_status", "git_head", "git_tree",
}
FORBIDDEN_MODE_KEYS = {
    "mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode",
}
EXPECTED_CHANGED_FIELDS = frozenset(
    {
        "chemistry_authority_source",
        "chemistry_disposition",
        "current_global_status",
        "current_review_status",
        "human_review_authority_source",
        "human_review_completed",
        "task_relevance_authority_source",
        "task_relevance_disposition",
        "training_use_disposition",
    }
)
EXPECTED_GLOBAL_COUNTS = Counter(
    {
        "CURRENTLY_UNREVIEWED": 211,
        "CURRENTLY_IN_PROGRESS": 0,
        "COMPLETED_HUMAN_POSITIVE": 99,
        "COMPLETED_HUMAN_NEGATIVE": 58,
        "COMPLETED_PARTIAL_AUTHORITY": 1,
        "CURRENT_RUNTIME_MODEL_USABLE": 17,
        "PUBLISHED_EXACT_AUTO_NEGATIVE": 32,
        "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
        "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
        "QUARANTINE_REPRESENTATION_GAP": 78,
        "REJECTED_FEATURE_INCOMPATIBLE": 2,
    }
)
EXPECTED_HUMAN_REVIEW = {
    "priority_review_population_event_count": 338,
    "review_unit_count": 131,
    "completed_event_count": 127,
    "completed_unit_count": 19,
    "completed_positive_event_count": 99,
    "completed_positive_unit_count": 14,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "unreviewed_event_count": 211,
    "unreviewed_unit_count": 112,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "pending_event_count": 211,
    "current_pending_review_unit_count": 112,
}
EXPECTED_REFRESH_DELTA = {
    "predecessor_currently_unreviewed_count": 215,
    "refreshed_currently_unreviewed_count": 211,
    "predecessor_completed_human_negative_global_count": 54,
    "refreshed_completed_human_negative_global_count": 58,
    "predecessor_chemistry_not_established_count": 86,
    "refreshed_chemistry_not_established_count": 90,
    "predecessor_task_not_relevant_count": 86,
    "refreshed_task_not_relevant_count": 90,
    "predecessor_training_not_applicable_count": 86,
    "refreshed_training_not_applicable_count": 90,
    "one_n0_exact4_delta_count": 4,
    "changed_event_count": 4,
    "unchanged_event_count": 996,
    "derived_refresh_not_new_authority": True,
}


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


def _git(root: Path, *args: str) -> list[str]:
    completed = subprocess.run(
        ("git", *args), cwd=root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def _parse_census(payload: bytes) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise ValueError("CENSUS_NOT_UTF8") from error
    if tuple(reader.fieldnames or ()) != subject.CENSUS_COLUMNS_V1:
        raise ValueError("CENSUS_HEADER_NOT_EXACT47")
    return [dict(row) for row in reader]


def _parse_json(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(label + "_JSON_INVALID") from error
    if type(value) is not dict:
        raise ValueError(label + "_ROOT_NOT_OBJECT")
    return value


def _validate_text(payload: bytes, label: str) -> None:
    if (
        not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        raise ValueError("TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("TEXT_NOT_UTF8:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def _reject_dynamic_metadata(value: object, path: str = "root") -> None:
    if type(value) is dict:
        for key, child in value.items():
            lowered = key.lower()
            false_determinism_marker = (
                lowered == "timestamps_recorded" and child is False
            )
            if not false_determinism_marker and (
                lowered in DYNAMIC_KEYS or "timestamp" in lowered
            ):
                raise ValueError("DYNAMIC_METADATA:" + path + "." + key)
            if lowered in FORBIDDEN_MODE_KEYS:
                raise ValueError("SEMANTIC_MODE_FIELD_FORBIDDEN:" + path + "." + key)
            _reject_dynamic_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_metadata(child, f"{path}[{index}]")
    elif type(value) is str and (
        value.startswith("/cpfs")
        or value.startswith("/home/")
        or value.startswith("/tmp/")
        or value.startswith("file://")
    ):
        raise ValueError("ABSOLUTE_MACHINE_PATH:" + path)


def verify_exact7_inventory_v1(root: Path) -> dict[str, object]:
    expected = set(subject.EXACT7_PATHS_V1)
    if len(expected) != 7 or len(subject.EXACT7_PATHS_V1) != 7:
        raise ValueError("EXACT7_INTERNAL_CONTRACT_INVALID")
    records: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, "EXACT7:" + relative)
        _validate_text(payload, relative)
        metadata = path.lstat()
        if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            raise ValueError("EXACT7_EXECUTABLE_FORBIDDEN:" + relative)
        records.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "expected_executable": False,
            }
        )

    working = _git(root, "diff", "--name-only")
    staged = _git(root, "diff", "--cached", "--name-only")
    ordinary_untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    tracked_exact7 = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    if working:
        raise ValueError("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if staged:
        raise ValueError("STAGED_CHANGE_PRESENT")

    tracked_set = set(tracked_exact7)
    untracked_set = set(ordinary_untracked)
    if not tracked_set and untracked_set == expected:
        head = _git(root, "rev-parse", "HEAD")
        origin = _git(root, "rev-parse", "origin/main")
        subject_line = _git(root, "log", "-1", "--format=%s")
        relation = _git(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
        if (
            head != [BASELINE_COMMIT]
            or origin != [BASELINE_COMMIT]
            or subject_line != [BASELINE_SUBJECT]
            or relation != ["0\t0"]
        ):
            raise ValueError("CANDIDATE_BASELINE_INVALID")
        profile = "CANDIDATE_UNTRACKED"
    elif tracked_set == expected and not untracked_set:
        ancestor = subprocess.run(
            ("git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"),
            cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if ancestor.returncode != 0:
            raise ValueError("TRACKED_CLEAN_BASELINE_NOT_ANCESTOR")
        profile = "TRACKED_CLEAN"
    else:
        raise ValueError("EXACT7_PLACEMENT_OR_UNRELATED_UNTRACKED_INVALID")
    return {"profile": profile, "records": records}


def independently_verify_delta_v1(
    root: Path, rows: Sequence[Mapping[str, str]]
) -> dict[str, object]:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_i12_v1(
        root
    )
    normalized = [dict(row) for row in rows]
    if (
        len(normalized) != 1000
        or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in normalized)
        or [int(row["scaleup_rank"]) for row in normalized]
        != list(range(1, 1001))
    ):
        raise ValueError("CENSUS_EXACT1000_SCHEMA_OR_ORDER_INVALID")
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in normalized}
    if set(before) != set(after):
        raise ValueError("CENSUS_EVENT_SET_CHANGED")
    target = set(subject.ONE_N0_EXACT4_EVENT_IDS_V1)
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    if changed != target:
        raise ValueError("DELTA_NOT_EXACT_ONE_N0_EXACT4")
    if any(before[event_id] != after[event_id] for event_id in set(before) - target):
        raise ValueError("NON_TARGET_ROW_CHANGED")

    expected = {
        "current_global_status": "COMPLETED_HUMAN_NEGATIVE",
        "priority_review_in_scope": "true",
        "review_unit_id": subject.ONE_N0_REVIEW_UNIT_ID_V1,
        "current_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "human_review_completed": "true",
        "human_review_authority_source": subject.ONE_N0_HUMAN_DECISION_SOURCE,
        "chemistry_disposition": "NOT_ESTABLISHED",
        "chemistry_authority_source": subject.ONE_N0_EVENT_MATRIX_SOURCE,
        "positive_authority_source": "",
        "task_relevance_disposition": "NOT_RELEVANT",
        "task_relevance_authority_source": subject.ONE_N0_EVENT_MATRIX_SOURCE,
        "training_use_disposition": "NOT_APPLICABLE",
        "human_training_excluded": "false",
        "reactive_pair_sample_authoritative": "false",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": "NOT_ESTABLISHED",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_split_authoritative": "false",
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    changed_sets: set[tuple[str, ...]] = set()
    for event_id in subject.ONE_N0_EXACT4_EVENT_IDS_V1:
        changed_fields = frozenset(
            field
            for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        )
        if changed_fields != EXPECTED_CHANGED_FIELDS:
            raise ValueError("TARGET_CHANGED_FIELDS_NOT_EXACT9:" + event_id)
        changed_sets.add(tuple(sorted(changed_fields)))
        if any(after[event_id][field] != value for field, value in expected.items()):
            raise ValueError("TARGET_SEMANTICS_INVALID:" + event_id)
        if any(
            before[event_id][field] != after[event_id][field]
            for field in subject.CENSUS_COLUMNS_V1
            if field not in EXPECTED_CHANGED_FIELDS
        ):
            raise ValueError("TARGET_NON_EXACT9_FIELD_CHANGED:" + event_id)
    if len(changed_sets) != 1:
        raise ValueError("TARGET_CHANGED_FIELD_SETS_DIFFER")

    for rank in (777, 779):
        event_id = next(
            row["canonical_event_id"]
            for row in frozen.rows
            if int(row["scaleup_rank"]) == rank
        )
        if before[event_id] != after[event_id]:
            raise ValueError("NEGATIVE_CONTROL_ROW_CHANGED:" + str(rank))
    return {
        "predecessor": frozen,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "changed_fields": sorted(EXPECTED_CHANGED_FIELDS),
        "rank777_changed": False,
        "rank779_changed": False,
    }


def independently_compute_top10_v1(
    root: Path,
) -> tuple[list[dict[str, object]], int]:
    result = reconciliation.reconcile_real_completed_human_decisions_with_1n0_v1(
        root
    )
    payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE")
    queue = list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
    status_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in result.reconciled_rows:
        status_by_unit[row["raw_review_unit_id"]].add(row["current_review_status"])
    candidates: list[tuple[int, int, str, dict[str, str], str]] = []
    for row in queue:
        statuses = status_by_unit.get(row["review_unit_id"])
        if statuses is None or len(statuses) != 1:
            raise ValueError("QUEUE_UNIT_STATUS_INVALID:" + row["review_unit_id"])
        status = next(iter(statuses))
        if status not in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            continue
        candidates.append(
            (
                -int(row["event_count"]),
                int(row["priority_rank"]),
                row["review_unit_id"],
                row,
                status,
            )
        )
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 112:
        raise ValueError("PENDING_UNIT_COUNT_NOT_112")
    if not any(
        unit == subject.ONE_N0_EXCLUDED_REVIEW_UNIT_ID_V1
        and status == "CURRENTLY_UNREVIEWED"
        and json.loads(row["ligand_component_ids_json"]) == ["1N0"]
        and int(row["event_count"]) == 2
        for _negative, _priority, unit, row, status in candidates
    ):
        raise ValueError("D60E_NEGATIVE_CONTROL_NOT_PENDING")
    top: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(
        candidates[:10], 1
    ):
        top.append(
            {
                "rank": rank,
                "raw_priority_rank": int(row["priority_rank"]),
                "review_unit_id": unit,
                "event_count": int(row["event_count"]),
                "pdb_ids": json.loads(row["pdb_ids_json"]),
                "ligand_component_ids": json.loads(row["ligand_component_ids_json"]),
                "full_coordinate_count": int(row["full_coordinate_event_count"]),
                "exact_pair_count": int(row["exact_reactive_pair_event_count"]),
                "ccd_complete_count": int(row["CCD_graph_complete_event_count"]),
                "post_source_evidence_count": int(
                    row["POST_geometry_available_event_count"]
                ),
                "current_review_status": status,
            }
        )
    return top, len(candidates)


def independently_verify_counts_v1(
    rows: Sequence[Mapping[str, str]],
    summary: Mapping[str, object],
    predecessor_summary: Mapping[str, object],
) -> None:
    normalized = [dict(row) for row in rows]
    if Counter(row["current_global_status"] for row in normalized) != EXPECTED_GLOBAL_COUNTS:
        raise ValueError("GLOBAL_STATUS_COUNTS_INVALID")
    if Counter(row["chemistry_disposition"] for row in normalized) != Counter(
        {"POSITIVE": 116, "NOT_ESTABLISHED": 90, "UNRESOLVED": 794}
    ):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in normalized) != Counter(
        {"RELEVANT": 117, "NOT_RELEVANT": 90, "UNRESOLVED": 793}
    ):
        raise ValueError("TASK_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in normalized) != Counter(
        {
            "INCLUDE": 48,
            "EXCLUDE_FROM_TRAINING_ONLY": 68,
            "NOT_APPLICABLE": 90,
            "UNRESOLVED": 794,
        }
    ):
        raise ValueError("TRAINING_COUNTS_INVALID")
    if summary.get("human_review") != EXPECTED_HUMAN_REVIEW:
        raise ValueError("HUMAN_REVIEW_COUNTS_INVALID")
    if summary.get("refresh_delta") != EXPECTED_REFRESH_DELTA:
        raise ValueError("REFRESH_DELTA_INVALID")
    for key in (
        "structural", "geometry", "reactive_pair", "role",
        "canonical_exact5", "training_stage",
    ):
        if summary.get(key) != predecessor_summary.get(key):
            raise ValueError("PREDECESSOR_AUTHORITY_COUNT_CHANGED:" + key)
    exact5 = summary["canonical_exact5"]
    if (
        exact5["task_count"] != 5
        or exact5["B3_present"] is not True
        or exact5["sixth_task_present"] is not False
        or [item["semantic_name"] for item in exact5["tasks"]]
        != [
            "warhead_only", "linker_plus_warhead",
            "scaffold_plus_warhead", "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ]
        or [
            item["structurally_applicable_authoritative_role_count"]
            for item in exact5["tasks"]
        ] != [116, 52, 52, 116, 116]
    ):
        raise ValueError("CANONICAL_EXACT5_INVALID")


def independently_verify_bindings_v1(
    bindings: Sequence[Mapping[str, object]],
    predecessor_bindings: Sequence[Mapping[str, object]],
) -> None:
    normalized = tuple(dict(item) for item in bindings)
    frozen = tuple(dict(item) for item in predecessor_bindings)
    if len(frozen) != 114 or normalized[:114] != frozen or len(normalized) != 120:
        raise ValueError("BINDING_LINEAGE_NOT_114_PLUS_6")
    expected_additive = tuple(
        {
            "artifact_role": role,
            "path": relative.as_posix(),
            "path_namespace": namespace,
            "byte_count": byte_count,
            "sha256": sha256,
            "expected_executable": expected_executable,
        }
        for role, relative, namespace, byte_count, sha256, expected_executable
        in subject._ADDITIVE_SOURCE_SPECS_V1
    )
    if normalized[114:] != expected_additive:
        raise ValueError("ADDITIVE_BINDINGS_NOT_EXACT6")
    identities = [
        (item["path_namespace"], item["path"]) for item in normalized
    ]
    if len(identities) != len(set(identities)):
        raise ValueError("SEMANTIC_IDENTITY_COLLISION")
    frozen_roles = {item["artifact_role"] for item in normalized[:114]}
    additive_roles = [item["artifact_role"] for item in normalized[114:]]
    if (
        len(additive_roles) != len(set(additive_roles))
        or frozen_roles & set(additive_roles)
    ):
        raise ValueError("SOURCE_ROLE_COLLISION")


def verify_manifest_v1(
    root: Path,
    manifest: Mapping[str, object],
    artifacts: Mapping[str, bytes],
    bindings: Sequence[Mapping[str, object]],
) -> None:
    _reject_dynamic_metadata(dict(manifest))
    if manifest.get("schema_version") != subject.SCHEMA_VERSION:
        raise ValueError("MANIFEST_SCHEMA_INVALID")
    if manifest.get("candidate_inventory") != {
        "exact_file_count": 7,
        "paths": list(subject.EXACT7_PATHS_V1),
    }:
        raise ValueError("MANIFEST_CANDIDATE_INVENTORY_INVALID")
    if manifest.get("output_inventory") != {
        "exact_output_count": 3,
        "paths": [
            (subject.OUTPUT_DIRECTORY_RELATIVE / subject.CENSUS_FILE).as_posix(),
            (subject.OUTPUT_DIRECTORY_RELATIVE / subject.SUMMARY_FILE).as_posix(),
            (subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE).as_posix(),
        ],
    }:
        raise ValueError("MANIFEST_OUTPUT_INVENTORY_INVALID")
    predecessor_binding = manifest.get("predecessor_manifest_validation_binding")
    if predecessor_binding != {
        "artifact_role": "PREDECESSOR_I12_MANIFEST_VALIDATION_IDENTITY",
        "path": subject.PREDECESSOR_MANIFEST_RELATIVE.as_posix(),
        "path_namespace": "repository_relative",
        "byte_count": 51041,
        "sha256": "d22c388f7da5fecede11df15e3bc188196328e24009ad9363932bebc971da150",
        "expected_executable": False,
    }:
        raise ValueError("PREDECESSOR_MANIFEST_BINDING_INVALID")
    if manifest.get("semantic_source_bindings") != list(bindings):
        raise ValueError("MANIFEST_SEMANTIC_BINDINGS_INVALID")
    if manifest.get("refresh_contract") != {
        "row_count": 1000,
        "column_count": 47,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "changed_field_count_per_one_n0_row": 9,
        "semantic_source_binding_count": 120,
        "predecessor_semantic_source_binding_count": 114,
        "additive_semantic_source_binding_count": 6,
        "semantic_identity_collision_count": 0,
        "source_role_collision_count": 0,
        "queue_refreshed": False,
        "training_started": False,
        "ready_for_training": False,
        "source_binding_v2_clean_from_birth": True,
        "new_numeric_POSIX_semantic_identity": False,
    }:
        raise ValueError("MANIFEST_REFRESH_CONTRACT_INVALID")
    self_binding = manifest.get("manifest_self_binding")
    if self_binding != {
        "path": (
            subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE
        ).as_posix(),
        "sha256_recorded_inside_self": False,
        "policy": "MANIFEST_SELF_SHA256_PROHIBITED",
    }:
        raise ValueError("MANIFEST_SELF_BINDING_INVALID")
    expected_digests = {
        "refreshed_census_sha256": _sha(artifacts[subject.CENSUS_FILE]),
        "refreshed_summary_sha256": _sha(artifacts[subject.SUMMARY_FILE]),
        "semantic_source_bindings_sha256": _sha(
            _canonical_json(list(bindings)).encode("utf-8")
        ),
        "authority_created": False,
    }
    if manifest.get("derived_projection_contract_digests") != expected_digests:
        raise ValueError("MANIFEST_DERIVED_DIGESTS_INVALID")
    candidate_bindings = manifest.get("candidate_contract_bindings")
    if type(candidate_bindings) is not list or len(candidate_bindings) != 4:
        raise ValueError("CANDIDATE_CONTRACT_BINDINGS_INVALID")
    for binding in candidate_bindings:
        relative = binding["path"]
        payload = _read(root / relative, "CANDIDATE_BINDING:" + relative)
        if binding != {
            "artifact_role": binding["artifact_role"],
            "path": relative,
            "byte_count": len(payload),
            "sha256": _sha(payload),
        }:
            raise ValueError("CANDIDATE_CONTRACT_BINDING_DRIFT:" + relative)


def verify_authority_boundary_v1(summary: Mapping[str, object]) -> None:
    boundary = summary.get("authority_boundary")
    if type(boundary) is not dict:
        raise ValueError("AUTHORITY_BOUNDARY_NOT_OBJECT")
    required_true = (
        "CURRENT_GLOBAL_RECONCILIATION_COMPLETE",
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE",
        "1N0_REVIEW_COMPLETED",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    )
    required_false = (
        "QUEUE_REFRESH", "next_review_started",
        "new_human_authority_created", "new_chemistry_authority_created",
        "new_pair_authority_created", "new_role_authority_created",
        "new_reusable_authority_created",
        "post_geometry_training_authority_created",
        "pre_geometry_authority_created", "training_admission_created",
        "training_materialization_allowed", "tensor_integration_performed",
        "model_forward_performed", "loss_executed", "backward_performed",
        "optimizer_created", "optimizer_step_performed",
        "parameter_update_authorization", "parameter_update_performed",
        "training_started", "READY_FOR_TRAINING",
        "feature_semantics_audit_performed",
        "new_exact_posix_source_mode_authority_introduced",
        "new_ambiguous_source_mode_authority_introduced",
    )
    if any(boundary.get(key) is not True for key in required_true):
        raise ValueError("AUTHORITY_REQUIRED_TRUE_MISSING")
    if any(boundary.get(key) is not False for key in required_false):
        raise ValueError("AUTHORITY_FORBIDDEN_ACTION_PRESENT")
    if (
        boundary.get("feature_semantics_status") != "AUDIT_REQUIRED_LATER"
        or boundary.get("Step12D")
        != "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
        or boundary.get("next_priority_review_unit")
        != "COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A"
        or boundary.get("next_priority_review_ligand") != "CER"
        or boundary.get("next_priority_review_current_pending_rank") != 1
        or boundary.get("next_priority_review_raw_priority_rank") != 19
    ):
        raise ValueError("AUTHORITY_BOUNDARY_VALUE_INVALID")


def verify_b4_core_v1(root: Path) -> dict[str, object]:
    result = b4_guard.verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
        repo_root=root
    )
    required = {
        "new_semantic_exact_posix_mode_occurrence_count": 0,
        "new_ambiguous_mode_occurrence_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "ready_for_training": False,
        "B4_PRODUCTION_SELF_SCAN_PASSED": True,
        "B4_CHECKER_SELF_SCAN_PASSED": True,
    }
    if any(result.get(key) != value for key, value in required.items()):
        raise ValueError("B4_CORE_INVALID")
    scanned = set(result.get("future_guard_scanned_python_paths", ()))
    required_paths = {
        subject.PRODUCTION_RELATIVE.as_posix(),
        subject.CHECKER_RELATIVE.as_posix(),
        subject.TEST_RELATIVE.as_posix(),
    }
    if not required_paths <= scanned:
        raise ValueError("B4_NEW_PYTHON_PATHS_NOT_SCANNED")
    return result


def _directory_payloads(path: Path) -> dict[str, bytes]:
    return {
        item.name: _read(item, "TEMP_OUTPUT:" + item.name)
        for item in sorted(path.iterdir())
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    inventory = verify_exact7_inventory_v1(root)
    first = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        root
    )
    second = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        root
    )
    if first != second:
        raise ValueError("TWO_IN_MEMORY_BUILDS_DIFFER")
    live = {
        name: _read(root / subject.OUTPUT_DIRECTORY_RELATIVE / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    if live != first:
        raise ValueError("MATERIALIZED_EXACT3_NOT_SOURCE_DERIVED")

    rows = _parse_census(live[subject.CENSUS_FILE])
    summary = _parse_json(live[subject.SUMMARY_FILE], "SUMMARY")
    manifest = _parse_json(live[subject.MANIFEST_FILE], "MANIFEST")
    for name, payload in live.items():
        _validate_text(payload, name)
    delta = independently_verify_delta_v1(root, rows)
    frozen = delta["predecessor"]
    independently_verify_counts_v1(rows, summary, frozen.summary)
    independently_verify_bindings_v1(
        manifest["semantic_source_bindings"], frozen.semantic_source_bindings
    )
    top, pending_count = independently_compute_top10_v1(root)
    if summary.get("top_pending_review_units_by_event_yield") != top:
        raise ValueError("DYNAMIC_PENDING_TOP10_INVALID")
    if not (
        top[0]["rank"] == 1
        and top[0]["raw_priority_rank"] == 19
        and top[0]["review_unit_id"]
        == "COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A"
        and top[0]["ligand_component_ids"] == ["CER"]
        and top[0]["event_count"] == 4
        and pending_count == 112
        and all(
            item["review_unit_id"] != subject.ONE_N0_REVIEW_UNIT_ID_V1
            for item in top
        )
    ):
        raise ValueError("NEXT_PRIORITY_NOT_CER")
    verify_manifest_v1(
        root, manifest, live, manifest["semantic_source_bindings"]
    )
    verify_authority_boundary_v1(summary)

    with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
        one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
            root, Path(left)
        )
        two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
            root, Path(right)
        )
        if (
            one != first
            or two != first
            or _directory_payloads(Path(left)) != first
            or _directory_payloads(Path(right)) != first
        ):
            raise ValueError("TWO_TEMP_MATERIALIZATIONS_DIFFER")

    b4 = verify_b4_core_v1(root)
    ordinary_untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    if any(path.lower().endswith(FORBIDDEN_SUFFIXES) for path in ordinary_untracked):
        raise ValueError("FORBIDDEN_ORDINARY_UNTRACKED_FILE")
    return {
        "status": "PASS",
        "repository_profile": inventory["profile"],
        "candidate_file_count": 7,
        "row_count": 1000,
        "column_count": 47,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "changed_field_count_per_target": 9,
        "rank777_changed": False,
        "rank779_changed": False,
        "predecessor_semantic_source_binding_count": 114,
        "additive_semantic_source_binding_count": 6,
        "semantic_source_binding_count": 120,
        "semantic_identity_collision_count": 0,
        "source_role_collision_count": 0,
        "pending_review_unit_count": 112,
        "next_priority_review_unit": top[0]["review_unit_id"],
        "queue_refreshed": False,
        "two_in_memory_builds_identical": True,
        "two_temp_materializations_identical": True,
        "materialized_exact3_source_derived": True,
        "b4": {
            "new_semantic_exact_posix_mode_occurrence_count": b4[
                "new_semantic_exact_posix_mode_occurrence_count"
            ],
            "new_ambiguous_mode_occurrence_count": b4[
                "new_ambiguous_mode_occurrence_count"
            ],
            "status": "PASS",
        },
        "training_started": False,
        "ready_for_training": False,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    if result["ready_for_training"] is not False:
        raise ValueError("READY_FOR_TRAINING_MUST_BE_FALSE")
    print("PASS")
    print(result["repository_profile"])
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
