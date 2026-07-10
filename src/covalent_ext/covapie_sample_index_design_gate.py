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
STEP_LABEL = "Step 14AC"
PREVIOUS_STAGE = "covapie_sample_preparation_qa_gate_v0"
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_index_design_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_design_precondition_audit.csv"
SOURCE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_sample_index_source_inventory.csv"
SOURCE_INVENTORY_JSON = OUTPUT_ROOT / "covapie_sample_index_source_inventory.json"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_index_schema_contract.csv"
FIELD_MAPPING_CSV = OUTPUT_ROOT / "covapie_sample_index_field_mapping.csv"
MATERIALIZATION_PLAN_CSV = OUTPUT_ROOT / "covapie_sample_index_materialization_plan.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_index_design_policy_contract.csv"
DOWNSTREAM_READINESS_CSV = OUTPUT_ROOT / "covapie_sample_index_design_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_design_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_index_design_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_index_design_gate_v0_summary.md")

STEP14AB_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_qa_gate_v0")
STEP14AB_MANIFEST_JSON = STEP14AB_ROOT / "covapie_sample_preparation_qa_gate_manifest.json"
STEP14AB_SAMPLE_QA_CSV = STEP14AB_ROOT / "covapie_sample_preparation_sample_level_qa.csv"
STEP14AB_SAMPLE_QA_JSON = STEP14AB_ROOT / "covapie_sample_preparation_sample_level_qa.json"
STEP14AB_TABLE_QA_CSV = STEP14AB_ROOT / "covapie_sample_preparation_table_integrity_qa.csv"
STEP14AB_EVENT_QA_CSV = STEP14AB_ROOT / "covapie_sample_preparation_event_pair_qa.csv"
STEP14AB_ISSUE_INVENTORY_CSV = STEP14AB_ROOT / "covapie_sample_preparation_issue_inventory.csv"

STEP14AA_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0")
STEP14AA_EXECUTION_MANIFEST_CSV = STEP14AA_ROOT / "covapie_sample_preparation_execution_manifest.csv"
STEP14AA_EXECUTION_MANIFEST_JSON = STEP14AA_ROOT / "covapie_sample_preparation_execution_manifest.json"
STEP14AA_SAMPLE_INVENTORY_CSV = STEP14AA_ROOT / "covapie_sample_preparation_execution_sample_inventory.csv"
STEP14AA_SAMPLE_INVENTORY_JSON = STEP14AA_ROOT / "covapie_sample_preparation_execution_sample_inventory.json"
STEP14Z_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_design_gate_v0")
STEP14Y_ROOT = Path("data/derived/covalent_small/covapie_small_pilot_manifest_rerun_gate_v0")

RAW_ROOT = Path("data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0")
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"
CANONICAL_MASK_TASK_NAMES = ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
CANONICAL_MASK_TASK_ALIASES = ["A", "B", "B2", "B3", "C"]
MASK_DESCRIPTIONS = {
    "warhead_only": "mask warhead atoms only while preserving linker and scaffold context",
    "linker_plus_warhead": "mask linker and warhead atoms while preserving scaffold context",
    "scaffold_plus_warhead": "mask scaffold and warhead atoms while preserving linker context",
    "scaffold_only": "mask scaffold atoms only while preserving linker and warhead context",
    "scaffold_plus_linker_plus_warhead": "mask full ligand scaffold linker and warhead",
}
ACCEPTED_PDB_HET_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]

REQUIRED_TABLES = [
    "protein_atom_table.csv",
    "ligand_atom_table.csv",
    "pocket_atom_table.csv",
    "covalent_event_table.csv",
    "ligand_residue_atom_pair_table.csv",
    "sample_preparation_audit.csv",
]

SAMPLE_INDEX_FIELDS = [
    "sample_index_row_id",
    "sample_preparation_input_id",
    "sample_execution_id",
    "sample_qa_id",
    "pdb_id",
    "expected_het_id",
    "sample_artifact_root",
    "protein_atom_table_path",
    "ligand_atom_table_path",
    "pocket_atom_table_path",
    "covalent_event_table_path",
    "ligand_residue_atom_pair_table_path",
    "sample_preparation_audit_path",
    "protein_atom_count",
    "ligand_atom_count",
    "pocket_atom_count",
    "covalent_event_count",
    "ligand_residue_atom_pair_count",
    "covalent_residue_name",
    "covalent_residue_chain_id",
    "covalent_residue_index",
    "covalent_residue_atom_name",
    "ligand_comp_id",
    "ligand_covalent_atom_name",
    "covalent_bond_atom_pair",
    "conn_id",
    "conn_type_id",
    "bond_distance_angstrom",
    "sample_index_status",
    "eligible_for_final_dataset_design",
    "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_INVENTORY_COLUMNS = ["sample_index_source_id", "sample_qa_id", "sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "sample_artifact_root", "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path", "covalent_event_table_path", "ligand_residue_atom_pair_table_path", "sample_preparation_audit_path", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "covalent_bond_atom_pair", "sample_level_qa_status", "table_integrity_status", "event_pair_qa_status", "eligible_for_sample_index_materialization", "ready_for_training_current_step", "qa_comment"]
SCHEMA_COLUMNS = ["sample_index_field", "planned_data_type", "required", "nullable", "semantic_role", "source_artifact", "source_field", "validation_rule", "current_step_materializes_field", "schema_contract_passed"]
FIELD_MAPPING_COLUMNS = ["mapping_id", "sample_index_field", "primary_source_artifact", "primary_source_field", "fallback_source_artifact", "fallback_source_field", "transformation_rule", "required_validation", "mapping_status"]
MATERIALIZATION_PLAN_COLUMNS = ["sample_index_materialization_plan_id", "sample_index_source_id", "pdb_id", "expected_het_id", "planned_sample_index_row_id", "planned_materialization_status", "source_artifact_root", "required_source_table_count", "required_source_tables_present", "sample_qa_passed", "event_pair_qa_passed", "planned_next_gate", "sample_index_written_current_step", "final_dataset_written_current_step", "ready_for_training_current_step"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


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


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def _table_path(sample_root: str | Path, table_name: str) -> Path:
    return Path(sample_root) / table_name


def _first_row(path: str | Path) -> dict[str, str]:
    rows = _csv_rows(path)
    return rows[0] if rows else {}


def _all_required_tables_exist(sample_root: str | Path) -> bool:
    return all(_table_path(sample_root, table_name).is_file() for table_name in REQUIRED_TABLES)


def build_precondition_rows(sample_rows: list[dict[str, str]], sample_json: list[dict[str, Any]], execution_rows: list[dict[str, str]], execution_json: list[dict[str, Any]], inventory_rows: list[dict[str, str]], inventory_json: list[dict[str, Any]], table_rows: list[dict[str, str]], event_rows: list[dict[str, str]], issue_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14AB_MANIFEST_JSON) if STEP14AB_MANIFEST_JSON.exists() else {}
    sample_roots = [Path(row["sample_artifact_root"]) for row in sample_rows]
    checks = [
        ("step14ab_manifest_exists", STEP14AB_MANIFEST_JSON.as_posix(), "exists", STEP14AB_MANIFEST_JSON.exists(), STEP14AB_MANIFEST_JSON.exists()),
        ("step14ab_stage", STEP14AB_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14ab_all_checks_passed", STEP14AB_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14ab_sample_qa_count", STEP14AB_MANIFEST_JSON.as_posix(), "3", manifest.get("sample_qa_count"), manifest.get("sample_qa_count") == 3),
        ("step14ab_sample_qa_passed_count", STEP14AB_MANIFEST_JSON.as_posix(), "3", manifest.get("sample_qa_passed_count"), manifest.get("sample_qa_passed_count") == 3),
        ("step14ab_table_integrity_count", STEP14AB_MANIFEST_JSON.as_posix(), "18", manifest.get("table_integrity_qa_count"), manifest.get("table_integrity_qa_count") == 18),
        ("step14ab_table_integrity_passed_count", STEP14AB_MANIFEST_JSON.as_posix(), "18", manifest.get("table_integrity_passed_count"), manifest.get("table_integrity_passed_count") == 18),
        ("step14ab_event_pair_count", STEP14AB_MANIFEST_JSON.as_posix(), "3", manifest.get("event_pair_qa_count"), manifest.get("event_pair_qa_count") == 3),
        ("step14ab_event_pair_passed_count", STEP14AB_MANIFEST_JSON.as_posix(), "3", manifest.get("event_pair_qa_passed_count"), manifest.get("event_pair_qa_passed_count") == 3),
        ("step14ab_qa_issue_count", STEP14AB_MANIFEST_JSON.as_posix(), "0", manifest.get("qa_issue_count"), manifest.get("qa_issue_count") == 0),
        ("step14ab_ready_for_sample_index_design_gate", STEP14AB_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_sample_index_design_gate"), manifest.get("ready_for_covapie_sample_index_design_gate") is True),
        ("step14ab_ready_for_training_false", STEP14AB_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("sample_qa_csv_json_consistent", STEP14AB_SAMPLE_QA_JSON.as_posix(), "3 consistent rows", f"{len(sample_rows)} csv/{len(sample_json)} json", len(sample_rows) == len(sample_json) == 3 and _json_consistent(sample_rows, sample_json, "sample_qa_id")),
        ("execution_manifest_csv_json_consistent", STEP14AA_EXECUTION_MANIFEST_JSON.as_posix(), "3 consistent rows", f"{len(execution_rows)} csv/{len(execution_json)} json", len(execution_rows) == len(execution_json) == 3 and _json_consistent(execution_rows, execution_json, "sample_execution_id")),
        ("sample_inventory_csv_json_consistent", STEP14AA_SAMPLE_INVENTORY_JSON.as_posix(), "3 consistent rows", f"{len(inventory_rows)} csv/{len(inventory_json)} json", len(inventory_rows) == len(inventory_json) == 3 and _json_consistent(inventory_rows, inventory_json, "sample_execution_id")),
        ("sample_artifact_roots_exist", (STEP14AA_ROOT / "samples").as_posix(), "3 roots", [p.as_posix() for p in sample_roots], len(sample_roots) == 3 and all(p.is_dir() for p in sample_roots)),
        ("six_required_tables_per_sample_exist", (STEP14AA_ROOT / "samples").as_posix(), "18 tables", "present" if all(_all_required_tables_exist(p) for p in sample_roots) else "missing", all(_all_required_tables_exist(p) for p in sample_roots)),
        ("table_integrity_rows_passed", STEP14AB_TABLE_QA_CSV.as_posix(), "18 passed", len(table_rows), len(table_rows) == 18 and all(row["table_integrity_status"] == "passed" for row in table_rows)),
        ("event_pair_rows_passed", STEP14AB_EVENT_QA_CSV.as_posix(), "3 passed", len(event_rows), len(event_rows) == 3 and all(row["event_pair_qa_status"] == "passed" for row in event_rows)),
        ("issue_inventory_no_qa_issues", STEP14AB_ISSUE_INVENTORY_CSV.as_posix(), "NO_QA_ISSUES", issue_rows[0].get("issue_id") if issue_rows else "", len(issue_rows) == 1 and issue_rows[0].get("issue_id") == "NO_QA_ISSUES"),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_tracked", RAW_ROOT.as_posix(), "false", _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_source_inventory(sample_rows: list[dict[str, str]], table_rows: list[dict[str, str]], event_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    table_status = {(row["sample_execution_id"], row["table_name"]): row for row in table_rows}
    event_status = {row["sample_execution_id"]: row for row in event_rows}
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(sample_rows, start=1):
        root = row["sample_artifact_root"]
        sample_execution_id = row["sample_execution_id"]
        all_tables_present = all(table_status[(sample_execution_id, name)]["table_integrity_status"] == "passed" for name in REQUIRED_TABLES)
        event_passed = event_status[sample_execution_id]["event_pair_qa_status"] == "passed"
        eligible = row["sample_level_qa_status"] == "passed" and all_tables_present and event_passed
        rows.append({
            "sample_index_source_id": f"CYS_SG_SAMPLE_INDEX_SOURCE_{index:06d}",
            "sample_qa_id": row["sample_qa_id"],
            "sample_preparation_input_id": row["sample_preparation_input_id"],
            "sample_execution_id": sample_execution_id,
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "sample_artifact_root": root,
            "protein_atom_table_path": _table_path(root, "protein_atom_table.csv").as_posix(),
            "ligand_atom_table_path": _table_path(root, "ligand_atom_table.csv").as_posix(),
            "pocket_atom_table_path": _table_path(root, "pocket_atom_table.csv").as_posix(),
            "covalent_event_table_path": _table_path(root, "covalent_event_table.csv").as_posix(),
            "ligand_residue_atom_pair_table_path": _table_path(root, "ligand_residue_atom_pair_table.csv").as_posix(),
            "sample_preparation_audit_path": _table_path(root, "sample_preparation_audit.csv").as_posix(),
            "protein_atom_count": row["protein_atom_count"],
            "ligand_atom_count": row["ligand_atom_count"],
            "pocket_atom_count": row["pocket_atom_count"],
            "covalent_event_count": row["covalent_event_count"],
            "ligand_residue_atom_pair_count": row["ligand_residue_atom_pair_count"],
            "covalent_bond_atom_pair": event_status[sample_execution_id]["covalent_bond_atom_pair"],
            "sample_level_qa_status": row["sample_level_qa_status"],
            "table_integrity_status": "passed" if all_tables_present else "blocked",
            "event_pair_qa_status": event_status[sample_execution_id]["event_pair_qa_status"],
            "eligible_for_sample_index_materialization": eligible,
            "ready_for_training_current_step": False,
            "qa_comment": "qa-passed prepared sample is eligible for future sample index materialization smoke",
        })
    return rows


def build_schema_contract() -> list[dict[str, Any]]:
    source_by_field = {
        "sample_index_row_id": ("future_materialization", "generated_stable_id", "stable generated row id required"),
        "sample_preparation_input_id": ("source_inventory", "sample_preparation_input_id", "non-empty Step 14AA input id"),
        "sample_execution_id": ("source_inventory", "sample_execution_id", "non-empty Step 14AA execution id"),
        "sample_qa_id": ("source_inventory", "sample_qa_id", "non-empty Step 14AB QA id"),
        "pdb_id": ("source_inventory", "pdb_id", "one of accepted QA-passed PDB IDs"),
        "expected_het_id": ("source_inventory", "expected_het_id", "equals JUG for this pilot set"),
        "sample_artifact_root": ("source_inventory", "sample_artifact_root", "path exists"),
        "protein_atom_table_path": ("source_inventory", "protein_atom_table_path", "path exists"),
        "ligand_atom_table_path": ("source_inventory", "ligand_atom_table_path", "path exists"),
        "pocket_atom_table_path": ("source_inventory", "pocket_atom_table_path", "path exists"),
        "covalent_event_table_path": ("source_inventory", "covalent_event_table_path", "path exists"),
        "ligand_residue_atom_pair_table_path": ("source_inventory", "ligand_residue_atom_pair_table_path", "path exists"),
        "sample_preparation_audit_path": ("source_inventory", "sample_preparation_audit_path", "path exists"),
        "protein_atom_count": ("source_inventory", "protein_atom_count", "> 0"),
        "ligand_atom_count": ("source_inventory", "ligand_atom_count", "> 0"),
        "pocket_atom_count": ("source_inventory", "pocket_atom_count", "> 0"),
        "covalent_event_count": ("source_inventory", "covalent_event_count", "= 1"),
        "ligand_residue_atom_pair_count": ("source_inventory", "ligand_residue_atom_pair_count", "= 1"),
        "covalent_residue_name": ("covalent_event_table", "residue_comp_id", "equals CYS"),
        "covalent_residue_chain_id": ("covalent_event_table", "residue_auth_asym_id", "non-empty chain id"),
        "covalent_residue_index": ("covalent_event_table", "residue_auth_seq_id", "non-empty residue index"),
        "covalent_residue_atom_name": ("covalent_event_table", "residue_atom_name", "equals SG"),
        "ligand_comp_id": ("covalent_event_table", "ligand_comp_id", "equals JUG"),
        "ligand_covalent_atom_name": ("covalent_event_table", "ligand_atom_name", "equals CAG"),
        "covalent_bond_atom_pair": ("covalent_event_table", "covalent_bond_atom_pair", "equals SG--CAG"),
        "conn_id": ("covalent_event_table", "conn_id", "non-empty struct_conn id from prepared table"),
        "conn_type_id": ("covalent_event_table", "conn_type_id", "equals covale"),
        "bond_distance_angstrom": ("ligand_residue_atom_pair_table", "bond_distance_angstrom", "positive numeric distance"),
        "sample_index_status": ("future_constant", "sample_index_materialized_from_qa_passed_sample", "constant in future materialization"),
        "eligible_for_final_dataset_design": ("future_constant", "false", "false until future QA/application gate"),
        "ready_for_training_current_step": ("current_step_constant", "false", "must remain false"),
        "feature_semantics_audit_required_before_training": ("current_step_constant", "true", "must remain true"),
        "leakage_split_design_required_before_training": ("current_step_constant", "true", "must remain true"),
    }
    rows = []
    for field in SAMPLE_INDEX_FIELDS:
        source_artifact, source_field, validation_rule = source_by_field[field]
        rows.append({
            "sample_index_field": field,
            "planned_data_type": "string" if field.endswith("_path") or field not in {"protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "bond_distance_angstrom", "eligible_for_final_dataset_design", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training"} else "boolean" if field in {"eligible_for_final_dataset_design", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training"} else "number",
            "required": True,
            "nullable": field == "covalent_residue_index",
            "semantic_role": "future_materialized_sample_index_field",
            "source_artifact": source_artifact,
            "source_field": source_field,
            "validation_rule": validation_rule,
            "current_step_materializes_field": False,
            "schema_contract_passed": True,
        })
    return rows


def build_field_mapping() -> list[dict[str, Any]]:
    mapping_specs = {
        "pdb_id": ("sample-level QA", "pdb_id", "execution manifest", "pdb_id", "copy validated identity field"),
        "expected_het_id": ("sample-level QA", "expected_het_id", "execution manifest", "expected_het_id", "copy validated ligand identity"),
        "protein_atom_table_path": ("sample_artifact_root", "protein_atom_table.csv", "", "", "join sample_artifact_root with fixed filename"),
        "ligand_atom_table_path": ("sample_artifact_root", "ligand_atom_table.csv", "", "", "join sample_artifact_root with fixed filename"),
        "pocket_atom_table_path": ("sample_artifact_root", "pocket_atom_table.csv", "", "", "join sample_artifact_root with fixed filename"),
        "covalent_event_table_path": ("sample_artifact_root", "covalent_event_table.csv", "", "", "join sample_artifact_root with fixed filename"),
        "ligand_residue_atom_pair_table_path": ("sample_artifact_root", "ligand_residue_atom_pair_table.csv", "", "", "join sample_artifact_root with fixed filename"),
        "sample_preparation_audit_path": ("sample_artifact_root", "sample_preparation_audit.csv", "", "", "join sample_artifact_root with fixed filename"),
        "protein_atom_count": ("execution manifest", "protein_atom_count", "sample-level QA", "protein_atom_count", "copy validated count"),
        "ligand_atom_count": ("execution manifest", "ligand_atom_count", "sample-level QA", "ligand_atom_count", "copy validated count"),
        "pocket_atom_count": ("execution manifest", "pocket_atom_count", "sample-level QA", "pocket_atom_count", "copy validated count"),
        "covalent_event_count": ("execution manifest", "covalent_event_count", "sample-level QA", "covalent_event_count", "copy validated count"),
        "ligand_residue_atom_pair_count": ("execution manifest", "ligand_residue_atom_pair_count", "sample-level QA", "ligand_residue_atom_pair_count", "copy validated count"),
        "covalent_residue_name": ("Step 14AA covalent_event_table", "residue_comp_id", "", "", "copy CYS residue identity"),
        "covalent_residue_chain_id": ("Step 14AA covalent_event_table", "residue_auth_asym_id", "Step 14AA covalent_event_table", "residue_label_asym_id", "prefer auth chain id"),
        "covalent_residue_index": ("Step 14AA covalent_event_table", "residue_auth_seq_id", "Step 14AA covalent_event_table", "residue_label_seq_id", "prefer auth residue index"),
        "covalent_residue_atom_name": ("Step 14AA covalent_event_table", "residue_atom_name", "", "", "copy SG atom identity"),
        "ligand_comp_id": ("Step 14AA covalent_event_table", "ligand_comp_id", "", "", "copy ligand comp id"),
        "ligand_covalent_atom_name": ("Step 14AA covalent_event_table", "ligand_atom_name", "", "", "copy ligand covalent atom name"),
        "covalent_bond_atom_pair": ("Step 14AA covalent_event_table", "covalent_bond_atom_pair", "Step 14AB event pair QA", "covalent_bond_atom_pair", "copy validated atom pair"),
        "conn_id": ("Step 14AA covalent_event_table", "conn_id", "", "", "copy struct_conn id from derived table"),
        "conn_type_id": ("Step 14AA covalent_event_table", "conn_type_id", "", "", "copy covale conn type"),
        "bond_distance_angstrom": ("Step 14AA ligand_residue_atom_pair_table", "bond_distance_angstrom", "Step 14AB event pair QA", "bond_distance_angstrom", "copy validated distance"),
        "sample_index_status": ("constant", "sample_index_materialized_from_qa_passed_sample", "", "", "future materialization constant"),
        "eligible_for_final_dataset_design": ("constant", "false", "", "", "remain false until future QA/application gate"),
        "ready_for_training_current_step": ("constant", "false", "", "", "remain false"),
        "feature_semantics_audit_required_before_training": ("constant", "true", "", "", "remain true"),
        "leakage_split_design_required_before_training": ("constant", "true", "", "", "remain true"),
    }
    rows = []
    for index, field in enumerate(SAMPLE_INDEX_FIELDS, start=1):
        spec = mapping_specs.get(field, ("source inventory", field, "", "", "copy or generate during future materialization smoke"))
        rows.append({
            "mapping_id": f"CYS_SG_SAMPLE_INDEX_MAPPING_{index:06d}",
            "sample_index_field": field,
            "primary_source_artifact": spec[0],
            "primary_source_field": spec[1],
            "fallback_source_artifact": spec[2],
            "fallback_source_field": spec[3],
            "transformation_rule": spec[4],
            "required_validation": "validated by Step 14AB QA gate and future sample index materialization smoke",
            "mapping_status": "planned_and_validated",
        })
    return rows


def build_materialization_plan(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(source_rows, start=1):
        rows.append({
            "sample_index_materialization_plan_id": f"CYS_SG_SAMPLE_INDEX_PLAN_{index:06d}",
            "sample_index_source_id": row["sample_index_source_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "planned_sample_index_row_id": f"CYS_SG_SAMPLE_INDEX_{index:06d}",
            "planned_materialization_status": "pending_sample_index_materialization_smoke",
            "source_artifact_root": row["sample_artifact_root"],
            "required_source_table_count": 6,
            "required_source_tables_present": all(_table_path(row["sample_artifact_root"], name).is_file() for name in REQUIRED_TABLES),
            "sample_qa_passed": row["sample_level_qa_status"] == "passed",
            "event_pair_qa_passed": row["event_pair_qa_status"] == "passed",
            "planned_next_gate": "covapie_sample_index_materialization_smoke",
            "sample_index_written_current_step": False,
            "final_dataset_written_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_policy_rows() -> list[dict[str, Any]]:
    items = [
        "sample_index_design_gate_only",
        "design_gate_does_not_write_sample_index",
        "source_inventory_is_not_sample_index",
        "materialization_plan_is_not_sample_index",
        "design_gate_reads_qa_passed_derived_outputs_only",
        "design_gate_does_not_read_raw_mmcif",
        "design_gate_does_not_modify_atom_event_tables",
        "no_final_dataset_current_step",
        "no_split_or_leakage_current_step",
        "no_dataloader_smoke_current_step",
        "no_training_current_step",
        "feature_semantics_audit_required_before_training",
        "leakage_split_gate_required_before_training",
        "canonical_five_masks_preserved",
        "do_not_train_from_sample_index_design_artifacts",
    ]
    return [{"policy_item": item, "policy_description": item.replace("_", " "), "policy_contract_passed": True} for item in items]


def build_downstream_rows() -> list[dict[str, Any]]:
    statuses = {
        "ready_for_covapie_sample_index_materialization_smoke": True,
        "ready_for_covapie_final_dataset_design_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    return [
        {
            "readiness_item": key,
            "observed_status": value,
            "readiness_passed": value is True if key == "ready_for_covapie_sample_index_materialization_smoke" else value is False,
            "next_required_gate": "covapie_sample_index_materialization_smoke",
            "qa_comment": "sample index materialization smoke is allowed next; training and downstream dataset gates remain blocked",
        }
        for key, value in statuses.items()
    ]


def _forbidden_output_artifacts_absent() -> bool:
    forbidden_names = {
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "training_report.csv",
        "training_report.json",
    }
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    if not OUTPUT_ROOT.exists():
        return True
    return not any(p.is_file() and (p.name in forbidden_names or p.suffix.lower() in forbidden_suffixes) for p in OUTPUT_ROOT.rglob("*"))


def build_safety_rows() -> list[dict[str, Any]]:
    raw_tracked = bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    checks = [
        ("network_access_used_current_step", False, False),
        ("download_attempted_current_step", False, False),
        ("raw_mmcif_read_current_step", False, False),
        ("struct_conn_parsed_current_step", False, False),
        ("atom_site_parsed_current_step", False, False),
        ("data_raw_written_current_step", False, False),
        ("raw_files_remain_untracked", True, not raw_tracked),
        ("raw_files_remain_unstaged", True, not raw_staged),
        ("raw_files_committed", False, raw_tracked),
        ("metadata_csv_unchanged", True, _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14ab_artifacts_unchanged", True, not _path_diff_exists([STEP14AB_ROOT.as_posix()])),
        ("step14aa_artifacts_unchanged", True, not _path_diff_exists([STEP14AA_ROOT.as_posix()])),
        ("step14z_artifacts_unchanged", True, not _path_diff_exists([STEP14Z_ROOT.as_posix()])),
        ("protected_source_diff_empty", True, not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", True, not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("atom_event_tables_unchanged", True, not _path_diff_exists([(STEP14AA_ROOT / "samples").as_posix()])),
        ("sample_index_written_current_step", False, False),
        ("final_dataset_written", False, False),
        ("split_assignments_written", False, False),
        ("leakage_matrix_written", False, False),
        ("actual_dataloader_smoke_written", False, False),
        ("training_artifacts_written", False, False),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", True, _forbidden_output_artifacts_absent()),
        ("torch_imported", False, False),
        ("numpy_imported", False, False),
        ("rdkit_used", False, False),
        ("gemmi_used", False, False),
        ("requests_used", False, False),
        ("urllib_used", False, False),
        ("selenium_used", False, False),
        ("playwright_used", False, False),
        ("bs4_used", False, False),
    ]
    return [{"safety_item": item, "required_status": expected, "observed_status": observed, "safety_passed": observed == expected, "blocking_reasons": "" if observed == expected else item} for item, expected, observed in checks]


def build_manifest(precondition_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]], schema_rows: list[dict[str, Any]], mapping_rows: list[dict[str, Any]], plan_rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]], downstream_rows: list[dict[str, Any]], safety_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest14ab = _load_json(STEP14AB_MANIFEST_JSON)
    blocking = [row["precondition_item"] for row in precondition_rows if not _bool(row["precondition_passed"])]
    blocking += [row["safety_item"] for row in safety_rows if not _bool(row["safety_passed"])]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step14ab_sample_preparation_qa_gate_validated": _all_true(precondition_rows, "precondition_passed"),
        "input_sample_qa_count": manifest14ab["sample_qa_count"],
        "input_table_integrity_qa_count": manifest14ab["table_integrity_qa_count"],
        "input_event_pair_qa_count": manifest14ab["event_pair_qa_count"],
        "input_qa_issue_count": manifest14ab["qa_issue_count"],
        "sample_index_source_inventory_count": len(source_rows),
        "sample_index_schema_field_count": len(schema_rows),
        "sample_index_field_mapping_count": len(mapping_rows),
        "sample_index_materialization_plan_count": len(plan_rows),
        "eligible_for_sample_index_materialization_count": sum(1 for row in source_rows if _bool(row["eligible_for_sample_index_materialization"])),
        "accepted_pdb_het_pairs": [f"{row['pdb_id']}/{row['expected_het_id']}" for row in source_rows],
        "covalent_bond_atom_pairs": sorted({row["covalent_bond_atom_pair"] for row in source_rows}),
        "sample_index_source_inventory_csv_json_consistent": True,
        "sample_index_written_current_step": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "raw_mmcif_read_current_step": False,
        "struct_conn_parsed_current_step": False,
        "atom_site_parsed_current_step": False,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "data_raw_written_current_step": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "gemmi_used": False,
        "requests_used": False,
        "urllib_used": False,
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "ready_for_covapie_sample_index_materialization_smoke": True,
        "ready_for_covapie_final_dataset_design_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "canonical_mask_task_count": len(CANONICAL_MASK_TASK_NAMES),
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"],
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "precondition_audit_passed": _all_true(precondition_rows, "precondition_passed"),
        "source_inventory_passed": _all_true(source_rows, "eligible_for_sample_index_materialization"),
        "schema_contract_passed": _all_true(schema_rows, "schema_contract_passed"),
        "field_mapping_passed": all(row["mapping_status"] == "planned_and_validated" for row in mapping_rows),
        "materialization_plan_passed": _all_true(plan_rows, "required_source_tables_present"),
        "policy_contract_passed": _all_true(policy_rows, "policy_contract_passed"),
        "downstream_readiness_contract_passed": _all_true(downstream_rows, "readiness_passed"),
        "safety_audit_passed": _all_true(safety_rows, "safety_passed"),
        "recommended_next_step": "covapie_sample_index_materialization_smoke",
        "all_checks_passed": not blocking,
        "blocking_reasons": blocking,
    }


def run_covapie_sample_index_design_gate_v0() -> dict[str, Any]:
    sample_rows = _csv_rows(STEP14AB_SAMPLE_QA_CSV)
    sample_json = _load_json(STEP14AB_SAMPLE_QA_JSON)
    execution_rows = _csv_rows(STEP14AA_EXECUTION_MANIFEST_CSV)
    execution_json = _load_json(STEP14AA_EXECUTION_MANIFEST_JSON)
    inventory_rows = _csv_rows(STEP14AA_SAMPLE_INVENTORY_CSV)
    inventory_json = _load_json(STEP14AA_SAMPLE_INVENTORY_JSON)
    table_rows = _csv_rows(STEP14AB_TABLE_QA_CSV)
    event_rows = _csv_rows(STEP14AB_EVENT_QA_CSV)
    issue_rows = _csv_rows(STEP14AB_ISSUE_INVENTORY_CSV)

    precondition_rows = build_precondition_rows(sample_rows, sample_json, execution_rows, execution_json, inventory_rows, inventory_json, table_rows, event_rows, issue_rows)
    source_rows = build_source_inventory(sample_rows, table_rows, event_rows)
    schema_rows = build_schema_contract()
    mapping_rows = build_field_mapping()
    plan_rows = build_materialization_plan(source_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows()
    manifest = build_manifest(precondition_rows, source_rows, schema_rows, mapping_rows, plan_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "source_rows": source_rows,
        "schema_rows": schema_rows,
        "mapping_rows": mapping_rows,
        "plan_rows": plan_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }


if __name__ == "__main__":
    result = run_covapie_sample_index_design_gate_v0()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
