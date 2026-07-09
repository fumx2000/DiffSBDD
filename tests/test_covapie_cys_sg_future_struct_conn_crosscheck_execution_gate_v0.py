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

from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_execution_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0")
RAW_ROOT = Path("data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0")
EXPECTED_PAIRS = ["1A54/MDC", "6BV6/JUG", "6BV9/JUG", "6BV8/JUG", "6BV5/JUG"]
ALLOWED_STATUSES = {
    "matched_cys_sg_ligand_struct_conn",
    "ambiguous_multiple_cys_sg_ligand_struct_conn_matches",
    "no_struct_conn_loop_found",
    "no_cys_sg_ligand_match",
    "chain_or_residue_index_conflict",
    "ligand_comp_id_mismatch",
    "raw_parse_error",
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_manifest.json"
    assert path.is_file(), "Run the Step 14T check script before artifact tests"
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


def test_stdlib_struct_conn_parser_extracts_synthetic_loop_and_matches_both_orders() -> None:
    html = """data_TEST
#
loop_
_struct_conn.id
_struct_conn.conn_type_id
_struct_conn.ptnr1_label_asym_id
_struct_conn.ptnr1_label_comp_id
_struct_conn.ptnr1_label_seq_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr2_label_asym_id
_struct_conn.ptnr2_label_comp_id
_struct_conn.ptnr2_label_seq_id
_struct_conn.ptnr2_label_atom_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_seq_id
covale1 covale B JUG . CAG A 601 A CYS 275 SG A 346
#
"""
    tags, records, status, error = gate.parse_struct_conn_loop(html)
    assert status == "parsed_struct_conn_loop"
    assert error == ""
    assert "_struct_conn.ptnr2_label_atom_id" in tags
    assert len(records) == 1
    query = {
        "ligand_comp_id": "JUG",
        "residue_chain_id": "A",
        "residue_index": "346",
    }
    matches, crosscheck_status, blocking, _ = gate.match_struct_conn_records(query, records)
    assert crosscheck_status == "matched_cys_sg_ligand_struct_conn"
    assert blocking == ""
    assert matches[0]["residue"]["side"] == "ptnr2"
    assert matches[0]["ligand"]["atom_id"] == "CAG"


def test_step14s_precondition_and_manifest_contract() -> None:
    step14s_manifest = json.loads(gate.STEP14S_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_execution_precondition_audit.csv")
    manifest = _manifest()
    assert step14s_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14s_manifest["all_checks_passed"] is True
    assert step14s_manifest["raw_mmcif_available_count"] == 5
    assert step14s_manifest["raw_mmcif_integrity_passed_count"] == 5
    assert step14s_manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14T"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_raw_mmcif_read_parse_audit_counts_and_statuses() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_raw_struct_conn_parse_audit.csv")
    manifest = _manifest()
    assert len(rows) == 5
    assert [row["pdb_id"] for row in rows] == ["1A54", "6BV6", "6BV9", "6BV8", "6BV5"]
    assert {row["raw_file_exists"] for row in rows} == {"True"}
    assert {row["raw_mmcif_read_current_step"] for row in rows} == {"True"}
    assert {row["struct_conn_parsed_current_step"] for row in rows} == {"True"}
    assert {row["parse_audit_passed"] for row in rows} == {"True"}
    assert {row["parser_status"] for row in rows}.issubset({"parsed_struct_conn_loop", "no_struct_conn_loop_found"})
    for row in rows:
        assert int(row["raw_file_size_bytes"]) > 0
        assert len(row["raw_file_sha256"]) == 64
        assert row["first_nonempty_line"].startswith("data_")
    assert manifest["raw_mmcif_read_count"] == 5
    assert manifest["struct_conn_parse_attempt_count"] == 5
    assert manifest["struct_conn_parse_success_count"] == 5
    assert manifest["struct_conn_parsed_current_step"] is True


def test_query_execution_audit_exact_pairs_statuses_and_no_ready_candidates() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_query_execution_audit.csv")
    manifest = _manifest()
    assert len(rows) == 5
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["expected_residue_name"] for row in rows} == {"CYS"}
    assert {row["expected_residue_atom_name"] for row in rows} == {"SG"}
    assert {row["crosscheck_status"] for row in rows}.issubset(ALLOWED_STATUSES)
    by_pair = {f"{row['pdb_id']}/{row['expected_het_id']}": row for row in rows}
    assert by_pair["1A54/MDC"]["crosscheck_status"] == "no_struct_conn_loop_found"
    assert by_pair["6BV6/JUG"]["crosscheck_status"] == "matched_cys_sg_ligand_struct_conn"
    assert by_pair["6BV9/JUG"]["crosscheck_status"] == "ligand_comp_id_mismatch"
    assert by_pair["6BV8/JUG"]["crosscheck_status"] == "matched_cys_sg_ligand_struct_conn"
    assert by_pair["6BV5/JUG"]["crosscheck_status"] == "matched_cys_sg_ligand_struct_conn"
    assert {row["query_execution_passed"] for row in rows} == {"True"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["matched_input_count"] == 3
    assert manifest["unmatched_input_count"] == 2
    assert manifest["ambiguous_input_count"] == 0


def test_matched_evidence_candidates_csv_json_consistent_and_not_ready() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_matched_evidence_candidates.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_struct_conn_matched_evidence_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == 3
    assert [row["struct_conn_evidence_candidate_id"] for row in rows] == [
        row["struct_conn_evidence_candidate_id"] for row in rows_json
    ]
    assert {row["pdb_id"] for row in rows} == {"6BV6", "6BV8", "6BV5"}
    assert {row["ligand_comp_id"] for row in rows} == {"JUG"}
    assert {row["ligand_atom_name"] for row in rows} == {"CAG"}
    assert {row["residue_comp_id"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["evidence_status"] for row in rows} == {"struct_conn_match_found_pending_manual_review"}
    assert {row["next_required_gate"] for row in rows} == {
        "covapie_cys_sg_struct_conn_crosscheck_result_review_gate"
    }
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["evidence_candidate_count"] == 3
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True


def test_result_summary_downstream_masks_and_training_boundaries() -> None:
    summary = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_crosscheck_result_summary.csv")
    downstream = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_crosscheck_downstream_readiness_contract.csv")
    policy = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_crosscheck_policy_contract.csv")
    manifest = _manifest()
    assert len(summary) == 1
    row = summary[0]
    assert row["crosscheck_input_count"] == "5"
    assert row["raw_mmcif_read_count"] == "5"
    assert row["evidence_candidate_count"] == "3"
    assert row["ready_for_result_review_gate"] == "True"
    assert row["ready_for_training"] == "False"
    assert row["recommended_next_step"] == "covapie_cys_sg_struct_conn_crosscheck_result_review_gate"
    assert len(policy) == 12
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate"] is True
    assert manifest["ready_for_covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
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


def test_safety_raw_files_untracked_no_network_no_forbidden_imports_or_artifacts() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_crosscheck_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) == 18
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used_current_step",
        "download_attempted_current_step",
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
    tracked = subprocess.run(["git", "ls-files", RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not tracked
    assert not staged
    forbidden_names = [
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
    ]
    for name in forbidden_names:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_future_struct_conn_crosscheck_execution_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0.py"), name)


def test_no_forbidden_derived_artifacts_and_upstream_diffs() -> None:
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
