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

from covalent_ext import real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/check_real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0.py",
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


def test_check_script_blocks_when_step8_per_bond_evidence_is_missing() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0
    assert "blocked_as_expected" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13n_ligand_topology_policy_review_gate_validated"] is True
    assert manifest["all_checks_passed"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert "step8_per_atom_or_per_bond_topology_evidence_missing" in manifest["blocking_reasons"]


def test_topology_scope_and_input_boundaries_are_preserved() -> None:
    manifest = _manifest()
    assert manifest["topology_smoke_scope"] == gate.TOPOLOGY_SMOKE_SCOPE
    assert manifest["topology_smoke_input_source_policy"] == gate.TOPOLOGY_SMOKE_INPUT_SOURCE_POLICY
    assert manifest["topology_smoke_must_not_auto_restore_ligand"] is True
    assert manifest["topology_smoke_must_not_generalize_to_non_cys"] is True
    assert manifest["topology_smoke_must_not_claim_training_ready"] is True
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]
    assert manifest["ligand_full_atom_table_csv_read"] is True
    assert manifest["ligand_full_atom_table_row_count"] == 104
    assert manifest["ligand_topology_restoration_candidate_contract_row_count"] == 3


def test_artifact_discovery_audit_records_counts_but_missing_detail() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.ARTIFACT_DISCOVERY_AUDIT_CSV)
    assert manifest["artifact_discovery_audit_written"] is True
    assert len(rows) == manifest["artifact_discovery_audit_row_count"] == 3
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert {row["step8_artifact_found"] for row in rows} == {"True"}
    assert {row["artifact_contains_atom_count"] for row in rows} == {"True"}
    assert {row["artifact_contains_bond_count"] for row in rows} == {"True"}
    assert {row["artifact_contains_per_atom_topology"] for row in rows} == {"False"}
    assert {row["artifact_contains_per_bond_topology"] for row in rows} == {"False"}
    assert {row["artifact_sufficient_for_topology_smoke"] for row in rows} == {"False"}
    for row in rows:
        assert "missing_step8_per_atom_topology_evidence" in row["blocking_reasons"]
        assert "missing_step8_per_bond_topology_evidence" in row["blocking_reasons"]
    assert manifest["all_step8_topology_artifacts_found"] is True
    assert manifest["all_artifacts_contain_per_atom_topology"] is False
    assert manifest["all_artifacts_contain_per_bond_topology"] is False
    assert manifest["all_artifacts_sufficient_for_topology_smoke"] is False


def test_blocked_tables_are_header_only_and_audit_is_complete() -> None:
    manifest = _manifest()
    atom_rows = _csv_rows(gate.ATOM_TOPOLOGY_TABLE_CSV)
    bond_rows = _csv_rows(gate.BOND_TOPOLOGY_TABLE_CSV)
    audit_rows = _csv_rows(gate.TOPOLOGY_SMOKE_AUDIT_CSV)
    assert atom_rows == []
    assert bond_rows == []
    assert manifest["ligand_observed_atom_topology_table_written"] is False
    assert manifest["ligand_observed_atom_topology_table_row_count"] == 0
    assert manifest["ligand_observed_bond_topology_table_written"] is False
    assert manifest["ligand_observed_bond_topology_table_row_count"] == 0
    assert len(audit_rows) == manifest["ligand_topology_smoke_audit_row_count"] == 3
    expected_atoms = {"HR_0002": "33", "HR_0003": "30", "HR_0004": "41"}
    expected_bonds = {"HR_0002": "35", "HR_0003": "33", "HR_0004": "45"}
    for row in audit_rows:
        rid = row["review_row_id"]
        assert row["ligand_atom_input_row_count"] == expected_atoms[rid]
        assert row["expected_atom_topology_row_count"] == expected_atoms[rid]
        assert row["observed_atom_topology_row_count"] == "0"
        assert row["expected_bond_topology_row_count"] == expected_bonds[rid]
        assert row["observed_bond_topology_row_count"] == "0"
        assert row["covalent_ligand_endpoint_present"] == "True"
        assert row["topology_smoke_passed"] == "False"
    assert manifest["all_ligand_topology_smoke_passed"] is False
    assert manifest["ready_for_sample_index_design_gate"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_no_structure_sdf_dataset_model_input_or_training_outputs() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        gate.GZIP_OPEN_KEY,
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "sdf_read_for_topology",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "non_cys_generalization_run",
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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_output_root_and_protected_source_safety() -> None:
    _manifest()
    assert gate.ARTIFACT_DISCOVERY_AUDIT_CSV.is_file()
    assert gate.ATOM_TOPOLOGY_TABLE_CSV.is_file()
    assert gate.BOND_TOPOLOGY_TABLE_CSV.is_file()
    assert gate.TOPOLOGY_SMOKE_AUDIT_CSV.is_file()
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


def test_summary_states_blocked_topology_evidence_boundary() -> None:
    _manifest()
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "current CYS/SG golden samples only",
        "Step 8 manual-reviewed pre-reaction provenance or existing graph preview",
        "did not automatically restore ligands",
        "did not read, generate, modify, or copy SDF files",
        "did not generalize to non-CYS",
        "did not write sample_index",
        "did not train",
        "blocked because existing Step 8 evidence lacks per-atom and per-bond topology evidence",
        "locate or export Step 8 per-bond topology evidence",
        "Feature semantics audit is still required before formal training",
    ]:
        assert snippet in summary


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0.py"),
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
