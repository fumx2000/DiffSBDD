import argparse
import csv
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_diffsbdd_forward_mask_level_sweep_v0 as sweep_script  # noqa: E402
import covalent_ext.diffsbdd_forward_mask_sweep as sweep_module  # noqa: E402
from covalent_ext.diffsbdd_forward_mask_sweep import (  # noqa: E402
    MASK_LEVELS,
    run_diffsbdd_forward_mask_level_sweep_v0,
    validate_step10e_outputs_v0,
)


EXPECTED_TARGET_COUNTS = {
    "A_warhead_only": 12,
    "B_linker_warhead": 30,
    "B2_scaffold_warhead": 86,
    "C_scaffold_linker_warhead": 104,
}
EXPECTED_CONTEXT_COUNTS = {
    "A_warhead_only": 92,
    "B_linker_warhead": 74,
    "B2_scaffold_warhead": 18,
    "C_scaffold_linker_warhead": 0,
}


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        device="auto",
        output_report_csv=root / "diffsbdd_forward_mask_level_sweep_report.csv",
        output_manifest_json=root / "diffsbdd_forward_mask_level_sweep_preview_manifest.json",
        output_md=Path("docs/diffsbdd_forward_mask_level_sweep_v0_summary.md"),
    )


def _fake_row(mask_level, passed=True):
    return {
        "requested_device": "auto",
        "resolved_device": "cpu",
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": "",
        "mask_level": mask_level,
        "batch_size": 3,
        "model_class_name": "LigandPocketDDPM",
        "model_initialized": True,
        "parameter_count": 4822706,
        "trainable_parameter_count": 4822205,
        "selected_forward_call_style": "LigandPocketDDPM.forward(data_batch)",
        "ligand_x_shape": [104, 3],
        "ligand_one_hot_shape": [104, 11],
        "pocket_x_shape": [5642, 3],
        "pocket_one_hot_shape": [5642, 11],
        "ligand_mask_shape": [104],
        "pocket_mask_shape": [5642],
        "target_atom_count": EXPECTED_TARGET_COUNTS[mask_level],
        "context_atom_count": EXPECTED_CONTEXT_COUNTS[mask_level],
        "forward_called": True,
        "forward_success": passed,
        "output_type": "tuple" if passed else "",
        "output_keys": ["0", "1"] if passed else [],
        "tensor_output_shapes": {"output.0": [3]} if passed else {},
        "finite_tensor_outputs": passed,
        "scalar_loss_like_output_finite": passed,
        "forward_exception_type": "" if passed else "RuntimeError",
        "forward_exception_message": "" if passed else "synthetic failure",
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "smoke_status": "passed" if passed else "blocked",
        "blocking_reasons": [] if passed else ["forward_failed:RuntimeError"],
    }


def test_step10e_outputs_are_valid_for_sweep(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10e_outputs_v0() is True


def test_sweep_runs_four_mask_levels_and_preserves_safety_flags(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    result = run_diffsbdd_forward_mask_level_sweep_v0(device="auto")
    assert result["stage"] == "diffsbdd_forward_mask_level_sweep_without_checkpoint_v0"
    assert result["previous_stage"] == "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0"
    assert result["mask_levels_checked"] == 4
    assert result["report_row_count"] == 4
    assert {row["mask_level"] for row in result["rows"]} == set(MASK_LEVELS)
    assert result["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert result["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    if result["all_mask_levels_passed"]:
        assert result["recommended_next_step"] == "diffsbdd_forward_loss_semantics_review_without_backward"
        assert all(row["forward_called"] is True for row in result["rows"])
        assert all(row["forward_success"] is True for row in result["rows"])
        assert all(row["finite_tensor_outputs"] is True for row in result["rows"])
        assert all(row["scalar_loss_like_output_finite"] is True for row in result["rows"])
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
        assert result[field] is False


def test_blocked_forward_keeps_blocking_reason_and_manual_next_step(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)

    def fake_forward(device="auto", mask_level="A_warhead_only"):
        return _fake_row(mask_level, passed=mask_level != "B2_scaffold_warhead")

    monkeypatch.setattr(sweep_module, "run_diffsbdd_single_batch_forward_shape_smoke_v0", fake_forward)
    result = run_diffsbdd_forward_mask_level_sweep_v0(device="auto")
    assert result["all_mask_levels_passed"] is False
    assert result["sweep_status"] == "blocked"
    assert result["recommended_next_step"] == "manual_forward_mask_sweep_review"
    blocked = [row for row in result["rows"] if row["mask_level"] == "B2_scaffold_warhead"][0]
    assert blocked["smoke_status"] == "blocked"
    assert blocked["blocking_reasons"]


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)

    def fake_sweep(device="auto"):
        rows = [_fake_row(mask_level, passed=True) for mask_level in MASK_LEVELS]
        return {
            "stage": sweep_module.STAGE,
            "previous_stage": sweep_module.PREVIOUS_STAGE,
            "step10e_single_forward_passed": True,
            "requested_device": "auto",
            "resolved_device": "cpu",
            "cuda_available": False,
            "cuda_device_count": 0,
            "cuda_device_name": "",
            "model_class_name": "LigandPocketDDPM",
            "selected_forward_call_style": "LigandPocketDDPM.forward(data_batch)",
            "mask_levels_checked": 4,
            "report_row_count": 4,
            "all_mask_levels_passed": True,
            "sweep_status": "passed",
            "rows": rows,
            "target_atom_count_by_mask_level": EXPECTED_TARGET_COUNTS,
            "context_atom_count_by_mask_level": EXPECTED_CONTEXT_COUNTS,
            "forward_success_by_mask_level": {mask_level: True for mask_level in MASK_LEVELS},
            "finite_tensor_outputs_by_mask_level": {mask_level: True for mask_level in MASK_LEVELS},
            "scalar_loss_like_output_finite_by_mask_level": {mask_level: True for mask_level in MASK_LEVELS},
            "output_type_by_mask_level": {mask_level: "tuple" for mask_level in MASK_LEVELS},
            "tensor_output_shapes_by_mask_level": {mask_level: {"output.0": [3]} for mask_level in MASK_LEVELS},
            "checkpoint_loaded": False,
            "checkpoint_saved": False,
            "training_step_called": False,
            "backward_called": False,
            "optimizer_step_executed": False,
            "trainer_fit_called": False,
            "training_executed": False,
            "real_finetune_executed": False,
            "archive_created": False,
            "all_checks_passed": True,
            "recommended_next_step": "diffsbdd_forward_loss_semantics_review_without_backward",
        }

    monkeypatch.setattr(sweep_script, "run_diffsbdd_forward_mask_level_sweep_v0", fake_sweep)
    assert sweep_script.run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_forward_mask_level_sweep_report.csv")
    assert len(rows) == 4
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    assert all(row["smoke_status"] == "passed" for row in rows)
    assert all(row["forward_called"] == "true" for row in rows)
    assert all(row["forward_success"] == "true" for row in rows)
    assert all(row["finite_tensor_outputs"] == "true" for row in rows)
    assert all(row["scalar_loss_like_output_finite"] == "true" for row in rows)
    for row in rows:
        assert int(row["target_atom_count"]) == EXPECTED_TARGET_COUNTS[row["mask_level"]]
        assert int(row["context_atom_count"]) == EXPECTED_CONTEXT_COUNTS[row["mask_level"]]
        assert row["checkpoint_loaded"] == "false"
        assert row["checkpoint_saved"] == "false"
        assert row["training_step_called"] == "false"
        assert row["backward_called"] == "false"
        assert row["optimizer_step_executed"] == "false"
        assert row["trainer_fit_called"] == "false"
        assert row["training_executed"] == "false"
        assert row["real_finetune_executed"] == "false"
    preview = json.loads((root / "diffsbdd_forward_mask_level_sweep_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "diffsbdd_forward_mask_level_sweep_without_checkpoint_v0"
    assert preview["previous_stage"] == "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0"
    assert preview["step10e_single_forward_passed"] is True
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 4
    assert preview["all_mask_levels_passed"] is True
    assert preview["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert preview["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    assert preview["checkpoint_loaded"] is False
    assert preview["checkpoint_saved"] is False
    assert preview["training_step_called"] is False
    assert preview["backward_called"] is False
    assert preview["optimizer_step_executed"] is False
    assert preview["trainer_fit_called"] is False
    assert preview["training_executed"] is False
    assert preview["real_finetune_executed"] is False
    assert preview["archive_created"] is False
    assert preview["recommended_next_step"] == "diffsbdd_forward_loss_semantics_review_without_backward"
    assert Path("docs/diffsbdd_forward_mask_level_sweep_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    assert not (REPO_ROOT / "equivariant_diffusion").joinpath("__definitely_modified_by_test__").exists()
