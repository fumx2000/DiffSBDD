#!/usr/bin/env python3
"""Repository-state-neutral checker for the cumulative1000 YUN refresh V1."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_with_yun_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_yun_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_1f8_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_yun_v1 as subject  # noqa: E402


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
MAX_FILE_BYTES = 1024 * 1024
EXPECTED_CENSUS_SHA256 = "28eaa9833d69f191bf7eee91956588324ea1a3d145ebe5a99a31752a42e962e3"
EXPECTED_SUMMARY_SHA256 = "084d264f874547544a6b674cc1672298d2ac4eb08f61d139aa654f975d1c5767"
EXPECTED_BINDINGS_SHA256 = "07063135286c4756db628a79c9b668efa150ca89c68989b2ecb7b8d427ca94b2"
EXPECTED_YUN_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4LL0:A:CYS:797-:SG:C:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LL0:B:CYS:797-:SG:D:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:A:CYS:800-:SG:F:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:B:CYS:800-:SG:G:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:C:CYS:800-:SG:H:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:D:CYS:800-:SG:I:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:E:CYS:800-:SG:J:YUN:CAN",
)
EXPECTED_YUN_STRUCTURAL_CELLS = {
    "raw_structure_available": "true",
    "exact_cys_sg_event_recovered": "true",
    "explicit_covalent_evidence": "true",
    "distance_only_event_inference_used": "false",
    "full_coordinate_post_evidence_available": "true",
    "ccd_graph_complete": "true",
    "feature_compatible": "true",
    "structural_processing_success": "true",
    "post_geometry_source_evidence_available": "true",
    "representation_gap": "false",
    "feature_incompatible": "false",
    "reactive_pair_raw_structural_evidence": "true",
}
EXPECTED_BOOLEAN_COUNTS = {
    "raw_structure_available": 997,
    "exact_cys_sg_event_recovered": 867,
    "explicit_covalent_evidence": 867,
    "distance_only_event_inference_used": 0,
    "full_coordinate_post_evidence_available": 867,
    "ccd_graph_complete": 865,
    "feature_compatible": 865,
    "structural_processing_success": 865,
    "post_geometry_source_evidence_available": 867,
    "representation_gap": 78,
    "feature_incompatible": 2,
    "priority_review_in_scope": 338,
    "reactive_pair_raw_structural_evidence": 865,
    "reactive_pair_sample_authoritative": 89,
    "reactive_pair_training_target_available": 41,
    "role_partition_sample_authoritative": 89,
    "canonical_mask_structural_labels_available": 89,
    "post_geometry_sample_authoritative": 21,
    "post_geometry_training_target_available": 17,
    "pre_geometry_authoritative": 0,
    "pre_geometry_training_target_available": 0,
    "training_use_include": 36,
    "future_training_admission_candidate": 19,
    "formal_training_admitted": 5,
    "current_runtime_model_usable": 17,
}

FROZEN_BINDINGS = (
    (
        "PREDECESSOR_1F8_CENSUS_OWNER",
        "src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.py",
        "repository_relative", 55130,
        "cacb60cc5436b7744e7a545f275da44eb33a38825d04d91248ed91146f25f972",
    ),
    (
        "PREDECESSOR_1F8_MATERIALIZED_CENSUS",
        "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_1f8_v1/covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.csv",
        "repository_relative", 514588,
        "31d6add9d59d5eb9b40e8603eb9631230a75efa1f52590c3556827f62441175d",
    ),
    (
        "PREDECESSOR_1F8_MATERIALIZED_SUMMARY",
        "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_1f8_v1/covapie_cumulative1000_current_global_readiness_summary_with_1f8_v1.json",
        "repository_relative", 15062,
        "9a341222ff0932603f900042579b47f6969c50259bfd0d89d75dffe55bf3641f",
    ),
    (
        "PREDECESSOR_1F8_MATERIALIZED_MANIFEST",
        "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_1f8_v1/covapie_cumulative1000_current_global_readiness_manifest_with_1f8_v1.json",
        "repository_relative", 30872,
        "e9c159fa53550d3fd0a62e9cad0017255bae23a1952f8066e92ca4a56b0b7602",
    ),
    (
        "YUN_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_yun_v1.py",
        "repository_relative", 11824,
        "84c6c57666ec96dfdb1f39a9dd87d097efff2eb000e6bf10281f29471540c287",
    ),
    (
        "YUN_INGESTION_OWNER",
        "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
        "repository_relative", 82003,
        "8339aaa2c57fe1637ab4e4feb7db964fc76224957687d2e0752e28ba3b093928",
    ),
    (
        "YUN_EVENT_TASK_LABEL_AVAILABILITY",
        "data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_event_task_label_availability_v1.csv",
        "repository_relative", 13886,
        "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e",
    ),
    (
        "YUN_FORMAL_HUMAN_DECISION",
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/formal-human-decision-v1/yun_formal_human_decision_v1.json",
        "repository_parent_relative", 30722,
        "b4eeebe03354e820d9658225997c34b58b41c66f4dfe126230024306816e1140",
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
    if tuple(reader.fieldnames or ()) != subject.CENSUS_COLUMNS_V1:
        raise ValueError("CENSUS_HEADER_INVALID")
    rows = [dict(row) for row in reader]
    if len(rows) != 1000 or any(
        tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows
    ):
        raise ValueError("CENSUS_NOT_EXACT1000_SCHEMA")
    return rows


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if not output.is_dir() or output.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if sorted(path.name for path in output.iterdir() if path.is_file()) != sorted(
        (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    ):
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")
    bindings: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, "EXACT7:" + relative)
        _validate_text(payload, relative)
        if stat.S_IMODE(path.stat().st_mode) != 0o644:
            raise ValueError("EXACT7_MODE_NOT_0644:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT7_FORBIDDEN_SUFFIX:" + relative)
        if len(payload) > MAX_FILE_BYTES:
            raise ValueError("EXACT7_FILE_EXCEEDS_1_MIB:" + relative)
        bindings.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "mode": "0644",
            }
        )
    return bindings


def verify_frozen_bindings_v1(root: Path) -> list[dict[str, object]]:
    verified: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, sha256 in FROZEN_BINDINGS:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != sha256:
            raise ValueError("FROZEN_BINDING_INVALID:" + role)
        verified.append(
            {
                "artifact_role": role,
                "path": relative,
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
            }
        )
    matrix_path = root / ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX
    if ingestion.build_artifacts_v1(root)[ingestion.MATRIX] != _read(
        matrix_path, "YUN_SOURCE_DERIVED_MATRIX"
    ):
        raise ValueError("YUN_MATRIX_NOT_SOURCE_DERIVED_FROM_FROZEN_FORMAL_DECISION")
    return verified


def independently_verify_delta_v1(
    root: Path, rows: list[dict[str, str]]
) -> dict[str, object]:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(
        root
    )
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in rows}
    if tuple(int(row["scaleup_rank"]) for row in rows) != tuple(range(1, 1001)):
        raise ValueError("ROW_ORDER_OR_RANK_INVALID")
    if set(before) != set(after):
        raise ValueError("EVENT_SET_IDENTITY_INVALID")
    yun = set(EXPECTED_YUN_EVENT_IDS)
    if (
        len(yun) != 7
        or not yun <= set(before)
        or [int(before[event_id]["scaleup_rank"]) for event_id in EXPECTED_YUN_EVENT_IDS]
        != [783, 784, 786, 787, 788, 789, 790]
    ):
        raise ValueError("PREDECESSOR_YUN_IDENTITY_INVALID")
    expected_prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "priority_review_in_scope": "true",
        "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "human_training_excluded": "false",
        "reactive_pair_raw_structural_evidence": "true",
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
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    if any(
        any(before[event_id][field] != value for field, value in expected_prior.items())
        for event_id in yun
    ):
        raise ValueError("PREDECESSOR_YUN_STATE_INVALID")
    changed = {
        event_id for event_id in before if before[event_id] != after[event_id]
    }
    if changed != yun or len(changed) != 7:
        raise ValueError("DELTA_NOT_EXACT_YUN_EXACT7")
    if any(before[event_id] != after[event_id] for event_id in set(before) - yun):
        raise ValueError("NON_YUN_ROW_DRIFT")
    if [int(after[event_id]["scaleup_rank"]) for event_id in EXPECTED_YUN_EVENT_IDS] != [
        783, 784, 786, 787, 788, 789, 790,
    ]:
        raise ValueError("YUN_RANK_DRIFT")
    for event_id in yun:
        changed_fields = {
            field
            for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        if changed_fields != subject._AUTHORIZED_YUN_OVERLAY_FIELDS_V1:
            raise ValueError("YUN_CHANGED_FIELD_SET_INVALID:" + event_id)
        if any(
            before[event_id][field] != after[event_id][field]
            for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
        ):
            raise ValueError("YUN_STRUCTURAL_DRIFT:" + event_id)
        row = after[event_id]
        if (
            row["review_unit_id"] != subject.YUN_REVIEW_UNIT_ID_V1
            or row["current_global_status"] != "COMPLETED_HUMAN_POSITIVE"
            or row["current_review_status"] != "COMPLETED_HUMAN_POSITIVE"
            or row["human_review_completed"] != "true"
            or row["human_review_authority_source"] != subject.YUN_FORMAL_DECISION_SOURCE
            or row["chemistry_disposition"] != "POSITIVE"
            or row["chemistry_authority_source"] != subject.YUN_EVENT_MATRIX_SOURCE
            or row["task_relevance_disposition"] != "RELEVANT"
            or row["training_use_disposition"] != "INCLUDE"
            or row["human_training_excluded"] != "false"
            or row["training_use_include"] != "true"
            or row["future_training_admission_candidate"] != "true"
            or row["reactive_pair_sample_authoritative"] != "true"
            or row["reactive_pair_training_target_available"] != "false"
            or row["role_partition_sample_authoritative"] != "true"
            or row["role_profile"] != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
            or row["structurally_applicable_task_ids_json"] != "[0,3,4]"
            or row["post_geometry_training_target_available"] != "false"
            or row["pre_geometry_authoritative"] != "false"
            or row["formal_split_authoritative"] != "false"
            or row["formal_split"] != ""
            or row["formal_training_admitted"] != "false"
            or row["current_runtime_model_usable"] != "false"
            or row["training_materialization_allowed_current_source"] != "false"
        ):
            raise ValueError("YUN_SEMANTICS_INVALID:" + event_id)
        if any(
            row[field] != value
            for field, value in EXPECTED_YUN_STRUCTURAL_CELLS.items()
        ):
            raise ValueError("YUN_STRUCTURAL_COVERAGE_INVALID:" + event_id)

    def selected(source_rows: object, field: str, value: str) -> set[str]:
        return {
            row["canonical_event_id"]
            for row in source_rows  # type: ignore[union-attr]
            if row[field] == value
        }

    checks = (
        selected(rows, "chemistry_disposition", "POSITIVE")
        == selected(frozen.rows, "chemistry_disposition", "POSITIVE") | yun,
        selected(rows, "chemistry_disposition", "UNRESOLVED")
        == selected(frozen.rows, "chemistry_disposition", "UNRESOLVED") - yun,
        selected(rows, "task_relevance_disposition", "RELEVANT")
        == selected(frozen.rows, "task_relevance_disposition", "RELEVANT") | yun,
        selected(rows, "task_relevance_disposition", "UNRESOLVED")
        == selected(frozen.rows, "task_relevance_disposition", "UNRESOLVED") - yun,
        selected(rows, "training_use_disposition", "INCLUDE")
        == selected(frozen.rows, "training_use_disposition", "INCLUDE") | yun,
        selected(rows, "training_use_disposition", "UNRESOLVED")
        == selected(frozen.rows, "training_use_disposition", "UNRESOLVED") - yun,
        selected(rows, "future_training_admission_candidate", "true")
        == selected(frozen.rows, "future_training_admission_candidate", "true") | yun,
        selected(rows, "training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY")
        == selected(frozen.rows, "training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY"),
        selected(rows, "chemistry_disposition", "NEGATIVE")
        == selected(frozen.rows, "chemistry_disposition", "NEGATIVE"),
        selected(rows, "chemistry_disposition", "NOT_ESTABLISHED")
        == selected(frozen.rows, "chemistry_disposition", "NOT_ESTABLISHED"),
        selected(rows, "task_relevance_disposition", "NOT_RELEVANT")
        == selected(frozen.rows, "task_relevance_disposition", "NOT_RELEVANT"),
        selected(rows, "training_use_disposition", "NOT_APPLICABLE")
        == selected(frozen.rows, "training_use_disposition", "NOT_APPLICABLE"),
        selected(rows, "formal_training_admitted", "true")
        == selected(frozen.rows, "formal_training_admitted", "true"),
        selected(rows, "current_runtime_model_usable", "true")
        == selected(frozen.rows, "current_runtime_model_usable", "true"),
    )
    if not all(checks):
        raise ValueError("EXACT_SET_ALGEBRA_INVALID")
    return {
        "changed_event_count": 7,
        "unchanged_event_count": 993,
        "changed_fields": sorted(subject._AUTHORIZED_YUN_OVERLAY_FIELDS_V1),
    }


def independently_verify_counts_v1(
    rows: list[dict[str, str]], summary: dict[str, object]
) -> None:
    if Counter(row["current_global_status"] for row in rows) != Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        raise ValueError("EXACT11_INVALID")
    if summary["global_status_distribution"]["counts"] != {  # type: ignore[index]
        "CURRENTLY_UNREVIEWED": 242,
        "CURRENTLY_IN_PROGRESS": 0,
        "COMPLETED_HUMAN_POSITIVE": 72,
        "COMPLETED_HUMAN_NEGATIVE": 54,
        "COMPLETED_PARTIAL_AUTHORITY": 1,
        "CURRENT_RUNTIME_MODEL_USABLE": 17,
        "PUBLISHED_EXACT_AUTO_NEGATIVE": 32,
        "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
        "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
        "QUARANTINE_REPRESENTATION_GAP": 78,
        "REJECTED_FEATURE_INCOMPATIBLE": 2,
    }:
        raise ValueError("SUMMARY_EXACT11_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 89, "NOT_ESTABLISHED": 86, "UNRESOLVED": 825}
    ):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 90, "NOT_RELEVANT": 86, "UNRESOLVED": 824}
    ):
        raise ValueError("TASK_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {
            "INCLUDE": 36, "EXCLUDE_FROM_TRAINING_ONLY": 53,
            "NOT_APPLICABLE": 86, "UNRESOLVED": 825,
        }
    ):
        raise ValueError("TRAINING_COUNTS_INVALID")
    for field, expected in EXPECTED_BOOLEAN_COUNTS.items():
        if sum(row[field] == "true" for row in rows) != expected:
            raise ValueError("BOOLEAN_COUNT_INVALID:" + field)
    if summary["structural"] != {  # type: ignore[index]
        "raw_structure_available_count": 997,
        "exact_cys_sg_event_recovered_count": 867,
        "explicit_covalent_evidence_count": 867,
        "distance_only_event_inference_used_count": 0,
        "full_coordinate_post_evidence_available_count": 867,
        "ccd_graph_complete_count": 865,
        "feature_compatible_count": 865,
        "structural_processing_success_count": 865,
        "post_geometry_source_evidence_available_count": 867,
        "representation_gap_count": 78,
        "feature_incompatible_count": 2,
    }:
        raise ValueError("STRUCTURAL_SUMMARY_INVALID")
    role_counts = Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    if role_counts != Counter(
        {"STRICT_LINKER_PRESENT_V1": 39, "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 50}
    ):
        raise ValueError("ROLE_COUNTS_INVALID")
    if summary["chemistry"]["positive_source_composition"] != {  # type: ignore[index]
        "CURRENT_RUNTIME": 17, "FFQ": 8, "POA": 16, "G3H": 8,
        "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8, "YUN": 7,
    } or summary["chemistry"]["positive_authority_collision_count"] != 0:  # type: ignore[index]
        raise ValueError("POSITIVE_SOURCE_COMPOSITION_INVALID")
    if summary["reactive_pair"] != {  # type: ignore[index]
        "raw_structural_pair_evidence_count": 865,
        "sample_level_authoritative_pair_count": 89,
        "published_model_bound_target_constructible_count": 41,
        "current_runtime_bound_target_count": 17,
        "g3h_sample_authority_contribution_count": 8,
        "g3h_training_target_contribution_count": 0,
        "onl_sample_authority_contribution_count": 9,
        "onl_model_bound_target_contribution_count": 0,
        "prf_sample_authority_contribution_count": 8,
        "prf_model_bound_target_contribution_count": 0,
        "two_vs_sample_authority_contribution_count": 8,
        "two_vs_model_bound_target_contribution_count": 0,
        "one_f8_sample_authority_contribution_count": 8,
        "one_f8_model_bound_target_contribution_count": 0,
        "yun_sample_authority_contribution_count": 7,
        "yun_model_bound_target_contribution_count": 0,
        "positive_without_sample_pair_authority_count": 0,
    }:
        raise ValueError("REACTIVE_PAIR_COUNTS_INVALID")
    if summary["role"] != {  # type: ignore[index]
        "role_partition_sample_authoritative_count": 89,
        "role_profile_counts": {
            "STRICT_LINKER_PRESENT_V1": 39,
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 50,
            "other": 0,
        },
        "canonical_mask_structural_labels_available_count": 89,
        "all_five_structurally_applicable_count": 39,
        "direct_profile_A_B3_C_count": 50,
        "unknown_role_row_count": 911,
        "unknown_role_rows_are_not_false_applicability": True,
    }:
        raise ValueError("ROLE_SUMMARY_INVALID")
    exact5 = summary["canonical_exact5"]  # type: ignore[assignment]
    if (
        exact5["task_count"] != 5
        or [task["semantic_name"] for task in exact5["tasks"]]
        != [
            "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
            "scaffold_only", "scaffold_plus_linker_plus_warhead",
        ]
        or [task["structurally_applicable_authoritative_role_count"] for task in exact5["tasks"]]
        != [89, 39, 39, 89, 89]
        or exact5["B3_present"] is not True
        or exact5["sixth_task_present"] is not False
    ):
        raise ValueError("EXACT5_COUNTS_INVALID")
    if summary["geometry"] != {  # type: ignore[index]
        "POST_source_evidence_available_count": 867,
        "POST_sample_authoritative_count": 21,
        "POST_training_target_available_count": 17,
        "PRE_source_evidence_available_count": 0,
        "PRE_sample_authoritative_count": 0,
        "PRE_training_target_available_count": 0,
        "PRE_is_v1_hard_requirement": False,
        "POST_to_PRE_promotion_performed": False,
        "PRE_zero_fill_performed": False,
    }:
        raise ValueError("GEOMETRY_COUNTS_INVALID")
    if summary["training_stage"] != {  # type: ignore[index]
        "training_use_include_count": 36,
        "future_training_admission_candidate_count": 19,
        "future_candidate_source_composition": {
            "FFQ": 4, "POA": 8, "G3H": 0, "ONL": 0, "PRF": 0,
            "2VS": 0, "1F8": 0, "YUN": 7,
        },
        "current_runtime_model_usable_count": 17,
        "formal_training_admitted_count": 5,
        "ready_for_formal_training_event_count": 0,
        "training_materialization_allowed_global_status": "NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
        "feature_semantics_audit_completed": False,
        "step12d_status": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }:
        raise ValueError("TRAINING_STAGE_INVALID")
    if summary["human_review"] != {  # type: ignore[index]
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 96,
        "completed_unit_count": 12,
        "completed_positive_event_count": 72,
        "completed_positive_unit_count": 8,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "unreviewed_event_count": 242,
        "unreviewed_unit_count": 119,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 242,
        "current_pending_review_unit_count": 119,
    }:
        raise ValueError("HUMAN_REVIEW_SUMMARY_INVALID")
    expected_blockers = {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": 825},
        "pair_authority_absent": {"all_1000": 911, "within_positive_89": 0},
        "role_authority_absent": {"all_1000": 911, "within_positive_89": 0},
        "human_training_exclusion": {"within_positive_89": 53},
        "missing_split_authority": {
            "within_positive_89": 48, "within_include_36": 11,
        },
        "missing_tensor_integration": {
            "within_positive_89": 48, "within_include_36": 7,
            "all_missing_are_training_excluded_population": False,
            "missing_source_composition": {
                "G3H": 8, "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8,
                "YUN": 7,
            },
        },
        "missing_POST_training_authority": {
            "within_positive_89": 72, "within_include_36": 19,
        },
        "missing_training_admission": {
            "within_positive_89": 84, "within_include_36": 31,
        },
        "feature_semantics_pending": {"within_positive_89": 89},
    }
    if summary["blockers"] != expected_blockers:
        raise ValueError("BLOCKERS_INVALID")


def independently_compute_top10_v1(
    root: Path, reconciled_rows: tuple[dict[str, str], ...]
) -> list[dict[str, object]]:
    payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE")
    if len(payload) != 50116 or _sha(payload) != (
        "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
    ):
        raise ValueError("PRIORITY_QUEUE_BINDING_INVALID")
    queue_rows = [
        dict(row)
        for row in csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    ]
    if len(queue_rows) != 131:
        raise ValueError("PRIORITY_QUEUE_NOT_EXACT131")
    status_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in reconciled_rows:
        status_by_unit[row["raw_review_unit_id"]].add(row["current_review_status"])
    candidates: list[tuple[int, int, str, dict[str, str], str]] = []
    for row in queue_rows:
        unit = row["review_unit_id"]
        statuses = status_by_unit.get(unit)
        if statuses is None or len(statuses) != 1:
            raise ValueError("QUEUE_UNIT_STATUS_INVALID:" + unit)
        status = next(iter(statuses))
        if status not in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            continue
        candidates.append(
            (-int(row["event_count"]), int(row["priority_rank"]), unit, row, status)
        )
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 119:
        raise ValueError("PENDING_QUEUE_NOT_EXACT119")
    result: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(
        candidates[:10], 1
    ):
        result.append(
            {
                "rank": rank,
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
    return result


def verify_semantic_bindings_v1(
    root: Path, observed: tuple[dict[str, object], ...]
) -> None:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_1f8_v1(
        root
    )
    if len(frozen.semantic_source_bindings) != 67:
        raise ValueError("PREDECESSOR_SEMANTIC_BINDING_COUNT_NOT_67")
    if _sha(_canonical_json(list(frozen.semantic_source_bindings)).encode()) != (
        "41c0579eeab164ae884cc3ba8afd358b54d97fe16ed324b0c84497940bfa72c5"
    ):
        raise ValueError("PREDECESSOR_SEMANTIC_BINDING_DIGEST_INVALID")
    by_identity = {
        (row["path_namespace"], row["path"]): dict(row)
        for row in frozen.semantic_source_bindings
    }
    for role, relative, namespace, byte_count, sha256 in FROZEN_BINDINGS:
        if role == "PREDECESSOR_1F8_MATERIALIZED_MANIFEST":
            continue
        row = {
            "artifact_role": role,
            "path": relative,
            "path_namespace": namespace,
            "byte_count": byte_count,
            "sha256": sha256,
        }
        identity = (namespace, relative)
        prior = by_identity.get(identity)
        if prior is not None and prior != row:
            raise ValueError("SEMANTIC_BINDING_CONFLICT:" + relative)
        by_identity[identity] = row
    expected = tuple(
        sorted(by_identity.values(), key=lambda row: (row["path_namespace"], row["path"]))
    )
    if observed != expected or len(observed) != 74:
        raise ValueError("SEMANTIC_BINDINGS_NOT_PREDECESSOR_PLUS_EXACT7_REFRESH_INPUTS")


def verify_manifest_v1(
    root: Path, artifacts: dict[str, bytes], fresh: object
) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    if manifest["candidate_inventory"] != {
        "exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1),
    }:
        raise ValueError("MANIFEST_EXACT7_INVALID")
    if manifest["semantic_source_bindings"] != list(fresh.semantic_source_bindings):
        raise ValueError("MANIFEST_SEMANTIC_BINDINGS_INVALID")
    if manifest["derived_projection_contract_digests"] != {
        "refreshed_census_sha256": EXPECTED_CENSUS_SHA256,
        "refreshed_summary_sha256": EXPECTED_SUMMARY_SHA256,
        "semantic_source_bindings_sha256": EXPECTED_BINDINGS_SHA256,
        "authority_created": False,
    }:
        raise ValueError("MANIFEST_DERIVED_DIGESTS_INVALID")
    if manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is not False:
        raise ValueError("MANIFEST_SELF_SHA_RECORDED")
    candidate_paths = {
        binding["path"] for binding in manifest["candidate_contract_bindings"]
    }
    if candidate_paths != {
        subject.PRODUCTION_RELATIVE.as_posix(),
        subject.CHECKER_RELATIVE.as_posix(),
        subject.TEST_RELATIVE.as_posix(),
        subject.GUIDE_RELATIVE.as_posix(),
    }:
        raise ValueError("MANIFEST_CANDIDATE_EXACT4_INVALID")
    manifest_text = artifacts[subject.MANIFEST_FILE].decode("utf-8").lower()
    if any(
        token in manifest_text
        for token in (
            '"hostname"', '"pid"', '"timestamp"', '"head"',
            '"commit_subject"', '"ahead"', '"behind"', '"lifecycle_profile"',
        )
    ):
        raise ValueError("MANIFEST_DYNAMIC_OR_GIT_METADATA")


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    exact7 = verify_exact7_inventory_v1(root)
    frozen = verify_frozen_bindings_v1(root)
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {
        name: _read(output / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    for name, payload in materialized.items():
        _validate_text(payload, name)
    rows = _parse_census(materialized[subject.CENSUS_FILE])
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    delta = independently_verify_delta_v1(root, rows)
    independently_verify_counts_v1(rows, summary)

    fresh = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
        root
    )
    if not subject.validate_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
        fresh
    ):
        raise ValueError("PUBLIC_VALIDATOR_DID_NOT_PASS")
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1(
        root
    )
    if materialized != built:
        raise ValueError("MATERIALIZED_OUTPUTS_NOT_FRESH_BUILD")
    if _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256:
        raise ValueError("CENSUS_DERIVED_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256:
        raise ValueError("SUMMARY_DERIVED_DIGEST_INVALID")
    if _sha(_canonical_json(list(fresh.semantic_source_bindings)).encode()) != (
        EXPECTED_BINDINGS_SHA256
    ):
        raise ValueError("SEMANTIC_BINDINGS_DERIVED_DIGEST_INVALID")
    verify_semantic_bindings_v1(root, fresh.semantic_source_bindings)

    reconciled = reconciliation.reconcile_real_completed_human_decisions_with_yun_v1(
        root
    )
    if (
        reconciled.review_summary["completed_positive_event_count"] != 72
        or reconciled.review_summary["completed_total_event_count"] != 96
        or reconciled.review_summary["unreviewed_event_count"] != 242
        or reconciled.review_summary["unreviewed_unit_count"] != 119
    ):
        raise ValueError("RECONCILIATION_COUNTS_INVALID")
    expected_top = independently_compute_top10_v1(root, reconciled.reconciled_rows)
    if summary["top_pending_review_units_by_event_yield"] != expected_top:
        raise ValueError("FULL_QUEUE_DYNAMIC_TOP10_INVALID")
    if not (
        expected_top[0]["review_unit_id"]
        == "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62"
        and expected_top[0]["ligand_component_ids"] == ["NEQ"]
        and expected_top[0]["pdb_ids"] == ["3V61", "3V62"]
        and expected_top[0]["event_count"] == 6
    ):
        raise ValueError("NEXT_PRIORITY_NOT_NEQ_EXACT6")
    verify_manifest_v1(root, materialized, fresh)

    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1(
            root, Path(first)
        )
        two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_yun_v1(
            root, Path(second)
        )
        if one != two or one != built:
            raise ValueError("TWO_DIRECTORY_DETERMINISM_INVALID")

    boundary = summary["authority_boundary"]
    false_non_actions = (
        "new_human_authority_created", "new_chemistry_authority_created",
        "new_role_authority_created", "new_pair_authority_created",
        "new_reusable_authority_created", "tensor_integration_performed",
        "loader_modified", "batch_modified", "model_forward_performed",
        "auxiliary_head_executed", "loss_executed", "backward_performed",
        "optimizer_created", "optimizer_step_performed", "parameter_update_performed",
        "training_performed", "fine_tune_performed", "training_admission_created",
        "training_dataset_changed", "feature_semantics_audit_performed",
    )
    if (
        boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is not True
        or boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is not True
        or boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is not True
        or boundary["READY_FOR_FORMAL_TRAINING"] is not False
        or boundary["HUMAN_REVIEW_DECISION_NOT_PERFORMED"] is not True
        or boundary["NEXT_RECOMMENDED_MAINLINE"] != "HIGH_YIELD_HUMAN_REVIEW_EXPANSION"
        or boundary["next_priority_review_unit"]
        != "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62"
        or boundary["next_priority_review_ligand"] != "NEQ"
        or boundary["next_priority_review_event_count"] != 6
        or any(boundary[key] is not False for key in false_non_actions)
    ):
        raise ValueError("AUTHORITY_BOUNDARY_INVALID")
    return {
        "candidate_file_count": len(exact7),
        "frozen_binding_count": len(frozen),
        "semantic_source_binding_count": len(fresh.semantic_source_bindings),
        **delta,
        "refreshed_positive_count": 89,
        "training_include_count": 36,
        "future_candidate_count": 19,
        "pending_review_unit_count": 119,
        "next_priority_review_unit": boundary["next_priority_review_unit"],
        "ready_for_formal_training": False,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_YUN_V1_CHECK:PASS")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
