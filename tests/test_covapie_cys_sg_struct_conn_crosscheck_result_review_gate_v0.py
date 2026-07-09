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

from covalent_ext import covapie_cys_sg_struct_conn_crosscheck_result_review_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0")
RAW_ROOT = Path("data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0")
EXPECTED_MATCHED = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
EXPECTED_BLOCKED = {
    "1A54/MDC": "no_struct_conn_loop_found",
    "6BV9/JUG": "ligand_comp_id_mismatch",
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_struct_conn_crosscheck_result_review_gate_manifest.json"
    assert path.is_file(), "Run the Step 14U check script before artifact tests"
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


def test_step14t_precondition_and_manifest_contract() -> None:
    step14t_manifest = json.loads(gate.STEP14T_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_result_review_precondition_audit.csv")
    manifest = _manifest()
    assert step14t_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14t_manifest["all_checks_passed"] is True
    assert step14t_manifest["crosscheck_input_count"] == 5
    assert step14t_manifest["matched_input_count"] == 3
    assert step14t_manifest["unmatched_input_count"] == 2
    assert step14t_manifest["evidence_candidate_count"] == 3
    assert step14t_manifest["ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14U"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_evidence_inventory_row_count_pairs_and_csv_json_consistency() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_result_review_evidence_inventory.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_result_review_evidence_inventory.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == 3
    assert [row["result_review_evidence_id"] for row in rows] == [
        row["result_review_evidence_id"] for row in rows_json
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_MATCHED
    assert {row["expected_het_id"] for row in rows} == {"JUG"}
    assert {row["residue_comp_id"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["ligand_comp_id"] for row in rows} == {"JUG"}
    assert {row["ligand_atom_name"] for row in rows} == {"CAG"}
    assert {row["conn_type_id"] for row in rows} == {"covale"}
    assert {row["evidence_status_from_step14t"] for row in rows} == {
        "struct_conn_match_found_pending_manual_review"
    }
    assert {row["result_review_status"] for row in rows} == {"pending_result_review"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert {row["inventory_row_passed"] for row in rows} == {"True"}
    assert manifest["result_review_evidence_count"] == 3
    assert manifest["matched_pdb_het_pairs"] == EXPECTED_MATCHED
    assert manifest["result_review_template_csv_json_consistent"] is True


def test_unmatched_blocked_inventory_expected_statuses() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_result_review_unmatched_blocked_inventory.csv")
    manifest = _manifest()
    assert len(rows) == 2
    by_pair = {f"{row['pdb_id']}/{row['expected_het_id']}": row for row in rows}
    assert {pair: row["crosscheck_status"] for pair, row in by_pair.items()} == EXPECTED_BLOCKED
    assert {row["blocked_status"] for row in rows} == {"blocked_pending_manual_or_evidence_review"}
    assert {row["carry_forward_policy"] for row in rows} == {
        "do_not_use_as_ready_candidate_current_step"
    }
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["unmatched_blocked_count"] == 2
    assert manifest["blocked_pdb_het_pairs"] == list(EXPECTED_BLOCKED)


def test_decision_template_pending_only_and_csv_json_consistent() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_result_review_decision_template.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_result_review_decision_template.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    allowed = {
        "pending_result_review",
        "accept_for_future_ready_candidate_materialization",
        "reject",
        "needs_more_evidence",
    }
    assert len(rows) == len(rows_json) == 3
    assert [row["result_review_evidence_id"] for row in rows] == [
        row["result_review_evidence_id"] for row in rows_json
    ]
    assert {row["result_review_decision"] for row in rows} == {"pending_result_review"}
    assert all(set(row["result_review_allowed_values"].split(";")) == allowed for row in rows)
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["result_review_template_row_count"] == 3
    assert manifest["pending_result_review_count"] == 3
    assert manifest["accepted_for_future_ready_candidate_materialization_count_current_step"] == 0
    assert manifest["rejected_result_review_count_current_step"] == 0
    assert manifest["needs_more_evidence_count_current_step"] == 0


def test_policy_downstream_masks_and_training_boundaries() -> None:
    policy = _csv_rows(ROOT / "covapie_cys_sg_result_review_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_result_review_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(policy) == 12
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_covapie_cys_sg_result_review_decision_input_by_user"] is True
    assert manifest["ready_for_covapie_cys_sg_ready_candidate_materialization_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_result_review_decision_input_by_user"
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


def test_no_ready_candidates_raw_read_network_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_result_review_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) == 18
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used_current_step",
        "download_attempted_current_step",
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "data_raw_written_current_step",
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
        "urllib_used",
        "selenium_used",
        "playwright_used",
        "bs4_used",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True
    tracked = subprocess.run(["git", "ls-files", RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
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
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_struct_conn_crosscheck_result_review_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0.py"), name)


def test_no_forbidden_artifacts_and_upstream_diffs() -> None:
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
    forbidden_names = {
        "small_pilot_download_manifest.csv",
        "small_pilot_download_manifest.json",
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "training_report.csv",
        "training_report.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
    }
    bad_suffix = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in forbidden_suffix]
    bad_names = [p for p in ROOT.rglob("*") if p.is_file() and p.name in forbidden_names]
    assert not bad_suffix
    assert not bad_names
    for root in [
        "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
        "data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_manual_review_decision_application_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_manual_review_decision_input_by_user_v0",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    ]:
        assert subprocess.run(["git", "diff", "--quiet", "--", root], check=False).returncode == 0, root
