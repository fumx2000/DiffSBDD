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

from covalent_ext import covapie_metadata_dataloader_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_metadata_dataloader_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_metadata_dataloader_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BU check script before artifact tests"
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


def test_step13bt_precondition_and_readiness() -> None:
    manifest13bt = json.loads(smoke.step13bt.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_metadata_dataloader_smoke_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bt["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13bt["all_checks_passed"] is True
    assert manifest13bt["ready_for_covapie_metadata_dataloader_smoke"] is True
    assert manifest13bt["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest13bt["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13bt_dataloader_smoke_design_gate_validated"] is True


def test_metadata_dataset_shim_len_getitem_and_index_error() -> None:
    dataset = smoke.CovapieMetadataDatasetSmoke(smoke.step13br.INTERFACE_SMOKE_PREVIEW_CSV, smoke.step13bo.SMOKE_PREVIEW_CSV)
    assert len(dataset) == 20
    for index in [0, 10, 19]:
        item = dataset[index]
        assert isinstance(item, dict)
        assert item["metadata_dataset_row_id"] == f"metadata_dataloader_smoke::{item['identity']['dataloader_interface_smoke_row_id']}"
        assert set(["identity", "path_refs", "atom_counts", "mask", "conditioning", "covalent_geometry", "future_keys", "blockers", "checkpoint_compatibility_refs"]) <= set(item)
        assert item["mask"]["mask_task_name_is_source_of_truth"] is True
        assert item["mask"]["mask_task_alias_is_display_only"] is True
        assert item["blockers"]["ready_for_training"] is False
    try:
        dataset[len(dataset)]
    except IndexError:
        pass
    else:
        raise AssertionError("out-of-range __getitem__ did not raise IndexError")


def test_smoke_preview_csv_json_shape_consistency_and_order() -> None:
    preview = _csv_rows(ROOT / "covapie_metadata_dataloader_smoke_preview.csv")
    json_rows = json.loads((ROOT / "covapie_metadata_dataloader_smoke_preview.json").read_text(encoding="utf-8"))
    source = _csv_rows(smoke.step13br.INTERFACE_SMOKE_PREVIEW_CSV)
    manifest = _manifest()
    assert len(preview) == 20
    assert len(preview[0]) == 30
    assert json_rows == preview
    assert [row["dataloader_interface_smoke_row_id"] for row in preview] == [row["dataloader_interface_smoke_row_id"] for row in source]
    for index, row in enumerate(preview):
        assert row["metadata_dataset_row_id"] == f"metadata_dataloader_smoke::{row['dataloader_interface_smoke_row_id']}"
        assert row["getitem_index"] == str(index)
        assert row["has_identity_metadata"] == "True"
        assert row["has_path_refs"] == "True"
        assert row["has_blocker_flags"] == "True"
        assert row["contains_tensor_values"] == "False"
        assert row["ready_for_training"] == "False"
    assert manifest["metadata_dataset_len"] == 20
    assert manifest["metadata_dataloader_smoke_preview_row_count"] == 20
    assert manifest["metadata_dataloader_smoke_preview_column_count"] == 30


def test_len_getitem_and_key_coverage_audits() -> None:
    len_rows = _csv_rows(ROOT / "covapie_metadata_dataset_len_getitem_audit.csv")
    key_rows = _csv_rows(ROOT / "covapie_metadata_getitem_key_coverage_audit.csv")
    manifest = _manifest()
    assert len(len_rows) == 20
    assert {row["len_value"] for row in len_rows} == {"20"}
    assert {row["getitem_return_type"] for row in len_rows} == {"dict"}
    assert {row["index_in_bounds"] for row in len_rows} == {"True"}
    assert {row["index_error_checked"] for row in len_rows} == {"True"}
    assert {row["returns_python_dict"] for row in len_rows} == {"True"}
    assert {row["contains_tensor_values"] for row in len_rows} == {"False"}
    assert {row["contains_numpy_values"] for row in len_rows} == {"False"}
    assert {row["len_getitem_audit_passed"] for row in len_rows} == {"True"}
    assert len(key_rows) == 12
    assert {row["observed_in_all_getitems"] for row in key_rows} == {"True"}
    assert {row["python_type_policy_satisfied"] for row in key_rows} == {"True"}
    assert {row["tensorization_status"] for row in key_rows} == {"not_tensorized_metadata_only"}
    assert {row["key_coverage_passed"] for row in key_rows} == {"True"}
    assert manifest["out_of_range_index_error_checked"] is True
    assert manifest["len_getitem_audit_passed"] is True
    assert manifest["key_coverage_audit_passed"] is True


def test_mask_distribution_and_blocker_runtime_audits() -> None:
    masks = _csv_rows(ROOT / "covapie_metadata_mask_distribution_audit.csv")
    blockers = _csv_rows(ROOT / "covapie_metadata_blocker_runtime_audit.csv")
    manifest = _manifest()
    assert len(masks) == 5
    assert [row["mask_task_name"] for row in masks] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in masks] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in masks} == {"4"}
    assert {row["observed_unique_event_count"] for row in masks} == {"4"}
    assert {row["mask_task_name_is_source_of_truth"] for row in masks} == {"True"}
    assert {row["mask_task_alias_is_display_only"] for row in masks} == {"True"}
    assert {row["mask_distribution_passed"] for row in masks} == {"True"}
    assert len(blockers) == 12
    assert {row["preserved_in_all_getitems"] for row in blockers} == {"True"}
    assert {row["blocker_runtime_passed"] for row in blockers} == {"True"}
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["mask_distribution_audit_passed"] is True
    assert manifest["blocker_runtime_audit_passed"] is True


def test_runtime_boundary_no_actual_dataloader_or_training() -> None:
    manifest = _manifest()
    assert manifest["metadata_dataloader_smoke_written"] is True
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
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_parse_current_step",
        "coordinate_extraction_current_step",
        "network_access_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "gzip_open_used",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_metadata_dataloader_smoke_qa_gate"] is True
    assert manifest["recommended_next_step"] == "covapie_metadata_dataloader_smoke_qa_gate"


def test_no_forbidden_imports_outputs_or_existing_artifact_diffs() -> None:
    module_path = Path("src/covalent_ext/covapie_metadata_dataloader_smoke.py")
    script_path = Path("scripts/check_covapie_metadata_dataloader_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex", "numpy"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden_names = {
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
    allowed = {"covapie_metadata_dataloader_smoke_preview.csv", "covapie_metadata_dataloader_smoke_preview.json"}
    assert not any(path.name in forbidden_names and path.name not in allowed for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    tracked = subprocess.run(["git", "ls-files", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(smoke.step13bd.METADATA_CSV.read_bytes()).hexdigest() == smoke.METADATA_CSV_SHA256
    assert _git_diff_paths([smoke.step13bt.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([smoke.step13bs.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([smoke.step13br.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([smoke.step13bq.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([smoke.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
