from __future__ import annotations

import ast
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from covalent_ext.real_covalent_filtered_cuda_forward_backward_smoke import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    FILTERED_SINGLE_UPDATE_ALLOWED_KEY,
    FILTERED_SINGLE_UPDATE_NEXT_STEP,
    FILTER_POLICY_NAME,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    GRAD_TABLE_CSV,
    MANIFEST_JSON,
    NOT_OPTIMIZER_STEP_TEXT,
    OPTIMIZER_STEP_CALLED_KEY,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    TRAINER_FIT_CALLED_KEY,
    validate_cuda_readiness_v0,
    validate_step12b_validator_behavior_v0,
    validate_step12i_filtered_feature_semantics_audit_v0,
)

import check_real_covalent_filtered_cuda_forward_backward_smoke_v0 as script  # noqa: E402


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (REPORT_CSV.is_file() and MANIFEST_JSON.is_file() and GRAD_TABLE_CSV.is_file() and SUMMARY_MD.is_file()):
        code = script.run()
        assert code == (0 if torch.cuda.is_available() else 1)


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def _grad_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(GRAD_TABLE_CSV)


def _bool(value: str) -> bool:
    return str(value).lower() == "true"


def _json_value(value: str):
    return json.loads(value) if value else []


def _require_cuda_or_assert_clean_block(manifest: dict) -> None:
    if torch.cuda.is_available():
        return
    assert manifest["cuda_available"] is False
    assert manifest["real_covalent_filtered_cuda_forward_backward_smoke_passed"] is False
    assert manifest["recommended_next_step"] == "cuda_environment_fix"
    assert manifest["model_forward_called"] is False
    assert manifest["loss_compute_called"] is False
    assert manifest["backward_called"] is False
    pytest.skip("CUDA unavailable; clean block verified")


def test_step12i_and_step12b_preconditions_validate():
    assert validate_step12i_filtered_feature_semantics_audit_v0() is True
    assert validate_step12b_validator_behavior_v0() is True


def test_cuda_readiness_matches_manifest():
    readiness = validate_cuda_readiness_v0()
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert readiness["cuda_available"] is True
    assert readiness["requested_device"] == "cuda"
    assert readiness["resolved_device"].startswith("cuda")
    assert manifest["cuda_available"] is True
    assert manifest["requested_device"] == "cuda"
    assert manifest["resolved_device"].startswith("cuda")
    assert manifest["cuda_device_count"] > 0
    assert manifest["cuda_device_name"]


def test_manifest_precondition_filter_and_feature_semantics_contract():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest["step12i_filtered_feature_semantics_audit_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["filter_policy_name"] == FILTER_POLICY_NAME
    assert manifest["production_filter_helper_used"] is True
    assert manifest["production_adapter_modified"] is False
    assert manifest["original_data_modified"] is False
    assert manifest["checkpoint_ligand_feature_dim"] == 10
    assert manifest["checkpoint_pocket_feature_dim"] == 10
    assert manifest["checkpoint_10d_mapping_matches_project_mapping"] is True
    assert manifest["feature_semantics_known_after_filter"] is True
    assert manifest["unknown_atom_policy_triggered_after_filter"] is False
    assert manifest["zero_vector_unknown_atom_policy_safe_after_filter"] is True
    assert manifest["sample_count"] == 3
    assert manifest["sample_ids"]


def test_manifest_filtered_cuda_batches_and_mask_level_counts():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest["canonical_mask_levels"] == CANONICAL_MASK_LEVELS
    assert manifest["canonical_mask_level_count"] == 5
    assert manifest["attempted_mask_level_count"] == 5
    assert manifest["passed_mask_level_count"] == 5
    assert manifest["failed_mask_level_count"] == 0
    assert manifest["all_filtered_batches_constructed"] is True
    assert manifest["all_filtered_batches_on_cuda"] is True
    assert manifest["all_checkpoint_compatible_batches_constructed_after_filter"] is True
    assert manifest["all_ligand_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_pocket_one_hot_row_sums_valid_after_filter"] is True
    assert manifest["all_ligand_unknown_atom_count_zero_after_filter"] is True
    assert manifest["all_pocket_unknown_atom_count_zero_after_filter"] is True
    assert manifest["ligand_masks_unchanged_after_filter"] is True
    assert manifest["ligand_reactive_atom_region_preserved"] is True
    assert manifest["no_synthetic_fallback_used"] is True


def test_manifest_strict_load_cuda_forward_loss_and_backward():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["model_strict_loaded_once"] is True
    assert str(manifest["model_device"]).startswith("cuda")
    assert manifest["model_forward_called"] is True
    assert manifest["model_forward_call_count"] == 5
    assert manifest["all_level_forward_call_count_exactly_one"] is True
    assert manifest["loss_compute_called"] is True
    assert manifest["loss_compute_call_count"] == 5
    assert manifest["all_level_loss_compute_call_count_exactly_one"] is True
    assert manifest["selected_loss_key"] == "masked_loss_total_dry"
    assert manifest["all_losses_computed"] is True
    assert manifest["all_losses_finite"] is True
    assert manifest["all_losses_require_grad"] is True
    assert manifest["all_losses_on_cuda"] is True
    assert math.isfinite(float(manifest["min_selected_loss"]))
    assert math.isfinite(float(manifest["max_selected_loss"]))
    assert math.isfinite(float(manifest["mean_selected_loss"]))
    assert manifest["aggregate_loss_reduction"] == "mean"
    assert math.isfinite(float(manifest["aggregate_loss_value"]))
    assert manifest["aggregate_loss_finite"] is True
    assert manifest["aggregate_loss_requires_grad"] is True
    assert str(manifest["aggregate_loss_device"]).startswith("cuda")
    assert manifest["backward_called"] is True
    assert manifest["backward_call_count"] == 1
    assert manifest["backward_exactly_once"] is True
    assert manifest["backward_success"] is True


def test_manifest_gradient_summary_and_decision():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest["trainable_parameter_count"] > 0
    assert manifest["parameters_with_grad_count"] > 0
    assert manifest["parameters_with_nonzero_grad_count"] > 0
    assert manifest["finite_nonzero_gradients"] is True
    assert math.isfinite(float(manifest["total_grad_norm"])) and float(manifest["total_grad_norm"]) > 0
    assert math.isfinite(float(manifest["max_abs_grad"])) and float(manifest["max_abs_grad"]) > 0
    assert manifest["grad_nan_count"] == 0
    assert manifest["grad_inf_count"] == 0
    assert manifest["real_covalent_filtered_cuda_forward_backward_smoke_passed"] is True
    assert manifest["real_covalent_filtered_backward_contract_proven"] is True
    assert manifest[FILTERED_SINGLE_UPDATE_ALLOWED_KEY] is True
    assert manifest["recommended_next_step"] == FILTERED_SINGLE_UPDATE_NEXT_STEP


def test_manifest_safety_and_scope_boundary():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    for key in [
        "optimizer_created",
        OPTIMIZER_STEP_CALLED_KEY,
        "training_step_called",
        TRAINER_FIT_CALLED_KEY,
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
    assert manifest["cys_first_training_strategy_recommended"] is True
    assert manifest["train_ready_scope_v1"] == "cys_with_known_reconstruction_template_only"
    assert manifest["non_cys_data_bulk_cleaning_policy"] == "identify_classify_defer_until_template_gate"
    assert manifest["reaction_family_template_audit_required_before_broad_covalent_training"] is True
    assert manifest["ligand_reconstruction_template_gate_required"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_grad_table_rows_and_per_level_losses():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)
    rows = _grad_rows()
    mask_rows = [row for row in rows if row["row_type"] == "mask_level_filtered_cuda_forward_loss"]

    assert len(mask_rows) == 5
    assert [row["mask_level"] for row in mask_rows] == CANONICAL_MASK_LEVELS
    for row in mask_rows:
        expected_region = "context" if row["mask_level"] == "B3_scaffold_only" else "target"
        assert row["expected_reactive_atom_region"] == expected_region
        assert _bool(row["filtered_batch_constructed"])
        assert _bool(row["filtered_batch_on_cuda"])
        assert _bool(row["checkpoint_compatible_batch_constructed_after_filter"])
        assert row["ligand_feature_dim"] == "10"
        assert row["pocket_feature_dim"] == "10"
        assert _bool(row["ligand_one_hot_row_sums_valid_after_filter"])
        assert _bool(row["pocket_one_hot_row_sums_valid_after_filter"])
        assert row["ligand_unknown_atom_count_after_filter"] == "0"
        assert row["pocket_unknown_atom_count_after_filter"] == "0"
        assert _bool(row["ligand_masks_unchanged_after_filter"])
        assert _bool(row["ligand_reactive_atom_region_preserved"])
        assert _bool(row["no_synthetic_fallback_used"])
        assert _bool(row["production_filter_helper_used"])
        assert _bool(row["model_forward_called"])
        assert row["model_forward_call_count_for_level"] == "1"
        assert _bool(row["loss_compute_called"])
        assert row["loss_compute_call_count_for_level"] == "1"
        assert row["selected_loss_key"] == "masked_loss_total_dry"
        assert math.isfinite(float(row["selected_loss_value"]))
        assert _bool(row["selected_loss_finite"])
        assert _bool(row["selected_loss_requires_grad"])
        assert row["selected_loss_device"].startswith("cuda")
        assert set(_json_value(row["filtered_pocket_atom_numbers"])).issubset({12})
        assert row["status"] == "passed"


def test_report_manifest_grad_table_and_summary_written():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    report_rows = _read_csv(REPORT_CSV)
    summary = SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 9
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "CUDA forward/backward smoke" in summary
    assert "production filter helper" in summary
    assert "backward exactly once" in summary
    assert NOT_OPTIMIZER_STEP_TEXT in summary
    assert FILTERED_SINGLE_UPDATE_NEXT_STEP in summary


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


def test_ast_safety_for_step12j_files():
    files = [
        "src/covalent_ext/real_covalent_filtered_cuda_forward_backward_smoke.py",
        "scripts/check_real_covalent_filtered_cuda_forward_backward_smoke_v0.py",
        "tests/test_real_covalent_filtered_cuda_forward_backward_smoke_v0.py",
    ]
    backward_calls: list[tuple[str, int]] = []
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
                assert func.attr not in {"fit", "training_step"}
                if func.attr == "backward":
                    backward_calls.append((relative, node.lineno))
            if isinstance(func, ast.Name):
                assert func.id not in {"Adam", "AdamW", "SGD", "RMSprop"}
    assert len(backward_calls) == 1
    assert backward_calls[0][0] == "src/covalent_ext/real_covalent_filtered_cuda_forward_backward_smoke.py"
