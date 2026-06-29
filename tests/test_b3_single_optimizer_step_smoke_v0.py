from __future__ import annotations

import ast
import csv
import functools
import json
import math
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

from covalent_ext.b3_single_optimizer_step_smoke import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    LEARNING_RATE,
    MANIFEST_JSON,
    MASK_LEVEL,
    OPTIMIZER_TYPE,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    UPDATE_TABLE_CSV,
    WEIGHT_DECAY,
    build_b3_single_optimizer_step_smoke_decision_v0,
    build_b3_single_optimizer_step_smoke_v0,
    run_b3_single_optimizer_step_smoke_v0,
    validate_step11q_outputs_v0,
)

import check_b3_single_optimizer_step_smoke_v0 as script  # noqa: E402


STEP_MODULE_STEM = "b3_single_optimizer_step_smoke"
B3_STEP_PASSED = "b3_single_optimizer_step_smoke_passed"
B3_STEP_DEBUG = "b3_single_optimizer_step_debug"


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_result_json_text() -> str:
    return json.dumps(build_b3_single_optimizer_step_smoke_v0(device="cpu"), default=str)


def _cached_result() -> dict:
    return json.loads(_cached_result_json_text())


def test_validate_step11q_outputs_success_and_gradient_table_contract():
    assert validate_step11q_outputs_v0() is True
    rows = _read_csv("data/derived/covalent_small/b3_backward_smoke_v0/b3_backward_smoke_gradient_table.csv")

    assert len(rows) == 1
    assert rows[0]["mask_level"] == MASK_LEVEL
    assert rows[0]["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(rows[0]["selected_loss_value"]))
    assert rows[0]["loss_requires_grad"] == "True"
    assert rows[0]["loss_finite"] == "True"
    assert rows[0]["backward_called"] == "True"
    assert rows[0]["backward_call_count"] == "1"
    assert rows[0]["backward_success"] == "True"
    assert rows[0]["finite_nonzero_grad_exists"] == "True"
    assert rows[0]["optimizer_created"] == "False"
    assert rows[0]["optimizer_step_called"] == "False"
    assert rows[0]["status"] == "passed"


def test_run_b3_single_optimizer_step_smoke_updates_parameters_once():
    result = run_b3_single_optimizer_step_smoke_v0(device="cpu")

    assert result["step11q_validated"] is True
    assert result["mask_level"] == MASK_LEVEL
    assert result["input_source"] == "synthetic_10d_shape_contract"
    assert result["requested_device"] == "cpu"
    assert result["resolved_device"] == "cpu"
    assert result["model_instantiated"] is True
    assert result["strict_load_success"] is True
    assert result["pretrained_weights_loaded"] is True
    assert result["pretrained_base_integration_proven"] is True
    assert result["model_forward_called"] is True
    assert result["loss_computed"] is True
    assert result["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(result["selected_loss_value"]))
    assert result["loss_requires_grad"] is True
    assert result["loss_finite"] is True
    assert result["optimizer_type"] == OPTIMIZER_TYPE
    assert result["learning_rate"] == LEARNING_RATE
    assert result["weight_decay"] == WEIGHT_DECAY
    assert result["optimizer_created"] is True
    assert result["backward_called"] is True
    assert result["backward_call_count"] == 1
    assert result["backward_success"] is True
    assert result["optimizer_step_called"] is True
    assert result["optimizer_step_call_count"] == 1
    assert result["finite_nonzero_grad_exists"] is True
    assert result["trainable_parameter_count"] > 0
    assert result["parameters_with_grad_count"] > 0
    assert math.isfinite(float(result["total_grad_norm"]))
    assert float(result["total_grad_norm"]) > 0.0
    assert math.isfinite(float(result["max_abs_grad"]))
    assert float(result["max_abs_grad"]) > 0.0
    assert result["grad_nan_count"] == 0
    assert result["grad_inf_count"] == 0
    assert result["sampled_parameter_count"] > 0
    assert math.isfinite(float(result["sampled_parameter_delta_l2"]))
    assert float(result["sampled_parameter_delta_l2"]) > 0.0
    assert math.isfinite(float(result["sampled_parameter_delta_max_abs"]))
    assert float(result["sampled_parameter_delta_max_abs"]) > 0.0
    assert result["updated_parameter_tensors_count"] > 0
    assert result["parameter_update_finite"] is True
    assert result["parameter_update_nonzero"] is True
    assert result["b3_target_atom_count"] == 3
    assert result["b3_context_atom_count"] == 4
    assert result["b3_reactive_atom_in_context"] is True
    assert result["b3_reactive_atom_in_target"] is False
    assert result["status"] == "passed"
    assert result["blocking_reasons"] == []


def test_decision_recommends_real_loader_gate_not_synthetic_loop_mainline():
    result = run_b3_single_optimizer_step_smoke_v0(device="cpu")
    decision = build_b3_single_optimizer_step_smoke_decision_v0(result)
    blocked = dict(result, status="blocked", parameter_update_nonzero=False)
    blocked_decision = build_b3_single_optimizer_step_smoke_decision_v0(blocked)

    assert decision[B3_STEP_PASSED] is True
    assert decision["b3_parameter_update_contract_proven"] is True
    assert decision["b3_finite_nonzero_parameter_update_proven"] is True
    assert decision["b3_tiny_loop_optional"] is True
    assert decision["real_covalent_feature_mapping_loader_gate_allowed"] is True
    assert decision["recommended_next_step"] == "real_covalent_feature_mapping_loader_gate"
    assert blocked_decision[B3_STEP_PASSED] is False
    assert blocked_decision["recommended_next_step"] == B3_STEP_DEBUG
    for item in [decision, blocked_decision]:
        assert item["training_allowed"] is False
        assert item["formal_training_allowed"] is False
        assert item["finetune_allowed"] is False
        assert item["quality_claim_allowed"] is False
        assert item["checkpoint_save_allowed"] is False
        assert item["model_save_allowed"] is False


def test_manifest_contract_and_safety_boundary():
    manifest = _cached_result()["manifest"]

    assert manifest["stage"] == "b3_single_optimizer_step_smoke_v0"
    assert manifest["previous_stage"] == "b3_backward_smoke_v0"
    assert manifest["step11q_validated"] is True
    assert manifest["mask_level"] == MASK_LEVEL
    assert manifest["input_source"] == "synthetic_10d_shape_contract"
    assert manifest["checkpoint_path"] == "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert manifest["requested_device"] == "cpu"
    assert manifest["resolved_device"] == "cpu"
    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["model_forward_called"] is True
    assert manifest["loss_computed"] is True
    assert manifest["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(manifest["selected_loss_value"]))
    assert manifest["loss_requires_grad"] is True
    assert manifest["loss_finite"] is True
    assert manifest["optimizer_type"] == OPTIMIZER_TYPE
    assert manifest["learning_rate"] == LEARNING_RATE
    assert manifest["weight_decay"] == WEIGHT_DECAY
    assert manifest["optimizer_created"] is True
    assert manifest["backward_called"] is True
    assert manifest["backward_call_count"] == 1
    assert manifest["backward_success"] is True
    assert manifest["optimizer_step_called"] is True
    assert manifest["optimizer_step_call_count"] == 1
    assert manifest["finite_nonzero_grad_exists"] is True
    assert manifest["trainable_parameter_count"] > 0
    assert manifest["parameters_with_grad_count"] > 0
    assert float(manifest["total_grad_norm"]) > 0.0
    assert float(manifest["max_abs_grad"]) > 0.0
    assert manifest["grad_nan_count"] == 0
    assert manifest["grad_inf_count"] == 0
    assert manifest["sampled_parameter_count"] > 0
    assert float(manifest["sampled_parameter_delta_l2"]) > 0.0
    assert float(manifest["sampled_parameter_delta_max_abs"]) > 0.0
    assert manifest["updated_parameter_tensors_count"] > 0
    assert manifest["parameter_update_finite"] is True
    assert manifest["parameter_update_nonzero"] is True
    assert manifest["b3_target_atom_count"] == 3
    assert manifest["b3_context_atom_count"] == 4
    assert manifest["b3_reactive_atom_in_context"] is True
    assert manifest["b3_reactive_atom_in_target"] is False
    assert manifest[B3_STEP_PASSED] is True
    assert manifest["b3_parameter_update_contract_proven"] is True
    assert manifest["b3_finite_nonzero_parameter_update_proven"] is True
    assert manifest["b3_tiny_loop_optional"] is True
    assert manifest["real_covalent_feature_mapping_loader_gate_allowed"] is True
    assert manifest["recommended_next_step"] == "real_covalent_feature_mapping_loader_gate"
    for key in [
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "original_diffsbdd_source_modified",
        "forbidden_artifacts_created",
    ]:
        assert manifest[key] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_update_table_contract():
    rows = _cached_result()["update_table_rows"]

    assert len(rows) == 1
    row = rows[0]
    assert row["mask_level"] == MASK_LEVEL
    assert row["input_source"] == "synthetic_10d_shape_contract"
    assert row["selected_loss_key"] == "masked_loss_total_dry"
    assert math.isfinite(float(row["selected_loss_value"]))
    assert row["loss_requires_grad"] is True
    assert row["loss_finite"] is True
    assert row["optimizer_type"] == OPTIMIZER_TYPE
    assert row["learning_rate"] == LEARNING_RATE
    assert row["weight_decay"] == WEIGHT_DECAY
    assert row["backward_called"] is True
    assert row["backward_call_count"] == 1
    assert row["backward_success"] is True
    assert row["optimizer_created"] is True
    assert row["optimizer_step_called"] is True
    assert row["optimizer_step_call_count"] == 1
    assert row["finite_nonzero_grad_exists"] is True
    assert row["sampled_parameter_count"] > 0
    assert float(row["sampled_parameter_delta_l2"]) > 0.0
    assert float(row["sampled_parameter_delta_max_abs"]) > 0.0
    assert row["updated_parameter_tensors_count"] > 0
    assert row["parameter_update_finite"] is True
    assert row["parameter_update_nonzero"] is True
    assert row["checkpoint_saved"] is False
    assert row["model_saved"] is False
    assert row["tensor_dump_saved"] is False
    assert row["status"] == "passed"
    assert row["blocking_reasons"] == ""


def test_script_writes_report_manifest_update_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / ("b3_single_optimizer_step_smoke_v0")
    report_csv = output_root / "report.csv"
    manifest_json = output_root / "manifest.json"
    update_csv = output_root / "update.csv"
    summary_md = tmp_path / "docs" / "summary.md"
    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "UPDATE_TABLE_CSV", update_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu") == 0

    report_rows = _read_csv(report_csv)
    update_rows = _read_csv(update_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    summary = summary_md.read_text(encoding="utf-8")
    assert len(report_rows) == 9
    assert {row["status"] for row in report_rows} == {"passed"}
    assert len(update_rows) == 1
    assert update_rows[0]["status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert "not training" in summary
    assert "B3 tiny loop is optional" in summary
    assert "recommended_next_step: real_covalent_feature_mapping_loader_gate" in summary


def test_generated_outputs_and_no_forbidden_artifacts():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert UPDATE_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()

    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    update_rows = _read_csv(UPDATE_TABLE_CSV)
    assert len(_read_csv(REPORT_CSV)) == 9
    assert len(update_rows) == 1
    assert update_rows[0]["status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


def test_no_protected_source_modification():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_no_forbidden_execution_calls_in_step11r_files():
    files = [
        "src/covalent_ext/b3_single_optimizer_step_smoke.py",
        "scripts/check_b3_single_optimizer_step_smoke_v0.py",
        "tests/test_b3_single_optimizer_step_smoke_v0.py",
    ]
    for relative in files:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            assert not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "torch"
                and func.attr == "save"
            )
            assert not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "trainer"
                and func.attr == "fit"
            )
            assert not (isinstance(func, ast.Name) and func.id in {"training_step", "save_checkpoint", "load_from_checkpoint"})
            assert not (isinstance(func, ast.Attribute) and func.attr in {"training_step", "save_checkpoint", "load_from_checkpoint"})


def test_controlled_optimizer_and_backward_call_locations_are_single_module_calls():
    def call_counts(relative: str) -> tuple[int, int]:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        backward_calls = 0
        optimizer_step_calls = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "loss_tensor" and node.func.attr == "backward":
                backward_calls += 1
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "optimizer" and node.func.attr == "step":
                optimizer_step_calls += 1
        return backward_calls, optimizer_step_calls

    assert call_counts("src/covalent_ext/b3_single_optimizer_step_smoke.py") == (1, 1)
    assert call_counts("scripts/check_b3_single_optimizer_step_smoke_v0.py") == (0, 0)
    assert call_counts("tests/test_b3_single_optimizer_step_smoke_v0.py") == (0, 0)
