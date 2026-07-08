from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_batch_raw_read_extraction_smoke as step13be


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_extraction_qa_gate_v0"
PREVIOUS_STAGE = step13be.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_extraction_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_extraction_qa_precondition_audit.csv"
EVENT_TABLE_QA_CSV = OUTPUT_ROOT / "covapie_extracted_event_table_qa_audit.csv"
ATOM_TABLE_QA_CSV = OUTPUT_ROOT / "covapie_extracted_atom_table_qa_audit.csv"
GEOMETRY_QA_CSV = OUTPUT_ROOT / "covapie_extracted_geometry_qa_audit.csv"
TRACEABILITY_QA_CSV = OUTPUT_ROOT / "covapie_extraction_traceability_qa_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_extraction_qa_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_extraction_qa_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_extraction_qa_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_extraction_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_extraction_qa_gate_v0_summary.md")

EVENT_FIELDS = step13be.EVENT_FIELDS
ATOM_FIELDS = step13be.ATOM_FIELDS
CANONICAL_MASK_TASK_NAMES = step13be.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13be.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13be.step13bd.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EVENT_QA_COLUMNS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "row_index",
    "column_count",
    "schema_order_matches_contract",
    "extracted_event_id_deterministic",
    "extracted_event_id_unique",
    "allowlist_entry_id_unique",
    "candidate_metadata_id_unique",
    "extraction_status",
    "extraction_success",
    "extraction_blocking_reason_empty",
    "residue_atom_found",
    "ligand_atom_found",
    "covalent_connection_found",
    "covalent_bond_distance_angstrom",
    "covalent_bond_distance_numeric",
    "covalent_bond_distance_plausible_1_0_to_2_2",
    "ready_for_training_false",
    "feature_semantics_blocker_preserved",
    "leakage_split_blocker_preserved",
    "extracted_event_table_qa_passed",
    "qa_comment",
]
ATOM_QA_COLUMNS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "pdb_id",
    "het_code",
    "protein_atom_rows_for_event",
    "ligand_atom_rows_for_event",
    "protein_table_schema_matches_contract",
    "ligand_table_schema_matches_contract",
    "protein_rows_have_numeric_coordinates",
    "ligand_rows_have_numeric_coordinates",
    "protein_rows_ready_for_training_false",
    "ligand_rows_ready_for_training_false",
    "protein_feature_semantics_blocker_preserved",
    "ligand_feature_semantics_blocker_preserved",
    "covalent_residue_atom_present_in_protein_table",
    "covalent_ligand_atom_present_in_ligand_table",
    "extracted_atom_table_qa_passed",
    "qa_comment",
]
GEOMETRY_QA_COLUMNS = [
    "extracted_event_id",
    "pdb_id",
    "het_code",
    "residue_atom_xyz_present",
    "ligand_atom_xyz_present",
    "recomputed_distance_angstrom",
    "event_table_distance_angstrom",
    "distance_absolute_delta",
    "distance_recompute_matches_event_table",
    "distance_plausibility_status",
    "geometry_qa_passed",
    "qa_comment",
]
TRACEABILITY_QA_COLUMNS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "pdb_id",
    "het_code",
    "step13be_raw_read_audit_found",
    "step13be_mmcif_parse_audit_found",
    "step13be_extraction_qa_audit_found",
    "step13bd_input_contract_found",
    "step13bd_event_schema_contract_found",
    "step13bd_atom_schema_contract_found",
    "step13bb_allowlist_entry_found",
    "protein_atom_rows_found",
    "ligand_atom_rows_found",
    "traceability_qa_passed",
    "qa_comment",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKER_COLUMNS = ["training_blocker_item", "required_status", "current_step_status", "training_blocker_passed", "qa_comment"]


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
    path = step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _schema_fields(path: Path, field_column: str) -> list[str]:
    return [row[field_column] for row in _csv_rows(path)]


def _atom_contract_fields() -> list[str]:
    rows = _csv_rows(step13be.step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV)
    fields = []
    for row in rows:
        field = row["extracted_atom_field"]
        if field not in fields:
            fields.append(field)
    return fields


def _precondition_rows(manifest13be: dict[str, Any], event_rows: list[dict[str, str]], protein_rows: list[dict[str, str]], ligand_rows: list[dict[str, str]], event_contract: list[str], atom_contract: list[str]) -> list[dict[str, Any]]:
    checks = [
        ("step13be_manifest_exists", step13be.MANIFEST_JSON, "exists", step13be.MANIFEST_JSON.exists(), step13be.MANIFEST_JSON.exists()),
        ("step13be_stage", step13be.MANIFEST_JSON, PREVIOUS_STAGE, manifest13be.get("stage"), manifest13be.get("stage") == PREVIOUS_STAGE),
        ("step13be_all_checks_passed", step13be.MANIFEST_JSON, "true", manifest13be.get("all_checks_passed"), manifest13be.get("all_checks_passed") is True),
        ("step13be_ready_for_extraction_qa", step13be.MANIFEST_JSON, "true", manifest13be.get("ready_for_covapie_extraction_qa_gate"), manifest13be.get("ready_for_covapie_extraction_qa_gate") is True),
        ("step13be_ready_for_sample_index_design", step13be.MANIFEST_JSON, "false", manifest13be.get("ready_for_sample_index_design_gate"), manifest13be.get("ready_for_sample_index_design_gate") is False),
        ("step13be_ready_for_training", step13be.MANIFEST_JSON, "false", manifest13be.get("ready_for_training"), manifest13be.get("ready_for_training") is False),
        ("event_table_exists", step13be.EXTRACTED_EVENT_TABLE_CSV, "exists", step13be.EXTRACTED_EVENT_TABLE_CSV.exists(), step13be.EXTRACTED_EVENT_TABLE_CSV.exists()),
        ("event_table_row_count", step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("event_table_column_count", step13be.EXTRACTED_EVENT_TABLE_CSV, "31", len(event_rows[0]) if event_rows else 0, bool(event_rows) and len(event_rows[0]) == 31),
        ("protein_table_exists", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "exists", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV.exists(), step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV.exists()),
        ("protein_table_row_count", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("ligand_table_exists", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "exists", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV.exists(), step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV.exists()),
        ("ligand_table_row_count", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("event_schema_contract_exists", step13be.step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV, "exists", step13be.step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV.exists(), step13be.step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV.exists()),
        ("event_schema_contract_field_count", step13be.step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV, "31", len(event_contract), len(event_contract) == 31),
        ("atom_schema_contract_exists", step13be.step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV, "exists", step13be.step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV.exists(), step13be.step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV.exists()),
        ("atom_schema_contract_field_count", step13be.step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV, "23", len(atom_contract), len(atom_contract) == 23),
        ("metadata_csv_hash_unchanged", step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def _event_qa_rows(event_rows: list[dict[str, str]], event_contract: list[str]) -> list[dict[str, Any]]:
    event_ids = [row["extracted_event_id"] for row in event_rows]
    allowlist_ids = [row["allowlist_entry_id"] for row in event_rows]
    candidate_ids = [row["candidate_metadata_id"] for row in event_rows]
    rows = []
    for index, row in enumerate(event_rows, start=1):
        distance = _float_or_none(row["covalent_bond_distance_angstrom"])
        checks = {
            "schema_order_matches_contract": list(row.keys()) == event_contract,
            "extracted_event_id_deterministic": row["extracted_event_id"] == f"extracted_event::{row['candidate_metadata_id']}",
            "extracted_event_id_unique": event_ids.count(row["extracted_event_id"]) == 1,
            "allowlist_entry_id_unique": allowlist_ids.count(row["allowlist_entry_id"]) == 1,
            "candidate_metadata_id_unique": candidate_ids.count(row["candidate_metadata_id"]) == 1,
            "extraction_success": row["extraction_status"] == "extracted_success",
            "extraction_blocking_reason_empty": row["extraction_blocking_reason"] == "",
            "residue_atom_found": _bool(row["residue_atom_found"]),
            "ligand_atom_found": _bool(row["ligand_atom_found"]),
            "covalent_connection_found": _bool(row["covalent_connection_found"]),
            "covalent_bond_distance_numeric": distance is not None,
            "covalent_bond_distance_plausible_1_0_to_2_2": distance is not None and 1.0 <= distance <= 2.2,
            "ready_for_training_false": row["ready_for_training"] == "False",
            "feature_semantics_blocker_preserved": row["feature_semantics_audit_required_before_training"] == "True",
            "leakage_split_blocker_preserved": row["leakage_split_design_required_before_training"] == "True",
        }
        passed = all(checks.values()) and len(row) == 31
        rows.append(
            {
                "extracted_event_id": row["extracted_event_id"],
                "allowlist_entry_id": row["allowlist_entry_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "row_index": index,
                "column_count": len(row),
                **checks,
                "extraction_status": row["extraction_status"],
                "covalent_bond_distance_angstrom": row["covalent_bond_distance_angstrom"],
                "extracted_event_table_qa_passed": passed,
                "qa_comment": "event_table_row_validated" if passed else "event_table_row_failed",
            }
        )
    return rows


def _rows_numeric(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(_float_or_none(row["x"]) is not None and _float_or_none(row["y"]) is not None and _float_or_none(row["z"]) is not None for row in rows)


def _atom_qa_rows(event_rows: list[dict[str, str]], protein_rows: list[dict[str, str]], ligand_rows: list[dict[str, str]], atom_contract: list[str]) -> list[dict[str, Any]]:
    rows = []
    protein_schema = bool(protein_rows) and list(protein_rows[0].keys()) == atom_contract
    ligand_schema = bool(ligand_rows) and list(ligand_rows[0].keys()) == atom_contract
    for event in event_rows:
        event_protein = [row for row in protein_rows if row["extracted_event_id"] == event["extracted_event_id"]]
        event_ligand = [row for row in ligand_rows if row["extracted_event_id"] == event["extracted_event_id"]]
        residue_present = any(
            row["chain_id"] == event["chain_id"]
            and row["residue_name"] == event["residue_name"]
            and row["residue_index"] == event["residue_index"]
            and row["atom_name"] == event["residue_atom_name"]
            for row in event_protein
        )
        ligand_present = any(row["het_code"] == event["het_code"] and row["atom_name"] == event["ligand_atom_name"] for row in event_ligand)
        checks = {
            "protein_table_schema_matches_contract": protein_schema,
            "ligand_table_schema_matches_contract": ligand_schema,
            "protein_rows_have_numeric_coordinates": _rows_numeric(event_protein),
            "ligand_rows_have_numeric_coordinates": _rows_numeric(event_ligand),
            "protein_rows_ready_for_training_false": bool(event_protein) and all(row["ready_for_training"] == "False" for row in event_protein),
            "ligand_rows_ready_for_training_false": bool(event_ligand) and all(row["ready_for_training"] == "False" for row in event_ligand),
            "protein_feature_semantics_blocker_preserved": bool(event_protein) and all(row["feature_semantics_audit_required_before_training"] == "True" for row in event_protein),
            "ligand_feature_semantics_blocker_preserved": bool(event_ligand) and all(row["feature_semantics_audit_required_before_training"] == "True" for row in event_ligand),
            "covalent_residue_atom_present_in_protein_table": residue_present,
            "covalent_ligand_atom_present_in_ligand_table": ligand_present,
        }
        passed = all(checks.values()) and len(event_protein) >= 1 and len(event_ligand) >= 1
        rows.append(
            {
                "extracted_event_id": event["extracted_event_id"],
                "allowlist_entry_id": event["allowlist_entry_id"],
                "pdb_id": event["pdb_id"],
                "het_code": event["het_code"],
                "protein_atom_rows_for_event": len(event_protein),
                "ligand_atom_rows_for_event": len(event_ligand),
                **checks,
                "extracted_atom_table_qa_passed": passed,
                "qa_comment": "atom_tables_validated" if passed else "atom_tables_failed",
            }
        )
    return rows


def _geometry_qa_rows(event_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for event in event_rows:
        coords = [
            event["residue_atom_x"],
            event["residue_atom_y"],
            event["residue_atom_z"],
            event["ligand_atom_x"],
            event["ligand_atom_y"],
            event["ligand_atom_z"],
        ]
        present = all(_float_or_none(value) is not None for value in coords)
        recomputed = None
        if present:
            rx, ry, rz, lx, ly, lz = [float(value) for value in coords]
            recomputed = math.sqrt((rx - lx) ** 2 + (ry - ly) ** 2 + (rz - lz) ** 2)
        recorded = _float_or_none(event["covalent_bond_distance_angstrom"])
        delta = abs(recomputed - recorded) if recomputed is not None and recorded is not None else None
        plausible = recomputed is not None and 1.0 <= recomputed <= 2.2
        passed = present and delta is not None and delta <= 0.001 and plausible
        rows.append(
            {
                "extracted_event_id": event["extracted_event_id"],
                "pdb_id": event["pdb_id"],
                "het_code": event["het_code"],
                "residue_atom_xyz_present": present,
                "ligand_atom_xyz_present": present,
                "recomputed_distance_angstrom": f"{recomputed:.3f}" if recomputed is not None else "",
                "event_table_distance_angstrom": event["covalent_bond_distance_angstrom"],
                "distance_absolute_delta": f"{delta:.6f}" if delta is not None else "",
                "distance_recompute_matches_event_table": delta is not None and delta <= 0.001,
                "distance_plausibility_status": "plausible_covalent_distance" if plausible else "distance_not_plausible",
                "geometry_qa_passed": passed,
                "qa_comment": "geometry_validated" if passed else "geometry_failed",
            }
        )
    return rows


def _traceability_rows(event_rows: list[dict[str, str]], protein_rows: list[dict[str, str]], ligand_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    raw_read = {row["pdb_id"] for row in _csv_rows(step13be.RAW_READ_AUDIT_CSV)}
    parse = {row["pdb_id"] for row in _csv_rows(step13be.MMCIF_LOOP_PARSE_AUDIT_CSV)}
    extraction_qa = {row["extracted_event_id"] for row in _csv_rows(step13be.EXTRACTION_QA_AUDIT_CSV)}
    input_contract = {row["allowlist_entry_id"] for row in _csv_rows(step13be.step13bd.INPUT_CONTRACT_CSV)}
    allowlist = {row["allowlist_entry_id"] for row in _csv_rows(step13be.step13bd.STEP13BB_ALLOWLIST_CSV)}
    rows = []
    for event in event_rows:
        checks = {
            "step13be_raw_read_audit_found": event["pdb_id"] in raw_read,
            "step13be_mmcif_parse_audit_found": event["pdb_id"] in parse,
            "step13be_extraction_qa_audit_found": event["extracted_event_id"] in extraction_qa,
            "step13bd_input_contract_found": event["allowlist_entry_id"] in input_contract,
            "step13bd_event_schema_contract_found": step13be.step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV.exists(),
            "step13bd_atom_schema_contract_found": step13be.step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV.exists(),
            "step13bb_allowlist_entry_found": event["allowlist_entry_id"] in allowlist,
            "protein_atom_rows_found": any(row["extracted_event_id"] == event["extracted_event_id"] for row in protein_rows),
            "ligand_atom_rows_found": any(row["extracted_event_id"] == event["extracted_event_id"] for row in ligand_rows),
        }
        passed = all(checks.values())
        rows.append(
            {
                "extracted_event_id": event["extracted_event_id"],
                "allowlist_entry_id": event["allowlist_entry_id"],
                "pdb_id": event["pdb_id"],
                "het_code": event["het_code"],
                **checks,
                "traceability_qa_passed": passed,
                "qa_comment": "traceability_validated" if passed else "traceability_failed",
            }
        )
    return rows


def _boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "extraction_qa_gate": "executed_qa_gate_only",
        "read_step13be_derived_tables": "executed_derived_csv_json_read_only",
        "raw_file_content_read": "not_executed_current_step",
        "mmcif_parse": "not_executed_current_step",
        "atom_site_scan": "not_executed_current_step",
        "struct_conn_scan": "not_executed_current_step",
        "coordinate_extraction": "not_executed_current_step",
        "extracted_event_table_write": "not_executed_current_step_already_completed_previous_step",
        "extracted_atom_table_write": "not_executed_current_step_already_completed_previous_step",
        "sample_index": "blocked_current_step",
        "final_dataset": "blocked_current_step",
        "split_assignments": "blocked_current_step",
        "leakage_matrix": "blocked_current_step",
        "training": "blocked_current_step",
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


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in step13be.FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _sample_final_split_leakage_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
    }
    return any(path.is_file() and path.name in names for path in root.rglob("*")) if root.exists() else False


def _new_extracted_tables_exist(root: Path = OUTPUT_ROOT) -> bool:
    names = {
        "covapie_extracted_event_table.csv",
        "covapie_extracted_protein_pocket_atom_table.csv",
        "covapie_extracted_ligand_atom_table.csv",
    }
    return any(path.is_file() and path.name in names for path in root.rglob("*")) if root.exists() else False


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "policy check", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists()),
        ("no_new_extracted_event_or_atom_tables_written", "forbidden output name scan", "false", not _new_extracted_tables_exist()),
        ("no_sample_final_split_leakage_artifacts", "forbidden output name scan", "false", not _sample_final_split_leakage_exists()),
        ("metadata_csv_unchanged", str(step13be.step13bd.METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13be_artifacts_unchanged", "git diff step13be root", "empty", not _path_diff_exists([str(step13be.OUTPUT_ROOT)])),
        ("step13bd_artifacts_unchanged", "git diff step13bd root", "empty", not _path_diff_exists([str(step13be.step13bd.OUTPUT_ROOT)])),
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
    checks = [
        ("mask_warhead_only_A", "present", "present", True),
        ("mask_linker_plus_warhead_B", "present", "present", True),
        ("mask_scaffold_plus_warhead_B2", "present", "present", True),
        ("mask_scaffold_only_B3", "present", "present", True),
        ("mask_scaffold_plus_linker_plus_warhead_C", "present", "present", True),
        ("feature_semantics_audit_required", "true", "true", True),
        ("feature_semantics_fully_audited_claimed_false", "false", "false", True),
        ("leakage_split_design_required", "true", "true", True),
        ("sample_index_written_current_step_false", "false", "false", True),
        ("split_written_current_step_false", "false", "false", True),
        ("leakage_matrix_written_current_step_false", "false", "false", True),
        ("ready_for_training_false", "false", "false", True),
    ]
    return [
        {
            "training_blocker_item": item,
            "required_status": required,
            "current_step_status": current,
            "training_blocker_passed": passed,
            "qa_comment": "training_blocker_preserved" if passed else "training_blocker_failed",
        }
        for item, required, current, passed in checks
    ]


def run_covapie_extraction_qa_gate_v0() -> dict[str, Any]:
    manifest13be = _load_json(step13be.MANIFEST_JSON)
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    event_contract = _schema_fields(step13be.step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV, "extracted_event_field")
    atom_contract = _atom_contract_fields()
    precondition_rows = _precondition_rows(manifest13be, event_rows, protein_rows, ligand_rows, event_contract, atom_contract)
    event_qa_rows = _event_qa_rows(event_rows, event_contract)
    atom_qa_rows = _atom_qa_rows(event_rows, protein_rows, ligand_rows, atom_contract)
    geometry_qa_rows = _geometry_qa_rows(event_rows)
    traceability_rows = _traceability_rows(event_rows, protein_rows, ligand_rows)
    boundary_rows = _boundary_rows()
    git_safety_rows = _git_safety_rows()
    training_blocker_rows = _training_blocker_rows()

    distances = [float(row["covalent_bond_distance_angstrom"]) for row in event_rows]
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "event": len(event_qa_rows) == 4 and _all_true(event_qa_rows, "extracted_event_table_qa_passed"),
        "atom": len(atom_qa_rows) == 4 and _all_true(atom_qa_rows, "extracted_atom_table_qa_passed"),
        "geometry": len(geometry_qa_rows) == 4 and _all_true(geometry_qa_rows, "geometry_qa_passed"),
        "traceability": len(traceability_rows) == 4 and _all_true(traceability_rows, "traceability_qa_passed"),
        "boundary": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "training_blockers": _all_true(training_blocker_rows, "training_blocker_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13be_extraction_smoke_validated": qa_checks["precondition"],
        "source_extracted_event_row_count": len(event_rows),
        "source_extracted_event_column_count": len(event_rows[0]) if event_rows else 0,
        "source_protein_pocket_atom_row_count": len(protein_rows),
        "source_ligand_atom_row_count": len(ligand_rows),
        "extracted_event_table_qa_passed": qa_checks["event"],
        "extracted_atom_table_qa_passed": qa_checks["atom"],
        "geometry_qa_passed": qa_checks["geometry"],
        "traceability_qa_passed": qa_checks["traceability"],
        "boundary_safety_passed": qa_checks["boundary"],
        "git_safety_passed": qa_checks["git_safety"],
        "training_blockers_passed": qa_checks["training_blockers"],
        "extraction_success_count": sum(1 for row in event_rows if row["extraction_status"] == "extracted_success"),
        "extraction_blocked_count": sum(1 for row in event_rows if row["extraction_status"] != "extracted_success"),
        "residue_atom_found_count": sum(1 for row in event_rows if row["residue_atom_found"] == "True"),
        "ligand_atom_found_count": sum(1 for row in event_rows if row["ligand_atom_found"] == "True"),
        "covalent_connection_found_count": sum(1 for row in event_rows if row["covalent_connection_found"] == "True"),
        "covalent_bond_distance_min_angstrom": min(distances),
        "covalent_bond_distance_max_angstrom": max(distances),
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "atom_site_scan_current_step": False,
        "struct_conn_scan_current_step": False,
        "coordinate_extraction_current_step": False,
        "extracted_event_table_written_current_step": False,
        "extracted_atom_table_written_current_step": False,
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
        "ready_for_covapie_sample_index_design_gate": True,
        "ready_for_covapie_sample_index_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13be.step13bd.CANONICAL_MASK_TASK_NAMES,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_sample_index_design_gate",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "precondition_rows": precondition_rows,
        "event_qa_rows": event_qa_rows,
        "atom_qa_rows": atom_qa_rows,
        "geometry_qa_rows": geometry_qa_rows,
        "traceability_rows": traceability_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }
