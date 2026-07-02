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

from covalent_ext import real_covalent_struct_conn_candidate_adapter_merge_smoke as gate  # noqa: E402
import check_real_covalent_struct_conn_candidate_adapter_merge_smoke_v0 as script  # noqa: E402


EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_outputs() -> None:
    needs_run = not (
        gate.REPORT_CSV.is_file()
        and gate.MANIFEST_JSON.is_file()
        and gate.ENRICHED_STUB_CSV.is_file()
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


def _enriched_rows() -> list[dict[str, str]]:
    _ensure_outputs()
    return _read_csv(gate.ENRICHED_STUB_CSV)


def test_step12z_and_step12y_preconditions_validate():
    assert gate.validate_step12z_struct_conn_candidate_extraction_smoke_v0() is True
    assert gate.validate_step12y_adapter_summary_v0() is True
    manifest = _manifest()
    assert manifest["stage"] == "real_covalent_struct_conn_candidate_adapter_merge_smoke_v0"
    assert manifest["previous_stage"] == "real_covalent_struct_conn_candidate_extraction_smoke_v0"
    assert manifest["step12z_struct_conn_candidate_extraction_smoke_validated"] is True
    assert manifest["step12y_minimal_mmcif_adapter_smoke_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True


def test_merge_execution_counts_and_identity():
    manifest = _manifest()
    assert manifest["struct_conn_candidate_adapter_merge_smoke_defined"] is True
    assert manifest["struct_conn_candidate_adapter_merge_smoke_executed"] is True
    assert manifest["adapter_summary_csv_read"] is True
    assert manifest["candidate_table_csv_read"] is True
    assert manifest["adapter_summary_row_count"] == 3
    assert manifest["candidate_table_row_count"] == 16
    assert manifest["enriched_stub_csv_written"] is True
    assert manifest["enriched_stub_row_count"] == 16
    assert manifest["candidate_like_enriched_stub_count"] == 4
    assert manifest["processed_pdb_ids"] == EXPECTED_PDB_IDS
    assert manifest["per_pdb_enriched_stub_counts_recorded"] is True
    assert manifest["per_pdb_candidate_like_enriched_stub_counts_recorded"] is True
    assert manifest["all_candidate_stub_ids_unique"] is True
    assert manifest["all_rows_have_adapter_metadata"] is True
    assert manifest["all_rows_have_struct_conn_candidate_metadata"] is True
    assert manifest["all_candidate_like_flags_valid"] is True
    assert manifest["all_human_review_required_true"] is True
    assert manifest["all_training_ready_false"] is True
    assert manifest["all_unresolved_fields_preserved"] is True
    assert manifest["all_candidate_validation_status_unvalidated"] is True


def test_boundary_flags_no_raw_no_parser_no_training():
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
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "external_network_called",
        "data_downloaded",
        "download_attempted",
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
    assert manifest["adapter_execution_run"] is True


def test_enriched_stub_rows_shape_and_review_policy():
    rows = _enriched_rows()
    assert len(rows) == 16
    assert list(rows[0].keys()) == gate.ENRICHED_STUB_COLUMNS
    assert {row["pdb_id"] for row in rows}.issubset(set(EXPECTED_PDB_IDS))
    assert sum(row["candidate_like"] == "True" for row in rows) == 4
    for row in rows:
        assert row["conn_candidate_status"] in gate.VALID_CANDIDATE_STATUSES
        assert row["candidate_validation_status"] == "unvalidated_struct_conn_candidate"
        assert row["human_review_required"] == "True"
        assert row["training_ready"] == "False"
        for field in gate.UNRESOLVED_FIELDS:
            assert row[field] == gate.UNRESOLVED_VALUE
        if row["candidate_like"] == "True":
            assert row["candidate_rank_within_pdb"]
        else:
            assert row["candidate_rank_within_pdb"] == ""


def test_gate_decision_and_next_step():
    manifest = _manifest()
    assert manifest["real_covalent_struct_conn_candidate_adapter_merge_smoke_passed"] is True
    assert manifest["struct_conn_candidate_adapter_merge_contract_satisfied"] is True
    assert manifest["ready_for_struct_conn_candidate_human_review_table"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_struct_conn_candidate_human_review_table"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary_written():
    _ensure_outputs()
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.ENRICHED_STUB_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    assert len(_read_csv(gate.REPORT_CSV)) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    snippets = [
        "actual struct_conn candidate adapter merge smoke",
        "read the Step 12Y minimal adapter summary CSV",
        "read the Step 12Z struct_conn candidate table CSV",
        "did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF",
        f"did not use {gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}",
        "coordinate geometry, distance calculation",
        "candidate-enriched stub CSV",
        "enriched_stub_row_count: 16",
        "candidate_like_enriched_stub_count: 4",
        "human_review_required=true and training_ready=false",
        "did not write enriched sample_index and did not write final dataset",
        "real_covalent_struct_conn_candidate_human_review_table",
    ]
    for snippet in snippets:
        assert snippet in summary


def test_ast_and_text_safety():
    files = [
        REPO_ROOT / "src/covalent_ext/real_covalent_struct_conn_candidate_adapter_merge_smoke.py",
        REPO_ROOT / "scripts/check_real_covalent_struct_conn_candidate_adapter_merge_smoke_v0.py",
        REPO_ROOT / "tests/test_real_covalent_struct_conn_candidate_adapter_merge_smoke_v0.py",
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
