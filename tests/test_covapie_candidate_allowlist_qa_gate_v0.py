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

from covalent_ext import covapie_candidate_allowlist_qa_gate as qa_gate


ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_candidate_allowlist_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BC check script before artifact tests"
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


def test_step13bb_precondition_and_readiness() -> None:
    manifest13bb = json.loads(qa_gate.STEP13BB_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    precondition = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_precondition_audit.csv")
    assert manifest13bb["stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest13bb["all_checks_passed"] is True
    assert manifest13bb["candidate_allowlist_materialized"] is True
    assert manifest13bb["ready_for_covapie_candidate_allowlist_qa_gate"] is True
    assert manifest13bb["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == qa_gate.STAGE
    assert manifest["previous_stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest["step13bb_candidate_allowlist_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_allowlist_source_csv_json_schema_and_identity() -> None:
    allowlist_rows = _csv_rows(qa_gate.STEP13BB_ALLOWLIST_CSV)
    allowlist_json = json.loads(qa_gate.STEP13BB_ALLOWLIST_JSON.read_text(encoding="utf-8"))
    schema_rows = _csv_rows(qa_gate.STEP13BA_SCHEMA_CONTRACT_CSV)
    schema_identity = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_schema_identity_audit.csv")
    manifest = _manifest()
    expected_columns = [row["allowlist_field"] for row in schema_rows]
    assert expected_columns == qa_gate.ALLOWLIST_FIELDS
    assert len(allowlist_rows) == 4
    assert len(allowlist_json) == 4
    assert list(allowlist_rows[0].keys()) == expected_columns
    assert [row["allowlist_entry_id"] for row in allowlist_rows] == qa_gate.EXPECTED_ALLOWLIST_IDS
    assert [row["candidate_metadata_id"] for row in allowlist_rows] == qa_gate.EXPECTED_CANDIDATE_IDS
    assert [(row["pdb_id"], row["het_code"]) for row in allowlist_rows] == qa_gate.EXPECTED_PAIRS
    assert ("1A54", "MDC") not in {(row["pdb_id"], row["het_code"]) for row in allowlist_rows}
    assert len(schema_identity) == 4
    for key in [
        "schema_column_order_matches",
        "allowlist_entry_id_deterministic",
        "allowlist_entry_id_unique",
        "candidate_metadata_id_unique",
        "observed_pair_expected",
        "unresolved_1a54_mdc_absent",
        "all_required_fields_non_empty",
        "ready_for_training_false",
        "schema_identity_qa_passed",
    ]:
        assert {row[key] for row in schema_identity} == {"True"}
    assert {row["column_count"] for row in schema_identity} == {"25"}
    assert manifest["source_allowlist_row_count"] == 4
    assert manifest["source_allowlist_column_count"] == 25
    assert manifest["source_allowlist_json_row_count"] == 4
    assert manifest["allowlist_entry_id_unique_count"] == 4
    assert manifest["candidate_metadata_id_unique_count"] == 4
    assert manifest["schema_identity_qa_passed"] is True


def test_csv_json_consistency_is_exact() -> None:
    consistency = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_csv_json_consistency_audit.csv")
    manifest = _manifest()
    assert consistency == [
        {
            "consistency_item": "allowlist_csv_json_full_content",
            "csv_row_count": "4",
            "json_row_count": "4",
            "json_is_list_of_dicts": "True",
            "json_fields_match_schema": "True",
            "no_extra_json_fields": "True",
            "no_missing_json_fields": "True",
            "csv_json_content_identical": "True",
            "csv_json_consistency_qa_passed": "True",
            "blocking_reasons": "",
        }
    ]
    assert manifest["csv_json_consistency_qa_passed"] is True


def test_traceability_and_unresolved_exclusion_are_preserved() -> None:
    traceability = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_traceability_audit.csv")
    unresolved = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_unresolved_exclusion_audit.csv")
    manifest = _manifest()
    assert len(traceability) == 4
    assert [row["allowlist_entry_id"] for row in traceability] == qa_gate.EXPECTED_ALLOWLIST_IDS
    for key in [
        "step13ba_candidate_preview_found",
        "step13bb_qa_audit_found",
        "step13ay_candidate_metadata_found",
        "step13az_content_integrity_found",
        "step13az_traceability_found",
        "step13az_unresolved_exclusion_boundary_found",
        "traceability_qa_passed",
    ]:
        assert {row[key] for row in traceability} == {"True"}
    assert unresolved == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "present_in_step13az_unresolved_source": "True",
            "present_in_step13bb_unresolved_audit": "True",
            "present_in_allowlist_csv": "False",
            "present_in_allowlist_json": "False",
            "allowlist_entry_materialized": "False",
            "exclusion_preserved": "True",
            "unresolved_exclusion_qa_passed": "True",
            "qa_comment": "unresolved_case_remains_excluded",
        }
    ]
    assert manifest["traceability_qa_passed"] is True
    assert manifest["unresolved_exclusion_qa_passed"] is True
    assert manifest["unresolved_exclusion_preserved"] is True


def test_boundary_git_safety_training_blockers_and_readiness() -> None:
    boundary = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_boundary_safety.csv")
    git_safety = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_candidate_allowlist_qa_training_blockers.csv")
    manifest = _manifest()
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["candidate_allowlist_qa_gate"]["current_step_status"] == "executed_qa_gate_only"
    assert by_boundary["candidate_allowlist_materialization"]["current_step_status"] == "not_executed_current_step_already_completed_previous_step"
    assert by_boundary["candidate_metadata_materialization"]["current_step_status"] == "not_executed_current_step"
    for item in ["raw_read", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    for item in ["sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_step"
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
    assert manifest["candidate_allowlist_materialized_previous_step"] is True
    assert manifest["candidate_allowlist_materialized_current_step"] is False
    assert manifest["candidate_metadata_materialized_current_step"] is False
    assert manifest["raw_read_current_step"] is False
    assert manifest["raw_download_current_step"] is False
    assert manifest["sample_index_written"] is False
    assert manifest["final_dataset_written"] is False
    assert manifest["split_assignments_written"] is False
    assert manifest["leakage_matrix_written"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_design_gate"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_batch_raw_read_extraction_design_gate"
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
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_no_forbidden_imports_outputs_or_raw_tracking() -> None:
    module_path = Path("src/covalent_ext/covapie_candidate_allowlist_qa_gate.py")
    script_path = Path("scripts/check_covapie_candidate_allowlist_qa_gate_v0.py")
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
    raw_root = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")
    tracked = subprocess.run(["git", "ls-files", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in [
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
