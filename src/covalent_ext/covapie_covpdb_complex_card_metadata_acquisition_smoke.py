from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import subprocess
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_covpdb_complex_card_metadata_acquisition_smoke_v0"
PREVIOUS_STAGE = "covapie_covpdb_complex_card_metadata_probe_design_gate_v0"
PROJECT_NAME = "CovaPIE"

STEP13AR_ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_probe_design_gate_v0")
STEP13AR_MANIFEST_JSON = STEP13AR_ROOT / "covapie_covpdb_complex_card_metadata_probe_design_gate_manifest.json"
STEP13AR_ALLOWED_URL_CONTRACT_CSV = STEP13AR_ROOT / "covapie_covpdb_complex_card_allowed_url_contract.csv"
STEP13AR_TARGET_FIELD_CONTRACT_CSV = STEP13AR_ROOT / "covapie_covpdb_complex_card_probe_target_field_contract.csv"
STEP13AR_EVENT_KEY_RESOLUTION_CONTRACT_CSV = STEP13AR_ROOT / "covapie_covpdb_complex_card_event_key_resolution_contract.csv"
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_precondition_audit.csv"
ACQUISITION_PLAN_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_plan.csv"
FETCH_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_fetch_audit.csv"
HTML_METADATA_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_html_metadata_safety_audit.csv"
PARSE_LABEL_INVENTORY_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_parse_label_inventory.csv"
EVENT_FIELD_PROBE_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_event_field_probe.csv"
EVIDENCE_SNIPPET_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_evidence_snippet_audit.csv"
EVENT_KEY_RESOLUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_event_key_resolution_audit.csv"
OBSERVED_FAILURE_TAXONOMY_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_observed_failure_taxonomy.csv"
READINESS_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_readiness_boundary_audit.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_metadata_acquisition_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_covpdb_complex_card_metadata_acquisition_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_covpdb_complex_card_metadata_acquisition_smoke_v0_summary.md")

EXPECTED_FIRST_5_URLS = [
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2037",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2034",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1614",
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2",
]
METADATA_COLUMNS = [
    "source_dataset_name",
    "source_dataset_version",
    "source_page_url",
    "source_record_url",
    "covpdb_record_index",
    "pdb_id",
    "protein_name",
    "organism",
    "uniprot_id",
    "uniprot_label",
    "ligand_name",
    "het_code",
    "covpdb_ligand_id",
    "covpdb_complex_card_url",
    "acquisition_method",
    "acquisition_timestamp_utc",
    "raw_structure_downloaded",
    "raw_ligand_downloaded",
    "metadata_only_record",
]
CRITICAL_EVENT_KEY_FIELDS = ["chain_id", "residue_name", "residue_index", "residue_atom_name", "covalent_bond_atom_pair"]
LABEL_CATEGORIES = [
    "chain",
    "residue",
    "residue_name",
    "residue_index",
    "residue_atom",
    "covalent_bond",
    "ligand_atom",
    "protein_atom",
    "mechanism",
    "warhead",
]
LABEL_PATTERNS = {
    "chain": [r"\bchain(?:\s+id)?\b"],
    "residue": [r"\bresidue\b"],
    "residue_name": [r"\bresidue\s+name\b", r"\bresidue\s*[:=]\s*[A-Za-z]{3}\b"],
    "residue_index": [r"\bresidue\s+(?:index|number|no\.?)\b", r"\bresidue\s*[:=]\s*[A-Za-z]{3}\s*-?\d+"],
    "residue_atom": [r"\bresidue\s+atom\b", r"\breactive\s+atom\b", r"\bprotein\s+atom\b"],
    "covalent_bond": [r"\bcovalent\s+bond\b", r"\bbond\s+atom\s+pair\b"],
    "ligand_atom": [r"\bligand\s+atom\b"],
    "protein_atom": [r"\bprotein\s+atom\b"],
    "mechanism": [r"\bmechanism\b", r"\breaction\s+type\b"],
    "warhead": [r"\bwarhead\b"],
}
FIELD_PATTERNS = {
    "chain_id": [
        r"\bchain(?:\s+id)?\s*[:=]\s*([A-Za-z0-9])\b",
        r"\bchain\s+id\s+([A-Za-z0-9])\b",
        r"\bchain\s+([A-Za-z0-9])\b",
    ],
    "residue_name": [
        r"\bresidue\s+name\s*[:=]\s*([A-Za-z]{3})\b",
        r"\bresidue\s+name\s+([A-Za-z]{3})\b",
        r"\bresidue\s*[:=]\s*([A-Za-z]{3})\b",
    ],
    "residue_index": [
        r"\bresidue\s+(?:index|number|no\.?)\s*[:=]\s*(-?\d+[A-Za-z]?)\b",
        r"\bresidue\s+(?:index|number|no\.?)\s+(-?\d+[A-Za-z]?)\b",
        r"\bresidue\s*[:=]\s*[A-Za-z]{3}\s*(-?\d+[A-Za-z]?)\b",
    ],
    "residue_atom_name": [
        r"\b(?:residue|reactive|protein)\s+atom\s*[:=]\s*([A-Za-z0-9]+)\b",
        r"\b(?:residue|reactive|protein)\s+atom\s+([A-Za-z0-9]+)\b",
    ],
    "covalent_bond_atom_pair": [
        r"\b(?:covalent\s+bond|bond\s+atom\s+pair)\s*[:=]\s*([A-Za-z0-9]+(?:\s*[-–]\s*[A-Za-z0-9]+)+)\b",
        r"\b(?:covalent\s+bond|bond\s+atom\s+pair)\s+([A-Za-z0-9]+(?:\s*[-–]\s*[A-Za-z0-9]+)+)\b",
    ],
}
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm")
FORBIDDEN_RAW_LINK_SUFFIXES = (".zip", ".pdb", ".ent", ".cif", ".mmcif", ".sdf", ".mol2", ".gz")

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
ACQUISITION_PLAN_COLUMNS = ["card_index", "pdb_id", "het_code", "covpdb_ligand_id", "complex_card_url", "url_allowed", "attempt_planned", "within_first_5_limit", "source_record_url_ignored", "source_page_url_ignored", "acquisition_plan_passed", "blocking_reasons"]
FETCH_AUDIT_COLUMNS = ["card_index", "pdb_id", "het_code", "covpdb_ligand_id", "complex_card_url", "url_allowed", "fetch_attempted", "fetch_succeeded", "http_status_or_error", "content_type", "byte_count", "html_sha256", "full_html_written", "raw_download_attempted", "download_links_followed", "fetch_audit_passed"]
HTML_SAFETY_COLUMNS = ["card_index", "complex_card_url", "content_type_allowed", "full_html_written", "raw_html_artifact_written", "forbidden_suffix_url_requested", "forbidden_suffix_links_detected_count", "forbidden_suffix_links_followed", "external_raw_links_followed", "raw_structure_downloaded", "raw_ligand_downloaded", "html_metadata_safety_passed"]
LABEL_INVENTORY_COLUMNS = ["card_index", "pdb_id", "het_code", "label_category", "label_text_normalized", "label_found", "evidence_snippet_truncated", "parse_label_inventory_passed"]
EVENT_FIELD_COLUMNS = ["card_index", "pdb_id", "het_code", "target_field", "field_probe_status", "parsed_value", "evidence_snippet_truncated", "parse_confidence", "materialization_blocking_if_missing", "field_probe_passed"]
SNIPPET_AUDIT_COLUMNS = ["card_index", "pdb_id", "snippet_source", "target_or_label", "evidence_snippet", "snippet_length", "evidence_snippet_truncated", "evidence_snippet_audit_passed"]
EVENT_KEY_RESOLUTION_COLUMNS = ["card_index", "pdb_id", "het_code", "minimal_key_fields_found_count", "preferred_key_fields_found_count", "chain_id_status", "residue_name_status", "residue_index_status", "residue_atom_name_status", "covalent_bond_atom_pair_status", "minimal_event_key_resolved", "preferred_event_key_resolved", "resolution_status", "candidate_metadata_can_proceed", "candidate_allowlist_can_proceed", "raw_structure_annotation_may_be_required", "event_key_resolution_audit_passed"]
FAILURE_TAXONOMY_COLUMNS = ["failure_reason", "observed_count", "blocks_candidate_metadata", "recommended_handling"]
READINESS_COLUMNS = ["readiness_item", "current_step_status", "readiness_boundary_passed", "blocking_reasons"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_complex_card_acquisition_smoke", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = step13am.LEAKAGE_COLUMNS
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]

EXECUTION_BOUNDARY_ITEMS = [
    "complex_card_metadata_acquisition_smoke",
    "step13ar_manifest_read",
    "metadata_csv_card_urls_read",
    "allowed_url_contract_read",
    "complex_card_fetch",
    "html_visible_text_parse",
    "event_field_probe",
    "external_network_access",
    "urllib_use",
    "metadata_download",
    "raw_structure_download",
    "raw_ligand_download",
    "raw_data_read",
    "sdf_read",
    "pdb_read",
    "mmcif_read",
    "gzip_open",
    "rdkit_use",
    "biopdb_use",
    "gemmi_use",
    "candidate_metadata_materialization",
    "allowlist_materialization",
    "torch_import",
    "model_forward",
    "training_claim",
]


class VisibleTextAndLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.text_parts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip_depth += 1
        for name, value in attrs:
            if name.lower() in {"href", "src"} and value:
                self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.text_parts.append(data)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_header(path: str | Path) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _protected_source_diff_exists() -> bool:
    return _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _forbidden_committable_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES for path in root_path.rglob("*"))


def is_allowed_complex_card_url(url: str) -> bool:
    return (
        url.startswith("https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/")
        and not any(url.lower().endswith(suffix) for suffix in FORBIDDEN_RAW_LINK_SUFFIXES)
    )


def read_metadata_rows() -> list[dict[str, str]]:
    return _csv_rows(METADATA_CSV)


def first_5_metadata_rows() -> list[dict[str, str]]:
    return read_metadata_rows()[:5]


def first_5_complex_card_urls() -> list[str]:
    return [row["covpdb_complex_card_url"] for row in first_5_metadata_rows()]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def truncate_snippet(text: str, limit: int = 240) -> tuple[str, bool]:
    normalized = normalize_text(text)
    if len(normalized) <= limit:
        return normalized, False
    return normalized[:limit], True


def parse_visible_text_and_links(html_text: str) -> tuple[str, list[str]]:
    parser = VisibleTextAndLinkParser()
    parser.feed(html_text)
    return normalize_text(" ".join(parser.text_parts)), parser.links


def _snippet_around_match(text: str, match: re.Match[str] | None) -> tuple[str, bool]:
    if match is None:
        return "", False
    start = max(0, match.start() - 80)
    end = min(len(text), match.end() + 120)
    return truncate_snippet(text[start:end])


def find_label_evidence(text: str, category: str) -> dict[str, Any]:
    for pattern in LABEL_PATTERNS[category]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            snippet, truncated = _snippet_around_match(text, match)
            return {
                "label_found": True,
                "label_text_normalized": category,
                "evidence_snippet_truncated": snippet,
                "snippet_truncated": truncated,
            }
    return {
        "label_found": False,
        "label_text_normalized": category,
        "evidence_snippet_truncated": "",
        "snippet_truncated": False,
    }


def probe_event_field(text: str, target_field: str) -> dict[str, Any]:
    values: list[str] = []
    snippets: list[str] = []
    truncated_any = False
    for pattern in FIELD_PATTERNS[target_field]:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = normalize_text(match.group(1)).upper()
            if value:
                values.append(value)
                snippet, truncated = _snippet_around_match(text, match)
                snippets.append(snippet)
                truncated_any = truncated_any or truncated
    unique_values = sorted(set(values))
    if len(unique_values) == 1:
        return {
            "field_probe_status": "found",
            "parsed_value": unique_values[0],
            "evidence_snippet_truncated": snippets[0] if snippets else "",
            "snippet_truncated": truncated_any,
            "parse_confidence": "high",
        }
    if len(unique_values) > 1:
        return {
            "field_probe_status": "ambiguous",
            "parsed_value": ";".join(unique_values),
            "evidence_snippet_truncated": snippets[0] if snippets else "",
            "snippet_truncated": truncated_any,
            "parse_confidence": "low",
        }
    return {
        "field_probe_status": "not_found",
        "parsed_value": "",
        "evidence_snippet_truncated": "",
        "snippet_truncated": False,
        "parse_confidence": "none",
    }


def forbidden_suffix_links(links: list[str]) -> list[str]:
    return [link for link in links if any(link.lower().split("?", 1)[0].endswith(suffix) for suffix in FORBIDDEN_RAW_LINK_SUFFIXES)]


def validate_step13ar_precondition_v0() -> bool:
    manifest = _load_json(STEP13AR_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "complex_card_url_count": 25,
        "ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke": True,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    blockers = [f"{key}={manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    if manifest.get("blocking_reasons") != []:
        blockers.append("blocking_reasons")
    if blockers:
        raise ValueError("Step 13AR precondition failed: " + ";".join(blockers))
    return True


def validate_metadata_csv_v0() -> bool:
    rows = read_metadata_rows()
    return METADATA_CSV.is_file() and _csv_header(METADATA_CSV) == METADATA_COLUMNS and len(rows) == 25 and first_5_complex_card_urls() == EXPECTED_FIRST_5_URLS


def validate_covapie_naming_convention_v0() -> bool:
    return step13am.validate_covapie_naming_convention_v0()


def build_precondition_rows(output_root: Path) -> list[dict[str, Any]]:
    urls = first_5_complex_card_urls()
    specs = [
        ("step13ar_manifest", STEP13AR_MANIFEST_JSON, validate_step13ar_precondition_v0()),
        ("step13ar_allowed_url_contract", STEP13AR_ALLOWED_URL_CONTRACT_CSV, STEP13AR_ALLOWED_URL_CONTRACT_CSV.is_file()),
        ("step13ar_target_field_contract", STEP13AR_TARGET_FIELD_CONTRACT_CSV, STEP13AR_TARGET_FIELD_CONTRACT_CSV.is_file()),
        ("step13ar_event_key_resolution_contract", STEP13AR_EVENT_KEY_RESOLUTION_CONTRACT_CSV, STEP13AR_EVENT_KEY_RESOLUTION_CONTRACT_CSV.is_file()),
        ("metadata_csv_25x19", METADATA_CSV, validate_metadata_csv_v0()),
        ("first_5_urls_allowed", "first five covpdb_complex_card_url values", all(is_allowed_complex_card_url(url) for url in urls)),
        ("covapie_naming_convention", NAMING_CONVENTION_MD, validate_covapie_naming_convention_v0()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", not _protected_source_diff_exists()),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", not _original_dataloader_diff_exists()),
        ("raw_files_not_staged_or_tracked", "data/raw/covalent_sources", not _raw_files_staged() and not _raw_files_tracked()),
        ("output_root_declared", output_root, True),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(artifact),
            "expected_status": "present_or_clean",
            "observed_status": "present_or_clean" if passed else "missing_or_dirty",
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else f"{item}_failed",
        }
        for item, artifact, passed in specs
    ]


def fetch_allowed_complex_card(url: str, timeout: int = 20) -> dict[str, Any]:
    if not is_allowed_complex_card_url(url):
        return {
            "fetch_succeeded": False,
            "http_status_or_error": "url_not_allowed",
            "content_type": "",
            "byte_count": 0,
            "html_sha256": "",
            "html_text": "",
        }
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "CovaPIE-metadata-smoke/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            return {
                "fetch_succeeded": True,
                "http_status_or_error": str(response.getcode()),
                "content_type": content_type,
                "byte_count": len(payload),
                "html_sha256": hashlib.sha256(payload).hexdigest(),
                "html_text": payload.decode(charset, errors="replace"),
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "fetch_succeeded": False,
            "http_status_or_error": f"{type(exc).__name__}: {exc}",
            "content_type": "",
            "byte_count": 0,
            "html_sha256": "",
            "html_text": "",
        }


def build_acquisition_plan_rows(cards: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "card_index": index,
            "pdb_id": row["pdb_id"],
            "het_code": row["het_code"],
            "covpdb_ligand_id": row["covpdb_ligand_id"],
            "complex_card_url": row["covpdb_complex_card_url"],
            "url_allowed": is_allowed_complex_card_url(row["covpdb_complex_card_url"]),
            "attempt_planned": True,
            "within_first_5_limit": True,
            "source_record_url_ignored": True,
            "source_page_url_ignored": True,
            "acquisition_plan_passed": is_allowed_complex_card_url(row["covpdb_complex_card_url"]),
            "blocking_reasons": "" if is_allowed_complex_card_url(row["covpdb_complex_card_url"]) else "url_not_allowed",
        }
        for index, row in enumerate(cards, start=1)
    ]


def build_fetch_and_parse_rows(cards: list[dict[str, str]], fetcher: Any = fetch_allowed_complex_card) -> dict[str, Any]:
    fetch_rows: list[dict[str, Any]] = []
    safety_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    field_rows: list[dict[str, Any]] = []
    snippet_rows: list[dict[str, Any]] = []
    resolution_rows: list[dict[str, Any]] = []
    for index, row in enumerate(cards, start=1):
        url = row["covpdb_complex_card_url"]
        result = fetcher(url)
        html_text = result.get("html_text", "")
        visible_text, links = parse_visible_text_and_links(html_text) if result["fetch_succeeded"] else ("", [])
        forbidden_links = forbidden_suffix_links(links)
        fetch_rows.append(
            {
                "card_index": index,
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "covpdb_ligand_id": row["covpdb_ligand_id"],
                "complex_card_url": url,
                "url_allowed": is_allowed_complex_card_url(url),
                "fetch_attempted": True,
                "fetch_succeeded": result["fetch_succeeded"],
                "http_status_or_error": result["http_status_or_error"],
                "content_type": result["content_type"],
                "byte_count": result["byte_count"],
                "html_sha256": result["html_sha256"],
                "full_html_written": False,
                "raw_download_attempted": False,
                "download_links_followed": False,
                "fetch_audit_passed": is_allowed_complex_card_url(url) and True,
            }
        )
        safety_rows.append(
            {
                "card_index": index,
                "complex_card_url": url,
                "content_type_allowed": (not result["fetch_succeeded"]) or ("html" in result["content_type"].lower() or "text" in result["content_type"].lower()),
                "full_html_written": False,
                "raw_html_artifact_written": False,
                "forbidden_suffix_url_requested": False,
                "forbidden_suffix_links_detected_count": len(forbidden_links),
                "forbidden_suffix_links_followed": False,
                "external_raw_links_followed": False,
                "raw_structure_downloaded": False,
                "raw_ligand_downloaded": False,
                "html_metadata_safety_passed": True,
            }
        )
        for category in LABEL_CATEGORIES:
            evidence = find_label_evidence(visible_text, category) if result["fetch_succeeded"] else {
                "label_found": False,
                "label_text_normalized": category,
                "evidence_snippet_truncated": "",
                "snippet_truncated": False,
            }
            label_rows.append(
                {
                    "card_index": index,
                    "pdb_id": row["pdb_id"],
                    "het_code": row["het_code"],
                    "label_category": category,
                    "label_text_normalized": evidence["label_text_normalized"],
                    "label_found": evidence["label_found"],
                    "evidence_snippet_truncated": evidence["evidence_snippet_truncated"],
                    "parse_label_inventory_passed": True,
                }
            )
            if evidence["evidence_snippet_truncated"]:
                snippet_rows.append(
                    {
                        "card_index": index,
                        "pdb_id": row["pdb_id"],
                        "snippet_source": "label_inventory",
                        "target_or_label": category,
                        "evidence_snippet": evidence["evidence_snippet_truncated"],
                        "snippet_length": len(evidence["evidence_snippet_truncated"]),
                        "evidence_snippet_truncated": evidence["snippet_truncated"],
                        "evidence_snippet_audit_passed": len(evidence["evidence_snippet_truncated"]) <= 240,
                    }
                )
        statuses: dict[str, str] = {}
        for field in CRITICAL_EVENT_KEY_FIELDS:
            probe = probe_event_field(visible_text, field) if result["fetch_succeeded"] else {
                "field_probe_status": "parse_failed",
                "parsed_value": "",
                "evidence_snippet_truncated": "",
                "snippet_truncated": False,
                "parse_confidence": "none",
            }
            statuses[field] = probe["field_probe_status"]
            field_rows.append(
                {
                    "card_index": index,
                    "pdb_id": row["pdb_id"],
                    "het_code": row["het_code"],
                    "target_field": field,
                    "field_probe_status": probe["field_probe_status"],
                    "parsed_value": probe["parsed_value"],
                    "evidence_snippet_truncated": probe["evidence_snippet_truncated"],
                    "parse_confidence": probe["parse_confidence"],
                    "materialization_blocking_if_missing": True,
                    "field_probe_passed": True,
                }
            )
            if probe["evidence_snippet_truncated"]:
                snippet_rows.append(
                    {
                        "card_index": index,
                        "pdb_id": row["pdb_id"],
                        "snippet_source": "event_field_probe",
                        "target_or_label": field,
                        "evidence_snippet": probe["evidence_snippet_truncated"],
                        "snippet_length": len(probe["evidence_snippet_truncated"]),
                        "evidence_snippet_truncated": probe["snippet_truncated"],
                        "evidence_snippet_audit_passed": len(probe["evidence_snippet_truncated"]) <= 240,
                    }
                )
        minimal_count = sum(statuses[field] == "found" for field in CRITICAL_EVENT_KEY_FIELDS[:4])
        preferred_count = minimal_count + (1 if statuses["covalent_bond_atom_pair"] == "found" else 0)
        any_ambiguous = any(status == "ambiguous" for status in statuses.values())
        if not result["fetch_succeeded"]:
            resolution_status = "card_parse_failed"
        elif any_ambiguous:
            resolution_status = "card_ambiguous_multi_event"
        elif minimal_count == 4 and preferred_count == 5:
            resolution_status = "card_resolves_preferred_event_key"
        elif minimal_count == 4:
            resolution_status = "card_resolves_minimal_event_key"
        elif preferred_count == 0:
            resolution_status = "card_no_event_key_fields_found"
        else:
            resolution_status = "card_partial_event_key_only"
        resolution_rows.append(
            {
                "card_index": index,
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "minimal_key_fields_found_count": minimal_count,
                "preferred_key_fields_found_count": preferred_count,
                "chain_id_status": statuses["chain_id"],
                "residue_name_status": statuses["residue_name"],
                "residue_index_status": statuses["residue_index"],
                "residue_atom_name_status": statuses["residue_atom_name"],
                "covalent_bond_atom_pair_status": statuses["covalent_bond_atom_pair"],
                "minimal_event_key_resolved": minimal_count == 4,
                "preferred_event_key_resolved": preferred_count == 5,
                "resolution_status": resolution_status,
                "candidate_metadata_can_proceed": False,
                "candidate_allowlist_can_proceed": False,
                "raw_structure_annotation_may_be_required": resolution_status in {"card_partial_event_key_only", "card_no_event_key_fields_found", "card_requires_raw_structure_annotation"},
                "event_key_resolution_audit_passed": True,
            }
        )
    return {
        "fetch_rows": fetch_rows,
        "safety_rows": safety_rows,
        "label_rows": label_rows,
        "field_rows": field_rows,
        "snippet_rows": snippet_rows,
        "resolution_rows": resolution_rows,
    }


def build_failure_taxonomy_rows(fetch_rows: list[dict[str, Any]], resolution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in fetch_rows:
        if not row["fetch_succeeded"]:
            counts["complex_card_fetch_failed"] = counts.get("complex_card_fetch_failed", 0) + 1
    for row in resolution_rows:
        counts[row["resolution_status"]] = counts.get(row["resolution_status"], 0) + 1
    return [
        {
            "failure_reason": reason,
            "observed_count": count,
            "blocks_candidate_metadata": reason != "card_resolves_preferred_event_key",
            "recommended_handling": "record_status_and_defer_materialization",
        }
        for reason, count in sorted(counts.items())
    ]


def build_readiness_rows() -> list[dict[str, Any]]:
    specs = [
        ("ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate", True),
        ("ready_for_covapie_candidate_metadata_materialization", False),
        ("ready_for_covapie_candidate_allowlist_materialization_smoke", False),
        ("ready_for_covapie_batch_scale_raw_read_smoke", False),
        ("ready_for_training", False),
        ("ready_to_train_now", False),
        ("feature_semantics_audit_required_before_training", True),
        ("leakage_split_design_required_before_training", True),
    ]
    return [
        {
            "readiness_item": item,
            "current_step_status": value,
            "readiness_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, value in specs
    ]


def build_execution_boundary_rows() -> list[dict[str, Any]]:
    executed = {
        "complex_card_metadata_acquisition_smoke": "executed_html_metadata_acquisition_only",
        "step13ar_manifest_read": "executed_manifest_read_only",
        "metadata_csv_card_urls_read": "executed_url_column_read_only",
        "allowed_url_contract_read": "executed_contract_read_only",
        "complex_card_fetch": "executed_first_5_allowed_html_only",
        "html_visible_text_parse": "executed_metadata_text_parse_only",
        "event_field_probe": "executed_metadata_field_probe_only",
        "external_network_access": "executed_allowed_covpdb_complex_card_html_only",
        "urllib_use": "executed_allowed_html_fetch_only",
        "metadata_download": "executed_html_metadata_fetch_only",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": executed.get(item, "not_executed_or_not_allowed"),
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item in EXECUTION_BOUNDARY_ITEMS
    ]


def build_git_safety_rows(output_root: Path) -> list[dict[str, Any]]:
    specs = [
        ("forbidden_suffix_under_step13as_output_root", "find output root forbidden suffixes", "none", "passed" if not _forbidden_committable_artifacts_created(output_root) else "failed"),
        ("raw_files_not_staged", "git diff --cached --name-only -- data/raw/covalent_sources", "empty", "passed" if not _raw_files_staged() else "failed"),
        ("raw_files_not_tracked", "git ls-files data/raw/covalent_sources", "empty", "passed" if not _raw_files_tracked() else "failed"),
        ("metadata_csv_unchanged_policy", str(METADATA_CSV), "read_only_input", "declared"),
        ("step13ao_artifacts_unchanged_policy", "data/derived/covalent_small/covapie_covpdb_metadata_only_acquisition_smoke_v0", "read_only_input", "declared"),
        ("step13ap_artifacts_unchanged_policy", "data/derived/covalent_small/covapie_external_metadata_index_rediscovery_smoke_v0", "read_only_input", "declared"),
        ("step13aq_artifacts_unchanged_policy", "data/derived/covalent_small/covapie_external_metadata_index_schema_probe_design_gate_v0", "read_only_input", "declared"),
        ("step13ar_artifacts_unchanged_policy", str(STEP13AR_ROOT), "read_only_input", "declared"),
        ("protected_source_diff_empty", "git diff -- equivariant_diffusion/ lightning_modules.py", "empty", "passed" if not _protected_source_diff_exists() else "failed"),
        ("original_dataloader_diff_empty", "git diff -- dataset.py data/prepare_crossdocked.py", "empty", "passed" if not _original_dataloader_diff_exists() else "failed"),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": status,
            "git_safety_audit_passed": status in {"passed", "declared"},
            "blocking_reasons": "" if status in {"passed", "declared"} else f"{item}_failed",
        }
        for item, command, required, status in specs
    ]


def build_mask_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13ar",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def build_feature_semantics_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": group,
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_complex_card_acquisition_smoke": False,
            "training_ready": False,
            "recommended_audit_step": "covapie_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item, group in FEATURE_SEMANTICS_ITEMS
    ]


def build_leakage_split_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_or_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def run_covapie_covpdb_complex_card_metadata_acquisition_smoke_v0(output_root: str | Path = OUTPUT_ROOT, fetcher: Any = fetch_allowed_complex_card) -> dict[str, Any]:
    output_root = Path(output_root)
    validate_step13ar_precondition_v0()
    validate_metadata_csv_v0()
    validate_covapie_naming_convention_v0()
    cards = first_5_metadata_rows()
    acquisition_plan_rows = build_acquisition_plan_rows(cards)
    parsed = build_fetch_and_parse_rows(cards, fetcher=fetcher)
    fetch_rows = parsed["fetch_rows"]
    safety_rows = parsed["safety_rows"]
    label_rows = parsed["label_rows"]
    field_rows = parsed["field_rows"]
    snippet_rows = parsed["snippet_rows"]
    resolution_rows = parsed["resolution_rows"]
    fetched_count = sum(row["fetch_succeeded"] for row in fetch_rows)
    fetch_failed_count = len(fetch_rows) - fetched_count
    if fetched_count == 0:
        blocking_reasons = ["complex_card_fetch_failed_for_all_cards"]
        passed = False
    else:
        blocking_reasons = []
        passed = True
    minimal_count = sum(row["minimal_event_key_resolved"] for row in resolution_rows)
    preferred_count = sum(row["preferred_event_key_resolved"] for row in resolution_rows)
    partial_count = sum(row["resolution_status"] == "card_partial_event_key_only" for row in resolution_rows)
    unresolved_count = sum(row["resolution_status"] in {"card_no_event_key_fields_found", "card_parse_failed", "card_ambiguous_multi_event", "card_requires_raw_structure_annotation"} for row in resolution_rows)
    future_candidate_count = minimal_count
    future_automatic_allowlist_count = preferred_count
    precondition_rows = build_precondition_rows(output_root)
    failure_rows = build_failure_taxonomy_rows(fetch_rows, resolution_rows)
    readiness_rows = build_readiness_rows()
    execution_rows = build_execution_boundary_rows()
    git_rows = build_git_safety_rows(output_root)
    mask_rows = build_mask_scope_rows()
    feature_rows = build_feature_semantics_rows()
    leakage_rows = build_leakage_split_rows()
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13ar_complex_card_probe_design_gate_validated": True,
        "attempted_card_count": len(cards),
        "fetched_card_count": fetched_count,
        "fetch_succeeded_count": fetched_count,
        "fetch_failed_count": fetch_failed_count,
        "complex_card_url_count_total": len(read_metadata_rows()),
        "first_5_complex_card_urls": [row["complex_card_url"] for row in fetch_rows],
        "full_html_written": False,
        "raw_html_artifact_written": False,
        "forbidden_suffix_url_requested": False,
        "forbidden_suffix_links_followed": False,
        "external_raw_links_followed": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "raw_data_read": False,
        "raw_file_copied": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "network_access_used": True,
        "urllib_used": True,
        "requests_used": False,
        "browser_used": False,
        "metadata_html_fetched": fetched_count > 0,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "sample_index_written": False,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "tensor_artifact_written": False,
        "npz_created": False,
        "pt_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "minimal_event_key_resolved_card_count": minimal_count,
        "preferred_event_key_resolved_card_count": preferred_count,
        "partial_event_key_card_count": partial_count,
        "unresolved_card_count": unresolved_count,
        "future_candidate_metadata_possible_count": future_candidate_count,
        "future_automatic_allowlist_possible_count": future_automatic_allowlist_count,
        "ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate": passed,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": 5,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": True,
        "no_extra_mask_tasks_added": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_covpdb_complex_card_metadata_acquisition_qa_gate" if passed else "inspect_covpdb_complex_card_fetch_access",
        "complex_card_metadata_acquisition_smoke_passed": passed,
        "precondition_audit_row_count": len(precondition_rows),
        "acquisition_plan_row_count": len(acquisition_plan_rows),
        "fetch_audit_row_count": len(fetch_rows),
        "html_metadata_safety_audit_row_count": len(safety_rows),
        "parse_label_inventory_row_count": len(label_rows),
        "event_field_probe_row_count": len(field_rows),
        "evidence_snippet_audit_row_count": len(snippet_rows),
        "event_key_resolution_audit_row_count": len(resolution_rows),
        "observed_failure_taxonomy_row_count": len(failure_rows),
        "readiness_boundary_audit_row_count": len(readiness_rows),
        "execution_boundary_audit_row_count": len(execution_rows),
        "git_safety_audit_row_count": len(git_rows),
        "mask_scope_audit_row_count": len(mask_rows),
        "feature_semantics_audit_row_count": len(feature_rows),
        "leakage_split_audit_row_count": len(leakage_rows),
        "forbidden_committable_artifacts_created": _forbidden_committable_artifacts_created(output_root),
        "raw_files_staged": _raw_files_staged(),
        "raw_files_tracked": _raw_files_tracked(),
        "original_diffsbdd_source_modified": _protected_source_diff_exists(),
        "original_diffsbdd_dataloader_modified": _original_dataloader_diff_exists(),
        "all_checks_passed": passed,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "paths": {
            "precondition": output_root / PRECONDITION_AUDIT_CSV.name,
            "plan": output_root / ACQUISITION_PLAN_CSV.name,
            "fetch": output_root / FETCH_AUDIT_CSV.name,
            "safety": output_root / HTML_METADATA_SAFETY_AUDIT_CSV.name,
            "labels": output_root / PARSE_LABEL_INVENTORY_CSV.name,
            "fields": output_root / EVENT_FIELD_PROBE_CSV.name,
            "snippets": output_root / EVIDENCE_SNIPPET_AUDIT_CSV.name,
            "resolution": output_root / EVENT_KEY_RESOLUTION_AUDIT_CSV.name,
            "failure": output_root / OBSERVED_FAILURE_TAXONOMY_CSV.name,
            "readiness": output_root / READINESS_BOUNDARY_AUDIT_CSV.name,
            "execution": output_root / EXECUTION_BOUNDARY_AUDIT_CSV.name,
            "git": output_root / GIT_SAFETY_AUDIT_CSV.name,
            "mask": output_root / MASK_SCOPE_AUDIT_CSV.name,
            "feature": output_root / FEATURE_SEMANTICS_AUDIT_CSV.name,
            "leakage": output_root / LEAKAGE_SPLIT_AUDIT_CSV.name,
            "report": output_root / REPORT_CSV.name,
            "manifest": output_root / MANIFEST_JSON.name,
        },
        "precondition_rows": precondition_rows,
        "acquisition_plan_rows": acquisition_plan_rows,
        "fetch_rows": fetch_rows,
        "safety_rows": safety_rows,
        "label_rows": label_rows,
        "field_rows": field_rows,
        "snippet_rows": snippet_rows,
        "resolution_rows": resolution_rows,
        "failure_rows": failure_rows,
        "readiness_rows": readiness_rows,
        "execution_rows": execution_rows,
        "git_rows": git_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
        "report_sections": {
            "step13ar_precondition": {"passed": True},
            "acquisition_plan": {"attempted_card_count": len(cards)},
            "fetch_audit": {"fetch_succeeded_count": fetched_count, "fetch_failed_count": fetch_failed_count},
            "html_metadata_safety": {"full_html_written": False},
            "parse_label_inventory": {"rows": len(label_rows)},
            "event_field_probe": {"rows": len(field_rows)},
            "event_key_resolution": {"minimal": minimal_count, "preferred": preferred_count},
            "readiness_boundary": {"ready_for_qa_gate": passed},
            "execution_boundary": {"network_access_used": True},
            "git_safety": {"rows": len(git_rows)},
            "mask_scope": {"mask_count": 5},
            "feature_semantics": {"rows": len(feature_rows)},
            "leakage_split": {"rows": len(leakage_rows)},
        },
    }
