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

from covalent_ext import covapie_final_dataset_qa_gate as qa_gate


ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_final_dataset_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BP check script before artifact tests"
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


def test_step13bo_precondition_and_source_preview_shape() -> None:
    manifest13bo = json.loads(qa_gate.step13bo.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_final_dataset_qa_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bo["stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest13bo["all_checks_passed"] is True
    assert manifest13bo["ready_for_covapie_final_dataset_qa_gate"] is True
    assert manifest13bo["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bo["ready_for_training"] is False
    assert manifest13bo["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == qa_gate.STAGE
    assert manifest["previous_stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest["step13bo_final_dataset_smoke_validated"] is True
    assert manifest["source_preview_row_count"] == 20
    assert manifest["source_preview_column_count"] == 45
    assert manifest["source_preview_json_row_count"] == 20
    assert manifest["source_unique_event_count"] == 4
    assert manifest["source_unique_split_unit_count"] == 4
    assert manifest["source_canonical_mask_task_count"] == 5


def test_schema_order_and_csv_json_consistency_qa_passed() -> None:
    schema_rows = _csv_rows(ROOT / "covapie_final_dataset_schema_order_qa_audit.csv")
    consistency = _csv_rows(ROOT / "covapie_final_dataset_csv_json_consistency_qa_audit.csv")
    schema_fields = [row["final_dataset_field_name"] for row in _csv_rows(qa_gate.step13bn.SCHEMA_CONTRACT_CSV)]
    preview = _csv_rows(qa_gate.step13bo.SMOKE_PREVIEW_CSV)
    json_rows = json.loads(qa_gate.step13bo.SMOKE_PREVIEW_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(schema_rows) == 45
    assert [row["final_dataset_field_name"] for row in schema_rows] == schema_fields
    assert [row["observed_field_name"] for row in schema_rows] == schema_fields
    assert {row["source_schema_contract_found"] for row in schema_rows} == {"True"}
    assert {row["csv_field_order_matches"] for row in schema_rows} == {"True"}
    assert {row["json_field_order_matches"] for row in schema_rows} == {"True"}
    assert {row["no_missing_field"] for row in schema_rows} == {"True"}
    assert {row["no_extra_field"] for row in schema_rows} == {"True"}
    assert {row["schema_order_qa_passed"] for row in schema_rows} == {"True"}
    assert len(consistency) == 1
    assert consistency[0]["csv_row_count"] == "20"
    assert consistency[0]["csv_column_count"] == "45"
    assert consistency[0]["json_row_count"] == "20"
    assert consistency[0]["json_field_count"] == "45"
    assert consistency[0]["normalized_csv_json_identical"] == "True"
    assert consistency[0]["csv_json_consistency_qa_passed"] == "True"
    assert [{field: row[field] for field in schema_fields} for row in json_rows] == preview
    assert manifest["schema_order_qa_row_count"] == 45
    assert manifest["schema_order_qa_passed"] is True
    assert manifest["csv_json_consistency_qa_row_count"] == 1
    assert manifest["csv_json_consistency_qa_passed"] is True


def test_row_lineage_qa_maps_each_event_to_one_split_unit() -> None:
    lineage = _csv_rows(ROOT / "covapie_final_dataset_row_lineage_qa_audit.csv")
    manifest = _manifest()
    assert len(lineage) == 20
    for row in lineage:
        assert row["final_dataset_row_id"] == f"final_dataset_smoke::{row['sample_id']}"
        assert row["source_sample_index_row_found"] == "True"
        assert row["source_split_unit_found"] == "True"
        assert row["parent_event_group_bound_to_one_split_unit"] == "True"
        assert row["sample_id_matches_source"] == "True"
        assert row["split_unit_matches_step13bk"] == "True"
        assert row["final_dataset_smoke_row_materialized_previous_step"] == "True"
        assert row["final_dataset_smoke_preview_rewritten_current_step"] == "False"
        assert row["real_final_dataset_materialized"] == "False"
        assert row["dataloader_ready"] == "False"
        assert row["ready_for_training"] == "False"
        assert row["row_lineage_qa_passed"] == "True"
    by_event: dict[str, set[str]] = {}
    by_sample: dict[str, set[str]] = {}
    for row in lineage:
        by_event.setdefault(row["extracted_event_id"], set()).add(row["split_unit_id"])
        by_sample.setdefault(row["sample_id"], set()).add(row["split_unit_id"])
    assert len(by_event) == 4
    assert all(len(split_units) == 1 for split_units in by_event.values())
    assert all(len(split_units) == 1 for split_units in by_sample.values())
    assert manifest["row_lineage_qa_row_count"] == 20
    assert manifest["row_lineage_qa_passed"] is True


def test_mask_distribution_feature_blockers_and_readiness() -> None:
    mask_rows = _csv_rows(ROOT / "covapie_final_dataset_mask_distribution_qa_audit.csv")
    blockers = _csv_rows(ROOT / "covapie_final_dataset_feature_blocker_qa_audit.csv")
    readiness = _csv_rows(ROOT / "covapie_final_dataset_readiness_qa_audit.csv")
    manifest = _manifest()
    assert len(mask_rows) == 5
    assert [row["mask_task_name"] for row in mask_rows] == qa_gate.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in mask_rows] == qa_gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask_rows} == {"4"}
    assert {row["observed_unique_event_count"] for row in mask_rows} == {"4"}
    assert {row["observed_unique_split_unit_count"] for row in mask_rows} == {"4"}
    assert {row["mask_distribution_qa_passed"] for row in mask_rows} == {"True"}
    assert [row for row in mask_rows if row["mask_task_name"] == "scaffold_only"][0]["mask_task_alias"] == "B3"
    assert len(blockers) == 13
    assert {row["blocker_preserved_in_all_rows"] for row in blockers} == {"True"}
    assert {row["required_before_training"] for row in blockers} == {"True"}
    assert {row["blocker_qa_passed"] for row in blockers} == {"True"}
    assert len(readiness) == 10
    assert {row["readiness_qa_passed"] for row in readiness} == {"True"}
    assert manifest["mask_distribution_qa_row_count"] == 5
    assert manifest["mask_distribution_qa_passed"] is True
    assert manifest["feature_blocker_qa_row_count"] == 13
    assert manifest["feature_blocker_qa_passed"] is True
    assert manifest["readiness_qa_row_count"] == 10
    assert manifest["readiness_qa_passed"] is True
    assert manifest["canonical_mask_task_names"] == qa_gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == qa_gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_boundaries_no_real_outputs_no_preview_rewrite_and_next_step() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_final_dataset_qa_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_final_dataset_qa_git_safety.csv")
    manifest = _manifest()
    assert boundary["final_dataset_qa_gate"]["current_step_status"] == "executed_qa_gate_only"
    assert boundary["read_step13bo_smoke_preview"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["final_dataset_smoke_preview_write_current_step"]["current_step_status"] == "not_executed_current_step_already_completed_previous_step"
    for item in ["real_final_dataset_write", "generic_final_dataset_smoke_write", "new_sample_index_write", "split_assignment_write", "leakage_matrix_write", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "raw_cif_mmcif_sdf_pdb_gzip_read", "mmcif_parse", "atom_site_scan", "struct_conn_scan", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    forbidden_names = {"final_dataset.csv", "final_dataset.json", "final_dataset_smoke.csv", "final_dataset_smoke.json", "covapie_final_dataset_smoke_preview.csv", "covapie_final_dataset_smoke_preview.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "dataloader_smoke.csv", "dataloader_smoke.json", "training_report.csv", "training_report.json"}
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    for key in [
        "final_dataset_smoke_preview_written_current_step",
        "real_final_dataset_written",
        "generic_final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["final_dataset_smoke_preview_written_previous_step"] is True
    assert manifest["ready_for_covapie_dataloader_interface_design_gate"] is True
    assert manifest["recommended_next_step"] == "covapie_dataloader_interface_design_gate"
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_no_raw_network_torch_training_imports_and_source_artifacts_unchanged() -> None:
    module_path = Path("src/covalent_ext/covapie_final_dataset_qa_gate.py")
    script_path = Path("scripts/check_covapie_final_dataset_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(qa_gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(qa_gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(qa_gate.step13bd.METADATA_CSV.read_bytes()).hexdigest() == qa_gate.METADATA_CSV_SHA256
    assert _git_diff_paths(
        [
            "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
            qa_gate.step13bo.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bn.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bm.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bl.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bk.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bj.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bi.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bh.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bg.OUTPUT_ROOT.as_posix(),
            qa_gate.step13bf.OUTPUT_ROOT.as_posix(),
            qa_gate.step13be.OUTPUT_ROOT.as_posix(),
            "data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0",
            "equivariant_diffusion/",
            "lightning_modules.py",
            "dataset.py",
            "data/prepare_crossdocked.py",
        ]
    ) == []
    manifest = _manifest()
    for key in [
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
    ]:
        assert manifest[key] is False, key
    assert manifest["all_checks_passed"] is True
