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

from covalent_ext import covapie_sample_index_design_gate as design_gate


ROOT = Path("data/derived/covalent_small/covapie_sample_index_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_index_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BG check script before artifact tests"
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


def test_step13bf_precondition_and_readiness() -> None:
    manifest13bf = json.loads(design_gate.step13bf.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_index_design_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bf["stage"] == design_gate.PREVIOUS_STAGE
    assert manifest13bf["all_checks_passed"] is True
    assert manifest13bf["ready_for_covapie_sample_index_design_gate"] is True
    assert manifest13bf["ready_for_covapie_sample_index_smoke"] is False
    assert manifest13bf["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design_gate.STAGE
    assert manifest["previous_stage"] == design_gate.PREVIOUS_STAGE
    assert manifest["step13bf_extraction_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_source_artifact_contract_reads_required_derived_artifacts() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_source_artifact_contract.csv")
    manifest = _manifest()
    assert [row["source_artifact_name"] for row in rows] == [
        "extracted_event_table",
        "extracted_protein_pocket_atom_table",
        "extracted_ligand_atom_table",
        "extraction_qa_gate_manifest",
        "event_table_qa_audit",
        "atom_table_qa_audit",
        "geometry_qa_audit",
        "traceability_qa_audit",
    ]
    assert {row["required_for_future_sample_index_smoke"] for row in rows} == {"True"}
    assert {row["exists_current_step"] for row in rows} == {"True"}
    assert {row["content_read_current_step"] for row in rows} == {"True"}
    assert {row["source_artifact_contract_passed"] for row in rows} == {"True"}
    assert manifest["source_artifact_contract_passed"] is True


def test_sample_index_schema_contract_has_exactly_31_design_only_fields() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_schema_contract.csv")
    manifest = _manifest()
    assert len(rows) == 31
    assert [row["sample_index_field"] for row in rows] == design_gate.SAMPLE_INDEX_FIELDS
    assert [int(row["field_order"]) for row in rows] == list(range(1, 32))
    assert {row["materialized_current_step"] for row in rows} == {"False"}
    assert {row["required_in_future_sample_index_smoke"] for row in rows} == {"True"}
    assert {row["schema_contract_passed"] for row in rows} == {"True"}
    assert manifest["future_sample_index_schema_field_count"] == 31
    assert manifest["sample_index_schema_contract_passed"] is True


def test_mask_task_expansion_contract_is_four_events_by_five_canonical_masks() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_mask_task_expansion_contract.csv")
    manifest = _manifest()
    assert len(rows) == 20
    event_ids = sorted({row["extracted_event_id"] for row in rows})
    mask_names = [row["mask_task_name"] for row in rows]
    aliases = [row["mask_task_alias"] for row in rows]
    assert len(event_ids) == 4
    for event_id in event_ids:
        event_rows = [row for row in rows if row["extracted_event_id"] == event_id]
        assert [row["mask_task_name"] for row in event_rows] == design_gate.CANONICAL_MASK_TASK_NAMES
        assert [row["mask_task_alias"] for row in event_rows] == design_gate.CANONICAL_MASK_TASK_ALIASES
    assert {name: mask_names.count(name) for name in design_gate.CANONICAL_MASK_TASK_NAMES} == {name: 4 for name in design_gate.CANONICAL_MASK_TASK_NAMES}
    assert {alias: aliases.count(alias) for alias in design_gate.CANONICAL_MASK_TASK_ALIASES} == {alias: 4 for alias in design_gate.CANONICAL_MASK_TASK_ALIASES}
    assert ("scaffold_only" in mask_names) and ("B3" in aliases)
    for key in [
        "event_qa_passed",
        "atom_qa_passed",
        "geometry_qa_passed",
        "scaffold_linker_warhead_annotation_required",
        "auxiliary_labels_required",
        "ready_for_future_sample_index_smoke",
        "mask_task_expansion_contract_passed",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["materialized_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training"] for row in rows} == {"False"}
    assert manifest["future_mask_task_expansion_row_count"] == 20
    assert manifest["future_unique_event_count"] == 4
    assert manifest["future_mask_task_count"] == 5
    assert manifest["future_planned_sample_count"] == 20
    assert manifest["mask_task_expansion_contract_passed"] is True
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_sample_index_smoke_plan_boundary_and_training_blockers() -> None:
    plan = _csv_rows(ROOT / "covapie_sample_index_smoke_plan.csv")
    boundary = _csv_rows(ROOT / "covapie_sample_index_design_boundary_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_sample_index_design_training_blockers.csv")
    manifest = _manifest()
    assert [row["planned_step"] for row in plan] == [
        "read_extraction_qa_gate",
        "read_extracted_event_table",
        "read_extracted_atom_tables",
        "expand_4_events_to_20_mask_task_rows",
        "assign_deterministic_sample_ids",
        "write_sample_index_smoke_csv",
        "write_sample_index_smoke_json",
        "sample_index_qa_gate",
        "split_leakage_design_gate",
        "feature_semantics_audit_gate",
        "final_dataset_design_gate",
        "dataloader_smoke",
        "training",
    ]
    assert {row["plan_passed"] for row in plan} == {"True"}
    assert plan[-1]["planned_action"] == "blocked"
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["sample_index_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert by_boundary["read_step13bf_derived_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert by_boundary["sample_index_write"]["current_step_status"] == "blocked_current_design_gate"
    for item in ["final_dataset", "split_assignments", "leakage_matrix", "dataloader_smoke", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "mmcif_parse", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary} == {"True"}
    assert [row["training_blocker_item"] for row in blockers[:5]] == [
        "mask_warhead_only_A",
        "mask_linker_plus_warhead_B",
        "mask_scaffold_plus_warhead_B2",
        "mask_scaffold_only_B3",
        "mask_scaffold_plus_linker_plus_warhead_C",
    ]
    assert {row["training_blocker_passed"] for row in blockers} == {"True"}
    assert manifest["sample_index_smoke_plan_passed"] is True
    assert manifest["boundary_safety_passed"] is True
    assert manifest["training_blockers_passed"] is True


def test_no_sample_index_downstream_raw_model_or_training_actions() -> None:
    module_path = Path("src/covalent_ext/covapie_sample_index_design_gate.py")
    script_path = Path("scripts/check_covapie_sample_index_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
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
    tracked = subprocess.run(["git", "ls-files", str(design_gate.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(design_gate.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in [
        "sample_index_materialized_current_step",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
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
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_sample_index_smoke"] is True
    assert manifest["ready_for_covapie_sample_index_qa_gate"] is False
    assert manifest["ready_for_covapie_split_leakage_design_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["scaffold_linker_warhead_annotation_required_before_training"] is True
    assert manifest["auxiliary_labels_required_before_training"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_sample_index_smoke"
