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

from covalent_ext import covapie_diffsbdd_loader_adapter_implementation_qa_gate as qa


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not qa.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(qa.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def _imports_step13ac(path: Path) -> bool:
    target = "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(target in alias.name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and target in node.module:
            return True
    return False


def test_check_script_passes_and_validates_step13ac_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == qa.STAGE
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ac_diffsbdd_loader_adapter_implementation_smoke_validated"] is True
    assert manifest["historical_step_name_retained"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_covapie_naming_convention_is_validated() -> None:
    text = qa.NAMING_CONVENTION_MD.read_text(encoding="utf-8")
    assert "CovaPIE" in text
    assert "CovaGEN" in text
    assert "New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE" in text
    assert "Historical artifact paths, historical filenames, and historical step names are retained" in text
    assert "`src/covalent_ext/`" in text
    assert "dedicated migration design gate" in text
    assert qa.validate_covapie_naming_convention_v0() is True
    assert _manifest()["naming_convention_validated"] is True


def test_step13ad_does_not_import_torch_or_step13ac_module() -> None:
    module_path = Path("src/covalent_ext/covapie_diffsbdd_loader_adapter_implementation_qa_gate.py")
    script_path = Path("scripts/check_covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0.py")
    assert not _imports_name(module_path, "torch")
    assert not _imports_name(script_path, "torch")
    assert not _imports_step13ac(module_path)
    assert not _imports_step13ac(script_path)


def test_output_row_counts_match_contract() -> None:
    manifest = _manifest()
    assert manifest["covapie_adapter_input_qa_audit_row_count"] == len(_csv_rows(qa.INPUT_QA_AUDIT_CSV)) == 3
    assert manifest["covapie_adapter_sample_dict_qa_audit_row_count"] == len(_csv_rows(qa.SAMPLE_DICT_QA_AUDIT_CSV)) == 3
    assert manifest["covapie_adapter_field_shape_qa_audit_row_count"] == len(_csv_rows(qa.FIELD_SHAPE_QA_AUDIT_CSV)) == 42
    assert manifest["covapie_adapter_single_sample_batch_qa_audit_row_count"] == len(_csv_rows(qa.SINGLE_SAMPLE_BATCH_QA_AUDIT_CSV)) == 3
    assert manifest["covapie_adapter_mask_mapping_qa_audit_row_count"] == len(_csv_rows(qa.MASK_MAPPING_QA_AUDIT_CSV)) == 5
    assert manifest["covapie_adapter_auxiliary_label_qa_audit_row_count"] == len(_csv_rows(qa.AUXILIARY_LABEL_QA_AUDIT_CSV)) == 3
    assert manifest["covapie_adapter_execution_boundary_qa_audit_row_count"] == len(_csv_rows(qa.EXECUTION_BOUNDARY_QA_AUDIT_CSV)) == 19
    assert manifest["covapie_adapter_feature_semantics_qa_audit_row_count"] == len(_csv_rows(qa.FEATURE_SEMANTICS_QA_AUDIT_CSV)) == 12
    assert manifest["covapie_adapter_dependency_qa_audit_row_count"] == len(_csv_rows(qa.DEPENDENCY_QA_AUDIT_CSV)) == 12
    assert manifest["covapie_adapter_source_ast_safety_qa_audit_row_count"] == len(_csv_rows(qa.SOURCE_AST_SAFETY_QA_AUDIT_CSV)) >= 15


def test_input_and_sample_dict_qa_pass_for_three_goldens() -> None:
    input_rows = _csv_rows(qa.INPUT_QA_AUDIT_CSV)
    sample_rows = _csv_rows(qa.SAMPLE_DICT_QA_AUDIT_CSV)
    assert [row["adapter_design_sample_id"] for row in input_rows] == qa.EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS
    assert [row["review_row_id"] for row in input_rows] == qa.EXPECTED_REVIEW_ROW_IDS
    assert [row["pdb_id"] for row in input_rows] == qa.EXPECTED_PDB_IDS
    for key in [
        "input_audit_row_found",
        "expected_identity_validated",
        "cys_sg_scope_validated",
        "ligand_counts_validated",
        "endpoint_counts_validated",
        "canonical_masks_validated",
        "step13ac_input_audit_passed",
        "qa_passed",
    ]:
        assert {row[key] for row in input_rows} == {"True"}
    assert {row["blocking_reasons"] for row in input_rows} == {""}
    assert {row["adapter_sample_built"] for row in sample_rows} == {"True"}
    assert {row["metadata_present"] for row in sample_rows} == {"True"}
    assert {row["adapter_fields_present"] for row in sample_rows} == {"True"}
    assert {row["adapter_field_count"] for row in sample_rows} == {"14"}
    assert {row["canonical_mask_task_count"] for row in sample_rows} == {"5"}
    assert {row["auxiliary_label_count"] for row in sample_rows} == {"3"}
    assert {row["step13ac_sample_dict_audit_passed"] for row in sample_rows} == {"True"}
    assert {row["qa_passed"] for row in sample_rows} == {"True"}


def test_field_shape_qa_validates_42_transient_observations() -> None:
    rows = _csv_rows(qa.FIELD_SHAPE_QA_AUDIT_CSV)
    assert len(rows) == 42
    assert len({(row["adapter_design_sample_id"], row["covalent_shape_item"]) for row in rows}) == 42
    assert {row["tensor_created_in_step13ac"] for row in rows} == {"True"}
    assert {row["tensor_persisted"] for row in rows} == {"False"}
    assert {row["field_shape_observation_passed_in_step13ac"] for row in rows} == {"True"}
    assert {row["expected_shape_validated"] for row in rows} == {"True"}
    assert {row["qa_passed"] for row in rows} == {"True"}
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
    for review_id in qa.EXPECTED_REVIEW_ROW_IDS:
        assert by_review_shape[(review_id, "canonical_mask_task_id_or_name")] == [1]


def test_batch_mask_auxiliary_and_execution_boundaries_pass() -> None:
    batch_rows = _csv_rows(qa.SINGLE_SAMPLE_BATCH_QA_AUDIT_CSV)
    mask_rows = _csv_rows(qa.MASK_MAPPING_QA_AUDIT_CSV)
    aux_rows = _csv_rows(qa.AUXILIARY_LABEL_QA_AUDIT_CSV)
    boundary_rows = _csv_rows(qa.EXECUTION_BOUNDARY_QA_AUDIT_CSV)
    assert [int(row["batch_index"]) for row in batch_rows] == [0, 1, 2]
    assert {row["batch_size"] for row in batch_rows} == {"1"}
    assert {row["collate_status"] for row in batch_rows} == {"external_adapter_single_sample_collate_no_padding_no_training"}
    for key in ["adapter_batch_built", "batch_shape_checked", "batch_order_validated", "single_sample_batch_audit_passed", "qa_passed"]:
        assert {row[key] for row in batch_rows} == {"True"}
    for key in ["model_forward_called", "loss_compute_called", "backward_called", "optimizer_step_called", "training_step_called"]:
        assert {row[key] for row in batch_rows} == {"False"}
    assert [row["canonical_mask_task_name"] for row in mask_rows] == qa.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask_rows] == qa.CANONICAL_MASK_TASK_ALIASES
    assert {row["source_of_truth_status"] for row in mask_rows} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in mask_rows} == {"display_only"}
    assert {row["adapter_mask_carried"] for row in mask_rows} == {"True"}
    assert {row["tensor_mask_persisted"] for row in mask_rows} == {"False"}
    assert {row["qa_passed"] for row in mask_rows} == {"True"}
    assert [row["auxiliary_label_name"] for row in aux_rows] == [
        "warhead_type",
        "ligand_residue_atom_pair",
        "pre_post_covalent_geometry",
    ]
    assert {row["adapter_label_carried"] for row in aux_rows} == {"True"}
    assert {row["future_loss_integration_status"] for row in aux_rows} == {"not_integrated_into_loss"}
    assert {row["loss_integration_performed"] for row in aux_rows} == {"False"}
    assert {row["qa_passed"] for row in aux_rows} == {"True"}
    by_item = {row["boundary_item"]: row for row in boundary_rows}
    assert by_item["adapter_implementation"]["observed_current_step_status"] == "executed_external_covalent_ext_smoke_only"
    assert by_item["torch_import"]["observed_current_step_status"] == "executed_for_transient_shape_smoke"
    assert by_item["tensor_creation"]["observed_current_step_status"] == "executed_transient_in_memory_only"
    for item in [
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
    assert {row["qa_passed"] for row in boundary_rows} == {"True"}


def test_feature_dependency_and_source_ast_qa_pass() -> None:
    feature_rows = _csv_rows(qa.FEATURE_SEMANTICS_QA_AUDIT_CSV)
    dep_rows = _csv_rows(qa.DEPENDENCY_QA_AUDIT_CSV)
    ast_rows = _csv_rows(qa.SOURCE_AST_SAFETY_QA_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature_rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature_rows} == {"False"}
    assert {row["training_ready"] for row in feature_rows} == {"False"}
    assert {row["qa_passed"] for row in feature_rows} == {"True"}
    assert [row["dependency_name"] for row in dep_rows] == [
        "step13ac_manifest",
        "step13ac_input_audit",
        "step13ac_sample_dict_audit",
        "step13ac_field_shape_observation",
        "step13ac_single_sample_batch_audit",
        "step13ac_mask_mapping_audit",
        "step13ac_auxiliary_label_audit",
        "step13ac_execution_boundary_audit",
        "step13ac_feature_semantics_audit",
        "step13ac_dependency_audit",
        "step13ac_report",
        "covapie_naming_convention_doc",
    ]
    assert {row["dependency_exists"] for row in dep_rows} == {"True"}
    assert {row["dependency_count_validated"] for row in dep_rows} == {"True"}
    assert {row["dependency_qa_passed"] for row in dep_rows} == {"True"}
    assert len(ast_rows) >= 15
    assert {row["qa_passed"] for row in ast_rows} == {"True"}
    by_item = {row["safety_item"]: row for row in ast_rows}
    assert by_item["step13ac_module_imports_torch_allowed_in_step13ac"]["observed_status"] == "imports_torch"
    assert by_item["step13ad_module_does_not_import_torch"]["observed_status"] == "no_torch_import"
    assert by_item["step13ad_check_script_does_not_import_torch"]["observed_status"] == "no_torch_import"
    assert by_item["step13ad_module_does_not_import_step13ac_module"]["observed_status"] == "no_step13ac_module_import"


def test_manifest_records_step13ac_carryover_and_current_step_safety() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_names"] == qa.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == qa.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    for key in [
        "adapter_implemented_in_step13ac",
        "adapter_instantiated_in_step13ac",
        "torch_imported_in_step13ac",
        "torch_tensor_created_in_step13ac",
        "transient_adapter_field_shape_inspection_performed_in_step13ac",
        "diffsbdd_loader_adapter_implementation_smoke_passed_in_step13ac",
        "all_input_qa_passed",
        "all_sample_dict_qa_passed",
        "all_field_shape_qa_passed",
        "all_single_sample_batch_qa_passed",
        "all_mask_mapping_qa_passed",
        "all_auxiliary_label_qa_passed",
        "all_execution_boundary_qa_passed",
        "all_feature_semantics_qa_passed",
        "all_dependency_qa_passed",
        "all_source_ast_safety_qa_passed",
        "all_feature_semantics_audit_required_before_training",
        "no_feature_semantics_claimed_fully_audited",
        "checkpoint_compatibility_preserved_by_external_adapter",
        "covapie_adapter_implementation_qa_gate_passed",
    ]:
        assert manifest[key] is True
    false_keys = [
        "adapter_implemented",
        "adapter_instantiated",
        "torch_imported",
        "torch_tensor_created",
        "transient_adapter_field_shape_inspection_performed",
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
        "rdkit_used",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "raw_files_read",
        "gzip_open_used",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        "gemmi_used",
        "original_diffsbdd_source_modified",
        "original_diffsbdd_dataloader_modified",
        "original_diffsbdd_forward_modified",
        "original_diffsbdd_loss_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["ready_for_covapie_batch_scale_data_preparation_design_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_batch_scale_data_preparation_design_gate"


def test_no_forbidden_artifacts_or_protected_diffs() -> None:
    assert not any(
        path.is_file() and path.suffix in qa.FORBIDDEN_COMMITTABLE_SUFFIXES for path in qa.OUTPUT_ROOT.rglob("*")
    )
    protected = subprocess.run(
        ["git", "diff", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
    )
    dataloader = subprocess.run(
        ["git", "diff", "--", "dataset.py", "data/prepare_crossdocked.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
    )
    raw_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
    )
    raw_tracked = subprocess.run(
        ["git", "ls-files", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
    )
    assert protected.stdout == ""
    assert dataloader.stdout == ""
    assert raw_staged.stdout == ""
    assert raw_tracked.stdout == ""
