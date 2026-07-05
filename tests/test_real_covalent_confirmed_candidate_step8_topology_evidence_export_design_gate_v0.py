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

from covalent_ext import real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/check_real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0.py",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not gate.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_check_script_passes_and_recognizes_step13o_blocked_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13o_blocked_evidence_gate_validated"] is True
    assert manifest["step13o_all_checks_passed"] is False
    assert manifest["step13o_blocked_due_to_missing_per_atom_or_per_bond_topology_evidence"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_source_discovery_contract_has_three_allowed_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.SOURCE_DISCOVERY_CONTRACT_CSV)
    assert manifest["source_discovery_contract_written"] is True
    assert len(rows) == manifest["source_discovery_contract_row_count"] == 3
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert {row["step13o_artifact_found"] for row in rows} == {"True"}
    assert {row["candidate_pre_reaction_sdf_path_discovered"] for row in rows} == {"True"}
    assert {row["candidate_pre_reaction_sdf_hash_or_manifest_path_discovered"] for row in rows} == {"True"}
    assert {row["graph_preview_artifact_discovered"] for row in rows} == {"True"}
    assert {row["packaging_qa_artifact_discovered"] for row in rows} == {"True"}
    assert {row["allowed_for_future_readonly_topology_export"] for row in rows} == {"True"}
    assert {row["discovery_status"] for row in rows} == {"source_discovery_passed"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    for row in rows:
        assert row["candidate_pre_reaction_sdf_path"].endswith("_pre_reaction.sdf")
        assert "dataset_assembly_graph_preview_candidates.csv" in row[
            "candidate_pre_reaction_sdf_hash_or_manifest_path"
        ]


def test_export_schema_and_candidate_contracts_are_written() -> None:
    manifest = _manifest()
    schema_rows = _csv_rows(gate.EXPORT_SCHEMA_CONTRACT_CSV)
    candidate_rows = _csv_rows(gate.EXPORT_CANDIDATE_CONTRACT_CSV)
    assert manifest["export_schema_contract_written"] is True
    assert len(schema_rows) == manifest["export_schema_contract_row_count"] == 44
    assert manifest["export_candidate_contract_written"] is True
    assert len(candidate_rows) == manifest["export_candidate_contract_row_count"] == 3
    assert {row["training_use_status"] for row in schema_rows} == {"not_training_input_yet"}
    future_tables = {row["future_table_name"] for row in schema_rows}
    assert future_tables == {
        "step8_exported_ligand_atom_topology_table",
        "step8_exported_ligand_bond_topology_table",
    }
    expected_counts = {
        "HR_0002": ("33", "35"),
        "HR_0003": ("30", "33"),
        "HR_0004": ("41", "45"),
    }
    for row in candidate_rows:
        atoms, bonds = expected_counts[row["review_row_id"]]
        assert row["v1_train_ready_scope"] == gate.V1_TRAIN_READY_SCOPE
        assert row["topology_export_scope"] == gate.TOPOLOGY_EXPORT_SCOPE
        assert row["topology_export_input_policy"] == gate.TOPOLOGY_EXPORT_INPUT_POLICY
        assert row["readonly_rdkit_export_allowed_next_step"] == "True"
        assert row["expected_atom_topology_row_count"] == atoms
        assert row["expected_bond_topology_row_count"] == bonds
        assert row["auto_restore_ligand_allowed"] == "False"
        assert row["sdf_generation_allowed"] == "False"
        assert row["sdf_modification_allowed"] == "False"
        assert row["sdf_copy_allowed"] == "False"
        assert row["non_cys_generalization_allowed"] == "False"
        assert row["training_ready"] == "False"


def test_manifest_allows_next_readonly_export_but_not_training() -> None:
    manifest = _manifest()
    assert manifest["all_current_samples_cys_sg"] is True
    assert manifest["v1_train_ready_scope"] == gate.V1_TRAIN_READY_SCOPE
    assert manifest["topology_export_scope"] == gate.TOPOLOGY_EXPORT_SCOPE
    assert manifest["topology_export_input_policy"] == gate.TOPOLOGY_EXPORT_INPUT_POLICY
    assert manifest["all_candidates_have_step8_artifact_paths_from_step13o"] is True
    assert manifest["all_candidates_have_pre_reaction_sdf_path"] is True
    assert manifest["all_candidates_have_manual_review_or_graph_preview_provenance"] is True
    assert manifest["all_candidates_have_hash_or_manifest_provenance"] is True
    assert manifest["all_candidates_allowed_for_future_readonly_topology_export"] is True
    assert manifest["readonly_rdkit_export_allowed_next_step"] is True
    assert manifest["ready_for_step8_readonly_topology_evidence_export_smoke"] is True
    assert manifest["ready_for_sample_index_design_gate"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.ALLOWED_NEXT_STEP


def test_no_rdkit_sdf_read_topology_table_dataset_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "rdkit_used",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "ligand_topology_table_written",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "raw_files_read",
        gate.GZIP_OPEN_KEY,
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_output_root_and_protected_source_safety() -> None:
    _manifest()
    assert gate.SOURCE_DISCOVERY_CONTRACT_CSV.is_file()
    assert gate.EXPORT_SCHEMA_CONTRACT_CSV.is_file()
    assert gate.EXPORT_CANDIDATE_CONTRACT_CSV.is_file()
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


def test_summary_states_design_gate_boundary() -> None:
    _manifest()
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "Step 8 topology evidence export design gate",
        "Step 13O correctly blocked",
        "did not read, generate, modify, or copy SDF files",
        "only designs a future read-only topology export",
        "must not automatically restore ligands again",
        "must not generalize the CYS-only V1 scope",
        "No ligand topology table, sample_index, final_dataset, or model input was written",
        "Feature semantics audit is still required before formal training",
        gate.ALLOWED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0.py"),
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
        "MolFrom" + "Smiles",
        "MolFrom" + "MolFile",
        "MolFrom" + "PDBFile",
        "GetMorgan" + "Fingerprint",
        "GetMorgan" + "FingerprintAsBitVect",
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
