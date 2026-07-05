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

from covalent_ext import real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13x_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13x_model_input_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_input_contract_has_three_expected_cys_sg_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.INPUT_CONTRACT_CSV)
    assert manifest["loader_shape_dry_run_input_contract_written"] is True
    assert manifest["loader_shape_dry_run_input_contract_row_count"] == len(rows) == 3
    assert [row["loader_shape_dry_run_sample_id"] for row in rows] == gate.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS
    assert [row["model_input_smoke_row_id"] for row in rows] == gate.EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
    assert [row["sample_index_row_id"] for row in rows] == gate.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert {row["v1_train_ready_scope"] for row in rows} == {gate.V1_TRAIN_READY_SCOPE}
    assert {row["residue_scope"] for row in rows} == {gate.DESIGN_SCOPE}
    assert {row["residue_name"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert manifest["all_loader_shape_dry_run_input_rows_validated"] is True


def test_input_contract_counts_masks_and_non_execution_statuses() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.INPUT_CONTRACT_CSV)
    assert {
        row["review_row_id"]: (int(row["ligand_atom_count"]), int(row["ligand_bond_count"]))
        for row in rows
    } == {"HR_0002": (33, 35), "HR_0003": (30, 33), "HR_0004": (41, 45)}
    assert {row["endpoint_atom_count"] for row in rows} == {"1"}
    assert {row["endpoint_touching_bond_count"] for row in rows} == {"1"}
    assert {row["canonical_mask_task_names"] for row in rows} == {";".join(gate.CANONICAL_MASK_TASK_NAMES)}
    assert {row["canonical_mask_task_aliases"] for row in rows} == {";".join(gate.CANONICAL_MASK_TASK_ALIASES)}
    assert {row["mask_task_count"] for row in rows} == {"5"}
    assert {row["loader_shape_dry_run_input_status"] for row in rows} == {"design_only_not_executed"}
    assert {row["tensor_artifact_status"] for row in rows} == {"not_written"}
    assert {row["loader_execution_status"] for row in rows} == {"not_executed"}
    assert {row["forward_execution_status"] for row in rows} == {"not_executed"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert {row["feature_semantics_audit_required_before_training"] for row in rows} == {"True"}
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_dependency_contract_has_eleven_existing_count_validated_dependencies() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.DEPENDENCY_CONTRACT_CSV)
    assert manifest["loader_shape_dry_run_dependency_contract_written"] is True
    assert manifest["loader_shape_dry_run_dependency_contract_row_count"] == len(rows) == 11
    assert {row["dependency_exists"] for row in rows} == {"True"}
    assert {row["dependency_count_validated"] for row in rows} == {"True"}
    assert {row["dependency_validation_status"] for row in rows} == {"exists_and_count_validated"}
    assert {row["loader_execution_status"] for row in rows} == {"not_executed"}
    assert {row["training_use_status"] for row in rows} == {"not_training_input_yet"}
    assert manifest["all_dependency_artifacts_exist"] is True
    assert manifest["all_dependency_counts_validated"] is True


def test_shape_expectation_contract_declares_future_shapes_without_tensorization() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.SHAPE_EXPECTATION_CONTRACT_CSV)
    assert manifest["loader_shape_dry_run_shape_expectation_contract_written"] is True
    assert manifest["loader_shape_dry_run_shape_expectation_contract_row_count"] == len(rows) >= 14
    assert {
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
    } <= {row["shape_item"] for row in rows}
    assert {row["materialization_status"] for row in rows} == {"design_only_not_tensorized"}
    assert {row["expected_shape_status"] for row in rows} == {"declared_for_future_dry_run"}
    assert {row["validation_method_next_step"] for row in rows} == {"loader_shape_dry_run_execution_smoke"}
    assert {row["blocking_for_design_gate"] for row in rows} == {"False"}
    assert manifest["all_shape_expectations_declared"] is True
    assert manifest["no_shape_claimed_executed_or_tensorized"] is True


def test_execution_boundary_forbids_current_execution_and_training_paths() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.EXECUTION_BOUNDARY_CONTRACT_CSV)
    by_item = {row["boundary_item"]: row for row in rows}
    assert manifest["loader_shape_dry_run_execution_boundary_contract_written"] is True
    assert manifest["loader_shape_dry_run_execution_boundary_contract_row_count"] == len(rows) >= 14
    assert by_item["loader_instantiation"]["allowed_next_step_status"] == "allowed_only_for_shape_dry_run_execution_smoke"
    assert by_item["torch_tensor_creation"]["allowed_next_step_status"] == "allowed_only_for_shape_dry_run_execution_smoke"
    for item in [
        "dataloader_modification",
        "forward_call",
        "loss_compute",
        "backward_call",
        "optimizer_creation",
        "trainer_fit",
        "checkpoint_save",
        "pt_npz_artifact_creation",
        "training_claim",
    ]:
        assert by_item[item]["forbidden_current_step"] == "True"
        assert by_item[item]["forbidden_next_step"] == "True"
    assert by_item["feature_semantics_audit"]["allowed_next_step_status"] == "remains_required_before_training"
    assert manifest["all_execution_boundaries_validated"] is True


def test_feature_semantics_boundary_preserves_audit_requirement() -> None:
    manifest = _manifest()
    rows = _csv_rows(gate.FEATURE_SEMANTICS_BOUNDARY_CSV)
    assert manifest["loader_shape_dry_run_feature_semantics_boundary_written"] is True
    assert manifest["loader_shape_dry_run_feature_semantics_boundary_row_count"] == len(rows) == 12
    assert {row["audit_required_before_training"] for row in rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in rows} == {"False"}
    assert {row["blocking_for_loader_shape_dry_run_design_gate"] for row in rows} == {"False"}
    assert {row["blocking_for_loader_shape_dry_run_execution_smoke"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in rows)
    assert manifest["all_feature_semantics_audit_required_before_training"] is True
    assert manifest["no_feature_semantics_claimed_fully_audited"] is True


def test_design_gate_does_not_execute_loader_create_tensors_or_train() -> None:
    manifest = _manifest()
    assert manifest["loader_shape_dry_run_design_gate_passed"] is True
    false_keys = [
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
        "loader_instantiated",
        "torch_tensor_created",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
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
        "dataloader_modified",
        "forward_modified",
        "loss_modified",
        "loader_shape_dry_run_performed",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_readiness_boundary_allows_execution_smoke_but_not_training() -> None:
    manifest = _manifest()
    assert manifest["ready_for_loader_shape_dry_run_execution_smoke"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        gate.INPUT_CONTRACT_CSV,
        gate.DEPENDENCY_CONTRACT_CSV,
        gate.SHAPE_EXPECTATION_CONTRACT_CSV,
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


def test_summary_states_loader_shape_design_boundary() -> None:
    _manifest()
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "loader shape dry run design gate only",
        "does not instantiate loader",
        "create tensors",
        "does not create PT or NPZ",
        "does not modify dataloader, forward, loss",
        "scaffold_only/B3",
        "does not validate real tensor shapes yet",
        "feature semantics audit required",
        "loader shape dry run execution smoke next",
        "not training",
        gate.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0.py"),
    ]
    text_scan_files = files[:2]
    forbidden_text = [
        "urllib",
        "requests",
        "urlopen",
        "wget",
        "curl",
        "gzip.open",
        "Bio.PDB",
        "MMCIFParser",
        "PDBParser",
        "Chem.MolFrom",
        "AllChem",
        "compute_masked_loss",
        ".backward(",
        "torch.optim",
        "optimizer.step",
        "trainer.fit",
        "training_step(",
        "torch.save",
        "save_checkpoint",
        "load_from_checkpoint",
        "numpy.load",
        "np.load",
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
        "GetMorganFingerprint",
        "GetMorganFingerprintAsBitVect",
        "urlopen",
    }
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    for path in text_scan_files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text, f"{pattern} in {path}"
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner in {"np", "numpy"} and func.attr == "load")
                assert not (owner == "torch" and func.attr in {"save", "optim"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in dangerous_attrs
            if isinstance(func, ast.Name):
                assert func.id not in dangerous_names
