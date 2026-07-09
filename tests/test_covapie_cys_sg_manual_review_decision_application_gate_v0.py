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

from covalent_ext import covapie_cys_sg_manual_review_decision_application_gate as gate
from covalent_ext import covapie_cys_sg_manual_review_decision_input_by_user as step14p


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_manual_review_decision_application_gate_v0")
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
    path = ROOT / "covapie_cys_sg_manual_review_decision_application_gate_manifest.json"
    assert path.is_file(), "Run the Step 14Q check script before artifact tests"
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


def test_step14p_precondition_and_manifest_contract() -> None:
    step14p_manifest = json.loads(step14p.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_decision_application_precondition_audit.csv")
    manifest = _manifest()
    assert step14p_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14p_manifest["all_checks_passed"] is True
    assert step14p_manifest["input_manual_review_candidate_count"] == 25
    assert step14p_manifest["accepted_for_future_struct_conn_crosscheck_count"] == 5
    assert step14p_manifest["pending_manual_review_count"] == 20
    assert step14p_manifest["ready_for_covapie_cys_sg_manual_review_decision_application_gate"] is True
    assert step14p_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14Q"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_applied_decisions_have_25_rows_and_exact_five_accepted() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_applied_manual_review_decisions.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_applied_manual_review_decisions.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["input_manual_review_candidate_count"] == 25
    assert [row["manual_review_candidate_id"] for row in rows] == [
        row["manual_review_candidate_id"] for row in rows_json
    ]
    accepted = [row for row in rows if row["applied_decision"] == "accepted_for_future_struct_conn_crosscheck"]
    pending = [row for row in rows if row["applied_decision"] == "pending_manual_review"]
    assert len(accepted) == manifest["applied_accept_for_future_struct_conn_crosscheck_count"] == 5
    assert len(pending) == manifest["applied_pending_manual_review_count"] == 20
    assert [row["manual_review_candidate_id"] for row in accepted] == EXPECTED_ACCEPTED_IDS
    assert [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in accepted] == EXPECTED_ACCEPTED_PAIRS
    assert {row["user_manual_decision"] for row in accepted} == {"accept_for_future_struct_conn_crosscheck"}
    assert {row["application_status"] for row in accepted} == {"applied_to_future_struct_conn_crosscheck_input"}
    assert {row["application_status"] for row in pending} == {"kept_pending_manual_review"}


def test_future_struct_conn_crosscheck_input_manifest_has_exact_five_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_input_manifest.csv")
    rows_json = json.loads(
        (ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_input_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["future_struct_conn_crosscheck_input_count"] == 5
    assert [row["manual_review_candidate_id"] for row in rows] == EXPECTED_ACCEPTED_IDS
    assert [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    assert [row["crosscheck_input_id"] for row in rows] == [
        f"CYS_SG_STRUCT_CONN_CROSSCHECK_INPUT_{idx:06d}" for idx in range(1, 6)
    ]
    assert {row["struct_conn_evidence_status"] for row in rows} == {
        "pending_future_raw_mmcif_struct_conn_crosscheck"
    }
    assert {row["next_required_gate"] for row in rows} == {
        "covapie_cys_sg_future_struct_conn_crosscheck_gate"
    }
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["future_struct_conn_crosscheck_input_manifest_csv_json_consistent"] is True


def test_no_ready_candidates_or_training_candidates_created() -> None:
    applied = _csv_rows(ROOT / "covapie_cys_sg_applied_manual_review_decisions.csv")
    future = _csv_rows(ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_input_manifest.csv")
    manifest = _manifest()
    assert {row["ready_candidate_current_step"] for row in applied} == {"False"}
    assert {row["ready_for_training_current_step"] for row in applied} == {"False"}
    assert {row["ready_candidate_current_step"] for row in future} == {"False"}
    assert {row["ready_for_training_current_step"] for row in future} == {"False"}
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_diff_policy_downstream_readiness_and_next_step() -> None:
    diff = _csv_rows(ROOT / "covapie_cys_sg_decision_application_diff_audit.csv")
    policy = _csv_rows(ROOT / "covapie_cys_sg_decision_application_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_decision_application_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert {row["decision_application_diff_passed"] for row in diff} == {"True"}
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    by_diff = {row["decision_application_diff_item"]: row["decision_application_diff_value"] for row in diff}
    assert by_diff["applied_accept_for_future_struct_conn_crosscheck_count"] == "5"
    assert by_diff["applied_pending_manual_review_count"] == "20"
    assert by_diff["future_struct_conn_crosscheck_input_count"] == "5"
    assert manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate"] is True
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_future_struct_conn_crosscheck_gate"


def test_safety_no_raw_training_artifacts_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_decision_application_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used",
        "download_attempted",
        "raw_mmcif_read_current_step",
        "data_raw_written_current_step",
        "html_files_written_current_step",
        "sample_download_manifest_written",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
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
            Path("src/covalent_ext/covapie_cys_sg_manual_review_decision_application_gate.py"), name
        )
        assert not _imports_name(
            Path("scripts/check_covapie_cys_sg_manual_review_decision_application_gate_v0.py"), name
        )


def test_step14p_step14o_artifacts_unchanged_and_masks_preserved() -> None:
    manifest = _manifest()
    for root in [
        "data/derived/covalent_small/covapie_cys_sg_manual_review_decision_input_by_user_v0",
        "data/derived/covalent_small/covapie_cys_sg_acquired_annotation_manual_review_gate_v0",
    ]:
        assert subprocess.run(["git", "diff", "--quiet", "--", root], check=False).returncode == 0
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
