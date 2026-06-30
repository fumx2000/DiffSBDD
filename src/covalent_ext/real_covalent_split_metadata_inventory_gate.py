from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_split_metadata_inventory_gate_v0"
PREVIOUS_STAGE = "real_covalent_leakage_aware_split_design_gate_v0"

STEP12M_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_leakage_aware_split_design_gate_v0/"
    "real_covalent_leakage_aware_split_design_gate_manifest.json"
)
STEP12M_DESIGN_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_leakage_aware_split_design_gate_v0/"
    "real_covalent_leakage_aware_split_design_gate_table.csv"
)
STEP12M_SUMMARY_MD = Path("docs/real_covalent_leakage_aware_split_design_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_split_metadata_inventory_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_split_metadata_inventory_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_split_metadata_inventory_gate_manifest.json"
INVENTORY_TABLE_CSV = OUTPUT_ROOT / "real_covalent_split_metadata_inventory_gate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_split_metadata_inventory_gate_v0_summary.md")

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
RECOMMENDED_NEXT_STEP = "real_covalent_split_metadata_enrichment_design_gate"

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


def validate_step12m_leakage_aware_split_design_gate_v0() -> bool:
    if not STEP12M_MANIFEST_JSON.is_file() or not STEP12M_DESIGN_TABLE_CSV.is_file() or not STEP12M_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12M outputs are missing")
    manifest = _load_json(STEP12M_MANIFEST_JSON)
    rows = _read_csv(STEP12M_DESIGN_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_training_loop_design_gate_v0",
        "step12l_training_loop_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "sample_index_exists": True,
        "current_sample_index_inspected": True,
        "current_sample_count": 3,
        "sample_ids": [
            "BTK_C481_6DI9_pre_reaction",
            "KRAS_G12C_5F2E_pre_reaction",
            "KRAS_G12C_6OIM_pre_reaction",
        ],
        "current_dataset_is_small_smoke_set": True,
        "current_dataset_final_split_feasible": False,
        "actual_train_valid_test_split_created": False,
        "split_manifest_created": False,
        "required_split_metadata_schema_defined": True,
        "required_split_metadata_field_count": 38,
        "metadata_inventory_required_before_split": True,
        "missing_metadata_should_block_final_split": True,
        "hard_overlap_split_policy_defined": True,
        "hard_overlap_zero_tolerance": True,
        "same_parent_complex_cross_split_allowed": False,
        "same_mask_parent_cross_split_allowed": False,
        "soft_overlap_split_policy_defined": True,
        "protein_sequence_identity_soft_overlap_threshold": 0.9,
        "ligand_ecfp4_tanimoto_soft_overlap_threshold": 0.9,
        "soft_overlap_rule": "protein_sequence_cluster_ge_0.90_and_ligand_ecfp4_tanimoto_gt_0.90",
        "leakage_matrix_schema_defined": True,
        "leakage_matrix_pairs": ["train_vs_valid", "train_vs_test", "valid_vs_test"],
        "leakage_matrix_required_before_training": True,
        "future_split_output_schema_defined": True,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "split_feasibility_decision_defined": True,
        "final_train_valid_test_split_allowed": False,
        "final_paper_claim_allowed": False,
        "engineering_smoke_split_design_allowed": True,
        "final_split_requires_metadata_inventory": True,
        "split_implementation_allowed_after_this_step": False,
        "formal_training_allowed": False,
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
        "real_covalent_leakage_aware_split_design_gate_passed": True,
        "split_design_contract_defined": True,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.removesuffix("_v0"),
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12m_{key}_invalid:{manifest.get(key)!r}", blockers)
    row_types = [row.get("row_type") for row in rows]
    for required in [
        "step12l_precondition",
        "sample_index_audit",
        "required_split_metadata_schema",
        "hard_overlap_split_policy",
        "soft_overlap_split_policy",
        "leakage_matrix_schema",
        "split_feasibility_decision",
        "safety_and_next_step_decision",
    ]:
        _expect(required in row_types, f"step12m_table_missing:{required}", blockers)
    summary = STEP12M_SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "leakage-aware split design gate",
        "not split implementation, not training",
        "engineering smoke set",
        "insufficient for final train/valid/test leakage-aware split",
        "Hard overlap zero tolerance",
        "A/B/B2/B3/C mask levels",
        "Protein sequence identity threshold: 0.90",
        "Ligand ECFP4 Tanimoto threshold: 0.90",
        "train/valid/test leakage matrix schema",
        "No formal split",
        "recommended_next_step: real_covalent_split_metadata_inventory_gate",
    ]
    for snippet in snippets:
        _expect(snippet in summary, f"step12m_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def inventory_current_sample_index_metadata_v0() -> dict[str, Any]:
    exists = SELECTED_REAL_SAMPLE_INDEX.is_file()
    rows = _read_csv(SELECTED_REAL_SAMPLE_INDEX) if exists else []
    observed_fields = list(rows[0].keys()) if rows else []
    sample_ids = [row.get("sample_id", "") for row in rows]
    nonempty_sample_ids = [sample_id for sample_id in sample_ids if sample_id]
    return {
        "sample_index_exists": exists,
        "current_sample_index_inspected": exists,
        "current_sample_count": len(rows),
        "sample_ids": sample_ids,
        "sample_index_observed_fields": observed_fields,
        "sample_index_observed_field_count": len(observed_fields),
        "sample_index_rows_have_unique_sample_id": len(set(nonempty_sample_ids)) == len(rows) and len(rows) > 0,
        "sample_index_rows_have_nonempty_sample_id": len(nonempty_sample_ids) == len(rows) and len(rows) > 0,
        "sample_index_has_npz_path_column": "npz_path" in observed_fields,
        "sample_index_has_npz_sha256_column": "npz_sha256" in observed_fields,
        "sample_index_has_materialization_status_column": "materialization_status" in observed_fields,
        "sample_index_npz_path_values_nonempty": all(bool(row.get("npz_path")) for row in rows) if rows else False,
        "sample_index_npz_sha256_values_nonempty": all(bool(row.get("npz_sha256")) for row in rows) if rows else False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "npz_file_existence_checked": False,
        "sample_index_modified": False,
        "enriched_sample_index_written": False,
    }


def load_required_metadata_schema_from_step12m_v0() -> dict[str, Any]:
    manifest = _load_json(STEP12M_MANIFEST_JSON)
    return {
        "required_split_metadata_schema_loaded_from_step12m": True,
        "required_split_metadata_field_count": manifest["required_split_metadata_field_count"],
        "required_split_metadata_fields": manifest["required_split_metadata_fields"],
        "required_sample_identity_fields": manifest["required_sample_identity_fields"],
        "required_protein_identity_fields": manifest["required_protein_identity_fields"],
        "required_ligand_identity_fields": manifest["required_ligand_identity_fields"],
        "required_covalent_identity_fields": manifest["required_covalent_identity_fields"],
        "required_geometry_diversity_fields": manifest["required_geometry_diversity_fields"],
        "metadata_inventory_required_before_split": manifest["metadata_inventory_required_before_split"],
        "missing_metadata_should_block_final_split": manifest["missing_metadata_should_block_final_split"],
    }


def build_required_metadata_coverage_inventory_v0(
    sample_index_audit: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    observed = set(sample_index_audit["sample_index_observed_fields"])
    required = schema["required_split_metadata_fields"]
    present = [field for field in required if field in observed]
    missing = [field for field in required if field not in observed]
    group_specs = {
        "sample_identity": schema["required_sample_identity_fields"],
        "protein_identity": schema["required_protein_identity_fields"],
        "ligand_identity": schema["required_ligand_identity_fields"],
        "covalent_identity": schema["required_covalent_identity_fields"],
        "geometry_diversity": schema["required_geometry_diversity_fields"],
    }
    group_fields: dict[str, list[str]] = {}
    for group, fields in group_specs.items():
        group_fields[f"{group}_present_fields"] = [field for field in fields if field in observed]
        group_fields[f"{group}_missing_fields"] = [field for field in fields if field not in observed]
    return {
        "present_required_metadata_fields": present,
        "missing_required_metadata_fields": missing,
        "present_required_metadata_field_count": len(present),
        "missing_required_metadata_field_count": len(missing),
        "metadata_completeness_ratio": len(present) / len(required) if required else 0.0,
        "metadata_completeness_ratio_text": f"{len(present)}/{len(required)}",
        "metadata_complete_for_final_split": False,
        "final_split_blocked_by_missing_metadata": True,
        **group_fields,
    }


def build_observed_nonrequired_field_inventory_v0(
    sample_index_audit: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    observed = sample_index_audit["sample_index_observed_fields"]
    required = set(schema["required_split_metadata_fields"])
    nonrequired = [field for field in observed if field not in required]
    count_fields = [
        field
        for field in [
            "ligand_atom_count",
            "ligand_bond_count",
            "protein_atom_count",
            "protein_residue_count",
            "scaffold_atom_count",
            "linker_atom_count",
            "warhead_atom_count",
        ]
        if field in observed
    ]
    path_hash_fields = [field for field in ["npz_path", "npz_sha256"] if field in observed]
    return {
        "observed_nonrequired_fields": nonrequired,
        "observed_nonrequired_field_count": len(nonrequired),
        "observed_count_fields": count_fields,
        "observed_path_hash_fields": path_hash_fields,
        "observed_existing_split_field_present": "split" in observed,
        "observed_source_sample_id_field_present": "source_sample_id" in observed,
        "observed_atom_count_fields_present": all(
            field in observed
            for field in ["ligand_atom_count", "protein_atom_count", "scaffold_atom_count", "linker_atom_count", "warhead_atom_count"]
        ),
        "observed_split_field_is_not_final_leakage_aware_split": True,
        "observed_split_field_must_not_be_used_for_paper_claim": True,
    }


def build_candidate_metadata_derivation_plan_v0() -> dict[str, Any]:
    return {
        "candidate_derivation_plan_defined": True,
        "direct_exact_fields_already_available": ["sample_id", "ligand_reactive_atom_index"],
        "candidate_fields_derivable_from_existing_sample_index": [
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
        "candidate_fields_derivable_from_sample_id": [
            "source_pdb_id",
            "pdb_id",
            "target_name",
            "reactive_residue_type",
            "reactive_residue_id",
            "protein_family",
        ],
        "candidate_fields_derivable_from_source_sample_id": ["parent_complex_id", "mask_parent_id"],
        "candidate_fields_derivable_from_dataset_context": ["source_dataset"],
        "fields_requiring_ligand_structure_processing": [
            "canonical_pre_reaction_smiles",
            "ligand_inchikey",
            "ligand_inchikey_connectivity_layer",
            "ligand_ecfp4_fingerprint",
            "bemis_murcko_scaffold_smiles",
            "scaffold_id",
            "ligand_heavy_atom_count",
            "warhead_type",
            "reaction_family",
            "post_to_pre_reconstruction_template_id",
        ],
        "fields_requiring_protein_structure_or_sequence_mapping": [
            "chain_id",
            "uniprot_id",
            "protein_sequence",
            "protein_sequence_hash",
            "protein_sequence_cluster_0p90",
            "binding_site_residue_set_hash",
            "local_pocket_signature",
            "protein_reactive_atom_name",
        ],
        "fields_requiring_coordinate_geometry_calculation": [
            "covalent_bond_atom_pair",
            "ligand_reactive_atom_to_cys_sg_distance",
            "warhead_orientation_descriptor",
            "linker_length_bin",
            "pocket_geometry_bin",
            "target_context_atom_count",
            "target_mask_atom_count",
        ],
        "candidate_derived_metadata_authoritative": False,
        "heuristic_parsing_allowed_for_inventory_only": True,
        "heuristic_parsing_not_allowed_for_final_split_without_validation": True,
        "source_sample_id_to_parent_complex_mapping_requires_validation": True,
        "sample_id_regex_parsing_requires_validation": True,
    }


def build_future_metadata_enrichment_output_plan_v0() -> dict[str, Any]:
    return {
        "future_metadata_enrichment_output_plan_defined": True,
        "future_metadata_enrichment_outputs_required": [
            "enriched_split_metadata_inventory.csv",
            "enriched_sample_index_for_split.csv",
            "metadata_derivation_manifest.json",
            "metadata_gap_report.csv",
            "candidate_id_mapping_report.csv",
            "ligand_identity_enrichment_report.csv",
            "protein_identity_enrichment_report.csv",
            "covalent_identity_enrichment_report.csv",
            "geometry_diversity_enrichment_report.csv",
        ],
        "future_enriched_sample_index_required": True,
        "future_metadata_gap_report_required": True,
        "future_candidate_id_mapping_report_required": True,
        "future_ligand_identity_enrichment_report_required": True,
        "future_protein_identity_enrichment_report_required": True,
        "future_covalent_identity_enrichment_report_required": True,
        "future_geometry_diversity_enrichment_report_required": True,
        "enriched_sample_index_written": False,
        "metadata_gap_report_written": False,
        "candidate_id_mapping_report_written": False,
    }


def build_metadata_inventory_feasibility_decision_v0(
    sample_index_audit: dict[str, Any],
    coverage: dict[str, Any],
    derivation_plan: dict[str, Any],
) -> dict[str, Any]:
    missing_count = coverage["missing_required_metadata_field_count"]
    gap_level = "severe" if missing_count >= 20 else "moderate" if missing_count else "none"
    return {
        "metadata_inventory_feasibility_decision_defined": True,
        "metadata_complete_for_final_split": False,
        "metadata_gap_level": gap_level,
        "metadata_enrichment_required": True,
        "metadata_enrichment_design_allowed": derivation_plan["candidate_derivation_plan_defined"],
        "dataset_size_still_blocks_final_split": sample_index_audit["current_sample_count"] < 30,
        "final_train_valid_test_split_allowed": False,
        "final_paper_claim_allowed": False,
        "split_implementation_allowed_after_this_step": False,
        "formal_training_allowed": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def build_real_covalent_split_metadata_inventory_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12m_validated = validate_step12m_leakage_aware_split_design_gate_v0()
    except Exception as exc:
        step12m_validated = False
        blockers.append(f"step12m_validation_failed:{type(exc).__name__}:{exc}")

    sample_index_audit = inventory_current_sample_index_metadata_v0()
    schema = load_required_metadata_schema_from_step12m_v0()
    coverage = build_required_metadata_coverage_inventory_v0(sample_index_audit, schema)
    observed_nonrequired = build_observed_nonrequired_field_inventory_v0(sample_index_audit, schema)
    derivation_plan = build_candidate_metadata_derivation_plan_v0()
    future_enrichment = build_future_metadata_enrichment_output_plan_v0()
    feasibility = build_metadata_inventory_feasibility_decision_v0(sample_index_audit, coverage, derivation_plan)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    passed = bool(
        step12m_validated
        and sample_index_audit["current_sample_index_inspected"]
        and schema["required_split_metadata_schema_loaded_from_step12m"]
        and coverage["present_required_metadata_field_count"] == 2
        and coverage["missing_required_metadata_field_count"] == 36
        and observed_nonrequired["observed_nonrequired_field_count"] > 0
        and derivation_plan["candidate_derivation_plan_defined"]
        and future_enrichment["future_metadata_enrichment_output_plan_defined"]
        and feasibility["metadata_inventory_feasibility_decision_defined"]
        and not sample_index_audit["enriched_sample_index_written"]
        and not future_enrichment["enriched_sample_index_written"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_split_metadata_inventory_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12m_leakage_aware_split_design_gate_validated": step12m_validated,
        "step12b_mask_level_aware_validator_validated": step12m_validated,
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
        **sample_index_audit,
        **schema,
        **coverage,
        **observed_nonrequired,
        **derivation_plan,
        **future_enrichment,
        **feasibility,
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
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "real_covalent_split_metadata_inventory_gate_passed": passed,
        "split_metadata_inventory_contract_defined": passed,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "inventory_table_rows": _build_inventory_table_rows(manifest),
        "report_sections": _build_report_sections(manifest),
    }


def _status(value: bool) -> str:
    return "passed" if value else "blocked"


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _availability_for_field(field: str, manifest: dict[str, Any]) -> tuple[str, str, str, bool]:
    if field in manifest["present_required_metadata_fields"]:
        return "present_exact", field, "none", True
    if field in manifest["candidate_fields_derivable_from_sample_id"]:
        return "candidate_derivable_requires_validation", "sample_id", "validate_sample_id_regex_and_mapping", False
    if field in manifest["candidate_fields_derivable_from_source_sample_id"]:
        return "candidate_derivable_requires_validation", "source_sample_id", "validate_parent_complex_mapping", False
    if field in manifest["candidate_fields_derivable_from_dataset_context"]:
        return "candidate_derivable_requires_validation", "input_source", "validate_source_dataset_mapping", False
    if field in manifest["fields_requiring_ligand_structure_processing"]:
        return "requires_ligand_structure_processing", "", "ligand_structure_or_rdkit_enrichment", False
    if field in manifest["fields_requiring_protein_structure_or_sequence_mapping"]:
        return "requires_protein_structure_or_sequence_mapping", "", "protein_structure_sequence_uniprot_or_cluster_enrichment", False
    if field in manifest["fields_requiring_coordinate_geometry_calculation"]:
        return "requires_coordinate_geometry_calculation", "", "coordinate_geometry_enrichment", False
    return "missing_required", "", "metadata_enrichment_required", False


def _field_group(field: str, manifest: dict[str, Any]) -> str:
    groups = [
        ("sample_identity", "required_sample_identity_fields"),
        ("protein_identity", "required_protein_identity_fields"),
        ("ligand_identity", "required_ligand_identity_fields"),
        ("covalent_identity", "required_covalent_identity_fields"),
        ("geometry_diversity", "required_geometry_diversity_fields"),
    ]
    for group, key in groups:
        if field in manifest[key]:
            return group
    return ""


def _build_inventory_table_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        _summary_row(
            "step12m_precondition",
            "precondition",
            "",
            manifest["step12m_leakage_aware_split_design_gate_validated"],
            {"step12m_validated": manifest["step12m_leakage_aware_split_design_gate_validated"]},
            manifest,
        ),
        _summary_row(
            "sample_index_audit",
            "sample_index",
            "",
            manifest["current_sample_index_inspected"],
            {
                "current_sample_count": manifest["current_sample_count"],
                "sample_index_observed_fields": manifest["sample_index_observed_fields"],
            },
            manifest,
        ),
    ]
    for field in manifest["required_split_metadata_fields"]:
        availability, candidate_source, enrichment_requirement, authoritative_now = _availability_for_field(field, manifest)
        observed = field in manifest["sample_index_observed_fields"]
        rows.append(
            {
                "row_type": "required_metadata_field_inventory",
                "field_group": _field_group(field, manifest),
                "field_name": field,
                "availability_status": availability,
                "observed_in_sample_index": observed,
                "candidate_source_field": candidate_source,
                "enrichment_requirement": enrichment_requirement,
                "authoritative_now": authoritative_now,
                "blocks_final_split": not authoritative_now,
                "current_sample_count": manifest["current_sample_count"],
                "evidence": _json_text({"observed_in_sample_index": observed, "availability_status": availability}),
                "status": "present" if authoritative_now else "missing",
                "blocking_reasons": [] if authoritative_now else ["metadata_missing_or_not_authoritative"],
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    for group in ["sample_identity", "protein_identity", "ligand_identity", "covalent_identity", "geometry_diversity"]:
        present_key = f"{group}_present_fields"
        missing_key = f"{group}_missing_fields"
        rows.append(
            {
                "row_type": "metadata_group_summary",
                "field_group": group,
                "field_name": "",
                "availability_status": "present_exact" if not manifest[missing_key] else "missing_required",
                "observed_in_sample_index": bool(manifest[present_key]),
                "candidate_source_field": "",
                "enrichment_requirement": "metadata_enrichment_required" if manifest[missing_key] else "none",
                "authoritative_now": not bool(manifest[missing_key]),
                "blocks_final_split": bool(manifest[missing_key]),
                "current_sample_count": manifest["current_sample_count"],
                "evidence": _json_text({"present": manifest[present_key], "missing": manifest[missing_key]}),
                "status": "complete" if not manifest[missing_key] else "incomplete",
                "blocking_reasons": ["missing_group_metadata"] if manifest[missing_key] else [],
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    rows.extend(
        [
            _summary_row(
                "observed_nonrequired_field_inventory",
                "observed_nonrequired",
                "",
                manifest["observed_nonrequired_field_count"] > 0,
                {"observed_nonrequired_fields": manifest["observed_nonrequired_fields"]},
                manifest,
                availability_status="observed_nonrequired",
            ),
            _summary_row(
                "candidate_derivation_plan",
                "candidate_derivation",
                "",
                manifest["candidate_derivation_plan_defined"],
                {
                    "candidate_fields_derivable_from_sample_id": manifest["candidate_fields_derivable_from_sample_id"],
                    "candidate_derived_metadata_authoritative": manifest["candidate_derived_metadata_authoritative"],
                },
                manifest,
                availability_status="candidate_derivable_requires_validation",
            ),
            _summary_row(
                "future_metadata_enrichment_output_plan",
                "future_enrichment",
                "",
                manifest["future_metadata_enrichment_output_plan_defined"],
                {"future_metadata_enrichment_outputs_required": manifest["future_metadata_enrichment_outputs_required"]},
                manifest,
            ),
            _summary_row(
                "metadata_inventory_feasibility_decision",
                "feasibility",
                "",
                manifest["metadata_inventory_feasibility_decision_defined"],
                {
                    "metadata_gap_level": manifest["metadata_gap_level"],
                    "metadata_enrichment_required": manifest["metadata_enrichment_required"],
                },
                manifest,
            ),
            _summary_row(
                "safety_and_next_step_decision",
                "safety",
                "",
                manifest["real_covalent_split_metadata_inventory_gate_passed"],
                {
                    "formal_training_allowed": manifest["formal_training_allowed"],
                    "recommended_next_step": manifest["recommended_next_step"],
                },
                manifest,
            ),
        ]
    )
    return rows


def _summary_row(
    row_type: str,
    field_group: str,
    field_name: str,
    passed: bool,
    evidence: dict[str, Any],
    manifest: dict[str, Any],
    availability_status: str = "",
) -> dict[str, Any]:
    return {
        "row_type": row_type,
        "field_group": field_group,
        "field_name": field_name,
        "availability_status": availability_status,
        "observed_in_sample_index": "",
        "candidate_source_field": "",
        "enrichment_requirement": "",
        "authoritative_now": "",
        "blocks_final_split": not passed,
        "current_sample_count": manifest["current_sample_count"],
        "evidence": _json_text(evidence),
        "status": _status(bool(passed)),
        "blocking_reasons": [] if passed else manifest["blocking_reasons"],
        "recommended_next_step": manifest["recommended_next_step"],
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12m_precondition": {
            "step12m_leakage_aware_split_design_gate_validated": manifest[
                "step12m_leakage_aware_split_design_gate_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "sample_index_audit": {
            "current_sample_count": manifest["current_sample_count"],
            "sample_index_observed_field_count": manifest["sample_index_observed_field_count"],
            "npz_contents_read": manifest["npz_contents_read"],
        },
        "required_metadata_schema_loaded": {
            "required_split_metadata_field_count": manifest["required_split_metadata_field_count"],
            "required_split_metadata_schema_loaded_from_step12m": manifest[
                "required_split_metadata_schema_loaded_from_step12m"
            ],
        },
        "exact_field_coverage_inventory": {
            "present_required_metadata_field_count": manifest["present_required_metadata_field_count"],
            "missing_required_metadata_field_count": manifest["missing_required_metadata_field_count"],
            "metadata_completeness_ratio_text": manifest["metadata_completeness_ratio_text"],
        },
        "metadata_group_summary": {
            "sample_identity_missing_fields": manifest["sample_identity_missing_fields"],
            "protein_identity_missing_fields": manifest["protein_identity_missing_fields"],
            "ligand_identity_missing_fields": manifest["ligand_identity_missing_fields"],
            "covalent_identity_missing_fields": manifest["covalent_identity_missing_fields"],
            "geometry_diversity_missing_fields": manifest["geometry_diversity_missing_fields"],
        },
        "observed_nonrequired_fields": {
            "observed_nonrequired_fields": manifest["observed_nonrequired_fields"],
            "observed_split_field_is_not_final_leakage_aware_split": manifest[
                "observed_split_field_is_not_final_leakage_aware_split"
            ],
        },
        "candidate_derivation_plan": {
            "candidate_derivation_plan_defined": manifest["candidate_derivation_plan_defined"],
            "candidate_derived_metadata_authoritative": manifest["candidate_derived_metadata_authoritative"],
        },
        "future_metadata_enrichment_output_plan": {
            "future_metadata_enrichment_output_plan_defined": manifest[
                "future_metadata_enrichment_output_plan_defined"
            ],
            "enriched_sample_index_written": manifest["enriched_sample_index_written"],
        },
        "metadata_inventory_feasibility_decision": {
            "metadata_gap_level": manifest["metadata_gap_level"],
            "metadata_enrichment_required": manifest["metadata_enrichment_required"],
            "final_train_valid_test_split_allowed": manifest["final_train_valid_test_split_allowed"],
        },
        "safety_and_next_step_decision": {
            "model_forward_called": manifest["model_forward_called"],
            "backward_called": manifest["backward_called"],
            "optimizer_created": manifest["optimizer_created"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }


def _close_enough(value: float, expected: float, tolerance: float = 1e-12) -> bool:
    return math.isfinite(value) and abs(value - expected) <= tolerance
