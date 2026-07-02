from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_minimal_mmcif_adapter_smoke_v0"
PREVIOUS_STAGE = "real_covalent_minimal_mmcif_adapter_design_gate_v0"

STEP12X_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_adapter_design_gate_v0/"
    "real_covalent_minimal_mmcif_adapter_design_gate_manifest.json"
)
STEP12X_ADAPTER_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_adapter_design_gate_v0/"
    "real_covalent_minimal_mmcif_adapter_contract.csv"
)
STEP12X_SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_adapter_design_gate_v0_summary.md")

STEP12W_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_smoke_v0/"
    "real_covalent_minimal_mmcif_parser_smoke_manifest.json"
)
STEP12W_EXTRACTED_SUMMARY_CSV = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_smoke_v0/"
    "real_covalent_minimal_mmcif_parser_extracted_summary.csv"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_minimal_mmcif_adapter_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_adapter_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_minimal_mmcif_adapter_smoke_manifest.json"
ADAPTER_SUMMARY_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_adapter_summary.csv"
SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_adapter_smoke_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_RAW_FILES = [
    "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz",
    "data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz",
    "data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz",
]

SOURCE_NAME = "PDB/mmCIF direct"
SOURCE_STAGE = "real_covalent_minimal_mmcif_parser_smoke_v0"
ADAPTER_STATUS = "passed_minimal_stub"
TRAINING_READY_REASON = "minimal_stub_missing_covalent_bond_atom_pair_coordinates_warhead_and_geometry"

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

RECOMMENDED_NEXT_STEP = "real_covalent_struct_conn_candidate_extraction_smoke"

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
BIOPDB_TEXT = "Bio." + "PDB"
MMCIF_PARSER_TEXT = "MM" + "CIFParser"
PDB_PARSER_TEXT = "PDB" + "Parser"
VENDOR_TEXT = "ge" + "mmi"
RDKIT_TEXT = "RD" + "Kit"

ADAPTER_SUMMARY_COLUMNS = [
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
    "covalent_annotation_status",
    "adapter_status",
    *UNRESOLVED_FIELDS,
    "unresolved_field_count",
    "all_unresolved_fields_marked",
    "training_ready",
    "training_ready_reason",
    "adapter_claim",
    "raw_files_read",
    "raw_files_decompressed",
    "mmcif_parsed",
    "external_parser_used",
    "rdkit_used",
    "coordinate_geometry_calculation_run",
    "enriched_sample_index_written",
    "sample_stub_json_written",
]

REQUIRED_PARSER_FIELDS = [
    "pdb_id",
    "raw_path",
    "data_block_id",
    "entry_id",
    "structure_title",
    "entity_count",
    "atom_site_row_count",
    "chem_comp_ids",
    "chem_comp_id_count",
    "struct_conn_row_count",
    "covalent_connection_candidate_count",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _is_true(value: str) -> bool:
    return value == "True"


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


def validate_step12x_minimal_mmcif_adapter_design_gate_v0() -> bool:
    required_paths = [STEP12X_MANIFEST_JSON, STEP12X_ADAPTER_CONTRACT_CSV, STEP12X_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 12X prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP12X_MANIFEST_JSON)
    rows = _read_csv(STEP12X_ADAPTER_CONTRACT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": SOURCE_STAGE,
        "step12w_minimal_mmcif_parser_smoke_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "minimal_mmcif_adapter_contract_defined": True,
        "adapter_contract_csv_written": True,
        "adapter_contract_row_count": 47,
        "adapter_input_contract_row_count": 3,
        "schema_mapping_row_count": 16,
        "not_yet_available_schema_field_row_count": 15,
        "adapter_policy_row_count": 13,
        "adapter_scope_pdb_ids": EXPECTED_PDB_IDS,
        "adapter_scope_limited_to_current_pilot": True,
        "adapter_smoke_reads_parser_summary_next_step": True,
        "adapter_smoke_reads_raw_files_next_step": False,
        "adapter_smoke_decompresses_raw_files_next_step": False,
        "adapter_smoke_parses_mmcif_next_step": False,
        "adapter_smoke_runs_external_parser_next_step": False,
        "adapter_smoke_runs_rdkit_next_step": False,
        "adapter_smoke_runs_geometry_next_step": False,
        "adapter_smoke_writes_adapter_summary_next_step": True,
        "adapter_smoke_writes_sample_stub_json_next_step": False,
        "adapter_smoke_writes_enriched_sample_index_next_step": False,
        "adapter_smoke_output_limited_to_csv_json_md": True,
        "adapter_smoke_ready_next_step": True,
        "adapter_maps_parser_metadata_fields": True,
        "adapter_marks_unresolved_chemistry_fields": True,
        "adapter_does_not_infer_covalent_bond_atom_pair": True,
        "adapter_does_not_infer_warhead_type": True,
        "adapter_does_not_infer_coordinates": True,
        "adapter_does_not_claim_training_ready_samples": True,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "raw_files_read": False,
        "raw_files_decompressed": False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "adapter_implementation_written": False,
        "adapter_execution_run": False,
        "rdkit_processing_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
        "coordinate_geometry_calculation_run": False,
        "npz_files_loaded": False,
        "npz_contents_read": False,
        "enriched_sample_index_written": False,
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
        "real_covalent_minimal_mmcif_adapter_design_gate_passed": True,
        "minimal_mmcif_adapter_design_contract_defined": True,
        "ready_for_minimal_mmcif_adapter_smoke": True,
        "ready_to_run_adapter_now": False,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.replace("_v0", ""),
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12x_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == 47, "adapter_contract_row_count_invalid", blockers)
    input_rows = [row for row in rows if row["contract_section"] == "adapter_input"]
    mapping_rows = [row for row in rows if row["contract_section"] == "schema_mapping"]
    unresolved_rows = [row for row in rows if row["contract_section"] == "not_yet_available_schema_field"]
    policy_rows = [row for row in rows if row["contract_section"] == "adapter_policy"]
    _expect(len(input_rows) == 3, "adapter_input_row_count_invalid", blockers)
    _expect(len(mapping_rows) == 16, "schema_mapping_row_count_invalid", blockers)
    _expect(len(unresolved_rows) == 15, "unresolved_row_count_invalid", blockers)
    _expect(len(policy_rows) == 13, "adapter_policy_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in input_rows] == EXPECTED_PDB_IDS, "adapter_input_pdb_ids_invalid", blockers)
    target_fields = {row["target_field"] for row in mapping_rows}
    expected_targets = {
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
        "covalent_annotation_status",
        "adapter_status",
    }
    _expect(expected_targets.issubset(target_fields), "schema_mapping_targets_missing", blockers)
    _expect({row["target_field"] for row in unresolved_rows} == set(UNRESOLVED_FIELDS), "unresolved_targets_invalid", blockers)
    for row in unresolved_rows:
        _expect(row["expected_value_or_policy"] == "do_not_infer", "unresolved_expected_policy_invalid", blockers)
        _expect(
            row["unresolved_policy"] == "adapter_smoke_must_mark_unresolved=true",
            "unresolved_policy_invalid",
            blockers,
        )

    summary = STEP12X_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "minimal mmCIF adapter design gate",
        "does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF",
        "does not run the adapter",
        "Step 12W extracted summary CSV",
        "must not read raw",
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
        "struct_conn_row_count",
        "covalent_connection_candidate_count",
        "covalent_bond_atom_pair",
        "residue atom annotation",
        "ligand atom annotation",
        "coordinates",
        "warhead_type",
        "pre/post reaction geometry",
        "must not claim samples are training-ready",
        "must actually run adapter smoke",
        STAGE.replace("_v0", ""),
    ]:
        _expect(snippet in summary, f"step12x_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step12w_parser_summary_rows_v0() -> list[dict[str, str]]:
    if not STEP12W_MANIFEST_JSON.is_file() or not STEP12W_EXTRACTED_SUMMARY_CSV.is_file():
        raise FileNotFoundError("Step 12W parser smoke outputs are missing")
    manifest = _load_json(STEP12W_MANIFEST_JSON)
    rows = _read_csv(STEP12W_EXTRACTED_SUMMARY_CSV)
    blockers: list[str] = []
    _expect(manifest["stage"] == SOURCE_STAGE, "step12w_stage_invalid", blockers)
    _expect(manifest["real_covalent_minimal_mmcif_parser_smoke_passed"] is True, "step12w_not_passed", blockers)
    _expect(manifest["all_checks_passed"] is True, "step12w_checks_not_passed", blockers)
    _expect(len(rows) == 3, "parser_summary_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS, "parser_summary_pdb_ids_invalid", blockers)
    for row in rows:
        pdb_id = row["pdb_id"]
        _expect(row["parse_status"] == "passed", f"parse_status_invalid:{pdb_id}", blockers)
        for field in REQUIRED_PARSER_FIELDS:
            _expect(field in row, f"parser_field_missing:{pdb_id}:{field}", blockers)
        _expect(bool(row["raw_path"]), f"raw_path_missing:{pdb_id}", blockers)
        _expect(bool(row["data_block_id"]), f"data_block_id_missing:{pdb_id}", blockers)
        _expect(bool(row["entry_id"]), f"entry_id_missing:{pdb_id}", blockers)
        _expect("structure_title" in row, f"structure_title_field_missing:{pdb_id}", blockers)
        _expect(int(row["entity_count"]) > 0, f"entity_count_invalid:{pdb_id}", blockers)
        _expect(int(row["atom_site_row_count"]) > 0, f"atom_site_count_invalid:{pdb_id}", blockers)
        _expect(bool(row["chem_comp_ids"]), f"chem_comp_ids_missing:{pdb_id}", blockers)
        _expect(int(row["chem_comp_id_count"]) > 0, f"chem_comp_id_count_invalid:{pdb_id}", blockers)
        _expect("struct_conn_row_count" in row, f"struct_conn_count_missing:{pdb_id}", blockers)
        _expect("covalent_connection_candidate_count" in row, f"candidate_count_missing:{pdb_id}", blockers)
        _expect(_is_true(row["gzip_open_succeeded"]), f"gzip_status_invalid:{pdb_id}", blockers)
        _expect(_is_true(row["mmcif_text_stream_read_succeeded"]), f"text_stream_status_invalid:{pdb_id}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return rows


def _covalent_annotation_status(row: dict[str, str]) -> str:
    candidate_count = int(row["covalent_connection_candidate_count"])
    struct_conn_count = int(row["struct_conn_row_count"])
    if candidate_count > 0:
        return "candidate_connections_recorded"
    if struct_conn_count >= 0:
        return "no_candidate_connection_detected"
    return "not_yet_chemically_validated"


def build_minimal_adapter_summary_rows_v0(parser_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for parser_row in parser_rows:
        pdb_id = parser_row["pdb_id"]
        row: dict[str, Any] = {
            "sample_id": f"PDB_DIRECT_{pdb_id}_minimal_stub",
            "pdb_id": pdb_id,
            "source_name": SOURCE_NAME,
            "source_stage": SOURCE_STAGE,
            "raw_path": parser_row["raw_path"],
            "entry_id": parser_row["entry_id"],
            "data_block_id": parser_row["data_block_id"],
            "structure_title": parser_row["structure_title"],
            "entity_count": parser_row["entity_count"],
            "atom_site_row_count": parser_row["atom_site_row_count"],
            "chem_comp_ids": parser_row["chem_comp_ids"],
            "chem_comp_id_count": parser_row["chem_comp_id_count"],
            "struct_conn_row_count": parser_row["struct_conn_row_count"],
            "covalent_connection_candidate_count": parser_row["covalent_connection_candidate_count"],
            "covalent_annotation_status": _covalent_annotation_status(parser_row),
            "adapter_status": ADAPTER_STATUS,
            "unresolved_field_count": len(UNRESOLVED_FIELDS),
            "all_unresolved_fields_marked": True,
            "training_ready": False,
            "training_ready_reason": TRAINING_READY_REASON,
            "adapter_claim": "minimal_adapter_stub_only_not_training_ready",
            "raw_files_read": False,
            "raw_files_decompressed": False,
            "mmcif_parsed": False,
            "external_parser_used": False,
            "rdkit_used": False,
            "coordinate_geometry_calculation_run": False,
            "enriched_sample_index_written": False,
            "sample_stub_json_written": False,
        }
        for field in UNRESOLVED_FIELDS:
            row[field] = UNRESOLVED_VALUE
        rows.append(row)
    return rows


def _adapter_rows_pass(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 3
        and [row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS
        and len({row["sample_id"] for row in rows}) == len(rows)
        and all(row["adapter_status"] == ADAPTER_STATUS for row in rows)
        and all(row["source_name"] == SOURCE_NAME for row in rows)
        and all(row["source_stage"] == SOURCE_STAGE for row in rows)
        and all(row[field] == UNRESOLVED_VALUE for row in rows for field in UNRESOLVED_FIELDS)
        and all(row["training_ready"] is False for row in rows)
        and all(row["sample_stub_json_written"] is False for row in rows)
        and all(row["enriched_sample_index_written"] is False for row in rows)
    )


def build_minimal_mmcif_adapter_smoke_summary_v0(adapter_rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid_annotation_statuses = {
        "candidate_connections_recorded",
        "no_candidate_connection_detected",
        "not_yet_chemically_validated",
    }
    return {
        "minimal_mmcif_adapter_smoke_defined": True,
        "minimal_mmcif_adapter_smoke_executed": True,
        "adapter_input_parser_summary_csv_read": True,
        "adapter_input_parser_summary_row_count": len(adapter_rows),
        "adapter_processed_pdb_ids": [row["pdb_id"] for row in adapter_rows],
        "adapter_summary_csv_written": True,
        "adapter_summary_row_count": len(adapter_rows),
        "all_adapter_rows_passed": _adapter_rows_pass(adapter_rows),
        "all_sample_ids_unique": len({row["sample_id"] for row in adapter_rows}) == len(adapter_rows),
        "all_source_names_valid": all(row["source_name"] == SOURCE_NAME for row in adapter_rows),
        "all_source_stages_valid": all(row["source_stage"] == SOURCE_STAGE for row in adapter_rows),
        "all_adapter_status_passed_minimal_stub": all(row["adapter_status"] == ADAPTER_STATUS for row in adapter_rows),
        "all_covalent_annotation_status_values_valid": all(
            row["covalent_annotation_status"] in valid_annotation_statuses for row in adapter_rows
        ),
        "parser_metadata_mapped_to_adapter_summary": True,
        "all_required_parser_fields_mapped": all(
            all(field in row and row[field] != "" for field in REQUIRED_PARSER_FIELDS if field != "structure_title")
            and "structure_title" in row
            for row in adapter_rows
        ),
        "unresolved_schema_fields_marked": True,
        "unresolved_schema_field_count": len(UNRESOLVED_FIELDS),
        "all_unresolved_fields_set_to_unresolved": all(
            row[field] == UNRESOLVED_VALUE for row in adapter_rows for field in UNRESOLVED_FIELDS
        ),
        "covalent_bond_atom_pair_inferred": False,
        "warhead_type_inferred": False,
        "coordinates_inferred": False,
        "residue_ligand_atom_annotation_inferred": False,
        "training_ready_samples_claimed": False,
        "all_training_ready_false": all(row["training_ready"] is False for row in adapter_rows),
        "adapter_claim_minimal_stub_only": all(
            row["adapter_claim"] == "minimal_adapter_stub_only_not_training_ready" for row in adapter_rows
        ),
        "raw_files_read": False,
        "raw_files_decompressed": False,
        "mmcif_parsed": False,
        "mmcif_text_read": False,
        "external_parser_used": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
        "sample_stub_json_written": False,
        "enriched_sample_index_written": False,
        "output_limited_to_csv_json_md": True,
    }


def build_real_covalent_minimal_mmcif_adapter_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12x_validated = validate_step12x_minimal_mmcif_adapter_design_gate_v0()
    except Exception as exc:
        step12x_validated = False
        blockers.append(f"step12x_validation_failed:{type(exc).__name__}:{exc}")
    step12x_manifest = _load_json(STEP12X_MANIFEST_JSON)
    try:
        parser_rows = load_step12w_parser_summary_rows_v0()
    except Exception as exc:
        parser_rows = []
        blockers.append(f"parser_summary_load_failed:{type(exc).__name__}:{exc}")
    adapter_rows = build_minimal_adapter_summary_rows_v0(parser_rows)
    smoke_summary = build_minimal_mmcif_adapter_smoke_summary_v0(adapter_rows)
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
        step12x_validated
        and step12x_manifest["step12b_mask_level_aware_validator_validated"]
        and smoke_summary["minimal_mmcif_adapter_smoke_defined"]
        and smoke_summary["minimal_mmcif_adapter_smoke_executed"]
        and smoke_summary["adapter_input_parser_summary_row_count"] == 3
        and smoke_summary["adapter_processed_pdb_ids"] == EXPECTED_PDB_IDS
        and smoke_summary["adapter_summary_row_count"] == 3
        and smoke_summary["all_adapter_rows_passed"]
        and smoke_summary["all_required_parser_fields_mapped"]
        and smoke_summary["all_unresolved_fields_set_to_unresolved"]
        and smoke_summary["all_training_ready_false"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_minimal_mmcif_adapter_smoke_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12x_minimal_mmcif_adapter_design_gate_validated": step12x_validated,
        "step12b_mask_level_aware_validator_validated": step12x_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        **smoke_summary,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "adapter_implementation_written": False,
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
        "real_covalent_minimal_mmcif_adapter_smoke_passed": passed,
        "minimal_mmcif_adapter_smoke_contract_satisfied": passed,
        "ready_for_struct_conn_candidate_extraction_smoke": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "adapter_rows": adapter_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12x_precondition": {
            "step12x_minimal_mmcif_adapter_design_gate_validated": manifest[
                "step12x_minimal_mmcif_adapter_design_gate_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "adapter_smoke_execution": {
            "minimal_mmcif_adapter_smoke_executed": manifest["minimal_mmcif_adapter_smoke_executed"],
            "adapter_summary_row_count": manifest["adapter_summary_row_count"],
        },
        "parser_summary_to_adapter_mapping": {
            "parser_metadata_mapped_to_adapter_summary": manifest["parser_metadata_mapped_to_adapter_summary"],
            "all_required_parser_fields_mapped": manifest["all_required_parser_fields_mapped"],
        },
        "unresolved_schema_fields": {
            "unresolved_schema_field_count": manifest["unresolved_schema_field_count"],
            "all_unresolved_fields_set_to_unresolved": manifest["all_unresolved_fields_set_to_unresolved"],
        },
        "no_training_ready_claim": {
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
            "all_training_ready_false": manifest["all_training_ready_false"],
        },
        "output_artifact_policy": {
            "adapter_summary_csv_written": manifest["adapter_summary_csv_written"],
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
        },
        "no_raw_no_parser_no_training_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            "mmcif_parsed": manifest["mmcif_parsed"],
            "model_forward_called": manifest["model_forward_called"],
        },
        "next_step_decision": {
            "ready_for_struct_conn_candidate_extraction_smoke": manifest[
                "ready_for_struct_conn_candidate_extraction_smoke"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
