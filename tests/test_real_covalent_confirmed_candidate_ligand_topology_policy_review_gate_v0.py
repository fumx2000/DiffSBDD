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

from covalent_ext import real_covalent_confirmed_candidate_ligand_topology_policy_review_gate as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _decision_rows() -> list[dict[str, str]]:
    with gate.DECISION_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13m_precondition_and_contract_reads() -> None:
    assert gate.validate_step13m_ligand_topology_restoration_policy_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13m_ligand_topology_restoration_policy_design_gate_validated"] is True
    assert manifest["observed_topology_schema_contract_csv_read"] is True
    assert manifest["observed_topology_schema_contract_row_count"] == 24
    assert manifest["restoration_rule_registry_contract_csv_read"] is True
    assert manifest["restoration_rule_registry_contract_row_count"] == 7
    assert manifest["candidate_contract_csv_read"] is True
    assert manifest["candidate_contract_row_count"] == 3
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]


def test_policy_review_decision_contract_all_accepted() -> None:
    manifest = _manifest()
    rows = _decision_rows()
    assert gate.DECISION_CONTRACT_CSV.is_file()
    assert manifest["policy_review_decision_contract_written"] is True
    assert len(rows) == manifest["policy_review_decision_contract_row_count"] == 8
    assert list(rows[0]) == gate.DECISION_CONTRACT_COLUMNS
    assert {row["decision"] for row in rows} == {"accepted"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    topics = {row["review_topic"] for row in rows}
    assert topics == {
        "residue_agnostic_schema_review",
        "cys_only_v1_scope_review",
        "restoration_rule_specificity_review",
        "cys_acrylamide_non_generalization_review",
        "unknown_rule_quarantine_review",
        "step8_manual_review_provenance_review",
        "topology_smoke_scope_review",
        "training_boundary_review",
    }
    assert manifest["all_policy_review_decisions_accepted"] is True
    assert manifest["topology_schema_residue_agnostic_review_accepted"] is True
    assert manifest["cys_only_v1_scope_review_accepted"] is True
    assert manifest["restoration_rule_specificity_review_accepted"] is True
    assert manifest["cys_acrylamide_non_generalization_review_accepted"] is True
    assert manifest["unknown_rule_quarantine_review_accepted"] is True
    assert manifest["step8_manual_review_provenance_review_accepted"] is True
    assert manifest["topology_smoke_scope_review_accepted"] is True
    assert manifest["training_boundary_review_accepted"] is True


def test_topology_smoke_scope_and_training_boundary() -> None:
    manifest = _manifest()
    assert manifest["current_samples_all_cys_sg"] is True
    assert manifest["v1_train_ready_scope"] == gate.V1_TRAIN_READY_SCOPE
    assert manifest["topology_smoke_scope"] == gate.TOPOLOGY_SMOKE_SCOPE
    assert manifest["topology_smoke_input_source_policy"] == gate.TOPOLOGY_SMOKE_INPUT_SOURCE_POLICY
    assert manifest["topology_smoke_must_not_auto_restore_ligand"] is True
    assert manifest["topology_smoke_must_not_generalize_to_non_cys"] is True
    assert manifest["topology_smoke_must_not_claim_training_ready"] is True
    assert manifest["ready_for_ligand_topology_smoke"] is True
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_no_topology_sdf_dataset_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        gate.GZIP_OPEN_KEY,
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "sdf_generated",
        "sdf_modified",
        "ligand_topology_table_written",
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
        "ligand topology policy review gate",
        "accepted the Step 13M CYS-only V1 scope",
        "schema remains residue-agnostic",
        "restoration rule remains residue-warhead-specific",
        "limited to the 3 CYS/SG golden samples",
        "must not automatically restore ligands again",
        "must not generalize to non-CYS",
        "Step 8 manual-reviewed pre-reaction provenance or existing graph preview only",
        "did not generate SDF",
        "did not write ligand_topology_table",
        "did not write sample_index",
        "did not train",
        "Feature semantics audit is still required before formal training",
    ]:
        assert snippet in summary


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0.py"),
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
