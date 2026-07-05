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

from covalent_ext import real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate as qa


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0.py"],
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


def test_check_script_passes_and_validates_step13z_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == qa.STAGE
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["step13z_loader_shape_dry_run_execution_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_sample_qa_audit_has_three_expected_rows_and_all_pass() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.SAMPLE_QA_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_sample_qa_audit_written"] is True
    assert manifest["loader_shape_dry_run_sample_qa_audit_row_count"] == len(rows) == 3
    assert [row["loader_shape_dry_run_sample_id"] for row in rows] == qa.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS
    assert [row["model_input_smoke_row_id"] for row in rows] == qa.EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
    assert [row["sample_index_row_id"] for row in rows] == qa.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == qa.EXPECTED_REVIEW_ROW_IDS
    assert [row["pdb_id"] for row in rows] == qa.EXPECTED_PDB_IDS
    true_keys = [
        "sample_audit_row_found",
        "expected_identity_validated",
        "sample_shape_dry_run_passed",
        "dataset_row_found",
        "loader_batch_seen",
        "cys_sg_scope_validated",
        "ligand_counts_validated",
        "endpoint_counts_validated",
        "canonical_masks_validated",
        "transient_tensors_created_in_step13z",
        "sample_qa_passed",
    ]
    for key in true_keys:
        assert {row[key] for row in rows} == {"True"}
    for key in ["tensor_artifact_written", "model_forward_called", "loss_compute_called", "training_ready"]:
        assert {row[key] for row in rows} == {"False"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_sample_qa_passed"] is True


def test_shape_observation_qa_has_42_rows_no_duplicates_and_expected_shapes() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.SHAPE_OBSERVATION_QA_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_shape_observation_qa_audit_written"] is True
    assert manifest["loader_shape_dry_run_shape_observation_qa_audit_row_count"] == len(rows) == 42
    assert {row["tensor_persisted"] for row in rows} == {"False"}
    assert {row["shape_observation_passed"] for row in rows} == {"True"}
    assert {row["shape_contract_consistency_validated"] for row in rows} == {"True"}
    assert {row["shape_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert len({(row["loader_shape_dry_run_sample_id"], row["shape_item"]) for row in rows}) == 42
    assert {sample_id: sum(row["loader_shape_dry_run_sample_id"] == sample_id for row in rows) for sample_id in qa.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS} == {
        "LSDR_DESIGN_000001": 14,
        "LSDR_DESIGN_000002": 14,
        "LSDR_DESIGN_000003": 14,
    }
    by_review_shape = {(row["review_row_id"], row["shape_item"]): json.loads(row["observed_shape"]) for row in rows}
    assert by_review_shape[("HR_0002", "ligand_atom_coordinates")] == [33, 3]
    assert by_review_shape[("HR_0002", "ligand_bond_index")] == [2, 35]
    assert by_review_shape[("HR_0003", "ligand_atom_coordinates")] == [30, 3]
    assert by_review_shape[("HR_0003", "ligand_bond_index")] == [2, 33]
    assert by_review_shape[("HR_0004", "ligand_atom_coordinates")] == [41, 3]
    assert by_review_shape[("HR_0004", "ligand_bond_index")] == [2, 45]
    for review_id in qa.EXPECTED_REVIEW_ROW_IDS:
        assert by_review_shape[(review_id, "canonical_mask_task_id_or_name")] == [1]
    assert manifest["all_shape_observation_qa_passed"] is True


def test_batch_qa_validates_order_batch_size_and_no_training_calls() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.BATCH_QA_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_batch_qa_audit_written"] is True
    assert manifest["loader_shape_dry_run_batch_qa_audit_row_count"] == len(rows) == 3
    assert [int(row["batch_index"]) for row in rows] == [0, 1, 2]
    assert [row["loader_shape_dry_run_sample_id"] for row in rows] == qa.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS
    assert {row["batch_size"] for row in rows} == {"1"}
    assert {row["collate_status"] for row in rows} == {"single_sample_collate_no_padding_no_training"}
    for key in ["batch_shape_checked", "batch_order_validated", "batch_audit_passed", "batch_qa_passed"]:
        assert {row[key] for row in rows} == {"True"}
    for key in [
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_step_called",
        "training_step_called",
    ]:
        assert {row[key] for row in rows} == {"False"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_batch_qa_passed"] is True


def test_execution_boundary_qa_keeps_step13aa_read_only() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.EXECUTION_BOUNDARY_QA_AUDIT_CSV)
    by_item = {row["boundary_item"]: row for row in rows}
    assert manifest["loader_shape_dry_run_execution_boundary_qa_audit_written"] is True
    assert manifest["loader_shape_dry_run_execution_boundary_qa_audit_row_count"] == len(rows) == 14
    assert by_item["loader_instantiation"]["observed_current_step_status"] == "executed_allowed_for_shape_inspection"
    assert by_item["torch_tensor_creation"]["observed_current_step_status"] == "executed_transient_in_memory_for_shape_inspection"
    for item in [
        "dataloader_modification",
        "forward_call",
        "loss_compute",
        "backward_call",
        "optimizer_creation",
        "trainer_fit",
        "checkpoint_save",
        "pt_npz_artifact_creation",
        "rdkit_or_sdf_access",
        "raw_mmcif_access",
        "training_claim",
    ]:
        assert by_item[item]["observed_current_step_status"] == "not_executed_or_not_allowed"
    assert by_item["feature_semantics_audit"]["observed_current_step_status"] == "required_before_training_not_completed"
    for key in ["boundary_respected", "training_forbidden_respected", "artifact_forbidden_respected", "boundary_audit_passed", "boundary_qa_passed"]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_execution_boundary_qa_passed"] is True


def test_feature_semantics_qa_keeps_audit_required_before_training() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.FEATURE_SEMANTICS_QA_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_feature_semantics_qa_audit_written"] is True
    assert manifest["loader_shape_dry_run_feature_semantics_qa_audit_row_count"] == len(rows) == 12
    assert {row["audit_required_before_training"] for row in rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in rows} == {"False"}
    assert {row["blocking_for_loader_shape_dry_run_execution_smoke"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in rows)
    assert {row["feature_semantics_execution_audit_passed"] for row in rows} == {"True"}
    assert {row["feature_semantics_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_feature_semantics_qa_passed"] is True
    assert manifest["all_feature_semantics_audit_required_before_training"] is True
    assert manifest["no_feature_semantics_claimed_fully_audited"] is True


def test_dependency_qa_has_ten_existing_count_validated_dependencies() -> None:
    manifest = _manifest()
    rows = _csv_rows(qa.DEPENDENCY_QA_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_dependency_qa_audit_written"] is True
    assert manifest["loader_shape_dry_run_dependency_qa_audit_row_count"] == len(rows) == 10
    assert [row["dependency_name"] for row in rows] == [
        "step13z_manifest",
        "step13z_sample_audit",
        "step13z_shape_observation",
        "step13z_batch_audit",
        "step13z_execution_boundary_audit",
        "step13z_feature_semantics_audit",
        "step13y_input_contract",
        "step13y_shape_expectation_contract",
        "step13y_execution_boundary_contract",
        "step13y_feature_semantics_boundary",
    ]
    assert {row["dependency_exists"] for row in rows} == {"True"}
    assert {row["dependency_count_validated"] for row in rows} == {"True"}
    assert {row["dependency_qa_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_dependency_artifacts_exist"] is True
    assert manifest["all_dependency_counts_validated"] is True


def test_manifest_carries_step13z_execution_facts_but_current_step_does_not_execute_loader_or_torch() -> None:
    manifest = _manifest()
    assert manifest["smoke_dataset_instantiated_in_step13z"] is True
    assert manifest["loader_instantiated_in_step13z"] is True
    assert manifest["torch_tensor_created_in_step13z"] is True
    assert manifest["transient_tensor_shape_inspection_performed_in_step13z"] is True
    assert manifest["all_loader_batches_seen_in_step13z"] is True
    assert manifest["all_shape_observations_passed_in_step13z"] is True
    assert manifest["loader_shape_dry_run_execution_smoke_passed"] is True
    for key in [
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
    ]:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_canonical_masks_and_readiness_boundary() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == qa.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == qa.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["loader_shape_dry_run_qa_gate_passed"] is True
    assert manifest["ready_for_diffsbdd_loader_adapter_design_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == qa.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        qa.SAMPLE_QA_AUDIT_CSV,
        qa.SHAPE_OBSERVATION_QA_AUDIT_CSV,
        qa.BATCH_QA_AUDIT_CSV,
        qa.EXECUTION_BOUNDARY_QA_AUDIT_CSV,
        qa.FEATURE_SEMANTICS_QA_AUDIT_CSV,
        qa.DEPENDENCY_QA_AUDIT_CSV,
        qa.REPORT_CSV,
        qa.MANIFEST_JSON,
        qa.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in qa.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in qa.FORBIDDEN_COMMITTABLE_SUFFIXES
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


def test_summary_states_qa_only_boundary() -> None:
    _manifest()
    summary = qa.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "loader shape dry run QA gate only",
        "does not modify Step 13Z execution smoke artifacts",
        "does not instantiate a loader",
        "import torch",
        "create tensors",
        "create PT/NPZ",
        "transient shape observations",
        "scaffold_only/B3",
        "feature semantics audit required",
        "DiffSBDD loader adapter design gate next",
        qa.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_no_torch_or_training_calls_in_step13aa_files() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0.py"),
    ]
    text_scan_files = files[:1]
    forbidden_text = [
        "import torch",
        "from torch",
        "DataLoader",
        "Dataset",
        "torch.tensor",
        "torch.zeros",
        "torch.save",
        "np.save",
        "numpy.save",
        "Chem.MolFrom",
        "AllChem",
        "gzip.open",
        "Bio.PDB",
        "MMCIFParser",
        "PDBParser",
        "load_from_checkpoint",
        "compute_masked_loss",
        ".backward(",
        "torch.optim",
        "optimizer.step",
        "trainer.fit",
        "training_step(",
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
    for path in text_scan_files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text, f"{pattern} in {path}"
    for path in files:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
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
