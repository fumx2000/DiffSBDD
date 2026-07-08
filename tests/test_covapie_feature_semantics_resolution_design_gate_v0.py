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

from covalent_ext import covapie_feature_semantics_resolution_design_gate as design


ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_resolution_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_feature_semantics_resolution_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BY check script before artifact tests"
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


def test_step13bx_precondition_and_preview_shapes() -> None:
    manifest13bx = json.loads(design.step13bx.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_feature_semantics_resolution_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bx["stage"] == design.PREVIOUS_STAGE
    assert manifest13bx["all_checks_passed"] is True
    assert manifest13bx["ready_for_covapie_feature_semantics_resolution_design_gate"] is True
    assert manifest13bx["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest13bx["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest13bx["ready_for_training"] is False
    assert manifest13bx["ready_to_train_now"] is False
    assert manifest13bx["feature_semantics_known_for_training"] is False
    assert manifest13bx["unknown_atom_feature_policy_finalized_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == design.STAGE
    assert manifest["previous_stage"] == design.PREVIOUS_STAGE
    assert manifest["step13bx_feature_semantics_tensorization_audit_validated"] is True
    assert manifest["source_metadata_smoke_preview_row_count"] == 20
    assert manifest["source_metadata_smoke_preview_column_count"] == 30
    assert manifest["source_final_dataset_preview_row_count"] == 20
    assert manifest["source_final_dataset_preview_column_count"] == 45


def test_original_feature_schema_mapping_design_contract() -> None:
    rows = _csv_rows(ROOT / "covapie_original_diffsbbd_feature_schema_mapping_design.csv")
    manifest = _manifest()
    expected_items = [
        "original_dataset_py_feature_symbols",
        "original_prepare_crossdocked_feature_symbols",
        "original_lightning_batch_key_symbols",
        "original_equivariant_diffusion_feature_symbols",
        "original_atom_encoder_candidate_symbols",
        "original_atom_decoder_candidate_symbols",
        "original_residue_encoder_candidate_symbols",
        "original_feature_dimension_candidate_symbols",
        "original_one_hot_feature_candidate_symbols",
        "original_unknown_atom_candidate_symbols",
        "original_feature_schema_mapping_not_training_final",
        "original_checkpoint_compatibility_requires_static_mapping",
    ]
    assert [row["mapping_item"] for row in rows] == expected_items
    assert len(rows) == 12
    assert {row["training_final_status"] for row in rows} == {"not_training_final"}
    assert {row["blocks_actual_tensor_dataloader_smoke"] for row in rows} == {"True"}
    assert {row["mapping_design_passed"] for row in rows} == {"True"}
    assert manifest["original_diffsbbd_feature_schema_mapping_design_row_count"] == 12
    assert manifest["original_diffsbbd_feature_schema_mapping_design_passed"] is True


def test_coordinate_atom_unknown_label_and_tensor_contracts() -> None:
    coordinate = _csv_rows(ROOT / "covapie_coordinate_tensorization_resolution_contract.csv")
    atom = _csv_rows(ROOT / "covapie_atom_feature_schema_resolution_contract.csv")
    unknown = _csv_rows(ROOT / "covapie_unknown_atom_policy_resolution_contract.csv")
    label = _csv_rows(ROOT / "covapie_label_semantics_resolution_contract.csv")
    tensor = _csv_rows(ROOT / "covapie_tensor_shape_dtype_resolution_contract.csv")
    manifest = _manifest()

    assert len(coordinate) == 8
    assert {row["coordinate_resolution_passed"] for row in coordinate} == {"True"}
    assert {row["ready_for_actual_tensor_smoke"] for row in coordinate} == {"False"}
    assert {row["ready_for_resolution_smoke"] for row in coordinate} == {"True"}

    assert len(atom) == 12
    assert {row["atom_feature_resolution_passed"] for row in atom} == {"True"}
    assert {row["ready_for_actual_tensor_smoke"] for row in atom} == {"False"}
    assert {row["blocks_training"] for row in atom} == {"True"}
    assert {row["ready_for_resolution_smoke"] for row in atom} == {"True"}

    assert len(unknown) == 8
    assert {row["unknown_policy_resolution_passed"] for row in unknown} == {"True"}
    assert {row["finalized_for_training_current_step"] for row in unknown} == {"False"}
    assert {row["ready_for_resolution_smoke"] for row in unknown} == {"True"}

    assert len(label) == 14
    assert {row["label_resolution_passed"] for row in label} == {"True"}
    assert {row["ready_for_actual_tensor_smoke"] for row in label} == {"False"}
    by_label = {row["label_resolution_item"]: row for row in label}
    assert by_label["mask_task_name_string_selector_policy"]["proposed_policy"] == "long semantic mask task names remain source of truth"
    assert by_label["mask_task_alias_display_only_policy"]["proposed_policy"] == "aliases remain display-only labels"
    assert by_label["mask_task_name_string_selector_policy"]["blocks_training"] == "False"
    assert by_label["label_tensorization_actual_smoke_blocked"]["blocks_training"] == "True"

    assert len(tensor) == 10
    assert {row["tensor_policy_passed"] for row in tensor} == {"True"}
    assert {row["ready_for_actual_tensor_smoke"] for row in tensor} == {"False"}
    assert set(row["checkpoint_compatibility_risk"] for row in tensor) <= {"medium", "high"}

    assert manifest["coordinate_tensorization_resolution_contract_row_count"] == 8
    assert manifest["atom_feature_schema_resolution_contract_row_count"] == 12
    assert manifest["unknown_atom_policy_resolution_contract_row_count"] == 8
    assert manifest["label_semantics_resolution_contract_row_count"] == 14
    assert manifest["tensor_shape_dtype_resolution_contract_row_count"] == 10
    assert manifest["coordinate_tensorization_resolution_contract_passed"] is True
    assert manifest["atom_feature_schema_resolution_contract_passed"] is True
    assert manifest["unknown_atom_policy_resolution_contract_passed"] is True
    assert manifest["label_semantics_resolution_contract_passed"] is True
    assert manifest["tensor_shape_dtype_resolution_contract_passed"] is True


def test_resolution_smoke_plan_and_readiness_boundary() -> None:
    plan = _csv_rows(ROOT / "covapie_feature_semantics_resolution_smoke_plan.csv")
    manifest = _manifest()
    assert len(plan) == 8
    assert [row["planned_step"] for row in plan] == [
        "read_resolution_design_contracts",
        "validate_original_feature_schema_mapping_candidates",
        "validate_coordinate_policy_against_derived_tables",
        "validate_atom_feature_policy_against_derived_tables",
        "validate_unknown_atom_policy_against_derived_tables",
        "validate_label_policy_against_final_dataset_preview",
        "produce_resolution_smoke_audits_without_tensors",
        "keep_actual_dataloader_smoke_blocked",
    ]
    assert {row["resolution_smoke_plan_passed"] for row in plan} == {"True"}
    assert "actual dataloader smoke" in plan[-1]["blocked_outputs_current_step"]
    assert manifest["feature_semantics_resolution_smoke_plan_row_count"] == 8
    assert manifest["feature_semantics_resolution_smoke_plan_passed"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["proposed_feature_schema_resolution_written"] is True
    assert manifest["proposed_unknown_atom_policy_written"] is True
    assert manifest["proposed_label_semantics_resolution_written"] is True
    assert manifest["coordinate_resolution_ready_for_smoke"] is True
    assert manifest["atom_feature_resolution_ready_for_smoke"] is True
    assert manifest["unknown_policy_resolution_ready_for_smoke"] is True
    assert manifest["label_semantics_resolution_ready_for_smoke"] is True
    assert manifest["ready_for_covapie_feature_semantics_resolution_smoke"] is True
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_feature_semantics_resolution_smoke"


def test_manifest_preserves_masks_and_runtime_boundaries() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_names"] == design.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == design.CANONICAL_MASK_TASK_ALIASES
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


def test_safety_no_forbidden_outputs_or_imports_and_raw_untracked() -> None:
    safety = _csv_rows(ROOT / "covapie_feature_semantics_resolution_safety_audit.csv")
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

    module_path = Path("src/covalent_ext/covapie_feature_semantics_resolution_design_gate.py")
    script_path = Path("scripts/check_covapie_feature_semantics_resolution_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)

    tracked = subprocess.run(["git", "ls-files", str(design.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(design.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []


def test_existing_artifacts_unchanged_and_metadata_hash_stable() -> None:
    assert hashlib.sha256(design.step13bd.METADATA_CSV.read_bytes()).hexdigest() == design.METADATA_CSV_SHA256
    assert _git_diff_paths([design.step13bx.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bw.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bu.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([design.step13bm.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
