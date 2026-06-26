import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_checkpoint_compatible_instantiation_wrapper_v0 as script  # noqa: E402
from covalent_ext.checkpoint_compatible_model_instantiation import (  # noqa: E402
    BEST_CONFIG_CANDIDATE_PATH,
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_CONTRACT_PREVIEW_JSON,
    MANIFEST_JSON,
    OUTPUT_ROOT,
    PREVIOUS_SHAPE_MATCH_RATIO,
    REPORT_CSV,
    SHAPE_MATCH_GOAL,
    SHAPE_MATCH_TABLE_CSV,
    SUMMARY_MD,
    build_checkpoint_compatible_config_v0,
    build_checkpoint_compatible_input_contract_v0,
    build_checkpoint_compatible_instantiation_decision_v0,
    build_checkpoint_compatible_instantiation_wrapper_v0,
    build_checkpoint_compatible_shape_match_table_v0,
    instantiate_checkpoint_compatible_model_v0,
    load_checkpoint_shape_reference_v0,
    load_config_preview_v0,
    validate_step11c_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11c_outputs_success():
    assert validate_step11c_outputs_v0() is True


def test_load_checkpoint_shape_reference_reads_expected_shapes():
    reference = load_checkpoint_shape_reference_v0(CHECKPOINT_PATH)

    assert reference["checkpoint_present"] is True
    assert reference["checkpoint_sha256"] == "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    assert reference["checkpoint_size_bytes"] == 17861341
    assert reference["has_state_dict"] is True
    assert reference["has_hyper_parameters"] is True
    assert reference["state_dict_key_count"] == 122
    assert reference["checkpoint_target_fields"]["joint_nf"] == 32
    assert reference["checkpoint_target_fields"]["hidden_nf"] == 128
    assert reference["checkpoint_target_fields"]["n_layers"] == 5
    assert reference["checkpoint_target_fields"]["mode"] == "pocket_conditioning"
    assert reference["checkpoint_target_fields"]["pocket_representation"] == "full-atom"
    assert reference["checkpoint_target_fields"]["atom_feature_dim"] == 10
    assert reference["checkpoint_target_fields"]["residue_feature_dim"] == 10
    assert reference["checkpoint_target_fields"]["egnn_blocks"] == 5


def test_load_config_preview_reads_target_dims():
    preview = load_config_preview_v0(CONFIG_PREVIEW_PATH)

    assert preview["config_preview_loaded"] is True
    data = preview["preview"]
    assert data["target_egnn_params"] == {"joint_nf": 32, "hidden_nf": 128, "n_layers": 5}
    assert data["target_mode"] == "pocket_conditioning"
    assert data["target_pocket_representation"] == "full-atom"
    assert data["target_atom_feature_dim"] == 10
    assert data["target_residue_feature_dim"] == 10
    assert data["target_egnn_blocks"] == 5
    assert data["expected_shape_match_goal"]["shape_matched_ratio_minimum"] == SHAPE_MATCH_GOAL


def test_build_checkpoint_compatible_config_applies_overrides():
    preview = load_config_preview_v0(CONFIG_PREVIEW_PATH)["preview"]
    compatible = build_checkpoint_compatible_config_v0(preview, BEST_CONFIG_CANDIDATE_PATH)

    assert compatible["compatible_config_built"] is True
    fields = compatible["compatible_config_flattened_relevant_fields"]
    assert fields["mode"] == "pocket_conditioning"
    assert fields["pocket_representation"] == "full-atom"
    assert fields["virtual_nodes"] is False
    assert fields["egnn_params.joint_nf"] == 32
    assert fields["egnn_params.hidden_nf"] == 128
    assert fields["egnn_params.n_layers"] == 5
    assert compatible["unresolved_fields"]


def test_build_input_contract_records_10d_shape_only_contract():
    reference = load_checkpoint_shape_reference_v0(CHECKPOINT_PATH)
    preview = load_config_preview_v0(CONFIG_PREVIEW_PATH)["preview"]
    compatible = build_checkpoint_compatible_config_v0(preview, BEST_CONFIG_CANDIDATE_PATH)
    contract = build_checkpoint_compatible_input_contract_v0(reference, preview, compatible)

    assert contract["input_contract_built"] is True
    assert contract["target_atom_feature_dim"] == 10
    assert contract["target_residue_feature_dim"] == 10
    assert contract["target_ligand_feature_dim"] == 10
    assert contract["target_pocket_feature_dim"] == 10
    assert contract["current_default_atom_feature_dim"] == 11
    assert contract["current_default_crossdock_full_contract_used"] is False
    assert contract["feature_semantics_known"] is False
    assert contract["feature_semantics_status"] == "shape_only_contract_for_instantiation_smoke"
    assert contract["synthetic_forward_candidate_safe"] is True


def test_instantiate_checkpoint_compatible_model_shape_match_improves():
    result = instantiate_checkpoint_compatible_model_v0(CHECKPOINT_PATH, CONFIG_PREVIEW_PATH, device="cpu")

    assert result["wrapper_invoked"] is True
    assert result["step11c_validated"] is True
    assert result["checkpoint_reference_loaded"] is True
    assert result["config_preview_loaded"] is True
    assert result["compatible_config_built"] is True
    assert result["input_contract_built"] is True
    assert result["model_instantiation_attempted"] is True
    assert result["model_instantiated"] is True
    assert result["model_class"] == "LigandPocketDDPM"
    assert result["resolved_device"] == "cpu"
    assert result["model_state_dict_key_count"] == 122
    assert result["matched_key_count"] == 122
    assert result["shape_matched_key_count"] == 122
    assert result["shape_matched_ratio"] == 1.0
    assert result["shape_matched_ratio"] > PREVIOUS_SHAPE_MATCH_RATIO
    assert result["incompatible_shape_count"] == 0
    assert result["missing_key_count"] == 0
    assert result["unexpected_key_count"] == 0
    assert result["reached_shape_match_goal"] is True
    assert result["wrapper_status"] == "checkpoint_compatible_instantiation_proven"


def test_shape_match_table_is_written_from_model_and_checkpoint_shapes():
    result = instantiate_checkpoint_compatible_model_v0(CHECKPOINT_PATH, CONFIG_PREVIEW_PATH, device="cpu")
    table = build_checkpoint_compatible_shape_match_table_v0(result["checkpoint_shape_map"], result["model_shape_map"])

    assert len(table) == 122
    assert all(row["status"] == "shape_matched" for row in table)
    assert {row["category"] for row in table} >= {"atom_encoder", "atom_decoder", "residue_encoder", "egnn_edge_mlp"}


def test_decision_allows_load_smoke_only_after_shape_goal():
    high = {"model_instantiated": True, "shape_matched_ratio": 1.0}
    low = {"model_instantiated": True, "shape_matched_ratio": 0.5}
    blocked = {"model_instantiated": False, "shape_matched_ratio": 0.0}

    high_decision = build_checkpoint_compatible_instantiation_decision_v0(high, {})
    low_decision = build_checkpoint_compatible_instantiation_decision_v0(low, {})
    blocked_decision = build_checkpoint_compatible_instantiation_decision_v0(blocked, {})

    assert high_decision["checkpoint_load_smoke_allowed"] is True
    assert high_decision["recommended_next_step"] == "checkpoint_compatible_pretrained_load_smoke"
    assert low_decision["checkpoint_load_smoke_allowed"] is False
    assert low_decision["recommended_next_step"] == "checkpoint_compatible_wrapper_repair"
    assert blocked_decision["checkpoint_load_smoke_allowed"] is False
    assert blocked_decision["recommended_next_step"] == "checkpoint_compatible_wrapper_debug"
    for decision in [high_decision, low_decision, blocked_decision]:
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False
        assert decision["masked_loss_smoke_allowed"] is False
        assert decision["pretrained_masked_loss_smoke_allowed"] is False


def test_full_wrapper_manifest_contract():
    result = build_checkpoint_compatible_instantiation_wrapper_v0(device="cpu")
    manifest = result["manifest"]

    assert manifest["stage"] == "checkpoint_compatible_instantiation_wrapper_v0"
    assert manifest["previous_stage"] == "checkpoint_original_config_instantiation_design_v0"
    assert manifest["step11c_validated"] is True
    assert manifest["compatible_config_built"] is True
    assert manifest["input_contract_built"] is True
    assert manifest["target_joint_nf"] == 32
    assert manifest["target_hidden_nf"] == 128
    assert manifest["target_n_layers"] == 5
    assert manifest["target_mode"] == "pocket_conditioning"
    assert manifest["target_pocket_representation"] == "full-atom"
    assert manifest["target_atom_feature_dim"] == 10
    assert manifest["target_residue_feature_dim"] == 10
    assert manifest["target_egnn_blocks"] == 5
    assert manifest["model_instantiated"] is True
    assert manifest["shape_matched_key_count"] == 122
    assert manifest["shape_matched_ratio"] == 1.0
    assert manifest["reached_shape_match_goal"] is True
    assert manifest["forward_smoke_attempted"] is True
    assert manifest["forward_smoke_success"] is True
    assert manifest["output_finite"] is True
    assert manifest["checkpoint_load_smoke_allowed"] is True
    assert manifest["recommended_next_step"] == "checkpoint_compatible_pretrained_load_smoke"
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["masked_loss_smoke_allowed"] is False
    assert manifest["pretrained_masked_loss_smoke_allowed"] is False
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


def test_script_writes_report_manifest_shape_table_contract_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "checkpoint_compatible_instantiation_wrapper_v0"
    report_csv = output_root / "checkpoint_compatible_instantiation_report.csv"
    manifest_json = output_root / "checkpoint_compatible_instantiation_manifest.json"
    shape_table_csv = output_root / "checkpoint_compatible_shape_match_table.csv"
    input_contract_json = output_root / "checkpoint_compatible_input_contract_preview.json"
    summary_md = tmp_path / "docs" / "checkpoint_compatible_instantiation_wrapper_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "SHAPE_MATCH_TABLE_CSV", shape_table_csv)
    monkeypatch.setattr(script, "INPUT_CONTRACT_PREVIEW_JSON", input_contract_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu", checkpoint_path=CHECKPOINT_PATH, config_preview_path=CONFIG_PREVIEW_PATH) == 0

    rows = _read_csv(report_csv)
    shape_rows = _read_csv(shape_table_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    contract = json.loads(input_contract_json.read_text(encoding="utf-8"))
    assert len(rows) == 10
    assert len(shape_rows) == 122
    assert all(row["recommended_next_step"] == "checkpoint_compatible_pretrained_load_smoke" for row in rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["shape_matched_ratio"] == 1.0
    assert contract["target_atom_feature_dim"] == 10
    assert contract["feature_semantics_known"] is False
    assert summary_md.is_file()
    assert "not training" in summary_md.read_text(encoding="utf-8")


def test_generated_outputs_and_repository_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert SHAPE_MATCH_TABLE_CSV.is_file()
    assert INPUT_CONTRACT_PREVIEW_JSON.is_file()
    assert SUMMARY_MD.is_file()
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["shape_matched_key_count"] == 122
    assert len(_read_csv(REPORT_CSV)) == 10
    assert len(_read_csv(SHAPE_MATCH_TABLE_CSV)) == 122
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
        REPO_ROOT / "src/covalent_ext/checkpoint_compatible_model_instantiation.py",
        REPO_ROOT / "scripts/check_checkpoint_compatible_instantiation_wrapper_v0.py",
        REPO_ROOT / "tests/test_checkpoint_compatible_instantiation_wrapper_v0.py",
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
