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

from covalent_ext import covapie_candidate_allowlist_materialization_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_materialization_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_candidate_allowlist_materialization_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BB check script before artifact tests"
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


def test_step13ba_precondition_and_readiness() -> None:
    manifest13ba = json.loads(smoke.STEP13BA_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    precondition = _csv_rows(ROOT / "covapie_candidate_allowlist_smoke_precondition_audit.csv")
    assert manifest13ba["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13ba["all_checks_passed"] is True
    assert manifest13ba["ready_for_covapie_candidate_allowlist_materialization_smoke"] is True
    assert manifest13ba["candidate_allowlist_materialized"] is False
    assert manifest13ba["allowlist_schema_field_count"] == 25
    assert manifest13ba["allowlist_candidate_preview_row_count"] == 4
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13ba_candidate_allowlist_materialization_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_allowlist_smoke_csv_and_json_are_four_rows_with_schema_order() -> None:
    rows = _csv_rows(ROOT / "covapie_candidate_allowlist_smoke.csv")
    json_rows = json.loads((ROOT / "covapie_candidate_allowlist_smoke.json").read_text(encoding="utf-8"))
    schema_rows = _csv_rows(smoke.STEP13BA_SCHEMA_CONTRACT_CSV)
    expected_columns = [row["allowlist_field"] for row in schema_rows]
    manifest = _manifest()
    assert expected_columns == smoke.ALLOWLIST_FIELDS
    assert len(rows) == 4
    assert len(json_rows) == 4
    assert list(rows[0].keys()) == expected_columns
    assert all(set(row.keys()) == set(expected_columns) for row in json_rows)
    assert all(len(row) == 25 for row in json_rows)
    assert manifest["materialized_allowlist_row_count"] == 4
    assert manifest["materialized_allowlist_column_count"] == 25
    assert manifest["allowlist_csv_written"] is True
    assert manifest["allowlist_json_written"] is True


def test_allowlist_identity_values_are_expected_and_exclude_1a54_mdc() -> None:
    rows = _csv_rows(ROOT / "covapie_candidate_allowlist_smoke.csv")
    expected_candidate_ids = [
        "covpdb::1A3B::T29::H:SER195:OG-B",
        "covpdb::1A3E::T16::H:SER195:OG-B",
        "covpdb::1A46::00K::H:SER195:OG-C",
        "covpdb::1A5G::00L::H:SER195:OG-C",
    ]
    expected_allowlist_ids = [f"allowlist::{candidate_id}" for candidate_id in expected_candidate_ids]
    assert [row["allowlist_entry_id"] for row in rows] == expected_allowlist_ids
    assert [row["candidate_metadata_id"] for row in rows] == expected_candidate_ids
    assert len({row["allowlist_entry_id"] for row in rows}) == 4
    assert [(row["pdb_id"], row["het_code"]) for row in rows] == [
        ("1A3B", "T29"),
        ("1A3E", "T16"),
        ("1A46", "00K"),
        ("1A5G", "00L"),
    ]
    assert ("1A54", "MDC") not in {(row["pdb_id"], row["het_code"]) for row in rows}
    for row in rows:
        assert all(value != "" for value in row.values())
        assert row["project_name"] == "CovaPIE"
        assert row["source_name"] == "covpdb"
        assert row["source_database"] == "CovPDB"
        assert row["source_stage"] == smoke.STAGE
        assert row["candidate_metadata_qa_status"] == "passed"
        assert row["allowlist_entry_status"] == "allowlisted_for_future_batch_raw_read_design"
        assert row["allowlist_reason"] == "candidate_metadata_qa_passed_and_event_key_resolved"
        assert row["unresolved_exclusion_status"] == "not_unresolved_accepted_preferred_event"
        assert row["manual_review_required"] == "false"
        assert row["ready_for_training"] == "false"


def test_qa_audit_and_unresolved_exclusion_audit() -> None:
    qa = _csv_rows(ROOT / "covapie_candidate_allowlist_smoke_qa_audit.csv")
    unresolved = _csv_rows(ROOT / "covapie_candidate_allowlist_unresolved_exclusion_audit.csv")
    manifest = _manifest()
    assert len(qa) == 4
    assert {row["column_count"] for row in qa} == {"25"}
    for key in [
        "schema_column_order_matches",
        "allowlist_id_matches_design_preview",
        "allowlist_id_deterministic",
        "candidate_metadata_id_matches",
        "pair_is_allowed",
        "pair_is_not_unresolved",
        "source_candidate_metadata_found",
        "source_candidate_preview_found",
        "source_step13az_qa_found",
        "required_boolean_fields_valid",
        "ready_for_training_false",
        "qa_audit_passed",
    ]:
        assert {row[key] for row in qa} == {"True"}
    assert unresolved == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "resolution_status": "raw_no_connectivity_records_found",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "present_in_candidate_metadata": "False",
            "present_in_candidate_allowlist": "False",
            "allowlist_entry_materialized": "False",
            "exclusion_preserved": "True",
            "unresolved_exclusion_audit_passed": "True",
            "qa_comment": "unresolved_case_remains_blocked",
        }
    ]
    assert manifest["schema_content_identity_traceability_qa_passed"] is True
    assert manifest["unresolved_exclusion_preserved"] is True


def test_boundary_git_safety_training_blockers_and_readiness() -> None:
    boundary = _csv_rows(ROOT / "covapie_candidate_allowlist_boundary_safety.csv")
    git_safety = _csv_rows(ROOT / "covapie_candidate_allowlist_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_candidate_allowlist_training_blockers.csv")
    manifest = _manifest()
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["candidate_allowlist_materialization"]["current_step_status"] == "executed_first4_smoke_only"
    assert by_boundary["candidate_metadata_materialization"]["current_step_status"] == "not_executed_current_step"
    for item in ["sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["network_access", "raw_download", "raw_text_read", "rdkit_biopdb_gemmi", "torch_model_training"]:
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
    assert manifest["candidate_allowlist_materialized"] is True
    assert manifest["candidate_allowlist_materialized_current_step"] is True
    assert manifest["candidate_metadata_materialized_current_step"] is False
    assert manifest["sample_index_written"] is False
    assert manifest["final_dataset_written"] is False
    assert manifest["split_assignments_written"] is False
    assert manifest["leakage_matrix_written"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_qa_gate"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_design_gate"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_candidate_allowlist_qa_gate"
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
    module_path = Path("src/covalent_ext/covapie_candidate_allowlist_materialization_smoke.py")
    script_path = Path("scripts/check_covapie_candidate_allowlist_materialization_smoke_v0.py")
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
