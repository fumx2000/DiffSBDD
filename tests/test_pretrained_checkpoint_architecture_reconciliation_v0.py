import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_pretrained_checkpoint_architecture_reconciliation_v0 as script  # noqa: E402
from covalent_ext.pretrained_checkpoint_architecture_reconciliation import (  # noqa: E402
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    MISMATCH_TABLE_CSV,
    MODEL_CONFIG_PATH,
    OUTPUT_ROOT,
    REPORT_CSV,
    SUMMARY_MD,
    build_pretrained_checkpoint_architecture_reconciliation_v0,
    build_reconciliation_decision_v0,
    build_shape_mismatch_table_v0,
    compare_checkpoint_config_current_architecture_v0,
    infer_architecture_from_state_shapes_v0,
    inspect_current_model_architecture_v0,
    load_checkpoint_architecture_evidence_v0,
    load_current_config_evidence_v0,
    optional_candidate_instantiation_smoke_v0,
    search_repo_config_candidates_v0,
    validate_step11a_outputs_v0,
)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11a_outputs_success():
    assert validate_step11a_outputs_v0() is True


def test_load_checkpoint_architecture_evidence_reads_hparams_and_shapes():
    evidence = load_checkpoint_architecture_evidence_v0(CHECKPOINT_PATH)

    assert evidence["checkpoint_present"] is True
    assert evidence["checkpoint_sha256"] == "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    assert evidence["checkpoint_size_bytes"] == 17861341
    assert evidence["payload_type"] == "dict"
    assert evidence["has_state_dict"] is True
    assert evidence["has_hyper_parameters"] is True
    assert evidence["state_dict_key_count"] == 122
    assert "egnn_params" in evidence["hyper_parameters_keys"]
    relevant = evidence["hyper_parameters_relevant_fields"]
    assert relevant["egnn_params.hidden_nf"] == 128
    assert relevant["egnn_params.joint_nf"] == 32
    assert relevant["egnn_params.n_layers"] == 5
    assert relevant["mode"] == "pocket_conditioning"
    assert relevant["pocket_representation"] == "full-atom"
    arch = evidence["checkpoint_architecture_inferred"]
    assert arch["atom_encoder_input_dim"] == 10
    assert arch["egnn_hidden_dim_candidates"] == [128]
    assert arch["egnn_block_count"] == 5


def test_load_current_config_evidence_reads_relevant_fields():
    evidence = load_current_config_evidence_v0(MODEL_CONFIG_PATH)

    assert evidence["config_present"] is True
    assert evidence["config_path"] == str(MODEL_CONFIG_PATH)
    assert evidence["config_text_sha256"]
    relevant = evidence["relevant_config_candidates"]
    assert relevant["egnn_params.hidden_nf"] == 256
    assert relevant["egnn_params.joint_nf"] == 128
    assert relevant["egnn_params.n_layers"] == 6
    assert relevant["mode"] == "pocket_conditioning"
    assert relevant["pocket_representation"] == "full-atom"


def test_inspect_current_model_architecture_instantiates_current_model():
    evidence = inspect_current_model_architecture_v0(device="cpu")

    assert evidence["model_instantiated"] is True
    assert evidence["model_class"] == "LigandPocketDDPM"
    assert evidence["requested_device"] == "cpu"
    assert evidence["resolved_device"] == "cpu"
    assert evidence["model_state_dict_key_count"] == 142
    arch = evidence["current_architecture_inferred"]
    assert arch["atom_encoder_input_dim"] == 11
    assert arch["egnn_hidden_dim_candidates"] == [256]
    assert arch["egnn_block_count"] == 6


def test_infer_architecture_from_state_shapes_parses_expected_keys():
    shape_map = {
        "ddpm.dynamics.atom_encoder.0.weight": [20, 10],
        "ddpm.dynamics.atom_encoder.2.weight": [32, 20],
        "ddpm.dynamics.atom_decoder.0.weight": [20, 32],
        "ddpm.dynamics.atom_decoder.2.weight": [10, 20],
        "ddpm.dynamics.residue_encoder.0.weight": [20, 10],
        "ddpm.dynamics.residue_encoder.2.weight": [32, 20],
        "ddpm.dynamics.egnn.embedding.weight": [128, 33],
        "ddpm.dynamics.egnn.embedding_out.weight": [33, 128],
        "ddpm.dynamics.egnn.e_block_0.gcl_0.edge_mlp.0.weight": [128, 258],
        "ddpm.dynamics.egnn.e_block_1.gcl_0.node_mlp.0.weight": [128, 256],
        "ddpm.dynamics.egnn.e_block_1.gcl_equiv.coord_mlp.0.weight": [128, 258],
    }

    arch = infer_architecture_from_state_shapes_v0(shape_map, "synthetic")

    assert arch["source_name"] == "synthetic"
    assert arch["atom_encoder_input_dim"] == 10
    assert arch["atom_encoder_output_dim"] == 32
    assert arch["egnn_block_indices"] == [0, 1]
    assert arch["egnn_block_count"] == 2
    assert arch["egnn_hidden_dim_candidates"] == [128]
    assert arch["edge_mlp_input_dim_candidates"] == [258]
    assert arch["node_mlp_input_dim_candidates"] == [256]


def test_shape_mismatch_table_contains_atom_and_egnn_categories():
    checkpoint = load_checkpoint_architecture_evidence_v0(CHECKPOINT_PATH)
    current = inspect_current_model_architecture_v0(device="cpu")
    rows = build_shape_mismatch_table_v0(
        checkpoint["state_dict_shape_map"],
        current["model_state_dict_shape_map"],
    )

    assert len(rows) == 142
    statuses = {row["status"] for row in rows}
    categories = {row["category"] for row in rows}
    assert "shape_mismatched" in statuses
    assert "shape_matched" in statuses
    assert "missing_in_checkpoint" in statuses
    assert "unexpected_in_checkpoint" not in statuses
    assert {"atom_encoder", "atom_decoder", "egnn_edge_mlp", "egnn_node_mlp", "egnn_coord_mlp"}.issubset(
        categories
    )
    assert any(row["inferred_reason"] == "egnn_layer_count_mismatch" for row in rows)


def test_compare_checkpoint_config_current_architecture_identifies_root_causes():
    checkpoint = load_checkpoint_architecture_evidence_v0(CHECKPOINT_PATH)
    config = load_current_config_evidence_v0(MODEL_CONFIG_PATH)
    current = inspect_current_model_architecture_v0(device="cpu")

    comparison = compare_checkpoint_config_current_architecture_v0(checkpoint, config, current)

    root_causes = set(comparison["likely_root_causes"])
    assert root_causes & {"hidden_dim_mismatch", "atom_feature_dim_mismatch", "egnn_layer_count_mismatch"}
    assert "hidden_dim_mismatch" in root_causes
    assert "atom_feature_dim_mismatch" in root_causes
    assert "egnn_layer_count_mismatch" in root_causes
    assert comparison["confidence_by_root_cause"]["hidden_dim_mismatch"] == "high"
    assert comparison["current_config_not_checkpoint_config"] is True
    assert comparison["checkpoint_config_recovery_required"] is True


def test_config_search_and_decision_do_not_allow_masked_loss_smoke():
    checkpoint = load_checkpoint_architecture_evidence_v0(CHECKPOINT_PATH)
    config = load_current_config_evidence_v0(MODEL_CONFIG_PATH)
    current = inspect_current_model_architecture_v0(device="cpu")
    comparison = compare_checkpoint_config_current_architecture_v0(checkpoint, config, current)
    search = search_repo_config_candidates_v0(checkpoint)
    candidate = optional_candidate_instantiation_smoke_v0(search["best_config_candidate_path"])
    decision = build_reconciliation_decision_v0(comparison, search, candidate)

    assert search["config_candidate_count"] >= 1
    assert search["best_config_candidate_path"] == "configs/crossdock_fullatom_joint.yml"
    assert search["best_config_candidate_score"] >= 4
    assert candidate["candidate_instantiation_attempted"] is False
    assert decision["pretrained_masked_loss_smoke_allowed"] is False
    assert decision["masked_loss_smoke_allowed"] is False
    assert decision["formal_training_allowed"] is False
    assert decision["finetune_allowed"] is False
    assert decision["quality_claim_allowed"] is False
    assert decision["loss_decrease_required"] is False
    assert decision["reconciliation_status"] == "checkpoint_original_config_recovery_needed"
    assert decision["recommended_next_step"] == "checkpoint_original_config_model_instantiation_design"


def test_build_full_reconciliation_manifest_contract():
    result = build_pretrained_checkpoint_architecture_reconciliation_v0(
        device="cpu",
        checkpoint_path=CHECKPOINT_PATH,
        config_path=MODEL_CONFIG_PATH,
    )
    manifest = result["manifest"]

    assert manifest["stage"] == "pretrained_checkpoint_architecture_reconciliation_v0"
    assert manifest["previous_stage"] == "pretrained_checkpoint_load_smoke_v0"
    assert manifest["step11a_validated"] is True
    assert manifest["checkpoint_has_hyper_parameters"] is True
    assert manifest["checkpoint_state_dict_key_count"] == 122
    assert manifest["current_config_present"] is True
    assert manifest["current_model_instantiated"] is True
    assert manifest["matched_key_count"] == 122
    assert manifest["shape_matched_key_count"] == 7
    assert manifest["shape_matched_ratio"] == 0.05737704918032787
    assert manifest["incompatible_shape_count"] == 115
    assert manifest["missing_key_count"] == 20
    assert manifest["unexpected_key_count"] == 0
    assert "hidden_dim_mismatch" in manifest["likely_root_causes"]
    assert "atom_feature_dim_mismatch" in manifest["likely_root_causes"]
    assert "egnn_layer_count_mismatch" in manifest["likely_root_causes"]
    assert manifest["current_config_not_checkpoint_config"] is True
    assert manifest["checkpoint_config_recovery_required"] is True
    assert manifest["pretrained_masked_loss_smoke_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
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


def test_script_writes_report_manifest_mismatch_table_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "pretrained_checkpoint_architecture_reconciliation_v0"
    report_csv = output_root / "pretrained_checkpoint_architecture_reconciliation_report.csv"
    manifest_json = output_root / "pretrained_checkpoint_architecture_reconciliation_manifest.json"
    mismatch_csv = output_root / "pretrained_checkpoint_shape_mismatch_table.csv"
    summary_md = tmp_path / "docs" / "pretrained_checkpoint_architecture_reconciliation_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "MISMATCH_TABLE_CSV", mismatch_csv)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run(device="cpu", checkpoint_path=CHECKPOINT_PATH, config_path=MODEL_CONFIG_PATH) == 0

    rows = _read_csv(report_csv)
    assert len(rows) == 10
    assert all(row["stage"] == "pretrained_checkpoint_architecture_reconciliation_v0" for row in rows)
    assert all(row["recommended_next_step"] == "checkpoint_original_config_model_instantiation_design" for row in rows)
    assert all(row["status"] == "passed" for row in rows)
    mismatch_rows = _read_csv(mismatch_csv)
    assert len(mismatch_rows) == 142
    assert any(row["status"] == "shape_mismatched" for row in mismatch_rows)
    assert any(row["category"] == "atom_encoder" for row in mismatch_rows)
    assert any(row["category"] == "egnn_edge_mlp" for row in mismatch_rows)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["all_checks_passed"] is True
    assert manifest["pretrained_masked_loss_smoke_allowed"] is False
    assert summary_md.is_file()
    assert "not training" in summary_md.read_text(encoding="utf-8")


def test_generated_outputs_and_repository_safety_boundary():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert MISMATCH_TABLE_CSV.is_file()
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
        REPO_ROOT / "src/covalent_ext/pretrained_checkpoint_architecture_reconciliation.py",
        REPO_ROOT / "scripts/check_pretrained_checkpoint_architecture_reconciliation_v0.py",
        REPO_ROOT / "tests/test_pretrained_checkpoint_architecture_reconciliation_v0.py",
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
