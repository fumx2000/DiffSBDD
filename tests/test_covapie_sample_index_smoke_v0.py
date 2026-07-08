from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_sample_index_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_sample_index_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_index_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13BH check script before artifact tests"
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


def test_step13bg_precondition_and_readiness_boundary() -> None:
    manifest13bg = json.loads(smoke.step13bg.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_index_smoke_precondition_audit.csv")
    manifest = _manifest()
    assert manifest13bg["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13bg["all_checks_passed"] is True
    assert manifest13bg["ready_for_covapie_sample_index_smoke"] is True
    assert manifest13bg["ready_for_covapie_sample_index_qa_gate"] is False
    assert manifest13bg["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["step13bg_sample_index_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_sample_index_csv_json_schema_and_identity_contract() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_smoke.csv")
    json_rows = json.loads((ROOT / "covapie_sample_index_smoke.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == 20
    assert len(json_rows) == 20
    assert list(rows[0].keys()) == smoke.SAMPLE_INDEX_FIELDS
    assert list(json_rows[0].keys()) == smoke.SAMPLE_INDEX_FIELDS
    assert len(rows[0]) == 31
    assert manifest["sample_index_row_count"] == 20
    assert manifest["sample_index_column_count"] == 31
    assert manifest["sample_index_json_row_count"] == 20
    assert rows == [{key: str(value) for key, value in item.items()} for item in json_rows]
    sample_ids = [row["sample_id"] for row in rows]
    assert len(set(sample_ids)) == 20
    assert manifest["sample_id_unique_count"] == 20
    for row in rows:
        assert row["sample_id"] == f"sample::{row['candidate_metadata_id']}::{row['mask_task_name']}"
        assert row["sample_index_materialized_current_step"] == "True"
        assert row["ready_for_training"] == "False"


def test_four_events_by_five_canonical_masks_and_b3_included() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_smoke.csv")
    manifest = _manifest()
    event_counts = Counter(row["extracted_event_id"] for row in rows)
    mask_counts = Counter(row["mask_task_name"] for row in rows)
    alias_counts = Counter(row["mask_task_alias"] for row in rows)
    assert len(event_counts) == 4
    assert set(event_counts.values()) == {5}
    assert mask_counts == {name: 4 for name in smoke.CANONICAL_MASK_TASK_NAMES}
    assert alias_counts == {alias: 4 for alias in smoke.CANONICAL_MASK_TASK_ALIASES}
    assert "scaffold_only" in mask_counts
    assert "B3" in alias_counts
    assert manifest["unique_event_count"] == 4
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["planned_sample_count"] == 20
    assert manifest["observed_sample_count"] == 20
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["mask_scaffold_only_B3_count"] == 4


def test_row_qa_mask_distribution_and_source_traceability_pass() -> None:
    row_qa = _csv_rows(ROOT / "covapie_sample_index_row_qa_audit.csv")
    mask = _csv_rows(ROOT / "covapie_sample_index_mask_distribution_audit.csv")
    trace = _csv_rows(ROOT / "covapie_sample_index_source_traceability_audit.csv")
    manifest = _manifest()
    assert len(row_qa) == 20
    assert len(mask) == 5
    assert len(trace) == 4
    for key in [
        "sample_id_deterministic",
        "sample_id_unique",
        "schema_order_matches_contract",
        "source_event_found",
        "source_event_extraction_success",
        "source_event_geometry_qa_passed",
        "protein_atom_rows_count_matches_source",
        "ligand_atom_rows_count_matches_source",
        "canonical_mask_task_valid",
        "b3_scaffold_only_included_when_applicable",
        "annotation_blockers_preserved",
        "auxiliary_label_blockers_preserved",
        "ready_for_training_false",
        "row_qa_passed",
    ]:
        assert {row[key] for row in row_qa} == {"True"}
    assert {row["mask_distribution_passed"] for row in mask} == {"True"}
    assert {row["observed_row_count"] for row in mask} == {"4"}
    assert {row["observed_unique_event_count"] for row in mask} == {"4"}
    assert {row["sample_index_rows_for_event"] for row in trace} == {"5"}
    for key in [
        "source_event_table_found",
        "source_protein_atom_rows_found",
        "source_ligand_atom_rows_found",
        "step13bf_event_qa_found",
        "step13bf_atom_qa_found",
        "step13bf_geometry_qa_found",
        "step13bg_mask_expansion_contract_found",
        "traceability_qa_passed",
    ]:
        assert {row[key] for row in trace} == {"True"}
    assert manifest["row_qa_passed"] is True
    assert manifest["mask_distribution_qa_passed"] is True
    assert manifest["source_traceability_qa_passed"] is True


def test_source_atom_counts_match_extracted_tables() -> None:
    sample_rows = _csv_rows(ROOT / "covapie_sample_index_smoke.csv")
    protein_rows = _csv_rows(smoke.step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(smoke.step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    protein_counts = Counter(row["extracted_event_id"] for row in protein_rows)
    ligand_counts = Counter(row["extracted_event_id"] for row in ligand_rows)
    for row in sample_rows:
        assert int(row["protein_atom_row_count_for_event"]) == protein_counts[row["extracted_event_id"]]
        assert int(row["ligand_atom_row_count_for_event"]) == ligand_counts[row["extracted_event_id"]]
    assert sum(protein_counts.values()) == 1071
    assert sum(ligand_counts.values()) == 149


def test_boundary_git_safety_training_blockers_and_no_forbidden_outputs() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_sample_index_smoke_boundary_safety.csv")}
    git_rows = _csv_rows(ROOT / "covapie_sample_index_smoke_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_sample_index_smoke_training_blockers.csv")
    manifest = _manifest()
    assert boundary["sample_index_smoke"]["current_step_status"] == "executed_smoke_only"
    assert boundary["read_step13bg_design_contracts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13bf_qa_artifacts"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["read_step13be_extracted_tables"]["current_step_status"] == "executed_derived_csv_json_read_only"
    assert boundary["sample_index_csv_write"]["current_step_status"] == "executed_smoke_only"
    assert boundary["sample_index_json_write"]["current_step_status"] == "executed_smoke_only"
    assert boundary["sample_index_qa_gate"]["current_step_status"] == "blocked_until_next_gate"
    for item in ["final_dataset", "split_assignments", "leakage_matrix", "dataloader_smoke", "training"]:
        assert boundary[item]["current_step_status"] == "blocked_current_step"
    for item in ["raw_file_content_read", "mmcif_parse", "coordinate_extraction", "network_access", "raw_download", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary.values()} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_rows} == {"True"}
    assert [row["training_blocker_item"] for row in blockers[:5]] == [
        "mask_warhead_only_A",
        "mask_linker_plus_warhead_B",
        "mask_scaffold_plus_warhead_B2",
        "mask_scaffold_only_B3",
        "mask_scaffold_plus_linker_plus_warhead_C",
    ]
    assert {row["training_blocker_passed"] for row in blockers} == {"True"}
    assert manifest["boundary_safety_passed"] is True
    assert manifest["git_safety_passed"] is True
    assert manifest["training_blockers_passed"] is True
    forbidden_names = {"final_dataset.csv", "final_dataset.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json"}
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    assert [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes] == []


def test_no_raw_network_runtime_model_or_training_imports_and_readiness() -> None:
    module_path = Path("src/covalent_ext/covapie_sample_index_smoke.py")
    script_path = Path("scripts/check_covapie_sample_index_smoke_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "shlex"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    tracked = subprocess.run(["git", "ls-files", str(smoke.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(smoke.step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    assert manifest["sample_index_materialized_current_step"] is True
    assert manifest["sample_index_written"] is True
    for key in [
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
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
        "ready_for_covapie_split_leakage_design_gate",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_sample_index_qa_gate"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_sample_index_qa_gate"
