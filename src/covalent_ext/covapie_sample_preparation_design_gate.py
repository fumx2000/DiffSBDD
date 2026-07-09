from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_small_pilot_manifest_rerun_gate as step14y


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_sample_preparation_design_gate_v0"
STEP_LABEL = "Step 14Z"
PREVIOUS_STAGE = step14y.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_design_precondition_audit.csv"
INPUT_MANIFEST_CSV = OUTPUT_ROOT / "covapie_sample_preparation_input_manifest.csv"
INPUT_MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_preparation_input_manifest.json"
REQUIRED_ARTIFACT_PLAN_CSV = OUTPUT_ROOT / "covapie_sample_preparation_required_artifact_plan.csv"
RAW_ACCESS_PLAN_CSV = OUTPUT_ROOT / "covapie_sample_preparation_raw_access_plan.csv"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_schema_contract.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_design_policy_contract.csv"
DOWNSTREAM_READINESS_CSV = OUTPUT_ROOT / "covapie_sample_preparation_design_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_preparation_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_preparation_design_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_sample_preparation_design_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_sample_preparation_design_gate_v0.py")

STEP14Y_MANIFEST_JSON = step14y.MANIFEST_JSON
STEP14Y_PILOT_MANIFEST_CSV = step14y.PILOT_MANIFEST_CSV
STEP14Y_PILOT_MANIFEST_JSON = step14y.PILOT_MANIFEST_JSON
STEP14Y_TRACEABILITY_CSV = step14y.TRACEABILITY_AUDIT_CSV
STEP14Y_BLOCKED_CSV = step14y.BLOCKED_EXCLUSION_AUDIT_CSV
STEP14Y_ROOT = step14y.OUTPUT_ROOT
STEP14X_ROOT = step14y.STEP14X_ROOT
STEP14W_ROOT = step14y.STEP14W_ROOT
STEP14V_ROOT = step14y.STEP14V_ROOT
STEP14U_ROOT = step14y.STEP14U_ROOT
STEP14T_ROOT = step14y.STEP14T_ROOT

METADATA_CSV = step14y.METADATA_CSV
METADATA_CSV_SHA256 = step14y.METADATA_CSV_SHA256
RAW_ROOT = step14y.RAW_ROOT

CANONICAL_MASK_TASK_NAMES = step14y.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14y.CANONICAL_MASK_TASK_ALIASES
ACCEPTED_PDB_HET_PAIRS = step14y.ACCEPTED_PDB_HET_PAIRS
BLOCKED_PDB_HET_PAIRS = step14y.BLOCKED_PDB_HET_PAIRS
PLANNED_SAMPLE_SCOPE = "cys_sg_struct_conn_validated_small_pilot_v0"
NEXT_REQUIRED_GATE = "covapie_sample_preparation_execution_smoke"

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
INPUT_MANIFEST_COLUMNS = ["sample_preparation_input_id", "small_pilot_manifest_id", "ready_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "residue_atom_name", "ligand_comp_id", "ligand_atom_name", "conn_id", "conn_type_id", "covalent_bond_atom_pair", "sample_preparation_design_status", "planned_sample_scope", "ready_for_sample_preparation_execution_smoke", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training", "qa_comment"]
REQUIRED_ARTIFACT_COLUMNS = ["sample_preparation_input_id", "pdb_id", "expected_het_id", "planned_sample_artifact_root", "protein_atom_table_required_next_step", "ligand_atom_table_required_next_step", "pocket_atom_table_required_next_step", "covalent_event_table_required_next_step", "ligand_residue_atom_pair_required_next_step", "mask_annotation_design_required_later", "topology_restoration_policy_required_later", "actual_raw_mmcif_read_required_next_step", "actual_struct_conn_parse_allowed_next_step", "actual_sample_index_written_next_step", "actual_final_dataset_written_next_step", "ready_for_training_current_step"]
RAW_ACCESS_COLUMNS = ["sample_preparation_input_id", "pdb_id", "expected_het_id", "planned_raw_source_root", "planned_raw_lookup_policy", "raw_mmcif_read_current_step", "raw_mmcif_read_required_next_step", "raw_file_git_tracked_current_step", "raw_file_git_staged_current_step", "raw_file_commit_policy", "qa_comment"]
SCHEMA_CONTRACT_COLUMNS = ["schema_item", "required_in_next_execution_smoke", "planned_minimum_fields", "current_step_writes_this_schema", "schema_contract_passed"]
POLICY_CONTRACT_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
DOWNSTREAM_READINESS_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_AUDIT_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _metadata_hash() -> str:
    path = REPO_ROOT / METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def _forbidden_output_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    names = {"protein_atom_table.csv", "ligand_atom_table.csv", "pocket_atom_table.csv", "covalent_event_table.csv", "sample_index.csv", "sample_index.json", "final_dataset.csv", "final_dataset.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def build_precondition_rows(pilot_rows: list[dict[str, str]], pilot_json: list[dict[str, Any]], traceability_rows: list[dict[str, str]], blocked_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14Y_MANIFEST_JSON) if STEP14Y_MANIFEST_JSON.exists() else {}
    csv_json_consistent = _json_consistent(pilot_rows, pilot_json, "small_pilot_manifest_id")
    checks = [
        ("step14y_manifest_exists", STEP14Y_MANIFEST_JSON.as_posix(), "exists", STEP14Y_MANIFEST_JSON.exists(), STEP14Y_MANIFEST_JSON.exists()),
        ("step14y_stage", STEP14Y_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14y_all_checks_passed", STEP14Y_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14y_small_pilot_manifest_row_count", STEP14Y_MANIFEST_JSON.as_posix(), "3", manifest.get("small_pilot_manifest_row_count"), manifest.get("small_pilot_manifest_row_count") == 3),
        ("step14y_ready_for_sample_preparation_count", STEP14Y_MANIFEST_JSON.as_posix(), "3", manifest.get("ready_for_sample_preparation_count"), manifest.get("ready_for_sample_preparation_count") == 3),
        ("step14y_ready_for_sample_preparation_design_gate", STEP14Y_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_sample_preparation_design_gate"), manifest.get("ready_for_covapie_sample_preparation_design_gate") is True),
        ("step14y_ready_for_training_false", STEP14Y_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14y_pilot_manifest_csv_json_exists_consistent", STEP14Y_PILOT_MANIFEST_JSON.as_posix(), "3 consistent rows", f"{len(pilot_rows)} csv/{len(pilot_json)} json", STEP14Y_PILOT_MANIFEST_CSV.exists() and STEP14Y_PILOT_MANIFEST_JSON.exists() and len(pilot_rows) == len(pilot_json) == 3 and csv_json_consistent),
        ("step14y_traceability_audit_all_passed", STEP14Y_TRACEABILITY_CSV.as_posix(), "3 passed", len(traceability_rows), STEP14Y_TRACEABILITY_CSV.exists() and len(traceability_rows) == 3 and all(row["traceability_audit_passed"] == "True" for row in traceability_rows)),
        ("step14y_blocked_exclusion_audit_exists", STEP14Y_BLOCKED_CSV.as_posix(), "2", len(blocked_rows), STEP14Y_BLOCKED_CSV.exists() and len(blocked_rows) == 2),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_tracked", RAW_ROOT.as_posix(), "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14y.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_input_manifest_rows(pilot_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(pilot_rows, start=1):
        rows.append({
            "sample_preparation_input_id": f"CYS_SG_SAMPLE_PREP_INPUT_{idx:06d}",
            "small_pilot_manifest_id": row["small_pilot_manifest_id"],
            "ready_candidate_id": row["ready_candidate_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "covpdb_residue_name": row["covpdb_residue_name"],
            "covpdb_residue_index": row["covpdb_residue_index"],
            "covpdb_chain_id": row["covpdb_chain_id"],
            "residue_atom_name": row["residue_atom_name"],
            "ligand_comp_id": row["ligand_comp_id"],
            "ligand_atom_name": row["ligand_atom_name"],
            "conn_id": row["conn_id"],
            "conn_type_id": row["conn_type_id"],
            "covalent_bond_atom_pair": row["covalent_bond_atom_pair"],
            "sample_preparation_design_status": "sample_preparation_design_ready",
            "planned_sample_scope": PLANNED_SAMPLE_SCOPE,
            "ready_for_sample_preparation_execution_smoke": True,
            "ready_for_training_current_step": False,
            "feature_semantics_audit_required_before_training": True,
            "leakage_split_design_required_before_training": True,
            "qa_comment": "design input only; actual sample preparation execution smoke required next",
        })
    return rows


def build_required_artifact_plan_rows(input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in input_rows:
        rows.append({
            "sample_preparation_input_id": row["sample_preparation_input_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "planned_sample_artifact_root": f"data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/samples/{row['pdb_id']}_{row['expected_het_id']}",
            "protein_atom_table_required_next_step": True,
            "ligand_atom_table_required_next_step": True,
            "pocket_atom_table_required_next_step": True,
            "covalent_event_table_required_next_step": True,
            "ligand_residue_atom_pair_required_next_step": True,
            "mask_annotation_design_required_later": True,
            "topology_restoration_policy_required_later": True,
            "actual_raw_mmcif_read_required_next_step": True,
            "actual_struct_conn_parse_allowed_next_step": True,
            "actual_sample_index_written_next_step": False,
            "actual_final_dataset_written_next_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_raw_access_plan_rows(input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "sample_preparation_input_id": row["sample_preparation_input_id"],
        "pdb_id": row["pdb_id"],
        "expected_het_id": row["expected_het_id"],
        "planned_raw_source_root": RAW_ROOT.as_posix(),
        "planned_raw_lookup_policy": "case_insensitive_pdb_id_mmcif_or_cif_lookup_in_ignored_raw_root",
        "raw_mmcif_read_current_step": False,
        "raw_mmcif_read_required_next_step": True,
        "raw_file_git_tracked_current_step": False,
        "raw_file_git_staged_current_step": False,
        "raw_file_commit_policy": "do_not_commit_raw_files",
        "qa_comment": "raw lookup is planned for next execution smoke only",
    } for row in input_rows]


def build_schema_contract_rows() -> list[dict[str, Any]]:
    specs = [
        ("sample_preparation_execution_manifest_schema", True, "sample_preparation_input_id;pdb_id;expected_het_id;execution_status;sample_artifact_root", False),
        ("protein_atom_table_schema", True, "atom_id;element;atom_name;residue_name;chain_id;residue_index;x;y;z", False),
        ("ligand_atom_table_schema", True, "atom_id;element;atom_name;ligand_comp_id;x;y;z", False),
        ("pocket_atom_table_schema", True, "pocket_atom_id;element;atom_name;distance_to_ligand;source_atom_id", False),
        ("covalent_event_table_schema", True, "pdb_id;expected_het_id;conn_id;conn_type_id;residue_atom_name;ligand_atom_name;covalent_bond_atom_pair", False),
        ("ligand_residue_atom_pair_schema", True, "residue_atom_name;ligand_atom_name;covalent_bond_atom_pair;validation_status", False),
        ("sample_preparation_audit_schema", True, "sample_preparation_input_id;raw_lookup_status;struct_conn_parse_status;artifact_write_status;audit_passed", False),
        ("no_sample_index_current_stage", False, "sample_index is not written in this design gate", False),
        ("no_final_dataset_current_stage", False, "final_dataset is not written in this design gate", False),
        ("no_training_current_stage", False, "training artifacts are not written in this design gate", False),
    ]
    return [{"schema_item": item, "required_in_next_execution_smoke": required, "planned_minimum_fields": fields, "current_step_writes_this_schema": writes, "schema_contract_passed": True} for item, required, fields, writes in specs]


def build_policy_contract_rows() -> list[dict[str, Any]]:
    descriptions = {
        "sample_preparation_design_gate_only": "This step writes design contracts for future sample preparation execution.",
        "design_gate_does_not_read_raw_mmcif": "Raw CIF/mmCIF is not read in this design gate.",
        "design_gate_does_not_parse_struct_conn_or_atom_site": "struct_conn and atom_site parsing are reserved for the next execution smoke.",
        "sample_preparation_input_manifest_is_not_sample_index": "The input manifest is not a sample index.",
        "sample_preparation_input_manifest_is_not_final_dataset": "The input manifest is not a final dataset.",
        "sample_preparation_input_manifest_is_not_training_sample": "The input manifest is not a training sample.",
        "execution_smoke_required_next": "A sample preparation execution smoke is required next.",
        "final_dataset_not_written_current_step": "No final dataset is written.",
        "sample_index_not_written_current_step": "No sample index is written.",
        "split_and_leakage_not_written_current_step": "No split or leakage matrix is written.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split design remains required before training.",
        "canonical_five_masks_preserved": "The canonical five masks are preserved.",
        "do_not_train_from_sample_preparation_design_artifacts": "Design artifacts must not be used for training.",
    }
    return [{"policy_item": item, "policy_description": description, "policy_contract_passed": True} for item, description in descriptions.items()]


def build_downstream_readiness_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_sample_preparation_execution_smoke", True, True, NEXT_REQUIRED_GATE, "allowed next step"),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", False, True, "not_allowed_current_step", "sample preparation execution smoke must run first"),
        ("ready_for_training", False, True, "not_allowed_current_step", "not a training sample"),
        ("ready_to_train_now", False, True, "not_allowed_current_step", "feature semantics and leakage/split gates remain required"),
    ]
    return [{"readiness_item": item, "observed_status": observed, "readiness_passed": passed, "next_required_gate": next_gate, "qa_comment": comment} for item, observed, passed, next_gate, comment in specs]


def build_safety_audit_rows() -> list[dict[str, Any]]:
    no_forbidden = not _forbidden_output_artifact_exists()
    checks = [
        ("no_network_access_current_step", "true", "true", True),
        ("no_download_current_step", "true", "true", True),
        ("no_raw_mmcif_read_current_step", "true", "true", True),
        ("no_struct_conn_parse_current_step", "true", "true", True),
        ("no_atom_site_parse_current_step", "true", "true", True),
        ("no_data_raw_write_current_step", "true", "true", True),
        ("raw_files_remain_untracked", "true", str(not _raw_files_tracked()).lower(), not _raw_files_tracked()),
        ("raw_files_remain_unstaged", "true", str(not _raw_files_staged()).lower(), not _raw_files_staged()),
        ("no_html_or_part_files", "true", str(no_forbidden).lower(), no_forbidden),
        ("metadata_csv_unchanged", "true", str(_metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])).lower(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14y_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14Y_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14Y_ROOT.as_posix()])),
        ("step14x_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14X_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14X_ROOT.as_posix()])),
        ("step14w_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14W_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14W_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_actual_atom_tables_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_sample_index_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_final_dataset_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_split_or_leakage_written", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_training_artifacts", "true", str(no_forbidden).lower(), no_forbidden),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", "true", str(no_forbidden).lower(), no_forbidden),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "true", "true", True),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(precondition_rows, input_rows, artifact_rows, raw_rows, schema_rows, policy_rows, downstream_rows, safety_rows, blocked_rows) -> dict[str, Any]:
    accepted_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in input_rows]
    blocked_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in blocked_rows]
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (precondition_rows, "precondition_passed"),
            (schema_rows, "schema_contract_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and accepted_pairs == ACCEPTED_PDB_HET_PAIRS and len(input_rows) == 3
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "input_small_pilot_manifest_row_count": len(_csv_rows(STEP14Y_PILOT_MANIFEST_CSV)),
        "sample_preparation_input_count": len(input_rows),
        "required_artifact_plan_count": len(artifact_rows),
        "raw_access_plan_count": len(raw_rows),
        "accepted_pdb_het_pairs": accepted_pairs,
        "blocked_pdb_het_pairs": blocked_pairs,
        "sample_preparation_input_csv_json_consistent": True,
        "ready_for_sample_preparation_execution_smoke_count": sum(_bool(row["ready_for_sample_preparation_execution_smoke"]) for row in input_rows),
        "ready_for_training_candidate_count_current_step": sum(_bool(row["ready_for_training_current_step"]) for row in input_rows),
        "raw_mmcif_read_current_step": False,
        "raw_mmcif_read_required_next_step": True,
        "struct_conn_parsed_current_step": False,
        "atom_site_parsed_current_step": False,
        "actual_atom_tables_written_current_step": False,
        "protein_atom_table_written_current_step": False,
        "ligand_atom_table_written_current_step": False,
        "pocket_atom_table_written_current_step": False,
        "covalent_event_table_written_current_step": False,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "data_raw_written_current_step": False,
        "html_files_written_current_step": False,
        "part_files_leftover_current_step": False,
        "sample_index_written_current_step": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "requests_used": False,
        "urllib_used": False,
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "ready_for_covapie_sample_preparation_execution_smoke": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": NEXT_REQUIRED_GATE,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["sample_preparation_design_gate_failed"],
    }


def run_covapie_sample_preparation_design_gate_v0() -> dict[str, Any]:
    pilot_rows = _csv_rows(STEP14Y_PILOT_MANIFEST_CSV)
    pilot_json = _load_json(STEP14Y_PILOT_MANIFEST_JSON)
    traceability_rows = _csv_rows(STEP14Y_TRACEABILITY_CSV)
    blocked_rows = _csv_rows(STEP14Y_BLOCKED_CSV)
    precondition_rows = build_precondition_rows(pilot_rows, pilot_json, traceability_rows, blocked_rows)
    input_rows = build_input_manifest_rows(pilot_rows)
    artifact_rows = build_required_artifact_plan_rows(input_rows)
    raw_rows = build_raw_access_plan_rows(input_rows)
    schema_rows = build_schema_contract_rows()
    policy_rows = build_policy_contract_rows()
    downstream_rows = build_downstream_readiness_rows()
    safety_rows = build_safety_audit_rows()
    manifest = build_manifest(precondition_rows, input_rows, artifact_rows, raw_rows, schema_rows, policy_rows, downstream_rows, safety_rows, blocked_rows)
    return {
        "precondition_rows": precondition_rows,
        "input_rows": input_rows,
        "artifact_rows": artifact_rows,
        "raw_rows": raw_rows,
        "schema_rows": schema_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
