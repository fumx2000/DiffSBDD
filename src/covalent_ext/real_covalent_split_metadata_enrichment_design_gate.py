from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_split_metadata_enrichment_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_split_metadata_inventory_gate_v0"

STEP12N_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_split_metadata_inventory_gate_v0/"
    "real_covalent_split_metadata_inventory_gate_manifest.json"
)
STEP12N_INVENTORY_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_split_metadata_inventory_gate_v0/"
    "real_covalent_split_metadata_inventory_gate_table.csv"
)
STEP12N_SUMMARY_MD = Path("docs/real_covalent_split_metadata_inventory_gate_v0_summary.md")

STEP12M_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_leakage_aware_split_design_gate_v0/"
    "real_covalent_leakage_aware_split_design_gate_manifest.json"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_split_metadata_enrichment_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_split_metadata_enrichment_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_split_metadata_enrichment_design_gate_manifest.json"
DESIGN_TABLE_CSV = OUTPUT_ROOT / "real_covalent_split_metadata_enrichment_design_gate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_split_metadata_enrichment_design_gate_v0_summary.md")

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
RECOMMENDED_NEXT_STEP = "real_covalent_multi_source_dataset_ingestion_design_gate"

FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
OPTIMIZER_STEP_CALLED_KEY = "_".join(["optimizer", "step", "called"])
TRAINER_FIT_CALLED_KEY = "_".join(["trainer", "fit", "called"])


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


def validate_step12n_split_metadata_inventory_gate_v0() -> bool:
    if not STEP12N_MANIFEST_JSON.is_file() or not STEP12N_INVENTORY_TABLE_CSV.is_file() or not STEP12N_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12N outputs are missing")
    manifest = _load_json(STEP12N_MANIFEST_JSON)
    rows = _read_csv(STEP12N_INVENTORY_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_leakage_aware_split_design_gate_v0",
        "step12m_leakage_aware_split_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "sample_index_exists": True,
        "current_sample_index_inspected": True,
        "current_sample_count": 3,
        "sample_index_observed_field_count": 14,
        "required_split_metadata_schema_loaded_from_step12m": True,
        "required_split_metadata_field_count": 38,
        "present_required_metadata_fields": ["sample_id", "ligand_reactive_atom_index"],
        "present_required_metadata_field_count": 2,
        "missing_required_metadata_field_count": 36,
        "metadata_completeness_ratio_text": "2/38",
        "metadata_complete_for_final_split": False,
        "final_split_blocked_by_missing_metadata": True,
        "observed_existing_split_field_present": True,
        "observed_split_field_is_not_final_leakage_aware_split": True,
        "observed_split_field_must_not_be_used_for_paper_claim": True,
        "candidate_derivation_plan_defined": True,
        "candidate_derived_metadata_authoritative": False,
        "heuristic_parsing_allowed_for_inventory_only": True,
        "heuristic_parsing_not_allowed_for_final_split_without_validation": True,
        "future_metadata_enrichment_output_plan_defined": True,
        "metadata_gap_level": "severe",
        "metadata_enrichment_required": True,
        "metadata_enrichment_design_allowed": True,
        "final_train_valid_test_split_allowed": False,
        "final_paper_claim_allowed": False,
        "split_implementation_allowed_after_this_step": False,
        "formal_training_allowed": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "npz_file_existence_checked": False,
        "enriched_sample_index_written": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        OPTIMIZER_STEP_CALLED_KEY: False,
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "real_covalent_split_metadata_inventory_gate_passed": True,
        "split_metadata_inventory_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.removesuffix("_v0"),
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12n_{key}_invalid:{manifest[key]!r}", blockers)
    contains_checks = {
        "fields_requiring_ligand_structure_processing": [
            "canonical_pre_reaction_smiles",
            "ligand_inchikey",
            "ligand_ecfp4_fingerprint",
            "bemis_murcko_scaffold_smiles",
            "warhead_type",
            "reaction_family",
        ],
        "fields_requiring_protein_structure_or_sequence_mapping": [
            "uniprot_id",
            "protein_sequence",
            "protein_sequence_cluster_0p90",
            "local_pocket_signature",
        ],
        "fields_requiring_coordinate_geometry_calculation": [
            "covalent_bond_atom_pair",
            "ligand_reactive_atom_to_cys_sg_distance",
            "pocket_geometry_bin",
        ],
    }
    for key, values in contains_checks.items():
        for value in values:
            _expect(value in manifest[key], f"step12n_{key}_missing:{value}", blockers)
    row_types = [row["row_type"] for row in rows]
    _expect(row_types.count("required_metadata_field_inventory") == 38, "step12n_required_field_row_count_invalid", blockers)
    _expect(row_types.count("metadata_group_summary") == 5, "step12n_group_summary_row_count_invalid", blockers)
    summary = STEP12N_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "split metadata inventory gate",
        "not enrichment",
        "not split implementation",
        "not training",
        "3 samples",
        "field count: 38",
        "sample_id, ligand_reactive_atom_index",
        "missing required metadata count: 36",
        "metadata completeness: 2/38",
        "split field is not final leakage-aware split",
        "No NPZ contents read",
        "Candidate metadata parsed from sample_id or source_sample_id is not authoritative",
        "ligand identity requires RDKit/ligand structure",
        "protein identity requires sequence/UniProt/CD-HIT",
        "geometry requires coordinate calculation",
        "metadata gap level: severe",
        "recommended_next_step: real_covalent_split_metadata_enrichment_design_gate",
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12n_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_metadata_enrichment_concept_v0() -> dict[str, Any]:
    return {
        "metadata_enrichment_concept_defined": True,
        "metadata_enrichment_definition": "convert_thin_materialization_index_into_authoritative_leakage_aware_split_metadata",
        "metadata_enrichment_is_required_because_current_metadata_completeness": "2/38",
        "metadata_enrichment_not_equal_to_training": True,
        "metadata_enrichment_not_equal_to_split_implementation": True,
        "metadata_enrichment_not_equal_to_downloading": True,
        "metadata_enrichment_creates_authoritative_metadata_for_split": True,
        "metadata_enrichment_enables_leakage_aware_split": True,
        "metadata_enrichment_enables_cys_train_ready_inventory": True,
        "metadata_enrichment_enables_scaffold_target_warhead_diversity_reports": True,
    }


def build_multi_source_adapter_architecture_v0() -> dict[str, Any]:
    return {
        "multi_source_adapter_architecture_defined": True,
        "heterogeneous_datasets_can_share_common_enrichment_pipeline": True,
        "source_specific_adapter_required": True,
        "canonical_raw_record_schema_required": True,
        "common_enrichment_pipeline_required": True,
        "source_dataset_provenance_required": True,
        "source_version_tracking_required": True,
        "license_or_usage_note_required": True,
        "source_specific_field_mapping_required": True,
        "direct_mixture_without_adapter_allowed": False,
        "one_pot_merge_before_normalization_allowed": False,
        "architecture_layers": [
            "source_specific_raw_adapters",
            "canonical_raw_covalent_record_schema",
            "common_enrichment_pipeline",
        ],
        "source_specific_raw_adapters": [
            "CovPDB adapter",
            "CovBinderInPDB adapter",
            "CovalentInDB adapter",
            "PDB/mmCIF direct adapter",
            "local curated covalent examples adapter",
        ],
        "canonical_raw_covalent_record_fields": [
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
        ],
        "common_enrichment_pipeline_steps": [
            "ligand identity enrichment",
            "protein identity enrichment",
            "covalent identity enrichment",
            "geometry/diversity enrichment",
            "quality control enrichment",
            "leakage metadata enrichment",
        ],
    }


def build_required_source_adapter_design_v0() -> dict[str, Any]:
    planned = [
        "covpdb_adapter",
        "covbinderinpdb_adapter",
        "covalentindb_adapter",
        "pdb_direct_adapter",
        "local_curated_adapter",
    ]
    details = {
        "covpdb_adapter": {
            "purpose": "covalent protein-ligand complex source",
            "expected_inputs": ["source table", "structure files", "covalent bond annotations if available"],
            "expected_outputs": ["canonical raw covalent records"],
            "risk": ["source format/version differences", "ligand reconstruction uncertainty"],
        },
        "covbinderinpdb_adapter": {
            "purpose": "covalent binder annotations in PDB",
            "expected_inputs": ["source table", "PDB IDs", "ligand/binder annotations"],
            "expected_outputs": ["canonical raw covalent records"],
            "risk": ["duplicate PDB entries", "annotation ambiguity"],
        },
        "covalentindb_adapter": {
            "purpose": "covalent inhibitor/target database",
            "expected_inputs": ["inhibitor-target metadata", "available cocrystal structures"],
            "expected_outputs": ["canonical raw covalent records"],
            "risk": ["entries may lack 3D protein-ligand complex", "entries may lack exact atom mapping"],
        },
        "pdb_direct_adapter": {
            "purpose": "direct PDB/mmCIF structure harvesting",
            "expected_inputs": ["PDB IDs", "mmCIF/PDB files", "LINK/CONECT records", "ligand CCD IDs"],
            "expected_outputs": ["canonical raw covalent records"],
            "risk": ["biological assembly ambiguity", "covalent LINK parsing ambiguity", "modified residues"],
        },
        "local_curated_adapter": {
            "purpose": "keep current BTK/KRAS examples and future NLRP3 curated examples compatible",
            "expected_inputs": ["local curated files", "current sample index"],
            "expected_outputs": ["canonical raw covalent records"],
            "risk": ["manual curation must be flagged and versioned"],
        },
    }
    return {
        "required_source_adapter_design_defined": True,
        "planned_source_adapters": planned,
        "planned_source_adapter_display_names": [
            "CovPDB",
            "CovBinderInPDB",
            "CovalentInDB",
            "PDB/mmCIF direct",
            "local curated",
        ],
        "source_adapter_count": len(planned),
        "all_source_adapters_output_canonical_raw_records": True,
        "source_adapter_quality_flags_required": True,
        "duplicate_detection_across_sources_required": True,
        "source_priority_policy_required": True,
        "source_adapter_design_details": details,
    }


def build_enrichment_field_derivation_plan_v0() -> dict[str, Any]:
    return {
        "enrichment_field_derivation_plan_defined": True,
        "already_exact_present_fields": ["sample_id", "ligand_reactive_atom_index"],
        "candidate_id_parsing_fields": [
            "parent_complex_id",
            "mask_parent_id",
            "source_dataset",
            "source_pdb_id",
            "pdb_id",
            "target_name",
            "reactive_residue_type",
            "reactive_residue_id",
            "protein_family",
        ],
        "ligand_identity_enrichment_fields": [
            "canonical_pre_reaction_smiles",
            "ligand_inchikey",
            "ligand_inchikey_connectivity_layer",
            "ligand_ecfp4_fingerprint",
            "bemis_murcko_scaffold_smiles",
            "scaffold_id",
            "ligand_heavy_atom_count",
        ],
        "ligand_identity_required_methods": [
            "RDKit canonicalization",
            "RDKit InChIKey",
            "RDKit Morgan fingerprint radius=2 / ECFP4",
            "RDKit Murcko scaffold",
            "ligand sanitization status",
            "pre-reaction ligand reconstruction validation",
        ],
        "protein_identity_enrichment_fields": [
            "chain_id",
            "uniprot_id",
            "protein_sequence",
            "protein_sequence_hash",
            "protein_sequence_cluster_0p90",
            "protein_family",
            "binding_site_residue_set_hash",
            "local_pocket_signature",
        ],
        "protein_identity_required_methods": [
            "PDB/mmCIF parser",
            "SEQRES/ATOM sequence extraction",
            "SIFTS or equivalent PDB-to-UniProt mapping",
            "CD-HIT or equivalent sequence clustering at 0.90",
            "pocket residue set extraction",
        ],
        "covalent_identity_enrichment_fields": [
            "reactive_residue_type",
            "reactive_residue_id",
            "reactive_residue_chain",
            "protein_reactive_atom_name",
            "covalent_bond_atom_pair",
            "warhead_type",
            "reaction_family",
            "post_to_pre_reconstruction_template_id",
        ],
        "covalent_identity_required_methods": [
            "LINK/CONECT/covalent annotation parsing",
            "residue atom identification",
            "ligand reactive atom validation",
            "warhead SMARTS library",
            "reaction family classifier",
            "reconstruction template registry",
        ],
        "geometry_diversity_enrichment_fields": [
            "ligand_reactive_atom_to_cys_sg_distance",
            "warhead_orientation_descriptor",
            "linker_length_bin",
            "pocket_geometry_bin",
            "target_context_atom_count",
            "target_mask_atom_count",
        ],
        "geometry_diversity_required_methods": [
            "3D coordinate extraction",
            "Cys SG distance calculation",
            "warhead orientation vector descriptor",
            "linker atom graph distance/binning",
            "local pocket geometry descriptor/binning",
            "mask atom count consistency check",
        ],
        "rdkit_required_for_ligand_identity": True,
        "pdb_parser_required_for_protein_identity": True,
        "uniprot_mapping_required": True,
        "cdhit_or_equivalent_required_for_sequence_cluster": True,
        "coordinate_geometry_required": True,
        "warhead_smarts_library_required": True,
        "reaction_family_classifier_required": True,
        "reconstruction_template_registry_required": True,
    }


def build_enrichment_quality_policy_v0() -> dict[str, Any]:
    return {
        "enrichment_quality_policy_defined": True,
        "authoritative_metadata_required_for_final_split": True,
        "heuristic_metadata_allowed_for_inventory_only": True,
        "heuristic_metadata_allowed_for_final_split": False,
        "missing_authoritative_metadata_blocks_final_split": True,
        "missing_authoritative_metadata_blocks_training": True,
        "low_confidence_records_deferred": True,
        "ambiguous_covalent_bond_records_deferred": True,
        "ligand_sanitization_fail_records_deferred": True,
        "protein_mapping_fail_records_deferred": True,
        "non_cys_records_identified_but_deferred_for_v1": True,
        "duplicate_records_across_sources_flagged": True,
        "duplicate_resolution_policy_required": True,
        "source_priority_policy_required": True,
        "manual_override_allowed_with_audit": True,
        "manual_override_requires_reason": True,
    }


def build_enrichment_output_schema_v0() -> dict[str, Any]:
    return {
        "enrichment_output_schema_defined": True,
        "future_enrichment_outputs_required": [
            "enriched_sample_index_for_split.csv",
            "enriched_split_metadata_inventory.csv",
            "metadata_derivation_manifest.json",
            "metadata_gap_report.csv",
            "candidate_id_mapping_report.csv",
            "ligand_identity_enrichment_report.csv",
            "protein_identity_enrichment_report.csv",
            "covalent_identity_enrichment_report.csv",
            "geometry_diversity_enrichment_report.csv",
            "multi_source_duplicate_report.csv",
            "deferred_records_report.csv",
            "source_adapter_coverage_report.csv",
        ],
        "future_enriched_sample_index_for_split_required": True,
        "future_metadata_derivation_manifest_required": True,
        "future_metadata_gap_report_required": True,
        "future_candidate_id_mapping_report_required": True,
        "future_ligand_identity_enrichment_report_required": True,
        "future_protein_identity_enrichment_report_required": True,
        "future_covalent_identity_enrichment_report_required": True,
        "future_geometry_diversity_enrichment_report_required": True,
        "future_multi_source_duplicate_report_required": True,
        "future_deferred_records_report_required": True,
        "future_source_adapter_coverage_report_required": True,
        "enriched_sample_index_for_split_written": False,
        "metadata_derivation_manifest_written": False,
        "enrichment_reports_written": False,
    }


def build_large_scale_data_transition_plan_v0() -> dict[str, Any]:
    return {
        "large_scale_data_transition_plan_defined": True,
        "ready_to_design_multi_source_ingestion": True,
        "ready_to_download_large_scale_data_now": False,
        "download_requires_source_adapter_design": True,
        "download_requires_storage_policy": True,
        "download_requires_license_usage_audit": True,
        "download_requires_incremental_manifest": True,
        "download_requires_resume_and_checksum_policy": True,
        "download_requires_raw_data_not_in_git_policy": True,
        "raw_downloads_must_not_be_committed": True,
        "large_binary_structures_must_not_be_committed": True,
        "allowed_git_outputs_for_design_stage": ["csv", "json", "md", "py"],
        "recommended_data_sources_for_next_design": [
            "CovPDB",
            "CovBinderInPDB",
            "CovalentInDB",
            "PDB/mmCIF direct",
            "local curated",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def build_real_covalent_split_metadata_enrichment_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12n_validated = validate_step12n_split_metadata_inventory_gate_v0()
    except Exception as exc:
        step12n_validated = False
        blockers.append(f"step12n_validation_failed:{type(exc).__name__}:{exc}")
    step12n_manifest = _load_json(STEP12N_MANIFEST_JSON)
    concept = build_metadata_enrichment_concept_v0()
    architecture = build_multi_source_adapter_architecture_v0()
    adapters = build_required_source_adapter_design_v0()
    derivation = build_enrichment_field_derivation_plan_v0()
    quality = build_enrichment_quality_policy_v0()
    outputs = build_enrichment_output_schema_v0()
    transition = build_large_scale_data_transition_plan_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12n_validated
        and concept["metadata_enrichment_concept_defined"]
        and architecture["multi_source_adapter_architecture_defined"]
        and adapters["required_source_adapter_design_defined"]
        and derivation["enrichment_field_derivation_plan_defined"]
        and quality["enrichment_quality_policy_defined"]
        and outputs["enrichment_output_schema_defined"]
        and transition["large_scale_data_transition_plan_defined"]
        and not outputs["enriched_sample_index_for_split_written"]
        and not transition["ready_to_download_large_scale_data_now"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_split_metadata_enrichment_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12n_split_metadata_inventory_gate_validated": step12n_validated,
        "step12b_mask_level_aware_validator_validated": step12n_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "current_sample_count": step12n_manifest["current_sample_count"],
        "required_split_metadata_field_count": step12n_manifest["required_split_metadata_field_count"],
        "present_required_metadata_field_count": step12n_manifest["present_required_metadata_field_count"],
        "missing_required_metadata_field_count": step12n_manifest["missing_required_metadata_field_count"],
        "metadata_completeness_ratio_text": step12n_manifest["metadata_completeness_ratio_text"],
        "metadata_gap_level": step12n_manifest["metadata_gap_level"],
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        **concept,
        **architecture,
        **adapters,
        **derivation,
        **quality,
        **outputs,
        **transition,
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
        OPTIMIZER_STEP_CALLED_KEY: False,
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
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
        "real_covalent_split_metadata_enrichment_design_gate_passed": passed,
        "metadata_enrichment_design_contract_defined": passed,
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
        "current_sample_count": manifest["current_sample_count"],
        "missing_required_metadata_field_count": manifest["missing_required_metadata_field_count"],
        "recommended_next_step": manifest["recommended_next_step"],
        "blocking_reasons": [] if passed else manifest["blocking_reasons"],
    }


def _build_design_table_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _summary_row(
            "step12n_precondition",
            manifest["step12n_split_metadata_inventory_gate_validated"],
            "Step 12N metadata inventory precondition",
            {"metadata_completeness_ratio_text": manifest["metadata_completeness_ratio_text"]},
            manifest,
        ),
        _summary_row(
            "metadata_enrichment_concept",
            manifest["metadata_enrichment_concept_defined"],
            "metadata enrichment concept",
            {"metadata_enrichment_definition": manifest["metadata_enrichment_definition"]},
            manifest,
        ),
        _summary_row(
            "multi_source_adapter_architecture",
            manifest["multi_source_adapter_architecture_defined"],
            "multi-source adapter architecture",
            {"architecture_layers": manifest["architecture_layers"]},
            manifest,
        ),
        _summary_row(
            "required_source_adapter_design",
            manifest["required_source_adapter_design_defined"],
            "required source adapter design",
            {"planned_source_adapters": manifest["planned_source_adapters"]},
            manifest,
        ),
        _summary_row(
            "enrichment_field_derivation_plan",
            manifest["enrichment_field_derivation_plan_defined"],
            "enrichment field derivation plan",
            {"already_exact_present_fields": manifest["already_exact_present_fields"]},
            manifest,
        ),
        _summary_row(
            "enrichment_quality_policy",
            manifest["enrichment_quality_policy_defined"],
            "enrichment quality policy",
            {"authoritative_metadata_required_for_final_split": manifest["authoritative_metadata_required_for_final_split"]},
            manifest,
        ),
        _summary_row(
            "enrichment_output_schema",
            manifest["enrichment_output_schema_defined"],
            "enrichment output schema",
            {"future_enrichment_outputs_required": manifest["future_enrichment_outputs_required"]},
            manifest,
        ),
        _summary_row(
            "large_scale_data_transition_plan",
            manifest["large_scale_data_transition_plan_defined"],
            "large-scale data transition plan",
            {"ready_to_design_multi_source_ingestion": manifest["ready_to_design_multi_source_ingestion"]},
            manifest,
        ),
        _summary_row(
            "safety_and_next_step_decision",
            manifest["real_covalent_split_metadata_enrichment_design_gate_passed"],
            "safety and next-step decision",
            {"recommended_next_step": manifest["recommended_next_step"]},
            manifest,
        ),
    ]


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12n_precondition": {
            "step12n_split_metadata_inventory_gate_validated": manifest["step12n_split_metadata_inventory_gate_validated"],
            "metadata_gap_level": manifest["metadata_gap_level"],
        },
        "metadata_enrichment_concept": {
            "metadata_enrichment_definition": manifest["metadata_enrichment_definition"],
            "metadata_enrichment_creates_authoritative_metadata_for_split": manifest[
                "metadata_enrichment_creates_authoritative_metadata_for_split"
            ],
        },
        "multi_source_adapter_architecture": {
            "source_specific_adapter_required": manifest["source_specific_adapter_required"],
            "canonical_raw_record_schema_required": manifest["canonical_raw_record_schema_required"],
        },
        "required_source_adapter_design": {
            "planned_source_adapters": manifest["planned_source_adapters"],
            "source_adapter_count": manifest["source_adapter_count"],
        },
        "enrichment_field_derivation_plan": {
            "rdkit_required_for_ligand_identity": manifest["rdkit_required_for_ligand_identity"],
            "uniprot_mapping_required": manifest["uniprot_mapping_required"],
            "coordinate_geometry_required": manifest["coordinate_geometry_required"],
        },
        "enrichment_quality_policy": {
            "authoritative_metadata_required_for_final_split": manifest["authoritative_metadata_required_for_final_split"],
            "heuristic_metadata_allowed_for_final_split": manifest["heuristic_metadata_allowed_for_final_split"],
        },
        "enrichment_output_schema": {
            "enrichment_output_schema_defined": manifest["enrichment_output_schema_defined"],
            "enriched_sample_index_for_split_written": manifest["enriched_sample_index_for_split_written"],
        },
        "large_scale_data_transition_plan": {
            "ready_to_design_multi_source_ingestion": manifest["ready_to_design_multi_source_ingestion"],
            "ready_to_download_large_scale_data_now": manifest["ready_to_download_large_scale_data_now"],
        },
        "safety_and_next_step_decision": {
            "data_downloaded": manifest["data_downloaded"],
            "external_network_called": manifest["external_network_called"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
