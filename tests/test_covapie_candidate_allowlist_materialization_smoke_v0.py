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


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_candidate_allowlist_materialization_smoke_v0.py"],
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


def _write_metadata(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=smoke.ALLOWLIST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _valid_rows(count: int = 10) -> list[dict[str, str]]:
    rows = []
    for index in range(count):
        rows.append(
            {
                "candidate_id": f"CAND_{index + 1:03d}",
                "source_dataset_name": "curated_covapie_metadata",
                "source_dataset_version": "v0",
                "source_file_relative_path": f"curated/pdb_{index + 1:03d}.cif",
                "pdb_id": f"P{index + 1:03d}",
                "ligand_id": f"L{index + 1:03d}",
                "chain_id": "A",
                "residue_name": "CYS",
                "residue_index": str(100 + index),
                "residue_atom_name": "SG",
                "covalent_bond_atom_pair": f"SG-C{index + 1}",
                "restoration_policy_id": "known_restoration_template_v1",
                "manual_review_status": "reviewed_pass" if index % 2 == 0 else "approved_for_smoke",
                "include_in_smoke": "true",
                "exclusion_reason": "",
            }
        )
    return rows


def test_check_script_passes_missing_metadata_mode() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_candidate_allowlist_materialization_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ag_allowlist_creation_gate_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["materialization_status"] == "blocked_due_to_missing_explicit_metadata"
    assert manifest["blocking_reasons"] == ["missing_explicit_candidate_metadata"]


def test_covapie_naming_and_no_runtime_imports() -> None:
    text = smoke.NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    assert "CovaPIE" in text
    assert "CovaGEN" in text
    assert smoke.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_candidate_allowlist_materialization_smoke.py")
    script_path = Path("scripts/check_covapie_candidate_allowlist_materialization_smoke_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)


def test_missing_metadata_outputs_are_blocked_header_only() -> None:
    manifest = _manifest()
    assert manifest["input_metadata_exists"] is False
    assert manifest["input_metadata_read"] is False
    assert manifest["input_metadata_row_count"] == 0
    assert manifest["included_candidate_count"] == 0
    assert manifest["metadata_schema_validated"] is False
    assert manifest["candidate_validation_passed"] is False
    assert manifest["duplicate_exclusion_validation_passed"] is False
    assert manifest["shard_plan_created"] is False
    assert manifest["shard_count"] == 0
    assert manifest["materialized_allowlist_written"] is False
    assert manifest["materialized_allowlist_path"] == ""
    assert manifest["blocked_header_only_written"] is True
    blocked_path = Path(manifest["blocked_header_only_path"])
    assert blocked_path == smoke.BLOCKED_HEADER_ONLY_CSV
    with blocked_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [smoke.ALLOWLIST_COLUMNS]
    assert not smoke.MATERIALIZED_ALLOWLIST_CSV.exists()
    assert manifest["candidate_rows_materialized"] is False
    assert manifest["candidate_allowlist_created"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False


def test_actual_missing_metadata_row_counts_and_audits() -> None:
    manifest = _manifest()
    assert manifest["covapie_allowlist_materialization_precondition_audit_row_count"] == len(_csv_rows(smoke.PRECONDITION_AUDIT_CSV)) == 7
    assert manifest["covapie_allowlist_materialization_input_discovery_audit_row_count"] == len(_csv_rows(smoke.INPUT_DISCOVERY_AUDIT_CSV)) == 1
    assert manifest["covapie_allowlist_materialization_schema_audit_row_count"] == len(_csv_rows(smoke.SCHEMA_AUDIT_CSV)) == 15
    assert manifest["covapie_allowlist_materialization_candidate_validation_audit_row_count"] == len(_csv_rows(smoke.CANDIDATE_VALIDATION_AUDIT_CSV)) == 12
    assert manifest["covapie_allowlist_materialization_duplicate_exclusion_audit_row_count"] == len(_csv_rows(smoke.DUPLICATE_EXCLUSION_AUDIT_CSV)) == 8
    assert manifest["covapie_allowlist_materialization_shard_plan_audit_row_count"] == len(_csv_rows(smoke.SHARD_PLAN_AUDIT_CSV)) == 1
    assert manifest["covapie_allowlist_materialization_output_audit_row_count"] == len(_csv_rows(smoke.OUTPUT_AUDIT_CSV)) == 1
    assert manifest["covapie_allowlist_materialization_execution_boundary_audit_row_count"] == len(_csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_allowlist_materialization_git_safety_audit_row_count"] == len(_csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_allowlist_materialization_mask_scope_audit_row_count"] == len(_csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_allowlist_materialization_feature_semantics_audit_row_count"] == len(_csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_allowlist_materialization_leakage_split_audit_row_count"] == len(_csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)) == 12
    discovery = _csv_rows(smoke.INPUT_DISCOVERY_AUDIT_CSV)[0]
    assert discovery["materialization_status"] == "blocked_due_to_missing_explicit_metadata"
    assert discovery["discovery_audit_passed"] == "True"
    assert discovery["blocking_reasons"] == "missing_explicit_candidate_metadata"
    schema = _csv_rows(smoke.SCHEMA_AUDIT_CSV)
    assert {row["schema_audit_status"] for row in schema} == {"not_applicable_missing_metadata"}
    assert {row["schema_audit_passed"] for row in schema} == {"True"}
    candidate = _csv_rows(smoke.CANDIDATE_VALIDATION_AUDIT_CSV)
    assert {row["validation_status"] for row in candidate} == {"not_evaluated_missing_metadata"}
    assert {row["validation_audit_passed"] for row in candidate} == {"True"}


def test_synthetic_valid_metadata_materializes_allowlist(tmp_path: Path) -> None:
    input_path = tmp_path / "input" / "covapie_candidate_metadata_for_allowlist.csv"
    output_root = tmp_path / "out"
    rows = list(reversed(_valid_rows(10)))
    _write_metadata(input_path, rows)
    result = smoke.run_covapie_candidate_allowlist_materialization_smoke_v0(input_path, output_root)
    manifest = result["manifest"]
    assert manifest["input_metadata_exists"] is True
    assert manifest["input_metadata_read"] is True
    assert manifest["input_metadata_row_count"] == 10
    assert manifest["included_candidate_count"] == 10
    assert manifest["materialization_status"] == "materialized_allowlist_validated"
    assert manifest["metadata_schema_validated"] is True
    assert manifest["candidate_validation_passed"] is True
    assert manifest["duplicate_exclusion_validation_passed"] is True
    assert manifest["shard_plan_created"] is True
    assert manifest["shard_count"] == 2
    assert manifest["materialized_allowlist_written"] is True
    assert manifest["blocked_header_only_written"] is False
    assert manifest["candidate_rows_materialized"] is True
    assert manifest["candidate_allowlist_created"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is True
    materialized = Path(manifest["materialized_allowlist_path"])
    materialized_rows = _csv_rows(materialized)
    assert len(materialized_rows) == 10
    assert list(materialized_rows[0]) == smoke.ALLOWLIST_COLUMNS
    assert [row["candidate_id"] for row in materialized_rows] == sorted(row["candidate_id"] for row in rows)
    assert all(row["residue_name"] == "CYS" and row["residue_atom_name"] == "SG" for row in materialized_rows)
    assert not Path(manifest["blocked_header_only_path"]).exists() if manifest["blocked_header_only_path"] else True
    assert manifest["raw_data_read"] is False


def test_synthetic_invalid_metadata_blocks_materialization(tmp_path: Path) -> None:
    input_path = tmp_path / "input" / "covapie_candidate_metadata_for_allowlist.csv"
    output_root = tmp_path / "out"
    rows = _valid_rows(10)
    rows[1]["candidate_id"] = rows[0]["candidate_id"]
    rows[2]["residue_name"] = "SER"
    rows[3]["source_file_relative_path"] = "../unsafe.cif"
    rows[4]["manual_review_status"] = "not_reviewed"
    _write_metadata(input_path, rows)
    result = smoke.run_covapie_candidate_allowlist_materialization_smoke_v0(input_path, output_root)
    manifest = result["manifest"]
    assert manifest["input_metadata_exists"] is True
    assert manifest["input_metadata_read"] is True
    assert manifest["materialization_status"] == "blocked_due_to_invalid_metadata"
    assert manifest["metadata_schema_validated"] is True
    assert manifest["candidate_validation_passed"] is False
    assert manifest["duplicate_exclusion_validation_passed"] is False
    assert manifest["materialized_allowlist_written"] is False
    assert manifest["blocked_header_only_written"] is True
    assert manifest["blocking_reasons"] == ["invalid_metadata"]
    candidate = {row["validation_item"]: row for row in result["candidate_rows"]}
    assert candidate["candidate_id_non_empty_unique"]["validation_audit_passed"] is False
    assert candidate["source_file_relative_path_safe"]["validation_audit_passed"] is False
    assert candidate["cys_sg_only_scope"]["validation_audit_passed"] is False
    assert candidate["manual_review_status_allowed"]["validation_audit_passed"] is False
    duplicate = {row["duplicate_exclusion_item"]: row for row in result["duplicate_rows"]}
    assert duplicate["unique_candidate_id"]["duplicate_audit_passed"] is False


def test_canonical_masks_feature_semantics_and_leakage_boundaries() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13ag"}
    assert {row["mask_scope_audit_passed"] for row in mask} == {"True"}
    feature = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_allowlist_materialization_smoke"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    leakage = _csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["allowlist_materialization_smoke"]["current_step_status"] == "executed_metadata_preflight_only"
    assert boundary["input_metadata_csv_read"]["current_step_status"] == "executed_only_if_metadata_exists_else_not_executed"
    assert boundary["candidate_row_materialization"]["current_step_status"] == "executed_only_if_metadata_valid_else_not_executed"
    for item in smoke.EXECUTION_BOUNDARY_ITEMS[3:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["execution_boundary_passed"] == "True"
    git_rows = {row["git_safety_item"]: row for row in _csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)}
    assert ".pt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".ckpt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".npz" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".sdf" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert {row["git_safety_audit_passed"] for row in git_rows.values()} == {"True"}
    manifest = _manifest()
    for key in [
        "raw_data_read",
        "raw_file_copied",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "pdb_read",
        "pdb_generated",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "atom_site_text_scan_run",
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
    ]:
        assert manifest[key] is False


def test_readiness_boundary() -> None:
    manifest = _manifest()
    assert manifest["allowlist_materialization_smoke_preflight_passed"] is True
    assert manifest["covapie_candidate_allowlist_materialization_smoke_passed"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "provide_explicit_candidate_metadata_for_allowlist"
