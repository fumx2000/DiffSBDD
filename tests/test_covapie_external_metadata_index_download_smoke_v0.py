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

from covalent_ext import covapie_external_metadata_index_download_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_external_metadata_index_download_smoke_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not smoke.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_committed_step13an_missing_manual_csv_state_blocks_safely() -> None:
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["enabled_source_name"] == "CovPDB"
    assert manifest["enabled_source_access_method"] == "manual_user_supplied"
    assert manifest["enabled_source_artifact_type"] == "csv"
    assert manifest["metadata_index_file_checked"] is True
    assert manifest["metadata_index_file_exists"] is False
    assert manifest["metadata_index_file_read"] is False
    assert manifest["metadata_index_download_smoke_status"] == "blocked_due_to_missing_manual_metadata_index"
    assert manifest["external_metadata_index_download_smoke_passed"] is False
    assert manifest["recommended_next_step"] == "provide_manual_covpdb_metadata_index_csv"
    assert manifest["blocking_reasons"] == ["missing_manual_metadata_index_csv"]
    assert manifest["all_checks_passed"] is True


def test_preconditions_contracts_and_no_forbidden_runtime_imports() -> None:
    assert smoke.validate_step13am_precondition_v0() is True
    assert smoke.validate_step13am_source_config_v0() is True
    assert smoke.validate_step13ak_allowed_artifact_contract_v0() is True
    assert smoke.validate_step13aj_event_identity_key_contract_v0() is True
    assert smoke.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_external_metadata_index_download_smoke.py")
    script_path = Path("scripts/check_covapie_external_metadata_index_download_smoke_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio", "requests", "urllib"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    for path in [module_path, script_path]:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                call_text = ast.get_source_segment(text, node) or ""
                assert "curl" not in call_text
                assert "wget" not in call_text


def test_default_missing_csv_outputs_and_row_counts() -> None:
    manifest = _manifest()
    assert manifest["covapie_external_metadata_index_download_smoke_precondition_audit_row_count"] == len(_csv_rows(smoke.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["covapie_external_metadata_index_source_config_audit_row_count"] == len(_csv_rows(smoke.SOURCE_CONFIG_AUDIT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_file_discovery_audit_row_count"] == len(_csv_rows(smoke.FILE_DISCOVERY_AUDIT_CSV)) == 1
    assert manifest["covapie_external_metadata_index_allowed_artifact_audit_row_count"] == len(_csv_rows(smoke.ALLOWED_ARTIFACT_AUDIT_CSV)) == 8
    assert manifest["covapie_external_metadata_index_header_probe_audit_row_count"] == len(_csv_rows(smoke.HEADER_PROBE_AUDIT_CSV)) == 1
    assert manifest["covapie_external_metadata_index_sample_rows_probe_audit_row_count"] == len(_csv_rows(smoke.SAMPLE_ROWS_PROBE_AUDIT_CSV)) == 1
    assert manifest["covapie_external_metadata_index_event_key_boundary_audit_row_count"] == len(_csv_rows(smoke.EVENT_KEY_BOUNDARY_AUDIT_CSV)) == 8
    assert manifest["covapie_external_metadata_index_execution_boundary_audit_row_count"] == len(_csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_external_metadata_index_git_safety_audit_row_count"] == len(_csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_external_metadata_index_mask_scope_audit_row_count"] == len(_csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_external_metadata_index_feature_semantics_audit_row_count"] == len(_csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_leakage_split_audit_row_count"] == len(_csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)) == 12
    assert {row["precondition_passed"] for row in _csv_rows(smoke.PRECONDITION_AUDIT_CSV)} == {"True"}


def test_missing_csv_probe_audits_do_not_copy_metadata_into_step13an_outputs() -> None:
    manifest = _manifest()
    file_discovery = _csv_rows(smoke.FILE_DISCOVERY_AUDIT_CSV)[0]
    assert file_discovery["metadata_index_file_exists"] == "False"
    assert file_discovery["metadata_index_file_checked"] == "True"
    assert file_discovery["metadata_index_file_read"] == "False"
    assert file_discovery["metadata_index_download_or_copy_performed"] == "False"
    assert file_discovery["file_discovery_status"] == "blocked_due_to_missing_manual_metadata_index"
    header = _csv_rows(smoke.HEADER_PROBE_AUDIT_CSV)[0]
    assert header["header_probe_status"] == "not_available_missing_manual_metadata_index"
    assert header["header_probe_executed"] == "False"
    assert header["column_count"] == "0"
    sample = _csv_rows(smoke.SAMPLE_ROWS_PROBE_AUDIT_CSV)[0]
    assert sample["sample_rows_probe_status"] == "not_available_missing_manual_metadata_index"
    assert sample["sample_rows_probe_executed"] == "False"
    assert sample["sampled_row_count"] == "0"
    assert manifest["metadata_index_file_copied_to_output_root"] is False


def test_synthetic_existing_manual_csv_reads_header_and_max_five_rows(tmp_path: Path) -> None:
    metadata_csv = tmp_path / "covpdb_complexes_metadata_manual.csv"
    with metadata_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pdb_id", "ligand_id", "chain_id"])
        for index in range(7):
            writer.writerow([f"P{index}", f"L{index}", "A"])
    result = smoke.run_covapie_external_metadata_index_download_smoke_v0(
        output_root=tmp_path / "out",
        metadata_index_path_override=metadata_csv,
    )
    manifest = result["manifest"]
    assert manifest["metadata_index_file_exists"] is True
    assert manifest["metadata_index_file_read"] is True
    assert manifest["metadata_index_column_count"] == 3
    assert manifest["metadata_index_column_names"] == ["pdb_id", "ligand_id", "chain_id"]
    assert manifest["metadata_index_sample_rows_probe_executed"] is True
    assert manifest["metadata_index_sampled_row_count"] == 5
    assert manifest["metadata_index_total_rows_scanned"] == 7
    assert manifest["external_metadata_index_download_smoke_passed"] is True
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is True
    assert manifest["recommended_next_step"] == "covapie_external_metadata_index_schema_probe_design_gate"
    assert manifest["candidate_metadata_materialized"] is False
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["metadata_index_file_copied_to_output_root"] is False


def test_allowed_artifact_event_key_masks_feature_and_leakage() -> None:
    manifest = _manifest()
    assert manifest["metadata_index_root"] == "data/derived/covalent_small/external_metadata_index"
    assert manifest["raw_structure_root"] == "data/raw/covalent_sources"
    allowed = _csv_rows(smoke.ALLOWED_ARTIFACT_AUDIT_CSV)
    assert [row["allowed_artifact_item"] for row in allowed] == smoke.ALLOWED_ARTIFACT_ITEMS
    assert {row["allowed_artifact_audit_passed"] for row in allowed} == {"True"}
    event = _csv_rows(smoke.EVENT_KEY_BOUNDARY_AUDIT_CSV)
    assert [row["event_key_boundary_item"] for row in event] == smoke.EVENT_KEY_ITEMS
    assert {row["event_key_boundary_audit_passed"] for row in event} == {"True"}
    assert manifest["event_identity_key_policy"] == "no_pdb_id_only_join"
    assert manifest["one_row_one_covalent_event"] is True
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13am"}
    feature = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    leakage = _csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    manifest = _manifest()
    boundary = {row["boundary_item"]: row for row in _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["external_metadata_index_download_smoke"]["current_step_status"] == "executed_metadata_index_smoke_only"
    assert boundary["source_config_read"]["current_step_status"] == "executed_config_only"
    assert boundary["manual_metadata_index_file_discovery"]["current_step_status"] == "executed_path_exists_check_only"
    assert boundary["manual_metadata_index_header_probe"]["current_step_status"] == "not_executed_missing_manual_metadata_index"
    assert boundary["manual_metadata_index_sample_rows_probe"]["current_step_status"] == "not_executed_missing_manual_metadata_index"
    for item in smoke.EXECUTION_BOUNDARY_ITEMS[5:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["execution_boundary_passed"] == "True"
    git_rows = {row["git_safety_item"]: row for row in _csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)}
    assert ".pt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".npz" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".sdf" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert {row["git_safety_audit_passed"] for row in git_rows.values()} == {"True"}
    for key in [
        "network_access_used",
        "curl_used",
        "wget_used",
        "requests_used",
        "urllib_used",
        "browser_used",
        "external_source_url_verified",
        "external_metadata_downloaded",
        "raw_structure_downloaded",
        "raw_data_read",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "adapter_instantiated",
        "torch_imported",
        "torch_tensor_created",
        "tensor_artifact_written",
        "npz_created",
        "pt_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
        "original_diffsbdd_source_modified",
        "original_diffsbdd_dataloader_modified",
    ]:
        assert manifest[key] is False


def test_readiness_boundary_for_missing_manual_csv() -> None:
    manifest = _manifest()
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is False
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
