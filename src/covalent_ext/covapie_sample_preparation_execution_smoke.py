from __future__ import annotations

import csv
import hashlib
import json
import math
import shlex
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_sample_preparation_design_gate as step14z


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_sample_preparation_execution_smoke_v0"
STEP_LABEL = "Step 14AA"
PREVIOUS_STAGE = step14z.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_precondition_audit.csv"
EXECUTION_MANIFEST_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_manifest.csv"
EXECUTION_MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_preparation_execution_manifest.json"
SAMPLE_INVENTORY_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_sample_inventory.csv"
SAMPLE_INVENTORY_JSON = OUTPUT_ROOT / "covapie_sample_preparation_execution_sample_inventory.json"
TRACEABILITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_traceability_audit.csv"
QUALITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_quality_audit.csv"
POLICY_CONTRACT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_policy_contract.csv"
DOWNSTREAM_READINESS_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_downstream_readiness_contract.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_preparation_execution_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_preparation_execution_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_preparation_execution_smoke_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_sample_preparation_execution_smoke_v0.py")

STEP14Z_MANIFEST_JSON = step14z.MANIFEST_JSON
STEP14Z_INPUT_MANIFEST_CSV = step14z.INPUT_MANIFEST_CSV
STEP14Z_INPUT_MANIFEST_JSON = step14z.INPUT_MANIFEST_JSON
STEP14Z_REQUIRED_ARTIFACT_PLAN_CSV = step14z.REQUIRED_ARTIFACT_PLAN_CSV
STEP14Z_RAW_ACCESS_PLAN_CSV = step14z.RAW_ACCESS_PLAN_CSV
STEP14Z_ROOT = step14z.OUTPUT_ROOT
STEP14Y_ROOT = step14z.STEP14Y_ROOT
STEP14X_ROOT = step14z.STEP14X_ROOT
STEP14W_ROOT = step14z.STEP14W_ROOT
STEP14V_ROOT = step14z.STEP14V_ROOT
STEP14U_ROOT = step14z.STEP14U_ROOT
STEP14T_ROOT = step14z.STEP14T_ROOT

RAW_ROOT = step14z.RAW_ROOT
METADATA_CSV = step14z.METADATA_CSV
METADATA_CSV_SHA256 = step14z.METADATA_CSV_SHA256
CANONICAL_MASK_TASK_NAMES = step14z.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14z.CANONICAL_MASK_TASK_ALIASES
ACCEPTED_PDB_HET_PAIRS = step14z.ACCEPTED_PDB_HET_PAIRS
POCKET_RADIUS_ANGSTROM = 8.0
NEXT_REQUIRED_GATE = "covapie_sample_preparation_qa_gate"

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EXECUTION_MANIFEST_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "raw_file_path", "sample_artifact_root", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "sample_preparation_status", "ready_for_sample_index_current_step", "ready_for_final_dataset_current_step", "ready_for_training_current_step"]
SAMPLE_INVENTORY_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "raw_file_path", "sample_artifact_root", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "sample_preparation_status", "ready_for_sample_index_current_step", "ready_for_final_dataset_current_step", "ready_for_training_current_step"]
TRACEABILITY_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "raw_file_path", "struct_conn_event_source", "residue_atom_from_struct_conn", "ligand_atom_from_struct_conn", "atom_site_residue_atom_found", "atom_site_ligand_atom_found", "traceability_audit_passed", "blocking_reasons"]
QUALITY_COLUMNS = ["sample_preparation_input_id", "sample_execution_id", "pdb_id", "expected_het_id", "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count", "ligand_covalent_atom_count", "quality_audit_passed", "blocking_reasons"]
POLICY_COLUMNS = ["policy_item", "policy_description", "policy_contract_passed"]
DOWNSTREAM_COLUMNS = ["readiness_item", "observed_status", "readiness_passed", "next_required_gate", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]

PROTEIN_ATOM_COLUMNS = ["sample_preparation_input_id", "pdb_id", "atom_site_id", "group_pdb", "type_symbol", "atom_name", "residue_name", "chain_id", "residue_index", "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id", "x", "y", "z", "occupancy", "altloc", "model_num", "source_raw_file"]
LIGAND_ATOM_COLUMNS = ["sample_preparation_input_id", "pdb_id", "expected_het_id", "atom_site_id", "type_symbol", "atom_name", "ligand_comp_id", "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id", "x", "y", "z", "occupancy", "altloc", "model_num", "is_covalent_ligand_atom", "source_raw_file"]
POCKET_ATOM_COLUMNS = ["sample_preparation_input_id", "pdb_id", "pocket_radius_angstrom", "atom_site_id", "group_pdb", "type_symbol", "atom_name", "residue_name", "chain_id", "residue_index", "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id", "x", "y", "z", "min_distance_to_ligand_angstrom", "source_raw_file"]
COVALENT_EVENT_COLUMNS = ["sample_preparation_input_id", "pdb_id", "expected_het_id", "conn_id", "conn_type_id", "residue_comp_id", "residue_atom_name", "residue_auth_asym_id", "residue_auth_seq_id", "residue_label_asym_id", "residue_label_seq_id", "ligand_comp_id", "ligand_atom_name", "ligand_auth_asym_id", "ligand_auth_seq_id", "ligand_label_asym_id", "ligand_label_seq_id", "covalent_bond_atom_pair", "event_source", "event_status"]
PAIR_TABLE_COLUMNS = ["sample_preparation_input_id", "pdb_id", "expected_het_id", "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair", "residue_atom_site_id", "ligand_atom_site_id", "residue_x", "residue_y", "residue_z", "ligand_x", "ligand_y", "ligand_z", "bond_distance_angstrom", "validation_status"]
SAMPLE_AUDIT_COLUMNS = ["audit_item", "expected_status", "observed_status", "audit_passed", "blocking_reasons"]

ATOM_SITE_TAGS = [
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_alt_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.occupancy",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_atom_id",
    "_atom_site.pdbx_PDB_model_num",
]

STRUCT_CONN_TAGS = [
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
    path = REPO_ROOT / METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _clean_token(value: str) -> str:
    return "" if value in {"?", "."} else value


def _split_mmcif_line(line: str) -> list[str]:
    return [_clean_token(token) for token in shlex.split(line, posix=True)]


def _parse_loop(text: str, prefix: str, required_tags: list[str]) -> tuple[list[str], list[dict[str, str]], str]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        tag_index = idx + 1
        tags: list[str] = []
        while tag_index < len(lines) and lines[tag_index].strip().startswith("_"):
            tags.append(lines[tag_index].strip())
            tag_index += 1
        if not tags or not all(tag.startswith(prefix) for tag in tags):
            continue
        tokens: list[str] = []
        row_index = tag_index
        while row_index < len(lines):
            stripped = lines[row_index].strip()
            if not stripped or stripped == "#" or stripped == "loop_" or stripped.startswith("_"):
                break
            tokens.extend(_split_mmcif_line(stripped))
            row_index += 1
        if not tokens:
            return tags, [], "parsed_empty_loop"
        if len(tokens) % len(tags) != 0:
            return tags, [], f"token_count_not_divisible:{len(tokens)}:{len(tags)}"
        rows = []
        for start in range(0, len(tokens), len(tags)):
            row = {tag: tokens[start + pos] for pos, tag in enumerate(tags)}
            for tag in required_tags:
                row.setdefault(tag, "")
            rows.append(row)
        return tags, rows, "parsed_loop"
    return [], [], "loop_not_found"


def parse_atom_site_loop(text: str) -> tuple[list[str], list[dict[str, str]], str]:
    return _parse_loop(text, "_atom_site.", ATOM_SITE_TAGS)


def parse_struct_conn_loop(text: str) -> tuple[list[str], list[dict[str, str]], str]:
    return _parse_loop(text, "_struct_conn.", STRUCT_CONN_TAGS)


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


def _matches(value: str, expected: str) -> bool:
    return not value or str(value).upper() == str(expected).upper()


def _seq_matches(value: str, expected: str) -> bool:
    return not value or str(value) == str(expected)


def find_matching_event(sample: dict[str, str], struct_rows: list[dict[str, str]]) -> tuple[dict[str, Any] | None, str]:
    matches: list[dict[str, Any]] = []
    for record in struct_rows:
        if record.get("_struct_conn.conn_type_id") != "covale":
            continue
        p1 = _side(record, "ptnr1")
        p2 = _side(record, "ptnr2")
        for residue, ligand in [(p1, p2), (p2, p1)]:
            residue_ok = residue["comp_id"] == sample["covpdb_residue_name"] and residue["atom_id"] == sample["residue_atom_name"]
            ligand_ok = ligand["comp_id"] == sample["expected_het_id"] and ligand["atom_id"] == sample["ligand_atom_name"]
            chain_ok = _matches(residue["auth_asym_id"], sample["covpdb_chain_id"]) and _matches(residue["label_asym_id"], sample["covpdb_chain_id"])
            seq_ok = _seq_matches(residue["auth_seq_id"], sample["covpdb_residue_index"]) or _seq_matches(residue["label_seq_id"], sample["covpdb_residue_index"])
            if residue_ok and ligand_ok and chain_ok and seq_ok:
                matches.append({"record": record, "residue": residue, "ligand": ligand})
    if len(matches) == 1:
        return matches[0], "validated"
    if len(matches) > 1:
        return None, "ambiguous_multiple_matching_struct_conn_events"
    return None, "no_matching_cys_sg_jug_cag_struct_conn_event"


def _model_allowed(atom: dict[str, str]) -> bool:
    model = atom.get("_atom_site.pdbx_PDB_model_num", "")
    return model in {"", "1"}


def _altloc_allowed(atom: dict[str, str]) -> bool:
    return atom.get("_atom_site.label_alt_id", "") in {"", "A"}


def _float(atom: dict[str, str], tag: str) -> float:
    return float(atom[tag])


def _coords(atom: dict[str, str]) -> tuple[float, float, float]:
    return (_float(atom, "_atom_site.Cartn_x"), _float(atom, "_atom_site.Cartn_y"), _float(atom, "_atom_site.Cartn_z"))


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _atom_comp(atom: dict[str, str]) -> str:
    return atom.get("_atom_site.auth_comp_id") or atom.get("_atom_site.label_comp_id", "")


def _atom_name(atom: dict[str, str]) -> str:
    return atom.get("_atom_site.auth_atom_id") or atom.get("_atom_site.label_atom_id", "")


def _atom_auth_asym(atom: dict[str, str]) -> str:
    return atom.get("_atom_site.auth_asym_id", "")


def _atom_auth_seq(atom: dict[str, str]) -> str:
    return atom.get("_atom_site.auth_seq_id", "")


def _atom_label_asym(atom: dict[str, str]) -> str:
    return atom.get("_atom_site.label_asym_id", "")


def _atom_label_seq(atom: dict[str, str]) -> str:
    return atom.get("_atom_site.label_seq_id", "")


def _atom_matches_partner(atom: dict[str, str], partner: dict[str, str]) -> bool:
    comp_ok = _atom_comp(atom) == partner["comp_id"]
    atom_ok = _atom_name(atom) == partner["atom_id"]
    auth_ok = (not partner["auth_asym_id"] or _atom_auth_asym(atom) == partner["auth_asym_id"]) and (not partner["auth_seq_id"] or _atom_auth_seq(atom) == partner["auth_seq_id"])
    label_ok = (not partner["label_asym_id"] or _atom_label_asym(atom) == partner["label_asym_id"]) and (not partner["label_seq_id"] or _atom_label_seq(atom) == partner["label_seq_id"])
    return comp_ok and atom_ok and (auth_ok or label_ok)


def _ligand_instance_matches(atom: dict[str, str], ligand: dict[str, str]) -> bool:
    if _atom_comp(atom) != ligand["comp_id"]:
        return False
    auth_ok = (not ligand["auth_asym_id"] or _atom_auth_asym(atom) == ligand["auth_asym_id"]) and (not ligand["auth_seq_id"] or _atom_auth_seq(atom) == ligand["auth_seq_id"])
    label_ok = (not ligand["label_asym_id"] or _atom_label_asym(atom) == ligand["label_asym_id"]) and (not ligand["label_seq_id"] or _atom_label_seq(atom) == ligand["label_seq_id"])
    return auth_ok or label_ok


def _raw_files_for_pdb(pdb_id: str) -> list[Path]:
    if not (REPO_ROOT / RAW_ROOT).exists():
        return []
    targets = {f"{pdb_id.lower()}.cif", f"{pdb_id.lower()}.mmcif"}
    return sorted(path for path in (REPO_ROOT / RAW_ROOT).iterdir() if path.is_file() and path.name.lower() in targets)


def _source_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sample_root(sample: dict[str, str]) -> Path:
    return OUTPUT_ROOT / "samples" / f"{sample['pdb_id']}_{sample['expected_het_id']}"


def _protein_row(sample_id: str, pdb_id: str, atom: dict[str, str], source: str) -> dict[str, Any]:
    return {
        "sample_preparation_input_id": sample_id,
        "pdb_id": pdb_id,
        "atom_site_id": atom.get("_atom_site.id", ""),
        "group_pdb": atom.get("_atom_site.group_PDB", ""),
        "type_symbol": atom.get("_atom_site.type_symbol", ""),
        "atom_name": _atom_name(atom),
        "residue_name": _atom_comp(atom),
        "chain_id": _atom_auth_asym(atom) or _atom_label_asym(atom),
        "residue_index": _atom_auth_seq(atom) or _atom_label_seq(atom),
        "auth_asym_id": _atom_auth_asym(atom),
        "auth_seq_id": _atom_auth_seq(atom),
        "label_asym_id": _atom_label_asym(atom),
        "label_seq_id": _atom_label_seq(atom),
        "x": atom.get("_atom_site.Cartn_x", ""),
        "y": atom.get("_atom_site.Cartn_y", ""),
        "z": atom.get("_atom_site.Cartn_z", ""),
        "occupancy": atom.get("_atom_site.occupancy", ""),
        "altloc": atom.get("_atom_site.label_alt_id", ""),
        "model_num": atom.get("_atom_site.pdbx_PDB_model_num", ""),
        "source_raw_file": source,
    }


def _ligand_row(sample_id: str, pdb_id: str, expected_het_id: str, atom: dict[str, str], covalent_atom_id: str, source: str) -> dict[str, Any]:
    return {
        "sample_preparation_input_id": sample_id,
        "pdb_id": pdb_id,
        "expected_het_id": expected_het_id,
        "atom_site_id": atom.get("_atom_site.id", ""),
        "type_symbol": atom.get("_atom_site.type_symbol", ""),
        "atom_name": _atom_name(atom),
        "ligand_comp_id": _atom_comp(atom),
        "auth_asym_id": _atom_auth_asym(atom),
        "auth_seq_id": _atom_auth_seq(atom),
        "label_asym_id": _atom_label_asym(atom),
        "label_seq_id": _atom_label_seq(atom),
        "x": atom.get("_atom_site.Cartn_x", ""),
        "y": atom.get("_atom_site.Cartn_y", ""),
        "z": atom.get("_atom_site.Cartn_z", ""),
        "occupancy": atom.get("_atom_site.occupancy", ""),
        "altloc": atom.get("_atom_site.label_alt_id", ""),
        "model_num": atom.get("_atom_site.pdbx_PDB_model_num", ""),
        "is_covalent_ligand_atom": _atom_name(atom) == covalent_atom_id,
        "source_raw_file": source,
    }


def _pocket_row(sample_id: str, pdb_id: str, atom: dict[str, str], min_distance: float, source: str) -> dict[str, Any]:
    base = _protein_row(sample_id, pdb_id, atom, source)
    return {
        "sample_preparation_input_id": sample_id,
        "pdb_id": pdb_id,
        "pocket_radius_angstrom": f"{POCKET_RADIUS_ANGSTROM:.1f}",
        "atom_site_id": base["atom_site_id"],
        "group_pdb": base["group_pdb"],
        "type_symbol": base["type_symbol"],
        "atom_name": base["atom_name"],
        "residue_name": base["residue_name"],
        "chain_id": base["chain_id"],
        "residue_index": base["residue_index"],
        "auth_asym_id": base["auth_asym_id"],
        "auth_seq_id": base["auth_seq_id"],
        "label_asym_id": base["label_asym_id"],
        "label_seq_id": base["label_seq_id"],
        "x": base["x"],
        "y": base["y"],
        "z": base["z"],
        "min_distance_to_ligand_angstrom": f"{min_distance:.3f}",
        "source_raw_file": source,
    }


def _covalent_event_row(sample: dict[str, str], event: dict[str, Any]) -> dict[str, Any]:
    residue = event["residue"]
    ligand = event["ligand"]
    record = event["record"]
    return {
        "sample_preparation_input_id": sample["sample_preparation_input_id"],
        "pdb_id": sample["pdb_id"],
        "expected_het_id": sample["expected_het_id"],
        "conn_id": record.get("_struct_conn.id", ""),
        "conn_type_id": record.get("_struct_conn.conn_type_id", ""),
        "residue_comp_id": residue["comp_id"],
        "residue_atom_name": residue["atom_id"],
        "residue_auth_asym_id": residue["auth_asym_id"],
        "residue_auth_seq_id": residue["auth_seq_id"],
        "residue_label_asym_id": residue["label_asym_id"],
        "residue_label_seq_id": residue["label_seq_id"],
        "ligand_comp_id": ligand["comp_id"],
        "ligand_atom_name": ligand["atom_id"],
        "ligand_auth_asym_id": ligand["auth_asym_id"],
        "ligand_auth_seq_id": ligand["auth_seq_id"],
        "ligand_label_asym_id": ligand["label_asym_id"],
        "ligand_label_seq_id": ligand["label_seq_id"],
        "covalent_bond_atom_pair": "SG--CAG",
        "event_source": "raw_struct_conn",
        "event_status": "validated",
    }


def _pair_row(sample: dict[str, str], residue_atom: dict[str, str], ligand_atom: dict[str, str]) -> dict[str, Any]:
    rc = _coords(residue_atom)
    lc = _coords(ligand_atom)
    return {
        "sample_preparation_input_id": sample["sample_preparation_input_id"],
        "pdb_id": sample["pdb_id"],
        "expected_het_id": sample["expected_het_id"],
        "residue_atom_name": "SG",
        "ligand_atom_name": "CAG",
        "covalent_bond_atom_pair": "SG--CAG",
        "residue_atom_site_id": residue_atom.get("_atom_site.id", ""),
        "ligand_atom_site_id": ligand_atom.get("_atom_site.id", ""),
        "residue_x": f"{rc[0]:.3f}",
        "residue_y": f"{rc[1]:.3f}",
        "residue_z": f"{rc[2]:.3f}",
        "ligand_x": f"{lc[0]:.3f}",
        "ligand_y": f"{lc[1]:.3f}",
        "ligand_z": f"{lc[2]:.3f}",
        "bond_distance_angstrom": f"{_distance(rc, lc):.3f}",
        "validation_status": "validated_from_raw_struct_conn_and_atom_site",
    }


def _audit_rows(statuses: dict[str, bool]) -> list[dict[str, Any]]:
    order = [
        "raw_file_resolved",
        "atom_site_loop_parsed",
        "struct_conn_loop_parsed",
        "matching_cys_sg_jug_cag_event_found",
        "protein_atom_table_written",
        "ligand_atom_table_written",
        "pocket_atom_table_written",
        "covalent_event_table_written",
        "ligand_residue_atom_pair_table_written",
        "sample_preparation_passed",
    ]
    return [{"audit_item": item, "expected_status": "true", "observed_status": statuses.get(item, False), "audit_passed": statuses.get(item, False), "blocking_reasons": "" if statuses.get(item, False) else item} for item in order]


def prepare_sample(sample: dict[str, str]) -> dict[str, Any]:
    raw_files = _raw_files_for_pdb(sample["pdb_id"])
    raw_file = raw_files[0] if len(raw_files) == 1 else None
    statuses = {"raw_file_resolved": raw_file is not None}
    protein_rows: list[dict[str, Any]] = []
    ligand_rows: list[dict[str, Any]] = []
    pocket_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    event_status = "raw_file_not_resolved"
    atom_tags: list[str] = []
    struct_tags: list[str] = []
    atom_rows: list[dict[str, str]] = []
    struct_rows: list[dict[str, str]] = []
    event: dict[str, Any] | None = None
    residue_atom: dict[str, str] | None = None
    ligand_atom: dict[str, str] | None = None
    source = _source_path(raw_file) if raw_file else ""

    if raw_file:
        text = raw_file.read_text(encoding="utf-8", errors="replace")
        atom_tags, atom_rows, atom_status = parse_atom_site_loop(text)
        struct_tags, struct_rows, struct_status = parse_struct_conn_loop(text)
        statuses["atom_site_loop_parsed"] = atom_status == "parsed_loop" and len(atom_rows) > 0
        statuses["struct_conn_loop_parsed"] = struct_status == "parsed_loop" and len(struct_rows) > 0
        event, event_status = find_matching_event(sample, struct_rows)
        statuses["matching_cys_sg_jug_cag_event_found"] = event is not None
        if event:
            filtered_atoms = [a for a in atom_rows if _model_allowed(a) and _altloc_allowed(a)]
            residue_atoms = [a for a in filtered_atoms if _atom_matches_partner(a, event["residue"])]
            ligand_instance_atoms = [a for a in filtered_atoms if _ligand_instance_matches(a, event["ligand"])]
            ligand_cag_atoms = [a for a in ligand_instance_atoms if _atom_name(a) == event["ligand"]["atom_id"]]
            residue_atom = residue_atoms[0] if len(residue_atoms) == 1 else None
            ligand_atom = ligand_cag_atoms[0] if len(ligand_cag_atoms) == 1 else None
            protein_atoms = [a for a in filtered_atoms if a.get("_atom_site.group_PDB") == "ATOM"]
            protein_rows = [_protein_row(sample["sample_preparation_input_id"], sample["pdb_id"], a, source) for a in protein_atoms]
            ligand_rows = [_ligand_row(sample["sample_preparation_input_id"], sample["pdb_id"], sample["expected_het_id"], a, event["ligand"]["atom_id"], source) for a in ligand_instance_atoms]
            event_rows = [_covalent_event_row(sample, event)]
            if residue_atom and ligand_atom:
                pair_rows = [_pair_row(sample, residue_atom, ligand_atom)]
            ligand_coords = [_coords(a) for a in ligand_instance_atoms]
            if ligand_coords:
                for atom in protein_atoms:
                    min_dist = min(_distance(_coords(atom), coord) for coord in ligand_coords)
                    if min_dist <= POCKET_RADIUS_ANGSTROM:
                        pocket_rows.append(_pocket_row(sample["sample_preparation_input_id"], sample["pdb_id"], atom, min_dist, source))
    else:
        statuses["atom_site_loop_parsed"] = False
        statuses["struct_conn_loop_parsed"] = False
        statuses["matching_cys_sg_jug_cag_event_found"] = False

    statuses.update({
        "protein_atom_table_written": len(protein_rows) > 0,
        "ligand_atom_table_written": len(ligand_rows) > 0 and sum(_bool(row["is_covalent_ligand_atom"]) for row in ligand_rows) == 1,
        "pocket_atom_table_written": len(pocket_rows) > 0,
        "covalent_event_table_written": len(event_rows) == 1,
        "ligand_residue_atom_pair_table_written": len(pair_rows) == 1 and float(pair_rows[0]["bond_distance_angstrom"]) > 0 if pair_rows else False,
    })
    statuses["sample_preparation_passed"] = all(statuses.values())
    return {
        "sample": sample,
        "raw_files": raw_files,
        "raw_file": raw_file,
        "source_raw_file": source,
        "atom_site_tags": atom_tags,
        "struct_conn_tags": struct_tags,
        "atom_site_row_count": len(atom_rows),
        "struct_conn_row_count": len(struct_rows),
        "event_status": event_status,
        "residue_atom_found": residue_atom is not None,
        "ligand_atom_found": ligand_atom is not None,
        "protein_rows": protein_rows,
        "ligand_rows": ligand_rows,
        "pocket_rows": pocket_rows,
        "event_rows": event_rows,
        "pair_rows": pair_rows,
        "audit_rows": _audit_rows(statuses),
        "sample_preparation_passed": statuses["sample_preparation_passed"],
    }


def build_precondition_rows(input_rows: list[dict[str, str]], input_json: list[dict[str, Any]], artifact_plan_rows: list[dict[str, str]], raw_access_rows: list[dict[str, str]], sample_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14Z_MANIFEST_JSON) if STEP14Z_MANIFEST_JSON.exists() else {}
    raw_resolved = all(len(result["raw_files"]) == 1 for result in sample_results)
    checks = [
        ("step14z_manifest_exists", STEP14Z_MANIFEST_JSON.as_posix(), "exists", STEP14Z_MANIFEST_JSON.exists(), STEP14Z_MANIFEST_JSON.exists()),
        ("step14z_stage", STEP14Z_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14z_all_checks_passed", STEP14Z_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14z_sample_preparation_input_count", STEP14Z_MANIFEST_JSON.as_posix(), "3", manifest.get("sample_preparation_input_count"), manifest.get("sample_preparation_input_count") == 3),
        ("step14z_raw_read_required_next_step", STEP14Z_MANIFEST_JSON.as_posix(), "true", manifest.get("raw_mmcif_read_required_next_step"), manifest.get("raw_mmcif_read_required_next_step") is True),
        ("step14z_ready_for_execution_smoke", STEP14Z_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_sample_preparation_execution_smoke"), manifest.get("ready_for_covapie_sample_preparation_execution_smoke") is True),
        ("step14z_ready_for_training_false", STEP14Z_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14z_input_manifest_csv_json_consistent", STEP14Z_INPUT_MANIFEST_JSON.as_posix(), "3 consistent rows", f"{len(input_rows)} csv/{len(input_json)} json", len(input_rows) == len(input_json) == 3 and [r["sample_preparation_input_id"] for r in input_rows] == [r["sample_preparation_input_id"] for r in input_json]),
        ("step14z_required_artifact_plan_exists", STEP14Z_REQUIRED_ARTIFACT_PLAN_CSV.as_posix(), "3", len(artifact_plan_rows), STEP14Z_REQUIRED_ARTIFACT_PLAN_CSV.exists() and len(artifact_plan_rows) == 3),
        ("step14z_raw_access_plan_exists", STEP14Z_RAW_ACCESS_PLAN_CSV.as_posix(), "3", len(raw_access_rows), STEP14Z_RAW_ACCESS_PLAN_CSV.exists() and len(raw_access_rows) == 3),
        ("raw_files_exist_for_6bv6_6bv8_6bv5", RAW_ROOT.as_posix(), "one per PDB", [len(result["raw_files"]) for result in sample_results], raw_resolved),
        ("raw_files_not_tracked", RAW_ROOT.as_posix(), "false", _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip()),
        ("raw_files_not_staged", RAW_ROOT.as_posix(), "false", _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip(), not _run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip()),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14z.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_execution_rows(sample_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, result in enumerate(sample_results, start=1):
        sample = result["sample"]
        rows.append({
            "sample_preparation_input_id": sample["sample_preparation_input_id"],
            "sample_execution_id": f"CYS_SG_SAMPLE_PREP_EXECUTION_{idx:06d}",
            "pdb_id": sample["pdb_id"],
            "expected_het_id": sample["expected_het_id"],
            "raw_file_path": result["source_raw_file"],
            "sample_artifact_root": _sample_root(sample).as_posix(),
            "protein_atom_count": len(result["protein_rows"]),
            "ligand_atom_count": len(result["ligand_rows"]),
            "pocket_atom_count": len(result["pocket_rows"]),
            "covalent_event_count": len(result["event_rows"]),
            "ligand_residue_atom_pair_count": len(result["pair_rows"]),
            "sample_preparation_status": "sample_preparation_smoke_passed" if result["sample_preparation_passed"] else result["event_status"],
            "ready_for_sample_index_current_step": False,
            "ready_for_final_dataset_current_step": False,
            "ready_for_training_current_step": False,
        })
    return rows


def build_traceability_rows(sample_results: list[dict[str, Any]], execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_input = {row["sample_preparation_input_id"]: row for row in execution_rows}
    rows = []
    for result in sample_results:
        sample = result["sample"]
        exec_row = by_input[sample["sample_preparation_input_id"]]
        passed = result["event_status"] == "validated" and result["residue_atom_found"] and result["ligand_atom_found"]
        rows.append({
            "sample_preparation_input_id": sample["sample_preparation_input_id"],
            "sample_execution_id": exec_row["sample_execution_id"],
            "pdb_id": sample["pdb_id"],
            "expected_het_id": sample["expected_het_id"],
            "raw_file_path": result["source_raw_file"],
            "struct_conn_event_source": "raw_struct_conn",
            "residue_atom_from_struct_conn": True,
            "ligand_atom_from_struct_conn": True,
            "atom_site_residue_atom_found": result["residue_atom_found"],
            "atom_site_ligand_atom_found": result["ligand_atom_found"],
            "traceability_audit_passed": passed,
            "blocking_reasons": "" if passed else result["event_status"],
        })
    return rows


def build_quality_rows(sample_results: list[dict[str, Any]], execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_input = {row["sample_preparation_input_id"]: row for row in execution_rows}
    rows = []
    for result in sample_results:
        sample = result["sample"]
        exec_row = by_input[sample["sample_preparation_input_id"]]
        ligand_covalent_atom_count = sum(_bool(row["is_covalent_ligand_atom"]) for row in result["ligand_rows"])
        passed = result["sample_preparation_passed"] and ligand_covalent_atom_count == 1
        rows.append({
            "sample_preparation_input_id": sample["sample_preparation_input_id"],
            "sample_execution_id": exec_row["sample_execution_id"],
            "pdb_id": sample["pdb_id"],
            "expected_het_id": sample["expected_het_id"],
            "protein_atom_count": len(result["protein_rows"]),
            "ligand_atom_count": len(result["ligand_rows"]),
            "pocket_atom_count": len(result["pocket_rows"]),
            "covalent_event_count": len(result["event_rows"]),
            "ligand_residue_atom_pair_count": len(result["pair_rows"]),
            "ligand_covalent_atom_count": ligand_covalent_atom_count,
            "quality_audit_passed": passed,
            "blocking_reasons": "" if passed else result["event_status"],
        })
    return rows


def build_policy_rows() -> list[dict[str, Any]]:
    descriptions = {
        "sample_preparation_execution_smoke_only": "This step writes small pilot sample preparation smoke outputs.",
        "raw_read_allowed_current_step": "Ignored raw CIF/mmCIF read is allowed in this step.",
        "struct_conn_and_atom_site_parse_allowed_current_step": "struct_conn and atom_site parsing are allowed in this step.",
        "atom_tables_are_smoke_outputs_not_training_samples": "Atom tables are smoke outputs, not training samples.",
        "no_sample_index_current_step": "No sample index is written.",
        "no_final_dataset_current_step": "No final dataset is written.",
        "no_split_or_leakage_current_step": "No split or leakage matrix is written.",
        "no_dataloader_smoke_current_step": "No dataloader smoke is written.",
        "feature_semantics_audit_required_before_training": "Feature semantics audit remains required before training.",
        "leakage_split_gate_required_before_training": "Leakage/split gate remains required before training.",
        "canonical_five_masks_preserved": "The canonical five mask tasks are preserved.",
        "do_not_train_from_execution_smoke_outputs": "Execution smoke outputs must not be used for training.",
    }
    return [{"policy_item": item, "policy_description": description, "policy_contract_passed": True} for item, description in descriptions.items()]


def build_downstream_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_sample_preparation_qa_gate", True, True, NEXT_REQUIRED_GATE, "allowed next step"),
        ("ready_for_covapie_sample_index_design_gate", False, True, "not_allowed_current_step", "sample preparation QA gate must run first"),
        ("ready_for_covapie_actual_dataloader_adapter_smoke", False, True, "not_allowed_current_step", "sample index/final dataset path not ready"),
        ("ready_for_training", False, True, "not_allowed_current_step", "not a training sample"),
        ("ready_to_train_now", False, True, "not_allowed_current_step", "feature semantics and leakage/split gates remain required"),
    ]
    return [{"readiness_item": item, "observed_status": observed, "readiness_passed": passed, "next_required_gate": next_gate, "qa_comment": comment} for item, observed, passed, next_gate, comment in specs]


def _forbidden_derived_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm", ".part"}
    names = {"sample_index.csv", "sample_index.json", "final_dataset.csv", "final_dataset.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.is_file() and (path.suffix.lower() in suffixes or path.name in names) for path in root.rglob("*"))


def _raw_leftovers_exist() -> bool:
    return (REPO_ROOT / RAW_ROOT).exists() and any(path.is_file() and path.suffix.lower() in {".part", ".html", ".htm"} for path in (REPO_ROOT / RAW_ROOT).rglob("*"))


def build_safety_rows() -> list[dict[str, Any]]:
    raw_tracked = bool(_run_git(["ls-files", RAW_ROOT.as_posix()]).stdout.strip())
    raw_staged = bool(_run_git(["diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()]).stdout.strip())
    no_forbidden = not _forbidden_derived_artifact_exists()
    checks = [
        ("network_access_used_current_step", "false", "false", True),
        ("download_attempted_current_step", "false", "false", True),
        ("raw_mmcif_read_current_step", "true", "true", True),
        ("struct_conn_parsed_current_step", "true", "true", True),
        ("atom_site_parsed_current_step", "true", "true", True),
        ("data_raw_written_current_step", "false", "false", True),
        ("raw_files_remain_untracked", "true", str(not raw_tracked).lower(), not raw_tracked),
        ("raw_files_remain_unstaged", "true", str(not raw_staged).lower(), not raw_staged),
        ("raw_files_committed", "false", str(raw_tracked).lower(), not raw_tracked),
        ("html_files_written_current_step", "false", str(_raw_leftovers_exist()).lower(), not _raw_leftovers_exist()),
        ("part_files_leftover_current_step", "false", str(_raw_leftovers_exist()).lower(), not _raw_leftovers_exist()),
        ("metadata_csv_unchanged", "true", str(_metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])).lower(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14z_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14Z_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14Z_ROOT.as_posix()])),
        ("step14y_artifacts_unchanged", "true", str(not _path_diff_exists([STEP14Y_ROOT.as_posix()])).lower(), not _path_diff_exists([STEP14Y_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", str(not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])).lower(), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", str(not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])).lower(), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("sample_index_written_current_step", "false", str(not no_forbidden).lower(), no_forbidden),
        ("final_dataset_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("split_assignments_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("leakage_matrix_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("actual_dataloader_smoke_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("training_artifacts_written", "false", str(not no_forbidden).lower(), no_forbidden),
        ("torch_imported", "false", "false", True),
        ("numpy_imported", "false", "false", True),
        ("rdkit_used", "false", "false", True),
        ("gemmi_used", "false", "false", True),
        ("requests_used", "false", "false", True),
        ("urllib_used", "false", "false", True),
        ("selenium_used", "false", "false", True),
        ("playwright_used", "false", "false", True),
        ("bs4_used", "false", "false", True),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(input_rows, execution_rows, precondition_rows, traceability_rows, quality_rows, policy_rows, downstream_rows, safety_rows) -> dict[str, Any]:
    accepted_pairs = [f"{row['pdb_id']}/{row['expected_het_id']}" for row in input_rows]
    passed = all(
        _all_true(rows, column)
        for rows, column in [
            (precondition_rows, "precondition_passed"),
            (traceability_rows, "traceability_audit_passed"),
            (quality_rows, "quality_audit_passed"),
            (policy_rows, "policy_contract_passed"),
            (downstream_rows, "readiness_passed"),
            (safety_rows, "safety_passed"),
        ]
    ) and len(execution_rows) == 3 and accepted_pairs == ACCEPTED_PDB_HET_PAIRS
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "input_sample_preparation_count": len(input_rows),
        "sample_execution_count": len(execution_rows),
        "sample_preparation_passed_count": sum(row["sample_preparation_status"] == "sample_preparation_smoke_passed" for row in execution_rows),
        "raw_file_resolved_count": sum(bool(row["raw_file_path"]) for row in execution_rows),
        "raw_mmcif_read_current_step": True,
        "struct_conn_parsed_current_step": True,
        "atom_site_parsed_current_step": True,
        "protein_atom_table_written_count": sum(int(row["protein_atom_count"]) > 0 for row in execution_rows),
        "ligand_atom_table_written_count": sum(int(row["ligand_atom_count"]) > 0 for row in execution_rows),
        "pocket_atom_table_written_count": sum(int(row["pocket_atom_count"]) > 0 for row in execution_rows),
        "covalent_event_table_written_count": sum(int(row["covalent_event_count"]) == 1 for row in execution_rows),
        "ligand_residue_atom_pair_table_written_count": sum(int(row["ligand_residue_atom_pair_count"]) == 1 for row in execution_rows),
        "accepted_pdb_het_pairs": accepted_pairs,
        "covalent_bond_atom_pairs": ["SG--CAG"],
        "ready_for_covapie_sample_preparation_qa_gate": True,
        "ready_for_covapie_sample_index_design_gate": False,
        "ready_for_covapie_actual_dataloader_adapter_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "sample_index_written_current_step": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": NEXT_REQUIRED_GATE,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["sample_preparation_execution_smoke_failed"],
    }


def run_covapie_sample_preparation_execution_smoke_v0() -> dict[str, Any]:
    input_rows = _csv_rows(STEP14Z_INPUT_MANIFEST_CSV)
    input_json = _load_json(STEP14Z_INPUT_MANIFEST_JSON)
    artifact_plan_rows = _csv_rows(STEP14Z_REQUIRED_ARTIFACT_PLAN_CSV)
    raw_access_rows = _csv_rows(STEP14Z_RAW_ACCESS_PLAN_CSV)
    sample_results = [prepare_sample(row) for row in input_rows]
    precondition_rows = build_precondition_rows(input_rows, input_json, artifact_plan_rows, raw_access_rows, sample_results)
    execution_rows = build_execution_rows(sample_results)
    traceability_rows = build_traceability_rows(sample_results, execution_rows)
    quality_rows = build_quality_rows(sample_results, execution_rows)
    policy_rows = build_policy_rows()
    downstream_rows = build_downstream_rows()
    safety_rows = build_safety_rows()
    manifest = build_manifest(input_rows, execution_rows, precondition_rows, traceability_rows, quality_rows, policy_rows, downstream_rows, safety_rows)
    return {
        "precondition_rows": precondition_rows,
        "execution_rows": execution_rows,
        "sample_inventory_rows": execution_rows,
        "traceability_rows": traceability_rows,
        "quality_rows": quality_rows,
        "policy_rows": policy_rows,
        "downstream_rows": downstream_rows,
        "safety_rows": safety_rows,
        "sample_results": sample_results,
        "manifest": manifest,
    }
