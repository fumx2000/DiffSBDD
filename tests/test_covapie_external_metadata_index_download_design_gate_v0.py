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

from covalent_ext import covapie_external_metadata_index_download_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_external_metadata_index_download_design_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13aj_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_external_metadata_index_download_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13aj_source_acquisition_design_gate_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_step13aj_contracts_template_naming_and_no_network_imports() -> None:
    assert gate.validate_step13aj_precondition_v0() is True
    assert gate.validate_step13aj_source_registry_contract_v0() is True
    assert gate.validate_step13aj_event_identity_key_contract_v0() is True
    assert gate.validate_step13ag_template_v0() is True
    assert gate.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_external_metadata_index_download_design_gate.py")
    script_path = Path("scripts/check_covapie_external_metadata_index_download_design_gate_v0.py")
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


def test_output_row_counts_match_contracts() -> None:
    manifest = _manifest()
    assert manifest["covapie_external_metadata_download_precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["covapie_external_metadata_index_source_config_schema_contract_row_count"] == len(_csv_rows(gate.SOURCE_CONFIG_SCHEMA_CONTRACT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_download_plan_contract_row_count"] == len(_csv_rows(gate.DOWNLOAD_PLAN_CONTRACT_CSV)) == 10
    assert manifest["covapie_external_metadata_index_allowed_artifact_contract_row_count"] == len(_csv_rows(gate.ALLOWED_ARTIFACT_CONTRACT_CSV)) == 10
    assert manifest["covapie_external_metadata_index_output_path_contract_row_count"] == len(_csv_rows(gate.OUTPUT_PATH_CONTRACT_CSV)) == 8
    assert manifest["covapie_external_metadata_index_download_manifest_contract_row_count"] == len(_csv_rows(gate.DOWNLOAD_MANIFEST_CONTRACT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_schema_probe_contract_row_count"] == len(_csv_rows(gate.SCHEMA_PROBE_CONTRACT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_event_key_mapping_contract_row_count"] == len(_csv_rows(gate.EVENT_KEY_MAPPING_CONTRACT_CSV)) == 8
    assert manifest["covapie_external_metadata_index_candidate_filter_contract_row_count"] == len(_csv_rows(gate.CANDIDATE_FILTER_CONTRACT_CSV)) == 10
    assert manifest["covapie_external_metadata_index_failure_taxonomy_contract_row_count"] == len(_csv_rows(gate.FAILURE_TAXONOMY_CONTRACT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_execution_boundary_audit_row_count"] == len(_csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_external_metadata_index_git_safety_audit_row_count"] == len(_csv_rows(gate.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_external_metadata_index_mask_scope_audit_row_count"] == len(_csv_rows(gate.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_external_metadata_index_feature_semantics_audit_row_count"] == len(_csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_external_metadata_index_leakage_split_audit_row_count"] == len(_csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)) == 12


def test_source_config_and_download_plan_are_design_only() -> None:
    config = _csv_rows(gate.SOURCE_CONFIG_SCHEMA_CONTRACT_CSV)
    assert [row["config_field"] for row in config] == [
        "source_slot_id",
        "source_name",
        "source_family",
        "source_priority",
        "source_metadata_index_url_or_local_path",
        "source_access_method",
        "source_version_or_download_date",
        "expected_metadata_artifact_type",
        "expected_candidate_unit",
        "citation_or_license_note",
        "enabled_for_download_smoke",
        "manual_source_verification_status",
    ]
    assert {row["current_step_configured"] for row in config} == {"False"}
    assert {row["config_contract_passed"] for row in config} == {"True"}
    assert "covalent_ligand_residue_event" in {row["allowed_values_or_rule"] for row in config}
    source_family = next(row for row in config if row["config_field"] == "source_family")
    assert "specialized_covalent_protein_ligand_database" in source_family["allowed_values_or_rule"]
    assert "pdb_covalent_annotation_fallback" in source_family["allowed_values_or_rule"]
    plan = _csv_rows(gate.DOWNLOAD_PLAN_CONTRACT_CSV)
    assert len(plan) == 10
    assert {row["current_step_executed"] for row in plan} == {"False"}
    assert {row["network_or_download_used"] for row in plan} == {"False"}
    assert {row["plan_contract_passed"] for row in plan} == {"True"}


def test_allowed_artifacts_output_paths_manifest_and_probe_contracts() -> None:
    manifest = _manifest()
    artifacts = {row["artifact_type"]: row for row in _csv_rows(gate.ALLOWED_ARTIFACT_CONTRACT_CSV)}
    for key in ["csv_metadata_index", "tsv_metadata_index", "json_metadata_index", "jsonl_metadata_index"]:
        assert artifacts[key]["allowed_for_metadata_index_download_smoke"] == "True"
        assert artifacts[key]["current_step_downloaded"] == "False"
    for key in ["zip_archive_forbidden_current_smoke", "raw_pdb_forbidden", "raw_mmcif_forbidden", "raw_sdf_mol2_forbidden"]:
        assert artifacts[key]["allowed_for_metadata_index_download_smoke"] == "False"
    assert artifacts["raw_pdb_forbidden"]["raw_structure_artifact"] == "True"
    assert artifacts["raw_mmcif_forbidden"]["raw_structure_artifact"] == "True"
    paths = {row["path_rule"]: row for row in _csv_rows(gate.OUTPUT_PATH_CONTRACT_CSV)}
    assert paths["external_metadata_index_root"]["path_or_policy"] == gate.METADATA_INDEX_ROOT
    assert paths["raw_structure_root_separate"]["path_or_policy"] == gate.RAW_STRUCTURE_ROOT
    assert {row["current_step_written"] for row in paths.values()} == {"False"}
    dl_manifest = _csv_rows(gate.DOWNLOAD_MANIFEST_CONTRACT_CSV)
    assert len(dl_manifest) == 12
    assert {row["current_step_written"] for row in dl_manifest} == {"False"}
    assert next(row for row in dl_manifest if row["manifest_field"] == "checksum_optional")["manifest_field_required"] == "False"
    probe = _csv_rows(gate.SCHEMA_PROBE_CONTRACT_CSV)
    assert len(probe) == 12
    assert {row["current_step_probe_executed"] for row in probe} == {"False"}
    assert {row["schema_probe_contract_passed"] for row in probe} == {"True"}
    assert manifest["metadata_index_root"] == gate.METADATA_INDEX_ROOT
    assert manifest["raw_structure_root"] == gate.RAW_STRUCTURE_ROOT
    assert manifest["metadata_index_allowed_artifact_types"] == ["csv", "tsv", "json", "jsonl"]
    assert manifest["metadata_index_deferred_artifact_types"] == ["xlsx", "html_table"]
    assert manifest["metadata_index_forbidden_artifact_types"] == ["zip", "pdb", "mmcif", "cif", "sdf", "mol2", "gz"]


def test_event_key_mapping_and_candidate_filter_contracts() -> None:
    manifest = _manifest()
    rows = {row["event_key_mapping_rule"]: row for row in _csv_rows(gate.EVENT_KEY_MAPPING_CONTRACT_CSV)}
    minimal = "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name"
    preferred = minimal + "+covalent_bond_atom_pair"
    assert rows["no_pdb_id_only_join"]["required_fields_or_policy"] == "pdb_id is insufficient"
    assert rows["minimal_event_key_fields_required"]["required_fields_or_policy"] == minimal
    assert rows["preferred_event_key_fields_required"]["required_fields_or_policy"] == preferred
    assert {row["event_key_mapping_contract_passed"] for row in rows.values()} == {"True"}
    assert manifest["event_identity_key_policy"] == "no_pdb_id_only_join"
    assert manifest["minimal_event_key"] == minimal
    assert manifest["preferred_event_key"] == preferred
    assert manifest["one_row_one_covalent_event"] is True
    candidate = _csv_rows(gate.CANDIDATE_FILTER_CONTRACT_CSV)
    assert len(candidate) == 10
    assert {row["current_step_filter_executed"] for row in candidate} == {"False"}
    assert {row["candidate_filter_contract_passed"] for row in candidate} == {"True"}
    failure = _csv_rows(gate.FAILURE_TAXONOMY_CONTRACT_CSV)
    assert len(failure) == 12
    assert {row["failure_taxonomy_passed"] for row in failure} == {"True"}


def test_masks_feature_semantics_and_leakage_boundaries() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(gate.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13aj"}
    feature = _csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_external_metadata_index_design_gate"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    leakage = _csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["future_required_gate"] for row in leakage} == {"covapie_leakage_split_design_gate_before_training"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    manifest = _manifest()
    boundary = {row["boundary_item"]: row for row in _csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["external_metadata_index_download_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert boundary["source_config_schema_contract_write"]["current_step_status"] == "executed_contract_only"
    assert boundary["metadata_download_plan_contract_write"]["current_step_status"] == "executed_contract_only"
    for item in gate.EXECUTION_BOUNDARY_ITEMS[3:]:
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


def test_design_gate_and_readiness_boundary() -> None:
    manifest = _manifest()
    for key in [
        "all_preconditions_validated",
        "all_source_config_schema_contracts_declared",
        "all_download_plan_contracts_declared",
        "all_allowed_artifact_contracts_declared",
        "all_output_path_contracts_declared",
        "all_download_manifest_contracts_declared",
        "all_schema_probe_contracts_declared",
        "all_event_key_mapping_contracts_declared",
        "all_candidate_filter_contracts_declared",
        "all_failure_taxonomy_contracts_declared",
        "external_metadata_index_download_design_gate_passed",
    ]:
        assert manifest[key] is True
    assert manifest["external_source_configured_current_step"] is False
    assert manifest["external_source_verified_current_step"] is False
    assert manifest["external_network_access_used"] is False
    assert manifest["external_metadata_downloaded"] is False
    assert manifest["raw_structure_downloaded"] is False
    assert manifest["ready_for_covapie_external_source_registry_configuration"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is False
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_external_source_registry_configuration"
