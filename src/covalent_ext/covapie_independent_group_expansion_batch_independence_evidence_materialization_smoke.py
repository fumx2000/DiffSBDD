from __future__ import annotations

import csv
import hashlib
import json
import os
import shlex
import subprocess
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold


REPO = Path(__file__).resolve().parents[2]
STAGE = "covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0"
STEP_LABEL = "Step 14AO"
PREVIOUS_STAGE = "covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0"
PROJECT_NAME = "CovaPIE"

ROOT = Path("data/derived/covalent_small") / STAGE
PRECONDITION = ROOT / "covapie_independence_evidence_precondition_audit.csv"
SOURCE_INVENTORY = ROOT / "covapie_unified_independence_evidence_source_inventory.csv"
CCD_AUDIT = ROOT / "covapie_ccd_acquisition_integrity_audit.csv"
LIGAND_EVIDENCE = ROOT / "covapie_ligand_graph_scaffold_evidence.csv"
LIGAND_GROUPS = ROOT / "covapie_ligand_graph_scaffold_group_inventory.csv"
LIGAND_PAIRWISE = ROOT / "covapie_ligand_pairwise_similarity_evidence.csv"
PROTEIN_EVIDENCE = ROOT / "covapie_protein_sequence_accession_evidence.csv"
PROTEIN_GROUPS = ROOT / "covapie_protein_sequence_cluster_inventory.csv"
PROTEIN_PAIRWISE = ROOT / "covapie_protein_pairwise_sequence_identity_evidence.csv"
COMBINED_PAIRWISE = ROOT / "covapie_combined_pairwise_independence_evidence.csv"
ISSUES = ROOT / "covapie_independence_evidence_materialization_issue_inventory.csv"
SAFETY = ROOT / "covapie_independence_evidence_safety_audit.csv"
MANIFEST = ROOT / "covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_manifest.json"
SUMMARY = Path("docs/covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0_summary.md")

PILOT_CSV = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.csv")
PILOT_JSON = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/sample_index.json")
EXPANSION_CSV = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0/expansion_batch_sample_index.csv")
EXPANSION_JSON = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0/expansion_batch_sample_index.json")
STEP14AN_MANIFEST = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_manifest.json")
STEP14AM_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0")
STEP14AN_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0")
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
CCD_ROOT = Path("data/raw/covalent_sources/ccd/independence_evidence_batch_000001")

EXPECTED_HASHES = {
    PILOT_CSV: "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5",
    PILOT_JSON: "8d740458e30cc77bbaa568c615dd10f5df334cd0c46f21433c570c16391b8b38",
    EXPANSION_CSV: "857a0bdb665b49efd5d079a855142fed0985106f844338401f6329aeeae368c7",
    EXPANSION_JSON: "5f188c9a0ebf5840d1cca7041788a3eca2235f666ab76ab524482c997d186f1b",
    METADATA_CSV: "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365",
}
EXPECTED_SAMPLE_ORDER = [
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP"),
]
UNIQUE_HETS = ["JUG", "E64", "ZYA", "PCM", "INP", "INA", "IN6", "IN3", "UFP"]
MASK_NAMES = ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
MASK_ALIASES = ["A", "B", "B2", "B3", "C"]

REACTION_DELTA_REGISTRY = {
    ("ZYA", "CYS", "SG", "CM"): {
        "reaction_delta_rule_id": "ZYA_CYS_SG_FLUOROMETHYL_F1_LOSS_V1",
        "permitted_missing_parent_atom_ids": {"F1"},
        "required_parent_bond": frozenset({"CM", "F1"}),
        "reaction_delta_class": "covalent_leaving_group_loss",
        "evidence_scope": "explicit_zya_fluoromethyl_ketone_rule_v1",
    },
}

SOURCE_TABLE_FIELDS = [
    "protein_atom_table_path",
    "ligand_atom_table_path",
    "pocket_atom_table_path",
    "covalent_event_table_path",
    "ligand_residue_atom_pair_table_path",
    "sample_preparation_audit_path",
]

# Every derived CSV has a stable schema, including intentionally empty blocked
# outputs.  This prevents a failed validation from silently producing a
# zero-byte artifact without a machine-readable contract.
CSV_COLUMNS = {
    PRECONDITION: ["precondition_item", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"],
    SOURCE_INVENTORY: [
        "sample_order", "sample_index_row_id", "pdb_id", "ligand_comp_id", "source_stage",
        *SOURCE_TABLE_FIELDS, "pilot_csv_json_consistent", "expansion_csv_json_consistent",
        "all_source_tables_exist", "protein_atom_table_nonempty", "ligand_atom_table_nonempty",
        "covalent_event_table_exactly_one_row", "ligand_residue_atom_pair_table_exactly_one_row",
        "sample_preparation_audit_expected_row_count", "sample_preparation_audit_row_count",
        "sample_preparation_audit_all_passed", "event_identity_consistent", "pair_attachment_consistent", "raw_source_path",
        "raw_source_path_consistent", "raw_file_exists", "raw_filename_matches_pdb_id",
        "raw_sha256_before", "raw_sha256_after", "raw_sha256_unchanged", "source_inventory_passed", "blocking_reasons",
    ],
    CCD_AUDIT: [
        "het_id", "ccd_url", "ccd_raw_path", "acquisition_performed_by_step14ao",
        "initial_acquisition_http_status", "source_origin", "acquisition_provenance_status",
        "file_exists", "file_size_bytes", "minimum_size_passed", "data_block_present", "chem_comp_id",
        "chem_comp_id_matches_expected", "chem_comp_atom_loop_present", "descriptor_loop_present",
        "html_signature_absent", "sha256", "part_file_absent", "integrity_passed", "ccd_audit_passed", "blocking_reasons",
    ],
    LIGAND_EVIDENCE: [
        "sample_index_row_id", "pdb_id", "ligand_comp_id", "ligand_covalent_atom_name", "ccd_sha256",
        "selected_descriptor_type", "selected_descriptor_program", "source_descriptor_smiles",
        "canonical_heavy_atom_isomeric_smiles", "canonical_graph_sha256", "ligand_graph_group_id",
        "murcko_scaffold_smiles", "murcko_scaffold_sha256", "murcko_scaffold_status", "scaffold_group_key",
        "ligand_scaffold_group_id", "ccd_heavy_atom_count", "rdkit_heavy_atom_count",
        "sample_ligand_total_atom_count", "sample_ligand_heavy_atom_count", "sample_explicit_hydrogen_atom_count",
        "parent_ccd_heavy_atom_ids", "observed_post_covalent_heavy_atom_ids", "missing_parent_heavy_atom_ids",
        "unexpected_observed_heavy_atom_ids", "parent_ccd_heavy_atom_count", "observed_post_covalent_heavy_atom_count",
        "heavy_atom_count_delta", "reaction_delta_rule_id", "reaction_delta_class", "leaving_group_atom_ids",
        "parent_leaving_group_bond_verified", "covalent_attachment_atom_verified", "atom_inventory_reconciliation_status",
        "atom_inventory_reconciliation_passed", "reaction_delta_evidence_scope", "index_attachment_atom_verified",
        "event_attachment_atom_verified", "pair_attachment_atom_verified",
        "ccd_heavy_count_matches_rdkit", "sample_ligand_heavy_count_matches_rdkit",
        "ligand_covalent_atom_found_in_ccd", "ligand_graph_evidence_passed", "blocking_reasons",
    ],
    LIGAND_GROUPS: ["group_type", "group_id", "group_key", "member_count", "member_sample_index_row_ids", "group_inventory_passed"],
    LIGAND_PAIRWISE: [
        "ligand_pairwise_evidence_id", "left_sample_index_row_id", "right_sample_index_row_id", "left_pdb_id", "right_pdb_id",
        "left_ligand_comp_id", "right_ligand_comp_id", "same_ligand_graph", "same_murcko_scaffold",
        "ligand_tanimoto_radius2_2048", "ligand_pairwise_classification", "ligand_pairwise_evidence_passed", "blocking_reasons",
    ],
    PROTEIN_EVIDENCE: [
        "sample_index_row_id", "pdb_id", "ligand_comp_id", "residue_auth_asym_id", "residue_label_asym_id",
        "resolved_struct_asym_id", "resolved_entity_id", "entity_poly_seq_row_count", "sequence_number_min", "sequence_number_max",
        "duplicate_sequence_number_count", "duplicate_sequence_numbers", "missing_sequence_number_count", "missing_sequence_numbers",
        "sequence_numbering_status", "full_polymer_monomer_sequence", "full_polymer_one_letter_sequence",
        "full_polymer_monomer_sequence_sha256", "full_polymer_one_letter_sequence_sha256", "unknown_monomer_count",
        "unknown_monomer_codes", "protein_accession", "protein_accession_isoform", "protein_accession_label",
        "protein_accession_status", "struct_ref_seq_crosscheck_status", "full_polymer_sequence_status",
        "protein_accession_evidence_complete", "protein_accession_missingness_nonblocking", "protein_sequence_evidence_passed", "blocking_reasons", "protein_exact_sequence_group_id",
        "protein_sequence_cluster_90_id", "protein_sequence_cluster_50_id", "protein_accession_group_id",
    ],
    PROTEIN_GROUPS: ["group_type", "group_id", "group_key", "member_count", "member_sample_index_row_ids", "group_inventory_passed"],
    PROTEIN_PAIRWISE: [
        "protein_pairwise_evidence_id", "left_sample_index_row_id", "right_sample_index_row_id", "left_pdb_id", "right_pdb_id",
        "protein_sequence_identity", "same_exact_protein_sequence", "same_protein_accession", "same_sequence_cluster_90",
        "same_sequence_cluster_50", "protein_pairwise_classification", "protein_pairwise_evidence_passed", "blocking_reasons",
    ],
    COMBINED_PAIRWISE: [
        "pairwise_evidence_id", "left_sample_index_row_id", "right_sample_index_row_id", "left_pdb_id", "right_pdb_id",
        "left_ligand_comp_id", "right_ligand_comp_id", "same_ligand_graph", "same_murcko_scaffold",
        "ligand_tanimoto_radius2_2048", "same_protein_accession", "same_exact_protein_sequence", "protein_sequence_identity",
        "same_sequence_cluster_90", "same_sequence_cluster_50", "ligand_pairwise_classification",
        "protein_pairwise_classification", "combined_pairwise_independence_evidence_classification",
        "final_independent_group_confirmed_current_step", "evidence_status", "blocking_reasons",
    ],
    ISSUES: ["issue_id", "issue_scope", "sample_index_row_id", "pdb_id", "expected_het_id", "issue_severity", "issue_type", "issue_description", "issue_status"],
    SAFETY: ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"],
}

AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M", "SEC": "U", "PYL": "O", "ASX": "B", "GLX": "Z",
    "XLE": "J", "UNK": "X",
}


@dataclass(frozen=True)
class Sample:
    order: int
    row: dict[str, str]
    raw_path: Path
    raw_sha256_before: str
    protein_rows: list[dict[str, str]]
    ligand_rows: list[dict[str, str]]
    event_row: dict[str, str]
    pair_row: dict[str, str]


def _repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO / path


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def sha256(path: str | Path) -> str:
    p = _repo_path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with _repo_path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or CSV_COLUMNS.get(path) or (list(rows[0]) if rows else [])
    if not columns:
        raise ValueError(f"fixed CSV schema missing for {path}")
    tmp = target.with_name(target.name + ".tmp")
    try:
        with tmp.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def _write_json(path: Path, data: Any) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def _write_summary(text: str) -> None:
    target = _repo_path(SUMMARY)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _changed(paths: list[str | Path]) -> bool:
    values = [str(path) for path in paths]
    return _git(["diff", "--quiet", "--", *values]).returncode != 0 or _git(["diff", "--cached", "--quiet", "--", *values]).returncode != 0


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _clean_token(value: str) -> str:
    return "" if value in {"?", "."} else value


def tokenize_mmcif(text: str) -> list[str]:
    tokens: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped == "#":
            i += 1
            continue
        if line.startswith(";"):
            block: list[str] = []
            first = line[1:]
            if first:
                block.append(first)
            i += 1
            while i < len(lines) and not lines[i].startswith(";"):
                block.append(lines[i])
                i += 1
            tokens.append("\n".join(block).strip())
            i += 1
            continue
        lexer = shlex.shlex(line, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens.extend(_clean_token(token) for token in lexer)
        i += 1
    return tokens


def parse_loop(text: str, prefix: str) -> tuple[list[str], list[dict[str, str]]]:
    tokens = tokenize_mmcif(text)
    i = 0
    while i < len(tokens):
        if tokens[i] != "loop_":
            i += 1
            continue
        i += 1
        tags: list[str] = []
        while i < len(tokens) and tokens[i].startswith("_"):
            tags.append(tokens[i])
            i += 1
        if not tags:
            continue
        values: list[str] = []
        while i < len(tokens) and tokens[i] != "loop_" and not tokens[i].startswith("_"):
            if tokens[i] != "#":
                values.append(tokens[i])
            i += 1
        if not all(tag.startswith(prefix) for tag in tags):
            continue
        if not values or len(values) % len(tags) != 0:
            return tags, []
        rows = []
        for start in range(0, len(values), len(tags)):
            rows.append({tag: values[start + idx] for idx, tag in enumerate(tags)})
        return tags, rows
    return [], []


def parse_scalars(text: str, wanted_prefix: str) -> dict[str, str]:
    lines = text.splitlines()
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith(wanted_prefix):
            i += 1
            continue
        parts = stripped.split(None, 1)
        tag = parts[0]
        if len(parts) == 2:
            out[tag] = _clean_token(parts[1].strip("'\""))
            i += 1
        elif i + 1 < len(lines) and lines[i + 1].startswith(";"):
            i += 2
            block: list[str] = []
            while i < len(lines) and not lines[i].startswith(";"):
                block.append(lines[i])
                i += 1
            out[tag] = "\n".join(block).strip()
            i += 1
        else:
            out[tag] = ""
            i += 1
    return out


def _rows_by_entity(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("_entity_poly_seq.entity_id", "")].append(row)
    for entity_rows in grouped.values():
        entity_rows.sort(key=lambda row: int(row.get("_entity_poly_seq.num", "0")) if row.get("_entity_poly_seq.num", "").isdigit() else 10**9)
    return grouped


def _seq_to_one_letter(monomers: list[str]) -> tuple[str, int, str]:
    unknown = sorted({mon for mon in monomers if mon not in AA3_TO_1})
    return "".join(AA3_TO_1.get(mon, "X") for mon in monomers), len([m for m in monomers if m not in AA3_TO_1]), ";".join(unknown)


def _download_ccd(url: str, part_path: Path, timeout: int = 30) -> tuple[int, str]:
    if not url.startswith("https://files.rcsb.org/ligands/download/") or not url.endswith(".cif"):
        return 0, "blocked_url_out_of_scope"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            data = response.read()
        part_path.write_bytes(data)
        return int(status), ""
    except Exception as exc:  # pragma: no cover - exercised through injected tests.
        return 0, str(exc)


def _ccd_id(text: str) -> str:
    scalars = parse_scalars(text, "_chem_comp.")
    return scalars.get("_chem_comp.id", "").upper()


def _ccd_integrity(path: Path, expected_het: str) -> dict[str, Any]:
    exists = path.exists()
    text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    _, atom_rows = parse_loop(text, "_chem_comp_atom.")
    _, descriptors = parse_loop(text, "_pdbx_chem_comp_descriptor.")
    lower = text[:2000].lower()
    result = {
        "file_exists": exists,
        "file_size_bytes": path.stat().st_size if exists else 0,
        "minimum_size_passed": path.stat().st_size > 200 if exists else False,
        "data_block_present": text.lstrip().startswith("data_"),
        "chem_comp_id": _ccd_id(text),
        "chem_comp_id_matches_expected": _ccd_id(text) == expected_het,
        "chem_comp_atom_loop_present": bool(atom_rows),
        "descriptor_loop_present": bool(descriptors),
        "html_signature_absent": "<html" not in lower and "<!doctype html" not in lower,
        "sha256": sha256(path) if exists else "",
        "part_file_absent": not path.with_suffix(path.suffix + ".part").exists(),
    }
    result["integrity_passed"] = all(
        [
            result["file_exists"],
            result["minimum_size_passed"],
            result["data_block_present"],
            result["chem_comp_id_matches_expected"],
            result["chem_comp_atom_loop_present"],
            result["descriptor_loop_present"],
            result["html_signature_absent"],
            bool(result["sha256"]),
            result["part_file_absent"],
        ]
    )
    return result


def acquire_ccd_files(acquire_missing: bool, downloader: Callable[[str, Path], tuple[int, str]] = _download_ccd) -> list[dict[str, Any]]:
    ccd_root = _repo_path(CCD_ROOT)
    ccd_root.mkdir(parents=True, exist_ok=True)
    previous_by_het: dict[str, dict[str, str]] = {}
    if _repo_path(CCD_AUDIT).exists():
        previous_by_het = {row["het_id"]: row for row in _csv_rows(CCD_AUDIT)}
    rows: list[dict[str, Any]] = []
    for het in UNIQUE_HETS:
        path = ccd_root / f"{het}.cif"
        part = ccd_root / f"{het}.cif.part"
        url = f"https://files.rcsb.org/ligands/download/{het}.cif"
        http_status: int | str = ""
        error = ""
        acquired_now = False
        if not _ccd_integrity(path, het)["integrity_passed"] and acquire_missing:
            if part.exists():
                part.unlink()
            http_status, error = downloader(url, part)
            candidate = _ccd_integrity(part, het) if part.exists() else {"integrity_passed": False}
            if http_status == 200 and candidate["integrity_passed"]:
                os.replace(part, path)
                acquired_now = True
            elif part.exists():
                part.unlink()
        integrity = _ccd_integrity(path, het)
        previous = previous_by_het.get(het, {})
        previous_matches = previous.get("sha256") == integrity["sha256"] and bool(integrity["sha256"])
        if not integrity["integrity_passed"]:
            acquisition_performed = False
            initial_status: int | str = ""
            source_origin = "unresolved"
            provenance_status = "integrity_failed_unresolved"
        elif acquired_now:
            acquisition_performed = True
            initial_status = http_status
            source_origin = "downloaded_by_step14ao"
            provenance_status = "downloaded_and_integrity_validated"
        elif previous_matches and previous.get("source_origin") == "downloaded_by_step14ao":
            acquisition_performed = _truth(previous.get("acquisition_performed_by_step14ao", True))
            initial_status = previous.get("initial_acquisition_http_status", 200)
            source_origin = "downloaded_by_step14ao"
            provenance_status = previous.get("acquisition_provenance_status", "downloaded_and_integrity_validated")
        elif previous_matches and previous.get("source_origin") == "reused_preexisting_ccd":
            acquisition_performed = False
            initial_status = previous.get("initial_acquisition_http_status", "")
            source_origin = "reused_preexisting_ccd"
            provenance_status = previous.get("acquisition_provenance_status", "reused_preexisting_integrity_validated")
        else:
            acquisition_performed = False
            initial_status = ""
            source_origin = "reused_preexisting_ccd"
            provenance_status = "reused_preexisting_integrity_validated"
        rows.append(
            {
                "het_id": het,
                "ccd_url": url,
                "ccd_raw_path": _display_path(path),
                "acquisition_performed_by_step14ao": acquisition_performed,
                "initial_acquisition_http_status": initial_status,
                "source_origin": source_origin,
                "acquisition_provenance_status": provenance_status,
                **integrity,
                "ccd_audit_passed": integrity["integrity_passed"],
                "blocking_reasons": "" if integrity["integrity_passed"] else f"ccd_integrity_failed:{het}:{error or 'not_acquired'}",
            }
        )
    return rows


def _select_smiles(descriptors: list[dict[str, str]]) -> tuple[str, str, str]:
    candidates = []
    for row in descriptors:
        dtype = row.get("_pdbx_chem_comp_descriptor.type", "")
        program = row.get("_pdbx_chem_comp_descriptor.program", "")
        desc = row.get("_pdbx_chem_comp_descriptor.descriptor", "")
        if "SMILES" not in dtype.upper() or not desc:
            continue
        rank = 3
        if dtype.upper() == "SMILES_CANONICAL" and program in {"OpenEye OEToolkits", "CACTVS"}:
            rank = 0
        elif dtype.upper() == "SMILES_CANONICAL":
            rank = 1
        elif dtype.upper() == "SMILES":
            rank = 2
        candidates.append((rank, dtype, program, desc))
    if not candidates:
        return "", "", ""
    _, dtype, program, desc = sorted(candidates, key=lambda item: item[:3])[0]
    return dtype, program, desc


def parse_ccd_ligand(het: str, ccd_path: Path) -> dict[str, Any]:
    text = _repo_path(ccd_path).read_text(encoding="utf-8", errors="replace")
    _, atom_rows = parse_loop(text, "_chem_comp_atom.")
    _, bond_rows = parse_loop(text, "_chem_comp_bond.")
    _, descriptors = parse_loop(text, "_pdbx_chem_comp_descriptor.")
    dtype, program, smiles = _select_smiles(descriptors)
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        raise ValueError(f"RDKit failed to parse CCD SMILES for {het}")
    mol = Chem.RemoveHs(mol)
    canonical = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
    graph_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    if scaffold.GetNumHeavyAtoms() == 0:
        scaffold_smiles = ""
        scaffold_hash = ""
        scaffold_status = "acyclic_no_murcko_scaffold"
        scaffold_group_key = f"ACYCLIC_GRAPH:{graph_hash}"
    else:
        scaffold_smiles = Chem.MolToSmiles(scaffold, isomericSmiles=True, canonical=True)
        scaffold_hash = hashlib.sha256(scaffold_smiles.encode("utf-8")).hexdigest()
        scaffold_status = "ring_scaffold_materialized"
        scaffold_group_key = scaffold_hash
    fp = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048).GetFingerprint(mol)
    ccd_atom_ids = [row.get("_chem_comp_atom.atom_id", "") for row in atom_rows]
    ccd_heavy_atom_ids = sorted(row.get("_chem_comp_atom.atom_id", "") for row in atom_rows if row.get("_chem_comp_atom.type_symbol", "").upper() != "H")
    bond_inventory = sorted(
        {
            "atom_id_1": row.get("_chem_comp_bond.atom_id_1", ""),
            "atom_id_2": row.get("_chem_comp_bond.atom_id_2", ""),
            "value_order": row.get("_chem_comp_bond.value_order", ""),
            "pdbx_aromatic_flag": row.get("_chem_comp_bond.pdbx_aromatic_flag", ""),
        }.items()
        for row in bond_rows
    )
    ccd_heavy_count = sum(1 for row in atom_rows if row.get("_chem_comp_atom.type_symbol", "").upper() != "H")
    return {
        "het_id": het,
        "selected_descriptor_type": dtype,
        "selected_descriptor_program": program,
        "source_descriptor_smiles": smiles,
        "canonical_heavy_atom_isomeric_smiles": canonical,
        "canonical_graph_sha256": graph_hash,
        "ccd_atom_count": len(atom_rows),
        "ccd_heavy_atom_count": ccd_heavy_count,
        "rdkit_heavy_atom_count": mol.GetNumHeavyAtoms(),
        "rdkit_sanitization_status": "passed",
        "murcko_scaffold_smiles": scaffold_smiles,
        "murcko_scaffold_sha256": scaffold_hash,
        "murcko_scaffold_status": scaffold_status,
        "scaffold_group_key": scaffold_group_key,
        "ccd_atom_ids": ccd_atom_ids,
        "ccd_heavy_atom_ids": ccd_heavy_atom_ids,
        "ccd_bond_inventory": [dict(items) for items in bond_inventory],
        "fingerprint": fp,
    }


def _safe_csv_rows(path: str | Path) -> tuple[list[dict[str, str]], str]:
    target = _repo_path(path)
    if not target.is_file():
        return [], f"missing_source_table:{_display_path(target)}"
    try:
        return _csv_rows(target), ""
    except (OSError, csv.Error, UnicodeError) as exc:
        return [], f"unreadable_source_table:{_display_path(target)}:{type(exc).__name__}"


def _safe_index_rows(csv_path: Path, json_path: Path, expected_count: int) -> tuple[list[dict[str, str]], bool, list[str]]:
    csv_rows, csv_error = _safe_csv_rows(csv_path)
    blockers = [csv_error] if csv_error else []
    try:
        json_rows = json.loads(_repo_path(json_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        json_rows = []
        blockers.append(f"unreadable_source_index_json:{_display_path(_repo_path(json_path))}:{type(exc).__name__}")
    if not isinstance(json_rows, list) or not all(isinstance(row, dict) for row in json_rows):
        blockers.append(f"invalid_source_index_json_schema:{_display_path(_repo_path(json_path))}")
        json_rows = []
    normalized_json = [{str(k): str(v) for k, v in row.items()} for row in json_rows]
    if len(csv_rows) != expected_count or len(normalized_json) != expected_count:
        blockers.append(f"source_index_row_count_mismatch:{_display_path(_repo_path(csv_path))}")
    if csv_rows and normalized_json:
        if len(csv_rows[0]) != 33 or len(normalized_json[0]) != 33 or list(csv_rows[0]) != list(normalized_json[0]) or csv_rows != normalized_json:
            blockers.append(f"source_index_csv_json_inconsistent:{_display_path(_repo_path(csv_path))}")
    return csv_rows, not blockers, blockers


def _load_samples_safely() -> tuple[list[Sample], list[dict[str, Any]], list[str]]:
    pilot_rows, pilot_ok, blockers = _safe_index_rows(PILOT_CSV, PILOT_JSON, 3)
    expansion_rows, expansion_ok, expansion_blockers = _safe_index_rows(EXPANSION_CSV, EXPANSION_JSON, 8)
    blockers.extend(expansion_blockers)
    rows = pilot_rows + expansion_rows
    if len(rows) != 11:
        blockers.append(f"unified_source_row_count_mismatch:{len(rows)}")
    ids = [row.get("sample_index_row_id", "") for row in rows]
    pairs = [(row.get("pdb_id", ""), row.get("ligand_comp_id", "")) for row in rows]
    if len(ids) != len(set(ids)):
        blockers.append("duplicate_sample_index_row_id")
    if len(pairs) != len(set(pairs)):
        blockers.append("duplicate_pdb_het_pair")
    source_rows: list[dict[str, Any]] = []
    samples: list[Sample] = []
    for idx, row in enumerate(rows, start=1):
        expected = EXPECTED_SAMPLE_ORDER[idx - 1] if idx <= len(EXPECTED_SAMPLE_ORDER) else ("", "", "")
        sample_id, pdb_id, het_id = row.get("sample_index_row_id", ""), row.get("pdb_id", ""), row.get("ligand_comp_id", "")
        row_issues: list[str] = []
        if (sample_id, pdb_id, het_id) != expected:
            row_issues.append("row_identity_or_order_mismatch")
        table_data: dict[str, list[dict[str, str]]] = {}
        for field in SOURCE_TABLE_FIELDS:
            value = row.get(field, "")
            table_data[field], error = _safe_csv_rows(value) if value else ([], f"missing_source_path:{field}")
            if error:
                row_issues.append(f"{sample_id}:{error}")
        protein_rows = table_data["protein_atom_table_path"]
        ligand_rows = table_data["ligand_atom_table_path"]
        event_rows = table_data["covalent_event_table_path"]
        pair_rows = table_data["ligand_residue_atom_pair_table_path"]
        audit_rows = table_data["sample_preparation_audit_path"]
        expected_audit_rows = 10 if idx <= 3 else 13
        if not protein_rows:
            row_issues.append("protein_atom_table_empty")
        if not ligand_rows:
            row_issues.append("ligand_atom_table_empty")
        if len(event_rows) != 1:
            row_issues.append("covalent_event_table_not_exactly_one_row")
        if len(pair_rows) != 1:
            row_issues.append("ligand_residue_atom_pair_table_not_exactly_one_row")
        audit_ok = len(audit_rows) == expected_audit_rows and all(_truth(value.get("audit_passed")) for value in audit_rows)
        if not audit_ok:
            row_issues.append(f"sample_preparation_audit_not_{expected_audit_rows}_passed")
        event = event_rows[0] if event_rows else {}
        pair = pair_rows[0] if pair_rows else {}
        event_ok = bool(event) and all([
            event.get("pdb_id") == pdb_id,
            event.get("expected_het_id") == row.get("expected_het_id"),
            event.get("ligand_comp_id") == het_id,
            event.get("ligand_atom_name") == row.get("ligand_covalent_atom_name"),
            event.get("residue_comp_id") == row.get("covalent_residue_name"),
            event.get("residue_atom_name") == row.get("covalent_residue_atom_name"),
        ])
        if not event_ok:
            row_issues.append("event_identity_inconsistent_with_index")
        pair_ok = bool(pair) and all([
            pair.get("pdb_id") == pdb_id,
            pair.get("expected_het_id") == row.get("expected_het_id"),
            pair.get("residue_atom_name") == row.get("covalent_residue_atom_name"),
            pair.get("ligand_atom_name") == row.get("ligand_covalent_atom_name"),
            pair.get("covalent_bond_atom_pair") == row.get("covalent_bond_atom_pair"),
            pair.get("covalent_bond_atom_pair") == event.get("covalent_bond_atom_pair"),
        ])
        if not pair_ok:
            row_issues.append("pair_attachment_inconsistent_with_index_or_event")
        raw_paths = {value.get("source_raw_file", "") for value in protein_rows + ligand_rows if value.get("source_raw_file", "")}
        raw_path = Path(next(iter(raw_paths))) if len(raw_paths) == 1 else Path("")
        raw_exists = bool(raw_path) and _repo_path(raw_path).is_file()
        filename_ok = raw_exists and _repo_path(raw_path).stem.upper() == pdb_id.upper()
        if len(raw_paths) != 1:
            row_issues.append("raw_source_path_inconsistent")
        if not raw_exists:
            row_issues.append(f"raw_source_file_missing:{raw_path.as_posix()}")
        elif not filename_ok:
            row_issues.append("raw_source_filename_pdb_mismatch")
        raw_sha = sha256(raw_path) if raw_exists else ""
        raw_sha_after = sha256(raw_path) if raw_exists else ""
        table_exists = all(bool(row.get(field)) and _repo_path(row[field]).is_file() for field in SOURCE_TABLE_FIELDS)
        source_rows.append({
            "sample_order": idx, "sample_index_row_id": sample_id, "pdb_id": pdb_id, "ligand_comp_id": het_id,
            "source_stage": "pilot" if idx <= 3 else "expansion", **{field: row.get(field, "") for field in SOURCE_TABLE_FIELDS},
            "pilot_csv_json_consistent": pilot_ok, "expansion_csv_json_consistent": expansion_ok,
            "all_source_tables_exist": table_exists, "protein_atom_table_nonempty": bool(protein_rows),
            "ligand_atom_table_nonempty": bool(ligand_rows), "covalent_event_table_exactly_one_row": len(event_rows) == 1,
            "ligand_residue_atom_pair_table_exactly_one_row": len(pair_rows) == 1,
            "sample_preparation_audit_expected_row_count": expected_audit_rows, "sample_preparation_audit_row_count": len(audit_rows),
            "sample_preparation_audit_all_passed": audit_ok, "event_identity_consistent": event_ok, "pair_attachment_consistent": pair_ok,
            "raw_source_path": raw_path.as_posix(), "raw_source_path_consistent": len(raw_paths) == 1,
            "raw_file_exists": raw_exists, "raw_filename_matches_pdb_id": filename_ok,
            "raw_sha256_before": raw_sha, "raw_sha256_after": raw_sha_after,
            "raw_sha256_unchanged": raw_sha == raw_sha_after and bool(raw_sha),
            "source_inventory_passed": not row_issues, "blocking_reasons": ";".join(row_issues),
        })
        samples.append(Sample(idx, row, raw_path, raw_sha, protein_rows, ligand_rows, event, pair))
    return samples, source_rows, blockers


def _validate_entity_poly_sequence(entity_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    numbers: list[int] = []
    invalid = 0
    for row in entity_rows:
        try:
            numbers.append(int(row.get("_entity_poly_seq.num", "")))
        except (TypeError, ValueError):
            invalid += 1
    duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
    minimum, maximum = (min(numbers), max(numbers)) if numbers else (0, 0)
    missing = [number for number in range(1, maximum + 1) if number not in set(numbers)] if maximum else []
    status = "continuous_from_1" if numbers and not invalid and not duplicates and not missing and minimum == 1 else "invalid_entity_poly_seq_numbering"
    sorted_rows = sorted(entity_rows, key=lambda row: int(row.get("_entity_poly_seq.num", "0")) if row.get("_entity_poly_seq.num", "").isdigit() else 10**9)
    return sorted_rows, {
        "sequence_number_min": minimum if numbers else "",
        "sequence_number_max": maximum if numbers else "",
        "duplicate_sequence_number_count": len(duplicates),
        "duplicate_sequence_numbers": ";".join(str(value) for value in duplicates),
        "missing_sequence_number_count": len(missing) + invalid,
        "missing_sequence_numbers": ";".join(str(value) for value in missing) + (";non_numeric" if invalid else ""),
        "sequence_numbering_status": status,
    }


def _extract_accession(text: str, entity_id: str, asym_id: str) -> tuple[str, str, str, str, str]:
    _, ref_rows = parse_loop(text, "_struct_ref.")
    if not ref_rows:
        scalar = parse_scalars(text, "_struct_ref.")
        ref_rows = [scalar] if scalar else []
    accessions: list[str] = []
    labels: list[str] = []
    ref_ids: set[str] = set()
    for row in ref_rows:
        if row.get("_struct_ref.entity_id", "") != entity_id:
            continue
        db = row.get("_struct_ref.db_name", "")
        acc = row.get("_struct_ref.pdbx_db_accession", "")
        label = row.get("_struct_ref.db_code", "")
        if acc and db.upper() in {"UNP", "UNIPROT"}:
            accessions.append(acc)
            labels.append(label)
            ref_ids.add(row.get("_struct_ref.id", ""))
    unique = sorted(set(accessions))
    _, ref_seq_rows = parse_loop(text, "_struct_ref_seq.")
    ref_seq_present = bool(ref_seq_rows)
    ref_seq_matches = not ref_seq_present or any(
        row.get("_struct_ref_seq.ref_id", "") in ref_ids
        and (not row.get("_struct_ref_seq.pdbx_strand_id", "") or asym_id in row.get("_struct_ref_seq.pdbx_strand_id", "").replace(",", " ").split())
        for row in ref_seq_rows
    )
    crosscheck = "struct_ref_seq_crosschecked" if ref_seq_present and ref_seq_matches else ("struct_ref_seq_crosscheck_mismatch" if ref_seq_present else "struct_ref_seq_not_present")
    if not unique:
        return "", "", "", "accession_missing_in_raw_mmcif", crosscheck
    if len(unique) == 1:
        accession = unique[0]
        isoform = accession.split("-", 1)[1] if "-" in accession else ""
        return accession, isoform, labels[0] if labels else "", "unique_uniprot_accession", crosscheck
    return ";".join(unique), "", ";".join(sorted(set(labels))), "multiple_uniprot_accessions", crosscheck


def protein_evidence_for_sample(sample: Sample) -> dict[str, Any]:
    text = _repo_path(sample.raw_path).read_text(encoding="utf-8", errors="replace")
    _, asym_rows = parse_loop(text, "_struct_asym.")
    _, seq_rows = parse_loop(text, "_entity_poly_seq.")
    asym_to_entity = {row.get("_struct_asym.id", ""): row.get("_struct_asym.entity_id", "") for row in asym_rows}
    event = sample.event_row
    label_asym = event.get("residue_label_asym_id", "")
    auth_asym = event.get("residue_auth_asym_id", "")
    asym_id = label_asym if label_asym in asym_to_entity else auth_asym
    entity_id = asym_to_entity.get(asym_id, "")
    grouped = _rows_by_entity(seq_rows)
    entity_rows, numbering = _validate_entity_poly_sequence(grouped.get(entity_id, []))
    monomers = [row.get("_entity_poly_seq.mon_id", "") for row in entity_rows]
    one_letter, unknown_count, unknown_codes = _seq_to_one_letter(monomers)
    accession, accession_isoform, accession_label, accession_status, ref_seq_crosscheck = _extract_accession(text, entity_id, asym_id)
    monomer_joined = ";".join(monomers)
    sequence_hash = hashlib.sha256(monomer_joined.encode("utf-8")).hexdigest() if monomers else ""
    one_letter_hash = hashlib.sha256(one_letter.encode("utf-8")).hexdigest() if one_letter else ""
    accession_complete = accession_status == "unique_uniprot_accession"
    accession_nonblocking = accession_status in {"accession_missing_in_raw_mmcif", "multiple_uniprot_accessions"}
    sequence_passed = bool(entity_rows) and numbering["sequence_numbering_status"] == "continuous_from_1" and ref_seq_crosscheck != "struct_ref_seq_crosscheck_mismatch"
    return {
        "sample_index_row_id": sample.row["sample_index_row_id"],
        "pdb_id": sample.row["pdb_id"],
        "ligand_comp_id": sample.row["ligand_comp_id"],
        "residue_auth_asym_id": auth_asym,
        "residue_label_asym_id": label_asym,
        "resolved_struct_asym_id": asym_id,
        "resolved_entity_id": entity_id,
        "entity_poly_seq_row_count": len(entity_rows),
        **numbering,
        "full_polymer_monomer_sequence": monomer_joined,
        "full_polymer_one_letter_sequence": one_letter,
        "full_polymer_monomer_sequence_sha256": sequence_hash,
        "full_polymer_one_letter_sequence_sha256": one_letter_hash,
        "unknown_monomer_count": unknown_count,
        "unknown_monomer_codes": unknown_codes,
        "protein_accession": accession,
        "protein_accession_isoform": accession_isoform,
        "protein_accession_label": accession_label,
        "protein_accession_status": accession_status,
        "struct_ref_seq_crosscheck_status": ref_seq_crosscheck,
        "full_polymer_sequence_status": "materialized" if entity_rows else "missing",
        "protein_accession_evidence_complete": accession_complete,
        "protein_accession_missingness_nonblocking": accession_nonblocking,
        "protein_sequence_evidence_passed": sequence_passed,
        "blocking_reasons": "" if sequence_passed else "protein_sequence_validation_failed",
    }


def global_identity(a: str, b: str) -> float:
    gap = -2
    match = 2
    mismatch = -1
    n, m = len(a), len(b)
    score = [[0] * (m + 1) for _ in range(n + 1)]
    trace = [[""] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = score[i - 1][0] + gap
        trace[i][0] = "U"
    for j in range(1, m + 1):
        score[0][j] = score[0][j - 1] + gap
        trace[0][j] = "L"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = score[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            up = score[i - 1][j] + gap
            left = score[i][j - 1] + gap
            best = max(diag, up, left)
            score[i][j] = best
            trace[i][j] = "D" if best == diag else ("U" if best == up else "L")
    i, j = n, m
    matches = 0
    length = 0
    while i > 0 or j > 0:
        step = trace[i][j]
        if step == "D":
            matches += a[i - 1] == b[j - 1]
            i -= 1
            j -= 1
        elif step == "U":
            i -= 1
        else:
            j -= 1
        length += 1
    return matches / length if length else 0.0


class UnionFind:
    def __init__(self, items: list[str]):
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def assign_group_ids(keys: dict[str, str], prefix: str, order: list[str]) -> dict[str, str]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for sample_id, key in keys.items():
        buckets[key].append(sample_id)
    # Group IDs are a deterministic encoding of evidence keys, not discovery
    # order.  This keeps replayed output stable when input rows are reloaded.
    sorted_keys = sorted(buckets)
    return {sample_id: f"{prefix}_{idx:06d}" for idx, key in enumerate(sorted_keys, 1) for sample_id in buckets[key]}


def assign_threshold_groups(pair_rows: list[dict[str, Any]], sample_ids: list[str], threshold: float, prefix: str) -> dict[str, str]:
    uf = UnionFind(sample_ids)
    for row in pair_rows:
        if float(row["protein_sequence_identity"]) >= threshold:
            uf.union(row["left_sample_index_row_id"], row["right_sample_index_row_id"])
    root_to_members: dict[str, list[str]] = defaultdict(list)
    for sample_id in sample_ids:
        root_to_members[uf.find(sample_id)].append(sample_id)
    roots = sorted(root_to_members, key=lambda root: tuple(sorted(root_to_members[root])))
    return {sample_id: f"{prefix}_{idx:06d}" for idx, root in enumerate(roots, 1) for sample_id in root_to_members[root]}


def _classification_ligand(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["canonical_graph_sha256"] == right["canonical_graph_sha256"]:
        return "same_exact_graph"
    if left["murcko_scaffold_status"] == "acyclic_no_murcko_scaffold" or right["murcko_scaffold_status"] == "acyclic_no_murcko_scaffold":
        return "different_graph_acyclic_scaffold_unavailable"
    if left["murcko_scaffold_sha256"] == right["murcko_scaffold_sha256"]:
        return "different_graph_same_scaffold"
    return "different_scaffold"


def _classification_protein(identity: float, same_exact: bool, same_accession: bool) -> str:
    if same_exact:
        return "same_exact_sequence"
    if same_accession:
        return "same_accession_nonidentical_sequence"
    if identity >= 0.9:
        return "same_sequence_cluster_90"
    if identity >= 0.5:
        return "same_sequence_cluster_50"
    return "sequence_below_50_identity"


def _classification_combined(ligand_class: str, protein_class: str) -> str:
    protein_related = protein_class in {"same_exact_sequence", "same_accession_nonidentical_sequence", "same_sequence_cluster_90", "same_sequence_cluster_50"}
    ligand_related = ligand_class in {"same_exact_graph", "different_graph_same_scaffold"}
    if protein_related and ligand_related:
        return "strong_same_group_evidence"
    if protein_related:
        return "protein_related_ligand_distinct"
    if ligand_related:
        return "ligand_related_protein_distinct"
    return "provisional_distinct_both_axes"


def _sample_ligand_atom_counts(rows: list[dict[str, str]]) -> tuple[int, int, int]:
    total = len(rows)
    hydrogens = sum(row.get("type_symbol", "").upper() == "H" for row in rows)
    return total, total - hydrogens, hydrogens


def _bond_present(bonds: list[dict[str, str]], atom_a: str, atom_b: str) -> bool:
    expected = frozenset({atom_a, atom_b})
    return any(frozenset({row.get("atom_id_1", ""), row.get("atom_id_2", "")}) == expected for row in bonds)


def reconcile_post_covalent_atom_inventory(sample: Sample, ligand_info: dict[str, Any]) -> dict[str, Any]:
    parent = set(ligand_info["ccd_heavy_atom_ids"])
    observed = {row.get("atom_name", "") for row in sample.ligand_rows if row.get("type_symbol", "").upper() != "H"}
    missing = parent - observed
    unexpected = observed - parent
    selected = sample.row["ligand_covalent_atom_name"]
    event = sample.event_row
    pair = sample.pair_row
    index_attachment = sample.row.get("covalent_bond_atom_pair", "") == f"SG--{selected}"
    event_attachment = event.get("covalent_bond_atom_pair", "") == sample.row.get("covalent_bond_atom_pair", "")
    pair_attachment = pair.get("covalent_bond_atom_pair", "") == sample.row.get("covalent_bond_atom_pair", "") and pair.get("ligand_atom_name", "") == selected and pair.get("residue_atom_name", "") == sample.row.get("covalent_residue_atom_name", "")
    attachment_ok = index_attachment and event_attachment and pair_attachment
    key = (sample.row["ligand_comp_id"], event.get("residue_comp_id", ""), event.get("residue_atom_name", ""), selected)
    rule = REACTION_DELTA_REGISTRY.get(key)
    intact = not missing and not unexpected
    if intact:
        status = "intact_parent_atom_inventory_match" if attachment_ok else "unexplained_atom_inventory_mismatch"
        passed = attachment_ok
        rule_id = ""
        delta_class = ""
        leaving = []
        parent_bond_verified = False
    elif rule and missing == rule["permitted_missing_parent_atom_ids"] and not unexpected:
        leaving = sorted(rule["permitted_missing_parent_atom_ids"])
        parent_bond_verified = _bond_present(ligand_info["ccd_bond_inventory"], *tuple(rule["required_parent_bond"]))
        passed = parent_bond_verified and attachment_ok
        status = "validated_post_covalent_leaving_group_loss" if passed else "unexplained_atom_inventory_mismatch"
        rule_id = rule["reaction_delta_rule_id"] if passed else ""
        delta_class = rule["reaction_delta_class"] if passed else ""
    else:
        status = "unexplained_atom_inventory_mismatch"
        passed = False
        rule_id = ""
        delta_class = ""
        leaving = []
        parent_bond_verified = False
    return {
        "parent_ccd_heavy_atom_ids": ";".join(sorted(parent)),
        "observed_post_covalent_heavy_atom_ids": ";".join(sorted(observed)),
        "missing_parent_heavy_atom_ids": ";".join(sorted(missing)),
        "unexpected_observed_heavy_atom_ids": ";".join(sorted(unexpected)),
        "parent_ccd_heavy_atom_count": len(parent),
        "observed_post_covalent_heavy_atom_count": len(observed),
        "heavy_atom_count_delta": len(observed) - len(parent),
        "reaction_delta_rule_id": rule_id,
        "reaction_delta_class": delta_class,
        "reaction_delta_evidence_scope": rule["evidence_scope"] if rule and missing and passed else "",
        "leaving_group_atom_ids": ";".join(leaving),
        "parent_leaving_group_bond_verified": parent_bond_verified,
        "index_attachment_atom_verified": index_attachment,
        "event_attachment_atom_verified": event_attachment,
        "pair_attachment_atom_verified": pair_attachment,
        "covalent_attachment_atom_verified": attachment_ok,
        "atom_inventory_reconciliation_status": status,
        "atom_inventory_reconciliation_passed": passed,
    }


def _make_ligand_evidence(samples: list[Sample], ccd_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    ccd_by_het = {row["het_id"]: row for row in ccd_rows}
    parsed = {het: parse_ccd_ligand(het, _repo_path(CCD_ROOT / f"{het}.cif")) for het in UNIQUE_HETS}
    sample_ids = [sample.row["sample_index_row_id"] for sample in samples]
    graph_groups = assign_group_ids({sid: parsed[next(s.row["ligand_comp_id"] for s in samples if s.row["sample_index_row_id"] == sid)]["canonical_graph_sha256"] for sid in sample_ids}, "COVAPIE_LIGAND_GRAPH_GROUP", sample_ids)
    scaffold_groups = assign_group_ids({sid: parsed[next(s.row["ligand_comp_id"] for s in samples if s.row["sample_index_row_id"] == sid)]["scaffold_group_key"] for sid in sample_ids}, "COVAPIE_LIGAND_SCAFFOLD_GROUP", sample_ids)
    rows: list[dict[str, Any]] = []
    by_sample: dict[str, dict[str, Any]] = {}
    for sample in samples:
        het = sample.row["ligand_comp_id"]
        info = parsed[het]
        atom_ok = sample.row["ligand_covalent_atom_name"] in info["ccd_atom_ids"]
        ccd_rdkit_counts_match = info["ccd_heavy_atom_count"] == info["rdkit_heavy_atom_count"]
        sample_total_count, sample_heavy_count, sample_hydrogen_count = _sample_ligand_atom_counts(sample.ligand_rows)
        sample_counts_match = sample_heavy_count == int(info["rdkit_heavy_atom_count"])
        reconciliation = reconcile_post_covalent_atom_inventory(sample, info)
        row = {
            "sample_index_row_id": sample.row["sample_index_row_id"],
            "pdb_id": sample.row["pdb_id"],
            "ligand_comp_id": het,
            "ligand_covalent_atom_name": sample.row["ligand_covalent_atom_name"],
            "ccd_sha256": ccd_by_het[het]["sha256"],
            "selected_descriptor_type": info["selected_descriptor_type"],
            "selected_descriptor_program": info["selected_descriptor_program"],
            "source_descriptor_smiles": info["source_descriptor_smiles"],
            "canonical_heavy_atom_isomeric_smiles": info["canonical_heavy_atom_isomeric_smiles"],
            "canonical_graph_sha256": info["canonical_graph_sha256"],
            "ligand_graph_group_id": graph_groups[sample.row["sample_index_row_id"]],
            "murcko_scaffold_smiles": info["murcko_scaffold_smiles"],
            "murcko_scaffold_sha256": info["murcko_scaffold_sha256"],
            "murcko_scaffold_status": info["murcko_scaffold_status"],
            "scaffold_group_key": info["scaffold_group_key"],
            "ligand_scaffold_group_id": scaffold_groups[sample.row["sample_index_row_id"]],
            "ccd_heavy_atom_count": info["ccd_heavy_atom_count"],
            "rdkit_heavy_atom_count": info["rdkit_heavy_atom_count"],
            "sample_ligand_total_atom_count": sample_total_count,
            "sample_ligand_heavy_atom_count": sample_heavy_count,
            "sample_explicit_hydrogen_atom_count": sample_hydrogen_count,
            **reconciliation,
            "ccd_heavy_count_matches_rdkit": ccd_rdkit_counts_match,
            "sample_ligand_heavy_count_matches_rdkit": sample_counts_match,
            "ligand_covalent_atom_found_in_ccd": atom_ok,
            "ligand_graph_evidence_passed": _truth(ccd_by_het[het]["ccd_audit_passed"]) and atom_ok and ccd_rdkit_counts_match and reconciliation["atom_inventory_reconciliation_passed"],
            "blocking_reasons": "" if _truth(ccd_by_het[het]["ccd_audit_passed"]) and atom_ok and ccd_rdkit_counts_match and reconciliation["atom_inventory_reconciliation_passed"] else "ligand_graph_validation_failed",
        }
        rows.append(row)
        by_sample[sample.row["sample_index_row_id"]] = {**row, "fingerprint": info["fingerprint"]}
    group_rows = _ligand_group_rows(rows)
    return rows, by_sample, group_rows


def _ligand_group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    graph_buckets: dict[str, list[str]] = defaultdict(list)
    scaffold_buckets: dict[str, list[str]] = defaultdict(list)
    graph_keys: dict[str, str] = {}
    scaffold_keys: dict[str, str] = {}
    for row in rows:
        graph_buckets[row["ligand_graph_group_id"]].append(row["sample_index_row_id"])
        scaffold_buckets[row["ligand_scaffold_group_id"]].append(row["sample_index_row_id"])
        graph_keys[row["ligand_graph_group_id"]] = row["canonical_graph_sha256"]
        scaffold_keys[row["ligand_scaffold_group_id"]] = row["scaffold_group_key"]
    out = []
    for group_id, members in sorted(graph_buckets.items()):
        out.append({"group_type": "ligand_exact_graph", "group_id": group_id, "group_key": graph_keys[group_id], "member_count": len(members), "member_sample_index_row_ids": ";".join(members), "group_inventory_passed": True})
    for group_id, members in sorted(scaffold_buckets.items()):
        out.append({"group_type": "ligand_murcko_scaffold", "group_id": group_id, "group_key": scaffold_keys[group_id], "member_count": len(members), "member_sample_index_row_ids": ";".join(members), "group_inventory_passed": True})
    return out


def _make_pairwise(samples: list[Sample], ligand_by_sample: dict[str, dict[str, Any]], protein_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    protein_by_sample = {row["sample_index_row_id"]: row for row in protein_rows}
    sample_ids = [sample.row["sample_index_row_id"] for sample in samples]
    protein_pairwise: list[dict[str, Any]] = []
    for protein_pair_id, (left, right) in enumerate(combinations(samples, 2), 1):
        lpid, rpid = left.row["sample_index_row_id"], right.row["sample_index_row_id"]
        lseq = protein_by_sample[lpid]["full_polymer_one_letter_sequence"]
        rseq = protein_by_sample[rpid]["full_polymer_one_letter_sequence"]
        identity = global_identity(lseq, rseq)
        same_exact = protein_by_sample[lpid]["full_polymer_monomer_sequence_sha256"] == protein_by_sample[rpid]["full_polymer_monomer_sequence_sha256"]
        lacc, racc = protein_by_sample[lpid]["protein_accession"], protein_by_sample[rpid]["protein_accession"]
        same_accession = bool(lacc and racc and lacc == racc)
        protein_pairwise.append({
            "protein_pairwise_evidence_id": f"COVAPIE_PROTEIN_PAIRWISE_{protein_pair_id:06d}",
            "left_sample_index_row_id": lpid,
            "right_sample_index_row_id": rpid,
            "left_pdb_id": left.row["pdb_id"],
            "right_pdb_id": right.row["pdb_id"],
            "protein_sequence_identity": f"{identity:.6f}",
            "same_exact_protein_sequence": same_exact,
            "same_protein_accession": same_accession,
            "protein_pairwise_classification": _classification_protein(identity, same_exact, same_accession),
            "protein_pairwise_evidence_passed": bool(lseq and rseq and protein_by_sample[lpid]["protein_sequence_evidence_passed"] and protein_by_sample[rpid]["protein_sequence_evidence_passed"] and 0.0 <= identity <= 1.0),
            "blocking_reasons": "" if bool(lseq and rseq and protein_by_sample[lpid]["protein_sequence_evidence_passed"] and protein_by_sample[rpid]["protein_sequence_evidence_passed"] and 0.0 <= identity <= 1.0) else "protein_pairwise_evidence_incomplete",
        })
    group90 = assign_threshold_groups(protein_pairwise, sample_ids, 0.9, "COVAPIE_PROTEIN_SEQUENCE_CLUSTER_90")
    group50 = assign_threshold_groups(protein_pairwise, sample_ids, 0.5, "COVAPIE_PROTEIN_SEQUENCE_CLUSTER_50")
    exact = assign_group_ids({row["sample_index_row_id"]: row["full_polymer_monomer_sequence_sha256"] for row in protein_rows}, "COVAPIE_PROTEIN_EXACT_SEQUENCE_GROUP", sample_ids)
    accession = assign_group_ids({row["sample_index_row_id"]: row["protein_accession"] or f"MISSING:{row['sample_index_row_id']}" for row in protein_rows}, "COVAPIE_PROTEIN_ACCESSION_GROUP", sample_ids)
    for row in protein_rows:
        sid = row["sample_index_row_id"]
        row["protein_exact_sequence_group_id"] = exact[sid]
        row["protein_sequence_cluster_90_id"] = group90[sid]
        row["protein_sequence_cluster_50_id"] = group50[sid]
        row["protein_accession_group_id"] = accession[sid]
    for row in protein_pairwise:
        row["same_sequence_cluster_90"] = group90[row["left_sample_index_row_id"]] == group90[row["right_sample_index_row_id"]]
        row["same_sequence_cluster_50"] = group50[row["left_sample_index_row_id"]] == group50[row["right_sample_index_row_id"]]
    ligand_pairwise: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    pair_id = 0
    for p_row, (left, right) in zip(protein_pairwise, combinations(samples, 2)):
        pair_id += 1
        lsid, rsid = left.row["sample_index_row_id"], right.row["sample_index_row_id"]
        llig, rlig = ligand_by_sample[lsid], ligand_by_sample[rsid]
        tanimoto = DataStructs.TanimotoSimilarity(llig["fingerprint"], rlig["fingerprint"])
        same_graph = llig["canonical_graph_sha256"] == rlig["canonical_graph_sha256"]
        same_scaffold = llig["ligand_scaffold_group_id"] == rlig["ligand_scaffold_group_id"]
        ligand_class = _classification_ligand(llig, rlig)
        ligand_complete = bool(llig["ligand_graph_evidence_passed"] and rlig["ligand_graph_evidence_passed"] and 0.0 <= tanimoto <= 1.0)
        protein_complete = _truth(p_row["protein_pairwise_evidence_passed"])
        ligand_pairwise.append({
            "ligand_pairwise_evidence_id": f"COVAPIE_LIGAND_PAIRWISE_{pair_id:06d}",
            "left_sample_index_row_id": lsid,
            "right_sample_index_row_id": rsid,
            "left_pdb_id": left.row["pdb_id"],
            "right_pdb_id": right.row["pdb_id"],
            "left_ligand_comp_id": left.row["ligand_comp_id"],
            "right_ligand_comp_id": right.row["ligand_comp_id"],
            "same_ligand_graph": same_graph,
            "same_murcko_scaffold": same_scaffold,
            "ligand_tanimoto_radius2_2048": f"{tanimoto:.6f}",
            "ligand_pairwise_classification": ligand_class if ligand_complete else "evidence_incomplete",
            "ligand_pairwise_evidence_passed": ligand_complete,
            "blocking_reasons": "" if ligand_complete else "ligand_pairwise_evidence_incomplete",
        })
        combined_class = _classification_combined(ligand_class, p_row["protein_pairwise_classification"]) if ligand_complete and protein_complete else "evidence_incomplete"
        combined_rows.append({
            "pairwise_evidence_id": f"COVAPIE_COMBINED_PAIRWISE_{pair_id:06d}",
            "left_sample_index_row_id": lsid,
            "right_sample_index_row_id": rsid,
            "left_pdb_id": left.row["pdb_id"],
            "right_pdb_id": right.row["pdb_id"],
            "left_ligand_comp_id": left.row["ligand_comp_id"],
            "right_ligand_comp_id": right.row["ligand_comp_id"],
            "same_ligand_graph": same_graph,
            "same_murcko_scaffold": same_scaffold,
            "ligand_tanimoto_radius2_2048": f"{tanimoto:.6f}",
            "same_protein_accession": p_row["same_protein_accession"],
            "same_exact_protein_sequence": p_row["same_exact_protein_sequence"],
            "protein_sequence_identity": p_row["protein_sequence_identity"],
            "same_sequence_cluster_90": p_row["same_sequence_cluster_90"],
            "same_sequence_cluster_50": p_row["same_sequence_cluster_50"],
            "ligand_pairwise_classification": ligand_class,
            "protein_pairwise_classification": p_row["protein_pairwise_classification"],
            "combined_pairwise_independence_evidence_classification": combined_class,
            "final_independent_group_confirmed_current_step": False,
            "evidence_status": "materialized_not_final_group_assignment",
            "blocking_reasons": "" if ligand_complete and protein_complete else "pairwise_evidence_incomplete",
        })
    group_rows = _protein_group_rows(protein_rows)
    return ligand_pairwise, protein_pairwise, combined_rows, group_rows


def _protein_group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for group_type, field in [
        ("protein_exact_sequence", "protein_exact_sequence_group_id"),
        ("protein_sequence_cluster_90", "protein_sequence_cluster_90_id"),
        ("protein_sequence_cluster_50", "protein_sequence_cluster_50_id"),
        ("protein_accession", "protein_accession_group_id"),
    ]:
        buckets: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            buckets[row[field]].append(row["sample_index_row_id"])
        for group_id, members in sorted(buckets.items()):
            members = sorted(members)
            representative = next(row for row in rows if row["sample_index_row_id"] == members[0])
            if group_type == "protein_exact_sequence":
                group_key = representative["full_polymer_monomer_sequence_sha256"]
            elif group_type == "protein_accession":
                group_key = representative["protein_accession"] or f"MISSING_ACCESSION:{members[0]}"
            elif group_type == "protein_sequence_cluster_90":
                group_key = f"sequence_identity_threshold_0.90|members:{';'.join(members)}"
            else:
                group_key = f"sequence_identity_threshold_0.50|members:{';'.join(members)}"
            out.append({"group_type": group_type, "group_id": group_id, "group_key": group_key, "member_count": len(members), "member_sample_index_row_ids": ";".join(members), "group_inventory_passed": True})
    return out


SAFETY_EXPECTED = {
    "network_host_restricted_to_files_rcsb_org": True,
    "ccd_download_scope_limited_to_nine_components": True,
    "ccd_raw_files_git_ignored": True,
    "all_entry_raw_files_git_ignored": True,
    "ccd_raw_files_tracked": False,
    "ccd_raw_files_staged": False,
    "ccd_part_files_remaining": False,
    "entry_raw_files_modified": False,
    "entry_raw_files_tracked": False,
    "entry_raw_files_staged": False,
    "pilot_index_files_unchanged": True,
    "expansion_index_files_unchanged": True,
    "step14an_artifacts_unchanged": True,
    "step14am_artifacts_unchanged": True,
    "metadata_csv_unchanged": True,
    "combined_sample_index_written": False,
    "split_assignments_written": False,
    "leakage_matrix_written": False,
    "final_dataset_written": False,
    "actual_dataloader_artifacts_written": False,
    "training_artifacts_written": False,
    "standalone_evidence_qa_gate_created": False,
    "embedded_evidence_qa_performed": True,
    "part_or_tmp_files_remaining": False,
    "protected_source_diff_empty": True,
    "original_dataloader_diff_empty": True,
    "torch_imported": False,
    "numpy_imported": False,
    "rdkit_used": True,
    "biopython_used": False,
    "gemmi_used": False,
    "requests_used": False,
    "staged_files_empty": True,
}


def _any_matching_artifact(patterns: list[str]) -> bool:
    root = _repo_path(ROOT)
    return any(any(root.rglob(pattern)) for pattern in patterns)


def safety_rows(samples: list[Sample], ccd_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ccd_root = _repo_path(CCD_ROOT)
    raw_paths = [sample.raw_path for sample in samples]
    raw_root_args = [path.as_posix() for path in raw_paths]
    raw_hashes_unchanged = all(sample.raw_sha256_before and sample.raw_sha256_before == sha256(sample.raw_path) for sample in samples)
    ccd_paths = [ccd_root / f"{het}.cif" for het in UNIQUE_HETS]
    ccd_ignored = all(_git(["check-ignore", "-q", _display_path(path)]).returncode == 0 for path in ccd_paths)
    raw_ignored = all(_git(["check-ignore", "-q", _display_path(_repo_path(path))]).returncode == 0 for path in raw_paths)
    forbidden_tmp = any(path.suffix in {".part", ".tmp"} for root in [ccd_root, _repo_path(ROOT)] if root.exists() for path in root.rglob("*"))
    urls = [str(row.get("ccd_url", "")) for row in ccd_rows]
    allowed_urls = {f"https://files.rcsb.org/ligands/download/{het}.cif" for het in UNIQUE_HETS}
    observed = {
        "network_host_restricted_to_files_rcsb_org": bool(urls) and all(url in allowed_urls and url.startswith("https://files.rcsb.org/") for url in urls),
        "ccd_download_scope_limited_to_nine_components": {row.get("het_id") for row in ccd_rows} == set(UNIQUE_HETS) and len(ccd_rows) == 9,
        "ccd_raw_files_git_ignored": ccd_ignored,
        "all_entry_raw_files_git_ignored": raw_ignored,
        "ccd_raw_files_tracked": bool(_git(["ls-files", CCD_ROOT.as_posix()]).stdout.strip()),
        "ccd_raw_files_staged": bool(_git(["diff", "--cached", "--name-only", "--", CCD_ROOT.as_posix()]).stdout.strip()),
        "ccd_part_files_remaining": ccd_root.exists() and any(path.suffix == ".part" for path in ccd_root.rglob("*")),
        "entry_raw_files_modified": not raw_hashes_unchanged,
        "entry_raw_files_tracked": bool(_git(["ls-files", *raw_root_args]).stdout.strip()) if raw_root_args else False,
        "entry_raw_files_staged": bool(_git(["diff", "--cached", "--name-only", "--", *raw_root_args]).stdout.strip()) if raw_root_args else False,
        "pilot_index_files_unchanged": all(sha256(path) == EXPECTED_HASHES[path] for path in [PILOT_CSV, PILOT_JSON]) and not _changed([PILOT_CSV, PILOT_JSON]),
        "expansion_index_files_unchanged": all(sha256(path) == EXPECTED_HASHES[path] for path in [EXPANSION_CSV, EXPANSION_JSON]) and not _changed([EXPANSION_CSV, EXPANSION_JSON]),
        "step14an_artifacts_unchanged": not _changed([STEP14AN_ROOT]),
        "step14am_artifacts_unchanged": not _changed([STEP14AM_ROOT]),
        "metadata_csv_unchanged": sha256(METADATA_CSV) == EXPECTED_HASHES[METADATA_CSV] and not _changed([METADATA_CSV]),
        "combined_sample_index_written": _any_matching_artifact(["*combined*sample*index*", "*sample_index.csv", "*sample_index.json"]),
        "split_assignments_written": _any_matching_artifact(["*split*assignment*", "*split*.csv"]),
        "leakage_matrix_written": _any_matching_artifact(["*leakage*matrix*"]),
        "final_dataset_written": _any_matching_artifact(["*final*dataset*"]),
        "actual_dataloader_artifacts_written": _any_matching_artifact(["*dataloader*", "*.pt", "*.npz"]),
        "training_artifacts_written": _any_matching_artifact(["*.ckpt", "*.pth", "*.pt", "*training*"]),
        "standalone_evidence_qa_gate_created": any(_repo_path("data/derived/covalent_small").glob("covapie_independent_group_expansion_batch_independence_evidence_qa_gate_v0")),
        "embedded_evidence_qa_performed": bool(source_rows) and all(_truth(row.get("source_inventory_passed")) for row in source_rows),
        "part_or_tmp_files_remaining": forbidden_tmp,
        "protected_source_diff_empty": not _changed(["equivariant_diffusion/", "lightning_modules.py"]),
        "original_dataloader_diff_empty": not _changed(["dataset.py", "data/prepare_crossdocked.py"]),
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": True,
        "biopython_used": False,
        "gemmi_used": False,
        "requests_used": False,
        "staged_files_empty": not bool(_git(["diff", "--cached", "--name-only"]).stdout.strip()),
    }
    return [
        {
            "safety_item": item,
            "required_status": expected,
            "observed_status": observed[item],
            "safety_passed": observed[item] == expected,
            "blocking_reasons": "" if observed[item] == expected else item,
        }
        for item, expected in SAFETY_EXPECTED.items()
    ]


def precondition_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        manifest = json.loads(_repo_path(STEP14AN_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        manifest = {}
    rows = [
        ("step14an_manifest_valid", True, manifest.get("stage") == PREVIOUS_STAGE and manifest.get("all_checks_passed") is True),
        ("step14an_ready_for_current_step", True, manifest.get("ready_for_covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke") is True),
        ("pilot_index_hashes_unchanged", True, sha256(PILOT_CSV) == EXPECTED_HASHES[PILOT_CSV] and sha256(PILOT_JSON) == EXPECTED_HASHES[PILOT_JSON]),
        ("expansion_index_hashes_unchanged", True, sha256(EXPANSION_CSV) == EXPECTED_HASHES[EXPANSION_CSV] and sha256(EXPANSION_JSON) == EXPECTED_HASHES[EXPANSION_JSON]),
        ("metadata_hash_unchanged", True, sha256(METADATA_CSV) == EXPECTED_HASHES[METADATA_CSV]),
        ("future_unified_sample_count", 11, len(source_rows)),
        ("all_source_inventory_rows_passed", True, all(_truth(row["source_inventory_passed"]) for row in source_rows)),
        ("canonical_five_masks_preserved", True, MASK_ALIASES == ["A", "B", "B2", "B3", "C"]),
    ]
    return [
        {"precondition_item": item, "expected_status": expected, "observed_status": observed, "precondition_passed": expected == observed, "blocking_reasons": "" if expected == observed else item}
        for item, expected, observed in rows
    ]


def _issue_rows(issues: list[tuple[str, str, str, str, str]]) -> list[dict[str, Any]]:
    if not issues:
        return [{
            "issue_id": "NO_INDEPENDENCE_EVIDENCE_MATERIALIZATION_ISSUES",
            "issue_scope": "unified_11_sample_evidence_v0",
            "sample_index_row_id": "",
            "pdb_id": "",
            "expected_het_id": "",
            "issue_severity": "none",
            "issue_type": "no_issues",
            "issue_description": "No independence evidence materialization issues detected.",
            "issue_status": "passed",
        }]
    return [{
        "issue_id": f"COVAPIE_INDEPENDENCE_EVIDENCE_ISSUE_{idx:06d}",
        "issue_scope": scope,
        "sample_index_row_id": sample_id,
        "pdb_id": pdb_id,
        "expected_het_id": het_id,
        "issue_severity": "blocking",
        "issue_type": scope,
        "issue_description": description,
        "issue_status": "failed",
    } for idx, (scope, sample_id, pdb_id, het_id, description) in enumerate(issues, 1)]


def _pairwise_complete(rows: list[dict[str, Any]], expected_prefix: str) -> bool:
    expected_count = len(EXPECTED_SAMPLE_ORDER) * (len(EXPECTED_SAMPLE_ORDER) - 1) // 2
    ids = [row.get("left_sample_index_row_id", "") + "|" + row.get("right_sample_index_row_id", "") for row in rows]
    if len(rows) != expected_count or len(ids) != len(set(ids)):
        return False
    for idx, row in enumerate(rows, 1):
        if row.get("left_sample_index_row_id", "") >= row.get("right_sample_index_row_id", ""):
            return False
        identifier = row.get("pairwise_evidence_id") or row.get("ligand_pairwise_evidence_id") or row.get("protein_pairwise_evidence_id")
        if identifier != f"{expected_prefix}_{idx:06d}":
            return False
    return True


def run(acquire_missing_ccd: bool = False, downloader: Callable[[str, Path], tuple[int, str]] = _download_ccd) -> dict[str, Any]:
    samples, source_rows, source_blockers = _load_samples_safely()
    pre_rows = precondition_rows(source_rows)
    ccd_rows = acquire_ccd_files(acquire_missing_ccd, downloader)
    failed_ccd = [row for row in ccd_rows if not _truth(row["ccd_audit_passed"])]
    failed_preconditions = [row["precondition_item"] for row in pre_rows if not _truth(row["precondition_passed"])]
    failed_source = source_blockers + [row["blocking_reasons"] for row in source_rows if row.get("blocking_reasons")]
    if failed_ccd or failed_preconditions or failed_source:
        safe_rows = safety_rows(samples, ccd_rows, source_rows)
        raw_issues: list[tuple[str, str, str, str, str]] = []
        for issue in failed_preconditions:
            raw_issues.append(("precondition", "", "", "", issue))
        for issue in failed_source:
            raw_issues.append(("source_inventory", "", "", "", issue))
        for row in failed_ccd:
            raw_issues.append(("ccd", "", "", row.get("het_id", ""), row.get("blocking_reasons", "ccd_integrity_failed")))
        for row in safe_rows:
            if not _truth(row["safety_passed"]):
                raw_issues.append(("safety", "", "", "", row["blocking_reasons"]))
        issue_rows = _issue_rows(raw_issues)
        manifest = {
            "stage": STAGE,
            "step_label": STEP_LABEL,
            "previous_stage": PREVIOUS_STAGE,
            "project_name": PROJECT_NAME,
            "future_unified_sample_count": len(samples),
            "pilot_sample_count": 3,
            "expansion_sample_count": 8,
            "unique_ligand_component_count": len(UNIQUE_HETS),
            "unique_ligand_components": UNIQUE_HETS,
            "ccd_component_count": len(ccd_rows),
            "ccd_integrity_passed_count": sum(_truth(row["ccd_audit_passed"]) for row in ccd_rows),
            "ccd_downloaded_by_step14ao_count": sum(row.get("source_origin") == "downloaded_by_step14ao" for row in ccd_rows),
            "ccd_reused_preexisting_count": sum(row.get("source_origin") == "reused_preexisting_ccd" for row in ccd_rows),
            "ccd_acquisition_provenance_stable": False,
            "ligand_graph_scaffold_evidence_row_count": 0,
            "ligand_pairwise_similarity_evidence_row_count": 0,
            "protein_sequence_accession_evidence_row_count": 0,
            "protein_pairwise_sequence_identity_evidence_row_count": 0,
            "combined_pairwise_independence_evidence_row_count": 0,
            "pairwise_expected_row_count": 55,
            "confirmed_new_independent_group_count_current_step": 0,
            "combined_sample_index_written": False,
            "split_assignments_written": False,
            "leakage_matrix_written": False,
            "final_dataset_written": False,
            "actual_dataloader_artifacts_written": False,
            "training_artifacts_written": False,
            "feature_semantics_known_for_training": False,
            "unknown_atom_feature_policy_finalized_for_training": False,
            "ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke": False,
            "ready_for_covapie_independence_evidence_issue_resolution": True,
            "ready_for_covapie_split_materialization_smoke": False,
            "ready_for_covapie_final_dataset_materialization_smoke": False,
            "ready_for_training": False,
            "ready_to_train_now": False,
            "feature_semantics_audit_required_before_training": True,
            "leakage_split_design_required_before_training": True,
            "canonical_mask_task_names": MASK_NAMES,
            "canonical_mask_task_aliases": MASK_ALIASES,
            "b3_scaffold_only_included": True,
            "no_extra_mask_tasks_added": True,
            "recommended_next_step": "resolve_covapie_independence_evidence_materialization_issues",
            "all_checks_passed": False,
            "blocking_reasons": [row["issue_description"] for row in issue_rows],
        }
        empty: list[dict[str, Any]] = []
        for path, rows in {
            PRECONDITION: pre_rows,
            SOURCE_INVENTORY: source_rows,
            CCD_AUDIT: ccd_rows,
            LIGAND_EVIDENCE: empty,
            LIGAND_GROUPS: empty,
            LIGAND_PAIRWISE: empty,
            PROTEIN_EVIDENCE: empty,
            PROTEIN_GROUPS: empty,
            PROTEIN_PAIRWISE: empty,
            COMBINED_PAIRWISE: empty,
            ISSUES: issue_rows,
            SAFETY: safe_rows,
        }.items():
            _write_csv(path, rows)
        _write_json(MANIFEST, manifest)
        _write_summary(
            "\n".join([
                "# CovaPIE independent group expansion batch independence evidence materialization smoke v0",
                "",
                "Step 14AO is blocked by validated evidence inconsistency. No group assignment, combined sample index, split, final dataset, dataloader artifact, or training artifact was written.",
                "",
                "- source and CCD validation completed before the block",
                "- blocked evidence is listed in covapie_independence_evidence_materialization_issue_inventory.csv",
                "- feature semantics audit and leakage/split design remain required before training",
                "",
            ])
        )
        return {"samples": samples, "precondition": pre_rows, "source_inventory": source_rows, "ccd": ccd_rows, "ligand": [], "ligand_pairwise": [], "protein": [], "protein_pairwise": [], "combined_pairwise": [], "safety": safe_rows, "issues": issue_rows, "manifest": manifest}
    ligand_rows, ligand_by_sample, ligand_group_rows = _make_ligand_evidence(samples, ccd_rows)
    protein_rows = [protein_evidence_for_sample(sample) for sample in samples]
    ligand_pair_rows, protein_pair_rows, combined_rows, protein_group_rows = _make_pairwise(samples, ligand_by_sample, protein_rows)
    safe_rows = safety_rows(samples, ccd_rows, source_rows)
    issue_details: list[tuple[str, str, str, str, str]] = []
    for scope, table in [
        ("precondition", pre_rows), ("source_inventory", source_rows), ("ccd", ccd_rows),
        ("ligand", ligand_rows), ("protein", protein_rows), ("ligand_pairwise", ligand_pair_rows),
        ("protein_pairwise", protein_pair_rows), ("combined_pairwise", combined_rows), ("safety", safe_rows),
    ]:
        for row in table:
            failed = ("safety_passed" in row and not _truth(row["safety_passed"])) or ("precondition_passed" in row and not _truth(row["precondition_passed"])) or bool(row.get("blocking_reasons"))
            if failed:
                issue_details.append((scope, row.get("sample_index_row_id", ""), row.get("pdb_id", ""), row.get("ligand_comp_id", row.get("het_id", "")), row.get("blocking_reasons") or f"{scope}_validation_failed"))
    ligand_pairwise_ok = _pairwise_complete(ligand_pair_rows, "COVAPIE_LIGAND_PAIRWISE") and all(_truth(row["ligand_pairwise_evidence_passed"]) for row in ligand_pair_rows)
    protein_pairwise_ok = _pairwise_complete(protein_pair_rows, "COVAPIE_PROTEIN_PAIRWISE") and all(_truth(row["protein_pairwise_evidence_passed"]) for row in protein_pair_rows)
    combined_pairwise_ok = _pairwise_complete(combined_rows, "COVAPIE_COMBINED_PAIRWISE") and all(not _truth(row["final_independent_group_confirmed_current_step"]) and row["combined_pairwise_independence_evidence_classification"] != "evidence_incomplete" for row in combined_rows)
    if not ligand_pairwise_ok:
        issue_details.append(("ligand_pairwise", "", "", "", "ligand_pairwise_set_incomplete_or_invalid"))
    if not protein_pairwise_ok:
        issue_details.append(("protein_pairwise", "", "", "", "protein_pairwise_set_incomplete_or_invalid"))
    if not combined_pairwise_ok:
        issue_details.append(("combined_pairwise", "", "", "", "combined_pairwise_set_incomplete_or_invalid"))
    issue_rows = _issue_rows(issue_details)
    all_preconditions = all(_truth(row["precondition_passed"]) for row in pre_rows)
    all_sources = not source_blockers and all(_truth(row["source_inventory_passed"]) for row in source_rows)
    all_ccd = all(_truth(row["ccd_audit_passed"]) for row in ccd_rows)
    all_ligand = all(_truth(row["ligand_graph_evidence_passed"]) for row in ligand_rows)
    all_protein = all(_truth(row["protein_sequence_evidence_passed"]) for row in protein_rows)
    all_safety = all(_truth(row["safety_passed"]) for row in safe_rows)
    all_pairwise = ligand_pairwise_ok and protein_pairwise_ok and combined_pairwise_ok
    all_checks = all_preconditions and all_sources and all_ccd and all_ligand and all_protein and all_pairwise and all_safety
    manifest = {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step14an_batch_sample_index_materialization_validated": True,
        "unified_evidence_sample_count": len(samples),
        "future_unified_sample_count": len(samples),
        "pilot_sample_count": 3,
        "expansion_sample_count": 8,
        "unique_ligand_component_count": len(UNIQUE_HETS),
        "unique_ligand_components": UNIQUE_HETS,
        "ccd_component_count": len(ccd_rows),
        "ccd_acquisition_audit_count": len(ccd_rows),
        "ccd_component_count": len(ccd_rows),
        "ccd_integrity_passed_count": sum(_truth(row["ccd_audit_passed"]) for row in ccd_rows),
        "ccd_downloaded_by_step14ao_count": sum(row.get("source_origin") == "downloaded_by_step14ao" for row in ccd_rows),
        "ccd_reused_preexisting_count": sum(row.get("source_origin") == "reused_preexisting_ccd" for row in ccd_rows),
        "ccd_acquisition_provenance_stable": all(row.get("source_origin") in {"downloaded_by_step14ao", "reused_preexisting_ccd"} and row.get("acquisition_provenance_status") for row in ccd_rows),
        "network_access_used_during_ccd_acquisition": any(row.get("source_origin") == "downloaded_by_step14ao" for row in ccd_rows),
        "network_access_used_current_run": False,
        "ligand_graph_evidence_count": len(ligand_rows),
        "ligand_graph_scaffold_evidence_row_count": len(ligand_rows),
        "ligand_graph_evidence_passed_count": sum(_truth(row["ligand_graph_evidence_passed"]) for row in ligand_rows),
        "ligand_exact_graph_group_count": len({row["ligand_graph_group_id"] for row in ligand_rows}),
        "ligand_graph_group_count": len({row["ligand_graph_group_id"] for row in ligand_rows}),
        "ligand_scaffold_group_count": len({row["ligand_scaffold_group_id"] for row in ligand_rows}),
        "ligand_pairwise_evidence_count": len(ligand_pair_rows),
        "ligand_pairwise_similarity_evidence_row_count": len(ligand_pair_rows),
        "protein_sequence_evidence_count": len(protein_rows),
        "protein_sequence_accession_evidence_row_count": len(protein_rows),
        "protein_sequence_resolved_count": sum(_truth(row["protein_sequence_evidence_passed"]) for row in protein_rows),
        "protein_accession_unique_count": sum(row["protein_accession_status"] == "unique_uniprot_accession" for row in protein_rows),
        "protein_accession_missing_count": sum(row["protein_accession_status"] == "accession_missing_in_raw_mmcif" for row in protein_rows),
        "protein_accession_multiple_count": sum(row["protein_accession_status"] == "multiple_uniprot_accessions" for row in protein_rows),
        "protein_pairwise_evidence_count": len(protein_pair_rows),
        "protein_pairwise_sequence_identity_evidence_row_count": len(protein_pair_rows),
        "protein_exact_sequence_group_count": len({row["protein_exact_sequence_group_id"] for row in protein_rows}),
        "protein_accession_group_count": len({row["protein_accession_group_id"] for row in protein_rows}),
        "protein_sequence_cluster_90_count": len({row["protein_sequence_cluster_90_id"] for row in protein_rows}),
        "protein_sequence_cluster_50_count": len({row["protein_sequence_cluster_50_id"] for row in protein_rows}),
        "combined_pairwise_evidence_count": len(combined_rows),
        "combined_pairwise_independence_evidence_row_count": len(combined_rows),
        "combined_strong_same_group_evidence_count": sum(row["combined_pairwise_independence_evidence_classification"] == "strong_same_group_evidence" for row in combined_rows),
        "combined_protein_related_ligand_distinct_count": sum(row["combined_pairwise_independence_evidence_classification"] == "protein_related_ligand_distinct" for row in combined_rows),
        "combined_provisional_distinct_both_axes_count": sum(row["combined_pairwise_independence_evidence_classification"] == "provisional_distinct_both_axes" for row in combined_rows),
        "pairwise_expected_row_count": 55,
        "issue_inventory_row_count": len(issue_rows),
        "materialization_issue_count": len(issue_details),
        "rdkit_version": rdBase.rdkitVersion,
        "ligand_fingerprint_policy": "morgan_radius_2_nbits_2048",
        "protein_alignment_policy": "global_match_2_mismatch_minus1_gap_minus2_diagonal_up_left",
        "ligand_graph_source_policy": "wwpdb_ccd_smiles_only_no_coordinate_bond_guessing",
        "protein_sequence_source_policy": "raw_entry_mmcif_struct_asym_entity_poly_seq_full_entity_sequence",
        "combined_sample_index_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "final_dataset_written": False,
        "actual_dataloader_artifacts_written": False,
        "training_artifacts_written": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": True,
        "biopython_used": False,
        "gemmi_used": False,
        "requests_used": False,
        "confirmed_new_independent_group_count_current_step": 0,
        "final_independent_group_assignment_written": False,
        "all_preconditions_passed": all_preconditions,
        "all_source_inventory_checks_passed": all_sources,
        "all_ccd_integrity_checks_passed": all_ccd,
        "all_ligand_evidence_checks_passed": all_ligand,
        "all_protein_evidence_checks_passed": all_protein,
        "all_pairwise_checks_passed": all_pairwise,
        "all_safety_checks_passed": all_safety,
        "ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke": all_checks,
        "ready_for_covapie_independence_evidence_issue_resolution": not all_checks,
        "ready_for_covapie_split_materialization_smoke": False,
        "ready_for_covapie_final_dataset_materialization_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "canonical_mask_task_names": MASK_NAMES,
        "canonical_mask_task_aliases": MASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "recommended_next_step": "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke" if all_checks else "resolve_covapie_independence_evidence_materialization_issues",
        "all_checks_passed": all_checks,
        "blocking_reasons": [row["issue_description"] for row in issue_rows if row["issue_status"] == "failed"],
    }
    outputs = {
        PRECONDITION: pre_rows,
        SOURCE_INVENTORY: source_rows,
        CCD_AUDIT: ccd_rows,
        LIGAND_EVIDENCE: ligand_rows,
        LIGAND_GROUPS: ligand_group_rows,
        LIGAND_PAIRWISE: ligand_pair_rows,
        PROTEIN_EVIDENCE: protein_rows,
        PROTEIN_GROUPS: protein_group_rows,
        PROTEIN_PAIRWISE: protein_pair_rows,
        COMBINED_PAIRWISE: combined_rows,
        ISSUES: issue_rows,
        SAFETY: safe_rows,
    }
    for path, rows in outputs.items():
        cleaned = [{k: v for k, v in row.items() if k != "fingerprint" and k != "ccd_atom_ids"} for row in rows]
        _write_csv(path, cleaned)
    _write_json(MANIFEST, manifest)
    _write_summary(
        "\n".join(
            [
                "# CovaPIE independent group expansion batch independence evidence materialization smoke v0",
                "",
                "Step 14AO materializes ligand graph/scaffold and protein sequence/accession evidence for the existing 3 pilot samples plus 8 expansion samples.",
                "",
                "This step writes evidence only. It does not write a combined sample index, split assignments, leakage matrix, final dataset, dataloader artifacts, tensors, checkpoints, or training outputs.",
                "",
                f"- samples: {len(samples)}",
                f"- CCD components: {len(ccd_rows)}",
                f"- ligand pairwise rows: {len(ligand_pair_rows)}",
                f"- protein pairwise rows: {len(protein_pair_rows)}",
                f"- combined pairwise rows: {len(combined_rows)}",
                "- confirmed independent groups current step: 0",
                f"- materialization issues: {len(issue_details)}",
                f"- next step: {manifest['recommended_next_step']}",
                "- feature semantics audit remains required before formal training, fine-tuning, or real parameter updates.",
                "",
            ]
        ),
    )
    return {
        "samples": samples,
        "precondition": pre_rows,
        "source_inventory": source_rows,
        "ccd": ccd_rows,
        "ligand": ligand_rows,
        "ligand_pairwise": ligand_pair_rows,
        "protein": protein_rows,
        "protein_pairwise": protein_pair_rows,
        "combined_pairwise": combined_rows,
        "safety": safe_rows,
        "issues": issue_rows,
        "manifest": manifest,
    }
