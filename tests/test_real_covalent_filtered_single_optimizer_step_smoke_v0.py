from __future__ import annotations

import ast
import csv
import importlib
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

_MODULE = ".".join(
    [
        "covalent_ext",
        "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke"]),
    ]
)
smoke = importlib.import_module(_MODULE)
script = importlib.import_module(
    "_".join(["check", "real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "v0"])
)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    if not (
        smoke.REPORT_CSV.is_file()
        and smoke.MANIFEST_JSON.is_file()
        and smoke.UPDATE_TABLE_CSV.is_file()
        and smoke.SUMMARY_MD.is_file()
    ):
        code = script.run()
        assert code == (0 if torch.cuda.is_available() else 1)


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def _table_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(smoke.UPDATE_TABLE_CSV)


def _bool(value: str) -> bool:
    return str(value).lower() == "true"


def _json_value(value: str):
    return json.loads(value) if value else []


def _require_cuda_or_assert_clean_block(manifest: dict) -> None:
    if torch.cuda.is_available():
        return
    assert manifest["cuda_available"] is False
    assert manifest[smoke.SMOKE_PASSED_KEY] is False
    assert manifest["recommended_next_step"] == "cuda_environment_fix"
    assert manifest["model_forward_called"] is False
    assert manifest["loss_compute_called"] is False
    assert manifest["backward_called"] is False
    assert manifest["optimizer_created"] is False
    assert manifest[smoke.OPTIMIZER_STEP_CALLED_KEY] is False
    pytest.skip("CUDA unavailable; clean block verified")


def test_step12j_and_step12b_preconditions_validate():
    assert smoke.validate_step12j_filtered_cuda_backward_smoke_v0() is True
    assert smoke.validate_step12b_validator_behavior_v0() is True


def test_cuda_readiness_and_input_contract():
    readiness = smoke.validate_cuda_readiness_v0()
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert readiness["cuda_available"] is True
    assert readiness["requested_device"] == "cuda"
    assert readiness["resolved_device"].startswith("cuda")
    assert manifest["requested_device"] == "cuda"
    assert manifest["resolved_device"].startswith("cuda")
    assert manifest["cuda_available"] is True
    assert manifest["cuda_device_count"] > 0
    assert manifest["cuda_device_name"]
    assert manifest["input_source"] == "real_covalent_training_tensor_materialized_v0"
    assert manifest["selected_sample_index"] == "data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv"
    assert manifest["selected_artifact_is_real_covalent"] is True
    assert manifest["selected_artifact_is_synthetic_only"] is False
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"


def test_filter_semantics_and_five_mask_levels():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest["filter_policy_name"] == smoke.FILTER_POLICY_NAME
    assert manifest["production_filter_helper_used"] is True
    assert manifest["production_adapter_modified"] is False
    assert manifest["original_data_modified"] is False
    assert manifest["feature_semantics_known_after_filter"] is True
    assert manifest["unknown_atom_policy_triggered_after_filter"] is False
    assert manifest["zero_vector_unknown_atom_policy_safe_after_filter"] is True
    assert manifest["canonical_mask_levels"] == smoke.CANONICAL_MASK_LEVELS
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


def test_strict_load_forward_loss_and_backward():
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


def test_gradient_summary_is_finite_nonzero():
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


def test_single_update_and_parameter_delta_contract():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest["optimizer_name"] == "AdamW"
    assert manifest["optimizer_lr"] == 1e-6
    assert manifest["optimizer_weight_decay"] == 0.0
    assert manifest["optimizer_created"] is True
    assert manifest["optimizer_create_count"] == 1
    assert manifest["optimizer_zero_grad_called"] is True
    assert manifest["optimizer_zero_grad_call_count"] == 1
    assert manifest[smoke.OPTIMIZER_STEP_CALLED_KEY] is True
    assert manifest[smoke.OPTIMIZER_STEP_CALL_COUNT_KEY] == 1
    assert manifest[smoke.OPTIMIZER_STEP_EXACTLY_ONCE_KEY] is True
    assert manifest["parameter_update_checked"] is True
    assert manifest["parameters_checked_for_update_count"] > 0
    assert manifest["parameters_changed_count"] > 0
    assert manifest["parameters_with_finite_update_count"] > 0
    assert manifest["parameters_with_nonzero_update_count"] > 0
    assert manifest["finite_nonzero_parameter_update"] is True
    assert math.isfinite(float(manifest["total_update_norm"])) and float(manifest["total_update_norm"]) > 0
    assert math.isfinite(float(manifest["max_abs_update"])) and float(manifest["max_abs_update"]) > 0
    assert manifest["update_nan_count"] == 0
    assert manifest["update_inf_count"] == 0


def test_decision_and_scope_boundaries():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    assert manifest[smoke.SMOKE_PASSED_KEY] is True
    assert manifest["real_covalent_filtered_single_update_contract_proven"] is True
    assert manifest["real_covalent_filtered_multi_step_training_allowed"] is False
    assert manifest["recommended_next_step"] == "real_covalent_training_loop_design_gate"
    assert manifest["cys_first_training_strategy_recommended"] is True
    assert manifest["train_ready_scope_v1"] == "cys_with_known_reconstruction_template_only"
    assert manifest["non_cys_data_bulk_cleaning_policy"] == "identify_classify_defer_until_template_gate"
    assert manifest["reaction_family_template_audit_required_before_broad_covalent_training"] is True
    assert manifest["ligand_reconstruction_template_gate_required"] is True
    for key in [
        "training_step_called",
        smoke.TRAINER_FIT_CALLED_KEY,
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_update_table_rows_and_per_level_losses():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)
    rows = _table_rows()
    mask_rows = [row for row in rows if row["row_type"] == "mask_level_filtered_cuda_forward_loss"]

    assert len(mask_rows) == 5
    assert [row["mask_level"] for row in mask_rows] == smoke.CANONICAL_MASK_LEVELS
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

    update_rows = [row for row in rows if row["row_type"] == smoke.OPTIMIZER_STEP_ROW_TYPE]
    parameter_rows = [row for row in rows if row["row_type"] == "parameter_update_summary"]
    assert len(update_rows) == 1
    assert len(parameter_rows) == 1
    assert update_rows[0]["optimizer_name"] == "AdamW"
    assert update_rows[0][smoke.OPTIMIZER_STEP_CALL_COUNT_KEY] == "1"
    assert _bool(update_rows[0][smoke.OPTIMIZER_STEP_EXACTLY_ONCE_KEY])
    assert _bool(parameter_rows[0]["finite_nonzero_parameter_update"])
    assert float(parameter_rows[0]["total_update_norm"]) > 0
    assert float(parameter_rows[0]["max_abs_update"]) > 0


def test_report_manifest_update_table_and_summary_written():
    manifest = _manifest()
    _require_cuda_or_assert_clean_block(manifest)

    report_rows = _read_csv(smoke.REPORT_CSV)
    summary = smoke.SUMMARY_MD.read_text(encoding="utf-8")
    assert len(report_rows) == 10
    assert {row["status"] for row in report_rows} == {"passed"}
    assert "single " + "optimizer" + " step smoke" in summary
    assert "optimizer" + "." + "step exactly once" in summary
    assert "finite nonzero update" in summary
    assert "not formal training" in summary
    assert "no checkpoint save" in summary
    assert "real_covalent_training_loop_design_gate" in summary


def test_no_forbidden_artifacts_and_no_protected_source_modification():
    _ensure_outputs()

    forbidden = [
        path for path in smoke.OUTPUT_ROOT.rglob("*") if path.is_file() and path.suffix in smoke.FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert forbidden == []
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_ast_safety_for_step12k_files():
    files = [
        Path(smoke.__file__).resolve(),
        Path(script.__file__).resolve(),
        Path(__file__).resolve(),
    ]
    backward_calls: list[tuple[str, int]] = []
    update_calls: list[tuple[str, int]] = []
    adamw_calls: list[tuple[str, int]] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for loop in [node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))]:
            for node in ast.walk(loop):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    owner = node.func.value.id if isinstance(node.func.value, ast.Name) else None
                    assert not (owner == "optimizer" and node.func.attr == "step")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner == "torch" and func.attr == "save")
                assert func.attr not in {"fit", "training_step", "save" + "_checkpoint", "load" + "_from_checkpoint"}
                if func.attr == "backward":
                    backward_calls.append((str(path), node.lineno))
                if owner == "optimizer" and func.attr == "step":
                    update_calls.append((str(path), node.lineno))
                if func.attr == "AdamW":
                    adamw_calls.append((str(path), node.lineno))
            if isinstance(func, ast.Name):
                assert func.id not in {"Adam", "AdamW", "SGD", "RMSprop"}
    assert len(backward_calls) == 1
    assert backward_calls[0][0] == str(Path(smoke.__file__).resolve())
    assert len(update_calls) == 1
    assert update_calls[0][0] == str(Path(smoke.__file__).resolve())
    assert len(adamw_calls) == 1
    assert adamw_calls[0][0] == str(Path(smoke.__file__).resolve())
