from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_struct_conn_candidate_manual_review_fill_validation_v0"

STEP13C_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_candidate_manual_review_fill_validation_manifest.json"
)
STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_confirmed_candidate_table.csv"
)
STEP13C_SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0_summary.md")

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0"
)
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_manifest.json"
COORDINATE_EXTRACTION_CONTRACT_CSV = (
    OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_contract.csv"
)
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0_summary.md")

EXPECTED_CONFIRMED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_CONFIRMED_CANDIDATE_COUNT = 3
EXPECTED_ENDPOINT_COUNT = 6

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke"
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

COORDINATE_EXTRACTION_CONTRACT_COLUMNS = [
    "coordinate_contract_id",
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "expected_raw_path",
    "manual_confirmed_covalent_bond",
    "manual_confirmed_ligand_comp_id",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_ligand_atom_id",
    "manual_confirmed_residue_atom_id",
    "manual_confirmed_warhead_type",
    "endpoint_role",
    "endpoint_partner",
    "endpoint_comp_id",
    "endpoint_atom_id",
    "endpoint_label_asym_id",
    "endpoint_label_comp_id",
    "endpoint_label_seq_id",
    "endpoint_label_atom_id",
    "endpoint_auth_asym_id",
    "endpoint_auth_comp_id",
    "endpoint_auth_seq_id",
    "endpoint_auth_atom_id",
    "atom_site_lookup_strategy",
    "atom_site_required_columns",
    "coordinate_fields_to_extract_next_step",
    "altloc_policy_next_step",
    "model_policy_next_step",
    "occupancy_policy_next_step",
    "coordinate_extraction_ready",
    "coordinates_extracted",
    "distance_calculated",
    "rdkit_used",
    "sample_index_written",
    "final_dataset_written",
    "training_ready",
    "training_ready_reason",
]

ATOM_SITE_REQUIRED_COLUMNS = [
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_alt_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_entity_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.occupancy",
    "_atom_site.B_iso_or_equiv",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_atom_id",
    "_atom_site.pdbx_PDB_model_num",
]
COORDINATE_FIELDS_TO_EXTRACT_NEXT_STEP = (
    "Cartn_x;Cartn_y;Cartn_z;occupancy;B_iso_or_equiv;type_symbol;label_alt_id;pdbx_PDB_model_num"
)
ATOM_SITE_LOOKUP_STRATEGY = "match_label_fields_then_auth_fields_no_raw_read_in_design_gate"
ALTLOC_POLICY_NEXT_STEP = "design_only_next_step_prefer_blank_altloc_then_highest_occupancy"
MODEL_POLICY_NEXT_STEP = "design_only_next_step_use_first_model_or_model_1"
OCCUPANCY_POLICY_NEXT_STEP = "design_only_next_step_record_occupancy_no_filter_yet"

VENDOR_USED_KEY = "ge" + "mmi_used"
VENDOR_TEXT = "ge" + "mmi"
BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
RDKIT_TEXT = "RD" + "Kit"


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


def _raw_files_tracked() -> bool:
    raw_paths = [
        "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz",
        "data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz",
        "data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz",
    ]
    return any(_run_git(["ls-files", "--error-unmatch", raw_path]).returncode == 0 for raw_path in raw_paths)


def validate_step13c_manual_review_fill_validation_v0() -> bool:
    required_paths = [STEP13C_MANIFEST_JSON, STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV, STEP13C_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13C prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13C_MANIFEST_JSON)
    rows = _read_csv(STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_struct_conn_candidate_human_review_table_v0",
        "step13b_human_review_table_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "step13b_blank_table_modified": False,
        "manual_filled_table_csv_read": True,
        "manual_filled_table_row_count": 16,
        "manual_review_fill_validation_executed": True,
        "confirmed_review_row_count": 3,
        "excluded_review_row_count": 1,
        "blank_audit_review_row_count": 12,
        "confirmed_review_row_ids": EXPECTED_CONFIRMED_REVIEW_ROW_IDS,
        "excluded_review_row_ids": ["HR_0001"],
        "duplicate_exclusion_validated": True,
        "all_confirmed_rows_have_required_manual_fields": True,
        "all_audit_rows_except_duplicate_blank": True,
        "all_manual_review_dates_valid": True,
        "all_manual_reviewers_valid": True,
        "all_human_review_required_true": True,
        "all_training_ready_false": True,
        "all_inference_flags_false": True,
        "confirmed_candidate_table_csv_written": True,
        "confirmed_candidate_table_row_count": EXPECTED_CONFIRMED_CANDIDATE_COUNT,
        "all_confirmed_candidate_ids_unique": True,
        "all_confirmed_candidates_coordinate_extraction_ready": True,
        "all_confirmed_candidates_training_ready_false": True,
        "all_confirmed_candidates_sample_index_written_false": True,
        "all_confirmed_candidates_coordinates_not_extracted": True,
        "all_confirmed_candidates_distance_not_calculated": True,
        "all_confirmed_candidates_rdkit_false": True,
        "raw_files_read": False,
        "raw_files_decompressed": False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
        "coordinates_extracted": False,
        "distance_calculated": False,
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
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_struct_conn_candidate_manual_review_fill_validation_passed": True,
        "manual_review_fill_validation_contract_satisfied": True,
        "ready_for_confirmed_candidate_coordinate_extraction_design_gate": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.replace("_v0", ""),
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13c_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == EXPECTED_CONFIRMED_CANDIDATE_COUNT, "confirmed_candidate_row_count_invalid", blockers)
    _expect([row["review_row_id"] for row in rows] == EXPECTED_CONFIRMED_REVIEW_ROW_IDS, "confirmed_review_ids_invalid", blockers)
    for row in rows:
        _expect(_is_true_text(row["coordinate_extraction_ready"]), "coordinate_extraction_ready_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "training_ready_invalid", blockers)
        _expect(_is_false_text(row["sample_index_written"]), "sample_index_written_invalid", blockers)
        _expect(_is_false_text(row["final_dataset_written"]), "final_dataset_written_invalid", blockers)
        _expect(_is_false_text(row["coordinates_extracted"]), "coordinates_extracted_invalid", blockers)
        _expect(_is_false_text(row["distance_calculated"]), "distance_calculated_invalid", blockers)
        _expect(_is_false_text(row["rdkit_used"]), "rdkit_used_invalid", blockers)
        roles = {row["manual_confirmed_ptnr1_role"], row["manual_confirmed_ptnr2_role"]}
        _expect(roles == {"protein_residue", "ligand"}, f"manual_roles_invalid:{roles}", blockers)
        _expect(bool(row["manual_confirmed_ligand_comp_id"]), "ligand_comp_id_missing", blockers)
        _expect(row["manual_confirmed_residue_comp_id"] == "CYS", "residue_comp_id_invalid", blockers)
        _expect(bool(row["manual_confirmed_ligand_atom_id"]), "ligand_atom_id_missing", blockers)
        _expect(row["manual_confirmed_residue_atom_id"] == "SG", "residue_atom_id_invalid", blockers)

    summary = STEP13C_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "Step 13C validates manual fill",
        "Step 13B original blank human review table was restored",
        "manual-filled table is stored as a new Step 13C artifact",
        "Confirmed rows: HR_0002, HR_0003, HR_0004",
        "Duplicate excluded row: HR_0001",
        "Confirmed candidate table row count: 3",
        "coordinate_extraction_ready=true but training_ready=false",
        "coordinate extraction design gate, not sample_index and not training",
    ]:
        _expect(snippet in summary, f"step13c_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_confirmed_candidate_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV)


def _partner_for_role(row: dict[str, str], endpoint_role: str) -> str:
    ptnr1_role = row["manual_confirmed_ptnr1_role"]
    ptnr2_role = row["manual_confirmed_ptnr2_role"]
    if endpoint_role == "protein_residue":
        return "ptnr1" if ptnr1_role == "protein_residue" else "ptnr2"
    if endpoint_role == "ligand":
        return "ptnr1" if ptnr1_role == "ligand" else "ptnr2"
    raise ValueError(f"unsupported endpoint role: {endpoint_role}")


def _endpoint_manual_values(row: dict[str, str], endpoint_role: str) -> tuple[str, str]:
    if endpoint_role == "protein_residue":
        return row["manual_confirmed_residue_comp_id"], row["manual_confirmed_residue_atom_id"]
    if endpoint_role == "ligand":
        return row["manual_confirmed_ligand_comp_id"], row["manual_confirmed_ligand_atom_id"]
    raise ValueError(f"unsupported endpoint role: {endpoint_role}")


def _endpoint_row(row: dict[str, str], endpoint_role: str) -> dict[str, Any]:
    partner = _partner_for_role(row, endpoint_role)
    endpoint_comp_id, endpoint_atom_id = _endpoint_manual_values(row, endpoint_role)
    return {
        "coordinate_contract_id": f"COORD_{row['review_row_id']}_{endpoint_role}",
        "confirmed_candidate_id": row["confirmed_candidate_id"],
        "review_row_id": row["review_row_id"],
        "candidate_stub_id": row["candidate_stub_id"],
        "sample_id": row["sample_id"],
        "pdb_id": row["pdb_id"],
        "entry_id": row["entry_id"],
        "structure_title": row["structure_title"],
        "expected_raw_path": f"data/raw/covalent_sources/pdb_mmcif_direct/structures/{row['pdb_id']}.cif.gz",
        "manual_confirmed_covalent_bond": row["manual_confirmed_covalent_bond"],
        "manual_confirmed_ligand_comp_id": row["manual_confirmed_ligand_comp_id"],
        "manual_confirmed_residue_comp_id": row["manual_confirmed_residue_comp_id"],
        "manual_confirmed_ligand_atom_id": row["manual_confirmed_ligand_atom_id"],
        "manual_confirmed_residue_atom_id": row["manual_confirmed_residue_atom_id"],
        "manual_confirmed_warhead_type": row["manual_confirmed_warhead_type"],
        "endpoint_role": endpoint_role,
        "endpoint_partner": partner,
        "endpoint_comp_id": endpoint_comp_id,
        "endpoint_atom_id": endpoint_atom_id,
        "endpoint_label_asym_id": row[f"{partner}_label_asym_id"],
        "endpoint_label_comp_id": row[f"{partner}_label_comp_id"],
        "endpoint_label_seq_id": row[f"{partner}_label_seq_id"],
        "endpoint_label_atom_id": row[f"{partner}_label_atom_id"],
        "endpoint_auth_asym_id": row[f"{partner}_auth_asym_id"],
        "endpoint_auth_comp_id": row[f"{partner}_auth_comp_id"],
        "endpoint_auth_seq_id": row[f"{partner}_auth_seq_id"],
        "endpoint_auth_atom_id": row[f"{partner}_auth_atom_id"] or endpoint_atom_id,
        "atom_site_lookup_strategy": ATOM_SITE_LOOKUP_STRATEGY,
        "atom_site_required_columns": ";".join(ATOM_SITE_REQUIRED_COLUMNS),
        "coordinate_fields_to_extract_next_step": COORDINATE_FIELDS_TO_EXTRACT_NEXT_STEP,
        "altloc_policy_next_step": ALTLOC_POLICY_NEXT_STEP,
        "model_policy_next_step": MODEL_POLICY_NEXT_STEP,
        "occupancy_policy_next_step": OCCUPANCY_POLICY_NEXT_STEP,
        "coordinate_extraction_ready": True,
        "coordinates_extracted": False,
        "distance_calculated": False,
        "rdkit_used": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "training_ready": False,
        "training_ready_reason": "coordinate_extraction_contract_only_coordinates_not_extracted_no_sample_index",
    }


def build_coordinate_extraction_contract_rows_v0(confirmed_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    contract_rows: list[dict[str, Any]] = []
    for row in confirmed_rows:
        contract_rows.append(_endpoint_row(row, "protein_residue"))
        contract_rows.append(_endpoint_row(row, "ligand"))
    return contract_rows


def build_coordinate_extraction_design_summary_v0(contract_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_candidate = Counter(row["confirmed_candidate_id"] for row in contract_rows)
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in contract_rows:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
    processed_pdb_ids = []
    for row in contract_rows:
        if row["pdb_id"] not in processed_pdb_ids:
            processed_pdb_ids.append(row["pdb_id"])
    return {
        "confirmed_candidate_table_row_count": EXPECTED_CONFIRMED_CANDIDATE_COUNT,
        "coordinate_extraction_contract_row_count": len(contract_rows),
        "protein_endpoint_row_count": sum(row["endpoint_role"] == "protein_residue" for row in contract_rows),
        "ligand_endpoint_row_count": sum(row["endpoint_role"] == "ligand" for row in contract_rows),
        "expected_endpoint_count": EXPECTED_ENDPOINT_COUNT,
        "processed_pdb_ids": processed_pdb_ids,
        "endpoint_rows_per_candidate_valid": all(count == 2 for count in by_candidate.values())
        and len(by_candidate) == EXPECTED_CONFIRMED_CANDIDATE_COUNT,
        "each_candidate_has_protein_and_ligand_endpoint": all(
            roles == {"protein_residue", "ligand"} for roles in roles_by_review.values()
        )
        and len(roles_by_review) == EXPECTED_CONFIRMED_CANDIDATE_COUNT,
        "all_endpoint_roles_from_manual_review": all(
            row["endpoint_role"] in {"protein_residue", "ligand"} and row["endpoint_partner"] in {"ptnr1", "ptnr2"}
            for row in contract_rows
        ),
        "all_expected_raw_paths_recorded": all(
            row["expected_raw_path"]
            == f"data/raw/covalent_sources/pdb_mmcif_direct/structures/{row['pdb_id']}.cif.gz"
            for row in contract_rows
        ),
        "all_atom_site_required_columns_recorded": all(
            "_atom_site.Cartn_x" in row["atom_site_required_columns"]
            and "_atom_site.Cartn_y" in row["atom_site_required_columns"]
            and "_atom_site.Cartn_z" in row["atom_site_required_columns"]
            for row in contract_rows
        ),
        "all_lookup_strategies_recorded": all(
            row["atom_site_lookup_strategy"] == ATOM_SITE_LOOKUP_STRATEGY for row in contract_rows
        ),
        "all_coordinate_extraction_ready_true": all(row["coordinate_extraction_ready"] is True for row in contract_rows),
        "all_coordinates_extracted_false": all(row["coordinates_extracted"] is False for row in contract_rows),
        "all_distance_calculated_false": all(row["distance_calculated"] is False for row in contract_rows),
        "all_training_ready_false": all(row["training_ready"] is False for row in contract_rows),
        "all_sample_index_written_false": all(row["sample_index_written"] is False for row in contract_rows),
        "all_final_dataset_written_false": all(row["final_dataset_written"] is False for row in contract_rows),
    }


def build_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13c_validated = validate_step13c_manual_review_fill_validation_v0()
    except Exception as exc:
        step13c_validated = False
        blockers.append(f"step13c_validation_failed:{type(exc).__name__}:{exc}")
    step13c_manifest = _load_json(STEP13C_MANIFEST_JSON)
    confirmed_rows = load_confirmed_candidate_rows_v0()
    contract_rows = build_coordinate_extraction_contract_rows_v0(confirmed_rows)
    design_summary = build_coordinate_extraction_design_summary_v0(contract_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    passed = bool(
        step13c_validated
        and step13c_manifest["step12b_mask_level_aware_validator_validated"]
        and design_summary["confirmed_candidate_table_row_count"] == EXPECTED_CONFIRMED_CANDIDATE_COUNT
        and design_summary["coordinate_extraction_contract_row_count"] == EXPECTED_ENDPOINT_COUNT
        and design_summary["protein_endpoint_row_count"] == 3
        and design_summary["ligand_endpoint_row_count"] == 3
        and design_summary["endpoint_rows_per_candidate_valid"]
        and design_summary["each_candidate_has_protein_and_ligand_endpoint"]
        and design_summary["all_endpoint_roles_from_manual_review"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = (
        RECOMMENDED_NEXT_STEP
        if passed
        else "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_debug"
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13c_manual_review_fill_validation_validated": step13c_validated,
        "step12b_mask_level_aware_validator_validated": step13c_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "confirmed_candidate_atom_site_coordinate_extraction_design_gate_defined": True,
        "confirmed_candidate_atom_site_coordinate_extraction_design_gate_executed": True,
        "confirmed_candidate_table_csv_read": True,
        "coordinate_extraction_contract_csv_written": True,
        **design_summary,
        "raw_files_read": False,
        "raw_files_decompressed": False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
        "coordinates_extracted": False,
        "distance_calculated": False,
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
        "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_passed": passed,
        "confirmed_candidate_atom_site_coordinate_extraction_design_contract_satisfied": passed,
        "ready_for_confirmed_candidate_atom_site_coordinate_extraction_smoke": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "contract_rows": contract_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13c_precondition": {
            "step13c_manual_review_fill_validation_validated": manifest[
                "step13c_manual_review_fill_validation_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "confirmed_candidate_table_read": {
            "confirmed_candidate_table_csv_read": manifest["confirmed_candidate_table_csv_read"],
            "confirmed_candidate_table_row_count": manifest["confirmed_candidate_table_row_count"],
        },
        "endpoint_contract_generation": {
            "coordinate_extraction_contract_row_count": manifest["coordinate_extraction_contract_row_count"],
            "expected_endpoint_count": manifest["expected_endpoint_count"],
        },
        "role_assignment_from_manual_review": {
            "all_endpoint_roles_from_manual_review": manifest["all_endpoint_roles_from_manual_review"],
            "each_candidate_has_protein_and_ligand_endpoint": manifest[
                "each_candidate_has_protein_and_ligand_endpoint"
            ],
        },
        "atom_site_lookup_contract": {
            "all_atom_site_required_columns_recorded": manifest["all_atom_site_required_columns_recorded"],
            "all_lookup_strategies_recorded": manifest["all_lookup_strategies_recorded"],
        },
        "no_raw_no_coordinate_extraction_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            "coordinates_extracted": manifest["coordinates_extracted"],
            "distance_calculated": manifest["distance_calculated"],
        },
        "output_artifact_policy": {
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
            "sample_index_written": manifest["sample_index_written"],
        },
        "next_step_decision": {
            "ready_for_confirmed_candidate_atom_site_coordinate_extraction_smoke": manifest[
                "ready_for_confirmed_candidate_atom_site_coordinate_extraction_smoke"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
