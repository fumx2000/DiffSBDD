from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_confirmed_candidate_full_atom_extraction_design_gate as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _schema_rows() -> list[dict[str, str]]:
    with gate.SCHEMA_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _candidate_rows() -> list[dict[str, str]]:
    with gate.CANDIDATE_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13h_precondition_and_input_reads() -> None:
    assert gate.validate_step13h_minimal_sample_record_write_smoke_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13h_minimal_sample_record_write_smoke_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["full_atom_extraction_design_gate_defined"] is True
    assert manifest["full_atom_extraction_design_gate_executed"] is True
    assert manifest["minimal_sample_records_csv_read"] is True
    assert manifest["minimal_sample_record_row_count"] == 3
    assert manifest["field_audit_csv_read"] is True
    assert manifest["field_audit_row_count"] == 50
    assert manifest["pair_sanity_table_csv_read"] is True
    assert manifest["pair_sanity_row_count"] == 3
    assert manifest["altloc_aware_endpoint_coordinates_csv_read"] is True
    assert manifest["altloc_aware_endpoint_row_count"] == 6
    assert manifest["altloc_selection_audit_csv_read"] is True
    assert manifest["altloc_selection_audit_row_count"] == 3


def test_schema_contract_csv() -> None:
    manifest = _manifest()
    rows = _schema_rows()
    assert manifest["full_atom_extraction_schema_contract_csv_written"] is True
    assert len(rows) == manifest["full_atom_extraction_schema_field_count"]
    assert len(rows) >= 60
    assert list(rows[0]) == gate.SCHEMA_CONTRACT_COLUMNS
    field_names = {row["field_name"] for row in rows}
    protein_table_fields = {row["field_name"] for row in rows if row["output_table"] == "protein_full_atom_table"}
    ligand_table_fields = {row["field_name"] for row in rows if row["output_table"] == "ligand_full_atom_table"}
    for field_name in [
        "protein_full_atom_extraction_scope",
        "ligand_full_atom_extraction_scope",
        "altloc_selection_policy",
        "full_atom_extraction_run",
        "protein_full_atom_table_written",
        "ligand_full_atom_table_written",
        "training_ready",
    ]:
        assert field_name in field_names
    for field_name in ["atom_site_id", "label_alt_id", "Cartn_x", "Cartn_y", "Cartn_z"]:
        assert field_name in protein_table_fields
        assert field_name in ligand_table_fields
    for row in rows:
        assert row["required_for_full_atom_extraction_smoke"] == "True"
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}


def test_candidate_contract_csv() -> None:
    manifest = _manifest()
    rows = _candidate_rows()
    assert manifest["full_atom_extraction_candidate_contract_csv_written"] is True
    assert len(rows) == 3
    assert list(rows[0]) == gate.CANDIDATE_CONTRACT_COLUMNS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    for row in rows:
        assert row["raw_path"].startswith("data/raw/covalent_sources/")
        assert row["raw_structure_reference_available"] == "True"
        assert row["raw_structure_read_allowed_in_next_smoke"] == "True"
        assert row["raw_structure_read_in_this_design_gate"] == "False"
        assert row["protein_full_atom_table_planned"] == "True"
        assert row["ligand_full_atom_table_planned"] == "True"
        assert row["pocket_atom_table_planned"] == "False"
        assert row["ligand_topology_table_planned"] == "False"
        assert row["full_atom_extraction_run"] == "False"
        assert row["protein_full_atom_table_written"] == "False"
        assert row["ligand_full_atom_table_written"] == "False"
        assert row["sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
        assert row["model_input_materialized"] == "False"
        assert row["training_ready"] == "False"
        assert row["training_ready_reason"] == "full_atom_extraction_design_only_no_atom_tables_written"
    hr2 = rows[0]
    assert hr2["protein_selected_atom_site_id"] == "659"
    assert hr2["protein_selected_label_alt_id"] == "B"
    assert hr2["expected_protein_endpoint_atom_site_id"] == "659"
    assert hr2["expected_protein_endpoint_altloc"] == "B"
    assert abs(float(hr2["computed_endpoint_distance_angstrom"]) - 1.8053) <= 0.001


def test_manifest_contract_and_altloc_fields() -> None:
    manifest = _manifest()
    true_keys = [
        "all_minimal_sample_record_inputs_valid",
        "all_candidate_contract_rows_have_raw_references",
        "all_candidate_contract_rows_have_protein_extraction_policy",
        "all_candidate_contract_rows_have_ligand_extraction_policy",
        "all_candidate_contract_rows_preserve_altloc_aware_selection",
        "all_candidate_contract_rows_preserve_pair_sanity",
        "all_candidate_contract_rows_plan_protein_and_ligand_full_atom_tables",
        "all_candidate_contract_rows_do_not_plan_pocket_or_topology_yet",
        "all_candidate_contract_rows_full_atom_extraction_run_false",
        "all_candidate_contract_rows_atom_tables_written_false",
        "all_candidate_contract_rows_sample_index_written_false",
        "all_candidate_contract_rows_final_dataset_written_false",
        "all_candidate_contract_rows_model_input_materialized_false",
        "all_candidate_contract_rows_training_ready_false",
        "hr0002_altloc_b_preserved",
        "hr0002_raw_path_present",
    ]
    for key in true_keys:
        assert manifest[key] is True
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]
    assert manifest["hr0002_selected_protein_atom_site_id"] == "659"
    assert manifest["hr0002_selected_protein_label_alt_id"] == "B"


def test_boundary_and_decision_fields() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        "raw_files_decompressed",
        gate.GZIP_OPEN_KEY,
        "mmcif_parsed",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "coordinate_geometry_calculation_run",
        "final_pair_sanity_distance_calculated",
        "full_protein_atom_extraction_run",
        "full_ligand_atom_extraction_run",
        "pocket_definition_run",
        "ligand_bond_topology_extraction_run",
        "protein_full_atom_table_written",
        "ligand_full_atom_table_written",
        "pocket_atom_table_written",
        "ligand_topology_table_written",
        "raw_or_decompressed_mmcif_output_written",
        "structure_output_files_written",
        "full_mmcif_parser_used",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "model_input_materialized",
        "training_ready_samples_claimed",
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "adapter_execution_run",
        "real_adapter_execution_run",
        "uniprot_mapping_run",
        "cdhit_run",
        "npz_files_loaded",
        "npz_contents_read",
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
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["output_limited_to_csv_json_md"] is True
    assert manifest["real_covalent_confirmed_candidate_full_atom_extraction_design_gate_passed"] is True
    assert manifest["full_atom_extraction_design_contract_satisfied"] is True
    assert manifest["ready_for_full_atom_extraction_smoke"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_full_atom_extraction_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.SCHEMA_CONTRACT_CSV.is_file()
    assert gate.CANDIDATE_CONTRACT_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "full atom extraction design gate",
        "Step 13H minimal sample records and field audit",
        "Step 13F-v1 coordinate pair sanity table",
        "Step 13E2 altloc-aware endpoint coordinates",
        "did not read raw `.cif.gz`",
        f"did not use {gate.GZIP_TEXT}",
        "did not parse mmCIF",
        "did not run actual full protein atom extraction or full ligand atom extraction",
        "did not write protein full atom tables, ligand full atom tables, pocket atom tables, or ligand topology tables",
        f"did not use {parser_tools}",
        "did not write sample_index, did not write enriched sample_index, did not write final dataset",
        "did not materialize model input, and did not train",
        "HR_0002 altloc B atom_site 659",
        "full atom extraction smoke, not direct training",
    ]:
        assert snippet in summary


def test_builder_functions_return_expected_records() -> None:
    minimal_records = gate.load_step13h_minimal_sample_records_v0()
    field_audit = gate.load_step13h_field_audit_rows_v0()
    pair_rows = gate.load_step13f_pair_sanity_rows_v1()
    endpoint_rows = gate.load_step13e2_altloc_aware_endpoint_rows_v0()
    audit_rows = gate.load_step13e2_altloc_selection_audit_rows_v0()
    schema_rows = gate.build_full_atom_extraction_schema_contract_v0()
    candidate_rows = gate.build_full_atom_extraction_candidate_contract_v0(
        minimal_records, pair_rows, endpoint_rows, audit_rows
    )
    assert len(minimal_records) == 3
    assert len(field_audit) == 50
    assert len(pair_rows) == 3
    assert len(endpoint_rows) == 6
    assert len(audit_rows) == 3
    assert len(schema_rows) >= 60
    assert len(candidate_rows) == 3
    assert candidate_rows[0]["review_row_id"] == "HR_0002"
    assert candidate_rows[0]["protein_selected_atom_site_id"] == "659"
    assert candidate_rows[0]["protein_selected_label_alt_id"] == "B"


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_full_atom_extraction_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0.py"),
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
