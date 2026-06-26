import csv
import functools
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_pretrained_masked_loss_smoke_v0 as script  # noqa: E402
from covalent_ext.pretrained_masked_loss_smoke import (  # noqa: E402
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    LOSS_TABLE_CSV,
    MANIFEST_JSON,
    MASK_LEVELS,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_pretrained_masked_loss_candidate_inputs_v0,
    build_pretrained_masked_loss_smoke_decision_v0,
    build_pretrained_masked_loss_smoke_v0,
    build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0,
    run_pretrained_masked_loss_smoke_for_level_v0,
    validate_step11e_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@functools.lru_cache(maxsize=1)
def _cached_result_json_text():
    result = build_pretrained_masked_loss_smoke_v0(device="cpu")
    return json.dumps(result, default=str)


def _cached_result():
    return json.loads(_cached_result_json_text())


def test_validate_step11e_outputs_success():
    assert validate_step11e_outputs_v0() is True


def test_strict_loaded_model_builder_succeeds():
    result = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(device="cpu")

    assert result["model_instantiated"] is True
    assert result["strict_load_success"] is True
    assert result["pretrained_weights_loaded"] is True
    assert result["pretrained_base_integration_proven"] is True
    assert result["load_result"]["loaded_parameter_key_count"] == 122
    assert result["load_result"]["loaded_parameter_numel_total"] == 1006560


def test_candidate_inputs_build_for_all_mask_levels():
    input_contract = {"target_ligand_feature_dim": 10, "target_pocket_feature_dim": 10}
    expected_counts = {
        "A_warhead_only": (2, 2),
        "B_linker_warhead": (3, 1),
        "B2_scaffold_warhead": (3, 1),
        "C_scaffold_linker_warhead": (4, 0),
    }

    for mask_level in MASK_LEVELS:
        candidate = build_pretrained_masked_loss_candidate_inputs_v0(mask_level, input_contract, device="cpu")
        data_batch = candidate["data_batch"]
        metadata = candidate["metadata"]
        expected_target, expected_context = expected_counts[mask_level]

        assert data_batch["lig_coords"].shape == (4, 3)
        assert data_batch["lig_one_hot"].shape == (4, 10)
        assert data_batch["pocket_coords"].shape == (5, 3)
        assert data_batch["pocket_one_hot"].shape == (5, 10)
        assert metadata["target_atom_count"] == expected_target
        assert metadata["context_atom_count"] == expected_context
        assert metadata["synthetic_shape_smoke_only"] is True
        assert metadata["feature_semantics_known"] is False
        assert metadata["not_training_data"] is True


def test_each_mask_level_smoke_has_finite_loss():
    bundle = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(device="cpu")
    assert bundle["strict_load_success"] is True

    for mask_level in MASK_LEVELS:
        result = run_pretrained_masked_loss_smoke_for_level_v0(
            bundle["model"],
            mask_level,
            bundle["input_contract"],
            device="cpu",
        )
        assert result["candidate_inputs_built"] is True
        assert result["forward_success"] is True
        assert result["loss_hook_success"] is True
        assert result["finite_loss"] is True
        assert result["status"] == "passed"
        assert result["selected_primary_loss_key"] in {
            "masked_loss_total_dry",
            "error_t_lig",
            "loss_0",
            "kl_prior",
            "output0_mean",
        }
        assert result["nan_count"] == 0
        assert result["inf_count"] == 0


def test_full_smoke_manifest_contract():
    result = _cached_result()
    manifest = result["manifest"]

    assert manifest["stage"] == "pretrained_masked_loss_smoke_v0"
    assert manifest["previous_stage"] == "checkpoint_compatible_pretrained_load_smoke_v0"
    assert manifest["step11e_validated"] is True
    assert manifest["pretrained_weights_loaded"] is True
    assert manifest["pretrained_base_integration_proven"] is True
    assert manifest["model_instantiated"] is True
    assert manifest["strict_load_success"] is True
    assert manifest["requested_device"] == "cpu"
    assert manifest["resolved_device"] == "cpu"
    assert manifest["mask_levels_attempted"] == MASK_LEVELS
    assert manifest["mask_levels_passed"] == MASK_LEVELS
    assert manifest["all_mask_levels_passed"] is True
    assert manifest["finite_loss_level_count"] == 4
    assert manifest["failed_mask_levels"] == []
    assert manifest["synthetic_shape_smoke_only"] is True
    assert manifest["feature_semantics_known"] is False
    assert manifest["synthetic_mask_loss_adapter_used"] is True
    assert manifest["pretrained_masked_loss_smoke_passed"] is True
    assert manifest["pretrained_model_mask_hook_integration_proven"] is True
    assert manifest["masked_loss_smoke_status"] == "pretrained_masked_loss_smoke_passed"
    assert manifest["microbatch_dry_run_allowed"] is True
    assert manifest["recommended_next_step"] == "pretrained_masked_loss_microbatch_dry_run_design"
    assert manifest["all_checks_passed"] is True


def test_decision_only_allows_microbatch_when_all_levels_pass():
    load_evidence = {
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
    }
    all_passed = {"all_mask_levels_passed": True}
    partial = {"all_mask_levels_passed": False}
    unavailable = {"strict_load_success": False}

    passed_decision = build_pretrained_masked_loss_smoke_decision_v0(load_evidence, all_passed)
    partial_decision = build_pretrained_masked_loss_smoke_decision_v0(load_evidence, partial)
    unavailable_decision = build_pretrained_masked_loss_smoke_decision_v0(unavailable, all_passed)

    assert passed_decision["microbatch_dry_run_allowed"] is True
    assert passed_decision["recommended_next_step"] == "pretrained_masked_loss_microbatch_dry_run_design"
    assert partial_decision["microbatch_dry_run_allowed"] is False
    assert partial_decision["recommended_next_step"] == "pretrained_masked_loss_failed_level_debug"
    assert unavailable_decision["recommended_next_step"] == "checkpoint_compatible_pretrained_load_smoke_debug"
    for decision in [passed_decision, partial_decision, unavailable_decision]:
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False
        assert decision["optimizer_allowed"] is False
        assert decision["quality_claim_allowed"] is False


def test_script_writes_report_manifest_loss_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "pretrained_masked_loss_smoke_v0"
    report_csv = output_root / "pretrained_masked_loss_smoke_report.csv"
    manifest_json = output_root / "pretrained_masked_loss_smoke_manifest.json"
    loss_table_csv = output_root / "pretrained_masked_loss_smoke_loss_table.csv"
    summary_md = tmp_path / "docs" / "pretrained_masked_loss_smoke_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "LOSS_TABLE_CSV", loss_table_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu", checkpoint_path=CHECKPOINT_PATH, config_preview_path=CONFIG_PREVIEW_PATH) == 0

    report_rows = _read_csv(report_csv)
    loss_rows = _read_csv(loss_table_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert len(report_rows) == 9
    assert len(loss_rows) == 4
    assert all(row["status"] == "passed" for row in loss_rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["all_mask_levels_passed"] is True
    assert summary_md.is_file()
    text = summary_md.read_text(encoding="utf-8")
    assert "not training" in text
    assert "synthetic 10D shape-only contract" in text


def test_generated_outputs_and_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert LOSS_TABLE_CSV.is_file()
    assert SUMMARY_MD.is_file()

    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    rows = _read_csv(LOSS_TABLE_CSV)
    assert manifest["all_checks_passed"] is True
    assert len(_read_csv(REPORT_CSV)) == 9
    assert len(rows) == 4
    assert all(row["status"] == "passed" for row in rows)
    for key in [
        "training_allowed",
        "formal_training_allowed",
        "finetune_allowed",
        "optimizer_allowed",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_saved",
        "model_saved",
    ]:
        assert manifest[key] is False
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


def test_no_diffsbdd_source_modification():
    source_diff = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    staged_source_diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert source_diff.returncode == 0
    assert staged_source_diff.returncode == 0


def test_source_files_do_not_contain_forbidden_training_or_save_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/pretrained_masked_loss_smoke.py",
        REPO_ROOT / "scripts/check_pretrained_masked_loss_smoke_v0.py",
        REPO_ROOT / "tests/test_pretrained_masked_loss_smoke_v0.py",
    ]
    forbidden = [
        "torch" + ".save",
        "optimizer" + ".step",
        "trainer" + ".fit",
        "training" + "_step" + "(",
        "backward" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
