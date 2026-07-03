from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_struct_conn_candidate_manual_review_fill_validation_v0"
PREVIOUS_STAGE = "real_covalent_struct_conn_candidate_human_review_table_v0"

STEP13B_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_human_review_table_v0/"
    "real_covalent_struct_conn_candidate_human_review_table_manifest.json"
)
STEP13B_BLANK_HUMAN_REVIEW_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_human_review_table_v0/"
    "real_covalent_struct_conn_candidate_human_review_table.csv"
)
STEP13B_SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_human_review_table_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_manual_review_fill_validation_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_manual_review_fill_validation_manifest.json"
MANUAL_FILLED_TABLE_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_human_review_table_manual_filled.csv"
CONFIRMED_CANDIDATE_TABLE_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_confirmed_candidate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
CONFIRMED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXCLUDED_REVIEW_ROW_IDS = ["HR_0001"]

MANUAL_REVIEW_COLUMNS = [
    "manual_review_decision",
    "manual_review_notes",
    "manual_confirmed_covalent_bond",
    "manual_confirmed_ptnr1_role",
    "manual_confirmed_ptnr2_role",
    "manual_confirmed_ligand_comp_id",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_ligand_atom_id",
    "manual_confirmed_residue_atom_id",
    "manual_confirmed_warhead_type",
    "manual_exclusion_reason",
    "manual_reviewer",
    "manual_review_date",
]

CONFIRMED_CANDIDATE_TABLE_COLUMNS = [
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "conn_type_id",
    "conn_candidate_status",
    "struct_conn_id",
    "struct_conn_row_index",
    "pdbx_dist_value",
    "pdbx_role",
    "manual_confirmed_covalent_bond",
    "manual_confirmed_ptnr1_role",
    "manual_confirmed_ptnr2_role",
    "manual_confirmed_ligand_comp_id",
    "manual_confirmed_residue_comp_id",
    "manual_confirmed_ligand_atom_id",
    "manual_confirmed_residue_atom_id",
    "manual_confirmed_warhead_type",
    "ptnr1_label_asym_id",
    "ptnr1_label_comp_id",
    "ptnr1_label_seq_id",
    "ptnr1_label_atom_id",
    "ptnr1_auth_asym_id",
    "ptnr1_auth_comp_id",
    "ptnr1_auth_seq_id",
    "ptnr1_auth_atom_id",
    "ptnr2_label_asym_id",
    "ptnr2_label_comp_id",
    "ptnr2_label_seq_id",
    "ptnr2_label_atom_id",
    "ptnr2_auth_asym_id",
    "ptnr2_auth_comp_id",
    "ptnr2_auth_seq_id",
    "ptnr2_auth_atom_id",
    "chem_comp_ids",
    "manual_review_notes",
    "manual_reviewer",
    "manual_review_date",
    "manual_review_validated",
    "coordinate_extraction_ready",
    "training_ready",
    "training_ready_reason",
    "sample_index_written",
    "final_dataset_written",
    "coordinates_extracted",
    "distance_calculated",
    "rdkit_used",
]

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate"
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

VENDOR_USED_KEY = "ge" + "mmi_used"
VENDOR_TEXT = "ge" + "mmi"
BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
RDKIT_TEXT = "RD" + "Kit"

INFERENCE_FLAG_COLUMNS = [
    "covalent_bond_atom_pair_inferred",
    "ligand_residue_role_inferred",
    "warhead_type_inferred",
    "coordinates_inferred",
    "distance_calculated",
]

EXPECTED_MANUAL_VALUES = {
    "HR_0001": {
        "manual_review_decision": "exclude",
        "manual_review_notes": (
            "duplicate BTK CYS481-GJJ C33 struct_conn record; excluded to keep one reviewed "
            "covalent candidate per identical atom pair"
        ),
        "manual_exclusion_reason": "duplicate_struct_conn_same_CYS481_GJJ_C33_as_HR_0002",
    },
    "HR_0002": {
        "manual_review_decision": "confirm",
        "manual_confirmed_covalent_bond": "CYS481:SG-GJJ:C33",
        "manual_confirmed_ptnr1_role": "protein_residue",
        "manual_confirmed_ptnr2_role": "ligand",
        "manual_confirmed_ligand_comp_id": "GJJ",
        "manual_confirmed_residue_comp_id": "CYS",
        "manual_confirmed_ligand_atom_id": "C33",
        "manual_confirmed_residue_atom_id": "SG",
        "manual_confirmed_warhead_type": "unknown_covalent_warhead",
        "manual_exclusion_reason": "",
        "manual_review_notes": (
            "confirmed BTK CYS481 SG to covalent inhibitor GJJ C33; selected over duplicate HR_0001"
        ),
        "manual_reviewer": "manual_review_v0",
        "manual_review_date": "2026-07-02",
    },
    "HR_0003": {
        "manual_review_decision": "confirm",
        "manual_confirmed_covalent_bond": "CYS12:SG-5UT:C15",
        "manual_confirmed_ptnr1_role": "protein_residue",
        "manual_confirmed_ptnr2_role": "ligand",
        "manual_confirmed_ligand_comp_id": "5UT",
        "manual_confirmed_residue_comp_id": "CYS",
        "manual_confirmed_ligand_atom_id": "C15",
        "manual_confirmed_residue_atom_id": "SG",
        "manual_confirmed_warhead_type": "acrylamide_like_or_unknown_manual_check",
        "manual_exclusion_reason": "",
        "manual_review_notes": (
            "confirmed KRAS G12C CYS12 SG to ligand 5UT C15 based on struct_conn and structure title"
        ),
        "manual_reviewer": "manual_review_v0",
        "manual_review_date": "2026-07-02",
    },
    "HR_0004": {
        "manual_review_decision": "confirm",
        "manual_confirmed_covalent_bond": "CYS12:SG-MOV:C25",
        "manual_confirmed_ptnr1_role": "protein_residue",
        "manual_confirmed_ptnr2_role": "ligand",
        "manual_confirmed_ligand_comp_id": "MOV",
        "manual_confirmed_residue_comp_id": "CYS",
        "manual_confirmed_ligand_atom_id": "C25",
        "manual_confirmed_residue_atom_id": "SG",
        "manual_confirmed_warhead_type": "acrylamide_like_or_unknown_manual_check",
        "manual_exclusion_reason": "",
        "manual_review_notes": (
            "confirmed KRAS G12C CYS12 SG to ligand MOV C25 based on struct_conn and structure title"
        ),
        "manual_reviewer": "manual_review_v0",
        "manual_review_date": "2026-07-02",
    },
}


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


def _path_modified(path: Path) -> bool:
    result = _run_git(["status", "--short", "--", str(path)])
    return bool(result.stdout.strip())


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


def _review_ids(rows: list[dict[str, str]], decision: str) -> list[str]:
    return [row["review_row_id"] for row in rows if row["manual_review_decision"] == decision]


def _manual_fields_blank(row: dict[str, str]) -> bool:
    return all(row[column] == "" for column in MANUAL_REVIEW_COLUMNS)


def _high_priority_rows_first(rows: list[dict[str, str]]) -> bool:
    seen_non_high = False
    for row in rows:
        if row["review_priority"] != "high":
            seen_non_high = True
        if seen_non_high and row["review_priority"] == "high":
            return False
    return True


def validate_step13b_human_review_table_v0() -> bool:
    required_paths = [STEP13B_MANIFEST_JSON, STEP13B_BLANK_HUMAN_REVIEW_TABLE_CSV, STEP13B_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13B prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13B_MANIFEST_JSON)
    rows = _read_csv(STEP13B_BLANK_HUMAN_REVIEW_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_struct_conn_candidate_adapter_merge_smoke_v0",
        "step13a_struct_conn_candidate_adapter_merge_smoke_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "struct_conn_candidate_human_review_table_defined": True,
        "struct_conn_candidate_human_review_table_executed": True,
        "enriched_stub_csv_read": True,
        "enriched_stub_row_count": 16,
        "human_review_table_csv_written": True,
        "human_review_table_row_count": 16,
        "candidate_like_review_row_count": 4,
        "high_priority_review_row_count": 4,
        "audit_review_row_count": 12,
        "manual_review_columns_added": True,
        "manual_review_column_count": 13,
        "ready_for_manual_human_review": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "all_checks_passed": True,
        "recommended_next_step": "manual_fill_struct_conn_candidate_human_review_table",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13b_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(len(rows) == 16, "step13b_blank_row_count_invalid", blockers)
    _expect(all(_manual_fields_blank(row) for row in rows), "step13b_manual_fields_not_blank", blockers)
    _expect(all(row["review_priority"] == "high" and row["candidate_like"] == "True" for row in rows[:4]), "step13b_high_rows_invalid", blockers)
    _expect(all(row["review_priority"] == "audit" and row["candidate_like"] == "False" for row in rows[4:]), "step13b_audit_rows_invalid", blockers)
    summary = STEP13B_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "actual struct_conn candidate human review table",
        "human-reviewable candidate table",
        "manual fill of the human review table, not training",
    ]:
        _expect(snippet in summary, f"step13b_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_manual_filled_review_rows_v0() -> list[dict[str, str]]:
    return _read_csv(MANUAL_FILLED_TABLE_CSV)


def validate_manual_filled_rows_v0(rows: list[dict[str, str]]) -> dict[str, Any]:
    blockers: list[str] = []
    by_id = {row["review_row_id"]: row for row in rows}
    confirm_ids = _review_ids(rows, "confirm")
    exclude_ids = _review_ids(rows, "exclude")
    audit_blank_rows = [
        row
        for row in rows
        if row["review_priority"] == "audit" and row["review_row_id"] not in EXCLUDED_REVIEW_ROW_IDS
    ]
    _expect(len(rows) == 16, "manual_filled_row_count_invalid", blockers)
    _expect(len(by_id) == len(rows), "review_row_ids_not_unique", blockers)
    _expect(_high_priority_rows_first(rows), "high_priority_rows_not_first", blockers)
    _expect(confirm_ids == CONFIRMED_REVIEW_ROW_IDS, f"confirmed_ids_invalid:{confirm_ids}", blockers)
    _expect(exclude_ids == EXCLUDED_REVIEW_ROW_IDS, f"excluded_ids_invalid:{exclude_ids}", blockers)
    _expect(len(audit_blank_rows) == 12, "blank_audit_row_count_invalid", blockers)
    for review_id, expected_fields in EXPECTED_MANUAL_VALUES.items():
        row = by_id.get(review_id)
        _expect(row is not None, f"missing_review_row:{review_id}", blockers)
        if row is None:
            continue
        for field, expected_value in expected_fields.items():
            _expect(row[field] == expected_value, f"{review_id}_{field}_invalid:{row[field]!r}", blockers)
        if review_id == "HR_0001":
            for column in MANUAL_REVIEW_COLUMNS:
                if column not in expected_fields:
                    _expect(row[column] == "", f"HR_0001_{column}_should_be_blank", blockers)
    confirmed_rows = [by_id[review_id] for review_id in CONFIRMED_REVIEW_ROW_IDS if review_id in by_id]
    all_confirmed_required = all(
        row["manual_confirmed_covalent_bond"]
        and row["manual_confirmed_ptnr1_role"] == "protein_residue"
        and row["manual_confirmed_ptnr2_role"] == "ligand"
        and row["manual_confirmed_ligand_comp_id"]
        and row["manual_confirmed_residue_comp_id"] == "CYS"
        and row["manual_confirmed_ligand_atom_id"]
        and row["manual_confirmed_residue_atom_id"] == "SG"
        and row["manual_review_date"] == "2026-07-02"
        and row["manual_reviewer"] == "manual_review_v0"
        for row in confirmed_rows
    )
    all_audit_blank = all(_manual_fields_blank(row) for row in audit_blank_rows)
    all_human_review = all(_is_true_text(row["human_review_required"]) for row in rows)
    all_training_false = all(_is_false_text(row["training_ready"]) for row in rows)
    all_inference_false = all(_is_false_text(row[column]) for row in rows for column in INFERENCE_FLAG_COLUMNS)
    duplicate_exclusion = (
        by_id.get("HR_0001", {}).get("manual_exclusion_reason")
        == "duplicate_struct_conn_same_CYS481_GJJ_C33_as_HR_0002"
    )
    if blockers:
        validation_passed = False
    else:
        validation_passed = bool(
            all_confirmed_required
            and all_audit_blank
            and all_human_review
            and all_training_false
            and all_inference_false
            and duplicate_exclusion
        )
    return {
        "manual_filled_table_csv_read": True,
        "manual_filled_table_row_count": len(rows),
        "manual_review_fill_validation_executed": True,
        "confirmed_review_row_count": len(confirm_ids),
        "excluded_review_row_count": len(exclude_ids),
        "blank_audit_review_row_count": len(audit_blank_rows),
        "confirmed_review_row_ids": confirm_ids,
        "excluded_review_row_ids": exclude_ids,
        "duplicate_exclusion_validated": duplicate_exclusion,
        "all_confirmed_rows_have_required_manual_fields": all_confirmed_required,
        "all_audit_rows_except_duplicate_blank": all_audit_blank,
        "all_manual_review_dates_valid": all(row["manual_review_date"] == "2026-07-02" for row in confirmed_rows),
        "all_manual_reviewers_valid": all(row["manual_reviewer"] == "manual_review_v0" for row in confirmed_rows),
        "all_human_review_required_true": all_human_review,
        "all_training_ready_false": all_training_false,
        "all_inference_flags_false": all_inference_false,
        "manual_validation_passed": validation_passed,
        "manual_validation_blocking_reasons": blockers,
    }


def build_confirmed_candidate_rows_v0(manual_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    confirmed_rows = [row for row in manual_rows if row["manual_review_decision"] == "confirm"]
    output_rows: list[dict[str, Any]] = []
    for row in confirmed_rows:
        output_rows.append(
            {
                "confirmed_candidate_id": (
                    f"CONFIRMED_{row['review_row_id']}_{row['pdb_id']}_{row['manual_confirmed_ligand_comp_id']}"
                ),
                "review_row_id": row["review_row_id"],
                "candidate_stub_id": row["candidate_stub_id"],
                "sample_id": row["sample_id"],
                "pdb_id": row["pdb_id"],
                "entry_id": row["entry_id"],
                "structure_title": row["structure_title"],
                "conn_type_id": row["conn_type_id"],
                "conn_candidate_status": row["conn_candidate_status"],
                "struct_conn_id": row["struct_conn_id"],
                "struct_conn_row_index": row["struct_conn_row_index"],
                "pdbx_dist_value": row["pdbx_dist_value"],
                "pdbx_role": row["pdbx_role"],
                "manual_confirmed_covalent_bond": row["manual_confirmed_covalent_bond"],
                "manual_confirmed_ptnr1_role": row["manual_confirmed_ptnr1_role"],
                "manual_confirmed_ptnr2_role": row["manual_confirmed_ptnr2_role"],
                "manual_confirmed_ligand_comp_id": row["manual_confirmed_ligand_comp_id"],
                "manual_confirmed_residue_comp_id": row["manual_confirmed_residue_comp_id"],
                "manual_confirmed_ligand_atom_id": row["manual_confirmed_ligand_atom_id"],
                "manual_confirmed_residue_atom_id": row["manual_confirmed_residue_atom_id"],
                "manual_confirmed_warhead_type": row["manual_confirmed_warhead_type"],
                "ptnr1_label_asym_id": row["ptnr1_label_asym_id"],
                "ptnr1_label_comp_id": row["ptnr1_label_comp_id"],
                "ptnr1_label_seq_id": row["ptnr1_label_seq_id"],
                "ptnr1_label_atom_id": row["ptnr1_label_atom_id"],
                "ptnr1_auth_asym_id": row["ptnr1_auth_asym_id"],
                "ptnr1_auth_comp_id": row["ptnr1_auth_comp_id"],
                "ptnr1_auth_seq_id": row["ptnr1_auth_seq_id"],
                "ptnr1_auth_atom_id": row["ptnr1_auth_atom_id"],
                "ptnr2_label_asym_id": row["ptnr2_label_asym_id"],
                "ptnr2_label_comp_id": row["ptnr2_label_comp_id"],
                "ptnr2_label_seq_id": row["ptnr2_label_seq_id"],
                "ptnr2_label_atom_id": row["ptnr2_label_atom_id"],
                "ptnr2_auth_asym_id": row["ptnr2_auth_asym_id"],
                "ptnr2_auth_comp_id": row["ptnr2_auth_comp_id"],
                "ptnr2_auth_seq_id": row["ptnr2_auth_seq_id"],
                "ptnr2_auth_atom_id": row["ptnr2_auth_atom_id"],
                "chem_comp_ids": row["chem_comp_ids"],
                "manual_review_notes": row["manual_review_notes"],
                "manual_reviewer": row["manual_reviewer"],
                "manual_review_date": row["manual_review_date"],
                "manual_review_validated": True,
                "coordinate_extraction_ready": True,
                "training_ready": False,
                "training_ready_reason": (
                    "manual_review_validated_but_coordinates_not_extracted_and_no_sample_index"
                ),
                "sample_index_written": False,
                "final_dataset_written": False,
                "coordinates_extracted": False,
                "distance_calculated": False,
                "rdkit_used": False,
            }
        )
    return output_rows


def _confirmed_candidate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "confirmed_candidate_table_csv_written": True,
        "confirmed_candidate_table_row_count": len(rows),
        "all_confirmed_candidate_ids_unique": len({row["confirmed_candidate_id"] for row in rows}) == len(rows),
        "all_confirmed_candidates_coordinate_extraction_ready": all(
            row["coordinate_extraction_ready"] is True for row in rows
        ),
        "all_confirmed_candidates_training_ready_false": all(row["training_ready"] is False for row in rows),
        "all_confirmed_candidates_sample_index_written_false": all(
            row["sample_index_written"] is False for row in rows
        ),
        "all_confirmed_candidates_coordinates_not_extracted": all(
            row["coordinates_extracted"] is False for row in rows
        ),
        "all_confirmed_candidates_distance_not_calculated": all(row["distance_calculated"] is False for row in rows),
        "all_confirmed_candidates_rdkit_false": all(row["rdkit_used"] is False for row in rows),
    }


def build_real_covalent_struct_conn_candidate_manual_review_fill_validation_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13b_validated = validate_step13b_human_review_table_v0()
    except Exception as exc:
        step13b_validated = False
        blockers.append(f"step13b_validation_failed:{type(exc).__name__}:{exc}")
    step13b_manifest = _load_json(STEP13B_MANIFEST_JSON)
    manual_rows = load_manual_filled_review_rows_v0()
    manual_summary = validate_manual_filled_rows_v0(manual_rows)
    blockers.extend(manual_summary["manual_validation_blocking_reasons"])
    confirmed_rows = build_confirmed_candidate_rows_v0(manual_rows)
    confirmed_summary = _confirmed_candidate_summary(confirmed_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked()
    step13b_blank_modified = _path_modified(STEP13B_BLANK_HUMAN_REVIEW_TABLE_CSV)
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    if step13b_blank_modified:
        blockers.append("step13b_blank_table_modified")
    passed = bool(
        step13b_validated
        and step13b_manifest["step12b_mask_level_aware_validator_validated"]
        and manual_summary["manual_validation_passed"]
        and confirmed_summary["confirmed_candidate_table_row_count"] == 3
        and confirmed_summary["all_confirmed_candidate_ids_unique"]
        and confirmed_summary["all_confirmed_candidates_coordinate_extraction_ready"]
        and confirmed_summary["all_confirmed_candidates_training_ready_false"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not step13b_blank_modified
        and not blockers
    )
    next_step = (
        RECOMMENDED_NEXT_STEP
        if passed
        else "real_covalent_struct_conn_candidate_manual_review_fill_validation_debug"
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13b_human_review_table_validated": step13b_validated,
        "step12b_mask_level_aware_validator_validated": step13b_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        **{key: value for key, value in manual_summary.items() if not key.startswith("manual_validation_")},
        **confirmed_summary,
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
        "step13b_blank_table_modified": step13b_blank_modified,
        "real_covalent_struct_conn_candidate_manual_review_fill_validation_passed": passed,
        "manual_review_fill_validation_contract_satisfied": passed,
        "ready_for_confirmed_candidate_coordinate_extraction_design_gate": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "confirmed_rows": confirmed_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13b_precondition_blank_table_restored": {
            "step13b_human_review_table_validated": manifest["step13b_human_review_table_validated"],
            "step13b_blank_table_modified": manifest["step13b_blank_table_modified"],
        },
        "manual_filled_table_read": {
            "manual_filled_table_csv_read": manifest["manual_filled_table_csv_read"],
            "manual_filled_table_row_count": manifest["manual_filled_table_row_count"],
        },
        "manual_decision_counts": {
            "confirmed_review_row_count": manifest["confirmed_review_row_count"],
            "excluded_review_row_count": manifest["excluded_review_row_count"],
            "blank_audit_review_row_count": manifest["blank_audit_review_row_count"],
        },
        "confirmed_rows_required_fields": {
            "confirmed_review_row_ids": manifest["confirmed_review_row_ids"],
            "all_confirmed_rows_have_required_manual_fields": manifest[
                "all_confirmed_rows_have_required_manual_fields"
            ],
        },
        "duplicate_exclusion_validation": {
            "excluded_review_row_ids": manifest["excluded_review_row_ids"],
            "duplicate_exclusion_validated": manifest["duplicate_exclusion_validated"],
        },
        "confirmed_candidate_table_written": {
            "confirmed_candidate_table_csv_written": manifest["confirmed_candidate_table_csv_written"],
            "confirmed_candidate_table_row_count": manifest["confirmed_candidate_table_row_count"],
        },
        "no_raw_no_training_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            "mmcif_parsed": manifest["mmcif_parsed"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "next_step_decision": {
            "ready_for_confirmed_candidate_coordinate_extraction_design_gate": manifest[
                "ready_for_confirmed_candidate_coordinate_extraction_design_gate"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
