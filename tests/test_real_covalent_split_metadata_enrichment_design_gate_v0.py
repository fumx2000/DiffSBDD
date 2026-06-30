from __future__ import annotations

import ast
import csv
import json
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from covalent_ext import real_covalent_split_metadata_enrichment_design_gate as design  # noqa: E402
import check_real_covalent_split_metadata_enrichment_design_gate_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        design.REPORT_CSV.is_file()
        and design.MANIFEST_JSON.is_file()
        and design.DESIGN_TABLE_CSV.is_file()
        and design.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(design.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = "planned_source_adapter_display_names" not in manifest
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(design.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_step12n_precondition_and_current_gap_state():
    assert design.validate_step12n_split_metadata_inventory_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_split_metadata_enrichment_design_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_split_metadata_inventory_gate_v0"
    assert manifest["step12n_split_metadata_inventory_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["current_sample_count"] == 3
    assert manifest["required_split_metadata_field_count"] == 38
    assert manifest["present_required_metadata_field_count"] == 2
    assert manifest["missing_required_metadata_field_count"] == 36
    assert manifest["metadata_completeness_ratio_text"] == "2/38"
    assert manifest["metadata_gap_level"] == "severe"


def test_metadata_enrichment_concept():
    manifest = _manifest()
    assert manifest["metadata_enrichment_concept_defined"] is True
    assert (
        manifest["metadata_enrichment_definition"]
        == "convert_thin_materialization_index_into_authoritative_leakage_aware_split_metadata"
    )
    assert manifest["metadata_enrichment_is_required_because_current_metadata_completeness"] == "2/38"
    assert manifest["metadata_enrichment_not_equal_to_training"] is True
    assert manifest["metadata_enrichment_not_equal_to_split_implementation"] is True
    assert manifest["metadata_enrichment_not_equal_to_downloading"] is True
    assert manifest["metadata_enrichment_creates_authoritative_metadata_for_split"] is True
    assert manifest["metadata_enrichment_enables_leakage_aware_split"] is True
    assert manifest["metadata_enrichment_enables_cys_train_ready_inventory"] is True
    assert manifest["metadata_enrichment_enables_scaffold_target_warhead_diversity_reports"] is True


def test_multi_source_adapter_architecture():
    manifest = _manifest()
    assert manifest["multi_source_adapter_architecture_defined"] is True
    assert manifest["heterogeneous_datasets_can_share_common_enrichment_pipeline"] is True
    assert manifest["source_specific_adapter_required"] is True
    assert manifest["canonical_raw_record_schema_required"] is True
    assert manifest["common_enrichment_pipeline_required"] is True
    assert manifest["source_dataset_provenance_required"] is True
    assert manifest["source_version_tracking_required"] is True
    assert manifest["license_or_usage_note_required"] is True
    assert manifest["direct_mixture_without_adapter_allowed"] is False
    assert manifest["one_pot_merge_before_normalization_allowed"] is False
    for field in [
        "source_dataset",
        "source_record_id",
        "pdb_id",
        "ligand_structure_path",
        "protein_structure_path",
        "covalent_bond_annotation_raw",
    ]:
        assert field in manifest["canonical_raw_covalent_record_fields"]


def test_required_source_adapter_design():
    manifest = _manifest()
    assert manifest["required_source_adapter_design_defined"] is True
    assert manifest["planned_source_adapters"] == [
        "covpdb_adapter",
        "covbinderinpdb_adapter",
        "covalentindb_adapter",
        "pdb_direct_adapter",
        "local_curated_adapter",
    ]
    assert manifest["planned_source_adapter_display_names"] == [
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "PDB/mmCIF direct",
        "local curated",
    ]
    assert manifest["source_adapter_count"] == 5
    assert manifest["all_source_adapters_output_canonical_raw_records"] is True
    assert manifest["duplicate_detection_across_sources_required"] is True
    assert manifest["source_priority_policy_required"] is True
    details = manifest["source_adapter_design_details"]
    for key in manifest["planned_source_adapters"]:
        assert "purpose" in details[key]
        assert "expected_inputs" in details[key]
        assert "expected_outputs" in details[key]
        assert "risk" in details[key]


def test_enrichment_field_derivation_plan():
    manifest = _manifest()
    assert manifest["enrichment_field_derivation_plan_defined"] is True
    assert manifest["already_exact_present_fields"] == ["sample_id", "ligand_reactive_atom_index"]
    for field in ["parent_complex_id", "pdb_id", "target_name", "reactive_residue_type", "reactive_residue_id"]:
        assert field in manifest["candidate_id_parsing_fields"]
    for field in [
        "canonical_pre_reaction_smiles",
        "ligand_inchikey",
        "ligand_ecfp4_fingerprint",
        "bemis_murcko_scaffold_smiles",
    ]:
        assert field in manifest["ligand_identity_enrichment_fields"]
    for field in ["uniprot_id", "protein_sequence", "protein_sequence_cluster_0p90"]:
        assert field in manifest["protein_identity_enrichment_fields"]
    for field in ["covalent_bond_atom_pair", "warhead_type", "reaction_family"]:
        assert field in manifest["covalent_identity_enrichment_fields"]
    for field in ["ligand_reactive_atom_to_cys_sg_distance", "warhead_orientation_descriptor", "pocket_geometry_bin"]:
        assert field in manifest["geometry_diversity_enrichment_fields"]
    assert manifest["rdkit_required_for_ligand_identity"] is True
    assert manifest["pdb_parser_required_for_protein_identity"] is True
    assert manifest["uniprot_mapping_required"] is True
    assert manifest["cdhit_or_equivalent_required_for_sequence_cluster"] is True
    assert manifest["coordinate_geometry_required"] is True
    assert manifest["warhead_smarts_library_required"] is True
    assert manifest["reaction_family_classifier_required"] is True
    assert manifest["reconstruction_template_registry_required"] is True


def test_enrichment_quality_policy():
    manifest = _manifest()
    assert manifest["enrichment_quality_policy_defined"] is True
    assert manifest["authoritative_metadata_required_for_final_split"] is True
    assert manifest["heuristic_metadata_allowed_for_inventory_only"] is True
    assert manifest["heuristic_metadata_allowed_for_final_split"] is False
    assert manifest["missing_authoritative_metadata_blocks_final_split"] is True
    assert manifest["missing_authoritative_metadata_blocks_training"] is True
    assert manifest["low_confidence_records_deferred"] is True
    assert manifest["ambiguous_covalent_bond_records_deferred"] is True
    assert manifest["ligand_sanitization_fail_records_deferred"] is True
    assert manifest["protein_mapping_fail_records_deferred"] is True
    assert manifest["non_cys_records_identified_but_deferred_for_v1"] is True
    assert manifest["duplicate_records_across_sources_flagged"] is True
    assert manifest["manual_override_allowed_with_audit"] is True
    assert manifest["manual_override_requires_reason"] is True


def test_enrichment_output_schema_and_large_scale_transition():
    manifest = _manifest()
    assert manifest["enrichment_output_schema_defined"] is True
    for key in [
        "future_enriched_sample_index_for_split_required",
        "future_metadata_derivation_manifest_required",
        "future_metadata_gap_report_required",
        "future_ligand_identity_enrichment_report_required",
        "future_protein_identity_enrichment_report_required",
        "future_covalent_identity_enrichment_report_required",
        "future_geometry_diversity_enrichment_report_required",
        "future_multi_source_duplicate_report_required",
        "future_deferred_records_report_required",
        "future_source_adapter_coverage_report_required",
    ]:
        assert manifest[key] is True
    assert manifest["enriched_sample_index_for_split_written"] is False
    assert manifest["metadata_derivation_manifest_written"] is False
    assert manifest["enrichment_reports_written"] is False

    assert manifest["large_scale_data_transition_plan_defined"] is True
    assert manifest["ready_to_design_multi_source_ingestion"] is True
    assert manifest["ready_to_download_large_scale_data_now"] is False
    for key in [
        "download_requires_source_adapter_design",
        "download_requires_storage_policy",
        "download_requires_license_usage_audit",
        "download_requires_incremental_manifest",
        "download_requires_resume_and_checksum_policy",
        "download_requires_raw_data_not_in_git_policy",
        "raw_downloads_must_not_be_committed",
        "large_binary_structures_must_not_be_committed",
    ]:
        assert manifest[key] is True
    assert manifest["recommended_data_sources_for_next_design"] == [
        "CovPDB",
        "CovBinderInPDB",
        "CovalentInDB",
        "PDB/mmCIF direct",
        "local curated",
    ]


def test_safety_flags_and_decision():
    manifest = _manifest()
    for key in [
        "data_downloaded",
        "external_network_called",
        "rdkit_processing_run",
        "uniprot_mapping_run",
        "cdhit_run",
        "coordinate_geometry_calculation_run",
        "npz_files_loaded",
        "npz_contents_read",
        "enriched_sample_index_written",
        "actual_split_assignments_written",
        "actual_leakage_matrix_written",
        "final_split_created",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        design.OPTIMIZER_STEP_CALLED_KEY,
        "training_step_called",
        design.TRAINER_FIT_CALLED_KEY,
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["real_covalent_split_metadata_enrichment_design_gate_passed"] is True
    assert manifest["metadata_enrichment_design_contract_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_multi_source_dataset_ingestion_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_report_manifest_table_and_summary_written():
    _ensure_outputs()
    assert design.REPORT_CSV.is_file()
    assert design.MANIFEST_JSON.is_file()
    assert design.DESIGN_TABLE_CSV.is_file()
    assert design.SUMMARY_MD.is_file()
    assert len(_read_csv(design.REPORT_CSV)) == 9
    table = _read_csv(design.DESIGN_TABLE_CSV)
    assert [row["row_type"] for row in table] == [
        "step12n_precondition",
        "metadata_enrichment_concept",
        "multi_source_adapter_architecture",
        "required_source_adapter_design",
        "enrichment_field_derivation_plan",
        "enrichment_quality_policy",
        "enrichment_output_schema",
        "large_scale_data_transition_plan",
        "safety_and_next_step_decision",
    ]


def test_summary_mentions_required_design_language():
    _ensure_outputs()
    summary = design.SUMMARY_MD.read_text(encoding="utf-8")
    for phrase in [
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
    ]:
        assert phrase in summary


def test_no_forbidden_artifacts_and_no_protected_source_modification():
    _ensure_outputs()
    forbidden = [
        path for path in design.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in design.FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert forbidden == []
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_and_text_safety_for_step12o_files():
    files = [
        Path(design.__file__).resolve(),
        Path(script.__file__).resolve(),
        Path(__file__).resolve(),
    ]
    text_patterns = [
        "model" + "(",
        "compute_" + "masked_loss",
        "." + "backward" + "(",
        "torch." + "optim",
        "optimizer" + "." + "step",
        "trainer" + "." + "fit",
        "training_" + "step" + "(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_" + "from_checkpoint",
        "numpy." + "load",
        "np." + "load",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "requests." + "get",
        "url" + "lib",
        "w" + "get ",
        "cu" + "rl ",
    ]
    compiled = re.compile("|".join(re.escape(pattern) for pattern in text_patterns))
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save" + "_checkpoint",
        "load" + "_from_checkpoint",
        "MolFromSmiles",
        "MolFromMolFile",
        "MolFromPDBFile",
        "GetMorganFingerprint",
        "GetMorganFingerprintAsBitVect",
        "get",
        "urlopen",
    }
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert compiled.search(text) is None
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner in {"np", "numpy"} and func.attr == "load")
                assert not (owner == "torch" and func.attr in {"save", "optim"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in dangerous_attrs
            if isinstance(func, ast.Name):
                assert func.id not in dangerous_names
