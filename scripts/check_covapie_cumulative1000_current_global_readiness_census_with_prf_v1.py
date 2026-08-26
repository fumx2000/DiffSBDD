#!/usr/bin/env python3
"""Repository-state-neutral checker for the cumulative1000 PRF refresh V1."""

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

from covalent_ext import covapie_completed_human_decision_reconciliation_with_prf_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_onl_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_prf_v1 as subject  # noqa: E402


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
MAX_FILE_BYTES = 1024 * 1024
EXPECTED_CENSUS_SHA256 = "a707cb60c8f788f9ad0e94e89c4038226cfa5f94c15b0afcfa6e36adca3c1b12"
EXPECTED_SUMMARY_SHA256 = "82d4d36beb21efb2a588beaea9d3b9c61a6275596482e39ff45341e4cbe316f7"
EXPECTED_BINDINGS_SHA256 = "e6f3a5ae1fdc566887daa65324c6a110b439524b91c3b913105206f951694344"

FROZEN_BINDINGS = (
    ("PREDECESSOR_ONL_CENSUS_OWNER", "src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_onl_v1.py", "repository_relative", 70095, "f74d2d486492a89c1aaeb523220e18558f80a8d50389e9deb076c86df7802f5b"),
    ("PREDECESSOR_ONL_MATERIALIZED_CENSUS", "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_onl_v1/covapie_cumulative1000_current_global_readiness_census_with_onl_v1.csv", "repository_relative", 502004, "57be12d7ed5d4e013dbd402ccf0ed49aa3d86067a952fdd339fcc945062894e4"),
    ("PREDECESSOR_ONL_MATERIALIZED_SUMMARY", "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_onl_v1/covapie_cumulative1000_current_global_readiness_summary_with_onl_v1.json", "repository_relative", 14489, "3271df9a94bf72f8ae081735e07e132c4a7d0dfb389f3acfdf31789420f2c19b"),
    ("PREDECESSOR_ONL_MATERIALIZED_MANIFEST", "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_onl_v1/covapie_cumulative1000_current_global_readiness_manifest_with_onl_v1.json", "repository_relative", 22870, "0e08c62d1ee3c42a0bcddc8c937ec56b2726d037649575b10287fe95978436c4"),
    ("PRF_RECONCILIATION_SUCCESSOR", "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_prf_v1.py", "repository_relative", 11728, "ce4db4fcbf909852a6fca1a919ee50750279a8a6ca0968d4b33ae8f510bd0f74"),
    ("PRF_INGESTION_OWNER", "src/covalent_ext/covapie_prf_completed_decision_ingestion_and_task_label_availability_v1.py", "repository_relative", 76082, "52ce8a00e6e02af7a0dcec9fdccdc69f19555a49557b1b9f73fdf4d20e230264"),
    ("PRF_EVENT_TASK_LABEL_AVAILABILITY", "data/derived/covalent_small/covapie_prf_completed_decision_ingestion_and_task_label_availability_v1/covapie_prf_event_task_label_availability_v1.csv", "repository_relative", 14303, "40df3625bda841ffe94ee12681da5593fece9598f44a971b00154c66322ff75b"),
    ("PRF_FORMAL_HUMAN_DECISION", "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/PRF_COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58/formal-human-decision-v1/prf_formal_human_decision_v1.json", "repository_parent_relative", 26699, "2b5b81290405761acaaacc5ba0764aeed23c93ea1eebe420f2c14528045c3ce3"),
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


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
    if not output.is_dir() or output.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if sorted(path.name for path in output.iterdir() if path.is_file()) != sorted((subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)):
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
        bindings.append({"path": relative, "byte_count": len(payload), "sha256": _sha(payload), "mode": "0644"})
    return bindings


def verify_frozen_bindings_v1(root: Path) -> list[dict[str, object]]:
    verified: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, sha256 in FROZEN_BINDINGS:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != sha256:
            raise ValueError("FROZEN_BINDING_INVALID:" + role)
        verified.append({"artifact_role": role, "path": relative, "path_namespace": namespace, "byte_count": byte_count, "sha256": sha256})
    return verified


def independently_verify_delta_v1(root: Path, rows: list[dict[str, str]]) -> dict[str, object]:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(root)
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in rows}
    if tuple(int(row["scaleup_rank"]) for row in rows) != tuple(range(1, 1001)):
        raise ValueError("ROW_ORDER_OR_RANK_INVALID")
    if set(before) != set(after):
        raise ValueError("EVENT_SET_IDENTITY_INVALID")
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    prf = set(subject.PRF_EXACT8_EVENT_IDS_V1)
    if changed != prf or len(changed) != 8:
        raise ValueError("DELTA_NOT_EXACT_PRF8")
    if any(before[event_id] != after[event_id] for event_id in set(before) - prf):
        raise ValueError("NON_PRF_ROW_DRIFT")
    if [int(after[event_id]["scaleup_rank"]) for event_id in subject.PRF_EXACT8_EVENT_IDS_V1] != list(subject.PRF_EXACT8_RANKS_V1):
        raise ValueError("PRF_RANK_DRIFT")
    for event_id in prf:
        if any(before[event_id][field] != after[event_id][field] for field in subject._STRUCTURAL_IDENTITY_FIELDS_V1):
            raise ValueError("PRF_STRUCTURAL_DRIFT:" + event_id)
        row = after[event_id]
        if (
            row["review_unit_id"] != subject.PRF_REVIEW_UNIT_ID_V1
            or row["current_global_status"] != "COMPLETED_HUMAN_POSITIVE"
            or row["current_review_status"] != "COMPLETED_HUMAN_POSITIVE"
            or row["human_review_completed"] != "true"
            or row["human_review_authority_source"] != subject.PRF_FORMAL_DECISION_SOURCE
            or row["chemistry_disposition"] != "POSITIVE"
            or row["chemistry_authority_source"] != subject.PRF_EVENT_MATRIX_SOURCE
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
            or row["formal_split_authoritative"] != "false"
            or row["formal_training_admitted"] != "false"
            or row["current_runtime_model_usable"] != "false"
        ):
            raise ValueError("PRF_SEMANTICS_INVALID:" + event_id)

    def selected(source_rows: object, field: str, value: str) -> set[str]:
        return {row["canonical_event_id"] for row in source_rows if row[field] == value}  # type: ignore[union-attr]

    checks = (
        selected(rows, "chemistry_disposition", "POSITIVE") == selected(frozen.rows, "chemistry_disposition", "POSITIVE") | prf,
        selected(rows, "chemistry_disposition", "UNRESOLVED") == selected(frozen.rows, "chemistry_disposition", "UNRESOLVED") - prf,
        selected(rows, "task_relevance_disposition", "RELEVANT") == selected(frozen.rows, "task_relevance_disposition", "RELEVANT") | prf,
        selected(rows, "task_relevance_disposition", "UNRESOLVED") == selected(frozen.rows, "task_relevance_disposition", "UNRESOLVED") - prf,
        selected(rows, "training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY") == selected(frozen.rows, "training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY") | prf,
        selected(rows, "training_use_disposition", "INCLUDE") == selected(frozen.rows, "training_use_disposition", "INCLUDE"),
        selected(rows, "chemistry_disposition", "NOT_ESTABLISHED") == selected(frozen.rows, "chemistry_disposition", "NOT_ESTABLISHED"),
        selected(rows, "task_relevance_disposition", "NOT_RELEVANT") == selected(frozen.rows, "task_relevance_disposition", "NOT_RELEVANT"),
        selected(rows, "training_use_disposition", "NOT_APPLICABLE") == selected(frozen.rows, "training_use_disposition", "NOT_APPLICABLE"),
    )
    if not all(checks):
        raise ValueError("EXACT_SET_ALGEBRA_INVALID")
    return {"changed_event_count": 8, "unchanged_event_count": 992}


def independently_verify_counts_v1(rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    if Counter(row["current_global_status"] for row in rows) != Counter(subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1):
        raise ValueError("EXACT11_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter({"POSITIVE": 66, "NOT_ESTABLISHED": 86, "UNRESOLVED": 848}):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter({"RELEVANT": 67, "NOT_RELEVANT": 86, "UNRESOLVED": 847}):
        raise ValueError("TASK_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter({"INCLUDE": 29, "EXCLUDE_FROM_TRAINING_ONLY": 37, "NOT_APPLICABLE": 86, "UNRESOLVED": 848}):
        raise ValueError("TRAINING_COUNTS_INVALID")
    for field, expected in subject._EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            raise ValueError("BOOLEAN_COUNT_INVALID:" + field)
    role_counts = Counter(row["role_profile"] for row in rows if row["role_partition_sample_authoritative"] == "true")
    if role_counts != Counter({"STRICT_LINKER_PRESENT_V1": 31, "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 35}):
        raise ValueError("ROLE_COUNTS_INVALID")
    tasks = summary["canonical_exact5"]["tasks"]  # type: ignore[index]
    if [item["structurally_applicable_authoritative_role_count"] for item in tasks] != [66, 31, 31, 66, 66]:
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
    expected_blockers = {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": 848},
        "pair_authority_absent": {"all_1000": 934, "within_positive_66": 0},
        "role_authority_absent": {"all_1000": 934, "within_positive_66": 0},
        "human_training_exclusion": {"within_positive_66": 37},
        "missing_split_authority": {"within_positive_66": 25, "within_include_29": 4},
        "missing_tensor_integration": {"within_positive_66": 25, "within_include_29": 0, "all_missing_are_training_excluded_population": True, "missing_source_composition": {"G3H": 8, "ONL": 9, "PRF": 8}},
        "missing_POST_training_authority": {"within_positive_66": 49, "within_include_29": 12},
        "missing_training_admission": {"within_positive_66": 61, "within_include_29": 24},
        "feature_semantics_pending": {"within_positive_66": 66},
    }
    if summary["blockers"] != expected_blockers:  # type: ignore[index]
        raise ValueError("BLOCKERS_INVALID")


def independently_compute_top10_v1(root: Path, reconciled_rows: tuple[dict[str, str], ...]) -> list[dict[str, object]]:
    payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE")
    if len(payload) != 50116 or _sha(payload) != "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2":
        raise ValueError("PRIORITY_QUEUE_BINDING_INVALID")
    queue_rows = [dict(row) for row in csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))]
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
        candidates.append((-int(row["event_count"]), int(row["priority_rank"]), unit, row, status))
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 122:
        raise ValueError("PENDING_QUEUE_NOT_EXACT122")
    result: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(candidates[:10], 1):
        result.append({
            "rank": rank,
            "review_unit_id": unit,
            "event_count": int(row["event_count"]),
            "pdb_ids": json.loads(row["pdb_ids_json"]),
            "ligand_component_ids": json.loads(row["ligand_component_ids_json"]),
            "full_coordinate_count": int(row["full_coordinate_event_count"]),
            "exact_pair_count": int(row["exact_reactive_pair_event_count"]),
            "ccd_complete_count": int(row["CCD_graph_complete_event_count"]),
            "post_source_evidence_count": int(row["POST_geometry_available_event_count"]),
            "current_review_status": status,
        })
    return result


def verify_semantic_bindings_v1(root: Path, observed: tuple[dict[str, object], ...]) -> None:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(root)
    by_identity = {(row["path_namespace"], row["path"]): dict(row) for row in frozen.semantic_source_bindings}
    for role, relative, namespace, byte_count, sha256 in FROZEN_BINDINGS:
        if role == "PREDECESSOR_ONL_MATERIALIZED_MANIFEST":
            continue
        row = {"artifact_role": role, "path": relative, "path_namespace": namespace, "byte_count": byte_count, "sha256": sha256}
        identity = (namespace, relative)
        prior = by_identity.get(identity)
        if prior is not None and prior != row:
            raise ValueError("SEMANTIC_BINDING_CONFLICT:" + relative)
        by_identity[identity] = row
    expected = tuple(sorted(by_identity.values(), key=lambda row: (row["path_namespace"], row["path"])))
    if observed != expected or len(observed) != 53:
        raise ValueError("SEMANTIC_BINDINGS_NOT_PREDECESSOR_PLUS_EXACT7")


def verify_manifest_v1(root: Path, artifacts: dict[str, bytes], fresh: object) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    if manifest["candidate_inventory"] != {"exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)}:
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
    candidate_paths = {binding["path"] for binding in manifest["candidate_contract_bindings"]}
    if candidate_paths != {subject.PRODUCTION_RELATIVE.as_posix(), subject.CHECKER_RELATIVE.as_posix(), subject.TEST_RELATIVE.as_posix(), subject.GUIDE_RELATIVE.as_posix()}:
        raise ValueError("MANIFEST_CANDIDATE_EXACT4_INVALID")
    manifest_text = artifacts[subject.MANIFEST_FILE].decode("utf-8").lower()
    if any(token in manifest_text for token in ('"hostname"', '"pid"', '"timestamp"', '"head"', '"commit_subject"', '"ahead"', '"behind"', '"lifecycle_profile"')):
        raise ValueError("MANIFEST_DYNAMIC_OR_GIT_METADATA")


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    exact7 = verify_exact7_inventory_v1(root)
    frozen = verify_frozen_bindings_v1(root)
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {name: _read(output / name, name) for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)}
    for name, payload in materialized.items():
        _validate_text(payload, name)
    rows = _parse_census(materialized[subject.CENSUS_FILE])
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    delta = independently_verify_delta_v1(root, rows)
    independently_verify_counts_v1(rows, summary)

    fresh = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_prf_v1(root)
    if not subject.validate_covapie_cumulative1000_current_global_readiness_census_with_prf_v1(fresh):
        raise ValueError("PUBLIC_VALIDATOR_DID_NOT_PASS")
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_prf_v1(root)
    if materialized != built:
        raise ValueError("MATERIALIZED_OUTPUTS_NOT_FRESH_BUILD")
    if _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256:
        raise ValueError("CENSUS_DERIVED_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256:
        raise ValueError("SUMMARY_DERIVED_DIGEST_INVALID")
    if _sha(_canonical_json(list(fresh.semantic_source_bindings)).encode("utf-8")) != EXPECTED_BINDINGS_SHA256:
        raise ValueError("SEMANTIC_BINDINGS_DERIVED_DIGEST_INVALID")
    verify_semantic_bindings_v1(root, fresh.semantic_source_bindings)

    reconciled = reconciliation.reconcile_real_completed_human_decisions_with_prf_v1(root)
    if reconciled.review_summary["completed_positive_event_count"] != 49 or reconciled.review_summary["completed_total_event_count"] != 73 or reconciled.review_summary["unreviewed_event_count"] != 265:
        raise ValueError("RECONCILIATION_COUNTS_INVALID")
    expected_top = independently_compute_top10_v1(root, reconciled.reconciled_rows)
    if summary["top_pending_review_units_by_event_yield"] != expected_top:
        raise ValueError("FULL_QUEUE_DYNAMIC_TOP10_INVALID")
    if expected_top[0]["review_unit_id"] != "COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22" or expected_top[0]["ligand_component_ids"] != ["2VS"]:
        raise ValueError("NEXT_PRIORITY_NOT_2VS")
    verify_manifest_v1(root, materialized, fresh)

    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_prf_v1(root, Path(first))
        two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_prf_v1(root, Path(second))
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
        or boundary["next_priority_review_unit"] != "COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22"
        or boundary["next_priority_review_ligand"] != "2VS"
        or boundary["next_priority_review_event_count"] != 8
        or any(boundary[key] is not False for key in false_non_actions)
    ):
        raise ValueError("AUTHORITY_BOUNDARY_INVALID")
    return {
        "candidate_file_count": len(exact7),
        "frozen_binding_count": len(frozen),
        "semantic_source_binding_count": len(fresh.semantic_source_bindings),
        **delta,
        "refreshed_positive_count": 66,
        "pending_review_unit_count": 122,
        "next_priority_review_unit": boundary["next_priority_review_unit"],
        "ready_for_formal_training": False,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_PRF_V1_CHECK:PASS")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
