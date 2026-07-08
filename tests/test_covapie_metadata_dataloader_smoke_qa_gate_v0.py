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

from covalent_ext import covapie_metadata_dataloader_smoke_qa_gate as qa


ROOT = Path("data/derived/covalent_small/covapie_metadata_dataloader_smoke_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_metadata_dataloader_smoke_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BV check script before artifact tests"
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


def test_step13bu_precondition_and_preview_shape() -> None:
    manifest13bu = json.loads(qa.step13bu.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_metadata_dataloader_smoke_qa_precondition_audit.csv")
    manifest = _manifest()
    source = _csv_rows(qa.step13bu.SMOKE_PREVIEW_CSV)
    assert manifest13bu["stage"] == qa.PREVIOUS_STAGE
    assert manifest13bu["all_checks_passed"] is True
    assert manifest13bu["metadata_dataset_len"] == 20
    assert manifest13bu["ready_for_covapie_metadata_dataloader_smoke_qa_gate"] is True
    assert manifest13bu["ready_for_covapie_actual_dataloader_smoke"] is False
    assert manifest13bu["ready_for_training"] is False
    assert len(source) == 20
    assert len(source[0]) == 30
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == qa.STAGE
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["step13bu_metadata_dataloader_smoke_validated"] is True


def test_shim_api_qa_and_rechecked_dataset_behavior() -> None:
    rows = _csv_rows(ROOT / "covapie_metadata_dataset_shim_api_qa_audit.csv")
    manifest = _manifest()
    assert len(rows) == 8
    assert {row["shim_api_qa_passed"] for row in rows} == {"True"}
    by_item = {row["shim_api_item"]: row for row in rows}
    assert by_item["shim_class_exists"]["observed_status"] == "class importable"
    assert by_item["shim_len_returns_20"]["observed_status"] == "20"
    assert by_item["shim_getitem_returns_dict"]["observed_status"] == "dict"
    assert by_item["shim_out_of_range_raises_index_error"]["observed_status"] == "IndexError checked"
    assert by_item["shim_no_tensor_or_numpy_values"]["observed_status"] == "metadata only"
    dataset = qa.step13bu.CovapieMetadataDatasetSmoke(qa.step13br.INTERFACE_SMOKE_PREVIEW_CSV, qa.step13bo.SMOKE_PREVIEW_CSV)
    assert len(dataset) == 20
    assert isinstance(dataset[0], dict)
    assert isinstance(dataset[10], dict)
    assert isinstance(dataset[19], dict)
    try:
        dataset[20]
    except IndexError:
        pass
    else:
        raise AssertionError("out-of-range __getitem__ did not raise IndexError")
    assert manifest["metadata_dataset_len_rechecked"] == 20
    assert manifest["shim_api_qa_passed"] is True


def test_preview_integrity_qa_does_not_rewrite_step13bu_preview() -> None:
    rows = _csv_rows(ROOT / "covapie_metadata_dataloader_preview_integrity_qa_audit.csv")
    source = _csv_rows(qa.step13bu.SMOKE_PREVIEW_CSV)
    manifest = _manifest()
    assert len(rows) == 20
    assert [row["metadata_dataset_row_id"] for row in rows] == [row["metadata_dataset_row_id"] for row in source]
    for index, row in enumerate(rows):
        assert row["metadata_dataset_row_id"] == f"metadata_dataloader_smoke::{row['dataloader_interface_smoke_row_id']}"
        assert row["getitem_index"] == str(index)
        assert row["source_interface_preview_row_found"] == "True"
        assert row["metadata_dataset_row_id_deterministic"] == "True"
        assert row["csv_json_row_consistent"] == "True"
        assert row["row_order_preserved"] == "True"
        assert row["metadata_preview_rewritten_current_step"] == "False"
        assert row["contains_tensor_values"] == "False"
        assert row["ready_for_training"] == "False"
        assert row["preview_integrity_qa_passed"] == "True"
    assert manifest["preview_integrity_qa_row_count"] == 20
    assert manifest["preview_integrity_qa_passed"] is True
    assert manifest["metadata_dataloader_smoke_preview_written_current_step"] is False


def test_getitem_contract_mask_and_blocker_qa() -> None:
    getitem_rows = _csv_rows(ROOT / "covapie_metadata_getitem_contract_qa_audit.csv")
    mask_rows = _csv_rows(ROOT / "covapie_metadata_mask_distribution_qa_audit.csv")
    blocker_rows = _csv_rows(ROOT / "covapie_metadata_blocker_runtime_qa_audit.csv")
    manifest = _manifest()
    assert len(getitem_rows) == 12
    assert {row["observed_in_all_getitems"] for row in getitem_rows} == {"True"}
    assert {row["python_type_policy_satisfied"] for row in getitem_rows} == {"True"}
    assert {row["tensorization_status"] for row in getitem_rows} == {"not_tensorized_metadata_only"}
    assert {row["getitem_contract_qa_passed"] for row in getitem_rows} == {"True"}
    assert len(mask_rows) == 5
    assert [row["mask_task_name"] for row in mask_rows] == qa.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in mask_rows] == qa.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask_rows} == {"4"}
    assert {row["observed_unique_event_count"] for row in mask_rows} == {"4"}
    assert {row["mask_task_name_is_source_of_truth"] for row in mask_rows} == {"True"}
    assert {row["mask_task_alias_is_display_only"] for row in mask_rows} == {"True"}
    assert {row["mask_distribution_qa_passed"] for row in mask_rows} == {"True"}
    assert len(blocker_rows) == 12
    assert {row["preserved_in_all_getitems"] for row in blocker_rows} == {"True"}
    assert {row["blocker_runtime_qa_passed"] for row in blocker_rows} == {"True"}
    assert manifest["getitem_contract_qa_passed"] is True
    assert manifest["mask_distribution_qa_passed"] is True
    assert manifest["blocker_runtime_qa_passed"] is True
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_readiness_and_runtime_boundaries() -> None:
    readiness = _csv_rows(ROOT / "covapie_metadata_dataloader_readiness_qa_audit.csv")
    manifest = _manifest()
    assert len(readiness) == 8
    assert {row["readiness_qa_passed"] for row in readiness} == {"True"}
    for key in [
        "metadata_dataloader_smoke_preview_written_current_step",
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
    assert manifest["metadata_dataloader_smoke_written_previous_step"] is True
    assert manifest["ready_for_covapie_actual_dataloader_design_gate"] is True
    assert manifest["recommended_next_step"] == "covapie_actual_dataloader_design_gate"


def test_safety_git_and_no_forbidden_outputs() -> None:
    safety = _csv_rows(ROOT / "covapie_metadata_dataloader_smoke_qa_safety_audit.csv")
    git_safety = _csv_rows(ROOT / "covapie_metadata_dataloader_smoke_qa_git_safety.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_safety} == {"True"}
    forbidden_names = {
        "covapie_metadata_dataloader_smoke_preview.csv",
        "covapie_metadata_dataloader_smoke_preview.json",
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
    assert manifest["safety_audit_passed"] is True
    assert manifest["git_safety_passed"] is True


def test_no_forbidden_imports_or_existing_artifact_diffs() -> None:
    module_path = Path("src/covalent_ext/covapie_metadata_dataloader_smoke_qa_gate.py")
    script_path = Path("scripts/check_covapie_metadata_dataloader_smoke_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex", "numpy"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(qa.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(qa.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(qa.step13bd.METADATA_CSV.read_bytes()).hexdigest() == qa.METADATA_CSV_SHA256
    assert _git_diff_paths([qa.step13bu.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bt.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bs.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13br.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bq.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths([qa.step13bo.OUTPUT_ROOT.as_posix()]) == []
    assert _git_diff_paths(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"]) == []
    assert _git_diff_paths(["dataset.py", "data/prepare_crossdocked.py"]) == []
    assert _git_diff_paths(["equivariant_diffusion/", "lightning_modules.py"]) == []
