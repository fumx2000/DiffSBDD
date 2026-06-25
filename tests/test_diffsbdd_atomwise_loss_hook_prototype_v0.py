import csv
import json
import shutil
import sys
from pathlib import Path

import pytest
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_diffsbdd_atomwise_loss_hook_prototype_v0 as prototype_script  # noqa: E402
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    AtomwiseProbeCapture,
    PROTECTED_SOURCE_FILES,
    atomwise_probe_context_v0,
    run_atomwise_loss_hook_prototype_v0,
    validate_step10j_outputs_v0,
)


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def prototype_result():
    return run_atomwise_loss_hook_prototype_v0(device="auto", mask_level="A_warhead_only")


def test_validate_step10j_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10j_outputs_v0() is True


def test_context_manager_restores_original_methods_with_fake_model():
    class FakeDynamics:
        def forward(self, x):
            return x + 1

    class FakeDDPM:
        def __init__(self):
            self.dynamics = FakeDynamics()

        def noised_representation(self, xh_lig, xh_pocket, lig_mask, pocket_mask, gamma_t):
            return xh_lig, xh_pocket, xh_lig + 2

    class FakeModel:
        def __init__(self):
            self.ddpm = FakeDDPM()

    model = FakeModel()
    assert "noised_representation" not in model.ddpm.__dict__
    assert "forward" not in model.ddpm.dynamics.__dict__
    capture = AtomwiseProbeCapture()
    x = torch.zeros((2, 4))
    mask = torch.tensor([0, 0])
    with atomwise_probe_context_v0(model, capture):
        model.ddpm.noised_representation(x, x, mask, mask, torch.zeros((1, 1)))
        model.ddpm.dynamics.forward(torch.zeros((2, 4)))
    assert capture.eps_t_lig is not None
    assert capture.net_out_lig is not None
    assert capture.ligand_mask_flat is not None
    assert capture.original_methods_restored is True
    assert "noised_representation" not in model.ddpm.__dict__
    assert "forward" not in model.ddpm.dynamics.__dict__


def test_real_forward_probe_preserves_behavior_and_captures_tensors(prototype_result):
    result = prototype_result
    assert result["smoke_status"] == "passed", result["blocking_reasons"]
    assert result["model_initialized"] is True
    assert result["model_mode"] == "train"
    assert result["forward_no_probe_success"] is True
    assert result["forward_probe_success"] is True
    assert result["default_behavior_preserved"] is True
    assert result["output0_allclose"] is True
    assert result["output1_scalar_allclose"] is True
    assert result["eps_t_lig_captured"] is True
    assert result["net_out_lig_captured"] is True
    assert result["ligand_mask_flat_available"] is True
    assert result["net_out_lig_requires_grad"] is True
    assert result["tensor_first_dim_matches_ligand_atoms"] is True
    assert result["target_mask_nonempty"] is True
    assert result["target_mask_matches_ligand_atoms"] is True
    assert result["residual_x_shape"] == [104, 3]
    assert result["residual_h_shape"] == [104, 11]
    assert result["residual_x_finite"] is True
    assert result["residual_h_finite"] is True
    assert result["can_compute_masked_x_loss_later"] is True
    assert result["can_compute_masked_h_loss_later"] is True
    assert result["original_methods_restored"] is True
    assert result["original_source_files_modified"] is False
    for field in [
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
        "checkpoint_written",
        "archive_created",
    ]:
        assert result[field] is False


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert prototype_script.run(device="auto", mask_level="A_warhead_only") == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_atomwise_loss_hook_prototype_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0"
    assert row["previous_stage"] == "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0"
    assert row["step10j_hook_design_passed"] == "true"
    assert row["model_initialized"] == "true"
    assert row["model_mode"] == "train"
    assert row["forward_no_probe_success"] == "true"
    assert row["forward_probe_success"] == "true"
    assert row["default_behavior_preserved"] == "true"
    assert row["output0_allclose"] == "true"
    assert row["output1_scalar_allclose"] == "true"
    assert row["eps_t_lig_captured"] == "true"
    assert row["net_out_lig_captured"] == "true"
    assert row["ligand_mask_flat_available"] == "true"
    assert row["net_out_lig_requires_grad"] == "true"
    assert row["tensor_first_dim_matches_ligand_atoms"] == "true"
    assert row["target_mask_nonempty"] == "true"
    assert row["residual_x_finite"] == "true"
    assert row["residual_h_finite"] == "true"
    assert row["can_compute_masked_x_loss_later"] == "true"
    assert row["can_compute_masked_h_loss_later"] == "true"
    assert row["original_methods_restored"] == "true"
    assert row["smoke_status"] == "passed"
    for field in [
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
        "checkpoint_written",
        "archive_created",
    ]:
        assert row[field] == "false"

    manifest = json.loads((root / "diffsbdd_atomwise_loss_hook_prototype_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0"
    assert manifest["previous_stage"] == "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0"
    assert manifest["step10j_hook_design_passed"] is True
    assert manifest["default_behavior_preserved"] is True
    assert manifest["output0_allclose"] is True
    assert manifest["output1_scalar_allclose"] is True
    assert manifest["captured_tensor_contract"]["required"] == ["eps_t_lig", "net_out_lig", "ligand_mask_flat"]
    assert manifest["eps_t_lig_shape"] == [104, 14]
    assert manifest["net_out_lig_shape"] == [104, 14]
    assert manifest["ligand_mask_flat_shape"] == [104]
    assert manifest["net_out_lig_requires_grad"] is True
    assert manifest["tensor_first_dim_matches_ligand_atoms"] is True
    assert manifest["target_mask_nonempty"] is True
    assert manifest["residual_x_shape"] == [104, 3]
    assert manifest["residual_h_shape"] == [104, 11]
    assert manifest["can_compute_masked_x_loss_later"] is True
    assert manifest["can_compute_masked_h_loss_later"] is True
    assert manifest["original_methods_restored"] is True
    assert manifest["original_source_files_modified"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "atomwise_loss_hook_shape_sweep_without_backward"
    for field in [
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
        "checkpoint_written",
        "archive_created",
    ]:
        assert manifest[field] is False

    assert Path("docs/diffsbdd_atomwise_loss_hook_prototype_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before
