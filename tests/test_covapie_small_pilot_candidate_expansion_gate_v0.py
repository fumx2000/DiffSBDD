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

from covalent_ext import covapie_small_pilot_candidate_expansion_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_small_pilot_candidate_expansion_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_small_pilot_candidate_expansion_gate_manifest.json"
    assert path.is_file(), "Run the Step 14D check script before artifact tests"
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


def test_step14c_precondition_source_profile_and_gap_reason() -> None:
    manifest14c = json.loads(gate.STEP14C_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_small_pilot_candidate_expansion_precondition_audit.csv")
    manifest = _manifest()
    assert manifest14c["stage"] == gate.PREVIOUS_STAGE
    assert manifest14c["step_label"] == "Step 14C"
    assert manifest14c["all_checks_passed"] is True
    assert manifest14c["current_source_profile"] == gate.CURRENT_SOURCE_PROFILE
    assert manifest14c["current_source_database"] == gate.CURRENT_SOURCE_DATABASE
    assert manifest14c["current_execution_source_specific"] is True
    assert manifest14c["cross_source_generalization_supported_by_schema"] is True
    assert manifest14c["pdb_wide_blind_scan_allowed"] is False
    assert manifest14c["selected_small_pilot_row_count"] == 0
    assert manifest14c["insufficient_candidate_count_for_20_to_50_pilot"] is True
    assert manifest14c["ready_for_covapie_small_pilot_download_smoke"] is False
    assert manifest14c["recommended_next_step"] == "covapie_small_pilot_candidate_expansion_gate"
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["current_source_profile"] == gate.CURRENT_SOURCE_PROFILE
    assert manifest["current_source_database"] == gate.CURRENT_SOURCE_DATABASE
    assert manifest["current_execution_source_specific"] is True
    assert manifest["cross_source_generalization_supported_by_schema"] is True
    assert manifest["pdb_wide_blind_scan_allowed"] is False


def test_evidence_inventory_required_sources_optional_missing_ok_and_mapping_contract() -> None:
    inventory = _csv_rows(ROOT / "covapie_small_pilot_candidate_evidence_source_inventory.csv")
    mapping = _csv_rows(ROOT / "covapie_small_pilot_event_identity_mapping_contract.csv")
    manifest = _manifest()
    names = [row["evidence_source_name"] for row in inventory]
    for required in [
        "current_metadata_csv",
        "step14c_candidate_selection_audit",
        "step14c_empty_small_pilot_manifest",
        "candidate_allowlist_qa_if_present",
        "batch_raw_read_extraction_smoke_if_present",
        "batch_raw_read_extraction_qa_if_present",
        "real_covalent_confirmed_candidate_full_atom_extraction_if_present",
        "final_dataset_smoke_preview_if_present",
        "metadata_dataloader_smoke_preview_if_present",
        "sample_index_smoke_preview_if_present",
        "step8_topology_evidence_export_if_present",
        "manual_event_identity_curation_required_policy",
    ]:
        assert required in names
    assert {row["evidence_source_inventory_passed"] for row in inventory} == {"True"}
    assert len(mapping) == 14
    assert [row["event_identity_field"] for row in mapping] == [
        "source_profile",
        "source_database",
        "pdb_id",
        "ligand_identifier",
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_bond_atom_pair",
        "covalent_event_id",
        "candidate_metadata_id",
        "evidence_source",
        "evidence_provenance_status",
    ]
    assert {row["mapping_contract_passed"] for row in mapping} == {"True"}
    by_field = {row["event_identity_field"]: row for row in mapping}
    assert by_field["pdb_id"]["pdb_only_join_allowed"] == "True"
    assert {row["pdb_only_join_allowed"] for row in mapping if row["event_identity_field"] != "pdb_id"} == {"False"}
    assert manifest["evidence_source_inventory_passed"] is True
    assert manifest["event_identity_mapping_contract_passed"] is True


def test_candidate_expansion_and_expanded_candidates_consistency() -> None:
    expansion = _csv_rows(ROOT / "covapie_small_pilot_candidate_expansion_audit.csv")
    expanded_csv = _csv_rows(ROOT / "covapie_small_pilot_expanded_event_candidates.csv")
    expanded_json = json.loads((ROOT / "covapie_small_pilot_expanded_event_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert expansion
    assert {row["candidate_expansion_passed"] for row in expansion} == {"True"}
    assert {row["pdb_only_join_used"] for row in expansion} == {"False"}
    assert len(expanded_csv) == len(expanded_json)
    assert len(expanded_csv) == manifest["expanded_event_candidates_row_count"]
    assert manifest["expanded_event_candidates_csv_json_consistent"] is True
    assert manifest["selected_for_manifest_rerun_count"] <= 50
    for row in expanded_csv:
        if row["selected_for_small_pilot_manifest_rerun"] == "True":
            assert row["event_identity_complete"] == "True"
            assert row["pdb_only_join_used"] == "False"
            assert row["covalent_event_id"]
            assert row["chain_id"]
            assert row["residue_name"]
            assert row["residue_index"]
            assert row["residue_atom_name"]
            assert row["covalent_bond_atom_pair"]
    if manifest["selected_for_manifest_rerun_count"] >= 20:
        assert manifest["ready_for_covapie_small_pilot_download_manifest_rerun_gate"] is True
        assert manifest["ready_for_covapie_small_pilot_manual_event_identity_curation_gate"] is False
    else:
        assert manifest["ready_for_covapie_small_pilot_download_manifest_rerun_gate"] is False
        assert manifest["ready_for_covapie_small_pilot_manual_event_identity_curation_gate"] is True


def test_gap_taxonomy_readiness_and_boundaries() -> None:
    gap = _csv_rows(ROOT / "covapie_small_pilot_candidate_gap_taxonomy_audit.csv")
    readiness = _csv_rows(ROOT / "covapie_small_pilot_candidate_expansion_readiness_contract.csv")
    manifest = _manifest()
    assert len(gap) == 12
    assert [row["gap_type"] for row in gap] == [
        "missing_chain_id",
        "missing_residue_name",
        "missing_residue_index",
        "missing_residue_atom_name",
        "missing_ligand_atom_name",
        "missing_covalent_bond_atom_pair",
        "missing_ligand_identifier",
        "missing_covalent_event_id",
        "duplicate_event_identity",
        "pdb_only_join_blocked",
        "non_cys_or_non_sg_event_out_of_v1_scope",
        "missing_authoritative_evidence_source",
    ]
    assert {row["gap_taxonomy_passed"] for row in gap} == {"True"}
    assert len(readiness) == 10
    assert {row["readiness_passed"] for row in readiness} == {"True"}
    assert manifest["ready_for_covapie_small_pilot_download_smoke"] is False
    assert manifest["ready_for_covapie_bulk_download_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["recommended_next_step"] in {
        "covapie_small_pilot_download_manifest_rerun_gate",
        "covapie_small_pilot_manual_event_identity_curation_gate",
    }


def test_runtime_raw_download_dataloader_training_and_mask_boundaries() -> None:
    manifest = _manifest()
    for key in [
        "pdb_only_join_used",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "raw_file_content_read_current_step",
        "raw_data_read",
        "mmcif_text_read",
        "mmcif_parse_current_step",
        "coordinate_extraction_current_step",
        "ligand_topology_auto_restored_current_step",
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
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
    ]:
        assert manifest[key] is False, key
    assert manifest["pdb_only_join_blocked"] is True
    assert manifest["canonical_mask_task_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert manifest["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_candidate_expansion_gate.py"), "torch")
    assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_candidate_expansion_gate.py"), "numpy")
    assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_candidate_expansion_gate.py"), "urllib")


def test_safety_audit_existing_artifacts_unchanged_and_raw_untracked() -> None:
    safety = _csv_rows(ROOT / "covapie_small_pilot_candidate_expansion_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) >= 31
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "raw_files_untracked",
        "raw_files_unstaged",
        "raw_files_not_read_current_step",
        "no_network_access_current_step",
        "no_download_current_step",
        "no_raw_files_written_current_step",
        "no_download_manifest_written_current_step",
        "no_actual_dataloader_smoke_written",
        "metadata_csv_unchanged",
        "step14c_artifacts_unchanged",
        "step14b_artifacts_unchanged",
        "step14a_artifacts_unchanged",
        "step13bz_artifacts_unchanged",
        "step13by_artifacts_unchanged",
        "step13bx_artifacts_unchanged",
        "step13bu_artifacts_unchanged",
        "step13bo_artifacts_unchanged",
        "step13bm_artifacts_unchanged",
        "step13ai_inventory_artifacts_unchanged",
        "protected_source_diff_empty",
        "original_dataloader_diff_empty",
        "no_network_download_rdkit_biopdb_gemmi_gzip_torch_numpy_imports",
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert manifest["safety_audit_passed"] is True
    tracked = subprocess.run(["git", "ls-files", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert tracked == ""
    assert staged == ""
