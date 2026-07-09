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

from covalent_ext import covapie_small_pilot_download_manifest_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_small_pilot_download_manifest_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_small_pilot_download_manifest_gate_manifest.json"
    assert path.is_file(), "Run the Step 14C check script before artifact tests"
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


def test_step14b_precondition_and_source_profile_contract() -> None:
    manifest14b = json.loads(gate.STEP14B_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_small_pilot_download_manifest_precondition_audit.csv")
    source = _csv_rows(ROOT / "covapie_small_pilot_source_profile_contract.csv")
    manifest = _manifest()
    assert manifest14b["stage"] == gate.PREVIOUS_STAGE
    assert manifest14b["step_label"] == "Step 14B"
    assert manifest14b["all_checks_passed"] is True
    assert manifest14b["ready_for_covapie_small_pilot_download_manifest_gate"] is True
    assert manifest14b["ready_for_covapie_small_pilot_download_smoke"] is False
    assert manifest14b["ready_for_covapie_bulk_download_smoke"] is False
    assert manifest14b["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(source) == 8
    assert [row["source_profile_item"] for row in source] == [
        "current_source_profile_name",
        "current_source_profile_scope",
        "current_source_database",
        "current_source_metadata_csv",
        "current_source_resolver_policy",
        "cross_source_generalization_policy",
        "pbd_wide_blind_scan_not_allowed",
        "new_source_requires_source_registry_and_schema_mapping",
    ]
    assert {row["source_profile_contract_passed"] for row in source} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["current_source_profile"] == gate.CURRENT_SOURCE_PROFILE
    assert manifest["current_source_database"] == gate.CURRENT_SOURCE_DATABASE
    assert manifest["cross_source_generalization_supported_by_schema"] is True
    assert manifest["current_execution_source_specific"] is True
    assert manifest["pdb_wide_blind_scan_allowed"] is False


def test_manifest_csv_json_written_consistent_and_schema_preserved() -> None:
    csv_rows = _csv_rows(ROOT / "covapie_small_pilot_download_manifest.csv")
    json_rows = json.loads((ROOT / "covapie_small_pilot_download_manifest.json").read_text(encoding="utf-8"))
    schema = _csv_rows(ROOT / "covapie_small_pilot_download_manifest_schema_validation_audit.csv")
    manifest = _manifest()
    assert len(csv_rows) == len(json_rows)
    assert len(csv_rows) == manifest["small_pilot_download_manifest_row_count"]
    assert len(csv_rows) == manifest["selected_small_pilot_row_count"]
    assert len(csv_rows) <= 50
    assert len(schema) == 24
    assert [row["manifest_field"] for row in schema] == gate.SMALL_PILOT_MANIFEST_COLUMNS
    assert {row["observed_in_all_manifest_rows"] for row in schema} == {"True"}
    assert {row["value_policy_satisfied"] for row in schema} == {"True"}
    assert {row["schema_validation_passed"] for row in schema} == {"True"}
    if csv_rows:
        for row in csv_rows:
            assert set(gate.SMALL_PILOT_MANIFEST_COLUMNS) == set(row)
            assert row["source_profile"] == gate.CURRENT_SOURCE_PROFILE
            assert row["source_database"] == gate.CURRENT_SOURCE_DATABASE
            assert row["intended_download_url_or_resolver"]
            assert row["download_status"] == "pending_not_downloaded"
            assert row["retry_count"] == "0"
            assert row["git_tracking_guard"] == "raw_must_remain_untracked_unstaged"
            assert not Path(row["raw_output_path"]).exists()


def test_candidate_selection_insufficient_event_identity_blocks_download_smoke_when_needed() -> None:
    candidate = _csv_rows(ROOT / "covapie_small_pilot_candidate_selection_audit.csv")
    manifest = _manifest()
    by_item = {row["selection_item_or_candidate_id"]: row for row in candidate}
    assert "candidate_universe_row_count" in by_item
    assert "candidate_rows_with_pdb_id" in by_item
    assert "candidate_rows_with_ligand_identifier" in by_item
    assert "candidate_rows_with_event_identity" in by_item
    assert "selected_small_pilot_row_count" in by_item
    assert {row["candidate_selection_passed"] for row in candidate} == {"True"}
    assert manifest["candidate_selection_audit_passed"] is True
    assert manifest["selected_small_pilot_row_count"] <= 50
    if manifest["selected_small_pilot_row_count"] >= 20:
        assert manifest["ready_for_covapie_small_pilot_download_smoke"] is True
        assert manifest["recommended_next_step"] == "covapie_small_pilot_download_smoke"
        assert manifest["insufficient_candidate_count_for_20_to_50_pilot"] is False
    else:
        assert manifest["ready_for_covapie_small_pilot_download_smoke"] is False
        assert manifest["recommended_next_step"] == "covapie_small_pilot_candidate_expansion_gate"
        assert manifest["insufficient_candidate_count_for_20_to_50_pilot"] is True


def test_network_raw_runtime_and_training_boundaries() -> None:
    network = _csv_rows(ROOT / "covapie_small_pilot_download_network_boundary_audit.csv")
    readiness = _csv_rows(ROOT / "covapie_small_pilot_download_readiness_contract.csv")
    manifest = _manifest()
    assert len(network) == 10
    assert {row["network_boundary_passed"] for row in network} == {"True"}
    assert len(readiness) == 8
    assert {row["readiness_passed"] for row in readiness} == {"True"}
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
    assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_download_manifest_gate.py"), "torch")
    assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_download_manifest_gate.py"), "numpy")
    assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_download_manifest_gate.py"), "urllib")


def test_masks_feature_flags_and_readiness_boundaries() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["ready_for_covapie_bulk_download_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
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


def test_safety_audit_raw_paths_and_existing_artifacts_unchanged() -> None:
    safety = _csv_rows(ROOT / "covapie_small_pilot_download_manifest_safety_audit.csv")
    manifest_rows = _csv_rows(ROOT / "covapie_small_pilot_download_manifest.csv")
    manifest = _manifest()
    assert len(safety) >= 31
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "raw_files_untracked",
        "raw_files_unstaged",
        "raw_files_not_read_current_step",
        "no_network_access_current_step",
        "no_download_current_step",
        "no_raw_files_written_current_step",
        "manifest_paths_point_to_future_raw_storage_only",
        "raw_output_paths_do_not_exist_current_step",
        "metadata_csv_unchanged",
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
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert manifest["safety_audit_passed"] is True
    assert all(not Path(row["raw_output_path"]).exists() for row in manifest_rows if row.get("raw_output_path"))
    tracked = subprocess.run(["git", "ls-files", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert tracked == ""
    assert staged == ""
