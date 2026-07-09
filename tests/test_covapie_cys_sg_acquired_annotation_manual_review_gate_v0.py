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

from covalent_ext import covapie_cys_sg_acquired_annotation_manual_review_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_acquired_annotation_manual_review_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_acquired_annotation_manual_review_gate_manifest.json"
    assert path.is_file(), "Run the Step 14O check script before artifact tests"
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


def test_step14n_precondition_and_manifest_contract() -> None:
    step14n_manifest = json.loads(gate.STEP14N_MANIFEST_JSON.read_text(encoding="utf-8"))
    pre = _csv_rows(ROOT / "covapie_cys_sg_manual_review_precondition_audit.csv")
    manifest = _manifest()
    assert step14n_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14n_manifest["all_checks_passed"] is True
    assert step14n_manifest["existing_candidate_count"] == 9
    assert step14n_manifest["new_candidate_count"] == 16
    assert step14n_manifest["combined_candidate_count"] == 25
    assert step14n_manifest["ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate"] is True
    assert {row["precondition_passed"] for row in pre} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step14l_input_candidate_count"] == 9
    assert manifest["step14n_input_candidate_count"] == 16
    assert manifest["combined_manual_review_candidate_count"] == 25
    assert manifest["threshold_20_met"] is True
    assert manifest["all_checks_passed"] is True


def test_combined_inventory_source_counts_and_statuses() -> None:
    inventory = _csv_rows(ROOT / "covapie_cys_sg_combined_acquired_annotation_inventory.csv")
    manifest = _manifest()
    assert len(inventory) == manifest["combined_manual_review_candidate_count"] == 25
    source_counts = {
        "step14l": sum(row["candidate_source_stage"] == "step14l_targeted_annotation_acquisition" for row in inventory),
        "step14n": sum(row["candidate_source_stage"] == "step14n_next_batch_metadata_acquisition" for row in inventory),
    }
    assert source_counts == {"step14l": 9, "step14n": 16}
    assert {row["manual_review_status"] for row in inventory} == {"pending_manual_review"}
    assert {row["ready_candidate_current_step"] for row in inventory} == {"False"}
    assert {row["ready_for_training_current_step"] for row in inventory} == {"False"}
    assert {row["inventory_row_passed"] for row in inventory} == {"True"}
    assert {
        row["struct_conn_evidence_status"]
        for row in inventory
        if row["candidate_source_stage"] == "step14l_targeted_annotation_acquisition"
    } == {"available_from_step14j_struct_conn"}
    assert {
        row["struct_conn_evidence_status"]
        for row in inventory
        if row["candidate_source_stage"] == "step14n_next_batch_metadata_acquisition"
    } == {"pending_future_raw_mmcif_struct_conn_crosscheck"}


def test_event_identity_audit_has_no_duplicate_or_single_field_identity() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_combined_event_identity_audit.csv")
    assert len(rows) == 25
    assert len({row["event_identity_tuple"] for row in rows}) == 25
    assert {row["duplicate_within_combined_inventory"] for row in rows} == {"False"}
    assert {row["pdb_id_alone_used_as_identity"] for row in rows} == {"False"}
    assert {row["ligand_id_alone_used_as_identity"] for row in rows} == {"False"}
    assert {row["has_cys_residue"] for row in rows} == {"True"}
    assert {row["has_warhead"] for row in rows} == {"True"}
    assert {row["has_reaction"] for row in rows} == {"True"}
    assert {row["has_chain"] for row in rows} == {"True"}
    assert {row["has_ligand_metadata"] for row in rows} == {"True"}
    assert {row["event_identity_audit_passed"] for row in rows} == {"True"}
    assert sum(row["has_struct_conn_evidence"] == "True" for row in rows) == 9
    assert sum(row["requires_future_struct_conn_crosscheck"] == "True" for row in rows) == 16


def test_manual_review_decision_template_pending_and_consistent() -> None:
    template = _csv_rows(ROOT / "covapie_cys_sg_manual_review_decision_template.csv")
    template_json = json.loads((ROOT / "covapie_cys_sg_manual_review_decision_template.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(template) == len(template_json) == manifest["manual_review_template_row_count"] == 25
    assert [row["manual_review_candidate_id"] for row in template] == [
        row["manual_review_candidate_id"] for row in template_json
    ]
    assert manifest["manual_review_template_csv_json_consistent"] is True
    assert {row["manual_decision"] for row in template} == {"pending_manual_review"}
    for row in template:
        allowed = set(row["manual_decision_allowed_values"].split(";"))
        assert {"pending_manual_review", "accept_for_future_struct_conn_crosscheck", "reject", "needs_more_evidence"} <= allowed


def test_criteria_auto_flags_and_downstream_readiness() -> None:
    criteria = _csv_rows(ROOT / "covapie_cys_sg_manual_review_criteria_contract.csv")
    flags = _csv_rows(ROOT / "covapie_cys_sg_manual_review_auto_flag_audit.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_manual_review_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(criteria) == 12
    assert {row["criterion_contract_passed"] for row in criteria} == {"True"}
    by_flag = {row["auto_flag_item"]: row["auto_flag_value"] for row in flags}
    assert by_flag["total_manual_review_candidate_count"] == "25"
    assert by_flag["step14l_candidate_count"] == "9"
    assert by_flag["step14n_candidate_count"] == "16"
    assert by_flag["pending_manual_review_count"] == "25"
    assert by_flag["ready_candidate_count_current_step"] == "0"
    assert by_flag["step14n_requires_struct_conn_crosscheck_count"] == "16"
    assert by_flag["duplicate_candidate_count"] == "0"
    assert {row["auto_flag_audit_passed"] for row in flags} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_manual_review_input_by_user"] is True
    assert manifest["ready_for_covapie_cys_sg_manual_review_decision_application_gate"] is False
    assert manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "manual_review_decision_input_by_user"


def test_safety_no_raw_training_artifacts_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_manual_review_safety_audit.csv")
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
        "urllib_used",
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
    for name in ["requests", "urllib", "torch", "numpy", "rdkit", "Bio", "gemmi", "gzip", "selenium", "playwright", "bs4"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_acquired_annotation_manual_review_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_acquired_annotation_manual_review_gate_v0.py"), name)


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
