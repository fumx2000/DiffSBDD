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

from covalent_ext.real_covalent_filtered_feature_semantics_audit import (  # noqa: E402
    AUDIT_TABLE_CSV,
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX,
    FILTER_POLICY_NAME,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    audit_filtered_checkpoint_compatible_conversion_semantics_v0,
    audit_filtered_checkpoint_feature_contract_v0,
    audit_filtered_real_covalent_atom_vocabulary_v0,
    validate_step12b_validator_behavior_v0,
    validate_step12h_filter_gate_v0,
)

import check_real_covalent_filtered_feature_semantics_audit_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and AUDIT_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _audit_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(AUDIT_TABLE_CSV)


def _bool(value: str) -> bool:
    return str(value).lower() == "true"


def _json_value(value: str):
    return json.loads(value) if value else []


def test_step12h_and_step12b_preconditions_validate():
    assert validate_step12h_filter_gate_v0() is True
    assert validate_step12b_validator_behavior_v0() is True


def test_checkpoint_contract_and_project_mapping_are_confirmed():
    contract = audit_filtered_checkpoint_feature_contract_v0()

    assert contract["checkpoint_ligand_feature_dim"] == 10
    assert contract["checkpoint_pocket_feature_dim"] == 10
    assert contract["ligand_feature_dim_is_10"] is True
    assert contract["pocket_feature_dim_is_10"] is True
    assert contract["checkpoint_10d_feature_contract_detected"] is True
    assert contract["checkpoint_feature_semantics_source"] == "repo_dataset_info_or_config"
    assert contract["checkpoint_feature_semantics_directly_encoded"] is True
    assert contract["checkpoint_10d_mapping_matches_project_mapping"] is True
    assert CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX == {
        6: 0,
        7: 1,
        8: 2,
        16: 3,
        5: 4,
        35: 5,
        17: 6,
        15: 7,
        53: 8,
        9: 9,
    }


def test_filtered_real_atom_vocabulary_removes_mg_without_ligand_unknowns():
    vocab = audit_filtered_real_covalent_atom_vocabulary_v0()

    assert vocab["sample_count"] == 3
    assert vocab["sample_ids"]
    assert vocab["ligand_atom_count_total"] > 0
    assert vocab["pocket_atom_count_total_before_filter"] > vocab["pocket_atom_count_total_after_filter"]
    assert vocab["ligand_unknown_atom_count_before_filter"] == 0
    assert vocab["pocket_unknown_atom_count_before_filter"] == 2
    assert vocab["pocket_unknown_atom_numbers_before_filter"] == [12]
    assert vocab["filtered_pocket_atom_count"] == 2
    assert vocab["filtered_pocket_atom_numbers"] == [12]
    assert vocab["filtered_pocket_atom_symbols"] == ["Mg"]
    assert vocab["filtered_atoms_direct_ligand_contact_detected"] is False
    assert vocab["filtered_atoms_ligand_reactive_contact_detected"] is False
    assert vocab["ligand_unknown_atom_count_after_filter"] == 0
    assert vocab["pocket_unknown_atom_count_after_filter"] == 0
    assert vocab["all_ligand_atoms_in_checkpoint_10d_vocab_after_filter"] is True
    assert vocab["all_pocket_atoms_in_checkpoint_10d_vocab_after_filter"] is True
    assert vocab["unknown_atom_policy_triggered_after_filter"] is False
    assert vocab["zero_vector_unknown_atom_policy_safe_after_filter"] is True


def test_filtered_conversion_audits_all_five_mask_levels():
    conversion = audit_filtered_checkpoint_compatible_conversion_semantics_v0()

    assert conversion["audited_mask_level_count"] == 5
    assert conversion["passed_mask_level_count"] == 5
    assert conversion["failed_mask_level_count"] == 0
    assert conversion["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert conversion["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert conversion["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert conversion["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert conversion["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert conversion["ligand_masks_unchanged_after_filter"] is True
    assert conversion["ligand_reactive_atom_region_preserved"] is True
    assert conversion["no_synthetic_fallback_used"] is True
    assert conversion["production_filter_helper_used"] is True
    assert conversion["production_adapter_modified"] is False
    assert conversion["original_data_modified"] is False


def test_manifest_core_contract_and_filter_policy():
    manifest = _manifest()

    assert manifest["stage"] == "real_covalent_filtered_feature_semantics_audit_v0"
    assert manifest["previous_stage"] == "real_covalent_noncheckpoint_pocket_atom_filter_gate_v0"
    assert manifest["step12h_filter_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["checkpoint_ligand_feature_dim"] == 10
    assert manifest["checkpoint_pocket_feature_dim"] == 10
    assert manifest["checkpoint_feature_semantics_source"] == "repo_dataset_info_or_config"
    assert manifest["checkpoint_feature_semantics_directly_encoded"] is True
    assert manifest["checkpoint_10d_mapping_matches_project_mapping"] is True
    assert manifest["filter_policy_name"] == FILTER_POLICY_NAME
    assert manifest["production_filter_helper_used"] is True
    assert manifest["production_adapter_modified"] is False
    assert manifest["original_data_modified"] is False


def test_manifest_filtered_vocabulary_and_unknown_policy():
    manifest = _manifest()

    assert manifest["sample_count"] == 3
    assert manifest["sample_ids"]
    assert manifest["ligand_atom_count_total"] > 0
    assert manifest["pocket_atom_count_total_before_filter"] > manifest["pocket_atom_count_total_after_filter"]
    assert manifest["ligand_unknown_atom_count_before_filter"] == 0
    assert manifest["pocket_unknown_atom_count_before_filter"] == 2
    assert manifest["pocket_unknown_atom_numbers_before_filter"] == [12]
    assert manifest["filtered_pocket_atom_count"] == 2
    assert manifest["filtered_pocket_atom_numbers"] == [12]
    assert manifest["filtered_pocket_atom_symbols"] == ["Mg"]
    assert manifest["filtered_atoms_direct_ligand_contact_detected"] is False
    assert manifest["filtered_atoms_ligand_reactive_contact_detected"] is False
    assert manifest["ligand_unknown_atom_count_after_filter"] == 0
    assert manifest["pocket_unknown_atom_count_after_filter"] == 0
    assert manifest["all_ligand_atoms_in_checkpoint_10d_vocab_after_filter"] is True
    assert manifest["all_pocket_atoms_in_checkpoint_10d_vocab_after_filter"] is True
    assert manifest["unknown_atom_policy_triggered_after_filter"] is False
    assert manifest["zero_vector_unknown_atom_policy_safe_after_filter"] is True


def test_manifest_conversion_and_feature_semantics_hard_pass():
    manifest = _manifest()

    assert manifest["canonical_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["canonical_mask_level_count"] == 5
    assert manifest["audited_mask_level_count"] == 5
    assert manifest["passed_mask_level_count"] == 5
    assert manifest["failed_mask_level_count"] == 0
    assert manifest["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert manifest["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert manifest["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert manifest["ligand_masks_unchanged_after_filter"] is True
    assert manifest["ligand_reactive_atom_region_preserved"] is True
    assert manifest["no_synthetic_fallback_used"] is True
    assert manifest["feature_semantics_dimension_contract_passed_after_filter"] is True
    assert manifest["feature_semantics_mapping_confirmed"] is True
    assert manifest["feature_semantics_known_after_filter"] is True
    assert manifest["real_covalent_filtered_feature_semantics_audit_passed"] is True
    assert manifest["real_covalent_filtered_cuda_forward_backward_smoke_allowed"] is True
    assert manifest["real_covalent_single_optimizer_step_smoke_allowed"] is False
    assert manifest["recommended_next_step"] == "real_covalent_filtered_cuda_forward_backward_smoke"


def test_manifest_non_cys_scope_boundary_and_safety():
    manifest = _manifest()

    assert manifest["cys_first_training_strategy_recommended"] is True
    assert manifest["non_cys_reactive_residue_support_status"] == "schema_supported_but_template_audit_pending"
    assert manifest["reaction_family_template_audit_required_before_broad_covalent_training"] is True
    assert manifest["ligand_reconstruction_template_gate_required"] is True
    assert manifest["non_cys_data_bulk_cleaning_policy"] == "identify_classify_defer_until_template_gate"
    assert manifest["train_ready_scope_v1"] == "cys_with_known_reconstruction_template_only"
    for key in [
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
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


def test_audit_table_rows_and_mask_level_regions():
    rows = _audit_rows()
    row_types = [row["row_type"] for row in rows]
    conversion_rows = [row for row in rows if row["row_type"] == "mask_level_filtered_conversion"]

    assert "step12h_precondition" in row_types
    assert "checkpoint_feature_contract" in row_types
    assert "filtered_real_atom_vocabulary" in row_types
    assert "non_cys_training_scope_boundary" in row_types
    assert "decision" in row_types
    assert len(conversion_rows) == 5
    assert [row["mask_level"] for row in conversion_rows] == CANONICAL_MASK_LEVELS
    for row in conversion_rows:
        expected_region = "context" if row["mask_level"] == "B3_scaffold_only" else "target"
        assert row["expected_reactive_atom_region"] == expected_region
        assert _bool(row["checkpoint_compatible_batch_constructed_after_filter"])
        assert row["ligand_feature_dim"] == "10"
        assert row["pocket_feature_dim"] == "10"
        assert _bool(row["ligand_one_hot_row_sums_valid_after_filter"])
        assert _bool(row["pocket_one_hot_row_sums_valid_after_filter"])
        assert row["ligand_unknown_atom_count_after_filter"] == "0"
        assert row["pocket_unknown_atom_count_after_filter"] == "0"
        assert set(_json_value(row["filtered_pocket_atom_numbers"])).issubset({12})
        assert _bool(row["ligand_masks_unchanged_after_filter"])
        assert _bool(row["ligand_reactive_atom_region_preserved"])
        assert _bool(row["no_synthetic_fallback_used"])
        assert row["status"] == "passed"


def test_report_manifest_audit_table_and_summary_written():
    _ensure_outputs()

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 8
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "filtered feature semantics audit" in summary
    assert "production filter helper" in summary
    assert "pocket unknown count from 2 to 0" in summary
    assert "not optimizer step" in summary
    assert "Cys-first" in summary
    assert "recommended_next_step: real_covalent_filtered_cuda_forward_backward_smoke" in summary


def test_no_forbidden_artifacts_and_no_protected_source_modification():
    _ensure_outputs()

    forbidden = [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES]
    assert forbidden == []
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_safety_for_step12i_files():
    files = [
        "src/covalent_ext/real_covalent_filtered_feature_semantics_audit.py",
        "scripts/check_real_covalent_filtered_feature_semantics_audit_v0.py",
        "tests/test_real_covalent_filtered_feature_semantics_audit_v0.py",
    ]
    for relative in files:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner == "torch" and func.attr == "save")
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in {"backward", "fit", "training_step"}
            if isinstance(func, ast.Name):
                assert func.id not in {"Adam", "AdamW", "SGD", "RMSprop"}
