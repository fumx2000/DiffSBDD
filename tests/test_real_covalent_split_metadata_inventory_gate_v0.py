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

from covalent_ext import real_covalent_split_metadata_inventory_gate as inventory  # noqa: E402
import check_real_covalent_split_metadata_inventory_gate_v0 as script  # noqa: E402


EXPECTED_SAMPLE_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (
        inventory.REPORT_CSV.is_file()
        and inventory.MANIFEST_JSON.is_file()
        and inventory.INVENTORY_TABLE_CSV.is_file()
        and inventory.SUMMARY_MD.is_file()
    ):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(inventory.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_step12m_precondition_and_inputs_validate():
    assert inventory.validate_step12m_leakage_aware_split_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_split_metadata_inventory_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_leakage_aware_split_design_gate_v0"
    assert manifest["step12m_leakage_aware_split_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False


def test_sample_index_inventory_is_csv_only_and_expected():
    manifest = _manifest()
    assert manifest["sample_index_exists"] is True
    assert manifest["current_sample_index_inspected"] is True
    assert manifest["current_sample_count"] == 3
    assert manifest["sample_ids"] == EXPECTED_SAMPLE_IDS
    assert manifest["sample_index_rows_have_unique_sample_id"] is True
    assert manifest["sample_index_rows_have_nonempty_sample_id"] is True
    assert manifest["sample_index_observed_field_count"] == 14
    for field in [
        "sample_id",
        "ligand_reactive_atom_index",
        "source_sample_id",
        "split",
        "npz_path",
        "npz_sha256",
        "materialization_status",
    ]:
        assert field in manifest["sample_index_observed_fields"]
    assert manifest["sample_index_has_npz_path_column"] is True
    assert manifest["sample_index_has_npz_sha256_column"] is True
    assert manifest["sample_index_has_materialization_status_column"] is True
    assert manifest["sample_index_npz_path_values_nonempty"] is True
    assert manifest["sample_index_npz_sha256_values_nonempty"] is True
    assert manifest["npz_files_loaded"] is False
    assert manifest["npz_contents_read"] is False
    assert manifest["npz_file_existence_checked"] is False
    assert manifest["sample_index_modified"] is False
    assert manifest["enriched_sample_index_written"] is False


def test_required_schema_loaded_and_exact_coverage_counts():
    manifest = _manifest()
    assert manifest["required_split_metadata_schema_loaded_from_step12m"] is True
    assert manifest["required_split_metadata_field_count"] == 38
    assert manifest["metadata_inventory_required_before_split"] is True
    assert manifest["missing_metadata_should_block_final_split"] is True
    assert manifest["present_required_metadata_fields"] == ["sample_id", "ligand_reactive_atom_index"]
    assert manifest["present_required_metadata_field_count"] == 2
    assert manifest["missing_required_metadata_field_count"] == 36
    assert manifest["metadata_completeness_ratio"] == 2 / 38
    assert manifest["metadata_completeness_ratio_text"] == "2/38"
    assert manifest["metadata_complete_for_final_split"] is False
    assert manifest["final_split_blocked_by_missing_metadata"] is True


def test_metadata_group_coverage():
    manifest = _manifest()
    assert manifest["sample_identity_present_fields"] == ["sample_id"]
    for field in ["parent_complex_id", "mask_parent_id", "mask_level"]:
        assert field in manifest["sample_identity_missing_fields"]

    assert manifest["protein_identity_present_fields"] == []
    for field in ["uniprot_id", "protein_sequence_cluster_0p90"]:
        assert field in manifest["protein_identity_missing_fields"]

    assert manifest["ligand_identity_present_fields"] == []
    for field in [
        "canonical_pre_reaction_smiles",
        "ligand_inchikey",
        "ligand_ecfp4_fingerprint",
        "bemis_murcko_scaffold_smiles",
    ]:
        assert field in manifest["ligand_identity_missing_fields"]

    assert manifest["covalent_identity_present_fields"] == ["ligand_reactive_atom_index"]
    for field in ["reactive_residue_type", "covalent_bond_atom_pair", "warhead_type", "reaction_family"]:
        assert field in manifest["covalent_identity_missing_fields"]

    assert manifest["geometry_diversity_present_fields"] == []
    for field in ["ligand_reactive_atom_to_cys_sg_distance", "pocket_geometry_bin"]:
        assert field in manifest["geometry_diversity_missing_fields"]


def test_observed_nonrequired_fields_are_inventoried_without_claiming_split():
    manifest = _manifest()
    assert manifest["observed_nonrequired_field_count"] == 12
    for field in [
        "ligand_atom_count",
        "ligand_bond_count",
        "protein_atom_count",
        "protein_residue_count",
        "scaffold_atom_count",
        "linker_atom_count",
        "warhead_atom_count",
        "materialization_status",
        "npz_path",
        "npz_sha256",
        "source_sample_id",
        "split",
    ]:
        assert field in manifest["observed_nonrequired_fields"]
    for field in ["ligand_atom_count", "protein_atom_count", "scaffold_atom_count", "linker_atom_count", "warhead_atom_count"]:
        assert field in manifest["observed_count_fields"]
    assert manifest["observed_path_hash_fields"] == ["npz_path", "npz_sha256"]
    assert manifest["observed_existing_split_field_present"] is True
    assert manifest["observed_split_field_is_not_final_leakage_aware_split"] is True
    assert manifest["observed_split_field_must_not_be_used_for_paper_claim"] is True
    assert manifest["observed_source_sample_id_field_present"] is True
    assert manifest["observed_atom_count_fields_present"] is True


def test_candidate_derivation_plan_requires_validation():
    manifest = _manifest()
    assert manifest["candidate_derivation_plan_defined"] is True
    assert "sample_id" in manifest["direct_exact_fields_already_available"]
    assert "ligand_reactive_atom_index" in manifest["direct_exact_fields_already_available"]
    for field in ["target_name", "source_pdb_id", "pdb_id", "reactive_residue_type", "reactive_residue_id"]:
        assert field in manifest["candidate_fields_derivable_from_sample_id"]
    for field in ["parent_complex_id", "mask_parent_id"]:
        assert field in manifest["candidate_fields_derivable_from_source_sample_id"]
    assert manifest["candidate_derived_metadata_authoritative"] is False
    assert manifest["heuristic_parsing_allowed_for_inventory_only"] is True
    assert manifest["heuristic_parsing_not_allowed_for_final_split_without_validation"] is True
    assert manifest["source_sample_id_to_parent_complex_mapping_requires_validation"] is True
    assert manifest["sample_id_regex_parsing_requires_validation"] is True


def test_enrichment_requirements_are_classified():
    manifest = _manifest()
    for field in [
        "canonical_pre_reaction_smiles",
        "ligand_inchikey",
        "ligand_ecfp4_fingerprint",
        "bemis_murcko_scaffold_smiles",
        "warhead_type",
        "reaction_family",
    ]:
        assert field in manifest["fields_requiring_ligand_structure_processing"]
    for field in ["uniprot_id", "protein_sequence", "protein_sequence_cluster_0p90", "local_pocket_signature"]:
        assert field in manifest["fields_requiring_protein_structure_or_sequence_mapping"]
    for field in ["covalent_bond_atom_pair", "ligand_reactive_atom_to_cys_sg_distance", "pocket_geometry_bin"]:
        assert field in manifest["fields_requiring_coordinate_geometry_calculation"]


def test_future_enrichment_outputs_and_feasibility_decision():
    manifest = _manifest()
    assert manifest["future_metadata_enrichment_output_plan_defined"] is True
    assert manifest["future_enriched_sample_index_required"] is True
    assert manifest["future_metadata_gap_report_required"] is True
    assert manifest["future_candidate_id_mapping_report_required"] is True
    assert manifest["future_ligand_identity_enrichment_report_required"] is True
    assert manifest["future_protein_identity_enrichment_report_required"] is True
    assert manifest["future_covalent_identity_enrichment_report_required"] is True
    assert manifest["future_geometry_diversity_enrichment_report_required"] is True
    assert manifest["metadata_gap_report_written"] is False
    assert manifest["candidate_id_mapping_report_written"] is False

    assert manifest["metadata_inventory_feasibility_decision_defined"] is True
    assert manifest["metadata_gap_level"] == "severe"
    assert manifest["metadata_enrichment_required"] is True
    assert manifest["metadata_enrichment_design_allowed"] is True
    assert manifest["dataset_size_still_blocks_final_split"] is True
    assert manifest["final_train_valid_test_split_allowed"] is False
    assert manifest["final_paper_claim_allowed"] is False
    assert manifest["split_implementation_allowed_after_this_step"] is False
    assert manifest["formal_training_allowed"] is False


def test_safety_flags_and_decision():
    manifest = _manifest()
    for key in [
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        inventory.OPTIMIZER_STEP_CALLED_KEY,
        "training_step_called",
        inventory.TRAINER_FIT_CALLED_KEY,
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
        "actual_split_assignments_written",
        "actual_leakage_matrix_written",
        "final_split_created",
    ]:
        assert manifest[key] is False
    assert manifest["real_covalent_split_metadata_inventory_gate_passed"] is True
    assert manifest["split_metadata_inventory_contract_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_split_metadata_enrichment_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_report_manifest_table_and_summary_written():
    _ensure_outputs()
    assert inventory.REPORT_CSV.is_file()
    assert inventory.MANIFEST_JSON.is_file()
    assert inventory.INVENTORY_TABLE_CSV.is_file()
    assert inventory.SUMMARY_MD.is_file()
    report = _read_csv(inventory.REPORT_CSV)
    table = _read_csv(inventory.INVENTORY_TABLE_CSV)
    assert len(report) == 10
    assert sum(row["row_type"] == "required_metadata_field_inventory" for row in table) == 38
    assert sum(row["row_type"] == "metadata_group_summary" for row in table) == 5


def test_summary_mentions_required_inventory_language():
    _ensure_outputs()
    summary = inventory.SUMMARY_MD.read_text(encoding="utf-8")
    assert "split metadata inventory gate" in summary
    assert "not enrichment" in summary
    assert "not split implementation" in summary
    assert "not training" in summary
    assert "3 samples" in summary
    assert "field count: 38" in summary
    assert "sample_id, ligand_reactive_atom_index" in summary
    assert "missing required metadata count: 36" in summary
    assert "metadata completeness: 2/38" in summary
    assert "split field is not final leakage-aware split" in summary
    assert "No NPZ contents read" in summary
    assert "No enriched sample_index written" in summary
    assert "No split assignments written" in summary
    assert "Candidate metadata parsed from sample_id or source_sample_id is not authoritative" in summary
    assert "ligand identity requires RDKit/ligand structure" in summary
    assert "protein identity requires sequence/UniProt/CD-HIT" in summary
    assert "geometry requires coordinate calculation" in summary
    assert "metadata gap level: severe" in summary
    assert "recommended_next_step: real_covalent_split_metadata_enrichment_design_gate" in summary


def test_no_forbidden_artifacts_and_no_protected_source_modification():
    _ensure_outputs()
    forbidden = [
        path for path in inventory.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in inventory.FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert forbidden == []
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_and_text_safety_for_step12n_files():
    files = [
        Path(inventory.__file__).resolve(),
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
    ]
    compiled = re.compile("|".join(re.escape(pattern) for pattern in text_patterns))
    forbidden_attr = {"backward", "fit", "save"}
    forbidden_names = {"Adam", "AdamW", "SGD", "RMSprop"}
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
                assert func.attr not in forbidden_attr
                assert func.attr not in {"save" + "_checkpoint", "load" + "_from_checkpoint"}
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_names
