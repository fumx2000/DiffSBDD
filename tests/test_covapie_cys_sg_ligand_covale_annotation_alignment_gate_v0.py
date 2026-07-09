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

from covalent_ext import covapie_cys_sg_discovery_support_review_gate as step14i
from covalent_ext import covapie_cys_sg_ligand_covale_annotation_alignment_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_annotation_alignment_gate_manifest.json"
    assert path.is_file(), "Run the Step 14J check script before artifact tests"
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


def test_step14i_precondition_and_candidate_input() -> None:
    step14i_manifest = json.loads(step14i.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_annotation_alignment_precondition_audit.csv")
    input_audit = _csv_rows(ROOT / "covapie_cys_sg_annotation_candidate_input_audit.csv")
    manifest = _manifest()
    assert step14i_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14i_manifest["all_checks_passed"] is True
    assert step14i_manifest["ligand_covale_candidate_count"] == 9
    assert step14i_manifest["ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(input_audit) == 10
    assert {row["candidate_input_passed"] for row in input_audit} == {"True"}
    assert manifest["input_ligand_covale_candidate_count"] == 9
    assert manifest["annotation_alignment_candidate_count"] == 9


def test_metadata_schema_audit_records_optional_event_annotation_gaps() -> None:
    schema = _csv_rows(ROOT / "covapie_cys_sg_annotation_metadata_schema_audit.csv")
    by_field = {row["metadata_field_name"]: row for row in schema}
    assert by_field["pdb_id"]["field_present"] == "True"
    assert by_field["pdb_id"]["schema_audit_passed"] == "True"
    assert any(by_field[field]["field_present"] == "True" for field in ["covpdb_ligand_id", "het_code", "ligand_name"])
    assert {row["schema_audit_passed"] for row in schema} == {"True"}
    for optional in ["residue_name", "residue_atom_name", "residue_index", "chain_id", "warhead", "mechanism"]:
        assert by_field[optional]["schema_audit_passed"] == "True"


def test_annotation_candidates_are_consistent_pending_and_not_ready() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_annotation_alignment_candidates.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_annotation_alignment_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["annotation_alignment_candidate_count"] == 9
    assert manifest["annotation_alignment_candidates_csv_json_consistent"] is True
    assert {row["manual_review_status"] for row in rows} == {"pending_manual_review"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["struct_conn_type"] for row in rows} == {"covale"}
    assert {row["rcsb_covale_evidence_status"] for row in rows} == {"rcsb_struct_conn_covale_evidence_present"}
    assert all(int(row["metadata_row_match_count_by_pdb"]) >= 1 for row in rows)
    assert manifest["metadata_pdb_match_count"] == 9
    assert manifest["metadata_ligand_or_het_alignment_count"] == 9
    assert manifest["metadata_event_annotation_gap_count"] == 9
    assert manifest["metadata_conflict_count"] == 0
    assert manifest["all_annotation_alignment_candidates_pending_manual_review"] is True
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True
    assert {row["covpdb_metadata_alignment_status"] for row in rows} == {"metadata_ligand_or_het_aligned_pending_manual_review"}
    assert {row["annotation_gap_status"] for row in rows} == {"metadata_event_annotation_gap_recorded"}


def test_gap_readiness_and_below_20_next_step() -> None:
    gap = _csv_rows(ROOT / "covapie_cys_sg_annotation_gap_audit.csv")
    readiness = _csv_rows(ROOT / "covapie_cys_sg_annotation_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(gap) == 10
    assert len(readiness) == 10
    assert {row["gap_audit_passed"] for row in gap} == {"True"}
    assert {row["readiness_passed"] for row in readiness} == {"True"}
    assert manifest["small_pilot_threshold_20_met"] is False
    assert manifest["small_pilot_threshold_20_status"] == "below_threshold_needs_targeted_expansion_after_alignment"
    assert manifest["ready_for_covapie_cys_sg_ligand_covale_manual_review_gate"] is True
    assert manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20"] is True
    assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_metadata_expansion_gate"
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_safety_masks_no_raw_network_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_annotation_alignment_safety_audit.csv")
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
        "step14i_artifacts_unchanged",
        "step14h_artifacts_unchanged",
        "step14g_artifacts_unchanged",
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
        "no_ready_candidates_created",
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
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_ligand_covale_annotation_alignment_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0.py"), name)
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
