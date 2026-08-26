#!/usr/bin/env python3
"""Repository-state-neutral checker for the cumulative1000 ONL refresh V1."""

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

from covalent_ext import covapie_cumulative1000_current_global_readiness_census_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_onl_v1 as subject  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_onl_v1 as reconciliation  # noqa: E402


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
MAX_FILE_BYTES = 1024 * 1024


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
    if len(rows) != 1000 or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows):
        raise ValueError("CENSUS_NOT_EXACT1000_SCHEMA")
    return rows


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if not output.is_dir():
        raise ValueError("OUTPUT_DIRECTORY_MISSING")
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
    for role, relative, namespace, byte_count, sha256 in subject._ADDITIVE_SOURCE_SPECS_V1:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != sha256:
            raise ValueError("FROZEN_BINDING_INVALID:" + role)
        verified.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
            }
        )
    return verified


def independently_verify_delta_v1(root: Path, rows: list[dict[str, str]]) -> dict[str, object]:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_v1(root)
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in rows}
    if tuple(int(row["scaleup_rank"]) for row in rows) != tuple(range(1, 1001)):
        raise ValueError("ROW_ORDER_OR_RANK_INVALID")
    if set(before) != set(after):
        raise ValueError("EVENT_SET_IDENTITY_INVALID")
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    onl = set(subject.ONL_EXACT9_EVENT_IDS_V1)
    if changed != onl or len(changed) != 9:
        raise ValueError("DELTA_NOT_EXACT_ONL9")
    if any(before[event_id] != after[event_id] for event_id in set(before) - onl):
        raise ValueError("NON_ONL_ROW_DRIFT")
    for event_id in onl:
        if any(
            before[event_id][field] != after[event_id][field]
            for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1
        ):
            raise ValueError("ONL_STRUCTURAL_DRIFT:" + event_id)
        row = after[event_id]
        if (
            row["current_review_status"] != "COMPLETED_HUMAN_POSITIVE"
            or row["chemistry_disposition"] != "POSITIVE"
            or row["task_relevance_disposition"] != "RELEVANT"
            or row["training_use_disposition"] != "EXCLUDE_FROM_TRAINING_ONLY"
            or row["reactive_pair_sample_authoritative"] != "true"
            or row["reactive_pair_training_target_available"] != "false"
            or row["role_partition_sample_authoritative"] != "true"
            or row["role_profile"] != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
            or row["structurally_applicable_task_ids_json"] != "[0,3,4]"
            or row["post_geometry_training_target_available"] != "false"
            or row["pre_geometry_authoritative"] != "false"
            or row["future_training_admission_candidate"] != "false"
            or row["formal_training_admitted"] != "false"
            or row["current_runtime_model_usable"] != "false"
        ):
            raise ValueError("ONL_SEMANTICS_INVALID:" + event_id)

    def selected(source_rows: object, field: str, value: str) -> set[str]:
        return {
            row["canonical_event_id"]
            for row in source_rows  # type: ignore[union-attr]
            if row[field] == value
        }

    set_checks = (
        selected(rows, "chemistry_disposition", "POSITIVE")
        == selected(frozen.rows, "chemistry_disposition", "POSITIVE") | onl,
        selected(rows, "chemistry_disposition", "UNRESOLVED")
        == selected(frozen.rows, "chemistry_disposition", "UNRESOLVED") - onl,
        selected(rows, "task_relevance_disposition", "RELEVANT")
        == selected(frozen.rows, "task_relevance_disposition", "RELEVANT") | onl,
        selected(rows, "task_relevance_disposition", "UNRESOLVED")
        == selected(frozen.rows, "task_relevance_disposition", "UNRESOLVED") - onl,
        selected(rows, "training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY")
        == selected(frozen.rows, "training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY") | onl,
        selected(rows, "training_use_disposition", "INCLUDE")
        == selected(frozen.rows, "training_use_disposition", "INCLUDE"),
    )
    if not all(set_checks):
        raise ValueError("EXACT_SET_ALGEBRA_INVALID")
    return {"changed_event_count": 9, "unchanged_event_count": 991}


def independently_verify_counts_v1(rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    if Counter(row["current_global_status"] for row in rows) != Counter(
        subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        raise ValueError("EXACT11_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 58, "NOT_ESTABLISHED": 86, "UNRESOLVED": 856}
    ):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 59, "NOT_RELEVANT": 86, "UNRESOLVED": 855}
    ):
        raise ValueError("TASK_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {"INCLUDE": 29, "EXCLUDE_FROM_TRAINING_ONLY": 29, "NOT_APPLICABLE": 86, "UNRESOLVED": 856}
    ):
        raise ValueError("TRAINING_COUNTS_INVALID")
    for field, expected in subject._EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            raise ValueError("BOOLEAN_COUNT_INVALID:" + field)
    role_counts = Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    if role_counts != Counter(
        {"STRICT_LINKER_PRESENT_V1": 31, "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 27}
    ):
        raise ValueError("ROLE_COUNTS_INVALID")
    expected_tasks = [58, 31, 31, 58, 58]
    tasks = summary["canonical_exact5"]["tasks"]  # type: ignore[index]
    if [item["structurally_applicable_authoritative_role_count"] for item in tasks] != expected_tasks:
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


def independently_compute_top10_v1(
    root: Path,
    reconciled_rows: tuple[dict[str, str], ...],
) -> list[dict[str, object]]:
    queue_path = root / subject.PRIORITY_QUEUE_RELATIVE
    payload = _read(queue_path, "PRIORITY_QUEUE")
    if (
        len(payload) != 50116
        or _sha(payload)
        != "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
    ):
        raise ValueError("PRIORITY_QUEUE_BINDING_INVALID")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    queue_rows = [dict(row) for row in reader]
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
    if len(candidates) != 123:
        raise ValueError("PENDING_QUEUE_NOT_EXACT123")
    result: list[dict[str, object]] = []
    for rank, (_neg_count, _priority, unit, row, status) in enumerate(
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


def verify_manifest_v1(root: Path, artifacts: dict[str, bytes]) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    if manifest["candidate_inventory"] != {
        "exact_file_count": 7,
        "paths": list(subject.EXACT7_PATHS_V1),
    }:
        raise ValueError("MANIFEST_EXACT7_INVALID")
    if manifest["semantic_source_bindings"] != list(
        subject.compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
            root
        ).semantic_source_bindings
    ):
        raise ValueError("MANIFEST_SEMANTIC_BINDINGS_INVALID")
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


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    exact7 = verify_exact7_inventory_v1(root)
    frozen = verify_frozen_bindings_v1(root)
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {
        filename: _read(output / filename, filename)
        for filename in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    for filename, payload in materialized.items():
        _validate_text(payload, filename)
    rows = _parse_census(materialized[subject.CENSUS_FILE])
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    delta = independently_verify_delta_v1(root, rows)
    independently_verify_counts_v1(rows, summary)

    fresh = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
        root
    )
    if not subject.validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
        fresh
    ):
        raise ValueError("PUBLIC_VALIDATOR_DID_NOT_PASS")
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
        root
    )
    if materialized != built:
        raise ValueError("MATERIALIZED_OUTPUTS_NOT_FRESH_BUILD")
    if _sha(materialized[subject.CENSUS_FILE]) != subject._EXPECTED_REFRESHED_CENSUS_SHA256_V1:
        raise ValueError("CENSUS_DERIVED_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != subject._EXPECTED_REFRESHED_SUMMARY_SHA256_V1:
        raise ValueError("SUMMARY_DERIVED_DIGEST_INVALID")
    binding_digest = _sha(
        subject._canonical_json(list(fresh.semantic_source_bindings)).encode("utf-8")
    )
    if binding_digest != subject._EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1:
        raise ValueError("SEMANTIC_BINDING_DERIVED_DIGEST_INVALID")
    reconcile = reconciliation.reconcile_real_completed_human_decisions_with_onl_v1(root)
    if reconcile.review_summary != {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 41,
        "completed_positive_unit_count": 4,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 65,
        "completed_total_unit_count": 8,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 273,
        "unreviewed_unit_count": 123,
    }:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    expected_top = independently_compute_top10_v1(root, reconcile.reconciled_rows)
    if summary["top_pending_review_units_by_event_yield"] != expected_top:
        raise ValueError("FULL_QUEUE_DYNAMIC_TOP10_INVALID")
    verify_manifest_v1(root, materialized)

    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
            root, Path(first)
        )
        two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
            root, Path(second)
        )
        if one != two or one != built:
            raise ValueError("TWO_DIRECTORY_DETERMINISM_INVALID")

    boundary = summary["authority_boundary"]
    false_non_actions = (
        "new_human_authority_created",
        "new_chemistry_authority_created",
        "new_role_authority_created",
        "new_pair_authority_created",
        "new_reusable_authority_created",
        "tensor_integration_performed",
        "loader_modified",
        "batch_modified",
        "model_forward_performed",
        "auxiliary_head_executed",
        "loss_executed",
        "backward_performed",
        "optimizer_created",
        "optimizer_step_performed",
        "parameter_update_performed",
        "training_performed",
        "fine_tune_performed",
        "training_admission_created",
        "training_dataset_changed",
        "feature_semantics_audit_performed",
    )
    if (
        boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is not True
        or boundary["READY_FOR_FORMAL_TRAINING"] is not False
        or boundary["HUMAN_REVIEW_DECISION_NOT_PERFORMED"] is not True
        or boundary["next_priority_review_unit"]
        != "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58"
        or any(boundary[key] is not False for key in false_non_actions)
    ):
        raise ValueError("AUTHORITY_BOUNDARY_INVALID")
    return {
        "candidate_file_count": len(exact7),
        "frozen_additive_binding_count": len(frozen),
        **delta,
        "refreshed_positive_count": 58,
        "pending_review_unit_count": 123,
        "next_priority_review_unit": boundary["next_priority_review_unit"],
        "ready_for_formal_training": False,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_ONL_V1_CHECK:PASS")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
