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

from covalent_ext import covapie_cys_sg_result_review_decision_input_by_user as gate
from covalent_ext import covapie_cys_sg_struct_conn_crosscheck_result_review_gate as step14u


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_result_review_decision_input_by_user_v0")
EXPECTED_ACCEPTED_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
EXPECTED_BLOCKED = {
    "1A54/MDC": "no_struct_conn_loop_found",
    "6BV9/JUG": "ligand_comp_id_mismatch",
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_result_review_decision_input_by_user_manifest.json"
    assert path.is_file(), "Run the Step 14V check script before artifact tests"
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


def test_step14u_precondition_and_manifest_contract() -> None:
    step14u_manifest = json.loads(step14u.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_result_review_decision_input_precondition_audit.csv")
    manifest = _manifest()
    assert step14u_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14u_manifest["all_checks_passed"] is True
    assert step14u_manifest["result_review_evidence_count"] == 3
    assert step14u_manifest["unmatched_blocked_count"] == 2
    assert step14u_manifest["pending_result_review_count"] == 3
    assert step14u_manifest["ready_for_covapie_cys_sg_result_review_decision_input_by_user"] is True
    assert step14u_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14V"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_decision_input_accepts_three_result_review_rows_without_ready_candidates() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_result_review_decision_input.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_result_review_decision_input.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["input_result_review_evidence_count"] == 3
    assert [row["result_review_evidence_id"] for row in rows] == [
        "CYS_SG_RESULT_REVIEW_EVIDENCE_000001",
        "CYS_SG_RESULT_REVIEW_EVIDENCE_000002",
        "CYS_SG_RESULT_REVIEW_EVIDENCE_000003",
    ]
    assert [row["result_review_evidence_id"] for row in rows] == [
        row["result_review_evidence_id"] for row in rows_json
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    assert {row["previous_result_review_decision"] for row in rows} == {"pending_result_review"}
    assert {row["user_result_review_decision"] for row in rows} == {
        "accept_for_future_ready_candidate_materialization"
    }
    assert {row["user_result_review_reason"] for row in rows} == {
        "user_accepted_raw_struct_conn_cys_sg_ligand_evidence_for_future_ready_candidate_materialization"
    }
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["ligand_comp_id"] for row in rows} == {"JUG"}
    assert {row["ligand_atom_name"] for row in rows} == {"CAG"}
    assert {row["conn_type_id"] for row in rows} == {"covale"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["decision_input_csv_json_consistent"] is True
    assert manifest["user_accepted_for_future_ready_candidate_materialization_count"] == 3


def test_future_ready_materialization_manifest_is_not_ready_materialization() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_accept_for_future_ready_candidate_materialization_manifest.csv")
    rows_json = json.loads(
        (ROOT / "covapie_cys_sg_accept_for_future_ready_candidate_materialization_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["future_ready_materialization_input_count"] == 3
    assert [row["future_ready_materialization_input_id"] for row in rows] == [
        "CYS_SG_FUTURE_READY_MATERIALIZATION_INPUT_000001",
        "CYS_SG_FUTURE_READY_MATERIALIZATION_INPUT_000002",
        "CYS_SG_FUTURE_READY_MATERIALIZATION_INPUT_000003",
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    assert {row["user_result_review_decision"] for row in rows} == {
        "accept_for_future_ready_candidate_materialization"
    }
    assert {row["next_required_gate"] for row in rows} == {
        "covapie_cys_sg_result_review_decision_application_gate"
    }
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["future_ready_materialization_manifest_csv_json_consistent"] is True
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True


def test_blocked_carry_forward_rows_remain_blocked() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_result_review_blocked_carry_forward_manifest.csv")
    manifest = _manifest()
    assert len(rows) == manifest["blocked_carry_forward_count"] == 2
    by_pair = {f"{row['pdb_id']}/{row['expected_het_id']}": row for row in rows}
    assert {pair: row["crosscheck_status"] for pair, row in by_pair.items()} == EXPECTED_BLOCKED
    assert {pair: row["blocking_reason"] for pair, row in by_pair.items()} == EXPECTED_BLOCKED
    assert {row["carry_forward_policy"] for row in rows} == {"do_not_use_as_ready_candidate_current_step"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["blocked_pdb_het_pairs"] == list(EXPECTED_BLOCKED)


def test_diff_policy_masks_and_readiness_boundaries() -> None:
    diff = _csv_rows(ROOT / "covapie_cys_sg_result_review_decision_diff_audit.csv")
    policy = _csv_rows(ROOT / "covapie_cys_sg_result_review_decision_policy_contract.csv")
    manifest = _manifest()
    assert {row["decision_diff_passed"] for row in diff} == {"True"}
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    by_diff = {row["decision_diff_item"]: row for row in diff}
    assert by_diff["input_result_review_template_row_count"]["observed_value"] == "3"
    assert by_diff["decision_input_row_count"]["observed_value"] == "3"
    assert by_diff["accepted_for_future_ready_candidate_materialization_count"]["observed_value"] == "3"
    assert by_diff["pending_result_review_count"]["observed_value"] == "0"
    assert by_diff["ready_candidate_count_current_step"]["observed_value"] == "0"
    assert by_diff["ready_for_training_candidate_count_current_step"]["observed_value"] == "0"
    assert manifest["accepted_pdb_het_pairs"] == EXPECTED_ACCEPTED_PAIRS
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
    assert manifest["ready_for_covapie_cys_sg_result_review_decision_application_gate"] is True
    assert manifest["ready_for_covapie_cys_sg_ready_candidate_materialization_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_result_review_decision_application_gate"


def test_safety_no_raw_struct_conn_model_training_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_result_review_decision_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) == 18
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used_current_step",
        "download_attempted_current_step",
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "data_raw_written_current_step",
        "sample_index_written_current_step",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
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
    tracked = subprocess.run(["git", "ls-files", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
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
            Path("src/covalent_ext/covapie_cys_sg_result_review_decision_input_by_user.py"), name
        )
        assert not _imports_name(
            Path("scripts/check_covapie_cys_sg_result_review_decision_input_by_user_v0.py"), name
        )


def test_training_blockers_remain_in_force() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
