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

from covalent_ext import real_covalent_confirmed_candidate_pocket_extraction_design_gate as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _schema_rows() -> list[dict[str, str]]:
    with gate.SCHEMA_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _candidate_rows() -> list[dict[str, str]]:
    with gate.CANDIDATE_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13j_precondition_and_inherited_counts() -> None:
    assert gate.validate_step13j_full_atom_extraction_smoke_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13j_full_atom_extraction_smoke_validated"] is True
    assert manifest["protein_full_atom_table_csv_read"] is True
    assert manifest["ligand_full_atom_table_csv_read"] is True
    assert manifest["endpoint_recovery_audit_csv_read"] is True
    assert manifest["protein_full_atom_table_row_count"] == 4600
    assert manifest["ligand_full_atom_table_row_count"] == 104
    assert manifest["endpoint_recovery_audit_row_count"] == 3
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]


def test_schema_contract_written_and_grouped() -> None:
    manifest = _manifest()
    rows = _schema_rows()
    assert gate.SCHEMA_CONTRACT_CSV.is_file()
    assert manifest["pocket_extraction_schema_contract_csv_written"] is True
    assert len(rows) == manifest["pocket_extraction_schema_field_count"] == 41
    assert list(rows[0]) == gate.SCHEMA_CONTRACT_COLUMNS
    groups = {row["field_group"] for row in rows}
    expected_groups = {
        "sample_provenance",
        "pocket_policy",
        "pocket_center_policy",
        "protein_atom_source",
        "ligand_atom_source",
        "covalent_endpoint_policy",
        "altloc_model_policy",
        "validation_policy",
        "output_table_contract",
        "status_boundary",
    }
    assert expected_groups <= groups
    fields = {row["field_name"] for row in rows}
    for field_name in [
        "pocket_extraction_contract_id",
        "pocket_center_policy",
        "pocket_radius_angstrom",
        "distance_calculation_policy",
        "pocket_membership_policy",
        "pocket_extraction_run",
        "pocket_atom_table_written",
        "training_ready",
    ]:
        assert field_name in fields
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}


def test_candidate_contract_rows_and_policy() -> None:
    manifest = _manifest()
    rows = _candidate_rows()
    assert gate.CANDIDATE_CONTRACT_CSV.is_file()
    assert manifest["pocket_extraction_candidate_contract_csv_written"] is True
    assert len(rows) == manifest["pocket_extraction_candidate_contract_row_count"] == 3
    assert list(rows[0]) == gate.CANDIDATE_CONTRACT_COLUMNS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    for row in rows:
        assert row["protein_atom_input_available"] == "True"
        assert row["ligand_atom_input_available"] == "True"
        assert row["endpoint_recovery_passed"] == "True"
        assert row["pocket_center_policy"] == "ligand_heavy_atom_centroid_plus_covalent_endpoint_anchor"
        assert row["pocket_radius_angstrom"] == "8.0"
        assert row["pocket_radius_unit"] == "angstrom"
        assert row["protein_atom_source_policy"] == "use_step13j_target_protein_chain_atoms_only"
        assert row["ligand_atom_source_policy"] == "use_step13j_confirmed_ligand_instance_atoms_only"
        assert row["covalent_endpoint_anchor_policy"] == "require_recovered_protein_and_ligand_endpoints"
        assert row["altloc_selection_policy"] == "inherit_step13j_altloc_filtered_atoms"
        assert row["distance_calculation_policy"] == "next_smoke_compute_min_distance_to_ligand_atoms"
        assert row["pocket_membership_policy"] == (
            "protein_atom_within_radius_of_any_ligand_atom_or_force_included_endpoint_residue"
        )
        assert row["pocket_extraction_design_status"] == "contract_only_no_distance_calculation"
        assert row["pocket_extraction_run"] == "False"
        assert row["pocket_atom_table_written"] == "False"
        assert row["training_ready"] == "False"


def test_hr0002_altloc_b_atom_site_659_inherited() -> None:
    manifest = _manifest()
    rows = {row["review_row_id"]: row for row in _candidate_rows()}
    assert manifest["hr0002_altloc_b_atom_site_659_inherited"] is True
    assert rows["HR_0002"]["protein_endpoint_atom_site_id"] == "659"
    assert rows["HR_0002"]["protein_endpoint_altloc"] == "B"


def test_no_execution_or_training_boundary() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        gate.GZIP_OPEN_KEY,
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "coordinate_geometry_calculation_run",
        "distance_matrix_calculated",
        "pocket_extraction_run",
        "pocket_atom_table_written",
        "ligand_topology_table_written",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["all_candidate_contract_rows_have_atom_inputs"] is True
    assert manifest["all_candidate_contract_rows_preserve_endpoint_recovery"] is True
    assert manifest["all_candidate_contract_rows_have_pocket_policy"] is True
    assert manifest["pocket_radius_angstrom"] == 8.0
    assert manifest["ready_for_pocket_extraction_smoke"] is True
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_pocket_extraction_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_summary_and_safety() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.SCHEMA_CONTRACT_CSV.is_file()
    assert gate.CANDIDATE_CONTRACT_CSV.is_file()
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
        "pocket extraction design gate",
        "Step 13J protein full atom table, ligand full atom table, and endpoint recovery audit",
        "did not read raw `.cif.gz`",
        "did not calculate distances",
        "did not write pocket_atom_table",
        "did not write sample_index",
        "did not train",
        "Feature semantics audit is still required before formal training",
        "pocket extraction smoke, not training",
    ]:
        assert snippet in summary


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_pocket_extraction_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0.py"),
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
