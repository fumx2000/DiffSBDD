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

from covalent_ext import covapie_final_dataset_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_final_dataset_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_final_dataset_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BO check script before artifact tests"
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


def test_step13bn_precondition_and_readiness() -> None:
    manifest13bn = json.loads(smoke.step13bn.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_final_dataset_smoke_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bn["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13bn["all_checks_passed"] is True
    assert manifest13bn["ready_for_covapie_final_dataset_smoke"] is True
    assert manifest13bn["ready_for_covapie_final_dataset_qa_gate"] is False
    assert manifest13bn["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bn["ready_for_training"] is False
    assert manifest13bn["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13bn_final_dataset_design_gate_validated"] is True
    assert manifest["source_sample_index_row_count"] == 20
    assert manifest["source_unique_event_count"] == 4
    assert manifest["source_canonical_mask_task_count"] == 5
    assert manifest["source_split_unit_preview_row_count"] == 4


def test_smoke_preview_csv_json_schema_order_and_consistency() -> None:
    csv_rows = _csv_rows(ROOT / "covapie_final_dataset_smoke_preview.csv")
    json_rows = json.loads((ROOT / "covapie_final_dataset_smoke_preview.json").read_text(encoding="utf-8"))
    schema_fields = [row["final_dataset_field_name"] for row in _csv_rows(smoke.step13bn.SCHEMA_CONTRACT_CSV)]
    schema_audit = _csv_rows(ROOT / "covapie_final_dataset_schema_order_smoke_audit.csv")
    manifest = _manifest()
    assert len(csv_rows) == 20
    assert len(json_rows) == 20
    assert len(csv_rows[0]) == 45
    assert list(csv_rows[0].keys()) == schema_fields
    assert json_rows == csv_rows
    assert len(schema_audit) == 1
    assert schema_audit[0]["schema_field_count"] == "45"
    assert schema_audit[0]["schema_order_matches_contract"] == "True"
    assert schema_audit[0]["csv_json_consistent"] == "True"
    assert schema_audit[0]["schema_order_smoke_passed"] == "True"
    assert manifest["final_dataset_smoke_preview_csv_written"] is True
    assert manifest["final_dataset_smoke_preview_json_written"] is True
    assert manifest["final_dataset_smoke_preview_row_count"] == 20
    assert manifest["final_dataset_smoke_preview_column_count"] == 45
    assert manifest["final_dataset_smoke_preview_json_row_count"] == 20
    assert manifest["schema_order_smoke_audit_passed"] is True


def test_row_lineage_smoke_maps_samples_to_one_split_unit() -> None:
    preview = _csv_rows(ROOT / "covapie_final_dataset_smoke_preview.csv")
    lineage = _csv_rows(ROOT / "covapie_final_dataset_row_lineage_smoke_audit.csv")
    manifest = _manifest()
    assert len(lineage) == 20
    for row in preview:
        assert row["final_dataset_row_id"] == f"final_dataset_smoke::{row['sample_id']}"
        assert row["final_dataset_materialized_current_step"] == "True"
        assert row["dataloader_ready"] == "False"
        assert row["ready_for_training"] == "False"
    for row in lineage:
        assert row["final_dataset_row_id"] == f"final_dataset_smoke::{row['sample_id']}"
        assert row["source_sample_index_row_found"] == "True"
        assert row["source_split_unit_found"] == "True"
        assert row["parent_event_group_bound_to_one_split_unit"] == "True"
        assert row["final_dataset_smoke_row_materialized"] == "True"
        assert row["final_dataset_real_row_materialized"] == "False"
        assert row["dataloader_ready"] == "False"
        assert row["ready_for_training"] == "False"
        assert row["row_lineage_smoke_passed"] == "True"
    by_event: dict[str, set[str]] = {}
    by_split: dict[str, int] = {}
    for row in preview:
        by_event.setdefault(row["extracted_event_id"], set()).add(row["split_unit_id"])
        by_split[row["split_unit_id"]] = by_split.get(row["split_unit_id"], 0) + 1
    assert len(by_event) == 4
    assert all(len(split_units) == 1 for split_units in by_event.values())
    assert set(by_split.values()) == {5}
    assert manifest["row_lineage_smoke_audit_row_count"] == 20
    assert manifest["row_lineage_smoke_audit_passed"] is True


def test_mask_distribution_preserves_five_canonical_masks_and_b3() -> None:
    preview = _csv_rows(ROOT / "covapie_final_dataset_smoke_preview.csv")
    mask_rows = _csv_rows(ROOT / "covapie_final_dataset_mask_distribution_smoke_audit.csv")
    manifest = _manifest()
    assert len(mask_rows) == 5
    assert [row["mask_task_name"] for row in mask_rows] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["mask_task_alias"] for row in mask_rows] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask_rows} == {"4"}
    assert {row["observed_unique_event_count"] for row in mask_rows} == {"4"}
    assert {row["observed_unique_split_unit_count"] for row in mask_rows} == {"4"}
    assert {row["mask_distribution_smoke_passed"] for row in mask_rows} == {"True"}
    assert [row for row in mask_rows if row["mask_task_name"] == "scaffold_only"][0]["mask_task_alias"] == "B3"
    assert sorted({row["mask_task_name"] for row in preview}) == sorted(smoke.CANONICAL_MASK_TASK_NAMES)
    assert manifest["mask_distribution_smoke_audit_row_count"] == 5
    assert manifest["mask_distribution_smoke_audit_passed"] is True
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_feature_blockers_are_preserved_in_all_preview_rows() -> None:
    preview = _csv_rows(ROOT / "covapie_final_dataset_smoke_preview.csv")
    blockers = _csv_rows(ROOT / "covapie_final_dataset_feature_blocker_smoke_audit.csv")
    manifest = _manifest()
    assert len(blockers) == 13
    assert [row["blocker_item"] for row in blockers] == [
        "feature_semantics_known_for_training_false",
        "unknown_atom_feature_policy_not_finalized",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "ligand_residue_atom_pair_label_audit_required",
        "pre_post_geometry_label_audit_required",
        "pre_covalent_geometry_not_materialized",
        "final_dataset_smoke_preview_only",
        "no_real_final_dataset_written",
        "no_dataloader_smoke",
        "no_training_current_step",
        "ready_for_training_false",
        "step12d_smoke_not_final_feature_semantics_audit",
    ]
    assert {row["blocker_smoke_passed"] for row in blockers} == {"True"}
    assert all(row["feature_semantics_known_for_training"] == "False" for row in preview)
    assert all(row["unknown_atom_feature_policy_finalized_for_training"] == "False" for row in preview)
    assert all(row["dataloader_ready"] == "False" for row in preview)
    assert all(row["ready_for_training"] == "False" for row in preview)
    assert all(row["split_assignment_status"] == "not_written_current_step" for row in preview)
    assert all(row["coordinate_unit"] == "angstrom" for row in preview)
    assert all(row["pre_covalent_geometry_status"] == "pre_covalent_geometry_not_materialized_current_step" for row in preview)
    assert all(row["post_covalent_geometry_status"] == "post_covalent_geometry_present" for row in preview)
    assert all(row["feature_semantics_audit_status"] == "feature_semantics_audit_completed_current_step" for row in preview)
    assert all(row["leakage_split_qa_status"] == "split_leakage_qa_passed" for row in preview)
    required_summary_terms = {
        "feature_semantics_known_for_training_false",
        "unknown_atom_feature_policy_not_finalized",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "pre_covalent_geometry_not_materialized",
        "ready_for_training_false",
    }
    for row in preview:
        assert required_summary_terms <= set(row["training_blocker_summary"].split(";"))
    assert manifest["feature_blocker_smoke_audit_row_count"] == 13
    assert manifest["feature_blocker_smoke_audit_passed"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False


def test_boundary_git_safety_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_final_dataset_smoke_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_final_dataset_smoke_git_safety.csv")
    manifest = _manifest()
    assert boundary["final_dataset_smoke"]["current_step_status"] == "executed_smoke_preview_only"
    assert boundary["final_dataset_smoke_preview_write"]["current_step_status"] == "executed_smoke_preview_only"
    for item in ["read_step13bn_design_artifacts", "read_step13bm_feature_semantics_artifacts", "read_step13bk_split_unit_preview", "read_step13bh_sample_index", "read_step13be_extracted_tables"]:
        assert boundary[item]["current_step_status"] == "executed_derived_csv_json_read_only"
    for item in ["real_final_dataset_write", "new_sample_index_write", "split_assignment_write", "leakage_matrix_write", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "raw_cif_mmcif_sdf_pdb_gzip_read", "mmcif_parse", "atom_site_scan", "struct_conn_scan", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    allowed = {"covapie_final_dataset_smoke_preview.csv", "covapie_final_dataset_smoke_preview.json"}
    forbidden_names = {"final_dataset.csv", "final_dataset.json", "final_dataset_smoke.csv", "final_dataset_smoke.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "dataloader_smoke.csv", "dataloader_smoke.json", "training_report.csv", "training_report.json"}
    assert not any(path.name in forbidden_names and path.name not in allowed for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True


def test_no_raw_network_torch_training_imports_and_next_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_final_dataset_smoke.py")
    script_path = Path("scripts/check_covapie_final_dataset_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(smoke.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(smoke.step13bd.METADATA_CSV.read_bytes()).hexdigest() == smoke.METADATA_CSV_SHA256
    manifest = _manifest()
    for key in [
        "real_final_dataset_written",
        "generic_final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "real_train_val_test_split_written",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
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
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["final_dataset_smoke_preview_written_current_step"] is True
    assert manifest["ready_for_covapie_final_dataset_qa_gate"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_final_dataset_qa_gate"
