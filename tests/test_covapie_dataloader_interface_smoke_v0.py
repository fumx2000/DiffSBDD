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

from covalent_ext import covapie_dataloader_interface_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_dataloader_interface_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_dataloader_interface_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BR check script before artifact tests"
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


def test_step13bq_precondition_and_readiness() -> None:
    manifest13bq = json.loads(smoke.step13bq.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_dataloader_interface_smoke_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bq["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13bq["all_checks_passed"] is True
    assert manifest13bq["ready_for_covapie_dataloader_interface_smoke"] is True
    assert manifest13bq["ready_for_covapie_dataloader_interface_qa_gate"] is False
    assert manifest13bq["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bq["ready_for_training"] is False
    assert manifest13bq["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13bq_dataloader_interface_design_gate_validated"] is True


def test_interface_smoke_preview_csv_json_and_row_identity() -> None:
    preview = _csv_rows(ROOT / "covapie_dataloader_interface_smoke_preview.csv")
    json_rows = json.loads((ROOT / "covapie_dataloader_interface_smoke_preview.json").read_text(encoding="utf-8"))
    source = _csv_rows(smoke.step13bo.SMOKE_PREVIEW_CSV)
    manifest = _manifest()
    assert len(preview) == 20
    assert len(json_rows) == 20
    assert len(preview[0]) == 35
    assert list(preview[0].keys()) == smoke.INTERFACE_SMOKE_PREVIEW_COLUMNS
    assert json_rows == preview
    assert [row["final_dataset_row_id"] for row in preview] == [row["final_dataset_row_id"] for row in source]
    assert [row["sample_id"] for row in preview] == [row["sample_id"] for row in source]
    assert [row["split_unit_id"] for row in preview] == [row["split_unit_id"] for row in source]
    assert [row["extracted_event_id"] for row in preview] == [row["extracted_event_id"] for row in source]
    for row in preview:
        assert row["dataloader_interface_smoke_row_id"] == f"dataloader_interface_smoke::{row['final_dataset_row_id']}"
        assert row["future_protein_xyz_key"] == "protein.x"
        assert row["future_ligand_xyz_key"] == "ligand.x"
        assert row["future_mask_selector_key"] == "mask.task_name"
        assert row["dataloader_interface_smoke_materialized_current_step"] == "True"
        assert row["actual_dataloader_smoke_written"] == "False"
        assert row["real_dataloader_written"] == "False"
        assert row["torch_tensor_created_current_step"] == "False"
        assert row["checkpoint_loaded_current_step"] == "False"
        assert row["model_forward_called_current_step"] == "False"
        assert row["ready_for_training"] == "False"
    assert manifest["dataloader_interface_smoke_preview_csv_written"] is True
    assert manifest["dataloader_interface_smoke_preview_json_written"] is True
    assert manifest["dataloader_interface_smoke_preview_row_count"] == 20
    assert manifest["dataloader_interface_smoke_preview_column_count"] == 35


def test_input_source_field_mapping_and_feature_batch_audits() -> None:
    input_rows = _csv_rows(ROOT / "covapie_dataloader_interface_input_source_smoke_audit.csv")
    field_rows = _csv_rows(ROOT / "covapie_dataloader_interface_field_mapping_smoke_audit.csv")
    feature_batch = _csv_rows(ROOT / "covapie_dataloader_interface_feature_batch_smoke_audit.csv")
    manifest = _manifest()
    assert len(input_rows) == 15
    assert {row["source_exists_or_policy_valid"] for row in input_rows} == {"True"}
    assert {row["runtime_dependency_used_current_step"] for row in input_rows} == {"False"}
    assert {row["input_source_smoke_passed"] for row in input_rows} == {"True"}
    assert len(field_rows) == 45
    assert {row["source_value_present_in_preview"] for row in field_rows} == {"True"}
    assert {row["tensorization_status_current_step"] for row in field_rows} == {"design_only_no_tensorization_current_step"}
    assert {row["field_mapping_smoke_passed"] for row in field_rows} == {"True"}
    by_field = {row["final_dataset_field_name"]: row for row in field_rows}
    assert by_field["mask_task_name"]["future_dataloader_role"] == "canonical_mask_task_selector_long_name"
    assert by_field["mask_task_alias"]["future_dataloader_role"] == "display_report_only"
    assert by_field["feature_semantics_known_for_training"]["blocker_before_training"] == "True"
    assert by_field["unknown_atom_feature_policy_finalized_for_training"]["blocker_before_training"] == "True"
    assert len(feature_batch) == 26
    assert {row["torch_tensor_created"] for row in feature_batch} == {"False"}
    assert {row["actual_collate_implemented"] for row in feature_batch} == {"False"}
    assert {row["feature_batch_smoke_passed"] for row in feature_batch} == {"True"}
    assert manifest["input_source_smoke_audit_row_count"] == 15
    assert manifest["field_mapping_smoke_audit_row_count"] == 45
    assert manifest["feature_batch_smoke_audit_row_count"] == 26
    assert manifest["input_source_smoke_audit_passed"] is True
    assert manifest["field_mapping_smoke_audit_passed"] is True
    assert manifest["feature_batch_smoke_audit_passed"] is True


def test_mask_and_checkpoint_audits_preserve_boundaries() -> None:
    mask_rows = _csv_rows(ROOT / "covapie_dataloader_interface_mask_smoke_audit.csv")
    checkpoint = _csv_rows(ROOT / "covapie_dataloader_interface_checkpoint_compatibility_smoke_audit.csv")
    manifest = _manifest()
    assert len(mask_rows) == 8
    assert [row["mask_task_name"] for row in mask_rows[:5]] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in mask_rows[:5]] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask_rows[:5]} == {"4"}
    assert {row["current_tensor_materialized"] for row in mask_rows} == {"False"}
    assert {row["mask_interface_smoke_passed"] for row in mask_rows} == {"True"}
    assert len(checkpoint) == 8
    assert {row["checkpoint_loaded"] for row in checkpoint} == {"False"}
    assert {row["model_forward_called"] for row in checkpoint} == {"False"}
    assert {row["original_dataloader_modified"] for row in checkpoint} == {"False"}
    assert {row["compatibility_smoke_passed"] for row in checkpoint} == {"True"}
    assert manifest["mask_interface_smoke_audit_row_count"] == 8
    assert manifest["checkpoint_compatibility_smoke_audit_row_count"] == 8
    assert manifest["mask_interface_smoke_audit_passed"] is True
    assert manifest["checkpoint_compatibility_smoke_audit_passed"] is True
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_runtime_training_and_readiness_boundaries() -> None:
    manifest = _manifest()
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
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["dataloader_interface_smoke_preview_written_current_step"] is True
    assert manifest["ready_for_covapie_dataloader_interface_qa_gate"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_dataloader_interface_qa_gate"


def test_boundary_git_safety_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_dataloader_interface_smoke_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_dataloader_interface_smoke_git_safety.csv")
    manifest = _manifest()
    assert boundary["dataloader_interface_smoke"]["current_step_status"] == "executed_interface_smoke_preview_only"
    assert boundary["dataloader_interface_smoke_preview_write"]["current_step_status"] == "executed_interface_smoke_preview_only"
    for item in ["actual_dataloader_smoke_write", "real_dataloader_write", "original_dataloader_modify", "torch_import", "tensor_creation", "checkpoint_load", "model_forward", "loss_backward_optimizer", "final_dataset_write", "new_sample_index_write", "split_assignment_write", "leakage_matrix_write", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "raw_cif_mmcif_sdf_pdb_gzip_read", "mmcif_parse", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    forbidden_names = {"dataloader_smoke.csv", "dataloader_smoke.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "final_dataset.csv", "final_dataset.json", "final_dataset_smoke.csv", "final_dataset_smoke.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json"}
    allowed = {"covapie_dataloader_interface_smoke_preview.csv", "covapie_dataloader_interface_smoke_preview.json"}
    assert not any(path.name in forbidden_names and path.name not in allowed for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True


def test_no_forbidden_imports_and_existing_artifacts_unchanged() -> None:
    module_path = Path("src/covalent_ext/covapie_dataloader_interface_smoke.py")
    script_path = Path("scripts/check_covapie_dataloader_interface_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(smoke.step13bd.METADATA_CSV.read_bytes()).hexdigest() == smoke.METADATA_CSV_SHA256
    assert _git_diff_paths(
        [
            "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
            smoke.step13bq.OUTPUT_ROOT.as_posix(),
            smoke.step13bp.OUTPUT_ROOT.as_posix(),
            smoke.step13bo.OUTPUT_ROOT.as_posix(),
            smoke.step13bn.OUTPUT_ROOT.as_posix(),
            smoke.step13bm.OUTPUT_ROOT.as_posix(),
            smoke.step13bl.OUTPUT_ROOT.as_posix(),
            smoke.step13bk.OUTPUT_ROOT.as_posix(),
            smoke.step13bj.OUTPUT_ROOT.as_posix(),
            smoke.step13bi.OUTPUT_ROOT.as_posix(),
            smoke.step13bh.OUTPUT_ROOT.as_posix(),
            smoke.step13bg.OUTPUT_ROOT.as_posix(),
            smoke.step13bf.OUTPUT_ROOT.as_posix(),
            smoke.step13be.OUTPUT_ROOT.as_posix(),
            "data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0",
            "equivariant_diffusion/",
            "lightning_modules.py",
            "dataset.py",
            "data/prepare_crossdocked.py",
        ]
    ) == []
    assert _manifest()["all_checks_passed"] is True
