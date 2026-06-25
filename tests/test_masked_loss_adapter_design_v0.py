import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_masked_loss_adapter_design_v0 as design_script  # noqa: E402
from covalent_ext.masked_loss_adapter_design import (  # noqa: E402
    MASK_LEVELS,
    build_masked_loss_adapter_design_v0,
    inspect_masked_loss_candidate_sources_v0,
    validate_step10h_outputs_v0,
)


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step10h_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10h_outputs_v0() is True


def test_source_inspection_finds_loss_error_and_reduction_locations():
    source_info = inspect_masked_loss_candidate_sources_v0()
    assert "lightning_modules.py" in source_info["inspected_source_files"]
    assert source_info["loss_construction_locations"]
    assert source_info["ligand_error_locations"]
    assert source_info["feature_error_locations"]
    assert source_info["coordinate_error_locations"]
    assert source_info["reduction_locations"]
    assert source_info["available_forward_outputs"]["output0"].startswith("per-sample nll")
    assert source_info["atomwise_loss_exposed_by_current_forward"] is False
    assert source_info["nodewise_noise_exposed_by_current_forward"] is False
    assert source_info["can_build_masked_loss_from_current_output_only"] is False


def test_design_contains_components_contracts_and_all_mask_levels():
    source_info = inspect_masked_loss_candidate_sources_v0()
    design = build_masked_loss_adapter_design_v0(source_info)
    assert design["design_status"] == "ready"
    assert design["proposed_loss_components"]
    assert "loss_original = nll.mean()" in design["proposed_loss_components"]
    assert "loss_masked_x = masked coordinate denoising loss over ligand target atoms" in design["proposed_loss_components"]
    assert set(design["mask_level_loss_policy"]) == set(MASK_LEVELS)
    assert design["adapter_input_contract"]
    assert design["adapter_output_contract"]
    assert "loss_total" in design["adapter_output_contract"]
    assert design["recommended_next_step"] == "diffsbdd_atomwise_loss_hook_design_without_behavior_change"


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert design_script.run() == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "masked_loss_adapter_design_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "masked_loss_adapter_design_without_diffsbdd_modification_v0"
    assert row["step10h_backward_smoke_passed"] == "true"
    assert row["source_inspection_status"] == "passed"
    assert row["design_status"] == "ready"
    assert row["atomwise_loss_exposed_by_current_forward"] == "false"
    assert row["nodewise_noise_exposed_by_current_forward"] == "false"
    assert row["can_build_masked_loss_from_current_output_only"] == "false"
    assert row["current_forward_is_mask_aware"] == "false"
    assert row["current_forward_is_full_ligand_objective"] == "true"
    assert row["must_modify_loss_for_masked_training"] == "true"
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
    manifest = json.loads((root / "masked_loss_adapter_design_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "masked_loss_adapter_design_without_diffsbdd_modification_v0"
    assert manifest["previous_stage"] == "diffsbdd_backward_smoke_without_checkpoint_v0"
    assert manifest["step10h_backward_smoke_passed"] is True
    assert manifest["atomwise_loss_exposed_by_current_forward"] is False
    assert manifest["nodewise_noise_exposed_by_current_forward"] is False
    assert manifest["can_build_masked_loss_from_current_output_only"] is False
    assert manifest["current_forward_is_mask_aware"] is False
    assert manifest["current_forward_is_full_ligand_objective"] is True
    assert set(manifest["mask_level_loss_policy"]) == set(MASK_LEVELS)
    assert manifest["adapter_input_contract"]
    assert manifest["adapter_output_contract"]
    assert manifest["checkpoint_loaded"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["training_step_called"] is False
    assert manifest["backward_called"] is False
    assert manifest["optimizer_step_executed"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["training_executed"] is False
    assert manifest["real_finetune_executed"] is False
    assert manifest["checkpoint_written"] is False
    assert manifest["archive_created"] is False
    assert manifest["recommended_next_step"] == "diffsbdd_atomwise_loss_hook_design_without_behavior_change"
    assert Path("docs/masked_loss_adapter_design_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not (REPO_ROOT / "equivariant_diffusion").joinpath("__definitely_modified_by_test__").exists()
