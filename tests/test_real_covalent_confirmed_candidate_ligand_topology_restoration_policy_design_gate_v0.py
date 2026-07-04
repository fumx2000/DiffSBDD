from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate as gate,
)


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _schema_rows() -> list[dict[str, str]]:
    with gate.OBSERVED_TOPOLOGY_SCHEMA_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _rule_rows() -> list[dict[str, str]]:
    with gate.COVALENT_RESTORATION_RULE_REGISTRY_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _candidate_rows() -> list[dict[str, str]]:
    with gate.LIGAND_TOPOLOGY_RESTORATION_CANDIDATE_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13l_precondition_and_input_tables() -> None:
    assert gate.validate_step13l_pocket_extraction_smoke_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13l_pocket_extraction_smoke_validated"] is True
    assert manifest["ligand_full_atom_table_csv_read"] is True
    assert manifest["pocket_atom_table_csv_read"] is True
    assert manifest["pocket_extraction_audit_csv_read"] is True
    assert manifest["ligand_full_atom_table_row_count"] == 104
    assert manifest["pocket_atom_table_row_count"] == 741
    assert manifest["pocket_extraction_audit_row_count"] == 3
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]


def test_observed_topology_schema_is_residue_agnostic() -> None:
    manifest = _manifest()
    rows = _schema_rows()
    assert gate.OBSERVED_TOPOLOGY_SCHEMA_CONTRACT_CSV.is_file()
    assert manifest["ligand_observed_topology_schema_contract_written"] is True
    assert len(rows) == manifest["ligand_observed_topology_schema_contract_row_count"] == 24
    assert list(rows[0]) == gate.OBSERVED_TOPOLOGY_SCHEMA_COLUMNS
    fields = {row["schema_field_name"] for row in rows}
    for field in [
        "manual_confirmed_residue_comp_id",
        "manual_confirmed_residue_atom_id",
        "covalent_residue_endpoint_atom_id",
        "covalent_ligand_endpoint_atom_id",
        "reactive_residue_class",
        "restoration_policy_link",
    ]:
        assert field in fields
    assert {row["residue_agnostic_schema"] for row in rows} == {"True"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert manifest["topology_schema_residue_agnostic"] is True


def test_restoration_rule_registry_blocks_generalization() -> None:
    manifest = _manifest()
    rows = {row["rule_id"]: row for row in _rule_rows()}
    cys_rule = rows[gate.CURRENT_CYS_RULE_ID]
    unknown_rule = rows[gate.UNKNOWN_RULE_ID]
    assert gate.COVALENT_RESTORATION_RULE_REGISTRY_CONTRACT_CSV.is_file()
    assert manifest["covalent_restoration_rule_registry_contract_written"] is True
    assert manifest["covalent_restoration_rule_registry_contract_row_count"] == 7
    assert cys_rule["residue_comp_id"] == "CYS"
    assert cys_rule["residue_atom_id"] == "SG"
    assert cys_rule["warhead_family"] == "acrylamide_like_michael_acceptor"
    assert cys_rule["restoration_rule_scope"] == "current_cys_sg_golden_samples_only"
    assert cys_rule["validated_for_current_samples"] == "True"
    assert cys_rule["validated_for_new_residue_class"] == "False"
    assert cys_rule["validated_for_new_warhead_class"] == "False"
    assert cys_rule["auto_apply_to_new_residue_class_allowed"] == "False"
    assert cys_rule["auto_apply_to_new_warhead_class_allowed"] == "False"
    assert cys_rule["manual_visual_review_required_for_new_rule"] == "True"
    assert cys_rule["quarantine_if_rule_unknown"] == "True"
    assert unknown_rule["restoration_rule_scope"] == "quarantine_only"
    assert unknown_rule["v1_train_ready_scope_allowed"] == "False"
    assert unknown_rule["quarantine_if_rule_unknown"] == "True"
    deferred = [row for row in rows.values() if row["restoration_rule_scope"] == "deferred_not_v1_train_ready"]
    assert len(deferred) >= 5
    assert manifest["restoration_rules_residue_warhead_specific"] is True
    assert manifest["cys_acrylamide_rule_not_generalized_to_other_residues"] is True
    assert manifest["unknown_residue_warhead_pair_quarantined"] is True
    assert manifest["manual_visual_review_required_for_new_restoration_rule"] is True


def test_candidate_contract_current_samples_are_cys_sg_policy_only() -> None:
    manifest = _manifest()
    rows = _candidate_rows()
    assert gate.LIGAND_TOPOLOGY_RESTORATION_CANDIDATE_CONTRACT_CSV.is_file()
    assert manifest["ligand_topology_restoration_candidate_contract_written"] is True
    assert len(rows) == manifest["ligand_topology_restoration_candidate_contract_row_count"] == 3
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    expected_counts = {"HR_0002": ("33", "224"), "HR_0003": ("30", "254"), "HR_0004": ("41", "263")}
    for row in rows:
        ligand_count, pocket_count = expected_counts[row["review_row_id"]]
        assert row["manual_confirmed_residue_comp_id"] == "CYS"
        assert row["manual_confirmed_residue_atom_id"] == "SG"
        assert row["reactive_residue_class"] == "cys_sg"
        assert row["ligand_heavy_atom_count"] == ligand_count
        assert row["pocket_atom_row_count"] == pocket_count
        assert row["restoration_rule_id"] == gate.CURRENT_CYS_RULE_ID
        assert row["restoration_rule_scope"] == "current_cys_sg_golden_samples_only"
        assert row["restoration_rule_validated_for_current_sample"] == "True"
        assert row["restoration_rule_validated_for_residue_warhead_class"] == "False"
        assert row["auto_apply_to_new_residue_class_allowed"] == "False"
        assert row["auto_apply_to_new_warhead_class_allowed"] == "False"
        assert row["manual_visual_review_required_for_new_rule"] == "True"
        assert row["quarantine_if_restoration_rule_unknown"] == "True"
        assert row["v1_cys_only_train_ready_scope_candidate"] == "True"
        assert row["training_ready"] == "False"
        assert row["training_ready_reason"] == "design_gate_only_no_ligand_topology_table_written"
    assert manifest["current_samples_all_cys_sg"] is True
    assert manifest["cys_only_current_smoke_samples"] is True
    assert manifest["v1_train_ready_scope"] == gate.V1_TRAIN_READY_SCOPE
    assert manifest["all_candidate_rows_have_cys_sg_policy"] is True
    assert manifest["all_candidate_rows_block_auto_generalization"] is True
    assert manifest["all_candidate_rows_training_ready_false"] is True


def test_step8_history_and_decision_boundary() -> None:
    manifest = _manifest()
    assert manifest["step8_manual_review_history_acknowledged"] is True
    assert isinstance(manifest["step8_pre_reaction_manual_review_artifact_found"], bool)
    assert manifest["ready_for_ligand_topology_policy_review"] is True
    assert manifest["ready_for_ligand_topology_smoke"] is False
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_no_topology_restoration_sdf_dataset_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        gate.GZIP_OPEN_KEY,
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "ligand_topology_table_written",
        "pre_reaction_sdf_generated",
        "pre_reaction_sdf_modified",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False


def test_output_root_summary_and_protected_source_safety() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.SUMMARY_MD.is_file()
    forbidden = [
        path
        for path in gate.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in gate.FORBIDDEN_COMMITTABLE_SUFFIXES
    ]
    assert forbidden == []
    protected_diff = subprocess.run(
        ["git", "diff", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    protected_cached_diff = subprocess.run(
        ["git", "diff", "--cached", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert protected_diff.stdout == ""
    assert protected_cached_diff.stdout == ""
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "ligand topology plus restoration policy design gate",
        "schema is residue-agnostic",
        "CYS/SG golden smoke samples",
        "Step 8 already performed pre-reaction SDF manual review",
        f"did not run {gate.RDKIT_TEXT}",
        "pre-reaction restoration rule is residue-warhead-specific",
        "not generalized to other residues or other warheads",
        "Unknown residue-warhead pairs must be quarantined",
        "manual visual review",
        "did not write ligand_topology_table",
        "did not train",
        "Feature semantics audit is still required before formal training",
    ]:
        assert snippet in summary


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0.py"),
    ]
    forbidden_text = [
        "ur" + "llib",
        "requ" + "ests",
        "url" + "open",
        "w" + "get",
        "c" + "url",
        "gzip" + ".open",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "ge" + "mmi",
        "RD" + "Kit",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "model" + "(",
        "compute_" + "masked_loss",
        "." + "backward" + "(",
        "torch." + "optim",
        "optimizer." + "step",
        "trainer." + "fit",
        "training_" + "step" + "(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "numpy." + "load",
        "np." + "load",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "MolFromSmiles",
        "MolFromMolFile",
        "MolFromPDBFile",
        "GetMorganFingerprint",
        "GetMorganFingerprintAsBitVect",
        "url" + "open",
    }
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner in {"np", "numpy"} and func.attr == "load")
                assert not (owner == "torch" and func.attr in {"save", "optim"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in dangerous_attrs
            if isinstance(func, ast.Name):
                assert func.id not in dangerous_names
