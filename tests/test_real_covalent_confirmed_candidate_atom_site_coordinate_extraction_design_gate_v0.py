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

from covalent_ext import real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _contract_rows() -> list[dict[str, str]]:
    with gate.COORDINATE_EXTRACTION_CONTRACT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13c_precondition_and_basic_design_fields() -> None:
    assert gate.validate_step13c_manual_review_fill_validation_v0() is True
    manifest = _manifest()
    assert manifest["step13c_manual_review_fill_validation_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["confirmed_candidate_table_csv_read"] is True
    assert manifest["confirmed_candidate_table_row_count"] == 3
    assert manifest["confirmed_candidate_atom_site_coordinate_extraction_design_gate_defined"] is True
    assert manifest["confirmed_candidate_atom_site_coordinate_extraction_design_gate_executed"] is True


def test_coordinate_contract_counts_and_roles() -> None:
    manifest = _manifest()
    assert manifest["coordinate_extraction_contract_csv_written"] is True
    assert manifest["coordinate_extraction_contract_row_count"] == 6
    assert manifest["protein_endpoint_row_count"] == 3
    assert manifest["ligand_endpoint_row_count"] == 3
    assert manifest["expected_endpoint_count"] == 6
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["endpoint_rows_per_candidate_valid"] is True
    assert manifest["each_candidate_has_protein_and_ligand_endpoint"] is True
    assert manifest["all_endpoint_roles_from_manual_review"] is True
    assert manifest["all_expected_raw_paths_recorded"] is True
    assert manifest["all_atom_site_required_columns_recorded"] is True
    assert manifest["all_lookup_strategies_recorded"] is True
    assert manifest["all_coordinate_extraction_ready_true"] is True
    assert manifest["all_coordinates_extracted_false"] is True
    assert manifest["all_distance_calculated_false"] is True
    assert manifest["all_training_ready_false"] is True
    assert manifest["all_sample_index_written_false"] is True
    assert manifest["all_final_dataset_written_false"] is True


def test_contract_csv_shape_and_lookup_keys() -> None:
    rows = _contract_rows()
    assert len(rows) == 6
    assert list(rows[0]) == gate.COORDINATE_EXTRACTION_CONTRACT_COLUMNS
    by_candidate = Counter(row["confirmed_candidate_id"] for row in rows)
    assert set(by_candidate.values()) == {2}
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
        assert row["endpoint_role"] in {"protein_residue", "ligand"}
        assert row["endpoint_partner"] in {"ptnr1", "ptnr2"}
        assert row["expected_raw_path"] == (
            f"data/raw/covalent_sources/pdb_mmcif_direct/structures/{row['pdb_id']}.cif.gz"
        )
        assert "_atom_site.Cartn_x" in row["atom_site_required_columns"]
        assert "_atom_site.Cartn_y" in row["atom_site_required_columns"]
        assert "_atom_site.Cartn_z" in row["atom_site_required_columns"]
        assert row["endpoint_label_comp_id"]
        assert row["endpoint_label_atom_id"]
        assert row["endpoint_auth_comp_id"]
        assert row["endpoint_auth_atom_id"]
        assert row["coordinate_extraction_ready"] == "True"
        assert row["coordinates_extracted"] == "False"
        assert row["distance_calculated"] == "False"
        assert row["training_ready"] == "False"
        assert row["sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
    assert set(roles_by_review) == {"HR_0002", "HR_0003", "HR_0004"}
    assert all(roles == {"protein_residue", "ligand"} for roles in roles_by_review.values())


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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["output_limited_to_csv_json_md"] is True


def test_gate_decision_fields() -> None:
    manifest = _manifest()
    assert manifest["real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_passed"] is True
    assert manifest["confirmed_candidate_atom_site_coordinate_extraction_design_contract_satisfied"] is True
    assert manifest["ready_for_confirmed_candidate_atom_site_coordinate_extraction_smoke"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.COORDINATE_EXTRACTION_CONTRACT_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "confirmed candidate atom_site coordinate extraction design gate",
        "did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF",
        f"did not use {parser_tools}",
        "did not extract coordinates, did not calculate distance",
        "Confirmed candidates used: 3",
        "Atom endpoint coordinate extraction contract rows written: 6",
        "Endpoint role comes from manual review fields, not inference",
        "label/auth atom_site lookup keys and required `_atom_site` columns",
        "next step is actual atom_site coordinate extraction smoke, not sample_index and not training",
    ]:
        assert snippet in summary


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0.py"),
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
