import csv
import functools
import json
import math
import subprocess
import sys
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_pretrained_masked_loss_microbatch_backward_dry_run_v0 as script  # noqa: E402
from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    GRADIENT_TABLE_CSV,
    MANIFEST_JSON,
    MASK_LEVELS,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_differentiable_masked_loss_for_level_v0,
    build_fresh_strict_loaded_model_for_backward_level_v0,
    build_microbatch_backward_decision_v0,
    build_pretrained_masked_loss_microbatch_backward_dry_run_v0,
    collect_gradient_stats_v0,
    run_isolated_backward_for_mask_level_v0,
    run_pretrained_microbatch_backward_all_levels_v0,
    validate_step11g_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_full_result():
    return build_pretrained_masked_loss_microbatch_backward_dry_run_v0(device="cpu")


def test_validate_step11g_outputs_success():
    assert validate_step11g_outputs_v0() is True


def test_build_fresh_strict_loaded_model_for_each_mask_level():
    for mask_level in MASK_LEVELS:
        result = build_fresh_strict_loaded_model_for_backward_level_v0(mask_level, device="cpu")
        assert result["model_instantiated"] is True
        assert result["strict_load_success"] is True
        assert result["pretrained_weights_loaded"] is True
        assert result["pretrained_base_integration_proven"] is True
        assert result["optimizer_created"] is False
        assert result["optimizer_step_called"] is False
        assert result["model"] is not None


def test_build_differentiable_loss_requires_grad_and_is_finite():
    bundle = build_fresh_strict_loaded_model_for_backward_level_v0("A_warhead_only", device="cpu")
    result = build_differentiable_masked_loss_for_level_v0(
        bundle["model"],
        "A_warhead_only",
        bundle["input_contract"],
        device="cpu",
    )
    loss_tensor = result["loss_tensor"]

    assert torch.is_tensor(loss_tensor)
    assert result["candidate_inputs_built"] is True
    assert result["forward_success"] is True
    assert result["loss_tensor_built"] is True
    assert result["loss_requires_grad"] is True
    assert result["loss_finite"] is True
    assert result["selected_loss_key"] == "masked_loss_total_differentiable"
    assert result["target_atom_count"] == 2
    assert result["context_atom_count"] == 2
    assert result["synthetic_shape_smoke_only"] is True
    assert result["feature_semantics_known"] is False


def test_collect_gradient_stats_on_fresh_model_before_reverse_pass():
    bundle = build_fresh_strict_loaded_model_for_backward_level_v0("A_warhead_only", device="cpu")
    model = bundle["model"]
    model.zero_grad(set_to_none=True)
    stats = collect_gradient_stats_v0(model)

    assert stats["parameters_with_grad_count"] == 0
    assert stats["parameters_with_nonzero_grad_count"] == 0
    assert stats["parameters_with_finite_grad_count"] == 0
    assert stats["grad_nan_count"] == 0
    assert stats["grad_inf_count"] == 0
    assert stats["total_grad_norm"] == 0.0
    assert stats["max_abs_grad"] == 0.0


def test_run_isolated_backward_for_all_mask_levels():
    for mask_level in MASK_LEVELS:
        result = run_isolated_backward_for_mask_level_v0(mask_level, device="cpu")

        assert result["status"] == "passed"
        assert result["strict_load_success"] is True
        assert result["loss_requires_grad"] is True
        assert result["loss_finite"] is True
        assert result["backward_called"] is True
        assert result["backward_call_count"] == 1
        assert result["backward_success"] is True
        assert result["optimizer_created"] is False
        assert result["optimizer_step_called"] is False
        assert result["finite_nonzero_grad_exists"] is True
        assert result["grad_nan_count"] == 0
        assert result["grad_inf_count"] == 0
        assert math.isfinite(result["total_grad_norm"])
        assert math.isfinite(result["max_abs_grad"])


def test_all_level_backward_result_and_decision():
    result = run_pretrained_microbatch_backward_all_levels_v0(device="cpu")
    decision = build_microbatch_backward_decision_v0(result)

    assert result["mask_levels_attempted"] == MASK_LEVELS
    assert result["mask_levels_passed"] == MASK_LEVELS
    assert result["all_mask_levels_passed"] is True
    assert result["backward_level_count"] == 4
    assert result["backward_success_level_count"] == 4
    assert result["failed_mask_levels"] == []
    assert len(result["gradient_table_rows"]) == 4
    assert all(row["status"] == "passed" for row in result["gradient_table_rows"])
    assert decision["microbatch_backward_status"] == "pretrained_microbatch_backward_dry_run_passed"
    assert decision["microbatch_backward_dry_run_passed"] is True
    assert decision["gradient_plumbing_proven"] is True
    assert decision["optimizer_smoke_design_allowed"] is True
    assert decision["recommended_next_step"] == "optimizer_free_to_optimizer_smoke_design"
    assert decision["optimizer_created"] is False
    assert decision["optimizer_step_called"] is False
    assert decision["training_allowed"] is False


def test_full_backward_manifest_contract():
    result = _cached_full_result()
    manifest = result["manifest"]

    assert manifest["stage"] == "pretrained_masked_loss_microbatch_backward_dry_run_v0"
    assert manifest["previous_stage"] == "pretrained_masked_loss_microbatch_design_v0"
    assert manifest["step11g_validated"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["microbatch_backward_policy"] == "isolated_backward_per_mask_level"
    assert manifest["fresh_model_per_mask_level"] is True
    assert manifest["mask_levels_attempted"] == MASK_LEVELS
    assert manifest["mask_levels_passed"] == MASK_LEVELS
    assert manifest["all_mask_levels_passed"] is True
    assert manifest["backward_level_count"] == 4
    assert manifest["backward_success_level_count"] == 4
    assert manifest["backward_called"] is True
    assert manifest["backward_call_count_total"] == 4
    assert manifest["failed_mask_levels"] == []
    assert manifest["loss_requires_grad_all_levels"] is True
    assert manifest["finite_loss_all_levels"] is True
    assert manifest["finite_nonzero_grad_all_levels"] is True
    assert manifest["grad_nan_count_total"] == 0
    assert manifest["grad_inf_count_total"] == 0
    assert manifest["max_total_grad_norm"] > 0
    assert manifest["max_abs_grad_overall"] > 0
    assert manifest["microbatch_backward_status"] == "pretrained_microbatch_backward_dry_run_passed"
    assert manifest["microbatch_backward_dry_run_passed"] is True
    assert manifest["gradient_plumbing_proven"] is True
    assert manifest["optimizer_smoke_design_allowed"] is True
    assert manifest["optimizer_created"] is False
    assert manifest["optimizer_step_called"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "optimizer_free_to_optimizer_smoke_design"


def test_script_writes_report_manifest_gradient_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "pretrained_masked_loss_microbatch_backward_dry_run_v0"
    report_csv = output_root / "pretrained_masked_loss_microbatch_backward_report.csv"
    manifest_json = output_root / "pretrained_masked_loss_microbatch_backward_manifest.json"
    gradient_table_csv = output_root / "pretrained_masked_loss_microbatch_gradient_table.csv"
    summary_md = tmp_path / "docs" / "pretrained_masked_loss_microbatch_backward_dry_run_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "GRADIENT_TABLE_CSV", gradient_table_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu") == 0

    rows = _read_csv(report_csv)
    gradient_rows = _read_csv(gradient_table_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert len(rows) == 8
    assert len(gradient_rows) == 4
    assert all(row["status"] == "passed" for row in gradient_rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["backward_call_count_total"] == 4
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not formal training" in text
    assert "optimizer_free_to_optimizer_smoke_design" in text


def test_generated_outputs_and_safety_boundary_after_script_run():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert GRADIENT_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()
    rows = _read_csv(REPORT_CSV)
    gradient_rows = _read_csv(GRADIENT_TABLE_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))

    assert len(rows) == 8
    assert len(gradient_rows) == 4
    assert all(row["status"] == "passed" for row in gradient_rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["optimizer_created"] is False
    assert manifest["optimizer_step_called"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


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


def test_source_files_do_not_contain_forbidden_optimizer_train_or_save_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/pretrained_masked_loss_microbatch_backward_dry_run.py",
        REPO_ROOT / "scripts/check_pretrained_masked_loss_microbatch_backward_dry_run_v0.py",
        REPO_ROOT / "tests/test_pretrained_masked_loss_microbatch_backward_dry_run_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "optimizer" + ".step",
        "trainer" + ".fit",
        "training" + "_step" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
        "torch" + "." + "optim",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
