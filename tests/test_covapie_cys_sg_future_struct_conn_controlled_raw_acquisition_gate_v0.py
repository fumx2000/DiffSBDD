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

from covalent_ext import covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate as gate
from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_gate as step14r


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate_v0")
RAW_ROOT = Path("data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0")
EXPECTED_PAIRS = ["1A54/MDC", "6BV6/JUG", "6BV9/JUG", "6BV8/JUG", "6BV5/JUG"]
EXPECTED_RAW_FILES = ["1a54.cif", "6bv6.cif", "6bv9.cif", "6bv8.cif", "6bv5.cif"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_manifest.json"
    assert path.is_file(), "Run the Step 14S check script before artifact tests"
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


def test_step14r_precondition_and_manifest_contract() -> None:
    step14r_manifest = json.loads(step14r.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_acquisition_precondition_audit.csv")
    manifest = _manifest()
    assert step14r_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14r_manifest["all_checks_passed"] is True
    assert step14r_manifest["future_struct_conn_crosscheck_input_count"] == 5
    assert step14r_manifest["expected_raw_mmcif_acquisition_plan_count"] == 5
    assert step14r_manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate"] is True
    assert step14r_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14S"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_request_manifest_count_pairs_urls_and_json_consistency() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_acquisition_request_manifest.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_controlled_raw_acquisition_request_manifest.json").read_text(encoding="utf-8"))
    assert len(rows) == len(rows_json) == 5
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert [row["expected_raw_filename"] for row in rows] == EXPECTED_RAW_FILES
    assert [row["rcsb_mmcif_url"] for row in rows] == [
        f"https://files.rcsb.org/download/{pair.split('/')[0]}.cif" for pair in EXPECTED_PAIRS
    ]
    assert {row["download_or_reuse_policy"] for row in rows} == {
        "download_if_missing_else_reuse_existing_raw"
    }
    assert {row["request_scope"] for row in rows} == {"raw_mmcif_acquisition_only_no_struct_conn_parse"}
    assert {row["request_contract_passed"] for row in rows} == {"True"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}


def test_execution_and_integrity_audits_have_five_valid_raw_files() -> None:
    execution = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_acquisition_execution_audit.csv")
    integrity = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_file_integrity_audit.csv")
    manifest = _manifest()
    assert len(execution) == len(integrity) == 5
    assert {row["acquisition_status"] for row in execution} == {"success"}
    assert {row["raw_file_exists_after_step"] for row in execution} == {"True"}
    assert {row["html_detected"] for row in execution} == {"False"}
    assert {row["part_file_leftover"] for row in execution} == {"False"}
    assert {row["execution_audit_passed"] for row in execution} == {"True"}
    assert {row["starts_with_data_block"] for row in integrity} == {"True"}
    assert {row["html_or_error_page_detected"] for row in integrity} == {"False"}
    assert {row["struct_conn_parsed_current_step"] for row in integrity} == {"False"}
    assert {row["integrity_audit_passed"] for row in integrity} == {"True"}
    for row in execution:
        assert int(row["raw_file_size_bytes"]) > 0
        assert len(row["raw_file_sha256"]) == 64
    assert manifest["raw_mmcif_expected_count"] == 5
    assert manifest["raw_mmcif_available_count"] == 5
    assert manifest["raw_mmcif_integrity_passed_count"] == 5
    assert manifest["raw_acquisition_success_count"] == 5
    assert manifest["raw_downloaded_current_run_count"] + manifest["raw_reused_existing_count"] == 5
    assert manifest["struct_conn_parsed_current_step"] is False


def test_raw_files_exist_but_are_not_tracked_or_staged() -> None:
    availability = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_file_availability_manifest.csv")
    assert len(availability) == 5
    assert {row["raw_file_available"] for row in availability} == {"True"}
    assert {row["git_tracked"] for row in availability} == {"False"}
    assert {row["git_staged"] for row in availability} == {"False"}
    assert {row["available_for_future_struct_conn_parse"] for row in availability} == {"True"}
    assert {row["ready_candidate_current_step"] for row in availability} == {"False"}
    assert {row["ready_for_training_current_step"] for row in availability} == {"False"}
    for name in EXPECTED_RAW_FILES:
        path = RAW_ROOT / name
        assert path.is_file()
        assert path.stat().st_size > 0
    tracked = subprocess.run(["git", "ls-files", RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not tracked
    assert not staged


def test_policy_downstream_and_training_boundaries() -> None:
    policy = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_acquisition_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_acquisition_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(policy) == 12
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate"] is True
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate"


def test_safety_no_struct_conn_parse_ready_candidates_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_controlled_raw_acquisition_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "raw_mmcif_content_parsed_current_step",
        "struct_conn_parsed_current_step",
        "html_files_written_current_step",
        "part_files_leftover_current_step",
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
        "selenium_used",
        "playwright_used",
        "bs4_used",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True
    for name in [
        "requests",
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
            Path("src/covalent_ext/covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate.py"),
            name,
        )
        assert not _imports_name(
            Path("scripts/check_covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_v0.py"),
            name,
        )


def test_no_forbidden_derived_artifacts_and_no_raw_leftovers() -> None:
    forbidden_suffix = {
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".pdb",
        ".cif",
        ".mmcif",
        ".sdf",
        ".mol2",
        ".gz",
        ".html",
        ".htm",
        ".part",
    }
    bad_derived = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in forbidden_suffix]
    bad_raw = [p for p in RAW_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in {".part", ".html", ".htm"}]
    assert not bad_derived
    assert not bad_raw


def test_step14r_step14q_step14p_artifacts_unchanged_and_masks_preserved() -> None:
    manifest = _manifest()
    for root in [
        "data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_manual_review_decision_application_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_manual_review_decision_input_by_user_v0",
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
