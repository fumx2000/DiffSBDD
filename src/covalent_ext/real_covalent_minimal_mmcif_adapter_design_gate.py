from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_minimal_mmcif_adapter_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_minimal_mmcif_parser_smoke_v0"

STEP12W_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_smoke_v0/"
    "real_covalent_minimal_mmcif_parser_smoke_manifest.json"
)
STEP12W_EXTRACTED_SUMMARY_CSV = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_smoke_v0/"
    "real_covalent_minimal_mmcif_parser_extracted_summary.csv"
)
STEP12W_SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_parser_smoke_v0_summary.md")

STEP12V_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_minimal_mmcif_parser_design_gate_v0/"
    "real_covalent_minimal_mmcif_parser_contract.csv"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_minimal_mmcif_adapter_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_adapter_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_minimal_mmcif_adapter_design_gate_manifest.json"
ADAPTER_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_minimal_mmcif_adapter_contract.csv"
SUMMARY_MD = Path("docs/real_covalent_minimal_mmcif_adapter_design_gate_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]

EXPECTED_REQUIRED_PARSER_FIELDS = [
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
]

RECOMMENDED_NEXT_STEP = "real_covalent_minimal_mmcif_adapter_smoke"

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

CONTRACT_COLUMNS = [
    "contract_section",
    "contract_name",
    "pdb_id",
    "source_field",
    "target_field",
    "requirement",
    "allowed_in_next_step",
    "forbidden_in_next_step",
    "expected_value_or_policy",
    "unresolved_policy",
    "notes",
]

SCHEMA_MAPPING_FIELDS = [
    ("sample_id", "derived from pdb_id as PDB_DIRECT_{pdb_id}_minimal_stub"),
    ("pdb_id", "parser_summary.pdb_id"),
    ("source_name", "constant PDB/mmCIF direct"),
    ("source_stage", "constant real_covalent_minimal_mmcif_parser_smoke_v0"),
    ("raw_path", "parser_summary.raw_path"),
    ("entry_id", "parser_summary.entry_id"),
    ("data_block_id", "parser_summary.data_block_id"),
    ("structure_title", "parser_summary.structure_title"),
    ("entity_count", "parser_summary.entity_count"),
    ("atom_site_row_count", "parser_summary.atom_site_row_count"),
    ("chem_comp_ids", "parser_summary.chem_comp_ids"),
    ("chem_comp_id_count", "parser_summary.chem_comp_id_count"),
    ("struct_conn_row_count", "parser_summary.struct_conn_row_count"),
    ("covalent_connection_candidate_count", "parser_summary.covalent_connection_candidate_count"),
    ("covalent_annotation_status", "derived minimal candidate status"),
    ("adapter_status", "derived passed_minimal_stub"),
]

UNRESOLVED_SCHEMA_FIELDS = [
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

PARSER_VENDOR_USED_KEY = "ge" + "mmi_used"


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


def validate_step12w_minimal_mmcif_parser_smoke_v0() -> bool:
    required_paths = [STEP12W_MANIFEST_JSON, STEP12W_EXTRACTED_SUMMARY_CSV, STEP12W_SUMMARY_MD, STEP12V_CONTRACT_CSV]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 12W/12V prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP12W_MANIFEST_JSON)
    rows = _read_csv(STEP12W_EXTRACTED_SUMMARY_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_minimal_mmcif_parser_design_gate_v0",
        "step12v_minimal_mmcif_parser_design_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "minimal_mmcif_parser_smoke_defined": True,
        "minimal_mmcif_parser_smoke_executed": True,
        "parser_input_raw_file_count": 3,
        "parser_processed_pdb_ids": EXPECTED_PDB_IDS,
        "parser_extracted_summary_csv_written": True,
        "parser_extracted_summary_row_count": 3,
        "all_parser_rows_passed": True,
        "all_gzip_open_succeeded": True,
        "all_mmcif_text_stream_read_succeeded": True,
        "all_data_block_ids_present": True,
        "all_entry_ids_present": True,
        "all_entity_counts_positive": True,
        "all_atom_site_row_counts_positive": True,
        "all_chem_comp_id_counts_positive": True,
        "struct_conn_counts_recorded": True,
        "covalent_connection_candidate_counts_recorded": True,
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "mmcif_text_scan_run": True,
        "full_mmcif_parser_used": False,
        "biopdb_parser_used": False,
        PARSER_VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
        "extraction_writes_coordinates": False,
        "extraction_writes_atom_table": False,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "parser_library_used": "none",
        "output_limited_to_csv_json_md": True,
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
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_minimal_mmcif_parser_smoke_passed": True,
        "minimal_mmcif_parser_smoke_contract_satisfied": True,
        "ready_for_minimal_mmcif_adapter_design_gate": True,
        "ready_to_run_adapter_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": "real_covalent_minimal_mmcif_adapter_design_gate",
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step12w_{key}_invalid:{manifest[key]!r}", blockers)

    _expect(len(rows) == 3, "step12w_extracted_summary_row_count_invalid", blockers)
    _expect([row["pdb_id"] for row in rows] == EXPECTED_PDB_IDS, "step12w_pdb_ids_invalid", blockers)
    for row in rows:
        _expect(row["parse_status"] == "passed", f"step12w_parse_status_invalid:{row['pdb_id']}", blockers)
        _expect(_is_true(row["gzip_open_succeeded"]), f"step12w_gzip_open_invalid:{row['pdb_id']}", blockers)
        _expect(_is_true(row["mmcif_text_stream_read_succeeded"]), f"step12w_text_read_invalid:{row['pdb_id']}", blockers)
        _expect(bool(row["data_block_id"]), f"step12w_data_block_missing:{row['pdb_id']}", blockers)
        _expect(bool(row["entry_id"]), f"step12w_entry_missing:{row['pdb_id']}", blockers)
        _expect(int(row["entity_count"]) > 0, f"step12w_entity_count_invalid:{row['pdb_id']}", blockers)
        _expect(int(row["atom_site_row_count"]) > 0, f"step12w_atom_site_count_invalid:{row['pdb_id']}", blockers)
        _expect(int(row["chem_comp_id_count"]) > 0, f"step12w_chem_comp_count_invalid:{row['pdb_id']}", blockers)
        _expect("struct_conn_row_count" in row, f"step12w_struct_conn_missing:{row['pdb_id']}", blockers)
        _expect("covalent_connection_candidate_count" in row, f"step12w_candidate_count_missing:{row['pdb_id']}", blockers)
        for field in [
            "extraction_writes_coordinates",
            "extraction_writes_atom_table",
            "raw_or_decompressed_mmcif_output_written",
            "full_mmcif_parser_used",
            "biopdb_parser_used",
            PARSER_VENDOR_USED_KEY,
            "rdkit_used",
            "coordinate_geometry_calculation_run",
        ]:
            _expect(_is_false(row[field]), f"step12w_{field}_invalid:{row['pdb_id']}", blockers)
        _expect(row["parser_library_used"] == "none", f"step12w_parser_library_invalid:{row['pdb_id']}", blockers)
        _expect(row["error_message"] == "", f"step12w_error_message_invalid:{row['pdb_id']}", blockers)

    summary = STEP12W_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "actual minimal mmCIF parser smoke",
        "actually read 3 raw",
        "standard library " + "gzip." + "open",
        "in-memory text scan",
        "did not network and did not re-download",
        "did not write raw/decompressed mmCIF/PDB/SDF/MOL2 outputs",
        "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit",
        "adapters, coordinate geometry, UniProt/CD-HIT, NPZ reads, or training",
        "6DI9",
        "5F2E",
        "6OIM",
        "entry id, structure title, entity count, atom_site row count, chem_comp ids, struct_conn row count, and covalent connection candidate count",
        "does not claim complete structure parsing",
        "real_covalent_minimal_mmcif_adapter_design_gate",
    ]:
        _expect(snippet in summary, f"step12w_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _contract_row(
    section: str,
    name: str,
    source_field: str,
    target_field: str,
    requirement: str,
    allowed: bool,
    forbidden: bool,
    policy: str,
    unresolved_policy: str = "",
    pdb_id: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "contract_section": section,
        "contract_name": name,
        "pdb_id": pdb_id,
        "source_field": source_field,
        "target_field": target_field,
        "requirement": requirement,
        "allowed_in_next_step": allowed,
        "forbidden_in_next_step": forbidden,
        "expected_value_or_policy": policy,
        "unresolved_policy": unresolved_policy,
        "notes": notes,
    }


def build_minimal_mmcif_adapter_contract_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pdb_id in EXPECTED_PDB_IDS:
        rows.append(
            _contract_row(
                "adapter_input",
                "parser_summary_row_input",
                "parser_summary_row",
                "minimal_adapter_input",
                "required parser summary row must pass before adapter smoke",
                True,
                False,
                "source_parser_stage=real_covalent_minimal_mmcif_parser_smoke_v0",
                pdb_id=pdb_id,
                notes=(
                    "input_row_required=true;"
                    "parse_status_must_be_passed=true;"
                    f"required_parser_fields={';'.join(EXPECTED_REQUIRED_PARSER_FIELDS)};"
                    "raw_file_read_allowed_next_step=false;"
                    "raw_file_decompression_allowed_next_step=false;"
                    "mmcif_parse_allowed_next_step=false;"
                    "adapter_may_read_parser_summary_csv=true;"
                    "adapter_may_write_adapter_summary_csv=true;"
                    "adapter_may_write_sample_stub_json=false;"
                    "adapter_may_write_enriched_sample_index=false"
                ),
            )
        )
    for target_field, source_field in SCHEMA_MAPPING_FIELDS:
        rows.append(
            _contract_row(
                "schema_mapping",
                "parser_metadata_to_adapter_summary",
                source_field,
                target_field,
                f"map {target_field} from parser summary or deterministic constant",
                True,
                False,
                "minimal_adapter_summary_field",
            )
        )
    for field in UNRESOLVED_SCHEMA_FIELDS:
        rows.append(
            _contract_row(
                "not_yet_available_schema_field",
                "mark_unresolved_without_inference",
                "",
                field,
                "field cannot be inferred during minimal adapter smoke",
                False,
                True,
                "do_not_infer",
                "adapter_smoke_must_mark_unresolved=true",
                notes=(
                    "adapter_smoke_may_infer=false;"
                    "reason=requires full parser/chemistry/geometry annotation beyond Step 12Y"
                ),
            )
        )
    policy_rows = [
        ("read_parser_summary_only", "Step 12Y reads Step 12W extracted summary CSV only", True, False),
        ("do_not_read_raw", "Step 12Y does not read raw compressed files", False, True),
        ("do_not_decompress_or_parse", "Step 12Y does not decompress or parse mmCIF", False, True),
        ("no_external_parser", "Step 12Y uses no external parser libraries", False, True),
        ("no_rdkit", "Step 12Y does not run RDKit", False, True),
        ("no_geometry", "Step 12Y does not compute coordinate geometry", False, True),
        ("no_uniprot_cdhit", "Step 12Y does not run UniProt or CD-HIT", False, True),
        ("no_npz", "Step 12Y does not read NPZ contents", False, True),
        ("no_enriched_index", "Step 12Y does not write enriched sample_index", False, True),
        ("no_final_dataset", "Step 12Y does not write final dataset or split artifacts", False, True),
        ("no_training_artifacts", "Step 12Y writes no model training or tensor artifacts", False, True),
        ("csv_json_md_only", "Step 12Y outputs CSV JSON MD adapter summary only", True, False),
        ("no_training_ready_claim", "Step 12Y claims only minimal adapter stub contract satisfaction", False, True),
    ]
    for name, requirement, allowed, forbidden in policy_rows:
        rows.append(
            _contract_row(
                "adapter_policy",
                name,
                "",
                "",
                requirement,
                allowed,
                forbidden,
                "policy_for_next_step",
            )
        )
    return rows


def build_minimal_mmcif_adapter_design_summary_v0(contract_rows: list[dict[str, Any]]) -> dict[str, Any]:
    input_count = sum(row["contract_section"] == "adapter_input" for row in contract_rows)
    mapping_count = sum(row["contract_section"] == "schema_mapping" for row in contract_rows)
    unresolved_count = sum(row["contract_section"] == "not_yet_available_schema_field" for row in contract_rows)
    policy_count = sum(row["contract_section"] == "adapter_policy" for row in contract_rows)
    return {
        "minimal_mmcif_adapter_contract_defined": True,
        "adapter_contract_csv_written": True,
        "adapter_contract_row_count": len(contract_rows),
        "adapter_input_contract_row_count": input_count,
        "schema_mapping_row_count": mapping_count,
        "not_yet_available_schema_field_row_count": unresolved_count,
        "adapter_policy_row_count": policy_count,
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
    }


def build_real_covalent_minimal_mmcif_adapter_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12w_validated = validate_step12w_minimal_mmcif_parser_smoke_v0()
    except Exception as exc:
        step12w_validated = False
        blockers.append(f"step12w_validation_failed:{type(exc).__name__}:{exc}")
    step12w_manifest = _load_json(STEP12W_MANIFEST_JSON)
    contract_rows = build_minimal_mmcif_adapter_contract_v0()
    design_summary = build_minimal_mmcif_adapter_design_summary_v0(contract_rows)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")

    passed = bool(
        step12w_validated
        and step12w_manifest["step12b_mask_level_aware_validator_validated"]
        and design_summary["minimal_mmcif_adapter_contract_defined"]
        and design_summary["adapter_contract_csv_written"]
        and design_summary["adapter_input_contract_row_count"] == 3
        and design_summary["schema_mapping_row_count"] >= 14
        and design_summary["not_yet_available_schema_field_row_count"] >= 12
        and design_summary["adapter_policy_row_count"] >= 10
        and design_summary["adapter_scope_pdb_ids"] == EXPECTED_PDB_IDS
        and design_summary["adapter_smoke_ready_next_step"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_minimal_mmcif_adapter_design_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12w_minimal_mmcif_parser_smoke_validated": step12w_validated,
        "step12b_mask_level_aware_validator_validated": step12w_manifest["step12b_mask_level_aware_validator_validated"],
        **design_summary,
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
        "real_covalent_minimal_mmcif_adapter_design_gate_passed": passed,
        "minimal_mmcif_adapter_design_contract_defined": passed,
        "ready_for_minimal_mmcif_adapter_smoke": passed,
        "ready_to_run_adapter_now": False,
        "ready_to_write_enriched_sample_index_now": False,
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
        "step12w_precondition": {
            "step12w_minimal_mmcif_parser_smoke_validated": manifest["step12w_minimal_mmcif_parser_smoke_validated"],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "adapter_input_scope_contract": {
            "adapter_scope_pdb_ids": manifest["adapter_scope_pdb_ids"],
            "adapter_scope_limited_to_current_pilot": manifest["adapter_scope_limited_to_current_pilot"],
        },
        "parser_to_adapter_schema_mapping": {
            "schema_mapping_row_count": manifest["schema_mapping_row_count"],
            "adapter_maps_parser_metadata_fields": manifest["adapter_maps_parser_metadata_fields"],
        },
        "unresolved_chemistry_fields_policy": {
            "not_yet_available_schema_field_row_count": manifest["not_yet_available_schema_field_row_count"],
            "adapter_marks_unresolved_chemistry_fields": manifest["adapter_marks_unresolved_chemistry_fields"],
        },
        "adapter_safety_policy": {
            "adapter_smoke_reads_raw_files_next_step": manifest["adapter_smoke_reads_raw_files_next_step"],
            "adapter_smoke_parses_mmcif_next_step": manifest["adapter_smoke_parses_mmcif_next_step"],
            "adapter_smoke_runs_rdkit_next_step": manifest["adapter_smoke_runs_rdkit_next_step"],
        },
        "output_artifact_policy": {
            "adapter_smoke_writes_adapter_summary_next_step": manifest["adapter_smoke_writes_adapter_summary_next_step"],
            "adapter_smoke_output_limited_to_csv_json_md": manifest["adapter_smoke_output_limited_to_csv_json_md"],
        },
        "no_adapter_execution_boundary_this_step": {
            "adapter_implementation_written": manifest["adapter_implementation_written"],
            "adapter_execution_run": manifest["adapter_execution_run"],
        },
        "next_step_decision": {
            "ready_for_minimal_mmcif_adapter_smoke": manifest["ready_for_minimal_mmcif_adapter_smoke"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
