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

from covalent_ext import real_covalent_minimal_mmcif_adapter_smoke as gate  # noqa: E402
import check_real_covalent_minimal_mmcif_adapter_smoke_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.ADAPTER_SUMMARY_CSV.is_file()
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


def _adapter_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.ADAPTER_SUMMARY_CSV)


def test_step12x_precondition_validates_and_step12b_inherited():
    assert gate.validate_step12x_minimal_mmcif_adapter_design_gate_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_minimal_mmcif_adapter_smoke_v0"
    assert manifest["previous_stage"] == "real_covalent_minimal_mmcif_adapter_design_gate_v0"
    assert manifest["step12x_minimal_mmcif_adapter_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_adapter_smoke_execution_and_counts():
    manifest = _manifest()
    assert manifest["minimal_mmcif_adapter_smoke_defined"] is True
    assert manifest["minimal_mmcif_adapter_smoke_executed"] is True
    assert manifest["adapter_input_parser_summary_csv_read"] is True
    assert manifest["adapter_input_parser_summary_row_count"] == 3
    assert manifest["adapter_processed_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["adapter_summary_csv_written"] is True
    assert manifest["adapter_summary_row_count"] == 3
    assert manifest["all_adapter_rows_passed"] is True
    assert manifest["all_sample_ids_unique"] is True
    assert manifest["all_source_names_valid"] is True
    assert manifest["all_source_stages_valid"] is True
    assert manifest["all_adapter_status_passed_minimal_stub"] is True
    assert manifest["all_covalent_annotation_status_values_valid"] is True


def test_parser_metadata_mapping_and_unresolved_schema_fields():
    manifest = _manifest()
    assert manifest["parser_metadata_mapped_to_adapter_summary"] is True
    assert manifest["all_required_parser_fields_mapped"] is True
    assert manifest["unresolved_schema_fields_marked"] is True
    assert manifest["unresolved_schema_field_count"] == 15
    assert manifest["all_unresolved_fields_set_to_unresolved"] is True
    assert manifest["covalent_bond_atom_pair_inferred"] is False
    assert manifest["warhead_type_inferred"] is False
    assert manifest["coordinates_inferred"] is False
    assert manifest["residue_ligand_atom_annotation_inferred"] is False
    assert manifest["training_ready_samples_claimed"] is False
    assert manifest["all_training_ready_false"] is True
    assert manifest["adapter_claim_minimal_stub_only"] is True


def test_boundary_flags_for_this_step():
    manifest = _manifest()
    false_keys = [
        "raw_files_read",
        "raw_files_decompressed",
        "mmcif_parsed",
        "mmcif_text_read",
        "external_parser_used",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "coordinate_geometry_calculation_run",
        "sample_stub_json_written",
        "enriched_sample_index_written",
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "adapter_implementation_written",
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
    assert manifest["adapter_execution_run"] is True
    assert manifest["output_limited_to_csv_json_md"] is True


def test_adapter_summary_rows_have_expected_stub_values():
    rows = _adapter_rows()
    assert len(rows) == 3
    assert [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
    assert [row["sample_id"] for row in rows] == [f"PDB_DIRECT_{pdb_id}_minimal_stub" for pdb_id in EXPECTED_PDB_IDS]
    for row in rows:
        assert row["source_name"] == gate.SOURCE_NAME
        assert row["source_stage"] == gate.SOURCE_STAGE
        assert row["adapter_status"] == gate.ADAPTER_STATUS
        assert row["covalent_annotation_status"] in {
            "candidate_connections_recorded",
            "no_candidate_connection_detected",
            "not_yet_chemically_validated",
        }
        for field in gate.UNRESOLVED_FIELDS:
            assert row[field] == gate.UNRESOLVED_VALUE
        assert row["unresolved_field_count"] == "15"
        assert row["all_unresolved_fields_marked"] == "True"
        assert row["training_ready"] == "False"
        assert row["sample_stub_json_written"] == "False"
        assert row["enriched_sample_index_written"] == "False"


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_minimal_mmcif_adapter_smoke_passed"] is True
    assert manifest["minimal_mmcif_adapter_smoke_contract_satisfied"] is True
    assert manifest["ready_for_struct_conn_candidate_extraction_smoke"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_struct_conn_candidate_extraction_smoke"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.ADAPTER_SUMMARY_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "actual minimal mmCIF adapter smoke",
        "actually read the Step 12W extracted summary CSV",
        "did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF",
        f"did not use {gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}",
        "covalent_bond_atom_pair",
        "residue/ligand atom annotation",
        "coordinates",
        "warhead_type",
        "pre/post reaction geometry",
        "does not claim samples are training-ready",
        "did not write sample stub JSON and did not write enriched sample_index",
        "real_covalent_struct_conn_candidate_extraction_smoke",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_minimal_mmcif_adapter_smoke.py",
        REPO_ROOT / "scripts/check_real_covalent_minimal_mmcif_adapter_smoke_v0.py",
        REPO_ROOT / "tests/test_real_covalent_minimal_mmcif_adapter_smoke_v0.py",
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
