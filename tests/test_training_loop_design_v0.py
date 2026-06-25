import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_training_loop_design_v0 as design_script  # noqa: E402
from covalent_ext.training_loop_design import (  # noqa: E402
    LOSS_WEIGHTS,
    MASK_LEVELS,
    build_checkpoint_boundary_policy_v0,
    build_loss_policy_v0,
    build_mask_schedule_policy_v0,
    build_minimal_training_loop_plan_v0,
    build_training_loop_contract_v0,
    build_training_loop_design_v0,
    validate_step10o_outputs_v0,
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


def test_validate_step10o_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10o_outputs_v0() is True


def test_contract_contains_required_allowed_forbidden_actions():
    contract = build_training_loop_contract_v0()
    allowed = set(contract["allowed_actions_next_stage"])
    forbidden = set(contract["forbidden_actions_next_stage"])

    assert contract["loop_name"] == "masked_covalent_training_loop_v0"
    assert contract["intended_next_stage"] == "few_step_training_dry_run_no_checkpoint"
    for item in [
        "instantiate model",
        "build optimizer",
        "iterate over dataloader",
        "compute masked loss",
        "backward",
        "optimizer.step",
        "log scalar metrics",
    ]:
        assert item in allowed
    for item in [
        "trainer.fit",
        "training_step",
        "checkpoint saving",
        "torch.save",
        "model saving",
        "source modification",
    ]:
        assert item in forbidden
    assert ".pt" in contract["forbidden_outputs_next_stage"]
    assert ".pkl" in contract["forbidden_outputs_next_stage"]
    assert ".lmdb" in contract["forbidden_outputs_next_stage"]
    assert ".tar" in contract["forbidden_outputs_next_stage"]
    assert ".zip" in contract["forbidden_outputs_next_stage"]
    assert ".tgz" in contract["forbidden_outputs_next_stage"]


def test_mask_schedule_loss_and_checkpoint_policies():
    mask_schedule = build_mask_schedule_policy_v0()
    loss_policy = build_loss_policy_v0()
    checkpoint_policy = build_checkpoint_boundary_policy_v0()

    assert mask_schedule["schedule_name"] == "balanced_A_B_B2_C_cycle"
    assert mask_schedule["mask_order"] == MASK_LEVELS
    assert mask_schedule["max_steps_initial_dry_run"] <= 8
    assert mask_schedule["batch_size"] == 3
    assert mask_schedule["shuffle"] is False
    assert mask_schedule["not_for_real_training"] is True
    assert loss_policy["default_weights"] == LOSS_WEIGHTS
    assert loss_policy["current_step_auxiliary_losses_enabled"] is False
    assert checkpoint_policy["current_stage_checkpoint_allowed"] is False
    assert checkpoint_policy["next_few_step_dry_run_checkpoint_allowed"] is False
    assert "torch.save" in checkpoint_policy["checkpoint_forbidden_patterns"]
    assert ".pt" in checkpoint_policy["checkpoint_forbidden_patterns"]


def test_training_loop_design_manifest_core_fields(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    design = build_training_loop_design_v0()
    manifest = design_script.preview_manifest(design)

    assert manifest["stage"] == "training_loop_design_without_checkpoint_v0"
    assert manifest["previous_stage"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
    assert manifest["step10o_optimizer_smoke_passed"] is True
    assert manifest["loop_name"] == "masked_covalent_training_loop_v0"
    assert manifest["intended_next_stage"] == "few_step_training_dry_run_no_checkpoint"
    assert manifest["mask_schedule_name"] == "balanced_A_B_B2_C_cycle"
    assert manifest["mask_order"] == MASK_LEVELS
    assert manifest["max_steps_initial_dry_run"] <= 8
    assert manifest["batch_size"] == 3
    assert manifest["shuffle"] is False
    assert manifest["loss_weights"] == LOSS_WEIGHTS
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["trainer_fit_allowed"] is False
    assert manifest["training_step_allowed"] is False
    assert manifest["source_modification_allowed"] is False
    assert "max_steps hard cap" in manifest["stop_conditions"]
    assert "finite loss required" in manifest["stop_conditions"]
    assert "step" in manifest["required_logging_fields"]
    assert "loss_total" in manifest["required_logging_fields"]
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "few_step_training_dry_run_no_checkpoint"


def test_plan_contains_expected_stages():
    plan = build_minimal_training_loop_plan_v0()
    stage_names = [row["stage_name"] for row in plan]
    assert stage_names == [
        "preflight_validate_inputs",
        "instantiate_model_no_checkpoint",
        "build_optimizer",
        "prepare_mask_schedule",
        "run_few_step_dry_loop",
        "collect_loss_metrics",
        "collect_gradient_metrics",
        "collect_parameter_update_metrics",
        "enforce_stop_conditions",
        "write_report_only",
        "verify_no_checkpoint_or_model_saved",
        "verify_sources_unmodified",
    ]
    assert [row["order"] for row in plan] == list(range(1, len(plan) + 1))


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert design_script.run() == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "training_loop_design_report.csv")
    assert len(rows) == 12
    assert rows[0]["stage"] == "training_loop_design_without_checkpoint_v0"
    assert rows[0]["previous_stage"] == "masked_loss_optimizer_smoke_one_step_no_checkpoint_v0"
    assert rows[0]["step10o_optimizer_smoke_passed"] == "true"
    for row in rows:
        assert row["checkpoint_allowed"] == "false"
        assert row["model_save_allowed"] == "false"
        assert row["trainer_fit_allowed"] == "false"
        assert row["training_step_allowed"] == "false"
        assert row["source_modification_allowed"] == "false"
        assert row["design_status"] == "passed"
        assert row["blocking_reasons"] == ""

    manifest = json.loads((root / "training_loop_design_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["recommended_next_step"] == "few_step_training_dry_run_no_checkpoint"
    assert manifest["checkpoint_allowed"] is False
    assert manifest["model_save_allowed"] is False
    assert manifest["trainer_fit_allowed"] is False
    assert manifest["training_step_allowed"] is False
    assert manifest["source_modification_allowed"] is False
    assert Path("docs/training_loop_design_v0_summary.md").is_file()

    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before


def test_design_sources_do_not_call_training_or_save_apis():
    source_paths = [
        REPO_ROOT / "src" / "covalent_ext" / "training_loop_design.py",
        REPO_ROOT / "scripts" / "check_training_loop_design_v0.py",
        REPO_ROOT / "tests" / "test_training_loop_design_v0.py",
    ]
    forbidden_call_tokens = [
        "." + "backward" + "(",
        "optimizer" + "." + "step" + "(",
        "trainer" + "." + "fit" + "(",
        "." + "fit" + "(",
        "training" + "_step" + "(",
        "torch" + "." + "save" + "(",
        "save" + "_checkpoint" + "(",
        "load" + "_from" + "_checkpoint" + "(",
    ]
    for source_path in source_paths:
        text = source_path.read_text(encoding="utf-8")
        for token in forbidden_call_tokens:
            assert token not in text
