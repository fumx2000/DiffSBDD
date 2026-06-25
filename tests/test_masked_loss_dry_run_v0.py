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

import check_masked_loss_dry_run_v0 as dry_script  # noqa: E402
from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    EXPECTED_CONTEXT_COUNTS,
    EXPECTED_TARGET_COUNTS,
    MASK_LEVELS,
    SAFETY_FALSE_FIELDS,
    compute_masked_loss_components_v0,
    run_masked_loss_dry_run_v0,
    summarize_loss_components_v0,
    validate_step10l_outputs_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import PROTECTED_SOURCE_FILES  # noqa: E402


def _copy_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def dry_run_result():
    return run_masked_loss_dry_run_v0(device="auto")


def test_validate_step10l_outputs_v0_success(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    assert validate_step10l_outputs_v0() is True


def test_compute_masked_loss_components_nonempty_and_empty_masks():
    output0 = torch.tensor([1.0, 2.0], requires_grad=True)
    eps = torch.arange(30, dtype=torch.float32).view(3, 10)
    net = torch.zeros_like(eps, requires_grad=True)
    target = torch.tensor([True, False, True])
    components = compute_masked_loss_components_v0(output0, eps, net, target)
    summary = summarize_loss_components_v0(components)
    assert components["dry_run_status"] == "passed"
    assert components["residual_x"].shape == (3, 3)
    assert components["residual_h"].shape == (3, 7)
    assert summary["loss_original_finite"] is True
    assert summary["loss_masked_x_finite"] is True
    assert summary["loss_masked_h_finite"] is True
    assert summary["loss_total_dry_finite"] is True
    assert summary["loss_total_dry_requires_grad"] is True

    blocked = compute_masked_loss_components_v0(output0, eps, net, torch.zeros(3, dtype=torch.bool))
    assert blocked["dry_run_status"] == "blocked"
    assert "target_mask_empty" in blocked["blocking_reasons"]


def test_dry_run_covers_all_mask_levels_and_losses_are_valid(dry_run_result):
    rows = dry_run_result["rows"]
    summary = dry_run_result["summary"]
    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    assert summary["mask_levels"] == MASK_LEVELS
    assert summary["mask_levels_checked"] == 4
    assert summary["all_mask_levels_passed"] is True
    assert summary["all_loss_scalars_finite"] is True
    assert summary["all_loss_total_requires_grad"] is True
    assert summary["all_target_masks_nonempty"] is True
    assert summary["all_expected_target_counts"] is True
    assert summary["all_expected_context_counts"] is True
    assert summary["all_sources_unmodified"] is True
    assert summary["all_safety_flags_false"] is True
    assert summary["all_checks_passed"] is True
    assert summary["recommended_next_step"] == "masked_loss_backward_smoke_without_optimizer"
    assert summary["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert summary["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    assert all(summary["loss_total_dry_requires_grad_by_mask_level"].values())
    assert summary["c_level_full_ligand_target_expected"] is True


def test_each_mask_level_has_expected_counts_masks_and_safety(dry_run_result):
    for row in dry_run_result["rows"]:
        mask_level = row["mask_level"]
        assert row["target_atom_count"] == EXPECTED_TARGET_COUNTS[mask_level]
        assert row["context_atom_count"] == EXPECTED_CONTEXT_COUNTS[mask_level]
        assert row["ligand_atom_count"] == 104
        assert row["eps_t_lig_shape"] == [104, 14]
        assert row["net_out_lig_shape"] == [104, 14]
        assert row["residual_x_shape"] == [104, 3]
        assert row["residual_h_shape"] == [104, 11]
        assert row["loss_original_finite"] is True
        assert row["loss_masked_x_finite"] is True
        assert row["loss_masked_h_finite"] is True
        assert row["loss_total_dry_finite"] is True
        assert row["loss_total_dry_requires_grad"] is True
        assert row["loss_masked_x_requires_grad"] is True
        assert row["loss_masked_h_requires_grad"] is True
        assert row["target_mask_nonempty"] is True
        assert row["target_mask_matches_ligand_atoms"] is True
        assert row["dry_run_status"] == "passed"
        if mask_level == "C_scaffold_linker_warhead":
            assert row["used_target_mask_not_full_ligand"] is False
            assert row["c_level_full_ligand_target_expected"] is True
        else:
            assert row["used_target_mask_not_full_ligand"] is True
            assert row["c_level_full_ligand_target_expected"] is False
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] is False


def test_script_writes_report_manifest_summary_and_preserves_sources(tmp_path, monkeypatch):
    _copy_workspace(tmp_path, monkeypatch)
    source_snapshots = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }

    assert dry_script.run(device="auto") == 0

    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "masked_loss_dry_run_report.csv")
    assert len(rows) == 4
    assert [row["mask_level"] for row in rows] == MASK_LEVELS
    for row in rows:
        mask_level = row["mask_level"]
        assert row["stage"] == "masked_loss_dry_run_without_backward_v0"
        assert row["previous_stage"] == "diffsbdd_atomwise_loss_hook_shape_sweep_without_backward_v0"
        assert row["step10l_hook_shape_sweep_passed"] == "true"
        assert row["target_atom_count"] == str(EXPECTED_TARGET_COUNTS[mask_level])
        assert row["context_atom_count"] == str(EXPECTED_CONTEXT_COUNTS[mask_level])
        assert row["ligand_atom_count"] == "104"
        assert row["loss_original_finite"] == "true"
        assert row["loss_masked_x_finite"] == "true"
        assert row["loss_masked_h_finite"] == "true"
        assert row["loss_total_dry_finite"] == "true"
        assert row["loss_total_dry_requires_grad"] == "true"
        assert row["target_mask_nonempty"] == "true"
        assert row["target_mask_matches_ligand_atoms"] == "true"
        assert row["dry_run_status"] == "passed"
        for field_name in SAFETY_FALSE_FIELDS:
            assert row[field_name] == "false"

    manifest = json.loads((root / "masked_loss_dry_run_preview_manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "masked_loss_dry_run_without_backward_v0"
    assert manifest["previous_stage"] == "diffsbdd_atomwise_loss_hook_shape_sweep_without_backward_v0"
    assert manifest["step10l_hook_shape_sweep_passed"] is True
    assert manifest["mask_levels_checked"] == 4
    assert manifest["mask_levels"] == MASK_LEVELS
    assert manifest["all_mask_levels_passed"] is True
    assert manifest["all_loss_scalars_finite"] is True
    assert manifest["all_loss_total_requires_grad"] is True
    assert manifest["all_target_masks_nonempty"] is True
    assert manifest["all_expected_target_counts"] is True
    assert manifest["all_expected_context_counts"] is True
    assert manifest["target_atom_count_by_mask_level"] == EXPECTED_TARGET_COUNTS
    assert manifest["context_atom_count_by_mask_level"] == EXPECTED_CONTEXT_COUNTS
    assert all(manifest["loss_total_dry_requires_grad_by_mask_level"].values())
    assert manifest["used_target_mask_not_full_ligand_by_mask_level"]["A_warhead_only"] is True
    assert manifest["used_target_mask_not_full_ligand_by_mask_level"]["B_linker_warhead"] is True
    assert manifest["used_target_mask_not_full_ligand_by_mask_level"]["B2_scaffold_warhead"] is True
    assert manifest["used_target_mask_not_full_ligand_by_mask_level"]["C_scaffold_linker_warhead"] is False
    assert manifest["c_level_full_ligand_target_expected"] is True
    assert manifest["original_source_files_modified"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "masked_loss_backward_smoke_without_optimizer"
    for field_name in SAFETY_FALSE_FIELDS:
        assert manifest[field_name] is False

    assert Path("docs/masked_loss_dry_run_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
    for rel_path, before in source_snapshots.items():
        assert (REPO_ROOT / rel_path).read_text(encoding="utf-8") == before
