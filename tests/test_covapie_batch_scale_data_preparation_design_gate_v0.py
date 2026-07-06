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

from covalent_ext import covapie_batch_scale_data_preparation_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_batch_scale_data_preparation_design_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13ad_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_batch_scale_data_preparation_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ad_covapie_adapter_implementation_qa_gate_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_covapie_naming_convention_is_validated() -> None:
    text = gate.NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    assert "CovaPIE" in text
    assert "CovaGEN" in text
    assert "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE" in text
    assert "Historical artifact paths, historical filenames, and historical step names are retained" in text
    assert "`src/covalent_ext/`" in text
    assert "dedicated migration design gate" in text
    assert gate.validate_covapie_naming_convention_v0() is True


def test_output_row_counts_match_contract() -> None:
    manifest = _manifest()
    assert manifest["covapie_batch_scale_precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 6
    assert manifest["covapie_batch_scale_input_source_contract_row_count"] == len(_csv_rows(gate.INPUT_SOURCE_CONTRACT_CSV)) == 8
    assert manifest["covapie_batch_scale_candidate_selection_contract_row_count"] == len(_csv_rows(gate.CANDIDATE_SELECTION_CONTRACT_CSV)) == 12
    assert manifest["covapie_batch_scale_sharding_contract_row_count"] == len(_csv_rows(gate.SHARDING_CONTRACT_CSV)) == 7
    assert manifest["covapie_batch_scale_failure_taxonomy_contract_row_count"] == len(_csv_rows(gate.FAILURE_TAXONOMY_CONTRACT_CSV)) == 18
    assert manifest["covapie_batch_scale_provenance_contract_row_count"] == len(_csv_rows(gate.PROVENANCE_CONTRACT_CSV)) == 14
    assert manifest["covapie_batch_scale_output_artifact_contract_row_count"] == len(_csv_rows(gate.OUTPUT_ARTIFACT_CONTRACT_CSV)) == 12
    assert manifest["covapie_batch_scale_git_safety_contract_row_count"] == len(_csv_rows(gate.GIT_SAFETY_CONTRACT_CSV)) == 10
    assert manifest["covapie_batch_scale_mask_scope_contract_row_count"] == len(_csv_rows(gate.MASK_SCOPE_CONTRACT_CSV)) == 5
    assert manifest["covapie_batch_scale_feature_semantics_boundary_row_count"] == len(_csv_rows(gate.FEATURE_SEMANTICS_BOUNDARY_CSV)) == 12
    assert manifest["covapie_batch_scale_leakage_split_placeholder_contract_row_count"] == len(_csv_rows(gate.LEAKAGE_SPLIT_PLACEHOLDER_CONTRACT_CSV)) == 12
    assert manifest["covapie_batch_scale_execution_boundary_contract_row_count"] == len(_csv_rows(gate.EXECUTION_BOUNDARY_CONTRACT_CSV)) == 24


def test_candidate_selection_sharding_and_failure_taxonomy_contracts() -> None:
    selection = {row["selection_rule"]: row for row in _csv_rows(gate.CANDIDATE_SELECTION_CONTRACT_CSV)}
    assert selection["max_candidate_count_initial_smoke"]["rule_value"] == "30"
    assert selection["min_candidate_count_initial_smoke"]["rule_value"] == "10"
    assert selection["cys_sg_only_scope"]["rule_value"] == "true"
    assert selection["known_restoration_template_required"]["rule_value"] == "true"
    assert selection["non_cys_excluded_current_phase"]["future_batch_smoke_policy"] == "exclude_non_cys"
    assert {row["design_contract_passed"] for row in selection.values()} == {"True"}

    sharding = {row["sharding_item"]: row for row in _csv_rows(gate.SHARDING_CONTRACT_CSV)}
    assert sharding["shard_size_initial_smoke"]["rule_value"] == "5"
    assert sharding["single_sample_failure_isolation"]["rule_value"] == "true"
    assert sharding["partial_success_allowed"]["rule_value"] == "true"
    assert sharding["deterministic_sample_order"]["rule_value"] == "true"
    assert {row["design_contract_passed"] for row in sharding.values()} == {"True"}

    failure_codes = [row["failure_code"] for row in _csv_rows(gate.FAILURE_TAXONOMY_CONTRACT_CSV)]
    assert failure_codes == [
        "missing_raw_structure",
        "unreadable_structure",
        "unsupported_file_format",
        "missing_reactive_residue",
        "missing_reactive_residue_atom",
        "non_cys_residue_currently_blocked",
        "missing_ligand",
        "multiple_ligands_ambiguous",
        "missing_covalent_bond_evidence",
        "missing_ligand_topology_evidence",
        "ligand_atom_count_mismatch",
        "ligand_bond_count_mismatch",
        "missing_warhead_group",
        "missing_linker_group",
        "missing_scaffold_group",
        "invalid_canonical_mask_set",
        "feature_semantics_unknown",
        "unexpected_exception",
    ]


def test_mask_scope_and_feature_semantics_boundaries() -> None:
    mask_rows = _csv_rows(gate.MASK_SCOPE_CONTRACT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask_rows] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask_rows] == gate.CANONICAL_MASK_TASK_ALIASES
    assert gate.CANONICAL_MASK_TASK_NAMES[3] == "scaffold_only"
    assert gate.CANONICAL_MASK_TASK_ALIASES[3] == "B3"
    assert {row["source_of_truth_status"] for row in mask_rows} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in mask_rows} == {"display_only"}
    assert {row["no_extra_mask_tasks_added"] for row in mask_rows} == {"True"}
    assert len(mask_rows) == 5

    feature_rows = _csv_rows(gate.FEATURE_SEMANTICS_BOUNDARY_CSV)
    assert len(feature_rows) == 12
    assert {row["audit_required_before_training"] for row in feature_rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature_rows} == {"False"}
    assert {row["blocking_for_batch_scale_design_gate"] for row in feature_rows} == {"False"}
    assert {row["training_ready"] for row in feature_rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in feature_rows)


def test_provenance_output_git_and_leakage_contracts() -> None:
    provenance_fields = [row["provenance_field"] for row in _csv_rows(gate.PROVENANCE_CONTRACT_CSV)]
    assert provenance_fields == [
        "source_dataset_name",
        "source_dataset_version",
        "source_file_path",
        "source_file_checksum_placeholder",
        "pdb_id",
        "ligand_id",
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "covalent_bond_atom_pair",
        "extraction_step_id",
        "restoration_policy_id",
        "manual_review_status",
    ]
    assert {row["design_contract_passed"] for row in _csv_rows(gate.PROVENANCE_CONTRACT_CSV)} == {"True"}

    output_rows = {row["output_item"]: row for row in _csv_rows(gate.OUTPUT_ARTIFACT_CONTRACT_CSV)}
    assert output_rows["no_raw_copy_artifacts"]["file_type_policy"] == "forbid_raw_copy"
    assert output_rows["no_pt_npz_artifacts"]["file_type_policy"] == "forbid_pt_npz"
    assert output_rows["no_tensor_artifacts"]["file_type_policy"] == "no_tensor_files"
    assert output_rows["no_sdf_pdb_cif_generated_current_design"]["allowed_future_smoke"] == "False"

    git_rows = {row["git_safety_item"]: row for row in _csv_rows(gate.GIT_SAFETY_CONTRACT_CSV)}
    assert ".pt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".npz" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert git_rows["raw_directory_not_staged"]["required_status"] == "empty"
    assert git_rows["raw_directory_not_tracked"]["required_status"] == "empty"

    leakage = {row["leakage_or_split_item"]: row for row in _csv_rows(gate.LEAKAGE_SPLIT_PLACEHOLDER_CONTRACT_CSV)}
    assert leakage["no_split_written_current_step"]["current_step_status"] == "placeholder_only_no_split_written"
    assert leakage["no_leakage_matrix_written_current_step"]["current_step_status"] == "placeholder_only_no_split_written"
    assert leakage["future_split_design_gate_required"]["future_required_gate"] == "covapie_leakage_split_design_gate_before_training"
    assert {row["blocking_for_training"] for row in leakage.values()} == {"True"}


def test_execution_boundary_forbids_execution_training_and_raw_access() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(gate.EXECUTION_BOUNDARY_CONTRACT_CSV)}
    assert boundary["batch_scale_design_only"]["current_step_status"] == "executed_design_only"
    for item in [
        "raw_data_read",
        "raw_file_copy",
        "sdf_read",
        "sdf_write",
        "pdb_read",
        "pdb_write",
        "mmcif_read",
        "gzip_open",
        "rdkit_use",
        "biopdb_use",
        "gemmi_use",
        "atom_site_scan",
        "candidate_materialization",
        "sample_index_write",
        "final_dataset_write",
        "adapter_instantiation",
        "torch_import",
        "tensor_creation",
        "checkpoint_load",
        "model_forward",
        "loss_compute",
        "trainer_fit",
        "training_claim",
    ]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["forbidden_current_step"] == "True"
    assert {row["design_contract_passed"] for row in boundary.values()} == {"True"}


def test_manifest_readiness_and_current_step_safety_boundary() -> None:
    manifest = _manifest()
    for key in [
        "all_preconditions_validated",
        "all_input_source_contracts_declared",
        "all_candidate_selection_contracts_declared",
        "all_sharding_contracts_declared",
        "all_failure_taxonomy_contracts_declared",
        "all_provenance_contracts_declared",
        "all_output_artifact_contracts_declared",
        "all_git_safety_contracts_declared",
        "all_mask_scope_contracts_declared",
        "all_feature_semantics_boundaries_declared",
        "all_leakage_split_placeholders_declared",
        "all_execution_boundaries_declared",
        "batch_scale_design_gate_passed",
    ]:
        assert manifest[key] is True
    assert manifest["batch_scale_initial_min_candidate_count"] == 10
    assert manifest["batch_scale_initial_max_candidate_count"] == 30
    assert manifest["batch_scale_initial_shard_size"] == 5
    assert manifest["current_reactive_residue_scope"] == "cys_sg_only"
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["checkpoint_compatibility_policy"] == "preserve_diffsbdd_checkpoint_compatibility_by_external_adapter_only"
    assert manifest["ready_for_covapie_batch_scale_data_preparation_smoke"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_batch_scale_data_preparation_smoke"
    for key in [
        "batch_scale_smoke_executed",
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
        "candidate_materialized",
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
        "original_diffsbdd_source_modified",
        "original_diffsbdd_dataloader_modified",
        "original_diffsbdd_forward_modified",
        "original_diffsbdd_loss_modified",
    ]:
        assert manifest[key] is False


def test_no_runtime_library_imports_or_forbidden_artifacts() -> None:
    module_path = Path("src/covalent_ext/covapie_batch_scale_data_preparation_design_gate.py")
    script_path = Path("scripts/check_covapie_batch_scale_data_preparation_design_gate_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden_suffixes = {
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".pdb",
        ".cif",
        ".mmcif",
        ".sdf",
        ".mol2",
        ".gz",
    }
    assert not [
        path
        for path in gate.OUTPUT_ROOT.rglob("*")
        if path.is_file() and any(str(path).endswith(suffix) for suffix in forbidden_suffixes)
    ]
    assert subprocess.run(["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"]).returncode == 0
    assert subprocess.run(["git", "diff", "--quiet", "--", "src/DiffSBDD/", "src/diffsbdd/", "DiffSBDD/"]).returncode == 0
    assert subprocess.run(["git", "diff", "--cached", "--quiet", "--", "data/raw/covalent_sources"]).returncode == 0
