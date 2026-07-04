from __future__ import annotations

import csv
import gzip
import json
import math
import shlex
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0"

STEP13E_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_manifest.json"
)
STEP13D_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_contract.csv"
)
STEP13D_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_manifest.json"
)
STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_confirmed_candidate_table.csv"
)
STEP13E_SUMMARY_MD = Path(
    "docs/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0_summary.md"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0"
)
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / (
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_manifest.json"
)
ALTLOC_AWARE_COORDINATES_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinates_altloc_aware.csv"
ALTLOC_SELECTION_AUDIT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_altloc_selection_audit.csv"
SUMMARY_MD = Path(
    "docs/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0_summary.md"
)

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_CONTRACT_ROW_COUNT = 6
EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT = 6
EXPECTED_AUDIT_ROW_COUNT = 3

STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM = 0.05
RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware"

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

EXTRACTED_COORDINATE_COLUMNS = [
    "coordinate_contract_id",
    "confirmed_candidate_id",
    "review_row_id",
    "candidate_stub_id",
    "sample_id",
    "pdb_id",
    "entry_id",
    "structure_title",
    "raw_path",
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
    "match_strategy_used",
    "atom_site_match_status",
    "atom_site_match_count",
    "selected_atom_site_id",
    "selected_group_PDB",
    "selected_type_symbol",
    "selected_label_atom_id",
    "selected_label_alt_id",
    "selected_label_comp_id",
    "selected_label_asym_id",
    "selected_label_entity_id",
    "selected_label_seq_id",
    "selected_auth_seq_id",
    "selected_auth_comp_id",
    "selected_auth_asym_id",
    "selected_auth_atom_id",
    "selected_pdbx_PDB_model_num",
    "Cartn_x",
    "Cartn_y",
    "Cartn_z",
    "occupancy",
    "B_iso_or_equiv",
    "altloc_policy_applied",
    "model_policy_applied",
    "occupancy_policy_applied",
    "coordinate_extraction_ready",
    "coordinates_extracted",
    "distance_calculated",
    "rdkit_used",
    "sample_index_written",
    "final_dataset_written",
    "training_ready",
    "training_ready_reason",
]

ALTLOC_SELECTION_AUDIT_COLUMNS = [
    "confirmed_candidate_id",
    "review_row_id",
    "pdb_id",
    "manual_confirmed_covalent_bond",
    "struct_conn_reported_distance_angstrom",
    "protein_candidate_count",
    "ligand_candidate_count",
    "candidate_pair_count",
    "selected_protein_atom_site_id",
    "selected_protein_label_alt_id",
    "selected_protein_occupancy",
    "selected_ligand_atom_site_id",
    "selected_ligand_label_alt_id",
    "selected_ligand_occupancy",
    "selected_pair_distance_angstrom",
    "selected_pair_delta_from_struct_conn",
    "selection_strategy",
    "selection_reason",
    "distance_agrees_with_struct_conn",
    "altloc_aware_selection_applied",
]

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


def _normalize_missing(value: str) -> str:
    return "" if value in {".", "?"} else value


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


def _raw_files_tracked(raw_paths: list[str]) -> bool:
    return any(_run_git(["ls-files", "--error-unmatch", raw_path]).returncode == 0 for raw_path in raw_paths)


def _float_parseable(value: Any) -> bool:
    try:
        float(str(value))
    except ValueError:
        return False
    return True


def _format_distance(value: float) -> str:
    return f"{value:.4f}"


def validate_step13e_smoke_and_step13d_contract_v0() -> bool:
    required_paths = [STEP13E_MANIFEST_JSON, STEP13D_MANIFEST_JSON, STEP13D_CONTRACT_CSV, STEP13E_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13E2 prerequisite outputs are missing: {missing}")
    step13e = _load_json(STEP13E_MANIFEST_JSON)
    step13d = _load_json(STEP13D_MANIFEST_JSON)
    contract_rows = _read_csv(STEP13D_CONTRACT_CSV)
    blockers: list[str] = []
    step13e_expected = {
        "stage": PREVIOUS_STAGE,
        "all_checks_passed": True,
        "extracted_coordinate_row_count": 6,
        "matched_endpoint_row_count": 6,
        "unmatched_endpoint_row_count": 0,
        "all_endpoint_coordinates_extracted": True,
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "atom_site_text_scan_run": True,
        "ready_for_confirmed_candidate_coordinate_pair_sanity_gate": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "recommended_next_step": "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate",
    }
    for key, value in step13e_expected.items():
        _expect(step13e[key] == value, f"step13e_{key}_invalid:{step13e[key]!r}", blockers)
    step13d_expected = {
        "stage": "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0",
        "all_checks_passed": True,
        "coordinate_extraction_contract_row_count": 6,
        "all_endpoint_roles_from_manual_review": True,
        "ready_for_confirmed_candidate_atom_site_coordinate_extraction_smoke": True,
    }
    for key, value in step13d_expected.items():
        _expect(step13d[key] == value, f"step13d_{key}_invalid:{step13d[key]!r}", blockers)
    _expect(len(contract_rows) == EXPECTED_CONTRACT_ROW_COUNT, "contract_row_count_invalid", blockers)
    by_candidate = Counter(row["confirmed_candidate_id"] for row in contract_rows)
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in contract_rows:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
        _expect(Path(row["expected_raw_path"]).is_file(), f"expected_raw_path_missing:{row['expected_raw_path']}", blockers)
        _expect(_is_true_text(row["coordinate_extraction_ready"]), "coordinate_extraction_ready_invalid", blockers)
        _expect(_is_false_text(row["coordinates_extracted"]), "coordinates_extracted_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "training_ready_invalid", blockers)
    _expect(sorted(by_candidate.values()) == [2, 2, 2], "contract_rows_per_candidate_invalid", blockers)
    _expect(
        all(roles == {"protein_residue", "ligand"} for roles in roles_by_review.values()),
        "contract_roles_per_review_invalid",
        blockers,
    )
    summary = STEP13E_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "actual confirmed candidate atom_site coordinate extraction smoke",
        "Endpoint coordinates extracted: 6",
        "not sample_index and not training",
    ]:
        _expect(snippet in summary, f"step13e_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_coordinate_contract_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13D_CONTRACT_CSV)


def load_struct_conn_reported_distances_v0() -> dict[str, str]:
    rows = _read_csv(STEP13C_CONFIRMED_CANDIDATE_TABLE_CSV)
    return {row["review_row_id"]: row["pdbx_dist_value"] for row in rows}


def read_raw_mmcif_text_in_memory_v0(raw_path: Path) -> str:
    with gzip.open(raw_path, "rt", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def extract_atom_site_loop_rows_v0(mmcif_text: str) -> list[dict[str, str]]:
    lines = mmcif_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        header_index = index + 1
        headers: list[str] = []
        while header_index < len(lines) and lines[header_index].strip().startswith("_atom_site."):
            headers.append(lines[header_index].strip())
            header_index += 1
        if not headers or "_atom_site.Cartn_x" not in headers or "_atom_site.Cartn_y" not in headers:
            continue
        if "_atom_site.Cartn_z" not in headers:
            continue
        rows: list[dict[str, str]] = []
        data_index = header_index
        while data_index < len(lines):
            stripped = lines[data_index].strip()
            if not stripped:
                data_index += 1
                continue
            if stripped == "#" or stripped == "loop_" or stripped.startswith("data_"):
                break
            if stripped.startswith("_") and not stripped.startswith("_atom_site."):
                break
            tokens = shlex.split(stripped, posix=True)
            if len(tokens) == len(headers):
                rows.append({header: _normalize_missing(token) for header, token in zip(headers, tokens)})
            data_index += 1
        return rows
    return []


def _atom_value(atom_row: dict[str, str], field: str) -> str:
    return _normalize_missing(atom_row.get("_atom_site." + field, ""))


def _contract_value(contract_row: dict[str, str], field: str) -> str:
    return contract_row.get(field, "")


def _label_matches(atom_row: dict[str, str], contract_row: dict[str, str]) -> bool:
    return (
        _atom_value(atom_row, "label_asym_id") == _contract_value(contract_row, "endpoint_label_asym_id")
        and _atom_value(atom_row, "label_comp_id") == _contract_value(contract_row, "endpoint_label_comp_id")
        and _atom_value(atom_row, "label_seq_id") == _contract_value(contract_row, "endpoint_label_seq_id")
        and _atom_value(atom_row, "label_atom_id") == _contract_value(contract_row, "endpoint_label_atom_id")
    )


def _auth_matches(atom_row: dict[str, str], contract_row: dict[str, str]) -> bool:
    return (
        _atom_value(atom_row, "auth_asym_id") == _contract_value(contract_row, "endpoint_auth_asym_id")
        and _atom_value(atom_row, "auth_comp_id") == _contract_value(contract_row, "endpoint_auth_comp_id")
        and _atom_value(atom_row, "auth_seq_id") == _contract_value(contract_row, "endpoint_auth_seq_id")
        and _atom_value(atom_row, "auth_atom_id") == _contract_value(contract_row, "endpoint_auth_atom_id")
    )


def _auth_ligand_optional_seq_matches(atom_row: dict[str, str], contract_row: dict[str, str]) -> bool:
    return (
        contract_row["endpoint_role"] == "ligand"
        and _atom_value(atom_row, "auth_asym_id") == _contract_value(contract_row, "endpoint_auth_asym_id")
        and _atom_value(atom_row, "auth_comp_id") == _contract_value(contract_row, "endpoint_auth_comp_id")
        and _atom_value(atom_row, "auth_atom_id") == _contract_value(contract_row, "endpoint_auth_atom_id")
    )


def find_atom_site_candidate_matches_v0(
    atom_rows: list[dict[str, str]], contract_row: dict[str, str]
) -> dict[str, Any]:
    strategy_matches = [
        ("label_exact", [row for row in atom_rows if _label_matches(row, contract_row)]),
        ("auth_exact", [row for row in atom_rows if _auth_matches(row, contract_row)]),
        ("auth_ligand_seq_optional", [row for row in atom_rows if _auth_ligand_optional_seq_matches(row, contract_row)]),
    ]
    for strategy, matches in strategy_matches:
        if matches:
            return {"match_strategy_used": strategy, "atom_site_match_count": len(matches), "candidate_rows": matches}
    return {"match_strategy_used": "unmatched", "atom_site_match_count": 0, "candidate_rows": []}


def _distance(left: dict[str, str], right: dict[str, str]) -> float:
    return math.sqrt(
        (float(_atom_value(left, "Cartn_x")) - float(_atom_value(right, "Cartn_x"))) ** 2
        + (float(_atom_value(left, "Cartn_y")) - float(_atom_value(right, "Cartn_y"))) ** 2
        + (float(_atom_value(left, "Cartn_z")) - float(_atom_value(right, "Cartn_z"))) ** 2
    )


def _model_rank(atom_row: dict[str, str]) -> int:
    return 0 if _atom_value(atom_row, "pdbx_PDB_model_num") in {"", "1"} else 1


def _occupancy(atom_row: dict[str, str]) -> float:
    text = _atom_value(atom_row, "occupancy")
    return float(text) if text else 0.0


def _atom_id_rank(atom_row: dict[str, str]) -> int:
    text = _atom_value(atom_row, "id")
    return int(text) if text.isdigit() else 10**9


def _ligand_altloc_rank(atom_row: dict[str, str]) -> int:
    return 0 if _atom_value(atom_row, "label_alt_id") == "" else 1


def select_altloc_aware_pair_v0(
    protein_contract_row: dict[str, str],
    ligand_contract_row: dict[str, str],
    protein_candidates: list[dict[str, str]],
    ligand_candidates: list[dict[str, str]],
    reported_distance: str,
) -> dict[str, Any]:
    reported = float(reported_distance)
    pair_options: list[dict[str, Any]] = []
    for protein in protein_candidates:
        for ligand in ligand_candidates:
            distance = _distance(protein, ligand)
            delta = abs(distance - reported)
            pair_options.append(
                {
                    "protein": protein,
                    "ligand": ligand,
                    "distance": distance,
                    "delta": delta,
                    "sort_key": (
                        round(delta, 10),
                        _model_rank(protein) + _model_rank(ligand),
                        -(_occupancy(protein) + _occupancy(ligand)),
                        _ligand_altloc_rank(ligand),
                        _atom_id_rank(protein),
                        _atom_id_rank(ligand),
                    ),
                }
            )
    if not pair_options:
        raise ValueError(
            "no_atom_site_pair_candidates:"
            f"{protein_contract_row['review_row_id']}:{protein_contract_row['confirmed_candidate_id']}"
        )
    selected = sorted(pair_options, key=lambda row: row["sort_key"])[0]
    return {
        "selected_protein": selected["protein"],
        "selected_ligand": selected["ligand"],
        "selected_pair_distance": selected["distance"],
        "selected_pair_delta": selected["delta"],
        "candidate_pair_count": len(pair_options),
        "distance_agrees_with_struct_conn": selected["delta"] <= STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM,
        "selection_strategy": "nearest_struct_conn_reported_distance_then_model_occupancy_altloc_tiebreak",
        "selection_reason": (
            "selected_endpoint_pair_minimizes_abs_delta_to_struct_conn_pdbx_dist_value"
            f":reported={reported_distance}:distance={_format_distance(selected['distance'])}:"
            f"delta={_format_distance(selected['delta'])}"
        ),
    }


def _selected_value(atom_row: dict[str, str], field: str) -> str:
    return _atom_value(atom_row, field)


def _coordinate_row(
    contract_row: dict[str, str],
    selected_atom: dict[str, str],
    match_info: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    return {
        "coordinate_contract_id": contract_row["coordinate_contract_id"],
        "confirmed_candidate_id": contract_row["confirmed_candidate_id"],
        "review_row_id": contract_row["review_row_id"],
        "candidate_stub_id": contract_row["candidate_stub_id"],
        "sample_id": contract_row["sample_id"],
        "pdb_id": contract_row["pdb_id"],
        "entry_id": contract_row["entry_id"],
        "structure_title": contract_row["structure_title"],
        "raw_path": contract_row["expected_raw_path"],
        "manual_confirmed_covalent_bond": contract_row["manual_confirmed_covalent_bond"],
        "manual_confirmed_ligand_comp_id": contract_row["manual_confirmed_ligand_comp_id"],
        "manual_confirmed_residue_comp_id": contract_row["manual_confirmed_residue_comp_id"],
        "manual_confirmed_ligand_atom_id": contract_row["manual_confirmed_ligand_atom_id"],
        "manual_confirmed_residue_atom_id": contract_row["manual_confirmed_residue_atom_id"],
        "manual_confirmed_warhead_type": contract_row["manual_confirmed_warhead_type"],
        "endpoint_role": contract_row["endpoint_role"],
        "endpoint_partner": contract_row["endpoint_partner"],
        "endpoint_comp_id": contract_row["endpoint_comp_id"],
        "endpoint_atom_id": contract_row["endpoint_atom_id"],
        "match_strategy_used": match_info["match_strategy_used"],
        "atom_site_match_status": status,
        "atom_site_match_count": match_info["atom_site_match_count"],
        "selected_atom_site_id": _selected_value(selected_atom, "id"),
        "selected_group_PDB": _selected_value(selected_atom, "group_PDB"),
        "selected_type_symbol": _selected_value(selected_atom, "type_symbol"),
        "selected_label_atom_id": _selected_value(selected_atom, "label_atom_id"),
        "selected_label_alt_id": _selected_value(selected_atom, "label_alt_id"),
        "selected_label_comp_id": _selected_value(selected_atom, "label_comp_id"),
        "selected_label_asym_id": _selected_value(selected_atom, "label_asym_id"),
        "selected_label_entity_id": _selected_value(selected_atom, "label_entity_id"),
        "selected_label_seq_id": _selected_value(selected_atom, "label_seq_id"),
        "selected_auth_seq_id": _selected_value(selected_atom, "auth_seq_id"),
        "selected_auth_comp_id": _selected_value(selected_atom, "auth_comp_id"),
        "selected_auth_asym_id": _selected_value(selected_atom, "auth_asym_id"),
        "selected_auth_atom_id": _selected_value(selected_atom, "auth_atom_id"),
        "selected_pdbx_PDB_model_num": _selected_value(selected_atom, "pdbx_PDB_model_num"),
        "Cartn_x": _selected_value(selected_atom, "Cartn_x"),
        "Cartn_y": _selected_value(selected_atom, "Cartn_y"),
        "Cartn_z": _selected_value(selected_atom, "Cartn_z"),
        "occupancy": _selected_value(selected_atom, "occupancy"),
        "B_iso_or_equiv": _selected_value(selected_atom, "B_iso_or_equiv"),
        "altloc_policy_applied": "selected_by_struct_conn_distance_agreement",
        "model_policy_applied": "prefer_model_1_then_distance_tiebreak",
        "occupancy_policy_applied": "record_occupancy_use_as_tiebreak_after_distance",
        "coordinate_extraction_ready": True,
        "coordinates_extracted": True,
        "distance_calculated": False,
        "rdkit_used": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "training_ready": False,
        "training_ready_reason": "altloc_aware_coordinates_extracted_but_no_pair_sanity_no_sample_index",
    }


def build_altloc_aware_coordinate_rows_and_audit_v0(
    contract_rows: list[dict[str, str]],
    atom_rows_by_pdb: dict[str, list[dict[str, str]]],
    struct_conn_distances: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in contract_rows:
        rows_by_candidate[row["confirmed_candidate_id"]].append(row)
    coordinate_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for confirmed_candidate_id in sorted(rows_by_candidate):
        group = rows_by_candidate[confirmed_candidate_id]
        role_map = {row["endpoint_role"]: row for row in group}
        protein_contract = role_map["protein_residue"]
        ligand_contract = role_map["ligand"]
        pdb_id = protein_contract["pdb_id"]
        protein_match = find_atom_site_candidate_matches_v0(atom_rows_by_pdb[pdb_id], protein_contract)
        ligand_match = find_atom_site_candidate_matches_v0(atom_rows_by_pdb[pdb_id], ligand_contract)
        selected = select_altloc_aware_pair_v0(
            protein_contract,
            ligand_contract,
            protein_match["candidate_rows"],
            ligand_match["candidate_rows"],
            struct_conn_distances[protein_contract["review_row_id"]],
        )
        protein_status = (
            "matched_altloc_aware_pair_selected"
            if protein_match["atom_site_match_count"] > 1
            else "matched_unique_after_altloc_aware_pair_selection"
        )
        ligand_status = (
            "matched_altloc_aware_pair_selected"
            if ligand_match["atom_site_match_count"] > 1
            else "matched_unique_after_altloc_aware_pair_selection"
        )
        coordinate_rows.append(
            _coordinate_row(protein_contract, selected["selected_protein"], protein_match, protein_status)
        )
        coordinate_rows.append(_coordinate_row(ligand_contract, selected["selected_ligand"], ligand_match, ligand_status))
        audit_rows.append(
            {
                "confirmed_candidate_id": confirmed_candidate_id,
                "review_row_id": protein_contract["review_row_id"],
                "pdb_id": pdb_id,
                "manual_confirmed_covalent_bond": protein_contract["manual_confirmed_covalent_bond"],
                "struct_conn_reported_distance_angstrom": struct_conn_distances[protein_contract["review_row_id"]],
                "protein_candidate_count": protein_match["atom_site_match_count"],
                "ligand_candidate_count": ligand_match["atom_site_match_count"],
                "candidate_pair_count": selected["candidate_pair_count"],
                "selected_protein_atom_site_id": _atom_value(selected["selected_protein"], "id"),
                "selected_protein_label_alt_id": _atom_value(selected["selected_protein"], "label_alt_id"),
                "selected_protein_occupancy": _atom_value(selected["selected_protein"], "occupancy"),
                "selected_ligand_atom_site_id": _atom_value(selected["selected_ligand"], "id"),
                "selected_ligand_label_alt_id": _atom_value(selected["selected_ligand"], "label_alt_id"),
                "selected_ligand_occupancy": _atom_value(selected["selected_ligand"], "occupancy"),
                "selected_pair_distance_angstrom": _format_distance(selected["selected_pair_distance"]),
                "selected_pair_delta_from_struct_conn": _format_distance(selected["selected_pair_delta"]),
                "selection_strategy": selected["selection_strategy"],
                "selection_reason": selected["selection_reason"],
                "distance_agrees_with_struct_conn": selected["distance_agrees_with_struct_conn"],
                "altloc_aware_selection_applied": True,
            }
        )
    return coordinate_rows, audit_rows


def _build_extraction_summary(
    contract_rows: list[dict[str, str]],
    coordinate_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    atom_rows_by_pdb: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    atom_counts = {pdb_id: len(atom_rows_by_pdb[pdb_id]) for pdb_id in EXPECTED_PDB_IDS}
    deltas = [float(row["selected_pair_delta_from_struct_conn"]) for row in audit_rows]
    hr0002 = next(row for row in audit_rows if row["review_row_id"] == "HR_0002")
    return {
        "coordinate_contract_row_count": len(contract_rows),
        "raw_file_count": len({row["expected_raw_path"] for row in contract_rows}),
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "atom_site_text_scan_run": True,
        "atom_site_rows_scanned_total": sum(atom_counts.values()),
        "atom_site_rows_scanned_by_pdb": atom_counts,
        "altloc_aware_coordinates_csv_written": True,
        "altloc_aware_coordinate_row_count": len(coordinate_rows),
        "altloc_selection_audit_csv_written": True,
        "altloc_selection_audit_row_count": len(audit_rows),
        "matched_endpoint_row_count": sum(1 for row in coordinate_rows if row["coordinates_extracted"] is True),
        "unmatched_endpoint_row_count": sum(1 for row in coordinate_rows if row["coordinates_extracted"] is not True),
        "all_endpoint_coordinates_extracted": all(row["coordinates_extracted"] is True for row in coordinate_rows),
        "all_required_coordinate_fields_present": all(
            row["Cartn_x"] and row["Cartn_y"] and row["Cartn_z"] for row in coordinate_rows
        ),
        "all_numeric_coordinate_fields_parseable": all(
            _float_parseable(row["Cartn_x"])
            and _float_parseable(row["Cartn_y"])
            and _float_parseable(row["Cartn_z"])
            and (not row["occupancy"] or _float_parseable(row["occupancy"]))
            and (not row["B_iso_or_equiv"] or _float_parseable(row["B_iso_or_equiv"]))
            for row in coordinate_rows
        ),
        "all_endpoint_roles_preserved": all(row["endpoint_role"] in {"protein_residue", "ligand"} for row in coordinate_rows),
        "all_altloc_selection_audit_rows_valid": all(
            int(row["protein_candidate_count"]) >= 1
            and int(row["ligand_candidate_count"]) >= 1
            and int(row["candidate_pair_count"]) >= 1
            for row in audit_rows
        ),
        "all_selected_pairs_match_struct_conn_reported": all(
            row["distance_agrees_with_struct_conn"] is True for row in audit_rows
        ),
        "max_selected_pair_delta_from_struct_conn": max(deltas) if deltas else None,
        "hr0002_altloc_corrected": hr0002["selected_protein_atom_site_id"] == "659"
        and hr0002["selected_protein_label_alt_id"] == "B",
        "hr0002_selected_protein_atom_site_id": hr0002["selected_protein_atom_site_id"],
        "hr0002_selected_protein_label_alt_id": hr0002["selected_protein_label_alt_id"],
        "hr0002_selected_pair_distance_angstrom": float(hr0002["selected_pair_distance_angstrom"]),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "processed_review_row_ids": EXPECTED_REVIEW_ROW_IDS,
    }


def build_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        precondition_validated = validate_step13e_smoke_and_step13d_contract_v0()
    except Exception as exc:
        precondition_validated = False
        blockers.append(f"precondition_validation_failed:{type(exc).__name__}:{exc}")
    step13d_manifest = _load_json(STEP13D_MANIFEST_JSON)
    contract_rows = load_coordinate_contract_rows_v0()
    struct_conn_distances = load_struct_conn_reported_distances_v0()
    atom_rows_by_pdb: dict[str, list[dict[str, str]]] = {}
    for pdb_id in EXPECTED_PDB_IDS:
        raw_path = next(Path(row["expected_raw_path"]) for row in contract_rows if row["pdb_id"] == pdb_id)
        try:
            text = read_raw_mmcif_text_in_memory_v0(raw_path)
            atom_rows_by_pdb[pdb_id] = extract_atom_site_loop_rows_v0(text)
        except Exception as exc:
            atom_rows_by_pdb[pdb_id] = []
            blockers.append(f"atom_site_scan_failed:{pdb_id}:{type(exc).__name__}:{exc}")
    try:
        coordinate_rows, audit_rows = build_altloc_aware_coordinate_rows_and_audit_v0(
            contract_rows, atom_rows_by_pdb, struct_conn_distances
        )
    except Exception as exc:
        coordinate_rows, audit_rows = [], []
        blockers.append(f"altloc_aware_selection_failed:{type(exc).__name__}:{exc}")
    extraction_summary = _build_extraction_summary(contract_rows, coordinate_rows, audit_rows, atom_rows_by_pdb) if audit_rows else {}
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked(sorted({row["expected_raw_path"] for row in contract_rows}))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    passed = bool(
        precondition_validated
        and step13d_manifest["step12b_mask_level_aware_validator_validated"]
        and extraction_summary.get("coordinate_contract_row_count") == EXPECTED_CONTRACT_ROW_COUNT
        and extraction_summary.get("altloc_aware_coordinate_row_count") == EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT
        and extraction_summary.get("altloc_selection_audit_row_count") == EXPECTED_AUDIT_ROW_COUNT
        and extraction_summary.get("matched_endpoint_row_count") == EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT
        and extraction_summary.get("unmatched_endpoint_row_count") == 0
        and extraction_summary.get("all_endpoint_coordinates_extracted") is True
        and extraction_summary.get("all_selected_pairs_match_struct_conn_reported") is True
        and extraction_summary.get("max_selected_pair_delta_from_struct_conn", 1.0)
        <= STRUCT_CONN_DISTANCE_TOLERANCE_ANGSTROM
        and extraction_summary.get("hr0002_altloc_corrected") is True
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = (
        RECOMMENDED_NEXT_STEP
        if passed
        else "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_debug"
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13e_atom_site_coordinate_extraction_smoke_validated": precondition_validated,
        "step13d_coordinate_extraction_design_gate_validated": precondition_validated,
        "step12b_mask_level_aware_validator_validated": step13d_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "altloc_aware_coordinate_extraction_rerun_defined": True,
        "altloc_aware_coordinate_extraction_rerun_executed": True,
        "coordinate_contract_csv_read": True,
        "struct_conn_reference_csv_read": True,
        **extraction_summary,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": True,
        "distance_calculated_for_altloc_selection": True,
        "final_pair_sanity_distance_calculated": False,
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
        "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_passed": passed,
        "altloc_aware_coordinate_extraction_contract_satisfied": passed,
        "ready_for_altloc_aware_coordinate_pair_sanity_gate": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {"manifest": manifest, "coordinate_rows": coordinate_rows, "audit_rows": audit_rows, "report_sections": _build_report_sections(manifest)}


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "cleanup_untracked_step13f": {"blocked_step13f_untracked_files_cleaned_before_rerun": True},
        "step13e_step13d_preconditions": {
            "step13e_atom_site_coordinate_extraction_smoke_validated": manifest[
                "step13e_atom_site_coordinate_extraction_smoke_validated"
            ],
            "step13d_coordinate_extraction_design_gate_validated": manifest[
                "step13d_coordinate_extraction_design_gate_validated"
            ],
        },
        "coordinate_contract_read": {
            "coordinate_contract_csv_read": manifest["coordinate_contract_csv_read"],
            "coordinate_contract_row_count": manifest["coordinate_contract_row_count"],
        },
        "raw_atom_site_rescan": {
            "raw_file_count": manifest["raw_file_count"],
            "atom_site_rows_scanned_total": manifest["atom_site_rows_scanned_total"],
        },
        "altloc_candidate_pair_selection": {
            "hr0002_altloc_corrected": manifest["hr0002_altloc_corrected"],
            "max_selected_pair_delta_from_struct_conn": manifest["max_selected_pair_delta_from_struct_conn"],
        },
        "altloc_aware_coordinates_written": {
            "altloc_aware_coordinate_row_count": manifest["altloc_aware_coordinate_row_count"],
            "altloc_selection_audit_row_count": manifest["altloc_selection_audit_row_count"],
        },
        "no_sample_index_no_training_boundary": {
            "sample_index_written": manifest["sample_index_written"],
            "final_dataset_written": manifest["final_dataset_written"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "next_step_decision": {
            "ready_for_altloc_aware_coordinate_pair_sanity_gate": manifest[
                "ready_for_altloc_aware_coordinate_pair_sanity_gate"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
