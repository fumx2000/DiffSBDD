from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_pilot_download_manifest_gate_v0"
PREVIOUS_STAGE = "real_covalent_source_registry_license_audit_gate_v0"

STEP12Q_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_source_registry_license_audit_gate_v0/"
    "real_covalent_source_registry_license_audit_gate_manifest.json"
)
STEP12Q_AUDIT_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_source_registry_license_audit_gate_v0/"
    "real_covalent_source_registry_license_audit_table.csv"
)
STEP12Q_SUMMARY_MD = Path("docs/real_covalent_source_registry_license_audit_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_pilot_download_manifest_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_manifest_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_pilot_download_manifest_gate_manifest.json"
PILOT_DOWNLOAD_MANIFEST_CSV = OUTPUT_ROOT / "real_covalent_pilot_download_manifest.csv"
SUMMARY_MD = Path("docs/real_covalent_pilot_download_manifest_gate_v0_summary.md")

INPUT_SOURCE = "real_covalent_training_tensor_materialized_v0"
SELECTED_REAL_SAMPLE_INDEX = Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"

TRAIN_READY_SCOPE_V1 = "cys_with_known_reconstruction_template_only"
NON_CYS_DATA_BULK_CLEANING_POLICY = "identify_classify_defer_until_template_gate"
RECOMMENDED_NEXT_STEP = "real_covalent_pilot_download_dry_run_gate"

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
}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

PDB_MMCIF_URL_TEMPLATE = "https://files.rcsb.org/download/{pdb_id}.cif.gz"
PDB_MMCIF_FILE_TYPE = "pdbx_mmcif_gzip"
PDB_USAGE_POLICY_STATUS = "verified_cc0_for_pdb_archive"

PILOT_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
PILOT_LOCAL_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]
BLOCKED_SOURCES = ["CovPDB", "CovBinderInPDB", "CovalentInDB"]
ALLOWED_PILOT_SOURCES = ["PDB/mmCIF direct", "local curated"]

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


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


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


def validate_step12q_source_registry_license_audit_gate_v0() -> bool:
    if not STEP12Q_MANIFEST_JSON.is_file() or not STEP12Q_AUDIT_TABLE_CSV.is_file() or not STEP12Q_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12Q outputs are missing")
    manifest = _load_json(STEP12Q_MANIFEST_JSON)
    rows = _read_csv(STEP12Q_AUDIT_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_multi_source_dataset_ingestion_design_gate_v0",
        "step12p_multi_source_dataset_ingestion_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "source_registry_license_audit_seed_defined": True,
        "source_registry_audit_record_count": 5,
        "audited_source_names": ["CovPDB", "CovBinderInPDB", "CovalentInDB", "PDB/mmCIF direct", "local curated"],
        "sources_with_verified_license_count": 2,
        "sources_with_verified_license": ALLOWED_PILOT_SOURCES,
        "sources_requiring_manual_license_review_count": 3,
        "sources_requiring_manual_license_review": BLOCKED_SOURCES,
        "sources_pilot_candidate_count": 2,
        "sources_pilot_candidate_after_audit": ALLOWED_PILOT_SOURCES,
        "sources_bulk_download_candidate_count": 0,
        "all_bulk_downloads_disabled_after_audit": True,
        "license_decision_policy_defined": True,
        "explicit_license_required_for_bulk_download": True,
        "unclear_license_blocks_bulk_download": True,
        "unclear_license_blocks_pilot_download": True,
        "publication_found_is_not_license_clearance": True,
        "free_web_access_is_not_bulk_download_permission": True,
        "pilot_eligibility_decision_defined": True,
        "pilot_eligible_sources_after_audit": ALLOWED_PILOT_SOURCES,
        "pilot_blocked_sources_after_audit": BLOCKED_SOURCES,
        "ready_to_create_pilot_download_manifest": True,
        "ready_to_download_large_scale_data_now": False,
        "pilot_download_allowed_after_this_step": False,
        "bulk_download_allowed_after_this_step": False,
        "source_registry_license_audit_table_written": True,
        "source_registry_json_for_download_written": False,
        "download_manifest_written": False,
        "raw_registry_written": False,
        "raw_data_written": False,
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
        "real_covalent_source_registry_license_audit_gate_passed": True,
        "source_registry_license_audit_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_pilot_download_manifest_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12q_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(len(rows) == 5, "step12q_audit_table_row_count_invalid", blockers)
    _expect([row["source_name"] for row in rows] == expected["audited_source_names"], "step12q_audit_table_source_order_invalid", blockers)
    by_source = {row["source_name"]: row for row in rows}
    for source in ALLOWED_PILOT_SOURCES:
        _expect(by_source[source]["pilot_download_candidate_after_audit"] == "True", f"step12q_pilot_candidate_invalid:{source}", blockers)
        _expect(by_source[source]["bulk_download_candidate_after_audit"] == "False", f"step12q_bulk_candidate_invalid:{source}", blockers)
    for source in BLOCKED_SOURCES:
        _expect(by_source[source]["license_usage_status"] == "requires_manual_review", f"step12q_blocked_license_invalid:{source}", blockers)
        _expect(by_source[source]["pilot_download_candidate_after_audit"] == "False", f"step12q_blocked_pilot_invalid:{source}", blockers)
    summary = STEP12Q_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "source registry license audit gate",
        "not downloading",
        "not adapter implementation",
        "not enrichment",
        "not split",
        "not training",
        "manual web-audit seed",
        "PDB archive license status verified CC0",
        "local project controlled",
        "CovPDB / CovBinderInPDB / CovalentInDB require manual license review",
        "Publication found is not license clearance",
        "Free web access is not bulk download permission",
        "All bulk downloads disabled",
        "Pilot candidates after audit are PDB/mmCIF direct and local curated",
        "No data download/network/raw dirs/raw files/adapters",
        "real_covalent_pilot_download_manifest_gate",
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12q_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _extract_pdb_id_from_sample_id(sample_id: str) -> str:
    parts = sample_id.split("_")
    if len(parts) < 3:
        raise ValueError(f"sample_id_pdb_id_unparseable:{sample_id}")
    return parts[2]


def audit_current_sample_index_for_pilot_v0() -> dict[str, Any]:
    if not SELECTED_REAL_SAMPLE_INDEX.is_file():
        raise FileNotFoundError(f"sample_index_missing:{SELECTED_REAL_SAMPLE_INDEX}")
    rows = _read_csv(SELECTED_REAL_SAMPLE_INDEX)
    sample_ids = [row["sample_id"] for row in rows]
    pdb_ids = [_extract_pdb_id_from_sample_id(sample_id) for sample_id in sample_ids]
    return {
        "sample_index_exists": True,
        "sample_index_current_sample_count": len(rows),
        "sample_index_sample_ids": sample_ids,
        "pilot_pdb_ids_derived_from_sample_ids": pdb_ids,
        "pilot_pdb_id_derivation_authoritative_for_manifest": sample_ids == PILOT_LOCAL_SAMPLE_IDS and pdb_ids == PILOT_PDB_IDS,
        "npz_files_loaded": False,
        "npz_contents_read": False,
    }


def build_pilot_download_manifest_rows_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pdb_id in PILOT_PDB_IDS:
        rows.append(
            {
                "job_id": f"pdb_mmcif_direct_{pdb_id}",
                "source_name": "PDB/mmCIF direct",
                "adapter_name": "pdb_direct_adapter",
                "job_type": "pdb_mmcif_download",
                "pilot_scope": "pdb_direct_three_current_smoke_pdb_ids",
                "source_license_status": PDB_USAGE_POLICY_STATUS,
                "source_license_verified_for_pilot": True,
                "source_requires_manual_review": False,
                "pdb_id": pdb_id,
                "sample_id": "",
                "candidate_download_url": PDB_MMCIF_URL_TEMPLATE.format(pdb_id=pdb_id),
                "url_template": PDB_MMCIF_URL_TEMPLATE,
                "url_template_verified": True,
                "file_type": PDB_MMCIF_FILE_TYPE,
                "compression": "gzip",
                "expected_local_output_path": f"data/raw/covalent_sources/pdb_mmcif_direct/structures/{pdb_id}.cif.gz",
                "raw_storage_root": "data/raw/covalent_sources",
                "raw_subdir": "pdb_mmcif_direct/structures",
                "checksum_required": True,
                "sha256_expected_now": "not_available_until_download",
                "checksum_status": "pending_download",
                "resume_supported": True,
                "retry_policy": "max_retries_3_exponential_backoff_design",
                "provenance_required": True,
                "download_enabled_in_this_step": False,
                "ready_for_dry_run": True,
                "ready_for_execution": False,
                "blocked_reason": "download_execution_not_allowed_in_manifest_gate",
                "notes": "manifest row only; no raw file written",
            }
        )
    for sample_id in PILOT_LOCAL_SAMPLE_IDS:
        rows.append(
            {
                "job_id": f"local_curated_{sample_id}",
                "source_name": "local curated",
                "adapter_name": "local_curated_adapter",
                "job_type": "local_curated_register_existing_sample",
                "pilot_scope": "local_curated_current_smoke_samples",
                "source_license_status": "local_project_controlled",
                "source_license_verified_for_pilot": True,
                "source_requires_manual_review": False,
                "pdb_id": _extract_pdb_id_from_sample_id(sample_id),
                "sample_id": sample_id,
                "candidate_download_url": "local_only",
                "url_template": "local_only",
                "url_template_verified": True,
                "file_type": "local_curated_existing_record",
                "compression": "none",
                "expected_local_output_path": "local_curated_existing_sample_index",
                "raw_storage_root": "not_applicable",
                "raw_subdir": "not_applicable",
                "checksum_required": False,
                "sha256_expected_now": "not_applicable",
                "checksum_status": "not_applicable",
                "resume_supported": False,
                "retry_policy": "not_applicable",
                "provenance_required": True,
                "download_enabled_in_this_step": False,
                "ready_for_dry_run": True,
                "ready_for_execution": False,
                "blocked_reason": "manual_provenance_manifest_not_created_yet",
                "notes": "existing sample_index row only; no raw file written",
            }
        )
    adapter_names = {
        "CovPDB": "covpdb_adapter",
        "CovBinderInPDB": "covbinderinpdb_adapter",
        "CovalentInDB": "covalentindb_adapter",
    }
    for source in BLOCKED_SOURCES:
        rows.append(
            {
                "job_id": f"blocked_{source.lower().replace('/', '_')}",
                "source_name": source,
                "adapter_name": adapter_names[source],
                "job_type": "blocked_source_no_pilot_download",
                "pilot_scope": "blocked_by_source_registry_license_audit",
                "source_license_status": "requires_manual_review",
                "source_license_verified_for_pilot": False,
                "source_requires_manual_review": True,
                "pdb_id": "",
                "sample_id": "",
                "candidate_download_url": "",
                "url_template": "",
                "url_template_verified": False,
                "file_type": "",
                "compression": "",
                "expected_local_output_path": "",
                "raw_storage_root": "",
                "raw_subdir": "",
                "checksum_required": False,
                "sha256_expected_now": "",
                "checksum_status": "",
                "resume_supported": False,
                "retry_policy": "",
                "provenance_required": False,
                "download_enabled_in_this_step": False,
                "ready_for_dry_run": False,
                "ready_for_execution": False,
                "blocked_reason": "manual_license_review_required",
                "notes": "blocked by Step 12Q license audit",
            }
        )
    return rows


def build_pilot_manifest_summary_v0(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pilot_rows = [row for row in rows if row["source_name"] in ALLOWED_PILOT_SOURCES]
    blocked_rows = [row for row in rows if row["source_name"] in BLOCKED_SOURCES]
    pdb_rows = [row for row in rows if row["source_name"] == "PDB/mmCIF direct"]
    local_rows = [row for row in rows if row["source_name"] == "local curated"]
    return {
        "pilot_download_manifest_defined": True,
        "pilot_download_manifest_written": True,
        "pilot_download_manifest_row_count": len(rows),
        "pilot_download_job_count": len(pilot_rows),
        "blocked_source_row_count": len(blocked_rows),
        "pdb_direct_pilot_job_count": len(pdb_rows),
        "local_curated_pilot_job_count": len(local_rows),
        "pilot_pdb_ids": [row["pdb_id"] for row in pdb_rows],
        "pilot_local_sample_ids": [row["sample_id"] for row in local_rows],
        "blocked_sources": [row["source_name"] for row in blocked_rows],
        "allowed_pilot_sources": ALLOWED_PILOT_SOURCES,
        "all_pilot_jobs_download_disabled_in_this_step": all(row["download_enabled_in_this_step"] is False for row in pilot_rows),
        "all_pilot_jobs_ready_for_dry_run": all(row["ready_for_dry_run"] is True for row in pilot_rows),
        "any_pilot_job_ready_for_execution": any(row["ready_for_execution"] is True for row in pilot_rows),
        "all_blocked_sources_not_ready_for_dry_run": all(row["ready_for_dry_run"] is False for row in blocked_rows),
        "rcsb_mmcif_url_template_defined": all(row["url_template"] == PDB_MMCIF_URL_TEMPLATE for row in pdb_rows),
        "rcsb_mmcif_url_template_verified_by_external_audit": all(row["url_template_verified"] is True for row in pdb_rows),
        "checksum_required_for_pdb_downloads": all(row["checksum_required"] is True for row in pdb_rows),
        "provenance_required_for_all_pilot_jobs": all(row["provenance_required"] is True for row in pilot_rows),
        "pilot_manifest_does_not_grant_download_execution": all(row["ready_for_execution"] is False for row in rows),
    }


def build_download_dry_run_readiness_policy_v0() -> dict[str, Any]:
    return {
        "download_dry_run_readiness_policy_defined": True,
        "dry_run_checks_url_strings_only": True,
        "dry_run_may_create_raw_dirs": False,
        "dry_run_may_download_files": False,
        "dry_run_may_call_network": False,
        "dry_run_may_validate_manifest_schema": True,
        "dry_run_may_validate_local_output_paths": True,
        "dry_run_may_validate_source_license_status": True,
        "dry_run_may_validate_blocked_sources": True,
        "pilot_download_execution_requires_next_gate": True,
        "pilot_download_execution_allowed_after_this_step": False,
        "ready_to_run_pilot_download_dry_run": True,
        "ready_to_execute_pilot_download": False,
        "ready_to_download_large_scale_data_now": False,
    }


def build_real_covalent_pilot_download_manifest_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12q_validated = validate_step12q_source_registry_license_audit_gate_v0()
    except Exception as exc:
        step12q_validated = False
        blockers.append(f"step12q_validation_failed:{type(exc).__name__}:{exc}")
    step12q_manifest = _load_json(STEP12Q_MANIFEST_JSON)
    try:
        sample_index_audit = audit_current_sample_index_for_pilot_v0()
    except Exception as exc:
        sample_index_audit = {
            "sample_index_exists": False,
            "sample_index_current_sample_count": 0,
            "sample_index_sample_ids": [],
            "pilot_pdb_ids_derived_from_sample_ids": [],
            "pilot_pdb_id_derivation_authoritative_for_manifest": False,
            "npz_files_loaded": False,
            "npz_contents_read": False,
        }
        blockers.append(f"sample_index_audit_failed:{type(exc).__name__}:{exc}")
    rows = build_pilot_download_manifest_rows_v0()
    pilot_summary = build_pilot_manifest_summary_v0(rows)
    dry_run_policy = build_download_dry_run_readiness_policy_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12q_validated
        and step12q_manifest["step12b_mask_level_aware_validator_validated"]
        and sample_index_audit["sample_index_exists"]
        and sample_index_audit["sample_index_current_sample_count"] == 3
        and sample_index_audit["sample_index_sample_ids"] == PILOT_LOCAL_SAMPLE_IDS
        and sample_index_audit["pilot_pdb_ids_derived_from_sample_ids"] == PILOT_PDB_IDS
        and sample_index_audit["pilot_pdb_id_derivation_authoritative_for_manifest"]
        and pilot_summary["pilot_download_manifest_row_count"] == 9
        and pilot_summary["pilot_download_job_count"] == 6
        and pilot_summary["blocked_source_row_count"] == 3
        and pilot_summary["pdb_direct_pilot_job_count"] == 3
        and pilot_summary["local_curated_pilot_job_count"] == 3
        and pilot_summary["all_pilot_jobs_download_disabled_in_this_step"]
        and pilot_summary["all_pilot_jobs_ready_for_dry_run"]
        and not pilot_summary["any_pilot_job_ready_for_execution"]
        and pilot_summary["all_blocked_sources_not_ready_for_dry_run"]
        and pilot_summary["rcsb_mmcif_url_template_defined"]
        and pilot_summary["rcsb_mmcif_url_template_verified_by_external_audit"]
        and pilot_summary["checksum_required_for_pdb_downloads"]
        and pilot_summary["provenance_required_for_all_pilot_jobs"]
        and pilot_summary["pilot_manifest_does_not_grant_download_execution"]
        and dry_run_policy["download_dry_run_readiness_policy_defined"]
        and dry_run_policy["ready_to_run_pilot_download_dry_run"]
        and not dry_run_policy["ready_to_execute_pilot_download"]
        and not dry_run_policy["ready_to_download_large_scale_data_now"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_pilot_download_manifest_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12q_source_registry_license_audit_gate_validated": step12q_validated,
        "step12b_mask_level_aware_validator_validated": step12q_manifest["step12b_mask_level_aware_validator_validated"],
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "current_sample_count": step12q_manifest["current_sample_count"],
        "required_split_metadata_field_count": step12q_manifest["required_split_metadata_field_count"],
        "present_required_metadata_field_count": step12q_manifest["present_required_metadata_field_count"],
        "missing_required_metadata_field_count": step12q_manifest["missing_required_metadata_field_count"],
        "metadata_completeness_ratio_text": step12q_manifest["metadata_completeness_ratio_text"],
        "metadata_gap_level": step12q_manifest["metadata_gap_level"],
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        **sample_index_audit,
        **pilot_summary,
        **dry_run_policy,
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
        "real_covalent_pilot_download_manifest_gate_passed": passed,
        "pilot_download_manifest_contract_defined": passed,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "pilot_download_manifest_rows": rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12q_precondition": {
            "step12q_source_registry_license_audit_gate_validated": manifest[
                "step12q_source_registry_license_audit_gate_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "sample_index_pilot_id_audit": {
            "sample_index_current_sample_count": manifest["sample_index_current_sample_count"],
            "pilot_pdb_ids_derived_from_sample_ids": manifest["pilot_pdb_ids_derived_from_sample_ids"],
        },
        "pilot_download_manifest_rows": {
            "pilot_download_manifest_row_count": manifest["pilot_download_manifest_row_count"],
            "pilot_download_job_count": manifest["pilot_download_job_count"],
        },
        "pdb_direct_pilot_jobs": {
            "pdb_direct_pilot_job_count": manifest["pdb_direct_pilot_job_count"],
            "rcsb_mmcif_url_template_defined": manifest["rcsb_mmcif_url_template_defined"],
        },
        "local_curated_pilot_jobs": {
            "local_curated_pilot_job_count": manifest["local_curated_pilot_job_count"],
            "pilot_local_sample_ids": manifest["pilot_local_sample_ids"],
        },
        "blocked_source_rows": {
            "blocked_source_row_count": manifest["blocked_source_row_count"],
            "blocked_sources": manifest["blocked_sources"],
        },
        "download_dry_run_readiness_policy": {
            "ready_to_run_pilot_download_dry_run": manifest["ready_to_run_pilot_download_dry_run"],
            "ready_to_execute_pilot_download": manifest["ready_to_execute_pilot_download"],
        },
        "safety_and_next_step_decision": {
            "data_downloaded": manifest["data_downloaded"],
            "external_network_called": manifest["external_network_called"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
