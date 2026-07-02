from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_struct_conn_candidate_human_review_table as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _review_rows() -> list[dict[str, str]]:
    with gate.HUMAN_REVIEW_TABLE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13a_preconditions_validate() -> None:
    assert gate.validate_step13a_struct_conn_candidate_adapter_merge_smoke_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13a_struct_conn_candidate_adapter_merge_smoke_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_human_review_table_execution_contract() -> None:
    manifest = _manifest()
    assert manifest["struct_conn_candidate_human_review_table_defined"] is True
    assert manifest["struct_conn_candidate_human_review_table_executed"] is True
    assert manifest["enriched_stub_csv_read"] is True
    assert manifest["enriched_stub_row_count"] == 16
    assert manifest["human_review_table_csv_written"] is True
    assert manifest["human_review_table_row_count"] == 16
    assert manifest["candidate_like_review_row_count"] == 4
    assert manifest["high_priority_review_row_count"] == 4
    assert manifest["audit_review_row_count"] == 12
    assert manifest["processed_pdb_ids"] == gate.EXPECTED_PDB_IDS
    assert manifest["per_pdb_review_row_counts_recorded"] is True
    assert manifest["per_pdb_candidate_like_review_counts_recorded"] is True
    assert manifest["manual_review_columns_added"] is True
    assert manifest["manual_review_column_count"] == 13
    assert manifest["all_manual_review_columns_blank"] is True
    assert manifest["all_review_row_ids_unique"] is True
    assert manifest["all_review_priorities_valid"] is True
    assert manifest["high_priority_rows_first"] is True
    assert manifest["all_rows_have_partner_atom_identifiers"] is True
    assert manifest["all_rows_preserve_candidate_status"] is True
    assert manifest["all_human_review_required_true"] is True
    assert manifest["all_training_ready_false"] is True
    assert manifest["all_inference_flags_false"] is True


def test_human_review_rows_are_blank_manual_review_stubs() -> None:
    rows = _review_rows()
    assert len(rows) == 16
    assert list(rows[0]) == gate.HUMAN_REVIEW_COLUMNS
    assert [row["review_priority"] for row in rows[:4]] == ["high"] * 4
    assert [row["candidate_like"] for row in rows[:4]] == ["True"] * 4
    assert all(row["review_priority"] == "audit" for row in rows[4:])
    assert all(row["candidate_like"] == "False" for row in rows[4:])
    assert len({row["review_row_id"] for row in rows}) == 16
    for row in rows:
        assert row["human_review_required"] == "True"
        assert row["training_ready"] == "False"
        assert row["candidate_validation_status"] == "unvalidated_struct_conn_candidate"
        assert row["conn_candidate_status"] in gate.VALID_CANDIDATE_STATUSES
        assert row["source_enriched_stub_stage"] == gate.PREVIOUS_STAGE
        for column in gate.MANUAL_REVIEW_COLUMNS:
            assert row[column] == ""


def test_no_raw_parser_chemistry_training_or_dataset_outputs() -> None:
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
        "covalent_bond_atom_pair_inferred",
        "ligand_residue_role_inferred",
        "warhead_type_inferred",
        "coordinates_inferred",
        "distance_calculated",
        "manual_review_decisions_filled",
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
    assert manifest["output_limited_to_csv_json_md"] is True


def test_decision_fields() -> None:
    manifest = _manifest()
    assert manifest["real_covalent_struct_conn_candidate_human_review_table_passed"] is True
    assert manifest["struct_conn_candidate_human_review_table_contract_satisfied"] is True
    assert manifest["ready_for_manual_human_review"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "manual_fill_struct_conn_candidate_human_review_table"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.HUMAN_REVIEW_TABLE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "actual struct_conn candidate human review table",
        "read the Step 13A candidate-enriched stub CSV",
        "did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF",
        f"did not use {parser_tools}",
        "coordinate geometry, distance calculation",
        "human-reviewable candidate table",
        "Candidate-like rows are sorted first",
        "Manual review blank columns",
        "did not fill manual review decision",
        "did not infer ligand/residue role",
        "did not infer warhead_type",
        "did not claim covalent_bond_atom_pair is chemically verified",
        "human_review_required=true and training_ready=false",
        "did not write enriched sample_index and did not write final dataset",
        "manual fill of the human review table, not training",
    ]:
        assert snippet in summary


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_struct_conn_candidate_human_review_table.py"),
        Path("scripts/check_real_covalent_struct_conn_candidate_human_review_table_v0.py"),
        Path("tests/test_real_covalent_struct_conn_candidate_human_review_table_v0.py"),
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
