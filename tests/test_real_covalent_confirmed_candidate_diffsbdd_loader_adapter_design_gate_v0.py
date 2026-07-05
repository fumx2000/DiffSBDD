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

from covalent_ext import real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13aa_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13aa_loader_shape_dry_run_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_input_contract_has_three_expected_cys_sg_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.INPUT_CONTRACT_CSV)
    assert manifest["diffsbdd_loader_adapter_input_contract_written"] is True
    assert manifest["diffsbdd_loader_adapter_input_contract_row_count"] == len(rows) == 3
    assert [row["adapter_design_sample_id"] for row in rows] == gate.EXPECTED_ADAPTER_DESIGN_SAMPLE_IDS
    assert [row["loader_shape_dry_run_sample_id"] for row in rows] == gate.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS
    assert [row["model_input_smoke_row_id"] for row in rows] == gate.EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
    assert [row["sample_index_row_id"] for row in rows] == gate.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == gate.EXPECTED_REVIEW_ROW_IDS
    assert [row["pdb_id"] for row in rows] == gate.EXPECTED_PDB_IDS
    assert {row["residue_name"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in rows
    } == gate.EXPECTED_ATOM_BOND_COUNTS
    assert {row["endpoint_atom_count"] for row in rows} == {"1"}
    assert {row["endpoint_touching_bond_count"] for row in rows} == {"1"}
    assert {row["canonical_mask_task_names"] for row in rows} == {";".join(gate.CANONICAL_MASK_TASK_NAMES)}
    assert {row["canonical_mask_task_aliases"] for row in rows} == {";".join(gate.CANONICAL_MASK_TASK_ALIASES)}
    assert {row["mask_task_count"] for row in rows} == {"5"}
    assert {row["adapter_input_status"] for row in rows} == {"design_only_from_validated_loader_shape_smoke"}
    assert {row["adapter_implementation_status"] for row in rows} == {"not_implemented"}
    assert {row["tensor_artifact_status"] for row in rows} == {"not_written"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert {row["feature_semantics_audit_required_before_training"] for row in rows} == {"True"}
    assert manifest["all_adapter_input_rows_validated"] is True


def test_source_discovery_is_read_only_and_marks_protected_sources() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.SOURCE_DISCOVERY_AUDIT_CSV)
    assert manifest["diffsbdd_loader_adapter_source_discovery_audit_written"] is True
    assert manifest["diffsbdd_loader_adapter_source_discovery_audit_row_count"] == len(rows)
    assert len(rows) >= 1
    assert {row["read_only_discovery_performed"] for row in rows} == {"True"}
    assert {row["import_performed"] for row in rows} == {"False"}
    assert {row["execution_performed"] for row in rows} == {"False"}
    assert {row["modification_allowed_current_step"] for row in rows} == {"False"}
    assert all(row["adapter_design_note"] for row in rows)
    by_path = {row["source_path"]: row for row in rows}
    assert by_path["lightning_modules.py"]["protected_source_path"] == "True"
    assert any(row["source_path"].startswith("equivariant_diffusion/") and row["protected_source_path"] == "True" for row in rows)
    assert manifest["source_discovery_read_only"] is True
    assert manifest["no_source_import_or_execution"] is True


def test_interface_contract_declares_external_adapter_without_implementation() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.INTERFACE_CONTRACT_CSV)
    assert manifest["diffsbdd_loader_adapter_interface_contract_written"] is True
    assert manifest["diffsbdd_loader_adapter_interface_contract_row_count"] == len(rows) >= 12
    assert {row["implementation_status"] for row in rows} == {"design_only_not_implemented"}
    assert {row["blocking_for_design_gate"] for row in rows} == {"False"}
    assert all(row["checkpoint_compatibility_note"] for row in rows)
    by_item = {row["interface_item"]: row for row in rows}
    assert "src/covalent_ext/" in by_item["adapter_module_location"]["proposed_contract"]
    assert "adapter" in by_item["adapter_checkpoint_compatibility_policy"]["proposed_contract"]
    assert manifest["all_interface_contracts_declared"] is True


def test_shape_mapping_contract_has_fourteen_design_only_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.SHAPE_MAPPING_CONTRACT_CSV)
    assert manifest["diffsbdd_loader_adapter_shape_mapping_contract_written"] is True
    assert manifest["diffsbdd_loader_adapter_shape_mapping_contract_row_count"] == len(rows) == 14
    assert [row["covalent_shape_item"] for row in rows] == [
        "pocket_atom_coordinates",
        "pocket_atom_features",
        "pocket_residue_features",
        "ligand_atom_coordinates",
        "ligand_atom_features",
        "ligand_bond_index",
        "ligand_bond_features",
        "ligand_group_labels",
        "covalent_endpoint_atom_mask",
        "reactive_residue_atom_coordinates",
        "canonical_mask_task_id_or_name",
        "auxiliary_warhead_type_label",
        "auxiliary_ligand_residue_atom_pair_label",
        "auxiliary_pre_post_geometry_label",
    ]
    assert {row["implementation_status"] for row in rows} == {"design_only_not_implemented"}
    assert {row["tensor_persistence_policy"] for row in rows} == {"do_not_persist_tensor_artifacts"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert {row["shape_mapping_design_passed"] for row in rows} == {"True"}
    assert manifest["all_shape_mappings_declared"] is True


def test_mask_mapping_preserves_five_canonical_tasks_and_b3() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.MASK_MAPPING_CONTRACT_CSV)
    assert manifest["diffsbdd_loader_adapter_mask_mapping_contract_written"] is True
    assert manifest["diffsbdd_loader_adapter_mask_mapping_contract_row_count"] == len(rows) == 5
    assert [row["canonical_mask_task_name"] for row in rows] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in rows] == gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["source_of_truth_status"] for row in rows} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in rows} == {"display_only"}
    assert {row["tensor_mask_written_current_step"] for row in rows} == {"False"}
    assert {row["implementation_status"] for row in rows} == {"design_only_not_implemented"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert {row["mask_mapping_design_passed"] for row in rows} == {"True"}
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["all_mask_mappings_declared"] is True


def test_auxiliary_label_contract_carries_labels_without_loss_integration() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.AUXILIARY_LABEL_CONTRACT_CSV)
    assert manifest["diffsbdd_loader_adapter_auxiliary_label_contract_written"] is True
    assert manifest["diffsbdd_loader_adapter_auxiliary_label_contract_row_count"] == len(rows) == 3
    assert [row["auxiliary_label_name"] for row in rows] == [
        "warhead_type",
        "ligand_residue_atom_pair",
        "pre_post_covalent_geometry",
    ]
    assert {row["future_loss_integration_status"] for row in rows} == {"not_integrated_into_loss"}
    assert {row["implementation_status"] for row in rows} == {"design_only_not_implemented"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert {row["feature_semantics_audit_required_before_training"] for row in rows} == {"True"}
    assert {row["auxiliary_label_design_passed"] for row in rows} == {"True"}
    assert manifest["all_auxiliary_label_contracts_declared"] is True


def test_execution_boundary_contract_forbids_training_and_original_source_modification() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.EXECUTION_BOUNDARY_CONTRACT_CSV)
    by_item = {row["boundary_item"]: row for row in rows}
    assert manifest["diffsbdd_loader_adapter_execution_boundary_contract_written"] is True
    assert manifest["diffsbdd_loader_adapter_execution_boundary_contract_row_count"] == len(rows) >= 18
    assert {row["current_step_status"] for row in rows} == {"not_executed_or_not_allowed"}
    assert {row["forbidden_current_step"] for row in rows} == {"True"}
    assert by_item["adapter_implementation"]["allowed_next_step_status"] == "allowed_only_under_src_covalent_ext_in_next_smoke"
    for item in [
        "dataloader_modification",
        "original_diffsbdd_source_modification",
        "model_forward_call",
        "loss_compute",
        "backward_call",
        "optimizer_creation",
        "trainer_fit",
        "checkpoint_load",
        "checkpoint_save",
        "pt_npz_artifact_creation",
        "training_claim",
    ]:
        assert by_item[item]["forbidden_next_step"] == "True"
    assert by_item["feature_semantics_audit"]["allowed_next_step_status"] == "required_before_training_not_completed"
    assert manifest["all_execution_boundaries_declared"] is True


def test_feature_semantics_boundary_keeps_audit_required() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.FEATURE_SEMANTICS_BOUNDARY_CSV)
    assert manifest["diffsbdd_loader_adapter_feature_semantics_boundary_written"] is True
    assert manifest["diffsbdd_loader_adapter_feature_semantics_boundary_row_count"] == len(rows) == 12
    assert {row["audit_required_before_training"] for row in rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in rows} == {"False"}
    assert {row["blocking_for_adapter_design_gate"] for row in rows} == {"False"}
    assert {row["blocking_for_adapter_implementation_smoke"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in rows)
    assert manifest["all_feature_semantics_audit_required_before_training"] is True
    assert manifest["no_feature_semantics_claimed_fully_audited"] is True


def test_manifest_records_design_only_safety_and_readiness() -> None:
    manifest = _manifest()
    assert manifest["checkpoint_compatibility_policy"] == gate.CHECKPOINT_COMPATIBILITY_POLICY
    assert manifest["checkpoint_compatibility_preserved_by_design"] is True
    assert manifest["diffsbdd_loader_adapter_design_gate_passed"] is True
    false_keys = [
        "adapter_implemented",
        "adapter_instantiated",
        "smoke_dataset_instantiated",
        "loader_instantiated",
        "torch_imported",
        "torch_tensor_created",
        "transient_tensor_shape_inspection_performed",
        "sample_index_written",
        "sample_index_modified",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_smoke_modified",
        "model_input_materialized",
        "model_input_written",
        "tensor_artifact_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "dataloader_modified",
        "forward_modified",
        "loss_modified",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_loaded",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "pt_created",
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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["ready_for_diffsbdd_loader_adapter_implementation_smoke"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        gate.INPUT_CONTRACT_CSV,
        gate.SOURCE_DISCOVERY_AUDIT_CSV,
        gate.INTERFACE_CONTRACT_CSV,
        gate.SHAPE_MAPPING_CONTRACT_CSV,
        gate.MASK_MAPPING_CONTRACT_CSV,
        gate.AUXILIARY_LABEL_CONTRACT_CSV,
        gate.EXECUTION_BOUNDARY_CONTRACT_CSV,
        gate.FEATURE_SEMANTICS_BOUNDARY_CSV,
        gate.REPORT_CSV,
        gate.MANIFEST_JSON,
        gate.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in gate.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in gate.FORBIDDEN_COMMITTABLE_SUFFIXES
    ]
    assert forbidden == []
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


def test_summary_states_design_only_boundary() -> None:
    _manifest()
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "DiffSBDD loader adapter design gate only",
        "does not implement the adapter",
        "does not modify original DiffSBDD dataloader",
        "external adapter under covalent_ext",
        "14 shape items",
        "scaffold_only/B3",
        "3 auxiliary labels",
        "out of loss integration",
        "does not import torch",
        "feature semantics audit required",
        "adapter implementation smoke next",
    ]:
        assert snippet in summary


def test_ast_safety_no_loader_tensor_training_calls_in_step13ab_files() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0.py"),
    ]
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_checkpoint",
        "load_from_checkpoint",
        "MolFromSmiles",
        "MolFromMolFile",
        "MolFromPDBFile",
        "urlopen",
    }
    dangerous_names = {"DataLoader", "Dataset", "Adam", "AdamW", "SGD", "RMSprop"}
    for path in files:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            assert not (isinstance(node, ast.Import) and any(alias.name == "torch" for alias in node.names))
            assert not (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and (node.module == "torch" or node.module.startswith("torch."))
            )
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner in {"torch", "np", "numpy"} and func.attr in {"save", "load", "tensor", "zeros"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in dangerous_attrs
            if isinstance(func, ast.Name):
                assert func.id not in dangerous_names
