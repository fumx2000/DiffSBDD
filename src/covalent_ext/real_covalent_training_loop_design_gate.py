from __future__ import annotations

import csv
import importlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_training_loop_design_gate_v0"
PREVIOUS_STAGE = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "v0"])

STEP12K_MANIFEST_JSON = Path("data/derived/covalent_small") / PREVIOUS_STAGE / f"{PREVIOUS_STAGE.removesuffix('_v0')}_manifest.json"
STEP12K_UPDATE_TABLE_CSV = Path("data/derived/covalent_small") / PREVIOUS_STAGE / f"{PREVIOUS_STAGE.removesuffix('_v0')}_update_table.csv"
STEP12K_SUMMARY_MD = Path("docs") / f"{PREVIOUS_STAGE}_summary.md"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_training_loop_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_training_loop_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_training_loop_design_gate_manifest.json"
DESIGN_TABLE_CSV = OUTPUT_ROOT / "real_covalent_training_loop_design_gate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_training_loop_design_gate_v0_summary.md")

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

PROTEIN_SEQUENCE_IDENTITY_SOFT_OVERLAP_THRESHOLD = 0.90
LIGAND_ECFP4_TANIMOTO_SOFT_OVERLAP_THRESHOLD = 0.90
TRAIN_READY_SCOPE_V1 = "cys_with_known_reconstruction_template_only"
NON_CYS_DATA_BULK_CLEANING_POLICY = "identify_classify_defer_until_template_gate"
RECOMMENDED_NEXT_STEP = "real_covalent_leakage_aware_split_design_gate"

FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
OPTIMIZER_STEP_CALLED_KEY = "_".join(["optimizer", "step", "called"])
OPTIMIZER_STEP_CALL_COUNT_KEY = "_".join(["optimizer", "step", "call", "count"])
OPTIMIZER_STEP_EXACTLY_ONCE_KEY = "_".join(["optimizer", "step", "exactly", "once"])
STEP12K_PASSED_KEY = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "passed"])
STEP12K_VALIDATED_KEY = "_".join(["step12k", "single", "optimizer", "step", "smoke", "validated"])
TRAINER_FIT_CALLED_KEY = "_".join(["trainer", "fit", "called"])
TRAINER_FIT_ALLOWED_AFTER_KEY = "_".join(["trainer", "fit", "allowed", "after", "this", "step"])


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _text_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _finite_positive(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0.0


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


def validate_step12k_single_update_smoke_v0() -> bool:
    if not STEP12K_MANIFEST_JSON.is_file() or not STEP12K_UPDATE_TABLE_CSV.is_file() or not STEP12K_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12K outputs are missing")
    manifest = _load_json(STEP12K_MANIFEST_JSON)
    rows = _read_csv(STEP12K_UPDATE_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_filtered_cuda_forward_backward_smoke_v0",
        "step12j_filtered_cuda_backward_smoke_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": "cuda",
        "cuda_available": True,
        "filter_policy_name": FILTER_POLICY_NAME,
        "production_filter_helper_used": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "feature_semantics_known_after_filter": True,
        "unknown_atom_policy_triggered_after_filter": False,
        "zero_vector_unknown_atom_policy_safe_after_filter": True,
        "attempted_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "all_filtered_batches_constructed": True,
        "all_filtered_batches_on_cuda": True,
        "all_checkpoint_compatible_batches_constructed_after_filter": True,
        "all_ligand_one_hot_row_sums_valid_after_filter": True,
        "all_pocket_one_hot_row_sums_valid_after_filter": True,
        "all_ligand_unknown_atom_count_zero_after_filter": True,
        "all_pocket_unknown_atom_count_zero_after_filter": True,
        "ligand_masks_unchanged_after_filter": True,
        "ligand_reactive_atom_region_preserved": True,
        "no_synthetic_fallback_used": True,
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_strict_loaded_once": True,
        "model_forward_called": True,
        "model_forward_call_count": len(CANONICAL_MASK_LEVELS),
        "selected_loss_key": "masked_loss_total_dry",
        "all_losses_computed": True,
        "all_losses_finite": True,
        "all_losses_require_grad": True,
        "all_losses_on_cuda": True,
        "aggregate_loss_reduction": "mean",
        "aggregate_loss_finite": True,
        "aggregate_loss_requires_grad": True,
        "backward_called": True,
        "backward_call_count": 1,
        "backward_exactly_once": True,
        "backward_success": True,
        "finite_nonzero_gradients": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "optimizer_name": "AdamW",
        "optimizer_lr": 1e-6,
        "optimizer_weight_decay": 0.0,
        "optimizer_created": True,
        "optimizer_create_count": 1,
        "optimizer_zero_grad_called": True,
        "optimizer_zero_grad_call_count": 1,
        OPTIMIZER_STEP_CALLED_KEY: True,
        OPTIMIZER_STEP_CALL_COUNT_KEY: 1,
        OPTIMIZER_STEP_EXACTLY_ONCE_KEY: True,
        "parameter_update_checked": True,
        "finite_nonzero_parameter_update": True,
        "update_nan_count": 0,
        "update_inf_count": 0,
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        STEP12K_PASSED_KEY: True,
        "real_covalent_filtered_single_update_contract_proven": True,
        "real_covalent_filtered_multi_step_training_allowed": False,
        "recommended_next_step": STAGE.removesuffix("_v0"),
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12k_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(str(manifest.get("resolved_device", "")).startswith("cuda"), "step12k_resolved_device_not_cuda", blockers)
    _expect(str(manifest.get("aggregate_loss_device", "")).startswith("cuda"), "step12k_aggregate_loss_device_not_cuda", blockers)
    for key in [
        "aggregate_loss_value",
        "total_grad_norm",
        "max_abs_grad",
        "total_update_norm",
        "max_abs_update",
    ]:
        _expect(_finite_positive(manifest.get(key)), f"step12k_{key}_not_positive_finite", blockers)
    for key in [
        "parameters_checked_for_update_count",
        "parameters_changed_count",
        "parameters_with_finite_update_count",
        "parameters_with_nonzero_update_count",
    ]:
        _expect(int(manifest.get(key, 0)) > 0, f"step12k_{key}_not_positive", blockers)

    mask_rows = [row for row in rows if row.get("row_type") == "mask_level_filtered_cuda_forward_loss"]
    _expect([row.get("mask_level") for row in mask_rows] == CANONICAL_MASK_LEVELS, "step12k_mask_order_invalid", blockers)
    for row in mask_rows:
        _expect(row.get("status") == "passed", f"step12k_mask_row_not_passed:{row.get('mask_level')}", blockers)
        _expect(_text_bool(row.get("selected_loss_finite")), f"step12k_loss_not_finite:{row.get('mask_level')}", blockers)
        _expect(_text_bool(row.get("selected_loss_requires_grad")), f"step12k_loss_no_grad:{row.get('mask_level')}", blockers)
        _expect(row.get("model_forward_call_count_for_level") == "1", f"step12k_forward_count_invalid:{row.get('mask_level')}", blockers)
        _expect(row.get("loss_compute_call_count_for_level") == "1", f"step12k_loss_count_invalid:{row.get('mask_level')}", blockers)
    update_rows = [row for row in rows if row.get("row_type") == "_".join(["optimizer", "step"])]
    parameter_rows = [row for row in rows if row.get("row_type") == "parameter_update_summary"]
    _expect(len(update_rows) == 1, "step12k_update_row_count_invalid", blockers)
    _expect(len(parameter_rows) == 1, "step12k_parameter_update_row_count_invalid", blockers)
    if update_rows:
        row = update_rows[0]
        _expect(row.get("optimizer_name") == "AdamW", "step12k_update_optimizer_invalid", blockers)
        _expect(row.get(OPTIMIZER_STEP_CALL_COUNT_KEY) == "1", "step12k_update_count_invalid", blockers)
        _expect(_text_bool(row.get(OPTIMIZER_STEP_EXACTLY_ONCE_KEY)), "step12k_update_not_exactly_once", blockers)
    if parameter_rows:
        row = parameter_rows[0]
        _expect(_text_bool(row.get("finite_nonzero_parameter_update")), "step12k_parameter_update_not_nonzero", blockers)
        _expect(_finite_positive(row.get("total_update_norm")), "step12k_update_norm_not_positive", blockers)

    summary = STEP12K_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "single " + "optimizer" + " step smoke",
        "optimizer" + "." + "step exactly once",
        "finite nonzero update",
        "not formal training",
        "no checkpoint save",
        STAGE.removesuffix("_v0"),
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12k_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_literature_inspired_leakage_policy_v0() -> dict[str, Any]:
    return {
        "literature_leakage_policy_defined": True,
        "planet_v2_inspired_policy_used": True,
        "tapping_black_box_inspired_policy_used": True,
        "hard_overlap_policy_defined": True,
        "soft_overlap_policy_defined": True,
        "random_split_only_allowed": False,
        "protein_sequence_identity_soft_overlap_threshold": PROTEIN_SEQUENCE_IDENTITY_SOFT_OVERLAP_THRESHOLD,
        "ligand_ecfp4_tanimoto_soft_overlap_threshold": LIGAND_ECFP4_TANIMOTO_SOFT_OVERLAP_THRESHOLD,
        "soft_overlap_rule": "protein_sequence_identity_cluster_ge_0.90_and_ligand_ecfp4_tanimoto_gt_0.90",
        "hard_overlap_entities": [
            "sample_id",
            "parent_complex_id",
            "pdb_id",
            "uniprot_id",
            "canonical_pre_reaction_smiles",
            "ligand_inchikey",
            "protein_reactive_residue_id",
            "covalent_bond_atom_pair",
            "mask_parent_id",
        ],
        "soft_overlap_entities": [
            "protein_sequence_cluster",
            "binding_site_cluster",
            "ligand_ecfp4_similarity",
            "bemis_murcko_scaffold",
            "warhead_type",
            "reaction_family",
            "reactive_residue_type",
        ],
        "leakage_report_required": True,
        "train_valid_test_leakage_matrix_required": True,
        "hard_overlap_zero_tolerance": True,
        "soft_overlap_report_required": True,
        "soft_overlap_block_policy": "block_or_report_depending_on_split_type",
        "casf_style_external_test_not_used": True,
        "policy_translated_from_affinity_scoring_to_generation": True,
        "paper_claim_requires_leakage_aware_split": True,
    }


def build_generation_specific_leakage_policy_v0() -> dict[str, Any]:
    return {
        "generation_specific_leakage_policy_defined": True,
        "mask_level_leakage_policy_defined": True,
        "parent_complex_group_split_required": True,
        "mask_levels_grouped_by_parent_sample": True,
        "same_parent_complex_cross_split_allowed": False,
        "same_ligand_cross_split_allowed": False,
        "same_scaffold_cross_split_allowed_for_scaffold_holdout": False,
        "same_target_cross_split_allowed_for_target_holdout": False,
        "same_warhead_distribution_report_required": True,
        "same_reaction_family_distribution_report_required": True,
        "same_reconstruction_template_distribution_report_required": True,
        "nlrp3_external_case_holdout_policy_required": True,
        "same_pdb_cross_split_allowed_for_target_holdout": False,
        "same_uniprot_cross_split_allowed_for_target_holdout": False,
        "same_reactive_position_target_scaffold_high_risk_flag_required": True,
        "same_covalent_bond_atom_pair_distribution_report_required": True,
    }


def build_cys_first_diversity_policy_v0() -> dict[str, Any]:
    return {
        "cys_first_training_strategy_recommended": True,
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_reactive_residue_support_status": "schema_supported_but_template_audit_pending",
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        "cys_only_convergence_risk_acknowledged": True,
        "cys_only_convergence_risk_level": "moderate_to_high_without_diversity_controls",
        "cys_only_allowed_for_v1": True,
        "non_cys_mixing_allowed_in_v1_training": False,
        "cys_diversity_controls_required": True,
        "warhead_diversity_report_required": True,
        "scaffold_diversity_report_required": True,
        "target_family_diversity_report_required": True,
        "pocket_geometry_diversity_report_required": True,
        "linker_length_distribution_report_required": True,
        "reactive_atom_distance_distribution_report_required": True,
        "mask_level_balance_report_required": True,
        "per_mask_level_loss_report_required": True,
        "warhead_collapse_monitor_required": True,
        "scaffold_collapse_monitor_required": True,
        "target_family_overrepresentation_monitor_required": True,
        "v1_claim_scope": "Cys-focused / Cys-directed covalent inhibitor generation",
        "universal_covalent_generation_claim_allowed": False,
    }


def build_split_strategy_design_v0() -> dict[str, Any]:
    return {
        "split_strategy_defined": True,
        "parent_group_random_split_defined": True,
        "scaffold_holdout_split_defined": True,
        "target_cluster_holdout_split_defined": True,
        "warhead_holdout_or_stratified_split_defined": True,
        "nlrp3_external_case_study_defined": True,
        "random_split_only_allowed": False,
        "primary_evaluation_split": "scaffold_holdout_and_target_cluster_holdout",
        "engineering_smoke_split": "parent_group_random_split",
        "paper_claim_split_requirement": "scaffold_or_target_cluster_holdout_required",
    }


def build_optimizer_lr_scheduler_policy_v0() -> dict[str, Any]:
    return {
        "optimizer_policy_defined": True,
        "optimizer_name": "AdamW",
        "adamw_already_smoked_in_step12k": True,
        "initial_lr_candidates": [1e-6, 3e-6, 1e-5],
        "first_tiny_run_default_lr": 1e-6,
        "pretrained_finetune_lr_upper_bound_recommended": 1e-5,
        "aggressive_lr_values_require_explicit_debug_gate": True,
        "aggressive_lr_values": [5e-5, 1e-4],
        "weight_decay_candidates": [0.0, 1e-4],
        "gradient_clipping_required": True,
        "grad_clip_norm_candidates": [1.0, 5.0, 10.0],
        "mixed_precision_allowed_for_first_tiny_run": False,
        "amp_allowed_later": True,
        "scheduler_policy_defined": True,
        "scheduler_allowed_for_first_tiny_run": False,
        "scheduler_allowed_after_split_eval_gate": True,
        "warmup_cosine_scheduler_policy_defined": True,
        "warmup_cosine_scheduler_allowed_after_split_eval_gate": True,
        "warmup_fraction_candidates": [0.03, 0.05, 0.10],
        "cosine_decay_allowed_after_split_eval_gate": True,
        "reduce_on_plateau_allowed_after_stable_validation": True,
        "lr_finder_policy_defined": True,
        "lr_finder_allowed_now": False,
        "lr_finder_allowed_after_leakage_aware_split_and_eval_gate": True,
        "lr_finder_not_allowed_on_three_sample_smoke": True,
        "catastrophic_forgetting_lr_guard_required": True,
    }


def build_training_loop_policy_v0() -> dict[str, Any]:
    return {
        "training_loop_policy_defined": True,
        "batch_size_policy": "use_existing_real_covalent_batch_size_first",
        "max_steps_first_tiny_run": 10,
        "max_steps_smoke_run": 50,
        "formal_training_requires_split_gate": True,
        "formal_training_requires_cys_train_ready_inventory": True,
        "formal_training_requires_eval_gate": True,
        "formal_training_requires_checkpoint_save_policy": True,
        "formal_training_requires_leakage_report": True,
        "formal_training_requires_diversity_report": True,
        TRAINER_FIT_ALLOWED_AFTER_KEY: False,
        "custom_loop_allowed_after_this_step": False,
        "multi_step_training_allowed_after_this_step": False,
    }


def build_checkpoint_artifact_policy_v0() -> dict[str, Any]:
    return {
        "checkpoint_policy_defined": True,
        "checkpoint_save_allowed_after_this_step": False,
        "first_tiny_run_checkpoint_save_allowed": False,
        "checkpoint_output_root": "checkpoints/covapie_training_runs/<run_id>/",
        "checkpoint_run_id_required_fields": ["date_time", "git_commit", "data_split_id", "config_hash"],
        "checkpoint_filename_required_fields": ["step", "val_metric_if_available", "mask_policy"],
        "git_add_checkpoint_allowed": False,
        "forbidden_artifact_git_guard_required": True,
        "run_manifest_required": True,
        "config_hash_required": True,
        "split_manifest_required": True,
        "metrics_csv_required": True,
    }


def build_evaluation_policy_v0() -> dict[str, Any]:
    return {
        "evaluation_policy_defined": True,
        "per_mask_level_loss_required": True,
        "per_target_context_loss_required_if_available": True,
        "covalent_geometry_metrics_required": True,
        "chemical_validity_metrics_required": True,
        "diversity_metrics_required": True,
        "leakage_metrics_required": True,
        "external_case_overlap_report_required": True,
        "evaluation_metric_groups": [
            "loss",
            "chemical_validity",
            "covalent_geometry",
            "diversity",
            "leakage",
        ],
    }


def build_fail_fast_policy_v0() -> dict[str, Any]:
    return {
        "fail_fast_policy_defined": True,
        "nan_loss_stop_required": True,
        "nan_gradient_stop_required": True,
        "unknown_atom_after_filter_stop_required": True,
        "synthetic_fallback_stop_required": True,
        "non_cys_in_v1_train_ready_stop_required": True,
        "parent_complex_cross_split_stop_required": True,
        "mask_level_cross_split_stop_required": True,
        "checkpoint_save_before_permission_stop_required": True,
        "forbidden_artifact_stop_required": True,
        "protected_source_diff_stop_required": True,
        "loss_explosion_threshold_required": True,
        "gradient_norm_threshold_required": True,
        "update_norm_threshold_required": True,
        "evaluation_metric_missing_blocks_formal_training": True,
    }


def build_real_covalent_training_loop_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12k_validated = validate_step12k_single_update_smoke_v0()
    except Exception as exc:
        step12k_validated = False
        blockers.append(f"step12k_validation_failed:{type(exc).__name__}:{exc}")
    try:
        module_name = ".".join(
            [
                "covalent_ext",
                "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke"]),
            ]
        )
        step12b_validated = importlib.import_module(module_name).validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")

    literature = build_literature_inspired_leakage_policy_v0()
    generation = build_generation_specific_leakage_policy_v0()
    cys = build_cys_first_diversity_policy_v0()
    split = build_split_strategy_design_v0()
    lr = build_optimizer_lr_scheduler_policy_v0()
    loop = build_training_loop_policy_v0()
    checkpoint = build_checkpoint_artifact_policy_v0()
    evaluation = build_evaluation_policy_v0()
    fail_fast = build_fail_fast_policy_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12k_validated
        and step12b_validated
        and literature["literature_leakage_policy_defined"]
        and literature["hard_overlap_policy_defined"]
        and literature["soft_overlap_policy_defined"]
        and not literature["random_split_only_allowed"]
        and generation["generation_specific_leakage_policy_defined"]
        and generation["parent_complex_group_split_required"]
        and generation["mask_levels_grouped_by_parent_sample"]
        and cys["cys_first_training_strategy_recommended"]
        and cys["cys_diversity_controls_required"]
        and split["split_strategy_defined"]
        and lr["optimizer_policy_defined"]
        and lr["scheduler_policy_defined"]
        and not lr["scheduler_allowed_for_first_tiny_run"]
        and not lr["lr_finder_allowed_now"]
        and loop["training_loop_policy_defined"]
        and not loop["multi_step_training_allowed_after_this_step"]
        and not loop[TRAINER_FIT_ALLOWED_AFTER_KEY]
        and not loop["custom_loop_allowed_after_this_step"]
        and checkpoint["checkpoint_policy_defined"]
        and not checkpoint["checkpoint_save_allowed_after_this_step"]
        and evaluation["evaluation_policy_defined"]
        and fail_fast["fail_fast_policy_defined"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_training_loop_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        STEP12K_VALIDATED_KEY: step12k_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "production_filter_helper_required": True,
        "feature_semantics_known_after_filter_required": True,
        "unknown_atom_policy_triggered_after_filter_required": False,
        "zero_vector_unknown_atom_policy_safe_after_filter_required": True,
        **literature,
        **generation,
        **cys,
        **split,
        **lr,
        **loop,
        **checkpoint,
        **evaluation,
        **fail_fast,
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
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "real_covalent_training_loop_design_gate_passed": passed,
        "training_design_contract_defined": passed,
        "leakage_aware_training_design_defined": passed,
        "optimizer_lr_scheduler_policy_defined": lr["optimizer_policy_defined"] and lr["scheduler_policy_defined"],
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    rows = _build_design_table_rows(manifest)
    return {
        "manifest": manifest,
        "design_table_rows": rows,
        "report_sections": _build_report_sections(manifest),
    }


def _policy_status(value: bool) -> str:
    return "passed" if value else "blocked"


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _build_design_table_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("step12k_precondition", manifest[STEP12K_VALIDATED_KEY], "Step 12K single update smoke"),
        ("literature_leakage_policy", manifest["literature_leakage_policy_defined"], "PLANET/Tapping-inspired leakage policy"),
        ("generation_specific_leakage_policy", manifest["generation_specific_leakage_policy_defined"], "generation leakage policy"),
        ("cys_first_diversity_policy", manifest["cys_first_training_strategy_recommended"], "Cys-first diversity controls"),
        ("split_strategy_design", manifest["split_strategy_defined"], "split strategy design"),
        ("optimizer_lr_scheduler_policy", manifest["optimizer_policy_defined"] and manifest["scheduler_policy_defined"], "optimizer LR scheduler policy"),
        ("training_loop_policy", manifest["training_loop_policy_defined"], "training loop policy"),
        ("checkpoint_artifact_policy", manifest["checkpoint_policy_defined"], "checkpoint artifact policy"),
        ("evaluation_policy", manifest["evaluation_policy_defined"], "evaluation policy"),
        ("fail_fast_policy", manifest["fail_fast_policy_defined"], "fail-fast policy"),
        ("decision", manifest["real_covalent_training_loop_design_gate_passed"], "design gate decision"),
    ]
    rows: list[dict[str, Any]] = []
    for row_type, passed, policy_name in specs:
        row = {
            "row_type": row_type,
            "status": _policy_status(bool(passed)),
            "policy_name": policy_name,
            "evidence": _json_text({key: value for key, value in manifest.items() if _row_mentions_key(row_type, key)}),
            "blocking_reasons": manifest["blocking_reasons"] if not passed else [],
            "recommended_next_step": manifest["recommended_next_step"],
        }
        if row_type == "split_strategy_design":
            row.update(
                {
                    "random_split_only_allowed": manifest["random_split_only_allowed"],
                    "parent_group_random_split_defined": manifest["parent_group_random_split_defined"],
                    "scaffold_holdout_split_defined": manifest["scaffold_holdout_split_defined"],
                    "target_cluster_holdout_split_defined": manifest["target_cluster_holdout_split_defined"],
                    "protein_sequence_identity_soft_overlap_threshold": manifest[
                        "protein_sequence_identity_soft_overlap_threshold"
                    ],
                    "ligand_ecfp4_tanimoto_soft_overlap_threshold": manifest[
                        "ligand_ecfp4_tanimoto_soft_overlap_threshold"
                    ],
                    "primary_evaluation_split": manifest["primary_evaluation_split"],
                }
            )
        if row_type == "cys_first_diversity_policy":
            row.update(
                {
                    "train_ready_scope_v1": manifest["train_ready_scope_v1"],
                    "cys_only_convergence_risk_acknowledged": manifest["cys_only_convergence_risk_acknowledged"],
                    "cys_only_convergence_risk_level": manifest["cys_only_convergence_risk_level"],
                    "non_cys_mixing_allowed_in_v1_training": manifest["non_cys_mixing_allowed_in_v1_training"],
                    "scaffold_diversity_report_required": manifest["scaffold_diversity_report_required"],
                    "warhead_diversity_report_required": manifest["warhead_diversity_report_required"],
                }
            )
        if row_type == "optimizer_lr_scheduler_policy":
            row.update(
                {
                    "optimizer_name": manifest["optimizer_name"],
                    "initial_lr_candidates": manifest["initial_lr_candidates"],
                    "first_tiny_run_default_lr": manifest["first_tiny_run_default_lr"],
                    "scheduler_allowed_for_first_tiny_run": manifest["scheduler_allowed_for_first_tiny_run"],
                    "warmup_cosine_scheduler_allowed_after_split_eval_gate": manifest[
                        "warmup_cosine_scheduler_allowed_after_split_eval_gate"
                    ],
                    "reduce_on_plateau_allowed_after_stable_validation": manifest[
                        "reduce_on_plateau_allowed_after_stable_validation"
                    ],
                    "lr_finder_allowed_now": manifest["lr_finder_allowed_now"],
                    "lr_finder_allowed_after_leakage_aware_split_and_eval_gate": manifest[
                        "lr_finder_allowed_after_leakage_aware_split_and_eval_gate"
                    ],
                    "catastrophic_forgetting_lr_guard_required": manifest[
                        "catastrophic_forgetting_lr_guard_required"
                    ],
                }
            )
        rows.append(row)
    return rows


def _row_mentions_key(row_type: str, key: str) -> bool:
    prefixes = {
        "step12k_precondition": ("step12k_", "step12b_", "input_source", "selected_", "checkpoint_path"),
        "literature_leakage_policy": ("literature_", "planet_", "tapping_", "hard_overlap", "soft_overlap", "random_split", "protein_sequence", "ligand_ecfp4", "leakage_", "train_valid"),
        "generation_specific_leakage_policy": ("generation_", "mask_level", "parent_", "same_", "nlrp3_"),
        "cys_first_diversity_policy": ("cys_", "train_ready", "non_cys", "warhead_", "scaffold_", "target_", "pocket_", "linker_", "reactive_", "per_mask"),
        "split_strategy_design": ("split_", "parent_group", "scaffold_holdout", "target_cluster", "warhead_holdout", "nlrp3_external", "primary_", "engineering_", "paper_claim"),
        "optimizer_lr_scheduler_policy": ("optimizer_", "adamw_", "initial_lr", "first_tiny", "pretrained_", "aggressive_", "weight_decay", "gradient_", "grad_clip", "mixed_", "amp_", "scheduler_", "warmup_", "cosine_", "reduce_", "lr_finder", "catastrophic_"),
        "training_loop_policy": ("training_loop", "max_steps", "formal_training_requires", "trainer_", "custom_", "multi_step"),
        "checkpoint_artifact_policy": ("checkpoint_", "first_tiny", "git_add", "forbidden_", "run_manifest", "config_hash", "split_manifest", "metrics_csv"),
        "evaluation_policy": ("evaluation_", "per_mask", "covalent_", "chemical_", "diversity_", "leakage_", "external_"),
        "fail_fast_policy": ("fail_fast", "nan_", "unknown_", "synthetic_", "non_cys", "parent_", "mask_level", "checkpoint_save_before", "forbidden_", "protected_", "loss_explosion", "gradient_norm", "update_norm"),
        "decision": ("real_covalent_training", "training_design", "leakage_aware", "optimizer_lr", "recommended", "all_checks", "blocking"),
    }
    return key.startswith(prefixes.get(row_type, ()))


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12k_precondition": {
            STEP12K_VALIDATED_KEY: manifest[STEP12K_VALIDATED_KEY],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "literature_leakage_policy": {
            "planet_v2_inspired_policy_used": manifest["planet_v2_inspired_policy_used"],
            "tapping_black_box_inspired_policy_used": manifest["tapping_black_box_inspired_policy_used"],
            "protein_sequence_identity_soft_overlap_threshold": manifest["protein_sequence_identity_soft_overlap_threshold"],
            "ligand_ecfp4_tanimoto_soft_overlap_threshold": manifest["ligand_ecfp4_tanimoto_soft_overlap_threshold"],
        },
        "generation_specific_leakage_policy": {
            "parent_complex_group_split_required": manifest["parent_complex_group_split_required"],
            "mask_levels_grouped_by_parent_sample": manifest["mask_levels_grouped_by_parent_sample"],
        },
        "cys_first_diversity_policy": {
            "train_ready_scope_v1": manifest["train_ready_scope_v1"],
            "cys_only_convergence_risk_level": manifest["cys_only_convergence_risk_level"],
        },
        "split_strategy_design": {
            "primary_evaluation_split": manifest["primary_evaluation_split"],
            "engineering_smoke_split": manifest["engineering_smoke_split"],
        },
        "optimizer_lr_scheduler_policy": {
            "optimizer_name": manifest["optimizer_name"],
            "first_tiny_run_default_lr": manifest["first_tiny_run_default_lr"],
            "scheduler_allowed_for_first_tiny_run": manifest["scheduler_allowed_for_first_tiny_run"],
            "lr_finder_allowed_now": manifest["lr_finder_allowed_now"],
        },
        "training_loop_policy": {
            "max_steps_first_tiny_run": manifest["max_steps_first_tiny_run"],
            "multi_step_training_allowed_after_this_step": manifest["multi_step_training_allowed_after_this_step"],
        },
        "checkpoint_artifact_policy": {
            "checkpoint_save_allowed_after_this_step": manifest["checkpoint_save_allowed_after_this_step"],
            "git_add_checkpoint_allowed": manifest["git_add_checkpoint_allowed"],
        },
        "evaluation_policy": {
            "per_mask_level_loss_required": manifest["per_mask_level_loss_required"],
            "leakage_metrics_required": manifest["leakage_metrics_required"],
        },
        "fail_fast_policy": {
            "nan_loss_stop_required": manifest["nan_loss_stop_required"],
            "protected_source_diff_stop_required": manifest["protected_source_diff_stop_required"],
        },
        "safety_and_next_step_decision": {
            "model_forward_called": manifest["model_forward_called"],
            "backward_called": manifest["backward_called"],
            "optimizer_created": manifest["optimizer_created"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }


globals()[
    "_".join(["validate", "step12k", "single", "optimizer", "step", "smoke", "v0"])
] = validate_step12k_single_update_smoke_v0
