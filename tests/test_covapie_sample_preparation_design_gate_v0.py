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

from covalent_ext import covapie_sample_preparation_design_gate as gate
from covalent_ext import covapie_small_pilot_manifest_rerun_gate as step14y


ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_design_gate_v0")
EXPECTED_ACCEPTED_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
EXPECTED_BLOCKED_PAIRS = ["1A54/MDC", "6BV9/JUG"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_preparation_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 14Z check script before artifact tests"
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


def test_step14y_precondition_and_manifest_contract() -> None:
    step14y_manifest = json.loads(step14y.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_preparation_design_precondition_audit.csv")
    manifest = _manifest()
    assert step14y_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14y_manifest["all_checks_passed"] is True
    assert step14y_manifest["small_pilot_manifest_row_count"] == 3
    assert step14y_manifest["ready_for_sample_preparation_count"] == 3
    assert step14y_manifest["ready_for_covapie_sample_preparation_design_gate"] is True
    assert step14y_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14Z"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_sample_preparation_input_manifest_three_rows_and_pairs() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_input_manifest.csv")
    rows_json = json.loads((ROOT / "covapie_sample_preparation_input_manifest.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["sample_preparation_input_count"] == 3
    assert [row["sample_preparation_input_id"] for row in rows] == [
        "CYS_SG_SAMPLE_PREP_INPUT_000001",
        "CYS_SG_SAMPLE_PREP_INPUT_000002",
        "CYS_SG_SAMPLE_PREP_INPUT_000003",
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["ligand_atom_name"] for row in rows} == {"CAG"}
    assert {row["covalent_bond_atom_pair"] for row in rows} == {"SG--CAG"}
    assert {row["conn_type_id"] for row in rows} == {"covale"}
    assert {row["sample_preparation_design_status"] for row in rows} == {
        "sample_preparation_design_ready"
    }
    assert {row["planned_sample_scope"] for row in rows} == {
        "cys_sg_struct_conn_validated_small_pilot_v0"
    }
    assert manifest["sample_preparation_input_csv_json_consistent"] is True


def test_sample_preparation_inputs_ready_for_execution_not_training() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_input_manifest.csv")
    manifest = _manifest()
    assert {row["ready_for_sample_preparation_execution_smoke"] for row in rows} == {"True"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert {row["feature_semantics_audit_required_before_training"] for row in rows} == {"True"}
    assert {row["leakage_split_design_required_before_training"] for row in rows} == {"True"}
    assert manifest["ready_for_sample_preparation_execution_smoke_count"] == 3
    assert manifest["ready_for_training_candidate_count_current_step"] == 0
    assert manifest["ready_for_covapie_sample_preparation_execution_smoke"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_required_artifact_plan_defers_actual_artifacts_to_next_step() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_required_artifact_plan.csv")
    manifest = _manifest()
    assert len(rows) == manifest["required_artifact_plan_count"] == 3
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_ACCEPTED_PAIRS
    for row in rows:
        assert row["planned_sample_artifact_root"] == (
            "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/"
            f"samples/{row['pdb_id']}_{row['expected_het_id']}"
        )
    for key in [
        "protein_atom_table_required_next_step",
        "ligand_atom_table_required_next_step",
        "pocket_atom_table_required_next_step",
        "covalent_event_table_required_next_step",
        "ligand_residue_atom_pair_required_next_step",
        "mask_annotation_design_required_later",
        "topology_restoration_policy_required_later",
        "actual_raw_mmcif_read_required_next_step",
        "actual_struct_conn_parse_allowed_next_step",
    ]:
        assert {row[key] for row in rows} == {"True"}
    assert {row["actual_sample_index_written_next_step"] for row in rows} == {"False"}
    assert {row["actual_final_dataset_written_next_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}


def test_raw_access_plan_no_current_raw_read_but_required_next_step() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_raw_access_plan.csv")
    manifest = _manifest()
    assert len(rows) == manifest["raw_access_plan_count"] == 3
    assert {row["planned_raw_source_root"] for row in rows} == {
        "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0"
    }
    assert {row["planned_raw_lookup_policy"] for row in rows} == {
        "case_insensitive_pdb_id_mmcif_or_cif_lookup_in_ignored_raw_root"
    }
    assert {row["raw_mmcif_read_current_step"] for row in rows} == {"False"}
    assert {row["raw_mmcif_read_required_next_step"] for row in rows} == {"True"}
    assert {row["raw_file_git_tracked_current_step"] for row in rows} == {"False"}
    assert {row["raw_file_git_staged_current_step"] for row in rows} == {"False"}
    assert {row["raw_file_commit_policy"] for row in rows} == {"do_not_commit_raw_files"}
    assert manifest["raw_mmcif_read_current_step"] is False
    assert manifest["raw_mmcif_read_required_next_step"] is True
    assert manifest["struct_conn_parsed_current_step"] is False
    assert manifest["atom_site_parsed_current_step"] is False


def test_schema_policy_readiness_and_masks() -> None:
    schema = _csv_rows(ROOT / "covapie_sample_preparation_schema_contract.csv")
    policy = _csv_rows(ROOT / "covapie_sample_preparation_design_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_sample_preparation_design_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert len(schema) == 10
    assert len(policy) == 14
    assert len(downstream) == 4
    assert {row["schema_contract_passed"] for row in schema} == {"True"}
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    by_schema = {row["schema_item"]: row for row in schema}
    assert by_schema["no_sample_index_current_stage"]["schema_contract_passed"] == "True"
    assert by_schema["no_final_dataset_current_stage"]["schema_contract_passed"] == "True"
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
    assert manifest["accepted_pdb_het_pairs"] == EXPECTED_ACCEPTED_PAIRS
    assert manifest["blocked_pdb_het_pairs"] == EXPECTED_BLOCKED_PAIRS
    assert manifest["recommended_next_step"] == "covapie_sample_preparation_execution_smoke"


def test_safety_no_raw_atom_tables_sample_final_model_training_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_sample_preparation_design_safety_audit.csv")
    manifest = _manifest()
    assert len(safety) == 22
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "network_access_used_current_step",
        "download_attempted_current_step",
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "atom_site_parsed_current_step",
        "data_raw_written_current_step",
        "html_files_written_current_step",
        "part_files_leftover_current_step",
        "actual_atom_tables_written_current_step",
        "protein_atom_table_written_current_step",
        "ligand_atom_table_written_current_step",
        "pocket_atom_table_written_current_step",
        "covalent_event_table_written_current_step",
        "sample_index_written_current_step",
        "final_dataset_written",
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
        assert not _imports_name(Path("src/covalent_ext/covapie_sample_preparation_design_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_sample_preparation_design_gate_v0.py"), name)


def test_existing_artifacts_and_raw_files_remain_clean() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    tracked = subprocess.run(["git", "ls-files", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not tracked
    assert not staged
    for path in [
        "data/derived/covalent_small/covapie_small_pilot_manifest_rerun_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_ready_candidate_materialization_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_result_review_decision_application_gate_v0",
    ]:
        diff = subprocess.run(["git", "diff", "--", path], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not diff
