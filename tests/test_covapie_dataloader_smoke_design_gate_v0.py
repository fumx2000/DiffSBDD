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

from covalent_ext import covapie_dataloader_smoke_design_gate as design


ROOT = Path("data/derived/covalent_small/covapie_dataloader_smoke_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_dataloader_smoke_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BT check script before artifact tests"
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


def test_step13bs_precondition_and_readiness() -> None:
    manifest13bs = json.loads(design.step13bs.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_dataloader_smoke_design_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bs["stage"] == design.PREVIOUS_STAGE
    assert manifest13bs["all_checks_passed"] is True
    assert manifest13bs["ready_for_covapie_dataloader_smoke_design_gate"] is True
    assert manifest13bs["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bs["ready_for_training"] is False
    assert manifest13bs["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design.STAGE
    assert manifest["previous_stage"] == design.PREVIOUS_STAGE
    assert manifest["step13bs_dataloader_interface_qa_gate_validated"] is True


def test_contract_row_counts_and_pass_flags() -> None:
    manifest = _manifest()
    checks = [
        ("covapie_dataloader_smoke_runtime_boundary_contract.csv", 14, "runtime_boundary_contract_passed"),
        ("covapie_metadata_dataset_api_contract.csv", 10, "api_contract_passed"),
        ("covapie_metadata_getitem_output_mapping_contract.csv", 12, "mapping_contract_passed"),
        ("covapie_tensorization_blocker_contract.csv", 10, "blocker_contract_passed"),
        ("covapie_batch_collate_design_contract.csv", 8, "batch_collate_design_passed"),
        ("covapie_checkpoint_runtime_risk_contract.csv", 8, "checkpoint_runtime_risk_passed"),
        ("covapie_metadata_dataloader_smoke_plan.csv", 10, "metadata_smoke_plan_passed"),
    ]
    for filename, count, passed_key in checks:
        rows = _csv_rows(ROOT / filename)
        assert len(rows) == count
        assert {row[passed_key] for row in rows} == {"True"}
    assert manifest["runtime_boundary_contract_row_count"] == 14
    assert manifest["metadata_dataset_api_contract_row_count"] == 10
    assert manifest["metadata_getitem_output_mapping_contract_row_count"] == 12
    assert manifest["tensorization_blocker_contract_row_count"] == 10
    assert manifest["batch_collate_design_contract_row_count"] == 8
    assert manifest["checkpoint_runtime_risk_contract_row_count"] == 8
    assert manifest["metadata_dataloader_smoke_plan_row_count"] == 10


def test_runtime_boundary_and_metadata_dataset_api_contracts() -> None:
    runtime = {row["runtime_boundary_item"]: row for row in _csv_rows(ROOT / "covapie_dataloader_smoke_runtime_boundary_contract.csv")}
    api = {row["api_contract_item"]: row for row in _csv_rows(ROOT / "covapie_metadata_dataset_api_contract.csv")}
    assert runtime["future_smoke_reads_interface_preview"]["allowed_in_next_metadata_smoke"] == "True"
    assert runtime["future_smoke_constructs_metadata_dataset_shim"]["allowed_in_next_metadata_smoke"] == "True"
    for item in [
        "future_smoke_no_torch_import",
        "future_smoke_no_tensor_creation",
        "future_smoke_no_checkpoint_load",
        "future_smoke_no_model_forward",
        "future_smoke_no_loss_or_training",
        "future_smoke_no_original_dataloader_modify",
        "future_smoke_no_raw_file_read",
        "actual_torch_dataloader_still_blocked",
    ]:
        assert runtime[item]["blocked_in_next_metadata_smoke"] == "True"
    assert api["metadata_dataset_constructor"]["current_step_implemented"] == "False"
    assert api["metadata_dataset_len"]["expected_output"] == "integer row count"
    assert api["metadata_dataset_getitem_by_index"]["expected_output"] == "dict[str, metadata scalar/list]"
    assert api["metadata_dataset_no_tensor_outputs"]["expected_output"] == "Python dict only"
    assert api["metadata_dataset_no_collate_current_step"]["current_step_implemented"] == "False"


def test_getitem_mapping_preserves_mask_and_no_tensorization() -> None:
    rows = _csv_rows(ROOT / "covapie_metadata_getitem_output_mapping_contract.csv")
    by_item = {row["getitem_mapping_item"]: row for row in rows}
    assert len(rows) == 12
    assert {row["tensorization_status"] for row in rows} == {"not_tensorized_metadata_only"}
    assert {row["mapping_contract_passed"] for row in rows} == {"True"}
    assert by_item["mask_task_selector"]["source_fields"] == "mask_task_name"
    assert by_item["mask_task_selector"]["expected_python_type_policy"] == "str canonical long name"
    assert by_item["mask_alias_display_only"]["source_fields"] == "mask_task_alias"
    assert by_item["mask_alias_display_only"]["expected_python_type_policy"] == "str display only"


def test_tensorization_batch_and_checkpoint_risk_contracts() -> None:
    blockers = {row["blocker_item"]: row for row in _csv_rows(ROOT / "covapie_tensorization_blocker_contract.csv")}
    batch = {row["batch_collate_item"]: row for row in _csv_rows(ROOT / "covapie_batch_collate_design_contract.csv")}
    checkpoint = {row["checkpoint_risk_item"]: row for row in _csv_rows(ROOT / "covapie_checkpoint_runtime_risk_contract.csv")}
    assert blockers["no_torch_import_current_step"]["current_status"] == "torch_imported=false"
    assert blockers["unknown_atom_feature_policy_not_finalized"]["current_status"] == "unknown_atom_feature_policy_finalized_for_training=false"
    assert batch["no_collate_current_step"]["current_step_status"] == "no collate implementation"
    assert batch["future_real_collate_requires_torch_gate"]["actual_dataloader_requirement"] == "torch/import/collate gate"
    assert checkpoint["checkpoint_not_loaded_current_step"]["current_status"] == "not loaded"
    assert checkpoint["no_model_forward_current_step"]["current_status"] == "not called"
    assert checkpoint["original_diffsbbd_dataloader_unchanged"]["current_status"] == "no diff"


def test_metadata_dataloader_smoke_plan_and_readiness_boundary() -> None:
    plan = {row["planned_step"]: row for row in _csv_rows(ROOT / "covapie_metadata_dataloader_smoke_plan.csv")}
    manifest = _manifest()
    assert plan["construct_metadata_dataset_shim_future_step"]["planned_action"] == "construct additive Python metadata shim"
    assert plan["actual_dataloader_smoke_blocked_until_metadata_smoke_qa"]["planned_action"] == "keep actual dataloader blocked"
    for key in [
        "metadata_dataloader_smoke_written",
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
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_metadata_dataloader_smoke"] is True
    assert manifest["recommended_next_step"] == "covapie_metadata_dataloader_smoke"


def test_canonical_masks_and_safety_audit() -> None:
    safety = _csv_rows(ROOT / "covapie_dataloader_smoke_design_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    assert manifest["canonical_mask_task_names"] == design.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == design.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_no_forbidden_imports_outputs_or_existing_artifact_diffs() -> None:
    module_path = Path("src/covalent_ext/covapie_dataloader_smoke_design_gate.py")
    script_path = Path("scripts/check_covapie_dataloader_smoke_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden_names = {
        "covapie_metadata_dataloader_smoke_preview.csv",
        "covapie_metadata_dataloader_smoke_preview.json",
        "metadata_dataloader_smoke.csv",
        "metadata_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
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
    tracked = subprocess.run(["git", "ls-files", str(design.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(design.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(design.step13bd.METADATA_CSV.read_bytes()).hexdigest() == design.METADATA_CSV_SHA256
    assert _git_diff_paths([design.step13bs.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13br.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bq.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
