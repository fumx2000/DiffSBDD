import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_tiny_training_dry_run_design_v0 as script  # noqa: E402
from covalent_ext.tiny_training_dry_run_design import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    PROTOCOL_JSON,
    REPORT_CSV,
    SUMMARY_MD,
    build_tiny_training_design_decision_v0,
    build_tiny_training_dry_run_design_v0,
    build_tiny_training_evidence_schema_v0,
    build_tiny_training_protocol_v0,
    build_tiny_training_risk_register_v0,
    build_tiny_training_scope_v0,
    load_step11j_optimizer_evidence_v0,
    validate_step11j_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11j_outputs_success():
    assert validate_step11j_outputs_v0() is True


def test_load_step11j_optimizer_evidence_reads_single_delta_row():
    evidence = load_step11j_optimizer_evidence_v0()

    assert evidence["delta_table_present"] is True
    assert evidence["delta_table_row_count"] == 1
    assert evidence["selected_mask_level"] == "A_warhead_only"
    assert evidence["optimizer_class"] == "AdamW"
    assert evidence["optimizer_lr"] == 1e-6
    assert evidence["optimizer_weight_decay"] == 0.0
    assert evidence["selected_loss_value"] == 1.6932651996612549
    assert evidence["backward_call_count"] == 1
    assert evidence["optimizer_step_call_count"] == 1
    assert evidence["sampled_parameter_count"] == 20
    assert evidence["changed_parameter_count"] == 20
    assert evidence["unchanged_parameter_count"] == 0
    assert evidence["parameter_delta_l2_total"] == 0.0002464914740098643
    assert evidence["parameter_delta_max_abs"] == 1.0132789611816406e-06
    assert evidence["parameter_delta_mean_abs"] == 9.956481736214966e-07
    assert evidence["finite_parameter_delta"] is True
    assert evidence["delta_nan_count"] == 0
    assert evidence["delta_inf_count"] == 0
    assert evidence["optimizer_step_smoke_passed"] is True
    assert evidence["optimizer_plumbing_proven"] is True


def test_tiny_training_scope_uses_three_a_only_synthetic_steps():
    evidence = load_step11j_optimizer_evidence_v0()
    scope = build_tiny_training_scope_v0(evidence)

    assert scope["proposed_next_stage"] == "tiny_training_dry_run_v0"
    assert scope["input_source"] == "synthetic_10d_shape_contract"
    assert scope["selected_mask_levels"] == ["A_warhead_only"]
    assert scope["optional_later_expand_mask_levels"] == [
        "B_linker_warhead",
        "B2_scaffold_warhead",
        "C_scaffold_linker_warhead",
    ]
    assert scope["max_steps"] == 3
    assert scope["batch_size"] == 1
    assert scope["device_default"] == "cpu"
    assert scope["optimizer_class"] == "AdamW"
    assert scope["lr"] == 1e-6
    assert scope["weight_decay"] == 0.0
    assert scope["fresh_model_once"] is True
    assert scope["reuse_optimizer_across_steps"] is True
    assert scope["no_scheduler"] is True
    assert scope["no_mixed_precision"] is True
    assert scope["no_gradient_accumulation"] is True
    assert scope["no_gradient_clipping"] is True


def test_protocol_allows_next_three_step_tiny_dry_run_only():
    evidence = load_step11j_optimizer_evidence_v0()
    scope = build_tiny_training_scope_v0(evidence)
    protocol = build_tiny_training_protocol_v0(scope, evidence)

    assert protocol["proposed_next_stage"] == "tiny_training_dry_run_v0"
    assert protocol["input_source"] == "synthetic_10d_shape_contract"
    assert protocol["selected_mask_levels"] == ["A_warhead_only"]
    assert protocol["max_steps"] == 3
    assert protocol["fresh_strict_loaded_pretrained_model"] is True
    assert protocol["create_one_optimizer"] is True
    assert protocol["reuse_optimizer_across_steps"] is True
    assert protocol["optimizer_class"] == "AdamW"
    assert protocol["optimizer_lr"] == 1e-6
    assert protocol["optimizer_weight_decay"] == 0.0
    assert "step_count equals 3" in protocol["pass_conditions"]
    assert "no checkpoint/model/tensor dump saved" in protocol["pass_conditions"]
    assert protocol["loss_trajectory_rule"]["loss_decrease_required"] is False
    assert protocol["loss_trajectory_rule"]["allow_loss_up_down_or_flat"] is True
    assert "loss decrease not required" in protocol["non_claims"]
    assert "no real covalent data-loader readiness claim" in protocol["non_claims"]


def test_evidence_schema_contains_step_table_and_manifest_fields():
    schema = build_tiny_training_evidence_schema_v0()

    for field in [
        "step_index",
        "loss_value",
        "loss_requires_grad",
        "loss_finite",
        "backward_called",
        "optimizer_step_called",
        "parameter_delta_l2_total",
        "finite_parameter_delta",
    ]:
        assert field in schema["step_table_fields"]
    for field in [
        "tiny_training_dry_run_step_count",
        "loss_decrease_required",
        "tiny_training_dry_run_passed",
        "real_covalent_loader_gate_allowed",
        "recommended_next_step",
    ]:
        assert field in schema["manifest_fields"]
    assert schema["scalar_only_parameter_delta"] is True
    assert schema["full_tensor_dump_allowed"] is False


def test_risk_register_includes_required_risks():
    evidence = load_step11j_optimizer_evidence_v0()
    scope = build_tiny_training_scope_v0(evidence)
    protocol = build_tiny_training_protocol_v0(scope, evidence)
    risks = build_tiny_training_risk_register_v0(evidence, scope, protocol)

    risk_ids = {risk["risk_id"] for risk in risks}
    assert "R1_synthetic_10d_semantics" in risk_ids
    assert "R6_real_covalent_loader_gap" in risk_ids
    assert "R7_a_only_mask_scope" in risk_ids
    assert len(risks) >= 10
    assert all("mitigation" in risk for risk in risks)
    assert all(risk["blocks_11L"] is False for risk in risks)


def test_decision_allows_tiny_dry_run_only_after_step11j_passes():
    evidence = load_step11j_optimizer_evidence_v0()
    scope = build_tiny_training_scope_v0(evidence)
    protocol = build_tiny_training_protocol_v0(scope, evidence)

    ready = build_tiny_training_design_decision_v0(evidence, scope, protocol, step11j_validated=True)
    blocked_step = build_tiny_training_design_decision_v0(evidence, scope, protocol, step11j_validated=False)
    blocked_evidence = build_tiny_training_design_decision_v0(
        {**evidence, "optimizer_plumbing_proven": False},
        scope,
        protocol,
        step11j_validated=True,
    )

    assert ready["design_status"] == "tiny_training_dry_run_design_ready"
    assert ready["tiny_training_dry_run_allowed"] is True
    assert ready["recommended_next_step"] == "tiny_training_dry_run"
    assert blocked_step["design_status"] == "step11j_precondition_failed"
    assert blocked_step["tiny_training_dry_run_allowed"] is False
    assert blocked_evidence["design_status"] == "optimizer_evidence_missing"
    assert blocked_evidence["tiny_training_dry_run_allowed"] is False
    for decision in [ready, blocked_step, blocked_evidence]:
        assert decision["this_design_runs_training_loop"] is False
        assert decision["this_design_runs_backward"] is False
        assert decision["this_design_creates_optimizer"] is False
        assert decision["this_design_runs_optimizer_step"] is False
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False


def test_full_design_manifest_contract():
    result = build_tiny_training_dry_run_design_v0()
    manifest = result["manifest"]

    assert manifest["stage"] == "tiny_training_dry_run_design_v0"
    assert manifest["previous_stage"] == "single_optimizer_step_smoke_v0"
    assert manifest["step11j_validated"] is True
    assert manifest["optimizer_plumbing_proven"] is True
    assert manifest["selected_mask_level"] == "A_warhead_only"
    assert manifest["optimizer_class"] == "AdamW"
    assert manifest["optimizer_lr"] == 1e-6
    assert manifest["optimizer_weight_decay"] == 0.0
    assert manifest["single_step_delta_positive"] is True
    assert manifest["protocol_written"] is True
    assert manifest["proposed_next_stage"] == "tiny_training_dry_run_v0"
    assert manifest["tiny_training_dry_run_step_count"] == 3
    assert manifest["selected_mask_levels"] == ["A_warhead_only"]
    assert manifest["input_source"] == "synthetic_10d_shape_contract"
    assert manifest["reuse_optimizer_across_steps"] is True
    assert manifest["tiny_training_dry_run_allowed"] is True
    assert manifest["checkpoint_save_allowed_next_step"] is False
    assert manifest["model_save_allowed_next_step"] is False
    assert manifest["tensor_dump_allowed_next_step"] is False
    assert manifest["design_status"] == "tiny_training_dry_run_design_ready"
    assert manifest["this_design_runs_training_loop"] is False
    assert manifest["this_design_runs_backward"] is False
    assert manifest["this_design_creates_optimizer"] is False
    assert manifest["this_design_runs_optimizer_step"] is False
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
    assert manifest["tensor_dump_saved"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "tiny_training_dry_run"


def test_script_writes_report_manifest_protocol_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "tiny_training_dry_run_design_v0"
    report_csv = output_root / "tiny_training_dry_run_design_report.csv"
    manifest_json = output_root / "tiny_training_dry_run_design_manifest.json"
    protocol_json = output_root / "tiny_training_dry_run_protocol.json"
    summary_md = tmp_path / "docs" / "tiny_training_dry_run_design_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "PROTOCOL_JSON", protocol_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    rows = _read_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_json.read_text(encoding="utf-8"))
    assert len(rows) == 8
    assert [row["section"] for row in rows] == [
        "step11j_precondition",
        "optimizer_evidence",
        "tiny_training_scope",
        "tiny_training_protocol",
        "evidence_schema",
        "risk_register",
        "design_decision",
        "safety_boundary",
    ]
    assert manifest["all_checks_passed"] is True
    assert protocol["scope"]["max_steps"] == 3
    assert protocol["protocol"]["loss_trajectory_rule"]["loss_decrease_required"] is False
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not training" in text
    assert "tiny_training_dry_run" in text


def test_generated_outputs_and_safety_boundary_after_script_run():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert PROTOCOL_JSON.is_file()
    assert SUMMARY_MD.is_file()
    rows = _read_csv(REPORT_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))

    assert len(rows) == 8
    assert all(row["status"] == "passed" for row in rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["this_design_runs_training_loop"] is False
    assert manifest["this_design_runs_backward"] is False
    assert manifest["this_design_creates_optimizer"] is False
    assert manifest["this_design_runs_optimizer_step"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert protocol["protocol"]["max_steps"] == 3
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
        REPO_ROOT / "src/covalent_ext/tiny_training_dry_run_design.py",
        REPO_ROOT / "scripts/check_tiny_training_dry_run_design_v0.py",
        REPO_ROOT / "tests/test_tiny_training_dry_run_design_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "optimizer" + ".step",
        "trainer" + ".fit",
        "training" + "_step" + "(",
        "back" + "ward" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
        "torch" + "." + "optim",
        "op" + "tim" + ".",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
