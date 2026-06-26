import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_pretrained_checkpoint_load_smoke_v0 as script  # noqa: E402
import covalent_ext.pretrained_checkpoint_load_smoke as smoke  # noqa: E402
from covalent_ext.pretrained_checkpoint_load_smoke import (  # noqa: E402
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    MODEL_CONFIG_PATH,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    attempt_load_pretrained_state_dict_v0,
    build_pretrained_checkpoint_load_smoke_v0,
    instantiate_model_for_pretrained_load_v0,
    load_pretrained_checkpoint_payload_v0,
    locate_pretrained_checkpoint_v0,
    normalize_pretrained_state_dict_keys_v0,
    run_no_grad_forward_smoke_v0,
    validate_step10x_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step10x_outputs_success_and_checkpoint_target_is_pretrained():
    assert validate_step10x_outputs_v0() is True
    assert CHECKPOINT_PATH == Path("checkpoints/crossdocked_fullatom_cond.ckpt")
    assert "training_runs" not in str(CHECKPOINT_PATH)
    assert MODEL_CONFIG_PATH == "configs/crossdock_fullatom_cond.yml"


def test_locate_pretrained_checkpoint_present_and_missing_path_blocks(tmp_path):
    result = locate_pretrained_checkpoint_v0(CHECKPOINT_PATH)

    assert result["status"] == "passed"
    assert result["pretrained_checkpoint_present"] is True
    assert result["checkpoint_suffix"] == ".ckpt"
    assert result["checkpoint_size_bytes"] > 0
    assert len(result["checkpoint_sha256"]) == 64
    assert result["blocking_reasons"] == []

    missing = tmp_path / "missing_pretrained.ckpt"
    blocked = locate_pretrained_checkpoint_v0(missing)
    assert blocked["status"] == "blocked"
    assert blocked["pretrained_checkpoint_present"] is False
    assert "pretrained_checkpoint_missing" in blocked["blocking_reasons"]
    assert not missing.exists()


def test_load_payload_detects_lightning_state_dict_and_raw_state_dict(monkeypatch):
    result = load_pretrained_checkpoint_payload_v0(CHECKPOINT_PATH, map_location="cpu")

    assert result["checkpoint_loaded"] is True
    assert result["checkpoint_payload_type"] == "dict"
    assert "state_dict" in result["checkpoint_top_level_keys"]
    assert result["has_state_dict"] is True
    assert result["has_hyper_parameters"] is True
    assert result["state_dict_key_count"] > 0
    assert result["sample_state_dict_keys"]
    assert result["blocking_reasons"] == []

    def fake_load(path, map_location):
        return {"layer.weight": torch.ones(2, 2)}

    monkeypatch.setattr(smoke.torch, "load", fake_load)
    raw = load_pretrained_checkpoint_payload_v0("in_memory_raw_state_dict.ckpt", map_location="cpu")
    assert raw["checkpoint_loaded"] is True
    assert raw["has_state_dict"] is False
    assert raw["state_dict_key_count"] == 1
    assert raw["sample_state_dict_keys"] == ["layer.weight"]


def test_normalize_pretrained_state_dict_keys_produces_conservative_variants():
    raw_state = {
        "model.layer.weight": torch.ones(2, 2),
        "module.layer.bias": torch.ones(2),
        "dynamics.block.weight": torch.ones(1),
        "model.dynamics.block.bias": torch.ones(1),
    }

    normalized = normalize_pretrained_state_dict_keys_v0(raw_state)
    variants = {variant["variant_name"]: variant for variant in normalized["candidate_variants"]}

    assert {"raw", "strip_model_prefix", "strip_module_prefix", "strip_dynamics_prefix", "strip_model_dynamics_prefix"}.issubset(
        variants
    )
    assert "layer.weight" in variants["strip_model_prefix"]["state_dict"]
    assert "layer.bias" in variants["strip_module_prefix"]["state_dict"]
    assert "block.weight" in variants["strip_dynamics_prefix"]["state_dict"]
    assert "block.bias" in variants["strip_model_dynamics_prefix"]["state_dict"]
    assert variants["raw"]["state_dict"]["model.layer.weight"].shape == torch.Size([2, 2])


def test_attempt_load_state_dict_prefers_shape_matched_variant_and_blocks_zero_match():
    model = torch.nn.Sequential(torch.nn.Linear(2, 2))
    model_state = model.state_dict()
    matching_key = next(iter(model_state.keys()))
    incompatible_key = list(model_state.keys())[1]

    candidate_variants = [
        {
            "variant_name": "raw",
            "state_dict": {
                matching_key: torch.ones_like(model_state[matching_key]),
                incompatible_key: torch.ones(3),
                "extra.weight": torch.ones(1),
            },
        }
    ]
    result = attempt_load_pretrained_state_dict_v0(model, candidate_variants)

    assert result["load_attempted"] is True
    assert result["best_variant_name"] == "raw"
    assert result["matched_key_count"] == 2
    assert result["shape_matched_key_count"] == 1
    assert result["incompatible_shape_count"] == 1
    assert result["unexpected_key_count"] == 1
    assert result["nonstrict_load_success"] is True
    assert result["shape_matched_ratio"] < 0.5
    assert result["pretrained_partial_shape_load_success"] is True
    assert result["pretrained_full_architecture_compatible"] is False
    assert result["shape_mismatch_detected"] is True
    assert result["architecture_config_mismatch_suspected"] is True
    assert result["pretrained_weights_loaded"] is False

    compatible = attempt_load_pretrained_state_dict_v0(
        model,
        [{"variant_name": "compatible", "state_dict": {key: torch.ones_like(value) for key, value in model_state.items()}}],
    )
    assert compatible["shape_matched_ratio"] == 1.0
    assert compatible["pretrained_partial_shape_load_success"] is True
    assert compatible["pretrained_full_architecture_compatible"] is True
    assert compatible["pretrained_weights_loaded"] is True

    blocked = attempt_load_pretrained_state_dict_v0(
        model,
        [{"variant_name": "no_match", "state_dict": {"other.weight": torch.ones(1)}}],
    )
    assert blocked["shape_matched_key_count"] == 0
    assert blocked["shape_matched_ratio"] == 0.0
    assert blocked["nonstrict_load_success"] is False
    assert blocked["pretrained_partial_shape_load_success"] is False
    assert blocked["pretrained_weights_loaded"] is False
    assert "shape_matched_key_count_zero" in blocked["blocking_reasons"]


def test_instantiate_model_for_pretrained_load_contract_cpu():
    result = instantiate_model_for_pretrained_load_v0(device="cpu")

    assert result["requested_device"] == "cpu"
    assert result["resolved_device"] == "cpu"
    assert result["model_class"] == "LigandPocketDDPM"
    assert result["model_instantiated"] is True
    assert result["trainable_parameter_count"] > 0
    assert result["state_dict_key_count"] > 0
    assert result["sample_model_state_keys"]
    assert result["blocking_reasons"] == []
    assert result["model"] is not None


def test_no_grad_forward_smoke_does_not_create_gradients_or_backward():
    class FakeForwardModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.ones(1))
            self.training_state_seen = None

        def forward(self, data_batch):
            self.training_state_seen = self.training
            return torch.ones(3, device=self.weight.device) * self.weight

    model = FakeForwardModel()
    result = run_no_grad_forward_smoke_v0(model, {"resolved_device": "cpu"})

    assert result["forward_smoke_attempted"] is True
    assert result["forward_smoke_success"] is True
    assert result["output_finite"] is True
    assert result["nan_count"] == 0
    assert result["inf_count"] == 0
    assert result["output_shape_summary"]["output"] == [3]
    assert model.training_state_seen is False
    assert model.weight.grad is None


def test_build_smoke_manifest_contract_and_safety_flags():
    result = build_pretrained_checkpoint_load_smoke_v0(device="auto", checkpoint_path=CHECKPOINT_PATH)
    manifest = result["manifest"]

    assert manifest["stage"] == "pretrained_checkpoint_load_smoke_v0"
    assert manifest["previous_stage"] == "first_checkpointed_training_dry_run_review_v0"
    assert manifest["step10x_review_passed"] is True
    assert manifest["pretrained_checkpoint_present"] is True
    assert manifest["pretrained_checkpoint_readable"] is True
    assert manifest["pretrained_state_dict_extracted"] is True
    assert manifest["checkpoint_loaded"] is True
    assert manifest["checkpoint_payload_type"] == "dict"
    assert manifest["has_state_dict"] is True
    assert manifest["state_dict_key_count"] == 122
    assert manifest["model_instantiated"] is True
    assert manifest["model_class"] == "LigandPocketDDPM"
    assert manifest["load_attempted"] is True
    assert manifest["matched_key_count"] == 122
    assert manifest["shape_matched_key_count"] == 7
    assert manifest["shape_matched_ratio"] < 0.5
    assert manifest["missing_key_count"] == 20
    assert manifest["unexpected_key_count"] == 0
    assert manifest["incompatible_shape_count"] == 115
    assert manifest["nonstrict_load_success"] is True
    assert manifest["pretrained_partial_shape_load_success"] is True
    assert manifest["pretrained_full_architecture_compatible"] is False
    assert manifest["pretrained_effective_load_status"] == "partial_shape_compatible_only"
    assert manifest["shape_mismatch_detected"] is True
    assert manifest["architecture_config_mismatch_suspected"] is True
    assert manifest["pretrained_weights_loaded"] is False
    assert manifest["forward_smoke_attempted"] is True
    assert manifest["forward_smoke_success"] is True
    assert manifest["output_finite"] is True
    assert manifest["backward_called"] is False
    assert manifest["optimizer_created"] is False
    assert manifest["optimizer_step_called"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["formal_training_executed"] is False
    assert manifest["real_finetune_executed"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["loss_decrease_required"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["all_checks_passed_meaning"] == "smoke_completed_and_mismatch_detected"
    assert manifest["recommended_next_step"] == "pretrained_checkpoint_architecture_config_reconciliation"
    assert manifest["recommended_next_step"] != "pretrained_masked_loss_smoke"


def test_script_writes_report_manifest_summary_to_patched_outputs(tmp_path, monkeypatch):
    output_root = tmp_path / "pretrained_checkpoint_load_smoke_v0"
    report_csv = output_root / "pretrained_checkpoint_load_smoke_report.csv"
    manifest_json = output_root / "pretrained_checkpoint_load_smoke_manifest.json"
    summary_md = tmp_path / "docs" / "pretrained_checkpoint_load_smoke_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="auto", checkpoint_path=CHECKPOINT_PATH) == 0

    rows = _read_csv(report_csv)
    assert len(rows) == 8
    assert [row["section"] for row in rows] == [
        "step10x_review_precondition",
        "pretrained_checkpoint_location",
        "checkpoint_payload_inspection",
        "state_dict_key_normalization",
        "model_instantiation",
        "pretrained_state_dict_load",
        "no_grad_forward_smoke",
        "safety_boundary",
    ]
    assert all(row["stage"] == "pretrained_checkpoint_load_smoke_v0" for row in rows)
    assert all(row["previous_stage"] == "first_checkpointed_training_dry_run_review_v0" for row in rows)
    assert all(row["status"] == "passed" for row in rows)
    assert all(
        row["recommended_next_step"] == "pretrained_checkpoint_architecture_config_reconciliation" for row in rows
    )

    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["pretrained_checkpoint_path"] == str(CHECKPOINT_PATH)
    assert manifest["pretrained_weights_loaded"] is False
    assert manifest["pretrained_partial_shape_load_success"] is True
    assert manifest["pretrained_full_architecture_compatible"] is False
    assert manifest["shape_mismatch_detected"] is True
    assert manifest["architecture_config_mismatch_suspected"] is True
    assert manifest["recommended_next_step"] == "pretrained_checkpoint_architecture_config_reconciliation"
    assert manifest["forward_smoke_success"] is True
    assert summary_md.is_file()
    assert "not training" in summary_md.read_text(encoding="utf-8")


def test_generated_outputs_and_repository_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert SUMMARY_MD.is_file()
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["forbidden_artifacts_created"] is False
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]

    source_diff = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    staged_source_diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert source_diff.returncode == 0
    assert staged_source_diff.returncode == 0


def test_source_files_do_not_contain_forbidden_training_or_save_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/pretrained_checkpoint_load_smoke.py",
        REPO_ROOT / "scripts/check_pretrained_checkpoint_load_smoke_v0.py",
        REPO_ROOT / "tests/test_pretrained_checkpoint_load_smoke_v0.py",
    ]
    forbidden = [
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
        "optimizer" + ".step",
        "trainer" + ".fit",
        "." + "backward" + "(",
        "training" + "_step" + "(",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
