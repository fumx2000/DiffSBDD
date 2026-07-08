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

from covalent_ext import covapie_split_leakage_design_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_split_leakage_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_split_leakage_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13BJ check script before artifact tests"
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


def test_step13bi_precondition_and_readiness() -> None:
    manifest13bi = json.loads(gate.step13bi.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_split_leakage_design_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bi["stage"] == gate.PREVIOUS_STAGE
    assert manifest13bi["all_checks_passed"] is True
    assert manifest13bi["ready_for_covapie_split_leakage_design_gate"] is True
    assert manifest13bi["ready_for_covapie_final_dataset_design_gate"] is False
    assert manifest13bi["ready_for_covapie_dataloader_smoke"] is False
    assert manifest13bi["ready_for_training"] is False
    assert manifest13bi["ready_to_train_now"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13bi_sample_index_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_grouping_key_contract_has_required_keys_and_passes() -> None:
    rows = _csv_rows(ROOT / "covapie_split_grouping_key_contract.csv")
    manifest = _manifest()
    assert len(rows) == 13
    assert [row["grouping_key_name"] for row in rows] == [
        "extracted_event_id",
        "candidate_metadata_id",
        "pdb_id",
        "allowlist_entry_id",
        "ligand_het_code",
        "covalent_residue_site",
        "covalent_bond_atom_pair",
        "source_dataset_name",
        "scaffold_identity_future",
        "linker_identity_future",
        "warhead_type_future",
        "protein_sequence_cluster_future",
        "pocket_similarity_cluster_future",
    ]
    current_keys = {row["grouping_key_name"] for row in rows if row["available_in_current_sample_index"] == "True"}
    assert {"extracted_event_id", "candidate_metadata_id", "pdb_id", "allowlist_entry_id", "ligand_het_code", "covalent_residue_site", "covalent_bond_atom_pair"} <= current_keys
    assert {row["design_contract_passed"] for row in rows} == {"True"}
    assert manifest["split_grouping_key_contract_row_count"] == 13
    assert manifest["split_grouping_key_contract_passed"] is True


def test_leakage_rules_include_hard_constraints_and_no_row_level_split() -> None:
    rows = _csv_rows(ROOT / "covapie_split_leakage_rule_contract.csv")
    manifest = _manifest()
    by_id = {row["leakage_rule_id"]: row for row in rows}
    assert len(rows) == 15
    for rule_id in [
        "same_extracted_event_id_same_split",
        "same_candidate_metadata_id_same_split",
        "same_pdb_id_same_split",
        "same_allowlist_entry_id_same_split",
        "mask_task_rows_bound_to_parent_event",
        "no_random_row_level_split_allowed",
        "no_training_until_feature_semantics_audit",
        "no_training_until_leakage_split_gate",
    ]:
        assert by_id[rule_id]["enforcement_level"] == "hard_constraint"
        assert by_id[rule_id]["design_contract_passed"] == "True"
    for rule_id in [
        "same_ligand_het_code_flagged_for_review",
        "same_covalent_residue_site_flagged_for_review",
        "same_covalent_bond_atom_pair_flagged_for_review",
    ]:
        assert by_id[rule_id]["enforcement_level"] == "review_constraint"
    assert by_id["no_random_row_level_split_allowed"]["expected_current_status"] == "forbidden"
    assert {row["design_contract_passed"] for row in rows} == {"True"}
    assert manifest["leakage_rule_contract_row_count"] == 15
    assert manifest["leakage_rule_contract_passed"] is True


def test_leakage_risk_audit_current_counts_and_future_missing_groups() -> None:
    rows = _csv_rows(ROOT / "covapie_split_leakage_risk_design_audit.csv")
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
    for group in ["scaffold_future_missing", "warhead_type_future_missing", "sequence_cluster_future_missing", "pocket_cluster_future_missing"]:
        assert by_group[group]["current_smoke_status"] == "required_before_real_split"
    assert by_group["row_level_random_split_forbidden"]["current_smoke_status"] == "forbidden_by_design"
    assert {row["risk_design_audit_passed"] for row in rows} == {"True"}
    assert manifest["leakage_risk_design_audit_row_count"] == 12
    assert manifest["leakage_risk_design_audit_passed"] is True


def test_split_unit_design_preview_binds_five_mask_rows_to_parent_event() -> None:
    rows = _csv_rows(ROOT / "covapie_split_unit_design_preview.csv")
    manifest = _manifest()
    assert len(rows) == 4
    for row in rows:
        assert row["sample_rows_in_unit"] == "5"
        assert row["mask_task_count_in_unit"] == "5"
        assert row["mask_task_names_in_unit"].split(";") == gate.CANONICAL_MASK_TASK_NAMES
        assert row["split_assignment_current_step"] == "not_written_current_step"
        assert row["eligible_for_real_split_assignment"] == "False"
        assert "smoke_size_too_small" in row["blocker_reason"]
        assert "feature_semantics_audit_required" in row["blocker_reason"]
        assert "scaffold_linker_warhead_annotation_required" in row["blocker_reason"]
        assert row["split_unit_design_passed"] == "True"
    assert manifest["split_unit_design_preview_row_count"] == 4
    assert manifest["split_unit_design_preview_passed"] is True


def test_smoke_plan_blocks_final_dataset_dataloader_and_training() -> None:
    rows = _csv_rows(ROOT / "covapie_split_leakage_smoke_plan.csv")
    manifest = _manifest()
    by_step = {row["planned_step"]: row for row in rows}
    assert len(rows) == 11
    assert by_step["split_leakage_qa_gate"]["required_preconditions"] == "split_leakage_smoke_passed"
    assert "split_qa_and_feature_audit_required" in by_step["final_dataset_design_gate"]["required_preconditions"]
    assert by_step["dataloader_smoke"]["required_preconditions"] == "final_dataset_gate_required"
    assert "forward;loss;backward;optimizer;trainer.fit" in by_step["training"]["blocked_outputs"]
    assert {row["plan_passed"] for row in rows} == {"True"}
    assert manifest["split_leakage_smoke_plan_row_count"] == 11
    assert manifest["split_leakage_smoke_plan_passed"] is True


def test_boundary_git_safety_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_split_leakage_design_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_split_leakage_design_git_safety.csv")
    manifest = _manifest()
    assert boundary["split_leakage_design_gate"]["current_step_status"] == "executed_design_gate_only"
    assert boundary["read_step13bi_qa_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bh_sample_index"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["split_assignment_write"]["current_step_status"] == "blocked_current_design_gate"
    assert boundary["leakage_matrix_write"]["current_step_status"] == "blocked_current_design_gate"
    for item in ["final_dataset", "dataloader_smoke", "training"]:
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


def test_masks_safety_imports_raw_status_and_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_split_leakage_design_gate.py")
    script_path = Path("scripts/check_covapie_split_leakage_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(gate.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(gate.step13bi.step13bh.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    assert manifest["canonical_mask_task_names"] == gate.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    for key in [
        "split_assignments_written",
        "leakage_matrix_written",
        "final_dataset_written",
        "sample_index_written_current_step",
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
        "ready_for_covapie_split_leakage_qa_gate",
        "ready_for_covapie_feature_semantics_audit_gate",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_split_leakage_smoke"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_split_leakage_smoke"
