from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_final_dataset_design_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_final_dataset_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_final_dataset_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BN check script before artifact tests"
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


def test_step13bm_precondition_and_readiness_boundary() -> None:
    manifest13bm = json.loads(gate.step13bm.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_final_dataset_design_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bm["stage"] == gate.PREVIOUS_STAGE
    assert manifest13bm["all_checks_passed"] is True
    assert manifest13bm["ready_for_covapie_final_dataset_design_gate"] is True
    assert manifest13bm["ready_for_covapie_final_dataset_smoke"] is False
    assert manifest13bm["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bm["ready_for_training"] is False
    assert manifest13bm["ready_to_train_now"] is False
    assert manifest13bm["feature_semantics_audit_completed_current_step"] is True
    assert manifest13bm["feature_semantics_known_for_training"] is False
    assert manifest13bm["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest13bm["step12d_was_smoke_legality_only"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13bm_feature_semantics_audit_gate_validated"] is True
    assert manifest["source_sample_index_row_count"] == 20
    assert manifest["source_unique_event_count"] == 4
    assert manifest["source_canonical_mask_task_count"] == 5
    assert manifest["source_split_unit_preview_row_count"] == 4
    assert manifest["source_extracted_event_table_row_count"] == 4
    assert manifest["source_protein_atom_table_row_count"] == 1071
    assert manifest["source_ligand_atom_table_row_count"] == 149
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_final_dataset_schema_contract_has_45_rows_and_required_fields() -> None:
    rows = _csv_rows(ROOT / "covapie_final_dataset_schema_contract.csv")
    manifest = _manifest()
    fields = [row["final_dataset_field_name"] for row in rows]
    assert len(rows) == 45
    for field in [
        "final_dataset_row_id",
        "sample_id",
        "split_unit_id",
        "mask_task_name",
        "mask_task_alias",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_training",
    ]:
        assert field in fields
    by_field = {row["final_dataset_field_name"]: row for row in rows}
    assert by_field["mask_task_name"]["source_field_or_policy"] == "mask_task_name"
    assert by_field["mask_task_alias"]["source_field_or_policy"] == "mask_task_alias"
    assert by_field["final_dataset_materialized_current_step"]["source_field_or_policy"] == "false_design_only"
    assert by_field["ready_for_training"]["source_field_or_policy"] == "false"
    assert {row["schema_contract_passed"] for row in rows} == {"True"}
    assert manifest["final_dataset_schema_contract_row_count"] == 45
    assert manifest["final_dataset_schema_contract_passed"] is True


def test_row_lineage_contract_maps_20_rows_to_split_units() -> None:
    rows = _csv_rows(ROOT / "covapie_final_dataset_row_lineage_contract.csv")
    manifest = _manifest()
    assert len(rows) == 20
    for row in rows:
        assert row["final_dataset_row_id"] == f"final_dataset_design::{row['sample_id']}"
        assert row["source_sample_index_row_found"] == "True"
        assert row["source_split_unit_found"] == "True"
        assert row["parent_event_group_bound_to_one_split_unit"] == "True"
        assert row["feature_semantics_audit_completed"] == "True"
        assert row["feature_semantics_known_for_training"] == "False"
        assert row["unknown_atom_feature_policy_finalized_for_training"] == "False"
        assert row["final_dataset_materialized_current_step"] == "False"
        assert row["ready_for_training"] == "False"
        assert row["row_lineage_contract_passed"] == "True"
    by_event: dict[str, set[str]] = {}
    for row in rows:
        by_event.setdefault(row["extracted_event_id"], set()).add(row["split_unit_id"])
    assert len(by_event) == 4
    assert all(len(split_units) == 1 for split_units in by_event.values())
    assert {sum(row["extracted_event_id"] == event for row in rows) for event in by_event} == {5}
    assert manifest["final_dataset_row_lineage_contract_row_count"] == 20
    assert manifest["final_dataset_row_lineage_contract_passed"] is True


def test_canonical_masks_preserved_with_b3_and_no_extra_masks() -> None:
    rows = _csv_rows(ROOT / "covapie_final_dataset_row_lineage_contract.csv")
    manifest = _manifest()
    assert sorted({row["mask_task_name"] for row in rows}) == sorted(gate.CANONICAL_MASK_TASK_NAMES)
    by_name = {row["mask_task_name"]: row["mask_task_alias"] for row in rows}
    for name, alias in zip(gate.CANONICAL_MASK_TASK_NAMES, gate.CANONICAL_MASK_TASK_ALIASES):
        assert by_name[name] == alias
    assert by_name["scaffold_only"] == "B3"
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_materialization_feature_requirement_split_policy_and_smoke_plans() -> None:
    materialization = _csv_rows(ROOT / "covapie_final_dataset_materialization_plan.csv")
    requirements = _csv_rows(ROOT / "covapie_final_dataset_feature_requirement_contract.csv")
    split_policy = _csv_rows(ROOT / "covapie_final_dataset_split_policy_contract.csv")
    smoke_plan = _csv_rows(ROOT / "covapie_final_dataset_smoke_plan.csv")
    manifest = _manifest()
    assert len(materialization) == 12
    assert len(requirements) == 13
    assert len(split_policy) == 10
    assert len(smoke_plan) == 10
    assert {row["materialization_plan_passed"] for row in materialization} == {"True"}
    assert {row["requirement_contract_passed"] for row in requirements} == {"True"}
    assert {row["split_policy_contract_passed"] for row in split_policy} == {"True"}
    assert {row["plan_passed"] for row in smoke_plan} == {"True"}
    assert any("final_dataset.csv" in row["blocked_outputs_current_step"] for row in materialization)
    req = {row["requirement_name"]: row for row in requirements}
    assert req["feature_semantics_known_for_training_false"]["current_status"] == "false_preserved"
    assert req["unknown_atom_feature_policy_not_finalized"]["blocker_before_training"] == "True"
    assert req["ready_for_training_false"]["blocker_before_training"] == "True"
    policy = {row["split_policy_name"]: row for row in split_policy}
    assert policy["no_random_row_level_split"]["current_status"] == "forbidden"
    assert policy["real_split_assignment_not_written_current_step"]["current_step_write_status"] == "not_written_current_step"
    assert policy["leakage_matrix_not_written_current_step"]["current_step_write_status"] == "not_written_current_step"
    assert policy["final_dataset_smoke_not_training_split"]["current_status"] == "smoke_only"
    plan = {row["planned_step"]: row for row in smoke_plan}
    assert plan["materialize_final_dataset_smoke_preview"]["allowed_outputs"] == "final_dataset_smoke_preview_future_step_only"
    assert "training" in plan["dataloader_smoke_blocked"]["blocked_outputs"]
    assert manifest["final_dataset_materialization_plan_passed"] is True
    assert manifest["final_dataset_feature_requirement_contract_passed"] is True
    assert manifest["final_dataset_split_policy_contract_passed"] is True
    assert manifest["final_dataset_smoke_plan_passed"] is True


def test_boundary_git_safety_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_final_dataset_design_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_final_dataset_design_git_safety.csv")
    manifest = _manifest()
    assert boundary["final_dataset_design_gate"]["current_step_status"] == "executed_design_gate_only"
    for item in [
        "read_step13bm_feature_semantics_artifacts",
        "read_step13bl_split_leakage_qa_artifacts",
        "read_step13bk_split_unit_preview",
        "read_step13bh_sample_index",
        "read_step13be_extracted_tables",
    ]:
        assert boundary[item]["current_step_status"] == "executed_derived_csv_json_read_only"
    for item in ["final_dataset_write", "final_dataset_smoke_write", "new_sample_index_write", "split_assignment_write", "leakage_matrix_write", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "raw_cif_mmcif_sdf_pdb_gzip_read", "mmcif_parse", "atom_site_scan", "struct_conn_scan", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    forbidden_names = {
        "final_dataset.csv",
        "final_dataset.json",
        "final_dataset_smoke.csv",
        "final_dataset_smoke.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "training_report.csv",
        "training_report.json",
    }
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True


def test_no_raw_network_torch_training_imports_and_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_final_dataset_design_gate.py")
    script_path = Path("scripts/check_covapie_final_dataset_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(gate.step13bd.METADATA_CSV.read_bytes()).hexdigest() == gate.METADATA_CSV_SHA256
    manifest = _manifest()
    for key in [
        "final_dataset_written",
        "final_dataset_smoke_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "real_train_val_test_split_written",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_text_read",
        "mmcif_parse_current_step",
        "atom_site_scan_current_step",
        "struct_conn_scan_current_step",
        "coordinate_extraction_current_step",
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
        "ready_for_covapie_final_dataset_qa_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["final_dataset_design_completed_current_step"] is True
    assert manifest["feature_semantics_audit_completed_current_step"] is True
    assert manifest["ready_for_covapie_final_dataset_smoke"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_final_dataset_smoke"
