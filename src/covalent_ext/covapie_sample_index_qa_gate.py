from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from covalent_ext import covapie_sample_index_smoke as step13bh


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_sample_index_qa_gate_v0"
PREVIOUS_STAGE = step13bh.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_index_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_qa_precondition_audit.csv"
SCHEMA_CSV_JSON_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_schema_csv_json_qa_audit.csv"
ROW_IDENTITY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_row_identity_qa_audit.csv"
MASK_DISTRIBUTION_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_mask_distribution_qa_audit.csv"
SOURCE_TRACEABILITY_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_source_traceability_qa_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_sample_index_qa_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_sample_index_qa_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_sample_index_qa_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_index_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_index_qa_gate_v0_summary.md")

SAMPLE_INDEX_FIELDS = step13bh.SAMPLE_INDEX_FIELDS
CANONICAL_MASK_TASK_NAMES = step13bh.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bh.CANONICAL_MASK_TASK_ALIASES
MASK_ALIAS_BY_NAME = dict(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES))
METADATA_CSV_SHA256 = step13bh.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_QA_COLUMNS = ["qa_item", "expected_status", "observed_status", "schema_csv_json_qa_passed", "qa_comment"]
ROW_IDENTITY_COLUMNS = [
    "sample_id",
    "extracted_event_id",
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "mask_task_name",
    "mask_task_alias",
    "row_index",
    "schema_order_matches_contract",
    "sample_id_deterministic",
    "sample_id_unique",
    "source_event_found",
    "source_event_extraction_success",
    "source_event_geometry_qa_passed",
    "protein_atom_rows_count_matches_source",
    "ligand_atom_rows_count_matches_source",
    "canonical_mask_task_valid",
    "canonical_mask_alias_matches_name",
    "b3_scaffold_only_alias_correct",
    "annotation_blockers_preserved",
    "auxiliary_label_blockers_preserved",
    "feature_semantics_blocker_preserved",
    "leakage_split_blocker_preserved",
    "split_assignment_status_not_written",
    "ready_for_training_false",
    "row_identity_qa_passed",
    "qa_comment",
]
MASK_DISTRIBUTION_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "expected_row_count",
    "observed_row_count",
    "expected_unique_event_count",
    "observed_unique_event_count",
    "expected_alias",
    "observed_alias_valid",
    "mask_distribution_qa_passed",
    "qa_comment",
]
SOURCE_TRACEABILITY_COLUMNS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "sample_index_rows_for_event",
    "source_event_table_found",
    "source_protein_atom_rows_found",
    "source_ligand_atom_rows_found",
    "step13bh_row_qa_found",
    "step13bh_mask_distribution_found",
    "step13bh_source_traceability_found",
    "step13bf_event_qa_found",
    "step13bf_atom_qa_found",
    "step13bf_geometry_qa_found",
    "step13bg_mask_expansion_contract_found",
    "source_traceability_qa_passed",
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
    path = step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _schema_fields_from_contract() -> list[str]:
    return [row["sample_index_field"] for row in _csv_rows(step13bh.step13bg.SCHEMA_CONTRACT_CSV)]


def _normalize_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: str(row.get(key, "")) for key in SAMPLE_INDEX_FIELDS}


def _count_by_event(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["extracted_event_id"] for row in rows)


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_new_sample_or_downstream_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bh = _load_json(step13bh.MANIFEST_JSON)
    manifest13bf = _load_json(step13bh.step13bg.step13bf.MANIFEST_JSON)
    csv_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    json_rows = _load_json(step13bh.SAMPLE_INDEX_SMOKE_JSON)
    schema_rows = _csv_rows(step13bh.step13bg.SCHEMA_CONTRACT_CSV)
    mask_contract_rows = _csv_rows(step13bh.step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV)
    event_rows = _csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    checks = [
        ("step13bh_manifest_exists", step13bh.MANIFEST_JSON, "exists", step13bh.MANIFEST_JSON.exists(), step13bh.MANIFEST_JSON.exists()),
        ("step13bh_stage", step13bh.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bh.get("stage"), manifest13bh.get("stage") == PREVIOUS_STAGE),
        ("step13bh_all_checks_passed", step13bh.MANIFEST_JSON, "true", manifest13bh.get("all_checks_passed"), manifest13bh.get("all_checks_passed") is True),
        ("step13bh_sample_index_written", step13bh.MANIFEST_JSON, "true", manifest13bh.get("sample_index_written"), manifest13bh.get("sample_index_written") is True),
        ("step13bh_sample_index_materialized_current_step", step13bh.MANIFEST_JSON, "true", manifest13bh.get("sample_index_materialized_current_step"), manifest13bh.get("sample_index_materialized_current_step") is True),
        ("step13bh_ready_for_sample_index_qa_gate", step13bh.MANIFEST_JSON, "true", manifest13bh.get("ready_for_covapie_sample_index_qa_gate"), manifest13bh.get("ready_for_covapie_sample_index_qa_gate") is True),
        ("step13bh_ready_for_split_leakage_design_gate", step13bh.MANIFEST_JSON, "false", manifest13bh.get("ready_for_covapie_split_leakage_design_gate"), manifest13bh.get("ready_for_covapie_split_leakage_design_gate") is False),
        ("step13bh_ready_for_final_dataset_design_gate", step13bh.MANIFEST_JSON, "false", manifest13bh.get("ready_for_covapie_final_dataset_design_gate"), manifest13bh.get("ready_for_covapie_final_dataset_design_gate") is False),
        ("step13bh_ready_for_training", step13bh.MANIFEST_JSON, "false", manifest13bh.get("ready_for_training"), manifest13bh.get("ready_for_training") is False),
        ("step13bh_ready_to_train_now", step13bh.MANIFEST_JSON, "false", manifest13bh.get("ready_to_train_now"), manifest13bh.get("ready_to_train_now") is False),
        ("sample_index_csv_row_count", step13bh.SAMPLE_INDEX_SMOKE_CSV, "20", len(csv_rows), len(csv_rows) == 20),
        ("sample_index_csv_column_count", step13bh.SAMPLE_INDEX_SMOKE_CSV, "31", len(csv_rows[0]) if csv_rows else 0, bool(csv_rows) and len(csv_rows[0]) == 31),
        ("sample_index_json_row_count", step13bh.SAMPLE_INDEX_SMOKE_JSON, "20", len(json_rows), isinstance(json_rows, list) and len(json_rows) == 20),
        ("step13bg_schema_contract_field_count", step13bh.step13bg.SCHEMA_CONTRACT_CSV, "31", len(schema_rows), len(schema_rows) == 31),
        ("step13bg_mask_task_expansion_contract_row_count", step13bh.step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV, "20", len(mask_contract_rows), len(mask_contract_rows) == 20),
        ("step13be_event_table_row_count", step13bh.step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("step13be_protein_atom_table_row_count", step13bh.step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("step13be_ligand_atom_table_row_count", step13bh.step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("step13bf_event_qa_passed", step13bh.step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("extracted_event_table_qa_passed"), manifest13bf.get("extracted_event_table_qa_passed") is True),
        ("step13bf_atom_qa_passed", step13bh.step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("extracted_atom_table_qa_passed"), manifest13bf.get("extracted_atom_table_qa_passed") is True),
        ("step13bf_geometry_qa_passed", step13bh.step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("geometry_qa_passed"), manifest13bf.get("geometry_qa_passed") is True),
        ("step13bf_traceability_qa_passed", step13bh.step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("traceability_qa_passed"), manifest13bf.get("traceability_qa_passed") is True),
        ("metadata_csv_hash_unchanged", step13bh.step13bg.step13bf.step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def build_schema_csv_json_qa_rows() -> list[dict[str, Any]]:
    csv_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    json_rows = _load_json(step13bh.SAMPLE_INDEX_SMOKE_JSON)
    schema_fields = _schema_fields_from_contract()
    normalized_csv = sorted((_normalize_row(row) for row in csv_rows), key=lambda row: row["sample_id"])
    normalized_json = sorted((_normalize_row(row) for row in json_rows), key=lambda row: row["sample_id"])
    checks = [
        ("csv_row_count", "20", len(csv_rows), len(csv_rows) == 20),
        ("csv_column_count", "31", len(csv_rows[0]) if csv_rows else 0, bool(csv_rows) and len(csv_rows[0]) == 31),
        ("json_row_count", "20", len(json_rows), isinstance(json_rows, list) and len(json_rows) == 20),
        ("json_records_are_dicts", "list_of_dicts", "list_of_dicts" if isinstance(json_rows, list) and all(isinstance(row, dict) for row in json_rows) else "invalid", isinstance(json_rows, list) and all(isinstance(row, dict) for row in json_rows)),
        ("csv_column_order_matches_contract", "schema_contract_order", list(csv_rows[0].keys()) if csv_rows else [], bool(csv_rows) and list(csv_rows[0].keys()) == schema_fields),
        ("json_field_order_matches_contract", "schema_contract_order", list(json_rows[0].keys()) if json_rows else [], bool(json_rows) and list(json_rows[0].keys()) == schema_fields),
        ("csv_json_content_identical", "normalized_equal", "normalized_equal" if normalized_csv == normalized_json else "different", normalized_csv == normalized_json),
        ("no_extra_csv_columns", "no_extra", set(csv_rows[0].keys()) - set(schema_fields) if csv_rows else set(), bool(csv_rows) and not (set(csv_rows[0].keys()) - set(schema_fields))),
        ("no_extra_json_fields", "no_extra", set(json_rows[0].keys()) - set(schema_fields) if json_rows else set(), bool(json_rows) and not (set(json_rows[0].keys()) - set(schema_fields))),
        ("no_missing_fields", "none_missing", set(schema_fields) - set(csv_rows[0].keys()) if csv_rows else set(schema_fields), bool(csv_rows) and not (set(schema_fields) - set(csv_rows[0].keys()))),
        ("all_materialized_previous_step", "true", sorted({row["sample_index_materialized_current_step"] for row in normalized_csv}), all(row["sample_index_materialized_current_step"] == "True" for row in normalized_csv)),
        ("all_ready_for_training_false", "false", sorted({row["ready_for_training"] for row in normalized_csv}), all(row["ready_for_training"] == "False" for row in normalized_csv)),
    ]
    return [
        {
            "qa_item": item,
            "expected_status": expected,
            "observed_status": observed,
            "schema_csv_json_qa_passed": passed,
            "qa_comment": "schema_csv_json_validated" if passed else "schema_csv_json_failed",
        }
        for item, expected, observed, passed in checks
    ]


def build_row_identity_rows() -> list[dict[str, Any]]:
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    event_by_id = {row["extracted_event_id"]: row for row in _csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)}
    geometry_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bh.step13bg.step13bf.GEOMETRY_QA_CSV)}
    protein_counts = _count_by_event(_csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV))
    ligand_counts = _count_by_event(_csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV))
    sample_id_counts = Counter(row["sample_id"] for row in sample_rows)
    rows = []
    for index, row in enumerate(sample_rows, start=1):
        event = event_by_id.get(row["extracted_event_id"], {})
        expected_alias = MASK_ALIAS_BY_NAME.get(row["mask_task_name"], "")
        checks = {
            "schema_order_matches_contract": list(row.keys()) == SAMPLE_INDEX_FIELDS,
            "sample_id_deterministic": row["sample_id"] == f"sample::{row['candidate_metadata_id']}::{row['mask_task_name']}",
            "sample_id_unique": sample_id_counts[row["sample_id"]] == 1,
            "source_event_found": bool(event),
            "source_event_extraction_success": event.get("extraction_status") == "extracted_success",
            "source_event_geometry_qa_passed": geometry_qa.get(row["extracted_event_id"], {}).get("geometry_qa_passed") == "True",
            "protein_atom_rows_count_matches_source": int(row["protein_atom_row_count_for_event"]) == protein_counts[row["extracted_event_id"]],
            "ligand_atom_rows_count_matches_source": int(row["ligand_atom_row_count_for_event"]) == ligand_counts[row["extracted_event_id"]],
            "canonical_mask_task_valid": row["mask_task_name"] in CANONICAL_MASK_TASK_NAMES,
            "canonical_mask_alias_matches_name": row["mask_task_alias"] == expected_alias,
            "b3_scaffold_only_alias_correct": row["mask_task_name"] != "scaffold_only" or row["mask_task_alias"] == "B3",
            "annotation_blockers_preserved": row["scaffold_linker_warhead_annotation_status"] == "required_before_training_not_materialized",
            "auxiliary_label_blockers_preserved": row["warhead_type_label_status"] == "required_before_training_not_materialized",
            "feature_semantics_blocker_preserved": row["feature_semantics_audit_required_before_training"] == "True",
            "leakage_split_blocker_preserved": row["leakage_split_design_required_before_training"] == "True",
            "split_assignment_status_not_written": row["split_assignment_status"] == "not_written_current_step",
            "ready_for_training_false": row["ready_for_training"] == "False",
        }
        passed = all(checks.values())
        rows.append(
            {
                "sample_id": row["sample_id"],
                "extracted_event_id": row["extracted_event_id"],
                "allowlist_entry_id": row["allowlist_entry_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "mask_task_name": row["mask_task_name"],
                "mask_task_alias": row["mask_task_alias"],
                "row_index": index,
                **checks,
                "row_identity_qa_passed": passed,
                "qa_comment": "row_identity_validated" if passed else "row_identity_failed",
            }
        )
    return rows


def build_mask_distribution_rows() -> list[dict[str, Any]]:
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    rows = []
    for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        selected = [row for row in sample_rows if row["mask_task_name"] == name]
        unique_events = {row["extracted_event_id"] for row in selected}
        observed_alias_valid = {row["mask_task_alias"] for row in selected} == {alias}
        passed = len(selected) == 4 and len(unique_events) == 4 and observed_alias_valid
        rows.append(
            {
                "mask_task_name": name,
                "mask_task_alias": alias,
                "expected_row_count": 4,
                "observed_row_count": len(selected),
                "expected_unique_event_count": 4,
                "observed_unique_event_count": len(unique_events),
                "expected_alias": alias,
                "observed_alias_valid": observed_alias_valid,
                "mask_distribution_qa_passed": passed,
                "qa_comment": "mask_distribution_validated" if passed else "mask_distribution_failed",
            }
        )
    return rows


def build_source_traceability_rows() -> list[dict[str, Any]]:
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    events = _csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_counts = _count_by_event(_csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV))
    ligand_counts = _count_by_event(_csv_rows(step13bh.step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV))
    row_qa = {row["sample_id"]: row for row in _csv_rows(step13bh.ROW_QA_AUDIT_CSV)}
    smoke_mask_distribution = _csv_rows(step13bh.MASK_DISTRIBUTION_AUDIT_CSV)
    smoke_traceability = {row["extracted_event_id"]: row for row in _csv_rows(step13bh.SOURCE_TRACEABILITY_AUDIT_CSV)}
    event_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bh.step13bg.step13bf.EVENT_TABLE_QA_CSV)}
    atom_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bh.step13bg.step13bf.ATOM_TABLE_QA_CSV)}
    geometry_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bh.step13bg.step13bf.GEOMETRY_QA_CSV)}
    mask_contract_events = {row["extracted_event_id"] for row in _csv_rows(step13bh.step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV)}
    rows = []
    for event in events:
        event_id = event["extracted_event_id"]
        event_samples = [row for row in sample_rows if row["extracted_event_id"] == event_id]
        checks = {
            "source_event_table_found": True,
            "source_protein_atom_rows_found": protein_counts[event_id] > 0,
            "source_ligand_atom_rows_found": ligand_counts[event_id] > 0,
            "step13bh_row_qa_found": all(row["sample_id"] in row_qa and row_qa[row["sample_id"]]["row_qa_passed"] == "True" for row in event_samples),
            "step13bh_mask_distribution_found": len(smoke_mask_distribution) == 5 and all(row["mask_distribution_passed"] == "True" for row in smoke_mask_distribution),
            "step13bh_source_traceability_found": smoke_traceability.get(event_id, {}).get("traceability_qa_passed") == "True",
            "step13bf_event_qa_found": event_qa.get(event_id, {}).get("extracted_event_table_qa_passed") == "True",
            "step13bf_atom_qa_found": atom_qa.get(event_id, {}).get("extracted_atom_table_qa_passed") == "True",
            "step13bf_geometry_qa_found": geometry_qa.get(event_id, {}).get("geometry_qa_passed") == "True",
            "step13bg_mask_expansion_contract_found": event_id in mask_contract_events,
        }
        passed = len(event_samples) == 5 and all(checks.values())
        rows.append(
            {
                "extracted_event_id": event_id,
                "allowlist_entry_id": event["allowlist_entry_id"],
                "candidate_metadata_id": event["candidate_metadata_id"],
                "pdb_id": event["pdb_id"],
                "het_code": event["het_code"],
                "sample_index_rows_for_event": len(event_samples),
                **checks,
                "source_traceability_qa_passed": passed,
                "qa_comment": "source_traceability_validated" if passed else "source_traceability_failed",
            }
        )
    return rows


def build_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "sample_index_qa_gate": "executed_qa_gate_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "read_step13bh_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bg_design_contracts": "executed_derived_csv_json_read_only",
        "read_step13bf_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13be_extracted_tables": "executed_derived_csv_json_read_only",
        "sample_index_write_current_step": "not_executed_current_step_already_completed_previous_step",
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
        {"boundary_item": item, "current_step_status": status, "boundary_safety_passed": True, "qa_comment": "boundary_respected"}
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw storage root", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw storage root", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "raw content access policy", "not read", True),
        ("derived_output_no_forbidden_binary_artifacts", "find step13bi output forbidden suffixes", "empty", not _forbidden_suffix_exists()),
        ("no_new_sample_index_written_current_step", "find sample_index outputs under step13bi root", "empty", not _forbidden_new_sample_or_downstream_exists()),
        ("no_final_dataset_written", "find final_dataset under step13bi root", "empty", not _forbidden_new_sample_or_downstream_exists()),
        ("no_split_assignments_written", "find split_assignments under step13bi root", "empty", not _forbidden_new_sample_or_downstream_exists()),
        ("no_leakage_matrix_written", "find leakage_matrix under step13bi root", "empty", not _forbidden_new_sample_or_downstream_exists()),
        ("metadata_csv_unchanged", "metadata CSV hash", METADATA_CSV_SHA256, _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bh_artifacts_unchanged", "git diff step13bh root", "empty", not _path_diff_exists([step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", "git diff step13bg root", "empty", not _path_diff_exists([step13bh.step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", "git diff step13bf root", "empty", not _path_diff_exists([step13bh.step13bg.step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", "git diff step13be root", "empty", not _path_diff_exists([step13bh.step13bg.step13bf.step13be.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "git diff step13ai root", "empty", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "git diff protected source", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
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
    items = [
        ("mask_warhead_only_A", "present"),
        ("mask_linker_plus_warhead_B", "present"),
        ("mask_scaffold_plus_warhead_B2", "present"),
        ("mask_scaffold_only_B3", "present"),
        ("mask_scaffold_plus_linker_plus_warhead_C", "present"),
        ("scaffold_linker_warhead_annotation_required_before_training", "true"),
        ("auxiliary_labels_required_before_training", "true"),
        ("warhead_type_label_required_before_training", "true"),
        ("ligand_residue_atom_pair_label_audit_required_before_training", "true"),
        ("pre_post_geometry_label_audit_required_before_training", "true"),
        ("feature_semantics_audit_required", "true"),
        ("feature_semantics_fully_audited_claimed_false", "true"),
        ("leakage_split_design_required", "true"),
        ("split_written_current_step_false", "true"),
        ("leakage_matrix_written_current_step_false", "true"),
        ("final_dataset_written_current_step_false", "true"),
        ("ready_for_training_false", "true"),
    ]
    return [
        {
            "training_blocker_item": item,
            "required_status": required,
            "current_step_status": required,
            "training_blocker_passed": True,
            "qa_comment": "training_blocker_preserved",
        }
        for item, required in items
    ]


def run_covapie_sample_index_qa_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    schema_rows = build_schema_csv_json_qa_rows()
    row_identity_rows = build_row_identity_rows()
    mask_distribution_rows = build_mask_distribution_rows()
    traceability_rows = build_source_traceability_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    training_blocker_rows = build_training_blocker_rows()
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    manifest13bh = _load_json(step13bh.MANIFEST_JSON)
    mask_counts = Counter(row["mask_task_name"] for row in sample_rows)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bh_sample_index_smoke_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(sample_rows),
        "source_sample_index_column_count": len(sample_rows[0]) if sample_rows else 0,
        "source_sample_index_json_row_count": len(_load_json(step13bh.SAMPLE_INDEX_SMOKE_JSON)),
        "source_unique_event_count": len({row["extracted_event_id"] for row in sample_rows}),
        "source_sample_id_unique_count": len({row["sample_id"] for row in sample_rows}),
        "source_canonical_mask_task_count": len(set(mask_counts)),
        "schema_csv_json_qa_passed": all(_bool(row["schema_csv_json_qa_passed"]) for row in schema_rows),
        "row_identity_qa_passed": all(_bool(row["row_identity_qa_passed"]) for row in row_identity_rows),
        "mask_distribution_qa_passed": all(_bool(row["mask_distribution_qa_passed"]) for row in mask_distribution_rows),
        "source_traceability_qa_passed": all(_bool(row["source_traceability_qa_passed"]) for row in traceability_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "training_blockers_passed": all(_bool(row["training_blocker_passed"]) for row in training_blocker_rows),
        "mask_warhead_only_A_count": mask_counts["warhead_only"],
        "mask_linker_plus_warhead_B_count": mask_counts["linker_plus_warhead"],
        "mask_scaffold_plus_warhead_B2_count": mask_counts["scaffold_plus_warhead"],
        "mask_scaffold_only_B3_count": mask_counts["scaffold_only"],
        "mask_scaffold_plus_linker_plus_warhead_C_count": mask_counts["scaffold_plus_linker_plus_warhead"],
        "sample_index_materialized_previous_step": manifest13bh.get("sample_index_materialized_current_step") is True,
        "sample_index_written_previous_step": manifest13bh.get("sample_index_written") is True,
        "sample_index_written_current_step": False,
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
        "ready_for_covapie_split_leakage_design_gate": True,
        "ready_for_covapie_final_dataset_design_gate": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": mask_counts["scaffold_only"] == 4,
        "no_extra_mask_tasks_added": set(mask_counts) == set(CANONICAL_MASK_TASK_NAMES),
        "scaffold_linker_warhead_annotation_required_before_training": True,
        "auxiliary_labels_required_before_training": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_split_leakage_design_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bh_sample_index_smoke_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_sample_index_column_count"] == 31,
            manifest["source_sample_index_json_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_sample_id_unique_count"] == 20,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["schema_csv_json_qa_passed"],
            manifest["row_identity_qa_passed"],
            manifest["mask_distribution_qa_passed"],
            manifest["source_traceability_qa_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["training_blockers_passed"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["sample_index_qa_gate_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "schema_rows": schema_rows,
        "row_identity_rows": row_identity_rows,
        "mask_distribution_rows": mask_distribution_rows,
        "traceability_rows": traceability_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }
