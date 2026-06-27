import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_pretrained_masked_loss_microbatch_design_v0 as script  # noqa: E402
from covalent_ext.pretrained_masked_loss_microbatch_design import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    MASK_LEVELS,
    OUTPUT_ROOT,
    PROTOCOL_JSON,
    RECOMMENDED_MASK_SEQUENCE,
    REPORT_CSV,
    SUMMARY_MD,
    build_microbatch_design_decision_v0,
    build_microbatch_dry_run_protocol_v0,
    build_microbatch_risk_register_v0,
    build_pretrained_masked_loss_microbatch_design_v0,
    inspect_microbatch_data_sources_v0,
    load_step11f_loss_evidence_v0,
    validate_step11f_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11f_outputs_success():
    assert validate_step11f_outputs_v0() is True


def test_load_step11f_loss_evidence_reads_four_mask_losses():
    evidence = load_step11f_loss_evidence_v0()

    assert evidence["loss_table_present"] is True
    assert evidence["loss_table_row_count"] == 4
    assert set(evidence["mask_levels"]) == set(MASK_LEVELS)
    assert evidence["finite_loss_count"] == 4
    assert evidence["all_loss_values_positive"] is True
    assert evidence["loss_values_by_level"]["A_warhead_only"] == 24.993852615356445
    assert evidence["loss_values_by_level"]["B_linker_warhead"] == 64.95052337646484
    assert evidence["loss_values_by_level"]["B2_scaffold_warhead"] == 16.925447463989258
    assert evidence["loss_values_by_level"]["C_scaffold_linker_warhead"] == 508.4341735839844
    assert evidence["max_loss"] == 508.4341735839844
    assert evidence["loss_value_scale_warning"] == "monitor_gradient_norm_for_large_C_level_loss"


def test_inspect_microbatch_data_sources_recommends_synthetic_10d_contract():
    sources = inspect_microbatch_data_sources_v0()

    assert sources["real_covalent_sample_available"] is True
    assert sources["real_covalent_sample_candidates"]
    assert sources["synthetic_contract_available"] is True
    assert sources["synthetic_10d_contract_available"] is True
    assert sources["recommended_microbatch_input_source"] == "synthetic_10d_shape_contract"
    assert sources["schema_sources"] == ["src/covalent_ext/schema.py", "src/covalent_ext/masking.py"]
    assert sources["real_covalent_sample_checkpoint_compatible"] is False


def test_microbatch_protocol_defines_isolated_backward_per_level_boundary():
    loss_evidence = load_step11f_loss_evidence_v0()
    sources = inspect_microbatch_data_sources_v0()
    protocol = build_microbatch_dry_run_protocol_v0(loss_evidence, sources)

    assert protocol["proposed_next_stage"] == "pretrained_masked_loss_microbatch_dry_run_v0"
    assert protocol["allowed_device_default"] == "cpu"
    assert protocol["allowed_mask_levels"] == MASK_LEVELS
    assert protocol["recommended_mask_level_sequence"] == RECOMMENDED_MASK_SEQUENCE
    assert protocol["mask_levels_for_backward_dry_run"] == MASK_LEVELS
    assert protocol["microbatch_backward_policy"] == "isolated_backward_per_mask_level"
    assert protocol["fresh_model_per_mask_level"] is True
    assert protocol["strict_load_fresh_model_per_mask_level"] is True
    assert protocol["backward_allowed_next_step"] is True
    assert protocol["reverse_pass_invocations_per_mask_level"] == 1
    assert protocol["optimizer_allowed_next_step"] is False
    assert protocol["optimizer_step_allowed_next_step"] is False
    assert protocol["trainer_fit_allowed_next_step"] is False
    assert protocol["training_step_allowed_next_step"] is False
    assert protocol["checkpoint_save_allowed_next_step"] is False
    assert protocol["model_save_allowed_next_step"] is False
    assert "loss requires grad" in protocol["pass_conditions"]
    assert "training quality is not proven" in protocol["non_claims"]


def test_risk_register_includes_synthetic_10d_semantics_risk():
    loss_evidence = load_step11f_loss_evidence_v0()
    sources = inspect_microbatch_data_sources_v0()
    protocol = build_microbatch_dry_run_protocol_v0(loss_evidence, sources)
    risks = build_microbatch_risk_register_v0(loss_evidence, sources, protocol)

    assert len(risks) >= 6
    risk_ids = {risk["risk_id"] for risk in risks}
    assert "R1_synthetic_10d_semantics" in risk_ids
    assert "R6_real_covalent_loader_gap" in risk_ids
    assert any("Synthetic 10D contract" in risk["description"] for risk in risks)
    assert all("mitigation" in risk for risk in risks)
    assert all(risk["blocks_11H"] is False for risk in risks)


def test_decision_allows_microbatch_backward_only_after_step11f_and_source():
    loss_evidence = load_step11f_loss_evidence_v0()
    sources = inspect_microbatch_data_sources_v0()
    protocol = build_microbatch_dry_run_protocol_v0(loss_evidence, sources)

    ready = build_microbatch_design_decision_v0(loss_evidence, sources, protocol, step11f_validated=True)
    blocked_source = build_microbatch_design_decision_v0(
        loss_evidence,
        {**sources, "synthetic_10d_contract_available": False},
        protocol,
        step11f_validated=True,
    )
    blocked_step = build_microbatch_design_decision_v0(loss_evidence, sources, protocol, step11f_validated=False)

    assert ready["design_status"] == "microbatch_dry_run_design_ready"
    assert ready["microbatch_backward_dry_run_allowed"] is True
    assert ready["recommended_next_step"] == "pretrained_masked_loss_microbatch_backward_dry_run"
    assert blocked_source["design_status"] == "microbatch_input_source_blocked"
    assert blocked_source["microbatch_backward_dry_run_allowed"] is False
    assert blocked_step["design_status"] == "step11f_precondition_failed"
    for decision in [ready, blocked_source, blocked_step]:
        assert decision["this_design_executes_backward"] is False
        assert decision["this_design_creates_optimizer"] is False
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False
        assert decision["optimizer_step_allowed"] is False


def test_full_design_manifest_contract():
    result = build_pretrained_masked_loss_microbatch_design_v0()
    manifest = result["manifest"]

    assert manifest["stage"] == "pretrained_masked_loss_microbatch_design_v0"
    assert manifest["previous_stage"] == "pretrained_masked_loss_smoke_v0"
    assert manifest["step11f_validated"] is True
    assert manifest["step11f_all_mask_levels_passed"] is True
    assert manifest["step11f_finite_loss_level_count"] == 4
    assert manifest["recommended_microbatch_input_source"] == "synthetic_10d_shape_contract"
    assert manifest["real_covalent_sample_available"] is True
    assert manifest["synthetic_10d_contract_available"] is True
    assert manifest["protocol_written"] is True
    assert manifest["proposed_next_stage"] == "pretrained_masked_loss_microbatch_dry_run_v0"
    assert manifest["microbatch_backward_policy"] == "isolated_backward_per_mask_level"
    assert manifest["mask_levels_for_backward_dry_run"] == MASK_LEVELS
    assert manifest["fresh_model_per_mask_level"] is True
    assert manifest["backward_allowed_next_step"] is True
    assert manifest["optimizer_step_allowed_next_step"] is False
    assert manifest["optimizer_allowed_next_step"] is False
    assert manifest["checkpoint_save_allowed_next_step"] is False
    assert manifest["model_save_allowed_next_step"] is False
    assert manifest["design_status"] == "microbatch_dry_run_design_ready"
    assert manifest["microbatch_backward_dry_run_allowed"] is True
    assert manifest["this_design_executes_backward"] is False
    assert manifest["this_design_creates_optimizer"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["optimizer_step_allowed"] is False
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
    assert manifest["recommended_next_step"] == "pretrained_masked_loss_microbatch_backward_dry_run"


def test_script_writes_report_manifest_protocol_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "pretrained_masked_loss_microbatch_design_v0"
    report_csv = output_root / "pretrained_masked_loss_microbatch_design_report.csv"
    manifest_json = output_root / "pretrained_masked_loss_microbatch_design_manifest.json"
    protocol_json = output_root / "pretrained_masked_loss_microbatch_protocol.json"
    summary_md = tmp_path / "docs" / "pretrained_masked_loss_microbatch_design_v0_summary.md"

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
        "step11f_precondition",
        "step11f_loss_evidence",
        "microbatch_data_source_inspection",
        "microbatch_protocol",
        "risk_register",
        "design_decision",
        "safety_boundary",
    ]
    assert manifest["all_checks_passed"] is True
    assert protocol["protocol"]["microbatch_backward_policy"] == "isolated_backward_per_mask_level"
    assert protocol["data_source_evidence"]["recommended_microbatch_input_source"] == "synthetic_10d_shape_contract"
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not training" in text
    assert "pretrained_masked_loss_microbatch_backward_dry_run" in text


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
    assert manifest["this_design_executes_backward"] is False
    assert manifest["this_design_creates_optimizer"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["optimizer_step_allowed"] is False
    assert protocol["protocol"]["optimizer_allowed_next_step"] is False
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
        REPO_ROOT / "src/covalent_ext/pretrained_masked_loss_microbatch_design.py",
        REPO_ROOT / "scripts/check_pretrained_masked_loss_microbatch_design_v0.py",
        REPO_ROOT / "tests/test_pretrained_masked_loss_microbatch_design_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "optimizer" + ".step",
        "trainer" + ".fit",
        "training" + "_step" + "(",
        "backward" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
