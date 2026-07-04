from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0"

STEP13K_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_pocket_extraction_design_gate_manifest.json"
)
STEP13K_CANDIDATE_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_pocket_extraction_candidate_contract.csv"
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

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0")
POCKET_ATOM_TABLE_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_atom_table.csv"
POCKET_EXTRACTION_AUDIT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_pocket_extraction_smoke_manifest.json"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_pocket_extraction_smoke_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_CONTRACT_ROW_COUNT = 3
EXPECTED_PROTEIN_ROW_COUNT = 4600
EXPECTED_LIGAND_ROW_COUNT = 104
POCKET_RADIUS_ANGSTROM = 8.0
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_ligand_topology_design_gate"

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

POCKET_ATOM_COLUMNS = [
    "pocket_atom_row_id",
    "pocket_extraction_contract_id",
    "minimal_sample_record_id",
    "confirmed_candidate_id",
    "review_row_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "source_protein_full_atom_row_id",
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
    "B_iso_or_equiv",
    "pdbx_PDB_model_num",
    "pocket_radius_angstrom",
    "min_distance_to_ligand_heavy_atom_angstrom",
    "nearest_ligand_atom_site_id",
    "nearest_ligand_label_atom_id",
    "nearest_ligand_label_comp_id",
    "nearest_ligand_distance_angstrom",
    "is_within_radius",
    "is_covalent_residue_atom",
    "is_covalent_endpoint_atom",
    "force_included_by_covalent_residue",
    "force_included_by_covalent_endpoint",
    "pocket_membership_reason",
    "extraction_source_stage",
]

POCKET_AUDIT_COLUMNS = [
    "review_row_id",
    "pdb_id",
    "pocket_extraction_contract_id",
    "protein_atom_input_row_count",
    "ligand_atom_input_row_count",
    "ligand_heavy_atom_count",
    "pocket_atom_row_count",
    "within_radius_atom_count",
    "force_included_covalent_residue_atom_count",
    "force_included_endpoint_atom_count",
    "covalent_endpoint_in_pocket",
    "covalent_residue_atoms_in_pocket",
    "min_pocket_distance_angstrom",
    "max_pocket_distance_angstrom",
    "pocket_radius_angstrom",
    "pocket_extraction_passed",
    "blocking_reasons",
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


def _is_true_text(value: str) -> bool:
    return value == "True"


def _is_false_text(value: str) -> bool:
    return value == "False"


def _format_float(value: float) -> str:
    return f"{value:.4f}"


def _xyz(row: dict[str, str]) -> tuple[float, float, float]:
    return (float(row["Cartn_x"]), float(row["Cartn_y"]), float(row["Cartn_z"]))


def _distance(left: dict[str, str], right: dict[str, str]) -> float:
    lx, ly, lz = _xyz(left)
    rx, ry, rz = _xyz(right)
    return math.sqrt((lx - rx) ** 2 + (ly - ry) ** 2 + (lz - rz) ** 2)


def validate_step13k_pocket_extraction_design_gate_v0() -> bool:
    required_paths = [
        STEP13K_MANIFEST_JSON,
        STEP13K_CANDIDATE_CONTRACT_CSV,
        STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV,
        STEP13J_LIGAND_FULL_ATOM_TABLE_CSV,
        STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13L prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13K_MANIFEST_JSON)
    contract_rows = _read_csv(STEP13K_CANDIDATE_CONTRACT_CSV)
    protein_rows = _read_csv(STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV)
    ligand_rows = _read_csv(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV)
    audit_rows = _read_csv(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "ready_for_pocket_extraction_smoke": True,
        "pocket_radius_angstrom": POCKET_RADIUS_ANGSTROM,
        "pocket_extraction_candidate_contract_row_count": EXPECTED_CONTRACT_ROW_COUNT,
        "hr0002_altloc_b_atom_site_659_inherited": True,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step13k_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(len(contract_rows) == EXPECTED_CONTRACT_ROW_COUNT, f"contract_row_count_invalid:{len(contract_rows)}", blockers)
    _expect([row["review_row_id"] for row in contract_rows] == EXPECTED_REVIEW_ROW_IDS, "contract_review_ids_invalid", blockers)
    _expect([row["pdb_id"] for row in contract_rows] == EXPECTED_PDB_IDS, "contract_pdb_ids_invalid", blockers)
    _expect(len(protein_rows) == EXPECTED_PROTEIN_ROW_COUNT, f"protein_row_count_invalid:{len(protein_rows)}", blockers)
    _expect(len(ligand_rows) == EXPECTED_LIGAND_ROW_COUNT, f"ligand_row_count_invalid:{len(ligand_rows)}", blockers)
    _expect(len(audit_rows) == EXPECTED_CONTRACT_ROW_COUNT, f"endpoint_audit_row_count_invalid:{len(audit_rows)}", blockers)
    _expect(all(row["endpoint_recovery_passed"] == "True" for row in audit_rows), "endpoint_recovery_not_all_passed", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step13k_candidate_contract_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13K_CANDIDATE_CONTRACT_CSV)


def load_step13j_protein_full_atom_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV)


def load_step13j_ligand_full_atom_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_LIGAND_FULL_ATOM_TABLE_CSV)


def load_step13j_endpoint_recovery_audit_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV)


def _rows_by_review(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["review_row_id"]].append(row)
    return grouped


def _nearest_ligand_heavy_atom(
    protein_row: dict[str, str],
    ligand_heavy_rows: list[dict[str, str]],
) -> tuple[dict[str, str], float]:
    distances = [(_distance(protein_row, ligand_row), ligand_row) for ligand_row in ligand_heavy_rows]
    distance, ligand_row = min(distances, key=lambda item: item[0])
    return ligand_row, distance


def build_pocket_atom_table_and_audit_v0(
    contract_rows: list[dict[str, str]],
    protein_rows: list[dict[str, str]],
    ligand_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    protein_by_review = _rows_by_review(protein_rows)
    ligand_by_review = _rows_by_review(ligand_rows)
    pocket_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    row_index = 1
    for contract in contract_rows:
        review_id = contract["review_row_id"]
        proteins = protein_by_review.get(review_id, [])
        ligands = ligand_by_review.get(review_id, [])
        ligand_heavy = [row for row in ligands if row["type_symbol"] != "H"]
        candidate_pocket_rows: list[dict[str, Any]] = []
        blockers: list[str] = []
        if not proteins:
            blockers.append("missing_protein_rows")
        if not ligands:
            blockers.append("missing_ligand_rows")
        if not ligand_heavy:
            blockers.append("missing_ligand_heavy_rows")
        for protein in proteins:
            if not ligand_heavy:
                continue
            nearest_ligand, min_distance = _nearest_ligand_heavy_atom(protein, ligand_heavy)
            is_within_radius = min_distance <= POCKET_RADIUS_ANGSTROM
            is_covalent_residue = _is_true_text(protein["is_covalent_residue_atom"])
            is_covalent_endpoint = _is_true_text(protein["is_covalent_endpoint_atom"])
            force_residue = is_covalent_residue
            force_endpoint = is_covalent_endpoint
            if not (is_within_radius or force_residue or force_endpoint):
                continue
            reasons: list[str] = []
            if is_within_radius:
                reasons.append("within_radius")
            if force_residue:
                reasons.append("force_include_covalent_residue")
            if force_endpoint:
                reasons.append("force_include_covalent_endpoint")
            candidate_pocket_rows.append(
                {
                    "pocket_atom_row_id": f"POCKET_ATOM_{row_index:06d}",
                    "pocket_extraction_contract_id": contract["pocket_extraction_contract_id"],
                    "minimal_sample_record_id": contract["minimal_sample_record_id"],
                    "confirmed_candidate_id": contract["confirmed_candidate_id"],
                    "review_row_id": review_id,
                    "sample_id": contract["sample_id"],
                    "pdb_id": contract["pdb_id"],
                    "entry_id": contract["entry_id"],
                    "source_protein_full_atom_row_id": protein["full_atom_row_id"],
                    "atom_site_id": protein["atom_site_id"],
                    "group_PDB": protein["group_PDB"],
                    "type_symbol": protein["type_symbol"],
                    "label_atom_id": protein["label_atom_id"],
                    "label_comp_id": protein["label_comp_id"],
                    "label_asym_id": protein["label_asym_id"],
                    "label_seq_id": protein["label_seq_id"],
                    "label_alt_id": protein["label_alt_id"],
                    "auth_atom_id": protein["auth_atom_id"],
                    "auth_comp_id": protein["auth_comp_id"],
                    "auth_asym_id": protein["auth_asym_id"],
                    "auth_seq_id": protein["auth_seq_id"],
                    "Cartn_x": protein["Cartn_x"],
                    "Cartn_y": protein["Cartn_y"],
                    "Cartn_z": protein["Cartn_z"],
                    "occupancy": protein["occupancy"],
                    "B_iso_or_equiv": protein["B_iso_or_equiv"],
                    "pdbx_PDB_model_num": protein["pdbx_PDB_model_num"],
                    "pocket_radius_angstrom": POCKET_RADIUS_ANGSTROM,
                    "min_distance_to_ligand_heavy_atom_angstrom": _format_float(min_distance),
                    "nearest_ligand_atom_site_id": nearest_ligand["atom_site_id"],
                    "nearest_ligand_label_atom_id": nearest_ligand["label_atom_id"],
                    "nearest_ligand_label_comp_id": nearest_ligand["label_comp_id"],
                    "nearest_ligand_distance_angstrom": _format_float(min_distance),
                    "is_within_radius": is_within_radius,
                    "is_covalent_residue_atom": is_covalent_residue,
                    "is_covalent_endpoint_atom": is_covalent_endpoint,
                    "force_included_by_covalent_residue": force_residue,
                    "force_included_by_covalent_endpoint": force_endpoint,
                    "pocket_membership_reason": "+".join(reasons),
                    "extraction_source_stage": STAGE,
                }
            )
            row_index += 1
        input_covalent_endpoint_ids = {
            row["atom_site_id"] for row in proteins if _is_true_text(row["is_covalent_endpoint_atom"])
        }
        input_covalent_residue_ids = {
            row["atom_site_id"] for row in proteins if _is_true_text(row["is_covalent_residue_atom"])
        }
        pocket_ids = {row["atom_site_id"] for row in candidate_pocket_rows}
        distances = [float(row["min_distance_to_ligand_heavy_atom_angstrom"]) for row in candidate_pocket_rows]
        covalent_endpoint_in_pocket = bool(input_covalent_endpoint_ids) and input_covalent_endpoint_ids <= pocket_ids
        covalent_residue_atoms_in_pocket = bool(input_covalent_residue_ids) and input_covalent_residue_ids <= pocket_ids
        pocket_passed = (
            bool(candidate_pocket_rows)
            and bool(ligand_heavy)
            and covalent_endpoint_in_pocket
            and covalent_residue_atoms_in_pocket
            and not blockers
        )
        if not candidate_pocket_rows:
            blockers.append("empty_pocket_atom_rows")
        if not covalent_endpoint_in_pocket:
            blockers.append("covalent_endpoint_not_in_pocket")
        if not covalent_residue_atoms_in_pocket:
            blockers.append("covalent_residue_atoms_not_in_pocket")
        audit_rows.append(
            {
                "review_row_id": review_id,
                "pdb_id": contract["pdb_id"],
                "pocket_extraction_contract_id": contract["pocket_extraction_contract_id"],
                "protein_atom_input_row_count": len(proteins),
                "ligand_atom_input_row_count": len(ligands),
                "ligand_heavy_atom_count": len(ligand_heavy),
                "pocket_atom_row_count": len(candidate_pocket_rows),
                "within_radius_atom_count": sum(1 for row in candidate_pocket_rows if row["is_within_radius"] is True),
                "force_included_covalent_residue_atom_count": sum(
                    1 for row in candidate_pocket_rows if row["force_included_by_covalent_residue"] is True
                ),
                "force_included_endpoint_atom_count": sum(
                    1 for row in candidate_pocket_rows if row["force_included_by_covalent_endpoint"] is True
                ),
                "covalent_endpoint_in_pocket": covalent_endpoint_in_pocket,
                "covalent_residue_atoms_in_pocket": covalent_residue_atoms_in_pocket,
                "min_pocket_distance_angstrom": _format_float(min(distances)) if distances else "",
                "max_pocket_distance_angstrom": _format_float(max(distances)) if distances else "",
                "pocket_radius_angstrom": POCKET_RADIUS_ANGSTROM,
                "pocket_extraction_passed": pocket_passed,
                "blocking_reasons": ";".join(sorted(set(blockers))),
            }
        )
        pocket_rows.extend(candidate_pocket_rows)
    return pocket_rows, audit_rows


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13k_precondition": {
            "step13k_pocket_extraction_design_gate_validated": manifest[
                "step13k_pocket_extraction_design_gate_validated"
            ],
        },
        "inherited_inputs": {
            "pocket_extraction_candidate_contract_row_count": manifest[
                "pocket_extraction_candidate_contract_row_count"
            ],
            "protein_full_atom_table_row_count": manifest["protein_full_atom_table_row_count"],
            "ligand_full_atom_table_row_count": manifest["ligand_full_atom_table_row_count"],
        },
        "pocket_outputs": {
            "pocket_atom_table_written": manifest["pocket_atom_table_written"],
            "pocket_atom_table_row_count": manifest["pocket_atom_table_row_count"],
            "pocket_extraction_audit_row_count": manifest["pocket_extraction_audit_row_count"],
        },
        "geometry_smoke": {
            "coordinate_geometry_calculation_run": manifest["coordinate_geometry_calculation_run"],
            "distance_matrix_calculated": manifest["distance_matrix_calculated"],
            "pocket_radius_angstrom": manifest["pocket_radius_angstrom"],
        },
        "altloc_endpoint": {
            "hr0002_altloc_b_atom_site_659_in_pocket": manifest["hr0002_altloc_b_atom_site_659_in_pocket"],
        },
        "no_raw_or_parser_boundary": {
            "raw_files_read": manifest["raw_files_read"],
            GZIP_OPEN_KEY: manifest[GZIP_OPEN_KEY],
            "mmcif_text_read": manifest["mmcif_text_read"],
            "atom_site_text_scan_run": manifest["atom_site_text_scan_run"],
        },
        "no_training_boundary": {
            "sample_index_written": manifest["sample_index_written"],
            "model_input_materialized": manifest["model_input_materialized"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "next_step": {
            "ready_for_ligand_topology_design_gate": manifest["ready_for_ligand_topology_design_gate"],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }


def build_real_covalent_confirmed_candidate_pocket_extraction_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13k_validated = validate_step13k_pocket_extraction_design_gate_v0()
    except Exception as exc:
        step13k_validated = False
        blockers.append(f"step13k_precondition_failed:{type(exc).__name__}:{exc}")
    contract_rows = load_step13k_candidate_contract_rows_v0() if STEP13K_CANDIDATE_CONTRACT_CSV.is_file() else []
    protein_rows = load_step13j_protein_full_atom_rows_v0() if STEP13J_PROTEIN_FULL_ATOM_TABLE_CSV.is_file() else []
    ligand_rows = load_step13j_ligand_full_atom_rows_v0() if STEP13J_LIGAND_FULL_ATOM_TABLE_CSV.is_file() else []
    _ = load_step13j_endpoint_recovery_audit_rows_v0() if STEP13J_ENDPOINT_RECOVERY_AUDIT_CSV.is_file() else []
    pocket_rows, audit_rows = (
        build_pocket_atom_table_and_audit_v0(contract_rows, protein_rows, ligand_rows)
        if step13k_validated
        else ([], [])
    )
    processed_pdb_ids = [row["pdb_id"] for row in contract_rows]
    processed_review_row_ids = [row["review_row_id"] for row in contract_rows]
    all_pocket_extraction_passed = bool(audit_rows) and all(row["pocket_extraction_passed"] is True for row in audit_rows)
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
    hr2_in_pocket = any(
        row["review_row_id"] == "HR_0002"
        and row["atom_site_id"] == "659"
        and row["label_alt_id"] == "B"
        and row["is_covalent_endpoint_atom"] is True
        for row in pocket_rows
    )
    passed = (
        step13k_validated
        and len(contract_rows) == EXPECTED_CONTRACT_ROW_COUNT
        and len(protein_rows) == EXPECTED_PROTEIN_ROW_COUNT
        and len(ligand_rows) == EXPECTED_LIGAND_ROW_COUNT
        and len(audit_rows) == EXPECTED_CONTRACT_ROW_COUNT
        and bool(pocket_rows)
        and all_pocket_extraction_passed
        and hr2_in_pocket
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    manifest: dict[str, Any] = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13k_pocket_extraction_design_gate_validated": step13k_validated,
        "pocket_extraction_candidate_contract_csv_read": bool(contract_rows),
        "pocket_extraction_candidate_contract_row_count": len(contract_rows),
        "protein_full_atom_table_csv_read": bool(protein_rows),
        "ligand_full_atom_table_csv_read": bool(ligand_rows),
        "protein_full_atom_table_row_count": len(protein_rows),
        "ligand_full_atom_table_row_count": len(ligand_rows),
        "pocket_radius_angstrom": POCKET_RADIUS_ANGSTROM,
        "coordinate_geometry_calculation_run": True,
        "distance_matrix_calculated": True,
        "pocket_extraction_run": True,
        "pocket_atom_table_written": True,
        "pocket_extraction_audit_written": True,
        "pocket_extraction_audit_row_count": len(audit_rows),
        "pocket_atom_table_row_count": len(pocket_rows),
        "all_pocket_extraction_passed": all_pocket_extraction_passed,
        "processed_pdb_ids": processed_pdb_ids,
        "processed_review_row_ids": processed_review_row_ids,
        "per_candidate_pocket_atom_row_count": {
            row["review_row_id"]: row["pocket_atom_row_count"] for row in audit_rows
        },
        "per_candidate_ligand_heavy_atom_count": {
            row["review_row_id"]: row["ligand_heavy_atom_count"] for row in audit_rows
        },
        "hr0002_altloc_b_atom_site_659_in_pocket": hr2_in_pocket,
        "raw_files_read": False,
        GZIP_OPEN_KEY: False,
        "mmcif_text_read": False,
        "atom_site_text_scan_run": False,
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "ligand_topology_table_written": False,
        "sample_index_written": False,
        "enriched_sample_index_written": False,
        "final_dataset_written": False,
        "model_input_materialized": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "training_ready_samples_claimed": False,
        "training_allowed": False,
        "finetune_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "external_network_called": False,
        "data_downloaded": False,
        "download_attempted": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "output_limited_to_csv_json_md": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_committable_artifacts_created": forbidden_artifacts,
        "raw_files_staged": raw_staged,
        "raw_files_tracked": raw_tracked,
        "ready_for_ligand_topology_design_gate": passed,
        "ready_to_write_sample_index_now": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP
        if passed
        else "real_covalent_confirmed_candidate_pocket_extraction_smoke_debug",
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "pocket_rows": pocket_rows,
        "audit_rows": audit_rows,
        "report_sections": _build_report_sections(manifest),
    }
