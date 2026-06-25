import argparse
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

from check_diffsbdd_model_instantiation_dry_run_v0 import run  # noqa: E402
from covalent_ext.diffsbdd_model_instantiation import (  # noqa: E402
    build_minimal_diffsbdd_instantiation_config_v0,
    inspect_diffsbdd_model_constructor_v0,
    try_instantiate_diffsbdd_model_without_checkpoint_v0,
)


@pytest.fixture(autouse=True)
def _fixture_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    target = tmp_path / "data" / "derived" / "covalent_small" / "training_tensor_materialized_v0"
    shutil.copytree(source, target)


def _args():
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    return argparse.Namespace(
        device="cpu",
        shape_smoke_report_csv=root / "diffsbdd_adapter_shape_smoke_report.csv",
        shape_smoke_manifest_json=root / "diffsbdd_adapter_shape_smoke_preview_manifest.json",
        output_report_csv=root / "diffsbdd_model_instantiation_dry_run_report.csv",
        output_manifest_json=root / "diffsbdd_model_instantiation_dry_run_preview_manifest.json",
        output_md=Path("docs/diffsbdd_model_instantiation_dry_run_v0_summary.md"),
    )


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_constructor_inspection_returns_real_model_class_and_signature():
    info = inspect_diffsbdd_model_constructor_v0()
    assert info["model_class_name"] == "LigandPocketDDPM"
    assert info["module_name"] == "lightning_modules"
    assert "outdir" in info["constructor_signature"]
    assert "dataset" in info["required_constructor_args"]
    assert "egnn_params" in info["required_constructor_args"]
    assert "diffusion_params" in info["required_constructor_args"]
    assert "pocket_representation" in info["optional_constructor_args"]
    assert "lightning_modules.py" in info["inspected_source_files"]
    assert "configs/crossdock_fullatom_cond.yml" in info["inspected_source_files"]
    assert info["detected_config_sources"]
    assert info["detected_dataset_info_sources"]


def test_minimal_instantiation_config_reports_status_and_sources():
    config = build_minimal_diffsbdd_instantiation_config_v0()
    assert config["config_status"] in {"ready", "blocked"}
    assert config["config_source"] == "configs/crossdock_fullatom_cond.yml"
    assert config["model_class_name"] == "LigandPocketDDPM"
    assert config["dataset_info_source"] == "constants.dataset_params['crossdock_full']"
    assert config["atom_encoder_source"] == "constants.dataset_params['crossdock_full']['atom_encoder']"
    assert isinstance(config["missing_or_uncertain_config_fields"], list)
    if config["config_status"] == "ready":
        assert config["config_dict"]["dataset"] == "crossdock_full"
        assert config["config_dict"]["mode"] == "pocket_conditioning"
        assert config["config_dict"]["pocket_representation"] == "full-atom"
        assert config["config_dict"]["egnn_params"]["device"] == "cpu"
        assert config["blocking_reasons"] == []
    else:
        assert config["blocking_reasons"]


def test_try_instantiate_diffsbdd_model_without_checkpoint_contract():
    result = try_instantiate_diffsbdd_model_without_checkpoint_v0(device="cpu")
    assert result["device"] == "cpu"
    assert result["model_class_name"] == "LigandPocketDDPM"
    assert result["constructor_signature_resolved"] is True
    assert result["checkpoint_loaded"] is False
    assert result["checkpoint_saved"] is False
    assert result["forward_called"] is False
    assert result["diffsbdd_model_called"] is False
    assert result["training_step_called"] is False
    assert result["training_executed"] is False
    if result["config_status"] == "ready":
        assert result["model_class_imported"] is True
        assert result["model_initialized"] is True
        assert result["parameter_count"] > 0
        assert result["trainable_parameter_count"] > 0
        assert result["module_count"] > 0
        assert result["smoke_status"] == "passed"
    else:
        assert result["model_initialized"] is False
        assert result["smoke_status"] == "blocked"
        assert result["blocking_reasons"]


def test_script_writes_report_manifest_summary_and_no_forbidden_artifacts():
    assert run(_args()) == 0
    root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    rows = _read_csv(root / "diffsbdd_model_instantiation_dry_run_report.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row["stage"] == "diffsbdd_model_instantiation_dry_run_without_checkpoint_v0"
    assert row["device"] == "cpu"
    assert row["model_class_name"] == "LigandPocketDDPM"
    assert row["model_class_imported"] == "true"
    assert row["constructor_signature_resolved"] == "true"
    assert row["config_status"] == "ready"
    assert row["model_initialized"] == "true"
    assert int(row["parameter_count"]) > 0
    assert int(row["trainable_parameter_count"]) > 0
    assert int(row["module_count"]) > 0
    assert row["checkpoint_loaded"] == "false"
    assert row["checkpoint_saved"] == "false"
    assert row["forward_called"] == "false"
    assert row["diffsbdd_model_called"] == "false"
    assert row["training_step_called"] == "false"
    assert row["training_executed"] == "false"
    assert row["smoke_status"] == "passed"
    preview = json.loads((root / "diffsbdd_model_instantiation_dry_run_preview_manifest.json").read_text(encoding="utf-8"))
    assert preview["stage"] == "diffsbdd_model_instantiation_dry_run_without_checkpoint_v0"
    assert preview["previous_stage"] == "diffsbdd_adapter_shape_smoke_without_checkpoint_v0"
    assert preview["step10c_shape_smoke_passed"] is True
    assert preview["device"] == "cpu"
    assert preview["model_class_name"] == "LigandPocketDDPM"
    assert preview["model_class_imported"] is True
    assert preview["constructor_signature_resolved"] is True
    assert preview["config_status"] == "ready"
    assert preview["model_initialized"] is True
    assert preview["parameter_count"] > 0
    assert preview["trainable_parameter_count"] > 0
    assert preview["module_count"] > 0
    assert preview["checkpoint_loaded"] is False
    assert preview["checkpoint_saved"] is False
    assert preview["forward_called"] is False
    assert preview["diffsbdd_model_called"] is False
    assert preview["training_step_called"] is False
    assert preview["training_executed"] is False
    assert preview["archive_created"] is False
    assert preview["all_checks_passed"] is True
    assert preview["recommended_next_step"] == "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint"
    assert Path("docs/diffsbdd_model_instantiation_dry_run_v0_summary.md").is_file()
    assert not list(root.rglob("*.pt"))
    assert not list(root.rglob("*.pkl"))
    assert not list(root.rglob("*.lmdb"))
    assert not list(root.rglob("*.tar"))
    assert not list(root.rglob("*.zip"))
    assert not list(root.rglob("*.tgz"))
