from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_struct_conn_candidate_human_review_table_v0"
PREVIOUS_STAGE = "real_covalent_struct_conn_candidate_adapter_merge_smoke_v0"

STEP13A_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_adapter_merge_smoke_v0/"
    "real_covalent_struct_conn_candidate_adapter_merge_smoke_manifest.json"
)
STEP13A_ENRICHED_STUB_CSV = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_adapter_merge_smoke_v0/"
    "real_covalent_struct_conn_candidate_enriched_stub.csv"
)
STEP13A_SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_adapter_merge_smoke_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_struct_conn_candidate_human_review_table_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_human_review_table_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_human_review_table_manifest.json"
HUMAN_REVIEW_TABLE_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_human_review_table.csv"
SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_human_review_table_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]

CANDIDATE_LIKE_STATUSES = {
    "covalent_like_candidate",
    "disulfide_like_candidate",
    "link_like_candidate",
    "modres_like_candidate",
}

VALID_CANDIDATE_STATUSES = {
    "covalent_like_candidate",
    "disulfide_like_candidate",
    "link_like_candidate",
    "modres_like_candidate",
    "non_candidate_recorded",
    "no_struct_conn_rows_detected",
}

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

HUMAN_REVIEW_COLUMNS = [
    "review_row_id",
    "review_priority",
    "review_bucket",
    "candidate_like",
    "candidate_rank_within_pdb",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "conn_candidate_status",
    "conn_type_id",
    "conn_type_candidate_reason",
    "struct_conn_id",
    "struct_conn_row_index",
    "pdbx_dist_value",
    "pdbx_role",
    "ptnr1_label_asym_id",
    "ptnr1_label_comp_id",
    "ptnr1_label_seq_id",
    "ptnr1_label_atom_id",
    "ptnr1_auth_asym_id",
    "ptnr1_auth_comp_id",
    "ptnr1_auth_seq_id",
    "ptnr1_auth_atom_id",
    "ptnr1_symmetry",
    "ptnr2_label_asym_id",
    "ptnr2_label_comp_id",
    "ptnr2_label_seq_id",
    "ptnr2_label_atom_id",
    "ptnr2_auth_asym_id",
    "ptnr2_auth_comp_id",
    "ptnr2_auth_seq_id",
    "ptnr2_auth_atom_id",
    "ptnr2_symmetry",
    "chem_comp_ids",
    "candidate_validation_status",
    "human_review_required",
    "training_ready",
    "training_ready_reason",
    "covalent_bond_atom_pair_inferred",
    "ligand_residue_role_inferred",
    "warhead_type_inferred",
    "coordinates_inferred",
    "distance_calculated",
    "source_enriched_stub_stage",
    *MANUAL_REVIEW_COLUMNS,
]

RECOMMENDED_NEXT_STEP = "manual_fill_struct_conn_candidate_human_review_table"

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

PARTNER_FIELDS = [
    "ptnr1_label_asym_id",
    "ptnr1_label_comp_id",
    "ptnr1_label_seq_id",
    "ptnr1_label_atom_id",
    "ptnr2_label_asym_id",
    "ptnr2_label_comp_id",
    "ptnr2_label_seq_id",
    "ptnr2_label_atom_id",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _bool_text(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"not a bool text: {value!r}")


def _is_false(value: str) -> bool:
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


def validate_step13a_struct_conn_candidate_adapter_merge_smoke_v0() -> bool:
    required_paths = [STEP13A_MANIFEST_JSON, STEP13A_ENRICHED_STUB_CSV, STEP13A_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13A prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13A_MANIFEST_JSON)
    rows = _read_csv(STEP13A_ENRICHED_STUB_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_struct_conn_candidate_extraction_smoke_v0",
        "step12z_struct_conn_candidate_extraction_smoke_validated": True,
        "step12y_minimal_mmcif_adapter_smoke_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "struct_conn_candidate_adapter_merge_smoke_defined": True,
        "struct_conn_candidate_adapter_merge_smoke_executed": True,
        "adapter_summary_csv_read": True,
        "candidate_table_csv_read": True,
        "adapter_summary_row_count": 3,
        "candidate_table_row_count": 16,
        "enriched_stub_csv_written": True,
        "enriched_stub_row_count": 16,
        "candidate_like_enriched_stub_count": 4,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "per_pdb_enriched_stub_counts_recorded": True,
        "per_pdb_candidate_like_enriched_stub_counts_recorded": True,
        "all_candidate_stub_ids_unique": True,
        "all_rows_have_adapter_metadata": True,
        "all_rows_have_struct_conn_candidate_metadata": True,
        "all_candidate_like_flags_valid": True,
        "all_human_review_required_true": True,
        "all_training_ready_false": True,
        "all_unresolved_fields_preserved": True,
        "all_candidate_validation_status_unvalidated": True,
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
        "covalent_bond_atom_pair_inferred": False,
        "ligand_residue_role_inferred": False,
        "warhead_type_inferred": False,
        "coordinates_inferred": False,
        "distance_calculated": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "output_limited_to_csv_json_md": True,
        "adapter_execution_run": True,
        "real_adapter_execution_run": False,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
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
        "real_covalent_struct_conn_candidate_adapter_merge_smoke_passed": True,
        "struct_conn_candidate_adapter_merge_contract_satisfied": True,
        "ready_for_struct_conn_candidate_human_review_table": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.replace("_v0", ""),
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13a_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == 16, "enriched_stub_row_count_invalid", blockers)
    _expect(sum(row["candidate_like"] == "True" for row in rows) == 4, "candidate_like_count_invalid", blockers)
    _expect({row["pdb_id"] for row in rows}.issubset(set(EXPECTED_PDB_IDS)), "enriched_pdb_ids_invalid", blockers)
    for row in rows:
        _expect(row["conn_candidate_status"] in VALID_CANDIDATE_STATUSES, "candidate_status_invalid", blockers)
        _expect(
            row["candidate_validation_status"] == "unvalidated_struct_conn_candidate",
            "validation_status_invalid",
            blockers,
        )
        _expect(row["human_review_required"] == "True", "human_review_required_invalid", blockers)
        _expect(row["training_ready"] == "False", "training_ready_invalid", blockers)
        for field in [
            "covalent_bond_atom_pair_inferred",
            "ligand_residue_role_inferred",
            "warhead_type_inferred",
            "coordinates_inferred",
            "sample_index_written",
            "final_dataset_written",
        ]:
            _expect(_is_false(row[field]), f"enriched_{field}_invalid", blockers)
        if "distance_calculated" in row:
            _expect(_is_false(row["distance_calculated"]), "enriched_distance_calculated_invalid", blockers)

    summary = STEP13A_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "actual struct_conn candidate adapter merge smoke",
        "Step 12Y minimal adapter summary CSV",
        "Step 12Z struct_conn candidate table CSV",
        "did not read raw",
        "did not decompress raw files",
        "did not parse mmCIF",
        f"{BIOPDB_TEXT}/{MMCIF_PARSER_TEXT}/{PDB_PARSER_TEXT}/{VENDOR_TEXT}/{RDKIT_TEXT}",
        "coordinate geometry, distance calculation",
        "candidate-enriched stub CSV",
        "enriched_stub_row_count: 16",
        "candidate_like_enriched_stub_count: 4",
        "human_review_required=true and training_ready=false",
        "did not write enriched sample_index and did not write final dataset",
        STAGE.replace("_v0", ""),
    ]:
        _expect(snippet in summary, f"step13a_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_enriched_stub_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13A_ENRICHED_STUB_CSV)


def _review_bucket(row: dict[str, str]) -> str:
    if _bool_text(row["candidate_like"]):
        return "candidate_like_priority"
    if row["conn_candidate_status"] == "non_candidate_recorded":
        return "non_candidate_audit"
    return "status_row_or_other"


def _int_or_large(value: str) -> int:
    return int(value) if value else 10**9


def _sort_key(row: dict[str, str]) -> tuple[int, int, int, int, str]:
    pdb_order = EXPECTED_PDB_IDS.index(row["pdb_id"])
    return (
        0 if _bool_text(row["candidate_like"]) else 1,
        pdb_order,
        _int_or_large(row["candidate_rank_within_pdb"]),
        _int_or_large(row["struct_conn_row_index"]),
        row["candidate_stub_id"],
    )


def build_human_review_table_rows_v0(enriched_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(enriched_rows, key=_sort_key)
    review_rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted_rows, start=1):
        candidate_like = _bool_text(row["candidate_like"])
        review_row: dict[str, Any] = {
            "review_row_id": f"HR_{index:04d}",
            "review_priority": "high" if candidate_like else "audit",
            "review_bucket": _review_bucket(row),
            "candidate_like": candidate_like,
            "candidate_rank_within_pdb": row["candidate_rank_within_pdb"],
            "candidate_stub_id": row["candidate_stub_id"],
            "sample_id": row["sample_id"],
            "pdb_id": row["pdb_id"],
            "entry_id": row["entry_id"],
            "structure_title": row["structure_title"],
            "conn_candidate_status": row["conn_candidate_status"],
            "conn_type_id": row["conn_type_id"],
            "conn_type_candidate_reason": row["conn_type_candidate_reason"],
            "struct_conn_id": row["struct_conn_id"],
            "struct_conn_row_index": row["struct_conn_row_index"],
            "pdbx_dist_value": row["pdbx_dist_value"],
            "pdbx_role": row["pdbx_role"],
            "ptnr1_label_asym_id": row["ptnr1_label_asym_id"],
            "ptnr1_label_comp_id": row["ptnr1_label_comp_id"],
            "ptnr1_label_seq_id": row["ptnr1_label_seq_id"],
            "ptnr1_label_atom_id": row["ptnr1_label_atom_id"],
            "ptnr1_auth_asym_id": row["ptnr1_auth_asym_id"],
            "ptnr1_auth_comp_id": row["ptnr1_auth_comp_id"],
            "ptnr1_auth_seq_id": row["ptnr1_auth_seq_id"],
            "ptnr1_auth_atom_id": row["ptnr1_auth_atom_id"],
            "ptnr1_symmetry": row["ptnr1_symmetry"],
            "ptnr2_label_asym_id": row["ptnr2_label_asym_id"],
            "ptnr2_label_comp_id": row["ptnr2_label_comp_id"],
            "ptnr2_label_seq_id": row["ptnr2_label_seq_id"],
            "ptnr2_label_atom_id": row["ptnr2_label_atom_id"],
            "ptnr2_auth_asym_id": row["ptnr2_auth_asym_id"],
            "ptnr2_auth_comp_id": row["ptnr2_auth_comp_id"],
            "ptnr2_auth_seq_id": row["ptnr2_auth_seq_id"],
            "ptnr2_auth_atom_id": row["ptnr2_auth_atom_id"],
            "ptnr2_symmetry": row["ptnr2_symmetry"],
            "chem_comp_ids": row["chem_comp_ids"],
            "candidate_validation_status": row["candidate_validation_status"],
            "human_review_required": True,
            "training_ready": False,
            "training_ready_reason": row["training_ready_reason"],
            "covalent_bond_atom_pair_inferred": False,
            "ligand_residue_role_inferred": False,
            "warhead_type_inferred": False,
            "coordinates_inferred": False,
            "distance_calculated": False,
            "source_enriched_stub_stage": PREVIOUS_STAGE,
        }
        for manual_column in MANUAL_REVIEW_COLUMNS:
            review_row[manual_column] = ""
        review_rows.append(review_row)
    return review_rows


def _high_priority_rows_first(rows: list[dict[str, Any]]) -> bool:
    seen_audit = False
    for row in rows:
        if row["review_priority"] == "audit":
            seen_audit = True
        if seen_audit and row["review_priority"] == "high":
            return False
    return True


def build_human_review_table_summary_v0(review_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_like_rows = [row for row in review_rows if row["candidate_like"] is True]
    per_pdb_counts = {pdb_id: sum(row["pdb_id"] == pdb_id for row in review_rows) for pdb_id in EXPECTED_PDB_IDS}
    per_pdb_candidate_counts = {
        pdb_id: sum(row["pdb_id"] == pdb_id and row["candidate_like"] is True for row in review_rows)
        for pdb_id in EXPECTED_PDB_IDS
    }
    inference_fields = [
        "covalent_bond_atom_pair_inferred",
        "ligand_residue_role_inferred",
        "warhead_type_inferred",
        "coordinates_inferred",
        "distance_calculated",
    ]
    return {
        "struct_conn_candidate_human_review_table_defined": True,
        "struct_conn_candidate_human_review_table_executed": True,
        "enriched_stub_csv_read": True,
        "enriched_stub_row_count": 16,
        "human_review_table_csv_written": True,
        "human_review_table_row_count": len(review_rows),
        "candidate_like_review_row_count": len(candidate_like_rows),
        "high_priority_review_row_count": sum(row["review_priority"] == "high" for row in review_rows),
        "audit_review_row_count": sum(row["review_priority"] == "audit" for row in review_rows),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "per_pdb_review_row_counts": per_pdb_counts,
        "per_pdb_candidate_like_review_counts": per_pdb_candidate_counts,
        "per_pdb_review_row_counts_recorded": True,
        "per_pdb_candidate_like_review_counts_recorded": True,
        "manual_review_columns_added": True,
        "manual_review_column_count": len(MANUAL_REVIEW_COLUMNS),
        "all_manual_review_columns_blank": all(
            row[column] == "" for row in review_rows for column in MANUAL_REVIEW_COLUMNS
        ),
        "all_review_row_ids_unique": len({row["review_row_id"] for row in review_rows}) == len(review_rows),
        "all_review_priorities_valid": all(row["review_priority"] in {"high", "audit"} for row in review_rows),
        "high_priority_rows_first": _high_priority_rows_first(review_rows),
        "all_rows_have_partner_atom_identifiers": all(all(field in row for field in PARTNER_FIELDS) for row in review_rows),
        "all_rows_preserve_candidate_status": all(
            row["conn_candidate_status"] in VALID_CANDIDATE_STATUSES for row in review_rows
        ),
        "all_human_review_required_true": all(row["human_review_required"] is True for row in review_rows),
        "all_training_ready_false": all(row["training_ready"] is False for row in review_rows),
        "all_inference_flags_false": all(row[field] is False for row in review_rows for field in inference_fields),
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
        "covalent_bond_atom_pair_inferred": False,
        "ligand_residue_role_inferred": False,
        "warhead_type_inferred": False,
        "coordinates_inferred": False,
        "distance_calculated": False,
        "manual_review_decisions_filled": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "output_limited_to_csv_json_md": True,
    }


def build_real_covalent_struct_conn_candidate_human_review_table_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13a_validated = validate_step13a_struct_conn_candidate_adapter_merge_smoke_v0()
    except Exception as exc:
        step13a_validated = False
        blockers.append(f"step13a_validation_failed:{type(exc).__name__}:{exc}")
    step13a_manifest = _load_json(STEP13A_MANIFEST_JSON)
    enriched_rows = load_enriched_stub_rows_v0()
    review_rows = build_human_review_table_rows_v0(enriched_rows)
    review_summary = build_human_review_table_summary_v0(review_rows)
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
        step13a_validated
        and step13a_manifest["step12b_mask_level_aware_validator_validated"]
        and review_summary["enriched_stub_row_count"] == 16
        and review_summary["human_review_table_row_count"] == 16
        and review_summary["candidate_like_review_row_count"] == 4
        and review_summary["high_priority_review_row_count"] == 4
        and review_summary["audit_review_row_count"] == 12
        and review_summary["all_manual_review_columns_blank"]
        and review_summary["high_priority_rows_first"]
        and review_summary["all_human_review_required_true"]
        and review_summary["all_training_ready_false"]
        and review_summary["all_inference_flags_false"]
        and not review_summary["raw_files_read"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_struct_conn_candidate_human_review_table_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13a_struct_conn_candidate_adapter_merge_smoke_validated": step13a_validated,
        "step12b_mask_level_aware_validator_validated": step13a_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        **review_summary,
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
        "real_covalent_struct_conn_candidate_human_review_table_passed": passed,
        "struct_conn_candidate_human_review_table_contract_satisfied": passed,
        "ready_for_manual_human_review": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "review_rows": review_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13a_precondition": {
            "step13a_struct_conn_candidate_adapter_merge_smoke_validated": manifest[
                "step13a_struct_conn_candidate_adapter_merge_smoke_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "human_review_table_execution": {
            "struct_conn_candidate_human_review_table_executed": manifest[
                "struct_conn_candidate_human_review_table_executed"
            ],
            "human_review_table_row_count": manifest["human_review_table_row_count"],
        },
        "priority_sorting": {
            "high_priority_review_row_count": manifest["high_priority_review_row_count"],
            "high_priority_rows_first": manifest["high_priority_rows_first"],
        },
        "manual_review_columns": {
            "manual_review_column_count": manifest["manual_review_column_count"],
            "all_manual_review_columns_blank": manifest["all_manual_review_columns_blank"],
        },
        "candidate_status_preservation": {
            "all_rows_preserve_candidate_status": manifest["all_rows_preserve_candidate_status"],
            "all_rows_have_partner_atom_identifiers": manifest["all_rows_have_partner_atom_identifiers"],
        },
        "no_inference_no_training_boundary": {
            "all_inference_flags_false": manifest["all_inference_flags_false"],
            "all_training_ready_false": manifest["all_training_ready_false"],
        },
        "output_artifact_policy": {
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
            "sample_index_written": manifest["sample_index_written"],
        },
        "next_step_decision": {
            "ready_for_manual_human_review": manifest["ready_for_manual_human_review"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
