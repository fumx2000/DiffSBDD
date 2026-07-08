from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_candidate_allowlist_qa_gate as step13bc


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_batch_raw_read_extraction_design_gate_v0"
PREVIOUS_STAGE = "covapie_candidate_allowlist_qa_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13BC_ROOT = step13bc.OUTPUT_ROOT
STEP13BB_ROOT = step13bc.STEP13BB_ROOT
STEP13BA_ROOT = step13bc.STEP13BA_ROOT
STEP13BC_MANIFEST_JSON = step13bc.MANIFEST_JSON
STEP13BB_ALLOWLIST_CSV = step13bc.STEP13BB_ALLOWLIST_CSV
STEP13BB_ALLOWLIST_JSON = step13bc.STEP13BB_ALLOWLIST_JSON
STEP13BB_MANIFEST_JSON = step13bc.STEP13BB_MANIFEST_JSON
METADATA_CSV = step13bc.METADATA_CSV
METADATA_CSV_SHA256 = step13bc.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step13bc.RAW_STORAGE_ROOT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_precondition_audit.csv"
INPUT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_input_contract.csv"
RAW_FILE_PATH_CONTRACT_CSV = OUTPUT_ROOT / "covapie_batch_raw_file_path_contract.csv"
EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_extracted_event_schema_contract.csv"
EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_extracted_atom_table_schema_contract.csv"
SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_smoke_plan.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_batch_raw_read_extraction_design_gate_v0_summary.md")

EXPECTED_PAIRS = step13bc.EXPECTED_PAIRS
EXPECTED_ALLOWLIST_IDS = step13bc.EXPECTED_ALLOWLIST_IDS
CANONICAL_MASK_TASK_NAMES = step13bc.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bc.CANONICAL_MASK_TASK_ALIASES
FORBIDDEN_DERIVED_SUFFIXES = step13bc.FORBIDDEN_DERIVED_SUFFIXES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_COLUMNS = [
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "event_key_resolution_status",
    "source_allowlist_stage",
    "source_allowlist_row_index",
    "raw_read_required_next_step",
    "extraction_required_next_step",
    "current_step_raw_content_read",
    "current_step_extraction_executed",
    "input_contract_passed",
]
RAW_PATH_COLUMNS = [
    "pdb_id",
    "expected_raw_file_path",
    "expected_raw_file_suffix",
    "raw_file_path_exists",
    "raw_file_tracked_by_git",
    "raw_file_staged_by_git",
    "raw_file_content_read_current_step",
    "raw_file_policy",
    "future_raw_read_allowed_after_design_gate",
    "raw_file_path_contract_passed",
]
EVENT_SCHEMA_COLUMNS = [
    "extracted_event_field",
    "field_order",
    "field_description",
    "source_or_future_derivation",
    "materialized_current_step",
    "required_in_future_smoke",
    "schema_contract_passed",
]
ATOM_SCHEMA_COLUMNS = [
    "atom_table_role",
    "extracted_atom_field",
    "field_order",
    "field_description",
    "source_or_future_derivation",
    "materialized_current_step",
    "required_in_future_smoke",
    "schema_contract_passed",
]
PLAN_COLUMNS = ["planned_step", "planned_action", "allowed_inputs", "allowed_outputs", "blocked_outputs", "required_preconditions", "plan_passed"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "allowed_current_step", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

EVENT_FIELDS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "chain_id",
    "residue_name",
    "residue_index",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_bond_atom_pair",
    "raw_file_path",
    "raw_file_sha256",
    "mmcif_stage",
    "atom_site_rows_scanned",
    "struct_conn_rows_scanned",
    "residue_atom_found",
    "ligand_atom_found",
    "covalent_connection_found",
    "residue_atom_x",
    "residue_atom_y",
    "residue_atom_z",
    "ligand_atom_x",
    "ligand_atom_y",
    "ligand_atom_z",
    "covalent_bond_distance_angstrom",
    "extraction_status",
    "extraction_blocking_reason",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
    "ready_for_training",
]
ATOM_FIELDS = [
    "extracted_atom_id",
    "extracted_event_id",
    "allowlist_entry_id",
    "atom_table_role",
    "pdb_id",
    "chain_id",
    "residue_name",
    "residue_index",
    "het_code",
    "atom_name",
    "element",
    "formal_charge",
    "x",
    "y",
    "z",
    "occupancy",
    "b_factor",
    "altloc",
    "model_id",
    "source_raw_file_path",
    "extraction_status",
    "feature_semantics_audit_required_before_training",
    "ready_for_training",
]
FORBIDDEN_OUTPUT_NAMES = {
    "covapie_extracted_event_table.csv",
    "covapie_extracted_event_table.json",
    "covapie_extracted_protein_atom_table.csv",
    "covapie_extracted_ligand_atom_table.csv",
    "sample_index.csv",
    "sample_index.json",
    "final_dataset.csv",
    "final_dataset.json",
    "split_assignments.csv",
    "split_assignments.json",
    "leakage_matrix.csv",
    "leakage_matrix.json",
}


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
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _raw_file_tracked(path: Path) -> bool:
    return bool(_run_git(["ls-files", path.as_posix()]).stdout.strip())


def _raw_file_staged(path: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", path.as_posix()]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _forbidden_output_names_exist(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.name in FORBIDDEN_OUTPUT_NAMES for path in root.rglob("*")) if root.exists() else False


def _precondition_rows(manifest13bc: dict[str, Any], allowlist_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    checks = [
        ("step13bc_manifest_exists", STEP13BC_MANIFEST_JSON, "exists", STEP13BC_MANIFEST_JSON.exists(), STEP13BC_MANIFEST_JSON.exists()),
        ("step13bc_stage", STEP13BC_MANIFEST_JSON, PREVIOUS_STAGE, manifest13bc.get("stage"), manifest13bc.get("stage") == PREVIOUS_STAGE),
        ("step13bc_all_checks_passed", STEP13BC_MANIFEST_JSON, "true", manifest13bc.get("all_checks_passed"), manifest13bc.get("all_checks_passed") is True),
        ("step13bc_ready_for_design_gate", STEP13BC_MANIFEST_JSON, "true", manifest13bc.get("ready_for_covapie_batch_scale_raw_read_design_gate"), manifest13bc.get("ready_for_covapie_batch_scale_raw_read_design_gate") is True),
        ("step13bc_ready_for_raw_read_smoke", STEP13BC_MANIFEST_JSON, "false", manifest13bc.get("ready_for_covapie_batch_scale_raw_read_smoke"), manifest13bc.get("ready_for_covapie_batch_scale_raw_read_smoke") is False),
        ("step13bc_ready_for_training", STEP13BC_MANIFEST_JSON, "false", manifest13bc.get("ready_for_training"), manifest13bc.get("ready_for_training") is False),
        ("step13bb_allowlist_csv_exists", STEP13BB_ALLOWLIST_CSV, "exists", STEP13BB_ALLOWLIST_CSV.exists(), STEP13BB_ALLOWLIST_CSV.exists()),
        ("step13bb_allowlist_json_exists", STEP13BB_ALLOWLIST_JSON, "exists", STEP13BB_ALLOWLIST_JSON.exists(), STEP13BB_ALLOWLIST_JSON.exists()),
        ("step13bb_allowlist_row_count", STEP13BB_ALLOWLIST_CSV, "4", len(allowlist_rows), len(allowlist_rows) == 4),
        ("step13bb_allowlist_column_count", STEP13BB_ALLOWLIST_CSV, "25", len(allowlist_rows[0]) if allowlist_rows else 0, bool(allowlist_rows) and len(allowlist_rows[0]) == 25),
        ("metadata_csv_hash_unchanged", METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def _input_contract_rows(allowlist_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "allowlist_entry_id": row["allowlist_entry_id"],
            "candidate_metadata_id": row["candidate_metadata_id"],
            "pdb_id": row["pdb_id"],
            "het_code": row["het_code"],
            "chain_id": row["chain_id"],
            "residue_name": row["residue_name"],
            "residue_index": row["residue_index"],
            "residue_atom_name": row["residue_atom_name"],
            "ligand_atom_name": row["ligand_atom_name"],
            "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
            "event_key_resolution_status": row["event_key_resolution_status"],
            "source_allowlist_stage": step13bc.PREVIOUS_STAGE,
            "source_allowlist_row_index": index,
            "raw_read_required_next_step": True,
            "extraction_required_next_step": True,
            "current_step_raw_content_read": False,
            "current_step_extraction_executed": False,
            "input_contract_passed": (row["pdb_id"], row["het_code"]) in EXPECTED_PAIRS,
        }
        for index, row in enumerate(allowlist_rows, start=1)
    ]


def _raw_file_path_rows(allowlist_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in allowlist_rows:
        path = RAW_STORAGE_ROOT / f"{row['pdb_id']}.cif"
        tracked = _raw_file_tracked(path)
        staged = _raw_file_staged(path)
        passed = not tracked and not staged
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "expected_raw_file_path": path.as_posix(),
                "expected_raw_file_suffix": ".cif",
                "raw_file_path_exists": path.exists(),
                "raw_file_tracked_by_git": tracked,
                "raw_file_staged_by_git": staged,
                "raw_file_content_read_current_step": False,
                "raw_file_policy": "raw_file_external_untracked_input_for_future_smoke",
                "future_raw_read_allowed_after_design_gate": True,
                "raw_file_path_contract_passed": passed,
            }
        )
    return rows


def _event_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "extracted_event_field": field,
            "field_order": index,
            "field_description": f"future extracted event field {field}",
            "source_or_future_derivation": "future_raw_mmcif_extraction_smoke",
            "materialized_current_step": False,
            "required_in_future_smoke": True,
            "schema_contract_passed": True,
        }
        for index, field in enumerate(EVENT_FIELDS, start=1)
    ]


def _atom_schema_rows() -> list[dict[str, Any]]:
    rows = []
    for role in ["protein_pocket_atom", "ligand_atom"]:
        for index, field in enumerate(ATOM_FIELDS, start=1):
            rows.append(
                {
                    "atom_table_role": role,
                    "extracted_atom_field": field,
                    "field_order": index,
                    "field_description": f"future {role} field {field}",
                    "source_or_future_derivation": "future_raw_mmcif_atom_site_extraction_smoke",
                    "materialized_current_step": False,
                    "required_in_future_smoke": True,
                    "schema_contract_passed": True,
                }
            )
    return rows


def _plan_rows() -> list[dict[str, Any]]:
    plan = [
        ("raw_file_content_read", "ready_next_after_design_gate", "allowlist_qa_gate;raw_file_path_contract", "raw_content_read_in_future_smoke_only", "training;sample_index;final_dataset", "Step13BD design gate passed"),
        ("mmcif_parse", "future_smoke_operations", "raw_file_content", "parsed_mmcif_metadata_for_smoke", "training", "raw_file_content_read"),
        ("atom_site_scan", "future_smoke_operations", "parsed_mmcif", "atom_site_lookup_results", "training", "mmcif_parse"),
        ("struct_conn_scan", "future_smoke_operations", "parsed_mmcif", "struct_conn_lookup_results", "training", "mmcif_parse"),
        ("residue_atom_lookup", "future_smoke_operations", "atom_site_rows", "residue_atom_found_status", "training", "atom_site_scan"),
        ("ligand_atom_lookup", "future_smoke_operations", "atom_site_rows", "ligand_atom_found_status", "training", "atom_site_scan"),
        ("covalent_connection_validation", "future_smoke_operations", "struct_conn_rows", "covalent_connection_found_status", "training", "struct_conn_scan"),
        ("coordinate_extraction", "future_smoke_operations", "atom_lookup_results", "coordinate_fields", "training", "residue_and_ligand_atoms_found"),
        ("extracted_event_table_write", "future_smoke_operations", "extraction_results", "covapie_extracted_event_table.csv", "sample_index;final_dataset;training", "coordinate_extraction"),
        ("extracted_atom_tables_write", "future_smoke_operations", "atom_site_lookup_results", "future_atom_tables", "sample_index;final_dataset;training", "coordinate_extraction"),
        ("extraction_qa_gate", "qa_after_smoke", "extraction_smoke_outputs", "qa_artifacts", "training", "extraction_smoke_passed"),
        ("sample_index_design_gate", "blocked_until_extraction_qa", "extraction_qa_outputs", "future_sample_index_design", "training", "extraction_qa_passed"),
        ("training", "blocked", "none_current_step", "none", "forward;loss;backward;optimizer;trainer.fit", "feature_semantics_audit;leakage_split_design;dataset_gates"),
    ]
    return [
        {
            "planned_step": step,
            "planned_action": action,
            "allowed_inputs": inputs,
            "allowed_outputs": outputs,
            "blocked_outputs": blocked,
            "required_preconditions": preconditions,
            "plan_passed": True,
        }
        for step, action, inputs, outputs, blocked, preconditions in plan
    ]


def _boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "batch_raw_read_extraction_design_gate": ("executed_design_gate_only", True),
        "raw_file_path_check": ("path_exists_git_status_only_no_content_read", True),
        "raw_file_content_read": ("blocked_current_design_gate", False),
        "mmcif_parse": ("blocked_current_design_gate", False),
        "atom_site_scan": ("blocked_current_design_gate", False),
        "struct_conn_scan": ("blocked_current_design_gate", False),
        "coordinate_extraction": ("blocked_current_design_gate", False),
        "extracted_event_table_write": ("blocked_current_design_gate", False),
        "extracted_atom_table_write": ("blocked_current_design_gate", False),
        "sample_index": ("blocked_current_design_gate", False),
        "final_dataset": ("blocked_current_design_gate", False),
        "split_assignments": ("blocked_current_design_gate", False),
        "leakage_matrix": ("blocked_current_design_gate", False),
        "training": ("blocked_current_design_gate", False),
        "network_access": ("not_executed_or_not_allowed", False),
        "rdkit_biopdb_gemmi": ("not_executed_or_not_allowed", False),
        "torch_model_training": ("not_executed_or_not_allowed", False),
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "allowed_current_step": allowed,
            "boundary_safety_passed": True,
            "qa_comment": "boundary_respected",
        }
        for item, (status, allowed) in statuses.items()
    ]


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("derived_output_no_raw_suffix_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists()),
        ("no_extracted_event_table_written", "forbidden output name scan", "false", not any((OUTPUT_ROOT / name).exists() for name in ["covapie_extracted_event_table.csv", "covapie_extracted_event_table.json"])),
        ("no_extracted_atom_table_written", "forbidden output name scan", "false", not any((OUTPUT_ROOT / name).exists() for name in ["covapie_extracted_protein_atom_table.csv", "covapie_extracted_ligand_atom_table.csv"])),
        ("no_sample_final_split_leakage_artifacts", "forbidden output name scan", "false", not _forbidden_output_names_exist()),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bc_artifacts_unchanged", "git diff step13bc root", "empty", not _path_diff_exists([str(STEP13BC_ROOT)])),
        ("step13bb_artifacts_unchanged", "git diff step13bb root", "empty", not _path_diff_exists([str(STEP13BB_ROOT)])),
        ("protected_source_diff_empty", "git diff equivariant_diffusion/ lightning_modules.py", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "git_safety_audit_passed": status is True,
            "blocking_reasons": "" if status is True else item,
        }
        for item, command, required, status in checks
    ]


def run_covapie_batch_raw_read_extraction_design_gate_v0() -> dict[str, Any]:
    manifest13bc = _load_json(STEP13BC_MANIFEST_JSON)
    allowlist_rows = _csv_rows(STEP13BB_ALLOWLIST_CSV)
    precondition_rows = _precondition_rows(manifest13bc, allowlist_rows)
    input_rows = _input_contract_rows(allowlist_rows)
    raw_path_rows = _raw_file_path_rows(allowlist_rows)
    event_schema_rows = _event_schema_rows()
    atom_schema_rows = _atom_schema_rows()
    plan_rows = _plan_rows()
    boundary_rows = _boundary_rows()
    git_safety_rows = _git_safety_rows()

    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "input": len(input_rows) == 4 and _all_true(input_rows, "input_contract_passed"),
        "raw_path": len(raw_path_rows) == 4 and _all_true(raw_path_rows, "raw_file_path_contract_passed"),
        "event_schema": len(event_schema_rows) == 31 and _all_true(event_schema_rows, "schema_contract_passed"),
        "atom_schema": len(atom_schema_rows) == 46 and _all_true(atom_schema_rows, "schema_contract_passed"),
        "plan": len(plan_rows) == 13 and _all_true(plan_rows, "plan_passed"),
        "boundary": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bc_candidate_allowlist_qa_gate_validated": qa_checks["precondition"],
        "source_allowlist_row_count": len(allowlist_rows),
        "source_allowlist_column_count": len(allowlist_rows[0]) if allowlist_rows else 0,
        "batch_raw_read_input_contract_row_count": len(input_rows),
        "raw_file_path_contract_row_count": len(raw_path_rows),
        "raw_file_path_exists_count": sum(1 for row in raw_path_rows if row["raw_file_path_exists"]),
        "extracted_event_schema_field_count": len(event_schema_rows),
        "extracted_atom_schema_row_count": len(atom_schema_rows),
        "raw_read_extraction_smoke_plan_row_count": len(plan_rows),
        "precondition_audit_passed": qa_checks["precondition"],
        "input_contract_passed": qa_checks["input"],
        "raw_file_path_contract_passed": qa_checks["raw_path"],
        "extracted_event_schema_contract_passed": qa_checks["event_schema"],
        "extracted_atom_table_schema_contract_passed": qa_checks["atom_schema"],
        "raw_read_extraction_smoke_plan_passed": qa_checks["plan"],
        "boundary_safety_passed": qa_checks["boundary"],
        "git_safety_passed": qa_checks["git_safety"],
        "candidate_allowlist_materialized_previous_step": True,
        "candidate_allowlist_materialized_current_step": False,
        "raw_file_path_checked_current_step": True,
        "raw_file_content_read_current_step": False,
        "raw_read_current_step": False,
        "raw_download_current_step": False,
        "mmcif_parse_current_step": False,
        "atom_site_scan_current_step": False,
        "struct_conn_scan_current_step": False,
        "coordinate_extraction_current_step": False,
        "extracted_event_table_written": False,
        "extracted_atom_table_written": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_file_created": False,
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
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
        "ready_for_covapie_batch_raw_read_extraction_smoke": True,
        "ready_for_covapie_extraction_qa_gate": False,
        "ready_for_sample_index_design_gate": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13bc.CANONICAL_MASK_TASK_NAMES,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_batch_raw_read_extraction_smoke",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "precondition_rows": precondition_rows,
        "input_rows": input_rows,
        "raw_path_rows": raw_path_rows,
        "event_schema_rows": event_schema_rows,
        "atom_schema_rows": atom_schema_rows,
        "plan_rows": plan_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }
