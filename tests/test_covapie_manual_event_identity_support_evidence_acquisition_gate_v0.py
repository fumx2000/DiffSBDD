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

from covalent_ext import covapie_manual_event_identity_support_evidence_acquisition_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_manual_event_identity_support_evidence_acquisition_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_support_evidence_acquisition_gate_manifest.json"
    assert path.is_file(), "Run the Step 14F check script before artifact tests"
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


def test_step14e_precondition_and_template_pending() -> None:
    manifest14e = json.loads(gate.STEP14E_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_support_evidence_acquisition_precondition_audit.csv")
    template_audit = _csv_rows(ROOT / "covapie_support_evidence_input_template_audit.csv")
    manifest = _manifest()
    assert manifest14e["stage"] == gate.PREVIOUS_STAGE
    assert manifest14e["step_label"] == "Step 14E"
    assert manifest14e["all_checks_passed"] is True
    assert manifest14e["manual_curation_template_row_count"] == 25
    assert manifest14e["manual_review_status_all_pending"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len([row for row in template_audit if row["input_template_audit_passed"] == "True"]) == 10
    by_check = {row["input_template_check"]: row for row in template_audit}
    assert by_check["template_row_count_25"]["observed_status"] == "25"
    assert by_check["all_rows_pending_manual_review"]["observed_status"] == "True"
    assert by_check["event_level_fields_blank_pending"]["observed_status"] == "True"
    assert manifest["template_candidate_count"] == 25
    assert manifest["step14e_manual_curation_template_validated"] is True


def test_source_inventory_and_local_raw_availability() -> None:
    inventory = _csv_rows(ROOT / "covapie_support_evidence_source_inventory.csv")
    raw = _csv_rows(ROOT / "covapie_support_evidence_local_raw_availability_audit.csv")
    manifest = _manifest()
    names = [row["evidence_source_name"] for row in inventory]
    for required in [
        "step14e_manual_curation_template",
        "metadata_csv",
        "local_raw_cif_root",
        "local_raw_cif_files_for_template_pdb_ids",
        "step14d_candidate_expansion_artifacts",
        "step14c_manifest_artifacts",
        "candidate_allowlist_qa_if_present",
        "batch_raw_read_extraction_smoke_if_present",
        "batch_raw_read_extraction_qa_if_present",
        "step8_topology_evidence_if_present",
        "no_network_source_current_step",
        "no_external_download_current_step",
    ]:
        assert required in names
    assert {row["evidence_source_inventory_passed"] for row in inventory} == {"True"}
    candidate_rows = [row for row in raw if row["curation_candidate_id"].startswith("CUR_EVT_")]
    assert len(candidate_rows) == 25
    assert {row["raw_availability_audit_passed"] for row in raw} == {"True"}
    assert sum(row["local_raw_file_exists"] == "True" for row in candidate_rows) == manifest["local_raw_available_count"]
    assert sum(row["raw_read_attempted_current_step"] == "True" for row in candidate_rows) == manifest["local_raw_read_count"]
    assert {row["local_raw_file_tracked_by_git"] for row in candidate_rows if row["local_raw_file_exists"] == "True"} == {"False"}
    assert {row["local_raw_file_staged_by_git"] for row in candidate_rows if row["local_raw_file_exists"] == "True"} == {"False"}


def test_struct_conn_proposal_audit_and_proposals_pending() -> None:
    audit = _csv_rows(ROOT / "covapie_support_evidence_struct_conn_proposal_audit.csv")
    proposals_csv = _csv_rows(ROOT / "covapie_manual_event_identity_support_evidence_proposals.csv")
    proposals_json = json.loads((ROOT / "covapie_manual_event_identity_support_evidence_proposals.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert audit
    assert {row["proposal_audit_passed"] for row in audit} == {"True"}
    by_summary = {row["proposal_or_summary_id"]: row for row in audit[:10]}
    assert by_summary["template_candidate_count"]["qa_comment"] == "25"
    assert int(by_summary["local_raw_available_count"]["qa_comment"]) == manifest["local_raw_available_count"]
    assert int(by_summary["struct_conn_rows_detected_count"]["qa_comment"]) == manifest["struct_conn_rows_detected_count"]
    assert len(proposals_csv) == len(proposals_json)
    assert len(proposals_csv) == manifest["support_proposal_count"]
    assert manifest["support_proposals_csv_json_consistent"] is True
    assert {row["proposal_status"] for row in proposals_csv}.issubset({"pending_manual_review"})
    assert {row["manual_review_status"] for row in proposals_csv}.issubset({"pending_manual_review"})
    for row in proposals_csv:
        assert row["suggested_residue_name"] == "CYS"
        assert row["suggested_residue_atom_name"] == "SG"
        assert row["cys_sg_v1_candidate_proposal"] == "True"
        assert row["proposal_status"] == "pending_manual_review"


def test_validation_readiness_boundaries_masks_and_training_blockers() -> None:
    validation = _csv_rows(ROOT / "covapie_support_evidence_proposal_validation_audit.csv")
    manifest = _manifest()
    assert len(validation) == 10
    assert {row["validation_passed"] for row in validation} == {"True"}
    for key in [
        "coordinate_extraction_current_step",
        "ligand_topology_auto_restored_current_step",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "raw_files_committed",
        "download_manifest_written",
        "actual_download_smoke_written",
        "actual_dataloader_adapter_smoke_written",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "torch_imported",
        "torch_tensor_created",
        "numpy_imported",
        "numpy_array_returned",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_small_pilot_manual_event_identity_validation_gate",
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["no_ready_candidates_created"] is True
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_covapie_manual_event_identity_support_review_gate"] is True
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
    assert manifest["recommended_next_step"] == "covapie_manual_event_identity_support_review_gate"
    for name in ["torch", "numpy", "urllib", "requests", "rdkit", "Bio", "gemmi", "gzip"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_manual_event_identity_support_evidence_acquisition_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_manual_event_identity_support_evidence_acquisition_gate_v0.py"), name)


def test_safety_audit_existing_artifacts_unchanged_and_raw_untracked() -> None:
    safety = _csv_rows(ROOT / "covapie_support_evidence_acquisition_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) >= 34
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "raw_files_untracked",
        "raw_files_unstaged",
        "raw_files_read_only_if_present",
        "no_raw_files_written_current_step",
        "no_network_access_current_step",
        "no_download_current_step",
        "no_download_manifest_written_current_step",
        "no_actual_dataloader_smoke_written",
        "no_real_final_dataset_written",
        "no_new_sample_index_written",
        "no_split_assignments_written",
        "no_leakage_matrix_written",
        "metadata_csv_unchanged",
        "step14e_artifacts_unchanged",
        "step14d_artifacts_unchanged",
        "step14c_artifacts_unchanged",
        "step14b_artifacts_unchanged",
        "step14a_artifacts_unchanged",
        "step13bz_artifacts_unchanged",
        "step13by_artifacts_unchanged",
        "step13bx_artifacts_unchanged",
        "step13bu_artifacts_unchanged",
        "step13bo_artifacts_unchanged",
        "step13bm_artifacts_unchanged",
        "step13ai_inventory_artifacts_unchanged",
        "protected_source_diff_empty",
        "original_dataloader_diff_empty",
        "no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports",
        "derived_output_no_forbidden_binary_artifacts",
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert manifest["all_checks_passed"] is True
    assert not subprocess.run(["git", "ls-files", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()


def test_no_forbidden_named_or_suffix_artifacts() -> None:
    forbidden_names = {
        "actual_download_manifest.csv",
        "actual_download_manifest.json",
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
        "download_smoke.csv",
        "download_smoke.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
    }
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert not [path for path in ROOT.rglob("*") if path.name in forbidden_names]
    assert not [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes]
