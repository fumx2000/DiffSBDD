import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_diffsbdd_forward_loss_semantics_v0 as semantics_script  # noqa: E402
from covalent_ext.diffsbdd_loss_semantics import (  # noqa: E402
    MASK_LEVELS,
    assess_forward_loss_training_readiness_v0,
    inspect_diffsbdd_loss_semantics_sources_v0,
    run_forward_output_semantics_probe_v0,
    validate_step10f_outputs_v0,
)


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_source_inspection_finds_forward_training_step_and_en_diffusion_forward():
    source_info = inspect_diffsbdd_loss_semantics_sources_v0()
    assert "lightning_modules.py" in source_info["inspected_source_files"]
    assert source_info["forward_signature"] == "(self, data)"
    assert source_info["training_step_signature"].startswith("(self, data")
    assert source_info["en_diffusion_forward_signature"] == "(self, ligand, pocket, return_info=False)"
    assert source_info["located_forward_return_lines"]
    assert source_info["located_training_step_loss_lines"]
    assert source_info["located_en_diffusion_loss_lines"]
    assert source_info["training_step_uses_forward_output0"] is True
    assert source_info["training_step_reduction_semantics"] == "nll.mean(0)"


def test_forward_probe_covers_four_mask_levels_and_preserves_safety_flags(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10f_outputs_v0() is True
    probe = run_forward_output_semantics_probe_v0(device="auto")
    assert probe["probe_status"] == "passed"
    assert set(probe["output0_shape_by_mask_level"]) == set(MASK_LEVELS)
    assert all(shape == [3] for shape in probe["output0_shape_by_mask_level"].values())
    assert all(value is True for value in probe["output0_finite_by_mask_level"].values())
    assert all(probe["output1_keys_by_mask_level"][mask_level] for mask_level in MASK_LEVELS)
    for finite_by_key in probe["output1_finite_by_mask_level"].values():
        assert finite_by_key
        assert all(value is True for value in finite_by_key.values())
    for field in [
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
    ]:
        assert probe[field] is False


def test_assessment_marks_output0_loss_like_and_forward_not_mask_aware(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_info = inspect_diffsbdd_loss_semantics_sources_v0()
    probe = run_forward_output_semantics_probe_v0(device="auto")
    assessment = assess_forward_loss_training_readiness_v0(source_info, probe)
    assert assessment["output0_is_loss_like"] is True
    assert assessment["output0_is_per_sample_vector"] is True
    assert assessment["recommended_loss_reduction"] == "mean"
    assert assessment["training_step_uses_forward_output0"] is True
    assert assessment["output1_is_diagnostics"] is True
    assert assessment["mask_consumption_status"] in {"consumed_by_sampling_only", "not_consumed"}
    assert assessment["lig_fixed_consumed_by_forward"] is False
    assert assessment["generation_mask_consumed_by_forward"] is False
    assert assessment["target_mask_consumed_by_forward"] is False
    assert assessment["current_forward_is_mask_aware"] is False
    assert assessment["current_forward_is_full_ligand_objective"] is True
    assert assessment["can_do_backward_smoke_next"] is True
    assert assessment["must_modify_loss_for_masked_training"] is True


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert semantics_script.run() == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_forward_loss_semantics_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "diffsbdd_forward_loss_semantics_review_without_backward_v0"
    assert row["source_inspection_status"] == "passed"
    assert row["probe_status"] == "passed"
    assert row["output0_is_loss_like"] == "true"
    assert row["output0_is_per_sample_vector"] == "true"
    assert row["recommended_loss_reduction"] == "mean"
    assert row["training_step_uses_forward_output0"] == "true"
    assert row["output1_is_diagnostics"] == "true"
    assert row["current_forward_is_mask_aware"] == "false"
    assert row["current_forward_is_full_ligand_objective"] == "true"
    assert row["must_modify_loss_for_masked_training"] == "true"
    assert row["checkpoint_loaded"] == "false"
    assert row["checkpoint_saved"] == "false"
    assert row["training_step_called"] == "false"
    assert row["backward_called"] == "false"
    assert row["optimizer_step_executed"] == "false"
    assert row["trainer_fit_called"] == "false"
    assert row["training_executed"] == "false"
    assert row["real_finetune_executed"] == "false"
    manifest = json.loads((root / "diffsbdd_forward_loss_semantics_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "diffsbdd_forward_loss_semantics_review_without_backward_v0"
    assert manifest["previous_stage"] == "diffsbdd_forward_mask_level_sweep_without_checkpoint_v0"
    assert manifest["step10f_forward_sweep_passed"] is True
    assert manifest["output0_is_loss_like"] is True
    assert manifest["output0_is_per_sample_vector"] is True
    assert manifest["can_do_backward_smoke_next"] is True
    assert manifest["current_forward_is_mask_aware"] is False
    assert manifest["archive_created"] is False
    assert Path("docs/diffsbdd_forward_loss_semantics_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not (REPO_ROOT / "equivariant_diffusion").joinpath("__definitely_modified_by_test__").exists()
