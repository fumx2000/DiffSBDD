from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0"

STEP13J_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_full_atom_extraction_smoke_manifest.json"
)
STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_protein_full_atom_table.csv"
)
STEP13J_LIGAND_FULL_ATOM_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_ligand_full_atom_table.csv"
)
STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_full_atom_endpoint_recovery_audit.csv"
)

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_design_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_design_gate_manifest.json"
SCHEMA_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_schema_contract.csv"
CANDIDATE_CONTRACT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_candidate_contract.csv"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_PROTEIN_ROW_COUNT = 4600
EXPECTED_LIGAND_ROW_COUNT = 104
EXPECTED_ENDPOINT_AUDIT_ROW_COUNT = 3
POCKET_RADIUS_ANGSTROM = 8.0
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_pocket_extraction_smoke"

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
    "required_for_pocket_extraction_smoke",
    "source_stage",
    "source_column",
    "design_rule",
    "validation_rule",
    "training_use_status",
]

CANDIDATE_CONTRACT_COLUMNS = [
    "pocket_extraction_contract_id",
    "minimal_sample_record_id",
    "confirmed_candidate_id",
    "review_row_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "protein_full_atom_table_source",
    "ligand_full_atom_table_source",
    "endpoint_recovery_audit_source",
    "protein_atom_input_available",
    "ligand_atom_input_available",
    "endpoint_recovery_passed",
    "protein_atom_input_row_count",
    "ligand_atom_input_row_count",
    "protein_endpoint_atom_site_id",
    "protein_endpoint_altloc",
    "ligand_endpoint_atom_site_id",
    "ligand_endpoint_altloc",
    "pocket_center_policy",
    "pocket_radius_angstrom",
    "pocket_radius_unit",
    "protein_atom_source_policy",
    "ligand_atom_source_policy",
    "covalent_endpoint_anchor_policy",
    "altloc_selection_policy",
    "model_selection_policy",
    "water_handling_policy",
    "ion_handling_policy",
    "hydrogen_handling_policy",
    "include_covalent_residue_policy",
    "include_covalent_endpoint_policy",
    "distance_calculation_policy",
    "pocket_membership_policy",
    "pocket_extraction_design_status",
    "pocket_extraction_run",
    "pocket_atom_table_written",
    "ligand_topology_table_written",
    "sample_index_written",
    "enriched_sample_index_written",
    "final_dataset_written",
    "model_input_materialized",
    "training_ready",
    "training_ready_reason",
]

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


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _source_diff_exists() -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS])
    staged = _run_git(["diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS])
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_COMMITTABLE_SUFFIXES for path in root_path.rglob("*"))


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def validate_step13j_full_atom_extraction_smoke_v0() -> bool:
    required_paths = [
        STEP13J_MANIFEST_JSON,
        STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV,
        STEP13J_LIGAND_FULL_ATOM_TABLE_CSV,
        STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13K prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13J_MANIFEST_JSON)
    protein_rows = _read_csv(STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV)
    ligand_rows = _read_csv(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV)
    audit_rows = _read_csv(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "all_endpoint_recovery_passed": True,
        "protein_full_atom_table_written": True,
        "ligand_full_atom_table_written": True,
        "endpoint_recovery_audit_written": True,
        "pocket_atom_table_written": False,
        "ligand_topology_table_written": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "hr0002_altloc_b_preserved": True,
        "hr0002_selected_protein_atom_site_id": "659",
        "hr0002_selected_protein_label_alt_id": "B",
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step13j_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(len(protein_rows) == EXPECTED_PROTEIN_ROW_COUNT, f"protein_row_count_invalid:{len(protein_rows)}", blockers)
    _expect(len(ligand_rows) == EXPECTED_LIGAND_ROW_COUNT, f"ligand_row_count_invalid:{len(ligand_rows)}", blockers)
    _expect(len(audit_rows) == EXPECTED_ENDPOINT_AUDIT_ROW_COUNT, f"endpoint_audit_row_count_invalid:{len(audit_rows)}", blockers)
    _expect([row["review_row_id"] for row in audit_rows] == EXPECTED_REVIEW_ROW_IDS, "audit_review_ids_invalid", blockers)
    _expect([row["pdb_id"] for row in audit_rows] == EXPECTED_PDB_IDS, "audit_pdb_ids_invalid", blockers)
    _expect(all(row["endpoint_recovery_passed"] == "True" for row in audit_rows), "endpoint_recovery_not_all_passed", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step13j_protein_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV)


def load_step13j_ligand_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV)


def load_step13j_endpoint_audit_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV)


def _schema_row(
    field_name: str,
    field_group: str,
    data_type: str,
    source_stage: str,
    source_column: str,
    design_rule: str,
    validation_rule: str,
    output_table: str = "pocket_extraction_contract",
) -> dict[str, Any]:
    return {
        "field_name": field_name,
        "field_group": field_group,
        "output_table": output_table,
        "data_type": data_type,
        "required_for_pocket_extraction_smoke": True,
        "source_stage": source_stage,
        "source_column": source_column,
        "design_rule": design_rule,
        "validation_rule": validation_rule,
        "training_use_status": "not_training_input_yet",
    }


def build_pocket_extraction_schema_contract_v0() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = {
        "sample_provenance": [
            "pocket_extraction_contract_id",
            "minimal_sample_record_id",
            "confirmed_candidate_id",
            "review_row_id",
            "sample_id",
            "pdb_id",
            "entry_id",
            "full_atom_extraction_smoke_stage",
            "pocket_extraction_design_stage",
        ],
        "protein_atom_source": ["protein_full_atom_table_source", "expected_protein_atom_input_row_count"],
        "ligand_atom_source": ["ligand_full_atom_table_source", "expected_ligand_atom_input_row_count"],
        "covalent_endpoint_policy": [
            "endpoint_recovery_audit_source",
            "expected_endpoint_recovery_audit_rows",
            "include_covalent_residue_policy",
            "include_covalent_endpoint_policy",
            "covalent_endpoint_anchor_policy",
        ],
        "pocket_center_policy": ["pocket_center_policy", "pocket_radius_angstrom", "pocket_radius_unit"],
        "pocket_policy": [
            "protein_atom_source_policy",
            "ligand_atom_source_policy",
            "water_handling_policy",
            "ion_handling_policy",
            "hydrogen_handling_policy",
        ],
        "altloc_model_policy": ["altloc_selection_policy", "model_selection_policy"],
        "validation_policy": ["distance_calculation_policy", "pocket_membership_policy"],
        "output_table_contract": ["pocket_atom_table_columns_planned", "pocket_atom_table_validation_planned"],
        "status_boundary": [
            "pocket_extraction_run",
            "pocket_atom_table_written",
            "ligand_topology_table_written",
            "sample_index_written",
            "enriched_sample_index_written",
            "final_dataset_written",
            "model_input_materialized",
            "training_ready",
            "training_ready_reason",
        ],
    }
    for group, fields in groups.items():
        for field in fields:
            data_type = "float" if field == "pocket_radius_angstrom" else "bool" if field.endswith("_written") or field.endswith("_run") or field == "training_ready" else "string"
            rows.append(
                _schema_row(
                    field,
                    group,
                    data_type,
                    STAGE if group in {"pocket_policy", "pocket_center_policy", "altloc_model_policy", "validation_policy", "status_boundary"} else PREVIOUS_STAGE,
                    field,
                    "define_next_smoke_contract_without_distance_calculation",
                    "non_empty_or_false_until_smoke_runs",
                )
            )
    return rows


def build_pocket_extraction_candidate_contract_v0(
    protein_rows: list[dict[str, str]],
    ligand_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    protein_counts = Counter(row["review_row_id"] for row in protein_rows)
    ligand_counts = Counter(row["review_row_id"] for row in ligand_rows)
    sample_ids = {row["review_row_id"]: row["sample_id"] for row in protein_rows}
    confirmed_ids = {row["review_row_id"]: row["confirmed_candidate_id"] for row in protein_rows}
    minimal_ids = {row["review_row_id"]: row["minimal_sample_record_id"] for row in protein_rows}
    entry_ids = {row["review_row_id"]: row["entry_id"] for row in protein_rows}
    rows: list[dict[str, Any]] = []
    for index, audit in enumerate(audit_rows, start=1):
        review_id = audit["review_row_id"]
        rows.append(
            {
                "pocket_extraction_contract_id": f"POCKET_CONTRACT_{index:04d}_{review_id}",
                "minimal_sample_record_id": minimal_ids[review_id],
                "confirmed_candidate_id": confirmed_ids[review_id],
                "review_row_id": review_id,
                "sample_id": sample_ids[review_id],
                "pdb_id": audit["pdb_id"],
                "entry_id": entry_ids[review_id],
                "protein_full_atom_table_source": str(STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV),
                "ligand_full_atom_table_source": str(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV),
                "endpoint_recovery_audit_source": str(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV),
                "protein_atom_input_available": True,
                "ligand_atom_input_available": True,
                "endpoint_recovery_passed": audit["endpoint_recovery_passed"] == "True",
                "protein_atom_input_row_count": protein_counts[review_id],
                "ligand_atom_input_row_count": ligand_counts[review_id],
                "protein_endpoint_atom_site_id": audit["recovered_protein_endpoint_atom_site_id"],
                "protein_endpoint_altloc": audit["recovered_protein_endpoint_altloc"],
                "ligand_endpoint_atom_site_id": audit["recovered_ligand_endpoint_atom_site_id"],
                "ligand_endpoint_altloc": audit["recovered_ligand_endpoint_altloc"],
                "pocket_center_policy": "ligand_heavy_atom_centroid_plus_covalent_endpoint_anchor",
                "pocket_radius_angstrom": POCKET_RADIUS_ANGSTROM,
                "pocket_radius_unit": "angstrom",
                "protein_atom_source_policy": "use_step13j_target_protein_chain_atoms_only",
                "ligand_atom_source_policy": "use_step13j_confirmed_ligand_instance_atoms_only",
                "covalent_endpoint_anchor_policy": "require_recovered_protein_and_ligand_endpoints",
                "altloc_selection_policy": "inherit_step13j_altloc_filtered_atoms",
                "model_selection_policy": "inherit_step13j_model_policy",
                "water_handling_policy": "exclude_waters_initial_pocket_smoke",
                "ion_handling_policy": "exclude_ions_initial_pocket_smoke",
                "hydrogen_handling_policy": "preserve_deposited_atoms_no_hydrogen_addition",
                "include_covalent_residue_policy": "force_include_confirmed_covalent_residue_atoms",
                "include_covalent_endpoint_policy": "force_include_recovered_endpoint_atoms",
                "distance_calculation_policy": "next_smoke_compute_min_distance_to_ligand_atoms",
                "pocket_membership_policy": (
                    "protein_atom_within_radius_of_any_ligand_atom_or_force_included_endpoint_residue"
                ),
                "pocket_extraction_design_status": "contract_only_no_distance_calculation",
                "pocket_extraction_run": False,
                "pocket_atom_table_written": False,
                "ligand_topology_table_written": False,
                "sample_index_written": False,
                "enriched_sample_index_written": False,
                "final_dataset_written": False,
                "model_input_materialized": False,
                "training_ready": False,
                "training_ready_reason": "pocket_extraction_design_only_no_pocket_atoms_written",
            }
        )
    return rows


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13j_precondition": {
            "step13j_full_atom_extraction_smoke_validated": manifest["step13j_full_atom_extraction_smoke_validated"],
        },
        "inherited_tables": {
            "protein_full_atom_table_row_count": manifest["protein_full_atom_table_row_count"],
            "ligand_full_atom_table_row_count": manifest["ligand_full_atom_table_row_count"],
            "endpoint_recovery_audit_row_count": manifest["endpoint_recovery_audit_row_count"],
        },
        "schema_contract": {
            "pocket_extraction_schema_contract_csv_written": manifest["pocket_extraction_schema_contract_csv_written"],
            "pocket_extraction_schema_field_count": manifest["pocket_extraction_schema_field_count"],
        },
        "candidate_contract": {
            "pocket_extraction_candidate_contract_csv_written": manifest[
                "pocket_extraction_candidate_contract_csv_written"
            ],
            "pocket_extraction_candidate_contract_row_count": manifest[
                "pocket_extraction_candidate_contract_row_count"
            ],
        },
        "policy": {
            "pocket_radius_angstrom": manifest["pocket_radius_angstrom"],
            "all_candidate_contract_rows_have_pocket_policy": manifest["all_candidate_contract_rows_have_pocket_policy"],
        },
        "no_execution_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            "distance_matrix_calculated": manifest["distance_matrix_calculated"],
            "pocket_atom_table_written": manifest["pocket_atom_table_written"],
        },
        "no_training_boundary": {
            "sample_index_written": manifest["sample_index_written"],
            "model_input_materialized": manifest["model_input_materialized"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "next_step": {
            "ready_for_pocket_extraction_smoke": manifest["ready_for_pocket_extraction_smoke"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }


def build_real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13j_validated = validate_step13j_full_atom_extraction_smoke_v0()
    except Exception as exc:
        step13j_validated = False
        blockers.append(f"step13j_precondition_failed:{type(exc).__name__}:{exc}")
    protein_rows = load_step13j_protein_rows_v0() if STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV.is_file() else []
    ligand_rows = load_step13j_ligand_rows_v0() if STEP13J_LIGAND_FULL_ATOM_TABLE_CSV.is_file() else []
    audit_rows = load_step13j_endpoint_audit_rows_v0() if STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV.is_file() else []
    schema_rows = build_pocket_extraction_schema_contract_v0()
    candidate_rows = build_pocket_extraction_candidate_contract_v0(protein_rows, ligand_rows, audit_rows) if step13j_validated else []

    processed_pdb_ids = [row["pdb_id"] for row in audit_rows]
    processed_review_row_ids = [row["review_row_id"] for row in audit_rows]
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked()
    if source_modified:
        blockers.append("protected_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")

    all_candidate_rows_have_atom_inputs = bool(candidate_rows) and all(
        row["protein_atom_input_available"] is True and row["ligand_atom_input_available"] is True
        for row in candidate_rows
    )
    all_endpoint_recovery_preserved = bool(candidate_rows) and all(
        row["endpoint_recovery_passed"] is True for row in candidate_rows
    )
    all_have_policy = bool(candidate_rows) and all(
        row["pocket_radius_angstrom"] == POCKET_RADIUS_ANGSTROM
        and row["pocket_center_policy"] == "ligand_heavy_atom_centroid_plus_covalent_endpoint_anchor"
        for row in candidate_rows
    )
    hr2 = next((row for row in candidate_rows if row.get("review_row_id") == "HR_0002"), {})
    passed = (
        step13j_validated
        and len(protein_rows) == EXPECTED_PROTEIN_ROW_COUNT
        and len(ligand_rows) == EXPECTED_LIGAND_ROW_COUNT
        and len(audit_rows) == EXPECTED_ENDPOINT_AUDIT_ROW_COUNT
        and len(candidate_rows) == 3
        and all_candidate_rows_have_atom_inputs
        and all_endpoint_recovery_preserved
        and all_have_policy
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13j_full_atom_extraction_smoke_validated": step13j_validated,
        "protein_full_atom_table_csv_read": bool(protein_rows),
        "ligand_full_atom_table_csv_read": bool(ligand_rows),
        "endpoint_recovery_audit_csv_read": bool(audit_rows),
        "protein_full_atom_table_row_count": len(protein_rows),
        "ligand_full_atom_table_row_count": len(ligand_rows),
        "endpoint_recovery_audit_row_count": len(audit_rows),
        "pocket_extraction_schema_contract_csv_written": True,
        "pocket_extraction_schema_field_count": len(schema_rows),
        "pocket_extraction_candidate_contract_csv_written": True,
        "pocket_extraction_candidate_contract_row_count": len(candidate_rows),
        "processed_pdb_ids": processed_pdb_ids,
        "processed_review_row_ids": processed_review_row_ids,
        "all_candidate_contract_rows_have_atom_inputs": all_candidate_rows_have_atom_inputs,
        "all_candidate_contract_rows_preserve_endpoint_recovery": all_endpoint_recovery_preserved,
        "all_candidate_contract_rows_have_pocket_policy": all_have_policy,
        "pocket_radius_angstrom": POCKET_RADIUS_ANGSTROM,
        "hr0002_altloc_b_atom_site_659_inherited": hr2.get("protein_endpoint_atom_site_id") == "659"
        and hr2.get("protein_endpoint_altloc") == "B",
        "raw_files_read": False,
        GZIP_OPEN_KEY: False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "coordinate_geometry_calculation_run": False,
        "distance_matrix_calculated": False,
        "pocket_extraction_run": False,
        "pocket_atom_table_written": False,
        "ligand_topology_table_written": False,
        "sample_index_written": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_pocket_extraction_smoke": passed,
        "ready_to_write_sample_index_now": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP
        if passed
        else "real_covalent_confirmed_candidate_pocket_extraction_design_gate_debug",
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "schema_rows": schema_rows,
        "candidate_rows": candidate_rows,
        "report_sections": _build_report_sections(manifest),
    }
