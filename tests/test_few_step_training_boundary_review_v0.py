import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_few_step_training_boundary_review_v0 as review_script  # noqa: E402
from covalent_ext.few_step_training_boundary_review import (  # noqa: E402
    DEFAULT_ROOT,
    MASK_ORDER,
    NEXT_MASK_SCHEDULE,
    PROPOSED_NEXT_LR,
    PROPOSED_NEXT_MAX_STEPS,
    STAGE,
    assess_dry_run_stability_v0,
    build_checkpoint_boundary_v0,
    build_few_step_training_boundary_review_v0,
    build_next_run_stop_policy_v0,
    build_training_boundary_decision_v0,
    summarize_step10q_evidence_v0,
    validate_step10q_outputs_v0,
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


def test_validate_step10q_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10q_outputs_v0() is True


def test_evidence_summary_reads_step10q_core_fields():
    evidence = summarize_step10q_evidence_v0()

    assert evidence["step10q_dry_run_passed"] is True
    assert evidence["executed_steps"] == 4
    assert evidence["dry_run_training_steps_executed"] == 4
    assert evidence["mask_order"] == MASK_ORDER
    assert evidence["mask_levels_seen"] == MASK_ORDER
    assert evidence["mask_level_by_step"] == {
        "1": "A_warhead_only",
        "2": "B_linker_warhead",
        "3": "B2_scaffold_warhead",
        "4": "C_scaffold_linker_warhead",
    }
    assert set(evidence["loss_total_by_step"]) == {"1", "2", "3", "4"}
    assert all(value > 0 for value in evidence["loss_total_by_step"].values())
    assert all(value > 0 for value in evidence["grad_norm_by_step"].values())
    assert all(value > 0 for value in evidence["param_delta_norm_by_step"].values())
    assert evidence["all_safety_flags_false"] is True
    assert evidence["forbidden_artifacts_created"] is False
    assert evidence["original_source_files_modified"] is False


def test_stability_assessment_passes_without_requiring_loss_decrease():
    evidence = summarize_step10q_evidence_v0()
    stability = assess_dry_run_stability_v0(evidence)

    assert stability["stability_status"] == "passed"
    assert stability["loss_decrease_required"] is False
    assert stability["blocking_reasons"] == []
    assert stability["reason"] == "4-step dry run checks wiring and stability, not model quality"


def test_training_boundary_decision_keeps_training_and_checkpoint_forbidden():
    evidence = summarize_step10q_evidence_v0()
    stability = assess_dry_run_stability_v0(evidence)
    decision = build_training_boundary_decision_v0(evidence, stability)

    assert decision["formal_training_allowed"] is False
    assert decision["finetune_allowed"] is False
    assert decision["checkpoint_allowed"] is False
    assert decision["model_save_allowed"] is False
    assert decision["trainer_fit_allowed"] is False
    assert decision["training_step_allowed"] is False
    assert decision["source_modification_allowed"] is False
    assert decision["longer_no_checkpoint_dry_run_allowed"] is True
    assert decision["recommended_next_stage"] == "longer_no_checkpoint_training_dry_run_design"
    assert decision["next_run_type"] == "longer_no_checkpoint_dry_run"
    assert decision["proposed_max_steps"] == PROPOSED_NEXT_MAX_STEPS
    assert decision["proposed_mask_schedule"] == NEXT_MASK_SCHEDULE
    assert decision["proposed_batch_size"] == 3
    assert decision["proposed_shuffle"] is False
    assert decision["proposed_lr"] == PROPOSED_NEXT_LR
    assert decision["checkpoint_remains_forbidden"] is True
    assert decision["model_saving_remains_forbidden"] is True


def test_next_run_stop_policy_and_checkpoint_boundary():
    stop_policy = build_next_run_stop_policy_v0()
    checkpoint_boundary = build_checkpoint_boundary_v0()

    assert stop_policy["hard_max_steps"] == 12
    assert "abort on non-finite loss" in stop_policy["hard_stop_conditions"]
    assert "abort on non-finite gradients" in stop_policy["hard_stop_conditions"]
    assert "abort on checkpoint/model artifact" in stop_policy["hard_stop_conditions"]
    assert "abort on source modification" in stop_policy["hard_stop_conditions"]
    assert stop_policy["warning_thresholds"]["loss_total"] == 1e4
    assert stop_policy["warning_thresholds"]["grad_norm"] == 1e4
    assert stop_policy["warning_thresholds"]["max_grad_abs"] == 1e3
    assert stop_policy["warning_thresholds"]["param_delta_norm"] == 1.0
    assert stop_policy["warnings_are_hard_stop_by_default"] is False
    assert checkpoint_boundary["current_review_checkpoint_allowed"] is False
    assert checkpoint_boundary["next_12_step_dry_run_checkpoint_allowed"] is False
    assert checkpoint_boundary["next_checkpoint_allowed"] is False
    assert "explicit user approval" in checkpoint_boundary["first_checkpoint_discussion_requires"]


def test_full_review_manifest_core_fields():
    review = build_few_step_training_boundary_review_v0()
    manifest = review_script.preview_manifest(review)

    assert review["stage"] == STAGE
    assert review["previous_stage"] == "few_step_training_dry_run_no_checkpoint_v0"
    assert review["step10q_dry_run_passed"] is True
    assert review["stability_assessment"]["stability_status"] == "passed"
    assert review["all_checks_passed"] is True
    assert review["recommended_next_step"] == "longer_no_checkpoint_training_dry_run_design"
    assert manifest["stage"] == STAGE
    assert manifest["previous_stage"] == "few_step_training_dry_run_no_checkpoint_v0"
    assert manifest["step10q_dry_run_passed"] is True
    assert manifest["executed_steps"] == 4
    assert manifest["mask_order"] == MASK_ORDER
    assert manifest["all_losses_finite"] is True
    assert manifest["all_backward_success"] is True
    assert manifest["all_optimizer_steps_success"] is True
    assert manifest["all_parameter_updates_finite"] is True
    assert manifest["stop_triggered"] is False
    assert manifest["stability_status"] == "passed"
    assert manifest["loss_decrease_required"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["trainer_fit_allowed"] is False
    assert manifest["training_step_allowed"] is False
    assert manifest["source_modification_allowed"] is False
    assert manifest["longer_no_checkpoint_dry_run_allowed"] is True
    assert manifest["proposed_next_max_steps"] == 12
    assert manifest["proposed_next_mask_schedule"] == (
        "A_warhead_only / B_linker_warhead / B2_scaffold_warhead / C_scaffold_linker_warhead repeated 3 cycles"
    )
    assert manifest["proposed_next_lr"] == 1e-6
    assert manifest["proposed_next_shuffle"] is False
    assert manifest["next_checkpoint_allowed"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "longer_no_checkpoint_training_dry_run_design"


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert review_script.run() == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "few_step_training_boundary_review_report.csv")
    assert len(rows) == 6
    assert [row["review_section"] for row in rows] == [
        "evidence_review",
        "stability_assessment",
        "training_boundary_decision",
        "next_run_stop_policy",
        "checkpoint_boundary",
        "risk_register",
    ]
    assert all(row["stage"] == STAGE for row in rows)
    assert all(row["previous_stage"] == "few_step_training_dry_run_no_checkpoint_v0" for row in rows)
    assert all(row["status"] == "passed" for row in rows)
    assert all(row["recommended_next_step"] == "longer_no_checkpoint_training_dry_run_design" for row in rows)

    manifest = json.loads((root / "few_step_training_boundary_review_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["stability_status"] == "passed"
    assert manifest["formal_training_allowed"] is False
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["longer_no_checkpoint_dry_run_allowed"] is True
    assert manifest["next_checkpoint_allowed"] is False
    assert manifest["recommended_next_step"] == "longer_no_checkpoint_training_dry_run_design"
    assert Path("docs/few_step_training_boundary_review_v0_summary.md").is_file()

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
        REPO_ROOT / "src" / "covalent_ext" / "few_step_training_boundary_review.py",
        REPO_ROOT / "scripts" / "check_few_step_training_boundary_review_v0.py",
        REPO_ROOT / "tests" / "test_few_step_training_boundary_review_v0.py",
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
