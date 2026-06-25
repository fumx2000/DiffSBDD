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
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_diffsbdd_single_batch_forward_shape_smoke_v0 import run  # noqa: E402
from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0  # noqa: E402
from covalent_ext.diffsbdd_forward_shape_smoke import (  # noqa: E402
    build_forward_candidate_inputs_v0,
    resolve_diffsbdd_forward_device_v0,
    run_diffsbdd_single_batch_forward_shape_smoke_v0,
)
from covalent_ext.diffsbdd_input_adapter import build_diffsbdd_like_input_from_covalent_v0  # noqa: E402
from covalent_ext.diffsbdd_shape_smoke import build_diffsbdd_batch_fields_v0, build_ligand_pocket_dicts_for_diffsbdd_v0  # noqa: E402
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
    return build_ligand_pocket_dicts_for_diffsbdd_v0(batch_fields)


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        device="auto",
        mask_level="A_warhead_only",
        instantiation_report_csv=root / "diffsbdd_model_instantiation_dry_run_report.csv",
        instantiation_manifest_json=root / "diffsbdd_model_instantiation_dry_run_preview_manifest.json",
        output_report_csv=root / "diffsbdd_single_batch_forward_shape_smoke_report.csv",
        output_manifest_json=root / "diffsbdd_single_batch_forward_shape_smoke_preview_manifest.json",
        output_md=Path("docs/diffsbdd_single_batch_forward_shape_smoke_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_device_resolver_auto_prefers_cuda_when_available():
    info = resolve_diffsbdd_forward_device_v0("auto")
    if torch.cuda.is_available():
        assert info["resolved_device"] == "cuda:0"
        assert info["cuda_available"] is True
        assert info["cuda_device_count"] >= 1
        assert info["cuda_device_name"]
    else:
        assert info["resolved_device"] == "cpu"
        assert info["device_fallback_reason"] == "cuda_unavailable"


def test_build_forward_candidate_inputs_shapes_and_metadata():
    candidate = build_forward_candidate_inputs_v0(_shape_smoke("A_warhead_only"))
    assert set(candidate) == {"data_batch", "ligand", "pocket", "metadata"}
    data_batch = candidate["data_batch"]
    ligand = candidate["ligand"]
    pocket = candidate["pocket"]
    metadata = candidate["metadata"]
    for key in ["lig_coords", "lig_one_hot", "lig_mask", "pocket_coords", "pocket_one_hot", "pocket_mask", "num_lig_atoms", "num_pocket_nodes", "lig_fixed"]:
        assert key in data_batch
    assert ligand["x"].shape == (104, 3)
    assert ligand["one_hot"].shape == (104, 11)
    assert ligand["mask"].shape == (104,)
    assert ligand["size"].tolist() == [33, 30, 41]
    assert pocket["x"].shape == (5642, 3)
    assert pocket["one_hot"].shape == (5642, 11)
    assert pocket["mask"].shape == (5642,)
    assert pocket["size"].tolist() == [2306, 1723, 1613]
    assert metadata["mask_level"] == "A_warhead_only"
    assert metadata["batch_size"] == 3
    assert int(metadata["ligand_target_mask_flat"].sum().item()) == 12
    assert torch.equal(metadata["generation_mask_flat"], metadata["ligand_target_mask_flat"])


def test_run_forward_shape_smoke_returns_complete_safety_contract():
    result = run_diffsbdd_single_batch_forward_shape_smoke_v0(device="auto", mask_level="A_warhead_only")
    required = {
        "requested_device",
        "resolved_device",
        "cuda_available",
        "cuda_device_count",
        "cuda_device_name",
        "mask_level",
        "batch_size",
        "model_class_name",
        "model_initialized",
        "parameter_count",
        "trainable_parameter_count",
        "forward_signature",
        "get_ligand_and_pocket_signature",
        "selected_forward_call_style",
        "ligand_x_shape",
        "ligand_one_hot_shape",
        "pocket_x_shape",
        "pocket_one_hot_shape",
        "ligand_mask_shape",
        "pocket_mask_shape",
        "target_atom_count",
        "context_atom_count",
        "forward_called",
        "forward_success",
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
        "smoke_status",
        "blocking_reasons",
    }
    assert required.issubset(result)
    assert result["mask_level"] == "A_warhead_only"
    assert result["model_class_name"] == "LigandPocketDDPM"
    assert result["selected_forward_call_style"] in {"LigandPocketDDPM.forward(data_batch)", ""}
    assert result["ligand_x_shape"] == [104, 3]
    assert result["pocket_x_shape"] == [5642, 3]
    assert result["target_atom_count"] == 12
    assert result["checkpoint_loaded"] is False
    assert result["checkpoint_saved"] is False
    assert result["training_step_called"] is False
    assert result["backward_called"] is False
    assert result["optimizer_step_executed"] is False
    assert result["trainer_fit_called"] is False
    assert result["training_executed"] is False
    assert result["real_finetune_executed"] is False
    if result["forward_success"]:
        assert result["forward_called"] is True
        assert result["finite_tensor_outputs"] is True
        assert result["smoke_status"] == "passed"
        assert result["forward_signature"]
        assert result["get_ligand_and_pocket_signature"]
    else:
        assert result["smoke_status"] == "blocked"
        assert result["forward_exception_type"]
        assert result["blocking_reasons"]


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts():
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_single_batch_forward_shape_smoke_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0"
    assert row["requested_device"] == "auto"
    assert row["mask_level"] == "A_warhead_only"
    assert row["model_class_name"] == "LigandPocketDDPM"
    assert row["model_initialized"] in {"true", "false"}
    assert row["forward_called"] in {"true", "false"}
    assert row["checkpoint_loaded"] == "false"
    assert row["checkpoint_saved"] == "false"
    assert row["training_step_called"] == "false"
    assert row["backward_called"] == "false"
    assert row["optimizer_step_executed"] == "false"
    assert row["trainer_fit_called"] == "false"
    assert row["training_executed"] == "false"
    assert row["real_finetune_executed"] == "false"
    assert row["smoke_status"] in {"passed", "blocked"}
    if row["forward_success"] == "true":
        assert row["forward_called"] == "true"
        assert row["finite_tensor_outputs"] == "true"
        assert row["smoke_status"] == "passed"
    else:
        assert row["smoke_status"] == "blocked"
        assert row["forward_exception_type"]
    preview = json.loads((root / "diffsbdd_single_batch_forward_shape_smoke_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint_v0"
    assert preview["previous_stage"] == "diffsbdd_model_instantiation_dry_run_without_checkpoint_v0"
    assert preview["step10d_instantiation_passed"] is True
    assert preview["mask_level"] == "A_warhead_only"
    assert preview["model_class_name"] == "LigandPocketDDPM"
    assert preview["checkpoint_loaded"] is False
    assert preview["checkpoint_saved"] is False
    assert preview["training_step_called"] is False
    assert preview["backward_called"] is False
    assert preview["optimizer_step_executed"] is False
    assert preview["trainer_fit_called"] is False
    assert preview["training_executed"] is False
    assert preview["real_finetune_executed"] is False
    assert preview["archive_created"] is False
    assert Path("docs/diffsbdd_single_batch_forward_shape_smoke_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
