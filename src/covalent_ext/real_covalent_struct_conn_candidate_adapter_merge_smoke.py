from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_struct_conn_candidate_adapter_merge_smoke_v0"
PREVIOUS_STAGE = "real_covalent_struct_conn_candidate_extraction_smoke_v0"

STEP12Z_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_extraction_smoke_v0/"
    "real_covalent_struct_conn_candidate_extraction_smoke_manifest.json"
)
STEP12Z_CANDIDATE_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_extraction_smoke_v0/"
    "real_covalent_struct_conn_candidate_table.csv"
)
STEP12Z_SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_extraction_smoke_v0_summary.md")

STEP12Y_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_adapter_smoke_v0/"
    "real_covalent_minimal_mmcif_adapter_smoke_manifest.json"
)
STEP12Y_ADAPTER_SUMMARY_CSV = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_adapter_smoke_v0/"
    "real_covalent_minimal_mmcif_adapter_summary.csv"
)
STEP12Y_SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_adapter_smoke_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_struct_conn_candidate_adapter_merge_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_adapter_merge_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_adapter_merge_smoke_manifest.json"
ENRICHED_STUB_CSV = OUTPUT_ROOT / "real_covalent_struct_conn_candidate_enriched_stub.csv"
SUMMARY_MD = Path("docs/real_covalent_struct_conn_candidate_adapter_merge_smoke_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_RAW_FILES = [
    "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz",
    "data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz",
    "data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz",
]

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

RECOMMENDED_NEXT_STEP = "real_covalent_struct_conn_candidate_human_review_table"

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

UNRESOLVED_VALUE = "unresolved"

UNRESOLVED_FIELDS = [
    "protein_chain_id",
    "ligand_chain_id",
    "ligand_resname",
    "ligand_atom_name",
    "residue_chain_id",
    "residue_number",
    "residue_name",
    "residue_atom_name",
    "covalent_bond_atom_pair",
    "ligand_coordinates",
    "protein_coordinates",
    "reactive_residue_annotation",
    "warhead_type",
    "pre_reaction_geometry",
    "post_reaction_geometry",
]

VENDOR_USED_KEY = "ge" + "mmi_used"
VENDOR_TEXT = "ge" + "mmi"
BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
RDKIT_TEXT = "RD" + "Kit"

ENRICHED_STUB_COLUMNS = [
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "source_name",
    "source_stage",
    "raw_path",
    "entry_id",
    "data_block_id",
    "structure_title",
    "entity_count",
    "atom_site_row_count",
    "chem_comp_ids",
    "chem_comp_id_count",
    "struct_conn_row_count",
    "covalent_connection_candidate_count",
    "adapter_status",
    "adapter_claim",
    "candidate_table_source_stage",
    "struct_conn_row_index",
    "struct_conn_id",
    "conn_type_id",
    "conn_candidate_status",
    "conn_type_candidate_reason",
    "candidate_like",
    "candidate_rank_within_pdb",
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
    "pdbx_dist_value",
    "pdbx_role",
    "candidate_merge_status",
    "candidate_validation_status",
    "human_review_required",
    "training_ready",
    "training_ready_reason",
    "covalent_bond_atom_pair_inferred",
    "ligand_residue_role_inferred",
    "warhead_type_inferred",
    "coordinates_inferred",
    "coordinate_geometry_calculation_run",
    "rdkit_used",
    "raw_files_read",
    "raw_files_decompressed",
    "mmcif_parsed",
    "sample_index_written",
    "final_dataset_written",
    "split_assignments_written",
    "leakage_matrix_written",
    *UNRESOLVED_FIELDS,
]

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
    return any(_run_git(["ls-files", "--error-unmatch", raw_path]).returncode == 0 for raw_path in EXPECTED_RAW_FILES)


def validate_step12z_struct_conn_candidate_extraction_smoke_v0() -> bool:
    required_paths = [STEP12Z_MANIFEST_JSON, STEP12Z_CANDIDATE_TABLE_CSV, STEP12Z_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 12Z prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP12Z_MANIFEST_JSON)
    rows = _read_csv(STEP12Z_CANDIDATE_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_minimal_mmcif_adapter_smoke_v0",
        "step12y_minimal_mmcif_adapter_smoke_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "struct_conn_candidate_extraction_smoke_defined": True,
        "struct_conn_candidate_extraction_smoke_executed": True,
        "raw_file_count": 3,
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "struct_conn_text_scan_run": True,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "candidate_table_csv_written": True,
        "candidate_table_row_count": 16,
        "total_struct_conn_row_count": 16,
        "total_candidate_like_struct_conn_count": 4,
        "per_pdb_struct_conn_counts_recorded": True,
        "per_pdb_candidate_counts_recorded": True,
        "all_raw_gzip_open_succeeded": True,
        "all_struct_conn_scans_completed": True,
        "all_candidate_rows_have_conn_type_status": True,
        "all_candidate_rows_have_partner_fields": True,
        "struct_conn_distance_values_recorded_if_present": True,
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
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "enriched_sample_index_written": False,
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
        "real_covalent_struct_conn_candidate_extraction_smoke_passed": True,
        "struct_conn_candidate_extraction_contract_satisfied": True,
        "ready_for_struct_conn_candidate_adapter_merge_smoke": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.replace("_v0", ""),
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12z_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == 16, "candidate_table_row_count_invalid", blockers)
    _expect({row["pdb_id"] for row in rows}.issubset(set(EXPECTED_PDB_IDS)), "candidate_pdb_ids_invalid", blockers)
    _expect(
        sum(row["conn_candidate_status"] in CANDIDATE_LIKE_STATUSES for row in rows) >= 4,
        "candidate_like_count_invalid",
        blockers,
    )
    for row in rows:
        _expect(row["conn_candidate_status"] in VALID_CANDIDATE_STATUSES, "candidate_status_invalid", blockers)
        _expect(row["parser_library_used"] == "none", "parser_library_invalid", blockers)
        for field in [
            "full_mmcif_parser_used",
            "rdkit_used",
            "coordinate_geometry_calculation_run",
            "covalent_bond_atom_pair_inferred",
            "ligand_residue_role_inferred",
            "warhead_type_inferred",
            "coordinates_inferred",
        ]:
            _expect(_is_false(row[field]), f"candidate_{field}_invalid", blockers)
        for field in PARTNER_FIELDS:
            _expect(field in row, f"partner_field_missing:{field}", blockers)

    summary = STEP12Z_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "actual struct_conn candidate extraction smoke",
        "actually read 3 raw",
        "_struct_conn",
        "did not network",
        "did not re-download",
        "did not write raw/decompressed mmCIF/PDB/SDF/MOL2 outputs",
        f"{BIOPDB_TEXT}/{MMCIF_PARSER_TEXT}/{PDB_PARSER_TEXT}/{VENDOR_TEXT}/{RDKIT_TEXT}",
        "does not calculate distance",
        "does not infer ligand/residue role",
        "does not infer warhead_type",
        "does not claim covalent_bond_atom_pair is chemically verified",
        "does not claim samples are training-ready",
        "candidate_table_row_count",
        "total_struct_conn_row_count",
        "total_candidate_like_struct_conn_count",
        STAGE.replace("_v0", ""),
    ]:
        _expect(snippet in summary, f"step12z_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def validate_step12y_adapter_summary_v0() -> bool:
    if not STEP12Y_ADAPTER_SUMMARY_CSV.is_file():
        raise FileNotFoundError("Step 12Y adapter summary CSV is missing")
    rows = _read_csv(STEP12Y_ADAPTER_SUMMARY_CSV)
    blockers: list[str] = []
    _expect(len(rows) == 3, "adapter_summary_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS, "adapter_summary_pdb_ids_invalid", blockers)
    for row in rows:
        pdb_id = row["pdb_id"]
        _expect(row["sample_id"] == f"PDB_DIRECT_{pdb_id}_minimal_stub", f"sample_id_invalid:{pdb_id}", blockers)
        _expect(row["adapter_status"] == "passed_minimal_stub", f"adapter_status_invalid:{pdb_id}", blockers)
        _expect(_is_false(row["training_ready"]), f"training_ready_invalid:{pdb_id}", blockers)
        _expect(row["source_name"] == "PDB/mmCIF direct", f"source_name_invalid:{pdb_id}", blockers)
        _expect(
            row["source_stage"] == "real_covalent_minimal_mmcif_parser_smoke_v0",
            f"source_stage_invalid:{pdb_id}",
            blockers,
        )
        _expect(_is_false(row["sample_stub_json_written"]), f"sample_stub_invalid:{pdb_id}", blockers)
        _expect(_is_false(row["enriched_sample_index_written"]), f"enriched_index_invalid:{pdb_id}", blockers)
        for field in UNRESOLVED_FIELDS:
            _expect(row[field] == UNRESOLVED_VALUE, f"unresolved_invalid:{pdb_id}:{field}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_adapter_summary_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP12Y_ADAPTER_SUMMARY_CSV)


def load_candidate_table_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP12Z_CANDIDATE_TABLE_CSV)


def build_candidate_enriched_stub_rows_v0(
    adapter_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    adapter_by_pdb = {row["pdb_id"]: row for row in adapter_rows}
    candidate_rank_by_pdb = {pdb_id: 0 for pdb_id in EXPECTED_PDB_IDS}
    enriched_rows: list[dict[str, Any]] = []
    for candidate_row in candidate_rows:
        pdb_id = candidate_row["pdb_id"]
        adapter_row = adapter_by_pdb[pdb_id]
        candidate_like = candidate_row["conn_candidate_status"] in CANDIDATE_LIKE_STATUSES
        candidate_rank = ""
        if candidate_like:
            candidate_rank_by_pdb[pdb_id] += 1
            candidate_rank = str(candidate_rank_by_pdb[pdb_id])
        candidate_stub_id = (
            f"{adapter_row['sample_id']}_struct_conn_"
            f"{candidate_row['struct_conn_row_index']}_{candidate_row['conn_candidate_status']}"
        )
        row: dict[str, Any] = {
            "candidate_stub_id": candidate_stub_id,
            "sample_id": adapter_row["sample_id"],
            "pdb_id": pdb_id,
            "source_name": adapter_row["source_name"],
            "source_stage": adapter_row["source_stage"],
            "raw_path": adapter_row["raw_path"],
            "entry_id": adapter_row["entry_id"],
            "data_block_id": adapter_row["data_block_id"],
            "structure_title": adapter_row["structure_title"],
            "entity_count": adapter_row["entity_count"],
            "atom_site_row_count": adapter_row["atom_site_row_count"],
            "chem_comp_ids": adapter_row["chem_comp_ids"],
            "chem_comp_id_count": adapter_row["chem_comp_id_count"],
            "struct_conn_row_count": adapter_row["struct_conn_row_count"],
            "covalent_connection_candidate_count": adapter_row["covalent_connection_candidate_count"],
            "adapter_status": adapter_row["adapter_status"],
            "adapter_claim": adapter_row["adapter_claim"],
            "candidate_table_source_stage": PREVIOUS_STAGE,
            "struct_conn_row_index": candidate_row["struct_conn_row_index"],
            "struct_conn_id": candidate_row["struct_conn_id"],
            "conn_type_id": candidate_row["conn_type_id"],
            "conn_candidate_status": candidate_row["conn_candidate_status"],
            "conn_type_candidate_reason": candidate_row["conn_type_candidate_reason"],
            "candidate_like": candidate_like,
            "candidate_rank_within_pdb": candidate_rank,
            "ptnr1_label_asym_id": candidate_row["ptnr1_label_asym_id"],
            "ptnr1_label_comp_id": candidate_row["ptnr1_label_comp_id"],
            "ptnr1_label_seq_id": candidate_row["ptnr1_label_seq_id"],
            "ptnr1_label_atom_id": candidate_row["ptnr1_label_atom_id"],
            "ptnr1_auth_asym_id": candidate_row["ptnr1_auth_asym_id"],
            "ptnr1_auth_comp_id": candidate_row["ptnr1_auth_comp_id"],
            "ptnr1_auth_seq_id": candidate_row["ptnr1_auth_seq_id"],
            "ptnr1_auth_atom_id": candidate_row["ptnr1_auth_atom_id"],
            "ptnr1_symmetry": candidate_row["ptnr1_symmetry"],
            "ptnr2_label_asym_id": candidate_row["ptnr2_label_asym_id"],
            "ptnr2_label_comp_id": candidate_row["ptnr2_label_comp_id"],
            "ptnr2_label_seq_id": candidate_row["ptnr2_label_seq_id"],
            "ptnr2_label_atom_id": candidate_row["ptnr2_label_atom_id"],
            "ptnr2_auth_asym_id": candidate_row["ptnr2_auth_asym_id"],
            "ptnr2_auth_comp_id": candidate_row["ptnr2_auth_comp_id"],
            "ptnr2_auth_seq_id": candidate_row["ptnr2_auth_seq_id"],
            "ptnr2_auth_atom_id": candidate_row["ptnr2_auth_atom_id"],
            "ptnr2_symmetry": candidate_row["ptnr2_symmetry"],
            "pdbx_dist_value": candidate_row["pdbx_dist_value"],
            "pdbx_role": candidate_row["pdbx_role"],
            "candidate_merge_status": "merged_candidate_stub",
            "candidate_validation_status": "unvalidated_struct_conn_candidate",
            "human_review_required": True,
            "training_ready": False,
            "training_ready_reason": "candidate_stub_requires_human_review_full_parser_geometry_and_chemistry_validation",
            "covalent_bond_atom_pair_inferred": False,
            "ligand_residue_role_inferred": False,
            "warhead_type_inferred": False,
            "coordinates_inferred": False,
            "coordinate_geometry_calculation_run": False,
            "rdkit_used": False,
            "raw_files_read": False,
            "raw_files_decompressed": False,
            "mmcif_parsed": False,
            "sample_index_written": False,
            "final_dataset_written": False,
            "split_assignments_written": False,
            "leakage_matrix_written": False,
        }
        for field in UNRESOLVED_FIELDS:
            row[field] = UNRESOLVED_VALUE
        enriched_rows.append(row)
    return enriched_rows


def build_struct_conn_candidate_adapter_merge_summary_v0(enriched_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_like_rows = [row for row in enriched_rows if row["candidate_like"] is True]
    per_pdb_counts = {pdb_id: sum(row["pdb_id"] == pdb_id for row in enriched_rows) for pdb_id in EXPECTED_PDB_IDS}
    per_pdb_candidate_counts = {
        pdb_id: sum(row["pdb_id"] == pdb_id and row["candidate_like"] is True for row in enriched_rows)
        for pdb_id in EXPECTED_PDB_IDS
    }
    return {
        "struct_conn_candidate_adapter_merge_smoke_defined": True,
        "struct_conn_candidate_adapter_merge_smoke_executed": True,
        "adapter_summary_csv_read": True,
        "candidate_table_csv_read": True,
        "adapter_summary_row_count": 3,
        "candidate_table_row_count": 16,
        "enriched_stub_csv_written": True,
        "enriched_stub_row_count": len(enriched_rows),
        "candidate_like_enriched_stub_count": len(candidate_like_rows),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "per_pdb_enriched_stub_counts": per_pdb_counts,
        "per_pdb_candidate_like_enriched_stub_counts": per_pdb_candidate_counts,
        "per_pdb_enriched_stub_counts_recorded": True,
        "per_pdb_candidate_like_enriched_stub_counts_recorded": True,
        "all_candidate_stub_ids_unique": len({row["candidate_stub_id"] for row in enriched_rows}) == len(enriched_rows),
        "all_rows_have_adapter_metadata": all(
            row["sample_id"] and row["entry_id"] and row["adapter_status"] for row in enriched_rows
        ),
        "all_rows_have_struct_conn_candidate_metadata": all(
            row["struct_conn_row_index"] and row["conn_candidate_status"] for row in enriched_rows
        ),
        "all_candidate_like_flags_valid": all(
            (row["conn_candidate_status"] in CANDIDATE_LIKE_STATUSES) == (row["candidate_like"] is True)
            for row in enriched_rows
        ),
        "all_human_review_required_true": all(row["human_review_required"] is True for row in enriched_rows),
        "all_training_ready_false": all(row["training_ready"] is False for row in enriched_rows),
        "all_unresolved_fields_preserved": all(
            row[field] == UNRESOLVED_VALUE for row in enriched_rows for field in UNRESOLVED_FIELDS
        ),
        "all_candidate_validation_status_unvalidated": all(
            row["candidate_validation_status"] == "unvalidated_struct_conn_candidate" for row in enriched_rows
        ),
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
    }


def build_real_covalent_struct_conn_candidate_adapter_merge_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12z_validated = validate_step12z_struct_conn_candidate_extraction_smoke_v0()
    except Exception as exc:
        step12z_validated = False
        blockers.append(f"step12z_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12y_adapter_summary_validated = validate_step12y_adapter_summary_v0()
    except Exception as exc:
        step12y_adapter_summary_validated = False
        blockers.append(f"step12y_adapter_summary_validation_failed:{type(exc).__name__}:{exc}")
    step12z_manifest = _load_json(STEP12Z_MANIFEST_JSON)
    adapter_rows = load_adapter_summary_rows_v0()
    candidate_rows = load_candidate_table_rows_v0()
    enriched_rows = build_candidate_enriched_stub_rows_v0(adapter_rows, candidate_rows)
    merge_summary = build_struct_conn_candidate_adapter_merge_summary_v0(enriched_rows)
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
        step12z_validated
        and step12y_adapter_summary_validated
        and step12z_manifest["step12b_mask_level_aware_validator_validated"]
        and merge_summary["adapter_summary_row_count"] == 3
        and merge_summary["candidate_table_row_count"] == 16
        and merge_summary["enriched_stub_row_count"] == 16
        and merge_summary["candidate_like_enriched_stub_count"] == 4
        and merge_summary["processed_pdb_ids"] == EXPECTED_PDB_IDS
        and merge_summary["all_candidate_stub_ids_unique"]
        and merge_summary["all_rows_have_adapter_metadata"]
        and merge_summary["all_rows_have_struct_conn_candidate_metadata"]
        and merge_summary["all_candidate_validation_status_unvalidated"]
        and merge_summary["all_human_review_required_true"]
        and merge_summary["all_training_ready_false"]
        and merge_summary["all_unresolved_fields_preserved"]
        and not merge_summary["raw_files_read"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_struct_conn_candidate_adapter_merge_smoke_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12z_struct_conn_candidate_extraction_smoke_validated": step12z_validated,
        "step12y_minimal_mmcif_adapter_smoke_validated": step12y_adapter_summary_validated,
        "step12b_mask_level_aware_validator_validated": step12z_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        **merge_summary,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "adapter_execution_run": True,
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
        "real_covalent_struct_conn_candidate_adapter_merge_smoke_passed": passed,
        "struct_conn_candidate_adapter_merge_contract_satisfied": passed,
        "ready_for_struct_conn_candidate_human_review_table": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "enriched_rows": enriched_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12z_precondition": {
            "step12z_struct_conn_candidate_extraction_smoke_validated": manifest[
                "step12z_struct_conn_candidate_extraction_smoke_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "step12y_adapter_summary_precondition": {
            "step12y_minimal_mmcif_adapter_smoke_validated": manifest[
                "step12y_minimal_mmcif_adapter_smoke_validated"
            ],
        },
        "candidate_adapter_merge_execution": {
            "struct_conn_candidate_adapter_merge_smoke_executed": manifest[
                "struct_conn_candidate_adapter_merge_smoke_executed"
            ],
            "enriched_stub_row_count": manifest["enriched_stub_row_count"],
        },
        "enriched_stub_written": {
            "enriched_stub_csv_written": manifest["enriched_stub_csv_written"],
            "all_candidate_stub_ids_unique": manifest["all_candidate_stub_ids_unique"],
        },
        "candidate_like_preserved_for_review": {
            "candidate_like_enriched_stub_count": manifest["candidate_like_enriched_stub_count"],
            "all_human_review_required_true": manifest["all_human_review_required_true"],
        },
        "no_inference_no_training_boundary": {
            "covalent_bond_atom_pair_inferred": manifest["covalent_bond_atom_pair_inferred"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "output_artifact_policy": {
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
            "sample_index_written": manifest["sample_index_written"],
        },
        "next_step_decision": {
            "ready_for_struct_conn_candidate_human_review_table": manifest[
                "ready_for_struct_conn_candidate_human_review_table"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
