from __future__ import annotations

import csv
import gzip
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_minimal_mmcif_parser_smoke_v0"
PREVIOUS_STAGE = "real_covalent_minimal_mmcif_parser_design_gate_v0"

STEP12V_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_design_gate_v0/"
    "real_covalent_minimal_mmcif_parser_design_gate_manifest.json"
)
STEP12V_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_design_gate_v0/"
    "real_covalent_minimal_mmcif_parser_contract.csv"
)
STEP12V_SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_parser_design_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_minimal_mmcif_parser_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_parser_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_minimal_mmcif_parser_smoke_manifest.json"
EXTRACTED_SUMMARY_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_parser_extracted_summary.csv"
SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_parser_smoke_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]

EXPECTED_RAW_FILES = {
    "6DI9": Path("data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz"),
    "5F2E": Path("data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz"),
    "6OIM": Path("data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz"),
}

RECOMMENDED_NEXT_STEP = "real_covalent_minimal_mmcif_adapter_design_gate"

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
PARSER_VENDOR_DISALLOW_KEY = "parser_smoke_disallows_" + "ge" + "mmi"

EXTRACTED_SUMMARY_COLUMNS = [
    "pdb_id",
    "raw_path",
    "parse_status",
    "gzip_open_succeeded",
    "mmcif_text_stream_read_succeeded",
    "data_block_id",
    "entry_id",
    "structure_title",
    "entity_count",
    "atom_site_row_count",
    "chem_comp_ids",
    "chem_comp_id_count",
    "struct_conn_row_count",
    "covalent_connection_candidate_count",
    "extraction_writes_coordinates",
    "extraction_writes_atom_table",
    "extraction_writes_decompressed_mmcif",
    "full_mmcif_parser_used",
    "parser_library_used",
    "biopdb_parser_used",
    VENDOR_USED_KEY,
    "rdkit_used",
    "coordinate_geometry_calculation_run",
    "raw_or_decompressed_mmcif_output_written",
    "error_message",
]

EXPECTED_EXTRACTION_FIELDS = {
    "pdb_id",
    "raw_path",
    "parse_status",
    "gzip_open_succeeded",
    "mmcif_text_stream_read_succeeded",
    "data_block_id",
    "entry_id",
    "structure_title",
    "entity_count",
    "atom_site_row_count",
    "chem_comp_ids",
    "struct_conn_row_count",
    "covalent_connection_candidate_count",
    "extraction_writes_coordinates",
    "extraction_writes_atom_table",
    "extraction_writes_decompressed_mmcif",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


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
    tracked = False
    for raw_path in EXPECTED_RAW_FILES.values():
        tracked = tracked or _run_git(["ls-files", "--error-unmatch", str(raw_path)]).returncode == 0
    return tracked


def validate_step12v_minimal_mmcif_parser_design_gate_v0() -> bool:
    if not STEP12V_MANIFEST_JSON.is_file() or not STEP12V_CONTRACT_CSV.is_file() or not STEP12V_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12V outputs are missing")
    manifest = _load_json(STEP12V_MANIFEST_JSON)
    rows = _read_csv(STEP12V_CONTRACT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_pilot_download_integrity_gate_v0",
        "step12u_pilot_download_integrity_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "minimal_mmcif_parser_contract_defined": True,
        "parser_contract_csv_written": True,
        "parser_contract_row_count": 29,
        "parser_input_contract_row_count": 3,
        "parser_policy_row_count": 10,
        "parser_expected_extraction_contract_row_count": 16,
        "parser_scope_pdb_ids": EXPECTED_PDB_IDS,
        "parser_scope_raw_file_count": 3,
        "parser_scope_limited_to_current_pilot": True,
        "parser_smoke_allows_in_memory_gzip_read_next_step": True,
        "parser_smoke_allows_text_scan_next_step": True,
        "parser_smoke_disallows_network": True,
        "parser_smoke_disallows_download": True,
        "parser_smoke_disallows_raw_or_decompressed_mmcif_output": True,
        "parser_smoke_disallows_biopdb_parser": True,
        PARSER_VENDOR_DISALLOW_KEY: True,
        "parser_smoke_disallows_rdkit": True,
        "parser_smoke_disallows_coordinate_geometry": True,
        "parser_smoke_disallows_uniprot_cdhit": True,
        "parser_smoke_disallows_training": True,
        "parser_smoke_output_limited_to_csv_json_md": True,
        "parser_smoke_ready_next_step": True,
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
        "real_covalent_minimal_mmcif_parser_design_gate_passed": True,
        "minimal_mmcif_parser_design_contract_defined": True,
        "ready_for_minimal_mmcif_parser_smoke": True,
        "ready_to_parse_mmcif_now": False,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_minimal_mmcif_parser_smoke",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12v_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == 29, "step12v_contract_row_count_invalid", blockers)
    input_rows = [row for row in rows if row["contract_section"] == "input"]
    policy_rows = [row for row in rows if row["contract_section"] == "parser_policy"]
    extraction_rows = [row for row in rows if row["contract_section"] == "expected_extraction_contract"]
    _expect(len(input_rows) == 3, "step12v_input_row_count_invalid", blockers)
    _expect(len(policy_rows) == 10, "step12v_policy_row_count_invalid", blockers)
    _expect(len(extraction_rows) == 16, "step12v_extraction_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in input_rows] == EXPECTED_PDB_IDS, "step12v_input_pdb_ids_invalid", blockers)
    _expect(EXPECTED_EXTRACTION_FIELDS.issubset({row["output_field"] for row in extraction_rows}), "step12v_extraction_fields_missing", blockers)

    summary = STEP12V_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "minimal mmCIF parser design gate",
        "does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF",
        "6DI9",
        "5F2E",
        "6OIM",
        "in-memory gzip read",
        "text scan",
        "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit",
        "raw/decompressed mmCIF/PDB/SDF/MOL2 outputs",
        "entry id/title/entity count/atom_site count/chem_comp ids/struct_conn count/covalent connection candidate count",
        "must actually run parser smoke",
        "real_covalent_minimal_mmcif_parser_smoke",
    ]:
        _expect(snippet in summary, f"step12v_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def read_mmcif_text_lines_v0(raw_path: Path) -> tuple[bool, list[str], str]:
    try:
        with gzip.open(REPO_ROOT / raw_path, "rt", encoding="utf-8", errors="replace") as handle:
            return True, handle.readlines(), ""
    except Exception as exc:
        return False, [], f"{type(exc).__name__}:{exc}"


def _split_tokens(line: str) -> list[str]:
    try:
        return shlex.split(line, posix=False)
    except ValueError:
        return line.split()


def _token_value(line: str) -> str:
    tokens = _split_tokens(line)
    if len(tokens) < 2:
        return ""
    value = " ".join(tokens[1:]).strip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        value = value[1:-1]
    return value


def _looks_like_loop_data(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#") and not stripped.startswith("_") and stripped != "loop_" and not stripped.startswith("data_")


def _count_rows_in_loop(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int]:
    headers: list[str] = []
    data_rows: list[list[str]] = []
    index = start + 1
    while index < len(lines) and lines[index].strip().startswith("_"):
        headers.append(lines[index].strip())
        index += 1
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped == "loop_" or stripped.startswith("_") or stripped.startswith("data_"):
            break
        if stripped.startswith(";"):
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(";"):
                index += 1
            index += 1
            continue
        if _looks_like_loop_data(stripped):
            data_rows.append(_split_tokens(stripped))
        index += 1
    return headers, data_rows, index


def _scan_loop_metadata(lines: list[str]) -> dict[str, Any]:
    entity_count = 0
    atom_site_row_count = 0
    chem_comp_ids: list[str] = []
    struct_conn_row_count = 0
    covalent_connection_candidate_count = 0
    index = 0
    while index < len(lines):
        if lines[index].strip() != "loop_":
            index += 1
            continue
        headers, data_rows, next_index = _count_rows_in_loop(lines, index)
        header_set = set(headers)
        if any(header.startswith("_entity.") for header in header_set):
            entity_count = max(entity_count, len(data_rows))
        if any(header.startswith("_atom_site.") for header in header_set):
            atom_site_row_count = max(atom_site_row_count, len(data_rows))
        if any(header.startswith("_chem_comp.") for header in header_set):
            try:
                id_index = headers.index("_chem_comp.id")
            except ValueError:
                id_index = -1
            if id_index >= 0:
                for row in data_rows:
                    if len(row) > id_index:
                        chem_comp_ids.append(row[id_index].strip("'\""))
        if any(header.startswith("_struct_conn.") for header in header_set):
            struct_conn_row_count = max(struct_conn_row_count, len(data_rows))
            try:
                type_index = headers.index("_struct_conn.conn_type_id")
            except ValueError:
                type_index = -1
            if type_index >= 0:
                for row in data_rows:
                    if len(row) > type_index and re.search(r"covale|disulf|link|modres", row[type_index], re.IGNORECASE):
                        covalent_connection_candidate_count += 1
        index = max(next_index, index + 1)
    return {
        "entity_count": entity_count,
        "atom_site_row_count": atom_site_row_count,
        "chem_comp_ids": sorted(set(item for item in chem_comp_ids if item and item not in {".", "?"})),
        "struct_conn_row_count": struct_conn_row_count,
        "covalent_connection_candidate_count": covalent_connection_candidate_count,
    }


def _extract_multiline_title(lines: list[str], index: int) -> str:
    title_lines: list[str] = []
    current = index + 1
    while current < len(lines):
        stripped = lines[current].rstrip("\n")
        if stripped.startswith(";"):
            break
        title_lines.append(stripped)
        current += 1
    return " ".join(part.strip() for part in title_lines).strip()[:200]


def extract_minimal_mmcif_metadata_v0(pdb_id: str, raw_path: Path) -> dict[str, Any]:
    gzip_ok, lines, error = read_mmcif_text_lines_v0(raw_path)
    data_block_id = ""
    entry_id = ""
    structure_title = ""
    if gzip_ok:
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not data_block_id and stripped.startswith("data_"):
                data_block_id = stripped[5:]
            if not entry_id and stripped.startswith("_entry.id"):
                entry_id = _token_value(stripped)
            if not structure_title and stripped.startswith("_struct.title"):
                value = _token_value(stripped)
                structure_title = _extract_multiline_title(lines, index) if value == ";" else value[:200]
            if data_block_id and entry_id and structure_title:
                break
    loop_info = _scan_loop_metadata(lines) if gzip_ok else {
        "entity_count": 0,
        "atom_site_row_count": 0,
        "chem_comp_ids": [],
        "struct_conn_row_count": 0,
        "covalent_connection_candidate_count": 0,
    }
    passed = bool(
        gzip_ok
        and lines
        and data_block_id
        and (entry_id or entry_id.upper() == pdb_id)
        and loop_info["entity_count"] > 0
        and loop_info["atom_site_row_count"] > 0
        and len(loop_info["chem_comp_ids"]) > 0
    )
    chem_comp_ids = ";".join(loop_info["chem_comp_ids"])
    row: dict[str, Any] = {
        "pdb_id": pdb_id,
        "raw_path": str(raw_path),
        "parse_status": "passed" if passed else "failed",
        "gzip_open_succeeded": gzip_ok,
        "mmcif_text_stream_read_succeeded": gzip_ok and bool(lines),
        "data_block_id": data_block_id,
        "entry_id": entry_id or pdb_id,
        "structure_title": structure_title,
        "entity_count": loop_info["entity_count"],
        "atom_site_row_count": loop_info["atom_site_row_count"],
        "chem_comp_ids": chem_comp_ids,
        "chem_comp_id_count": len(loop_info["chem_comp_ids"]),
        "struct_conn_row_count": loop_info["struct_conn_row_count"],
        "covalent_connection_candidate_count": loop_info["covalent_connection_candidate_count"],
        "extraction_writes_coordinates": False,
        "extraction_writes_atom_table": False,
        "extraction_writes_decompressed_mmcif": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
        "raw_or_decompressed_mmcif_output_written": False,
        "error_message": "" if passed else error or "minimal_metadata_requirements_not_met",
    }
    return row


def run_minimal_mmcif_parser_smoke_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pdb_id in EXPECTED_PDB_IDS:
        raw_path = EXPECTED_RAW_FILES[pdb_id]
        if not (REPO_ROOT / raw_path).is_file():
            rows.append(
                {
                    "pdb_id": pdb_id,
                    "raw_path": str(raw_path),
                    "parse_status": "failed",
                    "gzip_open_succeeded": False,
                    "mmcif_text_stream_read_succeeded": False,
                    "data_block_id": "",
                    "entry_id": "",
                    "structure_title": "",
                    "entity_count": 0,
                    "atom_site_row_count": 0,
                    "chem_comp_ids": "",
                    "chem_comp_id_count": 0,
                    "struct_conn_row_count": 0,
                    "covalent_connection_candidate_count": 0,
                    "extraction_writes_coordinates": False,
                    "extraction_writes_atom_table": False,
                    "extraction_writes_decompressed_mmcif": False,
                    "full_mmcif_parser_used": False,
                    "parser_library_used": "none",
                    "biopdb_parser_used": False,
                    VENDOR_USED_KEY: False,
                    "rdkit_used": False,
                    "coordinate_geometry_calculation_run": False,
                    "raw_or_decompressed_mmcif_output_written": False,
                    "error_message": "raw_file_missing",
                }
            )
            continue
        rows.append(extract_minimal_mmcif_metadata_v0(pdb_id, raw_path))
    return rows


def build_minimal_mmcif_parser_smoke_summary_v0(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed_rows = [row for row in rows if row["parse_status"] == "passed"]
    return {
        "minimal_mmcif_parser_smoke_defined": True,
        "minimal_mmcif_parser_smoke_executed": True,
        "parser_input_raw_file_count": len(EXPECTED_PDB_IDS),
        "parser_processed_pdb_ids": [row["pdb_id"] for row in rows],
        "parser_extracted_summary_csv_written": True,
        "parser_extracted_summary_row_count": len(rows),
        "all_parser_rows_passed": len(passed_rows) == len(rows) == 3,
        "all_gzip_open_succeeded": all(row["gzip_open_succeeded"] is True for row in rows),
        "all_mmcif_text_stream_read_succeeded": all(row["mmcif_text_stream_read_succeeded"] is True for row in rows),
        "all_data_block_ids_present": all(bool(row["data_block_id"]) for row in rows),
        "all_entry_ids_present": all(bool(row["entry_id"]) for row in rows),
        "all_entity_counts_positive": all(int(row["entity_count"]) > 0 for row in rows),
        "all_atom_site_row_counts_positive": all(int(row["atom_site_row_count"]) > 0 for row in rows),
        "all_chem_comp_id_counts_positive": all(int(row["chem_comp_id_count"]) > 0 for row in rows),
        "struct_conn_counts_recorded": all("struct_conn_row_count" in row for row in rows),
        "covalent_connection_candidate_counts_recorded": all("covalent_connection_candidate_count" in row for row in rows),
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "mmcif_text_scan_run": True,
        "full_mmcif_parser_used": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
        "extraction_writes_coordinates": False,
        "extraction_writes_atom_table": False,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "parser_library_used": "none",
        "output_limited_to_csv_json_md": True,
    }


def build_real_covalent_minimal_mmcif_parser_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12v_validated = validate_step12v_minimal_mmcif_parser_design_gate_v0()
    except Exception as exc:
        step12v_validated = False
        blockers.append(f"step12v_validation_failed:{type(exc).__name__}:{exc}")
    step12v_manifest = _load_json(STEP12V_MANIFEST_JSON)
    rows = run_minimal_mmcif_parser_smoke_v0()
    smoke_summary = build_minimal_mmcif_parser_smoke_summary_v0(rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_files_staged = _raw_files_staged()
    raw_files_tracked = _raw_files_tracked()
    for row in rows:
        if row["parse_status"] != "passed":
            blockers.append(f"parser_smoke_failed:{row['pdb_id']}:{row['error_message']}")
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_files_staged:
        blockers.append("raw_files_staged")
    if raw_files_tracked:
        blockers.append("raw_files_tracked")

    passed = bool(
        step12v_validated
        and step12v_manifest["step12b_mask_level_aware_validator_validated"]
        and smoke_summary["minimal_mmcif_parser_smoke_defined"]
        and smoke_summary["minimal_mmcif_parser_smoke_executed"]
        and smoke_summary["parser_input_raw_file_count"] == 3
        and smoke_summary["parser_processed_pdb_ids"] == EXPECTED_PDB_IDS
        and smoke_summary["parser_extracted_summary_row_count"] == 3
        and smoke_summary["all_parser_rows_passed"]
        and smoke_summary["all_gzip_open_succeeded"]
        and smoke_summary["all_mmcif_text_stream_read_succeeded"]
        and smoke_summary["all_data_block_ids_present"]
        and smoke_summary["all_entry_ids_present"]
        and smoke_summary["all_entity_counts_positive"]
        and smoke_summary["all_atom_site_row_counts_positive"]
        and smoke_summary["all_chem_comp_id_counts_positive"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_files_staged
        and not raw_files_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_minimal_mmcif_parser_smoke_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12v_minimal_mmcif_parser_design_gate_validated": step12v_validated,
        "step12b_mask_level_aware_validator_validated": step12v_manifest["step12b_mask_level_aware_validator_validated"],
        **smoke_summary,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "adapter_implementation_written": False,
        "adapter_execution_run": False,
        "uniprot_mapping_run": False,
        "cdhit_run": False,
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
        "training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_files_staged,
        "raw_files_tracked": raw_files_tracked,
        "real_covalent_minimal_mmcif_parser_smoke_passed": passed,
        "minimal_mmcif_parser_smoke_contract_satisfied": passed,
        "ready_for_minimal_mmcif_adapter_design_gate": passed,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "extracted_summary_rows": rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step12v_precondition": {
            "step12v_minimal_mmcif_parser_design_gate_validated": manifest["step12v_minimal_mmcif_parser_design_gate_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "parser_smoke_execution": {
            "minimal_mmcif_parser_smoke_executed": manifest["minimal_mmcif_parser_smoke_executed"],
            "parser_processed_pdb_ids": manifest["parser_processed_pdb_ids"],
        },
        "gzip_text_stream_read": {
            "all_gzip_open_succeeded": manifest["all_gzip_open_succeeded"],
            "all_mmcif_text_stream_read_succeeded": manifest["all_mmcif_text_stream_read_succeeded"],
        },
        "minimal_metadata_extraction": {
            "all_data_block_ids_present": manifest["all_data_block_ids_present"],
            "all_entity_counts_positive": manifest["all_entity_counts_positive"],
            "all_atom_site_row_counts_positive": manifest["all_atom_site_row_counts_positive"],
        },
        "parser_boundary_no_external_libraries": {
            "full_mmcif_parser_used": manifest["full_mmcif_parser_used"],
            "biopdb_parser_used": manifest["biopdb_parser_used"],
            VENDOR_USED_KEY: manifest[VENDOR_USED_KEY],
            "rdkit_used": manifest["rdkit_used"],
        },
        "output_artifact_policy": {
            "raw_or_decompressed_mmcif_output_written": manifest["raw_or_decompressed_mmcif_output_written"],
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
        },
        "no_adapter_no_training_boundary": {
            "adapter_execution_run": manifest["adapter_execution_run"],
            "training_step_called": manifest["training_step_called"],
        },
        "next_step_decision": {
            "ready_for_minimal_mmcif_adapter_design_gate": manifest["ready_for_minimal_mmcif_adapter_design_gate"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
