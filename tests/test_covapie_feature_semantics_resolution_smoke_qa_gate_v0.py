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

from covalent_ext import covapie_feature_semantics_resolution_smoke_qa_gate as qa


ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_resolution_smoke_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_feature_semantics_resolution_smoke_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 14A check script before artifact tests"
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


def test_step13bz_precondition_and_manifest_boundary() -> None:
    manifest13bz = json.loads(qa.step13bz.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_feature_semantics_resolution_smoke_qa_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bz["stage"] == qa.PREVIOUS_STAGE
    assert manifest13bz["all_checks_passed"] is True
    assert manifest13bz["ready_for_covapie_feature_semantics_resolution_smoke_qa_gate"] is True
    assert manifest13bz["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest13bz["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest13bz["ready_for_training"] is False
    assert manifest13bz["ready_to_train_now"] is False
    assert manifest13bz["feature_semantics_known_for_training"] is False
    assert manifest13bz["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest13bz["proposed_feature_schema_resolution_validated_by_smoke"] is True
    assert manifest13bz["proposed_unknown_atom_policy_validated_by_smoke"] is True
    assert manifest13bz["proposed_label_semantics_validated_by_smoke"] is True
    assert manifest13bz["derived_atom_tables_read_only"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == qa.STAGE
    assert manifest["step_label"] == "Step 14A"
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["step13bz_feature_semantics_resolution_smoke_validated"] is True
    assert manifest["source_feature_schema_mapping_smoke_row_count"] == 12
    assert manifest["source_coordinate_policy_smoke_row_count"] == 8
    assert manifest["source_atom_feature_policy_smoke_row_count"] == 12
    assert manifest["source_unknown_atom_policy_smoke_row_count"] == 8
    assert manifest["source_label_policy_smoke_row_count"] == 14
    assert manifest["source_tensor_shape_dtype_policy_smoke_row_count"] == 10
    assert manifest["source_readiness_smoke_row_count"] == 10


def test_feature_schema_coordinate_atom_unknown_label_tensor_qa_rows() -> None:
    feature = _csv_rows(ROOT / "covapie_feature_schema_mapping_smoke_qa_audit.csv")
    coordinate = _csv_rows(ROOT / "covapie_coordinate_policy_smoke_qa_audit.csv")
    atom = _csv_rows(ROOT / "covapie_atom_feature_policy_smoke_qa_audit.csv")
    unknown = _csv_rows(ROOT / "covapie_unknown_atom_policy_smoke_qa_audit.csv")
    label = _csv_rows(ROOT / "covapie_label_policy_smoke_qa_audit.csv")
    tensor = _csv_rows(ROOT / "covapie_tensor_shape_dtype_policy_smoke_qa_audit.csv")
    manifest = _manifest()

    assert len(feature) == 12
    assert {row["source_smoke_row_found"] for row in feature} == {"True"}
    assert {row["observed_passed_status"] for row in feature} == {"True"}
    assert {row["training_final_status"] for row in feature} == {"not_training_final"}
    assert {row["actual_tensor_smoke_allowed"] for row in feature} == {"False"}
    assert {row["qa_passed"] for row in feature} == {"True"}

    assert len(coordinate) == 8
    assert {row["source_smoke_row_found"] for row in coordinate} == {"True"}
    assert {row["observed_passed_status"] for row in coordinate} == {"True"}
    assert {row["derived_table_evidence_found"] for row in coordinate} == {"True"}
    assert {row["coordinate_like_columns_detected"] for row in coordinate} == {"x;y;z"}
    assert {row["current_step_tensorized"] for row in coordinate} == {"False"}
    assert {row["ready_for_actual_tensor_smoke"] for row in coordinate} == {"False"}
    assert {row["qa_passed"] for row in coordinate} == {"True"}

    assert len(atom) == 12
    assert {row["source_smoke_row_found"] for row in atom} == {"True"}
    assert {row["observed_passed_status"] for row in atom} == {"True"}
    assert {row["proposed_policy_status"] for row in atom} == {"candidate_policy_only_not_training_final"}
    assert {row["ready_for_actual_tensor_smoke"] for row in atom} == {"False"}
    assert {row["blocks_training"] for row in atom} == {"True"}
    assert {row["qa_passed"] for row in atom} == {"True"}

    assert len(unknown) == 8
    assert {row["source_smoke_row_found"] for row in unknown} == {"True"}
    assert {row["observed_passed_status"] for row in unknown} == {"True"}
    assert {row["policy_finalized_for_training_current_step"] for row in unknown} == {"False"}
    assert {row["ready_for_actual_tensor_smoke"] for row in unknown} == {"False"}
    assert {row["blocks_training"] for row in unknown} == {"True"}
    assert {row["qa_passed"] for row in unknown} == {"True"}

    assert len(label) == 14
    assert {row["source_smoke_row_found"] for row in label} == {"True"}
    assert {row["observed_passed_status"] for row in label} == {"True"}
    assert {row["mask_task_name_source_of_truth"] for row in label} == {"True"}
    assert {row["mask_task_alias_display_only"] for row in label} == {"True"}
    assert {row["ready_for_actual_tensor_smoke"] for row in label} == {"False"}
    assert {row["qa_passed"] for row in label} == {"True"}
    by_label = {row["qa_item"]: row for row in label}
    assert by_label["mask_task_name_string_selector_policy"]["blocks_training"] == "False"
    assert by_label["mask_task_alias_display_only_policy"]["blocks_training"] == "False"

    assert len(tensor) == 10
    assert {row["source_smoke_row_found"] for row in tensor} == {"True"}
    assert {row["observed_passed_status"] for row in tensor} == {"True"}
    assert {row["current_step_tensorized"] for row in tensor} == {"False"}
    assert {row["ready_for_actual_tensor_smoke"] for row in tensor} == {"False"}
    assert {row["qa_passed"] for row in tensor} == {"True"}
    assert set(row["checkpoint_compatibility_risk"] for row in tensor) <= {"medium", "high"}

    assert manifest["feature_schema_mapping_smoke_qa_passed"] is True
    assert manifest["coordinate_policy_smoke_qa_passed"] is True
    assert manifest["atom_feature_policy_smoke_qa_passed"] is True
    assert manifest["unknown_atom_policy_smoke_qa_passed"] is True
    assert manifest["label_policy_smoke_qa_passed"] is True
    assert manifest["tensor_shape_dtype_policy_smoke_qa_passed"] is True


def test_readiness_qa_bulk_download_boundary_and_masks() -> None:
    readiness = _csv_rows(ROOT / "covapie_feature_semantics_resolution_smoke_readiness_qa_audit.csv")
    manifest = _manifest()
    assert len(readiness) == 10
    assert [row["qa_item"] for row in readiness] == [
        "feature_schema_resolution_smoke_completed",
        "coordinate_policy_smoke_completed",
        "atom_feature_policy_smoke_completed",
        "unknown_atom_policy_smoke_completed",
        "label_policy_smoke_completed",
        "tensor_shape_dtype_policy_smoke_completed",
        "feature_semantics_training_final_still_false",
        "actual_dataloader_adapter_smoke_still_blocked",
        "actual_dataloader_smoke_still_blocked",
        "training_still_blocked",
    ]
    assert {row["source_readiness_row_found"] for row in readiness} == {"True"}
    assert {row["qa_passed"] for row in readiness} == {"True"}
    assert manifest["readiness_smoke_qa_row_count"] == 10
    assert manifest["readiness_smoke_qa_passed"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["proposed_feature_schema_resolution_validated_by_smoke"] is True
    assert manifest["proposed_unknown_atom_policy_validated_by_smoke"] is True
    assert manifest["proposed_label_semantics_validated_by_smoke"] is True
    assert manifest["derived_atom_tables_read_only"] is True
    assert manifest["ready_for_covapie_bulk_download_design_gate"] is True
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_bulk_download_design_gate"
    assert manifest["canonical_mask_task_names"] == qa.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == qa.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_runtime_training_raw_and_dataloader_boundaries() -> None:
    manifest = _manifest()
    for key in [
        "actual_dataloader_adapter_smoke_written",
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
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_safety_no_forbidden_outputs_or_imports_and_raw_untracked() -> None:
    safety = _csv_rows(ROOT / "covapie_feature_semantics_resolution_smoke_qa_safety_audit.csv")
    assert len(safety) == 26
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

    module_path = Path("src/covalent_ext/covapie_feature_semantics_resolution_smoke_qa_gate.py")
    script_path = Path("scripts/check_covapie_feature_semantics_resolution_smoke_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)

    tracked = subprocess.run(["git", "ls-files", str(qa.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(qa.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []


def test_existing_artifacts_unchanged_and_metadata_hash_stable() -> None:
    assert hashlib.sha256(qa.step13bd.METADATA_CSV.read_bytes()).hexdigest() == qa.METADATA_CSV_SHA256
    assert _git_diff_paths([qa.step13bz.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13by.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bx.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bw.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bu.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bm.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
