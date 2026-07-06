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

from covalent_ext import covapie_metadata_source_inventory_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_metadata_source_inventory_gate_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not gate.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_check_script_passes_and_validates_step13ah_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_metadata_source_inventory_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ah_missing_metadata_materialization_smoke_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_step13ag_template_and_covapie_naming_and_no_runtime_imports() -> None:
    with gate.STEP13AG_TEMPLATE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [gate.ALLOWLIST_COLUMNS]
    assert gate.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_metadata_source_inventory_gate.py")
    script_path = Path("scripts/check_covapie_metadata_source_inventory_gate_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)


def test_scanner_only_includes_allowed_suffixes_and_excludes_current_output_root() -> None:
    scanned = _csv_rows(gate.SCANNED_ARTIFACT_AUDIT_CSV)
    assert scanned
    assert {row["scan_status"] for row in scanned} == {"header_or_json_summary_only"}
    assert {row["scan_audit_passed"] for row in scanned} == {"True"}
    assert {row["artifact_suffix"] for row in scanned} <= set(gate.ALLOWED_SUFFIXES)
    assert not any("covapie_metadata_source_inventory_gate_v0" in row["artifact_path"] for row in scanned)
    assert all(not row["artifact_path"].startswith("data/raw/covalent_sources") for row in scanned)


def test_output_row_counts_match_contract() -> None:
    manifest = _manifest()
    assert manifest["covapie_metadata_inventory_precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 7
    assert manifest["covapie_metadata_inventory_scanned_artifact_audit_row_count"] == len(_csv_rows(gate.SCANNED_ARTIFACT_AUDIT_CSV))
    assert manifest["covapie_metadata_inventory_forbidden_artifact_audit_row_count"] == len(_csv_rows(gate.FORBIDDEN_ARTIFACT_AUDIT_CSV)) == 15
    assert manifest["covapie_allowlist_field_source_coverage_matrix_row_count"] == len(_csv_rows(gate.FIELD_COVERAGE_MATRIX_CSV)) == 15
    assert manifest["covapie_candidate_metadata_assembly_gap_audit_row_count"] == len(_csv_rows(gate.GAP_AUDIT_CSV)) == 15
    assert manifest["covapie_metadata_inventory_candidate_count_estimate_row_count"] == len(_csv_rows(gate.CANDIDATE_COUNT_ESTIMATE_CSV)) == 1
    assert manifest["covapie_metadata_inventory_execution_boundary_audit_row_count"] == len(_csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_metadata_inventory_git_safety_audit_row_count"] == len(_csv_rows(gate.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_metadata_inventory_mask_scope_audit_row_count"] == len(_csv_rows(gate.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_metadata_inventory_feature_semantics_audit_row_count"] == len(_csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_metadata_inventory_leakage_split_audit_row_count"] == len(_csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)) == 12


def test_forbidden_suffixes_are_counted_but_not_read() -> None:
    forbidden = _csv_rows(gate.FORBIDDEN_ARTIFACT_AUDIT_CSV)
    assert [row["forbidden_suffix"] for row in forbidden] == gate.FORBIDDEN_SUFFIXES
    assert {row["searched_under_inventory_root"] for row in forbidden} == {"True"}
    assert {row["files_read"] for row in forbidden} == {"False"}
    assert {row["policy"] for row in forbidden} == {"do_not_read_or_commit"}
    assert {row["forbidden_audit_passed"] for row in forbidden} == {"True"}


def test_field_coverage_gap_and_count_estimate_are_conservative() -> None:
    manifest = _manifest()
    coverage = _csv_rows(gate.FIELD_COVERAGE_MATRIX_CSV)
    gap = _csv_rows(gate.GAP_AUDIT_CSV)
    estimate = _csv_rows(gate.CANDIDATE_COUNT_ESTIMATE_CSV)[0]
    assert [row["allowlist_column"] for row in coverage] == gate.ALLOWLIST_COLUMNS
    assert [row["allowlist_column"] for row in gap] == gate.ALLOWLIST_COLUMNS
    assert {row["source_coverage_passed"] for row in coverage} == {"True"}
    assert {row["gap_audit_passed"] for row in gap} == {"True"}
    assert manifest["allowlist_required_column_count"] == 15
    assert manifest["allowlist_required_columns"] == gate.ALLOWLIST_COLUMNS
    assert manifest["directly_available_column_count"] >= 0
    assert manifest["derivable_column_count"] >= 0
    assert manifest["missing_required_column_count"] >= 0
    assert int(estimate["fully_covered_allowlist_candidate_count_estimate"]) == manifest["fully_covered_allowlist_candidate_count_estimate"]
    assert estimate["estimate_basis"] == "conservative_header_only_inventory_no_raw_read_no_candidate_invention"
    assert estimate["count_estimate_passed"] == "True"
    assert manifest["enough_for_10_to_30_materialization"] is False
    assert manifest["fully_covered_allowlist_candidate_count_estimate"] < 10


def test_canonical_masks_feature_semantics_and_leakage_boundaries() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(gate.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13ah"}
    feature = _csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_metadata_inventory_gate"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    leakage = _csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["metadata_source_inventory_gate"]["current_step_status"] == "executed_inventory_gate_only"
    assert boundary["derived_csv_json_md_scan"]["current_step_status"] == "executed_header_and_metadata_summary_only"
    for item in gate.EXECUTION_BOUNDARY_ITEMS[2:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["execution_boundary_passed"] == "True"
    git_rows = {row["git_safety_item"]: row for row in _csv_rows(gate.GIT_SAFETY_AUDIT_CSV)}
    assert ".pt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".npz" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".sdf" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert {row["git_safety_audit_passed"] for row in git_rows.values()} == {"True"}
    manifest = _manifest()
    for key in [
        "raw_data_read",
        "raw_file_copied",
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


def test_readiness_boundary() -> None:
    manifest = _manifest()
    assert manifest["metadata_source_inventory_gate_passed"] is True
    assert manifest["ready_for_covapie_candidate_metadata_assembly_design_gate"] is False
    assert manifest["ready_for_user_or_pipeline_metadata"] is True
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "provide_or_generate_explicit_candidate_metadata_source"
