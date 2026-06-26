import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_checkpoint_compatible_pretrained_load_smoke_v0 as script  # noqa: E402
from covalent_ext.checkpoint_compatible_pretrained_load_smoke import (  # noqa: E402
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    DIAGNOSTICS_JSON,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_checkpoint_compatible_pretrained_load_decision_v0,
    build_checkpoint_compatible_pretrained_load_smoke_v0,
    instantiate_model_for_pretrained_load_v0,
    load_checkpoint_state_dict_for_smoke_v0,
    run_loaded_model_no_grad_forward_smoke_v0,
    strict_load_checkpoint_weights_v0,
    validate_step11d_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11d_outputs_success():
    assert validate_step11d_outputs_v0() is True


def test_load_checkpoint_state_dict_for_smoke_reads_checkpoint():
    checkpoint = load_checkpoint_state_dict_for_smoke_v0(CHECKPOINT_PATH)

    assert checkpoint["checkpoint_present"] is True
    assert checkpoint["checkpoint_sha256"] == "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    assert checkpoint["checkpoint_size_bytes"] == 17861341
    assert checkpoint["checkpoint_loaded"] is True
    assert checkpoint["checkpoint_payload_type"] == "dict"
    assert checkpoint["has_state_dict"] is True
    assert checkpoint["has_hyper_parameters"] is True
    assert checkpoint["state_dict_key_count"] == 122
    assert checkpoint["state_dict_keys_sample"]
    assert checkpoint["checkpoint_target_fields"]["joint_nf"] == 32
    assert checkpoint["checkpoint_target_fields"]["hidden_nf"] == 128
    assert checkpoint["checkpoint_target_fields"]["n_layers"] == 5
    assert checkpoint["checkpoint_target_fields"]["atom_feature_dim"] == 10
    assert checkpoint["checkpoint_target_fields"]["residue_feature_dim"] == 10


def test_instantiate_model_for_pretrained_load_is_checkpoint_compatible():
    model_result = instantiate_model_for_pretrained_load_v0(device="cpu")

    assert model_result["model_instantiation_attempted"] is True
    assert model_result["model_instantiated"] is True
    assert model_result["model_class"] == "LigandPocketDDPM"
    assert model_result["requested_device"] == "cpu"
    assert model_result["resolved_device"] == "cpu"
    assert model_result["model_state_dict_key_count"] == 122
    assert model_result["shape_match_ratio_vs_checkpoint"] == 1.0
    assert model_result["pre_load_shape_counts"]["pre_load_shape_matched_key_count"] == 122
    assert model_result["pre_load_shape_counts"]["pre_load_incompatible_shape_count"] == 0
    assert model_result["pre_load_shape_counts"]["pre_load_missing_key_count"] == 0
    assert model_result["pre_load_shape_counts"]["pre_load_unexpected_key_count"] == 0


def test_strict_load_checkpoint_weights_succeeds_with_zero_mismatches():
    checkpoint = load_checkpoint_state_dict_for_smoke_v0(CHECKPOINT_PATH)
    model_result = instantiate_model_for_pretrained_load_v0(device="cpu")
    load_result = strict_load_checkpoint_weights_v0(model_result["model"], checkpoint["state_dict"])

    assert load_result["strict_load_attempted"] is True
    assert load_result["strict_load_success"] is True
    assert load_result["missing_keys_count"] == 0
    assert load_result["unexpected_keys_count"] == 0
    assert load_result["incompatible_shape_count"] == 0
    assert load_result["loaded_parameter_key_count"] == 122
    assert load_result["loaded_parameter_tensor_count"] == 122
    assert load_result["loaded_parameter_numel_total"] == 1006560
    assert load_result["pretrained_weights_loaded"] is True
    assert load_result["pretrained_base_integration_proven"] is True


def test_loaded_model_no_grad_forward_smoke_is_finite():
    checkpoint = load_checkpoint_state_dict_for_smoke_v0(CHECKPOINT_PATH)
    model_result = instantiate_model_for_pretrained_load_v0(device="cpu")
    load_result = strict_load_checkpoint_weights_v0(model_result["model"], checkpoint["state_dict"])
    assert load_result["strict_load_success"] is True

    forward = run_loaded_model_no_grad_forward_smoke_v0(
        model_result["model"],
        model_result["input_contract"],
        device="cpu",
    )

    assert forward["forward_smoke_attempted"] is True
    assert forward["forward_smoke_success"] is True
    assert forward["output_finite"] is True
    assert forward["nan_count"] == 0
    assert forward["inf_count"] == 0
    assert forward["output_shape_summary"]["output.0"] == [1]


def test_decision_allows_pretrained_masked_loss_only_after_strict_load_and_forward():
    passed = {"strict_load_success": True}
    forward_passed = {"forward_smoke_success": True}
    forward_blocked = {"forward_smoke_success": False}
    load_blocked = {"strict_load_success": False}

    passed_decision = build_checkpoint_compatible_pretrained_load_decision_v0(passed, forward_passed)
    forward_blocked_decision = build_checkpoint_compatible_pretrained_load_decision_v0(passed, forward_blocked)
    load_blocked_decision = build_checkpoint_compatible_pretrained_load_decision_v0(load_blocked, forward_passed)

    assert passed_decision["load_smoke_status"] == "checkpoint_compatible_pretrained_load_proven"
    assert passed_decision["pretrained_weights_loaded"] is True
    assert passed_decision["pretrained_base_integration_proven"] is True
    assert passed_decision["pretrained_masked_loss_smoke_allowed"] is True
    assert passed_decision["masked_loss_smoke_allowed"] is False
    assert passed_decision["recommended_next_step"] == "pretrained_masked_loss_smoke_on_checkpoint_compatible_model"
    assert forward_blocked_decision["pretrained_masked_loss_smoke_allowed"] is False
    assert forward_blocked_decision["recommended_next_step"] == "loaded_model_forward_smoke_debug"
    assert load_blocked_decision["pretrained_weights_loaded"] is False
    assert load_blocked_decision["recommended_next_step"] == "checkpoint_compatible_strict_load_debug"
    for decision in [passed_decision, forward_blocked_decision, load_blocked_decision]:
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False
        assert decision["quality_claim_allowed"] is False


def test_full_pretrained_load_smoke_manifest_contract():
    result = build_checkpoint_compatible_pretrained_load_smoke_v0(device="cpu")
    manifest = result["manifest"]

    assert manifest["stage"] == "checkpoint_compatible_pretrained_load_smoke_v0"
    assert manifest["previous_stage"] == "checkpoint_compatible_instantiation_wrapper_v0"
    assert manifest["step11d_validated"] is True
    assert manifest["checkpoint_loaded"] is True
    assert manifest["checkpoint_state_dict_key_count"] == 122
    assert manifest["model_instantiated"] is True
    assert manifest["model_class"] == "LigandPocketDDPM"
    assert manifest["requested_device"] == "cpu"
    assert manifest["resolved_device"] == "cpu"
    assert manifest["model_state_dict_key_count"] == 122
    assert manifest["pre_load_shape_matched_key_count"] == 122
    assert manifest["pre_load_shape_matched_ratio"] == 1.0
    assert manifest["pre_load_incompatible_shape_count"] == 0
    assert manifest["strict_load_attempted"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["missing_keys_count"] == 0
    assert manifest["unexpected_keys_count"] == 0
    assert manifest["incompatible_shape_count"] == 0
    assert manifest["loaded_parameter_key_count"] == 122
    assert manifest["loaded_parameter_numel_total"] == 1006560
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["forward_smoke_attempted"] is True
    assert manifest["forward_smoke_success"] is True
    assert manifest["output_finite"] is True
    assert manifest["nan_count"] == 0
    assert manifest["inf_count"] == 0
    assert manifest["load_smoke_status"] == "checkpoint_compatible_pretrained_load_proven"
    assert manifest["pretrained_masked_loss_smoke_allowed"] is True
    assert manifest["masked_loss_smoke_allowed"] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["backward_called"] is False
    assert manifest["optimizer_created"] is False
    assert manifest["optimizer_step_called"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "pretrained_masked_loss_smoke_on_checkpoint_compatible_model"


def test_script_writes_report_manifest_diagnostics_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "checkpoint_compatible_pretrained_load_smoke_v0"
    report_csv = output_root / "checkpoint_compatible_pretrained_load_smoke_report.csv"
    manifest_json = output_root / "checkpoint_compatible_pretrained_load_smoke_manifest.json"
    diagnostics_json = output_root / "checkpoint_compatible_pretrained_load_diagnostics.json"
    summary_md = tmp_path / "docs" / "checkpoint_compatible_pretrained_load_smoke_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "DIAGNOSTICS_JSON", diagnostics_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu", checkpoint_path=CHECKPOINT_PATH, config_preview_path=CONFIG_PREVIEW_PATH) == 0

    rows = _read_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    diagnostics = json.loads(diagnostics_json.read_text(encoding="utf-8"))
    assert len(rows) == 8
    assert all(row["recommended_next_step"] == "pretrained_masked_loss_smoke_on_checkpoint_compatible_model" for row in rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["strict_load_success"] is True
    assert diagnostics["load_result_summary"]["strict_load_success"] is True
    assert diagnostics["nonstrict_diagnostic_only"] is False
    assert "state_dict" not in diagnostics
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not training" in text
    assert "strict_load_success: true" in text


def test_generated_outputs_and_repository_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert DIAGNOSTICS_JSON.is_file()
    assert SUMMARY_MD.is_file()
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert len(_read_csv(REPORT_CSV)) == 8
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
        REPO_ROOT / "src/covalent_ext/checkpoint_compatible_pretrained_load_smoke.py",
        REPO_ROOT / "scripts/check_checkpoint_compatible_pretrained_load_smoke_v0.py",
        REPO_ROOT / "tests/test_checkpoint_compatible_pretrained_load_smoke_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
        "optimizer" + ".step",
        "trainer" + ".fit",
        "backward" + "(",
        "training" + "_step" + "(",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
