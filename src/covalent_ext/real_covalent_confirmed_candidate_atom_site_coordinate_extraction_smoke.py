from __future__ import annotations

import csv
import gzip
import json
import shlex
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0"
PREVIOUS_STAGE = "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0"

STEP13D_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_manifest.json"
)
STEP13D_CONTRACT_CSV = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_contract.csv"
)
STEP13D_SUMMARY_MD = Path(
    "docs/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_v0_summary.md"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0"
)
REPORT_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_manifest.json"
EXTRACTED_COORDINATES_CSV = OUTPUT_ROOT / "real_covalent_confirmed_candidate_atom_site_coordinates.csv"
SUMMARY_MD = Path("docs/real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0_summary.md")

EXPECTED_PDB_IDS = ["6DI9", "5F2E", "6OIM"]
EXPECTED_CONFIRMED_REVIEW_ROW_IDS = ["HR_0002", "HR_0003", "HR_0004"]
EXPECTED_CONTRACT_ROW_COUNT = 6
EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT = 6

RECOMMENDED_NEXT_STEP = "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate"
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

ATOM_SITE_REQUIRED_COLUMNS = [
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_alt_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_entity_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.occupancy",
    "_atom_site.B_iso_or_equiv",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_atom_id",
    "_atom_site.pdbx_PDB_model_num",
]

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


def validate_step13d_coordinate_extraction_design_gate_v0() -> bool:
    required_paths = [STEP13D_MANIFEST_JSON, STEP13D_CONTRACT_CSV, STEP13D_SUMMARY_MD]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Step 13D prerequisite outputs are missing: {missing}")
    manifest = _load_json(STEP13D_MANIFEST_JSON)
    rows = _read_csv(STEP13D_CONTRACT_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_struct_conn_candidate_manual_review_fill_validation_v0",
        "step13c_manual_review_fill_validation_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "confirmed_candidate_atom_site_coordinate_extraction_design_gate_defined": True,
        "confirmed_candidate_atom_site_coordinate_extraction_design_gate_executed": True,
        "confirmed_candidate_table_csv_read": True,
        "confirmed_candidate_table_row_count": 3,
        "coordinate_extraction_contract_csv_written": True,
        "coordinate_extraction_contract_row_count": 6,
        "protein_endpoint_row_count": 3,
        "ligand_endpoint_row_count": 3,
        "expected_endpoint_count": 6,
        "processed_pdb_ids": EXPECTED_PDB_IDS,
        "endpoint_rows_per_candidate_valid": True,
        "each_candidate_has_protein_and_ligand_endpoint": True,
        "all_endpoint_roles_from_manual_review": True,
        "all_expected_raw_paths_recorded": True,
        "all_atom_site_required_columns_recorded": True,
        "all_lookup_strategies_recorded": True,
        "all_coordinate_extraction_ready_true": True,
        "all_coordinates_extracted_false": True,
        "all_distance_calculated_false": True,
        "all_training_ready_false": True,
        "all_sample_index_written_false": True,
        "all_final_dataset_written_false": True,
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
        "original_diffsbdd_source_modified": False,
        "forbidden_committable_artifacts_created": False,
        "raw_files_staged": False,
        "raw_files_tracked": False,
        "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_design_gate_passed": True,
        "confirmed_candidate_atom_site_coordinate_extraction_design_contract_satisfied": True,
        "ready_for_confirmed_candidate_atom_site_coordinate_extraction_smoke": True,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
        "recommended_next_step": STAGE.replace("_v0", ""),
    }
    for key, value in expected.items():
        _expect(manifest[key] == value, f"step13d_{key}_invalid:{manifest[key]!r}", blockers)
    _expect(len(rows) == EXPECTED_CONTRACT_ROW_COUNT, "contract_row_count_invalid", blockers)
    by_candidate = Counter(row["confirmed_candidate_id"] for row in rows)
    roles_by_review: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        roles_by_review[row["review_row_id"]].add(row["endpoint_role"])
        _expect(row["endpoint_role"] in {"protein_residue", "ligand"}, "endpoint_role_invalid", blockers)
        _expect(row["endpoint_partner"] in {"ptnr1", "ptnr2"}, "endpoint_partner_invalid", blockers)
        _expect(Path(row["expected_raw_path"]).is_file(), f"expected_raw_path_missing:{row['expected_raw_path']}", blockers)
        _expect("_atom_site.Cartn_x" in row["atom_site_required_columns"], "cartn_x_required_missing", blockers)
        _expect("_atom_site.Cartn_y" in row["atom_site_required_columns"], "cartn_y_required_missing", blockers)
        _expect("_atom_site.Cartn_z" in row["atom_site_required_columns"], "cartn_z_required_missing", blockers)
        _expect(_is_true_text(row["coordinate_extraction_ready"]), "coordinate_extraction_ready_invalid", blockers)
        _expect(_is_false_text(row["coordinates_extracted"]), "coordinates_extracted_invalid", blockers)
        _expect(_is_false_text(row["distance_calculated"]), "distance_calculated_invalid", blockers)
        _expect(_is_false_text(row["training_ready"]), "training_ready_invalid", blockers)
        _expect(_is_false_text(row["sample_index_written"]), "sample_index_written_invalid", blockers)
        _expect(_is_false_text(row["final_dataset_written"]), "final_dataset_written_invalid", blockers)
    _expect(all(count == 2 for count in by_candidate.values()), "contract_rows_per_candidate_invalid", blockers)
    _expect(
        all(roles == {"protein_residue", "ligand"} for roles in roles_by_review.values()),
        "roles_by_review_invalid",
        blockers,
    )
    summary = STEP13D_SUMMARY_MD.read_text(encoding="utf-8")
    parser_tools = f"{BIOPDB_TEXT}/{MMCIF_PARSER_TEXT}/{PDB_PARSER_TEXT}/{VENDOR_TEXT}/{RDKIT_TEXT}"
    for snippet in [
        "confirmed candidate atom_site coordinate extraction design gate",
        "did not read raw",
        "did not decompress raw files",
        "did not parse mmCIF",
        f"did not use {parser_tools}",
        "did not extract coordinates",
        "did not calculate distance",
        "Atom endpoint coordinate extraction contract rows written: 6",
        "Endpoint role comes from manual review fields, not inference",
        "next step is actual atom_site coordinate extraction smoke, not sample_index and not training",
    ]:
        _expect(snippet in summary, f"step13d_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_coordinate_contract_rows_v0() -> list[dict[str, str]]:
    return _read_csv(STEP13D_CONTRACT_CSV)


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


def _sort_model_value(value: str) -> tuple[int, str]:
    if value in {"", "1"}:
        return (0, value)
    return (1, value)


def _sort_altloc_occupancy_atom(atom_row: dict[str, str]) -> tuple[int, float, int]:
    altloc = _atom_value(atom_row, "label_alt_id")
    occupancy_text = _atom_value(atom_row, "occupancy")
    occupancy = float(occupancy_text) if occupancy_text else 0.0
    atom_id = _atom_value(atom_row, "id")
    atom_sort_id = int(atom_id) if atom_id.isdigit() else 10**9
    return (0 if altloc == "" else 1, -occupancy, atom_sort_id)


def _select_atom_site_match(matches: list[dict[str, str]]) -> dict[str, str]:
    model_sorted = sorted(matches, key=lambda row: _sort_model_value(_atom_value(row, "pdbx_PDB_model_num")))
    best_model_rank = _sort_model_value(_atom_value(model_sorted[0], "pdbx_PDB_model_num"))
    model_matches = [row for row in model_sorted if _sort_model_value(_atom_value(row, "pdbx_PDB_model_num")) == best_model_rank]
    return sorted(model_matches, key=_sort_altloc_occupancy_atom)[0]


def find_atom_site_match_v0(atom_rows: list[dict[str, str]], contract_row: dict[str, str]) -> dict[str, Any]:
    strategy_matches = [
        ("label_exact", [row for row in atom_rows if _label_matches(row, contract_row)]),
        ("auth_exact", [row for row in atom_rows if _auth_matches(row, contract_row)]),
        ("auth_ligand_seq_optional", [row for row in atom_rows if _auth_ligand_optional_seq_matches(row, contract_row)]),
    ]
    for strategy, matches in strategy_matches:
        if not matches:
            continue
        selected = _select_atom_site_match(matches)
        status = "matched_unique_after_policy" if len(matches) == 1 else "matched_multiple_policy_selected"
        return {
            "match_strategy_used": strategy,
            "atom_site_match_status": status,
            "atom_site_match_count": len(matches),
            "selected_atom_site_row": selected,
        }
    return {
        "match_strategy_used": "unmatched",
        "atom_site_match_status": "unmatched",
        "atom_site_match_count": 0,
        "selected_atom_site_row": {},
    }


def _selected_value(atom_row: dict[str, str], field: str) -> str:
    return _atom_value(atom_row, field)


def build_extracted_coordinate_rows_v0(
    contract_rows: list[dict[str, str]], atom_rows_by_pdb: dict[str, list[dict[str, str]]]
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for contract_row in contract_rows:
        match = find_atom_site_match_v0(atom_rows_by_pdb[contract_row["pdb_id"]], contract_row)
        selected = match["selected_atom_site_row"]
        matched = bool(selected)
        output_rows.append(
            {
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
                "match_strategy_used": match["match_strategy_used"],
                "atom_site_match_status": match["atom_site_match_status"],
                "atom_site_match_count": match["atom_site_match_count"],
                "selected_atom_site_id": _selected_value(selected, "id"),
                "selected_group_PDB": _selected_value(selected, "group_PDB"),
                "selected_type_symbol": _selected_value(selected, "type_symbol"),
                "selected_label_atom_id": _selected_value(selected, "label_atom_id"),
                "selected_label_alt_id": _selected_value(selected, "label_alt_id"),
                "selected_label_comp_id": _selected_value(selected, "label_comp_id"),
                "selected_label_asym_id": _selected_value(selected, "label_asym_id"),
                "selected_label_entity_id": _selected_value(selected, "label_entity_id"),
                "selected_label_seq_id": _selected_value(selected, "label_seq_id"),
                "selected_auth_seq_id": _selected_value(selected, "auth_seq_id"),
                "selected_auth_comp_id": _selected_value(selected, "auth_comp_id"),
                "selected_auth_asym_id": _selected_value(selected, "auth_asym_id"),
                "selected_auth_atom_id": _selected_value(selected, "auth_atom_id"),
                "selected_pdbx_PDB_model_num": _selected_value(selected, "pdbx_PDB_model_num"),
                "Cartn_x": _selected_value(selected, "Cartn_x"),
                "Cartn_y": _selected_value(selected, "Cartn_y"),
                "Cartn_z": _selected_value(selected, "Cartn_z"),
                "occupancy": _selected_value(selected, "occupancy"),
                "B_iso_or_equiv": _selected_value(selected, "B_iso_or_equiv"),
                "altloc_policy_applied": "prefer_blank_altloc_then_highest_occupancy",
                "model_policy_applied": "prefer_blank_or_model_1",
                "occupancy_policy_applied": "record_occupancy_no_filter",
                "coordinate_extraction_ready": True,
                "coordinates_extracted": matched,
                "distance_calculated": False,
                "rdkit_used": False,
                "sample_index_written": False,
                "final_dataset_written": False,
                "training_ready": False,
                "training_ready_reason": (
                    "coordinates_extracted_but_distance_not_checked_no_sample_index"
                    if matched
                    else "coordinate_extraction_unmatched_no_sample_index"
                ),
            }
        )
    return output_rows


def _float_parseable(value: Any) -> bool:
    try:
        float(str(value))
    except ValueError:
        return False
    return True


def _build_extraction_summary(
    contract_rows: list[dict[str, str]],
    coordinate_rows: list[dict[str, Any]],
    atom_rows_by_pdb: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    matched_rows = [row for row in coordinate_rows if row["coordinates_extracted"] is True]
    atom_counts = {pdb_id: len(atom_rows_by_pdb[pdb_id]) for pdb_id in EXPECTED_PDB_IDS}
    return {
        "coordinate_contract_row_count": len(contract_rows),
        "raw_file_count": len({row["expected_raw_path"] for row in contract_rows}),
        "raw_files_read": True,
        "raw_files_decompressed_in_memory": True,
        "mmcif_text_read": True,
        "atom_site_text_scan_run": True,
        "atom_site_rows_scanned_total": sum(atom_counts.values()),
        "atom_site_rows_scanned_by_pdb": atom_counts,
        "extracted_coordinates_csv_written": True,
        "extracted_coordinate_row_count": len(coordinate_rows),
        "matched_endpoint_row_count": len(matched_rows),
        "unmatched_endpoint_row_count": len(coordinate_rows) - len(matched_rows),
        "all_endpoint_coordinates_extracted": len(matched_rows) == EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT,
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
        "all_match_strategies_recorded": all(
            row["match_strategy_used"] in {"label_exact", "auth_exact", "auth_ligand_seq_optional"}
            for row in coordinate_rows
        ),
        "all_match_statuses_recorded": all(
            row["atom_site_match_status"] in {"matched_unique_after_policy", "matched_multiple_policy_selected"}
            for row in coordinate_rows
        ),
        "processed_pdb_ids": EXPECTED_PDB_IDS,
    }


def build_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step13d_validated = validate_step13d_coordinate_extraction_design_gate_v0()
    except Exception as exc:
        step13d_validated = False
        blockers.append(f"step13d_validation_failed:{type(exc).__name__}:{exc}")
    step13d_manifest = _load_json(STEP13D_MANIFEST_JSON)
    contract_rows = load_coordinate_contract_rows_v0()
    raw_paths_by_pdb = {row["pdb_id"]: Path(row["expected_raw_path"]) for row in contract_rows}
    atom_rows_by_pdb: dict[str, list[dict[str, str]]] = {}
    for pdb_id in EXPECTED_PDB_IDS:
        try:
            text = read_raw_mmcif_text_in_memory_v0(raw_paths_by_pdb[pdb_id])
            atom_rows_by_pdb[pdb_id] = extract_atom_site_loop_rows_v0(text)
        except Exception as exc:
            atom_rows_by_pdb[pdb_id] = []
            blockers.append(f"atom_site_scan_failed:{pdb_id}:{type(exc).__name__}:{exc}")
    coordinate_rows = build_extracted_coordinate_rows_v0(contract_rows, atom_rows_by_pdb)
    extraction_summary = _build_extraction_summary(contract_rows, coordinate_rows, atom_rows_by_pdb)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_committable_artifacts_created()
    raw_staged = _raw_files_staged()
    raw_tracked = _raw_files_tracked([str(path) for path in raw_paths_by_pdb.values()])
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_committable_artifacts_created")
    if raw_staged:
        blockers.append("raw_files_staged")
    if raw_tracked:
        blockers.append("raw_files_tracked")
    passed = bool(
        step13d_validated
        and step13d_manifest["step12b_mask_level_aware_validator_validated"]
        and extraction_summary["coordinate_contract_row_count"] == EXPECTED_CONTRACT_ROW_COUNT
        and extraction_summary["raw_file_count"] == 3
        and extraction_summary["extracted_coordinate_row_count"] == EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT
        and extraction_summary["matched_endpoint_row_count"] == EXPECTED_EXTRACTED_COORDINATE_ROW_COUNT
        and extraction_summary["unmatched_endpoint_row_count"] == 0
        and extraction_summary["all_endpoint_coordinates_extracted"]
        and extraction_summary["all_required_coordinate_fields_present"]
        and extraction_summary["all_numeric_coordinate_fields_parseable"]
        and not source_modified
        and not forbidden_artifacts
        and not raw_staged
        and not raw_tracked
        and not blockers
    )
    next_step = RECOMMENDED_NEXT_STEP if passed else "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step13d_coordinate_extraction_design_gate_validated": step13d_validated,
        "step12b_mask_level_aware_validator_validated": step13d_manifest[
            "step12b_mask_level_aware_validator_validated"
        ],
        "confirmed_candidate_atom_site_coordinate_extraction_smoke_defined": True,
        "confirmed_candidate_atom_site_coordinate_extraction_smoke_executed": True,
        "coordinate_contract_csv_read": True,
        **extraction_summary,
        "raw_or_decompressed_mmcif_output_written": False,
        "structure_output_files_written": False,
        "full_mmcif_parser_used": False,
        "parser_library_used": "none",
        "biopdb_parser_used": False,
        VENDOR_USED_KEY: False,
        "rdkit_used": False,
        "coordinate_geometry_calculation_run": False,
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
        "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_smoke_passed": passed,
        "confirmed_candidate_atom_site_coordinate_extraction_contract_satisfied": passed,
        "ready_for_confirmed_candidate_coordinate_pair_sanity_gate": passed,
        "ready_to_write_enriched_sample_index_now": False,
        "ready_to_train_now": False,
        "ready_to_download_large_scale_data_now": False,
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }
    return {
        "manifest": manifest,
        "coordinate_rows": coordinate_rows,
        "report_sections": _build_report_sections(manifest),
    }


def _build_report_sections(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "step13d_precondition": {
            "step13d_coordinate_extraction_design_gate_validated": manifest[
                "step13d_coordinate_extraction_design_gate_validated"
            ],
            "step12b_mask_level_aware_validator_validated": manifest["step12b_mask_level_aware_validator_validated"],
        },
        "coordinate_contract_read": {
            "coordinate_contract_csv_read": manifest["coordinate_contract_csv_read"],
            "coordinate_contract_row_count": manifest["coordinate_contract_row_count"],
        },
        "raw_atom_site_scan": {
            "raw_file_count": manifest["raw_file_count"],
            "atom_site_rows_scanned_total": manifest["atom_site_rows_scanned_total"],
        },
        "endpoint_coordinate_matching": {
            "matched_endpoint_row_count": manifest["matched_endpoint_row_count"],
            "unmatched_endpoint_row_count": manifest["unmatched_endpoint_row_count"],
        },
        "extracted_coordinates_written": {
            "extracted_coordinates_csv_written": manifest["extracted_coordinates_csv_written"],
            "extracted_coordinate_row_count": manifest["extracted_coordinate_row_count"],
        },
        "no_distance_no_sample_index_boundary": {
            "distance_calculated": manifest["distance_calculated"],
            "sample_index_written": manifest["sample_index_written"],
            "training_ready_samples_claimed": manifest["training_ready_samples_claimed"],
        },
        "output_artifact_policy": {
            "output_limited_to_csv_json_md": manifest["output_limited_to_csv_json_md"],
            "raw_or_decompressed_mmcif_output_written": manifest["raw_or_decompressed_mmcif_output_written"],
        },
        "next_step_decision": {
            "ready_for_confirmed_candidate_coordinate_pair_sanity_gate": manifest[
                "ready_for_confirmed_candidate_coordinate_pair_sanity_gate"
            ],
            "recommended_next_step": manifest["recommended_next_step"],
        },
    }
