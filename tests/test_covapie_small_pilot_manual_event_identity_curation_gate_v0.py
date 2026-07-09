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

from covalent_ext import covapie_small_pilot_manual_event_identity_curation_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_small_pilot_manual_event_identity_curation_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_manual_event_identity_curation_gate_manifest.json"
    assert path.is_file(), "Run the Step 14E check script before artifact tests"
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


def test_step14d_precondition_and_source_profile_preserved() -> None:
    manifest14d = json.loads(gate.STEP14D_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_manual_event_identity_curation_precondition_audit.csv")
    manifest = _manifest()
    assert manifest14d["stage"] == gate.PREVIOUS_STAGE
    assert manifest14d["step_label"] == "Step 14D"
    assert manifest14d["all_checks_passed"] is True
    assert manifest14d["current_source_profile"] == gate.CURRENT_SOURCE_PROFILE
    assert manifest14d["current_source_database"] == gate.CURRENT_SOURCE_DATABASE
    assert manifest14d["selected_for_manifest_rerun_count"] == 0
    assert manifest14d["ready_for_covapie_small_pilot_manual_event_identity_curation_gate"] is True
    assert manifest14d["ready_for_covapie_small_pilot_download_smoke"] is False
    assert manifest14d["recommended_next_step"] == "covapie_small_pilot_manual_event_identity_curation_gate"
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["current_source_profile"] == gate.CURRENT_SOURCE_PROFILE
    assert manifest["current_source_database"] == gate.CURRENT_SOURCE_DATABASE
    assert manifest["step14d_candidate_expansion_block_validated"] is True


def test_field_contract_and_curation_template_pending_consistency() -> None:
    fields = _csv_rows(ROOT / "covapie_manual_event_identity_curation_field_contract.csv")
    template_csv = _csv_rows(ROOT / "covapie_manual_event_identity_curation_candidate_template.csv")
    template_json = json.loads((ROOT / "covapie_manual_event_identity_curation_candidate_template.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(fields) == 18
    assert {row["field_contract_passed"] for row in fields} == {"True"}
    by_field = {row["field_name"]: row for row in fields}
    assert by_field["pdb_id"]["prefilled_from_metadata_allowed"] == "True"
    assert by_field["ligand_identifier"]["prefilled_from_metadata_allowed"] == "True"
    for field in ["chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair"]:
        assert by_field[field]["must_be_manual_or_authoritative"] == "True"
    assert by_field["covalent_event_id"]["must_be_manual_or_authoritative"] == "True"
    assert "never PDB-only" in by_field["covalent_event_id"]["allowed_values_or_policy"]
    assert len(template_csv) == len(template_json)
    assert len(template_csv) == manifest["manual_curation_template_row_count"]
    assert len(template_csv) <= 50
    assert manifest["manual_curation_template_csv_json_consistent"] is True
    assert {row["manual_review_status"] for row in template_csv} == {"pending_manual_review"}
    assert {row["evidence_provenance_status"] for row in template_csv} == {"pending_manual_evidence"}
    assert {row["selected_for_manual_curation"] for row in template_csv} == {"True"}
    assert {row["cys_sg_v1_candidate"] for row in template_csv} == {"unknown_pending_manual_review"}
    assert manifest["manual_review_status_all_pending"] is True
    assert manifest["ready_candidate_count_current_step"] == 0
    for row in template_csv:
        for field in ["chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "covalent_event_id"]:
            assert row[field] == ""


def test_instruction_evidence_v1_scope_and_readiness_contracts() -> None:
    instructions = _csv_rows(ROOT / "covapie_manual_event_identity_curation_instruction_sheet.csv")
    evidence = _csv_rows(ROOT / "covapie_manual_event_identity_required_evidence_contract.csv")
    v1_scope = _csv_rows(ROOT / "covapie_manual_event_identity_v1_scope_contract.csv")
    readiness = _csv_rows(ROOT / "covapie_manual_event_identity_curation_readiness_contract.csv")
    manifest = _manifest()
    assert len(instructions) == 12
    assert {row["instruction_passed"] for row in instructions} == {"True"}
    assert instructions[-1]["instruction_item"] == "never_use_pdb_only_join"
    assert len(evidence) == 10
    assert {row["current_step_status"] for row in evidence} == {"template_only_not_validated"}
    assert {row["evidence_contract_passed"] for row in evidence} == {"True"}
    assert len(v1_scope) == 8
    assert [row["scope_item"] for row in v1_scope][:2] == ["v1_residue_scope_cys_only", "v1_residue_atom_scope_sg"]
    assert {row["scope_contract_passed"] for row in v1_scope} == {"True"}
    assert len(readiness) == 10
    assert {row["readiness_passed"] for row in readiness} == {"True"}
    by_ready = {row["readiness_item"]: row for row in readiness}
    assert by_ready["ready_candidate_count_current_step_zero"]["observed_status"] == "0"
    assert by_ready["ready_for_manual_curation_validation_gate"]["observed_status"] == "true"
    assert by_ready["ready_for_manifest_rerun_gate_false"]["observed_status"] == "false"
    assert by_ready["ready_for_download_smoke_false"]["observed_status"] == "false"
    assert manifest["instruction_sheet_passed"] is True
    assert manifest["required_evidence_contract_passed"] is True
    assert manifest["v1_scope_contract_passed"] is True
    assert manifest["readiness_contract_passed"] is True


def test_runtime_boundaries_masks_and_training_blockers() -> None:
    manifest = _manifest()
    for key in [
        "pdb_only_join_used",
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_covapie_bulk_download_smoke",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
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
    assert manifest["ready_for_covapie_small_pilot_manual_event_identity_validation_gate"] is True
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
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_small_pilot_manual_event_identity_validation_gate"
    for name in ["torch", "numpy", "urllib", "requests", "rdkit", "Bio", "gemmi", "gzip"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_manual_event_identity_curation_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_small_pilot_manual_event_identity_curation_gate_v0.py"), name)


def test_safety_audit_existing_artifacts_unchanged_and_raw_untracked() -> None:
    safety = _csv_rows(ROOT / "covapie_manual_event_identity_curation_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) >= 33
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
        "no_real_final_dataset_written",
        "no_new_sample_index_written",
        "no_split_assignments_written",
        "no_leakage_matrix_written",
        "metadata_csv_unchanged",
        "step14d_artifacts_unchanged",
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
        "derived_output_no_forbidden_binary_artifacts",
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert manifest["safety_audit_passed"] is True
    assert not subprocess.run(["git", "ls-files", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()


def test_no_forbidden_named_or_suffix_artifacts() -> None:
    forbidden_names = {
        "actual_download_manifest.csv",
        "actual_download_manifest.json",
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
        "download_smoke.csv",
        "download_smoke.json",
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
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert not [path for path in ROOT.rglob("*") if path.name in forbidden_names]
    assert not [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes]
