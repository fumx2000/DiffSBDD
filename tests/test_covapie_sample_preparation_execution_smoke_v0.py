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

from covalent_ext import covapie_sample_preparation_design_gate as step14z
from covalent_ext import covapie_sample_preparation_execution_smoke as gate


ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0")
EXPECTED_PAIRS = ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
SAMPLE_DIRS = ["6BV6_JUG", "6BV8_JUG", "6BV5_JUG"]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_sample_preparation_execution_smoke_manifest.json"
    assert path.is_file(), "Run the Step 14AA check script before artifact tests"
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


def test_step14z_precondition_and_manifest_contract() -> None:
    step14z_manifest = json.loads(step14z.MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_sample_preparation_execution_precondition_audit.csv")
    manifest = _manifest()
    assert step14z_manifest["stage"] == gate.PREVIOUS_STAGE
    assert step14z_manifest["all_checks_passed"] is True
    assert step14z_manifest["sample_preparation_input_count"] == 3
    assert step14z_manifest["raw_mmcif_read_required_next_step"] is True
    assert step14z_manifest["ready_for_covapie_sample_preparation_execution_smoke"] is True
    assert step14z_manifest["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step 14AA"
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_execution_manifest_has_three_passed_samples() -> None:
    rows = _csv_rows(ROOT / "covapie_sample_preparation_execution_manifest.csv")
    rows_json = json.loads((ROOT / "covapie_sample_preparation_execution_manifest.json").read_text(encoding="utf-8"))
    inventory = _csv_rows(ROOT / "covapie_sample_preparation_execution_sample_inventory.csv")
    manifest = _manifest()
    assert len(rows) == len(rows_json) == len(inventory) == manifest["sample_execution_count"] == 3
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in rows] == EXPECTED_PAIRS
    assert {row["sample_preparation_status"] for row in rows} == {"sample_preparation_smoke_passed"}
    assert {row["ready_for_sample_index_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_final_dataset_current_step"] for row in rows} == {"False"}
    assert {row["ready_for_training_current_step"] for row in rows} == {"False"}
    for row in rows:
        assert row["raw_file_path"].endswith(f"{row['pdb_id'].lower()}.cif")
        assert int(row["protein_atom_count"]) > 0
        assert int(row["ligand_atom_count"]) > 0
        assert int(row["pocket_atom_count"]) > 0
        assert int(row["covalent_event_count"]) == 1
        assert int(row["ligand_residue_atom_pair_count"]) == 1


def test_per_sample_tables_exist_and_have_expected_event_rows() -> None:
    for sample_dir in SAMPLE_DIRS:
        root = ROOT / "samples" / sample_dir
        protein = _csv_rows(root / "protein_atom_table.csv")
        ligand = _csv_rows(root / "ligand_atom_table.csv")
        pocket = _csv_rows(root / "pocket_atom_table.csv")
        event = _csv_rows(root / "covalent_event_table.csv")
        pair = _csv_rows(root / "ligand_residue_atom_pair_table.csv")
        audit = _csv_rows(root / "sample_preparation_audit.csv")
        assert len(protein) > 0
        assert len(ligand) > 0
        assert len(pocket) > 0
        assert len(event) == 1
        assert len(pair) == 1
        assert len(audit) == 10
        assert {row["audit_passed"] for row in audit} == {"True"}
        ev = event[0]
        assert ev["conn_type_id"] == "covale"
        assert ev["residue_comp_id"] == "CYS"
        assert ev["residue_atom_name"] == "SG"
        assert ev["ligand_comp_id"] == "JUG"
        assert ev["ligand_atom_name"] == "CAG"
        assert ev["covalent_bond_atom_pair"] == "SG--CAG"
        assert ev["event_source"] == "raw_struct_conn"
        assert ev["event_status"] == "validated"


def test_ligand_pair_and_pocket_tables_are_valid() -> None:
    for sample_dir in SAMPLE_DIRS:
        root = ROOT / "samples" / sample_dir
        ligand = _csv_rows(root / "ligand_atom_table.csv")
        pocket = _csv_rows(root / "pocket_atom_table.csv")
        pair = _csv_rows(root / "ligand_residue_atom_pair_table.csv")[0]
        assert {row["ligand_comp_id"] for row in ligand} == {"JUG"}
        covalent_atoms = [row for row in ligand if row["is_covalent_ligand_atom"] == "True"]
        assert len(covalent_atoms) == 1
        assert covalent_atoms[0]["atom_name"] == "CAG"
        assert pair["covalent_bond_atom_pair"] == "SG--CAG"
        assert pair["residue_atom_site_id"]
        assert pair["ligand_atom_site_id"]
        assert float(pair["bond_distance_angstrom"]) > 0
        assert pair["validation_status"] == "validated_from_raw_struct_conn_and_atom_site"
        assert {row["pocket_radius_angstrom"] for row in pocket} == {"8.0"}
        assert max(float(row["min_distance_to_ligand_angstrom"]) for row in pocket) <= 8.0


def test_traceability_quality_policy_readiness_and_masks() -> None:
    traceability = _csv_rows(ROOT / "covapie_sample_preparation_execution_traceability_audit.csv")
    quality = _csv_rows(ROOT / "covapie_sample_preparation_execution_quality_audit.csv")
    policy = _csv_rows(ROOT / "covapie_sample_preparation_execution_policy_contract.csv")
    downstream = _csv_rows(ROOT / "covapie_sample_preparation_execution_downstream_readiness_contract.csv")
    manifest = _manifest()
    assert {row["traceability_audit_passed"] for row in traceability} == {"True"}
    assert {row["quality_audit_passed"] for row in quality} == {"True"}
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    assert {row["readiness_passed"] for row in downstream} == {"True"}
    assert manifest["protein_atom_table_written_count"] == 3
    assert manifest["ligand_atom_table_written_count"] == 3
    assert manifest["pocket_atom_table_written_count"] == 3
    assert manifest["covalent_event_table_written_count"] == 3
    assert manifest["ligand_residue_atom_pair_table_written_count"] == 3
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
    assert manifest["ready_for_covapie_sample_preparation_qa_gate"] is True
    assert manifest["ready_for_covapie_sample_index_design_gate"] is False
    assert manifest["recommended_next_step"] == "covapie_sample_preparation_qa_gate"


def test_no_sample_final_split_leakage_dataloader_training_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_sample_preparation_execution_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    assert manifest["raw_mmcif_read_current_step"] is True
    assert manifest["struct_conn_parsed_current_step"] is True
    assert manifest["atom_site_parsed_current_step"] is True
    for key in [
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
        assert not _imports_name(Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_sample_preparation_execution_smoke_v0.py"), name)


def test_raw_metadata_and_protected_paths_remain_clean() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    tracked = subprocess.run(["git", "ls-files", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", gate.RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not tracked
    assert not staged
    for path in [
        "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
        "data/derived/covalent_small/covapie_sample_preparation_design_gate_v0",
        "data/derived/covalent_small/covapie_small_pilot_manifest_rerun_gate_v0",
        "data/derived/covalent_small/covapie_cys_sg_ready_candidate_materialization_gate_v0",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    ]:
        diff = subprocess.run(["git", "diff", "--", path], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not diff, path
