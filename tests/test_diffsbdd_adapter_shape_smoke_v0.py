import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import pytest
import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_diffsbdd_adapter_shape_smoke_v0 import MASK_LEVELS, run  # noqa: E402
from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.diffsbdd_input_adapter import build_diffsbdd_like_input_from_covalent_v0  # noqa: E402
from covalent_ext.diffsbdd_shape_smoke import (  # noqa: E402
    EXPECTED_DIFFSBDD_BATCH_FIELDS,
    EXPECTED_LIGAND_DICT_FIELDS,
    EXPECTED_POCKET_DICT_FIELDS,
    build_diffsbdd_batch_fields_v0,
    build_ligand_pocket_dicts_for_diffsbdd_v0,
    summarize_diffsbdd_shape_smoke_v0,
    validate_diffsbdd_adapter_shape_smoke_v0,
)
from covalent_ext.model_input_adapter import build_covalent_model_input_v0  # noqa: E402
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn  # noqa: E402


@pytest.fixture(autouse=True)
def _fixture_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _batch():
    dataset = CovalentNPZDataset("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    return next(iter(loader))


def _shape_smoke(mask_level="A_warhead_only"):
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level=mask_level)
    model_input = build_covalent_model_input_v0(adapted)
    diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
    batch_fields = build_diffsbdd_batch_fields_v0(diffsbdd_like)
    return batch_fields, build_ligand_pocket_dicts_for_diffsbdd_v0(batch_fields)


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        sample_index_csv=root / "sample_index.csv",
        diffsbdd_input_interface_report_csv=root / "diffsbdd_input_interface_report.csv",
        diffsbdd_input_interface_manifest_json=root / "diffsbdd_input_adapter_preview_manifest.json",
        output_report_csv=root / "diffsbdd_adapter_shape_smoke_report.csv",
        output_manifest_json=root / "diffsbdd_adapter_shape_smoke_preview_manifest.json",
        output_md=Path("docs/diffsbdd_adapter_shape_smoke_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_diffsbdd_batch_fields_outputs_required_fields():
    batch_fields, _ = _shape_smoke("A_warhead_only")
    for key in EXPECTED_DIFFSBDD_BATCH_FIELDS:
        assert key in batch_fields
    assert batch_fields["lig_coords"].shape == (104, 3)
    assert batch_fields["lig_one_hot"].shape == (104, 11)
    assert batch_fields["lig_mask"].shape == (104,)
    assert batch_fields["num_lig_atoms"].tolist() == [33, 30, 41]
    assert batch_fields["pocket_coords"].shape == (5642, 3)
    assert batch_fields["pocket_one_hot"].shape == (5642, 11)
    assert batch_fields["pocket_mask"].shape == (5642,)
    assert batch_fields["num_pocket_nodes"].tolist() == [2306, 1723, 1613]
    assert batch_fields["lig_fixed"].shape == (104, 1)
    assert batch_fields["generation_mask_flat"].shape == (104,)
    assert batch_fields["ligand_context_mask_flat"].shape == (104,)
    assert batch_fields["ligand_target_mask_flat"].shape == (104,)
    assert batch_fields["coordinate_center"].shape == (3, 3)


def test_ligand_pocket_dicts_and_shape_smoke_pass_for_all_mask_levels():
    expected_targets = {
        "A_warhead_only": 12,
        "B_linker_warhead": 30,
        "B2_scaffold_warhead": 86,
        "C_scaffold_linker_warhead": 104,
    }
    for mask_level in MASK_LEVELS:
        _, shape_smoke = _shape_smoke(mask_level)
        assert set(EXPECTED_LIGAND_DICT_FIELDS).issubset(shape_smoke["ligand"])
        assert set(EXPECTED_POCKET_DICT_FIELDS).issubset(shape_smoke["pocket"])
        ok, reasons = validate_diffsbdd_adapter_shape_smoke_v0(shape_smoke)
        assert ok, reasons
        summary = summarize_diffsbdd_shape_smoke_v0(shape_smoke)
        assert shape_smoke["ligand"]["x"].shape == (104, 3)
        assert shape_smoke["pocket"]["x"].shape == (5642, 3)
        assert shape_smoke["ligand"]["one_hot"].shape[0] == shape_smoke["ligand"]["x"].shape[0]
        assert shape_smoke["pocket"]["one_hot"].shape[0] == shape_smoke["pocket"]["x"].shape[0]
        assert int(shape_smoke["ligand"]["size"].sum().item()) == shape_smoke["ligand"]["x"].shape[0]
        assert int(shape_smoke["pocket"]["size"].sum().item()) == shape_smoke["pocket"]["x"].shape[0]
        assert torch.equal(shape_smoke["generation_mask_flat"], shape_smoke["ligand_target_mask_flat"])
        assert not (shape_smoke["ligand_context_mask_flat"] & shape_smoke["ligand_target_mask_flat"]).any()
        assert torch.equal(shape_smoke["lig_fixed"].squeeze(1).to(dtype=torch.bool), shape_smoke["ligand_context_mask_flat"])
        assert summary["target_atom_count"] == expected_targets[mask_level]
        assert summary["shape_sanity_passed"] is True
        assert summary["mask_sanity_passed"] is True
        assert shape_smoke["checkpoint_loaded"] is False
        assert shape_smoke["checkpoint_saved"] is False
        assert shape_smoke["diffsbdd_model_initialized"] is False
        assert shape_smoke["diffsbdd_model_called"] is False
        assert shape_smoke["training_executed"] is False


def test_validation_catches_lig_fixed_context_mismatch():
    _, shape_smoke = _shape_smoke("A_warhead_only")
    shape_smoke["lig_fixed"] = torch.zeros_like(shape_smoke["lig_fixed"])
    ok, reasons = validate_diffsbdd_adapter_shape_smoke_v0(shape_smoke)
    assert ok is False
    assert "mask_sanity_failed" in reasons


def test_script_writes_shape_smoke_report_manifest_summary_and_no_forbidden_artifacts():
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_adapter_shape_smoke_report.csv")
    assert len(rows) == 4
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    assert all(row["shape_smoke_status"] == "passed" for row in rows)
    assert all(row["ligand_atom_total"] == "104" for row in rows)
    assert all(row["pocket_atom_total"] == "5642" for row in rows)
    assert all(row["ligand_feature_dim"] == "11" for row in rows)
    assert all(row["pocket_feature_dim"] == "11" for row in rows)
    assert all(row["generation_equals_target"] == "true" for row in rows)
    assert all(row["context_target_no_overlap"] == "true" for row in rows)
    assert all(row["lig_fixed_matches_context"] == "true" for row in rows)
    assert all(row["flattened_ligand_count_matches_size"] == "true" for row in rows)
    assert all(row["flattened_pocket_count_matches_size"] == "true" for row in rows)
    assert all(row["coords_finite"] == "true" for row in rows)
    assert all(row["one_hot_finite"] == "true" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["checkpoint_saved"] == "false" for row in rows)
    assert all(row["diffsbdd_model_initialized"] == "false" for row in rows)
    assert all(row["diffsbdd_model_called"] == "false" for row in rows)
    assert all(row["training_executed"] == "false" for row in rows)
    preview = json.loads((root / "diffsbdd_adapter_shape_smoke_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "diffsbdd_adapter_shape_smoke_without_checkpoint_v0"
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 4
    assert preview["all_mask_levels_passed"] is True
    assert preview["ligand_atom_total_by_mask_level"] == {level: 104 for level in MASK_LEVELS}
    assert preview["pocket_atom_total_by_mask_level"] == {level: 5642 for level in MASK_LEVELS}
    assert preview["target_atom_count_by_mask_level"] == {
        "A_warhead_only": 12,
        "B_linker_warhead": 30,
        "B2_scaffold_warhead": 86,
        "C_scaffold_linker_warhead": 104,
    }
    assert preview["ligand_feature_dim"] == 11
    assert preview["pocket_feature_dim"] == 11
    assert set(EXPECTED_DIFFSBDD_BATCH_FIELDS).issubset(preview["expected_diffsbdd_batch_fields"])
    assert set(EXPECTED_LIGAND_DICT_FIELDS).issubset(preview["expected_ligand_dict_fields"])
    assert set(EXPECTED_POCKET_DICT_FIELDS).issubset(preview["expected_pocket_dict_fields"])
    assert preview["shape_sanity_all_passed"] is True
    assert preview["mask_sanity_all_passed"] is True
    assert preview["checkpoint_loaded"] is False
    assert preview["checkpoint_saved"] is False
    assert preview["diffsbdd_model_initialized"] is False
    assert preview["diffsbdd_model_called"] is False
    assert preview["training_executed"] is False
    assert preview["archive_created"] is False
    assert Path("docs/diffsbdd_adapter_shape_smoke_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
