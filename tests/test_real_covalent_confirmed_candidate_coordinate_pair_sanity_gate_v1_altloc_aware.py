from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _pair_rows() -> list[dict[str, str]]:
    with gate.PAIR_SANITY_TABLE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13e2_precondition_and_basic_execution_fields() -> None:
    assert gate.validate_step13e2_altloc_aware_rerun_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13e2_altloc_aware_coordinate_extraction_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["coordinate_pair_sanity_gate_v1_altloc_aware_defined"] is True
    assert manifest["coordinate_pair_sanity_gate_v1_altloc_aware_executed"] is True
    assert manifest["altloc_aware_coordinates_csv_read"] is True
    assert manifest["altloc_selection_audit_csv_read"] is True
    assert manifest["struct_conn_reference_csv_read"] is True
    assert manifest["coordinate_pair_sanity_table_csv_written"] is True


def test_pair_sanity_counts_and_distance_summary() -> None:
    manifest = _manifest()
    assert manifest["altloc_aware_endpoint_row_count"] == 6
    assert manifest["altloc_selection_audit_row_count"] == 3
    assert manifest["coordinate_pair_sanity_row_count"] == 3
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]
    assert manifest["all_pairs_have_two_endpoints"] is True
    assert manifest["all_pairs_have_protein_and_ligand_endpoint"] is True
    assert manifest["all_pair_distances_calculated"] is True
    assert manifest["all_pair_distances_numeric"] is True
    assert manifest["min_computed_distance_angstrom"] == 1.7554
    assert manifest["max_computed_distance_angstrom"] == 1.8054
    assert manifest["all_pair_distances_within_covalent_sanity_range"] is True
    assert manifest["all_pair_distances_match_struct_conn_reported"] is True
    assert manifest["all_coordinate_pair_sanity_passed"] is True


def test_pair_sanity_table_contract_and_rows() -> None:
    rows = _pair_rows()
    assert len(rows) == 3
    assert list(rows[0]) == gate.PAIR_SANITY_TABLE_COLUMNS
    expected_ligand_atoms = {"HR_0002": "C33", "HR_0003": "C15", "HR_0004": "C25"}
    expected_pdb_ids = {"HR_0002": "6DI9", "HR_0003": "5F2E", "HR_0004": "6OIM"}
    for row in rows:
        review_id = row["review_row_id"]
        assert row["pdb_id"] == expected_pdb_ids[review_id]
        assert row["protein_endpoint_comp_id"] == "CYS"
        assert row["protein_endpoint_atom_id"] == "SG"
        assert row["ligand_endpoint_atom_id"] == expected_ligand_atoms[review_id]
        assert row["distance_within_covalent_sanity_range"] == "True"
        assert row["distance_matches_struct_conn_reported"] == "True"
        assert row["coordinate_pair_sanity_passed"] == "True"
        assert row["coordinate_pair_sanity_reason"] == "passed_altloc_aware_covalent_range_and_struct_conn_distance_agreement"
        assert row["altloc_aware_coordinates_source"] == gate.PREVIOUS_STAGE
        assert row["altloc_aware_selection_audit_confirmed"] == "True"
        assert row["coordinates_extracted"] == "True"
        assert row["coordinate_geometry_calculation_run"] == "True"
        assert row["final_pair_sanity_distance_calculated"] == "True"
        assert row["rdkit_used"] == "False"
        assert row["sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
        assert row["training_ready"] == "False"
        assert 1.4 <= float(row["computed_endpoint_distance_angstrom"]) <= 2.2
        assert float(row["distance_abs_delta_from_struct_conn"]) <= 0.05


def test_hr0002_altloc_b_pair_is_preserved() -> None:
    manifest = _manifest()
    assert manifest["hr0002_altloc_b_preserved"] is True
    assert manifest["hr0002_selected_protein_atom_site_id"] == "659"
    assert manifest["hr0002_selected_protein_label_alt_id"] == "B"
    assert abs(manifest["hr0002_computed_distance_angstrom"] - 1.8053) <= 0.001
    assert manifest["hr0002_distance_delta_from_struct_conn"] <= 0.0004
    row = next(item for item in _pair_rows() if item["review_row_id"] == "HR_0002")
    assert row["protein_selected_atom_site_id"] == "659"
    assert row["protein_selected_label_alt_id"] == "B"
    assert row["protein_selected_occupancy"] == "0.50"
    assert row["ligand_selected_atom_site_id"] == "2070"
    assert row["hr0002_altloc_b_preserved"] == "True"
    assert abs(float(row["computed_endpoint_distance_angstrom"]) - 1.8053) <= 0.001


def test_boundary_flags_and_next_step_decision() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        "raw_files_decompressed",
        gate.GZIP_OPEN_KEY,
        "mmcif_parsed",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "raw_or_decompressed_mmcif_output_written",
        "structure_output_files_written",
        "full_mmcif_parser_used",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
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
    assert manifest["coordinates_extracted"] is True
    assert manifest["coordinate_geometry_calculation_run"] is True
    assert manifest["final_pair_sanity_distance_calculated"] is True
    assert manifest["output_limited_to_csv_json_md"] is True
    assert manifest["real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_passed"] is True
    assert manifest["coordinate_pair_sanity_v1_altloc_aware_contract_satisfied"] is True
    assert manifest["ready_for_minimal_sample_record_design_gate"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_minimal_sample_record_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.PAIR_SANITY_TABLE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    gzip_phrase = "gzip" + ".open"
    for snippet in [
        "altloc-aware coordinate pair sanity gate",
        "did not read raw `.cif.gz`",
        f"did not use {gzip_phrase}",
        "did not parse mmCIF",
        "paired 6 corrected endpoint rows into 3 protein-ligand coordinate pairs",
        "calculated 3 corrected protein SG to ligand atom distances",
        "HR_0002 preserved CYS481 SG altloc B atom_site id 659",
        "HR_0002 distance now agrees with struct_conn reported distance",
        "All 3 pairs agree",
        f"did not use {parser_tools}",
        "did not write sample_index, did not write final dataset, and did not train",
        "minimal sample record design gate",
    ]:
        assert snippet in summary


def test_pair_builder_recomputes_expected_distances_from_inputs() -> None:
    endpoint_rows = gate.load_altloc_aware_coordinate_rows_v1()
    audit_rows = gate.load_altloc_selection_audit_rows_v1()
    reported = gate.load_struct_conn_reported_distances_v1()
    rows = gate.build_coordinate_pair_sanity_rows_v1_altloc_aware(endpoint_rows, audit_rows, reported)
    by_review = {row["review_row_id"]: row for row in rows}
    assert sorted(by_review) == ["HR_0002", "HR_0003", "HR_0004"]
    assert by_review["HR_0002"]["computed_endpoint_distance_angstrom"] == "1.8053"
    assert by_review["HR_0003"]["computed_endpoint_distance_angstrom"] == "1.7554"
    assert by_review["HR_0004"]["computed_endpoint_distance_angstrom"] == "1.8054"
    assert all(row["coordinate_pair_sanity_passed"] is True for row in rows)
    assert all(row["distance_matches_struct_conn_reported"] is True for row in rows)


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware.py"),
        Path("tests/test_real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware.py"),
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
