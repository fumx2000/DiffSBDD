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

from covalent_ext import covapie_feature_semantics_audit_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_feature_semantics_audit_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BM check script before artifact tests"
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


def test_step13bl_precondition_and_readiness_boundary() -> None:
    manifest13bl = json.loads(gate.step13bl.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_feature_semantics_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bl["stage"] == gate.PREVIOUS_STAGE
    assert manifest13bl["all_checks_passed"] is True
    assert manifest13bl["ready_for_covapie_feature_semantics_audit_gate"] is True
    assert manifest13bl["ready_for_covapie_final_dataset_design_gate"] is False
    assert manifest13bl["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bl["ready_for_training"] is False
    assert manifest13bl["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13bl_split_leakage_qa_gate_validated"] is True
    assert manifest["source_sample_index_row_count"] == 20
    assert manifest["source_unique_event_count"] == 4
    assert manifest["source_extracted_event_table_row_count"] == 4
    assert manifest["source_protein_atom_table_row_count"] == 1071
    assert manifest["source_ligand_atom_table_row_count"] == 149
    assert manifest["source_canonical_mask_task_count"] == 5
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_source_inventory_is_derived_or_static_read_only() -> None:
    rows = _csv_rows(ROOT / "covapie_feature_source_inventory_audit.csv")
    manifest = _manifest()
    assert len(rows) == 10
    assert [row["feature_source_name"] for row in rows] == [
        "step13bh_sample_index_smoke_csv",
        "step13be_extracted_event_table",
        "step13be_protein_atom_table",
        "step13be_ligand_atom_table",
        "step13bl_split_leakage_qa_manifest",
        "src_covalent_ext_feature_related_modules",
        "dataset_py_static_source",
        "prepare_crossdocked_static_source",
        "lightning_modules_static_source",
        "equivariant_diffusion_static_source",
    ]
    assert {row["raw_data_or_runtime_dependency_used"] for row in rows} == {"False"}
    assert {row["source_inventory_passed"] for row in rows} == {"True"}
    assert {row["current_step_access_status"] for row in rows} == {"derived_csv_json_read_only", "static_text_read_only"}
    assert manifest["feature_source_inventory_audit_row_count"] == 10
    assert manifest["feature_source_inventory_audit_passed"] is True


def test_feature_semantics_contract_has_31_rows_and_training_stays_unknown() -> None:
    rows = _csv_rows(ROOT / "covapie_feature_semantics_contract.csv")
    manifest = _manifest()
    by_name = {row["feature_name"]: row for row in rows}
    assert len(rows) == 31
    assert by_name["mask_task_name"]["expected_current_value_or_policy"].split(";") == gate.CANONICAL_MASK_TASK_NAMES
    assert by_name["mask_task_alias"]["expected_current_value_or_policy"].split(";") == gate.CANONICAL_MASK_TASK_ALIASES
    assert by_name["conditioning_mode"]["current_semantics_status"] == "protein_covalent_residue_conditioned"
    assert by_name["covalent_residue_conditioned"]["current_semantics_status"] == "true_for_current_samples"
    assert by_name["scaffold_linker_warhead_annotation_status"]["current_semantics_status"] == "required_before_training_not_materialized"
    assert by_name["warhead_type_label_status"]["current_semantics_status"] == "required_before_training_not_materialized"
    assert by_name["ligand_residue_atom_pair_label_status"]["current_semantics_status"] == "present_from_extraction_qa_feature_audit_required"
    assert by_name["pre_post_geometry_label_status"]["current_semantics_status"] == "post_covalent_geometry_present_feature_audit_required"
    assert by_name["unknown_atom_feature_policy"]["current_semantics_status"] == "not_finalized_for_training_current_step"
    assert by_name["feature_semantics_known_for_training"]["current_semantics_status"] == "false"
    assert {row["blocker_before_training"] for row in rows} == {"True"}
    assert {row["feature_semantics_contract_passed"] for row in rows} == {"True"}
    assert manifest["feature_semantics_contract_row_count"] == 31
    assert manifest["feature_semantics_contract_passed"] is True
    assert manifest["feature_semantics_audit_completed_current_step"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["step12d_was_smoke_legality_only"] is True


def test_coordinate_geometry_semantics_are_angstrom_and_post_covalent_only() -> None:
    rows = _csv_rows(ROOT / "covapie_coordinate_geometry_semantics_audit.csv")
    manifest = _manifest()
    by_name = {row["geometry_feature_name"]: row for row in rows}
    assert len(rows) == 10
    assert by_name["covalent_bond_distance_angstrom"]["coordinate_unit_or_policy"] == "angstrom"
    assert by_name["protein_atom_xyz_coordinates"]["observed_count_or_range"] == "1071"
    assert by_name["ligand_atom_xyz_coordinates"]["observed_count_or_range"] == "149"
    assert by_name["post_covalent_geometry_status"]["current_semantics_status"] == "post_covalent_geometry_present"
    assert by_name["pre_covalent_geometry_status"]["current_semantics_status"] == "pre_covalent_geometry_not_materialized_current_step"
    assert by_name["geometry_training_readiness"]["training_readiness_status"] == "false"
    assert {row["geometry_semantics_audit_passed"] for row in rows} == {"True"}
    assert manifest["coordinate_geometry_semantics_audit_row_count"] == 10
    assert manifest["coordinate_geometry_semantics_audit_passed"] is True


def test_mask_conditioning_preserves_five_masks_and_b3() -> None:
    rows = _csv_rows(ROOT / "covapie_mask_conditioning_semantics_audit.csv")
    manifest = _manifest()
    mask_rows = [row for row in rows if row["semantics_item"].startswith("mask_task::")]
    assert len(rows) == 8
    assert [row["long_name"] for row in mask_rows] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["alias"] for row in mask_rows] == gate.CANONICAL_MASK_TASK_ALIASES
    assert {row["observed_row_count"] for row in mask_rows} == {"4"}
    assert {row["expected_row_count"] for row in mask_rows} == {"4"}
    assert [row for row in mask_rows if row["long_name"] == "scaffold_only"][0]["alias"] == "B3"
    assert {row["mask_conditioning_semantics_passed"] for row in rows} == {"True"}
    assert manifest["mask_conditioning_semantics_audit_row_count"] == 8
    assert manifest["mask_conditioning_semantics_audit_passed"] is True
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_auxiliary_labels_and_training_blockers_remain_explicit() -> None:
    aux = _csv_rows(ROOT / "covapie_auxiliary_label_semantics_audit.csv")
    blockers = _csv_rows(ROOT / "covapie_feature_semantics_training_blockers.csv")
    manifest = _manifest()
    assert len(aux) == 10
    assert len(blockers) == 13
    by_aux = {row["auxiliary_label_name"]: row for row in aux}
    assert by_aux["scaffold_linker_warhead_annotation"]["current_status"] == "required_before_training_not_materialized"
    assert by_aux["warhead_type_label"]["current_status"] == "required_before_training_not_materialized"
    assert by_aux["ligand_residue_atom_pair_label"]["required_before_training"] == "True"
    assert by_aux["pre_post_geometry_label"]["required_before_training"] == "True"
    assert {row["auxiliary_label_semantics_passed"] for row in aux} == {"True"}
    assert [row["blocker_item"] for row in blockers] == [
        "feature_semantics_known_for_training_false",
        "unknown_atom_feature_policy_not_finalized",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "ligand_residue_atom_pair_label_audit_required",
        "pre_post_geometry_label_audit_required",
        "pre_covalent_geometry_not_materialized",
        "final_dataset_not_written",
        "dataloader_smoke_not_run",
        "no_training_current_step",
        "ready_for_training_false",
        "step12d_smoke_not_final_feature_semantics_audit",
        "leakage_split_qa_completed_but_training_still_blocked",
    ]
    assert {row["required_before_training"] for row in blockers} == {"True"}
    assert {row["blocker_preserved"] for row in blockers} == {"True"}
    assert {row["training_blocker_passed"] for row in blockers} == {"True"}
    assert manifest["auxiliary_label_semantics_audit_row_count"] == 10
    assert manifest["feature_semantics_training_blocker_row_count"] == 13
    assert manifest["auxiliary_label_semantics_audit_passed"] is True
    assert manifest["feature_semantics_training_blockers_passed"] is True


def test_boundary_git_safety_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_feature_semantics_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_feature_semantics_git_safety.csv")
    manifest = _manifest()
    assert boundary["feature_semantics_audit_gate"]["current_step_status"] == "executed_audit_gate_only"
    assert boundary["read_step13bl_qa_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bk_smoke_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bh_sample_index"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["static_source_text_read"]["current_step_status"] == "executed_static_text_read_only"
    for item in ["final_dataset", "new_sample_index", "split_assignments", "leakage_matrix", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in [
        "raw_file_content_read",
        "raw_cif_mmcif_sdf_pdb_gzip_read",
        "mmcif_parse",
        "atom_site_scan",
        "struct_conn_scan",
        "coordinate_extraction",
        "network_access",
        "raw_download",
        "rdkit_biopdb_gemmi",
        "torch_model_training",
    ]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []
    forbidden_names = {"final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json"}
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True


def test_no_raw_network_torch_training_imports_and_next_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_feature_semantics_audit_gate.py")
    script_path = Path("scripts/check_covapie_feature_semantics_audit_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(gate.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    assert hashlib.sha256(gate.step13bd.METADATA_CSV.read_bytes()).hexdigest() == gate.METADATA_CSV_SHA256
    manifest = _manifest()
    for key in [
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
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
        "ready_for_covapie_final_dataset_smoke",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_final_dataset_design_gate"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_final_dataset_design_gate"
