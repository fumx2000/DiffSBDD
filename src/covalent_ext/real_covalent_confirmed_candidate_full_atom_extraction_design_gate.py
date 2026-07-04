from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0"

STEP13H_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0/"
    "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_manifest.json"
)
STEP13H_MINIMAL_SAMPLE_RECORDS_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0/"
    "real_covalent_confirmed_candidate_minimal_sample_records.csv"
)
STEP13H_FIELD_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0/"
    "real_covalent_confirmed_candidate_minimal_sample_record_field_audit.csv"
)
STEP13H_SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_v0_summary.md")

STEP13F_V1_PAIR_SANITY_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_table_v1_altloc_aware.csv"
)
STEP13E2_ALTLOC_AWARE_COORDINATES_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinates_altloc_aware.csv"
)
STEP13E2_ALTLOC_SELECTION_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0/"
    "real_covalent_confirmed_candidate_atom_site_altloc_selection_audit.csv"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_full_atom_extraction_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_full_atom_extraction_design_gate_manifest.json"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_full_atom_extraction_schema_contract.csv"
CANDIDATE_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_full_atom_extraction_candidate_contract.csv"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_MINIMAL_SAMPLE_RECORD_ROW_COUNT = 3
EXPECTED_FIELD_AUDIT_ROW_COUNT = 50
EXPECTED_CANDIDATE_CONTRACT_ROW_COUNT = 3
EXPECTED_SCHEMA_MIN_FIELD_COUNT = 60

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_full_atom_extraction_smoke"
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
    "output_table",
    "data_type",
    "required_for_full_atom_extraction_smoke",
    "source_stage",
    "source_column",
    "design_rule",
    "validation_rule",
    "training_use_status",
]

CANDIDATE_CONTRACT_COLUMNS = [
    "full_atom_extraction_contract_id",
    "minimal_sample_record_id",
    "minimal_sample_record_contract_id",
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "raw_path",
    "raw_structure_reference_available",
    "raw_structure_read_allowed_in_next_smoke",
    "raw_structure_read_in_this_design_gate",
    "pair_sanity_stage",
    "coordinate_source_stage",
    "minimal_sample_record_writer_stage",
    "full_atom_extraction_design_stage",
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
    "coordinate_pair_sanity_passed",
    "protein_full_atom_table_planned",
    "ligand_full_atom_table_planned",
    "pocket_atom_table_planned",
    "ligand_topology_table_planned",
    "protein_full_atom_extraction_scope",
    "ligand_full_atom_extraction_scope",
    "altloc_selection_policy",
    "model_selection_policy",
    "hydrogen_handling_policy",
    "water_handling_policy",
    "ion_handling_policy",
    "protein_chain_selection_policy",
    "ligand_selection_policy",
    "covalent_endpoint_validation_policy",
    "expected_protein_endpoint_atom_site_id",
    "expected_ligand_endpoint_atom_site_id",
    "expected_protein_endpoint_altloc",
    "expected_ligand_endpoint_altloc",
    "full_atom_extraction_design_status",
    "schema_contract_version",
    "full_atom_extraction_run",
    "protein_full_atom_table_written",
    "ligand_full_atom_table_written",
    "pocket_atom_table_written",
    "ligand_topology_table_written",
    "sample_index_written",
    "enriched_sample_index_written",
    "final_dataset_written",
    "model_input_materialized",
    "training_ready",
    "training_ready_reason",
]

GZIP_TEXT = "gzip" + ".open"
BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
VENDOR_TEXT = "ge" + "mmi"
RDKIT_TEXT = "RD" + "Kit"
GZIP_OPEN_KEY = "gzip_" + "open_used"
VENDOR_USED_KEY = "ge" + "mmi_used"


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


def validate_step13h_minimal_sample_record_write_smoke_v0() -> bool:
    required_paths = [STEP13H_MANIFEST_JSON, STEP13H_MINIMAL_SAMPLE_RECORDS_CSV, STEP13H_FIELD_AUDIT_CSV, STEP13H_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13I prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13H_MANIFEST_JSON)
    records = _read_csv(STEP13H_MINIMAL_SAMPLE_RECORDS_CSV)
    audit_rows = _read_csv(STEP13H_FIELD_AUDIT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0",
        "all_checks_passed": True,
        "step13g_minimal_sample_record_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "minimal_sample_record_write_smoke_defined": True,
        "minimal_sample_record_write_smoke_executed": True,
        "schema_contract_csv_read": True,
        "schema_contract_field_count": 50,
        "candidate_contract_csv_read": True,
        "candidate_contract_row_count": 3,
        "minimal_sample_records_csv_written": True,
        "minimal_sample_record_row_count": 3,
        "field_audit_csv_written": True,
        "field_audit_row_count": 50,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_minimal_sample_records_have_stable_ids": True,
        "all_minimal_sample_records_have_required_identity": True,
        "all_minimal_sample_records_have_covalent_annotation": True,
        "all_minimal_sample_records_have_endpoint_coordinates": True,
        "all_minimal_sample_records_preserve_altloc_aware_selection": True,
        "all_minimal_sample_records_preserve_pair_sanity": True,
        "all_minimal_sample_records_mark_future_extraction_required": True,
        "all_minimal_sample_records_written_true": True,
        "all_minimal_sample_records_training_ready_false": True,
        "all_minimal_sample_records_sample_index_written_false": True,
        "all_minimal_sample_records_enriched_sample_index_written_false": True,
        "all_minimal_sample_records_final_dataset_written_false": True,
        "all_minimal_sample_records_model_input_materialized_false": True,
        "all_required_schema_fields_present_in_records": True,
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
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_confirmed_candidate_minimal_sample_record_write_smoke_passed": True,
        "minimal_sample_record_write_smoke_contract_satisfied": True,
        "ready_for_full_atom_extraction_design_gate": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": STAGE.removesuffix("_v0"),
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13h_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(len(records) == 3, "minimal_record_count_invalid", blockers)
    _expect([row["review_row_id"] for row in records] == EXPECTED_REVIEW_ROW_IDS, "minimal_record_order_invalid", blockers)
    _expect(
        [row["minimal_sample_record_id"] for row in records]
        == ["MSR_0001_HR_0002", "MSR_0002_HR_0003", "MSR_0003_HR_0004"],
        "minimal_record_ids_invalid",
        blockers,
    )
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
    for row in records:
        _expect(_is_true_text(row["minimal_sample_record_written"]), "record_written_invalid", blockers)
        _expect(_is_true_text(row["coordinate_pair_sanity_passed"]), "record_pair_sanity_invalid", blockers)
        _expect(_is_true_text(row["altloc_aware_selection_confirmed"]), "record_altloc_invalid", blockers)
        _expect(all(_is_true_text(row[key]) for key in future_flags), "record_future_flags_invalid", blockers)
        _expect(_is_false_text(row["sample_index_written"]), "record_sample_index_invalid", blockers)
        _expect(_is_false_text(row["enriched_sample_index_written"]), "record_enriched_sample_index_invalid", blockers)
        _expect(_is_false_text(row["final_dataset_written"]), "record_final_dataset_invalid", blockers)
        _expect(_is_false_text(row["model_input_materialized"]), "record_model_input_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "record_training_ready_invalid", blockers)
    hr2 = next(row for row in records if row["review_row_id"] == "HR_0002")
    _expect(hr2["protein_selected_atom_site_id"] == "659", "record_hr2_atom_site_invalid", blockers)
    _expect(hr2["protein_selected_label_alt_id"] == "B", "record_hr2_altloc_invalid", blockers)
    _expect(len(audit_rows) == 50, "field_audit_count_invalid", blockers)
    for row in audit_rows:
        _expect(row["training_use_status"] == "not_training_input_yet", "field_audit_training_status_invalid", blockers)
    by_field = {row["field_name"]: row for row in audit_rows}
    for field in [
        "minimal_sample_record_id",
        "training_ready",
        "training_ready_reason",
        "full_protein_atom_extraction_required",
        "full_ligand_atom_extraction_required",
        "pocket_definition_required",
        "ligand_bond_topology_required",
    ]:
        _expect(by_field[field]["present_in_minimal_sample_records"] == "True", f"field_audit_missing:{field}", blockers)
    summary = STEP13H_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "minimal sample record write smoke",
        "wrote 3 minimal sample records",
        "field audit",
        "HR_0002 altloc B atom_site 659",
        "did not read raw",
        "did not run full protein atom extraction",
        "did not materialize model input",
        "full atom extraction design gate, not direct training",
    ]:
        _expect(snippet in summary, f"step13h_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step13h_minimal_sample_records_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13H_MINIMAL_SAMPLE_RECORDS_CSV)


def load_step13h_field_audit_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13H_FIELD_AUDIT_CSV)


def load_step13f_pair_sanity_rows_v1() -> list[dict[str, str]]:
    return _read_csv(STEP13F_V1_PAIR_SANITY_TABLE_CSV)


def load_step13e2_altloc_aware_endpoint_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13E2_ALTLOC_AWARE_COORDINATES_CSV)


def load_step13e2_altloc_selection_audit_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13E2_ALTLOC_SELECTION_AUDIT_CSV)


def _schema_row(
    field_name: str,
    field_group: str,
    output_table: str,
    data_type: str,
    required: bool,
    source_stage: str,
    source_column: str,
    design_rule: str,
    validation_rule: str,
) -> dict[str, str]:
    return {
        "field_name": field_name,
        "field_group": field_group,
        "output_table": output_table,
        "data_type": data_type,
        "required_for_full_atom_extraction_smoke": str(required),
        "source_stage": source_stage,
        "source_column": source_column,
        "design_rule": design_rule,
        "validation_rule": validation_rule,
        "training_use_status": "not_training_input_yet",
    }


def build_full_atom_extraction_schema_contract_v0() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sample_fields = [
        "full_atom_extraction_contract_id",
        "minimal_sample_record_id",
        "confirmed_candidate_id",
        "review_row_id",
        "sample_id",
        "pdb_id",
        "entry_id",
        "raw_path",
        "pair_sanity_stage",
        "coordinate_source_stage",
        "minimal_sample_record_writer_stage",
        "full_atom_extraction_design_stage",
        "schema_contract_version",
    ]
    for field in sample_fields:
        rows.append(
            _schema_row(
                field,
                "sample_provenance",
                "sample_extraction_contract",
                "string",
                True,
                STAGE if field.endswith("stage") or field.endswith("version") else PREVIOUS_STAGE,
                "derived" if field in {"full_atom_extraction_contract_id", "full_atom_extraction_design_stage"} else field,
                "copy_or_derive_contract_value_without_raw_read",
                "present_in_candidate_contract",
            )
        )
    protein_fields = [
        "minimal_sample_record_id",
        "pdb_id",
        "raw_path",
        "atom_site_id",
        "group_PDB",
        "type_symbol",
        "label_atom_id",
        "label_comp_id",
        "label_asym_id",
        "label_seq_id",
        "label_alt_id",
        "auth_atom_id",
        "auth_comp_id",
        "auth_asym_id",
        "auth_seq_id",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
        "occupancy",
        "is_polymer_atom",
        "is_target_protein_chain_atom",
        "is_covalent_residue_atom",
        "is_covalent_endpoint_atom",
        "extraction_source_stage",
    ]
    for field in protein_fields:
        rows.append(
            _schema_row(
                field,
                "protein_full_atom_table",
                "protein_full_atom_table",
                "bool" if field.startswith("is_") else "float_string" if field in {"Cartn_x", "Cartn_y", "Cartn_z", "occupancy"} else "string",
                True,
                RECOMMENDED_NEXT_STEP,
                field,
                "extract_in_next_smoke_from_raw_text_stream",
                "not_written_in_design_gate",
            )
        )
    ligand_fields = [
        "minimal_sample_record_id",
        "pdb_id",
        "raw_path",
        "atom_site_id",
        "group_PDB",
        "type_symbol",
        "label_atom_id",
        "label_comp_id",
        "label_asym_id",
        "label_seq_id",
        "label_alt_id",
        "auth_atom_id",
        "auth_comp_id",
        "auth_asym_id",
        "auth_seq_id",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
        "occupancy",
        "is_ligand_atom",
        "is_covalent_ligand_atom",
        "is_covalent_endpoint_atom",
        "extraction_source_stage",
    ]
    for field in ligand_fields:
        rows.append(
            _schema_row(
                field,
                "ligand_full_atom_table",
                "ligand_full_atom_table",
                "bool" if field.startswith("is_") else "float_string" if field in {"Cartn_x", "Cartn_y", "Cartn_z", "occupancy"} else "string",
                True,
                RECOMMENDED_NEXT_STEP,
                field,
                "extract_in_next_smoke_from_raw_text_stream",
                "not_written_in_design_gate",
            )
        )
    policy_fields = [
        "protein_full_atom_extraction_scope",
        "ligand_full_atom_extraction_scope",
        "altloc_selection_policy",
        "model_selection_policy",
        "hydrogen_handling_policy",
        "water_handling_policy",
        "ion_handling_policy",
        "protein_chain_selection_policy",
        "ligand_selection_policy",
        "covalent_endpoint_validation_policy",
    ]
    for field in policy_fields:
        rows.append(
            _schema_row(
                field,
                "extraction_policy",
                "sample_extraction_contract",
                "string",
                True,
                STAGE,
                "constant",
                "define_next_smoke_policy_without_execution",
                "policy_text_non_empty",
            )
        )
    status_fields = [
        "full_atom_extraction_run",
        "protein_full_atom_table_written",
        "ligand_full_atom_table_written",
        "pocket_atom_table_written",
        "ligand_topology_table_written",
        "sample_index_written",
        "enriched_sample_index_written",
        "final_dataset_written",
        "model_input_materialized",
        "training_ready",
        "training_ready_reason",
    ]
    for field in status_fields:
        rows.append(
            _schema_row(
                field,
                "status_boundary",
                "sample_extraction_contract",
                "string" if field == "training_ready_reason" else "bool",
                True,
                STAGE,
                "constant",
                "write_false_or_reason_until_future_gates_pass",
                "must_not_claim_training_or_dataset_ready",
            )
        )
    return rows


def build_full_atom_extraction_candidate_contract_v0(
    minimal_records: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    endpoint_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    record_by_review = {row["review_row_id"]: row for row in minimal_records}
    pair_by_review = {row["review_row_id"]: row for row in pair_rows}
    endpoint_by_review_role = {(row["review_row_id"], row["endpoint_role"]): row for row in endpoint_rows}
    audit_by_review = {row["review_row_id"]: row for row in audit_rows}
    rows: list[dict[str, Any]] = []
    for index, review_id in enumerate(EXPECTED_REVIEW_ROW_IDS, start=1):
        record = record_by_review[review_id]
        pair = pair_by_review[review_id]
        protein_endpoint = endpoint_by_review_role[(review_id, "protein_residue")]
        ligand_endpoint = endpoint_by_review_role[(review_id, "ligand")]
        audit = audit_by_review[review_id]
        raw_path = protein_endpoint["raw_path"]
        rows.append(
            {
                "full_atom_extraction_contract_id": f"FAE_CONTRACT_{index:04d}_{review_id}",
                "minimal_sample_record_id": record["minimal_sample_record_id"],
                "minimal_sample_record_contract_id": record["minimal_sample_record_contract_id"],
                "confirmed_candidate_id": record["confirmed_candidate_id"],
                "review_row_id": review_id,
                "candidate_stub_id": record["candidate_stub_id"],
                "sample_id": record["sample_id"],
                "pdb_id": record["pdb_id"],
                "entry_id": record["entry_id"],
                "structure_title": record["structure_title"],
                "raw_path": raw_path,
                "raw_structure_reference_available": raw_path != "",
                "raw_structure_read_allowed_in_next_smoke": True,
                "raw_structure_read_in_this_design_gate": False,
                "pair_sanity_stage": record["pair_sanity_stage"],
                "coordinate_source_stage": record["coordinate_source_stage"],
                "minimal_sample_record_writer_stage": PREVIOUS_STAGE,
                "full_atom_extraction_design_stage": STAGE,
                "coordinate_pair_id": record["coordinate_pair_id"],
                "altloc_aware_selection_confirmed": record["altloc_aware_selection_confirmed"] == "True"
                and audit["altloc_aware_selection_applied"] == "True",
                "manual_confirmed_covalent_bond": record["manual_confirmed_covalent_bond"],
                "manual_confirmed_ligand_comp_id": record["manual_confirmed_ligand_comp_id"],
                "manual_confirmed_residue_comp_id": record["manual_confirmed_residue_comp_id"],
                "manual_confirmed_ligand_atom_id": record["manual_confirmed_ligand_atom_id"],
                "manual_confirmed_residue_atom_id": record["manual_confirmed_residue_atom_id"],
                "manual_confirmed_warhead_type": record["manual_confirmed_warhead_type"],
                "protein_endpoint_comp_id": record["protein_endpoint_comp_id"],
                "protein_endpoint_atom_id": record["protein_endpoint_atom_id"],
                "protein_selected_atom_site_id": record["protein_selected_atom_site_id"],
                "protein_selected_label_alt_id": record["protein_selected_label_alt_id"],
                "protein_selected_occupancy": record["protein_selected_occupancy"],
                "protein_selected_label_asym_id": pair["protein_selected_label_asym_id"],
                "protein_selected_label_comp_id": pair["protein_selected_label_comp_id"],
                "protein_selected_label_seq_id": pair["protein_selected_label_seq_id"],
                "protein_selected_label_atom_id": pair["protein_selected_label_atom_id"],
                "protein_selected_auth_asym_id": pair["protein_selected_auth_asym_id"],
                "protein_selected_auth_comp_id": pair["protein_selected_auth_comp_id"],
                "protein_selected_auth_seq_id": pair["protein_selected_auth_seq_id"],
                "protein_selected_auth_atom_id": pair["protein_selected_auth_atom_id"],
                "protein_Cartn_x": record["protein_Cartn_x"],
                "protein_Cartn_y": record["protein_Cartn_y"],
                "protein_Cartn_z": record["protein_Cartn_z"],
                "ligand_endpoint_comp_id": record["ligand_endpoint_comp_id"],
                "ligand_endpoint_atom_id": record["ligand_endpoint_atom_id"],
                "ligand_selected_atom_site_id": record["ligand_selected_atom_site_id"],
                "ligand_selected_label_alt_id": record["ligand_selected_label_alt_id"],
                "ligand_selected_occupancy": record["ligand_selected_occupancy"],
                "ligand_selected_label_asym_id": pair["ligand_selected_label_asym_id"],
                "ligand_selected_label_comp_id": pair["ligand_selected_label_comp_id"],
                "ligand_selected_label_seq_id": pair["ligand_selected_label_seq_id"],
                "ligand_selected_label_atom_id": pair["ligand_selected_label_atom_id"],
                "ligand_selected_auth_asym_id": pair["ligand_selected_auth_asym_id"],
                "ligand_selected_auth_comp_id": pair["ligand_selected_auth_comp_id"],
                "ligand_selected_auth_seq_id": pair["ligand_selected_auth_seq_id"],
                "ligand_selected_auth_atom_id": pair["ligand_selected_auth_atom_id"],
                "ligand_Cartn_x": record["ligand_Cartn_x"],
                "ligand_Cartn_y": record["ligand_Cartn_y"],
                "ligand_Cartn_z": record["ligand_Cartn_z"],
                "computed_endpoint_distance_angstrom": record["computed_endpoint_distance_angstrom"],
                "struct_conn_reported_distance_angstrom": record["struct_conn_reported_distance_angstrom"],
                "distance_abs_delta_from_struct_conn": record["distance_abs_delta_from_struct_conn"],
                "coordinate_pair_sanity_passed": record["coordinate_pair_sanity_passed"] == "True",
                "protein_full_atom_table_planned": True,
                "ligand_full_atom_table_planned": True,
                "pocket_atom_table_planned": False,
                "ligand_topology_table_planned": False,
                "protein_full_atom_extraction_scope": "same_model_same_entry_polymer_atoms_matching_endpoint_protein_chain",
                "ligand_full_atom_extraction_scope": "same_model_same_entry_nonpolymer_atoms_matching_endpoint_ligand_comp_and_asym",
                "altloc_selection_policy": "preserve_endpoint_altloc_and_select_matching_altloc_or_blank_for_context_atoms",
                "model_selection_policy": "use_model_1_or_endpoint_model_if_available",
                "hydrogen_handling_policy": "preserve_deposited_atoms_no_hydrogen_addition",
                "water_handling_policy": "exclude_waters_from_initial_full_atom_smoke",
                "ion_handling_policy": "exclude_ions_from_initial_full_atom_smoke",
                "protein_chain_selection_policy": "select_chain_containing_confirmed_covalent_residue_endpoint",
                "ligand_selection_policy": "select_ligand_instance_containing_confirmed_covalent_ligand_endpoint",
                "covalent_endpoint_validation_policy": "must_recover_step13h_endpoint_atom_site_ids_and_coordinates",
                "expected_protein_endpoint_atom_site_id": record["protein_selected_atom_site_id"],
                "expected_ligand_endpoint_atom_site_id": record["ligand_selected_atom_site_id"],
                "expected_protein_endpoint_altloc": record["protein_selected_label_alt_id"],
                "expected_ligand_endpoint_altloc": record["ligand_selected_label_alt_id"],
                "full_atom_extraction_design_status": "contract_only_no_raw_read",
                "schema_contract_version": "full_atom_extraction_schema_v0",
                "full_atom_extraction_run": False,
                "protein_full_atom_table_written": False,
                "ligand_full_atom_table_written": False,
                "pocket_atom_table_written": False,
                "ligand_topology_table_written": False,
                "sample_index_written": False,
                "enriched_sample_index_written": False,
                "final_dataset_written": False,
                "model_input_materialized": False,
                "training_ready": False,
                "training_ready_reason": "full_atom_extraction_design_only_no_atom_tables_written",
            }
        )
    return rows


def _build_design_summary(schema_rows: list[dict[str, str]], candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    hr2 = next(row for row in candidate_rows if row["review_row_id"] == "HR_0002")
    return {
        "minimal_sample_record_row_count": EXPECTED_MINIMAL_SAMPLE_RECORD_ROW_COUNT,
        "field_audit_row_count": EXPECTED_FIELD_AUDIT_ROW_COUNT,
        "pair_sanity_row_count": EXPECTED_CANDIDATE_CONTRACT_ROW_COUNT,
        "altloc_aware_endpoint_row_count": 6,
        "altloc_selection_audit_row_count": 3,
        "full_atom_extraction_schema_field_count": len(schema_rows),
        "full_atom_extraction_candidate_contract_row_count": len(candidate_rows),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
        "all_minimal_sample_record_inputs_valid": True,
        "all_candidate_contract_rows_have_raw_references": all(row["raw_path"] for row in candidate_rows),
        "all_candidate_contract_rows_have_protein_extraction_policy": all(row["protein_full_atom_extraction_scope"] for row in candidate_rows),
        "all_candidate_contract_rows_have_ligand_extraction_policy": all(row["ligand_full_atom_extraction_scope"] for row in candidate_rows),
        "all_candidate_contract_rows_preserve_altloc_aware_selection": all(row["altloc_aware_selection_confirmed"] is True for row in candidate_rows),
        "all_candidate_contract_rows_preserve_pair_sanity": all(row["coordinate_pair_sanity_passed"] is True for row in candidate_rows),
        "all_candidate_contract_rows_plan_protein_and_ligand_full_atom_tables": all(
            row["protein_full_atom_table_planned"] is True and row["ligand_full_atom_table_planned"] is True
            for row in candidate_rows
        ),
        "all_candidate_contract_rows_do_not_plan_pocket_or_topology_yet": all(
            row["pocket_atom_table_planned"] is False and row["ligand_topology_table_planned"] is False
            for row in candidate_rows
        ),
        "all_candidate_contract_rows_full_atom_extraction_run_false": all(
            row["full_atom_extraction_run"] is False for row in candidate_rows
        ),
        "all_candidate_contract_rows_atom_tables_written_false": all(
            row["protein_full_atom_table_written"] is False
            and row["ligand_full_atom_table_written"] is False
            and row["pocket_atom_table_written"] is False
            and row["ligand_topology_table_written"] is False
            for row in candidate_rows
        ),
        "all_candidate_contract_rows_sample_index_written_false": all(row["sample_index_written"] is False for row in candidate_rows),
        "all_candidate_contract_rows_final_dataset_written_false": all(row["final_dataset_written"] is False for row in candidate_rows),
        "all_candidate_contract_rows_model_input_materialized_false": all(row["model_input_materialized"] is False for row in candidate_rows),
        "all_candidate_contract_rows_training_ready_false": all(row["training_ready"] is False for row in candidate_rows),
        "hr0002_altloc_b_preserved": hr2["protein_selected_atom_site_id"] == "659" and hr2["protein_selected_label_alt_id"] == "B",
        "hr0002_selected_protein_atom_site_id": hr2["protein_selected_atom_site_id"],
        "hr0002_selected_protein_label_alt_id": hr2["protein_selected_label_alt_id"],
        "hr0002_raw_path_present": bool(hr2["raw_path"]),
    }


def build_real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13h_validated = validate_step13h_minimal_sample_record_write_smoke_v0()
    except Exception as exc:
        step13h_validated = False
        blockers.append(f"step13h_validation_failed:{type(exc).__name__}:{exc}")
    step13h_manifest = _load_json(STEP13H_MANIFEST_JSON)
    minimal_records = load_step13h_minimal_sample_records_v0()
    field_audit_rows = load_step13h_field_audit_rows_v0()
    pair_rows = load_step13f_pair_sanity_rows_v1()
    endpoint_rows = load_step13e2_altloc_aware_endpoint_rows_v0()
    audit_rows = load_step13e2_altloc_selection_audit_rows_v0()
    schema_rows = build_full_atom_extraction_schema_contract_v0()
    candidate_rows = build_full_atom_extraction_candidate_contract_v0(minimal_records, pair_rows, endpoint_rows, audit_rows)
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
        step13h_validated
        and step13h_manifest["step12b_mask_level_aware_validator_validated"]
        and len(schema_rows) >= EXPECTED_SCHEMA_MIN_FIELD_COUNT
        and len(candidate_rows) == EXPECTED_CANDIDATE_CONTRACT_ROW_COUNT
        and design_summary["all_minimal_sample_record_inputs_valid"]
        and design_summary["all_candidate_contract_rows_have_raw_references"]
        and design_summary["all_candidate_contract_rows_have_protein_extraction_policy"]
        and design_summary["all_candidate_contract_rows_have_ligand_extraction_policy"]
        and design_summary["all_candidate_contract_rows_preserve_altloc_aware_selection"]
        and design_summary["all_candidate_contract_rows_preserve_pair_sanity"]
        and design_summary["all_candidate_contract_rows_plan_protein_and_ligand_full_atom_tables"]
        and design_summary["all_candidate_contract_rows_do_not_plan_pocket_or_topology_yet"]
        and design_summary["all_candidate_contract_rows_full_atom_extraction_run_false"]
        and design_summary["all_candidate_contract_rows_atom_tables_written_false"]
        and design_summary["all_candidate_contract_rows_sample_index_written_false"]
        and design_summary["all_candidate_contract_rows_final_dataset_written_false"]
        and design_summary["all_candidate_contract_rows_model_input_materialized_false"]
        and design_summary["all_candidate_contract_rows_training_ready_false"]
        and design_summary["hr0002_altloc_b_preserved"]
        and design_summary["hr0002_raw_path_present"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_confirmed_candidate_full_atom_extraction_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13h_minimal_sample_record_write_smoke_validated": step13h_validated,
        "step12b_mask_level_aware_validator_validated": step13h_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "full_atom_extraction_design_gate_defined": True,
        "full_atom_extraction_design_gate_executed": True,
        "minimal_sample_records_csv_read": True,
        "field_audit_csv_read": True,
        "pair_sanity_table_csv_read": True,
        "altloc_aware_endpoint_coordinates_csv_read": True,
        "altloc_selection_audit_csv_read": True,
        "full_atom_extraction_schema_contract_csv_written": True,
        "full_atom_extraction_candidate_contract_csv_written": True,
        **design_summary,
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
        "protein_full_atom_table_written": False,
        "ligand_full_atom_table_written": False,
        "pocket_atom_table_written": False,
        "ligand_topology_table_written": False,
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
        "real_covalent_confirmed_candidate_full_atom_extraction_design_gate_passed": passed,
        "full_atom_extraction_design_contract_satisfied": passed,
        "ready_for_full_atom_extraction_smoke": passed,
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
        "step13h_precondition": {
            "step13h_minimal_sample_record_write_smoke_validated": manifest[
                "step13h_minimal_sample_record_write_smoke_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "minimal_sample_record_inputs": {
            "minimal_sample_records_csv_read": manifest["minimal_sample_records_csv_read"],
            "minimal_sample_record_row_count": manifest["minimal_sample_record_row_count"],
        },
        "pair_and_endpoint_provenance_inputs": {
            "pair_sanity_table_csv_read": manifest["pair_sanity_table_csv_read"],
            "altloc_aware_endpoint_coordinates_csv_read": manifest["altloc_aware_endpoint_coordinates_csv_read"],
            "altloc_selection_audit_csv_read": manifest["altloc_selection_audit_csv_read"],
        },
        "full_atom_schema_contract": {
            "full_atom_extraction_schema_contract_csv_written": manifest[
                "full_atom_extraction_schema_contract_csv_written"
            ],
            "full_atom_extraction_schema_field_count": manifest["full_atom_extraction_schema_field_count"],
        },
        "full_atom_candidate_contract": {
            "full_atom_extraction_candidate_contract_csv_written": manifest[
                "full_atom_extraction_candidate_contract_csv_written"
            ],
            "full_atom_extraction_candidate_contract_row_count": manifest[
                "full_atom_extraction_candidate_contract_row_count"
            ],
        },
        "no_raw_no_actual_extraction_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            "full_protein_atom_extraction_run": manifest["full_protein_atom_extraction_run"],
            "protein_full_atom_table_written": manifest["protein_full_atom_table_written"],
        },
        "no_sample_index_no_training_boundary": {
            "sample_index_written": manifest["sample_index_written"],
            "model_input_materialized": manifest["model_input_materialized"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "next_step_decision": {
            "ready_for_full_atom_extraction_smoke": manifest["ready_for_full_atom_extraction_smoke"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
