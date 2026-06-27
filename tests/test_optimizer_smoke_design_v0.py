import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_optimizer_smoke_design_v0 as script  # noqa: E402
from covalent_ext.optimizer_smoke_design import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    MASK_LEVELS,
    OUTPUT_ROOT,
    PROTOCOL_JSON,
    REPORT_CSV,
    SUMMARY_MD,
    build_optimizer_config_recommendation_v0,
    build_optimizer_smoke_design_decision_v0,
    build_optimizer_smoke_design_v0,
    build_optimizer_smoke_input_policy_v0,
    build_optimizer_smoke_protocol_v0,
    build_optimizer_smoke_risk_register_v0,
    load_step11h_gradient_evidence_v0,
    validate_step11h_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11h_outputs_success():
    assert validate_step11h_outputs_v0() is True


def test_load_step11h_gradient_evidence_reads_four_rows():
    evidence = load_step11h_gradient_evidence_v0()

    assert evidence["gradient_table_present"] is True
    assert evidence["gradient_table_row_count"] == 4
    assert set(evidence["mask_levels"]) == set(MASK_LEVELS)
    assert evidence["all_backward_success"] is True
    assert evidence["all_grad_finite"] is True
    assert evidence["all_have_nonzero_grad"] is True
    assert evidence["grad_nan_count_total"] == 0
    assert evidence["grad_inf_count_total"] == 0
    assert evidence["loss_values_by_level"]["A_warhead_only"] == 3.3604235649108887
    assert evidence["grad_norm_by_level"]["A_warhead_only"] == 118.79651159480801
    assert evidence["max_grad_norm"] == 118.79651159480801
    assert evidence["max_abs_grad_overall"] == 32.380165100097656
    assert evidence["gradient_scale_warning"] == "monitor_optimizer_step_size_for_large_gradient_norm"


def test_input_policy_selects_a_warhead_only():
    evidence = load_step11h_gradient_evidence_v0()
    policy = build_optimizer_smoke_input_policy_v0(evidence)

    assert policy["optimizer_smoke_input_source"] == "synthetic_10d_shape_contract"
    assert policy["mask_levels_for_optimizer_smoke"] == ["A_warhead_only"]
    assert policy["optional_expand_to_all_levels_after_first_pass"] is True
    assert policy["all_mask_levels_have_backward_evidence"] is True
    assert policy["selected_initial_mask_level"] == "A_warhead_only"
    assert policy["selection_reason"] == "largest_observed_grad_norm_and_simple_warhead_mask"


def test_optimizer_config_recommends_adamw_small_lr():
    config = build_optimizer_config_recommendation_v0()

    assert config["optimizer_class"] == "AdamW"
    assert config["optimizer_import_path_next_step"] == "torch" + "." + "optim" + ".AdamW"
    assert config["lr"] == 1e-6
    assert config["weight_decay"] == 0.0
    assert config["betas"] == [0.9, 0.999]
    assert config["eps"] == 1e-8
    assert config["base_lr_from_config"] == 1e-3
    assert config["scheduler_allowed"] is False
    assert config["gradient_accumulation_allowed"] is False
    assert config["mixed_precision_allowed"] is False
    assert config["gradient_clipping_allowed"] is False


def test_protocol_allows_single_optimizer_step_next_only():
    evidence = load_step11h_gradient_evidence_v0()
    policy = build_optimizer_smoke_input_policy_v0(evidence)
    config = build_optimizer_config_recommendation_v0()
    protocol = build_optimizer_smoke_protocol_v0(evidence, policy, config)

    assert protocol["proposed_next_stage"] == "optimizer_step_smoke_v0"
    assert protocol["input_source"] == "synthetic_10d_shape_contract"
    assert protocol["selected_mask_level"] == "A_warhead_only"
    assert protocol["model_policy"] == "fresh_strict_loaded_pretrained_model"
    assert protocol["optimizer_policy"] == "single AdamW optimizer for smoke only"
    assert protocol["backward_policy"] == "single backward"
    assert protocol["optimizer_step_policy"] == "single " + "optimizer" + ".step exactly once"
    assert protocol["optimizer_step_call_count_next_step"] == 1
    assert protocol["parameter_delta_policy"]["save_full_tensors"] is False
    assert "parameter_delta_l2_total finite positive" in protocol["pass_conditions"]
    assert "no checkpoint/model saved" in protocol["pass_conditions"]
    assert "not formal training" in protocol["non_claims"]
    assert "no generation quality claim" in protocol["non_claims"]


def test_risk_register_includes_required_risks():
    evidence = load_step11h_gradient_evidence_v0()
    policy = build_optimizer_smoke_input_policy_v0(evidence)
    config = build_optimizer_config_recommendation_v0()
    protocol = build_optimizer_smoke_protocol_v0(evidence, policy, config)
    risks = build_optimizer_smoke_risk_register_v0(evidence, policy, config, protocol)

    risk_ids = {risk["risk_id"] for risk in risks}
    assert "R1_synthetic_10d_contract" in risk_ids
    assert "R8_parameter_delta_tensor_leak" in risk_ids
    assert len(risks) >= 8
    assert all("mitigation" in risk for risk in risks)
    assert all(risk["blocks_11J"] is False for risk in risks)


def test_decision_allows_optimizer_step_smoke_only_after_step11h_passes():
    evidence = load_step11h_gradient_evidence_v0()
    policy = build_optimizer_smoke_input_policy_v0(evidence)
    config = build_optimizer_config_recommendation_v0()
    protocol = build_optimizer_smoke_protocol_v0(evidence, policy, config)

    ready = build_optimizer_smoke_design_decision_v0(evidence, policy, config, protocol, step11h_validated=True)
    blocked_step = build_optimizer_smoke_design_decision_v0(evidence, policy, config, protocol, step11h_validated=False)
    blocked_gradient = build_optimizer_smoke_design_decision_v0(
        {**evidence, "all_have_nonzero_grad": False},
        policy,
        config,
        protocol,
        step11h_validated=True,
    )

    assert ready["design_status"] == "optimizer_smoke_design_ready"
    assert ready["optimizer_step_smoke_allowed"] is True
    assert ready["recommended_next_step"] == "single_optimizer_step_smoke"
    assert blocked_step["design_status"] == "step11h_precondition_failed"
    assert blocked_step["optimizer_step_smoke_allowed"] is False
    assert blocked_gradient["design_status"] == "gradient_evidence_missing"
    assert blocked_gradient["optimizer_step_smoke_allowed"] is False
    for decision in [ready, blocked_step, blocked_gradient]:
        assert decision["this_design_creates_optimizer"] is False
        assert decision["this_design_runs_optimizer_step"] is False
        assert decision["this_design_runs_backward"] is False
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False


def test_full_design_manifest_contract():
    result = build_optimizer_smoke_design_v0()
    manifest = result["manifest"]

    assert manifest["stage"] == "optimizer_smoke_design_v0"
    assert manifest["previous_stage"] == "pretrained_masked_loss_microbatch_backward_dry_run_v0"
    assert manifest["step11h_validated"] is True
    assert manifest["gradient_plumbing_proven"] is True
    assert manifest["all_mask_levels_backward_passed"] is True
    assert manifest["grad_nan_count_total"] == 0
    assert manifest["grad_inf_count_total"] == 0
    assert manifest["max_total_grad_norm"] == 118.79651159480801
    assert manifest["selected_initial_mask_level"] == "A_warhead_only"
    assert manifest["optimizer_smoke_input_source"] == "synthetic_10d_shape_contract"
    assert manifest["optimizer_class_recommended"] == "AdamW"
    assert manifest["optimizer_lr_recommended"] == 1e-6
    assert manifest["optimizer_weight_decay_recommended"] == 0.0
    assert manifest["protocol_written"] is True
    assert manifest["proposed_next_stage"] == "optimizer_step_smoke_v0"
    assert manifest["optimizer_step_smoke_allowed"] is True
    assert manifest["optimizer_step_policy_next_step"] == "single " + "optimizer" + ".step exactly once"
    assert manifest["optimizer_step_call_count_next_step"] == 1
    assert manifest["checkpoint_save_allowed_next_step"] is False
    assert manifest["model_save_allowed_next_step"] is False
    assert manifest["design_status"] == "optimizer_smoke_design_ready"
    assert manifest["this_design_creates_optimizer"] is False
    assert manifest["this_design_runs_optimizer_step"] is False
    assert manifest["this_design_runs_backward"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["loss_decrease_required"] is False
    assert manifest["backward_called"] is False
    assert manifest["optimizer_created"] is False
    assert manifest["optimizer_step_called"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "single_optimizer_step_smoke"


def test_script_writes_report_manifest_protocol_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "optimizer_smoke_design_v0"
    report_csv = output_root / "optimizer_smoke_design_report.csv"
    manifest_json = output_root / "optimizer_smoke_design_manifest.json"
    protocol_json = output_root / "optimizer_smoke_protocol.json"
    summary_md = tmp_path / "docs" / "optimizer_smoke_design_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "PROTOCOL_JSON", protocol_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    rows = _read_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_json.read_text(encoding="utf-8"))
    assert len(rows) == 7
    assert [row["section"] for row in rows] == [
        "step11h_precondition",
        "gradient_evidence",
        "optimizer_input_policy",
        "optimizer_config",
        "optimizer_protocol",
        "design_decision",
        "safety_boundary",
    ]
    assert manifest["all_checks_passed"] is True
    assert protocol["protocol"]["optimizer_step_call_count_next_step"] == 1
    assert protocol["input_policy"]["selected_initial_mask_level"] == "A_warhead_only"
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not training" in text
    assert "single_optimizer_step_smoke" in text


def test_generated_outputs_and_safety_boundary_after_script_run():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert PROTOCOL_JSON.is_file()
    assert SUMMARY_MD.is_file()
    rows = _read_csv(REPORT_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))

    assert len(rows) == 7
    assert all(row["status"] == "passed" for row in rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["this_design_creates_optimizer"] is False
    assert manifest["this_design_runs_optimizer_step"] is False
    assert manifest["this_design_runs_backward"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert protocol["protocol"]["optimizer_step_call_count_next_step"] == 1
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


def test_source_files_do_not_contain_forbidden_execution_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/optimizer_smoke_design.py",
        REPO_ROOT / "scripts/check_optimizer_smoke_design_v0.py",
        REPO_ROOT / "tests/test_optimizer_smoke_design_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "optimizer" + ".step(",
        "trainer" + ".fit",
        "training" + "_step" + "(",
        "backward" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
        "torch" + "." + "optim",
        "op" + "tim" + ".",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
