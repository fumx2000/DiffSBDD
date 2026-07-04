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

from covalent_ext import real_covalent_confirmed_candidate_pocket_extraction_smoke as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _pocket_rows() -> list[dict[str, str]]:
    with gate.POCKET_ATOM_TABLE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _audit_rows() -> list[dict[str, str]]:
    with gate.POCKET_EXTRACTION_AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13k_precondition_and_inputs() -> None:
    assert gate.validate_step13k_pocket_extraction_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13k_pocket_extraction_design_gate_validated"] is True
    assert manifest["pocket_extraction_candidate_contract_csv_read"] is True
    assert manifest["pocket_extraction_candidate_contract_row_count"] == 3
    assert manifest["protein_full_atom_table_csv_read"] is True
    assert manifest["ligand_full_atom_table_csv_read"] is True
    assert manifest["protein_full_atom_table_row_count"] == 4600
    assert manifest["ligand_full_atom_table_row_count"] == 104
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]


def test_pocket_atom_table_written_and_nonempty() -> None:
    manifest = _manifest()
    rows = _pocket_rows()
    assert gate.POCKET_ATOM_TABLE_CSV.is_file()
    assert manifest["pocket_atom_table_written"] is True
    assert len(rows) == manifest["pocket_atom_table_row_count"] == 741
    assert list(rows[0]) == gate.POCKET_ATOM_COLUMNS
    assert {row["review_row_id"] for row in rows} == {"HR_0002", "HR_0003", "HR_0004"}
    assert {row["group_PDB"] for row in rows} == {"ATOM"}
    assert all(float(row["min_distance_to_ligand_heavy_atom_angstrom"]) >= 0.0 for row in rows)
    assert all(row["extraction_source_stage"] == gate.STAGE for row in rows)


def test_pocket_extraction_audit_all_candidates_pass() -> None:
    manifest = _manifest()
    audit_rows = _audit_rows()
    assert gate.POCKET_EXTRACTION_AUDIT_CSV.is_file()
    assert manifest["pocket_extraction_audit_written"] is True
    assert len(audit_rows) == manifest["pocket_extraction_audit_row_count"] == 3
    assert list(audit_rows[0]) == gate.POCKET_AUDIT_COLUMNS
    assert [row["review_row_id"] for row in audit_rows] == ["HR_0002", "HR_0003", "HR_0004"]
    expected_pocket_counts = {"HR_0002": "224", "HR_0003": "254", "HR_0004": "263"}
    expected_ligand_heavy_counts = {"HR_0002": "33", "HR_0003": "30", "HR_0004": "41"}
    for row in audit_rows:
        assert row["pocket_atom_row_count"] == expected_pocket_counts[row["review_row_id"]]
        assert row["ligand_heavy_atom_count"] == expected_ligand_heavy_counts[row["review_row_id"]]
        assert int(row["pocket_atom_row_count"]) > 0
        assert int(row["ligand_heavy_atom_count"]) > 0
        assert row["covalent_endpoint_in_pocket"] == "True"
        assert row["covalent_residue_atoms_in_pocket"] == "True"
        assert row["pocket_extraction_passed"] == "True"
        assert row["blocking_reasons"] == ""


def test_distance_fields_parse_and_are_reasonable() -> None:
    audit_rows = _audit_rows()
    for row in audit_rows:
        min_distance = float(row["min_pocket_distance_angstrom"])
        max_distance = float(row["max_pocket_distance_angstrom"])
        assert 0.0 <= min_distance <= gate.POCKET_RADIUS_ANGSTROM
        assert max_distance >= min_distance
        assert max_distance < 25.0
        assert float(row["pocket_radius_angstrom"]) == 8.0


def test_hr0002_altloc_b_atom_site_659_in_pocket() -> None:
    manifest = _manifest()
    rows = _pocket_rows()
    hr2_endpoint_rows = [
        row
        for row in rows
        if row["review_row_id"] == "HR_0002"
        and row["atom_site_id"] == "659"
        and row["label_alt_id"] == "B"
        and row["is_covalent_endpoint_atom"] == "True"
    ]
    assert manifest["hr0002_altloc_b_atom_site_659_in_pocket"] is True
    assert len(hr2_endpoint_rows) == 1
    assert hr2_endpoint_rows[0]["force_included_by_covalent_endpoint"] == "True"


def test_no_raw_parser_topology_dataset_model_input_or_training() -> None:
    manifest = _manifest()
    assert manifest["coordinate_geometry_calculation_run"] is True
    assert manifest["distance_matrix_calculated"] is True
    assert manifest["pocket_extraction_run"] is True
    false_keys = [
        "raw_files_read",
        gate.GZIP_OPEN_KEY,
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
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
    assert manifest["ready_for_ligand_topology_design_gate"] is True
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_ligand_topology_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


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
        "pocket extraction smoke",
        "Step 13K pocket contract and the Step 13J full atom tables",
        "calculated protein atom distances to ligand heavy atoms",
        "wrote pocket_atom_table",
        "did not read raw `.cif.gz`",
        "did not parse mmCIF",
        "did not write ligand_topology_table",
        "did not write sample_index",
        "did not train",
        "Feature semantics audit is still required before formal training",
        "ligand topology design gate, not training",
    ]:
        assert snippet in summary


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_pocket_extraction_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_pocket_extraction_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_pocket_extraction_smoke_v0.py"),
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
