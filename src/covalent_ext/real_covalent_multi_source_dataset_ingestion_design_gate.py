from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_multi_source_dataset_ingestion_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_split_metadata_enrichment_design_gate_v0"

STEP12O_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_split_metadata_enrichment_design_gate_v0/"
    "real_covalent_split_metadata_enrichment_design_gate_manifest.json"
)
STEP12O_DESIGN_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_split_metadata_enrichment_design_gate_v0/"
    "real_covalent_split_metadata_enrichment_design_gate_table.csv"
)
STEP12O_SUMMARY_MD = Path("docs/real_covalent_split_metadata_enrichment_design_gate_v0_summary.md")

STEP12N_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_split_metadata_inventory_gate_v0/"
    "real_covalent_split_metadata_inventory_gate_manifest.json"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_multi_source_dataset_ingestion_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_multi_source_dataset_ingestion_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_multi_source_dataset_ingestion_design_gate_manifest.json"
DESIGN_TABLE_CSV = OUTPUT_ROOT / "real_covalent_multi_source_dataset_ingestion_design_gate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_multi_source_dataset_ingestion_design_gate_v0_summary.md")

INPUT_SOURCE = "real_covalent_training_tensor_materialized_v0"
SELECTED_REAL_SAMPLE_INDEX = Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")

FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"

CANONICAL_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]

TRAIN_READY_SCOPE_V1 = "cys_with_known_reconstruction_template_only"
NON_CYS_DATA_BULK_CLEANING_POLICY = "identify_classify_defer_until_template_gate"

RECOMMENDED_NEXT_STEP = "real_covalent_source_registry_license_audit_gate"

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

PLANNED_SOURCE_ADAPTERS = [
    "covpdb_adapter",
    "covbinderinpdb_adapter",
    "covalentindb_adapter",
    "pdb_direct_adapter",
    "local_curated_adapter",
]
PLANNED_SOURCE_DISPLAY_NAMES = [
    "CovPDB",
    "CovBinderInPDB",
    "CovalentInDB",
    "PDB/mmCIF direct",
    "local curated",
]
CANONICAL_RAW_RECORD_FIELDS = [
    "source_dataset",
    "source_record_id",
    "source_version",
    "source_license_or_usage_note",
    "source_url_or_local_path",
    "pdb_id",
    "chain_id",
    "residue_id",
    "residue_type",
    "ligand_id",
    "ligand_structure_path",
    "protein_structure_path",
    "complex_structure_path",
    "covalent_bond_annotation_raw",
    "raw_warhead_annotation",
    "raw_reaction_annotation",
    "raw_quality_flags",
]
SOURCE_REGISTRY_ENTRY_FIELDS = [
    "source_name",
    "adapter_name",
    "source_category",
    "source_description",
    "source_url",
    "source_url_status",
    "source_version",
    "source_release_date",
    "license_or_usage_note",
    "license_audit_status",
    "requires_manual_license_review",
    "expected_raw_inputs",
    "expected_raw_file_types",
    "expected_raw_record_count_unknown",
    "expected_3d_complex_availability",
    "expected_covalent_bond_annotation_availability",
    "expected_atom_mapping_availability",
    "download_method_design",
    "download_requires_network",
    "local_cache_root",
    "raw_data_git_policy",
    "checksum_policy",
    "resume_policy",
    "provenance_policy",
    "adapter_output_schema",
    "quality_flags",
    "duplicate_keys",
    "source_priority_rank",
    "ingestion_enabled_after_audit",
    "blocking_reasons",
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


def validate_step12o_split_metadata_enrichment_design_gate_v0() -> bool:
    if not STEP12O_MANIFEST_JSON.is_file() or not STEP12O_DESIGN_TABLE_CSV.is_file() or not STEP12O_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12O outputs are missing")
    if not STEP12N_MANIFEST_JSON.is_file():
        raise FileNotFoundError("Step 12N manifest is missing")
    manifest = _load_json(STEP12O_MANIFEST_JSON)
    rows = _read_csv(STEP12O_DESIGN_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_split_metadata_inventory_gate_v0",
        "step12n_split_metadata_inventory_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "current_sample_count": 3,
        "required_split_metadata_field_count": 38,
        "present_required_metadata_field_count": 2,
        "missing_required_metadata_field_count": 36,
        "metadata_completeness_ratio_text": "2/38",
        "metadata_gap_level": "severe",
        "metadata_enrichment_concept_defined": True,
        "metadata_enrichment_definition": "convert_thin_materialization_index_into_authoritative_leakage_aware_split_metadata",
        "multi_source_adapter_architecture_defined": True,
        "heterogeneous_datasets_can_share_common_enrichment_pipeline": True,
        "source_specific_adapter_required": True,
        "canonical_raw_record_schema_required": True,
        "common_enrichment_pipeline_required": True,
        "direct_mixture_without_adapter_allowed": False,
        "one_pot_merge_before_normalization_allowed": False,
        "required_source_adapter_design_defined": True,
        "source_adapter_count": 5,
        "planned_source_adapters": PLANNED_SOURCE_ADAPTERS,
        "planned_source_adapter_display_names": PLANNED_SOURCE_DISPLAY_NAMES,
        "all_source_adapters_output_canonical_raw_records": True,
        "duplicate_detection_across_sources_required": True,
        "source_priority_policy_required": True,
        "enrichment_field_derivation_plan_defined": True,
        "rdkit_required_for_ligand_identity": True,
        "pdb_parser_required_for_protein_identity": True,
        "uniprot_mapping_required": True,
        "cdhit_or_equivalent_required_for_sequence_cluster": True,
        "coordinate_geometry_required": True,
        "warhead_smarts_library_required": True,
        "reaction_family_classifier_required": True,
        "reconstruction_template_registry_required": True,
        "enrichment_quality_policy_defined": True,
        "authoritative_metadata_required_for_final_split": True,
        "heuristic_metadata_allowed_for_inventory_only": True,
        "heuristic_metadata_allowed_for_final_split": False,
        "missing_authoritative_metadata_blocks_final_split": True,
        "missing_authoritative_metadata_blocks_training": True,
        "enrichment_output_schema_defined": True,
        "large_scale_data_transition_plan_defined": True,
        "ready_to_design_multi_source_ingestion": True,
        "ready_to_download_large_scale_data_now": False,
        "raw_downloads_must_not_be_committed": True,
        "large_binary_structures_must_not_be_committed": True,
        "data_downloaded": False,
        "external_network_called": False,
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
        "formal_training_allowed": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "real_covalent_split_metadata_enrichment_design_gate_passed": True,
        "metadata_enrichment_design_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_multi_source_dataset_ingestion_design_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12o_{key}_invalid:{manifest[key]!r}", blockers)
    row_types = [row["row_type"] for row in rows]
    _expect(
        row_types
        == [
            "step12n_precondition",
            "metadata_enrichment_concept",
            "multi_source_adapter_architecture",
            "required_source_adapter_design",
            "enrichment_field_derivation_plan",
            "enrichment_quality_policy",
            "enrichment_output_schema",
            "large_scale_data_transition_plan",
            "safety_and_next_step_decision",
        ],
        "step12o_design_table_rows_invalid",
        blockers,
    )
    summary = STEP12O_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "metadata enrichment design gate",
        "not actual enrichment",
        "not downloading",
        "not split",
        "not training",
        "thin materialization index to authoritative leakage-aware split metadata",
        "Different datasets can enter via source-specific adapters",
        "canonical raw covalent record schema",
        "cannot one-pot merge before normalization",
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "PDB/mmCIF direct",
        "local curated",
        "RDKit",
        "UniProt",
        "CD-HIT",
        "coordinate geometry calculation",
        "Authoritative metadata missing blocks final split and training",
        "Raw downloads and large binary structures cannot be committed",
        "ready_to_design_multi_source_ingestion=true",
        "ready_to_download_large_scale_data_now=false",
        "No data download/network/RDKit/UniProt/CD-HIT/geometry run",
        "recommended_next_step: real_covalent_multi_source_dataset_ingestion_design_gate",
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12o_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_multi_source_ingestion_concept_v0() -> dict[str, Any]:
    return {
        "multi_source_ingestion_concept_defined": True,
        "multi_source_ingestion_definition": (
            "standardize_source_specific_covalent_dataset_downloads_into_versioned_raw_records_before_enrichment"
        ),
        "multi_source_ingestion_not_equal_to_downloading": True,
        "multi_source_ingestion_not_equal_to_enrichment": True,
        "multi_source_ingestion_not_equal_to_training": True,
        "ingestion_design_precedes_actual_download": True,
        "ingestion_design_precedes_metadata_enrichment": True,
        "ingestion_design_defines_storage_registry_resume_checksum_and_provenance": True,
        "ingestion_design_required_because_ready_to_design_multi_source_ingestion": True,
        "large_scale_download_still_blocked_until_source_registry_license_audit": True,
    }


def build_source_registry_schema_v0() -> dict[str, Any]:
    return {
        "source_registry_schema_defined": True,
        "source_registry_entry_fields": SOURCE_REGISTRY_ENTRY_FIELDS,
        "source_registry_entry_field_count": len(SOURCE_REGISTRY_ENTRY_FIELDS),
        "planned_source_registry_entries": PLANNED_SOURCE_DISPLAY_NAMES,
        "source_registry_entry_count": len(PLANNED_SOURCE_DISPLAY_NAMES),
        "source_urls_are_placeholders": True,
        "source_url_currentness_not_verified": True,
        "license_usage_currentness_not_verified": True,
        "source_registry_license_audit_required": True,
        "source_registry_written": False,
    }


def build_raw_storage_layout_design_v0() -> dict[str, Any]:
    return {
        "raw_storage_layout_defined": True,
        "raw_storage_root_design": "data/raw/covalent_sources",
        "raw_source_subdirectories": ["downloads", "structures", "tables", "manifests", "logs", "checksums"],
        "raw_storage_directories_created": False,
        "raw_download_files_written": False,
        "raw_structure_files_written": False,
        "raw_tables_written": False,
        "raw_logs_written": False,
        "raw_checksums_written": False,
        "raw_data_must_not_be_committed": True,
        "large_binary_structures_must_not_be_committed": True,
        "design_outputs_only_in_git": True,
    }


def build_download_job_manifest_schema_v0() -> dict[str, Any]:
    fields = [
        "job_id",
        "source_name",
        "adapter_name",
        "source_url",
        "source_url_verified",
        "license_audit_status",
        "download_enabled",
        "local_output_dir",
        "expected_file_type",
        "expected_record_count",
        "started_at",
        "completed_at",
        "status",
        "bytes_downloaded",
        "file_count",
        "sha256_manifest_path",
        "resume_supported",
        "retry_policy",
        "checksum_verification_required",
        "provenance_record_required",
        "blocking_reasons",
    ]
    return {
        "download_job_manifest_schema_defined": True,
        "download_job_manifest_fields": fields,
        "download_job_manifest_field_count": len(fields),
        "download_job_manifest_required_before_download": True,
        "incremental_download_manifest_required": True,
        "checksum_manifest_required": True,
        "resume_policy_required": True,
        "retry_policy_required": True,
        "provenance_record_required": True,
        "download_jobs_written": False,
        "download_jobs_run": False,
    }


def build_source_adapter_interface_contract_v0() -> dict[str, Any]:
    return {
        "source_adapter_interface_contract_defined": True,
        "adapter_input_contract_defined": True,
        "adapter_input_contract": [
            "source_registry_entry",
            "raw_source_root",
            "download_manifest",
            "local_cache_root",
            "adapter_config",
            "manual_override_config",
        ],
        "adapter_output_contract_defined": True,
        "adapter_output_contract": [
            "canonical_raw_records.csv",
            "adapter_manifest.json",
            "adapter_quality_report.csv",
            "deferred_raw_records_report.csv",
            "duplicate_candidate_keys.csv",
        ],
        "canonical_raw_record_required_fields_defined": True,
        "canonical_raw_record_required_fields": CANONICAL_RAW_RECORD_FIELDS,
        "all_adapters_must_emit_canonical_raw_records": True,
        "adapter_quality_report_required": True,
        "deferred_raw_records_report_required": True,
        "duplicate_candidate_keys_required": True,
        "adapter_implementation_allowed_after_this_step": False,
        "adapter_execution_allowed_after_this_step": False,
    }


def build_source_specific_ingestion_design_details_v0() -> dict[str, Any]:
    details = {
        "CovPDB": {
            "adapter_name": "covpdb_adapter",
            "ingestion_mode": "source_table_plus_structures",
            "expected_raw_inputs": ["source table", "structure files", "covalent bond annotations if available"],
            "high_value_for_training": True,
            "expected_3d_complex_availability": "likely_high_but_unverified",
            "expected_atom_mapping_availability": "source_dependent_unverified",
            "known_risks": [
                "source format/version differences",
                "ligand reconstruction uncertainty",
                "duplicate overlap with PDB direct",
            ],
        },
        "CovBinderInPDB": {
            "adapter_name": "covbinderinpdb_adapter",
            "ingestion_mode": "pdb_id_annotation_table",
            "expected_raw_inputs": ["source table", "PDB IDs", "ligand/binder annotations"],
            "known_risks": ["duplicate PDB entries", "annotation ambiguity", "requires PDB/mmCIF fetch later"],
        },
        "CovalentInDB": {
            "adapter_name": "covalentindb_adapter",
            "ingestion_mode": "target_inhibitor_metadata_plus_optional_structures",
            "expected_raw_inputs": ["inhibitor-target metadata", "available cocrystal structures"],
            "known_risks": [
                "many entries may lack 3D complex",
                "may lack exact covalent atom mapping",
                "more useful for warhead/reaction annotation than direct 3D training",
            ],
        },
        "PDB/mmCIF direct": {
            "adapter_name": "pdb_direct_adapter",
            "ingestion_mode": "structure_harvesting_from_pdb_ids",
            "expected_raw_inputs": ["PDB IDs", "mmCIF/PDB files", "LINK/CONECT records", "ligand CCD IDs"],
            "known_risks": [
                "biological assembly ambiguity",
                "LINK parsing ambiguity",
                "modified residue handling",
                "ligand CCD atom naming",
            ],
        },
        "local curated": {
            "adapter_name": "local_curated_adapter",
            "ingestion_mode": "manual_local_examples",
            "expected_raw_inputs": ["current BTK/KRAS examples", "future NLRP3 curated examples"],
            "known_risks": ["manual curation bias", "must be versioned and audited"],
        },
    }
    return {
        "source_specific_ingestion_design_details_defined": True,
        "covpdb_ingestion_design_defined": True,
        "covbinderinpdb_ingestion_design_defined": True,
        "covalentindb_ingestion_design_defined": True,
        "pdb_direct_ingestion_design_defined": True,
        "local_curated_ingestion_design_defined": True,
        "source_specific_ingestion_details": details,
    }


def build_duplicate_provenance_priority_policy_v0() -> dict[str, Any]:
    return {
        "duplicate_provenance_priority_policy_defined": True,
        "duplicate_detection_keys": [
            "pdb_id",
            "chain_id",
            "ligand_id",
            "residue_id",
            "residue_type",
            "covalent_bond_annotation_raw",
            "ligand_inchikey_after_enrichment",
            "parent_complex_id_after_enrichment",
        ],
        "duplicate_detection_across_sources_required": True,
        "source_priority_policy_defined": True,
        "source_priority_order_design": ["local_curated", "CovPDB", "CovBinderInPDB", "PDB/mmCIF direct", "CovalentInDB"],
        "source_priority_is_design_only": True,
        "duplicate_resolution_requires_audit": True,
        "duplicate_records_not_dropped_without_report": True,
        "provenance_chain_required": True,
        "source_record_id_required": True,
        "source_version_required": True,
        "source_license_or_usage_note_required": True,
    }


def build_small_pilot_ingestion_plan_v0() -> dict[str, Any]:
    return {
        "small_pilot_ingestion_plan_defined": True,
        "pilot_before_large_scale_download_required": True,
        "recommended_pilot_scope": "one_to_three_records_per_source_after_license_audit",
        "pilot_max_records_per_source": 3,
        "pilot_sources": ["local_curated", "PDB/mmCIF direct", "CovPDB", "CovBinderInPDB", "CovalentInDB"],
        "pilot_requires_current_source_registry": True,
        "pilot_requires_license_audit": True,
        "pilot_requires_download_manifest": True,
        "pilot_requires_checksum_manifest": True,
        "pilot_requires_raw_data_not_in_git": True,
        "pilot_download_allowed_in_this_step": False,
        "large_scale_download_allowed_in_this_step": False,
    }


def build_git_data_policy_v0() -> dict[str, Any]:
    return {
        "git_data_policy_defined": True,
        "allowed_git_artifact_suffixes_for_design": [".py", ".csv", ".json", ".md"],
        "forbidden_git_artifact_suffixes": sorted(FORBIDDEN_ARTIFACT_SUFFIXES),
        "raw_data_not_in_git_policy_defined": True,
        "raw_downloads_must_not_be_committed": True,
        "raw_structures_must_not_be_committed": True,
        "generated_training_tensors_must_not_be_committed": True,
        "checkpoint_files_must_not_be_committed": True,
        "large_binary_structures_must_not_be_committed": True,
        "git_allowed_design_outputs_only": True,
        "future_download_outputs_go_under_data_raw_or_external_storage": True,
        "future_training_tensor_outputs_go_under_data_derived_but_not_committed_if_binary": True,
    }


def build_real_covalent_multi_source_dataset_ingestion_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12o_validated = validate_step12o_split_metadata_enrichment_design_gate_v0()
    except Exception as exc:
        step12o_validated = False
        blockers.append(f"step12o_validation_failed:{type(exc).__name__}:{exc}")
    step12o_manifest = _load_json(STEP12O_MANIFEST_JSON)
    concept = build_multi_source_ingestion_concept_v0()
    registry = build_source_registry_schema_v0()
    storage = build_raw_storage_layout_design_v0()
    download_schema = build_download_job_manifest_schema_v0()
    adapter_contract = build_source_adapter_interface_contract_v0()
    source_details = build_source_specific_ingestion_design_details_v0()
    duplicate_policy = build_duplicate_provenance_priority_policy_v0()
    pilot = build_small_pilot_ingestion_plan_v0()
    git_policy = build_git_data_policy_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12o_validated
        and concept["multi_source_ingestion_concept_defined"]
        and registry["source_registry_schema_defined"]
        and storage["raw_storage_layout_defined"]
        and download_schema["download_job_manifest_schema_defined"]
        and adapter_contract["source_adapter_interface_contract_defined"]
        and source_details["source_specific_ingestion_design_details_defined"]
        and duplicate_policy["duplicate_provenance_priority_policy_defined"]
        and pilot["small_pilot_ingestion_plan_defined"]
        and git_policy["git_data_policy_defined"]
        and not registry["source_registry_written"]
        and not storage["raw_storage_directories_created"]
        and not download_schema["download_jobs_written"]
        and not download_schema["download_jobs_run"]
        and not adapter_contract["adapter_implementation_allowed_after_this_step"]
        and not adapter_contract["adapter_execution_allowed_after_this_step"]
        and not pilot["pilot_download_allowed_in_this_step"]
        and not pilot["large_scale_download_allowed_in_this_step"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_multi_source_dataset_ingestion_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12o_split_metadata_enrichment_design_gate_validated": step12o_validated,
        "step12b_mask_level_aware_validator_validated": step12o_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "current_sample_count": step12o_manifest["current_sample_count"],
        "required_split_metadata_field_count": step12o_manifest["required_split_metadata_field_count"],
        "present_required_metadata_field_count": step12o_manifest["present_required_metadata_field_count"],
        "missing_required_metadata_field_count": step12o_manifest["missing_required_metadata_field_count"],
        "metadata_completeness_ratio_text": step12o_manifest["metadata_completeness_ratio_text"],
        "metadata_gap_level": step12o_manifest["metadata_gap_level"],
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        **concept,
        **registry,
        **storage,
        **download_schema,
        **adapter_contract,
        **source_details,
        **duplicate_policy,
        **pilot,
        **git_policy,
        "data_downloaded": False,
        "external_network_called": False,
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
        "real_covalent_multi_source_dataset_ingestion_design_gate_passed": passed,
        "multi_source_dataset_ingestion_design_contract_defined": passed,
        "ready_to_create_source_registry_license_audit": passed,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "design_table_rows": _build_design_table_rows(manifest),
        "report_sections": _build_report_sections(manifest),
    }


def _status(value: bool) -> str:
    return "passed" if value else "blocked"


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _summary_row(
    row_type: str,
    passed: bool,
    policy_name: str,
    evidence: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "row_type": row_type,
        "status": _status(bool(passed)),
        "policy_name": policy_name,
        "evidence": _json_text(evidence),
        "source_count": manifest["source_registry_entry_count"],
        "ready_to_download_large_scale_data_now": manifest["ready_to_download_large_scale_data_now"],
        "recommended_next_step": manifest["recommended_next_step"],
        "blocking_reasons": [] if passed else manifest["blocking_reasons"],
    }


def _build_design_table_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _summary_row(
            "step12o_precondition",
            manifest["step12o_split_metadata_enrichment_design_gate_validated"],
            "Step 12O metadata enrichment design precondition",
            {"metadata_completeness_ratio_text": manifest["metadata_completeness_ratio_text"]},
            manifest,
        ),
        _summary_row(
            "multi_source_ingestion_concept",
            manifest["multi_source_ingestion_concept_defined"],
            "multi-source ingestion concept",
            {"multi_source_ingestion_definition": manifest["multi_source_ingestion_definition"]},
            manifest,
        ),
        _summary_row(
            "source_registry_schema",
            manifest["source_registry_schema_defined"],
            "source registry schema",
            {"planned_source_registry_entries": manifest["planned_source_registry_entries"]},
            manifest,
        ),
        _summary_row(
            "raw_storage_layout_design",
            manifest["raw_storage_layout_defined"],
            "raw storage layout design",
            {"raw_storage_root_design": manifest["raw_storage_root_design"]},
            manifest,
        ),
        _summary_row(
            "download_job_manifest_schema",
            manifest["download_job_manifest_schema_defined"],
            "download job manifest schema",
            {"download_job_manifest_required_before_download": manifest["download_job_manifest_required_before_download"]},
            manifest,
        ),
        _summary_row(
            "source_adapter_interface_contract",
            manifest["source_adapter_interface_contract_defined"],
            "source adapter interface contract",
            {"canonical_raw_record_required_fields": manifest["canonical_raw_record_required_fields"]},
            manifest,
        ),
        _summary_row(
            "source_specific_ingestion_design_details",
            manifest["source_specific_ingestion_design_details_defined"],
            "source-specific ingestion design details",
            {"source_specific_ingestion_details": manifest["source_specific_ingestion_details"]},
            manifest,
        ),
        _summary_row(
            "duplicate_provenance_priority_policy",
            manifest["duplicate_provenance_priority_policy_defined"],
            "duplicate provenance priority policy",
            {"source_priority_order_design": manifest["source_priority_order_design"]},
            manifest,
        ),
        _summary_row(
            "small_pilot_ingestion_plan",
            manifest["small_pilot_ingestion_plan_defined"],
            "small pilot ingestion plan",
            {"recommended_pilot_scope": manifest["recommended_pilot_scope"]},
            manifest,
        ),
        _summary_row(
            "git_data_policy",
            manifest["git_data_policy_defined"],
            "git data policy",
            {"forbidden_git_artifact_suffixes": manifest["forbidden_git_artifact_suffixes"]},
            manifest,
        ),
        _summary_row(
            "safety_and_next_step_decision",
            manifest["real_covalent_multi_source_dataset_ingestion_design_gate_passed"],
            "safety and next-step decision",
            {"recommended_next_step": manifest["recommended_next_step"]},
            manifest,
        ),
    ]


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12o_precondition": {
            "step12o_split_metadata_enrichment_design_gate_validated": manifest[
                "step12o_split_metadata_enrichment_design_gate_validated"
            ],
            "metadata_gap_level": manifest["metadata_gap_level"],
        },
        "multi_source_ingestion_concept": {
            "multi_source_ingestion_definition": manifest["multi_source_ingestion_definition"],
            "large_scale_download_still_blocked_until_source_registry_license_audit": manifest[
                "large_scale_download_still_blocked_until_source_registry_license_audit"
            ],
        },
        "source_registry_schema": {
            "source_registry_entry_count": manifest["source_registry_entry_count"],
            "source_urls_are_placeholders": manifest["source_urls_are_placeholders"],
        },
        "raw_storage_layout_design": {
            "raw_storage_root_design": manifest["raw_storage_root_design"],
            "raw_storage_directories_created": manifest["raw_storage_directories_created"],
        },
        "download_job_manifest_schema": {
            "download_job_manifest_required_before_download": manifest["download_job_manifest_required_before_download"],
            "download_jobs_run": manifest["download_jobs_run"],
        },
        "source_adapter_interface_contract": {
            "all_adapters_must_emit_canonical_raw_records": manifest["all_adapters_must_emit_canonical_raw_records"],
            "adapter_execution_allowed_after_this_step": manifest["adapter_execution_allowed_after_this_step"],
        },
        "source_specific_ingestion_design_details": {
            "source_specific_ingestion_design_details_defined": manifest["source_specific_ingestion_design_details_defined"],
            "planned_source_registry_entries": manifest["planned_source_registry_entries"],
        },
        "duplicate_provenance_priority_policy": {
            "duplicate_detection_across_sources_required": manifest["duplicate_detection_across_sources_required"],
            "source_priority_order_design": manifest["source_priority_order_design"],
        },
        "small_pilot_ingestion_plan": {
            "pilot_max_records_per_source": manifest["pilot_max_records_per_source"],
            "pilot_download_allowed_in_this_step": manifest["pilot_download_allowed_in_this_step"],
        },
        "git_data_policy": {
            "raw_downloads_must_not_be_committed": manifest["raw_downloads_must_not_be_committed"],
            "raw_structures_must_not_be_committed": manifest["raw_structures_must_not_be_committed"],
        },
        "safety_and_next_step_decision": {
            "data_downloaded": manifest["data_downloaded"],
            "external_network_called": manifest["external_network_called"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
