from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_leakage_aware_split_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_training_loop_design_gate_v0"

STEP12L_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_training_loop_design_gate_v0/"
    "real_covalent_training_loop_design_gate_manifest.json"
)
STEP12L_DESIGN_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_training_loop_design_gate_v0/"
    "real_covalent_training_loop_design_gate_table.csv"
)
STEP12L_SUMMARY_MD = Path("docs/real_covalent_training_loop_design_gate_v0_summary.md")

STEP12K_STAGE = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "v0"])
STEP12K_MANIFEST_JSON = Path("data/derived/covalent_small") / STEP12K_STAGE / f"{STEP12K_STAGE.removesuffix('_v0')}_manifest.json"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_leakage_aware_split_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_leakage_aware_split_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_leakage_aware_split_design_gate_manifest.json"
DESIGN_TABLE_CSV = OUTPUT_ROOT / "real_covalent_leakage_aware_split_design_gate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_leakage_aware_split_design_gate_v0_summary.md")

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
RECOMMENDED_NEXT_STEP = "real_covalent_split_metadata_inventory_gate"
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

STEP12L_STEP12K_VALIDATED_KEY = "_".join(["step12k", "single", "optimizer", "step", "smoke", "validated"])
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


def validate_step12l_training_loop_design_gate_v0() -> bool:
    if not STEP12L_MANIFEST_JSON.is_file() or not STEP12L_DESIGN_TABLE_CSV.is_file() or not STEP12L_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12L outputs are missing")
    manifest = _load_json(STEP12L_MANIFEST_JSON)
    rows = _read_csv(STEP12L_DESIGN_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": STEP12K_STAGE,
        STEP12L_STEP12K_VALIDATED_KEY: True,
        "step12b_mask_level_aware_validator_validated": True,
        "literature_leakage_policy_defined": True,
        "planet_v2_inspired_policy_used": True,
        "tapping_black_box_inspired_policy_used": True,
        "hard_overlap_policy_defined": True,
        "soft_overlap_policy_defined": True,
        "random_split_only_allowed": False,
        "protein_sequence_identity_soft_overlap_threshold": PROTEIN_SEQUENCE_IDENTITY_SOFT_OVERLAP_THRESHOLD,
        "ligand_ecfp4_tanimoto_soft_overlap_threshold": LIGAND_ECFP4_TANIMOTO_SOFT_OVERLAP_THRESHOLD,
        "leakage_report_required": True,
        "train_valid_test_leakage_matrix_required": True,
        "hard_overlap_zero_tolerance": True,
        "soft_overlap_report_required": True,
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
        "cys_first_training_strategy_recommended": True,
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_mixing_allowed_in_v1_training": False,
        "cys_only_convergence_risk_acknowledged": True,
        "cys_only_convergence_risk_level": "moderate_to_high_without_diversity_controls",
        "cys_diversity_controls_required": True,
        "scaffold_diversity_report_required": True,
        "warhead_diversity_report_required": True,
        "target_family_diversity_report_required": True,
        "pocket_geometry_diversity_report_required": True,
        "split_strategy_defined": True,
        "parent_group_random_split_defined": True,
        "scaffold_holdout_split_defined": True,
        "target_cluster_holdout_split_defined": True,
        "warhead_holdout_or_stratified_split_defined": True,
        "nlrp3_external_case_study_defined": True,
        "primary_evaluation_split": "scaffold_holdout_and_target_cluster_holdout",
        "engineering_smoke_split": "parent_group_random_split",
        "optimizer_lr_scheduler_policy_defined": True,
        "scheduler_allowed_for_first_tiny_run": False,
        "lr_finder_allowed_now": False,
        "training_loop_policy_defined": True,
        "formal_training_allowed": False,
        "multi_step_training_allowed_after_this_step": False,
        "checkpoint_save_allowed_after_this_step": False,
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
        "real_covalent_training_loop_design_gate_passed": True,
        "training_design_contract_defined": True,
        "leakage_aware_training_design_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.removesuffix("_v0"),
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12l_{key}_invalid:{manifest.get(key)!r}", blockers)
    row_types = [row.get("row_type") for row in rows]
    for required in [
        "literature_leakage_policy",
        "generation_specific_leakage_policy",
        "split_strategy_design",
        "training_loop_policy",
        "decision",
    ]:
        _expect(required in row_types, f"step12l_table_missing:{required}", blockers)
    summary = STEP12L_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "PLANET v2.0-style soft overlap",
        "protein sequence identity threshold 0.90",
        "ECFP4 Tanimoto threshold 0.90",
        "Tapping-on-the-Black-Box-style warning",
        "parent complex group split",
        "mask levels not cross split",
        "Cys-only convergence risk",
        "not training",
        STAGE.removesuffix("_v0"),
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12l_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def audit_current_sample_index_for_split_design_v0() -> dict[str, Any]:
    exists = SELECTED_REAL_SAMPLE_INDEX.is_file()
    rows = _read_csv(SELECTED_REAL_SAMPLE_INDEX) if exists else []
    sample_ids = [row.get("sample_id", "") for row in rows if row.get("sample_id")]
    observed_fields = sorted(rows[0].keys()) if rows else []
    metadata_schema = build_required_split_metadata_schema_v0()
    required_fields = metadata_schema["required_split_metadata_fields"]
    missing_fields = [field for field in required_fields if field not in observed_fields]
    count = len(rows)
    final_feasible = count >= 30
    return {
        "sample_index_exists": exists,
        "current_sample_index_inspected": exists,
        "current_sample_count": count,
        "sample_ids": sample_ids,
        "sample_index_observed_fields": observed_fields,
        "sample_index_missing_required_split_metadata_fields": missing_fields,
        "sample_index_missing_required_split_metadata_field_count": len(missing_fields),
        "current_dataset_is_small_smoke_set": count <= 10,
        "current_dataset_final_split_feasible": final_feasible,
        "current_dataset_final_split_blocking_reason": ""
        if final_feasible
        else "insufficient_sample_count_for_leakage_aware_train_valid_test_split",
        "actual_train_valid_test_split_created": False,
        "split_manifest_created": False,
        "engineering_smoke_split_design_allowed": True,
        "final_paper_split_allowed": False,
    }


def build_required_split_metadata_schema_v0() -> dict[str, Any]:
    sample_identity = [
        "sample_id",
        "parent_complex_id",
        "mask_parent_id",
        "mask_level",
        "source_dataset",
        "source_pdb_id",
    ]
    protein_identity = [
        "pdb_id",
        "chain_id",
        "uniprot_id",
        "protein_sequence",
        "protein_sequence_hash",
        "protein_sequence_cluster_0p90",
        "protein_family",
        "target_name",
        "binding_site_residue_set_hash",
        "local_pocket_signature",
    ]
    ligand_identity = [
        "canonical_pre_reaction_smiles",
        "ligand_inchikey",
        "ligand_inchikey_connectivity_layer",
        "ligand_ecfp4_fingerprint",
        "bemis_murcko_scaffold_smiles",
        "scaffold_id",
        "ligand_heavy_atom_count",
    ]
    covalent_identity = [
        "reactive_residue_type",
        "reactive_residue_id",
        "reactive_residue_chain",
        "ligand_reactive_atom_index",
        "protein_reactive_atom_name",
        "covalent_bond_atom_pair",
        "warhead_type",
        "reaction_family",
        "post_to_pre_reconstruction_template_id",
    ]
    geometry_diversity = [
        "ligand_reactive_atom_to_cys_sg_distance",
        "warhead_orientation_descriptor",
        "linker_length_bin",
        "pocket_geometry_bin",
        "target_context_atom_count",
        "target_mask_atom_count",
    ]
    fields = sample_identity + protein_identity + ligand_identity + covalent_identity + geometry_diversity
    return {
        "required_split_metadata_schema_defined": True,
        "required_split_metadata_field_count": len(fields),
        "required_split_metadata_fields": fields,
        "required_sample_identity_fields": sample_identity,
        "required_protein_identity_fields": protein_identity,
        "required_ligand_identity_fields": ligand_identity,
        "required_covalent_identity_fields": covalent_identity,
        "required_geometry_diversity_fields": geometry_diversity,
        "metadata_inventory_required_before_split": True,
        "missing_metadata_should_block_final_split": True,
    }


def build_hard_overlap_split_policy_v0() -> dict[str, Any]:
    entities = [
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
    ]
    return {
        "hard_overlap_split_policy_defined": True,
        "hard_overlap_zero_tolerance": True,
        "hard_overlap_entities": entities,
        "same_parent_complex_cross_split_allowed": False,
        "same_mask_parent_cross_split_allowed": False,
        "same_sample_id_cross_split_allowed": False,
        "same_pdb_cross_split_allowed_for_target_holdout": False,
        "same_uniprot_cross_split_allowed_for_target_holdout": False,
        "same_ligand_inchikey_cross_split_allowed": False,
        "same_canonical_smiles_cross_split_allowed": False,
        "same_covalent_bond_atom_pair_requires_distribution_report": True,
        "hard_overlap_violation_blocks_split": True,
        "hard_overlap_violation_blocks_training": True,
        "mask_levels_grouped_by_parent_sample": True,
        "canonical_mask_levels_grouped": CANONICAL_MASK_LEVELS,
    }


def build_soft_overlap_split_policy_v0() -> dict[str, Any]:
    return {
        "soft_overlap_split_policy_defined": True,
        "protein_sequence_identity_soft_overlap_threshold": PROTEIN_SEQUENCE_IDENTITY_SOFT_OVERLAP_THRESHOLD,
        "ligand_ecfp4_tanimoto_soft_overlap_threshold": LIGAND_ECFP4_TANIMOTO_SOFT_OVERLAP_THRESHOLD,
        "soft_overlap_rule": "protein_sequence_cluster_ge_0.90_and_ligand_ecfp4_tanimoto_gt_0.90",
        "protein_sequence_cluster_method_design": "CD-HIT_or_equivalent_offline_cluster_at_0.90",
        "ligand_similarity_method_design": "RDKit_ECFP4_radius2_Tanimoto",
        "binding_site_cluster_design_required": True,
        "bemis_murcko_scaffold_overlap_report_required": True,
        "warhead_overlap_report_required": True,
        "reaction_family_overlap_report_required": True,
        "protein_cluster_overlap_report_required": True,
        "ligand_ecfp4_overlap_report_required": True,
        "scaffold_overlap_report_required": True,
        "target_family_overlap_report_required": True,
        "soft_overlap_violation_blocks_primary_test_claim": True,
        "soft_overlap_violation_requires_limitation_note": True,
        "split_type_specific_soft_overlap_behavior_defined": True,
        "parent_group_random_split_soft_overlap_report_only": True,
        "scaffold_holdout_blocks_same_scaffold": True,
        "target_cluster_holdout_blocks_same_protein_cluster": True,
        "nlrp3_external_overlap_report_required": True,
    }


def build_train_valid_test_leakage_matrix_schema_v0() -> dict[str, Any]:
    pairs = ["train_vs_valid", "train_vs_test", "valid_vs_test"]
    columns = [
        "pair_name",
        "train_split_name",
        "eval_split_name",
        "hard_overlap_count",
        "hard_overlap_keys_triggered",
        "parent_complex_overlap_count",
        "mask_parent_overlap_count",
        "pdb_overlap_count",
        "uniprot_overlap_count",
        "ligand_inchikey_overlap_count",
        "canonical_smiles_overlap_count",
        "protein_cluster_0p90_overlap_count",
        "max_protein_sequence_identity",
        "ligand_ecfp4_tanimoto_max",
        "ligand_ecfp4_tanimoto_ge_0p90_pair_count",
        "bemis_murcko_scaffold_overlap_count",
        "warhead_type_overlap_count",
        "reaction_family_overlap_count",
        "reconstruction_template_overlap_count",
        "nlrp3_external_overlap_flag",
        "leakage_status",
        "claim_allowed",
        "blocking_reasons",
    ]
    return {
        "leakage_matrix_schema_defined": True,
        "leakage_matrix_pairs": pairs,
        "leakage_matrix_required_columns": columns,
        "leakage_matrix_required_before_training": True,
        "leakage_matrix_required_before_paper_claim": True,
        "train_valid_test_leakage_matrix_required": True,
    }


def build_split_design_outputs_v0() -> dict[str, Any]:
    return {
        "future_split_output_schema_defined": True,
        "future_split_outputs_required": [
            "split_manifest.json",
            "split_assignments.csv",
            "leakage_matrix.csv",
            "scaffold_holdout_report.csv",
            "target_cluster_holdout_report.csv",
            "warhead_distribution_report.csv",
            "reaction_family_distribution_report.csv",
            "cys_train_ready_inventory.csv",
            "nlrp3_external_overlap_report.csv",
        ],
        "future_split_manifest_required": True,
        "future_split_assignments_required": True,
        "future_leakage_matrix_required": True,
        "future_scaffold_holdout_report_required": True,
        "future_target_cluster_holdout_report_required": True,
        "future_warhead_distribution_report_required": True,
        "future_reaction_family_distribution_report_required": True,
        "future_cys_train_ready_inventory_required": True,
        "future_nlrp3_external_overlap_report_required": True,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
    }


def build_split_feasibility_decision_v0(
    sample_audit: dict[str, Any],
    metadata_schema: dict[str, Any],
    policies: dict[str, Any],
) -> dict[str, Any]:
    count = int(sample_audit["current_sample_count"])
    blockers: list[str] = []
    if count < 30:
        blockers.append("insufficient_sample_count_for_leakage_aware_train_valid_test_split")
    if sample_audit["sample_index_missing_required_split_metadata_field_count"] > 0:
        blockers.append("split_metadata_inventory_required")
    return {
        "split_feasibility_decision_defined": True,
        "current_dataset_final_split_feasible": count >= 30,
        "final_train_valid_test_split_allowed": False,
        "final_paper_claim_allowed": False,
        "engineering_smoke_split_design_allowed": True,
        "current_dataset_feasibility_label": "small_smoke_only" if count < 30 else "metadata_inventory_required",
        "split_feasibility_blocking_reasons": blockers,
        "metadata_inventory_required_before_split": metadata_schema["metadata_inventory_required_before_split"],
        "final_split_requires_metadata_inventory": True,
        "split_implementation_allowed_after_this_step": False,
        "hard_overlap_policy_required_for_future_split": policies["hard_overlap_split_policy_defined"],
        "soft_overlap_policy_required_for_future_split": policies["soft_overlap_split_policy_defined"],
        "leakage_matrix_required_for_future_split": True,
    }


def build_real_covalent_leakage_aware_split_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12l_validated = validate_step12l_training_loop_design_gate_v0()
    except Exception as exc:
        step12l_validated = False
        blockers.append(f"step12l_validation_failed:{type(exc).__name__}:{exc}")

    metadata_schema = build_required_split_metadata_schema_v0()
    sample_audit = audit_current_sample_index_for_split_design_v0()
    hard_policy = build_hard_overlap_split_policy_v0()
    soft_policy = build_soft_overlap_split_policy_v0()
    leakage_matrix = build_train_valid_test_leakage_matrix_schema_v0()
    future_outputs = build_split_design_outputs_v0()
    feasibility = build_split_feasibility_decision_v0(
        sample_audit=sample_audit,
        metadata_schema=metadata_schema,
        policies={**hard_policy, **soft_policy},
    )
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12l_validated
        and sample_audit["sample_index_exists"]
        and sample_audit["current_sample_index_inspected"]
        and metadata_schema["required_split_metadata_schema_defined"]
        and hard_policy["hard_overlap_split_policy_defined"]
        and soft_policy["soft_overlap_split_policy_defined"]
        and leakage_matrix["leakage_matrix_schema_defined"]
        and future_outputs["future_split_output_schema_defined"]
        and feasibility["split_feasibility_decision_defined"]
        and not future_outputs["actual_split_assignments_written"]
        and not future_outputs["actual_leakage_matrix_written"]
        and not future_outputs["final_split_created"]
        and not feasibility["final_train_valid_test_split_allowed"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_leakage_aware_split_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12l_training_loop_design_gate_validated": step12l_validated,
        "step12b_mask_level_aware_validator_validated": step12l_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        **sample_audit,
        **metadata_schema,
        **hard_policy,
        **soft_policy,
        **leakage_matrix,
        **future_outputs,
        **feasibility,
        "diversity_reports_required": True,
        "scaffold_diversity_report_required": True,
        "warhead_diversity_report_required": True,
        "target_family_diversity_report_required": True,
        "pocket_geometry_diversity_report_required": True,
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
        "real_covalent_leakage_aware_split_design_gate_passed": passed,
        "split_design_contract_defined": passed,
        "metadata_inventory_required_before_split": True,
        "final_train_valid_test_split_allowed": False,
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


def _status(value: bool) -> str:
    return "passed" if value else "blocked"


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _build_design_table_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("step12l_precondition", manifest["step12l_training_loop_design_gate_validated"], "Step 12L design gate"),
        ("sample_index_audit", manifest["current_sample_index_inspected"], "current sample index audit"),
        ("required_split_metadata_schema", manifest["required_split_metadata_schema_defined"], "required split metadata schema"),
        ("hard_overlap_split_policy", manifest["hard_overlap_split_policy_defined"], "hard overlap policy"),
        ("soft_overlap_split_policy", manifest["soft_overlap_split_policy_defined"], "soft overlap policy"),
        ("leakage_matrix_schema", manifest["leakage_matrix_schema_defined"], "train/valid/test leakage matrix schema"),
        ("future_split_output_schema", manifest["future_split_output_schema_defined"], "future split output schema"),
        ("split_feasibility_decision", manifest["split_feasibility_decision_defined"], "split feasibility decision"),
        (
            "safety_and_next_step_decision",
            manifest["real_covalent_leakage_aware_split_design_gate_passed"],
            "safety and next-step decision",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for row_type, passed, policy_name in specs:
        rows.append(
            {
                "row_type": row_type,
                "status": _status(bool(passed)),
                "policy_name": policy_name,
                "evidence": _json_text({key: value for key, value in manifest.items() if _row_mentions_key(row_type, key)}),
                "current_sample_count": manifest["current_sample_count"],
                "current_dataset_feasibility_label": manifest["current_dataset_feasibility_label"],
                "blocking_reasons": [] if passed else manifest["split_feasibility_blocking_reasons"],
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def _row_mentions_key(row_type: str, key: str) -> bool:
    prefixes = {
        "step12l_precondition": ("step12l_", "step12b_", "input_source", "selected_", "checkpoint_path"),
        "sample_index_audit": ("sample_", "current_", "actual_", "split_manifest", "engineering_", "final_paper"),
        "required_split_metadata_schema": ("required_", "metadata_", "missing_metadata"),
        "hard_overlap_split_policy": ("hard_overlap", "same_", "mask_levels", "canonical_mask", "parent_"),
        "soft_overlap_split_policy": ("soft_overlap", "protein_sequence", "ligand_ecfp4", "binding_", "bemis_", "warhead_", "reaction_", "protein_cluster", "scaffold_", "target_", "nlrp3_"),
        "leakage_matrix_schema": ("leakage_matrix", "train_valid_test"),
        "future_split_output_schema": ("future_", "actual_split", "actual_leakage", "final_split_created"),
        "split_feasibility_decision": ("split_feasibility", "final_", "engineering_", "current_dataset_feasibility", "metadata_inventory", "split_implementation"),
        "safety_and_next_step_decision": ("model_", "loss_", "backward", "optimizer", "training_", "trainer", "checkpoint_", "tensor_", "npz_", "real_covalent", "recommended", "all_checks", "blocking", "original_", "forbidden_"),
    }
    return key.startswith(prefixes.get(row_type, ()))


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12l_precondition": {
            "step12l_training_loop_design_gate_validated": manifest["step12l_training_loop_design_gate_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "sample_index_audit": {
            "current_sample_count": manifest["current_sample_count"],
            "sample_ids": manifest["sample_ids"],
            "current_dataset_final_split_feasible": manifest["current_dataset_final_split_feasible"],
        },
        "required_split_metadata_schema": {
            "required_split_metadata_field_count": manifest["required_split_metadata_field_count"],
            "metadata_inventory_required_before_split": manifest["metadata_inventory_required_before_split"],
        },
        "hard_overlap_split_policy": {
            "hard_overlap_zero_tolerance": manifest["hard_overlap_zero_tolerance"],
            "hard_overlap_entities": manifest["hard_overlap_entities"],
        },
        "soft_overlap_split_policy": {
            "soft_overlap_rule": manifest["soft_overlap_rule"],
            "protein_sequence_identity_soft_overlap_threshold": manifest["protein_sequence_identity_soft_overlap_threshold"],
            "ligand_ecfp4_tanimoto_soft_overlap_threshold": manifest["ligand_ecfp4_tanimoto_soft_overlap_threshold"],
        },
        "leakage_matrix_schema": {
            "leakage_matrix_pairs": manifest["leakage_matrix_pairs"],
            "leakage_matrix_required_before_training": manifest["leakage_matrix_required_before_training"],
        },
        "future_split_output_schema": {
            "future_split_outputs_required": manifest["future_split_outputs_required"],
            "final_split_created": manifest["final_split_created"],
        },
        "split_feasibility_decision": {
            "current_dataset_feasibility_label": manifest["current_dataset_feasibility_label"],
            "split_feasibility_blocking_reasons": manifest["split_feasibility_blocking_reasons"],
        },
        "safety_and_next_step_decision": {
            "formal_training_allowed": manifest["formal_training_allowed"],
            "real_covalent_leakage_aware_split_design_gate_passed": manifest[
                "real_covalent_leakage_aware_split_design_gate_passed"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
