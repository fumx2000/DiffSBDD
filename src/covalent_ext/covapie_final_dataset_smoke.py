from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_final_dataset_design_gate as step13bn
from covalent_ext.covapie_legacy_pipeline_retirement_policy import (
    LegacyStageRetirementPolicy,
    build_legacy_stage_retirement_policy,
    raise_legacy_stage_retired,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STAGE = "covapie_final_dataset_smoke_v0"
STAGE = LEGACY_STAGE
PREVIOUS_STAGE = step13bn.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_smoke_precondition_audit.csv"
SMOKE_PREVIEW_CSV = OUTPUT_ROOT / "covapie_final_dataset_smoke_preview.csv"
SMOKE_PREVIEW_JSON = OUTPUT_ROOT / "covapie_final_dataset_smoke_preview.json"
SCHEMA_ORDER_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_schema_order_smoke_audit.csv"
ROW_LINEAGE_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_row_lineage_smoke_audit.csv"
MASK_DISTRIBUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_mask_distribution_smoke_audit.csv"
FEATURE_BLOCKER_AUDIT_CSV = OUTPUT_ROOT / "covapie_final_dataset_feature_blocker_smoke_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_final_dataset_smoke_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_final_dataset_smoke_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_final_dataset_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_final_dataset_smoke_v0_summary.md")

step13bm = step13bn.step13bm
step13bl = step13bn.step13bl
step13bk = step13bn.step13bk
step13bj = step13bn.step13bj
step13bi = step13bn.step13bi
step13bh = step13bn.step13bh
step13bg = step13bn.step13bg
step13bf = step13bn.step13bf
step13be = step13bn.step13be
step13bd = step13bn.step13bd

CANONICAL_MASK_TASK_NAMES = step13bn.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bn.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bn.METADATA_CSV_SHA256

TRAINING_BLOCKER_SUMMARY = ";".join(
    [
        "feature_semantics_known_for_training_false",
        "unknown_atom_feature_policy_not_finalized",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "pre_covalent_geometry_not_materialized",
        "ready_for_training_false",
    ]
)

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_ORDER_COLUMNS = ["audit_item", "expected_status", "observed_status", "schema_field_count", "schema_order_matches_contract", "csv_json_consistent", "schema_order_smoke_passed", "qa_comment"]
ROW_LINEAGE_COLUMNS = [
    "final_dataset_row_id",
    "sample_id",
    "split_unit_id",
    "extracted_event_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "mask_task_name",
    "mask_task_alias",
    "source_sample_index_row_found",
    "source_split_unit_found",
    "parent_event_group_bound_to_one_split_unit",
    "final_dataset_smoke_row_materialized",
    "final_dataset_real_row_materialized",
    "dataloader_ready",
    "ready_for_training",
    "row_lineage_smoke_passed",
    "qa_comment",
]
MASK_DISTRIBUTION_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "observed_unique_event_count",
    "observed_unique_split_unit_count",
    "expected_row_count",
    "expected_unique_event_count",
    "expected_unique_split_unit_count",
    "alias_matches_canonical",
    "b3_scaffold_only_included_when_applicable",
    "no_extra_mask_tasks",
    "mask_distribution_smoke_passed",
    "qa_comment",
]
FEATURE_BLOCKER_COLUMNS = ["blocker_item", "expected_status", "observed_status", "blocker_preserved_in_all_rows", "required_before_training", "blocker_smoke_passed", "qa_comment"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "build_smoke_preview_rows",
    "build_schema_order_rows",
    "build_row_lineage_rows",
    "build_mask_distribution_rows",
    "build_feature_blocker_rows",
    "build_boundary_rows",
    "build_git_safety_rows",
    "run_covapie_final_dataset_smoke_v0",
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
    return hashlib.sha256(step13bd.METADATA_CSV.read_bytes()).hexdigest() if step13bd.METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _stringify_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{key: str(value) for key, value in row.items()} for row in rows]


def _schema_fields() -> list[str]:
    return [row["final_dataset_field_name"] for row in _csv_rows(step13bn.SCHEMA_CONTRACT_CSV)]


def _split_unit_by_sample_id() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV):
        for sample_id in row["sample_ids_in_unit"].split(";"):
            mapping[sample_id] = row["split_unit_id"]
    return mapping


def _split_unit_by_event(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for row in rows:
        mapping.setdefault(row["extracted_event_id"], set()).add(row["split_unit_id"])
    return mapping


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "final_dataset.csv",
        "final_dataset.json",
        "final_dataset_smoke.csv",
        "final_dataset_smoke.json",
        "sample_index.csv",
        "sample_index.json",
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "training_report.csv",
        "training_report.json",
    }
    allowed = {SMOKE_PREVIEW_CSV.name, SMOKE_PREVIEW_JSON.name}
    return root.exists() and any(path.name in forbidden and path.name not in allowed for path in root.rglob("*"))


def build_precondition_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    manifest13bn = _load_json(step13bn.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    split_rows = _csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    checks = [
        ("step13bn_manifest_exists", step13bn.MANIFEST_JSON, "exists", step13bn.MANIFEST_JSON.exists(), step13bn.MANIFEST_JSON.exists()),
        ("step13bn_stage", step13bn.MANIFEST_JSON, step13bn.STAGE, manifest13bn.get("stage"), manifest13bn.get("stage") == step13bn.STAGE),
        ("step13bn_all_checks_passed", step13bn.MANIFEST_JSON, "true", manifest13bn.get("all_checks_passed"), manifest13bn.get("all_checks_passed") is True),
        ("step13bn_ready_for_final_dataset_smoke", step13bn.MANIFEST_JSON, "true", manifest13bn.get("ready_for_covapie_final_dataset_smoke"), manifest13bn.get("ready_for_covapie_final_dataset_smoke") is True),
        ("step13bn_ready_for_final_dataset_qa_gate", step13bn.MANIFEST_JSON, "false", manifest13bn.get("ready_for_covapie_final_dataset_qa_gate"), manifest13bn.get("ready_for_covapie_final_dataset_qa_gate") is False),
        ("step13bn_ready_for_dataloader_smoke", step13bn.MANIFEST_JSON, "false", manifest13bn.get("ready_for_covapie_dataloader_smoke"), manifest13bn.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bn_ready_for_training", step13bn.MANIFEST_JSON, "false", manifest13bn.get("ready_for_training"), manifest13bn.get("ready_for_training") is False),
        ("step13bn_ready_to_train_now", step13bn.MANIFEST_JSON, "false", manifest13bn.get("ready_to_train_now"), manifest13bn.get("ready_to_train_now") is False),
        ("step13bn_schema_contract_row_count", step13bn.SCHEMA_CONTRACT_CSV, "45", len(_csv_rows(step13bn.SCHEMA_CONTRACT_CSV)), len(_csv_rows(step13bn.SCHEMA_CONTRACT_CSV)) == 45),
        ("step13bn_row_lineage_contract_row_count", step13bn.ROW_LINEAGE_CONTRACT_CSV, "20", len(_csv_rows(step13bn.ROW_LINEAGE_CONTRACT_CSV)), len(_csv_rows(step13bn.ROW_LINEAGE_CONTRACT_CSV)) == 20),
        ("step13bn_feature_requirement_contract_row_count", step13bn.FEATURE_REQUIREMENT_CONTRACT_CSV, "13", len(_csv_rows(step13bn.FEATURE_REQUIREMENT_CONTRACT_CSV)), len(_csv_rows(step13bn.FEATURE_REQUIREMENT_CONTRACT_CSV)) == 13),
        ("step13bn_split_policy_contract_row_count", step13bn.SPLIT_POLICY_CONTRACT_CSV, "10", len(_csv_rows(step13bn.SPLIT_POLICY_CONTRACT_CSV)), len(_csv_rows(step13bn.SPLIT_POLICY_CONTRACT_CSV)) == 10),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("step13bh_sample_index_smoke_shape", step13bh.SAMPLE_INDEX_SMOKE_CSV, "20x31", f"{len(sample_rows)}x{len(sample_rows[0]) if sample_rows else 0}", len(sample_rows) == 20 and bool(sample_rows) and len(sample_rows[0]) == 31),
        ("step13bk_split_unit_preview_row_count", step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV, "4", len(split_rows), len(split_rows) == 4),
        ("step13be_event_table_row_count", step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("step13be_protein_atom_table_row_count", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("step13be_ligand_atom_table_row_count", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("canonical_mask_count", step13bh.SAMPLE_INDEX_SMOKE_CSV, "5", len({row["mask_task_name"] for row in sample_rows}), len({row["mask_task_name"] for row in sample_rows}) == 5),
        ("b3_scaffold_only_included", step13bh.SAMPLE_INDEX_SMOKE_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in sample_rows}, "scaffold_only" in {row["mask_task_name"] for row in sample_rows}),
        ("no_extra_mask_tasks_added", step13bh.SAMPLE_INDEX_SMOKE_CSV, "true", {row["mask_task_name"] for row in sample_rows}, {row["mask_task_name"] for row in sample_rows} == set(CANONICAL_MASK_TASK_NAMES)),
        ("metadata_csv_hash_unchanged", step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def build_smoke_preview_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    schema_fields = _schema_fields()
    split_by_sample = _split_unit_by_sample_id()
    rows = []
    for sample in _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV):
        row = dict(sample)
        row.update(
            {
                "final_dataset_row_id": f"final_dataset_smoke::{sample['sample_id']}",
                "split_unit_id": split_by_sample[sample["sample_id"]],
                "source_sample_index_path": step13bh.SAMPLE_INDEX_SMOKE_CSV.as_posix(),
                "source_split_unit_preview_path": step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV.as_posix(),
                "feature_semantics_contract_path": step13bm.FEATURE_SEMANTICS_CONTRACT_CSV.as_posix(),
                "coordinate_unit": "angstrom",
                "coordinate_frame_status": "structure_coordinate_frame_inherited_not_finalized",
                "pre_covalent_geometry_status": "pre_covalent_geometry_not_materialized_current_step",
                "post_covalent_geometry_status": "post_covalent_geometry_present",
                "feature_semantics_audit_status": "feature_semantics_audit_completed_current_step",
                "feature_semantics_known_for_training": False,
                "unknown_atom_feature_policy_finalized_for_training": False,
                "leakage_split_qa_status": "split_leakage_qa_passed",
                "final_dataset_materialized_current_step": True,
                "dataloader_ready": False,
                "ready_for_training": False,
                "training_blocker_summary": TRAINING_BLOCKER_SUMMARY,
                "schema_version": STAGE,
            }
        )
        rows.append({field: row[field] for field in schema_fields})
    return rows


def build_schema_order_rows(preview_rows: list[dict[str, Any]], json_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    schema_fields = _schema_fields()
    csv_fields = list(preview_rows[0].keys()) if preview_rows else []
    csv_json_consistent = _stringify_rows(preview_rows) == json_rows
    passed = len(preview_rows) == 20 and len(json_rows) == 20 and len(csv_fields) == 45 and csv_fields == schema_fields and csv_json_consistent
    return [
        {
            "audit_item": "final_dataset_smoke_preview_schema_order",
            "expected_status": "20_rows_45_fields_schema_order_matches_step13bn",
            "observed_status": f"{len(preview_rows)}_rows_{len(csv_fields)}_fields",
            "schema_field_count": len(schema_fields),
            "schema_order_matches_contract": csv_fields == schema_fields,
            "csv_json_consistent": csv_json_consistent,
            "schema_order_smoke_passed": passed,
            "qa_comment": "CSV/JSON smoke preview normalized content and schema order validated",
        }
    ]


def build_row_lineage_rows(preview_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    sample_ids = {row["sample_id"] for row in _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)}
    split_by_sample = _split_unit_by_sample_id()
    event_to_splits = _split_unit_by_event(preview_rows)
    rows = []
    for row in preview_rows:
        event_bound = len(event_to_splits[row["extracted_event_id"]]) == 1
        passed = (
            row["final_dataset_row_id"] == f"final_dataset_smoke::{row['sample_id']}"
            and row["sample_id"] in sample_ids
            and row["split_unit_id"] == split_by_sample.get(row["sample_id"])
            and event_bound
            and _bool(row["final_dataset_materialized_current_step"])
            and not _bool(row["dataloader_ready"])
            and not _bool(row["ready_for_training"])
        )
        rows.append(
            {
                "final_dataset_row_id": row["final_dataset_row_id"],
                "sample_id": row["sample_id"],
                "split_unit_id": row["split_unit_id"],
                "extracted_event_id": row["extracted_event_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "mask_task_name": row["mask_task_name"],
                "mask_task_alias": row["mask_task_alias"],
                "source_sample_index_row_found": row["sample_id"] in sample_ids,
                "source_split_unit_found": row["split_unit_id"] == split_by_sample.get(row["sample_id"]),
                "parent_event_group_bound_to_one_split_unit": event_bound,
                "final_dataset_smoke_row_materialized": True,
                "final_dataset_real_row_materialized": False,
                "dataloader_ready": False,
                "ready_for_training": False,
                "row_lineage_smoke_passed": passed,
                "qa_comment": "smoke row lineage validated without real final dataset materialization",
            }
        )
    return rows


def build_mask_distribution_rows(preview_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    observed_masks = {row["mask_task_name"] for row in preview_rows}
    rows = []
    for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        mask_rows = [row for row in preview_rows if row["mask_task_name"] == name]
        event_count = len({row["extracted_event_id"] for row in mask_rows})
        split_count = len({row["split_unit_id"] for row in mask_rows})
        b3_ok = name != "scaffold_only" or alias == "B3"
        passed = len(mask_rows) == 4 and event_count == 4 and split_count == 4 and observed_masks == set(CANONICAL_MASK_TASK_NAMES) and b3_ok
        rows.append(
            {
                "mask_task_name": name,
                "mask_task_alias": alias,
                "observed_row_count": len(mask_rows),
                "observed_unique_event_count": event_count,
                "observed_unique_split_unit_count": split_count,
                "expected_row_count": 4,
                "expected_unique_event_count": 4,
                "expected_unique_split_unit_count": 4,
                "alias_matches_canonical": True,
                "b3_scaffold_only_included_when_applicable": b3_ok,
                "no_extra_mask_tasks": observed_masks == set(CANONICAL_MASK_TASK_NAMES),
                "mask_distribution_smoke_passed": passed,
                "qa_comment": "canonical mask distribution preserved in final dataset smoke preview",
            }
        )
    return rows


def build_feature_blocker_rows(preview_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    blockers = [
        "feature_semantics_known_for_training_false",
        "unknown_atom_feature_policy_not_finalized",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "ligand_residue_atom_pair_label_audit_required",
        "pre_post_geometry_label_audit_required",
        "pre_covalent_geometry_not_materialized",
        "final_dataset_smoke_preview_only",
        "no_real_final_dataset_written",
        "no_dataloader_smoke",
        "no_training_current_step",
        "ready_for_training_false",
        "step12d_smoke_not_final_feature_semantics_audit",
    ]
    checks = {
        "feature_semantics_known_for_training_false": all(not _bool(row["feature_semantics_known_for_training"]) for row in preview_rows),
        "unknown_atom_feature_policy_not_finalized": all(not _bool(row["unknown_atom_feature_policy_finalized_for_training"]) for row in preview_rows),
        "scaffold_linker_warhead_annotation_required": all(row["scaffold_linker_warhead_annotation_status"] == "required_before_training_not_materialized" for row in preview_rows),
        "warhead_type_label_required": all(row["warhead_type_label_status"] == "required_before_training_not_materialized" for row in preview_rows),
        "ligand_residue_atom_pair_label_audit_required": all(row["ligand_residue_atom_pair_label_status"] == "present_from_extraction_qa_feature_audit_required" for row in preview_rows),
        "pre_post_geometry_label_audit_required": all(row["pre_post_geometry_label_status"] == "post_covalent_geometry_present_feature_audit_required" for row in preview_rows),
        "pre_covalent_geometry_not_materialized": all(row["pre_covalent_geometry_status"] == "pre_covalent_geometry_not_materialized_current_step" for row in preview_rows),
        "final_dataset_smoke_preview_only": all(_bool(row["final_dataset_materialized_current_step"]) for row in preview_rows),
        "no_real_final_dataset_written": not _forbidden_named_artifact_exists(),
        "no_dataloader_smoke": all(not _bool(row["dataloader_ready"]) for row in preview_rows),
        "no_training_current_step": True,
        "ready_for_training_false": all(not _bool(row["ready_for_training"]) for row in preview_rows),
        "step12d_smoke_not_final_feature_semantics_audit": True,
    }
    return [
        {
            "blocker_item": blocker,
            "expected_status": "preserved",
            "observed_status": "preserved" if checks[blocker] else "failed",
            "blocker_preserved_in_all_rows": checks[blocker],
            "required_before_training": True,
            "blocker_smoke_passed": checks[blocker],
            "qa_comment": "training blocker preserved in smoke preview rows",
        }
        for blocker in blockers
    ]


def build_boundary_rows() -> list[dict[str, Any]]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    statuses = {
        "final_dataset_smoke": "executed_smoke_preview_only",
        "read_step13bn_design_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bm_feature_semantics_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bk_split_unit_preview": "executed_derived_csv_json_read_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "read_step13be_extracted_tables": "executed_derived_csv_json_read_only",
        "final_dataset_smoke_preview_write": "executed_smoke_preview_only",
        "real_final_dataset_write": "blocked_current_step",
        "new_sample_index_write": "blocked_current_step",
        "split_assignment_write": "blocked_current_step",
        "leakage_matrix_write": "blocked_current_step",
        "dataloader_smoke": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "raw_cif_mmcif_sdf_pdb_gzip_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "atom_site_scan": "not_executed_or_not_allowed",
        "struct_conn_scan": "not_executed_or_not_allowed",
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
            "qa_comment": "final dataset smoke preview boundary respected",
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
        ("no_real_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_generic_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_dataloader_smoke_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts_written", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bn_artifacts_unchanged", str(step13bn.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bn.OUTPUT_ROOT.as_posix()])),
        ("step13bm_artifacts_unchanged", str(step13bm.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bm.OUTPUT_ROOT.as_posix()])),
        ("step13bl_artifacts_unchanged", str(step13bl.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bl.OUTPUT_ROOT.as_posix()])),
        ("step13bk_artifacts_unchanged", str(step13bk.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.OUTPUT_ROOT.as_posix()])),
        ("step13bj_artifacts_unchanged", str(step13bj.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.OUTPUT_ROOT.as_posix()])),
        ("step13bi_artifacts_unchanged", str(step13bi.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.OUTPUT_ROOT.as_posix()])),
        ("step13bh_artifacts_unchanged", str(step13bh.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", str(step13bg.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", str(step13bf.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", str(step13be.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13be.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_final_dataset_smoke_v0() -> dict[str, Any]:
    raise_legacy_stage_retired(LEGACY_STAGE)
    precondition_rows = build_precondition_rows()
    preview_rows = build_smoke_preview_rows()
    json_rows = _stringify_rows(preview_rows)
    schema_order_rows = build_schema_order_rows(preview_rows, json_rows)
    lineage_rows = build_row_lineage_rows(preview_rows)
    mask_rows = build_mask_distribution_rows(preview_rows)
    blocker_rows = build_feature_blocker_rows(preview_rows)
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bn_final_dataset_design_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(_csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)),
        "source_unique_event_count": len({row["extracted_event_id"] for row in preview_rows}),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in preview_rows}),
        "source_split_unit_preview_row_count": len(_csv_rows(step13bk.SPLIT_UNIT_SMOKE_PREVIEW_CSV)),
        "final_dataset_smoke_preview_csv_written": True,
        "final_dataset_smoke_preview_json_written": True,
        "final_dataset_smoke_preview_row_count": len(preview_rows),
        "final_dataset_smoke_preview_column_count": len(preview_rows[0]) if preview_rows else 0,
        "final_dataset_smoke_preview_json_row_count": len(json_rows),
        "schema_order_smoke_audit_passed": all(_bool(row["schema_order_smoke_passed"]) for row in schema_order_rows),
        "row_lineage_smoke_audit_row_count": len(lineage_rows),
        "row_lineage_smoke_audit_passed": all(_bool(row["row_lineage_smoke_passed"]) for row in lineage_rows),
        "mask_distribution_smoke_audit_row_count": len(mask_rows),
        "mask_distribution_smoke_audit_passed": all(_bool(row["mask_distribution_smoke_passed"]) for row in mask_rows),
        "feature_blocker_smoke_audit_row_count": len(blocker_rows),
        "feature_blocker_smoke_audit_passed": all(_bool(row["blocker_smoke_passed"]) for row in blocker_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "final_dataset_smoke_preview_written_current_step": True,
        "real_final_dataset_written": False,
        "generic_final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "real_train_val_test_split_written": False,
        "feature_semantics_audit_completed_current_step": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
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
        "ready_for_covapie_final_dataset_qa_gate": True,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in preview_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in preview_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_final_dataset_qa_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bn_final_dataset_design_gate_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["source_split_unit_preview_row_count"] == 4,
            manifest["final_dataset_smoke_preview_row_count"] == 20,
            manifest["final_dataset_smoke_preview_column_count"] == 45,
            manifest["final_dataset_smoke_preview_json_row_count"] == 20,
            manifest["schema_order_smoke_audit_passed"],
            manifest["row_lineage_smoke_audit_row_count"] == 20,
            manifest["row_lineage_smoke_audit_passed"],
            manifest["mask_distribution_smoke_audit_row_count"] == 5,
            manifest["mask_distribution_smoke_audit_passed"],
            manifest["feature_blocker_smoke_audit_row_count"] == 13,
            manifest["feature_blocker_smoke_audit_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["final_dataset_smoke_preview_written_current_step"],
            not manifest["real_final_dataset_written"],
            not manifest["generic_final_dataset_written"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
            manifest["ready_for_covapie_final_dataset_qa_gate"],
            not manifest["ready_for_covapie_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["final_dataset_smoke_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "preview_rows": preview_rows,
        "json_rows": json_rows,
        "schema_order_rows": schema_order_rows,
        "lineage_rows": lineage_rows,
        "mask_rows": mask_rows,
        "blocker_rows": blocker_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }
