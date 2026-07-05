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

from covalent_ext import (  # noqa: E402
    real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke as smoke,
)


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/check_real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0.py",
        ],
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


def test_check_script_passes_and_validates_step13ab_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13ab_diffsbdd_loader_adapter_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_external_adapter_class_builds_three_smoke_samples_only() -> None:
    smoke.validate_step13ab_precondition_v0()
    adapter = smoke.RealCovalentDiffSBDDLoaderAdapter(
        _csv_rows(smoke.STEP13AB_INPUT_CONTRACT_CSV),
        _csv_rows(smoke.STEP13AB_SHAPE_MAPPING_CONTRACT_CSV),
        _csv_rows(smoke.STEP13AB_MASK_MAPPING_CONTRACT_CSV),
        _csv_rows(smoke.STEP13AB_AUXILIARY_LABEL_CONTRACT_CSV),
    )
    assert len(adapter) == 3
    sample = adapter.get_sample(0)
    assert set(sample) == {
        "metadata",
        "adapter_fields",
        "canonical_mask_tasks",
        "auxiliary_labels",
        "implementation_status",
    }
    assert sample["implementation_status"] == "external_covalent_ext_adapter_smoke_only"
    assert len(sample["adapter_fields"]) == 14
    assert len(sample["canonical_mask_tasks"]) == 5
    assert len(sample["auxiliary_labels"]) == 3
    assert list(sample["adapter_fields"]["diffsbdd_ligand_atom_positions"].shape) == [33, 3]
    assert list(sample["adapter_fields"]["diffsbdd_ligand_bond_index"].shape) == [2, 35]
    batch = smoke.collate_single_sample(sample)
    assert batch["batch_size"] == 1
    assert batch["collate_status"] == "external_adapter_single_sample_collate_no_padding_no_training"
    assert len(batch["adapter_fields"]) == 14


def test_audit_outputs_have_expected_row_counts_and_ids() -> None:
    manifest = _manifest()
    input_rows = _csv_rows(smoke.INPUT_AUDIT_CSV)
    sample_rows = _csv_rows(smoke.SAMPLE_DICT_AUDIT_CSV)
    shape_rows = _csv_rows(smoke.FIELD_SHAPE_OBSERVATION_CSV)
    batch_rows = _csv_rows(smoke.SINGLE_SAMPLE_BATCH_AUDIT_CSV)
    mask_rows = _csv_rows(smoke.MASK_MAPPING_AUDIT_CSV)
    aux_rows = _csv_rows(smoke.AUXILIARY_LABEL_AUDIT_CSV)
    boundary_rows = _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)
    feature_rows = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    dep_rows = _csv_rows(smoke.DEPENDENCY_AUDIT_CSV)
    assert manifest["diffsbdd_loader_adapter_input_audit_row_count"] == len(input_rows) == 3
    assert manifest["diffsbdd_loader_adapter_sample_dict_audit_row_count"] == len(sample_rows) == 3
    assert manifest["diffsbdd_loader_adapter_field_shape_observation_row_count"] == len(shape_rows) == 42
    assert manifest["diffsbdd_loader_adapter_single_sample_batch_audit_row_count"] == len(batch_rows) == 3
    assert manifest["diffsbdd_loader_adapter_mask_mapping_audit_row_count"] == len(mask_rows) == 5
    assert manifest["diffsbdd_loader_adapter_auxiliary_label_audit_row_count"] == len(aux_rows) == 3
    assert manifest["diffsbdd_loader_adapter_execution_boundary_audit_row_count"] == len(boundary_rows) == 19
    assert manifest["diffsbdd_loader_adapter_feature_semantics_audit_row_count"] == len(feature_rows) == 12
    assert manifest["diffsbdd_loader_adapter_dependency_audit_row_count"] == len(dep_rows) == 8
    assert [row["adapter_design_sample_id"] for row in input_rows] == smoke.EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS
    assert [row["review_row_id"] for row in input_rows] == smoke.EXPECTED_REVIEW_ROW_IDS
    assert [row["pdb_id"] for row in input_rows] == smoke.EXPECTED_PDB_IDS


def test_input_audit_validates_cys_sg_counts_endpoints_and_masks() -> None:
    rows = _csv_rows(smoke.INPUT_AUDIT_CSV)
    assert {
        row["review_row_id"]: (row["pdb_id"], row["adapter_design_sample_id"])
        for row in rows
    } == {
        "HR_0002": ("6DI9", "DSBDD_ADAPTER_DESIGN_000001"),
        "HR_0003": ("5F2E", "DSBDD_ADAPTER_DESIGN_000002"),
        "HR_0004": ("6OIM", "DSBDD_ADAPTER_DESIGN_000003"),
    }
    expected_counts = smoke.EXPECTED_ATOM_BOND_COUNTS
    source_rows = _csv_rows(smoke.STEP13AB_INPUT_CONTRACT_CSV)
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in source_rows
    } == expected_counts
    for key in [
        "adapter_input_row_found",
        "cys_sg_scope_validated",
        "ligand_counts_validated",
        "endpoint_counts_validated",
        "canonical_masks_validated",
        "adapter_input_audit_passed",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}


def test_sample_dict_and_single_sample_batches_are_smoke_only() -> None:
    sample_rows = _csv_rows(smoke.SAMPLE_DICT_AUDIT_CSV)
    batch_rows = _csv_rows(smoke.SINGLE_SAMPLE_BATCH_AUDIT_CSV)
    assert {row["adapter_sample_built"] for row in sample_rows} == {"True"}
    assert {row["metadata_present"] for row in sample_rows} == {"True"}
    assert {row["adapter_fields_present"] for row in sample_rows} == {"True"}
    assert {row["adapter_field_count"] for row in sample_rows} == {"14"}
    assert {row["canonical_mask_task_count"] for row in sample_rows} == {"5"}
    assert {row["auxiliary_label_count"] for row in sample_rows} == {"3"}
    assert {row["adapter_output_sample_dict_status"] for row in sample_rows} == {
        "external_adapter_smoke_only_not_training_input"
    }
    assert {row["adapter_sample_dict_audit_passed"] for row in sample_rows} == {"True"}
    assert [int(row["batch_index"]) for row in batch_rows] == [0, 1, 2]
    assert {row["batch_size"] for row in batch_rows} == {"1"}
    assert {row["collate_status"] for row in batch_rows} == {
        "external_adapter_single_sample_collate_no_padding_no_training"
    }
    assert {row["batch_field_count"] for row in batch_rows} == {"14"}
    for key in ["adapter_batch_built", "batch_shape_checked", "batch_order_validated", "single_sample_batch_audit_passed"]:
        assert {row[key] for row in batch_rows} == {"True"}
    for key in ["model_forward_called", "loss_compute_called", "backward_called", "optimizer_step_called", "training_step_called"]:
        assert {row[key] for row in batch_rows} == {"False"}


def test_field_shape_observations_are_transient_and_expected() -> None:
    rows = _csv_rows(smoke.FIELD_SHAPE_OBSERVATION_CSV)
    assert len(rows) == 42
    assert {row["tensor_created"] for row in rows} == {"True"}
    assert {row["tensor_persisted"] for row in rows} == {"False"}
    assert {row["field_shape_observation_status"] for row in rows} == {
        "observed_in_external_adapter_implementation_smoke"
    }
    assert {row["field_shape_observation_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    by_review_shape = {
        (row["review_row_id"], row["covalent_shape_item"]): json.loads(row["observed_shape"])
        for row in rows
    }
    assert by_review_shape[("HR_0002", "ligand_atom_coordinates")] == [33, 3]
    assert by_review_shape[("HR_0002", "ligand_bond_index")] == [2, 35]
    assert by_review_shape[("HR_0003", "ligand_atom_coordinates")] == [30, 3]
    assert by_review_shape[("HR_0003", "ligand_bond_index")] == [2, 33]
    assert by_review_shape[("HR_0004", "ligand_atom_coordinates")] == [41, 3]
    assert by_review_shape[("HR_0004", "ligand_bond_index")] == [2, 45]
    for review_id in smoke.EXPECTED_REVIEW_ROW_IDS:
        assert by_review_shape[(review_id, "canonical_mask_task_id_or_name")] == [1]


def test_mask_and_auxiliary_label_audits_preserve_boundaries() -> None:
    manifest = _manifest()
    mask_rows = _csv_rows(smoke.MASK_MAPPING_AUDIT_CSV)
    aux_rows = _csv_rows(smoke.AUXILIARY_LABEL_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask_rows] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask_rows] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert {row["source_of_truth_status"] for row in mask_rows} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in mask_rows} == {"display_only"}
    assert {row["adapter_mask_carried"] for row in mask_rows} == {"True"}
    assert {row["tensor_mask_persisted"] for row in mask_rows} == {"False"}
    assert {row["implementation_status"] for row in mask_rows} == {"implemented_in_external_adapter_smoke_only"}
    assert {row["training_use_status"] for row in mask_rows} == {"not_training_input_yet"}
    assert {row["mask_mapping_audit_passed"] for row in mask_rows} == {"True"}
    assert [row["auxiliary_label_name"] for row in aux_rows] == [
        "warhead_type",
        "ligand_residue_atom_pair",
        "pre_post_covalent_geometry",
    ]
    assert {row["adapter_label_carried"] for row in aux_rows} == {"True"}
    assert {row["future_loss_integration_status"] for row in aux_rows} == {"not_integrated_into_loss"}
    assert {row["loss_integration_performed"] for row in aux_rows} == {"False"}
    assert {row["feature_semantics_audit_required_before_training"] for row in aux_rows} == {"True"}
    assert {row["auxiliary_label_audit_passed"] for row in aux_rows} == {"True"}
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_execution_boundary_forbids_model_training_artifacts_and_source_changes() -> None:
    rows = _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)
    by_item = {row["boundary_item"]: row for row in rows}
    assert by_item["adapter_implementation"]["observed_current_step_status"] == "executed_external_covalent_ext_smoke_only"
    assert by_item["adapter_instantiation"]["observed_current_step_status"] == "executed_external_covalent_ext_smoke_only"
    assert by_item["torch_import"]["observed_current_step_status"] == "executed_for_transient_shape_smoke"
    assert by_item["tensor_creation"]["observed_current_step_status"] == "executed_transient_in_memory_only"
    assert by_item["single_sample_collate"]["observed_current_step_status"] == "executed_external_adapter_single_sample_only"
    for item in [
        "original_diffsbdd_source_modification",
        "dataloader_modification",
        "model_forward_call",
        "loss_compute",
        "backward_call",
        "optimizer_creation",
        "trainer_fit",
        "checkpoint_load",
        "checkpoint_save",
        "pt_npz_artifact_creation",
        "rdkit_or_sdf_access",
        "raw_mmcif_access",
        "training_claim",
    ]:
        assert by_item[item]["observed_current_step_status"] == "not_executed_or_not_allowed"
    assert by_item["feature_semantics_audit"]["observed_current_step_status"] == "required_before_training_not_completed"
    for key in [
        "boundary_respected",
        "training_forbidden_respected",
        "artifact_forbidden_respected",
        "original_source_protection_respected",
        "boundary_audit_passed",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}


def test_feature_semantics_and_dependency_audits_pass_without_training_claims() -> None:
    feature_rows = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    dep_rows = _csv_rows(smoke.DEPENDENCY_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature_rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature_rows} == {"False"}
    assert {row["blocking_for_adapter_implementation_smoke"] for row in feature_rows} == {"False"}
    assert {row["training_ready"] for row in feature_rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in feature_rows)
    assert {row["feature_semantics_adapter_smoke_audit_passed"] for row in feature_rows} == {"True"}
    assert [row["dependency_name"] for row in dep_rows] == [
        "step13ab_manifest",
        "step13ab_input_contract",
        "step13ab_shape_mapping_contract",
        "step13ab_mask_mapping_contract",
        "step13ab_auxiliary_label_contract",
        "step13ab_execution_boundary_contract",
        "step13ab_feature_semantics_boundary",
        "step13aa_manifest",
    ]
    assert {row["dependency_exists"] for row in dep_rows} == {"True"}
    assert {row["dependency_count_validated"] for row in dep_rows} == {"True"}
    assert {row["dependency_audit_passed"] for row in dep_rows} == {"True"}


def test_manifest_records_adapter_smoke_success_and_safety_boundary() -> None:
    manifest = _manifest()
    for key in [
        "adapter_implemented",
        "adapter_instantiated",
        "torch_imported",
        "torch_tensor_created",
        "transient_adapter_field_shape_inspection_performed",
        "all_adapter_input_audits_passed",
        "all_adapter_sample_dict_audits_passed",
        "all_adapter_field_shape_observations_passed",
        "all_adapter_single_sample_batch_audits_passed",
        "all_mask_mapping_audits_passed",
        "all_auxiliary_label_audits_passed",
        "all_execution_boundaries_respected",
        "all_dependency_artifacts_exist",
        "all_dependency_counts_validated",
        "all_feature_semantics_audit_required_before_training",
        "no_feature_semantics_claimed_fully_audited",
        "checkpoint_compatibility_preserved_by_external_adapter",
        "diffsbdd_loader_adapter_implementation_smoke_passed",
    ]:
        assert manifest[key] is True
    assert manifest["adapter_module_location"] == "src/covalent_ext/"
    assert manifest["adapter_sample_count"] == 3
    assert manifest["adapter_output_field_count"] == 14
    assert manifest["adapter_single_sample_batch_count"] == 3
    false_keys = [
        "original_diffsbdd_source_modified",
        "original_diffsbdd_dataloader_modified",
        "original_diffsbdd_forward_modified",
        "original_diffsbdd_loss_modified",
        "tensor_artifact_written",
        "tensor_dump_saved",
        "npz_created",
        "pt_created",
        "checkpoint_loaded",
        "checkpoint_saved",
        "model_saved",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "training_ready_samples_claimed",
        "sample_index_written",
        "sample_index_modified",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_smoke_modified",
        "model_input_materialized",
        "model_input_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "rdkit_used",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "non_cys_generalization_run",
        "raw_files_read",
        "gzip_open_used",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        "gemmi_used",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["ready_for_diffsbdd_loader_adapter_implementation_qa_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_qa_gate"


def test_no_forbidden_suffix_artifacts_or_protected_source_diff() -> None:
    forbidden_suffixes = smoke.FORBIDDEN_COMMITTABLE_SUFFIXES
    assert not any(path.is_file() and path.suffix in forbidden_suffixes for path in smoke.OUTPUT_ROOT.rglob("*"))
    protected_diff = subprocess.run(
        ["git", "diff", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    protected_cached_diff = subprocess.run(
        ["git", "diff", "--cached", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_tracked = subprocess.run(
        ["git", "ls-files", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert protected_diff.stdout == ""
    assert protected_cached_diff.stdout == ""
    assert raw_staged.stdout == ""
    assert raw_tracked.stdout == ""


def test_module_ast_does_not_call_forbidden_training_or_io_apis() -> None:
    tree = ast.parse(smoke.Path(__file__).parents[1].joinpath("src/covalent_ext/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke.py").read_text())
    forbidden_calls = {
        "save",
        "load",
        "load_from_checkpoint",
        "backward",
        "fit",
        "step",
        "SanitizeMol",
        "SDMolSupplier",
        "MolFromMolFile",
        "MolToMolFile",
    }
    forbidden_modules = {"rdkit", "gzip", "gemmi"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] not in forbidden_modules for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
            elif isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
