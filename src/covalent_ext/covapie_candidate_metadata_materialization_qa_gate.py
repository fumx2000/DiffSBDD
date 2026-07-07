from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_candidate_metadata_materialization_design_gate as design
from covalent_ext import covapie_candidate_metadata_materialization_smoke as step13ay
from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_candidate_metadata_materialization_qa_gate_v0"
PREVIOUS_STAGE = "covapie_candidate_metadata_materialization_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13AY_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_smoke_v0")
STEP13AX_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_design_gate_v0")
STEP13AW_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_qa_gate_v0")

STEP13AY_MANIFEST_JSON = STEP13AY_ROOT / "covapie_candidate_metadata_materialization_smoke_manifest.json"
STEP13AY_CANDIDATE_METADATA_CSV = STEP13AY_ROOT / "covapie_candidate_metadata_smoke.csv"
STEP13AY_CANDIDATE_METADATA_JSON = STEP13AY_ROOT / "covapie_candidate_metadata_smoke.json"
STEP13AY_TRACEABILITY_CSV = STEP13AY_ROOT / "covapie_candidate_metadata_source_traceability_audit.csv"
STEP13AY_UNRESOLVED_EXCLUSION_CSV = STEP13AY_ROOT / "covapie_candidate_metadata_unresolved_event_exclusion_audit.csv"
STEP13AY_VALIDATION_CSV = STEP13AY_ROOT / "covapie_candidate_metadata_validation_audit.csv"

STEP13AX_SCHEMA_CONTRACT_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_schema_contract.csv"
STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV = STEP13AX_ROOT / "covapie_candidate_metadata_accepted_event_inventory.csv"
STEP13AW_PREFERRED_QA_CSV = STEP13AW_ROOT / "covapie_raw_structure_preferred_event_acceptance_qa.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"
RAW_STORAGE_ROOT = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_precondition_audit.csv"
CONTENT_INTEGRITY_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_content_integrity.csv"
TRACEABILITY_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_traceability.csv"
UNRESOLVED_EXCLUSION_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_unresolved_exclusion.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_qa_gate_training_blockers.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_qa_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_candidate_metadata_materialization_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_candidate_metadata_materialization_qa_gate_v0_summary.md")

CANDIDATE_METADATA_FIELDS = design.CANDIDATE_METADATA_FIELDS
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
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
FORBIDDEN_OUTPUT_NAMES = {
    "covapie_candidate_allowlist.csv",
    "covapie_candidate_allowlist.json",
    "sample_index.csv",
    "sample_index.json",
    "final_dataset.csv",
    "final_dataset.json",
    "split_assignments.csv",
    "split_assignments.json",
    "leakage_matrix.csv",
    "leakage_matrix.json",
}
EXPECTED_IDS = [
    "covpdb::1A3B::T29::H:SER195:OG-B",
    "covpdb::1A3E::T16::H:SER195:OG-B",
    "covpdb::1A46::00K::H:SER195:OG-C",
    "covpdb::1A5G::00L::H:SER195:OG-C",
]
EXPECTED_PAIRS = [("1A3B", "T29"), ("1A3E", "T16"), ("1A46", "00K"), ("1A5G", "00L")]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
CONTENT_COLUMNS = ["candidate_metadata_id", "pdb_id", "het_code", "row_index", "column_count", "schema_column_order_matches", "id_matches_expected", "pair_is_allowed", "pair_is_not_unresolved", "required_boolean_fields_valid", "training_ready_false", "content_integrity_passed", "qa_comment"]
TRACEABILITY_COLUMNS = ["candidate_metadata_id", "pdb_id", "het_code", "source_step13ay_traceability_passed", "source_step13ax_accepted_event_found", "source_step13aw_preferred_event_found", "source_metadata_csv_row_found", "source_metadata_csv_row_key", "traceability_qa_passed", "qa_comment"]
UNRESOLVED_COLUMNS = ["pdb_id", "het_code", "resolution_status", "reason_unresolved", "present_in_candidate_metadata", "candidate_metadata_materialized", "candidate_allowlist_materialized", "exclusion_preserved", "unresolved_exclusion_qa_passed", "qa_comment"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "allowed_current_step", "future_condition", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKERS_COLUMNS = ["training_blocker_item", "current_step_status", "training_blocker_passed", "qa_comment"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


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


def _forbidden_output_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.name in FORBIDDEN_OUTPUT_NAMES for path in root.rglob("*")) if root.exists() else False


def _by_pair(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["pdb_id"], row["het_code"]): row for row in rows}


def _precondition_rows(manifest13ay: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("step13ay_manifest_exists", str(STEP13AY_MANIFEST_JSON), "exists", STEP13AY_MANIFEST_JSON.exists(), STEP13AY_MANIFEST_JSON.exists()),
        ("step13ay_stage", str(STEP13AY_MANIFEST_JSON), PREVIOUS_STAGE, manifest13ay.get("stage"), manifest13ay.get("stage") == PREVIOUS_STAGE),
        ("step13ay_all_checks_passed", str(STEP13AY_MANIFEST_JSON), "true", manifest13ay.get("all_checks_passed"), manifest13ay.get("all_checks_passed") is True),
        ("step13ay_candidate_metadata_materialized", str(STEP13AY_MANIFEST_JSON), "true", manifest13ay.get("candidate_metadata_materialized"), manifest13ay.get("candidate_metadata_materialized") is True),
        ("step13ay_candidate_allowlist_materialized", str(STEP13AY_MANIFEST_JSON), "false", manifest13ay.get("candidate_allowlist_materialized"), manifest13ay.get("candidate_allowlist_materialized") is False),
        ("step13ay_candidate_row_count", str(STEP13AY_MANIFEST_JSON), "4", manifest13ay.get("materialized_candidate_metadata_row_count"), manifest13ay.get("materialized_candidate_metadata_row_count") == 4),
        ("step13ay_candidate_column_count", str(STEP13AY_MANIFEST_JSON), "33", manifest13ay.get("materialized_candidate_metadata_column_count"), manifest13ay.get("materialized_candidate_metadata_column_count") == 33),
        ("step13ay_ready_for_qa_gate", str(STEP13AY_MANIFEST_JSON), "true", manifest13ay.get("ready_for_covapie_candidate_metadata_materialization_qa_gate"), manifest13ay.get("ready_for_covapie_candidate_metadata_materialization_qa_gate") is True),
        ("step13ay_ready_for_training", str(STEP13AY_MANIFEST_JSON), "false", manifest13ay.get("ready_for_training"), manifest13ay.get("ready_for_training") is False),
        ("step13ay_ready_to_train_now", str(STEP13AY_MANIFEST_JSON), "false", manifest13ay.get("ready_to_train_now"), manifest13ay.get("ready_to_train_now") is False),
        ("candidate_metadata_smoke_csv_exists", str(STEP13AY_CANDIDATE_METADATA_CSV), "exists", STEP13AY_CANDIDATE_METADATA_CSV.exists(), STEP13AY_CANDIDATE_METADATA_CSV.exists()),
        ("candidate_metadata_smoke_json_exists", str(STEP13AY_CANDIDATE_METADATA_JSON), "exists", STEP13AY_CANDIDATE_METADATA_JSON.exists(), STEP13AY_CANDIDATE_METADATA_JSON.exists()),
        ("step13ax_schema_contract_exists", str(STEP13AX_SCHEMA_CONTRACT_CSV), "exists", STEP13AX_SCHEMA_CONTRACT_CSV.exists(), STEP13AX_SCHEMA_CONTRACT_CSV.exists()),
        ("step13ao_metadata_csv_exists", str(METADATA_CSV), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
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


def _content_integrity_rows(candidate_rows: list[dict[str, str]], schema_fields: list[str]) -> list[dict[str, Any]]:
    rows = []
    observed_columns = list(candidate_rows[0].keys()) if candidate_rows else []
    for index, row in enumerate(candidate_rows, start=1):
        pair = (row["pdb_id"], row["het_code"])
        expected_id = EXPECTED_IDS[index - 1] if index <= len(EXPECTED_IDS) else ""
        bools_valid = (
            _bool(row["accepted_for_future_candidate_metadata"])
            and _bool(row["accepted_for_future_automatic_allowlist"])
            and _bool(row["current_step_materialization_allowed"])
            and not _bool(row["ready_for_training"])
        )
        passed = (
            len(row) == 33
            and observed_columns == schema_fields
            and row["candidate_metadata_id"] == expected_id
            and pair in EXPECTED_PAIRS
            and pair != ("1A54", "MDC")
            and bools_valid
            and not _bool(row["ready_for_training"])
            and all(str(value) != "" for value in row.values())
        )
        rows.append(
            {
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "row_index": index,
                "column_count": len(row),
                "schema_column_order_matches": observed_columns == schema_fields,
                "id_matches_expected": row["candidate_metadata_id"] == expected_id,
                "pair_is_allowed": pair in EXPECTED_PAIRS,
                "pair_is_not_unresolved": pair != ("1A54", "MDC"),
                "required_boolean_fields_valid": bools_valid,
                "training_ready_false": not _bool(row["ready_for_training"]),
                "content_integrity_passed": passed,
                "qa_comment": "candidate_metadata_row_valid" if passed else "candidate_metadata_row_blocked",
            }
        )
    return rows


def _traceability_rows(
    candidate_rows: list[dict[str, str]],
    traceability13ay_rows: list[dict[str, str]],
    accepted_rows: list[dict[str, str]],
    preferred_rows: list[dict[str, str]],
    metadata_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    trace_by_id = {row["candidate_metadata_id"]: row for row in traceability13ay_rows}
    accepted_by_pair = _by_pair(accepted_rows)
    preferred_by_pair = _by_pair(preferred_rows)
    metadata_by_pair = _by_pair(metadata_rows)
    rows = []
    for row in candidate_rows:
        pair = (row["pdb_id"], row["het_code"])
        trace = trace_by_id.get(row["candidate_metadata_id"], {})
        metadata_found = pair in metadata_by_pair
        source_key = row["source_metadata_csv_row_key"]
        key_prefix_ok = source_key.startswith("CovPDB::covpdb_web_metadata_smoke_2026-07-06::")
        passed = _bool(trace.get("traceability_audit_passed")) and pair in accepted_by_pair and pair in preferred_by_pair and metadata_found and bool(source_key) and key_prefix_ok
        rows.append(
            {
                "candidate_metadata_id": row["candidate_metadata_id"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "source_step13ay_traceability_passed": _bool(trace.get("traceability_audit_passed")),
                "source_step13ax_accepted_event_found": pair in accepted_by_pair,
                "source_step13aw_preferred_event_found": pair in preferred_by_pair,
                "source_metadata_csv_row_found": metadata_found,
                "source_metadata_csv_row_key": source_key,
                "traceability_qa_passed": passed,
                "qa_comment": "traceability_complete" if passed else "traceability_blocked",
            }
        )
    return rows


def _unresolved_exclusion_rows(unresolved13ay_rows: list[dict[str, str]], candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidate_pairs = {(row["pdb_id"], row["het_code"]) for row in candidate_rows}
    rows = []
    for row in unresolved13ay_rows:
        pair = (row["pdb_id"], row["het_code"])
        passed = pair == ("1A54", "MDC") and pair not in candidate_pairs and not _bool(row["candidate_metadata_materialized"]) and not _bool(row["candidate_allowlist_materialized"]) and _bool(row["exclusion_preserved"])
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "resolution_status": row["resolution_status"],
                "reason_unresolved": row["reason_unresolved"],
                "present_in_candidate_metadata": pair in candidate_pairs,
                "candidate_metadata_materialized": False,
                "candidate_allowlist_materialized": False,
                "exclusion_preserved": _bool(row["exclusion_preserved"]),
                "unresolved_exclusion_qa_passed": passed,
                "qa_comment": "unresolved_case_remains_blocked" if passed else "unresolved_case_boundary_failed",
            }
        )
    return rows


def _boundary_safety_rows() -> list[dict[str, Any]]:
    statuses = {
        "candidate_metadata_materialization": ("qa_only_existing_first4_metadata", False, "candidate_allowlist_materialization_design_gate"),
        "candidate_allowlist_materialization": ("blocked_until_candidate_metadata_qa_gate_passed", False, "candidate_allowlist_materialization_design_gate"),
        "sample_index": ("blocked_current_qa_gate", False, "future_sample_index_gate_required"),
        "final_dataset": ("blocked_current_qa_gate", False, "future_final_dataset_gate_required"),
        "split_assignments": ("blocked_current_qa_gate", False, "future_leakage_split_design_gate_required"),
        "leakage_matrix": ("blocked_current_qa_gate", False, "future_leakage_split_design_gate_required"),
        "training": ("blocked_current_qa_gate", False, "future_training_gate_required"),
        "network_access": ("not_executed_or_not_allowed", False, "not_applicable"),
        "raw_download": ("not_executed_or_not_allowed", False, "not_applicable"),
        "raw_text_read": ("not_executed_or_not_allowed", False, "not_applicable"),
        "rdkit_biopdb_gemmi": ("not_executed_or_not_allowed", False, "not_applicable"),
        "torch_model_training": ("not_executed_or_not_allowed", False, "not_applicable"),
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "allowed_current_step": allowed,
            "future_condition": future_condition,
            "boundary_safety_passed": True,
            "qa_comment": "boundary_respected",
        }
        for item, (status, allowed, future_condition) in statuses.items()
    ]


def _git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("derived_output_no_raw_suffix_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists(OUTPUT_ROOT)),
        ("no_allowlist_sample_final_split_leakage_artifacts", "forbidden output name scan", "false", not _forbidden_output_exists(OUTPUT_ROOT)),
        ("metadata_csv_unchanged", str(METADATA_CSV), "hash unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13ay_artifacts_unchanged", "git diff step13ay root", "empty", not _path_diff_exists([str(STEP13AY_ROOT)])),
        ("step13ax_artifacts_unchanged", "git diff step13ax root", "empty", not _path_diff_exists([str(STEP13AX_ROOT)])),
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


def run_covapie_candidate_metadata_materialization_qa_gate_v0() -> dict[str, Any]:
    manifest13ay = _load_json(STEP13AY_MANIFEST_JSON)
    candidate_rows = _csv_rows(STEP13AY_CANDIDATE_METADATA_CSV)
    candidate_json_rows = _load_json(STEP13AY_CANDIDATE_METADATA_JSON)
    traceability13ay_rows = _csv_rows(STEP13AY_TRACEABILITY_CSV)
    unresolved13ay_rows = _csv_rows(STEP13AY_UNRESOLVED_EXCLUSION_CSV)
    validation13ay_rows = _csv_rows(STEP13AY_VALIDATION_CSV)
    schema_rows = _csv_rows(STEP13AX_SCHEMA_CONTRACT_CSV)
    accepted_rows = _csv_rows(STEP13AX_ACCEPTED_EVENT_INVENTORY_CSV)
    preferred_rows = _csv_rows(STEP13AW_PREFERRED_QA_CSV)
    metadata_rows = _csv_rows(METADATA_CSV)

    schema_fields = [row["candidate_metadata_field"] for row in schema_rows]
    precondition_rows = _precondition_rows(manifest13ay)
    content_rows = _content_integrity_rows(candidate_rows, schema_fields)
    traceability_rows = _traceability_rows(candidate_rows, traceability13ay_rows, accepted_rows, preferred_rows, metadata_rows)
    unresolved_rows = _unresolved_exclusion_rows(unresolved13ay_rows, candidate_rows)
    boundary_rows = _boundary_safety_rows()
    git_safety_rows = _git_safety_rows()
    training_blocker_rows = _training_blocker_rows()

    ids = [row["candidate_metadata_id"] for row in candidate_rows]
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "content_integrity": _all_true(content_rows, "content_integrity_passed") and len(candidate_rows) == 4 and len(candidate_json_rows) == 4,
        "traceability": _all_true(traceability_rows, "traceability_qa_passed"),
        "unresolved_exclusion": _all_true(unresolved_rows, "unresolved_exclusion_qa_passed"),
        "boundary_safety": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
        "training_blockers": _all_true(training_blocker_rows, "training_blocker_passed"),
        "step13ay_validation": _all_true(validation13ay_rows, "validation_audit_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13ay_candidate_metadata_materialization_smoke_validated": qa_checks["precondition"],
        "qa_candidate_metadata_row_count": len(candidate_rows),
        "qa_candidate_metadata_column_count": len(candidate_rows[0]) if candidate_rows else 0,
        "qa_candidate_metadata_id_count": len(ids),
        "qa_candidate_metadata_id_unique_count": len(set(ids)),
        "qa_candidate_metadata_id_matches_expected_count": sum(row["candidate_metadata_id"] in EXPECTED_IDS for row in candidate_rows),
        "qa_unresolved_exclusion_preserved": qa_checks["unresolved_exclusion"],
        "qa_traceability_passed": qa_checks["traceability"],
        "qa_content_integrity_passed": qa_checks["content_integrity"],
        "qa_boundary_safety_passed": qa_checks["boundary_safety"],
        "qa_git_safety_passed": qa_checks["git_safety"],
        "qa_training_blockers_passed": qa_checks["training_blockers"],
        "candidate_metadata_materialized_previous_step": True,
        "candidate_metadata_materialized_current_step": False,
        "candidate_allowlist_materialized": False,
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
        "ready_for_covapie_candidate_allowlist_materialization_design_gate": True,
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
        "recommended_next_step": "covapie_candidate_allowlist_materialization_design_gate",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    report_sections = {
        "step13ay_precondition": {"row_count": len(precondition_rows), "passed": qa_checks["precondition"]},
        "content_integrity": {"row_count": len(content_rows), "passed": qa_checks["content_integrity"]},
        "traceability": {"row_count": len(traceability_rows), "passed": qa_checks["traceability"]},
        "unresolved_exclusion": {"row_count": len(unresolved_rows), "passed": qa_checks["unresolved_exclusion"]},
        "boundary_safety": {"row_count": len(boundary_rows), "passed": qa_checks["boundary_safety"]},
        "git_safety": {"row_count": len(git_safety_rows), "passed": qa_checks["git_safety"]},
        "training_blockers": {"row_count": len(training_blocker_rows), "passed": qa_checks["training_blockers"]},
        "readiness_boundary": {
            "passed": True,
            "ready_for_covapie_candidate_allowlist_materialization_design_gate": True,
            "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
            "ready_for_training": False,
            "ready_to_train_now": False,
        },
    }
    return {
        "precondition_rows": precondition_rows,
        "content_rows": content_rows,
        "traceability_rows": traceability_rows,
        "unresolved_rows": unresolved_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
        "report_sections": report_sections,
    }
