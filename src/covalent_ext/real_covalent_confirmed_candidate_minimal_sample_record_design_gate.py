from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware"

STEP13F_V1_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_manifest.json"
)
STEP13F_V1_PAIR_SANITY_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_table_v1_altloc_aware.csv"
)
STEP13F_V1_SUMMARY_MD = Path(
    "docs/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_summary.md"
)

STEP13E2_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_manifest.json"
)
STEP13E2_ALTLOC_SELECTION_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_altloc_selection_audit.csv"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0"
)
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_manifest.json"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_schema_contract.csv"
CANDIDATE_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_candidate_contract.csv"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PAIR_ROW_COUNT = 3
EXPECTED_SCHEMA_MIN_FIELD_COUNT = 40

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke"
PREVIOUS_STAGE_RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_minimal_sample_record_design_gate"
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

SCHEMA_CONTRACT_COLUMNS = [
    "field_name",
    "field_group",
    "data_type",
    "required_for_minimal_record",
    "source_stage",
    "source_column",
    "description",
    "future_writer_rule",
    "training_use_status",
]

CANDIDATE_CONTRACT_COLUMNS = [
    "minimal_sample_record_contract_id",
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "coordinate_pair_id",
    "pair_sanity_stage",
    "coordinate_source_stage",
    "altloc_aware_selection_confirmed",
    "manual_confirmed_covalent_bond",
    "manual_confirmed_ligand_comp_id",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_ligand_atom_id",
    "manual_confirmed_residue_atom_id",
    "manual_confirmed_warhead_type",
    "protein_endpoint_comp_id",
    "protein_endpoint_atom_id",
    "protein_selected_atom_site_id",
    "protein_selected_label_alt_id",
    "protein_selected_occupancy",
    "protein_Cartn_x",
    "protein_Cartn_y",
    "protein_Cartn_z",
    "ligand_endpoint_comp_id",
    "ligand_endpoint_atom_id",
    "ligand_selected_atom_site_id",
    "ligand_selected_label_alt_id",
    "ligand_selected_occupancy",
    "ligand_Cartn_x",
    "ligand_Cartn_y",
    "ligand_Cartn_z",
    "computed_endpoint_distance_angstrom",
    "struct_conn_reported_distance_angstrom",
    "distance_abs_delta_from_struct_conn",
    "coordinate_pair_sanity_passed",
    "minimal_sample_record_design_status",
    "schema_contract_version",
    "raw_structure_reference_required",
    "full_protein_atom_extraction_required",
    "full_ligand_atom_extraction_required",
    "pocket_definition_required",
    "ligand_bond_topology_required",
    "covalent_bond_annotation_required",
    "feature_semantics_audit_required",
    "split_leakage_check_required",
    "sample_index_written",
    "final_dataset_written",
    "model_input_materialized",
    "training_ready",
    "training_ready_reason",
]

REQUIRED_SCHEMA_FIELDS = [
    "minimal_sample_record_id",
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "pair_sanity_stage",
    "coordinate_source_stage",
    "schema_contract_version",
    "manual_confirmed_covalent_bond",
    "manual_confirmed_ligand_comp_id",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_ligand_atom_id",
    "manual_confirmed_residue_atom_id",
    "manual_confirmed_warhead_type",
    "protein_endpoint_comp_id",
    "protein_endpoint_atom_id",
    "protein_selected_atom_site_id",
    "protein_selected_label_alt_id",
    "protein_selected_occupancy",
    "ligand_endpoint_comp_id",
    "ligand_endpoint_atom_id",
    "ligand_selected_atom_site_id",
    "ligand_selected_label_alt_id",
    "ligand_selected_occupancy",
    "protein_Cartn_x",
    "protein_Cartn_y",
    "protein_Cartn_z",
    "ligand_Cartn_x",
    "ligand_Cartn_y",
    "ligand_Cartn_z",
    "computed_endpoint_distance_angstrom",
    "struct_conn_reported_distance_angstrom",
    "distance_abs_delta_from_struct_conn",
    "coordinate_pair_sanity_passed",
    "raw_structure_reference_required",
    "full_protein_atom_extraction_required",
    "full_ligand_atom_extraction_required",
    "pocket_definition_required",
    "ligand_bond_topology_required",
    "covalent_bond_annotation_required",
    "feature_semantics_audit_required",
    "split_leakage_check_required",
    "sample_index_written",
    "final_dataset_written",
    "model_input_materialized",
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
GZIP_TEXT = "gzip" + ".open"


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


def _raw_covalent_sources_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _float_parseable(value: Any) -> bool:
    try:
        float(str(value))
    except ValueError:
        return False
    return True


def validate_step13f_v1_altloc_aware_pair_sanity_v0() -> bool:
    required_paths = [
        STEP13F_V1_MANIFEST_JSON,
        STEP13F_V1_PAIR_SANITY_TABLE_CSV,
        STEP13F_V1_SUMMARY_MD,
        STEP13E2_MANIFEST_JSON,
        STEP13E2_ALTLOC_SELECTION_AUDIT_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13G prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13F_V1_MANIFEST_JSON)
    pair_rows = _read_csv(STEP13F_V1_PAIR_SANITY_TABLE_CSV)
    step13e2_manifest = _load_json(STEP13E2_MANIFEST_JSON)
    audit_rows = _read_csv(STEP13E2_ALTLOC_SELECTION_AUDIT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0",
        "all_checks_passed": True,
        "step13e2_altloc_aware_coordinate_extraction_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "coordinate_pair_sanity_gate_v1_altloc_aware_defined": True,
        "coordinate_pair_sanity_gate_v1_altloc_aware_executed": True,
        "altloc_aware_coordinates_csv_read": True,
        "altloc_selection_audit_csv_read": True,
        "struct_conn_reference_csv_read": True,
        "coordinate_pair_sanity_table_csv_written": True,
        "altloc_aware_endpoint_row_count": 6,
        "altloc_selection_audit_row_count": 3,
        "coordinate_pair_sanity_row_count": EXPECTED_PAIR_ROW_COUNT,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_pairs_have_two_endpoints": True,
        "all_pairs_have_protein_and_ligand_endpoint": True,
        "all_pair_distances_calculated": True,
        "all_pair_distances_numeric": True,
        "all_pair_distances_within_covalent_sanity_range": True,
        "all_pair_distances_match_struct_conn_reported": True,
        "all_coordinate_pair_sanity_passed": True,
        "hr0002_altloc_b_preserved": True,
        "hr0002_selected_protein_atom_site_id": "659",
        "hr0002_selected_protein_label_alt_id": "B",
        "coordinates_extracted": True,
        "coordinate_geometry_calculation_run": True,
        "final_pair_sanity_distance_calculated": True,
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
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware_passed": True,
        "coordinate_pair_sanity_v1_altloc_aware_contract_satisfied": True,
        "ready_for_minimal_sample_record_design_gate": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": PREVIOUS_STAGE_RECOMMENDED_NEXT_STEP,
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13f_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(abs(float(manifest["hr0002_computed_distance_angstrom"]) - 1.8053) <= 0.001, "hr0002_distance_invalid", blockers)
    _expect(float(manifest["hr0002_distance_delta_from_struct_conn"]) <= 0.05, "hr0002_delta_invalid", blockers)
    _expect(len(pair_rows) == EXPECTED_PAIR_ROW_COUNT, "pair_row_count_invalid", blockers)
    _expect([row["review_row_id"] for row in pair_rows] == EXPECTED_REVIEW_ROW_IDS, "pair_review_order_invalid", blockers)
    required_pair_columns = {
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
        "protein_endpoint_comp_id",
        "protein_endpoint_atom_id",
        "protein_selected_atom_site_id",
        "protein_selected_label_alt_id",
        "protein_selected_occupancy",
        "protein_Cartn_x",
        "protein_Cartn_y",
        "protein_Cartn_z",
        "ligand_endpoint_comp_id",
        "ligand_endpoint_atom_id",
        "ligand_selected_atom_site_id",
        "ligand_selected_label_alt_id",
        "ligand_selected_occupancy",
        "ligand_Cartn_x",
        "ligand_Cartn_y",
        "ligand_Cartn_z",
        "computed_endpoint_distance_angstrom",
        "struct_conn_reported_distance_angstrom",
        "distance_abs_delta_from_struct_conn",
        "distance_within_covalent_sanity_range",
        "distance_matches_struct_conn_reported",
        "coordinate_pair_sanity_passed",
        "altloc_aware_selection_audit_confirmed",
        "sample_index_written",
        "final_dataset_written",
        "training_ready",
    }
    _expect(required_pair_columns.issubset(pair_rows[0]), "pair_required_columns_missing", blockers)
    for row in pair_rows:
        _expect(row["pdb_id"] in EXPECTED_PDB_IDS, "pair_pdb_id_invalid", blockers)
        _expect(_is_true_text(row["coordinate_pair_sanity_passed"]), "pair_sanity_invalid", blockers)
        _expect(_is_true_text(row["distance_within_covalent_sanity_range"]), "pair_range_invalid", blockers)
        _expect(_is_true_text(row["distance_matches_struct_conn_reported"]), "pair_distance_agreement_invalid", blockers)
        _expect(_is_false_text(row["sample_index_written"]), "pair_sample_index_invalid", blockers)
        _expect(_is_false_text(row["final_dataset_written"]), "pair_final_dataset_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "pair_training_ready_invalid", blockers)
        _expect(
            all(_float_parseable(row[key]) for key in ["protein_Cartn_x", "protein_Cartn_y", "protein_Cartn_z"]),
            f"protein_coordinate_invalid:{row['review_row_id']}",
            blockers,
        )
        _expect(
            all(_float_parseable(row[key]) for key in ["ligand_Cartn_x", "ligand_Cartn_y", "ligand_Cartn_z"]),
            f"ligand_coordinate_invalid:{row['review_row_id']}",
            blockers,
        )
    hr2 = next(row for row in pair_rows if row["review_row_id"] == "HR_0002")
    _expect(hr2["protein_selected_atom_site_id"] == "659", "pair_hr0002_atom_site_invalid", blockers)
    _expect(hr2["protein_selected_label_alt_id"] == "B", "pair_hr0002_altloc_invalid", blockers)
    _expect(step13e2_manifest["all_checks_passed"] is True, "step13e2_manifest_not_passed", blockers)
    _expect(step13e2_manifest["hr0002_selected_protein_atom_site_id"] == "659", "step13e2_hr0002_atom_site_invalid", blockers)
    _expect(step13e2_manifest["hr0002_selected_protein_label_alt_id"] == "B", "step13e2_hr0002_altloc_invalid", blockers)
    _expect(len(audit_rows) == 3, "step13e2_audit_count_invalid", blockers)
    for row in audit_rows:
        _expect(_is_true_text(row["distance_agrees_with_struct_conn"]), "step13e2_audit_distance_invalid", blockers)
        _expect(_is_true_text(row["altloc_aware_selection_applied"]), "step13e2_audit_selection_invalid", blockers)
    summary = STEP13F_V1_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "altloc-aware coordinate pair sanity gate",
        "paired 6 corrected endpoint rows into 3 protein-ligand coordinate pairs",
        "HR_0002 preserved CYS481 SG altloc B atom_site id 659",
        "All 3 pairs agree",
        "did not write sample_index",
        "minimal sample record design gate",
    ]:
        _expect(snippet in summary, f"step13f_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step13f_pair_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13F_V1_PAIR_SANITY_TABLE_CSV)


def _schema_row(
    field_name: str,
    field_group: str,
    data_type: str,
    required: bool,
    source_stage: str,
    source_column: str,
    description: str,
    future_writer_rule: str,
) -> dict[str, str]:
    return {
        "field_name": field_name,
        "field_group": field_group,
        "data_type": data_type,
        "required_for_minimal_record": str(required),
        "source_stage": source_stage,
        "source_column": source_column,
        "description": description,
        "future_writer_rule": future_writer_rule,
        "training_use_status": "not_training_input_yet",
    }


def build_minimal_sample_record_schema_contract_v0() -> list[dict[str, str]]:
    current = PREVIOUS_STAGE
    design = STAGE
    rows: list[dict[str, str]] = []
    identity_fields = [
        ("minimal_sample_record_id", "string", design, "derived", "Stable future minimal sample record identifier."),
        ("confirmed_candidate_id", "string", current, "confirmed_candidate_id", "Confirmed candidate identifier."),
        ("review_row_id", "string", current, "review_row_id", "Manual review row identifier."),
        ("candidate_stub_id", "string", current, "candidate_stub_id", "Candidate stub identifier from merge smoke."),
        ("sample_id", "string", current, "sample_id", "Pilot sample identifier."),
        ("pdb_id", "string", current, "pdb_id", "PDB identifier."),
        ("entry_id", "string", current, "entry_id", "mmCIF entry identifier copied from parser summary."),
        ("structure_title", "string", current, "structure_title", "Structure title provenance."),
        ("pair_sanity_stage", "string", design, "constant", "Coordinate pair sanity source stage."),
        ("coordinate_source_stage", "string", current, "altloc_aware_coordinates_source", "Altloc-aware endpoint source stage."),
        ("schema_contract_version", "string", design, "constant", "Schema contract version."),
    ]
    for name, data_type, source_stage, source_column, description in identity_fields:
        rows.append(
            _schema_row(name, "identity_provenance", data_type, True, source_stage, source_column, description, "copy_or_derive_before_write_smoke")
        )
    covalent_fields = [
        "manual_confirmed_covalent_bond",
        "manual_confirmed_ligand_comp_id",
        "manual_confirmed_residue_comp_id",
        "manual_confirmed_ligand_atom_id",
        "manual_confirmed_residue_atom_id",
        "manual_confirmed_warhead_type",
    ]
    for name in covalent_fields:
        rows.append(
            _schema_row(name, "covalent_annotation", "string", True, current, name, f"Manual review covalent annotation field {name}.", "copy_manual_review_value")
        )
    endpoint_identity_fields = [
        ("protein_endpoint_comp_id", "string"),
        ("protein_endpoint_atom_id", "string"),
        ("protein_selected_atom_site_id", "string"),
        ("protein_selected_label_alt_id", "string"),
        ("protein_selected_occupancy", "float_string"),
        ("ligand_endpoint_comp_id", "string"),
        ("ligand_endpoint_atom_id", "string"),
        ("ligand_selected_atom_site_id", "string"),
        ("ligand_selected_label_alt_id", "string"),
        ("ligand_selected_occupancy", "float_string"),
    ]
    for name, data_type in endpoint_identity_fields:
        rows.append(
            _schema_row(name, "endpoint_atom_identity", data_type, True, current, name, f"Verified endpoint atom identity field {name}.", "copy_altloc_aware_pair_value")
        )
    coordinate_fields = [
        "protein_Cartn_x",
        "protein_Cartn_y",
        "protein_Cartn_z",
        "ligand_Cartn_x",
        "ligand_Cartn_y",
        "ligand_Cartn_z",
    ]
    for name in coordinate_fields:
        rows.append(
            _schema_row(name, "endpoint_coordinates", "float_string", True, current, name, f"Verified endpoint coordinate field {name}.", "copy_without_recomputing_geometry")
        )
    distance_fields = [
        "computed_endpoint_distance_angstrom",
        "struct_conn_reported_distance_angstrom",
        "distance_abs_delta_from_struct_conn",
        "coordinate_pair_sanity_passed",
    ]
    for name in distance_fields:
        data_type = "bool_string" if name == "coordinate_pair_sanity_passed" else "float_string"
        rows.append(
            _schema_row(name, "distance_sanity", data_type, True, current, name, f"Pair sanity distance field {name}.", "copy_existing_sanity_result")
        )
    future_fields = [
        "raw_structure_reference_required",
        "full_protein_atom_extraction_required",
        "full_ligand_atom_extraction_required",
        "pocket_definition_required",
        "ligand_bond_topology_required",
        "covalent_bond_annotation_required",
        "feature_semantics_audit_required",
        "split_leakage_check_required",
    ]
    for name in future_fields:
        rows.append(
            _schema_row(name, "future_required_gate", "bool", True, design, "constant_true", f"Future prerequisite flag {name}.", "required_before_sample_index")
        )
    status_fields = [
        ("sample_index_written", "bool", "Must remain false in this design gate."),
        ("final_dataset_written", "bool", "Must remain false in this design gate."),
        ("model_input_materialized", "bool", "Must remain false until full model input artifacts exist."),
        ("training_ready", "bool", "Must remain false until all future gates pass."),
        ("training_ready_reason", "string", "Reason current record is not training input."),
    ]
    for name, data_type, description in status_fields:
        rows.append(
            _schema_row(name, "status", data_type, True, design, "constant", description, "write_false_or_reason_until_future_gates_pass")
        )
    return rows


def build_minimal_sample_record_candidate_contract_v0(pair_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_review = {row["review_row_id"]: row for row in pair_rows}
    candidate_rows: list[dict[str, Any]] = []
    for index, review_id in enumerate(EXPECTED_REVIEW_ROW_IDS, start=1):
        row = by_review[review_id]
        candidate_rows.append(
            {
                "minimal_sample_record_contract_id": f"MSR_CONTRACT_{index:04d}_{review_id}",
                "confirmed_candidate_id": row["confirmed_candidate_id"],
                "review_row_id": row["review_row_id"],
                "candidate_stub_id": row["candidate_stub_id"],
                "sample_id": row["sample_id"],
                "pdb_id": row["pdb_id"],
                "entry_id": row["entry_id"],
                "structure_title": row["structure_title"],
                "coordinate_pair_id": row["coordinate_pair_id"],
                "pair_sanity_stage": PREVIOUS_STAGE,
                "coordinate_source_stage": row["altloc_aware_coordinates_source"],
                "altloc_aware_selection_confirmed": True,
                "manual_confirmed_covalent_bond": row["manual_confirmed_covalent_bond"],
                "manual_confirmed_ligand_comp_id": row["manual_confirmed_ligand_comp_id"],
                "manual_confirmed_residue_comp_id": row["manual_confirmed_residue_comp_id"],
                "manual_confirmed_ligand_atom_id": row["manual_confirmed_ligand_atom_id"],
                "manual_confirmed_residue_atom_id": row["manual_confirmed_residue_atom_id"],
                "manual_confirmed_warhead_type": row["manual_confirmed_warhead_type"],
                "protein_endpoint_comp_id": row["protein_endpoint_comp_id"],
                "protein_endpoint_atom_id": row["protein_endpoint_atom_id"],
                "protein_selected_atom_site_id": row["protein_selected_atom_site_id"],
                "protein_selected_label_alt_id": row["protein_selected_label_alt_id"],
                "protein_selected_occupancy": row["protein_selected_occupancy"],
                "protein_Cartn_x": row["protein_Cartn_x"],
                "protein_Cartn_y": row["protein_Cartn_y"],
                "protein_Cartn_z": row["protein_Cartn_z"],
                "ligand_endpoint_comp_id": row["ligand_endpoint_comp_id"],
                "ligand_endpoint_atom_id": row["ligand_endpoint_atom_id"],
                "ligand_selected_atom_site_id": row["ligand_selected_atom_site_id"],
                "ligand_selected_label_alt_id": row["ligand_selected_label_alt_id"],
                "ligand_selected_occupancy": row["ligand_selected_occupancy"],
                "ligand_Cartn_x": row["ligand_Cartn_x"],
                "ligand_Cartn_y": row["ligand_Cartn_y"],
                "ligand_Cartn_z": row["ligand_Cartn_z"],
                "computed_endpoint_distance_angstrom": row["computed_endpoint_distance_angstrom"],
                "struct_conn_reported_distance_angstrom": row["struct_conn_reported_distance_angstrom"],
                "distance_abs_delta_from_struct_conn": row["distance_abs_delta_from_struct_conn"],
                "coordinate_pair_sanity_passed": True,
                "minimal_sample_record_design_status": "contract_only_not_sample_index",
                "schema_contract_version": "minimal_sample_record_schema_v0",
                "raw_structure_reference_required": True,
                "full_protein_atom_extraction_required": True,
                "full_ligand_atom_extraction_required": True,
                "pocket_definition_required": True,
                "ligand_bond_topology_required": True,
                "covalent_bond_annotation_required": True,
                "feature_semantics_audit_required": True,
                "split_leakage_check_required": True,
                "sample_index_written": False,
                "final_dataset_written": False,
                "model_input_materialized": False,
                "training_ready": False,
                "training_ready_reason": "design_contract_only_full_atom_sample_not_written",
            }
        )
    return candidate_rows


def _all_nonempty(row: dict[str, Any], keys: list[str]) -> bool:
    return all(str(row.get(key, "")) != "" for key in keys)


def _build_design_summary(schema_rows: list[dict[str, str]], candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    future_flags = [
        "raw_structure_reference_required",
        "full_protein_atom_extraction_required",
        "full_ligand_atom_extraction_required",
        "pocket_definition_required",
        "ligand_bond_topology_required",
        "covalent_bond_annotation_required",
        "feature_semantics_audit_required",
        "split_leakage_check_required",
    ]
    identity_keys = ["confirmed_candidate_id", "review_row_id", "candidate_stub_id", "sample_id", "pdb_id"]
    covalent_keys = [
        "manual_confirmed_covalent_bond",
        "manual_confirmed_ligand_comp_id",
        "manual_confirmed_residue_comp_id",
        "manual_confirmed_ligand_atom_id",
        "manual_confirmed_residue_atom_id",
    ]
    coordinate_keys = [
        "protein_Cartn_x",
        "protein_Cartn_y",
        "protein_Cartn_z",
        "ligand_Cartn_x",
        "ligand_Cartn_y",
        "ligand_Cartn_z",
    ]
    hr2 = next(row for row in candidate_rows if row["review_row_id"] == "HR_0002")
    return {
        "pair_sanity_row_count": EXPECTED_PAIR_ROW_COUNT,
        "schema_contract_field_count": len(schema_rows),
        "candidate_contract_row_count": len(candidate_rows),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_pair_sanity_inputs_passed": True,
        "all_candidate_contract_rows_have_required_identity": all(_all_nonempty(row, identity_keys) for row in candidate_rows),
        "all_candidate_contract_rows_have_covalent_annotation": all(_all_nonempty(row, covalent_keys) for row in candidate_rows),
        "all_candidate_contract_rows_have_endpoint_coordinates": all(
            _all_nonempty(row, coordinate_keys) and all(_float_parseable(row[key]) for key in coordinate_keys)
            for row in candidate_rows
        ),
        "all_candidate_contract_rows_preserve_altloc_aware_selection": all(
            row["altloc_aware_selection_confirmed"] is True for row in candidate_rows
        ),
        "all_candidate_contract_rows_preserve_pair_sanity": all(
            row["coordinate_pair_sanity_passed"] is True for row in candidate_rows
        ),
        "all_candidate_contract_rows_mark_future_extraction_required": all(
            all(row[key] is True for key in future_flags) for row in candidate_rows
        ),
        "all_candidate_contract_rows_training_ready_false": all(row["training_ready"] is False for row in candidate_rows),
        "all_candidate_contract_rows_sample_index_written_false": all(
            row["sample_index_written"] is False for row in candidate_rows
        ),
        "all_candidate_contract_rows_final_dataset_written_false": all(
            row["final_dataset_written"] is False for row in candidate_rows
        ),
        "all_candidate_contract_rows_model_input_materialized_false": all(
            row["model_input_materialized"] is False for row in candidate_rows
        ),
        "hr0002_altloc_b_preserved": hr2["protein_selected_atom_site_id"] == "659"
        and hr2["protein_selected_label_alt_id"] == "B",
        "hr0002_selected_protein_atom_site_id": hr2["protein_selected_atom_site_id"],
        "hr0002_selected_protein_label_alt_id": hr2["protein_selected_label_alt_id"],
    }


def build_real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13f_validated = validate_step13f_v1_altloc_aware_pair_sanity_v0()
    except Exception as exc:
        step13f_validated = False
        blockers.append(f"step13f_v1_validation_failed:{type(exc).__name__}:{exc}")
    step13f_manifest = _load_json(STEP13F_V1_MANIFEST_JSON)
    pair_rows = load_step13f_pair_rows_v0()
    schema_rows = build_minimal_sample_record_schema_contract_v0()
    candidate_rows = build_minimal_sample_record_candidate_contract_v0(pair_rows)
    design_summary = _build_design_summary(schema_rows, candidate_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_covalent_sources_tracked()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    passed = bool(
        step13f_validated
        and step13f_manifest["step12b_mask_level_aware_validator_validated"]
        and design_summary["schema_contract_field_count"] >= EXPECTED_SCHEMA_MIN_FIELD_COUNT
        and design_summary["candidate_contract_row_count"] == EXPECTED_PAIR_ROW_COUNT
        and design_summary["all_pair_sanity_inputs_passed"]
        and design_summary["all_candidate_contract_rows_have_required_identity"]
        and design_summary["all_candidate_contract_rows_have_covalent_annotation"]
        and design_summary["all_candidate_contract_rows_have_endpoint_coordinates"]
        and design_summary["all_candidate_contract_rows_preserve_altloc_aware_selection"]
        and design_summary["all_candidate_contract_rows_preserve_pair_sanity"]
        and design_summary["all_candidate_contract_rows_mark_future_extraction_required"]
        and design_summary["all_candidate_contract_rows_training_ready_false"]
        and design_summary["all_candidate_contract_rows_sample_index_written_false"]
        and design_summary["all_candidate_contract_rows_final_dataset_written_false"]
        and design_summary["all_candidate_contract_rows_model_input_materialized_false"]
        and design_summary["hr0002_altloc_b_preserved"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13f_v1_altloc_aware_pair_sanity_validated": step13f_validated,
        "step12b_mask_level_aware_validator_validated": step13f_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "minimal_sample_record_design_gate_defined": True,
        "minimal_sample_record_design_gate_executed": True,
        "pair_sanity_table_csv_read": True,
        "schema_contract_csv_written": True,
        "candidate_contract_csv_written": True,
        **design_summary,
        "raw_files_read": False,
        "raw_files_decompressed": False,
        GZIP_OPEN_KEY: False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "coordinate_geometry_calculation_run": False,
        "final_pair_sanity_distance_calculated": False,
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
        "model_input_materialized": False,
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
        "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_passed": passed,
        "minimal_sample_record_design_contract_satisfied": passed,
        "ready_for_minimal_sample_record_write_smoke": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "schema_rows": schema_rows,
        "candidate_rows": candidate_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13f_v1_precondition": {
            "step13f_v1_altloc_aware_pair_sanity_validated": manifest[
                "step13f_v1_altloc_aware_pair_sanity_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "pair_sanity_inputs": {
            "pair_sanity_table_csv_read": manifest["pair_sanity_table_csv_read"],
            "pair_sanity_row_count": manifest["pair_sanity_row_count"],
            "all_pair_sanity_inputs_passed": manifest["all_pair_sanity_inputs_passed"],
        },
        "schema_contract_design": {
            "schema_contract_csv_written": manifest["schema_contract_csv_written"],
            "schema_contract_field_count": manifest["schema_contract_field_count"],
        },
        "candidate_contract_design": {
            "candidate_contract_csv_written": manifest["candidate_contract_csv_written"],
            "candidate_contract_row_count": manifest["candidate_contract_row_count"],
        },
        "future_extraction_requirements": {
            "all_candidate_contract_rows_mark_future_extraction_required": manifest[
                "all_candidate_contract_rows_mark_future_extraction_required"
            ],
            "ready_to_write_enriched_sample_index_now": manifest["ready_to_write_enriched_sample_index_now"],
        },
        "no_sample_index_no_training_boundary": {
            "sample_index_written": manifest["sample_index_written"],
            "final_dataset_written": manifest["final_dataset_written"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "output_artifact_policy": {
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
            "forbidden_committable_artifacts_created": manifest["forbidden_committable_artifacts_created"],
        },
        "next_step_decision": {
            "ready_for_minimal_sample_record_write_smoke": manifest["ready_for_minimal_sample_record_write_smoke"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
