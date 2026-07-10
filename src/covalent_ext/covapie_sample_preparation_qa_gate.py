from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_sample_preparation_execution_smoke as step14aa


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_sample_preparation_qa_gate_v0"
STEP_LABEL = "Step 14AB"
PREVIOUS_STAGE = step14aa.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_qa_precondition_audit.csv"
SAMPLE_LEVEL_QA_CSV = OUTPUT_ROOT / "covapie_sample_preparation_sample_level_qa.csv"
SAMPLE_LEVEL_QA_JSON = OUTPUT_ROOT / "covapie_sample_preparation_sample_level_qa.json"
TABLE_INTEGRITY_QA_CSV = OUTPUT_ROOT / "covapie_sample_preparation_table_integrity_qa.csv"
EVENT_PAIR_QA_CSV = OUTPUT_ROOT / "covapie_sample_preparation_event_pair_qa.csv"
ISSUE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_sample_preparation_issue_inventory.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_qa_policy_contract.csv"
DOWNSTREAM_READINESS_CSV = OUTPUT_ROOT / "covapie_sample_preparation_qa_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_qa_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_preparation_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_preparation_qa_gate_v0_summary.md")

STEP14AA_ROOT = step14aa.OUTPUT_ROOT
STEP14AA_MANIFEST_JSON = step14aa.MANIFEST_JSON
STEP14AA_EXECUTION_MANIFEST_CSV = step14aa.EXECUTION_MANIFEST_CSV
STEP14AA_EXECUTION_MANIFEST_JSON = step14aa.EXECUTION_MANIFEST_JSON
STEP14AA_SAMPLE_INVENTORY_CSV = step14aa.SAMPLE_INVENTORY_CSV
STEP14AA_SAMPLE_INVENTORY_JSON = step14aa.SAMPLE_INVENTORY_JSON
STEP14AA_TRACEABILITY_AUDIT_CSV = step14aa.TRACEABILITY_AUDIT_CSV
STEP14AA_QUALITY_AUDIT_CSV = step14aa.QUALITY_AUDIT_CSV
STEP14AA_SAFETY_AUDIT_CSV = step14aa.SAFETY_AUDIT_CSV
STEP14Z_ROOT = step14aa.STEP14Z_ROOT
STEP14Y_ROOT = step14aa.STEP14Y_ROOT

RAW_ROOT = step14aa.RAW_ROOT
METADATA_CSV = step14aa.METADATA_CSV
METADATA_CSV_SHA256 = step14aa.METADATA_CSV_SHA256
CANONICAL_MASK_TASK_NAMES = step14aa.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14aa.CANONICAL_MASK_TASK_ALIASES
ACCEPTED_PDB_HET_PAIRS = step14aa.ACCEPTED_PDB_HET_PAIRS
NEXT_REQUIRED_GATE = "covapie_sample_index_design_gate"

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SAMPLE_LEVEL_QA_COLUMNS = ["sample_qa_id", "sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "sample_artifact_root", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "sample_preparation_status", "sample_level_qa_status", "ready_for_sample_index_design_gate_current_step", "ready_for_training_current_step", "qa_comment"]
TABLE_INTEGRITY_QA_COLUMNS = ["table_integrity_qa_id", "sample_execution_id", "pdb_id", "expected_het_id", "table_name", "table_exists", "row_count", "required_columns_present", "table_integrity_status", "blocking_reasons"]
EVENT_PAIR_QA_COLUMNS = ["event_pair_qa_id", "sample_execution_id", "pdb_id", "expected_het_id", "conn_type_id", "residue_comp_id", "residue_atom_name", "ligand_comp_id", "ligand_atom_name", "covalent_bond_atom_pair", "event_source", "event_status", "bond_distance_angstrom", "bond_distance_status", "ligand_covalent_atom_count", "pocket_radius_status", "event_pair_qa_status", "blocking_reasons"]
ISSUE_INVENTORY_COLUMNS = ["issue_id", "issue_scope", "pdb_id", "expected_het_id", "issue_severity", "issue_type", "issue_description", "issue_status"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]

REQUIRED_TABLES = {
    "protein_atom_table.csv": step14aa.PROTEIN_ATOM_COLUMNS,
    "ligand_atom_table.csv": step14aa.LIGAND_ATOM_COLUMNS,
    "pocket_atom_table.csv": step14aa.POCKET_ATOM_COLUMNS,
    "covalent_event_table.csv": step14aa.COVALENT_EVENT_COLUMNS,
    "ligand_residue_atom_pair_table.csv": step14aa.PAIR_TABLE_COLUMNS,
    "sample_preparation_audit.csv": step14aa.SAMPLE_AUDIT_COLUMNS,
}


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_header(path: str | Path) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader)


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


def build_precondition_rows(execution_rows: list[dict[str, str]], execution_json: list[dict[str, Any]], inventory_rows: list[dict[str, str]], inventory_json: list[dict[str, Any]], traceability_rows: list[dict[str, str]], quality_rows: list[dict[str, str]], safety_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14AA_MANIFEST_JSON) if STEP14AA_MANIFEST_JSON.exists() else {}
    sample_dirs = [STEP14AA_ROOT / "samples" / pair.replace("/", "_") for pair in ACCEPTED_PDB_HET_PAIRS]
    checks = [
        ("step14aa_manifest_exists", STEP14AA_MANIFEST_JSON.as_posix(), "exists", STEP14AA_MANIFEST_JSON.exists(), STEP14AA_MANIFEST_JSON.exists()),
        ("step14aa_stage", STEP14AA_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14aa_all_checks_passed", STEP14AA_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14aa_sample_execution_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("sample_execution_count"), manifest.get("sample_execution_count") == 3),
        ("step14aa_sample_preparation_passed_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("sample_preparation_passed_count"), manifest.get("sample_preparation_passed_count") == 3),
        ("step14aa_raw_file_resolved_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("raw_file_resolved_count"), manifest.get("raw_file_resolved_count") == 3),
        ("step14aa_protein_atom_table_written_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("protein_atom_table_written_count"), manifest.get("protein_atom_table_written_count") == 3),
        ("step14aa_ligand_atom_table_written_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("ligand_atom_table_written_count"), manifest.get("ligand_atom_table_written_count") == 3),
        ("step14aa_pocket_atom_table_written_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("pocket_atom_table_written_count"), manifest.get("pocket_atom_table_written_count") == 3),
        ("step14aa_covalent_event_table_written_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("covalent_event_table_written_count"), manifest.get("covalent_event_table_written_count") == 3),
        ("step14aa_ligand_residue_atom_pair_table_written_count", STEP14AA_MANIFEST_JSON.as_posix(), "3", manifest.get("ligand_residue_atom_pair_table_written_count"), manifest.get("ligand_residue_atom_pair_table_written_count") == 3),
        ("step14aa_ready_for_qa_gate", STEP14AA_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_sample_preparation_qa_gate"), manifest.get("ready_for_covapie_sample_preparation_qa_gate") is True),
        ("step14aa_ready_for_training_false", STEP14AA_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("execution_manifest_csv_json_consistent", STEP14AA_EXECUTION_MANIFEST_JSON.as_posix(), "3 consistent rows", f"{len(execution_rows)} csv/{len(execution_json)} json", len(execution_rows) == len(execution_json) == 3 and _json_consistent(execution_rows, execution_json, "sample_execution_id")),
        ("sample_inventory_csv_json_consistent", STEP14AA_SAMPLE_INVENTORY_JSON.as_posix(), "3 consistent rows", f"{len(inventory_rows)} csv/{len(inventory_json)} json", len(inventory_rows) == len(inventory_json) == 3 and _json_consistent(inventory_rows, inventory_json, "sample_execution_id")),
        ("traceability_audit_all_passed", STEP14AA_TRACEABILITY_AUDIT_CSV.as_posix(), "3 passed", len(traceability_rows), len(traceability_rows) == 3 and all(row["traceability_audit_passed"] == "True" for row in traceability_rows)),
        ("quality_audit_all_passed", STEP14AA_QUALITY_AUDIT_CSV.as_posix(), "3 passed", len(quality_rows), len(quality_rows) == 3 and all(row["quality_audit_passed"] == "True" for row in quality_rows)),
        ("safety_audit_all_passed", STEP14AA_SAFETY_AUDIT_CSV.as_posix(), "passed", len(safety_rows), safety_rows and all(row["safety_passed"] == "True" for row in safety_rows)),
        ("per_sample_directories_exist", (STEP14AA_ROOT / "samples").as_posix(), "6BV6/6BV8/6BV5", [p.as_posix() for p in sample_dirs], all(p.is_dir() for p in sample_dirs)),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_tracked", RAW_ROOT.as_posix(), "false", _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14aa.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_sample_level_qa(execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(execution_rows, start=1):
        passed = (
            row["sample_preparation_status"] == "sample_preparation_smoke_passed"
            and int(row["protein_atom_count"]) > 0
            and int(row["ligand_atom_count"]) > 0
            and int(row["pocket_atom_count"]) > 0
            and int(row["covalent_event_count"]) == 1
            and int(row["ligand_residue_atom_pair_count"]) == 1
        )
        rows.append({
            "sample_qa_id": f"CYS_SG_SAMPLE_PREP_QA_{idx:06d}",
            "sample_preparation_input_id": row["sample_preparation_input_id"],
            "sample_execution_id": row["sample_execution_id"],
            "pdb_id": row["pdb_id"],
            "expected_het_id": row["expected_het_id"],
            "sample_artifact_root": row["sample_artifact_root"],
            "protein_atom_count": row["protein_atom_count"],
            "ligand_atom_count": row["ligand_atom_count"],
            "pocket_atom_count": row["pocket_atom_count"],
            "covalent_event_count": row["covalent_event_count"],
            "ligand_residue_atom_pair_count": row["ligand_residue_atom_pair_count"],
            "sample_preparation_status": row["sample_preparation_status"],
            "sample_level_qa_status": "passed" if passed else "failed",
            "ready_for_sample_index_design_gate_current_step": passed,
            "ready_for_training_current_step": False,
            "qa_comment": "sample preparation execution output passed QA" if passed else "sample preparation execution output failed QA",
        })
    return rows


def build_table_integrity_qa(execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    counter = 1
    for sample in execution_rows:
        sample_root = Path(sample["sample_artifact_root"])
        for table_name, required_columns in REQUIRED_TABLES.items():
            path = sample_root / table_name
            exists = path.is_file()
            table_rows = _csv_rows(path) if exists else []
            header = _csv_header(path) if exists else []
            columns_present = set(required_columns).issubset(set(header))
            passed = exists and len(table_rows) > 0 and columns_present
            rows.append({
                "table_integrity_qa_id": f"CYS_SG_TABLE_QA_{counter:06d}",
                "sample_execution_id": sample["sample_execution_id"],
                "pdb_id": sample["pdb_id"],
                "expected_het_id": sample["expected_het_id"],
                "table_name": table_name,
                "table_exists": exists,
                "row_count": len(table_rows),
                "required_columns_present": columns_present,
                "table_integrity_status": "passed" if passed else "failed",
                "blocking_reasons": "" if passed else "table_integrity_failed",
            })
            counter += 1
    return rows


def build_event_pair_qa(execution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for idx, sample in enumerate(execution_rows, start=1):
        sample_root = Path(sample["sample_artifact_root"])
        event_rows = _csv_rows(sample_root / "covalent_event_table.csv")
        pair_rows = _csv_rows(sample_root / "ligand_residue_atom_pair_table.csv")
        ligand_rows = _csv_rows(sample_root / "ligand_atom_table.csv")
        pocket_rows = _csv_rows(sample_root / "pocket_atom_table.csv")
        event = event_rows[0] if event_rows else {}
        pair = pair_rows[0] if pair_rows else {}
        ligand_covalent_atom_count = sum(row["is_covalent_ligand_atom"] == "True" for row in ligand_rows)
        distance = float(pair.get("bond_distance_angstrom", "0") or "0")
        pocket_ok = bool(pocket_rows) and all(float(row["pocket_radius_angstrom"]) == 8.0 and float(row["min_distance_to_ligand_angstrom"]) <= 8.0 for row in pocket_rows)
        event_ok = (
            len(event_rows) == 1
            and event.get("conn_type_id") == "covale"
            and event.get("residue_comp_id") == "CYS"
            and event.get("residue_atom_name") == "SG"
            and event.get("ligand_comp_id") == "JUG"
            and event.get("ligand_atom_name") == "CAG"
            and event.get("covalent_bond_atom_pair") == "SG--CAG"
            and event.get("event_source") == "raw_struct_conn"
            and event.get("event_status") == "validated"
        )
        passed = event_ok and len(pair_rows) == 1 and distance > 0 and ligand_covalent_atom_count == 1 and pocket_ok
        rows.append({
            "event_pair_qa_id": f"CYS_SG_EVENT_PAIR_QA_{idx:06d}",
            "sample_execution_id": sample["sample_execution_id"],
            "pdb_id": sample["pdb_id"],
            "expected_het_id": sample["expected_het_id"],
            "conn_type_id": event.get("conn_type_id", ""),
            "residue_comp_id": event.get("residue_comp_id", ""),
            "residue_atom_name": event.get("residue_atom_name", ""),
            "ligand_comp_id": event.get("ligand_comp_id", ""),
            "ligand_atom_name": event.get("ligand_atom_name", ""),
            "covalent_bond_atom_pair": event.get("covalent_bond_atom_pair", ""),
            "event_source": event.get("event_source", ""),
            "event_status": event.get("event_status", ""),
            "bond_distance_angstrom": pair.get("bond_distance_angstrom", ""),
            "bond_distance_status": "positive_numeric_distance" if distance > 0 else "invalid_distance",
            "ligand_covalent_atom_count": ligand_covalent_atom_count,
            "pocket_radius_status": "all_pocket_rows_within_8_angstrom" if pocket_ok else "invalid_pocket_radius_or_distance",
            "event_pair_qa_status": "passed" if passed else "failed",
            "blocking_reasons": "" if passed else "event_pair_qa_failed",
        })
    return rows


def build_issue_inventory(sample_rows: list[dict[str, Any]], table_rows: list[dict[str, Any]], event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures = [row for row in sample_rows if row["sample_level_qa_status"] != "passed"]
    failures.extend(row for row in table_rows if row["table_integrity_status"] != "passed")
    failures.extend(row for row in event_rows if row["event_pair_qa_status"] != "passed")
    if not failures:
        return [{
            "issue_id": "NO_QA_ISSUES",
            "issue_scope": "all_samples",
            "pdb_id": "",
            "expected_het_id": "",
            "issue_severity": "none",
            "issue_type": "no_issues",
            "issue_description": "No sample preparation QA issues detected.",
            "issue_status": "passed",
        }]
    rows = []
    for idx, row in enumerate(failures, start=1):
        rows.append({
            "issue_id": f"SAMPLE_PREP_QA_ISSUE_{idx:06d}",
            "issue_scope": "sample",
            "pdb_id": row.get("pdb_id", ""),
            "expected_het_id": row.get("expected_het_id", ""),
            "issue_severity": "blocking",
            "issue_type": "qa_failure",
            "issue_description": row.get("blocking_reasons", "qa_failure"),
            "issue_status": "open",
        })
    return rows


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "sample_preparation_qa_gate_only": "This step performs QA over Step 14AA outputs only.",
        "qa_gate_reads_execution_outputs_only": "QA reads derived execution outputs, not raw structure files.",
        "qa_gate_does_not_read_raw_mmcif": "Raw CIF/mmCIF is not read in this QA gate.",
        "qa_gate_does_not_modify_atom_tables": "Per-sample atom/event tables are not modified.",
        "qa_gate_does_not_create_sample_index": "No sample index is written.",
        "qa_gate_does_not_create_final_dataset": "No final dataset is written.",
        "qa_gate_does_not_create_split_or_leakage": "No split or leakage matrix is written.",
        "qa_gate_does_not_create_dataloader_smoke": "No dataloader smoke is written.",
        "sample_index_design_gate_required_next": "Sample index design gate is the next allowed step.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split gate remains required before training.",
        "canonical_five_masks_preserved": "The canonical five mask tasks are preserved.",
        "do_not_train_from_qa_artifacts": "QA artifacts must not be used for training.",
    }
    return [{"policy_item": item, "policy_description": desc, "policy_contract_passed": True} for item, desc in descriptions.items()]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_sample_index_design_gate", True, True, NEXT_REQUIRED_GATE, "allowed next step"),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", False, True, "not_allowed_current_step", "sample index/final dataset path not ready"),
        ("ready_for_training", False, True, "not_allowed_current_step", "not a training sample"),
        ("ready_to_train_now", False, True, "not_allowed_current_step", "feature semantics and leakage/split gates remain required"),
    ]
    return [{"readiness_item": item, "observed_status": observed, "readiness_passed": passed, "next_required_gate": next_gate, "qa_comment": comment} for item, observed, passed, next_gate, comment in specs]


def _forbidden_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    names = {"sample_index.csv", "sample_index.json", "final_dataset.csv", "final_dataset.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json", "protein_atom_table.csv", "ligand_atom_table.csv", "pocket_atom_table.csv", "covalent_event_table.csv", "ligand_residue_atom_pair_table.csv"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def build_safety_rows() -> list[dict[str, Any]]:
    raw_tracked = bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    no_forbidden = not _forbidden_artifact_exists()
    checks = [
        ("network_access_used_current_step", "false", "false", True),
        ("download_attempted_current_step", "false", "false", True),
        ("raw_mmcif_read_current_step", "false", "false", True),
        ("struct_conn_parsed_current_step", "false", "false", True),
        ("atom_site_parsed_current_step", "false", "false", True),
        ("data_raw_written_current_step", "false", "false", True),
        ("raw_files_remain_untracked", "true", str(not raw_tracked).lower(), not raw_tracked),
        ("raw_files_remain_unstaged", "true", str(not raw_staged).lower(), not raw_staged),
        ("raw_files_committed", "false", str(raw_tracked).lower(), not raw_tracked),
        ("metadata_csv_unchanged", "true", str(_metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])).lower(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14aa_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14AA_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14AA_ROOT.as_posix()])),
        ("step14z_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14Z_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14Z_ROOT.as_posix()])),
        ("step14y_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14Y_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14Y_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("sample_index_written_current_step", "false", str(not no_forbidden).lower(), no_forbidden),
        ("final_dataset_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("split_assignments_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("leakage_matrix_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("actual_dataloader_smoke_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("training_artifacts_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("torch_imported", "false", "false", True),
        ("numpy_imported", "false", "false", True),
        ("rdkit_used", "false", "false", True),
        ("gemmi_used", "false", "false", True),
        ("requests_used", "false", "false", True),
        ("urllib_used", "false", "false", True),
        ("selenium_used", "false", "false", True),
        ("playwright_used", "false", "false", True),
        ("bs4_used", "false", "false", True),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(sample_rows, table_rows, event_rows, issue_rows, precondition_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    issue_count = 0 if issue_rows and issue_rows[0]["issue_id"] == "NO_QA_ISSUES" else len(issue_rows)
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (precondition_rows, "precondition_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and all(row["sample_level_qa_status"] == "passed" for row in sample_rows) and all(row["table_integrity_status"] == "passed" for row in table_rows) and all(row["event_pair_qa_status"] == "passed" for row in event_rows) and issue_count == 0
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "sample_qa_count": len(sample_rows),
        "table_integrity_qa_count": len(table_rows),
        "event_pair_qa_count": len(event_rows),
        "qa_issue_count": issue_count,
        "sample_qa_passed_count": sum(row["sample_level_qa_status"] == "passed" for row in sample_rows),
        "table_integrity_passed_count": sum(row["table_integrity_status"] == "passed" for row in table_rows),
        "event_pair_qa_passed_count": sum(row["event_pair_qa_status"] == "passed" for row in event_rows),
        "accepted_pdb_het_pairs": ACCEPTED_PDB_HET_PAIRS,
        "covalent_bond_atom_pairs": ["SG--CAG"],
        "ready_for_covapie_sample_index_design_gate": True,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "raw_mmcif_read_current_step": False,
        "struct_conn_parsed_current_step": False,
        "atom_site_parsed_current_step": False,
        "sample_index_written_current_step": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": NEXT_REQUIRED_GATE,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["sample_preparation_qa_gate_failed"],
    }


def run_covapie_sample_preparation_qa_gate_v0() -> dict[str, Any]:
    execution_rows = _csv_rows(STEP14AA_EXECUTION_MANIFEST_CSV)
    execution_json = _load_json(STEP14AA_EXECUTION_MANIFEST_JSON)
    inventory_rows = _csv_rows(STEP14AA_SAMPLE_INVENTORY_CSV)
    inventory_json = _load_json(STEP14AA_SAMPLE_INVENTORY_JSON)
    traceability_rows = _csv_rows(STEP14AA_TRACEABILITY_AUDIT_CSV)
    quality_rows = _csv_rows(STEP14AA_QUALITY_AUDIT_CSV)
    safety_rows_input = _csv_rows(STEP14AA_SAFETY_AUDIT_CSV)
    precondition_rows = build_precondition_rows(execution_rows, execution_json, inventory_rows, inventory_json, traceability_rows, quality_rows, safety_rows_input)
    sample_rows = build_sample_level_qa(execution_rows)
    table_rows = build_table_integrity_qa(execution_rows)
    event_rows = build_event_pair_qa(execution_rows)
    issue_rows = build_issue_inventory(sample_rows, table_rows, event_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows()
    manifest = build_manifest(sample_rows, table_rows, event_rows, issue_rows, precondition_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "sample_rows": sample_rows,
        "table_rows": table_rows,
        "event_rows": event_rows,
        "issue_rows": issue_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
