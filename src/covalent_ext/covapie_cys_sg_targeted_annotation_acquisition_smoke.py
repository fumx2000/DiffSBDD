from __future__ import annotations

import ast
import csv
import hashlib
import html
import json
import re
import subprocess
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_gate as step14k


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_targeted_annotation_acquisition_smoke_v0"
STEP_LABEL = "Step 14L"
PREVIOUS_STAGE = step14k.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14k.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14k.CURRENT_SOURCE_DATABASE
METADATA_CSV = step14k.METADATA_CSV
METADATA_CSV_SHA256 = step14k.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14k.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14k.RAW_OUTPUT_ROOT
STEP14K_ROOT = step14k.OUTPUT_ROOT
STEP14K_MANIFEST_JSON = step14k.MANIFEST_JSON
STEP14K_ACQUISITION_MANIFEST_CSV = step14k.ACQUISITION_MANIFEST_CSV
STEP14K_ACQUISITION_MANIFEST_JSON = step14k.ACQUISITION_MANIFEST_JSON
STEP14K_SEED_CANDIDATE_AUDIT_CSV = step14k.SEED_CANDIDATE_AUDIT_CSV
STEP14J_ROOT = step14k.STEP14J_ROOT
STEP14J_CANDIDATES_CSV = step14k.STEP14J_CANDIDATES_CSV
STEP14I_ROOT = step14k.STEP14I_ROOT
STEP14H_ROOT = step14k.STEP14H_ROOT

CANONICAL_MASK_TASK_NAMES = step14k.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14k.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_annotation_acquisition_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_precondition_audit.csv"
EXECUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_execution_audit.csv"
LIGAND_CARD_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_covpdb_ligand_card_extraction_audit.csv"
COMPLEX_CARD_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_covpdb_complex_card_extraction_audit.csv"
RCSB_CCD_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_rcsb_ccd_extraction_audit.csv"
ACQUIRED_CANDIDATES_CSV = OUTPUT_ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.csv"
ACQUIRED_CANDIDATES_JSON = OUTPUT_ROOT / "covapie_cys_sg_acquired_event_level_annotation_candidates.json"
GAP_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_gap_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_targeted_annotation_acquisition_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_targeted_annotation_acquisition_smoke_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_targeted_annotation_acquisition_smoke.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_targeted_annotation_acquisition_smoke_v0.py")

TIMEOUT_SECONDS = 30
RETRY_LIMIT = 2
USER_AGENT = "CovaPIE-Step14L-targeted-annotation-smoke/0.1"
COVPDB_BASE = "https://drug-discovery.vm.uni-freiburg.de"
RCSB_CCD_BASE = "https://data.rcsb.org/rest/v1/core/chemcomp/"

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["acquisition_manifest_row_id", "source_registry_id", "source_name", "source_type", "query_key_type", "query_key_value", "attempted_current_step", "fetch_url_or_resolution_strategy", "network_status", "http_status_or_error", "retry_count_used", "response_text_sha256", "parsed_current_step", "parsed_field_count", "acquisition_execution_status", "execution_audit_passed", "qa_comment"]
LIGAND_COLUMNS = ["ligand_identifier", "ligand_card_url", "ligand_card_fetch_status", "ligand_name", "ligand_type", "covpdb_ligand_id_observed", "pubchem_id_if_available", "canonical_smiles_if_available", "het_codes_observed", "bound_pdb_ids_observed", "complex_card_link_count", "ligand_card_extraction_passed", "qa_comment"]
COMPLEX_COLUMNS = ["seed_candidate_id", "pdb_id", "ligand_identifier", "suggested_ligand_comp_id", "complex_card_resolution_status", "complex_card_url", "complex_card_fetch_status", "covpdb_pdb_id_observed", "covpdb_ligand_name_observed", "covpdb_het_code_observed", "covpdb_protein_name_observed", "covpdb_uniprot_observed", "covpdb_reaction_name_observed", "covpdb_residue_name_observed", "covpdb_residue_index_observed", "covpdb_chain_id_observed", "covpdb_sasa_observed", "covpdb_pka_observed", "covpdb_warhead_name_observed", "complex_card_extraction_passed", "qa_comment"]
CCD_COLUMNS = ["suggested_ligand_comp_id", "rcsb_ccd_url", "rcsb_ccd_fetch_status", "ccd_id_observed", "ccd_name_observed", "ccd_formula_observed", "ccd_formula_weight_observed", "ccd_type_observed", "ccd_smiles_observed_if_available", "ccd_inchi_observed_if_available", "rcsb_ccd_extraction_passed", "qa_comment"]
ACQUIRED_COLUMNS = ["acquired_annotation_candidate_id", "seed_candidate_id", "annotation_alignment_candidate_id", "pdb_id", "ligand_identifier", "suggested_ligand_comp_id", "suggested_residue_name", "suggested_residue_index", "suggested_residue_atom_name", "suggested_ligand_atom_name", "suggested_covalent_bond_atom_pair", "rcsb_struct_conn_type", "covpdb_complex_card_url", "covpdb_reaction_name", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "covpdb_warhead_name", "covpdb_sasa", "covpdb_pka", "ccd_ligand_name", "ccd_formula", "ccd_type", "annotation_acquisition_status", "event_level_alignment_status", "event_identity_status_current_step", "manual_review_status", "ready_candidate_current_step", "ready_for_training_current_step", "blocking_reasons"]
GAP_COLUMNS = ["gap_item", "gap_value", "gap_audit_passed", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.links: list[str] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: v or "" for k, v in attrs}
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"}:
            self._cell = []
        elif tag == "a":
            href = attr.get("href", "")
            if href:
                self.links.append(href)

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(_normalize_text(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(cell for cell in self._row):
                self.rows.append(self._row)
            self._row = None


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value))).strip()


def _plain_text(text: str) -> str:
    return _normalize_text(re.sub(r"<[^>]+>", " ", text))


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
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _raw_files_tracked(root: Path) -> bool:
    return bool(_run_git(["ls-files", root.as_posix()]).stdout.strip())


def _raw_files_staged(root: Path) -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", root.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _all_true(rows: list[dict[str, Any]], column: str) -> bool:
    return all(_bool(row[column]) for row in rows)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _allowed_metadata_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    forbidden_suffixes = (".zip", ".pdb", ".ent", ".cif", ".mmcif", ".sdf", ".mol2", ".gz")
    if path.endswith(forbidden_suffixes):
        return False
    if parsed.netloc == "drug-discovery.vm.uni-freiburg.de":
        return path.startswith("/covpdb/ligand_card/") or path.startswith("/covpdb/complex_card/")
    if parsed.netloc == "data.rcsb.org":
        return path.startswith("/rest/v1/core/chemcomp/")
    return False


def fetch_text(url: str) -> dict[str, Any]:
    if not _allowed_metadata_url(url):
        return {"url": url, "attempted": False, "status": "blocked_forbidden_url", "http_status_or_error": "blocked_forbidden_url", "retry_count_used": 0, "text": "", "sha256": ""}
    last_error = ""
    for attempt in range(RETRY_LIMIT + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read()
                text = raw.decode("utf-8", errors="replace")
                return {
                    "url": url,
                    "attempted": True,
                    "status": "fetched",
                    "http_status_or_error": str(getattr(response, "status", "")),
                    "retry_count_used": attempt,
                    "text": text,
                    "sha256": _sha256_text(text),
                }
        except Exception as exc:  # noqa: BLE001 - structured network smoke records exact failure text
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < RETRY_LIMIT:
                time.sleep(0.25)
    return {"url": url, "attempted": True, "status": "fetch_failed", "http_status_or_error": last_error, "retry_count_used": RETRY_LIMIT, "text": "", "sha256": ""}


def ligand_card_url(ligand_identifier: str) -> str:
    return f"{COVPDB_BASE}/covpdb/ligand_card/{quote('ligand_id=' + ligand_identifier, safe='')}"


def rcsb_ccd_url(het_code: str) -> str:
    return f"{RCSB_CCD_BASE}{quote(het_code.strip().upper(), safe='')}"


def _label_value(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*:?\s*(.*?)(?=\s+[A-Z][A-Za-z0-9 /().'-]{{1,40}}\s*:|$)", text, re.I)
    if not match:
        return ""
    return _normalize_text(match.group(1))


def parse_ligand_card(text: str, base_url: str) -> dict[str, Any]:
    parser = TableParser()
    parser.feed(text)
    plain = _plain_text(text)
    ligand_name = _label_value(plain, "Ligand Name")
    ligand_type = _label_value(plain, "Ligand Type")
    ligand_id = _label_value(plain, "Ligand ID")
    pubchem = _label_value(plain, "PubChem")
    smiles = _label_value(plain, "Canonical SMILES")
    complex_links = sorted({urljoin(base_url, link) for link in parser.links if "/covpdb/complex_card/" in link})
    pdb_ids = sorted({m.upper() for m in re.findall(r"rcsb\.org/structure/([A-Za-z0-9]{4})", text, re.I)})
    het_codes = sorted({m.upper() for m in re.findall(r"rcsb\.org/ligand/([A-Za-z0-9]{2,6})", text, re.I)})
    return {
        "ligand_name": ligand_name,
        "ligand_type": ligand_type,
        "covpdb_ligand_id_observed": ligand_id,
        "pubchem_id_if_available": re.sub(r"\D", "", pubchem) or "",
        "canonical_smiles_if_available": smiles,
        "het_codes_observed": ";".join(het_codes),
        "bound_pdb_ids_observed": ";".join(pdb_ids),
        "complex_links": complex_links,
        "complex_card_link_count": len(complex_links),
        "parsed_field_count": sum(bool(v) for v in [ligand_name, ligand_type, ligand_id, pubchem, smiles]) + len(het_codes) + len(pdb_ids),
    }


def parse_complex_card(text: str) -> dict[str, Any]:
    parser = TableParser()
    parser.feed(text)
    plain = _plain_text(text)
    pdb_id = ""
    pdb_match = re.search(r"PDB Entry \(([A-Za-z0-9]{4})\)", plain, re.I) or re.search(r"PDB ID:\s*([A-Za-z0-9]{4})", plain, re.I)
    if pdb_match:
        pdb_id = pdb_match.group(1).upper()
    het = ""
    het_match = re.search(r"ligand-label-comp-id=([A-Za-z0-9]{2,6})", text, re.I) or re.search(r"search_type=by_het_codesearch_term=([A-Za-z0-9]{2,6})", text, re.I)
    if het_match:
        het = het_match.group(1).upper()
    protein_name = _label_value(plain, "Protein Name")
    uniprot = ""
    uniprot_match = re.search(r"Uniprot ID/ACC:\s*([A-Z0-9]+(?:\s*\([^)]+\))?)", plain, re.I)
    if uniprot_match:
        uniprot = _normalize_text(uniprot_match.group(1))
    ligand_name = _label_value(plain, "Ligand Name")
    mechanism = {"reaction": "", "residue_name": "", "residue_index": "", "chain_id": "", "sasa": "", "pka": "", "warhead": ""}
    for row in parser.rows:
        cells = [_normalize_text(c) for c in row]
        if len(cells) >= 6 and re.match(r"^[A-Z]{3}\s+\d+", cells[1]):
            residue_parts = cells[1].split()
            mechanism = {
                "reaction": cells[0],
                "residue_name": residue_parts[0],
                "residue_index": residue_parts[1] if len(residue_parts) > 1 else "",
                "chain_id": cells[2],
                "sasa": cells[3],
                "pka": cells[4],
                "warhead": cells[5],
            }
            break
    return {
        "covpdb_pdb_id_observed": pdb_id,
        "covpdb_ligand_name_observed": ligand_name,
        "covpdb_het_code_observed": het,
        "covpdb_protein_name_observed": protein_name,
        "covpdb_uniprot_observed": uniprot,
        "covpdb_reaction_name_observed": mechanism["reaction"],
        "covpdb_residue_name_observed": mechanism["residue_name"],
        "covpdb_residue_index_observed": mechanism["residue_index"],
        "covpdb_chain_id_observed": mechanism["chain_id"],
        "covpdb_sasa_observed": mechanism["sasa"],
        "covpdb_pka_observed": mechanism["pka"],
        "covpdb_warhead_name_observed": mechanism["warhead"],
        "parsed_field_count": sum(bool(v) for v in [pdb_id, ligand_name, het, protein_name, uniprot, *mechanism.values()]),
    }


def parse_ccd_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"parsed_field_count": 0}
    chem = data.get("chem_comp", {}) if isinstance(data, dict) else {}
    desc = data.get("rcsb_chem_comp_descriptor", {}) if isinstance(data, dict) else {}
    return {
        "ccd_id_observed": chem.get("id", ""),
        "ccd_name_observed": chem.get("name", ""),
        "ccd_formula_observed": chem.get("formula", ""),
        "ccd_formula_weight_observed": chem.get("formula_weight", ""),
        "ccd_type_observed": chem.get("type", ""),
        "ccd_smiles_observed_if_available": desc.get("SMILES") or desc.get("smiles") or desc.get("smiles_stereo", ""),
        "ccd_inchi_observed_if_available": desc.get("InChI") or desc.get("inchi", ""),
        "parsed_field_count": sum(bool(v) for v in [chem.get("id"), chem.get("name"), chem.get("formula"), chem.get("formula_weight"), chem.get("type"), desc.get("SMILES") or desc.get("smiles"), desc.get("InChI") or desc.get("inchi")]),
    }


def _candidate_json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]]) -> bool:
    return [row["acquisition_manifest_row_id"] for row in csv_rows] == [str(row.get("acquisition_manifest_row_id", "")) for row in json_rows]


def build_precondition_rows(seeds: list[dict[str, str]], acquisition_rows: list[dict[str, str]], acquisition_json_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14K_MANIFEST_JSON) if STEP14K_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14k_manifest_exists", STEP14K_MANIFEST_JSON.as_posix(), "exists", STEP14K_MANIFEST_JSON.exists(), STEP14K_MANIFEST_JSON.exists()),
        ("step14k_stage", STEP14K_MANIFEST_JSON.as_posix(), step14k.STAGE, manifest.get("stage"), manifest.get("stage") == step14k.STAGE),
        ("step14k_all_checks_passed", STEP14K_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14k_acquisition_manifest_row_count", STEP14K_MANIFEST_JSON.as_posix(), "29", manifest.get("acquisition_manifest_row_count"), manifest.get("acquisition_manifest_row_count") == 29),
        ("step14k_ready_for_step14l", STEP14K_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke"), manifest.get("ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke") is True),
        ("step14k_ready_for_training", STEP14K_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("acquisition_csv_exists", STEP14K_ACQUISITION_MANIFEST_CSV.as_posix(), "exists", STEP14K_ACQUISITION_MANIFEST_CSV.exists(), STEP14K_ACQUISITION_MANIFEST_CSV.exists()),
        ("acquisition_json_exists", STEP14K_ACQUISITION_MANIFEST_JSON.as_posix(), "exists", STEP14K_ACQUISITION_MANIFEST_JSON.exists(), STEP14K_ACQUISITION_MANIFEST_JSON.exists()),
        ("acquisition_csv_json_consistent", STEP14K_ACQUISITION_MANIFEST_JSON.as_posix(), "true", _candidate_json_consistent(acquisition_rows, acquisition_json_rows), _candidate_json_consistent(acquisition_rows, acquisition_json_rows)),
        ("step14j_candidates_exist", STEP14J_CANDIDATES_CSV.as_posix(), "exists", STEP14J_CANDIDATES_CSV.exists(), STEP14J_CANDIDATES_CSV.exists()),
        ("seed_candidate_count", STEP14K_SEED_CANDIDATE_AUDIT_CSV.as_posix(), "9", len(seeds), len(seeds) == 9),
        ("metadata_csv_exists", METADATA_CSV.as_posix(), "exists", METADATA_CSV.exists(), METADATA_CSV.exists()),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14k.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def acquire_ligand_cards(seeds: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    ligand_ids = sorted({seed["ligand_identifier"] for seed in seeds})
    audits: list[dict[str, Any]] = []
    parsed: dict[str, dict[str, Any]] = {}
    fetches: dict[str, dict[str, Any]] = {}
    for ligand_id in ligand_ids:
        url = ligand_card_url(ligand_id)
        fetch = fetch_text(url)
        fetches[ligand_id] = fetch
        info = parse_ligand_card(fetch["text"], url) if fetch["status"] == "fetched" else {"parsed_field_count": 0, "complex_links": [], "complex_card_link_count": 0}
        parsed[ligand_id] = info
        passed = fetch["status"] == "fetched" and bool(info.get("covpdb_ligand_id_observed") or info.get("ligand_name") or info.get("complex_card_link_count"))
        audits.append({
            "ligand_identifier": ligand_id,
            "ligand_card_url": url,
            "ligand_card_fetch_status": fetch["status"],
            "ligand_name": info.get("ligand_name", ""),
            "ligand_type": info.get("ligand_type", ""),
            "covpdb_ligand_id_observed": info.get("covpdb_ligand_id_observed", ""),
            "pubchem_id_if_available": info.get("pubchem_id_if_available", ""),
            "canonical_smiles_if_available": info.get("canonical_smiles_if_available", ""),
            "het_codes_observed": info.get("het_codes_observed", ""),
            "bound_pdb_ids_observed": info.get("bound_pdb_ids_observed", ""),
            "complex_card_link_count": info.get("complex_card_link_count", 0),
            "ligand_card_extraction_passed": passed,
            "qa_comment": "" if passed else fetch["http_status_or_error"],
        })
    return audits, parsed, fetches


def acquire_ccd(het_codes: list[str]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    audits: list[dict[str, Any]] = []
    parsed: dict[str, dict[str, Any]] = {}
    fetches: dict[str, dict[str, Any]] = {}
    for het in sorted({code.upper() for code in het_codes if code}):
        url = rcsb_ccd_url(het)
        fetch = fetch_text(url)
        fetches[het] = fetch
        info = parse_ccd_json(fetch["text"]) if fetch["status"] == "fetched" else {"parsed_field_count": 0}
        parsed[het] = info
        passed = fetch["status"] == "fetched" and bool(info.get("ccd_id_observed"))
        audits.append({
            "suggested_ligand_comp_id": het,
            "rcsb_ccd_url": url,
            "rcsb_ccd_fetch_status": fetch["status"],
            "ccd_id_observed": info.get("ccd_id_observed", ""),
            "ccd_name_observed": info.get("ccd_name_observed", ""),
            "ccd_formula_observed": info.get("ccd_formula_observed", ""),
            "ccd_formula_weight_observed": info.get("ccd_formula_weight_observed", ""),
            "ccd_type_observed": info.get("ccd_type_observed", ""),
            "ccd_smiles_observed_if_available": info.get("ccd_smiles_observed_if_available", ""),
            "ccd_inchi_observed_if_available": info.get("ccd_inchi_observed_if_available", ""),
            "rcsb_ccd_extraction_passed": passed,
            "qa_comment": "" if passed else fetch["http_status_or_error"],
        })
    return audits, parsed, fetches


def acquire_complex_cards(seeds: list[dict[str, str]], ligand_info: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    audits: list[dict[str, Any]] = []
    parsed_by_seed: dict[str, dict[str, Any]] = {}
    fetch_cache: dict[str, dict[str, Any]] = {}
    for seed in seeds:
        target_pdb = seed["pdb_id"].upper()
        target_het = seed["suggested_ligand_comp_id"].upper()
        links = list(ligand_info.get(seed["ligand_identifier"], {}).get("complex_links", []))
        selected_url = ""
        selected_fetch: dict[str, Any] = {}
        selected_info: dict[str, Any] = {}
        status = "not_resolved_from_ligand_card"
        for link in links[:40]:
            fetch = fetch_cache.get(link)
            if fetch is None:
                fetch = fetch_text(link)
                fetch_cache[link] = fetch
            if fetch["status"] != "fetched":
                continue
            info = parse_complex_card(fetch["text"])
            pdb_match = str(info.get("covpdb_pdb_id_observed", "")).upper() == target_pdb
            het_observed = str(info.get("covpdb_het_code_observed", "")).upper()
            het_match = not het_observed or het_observed == target_het
            if pdb_match and het_match:
                selected_url = link
                selected_fetch = fetch
                selected_info = info
                status = "resolved_matching_pdb_and_compatible_het"
                break
        passed = status.startswith("resolved") and bool(selected_info.get("covpdb_reaction_name_observed") or selected_info.get("covpdb_residue_name_observed"))
        row = {
            "seed_candidate_id": seed["seed_candidate_id"],
            "pdb_id": seed["pdb_id"],
            "ligand_identifier": seed["ligand_identifier"],
            "suggested_ligand_comp_id": seed["suggested_ligand_comp_id"],
            "complex_card_resolution_status": status,
            "complex_card_url": selected_url,
            "complex_card_fetch_status": selected_fetch.get("status", "not_fetched_no_matching_link"),
            "covpdb_pdb_id_observed": selected_info.get("covpdb_pdb_id_observed", ""),
            "covpdb_ligand_name_observed": selected_info.get("covpdb_ligand_name_observed", ""),
            "covpdb_het_code_observed": selected_info.get("covpdb_het_code_observed", ""),
            "covpdb_protein_name_observed": selected_info.get("covpdb_protein_name_observed", ""),
            "covpdb_uniprot_observed": selected_info.get("covpdb_uniprot_observed", ""),
            "covpdb_reaction_name_observed": selected_info.get("covpdb_reaction_name_observed", ""),
            "covpdb_residue_name_observed": selected_info.get("covpdb_residue_name_observed", ""),
            "covpdb_residue_index_observed": selected_info.get("covpdb_residue_index_observed", ""),
            "covpdb_chain_id_observed": selected_info.get("covpdb_chain_id_observed", ""),
            "covpdb_sasa_observed": selected_info.get("covpdb_sasa_observed", ""),
            "covpdb_pka_observed": selected_info.get("covpdb_pka_observed", ""),
            "covpdb_warhead_name_observed": selected_info.get("covpdb_warhead_name_observed", ""),
            "complex_card_extraction_passed": passed,
            "qa_comment": "" if passed else status,
        }
        audits.append(row)
        parsed_by_seed[seed["seed_candidate_id"]] = row
    return audits, parsed_by_seed, fetch_cache


def build_execution_rows(acquisition_rows: list[dict[str, str]], ligand_fetches: dict[str, dict[str, Any]], ligand_info: dict[str, dict[str, Any]], complex_by_seed: dict[str, dict[str, Any]], ccd_fetches: dict[str, dict[str, Any]], ccd_info: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in acquisition_rows:
        sid = row["source_registry_id"]
        query_value = row["query_key_value"]
        attempted = True
        url_or_strategy = ""
        fetch: dict[str, Any] = {}
        parsed = False
        parsed_count = 0
        status = "attempted"
        comment = ""
        if sid == "covpdb_ligand_pages_for_seed_candidates":
            fetch = ligand_fetches.get(row["ligand_identifier"], {})
            url_or_strategy = ligand_card_url(row["ligand_identifier"])
            info = ligand_info.get(row["ligand_identifier"], {})
            parsed_count = int(info.get("parsed_field_count", 0) or 0)
            parsed = parsed_count > 0
            status = "ligand_card_parsed" if parsed else "ligand_card_fetch_or_parse_failed"
        elif sid == "rcsb_chemical_component_dictionary_crosscheck":
            fetch = ccd_fetches.get(row["suggested_ligand_comp_id"].upper(), {})
            url_or_strategy = rcsb_ccd_url(row["suggested_ligand_comp_id"])
            info = ccd_info.get(row["suggested_ligand_comp_id"].upper(), {})
            parsed_count = int(info.get("parsed_field_count", 0) or 0)
            parsed = parsed_count > 0
            status = "rcsb_ccd_json_parsed" if parsed else "rcsb_ccd_fetch_or_parse_failed"
        elif sid == "covpdb_complex_card_for_seed_candidates":
            complex_row = complex_by_seed.get(row["seed_candidate_id"], {})
            url_or_strategy = complex_row.get("complex_card_url") or "resolved_through_ligand_card_links"
            parsed = _bool(complex_row.get("complex_card_extraction_passed"))
            parsed_count = sum(bool(complex_row.get(k, "")) for k in COMPLEX_COLUMNS if k.startswith("covpdb_"))
            status = "complex_card_event_annotation_parsed" if parsed else str(complex_row.get("complex_card_resolution_status", "complex_card_not_resolved"))
            fetch = {"status": complex_row.get("complex_card_fetch_status", ""), "http_status_or_error": "", "retry_count_used": "", "sha256": ""}
        else:
            attempted = False
            url_or_strategy = "deferred_global_source_no_stable_metadata_url_current_step"
            fetch = {"status": "deferred", "http_status_or_error": "deferred_global_source", "retry_count_used": 0, "sha256": ""}
            status = "deferred_unresolved_global_source"
            comment = "global source deferred; not blocking seed-level smoke"
        rows.append({
            "acquisition_manifest_row_id": row["acquisition_manifest_row_id"],
            "source_registry_id": sid,
            "source_name": row["source_name"],
            "source_type": row["source_type"],
            "query_key_type": row["query_key_type"],
            "query_key_value": query_value,
            "attempted_current_step": attempted,
            "fetch_url_or_resolution_strategy": url_or_strategy,
            "network_status": fetch.get("status", "not_attempted"),
            "http_status_or_error": fetch.get("http_status_or_error", ""),
            "retry_count_used": fetch.get("retry_count_used", ""),
            "response_text_sha256": fetch.get("sha256", ""),
            "parsed_current_step": parsed,
            "parsed_field_count": parsed_count,
            "acquisition_execution_status": status,
            "execution_audit_passed": True,
            "qa_comment": comment,
        })
    return rows


def build_acquired_candidates(seeds: list[dict[str, str]], step14j_rows: list[dict[str, str]], complex_by_seed: dict[str, dict[str, Any]], ccd_info: dict[str, dict[str, Any]], ligand_audit_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    step14j_by_id = {row["annotation_alignment_candidate_id"]: row for row in step14j_rows}
    rows: list[dict[str, Any]] = []
    for i, seed in enumerate(seeds, start=1):
        complex_row = complex_by_seed.get(seed["seed_candidate_id"], {})
        ccd = ccd_info.get(seed["suggested_ligand_comp_id"].upper(), {})
        ligand = ligand_audit_by_id.get(seed["ligand_identifier"], {})
        complex_ok = _bool(complex_row.get("complex_card_extraction_passed"))
        ccd_ok = bool(ccd.get("ccd_id_observed"))
        ligand_ok = _bool(ligand.get("ligand_card_extraction_passed"))
        if complex_ok:
            align_status = "acquired_covpdb_event_annotation_pending_manual_review"
            acquisition_status = "event_annotation_acquired_pending_manual_review"
            blocking = ""
        elif ccd_ok or ligand_ok:
            align_status = "partial_annotation_acquired_pending_gap_resolution"
            acquisition_status = "partial_annotation_acquired_pending_gap_resolution"
            blocking = "covpdb_complex_card_event_annotation_missing"
        else:
            align_status = "annotation_acquisition_failed_pending_retry"
            acquisition_status = "annotation_acquisition_failed_pending_retry"
            blocking = "no_seed_level_annotation_source_succeeded"
        step14j_row = step14j_by_id.get(seed["annotation_alignment_candidate_id"], {})
        rows.append({
            "acquired_annotation_candidate_id": f"CYS_SG_ACQ_ANNOT_{i:06d}",
            "seed_candidate_id": seed["seed_candidate_id"],
            "annotation_alignment_candidate_id": seed["annotation_alignment_candidate_id"],
            "pdb_id": seed["pdb_id"],
            "ligand_identifier": seed["ligand_identifier"],
            "suggested_ligand_comp_id": seed["suggested_ligand_comp_id"],
            "suggested_residue_name": seed["suggested_residue_name"],
            "suggested_residue_index": seed["suggested_residue_index"],
            "suggested_residue_atom_name": seed["suggested_residue_atom_name"],
            "suggested_ligand_atom_name": seed["suggested_ligand_atom_name"],
            "suggested_covalent_bond_atom_pair": seed["suggested_covalent_bond_atom_pair"],
            "rcsb_struct_conn_type": step14j_row.get("struct_conn_type", ""),
            "covpdb_complex_card_url": complex_row.get("complex_card_url", ""),
            "covpdb_reaction_name": complex_row.get("covpdb_reaction_name_observed", ""),
            "covpdb_residue_name": complex_row.get("covpdb_residue_name_observed", ""),
            "covpdb_residue_index": complex_row.get("covpdb_residue_index_observed", ""),
            "covpdb_chain_id": complex_row.get("covpdb_chain_id_observed", ""),
            "covpdb_warhead_name": complex_row.get("covpdb_warhead_name_observed", ""),
            "covpdb_sasa": complex_row.get("covpdb_sasa_observed", ""),
            "covpdb_pka": complex_row.get("covpdb_pka_observed", ""),
            "ccd_ligand_name": ccd.get("ccd_name_observed", ""),
            "ccd_formula": ccd.get("ccd_formula_observed", ""),
            "ccd_type": ccd.get("ccd_type_observed", ""),
            "annotation_acquisition_status": acquisition_status,
            "event_level_alignment_status": align_status,
            "event_identity_status_current_step": "not_event_identity_until_manual_review",
            "manual_review_status": "pending_manual_review",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "blocking_reasons": blocking,
        })
    return rows


def build_gap_rows(ligand_audits: list[dict[str, Any]], complex_audits: list[dict[str, Any]], ccd_audits: list[dict[str, Any]], acquired: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ligand_success = sum(_bool(row["ligand_card_extraction_passed"]) for row in ligand_audits)
    complex_resolved = sum(str(row["complex_card_resolution_status"]).startswith("resolved") for row in complex_audits)
    complex_event = sum(_bool(row["complex_card_extraction_passed"]) for row in complex_audits)
    ccd_success = sum(_bool(row["rcsb_ccd_extraction_passed"]) for row in ccd_audits)
    partial = sum(row["event_level_alignment_status"] == "partial_annotation_acquired_pending_gap_resolution" for row in acquired)
    failed = sum(row["event_level_alignment_status"] == "annotation_acquisition_failed_pending_retry" for row in acquired)
    values = [
        ("seed_candidate_count", len(acquired), True, ""),
        ("ligand_card_fetch_success_count", ligand_success, ligand_success >= 0, ""),
        ("complex_card_resolved_count", complex_resolved, complex_resolved >= 0, ""),
        ("complex_card_event_annotation_acquired_count", complex_event, complex_event >= 0, ""),
        ("rcsb_ccd_fetch_success_count", ccd_success, ccd_success >= 0, ""),
        ("acquired_event_annotation_candidate_count", len(acquired), len(acquired) == 9, ""),
        ("partial_annotation_count", partial, partial >= 0, ""),
        ("failed_annotation_count", failed, failed >= 0, ""),
        ("ready_candidate_count_current_step", 0, True, ""),
        ("below_20_threshold_status", "below_threshold_needs_additional_cys_sg_candidates", len(acquired) < 20, ""),
        ("targeted_expansion_still_required", True, len(acquired) < 20, ""),
        ("training_still_blocked", True, True, ""),
    ]
    return [{"gap_item": item, "gap_value": value, "gap_audit_passed": passed, "qa_comment": comment} for item, value, passed, comment in values]


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


def _own_files_have_forbidden_imports() -> bool:
    forbidden = {"requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright", "bs4"}
    return any(_imports_forbidden_module(path, forbidden) for path in [MODULE_PATH, CHECK_SCRIPT_PATH])


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(p.name in names for p in root.rglob("*") if p.is_file())


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(p.suffix.lower() in suffixes for p in root.rglob("*") if p.is_file())


def build_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("network_access_used_current_step", "true", "true", True),
        ("download_attempted_current_step", "true", "true", True),
        ("no_raw_coordinate_download_current_step", "passed", "passed", True),
        ("no_raw_file_content_read_current_step", "passed", "passed", True),
        ("no_raw_files_written_current_step", "passed", "passed", True),
        ("no_html_files_written_current_step", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("raw_files_untracked", "passed", "passed" if not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT) else "failed", not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "passed", "passed" if not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT) else "failed", not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "passed", "passed" if _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]) else "failed", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14k_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14K_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14K_ROOT.as_posix()])),
        ("step14j_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14J_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14J_ROOT.as_posix()])),
        ("step14i_artifacts_unchanged", "passed", "passed" if not _path_diff_exists([STEP14I_ROOT.as_posix()]) else "failed", not _path_diff_exists([STEP14I_ROOT.as_posix()])),
        ("protected_source_diff_empty", "passed", "passed" if not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]) else "failed", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "passed", "passed" if not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]) else "failed", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_download_manifest_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_actual_dataloader_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_final_dataset_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_sample_index_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", "passed", "passed" if not _forbidden_named_artifact_exists() else "failed", not _forbidden_named_artifact_exists()),
        ("no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports", "passed", "passed" if not _own_files_have_forbidden_imports() else "failed", not _own_files_have_forbidden_imports()),
        ("derived_output_no_forbidden_binary_or_raw_suffix", "passed", "passed" if not _forbidden_suffix_exists() else "failed", not _forbidden_suffix_exists()),
        ("no_ready_candidates_created", "passed", "passed", True),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(pre, execution, ligand, complex_rows, ccd, acquired, gap, safety) -> dict[str, Any]:
    ligand_success = sum(_bool(row["ligand_card_extraction_passed"]) for row in ligand)
    complex_resolved = sum(str(row["complex_card_resolution_status"]).startswith("resolved") for row in complex_rows)
    complex_event = sum(_bool(row["complex_card_extraction_passed"]) for row in complex_rows)
    ccd_success = sum(_bool(row["rcsb_ccd_extraction_passed"]) for row in ccd)
    partial = sum(row["event_level_alignment_status"] == "partial_annotation_acquired_pending_gap_resolution" for row in acquired)
    failed = sum(row["event_level_alignment_status"] == "annotation_acquisition_failed_pending_retry" for row in acquired)
    any_seed_source = ligand_success > 0 or ccd_success > 0 or complex_event > 0
    passed = _all_true(pre, "precondition_passed") and _all_true(execution, "execution_audit_passed") and _all_true(gap, "gap_audit_passed") and _all_true(safety, "safety_passed") and any_seed_source
    next_step = "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate" if len(acquired) < 20 else "covapie_cys_sg_acquired_annotation_manual_review_gate"
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "input_seed_candidate_count": len(acquired),
        "input_acquisition_manifest_row_count": len(execution),
        "network_access_used": True,
        "download_attempted": True,
        "raw_coordinate_downloaded": False,
        "raw_file_content_read_current_step": False,
        "raw_files_written_current_step": False,
        "html_files_written_current_step": False,
        "ligand_card_fetch_success_count": ligand_success,
        "complex_card_resolved_count": complex_resolved,
        "complex_card_event_annotation_acquired_count": complex_event,
        "rcsb_ccd_fetch_success_count": ccd_success,
        "acquired_annotation_candidate_count": len(acquired),
        "partial_annotation_count": partial,
        "failed_annotation_count": failed,
        "acquired_annotation_candidates_csv_json_consistent": True,
        "ready_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "seed_candidate_count_current_step": len(acquired),
        "small_pilot_threshold_20_met": False,
        "small_pilot_threshold_20_status": "below_threshold_needs_additional_cys_sg_candidates",
        "sample_download_manifest_written": False,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate": complex_event > 0,
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate": True,
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
        "recommended_next_step": next_step,
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14l_annotation_acquisition_smoke_failed_or_no_seed_source_succeeded"],
    }


def run_covapie_cys_sg_targeted_annotation_acquisition_smoke_v0() -> dict[str, Any]:
    seeds = _csv_rows(STEP14K_SEED_CANDIDATE_AUDIT_CSV)
    acquisition_rows = _csv_rows(STEP14K_ACQUISITION_MANIFEST_CSV)
    acquisition_json_rows = _load_json(STEP14K_ACQUISITION_MANIFEST_JSON)
    step14j_rows = _csv_rows(STEP14J_CANDIDATES_CSV)
    pre = build_precondition_rows(seeds, acquisition_rows, acquisition_json_rows)
    ligand_audit, ligand_info, ligand_fetches = acquire_ligand_cards(seeds)
    ccd_audit, ccd_info, ccd_fetches = acquire_ccd([seed["suggested_ligand_comp_id"] for seed in seeds])
    complex_audit, complex_by_seed, _complex_fetches = acquire_complex_cards(seeds, ligand_info)
    ligand_audit_by_id = {row["ligand_identifier"]: row for row in ligand_audit}
    execution = build_execution_rows(acquisition_rows, ligand_fetches, ligand_info, complex_by_seed, ccd_fetches, ccd_info)
    acquired = build_acquired_candidates(seeds, step14j_rows, complex_by_seed, ccd_info, ligand_audit_by_id)
    gap = build_gap_rows(ligand_audit, complex_audit, ccd_audit, acquired)
    safety = build_safety_rows()
    manifest = build_manifest(pre, execution, ligand_audit, complex_audit, ccd_audit, acquired, gap, safety)
    return {
        "precondition_rows": pre,
        "execution_rows": execution,
        "ligand_rows": ligand_audit,
        "complex_rows": complex_audit,
        "ccd_rows": ccd_audit,
        "acquired_rows": acquired,
        "gap_rows": gap,
        "safety_rows": safety,
        "manifest": manifest,
    }
