from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_pilot_download_dry_run_gate_v0"
PREVIOUS_STAGE = "real_covalent_pilot_download_manifest_gate_v0"

STEP12R_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_manifest_gate_v0/"
    "real_covalent_pilot_download_manifest_gate_manifest.json"
)
STEP12R_PILOT_MANIFEST_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_manifest_gate_v0/"
    "real_covalent_pilot_download_manifest.csv"
)
STEP12R_SUMMARY_MD = Path("docs/real_covalent_pilot_download_manifest_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_pilot_download_dry_run_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_dry_run_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_pilot_download_dry_run_gate_manifest.json"
DRY_RUN_TABLE_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_dry_run_table.csv"
SUMMARY_MD = Path("docs/real_covalent_pilot_download_dry_run_gate_v0_summary.md")

INPUT_SOURCE = "real_covalent_training_tensor_materialized_v0"
SELECTED_REAL_SAMPLE_INDEX = Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"

TRAIN_READY_SCOPE_V1 = "cys_with_known_reconstruction_template_only"
NON_CYS_DATA_BULK_CLEANING_POLICY = "identify_classify_defer_until_template_gate"
RECOMMENDED_NEXT_STEP = "real_covalent_pilot_download_execution_gate"

FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

PDB_MMCIF_URL_TEMPLATE = "https://files.rcsb.org/download/{pdb_id}.cif.gz"
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_LOCAL_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]
EXPECTED_BLOCKED_SOURCES = ["CovPDB", "CovBinderInPDB", "CovalentInDB"]
EXPECTED_ALLOWED_PILOT_SOURCES = ["PDB/mmCIF direct", "local curated"]

PILOT_DOWNLOAD_MANIFEST_COLUMNS = [
    "job_id",
    "source_name",
    "adapter_name",
    "job_type",
    "pilot_scope",
    "source_license_status",
    "source_license_verified_for_pilot",
    "source_requires_manual_review",
    "pdb_id",
    "sample_id",
    "candidate_download_url",
    "url_template",
    "url_template_verified",
    "file_type",
    "compression",
    "expected_local_output_path",
    "raw_storage_root",
    "raw_subdir",
    "checksum_required",
    "sha256_expected_now",
    "checksum_status",
    "resume_supported",
    "retry_policy",
    "provenance_required",
    "download_enabled_in_this_step",
    "ready_for_dry_run",
    "ready_for_execution",
    "blocked_reason",
    "notes",
]

DRY_RUN_TABLE_COLUMNS = [
    "job_id",
    "source_name",
    "job_type",
    "pdb_id",
    "sample_id",
    "dry_run_status",
    "schema_valid",
    "source_policy_valid",
    "url_string_valid",
    "local_output_path_valid",
    "checksum_policy_valid",
    "provenance_policy_valid",
    "blocked_source_policy_valid",
    "network_called",
    "file_downloaded",
    "raw_dir_created",
    "raw_file_written",
    "adapter_run",
    "ready_for_execution_after_dry_run",
    "blocking_reasons",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_columns(path: str | Path) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [] if reader.fieldnames is None else list(reader.fieldnames)


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _is_true(value: str) -> bool:
    return value == "True"


def _is_false(value: str) -> bool:
    return value == "False"


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def validate_step12r_pilot_download_manifest_gate_v0() -> bool:
    if not STEP12R_MANIFEST_JSON.is_file() or not STEP12R_PILOT_MANIFEST_CSV.is_file() or not STEP12R_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12R outputs are missing")
    manifest = _load_json(STEP12R_MANIFEST_JSON)
    rows = _read_csv(STEP12R_PILOT_MANIFEST_CSV)
    columns = _csv_columns(STEP12R_PILOT_MANIFEST_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_source_registry_license_audit_gate_v0",
        "step12q_source_registry_license_audit_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "sample_index_exists": True,
        "sample_index_current_sample_count": 3,
        "pilot_pdb_ids_derived_from_sample_ids": EXPECTED_PDB_IDS,
        "pilot_download_manifest_defined": True,
        "pilot_download_manifest_written": True,
        "pilot_download_manifest_row_count": 9,
        "pilot_download_job_count": 6,
        "blocked_source_row_count": 3,
        "pdb_direct_pilot_job_count": 3,
        "local_curated_pilot_job_count": 3,
        "pilot_pdb_ids": EXPECTED_PDB_IDS,
        "pilot_local_sample_ids": EXPECTED_LOCAL_SAMPLE_IDS,
        "blocked_sources": EXPECTED_BLOCKED_SOURCES,
        "allowed_pilot_sources": EXPECTED_ALLOWED_PILOT_SOURCES,
        "all_pilot_jobs_download_disabled_in_this_step": True,
        "all_pilot_jobs_ready_for_dry_run": True,
        "any_pilot_job_ready_for_execution": False,
        "all_blocked_sources_not_ready_for_dry_run": True,
        "rcsb_mmcif_url_template_defined": True,
        "rcsb_mmcif_url_template_verified_by_external_audit": True,
        "checksum_required_for_pdb_downloads": True,
        "provenance_required_for_all_pilot_jobs": True,
        "pilot_manifest_does_not_grant_download_execution": True,
        "download_dry_run_readiness_policy_defined": True,
        "dry_run_may_download_files": False,
        "dry_run_may_call_network": False,
        "ready_to_run_pilot_download_dry_run": True,
        "ready_to_execute_pilot_download": False,
        "ready_to_download_large_scale_data_now": False,
        "data_downloaded": False,
        "external_network_called": False,
        "raw_storage_directories_created": False,
        "raw_download_files_written": False,
        "raw_structure_files_written": False,
        "adapter_implementation_written": False,
        "adapter_execution_run": False,
        "rdkit_processing_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "coordinate_geometry_calculation_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "enriched_sample_index_written": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "real_covalent_pilot_download_manifest_gate_passed": True,
        "pilot_download_manifest_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_pilot_download_dry_run_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12r_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(columns == PILOT_DOWNLOAD_MANIFEST_COLUMNS, "step12r_pilot_manifest_columns_invalid", blockers)
    _expect(len(rows) == 9, "step12r_pilot_manifest_row_count_invalid", blockers)
    pdb_rows = [row for row in rows if row["source_name"] == "PDB/mmCIF direct"]
    local_rows = [row for row in rows if row["source_name"] == "local curated"]
    blocked_rows = [row for row in rows if row["source_name"] in EXPECTED_BLOCKED_SOURCES]
    _expect(len(pdb_rows) == 3, "step12r_pdb_direct_row_count_invalid", blockers)
    _expect(len(local_rows) == 3, "step12r_local_curated_row_count_invalid", blockers)
    _expect(len(blocked_rows) == 3, "step12r_blocked_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in pdb_rows] == EXPECTED_PDB_IDS, "step12r_pdb_ids_invalid", blockers)
    for row in pdb_rows:
        pdb_id = row["pdb_id"]
        _expect(row["source_license_status"] == "verified_cc0_for_pdb_archive", f"step12r_pdb_license_invalid:{pdb_id}", blockers)
        _expect(_is_true(row["source_license_verified_for_pilot"]), f"step12r_pdb_license_verified_invalid:{pdb_id}", blockers)
        _expect(_is_false(row["source_requires_manual_review"]), f"step12r_pdb_manual_review_invalid:{pdb_id}", blockers)
        _expect(row["url_template"] == PDB_MMCIF_URL_TEMPLATE, f"step12r_pdb_url_template_invalid:{pdb_id}", blockers)
        _expect(row["candidate_download_url"].endswith(f"/{pdb_id}.cif.gz"), f"step12r_pdb_url_invalid:{pdb_id}", blockers)
        _expect(
            row["expected_local_output_path"].startswith("data/raw/covalent_sources/pdb_mmcif_direct/structures/"),
            f"step12r_pdb_output_path_invalid:{pdb_id}",
            blockers,
        )
        _expect(_is_true(row["checksum_required"]), f"step12r_pdb_checksum_invalid:{pdb_id}", blockers)
        _expect(_is_false(row["download_enabled_in_this_step"]), f"step12r_pdb_download_enabled_invalid:{pdb_id}", blockers)
        _expect(_is_true(row["ready_for_dry_run"]), f"step12r_pdb_ready_dry_invalid:{pdb_id}", blockers)
        _expect(_is_false(row["ready_for_execution"]), f"step12r_pdb_ready_exec_invalid:{pdb_id}", blockers)
    for row in local_rows:
        _expect(row["candidate_download_url"] == "local_only", f"step12r_local_url_invalid:{row['sample_id']}", blockers)
        _expect(row["file_type"] == "local_curated_existing_record", f"step12r_local_file_type_invalid:{row['sample_id']}", blockers)
        _expect(_is_false(row["checksum_required"]), f"step12r_local_checksum_invalid:{row['sample_id']}", blockers)
        _expect(_is_false(row["download_enabled_in_this_step"]), f"step12r_local_download_enabled_invalid:{row['sample_id']}", blockers)
        _expect(_is_true(row["ready_for_dry_run"]), f"step12r_local_ready_dry_invalid:{row['sample_id']}", blockers)
        _expect(_is_false(row["ready_for_execution"]), f"step12r_local_ready_exec_invalid:{row['sample_id']}", blockers)
    for row in blocked_rows:
        _expect(row["source_license_status"] == "requires_manual_review", f"step12r_blocked_license_invalid:{row['source_name']}", blockers)
        _expect(_is_true(row["source_requires_manual_review"]), f"step12r_blocked_manual_invalid:{row['source_name']}", blockers)
        _expect(_is_false(row["ready_for_dry_run"]), f"step12r_blocked_ready_dry_invalid:{row['source_name']}", blockers)
        _expect(_is_false(row["ready_for_execution"]), f"step12r_blocked_ready_exec_invalid:{row['source_name']}", blockers)
        _expect(row["blocked_reason"] == "manual_license_review_required", f"step12r_blocked_reason_invalid:{row['source_name']}", blockers)
    summary = STEP12R_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "pilot download manifest gate",
        "not download execution",
        "not network",
        "not adapter execution",
        "not enrichment",
        "not split",
        "not training",
        "6DI9",
        "5F2E",
        "6OIM",
        "BTK_C481_6DI9_pre_reaction",
        "KRAS_G12C_5F2E_pre_reaction",
        "KRAS_G12C_6OIM_pre_reaction",
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        PDB_MMCIF_URL_TEMPLATE,
        "verified_cc0_for_pdb_archive",
        "All downloads disabled",
        "ready_to_run_pilot_download_dry_run=true",
        "ready_to_execute_pilot_download=false",
        "No data download/network/raw dirs/raw files/adapters",
        "No RDKit/UniProt/CD-HIT/geometry/NPZ/training",
        "real_covalent_pilot_download_dry_run_gate",
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12r_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _dry_run_row_for_pdb(row: dict[str, str], schema_valid: bool) -> dict[str, Any]:
    pdb_id = row["pdb_id"]
    url_valid = row["candidate_download_url"] == PDB_MMCIF_URL_TEMPLATE.format(pdb_id=pdb_id)
    path_valid = row["expected_local_output_path"] == f"data/raw/covalent_sources/pdb_mmcif_direct/structures/{pdb_id}.cif.gz"
    checksum_valid = _is_true(row["checksum_required"]) and row["sha256_expected_now"] == "not_available_until_download"
    provenance_valid = _is_true(row["provenance_required"])
    source_policy_valid = (
        row["source_license_status"] == "verified_cc0_for_pdb_archive"
        and _is_true(row["source_license_verified_for_pilot"])
        and _is_false(row["source_requires_manual_review"])
        and _is_true(row["ready_for_dry_run"])
        and _is_false(row["ready_for_execution"])
    )
    passed = bool(schema_valid and source_policy_valid and url_valid and path_valid and checksum_valid and provenance_valid)
    return {
        "job_id": row["job_id"],
        "source_name": row["source_name"],
        "job_type": row["job_type"],
        "pdb_id": pdb_id,
        "sample_id": row["sample_id"],
        "dry_run_status": "passed" if passed else "failed",
        "schema_valid": schema_valid,
        "source_policy_valid": source_policy_valid,
        "url_string_valid": url_valid,
        "local_output_path_valid": path_valid,
        "checksum_policy_valid": checksum_valid,
        "provenance_policy_valid": provenance_valid,
        "blocked_source_policy_valid": True,
        "network_called": False,
        "file_downloaded": False,
        "raw_dir_created": False,
        "raw_file_written": False,
        "adapter_run": False,
        "ready_for_execution_after_dry_run": passed,
        "blocking_reasons": [] if passed else ["pdb_direct_dry_run_validation_failed"],
    }


def _dry_run_row_for_local(row: dict[str, str], schema_valid: bool) -> dict[str, Any]:
    url_valid = row["candidate_download_url"] == "local_only"
    path_valid = row["expected_local_output_path"] == "local_curated_existing_sample_index"
    checksum_valid = _is_false(row["checksum_required"])
    provenance_valid = _is_true(row["provenance_required"])
    source_policy_valid = (
        row["source_license_status"] == "local_project_controlled"
        and _is_true(row["source_license_verified_for_pilot"])
        and _is_false(row["source_requires_manual_review"])
        and _is_true(row["ready_for_dry_run"])
        and _is_false(row["ready_for_execution"])
    )
    passed = bool(schema_valid and source_policy_valid and url_valid and path_valid and checksum_valid and provenance_valid)
    return {
        "job_id": row["job_id"],
        "source_name": row["source_name"],
        "job_type": row["job_type"],
        "pdb_id": row["pdb_id"],
        "sample_id": row["sample_id"],
        "dry_run_status": "passed" if passed else "failed",
        "schema_valid": schema_valid,
        "source_policy_valid": source_policy_valid,
        "url_string_valid": url_valid,
        "local_output_path_valid": path_valid,
        "checksum_policy_valid": checksum_valid,
        "provenance_policy_valid": provenance_valid,
        "blocked_source_policy_valid": True,
        "network_called": False,
        "file_downloaded": False,
        "raw_dir_created": False,
        "raw_file_written": False,
        "adapter_run": False,
        "ready_for_execution_after_dry_run": passed,
        "blocking_reasons": [] if passed else ["local_curated_dry_run_validation_failed"],
    }


def _dry_run_row_for_blocked(row: dict[str, str], schema_valid: bool) -> dict[str, Any]:
    source_policy_valid = row["source_license_status"] == "requires_manual_review" and _is_true(row["source_requires_manual_review"])
    url_valid = row["candidate_download_url"] == ""
    path_valid = row["expected_local_output_path"] == ""
    checksum_valid = _is_false(row["checksum_required"])
    provenance_valid = _is_false(row["provenance_required"])
    blocked_valid = (
        _is_false(row["ready_for_dry_run"])
        and _is_false(row["ready_for_execution"])
        and row["blocked_reason"] == "manual_license_review_required"
    )
    passed = bool(schema_valid and source_policy_valid and url_valid and path_valid and checksum_valid and provenance_valid and blocked_valid)
    return {
        "job_id": row["job_id"],
        "source_name": row["source_name"],
        "job_type": row["job_type"],
        "pdb_id": row["pdb_id"],
        "sample_id": row["sample_id"],
        "dry_run_status": "blocked_as_expected" if passed else "failed",
        "schema_valid": schema_valid,
        "source_policy_valid": source_policy_valid,
        "url_string_valid": url_valid,
        "local_output_path_valid": path_valid,
        "checksum_policy_valid": checksum_valid,
        "provenance_policy_valid": provenance_valid,
        "blocked_source_policy_valid": blocked_valid,
        "network_called": False,
        "file_downloaded": False,
        "raw_dir_created": False,
        "raw_file_written": False,
        "adapter_run": False,
        "ready_for_execution_after_dry_run": False,
        "blocking_reasons": [] if passed else ["blocked_source_dry_run_validation_failed"],
    }


def run_pilot_download_manifest_dry_run_v0() -> dict[str, Any]:
    rows = _read_csv(STEP12R_PILOT_MANIFEST_CSV)
    schema_valid = _csv_columns(STEP12R_PILOT_MANIFEST_CSV) == PILOT_DOWNLOAD_MANIFEST_COLUMNS
    dry_rows: list[dict[str, Any]] = []
    for row in rows:
        if row["source_name"] == "PDB/mmCIF direct":
            dry_rows.append(_dry_run_row_for_pdb(row, schema_valid))
        elif row["source_name"] == "local curated":
            dry_rows.append(_dry_run_row_for_local(row, schema_valid))
        elif row["source_name"] in EXPECTED_BLOCKED_SOURCES:
            dry_rows.append(_dry_run_row_for_blocked(row, schema_valid))
        else:
            dry_rows.append(
                {
                    "job_id": row["job_id"],
                    "source_name": row["source_name"],
                    "job_type": row["job_type"],
                    "pdb_id": row["pdb_id"],
                    "sample_id": row["sample_id"],
                    "dry_run_status": "failed",
                    "schema_valid": schema_valid,
                    "source_policy_valid": False,
                    "url_string_valid": False,
                    "local_output_path_valid": False,
                    "checksum_policy_valid": False,
                    "provenance_policy_valid": False,
                    "blocked_source_policy_valid": False,
                    "network_called": False,
                    "file_downloaded": False,
                    "raw_dir_created": False,
                    "raw_file_written": False,
                    "adapter_run": False,
                    "ready_for_execution_after_dry_run": False,
                    "blocking_reasons": ["unknown_source_in_pilot_manifest"],
                }
            )
    return {"dry_run_rows": dry_rows}


def build_dry_run_summary_v0(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pdb_rows = [row for row in rows if row["source_name"] == "PDB/mmCIF direct"]
    local_rows = [row for row in rows if row["source_name"] == "local curated"]
    blocked_rows = [row for row in rows if row["source_name"] in EXPECTED_BLOCKED_SOURCES]
    passed_rows = [row for row in rows if row["dry_run_status"] == "passed"]
    blocked_expected_rows = [row for row in rows if row["dry_run_status"] == "blocked_as_expected"]
    failed_rows = [row for row in rows if row["dry_run_status"] == "failed"]
    allowed_rows = pdb_rows + local_rows
    return {
        "pilot_download_dry_run_defined": True,
        "pilot_download_dry_run_table_written": True,
        "dry_run_total_rows": len(rows),
        "dry_run_passed_rows": len(passed_rows),
        "dry_run_blocked_as_expected_rows": len(blocked_expected_rows),
        "dry_run_failed_rows": len(failed_rows),
        "dry_run_pdb_direct_passed_rows": sum(1 for row in pdb_rows if row["dry_run_status"] == "passed"),
        "dry_run_local_curated_passed_rows": sum(1 for row in local_rows if row["dry_run_status"] == "passed"),
        "dry_run_blocked_source_rows": len(blocked_rows),
        "dry_run_network_called": any(row["network_called"] is True for row in rows),
        "dry_run_files_downloaded": any(row["file_downloaded"] is True for row in rows),
        "dry_run_raw_dirs_created": any(row["raw_dir_created"] is True for row in rows),
        "dry_run_raw_files_written": any(row["raw_file_written"] is True for row in rows),
        "dry_run_adapters_run": any(row["adapter_run"] is True for row in rows),
        "all_allowed_pilot_jobs_ready_for_execution_after_dry_run": all(
            row["ready_for_execution_after_dry_run"] is True for row in allowed_rows
        ),
        "all_blocked_sources_remain_not_ready_for_execution": all(
            row["ready_for_execution_after_dry_run"] is False for row in blocked_rows
        ),
        "dry_run_validated_manifest_schema": all(row["schema_valid"] is True for row in rows),
        "dry_run_validated_url_strings": all(row["url_string_valid"] is True for row in rows),
        "dry_run_validated_local_output_paths": all(row["local_output_path_valid"] is True for row in rows),
        "dry_run_validated_checksum_policy": all(row["checksum_policy_valid"] is True for row in rows),
        "dry_run_validated_provenance_policy": all(row["provenance_policy_valid"] is True for row in rows),
        "dry_run_validated_blocked_source_policy": all(row["blocked_source_policy_valid"] is True for row in rows),
        "ready_to_execute_pilot_download_after_dry_run": len(failed_rows) == 0 and all(
            row["ready_for_execution_after_dry_run"] is True for row in allowed_rows
        ),
        "pilot_download_execution_allowed_in_this_step": False,
        "ready_to_download_large_scale_data_now": False,
    }


def build_real_covalent_pilot_download_dry_run_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12r_validated = validate_step12r_pilot_download_manifest_gate_v0()
    except Exception as exc:
        step12r_validated = False
        blockers.append(f"step12r_validation_failed:{type(exc).__name__}:{exc}")
    step12r_manifest = _load_json(STEP12R_MANIFEST_JSON)
    dry_run = run_pilot_download_manifest_dry_run_v0()
    dry_summary = build_dry_run_summary_v0(dry_run["dry_run_rows"])
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    passed = bool(
        step12r_validated
        and step12r_manifest["step12b_mask_level_aware_validator_validated"]
        and dry_summary["pilot_download_dry_run_defined"]
        and dry_summary["dry_run_total_rows"] == 9
        and dry_summary["dry_run_passed_rows"] == 6
        and dry_summary["dry_run_blocked_as_expected_rows"] == 3
        and dry_summary["dry_run_failed_rows"] == 0
        and dry_summary["dry_run_pdb_direct_passed_rows"] == 3
        and dry_summary["dry_run_local_curated_passed_rows"] == 3
        and dry_summary["dry_run_blocked_source_rows"] == 3
        and not dry_summary["dry_run_network_called"]
        and not dry_summary["dry_run_files_downloaded"]
        and not dry_summary["dry_run_raw_dirs_created"]
        and not dry_summary["dry_run_raw_files_written"]
        and not dry_summary["dry_run_adapters_run"]
        and dry_summary["all_allowed_pilot_jobs_ready_for_execution_after_dry_run"]
        and dry_summary["all_blocked_sources_remain_not_ready_for_execution"]
        and dry_summary["dry_run_validated_manifest_schema"]
        and dry_summary["dry_run_validated_url_strings"]
        and dry_summary["dry_run_validated_local_output_paths"]
        and dry_summary["dry_run_validated_checksum_policy"]
        and dry_summary["dry_run_validated_provenance_policy"]
        and dry_summary["dry_run_validated_blocked_source_policy"]
        and dry_summary["ready_to_execute_pilot_download_after_dry_run"]
        and not dry_summary["pilot_download_execution_allowed_in_this_step"]
        and not dry_summary["ready_to_download_large_scale_data_now"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_pilot_download_dry_run_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12r_pilot_download_manifest_gate_validated": step12r_validated,
        "step12b_mask_level_aware_validator_validated": step12r_manifest["step12b_mask_level_aware_validator_validated"],
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "current_sample_count": step12r_manifest["current_sample_count"],
        "metadata_completeness_ratio_text": step12r_manifest["metadata_completeness_ratio_text"],
        "metadata_gap_level": step12r_manifest["metadata_gap_level"],
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        **dry_summary,
        "data_downloaded": False,
        "external_network_called": False,
        "raw_storage_directories_created": False,
        "raw_download_files_written": False,
        "raw_structure_files_written": False,
        "adapter_implementation_written": False,
        "adapter_execution_run": False,
        "rdkit_processing_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "coordinate_geometry_calculation_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "enriched_sample_index_written": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "formal_training_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "real_covalent_pilot_download_dry_run_gate_passed": passed,
        "pilot_download_dry_run_contract_defined": passed,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "dry_run_rows": dry_run["dry_run_rows"],
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12r_precondition": {
            "step12r_pilot_download_manifest_gate_validated": manifest["step12r_pilot_download_manifest_gate_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "manifest_schema_validation": {
            "dry_run_total_rows": manifest["dry_run_total_rows"],
            "dry_run_validated_manifest_schema": manifest["dry_run_validated_manifest_schema"],
        },
        "pdb_direct_url_path_checksum_validation": {
            "dry_run_pdb_direct_passed_rows": manifest["dry_run_pdb_direct_passed_rows"],
            "dry_run_validated_url_strings": manifest["dry_run_validated_url_strings"],
            "dry_run_validated_checksum_policy": manifest["dry_run_validated_checksum_policy"],
        },
        "local_curated_validation": {
            "dry_run_local_curated_passed_rows": manifest["dry_run_local_curated_passed_rows"],
            "dry_run_validated_provenance_policy": manifest["dry_run_validated_provenance_policy"],
        },
        "blocked_source_policy_validation": {
            "dry_run_blocked_source_rows": manifest["dry_run_blocked_source_rows"],
            "dry_run_validated_blocked_source_policy": manifest["dry_run_validated_blocked_source_policy"],
        },
        "dry_run_safety_boundary": {
            "dry_run_network_called": manifest["dry_run_network_called"],
            "dry_run_files_downloaded": manifest["dry_run_files_downloaded"],
            "dry_run_raw_files_written": manifest["dry_run_raw_files_written"],
        },
        "dry_run_execution_readiness": {
            "ready_to_execute_pilot_download_after_dry_run": manifest["ready_to_execute_pilot_download_after_dry_run"],
            "pilot_download_execution_allowed_in_this_step": manifest["pilot_download_execution_allowed_in_this_step"],
        },
        "next_step_decision": {
            "real_covalent_pilot_download_dry_run_gate_passed": manifest["real_covalent_pilot_download_dry_run_gate_passed"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
