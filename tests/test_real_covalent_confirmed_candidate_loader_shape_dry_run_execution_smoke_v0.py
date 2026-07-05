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

from covalent_ext import real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0.py"],
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


def test_check_script_passes_and_validates_step13y_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13y_loader_shape_dry_run_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_local_smoke_dataset_length_and_transient_tensor_shapes() -> None:
    rows = _csv_rows(smoke.STEP13Y_INPUT_CONTRACT_CSV)
    dataset = smoke.LoaderShapeDryRunSmokeDataset(rows)
    assert len(dataset) == 3
    sample = dataset[0]
    metadata = sample["metadata"]
    tensors = sample["tensors"]
    assert metadata["loader_shape_dry_run_sample_id"] == "LSDR_DESIGN_000001"
    assert tensors["pocket_atom_coordinates"].shape == (int(metadata["pocket_atom_count"]), 3)
    assert tensors["ligand_atom_coordinates"].shape == (33, 3)
    assert tensors["ligand_bond_index"].shape == (2, 35)
    assert tensors["covalent_endpoint_atom_mask"].shape == (33,)
    assert tensors["canonical_mask_task_id_or_name"].shape == (1,)
    assert tensors["auxiliary_warhead_type_label"].dim() == 0


def test_sample_audit_has_three_expected_rows_and_all_pass() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.SAMPLE_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_sample_audit_written"] is True
    assert manifest["loader_shape_dry_run_sample_audit_row_count"] == len(rows) == 3
    assert [row["loader_shape_dry_run_sample_id"] for row in rows] == smoke.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS
    assert [row["model_input_smoke_row_id"] for row in rows] == smoke.EXPECTED_MODEL_INPUT_SMOKE_ROW_IDS
    assert [row["sample_index_row_id"] for row in rows] == smoke.EXPECTED_SAMPLE_INDEX_ROW_IDS
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    true_keys = [
        "dataset_row_found",
        "loader_batch_seen",
        "cys_sg_scope_validated",
        "ligand_counts_validated",
        "endpoint_counts_validated",
        "canonical_masks_validated",
        "transient_tensors_created",
        "sample_shape_dry_run_passed",
    ]
    for key in true_keys:
        assert {row[key] for row in rows} == {"True"}
    assert {row["tensor_artifact_written"] for row in rows} == {"False"}
    assert {row["model_forward_called"] for row in rows} == {"False"}
    assert {row["loss_compute_called"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_sample_shape_dry_run_passed"] is True


def test_shape_observation_has_42_passed_transient_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.SHAPE_OBSERVATION_CSV)
    assert manifest["loader_shape_dry_run_shape_observation_written"] is True
    assert manifest["loader_shape_dry_run_shape_observation_row_count"] == len(rows) == 42
    assert {row["shape_observation_status"] for row in rows} == {"observed_in_transient_shape_smoke"}
    assert {row["tensor_persisted"] for row in rows} == {"False"}
    assert {row["shape_observation_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert len({(row["loader_shape_dry_run_sample_id"], row["shape_item"]) for row in rows}) == 42
    by_review_shape = {(row["review_row_id"], row["shape_item"]): json.loads(row["observed_shape"]) for row in rows}
    assert by_review_shape[("HR_0002", "ligand_atom_coordinates")] == [33, 3]
    assert by_review_shape[("HR_0003", "ligand_bond_index")] == [2, 33]
    assert by_review_shape[("HR_0004", "canonical_mask_task_id_or_name")] == [1]
    assert manifest["all_shape_observations_passed"] is True


def test_batch_audit_has_three_ordered_batch_size_one_rows() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.BATCH_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_batch_audit_written"] is True
    assert manifest["loader_shape_dry_run_batch_audit_row_count"] == len(rows) == 3
    assert [int(row["batch_index"]) for row in rows] == [0, 1, 2]
    assert [row["loader_shape_dry_run_sample_id"] for row in rows] == smoke.EXPECTED_LOADER_SHAPE_DRY_RUN_SAMPLE_IDS
    assert {row["batch_size"] for row in rows} == {"1"}
    assert {row["collate_status"] for row in rows} == {"single_sample_collate_no_padding_no_training"}
    assert {row["batch_shape_checked"] for row in rows} == {"True"}
    assert {row["batch_order_validated"] for row in rows} == {"True"}
    assert {row["model_forward_called"] for row in rows} == {"False"}
    assert {row["loss_compute_called"] for row in rows} == {"False"}
    assert {row["backward_called"] for row in rows} == {"False"}
    assert {row["optimizer_step_called"] for row in rows} == {"False"}
    assert {row["training_step_called"] for row in rows} == {"False"}
    assert {row["batch_audit_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["loader_batch_size"] == 1
    assert manifest["loader_batch_count"] == 3
    assert manifest["all_loader_batches_seen"] is True
    assert manifest["all_batch_audits_passed"] is True


def test_execution_boundary_audit_respects_allowed_loader_and_forbidden_training_paths() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)
    by_item = {row["boundary_item"]: row for row in rows}
    assert manifest["loader_shape_dry_run_execution_boundary_audit_written"] is True
    assert manifest["loader_shape_dry_run_execution_boundary_audit_row_count"] == len(rows) == 14
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
    assert {row["boundary_respected"] for row in rows} == {"True"}
    assert {row["boundary_audit_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_execution_boundaries_respected"] is True


def test_feature_semantics_audit_keeps_training_audit_required() -> None:
    manifest = _manifest()
    rows = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert manifest["loader_shape_dry_run_feature_semantics_audit_written"] is True
    assert manifest["loader_shape_dry_run_feature_semantics_audit_row_count"] == len(rows) == 12
    assert {row["audit_required_before_training"] for row in rows} == {"True"}
    assert {row["fully_audited_claimed"] for row in rows} == {"False"}
    assert {row["blocking_for_loader_shape_dry_run_execution_smoke"] for row in rows} == {"False"}
    assert {row["training_ready"] for row in rows} == {"False"}
    assert all(row["recommended_audit_step"] for row in rows)
    assert {row["feature_semantics_execution_audit_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert manifest["all_feature_semantics_audit_required_before_training"] is True
    assert manifest["no_feature_semantics_claimed_fully_audited"] is True


def test_manifest_records_loader_execution_smoke_but_no_persistent_artifacts_or_training() -> None:
    manifest = _manifest()
    assert manifest["smoke_dataset_instantiated"] is True
    assert manifest["loader_instantiated"] is True
    assert manifest["torch_imported"] is True
    assert manifest["torch_tensor_created"] is True
    assert manifest["transient_tensor_shape_inspection_performed"] is True
    assert manifest["loader_shape_dry_run_execution_smoke_passed"] is True
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
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_readiness_boundary_points_to_qa_gate_not_training() -> None:
    manifest = _manifest()
    assert manifest["ready_for_loader_shape_dry_run_qa_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == smoke.RECOMMENDED_NEXT_STEP


def test_canonical_masks_preserved_in_manifest() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        smoke.SAMPLE_AUDIT_CSV,
        smoke.SHAPE_OBSERVATION_CSV,
        smoke.BATCH_AUDIT_CSV,
        smoke.EXECUTION_BOUNDARY_AUDIT_CSV,
        smoke.FEATURE_SEMANTICS_AUDIT_CSV,
        smoke.REPORT_CSV,
        smoke.MANIFEST_JSON,
        smoke.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in smoke.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in smoke.FORBIDDEN_COMMITTABLE_SUFFIXES
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


def test_summary_states_execution_smoke_boundary() -> None:
    _manifest()
    summary = smoke.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "loader shape dry run execution smoke",
        "minimal read-only smoke dataset and loader",
        "transient in-memory tensors only for shape inspection",
        "does not persist tensors",
        "does not create PT or NPZ",
        "does not modify dataloader, forward, loss",
        "does not call model forward, loss, backward",
        "scaffold_only/B3",
        "feature semantics audit required",
        "loader shape dry run QA gate next",
        smoke.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_persistent_or_training_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0.py"),
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
