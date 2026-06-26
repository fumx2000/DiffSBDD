import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_checkpoint_original_config_instantiation_design_v0 as script  # noqa: E402
from covalent_ext.checkpoint_original_config_instantiation_design import (  # noqa: E402
    BEST_CONFIG_CANDIDATE_PATH,
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_JSON,
    CURRENT_CONFIG_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_checkpoint_original_config_instantiation_design_v0,
    build_checkpoint_original_config_preview_v0,
    build_instantiation_design_decision_v0,
    design_checkpoint_compatible_instantiation_wrapper_v0,
    inspect_existing_instantiation_paths_v0,
    load_checkpoint_hparams_for_design_v0,
    load_config_for_design_v0,
    validate_step11b_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11b_outputs_success():
    assert validate_step11b_outputs_v0() is True


def test_checkpoint_hparams_are_read_and_complete_for_design():
    evidence = load_checkpoint_hparams_for_design_v0(CHECKPOINT_PATH)

    assert evidence["checkpoint_hparams_loaded"] is True
    assert evidence["checkpoint_hparams_complete_for_instantiation"] is True
    assert "egnn_params" in evidence["hyper_parameters_keys"]
    assert evidence["checkpoint_target_joint_nf"] == 32
    assert evidence["checkpoint_target_hidden_nf"] == 128
    assert evidence["checkpoint_target_n_layers"] == 5
    assert evidence["checkpoint_target_mode"] == "pocket_conditioning"
    assert evidence["checkpoint_target_pocket_representation"] == "full-atom"
    assert evidence["checkpoint_target_virtual_nodes"] is False
    assert evidence["checkpoint_target_atom_feature_dim"] == 10
    assert evidence["checkpoint_target_residue_feature_dim"] == 10
    assert evidence["checkpoint_target_egnn_embedding_input_dim"] == 33
    assert evidence["checkpoint_target_egnn_embedding_output_dim"] == 128
    assert evidence["checkpoint_target_egnn_blocks"] == 5


def test_current_and_best_candidate_configs_are_read():
    current = load_config_for_design_v0(CURRENT_CONFIG_PATH)
    candidate = load_config_for_design_v0(BEST_CONFIG_CANDIDATE_PATH)

    assert current["config_loaded"] is True
    assert current["joint_nf"] == 128
    assert current["hidden_nf"] == 256
    assert current["n_layers"] == 6
    assert current["mode"] == "pocket_conditioning"
    assert current["pocket_representation"] == "full-atom"
    assert candidate["config_loaded"] is True
    assert candidate["joint_nf"] == 32
    assert candidate["hidden_nf"] == 128
    assert candidate["n_layers"] == 5
    assert candidate["mode"] == "joint"
    assert candidate["pocket_representation"] == "full-atom"


def test_existing_instantiation_paths_show_wrapper_is_needed():
    paths = inspect_existing_instantiation_paths_v0()

    assert paths["instantiation_helpers_found"] is True
    assert "_instantiate_model_for_forward" in paths["helper_function_names"]
    assert "build_minimal_diffsbdd_instantiation_config_v0" in paths["helper_function_names"]
    assert paths["config_path_hardcoded_or_defaulted"] is True
    assert paths["candidate_inputs_dependency"] is True
    assert paths["model_factory_dependency"]
    assert paths["safe_config_override_supported"] is False
    assert paths["safe_config_override_blockers"]
    assert paths["minimal_required_changes_for_safe_override"]


def test_checkpoint_original_config_preview_contains_target_values():
    checkpoint = load_checkpoint_hparams_for_design_v0(CHECKPOINT_PATH)
    current = load_config_for_design_v0(CURRENT_CONFIG_PATH)
    candidate = load_config_for_design_v0(BEST_CONFIG_CANDIDATE_PATH)

    preview = build_checkpoint_original_config_preview_v0(checkpoint, candidate, current)

    assert preview["source"] == "checkpoint_hyper_parameters_plus_repo_config_template"
    assert preview["base_template_candidate"] == str(BEST_CONFIG_CANDIDATE_PATH)
    assert preview["current_config_reference"] == str(CURRENT_CONFIG_PATH)
    assert preview["target_mode"] == "pocket_conditioning"
    assert preview["target_pocket_representation"] == "full-atom"
    assert preview["target_egnn_params"] == {"joint_nf": 32, "hidden_nf": 128, "n_layers": 5}
    assert preview["target_atom_feature_dim"] == 10
    assert preview["target_residue_feature_dim"] == 10
    assert preview["target_egnn_embedding_input_dim"] == 33
    assert preview["target_egnn_embedding_output_dim"] == 128
    assert preview["target_egnn_blocks"] == 5
    assert preview["expected_checkpoint_state_dict_key_count"] == 122
    assert preview["expected_shape_match_goal"]["shape_matched_ratio_minimum"] == 0.8
    assert "egnn_params.hidden_nf" in preview["config_fields_to_override"]
    assert preview["config_fields_requiring_manual_resolution"]
    assert preview["risks"]


def test_wrapper_design_and_decision_block_training_paths():
    checkpoint = load_checkpoint_hparams_for_design_v0(CHECKPOINT_PATH)
    current = load_config_for_design_v0(CURRENT_CONFIG_PATH)
    candidate = load_config_for_design_v0(BEST_CONFIG_CANDIDATE_PATH)
    paths = inspect_existing_instantiation_paths_v0()
    preview = build_checkpoint_original_config_preview_v0(checkpoint, candidate, current)
    wrapper = design_checkpoint_compatible_instantiation_wrapper_v0(preview, paths)
    decision = build_instantiation_design_decision_v0(checkpoint, paths)

    assert wrapper["proposed_wrapper_name"] == "instantiate_checkpoint_compatible_model_v0"
    assert wrapper["proposed_location"] == "src/covalent_ext/checkpoint_compatible_model_instantiation.py"
    assert wrapper["requires_wrapper"] is True
    assert wrapper["input_arguments"]["allow_source_modification"] is False
    assert wrapper["safety"]["no_optimizer"] is True
    assert wrapper["safety"]["no_gradient_pass"] is True
    assert wrapper["safety"]["no_checkpoint_or_model_serialization"] is True
    assert decision["design_status"] == "wrapper_needed_for_checkpoint_compatible_instantiation"
    assert decision["recommended_next_step"] == "checkpoint_compatible_instantiation_wrapper_prototype"
    assert decision["checkpoint_compatible_instantiation_feasible"] is True
    assert decision["training_allowed"] is False
    assert decision["formal_training_allowed"] is False
    assert decision["finetune_allowed"] is False
    assert decision["masked_loss_smoke_allowed"] is False
    assert decision["pretrained_masked_loss_smoke_allowed"] is False
    assert decision["quality_claim_allowed"] is False
    assert decision["loss_decrease_required"] is False


def test_full_design_manifest_contract():
    result = build_checkpoint_original_config_instantiation_design_v0()
    manifest = result["manifest"]

    assert manifest["stage"] == "checkpoint_original_config_instantiation_design_v0"
    assert manifest["previous_stage"] == "pretrained_checkpoint_architecture_reconciliation_v0"
    assert manifest["step11b_validated"] is True
    assert manifest["checkpoint_hparams_loaded"] is True
    assert manifest["checkpoint_hparams_complete_for_instantiation"] is True
    assert manifest["checkpoint_target_joint_nf"] == 32
    assert manifest["checkpoint_target_hidden_nf"] == 128
    assert manifest["checkpoint_target_n_layers"] == 5
    assert manifest["checkpoint_target_mode"] == "pocket_conditioning"
    assert manifest["checkpoint_target_pocket_representation"] == "full-atom"
    assert manifest["checkpoint_target_atom_feature_dim"] == 10
    assert manifest["checkpoint_target_residue_feature_dim"] == 10
    assert manifest["checkpoint_target_egnn_blocks"] == 5
    assert manifest["current_config_joint_nf"] == 128
    assert manifest["current_config_hidden_nf"] == 256
    assert manifest["current_config_n_layers"] == 6
    assert manifest["best_config_candidate_path"] == str(BEST_CONFIG_CANDIDATE_PATH)
    assert manifest["best_config_candidate_loaded"] is True
    assert manifest["safe_config_override_supported"] is False
    assert manifest["safe_config_override_blockers"]
    assert manifest["config_preview_written"] is True
    assert manifest["proposed_wrapper_name"] == "instantiate_checkpoint_compatible_model_v0"
    assert manifest["checkpoint_compatible_instantiation_feasible"] is True
    assert manifest["design_status"] == "wrapper_needed_for_checkpoint_compatible_instantiation"
    assert manifest["recommended_next_step"] in {
        "checkpoint_compatible_model_instantiation_smoke",
        "checkpoint_compatible_instantiation_wrapper_prototype",
        "manual_checkpoint_hparams_recovery",
        "manual_config_candidate_review",
    }
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["masked_loss_smoke_allowed"] is False
    assert manifest["pretrained_masked_loss_smoke_allowed"] is False
    assert manifest["quality_claim_allowed"] is False
    assert manifest["loss_decrease_required"] is False
    assert manifest["backward_called"] is False
    assert manifest["optimizer_created"] is False
    assert manifest["optimizer_step_called"] is False
    assert manifest["training_step_called"] is False
    assert manifest["trainer_fit_called"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["original_source_files_modified"] is False
    assert manifest["forbidden_artifacts_created"] is False
    assert manifest["all_checks_passed"] is True


def test_script_writes_report_manifest_config_preview_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "checkpoint_original_config_instantiation_design_v0"
    report_csv = output_root / "checkpoint_original_config_instantiation_design_report.csv"
    manifest_json = output_root / "checkpoint_original_config_instantiation_design_manifest.json"
    preview_json = output_root / "checkpoint_original_config_preview.json"
    summary_md = tmp_path / "docs" / "checkpoint_original_config_instantiation_design_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "CONFIG_PREVIEW_JSON", preview_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    rows = _read_csv(report_csv)
    assert len(rows) == 8
    assert all(row["stage"] == "checkpoint_original_config_instantiation_design_v0" for row in rows)
    assert all(row["status"] == "passed" for row in rows)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    preview = json.loads(preview_json.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "checkpoint_compatible_instantiation_wrapper_prototype"
    assert preview["target_egnn_params"]["joint_nf"] == 32
    assert preview["target_egnn_params"]["hidden_nf"] == 128
    assert preview["target_egnn_params"]["n_layers"] == 5
    assert preview["target_atom_feature_dim"] == 10
    assert preview["target_residue_feature_dim"] == 10
    assert summary_md.is_file()
    assert "not training" in summary_md.read_text(encoding="utf-8")


def test_generated_outputs_and_repository_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert CONFIG_PREVIEW_JSON.is_file()
    assert SUMMARY_MD.is_file()
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    preview = json.loads(CONFIG_PREVIEW_JSON.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert preview["target_egnn_params"]["hidden_nf"] == 128
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
        REPO_ROOT / "src/covalent_ext/checkpoint_original_config_instantiation_design.py",
        REPO_ROOT / "scripts/check_checkpoint_original_config_instantiation_design_v0.py",
        REPO_ROOT / "tests/test_checkpoint_original_config_instantiation_design_v0.py",
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
