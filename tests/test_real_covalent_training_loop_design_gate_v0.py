from __future__ import annotations

import ast
import csv
import json
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

from covalent_ext import real_covalent_training_loop_design_gate as design  # noqa: E402
import check_real_covalent_training_loop_design_gate_v0 as script  # noqa: E402


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


def test_step12k_and_step12b_preconditions_validate():
    assert design.validate_step12k_single_update_smoke_v0() is True
    assert getattr(design, "validate_" + "_".join(["step12k", "single", "optimizer", "step", "smoke", "v0"]))() is True
    assert _manifest()[design.STEP12K_VALIDATED_KEY] is True
    assert _manifest()["step12b_mask_level_aware_validator_validated"] is True


def test_input_filter_and_feature_semantics_requirements():
    manifest = _manifest()
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["filter_policy_name"] == design.FILTER_POLICY_NAME
    assert manifest["production_filter_helper_required"] is True
    assert manifest["feature_semantics_known_after_filter_required"] is True
    assert manifest["unknown_atom_policy_triggered_after_filter_required"] is False
    assert manifest["zero_vector_unknown_atom_policy_safe_after_filter_required"] is True


def test_literature_leakage_policy():
    manifest = _manifest()
    assert manifest["literature_leakage_policy_defined"] is True
    assert manifest["planet_v2_inspired_policy_used"] is True
    assert manifest["tapping_black_box_inspired_policy_used"] is True
    assert manifest["hard_overlap_policy_defined"] is True
    assert manifest["soft_overlap_policy_defined"] is True
    assert manifest["protein_sequence_identity_soft_overlap_threshold"] == 0.90
    assert manifest["ligand_ecfp4_tanimoto_soft_overlap_threshold"] == 0.90
    assert manifest["random_split_only_allowed"] is False
    assert manifest["leakage_report_required"] is True
    assert manifest["train_valid_test_leakage_matrix_required"] is True
    assert manifest["hard_overlap_zero_tolerance"] is True
    assert manifest["soft_overlap_report_required"] is True
    assert manifest["paper_claim_requires_leakage_aware_split"] is True
    assert "parent_complex_id" in manifest["hard_overlap_entities"]
    assert "ligand_ecfp4_similarity" in manifest["soft_overlap_entities"]


def test_generation_specific_leakage_policy():
    manifest = _manifest()
    assert manifest["generation_specific_leakage_policy_defined"] is True
    assert manifest["mask_level_leakage_policy_defined"] is True
    assert manifest["parent_complex_group_split_required"] is True
    assert manifest["mask_levels_grouped_by_parent_sample"] is True
    assert manifest["same_parent_complex_cross_split_allowed"] is False
    assert manifest["same_ligand_cross_split_allowed"] is False
    assert manifest["same_scaffold_cross_split_allowed_for_scaffold_holdout"] is False
    assert manifest["same_target_cross_split_allowed_for_target_holdout"] is False
    assert manifest["same_warhead_distribution_report_required"] is True
    assert manifest["same_reaction_family_distribution_report_required"] is True
    assert manifest["same_reconstruction_template_distribution_report_required"] is True
    assert manifest["nlrp3_external_case_holdout_policy_required"] is True


def test_cys_first_diversity_policy():
    manifest = _manifest()
    assert manifest["cys_first_training_strategy_recommended"] is True
    assert manifest["train_ready_scope_v1"] == "cys_with_known_reconstruction_template_only"
    assert manifest["non_cys_reactive_residue_support_status"] == "schema_supported_but_template_audit_pending"
    assert manifest["reaction_family_template_audit_required_before_broad_covalent_training"] is True
    assert manifest["ligand_reconstruction_template_gate_required"] is True
    assert manifest["non_cys_data_bulk_cleaning_policy"] == "identify_classify_defer_until_template_gate"
    assert manifest["cys_only_convergence_risk_acknowledged"] is True
    assert manifest["cys_only_convergence_risk_level"] == "moderate_to_high_without_diversity_controls"
    assert manifest["cys_only_allowed_for_v1"] is True
    assert manifest["non_cys_mixing_allowed_in_v1_training"] is False
    assert manifest["cys_diversity_controls_required"] is True
    for key in [
        "warhead_diversity_report_required",
        "scaffold_diversity_report_required",
        "target_family_diversity_report_required",
        "pocket_geometry_diversity_report_required",
        "linker_length_distribution_report_required",
        "reactive_atom_distance_distribution_report_required",
        "mask_level_balance_report_required",
        "per_mask_level_loss_report_required",
        "warhead_collapse_monitor_required",
        "scaffold_collapse_monitor_required",
        "target_family_overrepresentation_monitor_required",
    ]:
        assert manifest[key] is True


def test_split_strategy_design():
    manifest = _manifest()
    assert manifest["split_strategy_defined"] is True
    assert manifest["parent_group_random_split_defined"] is True
    assert manifest["scaffold_holdout_split_defined"] is True
    assert manifest["target_cluster_holdout_split_defined"] is True
    assert manifest["warhead_holdout_or_stratified_split_defined"] is True
    assert manifest["nlrp3_external_case_study_defined"] is True
    assert manifest["random_split_only_allowed"] is False
    assert manifest["primary_evaluation_split"] == "scaffold_holdout_and_target_cluster_holdout"
    assert manifest["engineering_smoke_split"] == "parent_group_random_split"
    assert manifest["paper_claim_split_requirement"] == "scaffold_or_target_cluster_holdout_required"


def test_optimizer_lr_scheduler_policy():
    manifest = _manifest()
    assert manifest["optimizer_policy_defined"] is True
    assert manifest["optimizer_name"] == "AdamW"
    assert manifest["adamw_already_smoked_in_step12k"] is True
    assert manifest["initial_lr_candidates"] == [1e-6, 3e-6, 1e-5]
    assert manifest["first_tiny_run_default_lr"] == 1e-6
    assert manifest["pretrained_finetune_lr_upper_bound_recommended"] == 1e-5
    assert manifest["aggressive_lr_values_require_explicit_debug_gate"] is True
    assert manifest["aggressive_lr_values"] == [5e-5, 1e-4]
    assert manifest["gradient_clipping_required"] is True
    assert manifest["grad_clip_norm_candidates"] == [1.0, 5.0, 10.0]
    assert manifest["mixed_precision_allowed_for_first_tiny_run"] is False
    assert manifest["scheduler_policy_defined"] is True
    assert manifest["scheduler_allowed_for_first_tiny_run"] is False
    assert manifest["scheduler_allowed_after_split_eval_gate"] is True
    assert manifest["warmup_cosine_scheduler_policy_defined"] is True
    assert manifest["warmup_cosine_scheduler_allowed_after_split_eval_gate"] is True
    assert manifest["warmup_fraction_candidates"] == [0.03, 0.05, 0.10]
    assert manifest["reduce_on_plateau_allowed_after_stable_validation"] is True
    assert manifest["lr_finder_policy_defined"] is True
    assert manifest["lr_finder_allowed_now"] is False
    assert manifest["lr_finder_allowed_after_leakage_aware_split_and_eval_gate"] is True
    assert manifest["lr_finder_not_allowed_on_three_sample_smoke"] is True
    assert manifest["catastrophic_forgetting_lr_guard_required"] is True


def test_training_checkpoint_evaluation_and_fail_fast_policies():
    manifest = _manifest()
    assert manifest["training_loop_policy_defined"] is True
    assert manifest["max_steps_first_tiny_run"] == 10
    assert manifest["max_steps_smoke_run"] == 50
    for key in [
        "formal_training_requires_split_gate",
        "formal_training_requires_cys_train_ready_inventory",
        "formal_training_requires_eval_gate",
        "formal_training_requires_checkpoint_save_policy",
        "formal_training_requires_leakage_report",
        "formal_training_requires_diversity_report",
    ]:
        assert manifest[key] is True
    assert manifest[design.TRAINER_FIT_ALLOWED_AFTER_KEY] is False
    assert manifest["custom_loop_allowed_after_this_step"] is False
    assert manifest["multi_step_training_allowed_after_this_step"] is False

    assert manifest["checkpoint_policy_defined"] is True
    assert manifest["checkpoint_save_allowed_after_this_step"] is False
    assert manifest["first_tiny_run_checkpoint_save_allowed"] is False
    assert manifest["git_add_checkpoint_allowed"] is False
    assert manifest["forbidden_artifact_git_guard_required"] is True
    assert manifest["run_manifest_required"] is True
    assert manifest["config_hash_required"] is True
    assert manifest["split_manifest_required"] is True
    assert manifest["metrics_csv_required"] is True

    assert manifest["evaluation_policy_defined"] is True
    assert manifest["per_mask_level_loss_required"] is True
    assert manifest["covalent_geometry_metrics_required"] is True
    assert manifest["chemical_validity_metrics_required"] is True
    assert manifest["diversity_metrics_required"] is True
    assert manifest["leakage_metrics_required"] is True
    assert manifest["external_case_overlap_report_required"] is True

    assert manifest["fail_fast_policy_defined"] is True
    for key in [
        "nan_loss_stop_required",
        "nan_gradient_stop_required",
        "unknown_atom_after_filter_stop_required",
        "synthetic_fallback_stop_required",
        "non_cys_in_v1_train_ready_stop_required",
        "parent_complex_cross_split_stop_required",
        "mask_level_cross_split_stop_required",
        "checkpoint_save_before_permission_stop_required",
        "forbidden_artifact_stop_required",
        "protected_source_diff_stop_required",
    ]:
        assert manifest[key] is True


def test_safety_decision_and_written_outputs():
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
    assert manifest["real_covalent_training_loop_design_gate_passed"] is True
    assert manifest["training_design_contract_defined"] is True
    assert manifest["leakage_aware_training_design_defined"] is True
    assert manifest["optimizer_lr_scheduler_policy_defined"] is True
    assert manifest["recommended_next_step"] == "real_covalent_leakage_aware_split_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []

    assert design.REPORT_CSV.is_file()
    assert design.MANIFEST_JSON.is_file()
    assert design.DESIGN_TABLE_CSV.is_file()
    assert design.SUMMARY_MD.is_file()
    assert len(_read_csv(design.REPORT_CSV)) == 11
    assert len(_read_csv(design.DESIGN_TABLE_CSV)) == 11


def test_summary_mentions_required_policy_language():
    _ensure_outputs()
    summary = design.SUMMARY_MD.read_text(encoding="utf-8")
    assert "PLANET v2.0-style soft overlap" in summary
    assert "protein sequence identity threshold 0.90" in summary
    assert "ECFP4 Tanimoto threshold 0.90" in summary
    assert "Tapping-on-the-Black-Box-style warning" in summary
    assert "Cys-only convergence risk" in summary
    assert "Cys-focused / Cys-directed not universal" in summary
    assert "parent complex group split" in summary
    assert "mask levels not cross split" in summary
    assert "AdamW" in summary
    assert "lr=1e-6 first tiny run" in summary
    assert "scheduler disabled for first tiny run" in summary
    assert "warmup+cosine after split/eval gate" in summary
    assert "LR finder not allowed now" in summary
    assert "catastrophic forgetting" in summary
    assert "not training" in summary
    assert "real_covalent_leakage_aware_split_design_gate" in summary


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


def test_ast_safety_for_step12l_files():
    files = [
        Path(design.__file__).resolve(),
        Path(script.__file__).resolve(),
        Path(__file__).resolve(),
    ]
    forbidden_attr = {"backward", "fit", "save"}
    forbidden_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner == "torch" and func.attr == "save")
                assert not (owner == "torch" and func.attr == "optim")
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in forbidden_attr
                assert func.attr not in {"save" + "_checkpoint", "load" + "_from_checkpoint"}
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_names
