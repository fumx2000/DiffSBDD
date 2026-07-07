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

from covalent_ext import covapie_candidate_allowlist_materialization_design_gate as design_gate


ROOT = Path("data/derived/covalent_small/covapie_candidate_allowlist_materialization_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_candidate_allowlist_materialization_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BA check script before artifact tests"
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


def test_step13az_precondition_and_readiness() -> None:
    manifest13az = json.loads(design_gate.STEP13AZ_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    assert manifest13az["stage"] == design_gate.PREVIOUS_STAGE
    assert manifest13az["all_checks_passed"] is True
    assert manifest13az["ready_for_covapie_candidate_allowlist_materialization_design_gate"] is True
    assert manifest["stage"] == design_gate.STAGE
    assert manifest["previous_stage"] == design_gate.PREVIOUS_STAGE
    assert manifest["step13az_candidate_metadata_materialization_qa_gate_validated"] is True
    assert manifest["candidate_metadata_qa_row_count"] == 4
    assert manifest["candidate_metadata_qa_column_count"] == 33
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_allowlist_schema_contract_has_fixed_25_field_order() -> None:
    schema = _csv_rows(ROOT / "covapie_candidate_allowlist_schema_contract.csv")
    manifest = _manifest()
    assert [row["allowlist_field"] for row in schema] == design_gate.ALLOWLIST_FIELDS
    assert [int(row["field_order"]) for row in schema] == list(range(1, 26))
    assert len(schema) == 25
    assert {row["allowlist_schema_contract_passed"] for row in schema} == {"True"}
    assert {row["materialization_status"] for row in schema} == {"design_only_not_materialized"}
    assert {row["training_use_status"] for row in schema} == {"not_training_input_yet"}
    assert manifest["allowlist_schema_field_count"] == 25
    assert manifest["allowlist_schema_contract_passed"] is True


def test_candidate_preview_has_four_unique_design_only_allowlist_ids() -> None:
    preview = _csv_rows(ROOT / "covapie_candidate_allowlist_candidate_preview.csv")
    manifest = _manifest()
    expected_candidate_ids = [
        "covpdb::1A3B::T29::H:SER195:OG-B",
        "covpdb::1A3E::T16::H:SER195:OG-B",
        "covpdb::1A46::00K::H:SER195:OG-C",
        "covpdb::1A5G::00L::H:SER195:OG-C",
    ]
    expected_allowlist_ids = [f"allowlist::{candidate_id}" for candidate_id in expected_candidate_ids]
    assert len(preview) == 4
    assert [row["candidate_metadata_id"] for row in preview] == expected_candidate_ids
    assert [row["allowlist_entry_id_preview"] for row in preview] == expected_allowlist_ids
    assert len(expected_allowlist_ids) == len(set(expected_allowlist_ids))
    assert {row["candidate_metadata_qa_status"] for row in preview} == {"passed"}
    assert {row["allowlist_entry_status"] for row in preview} == {"eligible_for_future_allowlist_smoke"}
    assert {row["preview_only"] for row in preview} == {"True"}
    assert {row["current_step_allowlist_materialized"] for row in preview} == {"False"}
    assert {row["not_a_materialized_allowlist"] for row in preview} == {"True"}
    assert {row["candidate_preview_passed"] for row in preview} == {"True"}
    assert ("1A54", "MDC") not in {(row["pdb_id"], row["het_code"]) for row in preview}
    assert manifest["allowlist_candidate_preview_row_count"] == 4
    assert manifest["allowlist_entry_id_preview_count"] == 4
    assert manifest["allowlist_entry_id_preview_unique_count"] == 4
    assert manifest["allowlist_candidate_preview_passed"] is True


def test_unresolved_exclusion_policy_and_materialization_plan() -> None:
    exclusion = _csv_rows(ROOT / "covapie_candidate_allowlist_exclusion_policy.csv")
    plan = _csv_rows(ROOT / "covapie_candidate_allowlist_materialization_plan.csv")
    manifest = _manifest()
    assert exclusion == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "resolution_status": "raw_no_connectivity_records_found",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "candidate_metadata_present": "False",
            "allowlist_entry_preview_created": "False",
            "allowlist_entry_materialized": "False",
            "exclusion_policy": "manual_review_or_connectivity_fallback_design_required",
            "exclusion_policy_passed": "True",
        }
    ]
    by_plan = {row["planned_step"]: row for row in plan}
    assert by_plan["candidate_allowlist_materialization_smoke"]["planned_action"] == "ready_next"
    assert by_plan["candidate_allowlist_qa_gate"]["planned_action"] == "qa_after_smoke"
    assert by_plan["batch_raw_read_design_gate"]["planned_action"] == "blocked_until_allowlist_qa"
    assert by_plan["batch_raw_read_smoke"]["planned_action"] == "blocked_until_batch_raw_read_design_gate"
    assert by_plan["training"]["planned_action"] == "blocked"
    assert {row["plan_passed"] for row in plan} == {"True"}
    assert manifest["unresolved_exclusion_policy_row_count"] == 1
    assert manifest["unresolved_exclusion_policy_passed"] is True
    assert manifest["materialization_plan_passed"] is True


def test_boundary_safety_git_safety_training_blockers_and_readiness() -> None:
    boundary = _csv_rows(ROOT / "covapie_candidate_allowlist_boundary_safety.csv")
    git_safety = _csv_rows(ROOT / "covapie_candidate_allowlist_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_candidate_allowlist_training_blockers.csv")
    manifest = _manifest()
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["candidate_allowlist_materialization_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert by_boundary["candidate_allowlist_materialization"]["current_step_status"] == "blocked_current_design_gate"
    assert by_boundary["candidate_metadata_materialization"]["current_step_status"] == "not_executed_current_step"
    for item in ["sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_design_gate"
    for item in ["network_access", "raw_download", "raw_text_read", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_safety} == {"True"}
    assert {row["training_blocker_passed"] for row in blockers} == {"True"}
    assert [row["training_blocker_item"] for row in blockers[:5]] == [
        "mask_warhead_only_A",
        "mask_linker_plus_warhead_B",
        "mask_scaffold_plus_warhead_B2",
        "mask_scaffold_only_B3",
        "mask_scaffold_plus_linker_plus_warhead_C",
    ]
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["candidate_allowlist_materialized_current_step"] is False
    assert manifest["candidate_metadata_materialized_current_step"] is False
    assert manifest["sample_index_written"] is False
    assert manifest["final_dataset_written"] is False
    assert manifest["split_assignments_written"] is False
    assert manifest["leakage_matrix_written"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_design_gate"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_candidate_allowlist_materialization_smoke"
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_no_forbidden_imports_outputs_or_raw_tracking() -> None:
    module_path = Path("src/covalent_ext/covapie_candidate_allowlist_materialization_design_gate.py")
    script_path = Path("scripts/check_covapie_candidate_allowlist_materialization_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    bad = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden]
    assert bad == []
    forbidden_names = {
        "covapie_candidate_allowlist.csv",
        "covapie_candidate_allowlist.json",
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
        assert manifest[key] is False
