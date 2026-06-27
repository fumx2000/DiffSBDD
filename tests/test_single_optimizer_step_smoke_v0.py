import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_single_optimizer_step_smoke_v0 as script  # noqa: E402
from covalent_ext.single_optimizer_step_smoke import (  # noqa: E402
    DELTA_TABLE_CSV,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SELECTED_MASK_LEVEL,
    SUMMARY_MD,
    build_adamw_optimizer_for_smoke_v0,
    build_fresh_strict_loaded_model_for_optimizer_step_smoke_v0,
    build_optimizer_smoke_differentiable_loss_v0,
    build_single_optimizer_step_smoke_decision_v0,
    build_single_optimizer_step_smoke_v0,
    validate_step11i_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def smoke_result():
    return build_single_optimizer_step_smoke_v0(device="cpu")


@pytest.fixture(scope="module")
def fresh_model_bundle():
    bundle = build_fresh_strict_loaded_model_for_optimizer_step_smoke_v0(device="cpu")
    yield bundle
    model = bundle.get("model")
    if model is not None:
        model.zero_grad(set_to_none=True)


def test_validate_step11i_outputs_success():
    assert validate_step11i_outputs_v0() is True


def test_fresh_strict_loaded_model_success(fresh_model_bundle):
    assert fresh_model_bundle["selected_mask_level"] == SELECTED_MASK_LEVEL
    assert fresh_model_bundle["model_instantiated"] is True
    assert fresh_model_bundle["strict_load_success"] is True
    assert fresh_model_bundle["pretrained_weights_loaded"] is True
    assert fresh_model_bundle["pretrained_base_integration_proven"] is True
    assert fresh_model_bundle["checkpoint_saved"] is False
    assert fresh_model_bundle["model_saved"] is False


def test_adamw_optimizer_created_with_expected_config(fresh_model_bundle):
    optimizer_bundle = build_adamw_optimizer_for_smoke_v0(fresh_model_bundle["model"])
    optimizer = optimizer_bundle["optimizer"]

    assert optimizer_bundle["optimizer_created"] is True
    assert optimizer_bundle["optimizer_class"] == "AdamW"
    assert optimizer_bundle["optimizer_lr"] == 1e-6
    assert optimizer_bundle["optimizer_weight_decay"] == 0.0
    assert optimizer_bundle["optimizer_param_group_count"] == 1
    assert optimizer_bundle["optimizer_parameter_count"] > 0
    assert optimizer_bundle["optimizer_state_pre_step_count"] == 0
    assert isinstance(optimizer, torch.optim.AdamW)


def test_differentiable_loss_is_finite_and_requires_grad(fresh_model_bundle):
    model = fresh_model_bundle["model"]
    model.zero_grad(set_to_none=True)
    loss_result = build_optimizer_smoke_differentiable_loss_v0(
        model,
        fresh_model_bundle["input_contract"],
        fresh_model_bundle["resolved_device"],
    )

    assert loss_result["selected_mask_level"] == SELECTED_MASK_LEVEL
    assert loss_result["loss_tensor_built"] is True
    assert loss_result["loss_requires_grad"] is True
    assert loss_result["loss_finite"] is True
    assert loss_result["selected_loss_key"] == "masked_loss_total_differentiable"
    assert loss_result["selected_loss_value"] > 0
    assert loss_result["synthetic_shape_smoke_only"] is True
    assert loss_result["feature_semantics_known"] is False
    model.zero_grad(set_to_none=True)


def test_full_smoke_runs_one_backward_and_one_optimizer_step(smoke_result):
    manifest = smoke_result["manifest"]

    assert manifest["step11i_validated"] is True
    assert manifest["selected_mask_level"] == SELECTED_MASK_LEVEL
    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["optimizer_created"] is True
    assert manifest["optimizer_class"] == "AdamW"
    assert manifest["optimizer_lr"] == 1e-6
    assert manifest["optimizer_weight_decay"] == 0.0
    assert manifest["loss_requires_grad"] is True
    assert manifest["loss_finite"] is True
    assert manifest["selected_loss_key"] == "masked_loss_total_differentiable"
    assert manifest["backward_called"] is True
    assert manifest["backward_call_count"] == 1
    assert manifest["backward_success"] is True
    assert manifest["optimizer_step_called"] is True
    assert manifest["optimizer_step_call_count"] == 1
    assert manifest["optimizer_step_success"] is True


def test_gradient_and_parameter_delta_are_finite_positive(smoke_result):
    manifest = smoke_result["manifest"]

    assert manifest["grad_nan_count"] == 0
    assert manifest["grad_inf_count"] == 0
    assert manifest["finite_nonzero_grad_exists"] is True
    assert manifest["total_grad_norm"] > 0
    assert manifest["max_abs_grad"] > 0
    assert manifest["sampled_parameter_count"] > 0
    assert manifest["changed_parameter_count"] > 0
    assert manifest["parameter_delta_l2_total"] > 0
    assert manifest["parameter_delta_max_abs"] > 0
    assert manifest["parameter_delta_mean_abs"] > 0
    assert manifest["finite_parameter_delta"] is True
    assert manifest["delta_nan_count"] == 0
    assert manifest["delta_inf_count"] == 0


def test_snapshot_summary_is_in_memory_only(smoke_result):
    step_result = smoke_result["step_result"]

    assert step_result["snapshot_created"] is True
    assert step_result["sampled_parameter_count"] <= 20
    assert step_result["sampled_parameter_names"]
    assert "sampled_parameter_names" in step_result
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


def test_decision_allows_tiny_training_design_after_pass(smoke_result):
    decision = smoke_result["decision"]

    assert decision["optimizer_step_smoke_status"] == "single_optimizer_step_smoke_passed"
    assert decision["single_optimizer_step_smoke_passed"] is True
    assert decision["optimizer_plumbing_proven"] is True
    assert decision["tiny_training_dry_run_design_allowed"] is True
    assert decision["recommended_next_step"] == "tiny_training_dry_run_design"
    assert decision["training_allowed"] is False
    assert decision["formal_training_allowed"] is False
    assert decision["finetune_allowed"] is False
    assert decision["loss_decrease_required"] is False
    assert decision["quality_claim_allowed"] is False


def test_manifest_safety_boundary(smoke_result):
    manifest = smoke_result["manifest"]

    assert manifest["single_optimizer_step_smoke_passed"] is True
    assert manifest["optimizer_plumbing_proven"] is True
    assert manifest["tiny_training_dry_run_design_allowed"] is True
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["tensor_dump_saved"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "tiny_training_dry_run_design"


def test_script_writes_report_manifest_delta_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "single_optimizer_step_smoke_v0"
    report_csv = output_root / "single_optimizer_step_smoke_report.csv"
    manifest_json = output_root / "single_optimizer_step_smoke_manifest.json"
    delta_csv = output_root / "single_optimizer_step_delta_table.csv"
    summary_md = tmp_path / "docs" / "single_optimizer_step_smoke_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "DELTA_TABLE_CSV", delta_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu") == 0

    rows = _read_csv(report_csv)
    delta_rows = _read_csv(delta_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert len(rows) == 7
    assert [row["section"] for row in rows] == [
        "step11i_precondition",
        "pretrained_model_and_optimizer",
        "loss_and_backward",
        "optimizer_step",
        "parameter_delta",
        "decision",
        "safety_boundary",
    ]
    assert len(delta_rows) == 1
    assert delta_rows[0]["status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not formal training" in text
    assert "tiny_training_dry_run_design" in text


def test_generated_outputs_after_script_run():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert DELTA_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()
    rows = _read_csv(REPORT_CSV)
    delta_rows = _read_csv(DELTA_TABLE_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))

    assert len(rows) == 7
    assert all(row["status"] == "passed" for row in rows)
    assert len(delta_rows) == 1
    assert delta_rows[0]["selected_mask_level"] == SELECTED_MASK_LEVEL
    assert delta_rows[0]["status"] == "passed"
    assert manifest["optimizer_created"] is True
    assert manifest["optimizer_step_called"] is True
    assert manifest["optimizer_step_call_count"] == 1
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["tensor_dump_saved"] is False


def test_no_diffsbdd_source_modification():
    source_diff = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    staged_source_diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert source_diff.returncode == 0
    assert staged_source_diff.returncode == 0


def test_source_files_do_not_contain_forbidden_save_or_training_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/single_optimizer_step_smoke.py",
        REPO_ROOT / "scripts/check_single_optimizer_step_smoke_v0.py",
        REPO_ROOT / "tests/test_single_optimizer_step_smoke_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "trainer" + ".fit",
        "training" + "_step" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
