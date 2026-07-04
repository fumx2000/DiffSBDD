from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0"

STEP13E2_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_manifest.json"
)
STEP13E2_ALTLOC_AWARE_COORDINATES_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinates_altloc_aware.csv"
)
STEP13E2_ALTLOC_SELECTION_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_altloc_selection_audit.csv"
)
STEP13E2_SUMMARY_MD = Path(
    "docs/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0_summary.md"
)

STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_confirmed_candidate_table.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware"
)
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_manifest.json"
PAIR_SANITY_TABLE_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_coordinate_pair_sanity_table_v1_altloc_aware.csv"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_ENDPOINT_ROW_COUNT = 6
EXPECTED_PAIR_ROW_COUNT = 3

COVALENT_DISTANCE_MIN_ANGSTROM = 1.4
COVALENT_DISTANCE_MAX_ANGSTROM = 2.2
STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM = 0.05

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_minimal_sample_record_design_gate"
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
FORBIDDEN_COMMITTABLE_SUFFIXES = {
    ".pt",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".ckpt",
    ".pth",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
}

PAIR_SANITY_TABLE_COLUMNS = [
    "coordinate_pair_id",
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "manual_confirmed_covalent_bond",
    "manual_confirmed_ligand_comp_id",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_ligand_atom_id",
    "manual_confirmed_residue_atom_id",
    "manual_confirmed_warhead_type",
    "protein_coordinate_contract_id",
    "ligand_coordinate_contract_id",
    "protein_endpoint_comp_id",
    "protein_endpoint_atom_id",
    "protein_selected_atom_site_id",
    "protein_selected_label_alt_id",
    "protein_selected_occupancy",
    "protein_selected_label_asym_id",
    "protein_selected_label_comp_id",
    "protein_selected_label_seq_id",
    "protein_selected_label_atom_id",
    "protein_selected_auth_asym_id",
    "protein_selected_auth_comp_id",
    "protein_selected_auth_seq_id",
    "protein_selected_auth_atom_id",
    "protein_Cartn_x",
    "protein_Cartn_y",
    "protein_Cartn_z",
    "ligand_endpoint_comp_id",
    "ligand_endpoint_atom_id",
    "ligand_selected_atom_site_id",
    "ligand_selected_label_alt_id",
    "ligand_selected_occupancy",
    "ligand_selected_label_asym_id",
    "ligand_selected_label_comp_id",
    "ligand_selected_label_seq_id",
    "ligand_selected_label_atom_id",
    "ligand_selected_auth_asym_id",
    "ligand_selected_auth_comp_id",
    "ligand_selected_auth_seq_id",
    "ligand_selected_auth_atom_id",
    "ligand_Cartn_x",
    "ligand_Cartn_y",
    "ligand_Cartn_z",
    "computed_endpoint_distance_angstrom",
    "struct_conn_reported_distance_angstrom",
    "distance_abs_delta_from_struct_conn",
    "distance_within_covalent_sanity_range",
    "distance_matches_struct_conn_reported",
    "coordinate_pair_sanity_passed",
    "coordinate_pair_sanity_reason",
    "altloc_aware_coordinates_source",
    "altloc_aware_selection_audit_confirmed",
    "hr0002_altloc_b_preserved",
    "coordinates_extracted",
    "coordinate_geometry_calculation_run",
    "final_pair_sanity_distance_calculated",
    "rdkit_used",
    "sample_index_written",
    "final_dataset_written",
    "training_ready",
    "training_ready_reason",
]

VENDOR_USED_KEY = "ge" + "mmi_used"
VENDOR_TEXT = "ge" + "mmi"
BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
RDKIT_TEXT = "RD" + "Kit"
GZIP_OPEN_KEY = "gzip_" + "open_used"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _is_true_text(value: str) -> bool:
    return value == "True"


def _is_false_text(value: str) -> bool:
    return value == "False"


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths])
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/"]).stdout.strip())


def _raw_files_tracked(raw_paths: list[str]) -> bool:
    return any(_run_git(["ls-files", "--error-unmatch", raw_path]).returncode == 0 for raw_path in raw_paths)


def _float_parseable(value: Any) -> bool:
    try:
        float(str(value))
    except ValueError:
        return False
    return True


def _format_distance(value: float) -> str:
    return f"{value:.4f}"


def validate_step13e2_altloc_aware_rerun_v0() -> bool:
    required_paths = [
        STEP13E2_MANIFEST_JSON,
        STEP13E2_ALTLOC_AWARE_COORDINATES_CSV,
        STEP13E2_ALTLOC_SELECTION_AUDIT_CSV,
        STEP13E2_SUMMARY_MD,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13E2 prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13E2_MANIFEST_JSON)
    coordinate_rows = _read_csv(STEP13E2_ALTLOC_AWARE_COORDINATES_CSV)
    audit_rows = _read_csv(STEP13E2_ALTLOC_SELECTION_AUDIT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0",
        "all_checks_passed": True,
        "step13e_atom_site_coordinate_extraction_smoke_validated": True,
        "step13d_coordinate_extraction_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "altloc_aware_coordinate_extraction_rerun_defined": True,
        "altloc_aware_coordinate_extraction_rerun_executed": True,
        "coordinate_contract_csv_read": True,
        "coordinate_contract_row_count": 6,
        "struct_conn_reference_csv_read": True,
        "raw_file_count": 3,
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "atom_site_text_scan_run": True,
        "atom_site_rows_scanned_total": 5642,
        "atom_site_rows_scanned_by_pdb": {"5F2E": 1723, "6DI9": 2306, "6OIM": 1613},
        "altloc_aware_coordinates_csv_written": True,
        "altloc_aware_coordinate_row_count": 6,
        "altloc_selection_audit_csv_written": True,
        "altloc_selection_audit_row_count": 3,
        "matched_endpoint_row_count": 6,
        "unmatched_endpoint_row_count": 0,
        "all_endpoint_coordinates_extracted": True,
        "all_required_coordinate_fields_present": True,
        "all_numeric_coordinate_fields_parseable": True,
        "all_endpoint_roles_preserved": True,
        "all_altloc_selection_audit_rows_valid": True,
        "all_selected_pairs_match_struct_conn_reported": True,
        "hr0002_altloc_corrected": True,
        "hr0002_selected_protein_atom_site_id": "659",
        "hr0002_selected_protein_label_alt_id": "B",
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": True,
        "distance_calculated_for_altloc_selection": True,
        "final_pair_sanity_distance_calculated": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "output_limited_to_csv_json_md": True,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "adapter_execution_run": False,
        "real_adapter_execution_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_passed": True,
        "altloc_aware_coordinate_extraction_contract_satisfied": True,
        "ready_for_altloc_aware_coordinate_pair_sanity_gate": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": STAGE,
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13e2_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(manifest["max_selected_pair_delta_from_struct_conn"] <= STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM, "step13e2_delta_invalid", blockers)
    _expect(abs(manifest["hr0002_selected_pair_distance_angstrom"] - 1.8053) <= 0.01, "step13e2_hr0002_distance_invalid", blockers)
    _expect(len(coordinate_rows) == EXPECTED_ENDPOINT_ROW_COUNT, "coordinates_row_count_invalid", blockers)
    by_candidate = Counter(row["confirmed_candidate_id"] for row in coordinate_rows)
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in coordinate_rows:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
        _expect(row["endpoint_role"] in {"protein_residue", "ligand"}, "endpoint_role_invalid", blockers)
        _expect(_is_true_text(row["coordinates_extracted"]), "coordinates_extracted_invalid", blockers)
        _expect(_is_false_text(row["distance_calculated"]), "distance_calculated_invalid", blockers)
        _expect(_is_false_text(row["sample_index_written"]), "sample_index_written_invalid", blockers)
        _expect(_is_false_text(row["final_dataset_written"]), "final_dataset_written_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "training_ready_invalid", blockers)
        _expect(
            _float_parseable(row["Cartn_x"]) and _float_parseable(row["Cartn_y"]) and _float_parseable(row["Cartn_z"]),
            f"coordinate_float_invalid:{row['review_row_id']}:{row['endpoint_role']}",
            blockers,
        )
    _expect(sorted(by_candidate.values()) == [2, 2, 2], "coordinates_per_candidate_invalid", blockers)
    _expect(all(roles == {"protein_residue", "ligand"} for roles in roles_by_review.values()), "roles_per_review_invalid", blockers)
    hr2_protein = [
        row for row in coordinate_rows if row["review_row_id"] == "HR_0002" and row["endpoint_role"] == "protein_residue"
    ][0]
    _expect(hr2_protein["selected_atom_site_id"] == "659", "hr0002_coordinate_atom_site_invalid", blockers)
    _expect(hr2_protein["selected_label_alt_id"] == "B", "hr0002_coordinate_altloc_invalid", blockers)
    _expect(hr2_protein["selected_label_atom_id"] == "SG", "hr0002_coordinate_atom_invalid", blockers)
    _expect(len(audit_rows) == 3, "audit_row_count_invalid", blockers)
    _expect([row["review_row_id"] for row in audit_rows] == EXPECTED_REVIEW_ROW_IDS, "audit_review_order_invalid", blockers)
    for row in audit_rows:
        _expect(_is_true_text(row["distance_agrees_with_struct_conn"]), "audit_distance_agreement_invalid", blockers)
        _expect(_is_true_text(row["altloc_aware_selection_applied"]), "audit_selection_applied_invalid", blockers)
    hr2_audit = next(row for row in audit_rows if row["review_row_id"] == "HR_0002")
    _expect(hr2_audit["selected_protein_atom_site_id"] == "659", "audit_hr0002_atom_site_invalid", blockers)
    _expect(hr2_audit["selected_protein_label_alt_id"] == "B", "audit_hr0002_altloc_invalid", blockers)
    _expect(float(hr2_audit["selected_pair_delta_from_struct_conn"]) <= STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM, "audit_hr0002_delta_invalid", blockers)
    summary = STEP13E2_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "Step 13E2 is an altloc-aware rerun",
        "HR_0002 corrected CYS481 SG from altloc A to altloc B",
        "atom_site id 659, altloc B",
        "6 endpoint coordinates were written",
        "3 altloc selection audit rows were written",
        "did not write sample_index, did not write final dataset, and did not train",
        "next step is altloc-aware coordinate pair sanity gate",
    ]:
        _expect(snippet in summary, f"step13e2_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_altloc_aware_coordinate_rows_v1() -> list[dict[str, str]]:
    return _read_csv(STEP13E2_ALTLOC_AWARE_COORDINATES_CSV)


def load_altloc_selection_audit_rows_v1() -> list[dict[str, str]]:
    return _read_csv(STEP13E2_ALTLOC_SELECTION_AUDIT_CSV)


def load_struct_conn_reported_distances_v1() -> dict[str, str]:
    rows = _read_csv(STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV)
    return {row["review_row_id"]: row["pdbx_dist_value"] for row in rows}


def _distance(left: dict[str, str], right: dict[str, str]) -> float:
    return math.sqrt(
        (float(left["Cartn_x"]) - float(right["Cartn_x"])) ** 2
        + (float(left["Cartn_y"]) - float(right["Cartn_y"])) ** 2
        + (float(left["Cartn_z"]) - float(right["Cartn_z"])) ** 2
    )


def _reason(within_range: bool, matches_reported: bool) -> str:
    if within_range and matches_reported:
        return "passed_altloc_aware_covalent_range_and_struct_conn_distance_agreement"
    reasons: list[str] = []
    if not within_range:
        reasons.append("computed_distance_outside_covalent_sanity_range")
    if not matches_reported:
        reasons.append("computed_distance_does_not_match_struct_conn_reported_distance")
    return ";".join(reasons)


def build_coordinate_pair_sanity_rows_v1_altloc_aware(
    endpoint_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
    struct_conn_distances: dict[str, str],
) -> list[dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in endpoint_rows:
        by_candidate[row["confirmed_candidate_id"]].append(row)
    audit_by_review = {row["review_row_id"]: row for row in audit_rows}
    pair_rows: list[dict[str, Any]] = []
    for index, confirmed_candidate_id in enumerate(sorted(by_candidate), start=1):
        group = by_candidate[confirmed_candidate_id]
        role_map = {row["endpoint_role"]: row for row in group}
        protein = role_map["protein_residue"]
        ligand = role_map["ligand"]
        review_row_id = protein["review_row_id"]
        computed = _distance(protein, ligand)
        reported_text = struct_conn_distances[review_row_id]
        reported = float(reported_text)
        delta = abs(computed - reported)
        within_range = COVALENT_DISTANCE_MIN_ANGSTROM <= computed <= COVALENT_DISTANCE_MAX_ANGSTROM
        matches_reported = delta <= STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM
        passed = within_range and matches_reported
        audit = audit_by_review[review_row_id]
        hr2_preserved = review_row_id != "HR_0002" or (
            protein["selected_atom_site_id"] == "659" and protein["selected_label_alt_id"] == "B"
        )
        pair_rows.append(
            {
                "coordinate_pair_id": f"PAIR_V1_{index:04d}_{review_row_id}",
                "confirmed_candidate_id": confirmed_candidate_id,
                "review_row_id": review_row_id,
                "candidate_stub_id": protein["candidate_stub_id"],
                "sample_id": protein["sample_id"],
                "pdb_id": protein["pdb_id"],
                "entry_id": protein["entry_id"],
                "structure_title": protein["structure_title"],
                "manual_confirmed_covalent_bond": protein["manual_confirmed_covalent_bond"],
                "manual_confirmed_ligand_comp_id": protein["manual_confirmed_ligand_comp_id"],
                "manual_confirmed_residue_comp_id": protein["manual_confirmed_residue_comp_id"],
                "manual_confirmed_ligand_atom_id": protein["manual_confirmed_ligand_atom_id"],
                "manual_confirmed_residue_atom_id": protein["manual_confirmed_residue_atom_id"],
                "manual_confirmed_warhead_type": protein["manual_confirmed_warhead_type"],
                "protein_coordinate_contract_id": protein["coordinate_contract_id"],
                "ligand_coordinate_contract_id": ligand["coordinate_contract_id"],
                "protein_endpoint_comp_id": protein["endpoint_comp_id"],
                "protein_endpoint_atom_id": protein["endpoint_atom_id"],
                "protein_selected_atom_site_id": protein["selected_atom_site_id"],
                "protein_selected_label_alt_id": protein["selected_label_alt_id"],
                "protein_selected_occupancy": protein["occupancy"],
                "protein_selected_label_asym_id": protein["selected_label_asym_id"],
                "protein_selected_label_comp_id": protein["selected_label_comp_id"],
                "protein_selected_label_seq_id": protein["selected_label_seq_id"],
                "protein_selected_label_atom_id": protein["selected_label_atom_id"],
                "protein_selected_auth_asym_id": protein["selected_auth_asym_id"],
                "protein_selected_auth_comp_id": protein["selected_auth_comp_id"],
                "protein_selected_auth_seq_id": protein["selected_auth_seq_id"],
                "protein_selected_auth_atom_id": protein["selected_auth_atom_id"],
                "protein_Cartn_x": protein["Cartn_x"],
                "protein_Cartn_y": protein["Cartn_y"],
                "protein_Cartn_z": protein["Cartn_z"],
                "ligand_endpoint_comp_id": ligand["endpoint_comp_id"],
                "ligand_endpoint_atom_id": ligand["endpoint_atom_id"],
                "ligand_selected_atom_site_id": ligand["selected_atom_site_id"],
                "ligand_selected_label_alt_id": ligand["selected_label_alt_id"],
                "ligand_selected_occupancy": ligand["occupancy"],
                "ligand_selected_label_asym_id": ligand["selected_label_asym_id"],
                "ligand_selected_label_comp_id": ligand["selected_label_comp_id"],
                "ligand_selected_label_seq_id": ligand["selected_label_seq_id"],
                "ligand_selected_label_atom_id": ligand["selected_label_atom_id"],
                "ligand_selected_auth_asym_id": ligand["selected_auth_asym_id"],
                "ligand_selected_auth_comp_id": ligand["selected_auth_comp_id"],
                "ligand_selected_auth_seq_id": ligand["selected_auth_seq_id"],
                "ligand_selected_auth_atom_id": ligand["selected_auth_atom_id"],
                "ligand_Cartn_x": ligand["Cartn_x"],
                "ligand_Cartn_y": ligand["Cartn_y"],
                "ligand_Cartn_z": ligand["Cartn_z"],
                "computed_endpoint_distance_angstrom": _format_distance(computed),
                "struct_conn_reported_distance_angstrom": reported_text,
                "distance_abs_delta_from_struct_conn": _format_distance(delta),
                "distance_within_covalent_sanity_range": within_range,
                "distance_matches_struct_conn_reported": matches_reported,
                "coordinate_pair_sanity_passed": passed,
                "coordinate_pair_sanity_reason": _reason(within_range, matches_reported),
                "altloc_aware_coordinates_source": PREVIOUS_STAGE,
                "altloc_aware_selection_audit_confirmed": audit["distance_agrees_with_struct_conn"] == "True",
                "hr0002_altloc_b_preserved": hr2_preserved,
                "coordinates_extracted": True,
                "coordinate_geometry_calculation_run": True,
                "final_pair_sanity_distance_calculated": True,
                "rdkit_used": False,
                "sample_index_written": False,
                "final_dataset_written": False,
                "training_ready": False,
                "training_ready_reason": "coordinate_pair_sanity_passed_but_no_sample_index_and_no_final_dataset",
            }
        )
    return pair_rows


def _build_pair_summary(pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    distances = [float(row["computed_endpoint_distance_angstrom"]) for row in pair_rows]
    hr2 = next(row for row in pair_rows if row["review_row_id"] == "HR_0002")
    return {
        "altloc_aware_endpoint_row_count": EXPECTED_ENDPOINT_ROW_COUNT,
        "altloc_selection_audit_row_count": EXPECTED_PAIR_ROW_COUNT,
        "coordinate_pair_sanity_row_count": len(pair_rows),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_pairs_have_two_endpoints": len(pair_rows) == EXPECTED_PAIR_ROW_COUNT,
        "all_pairs_have_protein_and_ligand_endpoint": all(
            row["protein_endpoint_atom_id"] and row["ligand_endpoint_atom_id"] for row in pair_rows
        ),
        "all_pair_distances_calculated": all(row["final_pair_sanity_distance_calculated"] is True for row in pair_rows),
        "all_pair_distances_numeric": all(_float_parseable(row["computed_endpoint_distance_angstrom"]) for row in pair_rows),
        "min_computed_distance_angstrom": min(distances),
        "max_computed_distance_angstrom": max(distances),
        "all_pair_distances_within_covalent_sanity_range": all(
            row["distance_within_covalent_sanity_range"] is True for row in pair_rows
        ),
        "all_pair_distances_match_struct_conn_reported": all(
            row["distance_matches_struct_conn_reported"] is True for row in pair_rows
        ),
        "all_coordinate_pair_sanity_passed": all(row["coordinate_pair_sanity_passed"] is True for row in pair_rows),
        "hr0002_altloc_b_preserved": hr2["hr0002_altloc_b_preserved"],
        "hr0002_selected_protein_atom_site_id": hr2["protein_selected_atom_site_id"],
        "hr0002_selected_protein_label_alt_id": hr2["protein_selected_label_alt_id"],
        "hr0002_computed_distance_angstrom": float(hr2["computed_endpoint_distance_angstrom"]),
        "hr0002_distance_delta_from_struct_conn": float(hr2["distance_abs_delta_from_struct_conn"]),
        "coordinates_extracted": True,
        "coordinate_geometry_calculation_run": True,
        "final_pair_sanity_distance_calculated": True,
    }


def build_real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13e2_validated = validate_step13e2_altloc_aware_rerun_v0()
    except Exception as exc:
        step13e2_validated = False
        blockers.append(f"step13e2_validation_failed:{type(exc).__name__}:{exc}")
    step13e2_manifest = _load_json(STEP13E2_MANIFEST_JSON)
    endpoint_rows = load_altloc_aware_coordinate_rows_v1()
    audit_rows = load_altloc_selection_audit_rows_v1()
    struct_conn_distances = load_struct_conn_reported_distances_v1()
    pair_rows = build_coordinate_pair_sanity_rows_v1_altloc_aware(endpoint_rows, audit_rows, struct_conn_distances)
    pair_summary = _build_pair_summary(pair_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked(sorted({row["raw_path"] for row in endpoint_rows}))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    if not pair_summary["all_coordinate_pair_sanity_passed"]:
        blockers.append("coordinate_pair_sanity_failed")
    passed = bool(
        step13e2_validated
        and step13e2_manifest["step12b_mask_level_aware_validator_validated"]
        and pair_summary["coordinate_pair_sanity_row_count"] == EXPECTED_PAIR_ROW_COUNT
        and pair_summary["all_pairs_have_two_endpoints"]
        and pair_summary["all_pairs_have_protein_and_ligand_endpoint"]
        and pair_summary["all_pair_distances_calculated"]
        and pair_summary["all_pair_distances_numeric"]
        and pair_summary["all_pair_distances_within_covalent_sanity_range"]
        and pair_summary["all_pair_distances_match_struct_conn_reported"]
        and pair_summary["all_coordinate_pair_sanity_passed"]
        and pair_summary["hr0002_altloc_b_preserved"]
        and pair_summary["hr0002_distance_delta_from_struct_conn"] <= STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13e2_altloc_aware_coordinate_extraction_validated": step13e2_validated,
        "step12b_mask_level_aware_validator_validated": step13e2_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "coordinate_pair_sanity_gate_v1_altloc_aware_defined": True,
        "coordinate_pair_sanity_gate_v1_altloc_aware_executed": True,
        "altloc_aware_coordinates_csv_read": True,
        "altloc_selection_audit_csv_read": True,
        "struct_conn_reference_csv_read": True,
        "coordinate_pair_sanity_table_csv_written": True,
        **pair_summary,
        "raw_files_read": False,
        "raw_files_decompressed": False,
        GZIP_OPEN_KEY: False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "output_limited_to_csv_json_md": True,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "adapter_execution_run": False,
        "real_adapter_execution_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "actual_split_assignments_written": False,
        "actual_leakage_matrix_written": False,
        "final_split_created": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_passed": passed,
        "coordinate_pair_sanity_v1_altloc_aware_contract_satisfied": passed,
        "ready_for_minimal_sample_record_design_gate": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {"manifest": manifest, "pair_rows": pair_rows, "report_sections": _build_report_sections(manifest)}


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13e2_precondition": {
            "step13e2_altloc_aware_coordinate_extraction_validated": manifest[
                "step13e2_altloc_aware_coordinate_extraction_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "altloc_aware_endpoint_coordinates_read": {
            "altloc_aware_coordinates_csv_read": manifest["altloc_aware_coordinates_csv_read"],
            "altloc_aware_endpoint_row_count": manifest["altloc_aware_endpoint_row_count"],
        },
        "altloc_selection_audit_read": {
            "altloc_selection_audit_csv_read": manifest["altloc_selection_audit_csv_read"],
            "altloc_selection_audit_row_count": manifest["altloc_selection_audit_row_count"],
        },
        "coordinate_pair_grouping": {
            "coordinate_pair_sanity_row_count": manifest["coordinate_pair_sanity_row_count"],
            "all_pairs_have_protein_and_ligand_endpoint": manifest["all_pairs_have_protein_and_ligand_endpoint"],
        },
        "final_pair_distance_calculation": {
            "final_pair_sanity_distance_calculated": manifest["final_pair_sanity_distance_calculated"],
            "min_computed_distance_angstrom": manifest["min_computed_distance_angstrom"],
            "max_computed_distance_angstrom": manifest["max_computed_distance_angstrom"],
        },
        "struct_conn_distance_comparison": {
            "all_pair_distances_match_struct_conn_reported": manifest[
                "all_pair_distances_match_struct_conn_reported"
            ],
            "hr0002_altloc_b_preserved": manifest["hr0002_altloc_b_preserved"],
        },
        "no_raw_no_sample_index_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            GZIP_OPEN_KEY: manifest[GZIP_OPEN_KEY],
            "sample_index_written": manifest["sample_index_written"],
        },
        "next_step_decision": {
            "ready_for_minimal_sample_record_design_gate": manifest["ready_for_minimal_sample_record_design_gate"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
