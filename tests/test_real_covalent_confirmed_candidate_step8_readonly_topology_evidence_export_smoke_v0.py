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

from covalent_ext import real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/check_real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0.py",
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
    if not smoke.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def test_check_script_passes_and_validates_step13p_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13p_topology_evidence_export_design_gate_validated"] is True
    assert manifest["export_candidate_contract_csv_read"] is True
    assert manifest["export_candidate_contract_row_count"] == 3
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_only_contract_listed_sdf_paths_are_read_and_hash_checked() -> None:
    contract_rows = _csv_rows(smoke.STEP13P_EXPORT_CANDIDATE_CONTRACT_CSV)
    contract_paths = {row["source_pre_reaction_sdf_path"] for row in contract_rows}
    assert len(contract_paths) == 3
    audit_rows = _csv_rows(smoke.EXPORT_AUDIT_CSV)
    atom_rows = _csv_rows(smoke.ATOM_TOPOLOGY_TABLE_CSV)
    bond_rows = _csv_rows(smoke.BOND_TOPOLOGY_TABLE_CSV)
    audit_paths = {row["source_pre_reaction_sdf_path"] for row in audit_rows}
    atom_paths = {row["source_pre_reaction_sdf_path"] for row in atom_rows}
    bond_paths = {row["source_pre_reaction_sdf_path"] for row in bond_rows}
    assert audit_paths == contract_paths
    assert atom_paths == contract_paths
    assert bond_paths == contract_paths
    assert all(Path(path).suffix == ".sdf" for path in contract_paths)
    assert {row["hash_verification_status"] for row in audit_rows} == {"sha256_match"}
    assert {row["source_pre_reaction_sdf_exists"] for row in audit_rows} == {"True"}


def test_readonly_rdkit_export_counts_match_expected() -> None:
    manifest = _manifest()
    audit_rows = _csv_rows(smoke.EXPORT_AUDIT_CSV)
    assert manifest["rdkit_used"] is True
    assert manifest["rdkit_readonly_sdf_parse_used"] is True
    assert manifest["sdf_read"] is True
    assert manifest["all_rdkit_molecules_loaded"] is True
    assert manifest["all_atom_counts_match_expected"] is True
    assert manifest["all_bond_counts_match_expected"] is True
    assert manifest["all_readonly_exports_passed"] is True
    expected = {
        "HR_0002": ("33", "35"),
        "HR_0003": ("30", "33"),
        "HR_0004": ("41", "45"),
    }
    for row in audit_rows:
        atom_count, bond_count = expected[row["review_row_id"]]
        assert row["rdkit_atom_count"] == atom_count
        assert row["rdkit_bond_count"] == bond_count
        assert row["exported_atom_rows"] == atom_count
        assert row["exported_bond_rows"] == bond_count
        assert row["readonly_export_passed"] == "True"
        assert row["blocking_reasons"] == ""


def test_exported_atom_and_bond_tables_have_expected_rows_and_status() -> None:
    manifest = _manifest()
    atom_rows = _csv_rows(smoke.ATOM_TOPOLOGY_TABLE_CSV)
    bond_rows = _csv_rows(smoke.BOND_TOPOLOGY_TABLE_CSV)
    assert manifest["atom_topology_table_written"] is True
    assert manifest["atom_topology_table_row_count"] == 104
    assert manifest["bond_topology_table_written"] is True
    assert manifest["bond_topology_table_row_count"] == 113
    assert len(atom_rows) == 104
    assert len(bond_rows) == 113
    assert {row["training_use_status"] for row in atom_rows} == {"not_training_input_yet"}
    assert {row["training_use_status"] for row in bond_rows} == {"not_training_input_yet"}
    assert {row["export_source_stage"] for row in atom_rows} == {smoke.EXPORT_SOURCE_STAGE}
    assert {row["export_source_stage"] for row in bond_rows} == {smoke.EXPORT_SOURCE_STAGE}
    atom_counts = {rid: sum(row["review_row_id"] == rid for row in atom_rows) for rid in smoke.EXPECTED_REVIEW_ROW_IDS}
    bond_counts = {rid: sum(row["review_row_id"] == rid for row in bond_rows) for rid in smoke.EXPECTED_REVIEW_ROW_IDS}
    assert atom_counts == {"HR_0002": 33, "HR_0003": 30, "HR_0004": 41}
    assert bond_counts == {"HR_0002": 35, "HR_0003": 33, "HR_0004": 45}


def test_no_sdf_write_auto_restore_topology_table_sample_index_model_input_or_training() -> None:
    manifest = _manifest()
    true_keys = ["rdkit_used", "rdkit_readonly_sdf_parse_used", "sdf_read"]
    for key in true_keys:
        assert manifest[key] is True
    false_keys = [
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "non_cys_generalization_run",
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
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "raw_files_read",
        "gzip_open_used",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        "ge" + "mmi_used",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_next_step_is_ligand_topology_retry_not_sample_index_or_training() -> None:
    manifest = _manifest()
    assert manifest["ready_for_ligand_topology_smoke_retry"] is True
    assert manifest["ready_for_sample_index_design_gate"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == smoke.PASSED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        smoke.ATOM_TOPOLOGY_TABLE_CSV,
        smoke.BOND_TOPOLOGY_TABLE_CSV,
        smoke.EXPORT_AUDIT_CSV,
        smoke.REPORT_CSV,
        smoke.MANIFEST_JSON,
        smoke.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in smoke.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in smoke.FORBIDDEN_COMMITTABLE_SUFFIXES
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
    raw_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_tracked = subprocess.run(
        ["git", "ls-files", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert protected_diff.stdout == ""
    assert protected_cached_diff.stdout == ""
    assert raw_staged.stdout == ""
    assert raw_tracked.stdout == ""


def test_summary_states_readonly_evidence_boundary() -> None:
    _manifest()
    summary = smoke.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "read-only RDKit topology evidence export smoke",
        "only reads the three Step 8 manual-reviewed pre-reaction SDF files",
        "does not generate, modify, or copy SDF files",
        "does not automatically restore ligands",
        "does not generalize the current CYS/SG golden sample scope",
        "not final ligand topology or training tables",
        "ready_for_sample_index_design_gate: `False`",
        "Feature semantics audit is still required before formal training",
        smoke.PASSED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0.py"),
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
        "Chem." + "MolFrom",
        "Chem." + "SDWriter",
        "MolTo" + "MolFile",
        "Sanitize" + "Mol",
        "All" + "Chem",
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
        "MolTo" + "MolFile",
        "SD" + "Writer",
        "Sanitize" + "Mol",
        "GetMorgan" + "Fingerprint",
        "GetMorgan" + "FingerprintAsBitVect",
        "url" + "open",
    }
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text, f"{pattern} found in {path}"
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
