from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_sample_preparation_execution_smoke as step14aa
from covalent_ext import covapie_sample_preparation_qa_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_qa_gate_v0")
EXPECTED_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_preparation_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 14AB check script before artifact tests"
    return json.loads(path.read_text(encoding="utf-8"))


def test_step14aa_precondition_and_manifest_contract() -> None:
    step14aa_manifest = json.loads(step14aa.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_preparation_qa_precondition_audit.csv")
    manifest = _manifest()
    assert step14aa_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14aa_manifest["all_checks_passed"] is True
    assert step14aa_manifest["sample_execution_count"] == 3
    assert step14aa_manifest["sample_preparation_passed_count"] == 3
    assert step14aa_manifest["ready_for_covapie_sample_preparation_qa_gate"] is True
    assert step14aa_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14AB"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_sample_level_qa_has_three_passed_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_sample_level_qa.csv")
    rows_json = json.loads((ROOT / "covapie_sample_preparation_sample_level_qa.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(rows) == len(rows_json) == manifest["sample_qa_count"] == 3
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["sample_preparation_status"] for row in rows} == {"sample_preparation_smoke_passed"}
    assert {row["sample_level_qa_status"] for row in rows} == {"passed"}
    assert {row["ready_for_sample_index_design_gate_current_step"] for row in rows} == {"True"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    for row in rows:
        assert int(row["protein_atom_count"]) > 0
        assert int(row["ligand_atom_count"]) > 0
        assert int(row["pocket_atom_count"]) > 0
        assert int(row["covalent_event_count"]) == 1
        assert int(row["ligand_residue_atom_pair_count"]) == 1
    assert manifest["sample_qa_passed_count"] == 3


def test_table_integrity_qa_has_eighteen_passed_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_table_integrity_qa.csv")
    manifest = _manifest()
    assert len(rows) == manifest["table_integrity_qa_count"] == 18
    assert {row["table_exists"] for row in rows} == {"True"}
    assert {row["required_columns_present"] for row in rows} == {"True"}
    assert {row["table_integrity_status"] for row in rows} == {"passed"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert {row["table_name"] for row in rows} == set(gate.REQUIRED_TABLES)
    for row in rows:
        assert int(row["row_count"]) > 0
    assert manifest["table_integrity_passed_count"] == 18


def test_event_pair_qa_has_three_validated_events() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_event_pair_qa.csv")
    manifest = _manifest()
    assert len(rows) == manifest["event_pair_qa_count"] == 3
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["conn_type_id"] for row in rows} == {"covale"}
    assert {row["residue_comp_id"] for row in rows} == {"CYS"}
    assert {row["residue_atom_name"] for row in rows} == {"SG"}
    assert {row["ligand_comp_id"] for row in rows} == {"JUG"}
    assert {row["ligand_atom_name"] for row in rows} == {"CAG"}
    assert {row["covalent_bond_atom_pair"] for row in rows} == {"SG--CAG"}
    assert {row["event_source"] for row in rows} == {"raw_struct_conn"}
    assert {row["event_status"] for row in rows} == {"validated"}
    assert {row["bond_distance_status"] for row in rows} == {"positive_numeric_distance"}
    assert {row["ligand_covalent_atom_count"] for row in rows} == {"1"}
    assert {row["pocket_radius_status"] for row in rows} == {"all_pocket_rows_within_8_angstrom"}
    assert {row["event_pair_qa_status"] for row in rows} == {"passed"}
    for row in rows:
        assert float(row["bond_distance_angstrom"]) > 0
    assert manifest["event_pair_qa_passed_count"] == 3


def test_issue_inventory_and_downstream_readiness() -> None:
    issues = _csv_rows(ROOT / "covapie_sample_preparation_issue_inventory.csv")
    policy = _csv_rows(ROOT / "covapie_sample_preparation_qa_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_sample_preparation_qa_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert issues == [{
        "issue_id": "NO_QA_ISSUES",
        "issue_scope": "all_samples",
        "pdb_id": "",
        "expected_het_id": "",
        "issue_severity": "none",
        "issue_type": "no_issues",
        "issue_description": "No sample preparation QA issues detected.",
        "issue_status": "passed",
    }]
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["qa_issue_count"] == 0
    assert manifest["ready_for_covapie_sample_index_design_gate"] is True
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_sample_index_design_gate"


def test_safety_no_raw_read_no_new_atom_tables_no_training() -> None:
    safety = _csv_rows(ROOT / "covapie_sample_preparation_qa_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "atom_site_parsed_current_step",
        "sample_index_written_current_step",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "actual_dataloader_smoke_written",
        "training_artifacts_written",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert manifest[key] is False, key
    forbidden_names = {
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
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
        "protein_atom_table.csv",
        "ligand_atom_table.csv",
        "pocket_atom_table.csv",
        "covalent_event_table.csv",
        "ligand_residue_atom_pair_table.csv",
    }
    assert not [p for p in ROOT.rglob("*") if p.is_file() and p.name in forbidden_names]


def test_raw_metadata_existing_artifacts_masks_and_protected_paths_remain_clean() -> None:
    manifest = _manifest()
    assert manifest["accepted_pdb_het_pairs"] == EXPECTED_PAIRS
    assert manifest["covalent_bond_atom_pairs"] == ["SG--CAG"]
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
    tracked = subprocess.run(["git", "ls-files", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not tracked
    assert not staged
    for path in [
        "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
        "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0",
        "data/derived/covalent_small/covapie_sample_preparation_design_gate_v0",
        "data/derived/covalent_small/covapie_small_pilot_manifest_rerun_gate_v0",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    ]:
        diff = subprocess.run(["git", "diff", "--", path], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not diff, path
