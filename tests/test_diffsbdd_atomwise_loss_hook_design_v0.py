import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_diffsbdd_atomwise_loss_hook_design_v0 as hook_script  # noqa: E402
from covalent_ext.diffsbdd_atomwise_loss_hook_design import (  # noqa: E402
    MASK_LEVELS,
    SOURCE_FILES,
    build_atomwise_loss_hook_design_v0,
    inspect_atomwise_hook_candidate_sources_v0,
    validate_step10i_outputs_v0,
)


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step10i_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10i_outputs_v0() is True


def test_source_inspection_finds_atomwise_hook_candidates():
    source_info = inspect_atomwise_hook_candidate_sources_v0()
    assert "equivariant_diffusion/en_diffusion.py" in source_info["inspected_source_files"]
    assert "equivariant_diffusion/conditional_model.py" in source_info["inspected_source_files"]
    assert source_info["eps_t_lig_locations"]
    assert source_info["net_out_lig_locations"]
    assert source_info["squared_error_locations"] or source_info["error_t_lig_locations"]
    assert source_info["reduction_locations"]
    assert source_info["coordinate_channel_locations"]
    assert source_info["feature_channel_locations"]
    assert source_info["ligand_mask_locations"]
    assert source_info["candidate_hook_points"]
    assert source_info["preferred_hook_point"].startswith("B.")
    assert source_info["whether_original_forward_return_should_change"] is False
    assert source_info["whether_checkpoint_compatibility_should_be_affected"] is False


def test_design_contracts_preserve_behavior_and_cover_masks():
    source_info = inspect_atomwise_hook_candidate_sources_v0()
    design = build_atomwise_loss_hook_design_v0(source_info)
    assert design["design_status"] == "ready"
    assert design["preferred_hook_point"] == source_info["preferred_hook_point"]
    assert design["recommended_hook_strategy"] == "optional_no_behavior_change_atomwise_probe_for_eps_t_lig_and_net_out_lig"
    assert design["captured_tensor_contract"]["required"] == ["eps_t_lig", "net_out_lig", "ligand_mask_flat"]
    assert design["tensor_alignment_contract"]
    assert design["behavior_preservation_contract"]
    assert any("forward returns exactly the original tuple" in item for item in design["behavior_preservation_contract"])
    assert design["checkpoint_compatibility_contract"]
    assert design["masked_loss_readiness_after_hook"]["can_capture_atomwise_noise_after_hook"] is True
    assert design["masked_loss_readiness_after_hook"]["can_compute_masked_x_loss_after_hook"] is True
    assert design["masked_loss_readiness_after_hook"]["can_compute_masked_h_loss_after_hook"] is True
    assert design["recommended_next_step"] == "atomwise_loss_hook_prototype_without_behavior_change"
    assert set(MASK_LEVELS) == {"A_warhead_only", "B_linker_warhead", "B2_scaffold_warhead", "C_scaffold_linker_warhead"}


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert hook_script.run() == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_atomwise_loss_hook_design_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0"
    assert row["previous_stage"] == "masked_loss_adapter_design_without_diffsbdd_modification_v0"
    assert row["step10i_masked_loss_design_passed"] == "true"
    assert row["source_inspection_status"] == "passed"
    assert row["design_status"] == "ready"
    assert row["eps_t_lig_found"] == "true"
    assert row["net_out_lig_found"] == "true"
    assert row["squared_error_found"] == "true"
    assert row["reduction_found"] == "true"
    assert row["original_forward_return_should_change"] == "false"
    assert row["checkpoint_compatibility_affected"] == "false"
    assert row["can_preserve_default_behavior"] == "true"
    assert row["can_capture_atomwise_noise_after_hook"] == "true"
    assert row["can_compute_masked_x_loss_after_hook"] == "true"
    assert row["can_compute_masked_h_loss_after_hook"] == "true"
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

    manifest = json.loads((root / "diffsbdd_atomwise_loss_hook_design_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0"
    assert manifest["previous_stage"] == "masked_loss_adapter_design_without_diffsbdd_modification_v0"
    assert manifest["step10i_masked_loss_design_passed"] is True
    assert manifest["design_status"] == "ready"
    assert manifest["can_preserve_default_behavior"] is True
    assert manifest["original_forward_return_should_change"] is False
    assert manifest["checkpoint_compatibility_affected"] is False
    assert manifest["can_capture_atomwise_noise_after_hook"] is True
    assert manifest["can_compute_masked_x_loss_after_hook"] is True
    assert manifest["can_compute_masked_h_loss_after_hook"] is True
    assert manifest["captured_tensor_contract"]["required"] == ["eps_t_lig", "net_out_lig", "ligand_mask_flat"]
    assert manifest["tensor_alignment_contract"]
    assert manifest["behavior_preservation_contract"]
    assert manifest["checkpoint_compatibility_contract"]
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "atomwise_loss_hook_prototype_without_behavior_change"
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

    assert Path("docs/diffsbdd_atomwise_loss_hook_design_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before
