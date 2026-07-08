from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_actual_dataloader_design_gate as design


ROOT = Path("data/derived/covalent_small/covapie_actual_dataloader_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_actual_dataloader_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BW check script before artifact tests"
    return json.loads(path.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def _git_diff_paths(paths: list[str]) -> list[str]:
    result = subprocess.run(["git", "diff", "--name-only", "--", *paths], text=True, stdout=subprocess.PIPE, check=False)
    return result.stdout.strip().splitlines()


def test_step13bv_precondition_and_readiness_boundary() -> None:
    manifest13bv = json.loads(design.step13bv.MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    precondition = _csv_rows(ROOT / "covapie_actual_dataloader_design_precondition_audit.csv")
    assert manifest13bv["stage"] == design.PREVIOUS_STAGE
    assert manifest13bv["all_checks_passed"] is True
    assert manifest13bv["ready_for_covapie_actual_dataloader_design_gate"] is True
    assert manifest13bv["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest13bv["ready_for_training"] is False
    assert manifest13bv["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design.STAGE
    assert manifest["previous_stage"] == design.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13bv_metadata_dataloader_smoke_qa_validated"] is True
    assert manifest["source_metadata_smoke_preview_row_count"] == 20
    assert manifest["source_metadata_smoke_preview_column_count"] == 30
    assert manifest["source_interface_preview_row_count"] == 20
    assert manifest["source_interface_preview_column_count"] == 35
    assert manifest["source_final_dataset_preview_row_count"] == 20
    assert manifest["source_final_dataset_preview_column_count"] == 45


def test_static_reference_audit_has_expected_rows_and_no_diffs() -> None:
    rows = _csv_rows(ROOT / "covapie_original_dataloader_static_reference_audit.csv")
    manifest = _manifest()
    assert len(rows) == 10
    assert {row["static_reference_audit_passed"] for row in rows} == {"True"}
    by_item = {row["static_reference_item"]: row for row in rows}
    assert by_item["dataset_py_exists"]["observed_status"] == "exists"
    assert by_item["prepare_crossdocked_py_exists"]["observed_status"] == "exists"
    assert by_item["lightning_modules_py_exists"]["observed_status"] == "exists"
    assert by_item["equivariant_diffusion_dir_exists"]["observed_status"] == "exists"
    assert by_item["dataset_py_static_read_only"]["observed_status"].startswith("static_read_only_bytes=")
    assert by_item["equivariant_diffusion_static_read_only"]["observed_status"].startswith("static_read_only_py_files=")
    assert by_item["original_dataloader_no_diff"]["observed_status"] == "no_diff"
    assert by_item["protected_model_code_no_diff"]["observed_status"] == "no_diff"
    assert manifest["original_dataloader_static_reference_audit_row_count"] == 10
    assert manifest["original_dataloader_static_reference_audit_passed"] is True


def test_adapter_design_tensorization_batch_and_checkpoint_contracts() -> None:
    adapter = _csv_rows(ROOT / "covapie_actual_dataloader_adapter_design_contract.csv")
    tensor = _csv_rows(ROOT / "covapie_actual_dataloader_tensorization_input_contract.csv")
    batch = _csv_rows(ROOT / "covapie_actual_dataloader_batch_collate_contract.csv")
    checkpoint = _csv_rows(ROOT / "covapie_actual_dataloader_checkpoint_compatibility_contract.csv")
    manifest = _manifest()
    assert len(adapter) == 12
    assert {row["current_step_status"] for row in adapter} == {"design_only_not_implemented"}
    assert {row["adapter_design_contract_passed"] for row in adapter} == {"True"}
    assert len(tensor) == 14
    assert {row["tensorization_input_contract_passed"] for row in tensor} == {"True"}
    tensor_by_item = {row["tensorization_item"]: row for row in tensor}
    assert tensor_by_item["protein_xyz_from_derived_atom_table"]["blocked_before_actual_tensor_smoke"] == "False"
    assert tensor_by_item["ligand_xyz_from_derived_atom_table"]["blocked_before_actual_tensor_smoke"] == "False"
    assert tensor_by_item["protein_atom_feature_semantics_blocked"]["blocked_before_actual_tensor_smoke"] == "True"
    assert tensor_by_item["torch_tensor_creation_blocked_current_step"]["current_step_status"] == "blocked_current_step"
    assert len(batch) == 10
    assert {row["batch_collate_contract_passed"] for row in batch} == {"True"}
    batch_by_item = {row["batch_contract_item"]: row for row in batch}
    assert batch_by_item["future_batch_variable_size_collate_requires_torch_gate"]["blocked_before_actual_dataloader_smoke"] == "True"
    assert batch_by_item["future_training_batch_blocked"]["blocked_before_actual_dataloader_smoke"] == "True"
    assert len(checkpoint) == 10
    assert {row["checkpoint_compatibility_contract_passed"] for row in checkpoint} == {"True"}
    checkpoint_by_item = {row["checkpoint_compatibility_item"]: row for row in checkpoint}
    assert checkpoint_by_item["checkpoint_not_loaded_current_step"]["observed_status"] == "not loaded"
    assert checkpoint_by_item["no_model_forward_current_step"]["observed_status"] == "not called"
    assert checkpoint_by_item["original_diffsbbd_dataloader_unchanged"]["observed_status"] == "no diff"
    assert manifest["actual_dataloader_adapter_design_contract_row_count"] == 12
    assert manifest["tensorization_input_contract_row_count"] == 14
    assert manifest["batch_collate_contract_row_count"] == 10
    assert manifest["checkpoint_compatibility_contract_row_count"] == 10


def test_feature_semantics_blockers_force_next_gate_not_actual_smoke() -> None:
    feature = _csv_rows(ROOT / "covapie_actual_dataloader_feature_semantics_blocker_contract.csv")
    plan = _csv_rows(ROOT / "covapie_actual_dataloader_future_smoke_plan.csv")
    manifest = _manifest()
    assert len(feature) == 10
    assert {row["blocker_contract_passed"] for row in feature} == {"True"}
    assert {row["blocks_actual_tensor_dataloader_smoke"] for row in feature} == {"True"}
    assert {row["blocks_training"] for row in feature} == {"True"}
    feature_by_item = {row["blocker_item"]: row for row in feature}
    assert feature_by_item["feature_semantics_known_for_training_false"]["current_status"] == "feature_semantics_known_for_training=false"
    assert feature_by_item["unknown_atom_feature_policy_finalized_for_training_false"]["current_status"] == "unknown_atom_feature_policy_finalized_for_training=false"
    assert len(plan) == 8
    assert {row["future_smoke_plan_passed"] for row in plan} == {"True"}
    plan_by_step = {row["planned_step"]: row for row in plan}
    assert plan_by_step["feature_semantics_resolution_gate_next_if_blocked"]["planned_action"] == "resolve tensorization semantics blockers"
    assert "actual tensor dataloader smoke" in plan_by_step["feature_semantics_resolution_gate_next_if_blocked"]["blocked_outputs_current_step"]
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["ready_for_covapie_feature_semantics_tensorization_audit_gate"] is True
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_feature_semantics_tensorization_audit_gate"


def test_canonical_masks_and_manifest_safety_boundary() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_names"] == design.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == design.CANONICAL_MASK_TASK_ALIASES
    assert manifest["source_canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    for key in [
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "torch_imported",
        "torch_tensor_created",
        "numpy_imported",
        "numpy_array_returned",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_text_read",
        "mmcif_parse_current_step",
        "coordinate_extraction_current_step",
        "network_access_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "gzip_open_used",
    ]:
        assert manifest[key] is False, key
    assert manifest["actual_dataloader_design_completed_current_step"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_safety_audit_no_forbidden_outputs_or_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_actual_dataloader_design_safety_audit.csv")
    assert len(safety) == 24
    assert {row["safety_passed"] for row in safety} == {"True"}
    forbidden_names = {
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
    }
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    module_path = Path("src/covalent_ext/covapie_actual_dataloader_design_gate.py")
    script_path = Path("scripts/check_covapie_actual_dataloader_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)


def test_raw_files_untracked_metadata_hash_and_existing_artifacts_unchanged() -> None:
    tracked = subprocess.run(["git", "ls-files", str(design.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(design.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(design.step13bd.METADATA_CSV.read_bytes()).hexdigest() == design.METADATA_CSV_SHA256
    assert _git_diff_paths([design.step13bv.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bu.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bt.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13br.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bm.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
