from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun as gate


OLD_STEP13F_PATHS = [
    Path("src/covalent_ext/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate.py"),
    Path("scripts/check_real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v0.py"),
    Path("tests/test_real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v0.py"),
    Path(
        "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v0/"
        "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_report.csv"
    ),
    Path(
        "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v0/"
        "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_manifest.json"
    ),
    Path(
        "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v0/"
        "real_covalent_confirmed_candidate_coordinate_pair_sanity_table.csv"
    ),
    Path("docs/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v0_summary.md"),
]


def _manifest() -> dict:
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _coordinate_rows() -> list[dict[str, str]]:
    with gate.ALTLOC_AWARE_COORDINATES_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _audit_rows() -> list[dict[str, str]]:
    with gate.ALTLOC_SELECTION_AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_cleanup_removed_old_step13f_untracked_files() -> None:
    assert all(not path.exists() for path in OLD_STEP13F_PATHS)
    status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    for path in OLD_STEP13F_PATHS:
        assert str(path) not in status
        assert subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], check=False).returncode != 0


def test_preconditions_and_basic_execution_fields() -> None:
    assert gate.validate_step13e_smoke_and_step13d_contract_v0() is True
    manifest = _manifest()
    assert manifest["step13e_atom_site_coordinate_extraction_smoke_validated"] is True
    assert manifest["step13d_coordinate_extraction_design_gate_validated"] is True
    assert manifest["step12b_mask_level_aware_validator_validated"] is True
    assert manifest["altloc_aware_coordinate_extraction_rerun_defined"] is True
    assert manifest["altloc_aware_coordinate_extraction_rerun_executed"] is True
    assert manifest["coordinate_contract_csv_read"] is True
    assert manifest["coordinate_contract_row_count"] == 6
    assert manifest["struct_conn_reference_csv_read"] is True
    assert manifest["raw_file_count"] == 3
    assert manifest["raw_files_read"] is True
    assert manifest["raw_files_decompressed_in_memory"] is True
    assert manifest["mmcif_text_read"] is True
    assert manifest["atom_site_text_scan_run"] is True
    assert manifest["atom_site_rows_scanned_total"] > 0
    assert set(manifest["atom_site_rows_scanned_by_pdb"]) == {"6DI9", "5F2E", "6OIM"}


def test_altloc_aware_counts_and_hr0002_correction() -> None:
    manifest = _manifest()
    assert manifest["altloc_aware_coordinates_csv_written"] is True
    assert manifest["altloc_aware_coordinate_row_count"] == 6
    assert manifest["altloc_selection_audit_csv_written"] is True
    assert manifest["altloc_selection_audit_row_count"] == 3
    assert manifest["matched_endpoint_row_count"] == 6
    assert manifest["unmatched_endpoint_row_count"] == 0
    assert manifest["all_endpoint_coordinates_extracted"] is True
    assert manifest["all_required_coordinate_fields_present"] is True
    assert manifest["all_numeric_coordinate_fields_parseable"] is True
    assert manifest["all_endpoint_roles_preserved"] is True
    assert manifest["all_altloc_selection_audit_rows_valid"] is True
    assert manifest["all_selected_pairs_match_struct_conn_reported"] is True
    assert manifest["max_selected_pair_delta_from_struct_conn"] <= gate.STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM
    assert manifest["hr0002_altloc_corrected"] is True
    assert manifest["hr0002_selected_protein_atom_site_id"] == "659"
    assert manifest["hr0002_selected_protein_label_alt_id"] == "B"
    assert abs(manifest["hr0002_selected_pair_distance_angstrom"] - 1.805) <= 0.01
    assert manifest["processed_pdb_ids"] == ["6DI9", "5F2E", "6OIM"]
    assert manifest["processed_review_row_ids"] == ["HR_0002", "HR_0003", "HR_0004"]


def test_coordinate_and_audit_csv_contracts() -> None:
    coords = _coordinate_rows()
    audit = _audit_rows()
    assert len(coords) == 6
    assert len(audit) == 3
    assert list(coords[0]) == gate.EXTRACTED_COORDINATE_COLUMNS
    assert list(audit[0]) == gate.ALTLOC_SELECTION_AUDIT_COLUMNS
    assert sorted(Counter(row["confirmed_candidate_id"] for row in coords).values()) == [2, 2, 2]
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in coords:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
        assert row["coordinates_extracted"] == "True"
        assert row["distance_calculated"] == "False"
        assert row["sample_index_written"] == "False"
        assert row["final_dataset_written"] == "False"
        assert row["training_ready"] == "False"
        float(row["Cartn_x"])
        float(row["Cartn_y"])
        float(row["Cartn_z"])
    assert all(roles == {"protein_residue", "ligand"} for roles in roles_by_review.values())
    audit_by_review = {row["review_row_id"]: row for row in audit}
    assert audit_by_review["HR_0002"]["selected_protein_atom_site_id"] == "659"
    assert audit_by_review["HR_0002"]["selected_protein_label_alt_id"] == "B"
    assert audit_by_review["HR_0002"]["selected_pair_delta_from_struct_conn"] <= "0.0500"
    for review_id in ["HR_0002", "HR_0003", "HR_0004"]:
        assert float(audit_by_review[review_id]["selected_pair_delta_from_struct_conn"]) <= 0.05
        assert audit_by_review[review_id]["distance_agrees_with_struct_conn"] == "True"
        assert audit_by_review[review_id]["altloc_aware_selection_applied"] == "True"


def test_hr0002_no_longer_selects_altloc_a() -> None:
    rows = _coordinate_rows()
    hr2_protein = [
        row for row in rows if row["review_row_id"] == "HR_0002" and row["endpoint_role"] == "protein_residue"
    ][0]
    assert hr2_protein["selected_atom_site_id"] == "659"
    assert hr2_protein["selected_label_alt_id"] == "B"
    assert hr2_protein["selected_atom_site_id"] != "658"
    assert hr2_protein["selected_label_alt_id"] != "A"


def test_boundary_and_decision_fields() -> None:
    manifest = _manifest()
    false_keys = [
        "raw_or_decompressed_mmcif_output_written",
        "structure_output_files_written",
        "full_mmcif_parser_used",
        "biopdb_parser_used",
        gate.VENDOR_USED_KEY,
        "rdkit_used",
        "final_pair_sanity_distance_calculated",
        "sample_index_written",
        "final_dataset_written",
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
        "actual_split_assignments_written",
        "actual_leakage_matrix_written",
        "final_split_created",
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
        "training_allowed",
        "finetune_allowed",
        "quality_claim_allowed",
        "parameter_update_allowed",
        "checkpoint_save_allowed",
        "model_save_allowed",
        "original_diffsbdd_source_modified",
        "forbidden_committable_artifacts_created",
        "raw_files_staged",
        "raw_files_tracked",
    ]
    for key in false_keys:
        assert manifest[key] is False
    assert manifest["parser_library_used"] == "none"
    assert manifest["coordinate_geometry_calculation_run"] is True
    assert manifest["distance_calculated_for_altloc_selection"] is True
    assert manifest["output_limited_to_csv_json_md"] is True
    assert manifest["real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_passed"] is True
    assert manifest["altloc_aware_coordinate_extraction_contract_satisfied"] is True
    assert manifest["ready_for_altloc_aware_coordinate_pair_sanity_gate"] is True
    assert manifest["ready_to_write_enriched_sample_index_now"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_to_download_large_scale_data_now"] is False
    assert manifest["recommended_next_step"] == "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware"
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_outputs_and_summary() -> None:
    assert gate.REPORT_CSV.is_file()
    assert gate.MANIFEST_JSON.is_file()
    assert gate.ALTLOC_AWARE_COORDINATES_CSV.is_file()
    assert gate.ALTLOC_SELECTION_AUDIT_CSV.is_file()
    assert gate.SUMMARY_MD.is_file()
    with gate.REPORT_CSV.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 8
    summary = gate.SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    for snippet in [
        "altloc-aware rerun of confirmed candidate atom_site coordinate extraction",
        "HR_0002 altloc mismatch",
        "cleaned the uncommitted blocked Step 13F untracked files",
        "Step 13D contract and Step 13C struct_conn reported distance",
        "3 raw `.cif.gz` files",
        "wrote no decompressed mmCIF",
        "`_atom_site` loop",
        f"did not use {parser_tools}",
        "HR_0002 corrected CYS481 SG from altloc A to altloc B",
        "atom_site id 659, altloc B",
        "6 endpoint coordinates were written",
        "3 altloc selection audit rows were written",
        "did not write sample_index, did not write final dataset, and did not train",
    ]:
        assert snippet in summary


def test_ast_and_text_safety() -> None:
    files = [
        Path("src/covalent_ext/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun.py"),
        Path("scripts/check_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0.py"),
        Path("tests/test_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0.py"),
    ]
    forbidden_text = [
        "ur" + "llib",
        "re" + "quests",
        "url" + "open",
        "w" + "get",
        "cu" + "rl",
        "Bio." + "PDB",
        "MM" + "CIFParser",
        "PDB" + "Parser",
        "ge" + "mmi",
        "Chem." + "MolFrom",
        "AllChem." + "GetMorganFingerprint",
        "mo" + "del(",
        "compute_" + "masked_loss",
        "." + "backward(",
        "torch." + "optim",
        "optimizer." + "step",
        "trainer." + "fit",
        "training_" + "step(",
        "torch." + "save",
        "save_" + "checkpoint",
        "load_" + "from_checkpoint",
        "numpy." + "load",
        "np." + "load",
    ]
    dangerous_names = {"Adam", "AdamW", "SGD", "RMSprop"}
    dangerous_attrs = {
        "backward",
        "fit",
        "save",
        "save_" + "checkpoint",
        "load_" + "from_checkpoint",
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
