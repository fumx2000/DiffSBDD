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

from covalent_ext import covapie_bulk_download_design_gate as design_gate


ROOT = Path("data/derived/covalent_small/covapie_bulk_download_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_bulk_download_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 14B check script before artifact tests"
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


def test_step14a_precondition_and_readiness() -> None:
    manifest14a = json.loads(design_gate.STEP14A_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_bulk_download_design_precondition_audit.csv")
    manifest = _manifest()
    assert manifest14a["stage"] == design_gate.PREVIOUS_STAGE
    assert manifest14a["step_label"] == "Step 14A"
    assert manifest14a["all_checks_passed"] is True
    assert manifest14a["ready_for_covapie_bulk_download_design_gate"] is True
    assert manifest14a["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest14a["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest14a["ready_for_training"] is False
    assert manifest14a["ready_to_train_now"] is False
    assert manifest14a["feature_semantics_known_for_training"] is False
    assert manifest14a["unknown_atom_feature_policy_finalized_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design_gate.STAGE
    assert manifest["step_label"] == "Step 14B"
    assert manifest["previous_stage"] == design_gate.PREVIOUS_STAGE
    assert manifest["step14a_feature_semantics_resolution_smoke_qa_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_contract_row_counts_and_pass_flags() -> None:
    candidate = _csv_rows(ROOT / "covapie_bulk_download_candidate_source_contract.csv")
    storage = _csv_rows(ROOT / "covapie_bulk_download_storage_layout_contract.csv")
    schema = _csv_rows(ROOT / "covapie_bulk_download_manifest_schema_contract.csv")
    network = _csv_rows(ROOT / "covapie_bulk_download_network_boundary_contract.csv")
    pilot = _csv_rows(ROOT / "covapie_bulk_download_pilot_scale_contract.csv")
    resume = _csv_rows(ROOT / "covapie_bulk_download_resume_checksum_contract.csv")
    failure = _csv_rows(ROOT / "covapie_bulk_download_failure_taxonomy_contract.csv")
    manifest = _manifest()

    assert len(candidate) == 10
    assert [row["candidate_source_item"] for row in candidate] == [
        "metadata_csv_candidate_source",
        "allowlist_candidate_source_if_present",
        "confirmed_extraction_candidate_source_if_present",
        "feature_semantics_qa_candidate_source",
        "pdb_id_required",
        "covalent_event_id_required",
        "residue_atom_pair_required",
        "ligand_identifier_required",
        "duplicate_candidate_policy",
        "excluded_candidate_policy",
    ]
    assert {row["candidate_source_contract_passed"] for row in candidate} == {"True"}
    assert {row["used_for_future_download_manifest"] for row in candidate} == {"True"}

    assert len(storage) == 10
    assert {row["current_step_created"] for row in storage} == {"False"}
    assert {row["storage_layout_contract_passed"] for row in storage} == {"True"}
    assert {row["git_tracking_policy"] for row in storage} >= {"never_commit_raw_files", "raw_untracked_unstaged", "raw_never_committed"}

    assert len(schema) == 14
    assert [row["manifest_field"] for row in schema] == [
        "download_manifest_row_id",
        "candidate_metadata_id",
        "pdb_id",
        "source_database",
        "intended_structure_format",
        "intended_download_url_or_resolver",
        "raw_output_path",
        "expected_checksum_field",
        "download_status",
        "retry_count",
        "failure_reason",
        "source_metadata_hash",
        "downstream_extraction_status",
        "git_tracking_guard",
    ]
    assert {row["required_in_future_manifest"] for row in schema} == {"True"}
    assert {row["current_step_written"] for row in schema} == {"False"}
    assert {row["manifest_schema_contract_passed"] for row in schema} == {"True"}

    assert len(network) == 10
    assert {row["network_boundary_contract_passed"] for row in network} == {"True"}
    assert {row["current_step_status"] for row in network if row["network_boundary_item"].startswith("no_")} <= {"not_executed_or_not_allowed", "not_imported_or_executed"}

    assert len(pilot) == 8
    assert {row["pilot_scale_contract_passed"] for row in pilot} == {"True"}
    assert {row["current_step_status"] for row in pilot} == {"design_only"}

    assert len(resume) == 8
    assert {row["current_step_status"] for row in resume} == {"design_only_no_files_downloaded"}
    assert {row["future_step_required"] for row in resume} == {"True"}
    assert {row["resume_checksum_contract_passed"] for row in resume} == {"True"}

    assert len(failure) == 12
    assert {row["current_step_status"] for row in failure} == {"design_only"}
    assert {row["failure_taxonomy_contract_passed"] for row in failure} == {"True"}

    assert manifest["candidate_source_contract_row_count"] == 10
    assert manifest["storage_layout_contract_row_count"] == 10
    assert manifest["download_manifest_schema_contract_row_count"] == 14
    assert manifest["network_boundary_contract_row_count"] == 10
    assert manifest["pilot_scale_contract_row_count"] == 8
    assert manifest["resume_checksum_contract_row_count"] == 8
    assert manifest["failure_taxonomy_contract_row_count"] == 12
    assert manifest["candidate_source_contract_passed"] is True
    assert manifest["storage_layout_contract_passed"] is True
    assert manifest["download_manifest_schema_contract_passed"] is True
    assert manifest["network_boundary_contract_passed"] is True
    assert manifest["pilot_scale_contract_passed"] is True
    assert manifest["resume_checksum_contract_passed"] is True
    assert manifest["failure_taxonomy_contract_passed"] is True


def test_runtime_network_download_raw_and_training_boundaries() -> None:
    manifest = _manifest()
    for key in [
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_text_read",
        "mmcif_parse_current_step",
        "coordinate_extraction_current_step",
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
    ]:
        assert manifest[key] is False, key
    assert manifest["bulk_download_design_completed_current_step"] is True
    assert not _imports_name(Path("src/covalent_ext/covapie_bulk_download_design_gate.py"), "torch")
    assert not _imports_name(Path("src/covalent_ext/covapie_bulk_download_design_gate.py"), "numpy")
    assert not _imports_name(Path("src/covalent_ext/covapie_bulk_download_design_gate.py"), "urllib")
    assert not _imports_name(Path("scripts/check_covapie_bulk_download_design_gate_v0.py"), "urllib")


def test_readiness_masks_and_training_final_flags() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["ready_for_covapie_small_pilot_download_manifest_gate"] is True
    assert manifest["ready_for_covapie_small_pilot_download_smoke"] is False
    assert manifest["ready_for_covapie_bulk_download_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_small_pilot_download_manifest_gate"
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


def test_safety_audit_raw_git_and_existing_artifacts_unchanged() -> None:
    safety = _csv_rows(ROOT / "covapie_bulk_download_design_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) >= 28
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "raw_files_untracked",
        "raw_files_unstaged",
        "raw_files_not_read_current_step",
        "no_network_access_current_step",
        "no_download_current_step",
        "no_raw_files_written_current_step",
        "metadata_csv_unchanged",
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
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert manifest["metadata_csv_hash_unchanged"] is True
    assert manifest["safety_audit_passed"] is True
    tracked = subprocess.run(["git", "ls-files", design_gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", design_gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert tracked == ""
    assert staged == ""


def test_output_root_has_no_forbidden_artifacts_or_suffixes() -> None:
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
    bad_names = [path for path in ROOT.rglob("*") if path.name in forbidden_names]
    bad_suffixes = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes]
    assert bad_names == []
    assert bad_suffixes == []
