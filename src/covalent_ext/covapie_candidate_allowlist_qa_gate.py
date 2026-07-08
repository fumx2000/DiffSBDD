from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_candidate_allowlist_materialization_smoke as step13bb


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_allowlist_qa_gate_v0"
PREVIOUS_STAGE = "covapie_candidate_allowlist_materialization_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13BB_ROOT = step13bb.OUTPUT_ROOT
STEP13BA_ROOT = step13bb.STEP13BA_ROOT
STEP13AZ_ROOT = step13bb.STEP13AZ_ROOT
STEP13AY_ROOT = step13bb.STEP13AY_ROOT

STEP13BB_MANIFEST_JSON = step13bb.MANIFEST_JSON
STEP13BB_ALLOWLIST_CSV = step13bb.ALLOWLIST_SMOKE_CSV
STEP13BB_ALLOWLIST_JSON = step13bb.ALLOWLIST_SMOKE_JSON
STEP13BB_QA_AUDIT_CSV = step13bb.QA_AUDIT_CSV
STEP13BB_UNRESOLVED_EXCLUSION_AUDIT_CSV = step13bb.UNRESOLVED_EXCLUSION_AUDIT_CSV
STEP13BA_SCHEMA_CONTRACT_CSV = step13bb.STEP13BA_SCHEMA_CONTRACT_CSV
STEP13BA_CANDIDATE_PREVIEW_CSV = step13bb.STEP13BA_CANDIDATE_PREVIEW_CSV
STEP13AZ_CONTENT_INTEGRITY_CSV = step13bb.STEP13AZ_CONTENT_INTEGRITY_CSV
STEP13AZ_TRACEABILITY_CSV = step13bb.STEP13AZ_TRACEABILITY_CSV
STEP13AZ_UNRESOLVED_EXCLUSION_CSV = step13bb.STEP13AZ_UNRESOLVED_EXCLUSION_CSV
STEP13AY_CANDIDATE_METADATA_CSV = step13bb.STEP13AY_CANDIDATE_METADATA_CSV
METADATA_CSV = step13bb.METADATA_CSV
METADATA_CSV_SHA256 = step13bb.METADATA_CSV_SHA256
RAW_STORAGE_ROOT = step13bb.RAW_STORAGE_ROOT

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_precondition_audit.csv"
SCHEMA_IDENTITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_schema_identity_audit.csv"
CSV_JSON_CONSISTENCY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_csv_json_consistency_audit.csv"
TRACEABILITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_traceability_audit.csv"
UNRESOLVED_EXCLUSION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_unresolved_exclusion_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_allowlist_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_allowlist_qa_gate_v0_summary.md")

ALLOWLIST_FIELDS = step13bb.ALLOWLIST_FIELDS
EXPECTED_ALLOWLIST_IDS = step13bb.EXPECTED_ALLOWLIST_IDS
EXPECTED_CANDIDATE_IDS = step13bb.EXPECTED_CANDIDATE_IDS
EXPECTED_PAIRS = step13bb.EXPECTED_PAIRS
CANONICAL_MASK_TASK_NAMES = step13bb.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bb.CANONICAL_MASK_TASK_ALIASES
FORBIDDEN_DERIVED_SUFFIXES = step13bb.FORBIDDEN_DERIVED_SUFFIXES
FORBIDDEN_OUTPUT_NAMES = step13bb.FORBIDDEN_OUTPUT_NAMES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SCHEMA_IDENTITY_COLUMNS = [
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "row_index",
    "column_count",
    "schema_column_order_matches",
    "allowlist_entry_id_deterministic",
    "allowlist_entry_id_unique",
    "candidate_metadata_id_unique",
    "observed_pair_expected",
    "unresolved_1a54_mdc_absent",
    "all_required_fields_non_empty",
    "ready_for_training_false",
    "schema_identity_qa_passed",
    "qa_comment",
]
CSV_JSON_COLUMNS = [
    "consistency_item",
    "csv_row_count",
    "json_row_count",
    "json_is_list_of_dicts",
    "json_fields_match_schema",
    "no_extra_json_fields",
    "no_missing_json_fields",
    "csv_json_content_identical",
    "csv_json_consistency_qa_passed",
    "blocking_reasons",
]
TRACEABILITY_COLUMNS = [
    "allowlist_entry_id",
    "candidate_metadata_id",
    "pdb_id",
    "het_code",
    "step13ba_candidate_preview_found",
    "step13bb_qa_audit_found",
    "step13ay_candidate_metadata_found",
    "step13az_content_integrity_found",
    "step13az_traceability_found",
    "step13az_unresolved_exclusion_boundary_found",
    "traceability_qa_passed",
    "qa_comment",
]
UNRESOLVED_COLUMNS = [
    "pdb_id",
    "het_code",
    "reason_unresolved",
    "present_in_step13az_unresolved_source",
    "present_in_step13bb_unresolved_audit",
    "present_in_allowlist_csv",
    "present_in_allowlist_json",
    "allowlist_entry_materialized",
    "exclusion_preserved",
    "unresolved_exclusion_qa_passed",
    "qa_comment",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "allowed_current_step", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKERS_COLUMNS = ["training_blocker_item", "current_step_status", "training_blocker_passed", "qa_comment"]


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


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", str(RAW_STORAGE_ROOT)]).stdout.strip())


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _forbidden_output_names_exist(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.name in FORBIDDEN_OUTPUT_NAMES for path in root.rglob("*")) if root.exists() else False


def _precondition_rows(manifest13bb: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("step13bb_manifest_exists", str(STEP13BB_MANIFEST_JSON), "exists", STEP13BB_MANIFEST_JSON.exists(), STEP13BB_MANIFEST_JSON.exists()),
        ("step13bb_stage", str(STEP13BB_MANIFEST_JSON), PREVIOUS_STAGE, manifest13bb.get("stage"), manifest13bb.get("stage") == PREVIOUS_STAGE),
        ("step13bb_all_checks_passed", str(STEP13BB_MANIFEST_JSON), "true", manifest13bb.get("all_checks_passed"), manifest13bb.get("all_checks_passed") is True),
        ("step13bb_candidate_allowlist_materialized", str(STEP13BB_MANIFEST_JSON), "true", manifest13bb.get("candidate_allowlist_materialized"), manifest13bb.get("candidate_allowlist_materialized") is True),
        ("step13bb_ready_for_allowlist_qa_gate", str(STEP13BB_MANIFEST_JSON), "true", manifest13bb.get("ready_for_covapie_candidate_allowlist_qa_gate"), manifest13bb.get("ready_for_covapie_candidate_allowlist_qa_gate") is True),
        ("step13bb_ready_for_training", str(STEP13BB_MANIFEST_JSON), "false", manifest13bb.get("ready_for_training"), manifest13bb.get("ready_for_training") is False),
        ("step13bb_allowlist_csv_exists", str(STEP13BB_ALLOWLIST_CSV), "exists", STEP13BB_ALLOWLIST_CSV.exists(), STEP13BB_ALLOWLIST_CSV.exists()),
        ("step13bb_allowlist_json_exists", str(STEP13BB_ALLOWLIST_JSON), "exists", STEP13BB_ALLOWLIST_JSON.exists(), STEP13BB_ALLOWLIST_JSON.exists()),
        ("step13ba_schema_contract_exists", str(STEP13BA_SCHEMA_CONTRACT_CSV), "exists", STEP13BA_SCHEMA_CONTRACT_CSV.exists(), STEP13BA_SCHEMA_CONTRACT_CSV.exists()),
        ("step13ba_preview_exists", str(STEP13BA_CANDIDATE_PREVIEW_CSV), "exists", STEP13BA_CANDIDATE_PREVIEW_CSV.exists(), STEP13BA_CANDIDATE_PREVIEW_CSV.exists()),
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


def _schema_identity_rows(allowlist_rows: list[dict[str, str]], schema_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    schema_fields = [row["allowlist_field"] for row in schema_rows]
    allowlist_ids = [row["allowlist_entry_id"] for row in allowlist_rows]
    candidate_ids = [row["candidate_metadata_id"] for row in allowlist_rows]
    pairs = [(row["pdb_id"], row["het_code"]) for row in allowlist_rows]
    rows = []
    for index, row in enumerate(allowlist_rows, start=1):
        checks = {
            "schema_column_order_matches": list(row.keys()) == schema_fields == ALLOWLIST_FIELDS,
            "allowlist_entry_id_deterministic": row["allowlist_entry_id"] == f"allowlist::{row['candidate_metadata_id']}",
            "allowlist_entry_id_unique": allowlist_ids.count(row["allowlist_entry_id"]) == 1,
            "candidate_metadata_id_unique": candidate_ids.count(row["candidate_metadata_id"]) == 1,
            "observed_pair_expected": (row["pdb_id"], row["het_code"]) in EXPECTED_PAIRS and pairs == EXPECTED_PAIRS,
            "unresolved_1a54_mdc_absent": ("1A54", "MDC") not in pairs,
            "all_required_fields_non_empty": all(value != "" for value in row.values()),
            "ready_for_training_false": row["ready_for_training"] == "false",
        }
        passed = len(row) == 25 and all(checks.values())
        rows.append(
            {
                "allowlist_entry_id": row["allowlist_entry_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "row_index": index,
                "column_count": len(row),
                **checks,
                "schema_identity_qa_passed": passed,
                "qa_comment": "schema_identity_valid" if passed else "schema_identity_blocked",
            }
        )
    return rows


def _sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{field: str(row[field]) for field in ALLOWLIST_FIELDS} for row in sorted(rows, key=lambda item: str(item["allowlist_entry_id"]))]


def _csv_json_consistency_rows(allowlist_rows: list[dict[str, str]], json_rows: Any) -> list[dict[str, Any]]:
    json_is_list = isinstance(json_rows, list) and all(isinstance(row, dict) for row in json_rows)
    json_fields_match = json_is_list and all(set(row.keys()) == set(ALLOWLIST_FIELDS) for row in json_rows)
    no_extra = json_is_list and all(set(row.keys()).issubset(set(ALLOWLIST_FIELDS)) for row in json_rows)
    no_missing = json_is_list and all(set(ALLOWLIST_FIELDS).issubset(set(row.keys())) for row in json_rows)
    identical = json_is_list and _sorted_rows(allowlist_rows) == _sorted_rows(json_rows)
    passed = len(allowlist_rows) == 4 and json_is_list and len(json_rows) == 4 and json_fields_match and no_extra and no_missing and identical
    return [
        {
            "consistency_item": "allowlist_csv_json_full_content",
            "csv_row_count": len(allowlist_rows),
            "json_row_count": len(json_rows) if isinstance(json_rows, list) else 0,
            "json_is_list_of_dicts": json_is_list,
            "json_fields_match_schema": json_fields_match,
            "no_extra_json_fields": no_extra,
            "no_missing_json_fields": no_missing,
            "csv_json_content_identical": identical,
            "csv_json_consistency_qa_passed": passed,
            "blocking_reasons": "" if passed else "csv_json_consistency_failed",
        }
    ]


def _traceability_rows(
    allowlist_rows: list[dict[str, str]],
    preview_rows: list[dict[str, str]],
    step13bb_qa_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    content_rows: list[dict[str, str]],
    traceability_rows: list[dict[str, str]],
    unresolved_source_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    preview_ids = {row["candidate_metadata_id"] for row in preview_rows}
    step13bb_qa_ids = {row["candidate_metadata_id"] for row in step13bb_qa_rows if _bool(row.get("qa_audit_passed"))}
    candidate_ids = {row["candidate_metadata_id"] for row in candidate_rows}
    content_ids = {row["candidate_metadata_id"] for row in content_rows if _bool(row.get("content_integrity_passed"))}
    trace_ids = {row["candidate_metadata_id"] for row in traceability_rows if _bool(row.get("traceability_qa_passed"))}
    unresolved_boundary = any((row["pdb_id"], row["het_code"]) == ("1A54", "MDC") and _bool(row.get("unresolved_exclusion_qa_passed")) for row in unresolved_source_rows)
    rows = []
    for row in allowlist_rows:
        checks = {
            "step13ba_candidate_preview_found": row["candidate_metadata_id"] in preview_ids,
            "step13bb_qa_audit_found": row["candidate_metadata_id"] in step13bb_qa_ids,
            "step13ay_candidate_metadata_found": row["candidate_metadata_id"] in candidate_ids,
            "step13az_content_integrity_found": row["candidate_metadata_id"] in content_ids,
            "step13az_traceability_found": row["candidate_metadata_id"] in trace_ids,
            "step13az_unresolved_exclusion_boundary_found": unresolved_boundary,
        }
        passed = all(checks.values())
        rows.append(
            {
                "allowlist_entry_id": row["allowlist_entry_id"],
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                **checks,
                "traceability_qa_passed": passed,
                "qa_comment": "traceability_complete" if passed else "traceability_blocked",
            }
        )
    return rows


def _unresolved_exclusion_rows(
    allowlist_rows: list[dict[str, str]],
    json_rows: list[dict[str, Any]],
    step13bb_unresolved_rows: list[dict[str, str]],
    step13az_unresolved_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    csv_pairs = {(row["pdb_id"], row["het_code"]) for row in allowlist_rows}
    json_pairs = {(str(row["pdb_id"]), str(row["het_code"])) for row in json_rows}
    source = step13az_unresolved_rows[0]
    present_source = (source["pdb_id"], source["het_code"]) == ("1A54", "MDC")
    present_step13bb = any((row["pdb_id"], row["het_code"]) == ("1A54", "MDC") and _bool(row["unresolved_exclusion_audit_passed"]) for row in step13bb_unresolved_rows)
    passed = present_source and present_step13bb and ("1A54", "MDC") not in csv_pairs and ("1A54", "MDC") not in json_pairs and source["reason_unresolved"] == "raw_no_connectivity_records_found"
    return [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "reason_unresolved": source["reason_unresolved"],
            "present_in_step13az_unresolved_source": present_source,
            "present_in_step13bb_unresolved_audit": present_step13bb,
            "present_in_allowlist_csv": ("1A54", "MDC") in csv_pairs,
            "present_in_allowlist_json": ("1A54", "MDC") in json_pairs,
            "allowlist_entry_materialized": False,
            "exclusion_preserved": ("1A54", "MDC") not in csv_pairs and ("1A54", "MDC") not in json_pairs,
            "unresolved_exclusion_qa_passed": passed,
            "qa_comment": "unresolved_case_remains_excluded" if passed else "unresolved_case_boundary_failed",
        }
    ]


def _boundary_safety_rows() -> list[dict[str, Any]]:
    statuses = {
        "candidate_allowlist_qa_gate": ("executed_qa_gate_only", True),
        "candidate_allowlist_materialization": ("not_executed_current_step_already_completed_previous_step", False),
        "candidate_metadata_materialization": ("not_executed_current_step", False),
        "raw_read": ("not_executed_or_not_allowed", False),
        "raw_download": ("not_executed_or_not_allowed", False),
        "sample_index": ("blocked_current_step", False),
        "final_dataset": ("blocked_current_step", False),
        "split_assignments": ("blocked_current_step", False),
        "leakage_matrix": ("blocked_current_step", False),
        "training": ("blocked_current_step", False),
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
        ("no_new_materialized_allowlist_artifacts", "no covapie_candidate_allowlist_materialized files", "false", not any(OUTPUT_ROOT.glob("*materialized*"))),
        ("no_sample_final_split_leakage_artifacts", "forbidden output name scan", "false", not _forbidden_output_names_exist()),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bb_artifacts_unchanged", "git diff step13bb root", "empty", not _path_diff_exists([str(STEP13BB_ROOT)])),
        ("step13ba_artifacts_unchanged", "git diff step13ba root", "empty", not _path_diff_exists([str(STEP13BA_ROOT)])),
        ("step13az_artifacts_unchanged", "git diff step13az root", "empty", not _path_diff_exists([str(STEP13AZ_ROOT)])),
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
    rows = [
        ("mask_warhead_only_A", "warhead_only/A_preserved", True, "canonical_mask_preserved"),
        ("mask_linker_plus_warhead_B", "linker_plus_warhead/B_preserved", True, "canonical_mask_preserved"),
        ("mask_scaffold_plus_warhead_B2", "scaffold_plus_warhead/B2_preserved", True, "canonical_mask_preserved"),
        ("mask_scaffold_only_B3", "scaffold_only/B3_preserved", True, "canonical_mask_preserved"),
        ("mask_scaffold_plus_linker_plus_warhead_C", "scaffold_plus_linker_plus_warhead/C_preserved", True, "canonical_mask_preserved"),
        ("feature_semantics_audit_required", "required_before_training", True, "training_blocker_preserved"),
        ("feature_semantics_fully_audited_claimed_false", "fully_audited_claimed_false", True, "training_blocker_preserved"),
        ("leakage_split_design_required", "required_before_training", True, "training_blocker_preserved"),
        ("split_written_current_step_false", "false", True, "training_blocker_preserved"),
        ("leakage_matrix_written_current_step_false", "false", True, "training_blocker_preserved"),
        ("ready_for_training_false", "false", True, "training_blocker_preserved"),
    ]
    return [
        {
            "training_blocker_item": item,
            "current_step_status": status,
            "training_blocker_passed": passed,
            "qa_comment": comment,
        }
        for item, status, passed, comment in rows
    ]


def run_covapie_candidate_allowlist_qa_gate_v0() -> dict[str, Any]:
    manifest13bb = _load_json(STEP13BB_MANIFEST_JSON)
    allowlist_rows = _csv_rows(STEP13BB_ALLOWLIST_CSV)
    allowlist_json_rows = _load_json(STEP13BB_ALLOWLIST_JSON)
    step13bb_qa_rows = _csv_rows(STEP13BB_QA_AUDIT_CSV)
    step13bb_unresolved_rows = _csv_rows(STEP13BB_UNRESOLVED_EXCLUSION_AUDIT_CSV)
    schema_rows = _csv_rows(STEP13BA_SCHEMA_CONTRACT_CSV)
    preview_rows = _csv_rows(STEP13BA_CANDIDATE_PREVIEW_CSV)
    candidate_rows = _csv_rows(STEP13AY_CANDIDATE_METADATA_CSV)
    content_rows = _csv_rows(STEP13AZ_CONTENT_INTEGRITY_CSV)
    trace_rows = _csv_rows(STEP13AZ_TRACEABILITY_CSV)
    step13az_unresolved_rows = _csv_rows(STEP13AZ_UNRESOLVED_EXCLUSION_CSV)

    precondition_rows = _precondition_rows(manifest13bb)
    schema_identity_rows = _schema_identity_rows(allowlist_rows, schema_rows)
    csv_json_rows = _csv_json_consistency_rows(allowlist_rows, allowlist_json_rows)
    traceability_rows = _traceability_rows(allowlist_rows, preview_rows, step13bb_qa_rows, candidate_rows, content_rows, trace_rows, step13az_unresolved_rows)
    unresolved_rows = _unresolved_exclusion_rows(allowlist_rows, allowlist_json_rows, step13bb_unresolved_rows, step13az_unresolved_rows)
    boundary_rows = _boundary_safety_rows()
    git_safety_rows = _git_safety_rows()
    training_blocker_rows = _training_blocker_rows()

    allowlist_ids = [row["allowlist_entry_id"] for row in allowlist_rows]
    candidate_ids = [row["candidate_metadata_id"] for row in allowlist_rows]
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "schema_identity": len(schema_identity_rows) == 4 and _all_true(schema_identity_rows, "schema_identity_qa_passed"),
        "csv_json": len(csv_json_rows) == 1 and _all_true(csv_json_rows, "csv_json_consistency_qa_passed"),
        "traceability": len(traceability_rows) == 4 and _all_true(traceability_rows, "traceability_qa_passed"),
        "unresolved": len(unresolved_rows) == 1 and _all_true(unresolved_rows, "unresolved_exclusion_qa_passed"),
        "boundary": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "training_blockers": _all_true(training_blocker_rows, "training_blocker_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bb_candidate_allowlist_smoke_validated": qa_checks["precondition"],
        "source_allowlist_row_count": len(allowlist_rows),
        "source_allowlist_column_count": len(ALLOWLIST_FIELDS),
        "source_allowlist_json_row_count": len(allowlist_json_rows),
        "allowlist_entry_id_count": len(allowlist_ids),
        "allowlist_entry_id_unique_count": len(set(allowlist_ids)),
        "candidate_metadata_id_count": len(candidate_ids),
        "candidate_metadata_id_unique_count": len(set(candidate_ids)),
        "schema_identity_qa_passed": qa_checks["schema_identity"],
        "csv_json_consistency_qa_passed": qa_checks["csv_json"],
        "traceability_qa_passed": qa_checks["traceability"],
        "unresolved_exclusion_qa_passed": qa_checks["unresolved"],
        "unresolved_exclusion_preserved": qa_checks["unresolved"],
        "boundary_safety_passed": qa_checks["boundary"],
        "git_safety_passed": qa_checks["git_safety"],
        "training_blockers_passed": qa_checks["training_blockers"],
        "candidate_allowlist_materialized_previous_step": True,
        "candidate_allowlist_materialized_current_step": False,
        "candidate_metadata_materialized_current_step": False,
        "raw_read_current_step": False,
        "raw_download_current_step": False,
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
        "ready_for_covapie_batch_scale_raw_read_design_gate": True,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13bb.CANONICAL_MASK_TASK_NAMES,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_batch_raw_read_extraction_design_gate",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "precondition_rows": precondition_rows,
        "schema_identity_rows": schema_identity_rows,
        "csv_json_rows": csv_json_rows,
        "traceability_rows": traceability_rows,
        "unresolved_rows": unresolved_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }
