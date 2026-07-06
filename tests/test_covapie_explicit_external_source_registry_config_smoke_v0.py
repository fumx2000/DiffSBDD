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

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_explicit_external_source_registry_config_smoke_v0.py"],
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


def test_check_script_passes_and_writes_explicit_covpdb_config() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_explicit_external_source_registry_config_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["source_registry_config_written"] is True
    assert manifest["source_registry_config_row_count"] == 1
    assert manifest["enabled_source_name"] == "CovPDB"
    assert manifest["enabled_source_ready_for_download_smoke"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is True
    assert manifest["blocking_reasons"] == []
    assert manifest["all_checks_passed"] is True


def test_preconditions_contracts_and_no_forbidden_runtime_imports() -> None:
    assert smoke.validate_step13al_precondition_v0() is True
    assert smoke.validate_step13al_template_v0() is True
    assert smoke.validate_step13ak_allowed_artifact_contract_v0() is True
    assert smoke.validate_step13aj_event_identity_key_contract_v0() is True
    assert smoke.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_explicit_external_source_registry_config_smoke.py")
    script_path = Path("scripts/check_covapie_explicit_external_source_registry_config_smoke_v0.py")
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


def test_config_csv_has_exact_covpdb_row_and_does_not_require_path_existence() -> None:
    rows = _csv_rows(smoke.CONFIG_CSV)
    assert len(rows) == 1
    row = rows[0]
    assert list(row) == smoke.SOURCE_CONFIG_COLUMNS
    assert row == smoke.CONFIG_ROW
    assert row["source_name"] == "CovPDB"
    assert row["source_family"] == "specialized_covalent_protein_ligand_database"
    assert row["source_access_method"] == "manual_user_supplied"
    assert row["expected_metadata_artifact_type"] == "csv"
    assert row["expected_candidate_unit"] == "covalent_ligand_residue_event"
    assert row["enabled_for_download_smoke"] == "true"
    assert row["manual_source_verification_status"] == "verified_by_user"
    assert row["source_metadata_index_url_or_local_path"].startswith(
        "data/derived/covalent_small/external_metadata_index/covpdb/"
    )
    manifest = _manifest()
    assert manifest["source_metadata_index_path_checked_current_step"] is False
    assert manifest["source_metadata_index_file_opened"] is False
    assert manifest["source_metadata_index_file_exists_current_step"] is False


def test_output_row_counts_and_validation_audits() -> None:
    manifest = _manifest()
    assert manifest["covapie_explicit_external_source_registry_precondition_audit_row_count"] == len(_csv_rows(smoke.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["covapie_explicit_external_source_registry_schema_validation_audit_row_count"] == len(_csv_rows(smoke.SCHEMA_VALIDATION_AUDIT_CSV)) == 12
    assert manifest["covapie_explicit_external_source_registry_value_validation_audit_row_count"] == len(_csv_rows(smoke.VALUE_VALIDATION_AUDIT_CSV)) == 12
    assert manifest["covapie_explicit_external_source_registry_enabled_source_audit_row_count"] == len(_csv_rows(smoke.ENABLED_SOURCE_AUDIT_CSV)) == 8
    assert manifest["covapie_explicit_external_source_registry_path_policy_audit_row_count"] == len(_csv_rows(smoke.PATH_POLICY_AUDIT_CSV)) == 8
    assert manifest["covapie_explicit_external_source_registry_execution_boundary_audit_row_count"] == len(_csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_explicit_external_source_registry_git_safety_audit_row_count"] == len(_csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_explicit_external_source_registry_mask_scope_audit_row_count"] == len(_csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_explicit_external_source_registry_feature_semantics_audit_row_count"] == len(_csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_explicit_external_source_registry_leakage_split_audit_row_count"] == len(_csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)) == 12
    assert {row["precondition_passed"] for row in _csv_rows(smoke.PRECONDITION_AUDIT_CSV)} == {"True"}
    assert {row["schema_validation_status"] for row in _csv_rows(smoke.SCHEMA_VALIDATION_AUDIT_CSV)} == {"present"}
    assert {row["schema_validation_passed"] for row in _csv_rows(smoke.SCHEMA_VALIDATION_AUDIT_CSV)} == {"True"}
    assert {row["validation_status"] for row in _csv_rows(smoke.VALUE_VALIDATION_AUDIT_CSV)} == {"passed"}
    assert {row["validation_passed"] for row in _csv_rows(smoke.VALUE_VALIDATION_AUDIT_CSV)} == {"True"}


def test_enabled_source_and_path_policy_audits_pass() -> None:
    enabled = _csv_rows(smoke.ENABLED_SOURCE_AUDIT_CSV)
    assert [row["enabled_source_audit_item"] for row in enabled] == smoke.ENABLED_SOURCE_ITEMS
    assert {row["enabled_source_count"] for row in enabled} == {"1"}
    assert {row["audit_status"] for row in enabled} == {"passed"}
    assert {row["audit_passed"] for row in enabled} == {"True"}
    path_policy = _csv_rows(smoke.PATH_POLICY_AUDIT_CSV)
    assert [row["path_policy_item"] for row in path_policy] == smoke.PATH_POLICY_ITEMS
    assert {row["path_policy_status"] for row in path_policy} == {"passed"}
    assert {row["path_policy_passed"] for row in path_policy} == {"True"}


def test_event_key_masks_feature_semantics_and_leakage_boundaries() -> None:
    manifest = _manifest()
    assert manifest["metadata_index_root"] == "data/derived/covalent_small/external_metadata_index"
    assert manifest["raw_structure_root"] == "data/raw/covalent_sources"
    assert manifest["event_identity_key_policy"] == "no_pdb_id_only_join"
    assert manifest["minimal_event_key"] == "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name"
    assert manifest["preferred_event_key"] == "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair"
    assert manifest["one_row_one_covalent_event"] is True
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13al"}
    feature = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_explicit_source_registry_config_smoke"] for row in feature} == {"False"}
    leakage = _csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    manifest = _manifest()
    boundary = {row["boundary_item"]: row for row in _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["explicit_external_source_registry_config_smoke"]["current_step_status"] == "executed_config_smoke_only"
    assert boundary["source_config_write"]["current_step_status"] == "executed_config_only"
    assert boundary["source_config_validation"]["current_step_status"] == "executed_validation_only"
    for item in smoke.EXECUTION_BOUNDARY_ITEMS[3:]:
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


def test_readiness_boundary() -> None:
    manifest = _manifest()
    assert manifest["explicit_external_source_registry_config_smoke_passed"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is True
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_external_metadata_index_download_smoke"
