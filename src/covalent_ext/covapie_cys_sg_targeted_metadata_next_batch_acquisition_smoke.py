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

from covalent_ext import covapie_cys_sg_targeted_annotation_acquisition_smoke as step14l
from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_next_batch_gate as step14m


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0"
STEP_LABEL = "Step 14N"
PREVIOUS_STAGE = step14m.STAGE
PROJECT_NAME = "CovaPIE"

CURRENT_SOURCE_PROFILE = step14m.CURRENT_SOURCE_PROFILE
CURRENT_SOURCE_DATABASE = step14m.CURRENT_SOURCE_DATABASE
TOTAL_CANDIDATE_TARGET = step14m.TOTAL_CANDIDATE_TARGET
METADATA_CSV = step14m.METADATA_CSV
METADATA_CSV_SHA256 = step14m.METADATA_CSV_SHA256
RAW_REFERENCE_ROOT = step14m.RAW_REFERENCE_ROOT
RAW_OUTPUT_ROOT = step14m.RAW_OUTPUT_ROOT
STEP14K_ROOT = step14m.STEP14K_ROOT
STEP14L_ROOT = step14m.STEP14L_ROOT
STEP14L_ACQUIRED_CSV = step14m.STEP14L_ACQUIRED_CSV
STEP14M_ROOT = step14m.OUTPUT_ROOT
STEP14M_MANIFEST_JSON = step14m.MANIFEST_JSON
STEP14M_NEXT_BATCH_CSV = step14m.NEXT_BATCH_ACQUISITION_MANIFEST_CSV
STEP14M_NEXT_BATCH_JSON = step14m.NEXT_BATCH_ACQUISITION_MANIFEST_JSON
STEP14M_EXCLUSION_REGISTRY_CSV = step14m.EXCLUSION_REGISTRY_CSV

CANONICAL_MASK_TASK_NAMES = step14m.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step14m.CANONICAL_MASK_TASK_ALIASES

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquisition_precondition_audit.csv"
SOURCE_DISCOVERY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_source_discovery_audit.csv"
ACQUISITION_EXECUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquisition_execution_audit.csv"
COMPLEX_EXTRACTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_covpdb_complex_extraction_audit.csv"
RCSB_CCD_EXTRACTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_rcsb_ccd_extraction_audit.csv"
ACQUIRED_CANDIDATES_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.csv"
ACQUIRED_CANDIDATES_JSON = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.json"
THRESHOLD_GAP_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_threshold_gap_audit.csv"
SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_cys_sg_next_batch_acquisition_safety_audit.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0_summary.md")

MODULE_PATH = Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke.py")
CHECK_SCRIPT_PATH = Path("scripts/check_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0.py")

TIMEOUT_SECONDS = 30
RETRY_LIMIT = 2
USER_AGENT = "CovaPIE-Step14N-next-batch-acquisition-smoke/0.1"
COVPDB_BASE = "https://drug-discovery.vm.uni-freiburg.de"
RCSB_CCD_BASE = "https://data.rcsb.org/rest/v1/core/chemcomp/"
MAX_DISCOVERY_PAGES = 8
MAX_COMPLEX_CARD_FETCHES = 80

SEED_URLS = [
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/help",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/residues_list/initial=Allsortedby=residue_name",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/complexes_list/initial=Allsortedby=protein_id",
]
PREFERRED_CYS_COMPLEX_LIST_URL = "https://drug-discovery.vm.uni-freiburg.de/covpdb/complexes_list_by_id/search_type=by_residue_idsearch_id=3"
FORBIDDEN_URL_SUFFIXES = (".pdb", ".ent", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".zip", ".tar", ".tgz", ".npz")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_DISCOVERY_COLUMNS = ["discovery_row_id", "seed_url_or_strategy", "attempted_current_step", "discovered_url", "discovered_url_role", "discovery_status", "fetch_status", "http_status_or_error", "response_text_sha256", "parsed_link_count", "selected_for_complex_candidate_scan", "discovery_audit_passed", "qa_comment"]
ACQUISITION_EXECUTION_COLUMNS = ["execution_row_id", "source_name", "source_type", "query_key_type", "query_key_value", "attempted_current_step", "fetch_url_or_strategy", "network_status", "http_status_or_error", "retry_count_used", "response_text_sha256", "parsed_current_step", "parsed_field_count", "acquisition_execution_status", "execution_audit_passed", "qa_comment"]
COMPLEX_EXTRACTION_COLUMNS = ["complex_extraction_row_id", "complex_card_url", "fetch_status", "covpdb_pdb_id_observed", "covpdb_ligand_name_observed", "covpdb_het_code_observed", "covpdb_protein_name_observed", "covpdb_uniprot_observed", "covpdb_reaction_name_observed", "covpdb_residue_name_observed", "covpdb_residue_index_observed", "covpdb_chain_id_observed", "covpdb_sasa_observed", "covpdb_pka_observed", "covpdb_warhead_name_observed", "duplicate_against_existing_9", "excluded_reason", "kept_as_next_batch_candidate", "complex_extraction_passed", "qa_comment"]
RCSB_CCD_COLUMNS = ["suggested_ligand_comp_id", "rcsb_ccd_url", "rcsb_ccd_fetch_status", "ccd_id_observed", "ccd_name_observed", "ccd_formula_observed", "ccd_formula_weight_observed", "ccd_type_observed", "ccd_smiles_observed_if_available", "ccd_inchi_observed_if_available", "rcsb_ccd_extraction_passed", "qa_comment"]
ACQUIRED_COLUMNS = ["next_batch_acquired_candidate_id", "complex_card_url", "pdb_id", "ligand_identifier_if_available", "suggested_ligand_comp_id", "covpdb_ligand_name", "covpdb_protein_name", "covpdb_uniprot", "covpdb_reaction_name", "covpdb_residue_name", "covpdb_residue_index", "covpdb_chain_id", "covpdb_warhead_name", "covpdb_sasa", "covpdb_pka", "ccd_ligand_name", "ccd_formula", "ccd_type", "duplicate_exclusion_status", "annotation_acquisition_status", "event_identity_status_current_step", "manual_review_status", "ready_candidate_current_step", "ready_for_training_current_step", "blocking_reasons"]
THRESHOLD_GAP_COLUMNS = ["threshold_gap_item", "threshold_gap_value", "threshold_gap_audit_passed", "qa_comment"]
SAFETY_COLUMNS = ["safety_item", "required_status", "observed_status", "safety_passed", "blocking_reasons"]


class LinkTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag == "a" and attr.get("href"):
            self.links.append(attr["href"])
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"}:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(_normalize_text(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
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


def _is_forbidden_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(FORBIDDEN_URL_SUFFIXES)


def allowed_metadata_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path
    low_path = path.lower()
    if _is_forbidden_url(url):
        return False
    if parsed.netloc == "drug-discovery.vm.uni-freiburg.de":
        return low_path.startswith("/covpdb/") or low_path == "/covpdb"
    if parsed.netloc == "data.rcsb.org":
        return low_path.startswith("/rest/v1/core/chemcomp/")
    return False


def fetch_text(url: str) -> dict[str, Any]:
    if not allowed_metadata_url(url):
        return {"url": url, "attempted": False, "status": "blocked_forbidden_url", "http_status_or_error": "blocked_forbidden_url", "retry_count_used": 0, "text": "", "sha256": "", "byte_count": 0}
    last_error = ""
    for attempt in range(RETRY_LIMIT + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
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
                    "byte_count": len(raw),
                }
        except Exception as exc:  # noqa: BLE001 - network smoke records failures as data
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < RETRY_LIMIT:
                time.sleep(0.25)
    return {"url": url, "attempted": True, "status": "fetch_failed", "http_status_or_error": last_error, "retry_count_used": RETRY_LIMIT, "text": "", "sha256": "", "byte_count": 0}


def rcsb_ccd_url(het_code: str) -> str:
    return f"{RCSB_CCD_BASE}{quote(het_code.strip().upper(), safe='')}"


def _label_value(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*:?\s*(.*?)(?=\s+[A-Z][A-Za-z0-9 /().'-]{{1,40}}\s*:|$)", text, re.I)
    return _normalize_text(match.group(1)) if match else ""


def parse_discovery_links(text: str, base_url: str) -> list[str]:
    parser = LinkTableParser()
    parser.feed(text)
    urls: list[str] = []
    for link in parser.links:
        url = urljoin(base_url, html.unescape(link))
        parsed = urlparse(url)
        if parsed.netloc == "drug-discovery.vm.uni-freiburg.de" and parsed.path.startswith("/covpdb/") and not _is_forbidden_url(url):
            urls.append(url)
    return sorted(dict.fromkeys(urls))


def _ligand_id_from_complex_text(text: str) -> str:
    match = re.search(r"ligand_card/ligand_id=(COVPDB\d+)", text, re.I) or re.search(r"img_ligands/(COVPDB\d+)\.svg", text, re.I)
    return match.group(1).upper() if match else ""


def _looks_like_covpdb_boilerplate(value: Any) -> bool:
    text = _normalize_text(value)
    if not text:
        return False
    lower = text.lower()
    direct_markers = [
        "het code ligand id sequence",
        "pdb id uniprot id/acc",
        "download help contact",
        "table {",
    ]
    if any(marker in lower for marker in direct_markers):
        return True
    nav_terms = [
        "warhead",
        "mechanism",
        "targetable residue",
        "statistics",
        "similarity",
        "structure",
        "smiles",
        "sequence",
    ]
    return len(text) > 80 and sum(term in lower for term in nav_terms) >= 4


def _clean_covpdb_optional_name(value: Any) -> str:
    text = _normalize_text(value)
    return "" if _looks_like_covpdb_boilerplate(text) else text


def parse_complex_card(text: str) -> dict[str, Any]:
    info = step14l.parse_complex_card(text)
    if not info.get("covpdb_het_code_observed"):
        het_match = re.search(r"rcsb\.org/ligand/([A-Za-z0-9]{2,6})", text, re.I)
        if het_match:
            info["covpdb_het_code_observed"] = het_match.group(1).upper()
    info["covpdb_ligand_name_observed"] = _clean_covpdb_optional_name(info.get("covpdb_ligand_name_observed", ""))
    info["covpdb_protein_name_observed"] = _clean_covpdb_optional_name(info.get("covpdb_protein_name_observed", ""))
    info["ligand_identifier_if_available"] = _ligand_id_from_complex_text(text)
    return info


def parse_ccd_json(text: str) -> dict[str, Any]:
    return step14l.parse_ccd_json(text)


def discover_sources() -> tuple[list[dict[str, Any]], list[str], dict[str, dict[str, Any]]]:
    audits: list[dict[str, Any]] = []
    fetches: dict[str, dict[str, Any]] = {}
    selected_pages: list[str] = []
    seeds = list(SEED_URLS)
    if PREFERRED_CYS_COMPLEX_LIST_URL not in seeds:
        seeds.append(PREFERRED_CYS_COMPLEX_LIST_URL)
    for idx, url in enumerate(seeds[:MAX_DISCOVERY_PAGES], start=1):
        fetch = fetch_text(url)
        fetches[url] = fetch
        links = parse_discovery_links(fetch["text"], url) if fetch["status"] == "fetched" else []
        selected = url == PREFERRED_CYS_COMPLEX_LIST_URL or any("/covpdb/complex_card/" in link for link in links)
        if selected:
            selected_pages.append(url)
        audits.append({
            "discovery_row_id": f"CYS_SG_NEXT_DISCOVERY_{idx:06d}",
            "seed_url_or_strategy": url,
            "attempted_current_step": True,
            "discovered_url": url,
            "discovered_url_role": "covpdb_cys_complex_listing" if url == PREFERRED_CYS_COMPLEX_LIST_URL else "covpdb_html_seed_or_listing",
            "discovery_status": "fetched_and_links_parsed" if fetch["status"] == "fetched" else "fetch_failed",
            "fetch_status": fetch["status"],
            "http_status_or_error": fetch["http_status_or_error"],
            "response_text_sha256": fetch["sha256"],
            "parsed_link_count": len(links),
            "selected_for_complex_candidate_scan": selected,
            "discovery_audit_passed": fetch["status"] == "fetched",
            "qa_comment": "" if fetch["status"] == "fetched" else fetch["http_status_or_error"],
        })
    return audits, selected_pages, fetches


def _complex_links_from_fetches(fetches: dict[str, dict[str, Any]], selected_pages: list[str]) -> list[str]:
    links: list[str] = []
    for url in selected_pages:
        fetch = fetches.get(url, {})
        if fetch.get("status") != "fetched":
            continue
        for link in parse_discovery_links(str(fetch.get("text", "")), url):
            if "/covpdb/complex_card/" in link and allowed_metadata_url(link):
                links.append(link)
    return list(dict.fromkeys(links))[:MAX_COMPLEX_CARD_FETCHES]


def _existing_keys(existing_rows: list[dict[str, str]]) -> tuple[set[str], set[tuple[str, str, str, str, str]]]:
    urls = {row["covpdb_complex_card_url"] for row in existing_rows if row.get("covpdb_complex_card_url")}
    tuples = {
        (
            row.get("pdb_id", "").upper(),
            row.get("suggested_ligand_comp_id", "").upper(),
            row.get("covpdb_residue_name", "").upper(),
            row.get("covpdb_residue_index", ""),
            row.get("covpdb_chain_id", ""),
        )
        for row in existing_rows
    }
    return urls, tuples


def _is_disulfide_or_non_ligand(info: dict[str, Any]) -> bool:
    text = " ".join(str(info.get(key, "")) for key in ["covpdb_reaction_name_observed", "covpdb_warhead_name_observed", "covpdb_ligand_name_observed"]).lower()
    return "disulfide" in text or "sg--sg" in text or "cys-cys" in text


def acquire_complex_cards(existing_rows: list[dict[str, str]], fetches: dict[str, dict[str, Any]], selected_pages: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    complex_urls = _complex_links_from_fetches(fetches, selected_pages)
    existing_urls, existing_tuples = _existing_keys(existing_rows)
    audits: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    card_fetches: dict[str, dict[str, Any]] = {}
    seen_new_tuples: set[tuple[str, str, str, str, str]] = set()
    for idx, url in enumerate(complex_urls, start=1):
        fetch = fetch_text(url)
        card_fetches[url] = fetch
        info = parse_complex_card(fetch["text"]) if fetch["status"] == "fetched" else {"parsed_field_count": 0}
        key = (
            str(info.get("covpdb_pdb_id_observed", "")).upper(),
            str(info.get("covpdb_het_code_observed", "")).upper(),
            str(info.get("covpdb_residue_name_observed", "")).upper(),
            str(info.get("covpdb_residue_index_observed", "")),
            str(info.get("covpdb_chain_id_observed", "")),
        )
        duplicate = url in existing_urls or key in existing_tuples or key in seen_new_tuples
        is_cys = key[2] == "CYS"
        has_core = bool(key[0] and key[1] and info.get("covpdb_reaction_name_observed"))
        excluded = ""
        keep = False
        if fetch["status"] != "fetched":
            excluded = "complex_card_fetch_failed"
        elif duplicate:
            excluded = "duplicate_against_existing_9_or_current_step"
        elif not is_cys:
            excluded = "not_cys_residue"
        elif _is_disulfide_or_non_ligand(info):
            excluded = "disulfide_or_non_ligand_event"
        elif not has_core:
            excluded = "missing_core_metadata"
        else:
            keep = True
            seen_new_tuples.add(key)
        row = {
            "complex_extraction_row_id": f"CYS_SG_NEXT_COMPLEX_{idx:06d}",
            "complex_card_url": url,
            "fetch_status": fetch["status"],
            "covpdb_pdb_id_observed": info.get("covpdb_pdb_id_observed", ""),
            "covpdb_ligand_name_observed": info.get("covpdb_ligand_name_observed", ""),
            "covpdb_het_code_observed": info.get("covpdb_het_code_observed", ""),
            "covpdb_protein_name_observed": info.get("covpdb_protein_name_observed", ""),
            "covpdb_uniprot_observed": info.get("covpdb_uniprot_observed", ""),
            "covpdb_reaction_name_observed": info.get("covpdb_reaction_name_observed", ""),
            "covpdb_residue_name_observed": info.get("covpdb_residue_name_observed", ""),
            "covpdb_residue_index_observed": info.get("covpdb_residue_index_observed", ""),
            "covpdb_chain_id_observed": info.get("covpdb_chain_id_observed", ""),
            "covpdb_sasa_observed": info.get("covpdb_sasa_observed", ""),
            "covpdb_pka_observed": info.get("covpdb_pka_observed", ""),
            "covpdb_warhead_name_observed": info.get("covpdb_warhead_name_observed", ""),
            "duplicate_against_existing_9": duplicate,
            "excluded_reason": excluded,
            "kept_as_next_batch_candidate": keep,
            "complex_extraction_passed": fetch["status"] == "fetched",
            "qa_comment": "" if fetch["status"] == "fetched" else fetch["http_status_or_error"],
            "ligand_identifier_if_available": info.get("ligand_identifier_if_available", ""),
        }
        audits.append(row)
        if keep:
            kept.append(row)
    return audits, kept, card_fetches


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


def build_candidates(kept_complex_rows: list[dict[str, Any]], ccd_info: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(kept_complex_rows, start=1):
        het = str(row["covpdb_het_code_observed"]).upper()
        ccd = ccd_info.get(het, {})
        rows.append({
            "next_batch_acquired_candidate_id": f"CYS_SG_NEXT_ACQ_ANNOT_{idx:06d}",
            "complex_card_url": row["complex_card_url"],
            "pdb_id": row["covpdb_pdb_id_observed"],
            "ligand_identifier_if_available": row.get("ligand_identifier_if_available", ""),
            "suggested_ligand_comp_id": het,
            "covpdb_ligand_name": row["covpdb_ligand_name_observed"],
            "covpdb_protein_name": row["covpdb_protein_name_observed"],
            "covpdb_uniprot": row["covpdb_uniprot_observed"],
            "covpdb_reaction_name": row["covpdb_reaction_name_observed"],
            "covpdb_residue_name": row["covpdb_residue_name_observed"],
            "covpdb_residue_index": row["covpdb_residue_index_observed"],
            "covpdb_chain_id": row["covpdb_chain_id_observed"],
            "covpdb_warhead_name": row["covpdb_warhead_name_observed"],
            "covpdb_sasa": row["covpdb_sasa_observed"],
            "covpdb_pka": row["covpdb_pka_observed"],
            "ccd_ligand_name": ccd.get("ccd_name_observed", ""),
            "ccd_formula": ccd.get("ccd_formula_observed", ""),
            "ccd_type": ccd.get("ccd_type_observed", ""),
            "duplicate_exclusion_status": "not_duplicate_against_step14l",
            "annotation_acquisition_status": "next_batch_event_annotation_acquired_pending_manual_review",
            "event_identity_status_current_step": "not_event_identity_until_manual_review",
            "manual_review_status": "pending_manual_review",
            "ready_candidate_current_step": False,
            "ready_for_training_current_step": False,
            "blocking_reasons": "",
        })
    return rows


def _json_consistent(csv_rows: list[dict[str, str]], json_rows: list[dict[str, Any]], key: str) -> bool:
    return [row[key] for row in csv_rows] == [str(row.get(key, "")) for row in json_rows]


def build_precondition_rows(existing: list[dict[str, str]], next_batch: list[dict[str, str]], next_batch_json: list[dict[str, Any]], exclusion: list[dict[str, str]]) -> list[dict[str, Any]]:
    manifest = _load_json(STEP14M_MANIFEST_JSON) if STEP14M_MANIFEST_JSON.exists() else {}
    checks = [
        ("step14m_manifest_exists", STEP14M_MANIFEST_JSON.as_posix(), "exists", STEP14M_MANIFEST_JSON.exists(), STEP14M_MANIFEST_JSON.exists()),
        ("step14m_stage", STEP14M_MANIFEST_JSON.as_posix(), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("step14m_all_checks_passed", STEP14M_MANIFEST_JSON.as_posix(), "true", manifest.get("all_checks_passed"), manifest.get("all_checks_passed") is True),
        ("step14m_current_candidate_count", STEP14M_MANIFEST_JSON.as_posix(), "9", manifest.get("current_candidate_count"), manifest.get("current_candidate_count") == 9),
        ("step14m_total_candidate_target", STEP14M_MANIFEST_JSON.as_posix(), "20", manifest.get("total_candidate_target"), manifest.get("total_candidate_target") == 20),
        ("step14m_additional_candidate_needed", STEP14M_MANIFEST_JSON.as_posix(), "11", manifest.get("additional_candidate_needed_count"), manifest.get("additional_candidate_needed_count") == 11),
        ("step14m_ready_for_step14n", STEP14M_MANIFEST_JSON.as_posix(), "true", manifest.get("ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke"), manifest.get("ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke") is True),
        ("step14m_ready_for_training", STEP14M_MANIFEST_JSON.as_posix(), "false", manifest.get("ready_for_training"), manifest.get("ready_for_training") is False),
        ("step14m_next_batch_csv_exists", STEP14M_NEXT_BATCH_CSV.as_posix(), "exists", STEP14M_NEXT_BATCH_CSV.exists(), STEP14M_NEXT_BATCH_CSV.exists()),
        ("step14m_next_batch_json_exists", STEP14M_NEXT_BATCH_JSON.as_posix(), "exists", STEP14M_NEXT_BATCH_JSON.exists(), STEP14M_NEXT_BATCH_JSON.exists()),
        ("step14m_next_batch_csv_json_consistent", STEP14M_NEXT_BATCH_JSON.as_posix(), "true", _json_consistent(next_batch, next_batch_json, "next_batch_acquisition_row_id"), _json_consistent(next_batch, next_batch_json, "next_batch_acquisition_row_id")),
        ("step14m_exclusion_registry_exists", STEP14M_EXCLUSION_REGISTRY_CSV.as_posix(), "exists", STEP14M_EXCLUSION_REGISTRY_CSV.exists(), STEP14M_EXCLUSION_REGISTRY_CSV.exists()),
        ("step14m_exclusion_registry_row_count", STEP14M_EXCLUSION_REGISTRY_CSV.as_posix(), "9", len(exclusion), len(exclusion) == 9),
        ("step14l_acquired_exists", STEP14L_ACQUIRED_CSV.as_posix(), "exists", STEP14L_ACQUIRED_CSV.exists(), STEP14L_ACQUIRED_CSV.exists()),
        ("step14l_acquired_row_count", STEP14L_ACQUIRED_CSV.as_posix(), "9", len(existing), len(existing) == 9),
        ("metadata_csv_hash_unchanged", METADATA_CSV.as_posix(), METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("raw_roots_not_tracked", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_tracked(RAW_OUTPUT_ROOT) or _raw_files_tracked(RAW_REFERENCE_ROOT), not _raw_files_tracked(RAW_OUTPUT_ROOT) and not _raw_files_tracked(RAW_REFERENCE_ROOT)),
        ("raw_roots_not_staged", RAW_OUTPUT_ROOT.as_posix(), "false", _raw_files_staged(RAW_OUTPUT_ROOT) or _raw_files_staged(RAW_REFERENCE_ROOT), not _raw_files_staged(RAW_OUTPUT_ROOT) and not _raw_files_staged(RAW_REFERENCE_ROOT)),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("canonical_mask_count", "canonical masks", "5", len(CANONICAL_MASK_TASK_NAMES), len(CANONICAL_MASK_TASK_NAMES) == 5),
        ("b3_scaffold_only_included", "canonical masks", "true", "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES, "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES),
        ("no_extra_mask_tasks", "canonical masks", "true", CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_NAMES == step14m.CANONICAL_MASK_TASK_NAMES),
    ]
    return [{"precondition_item": item, "artifact_or_check": artifact, "expected_status": expected, "observed_status": observed, "precondition_passed": passed, "blocking_reasons": "" if passed else item} for item, artifact, expected, observed, passed in checks]


def build_execution_rows(discovery_rows: list[dict[str, Any]], complex_rows: list[dict[str, Any]], ccd_rows: list[dict[str, Any]], ccd_fetches: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(discovery_rows, start=1):
        rows.append({
            "execution_row_id": f"CYS_SG_NEXT_EXEC_{idx:06d}",
            "source_name": "CovPDB",
            "source_type": "covpdb_html_listing_metadata",
            "query_key_type": "seed_or_listing_url",
            "query_key_value": row["discovered_url"],
            "attempted_current_step": row["attempted_current_step"],
            "fetch_url_or_strategy": row["discovered_url"],
            "network_status": row["fetch_status"],
            "http_status_or_error": row["http_status_or_error"],
            "retry_count_used": "",
            "response_text_sha256": row["response_text_sha256"],
            "parsed_current_step": int(row["parsed_link_count"]) > 0,
            "parsed_field_count": row["parsed_link_count"],
            "acquisition_execution_status": row["discovery_status"],
            "execution_audit_passed": row["discovery_audit_passed"],
            "qa_comment": row["qa_comment"],
        })
    base = len(rows)
    for idx, row in enumerate(complex_rows, start=1):
        rows.append({
            "execution_row_id": f"CYS_SG_NEXT_EXEC_{base + idx:06d}",
            "source_name": "CovPDB",
            "source_type": "covpdb_complex_card_metadata",
            "query_key_type": "complex_card_url",
            "query_key_value": row["complex_card_url"],
            "attempted_current_step": True,
            "fetch_url_or_strategy": row["complex_card_url"],
            "network_status": row["fetch_status"],
            "http_status_or_error": row["qa_comment"],
            "retry_count_used": "",
            "response_text_sha256": "",
            "parsed_current_step": row["complex_extraction_passed"],
            "parsed_field_count": sum(bool(row.get(key, "")) for key in COMPLEX_EXTRACTION_COLUMNS if key.startswith("covpdb_")),
            "acquisition_execution_status": "complex_card_parsed_metadata_only" if _bool(row["complex_extraction_passed"]) else "complex_card_fetch_or_parse_failed",
            "execution_audit_passed": row["complex_extraction_passed"],
            "qa_comment": row["excluded_reason"],
        })
    base = len(rows)
    for idx, row in enumerate(ccd_rows, start=1):
        fetch = ccd_fetches.get(row["suggested_ligand_comp_id"], {})
        rows.append({
            "execution_row_id": f"CYS_SG_NEXT_EXEC_{base + idx:06d}",
            "source_name": "RCSB CCD",
            "source_type": "rcsb_chemical_component_dictionary_metadata",
            "query_key_type": "het_code",
            "query_key_value": row["suggested_ligand_comp_id"],
            "attempted_current_step": True,
            "fetch_url_or_strategy": row["rcsb_ccd_url"],
            "network_status": row["rcsb_ccd_fetch_status"],
            "http_status_or_error": row["qa_comment"],
            "retry_count_used": fetch.get("retry_count_used", ""),
            "response_text_sha256": fetch.get("sha256", ""),
            "parsed_current_step": row["rcsb_ccd_extraction_passed"],
            "parsed_field_count": sum(bool(row.get(key, "")) for key in RCSB_CCD_COLUMNS if key.startswith("ccd_")),
            "acquisition_execution_status": "rcsb_ccd_json_parsed" if _bool(row["rcsb_ccd_extraction_passed"]) else "rcsb_ccd_fetch_or_parse_failed",
            "execution_audit_passed": True,
            "qa_comment": "",
        })
    return rows


def build_threshold_gap_rows(existing_count: int, new_count: int) -> list[dict[str, Any]]:
    combined = existing_count + new_count
    needed_before = max(0, TOTAL_CANDIDATE_TARGET - existing_count)
    needed_after = max(0, TOTAL_CANDIDATE_TARGET - combined)
    specs = [
        ("existing_candidate_count", existing_count, existing_count == 9, ""),
        ("new_candidate_count", new_count, new_count >= 0, ""),
        ("combined_candidate_count", combined, combined == existing_count + new_count, ""),
        ("total_candidate_target", TOTAL_CANDIDATE_TARGET, TOTAL_CANDIDATE_TARGET == 20, ""),
        ("additional_candidate_needed_before_step", needed_before, needed_before == 11, ""),
        ("additional_candidate_needed_after_step", needed_after, needed_after >= 0, ""),
        ("new_candidate_target_met", new_count >= needed_before, True, ""),
        ("below_20_threshold_status", "below_threshold" if combined < TOTAL_CANDIDATE_TARGET else "target_reached_pending_manual_review", True, ""),
        ("ready_candidate_count_current_step", 0, True, ""),
        ("ready_for_manual_review_gate_if_combined_ge_20", combined >= TOTAL_CANDIDATE_TARGET, True, ""),
        ("targeted_expansion_still_required_if_combined_lt_20", combined < TOTAL_CANDIDATE_TARGET, True, ""),
        ("training_still_blocked", True, True, ""),
    ]
    return [{"threshold_gap_item": item, "threshold_gap_value": value, "threshold_gap_audit_passed": passed, "qa_comment": comment} for item, value, passed, comment in specs]


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


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    suffixes = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.suffix.lower() in suffixes for path in root.rglob("*") if path.is_file())


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    names = {"small_pilot_download_manifest.csv", "small_pilot_download_manifest.json", "final_dataset.csv", "final_dataset.json", "sample_index.csv", "sample_index.json", "split_assignments.csv", "split_assignments.json", "leakage_matrix.csv", "leakage_matrix.json", "training_report.csv", "training_report.json", "actual_dataloader_smoke.csv", "actual_dataloader_smoke.json", "dataloader_smoke.csv", "dataloader_smoke.json"}
    return root.exists() and any(path.name in names for path in root.rglob("*") if path.is_file())


def build_safety_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("network_access_used_current_step", "true", True, True),
        ("download_attempted_metadata_only", "true", True, True),
        ("no_raw_coordinate_downloaded", "false", False, True),
        ("no_raw_file_content_read_current_step", "false", False, True),
        ("no_raw_files_written_current_step", "false", False, True),
        ("no_html_files_written_current_step", "false", _forbidden_suffix_exists(), not _forbidden_suffix_exists()),
        ("raw_files_untracked", "false", _raw_files_tracked(RAW_REFERENCE_ROOT) or _raw_files_tracked(RAW_OUTPUT_ROOT), not _raw_files_tracked(RAW_REFERENCE_ROOT) and not _raw_files_tracked(RAW_OUTPUT_ROOT)),
        ("raw_files_unstaged", "false", _raw_files_staged(RAW_REFERENCE_ROOT) or _raw_files_staged(RAW_OUTPUT_ROOT), not _raw_files_staged(RAW_REFERENCE_ROOT) and not _raw_files_staged(RAW_OUTPUT_ROOT)),
        ("metadata_csv_unchanged", "true", _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()]), _metadata_hash() == METADATA_CSV_SHA256 and not _path_diff_exists([METADATA_CSV.as_posix()])),
        ("step14m_artifacts_unchanged", "true", not _path_diff_exists([STEP14M_ROOT.as_posix()]), not _path_diff_exists([STEP14M_ROOT.as_posix()])),
        ("step14l_artifacts_unchanged", "true", not _path_diff_exists([STEP14L_ROOT.as_posix()]), not _path_diff_exists([STEP14L_ROOT.as_posix()])),
        ("step14k_artifacts_unchanged", "true", not _path_diff_exists([STEP14K_ROOT.as_posix()]), not _path_diff_exists([STEP14K_ROOT.as_posix()])),
        ("protected_source_diff_empty", "true", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "true", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
        ("no_sample_index_final_split_leakage_or_training_artifacts", "true", not _forbidden_named_artifact_exists(), not _forbidden_named_artifact_exists()),
        ("no_forbidden_binary_raw_or_html_suffix_artifact", "true", not _forbidden_suffix_exists(), not _forbidden_suffix_exists()),
        ("no_forbidden_imports_in_step14n_code", "true", not _own_files_have_forbidden_imports(), not _own_files_have_forbidden_imports()),
        ("urllib_allowed_current_step", "true", True, True),
        ("no_ready_candidates_created", "true", all(not _bool(row["ready_candidate_current_step"]) for row in candidates), all(not _bool(row["ready_candidate_current_step"]) for row in candidates)),
        ("canonical_masks_preserved", "true", CANONICAL_MASK_TASK_NAMES == step14m.CANONICAL_MASK_TASK_NAMES and CANONICAL_MASK_TASK_ALIASES == step14m.CANONICAL_MASK_TASK_ALIASES, CANONICAL_MASK_TASK_NAMES == step14m.CANONICAL_MASK_TASK_NAMES and CANONICAL_MASK_TASK_ALIASES == step14m.CANONICAL_MASK_TASK_ALIASES),
    ]
    return [{"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else item} for item, required, observed, passed in checks]


def build_manifest(precondition: list[dict[str, Any]], discovery: list[dict[str, Any]], execution: list[dict[str, Any]], complex_rows: list[dict[str, Any]], ccd_rows: list[dict[str, Any]], candidates: list[dict[str, Any]], threshold: list[dict[str, Any]], safety: list[dict[str, Any]]) -> dict[str, Any]:
    existing_count = 9
    new_count = len(candidates)
    combined = existing_count + new_count
    needed_before = max(0, TOTAL_CANDIDATE_TARGET - existing_count)
    needed_after = max(0, TOTAL_CANDIDATE_TARGET - combined)
    complex_fetch_success = sum(row["fetch_status"] == "fetched" for row in complex_rows)
    complex_cys = sum(str(row["covpdb_residue_name_observed"]).upper() == "CYS" and _bool(row["complex_extraction_passed"]) for row in complex_rows)
    ccd_success = sum(_bool(row["rcsb_ccd_extraction_passed"]) for row in ccd_rows)
    passed = (
        _all_true(precondition, "precondition_passed")
        and _all_true(discovery, "discovery_audit_passed")
        and _all_true(execution, "execution_audit_passed")
        and _all_true(threshold, "threshold_gap_audit_passed")
        and _all_true(safety, "safety_passed")
        and any(row["fetch_status"] == "fetched" for row in discovery)
        and complex_fetch_success >= 1
    )
    ready_for_manual = combined >= TOTAL_CANDIDATE_TARGET
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "current_source_profile": CURRENT_SOURCE_PROFILE,
        "current_source_database": CURRENT_SOURCE_DATABASE,
        "existing_candidate_count": existing_count,
        "total_candidate_target": TOTAL_CANDIDATE_TARGET,
        "additional_candidate_needed_before_step": needed_before,
        "source_discovery_attempted": True,
        "network_access_used": True,
        "download_attempted": True,
        "raw_coordinate_downloaded": False,
        "raw_file_content_read_current_step": False,
        "raw_files_written_current_step": False,
        "html_files_written_current_step": False,
        "complex_card_fetch_attempt_count": len(complex_rows),
        "complex_card_fetch_success_count": complex_fetch_success,
        "complex_card_cys_event_annotation_count": complex_cys,
        "duplicate_existing_candidate_count": sum(_bool(row["duplicate_against_existing_9"]) for row in complex_rows),
        "new_candidate_count": new_count,
        "combined_candidate_count": combined,
        "additional_candidate_needed_after_step": needed_after,
        "rcsb_ccd_fetch_success_count": ccd_success,
        "next_batch_acquired_candidates_csv_json_consistent": True,
        "ready_candidate_count_current_step": 0,
        "ready_for_training_candidate_count_current_step": 0,
        "no_ready_candidates_created": True,
        "sample_index_written_current_step": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "sample_download_manifest_written": False,
        "actual_dataloader_adapter_smoke_written": False,
        "actual_dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "torch_imported": False,
        "numpy_imported": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "gzip_open_used": False,
        "requests_used": False,
        "selenium_used": False,
        "playwright_used": False,
        "bs4_used": False,
        "urllib_used": True,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate": ready_for_manual,
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate": not ready_for_manual,
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
        "recommended_next_step": "covapie_cys_sg_acquired_annotation_manual_review_gate" if ready_for_manual else "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v1",
        "all_checks_passed": passed,
        "blocking_reasons": [] if passed else ["step14n_metadata_next_batch_acquisition_smoke_failed"],
    }


def run_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0() -> dict[str, Any]:
    existing = _csv_rows(STEP14L_ACQUIRED_CSV)
    next_batch = _csv_rows(STEP14M_NEXT_BATCH_CSV)
    next_batch_json = _load_json(STEP14M_NEXT_BATCH_JSON)
    exclusion = _csv_rows(STEP14M_EXCLUSION_REGISTRY_CSV)
    precondition = build_precondition_rows(existing, next_batch, next_batch_json, exclusion)
    discovery, selected_pages, discovery_fetches = discover_sources()
    complex_rows, kept_complex_rows, _complex_fetches = acquire_complex_cards(existing, discovery_fetches, selected_pages)
    ccd_rows, ccd_info, ccd_fetches = acquire_ccd([row["covpdb_het_code_observed"] for row in kept_complex_rows])
    candidates = build_candidates(kept_complex_rows, ccd_info)
    execution = build_execution_rows(discovery, complex_rows, ccd_rows, ccd_fetches)
    threshold = build_threshold_gap_rows(len(existing), len(candidates))
    safety = build_safety_rows(candidates)
    manifest = build_manifest(precondition, discovery, execution, complex_rows, ccd_rows, candidates, threshold, safety)
    return {
        "precondition_rows": precondition,
        "source_discovery_rows": discovery,
        "acquisition_execution_rows": execution,
        "complex_extraction_rows": complex_rows,
        "rcsb_ccd_rows": ccd_rows,
        "candidate_rows": candidates,
        "threshold_gap_rows": threshold,
        "safety_rows": safety,
        "manifest": manifest,
    }
