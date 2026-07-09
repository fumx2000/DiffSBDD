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

from covalent_ext import covapie_cys_sg_ligand_covale_annotation_alignment_gate as step14j
from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_expansion_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_targeted_metadata_expansion_gate_manifest.json"
    assert path.is_file(), "Run the Step 14K check script before artifact tests"
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


def test_step14j_precondition_and_seed_count() -> None:
    step14j_manifest = json.loads(step14j.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_targeted_expansion_precondition_audit.csv")
    seeds = _csv_rows(ROOT / "covapie_cys_sg_targeted_seed_candidate_audit.csv")
    manifest = _manifest()
    assert step14j_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14j_manifest["all_checks_passed"] is True
    assert step14j_manifest["annotation_alignment_candidate_count"] == 9
    assert step14j_manifest["metadata_event_annotation_gap_count"] == 9
    assert step14j_manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(seeds) == manifest["seed_candidate_count"] == 9
    assert {row["included_as_expansion_seed"] for row in seeds} == {"True"}
    assert {row["seed_candidate_audit_passed"] for row in seeds} == {"True"}


def test_field_source_contract_and_source_registry() -> None:
    field = _csv_rows(ROOT / "covapie_cys_sg_event_level_field_source_contract.csv")
    registry = _csv_rows(ROOT / "covapie_cys_sg_targeted_source_registry.csv")
    manifest = _manifest()
    assert len(field) == 18
    assert {row["field_source_contract_passed"] for row in field} == {"True"}
    by_field = {row["event_field"]: row for row in field}
    assert by_field["chain_id"]["primary_source"] == "RCSB mmCIF _struct_conn"
    assert by_field["warhead_type"]["primary_source"] == "CovPDB annotation"
    assert by_field["ligand_het_code"]["primary_source"] == "PDB Chemical Component Dictionary / RCSB ligand context"
    assert by_field["ready_candidate_status"]["primary_source"] == "Manual review"
    ids = {row["source_registry_id"] for row in registry}
    assert len(registry) == manifest["source_registry_row_count"] >= 10
    assert {
        "covpdb_targetable_residue_cys",
        "covpdb_complex_card_for_seed_candidates",
        "covpdb_ligand_pages_for_seed_candidates",
        "covpdb_warhead_pages_or_download_tables",
        "covpdb_covalent_mechanism_pages_or_download_tables",
        "rcsb_mmcif_struct_conn_crosscheck",
        "rcsb_chemical_component_dictionary_crosscheck",
        "manual_review_curator_notes",
    } <= ids
    assert {row["source_registry_passed"] for row in registry} == {"True"}


def test_acquisition_manifest_is_future_only_and_consistent() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_targeted_annotation_acquisition_manifest.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_targeted_annotation_acquisition_manifest.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["acquisition_manifest_row_count"] == 29
    assert manifest["acquisition_manifest_csv_json_consistent"] is True
    assert {row["acquisition_status_current_step"] for row in rows} == {"pending_future_acquisition"}
    assert {row["event_identity_status_current_step"] for row in rows} == {"not_event_identity"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    per_seed = [row for row in rows if row["seed_candidate_id"]]
    assert len(per_seed) == 27
    global_rows = [row for row in rows if not row["seed_candidate_id"]]
    assert len(global_rows) == 2


def test_stop_downstream_and_training_boundaries() -> None:
    stop = _csv_rows(ROOT / "covapie_cys_sg_targeted_expansion_stop_condition_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_targeted_expansion_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(stop) == 8
    assert len(downstream) == 10
    assert {row["stop_condition_passed"] for row in stop} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke"] is True
    assert manifest["ready_for_covapie_cys_sg_ligand_covale_manual_review_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_annotation_acquisition_smoke"


def test_safety_masks_no_raw_network_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_targeted_expansion_safety_audit.csv")
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
        "step14j_artifacts_unchanged",
        "step14i_artifacts_unchanged",
        "step14h_artifacts_unchanged",
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
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_expansion_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_targeted_metadata_expansion_gate_v0.py"), name)
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
