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

from covalent_ext import covapie_external_metadata_index_rediscovery_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_external_metadata_index_rediscovery_smoke_v0.py"],
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


def test_check_script_passes_and_validates_preconditions() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_external_metadata_index_rediscovery_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ao_covpdb_metadata_only_acquisition_smoke_validated"] is True
    assert manifest["historical_step13an_blocked_state_validated"] is True
    assert manifest["source_name"] == "CovPDB"
    assert manifest["source_access_method"] == "manual_user_supplied"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_historical_step13an_remains_blocked_and_not_overwritten() -> None:
    assert smoke.validate_historical_step13an_blocked_state_v0() is True
    manifest = json.loads(smoke.STEP13AN_MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["stage"] == "covapie_external_metadata_index_download_smoke_v0"
    assert manifest["metadata_index_download_smoke_status"] == "blocked_due_to_missing_manual_metadata_index"
    assert manifest["external_metadata_index_download_smoke_passed"] is False
    assert manifest["recommended_next_step"] == "provide_manual_covpdb_metadata_index_csv"
    assert manifest["blocking_reasons"] == ["missing_manual_metadata_index_csv"]


def test_step13ao_and_step13am_preconditions() -> None:
    assert smoke.validate_step13ao_precondition_v0() is True
    assert smoke.validate_step13am_source_config_v0() is True
    assert smoke.validate_covapie_naming_convention_v0() is True


def test_metadata_csv_exists_has_expected_schema_rows_and_first5() -> None:
    header, rows, size = smoke.read_metadata_index()
    assert size > 0
    assert header == smoke.METADATA_COLUMNS
    assert len(rows) == 25
    assert [row["pdb_id"] for row in rows[:5]] == smoke.FIRST_5_PDB_IDS
    assert [row["het_code"] for row in rows[:5]] == smoke.FIRST_5_HET_CODES
    assert {row["source_dataset_name"] for row in rows} == {"CovPDB"}
    assert {row["raw_structure_downloaded"] for row in rows} == {"False"}
    assert {row["raw_ligand_downloaded"] for row in rows} == {"False"}
    assert {row["metadata_only_record"] for row in rows} == {"True"}


def test_no_network_or_forbidden_runtime_imports_in_step13ap() -> None:
    module_path = Path("src/covalent_ext/covapie_external_metadata_index_rediscovery_smoke.py")
    script_path = Path("scripts/check_covapie_external_metadata_index_rediscovery_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
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


def test_output_row_counts_and_probe_audits() -> None:
    manifest = _manifest()
    assert manifest["precondition_audit_row_count"] == len(_csv_rows(smoke.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["file_discovery_audit_row_count"] == len(_csv_rows(smoke.FILE_DISCOVERY_AUDIT_CSV)) == 1
    assert manifest["header_probe_audit_row_count"] == len(_csv_rows(smoke.HEADER_PROBE_AUDIT_CSV)) == 1
    assert manifest["sample_rows_probe_audit_row_count"] == len(_csv_rows(smoke.SAMPLE_ROWS_PROBE_AUDIT_CSV)) == 1
    assert manifest["schema_audit_row_count"] == len(_csv_rows(smoke.SCHEMA_AUDIT_CSV)) == 19
    assert manifest["event_key_boundary_audit_row_count"] == len(_csv_rows(smoke.EVENT_KEY_BOUNDARY_AUDIT_CSV)) == 8
    assert manifest["execution_boundary_audit_row_count"] == len(_csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)) == 20
    assert manifest["git_safety_audit_row_count"] == len(_csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["mask_scope_audit_row_count"] == len(_csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["feature_semantics_audit_row_count"] == len(_csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["leakage_split_audit_row_count"] == len(_csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)) == 12

    file_row = _csv_rows(smoke.FILE_DISCOVERY_AUDIT_CSV)[0]
    assert file_row["metadata_index_file_exists"] == "True"
    assert file_row["metadata_index_file_read"] == "True"
    assert file_row["metadata_index_copied_to_output_root"] == "False"
    assert file_row["file_discovery_status"] == "manual_metadata_index_discovered"
    header_row = _csv_rows(smoke.HEADER_PROBE_AUDIT_CSV)[0]
    assert header_row["header_probe_status"] == "header_read"
    assert header_row["column_count"] == "19"
    sample_row = _csv_rows(smoke.SAMPLE_ROWS_PROBE_AUDIT_CSV)[0]
    assert sample_row["sampled_row_count"] == "5"
    assert sample_row["total_rows_scanned"] == "25"
    assert sample_row["first_5_pdb_ids"] == "1A3B;1A3E;1A46;1A54;1A5G"
    assert sample_row["first_5_het_codes"] == "T29;T16;00K;MDC;00L"
    assert {row["schema_probe_passed"] for row in _csv_rows(smoke.SCHEMA_AUDIT_CSV)} == {"True"}


def test_event_execution_git_mask_feature_and_leakage_boundaries() -> None:
    manifest = _manifest()
    event = _csv_rows(smoke.EVENT_KEY_BOUNDARY_AUDIT_CSV)
    assert [row["event_key_boundary_item"] for row in event] == smoke.EVENT_KEY_ITEMS
    assert {row["event_key_materialized_current_step"] for row in event} == {"False"}
    assert {row["candidate_metadata_materialized"] for row in event} == {"False"}
    assert {row["candidate_allowlist_materialized"] for row in event} == {"False"}
    assert {row["event_key_boundary_audit_passed"] for row in event} == {"True"}

    execution = {row["boundary_item"]: row for row in _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert execution["external_metadata_index_rediscovery_smoke"]["current_step_status"] == "executed_metadata_index_rediscovery_only"
    assert execution["metadata_csv_header_probe"]["current_step_status"] == "executed_metadata_csv_header_probe_only"
    for item in smoke.EXECUTION_BOUNDARY_ITEMS[8:]:
        assert execution[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["execution_boundary_passed"] for row in execution.values()} == {"True"}

    assert {row["git_safety_audit_passed"] for row in _csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)} == {"True"}
    mask = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True

    feature = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    leakage = _csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["future_required_gate"] for row in leakage} == {"covapie_leakage_split_design_gate_before_training"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_manifest_safety_and_readiness_flags() -> None:
    manifest = _manifest()
    for key in [
        "network_access_used",
        "urllib_used",
        "requests_used",
        "browser_used",
        "metadata_index_download_or_copy_performed",
        "metadata_index_copied_to_step_output_root",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "raw_structure_downloaded",
        "raw_ligand_downloaded",
        "raw_data_read",
        "raw_file_copied",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "atom_site_text_scan_run",
        "torch_imported",
        "torch_tensor_created",
        "tensor_artifact_written",
        "npz_created",
        "pt_created",
        "checkpoint_loaded",
        "checkpoint_saved",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
    ]:
        assert manifest[key] is False
    assert manifest["metadata_index_file_exists"] is True
    assert manifest["metadata_index_file_read"] is True
    assert manifest["metadata_index_row_count"] == 25
    assert manifest["metadata_index_column_count"] == 19
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_external_metadata_index_schema_probe_design_gate"
