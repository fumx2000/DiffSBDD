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

from covalent_ext import covapie_cys_sg_ready_candidate_materialization_gate as step14x
from covalent_ext import covapie_small_pilot_manifest_rerun_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_small_pilot_manifest_rerun_gate_v0")
EXPECTED_ACCEPTED_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
EXPECTED_BLOCKED_PAIRS = ["1A54/MDC", "6BV9/JUG"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_small_pilot_manifest_rerun_gate_manifest.json"
    assert path.is_file(), "Run the Step 14Y check script before artifact tests"
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


def test_step14x_precondition_and_manifest_contract() -> None:
    step14x_manifest = json.loads(step14x.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_small_pilot_manifest_rerun_precondition_audit.csv")
    manifest = _manifest()
    assert step14x_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14x_manifest["all_checks_passed"] is True
    assert step14x_manifest["ready_candidate_count_current_step"] == 3
    assert step14x_manifest["ready_for_small_pilot_manifest_count"] == 3
    assert step14x_manifest["ready_for_sample_preparation_count"] == 3
    assert step14x_manifest["ready_for_covapie_small_pilot_manifest_rerun_gate"] is True
    assert step14x_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14Y"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_small_pilot_manifest_has_three_ready_candidate_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_small_pilot_ready_candidate_manifest.csv")
    rows_json = json.loads((ROOT / "covapie_small_pilot_ready_candidate_manifest.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["small_pilot_manifest_row_count"] == 3
    assert [row["small_pilot_manifest_id"] for row in rows] == [
        "CYS_SG_SMALL_PILOT_000001",
        "CYS_SG_SMALL_PILOT_000002",
        "CYS_SG_SMALL_PILOT_000003",
    ]
    assert [row["small_pilot_manifest_id"] for row in rows] == [
        row["small_pilot_manifest_id"] for row in rows_json
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["ligand_atom_name"] for row in rows} == {"CAG"}
    assert {row["covalent_bond_atom_pair"] for row in rows} == {"SG--CAG"}
    assert {row["conn_type_id"] for row in rows} == {"covale"}
    assert {row["small_pilot_entry_status"] for row in rows} == {
        "ready_candidate_selected_for_small_pilot"
    }
    assert {row["sample_preparation_status"] for row in rows} == {
        "pending_sample_preparation_design"
    }
    assert manifest["small_pilot_manifest_csv_json_consistent"] is True


def test_small_pilot_manifest_is_for_sample_preparation_not_training() -> None:
    rows = _csv_rows(ROOT / "covapie_small_pilot_ready_candidate_manifest.csv")
    manifest = _manifest()
    assert {row["ready_for_sample_preparation"] for row in rows} == {"True"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert {row["feature_semantics_audit_required_before_training"] for row in rows} == {"True"}
    assert {row["leakage_split_design_required_before_training"] for row in rows} == {"True"}
    assert manifest["ready_for_sample_preparation_count"] == 3
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_traceability_audit_complete() -> None:
    rows = _csv_rows(ROOT / "covapie_small_pilot_manifest_traceability_audit.csv")
    assert len(rows) == 3
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    for key in [
        "upstream_ready_candidate_present",
        "upstream_evidence_traceability_complete",
        "upstream_step14t_struct_conn_evidence_present",
        "ligand_atom_from_raw_struct_conn",
        "residue_atom_from_raw_struct_conn",
        "traceability_audit_passed",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["covalent_bond_atom_pair"] for row in rows} == {"SG--CAG"}
    assert {row["traceability_status"] for row in rows} == {
        "small_pilot_entry_has_complete_ready_candidate_chain"
    }


def test_blocked_inputs_excluded_from_small_pilot_manifest() -> None:
    rows = _csv_rows(ROOT / "covapie_small_pilot_manifest_blocked_exclusion_audit.csv")
    manifest = _manifest()
    assert len(rows) == manifest["blocked_exclusion_count"] == 2
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_BLOCKED_PAIRS
    assert {row["blocked_status_current_step"] for row in rows} == {
        "excluded_from_small_pilot_manifest"
    }
    assert {row["excluded_from_small_pilot_manifest"] for row in rows} == {"True"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["blocked_pdb_het_pairs"] == EXPECTED_BLOCKED_PAIRS


def test_diff_policy_readiness_and_masks() -> None:
    diff = _csv_rows(ROOT / "covapie_small_pilot_manifest_rerun_diff_audit.csv")
    policy = _csv_rows(ROOT / "covapie_small_pilot_manifest_rerun_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_small_pilot_manifest_rerun_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert {row["rerun_diff_passed"] for row in diff} == {"True"}
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    by_diff = {row["rerun_diff_item"]: row for row in diff}
    assert by_diff["small_pilot_manifest_row_count"]["observed_value"] == "3"
    assert by_diff["blocked_exclusion_count"]["observed_value"] == "2"
    assert by_diff["sample_index_written"]["observed_value"] == "False"
    assert by_diff["final_dataset_written"]["observed_value"] == "False"
    assert by_diff["training_artifacts_written"]["observed_value"] == "False"
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
    assert manifest["ready_for_covapie_sample_preparation_design_gate"] is True
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["recommended_next_step"] == "covapie_sample_preparation_design_gate"


def test_safety_no_sample_final_raw_model_training_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_small_pilot_manifest_rerun_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) == 20
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used_current_step",
        "download_attempted_current_step",
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "data_raw_written_current_step",
        "html_files_written_current_step",
        "part_files_leftover_current_step",
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
        assert not _imports_name(Path("src/covalent_ext/covapie_small_pilot_manifest_rerun_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_small_pilot_manifest_rerun_gate_v0.py"), name)


def test_training_blockers_remain_in_force() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
