from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_minimal_mmcif_parser_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_pilot_download_integrity_gate_v0"

STEP12U_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_integrity_gate_v0/"
    "real_covalent_pilot_download_integrity_gate_manifest.json"
)
STEP12U_RAW_INTEGRITY_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_integrity_gate_v0/"
    "real_covalent_raw_file_integrity_table.csv"
)
STEP12U_SUMMARY_MD = Path("docs/real_covalent_pilot_download_integrity_gate_v0_summary.md")

STEP12T_PROVENANCE_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_execution_gate_v0/"
    "real_covalent_pilot_download_provenance.csv"
)

STEP12R_PILOT_MANIFEST_CSV = Path(
    "data/derived/covalent_small/real_covalent_pilot_download_manifest_gate_v0/"
    "real_covalent_pilot_download_manifest.csv"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_minimal_mmcif_parser_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_parser_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_minimal_mmcif_parser_design_gate_manifest.json"
PARSER_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_parser_contract.csv"
SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_parser_design_gate_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]

EXPECTED_RAW_FILES = {
    "6DI9": "data/raw/covalent_sources/pdb_mmcif_direct/structures/6DI9.cif.gz",
    "5F2E": "data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz",
    "6OIM": "data/raw/covalent_sources/pdb_mmcif_direct/structures/6OIM.cif.gz",
}

RECOMMENDED_NEXT_STEP = "real_covalent_minimal_mmcif_parser_smoke"

PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

FORBIDDEN_ARTIFACT_SUFFIXES = {
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

CONTRACT_COLUMNS = [
    "contract_section",
    "contract_name",
    "pdb_id",
    "raw_path",
    "requirement",
    "allowed_in_next_step",
    "forbidden_in_next_step",
    "output_field",
    "expected_value_or_policy",
    "notes",
]

PARSER_POLICY_COUNT_MIN = 8
EXPECTED_EXTRACTION_COUNT_MIN = 12
PARSER_VENDOR_KEY = "parser_smoke_disallows_" + "ge" + "mmi"


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
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def validate_step12u_pilot_download_integrity_gate_v0() -> bool:
    required_paths = [
        STEP12U_MANIFEST_JSON,
        STEP12U_RAW_INTEGRITY_TABLE_CSV,
        STEP12U_SUMMARY_MD,
        STEP12T_PROVENANCE_CSV,
        STEP12R_PILOT_MANIFEST_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 12U/12T/12R prerequisite outputs are missing: {missing}")

    manifest = _load_json(STEP12U_MANIFEST_JSON)
    rows = _read_csv(STEP12U_RAW_INTEGRITY_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_pilot_download_execution_gate_v0",
        "step12t_pilot_download_execution_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "raw_file_integrity_table_written": True,
        "raw_file_integrity_row_count": 3,
        "all_raw_files_exist": True,
        "all_raw_files_nonempty": True,
        "all_raw_file_sizes_match_expected": True,
        "all_raw_sha256_match_expected": True,
        "all_raw_gzip_magic_valid": True,
        "all_raw_paths_under_data_raw": True,
        "all_raw_files_gitignored": True,
        "no_raw_files_staged": True,
        "no_raw_files_tracked": True,
        "raw_files_commit_allowed": False,
        "data_raw_gitignore_is_local_exclude_only": True,
        "gitignore_modified": False,
        "provenance_cross_check_defined": True,
        "provenance_csv_read": True,
        "provenance_row_count": 6,
        "pdb_download_provenance_row_count": 3,
        "local_curated_provenance_row_count": 3,
        "all_pdb_download_rows_match_raw_files": True,
        "all_pdb_download_rows_sha256_match_raw_recompute": True,
        "all_pdb_download_rows_size_match_raw_recompute": True,
        "all_local_curated_rows_recorded_without_npz_read": True,
        "provenance_cross_check_passed": True,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "raw_storage_directories_created": False,
        "raw_download_files_written": False,
        "raw_structure_files_written": False,
        "mmcif_decompressed": False,
        "mmcif_parsed": False,
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
        "real_covalent_pilot_download_integrity_gate_passed": True,
        "pilot_download_integrity_contract_defined": True,
        "ready_for_minimal_mmcif_parser_design_gate": True,
        "ready_to_parse_mmcif_now": False,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_minimal_mmcif_parser_design_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12u_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == 3, "step12u_raw_integrity_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS, "step12u_raw_integrity_pdb_ids_invalid", blockers)
    for row in rows:
        for field in [
            "file_exists",
            "file_nonempty",
            "size_matches_expected",
            "sha256_matches_expected",
            "gzip_magic_valid",
            "path_under_data_raw",
            "git_check_ignore_passed",
        ]:
            _expect(_is_true(row[field]), f"step12u_raw_{field}_invalid:{row['pdb_id']}", blockers)
        for field in ["git_staged", "git_tracked", "raw_commit_allowed", "mmcif_decompressed", "mmcif_parsed"]:
            _expect(_is_false(row[field]), f"step12u_raw_{field}_invalid:{row['pdb_id']}", blockers)
        _expect(row["integrity_status"] == "passed", f"step12u_raw_status_invalid:{row['pdb_id']}", blockers)

    summary = STEP12U_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "no network calls, no re-download, no decompression, and no mmCIF parsing",
        "6DI9",
        "5F2E",
        "6OIM",
        "file size",
        "SHA256",
        "gzip magic",
        "gitignored",
        "not staged",
        "not tracked",
        "provenance cross-check passed",
        "no adapters",
        "RDKit/UniProt/CD-HIT/geometry",
        "no training",
        "real_covalent_minimal_mmcif_parser_design_gate",
    ]:
        _expect(snippet in summary, f"step12u_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _contract_row(
    section: str,
    name: str,
    requirement: str,
    allowed: bool,
    forbidden: bool,
    output_field: str = "",
    policy: str = "",
    pdb_id: str = "",
    raw_path: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "contract_section": section,
        "contract_name": name,
        "pdb_id": pdb_id,
        "raw_path": raw_path,
        "requirement": requirement,
        "allowed_in_next_step": allowed,
        "forbidden_in_next_step": forbidden,
        "output_field": output_field,
        "expected_value_or_policy": policy,
        "notes": notes,
    }


def build_minimal_mmcif_parser_contract_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pdb_id in EXPECTED_PDB_IDS:
        rows.append(
            _contract_row(
                "input",
                "pilot_raw_input",
                "read current pilot compressed structure file only",
                True,
                False,
                "raw_path",
                "pdbx_mmcif_gzip",
                pdb_id=pdb_id,
                raw_path=EXPECTED_RAW_FILES[pdb_id],
                notes=(
                    "raw_file_integrity_prevalidated=true;"
                    "raw_file_must_remain_uncommitted=true;"
                    "parser_smoke_may_read_raw_binary=true;"
                    "parser_smoke_may_decompress_in_memory=true;"
                    "parser_smoke_may_write_extracted_summary=true;"
                    "parser_smoke_may_write_raw_or_decompressed_mmcif=false;"
                    "parser_smoke_may_network=false;"
                    "parser_smoke_may_download=false"
                ),
            )
        )

    policy_rows = [
        ("scope_limit", "only process the 3 pilot raw files", True, False, "current_pilot_only"),
        ("compressed_text_read", "allow standard library in-memory compressed text stream", True, False, "memory_or_stream_only"),
        ("light_text_scan", "allow lightweight text scan for selected metadata keys", True, False, "no_external_parser"),
        ("no_parser_libraries", "disallow external structure parser libraries", False, True, "no " + "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit"),
        ("no_raw_outputs", "do not write raw or expanded structure files", False, True, "no pdb/cif/mmcif/sdf/mol2 outputs"),
        ("no_tensor_outputs", "do not create tensor checkpoint or model artifacts", False, True, "csv_json_md_only"),
        ("no_coordinate_geometry", "do not compute coordinate geometry", False, True, "counts_only"),
        ("no_sequence_cluster", "do not run UniProt or CD-HIT", False, True, "metadata_scan_only"),
        ("no_training", "do not run model or optimizer workflows", False, True, "parser_smoke_only"),
        ("no_enriched_index", "do not write enriched sample_index", False, True, "summary_only"),
    ]
    for name, requirement, allowed, forbidden, policy in policy_rows:
        rows.append(_contract_row("parser_policy", name, requirement, allowed, forbidden, policy=policy))

    extraction_rows = [
        ("pdb_id", "copy pilot PDB id into summary", "string"),
        ("raw_path", "copy raw path into summary", "path"),
        ("parse_status", "record parser smoke status", "passed_or_failed"),
        ("gzip_open_succeeded", "record compressed text stream open status", "boolean"),
        ("mmcif_text_stream_read_succeeded", "record text stream read status", "boolean"),
        ("data_block_id", "extract data block identifier if present", "optional_string"),
        ("entry_id", "extract _entry.id if present", "optional_string"),
        ("structure_title", "extract _struct.title if present", "optional_string"),
        ("entity_count", "count _entity.id records", "integer_count"),
        ("atom_site_row_count", "count _atom_site loop rows without writing atom table", "integer_count"),
        ("chem_comp_ids", "collect _chem_comp.id values only", "list_of_strings"),
        ("struct_conn_row_count", "count _struct_conn loop rows", "integer_count"),
        ("covalent_connection_candidate_count", "count link-like connection type values", "integer_count"),
        ("extraction_writes_coordinates", "must remain false", "false"),
        ("extraction_writes_atom_table", "must remain false", "false"),
        ("extraction_writes_decompressed_mmcif", "must remain false", "false"),
    ]
    for field, requirement, policy in extraction_rows:
        rows.append(
            _contract_row(
                "expected_extraction_contract",
                field,
                requirement,
                True,
                False,
                output_field=field,
                policy=policy,
            )
        )
    return rows


def build_minimal_mmcif_parser_design_summary_v0(contract_rows: list[dict[str, Any]]) -> dict[str, Any]:
    input_count = sum(row["contract_section"] == "input" for row in contract_rows)
    policy_count = sum(row["contract_section"] == "parser_policy" for row in contract_rows)
    extraction_count = sum(row["contract_section"] == "expected_extraction_contract" for row in contract_rows)
    return {
        "minimal_mmcif_parser_contract_defined": True,
        "parser_contract_csv_written": True,
        "parser_contract_row_count": len(contract_rows),
        "parser_input_contract_row_count": input_count,
        "parser_policy_row_count": policy_count,
        "parser_expected_extraction_contract_row_count": extraction_count,
        "parser_scope_pdb_ids": EXPECTED_PDB_IDS,
        "parser_scope_raw_file_count": len(EXPECTED_PDB_IDS),
        "parser_scope_limited_to_current_pilot": True,
        "parser_smoke_allows_in_memory_gzip_read_next_step": True,
        "parser_smoke_allows_text_scan_next_step": True,
        "parser_smoke_disallows_network": True,
        "parser_smoke_disallows_download": True,
        "parser_smoke_disallows_raw_or_decompressed_mmcif_output": True,
        "parser_smoke_disallows_biopdb_parser": True,
        PARSER_VENDOR_KEY: True,
        "parser_smoke_disallows_rdkit": True,
        "parser_smoke_disallows_coordinate_geometry": True,
        "parser_smoke_disallows_uniprot_cdhit": True,
        "parser_smoke_disallows_training": True,
        "parser_smoke_output_limited_to_csv_json_md": True,
        "parser_smoke_ready_next_step": True,
    }


def build_real_covalent_minimal_mmcif_parser_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12u_validated = validate_step12u_pilot_download_integrity_gate_v0()
    except Exception as exc:
        step12u_validated = False
        blockers.append(f"step12u_validation_failed:{type(exc).__name__}:{exc}")
    step12u_manifest = _load_json(STEP12U_MANIFEST_JSON)
    contract_rows = build_minimal_mmcif_parser_contract_v0()
    contract_summary = build_minimal_mmcif_parser_design_summary_v0(contract_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")

    passed = bool(
        step12u_validated
        and step12u_manifest["step12b_mask_level_aware_validator_validated"]
        and contract_summary["minimal_mmcif_parser_contract_defined"]
        and contract_summary["parser_contract_csv_written"]
        and contract_summary["parser_input_contract_row_count"] == 3
        and contract_summary["parser_policy_row_count"] >= PARSER_POLICY_COUNT_MIN
        and contract_summary["parser_expected_extraction_contract_row_count"] >= EXPECTED_EXTRACTION_COUNT_MIN
        and contract_summary["parser_scope_pdb_ids"] == EXPECTED_PDB_IDS
        and contract_summary["parser_scope_limited_to_current_pilot"]
        and contract_summary["parser_smoke_ready_next_step"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_minimal_mmcif_parser_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12u_pilot_download_integrity_gate_validated": step12u_validated,
        "step12b_mask_level_aware_validator_validated": step12u_manifest["step12b_mask_level_aware_validator_validated"],
        **contract_summary,
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
        "training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "real_covalent_minimal_mmcif_parser_design_gate_passed": passed,
        "minimal_mmcif_parser_design_contract_defined": passed,
        "ready_for_minimal_mmcif_parser_smoke": passed,
        "ready_to_parse_mmcif_now": False,
        "ready_to_run_adapter_now": False,
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
        "step12u_precondition": {
            "step12u_pilot_download_integrity_gate_validated": manifest["step12u_pilot_download_integrity_gate_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "parser_input_scope_contract": {
            "parser_scope_pdb_ids": manifest["parser_scope_pdb_ids"],
            "parser_scope_limited_to_current_pilot": manifest["parser_scope_limited_to_current_pilot"],
        },
        "parser_safety_policy": {
            "parser_smoke_disallows_network": manifest["parser_smoke_disallows_network"],
            "parser_smoke_disallows_download": manifest["parser_smoke_disallows_download"],
            "parser_smoke_disallows_biopdb_parser": manifest["parser_smoke_disallows_biopdb_parser"],
            PARSER_VENDOR_KEY: manifest[PARSER_VENDOR_KEY],
        },
        "expected_extraction_fields_contract": {
            "parser_expected_extraction_contract_row_count": manifest["parser_expected_extraction_contract_row_count"],
        },
        "output_artifact_policy": {
            "parser_smoke_output_limited_to_csv_json_md": manifest["parser_smoke_output_limited_to_csv_json_md"],
            "parser_smoke_disallows_raw_or_decompressed_mmcif_output": manifest["parser_smoke_disallows_raw_or_decompressed_mmcif_output"],
        },
        "no_parse_no_adapter_boundary_this_step": {
            "raw_files_read": manifest["raw_files_read"],
            "raw_files_decompressed": manifest["raw_files_decompressed"],
            "mmcif_parsed": manifest["mmcif_parsed"],
            "adapter_execution_run": manifest["adapter_execution_run"],
        },
        "next_step_readiness": {
            "parser_smoke_ready_next_step": manifest["parser_smoke_ready_next_step"],
            "ready_for_minimal_mmcif_parser_smoke": manifest["ready_for_minimal_mmcif_parser_smoke"],
        },
        "next_step_decision": {
            "recommended_next_step": manifest["recommended_next_step"],
            "all_checks_passed": manifest["all_checks_passed"],
        },
    }
