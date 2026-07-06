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

from covalent_ext import covapie_candidate_allowlist_creation_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_candidate_allowlist_creation_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13af_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_candidate_allowlist_creation_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13af_missing_allowlist_preflight_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_covapie_naming_and_no_runtime_imports() -> None:
    text = gate.NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    assert "CovaPIE" in text
    assert "CovaGEN" in text
    assert "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE" in text
    assert gate.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_candidate_allowlist_creation_gate.py")
    script_path = Path("scripts/check_covapie_candidate_allowlist_creation_gate_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)


def test_header_only_template_contract() -> None:
    manifest = _manifest()
    template_path = Path(manifest["allowlist_template_path"])
    assert template_path == gate.TEMPLATE_CSV
    assert template_path.is_file()
    with template_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == gate.ALLOWLIST_COLUMNS
    assert len(rows) == 1
    assert manifest["allowlist_template_written"] is True
    assert manifest["allowlist_template_header_only"] is True
    assert manifest["allowlist_template_column_count"] == 15
    assert manifest["allowlist_template_data_row_count"] == 0
    assert manifest["candidate_rows_materialized"] is False
    assert manifest["candidate_allowlist_created"] is False
    assert manifest["candidate_allowlist_template_created"] is True
    audit = _csv_rows(gate.TEMPLATE_AUDIT_CSV)[0]
    assert audit["template_written"] == "True"
    assert audit["template_header_only"] == "True"
    assert audit["template_data_row_count"] == "0"
    assert audit["template_column_count"] == "15"
    assert audit["template_columns_match_contract"] == "True"
    assert audit["no_candidate_rows_materialized"] == "True"


def test_output_row_counts_match_contract() -> None:
    manifest = _manifest()
    assert manifest["covapie_allowlist_creation_precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 6
    assert manifest["covapie_allowlist_schema_contract_row_count"] == len(_csv_rows(gate.SCHEMA_CONTRACT_CSV)) == 15
    assert manifest["covapie_allowlist_candidate_source_contract_row_count"] == len(_csv_rows(gate.CANDIDATE_SOURCE_CONTRACT_CSV)) == 8
    assert manifest["covapie_allowlist_selection_rule_contract_row_count"] == len(_csv_rows(gate.SELECTION_RULE_CONTRACT_CSV)) == 12
    assert manifest["covapie_allowlist_manual_review_contract_row_count"] == len(_csv_rows(gate.MANUAL_REVIEW_CONTRACT_CSV)) == 6
    assert manifest["covapie_allowlist_path_safety_contract_row_count"] == len(_csv_rows(gate.PATH_SAFETY_CONTRACT_CSV)) == 8
    assert manifest["covapie_allowlist_duplicate_exclusion_contract_row_count"] == len(_csv_rows(gate.DUPLICATE_EXCLUSION_CONTRACT_CSV)) == 8
    assert manifest["covapie_allowlist_template_audit_row_count"] == len(_csv_rows(gate.TEMPLATE_AUDIT_CSV)) == 1
    assert manifest["covapie_allowlist_execution_boundary_audit_row_count"] == len(_csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_allowlist_git_safety_audit_row_count"] == len(_csv_rows(gate.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_allowlist_mask_scope_audit_row_count"] == len(_csv_rows(gate.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_allowlist_feature_semantics_audit_row_count"] == len(_csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_allowlist_leakage_split_audit_row_count"] == len(_csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)) == 12


def test_schema_selection_and_source_contracts() -> None:
    schema = {row["allowlist_column"]: row for row in _csv_rows(gate.SCHEMA_CONTRACT_CSV)}
    assert list(schema) == gate.ALLOWLIST_COLUMNS
    assert schema["candidate_id"]["validation_rule"] == "non-empty and unique"
    assert schema["source_file_relative_path"]["validation_rule"] == "relative path only and no parent directory escape"
    assert schema["residue_name"]["validation_rule"] == "must be CYS for current phase"
    assert schema["residue_atom_name"]["validation_rule"] == "must be SG for current phase"
    assert schema["manual_review_status"]["validation_rule"] == "reviewed_pass or approved_for_smoke for included rows"
    assert {row["contract_passed"] for row in schema.values()} == {"True"}

    selection = {row["contract_item"]: row for row in _csv_rows(gate.SELECTION_RULE_CONTRACT_CSV)}
    assert selection["min_included_candidates_10"]["contract_requirement"].endswith("at least 10 rows")
    assert selection["max_included_candidates_30"]["contract_requirement"].endswith("at most 30 rows")
    assert selection["shard_size_5"]["contract_requirement"] == "future shard size is fixed at 5"
    assert selection["cys_sg_only"]["contract_requirement"] == "current reactive residue scope is CYS/SG only"
    assert selection["known_restoration_template_required"]["contract_requirement"] == "known restoration template is required"
    assert {row["contract_passed"] for row in selection.values()} == {"True"}

    source_rows = _csv_rows(gate.CANDIDATE_SOURCE_CONTRACT_CSV)
    assert {row["raw_content_read_current_step"] for row in source_rows} == {"False"}
    assert {row["contract_passed"] for row in source_rows} == {"True"}


def test_manual_review_path_duplicate_contracts() -> None:
    manual = {row["contract_item"]: row for row in _csv_rows(gate.MANUAL_REVIEW_CONTRACT_CSV)}
    assert "manual_review_status_enum" in manual
    assert "included_rows_require_reviewed_pass_or_approved_for_smoke" in manual
    assert "no_training_readiness_claim_from_manual_review" in manual
    path_rows = {row["contract_item"]: row for row in _csv_rows(gate.PATH_SAFETY_CONTRACT_CSV)}
    assert "relative_path_only" in path_rows
    assert "no_parent_directory_escape" in path_rows
    assert "no_raw_file_content_read_current_step" in path_rows
    assert {row["raw_content_read_current_step"] for row in path_rows.values()} == {"False"}
    duplicate = {row["contract_item"]: row for row in _csv_rows(gate.DUPLICATE_EXCLUSION_CONTRACT_CSV)}
    assert "unique_candidate_id" in duplicate
    assert "excluded_rows_not_counted_in_10_to_30" in duplicate
    assert "invalid_rows_block_raw_read_smoke" in duplicate
    assert {row["contract_passed"] for row in duplicate.values()} == {"True"}


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
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13af"}
    assert {row["mask_scope_audit_passed"] for row in mask} == {"True"}
    feature = _csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_allowlist_creation_gate"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert all(row["recommended_audit_step"] for row in feature)
    leakage = _csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["future_required_gate"] for row in leakage} == {"covapie_leakage_split_design_gate_before_training"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["allowlist_creation_gate"]["current_step_status"] == "executed_contract_gate_only"
    assert boundary["template_header_write"]["current_step_status"] == "executed_header_only_template"
    for item in gate.EXECUTION_BOUNDARY_ITEMS[2:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["execution_boundary_passed"] == "True"
    git_rows = {row["git_safety_item"]: row for row in _csv_rows(gate.GIT_SAFETY_AUDIT_CSV)}
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


def test_design_booleans_and_readiness_boundary() -> None:
    manifest = _manifest()
    for key in [
        "all_preconditions_validated",
        "all_schema_contracts_declared",
        "all_candidate_source_contracts_declared",
        "all_selection_rule_contracts_declared",
        "all_manual_review_contracts_declared",
        "all_path_safety_contracts_declared",
        "all_duplicate_exclusion_contracts_declared",
        "all_template_audits_passed",
        "all_execution_boundaries_respected",
        "all_git_safety_audits_passed",
        "all_mask_scope_audits_passed",
        "all_feature_semantics_audits_passed",
        "all_leakage_split_audits_passed",
        "candidate_allowlist_creation_gate_passed",
    ]:
        assert manifest[key] is True
    assert manifest["current_reactive_residue_scope"] == "cys_sg_only"
    assert manifest["batch_scale_initial_min_candidate_count"] == 10
    assert manifest["batch_scale_initial_max_candidate_count"] == 30
    assert manifest["batch_scale_initial_shard_size"] == 5
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_candidate_allowlist_materialization_smoke"
    assert manifest["blocking_reasons"] == []


def test_no_forbidden_artifacts_or_protected_diffs() -> None:
    forbidden_suffixes = set(gate.FORBIDDEN_COMMITTABLE_SUFFIXES)
    assert not [
        path
        for path in gate.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in forbidden_suffixes
    ]
    assert subprocess.run(["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"]).returncode == 0
    assert subprocess.run(["git", "diff", "--quiet", "--", "dataset.py", "data/prepare_crossdocked.py"]).returncode == 0
    assert subprocess.run(["git", "diff", "--cached", "--quiet", "--", "data/raw/covalent_sources"]).returncode == 0
    assert subprocess.run(["git", "ls-files", "data/raw/covalent_sources"], stdout=subprocess.PIPE, text=True).stdout.strip() == ""
