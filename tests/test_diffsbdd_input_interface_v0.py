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

from inspect_diffsbdd_input_interface_v0 import MASK_LEVELS, run  # noqa: E402
from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.diffsbdd_input_adapter import (  # noqa: E402
    DIRECT_MAPPING_FIELDS,
    MISSING_OR_UNCERTAIN_FIELDS,
    build_diffsbdd_like_input_from_covalent_v0,
    validate_diffsbdd_like_input_v0,
)
from covalent_ext.model_input_adapter import build_covalent_model_input_v0, validate_covalent_model_input_v0  # noqa: E402
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


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        sample_index_csv=root / "sample_index.csv",
        tiny_smoke_report_csv=root / "tiny_training_smoke_report.csv",
        tiny_smoke_manifest_json=root / "tiny_training_smoke_preview_manifest.json",
        output_report_csv=root / "diffsbdd_input_interface_report.csv",
        output_manifest_json=root / "diffsbdd_input_adapter_preview_manifest.json",
        output_md=Path("docs/diffsbdd_input_interface_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_diffsbdd_like_adapter_keys_shapes_and_masks_for_all_mask_levels():
    batch = _batch()
    for mask_level in MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        model_ok, model_reasons = validate_covalent_model_input_v0(model_input)
        assert model_ok, model_reasons
        diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
        ok, reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
        assert ok, reasons
        for key in ["sample_id", "ligand_x", "protein_x", "ligand_mask", "protein_mask", "generation_mask"]:
            assert key in diffsbdd_like
        assert diffsbdd_like["ligand_x"].shape == (3, 41, 3)
        assert diffsbdd_like["protein_x"].shape == (3, 2306, 3)
        assert diffsbdd_like["ligand_mask"].shape == (3, 41)
        assert diffsbdd_like["protein_mask"].shape == (3, 2306)
        assert diffsbdd_like["generation_mask"].shape == (3, 41)
        assert diffsbdd_like["ligand"]["x"].shape[1] == 3
        assert diffsbdd_like["pocket"]["x"].shape[1] == 3
        assert diffsbdd_like["ligand"]["size"].tolist() == [33, 30, 41]
        assert diffsbdd_like["pocket"]["size"].tolist() == [2306, 1723, 1613]
        assert int(diffsbdd_like["ligand_target_mask"].sum().item()) > 0
        assert not (diffsbdd_like["generation_mask"] & ~diffsbdd_like["ligand_mask"]).any()
        assert not (diffsbdd_like["ligand_context_mask"] & diffsbdd_like["ligand_target_mask"]).any()
        assert torch.equal(diffsbdd_like["generation_mask"], diffsbdd_like["ligand_target_mask"])
        assert diffsbdd_like["edge_mask_required"] is False
        assert diffsbdd_like["edge_index_constructed_by_dynamics"] is True
        assert diffsbdd_like["checkpoint_loaded"] is False
        assert diffsbdd_like["diffsbdd_model_initialized"] is False
        assert diffsbdd_like["diffsbdd_model_called"] is False
        assert diffsbdd_like["training_executed"] is False


def test_diffsbdd_like_validation_catches_context_target_overlap():
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level="A_warhead_only")
    model_input = build_covalent_model_input_v0(adapted)
    diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
    diffsbdd_like["ligand_context_mask"] = diffsbdd_like["ligand_target_mask"].clone()
    ok, reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
    assert ok is False
    assert "context_target_overlap" in reasons


def test_diffsbdd_like_validation_catches_forbidden_runtime_flags():
    adapted = adapt_covalent_batch_for_model_v0(_batch(), mask_level="A_warhead_only")
    model_input = build_covalent_model_input_v0(adapted)
    diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
    diffsbdd_like["checkpoint_loaded"] = True
    diffsbdd_like["diffsbdd_model_initialized"] = True
    diffsbdd_like["diffsbdd_model_called"] = True
    diffsbdd_like["training_executed"] = True
    ok, reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
    assert ok is False
    assert "checkpoint_loaded" in reasons
    assert "diffsbdd_model_initialized" in reasons
    assert "diffsbdd_model_called" in reasons
    assert "training_executed" in reasons


def test_inspection_script_writes_report_manifest_summary_and_no_forbidden_artifacts():
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_input_interface_report.csv")
    assert len(rows) == 4
    assert {row["mask_level"] for row in rows} == set(MASK_LEVELS)
    assert all(row["adapter_status"] == "passed" for row in rows)
    assert all(row["diffsbdd_like_keys_present"] == "true" for row in rows)
    assert all(row["required_covalent_keys_present"] == "true" for row in rows)
    assert all(row["shape_sanity_passed"] == "true" for row in rows)
    assert all(row["mask_sanity_passed"] == "true" for row in rows)
    assert all(int(row["target_atom_count"]) > 0 for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["diffsbdd_model_initialized"] == "false" for row in rows)
    assert all(row["diffsbdd_model_called"] == "false" for row in rows)
    assert all(row["training_executed"] == "false" for row in rows)
    preview = json.loads((root / "diffsbdd_input_adapter_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "diffsbdd_input_interface_inspection_adapter_v0"
    assert preview["dataset_len"] == 3
    assert preview["batch_size"] == 3
    assert preview["mask_levels_checked"] == 4
    assert preview["report_row_count"] == 4
    assert preview["all_mask_levels_passed"] is True
    assert "dataset.py" in preview["source_files_inspected"]
    assert "lightning_modules.LigandPocketDDPM.forward" in preview["detected_diffsbdd_entrypoints"]
    assert "ligand.x" in preview["detected_expected_input_fields"]
    assert "pocket.x" in preview["detected_expected_input_fields"]
    assert set(DIRECT_MAPPING_FIELDS).issubset(set(preview["direct_mapping_fields"]))
    assert set(MISSING_OR_UNCERTAIN_FIELDS).issubset(set(preview["missing_or_uncertain_fields"]))
    assert preview["recommended_next_step"] == "diffsbdd_adapter_shape_smoke_without_checkpoint"
    assert preview["checkpoint_loaded"] is False
    assert preview["diffsbdd_model_initialized"] is False
    assert preview["diffsbdd_model_called"] is False
    assert preview["training_executed"] is False
    assert preview["archive_created"] is False
    assert Path("docs/diffsbdd_input_interface_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
