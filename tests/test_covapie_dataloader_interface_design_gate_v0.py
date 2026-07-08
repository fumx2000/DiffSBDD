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

from covalent_ext import covapie_dataloader_interface_design_gate as design_gate


ROOT = Path("data/derived/covalent_small/covapie_dataloader_interface_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_dataloader_interface_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BQ check script before artifact tests"
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


def test_step13bp_precondition_and_readiness_boundary() -> None:
    manifest13bp = json.loads(design_gate.step13bp.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_dataloader_interface_design_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bp["stage"] == design_gate.PREVIOUS_STAGE
    assert manifest13bp["all_checks_passed"] is True
    assert manifest13bp["ready_for_covapie_dataloader_interface_design_gate"] is True
    assert manifest13bp["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bp["ready_for_training"] is False
    assert manifest13bp["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design_gate.STAGE
    assert manifest["previous_stage"] == design_gate.PREVIOUS_STAGE
    assert manifest["step13bp_final_dataset_qa_gate_validated"] is True
    assert manifest["source_preview_row_count"] == 20
    assert manifest["source_preview_column_count"] == 45
    assert manifest["source_unique_event_count"] == 4
    assert manifest["source_unique_split_unit_count"] == 4
    assert manifest["source_canonical_mask_task_count"] == 5


def test_input_source_and_field_mapping_contracts() -> None:
    input_rows = _csv_rows(ROOT / "covapie_dataloader_input_source_contract.csv")
    field_rows = _csv_rows(ROOT / "covapie_dataloader_field_mapping_contract.csv")
    schema_fields = [row["final_dataset_field_name"] for row in _csv_rows(design_gate.step13bn.SCHEMA_CONTRACT_CSV)]
    manifest = _manifest()
    assert len(input_rows) == 15
    assert [row["input_source_name"] for row in input_rows] == [
        "final_dataset_smoke_preview_csv",
        "final_dataset_smoke_preview_json",
        "protein_pocket_atom_table",
        "ligand_atom_table",
        "feature_semantics_contract",
        "mask_conditioning_semantics_audit",
        "split_unit_smoke_preview",
        "final_dataset_qa_manifest",
        "dataset_py_static_reference",
        "prepare_crossdocked_static_reference",
        "lightning_modules_static_reference",
        "equivariant_diffusion_static_reference",
        "checkpoint_path_reference_only",
        "no_torch_runtime_dependency_current_step",
        "no_raw_files_current_step",
    ]
    assert {row["input_source_contract_passed"] for row in input_rows} == {"True"}
    assert {row["current_step_access_status"] for row in input_rows if row["source_type"] == "source_text"} == {"static_text_reference_only"}
    assert len(field_rows) == 45
    assert [row["final_dataset_field_name"] for row in field_rows] == schema_fields
    assert {row["field_mapping_contract_passed"] for row in field_rows} == {"True"}
    assert {row["tensorization_status_current_step"] for row in field_rows} == {"design_only_no_tensorization_current_step"}
    by_field = {row["final_dataset_field_name"]: row for row in field_rows}
    assert by_field["sample_id"]["future_dataloader_role"] == "metadata_key_not_tensor"
    assert by_field["protein_pocket_atom_table_path"]["future_dataloader_role"] == "future_protein_atom_table_loader_input"
    assert by_field["ligand_atom_table_path"]["future_dataloader_role"] == "future_ligand_atom_table_loader_input"
    assert by_field["mask_task_name"]["future_dataloader_role"] == "canonical_mask_task_selector_long_name"
    assert by_field["mask_task_alias"]["future_dataloader_role"] == "display_report_only"
    assert by_field["feature_semantics_known_for_training"]["blocker_before_training"] == "True"
    assert by_field["unknown_atom_feature_policy_finalized_for_training"]["blocker_before_training"] == "True"
    assert manifest["dataloader_input_source_contract_row_count"] == 15
    assert manifest["dataloader_field_mapping_contract_row_count"] == 45
    assert manifest["dataloader_input_source_contract_passed"] is True
    assert manifest["dataloader_field_mapping_contract_passed"] is True


def test_feature_mask_batch_checkpoint_and_plan_contracts() -> None:
    feature_rows = _csv_rows(ROOT / "covapie_dataloader_feature_interface_contract.csv")
    mask_rows = _csv_rows(ROOT / "covapie_dataloader_mask_interface_contract.csv")
    batch_rows = _csv_rows(ROOT / "covapie_dataloader_batch_collate_contract.csv")
    checkpoint_rows = _csv_rows(ROOT / "covapie_dataloader_checkpoint_compatibility_contract.csv")
    plan_rows = _csv_rows(ROOT / "covapie_dataloader_interface_smoke_plan.csv")
    manifest = _manifest()
    assert len(feature_rows) == 16
    assert {row["current_step_materialized"] for row in feature_rows} == {"False"}
    assert {row["feature_interface_contract_passed"] for row in feature_rows} == {"True"}
    assert len(mask_rows) == 8
    assert [row["mask_task_name"] for row in mask_rows[:5]] == design_gate.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in mask_rows[:5]] == design_gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask_rows[:5]} == {"4"}
    assert {row["current_tensor_materialized"] for row in mask_rows} == {"False"}
    assert {row["mask_interface_contract_passed"] for row in mask_rows} == {"True"}
    assert len(batch_rows) == 10
    assert {row["current_step_status"] for row in batch_rows} == {"design_only_not_implemented"}
    assert {row["batch_collate_contract_passed"] for row in batch_rows} == {"True"}
    assert len(checkpoint_rows) == 8
    assert {row["checkpoint_compatibility_contract_passed"] for row in checkpoint_rows} == {"True"}
    assert {row["compatibility_item"] for row in checkpoint_rows} >= {"original_diffsbbd_model_unchanged", "original_diffsbbd_dataloader_unchanged", "checkpoint_not_loaded", "no_model_forward"}
    assert len(plan_rows) == 10
    assert {row["smoke_plan_passed"] for row in plan_rows} == {"True"}
    assert "real_dataloader_smoke_blocked_until_interface_qa" in {row["planned_step"] for row in plan_rows}
    assert "training_blocked_until_real_dataloader_and_training_gates" in {row["planned_step"] for row in plan_rows}
    assert manifest["dataloader_feature_interface_contract_row_count"] == 16
    assert manifest["dataloader_mask_interface_contract_row_count"] == 8
    assert manifest["dataloader_batch_collate_contract_row_count"] == 10
    assert manifest["checkpoint_compatibility_contract_row_count"] == 8
    assert manifest["dataloader_interface_smoke_plan_row_count"] == 10
    assert manifest["dataloader_feature_interface_contract_passed"] is True
    assert manifest["dataloader_mask_interface_contract_passed"] is True
    assert manifest["dataloader_batch_collate_contract_passed"] is True
    assert manifest["checkpoint_compatibility_contract_passed"] is True
    assert manifest["dataloader_interface_smoke_plan_passed"] is True


def test_canonical_masks_readiness_and_blockers_preserved() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_names"] == design_gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == design_gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    for key in [
        "dataloader_interface_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_dataloader_interface_qa_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_dataloader_interface_smoke"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_dataloader_interface_smoke"


def test_boundary_and_git_safety_contracts() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_dataloader_interface_design_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_dataloader_interface_design_git_safety.csv")
    manifest = _manifest()
    assert boundary["dataloader_interface_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert boundary["static_original_dataloader_source_read"]["current_step_status"] == "executed_static_text_reference_only"
    for item in ["dataloader_interface_smoke_write", "real_dataloader_write", "original_dataloader_modify", "torch_import", "tensor_creation", "checkpoint_load", "model_forward", "loss_backward_optimizer", "final_dataset_write", "new_sample_index_write", "split_assignment_write", "leakage_matrix_write", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "raw_cif_mmcif_sdf_pdb_gzip_read", "mmcif_parse", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True


def test_no_forbidden_outputs_or_runtime_imports() -> None:
    module_path = Path("src/covalent_ext/covapie_dataloader_interface_design_gate.py")
    script_path = Path("scripts/check_covapie_dataloader_interface_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden_names = {
        "dataloader_interface_smoke.csv",
        "dataloader_interface_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
        "final_dataset.csv",
        "final_dataset.json",
        "final_dataset_smoke.csv",
        "final_dataset_smoke.json",
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
    manifest = _manifest()
    for key in [
        "torch_imported",
        "torch_tensor_created",
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


def test_raw_files_and_existing_artifacts_remain_unchanged() -> None:
    tracked = subprocess.run(["git", "ls-files", str(design_gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(design_gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(design_gate.step13bd.METADATA_CSV.read_bytes()).hexdigest() == design_gate.METADATA_CSV_SHA256
    assert _git_diff_paths(
        [
            "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
            design_gate.step13bp.OUTPUT_ROOT.as_posix(),
            design_gate.step13bo.OUTPUT_ROOT.as_posix(),
            design_gate.step13bn.OUTPUT_ROOT.as_posix(),
            design_gate.step13bm.OUTPUT_ROOT.as_posix(),
            design_gate.step13bl.OUTPUT_ROOT.as_posix(),
            design_gate.step13bk.OUTPUT_ROOT.as_posix(),
            design_gate.step13bj.OUTPUT_ROOT.as_posix(),
            design_gate.step13bi.OUTPUT_ROOT.as_posix(),
            design_gate.step13bh.OUTPUT_ROOT.as_posix(),
            design_gate.step13bg.OUTPUT_ROOT.as_posix(),
            design_gate.step13bf.OUTPUT_ROOT.as_posix(),
            design_gate.step13be.OUTPUT_ROOT.as_posix(),
            "data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0",
            "equivariant_diffusion/",
            "lightning_modules.py",
            "dataset.py",
            "data/prepare_crossdocked.py",
        ]
    ) == []
    assert _manifest()["all_checks_passed"] is True
