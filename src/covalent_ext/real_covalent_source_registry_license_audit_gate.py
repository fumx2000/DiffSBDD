from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_source_registry_license_audit_gate_v0"
PREVIOUS_STAGE = "real_covalent_multi_source_dataset_ingestion_design_gate_v0"

STEP12P_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_multi_source_dataset_ingestion_design_gate_v0/"
    "real_covalent_multi_source_dataset_ingestion_design_gate_manifest.json"
)
STEP12P_DESIGN_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_multi_source_dataset_ingestion_design_gate_v0/"
    "real_covalent_multi_source_dataset_ingestion_design_gate_table.csv"
)
STEP12P_SUMMARY_MD = Path("docs/real_covalent_multi_source_dataset_ingestion_design_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_source_registry_license_audit_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_source_registry_license_audit_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_source_registry_license_audit_gate_manifest.json"
SOURCE_REGISTRY_AUDIT_TABLE_CSV = OUTPUT_ROOT / "real_covalent_source_registry_license_audit_table.csv"
SUMMARY_MD = Path("docs/real_covalent_source_registry_license_audit_gate_v0_summary.md")

INPUT_SOURCE = "real_covalent_training_tensor_materialized_v0"
SELECTED_REAL_SAMPLE_INDEX = Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"

TRAIN_READY_SCOPE_V1 = "cys_with_known_reconstruction_template_only"
NON_CYS_DATA_BULK_CLEANING_POLICY = "identify_classify_defer_until_template_gate"

RECOMMENDED_NEXT_STEP = "real_covalent_pilot_download_manifest_gate"

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

AUDIT_TABLE_COLUMNS = [
    "source_name",
    "adapter_name",
    "source_category",
    "source_description",
    "candidate_homepage_url",
    "candidate_publication_url",
    "candidate_usage_policy_url",
    "candidate_download_docs_url",
    "url_found_by_audit",
    "scientific_source_verified",
    "source_url_currentness_status",
    "license_usage_status",
    "requires_manual_license_review",
    "usage_note",
    "expected_3d_complex_availability",
    "expected_covalent_bond_annotation_availability",
    "expected_atom_mapping_availability",
    "recommended_role",
    "download_enabled_after_audit",
    "pilot_download_candidate_after_audit",
    "bulk_download_candidate_after_audit",
    "audit_confidence",
    "audit_blocking_reasons",
    "citation_hint",
]

PLANNED_SOURCE_NAMES = ["CovPDB", "CovBinderInPDB", "CovalentInDB", "PDB/mmCIF direct", "local curated"]


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


def validate_step12p_multi_source_dataset_ingestion_design_gate_v0() -> bool:
    if not STEP12P_MANIFEST_JSON.is_file() or not STEP12P_DESIGN_TABLE_CSV.is_file() or not STEP12P_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12P outputs are missing")
    manifest = _load_json(STEP12P_MANIFEST_JSON)
    rows = _read_csv(STEP12P_DESIGN_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_split_metadata_enrichment_design_gate_v0",
        "step12o_split_metadata_enrichment_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "current_sample_count": 3,
        "required_split_metadata_field_count": 38,
        "present_required_metadata_field_count": 2,
        "missing_required_metadata_field_count": 36,
        "metadata_completeness_ratio_text": "2/38",
        "metadata_gap_level": "severe",
        "source_registry_schema_defined": True,
        "source_registry_entry_count": 5,
        "planned_source_registry_entries": PLANNED_SOURCE_NAMES,
        "source_urls_are_placeholders": True,
        "source_url_currentness_not_verified": True,
        "license_usage_currentness_not_verified": True,
        "source_registry_license_audit_required": True,
        "source_registry_written": False,
        "raw_storage_layout_defined": True,
        "raw_storage_root_design": "data/raw/covalent_sources",
        "raw_storage_directories_created": False,
        "download_job_manifest_schema_defined": True,
        "download_jobs_written": False,
        "download_jobs_run": False,
        "source_adapter_interface_contract_defined": True,
        "all_adapters_must_emit_canonical_raw_records": True,
        "adapter_implementation_allowed_after_this_step": False,
        "adapter_execution_allowed_after_this_step": False,
        "source_specific_ingestion_design_details_defined": True,
        "duplicate_provenance_priority_policy_defined": True,
        "small_pilot_ingestion_plan_defined": True,
        "pilot_max_records_per_source": 3,
        "pilot_download_allowed_in_this_step": False,
        "large_scale_download_allowed_in_this_step": False,
        "git_data_policy_defined": True,
        "raw_downloads_must_not_be_committed": True,
        "raw_structures_must_not_be_committed": True,
        "generated_training_tensors_must_not_be_committed": True,
        "ready_to_create_source_registry_license_audit": True,
        "ready_to_download_large_scale_data_now": False,
        "data_downloaded": False,
        "external_network_called": False,
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
        "real_covalent_multi_source_dataset_ingestion_design_gate_passed": True,
        "multi_source_dataset_ingestion_design_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_source_registry_license_audit_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12p_{key}_invalid:{manifest[key]!r}", blockers)
    row_types = [row["row_type"] for row in rows]
    _expect(
        row_types
        == [
            "step12o_precondition",
            "multi_source_ingestion_concept",
            "source_registry_schema",
            "raw_storage_layout_design",
            "download_job_manifest_schema",
            "source_adapter_interface_contract",
            "source_specific_ingestion_design_details",
            "duplicate_provenance_priority_policy",
            "small_pilot_ingestion_plan",
            "git_data_policy",
            "safety_and_next_step_decision",
        ],
        "step12p_design_table_rows_invalid",
        blockers,
    )
    summary = STEP12P_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "multi-source dataset ingestion design gate",
        "not downloading",
        "not enrichment",
        "not split",
        "not training",
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "PDB/mmCIF direct",
        "local curated",
        "Source URL placeholders",
        "source registry license audit",
        "canonical raw covalent records",
        "cannot one-pot merge before normalization",
        "data/raw/covalent_sources",
        "created no raw dirs",
        "Download manifest, checksum, resume, and provenance",
        "Raw downloads and large binary structures cannot commit",
        "1-3 records per source",
        "No data download/network/source registry/raw dirs/adapters",
        "No RDKit/UniProt/CD-HIT/geometry/NPZ/training",
        "real_covalent_source_registry_license_audit_gate",
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12p_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_source_registry_license_audit_seed_v0() -> dict[str, Any]:
    records = [
        {
            "source_name": "CovPDB",
            "adapter_name": "covpdb_adapter",
            "source_category": "3d_covalent_complex_database",
            "source_description": "high-resolution 3D structures of biologically relevant covalent protein-ligand complexes, mined from PDB",
            "candidate_homepage_url": "https://drug-discovery.vm.uni-freiburg.de/covpdb/",
            "candidate_publication_url": "https://academic.oup.com/nar/article/50/D1/D445/6377397",
            "candidate_usage_policy_url": "",
            "candidate_download_docs_url": "",
            "url_found_by_audit": True,
            "scientific_source_verified": True,
            "source_url_currentness_status": "candidate_url_found_manual_review_required",
            "license_usage_status": "requires_manual_review",
            "requires_manual_license_review": True,
            "usage_note": "freely accessible web database, but explicit bulk-download/reuse/license terms need manual review before automated ingestion",
            "expected_3d_complex_availability": "likely_high_but_unverified",
            "expected_covalent_bond_annotation_availability": "likely_available_but_unverified",
            "expected_atom_mapping_availability": "source_dependent_unverified",
            "recommended_role": "high-value 3D covalent complex source after license/manual review",
            "download_enabled_after_audit": False,
            "pilot_download_candidate_after_audit": False,
            "bulk_download_candidate_after_audit": False,
            "audit_confidence": "medium",
            "audit_blocking_reasons": ["explicit_bulk_download_license_not_verified"],
            "citation_hint": "NAR 2022 CovPDB publication",
        },
        {
            "source_name": "CovBinderInPDB",
            "adapter_name": "covbinderinpdb_adapter",
            "source_category": "pdb_derived_covalent_binder_annotation_database",
            "source_description": "structure-based covalent binder database curated from PDB, including pre-reaction forms of covalent binders",
            "candidate_homepage_url": "",
            "candidate_publication_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9772242/",
            "candidate_usage_policy_url": "",
            "candidate_download_docs_url": "https://pubs.acs.org/doi/10.1021/acs.jcim.2c01216",
            "url_found_by_audit": True,
            "scientific_source_verified": True,
            "source_url_currentness_status": "publication_found_dataset_url_requires_manual_review",
            "license_usage_status": "requires_manual_review",
            "requires_manual_license_review": True,
            "usage_note": "publication/source is identified, but dataset download URL and reuse/license terms need manual review",
            "expected_3d_complex_availability": "pdb_derived_likely_but_unverified",
            "expected_covalent_bond_annotation_availability": "annotation_source_expected_but_unverified",
            "expected_atom_mapping_availability": "source_dependent_unverified",
            "recommended_role": "PDB-derived covalent binder annotation source, likely useful for pre-reaction reconstruction and residue diversity",
            "download_enabled_after_audit": False,
            "pilot_download_candidate_after_audit": False,
            "bulk_download_candidate_after_audit": False,
            "audit_confidence": "medium",
            "audit_blocking_reasons": ["dataset_download_endpoint_not_verified"],
            "citation_hint": "JCIM 2022 CovBinderInPDB publication",
        },
        {
            "source_name": "CovalentInDB",
            "adapter_name": "covalentindb_adapter",
            "source_category": "covalent_inhibitor_target_database",
            "source_description": "covalent inhibitor database; useful for inhibitor, target, warhead, reaction, bioactivity, and available cocrystal metadata",
            "candidate_homepage_url": "http://cadd.zju.edu.cn/cidb",
            "candidate_publication_url": "https://academic.oup.com/nar/article/53/D1/D1322/7832349",
            "candidate_usage_policy_url": "",
            "candidate_download_docs_url": "",
            "url_found_by_audit": True,
            "scientific_source_verified": True,
            "source_url_currentness_status": "candidate_url_found_access_controls_possible",
            "license_usage_status": "requires_manual_review",
            "requires_manual_license_review": True,
            "usage_note": "official site may include robot test/access controls; bulk download/reuse/license and 3D complex availability need manual review",
            "expected_3d_complex_availability": "optional_cocrystal_metadata_unverified",
            "expected_covalent_bond_annotation_availability": "metadata_expected_but_unverified",
            "expected_atom_mapping_availability": "not_assumed_for_all_entries",
            "recommended_role": "warhead/reaction/target annotation and optional cocrystal source; not assumed to be direct 3D training source for all entries",
            "download_enabled_after_audit": False,
            "pilot_download_candidate_after_audit": False,
            "bulk_download_candidate_after_audit": False,
            "audit_confidence": "medium",
            "audit_blocking_reasons": ["robot_or_access_control_possible", "bulk_reuse_license_not_verified"],
            "citation_hint": "NAR 2025 CovalentInDB publication",
        },
        {
            "source_name": "PDB/mmCIF direct",
            "adapter_name": "pdb_direct_adapter",
            "source_category": "public_3d_structure_archive",
            "source_description": "direct PDB/mmCIF structure harvesting from RCSB/wwPDB",
            "candidate_homepage_url": "",
            "candidate_publication_url": "",
            "candidate_usage_policy_url": "https://www.rcsb.org/pages/usage-policy",
            "candidate_download_docs_url": "https://www.rcsb.org/docs/programmatic-access/file-download-services",
            "url_found_by_audit": True,
            "scientific_source_verified": True,
            "source_url_currentness_status": "official_policy_and_download_docs_found",
            "license_usage_status": "verified_cc0_for_pdb_archive",
            "requires_manual_license_review": False,
            "usage_note": "PDB archive data files are CC0 1.0; users should attribute original structure authors where possible; external integrated resources may have separate restrictions",
            "expected_3d_complex_availability": "primary_structure_archive",
            "expected_covalent_bond_annotation_availability": "link_or_conect_records_need_adapter_validation",
            "expected_atom_mapping_availability": "ccd_atom_names_need_adapter_validation",
            "recommended_role": "primary direct structure source for pilot after download manifest/rate/checksum policy",
            "download_enabled_after_audit": False,
            "pilot_download_candidate_after_audit": True,
            "bulk_download_candidate_after_audit": False,
            "audit_confidence": "high",
            "audit_blocking_reasons": ["download_manifest_not_created_yet"],
            "citation_hint": "RCSB/wwPDB usage policy and file download documentation",
        },
        {
            "source_name": "local curated",
            "adapter_name": "local_curated_adapter",
            "source_category": "local_project_curated_examples",
            "source_description": "current BTK/KRAS examples and future NLRP3 curated examples",
            "candidate_homepage_url": "local_only",
            "candidate_publication_url": "",
            "candidate_usage_policy_url": "",
            "candidate_download_docs_url": "",
            "url_found_by_audit": "not_applicable",
            "scientific_source_verified": "local_project_source",
            "source_url_currentness_status": "local_only",
            "license_usage_status": "local_project_controlled",
            "requires_manual_license_review": False,
            "usage_note": "manually curated examples must keep provenance, author, version, and manual override reason",
            "expected_3d_complex_availability": "project_curated",
            "expected_covalent_bond_annotation_availability": "project_curated",
            "expected_atom_mapping_availability": "project_curated",
            "recommended_role": "controlled sanity-check and NLRP3-specific pilot source",
            "download_enabled_after_audit": False,
            "pilot_download_candidate_after_audit": True,
            "bulk_download_candidate_after_audit": False,
            "audit_confidence": "high",
            "audit_blocking_reasons": ["manual_provenance_manifest_required"],
            "citation_hint": "local curated project provenance",
        },
    ]
    verified = [record["source_name"] for record in records if record["license_usage_status"] in {"verified_cc0_for_pdb_archive", "local_project_controlled"}]
    manual = [record["source_name"] for record in records if record["requires_manual_license_review"] is True]
    pilot = [record["source_name"] for record in records if record["pilot_download_candidate_after_audit"] is True]
    bulk = [record["source_name"] for record in records if record["bulk_download_candidate_after_audit"] is True]
    return {
        "source_registry_license_audit_seed_defined": True,
        "source_registry_audit_records": records,
        "source_registry_audit_record_count": len(records),
        "audited_source_names": [record["source_name"] for record in records],
        "sources_with_verified_license_count": len(verified),
        "sources_with_verified_license": verified,
        "sources_requiring_manual_license_review_count": len(manual),
        "sources_requiring_manual_license_review": manual,
        "sources_pilot_candidate_count": len(pilot),
        "sources_pilot_candidate_after_audit": pilot,
        "sources_bulk_download_candidate_count": len(bulk),
        "sources_bulk_download_candidate_after_audit": bulk,
        "all_bulk_downloads_disabled_after_audit": all(record["bulk_download_candidate_after_audit"] is False for record in records),
        "source_registry_audit_table_written": True,
    }


def build_license_decision_policy_v0() -> dict[str, Any]:
    return {
        "license_decision_policy_defined": True,
        "explicit_license_required_for_bulk_download": True,
        "unclear_license_blocks_bulk_download": True,
        "unclear_license_blocks_pilot_download": True,
        "pdb_direct_cc0_allows_future_pilot_manifest": True,
        "local_curated_allows_future_pilot_manifest": True,
        "non_pdb_sources_require_manual_license_review": True,
        "publication_found_is_not_license_clearance": True,
        "free_web_access_is_not_bulk_download_permission": True,
        "robot_access_control_blocks_automated_download": True,
        "manual_review_required_before_non_pdb_pilot": True,
        "license_audit_does_not_grant_download_permission": True,
    }


def build_pilot_eligibility_decision_v0(records: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [record["source_name"] for record in records if record["pilot_download_candidate_after_audit"] is True]
    blocked = [record["source_name"] for record in records if record["pilot_download_candidate_after_audit"] is False]
    return {
        "pilot_eligibility_decision_defined": True,
        "pilot_eligible_sources_after_audit": eligible,
        "pilot_blocked_sources_after_audit": blocked,
        "pilot_blocking_policy_by_source": {
            "PDB/mmCIF direct": "pilot_blocked_until_download_manifest",
            "local curated": "pilot_blocked_until_manual_provenance_manifest",
            "CovPDB": "blocked_by_manual_license_review",
            "CovBinderInPDB": "blocked_by_manual_license_review",
            "CovalentInDB": "blocked_by_manual_license_review",
        },
        "recommended_pilot_download_manifest_sources": eligible,
        "pilot_download_allowed_after_this_step": False,
        "ready_to_create_pilot_download_manifest": True,
        "ready_to_download_large_scale_data_now": False,
    }


def build_source_registry_audit_output_schema_v0() -> dict[str, Any]:
    return {
        "source_registry_audit_output_schema_defined": True,
        "source_registry_license_audit_table_required": True,
        "source_registry_license_audit_table_written": True,
        "source_registry_json_for_download_written": False,
        "download_manifest_written": False,
        "raw_registry_written": False,
        "raw_data_written": False,
        "source_registry_written": False,
    }


def build_real_covalent_source_registry_license_audit_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12p_validated = validate_step12p_multi_source_dataset_ingestion_design_gate_v0()
    except Exception as exc:
        step12p_validated = False
        blockers.append(f"step12p_validation_failed:{type(exc).__name__}:{exc}")
    step12p_manifest = _load_json(STEP12P_MANIFEST_JSON)
    seed = build_source_registry_license_audit_seed_v0()
    license_policy = build_license_decision_policy_v0()
    pilot = build_pilot_eligibility_decision_v0(seed["source_registry_audit_records"])
    outputs = build_source_registry_audit_output_schema_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12p_validated
        and seed["source_registry_license_audit_seed_defined"]
        and seed["source_registry_audit_record_count"] == 5
        and seed["sources_with_verified_license_count"] == 2
        and seed["sources_requiring_manual_license_review_count"] == 3
        and seed["sources_pilot_candidate_count"] == 2
        and seed["sources_bulk_download_candidate_count"] == 0
        and seed["all_bulk_downloads_disabled_after_audit"]
        and license_policy["license_decision_policy_defined"]
        and pilot["pilot_eligibility_decision_defined"]
        and outputs["source_registry_license_audit_table_written"]
        and not pilot["pilot_download_allowed_after_this_step"]
        and not outputs["download_manifest_written"]
        and not outputs["raw_data_written"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_source_registry_license_audit_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12p_multi_source_dataset_ingestion_design_gate_validated": step12p_validated,
        "step12b_mask_level_aware_validator_validated": step12p_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "current_sample_count": step12p_manifest["current_sample_count"],
        "required_split_metadata_field_count": step12p_manifest["required_split_metadata_field_count"],
        "present_required_metadata_field_count": step12p_manifest["present_required_metadata_field_count"],
        "missing_required_metadata_field_count": step12p_manifest["missing_required_metadata_field_count"],
        "metadata_completeness_ratio_text": step12p_manifest["metadata_completeness_ratio_text"],
        "metadata_gap_level": step12p_manifest["metadata_gap_level"],
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        **seed,
        **license_policy,
        **pilot,
        **outputs,
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
        "bulk_download_allowed_after_this_step": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "real_covalent_source_registry_license_audit_gate_passed": passed,
        "source_registry_license_audit_contract_defined": passed,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "audit_table_rows": seed["source_registry_audit_records"],
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12p_precondition": {
            "step12p_multi_source_dataset_ingestion_design_gate_validated": manifest[
                "step12p_multi_source_dataset_ingestion_design_gate_validated"
            ],
            "metadata_gap_level": manifest["metadata_gap_level"],
        },
        "source_registry_license_audit_seed": {
            "source_registry_license_audit_seed_defined": manifest["source_registry_license_audit_seed_defined"],
            "source_registry_audit_record_count": manifest["source_registry_audit_record_count"],
        },
        "source_registry_audit_records": {
            "audited_source_names": manifest["audited_source_names"],
            "sources_requiring_manual_license_review": manifest["sources_requiring_manual_license_review"],
        },
        "license_decision_policy": {
            "publication_found_is_not_license_clearance": manifest["publication_found_is_not_license_clearance"],
            "free_web_access_is_not_bulk_download_permission": manifest["free_web_access_is_not_bulk_download_permission"],
        },
        "pilot_eligibility_decision": {
            "pilot_eligible_sources_after_audit": manifest["pilot_eligible_sources_after_audit"],
            "pilot_download_allowed_after_this_step": manifest["pilot_download_allowed_after_this_step"],
        },
        "audit_output_schema": {
            "source_registry_license_audit_table_written": manifest["source_registry_license_audit_table_written"],
            "download_manifest_written": manifest["download_manifest_written"],
        },
        "safety_boundary": {
            "data_downloaded": manifest["data_downloaded"],
            "external_network_called": manifest["external_network_called"],
            "adapter_execution_run": manifest["adapter_execution_run"],
        },
        "next_step_decision": {
            "ready_to_create_pilot_download_manifest": manifest["ready_to_create_pilot_download_manifest"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
