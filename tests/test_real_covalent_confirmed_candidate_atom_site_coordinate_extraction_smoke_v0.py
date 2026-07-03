from __future__ import annotations

import ast
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _coordinate_rows() -> list[dict[str, str]]:
    with gate.EXTRACTED_COORDINATES_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13d_precondition_and_execution_fields() -> None:
    assert gate.validate_step13d_coordinate_extraction_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["step13d_coordinate_extraction_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["confirmed_candidate_atom_site_coordinate_extraction_smoke_defined"] is True
    assert manifest["confirmed_candidate_atom_site_coordinate_extraction_smoke_executed"] is True
    assert manifest["coordinate_contract_csv_read"] is True
    assert manifest["coordinate_contract_row_count"] == 6
    assert manifest["raw_file_count"] == 3
    assert manifest["raw_files_read"] is True
    assert manifest["raw_files_decompressed_in_memory"] is True
    assert manifest["mmcif_text_read"] is True
    assert manifest["atom_site_text_scan_run"] is True
    assert manifest["atom_site_rows_scanned_total"] > 0
    assert set(manifest["atom_site_rows_scanned_by_pdb"]) == {"6DI9", "5F2E", "6OIM"}
    assert all(count > 0 for count in manifest["atom_site_rows_scanned_by_pdb"].values())


def test_coordinate_extraction_counts_and_match_quality() -> None:
    manifest = _manifest()
    assert manifest["extracted_coordinates_csv_written"] is True
    assert manifest["extracted_coordinate_row_count"] == 6
    assert manifest["matched_endpoint_row_count"] == 6
    assert manifest["unmatched_endpoint_row_count"] == 0
    assert manifest["all_endpoint_coordinates_extracted"] is True
    assert manifest["all_required_coordinate_fields_present"] is True
    assert manifest["all_numeric_coordinate_fields_parseable"] is True
    assert manifest["all_endpoint_roles_preserved"] is True
    assert manifest["all_match_strategies_recorded"] is True
    assert manifest["all_match_statuses_recorded"] is True
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]


def test_extracted_coordinate_csv_shape_and_values() -> None:
    rows = _coordinate_rows()
    assert len(rows) == 6
    assert list(rows[0]) == gate.EXTRACTED_COORDINATE_COLUMNS
    assert sorted(Counter(row["confirmed_candidate_id"] for row in rows).values()) == [2, 2, 2]
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
        assert row["pdb_id"] in {"6DI9", "5F2E", "6OIM"}
        assert row["endpoint_role"] in {"protein_residue", "ligand"}
        assert row["match_strategy_used"] in {"label_exact", "auth_exact", "auth_ligand_seq_optional"}
        assert row["atom_site_match_status"] in {
            "matched_unique_after_policy",
            "matched_multiple_policy_selected",
        }
        assert int(row["atom_site_match_count"]) >= 1
        assert row["selected_atom_site_id"]
        assert row["selected_label_atom_id"] == row["endpoint_atom_id"]
        assert row["selected_label_comp_id"] == row["endpoint_comp_id"]
        assert row["selected_auth_atom_id"] == row["endpoint_atom_id"]
        assert row["Cartn_x"] and row["Cartn_y"] and row["Cartn_z"]
        float(row["Cartn_x"])
        float(row["Cartn_y"])
        float(row["Cartn_z"])
        if row["occupancy"]:
            float(row["occupancy"])
        if row["B_iso_or_equiv"]:
            float(row["B_iso_or_equiv"])
        assert row["coordinate_extraction_ready"] == "True"
        assert row["coordinates_extracted"] == "True"
        assert row["distance_calculated"] == "False"
        assert row["rdkit_used"] == "False"
        assert row["sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
        assert row["training_ready"] == "False"
    assert set(roles_by_review) == {"HR_0002", "HR_0003", "HR_0004"}
    assert all(roles == {"protein_residue", "ligand"} for roles in roles_by_review.values())


def test_boundary_flags_are_false() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_or_decompressed_mmcif_output_written",
        "structure_output_files_written",
        "full_mmcif_parser_used",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "coordinate_geometry_calculation_run",
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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["output_limited_to_csv_json_md"] is True


def test_gate_decision_and_outputs() -> None:
    manifest = _manifest()
    assert manifest["real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_passed"] is True
    assert manifest["confirmed_candidate_atom_site_coordinate_extraction_contract_satisfied"] is True
    assert manifest["ready_for_confirmed_candidate_coordinate_pair_sanity_gate"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.EXTRACTED_COORDINATES_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8


def test_summary_mentions_execution_and_boundaries() -> None:
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "actual confirmed candidate atom_site coordinate extraction smoke",
        "raw `.cif.gz` read",
        "decompressed raw mmCIF text in memory",
        "`_atom_site` loop",
        f"did not use {parser_tools}",
        "Endpoint coordinates extracted: 6",
        "matched_endpoint_row_count=6",
        "unmatched_endpoint_row_count=0",
        "did not calculate endpoint distance",
        "not sample_index and not training",
    ]:
        assert snippet in summary


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0.py"),
    ]
    forbidden_text = [
        "ur" + "llib",
        "re" + "quests",
        "url" + "open",
        "w" + "get",
        "cu" + "rl",
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
