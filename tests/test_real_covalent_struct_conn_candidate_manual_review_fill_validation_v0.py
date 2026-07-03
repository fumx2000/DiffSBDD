from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_struct_conn_candidate_manual_review_fill_validation as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13b_precondition_and_blank_table_restored() -> None:
    assert gate.validate_step13b_human_review_table_v0() is True
    blank_rows = _csv_rows(gate.STEP13B_BLANK_HUMAN_REVIEW_TABLE_CSV)
    assert len(blank_rows) == 16
    assert all(row[column] == "" for row in blank_rows for column in gate.MANUAL_REVIEW_COLUMNS)
    assert all(row["review_priority"] == "high" and row["candidate_like"] == "True" for row in blank_rows[:4])
    assert all(row["review_priority"] == "audit" and row["candidate_like"] == "False" for row in blank_rows[4:])
    manifest = _manifest()
    assert manifest["step13b_human_review_table_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["step13b_blank_table_modified"] is False


def test_manual_fill_validation_counts_and_ids() -> None:
    manifest = _manifest()
    assert manifest["manual_filled_table_csv_read"] is True
    assert manifest["manual_filled_table_row_count"] == 16
    assert manifest["manual_review_fill_validation_executed"] is True
    assert manifest["confirmed_review_row_count"] == 3
    assert manifest["excluded_review_row_count"] == 1
    assert manifest["blank_audit_review_row_count"] == 12
    assert manifest["confirmed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]
    assert manifest["excluded_review_row_ids"] == ["HR_0001"]
    assert manifest["duplicate_exclusion_validated"] is True
    assert manifest["all_confirmed_rows_have_required_manual_fields"] is True
    assert manifest["all_audit_rows_except_duplicate_blank"] is True
    assert manifest["all_manual_review_dates_valid"] is True
    assert manifest["all_manual_reviewers_valid"] is True
    assert manifest["all_human_review_required_true"] is True
    assert manifest["all_training_ready_false"] is True
    assert manifest["all_inference_flags_false"] is True


def test_confirmed_candidate_table_contract() -> None:
    manifest = _manifest()
    assert manifest["confirmed_candidate_table_csv_written"] is True
    assert manifest["confirmed_candidate_table_row_count"] == 3
    assert manifest["all_confirmed_candidate_ids_unique"] is True
    assert manifest["all_confirmed_candidates_coordinate_extraction_ready"] is True
    assert manifest["all_confirmed_candidates_training_ready_false"] is True
    assert manifest["all_confirmed_candidates_sample_index_written_false"] is True
    assert manifest["all_confirmed_candidates_coordinates_not_extracted"] is True
    assert manifest["all_confirmed_candidates_distance_not_calculated"] is True
    assert manifest["all_confirmed_candidates_rdkit_false"] is True
    rows = _csv_rows(gate.CONFIRMED_CANDIDATE_TABLE_CSV)
    assert len(rows) == 3
    assert list(rows[0]) == gate.CONFIRMED_CANDIDATE_TABLE_COLUMNS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    for row in rows:
        assert row["coordinate_extraction_ready"] == "True"
        assert row["training_ready"] == "False"
        assert row["sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
        assert row["coordinates_extracted"] == "False"
        assert row["distance_calculated"] == "False"
        assert row["rdkit_used"] == "False"


def test_boundary_flags_are_false() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        "raw_files_decompressed",
        "mmcif_parsed",
        "mmcif_text_read",
        "full_mmcif_parser_used",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "coordinate_geometry_calculation_run",
        "coordinates_extracted",
        "distance_calculated",
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
        "step13b_blank_table_modified",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["output_limited_to_csv_json_md"] is True


def test_gate_decision_fields() -> None:
    manifest = _manifest()
    assert manifest["real_covalent_struct_conn_candidate_manual_review_fill_validation_passed"] is True
    assert manifest["manual_review_fill_validation_contract_satisfied"] is True
    assert manifest["ready_for_confirmed_candidate_coordinate_extraction_design_gate"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert (
        manifest["recommended_next_step"]
        == "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate"
    )
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.MANUAL_FILLED_TABLE_CSV.is_file()
    assert gate.CONFIRMED_CANDIDATE_TABLE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "Step 13C validates manual fill of the Step 13B human review table",
        "Step 13B original blank human review table was restored",
        "manual-filled table is stored as a new Step 13C artifact",
        "Confirmed rows: HR_0002, HR_0003, HR_0004",
        "Duplicate excluded row: HR_0001",
        "Audit rows that remain blank: 12",
        "Confirmed candidate table row count: 3",
        f"use {parser_tools}",
        "coordinate_extraction_ready=true but training_ready=false",
        "coordinate extraction design gate, not sample_index and not training",
    ]:
        assert snippet in summary


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_struct_conn_candidate_manual_review_fill_validation.py"),
        Path("scripts/check_real_covalent_struct_conn_candidate_manual_review_fill_validation_v0.py"),
        Path("tests/test_real_covalent_struct_conn_candidate_manual_review_fill_validation_v0.py"),
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
            assert pattern not in text, f"forbidden text pattern {pattern!r} in {path}"
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
