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

from covalent_ext import covapie_specialized_covalent_database_source_acquisition_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_specialized_covalent_database_source_acquisition_design_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13ai_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_specialized_covalent_database_source_acquisition_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ai_metadata_inventory_gate_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_step13ag_template_covapie_naming_and_no_runtime_imports_or_fetch_commands() -> None:
    with gate.STEP13AG_TEMPLATE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [gate.ALLOWLIST_COLUMNS]
    assert gate.validate_covapie_naming_convention_v0() is True
    module_path = Path("src/covalent_ext/covapie_specialized_covalent_database_source_acquisition_design_gate.py")
    script_path = Path("scripts/check_covapie_specialized_covalent_database_source_acquisition_design_gate_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio", "requests", "urllib"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    for path in [module_path, script_path]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run":
                    text = ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
                    assert "curl" not in text
                    assert "wget" not in text


def test_source_registry_declares_unverified_specialized_database_slots() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.SOURCE_REGISTRY_CONTRACT_CSV)
    assert len(rows) == manifest["source_registry_contract_row_count"] == 5
    assert [row["source_slot_id"] for row in rows] == [
        "specialized_covalent_complex_database_primary_1",
        "specialized_covalent_complex_database_primary_2",
        "specialized_covalent_complex_database_primary_3",
        "pdb_covalent_annotation_fallback",
        "user_or_pipeline_curated_metadata_override",
    ]
    assert {row["source_family"] for row in rows[:3]} == {"specialized_covalent_protein_ligand_database"}
    assert {row["source_name_user_configurable"] for row in rows} == {"True"}
    assert {row["source_url_or_access_path_deferred"] for row in rows} == {"True"}
    assert {row["expected_candidate_unit"] for row in rows} == {"covalent_ligand_residue_event"}
    assert {row["source_verification_required"] for row in rows} == {"True"}
    assert {row["current_step_verified"] for row in rows} == {"False"}
    assert {row["contract_passed"] for row in rows} == {"True"}
    assert manifest["external_source_verified_current_step"] is False
    assert manifest["external_network_access_used"] is False
    assert manifest["external_metadata_downloaded"] is False
    assert manifest["raw_structure_downloaded"] is False


def test_contract_row_counts_and_allowlist_mapping() -> None:
    manifest = _manifest()
    assert manifest["covapie_covalent_db_source_acquisition_precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 7
    assert manifest["covapie_covalent_db_field_availability_contract_row_count"] == len(_csv_rows(gate.FIELD_AVAILABILITY_CONTRACT_CSV)) == 15
    assert manifest["covapie_covalent_db_allowlist_schema_mapping_contract_row_count"] == len(_csv_rows(gate.SCHEMA_MAPPING_CONTRACT_CSV)) == 15
    assert manifest["covapie_covalent_event_identity_key_contract_row_count"] == len(_csv_rows(gate.EVENT_IDENTITY_KEY_CONTRACT_CSV)) == 8
    assert manifest["covapie_covalent_db_acquisition_method_contract_row_count"] == len(_csv_rows(gate.ACQUISITION_METHOD_CONTRACT_CSV)) == 8
    assert manifest["covapie_covalent_db_download_boundary_contract_row_count"] == len(_csv_rows(gate.DOWNLOAD_BOUNDARY_CONTRACT_CSV)) == 8
    assert manifest["covapie_covalent_db_provenance_license_contract_row_count"] == len(_csv_rows(gate.PROVENANCE_LICENSE_CONTRACT_CSV)) == 8
    assert manifest["covapie_covalent_db_manual_review_contract_row_count"] == len(_csv_rows(gate.MANUAL_REVIEW_CONTRACT_CSV)) == 8
    assert manifest["covapie_covalent_db_candidate_selection_contract_row_count"] == len(_csv_rows(gate.CANDIDATE_SELECTION_CONTRACT_CSV)) == 12
    assert manifest["covapie_covalent_db_failure_taxonomy_contract_row_count"] == len(_csv_rows(gate.FAILURE_TAXONOMY_CONTRACT_CSV)) == 14
    fields = _csv_rows(gate.FIELD_AVAILABILITY_CONTRACT_CSV)
    mapping = _csv_rows(gate.SCHEMA_MAPPING_CONTRACT_CSV)
    assert [row["allowlist_column"] for row in fields] == gate.ALLOWLIST_COLUMNS
    assert [row["allowlist_column"] for row in mapping] == gate.ALLOWLIST_COLUMNS
    assert {row["acquisition_status_current_step"] for row in fields} == {"design_only_not_verified"}
    assert {row["field_contract_passed"] for row in fields} == {"True"}
    assert {row["mapping_contract_passed"] for row in mapping} == {"True"}
    by_col = {row["allowlist_column"]: row for row in fields}
    assert by_col["candidate_id"]["likely_covapie_generated_field"] == "True"
    assert by_col["pdb_id"]["likely_external_db_direct_field"] == "True"
    assert by_col["manual_review_status"]["manual_review_or_policy_required"] == "True"
    mapping_by_col = {row["allowlist_column"]: row for row in mapping}
    assert "pdb_id" in mapping_by_col["pdb_id"]["external_db_field_candidates"]
    assert "set after local raw download, not before" in mapping_by_col["source_file_relative_path"]["covapie_rule_to_fill"]
    assert "reviewed_pass" in mapping_by_col["manual_review_status"]["covapie_rule_to_fill"]


def test_event_identity_key_prevents_pdb_only_join() -> None:
    manifest = _manifest()
    rows = {row["identity_key_rule"]: row for row in _csv_rows(gate.EVENT_IDENTITY_KEY_CONTRACT_CSV)}
    assert set(rows) == {
        "no_pdb_id_only_join",
        "minimal_event_key",
        "preferred_event_key",
        "ligand_instance_disambiguation",
        "chain_and_residue_disambiguation",
        "bond_pair_disambiguation",
        "multi_event_pdb_handling",
        "ambiguous_event_exclusion",
    }
    assert rows["no_pdb_id_only_join"]["required_fields_or_policy"] == "pdb_id is insufficient"
    minimal = "pdb_id+ligand_id+chain_id+residue_name+residue_index+residue_atom_name"
    preferred = minimal + "+covalent_bond_atom_pair"
    assert rows["minimal_event_key"]["required_fields_or_policy"] == minimal
    assert rows["preferred_event_key"]["required_fields_or_policy"] == preferred
    assert "one covalent ligand-residue event" in rows["minimal_event_key"]["rule_description"]
    assert "one covalent ligand-residue event" in rows["multi_event_pdb_handling"]["rule_description"]
    assert "block materialization" in rows["ambiguous_event_exclusion"]["rule_description"]
    assert {row["contract_passed"] for row in rows.values()} == {"True"}
    assert manifest["event_identity_key_policy"] == "no_pdb_id_only_join"
    assert manifest["minimal_event_key"] == minimal
    assert manifest["preferred_event_key"] == preferred
    assert manifest["one_row_one_covalent_event"] is True


def test_method_download_provenance_review_selection_and_failure_contracts() -> None:
    assert {row["current_step_status"] for row in _csv_rows(gate.ACQUISITION_METHOD_CONTRACT_CSV)} == {"design_only"}
    assert {row["network_or_download_used"] for row in _csv_rows(gate.ACQUISITION_METHOD_CONTRACT_CSV)} == {"False"}
    assert {row["contract_passed"] for row in _csv_rows(gate.ACQUISITION_METHOD_CONTRACT_CSV)} == {"True"}
    assert {row["download_allowed_current_step"] for row in _csv_rows(gate.DOWNLOAD_BOUNDARY_CONTRACT_CSV)} == {"False"}
    assert {row["contract_passed"] for row in _csv_rows(gate.DOWNLOAD_BOUNDARY_CONTRACT_CSV)} == {"True"}
    assert {row["current_step_verified_external_license"] for row in _csv_rows(gate.PROVENANCE_LICENSE_CONTRACT_CSV)} == {"False"}
    assert {row["provenance_contract_passed"] for row in _csv_rows(gate.PROVENANCE_LICENSE_CONTRACT_CSV)} == {"True"}
    assert {row["manual_review_contract_passed"] for row in _csv_rows(gate.MANUAL_REVIEW_CONTRACT_CSV)} == {"True"}
    assert {row["current_step_executed"] for row in _csv_rows(gate.CANDIDATE_SELECTION_CONTRACT_CSV)} == {"False"}
    assert {row["future_selection_required"] for row in _csv_rows(gate.CANDIDATE_SELECTION_CONTRACT_CSV)} == {"True"}
    assert {row["selection_contract_passed"] for row in _csv_rows(gate.CANDIDATE_SELECTION_CONTRACT_CSV)} == {"True"}
    assert {row["failure_taxonomy_passed"] for row in _csv_rows(gate.FAILURE_TAXONOMY_CONTRACT_CSV)} == {"True"}


def test_masks_feature_semantics_and_leakage_boundaries() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    mask = _csv_rows(gate.MASK_SCOPE_AUDIT_CSV)
    assert len(mask) == manifest["covapie_covalent_db_mask_scope_audit_row_count"] == 5
    assert [row["canonical_mask_task_name"] for row in mask] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["source_of_truth_status"] for row in mask} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in mask} == {"display_only"}
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13ai"}
    feature = _csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)
    assert len(feature) == manifest["covapie_covalent_db_feature_semantics_audit_row_count"] == 12
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_covalent_db_source_acquisition_gate"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    leakage = _csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)
    assert len(leakage) == manifest["covapie_covalent_db_leakage_split_audit_row_count"] == 12
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["future_required_gate"] for row in leakage} == {"covapie_leakage_split_design_gate_before_training"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    manifest = _manifest()
    boundary = {row["boundary_item"]: row for row in _csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert len(boundary) == manifest["covapie_covalent_db_execution_boundary_audit_row_count"] == 24
    assert boundary["specialized_covalent_db_source_acquisition_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert boundary["source_registry_contract_write"]["current_step_status"] == "executed_contract_only"
    for item in gate.EXECUTION_BOUNDARY_ITEMS[2:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["execution_boundary_passed"] == "True"
    git_rows = {row["git_safety_item"]: row for row in _csv_rows(gate.GIT_SAFETY_AUDIT_CSV)}
    assert len(git_rows) == manifest["covapie_covalent_db_git_safety_audit_row_count"] == 10
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
        "all_source_registry_contracts_declared",
        "all_field_availability_contracts_declared",
        "all_schema_mapping_contracts_declared",
        "all_event_identity_key_contracts_declared",
        "all_acquisition_method_contracts_declared",
        "all_download_boundary_contracts_declared",
        "all_provenance_license_contracts_declared",
        "all_manual_review_contracts_declared",
        "all_candidate_selection_contracts_declared",
        "all_failure_taxonomy_contracts_declared",
        "specialized_covalent_database_source_acquisition_design_gate_passed",
    ]:
        assert manifest[key] is True
    assert manifest["ready_for_covapie_external_source_registry_configuration"] is False
    assert manifest["ready_for_covapie_external_metadata_index_download_design_gate"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke"] is False
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_external_metadata_index_download_design_gate"
