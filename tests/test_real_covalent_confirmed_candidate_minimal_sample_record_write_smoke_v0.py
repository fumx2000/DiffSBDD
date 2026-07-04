from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_confirmed_candidate_minimal_sample_record_write_smoke as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _records() -> list[dict[str, str]]:
    with gate.MINIMAL_SAMPLE_RECORDS_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _field_audit_rows() -> list[dict[str, str]]:
    with gate.FIELD_AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13g_precondition_and_execution_fields() -> None:
    assert gate.validate_step13g_minimal_sample_record_design_gate_v0() is True
    previous = json.loads(gate.STEP13G_MANIFEST_JSON.read_text(encoding="utf-8"))
    assert previous["all_checks_passed"] is True
    assert previous["ready_for_minimal_sample_record_write_smoke"] is True
    assert previous["hr0002_altloc_b_preserved"] is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13g_minimal_sample_record_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["minimal_sample_record_write_smoke_defined"] is True
    assert manifest["minimal_sample_record_write_smoke_executed"] is True
    assert manifest["schema_contract_csv_read"] is True
    assert manifest["schema_contract_field_count"] == 50
    assert manifest["candidate_contract_csv_read"] is True
    assert manifest["candidate_contract_row_count"] == 3
    assert manifest["minimal_sample_records_csv_written"] is True
    assert manifest["minimal_sample_record_row_count"] == 3
    assert manifest["field_audit_csv_written"] is True
    assert manifest["field_audit_row_count"] == 50


def test_manifest_record_contract_fields() -> None:
    manifest = _manifest()
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]
    true_keys = [
        "all_minimal_sample_records_have_stable_ids",
        "all_minimal_sample_records_have_required_identity",
        "all_minimal_sample_records_have_covalent_annotation",
        "all_minimal_sample_records_have_endpoint_coordinates",
        "all_minimal_sample_records_preserve_altloc_aware_selection",
        "all_minimal_sample_records_preserve_pair_sanity",
        "all_minimal_sample_records_mark_future_extraction_required",
        "all_minimal_sample_records_written_true",
        "all_minimal_sample_records_training_ready_false",
        "all_minimal_sample_records_sample_index_written_false",
        "all_minimal_sample_records_enriched_sample_index_written_false",
        "all_minimal_sample_records_final_dataset_written_false",
        "all_minimal_sample_records_model_input_materialized_false",
        "all_required_schema_fields_present_in_records",
        "hr0002_altloc_b_preserved",
    ]
    for key in true_keys:
        assert manifest[key] is True
    assert manifest["hr0002_selected_protein_atom_site_id"] == "659"
    assert manifest["hr0002_selected_protein_label_alt_id"] == "B"


def test_minimal_sample_records_csv() -> None:
    rows = _records()
    assert len(rows) == 3
    assert list(rows[0]) == gate.MINIMAL_SAMPLE_RECORD_COLUMNS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["minimal_sample_record_id"] for row in rows] == [
        "MSR_0001_HR_0002",
        "MSR_0002_HR_0003",
        "MSR_0003_HR_0004",
    ]
    future_flags = [
        "raw_structure_reference_required",
        "full_protein_atom_extraction_required",
        "full_ligand_atom_extraction_required",
        "pocket_definition_required",
        "ligand_bond_topology_required",
        "covalent_bond_annotation_required",
        "feature_semantics_audit_required",
        "split_leakage_check_required",
    ]
    for row in rows:
        assert row["minimal_sample_record_written"] == "True"
        assert row["coordinate_pair_sanity_passed"] == "True"
        assert row["altloc_aware_selection_confirmed"] == "True"
        assert all(row[key] == "True" for key in future_flags)
        assert row["sample_index_written"] == "False"
        assert row["enriched_sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
        assert row["model_input_materialized"] == "False"
        assert row["training_ready"] == "False"
        assert row["training_ready_reason"] == "minimal_sample_record_written_but_full_atom_model_input_not_materialized"
    hr2 = rows[0]
    assert hr2["protein_selected_atom_site_id"] == "659"
    assert hr2["protein_selected_label_alt_id"] == "B"
    assert abs(float(hr2["computed_endpoint_distance_angstrom"]) - 1.8053) <= 0.001


def test_field_audit_csv() -> None:
    rows = _field_audit_rows()
    assert len(rows) == 50
    assert list(rows[0]) == gate.FIELD_AUDIT_COLUMNS
    by_field = {row["field_name"]: row for row in rows}
    for field_name in gate.REQUIRED_SCHEMA_FIELDS:
        assert by_field[field_name]["present_in_minimal_sample_records"] == "True"
    assert by_field["minimal_sample_record_id"]["present_in_minimal_sample_records"] == "True"
    assert by_field["training_ready"]["present_in_minimal_sample_records"] == "True"
    assert by_field["training_ready_reason"]["present_in_minimal_sample_records"] == "True"
    for row in rows:
        assert row["training_use_status"] == "not_training_input_yet"
    for field_name in [
        "full_protein_atom_extraction_required",
        "full_ligand_atom_extraction_required",
        "pocket_definition_required",
        "ligand_bond_topology_required",
    ]:
        assert by_field[field_name]["present_in_minimal_sample_records"] == "True"
        assert by_field[field_name]["non_empty_for_all_records"] == "True"


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
        "actual_split_assignments_written",
        "actual_leakage_matrix_written",
        "final_split_created",
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
        "training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["output_limited_to_csv_json_md"] is True
    assert manifest["real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_passed"] is True
    assert manifest["minimal_sample_record_write_smoke_contract_satisfied"] is True
    assert manifest["ready_for_full_atom_extraction_design_gate"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_full_atom_extraction_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.MINIMAL_SAMPLE_RECORDS_CSV.is_file()
    assert gate.FIELD_AUDIT_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "minimal sample record write smoke",
        "Step 13G schema contract and candidate contract",
        "wrote 3 minimal sample records",
        "field audit",
        "HR_0002 altloc B atom_site 659",
        "did not read raw `.cif.gz`",
        f"did not use {gate.GZIP_TEXT}",
        "did not parse mmCIF",
        "did not recompute geometry distance",
        "did not run full protein atom extraction, full ligand atom extraction, pocket definition, or ligand topology",
        f"did not use {parser_tools}",
        "did not write sample_index, did not write enriched sample_index, did not write final dataset",
        "did not materialize model input, and did not train",
        "full atom extraction design gate, not direct training",
    ]:
        assert snippet in summary


def test_builder_functions_return_expected_records() -> None:
    schema_rows = gate.load_step13g_schema_contract_rows_v0()
    candidate_rows = gate.load_step13g_candidate_contract_rows_v0()
    records = gate.build_minimal_sample_records_v0(candidate_rows)
    audit = gate.build_minimal_sample_record_field_audit_v0(schema_rows, records)
    assert len(schema_rows) == 50
    assert len(candidate_rows) == 3
    assert len(records) == 3
    assert len(audit) == 50
    assert records[0]["minimal_sample_record_id"] == "MSR_0001_HR_0002"
    assert records[0]["protein_selected_atom_site_id"] == "659"
    assert records[0]["protein_selected_label_alt_id"] == "B"
    assert records[0]["training_ready"] is False


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0.py"),
    ]
    forbidden_text = [
        "ur" + "llib",
        "re" + "quests",
        "url" + "open",
        "w" + "get",
        "cu" + "rl",
        "gzip" + ".open",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "ge" + "mmi",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "mo" + "del(",
        "compute_" + "masked_loss",
        "." + "backward(",
        "torch." + "optim",
        "optimizer." + "step",
        "trainer." + "fit",
        "training_" + "step(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_" + "from_checkpoint",
        "numpy." + "load",
        "np." + "load",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_" + "from_checkpoint",
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
