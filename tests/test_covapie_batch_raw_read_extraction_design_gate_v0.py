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

from covalent_ext import covapie_batch_raw_read_extraction_design_gate as design_gate


ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_batch_raw_read_extraction_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BD check script before artifact tests"
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


def test_step13bc_precondition_and_readiness() -> None:
    manifest13bc = json.loads(design_gate.STEP13BC_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bc["stage"] == design_gate.PREVIOUS_STAGE
    assert manifest13bc["all_checks_passed"] is True
    assert manifest13bc["ready_for_covapie_batch_scale_raw_read_design_gate"] is True
    assert manifest13bc["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest13bc["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design_gate.STAGE
    assert manifest["previous_stage"] == design_gate.PREVIOUS_STAGE
    assert manifest["step13bc_candidate_allowlist_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_input_contract_rows_are_four_allowlist_events() -> None:
    rows = _csv_rows(ROOT / "covapie_batch_raw_read_input_contract.csv")
    manifest = _manifest()
    assert len(rows) == 4
    assert [row["allowlist_entry_id"] for row in rows] == design_gate.EXPECTED_ALLOWLIST_IDS
    assert [(row["pdb_id"], row["het_code"]) for row in rows] == design_gate.EXPECTED_PAIRS
    assert {row["raw_read_required_next_step"] for row in rows} == {"True"}
    assert {row["extraction_required_next_step"] for row in rows} == {"True"}
    assert {row["current_step_raw_content_read"] for row in rows} == {"False"}
    assert {row["current_step_extraction_executed"] for row in rows} == {"False"}
    assert {row["input_contract_passed"] for row in rows} == {"True"}
    assert manifest["source_allowlist_row_count"] == 4
    assert manifest["source_allowlist_column_count"] == 25
    assert manifest["batch_raw_read_input_contract_row_count"] == 4
    assert manifest["input_contract_passed"] is True


def test_raw_file_path_contract_checks_only_paths_and_git_status() -> None:
    rows = _csv_rows(ROOT / "covapie_batch_raw_file_path_contract.csv")
    manifest = _manifest()
    assert len(rows) == 4
    assert [row["pdb_id"] for row in rows] == [pdb_id for pdb_id, _ in design_gate.EXPECTED_PAIRS]
    for row in rows:
        expected = design_gate.RAW_STORAGE_ROOT / f"{row['pdb_id']}.cif"
        assert row["expected_raw_file_path"] == expected.as_posix()
        assert row["expected_raw_file_suffix"] == ".cif"
        assert row["raw_file_tracked_by_git"] == "False"
        assert row["raw_file_staged_by_git"] == "False"
        assert row["raw_file_content_read_current_step"] == "False"
        assert row["future_raw_read_allowed_after_design_gate"] == "True"
        assert row["raw_file_path_contract_passed"] == "True"
    assert manifest["raw_file_path_contract_row_count"] == 4
    assert manifest["raw_file_path_exists_count"] == sum(row["raw_file_path_exists"] == "True" for row in rows)
    assert manifest["raw_file_path_contract_passed"] is True
    assert manifest["raw_file_path_checked_current_step"] is True
    assert manifest["raw_file_content_read_current_step"] is False


def test_extracted_event_and_atom_schema_contracts_are_design_only() -> None:
    event = _csv_rows(ROOT / "covapie_extracted_event_schema_contract.csv")
    atom = _csv_rows(ROOT / "covapie_extracted_atom_table_schema_contract.csv")
    manifest = _manifest()
    assert len(event) == 31
    assert [row["extracted_event_field"] for row in event] == design_gate.EVENT_FIELDS
    assert {row["materialized_current_step"] for row in event} == {"False"}
    assert {row["required_in_future_smoke"] for row in event} == {"True"}
    assert {row["schema_contract_passed"] for row in event} == {"True"}
    assert len(atom) == 46
    assert {row["atom_table_role"] for row in atom} == {"protein_pocket_atom", "ligand_atom"}
    for role in ["protein_pocket_atom", "ligand_atom"]:
        role_rows = [row for row in atom if row["atom_table_role"] == role]
        assert [row["extracted_atom_field"] for row in role_rows] == design_gate.ATOM_FIELDS
    assert {row["materialized_current_step"] for row in atom} == {"False"}
    assert {row["required_in_future_smoke"] for row in atom} == {"True"}
    assert {row["schema_contract_passed"] for row in atom} == {"True"}
    assert manifest["extracted_event_schema_field_count"] == 31
    assert manifest["extracted_atom_schema_row_count"] == 46
    assert manifest["extracted_event_table_written"] is False
    assert manifest["extracted_atom_table_written"] is False


def test_smoke_plan_and_boundary_safety_keep_execution_for_future_step() -> None:
    plan = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_smoke_plan.csv")
    boundary = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_boundary_safety.csv")
    manifest = _manifest()
    by_plan = {row["planned_step"]: row for row in plan}
    assert len(plan) == 13
    assert by_plan["raw_file_content_read"]["planned_action"] == "ready_next_after_design_gate"
    assert by_plan["extraction_qa_gate"]["planned_action"] == "qa_after_smoke"
    assert by_plan["sample_index_design_gate"]["planned_action"] == "blocked_until_extraction_qa"
    assert by_plan["training"]["planned_action"] == "blocked"
    assert {row["plan_passed"] for row in plan} == {"True"}
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["batch_raw_read_extraction_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert by_boundary["raw_file_path_check"]["current_step_status"] == "path_exists_git_status_only_no_content_read"
    for item in [
        "raw_file_content_read",
        "mmcif_parse",
        "atom_site_scan",
        "struct_conn_scan",
        "coordinate_extraction",
        "extracted_event_table_write",
        "extracted_atom_table_write",
        "sample_index",
        "final_dataset",
        "split_assignments",
        "leakage_matrix",
        "training",
    ]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_design_gate"
        assert by_boundary[item]["allowed_current_step"] == "False"
    for item in ["network_access", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary} == {"True"}
    assert manifest["raw_read_extraction_smoke_plan_row_count"] == 13
    assert manifest["raw_read_extraction_smoke_plan_passed"] is True
    assert manifest["boundary_safety_passed"] is True


def test_git_safety_readiness_masks_and_training_boundaries() -> None:
    git_safety = _csv_rows(ROOT / "covapie_batch_raw_read_extraction_git_safety.csv")
    manifest = _manifest()
    assert len(git_safety) == 11
    assert {row["git_safety_audit_passed"] for row in git_safety} == {"True"}
    assert manifest["git_safety_passed"] is True
    assert manifest["canonical_mask_task_count"] == 5
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
    for key in [
        "candidate_allowlist_materialized_current_step",
        "raw_file_content_read_current_step",
        "raw_read_current_step",
        "raw_download_current_step",
        "mmcif_parse_current_step",
        "atom_site_scan_current_step",
        "struct_conn_scan_current_step",
        "coordinate_extraction_current_step",
        "extracted_event_table_written",
        "extracted_atom_table_written",
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
        "raw_data_read",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
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
    assert manifest["candidate_allowlist_materialized_previous_step"] is True
    assert manifest["ready_for_covapie_batch_raw_read_extraction_smoke"] is True
    assert manifest["ready_for_covapie_extraction_qa_gate"] is False
    assert manifest["ready_for_sample_index_design_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_batch_raw_read_extraction_smoke"


def test_no_forbidden_imports_outputs_or_raw_tracking() -> None:
    module_path = Path("src/covalent_ext/covapie_batch_raw_read_extraction_design_gate.py")
    script_path = Path("scripts/check_covapie_batch_raw_read_extraction_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".pdb",
        ".cif",
        ".mmcif",
        ".sdf",
        ".mol2",
        ".gz",
        ".html",
        ".htm",
    }
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden] == []
    assert not any(path.name in design_gate.FORBIDDEN_OUTPUT_NAMES for path in ROOT.rglob("*"))
    tracked = subprocess.run(["git", "ls-files", str(design_gate.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(design_gate.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
