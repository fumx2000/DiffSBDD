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

from covalent_ext import covapie_cys_sg_discovery_download_smoke as step14h
from covalent_ext import covapie_cys_sg_discovery_support_review_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_discovery_support_review_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_support_review_gate_manifest.json"
    assert path.is_file(), "Run the Step 14I check script before artifact tests"
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


def test_step14h_precondition_and_input_audit() -> None:
    step14h_manifest = json.loads(step14h.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_support_review_precondition_audit.csv")
    input_audit = _csv_rows(ROOT / "covapie_cys_sg_support_review_input_proposal_audit.csv")
    manifest = _manifest()
    assert step14h_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14h_manifest["all_checks_passed"] is True
    assert step14h_manifest["support_proposal_count"] == 86
    assert step14h_manifest["ready_for_covapie_cys_sg_discovery_support_review_gate"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(input_audit) == 10
    assert {row["input_audit_passed"] for row in input_audit} == {"True"}
    assert manifest["input_support_proposal_count"] == step14h_manifest["support_proposal_count"]
    assert manifest["input_support_proposal_count"] == 86


def test_disulfide_classification_excludes_sg_sg_and_keeps_ligand_covale_only() -> None:
    audit = _csv_rows(ROOT / "covapie_cys_sg_disulfide_exclusion_audit.csv")
    manifest = _manifest()
    assert len(audit) == 86
    assert {row["disulfide_exclusion_audit_passed"] for row in audit} == {"True"}
    excluded = [row for row in audit if row["review_classification"] == "exclude_disulfide_or_protein_protein_sg_sg"]
    kept = [row for row in audit if row["review_classification"] == "keep_ligand_covale_candidate_pending_review"]
    other = [row for row in audit if row["review_classification"] == "other_excluded_or_needs_manual_triage"]
    assert manifest["disulfide_excluded_count"] == len(excluded)
    assert manifest["ligand_covale_candidate_count"] == len(kept)
    assert manifest["other_excluded_or_triage_count"] == len(other)
    assert excluded
    assert kept
    for row in excluded:
        assert row["keep_for_ligand_covale_review"] == "False"
        assert row["struct_conn_type"] == "disulf" or row["suggested_covalent_bond_atom_pair"] == "SG--SG" or row["suggested_ligand_comp_id"] == "CYS"
    for row in kept:
        assert row["keep_for_ligand_covale_review"] == "True"
        assert row["struct_conn_type"] == "covale"
        assert row["suggested_ligand_comp_id"] != "CYS"
        assert row["suggested_ligand_atom_name"] != "SG"
        assert row["suggested_covalent_bond_atom_pair"] != "SG--SG"


def test_ligand_covale_candidates_are_pending_and_csv_json_consistent() -> None:
    candidates = _csv_rows(ROOT / "covapie_cys_sg_ligand_covale_candidates.csv")
    candidates_json = json.loads((ROOT / "covapie_cys_sg_ligand_covale_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(candidates) == len(candidates_json) == manifest["ligand_covale_candidate_count"]
    assert manifest["ligand_covale_candidates_csv_json_consistent"] is True
    assert candidates
    assert {row["struct_conn_type"] for row in candidates} == {"covale"}
    assert {row["review_status"] for row in candidates} == {"pending_covpdb_annotation_alignment"}
    assert {row["covpdb_annotation_alignment_status"] for row in candidates} == {"pending"}
    assert {row["manual_review_status"] for row in candidates} == {"pending_manual_review"}
    assert {row["ready_candidate_current_step"] for row in candidates} == {"False"}
    assert "CYS" not in {row["suggested_ligand_comp_id"] for row in candidates}
    assert "SG--SG" not in {row["suggested_covalent_bond_atom_pair"] for row in candidates}
    assert manifest["all_ligand_covale_candidates_pending_manual_review"] is True
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True


def test_decision_readiness_next_step_and_training_boundaries() -> None:
    decision = _csv_rows(ROOT / "covapie_cys_sg_support_review_decision_audit.csv")
    readiness = _csv_rows(ROOT / "covapie_cys_sg_support_review_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(decision) == 10
    assert len(readiness) == 10
    assert {row["decision_passed"] for row in decision} == {"True"}
    assert {row["readiness_passed"] for row in readiness} == {"True"}
    if manifest["ligand_covale_candidate_count"] > 0:
        assert manifest["ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate"] is True
        assert manifest["recommended_next_step"] == "covapie_cys_sg_ligand_covale_annotation_alignment_gate"
    else:
        assert manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_gate"] is True
        assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_metadata_expansion_gate"
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_safety_masks_no_raw_network_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_support_review_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "no_network_access_current_step",
        "no_download_current_step",
        "no_raw_file_content_read_current_step",
        "no_raw_files_written_current_step",
        "raw_files_untracked",
        "raw_files_unstaged",
        "metadata_csv_unchanged",
        "step14h_artifacts_unchanged",
        "step14g_artifacts_unchanged",
        "step14f_artifacts_unchanged",
        "step14e_artifacts_unchanged",
        "protected_source_diff_empty",
        "original_dataloader_diff_empty",
        "no_sample_download_manifest_written",
        "no_actual_dataloader_artifacts",
        "no_training_artifacts",
        "no_final_dataset_written",
        "no_sample_index_written",
        "no_split_assignments_written",
        "no_leakage_matrix_written",
        "no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports",
        "derived_output_no_forbidden_binary_or_raw_suffix",
        "pdb_id_not_used_as_event_identity",
        "disulfide_not_promoted_to_training_candidate",
    ]:
        assert by_item[item]["observed_status"] == "passed"
    for key in [
        "network_access_used",
        "download_attempted",
        "raw_file_content_read_current_step",
        "raw_files_written_current_step",
        "sample_download_manifest_written",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "actual_dataloader_adapter_smoke_written",
        "actual_dataloader_smoke_written",
        "training_artifacts_written",
        "torch_imported",
        "numpy_imported",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "gzip_open_used",
    ]:
        assert manifest[key] is False, key
    assert not subprocess.run(["git", "ls-files", gate.RAW_OUTPUT_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    for name in ["torch", "numpy", "requests", "urllib", "rdkit", "Bio", "gemmi", "gzip"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_discovery_support_review_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_discovery_support_review_gate_v0.py"), name)
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
