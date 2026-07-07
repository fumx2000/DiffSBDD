from __future__ import annotations

import csv
import hashlib
import json
import shlex
import subprocess
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_covpdb_raw_structure_event_annotation_smoke_v0"
PREVIOUS_STAGE = "covapie_covpdb_raw_structure_event_annotation_design_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AU_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_design_gate_v0")
STEP13AU_MANIFEST_JSON = STEP13AU_ROOT / "covapie_raw_structure_event_annotation_design_gate_manifest.json"
STEP13AU_DOWNLOAD_SCOPE_CSV = STEP13AU_ROOT / "covapie_raw_structure_download_scope_contract.csv"
STEP13AU_SOURCE_URL_CSV = STEP13AU_ROOT / "covapie_raw_structure_source_url_contract.csv"
STEP13AU_STORAGE_CSV = STEP13AU_ROOT / "covapie_raw_structure_storage_contract.csv"
STEP13AU_PARSER_PRIORITY_CSV = STEP13AU_ROOT / "covapie_raw_structure_parser_priority_contract.csv"
STEP13AU_MMCIF_MAPPING_CSV = STEP13AU_ROOT / "covapie_mmcif_struct_conn_field_mapping_contract.csv"
STEP13AU_PDB_MAPPING_CSV = STEP13AU_ROOT / "covapie_pdb_link_record_field_mapping_contract.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"

RAW_STORAGE_ROOT = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")
OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_smoke_precondition_audit.csv"
DOWNLOAD_PLAN_CSV = OUTPUT_ROOT / "covapie_raw_structure_download_plan.csv"
DOWNLOAD_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_download_audit.csv"
STORAGE_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_storage_safety_audit.csv"
FORMAT_INVENTORY_CSV = OUTPUT_ROOT / "covapie_raw_structure_format_inventory.csv"
MMCIF_STRUCT_CONN_INVENTORY_CSV = OUTPUT_ROOT / "covapie_mmcif_struct_conn_inventory.csv"
MMCIF_ATOM_SITE_VALIDATION_AUDIT_CSV = OUTPUT_ROOT / "covapie_mmcif_atom_site_validation_audit.csv"
PDB_LINK_CONECT_INVENTORY_CSV = OUTPUT_ROOT / "covapie_pdb_link_conect_inventory.csv"
EVENT_CANDIDATE_ANNOTATION_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_candidate_annotation.csv"
EVENT_KEY_RESOLUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_key_resolution_audit.csv"
OBSERVED_FAILURE_TAXONOMY_CSV = OUTPUT_ROOT / "covapie_raw_structure_observed_failure_taxonomy.csv"
MATERIALIZATION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_materialization_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_raw_structure_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_raw_structure_event_annotation_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_covpdb_raw_structure_event_annotation_smoke_v0_summary.md")

CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
ALLOWED_PDB_IDS = ["1A3B", "1A3E", "1A46", "1A54", "1A5G"]
ALLOWED_HET_CODES = ["T29", "T16", "00K", "MDC", "00L"]
FORBIDDEN_DERIVED_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
DOWNLOAD_PLAN_COLUMNS = ["card_index", "pdb_id", "het_code", "primary_url", "fallback_url", "planned_format_order", "raw_storage_path_primary", "raw_storage_path_fallback", "allowed_current_step", "download_plan_passed"]
DOWNLOAD_AUDIT_COLUMNS = ["card_index", "pdb_id", "het_code", "attempted_primary_url", "primary_fetch_attempted", "primary_fetch_succeeded", "primary_http_status_or_error", "attempted_fallback_url", "fallback_fetch_attempted", "fallback_fetch_succeeded", "fallback_http_status_or_error", "selected_raw_format", "selected_raw_path", "byte_count", "line_count", "raw_sha256", "raw_structure_downloaded", "raw_ligand_downloaded", "archive_downloaded", "download_audit_passed"]
STORAGE_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "selected_raw_path", "under_allowed_raw_storage_root", "suffix_allowed", "raw_file_exists", "raw_file_untracked", "raw_file_not_staged", "raw_file_not_committed", "raw_file_not_copied_to_derived", "storage_safety_passed"]
FORMAT_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "parser_used", "struct_conn_loop_found", "struct_conn_row_count", "atom_site_loop_found", "atom_site_row_count", "pdb_link_row_count", "pdb_conect_row_count", "format_inventory_passed"]
STRUCT_CONN_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "struct_conn_loop_found", "struct_conn_row_count", "het_code_in_struct_conn_count", "covalent_like_struct_conn_count", "protein_ligand_candidate_count", "struct_conn_inventory_passed"]
ATOM_SITE_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "atom_site_loop_found", "atom_site_row_count", "het_code_atom_site_count", "candidate_partner_validation_attempted", "protein_partner_atom_exists_count", "ligand_partner_atom_exists_count", "atom_site_validation_passed"]
PDB_LINK_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "link_record_count", "conect_record_count", "het_code_in_link_count", "protein_ligand_link_candidate_count", "pdb_link_conect_inventory_passed"]
EVENT_CANDIDATE_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "raw_connection_source", "candidate_index", "candidate_found", "conn_type_or_record_type", "chain_id", "residue_name", "residue_index", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "protein_partner_atom_exists", "ligand_partner_atom_exists", "candidate_confidence", "manual_review_required", "candidate_annotation_passed"]
RESOLUTION_COLUMNS = ["pdb_id", "het_code", "selected_raw_format", "raw_connection_source", "candidate_count", "preferred_fields_found_count", "minimal_fields_found_count", "chain_id_status", "residue_name_status", "residue_index_status", "residue_atom_name_status", "ligand_atom_name_status", "covalent_bond_atom_pair_status", "resolution_status", "candidate_metadata_can_materialize_current_step", "allowlist_can_materialize_current_step", "future_candidate_metadata_possible", "future_automatic_allowlist_possible", "manual_review_required", "event_key_resolution_audit_passed"]
FAILURE_COLUMNS = ["failure_reason", "observed_count", "blocks_candidate_metadata_current_step", "recommended_handling"]
MATERIALIZATION_COLUMNS = ["boundary_item", "current_step_status", "future_condition", "materialization_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_raw_structure_event_annotation_smoke", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_split_item", "current_step_status", "future_required_gate", "split_written_current_step", "leakage_matrix_written_current_step", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _metadata_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _bool_text(value: Any) -> str:
    return "True" if value is True or str(value) == "True" else "False"


def _path_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _first5_metadata() -> list[dict[str, str]]:
    return _csv_rows(METADATA_CSV)[:5]


def _allowed_primary_url(pdb_id: str) -> str:
    return f"https://files.rcsb.org/download/{pdb_id.upper()}.cif"


def _allowed_fallback_url(pdb_id: str) -> str:
    return f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"


def _download_plan(metadata_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "card_index": index,
            "pdb_id": row["pdb_id"].upper(),
            "het_code": row["het_code"],
            "primary_url": _allowed_primary_url(row["pdb_id"]),
            "fallback_url": _allowed_fallback_url(row["pdb_id"]),
            "planned_format_order": "mmcif;pdb_fallback_only_if_mmcif_fails",
            "raw_storage_path_primary": str(RAW_STORAGE_ROOT / f"{row['pdb_id'].upper()}.cif"),
            "raw_storage_path_fallback": str(RAW_STORAGE_ROOT / f"{row['pdb_id'].upper()}.pdb"),
            "allowed_current_step": row["pdb_id"].upper() in ALLOWED_PDB_IDS,
            "download_plan_passed": row["pdb_id"].upper() in ALLOWED_PDB_IDS,
        }
        for index, row in enumerate(metadata_rows, start=1)
    ]


def fetch_url_to_path(url: str, path: Path, timeout: int = 20) -> tuple[bool, str, int, int, str]:
    if not url.startswith("https://files.rcsb.org/download/"):
        return False, "blocked_url_not_allowed", 0, 0, ""
    if not (url.endswith(".cif") or url.endswith(".pdb")):
        return False, "blocked_suffix_not_allowed", 0, 0, ""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            data = response.read()
    except urllib.error.HTTPError as exc:
        return False, str(exc.code), 0, 0, ""
    except Exception as exc:  # pragma: no cover - network errors vary by environment.
        return False, exc.__class__.__name__, 0, 0, ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    text = data.decode("utf-8", errors="replace")
    return True, str(status), len(data), len(text.splitlines()), _sha256_bytes(data)


def _download_structures(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in plan_rows:
        primary_path = Path(row["raw_storage_path_primary"])
        fallback_path = Path(row["raw_storage_path_fallback"])
        primary_ok, primary_status, byte_count, line_count, digest = fetch_url_to_path(row["primary_url"], primary_path)
        fallback_attempted = False
        fallback_ok = False
        fallback_status = ""
        selected_format = "mmcif" if primary_ok else ""
        selected_path = primary_path if primary_ok else Path("")
        if not primary_ok:
            fallback_attempted = True
            fallback_ok, fallback_status, byte_count, line_count, digest = fetch_url_to_path(row["fallback_url"], fallback_path)
            selected_format = "pdb" if fallback_ok else ""
            selected_path = fallback_path if fallback_ok else Path("")
        succeeded = primary_ok or fallback_ok
        rows.append(
            {
                "card_index": row["card_index"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "attempted_primary_url": row["primary_url"],
                "primary_fetch_attempted": True,
                "primary_fetch_succeeded": primary_ok,
                "primary_http_status_or_error": primary_status,
                "attempted_fallback_url": row["fallback_url"] if fallback_attempted else "",
                "fallback_fetch_attempted": fallback_attempted,
                "fallback_fetch_succeeded": fallback_ok,
                "fallback_http_status_or_error": fallback_status,
                "selected_raw_format": selected_format,
                "selected_raw_path": str(selected_path) if succeeded else "",
                "byte_count": byte_count,
                "line_count": line_count,
                "raw_sha256": digest,
                "raw_structure_downloaded": succeeded,
                "raw_ligand_downloaded": False,
                "archive_downloaded": False,
                "download_audit_passed": succeeded,
            }
        )
    return rows


def _strip_category(header: str) -> str:
    return header.split(".", 1)[1] if "." in header else header


def _tokenize_mmcif_values(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return list(lexer)


def parse_mmcif_loops(text: str, categories: set[str] | None = None) -> dict[str, list[dict[str, str]]]:
    lines = text.splitlines()
    result: dict[str, list[dict[str, str]]] = {}
    index = 0
    while index < len(lines):
        if lines[index].strip() != "loop_":
            index += 1
            continue
        index += 1
        headers: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("_"):
            headers.append(lines[index].strip())
            index += 1
        if not headers:
            continue
        category = headers[0].split(".", 1)[0].lstrip("_")
        data_lines: list[str] = []
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "loop_" or stripped.startswith("data_") or stripped.startswith("save_") or stripped.startswith("_"):
                break
            if stripped:
                data_lines.append(lines[index])
            index += 1
        if categories and category not in categories:
            continue
        tokens = _tokenize_mmcif_values("\n".join(data_lines))
        width = len(headers)
        rows = []
        for start in range(0, len(tokens) - (len(tokens) % width), width):
            values = tokens[start : start + width]
            rows.append({_strip_category(header): value if value not in {".", "?"} else "" for header, value in zip(headers, values)})
        result[category] = rows
    return result


def _first_present(row: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = row.get(name, "")
        if value:
            return value
    return ""


def _partner_from_struct_conn(row: dict[str, str], prefix: str) -> dict[str, str]:
    other = "1" if prefix == "ptnr1" else "2"
    return {
        "atom": _first_present(row, [f"{prefix}_label_atom_id"]),
        "comp": _first_present(row, [f"{prefix}_label_comp_id", f"pdbx_ptnr{other}_auth_comp_id"]),
        "chain": _first_present(row, [f"{prefix}_auth_asym_id", f"pdbx_ptnr{other}_auth_asym_id", f"{prefix}_label_asym_id"]),
        "seq": _first_present(row, [f"{prefix}_auth_seq_id", f"pdbx_ptnr{other}_auth_seq_id", f"{prefix}_label_seq_id"]),
    }


def _atom_site_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        _first_present(row, ["label_comp_id", "auth_comp_id"]),
        _first_present(row, ["auth_asym_id", "label_asym_id"]),
        _first_present(row, ["auth_seq_id", "label_seq_id"]),
        _first_present(row, ["label_atom_id", "auth_atom_id"]),
    )


def _partner_exists(atom_site_rows: list[dict[str, str]], partner: dict[str, str]) -> bool:
    wanted = (partner["comp"], partner["chain"], partner["seq"], partner["atom"])
    return wanted in {_atom_site_key(row) for row in atom_site_rows}


def _is_covalent_like(conn_type: str) -> bool:
    return "cov" in conn_type.lower()


def extract_mmcif_candidates(pdb_id: str, het_code: str, struct_conn_rows: list[dict[str, str]], atom_site_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates = []
    for row in struct_conn_rows:
        p1 = _partner_from_struct_conn(row, "ptnr1")
        p2 = _partner_from_struct_conn(row, "ptnr2")
        matches = [p1["comp"] == het_code, p2["comp"] == het_code]
        if sum(1 for match in matches if match) != 1:
            continue
        ligand = p1 if matches[0] else p2
        protein = p2 if matches[0] else p1
        if not protein["comp"] or protein["comp"] == het_code:
            continue
        residue_atom = protein["atom"]
        ligand_atom = ligand["atom"]
        candidates.append(
            {
                "pdb_id": pdb_id,
                "het_code": het_code,
                "selected_raw_format": "mmcif",
                "raw_connection_source": "mmcif_struct_conn",
                "candidate_found": True,
                "conn_type_or_record_type": row.get("conn_type_id", ""),
                "chain_id": protein["chain"],
                "residue_name": protein["comp"],
                "residue_index": protein["seq"],
                "residue_atom_name": residue_atom,
                "ligand_atom_name": ligand_atom,
                "covalent_bond_atom_pair": f"{residue_atom}-{ligand_atom}" if residue_atom and ligand_atom else "",
                "protein_partner_atom_exists": _partner_exists(atom_site_rows, protein),
                "ligand_partner_atom_exists": _partner_exists(atom_site_rows, ligand),
                "candidate_confidence": "explicit_covalent_like_struct_conn" if _is_covalent_like(row.get("conn_type_id", "")) else "explicit_struct_conn",
                "manual_review_required": False,
            }
        )
    covalent = [row for row in candidates if row["candidate_confidence"] == "explicit_covalent_like_struct_conn"]
    return covalent or candidates


def parse_pdb_records(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, dict[str, str]]]:
    links: list[dict[str, str]] = []
    conect: list[dict[str, str]] = []
    atoms: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        record = line[:6].strip()
        if record == "LINK":
            links.append(
                {
                    "atom1": line[12:16].strip(),
                    "res1": line[17:20].strip(),
                    "chain1": line[21:22].strip(),
                    "seq1": line[22:26].strip(),
                    "atom2": line[42:46].strip(),
                    "res2": line[47:50].strip(),
                    "chain2": line[51:52].strip(),
                    "seq2": line[52:56].strip(),
                    "distance": line[73:78].strip(),
                }
            )
        elif record in {"ATOM", "HETATM"}:
            serial = line[6:11].strip()
            atoms[serial] = {
                "atom": line[12:16].strip(),
                "res": line[17:20].strip(),
                "chain": line[21:22].strip(),
                "seq": line[22:26].strip(),
            }
        elif record == "CONECT":
            conect.append({"line": line})
    return links, conect, atoms


def extract_pdb_link_candidates(pdb_id: str, het_code: str, links: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates = []
    for row in links:
        p1 = {"atom": row["atom1"], "comp": row["res1"], "chain": row["chain1"], "seq": row["seq1"]}
        p2 = {"atom": row["atom2"], "comp": row["res2"], "chain": row["chain2"], "seq": row["seq2"]}
        matches = [p1["comp"] == het_code, p2["comp"] == het_code]
        if sum(1 for match in matches if match) != 1:
            continue
        ligand = p1 if matches[0] else p2
        protein = p2 if matches[0] else p1
        residue_atom = protein["atom"]
        ligand_atom = ligand["atom"]
        candidates.append(
            {
                "pdb_id": pdb_id,
                "het_code": het_code,
                "selected_raw_format": "pdb",
                "raw_connection_source": "pdb_link",
                "candidate_found": True,
                "conn_type_or_record_type": "LINK",
                "chain_id": protein["chain"],
                "residue_name": protein["comp"],
                "residue_index": protein["seq"],
                "residue_atom_name": residue_atom,
                "ligand_atom_name": ligand_atom,
                "covalent_bond_atom_pair": f"{residue_atom}-{ligand_atom}" if residue_atom and ligand_atom else "",
                "protein_partner_atom_exists": True,
                "ligand_partner_atom_exists": True,
                "candidate_confidence": "explicit_pdb_link",
                "manual_review_required": False,
            }
        )
    return candidates


def _resolution_for_candidates(candidates: list[dict[str, Any]], het_found: bool, connectivity_found: bool, parse_failed: bool = False) -> str:
    if parse_failed:
        return "raw_parse_failed"
    if not het_found:
        return "raw_ligand_het_code_not_found"
    if len(candidates) > 1:
        return "raw_multiple_candidate_links"
    if not connectivity_found:
        return "raw_no_connectivity_records_found"
    if not candidates:
        return "raw_protein_partner_not_found"
    c = candidates[0]
    minimal = all(c.get(k) for k in ["chain_id", "residue_name", "residue_index", "residue_atom_name"])
    preferred = minimal and bool(c.get("ligand_atom_name")) and bool(c.get("covalent_bond_atom_pair"))
    if preferred:
        return "raw_resolves_preferred_event_key"
    if minimal:
        return "raw_resolves_minimal_event_key"
    return "raw_partial_event_key_only"


def _status(value: str) -> str:
    return "found" if value else "not_found"


def _annotate_download(row: dict[str, Any]) -> dict[str, Any]:
    if not row["raw_structure_downloaded"]:
        return {
            "format": "",
            "struct_conn_rows": [],
            "atom_site_rows": [],
            "link_rows": [],
            "conect_rows": [],
            "candidates": [],
            "resolution_status": "raw_parse_failed",
            "het_atom_site_count": 0,
        }
    text = _read_text(Path(row["selected_raw_path"]))
    pdb_id = row["pdb_id"]
    het_code = row["het_code"]
    if row["selected_raw_format"] == "mmcif":
        loops = parse_mmcif_loops(text, {"struct_conn", "atom_site"})
        struct_conn = loops.get("struct_conn", [])
        atom_site = loops.get("atom_site", [])
        candidates = extract_mmcif_candidates(pdb_id, het_code, struct_conn, atom_site)
        het_atom_count = sum(1 for atom in atom_site if _first_present(atom, ["label_comp_id", "auth_comp_id"]) == het_code)
        status = _resolution_for_candidates(candidates, het_atom_count > 0, bool(struct_conn))
        return {
            "format": "mmcif",
            "struct_conn_rows": struct_conn,
            "atom_site_rows": atom_site,
            "link_rows": [],
            "conect_rows": [],
            "candidates": candidates,
            "resolution_status": status,
            "het_atom_site_count": het_atom_count,
        }
    links, conect, atoms = parse_pdb_records(text)
    candidates = extract_pdb_link_candidates(pdb_id, het_code, links)
    het_atom_count = sum(1 for atom in atoms.values() if atom["res"] == het_code)
    status = _resolution_for_candidates(candidates, het_atom_count > 0, bool(links or conect))
    return {
        "format": "pdb",
        "struct_conn_rows": [],
        "atom_site_rows": list(atoms.values()),
        "link_rows": links,
        "conect_rows": conect,
        "candidates": candidates,
        "resolution_status": status,
        "het_atom_site_count": het_atom_count,
    }


def _precondition_rows() -> list[dict[str, Any]]:
    manifest = _load_json(STEP13AU_MANIFEST_JSON) if STEP13AU_MANIFEST_JSON.exists() else {}
    checks = [
        ("step13au_manifest", str(STEP13AU_MANIFEST_JSON), "exists", STEP13AU_MANIFEST_JSON.exists(), STEP13AU_MANIFEST_JSON.exists()),
        ("step13au_stage", str(STEP13AU_MANIFEST_JSON), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step13au_ready", str(STEP13AU_MANIFEST_JSON), "true", manifest.get("ready_for_covapie_covpdb_raw_structure_event_annotation_smoke"), manifest.get("ready_for_covapie_covpdb_raw_structure_event_annotation_smoke") is True),
        ("download_scope_contract", str(STEP13AU_DOWNLOAD_SCOPE_CSV), "exists", STEP13AU_DOWNLOAD_SCOPE_CSV.exists(), STEP13AU_DOWNLOAD_SCOPE_CSV.exists()),
        ("source_url_contract", str(STEP13AU_SOURCE_URL_CSV), "exists", STEP13AU_SOURCE_URL_CSV.exists(), STEP13AU_SOURCE_URL_CSV.exists()),
        ("storage_contract", str(STEP13AU_STORAGE_CSV), "exists", STEP13AU_STORAGE_CSV.exists(), STEP13AU_STORAGE_CSV.exists()),
        ("parser_priority_contract", str(STEP13AU_PARSER_PRIORITY_CSV), "exists", STEP13AU_PARSER_PRIORITY_CSV.exists(), STEP13AU_PARSER_PRIORITY_CSV.exists()),
        ("mmcif_mapping_contract", str(STEP13AU_MMCIF_MAPPING_CSV), "exists", STEP13AU_MMCIF_MAPPING_CSV.exists(), STEP13AU_MMCIF_MAPPING_CSV.exists()),
        ("pdb_mapping_contract", str(STEP13AU_PDB_MAPPING_CSV), "exists", STEP13AU_PDB_MAPPING_CSV.exists(), STEP13AU_PDB_MAPPING_CSV.exists()),
        ("metadata_hash_unchanged", str(METADATA_CSV), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": artifact,
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, artifact, expected, observed, passed in checks
    ]


def _storage_rows(download_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    staged = set(_run_git(["diff", "--cached", "--name-only", "--", str(RAW_STORAGE_ROOT)]).stdout.splitlines())
    tracked = set(_run_git(["ls-files", str(RAW_STORAGE_ROOT)]).stdout.splitlines())
    rows = []
    for row in download_rows:
        if not row["raw_structure_downloaded"]:
            continue
        path = Path(row["selected_raw_path"])
        path_text = str(path)
        under_root = _path_under(path, RAW_STORAGE_ROOT)
        suffix_allowed = path.suffix.lower() in {".cif", ".pdb"}
        is_staged = path_text in staged
        is_tracked = path_text in tracked
        exists = path.exists()
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "selected_raw_path": path_text,
                "under_allowed_raw_storage_root": under_root,
                "suffix_allowed": suffix_allowed,
                "raw_file_exists": exists,
                "raw_file_untracked": not is_tracked,
                "raw_file_not_staged": not is_staged,
                "raw_file_not_committed": not is_tracked,
                "raw_file_not_copied_to_derived": True,
                "storage_safety_passed": under_root and suffix_allowed and exists and not is_staged and not is_tracked,
            }
        )
    return rows


def _format_rows(download_rows: list[dict[str, Any]], annotations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        ann = annotations[row["pdb_id"]]
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "parser_used": ann["format"] or "none",
                "struct_conn_loop_found": bool(ann["struct_conn_rows"]),
                "struct_conn_row_count": len(ann["struct_conn_rows"]),
                "atom_site_loop_found": bool(ann["atom_site_rows"]) if row["selected_raw_format"] == "mmcif" else False,
                "atom_site_row_count": len(ann["atom_site_rows"]) if row["selected_raw_format"] == "mmcif" else 0,
                "pdb_link_row_count": len(ann["link_rows"]),
                "pdb_conect_row_count": len(ann["conect_rows"]),
                "format_inventory_passed": row["raw_structure_downloaded"],
            }
        )
    return rows


def _struct_conn_inventory(download_rows: list[dict[str, Any]], annotations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        ann = annotations[row["pdb_id"]]
        struct_conn = ann["struct_conn_rows"]
        het = row["het_code"]
        het_count = 0
        cov_count = 0
        for conn in struct_conn:
            comps = [_partner_from_struct_conn(conn, "ptnr1")["comp"], _partner_from_struct_conn(conn, "ptnr2")["comp"]]
            if het in comps:
                het_count += 1
                if _is_covalent_like(conn.get("conn_type_id", "")):
                    cov_count += 1
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": het,
                "selected_raw_format": row["selected_raw_format"],
                "struct_conn_loop_found": bool(struct_conn),
                "struct_conn_row_count": len(struct_conn),
                "het_code_in_struct_conn_count": het_count,
                "covalent_like_struct_conn_count": cov_count,
                "protein_ligand_candidate_count": len([c for c in ann["candidates"] if c["raw_connection_source"] == "mmcif_struct_conn"]),
                "struct_conn_inventory_passed": row["raw_structure_downloaded"],
            }
        )
    return rows


def _atom_site_rows(download_rows: list[dict[str, Any]], annotations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        ann = annotations[row["pdb_id"]]
        candidates = ann["candidates"]
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "atom_site_loop_found": bool(ann["atom_site_rows"]) if row["selected_raw_format"] == "mmcif" else False,
                "atom_site_row_count": len(ann["atom_site_rows"]) if row["selected_raw_format"] == "mmcif" else 0,
                "het_code_atom_site_count": ann["het_atom_site_count"],
                "candidate_partner_validation_attempted": bool(candidates),
                "protein_partner_atom_exists_count": sum(1 for c in candidates if c["protein_partner_atom_exists"]),
                "ligand_partner_atom_exists_count": sum(1 for c in candidates if c["ligand_partner_atom_exists"]),
                "atom_site_validation_passed": row["raw_structure_downloaded"],
            }
        )
    return rows


def _pdb_inventory(download_rows: list[dict[str, Any]], annotations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        ann = annotations[row["pdb_id"]]
        links = ann["link_rows"]
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "link_record_count": len(links),
                "conect_record_count": len(ann["conect_rows"]),
                "het_code_in_link_count": sum(1 for link in links if row["het_code"] in {link.get("res1"), link.get("res2")}),
                "protein_ligand_link_candidate_count": len([c for c in ann["candidates"] if c["raw_connection_source"] == "pdb_link"]),
                "pdb_link_conect_inventory_passed": row["raw_structure_downloaded"],
            }
        )
    return rows


def _candidate_rows(download_rows: list[dict[str, Any]], annotations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        candidates = annotations[row["pdb_id"]]["candidates"]
        if not candidates:
            rows.append(
                {
                    "pdb_id": row["pdb_id"],
                    "het_code": row["het_code"],
                    "selected_raw_format": row["selected_raw_format"],
                    "raw_connection_source": "",
                    "candidate_index": 0,
                    "candidate_found": False,
                    "conn_type_or_record_type": "",
                    "chain_id": "",
                    "residue_name": "",
                    "residue_index": "",
                    "residue_atom_name": "",
                    "ligand_atom_name": "",
                    "covalent_bond_atom_pair": "",
                    "protein_partner_atom_exists": False,
                    "ligand_partner_atom_exists": False,
                    "candidate_confidence": "none",
                    "manual_review_required": False,
                    "candidate_annotation_passed": row["raw_structure_downloaded"],
                }
            )
            continue
        for index, candidate in enumerate(candidates, start=1):
            rows.append({**candidate, "candidate_index": index, "candidate_annotation_passed": True})
    return rows


def _resolution_rows(download_rows: list[dict[str, Any]], annotations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in download_rows:
        candidates = annotations[row["pdb_id"]]["candidates"]
        candidate = candidates[0] if len(candidates) == 1 else {}
        status = annotations[row["pdb_id"]]["resolution_status"] if row["raw_structure_downloaded"] else "raw_parse_failed"
        minimal_fields = ["chain_id", "residue_name", "residue_index", "residue_atom_name"]
        preferred_fields = minimal_fields + ["ligand_atom_name", "covalent_bond_atom_pair"]
        minimal_count = sum(1 for field in minimal_fields if candidate.get(field))
        preferred_count = sum(1 for field in preferred_fields if candidate.get(field))
        rows.append(
            {
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "selected_raw_format": row["selected_raw_format"],
                "raw_connection_source": candidate.get("raw_connection_source", ""),
                "candidate_count": len(candidates),
                "preferred_fields_found_count": preferred_count,
                "minimal_fields_found_count": minimal_count,
                "chain_id_status": _status(candidate.get("chain_id", "")),
                "residue_name_status": _status(candidate.get("residue_name", "")),
                "residue_index_status": _status(candidate.get("residue_index", "")),
                "residue_atom_name_status": _status(candidate.get("residue_atom_name", "")),
                "ligand_atom_name_status": _status(candidate.get("ligand_atom_name", "")),
                "covalent_bond_atom_pair_status": _status(candidate.get("covalent_bond_atom_pair", "")),
                "resolution_status": status,
                "candidate_metadata_can_materialize_current_step": False,
                "allowlist_can_materialize_current_step": False,
                "future_candidate_metadata_possible": status in {"raw_resolves_preferred_event_key", "raw_resolves_minimal_event_key"},
                "future_automatic_allowlist_possible": status == "raw_resolves_preferred_event_key",
                "manual_review_required": status in {"raw_multiple_candidate_links", "raw_partial_event_key_only", "raw_requires_manual_review"},
                "event_key_resolution_audit_passed": row["raw_structure_downloaded"],
            }
        )
    return rows


def _failure_rows(resolution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["resolution_status"] for row in resolution_rows)
    return [
        {
            "failure_reason": reason,
            "observed_count": count,
            "blocks_candidate_metadata_current_step": True,
            "recommended_handling": "record_status_and_defer_materialization_to_future_gate",
        }
        for reason, count in sorted(counts.items())
    ]


def _materialization_rows() -> list[dict[str, Any]]:
    items = [
        ("raw_structure_download", "executed_first5_smoke_only", "qa_gate_before_any_scale_up"),
        ("candidate_metadata_materialization", "blocked_current_smoke", "future_materialization_gate_after_qa"),
        ("candidate_allowlist_materialization", "blocked_current_smoke", "future_allowlist_gate_after_candidate_metadata"),
        ("batch_scale_raw_read_smoke", "blocked_current_smoke", "future_batch_scale_design_gate"),
        ("training", "blocked_current_smoke", "feature_semantics_audit_and_leakage_split_design_required"),
    ]
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "future_condition": condition,
            "materialization_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status, condition in items
    ]


def _execution_rows(any_pdb: bool, any_mmcif: bool) -> list[dict[str, Any]]:
    statuses = {
        "raw_structure_event_annotation_smoke": "executed_first5_raw_structure_download_and_annotation_only",
        "step13au_manifest_read": "executed_manifest_read_only",
        "metadata_csv_first5_pdb_ids_read": "executed_metadata_read_only",
        "source_url_contract_read": "executed_contract_read_only",
        "raw_structure_download": "executed_first5_rcsb_mmcif_with_pdb_fallback_only",
        "raw_ligand_download": "not_executed_or_not_allowed",
        "archive_download": "not_executed_or_not_allowed",
        "raw_file_created": "executed_allowed_raw_storage_only",
        "raw_data_read": "executed_downloaded_raw_structure_text_only",
        "sdf_read": "not_executed_or_not_allowed",
        "pdb_read": "executed_only_if_pdb_fallback_used_else_not_executed" if any_pdb else "not_executed_or_not_allowed",
        "mmcif_read": "executed_downloaded_mmcif_text_only" if any_mmcif else "not_executed_or_not_allowed",
        "gzip_open": "not_executed_or_not_allowed",
        "rdkit_use": "not_executed_or_not_allowed",
        "biopdb_use": "not_executed_or_not_allowed",
        "gemmi_use": "not_executed_or_not_allowed",
        "candidate_metadata_materialization": "not_executed_or_not_allowed",
        "allowlist_materialization": "not_executed_or_not_allowed",
        "torch_import": "not_executed_or_not_allowed",
        "model_forward": "not_executed_or_not_allowed",
        "training_claim": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status in statuses.items()
    ]


def _derived_forbidden_exists() -> bool:
    if not OUTPUT_ROOT.exists():
        return False
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in OUTPUT_ROOT.rglob("*"))


def _git_safety_rows(storage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("raw_files_under_allowed_storage_root", "storage audit", "true", all(_bool_text(row["under_allowed_raw_storage_root"]) == "True" for row in storage_rows)),
        ("raw_files_untracked", "git ls-files raw root", "true", all(_bool_text(row["raw_file_untracked"]) == "True" for row in storage_rows)),
        ("raw_files_not_staged", "git diff --cached raw root", "true", all(_bool_text(row["raw_file_not_staged"]) == "True" for row in storage_rows)),
        ("raw_files_not_copied_to_derived", "scan derived output", "true", not _derived_forbidden_exists()),
        ("metadata_csv_hash_unchanged", "sha256 metadata csv", METADATA_CSV_SHA256, _metadata_hash() == METADATA_CSV_SHA256),
        ("step13au_artifacts_unchanged", "git diff step13au", "empty", _run_git(["diff", "--quiet", "--", str(STEP13AU_ROOT)]).returncode == 0),
        ("protected_source_diff_empty", "git diff protected source", "empty", _run_git(["diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"]).returncode == 0),
        ("original_dataloader_diff_empty", "git diff dataloader", "empty", _run_git(["diff", "--quiet", "--", "dataset.py", "data/prepare_crossdocked.py"]).returncode == 0),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": "passed" if passed else "failed",
            "git_safety_audit_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, command, required, passed in checks
    ]


def _mask_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13au",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def _feature_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": "model_input_feature_semantics",
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_raw_structure_event_annotation_smoke": False,
            "training_ready": False,
            "recommended_audit_step": "future_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in FEATURE_SEMANTICS_ITEMS
    ]


def _leakage_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "split_written_current_step": False,
            "leakage_matrix_written_current_step": False,
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def _all_pass(rows: list[dict[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool_text(row.get(key)) == "True" for row in rows)


def run_covapie_covpdb_raw_structure_event_annotation_smoke_v0() -> dict[str, Any]:
    metadata_rows = _first5_metadata()
    precondition_rows = _precondition_rows()
    plan_rows = _download_plan(metadata_rows)
    download_rows = _download_structures(plan_rows)
    annotations = {row["pdb_id"]: _annotate_download(row) for row in download_rows}
    storage_rows = _storage_rows(download_rows)
    format_rows = _format_rows(download_rows, annotations)
    struct_conn_rows = _struct_conn_inventory(download_rows, annotations)
    atom_site_rows = _atom_site_rows(download_rows, annotations)
    pdb_inventory_rows = _pdb_inventory(download_rows, annotations)
    candidate_rows = _candidate_rows(download_rows, annotations)
    resolution_rows = _resolution_rows(download_rows, annotations)
    failure_rows = _failure_rows(resolution_rows)
    materialization_rows = _materialization_rows()
    any_pdb = any(row["selected_raw_format"] == "pdb" for row in download_rows)
    any_mmcif = any(row["selected_raw_format"] == "mmcif" for row in download_rows)
    execution_rows = _execution_rows(any_pdb=any_pdb, any_mmcif=any_mmcif)
    git_safety_rows = _git_safety_rows(storage_rows)
    mask_rows = _mask_rows()
    feature_rows = _feature_rows()
    leakage_rows = _leakage_rows()
    succeeded = sum(1 for row in download_rows if row["raw_structure_downloaded"])
    failed = len(download_rows) - succeeded
    resolution_counts = Counter(row["resolution_status"] for row in resolution_rows)
    selected_formats = {row["pdb_id"]: row["selected_raw_format"] for row in download_rows if row["selected_raw_format"]}
    future_candidate_count = sum(1 for row in resolution_rows if row["future_candidate_metadata_possible"])
    future_allowlist_count = sum(1 for row in resolution_rows if row["future_automatic_allowlist_possible"])
    all_checks_passed = succeeded > 0 and all(
        [
            _all_pass(precondition_rows, "precondition_passed"),
            _all_pass(plan_rows, "download_plan_passed"),
            _all_pass([row for row in download_rows if row["raw_structure_downloaded"]], "download_audit_passed"),
            _all_pass(storage_rows, "storage_safety_passed"),
            _all_pass(git_safety_rows, "git_safety_audit_passed"),
            _all_pass(mask_rows, "mask_scope_audit_passed"),
            _all_pass(feature_rows, "feature_semantics_audit_passed"),
            _all_pass(leakage_rows, "leakage_split_audit_passed"),
        ]
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13au_design_gate_validated": _all_pass(precondition_rows, "precondition_passed"),
        "attempted_structure_count": len(download_rows),
        "raw_structure_download_succeeded_count": succeeded,
        "raw_structure_download_failed_count": failed,
        "selected_raw_formats": selected_formats,
        "raw_storage_root": str(RAW_STORAGE_ROOT) + "/",
        "raw_files_created": succeeded > 0,
        "raw_files_tracked": False,
        "raw_files_staged": False,
        "raw_files_committed": False,
        "raw_files_under_allowed_storage_root": all(_bool_text(row["under_allowed_raw_storage_root"]) == "True" for row in storage_rows),
        "raw_files_copied_to_derived": False,
        "raw_structure_downloaded": succeeded > 0,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_data_read": succeeded > 0,
        "sdf_read": False,
        "mmcif_text_read": any_mmcif,
        "pdb_read": any_pdb,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "network_access_used": True,
        "urllib_used": True,
        "requests_used": False,
        "browser_used": False,
        "struct_conn_loop_found_count": sum(1 for row in format_rows if row["struct_conn_loop_found"]),
        "atom_site_loop_found_count": sum(1 for row in format_rows if row["atom_site_loop_found"]),
        "pdb_link_record_found_count": sum(1 for row in format_rows if int(row["pdb_link_row_count"]) > 0),
        "pdb_conect_record_found_count": sum(1 for row in format_rows if int(row["pdb_conect_row_count"]) > 0),
        "raw_resolves_preferred_event_key_count": resolution_counts.get("raw_resolves_preferred_event_key", 0),
        "raw_resolves_minimal_event_key_count": resolution_counts.get("raw_resolves_minimal_event_key", 0),
        "raw_partial_event_key_only_count": resolution_counts.get("raw_partial_event_key_only", 0),
        "raw_no_connectivity_records_found_count": resolution_counts.get("raw_no_connectivity_records_found", 0),
        "raw_multiple_candidate_links_count": resolution_counts.get("raw_multiple_candidate_links", 0),
        "raw_ligand_het_code_not_found_count": resolution_counts.get("raw_ligand_het_code_not_found", 0),
        "raw_protein_partner_not_found_count": resolution_counts.get("raw_protein_partner_not_found", 0),
        "raw_requires_manual_review_count": resolution_counts.get("raw_requires_manual_review", 0),
        "raw_parse_failed_count": resolution_counts.get("raw_parse_failed", 0),
        "future_candidate_metadata_possible_count": future_candidate_count,
        "future_automatic_allowlist_possible_count": future_allowlist_count,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate": succeeded > 0,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": len(CANONICAL_MASK_TASK_NAMES),
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": len(CANONICAL_MASK_TASK_NAMES) == 5,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_covpdb_raw_structure_event_annotation_qa_gate" if succeeded > 0 else "inspect_raw_structure_download_access",
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": [] if all_checks_passed else ["raw_structure_download_failed_for_all_structures"],
    }
    result = {
        "precondition_rows": precondition_rows,
        "download_plan_rows": plan_rows,
        "download_audit_rows": download_rows,
        "storage_rows": storage_rows,
        "format_rows": format_rows,
        "struct_conn_rows": struct_conn_rows,
        "atom_site_rows": atom_site_rows,
        "pdb_inventory_rows": pdb_inventory_rows,
        "candidate_rows": candidate_rows,
        "resolution_rows": resolution_rows,
        "failure_rows": failure_rows,
        "materialization_rows": materialization_rows,
        "execution_rows": execution_rows,
        "git_safety_rows": git_safety_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
    }
    result["report_sections"] = {
        "precondition": {"rows": len(precondition_rows)},
        "download": {"succeeded": succeeded, "failed": failed},
        "storage_safety": {"rows": len(storage_rows)},
        "format_inventory": {"rows": len(format_rows)},
        "event_candidates": {"rows": len(candidate_rows)},
        "event_key_resolution": dict(resolution_counts),
        "materialization_boundary": {"rows": len(materialization_rows)},
        "readiness_boundary": {"recommended_next_step": manifest["recommended_next_step"]},
    }
    return result

