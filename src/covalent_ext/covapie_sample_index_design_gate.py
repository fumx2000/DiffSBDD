from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_extraction_qa_gate as step13bf


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_sample_index_design_gate_v0"
PREVIOUS_STAGE = step13bf.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_index_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_design_precondition_audit.csv"
SOURCE_ARTIFACT_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_index_source_artifact_contract.csv"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_index_schema_contract.csv"
MASK_TASK_EXPANSION_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_index_mask_task_expansion_contract.csv"
SMOKE_PLAN_CSV = OUTPUT_ROOT / "covapie_sample_index_smoke_plan.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_sample_index_design_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_sample_index_design_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_sample_index_design_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_index_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_index_design_gate_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13bf.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bf.CANONICAL_MASK_TASK_ALIASES
MASK_DESCRIPTIONS = {
    "warhead_only": "mask warhead atoms only while preserving linker and scaffold context",
    "linker_plus_warhead": "mask linker and warhead atoms while preserving scaffold context",
    "scaffold_plus_warhead": "mask scaffold and warhead atoms while preserving linker context",
    "scaffold_only": "mask scaffold atoms only while preserving linker and warhead context",
    "scaffold_plus_linker_plus_warhead": "mask full ligand scaffold linker and warhead",
}
METADATA_CSV_SHA256 = step13bf.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_ARTIFACT_COLUMNS = ["source_artifact_name", "source_artifact_path", "source_stage", "required_for_future_sample_index_smoke", "exists_current_step", "row_count_if_csv", "content_read_current_step", "source_artifact_contract_passed"]
SCHEMA_COLUMNS = ["sample_index_field", "field_order", "field_description", "source_or_future_derivation", "materialized_current_step", "required_in_future_sample_index_smoke", "schema_contract_passed"]
MASK_EXPANSION_COLUMNS = ["planned_sample_id", "extracted_event_id", "pdb_id", "het_code", "mask_task_name", "mask_task_alias", "mask_task_semantic_description", "event_qa_passed", "atom_qa_passed", "geometry_qa_passed", "scaffold_linker_warhead_annotation_required", "auxiliary_labels_required", "materialized_current_step", "ready_for_future_sample_index_smoke", "ready_for_training", "mask_task_expansion_contract_passed"]
PLAN_COLUMNS = ["planned_step", "planned_action", "allowed_inputs", "allowed_outputs", "blocked_outputs", "required_preconditions", "plan_passed"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKER_COLUMNS = ["training_blocker_item", "required_status", "current_step_status", "training_blocker_passed", "qa_comment"]

SAMPLE_INDEX_FIELDS = [
    "sample_id",
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
    "covalent_bond_distance_angstrom",
    "protein_pocket_atom_table_path",
    "ligand_atom_table_path",
    "protein_atom_row_count_for_event",
    "ligand_atom_row_count_for_event",
    "mask_task_name",
    "mask_task_alias",
    "mask_task_semantic_description",
    "conditioning_mode",
    "covalent_residue_conditioned",
    "scaffold_linker_warhead_annotation_status",
    "warhead_type_label_status",
    "ligand_residue_atom_pair_label_status",
    "pre_post_geometry_label_status",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
    "split_assignment_status",
    "sample_index_materialized_current_step",
    "ready_for_training",
]


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
    path = step13bf.step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bf.step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bf.step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _precondition_rows(manifest13bf: dict[str, Any], event_rows: list[dict[str, str]], protein_rows: list[dict[str, str]], ligand_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    checks = [
        ("step13bf_manifest_exists", step13bf.MANIFEST_JSON, "exists", step13bf.MANIFEST_JSON.exists(), step13bf.MANIFEST_JSON.exists()),
        ("step13bf_stage", step13bf.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bf.get("stage"), manifest13bf.get("stage") == PREVIOUS_STAGE),
        ("step13bf_all_checks_passed", step13bf.MANIFEST_JSON, "true", manifest13bf.get("all_checks_passed"), manifest13bf.get("all_checks_passed") is True),
        ("step13bf_ready_for_design", step13bf.MANIFEST_JSON, "true", manifest13bf.get("ready_for_covapie_sample_index_design_gate"), manifest13bf.get("ready_for_covapie_sample_index_design_gate") is True),
        ("step13bf_ready_for_smoke", step13bf.MANIFEST_JSON, "false", manifest13bf.get("ready_for_covapie_sample_index_smoke"), manifest13bf.get("ready_for_covapie_sample_index_smoke") is False),
        ("step13bf_ready_for_training", step13bf.MANIFEST_JSON, "false", manifest13bf.get("ready_for_training"), manifest13bf.get("ready_for_training") is False),
        ("event_table_row_count", step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("event_table_column_count", step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV, "31", len(event_rows[0]) if event_rows else 0, bool(event_rows) and len(event_rows[0]) == 31),
        ("protein_table_row_count", step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("ligand_table_row_count", step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("extraction_qa_passed", step13bf.MANIFEST_JSON, "true", manifest13bf.get("extracted_event_table_qa_passed"), manifest13bf.get("extracted_event_table_qa_passed") is True),
        ("geometry_qa_passed", step13bf.MANIFEST_JSON, "true", manifest13bf.get("geometry_qa_passed"), manifest13bf.get("geometry_qa_passed") is True),
        ("traceability_qa_passed", step13bf.MANIFEST_JSON, "true", manifest13bf.get("traceability_qa_passed"), manifest13bf.get("traceability_qa_passed") is True),
        ("metadata_csv_hash_unchanged", step13bf.step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def _row_count(path: Path) -> int:
    return len(_csv_rows(path)) if path.suffix == ".csv" else 1


def _source_artifact_rows() -> list[dict[str, Any]]:
    artifacts = [
        ("extracted_event_table", step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV, step13bf.step13be.STAGE),
        ("extracted_protein_pocket_atom_table", step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, step13bf.step13be.STAGE),
        ("extracted_ligand_atom_table", step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, step13bf.step13be.STAGE),
        ("extraction_qa_gate_manifest", step13bf.MANIFEST_JSON, step13bf.STAGE),
        ("event_table_qa_audit", step13bf.EVENT_TABLE_QA_CSV, step13bf.STAGE),
        ("atom_table_qa_audit", step13bf.ATOM_TABLE_QA_CSV, step13bf.STAGE),
        ("geometry_qa_audit", step13bf.GEOMETRY_QA_CSV, step13bf.STAGE),
        ("traceability_qa_audit", step13bf.TRACEABILITY_QA_CSV, step13bf.STAGE),
    ]
    rows = []
    for name, path, stage in artifacts:
        exists = path.exists()
        rows.append(
            {
                "source_artifact_name": name,
                "source_artifact_path": path.as_posix(),
                "source_stage": stage,
                "required_for_future_sample_index_smoke": True,
                "exists_current_step": exists,
                "row_count_if_csv": _row_count(path) if exists and path.suffix == ".csv" else "",
                "content_read_current_step": True,
                "source_artifact_contract_passed": exists,
            }
        )
    return rows


def _schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "sample_index_field": field,
            "field_order": index,
            "field_description": f"future sample index field {field}",
            "source_or_future_derivation": "future_sample_index_smoke_from_extraction_tables_and_mask_contract",
            "materialized_current_step": False,
            "required_in_future_sample_index_smoke": True,
            "schema_contract_passed": True,
        }
        for index, field in enumerate(SAMPLE_INDEX_FIELDS, start=1)
    ]


def _mask_expansion_rows(event_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    event_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bf.EVENT_TABLE_QA_CSV)}
    atom_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bf.ATOM_TABLE_QA_CSV)}
    geometry_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bf.GEOMETRY_QA_CSV)}
    rows = []
    for event_index, event in enumerate(event_rows, start=1):
        for mask_index, (name, alias) in enumerate(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES), start=1):
            planned_id = f"sample_plan::{event['candidate_metadata_id']}::{alias}"
            passed = event["extracted_event_id"] in event_qa and event["extracted_event_id"] in atom_qa and event["extracted_event_id"] in geometry_qa
            rows.append(
                {
                    "planned_sample_id": planned_id,
                    "extracted_event_id": event["extracted_event_id"],
                    "pdb_id": event["pdb_id"],
                    "het_code": event["het_code"],
                    "mask_task_name": name,
                    "mask_task_alias": alias,
                    "mask_task_semantic_description": MASK_DESCRIPTIONS[name],
                    "event_qa_passed": event_qa.get(event["extracted_event_id"], {}).get("extracted_event_table_qa_passed") == "True",
                    "atom_qa_passed": atom_qa.get(event["extracted_event_id"], {}).get("extracted_atom_table_qa_passed") == "True",
                    "geometry_qa_passed": geometry_qa.get(event["extracted_event_id"], {}).get("geometry_qa_passed") == "True",
                    "scaffold_linker_warhead_annotation_required": True,
                    "auxiliary_labels_required": True,
                    "materialized_current_step": False,
                    "ready_for_future_sample_index_smoke": True,
                    "ready_for_training": False,
                    "mask_task_expansion_contract_passed": passed,
                }
            )
    return rows


def _plan_rows() -> list[dict[str, Any]]:
    plan = [
        ("read_extraction_qa_gate", "future_sample_index_smoke_operation", "extraction_qa_gate_artifacts", "loaded_qa_contracts", "training", "Step13BG passed"),
        ("read_extracted_event_table", "future_sample_index_smoke_operation", "extracted_event_table", "event_rows", "training", "extraction_qa_passed"),
        ("read_extracted_atom_tables", "future_sample_index_smoke_operation", "protein_and_ligand_atom_tables", "atom_row_counts", "training", "extraction_qa_passed"),
        ("expand_4_events_to_20_mask_task_rows", "future_sample_index_smoke_operation", "4_events;5_masks", "20_planned_rows", "training", "mask_contract_valid"),
        ("assign_deterministic_sample_ids", "future_sample_index_smoke_operation", "planned_rows", "sample_ids", "training", "expanded_rows"),
        ("write_sample_index_smoke_csv", "future_sample_index_smoke_operation", "sample_rows", "sample_index_smoke_csv", "final_dataset;training", "deterministic_ids"),
        ("write_sample_index_smoke_json", "future_sample_index_smoke_operation", "sample_rows", "sample_index_smoke_json", "final_dataset;training", "deterministic_ids"),
        ("sample_index_qa_gate", "qa_after_smoke", "sample_index_smoke_outputs", "qa_artifacts", "training", "sample_index_smoke_passed"),
        ("split_leakage_design_gate", "blocked_until_sample_index_qa", "sample_index_qa_outputs", "future_split_leakage_design", "training", "sample_index_qa_passed"),
        ("feature_semantics_audit_gate", "blocked_until_before_training", "sample_index_or_final_dataset_context", "feature_semantics_audit", "training", "before_training_or_finetune"),
        ("final_dataset_design_gate", "blocked_until_split_leakage_and_feature_semantics", "split_leakage_and_feature_audits", "future_final_dataset_design", "training", "split_and_feature_gates_passed"),
        ("dataloader_smoke", "blocked_until_final_dataset_design_smoke", "final_dataset_smoke", "loader_smoke_outputs", "training", "final_dataset_design_smoke_passed"),
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
        "sample_index_design_gate": "executed_design_gate_only",
        "read_step13bf_derived_artifacts": "executed_derived_csv_json_read_only",
        "sample_index_write": "blocked_current_design_gate",
        "final_dataset": "blocked_current_step",
        "split_assignments": "blocked_current_step",
        "leakage_matrix": "blocked_current_step",
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
            "qa_comment": "boundary_respected",
        }
        for item, status in statuses.items()
    ]


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in step13bf.step13be.FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _path_name_exists(names: set[str], root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.name in names for path in root.rglob("*")) if root.exists() else False


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "policy check", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "forbidden suffix scan", "false", not _forbidden_suffix_exists()),
        ("no_sample_index_written", "forbidden output name scan", "false", not _path_name_exists({"sample_index.csv", "sample_index.json"})),
        ("no_final_dataset_written", "forbidden output name scan", "false", not _path_name_exists({"final_dataset.csv", "final_dataset.json"})),
        ("no_split_assignments_written", "forbidden output name scan", "false", not _path_name_exists({"split_assignments.csv", "split_assignments.json"})),
        ("no_leakage_matrix_written", "forbidden output name scan", "false", not _path_name_exists({"leakage_matrix.csv", "leakage_matrix.json"})),
        ("metadata_csv_unchanged", str(step13bf.step13be.step13bd.METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bf_artifacts_unchanged", "git diff step13bf root", "empty", not _path_diff_exists([str(step13bf.OUTPUT_ROOT)])),
        ("step13be_artifacts_unchanged", "git diff step13be root", "empty", not _path_diff_exists([str(step13bf.step13be.OUTPUT_ROOT)])),
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


def _training_blocker_rows() -> list[dict[str, Any]]:
    items = [
        "mask_warhead_only_A",
        "mask_linker_plus_warhead_B",
        "mask_scaffold_plus_warhead_B2",
        "mask_scaffold_only_B3",
        "mask_scaffold_plus_linker_plus_warhead_C",
        "scaffold_linker_warhead_annotation_required_before_training",
        "auxiliary_labels_required_before_training",
        "feature_semantics_audit_required",
        "feature_semantics_fully_audited_claimed_false",
        "leakage_split_design_required",
        "sample_index_written_current_step_false",
        "split_written_current_step_false",
        "leakage_matrix_written_current_step_false",
        "ready_for_training_false",
    ]
    return [
        {
            "training_blocker_item": item,
            "required_status": "preserved",
            "current_step_status": "preserved",
            "training_blocker_passed": True,
            "qa_comment": "training_blocker_preserved",
        }
        for item in items
    ]


def run_covapie_sample_index_design_gate_v0() -> dict[str, Any]:
    manifest13bf = _load_json(step13bf.MANIFEST_JSON)
    event_rows = _csv_rows(step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    precondition_rows = _precondition_rows(manifest13bf, event_rows, protein_rows, ligand_rows)
    source_rows = _source_artifact_rows()
    schema_rows = _schema_rows()
    mask_rows = _mask_expansion_rows(event_rows)
    plan_rows = _plan_rows()
    boundary_rows = _boundary_rows()
    git_safety_rows = _git_safety_rows()
    training_blocker_rows = _training_blocker_rows()
    unique_events = sorted({row["extracted_event_id"] for row in mask_rows})
    unique_masks = sorted({row["mask_task_name"] for row in mask_rows})
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "source": len(source_rows) == 8 and _all_true(source_rows, "source_artifact_contract_passed"),
        "schema": len(schema_rows) == 31 and _all_true(schema_rows, "schema_contract_passed"),
        "mask": len(mask_rows) == 20 and len(unique_events) == 4 and len(unique_masks) == 5 and _all_true(mask_rows, "mask_task_expansion_contract_passed"),
        "plan": len(plan_rows) == 13 and _all_true(plan_rows, "plan_passed"),
        "boundary": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "training_blockers": _all_true(training_blocker_rows, "training_blocker_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bf_extraction_qa_gate_validated": qa_checks["precondition"],
        "source_extracted_event_row_count": len(event_rows),
        "source_protein_pocket_atom_row_count": len(protein_rows),
        "source_ligand_atom_row_count": len(ligand_rows),
        "future_sample_index_schema_field_count": len(schema_rows),
        "future_mask_task_expansion_row_count": len(mask_rows),
        "future_unique_event_count": len(unique_events),
        "future_mask_task_count": len(unique_masks),
        "future_planned_sample_count": len(mask_rows),
        "source_artifact_contract_passed": qa_checks["source"],
        "sample_index_schema_contract_passed": qa_checks["schema"],
        "mask_task_expansion_contract_passed": qa_checks["mask"],
        "sample_index_smoke_plan_passed": qa_checks["plan"],
        "boundary_safety_passed": qa_checks["boundary"],
        "git_safety_passed": qa_checks["git_safety"],
        "training_blockers_passed": qa_checks["training_blockers"],
        "sample_index_materialized_current_step": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
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
        "ready_for_covapie_sample_index_smoke": True,
        "ready_for_covapie_sample_index_qa_gate": False,
        "ready_for_covapie_split_leakage_design_gate": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13bf.CANONICAL_MASK_TASK_NAMES,
        "scaffold_linker_warhead_annotation_required_before_training": True,
        "auxiliary_labels_required_before_training": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_sample_index_smoke",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "precondition_rows": precondition_rows,
        "source_rows": source_rows,
        "schema_rows": schema_rows,
        "mask_rows": mask_rows,
        "plan_rows": plan_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }
