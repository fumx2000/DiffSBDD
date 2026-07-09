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

from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_gate as gate
from covalent_ext import covapie_cys_sg_manual_review_decision_application_gate as step14q


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_gate_v0")
EXPECTED_PAIRS = ["1A54/MDC", "6BV6/JUG", "6BV9/JUG", "6BV8/JUG", "6BV5/JUG"]
REQUIRED_STRUCT_CONN_FIELDS = {
    "_struct_conn.conn_type_id",
    "_struct_conn.ptnr1_label_comp_id",
    "_struct_conn.ptnr1_label_atom_id",
    "_struct_conn.ptnr1_auth_asym_id",
    "_struct_conn.ptnr1_auth_seq_id",
    "_struct_conn.ptnr2_label_comp_id",
    "_struct_conn.ptnr2_label_atom_id",
    "_struct_conn.ptnr2_auth_asym_id",
    "_struct_conn.ptnr2_auth_seq_id",
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_gate_manifest.json"
    assert path.is_file(), "Run the Step 14R check script before artifact tests"
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


def test_step14q_precondition_and_manifest_contract() -> None:
    step14q_manifest = json.loads(step14q.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_future_crosscheck_precondition_audit.csv")
    manifest = _manifest()
    assert step14q_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14q_manifest["all_checks_passed"] is True
    assert step14q_manifest["future_struct_conn_crosscheck_input_count"] == 5
    assert step14q_manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_gate"] is True
    assert step14q_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14R"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_future_crosscheck_input_contract_count_pairs_and_not_ready() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_future_crosscheck_input_contract.csv")
    manifest = _manifest()
    assert len(rows) == manifest["future_struct_conn_crosscheck_input_count"] == 5
    assert [f"{row['pdb_id']}/{row['suggested_ligand_comp_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["covpdb_residue_name"] for row in rows} == {"CYS"}
    assert {row["expected_residue_atom_name"] for row in rows} == {"SG"}
    assert {row["crosscheck_scope"] for row in rows} == {"metadata_to_raw_mmcif_struct_conn_evidence"}
    assert {row["ready_candidate_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert {row["input_contract_passed"] for row in rows} == {"True"}


def test_expected_struct_conn_query_plan_count_and_contract() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_expected_struct_conn_query_plan.csv")
    rows_json = json.loads((ROOT / "covapie_cys_sg_expected_struct_conn_query_plan.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["expected_struct_conn_query_plan_count"] == 5
    assert [row["struct_conn_query_id"] for row in rows] == [
        f"CYS_SG_STRUCT_CONN_QUERY_{idx:06d}" for idx in range(1, 6)
    ]
    assert [f"{row['pdb_id']}/{row['ligand_comp_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["residue_name"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["expected_partner_order_policy"] for row in rows} == {"search_both_partner_orders"}
    assert {row["expected_conn_type_policy"] for row in rows} == {
        "prefer_covale_allow_review_if_equivalent"
    }
    assert {row["ligand_atom_name_expected_current_step"] for row in rows} == {
        "unknown_until_raw_struct_conn_parse"
    }
    assert {row["residue_atom_name_expected_current_step"] for row in rows} == {"SG"}
    for row in rows:
        assert REQUIRED_STRUCT_CONN_FIELDS <= set(row["required_struct_conn_fields"].split(";"))
    assert {row["query_plan_passed"] for row in rows} == {"True"}


def test_raw_mmcif_acquisition_plan_is_future_only() -> None:
    rows = _csv_rows(ROOT / "covapie_cys_sg_expected_raw_mmcif_acquisition_plan.csv")
    manifest = _manifest()
    assert len(rows) == manifest["expected_raw_mmcif_acquisition_plan_count"] == 5
    assert [f"{row['pdb_id']}/{Path(row['expected_raw_filename']).stem.upper()}" for row in rows] == [
        "1A54/1A54",
        "6BV6/6BV6",
        "6BV9/6BV9",
        "6BV8/6BV8",
        "6BV5/6BV5",
    ]
    assert {row["raw_download_required_future_step"] for row in rows} == {"True"}
    assert {row["raw_downloaded_current_step"] for row in rows} == {"False"}
    assert {row["raw_file_read_current_step"] for row in rows} == {"False"}
    assert {row["acquisition_method_future_step"] for row in rows} == {
        "controlled_rcsb_mmcif_download_or_existing_raw_reuse"
    }
    assert {row["acquisition_plan_passed"] for row in rows} == {"True"}
    assert manifest["raw_downloaded_current_step"] is False
    assert manifest["raw_mmcif_read_current_step"] is False
    assert manifest["struct_conn_parsed_current_step"] is False


def test_acceptance_and_blocking_contracts_are_not_evaluated_current_step() -> None:
    acceptance = _csv_rows(ROOT / "covapie_cys_sg_crosscheck_evidence_acceptance_contract.csv")
    blocking = _csv_rows(ROOT / "covapie_cys_sg_crosscheck_blocking_reasons_contract.csv")
    assert len(acceptance) == 12
    assert {row["current_step_status"] for row in acceptance} == {"contract_only_not_evaluated"}
    assert {row["required_before_dataset_ready"] for row in acceptance} == {"True"}
    assert {row["required_before_training"] for row in acceptance} == {"True"}
    assert {row["acceptance_contract_passed"] for row in acceptance} == {"True"}
    assert len(blocking) == 10
    assert {row["blocking_contract_passed"] for row in blocking} == {"True"}
    assert {
        "missing_raw_mmcif",
        "missing_struct_conn_category",
        "no_cys_sg_ligand_match",
        "metadata_raw_event_identity_conflict",
    } <= {row["blocking_reason"] for row in blocking}


def test_downstream_readiness_boundaries() -> None:
    downstream = _csv_rows(ROOT / "covapie_cys_sg_future_crosscheck_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate"] is True
    assert manifest["ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate"] is False
    assert manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_acquisition_gate"


def test_safety_no_raw_training_artifacts_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_future_crosscheck_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used",
        "download_attempted",
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
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_future_struct_conn_crosscheck_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_future_struct_conn_crosscheck_gate_v0.py"), name)


def test_step14q_step14p_step14o_artifacts_unchanged_and_masks_preserved() -> None:
    manifest = _manifest()
    for root in [
        "data/derived/covalent_small/covapie_cys_sg_manual_review_decision_application_gate_v0",
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
