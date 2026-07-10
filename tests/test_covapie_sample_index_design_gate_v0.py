from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_sample_index_design_gate as design_gate


ROOT = Path("data/derived/covalent_small/covapie_sample_index_design_gate_v0")
EXPECTED_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
EXPECTED_IDS = ["CYS_SG_SAMPLE_INDEX_000001", "CYS_SG_SAMPLE_INDEX_000002", "CYS_SG_SAMPLE_INDEX_000003"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_index_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 14AC check script before artifact tests"
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


def test_step14ab_precondition_and_manifest_counts() -> None:
    manifest14ab = json.loads(design_gate.STEP14AB_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_index_design_precondition_audit.csv")
    manifest = _manifest()

    assert manifest14ab["stage"] == design_gate.PREVIOUS_STAGE
    assert manifest14ab["all_checks_passed"] is True
    assert manifest14ab["sample_qa_count"] == 3
    assert manifest14ab["sample_qa_passed_count"] == 3
    assert manifest14ab["table_integrity_qa_count"] == 18
    assert manifest14ab["table_integrity_passed_count"] == 18
    assert manifest14ab["event_pair_qa_count"] == 3
    assert manifest14ab["event_pair_qa_passed_count"] == 3
    assert manifest14ab["qa_issue_count"] == 0
    assert manifest14ab["ready_for_covapie_sample_index_design_gate"] is True
    assert manifest14ab["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}

    assert manifest["stage"] == design_gate.STAGE
    assert manifest["step_label"] == "Step 14AC"
    assert manifest["previous_stage"] == design_gate.PREVIOUS_STAGE
    assert manifest["step14ab_sample_preparation_qa_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_source_inventory_has_three_rows_and_json_consistency() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_source_inventory.csv")
    json_rows = json.loads((ROOT / "covapie_sample_index_source_inventory.json").read_text(encoding="utf-8"))
    manifest = _manifest()

    assert len(rows) == 3
    assert len(json_rows) == 3
    assert [row["sample_index_source_id"] for row in rows] == [
        "CYS_SG_SAMPLE_INDEX_SOURCE_000001",
        "CYS_SG_SAMPLE_INDEX_SOURCE_000002",
        "CYS_SG_SAMPLE_INDEX_SOURCE_000003",
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert [row["sample_index_source_id"] for row in rows] == [row["sample_index_source_id"] for row in json_rows]
    assert {row["sample_level_qa_status"] for row in rows} == {"passed"}
    assert {row["table_integrity_status"] for row in rows} == {"passed"}
    assert {row["event_pair_qa_status"] for row in rows} == {"passed"}
    assert {row["eligible_for_sample_index_materialization"] for row in rows} == {"True"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert {row["covalent_bond_atom_pair"] for row in rows} == {"SG--CAG"}
    assert manifest["sample_index_source_inventory_count"] == 3
    assert manifest["sample_index_source_inventory_csv_json_consistent"] is True
    assert manifest["eligible_for_sample_index_materialization_count"] == 3


def test_all_six_source_artifact_paths_exist_for_each_sample() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_source_inventory.csv")
    path_fields = [
        "protein_atom_table_path",
        "ligand_atom_table_path",
        "pocket_atom_table_path",
        "covalent_event_table_path",
        "ligand_residue_atom_pair_table_path",
        "sample_preparation_audit_path",
    ]
    for row in rows:
        assert Path(row["sample_artifact_root"]).is_dir()
        for field in path_fields:
            assert Path(row[field]).is_file(), (field, row[field])
        assert int(row["protein_atom_count"]) > 0
        assert int(row["ligand_atom_count"]) > 0
        assert int(row["pocket_atom_count"]) > 0
        assert int(row["covalent_event_count"]) == 1
        assert int(row["ligand_residue_atom_pair_count"]) == 1


def test_schema_contract_contains_required_33_fields_design_only() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_schema_contract.csv")
    manifest = _manifest()
    assert len(rows) == 33
    assert [row["sample_index_field"] for row in rows] == design_gate.SAMPLE_INDEX_FIELDS
    assert {row["current_step_materializes_field"] for row in rows} == {"False"}
    assert {row["schema_contract_passed"] for row in rows} == {"True"}
    assert rows[0]["sample_index_field"] == "sample_index_row_id"
    assert rows[18]["sample_index_field"] == "covalent_residue_name"
    assert rows[21]["sample_index_field"] == "covalent_residue_atom_name"
    assert rows[22]["sample_index_field"] == "ligand_comp_id"
    assert rows[23]["sample_index_field"] == "ligand_covalent_atom_name"
    assert rows[24]["sample_index_field"] == "covalent_bond_atom_pair"
    assert rows[-3]["sample_index_field"] == "ready_for_training_current_step"
    assert rows[-2]["sample_index_field"] == "feature_semantics_audit_required_before_training"
    assert rows[-1]["sample_index_field"] == "leakage_split_design_required_before_training"
    assert manifest["sample_index_schema_field_count"] == 33
    assert manifest["schema_contract_passed"] is True


def test_field_mapping_count_and_status() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_field_mapping.csv")
    manifest = _manifest()
    assert len(rows) == 33
    assert [row["sample_index_field"] for row in rows] == design_gate.SAMPLE_INDEX_FIELDS
    assert {row["mapping_status"] for row in rows} == {"planned_and_validated"}
    by_field = {row["sample_index_field"]: row for row in rows}
    assert by_field["pdb_id"]["primary_source_artifact"] == "sample-level QA"
    assert by_field["covalent_residue_name"]["primary_source_artifact"] == "Step 14AA covalent_event_table"
    assert by_field["conn_type_id"]["primary_source_field"] == "conn_type_id"
    assert by_field["bond_distance_angstrom"]["primary_source_artifact"] == "Step 14AA ligand_residue_atom_pair_table"
    assert by_field["ready_for_training_current_step"]["primary_source_field"] == "false"
    assert by_field["feature_semantics_audit_required_before_training"]["primary_source_field"] == "true"
    assert manifest["sample_index_field_mapping_count"] == 33
    assert manifest["field_mapping_passed"] is True


def test_materialization_plan_has_three_pending_rows() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_index_materialization_plan.csv")
    manifest = _manifest()
    assert len(rows) == 3
    assert [row["planned_sample_index_row_id"] for row in rows] == EXPECTED_IDS
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["planned_materialization_status"] for row in rows} == {"pending_sample_index_materialization_smoke"}
    assert {row["required_source_table_count"] for row in rows} == {"6"}
    assert {row["required_source_tables_present"] for row in rows} == {"True"}
    assert {row["sample_qa_passed"] for row in rows} == {"True"}
    assert {row["event_pair_qa_passed"] for row in rows} == {"True"}
    assert {row["planned_next_gate"] for row in rows} == {"covapie_sample_index_materialization_smoke"}
    assert {row["sample_index_written_current_step"] for row in rows} == {"False"}
    assert {row["final_dataset_written_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    assert manifest["sample_index_materialization_plan_count"] == 3
    assert manifest["materialization_plan_passed"] is True


def test_policies_downstream_readiness_masks_and_training_boundaries() -> None:
    policies = _csv_rows(ROOT / "covapie_sample_index_design_policy_contract.csv")
    readiness = _csv_rows(ROOT / "covapie_sample_index_design_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert [row["policy_item"] for row in policies] == [
        "sample_index_design_gate_only",
        "design_gate_does_not_write_sample_index",
        "source_inventory_is_not_sample_index",
        "materialization_plan_is_not_sample_index",
        "design_gate_reads_qa_passed_derived_outputs_only",
        "design_gate_does_not_read_raw_mmcif",
        "design_gate_does_not_modify_atom_event_tables",
        "no_final_dataset_current_step",
        "no_split_or_leakage_current_step",
        "no_dataloader_smoke_current_step",
        "no_training_current_step",
        "feature_semantics_audit_required_before_training",
        "leakage_split_gate_required_before_training",
        "canonical_five_masks_preserved",
        "do_not_train_from_sample_index_design_artifacts",
    ]
    assert {row["policy_contract_passed"] for row in policies} == {"True"}
    by_ready = {row["readiness_item"]: row for row in readiness}
    assert by_ready["ready_for_covapie_sample_index_materialization_smoke"]["observed_status"] == "True"
    for key in [
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_training",
        "ready_to_train_now",
    ]:
        assert by_ready[key]["observed_status"] == "False"
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
    assert manifest["ready_for_covapie_sample_index_materialization_smoke"] is True
    assert manifest["ready_for_covapie_final_dataset_design_gate"] is False
    assert manifest["ready_for_covapie_actual_dataloader_adapter_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_sample_index_materialization_smoke"


def test_no_actual_sample_index_or_forbidden_outputs() -> None:
    forbidden_exact_names = {
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "actual_dataloader_smoke.csv",
        "actual_dataloader_smoke.json",
        "training_report.csv",
        "training_report.json",
    }
    forbidden_suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    bad_names = [p for p in ROOT.rglob("*") if p.is_file() and p.name in forbidden_exact_names]
    bad_suffixes = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in forbidden_suffixes]
    assert bad_names == []
    assert bad_suffixes == []
    manifest = _manifest()
    for key in [
        "sample_index_written_current_step",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "actual_dataloader_smoke_written",
        "training_artifacts_written",
        "raw_mmcif_read_current_step",
        "struct_conn_parsed_current_step",
        "atom_site_parsed_current_step",
    ]:
        assert manifest[key] is False, key


def test_safety_metadata_raw_existing_artifacts_and_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_sample_index_design_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    metadata_hash = hashlib.sha256(design_gate.METADATA_CSV.read_bytes()).hexdigest()
    assert metadata_hash == design_gate.METADATA_CSV_SHA256

    tracked = subprocess.run(["git", "ls-files", design_gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", design_gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []

    for path in [
        "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
        "data/derived/covalent_small/covapie_sample_preparation_qa_gate_v0",
        "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0",
        "data/derived/covalent_small/covapie_sample_preparation_design_gate_v0",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    ]:
        diff = subprocess.run(["git", "diff", "--", path], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not diff, path

    module_path = Path("src/covalent_ext/covapie_sample_index_design_gate.py")
    script_path = Path("scripts/check_covapie_sample_index_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "bs4"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)

    for key in [
        "network_access_used_current_step",
        "download_attempted_current_step",
        "data_raw_written_current_step",
        "torch_imported",
        "numpy_imported",
        "rdkit_used",
        "gemmi_used",
        "requests_used",
        "urllib_used",
        "selenium_used",
        "playwright_used",
        "bs4_used",
    ]:
        assert manifest[key] is False, key
