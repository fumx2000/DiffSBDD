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

from covalent_ext import covapie_cys_sg_acquired_annotation_manual_review_gate as step14o
from covalent_ext import covapie_cys_sg_manual_review_decision_input_by_user as decision_input


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_manual_review_decision_input_by_user_v0")
EXPECTED_ACCEPTED_IDS = [
    "CYS_SG_MANUAL_REVIEW_000010",
    "CYS_SG_MANUAL_REVIEW_000012",
    "CYS_SG_MANUAL_REVIEW_000013",
    "CYS_SG_MANUAL_REVIEW_000014",
    "CYS_SG_MANUAL_REVIEW_000015",
]
EXPECTED_ACCEPTED_PAIRS = ["1A54/MDC", "6BV6/JUG", "6BV9/JUG", "6BV8/JUG", "6BV5/JUG"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_manual_review_decision_input_by_user_manifest.json"
    assert path.is_file(), "Run the Step 14P check script before artifact tests"
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


def test_step14o_precondition_and_manifest_contract() -> None:
    step14o_manifest = json.loads(step14o.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_decision_input_precondition_audit.csv")
    manifest = _manifest()
    assert step14o_manifest["stage"] == decision_input.PREVIOUS_STAGE
    assert step14o_manifest["all_checks_passed"] is True
    assert step14o_manifest["combined_manual_review_candidate_count"] == 25
    assert step14o_manifest["pending_manual_review_count"] == 25
    assert step14o_manifest["ready_for_manual_review_input_by_user"] is True
    assert step14o_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == decision_input.STAGE
    assert manifest["step_label"] == "Step 14P"
    assert manifest["previous_stage"] == decision_input.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_decision_input_marks_exactly_five_user_selected_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_manual_review_decision_input.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_manual_review_decision_input.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["input_manual_review_candidate_count"] == 25
    assert [row["manual_review_candidate_id"] for row in rows] == [
        row["manual_review_candidate_id"] for row in rows_json
    ]
    accepted = [row for row in rows if row["user_manual_decision"] == "accept_for_future_struct_conn_crosscheck"]
    pending = [row for row in rows if row["user_manual_decision"] == "pending_manual_review"]
    assert [row["manual_review_candidate_id"] for row in accepted] == EXPECTED_ACCEPTED_IDS
    assert [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in accepted] == EXPECTED_ACCEPTED_PAIRS
    assert len(accepted) == manifest["accepted_for_future_struct_conn_crosscheck_count"] == 5
    assert len(pending) == manifest["pending_manual_review_count"] == 20
    assert {row["previous_manual_decision"] for row in rows} == {"pending_manual_review"}
    assert {row["user_manual_decision"] for row in rows} == {
        "accept_for_future_struct_conn_crosscheck",
        "pending_manual_review",
    }
    assert manifest["decision_input_csv_json_consistent"] is True


def test_accepted_rows_are_step14n_future_crosscheck_not_ready() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_manual_review_decision_input.csv")
    accepted = [row for row in rows if row["user_manual_decision"] == "accept_for_future_struct_conn_crosscheck"]
    assert {row["candidate_source_stage"] for row in accepted} == {"step14n_next_batch_metadata_acquisition"}
    assert {row["struct_conn_evidence_status"] for row in accepted} == {
        "pending_future_raw_mmcif_struct_conn_crosscheck"
    }
    assert {row["covpdb_residue_name"] for row in accepted} == {"CYS"}
    assert {row["ready_candidate_current_step"] for row in accepted} == {"False"}
    assert {row["ready_for_training_current_step"] for row in accepted} == {"False"}
    assert all(row["user_decision_reason"] for row in accepted)


def test_no_reject_needs_more_evidence_ready_or_training_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_manual_review_decision_input.csv")
    manifest = _manifest()
    assert not [row for row in rows if row["user_manual_decision"] == "reject"]
    assert not [row for row in rows if row["user_manual_decision"] == "needs_more_evidence"]
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["rejected_candidate_count_current_step"] == 0
    assert manifest["needs_more_evidence_count_current_step"] == 0
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True


def test_accepted_crosscheck_manifest_contract() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_accept_for_future_struct_conn_crosscheck_manifest.csv")
    rows_json = json.loads(
        (ROOT / "covapie_cys_sg_accept_for_future_struct_conn_crosscheck_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["accepted_crosscheck_manifest_row_count"] == 5
    assert [row["manual_review_candidate_id"] for row in rows] == EXPECTED_ACCEPTED_IDS
    assert [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    assert [row["accepted_crosscheck_candidate_id"] for row in rows] == [
        f"CYS_SG_ACCEPT_CROSSCHECK_{idx:06d}" for idx in range(1, 6)
    ]
    assert {row["user_manual_decision"] for row in rows} == {"accept_for_future_struct_conn_crosscheck"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert {row["next_required_gate"] for row in rows} == {
        "covapie_cys_sg_future_struct_conn_crosscheck_gate"
    }
    assert manifest["accepted_crosscheck_manifest_csv_json_consistent"] is True


def test_diff_policy_downstream_and_readiness_boundaries() -> None:
    diff = _csv_rows(ROOT / "covapie_cys_sg_manual_review_decision_diff_audit.csv")
    policy = _csv_rows(ROOT / "covapie_cys_sg_decision_input_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_decision_input_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert {row["decision_diff_audit_passed"] for row in diff} == {"True"}
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    by_diff = {row["decision_diff_item"]: row["decision_diff_value"] for row in diff}
    assert by_diff["accepted_for_future_struct_conn_crosscheck_count"] == "5"
    assert by_diff["pending_manual_review_count"] == "20"
    assert by_diff["ready_candidate_count_current_step"] == "0"
    assert by_diff["training_candidate_count_current_step"] == "0"
    assert manifest["ready_for_covapie_cys_sg_manual_review_decision_application_gate"] is True
    assert manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_manual_review_decision_application_gate"


def test_safety_no_network_raw_training_artifacts_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_decision_input_safety_audit.csv")
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
    for root in [decision_input.RAW_OUTPUT_ROOT, decision_input.RAW_REFERENCE_ROOT]:
        tracked = subprocess.run(["git", "ls-files", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not tracked
        assert not staged
    for name in [
        "requests",
        "urllib",
        "torch",
        "numpy",
        "rdkit",
        "Bio",
        "gemmi",
        "gzip",
        "selenium",
        "playwright",
        "bs4",
    ]:
        assert not _imports_name(
            Path("src/covalent_ext/covapie_cys_sg_manual_review_decision_input_by_user.py"), name
        )
        assert not _imports_name(
            Path("scripts/check_covapie_cys_sg_manual_review_decision_input_by_user_v0.py"), name
        )


def test_canonical_masks_and_training_blockers_preserved() -> None:
    manifest = _manifest()
    assert manifest["canonical_mask_task_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert manifest["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert manifest["accepted_candidate_ids"] == EXPECTED_ACCEPTED_IDS
    assert manifest["accepted_pdb_het_pairs"] == EXPECTED_ACCEPTED_PAIRS
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
