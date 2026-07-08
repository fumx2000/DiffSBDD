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

from covalent_ext import covapie_extraction_qa_gate as qa_gate


ROOT = Path("data/derived/covalent_small/covapie_extraction_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_extraction_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BF check script before artifact tests"
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


def test_step13be_precondition_and_readiness() -> None:
    manifest13be = json.loads(qa_gate.step13be.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_extraction_qa_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13be["stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest13be["all_checks_passed"] is True
    assert manifest13be["ready_for_covapie_extraction_qa_gate"] is True
    assert manifest13be["ready_for_sample_index_design_gate"] is False
    assert manifest13be["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == qa_gate.STAGE
    assert manifest["previous_stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest["step13be_extraction_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_event_table_qa_validates_schema_identity_success_and_distances() -> None:
    event_source = _csv_rows(qa_gate.step13be.EXTRACTED_EVENT_TABLE_CSV)
    event_qa = _csv_rows(ROOT / "covapie_extracted_event_table_qa_audit.csv")
    manifest = _manifest()
    assert len(event_source) == 4
    assert list(event_source[0].keys()) == qa_gate.EVENT_FIELDS
    assert len(event_qa) == 4
    assert {row["column_count"] for row in event_qa} == {"31"}
    for key in [
        "schema_order_matches_contract",
        "extracted_event_id_deterministic",
        "extracted_event_id_unique",
        "allowlist_entry_id_unique",
        "candidate_metadata_id_unique",
        "extraction_success",
        "extraction_blocking_reason_empty",
        "residue_atom_found",
        "ligand_atom_found",
        "covalent_connection_found",
        "covalent_bond_distance_numeric",
        "covalent_bond_distance_plausible_1_0_to_2_2",
        "ready_for_training_false",
        "feature_semantics_blocker_preserved",
        "leakage_split_blocker_preserved",
        "extracted_event_table_qa_passed",
    ]:
        assert {row[key] for row in event_qa} == {"True"}
    assert {row["extraction_status"] for row in event_qa} == {"extracted_success"}
    distances = [float(row["covalent_bond_distance_angstrom"]) for row in event_qa]
    assert min(distances) == 1.572
    assert max(distances) == 1.821
    assert manifest["source_extracted_event_row_count"] == 4
    assert manifest["source_extracted_event_column_count"] == 31
    assert manifest["extracted_event_table_qa_passed"] is True
    assert manifest["extraction_success_count"] == 4
    assert manifest["extraction_blocked_count"] == 0
    assert manifest["residue_atom_found_count"] == 4
    assert manifest["ligand_atom_found_count"] == 4
    assert manifest["covalent_connection_found_count"] == 4


def test_atom_table_qa_validates_schema_counts_coordinates_and_endpoint_atoms() -> None:
    protein = _csv_rows(qa_gate.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand = _csv_rows(qa_gate.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    atom_qa = _csv_rows(ROOT / "covapie_extracted_atom_table_qa_audit.csv")
    manifest = _manifest()
    assert len(protein) == 1071
    assert len(ligand) == 149
    assert list(protein[0].keys()) == qa_gate.ATOM_FIELDS
    assert list(ligand[0].keys()) == qa_gate.ATOM_FIELDS
    assert len(atom_qa) == 4
    assert all(int(row["protein_atom_rows_for_event"]) >= 1 for row in atom_qa)
    assert all(int(row["ligand_atom_rows_for_event"]) >= 1 for row in atom_qa)
    for key in [
        "protein_table_schema_matches_contract",
        "ligand_table_schema_matches_contract",
        "protein_rows_have_numeric_coordinates",
        "ligand_rows_have_numeric_coordinates",
        "protein_rows_ready_for_training_false",
        "ligand_rows_ready_for_training_false",
        "protein_feature_semantics_blocker_preserved",
        "ligand_feature_semantics_blocker_preserved",
        "covalent_residue_atom_present_in_protein_table",
        "covalent_ligand_atom_present_in_ligand_table",
        "extracted_atom_table_qa_passed",
    ]:
        assert {row[key] for row in atom_qa} == {"True"}
    assert manifest["source_protein_pocket_atom_row_count"] == 1071
    assert manifest["source_ligand_atom_row_count"] == 149
    assert manifest["extracted_atom_table_qa_passed"] is True


def test_geometry_qa_recomputes_distances_from_event_table_coordinates() -> None:
    geometry = _csv_rows(ROOT / "covapie_extracted_geometry_qa_audit.csv")
    manifest = _manifest()
    assert len(geometry) == 4
    for key in [
        "residue_atom_xyz_present",
        "ligand_atom_xyz_present",
        "distance_recompute_matches_event_table",
        "geometry_qa_passed",
    ]:
        assert {row[key] for row in geometry} == {"True"}
    assert {row["distance_plausibility_status"] for row in geometry} == {"plausible_covalent_distance"}
    assert all(float(row["distance_absolute_delta"]) <= 0.001 for row in geometry)
    assert manifest["geometry_qa_passed"] is True
    assert manifest["covalent_bond_distance_min_angstrom"] == 1.572
    assert manifest["covalent_bond_distance_max_angstrom"] == 1.821


def test_traceability_qa_links_events_to_prior_audits_contracts_and_atom_tables() -> None:
    trace = _csv_rows(ROOT / "covapie_extraction_traceability_qa_audit.csv")
    manifest = _manifest()
    assert len(trace) == 4
    for key in [
        "step13be_raw_read_audit_found",
        "step13be_mmcif_parse_audit_found",
        "step13be_extraction_qa_audit_found",
        "step13bd_input_contract_found",
        "step13bd_event_schema_contract_found",
        "step13bd_atom_schema_contract_found",
        "step13bb_allowlist_entry_found",
        "protein_atom_rows_found",
        "ligand_atom_rows_found",
        "traceability_qa_passed",
    ]:
        assert {row[key] for row in trace} == {"True"}
    assert manifest["traceability_qa_passed"] is True


def test_boundary_git_safety_training_blockers_and_readiness() -> None:
    boundary = _csv_rows(ROOT / "covapie_extraction_qa_boundary_safety.csv")
    git_safety = _csv_rows(ROOT / "covapie_extraction_qa_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_extraction_qa_training_blockers.csv")
    manifest = _manifest()
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["extraction_qa_gate"]["current_step_status"] == "executed_qa_gate_only"
    assert by_boundary["read_step13be_derived_tables"]["current_step_status"] == "executed_derived_csv_json_read_only"
    for item in ["raw_file_content_read", "mmcif_parse", "atom_site_scan", "struct_conn_scan", "coordinate_extraction"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_current_step"
    for item in ["extracted_event_table_write", "extracted_atom_table_write"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_current_step_already_completed_previous_step"
    for item in ["sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_safety} == {"True"}
    assert [row["training_blocker_item"] for row in blockers[:5]] == [
        "mask_warhead_only_A",
        "mask_linker_plus_warhead_B",
        "mask_scaffold_plus_warhead_B2",
        "mask_scaffold_only_B3",
        "mask_scaffold_plus_linker_plus_warhead_C",
    ]
    assert {row["training_blocker_passed"] for row in blockers} == {"True"}
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True
    assert manifest["training_blockers_passed"] is True
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
    assert manifest["ready_for_covapie_sample_index_design_gate"] is True
    assert manifest["ready_for_covapie_sample_index_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_sample_index_design_gate"


def test_no_forbidden_imports_raw_read_or_downstream_outputs() -> None:
    module_path = Path("src/covalent_ext/covapie_extraction_qa_gate.py")
    script_path = Path("scripts/check_covapie_extraction_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden] == []
    forbidden_names = {
        "covapie_extracted_event_table.csv",
        "covapie_extracted_protein_pocket_atom_table.csv",
        "covapie_extracted_ligand_atom_table.csv",
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
    tracked = subprocess.run(["git", "ls-files", str(qa_gate.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(qa_gate.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in [
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_text_read",
        "mmcif_parse_current_step",
        "atom_site_scan_current_step",
        "struct_conn_scan_current_step",
        "coordinate_extraction_current_step",
        "extracted_event_table_written_current_step",
        "extracted_atom_table_written_current_step",
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
