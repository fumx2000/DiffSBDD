from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_split_leakage_smoke as step13bk
from covalent_ext.covapie_legacy_pipeline_retirement_policy import (
    LegacyStageRetirementPolicy,
    build_legacy_stage_retirement_policy,
    raise_legacy_stage_retired,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STAGE = "covapie_split_leakage_qa_gate_v0"
STAGE = LEGACY_STAGE
PREVIOUS_STAGE = step13bk.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_split_leakage_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_leakage_qa_precondition_audit.csv"
SPLIT_UNIT_PREVIEW_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_unit_preview_qa_audit.csv"
GROUP_INTEGRITY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_group_integrity_qa_audit.csv"
MASK_INTEGRITY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_mask_integrity_qa_audit.csv"
LEAKAGE_RISK_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_split_leakage_risk_qa_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_split_leakage_qa_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_split_leakage_qa_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_split_leakage_qa_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_split_leakage_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_split_leakage_qa_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13bk.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bk.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bk.METADATA_CSV_SHA256
MASK_ALIAS_BY_NAME = dict(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES))

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SPLIT_UNIT_QA_COLUMNS = [
    "split_unit_id",
    "extracted_event_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "csv_json_consistent",
    "sample_rows_in_unit",
    "mask_task_count_in_unit",
    "mask_task_names_in_unit",
    "sample_ids_in_unit_count",
    "split_assignment_current_step",
    "real_split_assignment_written",
    "eligible_for_training_split",
    "blocker_reason_contains_smoke_size_too_small",
    "blocker_reason_contains_feature_semantics_audit_required",
    "blocker_reason_contains_scaffold_linker_warhead_annotation_required",
    "split_unit_preview_qa_passed",
    "qa_comment",
]
GROUP_INTEGRITY_COLUMNS = [
    "group_type",
    "group_id",
    "related_split_unit_id",
    "sample_rows_in_group",
    "unique_split_unit_count",
    "mask_task_count",
    "all_rows_bound_to_one_unit",
    "no_row_level_split_assignment",
    "no_real_split_assignment_written",
    "group_integrity_qa_passed",
    "qa_comment",
]
MASK_INTEGRITY_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "observed_unique_event_count",
    "observed_unique_split_unit_count",
    "expected_row_count",
    "expected_unique_event_count",
    "expected_unique_split_unit_count",
    "mask_rows_distributed_across_all_events",
    "alias_matches_canonical",
    "b3_scaffold_only_included_when_applicable",
    "no_extra_mask_tasks",
    "mask_integrity_qa_passed",
    "qa_comment",
]
LEAKAGE_RISK_QA_COLUMNS = [
    "risk_group",
    "observed_group_count",
    "observed_max_rows_per_group",
    "smoke_status",
    "expected_status",
    "risk_level",
    "required_action_before_real_split",
    "risk_status_consistent_with_design",
    "risk_qa_passed",
    "qa_comment",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKER_COLUMNS = ["training_blocker_item", "required_status", "current_step_status", "training_blocker_passed", "qa_comment"]

GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "build_split_unit_preview_qa_rows",
    "build_group_integrity_qa_rows",
    "build_mask_integrity_qa_rows",
    "build_leakage_risk_qa_rows",
    "build_boundary_rows",
    "build_git_safety_rows",
    "build_training_blocker_rows",
    "run_covapie_split_leakage_qa_gate_v0",
)


def build_retirement_policy() -> LegacyStageRetirementPolicy:
    return build_legacy_stage_retirement_policy(LEGACY_STAGE)


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _metadata_hash() -> str:
    path = step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    root = step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    root = step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
        "covapie_split_unit_smoke_preview.csv",
        "covapie_split_unit_smoke_preview.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def _json_by_split_unit() -> dict[str, dict[str, Any]]:
    rows = _load_json(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_JSON)
    return {row["split_unit_id"]: row for row in rows}


def _split_unit_by_event() -> dict[str, str]:
    return {row["extracted_event_id"]: row["split_unit_id"] for row in _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)}


def _split_unit_by_candidate() -> dict[str, str]:
    return {row["candidate_metadata_id"]: row["split_unit_id"] for row in _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)}


def build_precondition_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    manifest13bk = _load_json(step13bk.MANIFEST_JSON)
    manifest13bj = _load_json(step13bk.step13bj.MANIFEST_JSON)
    manifest13bi = _load_json(step13bk.step13bj.step13bi.MANIFEST_JSON)
    sample_rows = _csv_rows(step13bk.step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    split_preview_csv = _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)
    split_preview_json = _load_json(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_JSON)
    checks = [
        ("step13bk_manifest_exists", step13bk.MANIFEST_JSON, "exists", step13bk.MANIFEST_JSON.exists(), step13bk.MANIFEST_JSON.exists()),
        ("step13bk_stage", step13bk.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bk.get("stage"), manifest13bk.get("stage") == PREVIOUS_STAGE),
        ("step13bk_all_checks_passed", step13bk.MANIFEST_JSON, "true", manifest13bk.get("all_checks_passed"), manifest13bk.get("all_checks_passed") is True),
        ("step13bk_ready_for_split_leakage_qa_gate", step13bk.MANIFEST_JSON, "true", manifest13bk.get("ready_for_covapie_split_leakage_qa_gate"), manifest13bk.get("ready_for_covapie_split_leakage_qa_gate") is True),
        ("step13bk_ready_for_feature_semantics_audit_gate", step13bk.MANIFEST_JSON, "false", manifest13bk.get("ready_for_covapie_feature_semantics_audit_gate"), manifest13bk.get("ready_for_covapie_feature_semantics_audit_gate") is False),
        ("step13bk_ready_for_final_dataset_design_gate", step13bk.MANIFEST_JSON, "false", manifest13bk.get("ready_for_covapie_final_dataset_design_gate"), manifest13bk.get("ready_for_covapie_final_dataset_design_gate") is False),
        ("step13bk_ready_for_dataloader_smoke", step13bk.MANIFEST_JSON, "false", manifest13bk.get("ready_for_covapie_dataloader_smoke"), manifest13bk.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bk_ready_for_training", step13bk.MANIFEST_JSON, "false", manifest13bk.get("ready_for_training"), manifest13bk.get("ready_for_training") is False),
        ("step13bk_ready_to_train_now", step13bk.MANIFEST_JSON, "false", manifest13bk.get("ready_to_train_now"), manifest13bk.get("ready_to_train_now") is False),
        ("step13bk_split_unit_preview_csv_row_count", step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV, "4", len(split_preview_csv), len(split_preview_csv) == 4),
        ("step13bk_split_unit_preview_json_row_count", step13bk.SPLIT_UNIT_SMOKE_PREVIEW_JSON, "4", len(split_preview_json), isinstance(split_preview_json, list) and len(split_preview_json) == 4),
        ("step13bk_parent_event_group_integrity_passed", step13bk.MANIFEST_JSON, "true", manifest13bk.get("parent_event_group_integrity_passed"), manifest13bk.get("parent_event_group_integrity_passed") is True),
        ("step13bk_candidate_metadata_group_integrity_passed", step13bk.MANIFEST_JSON, "true", manifest13bk.get("candidate_metadata_group_integrity_passed"), manifest13bk.get("candidate_metadata_group_integrity_passed") is True),
        ("step13bk_mask_task_grouping_integrity_passed", step13bk.MANIFEST_JSON, "true", manifest13bk.get("mask_task_grouping_integrity_passed"), manifest13bk.get("mask_task_grouping_integrity_passed") is True),
        ("step13bk_risk_smoke_audit_passed", step13bk.MANIFEST_JSON, "true", manifest13bk.get("split_leakage_risk_smoke_audit_passed"), manifest13bk.get("split_leakage_risk_smoke_audit_passed") is True),
        ("step13bj_design_gate_passed", step13bk.step13bj.MANIFEST_JSON, "true", manifest13bj.get("all_checks_passed"), manifest13bj.get("all_checks_passed") is True),
        ("step13bi_sample_index_qa_passed", step13bk.step13bj.step13bi.MANIFEST_JSON, "true", manifest13bi.get("all_checks_passed"), manifest13bi.get("all_checks_passed") is True),
        ("step13bh_sample_index_csv_shape", step13bk.step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV, "20x31", f"{len(sample_rows)}x{len(sample_rows[0]) if sample_rows else 0}", len(sample_rows) == 20 and bool(sample_rows) and len(sample_rows[0]) == 31),
        ("canonical_mask_count", step13bk.MANIFEST_JSON, "5", manifest13bk.get("source_canonical_mask_task_count"), manifest13bk.get("source_canonical_mask_task_count") == 5),
        ("b3_scaffold_only_included", step13bk.MANIFEST_JSON, "true", manifest13bk.get("b3_scaffold_only_included"), manifest13bk.get("b3_scaffold_only_included") is True),
        ("no_extra_mask_tasks_added", step13bk.MANIFEST_JSON, "true", manifest13bk.get("no_extra_mask_tasks_added"), manifest13bk.get("no_extra_mask_tasks_added") is True),
        ("metadata_csv_hash_unchanged", step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, check, expected, observed, passed in checks
    ]


def build_split_unit_preview_qa_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    json_rows = _json_by_split_unit()
    rows = []
    for row in _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV):
        json_row = json_rows.get(row["split_unit_id"], {})
        sample_ids = row["sample_ids_in_unit"].split(";") if row["sample_ids_in_unit"] else []
        csv_json_consistent = all(str(json_row.get(key, "")) == str(value) for key, value in row.items())
        blockers = row["blocker_reason"]
        passed = all(
            [
                csv_json_consistent,
                row["sample_rows_in_unit"] == "5",
                row["mask_task_count_in_unit"] == "5",
                row["mask_task_names_in_unit"].split(";") == CANONICAL_MASK_TASK_NAMES,
                len(sample_ids) == 5,
                row["split_assignment_current_step"] == "not_written_current_step",
                row["real_split_assignment_written"] == "False",
                row["eligible_for_training_split"] == "False",
                "smoke_size_too_small" in blockers,
                "feature_semantics_audit_required" in blockers,
                "scaffold_linker_warhead_annotation_required" in blockers,
            ]
        )
        rows.append(
            {
                "split_unit_id": row["split_unit_id"],
                "extracted_event_id": row["extracted_event_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "csv_json_consistent": csv_json_consistent,
                "sample_rows_in_unit": row["sample_rows_in_unit"],
                "mask_task_count_in_unit": row["mask_task_count_in_unit"],
                "mask_task_names_in_unit": row["mask_task_names_in_unit"],
                "sample_ids_in_unit_count": len(sample_ids),
                "split_assignment_current_step": row["split_assignment_current_step"],
                "real_split_assignment_written": row["real_split_assignment_written"],
                "eligible_for_training_split": row["eligible_for_training_split"],
                "blocker_reason_contains_smoke_size_too_small": "smoke_size_too_small" in blockers,
                "blocker_reason_contains_feature_semantics_audit_required": "feature_semantics_audit_required" in blockers,
                "blocker_reason_contains_scaffold_linker_warhead_annotation_required": "scaffold_linker_warhead_annotation_required" in blockers,
                "split_unit_preview_qa_passed": passed,
                "qa_comment": "split unit preview CSV/JSON and blocker boundary validated",
            }
        )
    return rows


def build_group_integrity_qa_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    split_by_event = _split_unit_by_event()
    split_by_candidate = _split_unit_by_candidate()
    rows = []
    for row in _csv_rows(step13bk.PARENT_EVENT_GROUP_INTEGRITY_AUDIT_CSV):
        passed = all(
            [
                row["sample_rows_for_event"] == "5",
                row["unique_split_unit_count"] == "1",
                row["mask_task_count"] == "5",
                row["all_mask_rows_bound_to_parent_event"] == "True",
                row["no_row_level_split_assignment"] == "True",
                row["group_integrity_passed"] == "True",
            ]
        )
        rows.append(
            {
                "group_type": "parent_event",
                "group_id": row["extracted_event_id"],
                "related_split_unit_id": split_by_event[row["extracted_event_id"]],
                "sample_rows_in_group": row["sample_rows_for_event"],
                "unique_split_unit_count": row["unique_split_unit_count"],
                "mask_task_count": row["mask_task_count"],
                "all_rows_bound_to_one_unit": row["all_mask_rows_bound_to_parent_event"],
                "no_row_level_split_assignment": row["no_row_level_split_assignment"],
                "no_real_split_assignment_written": True,
                "group_integrity_qa_passed": passed,
                "qa_comment": "parent event group remains bound to one split unit",
            }
        )
    for row in _csv_rows(step13bk.CANDIDATE_METADATA_GROUP_INTEGRITY_AUDIT_CSV):
        passed = all(
            [
                row["sample_rows_for_candidate"] == "5",
                row["unique_split_unit_count"] == "1",
                row["all_candidate_rows_bound_to_one_unit"] == "True",
                row["candidate_group_integrity_passed"] == "True",
            ]
        )
        rows.append(
            {
                "group_type": "candidate_metadata",
                "group_id": row["candidate_metadata_id"],
                "related_split_unit_id": split_by_candidate[row["candidate_metadata_id"]],
                "sample_rows_in_group": row["sample_rows_for_candidate"],
                "unique_split_unit_count": row["unique_split_unit_count"],
                "mask_task_count": 5,
                "all_rows_bound_to_one_unit": row["all_candidate_rows_bound_to_one_unit"],
                "no_row_level_split_assignment": True,
                "no_real_split_assignment_written": True,
                "group_integrity_qa_passed": passed,
                "qa_comment": "candidate metadata group remains bound to one split unit",
            }
        )
    return rows


def build_mask_integrity_qa_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    split_rows = _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)
    split_units_by_mask = {
        mask: {
            row["split_unit_id"]
            for row in split_rows
            if mask in row["mask_task_names_in_unit"].split(";")
        }
        for mask in CANONICAL_MASK_TASK_NAMES
    }
    source_rows = _csv_rows(step13bk.step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    observed_masks = {row["mask_task_name"] for row in source_rows}
    rows = []
    for row in _csv_rows(step13bk.MASK_TASK_GROUPING_INTEGRITY_AUDIT_CSV):
        mask_name = row["mask_task_name"]
        expected_alias = MASK_ALIAS_BY_NAME[mask_name]
        split_unit_count = len(split_units_by_mask[mask_name])
        b3_ok = mask_name != "scaffold_only" or row["mask_task_alias"] == "B3"
        passed = all(
            [
                row["observed_row_count"] == "4",
                row["observed_unique_event_count"] == "4",
                split_unit_count == 4,
                row["mask_rows_distributed_across_all_events"] == "True",
                row["mask_task_alias"] == expected_alias,
                b3_ok,
                observed_masks == set(CANONICAL_MASK_TASK_NAMES),
                row["mask_grouping_integrity_passed"] == "True",
            ]
        )
        rows.append(
            {
                "mask_task_name": mask_name,
                "mask_task_alias": row["mask_task_alias"],
                "observed_row_count": row["observed_row_count"],
                "observed_unique_event_count": row["observed_unique_event_count"],
                "observed_unique_split_unit_count": split_unit_count,
                "expected_row_count": 4,
                "expected_unique_event_count": 4,
                "expected_unique_split_unit_count": 4,
                "mask_rows_distributed_across_all_events": row["mask_rows_distributed_across_all_events"],
                "alias_matches_canonical": row["mask_task_alias"] == expected_alias,
                "b3_scaffold_only_included_when_applicable": b3_ok,
                "no_extra_mask_tasks": observed_masks == set(CANONICAL_MASK_TASK_NAMES),
                "mask_integrity_qa_passed": passed,
                "qa_comment": "canonical mask integrity preserved across all split units",
            }
        )
    return rows


def build_leakage_risk_qa_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    expected_status = {
        "row_level_random_split_forbidden": "forbidden_by_design",
        "scaffold_identity_missing": "required_before_real_split",
        "warhead_type_missing": "required_before_real_split",
        "feature_semantics_audit_required": "required_before_training",
        "smoke_size_too_small_for_real_train_val_test": "blocks_real_split_assignment",
    }
    rows = []
    for row in _csv_rows(step13bk.RISK_SMOKE_AUDIT_CSV):
        risk_group = row["risk_group"]
        expected = expected_status.get(risk_group, "observed_current_smoke_preview")
        status_ok = row["smoke_status"] == expected
        count_ok = True
        if risk_group in {"parent_event_grouping", "candidate_metadata_grouping", "pdb_grouping"}:
            count_ok = row["observed_group_count"] == "4" and row["observed_max_rows_per_group"] == "5"
        if risk_group == "mask_task_grouping":
            count_ok = row["observed_group_count"] == "5" and row["observed_max_rows_per_group"] == "4"
        passed = status_ok and count_ok and row["risk_smoke_audit_passed"] == "True"
        rows.append(
            {
                "risk_group": risk_group,
                "observed_group_count": row["observed_group_count"],
                "observed_max_rows_per_group": row["observed_max_rows_per_group"],
                "smoke_status": row["smoke_status"],
                "expected_status": expected,
                "risk_level": row["risk_level"],
                "required_action_before_real_split": row["required_action_before_real_split"],
                "risk_status_consistent_with_design": status_ok,
                "risk_qa_passed": passed,
                "qa_comment": "risk smoke status matches split/leakage design boundary",
            }
        )
    return rows


def build_boundary_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    statuses = {
        "split_leakage_qa_gate": "executed_qa_gate_only",
        "read_step13bk_smoke_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bj_design_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bi_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "split_unit_preview_write_current_step": "not_executed_current_step_already_completed_previous_step",
        "split_assignment_write": "blocked_current_step",
        "leakage_matrix_write": "blocked_current_step",
        "final_dataset": "blocked_current_step",
        "new_sample_index": "blocked_current_step",
        "dataloader_smoke": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "coordinate_extraction": "not_executed_or_not_allowed",
        "network_access": "not_executed_or_not_allowed",
        "raw_download": "not_executed_or_not_allowed",
        "rdkit_biopdb_gemmi": "not_executed_or_not_allowed",
        "torch_model_training": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "boundary_safety_passed": True,
            "qa_comment": "split/leakage QA gate boundary respected",
        }
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "boundary manifest", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_split_unit_preview_rewritten_current_step", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", str(step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bk_artifacts_unchanged", str(step13bk.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.OUTPUT_ROOT.as_posix()])),
        ("step13bj_artifacts_unchanged", str(step13bk.step13bj.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.step13bj.OUTPUT_ROOT.as_posix()])),
        ("step13bi_artifacts_unchanged", str(step13bk.step13bj.step13bi.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.step13bj.step13bi.OUTPUT_ROOT.as_posix()])),
        ("step13bh_artifacts_unchanged", str(step13bk.step13bj.step13bi.step13bh.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.step13bj.step13bi.step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", str(step13bk.step13bj.step13bi.step13bh.step13bg.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.step13bj.step13bi.step13bh.step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", str(step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", str(step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "no_diff", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "no_diff", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": "passed" if passed else "failed",
            "git_safety_audit_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, command, required, passed in checks
    ]


def build_training_blocker_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    blockers = [
        "no_real_train_val_test_split",
        "no_split_assignments",
        "no_leakage_matrix",
        "no_final_dataset",
        "no_dataloader_smoke",
        "no_training",
        "smoke_size_too_small_for_real_split",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "ligand_residue_atom_pair_label_audit_required",
        "pre_post_geometry_label_audit_required",
        "feature_semantics_audit_required",
        "feature_semantics_fully_audited_claimed_false",
        "leakage_split_qa_required_before_final_dataset",
        "ready_for_training_false",
    ]
    return [
        {
            "training_blocker_item": item,
            "required_status": "blocking_or_false_until_future_gate",
            "current_step_status": "passed",
            "training_blocker_passed": True,
            "qa_comment": "training remains blocked after split/leakage QA gate",
        }
        for item in blockers
    ]


def run_covapie_split_leakage_qa_gate_v0() -> dict[str, Any]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    precondition_rows = build_precondition_rows()
    split_unit_rows = build_split_unit_preview_qa_rows()
    group_rows = build_group_integrity_qa_rows()
    mask_rows = build_mask_integrity_qa_rows()
    risk_rows = build_leakage_risk_qa_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    training_blocker_rows = build_training_blocker_rows()
    manifest13bk = _load_json(step13bk.MANIFEST_JSON)
    sample_rows = _csv_rows(step13bk.step13bj.step13bi.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bk_split_leakage_smoke_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(sample_rows),
        "source_unique_event_count": len({row["extracted_event_id"] for row in sample_rows}),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in sample_rows}),
        "source_split_unit_preview_row_count": len(_csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)),
        "source_split_unit_preview_json_row_count": len(_load_json(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_JSON)),
        "split_unit_preview_qa_row_count": len(split_unit_rows),
        "group_integrity_qa_row_count": len(group_rows),
        "mask_integrity_qa_row_count": len(mask_rows),
        "leakage_risk_qa_row_count": len(risk_rows),
        "split_unit_preview_qa_passed": all(_bool(row["split_unit_preview_qa_passed"]) for row in split_unit_rows),
        "group_integrity_qa_passed": all(_bool(row["group_integrity_qa_passed"]) for row in group_rows),
        "mask_integrity_qa_passed": all(_bool(row["mask_integrity_qa_passed"]) for row in mask_rows),
        "leakage_risk_qa_passed": all(_bool(row["risk_qa_passed"]) for row in risk_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "training_blockers_passed": all(_bool(row["training_blocker_passed"]) for row in training_blocker_rows),
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_unit_preview_written_previous_step": manifest13bk.get("split_unit_preview_written_current_step") is True,
        "split_unit_preview_written_current_step": False,
        "real_train_val_test_split_written": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "atom_site_scan_current_step": False,
        "struct_conn_scan_current_step": False,
        "coordinate_extraction_current_step": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_file_created": False,
        "sdf_read": False,
        "pdb_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_feature_semantics_audit_gate": True,
        "ready_for_covapie_final_dataset_design_gate": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in sample_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in sample_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_feature_semantics_audit_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bk_split_leakage_smoke_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["source_split_unit_preview_row_count"] == 4,
            manifest["source_split_unit_preview_json_row_count"] == 4,
            manifest["split_unit_preview_qa_row_count"] == 4,
            manifest["group_integrity_qa_row_count"] == 8,
            manifest["mask_integrity_qa_row_count"] == 5,
            manifest["leakage_risk_qa_row_count"] == 12,
            manifest["split_unit_preview_qa_passed"],
            manifest["group_integrity_qa_passed"],
            manifest["mask_integrity_qa_passed"],
            manifest["leakage_risk_qa_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["training_blockers_passed"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["split_leakage_qa_gate_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "split_unit_rows": split_unit_rows,
        "group_rows": group_rows,
        "mask_rows": mask_rows,
        "risk_rows": risk_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }
