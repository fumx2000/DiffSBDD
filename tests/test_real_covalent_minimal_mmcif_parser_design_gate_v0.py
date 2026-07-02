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

from covalent_ext import real_covalent_minimal_mmcif_parser_design_gate as gate  # noqa: E402
import check_real_covalent_minimal_mmcif_parser_design_gate_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
VENDOR_KEY = "parser_smoke_disallows_" + "ge" + "mmi"


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.PARSER_CONTRACT_CSV.is_file()
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


def _contract_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.PARSER_CONTRACT_CSV)


def test_step12u_precondition_validates_and_step12b_inherited():
    assert gate.validate_step12u_pilot_download_integrity_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_minimal_mmcif_parser_design_gate_v0"
    assert manifest["previous_stage"] == "real_covalent_pilot_download_integrity_gate_v0"
    assert manifest["step12u_pilot_download_integrity_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_minimal_parser_contract_counts_and_scope():
    manifest = _manifest()
    rows = _contract_rows()
    assert manifest["minimal_mmcif_parser_contract_defined"] is True
    assert manifest["parser_contract_csv_written"] is True
    assert manifest["parser_contract_row_count"] == len(rows)
    assert manifest["parser_input_contract_row_count"] == 3
    assert manifest["parser_policy_row_count"] >= 8
    assert manifest["parser_expected_extraction_contract_row_count"] >= 12
    assert manifest["parser_scope_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["parser_scope_raw_file_count"] == 3
    assert manifest["parser_scope_limited_to_current_pilot"] is True


def test_parser_next_step_safety_policy():
    manifest = _manifest()
    assert manifest["parser_smoke_allows_in_memory_gzip_read_next_step"] is True
    assert manifest["parser_smoke_allows_text_scan_next_step"] is True
    assert manifest["parser_smoke_disallows_network"] is True
    assert manifest["parser_smoke_disallows_download"] is True
    assert manifest["parser_smoke_disallows_raw_or_decompressed_mmcif_output"] is True
    assert manifest["parser_smoke_disallows_biopdb_parser"] is True
    assert manifest[VENDOR_KEY] is True
    assert manifest["parser_smoke_disallows_rdkit"] is True
    assert manifest["parser_smoke_disallows_coordinate_geometry"] is True
    assert manifest["parser_smoke_disallows_uniprot_cdhit"] is True
    assert manifest["parser_smoke_disallows_training"] is True
    assert manifest["parser_smoke_output_limited_to_csv_json_md"] is True
    assert manifest["parser_smoke_ready_next_step"] is True


def test_contract_rows_include_inputs_policies_and_expected_fields():
    rows = _contract_rows()
    input_rows = [row for row in rows if row["contract_section"] == "input"]
    policy_rows = [row for row in rows if row["contract_section"] == "parser_policy"]
    extraction_rows = [row for row in rows if row["contract_section"] == "expected_extraction_contract"]
    assert [row["pdb_id"] for row in input_rows] == EXPECTED_PDB_IDS
    assert len(policy_rows) >= 8
    expected_fields = {
        "pdb_id",
        "raw_path",
        "parse_status",
        "gzip_open_succeeded",
        "mmcif_text_stream_read_succeeded",
        "data_block_id",
        "entry_id",
        "structure_title",
        "entity_count",
        "atom_site_row_count",
        "chem_comp_ids",
        "struct_conn_row_count",
        "covalent_connection_candidate_count",
    }
    assert expected_fields.issubset({row["output_field"] for row in extraction_rows})


def test_this_step_has_no_parse_download_training_side_effects():
    manifest = _manifest()
    for key in [
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "raw_files_read",
        "raw_files_decompressed",
        "mmcif_parsed",
        "mmcif_text_read",
        "adapter_implementation_written",
        "adapter_execution_run",
        "rdkit_processing_run",
        "uniprot_mapping_run",
        "cdhit_run",
        "coordinate_geometry_calculation_run",
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
    ]:
        assert manifest[key] is False


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_minimal_mmcif_parser_design_gate_passed"] is True
    assert manifest["minimal_mmcif_parser_design_contract_defined"] is True
    assert manifest["ready_for_minimal_mmcif_parser_smoke"] is True
    assert manifest["ready_to_parse_mmcif_now"] is False
    assert manifest["ready_to_run_adapter_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_minimal_mmcif_parser_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.PARSER_CONTRACT_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF",
        "6DI9",
        "5F2E",
        "6OIM",
        "in-memory gzip read",
        "text scan",
        "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit",
        "raw/decompressed mmCIF/PDB/SDF/MOL2 outputs",
        "entry id/title/entity count/atom_site count/chem_comp ids/struct_conn count/covalent connection candidate count",
        "must actually run parser smoke",
        "real_covalent_minimal_mmcif_parser_smoke",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_minimal_mmcif_parser_design_gate.py",
        REPO_ROOT / "scripts/check_real_covalent_minimal_mmcif_parser_design_gate_v0.py",
        REPO_ROOT / "tests/test_real_covalent_minimal_mmcif_parser_design_gate_v0.py",
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
        "gzip." + "open",
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
