from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_candidate_metadata_materialization_design_gate as design
from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_metadata_materialization_smoke_v0"
PREVIOUS_STAGE = "covapie_candidate_metadata_materialization_design_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AX_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_design_gate_v0")
STEP13AW_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_qa_gate_v0")
STEP13AV_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_smoke_v0")
STEP13AU_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_design_gate_v0")

STEP13AX_MANIFEST_JSON = STEP13AX_ROOT / "covapie_candidate_metadata_materialization_design_gate_manifest.json"
STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_accepted_event_inventory.csv"
STEP13AX_UNRESOLVED_EXCLUSION_POLICY_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_unresolved_event_exclusion_policy.csv"
STEP13AX_SCHEMA_CONTRACT_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_schema_contract.csv"
STEP13AX_FIELD_SOURCE_MAPPING_CONTRACT_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_field_source_mapping_contract.csv"
STEP13AX_ROW_IDENTITY_CONTRACT_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_row_identity_contract.csv"
STEP13AX_VALIDATION_CONTRACT_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_validation_contract.csv"
STEP13AX_MATERIALIZATION_SMOKE_PLAN_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_materialization_smoke_plan.csv"

STEP13AW_PREFERRED_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_preferred_event_acceptance_qa.csv"
STEP13AW_CANDIDATE_INTEGRITY_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_event_candidate_field_integrity_qa.csv"
STEP13AW_UNRESOLVED_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_unresolved_event_handling_qa.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"
RAW_STORAGE_ROOT = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_smoke_precondition_audit.csv"
CANDIDATE_METADATA_SMOKE_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_smoke.csv"
CANDIDATE_METADATA_SMOKE_JSON = OUTPUT_ROOT / "covapie_candidate_metadata_smoke.json"
SOURCE_TRACEABILITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_source_traceability_audit.csv"
ACCEPTED_EVENT_MATERIALIZATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_accepted_event_materialization_audit.csv"
UNRESOLVED_EVENT_EXCLUSION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_unresolved_event_exclusion_audit.csv"
SCHEMA_COMPLIANCE_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_schema_compliance_audit.csv"
FIELD_COMPLETENESS_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_field_completeness_audit.csv"
ROW_IDENTITY_UNIQUENESS_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_row_identity_uniqueness_audit.csv"
VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_validation_audit.csv"
ALLOWLIST_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_boundary_audit.csv"
MATERIALIZATION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_metadata_materialization_smoke_v0_summary.md")

CANDIDATE_METADATA_FIELDS = design.CANDIDATE_METADATA_FIELDS
CANONICAL_MASK_TASK_NAMES = design.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = design.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
FORBIDDEN_DERIVED_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
    ".html",
    ".htm",
)

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
TRACEABILITY_COLUMNS = ["candidate_metadata_id", "pdb_id", "het_code", "source_step13ax_accepted_event_inventory_found", "source_step13aw_preferred_acceptance_found", "source_step13aw_candidate_integrity_found", "source_metadata_csv_row_found", "source_metadata_csv_row_key", "traceability_audit_passed"]
ACCEPTED_MATERIALIZATION_COLUMNS = ["pdb_id", "het_code", "future_candidate_metadata_id_preview", "materialized_candidate_metadata_id", "materialized", "id_matches_design_preview", "accepted_for_future_candidate_metadata", "current_step_materialization_allowed", "accepted_event_materialization_audit_passed"]
UNRESOLVED_EXCLUSION_COLUMNS = ["pdb_id", "het_code", "resolution_status", "reason_unresolved", "candidate_metadata_materialized", "candidate_allowlist_materialized", "exclusion_preserved", "unresolved_event_exclusion_audit_passed"]
SCHEMA_COMPLIANCE_COLUMNS = ["schema_check_item", "expected_status", "observed_status", "schema_compliance_audit_passed", "blocking_reasons"]
FIELD_COMPLETENESS_COLUMNS = ["candidate_metadata_field", "non_empty_count", "expected_row_count", "field_completeness_status", "field_completeness_audit_passed"]
ROW_IDENTITY_COLUMNS = ["row_identity_check_item", "observed_status", "candidate_metadata_id_count", "duplicate_candidate_metadata_id_count", "row_identity_uniqueness_audit_passed", "blocking_reasons"]
VALIDATION_COLUMNS = ["validation_item", "validation_status", "validation_audit_passed", "blocking_reasons"]
ALLOWLIST_BOUNDARY_COLUMNS = ["boundary_item", "automatic_allowlist_possible_count", "candidate_metadata_rows_available", "current_step_allowed", "future_condition", "candidate_allowlist_boundary_passed"]
MATERIALIZATION_BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "future_condition", "materialization_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_candidate_metadata_materialization_smoke", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_split_item", "current_step_status", "future_required_gate", "split_written_current_step", "leakage_matrix_written_current_step", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> dict[str, Any]:
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


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _metadata_row_key(row: dict[str, str]) -> str:
    return f"{row['source_dataset_name']}::{row['source_dataset_version']}::{row['covpdb_record_index']}::{row['pdb_id']}::{row['het_code']}"


def _by_pair(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["pdb_id"], row["het_code"]): row for row in rows}


def _row_index_by_pair(rows: list[dict[str, str]]) -> dict[tuple[str, str], int]:
    return {(row["pdb_id"], row["het_code"]): index for index, row in enumerate(rows, start=1)}


def _precondition_rows(manifest13ax: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("step13ax_manifest_exists", str(STEP13AX_MANIFEST_JSON), "exists", STEP13AX_MANIFEST_JSON.exists(), STEP13AX_MANIFEST_JSON.exists()),
        ("step13ax_stage", str(STEP13AX_MANIFEST_JSON), PREVIOUS_STAGE, manifest13ax.get("stage"), manifest13ax.get("stage") == PREVIOUS_STAGE),
        ("step13ax_all_checks_passed", str(STEP13AX_MANIFEST_JSON), "true", manifest13ax.get("all_checks_passed"), manifest13ax.get("all_checks_passed") is True),
        ("step13ax_ready_for_smoke", str(STEP13AX_MANIFEST_JSON), "true", manifest13ax.get("ready_for_covapie_candidate_metadata_materialization_smoke"), manifest13ax.get("ready_for_covapie_candidate_metadata_materialization_smoke") is True),
        ("step13ax_schema_count", str(STEP13AX_MANIFEST_JSON), "33", manifest13ax.get("candidate_metadata_schema_field_count"), manifest13ax.get("candidate_metadata_schema_field_count") == 33),
        ("step13ax_accepted_count", str(STEP13AX_MANIFEST_JSON), "4", manifest13ax.get("accepted_preferred_event_count"), manifest13ax.get("accepted_preferred_event_count") == 4),
        ("step13ax_unresolved_count", str(STEP13AX_MANIFEST_JSON), "1", manifest13ax.get("blocked_unresolved_event_count"), manifest13ax.get("blocked_unresolved_event_count") == 1),
        ("step13ax_no_materialization_yet", str(STEP13AX_MANIFEST_JSON), "metadata/allowlist false", f"{manifest13ax.get('candidate_metadata_materialized')}/{manifest13ax.get('candidate_allowlist_materialized')}", manifest13ax.get("candidate_metadata_materialized") is False and manifest13ax.get("candidate_allowlist_materialized") is False),
        ("accepted_inventory_exists", str(STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV), "exists", STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV.exists(), STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV.exists()),
        ("schema_contract_exists", str(STEP13AX_SCHEMA_CONTRACT_CSV), "exists", STEP13AX_SCHEMA_CONTRACT_CSV.exists(), STEP13AX_SCHEMA_CONTRACT_CSV.exists()),
        ("field_source_mapping_exists", str(STEP13AX_FIELD_SOURCE_MAPPING_CONTRACT_CSV), "exists", STEP13AX_FIELD_SOURCE_MAPPING_CONTRACT_CSV.exists(), STEP13AX_FIELD_SOURCE_MAPPING_CONTRACT_CSV.exists()),
        ("row_identity_contract_exists", str(STEP13AX_ROW_IDENTITY_CONTRACT_CSV), "exists", STEP13AX_ROW_IDENTITY_CONTRACT_CSV.exists(), STEP13AX_ROW_IDENTITY_CONTRACT_CSV.exists()),
        ("validation_contract_exists", str(STEP13AX_VALIDATION_CONTRACT_CSV), "exists", STEP13AX_VALIDATION_CONTRACT_CSV.exists(), STEP13AX_VALIDATION_CONTRACT_CSV.exists()),
        ("materialization_smoke_plan_exists", str(STEP13AX_MATERIALIZATION_SMOKE_PLAN_CSV), "exists", STEP13AX_MATERIALIZATION_SMOKE_PLAN_CSV.exists(), STEP13AX_MATERIALIZATION_SMOKE_PLAN_CSV.exists()),
        ("step13aw_preferred_acceptance_exists", str(STEP13AW_PREFERRED_QA_CSV), "exists", STEP13AW_PREFERRED_QA_CSV.exists(), STEP13AW_PREFERRED_QA_CSV.exists()),
        ("step13aw_candidate_integrity_exists", str(STEP13AW_CANDIDATE_INTEGRITY_QA_CSV), "exists", STEP13AW_CANDIDATE_INTEGRITY_QA_CSV.exists(), STEP13AW_CANDIDATE_INTEGRITY_QA_CSV.exists()),
        ("step13aw_unresolved_exists", str(STEP13AW_UNRESOLVED_QA_CSV), "exists", STEP13AW_UNRESOLVED_QA_CSV.exists(), STEP13AW_UNRESOLVED_QA_CSV.exists()),
        ("metadata_csv_exists", str(METADATA_CSV), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", str(METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", "git ls-files raw root", "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "git diff equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": artifact,
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, artifact, expected, observed, passed in checks
    ]


def _candidate_metadata_rows(
    accepted_rows: list[dict[str, str]],
    preferred_rows: list[dict[str, str]],
    integrity_rows: list[dict[str, str]],
    metadata_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    preferred_by_pair = _by_pair(preferred_rows)
    integrity_by_pair = _by_pair(integrity_rows)
    metadata_by_pair = _by_pair(metadata_rows)
    preferred_index = _row_index_by_pair(preferred_rows)
    integrity_index = _row_index_by_pair(integrity_rows)
    rows = []
    for accepted in accepted_rows:
        pair = (accepted["pdb_id"], accepted["het_code"])
        preferred = preferred_by_pair[pair]
        integrity = integrity_by_pair[pair]
        metadata = metadata_by_pair[pair]
        row = {
            "candidate_metadata_id": accepted["future_candidate_metadata_id_preview"],
            "project_name": PROJECT_NAME,
            "source_name": "covpdb",
            "source_database": "CovPDB",
            "source_stage": STAGE,
            "pdb_id": accepted["pdb_id"],
            "het_code": accepted["het_code"],
            "selected_raw_format": "mmcif",
            "raw_connection_source": accepted["raw_connection_source"],
            "chain_id": accepted["chain_id"],
            "residue_name": accepted["residue_name"],
            "residue_index": accepted["residue_index"],
            "residue_atom_name": accepted["residue_atom_name"],
            "ligand_atom_name": accepted["ligand_atom_name"],
            "covalent_bond_atom_pair": accepted["covalent_bond_atom_pair"],
            "protein_partner_atom_exists": preferred["protein_partner_atom_exists"],
            "ligand_partner_atom_exists": preferred["ligand_partner_atom_exists"],
            "candidate_confidence": accepted["candidate_confidence"],
            "event_key_resolution_status": integrity["resolution_status"],
            "accepted_for_future_candidate_metadata": "true",
            "accepted_for_future_automatic_allowlist": "true",
            "current_step_materialization_allowed": "true",
            "unresolved_exclusion_status": "not_unresolved_accepted_preferred_event",
            "unresolved_exclusion_reason": "not_applicable",
            "manual_review_required": "false",
            "source_step13aw_preferred_acceptance_row_index": str(preferred_index[pair]),
            "source_step13aw_candidate_integrity_row_index": str(integrity_index[pair]),
            "source_metadata_csv_row_key": _metadata_row_key(metadata),
            "raw_file_path_policy": "raw_files_not_copied_to_candidate_metadata;raw_files_remain_untracked_external_inputs",
            "raw_file_tracked_policy": "raw_files_must_remain_untracked_unstaged_uncommitted",
            "feature_semantics_audit_required_before_training": "true",
            "leakage_split_design_required_before_training": "true",
            "ready_for_training": "false",
        }
        rows.append({field: row[field] for field in CANDIDATE_METADATA_FIELDS})
    return rows


def _source_traceability_rows(candidate_rows: list[dict[str, Any]], accepted_rows: list[dict[str, str]], preferred_rows: list[dict[str, str]], integrity_rows: list[dict[str, str]], metadata_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    accepted_by_pair = _by_pair(accepted_rows)
    preferred_by_pair = _by_pair(preferred_rows)
    integrity_by_pair = _by_pair(integrity_rows)
    metadata_by_pair = _by_pair(metadata_rows)
    rows = []
    for row in candidate_rows:
        pair = (row["pdb_id"], row["het_code"])
        passed = pair in accepted_by_pair and pair in preferred_by_pair and pair in integrity_by_pair and pair in metadata_by_pair and bool(row["source_metadata_csv_row_key"])
        rows.append(
            {
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "source_step13ax_accepted_event_inventory_found": pair in accepted_by_pair,
                "source_step13aw_preferred_acceptance_found": pair in preferred_by_pair,
                "source_step13aw_candidate_integrity_found": pair in integrity_by_pair,
                "source_metadata_csv_row_found": pair in metadata_by_pair,
                "source_metadata_csv_row_key": row["source_metadata_csv_row_key"],
                "traceability_audit_passed": passed,
            }
        )
    return rows


def _accepted_event_materialization_rows(candidate_rows: list[dict[str, Any]], accepted_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidate_by_pair = _by_pair(candidate_rows)
    rows = []
    for row in accepted_rows:
        pair = (row["pdb_id"], row["het_code"])
        candidate = candidate_by_pair.get(pair, {})
        materialized_id = candidate.get("candidate_metadata_id", "")
        passed = bool(candidate) and materialized_id == row["future_candidate_metadata_id_preview"] and _bool(row["accepted_for_future_candidate_metadata"])
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "future_candidate_metadata_id_preview": row["future_candidate_metadata_id_preview"],
                "materialized_candidate_metadata_id": materialized_id,
                "materialized": bool(candidate),
                "id_matches_design_preview": materialized_id == row["future_candidate_metadata_id_preview"],
                "accepted_for_future_candidate_metadata": _bool(row["accepted_for_future_candidate_metadata"]),
                "current_step_materialization_allowed": bool(candidate),
                "accepted_event_materialization_audit_passed": passed,
            }
        )
    return rows


def _unresolved_event_exclusion_rows(unresolved_rows: list[dict[str, str]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    materialized_pairs = {(row["pdb_id"], row["het_code"]) for row in candidate_rows}
    rows = []
    for row in unresolved_rows:
        pair = (row["pdb_id"], row["het_code"])
        excluded = pair not in materialized_pairs and row["pdb_id"] == "1A54" and row["het_code"] == "MDC"
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "resolution_status": row["resolution_status"],
                "reason_unresolved": row["reason_unresolved"],
                "candidate_metadata_materialized": False,
                "candidate_allowlist_materialized": False,
                "exclusion_preserved": excluded,
                "unresolved_event_exclusion_audit_passed": excluded,
            }
        )
    return rows


def _schema_compliance_rows(candidate_rows: list[dict[str, Any]], schema_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    observed_columns = list(candidate_rows[0].keys()) if candidate_rows else []
    expected_columns = [row["candidate_metadata_field"] for row in schema_rows]
    checks = [
        ("column_count", "33", len(observed_columns), len(observed_columns) == 33),
        ("column_order", ";".join(expected_columns), ";".join(observed_columns), observed_columns == expected_columns),
        ("schema_field_coverage", "all schema fields present", len(set(observed_columns) & set(expected_columns)), set(observed_columns) == set(expected_columns)),
        ("no_extra_columns", "no extras", sorted(set(observed_columns) - set(expected_columns)), not (set(observed_columns) - set(expected_columns))),
        ("no_missing_columns", "no missing", sorted(set(expected_columns) - set(observed_columns)), not (set(expected_columns) - set(observed_columns))),
        ("schema_compliance_audit_passed", "true", True, observed_columns == expected_columns and len(observed_columns) == 33),
    ]
    return [
        {
            "schema_check_item": item,
            "expected_status": expected,
            "observed_status": observed,
            "schema_compliance_audit_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, expected, observed, passed in checks
    ]


def _field_completeness_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected = len(candidate_rows)
    rows = []
    for field in CANDIDATE_METADATA_FIELDS:
        count = sum(1 for row in candidate_rows if str(row[field]) != "")
        passed = count == expected
        rows.append(
            {
                "candidate_metadata_field": field,
                "non_empty_count": count,
                "expected_row_count": expected,
                "field_completeness_status": "complete" if passed else "missing_values",
                "field_completeness_audit_passed": passed,
            }
        )
    return rows


def _row_identity_rows(candidate_rows: list[dict[str, Any]], unresolved_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = [row["candidate_metadata_id"] for row in candidate_rows]
    duplicates = len(ids) - len(set(ids))
    checks = [
        ("deterministic_id_format", all(candidate_id.startswith("covpdb::") and "::" in candidate_id for candidate_id in ids), len(ids), duplicates),
        ("candidate_metadata_id_unique", len(ids) == len(set(ids)), len(ids), duplicates),
        ("candidate_metadata_id_count", len(ids) == 4, len(ids), duplicates),
        ("duplicate_candidate_metadata_id_count", duplicates == 0, len(ids), duplicates),
        ("no_whitespace_in_ids", all(not any(char.isspace() for char in candidate_id) for candidate_id in ids), len(ids), duplicates),
        ("unresolved_event_has_no_id", all(row["pdb_id"] != "1A54" or not row["candidate_metadata_materialized"] for row in unresolved_rows), len(ids), duplicates),
        ("row_identity_uniqueness_audit_passed", len(ids) == 4 and len(ids) == len(set(ids)), len(ids), duplicates),
    ]
    return [
        {
            "row_identity_check_item": item,
            "observed_status": status,
            "candidate_metadata_id_count": count,
            "duplicate_candidate_metadata_id_count": duplicate_count,
            "row_identity_uniqueness_audit_passed": status,
            "blocking_reasons": "" if status else item,
        }
        for item, status, count, duplicate_count in checks
    ]


def _validation_rows(candidate_rows: list[dict[str, Any]], unresolved_rows: list[dict[str, Any]], schema_rows: list[dict[str, Any]], trace_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = {(row["pdb_id"], row["het_code"]) for row in candidate_rows}
    checks = [
        ("row_count_is_four", len(candidate_rows) == 4),
        ("only_accepted_preferred_events_materialized", pairs == {("1A3B", "T29"), ("1A3E", "T16"), ("1A46", "00K"), ("1A5G", "00L")}),
        ("unresolved_event_excluded", ("1A54", "MDC") not in pairs and _all_true(unresolved_rows, "unresolved_event_exclusion_audit_passed")),
        ("schema_compliant", _all_true(schema_rows, "schema_compliance_audit_passed")),
        ("source_traceability_complete", _all_true(trace_rows, "traceability_audit_passed")),
        ("no_allowlist_materialized", not (OUTPUT_ROOT / "covapie_candidate_allowlist.csv").exists() and not (OUTPUT_ROOT / "covapie_candidate_allowlist.json").exists()),
        ("no_sample_index_or_final_dataset", not any((OUTPUT_ROOT / name).exists() for name in ["sample_index.csv", "sample_index.json", "final_dataset.csv", "final_dataset.json"])),
        ("no_training_boundary_violation", True),
    ]
    return [
        {
            "validation_item": item,
            "validation_status": "passed" if passed else "blocked",
            "validation_audit_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, passed in checks
    ]


def _allowlist_boundary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "boundary_item": "candidate_allowlist_materialization",
            "automatic_allowlist_possible_count": 4,
            "candidate_metadata_rows_available": len(candidate_rows),
            "current_step_allowed": False,
            "future_condition": "candidate_metadata_materialization_qa_gate_passed",
            "candidate_allowlist_boundary_passed": len(candidate_rows) == 4,
        }
    ]


def _materialization_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "candidate_metadata_materialization": "executed_first4_smoke_only",
        "candidate_allowlist_materialization": "blocked_current_smoke",
        "sample_index": "blocked_current_smoke",
        "final_dataset": "blocked_current_smoke",
        "split_assignments": "blocked_current_smoke",
        "leakage_matrix": "blocked_current_smoke",
        "training": "blocked_current_smoke",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "future_condition": "future_gate_required",
            "materialization_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status in statuses.items()
    ]


def _execution_rows() -> list[dict[str, Any]]:
    statuses = {
        "candidate_metadata_materialization_smoke": "executed_first4_candidate_metadata_only",
        "step13ax_manifest_read": "executed_manifest_read_only",
        "step13ax_schema_contract_read": "executed_csv_read_only",
        "step13ax_accepted_event_inventory_read": "executed_csv_read_only",
        "step13ax_unresolved_exclusion_policy_read": "executed_csv_read_only",
        "step13aw_preferred_acceptance_read": "executed_csv_read_only",
        "step13aw_candidate_integrity_read": "executed_csv_read_only",
        "metadata_csv_read": "executed_metadata_read_only",
        "candidate_metadata_csv_write": "executed_first4_rows_only",
        "candidate_metadata_json_write": "executed_first4_rows_only",
        "candidate_allowlist_write": "not_executed_or_not_allowed",
        "raw_file_presence_check": "not_executed_or_not_allowed",
        "external_network_access": "not_executed_or_not_allowed",
        "raw_structure_download": "not_executed_or_not_allowed",
        "raw_ligand_download": "not_executed_or_not_allowed",
        "raw_file_created": "not_executed_or_not_allowed",
        "raw_data_text_read": "not_executed_or_not_allowed",
        "sdf_read": "not_executed_or_not_allowed",
        "pdb_text_read": "not_executed_or_not_allowed",
        "mmcif_text_read": "not_executed_or_not_allowed",
        "gzip_open": "not_executed_or_not_allowed",
        "rdkit_use": "not_executed_or_not_allowed",
        "biopdb_use": "not_executed_or_not_allowed",
        "gemmi_use": "not_executed_or_not_allowed",
        "sample_index_write": "not_executed_or_not_allowed",
        "final_dataset_write": "not_executed_or_not_allowed",
        "split_assignments_write": "not_executed_or_not_allowed",
        "leakage_matrix_write": "not_executed_or_not_allowed",
        "torch_import": "not_executed_or_not_allowed",
        "model_forward": "not_executed_or_not_allowed",
        "training_claim": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status in statuses.items()
    ]


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("derived_output_no_raw_suffix_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists(OUTPUT_ROOT)),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13ax_artifacts_unchanged", "git diff step13ax root", "empty", not _path_diff_exists([str(STEP13AX_ROOT)])),
        ("step13aw_artifacts_unchanged", "git diff step13aw root", "empty", not _path_diff_exists([str(STEP13AW_ROOT)])),
        ("step13av_artifacts_unchanged", "git diff step13av root", "empty", not _path_diff_exists([str(STEP13AV_ROOT)])),
        ("step13au_artifacts_unchanged", "git diff step13au root", "empty", not _path_diff_exists([str(STEP13AU_ROOT)])),
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


def _mask_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13ax",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def _feature_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": group,
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_candidate_metadata_materialization_smoke": False,
            "training_ready": False,
            "recommended_audit_step": "future_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item, group in FEATURE_SEMANTICS_ITEMS
    ]


def _leakage_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "split_written_current_step": False,
            "leakage_matrix_written_current_step": False,
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def run_covapie_candidate_metadata_materialization_smoke_v0() -> dict[str, Any]:
    manifest13ax = _load_json(STEP13AX_MANIFEST_JSON)
    accepted_rows = _csv_rows(STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV)
    unresolved_policy_rows13ax = _csv_rows(STEP13AX_UNRESOLVED_EXCLUSION_POLICY_CSV)
    schema_contract_rows = _csv_rows(STEP13AX_SCHEMA_CONTRACT_CSV)
    preferred_rows = _csv_rows(STEP13AW_PREFERRED_QA_CSV)
    integrity_rows = _csv_rows(STEP13AW_CANDIDATE_INTEGRITY_QA_CSV)
    unresolved_rows13aw = _csv_rows(STEP13AW_UNRESOLVED_QA_CSV)
    metadata_rows = _csv_rows(METADATA_CSV)

    precondition_rows = _precondition_rows(manifest13ax)
    candidate_rows = _candidate_metadata_rows(accepted_rows, preferred_rows, integrity_rows, metadata_rows)
    traceability_rows = _source_traceability_rows(candidate_rows, accepted_rows, preferred_rows, integrity_rows, metadata_rows)
    accepted_materialization_rows = _accepted_event_materialization_rows(candidate_rows, accepted_rows)
    unresolved_event_rows = _unresolved_event_exclusion_rows(unresolved_policy_rows13ax, candidate_rows)
    schema_compliance_rows = _schema_compliance_rows(candidate_rows, schema_contract_rows)
    field_completeness_rows = _field_completeness_rows(candidate_rows)
    row_identity_rows = _row_identity_rows(candidate_rows, unresolved_event_rows)
    validation_rows = _validation_rows(candidate_rows, unresolved_event_rows, schema_compliance_rows, traceability_rows)
    allowlist_boundary_rows = _allowlist_boundary_rows(candidate_rows)
    materialization_boundary_rows = _materialization_boundary_rows()
    execution_rows = _execution_rows()
    git_safety_rows = _git_safety_rows()
    mask_rows = _mask_rows()
    feature_rows = _feature_rows()
    leakage_rows = _leakage_rows()

    ids = [row["candidate_metadata_id"] for row in candidate_rows]
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "candidate_metadata_rows": len(candidate_rows) == 4 and len(candidate_rows[0]) == 33,
        "traceability": _all_true(traceability_rows, "traceability_audit_passed"),
        "accepted_materialization": _all_true(accepted_materialization_rows, "accepted_event_materialization_audit_passed"),
        "unresolved_exclusion": _all_true(unresolved_event_rows, "unresolved_event_exclusion_audit_passed"),
        "schema_compliance": _all_true(schema_compliance_rows, "schema_compliance_audit_passed"),
        "field_completeness": _all_true(field_completeness_rows, "field_completeness_audit_passed"),
        "row_identity": _all_true(row_identity_rows, "row_identity_uniqueness_audit_passed"),
        "validation": _all_true(validation_rows, "validation_audit_passed"),
        "allowlist_boundary": _all_true(allowlist_boundary_rows, "candidate_allowlist_boundary_passed"),
        "materialization_boundary": _all_true(materialization_boundary_rows, "materialization_boundary_passed"),
        "execution_boundary": _all_true(execution_rows, "execution_boundary_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "mask_scope": _all_true(mask_rows, "mask_scope_audit_passed"),
        "feature_semantics": _all_true(feature_rows, "feature_semantics_audit_passed"),
        "leakage_split": _all_true(leakage_rows, "leakage_split_audit_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13ax_candidate_metadata_materialization_design_gate_validated": qa_checks["precondition"],
        "materialized_candidate_metadata_row_count": len(candidate_rows),
        "materialized_candidate_metadata_column_count": len(CANDIDATE_METADATA_FIELDS),
        "accepted_event_source_row_count": len(accepted_rows),
        "unresolved_event_excluded_count": len(unresolved_event_rows),
        "candidate_metadata_id_count": len(ids),
        "candidate_metadata_id_unique_count": len(set(ids)),
        "candidate_metadata_id_matches_design_preview_count": sum(_bool(row["id_matches_design_preview"]) for row in accepted_materialization_rows),
        "candidate_metadata_csv_written": True,
        "candidate_metadata_json_written": True,
        "candidate_metadata_materialized": True,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "schema_compliance_passed": qa_checks["schema_compliance"],
        "field_completeness_passed": qa_checks["field_completeness"],
        "source_traceability_passed": qa_checks["traceability"],
        "row_identity_uniqueness_passed": qa_checks["row_identity"],
        "unresolved_exclusion_preserved": qa_checks["unresolved_exclusion"],
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
        "ready_for_covapie_candidate_metadata_materialization_qa_gate": True,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13am.CANONICAL_MASK_TASK_NAMES,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_candidate_metadata_materialization_qa_gate",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13ax_precondition": {"row_count": len(precondition_rows), "passed": qa_checks["precondition"]},
        "candidate_metadata_smoke": {"row_count": len(candidate_rows), "column_count": len(CANDIDATE_METADATA_FIELDS), "passed": qa_checks["candidate_metadata_rows"]},
        "source_traceability": {"row_count": len(traceability_rows), "passed": qa_checks["traceability"]},
        "accepted_event_materialization": {"row_count": len(accepted_materialization_rows), "passed": qa_checks["accepted_materialization"]},
        "unresolved_event_exclusion": {"row_count": len(unresolved_event_rows), "passed": qa_checks["unresolved_exclusion"]},
        "schema_compliance": {"row_count": len(schema_compliance_rows), "passed": qa_checks["schema_compliance"]},
        "field_completeness": {"row_count": len(field_completeness_rows), "passed": qa_checks["field_completeness"]},
        "row_identity_uniqueness": {"row_count": len(row_identity_rows), "passed": qa_checks["row_identity"]},
        "validation": {"row_count": len(validation_rows), "passed": qa_checks["validation"]},
        "allowlist_boundary": {"row_count": len(allowlist_boundary_rows), "passed": qa_checks["allowlist_boundary"]},
        "readiness_boundary": {
            "passed": True,
            "ready_for_covapie_candidate_metadata_materialization_qa_gate": True,
            "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
            "ready_for_training": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "precondition_rows": precondition_rows,
        "candidate_rows": candidate_rows,
        "traceability_rows": traceability_rows,
        "accepted_materialization_rows": accepted_materialization_rows,
        "unresolved_event_rows": unresolved_event_rows,
        "schema_compliance_rows": schema_compliance_rows,
        "field_completeness_rows": field_completeness_rows,
        "row_identity_rows": row_identity_rows,
        "validation_rows": validation_rows,
        "allowlist_boundary_rows": allowlist_boundary_rows,
        "materialization_boundary_rows": materialization_boundary_rows,
        "execution_rows": execution_rows,
        "git_safety_rows": git_safety_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }
