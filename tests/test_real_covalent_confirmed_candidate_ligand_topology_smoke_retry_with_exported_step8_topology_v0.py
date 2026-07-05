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

from covalent_ext import real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology as retry


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/check_real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0.py",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not retry.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(retry.MANIFEST_JSON.read_text(encoding="utf-8"))


def _true_count(rows: list[dict[str, str]], key: str) -> int:
    return sum(str(row.get(key, "")).lower() == "true" for row in rows)


def test_check_script_passes_and_validates_step13q_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == retry.STAGE
    assert manifest["previous_stage"] == retry.PREVIOUS_STAGE
    assert manifest["step13q_readonly_topology_evidence_export_validated"] is True
    assert manifest["topology_smoke_retry_scope"] == retry.TOPOLOGY_SMOKE_RETRY_SCOPE
    assert manifest["topology_smoke_retry_input_policy"] == retry.TOPOLOGY_SMOKE_RETRY_INPUT_POLICY
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_input_evidence_and_output_smoke_table_counts() -> None:
    manifest = _manifest()
    atom_rows = _csv_rows(retry.ATOM_SMOKE_TABLE_CSV)
    bond_rows = _csv_rows(retry.BOND_SMOKE_TABLE_CSV)
    assert manifest["step13q_atom_evidence_table_read"] is True
    assert manifest["step13q_atom_evidence_table_row_count"] == 104
    assert manifest["step13q_bond_evidence_table_read"] is True
    assert manifest["step13q_bond_evidence_table_row_count"] == 113
    assert manifest["ligand_observed_atom_topology_smoke_table_written"] is True
    assert manifest["ligand_observed_atom_topology_smoke_table_row_count"] == len(atom_rows) == 104
    assert manifest["ligand_observed_bond_topology_smoke_table_written"] is True
    assert manifest["ligand_observed_bond_topology_smoke_table_row_count"] == len(bond_rows) == 113
    assert {row["training_use_status"] for row in atom_rows} == {"not_training_input_yet"}
    assert {row["training_use_status"] for row in bond_rows} == {"not_training_input_yet"}
    assert {row["topology_source_stage"] for row in atom_rows} == {retry.TOPOLOGY_SOURCE_STAGE}
    assert {row["topology_source_stage"] for row in bond_rows} == {retry.TOPOLOGY_SOURCE_STAGE}
    assert {row["topology_smoke_status"] for row in atom_rows} == {retry.TOPOLOGY_SMOKE_STATUS}
    assert {row["topology_smoke_status"] for row in bond_rows} == {retry.TOPOLOGY_SMOKE_STATUS}


def test_per_candidate_counts_and_endpoint_counts() -> None:
    atom_rows = _csv_rows(retry.ATOM_SMOKE_TABLE_CSV)
    bond_rows = _csv_rows(retry.BOND_SMOKE_TABLE_CSV)
    atom_counts = {rid: sum(row["review_row_id"] == rid for row in atom_rows) for rid in retry.EXPECTED_REVIEW_ROW_IDS}
    bond_counts = {rid: sum(row["review_row_id"] == rid for row in bond_rows) for rid in retry.EXPECTED_REVIEW_ROW_IDS}
    assert atom_counts == {"HR_0002": 33, "HR_0003": 30, "HR_0004": 41}
    assert bond_counts == {"HR_0002": 35, "HR_0003": 33, "HR_0004": 45}
    endpoint_atom_counts = {
        rid: _true_count([row for row in atom_rows if row["review_row_id"] == rid], "is_covalent_ligand_endpoint_atom")
        for rid in retry.EXPECTED_REVIEW_ROW_IDS
    }
    endpoint_bond_counts = {
        rid: _true_count([row for row in bond_rows if row["review_row_id"] == rid], "touches_covalent_ligand_endpoint")
        for rid in retry.EXPECTED_REVIEW_ROW_IDS
    }
    assert endpoint_atom_counts == {"HR_0002": 1, "HR_0003": 1, "HR_0004": 1}
    assert endpoint_bond_counts == {"HR_0002": 1, "HR_0003": 1, "HR_0004": 1}
    manifest = _manifest()
    assert manifest["all_endpoint_atom_counts_equal_one"] is True
    assert manifest["all_endpoint_touching_bond_counts_equal_one"] is True


def test_group_counts_partition_and_cross_boundary_count() -> None:
    atom_rows = _csv_rows(retry.ATOM_SMOKE_TABLE_CSV)
    bond_rows = _csv_rows(retry.BOND_SMOKE_TABLE_CSV)
    assert _true_count(atom_rows, "warhead_group_status") == 12
    assert _true_count(atom_rows, "linker_group_status") == 18
    assert _true_count(atom_rows, "scaffold_group_status") == 74
    for row in atom_rows:
        assert (
            sum(
                str(row[key]).lower() == "true"
                for key in ["warhead_group_status", "linker_group_status", "scaffold_group_status"]
            )
            == 1
        )
    assert _true_count(bond_rows, "is_warhead_bond") == 9
    assert _true_count(bond_rows, "is_linker_bond") == 18
    assert _true_count(bond_rows, "is_scaffold_bond") == 79
    manifest = _manifest()
    assert manifest["atom_group_true_counts"] == {"warhead": 12, "linker": 18, "scaffold": 74}
    assert manifest["bond_group_true_counts"] == {"warhead": 9, "linker": 18, "scaffold": 79}
    assert manifest["cross_boundary_or_unassigned_bond_count"] == 7
    assert manifest["all_atom_group_partitions_passed"] is True
    assert manifest["all_ligand_topology_smoke_retry_passed"] is True


def test_audit_rows_are_complete_and_passing() -> None:
    manifest = _manifest()
    rows = _csv_rows(retry.AUDIT_CSV)
    assert manifest["smoke_retry_audit_written"] is True
    assert len(rows) == manifest["smoke_retry_audit_row_count"] == 3
    assert [row["review_row_id"] for row in rows] == retry.EXPECTED_REVIEW_ROW_IDS
    assert {row["atom_group_partition_passed"] for row in rows} == {"True"}
    assert {row["topology_smoke_retry_passed"] for row in rows} == {"True"}
    assert {row["blocking_reasons"] for row in rows} == {""}


def test_no_rdkit_sdf_raw_sample_index_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "rdkit_used",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "non_cys_generalization_run",
        "raw_files_read",
        "gzip_open_used",
        "mmcif_text_read",
        "atom_site_text_scan_run",
        "biopdb_parser_used",
        "gemmi_used",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["output_limited_to_csv_json_md"] is True


def test_readiness_boundary_points_to_sample_index_design_gate_only() -> None:
    manifest = _manifest()
    assert manifest["ready_for_sample_index_design_gate"] is True
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == retry.RECOMMENDED_NEXT_STEP


def test_output_root_and_repository_safety() -> None:
    _manifest()
    for path in [
        retry.ATOM_SMOKE_TABLE_CSV,
        retry.BOND_SMOKE_TABLE_CSV,
        retry.AUDIT_CSV,
        retry.REPORT_CSV,
        retry.MANIFEST_JSON,
        retry.SUMMARY_MD,
    ]:
        assert path.is_file()
    forbidden = [
        path
        for path in retry.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in retry.FORBIDDEN_COMMITTABLE_SUFFIXES
    ]
    assert forbidden == []
    protected_diff = subprocess.run(
        ["git", "diff", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    protected_cached_diff = subprocess.run(
        ["git", "diff", "--cached", "--", "equivariant_diffusion/", "lightning_modules.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw_tracked = subprocess.run(
        ["git", "ls-files", "data/raw/covalent_sources"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert protected_diff.stdout == ""
    assert protected_cached_diff.stdout == ""
    assert raw_staged.stdout == ""
    assert raw_tracked.stdout == ""


def test_summary_states_retry_boundary() -> None:
    _manifest()
    summary = retry.SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "consumes Step 13Q exported topology evidence tables only",
        "does not run " + "RD" + "Kit and does not read SDF",
        "promotes exported evidence into current CYS/SG golden topology smoke tables",
        "not model input and are not training data",
        "No sample_index",
        "ready_for_sample_index_design_gate=true",
        "ready_to_write_sample_index_now",
        "ready_to_train_now",
        "Feature semantics audit remains required before formal training",
        retry.RECOMMENDED_NEXT_STEP,
    ]:
        assert snippet in summary


def test_text_and_ast_safety_for_forbidden_execution_paths() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0.py"),
    ]
    forbidden_text = [
        "ur" + "llib",
        "requ" + "ests",
        "url" + "open",
        "w" + "get",
        "c" + "url",
        "gzip" + ".open",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "RD" + "Kit",
        "Chem." + "MolFrom",
        "Chem." + "SDMolSupplier",
        "model" + "(",
        "compute_" + "masked_loss",
        "." + "backward" + "(",
        "torch." + "optim",
        "optimizer." + "step",
        "trainer." + "fit",
        "training_" + "step" + "(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "numpy." + "load",
        "np." + "load",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_from_" + "checkpoint",
        "MolFrom" + "Smiles",
        "MolFrom" + "MolFile",
        "MolFrom" + "PDBFile",
        "SD" + "MolSupplier",
        "SD" + "Writer",
        "url" + "open",
    }
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text, f"{pattern} found in {path}"
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                owner = func.value.id if isinstance(func.value, ast.Name) else None
                assert not (owner in {"np", "numpy"} and func.attr == "load")
                assert not (owner == "torch" and func.attr in {"save", "optim"})
                assert not (owner == "optimizer" and func.attr == "step")
                assert func.attr not in dangerous_attrs
            if isinstance(func, ast.Name):
                assert func.id not in dangerous_names
