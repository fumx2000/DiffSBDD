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

from covalent_ext import covapie_split_leakage_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_split_leakage_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_split_leakage_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BK check script before artifact tests"
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


def test_step13bj_precondition_and_readiness() -> None:
    manifest13bj = json.loads(smoke.step13bj.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_split_leakage_smoke_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bj["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13bj["all_checks_passed"] is True
    assert manifest13bj["ready_for_covapie_split_leakage_smoke"] is True
    assert manifest13bj["ready_for_covapie_split_leakage_qa_gate"] is False
    assert manifest13bj["ready_for_covapie_final_dataset_design_gate"] is False
    assert manifest13bj["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bj["ready_for_training"] is False
    assert manifest13bj["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13bj_split_leakage_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_split_unit_smoke_preview_csv_json_has_four_units_no_real_assignments() -> None:
    csv_rows = _csv_rows(ROOT / "covapie_split_unit_smoke_preview.csv")
    json_rows = json.loads((ROOT / "covapie_split_unit_smoke_preview.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(csv_rows) == 4
    assert len(json_rows) == 4
    assert manifest["split_unit_smoke_preview_csv_written"] is True
    assert manifest["split_unit_smoke_preview_json_written"] is True
    for row in csv_rows:
        assert row["split_unit_id"].startswith("COVAPIE_SPLIT_UNIT_SMOKE_")
        assert row["sample_rows_in_unit"] == "5"
        assert row["mask_task_count_in_unit"] == "5"
        assert row["mask_task_names_in_unit"].split(";") == smoke.CANONICAL_MASK_TASK_NAMES
        assert len(row["sample_ids_in_unit"].split(";")) == 5
        assert row["split_assignment_current_step"] == "not_written_current_step"
        assert row["real_split_assignment_written"] == "False"
        assert row["eligible_for_training_split"] == "False"
        assert "smoke_size_too_small" in row["blocker_reason"]
        assert "feature_semantics_audit_required" in row["blocker_reason"]
        assert "scaffold_linker_warhead_annotation_required" in row["blocker_reason"]
        assert "split_leakage_smoke_only_current_step" in row["blocker_reason"]
        assert row["split_unit_smoke_passed"] == "True"
    assert manifest["split_unit_smoke_preview_row_count"] == 4
    assert manifest["split_unit_smoke_preview_passed"] is True


def test_parent_event_and_candidate_integrity_bind_rows_to_one_unit() -> None:
    parent = _csv_rows(ROOT / "covapie_parent_event_group_integrity_audit.csv")
    candidate = _csv_rows(ROOT / "covapie_candidate_metadata_group_integrity_audit.csv")
    manifest = _manifest()
    assert len(parent) == 4
    assert len(candidate) == 4
    for row in parent:
        assert row["sample_rows_for_event"] == "5"
        assert row["unique_split_unit_count"] == "1"
        assert row["mask_task_count"] == "5"
        assert row["mask_task_names"].split(";") == smoke.CANONICAL_MASK_TASK_NAMES
        assert row["all_mask_rows_bound_to_parent_event"] == "True"
        assert row["no_row_level_split_assignment"] == "True"
        assert row["group_integrity_passed"] == "True"
    for row in candidate:
        assert row["extracted_event_count"] == "1"
        assert row["sample_rows_for_candidate"] == "5"
        assert row["unique_split_unit_count"] == "1"
        assert row["all_candidate_rows_bound_to_one_unit"] == "True"
        assert row["no_candidate_level_leakage_in_smoke"] == "True"
        assert row["candidate_group_integrity_passed"] == "True"
    assert manifest["parent_event_group_integrity_row_count"] == 4
    assert manifest["candidate_metadata_group_integrity_row_count"] == 4
    assert manifest["parent_event_group_integrity_passed"] is True
    assert manifest["candidate_metadata_group_integrity_passed"] is True


def test_mask_task_grouping_preserves_five_masks_and_b3() -> None:
    rows = _csv_rows(ROOT / "covapie_mask_task_grouping_integrity_audit.csv")
    manifest = _manifest()
    assert len(rows) == 5
    assert [row["mask_task_name"] for row in rows] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in rows] == smoke.CANONICAL_MASK_TASK_ALIASES
    for row in rows:
        assert row["observed_row_count"] == "4"
        assert row["observed_unique_event_count"] == "4"
        assert row["expected_row_count"] == "4"
        assert row["expected_unique_event_count"] == "4"
        assert row["mask_rows_distributed_across_all_events"] == "True"
        assert row["no_extra_mask_tasks"] == "True"
        assert row["mask_grouping_integrity_passed"] == "True"
    b3 = [row for row in rows if row["mask_task_name"] == "scaffold_only"][0]
    assert b3["mask_task_alias"] == "B3"
    assert b3["b3_scaffold_only_included_when_applicable"] == "True"
    assert manifest["mask_task_grouping_integrity_row_count"] == 5
    assert manifest["mask_task_grouping_integrity_passed"] is True
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_risk_smoke_audit_blocks_row_level_and_real_train_val_test_split() -> None:
    rows = _csv_rows(ROOT / "covapie_split_leakage_risk_smoke_audit.csv")
    manifest = _manifest()
    by_group = {row["risk_group"]: row for row in rows}
    assert len(rows) == 12
    assert by_group["parent_event_grouping"]["observed_group_count"] == "4"
    assert by_group["parent_event_grouping"]["observed_max_rows_per_group"] == "5"
    assert by_group["candidate_metadata_grouping"]["observed_group_count"] == "4"
    assert by_group["candidate_metadata_grouping"]["observed_max_rows_per_group"] == "5"
    assert by_group["pdb_grouping"]["observed_group_count"] == "4"
    assert by_group["pdb_grouping"]["observed_max_rows_per_group"] == "5"
    assert by_group["mask_task_grouping"]["observed_group_count"] == "5"
    assert by_group["mask_task_grouping"]["observed_max_rows_per_group"] == "4"
    assert by_group["row_level_random_split_forbidden"]["smoke_status"] == "forbidden_by_design"
    assert by_group["scaffold_identity_missing"]["smoke_status"] == "required_before_real_split"
    assert by_group["warhead_type_missing"]["smoke_status"] == "required_before_real_split"
    assert by_group["feature_semantics_audit_required"]["smoke_status"] == "required_before_training"
    assert by_group["smoke_size_too_small_for_real_train_val_test"]["smoke_status"] == "blocks_real_split_assignment"
    assert {row["risk_smoke_audit_passed"] for row in rows} == {"True"}
    assert manifest["split_leakage_risk_smoke_audit_row_count"] == 12
    assert manifest["split_leakage_risk_smoke_audit_passed"] is True


def test_boundary_git_safety_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_split_leakage_smoke_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_split_leakage_smoke_git_safety.csv")
    manifest = _manifest()
    assert boundary["split_leakage_smoke"]["current_step_status"] == "executed_smoke_only"
    assert boundary["read_step13bj_design_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bi_qa_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bh_sample_index"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["split_unit_smoke_preview_write"]["current_step_status"] == "executed_smoke_only"
    for item in ["split_assignment_write", "leakage_matrix_write", "final_dataset", "new_sample_index", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "mmcif_parse", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True
    forbidden_names = {
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
    }
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []


def test_no_raw_network_model_imports_and_next_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_split_leakage_smoke.py")
    script_path = Path("scripts/check_covapie_split_leakage_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(smoke.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(smoke.step13bj.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in [
        "split_assignments_written",
        "leakage_matrix_written",
        "final_dataset_written",
        "sample_index_written_current_step",
        "real_train_val_test_split_written",
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_text_read",
        "mmcif_parse_current_step",
        "atom_site_scan_current_step",
        "struct_conn_scan_current_step",
        "coordinate_extraction_current_step",
        "network_access_used",
        "urllib_used",
        "requests_used",
        "browser_used",
        "raw_structure_downloaded",
        "raw_ligand_downloaded",
        "archive_downloaded",
        "raw_file_created",
        "sdf_read",
        "pdb_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "ready_for_covapie_feature_semantics_audit_gate",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["split_unit_preview_written_current_step"] is True
    assert manifest["ready_for_covapie_split_leakage_qa_gate"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_split_leakage_qa_gate"
