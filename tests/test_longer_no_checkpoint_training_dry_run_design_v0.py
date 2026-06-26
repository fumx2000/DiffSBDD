import csv
import json
import shutil
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_longer_no_checkpoint_training_dry_run_design_v0 as design_script  # noqa: E402
from covalent_ext.longer_no_checkpoint_training_dry_run_design import (  # noqa: E402
    BATCH_SIZE,
    DEFAULT_LR,
    DEFAULT_WEIGHT_DECAY,
    FORBIDDEN_OUTPUTS,
    LOSS_WEIGHTS,
    MASK_CYCLE,
    MASK_SCHEDULE,
    MAX_STEPS,
    OPTIMIZER_CLASS,
    SEED,
    SHUFFLE,
    build_longer_dry_run_checkpoint_policy_v0,
    build_longer_dry_run_contract_v0,
    build_longer_dry_run_loss_policy_v0,
    build_longer_dry_run_output_policy_v0,
    build_longer_dry_run_schedule_v0,
    build_longer_dry_run_stop_policy_v0,
    build_longer_dry_run_success_criteria_v0,
    build_longer_no_checkpoint_training_dry_run_design_v0,
    validate_step10r_outputs_v0,
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


def test_validate_step10r_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10r_outputs_v0() is True


def test_schedule_is_three_complete_a_b_b2_c_cycles():
    schedule = build_longer_dry_run_schedule_v0()

    assert len(schedule) == 12
    assert [row["step"] for row in schedule] == list(range(1, 13))
    assert [row["mask_level"] for row in schedule] == MASK_SCHEDULE
    assert [row["mask_level"] for row in schedule[0::4]] == ["A_warhead_only"] * 3
    assert [row["mask_level"] for row in schedule[1::4]] == ["B_linker_warhead"] * 3
    assert [row["mask_level"] for row in schedule[2::4]] == ["B2_scaffold_warhead"] * 3
    assert [row["mask_level"] for row in schedule[3::4]] == ["C_scaffold_linker_warhead"] * 3
    assert Counter(row["mask_level"] for row in schedule) == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert [row["cycle_index"] for row in schedule] == [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
    assert all(row["batch_size"] == BATCH_SIZE for row in schedule)
    assert all(row["shuffle"] is False for row in schedule)
    assert all(row["seed"] == SEED for row in schedule)


def test_contract_loss_output_checkpoint_and_stop_policies():
    contract = build_longer_dry_run_contract_v0()
    loss_policy = build_longer_dry_run_loss_policy_v0()
    stop_policy = build_longer_dry_run_stop_policy_v0()
    output_policy = build_longer_dry_run_output_policy_v0()
    checkpoint_policy = build_longer_dry_run_checkpoint_policy_v0()
    success_criteria = build_longer_dry_run_success_criteria_v0()

    assert "instantiate one fresh in-memory model" in contract["allowed_actions"]
    assert "build one AdamW optimizer" in contract["allowed_actions"]
    assert "run fixed 12-step loop" in contract["allowed_actions"]
    assert "backward" in contract["allowed_actions"]
    assert "optimizer" + "." + "step" in contract["allowed_actions"]
    assert "trainer" + "." + "fit" in contract["forbidden_actions"]
    assert "training_step" in contract["forbidden_actions"]
    assert "checkpoint loading" in contract["forbidden_actions"]
    assert "checkpoint saving" in contract["forbidden_actions"]
    assert "torch" + "." + "save" in contract["forbidden_actions"]
    assert "model saving" in contract["forbidden_actions"]
    assert "formal training" in contract["forbidden_actions"]
    assert "fine-tune" in contract["forbidden_actions"]
    assert loss_policy["loss_weights"] == LOSS_WEIGHTS
    assert loss_policy["auxiliary_losses_enabled"] is False
    assert loss_policy["loss_decrease_required"] is False
    assert loss_policy["quality_claim_allowed"] is False
    assert stop_policy["hard_max_steps"] == MAX_STEPS
    assert "abort on non-finite loss" in stop_policy["hard_stop_conditions"]
    assert "abort on optimizer step failure" in stop_policy["hard_stop_conditions"]
    assert "abort on checkpoint/model artifact" in stop_policy["hard_stop_conditions"]
    assert stop_policy["warnings_are_hard_stop_by_default"] is False
    assert stop_policy["warnings_must_be_logged"] is True
    assert output_policy["allowed_outputs"] == ["csv report", "json preview manifest", "markdown summary"]
    for suffix in [".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"]:
        assert suffix in output_policy["forbidden_outputs"]
        assert suffix in FORBIDDEN_OUTPUTS
    assert checkpoint_policy["current_design_checkpoint_allowed"] is False
    assert checkpoint_policy["next_12_step_dry_run_checkpoint_allowed"] is False
    assert checkpoint_policy["model_save_allowed"] is False
    assert checkpoint_policy["checkpoint_load_allowed"] is False
    assert checkpoint_policy["checkpoint_save_allowed"] is False
    assert "explicit user approval" in checkpoint_policy["checkpoint_discussion_deferred_until"]
    assert success_criteria["executed_steps"] == 12
    assert success_criteria["expected_mask_schedule_followed"] is True
    assert success_criteria["all_losses_finite"] is True
    assert success_criteria["all_backward_success"] is True
    assert success_criteria["all_optimizer_steps_success"] is True
    assert success_criteria["all_parameter_updates_finite"] is True
    assert success_criteria["stop_triggered"] is False
    assert success_criteria["forbidden_artifacts_created"] is False
    assert success_criteria["checkpoint_loaded"] is False
    assert success_criteria["checkpoint_saved"] is False


def test_design_manifest_core_fields():
    design = build_longer_no_checkpoint_training_dry_run_design_v0()
    manifest = design_script.preview_manifest(design)

    assert design["stage"] == "longer_no_checkpoint_training_dry_run_design_v0"
    assert design["previous_stage"] == "few_step_training_dry_run_review_and_training_boundary_v0"
    assert design["step10r_boundary_review_passed"] is True
    assert design["loop_name"] == "masked_covalent_training_loop_v0"
    assert design["next_stage"] == "longer_no_checkpoint_training_dry_run_v0"
    assert design["max_steps"] == 12
    assert design["batch_size"] == 3
    assert design["shuffle"] is False
    assert design["seed"] == 4401
    assert design["optimizer_class"] == OPTIMIZER_CLASS
    assert design["optimizer_lr"] == DEFAULT_LR
    assert design["optimizer_weight_decay"] == DEFAULT_WEIGHT_DECAY
    assert design["mask_schedule"] == MASK_SCHEDULE
    assert design["mask_schedule_length"] == 12
    assert design["mask_counts"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert design["all_checks_passed"] is True
    assert design["recommended_next_step"] == "longer_no_checkpoint_training_dry_run"

    assert manifest["stage"] == "longer_no_checkpoint_training_dry_run_design_v0"
    assert manifest["previous_stage"] == "few_step_training_dry_run_review_and_training_boundary_v0"
    assert manifest["step10r_boundary_review_passed"] is True
    assert manifest["loop_name"] == "masked_covalent_training_loop_v0"
    assert manifest["next_stage"] == "longer_no_checkpoint_training_dry_run_v0"
    assert manifest["max_steps"] == 12
    assert manifest["batch_size"] == 3
    assert manifest["shuffle"] is False
    assert manifest["seed"] == 4401
    assert manifest["optimizer_class"] == "AdamW"
    assert manifest["optimizer_lr"] == 1e-6
    assert manifest["optimizer_weight_decay"] == 0.0
    assert manifest["mask_schedule_length"] == 12
    assert manifest["mask_counts"] == {mask_level: 3 for mask_level in MASK_CYCLE}
    assert manifest["loss_weights"] == LOSS_WEIGHTS
    assert manifest["loss_decrease_required"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["checkpoint_load_allowed"] is False
    assert manifest["checkpoint_save_allowed"] is False
    assert manifest["trainer_fit_allowed"] is False
    assert manifest["training_step_allowed"] is False
    assert manifest["source_modification_allowed"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "longer_no_checkpoint_training_dry_run"


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert design_script.run() == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "longer_no_checkpoint_training_dry_run_design_report.csv")
    schedule_rows = [row for row in rows if row["row_type"] == "schedule"]
    assert len(schedule_rows) == 12
    assert [row["mask_level"] for row in schedule_rows] == MASK_SCHEDULE
    assert all(row["design_status"] == "passed" for row in rows)
    assert all(row["checkpoint_allowed"] == "false" for row in rows)
    assert all(row["model_save_allowed"] == "false" for row in rows)
    assert all(row["trainer_fit_allowed"] == "false" for row in rows)
    assert all(row["training_step_allowed"] == "false" for row in rows)
    assert all(row["source_modification_allowed"] == "false" for row in rows)

    manifest = json.loads(
        (root / "longer_no_checkpoint_training_dry_run_design_preview_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "longer_no_checkpoint_training_dry_run"
    assert manifest["max_steps"] == 12
    assert manifest["mask_schedule_values"] == MASK_SCHEDULE
    assert manifest["loss_decrease_required"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert Path("docs/longer_no_checkpoint_training_dry_run_design_v0_summary.md").is_file()

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


def test_design_sources_do_not_call_training_checkpoint_or_save_apis():
    source_paths = [
        REPO_ROOT / "src" / "covalent_ext" / "longer_no_checkpoint_training_dry_run_design.py",
        REPO_ROOT / "scripts" / "check_longer_no_checkpoint_training_dry_run_design_v0.py",
        REPO_ROOT / "tests" / "test_longer_no_checkpoint_training_dry_run_design_v0.py",
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
