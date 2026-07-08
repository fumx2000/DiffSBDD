from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_sample_index_qa_gate as qa_gate


ROOT = Path("data/derived/covalent_small/covapie_sample_index_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_index_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BI check script before artifact tests"
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


def test_step13bh_precondition_and_readiness() -> None:
    manifest13bh = json.loads(qa_gate.step13bh.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_index_qa_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bh["stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest13bh["all_checks_passed"] is True
    assert manifest13bh["sample_index_written"] is True
    assert manifest13bh["sample_index_materialized_current_step"] is True
    assert manifest13bh["ready_for_covapie_sample_index_qa_gate"] is True
    assert manifest13bh["ready_for_covapie_split_leakage_design_gate"] is False
    assert manifest13bh["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == qa_gate.STAGE
    assert manifest["previous_stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest["step13bh_sample_index_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_schema_csv_json_qa_validates_source_sample_index_without_rewrite() -> None:
    source_rows = _csv_rows(qa_gate.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    source_json = json.loads(qa_gate.step13bh.SAMPLE_INDEX_SMOKE_JSON.read_text(encoding="utf-8"))
    schema_qa = _csv_rows(ROOT / "covapie_sample_index_schema_csv_json_qa_audit.csv")
    manifest = _manifest()
    assert len(source_rows) == 20
    assert len(source_json) == 20
    assert list(source_rows[0].keys()) == qa_gate.SAMPLE_INDEX_FIELDS
    assert list(source_json[0].keys()) == qa_gate.SAMPLE_INDEX_FIELDS
    assert len(source_rows[0]) == 31
    assert {row["schema_csv_json_qa_passed"] for row in schema_qa} == {"True"}
    assert {row["qa_item"] for row in schema_qa} >= {
        "csv_row_count",
        "csv_column_count",
        "json_row_count",
        "csv_column_order_matches_contract",
        "json_field_order_matches_contract",
        "csv_json_content_identical",
        "no_extra_csv_columns",
        "no_extra_json_fields",
        "no_missing_fields",
    }
    assert manifest["source_sample_index_row_count"] == 20
    assert manifest["source_sample_index_column_count"] == 31
    assert manifest["source_sample_index_json_row_count"] == 20
    assert manifest["schema_csv_json_qa_passed"] is True
    assert manifest["sample_index_written_current_step"] is False


def test_row_identity_qa_passes_for_all_twenty_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_row_identity_qa_audit.csv")
    manifest = _manifest()
    assert len(rows) == 20
    for key in [
        "schema_order_matches_contract",
        "sample_id_deterministic",
        "sample_id_unique",
        "source_event_found",
        "source_event_extraction_success",
        "source_event_geometry_qa_passed",
        "protein_atom_rows_count_matches_source",
        "ligand_atom_rows_count_matches_source",
        "canonical_mask_task_valid",
        "canonical_mask_alias_matches_name",
        "b3_scaffold_only_alias_correct",
        "annotation_blockers_preserved",
        "auxiliary_label_blockers_preserved",
        "feature_semantics_blocker_preserved",
        "leakage_split_blocker_preserved",
        "split_assignment_status_not_written",
        "ready_for_training_false",
        "row_identity_qa_passed",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert len({row["sample_id"] for row in rows}) == 20
    for row in rows:
        assert row["sample_id"] == f"sample::{row['candidate_metadata_id']}::{row['mask_task_name']}"
    assert manifest["row_identity_qa_passed"] is True
    assert manifest["source_sample_id_unique_count"] == 20


def test_mask_distribution_qa_preserves_five_canonical_masks_and_b3() -> None:
    mask = _csv_rows(ROOT / "covapie_sample_index_mask_distribution_qa_audit.csv")
    manifest = _manifest()
    assert len(mask) == 5
    assert [row["mask_task_name"] for row in mask] == qa_gate.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in mask] == qa_gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask} == {"4"}
    assert {row["observed_unique_event_count"] for row in mask} == {"4"}
    assert {row["observed_alias_valid"] for row in mask} == {"True"}
    assert {row["mask_distribution_qa_passed"] for row in mask} == {"True"}
    assert manifest["mask_distribution_qa_passed"] is True
    assert manifest["source_canonical_mask_task_count"] == 5
    assert manifest["mask_scaffold_only_B3_count"] == 4
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_source_traceability_qa_passes_for_four_events() -> None:
    trace = _csv_rows(ROOT / "covapie_sample_index_source_traceability_qa_audit.csv")
    source_rows = _csv_rows(qa_gate.step13bh.SAMPLE_INDEX_SMOKE_CSV)
    event_counts = Counter(row["extracted_event_id"] for row in source_rows)
    manifest = _manifest()
    assert len(trace) == 4
    assert set(event_counts.values()) == {5}
    assert {row["sample_index_rows_for_event"] for row in trace} == {"5"}
    for key in [
        "source_event_table_found",
        "source_protein_atom_rows_found",
        "source_ligand_atom_rows_found",
        "step13bh_row_qa_found",
        "step13bh_mask_distribution_found",
        "step13bh_source_traceability_found",
        "step13bf_event_qa_found",
        "step13bf_atom_qa_found",
        "step13bf_geometry_qa_found",
        "step13bg_mask_expansion_contract_found",
        "source_traceability_qa_passed",
    ]:
        assert {row[key] for row in trace} == {"True"}
    assert manifest["source_traceability_qa_passed"] is True
    assert manifest["source_unique_event_count"] == 4


def test_boundary_git_safety_training_blockers_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_sample_index_qa_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_sample_index_qa_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_sample_index_qa_training_blockers.csv")
    manifest = _manifest()
    assert boundary["sample_index_qa_gate"]["current_step_status"] == "executed_qa_gate_only"
    assert boundary["read_step13bh_sample_index"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bh_qa_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["sample_index_write_current_step"]["current_step_status"] == "not_executed_current_step_already_completed_previous_step"
    for item in ["final_dataset", "split_assignments", "leakage_matrix", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "mmcif_parse", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
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
    forbidden_names = {
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
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
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []


def test_no_raw_network_runtime_model_or_training_imports_and_next_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_sample_index_qa_gate.py")
    script_path = Path("scripts/check_covapie_sample_index_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(qa_gate.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(qa_gate.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    assert manifest["sample_index_materialized_previous_step"] is True
    assert manifest["sample_index_written_previous_step"] is True
    for key in [
        "sample_index_written_current_step",
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
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_split_leakage_design_gate"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_split_leakage_design_gate"
