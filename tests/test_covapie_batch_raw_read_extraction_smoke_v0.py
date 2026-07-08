from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_batch_raw_read_extraction_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_batch_raw_read_extraction_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BE check script before artifact tests"
    return json.loads(path.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_step13bd_precondition_and_readiness() -> None:
    manifest13bd = json.loads(smoke.step13bd.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bd["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13bd["all_checks_passed"] is True
    assert manifest13bd["ready_for_covapie_batch_raw_read_extraction_smoke"] is True
    assert manifest13bd["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13bd_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_raw_read_audit_has_only_four_allowed_cifs_and_raw_is_untracked() -> None:
    rows = _csv_rows(ROOT / "covapie_batch_raw_read_audit.csv")
    manifest = _manifest()
    expected_paths = [
        f"data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0/{pdb_id}.cif"
        for pdb_id in smoke.ALLOWED_PDB_IDS
    ]
    assert len(rows) == 4
    assert [row["pdb_id"] for row in rows] == smoke.ALLOWED_PDB_IDS
    assert [row["expected_raw_file_path"] for row in rows] == expected_paths
    assert manifest["raw_file_read_paths"] == expected_paths
    for key in ["raw_file_exists", "raw_file_content_read_current_step", "raw_read_audit_passed"]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["raw_file_tracked_by_git"] for row in rows} == {"False"}
    assert {row["raw_file_staged_by_git"] for row in rows} == {"False"}
    assert {row["raw_read_status"] for row in rows} == {"read_success"}
    assert {row["raw_read_blocking_reason"] for row in rows} == {""}
    tracked = subprocess.run(["git", "ls-files", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert manifest["raw_file_read_count"] == 4
    assert manifest["raw_file_path_exists_count"] == 4
    assert manifest["raw_file_content_read_current_step"] is True


def test_mmcif_parser_finds_atom_site_and_struct_conn_for_all_four() -> None:
    rows = _csv_rows(ROOT / "covapie_mmcif_loop_parse_audit.csv")
    manifest = _manifest()
    assert len(rows) == 4
    assert [row["pdb_id"] for row in rows] == smoke.ALLOWED_PDB_IDS
    assert {row["atom_site_loop_found"] for row in rows} == {"True"}
    assert {row["atom_site_required_columns_found"] for row in rows} == {"True"}
    assert {row["struct_conn_loop_found"] for row in rows} == {"True"}
    assert {row["struct_conn_required_columns_found"] for row in rows} == {"True"}
    assert {row["parser_mode"] for row in rows} == {"standard_library_mmcif_loop_parser"}
    assert {row["mmcif_parse_status"] for row in rows} == {"parse_success"}
    assert {row["mmcif_loop_parse_audit_passed"] for row in rows} == {"True"}
    assert all(int(row["atom_site_row_count"]) > 0 for row in rows)
    assert all(int(row["struct_conn_row_count"]) > 0 for row in rows)
    assert manifest["mmcif_parse_current_step"] is True
    assert manifest["atom_site_scan_current_step"] is True
    assert manifest["struct_conn_scan_current_step"] is True
    assert manifest["mmcif_loop_parse_audit_passed"] is True


def test_extracted_event_table_has_four_successful_events_and_schema_order() -> None:
    rows = _csv_rows(ROOT / "covapie_extracted_event_table.csv")
    manifest = _manifest()
    assert len(rows) == 4
    assert list(rows[0].keys()) == smoke.EVENT_FIELDS
    assert [row["extracted_event_id"] for row in rows] == [
        f"extracted_event::{row['candidate_metadata_id']}" for row in rows
    ]
    assert [row["pdb_id"] for row in rows] == smoke.ALLOWED_PDB_IDS
    assert {row["residue_atom_found"] for row in rows} == {"True"}
    assert {row["ligand_atom_found"] for row in rows} == {"True"}
    assert {row["covalent_connection_found"] for row in rows} == {"True"}
    assert {row["extraction_status"] for row in rows} == {"extracted_success"}
    assert {row["extraction_blocking_reason"] for row in rows} == {""}
    assert {row["feature_semantics_audit_required_before_training"] for row in rows} == {"True"}
    assert {row["leakage_split_design_required_before_training"] for row in rows} == {"True"}
    assert {row["ready_for_training"] for row in rows} == {"False"}
    distances = [float(row["covalent_bond_distance_angstrom"]) for row in rows]
    assert all(1.0 <= distance <= 2.2 for distance in distances)
    assert manifest["extracted_event_table_written"] is True
    assert manifest["extracted_event_table_row_count"] == 4
    assert manifest["extracted_event_schema_field_count"] == 31
    assert manifest["extraction_success_count"] == 4
    assert manifest["extraction_blocked_count"] == 0
    assert manifest["residue_atom_found_count"] == 4
    assert manifest["ligand_atom_found_count"] == 4
    assert manifest["covalent_connection_found_count"] == 4


def test_atom_tables_follow_schema_and_have_rows_for_each_event() -> None:
    events = _csv_rows(ROOT / "covapie_extracted_event_table.csv")
    protein = _csv_rows(ROOT / "covapie_extracted_protein_pocket_atom_table.csv")
    ligand = _csv_rows(ROOT / "covapie_extracted_ligand_atom_table.csv")
    manifest = _manifest()
    event_ids = {row["extracted_event_id"] for row in events}
    assert list(protein[0].keys()) == smoke.ATOM_FIELDS
    assert list(ligand[0].keys()) == smoke.ATOM_FIELDS
    assert {row["atom_table_role"] for row in protein} == {"protein_pocket_atom"}
    assert {row["atom_table_role"] for row in ligand} == {"ligand_atom"}
    assert {row["ready_for_training"] for row in protein} == {"False"}
    assert {row["ready_for_training"] for row in ligand} == {"False"}
    assert {row["feature_semantics_audit_required_before_training"] for row in protein} == {"True"}
    assert {row["feature_semantics_audit_required_before_training"] for row in ligand} == {"True"}
    for event_id in event_ids:
        event = next(row for row in events if row["extracted_event_id"] == event_id)
        protein_rows = [row for row in protein if row["extracted_event_id"] == event_id]
        ligand_rows = [row for row in ligand if row["extracted_event_id"] == event_id]
        assert len(protein_rows) >= 1
        assert len(ligand_rows) >= 1
        assert any(
            row["chain_id"] == event["chain_id"]
            and row["residue_name"] == event["residue_name"]
            and row["residue_index"] == event["residue_index"]
            and row["atom_name"] == event["residue_atom_name"]
            for row in protein_rows
        )
        assert any(row["het_code"] == event["het_code"] and row["atom_name"] == event["ligand_atom_name"] for row in ligand_rows)
    assert manifest["extracted_protein_pocket_atom_table_written"] is True
    assert manifest["extracted_protein_pocket_atom_row_count"] == len(protein)
    assert manifest["extracted_ligand_atom_table_written"] is True
    assert manifest["extracted_ligand_atom_row_count"] == len(ligand)
    assert manifest["extracted_atom_schema_field_count"] == 23


def test_extraction_qa_boundary_readiness_masks_and_training_blockers() -> None:
    qa = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_qa_audit.csv")
    boundary = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_boundary_safety.csv")
    manifest = _manifest()
    assert len(qa) == 4
    for key in [
        "residue_atom_found",
        "ligand_atom_found",
        "covalent_connection_found",
        "extracted_event_schema_matches_contract",
        "atom_table_schema_matches_contract",
        "ready_for_training_false",
        "feature_semantics_blocker_preserved",
        "leakage_split_blocker_preserved",
        "extraction_qa_passed",
    ]:
        assert {row[key] for row in qa} == {"True"}
    assert all(int(row["protein_atom_rows_for_event"]) >= 1 for row in qa)
    assert all(int(row["ligand_atom_rows_for_event"]) >= 1 for row in qa)
    by_boundary = {row["boundary_item"]: row for row in boundary}
    for item in [
        "raw_file_content_read",
        "mmcif_parse",
        "atom_site_scan",
        "struct_conn_scan",
        "coordinate_extraction",
        "extracted_event_table_write",
        "extracted_atom_table_write",
    ]:
        assert by_boundary[item]["current_step_status"] == "executed_smoke_only"
    for item in ["sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert manifest["canonical_mask_task_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert manifest["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["ready_for_covapie_extraction_qa_gate"] is True
    assert manifest["ready_for_sample_index_design_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_extraction_qa_gate"


def test_no_forbidden_imports_artifacts_or_current_step_training() -> None:
    module_path = Path("src/covalent_ext/covapie_batch_raw_read_extraction_smoke.py")
    script_path = Path("scripts/check_covapie_batch_raw_read_extraction_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden] == []
    forbidden_names = {
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
    }
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    manifest = _manifest()
    for key in [
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "network_access_used",
        "urllib_used",
        "requests_used",
        "browser_used",
        "raw_structure_downloaded",
        "raw_ligand_downloaded",
        "archive_downloaded",
        "raw_file_created",
        "sdf_read",
        "pdb_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
    ]:
        assert manifest[key] is False, key
    assert manifest["raw_data_read"] is True
    assert manifest["mmcif_text_read"] is True
