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

from covalent_ext import real_covalent_confirmed_candidate_full_atom_extraction_smoke as gate


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _protein_rows() -> list[dict[str, str]]:
    with gate.PROTEIN_FULL_ATOM_TABLE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ligand_rows() -> list[dict[str, str]]:
    with gate.LIGAND_FULL_ATOM_TABLE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _audit_rows() -> list[dict[str, str]]:
    with gate.ENDPOINT_RECOVERY_AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step13i_precondition_and_contract_scope() -> None:
    assert gate.validate_step13i_full_atom_extraction_design_gate_v0() is True
    rows = gate.load_step13i_candidate_contract_rows_v0()
    assert len(rows) == 3
    assert [row["pdb_id"] for row in rows] == ["6DI9", "5F2E", "6OIM"]
    assert [row["review_row_id"] for row in rows] == ["HR_0002", "HR_0003", "HR_0004"]
    assert sorted({row["raw_path"] for row in rows}) == sorted(
        [
            "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz",
            "data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz",
            "data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz",
        ]
    )


def test_manifest_execution_fields() -> None:
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["step13i_design_gate_validated"] is True
    assert manifest["candidate_contract_csv_read"] is True
    assert manifest["candidate_contract_row_count"] == 3
    assert manifest["raw_file_count"] == 3
    assert manifest["raw_files_read"] is True
    assert manifest[gate.GZIP_OPEN_KEY] is True
    assert manifest["raw_files_decompressed"] is False
    assert manifest["decompressed_raw_files_written"] is False
    assert manifest["mmcif_text_read"] is True
    assert manifest["atom_site_text_scan_run"] is True
    assert manifest["parser_library_used"] == "custom_text_stream"
    assert manifest["atom_site_rows_scanned_by_pdb"] == {"5F2E": 1723, "6DI9": 2306, "6OIM": 1613}
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]


def test_full_atom_tables_written_and_nonempty() -> None:
    manifest = _manifest()
    protein_rows = _protein_rows()
    ligand_rows = _ligand_rows()
    assert gate.PROTEIN_FULL_ATOM_TABLE_CSV.is_file()
    assert gate.LIGAND_FULL_ATOM_TABLE_CSV.is_file()
    assert manifest["protein_full_atom_table_written"] is True
    assert manifest["ligand_full_atom_table_written"] is True
    assert len(protein_rows) == manifest["protein_full_atom_table_row_count"] == 4600
    assert len(ligand_rows) == manifest["ligand_full_atom_table_row_count"] == 104
    assert list(protein_rows[0]) == gate.FULL_ATOM_COLUMNS
    assert list(ligand_rows[0]) == gate.FULL_ATOM_COLUMNS
    assert {row["atom_table_kind"] for row in protein_rows} == {"protein"}
    assert {row["atom_table_kind"] for row in ligand_rows} == {"ligand"}
    assert all(row["group_PDB"] == "ATOM" for row in protein_rows)
    assert all(row["group_PDB"] == "HETATM" for row in ligand_rows)


def test_endpoint_recovery_audit_passes_all_candidates() -> None:
    audit_rows = _audit_rows()
    assert gate.ENDPOINT_RECOVERY_AUDIT_CSV.is_file()
    assert len(audit_rows) == 3
    assert list(audit_rows[0]) == gate.ENDPOINT_AUDIT_COLUMNS
    assert [row["review_row_id"] for row in audit_rows] == ["HR_0002", "HR_0003", "HR_0004"]
    for row in audit_rows:
        assert row["protein_endpoint_recovered"] == "True"
        assert row["ligand_endpoint_recovered"] == "True"
        assert row["protein_endpoint_coordinate_matches_step13i"] == "True"
        assert row["ligand_endpoint_coordinate_matches_step13i"] == "True"
        assert row["endpoint_recovery_passed"] == "True"
        assert row["blocking_reasons"] == ""


def test_hr0002_altloc_b_endpoint_is_preserved() -> None:
    manifest = _manifest()
    protein_rows = _protein_rows()
    ligand_rows = _ligand_rows()
    audit_by_review = {row["review_row_id"]: row for row in _audit_rows()}
    assert manifest["hr0002_altloc_b_preserved"] is True
    assert manifest["hr0002_selected_protein_atom_site_id"] == "659"
    assert manifest["hr0002_selected_protein_label_alt_id"] == "B"
    assert audit_by_review["HR_0002"]["recovered_protein_endpoint_atom_site_id"] == "659"
    assert audit_by_review["HR_0002"]["recovered_protein_endpoint_altloc"] == "B"
    hr2_protein_endpoint = [row for row in protein_rows if row["review_row_id"] == "HR_0002" and row["atom_site_id"] == "659"]
    assert len(hr2_protein_endpoint) == 1
    assert hr2_protein_endpoint[0]["label_alt_id"] == "B"
    assert hr2_protein_endpoint[0]["is_covalent_endpoint_atom"] == "True"
    hr2_ligand_endpoint = [row for row in ligand_rows if row["review_row_id"] == "HR_0002" and row["atom_site_id"] == "2070"]
    assert len(hr2_ligand_endpoint) == 1
    assert hr2_ligand_endpoint[0]["is_covalent_endpoint_atom"] == "True"


def test_no_pocket_topology_dataset_model_input_or_training() -> None:
    manifest = _manifest()
    false_keys = [
        "pocket_atom_table_written",
        "ligand_topology_table_written",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_ready_samples_claimed",
        "external_network_called",
        "data_downloaded",
        "download_attempted",
        "adapter_execution_run",
        "real_adapter_execution_run",
        "uniprot_mapping_run",
        "cdhit_run",
        "npz_files_loaded",
        "npz_contents_read",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "optimizer_step_called",
        "training_step_called",
        "trainer_fit_called",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        "npz_created",
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["ready_for_pocket_or_topology_design_gate"] is True
    assert manifest["ready_to_write_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_pocket_or_topology_design_gate"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_output_root_and_protected_source_safety() -> None:
    forbidden = [
        path
        for path in gate.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in gate.FORBIDDEN_COMMITTABLE_SUFFIXES
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
    assert protected_diff.stdout == ""
    assert protected_cached_diff.stdout == ""


def test_text_and_ast_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_full_atom_extraction_smoke.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0.py"),
    ]
    forbidden_text = [
        "ur" + "llib",
        "requ" + "ests",
        "url" + "open",
        "w" + "get",
        "c" + "url",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "ge" + "mmi",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
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
        "MolFromSmiles",
        "MolFromMolFile",
        "MolFromPDBFile",
        "GetMorganFingerprint",
        "GetMorganFingerprintAsBitVect",
        "url" + "open",
    }
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_text:
            assert pattern not in text
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
