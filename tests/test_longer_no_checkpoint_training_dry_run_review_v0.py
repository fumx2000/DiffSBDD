import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_longer_no_checkpoint_training_dry_run_review_v0 as review_script  # noqa: E402
from covalent_ext.longer_no_checkpoint_training_dry_run_review import (  # noqa: E402
    DEFAULT_ROOT,
    MASK_CYCLE,
    MASK_SCHEDULE,
    STAGE,
    assess_longer_dry_run_stability_v0,
    build_checkpoint_discussion_gate_v0,
    build_evidence_observations_v0,
    build_longer_no_checkpoint_training_dry_run_review_v0,
    build_next_boundary_decision_v0,
    summarize_step10t_evidence_v0,
    validate_step10t_outputs_v0,
)


PROTECTED_SOURCE_FILES = [
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/conditional_model.py",
    "equivariant_diffusion/dynamics.py",
    "lightning_modules.py",
]


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step10t_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10t_outputs_v0() is True


def test_evidence_summary_reads_step10t_core_fields():
    evidence = summarize_step10t_evidence_v0()

    assert evidence["step10t_dry_run_passed"] is True
    assert evidence["executed_steps"] == 12
    assert evidence["dry_run_training_steps_executed"] == 12
    assert evidence["mask_schedule"] == MASK_SCHEDULE
    assert evidence["mask_levels_seen"] == MASK_SCHEDULE
    assert evidence["mask_schedule_length"] == 12
    assert evidence["mask_counts_seen"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert evidence["all_steps_passed"] is True
    assert evidence["all_losses_finite"] is True
    assert evidence["all_backward_success"] is True
    assert evidence["all_optimizer_steps_success"] is True
    assert evidence["all_gradients_finite"] is True
    assert evidence["all_gradients_nonzero"] is True
    assert evidence["all_parameter_updates_finite"] is True
    assert evidence["all_parameter_updates_nonzero"] is True
    assert evidence["warning_steps"] == []
    assert evidence["warnings_triggered"] is False
    assert evidence["stop_triggered"] is False
    assert evidence["all_safety_flags_false"] is True
    assert evidence["forbidden_artifacts_created"] is False
    assert evidence["original_source_files_modified"] is False


def test_stability_assessment_passes_without_loss_decrease_or_quality_claim():
    evidence = summarize_step10t_evidence_v0()
    stability = assess_longer_dry_run_stability_v0(evidence)

    assert stability["stability_status"] == "passed"
    assert stability["loss_decrease_required"] is False
    assert stability["quality_claim_allowed"] is False
    assert stability["blocking_reasons"] == []
    assert stability["reason"] == "12-step dry run checks longer loop stability and safety boundaries, not model quality"


def test_observations_record_highest_gradient_without_failure():
    evidence = summarize_step10t_evidence_v0()
    observations = build_evidence_observations_v0(evidence)

    assert observations["highest_grad_step"] == 9
    assert observations["highest_grad_mask_level"] == "A_warhead_only"
    assert observations["highest_grad_value"] > 0
    assert observations["highest_grad_value"] == 201.119884
    assert observations["loss_trend_claim_allowed"] is False
    assert observations["quality_claim_allowed"] is False
    assert round(observations["grad_norm_range"][1], 6) == observations["highest_grad_value"]


def test_next_boundary_keeps_training_checkpoint_and_source_changes_forbidden():
    evidence = summarize_step10t_evidence_v0()
    stability = assess_longer_dry_run_stability_v0(evidence)
    observations = build_evidence_observations_v0(evidence)
    decision = build_next_boundary_decision_v0(evidence, stability, observations)

    assert decision["formal_training_allowed"] is False
    assert decision["finetune_allowed"] is False
    assert decision["checkpoint_allowed"] is False
    assert decision["model_save_allowed"] is False
    assert decision["trainer_fit_allowed"] is False
    assert decision["training_step_allowed"] is False
    assert decision["source_modification_allowed"] is False
    assert decision["checkpoint_policy_design_allowed"] is True
    assert decision["output_policy_design_allowed"] is True
    assert decision["longer_no_checkpoint_run_review_passed"] is True
    assert decision["next_stage_is_formal_training"] is False
    assert decision["next_stage_is_direct_checkpoint_save"] is False
    assert decision["recommended_next_stage"] == "checkpoint_and_output_policy_design"


def test_checkpoint_discussion_gate_keeps_checkpoint_disabled():
    gate = build_checkpoint_discussion_gate_v0()

    assert gate["current_review_checkpoint_allowed"] is False
    assert gate["checkpoint_save_allowed"] is False
    assert gate["checkpoint_load_allowed"] is False
    assert gate["model_save_allowed"] is False
    assert gate["next_step_is_policy_design_only"] is True
    assert "explicit user approval" in gate["checkpoint_may_be_enabled_only_after"]


def test_full_review_manifest_core_fields():
    review = build_longer_no_checkpoint_training_dry_run_review_v0()
    manifest = review_script.preview_manifest(review)

    assert review["stage"] == STAGE
    assert review["previous_stage"] == "longer_no_checkpoint_training_dry_run_v0"
    assert review["step10t_dry_run_passed"] is True
    assert review["stability_assessment"]["stability_status"] == "passed"
    assert review["all_checks_passed"] is True
    assert review["recommended_next_step"] == "checkpoint_and_output_policy_design"
    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == "longer_no_checkpoint_training_dry_run_v0"
    assert manifest["step10t_dry_run_passed"] is True
    assert manifest["executed_steps"] == 12
    assert manifest["dry_run_training_steps_executed"] == 12
    assert manifest["mask_schedule_length"] == 12
    assert manifest["mask_counts_seen"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert manifest["all_steps_passed"] is True
    assert manifest["all_losses_finite"] is True
    assert manifest["all_backward_success"] is True
    assert manifest["all_optimizer_steps_success"] is True
    assert manifest["all_gradients_finite"] is True
    assert manifest["all_gradients_nonzero"] is True
    assert manifest["all_parameter_updates_finite"] is True
    assert manifest["all_parameter_updates_nonzero"] is True
    assert manifest["warnings_triggered"] is False
    assert manifest["warning_steps"] == []
    assert manifest["stop_triggered"] is False
    assert manifest["stability_status"] == "passed"
    assert manifest["loss_decrease_required"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["highest_grad_step"] == 9
    assert manifest["highest_grad_mask_level"] == "A_warhead_only"
    assert manifest["highest_grad_value"] == 201.119884
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["trainer_fit_allowed"] is False
    assert manifest["training_step_allowed"] is False
    assert manifest["source_modification_allowed"] is False
    assert manifest["checkpoint_policy_design_allowed"] is True
    assert manifest["output_policy_design_allowed"] is True
    assert manifest["checkpoint_save_allowed"] is False
    assert manifest["checkpoint_load_allowed"] is False
    assert manifest["next_step_is_policy_design_only"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "checkpoint_and_output_policy_design"


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert review_script.run() == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "longer_no_checkpoint_training_dry_run_review_report.csv")
    assert len(rows) == 6
    assert [row["review_section"] for row in rows] == [
        "evidence_review",
        "stability_assessment",
        "observations",
        "next_boundary_decision",
        "checkpoint_discussion_gate",
        "risk_register",
    ]
    assert all(row["stage"] == STAGE for row in rows)
    assert all(row["previous_stage"] == "longer_no_checkpoint_training_dry_run_v0" for row in rows)
    assert all(row["status"] == "passed" for row in rows)
    assert all(row["recommended_next_step"] == "checkpoint_and_output_policy_design" for row in rows)

    manifest = json.loads(
        (root / "longer_no_checkpoint_training_dry_run_review_preview_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["all_checks_passed"] is True
    assert manifest["stability_status"] == "passed"
    assert manifest["formal_training_allowed"] is False
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["checkpoint_policy_design_allowed"] is True
    assert manifest["output_policy_design_allowed"] is True
    assert manifest["checkpoint_save_allowed"] is False
    assert manifest["checkpoint_load_allowed"] is False
    assert manifest["next_step_is_policy_design_only"] is True
    assert manifest["recommended_next_step"] == "checkpoint_and_output_policy_design"
    assert Path("docs/longer_no_checkpoint_training_dry_run_review_v0_summary.md").is_file()

    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not list(root.rglob("*.ckpt"))
    assert not list(root.rglob("*.pth"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before


def test_review_sources_do_not_call_training_checkpoint_or_save_apis():
    source_paths = [
        REPO_ROOT / "src" / "covalent_ext" / "longer_no_checkpoint_training_dry_run_review.py",
        REPO_ROOT / "scripts" / "check_longer_no_checkpoint_training_dry_run_review_v0.py",
        REPO_ROOT / "tests" / "test_longer_no_checkpoint_training_dry_run_review_v0.py",
    ]
    forbidden_call_tokens = [
        "." + "backward" + "(",
        "optimizer" + "." + "step" + "(",
        "trainer" + "." + "fit" + "(",
        "." + "fit" + "(",
        "training" + "_step" + "(",
        "torch" + "." + "save" + "(",
        "torch" + "." + "load" + "(",
        "save" + "_checkpoint" + "(",
        "load" + "_from" + "_checkpoint" + "(",
    ]
    for source_path in source_paths:
        text = source_path.read_text(encoding="utf-8")
        for token in forbidden_call_tokens:
            assert token not in text
