import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_tiny_training_dry_run_v0 as script  # noqa: E402
from covalent_ext.tiny_training_dry_run import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    MAX_STEPS,
    OPTIMIZER_CLASS,
    OPTIMIZER_LR,
    OPTIMIZER_WEIGHT_DECAY,
    OUTPUT_ROOT,
    REPORT_CSV,
    SELECTED_MASK_LEVEL,
    STEP_TABLE_CSV,
    SUMMARY_MD,
    build_tiny_training_dry_run_decision_v0,
    build_tiny_training_dry_run_v0,
    validate_step11k_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="session")
def dry_run_result():
    return build_tiny_training_dry_run_v0(device="cpu")


def test_validate_step11k_outputs_success():
    assert validate_step11k_outputs_v0() is True


def test_full_dry_run_manifest_contract(dry_run_result):
    manifest = dry_run_result["manifest"]

    assert manifest["stage"] == "tiny_training_dry_run_v0"
    assert manifest["previous_stage"] == "tiny_training_dry_run_design_v0"
    assert manifest["step11k_validated"] is True
    assert manifest["selected_mask_levels"] == [SELECTED_MASK_LEVEL]
    assert manifest["input_source"] == "synthetic_10d_shape_contract"
    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["optimizer_created"] is True
    assert manifest["optimizer_class"] == OPTIMIZER_CLASS
    assert manifest["optimizer_lr"] == OPTIMIZER_LR
    assert manifest["optimizer_weight_decay"] == OPTIMIZER_WEIGHT_DECAY
    assert manifest["reuse_optimizer_across_steps"] is True
    assert manifest["tiny_training_dry_run_step_count"] == MAX_STEPS
    assert manifest["step_count"] == MAX_STEPS
    assert manifest["step_indices"] == [1, 2, 3]
    assert manifest["all_steps_passed"] is True
    assert manifest["finite_loss_all_steps"] is True
    assert manifest["loss_decrease_required"] is False
    assert manifest["backward_call_count_total"] == 3
    assert manifest["optimizer_step_call_count_total"] == 3
    assert manifest["finite_grad_all_steps"] is True
    assert manifest["finite_parameter_delta_all_steps"] is True
    assert manifest["grad_nan_count_total"] == 0
    assert manifest["grad_inf_count_total"] == 0
    assert manifest["delta_nan_count_total"] == 0
    assert manifest["delta_inf_count_total"] == 0
    assert manifest["tiny_training_dry_run_passed"] is True
    assert manifest["tiny_training_loop_plumbing_proven"] is True
    assert manifest["real_covalent_loader_gate_allowed"] is True
    assert manifest["b3_scaffold_only_mask_design_allowed"] is True
    assert manifest["recommended_next_step"] == "b3_scaffold_only_mask_design"


def test_step_rows_show_three_finite_backward_optimizer_updates(dry_run_result):
    rows = dry_run_result["step_table_rows"]

    assert len(rows) == 3
    for index, row in enumerate(rows, start=1):
        assert int(row["step_index"]) == index
        assert row["selected_mask_level"] == SELECTED_MASK_LEVEL
        assert float(row["loss_value"]) > 0.0
        assert row["loss_requires_grad"] is True
        assert row["loss_finite"] is True
        assert row["backward_called"] is True
        assert row["backward_call_count"] == 1
        assert row["backward_success"] is True
        assert row["optimizer_step_called"] is True
        assert row["optimizer_step_call_count"] == 1
        assert row["optimizer_step_success"] is True
        assert row["grad_nan_count"] == 0
        assert row["grad_inf_count"] == 0
        assert float(row["total_grad_norm"]) > 0.0
        assert float(row["max_abs_grad"]) > 0.0
        assert row["finite_nonzero_grad_exists"] is True
        assert row["sampled_parameter_count"] == 20
        assert row["changed_parameter_count"] > 0
        assert float(row["parameter_delta_l2_total"]) > 0.0
        assert float(row["parameter_delta_max_abs"]) > 0.0
        assert row["finite_parameter_delta"] is True
        assert row["delta_nan_count"] == 0
        assert row["delta_inf_count"] == 0
        assert row["status"] == "passed"
        assert row["blocking_reasons"] == ""


def test_loss_trajectory_is_recorded_but_not_required_to_decrease(dry_run_result):
    manifest = dry_run_result["manifest"]
    losses = manifest["loss_values"]

    assert len(losses) == 3
    assert all(math.isfinite(float(loss)) and float(loss) > 0.0 for loss in losses)
    assert manifest["initial_loss_value"] == losses[0]
    assert manifest["final_loss_value"] == losses[-1]
    assert manifest["loss_decrease_required"] is False
    assert isinstance(manifest["loss_decreased_optional"], bool)
    assert isinstance(manifest["loss_increased_warning"], bool)


def test_decision_blocks_when_precondition_or_step_fails(dry_run_result):
    ready = build_tiny_training_dry_run_decision_v0(dry_run_result["run_result"])
    failed_step = build_tiny_training_dry_run_decision_v0(
        {**dry_run_result["run_result"], "step_rows": [{**dry_run_result["run_result"]["step_rows"][0], "status": "blocked"}]}
    )
    failed_precondition = build_tiny_training_dry_run_decision_v0({"step11k_validated": False, "step_rows": []})

    assert ready["tiny_training_dry_run_status"] == "tiny_training_dry_run_passed"
    assert ready["tiny_training_dry_run_passed"] is True
    assert ready["recommended_next_step"] == "b3_scaffold_only_mask_design"
    assert failed_step["tiny_training_dry_run_status"] == "tiny_training_step_failed"
    assert failed_step["tiny_training_dry_run_passed"] is False
    assert failed_step["recommended_next_step"] == "tiny_training_step_debug"
    assert failed_precondition["tiny_training_dry_run_status"] == "step11k_precondition_failed"
    assert failed_precondition["recommended_next_step"] == "tiny_training_dry_run_design_debug"
    for decision in [ready, failed_step, failed_precondition]:
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False
        assert decision["quality_claim_allowed"] is False
        assert decision["loss_decrease_required"] is False


def test_script_report_builder_has_expected_sections(dry_run_result):
    rows = script.build_report_rows(dry_run_result)

    assert len(rows) == 7
    assert [row["section"] for row in rows] == [
        "step11k_precondition",
        "pretrained_model_and_optimizer",
        "tiny_step_1",
        "tiny_step_2",
        "tiny_step_3",
        "decision",
        "safety_boundary",
    ]
    assert all(row["status"] == "passed" for row in rows)
    assert {row["recommended_next_step"] for row in rows} == {"b3_scaffold_only_mask_design"}


def test_generated_outputs_are_present_and_passed():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert STEP_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()

    report_rows = _read_csv(REPORT_CSV)
    step_rows = _read_csv(STEP_TABLE_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))

    assert len(report_rows) == 7
    assert all(row["status"] == "passed" for row in report_rows)
    assert len(step_rows) == 3
    assert all(row["status"] == "passed" for row in step_rows)
    assert all(row["selected_mask_level"] == SELECTED_MASK_LEVEL for row in step_rows)
    assert all(str(row["loss_finite"]).lower() == "true" for row in step_rows)
    assert all(str(row["backward_success"]).lower() == "true" for row in step_rows)
    assert all(str(row["optimizer_step_success"]).lower() == "true" for row in step_rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["tiny_training_dry_run_passed"] is True


def test_generated_summary_states_non_claims_and_next_step():
    text = SUMMARY_MD.read_text(encoding="utf-8")

    assert "not formal training" in text
    assert "synthetic 10D shape contract" in text
    assert "A_warhead_only" in text
    assert "does not prove convergence" in text
    assert "b3_scaffold_only_mask_design" in text


def test_safety_flags_are_false(dry_run_result):
    manifest = dry_run_result["manifest"]

    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["tensor_dump_saved"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["blocking_reasons"] == []


def test_no_forbidden_artifacts_in_output_root():
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


def test_source_files_do_not_contain_forbidden_save_trainer_checkpoint_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/tiny_training_dry_run.py",
        REPO_ROOT / "scripts/check_tiny_training_dry_run_v0.py",
        REPO_ROOT / "tests/test_tiny_training_dry_run_v0.py",
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
