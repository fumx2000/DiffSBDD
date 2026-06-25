import csv
import json
import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_diffsbdd_atomwise_loss_hook_shape_sweep_v0 as sweep_script  # noqa: E402
from covalent_ext.diffsbdd_atomwise_loss_hook_shape_sweep import (  # noqa: E402
    MASK_LEVELS,
    SAFETY_FALSE_FIELDS,
    validate_step10k_outputs_v0,
    run_atomwise_loss_hook_shape_sweep_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import PROTECTED_SOURCE_FILES  # noqa: E402


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


@pytest.fixture(scope="module")
def sweep_result():
    return run_atomwise_loss_hook_shape_sweep_v0(device="auto")


def test_validate_step10k_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10k_outputs_v0() is True


def test_sweep_covers_all_mask_levels_and_passes(sweep_result):
    rows = sweep_result["rows"]
    summary = sweep_result["summary"]
    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    assert summary["mask_levels"] == MASK_LEVELS
    assert summary["mask_levels_checked"] == 4
    assert summary["all_mask_levels_passed"] is True
    assert summary["all_default_behavior_preserved"] is True
    assert summary["all_atomwise_tensors_captured"] is True
    assert summary["all_residuals_finite"] is True
    assert summary["all_targets_nonempty"] is True
    assert summary["all_methods_restored"] is True
    assert summary["all_sources_unmodified"] is True
    assert summary["all_checks_passed"] is True
    assert summary["recommended_next_step"] == "masked_loss_dry_run_without_backward"
    assert summary["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert summary["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS


def test_each_mask_level_has_valid_probe_shapes_and_safety(sweep_result):
    for row in sweep_result["rows"]:
        mask_level = row["mask_level"]
        assert row["target_atom_count"] == EXPECTED_TARGET_COUNTS[mask_level]
        assert row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[mask_level]
        assert row["ligand_atom_count"] == 104
        assert row["forward_no_probe_success"] is True
        assert row["forward_probe_success"] is True
        assert row["default_behavior_preserved"] is True
        assert row["output0_allclose"] is True
        assert row["output1_scalar_allclose"] is True
        assert row["eps_t_lig_captured"] is True
        assert row["net_out_lig_captured"] is True
        assert row["ligand_mask_flat_available"] is True
        assert row["eps_t_lig_shape"] == [104, 14]
        assert row["net_out_lig_shape"] == [104, 14]
        assert row["ligand_mask_flat_shape"] == [104]
        assert row["net_out_lig_requires_grad"] is True
        assert row["tensor_first_dim_matches_ligand_atoms"] is True
        assert row["target_mask_nonempty"] is True
        assert row["target_mask_matches_ligand_atoms"] is True
        assert row["residual_shape"] == [104, 14]
        assert row["residual_x_shape"] == [104, 3]
        assert row["residual_h_shape"] == [104, 11]
        assert row["residual_x_finite"] is True
        assert row["residual_h_finite"] is True
        assert row["can_compute_masked_x_loss_later"] is True
        assert row["can_compute_masked_h_loss_later"] is True
        assert row["original_methods_restored"] is True
        assert row["original_source_files_modified"] is False
        assert row["smoke_status"] == "passed"
        assert row["blocking_reasons"] == []
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] is False


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert sweep_script.run(device="auto") == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_atomwise_loss_hook_shape_sweep_report.csv")
    assert len(rows) == 4
    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    for row in rows:
        mask_level = row["mask_level"]
        assert row["stage"] == "diffsbdd_atomwise_loss_hook_shape_sweep_without_backward_v0"
        assert row["previous_stage"] == "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0"
        assert row["step10k_hook_prototype_passed"] == "true"
        assert row["target_atom_count"] == str(EXPECTED_TARGET_COUNTS[mask_level])
        assert row["context_atom_count"] == str(EXPECTED_CONTEXT_COUNTS[mask_level])
        assert row["ligand_atom_count"] == "104"
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
        assert row["target_mask_matches_ligand_atoms"] == "true"
        assert row["residual_x_finite"] == "true"
        assert row["residual_h_finite"] == "true"
        assert row["can_compute_masked_x_loss_later"] == "true"
        assert row["can_compute_masked_h_loss_later"] == "true"
        assert row["original_methods_restored"] == "true"
        assert row["original_source_files_modified"] == "false"
        assert row["smoke_status"] == "passed"
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] == "false"

    manifest = json.loads((root / "diffsbdd_atomwise_loss_hook_shape_sweep_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "diffsbdd_atomwise_loss_hook_shape_sweep_without_backward_v0"
    assert manifest["previous_stage"] == "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0"
    assert manifest["step10k_hook_prototype_passed"] is True
    assert manifest["mask_levels_checked"] == 4
    assert manifest["mask_levels"] == MASK_LEVELS
    assert manifest["all_mask_levels_passed"] is True
    assert manifest["all_default_behavior_preserved"] is True
    assert manifest["all_atomwise_tensors_captured"] is True
    assert manifest["all_residuals_finite"] is True
    assert manifest["all_targets_nonempty"] is True
    assert manifest["all_methods_restored"] is True
    assert manifest["all_sources_unmodified"] is True
    assert manifest["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert manifest["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    assert set(manifest["eps_t_lig_shape_by_mask_level"]) == set(MASK_LEVELS)
    assert set(manifest["net_out_lig_shape_by_mask_level"]) == set(MASK_LEVELS)
    assert set(manifest["residual_x_shape_by_mask_level"]) == set(MASK_LEVELS)
    assert set(manifest["residual_h_shape_by_mask_level"]) == set(MASK_LEVELS)
    assert all(manifest["can_compute_masked_x_loss_by_mask_level"].values())
    assert all(manifest["can_compute_masked_h_loss_by_mask_level"].values())
    assert manifest["original_source_files_modified"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "masked_loss_dry_run_without_backward"
    for field_name in SAFETY_FALSE_FIELDS:
        assert manifest[field_name] is False

    assert Path("docs/diffsbdd_atomwise_loss_hook_shape_sweep_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before
