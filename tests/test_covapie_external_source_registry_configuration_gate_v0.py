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

from covalent_ext import covapie_external_source_registry_configuration_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_external_source_registry_configuration_gate_v0.py"],
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


def _write_config(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=gate.SOURCE_CONFIG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _valid_config_row(**overrides: str) -> dict[str, str]:
    row = {
        "source_slot_id": "specialized_covalent_complex_database_primary_1",
        "source_name": "user_configured_specialized_source",
        "source_family": "specialized_covalent_protein_ligand_database",
        "source_priority": "1",
        "source_metadata_index_url_or_local_path": "https://example.invalid/metadata.csv",
        "source_access_method": "configured_url",
        "source_version_or_download_date": "user_supplied_version_or_date",
        "expected_metadata_artifact_type": "csv",
        "expected_candidate_unit": "covalent_ligand_residue_event",
        "citation_or_license_note": "user_supplied_license_note_required",
        "enabled_for_download_smoke": "true",
        "manual_source_verification_status": "verified_by_user",
    }
    row.update(overrides)
    return row


def test_check_script_passes_and_missing_config_blocks_safely() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_external_source_registry_configuration_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ak_external_metadata_index_download_design_gate_validated"] is True
    assert manifest["source_registry_config_template_written"] is True
    assert manifest["source_registry_config_exists"] is False
    assert manifest["source_registry_config_read"] is False
    assert manifest["source_registry_config_row_count"] == 0
    assert manifest["configuration_status"] == "blocked_due_to_missing_explicit_source_registry_config"
    assert manifest["blocking_reasons"] == ["missing_explicit_source_registry_config"]
    assert manifest["all_checks_passed"] is True


def test_preconditions_templates_and_no_runtime_imports_or_fetch_commands() -> None:
    assert gate.validate_step13ak_precondition_v0() is True
    assert gate.validate_step13ak_source_config_schema_contract_v0() is True
    assert gate.validate_step13ak_allowed_artifact_contract_v0() is True
    assert gate.validate_step13aj_event_identity_key_contract_v0() is True
    assert gate.validate_step13ag_template_v0() is True
    assert gate.validate_covapie_naming_convention_v0() is True
    with gate.TEMPLATE_CSV.open(newline="", encoding="utf-8") as handle:
        assert list(csv.reader(handle)) == [gate.SOURCE_CONFIG_COLUMNS]
    with gate.BLOCKED_HEADER_ONLY_CSV.open(newline="", encoding="utf-8") as handle:
        assert list(csv.reader(handle)) == [gate.SOURCE_CONFIG_COLUMNS]
    assert not gate.VALIDATED_CONFIG_CSV.exists()
    module_path = Path("src/covalent_ext/covapie_external_source_registry_configuration_gate.py")
    script_path = Path("scripts/check_covapie_external_source_registry_configuration_gate_v0.py")
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


def test_default_missing_config_output_row_counts() -> None:
    manifest = _manifest()
    assert manifest["covapie_external_source_registry_precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["covapie_external_source_registry_input_discovery_audit_row_count"] == len(_csv_rows(gate.INPUT_DISCOVERY_AUDIT_CSV)) == 1
    assert manifest["covapie_external_source_registry_schema_validation_audit_row_count"] == len(_csv_rows(gate.SCHEMA_VALIDATION_AUDIT_CSV)) == 12
    assert manifest["covapie_external_source_registry_value_validation_audit_row_count"] == len(_csv_rows(gate.VALUE_VALIDATION_AUDIT_CSV)) == 12
    assert manifest["covapie_external_source_registry_enabled_source_audit_row_count"] == len(_csv_rows(gate.ENABLED_SOURCE_AUDIT_CSV)) == 8
    assert manifest["covapie_external_source_registry_output_audit_row_count"] == len(_csv_rows(gate.OUTPUT_AUDIT_CSV)) == 1
    assert manifest["covapie_external_source_registry_execution_boundary_audit_row_count"] == len(_csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_external_source_registry_git_safety_audit_row_count"] == len(_csv_rows(gate.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_external_source_registry_mask_scope_audit_row_count"] == len(_csv_rows(gate.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_external_source_registry_feature_semantics_audit_row_count"] == len(_csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_external_source_registry_leakage_split_audit_row_count"] == len(_csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)) == 12


def test_missing_config_audits_are_blocked_but_complete() -> None:
    discovery = _csv_rows(gate.INPUT_DISCOVERY_AUDIT_CSV)[0]
    assert discovery["source_registry_config_exists"] == "False"
    assert discovery["source_registry_config_read"] == "False"
    assert discovery["source_registry_config_row_count"] == "0"
    assert discovery["configuration_status"] == "blocked_due_to_missing_explicit_source_registry_config"
    assert discovery["blocking_reasons"] == "missing_explicit_source_registry_config"
    schema = _csv_rows(gate.SCHEMA_VALIDATION_AUDIT_CSV)
    assert [row["required_column"] for row in schema] == gate.SOURCE_CONFIG_COLUMNS
    assert {row["column_present"] for row in schema} == {"False"}
    assert {row["schema_validation_status"] for row in schema} == {"not_applicable_missing_config"}
    assert {row["schema_validation_passed"] for row in schema} == {"True"}
    value = _csv_rows(gate.VALUE_VALIDATION_AUDIT_CSV)
    assert {row["validation_status"] for row in value} == {"not_evaluated_missing_config"}
    assert {row["validation_passed"] for row in value} == {"True"}
    output = _csv_rows(gate.OUTPUT_AUDIT_CSV)[0]
    assert output["template_written"] == "True"
    assert output["blocked_header_only_written"] == "True"
    assert output["validated_config_written"] == "False"
    assert output["configured_source_count"] == "0"
    assert output["enabled_source_count"] == "0"


def test_synthetic_valid_config_allows_download_smoke(tmp_path: Path) -> None:
    config = tmp_path / "covapie_external_source_registry_config.csv"
    _write_config(config, [_valid_config_row()])
    result = gate.run_covapie_external_source_registry_configuration_gate_v0(output_root=tmp_path / "out", input_config_csv=config)
    manifest = result["manifest"]
    assert manifest["source_registry_config_exists"] is True
    assert manifest["source_registry_config_read"] is True
    assert manifest["source_registry_config_row_count"] == 1
    assert manifest["source_registry_schema_validated"] is True
    assert manifest["source_registry_values_validated"] is True
    assert manifest["configured_source_count"] == 1
    assert manifest["enabled_source_count"] == 1
    assert manifest["enabled_source_slot_id"] == "specialized_covalent_complex_database_primary_1"
    assert manifest["enabled_source_name"] == "user_configured_specialized_source"
    assert manifest["enabled_source_family"] == "specialized_covalent_protein_ligand_database"
    assert manifest["enabled_source_artifact_type"] == "csv"
    assert manifest["enabled_source_verified"] is True
    assert manifest["enabled_source_ready_for_download_smoke"] is True
    assert manifest["configuration_status"] == "validated_source_registry_config"
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is True
    assert manifest["recommended_next_step"] == "covapie_external_metadata_index_download_smoke"
    assert manifest["blocking_reasons"] == []


def test_synthetic_invalid_config_blocks(tmp_path: Path) -> None:
    config = tmp_path / "covapie_external_source_registry_config.csv"
    _write_config(config, [_valid_config_row(manual_source_verification_status="unverified")])
    result = gate.run_covapie_external_source_registry_configuration_gate_v0(output_root=tmp_path / "out", input_config_csv=config)
    manifest = result["manifest"]
    assert manifest["source_registry_config_exists"] is True
    assert manifest["source_registry_schema_validated"] is True
    assert manifest["source_registry_values_validated"] is True
    assert manifest["enabled_source_verified"] is False
    assert manifest["enabled_source_ready_for_download_smoke"] is False
    assert manifest["configuration_status"] == "blocked_due_to_invalid_source_registry_config"
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is False
    assert manifest["recommended_next_step"] == "provide_explicit_external_source_registry_config"
    assert manifest["blocking_reasons"] == ["invalid_source_registry_config"]


def test_allowed_values_event_key_masks_feature_and_leakage() -> None:
    manifest = _manifest()
    assert manifest["metadata_index_root"] == gate.METADATA_INDEX_ROOT
    assert manifest["raw_structure_root"] == gate.RAW_STRUCTURE_ROOT
    assert manifest["event_identity_key_policy"] == "no_pdb_id_only_join"
    assert manifest["minimal_event_key"] == "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name"
    assert manifest["preferred_event_key"] == "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name+covalent_bond_atom_pair"
    assert manifest["one_row_one_covalent_event"] is True
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(gate.MASK_SCOPE_AUDIT_CSV)
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13ak"}
    feature = _csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_external_source_registry_gate"] for row in feature} == {"False"}
    leakage = _csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    manifest = _manifest()
    boundary = {row["boundary_item"]: row for row in _csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["external_source_registry_configuration_gate"]["current_step_status"] == "executed_configuration_gate_only"
    assert boundary["source_config_template_write"]["current_step_status"] == "executed_template_only"
    assert boundary["source_config_input_read"]["current_step_status"] == "executed_only_if_explicit_config_exists_else_not_executed"
    for item in gate.EXECUTION_BOUNDARY_ITEMS[4:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["execution_boundary_passed"] == "True"
    git_rows = {row["git_safety_item"]: row for row in _csv_rows(gate.GIT_SAFETY_AUDIT_CSV)}
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
    assert manifest["external_source_registry_configuration_gate_passed"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is False
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "provide_explicit_external_source_registry_config"
