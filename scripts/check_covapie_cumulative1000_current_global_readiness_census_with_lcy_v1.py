#!/usr/bin/env python3
"""Independent fail-closed checker for the cumulative1000 with-LCY census V1."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_with_lcy_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_lcy_v1 as subject  # noqa: E402
from covalent_ext import covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


BASELINE_COMMIT = "23ee42e55207b8fc6e35ea92f0648f2504274cbe"
EXPECTED_CENSUS_SHA256 = "a393fc8e2419d354f73863b389a64a12874ec500282b61986bfefe51f10b12ce"
EXPECTED_SUMMARY_SHA256 = "edd88fce900fd8f77f1b1647b39b6a2adb54e184361c0edc5d1111d5346e7ada"
EXPECTED_BINDINGS_SHA256 = "1382e6a7bb4b3a01496c17afba6ccb27bff843ff814911c17c04b8119bf57f14"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part", ".log",
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )


def _event_set_sha(values: set[str]) -> str:
    return _sha(_canonical_json(sorted(values)).encode("utf-8"))


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


def _parse_csv(payload: bytes, expected_header: Sequence[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    rows = [dict(row) for row in reader]
    if tuple(reader.fieldnames or ()) != tuple(expected_header):
        raise ValueError("CSV_HEADER_INVALID")
    return rows


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, relative)
        _validate_text(payload, relative)
        if len(payload) > 1024 * 1024:
            raise ValueError("CANDIDATE_FILE_EXCEEDS_1_MIB:" + relative)
        records.append(
            {"path": relative, "byte_count": len(payload), "sha256": _sha(payload)}
        )
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if {entry.name for entry in output.iterdir()} != {
        subject.CENSUS_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }:
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")
    return records


def verify_frozen_bindings_v1(root: Path) -> None:
    for role, relative, namespace, size, digest, executable in subject._ADDITIVE_SOURCE_SPECS_V1:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        mode_executable = bool(path.stat().st_mode & 0o111)
        if len(payload) != size or _sha(payload) != digest or mode_executable != executable:
            raise ValueError("FROZEN_BINDING_INVALID:" + role)
    payload = _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    if len(payload) != 67869 or _sha(payload) != (
        "fc7110a4e2d013b03ce83e1829820c857938cf123826ccc8f09af7cc8b387391"
    ):
        raise ValueError("PREDECESSOR_MANIFEST_BINDING_INVALID")


def independently_verify_matrix_v1(root: Path) -> list[dict[str, str]]:
    payload = _read(root / subject.LCY_EVENT_MATRIX_RELATIVE, "LCY_MATRIX")
    rows = _parse_csv(payload, ingestion.MATRIX_HEADER)
    if (
        len(rows) != 4
        or tuple(row["canonical_event_id"] for row in rows) != ingestion.EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in rows) != ingestion.EXPECTED_RANKS
    ):
        raise ValueError("LCY_MATRIX_IDENTITY_INVALID")
    expected = {
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "LCY",
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "human_review_completed": "true",
        "task_relevance": "NOT_RELEVANT",
        "task_relevance_human_authoritative": "true",
        "chemistry": "POSITIVE",
        "chemistry_human_authoritative": "true",
        "negative_chemistry": "false",
        "positive_generative_supervision_eligible": "false",
        "reactive_pair_human_authoritative": "true",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C1",
        "role_partition_human_authoritative": "false",
        "selected_candidate_index_0based": "null",
        "role_profile": "NOT_ESTABLISHED",
        "warhead_atoms_json": "null",
        "linker_atoms_json": "null",
        "scaffold_atoms_json": "null",
        "W_L_S_counts_json": "null",
        "boundary_bonds_json": "null",
        "task_applicability_determined": "false",
        "formal_event_training_use_decision": "NOT_APPLICABLE",
        "human_training_excluded": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "training_materialization_allowed": "false",
        "READY_FOR_TRAINING": "false",
        "supporting_PRE_source_graph_count_per_event": "1",
        "PRE_mapping_count_per_event": "0",
        "PRE_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_status": "PRE_REACTION_UNRESOLVED",
        "POST_source_evidence_available": "true",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
    }
    for row in rows:
        if any(row[key] != value for key, value in expected.items()):
            raise ValueError("LCY_MATRIX_SEMANTICS_INVALID:" + row["canonical_event_id"])
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            [item["semantic_long_name"] for item in applicability]
            != [
                "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
                "scaffold_only", "scaffold_plus_linker_plus_warhead",
            ]
            or [item["display_alias"] for item in applicability]
            != ["A", "B", "B2", "B3", "C"]
            or any(item["structurally_applicable"] is not None for item in applicability)
        ):
            raise ValueError("LCY_MATRIX_EXACT5_INVALID")
    return rows


def independently_verify_delta_v1(
    root: Path, rows: Sequence[dict[str, str]], matrix: Sequence[dict[str, str]]
) -> dict[str, object]:
    before_rows = _parse_csv(
        _read(root / subject.PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS"),
        subject.CENSUS_COLUMNS_V1,
    )
    before = {row["canonical_event_id"]: row for row in before_rows}
    after = {row["canonical_event_id"]: row for row in rows}
    exact4 = set(ingestion.EXPECTED_EVENT_IDS)
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    if set(before) != set(after) or changed != exact4:
        raise ValueError("DELTA_NOT_EXACT_LCY_EXACT4")
    matrix_by_event = {row["canonical_event_id"]: row for row in matrix}
    expected_after = {
        "current_global_status": "COMPLETED_HUMAN_NEGATIVE",
        "current_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "human_review_completed": "true",
        "human_review_authority_source": subject.LCY_HUMAN_DECISION_SOURCE,
        "chemistry_disposition": "POSITIVE",
        "chemistry_authority_source": subject.LCY_EVENT_MATRIX_SOURCE,
        "positive_authority_source": subject.LCY_EVENT_MATRIX_SOURCE,
        "task_relevance_disposition": "NOT_RELEVANT",
        "task_relevance_authority_source": subject.LCY_EVENT_MATRIX_SOURCE,
        "training_use_disposition": "NOT_APPLICABLE",
        "human_training_excluded": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "training_materialization_allowed_current_source": "false",
        "reactive_pair_sample_authoritative": "true",
        "role_partition_sample_authoritative": "false",
        "role_profile": "NOT_ESTABLISHED",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
    }
    for event_id in exact4:
        fields = {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        unchanged_authorized = {
            field for field in subject._AUTHORIZED_LCY_OVERLAY_FIELDS_V1
            if before[event_id][field] == after[event_id][field]
        }
        if fields != subject._ACTUAL_CHANGED_LCY_FIELDS_V1:
            raise ValueError("LCY_CHANGED_FIELDS_NOT_EXACT12:" + event_id)
        if unchanged_authorized != subject._AUTHORIZED_BUT_UNCHANGED_LCY_FIELDS_V1:
            raise ValueError("LCY_AUTHORIZED_UNCHANGED_NOT_EXACT3:" + event_id)
        if fields & subject._FORBIDDEN_LCY_CHANGED_FIELDS_V1:
            raise ValueError("LCY_FORBIDDEN_FIELD_CHANGED:" + event_id)
        if any(after[event_id][key] != value for key, value in expected_after.items()):
            raise ValueError("LCY_FINAL_SEMANTICS_INVALID:" + event_id)
        if matrix_by_event[event_id]["chemistry_human_authoritative"] != "true":
            raise ValueError("LCY_POSITIVE_AUTHORITY_MISSING")
    gve_exact4 = set(subject.GVE_EXACT4_EVENT_IDS_V1)
    control = subject.LCY_SAME_COMPONENT_CONTROL_EVENT_ID_V1
    if any(before[event_id] != after[event_id] for event_id in gve_exact4):
        raise ValueError("GVE_EXACT4_CHANGED")
    if control in exact4 or before[control] != after[control]:
        raise ValueError("LCY_3A2G_SAME_COMPONENT_CONTROL_CHANGED")
    return {
        "changed_event_count": len(changed),
        "unchanged_event_count": len(rows) - len(changed),
        "authorized_overlay_field_count": len(subject._AUTHORIZED_LCY_OVERLAY_FIELDS_V1),
        "authorized_but_unchanged_field_count": len(subject._AUTHORIZED_BUT_UNCHANGED_LCY_FIELDS_V1),
        "actual_changed_field_count": len(subject._ACTUAL_CHANGED_LCY_FIELDS_V1),
    }


def _reject_stale_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "within_positive_132" or (
                key.startswith("within_positive_") and key.removeprefix("within_positive_").isdigit()
            ) or (
                key.startswith("within_include_") and key.removeprefix("within_include_").isdigit()
            ):
                raise ValueError("STALE_COUNT_CODED_SUMMARY_KEY:" + key)
            _reject_stale_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_stale_keys(item)


def independently_verify_counts_v1(
    rows: Sequence[dict[str, str]], summary: Mapping[str, object]
) -> None:
    if len(rows) != 1000 or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows):
        raise ValueError("CENSUS_NOT_1000_BY_47")
    if [int(row["scaleup_rank"]) for row in rows] != list(range(1, 1001)):
        raise ValueError("RANK_CONTINUITY_INVALID")
    if Counter(row["current_global_status"] for row in rows) != Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        raise ValueError("GLOBAL_STATUS_COUNTS_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 140, "NOT_ESTABLISHED": 90, "UNRESOLVED": 770}
    ):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 133, "NOT_RELEVANT": 98, "UNRESOLVED": 769}
    ):
        raise ValueError("TASK_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {"INCLUDE": 60, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 98, "UNRESOLVED": 770}
    ):
        raise ValueError("TRAINING_COUNTS_INVALID")
    legacy = {
        row["canonical_event_id"] for row in rows
        if row["task_relevance_disposition"] == "NOT_RELEVANT"
        and row["chemistry_disposition"] == "NOT_ESTABLISHED"
        and row["training_use_disposition"] == "NOT_APPLICABLE"
    }
    orthogonal = {
        row["canonical_event_id"] for row in rows
        if row["task_relevance_disposition"] == "NOT_RELEVANT"
        and row["chemistry_disposition"] == "POSITIVE"
        and row["training_use_disposition"] == "NOT_APPLICABLE"
    }
    if (
        len(legacy) != 90
        or orthogonal
        != set(subject.GVE_EXACT4_EVENT_IDS_V1) | set(ingestion.EXPECTED_EVENT_IDS)
        or len(orthogonal) != 8
    ):
        raise ValueError("TASK_NEGATIVE_POPULATIONS_INVALID")
    if any(
        row["task_relevance_disposition"] == "NOT_RELEVANT"
        and row["canonical_event_id"] not in legacy | orthogonal
        for row in rows
    ):
        raise ValueError("ARBITRARY_TASK_NEGATIVE_RELAXATION")
    boolean_counts = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "reactive_pair_sample_authoritative", "role_partition_sample_authoritative",
            "canonical_mask_structural_labels_available", "human_training_excluded",
            "training_use_include", "future_training_admission_candidate",
            "formal_training_admitted", "current_runtime_model_usable",
        )
    }
    if boolean_counts != {
        "reactive_pair_sample_authoritative": 140,
        "role_partition_sample_authoritative": 132,
        "canonical_mask_structural_labels_available": 132,
        "human_training_excluded": 72,
        "training_use_include": 60,
        "future_training_admission_candidate": 43,
        "formal_training_admitted": 5,
        "current_runtime_model_usable": 17,
    }:
        raise ValueError("AUTHORITY_COUNTS_INVALID")
    profiles = Counter(
        row["role_profile"] for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    applicability: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    if profiles != Counter({"DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 80, "STRICT_LINKER_PRESENT_V1": 52}):
        raise ValueError("ROLE_COUNTS_INVALID")
    if applicability != Counter({0: 132, 1: 52, 2: 52, 3: 132, 4: 132}):
        raise ValueError("EXACT5_COUNTS_INVALID")
    geometry = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "post_geometry_source_evidence_available", "post_geometry_sample_authoritative",
            "post_geometry_training_target_available", "pre_geometry_authoritative",
            "pre_geometry_training_target_available",
        )
    }
    if tuple(geometry.values()) != (867, 21, 17, 0, 0):
        raise ValueError("GEOMETRY_COUNTS_INVALID")
    _reject_stale_keys(summary)
    blockers = summary["blockers"]
    if (
        blockers["population_sizes"] != {
            "chemistry_positive_population_count": 140,
            "training_include_population_count": 60,
        }
        or blockers["chemistry_unresolved"] != {"all_1000": 770}
        or blockers["pair_authority_absent"] != {"all_1000": 860, "within_chemistry_positive": 0}
        or blockers["role_authority_absent"] != {"all_1000": 868, "within_chemistry_positive": 8}
        or blockers["human_training_exclusion"] != {"within_chemistry_positive": 72}
        or blockers["missing_split_authority"] != {
            "within_chemistry_positive": 99, "within_training_include": 35,
        }
        or blockers["missing_tensor_integration"]["within_chemistry_positive"] != 99
        or blockers["missing_tensor_integration"]["within_training_include"] != 31
        or blockers["missing_tensor_integration"]["missing_source_composition"].get("LCY") != 4
        or blockers["missing_tensor_integration"]["all_missing_are_training_excluded_population"] is not False
        or blockers["missing_POST_training_authority"] != {
            "within_chemistry_positive": 123, "within_training_include": 43,
        }
        or blockers["missing_training_admission"] != {
            "within_chemistry_positive": 135, "within_training_include": 55,
        }
        or blockers["feature_semantics_pending"] != {"within_chemistry_positive": 140}
    ):
        raise ValueError("SUMMARY_BLOCKERS_INVALID")
    if (
        summary["chemistry"]["positive_source_composition"].get("LCY") != 4
        or summary["chemistry"]["positive_source_composition"].get("GVE") != 4
    ):
        raise ValueError("LCY_POSITIVE_SOURCE_COMPOSITION_INVALID")
    if "LCY" in summary["training_stage"]["future_candidate_source_composition"]:
        raise ValueError("LCY_FUTURE_CANDIDATE_SOURCE_LEAK")
    human = summary["human_review"]
    if human != {
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 151,
        "completed_unit_count": 25,
        "completed_positive_event_count": 115,
        "completed_positive_unit_count": 18,
        "completed_negative_event_count": 36,
        "completed_negative_unit_count": 7,
        "unreviewed_event_count": 187,
        "unreviewed_unit_count": 106,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 187,
        "current_pending_review_unit_count": 106,
    }:
        raise ValueError("HUMAN_REVIEW_SUMMARY_INVALID")


def independently_compute_top10_v1(
    root: Path, reconciled_rows: Sequence[dict[str, str]]
) -> list[dict[str, object]]:
    queue = _parse_csv(
        _read(root / subject.PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE"),
        (
            "priority_rank", "review_unit_id", "event_count",
            "potential_event_yield_per_unit", "canonical_event_ids_json",
            "pdb_ids_json", "ligand_component_ids_json", "full_coordinate_event_count",
            "exact_reactive_pair_event_count", "CCD_graph_complete_event_count",
            "POST_geometry_available_event_count",
            "shadow_exact_component_event_count", "representation_blocked_event_count",
            "leakage_conflict_event_count", "priority_score", "priority_reason",
            "human_decision_created",
        ),
    )
    status_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in reconciled_rows:
        status_by_unit[row["raw_review_unit_id"]].add(row["current_review_status"])
    candidates = []
    for row in queue:
        status = next(iter(status_by_unit[row["review_unit_id"]]))
        if status not in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            continue
        candidates.append((-int(row["event_count"]), int(row["priority_rank"]), row["review_unit_id"], row, status))
    candidates.sort(key=lambda item: item[:3])
    top = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(candidates[:10], 1):
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
                "post_source_evidence_count": int(row["POST_geometry_available_event_count"]),
                "current_review_status": status,
            }
        )
    if len(candidates) != 106 or top[0] != {
        "rank": 1,
        "raw_priority_rank": 25,
        "review_unit_id": subject.NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "event_count": 4,
        "pdb_ids": ["4V37"],
        "ligand_component_ids": ["0D8"],
        "full_coordinate_count": 4,
        "exact_pair_count": 4,
        "ccd_complete_count": 4,
        "post_source_evidence_count": 4,
        "current_review_status": "CURRENTLY_UNREVIEWED",
    }:
        raise ValueError("DYNAMIC_NEXT_PENDING_INVALID")
    return top


def verify_manifest_v1(
    root: Path, manifest: Mapping[str, object], computation: object,
    materialized: Mapping[str, bytes]
) -> None:
    _reject_stale_keys(manifest)
    if (
        manifest["candidate_inventory"] != {"exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)}
        or manifest["semantic_source_bindings"] != list(computation.semantic_source_bindings)
        or manifest["semantic_source_binding_count"] != 156
        or manifest["manifest_self_SHA256_recorded"] is not False
        or manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is not False
        or "sha256" in manifest["manifest_self_binding"]
    ):
        raise ValueError("MANIFEST_CONTRACT_INVALID")
    identities = [
        (binding["path_namespace"], binding["path"])
        for binding in manifest["semantic_source_bindings"]
    ]
    if len(set(identities)) != 156:
        raise ValueError("SEMANTIC_BINDING_DUPLICATE")
    digest = _sha(_canonical_json(manifest["semantic_source_bindings"]).encode("utf-8"))
    if digest != EXPECTED_BINDINGS_SHA256:
        raise ValueError("SEMANTIC_BINDING_DIGEST_INVALID")
    contract = manifest["refresh_contract"]
    if (
        contract["authorized_overlay_field_count"] != 15
        or contract["authorized_but_unchanged_field_count"] != 3
        or contract["actual_changed_field_count_per_lcy_row"] != 12
        or contract["predecessor_semantic_source_binding_count"] != 150
        or contract["additive_semantic_source_binding_count"] != 6
        or contract["semantic_source_binding_count"] != 156
        or contract["gve_orthogonal_population_count"] != 4
        or contract["lcy_orthogonal_population_count"] != 4
        or contract["task_negative_chemistry_positive_population_count"] != 8
        or contract["task_negative_chemistry_positive_population_exactly_gve_plus_lcy_exact8"] is not True
        or contract["global_task_negative_chemistry_positive_relaxation_allowed"] is not False
        or contract["queue_refreshed"] is not False
        or contract["training_started"] is not False
    ):
        raise ValueError("MANIFEST_REFRESH_CONTRACT_INVALID")
    source_bindings = manifest["candidate_contract_bindings"]
    for binding in source_bindings:
        payload = _read(root / binding["path"], binding["artifact_role"])
        if len(payload) != binding["byte_count"] or _sha(payload) != binding["sha256"]:
            raise ValueError("CANDIDATE_CONTRACT_BINDING_INVALID")
    outputs = {item["path"]: item for item in manifest["output_bindings_excluding_manifest_self"]}
    for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE):
        path = (subject.OUTPUT_DIRECTORY_RELATIVE / name).as_posix()
        if outputs[path]["sha256"] != _sha(materialized[name]):
            raise ValueError("OUTPUT_BINDING_INVALID:" + name)


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ("git", *args), cwd=root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _classify_exact7_artifact_placement_v1(
    tracked: Sequence[str], untracked: Sequence[str]
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    if not tracked and set(untracked) == expected and len(untracked) == 7:
        return "CANDIDATE_UNTRACKED"
    if set(tracked) == expected and len(tracked) == 7 and not untracked:
        return "TRACKED_CLEAN"
    raise ValueError("EXACT7_ARTIFACT_PLACEMENT_INVALID")


def _classify_repository_lifecycle_v1(
    *, placement: str, head: str, origin: str, ahead: int, behind: int,
    baseline_is_ancestor_of_head: bool, baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool, baseline_to_head_changed_paths: Sequence[str],
) -> str:
    changed = set(baseline_to_head_changed_paths)
    expected = set(subject.EXACT7_PATHS_V1)
    if placement == "CANDIDATE_UNTRACKED":
        if not (
            head == origin == BASELINE_COMMIT and ahead == behind == 0
            and baseline_is_ancestor_of_head and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head and not changed
        ):
            raise ValueError("CANDIDATE_UNTRACKED_LIFECYCLE_INVALID")
        return placement
    if placement != "TRACKED_CLEAN" or (
        head == BASELINE_COMMIT or behind != 0 or ahead < 0
        or not baseline_is_ancestor_of_head or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head or not expected <= changed
        or ((ahead == 0) != (origin == head))
    ):
        raise ValueError("TRACKED_CLEAN_LIFECYCLE_INVALID")
    return placement


def check_lifecycle_simulations_v1() -> dict[str, bool]:
    expected = set(subject.EXACT7_PATHS_V1)
    candidate = dict(
        placement="CANDIDATE_UNTRACKED", head=BASELINE_COMMIT, origin=BASELINE_COMMIT,
        ahead=0, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=(),
    )
    tracked = dict(
        placement="TRACKED_CLEAN", head="later-head", origin="middle-origin",
        ahead=2, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=tuple(expected | {"docs/later.md"}),
    )
    _classify_repository_lifecycle_v1(**candidate)
    _classify_repository_lifecycle_v1(**tracked)
    _classify_repository_lifecycle_v1(**{**tracked, "origin": "later-head", "ahead": 0})
    for updates in (
        {"behind": 1}, {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False}, {"origin_is_ancestor_of_head": False},
        {"baseline_to_head_changed_paths": tuple(expected - {next(iter(expected))})},
    ):
        try:
            _classify_repository_lifecycle_v1(**{**tracked, **updates})
        except ValueError:
            continue
        raise ValueError("LIFECYCLE_FAIL_CLOSED_SIMULATION_ACCEPTED")
    return {
        "candidate_untracked": True, "tracked_clean": True,
        "multiple_later_commits": True, "origin_between_baseline_and_head": True,
    }


def _is_ancestor(root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer), cwd=root,
        check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise ValueError("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def verify_git_safety_v1(root: Path) -> dict[str, object]:
    working = _git(root, "diff", "--name-only")
    staged = _git(root, "diff", "--cached", "--name-only")
    if working or staged:
        raise ValueError("TRACKED_OR_STAGED_CHANGE_PRESENT")
    tracked = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    placement = _classify_exact7_artifact_placement_v1(tracked, untracked)
    head = _git(root, "rev-parse", "HEAD")[0]
    origin = _git(root, "rev-parse", "origin/main")[0]
    behind_text, ahead_text = _git(
        root, "rev-list", "--left-right", "--count", "origin/main...HEAD"
    )[0].split()
    committed = [] if placement == "CANDIDATE_UNTRACKED" else _git(
        root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD"
    )
    lifecycle = _classify_repository_lifecycle_v1(
        placement=placement, head=head, origin=origin,
        ahead=int(ahead_text), behind=int(behind_text),
        baseline_is_ancestor_of_head=_is_ancestor(root, BASELINE_COMMIT, "HEAD"),
        baseline_is_ancestor_of_origin=_is_ancestor(root, BASELINE_COMMIT, "origin/main"),
        origin_is_ancestor_of_head=_is_ancestor(root, "origin/main", "HEAD"),
        baseline_to_head_changed_paths=committed,
    )
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in untracked):
        raise ValueError("UNTRACKED_FORBIDDEN_SUFFIX")
    transients = []
    for directory, names, files in os.walk(root):
        relative = Path(directory).relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            names[:] = []
            continue
        if any(name in {"__pycache__", ".pytest_cache"} for name in names):
            transients.append(relative)
        if any(name.endswith((".pyc", ".tmp", ".part", ".log")) for name in files):
            transients.append(relative)
    if transients:
        raise ValueError("CACHE_OR_TRANSIENT_FILE_PRESENT")
    return {
        "placement": placement, "lifecycle": lifecycle,
        "tracked_modification_count": 0, "staged_count": 0,
        "ordinary_untracked_count": len(untracked), "head": head,
        "origin_main": origin, "ahead": int(ahead_text), "behind": int(behind_text),
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    inventory = verify_exact7_inventory_v1(root)
    verify_frozen_bindings_v1(root)
    matrix = independently_verify_matrix_v1(root)
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {
        name: _read(output / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    rows = _parse_csv(materialized[subject.CENSUS_FILE], subject.CENSUS_COLUMNS_V1)
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    manifest = json.loads(materialized[subject.MANIFEST_FILE])
    delta = independently_verify_delta_v1(root, rows, matrix)
    independently_verify_counts_v1(rows, summary)

    computation = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_lcy_v1(root)
    built = subject._build_artifacts_from_computation_v1(root, computation)
    rebuilt = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_lcy_v1(root)
    if materialized != built or built != rebuilt:
        raise ValueError("MATERIALIZED_FRESH_OR_DETERMINISTIC_BUILD_MISMATCH")
    if (
        _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256
        or _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256
        or _sha(_canonical_json(list(computation.semantic_source_bindings)).encode("utf-8"))
        != EXPECTED_BINDINGS_SHA256
    ):
        raise ValueError("DERIVED_PROJECTION_DIGEST_INVALID")
    verify_manifest_v1(root, manifest, computation, materialized)

    reconciled = reconciliation.reconcile_real_completed_human_decisions_with_lcy_v1(root)
    if (
        len(reconciled.source_bindings) != 21
        or len(reconciled.normalized_facts) != 127
        or len({binding.stable_identity for binding in reconciled.source_bindings}) != 21
        or reconciled.review_summary["completed_total_event_count"] != 151
        or reconciled.review_summary["completed_total_unit_count"] != 25
    ):
        raise ValueError("LCY_RECONCILIATION_COUNTS_INVALID")
    top = independently_compute_top10_v1(root, reconciled.reconciled_rows)
    if summary["top_pending_review_units_by_event_yield"] != top:
        raise ValueError("TOP_PENDING_SUMMARY_INVALID")
    boundary = summary["authority_boundary"]
    for key in (
        "LCY_REVIEW_COMPLETED", "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION",
        "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_PREPARATION",
        "CURRENT_GLOBAL_RECONCILIATION_COMPLETE", "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE",
        "CENSUS_REFRESH", "READY_FOR_EXTERNAL_REVIEW", "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
        "derived_refresh_not_new_authority",
    ):
        if boundary[key] is not True:
            raise ValueError("AUTHORITY_BOUNDARY_TRUE_INVALID:" + key)
    for key in (
        "NEXT_REVIEW_STARTED", "QUEUE_REFRESH", "TRAINING_STARTED", "READY_FOR_TRAINING",
        "new_human_authority_created", "new_scientific_authority_created",
        "new_chemistry_authority_created", "new_pair_authority_created",
        "new_role_authority_created", "new_reusable_authority_created",
        "formal_decision_read_directly", "formal_validator_executed",
    ):
        if boundary[key] is not False:
            raise ValueError("AUTHORITY_BOUNDARY_FALSE_INVALID:" + key)
    lifecycle = check_lifecycle_simulations_v1()
    safety = verify_git_safety_v1(root)
    return {
        "candidate_file_count": len(inventory),
        "semantic_source_binding_count": 156,
        **delta,
        "two_full_builds_byte_identical": True,
        "next_pending": top[0],
        "lifecycle_simulations": lifecycle,
        **safety,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    print("WITH_LCY_CENSUS_CANDIDATE_PASS=true")
    print("WITH_LCY_CENSUS_SCHEMA47_PRESERVED=true")
    print("LCY_EXACT4_OVERLAY_PASS=true")
    print("NON_LCY_ROWS_UNCHANGED_996_OF_996=true")
    print("AUTHORIZED_LCY_OVERLAY_EXACT15=true")
    print("AUTHORIZED_BUT_UNCHANGED_LCY_FIELDS_EXACT3=true")
    print("ACTUAL_LCY_CHANGED_FIELDS_EXACT12=true")
    print("LCY_TASK_NOT_RELEVANT=true")
    print("LCY_CHEMISTRY_POSITIVE=true")
    print("LCY_TRAINING_NOT_APPLICABLE=true")
    print("LCY_HUMAN_TRAINING_EXCLUDED=false")
    print("LEGACY_TASK_NEGATIVE_NOT_ESTABLISHED_POPULATION_90=true")
    print("LCY_TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_4=true")
    print("GVE_TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_4=true")
    print("TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_8=true")
    print("TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_EXACTLY_GVE_PLUS_LCY_EXACT8=true")
    print("GLOBAL_TASK_NEGATIVE_RELAXATION_ALLOWED=false")
    print("LCY_PAIR_AUTHORITY_COUNT_140=true")
    print("LCY_ROLE_AUTHORITY_COUNT_132=true")
    print("LCY_MASK_AUTHORITY_COUNT_132=true")
    print("EXACT5_B3_PRESENT=true")
    print("SIXTH_TASK=false")
    print("SUMMARY_POPULATION_CODED_STALE_KEYS_ABSENT=true")
    print("POST_COUNTS_UNCHANGED=true")
    print("PRE_COUNTS_UNCHANGED=true")
    print("SEMANTIC_SOURCE_BINDINGS_156=true")
    print("SEMANTIC_SOURCE_BINDING_COLLISIONS_0=true")
    print("GVE_EXACT4_UNCHANGED=true")
    print("LCY_3A2G_UNCHANGED=true")
    print("CURRENT_PENDING_REVIEW_UNIT_COUNT_106=true")
    print("NEXT_PENDING_0D8_RAW25=true")
    print("READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_PREPARATION=true")
    print("NEXT_REVIEW_STARTED=false")
    print("QUEUE_REFRESH=false")
    print("TRAINING_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    print("READY_FOR_EXTERNAL_REVIEW=true")
    print("COMMIT=false")
    print("PUSH=false")
    print(_canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
