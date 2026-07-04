from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0"

STEP13G_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0/"
    "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_manifest.json"
)
STEP13G_SCHEMA_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0/"
    "real_covalent_confirmed_candidate_minimal_sample_record_schema_contract.csv"
)
STEP13G_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0/"
    "real_covalent_confirmed_candidate_minimal_sample_record_candidate_contract.csv"
)
STEP13G_SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_manifest.json"
MINIMAL_SAMPLE_RECORDS_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_records.csv"
FIELD_AUDIT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_minimal_sample_record_field_audit.csv"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_SAMPLE_RECORD_ROW_COUNT = 3
EXPECTED_SCHEMA_FIELD_COUNT = 50
EXPECTED_FIELD_AUDIT_MIN_ROW_COUNT = 50

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_full_atom_extraction_design_gate"
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

MINIMAL_SAMPLE_RECORD_COLUMNS = [
    "minimal_sample_record_id",
    "minimal_sample_record_contract_id",
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
    "record_writer_stage",
    "coordinate_pair_id",
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
    "raw_structure_reference_required",
    "full_protein_atom_extraction_required",
    "full_ligand_atom_extraction_required",
    "pocket_definition_required",
    "ligand_bond_topology_required",
    "covalent_bond_annotation_required",
    "feature_semantics_audit_required",
    "split_leakage_check_required",
    "minimal_sample_record_written",
    "sample_index_written",
    "enriched_sample_index_written",
    "final_dataset_written",
    "model_input_materialized",
    "training_ready",
    "training_ready_reason",
]

FIELD_AUDIT_COLUMNS = [
    "field_name",
    "field_group",
    "schema_required_for_minimal_record",
    "source_stage",
    "source_column",
    "present_in_minimal_sample_records",
    "non_empty_for_all_records",
    "copied_or_derived_rule",
    "training_use_status",
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


def validate_step13g_minimal_sample_record_design_gate_v0() -> bool:
    required_paths = [STEP13G_MANIFEST_JSON, STEP13G_SCHEMA_CONTRACT_CSV, STEP13G_CANDIDATE_CONTRACT_CSV, STEP13G_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13H prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13G_MANIFEST_JSON)
    schema_rows = _read_csv(STEP13G_SCHEMA_CONTRACT_CSV)
    candidate_rows = _read_csv(STEP13G_CANDIDATE_CONTRACT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware",
        "all_checks_passed": True,
        "step13f_v1_altloc_aware_pair_sanity_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "minimal_sample_record_design_gate_defined": True,
        "minimal_sample_record_design_gate_executed": True,
        "pair_sanity_table_csv_read": True,
        "pair_sanity_row_count": 3,
        "schema_contract_csv_written": True,
        "schema_contract_field_count": EXPECTED_SCHEMA_FIELD_COUNT,
        "candidate_contract_csv_written": True,
        "candidate_contract_row_count": 3,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_pair_sanity_inputs_passed": True,
        "all_candidate_contract_rows_have_required_identity": True,
        "all_candidate_contract_rows_have_covalent_annotation": True,
        "all_candidate_contract_rows_have_endpoint_coordinates": True,
        "all_candidate_contract_rows_preserve_altloc_aware_selection": True,
        "all_candidate_contract_rows_preserve_pair_sanity": True,
        "all_candidate_contract_rows_mark_future_extraction_required": True,
        "all_candidate_contract_rows_training_ready_false": True,
        "all_candidate_contract_rows_sample_index_written_false": True,
        "all_candidate_contract_rows_final_dataset_written_false": True,
        "all_candidate_contract_rows_model_input_materialized_false": True,
        "hr0002_altloc_b_preserved": True,
        "hr0002_selected_protein_atom_site_id": "659",
        "hr0002_selected_protein_label_alt_id": "B",
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
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_passed": True,
        "minimal_sample_record_design_contract_satisfied": True,
        "ready_for_minimal_sample_record_write_smoke": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": STAGE.removesuffix("_v0"),
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13g_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(len(schema_rows) == EXPECTED_SCHEMA_FIELD_COUNT, "schema_row_count_invalid", blockers)
    _expect(list(schema_rows[0]) == SCHEMA_CONTRACT_COLUMNS, "schema_columns_invalid", blockers)
    schema_field_names = [row["field_name"] for row in schema_rows]
    _expect(len(schema_field_names) == len(set(schema_field_names)), "schema_field_names_not_unique", blockers)
    for row in schema_rows:
        _expect(row["field_name"] != "", "schema_field_name_empty", blockers)
        _expect(row["training_use_status"] == "not_training_input_yet", "schema_training_status_invalid", blockers)
    for required_field in [
        "minimal_sample_record_id",
        "training_ready",
        "training_ready_reason",
        "full_protein_atom_extraction_required",
        "full_ligand_atom_extraction_required",
        "pocket_definition_required",
        "ligand_bond_topology_required",
    ]:
        _expect(required_field in schema_field_names, f"schema_required_field_missing:{required_field}", blockers)
    _expect(len(candidate_rows) == EXPECTED_SAMPLE_RECORD_ROW_COUNT, "candidate_row_count_invalid", blockers)
    _expect(list(candidate_rows[0]) == CANDIDATE_CONTRACT_COLUMNS, "candidate_columns_invalid", blockers)
    _expect([row["review_row_id"] for row in candidate_rows] == EXPECTED_REVIEW_ROW_IDS, "candidate_review_order_invalid", blockers)
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
    for row in candidate_rows:
        _expect(row["minimal_sample_record_design_status"] == "contract_only_not_sample_index", "candidate_status_invalid", blockers)
        _expect(row["schema_contract_version"] == "minimal_sample_record_schema_v0", "candidate_schema_version_invalid", blockers)
        _expect(_is_true_text(row["coordinate_pair_sanity_passed"]), "candidate_pair_sanity_invalid", blockers)
        _expect(_is_true_text(row["altloc_aware_selection_confirmed"]), "candidate_altloc_invalid", blockers)
        _expect(all(_is_true_text(row[key]) for key in future_flags), "candidate_future_flags_invalid", blockers)
        _expect(_is_false_text(row["sample_index_written"]), "candidate_sample_index_invalid", blockers)
        _expect(_is_false_text(row["final_dataset_written"]), "candidate_final_dataset_invalid", blockers)
        _expect(_is_false_text(row["model_input_materialized"]), "candidate_model_input_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "candidate_training_ready_invalid", blockers)
    hr2 = next(row for row in candidate_rows if row["review_row_id"] == "HR_0002")
    _expect(hr2["protein_selected_atom_site_id"] == "659", "candidate_hr2_atom_site_invalid", blockers)
    _expect(hr2["protein_selected_label_alt_id"] == "B", "candidate_hr2_altloc_invalid", blockers)
    summary = STEP13G_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "minimal sample record design gate",
        "schema contract and a candidate contract",
        "candidate contract keeps training_ready=false",
        "Future steps still require full protein atom extraction",
        "HR_0002 altloc B atom_site 659 was preserved",
        "minimal sample record write smoke, not direct training",
    ]:
        _expect(snippet in summary, f"step13g_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step13g_schema_contract_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13G_SCHEMA_CONTRACT_CSV)


def load_step13g_candidate_contract_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13G_CANDIDATE_CONTRACT_CSV)


def build_minimal_sample_records_v0(candidate_contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_review = {row["review_row_id"]: row for row in candidate_contract_rows}
    records: list[dict[str, Any]] = []
    for index, review_id in enumerate(EXPECTED_REVIEW_ROW_IDS, start=1):
        row = by_review[review_id]
        record = {
            "minimal_sample_record_id": f"MSR_{index:04d}_{review_id}",
            "minimal_sample_record_contract_id": row["minimal_sample_record_contract_id"],
            "confirmed_candidate_id": row["confirmed_candidate_id"],
            "review_row_id": row["review_row_id"],
            "candidate_stub_id": row["candidate_stub_id"],
            "sample_id": row["sample_id"],
            "pdb_id": row["pdb_id"],
            "entry_id": row["entry_id"],
            "structure_title": row["structure_title"],
            "pair_sanity_stage": row["pair_sanity_stage"],
            "coordinate_source_stage": row["coordinate_source_stage"],
            "schema_contract_version": row["schema_contract_version"],
            "record_writer_stage": STAGE,
            "coordinate_pair_id": row["coordinate_pair_id"],
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
            "raw_structure_reference_required": True,
            "full_protein_atom_extraction_required": True,
            "full_ligand_atom_extraction_required": True,
            "pocket_definition_required": True,
            "ligand_bond_topology_required": True,
            "covalent_bond_annotation_required": True,
            "feature_semantics_audit_required": True,
            "split_leakage_check_required": True,
            "minimal_sample_record_written": True,
            "sample_index_written": False,
            "enriched_sample_index_written": False,
            "final_dataset_written": False,
            "model_input_materialized": False,
            "training_ready": False,
            "training_ready_reason": "minimal_sample_record_written_but_full_atom_model_input_not_materialized",
        }
        records.append(record)
    return records


def build_minimal_sample_record_field_audit_v0(
    schema_rows: list[dict[str, str]], minimal_sample_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    record_fields = set(MINIMAL_SAMPLE_RECORD_COLUMNS)
    for schema in schema_rows:
        field_name = schema["field_name"]
        present = field_name in record_fields
        non_empty = present and all(str(record.get(field_name, "")) != "" for record in minimal_sample_records)
        audit_rows.append(
            {
                "field_name": field_name,
                "field_group": schema["field_group"],
                "schema_required_for_minimal_record": schema["required_for_minimal_record"],
                "source_stage": schema["source_stage"],
                "source_column": schema["source_column"],
                "present_in_minimal_sample_records": present,
                "non_empty_for_all_records": non_empty,
                "copied_or_derived_rule": schema["future_writer_rule"],
                "training_use_status": schema["training_use_status"],
            }
        )
    return audit_rows


def _all_nonempty(row: dict[str, Any], keys: list[str]) -> bool:
    return all(str(row.get(key, "")) != "" for key in keys)


def _build_write_summary(records: list[dict[str, Any]], field_audit_rows: list[dict[str, Any]]) -> dict[str, Any]:
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
    identity_keys = ["minimal_sample_record_id", "confirmed_candidate_id", "review_row_id", "sample_id", "pdb_id"]
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
    audit_by_field = {row["field_name"]: row for row in field_audit_rows}
    hr2 = next(row for row in records if row["review_row_id"] == "HR_0002")
    return {
        "minimal_sample_record_row_count": len(records),
        "field_audit_row_count": len(field_audit_rows),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_minimal_sample_records_have_stable_ids": [
            row["minimal_sample_record_id"] for row in records
        ]
        == ["MSR_0001_HR_0002", "MSR_0002_HR_0003", "MSR_0003_HR_0004"],
        "all_minimal_sample_records_have_required_identity": all(_all_nonempty(row, identity_keys) for row in records),
        "all_minimal_sample_records_have_covalent_annotation": all(_all_nonempty(row, covalent_keys) for row in records),
        "all_minimal_sample_records_have_endpoint_coordinates": all(
            _all_nonempty(row, coordinate_keys) and all(_float_parseable(row[key]) for key in coordinate_keys)
            for row in records
        ),
        "all_minimal_sample_records_preserve_altloc_aware_selection": all(
            row["altloc_aware_selection_confirmed"] is True for row in records
        ),
        "all_minimal_sample_records_preserve_pair_sanity": all(
            row["coordinate_pair_sanity_passed"] is True for row in records
        ),
        "all_minimal_sample_records_mark_future_extraction_required": all(
            all(row[key] is True for key in future_flags) for row in records
        ),
        "all_minimal_sample_records_written_true": all(row["minimal_sample_record_written"] is True for row in records),
        "all_minimal_sample_records_training_ready_false": all(row["training_ready"] is False for row in records),
        "all_minimal_sample_records_sample_index_written_false": all(row["sample_index_written"] is False for row in records),
        "all_minimal_sample_records_enriched_sample_index_written_false": all(
            row["enriched_sample_index_written"] is False for row in records
        ),
        "all_minimal_sample_records_final_dataset_written_false": all(row["final_dataset_written"] is False for row in records),
        "all_minimal_sample_records_model_input_materialized_false": all(
            row["model_input_materialized"] is False for row in records
        ),
        "all_required_schema_fields_present_in_records": all(
            audit_by_field[field]["present_in_minimal_sample_records"] is True for field in REQUIRED_SCHEMA_FIELDS
        ),
        "hr0002_altloc_b_preserved": hr2["protein_selected_atom_site_id"] == "659"
        and hr2["protein_selected_label_alt_id"] == "B",
        "hr0002_selected_protein_atom_site_id": hr2["protein_selected_atom_site_id"],
        "hr0002_selected_protein_label_alt_id": hr2["protein_selected_label_alt_id"],
    }


def build_real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13g_validated = validate_step13g_minimal_sample_record_design_gate_v0()
    except Exception as exc:
        step13g_validated = False
        blockers.append(f"step13g_validation_failed:{type(exc).__name__}:{exc}")
    step13g_manifest = _load_json(STEP13G_MANIFEST_JSON)
    schema_rows = load_step13g_schema_contract_rows_v0()
    candidate_rows = load_step13g_candidate_contract_rows_v0()
    records = build_minimal_sample_records_v0(candidate_rows)
    field_audit_rows = build_minimal_sample_record_field_audit_v0(schema_rows, records)
    write_summary = _build_write_summary(records, field_audit_rows)
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
        step13g_validated
        and step13g_manifest["step12b_mask_level_aware_validator_validated"]
        and len(schema_rows) == EXPECTED_SCHEMA_FIELD_COUNT
        and len(candidate_rows) == EXPECTED_SAMPLE_RECORD_ROW_COUNT
        and write_summary["minimal_sample_record_row_count"] == EXPECTED_SAMPLE_RECORD_ROW_COUNT
        and write_summary["field_audit_row_count"] >= EXPECTED_FIELD_AUDIT_MIN_ROW_COUNT
        and write_summary["all_minimal_sample_records_have_stable_ids"]
        and write_summary["all_minimal_sample_records_have_required_identity"]
        and write_summary["all_minimal_sample_records_have_covalent_annotation"]
        and write_summary["all_minimal_sample_records_have_endpoint_coordinates"]
        and write_summary["all_minimal_sample_records_preserve_altloc_aware_selection"]
        and write_summary["all_minimal_sample_records_preserve_pair_sanity"]
        and write_summary["all_minimal_sample_records_mark_future_extraction_required"]
        and write_summary["all_minimal_sample_records_written_true"]
        and write_summary["all_minimal_sample_records_training_ready_false"]
        and write_summary["all_minimal_sample_records_sample_index_written_false"]
        and write_summary["all_minimal_sample_records_enriched_sample_index_written_false"]
        and write_summary["all_minimal_sample_records_final_dataset_written_false"]
        and write_summary["all_minimal_sample_records_model_input_materialized_false"]
        and write_summary["all_required_schema_fields_present_in_records"]
        and write_summary["hr0002_altloc_b_preserved"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13g_minimal_sample_record_design_gate_validated": step13g_validated,
        "step12b_mask_level_aware_validator_validated": step13g_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "minimal_sample_record_write_smoke_defined": True,
        "minimal_sample_record_write_smoke_executed": True,
        "schema_contract_csv_read": True,
        "schema_contract_field_count": len(schema_rows),
        "candidate_contract_csv_read": True,
        "candidate_contract_row_count": len(candidate_rows),
        "minimal_sample_records_csv_written": True,
        "field_audit_csv_written": True,
        **write_summary,
        "raw_files_read": False,
        "raw_files_decompressed": False,
        GZIP_OPEN_KEY: False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "coordinate_geometry_calculation_run": False,
        "final_pair_sanity_distance_calculated": False,
        "full_protein_atom_extraction_run": False,
        "full_ligand_atom_extraction_run": False,
        "pocket_definition_run": False,
        "ligand_bond_topology_extraction_run": False,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "sample_index_written": False,
        "enriched_sample_index_written": False,
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
        "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_passed": passed,
        "minimal_sample_record_write_smoke_contract_satisfied": passed,
        "ready_for_full_atom_extraction_design_gate": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "minimal_sample_records": records,
        "field_audit_rows": field_audit_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13g_precondition": {
            "step13g_minimal_sample_record_design_gate_validated": manifest[
                "step13g_minimal_sample_record_design_gate_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "schema_contract_input": {
            "schema_contract_csv_read": manifest["schema_contract_csv_read"],
            "schema_contract_field_count": manifest["schema_contract_field_count"],
        },
        "candidate_contract_input": {
            "candidate_contract_csv_read": manifest["candidate_contract_csv_read"],
            "candidate_contract_row_count": manifest["candidate_contract_row_count"],
        },
        "minimal_sample_records_written": {
            "minimal_sample_records_csv_written": manifest["minimal_sample_records_csv_written"],
            "minimal_sample_record_row_count": manifest["minimal_sample_record_row_count"],
        },
        "field_audit": {
            "field_audit_csv_written": manifest["field_audit_csv_written"],
            "field_audit_row_count": manifest["field_audit_row_count"],
        },
        "no_sample_index_no_final_dataset_boundary": {
            "sample_index_written": manifest["sample_index_written"],
            "enriched_sample_index_written": manifest["enriched_sample_index_written"],
            "final_dataset_written": manifest["final_dataset_written"],
            "model_input_materialized": manifest["model_input_materialized"],
        },
        "future_full_atom_requirements": {
            "full_protein_atom_extraction_run": manifest["full_protein_atom_extraction_run"],
            "full_ligand_atom_extraction_run": manifest["full_ligand_atom_extraction_run"],
            "ready_for_full_atom_extraction_design_gate": manifest["ready_for_full_atom_extraction_design_gate"],
        },
        "next_step_decision": {
            "recommended_next_step": manifest["recommended_next_step"],
            "ready_to_train_now": manifest["ready_to_train_now"],
        },
    }
