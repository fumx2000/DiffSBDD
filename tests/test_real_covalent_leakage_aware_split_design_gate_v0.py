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

from covalent_ext import real_covalent_leakage_aware_split_design_gate as design  # noqa: E402
import check_real_covalent_leakage_aware_split_design_gate_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (
        design.REPORT_CSV.is_file()
        and design.MANIFEST_JSON.is_file()
        and design.DESIGN_TABLE_CSV.is_file()
        and design.SUMMARY_MD.is_file()
    ):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(design.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_step12l_precondition_and_inputs_validate():
    assert design.validate_step12l_training_loop_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_leakage_aware_split_design_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_training_loop_design_gate_v0"
    assert manifest["step12l_training_loop_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False


def test_current_sample_index_audit_blocks_final_split_but_allows_design():
    manifest = _manifest()
    assert manifest["sample_index_exists"] is True
    assert manifest["current_sample_index_inspected"] is True
    assert manifest["current_sample_count"] > 0
    assert manifest["sample_ids"] == [
        "BTK_C481_6DI9_pre_reaction",
        "KRAS_G12C_5F2E_pre_reaction",
        "KRAS_G12C_6OIM_pre_reaction",
    ]
    assert manifest["current_dataset_is_small_smoke_set"] is True
    assert manifest["current_dataset_final_split_feasible"] is False
    assert (
        manifest["current_dataset_final_split_blocking_reason"]
        == "insufficient_sample_count_for_leakage_aware_train_valid_test_split"
    )
    assert manifest["actual_train_valid_test_split_created"] is False
    assert manifest["split_manifest_created"] is False
    assert manifest["engineering_smoke_split_design_allowed"] is True
    assert manifest["final_paper_split_allowed"] is False


def test_required_metadata_schema_is_complete_and_inventory_is_required():
    manifest = _manifest()
    assert manifest["required_split_metadata_schema_defined"] is True
    assert manifest["required_split_metadata_field_count"] == len(manifest["required_split_metadata_fields"])
    for field in ["sample_id", "parent_complex_id", "mask_parent_id", "mask_level", "source_pdb_id"]:
        assert field in manifest["required_sample_identity_fields"]
    for field in ["uniprot_id", "protein_sequence", "protein_sequence_cluster_0p90", "local_pocket_signature"]:
        assert field in manifest["required_protein_identity_fields"]
    for field in ["canonical_pre_reaction_smiles", "ligand_inchikey", "ligand_ecfp4_fingerprint"]:
        assert field in manifest["required_ligand_identity_fields"]
    for field in ["reactive_residue_type", "covalent_bond_atom_pair", "post_to_pre_reconstruction_template_id"]:
        assert field in manifest["required_covalent_identity_fields"]
    for field in ["warhead_orientation_descriptor", "linker_length_bin", "pocket_geometry_bin"]:
        assert field in manifest["required_geometry_diversity_fields"]
    assert manifest["metadata_inventory_required_before_split"] is True
    assert manifest["missing_metadata_should_block_final_split"] is True
    assert manifest["sample_index_missing_required_split_metadata_field_count"] > 0


def test_hard_overlap_policy_is_zero_tolerance_and_parent_grouped():
    manifest = _manifest()
    assert manifest["hard_overlap_split_policy_defined"] is True
    assert manifest["hard_overlap_zero_tolerance"] is True
    for entity in [
        "sample_id",
        "parent_complex_id",
        "mask_parent_id",
        "pdb_id",
        "uniprot_id",
        "canonical_pre_reaction_smiles",
        "ligand_inchikey",
        "ligand_inchikey_connectivity_layer",
        "protein_reactive_residue_id",
        "covalent_bond_atom_pair",
        "post_to_pre_reconstruction_template_id",
    ]:
        assert entity in manifest["hard_overlap_entities"]
    assert manifest["same_parent_complex_cross_split_allowed"] is False
    assert manifest["same_mask_parent_cross_split_allowed"] is False
    assert manifest["same_sample_id_cross_split_allowed"] is False
    assert manifest["same_pdb_cross_split_allowed_for_target_holdout"] is False
    assert manifest["same_uniprot_cross_split_allowed_for_target_holdout"] is False
    assert manifest["same_ligand_inchikey_cross_split_allowed"] is False
    assert manifest["same_canonical_smiles_cross_split_allowed"] is False
    assert manifest["same_covalent_bond_atom_pair_requires_distribution_report"] is True
    assert manifest["hard_overlap_violation_blocks_split"] is True
    assert manifest["hard_overlap_violation_blocks_training"] is True
    assert manifest["mask_levels_grouped_by_parent_sample"] is True


def test_soft_overlap_policy_and_thresholds():
    manifest = _manifest()
    assert manifest["soft_overlap_split_policy_defined"] is True
    assert manifest["protein_sequence_identity_soft_overlap_threshold"] == 0.90
    assert manifest["ligand_ecfp4_tanimoto_soft_overlap_threshold"] == 0.90
    assert manifest["soft_overlap_rule"] == "protein_sequence_cluster_ge_0.90_and_ligand_ecfp4_tanimoto_gt_0.90"
    assert manifest["protein_sequence_cluster_method_design"] == "CD-HIT_or_equivalent_offline_cluster_at_0.90"
    assert manifest["ligand_similarity_method_design"] == "RDKit_ECFP4_radius2_Tanimoto"
    for key in [
        "binding_site_cluster_design_required",
        "bemis_murcko_scaffold_overlap_report_required",
        "warhead_overlap_report_required",
        "reaction_family_overlap_report_required",
        "protein_cluster_overlap_report_required",
        "ligand_ecfp4_overlap_report_required",
        "scaffold_overlap_report_required",
        "target_family_overlap_report_required",
        "split_type_specific_soft_overlap_behavior_defined",
        "parent_group_random_split_soft_overlap_report_only",
        "scaffold_holdout_blocks_same_scaffold",
        "target_cluster_holdout_blocks_same_protein_cluster",
        "nlrp3_external_overlap_report_required",
    ]:
        assert manifest[key] is True
    assert manifest["soft_overlap_violation_blocks_primary_test_claim"] is True
    assert manifest["soft_overlap_violation_requires_limitation_note"] is True


def test_leakage_matrix_schema_and_future_outputs():
    manifest = _manifest()
    assert manifest["leakage_matrix_schema_defined"] is True
    assert manifest["leakage_matrix_pairs"] == ["train_vs_valid", "train_vs_test", "valid_vs_test"]
    for column in [
        "pair_name",
        "hard_overlap_count",
        "parent_complex_overlap_count",
        "mask_parent_overlap_count",
        "protein_cluster_0p90_overlap_count",
        "ligand_ecfp4_tanimoto_max",
        "bemis_murcko_scaffold_overlap_count",
        "warhead_type_overlap_count",
        "reaction_family_overlap_count",
        "reconstruction_template_overlap_count",
        "nlrp3_external_overlap_flag",
        "leakage_status",
        "claim_allowed",
    ]:
        assert column in manifest["leakage_matrix_required_columns"]
    assert manifest["leakage_matrix_required_before_training"] is True
    assert manifest["leakage_matrix_required_before_paper_claim"] is True
    assert manifest["train_valid_test_leakage_matrix_required"] is True

    assert manifest["future_split_output_schema_defined"] is True
    for key in [
        "future_split_manifest_required",
        "future_split_assignments_required",
        "future_leakage_matrix_required",
        "future_scaffold_holdout_report_required",
        "future_target_cluster_holdout_report_required",
        "future_warhead_distribution_report_required",
        "future_reaction_family_distribution_report_required",
        "future_cys_train_ready_inventory_required",
        "future_nlrp3_external_overlap_report_required",
    ]:
        assert manifest[key] is True
    assert manifest["actual_split_assignments_written"] is False
    assert manifest["actual_leakage_matrix_written"] is False
    assert manifest["final_split_created"] is False


def test_split_feasibility_decision_and_next_step():
    manifest = _manifest()
    assert manifest["split_feasibility_decision_defined"] is True
    assert manifest["current_dataset_feasibility_label"] == "small_smoke_only"
    assert manifest["final_train_valid_test_split_allowed"] is False
    assert manifest["final_paper_claim_allowed"] is False
    assert manifest["engineering_smoke_split_design_allowed"] is True
    assert manifest["final_split_requires_metadata_inventory"] is True
    assert manifest["split_implementation_allowed_after_this_step"] is False
    assert "insufficient_sample_count_for_leakage_aware_train_valid_test_split" in manifest[
        "split_feasibility_blocking_reasons"
    ]
    assert manifest["real_covalent_leakage_aware_split_design_gate_passed"] is True
    assert manifest["split_design_contract_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_split_metadata_inventory_gate"


def test_safety_flags_and_no_training_side_effects():
    manifest = _manifest()
    for key in [
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
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_report_manifest_table_and_summary_are_written():
    _ensure_outputs()
    assert design.REPORT_CSV.is_file()
    assert design.MANIFEST_JSON.is_file()
    assert design.DESIGN_TABLE_CSV.is_file()
    assert design.SUMMARY_MD.is_file()
    assert len(_read_csv(design.REPORT_CSV)) == 9
    table = _read_csv(design.DESIGN_TABLE_CSV)
    assert [row["row_type"] for row in table] == [
        "step12l_precondition",
        "sample_index_audit",
        "required_split_metadata_schema",
        "hard_overlap_split_policy",
        "soft_overlap_split_policy",
        "leakage_matrix_schema",
        "future_split_output_schema",
        "split_feasibility_decision",
        "safety_and_next_step_decision",
    ]


def test_summary_mentions_required_design_language():
    _ensure_outputs()
    summary = design.SUMMARY_MD.read_text(encoding="utf-8")
    assert "leakage-aware split design gate" in summary
    assert "not split implementation, not training" in summary
    assert "training loop design gate verified" in summary
    assert "engineering smoke set" in summary
    assert "insufficient for final train/valid/test leakage-aware split" in summary
    assert "Hard overlap zero tolerance" in summary
    assert "parent_complex_id" in summary
    assert "mask_parent_id" in summary
    assert "A/B/B2/B3/C mask levels" in summary
    assert "Protein sequence identity threshold: 0.90" in summary
    assert "Ligand ECFP4 Tanimoto threshold: 0.90" in summary
    assert "train/valid/test leakage matrix schema is defined" in summary
    assert "No formal split, no split assignments, and no leakage matrix" in summary
    assert "recommended_next_step: real_covalent_split_metadata_inventory_gate" in summary


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


def test_ast_and_text_safety_for_step12m_files():
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
                assert not (owner == "torch" and func.attr in {"save", "optim"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in forbidden_attr
                assert func.attr not in {"save" + "_checkpoint", "load" + "_from_checkpoint"}
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_names
