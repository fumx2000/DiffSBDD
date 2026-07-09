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

from covalent_ext import covapie_cys_sg_targeted_annotation_acquisition_smoke as step14l
from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_next_batch_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_manifest.json"
    assert path.is_file(), "Run the Step 14M check script before artifact tests"
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


def test_step14l_precondition_and_candidate_counts() -> None:
    step14l_manifest = json.loads(step14l.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_next_batch_precondition_audit.csv")
    existing = _csv_rows(ROOT / "covapie_cys_sg_existing_acquired_candidate_audit.csv")
    manifest = _manifest()
    assert step14l_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14l_manifest["all_checks_passed"] is True
    assert step14l_manifest["acquired_annotation_candidate_count"] == 9
    assert step14l_manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(existing) == manifest["input_acquired_annotation_candidate_count"] == 9
    assert manifest["current_candidate_count"] == 9
    assert manifest["total_candidate_target"] == 20
    assert manifest["additional_candidate_needed_count"] == 11
    assert manifest["next_batch_minimum_new_candidate_target"] == 11


def test_existing_candidates_and_exclusion_registry() -> None:
    existing = _csv_rows(ROOT / "covapie_cys_sg_existing_acquired_candidate_audit.csv")
    exclusion = _csv_rows(ROOT / "covapie_cys_sg_next_batch_exclusion_registry.csv")
    manifest = _manifest()
    assert len(existing) == 9
    assert len(exclusion) == manifest["existing_candidate_exclusion_registry_count"] == 9
    assert {row["manual_review_status"] for row in existing} == {"pending_manual_review"}
    assert {row["ready_candidate_current_step"] for row in existing} == {"False"}
    assert {row["included_in_exclusion_registry"] for row in existing} == {"True"}
    assert {row["existing_candidate_audit_passed"] for row in existing} == {"True"}
    assert {row["exclusion_reason"] for row in exclusion} == {"already_acquired_in_step14l"}
    assert {row["exclusion_registry_passed"] for row in exclusion} == {"True"}


def test_source_strategy_and_next_batch_manifest_contract() -> None:
    strategy = _csv_rows(ROOT / "covapie_cys_sg_next_batch_source_strategy_contract.csv")
    next_batch = _csv_rows(ROOT / "covapie_cys_sg_next_batch_acquisition_manifest.csv")
    next_batch_json = json.loads((ROOT / "covapie_cys_sg_next_batch_acquisition_manifest.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    items = {row["strategy_item"] for row in strategy}
    assert len(strategy) == manifest["next_batch_source_strategy_row_count"] >= 12
    assert {
        "covpdb_targetable_residue_cys_page_primary",
        "covpdb_cys_complex_listing_or_download_primary",
        "exclude_existing_9_candidates",
        "require_cys_sg_ligand_covale",
        "manual_review_required_before_ready",
    } <= items
    assert {row["strategy_contract_passed"] for row in strategy} == {"True"}
    assert len(next_batch) == len(next_batch_json) == manifest["next_batch_acquisition_manifest_row_count"] >= 5
    assert manifest["next_batch_acquisition_manifest_csv_json_consistent"] is True
    assert {row["acquisition_status_current_step"] for row in next_batch} == {"pending_future_acquisition"}
    assert {row["event_identity_status_current_step"] for row in next_batch} == {"not_event_identity"}
    assert {row["ready_candidate_current_step"] for row in next_batch} == {"False"}
    assert {row["ready_for_training_current_step"] for row in next_batch} == {"False"}
    assert {row["minimum_new_candidate_target"] for row in next_batch} == {"11"}


def test_threshold_downstream_and_readiness_boundaries() -> None:
    threshold = _csv_rows(ROOT / "covapie_cys_sg_next_batch_threshold_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_next_batch_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(threshold) == 10
    assert len(downstream) == 10
    assert {row["threshold_contract_passed"] for row in threshold} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke"] is True
    assert manifest["ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke"


def test_safety_no_network_raw_training_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_next_batch_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used",
        "download_attempted",
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
        "requests_used",
        "selenium_used",
        "playwright_used",
        "bs4_used",
    ]:
        assert manifest[key] is False, key
    for root in [gate.RAW_OUTPUT_ROOT, gate.RAW_REFERENCE_ROOT]:
        tracked = subprocess.run(["git", "ls-files", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not tracked
        assert not staged
    for name in ["torch", "numpy", "requests", "urllib", "rdkit", "Bio", "gemmi", "gzip", "selenium", "playwright", "bs4"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_expansion_next_batch_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0.py"), name)


def test_canonical_masks_preserved_and_no_ready_candidates() -> None:
    manifest = _manifest()
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True
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
