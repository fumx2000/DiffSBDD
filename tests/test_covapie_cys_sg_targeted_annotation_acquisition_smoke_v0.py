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

from covalent_ext import covapie_cys_sg_targeted_annotation_acquisition_smoke as smoke
from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_gate as step14k


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_annotation_acquisition_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_targeted_annotation_acquisition_smoke_manifest.json"
    assert path.is_file(), "Run the Step 14L check script before artifact tests"
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


def test_step14k_precondition_and_execution_manifest() -> None:
    step14k_manifest = json.loads(step14k.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_targeted_annotation_acquisition_precondition_audit.csv")
    execution = _csv_rows(ROOT / "covapie_cys_sg_targeted_annotation_acquisition_execution_audit.csv")
    manifest = _manifest()
    assert step14k_manifest["stage"] == smoke.PREVIOUS_STAGE
    assert step14k_manifest["all_checks_passed"] is True
    assert step14k_manifest["acquisition_manifest_row_count"] == 29
    assert step14k_manifest["ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(execution) == manifest["input_acquisition_manifest_row_count"] == 29
    assert {row["execution_audit_passed"] for row in execution} == {"True"}
    assert manifest["network_access_used"] is True
    assert manifest["download_attempted"] is True


def test_extraction_audits_exist_and_cover_inputs() -> None:
    ligand = _csv_rows(ROOT / "covapie_cys_sg_covpdb_ligand_card_extraction_audit.csv")
    complex_rows = _csv_rows(ROOT / "covapie_cys_sg_covpdb_complex_card_extraction_audit.csv")
    ccd = _csv_rows(ROOT / "covapie_cys_sg_rcsb_ccd_extraction_audit.csv")
    manifest = _manifest()
    assert len(ligand) >= 1
    assert len(complex_rows) == manifest["input_seed_candidate_count"] == 9
    assert len(ccd) >= 1
    assert manifest["ligand_card_fetch_success_count"] >= 0
    assert manifest["complex_card_resolved_count"] >= 0
    assert manifest["complex_card_event_annotation_acquired_count"] >= 0
    assert manifest["rcsb_ccd_fetch_success_count"] >= 0
    assert any(row["ligand_card_fetch_status"] == "fetched" for row in ligand) or any(row["rcsb_ccd_fetch_status"] == "fetched" for row in ccd)


def test_acquired_annotation_candidates_policy_and_consistency() -> None:
    acquired = _csv_rows(ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.csv")
    acquired_json = json.loads((ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(acquired) == len(acquired_json) == manifest["acquired_annotation_candidate_count"] == 9
    assert manifest["acquired_annotation_candidates_csv_json_consistent"] is True
    assert {row["manual_review_status"] for row in acquired} == {"pending_manual_review"}
    assert {row["event_identity_status_current_step"] for row in acquired} == {"not_event_identity_until_manual_review"}
    assert {row["ready_candidate_current_step"] for row in acquired} == {"False"}
    assert {row["ready_for_training_current_step"] for row in acquired} == {"False"}
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True


def test_gap_and_readiness_boundaries() -> None:
    gap = _csv_rows(ROOT / "covapie_cys_sg_targeted_annotation_acquisition_gap_audit.csv")
    manifest = _manifest()
    by_item = {row["gap_item"]: row for row in gap}
    assert int(by_item["seed_candidate_count"]["gap_value"]) == 9
    assert int(by_item["acquired_event_annotation_candidate_count"]["gap_value"]) == 9
    assert int(by_item["ready_candidate_count_current_step"]["gap_value"]) == 0
    assert by_item["below_20_threshold_status"]["gap_value"] == "below_threshold_needs_additional_cys_sg_candidates"
    assert by_item["targeted_expansion_still_required"]["gap_value"] == "True"
    assert by_item["training_still_blocked"]["gap_value"] == "True"
    assert manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate"] is True
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate"


def test_safety_raw_artifact_and_import_boundaries() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_targeted_annotation_acquisition_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "raw_coordinate_downloaded",
        "raw_file_content_read_current_step",
        "raw_files_written_current_step",
        "html_files_written_current_step",
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
    for root in [smoke.RAW_OUTPUT_ROOT, smoke.RAW_REFERENCE_ROOT]:
        tracked = subprocess.run(["git", "ls-files", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not tracked
        assert not staged
    for name in ["requests", "torch", "numpy", "rdkit", "Bio", "gemmi", "gzip", "selenium", "playwright", "bs4"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_targeted_annotation_acquisition_smoke.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_targeted_annotation_acquisition_smoke_v0.py"), name)
    assert _imports_name(Path("src/covalent_ext/covapie_cys_sg_targeted_annotation_acquisition_smoke.py"), "urllib")


def test_canonical_masks_preserved() -> None:
    manifest = _manifest()
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
