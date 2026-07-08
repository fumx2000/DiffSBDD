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

from covalent_ext import covapie_feature_semantics_tensorization_audit_gate as audit


ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_tensorization_audit_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_feature_semantics_tensorization_audit_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BX check script before artifact tests"
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


def test_step13bw_precondition_and_source_shapes() -> None:
    manifest13bw = json.loads(audit.step13bw.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_feature_semantics_tensorization_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bw["stage"] == audit.PREVIOUS_STAGE
    assert manifest13bw["all_checks_passed"] is True
    assert manifest13bw["ready_for_covapie_feature_semantics_tensorization_audit_gate"] is True
    assert manifest13bw["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest13bw["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest13bw["ready_for_training"] is False
    assert manifest13bw["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == audit.STAGE
    assert manifest["previous_stage"] == audit.PREVIOUS_STAGE
    assert manifest["step13bw_actual_dataloader_design_gate_validated"] is True
    assert manifest["source_metadata_smoke_preview_row_count"] == 20
    assert manifest["source_metadata_smoke_preview_column_count"] == 30
    assert manifest["source_final_dataset_preview_row_count"] == 20
    assert manifest["source_final_dataset_preview_column_count"] == 45


def test_static_source_and_coordinate_tensorization_audits() -> None:
    static = _csv_rows(ROOT / "covapie_original_feature_source_static_audit.csv")
    coordinate = _csv_rows(ROOT / "covapie_coordinate_tensorization_semantics_audit.csv")
    manifest = _manifest()
    assert len(static) == 12
    assert {row["source_audit_passed"] for row in static} == {"True"}
    by_static = {row["source_audit_item"]: row for row in static}
    assert by_static["dataset_py_static_feature_reference"]["observed_status"] == "static_read_only"
    assert by_static["existing_atom_encoder_symbols_search"]["observed_status"] == "static_search_completed"
    assert by_static["existing_unknown_atom_handling_search"]["observed_status"] == "static_search_completed"
    assert by_static["original_dataloader_no_diff"]["observed_status"] == "no_diff"
    assert by_static["protected_model_code_no_diff"]["observed_status"] == "no_diff"
    assert len(coordinate) == 8
    assert {row["coordinate_audit_passed"] for row in coordinate} == {"True"}
    assert {row["current_step_tensorized"] for row in coordinate} == {"False"}
    by_coordinate = {row["coordinate_item"]: row for row in coordinate}
    assert by_coordinate["protein_xyz_source_path_refs"]["future_tensor_key"] == "protein_xyz"
    assert by_coordinate["ligand_xyz_source_path_refs"]["future_tensor_key"] == "ligand_xyz"
    assert by_coordinate["coordinate_tensor_candidate_future"]["observed_status"] == "candidate_for_future_design_only"
    assert manifest["original_feature_source_static_audit_row_count"] == 12
    assert manifest["coordinate_tensorization_semantics_audit_row_count"] == 8
    assert manifest["coordinate_tensor_candidate_for_future_design"] is True


def test_atom_unknown_and_label_blocker_audits_keep_tensorization_blocked() -> None:
    atom = _csv_rows(ROOT / "covapie_atom_feature_semantics_audit.csv")
    unknown = _csv_rows(ROOT / "covapie_unknown_atom_policy_audit.csv")
    label = _csv_rows(ROOT / "covapie_label_tensorization_blocker_audit.csv")
    manifest = _manifest()
    assert len(atom) == 10
    assert {row["atom_feature_audit_passed"] for row in atom} == {"True"}
    assert {row["blocks_actual_tensor_dataloader_smoke"] for row in atom} == {"True"}
    assert {row["blocks_training"] for row in atom} == {"True"}
    atom_by_item = {row["atom_feature_item"]: row for row in atom}
    assert atom_by_item["atom_feature_tensorization_blocked"]["observed_status"] == "blocked_current_step"
    assert len(unknown) == 8
    assert {row["unknown_policy_audit_passed"] for row in unknown} == {"True"}
    assert {row["blocks_actual_tensor_dataloader_smoke"] for row in unknown} == {"True"}
    assert {row["blocks_training"] for row in unknown} == {"True"}
    unknown_by_item = {row["unknown_policy_item"]: row for row in unknown}
    assert unknown_by_item["unknown_atom_feature_policy_finalized_for_training_false"]["observed_status"] == "unknown_atom_feature_policy_finalized_for_training=false"
    assert len(label) == 12
    assert {row["label_blocker_audit_passed"] for row in label} == {"True"}
    label_by_item = {row["label_blocker_item"]: row for row in label}
    assert label_by_item["mask_task_name_string_selector_ok_for_metadata"]["current_tensorization_status"] == "metadata_only_not_tensorized"
    assert label_by_item["mask_boolean_tensor_blocked_until_group_labels"]["blocks_actual_tensor_dataloader_smoke"] == "True"
    assert label_by_item["training_targets_blocked"]["blocks_training"] == "True"
    assert manifest["atom_feature_tensorization_ready"] is False
    assert manifest["mask_boolean_tensorization_ready"] is False
    assert manifest["auxiliary_label_tensorization_ready"] is False


def test_readiness_decision_and_resolution_plan_select_resolution_gate() -> None:
    readiness = _csv_rows(ROOT / "covapie_tensorization_readiness_decision_contract.csv")
    resolution = _csv_rows(ROOT / "covapie_feature_semantics_resolution_plan.csv")
    manifest = _manifest()
    assert len(readiness) == 10
    assert {row["readiness_decision_passed"] for row in readiness} == {"True"}
    by_readiness = {row["readiness_decision_item"]: row for row in readiness}
    assert by_readiness["coordinate_tensor_candidate_ready_for_design_only"]["ready_current_step"] == "True"
    assert by_readiness["atom_feature_tensorization_not_ready"]["ready_current_step"] == "False"
    assert by_readiness["actual_dataloader_adapter_smoke_not_ready"]["ready_current_step"] == "False"
    assert by_readiness["formal_training_not_ready"]["ready_current_step"] == "False"
    assert len(resolution) == 8
    assert {row["resolution_plan_passed"] for row in resolution} == {"True"}
    by_resolution = {row["resolution_item"]: row for row in resolution}
    assert by_resolution["resolve_unknown_atom_policy"]["expected_future_output"] == "unknown atom policy contract"
    assert "actual dataloader smoke" in by_resolution["resolve_covapie_ligand_atom_feature_schema"]["blocked_outputs_current_step"]
    assert manifest["ready_for_covapie_feature_semantics_resolution_design_gate"] is True
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_feature_semantics_resolution_design_gate"


def test_manifest_preserves_blockers_masks_and_runtime_boundaries() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_tensorization_audit_completed_current_step"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["canonical_mask_task_names"] == audit.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == audit.CANONICAL_MASK_TASK_ALIASES
    assert manifest["source_canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
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


def test_safety_audit_no_forbidden_outputs_or_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_feature_semantics_tensorization_safety_audit.csv")
    assert len(safety) == 23
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
    module_path = Path("src/covalent_ext/covapie_feature_semantics_tensorization_audit_gate.py")
    script_path = Path("scripts/check_covapie_feature_semantics_tensorization_audit_gate_v0.py")
    for name in ["urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)


def test_raw_files_untracked_metadata_hash_and_existing_artifacts_unchanged() -> None:
    tracked = subprocess.run(["git", "ls-files", str(audit.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(audit.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(audit.step13bd.METADATA_CSV.read_bytes()).hexdigest() == audit.METADATA_CSV_SHA256
    assert _git_diff_paths([audit.step13bw.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([audit.step13bv.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([audit.step13bu.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([audit.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([audit.step13bm.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
