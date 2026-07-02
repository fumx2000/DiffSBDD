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

from covalent_ext import real_covalent_minimal_mmcif_parser_smoke as smoke  # noqa: E402
import check_real_covalent_minimal_mmcif_parser_smoke_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
VENDOR_USED_KEY = "ge" + "mmi_used"


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        smoke.REPORT_CSV.is_file()
        and smoke.MANIFEST_JSON.is_file()
        and smoke.EXTRACTED_SUMMARY_CSV.is_file()
        and smoke.SUMMARY_MD.is_file()
    )
    if not needs_run:
        manifest = json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))
        needs_run = manifest["stage"] != smoke.STAGE or not manifest["all_checks_passed"]
    if needs_run:
        assert script.run() == 0


def _manifest() -> dict:
    _ensure_outputs()
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def _summary_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(smoke.EXTRACTED_SUMMARY_CSV)


def _bool_text(value: str) -> bool:
    return value == "True"


def test_step12v_precondition_validates_and_step12b_inherited():
    assert smoke.validate_step12v_minimal_mmcif_parser_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_minimal_mmcif_parser_smoke_v0"
    assert manifest["previous_stage"] == "real_covalent_minimal_mmcif_parser_design_gate_v0"
    assert manifest["step12v_minimal_mmcif_parser_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_parser_smoke_execution_and_counts():
    manifest = _manifest()
    assert manifest["minimal_mmcif_parser_smoke_defined"] is True
    assert manifest["minimal_mmcif_parser_smoke_executed"] is True
    assert manifest["parser_input_raw_file_count"] == 3
    assert manifest["parser_processed_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["parser_extracted_summary_csv_written"] is True
    assert manifest["parser_extracted_summary_row_count"] == 3
    assert manifest["all_parser_rows_passed"] is True
    assert manifest["all_gzip_open_succeeded"] is True
    assert manifest["all_mmcif_text_stream_read_succeeded"] is True
    assert manifest["all_data_block_ids_present"] is True
    assert manifest["all_entry_ids_present"] is True
    assert manifest["all_entity_counts_positive"] is True
    assert manifest["all_atom_site_row_counts_positive"] is True
    assert manifest["all_chem_comp_id_counts_positive"] is True
    assert manifest["struct_conn_counts_recorded"] is True
    assert manifest["covalent_connection_candidate_counts_recorded"] is True


def test_parser_boundary_and_allowed_read_scope():
    manifest = _manifest()
    assert manifest["raw_files_read"] is True
    assert manifest["raw_files_decompressed_in_memory"] is True
    assert manifest["mmcif_text_read"] is True
    assert manifest["mmcif_text_scan_run"] is True
    assert manifest["full_mmcif_parser_used"] is False
    assert manifest["biopdb_parser_used"] is False
    assert manifest[VENDOR_USED_KEY] is False
    assert manifest["rdkit_used"] is False
    assert manifest["coordinate_geometry_calculation_run"] is False
    assert manifest["extraction_writes_coordinates"] is False
    assert manifest["extraction_writes_atom_table"] is False
    assert manifest["raw_or_decompressed_mmcif_output_written"] is False
    assert manifest["structure_output_files_written"] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["output_limited_to_csv_json_md"] is True


def test_prohibited_operations_remain_false():
    manifest = _manifest()
    for key in [
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "adapter_implementation_written",
        "adapter_execution_run",
        "uniprot_mapping_run",
        "cdhit_run",
        "npz_files_loaded",
        "npz_contents_read",
        "enriched_sample_index_written",
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


def test_extracted_summary_rows_have_minimal_metadata():
    rows = _summary_rows()
    assert len(rows) == 3
    assert [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
    for row in rows:
        assert row["parse_status"] == "passed"
        assert _bool_text(row["gzip_open_succeeded"]) is True
        assert _bool_text(row["mmcif_text_stream_read_succeeded"]) is True
        assert row["data_block_id"]
        assert row["entry_id"]
        assert int(row["atom_site_row_count"]) > 0
        assert int(row["entity_count"]) > 0
        assert int(row["chem_comp_id_count"]) > 0
        assert "struct_conn_row_count" in row
        assert "covalent_connection_candidate_count" in row
        assert _bool_text(row["extraction_writes_coordinates"]) is False
        assert _bool_text(row["extraction_writes_atom_table"]) is False
        assert _bool_text(row["raw_or_decompressed_mmcif_output_written"]) is False
        assert row["parser_library_used"] == "none"
        assert row["error_message"] == ""


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_minimal_mmcif_parser_smoke_passed"] is True
    assert manifest["minimal_mmcif_parser_smoke_contract_satisfied"] is True
    assert manifest["ready_for_minimal_mmcif_adapter_design_gate"] is True
    assert manifest["ready_to_run_adapter_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_minimal_mmcif_adapter_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary_written():
    _ensure_outputs()
    assert smoke.REPORT_CSV.is_file()
    assert smoke.MANIFEST_JSON.is_file()
    assert smoke.EXTRACTED_SUMMARY_CSV.is_file()
    assert smoke.SUMMARY_MD.is_file()
    assert len(_read_csv(smoke.REPORT_CSV)) == 8
    summary = smoke.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "actual minimal mmCIF parser smoke",
        "actually read 3 raw `.cif.gz` files",
        "standard library gzip.open",
        "in-memory text scan",
        "did not network and did not re-download",
        "did not write raw/decompressed mmCIF/PDB/SDF/MOL2 outputs",
        "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit",
        "adapters, coordinate geometry, UniProt/CD-HIT, NPZ reads, or training",
        "6DI9",
        "5F2E",
        "6OIM",
        "entry id, structure title, entity count, atom_site row count, chem_comp ids, struct_conn row count, and covalent connection candidate count",
        "does not claim complete structure parsing",
        "real_covalent_minimal_mmcif_adapter_design_gate",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_minimal_mmcif_parser_smoke.py",
        REPO_ROOT / "scripts/check_real_covalent_minimal_mmcif_parser_smoke_v0.py",
        REPO_ROOT / "tests/test_real_covalent_minimal_mmcif_parser_smoke_v0.py",
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
