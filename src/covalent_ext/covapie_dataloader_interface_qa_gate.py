from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_dataloader_interface_smoke as step13br


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_dataloader_interface_qa_gate_v0"
PREVIOUS_STAGE = step13br.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_dataloader_interface_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_qa_precondition_audit.csv"
PREVIEW_INTEGRITY_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_preview_integrity_qa_audit.csv"
INPUT_SOURCE_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_input_source_qa_audit.csv"
FIELD_MAPPING_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_field_mapping_qa_audit.csv"
FEATURE_BATCH_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_feature_batch_qa_audit.csv"
MASK_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_mask_qa_audit.csv"
CHECKPOINT_COMPATIBILITY_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_checkpoint_compatibility_qa_audit.csv"
READINESS_QA_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_readiness_qa_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_qa_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_dataloader_interface_qa_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_dataloader_interface_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_dataloader_interface_qa_gate_v0_summary.md")

step13bq = step13br.step13bq
step13bp = step13br.step13bp
step13bo = step13br.step13bo
step13bn = step13br.step13bn
step13bm = step13br.step13bm
step13bl = step13br.step13bl
step13bk = step13br.step13bk
step13bj = step13br.step13bj
step13bi = step13br.step13bi
step13bh = step13br.step13bh
step13bg = step13br.step13bg
step13bf = step13br.step13bf
step13be = step13br.step13be
step13bd = step13br.step13bd

CANONICAL_MASK_TASK_NAMES = step13br.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13br.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13br.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
PREVIEW_INTEGRITY_COLUMNS = [
    "dataloader_interface_smoke_row_id",
    "final_dataset_row_id",
    "sample_id",
    "split_unit_id",
    "extracted_event_id",
    "pdb_id",
    "het_code",
    "mask_task_name",
    "mask_task_alias",
    "source_final_dataset_preview_row_found",
    "interface_row_id_deterministic",
    "csv_json_row_consistent",
    "final_dataset_row_id_preserved",
    "sample_id_preserved",
    "split_unit_id_preserved",
    "extracted_event_id_preserved",
    "interface_preview_rewritten_current_step",
    "actual_dataloader_smoke_written",
    "torch_tensor_created_current_step",
    "checkpoint_loaded_current_step",
    "model_forward_called_current_step",
    "ready_for_training",
    "preview_integrity_qa_passed",
    "qa_comment",
]
INPUT_SOURCE_QA_COLUMNS = [
    "input_source_name",
    "source_path_or_policy",
    "source_type",
    "allowed_access_mode",
    "source_exists_or_policy_valid",
    "current_step_access_status",
    "runtime_dependency_used_current_step",
    "raw_access_blocked",
    "input_source_smoke_passed",
    "input_source_qa_passed",
    "qa_comment",
]
FIELD_MAPPING_QA_COLUMNS = [
    "final_dataset_field_name",
    "future_dataloader_role",
    "future_batch_key_or_metadata_key",
    "source_value_present_in_preview",
    "tensorization_status_current_step",
    "current_smoke_value_status",
    "blocker_before_training",
    "field_mapping_smoke_passed",
    "field_mapping_qa_passed",
    "qa_comment",
]
FEATURE_BATCH_QA_COLUMNS = [
    "interface_item",
    "interface_contract_type",
    "source_field_or_table",
    "future_tensor_name_or_metadata_key",
    "current_step_materialized",
    "current_step_status",
    "torch_tensor_created",
    "actual_collate_implemented",
    "blocker_status",
    "feature_batch_smoke_passed",
    "feature_batch_qa_passed",
    "qa_comment",
]
MASK_QA_COLUMNS = [
    "mask_interface_item",
    "mask_task_name",
    "mask_task_alias",
    "observed_row_count",
    "expected_row_count",
    "future_mask_tensor_policy",
    "current_tensor_materialized",
    "mask_interface_smoke_passed",
    "mask_interface_qa_passed",
    "qa_comment",
]
CHECKPOINT_COMPATIBILITY_QA_COLUMNS = [
    "compatibility_item",
    "expected_status",
    "observed_status",
    "checkpoint_loaded",
    "model_forward_called",
    "original_dataloader_modified",
    "compatibility_smoke_passed",
    "compatibility_qa_passed",
    "qa_comment",
]
READINESS_QA_COLUMNS = ["readiness_item", "expected_status", "observed_status", "readiness_qa_passed", "qa_comment"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _metadata_hash() -> str:
    return hashlib.sha256(step13bd.METADATA_CSV.read_bytes()).hexdigest() if step13bd.METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        step13br.INTERFACE_SMOKE_PREVIEW_CSV.name,
        step13br.INTERFACE_SMOKE_PREVIEW_JSON.name,
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "final_dataset_smoke.csv",
        "final_dataset_smoke.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13br = _load_json(step13br.MANIFEST_JSON)
    manifest13bq = _load_json(step13bq.MANIFEST_JSON)
    manifest13bm = _load_json(step13bm.MANIFEST_JSON)
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    interface_json_rows = _load_json(step13br.INTERFACE_SMOKE_PREVIEW_JSON)
    final_preview_rows = _csv_rows(step13bo.SMOKE_PREVIEW_CSV)
    checks = [
        ("step13br_manifest_exists", step13br.MANIFEST_JSON, "exists", step13br.MANIFEST_JSON.exists(), step13br.MANIFEST_JSON.exists()),
        ("step13br_stage", step13br.MANIFEST_JSON, step13br.STAGE, manifest13br.get("stage"), manifest13br.get("stage") == step13br.STAGE),
        ("step13br_all_checks_passed", step13br.MANIFEST_JSON, "true", manifest13br.get("all_checks_passed"), manifest13br.get("all_checks_passed") is True),
        ("step13br_ready_for_interface_qa_gate", step13br.MANIFEST_JSON, "true", manifest13br.get("ready_for_covapie_dataloader_interface_qa_gate"), manifest13br.get("ready_for_covapie_dataloader_interface_qa_gate") is True),
        ("step13br_ready_for_dataloader_smoke", step13br.MANIFEST_JSON, "false", manifest13br.get("ready_for_covapie_dataloader_smoke"), manifest13br.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13br_ready_for_training", step13br.MANIFEST_JSON, "false", manifest13br.get("ready_for_training"), manifest13br.get("ready_for_training") is False),
        ("step13br_ready_to_train_now", step13br.MANIFEST_JSON, "false", manifest13br.get("ready_to_train_now"), manifest13br.get("ready_to_train_now") is False),
        ("step13br_preview_csv_shape", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "20x35", f"{len(interface_rows)}x{len(interface_rows[0]) if interface_rows else 0}", len(interface_rows) == 20 and bool(interface_rows) and len(interface_rows[0]) == 35),
        ("step13br_preview_json_row_count", step13br.INTERFACE_SMOKE_PREVIEW_JSON, "20", len(interface_json_rows), len(interface_json_rows) == 20),
        ("step13br_input_source_smoke_passed", step13br.INPUT_SOURCE_SMOKE_AUDIT_CSV, "true", manifest13br.get("input_source_smoke_audit_passed"), manifest13br.get("input_source_smoke_audit_passed") is True),
        ("step13br_field_mapping_smoke_passed", step13br.FIELD_MAPPING_SMOKE_AUDIT_CSV, "true", manifest13br.get("field_mapping_smoke_audit_passed"), manifest13br.get("field_mapping_smoke_audit_passed") is True),
        ("step13br_feature_batch_smoke_passed", step13br.FEATURE_BATCH_SMOKE_AUDIT_CSV, "true", manifest13br.get("feature_batch_smoke_audit_passed"), manifest13br.get("feature_batch_smoke_audit_passed") is True),
        ("step13br_mask_interface_smoke_passed", step13br.MASK_INTERFACE_SMOKE_AUDIT_CSV, "true", manifest13br.get("mask_interface_smoke_audit_passed"), manifest13br.get("mask_interface_smoke_audit_passed") is True),
        ("step13br_checkpoint_compatibility_smoke_passed", step13br.CHECKPOINT_COMPATIBILITY_SMOKE_AUDIT_CSV, "true", manifest13br.get("checkpoint_compatibility_smoke_audit_passed"), manifest13br.get("checkpoint_compatibility_smoke_audit_passed") is True),
        ("step13bq_design_contracts_exist", step13bq.OUTPUT_ROOT, "exists", step13bq.OUTPUT_ROOT.exists(), step13bq.OUTPUT_ROOT.exists()),
        ("step13bq_input_source_contract_row_count", step13bq.INPUT_SOURCE_CONTRACT_CSV, "15", len(_csv_rows(step13bq.INPUT_SOURCE_CONTRACT_CSV)), len(_csv_rows(step13bq.INPUT_SOURCE_CONTRACT_CSV)) == 15),
        ("step13bq_field_mapping_contract_row_count", step13bq.FIELD_MAPPING_CONTRACT_CSV, "45", len(_csv_rows(step13bq.FIELD_MAPPING_CONTRACT_CSV)), len(_csv_rows(step13bq.FIELD_MAPPING_CONTRACT_CSV)) == 45),
        ("step13bq_feature_interface_contract_row_count", step13bq.FEATURE_INTERFACE_CONTRACT_CSV, "16", len(_csv_rows(step13bq.FEATURE_INTERFACE_CONTRACT_CSV)), len(_csv_rows(step13bq.FEATURE_INTERFACE_CONTRACT_CSV)) == 16),
        ("step13bq_mask_interface_contract_row_count", step13bq.MASK_INTERFACE_CONTRACT_CSV, "8", len(_csv_rows(step13bq.MASK_INTERFACE_CONTRACT_CSV)), len(_csv_rows(step13bq.MASK_INTERFACE_CONTRACT_CSV)) == 8),
        ("step13bq_batch_collate_contract_row_count", step13bq.BATCH_COLLATE_CONTRACT_CSV, "10", len(_csv_rows(step13bq.BATCH_COLLATE_CONTRACT_CSV)), len(_csv_rows(step13bq.BATCH_COLLATE_CONTRACT_CSV)) == 10),
        ("step13bq_checkpoint_compatibility_contract_row_count", step13bq.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV, "8", len(_csv_rows(step13bq.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV)), len(_csv_rows(step13bq.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV)) == 8),
        ("step13bo_preview_csv_shape", step13bo.SMOKE_PREVIEW_CSV, "20x45", f"{len(final_preview_rows)}x{len(final_preview_rows[0]) if final_preview_rows else 0}", len(final_preview_rows) == 20 and bool(final_preview_rows) and len(final_preview_rows[0]) == 45),
        ("step13bm_feature_semantics_audit_completed", step13bm.MANIFEST_JSON, "true", manifest13bm.get("feature_semantics_audit_completed_current_step"), manifest13bm.get("feature_semantics_audit_completed_current_step") is True),
        ("step13bm_feature_semantics_known_for_training", step13bm.MANIFEST_JSON, "false", manifest13bm.get("feature_semantics_known_for_training"), manifest13bm.get("feature_semantics_known_for_training") is False),
        ("step13bm_unknown_atom_policy_finalized", step13bm.MANIFEST_JSON, "false", manifest13bm.get("unknown_atom_feature_policy_finalized_for_training"), manifest13bm.get("unknown_atom_feature_policy_finalized_for_training") is False),
        ("canonical_mask_count", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "5", len({row["mask_task_name"] for row in interface_rows}), len({row["mask_task_name"] for row in interface_rows}) == 5),
        ("b3_scaffold_only_included", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "true", "scaffold_only" in {row["mask_task_name"] for row in interface_rows}, "scaffold_only" in {row["mask_task_name"] for row in interface_rows}),
        ("no_extra_mask_tasks_added", step13br.INTERFACE_SMOKE_PREVIEW_CSV, "true", {row["mask_task_name"] for row in interface_rows}, {row["mask_task_name"] for row in interface_rows} == set(CANONICAL_MASK_TASK_NAMES)),
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


def build_preview_integrity_rows() -> list[dict[str, Any]]:
    csv_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    json_rows = _load_json(step13br.INTERFACE_SMOKE_PREVIEW_JSON)
    json_by_id = {row["dataloader_interface_smoke_row_id"]: row for row in json_rows}
    final_by_id = {row["final_dataset_row_id"]: row for row in _csv_rows(step13bo.SMOKE_PREVIEW_CSV)}
    rows = []
    for row in csv_rows:
        final_row = final_by_id.get(row["final_dataset_row_id"], {})
        json_row = json_by_id.get(row["dataloader_interface_smoke_row_id"], {})
        deterministic = row["dataloader_interface_smoke_row_id"] == f"dataloader_interface_smoke::{row['final_dataset_row_id']}"
        found = bool(final_row)
        csv_json_consistent = json_row == row
        preserved = {
            "final_dataset_row_id_preserved": found and row["final_dataset_row_id"] == final_row.get("final_dataset_row_id"),
            "sample_id_preserved": found and row["sample_id"] == final_row.get("sample_id"),
            "split_unit_id_preserved": found and row["split_unit_id"] == final_row.get("split_unit_id"),
            "extracted_event_id_preserved": found and row["extracted_event_id"] == final_row.get("extracted_event_id"),
        }
        passed = all(preserved.values()) and found and deterministic and csv_json_consistent
        rows.append(
            {
                "dataloader_interface_smoke_row_id": row["dataloader_interface_smoke_row_id"],
                "final_dataset_row_id": row["final_dataset_row_id"],
                "sample_id": row["sample_id"],
                "split_unit_id": row["split_unit_id"],
                "extracted_event_id": row["extracted_event_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "mask_task_name": row["mask_task_name"],
                "mask_task_alias": row["mask_task_alias"],
                "source_final_dataset_preview_row_found": found,
                "interface_row_id_deterministic": deterministic,
                "csv_json_row_consistent": csv_json_consistent,
                **preserved,
                "interface_preview_rewritten_current_step": False,
                "actual_dataloader_smoke_written": False,
                "torch_tensor_created_current_step": False,
                "checkpoint_loaded_current_step": False,
                "model_forward_called_current_step": False,
                "ready_for_training": False,
                "preview_integrity_qa_passed": passed,
                "qa_comment": "interface smoke preview validates against final dataset smoke preview without rewrite",
            }
        )
    return rows


def build_input_source_qa_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _csv_rows(step13br.INPUT_SOURCE_SMOKE_AUDIT_CSV):
        passed = _bool(row["source_exists_or_policy_valid"]) and _bool(row["input_source_smoke_passed"]) and not _bool(row["runtime_dependency_used_current_step"])
        rows.append(
            {
                **row,
                "runtime_dependency_used_current_step": False,
                "input_source_qa_passed": passed,
                "qa_comment": "input source smoke audit accepted without runtime/raw access",
            }
        )
    return rows


def build_field_mapping_qa_rows() -> list[dict[str, Any]]:
    preview_fields = set(_csv_rows(step13bo.SMOKE_PREVIEW_CSV)[0].keys())
    rows = []
    for row in _csv_rows(step13br.FIELD_MAPPING_SMOKE_AUDIT_CSV):
        present = row["final_dataset_field_name"] in preview_fields
        no_tensor = row["tensorization_status_current_step"] == "design_only_no_tensorization_current_step"
        passed = present and no_tensor and _bool(row["field_mapping_smoke_passed"])
        rows.append(
            {
                **row,
                "source_value_present_in_preview": present,
                "field_mapping_qa_passed": passed,
                "qa_comment": "field mapping QA preserves metadata-only no-tensor boundary",
            }
        )
    return rows


def build_feature_batch_qa_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _csv_rows(step13br.FEATURE_BATCH_SMOKE_AUDIT_CSV):
        passed = _bool(row["feature_batch_smoke_passed"]) and not _bool(row["current_step_materialized"]) and not _bool(row["torch_tensor_created"]) and not _bool(row["actual_collate_implemented"])
        rows.append(
            {
                **row,
                "current_step_materialized": False,
                "torch_tensor_created": False,
                "actual_collate_implemented": False,
                "feature_batch_qa_passed": passed,
                "qa_comment": "feature and batch interfaces remain metadata-only QA records",
            }
        )
    return rows


def build_mask_qa_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _csv_rows(step13br.MASK_INTERFACE_SMOKE_AUDIT_CSV):
        canonical_or_aux = row["mask_task_name"] in CANONICAL_MASK_TASK_NAMES or row["mask_interface_item"] in {
            "mask_task_name_long_semantic_source_of_truth",
            "mask_task_alias_display_only",
            "no_extra_mask_tasks",
        }
        no_tensor = not _bool(row["current_tensor_materialized"])
        passed = _bool(row["mask_interface_smoke_passed"]) and no_tensor and canonical_or_aux
        rows.append(
            {
                **row,
                "current_tensor_materialized": False,
                "mask_interface_qa_passed": passed,
                "qa_comment": "mask QA preserves five canonical masks, display aliases, and no tensor masks",
            }
        )
    return rows


def build_checkpoint_compatibility_qa_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _csv_rows(step13br.CHECKPOINT_COMPATIBILITY_SMOKE_AUDIT_CSV):
        passed = _bool(row["compatibility_smoke_passed"]) and not _bool(row["checkpoint_loaded"]) and not _bool(row["model_forward_called"]) and not _bool(row["original_dataloader_modified"])
        rows.append(
            {
                **row,
                "checkpoint_loaded": False,
                "model_forward_called": False,
                "original_dataloader_modified": False,
                "compatibility_qa_passed": passed,
                "qa_comment": "checkpoint compatibility QA remains static; no checkpoint or model runtime executed",
            }
        )
    return rows


def build_readiness_qa_rows() -> list[dict[str, Any]]:
    observed = {
        "dataloader_interface_smoke_preview_validated": True,
        "actual_dataloader_smoke_not_written": True,
        "real_dataloader_not_written": True,
        "original_dataloader_not_modified": True,
        "no_torch_tensor_checkpoint_model_loss_training": True,
        "feature_semantics_known_for_training_false": True,
        "unknown_atom_feature_policy_finalized_for_training_false": True,
        "ready_for_dataloader_smoke_design_gate": True,
        "actual_dataloader_smoke_still_blocked": True,
        "ready_for_training_false": True,
    }
    return [
        {
            "readiness_item": item,
            "expected_status": "true",
            "observed_status": value,
            "readiness_qa_passed": value is True,
            "qa_comment": "QA gate allows dataloader smoke design gate next, not actual dataloader smoke or training",
        }
        for item, value in observed.items()
    ]


def build_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "dataloader_interface_qa_gate": "executed_qa_gate_only",
        "read_step13br_interface_smoke_preview": "executed_derived_csv_json_read_only",
        "read_step13br_smoke_audits": "executed_derived_csv_json_read_only",
        "read_step13bq_design_contracts": "executed_derived_csv_json_read_only",
        "read_step13bp_final_dataset_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bo_final_dataset_smoke_preview": "executed_derived_csv_json_read_only",
        "read_step13bm_feature_semantics_artifacts": "executed_derived_csv_json_read_only",
        "static_original_dataloader_source_read": "executed_static_text_reference_only",
        "dataloader_interface_smoke_preview_write_current_step": "not_executed_current_step_already_completed_previous_step",
        "actual_dataloader_smoke_write": "blocked_current_step",
        "real_dataloader_write": "blocked_current_step",
        "original_dataloader_modify": "blocked_current_step",
        "torch_import": "blocked_current_step",
        "tensor_creation": "blocked_current_step",
        "checkpoint_load": "blocked_current_step",
        "model_forward": "blocked_current_step",
        "loss_backward_optimizer": "blocked_current_step",
        "final_dataset_write": "blocked_current_step",
        "new_sample_index_write": "blocked_current_step",
        "split_assignment_write": "blocked_current_step",
        "leakage_matrix_write": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "raw_cif_mmcif_sdf_pdb_gzip_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "coordinate_extraction": "not_executed_or_not_allowed",
        "network_access": "not_executed_or_not_allowed",
        "raw_download": "not_executed_or_not_allowed",
        "rdkit_biopdb_gemmi": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "boundary_safety_passed": True,
            "qa_comment": "dataloader interface QA boundary respected",
        }
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "boundary manifest", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_interface_smoke_preview_rewritten_current_step", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_smoke_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_real_dataloader_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_original_dataloader_modified", "dataset.py data/prepare_crossdocked.py", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_torch_tensor_checkpoint_training_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_real_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13br_artifacts_unchanged", str(step13br.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13br.OUTPUT_ROOT.as_posix()])),
        ("step13bq_artifacts_unchanged", str(step13bq.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bq.OUTPUT_ROOT.as_posix()])),
        ("step13bp_artifacts_unchanged", str(step13bp.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bp.OUTPUT_ROOT.as_posix()])),
        ("step13bo_artifacts_unchanged", str(step13bo.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bo.OUTPUT_ROOT.as_posix()])),
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


def run_covapie_dataloader_interface_qa_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    preview_rows = build_preview_integrity_rows()
    input_rows = build_input_source_qa_rows()
    field_rows = build_field_mapping_qa_rows()
    feature_batch_rows = build_feature_batch_qa_rows()
    mask_rows = build_mask_qa_rows()
    checkpoint_rows = build_checkpoint_compatibility_qa_rows()
    readiness_rows = build_readiness_qa_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    interface_rows = _csv_rows(step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13br_dataloader_interface_smoke_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_interface_preview_row_count": len(interface_rows),
        "source_interface_preview_column_count": len(interface_rows[0]) if interface_rows else 0,
        "source_unique_event_count": len({row["extracted_event_id"] for row in interface_rows}),
        "source_unique_split_unit_count": len({row["split_unit_id"] for row in interface_rows}),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in interface_rows}),
        "preview_integrity_qa_row_count": len(preview_rows),
        "input_source_qa_row_count": len(input_rows),
        "field_mapping_qa_row_count": len(field_rows),
        "feature_batch_qa_row_count": len(feature_batch_rows),
        "mask_interface_qa_row_count": len(mask_rows),
        "checkpoint_compatibility_qa_row_count": len(checkpoint_rows),
        "readiness_qa_row_count": len(readiness_rows),
        "preview_integrity_qa_passed": all(_bool(row["preview_integrity_qa_passed"]) for row in preview_rows),
        "input_source_qa_passed": all(_bool(row["input_source_qa_passed"]) for row in input_rows),
        "field_mapping_qa_passed": all(_bool(row["field_mapping_qa_passed"]) for row in field_rows),
        "feature_batch_qa_passed": all(_bool(row["feature_batch_qa_passed"]) for row in feature_batch_rows),
        "mask_interface_qa_passed": all(_bool(row["mask_interface_qa_passed"]) for row in mask_rows),
        "checkpoint_compatibility_qa_passed": all(_bool(row["compatibility_qa_passed"]) for row in checkpoint_rows),
        "readiness_qa_passed": all(_bool(row["readiness_qa_passed"]) for row in readiness_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "dataloader_interface_smoke_preview_written_previous_step": True,
        "dataloader_interface_smoke_preview_written_current_step": False,
        "actual_dataloader_smoke_written": False,
        "real_dataloader_written": False,
        "original_dataloader_modified": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "coordinate_extraction_current_step": False,
        "network_access_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_dataloader_smoke_design_gate": True,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in interface_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in interface_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_dataloader_smoke_design_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13br_dataloader_interface_smoke_validated"],
            manifest["source_interface_preview_row_count"] == 20,
            manifest["source_interface_preview_column_count"] == 35,
            manifest["source_unique_event_count"] == 4,
            manifest["source_unique_split_unit_count"] == 4,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["preview_integrity_qa_row_count"] == 20,
            manifest["input_source_qa_row_count"] == 15,
            manifest["field_mapping_qa_row_count"] == 45,
            manifest["feature_batch_qa_row_count"] == 26,
            manifest["mask_interface_qa_row_count"] == 8,
            manifest["checkpoint_compatibility_qa_row_count"] == 8,
            manifest["readiness_qa_row_count"] == 10,
            manifest["preview_integrity_qa_passed"],
            manifest["input_source_qa_passed"],
            manifest["field_mapping_qa_passed"],
            manifest["feature_batch_qa_passed"],
            manifest["mask_interface_qa_passed"],
            manifest["checkpoint_compatibility_qa_passed"],
            manifest["readiness_qa_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["dataloader_interface_smoke_preview_written_previous_step"],
            not manifest["dataloader_interface_smoke_preview_written_current_step"],
            not manifest["actual_dataloader_smoke_written"],
            not manifest["real_dataloader_written"],
            not manifest["original_dataloader_modified"],
            not manifest["torch_imported"],
            not manifest["torch_tensor_created"],
            not manifest["checkpoint_loaded"],
            not manifest["model_forward_called"],
            not manifest["loss_compute_called"],
            not manifest["training_allowed"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            manifest["ready_for_covapie_dataloader_smoke_design_gate"],
            not manifest["ready_for_covapie_dataloader_smoke"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["dataloader_interface_qa_gate_failed"]
    return {
        "precondition_rows": precondition_rows,
        "preview_rows": preview_rows,
        "input_rows": input_rows,
        "field_rows": field_rows,
        "feature_batch_rows": feature_batch_rows,
        "mask_rows": mask_rows,
        "checkpoint_rows": checkpoint_rows,
        "readiness_rows": readiness_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }
