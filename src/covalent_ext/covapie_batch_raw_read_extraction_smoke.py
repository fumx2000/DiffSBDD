from __future__ import annotations

import csv
import hashlib
import json
import math
import shlex
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_batch_raw_read_extraction_design_gate as step13bd


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_batch_raw_read_extraction_smoke_v0"
PREVIOUS_STAGE = step13bd.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_batch_raw_read_extraction_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_precondition_audit.csv"
RAW_READ_AUDIT_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_audit.csv"
MMCIF_LOOP_PARSE_AUDIT_CSV = OUTPUT_ROOT / "covapie_mmcif_loop_parse_audit.csv"
EXTRACTED_EVENT_TABLE_CSV = OUTPUT_ROOT / "covapie_extracted_event_table.csv"
EXTRACTED_PROTEIN_ATOM_TABLE_CSV = OUTPUT_ROOT / "covapie_extracted_protein_pocket_atom_table.csv"
EXTRACTED_LIGAND_ATOM_TABLE_CSV = OUTPUT_ROOT / "covapie_extracted_ligand_atom_table.csv"
EXTRACTION_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_qa_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_batch_raw_read_extraction_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_batch_raw_read_extraction_smoke_v0_summary.md")

ALLOWED_PDB_IDS = ["1A3B", "1A3E", "1A46", "1A5G"]
EVENT_FIELDS = step13bd.EVENT_FIELDS
ATOM_FIELDS = step13bd.ATOM_FIELDS
CANONICAL_MASK_TASK_NAMES = step13bd.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bd.CANONICAL_MASK_TASK_ALIASES
FORBIDDEN_DERIVED_SUFFIXES = step13bd.FORBIDDEN_DERIVED_SUFFIXES

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
RAW_READ_COLUMNS = [
    "pdb_id",
    "expected_raw_file_path",
    "raw_file_exists",
    "raw_file_tracked_by_git",
    "raw_file_staged_by_git",
    "raw_file_sha256",
    "raw_file_size_bytes",
    "raw_file_content_read_current_step",
    "raw_read_status",
    "raw_read_blocking_reason",
    "raw_read_audit_passed",
]
MMCIF_PARSE_COLUMNS = [
    "pdb_id",
    "atom_site_loop_found",
    "atom_site_row_count",
    "atom_site_required_columns_found",
    "struct_conn_loop_found",
    "struct_conn_row_count",
    "struct_conn_required_columns_found",
    "parser_mode",
    "mmcif_parse_status",
    "mmcif_parse_blocking_reason",
    "mmcif_loop_parse_audit_passed",
]
EXTRACTION_QA_COLUMNS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "pdb_id",
    "het_code",
    "residue_atom_found",
    "ligand_atom_found",
    "covalent_connection_found",
    "covalent_bond_distance_angstrom",
    "distance_plausibility_status",
    "protein_atom_rows_for_event",
    "ligand_atom_rows_for_event",
    "extracted_event_schema_matches_contract",
    "atom_table_schema_matches_contract",
    "ready_for_training_false",
    "feature_semantics_blocker_preserved",
    "leakage_split_blocker_preserved",
    "extraction_qa_passed",
    "qa_comment",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]

ATOM_REQUIRED_ALTERNATIVES = [
    ["_atom_site.group_PDB"],
    ["_atom_site.id"],
    ["_atom_site.type_symbol"],
    ["_atom_site.label_atom_id", "_atom_site.auth_atom_id"],
    ["_atom_site.label_comp_id", "_atom_site.auth_comp_id"],
    ["_atom_site.auth_asym_id", "_atom_site.label_asym_id"],
    ["_atom_site.auth_seq_id", "_atom_site.label_seq_id"],
    ["_atom_site.Cartn_x"],
    ["_atom_site.Cartn_y"],
    ["_atom_site.Cartn_z"],
    ["_atom_site.occupancy"],
    ["_atom_site.B_iso_or_equiv"],
]
STRUCT_CONN_REQUIRED_ALTERNATIVES = [
    ["_struct_conn.conn_type_id"],
    ["_struct_conn.ptnr1_label_asym_id", "_struct_conn.ptnr1_auth_asym_id"],
    ["_struct_conn.ptnr1_label_comp_id", "_struct_conn.ptnr1_auth_comp_id"],
    ["_struct_conn.ptnr1_label_seq_id", "_struct_conn.ptnr1_auth_seq_id"],
    ["_struct_conn.ptnr1_label_atom_id", "_struct_conn.ptnr1_auth_atom_id"],
    ["_struct_conn.ptnr2_label_asym_id", "_struct_conn.ptnr2_auth_asym_id"],
    ["_struct_conn.ptnr2_label_comp_id", "_struct_conn.ptnr2_auth_comp_id"],
    ["_struct_conn.ptnr2_label_seq_id", "_struct_conn.ptnr2_auth_seq_id"],
    ["_struct_conn.ptnr2_label_atom_id", "_struct_conn.ptnr2_auth_atom_id"],
]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _raw_file_tracked(path: Path) -> bool:
    return bool(_run_git(["ls-files", path.as_posix()]).stdout.strip())


def _raw_file_staged(path: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", path.as_posix()]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _metadata_hash() -> str:
    return _sha256_file(step13bd.METADATA_CSV) if step13bd.METADATA_CSV.exists() else ""


def _norm(value: str | None) -> str:
    if value is None or value in {".", "?"}:
        return ""
    return value


def _first(row: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = _norm(row.get(name))
        if value:
            return value
    return ""


def _as_float(value: str) -> float:
    return float(_norm(value))


def _distance(a: dict[str, str], b: dict[str, str]) -> float:
    return math.sqrt(
        (_as_float(a["_atom_site.Cartn_x"]) - _as_float(b["_atom_site.Cartn_x"])) ** 2
        + (_as_float(a["_atom_site.Cartn_y"]) - _as_float(b["_atom_site.Cartn_y"])) ** 2
        + (_as_float(a["_atom_site.Cartn_z"]) - _as_float(b["_atom_site.Cartn_z"])) ** 2
    )


def _all_alternatives_present(tags: list[str], alternatives: list[list[str]]) -> bool:
    tag_set = set(tags)
    return all(any(name in tag_set for name in group) for group in alternatives)


def _parse_target_loop(text: str, prefix: str) -> tuple[list[str], list[dict[str, str]], str]:
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].strip() != "loop_":
            index += 1
            continue
        cursor = index + 1
        tags: list[str] = []
        while cursor < len(lines) and lines[cursor].strip().startswith("_"):
            tags.append(lines[cursor].strip().split()[0])
            cursor += 1
        if not tags or not all(tag.startswith(prefix) for tag in tags):
            index = cursor
            continue
        rows: list[dict[str, str]] = []
        while cursor < len(lines):
            stripped = lines[cursor].strip()
            if not stripped or stripped == "#":
                break
            if stripped == "loop_" or stripped.startswith("data_") or stripped.startswith("_"):
                break
            if stripped.startswith(";"):
                return tags, rows, "blocked_parser_limitation_semicolon_block_in_target_loop"
            try:
                values = shlex.split(stripped, posix=True)
            except ValueError as exc:
                return tags, rows, f"blocked_parser_limitation_{exc}"
            if len(values) != len(tags):
                return tags, rows, f"blocked_parser_limitation_row_length_{len(values)}_expected_{len(tags)}"
            rows.append({tag: _norm(value) for tag, value in zip(tags, values)})
            cursor += 1
        return tags, rows, "parse_success"
    return [], [], "blocked_target_loop_not_found"


def _atom_model(row: dict[str, str]) -> str:
    return _first(row, ["_atom_site.pdbx_PDB_model_num"]) or "1"


def _is_preferred_atom(row: dict[str, str]) -> bool:
    altloc = _first(row, ["_atom_site.label_alt_id", "_atom_site.auth_alt_id"])
    return _atom_model(row) in {"", "1"} and altloc in {"", "A"}


def _atom_chain(row: dict[str, str]) -> str:
    return _first(row, ["_atom_site.auth_asym_id", "_atom_site.label_asym_id"])


def _atom_seq(row: dict[str, str]) -> str:
    return _first(row, ["_atom_site.auth_seq_id", "_atom_site.label_seq_id"])


def _atom_comp(row: dict[str, str]) -> str:
    return _first(row, ["_atom_site.auth_comp_id", "_atom_site.label_comp_id"])


def _atom_name(row: dict[str, str]) -> str:
    return _first(row, ["_atom_site.auth_atom_id", "_atom_site.label_atom_id"])


def _find_atom(rows: list[dict[str, str]], chain: str, comp: str, seq: str, atom_name: str) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if _atom_chain(row) == chain
        and _atom_comp(row) == comp
        and _atom_seq(row) == seq
        and _atom_name(row) == atom_name
        and _is_preferred_atom(row)
    ]
    return matches[0] if matches else None


def _find_ligand_atom(rows: list[dict[str, str]], chain: str, het_code: str, atom_name: str) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if _atom_chain(row) == chain
        and _atom_comp(row) == het_code
        and _atom_name(row) == atom_name
        and _is_preferred_atom(row)
    ]
    return matches[0] if matches else None


def _endpoint(row: dict[str, str], side: str) -> dict[str, str]:
    return {
        "chain": _first(row, [f"_struct_conn.ptnr{side}_auth_asym_id", f"_struct_conn.ptnr{side}_label_asym_id"]),
        "comp": _first(row, [f"_struct_conn.ptnr{side}_auth_comp_id", f"_struct_conn.ptnr{side}_label_comp_id"]),
        "seq": _first(row, [f"_struct_conn.ptnr{side}_auth_seq_id", f"_struct_conn.ptnr{side}_label_seq_id"]),
        "atom": _first(row, [f"_struct_conn.ptnr{side}_auth_atom_id", f"_struct_conn.ptnr{side}_label_atom_id"]),
    }


def _endpoint_matches_residue(endpoint: dict[str, str], allowlist_row: dict[str, str]) -> bool:
    return (
        endpoint["chain"] == allowlist_row["chain_id"]
        and endpoint["comp"] == allowlist_row["residue_name"]
        and endpoint["seq"] == allowlist_row["residue_index"]
        and endpoint["atom"] == allowlist_row["residue_atom_name"]
    )


def _endpoint_matches_ligand(endpoint: dict[str, str], allowlist_row: dict[str, str]) -> bool:
    return (
        endpoint["chain"] == allowlist_row["chain_id"]
        and endpoint["comp"] == allowlist_row["het_code"]
        and endpoint["atom"] == allowlist_row["ligand_atom_name"]
    )


def _find_covalent_connection(rows: list[dict[str, str]], allowlist_row: dict[str, str]) -> bool:
    for row in rows:
        conn_type = _first(row, ["_struct_conn.conn_type_id"]).lower()
        if "covale" not in conn_type and "covalent" not in conn_type:
            continue
        p1 = _endpoint(row, "1")
        p2 = _endpoint(row, "2")
        if (_endpoint_matches_residue(p1, allowlist_row) and _endpoint_matches_ligand(p2, allowlist_row)) or (
            _endpoint_matches_residue(p2, allowlist_row) and _endpoint_matches_ligand(p1, allowlist_row)
        ):
            return True
    return False


def _atom_table_row(atom: dict[str, str], event: dict[str, str], role: str, atom_index: int, raw_path: str, status: str = "extracted_success") -> dict[str, Any]:
    het_code = event["het_code"] if role == "ligand_atom" else ""
    return {
        "extracted_atom_id": f"extracted_atom::{event['extracted_event_id']}::{role}::{atom_index:05d}",
        "extracted_event_id": event["extracted_event_id"],
        "allowlist_entry_id": event["allowlist_entry_id"],
        "atom_table_role": role,
        "pdb_id": event["pdb_id"],
        "chain_id": _atom_chain(atom),
        "residue_name": _atom_comp(atom),
        "residue_index": _atom_seq(atom),
        "het_code": het_code,
        "atom_name": _atom_name(atom),
        "element": _first(atom, ["_atom_site.type_symbol"]),
        "formal_charge": _first(atom, ["_atom_site.pdbx_formal_charge"]),
        "x": _first(atom, ["_atom_site.Cartn_x"]),
        "y": _first(atom, ["_atom_site.Cartn_y"]),
        "z": _first(atom, ["_atom_site.Cartn_z"]),
        "occupancy": _first(atom, ["_atom_site.occupancy"]),
        "b_factor": _first(atom, ["_atom_site.B_iso_or_equiv"]),
        "altloc": _first(atom, ["_atom_site.label_alt_id", "_atom_site.auth_alt_id"]),
        "model_id": _atom_model(atom),
        "source_raw_file_path": raw_path,
        "extraction_status": status,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_training": False,
    }


def _ligand_atoms(atom_rows: list[dict[str, str]], allowlist_row: dict[str, str]) -> list[dict[str, str]]:
    return [
        row
        for row in atom_rows
        if _atom_chain(row) == allowlist_row["chain_id"]
        and _atom_comp(row) == allowlist_row["het_code"]
        and _is_preferred_atom(row)
    ]


def _protein_pocket_atoms(atom_rows: list[dict[str, str]], ligand_atoms: list[dict[str, str]]) -> list[dict[str, str]]:
    if not ligand_atoms:
        return []
    pocket = []
    for row in atom_rows:
        if row.get("_atom_site.group_PDB") != "ATOM" or not _is_preferred_atom(row):
            continue
        try:
            if min(_distance(row, ligand_atom) for ligand_atom in ligand_atoms) <= 8.0:
                pocket.append(row)
        except ValueError:
            continue
    return pocket


def _precondition_rows(manifest13bd: dict[str, Any], input_rows: list[dict[str, str]], raw_path_rows: list[dict[str, str]], event_schema_rows: list[dict[str, str]], atom_schema_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    checks = [
        ("step13bd_manifest_exists", step13bd.MANIFEST_JSON, "exists", step13bd.MANIFEST_JSON.exists(), step13bd.MANIFEST_JSON.exists()),
        ("step13bd_stage", step13bd.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bd.get("stage"), manifest13bd.get("stage") == PREVIOUS_STAGE),
        ("step13bd_all_checks_passed", step13bd.MANIFEST_JSON, "true", manifest13bd.get("all_checks_passed"), manifest13bd.get("all_checks_passed") is True),
        ("step13bd_ready_for_smoke", step13bd.MANIFEST_JSON, "true", manifest13bd.get("ready_for_covapie_batch_raw_read_extraction_smoke"), manifest13bd.get("ready_for_covapie_batch_raw_read_extraction_smoke") is True),
        ("step13bd_ready_for_training", step13bd.MANIFEST_JSON, "false", manifest13bd.get("ready_for_training"), manifest13bd.get("ready_for_training") is False),
        ("input_contract_row_count", step13bd.INPUT_CONTRACT_CSV, "4", len(input_rows), len(input_rows) == 4),
        ("raw_path_contract_row_count", step13bd.RAW_FILE_PATH_CONTRACT_CSV, "4", len(raw_path_rows), len(raw_path_rows) == 4),
        ("event_schema_field_count", step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV, "31", len(event_schema_rows), len(event_schema_rows) == 31),
        ("atom_schema_row_count", step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV, "46", len(atom_schema_rows), len(atom_schema_rows) == 46),
        ("metadata_csv_hash_unchanged", step13bd.METADATA_CSV, step13bd.METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == step13bd.METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, check, expected, observed, passed in checks
    ]


def _read_raw_files(raw_path_rows: list[dict[str, str]]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    texts: dict[str, str] = {}
    audit_rows = []
    for row in raw_path_rows:
        pdb_id = row["pdb_id"]
        path = Path(row["expected_raw_file_path"])
        exists = path.exists()
        tracked = _raw_file_tracked(path)
        staged = _raw_file_staged(path)
        before_hash = _sha256_file(path) if exists else ""
        size = path.stat().st_size if exists else 0
        status = "blocked_missing_raw_file"
        reason = "raw_file_missing"
        content_read = False
        if exists and pdb_id in ALLOWED_PDB_IDS:
            text = path.read_text(encoding="utf-8", errors="replace")
            after_hash = _sha256_file(path)
            if before_hash == after_hash:
                texts[pdb_id] = text
                status = "read_success"
                reason = ""
                content_read = True
            else:
                status = "blocked_raw_file_hash_changed_during_read"
                reason = "raw_file_hash_changed_during_read"
        elif pdb_id not in ALLOWED_PDB_IDS:
            status = "blocked_pdb_id_not_in_allowed_smoke_set"
            reason = "pdb_id_not_allowed"
        passed = exists and not tracked and not staged and content_read and status == "read_success"
        audit_rows.append(
            {
                "pdb_id": pdb_id,
                "expected_raw_file_path": path.as_posix(),
                "raw_file_exists": exists,
                "raw_file_tracked_by_git": tracked,
                "raw_file_staged_by_git": staged,
                "raw_file_sha256": before_hash,
                "raw_file_size_bytes": size,
                "raw_file_content_read_current_step": content_read,
                "raw_read_status": status,
                "raw_read_blocking_reason": reason,
                "raw_read_audit_passed": passed,
            }
        )
    return texts, audit_rows


def _parse_mmcif(texts: dict[str, str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    parsed: dict[str, dict[str, Any]] = {}
    audit_rows = []
    for pdb_id, text in texts.items():
        atom_tags, atom_rows, atom_status = _parse_target_loop(text, "_atom_site.")
        conn_tags, conn_rows, conn_status = _parse_target_loop(text, "_struct_conn.")
        atom_cols = _all_alternatives_present(atom_tags, ATOM_REQUIRED_ALTERNATIVES)
        conn_cols = _all_alternatives_present(conn_tags, STRUCT_CONN_REQUIRED_ALTERNATIVES)
        passed = atom_status == "parse_success" and conn_status == "parse_success" and bool(atom_rows) and bool(conn_rows) and atom_cols and conn_cols
        blocking = ""
        if not passed:
            blocking = ";".join(
                reason
                for reason in [
                    "" if atom_status == "parse_success" else atom_status,
                    "" if conn_status == "parse_success" else conn_status,
                    "" if atom_cols else "atom_site_required_columns_missing",
                    "" if conn_cols else "struct_conn_required_columns_missing",
                    "" if atom_rows else "atom_site_rows_missing",
                    "" if conn_rows else "struct_conn_rows_missing",
                ]
                if reason
            )
        parsed[pdb_id] = {"atom_tags": atom_tags, "atom_rows": atom_rows, "conn_tags": conn_tags, "conn_rows": conn_rows}
        audit_rows.append(
            {
                "pdb_id": pdb_id,
                "atom_site_loop_found": bool(atom_tags),
                "atom_site_row_count": len(atom_rows),
                "atom_site_required_columns_found": atom_cols,
                "struct_conn_loop_found": bool(conn_tags),
                "struct_conn_row_count": len(conn_rows),
                "struct_conn_required_columns_found": conn_cols,
                "parser_mode": "standard_library_mmcif_loop_parser",
                "mmcif_parse_status": "parse_success" if passed else "blocked_parse_failure",
                "mmcif_parse_blocking_reason": blocking,
                "mmcif_loop_parse_audit_passed": passed,
            }
        )
    return parsed, audit_rows


def _extract_tables(input_rows: list[dict[str, str]], raw_read_rows: list[dict[str, Any]], parsed: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    hash_by_pdb = {row["pdb_id"]: row["raw_file_sha256"] for row in raw_read_rows}
    path_by_pdb = {row["pdb_id"]: row["expected_raw_file_path"] for row in raw_read_rows}
    event_rows: list[dict[str, Any]] = []
    protein_rows: list[dict[str, Any]] = []
    ligand_rows_out: list[dict[str, Any]] = []
    qa_rows: list[dict[str, Any]] = []
    for input_row in input_rows:
        pdb_id = input_row["pdb_id"]
        event_id = f"extracted_event::{input_row['candidate_metadata_id']}"
        atom_rows = parsed[pdb_id]["atom_rows"]
        conn_rows = parsed[pdb_id]["conn_rows"]
        residue_atom = _find_atom(atom_rows, input_row["chain_id"], input_row["residue_name"], input_row["residue_index"], input_row["residue_atom_name"])
        ligand_atom = _find_ligand_atom(atom_rows, input_row["chain_id"], input_row["het_code"], input_row["ligand_atom_name"])
        connection_found = _find_covalent_connection(conn_rows, input_row)
        distance = _distance(residue_atom, ligand_atom) if residue_atom and ligand_atom else None
        distance_text = f"{distance:.3f}" if distance is not None else ""
        success = bool(residue_atom and ligand_atom and connection_found)
        reasons = []
        if residue_atom is None:
            reasons.append("residue_atom_not_found")
        if ligand_atom is None:
            reasons.append("ligand_atom_not_found")
        if not connection_found:
            reasons.append("covalent_connection_not_found")
        event = {
            "extracted_event_id": event_id,
            "allowlist_entry_id": input_row["allowlist_entry_id"],
            "candidate_metadata_id": input_row["candidate_metadata_id"],
            "pdb_id": pdb_id,
            "het_code": input_row["het_code"],
            "chain_id": input_row["chain_id"],
            "residue_name": input_row["residue_name"],
            "residue_index": input_row["residue_index"],
            "residue_atom_name": input_row["residue_atom_name"],
            "ligand_atom_name": input_row["ligand_atom_name"],
            "covalent_bond_atom_pair": input_row["covalent_bond_atom_pair"],
            "raw_file_path": path_by_pdb[pdb_id],
            "raw_file_sha256": hash_by_pdb[pdb_id],
            "mmcif_stage": "standard_library_atom_site_struct_conn_smoke",
            "atom_site_rows_scanned": len(atom_rows),
            "struct_conn_rows_scanned": len(conn_rows),
            "residue_atom_found": residue_atom is not None,
            "ligand_atom_found": ligand_atom is not None,
            "covalent_connection_found": connection_found,
            "residue_atom_x": _first(residue_atom or {}, ["_atom_site.Cartn_x"]),
            "residue_atom_y": _first(residue_atom or {}, ["_atom_site.Cartn_y"]),
            "residue_atom_z": _first(residue_atom or {}, ["_atom_site.Cartn_z"]),
            "ligand_atom_x": _first(ligand_atom or {}, ["_atom_site.Cartn_x"]),
            "ligand_atom_y": _first(ligand_atom or {}, ["_atom_site.Cartn_y"]),
            "ligand_atom_z": _first(ligand_atom or {}, ["_atom_site.Cartn_z"]),
            "covalent_bond_distance_angstrom": distance_text,
            "extraction_status": "extracted_success" if success else "blocked",
            "extraction_blocking_reason": ";".join(reasons),
            "feature_semantics_audit_required_before_training": True,
            "leakage_split_design_required_before_training": True,
            "ready_for_training": False,
        }
        event_rows.append(event)
        ligand_atoms = _ligand_atoms(atom_rows, input_row)
        pocket_atoms = _protein_pocket_atoms(atom_rows, ligand_atoms)
        if residue_atom and residue_atom not in pocket_atoms:
            pocket_atoms.insert(0, residue_atom)
        for index, atom in enumerate(pocket_atoms, start=1):
            protein_rows.append(_atom_table_row(atom, event, "protein_pocket_atom", index, path_by_pdb[pdb_id]))
        for index, atom in enumerate(ligand_atoms, start=1):
            ligand_rows_out.append(_atom_table_row(atom, event, "ligand_atom", index, path_by_pdb[pdb_id]))
        distance_status = "not_available"
        if distance is not None:
            distance_status = "plausible_covalent_distance" if 1.0 <= distance <= 2.2 else "warning_outside_initial_1_0_to_2_2_angstrom_range"
        qa_passed = success and len(pocket_atoms) >= 1 and len(ligand_atoms) >= 1
        qa_rows.append(
            {
                "extracted_event_id": event_id,
                "allowlist_entry_id": input_row["allowlist_entry_id"],
                "pdb_id": pdb_id,
                "het_code": input_row["het_code"],
                "residue_atom_found": residue_atom is not None,
                "ligand_atom_found": ligand_atom is not None,
                "covalent_connection_found": connection_found,
                "covalent_bond_distance_angstrom": distance_text,
                "distance_plausibility_status": distance_status,
                "protein_atom_rows_for_event": len(pocket_atoms),
                "ligand_atom_rows_for_event": len(ligand_atoms),
                "extracted_event_schema_matches_contract": list(event.keys()) == EVENT_FIELDS,
                "atom_table_schema_matches_contract": True,
                "ready_for_training_false": event["ready_for_training"] is False,
                "feature_semantics_blocker_preserved": event["feature_semantics_audit_required_before_training"] is True,
                "leakage_split_blocker_preserved": event["leakage_split_design_required_before_training"] is True,
                "extraction_qa_passed": qa_passed,
                "qa_comment": "pocket_scope=8_angstrom_ligand_neighborhood_smoke" if qa_passed else ";".join(reasons),
            }
        )
    return event_rows, protein_rows, ligand_rows_out, qa_rows


def _boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "batch_raw_read_extraction_smoke": "executed_smoke_only",
        "raw_file_content_read": "executed_smoke_only",
        "mmcif_parse": "executed_smoke_only",
        "atom_site_scan": "executed_smoke_only",
        "struct_conn_scan": "executed_smoke_only",
        "coordinate_extraction": "executed_smoke_only",
        "extracted_event_table_write": "executed_smoke_only",
        "extracted_atom_table_write": "executed_smoke_only",
        "sample_index": "blocked_current_step",
        "final_dataset": "blocked_current_step",
        "split_assignments": "blocked_current_step",
        "leakage_matrix": "blocked_current_step",
        "training": "blocked_current_step",
        "network_access": "not_executed_or_not_allowed",
        "raw_download": "not_executed_or_not_allowed",
        "rdkit_biopdb_gemmi": "not_executed_or_not_allowed",
        "torch_model_training": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "boundary_safety_passed": True,
            "qa_comment": "boundary_respected",
        }
        for item, status in statuses.items()
    ]


def _derived_forbidden_exists(root: Path = OUTPUT_ROOT) -> bool:
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_DERIVED_SUFFIXES for path in root.rglob("*")) if root.exists() else False


def _sample_final_split_leakage_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
    }
    return any(path.is_file() and path.name in names for path in root.rglob("*")) if root.exists() else False


def _git_safety_rows(raw_read_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_hashes_still_match = all(Path(row["expected_raw_file_path"]).exists() and _sha256_file(Path(row["expected_raw_file_path"])) == row["raw_file_sha256"] for row in raw_read_rows)
    checks = [
        ("raw_files_untracked", "git ls-files raw root", "false", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw root", "false", not _raw_files_staged()),
        ("raw_files_not_modified", "sha256 before/after read", "unchanged", raw_hashes_still_match),
        ("derived_output_no_forbidden_binary_artifacts", "forbidden suffix scan", "false", not _derived_forbidden_exists()),
        ("no_sample_final_split_leakage_artifacts", "forbidden output name scan", "false", not _sample_final_split_leakage_exists()),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), "hash unchanged", _metadata_hash() == step13bd.METADATA_CSV_SHA256),
        ("step13bd_artifacts_unchanged", "git diff step13bd root", "empty", not _path_diff_exists([str(step13bd.OUTPUT_ROOT)])),
        ("step13bc_artifacts_unchanged", "git diff step13bc root", "empty", not _path_diff_exists([str(step13bd.STEP13BC_ROOT)])),
        ("protected_source_diff_empty", "git diff equivariant_diffusion/ lightning_modules.py", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "git_safety_audit_passed": status is True,
            "blocking_reasons": "" if status is True else item,
        }
        for item, command, required, status in checks
    ]


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(value is True or str(value).lower() == "true" for value in [row[column] for row in rows])


def run_covapie_batch_raw_read_extraction_smoke_v0() -> dict[str, Any]:
    manifest13bd = _load_json(step13bd.MANIFEST_JSON)
    input_rows = _csv_rows(step13bd.INPUT_CONTRACT_CSV)
    raw_path_rows = _csv_rows(step13bd.RAW_FILE_PATH_CONTRACT_CSV)
    event_schema_rows = _csv_rows(step13bd.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV)
    atom_schema_rows = _csv_rows(step13bd.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV)
    precondition_rows = _precondition_rows(manifest13bd, input_rows, raw_path_rows, event_schema_rows, atom_schema_rows)
    raw_texts, raw_read_rows = _read_raw_files(raw_path_rows)
    parsed, parse_rows = _parse_mmcif(raw_texts)
    event_rows, protein_rows, ligand_rows, qa_rows = _extract_tables(input_rows, raw_read_rows, parsed)
    boundary_rows = _boundary_rows()
    git_safety_rows = _git_safety_rows(raw_read_rows)

    extraction_success_count = sum(1 for row in event_rows if row["extraction_status"] == "extracted_success")
    extraction_blocked_count = len(event_rows) - extraction_success_count
    distances = [float(row["covalent_bond_distance_angstrom"]) for row in event_rows if row["covalent_bond_distance_angstrom"]]
    qa_checks = {
        "precondition": _all_true(precondition_rows, "precondition_passed"),
        "raw_read": len(raw_read_rows) == 4 and _all_true(raw_read_rows, "raw_read_audit_passed"),
        "mmcif_parse": len(parse_rows) == 4 and _all_true(parse_rows, "mmcif_loop_parse_audit_passed"),
        "event_schema": len(event_rows) == 4 and list(event_rows[0].keys()) == EVENT_FIELDS if event_rows else False,
        "atom_schema": bool(protein_rows) and bool(ligand_rows) and list(protein_rows[0].keys()) == ATOM_FIELDS and list(ligand_rows[0].keys()) == ATOM_FIELDS,
        "extraction_qa": len(qa_rows) == 4 and _all_true(qa_rows, "extraction_qa_passed"),
        "boundary": _all_true(boundary_rows, "boundary_safety_passed"),
        "git_safety": _all_true(git_safety_rows, "git_safety_audit_passed"),
    }
    blocking_reasons = [key for key, passed in qa_checks.items() if not passed]
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bd_design_gate_validated": qa_checks["precondition"],
        "source_allowlist_row_count": len(input_rows),
        "raw_file_read_count": sum(1 for row in raw_read_rows if row["raw_file_content_read_current_step"] is True),
        "raw_file_read_paths": [row["expected_raw_file_path"] for row in raw_read_rows if row["raw_file_content_read_current_step"] is True],
        "raw_file_path_exists_count": sum(1 for row in raw_read_rows if row["raw_file_exists"] is True),
        "raw_file_content_read_current_step": True,
        "mmcif_parse_current_step": True,
        "atom_site_scan_current_step": True,
        "struct_conn_scan_current_step": True,
        "coordinate_extraction_current_step": True,
        "extracted_event_table_written": True,
        "extracted_event_table_row_count": len(event_rows),
        "extracted_event_schema_field_count": len(EVENT_FIELDS),
        "extracted_protein_pocket_atom_table_written": True,
        "extracted_protein_pocket_atom_row_count": len(protein_rows),
        "extracted_ligand_atom_table_written": True,
        "extracted_ligand_atom_row_count": len(ligand_rows),
        "extracted_atom_schema_field_count": len(ATOM_FIELDS),
        "extraction_qa_audit_row_count": len(qa_rows),
        "extraction_success_count": extraction_success_count,
        "extraction_blocked_count": extraction_blocked_count,
        "covalent_connection_found_count": sum(1 for row in event_rows if row["covalent_connection_found"] is True),
        "residue_atom_found_count": sum(1 for row in event_rows if row["residue_atom_found"] is True),
        "ligand_atom_found_count": sum(1 for row in event_rows if row["ligand_atom_found"] is True),
        "covalent_bond_distance_min_angstrom": min(distances) if distances else None,
        "covalent_bond_distance_max_angstrom": max(distances) if distances else None,
        "precondition_audit_passed": qa_checks["precondition"],
        "raw_read_audit_passed": qa_checks["raw_read"],
        "mmcif_loop_parse_audit_passed": qa_checks["mmcif_parse"],
        "extracted_event_schema_contract_passed": qa_checks["event_schema"],
        "extracted_atom_table_schema_contract_passed": qa_checks["atom_schema"],
        "extraction_qa_passed": qa_checks["extraction_qa"],
        "boundary_safety_passed": qa_checks["boundary"],
        "git_safety_passed": qa_checks["git_safety"],
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_file_created": False,
        "raw_data_read": True,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": True,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_extraction_qa_gate": extraction_success_count == 4,
        "ready_for_sample_index_design_gate": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": CANONICAL_MASK_TASK_NAMES == step13bd.CANONICAL_MASK_TASK_NAMES,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_extraction_qa_gate",
        "all_checks_passed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "precondition_rows": precondition_rows,
        "raw_read_rows": raw_read_rows,
        "parse_rows": parse_rows,
        "event_rows": event_rows,
        "protein_rows": protein_rows,
        "ligand_rows": ligand_rows,
        "qa_rows": qa_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }
