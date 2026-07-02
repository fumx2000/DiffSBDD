from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from covalent_ext import real_covalent_struct_conn_candidate_extraction_smoke as gate  # noqa: E402
import check_real_covalent_struct_conn_candidate_extraction_smoke_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.CANDIDATE_TABLE_CSV.is_file()
        and gate.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = manifest["stage"] != gate.STAGE or not manifest["all_checks_passed"]
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _candidate_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.CANDIDATE_TABLE_CSV)


def test_step12y_precondition_validates_and_step12b_inherited():
    assert gate.validate_step12y_minimal_mmcif_adapter_smoke_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_struct_conn_candidate_extraction_smoke_v0"
    assert manifest["previous_stage"] == "real_covalent_minimal_mmcif_adapter_smoke_v0"
    assert manifest["step12y_minimal_mmcif_adapter_smoke_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_struct_conn_extraction_execution_counts_and_read_flags():
    manifest = _manifest()
    assert manifest["struct_conn_candidate_extraction_smoke_defined"] is True
    assert manifest["struct_conn_candidate_extraction_smoke_executed"] is True
    assert manifest["raw_file_count"] == 3
    assert manifest["raw_files_read"] is True
    assert manifest["raw_files_decompressed_in_memory"] is True
    assert manifest["mmcif_text_read"] is True
    assert manifest["struct_conn_text_scan_run"] is True
    assert manifest["processed_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["candidate_table_csv_written"] is True
    assert manifest["candidate_table_row_count"] > 0
    assert manifest["total_struct_conn_row_count"] > 0
    assert manifest["total_candidate_like_struct_conn_count"] >= 1
    assert manifest["per_pdb_struct_conn_counts_recorded"] is True
    assert manifest["per_pdb_candidate_counts_recorded"] is True
    assert manifest["all_raw_gzip_open_succeeded"] is True
    assert manifest["all_struct_conn_scans_completed"] is True
    assert manifest["all_candidate_rows_have_conn_type_status"] is True
    assert manifest["all_candidate_rows_have_partner_fields"] is True
    assert manifest["struct_conn_distance_values_recorded_if_present"] is True


def test_parser_boundary_and_no_inference_flags():
    manifest = _manifest()
    assert manifest["full_mmcif_parser_used"] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["biopdb_parser_used"] is False
    assert manifest[gate.VENDOR_USED_KEY] is False
    assert manifest["rdkit_used"] is False
    assert manifest["coordinate_geometry_calculation_run"] is False
    assert manifest["covalent_bond_atom_pair_inferred"] is False
    assert manifest["ligand_residue_role_inferred"] is False
    assert manifest["warhead_type_inferred"] is False
    assert manifest["coordinates_inferred"] is False
    assert manifest["raw_or_decompressed_mmcif_output_written"] is False
    assert manifest["structure_output_files_written"] is False
    assert manifest["enriched_sample_index_written"] is False
    assert manifest["training_ready_samples_claimed"] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_still_prohibited_flags():
    manifest = _manifest()
    for key in [
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
    ]:
        assert manifest[key] is False


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_struct_conn_candidate_extraction_smoke_passed"] is True
    assert manifest["struct_conn_candidate_extraction_contract_satisfied"] is True
    assert manifest["ready_for_struct_conn_candidate_adapter_merge_smoke"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_struct_conn_candidate_adapter_merge_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_candidate_table_shape_and_row_flags():
    rows = _candidate_rows()
    assert rows
    assert list(rows[0].keys()) == gate.CANDIDATE_TABLE_COLUMNS
    assert {row["pdb_id"] for row in rows}.issubset(set(EXPECTED_PDB_IDS))
    statuses = {
        "covalent_like_candidate",
        "disulfide_like_candidate",
        "link_like_candidate",
        "modres_like_candidate",
        "non_candidate_recorded",
        "no_struct_conn_rows_detected",
    }
    candidate_like = {
        "covalent_like_candidate",
        "disulfide_like_candidate",
        "link_like_candidate",
        "modres_like_candidate",
    }
    assert any(row["conn_candidate_status"] in candidate_like for row in rows)
    for row in rows:
        assert row["parser_library_used"] == "none"
        assert row["conn_candidate_status"] in statuses
        assert row["full_mmcif_parser_used"] == "False"
        assert row["biopdb_parser_used"] == "False"
        assert row[gate.VENDOR_USED_KEY] == "False"
        assert row["rdkit_used"] == "False"
        assert row["coordinate_geometry_calculation_run"] == "False"
        assert row["covalent_bond_atom_pair_inferred"] == "False"
        assert row["ligand_residue_role_inferred"] == "False"
        assert row["warhead_type_inferred"] == "False"
        assert row["coordinates_inferred"] == "False"


def test_outputs_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.CANDIDATE_TABLE_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "actual struct_conn candidate extraction smoke",
        "actually read 3 raw `.cif.gz` files",
        "`_struct_conn` loop",
        f"did not use {gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}",
        "coordinate geometry",
        "does not infer ligand/residue role",
        "does not claim samples are training-ready",
        "candidate_table_row_count",
        "total_struct_conn_row_count",
        "total_candidate_like_struct_conn_count",
        "real_covalent_struct_conn_candidate_adapter_merge_smoke",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_struct_conn_candidate_extraction_smoke.py",
        REPO_ROOT / "scripts/check_real_covalent_struct_conn_candidate_extraction_smoke_v0.py",
        REPO_ROOT / "tests/test_real_covalent_struct_conn_candidate_extraction_smoke_v0.py",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "back" + "ward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "MolFrom" + "Smiles",
        "MolFrom" + "MolFile",
        "MolFrom" + "PDBFile",
        "GetMorgan" + "Fingerprint",
        "GetMorgan" + "FingerprintAsBitVect",
        "url" + "open",
    }
    forbidden_text = [
        "url" + "lib",
        "requ" + "ests",
        "url" + "open",
        "w" + "get",
        "cu" + "rl",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "ge" + "mmi",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "mod" + "el(",
        "compute_" + "masked_loss",
        ".back" + "ward(",
        "torch." + "optim",
        "optimizer." + "step",
        "trainer." + "fit",
        "training_" + "step(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "numpy." + "load",
        "np." + "load",
    ]
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
