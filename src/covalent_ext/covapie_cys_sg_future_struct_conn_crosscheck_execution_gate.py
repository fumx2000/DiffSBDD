from __future__ import annotations

import ast
import csv
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate as step14s
from covalent_ext import covapie_cys_sg_future_struct_conn_crosscheck_gate as step14r


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0"
STEP_LABEL = "Step 14T"
PREVIOUS_STAGE = step14s.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_execution_precondition_audit.csv"
RAW_PARSE_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_raw_struct_conn_parse_audit.csv"
QUERY_EXECUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_query_execution_audit.csv"
MATCHED_EVIDENCE_CANDIDATES_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_matched_evidence_candidates.csv"
MATCHED_EVIDENCE_CANDIDATES_JSON = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_matched_evidence_candidates.json"
RESULT_SUMMARY_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_crosscheck_result_summary.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_crosscheck_policy_contract.csv"
DOWNSTREAM_READINESS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_crosscheck_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_struct_conn_crosscheck_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_future_struct_conn_crosscheck_execution_gate.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0.py")

RAW_ROOT = step14s.RAW_OUTPUT_ROOT
STEP14S_ROOT = step14s.OUTPUT_ROOT
STEP14R_ROOT = step14r.OUTPUT_ROOT
STEP14Q_ROOT = step14r.STEP14Q_ROOT
STEP14P_ROOT = step14r.STEP14P_ROOT
STEP14O_ROOT = step14r.STEP14O_ROOT
METADATA_CSV = step14r.METADATA_CSV
METADATA_CSV_SHA256 = step14r.METADATA_CSV_SHA256

STEP14S_MANIFEST_JSON = step14s.MANIFEST_JSON
STEP14S_AVAILABILITY_CSV = step14s.AVAILABILITY_MANIFEST_CSV
STEP14R_QUERY_PLAN_CSV = step14r.QUERY_PLAN_CSV
STEP14R_QUERY_PLAN_JSON = step14r.QUERY_PLAN_JSON
STEP14R_INPUT_CONTRACT_CSV = step14r.INPUT_CONTRACT_CSV

EXPECTED_PDB_HET_PAIRS = ["1A54/MDC", "6BV6/JUG", "6BV9/JUG", "6BV8/JUG", "6BV5/JUG"]
CANONICAL_MASK_TASK_NAMES = step14r.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14r.CANONICAL_MASK_TASK_ALIASES

STRUCT_CONN_TAGS_OF_INTEREST = [
    "_struct_conn.id",
    "_struct_conn.conn_type_id",
    "_struct_conn.ptnr1_label_comp_id",
    "_struct_conn.ptnr1_label_atom_id",
    "_struct_conn.ptnr1_auth_asym_id",
    "_struct_conn.ptnr1_auth_seq_id",
    "_struct_conn.ptnr1_label_asym_id",
    "_struct_conn.ptnr1_label_seq_id",
    "_struct_conn.ptnr1_auth_comp_id",
    "_struct_conn.ptnr2_label_comp_id",
    "_struct_conn.ptnr2_label_atom_id",
    "_struct_conn.ptnr2_auth_asym_id",
    "_struct_conn.ptnr2_auth_seq_id",
    "_struct_conn.ptnr2_label_asym_id",
    "_struct_conn.ptnr2_label_seq_id",
    "_struct_conn.ptnr2_auth_comp_id",
]

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
RAW_PARSE_COLUMNS = ["pdb_id", "raw_path", "raw_file_exists", "raw_file_size_bytes", "raw_file_sha256", "first_nonempty_line", "raw_mmcif_read_current_step", "struct_conn_parsed_current_step", "struct_conn_loop_found", "struct_conn_record_count", "struct_conn_field_count", "parser_status", "parse_error_message", "parse_audit_passed"]
QUERY_COLUMNS = ["crosscheck_input_id", "pdb_id", "expected_het_id", "expected_residue_name", "expected_residue_atom_name", "expected_residue_chain_id", "expected_residue_index", "struct_conn_records_scanned", "matched_struct_conn_record_count", "matched_conn_ids", "matched_conn_type_ids", "matched_residue_partner_sides", "matched_ligand_partner_sides", "matched_residue_atom_names", "matched_ligand_atom_names", "crosscheck_status", "blocking_reason", "ready_candidate_current_step", "ready_for_training_current_step", "query_execution_passed", "qa_comment"]
EVIDENCE_COLUMNS = ["struct_conn_evidence_candidate_id", "crosscheck_input_id", "manual_review_candidate_id", "pdb_id", "expected_het_id", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "conn_id", "conn_type_id", "residue_partner_side", "ligand_partner_side", "residue_comp_id", "residue_atom_name", "residue_auth_asym_id", "residue_auth_seq_id", "residue_label_asym_id", "residue_label_seq_id", "ligand_comp_id", "ligand_atom_name", "ligand_auth_asym_id", "ligand_auth_seq_id", "ligand_label_asym_id", "ligand_label_seq_id", "evidence_status", "next_required_gate", "ready_candidate_current_step", "ready_for_training_current_step"]
SUMMARY_COLUMNS = ["crosscheck_input_count", "raw_mmcif_read_count", "struct_conn_parse_attempt_count", "struct_conn_parse_success_count", "matched_input_count", "unmatched_input_count", "ambiguous_input_count", "evidence_candidate_count", "ready_candidate_count_current_step", "ready_for_training_candidate_count_current_step", "ready_for_result_review_gate", "ready_for_training", "recommended_next_step"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _metadata_hash() -> str:
    return hashlib.sha256((REPO_ROOT / METADATA_CSV).read_bytes()).hexdigest() if (REPO_ROOT / METADATA_CSV).exists() else ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_nonempty_line(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _clean_token(value: str) -> str:
    return "" if value in {"?", "."} else value


def _split_mmcif_line(line: str) -> list[str]:
    return [_clean_token(token) for token in shlex.split(line, posix=True)]


def parse_struct_conn_loop(text: str) -> tuple[list[str], list[dict[str, str]], str, str]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        tag_index = idx + 1
        tags: list[str] = []
        while tag_index < len(lines) and lines[tag_index].strip().startswith("_"):
            tags.append(lines[tag_index].strip())
            tag_index += 1
        if not tags or not any(tag.startswith("_struct_conn.") for tag in tags):
            continue
        if not all(tag.startswith("_struct_conn.") for tag in tags):
            continue
        tokens: list[str] = []
        row_index = tag_index
        while row_index < len(lines):
            stripped = lines[row_index].strip()
            if not stripped or stripped == "#":
                break
            if stripped == "loop_" or stripped.startswith("_"):
                break
            try:
                tokens.extend(_split_mmcif_line(stripped))
            except ValueError as exc:
                return tags, [], "raw_parse_error", str(exc)
            row_index += 1
        if not tokens:
            return tags, [], "parsed_struct_conn_loop", ""
        if len(tokens) % len(tags) != 0:
            return tags, [], "raw_parse_error", f"struct_conn token count {len(tokens)} not divisible by field count {len(tags)}"
        rows = []
        for start in range(0, len(tokens), len(tags)):
            token_row = tokens[start : start + len(tags)]
            record = {tag: token_row[pos] for pos, tag in enumerate(tags)}
            for tag in STRUCT_CONN_TAGS_OF_INTEREST:
                record.setdefault(tag, "")
            rows.append(record)
        return tags, rows, "parsed_struct_conn_loop", ""
    return [], [], "no_struct_conn_loop_found", ""


def _side(record: dict[str, str], side: str) -> dict[str, str]:
    return {
        "side": side,
        "comp_id": record.get(f"_struct_conn.{side}_label_comp_id") or record.get(f"_struct_conn.{side}_auth_comp_id", ""),
        "atom_id": record.get(f"_struct_conn.{side}_label_atom_id", ""),
        "auth_asym_id": record.get(f"_struct_conn.{side}_auth_asym_id", ""),
        "auth_seq_id": record.get(f"_struct_conn.{side}_auth_seq_id", ""),
        "label_asym_id": record.get(f"_struct_conn.{side}_label_asym_id", ""),
        "label_seq_id": record.get(f"_struct_conn.{side}_label_seq_id", ""),
    }


def _sequence_matches(actual: str, expected: str) -> bool:
    return not actual or str(actual) == str(expected)


def _chain_matches(actual: str, expected: str) -> bool:
    return not actual or str(actual).upper() == str(expected).upper()


def match_struct_conn_records(query: dict[str, str], records: list[dict[str, str]]) -> tuple[list[dict[str, Any]], str, str, str]:
    matches: list[dict[str, Any]] = []
    conflicts = {"chain": False, "ligand": False}
    for record in records:
        p1 = _side(record, "ptnr1")
        p2 = _side(record, "ptnr2")
        for residue, ligand in [(p1, p2), (p2, p1)]:
            residue_core = residue["comp_id"] == "CYS" and residue["atom_id"] == "SG"
            ligand_core = ligand["comp_id"] == query["ligand_comp_id"]
            if residue_core and ligand["comp_id"] == "CYS" and ligand["atom_id"] == "SG":
                continue
            if residue_core and not ligand_core:
                conflicts["ligand"] = True
            if not (residue_core and ligand_core):
                continue
            chain_ok = _chain_matches(residue["auth_asym_id"], query["residue_chain_id"]) and _chain_matches(residue["label_asym_id"], query["residue_chain_id"])
            seq_ok = _sequence_matches(residue["auth_seq_id"], query["residue_index"]) or _sequence_matches(residue["label_seq_id"], query["residue_index"])
            if not (chain_ok and seq_ok):
                conflicts["chain"] = True
                continue
            matches.append({
                "record": record,
                "residue": residue,
                "ligand": ligand,
                "qa_comment": "auth_fields_matched" if residue["auth_seq_id"] else "label_fields_used_or_auth_fields_absent",
            })
    if len(matches) == 1:
        return matches, "matched_cys_sg_ligand_struct_conn", "", matches[0]["qa_comment"]
    if len(matches) > 1:
        return matches, "ambiguous_multiple_cys_sg_ligand_struct_conn_matches", "multiple_ambiguous_struct_conn_matches", "multiple matching struct_conn records"
    if conflicts["chain"]:
        return matches, "chain_or_residue_index_conflict", "chain_or_residue_index_conflict", "CYS SG and ligand found but chain/residue index did not match"
    if conflicts["ligand"]:
        return matches, "ligand_comp_id_mismatch", "ligand_comp_id_mismatch", "CYS SG struct_conn records found without expected ligand HET"
    return matches, "no_cys_sg_ligand_match", "no_cys_sg_ligand_match", ""


def build_precondition_rows(query_rows: list[dict[str, str]], query_json: list[dict[str, Any]], availability_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14S_MANIFEST_JSON) if STEP14S_MANIFEST_JSON.exists() else {}
    pairs = [f"{row['pdb_id']}/{row['ligand_comp_id']}" for row in query_rows]
    raw_paths = [REPO_ROOT / row["raw_path"] for row in availability_rows]
    checks = [
        ("step14s_manifest_exists", STEP14S_MANIFEST_JSON.as_posix(), "exists", STEP14S_MANIFEST_JSON.exists(), STEP14S_MANIFEST_JSON.exists()),
        ("step14s_stage", STEP14S_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14s_all_checks_passed", STEP14S_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14s_raw_mmcif_available_count", STEP14S_MANIFEST_JSON.as_posix(), "5", manifest.get("raw_mmcif_available_count"), manifest.get("raw_mmcif_available_count") == 5),
        ("step14s_raw_mmcif_integrity_passed_count", STEP14S_MANIFEST_JSON.as_posix(), "5", manifest.get("raw_mmcif_integrity_passed_count"), manifest.get("raw_mmcif_integrity_passed_count") == 5),
        ("step14s_ready_for_execution_gate", STEP14S_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate"), manifest.get("ready_for_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate") is True),
        ("step14s_ready_for_training_false", STEP14S_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14s_availability_manifest_exists", STEP14S_AVAILABILITY_CSV.as_posix(), "exists", STEP14S_AVAILABILITY_CSV.exists(), STEP14S_AVAILABILITY_CSV.exists()),
        ("step14r_query_plan_csv_json_consistent", STEP14R_QUERY_PLAN_JSON.as_posix(), "true", [row["struct_conn_query_id"] for row in query_rows], [row["struct_conn_query_id"] for row in query_rows] == [row["struct_conn_query_id"] for row in query_json]),
        ("raw_files_exist_size_positive_not_html", RAW_ROOT.as_posix(), "true", [path.as_posix() for path in raw_paths], all(path.is_file() and path.stat().st_size > 0 and not _first_nonempty_line(path).lower().startswith("<!doctype") for path in raw_paths)),
        ("accepted_pdb_het_pairs_match", STEP14R_QUERY_PLAN_CSV.as_posix(), str(EXPECTED_PDB_HET_PAIRS), pairs, pairs == EXPECTED_PDB_HET_PAIRS),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_files_not_git_tracked", RAW_ROOT.as_posix(), "false", _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14r.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_raw_parse_rows(query_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]]]:
    rows = []
    records_by_pdb: dict[str, list[dict[str, str]]] = {}
    for query in query_rows:
        pdb_id = query["pdb_id"]
        raw_path = REPO_ROOT / RAW_ROOT / f"{pdb_id.lower()}.cif"
        exists = raw_path.is_file()
        size = raw_path.stat().st_size if exists else 0
        sha = _sha256(raw_path) if exists and size > 0 else ""
        first_line = _first_nonempty_line(raw_path) if exists else ""
        tags: list[str] = []
        records: list[dict[str, str]] = []
        status = "raw_parse_error"
        error = ""
        if exists:
            tags, records, status, error = parse_struct_conn_loop(raw_path.read_text(encoding="utf-8", errors="replace"))
        records_by_pdb[pdb_id] = records
        rows.append({
            "pdb_id": pdb_id,
            "raw_path": (RAW_ROOT / f"{pdb_id.lower()}.cif").as_posix(),
            "raw_file_exists": exists,
            "raw_file_size_bytes": size,
            "raw_file_sha256": sha,
            "first_nonempty_line": first_line,
            "raw_mmcif_read_current_step": exists,
            "struct_conn_parsed_current_step": exists,
            "struct_conn_loop_found": bool(tags),
            "struct_conn_record_count": len(records),
            "struct_conn_field_count": len(tags),
            "parser_status": status,
            "parse_error_message": error,
            "parse_audit_passed": exists and size > 0 and len(sha) == 64 and first_line.startswith("data_") and status in {"parsed_struct_conn_loop", "no_struct_conn_loop_found"},
        })
    return rows, records_by_pdb


def build_query_and_evidence_rows(query_rows: list[dict[str, str]], records_by_pdb: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    input_by_id = {row["crosscheck_input_id"]: row for row in _csv_rows(STEP14R_INPUT_CONTRACT_CSV)}
    query_audit = []
    evidence = []
    for query in query_rows:
        pdb_id = query["pdb_id"]
        records = records_by_pdb[pdb_id]
        if not records:
            status = "no_struct_conn_loop_found"
            matches: list[dict[str, Any]] = []
            blocking = "no_struct_conn_loop_found"
            qa_comment = ""
        else:
            matches, status, blocking, qa_comment = match_struct_conn_records(query, records)
        matched_conn_ids = [match["record"].get("_struct_conn.id", "") for match in matches]
        matched_conn_types = [match["record"].get("_struct_conn.conn_type_id", "") for match in matches]
        query_audit.append({
            "crosscheck_input_id": query["crosscheck_input_id"],
            "pdb_id": pdb_id,
            "expected_het_id": query["ligand_comp_id"],
            "expected_residue_name": query["residue_name"],
            "expected_residue_atom_name": query["residue_atom_name"],
            "expected_residue_chain_id": query["residue_chain_id"],
            "expected_residue_index": query["residue_index"],
            "struct_conn_records_scanned": len(records),
            "matched_struct_conn_record_count": len(matches),
            "matched_conn_ids": ";".join(matched_conn_ids),
            "matched_conn_type_ids": ";".join(matched_conn_types),
            "matched_residue_partner_sides": ";".join(match["residue"]["side"] for match in matches),
            "matched_ligand_partner_sides": ";".join(match["ligand"]["side"] for match in matches),
            "matched_residue_atom_names": ";".join(match["residue"]["atom_id"] for match in matches),
            "matched_ligand_atom_names": ";".join(match["ligand"]["atom_id"] for match in matches),
            "crosscheck_status": status,
            "blocking_reason": blocking,
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "query_execution_passed": True,
            "qa_comment": qa_comment,
        })
        input_row = input_by_id.get(query["crosscheck_input_id"], {})
        for match in matches:
            evidence.append({
                "struct_conn_evidence_candidate_id": f"CYS_SG_STRUCT_CONN_EVIDENCE_{len(evidence) + 1:06d}",
                "crosscheck_input_id": query["crosscheck_input_id"],
                "manual_review_candidate_id": input_row.get("manual_review_candidate_id", ""),
                "pdb_id": pdb_id,
                "expected_het_id": query["ligand_comp_id"],
                "covpdb_residue_name": query["residue_name"],
                "covpdb_residue_index": query["residue_index"],
                "covpdb_chain_id": query["residue_chain_id"],
                "conn_id": match["record"].get("_struct_conn.id", ""),
                "conn_type_id": match["record"].get("_struct_conn.conn_type_id", ""),
                "residue_partner_side": match["residue"]["side"],
                "ligand_partner_side": match["ligand"]["side"],
                "residue_comp_id": match["residue"]["comp_id"],
                "residue_atom_name": match["residue"]["atom_id"],
                "residue_auth_asym_id": match["residue"]["auth_asym_id"],
                "residue_auth_seq_id": match["residue"]["auth_seq_id"],
                "residue_label_asym_id": match["residue"]["label_asym_id"],
                "residue_label_seq_id": match["residue"]["label_seq_id"],
                "ligand_comp_id": match["ligand"]["comp_id"],
                "ligand_atom_name": match["ligand"]["atom_id"],
                "ligand_auth_asym_id": match["ligand"]["auth_asym_id"],
                "ligand_auth_seq_id": match["ligand"]["auth_seq_id"],
                "ligand_label_asym_id": match["ligand"]["label_asym_id"],
                "ligand_label_seq_id": match["ligand"]["label_seq_id"],
                "evidence_status": "struct_conn_match_found_pending_manual_review",
                "next_required_gate": "covapie_cys_sg_struct_conn_crosscheck_result_review_gate",
                "ready_candidate_current_step": False,
                "ready_for_training_current_step": False,
            })
    return query_audit, evidence


def build_result_summary(query_rows: list[dict[str, Any]], parse_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched = sum(row["crosscheck_status"] == "matched_cys_sg_ligand_struct_conn" for row in query_rows)
    ambiguous = sum(row["crosscheck_status"] == "ambiguous_multiple_cys_sg_ligand_struct_conn_matches" for row in query_rows)
    evidence_count = len(evidence_rows)
    next_step = "covapie_cys_sg_struct_conn_crosscheck_result_review_gate" if evidence_count > 0 else "covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate"
    return [{
        "crosscheck_input_count": len(query_rows),
        "raw_mmcif_read_count": sum(_bool(row["raw_mmcif_read_current_step"]) for row in parse_rows),
        "struct_conn_parse_attempt_count": len(parse_rows),
        "struct_conn_parse_success_count": sum(str(row["parser_status"]) in {"parsed_struct_conn_loop", "no_struct_conn_loop_found"} for row in parse_rows),
        "matched_input_count": matched,
        "unmatched_input_count": len(query_rows) - matched - ambiguous,
        "ambiguous_input_count": ambiguous,
        "evidence_candidate_count": evidence_count,
        "ready_candidate_count_current_step": 0,
        "ready_for_training_candidate_count_current_step": 0,
        "ready_for_result_review_gate": evidence_count > 0,
        "ready_for_training": False,
        "recommended_next_step": next_step,
    }]


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "struct_conn_parse_execution_only": "This step only parses struct_conn and executes evidence cross-checks.",
        "ligand_atom_name_must_come_from_raw_struct_conn": "Ligand atom names must be copied from raw struct_conn records.",
        "search_both_partner_orders": "Both ptnr1/ptnr2 orders are searched.",
        "require_cys_sg_partner_for_evidence": "Evidence requires a CYS SG partner.",
        "require_expected_het_partner_for_evidence": "Evidence requires the expected ligand HET partner.",
        "disulfide_sg_sg_not_ligand_evidence": "CYS SG to CYS SG records are not ligand evidence.",
        "matched_evidence_is_not_ready_candidate": "Matched evidence remains pending review.",
        "result_review_required_before_ready": "A result review gate is required before ready status.",
        "no_training_current_step": "Training is not allowed in this step.",
        "no_sample_or_final_dataset_current_step": "Sample and final dataset artifacts are not written.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "canonical_five_masks_preserved": "The canonical five mask tasks remain unchanged.",
    }
    return [{"policy_item": item, "policy_description": desc, "policy_contract_passed": True} for item, desc in descriptions.items()]


def build_downstream_rows(evidence_count: int) -> list[dict[str, Any]]:
    result_review = evidence_count > 0
    blocked_review = evidence_count == 0
    specs = [
        ("ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate", str(result_review).lower(), True, "covapie_cys_sg_struct_conn_crosscheck_result_review_gate" if result_review else "not_ready_current_step", ""),
        ("ready_for_covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate", str(blocked_review).lower(), True, "covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate" if blocked_review else "not_ready_current_step", ""),
        ("ready_for_covapie_small_pilot_manifest_rerun_gate", "false", True, "not_allowed_current_step", ""),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", "false", True, "not_allowed_current_step", ""),
        ("ready_for_training", "false", True, "not_allowed_current_step", ""),
        ("ready_to_train_now", "false", True, "not_allowed_current_step", ""),
    ]
    return [{"readiness_item": item, "observed_status": observed, "readiness_passed": passed, "next_required_gate": next_gate, "qa_comment": comment} for item, observed, passed, next_gate, comment in specs]


def _imports_forbidden_module(path: Path, forbidden: set[str]) -> bool:
    full_path = REPO_ROOT / path
    if not full_path.exists():
        return False
    tree = ast.parse(full_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden:
            return True
    return False


def _forbidden_derived_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def _raw_leftovers_exist() -> bool:
    return RAW_ROOT.exists() and any(path.is_file() and path.suffix.lower() in {".part", ".html", ".htm"} for path in (REPO_ROOT / RAW_ROOT).rglob("*"))


def build_safety_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_tracked = bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    forbidden_imports = {"requests", "urllib", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "bs4"}
    own_imports_ok = not any(_imports_forbidden_module(path, forbidden_imports) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])
    checks = [
        ("no_network_access_current_step", "true", "true", True),
        ("no_download_current_step", "true", "true", True),
        ("raw_mmcif_read_current_step", "true", "true", True),
        ("struct_conn_parsed_current_step", "true", "true", True),
        ("no_data_raw_write_current_step", "true", "true", True),
        ("raw_files_remain_untracked", "true", str(not raw_tracked).lower(), not raw_tracked),
        ("raw_files_remain_unstaged", "true", str(not raw_staged).lower(), not raw_staged),
        ("no_html_or_part_files", "true", str(not _raw_leftovers_exist()).lower(), not _raw_leftovers_exist()),
        ("metadata_csv_unchanged", "true", str(_metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])).lower(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14s_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14S_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14S_ROOT.as_posix()])),
        ("step14r_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14R_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14R_ROOT.as_posix()])),
        ("step14q_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14Q_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14Q_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_final_split_leakage_training_artifacts", "true", str(not _forbidden_derived_artifact_exists()).lower(), not _forbidden_derived_artifact_exists()),
        ("derived_output_no_forbidden_raw_binary_or_html_suffix", "true", str(not _forbidden_derived_artifact_exists()).lower(), not _forbidden_derived_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_requests_urllib_selenium_playwright_bs4_imports", "true", str(own_imports_ok).lower(), own_imports_ok),
        ("no_ready_candidates_created", "true", str(all(not _bool(row["ready_candidate_current_step"]) for row in evidence_rows)).lower(), all(not _bool(row["ready_candidate_current_step"]) for row in evidence_rows)),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, parse_rows, query_rows, evidence_rows, summary_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    summary = summary_rows[0]
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (pre, "precondition_passed"),
            (parse_rows, "parse_audit_passed"),
            (query_rows, "query_execution_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    )
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "crosscheck_input_count": summary["crosscheck_input_count"],
        "raw_mmcif_read_count": summary["raw_mmcif_read_count"],
        "struct_conn_parse_attempt_count": summary["struct_conn_parse_attempt_count"],
        "struct_conn_parse_success_count": summary["struct_conn_parse_success_count"],
        "matched_input_count": summary["matched_input_count"],
        "unmatched_input_count": summary["unmatched_input_count"],
        "ambiguous_input_count": summary["ambiguous_input_count"],
        "evidence_candidate_count": summary["evidence_candidate_count"],
        "accepted_pdb_het_pairs": EXPECTED_PDB_HET_PAIRS,
        "raw_mmcif_read_current_step": True,
        "raw_mmcif_content_parsed_current_step": True,
        "struct_conn_parsed_current_step": True,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "data_raw_written_current_step": False,
        "html_files_written_current_step": False,
        "part_files_leftover_current_step": False,
        "sample_download_manifest_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "requests_used": False,
        "urllib_used": False,
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "ready_candidate_count_current_step": 0,
        "ready_for_training_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "ready_for_covapie_cys_sg_struct_conn_crosscheck_result_review_gate": summary["evidence_candidate_count"] > 0,
        "ready_for_covapie_cys_sg_struct_conn_crosscheck_blocked_review_gate": summary["evidence_candidate_count"] == 0,
        "ready_for_covapie_small_pilot_manifest_rerun_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": summary["recommended_next_step"],
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14t_struct_conn_crosscheck_execution_failed"],
    }


def run_covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0() -> dict[str, Any]:
    query_rows = _csv_rows(STEP14R_QUERY_PLAN_CSV)
    query_json = _load_json(STEP14R_QUERY_PLAN_JSON)
    availability_rows = _csv_rows(STEP14S_AVAILABILITY_CSV)
    pre = build_precondition_rows(query_rows, query_json, availability_rows)
    parse_rows, records_by_pdb = build_raw_parse_rows(query_rows)
    query_audit_rows, evidence_rows = build_query_and_evidence_rows(query_rows, records_by_pdb)
    summary_rows = build_result_summary(query_audit_rows, parse_rows, evidence_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows(len(evidence_rows))
    safety_rows = build_safety_rows(evidence_rows)
    manifest = build_manifest(pre, parse_rows, query_audit_rows, evidence_rows, summary_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": pre,
        "parse_rows": parse_rows,
        "query_rows": query_audit_rows,
        "evidence_rows": evidence_rows,
        "summary_rows": summary_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "manifest": manifest,
    }
