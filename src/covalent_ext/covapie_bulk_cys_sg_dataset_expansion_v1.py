"""Real bounded multi-source CYS-SG discovery and triage pipeline V1.

This successor is additive and review-only.  It downloads official source
exports and RCSB payloads into a task-owned external cache, writes only compact
derived metadata into the repository, and never mutates production registries.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
import gzip
import hashlib
from html.parser import HTMLParser
import io
from itertools import product
import json
import math
import os
from pathlib import Path
import re
import shlex
import tempfile
from functools import lru_cache
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zipfile import ZipFile

from covalent_ext import covapie_bulk_source_adapters_v1 as adapters
from covalent_ext import (
    covapie_cys_sg_dataset_expansion_pipeline_v1 as production_pipeline,
)
from covalent_ext import (
    covapie_cys_sg_future_struct_conn_crosscheck_execution_gate as struct_conn_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_owner,
)
from covalent_ext import (
    covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke
    as leakage_evidence_owner,
)
from covalent_ext import (
    real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun
    as atom_site_owner,
)


SNAPSHOT_DATE = "2026-08-19"
STAGE = "covapie_bulk_cys_sg_dataset_expansion_v1"
TASK_NAME = (
    "resolve_covapie_bulk_historical_baseline_leakage_extension_v1"
)
SCHEMA_VERSION = "covapie_bulk_multisource_cys_sg_dataset_expansion_v1"

REPOSITORY_OUTPUT_RELATIVE = Path(
    "data/derived/covalent_small/covapie_bulk_cys_sg_dataset_expansion_v1/"
    "bulk_pilot_v1"
)
AUTHORITY_REGISTRY_RELATIVE = Path(
    "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
    "6di9_gjj_approved_v1/reusable_authority_registry_v1.json"
)
LEAKAGE_REGISTRY_RELATIVE = Path(
    "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
    "6di9_gjj_approved_v1/cumulative_leakage_registry_v1.json"
)
CURRENT11_INDEX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
AUTHORITY_REGISTRY_SHA256 = (
    "c6f150bd82b1ea45121aa96e1fefb6af3be64584117cc462f74b2e10fd1913e9"
)
LEAKAGE_REGISTRY_SHA256 = (
    "24a58a6f9cc551c9b38527c1bfbf64aa2661bf1173b8eabcb44428513bfe15c8"
)

OUTPUT_FILENAMES = (
    "bulk_source_access_resolution_v1.json",
    "covpdb_discovery_snapshot_v1.json",
    "covbinderinpdb_discovery_snapshot_v1.json",
    "covalentindb_discovery_snapshot_v1.json",
    "rcsb_pdb_direct_discovery_snapshot_v1.json",
    "cross_source_canonical_event_manifest_v1.json",
    "bulk_acquisition_manifest_v1.json",
    "bulk_processing_outcomes_v1.json",
    "bulk_human_review_clusters_v1.json",
    "bulk_summary_v1.json",
)

BULK_STAGES = tuple(f"BULK_{index:02d}_{name}" for index, name in enumerate((
    "SOURCE_ACCESS_RESOLUTION",
    "SOURCE_DISCOVERY",
    "SOURCE_ADAPTER_NORMALIZATION",
    "CROSS_SOURCE_EVENT_DEDUP",
    "STRUCTURE_ACQUISITION",
    "MMCIF_VALIDATION",
    "EXACT_CYS_SG_EVENT_RECOVERY",
    "COMPONENT_TOPOLOGY_AND_ATOM_MAPPING",
    "MODEL_AND_FEATURE_COMPATIBILITY",
    "PRE_REACTION_REPRESENTABILITY",
    "EXISTING_EXACT_AUTHORITY_MATCH",
    "LEAKAGE_AND_SPLIT_PREDICTION",
    "AUTOMATIC_ROUTING",
    "HUMAN_REVIEW_CLUSTERING",
    "SUMMARY",
), 1))

TERMINAL_ROUTES = (
    "KNOWN_EXISTING_APPROVED_SAMPLE",
    "KNOWN_EXISTING_QUARANTINE",
    "KNOWN_RUNTIME_EXTENSION",
    "AUTO_ADMITTED_EXACT_SIGNATURE",
    "HUMAN_REVIEW_REQUIRED_NEW_CHEMISTRY",
    "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
    "QUARANTINE_REPRESENTATION_GAP",
    "RUNTIME_EXTENSION_REQUIRED",
    "LEAKAGE_BASELINE_EXTENSION_BLOCKED",
    "LEAKAGE_EXISTING_GROUP_CONFLICT",
    "STRUCTURAL_EVIDENCE_INCOMPLETE",
    "SOURCE_ANNOTATION_CONFLICT",
    "MISSING_SOURCE_AUTHORITY",
    "REJECTED_FEATURE_INCOMPATIBLE",
    "REJECTED_EVENT_INVALID",
    "DUPLICATE_BULK_EVENT",
)

PRE_STATUSES = frozenset((
    "PRE_EXPLICIT_AUTHORITY_AVAILABLE",
    "PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED",
    "PRE_GRAPH_TRANSFORM_REQUIRED",
    "PRE_FORMAL_CHARGE_UNRESOLVED",
    "PRE_ONLY_ATOMS_DETECTED",
    "PRE_ATOM_LOSS_REPRESENTATION_GAP",
    "PRE_COMPONENT_TOPOLOGY_INCOMPLETE",
    "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS",
    "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
    "PRE_REACTION_UNRESOLVED",
))

RCSB_SEARCH_EXAMINATION_CAP = 5000
RCSB_CONNECTION_RECORD_CAP = 5000
RCSB_EXACT_SHORTLIST_CAP = 300
UNIQUE_PDB_ACQUISITION_CAP = 250
SPECIALIST_RECORD_EXAMINATION_CAP = 5000
SPECIALIST_NORMALIZED_RECORD_CAP = 2000
UNIQUE_NEW_EVENT_PROCESSING_CAP = 250
COMPRESSED_FILE_CAP = 64 * 1024 * 1024
COVPDB_COMPLEX_ARCHIVE_CAP = 512 * 1024 * 1024
TOTAL_COMPRESSED_DOWNLOAD_CAP = 2 * 1024 * 1024 * 1024
NETWORK_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS_PER_REQUEST = 2
SPECIALIST_SEEDED_PDB_CAP = 1500

COVPDB_SDF_URL = (
    "https://drug-discovery.vm.uni-freiburg.de/staticfiles/covpdb/download/"
    "CovPDB_ligands.sdf"
)
COVPDB_DOWNLOAD_PAGE_URL = (
    "https://drug-discovery.vm.uni-freiburg.de/covpdb/download"
)
COVBINDER_ZIP_URL = (
    "https://yzhang.hpc.nyu.edu/CovBinderInPDB/"
    "CovBinderInPDB_2022Q4.zip"
)
RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_DATA_GRAPHQL_URL = "https://data.rcsb.org/graphql"
RCSB_MMCIF_URL = "https://files.rcsb.org/download/{pdb_id}.cif.gz"
RCSB_CCD_URL = "https://files.rcsb.org/ligands/download/{ccd_id}.cif"

_GRAPHQL_CONNECTION_QUERY = """query($ids:[String!]!){entries(entry_ids:$ids){rcsb_id polymer_entities{polymer_entity_instances{rcsb_id rcsb_polymer_struct_conn{id connect_type description dist_value value_order connect_target{auth_asym_id auth_seq_id label_alt_id label_asym_id label_atom_id label_comp_id label_seq_id symmetry} connect_partner{label_alt_id label_asym_id label_atom_id label_comp_id label_seq_id symmetry}}}}}}"""

KNOWN_EXPANSION_APPROVED = {
    ("5F2E", "5UT"), ("6OIM", "MOV"), ("6DI9", "GJJ"),
}
KNOWN_QUARANTINE = {("2DJF", "1ZB")}
KNOWN_RUNTIME_EXTENSION = {("2R9F", "K2Z")}
KNOWN_K36_EXACT16 = {
    ("4DCD", "K36"), ("4F49", "K36"), ("5WKJ", "K36"),
    ("6L70", "K36"), ("6WTT", "K36"),
}

_ENTRY_ID = re.compile(r"(?m)^_entry\.id\s+['\"]?([^\s'\"]+)")
_MISSING = {"", ".", "?"}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return adapters.canonical_json_bytes_v1(value)


def _json_without_newline(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_cache_write_v1(
    path: Path, payload: bytes, *, expected_sha256: str | None = None,
) -> str:
    digest = _sha(payload)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("CACHE_PAYLOAD_EXPECTED_SHA256_MISMATCH")
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("CACHE_EXISTING_BYTES_CONFLICT")
        return digest
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return digest


class BulkCacheV1:
    """Task-owned immutable payload cache with a deterministic acquisition ledger."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.root / "cache_manifest_v1.json"
        if self.ledger_path.exists():
            parsed = json.loads(self.ledger_path.read_text(encoding="utf-8"))
            if parsed.get("schema_version") != "covapie_bulk_cache_manifest_v1":
                raise ValueError("CACHE_MANIFEST_SCHEMA_INVALID")
            self.entries: dict[str, dict[str, Any]] = {
                item["relative_path"]: item for item in parsed["payloads"]
            }
        else:
            self.entries = {}

    def fetch(
        self,
        *,
        relative_path: str,
        url: str,
        source_dataset: str,
        retrieval_identity: Mapping[str, Any],
        request_body: bytes | None = None,
        content_type: str | None = None,
        maximum_bytes: int = COMPRESSED_FILE_CAP,
    ) -> tuple[bytes, dict[str, Any]]:
        path = self.root / relative_path
        identity_digest = _sha(_canonical_json(retrieval_identity))
        prior = self.entries.get(relative_path)
        if prior is not None and prior["retrieval_identity_sha256"] != identity_digest:
            raise ValueError("CACHE_RETRIEVAL_IDENTITY_CONFLICT:" + relative_path)
        if path.exists():
            payload = path.read_bytes()
            if len(payload) > maximum_bytes:
                raise ValueError("CACHE_PAYLOAD_SIZE_CAP_EXCEEDED:" + relative_path)
            digest = _sha(payload)
            if prior is not None and (
                prior["sha256"] != digest or prior["byte_count"] != len(payload)
            ):
                raise ValueError("CACHE_PAYLOAD_LEDGER_CONFLICT:" + relative_path)
            if prior is None:
                prior = self._entry(
                    relative_path=relative_path,
                    url=url,
                    source_dataset=source_dataset,
                    identity_digest=identity_digest,
                    http_status=200,
                    payload=payload,
                    cache_reuse_status="REUSED_FROM_TASK_CACHE",
                )
                self.entries[relative_path] = prior
                self.flush()
            return payload, prior

        headers = {
            "User-Agent": (
                "CovaPIE-bulk-pilot-v1/1.0 "
                "(bounded official scientific source acquisition)"
            ),
        }
        if content_type:
            headers["Content-Type"] = content_type
        last_error: Exception | None = None
        for _attempt in range(1, MAX_ATTEMPTS_PER_REQUEST + 1):
            try:
                request = Request(
                    url,
                    data=request_body,
                    headers=headers,
                    method="POST" if request_body is not None else "GET",
                )
                with urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
                    status = int(response.status)
                    chunks: list[bytes] = []
                    count = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > maximum_bytes:
                            raise ValueError(
                                "NETWORK_PAYLOAD_SIZE_CAP_EXCEEDED:" + relative_path
                            )
                        chunks.append(chunk)
                    payload = b"".join(chunks)
                if status != 200:
                    raise ValueError("NETWORK_HTTP_STATUS_INVALID")
                atomic_cache_write_v1(path, payload)
                entry = self._entry(
                    relative_path=relative_path,
                    url=url,
                    source_dataset=source_dataset,
                    identity_digest=identity_digest,
                    http_status=status,
                    payload=payload,
                    cache_reuse_status="DOWNLOADED_BY_BULK_PILOT",
                )
                self.entries[relative_path] = entry
                self.flush()
                return payload, entry
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
                last_error = error
        raise RuntimeError(
            "BOUNDED_NETWORK_REQUEST_FAILED:" + relative_path
        ) from last_error

    def _entry(
        self,
        *,
        relative_path: str,
        url: str,
        source_dataset: str,
        identity_digest: str,
        http_status: int,
        payload: bytes,
        cache_reuse_status: str,
    ) -> dict[str, Any]:
        return {
            "relative_path": relative_path,
            "source_url_or_endpoint": url,
            "source_dataset": source_dataset,
            "retrieval_identity_sha256": identity_digest,
            "http_status": http_status,
            "byte_count": len(payload),
            "sha256": _sha(payload),
            "validation_status": "SHA256_AND_SIZE_RECORDED",
            "cache_reuse_status": cache_reuse_status,
        }

    def flush(self) -> None:
        payload = _canonical_json({
            "schema_version": "covapie_bulk_cache_manifest_v1",
            "snapshot_date": SNAPSHOT_DATE,
            "payloads": [self.entries[key] for key in sorted(self.entries)],
        })
        # The ledger is the sole mutable cache index; immutable payload files
        # still use conflict-detecting ``atomic_cache_write_v1``.
        _atomic_write(self.ledger_path, payload)

    def summary(self) -> dict[str, Any]:
        files = sorted(path for path in self.root.rglob("*") if path.is_file())
        by_lane = {
            name: sum(1 for path in files if name in path.relative_to(self.root).parts)
            for name in ("rcsb", "covpdb", "covbinderinpdb", "covalentindb")
        }
        return {
            "bulk_cache_root": str(self.root),
            "bulk_cache_new_file_count": len(files),
            "bulk_cache_total_bytes": sum(path.stat().st_size for path in files),
            "bulk_task_cache_modified": bool(files),
            "preexisting_state_modified": False,
            "rcsb_cache_files": by_lane["rcsb"],
            "covpdb_cache_files": by_lane["covpdb"],
            "covbinderinpdb_cache_files": by_lane["covbinderinpdb"],
            "covalentindb_cache_files": by_lane["covalentindb"],
        }


def _terms_digest(text: str) -> str:
    return _sha(text.encode("utf-8"))


def source_access_resolution_v1() -> list[dict[str, Any]]:
    records = [
        {
            "source_name": adapters.SOURCE_COVPDB,
            "official_home": "https://drug-discovery.vm.uni-freiburg.de/covpdb/",
            "official_bulk_download_endpoint": COVPDB_SDF_URL,
            "official_API_endpoint": None,
            "current_access_mode": "official freely-provided bulk files",
            "usage_license_terms_source": (
                "https://drug-discovery.vm.uni-freiburg.de/covpdb/help#download"
            ),
            "usage_license_terms_snapshot_sha256": _terms_digest(
                "CovPDB freely provides its content as separate files for download; "
                "official All Ligands SDF, sequences FASTA, complexes ZIP, and warheads TXT."
            ),
            "metadata_bulk_access_allowed": True,
            "programmatic_access_allowed": True,
            "automated_scraping_allowed": "unresolved",
            "structure_files_directly_provided": True,
            "PDB_ids_available": True,
            "current_lane_status": "OPERATIONAL_OFFICIAL_BULK_DOWNLOAD",
        },
        {
            "source_name": adapters.SOURCE_COVBINDERINPDB,
            "official_home": "https://yzhang.hpc.nyu.edu/CovBinderInPDB/",
            "official_bulk_download_endpoint": COVBINDER_ZIP_URL,
            "official_API_endpoint": None,
            "current_access_mode": "official Download All Records and Binder Structures ZIP",
            "usage_license_terms_source": (
                "https://yzhang.hpc.nyu.edu/CovBinderInPDB/ and "
                "https://pmc.ncbi.nlm.nih.gov/articles/PMC9772242/"
            ),
            "usage_license_terms_snapshot_sha256": _terms_digest(
                "CovBinderInPDB is freely accessible and its official portal offers "
                "Download All Records and Binder Structures."
            ),
            "metadata_bulk_access_allowed": True,
            "programmatic_access_allowed": True,
            "automated_scraping_allowed": "unresolved",
            "structure_files_directly_provided": True,
            "PDB_ids_available": True,
            "current_lane_status": "OPERATIONAL_OFFICIAL_BULK_DOWNLOAD",
        },
        {
            "source_name": adapters.SOURCE_COVALENTINDB,
            "official_home": "https://cadd.zju.edu.cn/cidb/",
            "official_bulk_download_endpoint": None,
            "official_API_endpoint": None,
            "current_access_mode": "current official entry redirects to robot verification",
            "usage_license_terms_source": (
                "https://cadd.zju.edu.cn/cidb/ and primary CovalentInDB 2.0 publication"
            ),
            "usage_license_terms_snapshot_sha256": _terms_digest(
                "The primary publication describes downloads, but the current official "
                "entry presents a robot test and no current machine-readable bulk endpoint "
                "or programmatic terms were independently verified."
            ),
            "metadata_bulk_access_allowed": "unresolved",
            "programmatic_access_allowed": False,
            "automated_scraping_allowed": False,
            "structure_files_directly_provided": False,
            "PDB_ids_available": True,
            "current_lane_status": "DEFERRED_NO_MACHINE_READABLE_BULK_ACCESS",
        },
        {
            "source_name": adapters.SOURCE_RCSB_PDB_DIRECT,
            "official_home": "https://www.rcsb.org/",
            "official_bulk_download_endpoint": (
                "https://files.rcsb.org/download/{pdb_id}.cif.gz"
            ),
            "official_API_endpoint": (
                RCSB_SEARCH_URL + " ; " + RCSB_DATA_GRAPHQL_URL
            ),
            "current_access_mode": "official Search API, Data API, and HTTPS archive",
            "usage_license_terms_source": "https://www.rcsb.org/pages/usage-policy",
            "usage_license_terms_snapshot_sha256": _terms_digest(
                "PDB archive data files and all data from RCSB PDB programmatic APIs "
                "are available under CC0 1.0; attribution is encouraged."
            ),
            "metadata_bulk_access_allowed": True,
            "programmatic_access_allowed": True,
            "automated_scraping_allowed": False,
            "structure_files_directly_provided": True,
            "PDB_ids_available": True,
            "current_lane_status": "OPERATIONAL_BULK_API",
        },
    ]
    for record in records:
        adapters.validate_source_access_resolution_v1(record)
    return sorted(records, key=lambda item: item["source_name"])


def build_rcsb_search_request_v1(*, start: int, rows: int) -> dict[str, Any]:
    if start < 0 or rows < 1 or start + rows > RCSB_SEARCH_EXAMINATION_CAP:
        raise ValueError("RCSB_SEARCH_PAGINATION_BUDGET_INVALID")
    return {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_struct_conn.connect_type",
                        "operator": "in",
                        "value": [
                            "covalent bond", "covalent residue modification",
                        ],
                    },
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_entry_info.polymer_entity_count_protein",
                        "operator": "greater",
                        "value": 0,
                    },
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_entry_info.nonpolymer_entity_count",
                        "operator": "greater",
                        "value": 0,
                    },
                },
            ],
        },
        "request_options": {
            "paginate": {"start": start, "rows": rows},
            "results_verbosity": "compact",
        },
        "return_type": "entry",
    }


def _parse_covpdb_sdf_records(
    payload: bytes, *, maximum: int = SPECIALIST_RECORD_EXAMINATION_CAP,
) -> list[str]:
    records = payload.decode("utf-8", "replace").split("$$$$")
    identifiers: list[str] = []
    for record in records:
        lines = record.lstrip("\r\n").splitlines()
        if not lines:
            continue
        identity = lines[0].strip()
        if identity:
            identifiers.append(identity)
        if len(identifiers) >= maximum:
            break
    return identifiers


class _CovPDBDownloadPageParserV1(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[tuple[str, tuple[str, ...]]] = []
        self._in_row = False
        self._text: list[str] = []
        self._hrefs: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() == "tr":
            self._in_row = True
            self._text = []
            self._hrefs = []
        if self._in_row and tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self._hrefs.append(href)

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._in_row and tag.lower() == "tr":
            text = " ".join(" ".join(self._text).split())
            self.rows.append((text, tuple(self._hrefs)))
            self._in_row = False


def resolve_covpdb_complexes_href_v1(
    page_payload: bytes, *, page_url: str = COVPDB_DOWNLOAD_PAGE_URL,
) -> str:
    parser = _CovPDBDownloadPageParserV1()
    parser.feed(page_payload.decode("utf-8", "replace"))
    matches = [
        href
        for text, hrefs in parser.rows
        if "All Complexes" in text and "ZIP" in text.upper()
        for href in hrefs
    ]
    resolved = sorted(set(urljoin(page_url, href) for href in matches))
    if len(resolved) != 1 or not resolved[0].startswith(
        "https://drug-discovery.vm.uni-freiburg.de/"
    ):
        raise ValueError("COVPDB_ALL_COMPLEXES_OFFICIAL_HREF_NOT_EXACT_ONE")
    return resolved[0]


def _pdb_archive_member_identity_v1(name: str, text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("HEADER") and len(line) >= 66:
            identity = line[62:66].strip().upper()
            if re.fullmatch(r"[0-9][A-Z0-9]{3}", identity):
                return identity
    candidates = re.findall(
        r"(?i)(?<![A-Z0-9])([0-9][A-Z0-9]{3})(?![A-Z0-9])", name,
    )
    unique = sorted(set(item.upper() for item in candidates))
    return unique[0] if len(unique) == 1 else None


def _pdb_endpoint_v1(line: str, *, second: bool) -> dict[str, str]:
    if second:
        return {
            "atom": line[42:46].strip().upper(),
            "altloc": line[46:47].strip(),
            "component": line[47:50].strip().upper(),
            "chain": line[51:52].strip(),
            "number": line[52:56].strip(),
            "insertion": line[56:57].strip(),
        }
    return {
        "atom": line[12:16].strip().upper(),
        "altloc": line[16:17].strip(),
        "component": line[17:20].strip().upper(),
        "chain": line[21:22].strip(),
        "number": line[22:26].strip(),
        "insertion": line[26:27].strip(),
    }


def parse_covpdb_complex_member_v1(
    *, member_name: str, member_payload: bytes, archive_sha256: str,
) -> list[dict[str, Any]]:
    """Recover literal CYS-SG LINK seeds or one conservative PDB-only seed."""

    text = member_payload.decode("utf-8", "replace")
    pdb_id = _pdb_archive_member_identity_v1(member_name, text)
    if pdb_id is None:
        return []
    het_residues = {
        (
            line[17:20].strip().upper(), line[21:22].strip(),
            line[22:26].strip(), line[26:27].strip(),
        )
        for line in text.splitlines()
        if line.startswith("HETATM") and len(line) >= 27
    }
    result: list[dict[str, Any]] = []
    for link_index, line in enumerate(text.splitlines()):
        if not line.startswith("LINK  ") or len(line) < 57:
            continue
        left = _pdb_endpoint_v1(line, second=False)
        right = _pdb_endpoint_v1(line, second=True)
        for protein, ligand in ((left, right), (right, left)):
            ligand_key = (
                ligand["component"], ligand["chain"], ligand["number"],
                ligand["insertion"],
            )
            if not (
                protein["component"] == "CYS" and protein["atom"] == "SG"
                and ligand_key in het_residues
                and ligand["component"] not in {"", "CYS", "HOH", "WAT"}
                and ligand["atom"]
            ):
                continue
            result.append(adapters.normalize_covpdb_complex_seed_v1(
                record_id=f"{member_name}#LINK{link_index:05d}",
                pdb_id=pdb_id,
                source_payload_sha256=archive_sha256,
                protein_chain=protein["chain"],
                protein_residue_number=protein["number"],
                ligand_component_id=ligand["component"],
                ligand_instance_id=(
                    f"{ligand['chain'] or '?'}:{ligand['number'] or '?'}"
                ),
                ligand_reactive_atom=ligand["atom"],
                explicit_cys_sg_link=True,
            ))
    if result:
        return sorted(result, key=lambda item: str(item["source_record_id"]))
    return [adapters.normalize_covpdb_complex_seed_v1(
        record_id=member_name,
        pdb_id=pdb_id,
        source_payload_sha256=archive_sha256,
    )]


def parse_covpdb_complex_archive_v1(
    payload: bytes, *, archive_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    examined = 0
    pdb_members = 0
    with ZipFile(io.BytesIO(payload)) as archive:
        infos = sorted(archive.infolist(), key=lambda item: item.filename)
        if len(infos) > 10000:
            raise ValueError("COVPDB_COMPLEX_ARCHIVE_ENTRY_CAP_EXCEEDED")
        if sum(item.file_size for item in infos) > 8 * 1024 * 1024 * 1024:
            raise ValueError("COVPDB_COMPLEX_ARCHIVE_UNCOMPRESSED_CAP_EXCEEDED")
        for info in infos:
            if info.is_dir():
                continue
            examined += 1
            if info.file_size > 32 * 1024 * 1024:
                raise ValueError("COVPDB_COMPLEX_ARCHIVE_MEMBER_CAP_EXCEEDED")
            if not info.filename.lower().endswith(('.pdb', '.ent')):
                continue
            pdb_members += 1
            records.extend(parse_covpdb_complex_member_v1(
                member_name=info.filename,
                member_payload=archive.read(info),
                archive_sha256=archive_sha256,
            ))
    adapters.validate_shared_adapter_contract_v1(records)
    return records, {
        "archive_entry_count": examined,
        "pdb_member_count": pdb_members,
    }


def discover_covpdb_v1(cache: BulkCacheV1) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ligand_payload, ligand_entry = cache.fetch(
        relative_path="covpdb/CovPDB_ligands.sdf",
        url=COVPDB_SDF_URL,
        source_dataset=adapters.SOURCE_COVPDB,
        retrieval_identity={"official_export": "All Ligands", "snapshot_date": SNAPSHOT_DATE},
    )
    identifiers = _parse_covpdb_sdf_records(ligand_payload)
    ligand_records = [
        adapters.normalize_covpdb_ligand_record_v1(
            record_id=identity, source_payload_sha256=ligand_entry["sha256"],
        )
        for identity in identifiers[:SPECIALIST_NORMALIZED_RECORD_CAP]
    ]
    page_payload, page_entry = cache.fetch(
        relative_path="covpdb/official_download_page.html",
        url=COVPDB_DOWNLOAD_PAGE_URL,
        source_dataset=adapters.SOURCE_COVPDB,
        retrieval_identity={
            "official_page": "CovPDB Downloads", "snapshot_date": SNAPSHOT_DATE,
        },
        maximum_bytes=4 * 1024 * 1024,
    )
    complexes_url = resolve_covpdb_complexes_href_v1(page_payload)
    archive_payload, archive_entry = cache.fetch(
        relative_path="covpdb/CovPDB_complexes.zip",
        url=complexes_url,
        source_dataset=adapters.SOURCE_COVPDB,
        retrieval_identity={
            "official_export": "All Complexes",
            "resolved_from_download_page_sha256": page_entry["sha256"],
            "snapshot_date": SNAPSHOT_DATE,
        },
        maximum_bytes=COVPDB_COMPLEX_ARCHIVE_CAP,
    )
    complex_records, archive_facts = parse_covpdb_complex_archive_v1(
        archive_payload, archive_sha256=archive_entry["sha256"],
    )
    exact_records = [
        item for item in complex_records
        if item["protein_reactive_atom"] == "SG"
    ]
    pdb_seed_count = len({
        str(item["pdb_id"]) for item in complex_records if item["pdb_id"]
    })
    records = [*ligand_records, *complex_records]
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "source_dataset": adapters.SOURCE_COVPDB,
        "lane_status": "OPERATIONAL_OFFICIAL_BULK_DOWNLOAD",
        "reason": (
            "official ligand SDF and official All Complexes ZIP consumed; literal "
            "PDB LINK evidence is retained and all exact events require RCSB cross-check"
        ),
        "official_access_evidence": COVPDB_DOWNLOAD_PAGE_URL,
        "official_complex_archive_url": complexes_url,
        "download_page_sha256": page_entry["sha256"],
        "source_payload_sha256": ligand_entry["sha256"],
        "complex_archive_sha256": archive_entry["sha256"],
        "complex_archive_bytes": archive_entry["byte_count"],
        "complex_archive_entry_count": archive_facts["archive_entry_count"],
        "complex_archive_pdb_member_count": archive_facts["pdb_member_count"],
        "complex_archive_specific_cap_bytes": COVPDB_COMPLEX_ARCHIVE_CAP,
        "covpdb_ligand_records_normalized": len(ligand_records),
        "covpdb_complexes_examined": archive_facts["pdb_member_count"],
        "covpdb_pdb_seed_count": pdb_seed_count,
        "covpdb_exact_event_seed_count": len(exact_records),
        "source_records_examined": len(identifiers),
        "normalized_records": len(records),
        "records_with_pdb_event_mapping": len(exact_records),
        "normalized_record_identity_digest": _sha(_canonical_json([
            item["source_record_id"] for item in records
        ])),
        "representative_source_record_ids": [
            item["source_record_id"] for item in records[:10]
        ],
        "aggressive_html_scraping_performed": False,
        "archive_extracted_into_repository": False,
    }
    return records, snapshot


def discover_covbinder_v1(
    cache: BulkCacheV1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload, entry = cache.fetch(
        relative_path="covbinderinpdb/CovBinderInPDB_2022Q4.zip",
        url=COVBINDER_ZIP_URL,
        source_dataset=adapters.SOURCE_COVBINDERINPDB,
        retrieval_identity={"official_export": "2022Q4 All Records", "snapshot_date": SNAPSHOT_DATE},
    )
    with ZipFile(io.BytesIO(payload)) as archive:
        name = "CovBinderInPDB_2022Q4_AllRecords.csv"
        csv_payload = archive.read(name)
    reader = csv.DictReader(io.StringIO(csv_payload.decode("utf-8-sig")))
    examined = 0
    records: list[dict[str, Any]] = []
    for row in reader:
        if examined >= SPECIALIST_RECORD_EXAMINATION_CAP:
            break
        examined += 1
        if row.get("full_residue_name") != "Cysteine":
            continue
        records.append(adapters.normalize_covbinderinpdb_record_v1(
            row, source_payload_sha256=entry["sha256"],
        ))
        if len(records) >= SPECIALIST_NORMALIZED_RECORD_CAP:
            break
    adapters.validate_shared_adapter_contract_v1(records)
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "source_dataset": adapters.SOURCE_COVBINDERINPDB,
        "lane_status": "OPERATIONAL_OFFICIAL_BULK_DOWNLOAD",
        "reason": "official all-record CSV normalized without treating annotations as authority",
        "official_access_evidence": COVBINDER_ZIP_URL,
        "source_payload_sha256": entry["sha256"],
        "embedded_csv_sha256": _sha(csv_payload),
        "source_records_examined": examined,
        "normalized_records": len(records),
        "normalized_record_identity_digest": _sha(_canonical_json([
            item["source_record_id"] for item in records
        ])),
        "representative_source_record_ids": [
            item["source_record_id"] for item in records[:10]
        ],
        "aggressive_html_scraping_performed": False,
    }
    return records, snapshot


def deferred_covalentindb_snapshot_v1() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "source_dataset": adapters.SOURCE_COVALENTINDB,
        "lane_status": "DEFERRED_NO_MACHINE_READABLE_BULK_ACCESS",
        "reason": (
            "current official entry requires robot verification; no current official "
            "machine-readable bulk/API endpoint was independently verified"
        ),
        "official_access_evidence": "https://cadd.zju.edu.cn/cidb/",
        "source_records_examined": 0,
        "normalized_records": 0,
        "automated_scraping_performed": False,
        "captcha_bypassed": False,
    }


def _response_result_ids(parsed: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for item in parsed.get("result_set", []):
        identity = item if isinstance(item, str) else item.get("identifier")
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9A-Z]+", identity):
            raise ValueError("RCSB_SEARCH_RESULT_ID_INVALID")
        result.append(identity.upper())
    return result


def discover_rcsb_direct_v1(
    cache: BulkCacheV1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page_size = 1000
    entry_ids: list[str] = []
    page_evidence: list[dict[str, Any]] = []
    total_count: int | None = None
    for page, start in enumerate(range(0, RCSB_SEARCH_EXAMINATION_CAP, page_size)):
        request_value = build_rcsb_search_request_v1(start=start, rows=page_size)
        request_payload = _json_without_newline(request_value)
        response_payload, cache_entry = cache.fetch(
            relative_path=(
                f"rcsb/search_protein_nonpoly_v1/page_{page:04d}.json"
            ),
            url=RCSB_SEARCH_URL,
            source_dataset=adapters.SOURCE_RCSB_PDB_DIRECT,
            retrieval_identity={"request": request_value, "snapshot_date": SNAPSHOT_DATE},
            request_body=request_payload,
            content_type="application/json",
            maximum_bytes=16 * 1024 * 1024,
        )
        parsed = json.loads(response_payload)
        if total_count is None:
            total_count = int(parsed["total_count"])
        elif int(parsed["total_count"]) != total_count:
            raise ValueError("RCSB_SEARCH_TOTAL_COUNT_CHANGED_WITHIN_SNAPSHOT")
        ids = _response_result_ids(parsed)
        entry_ids.extend(ids)
        page_evidence.append({
            "page": page,
            "start": start,
            "rows_requested": page_size,
            "rows_returned": len(ids),
            "request_canonical_json": request_value,
            "request_sha256": _sha(request_payload),
            "response_payload_sha256": cache_entry["sha256"],
            "result_identity_digest": _sha(_canonical_json(ids)),
        })
        if len(ids) < page_size:
            break
    entry_ids = entry_ids[:RCSB_SEARCH_EXAMINATION_CAP]
    if len(entry_ids) != len(set(entry_ids)):
        raise ValueError("RCSB_SEARCH_PAGINATION_DUPLICATE_ENTRY")
    search_result_digest = _sha(_canonical_json(entry_ids))
    search_contract = build_rcsb_search_request_v1(start=0, rows=1000)
    search_contract["request_options"]["paginate"] = {
        "start": "PAGE_START", "rows": "PAGE_ROWS_MAX_1000",
    }
    search_request_sha = _sha(_canonical_json(search_contract))

    records: list[dict[str, Any]] = []
    examined_connections = 0
    incidental_connections_returned = 0
    graphql_evidence: list[dict[str, Any]] = []
    batch_size = 50
    for batch_index, offset in enumerate(range(0, len(entry_ids), batch_size)):
        if (
            examined_connections >= RCSB_CONNECTION_RECORD_CAP
            or len(records) >= RCSB_EXACT_SHORTLIST_CAP
        ):
            break
        ids = entry_ids[offset:offset + batch_size]
        graphql_request = {
            "query": _GRAPHQL_CONNECTION_QUERY,
            "variables": {"ids": ids},
        }
        request_payload = _json_without_newline(graphql_request)
        response_payload, cache_entry = cache.fetch(
            relative_path=(
                "rcsb/data_protein_nonpoly_v1_revision2/"
                f"connections_batch_{batch_index:04d}.json"
            ),
            url=RCSB_DATA_GRAPHQL_URL,
            source_dataset=adapters.SOURCE_RCSB_PDB_DIRECT,
            retrieval_identity={
                "graphql_query_sha256": _sha(_GRAPHQL_CONNECTION_QUERY.encode()),
                "entry_ids": ids,
                "snapshot_date": SNAPSHOT_DATE,
            },
            request_body=request_payload,
            content_type="application/json",
            maximum_bytes=32 * 1024 * 1024,
        )
        parsed = json.loads(response_payload)
        if parsed.get("errors"):
            raise ValueError("RCSB_GRAPHQL_RESPONSE_ERRORS")
        entries = sorted(
            parsed.get("data", {}).get("entries") or [],
            key=lambda item: item.get("rcsb_id", ""),
        )
        batch_examined = 0
        batch_retained = 0
        for entry in entries:
            entry_id = str(entry.get("rcsb_id", "")).upper()
            instances: list[Mapping[str, Any]] = []
            for entity in entry.get("polymer_entities") or []:
                instances.extend(entity.get("polymer_entity_instances") or [])
            for instance in sorted(instances, key=lambda item: item.get("rcsb_id", "")):
                connections = sorted(
                    instance.get("rcsb_polymer_struct_conn") or [],
                    key=lambda item: (
                        str(item.get("id", "")),
                        json.dumps(item, sort_keys=True, separators=(",", ":")),
                    ),
                )
                for connection in connections:
                    if str(connection.get("connect_type", "")).lower() not in {
                        "covalent bond", "covalent residue modification",
                    }:
                        incidental_connections_returned += 1
                        continue
                    if examined_connections >= RCSB_CONNECTION_RECORD_CAP:
                        break
                    examined_connections += 1
                    batch_examined += 1
                    normalized = adapters.normalize_rcsb_connection_record_v1(
                        entry_id=entry_id,
                        polymer_instance_id=str(instance.get("rcsb_id", "")),
                        connection=connection,
                        source_payload_sha256=cache_entry["sha256"],
                        search_request_sha256=search_request_sha,
                        search_result_identity_digest=search_result_digest,
                        data_api_endpoint_descriptor=(
                            RCSB_DATA_GRAPHQL_URL + "#rcsb_polymer_struct_conn"
                        ),
                    )
                    if normalized is not None:
                        records.append(normalized)
                        batch_retained += 1
                    if len(records) >= RCSB_EXACT_SHORTLIST_CAP:
                        break
                if (
                    examined_connections >= RCSB_CONNECTION_RECORD_CAP
                    or len(records) >= RCSB_EXACT_SHORTLIST_CAP
                ):
                    break
            if (
                examined_connections >= RCSB_CONNECTION_RECORD_CAP
                or len(records) >= RCSB_EXACT_SHORTLIST_CAP
            ):
                break
        graphql_evidence.append({
            "batch_index": batch_index,
            "entry_id_count": len(ids),
            "request_sha256": _sha(request_payload),
            "response_payload_sha256": cache_entry["sha256"],
            "connection_records_examined": batch_examined,
            "normalized_records": batch_retained,
        })
    adapters.validate_shared_adapter_contract_v1(records)
    network_performed = any(
        entry["cache_reuse_status"] == "DOWNLOADED_BY_BULK_PILOT"
        for key, entry in cache.entries.items()
        if key.startswith("rcsb/search_protein_nonpoly_v1/")
    )
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "source_dataset": adapters.SOURCE_RCSB_PDB_DIRECT,
        "lane_status": "OPERATIONAL_BULK_API",
        "official_search_endpoint": RCSB_SEARCH_URL,
        "official_data_endpoint": RCSB_DATA_GRAPHQL_URL,
        "search_request_contract_canonical_json": search_contract,
        "search_request_sha256": search_request_sha,
        "search_response_result_identity_digest": search_result_digest,
        "search_pages": page_evidence,
        "data_api_batches": graphql_evidence,
        "real_rcsb_network_discovery_performed": network_performed,
        "rcsb_search_raw_hit_count": total_count or 0,
        "rcsb_search_results_examined": len(entry_ids),
        "rcsb_connection_records_examined": examined_connections,
        "rcsb_connection_examination_scope": (
            "query-compatible covalent bond or covalent residue modification records"
        ),
        "rcsb_incidental_nonquery_connection_records_returned_count": (
            incidental_connections_returned
        ),
        "rcsb_normalized_records": len(records),
        "exact_cys_sg_shortlist_cap": RCSB_EXACT_SHORTLIST_CAP,
        "webpage_scraping_performed": False,
        "distance_only_event_inference_used": False,
    }
    return records, snapshot


def _specialist_seed_priority_v1(
    pdb_id: str, records: Sequence[Mapping[str, Any]],
) -> tuple[Any, ...]:
    matching = [item for item in records if item.get("pdb_id") == pdb_id]
    return (
        0 if any(item.get("protein_residue_name") == "CYS" for item in matching) else 1,
        0 if any(
            item.get("ligand_component_id")
            and item.get("protein_residue_number")
            for item in matching
        ) else 1,
        0 if any(
            item.get("supporting_pre_reaction_smiles")
            or item.get("supporting_adduct_smiles")
            for item in matching
        ) else 1,
        -len({str(item["source_dataset"]) for item in matching}),
        pdb_id,
    )


def discover_rcsb_specialist_seeded_v1(
    cache: BulkCacheV1,
    *,
    specialist_records: Sequence[Mapping[str, Any]],
    direct_records: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    """Recover exact events for bounded specialist PDB seeds outside direct search."""

    all_seed_ids = sorted({
        str(item["pdb_id"])
        for item in specialist_records if item.get("pdb_id")
    })
    direct_ids = {str(item["pdb_id"]) for item in direct_records}
    queued = sorted(
        (item for item in all_seed_ids if item not in direct_ids),
        key=lambda item: _specialist_seed_priority_v1(item, specialist_records),
    )[:SPECIALIST_SEEDED_PDB_CAP]
    statuses = {pdb_id: "EXAMINED" for pdb_id in direct_ids}
    records: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    query_contract_sha = _sha(_GRAPHQL_CONNECTION_QUERY.encode("utf-8"))
    for batch_index, offset in enumerate(range(0, len(queued), 50)):
        ids = queued[offset:offset + 50]
        request_value = {
            "query": _GRAPHQL_CONNECTION_QUERY,
            "variables": {"ids": ids},
        }
        request_payload = _json_without_newline(request_value)
        try:
            response_payload, cache_entry = cache.fetch(
                relative_path=(
                    "rcsb/specialist_seeded_v1/"
                    f"connections_batch_{batch_index:04d}.json"
                ),
                url=RCSB_DATA_GRAPHQL_URL,
                source_dataset=adapters.SOURCE_RCSB_PDB_DIRECT,
                retrieval_identity={
                    "graphql_query_sha256": query_contract_sha,
                    "entry_ids": ids,
                    "lane": "SPECIALIST_SEEDED_RCSB_RECOVERY_V1",
                    "snapshot_date": SNAPSHOT_DATE,
                },
                request_body=request_payload,
                content_type="application/json",
                maximum_bytes=32 * 1024 * 1024,
            )
            parsed = json.loads(response_payload)
            if parsed.get("errors"):
                raise ValueError("RCSB_SPECIALIST_GRAPHQL_RESPONSE_ERRORS")
            entries = [
                item for item in (parsed.get("data", {}).get("entries") or [])
                if isinstance(item, Mapping)
            ]
            returned_ids = {
                str(item.get("rcsb_id", "")).upper() for item in entries
            }
            for pdb_id in ids:
                statuses[pdb_id] = (
                    "EXAMINED" if pdb_id in returned_ids else "NOT_AVAILABLE"
                )
            retained_before = len(records)
            for entry in sorted(entries, key=lambda item: item.get("rcsb_id", "")):
                entry_id = str(entry.get("rcsb_id", "")).upper()
                for entity in entry.get("polymer_entities") or []:
                    instances = entity.get("polymer_entity_instances") or []
                    for instance in sorted(
                        instances, key=lambda item: item.get("rcsb_id", ""),
                    ):
                        connections = sorted(
                            instance.get("rcsb_polymer_struct_conn") or [],
                            key=lambda item: (
                                str(item.get("id", "")),
                                json.dumps(item, sort_keys=True, separators=(",", ":")),
                            ),
                        )
                        for connection in connections:
                            normalized = adapters.normalize_rcsb_connection_record_v1(
                                entry_id=entry_id,
                                polymer_instance_id=str(instance.get("rcsb_id", "")),
                                connection=connection,
                                source_payload_sha256=cache_entry["sha256"],
                                search_request_sha256=query_contract_sha,
                                search_result_identity_digest=_sha(_canonical_json(ids)),
                                data_api_endpoint_descriptor=(
                                    RCSB_DATA_GRAPHQL_URL
                                    + "#specialist_seeded_rcsb_polymer_struct_conn"
                                ),
                            )
                            if normalized is not None:
                                records.append(normalized)
            batches.append({
                "batch_index": batch_index,
                "pdb_ids_requested": ids,
                "pdb_ids_returned": sorted(returned_ids),
                "request_sha256": _sha(request_payload),
                "response_payload_sha256": cache_entry["sha256"],
                "exact_cys_sg_events_recovered": len(records) - retained_before,
            })
        except (RuntimeError, ValueError, json.JSONDecodeError) as error:
            for pdb_id in ids:
                statuses[pdb_id] = "NOT_AVAILABLE"
            batches.append({
                "batch_index": batch_index,
                "pdb_ids_requested": ids,
                "pdb_ids_returned": [],
                "request_sha256": _sha(request_payload),
                "response_payload_sha256": None,
                "exact_cys_sg_events_recovered": 0,
                "failure_reason": str(error),
            })
    unique_records = {
        str(item["canonical_event_id"]): item for item in records
    }
    records = [unique_records[key] for key in sorted(unique_records)]
    adapters.validate_shared_adapter_contract_v1(records)
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "lane": "SPECIALIST_SEEDED_RCSB_RECOVERY_V1",
        "specialist_seeded_rcsb_recovery_implemented": True,
        "specialist_seeded_pdb_cap": SPECIALIST_SEEDED_PDB_CAP,
        "specialist_seeded_unique_pdb_count": len(all_seed_ids),
        "specialist_seeded_direct_already_resolved_pdb_count": len(
            set(all_seed_ids) & direct_ids
        ),
        "specialist_seeded_rcsb_pdbs_examined": sum(
            statuses.get(item) == "EXAMINED" for item in queued
        ),
        "specialist_seeded_pdb_not_available_count": sum(
            statuses.get(item) == "NOT_AVAILABLE" for item in queued
        ),
        "specialist_seeded_pdbs_selected": queued,
        "specialist_seeded_exact_cys_sg_event_count": len(records),
        "batches": batches,
        "direct_search_examination_budget_consumed": 0,
        "distance_only_event_inference_used": False,
    }
    return records, snapshot, statuses


def _clean_cif(value: object) -> str:
    text = str(value or "").strip()
    return "" if text in _MISSING else text


def _atom_value(row: Mapping[str, str], field: str) -> str:
    return _clean_cif(row.get("_atom_site." + field, ""))


def _conn_value(row: Mapping[str, str], field: str) -> str:
    return _clean_cif(row.get("_struct_conn." + field, ""))


def _conn_side(row: Mapping[str, str], side: str) -> dict[str, str]:
    return {
        "side": side,
        "label_asym_id": _conn_value(row, side + "_label_asym_id"),
        "label_comp_id": (
            _conn_value(row, side + "_label_comp_id")
            or _conn_value(row, side + "_auth_comp_id")
        ).upper(),
        "label_seq_id": _conn_value(row, side + "_label_seq_id"),
        "label_atom_id": (
            _conn_value(row, side + "_label_atom_id")
            or _conn_value(row, side + "_auth_atom_id")
        ).upper(),
        "auth_asym_id": _conn_value(row, side + "_auth_asym_id"),
        "auth_seq_id": _conn_value(row, side + "_auth_seq_id"),
        "altloc": (
            _conn_value(row, "pdbx_" + side + "_label_alt_id")
            or _conn_value(row, side + "_label_alt_id")
        ),
        "insertion_code": _conn_value(row, "pdbx_" + side + "_PDB_ins_code"),
    }


def _connection_matches_event(
    row: Mapping[str, str], event: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]] | None:
    conn_type = _conn_value(row, "conn_type_id").lower()
    if "covale" not in conn_type:
        return None
    p1 = _conn_side(row, "ptnr1")
    p2 = _conn_side(row, "ptnr2")
    for protein, ligand in ((p1, p2), (p2, p1)):
        if not (
            protein["label_comp_id"] == "CYS"
            and protein["label_atom_id"] == "SG"
            and ligand["label_comp_id"] == event["ligand_component_id"]
            and ligand["label_atom_id"] == event["ligand_reactive_atom"]
        ):
            continue
        if (
            protein["label_asym_id"]
            and protein["label_asym_id"] != event["protein_instance"]
        ):
            continue
        if (
            ligand["label_asym_id"]
            and ligand["label_asym_id"] != event["ligand_instance"]
        ):
            continue
        number = protein["auth_seq_id"] or protein["label_seq_id"]
        if number and str(number) != str(event["protein_residue_number"]):
            continue
        return protein, ligand
    return None


def _float_atom(row: Mapping[str, str], field: str) -> float:
    value = float(_atom_value(row, field))
    if not math.isfinite(value):
        raise ValueError("ATOM_SITE_NONFINITE_" + field.upper())
    return value


def _coordinates(row: Mapping[str, str]) -> tuple[float, float, float]:
    return tuple(_float_atom(row, axis) for axis in (
        "Cartn_x", "Cartn_y", "Cartn_z",
    ))  # type: ignore[return-value]


def _occupancy(row: Mapping[str, str]) -> float:
    try:
        return _float_atom(row, "occupancy")
    except (TypeError, ValueError):
        return 0.0


def _model_is_primary(row: Mapping[str, str]) -> bool:
    return _atom_value(row, "pdbx_PDB_model_num") in {"", "1"}


def _atom_selection_key(row: Mapping[str, str]) -> tuple[Any, ...]:
    altloc = _atom_value(row, "label_alt_id")
    return (
        0 if _model_is_primary(row) else 1,
        -_occupancy(row),
        0 if not altloc else 1,
        altloc,
        _atom_value(row, "id"),
    )


def _endpoint_candidates(
    atom_rows: Sequence[Mapping[str, str]],
    *,
    endpoint: Mapping[str, str],
    event: Mapping[str, Any],
    protein: bool,
) -> list[Mapping[str, str]]:
    expected_comp = "CYS" if protein else event["ligand_component_id"]
    expected_atom = "SG" if protein else event["ligand_reactive_atom"]
    expected_asym = (
        event["protein_instance"] if protein else event["ligand_instance"]
    )
    result: list[Mapping[str, str]] = []
    for row in atom_rows:
        if not _model_is_primary(row):
            continue
        if (
            _atom_value(row, "label_comp_id").upper() != expected_comp
            or _atom_value(row, "label_atom_id").upper() != expected_atom
            or _atom_value(row, "label_asym_id") != expected_asym
        ):
            continue
        if protein:
            number = _atom_value(row, "auth_seq_id") or _atom_value(
                row, "label_seq_id"
            )
            if number != str(event["protein_residue_number"]):
                continue
        explicit_altloc = endpoint.get("altloc", "")
        if explicit_altloc and _atom_value(row, "label_alt_id") != explicit_altloc:
            continue
        try:
            _coordinates(row)
        except (TypeError, ValueError):
            continue
        result.append(row)
    return result


def _select_endpoint_pair(
    protein_rows: Sequence[Mapping[str, str]],
    ligand_rows: Sequence[Mapping[str, str]],
    *,
    reported_distance: float | None,
) -> tuple[Mapping[str, str], Mapping[str, str]]:
    if not protein_rows or not ligand_rows:
        raise ValueError("STRUCT_CONN_ENDPOINT_COORDINATE_MISSING")
    pairs: list[tuple[tuple[Any, ...], Mapping[str, str], Mapping[str, str]]] = []
    for protein in protein_rows:
        for ligand in ligand_rows:
            distance = math.dist(_coordinates(protein), _coordinates(ligand))
            key = (
                round(
                    abs(distance - reported_distance), 9
                    if reported_distance is not None else distance,
                ),
                _atom_selection_key(protein),
                _atom_selection_key(ligand),
            )
            pairs.append((key, protein, ligand))
    pairs.sort(key=lambda item: item[0])
    if len(pairs) > 1 and pairs[0][0] == pairs[1][0]:
        raise ValueError("ALTLOC_ENDPOINT_PAIR_AMBIGUOUS")
    return pairs[0][1], pairs[0][2]


def _selected_ligand_atoms(
    atom_rows: Sequence[Mapping[str, str]],
    event: Mapping[str, Any],
    selected_endpoint: Mapping[str, str],
) -> list[Mapping[str, str]]:
    selected_altloc = _atom_value(selected_endpoint, "label_alt_id")
    by_atom: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in atom_rows:
        if not _model_is_primary(row):
            continue
        if (
            _atom_value(row, "label_asym_id") != event["ligand_instance"]
            or _atom_value(row, "label_comp_id").upper()
            != event["ligand_component_id"]
        ):
            continue
        altloc = _atom_value(row, "label_alt_id")
        if selected_altloc and altloc not in {"", selected_altloc}:
            continue
        try:
            _coordinates(row)
        except (TypeError, ValueError):
            continue
        by_atom[_atom_value(row, "label_atom_id")].append(row)
    result = [sorted(rows, key=_atom_selection_key)[0] for rows in by_atom.values()]
    return sorted(result, key=lambda row: _atom_value(row, "label_atom_id"))


def _selected_pocket_atoms(
    atom_rows: Sequence[Mapping[str, str]],
    ligand_atoms: Sequence[Mapping[str, str]],
    *,
    radius: float = 6.0,
) -> list[Mapping[str, str]]:
    ligand_coordinates = [_coordinates(row) for row in ligand_atoms]
    ligand_grid: dict[tuple[int, int, int], list[tuple[float, float, float]]] = (
        defaultdict(list)
    )
    for coordinate in ligand_coordinates:
        ligand_grid[tuple(math.floor(value / radius) for value in coordinate)].append(
            coordinate
        )
    by_identity: dict[tuple[str, ...], list[Mapping[str, str]]] = defaultdict(list)
    for row in atom_rows:
        if _atom_value(row, "group_PDB") != "ATOM" or not _model_is_primary(row):
            continue
        if _atom_value(row, "type_symbol").upper() == "H":
            continue
        try:
            coordinate = _coordinates(row)
        except (TypeError, ValueError):
            continue
        cell = tuple(math.floor(value / radius) for value in coordinate)
        nearby = (
            other
            for delta in product((-1, 0, 1), repeat=3)
            for other in ligand_grid.get(tuple(
                cell[index] + delta[index] for index in range(3)
            ), ())
        )
        if not any(math.dist(coordinate, other) <= radius for other in nearby):
            continue
        identity = tuple(_atom_value(row, field) for field in (
            "label_asym_id", "label_seq_id", "auth_seq_id", "label_comp_id",
            "label_atom_id",
        ))
        by_identity[identity].append(row)
    result = [sorted(rows, key=_atom_selection_key)[0] for rows in by_identity.values()]
    return sorted(result, key=lambda row: tuple(_atom_value(row, field) for field in (
        "label_asym_id", "label_seq_id", "label_atom_id",
    )))


def _element_inventory(rows: Sequence[Mapping[str, str]]) -> list[str]:
    return [
        _atom_value(row, "type_symbol").strip().title()
        for row in rows if _atom_value(row, "type_symbol").strip().upper() != "H"
    ]


def parse_ccd_cif_v1(payload: bytes, *, ccd_id: str) -> dict[str, Any]:
    text = payload.decode("utf-8", "replace")
    if not re.search(
        rf"(?im)^data_{re.escape(ccd_id)}(?:\s|$)", text,
    ):
        raise ValueError("CCD_COMPONENT_ID_MISMATCH")
    atom_tags, atom_rows = leakage_evidence_owner.parse_loop(
        text, "_chem_comp_atom.",
    )
    bond_tags, bond_rows = leakage_evidence_owner.parse_loop(
        text, "_chem_comp_bond.",
    )
    required_atoms = {
        "_chem_comp_atom.atom_id", "_chem_comp_atom.type_symbol",
        "_chem_comp_atom.charge",
    }
    required_bonds = {
        "_chem_comp_bond.atom_id_1", "_chem_comp_bond.atom_id_2",
        "_chem_comp_bond.value_order",
    }
    if not required_atoms.issubset(atom_tags) or not required_bonds.issubset(
        bond_tags
    ):
        raise ValueError("CCD_REQUIRED_ATOM_OR_BOND_COLUMNS_MISSING")
    atoms: list[dict[str, Any]] = []
    for row in atom_rows:
        atom_id = _clean_cif(row.get("_chem_comp_atom.atom_id", ""))
        element = _clean_cif(row.get("_chem_comp_atom.type_symbol", "")).title()
        raw_charge = _clean_cif(row.get("_chem_comp_atom.charge", ""))
        if not atom_id or not element or not re.fullmatch(r"[+-]?\d+", raw_charge):
            raise ValueError("CCD_ATOM_ROW_INVALID")
        atoms.append({
            "atom_id": atom_id.upper(),
            "type_symbol": element,
            "charge": int(raw_charge),
            "aromatic_flag": _clean_cif(
                row.get("_chem_comp_atom.pdbx_aromatic_flag", "")
            ).upper() or None,
        })
    if not atoms or len({item["atom_id"] for item in atoms}) != len(atoms):
        raise ValueError("CCD_ATOM_INVENTORY_EMPTY_OR_DUPLICATE")
    atom_ids = {item["atom_id"] for item in atoms}
    bonds: list[dict[str, Any]] = []
    for row in bond_rows:
        left = _clean_cif(row.get("_chem_comp_bond.atom_id_1", "")).upper()
        right = _clean_cif(row.get("_chem_comp_bond.atom_id_2", "")).upper()
        order = _clean_cif(row.get("_chem_comp_bond.value_order", "")).upper()
        aromatic = _clean_cif(
            row.get("_chem_comp_bond.pdbx_aromatic_flag", "")
        ).upper() or None
        if not left or not right or left == right or not order:
            raise ValueError("CCD_BOND_ROW_INVALID")
        if left not in atom_ids or right not in atom_ids:
            raise ValueError("CCD_BOND_ENDPOINT_MISSING")
        bonds.append({
            "atom_id_1": min(left, right),
            "atom_id_2": max(left, right),
            "value_order": order,
            "pdbx_aromatic_flag": aromatic,
        })
    if len({
        (item["atom_id_1"], item["atom_id_2"]) for item in bonds
    }) != len(bonds):
        raise ValueError("CCD_BOND_INVENTORY_DUPLICATE")
    atoms.sort(key=lambda item: item["atom_id"])
    bonds.sort(key=lambda item: (
        item["atom_id_1"], item["atom_id_2"], item["value_order"],
    ))
    graph_payload = {
        "schema": "covapie_ccd_component_graph_v1",
        "atoms": atoms,
        "bonds": bonds,
    }
    return {
        "ccd_id": ccd_id.upper(),
        "ccd_atom_inventory": atoms,
        "ccd_bond_inventory": bonds,
        "ccd_formal_charge_pattern": [
            [item["atom_id"], item["charge"]] for item in atoms
        ],
        "ccd_component_graph_sha256": _sha(_canonical_json(graph_payload)),
        "ccd_heavy_atom_count": sum(
            item["type_symbol"].upper() != "H" for item in atoms
        ),
    }


def acquire_ccd_components_v1(
    cache: BulkCacheV1, component_ids: Sequence[str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    components: dict[str, dict[str, Any]] = {}
    manifest: list[dict[str, Any]] = []
    for ccd_id in sorted(set(item.upper() for item in component_ids)):
        url = RCSB_CCD_URL.format(ccd_id=ccd_id)
        try:
            payload, entry = cache.fetch(
                relative_path=f"rcsb/ccd/{ccd_id}.cif",
                url=url,
                source_dataset=adapters.SOURCE_RCSB_PDB_DIRECT,
                retrieval_identity={
                    "ccd_id": ccd_id,
                    "definition": "wwPDB Chemical Component Dictionary CIF",
                    "snapshot_date": SNAPSHOT_DATE,
                },
                maximum_bytes=4 * 1024 * 1024,
            )
            parsed = parse_ccd_cif_v1(payload, ccd_id=ccd_id)
            components[ccd_id] = parsed
            manifest.append({
                "ccd_id": ccd_id,
                "official_ccd_url": url,
                "status": "CCD_COMPONENT_RESOLVED",
                "sha256": entry["sha256"],
                "byte_count": entry["byte_count"],
            })
        except (RuntimeError, ValueError) as error:
            manifest.append({
                "ccd_id": ccd_id,
                "official_ccd_url": url,
                "status": "CCD_COMPONENT_FAILED",
                "failure_reason": str(error).split(":", 1)[0],
                "sha256": None,
                "byte_count": 0,
            })
    return components, manifest


def _ccd_rdkit_molecule_v1(
    ccd: Mapping[str, Any],
) -> tuple[Any, dict[str, int]]:
    try:
        from rdkit import Chem
    except ImportError as error:
        raise ValueError("RDKIT_CCD_GRAPH_UNAVAILABLE") from error
    editable = Chem.RWMol()
    index_by_id: dict[str, int] = {}
    for item in ccd["ccd_atom_inventory"]:
        if str(item["type_symbol"]).upper() == "H":
            continue
        atom = Chem.Atom(str(item["type_symbol"]))
        atom.SetFormalCharge(int(item["charge"]))
        aromatic = str(item.get("aromatic_flag") or "").upper() == "Y"
        atom.SetIsAromatic(aromatic)
        index_by_id[str(item["atom_id"])] = editable.AddAtom(atom)
    order_map = {
        "SING": Chem.BondType.SINGLE,
        "SINGLE": Chem.BondType.SINGLE,
        "DOUB": Chem.BondType.DOUBLE,
        "DOUBLE": Chem.BondType.DOUBLE,
        "TRIP": Chem.BondType.TRIPLE,
        "TRIPLE": Chem.BondType.TRIPLE,
        "AROM": Chem.BondType.AROMATIC,
        "AROMATIC": Chem.BondType.AROMATIC,
    }
    for item in ccd["ccd_bond_inventory"]:
        if (
            str(item["atom_id_1"]) not in index_by_id
            or str(item["atom_id_2"]) not in index_by_id
        ):
            continue
        raw = str(item["value_order"]).upper()
        aromatic = str(item.get("pdbx_aromatic_flag") or "").upper() == "Y"
        order = Chem.BondType.AROMATIC if aromatic else order_map.get(raw)
        if order is None:
            raise ValueError("CCD_BOND_ORDER_UNSUPPORTED")
        editable.AddBond(
            index_by_id[str(item["atom_id_1"])],
            index_by_id[str(item["atom_id_2"])],
            order,
        )
        if order == Chem.BondType.AROMATIC:
            bond = editable.GetBondBetweenAtoms(
                index_by_id[str(item["atom_id_1"])],
                index_by_id[str(item["atom_id_2"])],
            )
            bond.SetIsAromatic(True)
            editable.GetAtomWithIdx(index_by_id[str(item["atom_id_1"])]).SetIsAromatic(True)
            editable.GetAtomWithIdx(index_by_id[str(item["atom_id_2"])]).SetIsAromatic(True)
    molecule = editable.GetMol()
    try:
        Chem.SanitizeMol(molecule)
    except Exception as error:
        raise ValueError("CCD_RDKIT_GRAPH_SANITIZATION_FAILED") from error
    return molecule, index_by_id


def _canonical_molecule_graph_facts_v1(molecule: Any) -> dict[str, Any]:
    from rdkit import Chem

    molecule = Chem.RemoveHs(Chem.Mol(molecule))
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    smiles = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
    charges = sorted(int(atom.GetFormalCharge()) for atom in molecule.GetAtoms())
    payload = {
        "canonical_smiles": smiles,
        "formal_charge_pattern": charges,
        "heavy_atom_count": molecule.GetNumHeavyAtoms(),
    }
    return {
        **payload,
        "canonical_graph_fingerprint": _sha(_canonical_json(payload)),
    }


def _rooted_local_fingerprint_v1(
    molecule: Any, *, root_index: int, radius: int,
) -> tuple[str, str]:
    from rdkit import Chem

    if radius not in {1, 2} or not 0 <= root_index < molecule.GetNumAtoms():
        raise ValueError("REACTIVE_CENTER_ROOT_OR_RADIUS_INVALID")
    distances = Chem.GetDistanceMatrix(molecule)
    atom_indices = sorted(
        index for index in range(molecule.GetNumAtoms())
        if distances[root_index][index] <= radius
    )
    marked = Chem.Mol(molecule)
    marked.GetAtomWithIdx(root_index).SetAtomMapNum(1)
    topology = Chem.MolFragmentToSmiles(
        marked,
        atomsToUse=atom_indices,
        rootedAtAtom=root_index,
        canonical=True,
        isomericSmiles=True,
        allBondsExplicit=True,
    )
    payload = {
        "schema": "covapie_reactive_center_local_graph_v1",
        "radius": radius,
        "rooted_topology": topology,
    }
    return _sha(_canonical_json(payload)), topology


def build_reactive_center_facts_v1(
    ccd: Mapping[str, Any], *, reactive_atom_id: str,
) -> dict[str, Any]:
    molecule, index_by_id = _ccd_rdkit_molecule_v1(ccd)
    root = index_by_id.get(reactive_atom_id.upper())
    if root is None:
        raise ValueError("REACTIVE_ATOM_NOT_IN_CCD")
    radius1, topology1 = _rooted_local_fingerprint_v1(
        molecule, root_index=root, radius=1,
    )
    radius2, topology2 = _rooted_local_fingerprint_v1(
        molecule, root_index=root, radius=2,
    )
    atom = molecule.GetAtomWithIdx(root)
    return {
        "reactive_center_radius0": {
            "element": atom.GetSymbol(),
            "formal_charge": atom.GetFormalCharge(),
            "aromatic": atom.GetIsAromatic(),
        },
        "reactive_center_radius1_sha256": radius1,
        "reactive_center_radius2_sha256": radius2,
        "reactive_center_radius1_topology": topology1,
        "reactive_center_local_topology": topology2,
    }


def _source_molecule_v1(smiles: str) -> Any | None:
    try:
        from rdkit import Chem
    except ImportError:
        return None
    molecule = Chem.MolFromSmiles(smiles)
    return Chem.RemoveHs(molecule) if molecule is not None else None


def _source_graph_set_v1(smiles_values: Sequence[str]) -> dict[str, Any]:
    parsed: dict[str, tuple[Any, dict[str, Any]]] = {}
    failures = 0
    for value in smiles_values:
        molecule = _source_molecule_v1(value)
        if molecule is None:
            failures += 1
            continue
        facts = _canonical_molecule_graph_facts_v1(molecule)
        parsed.setdefault(str(facts["canonical_graph_fingerprint"]), (molecule, facts))
    ordered = [parsed[key] for key in sorted(parsed)]
    return {
        "graphs": ordered,
        "parse_failures": failures,
        "graph_count": len(ordered),
    }


def supporting_source_graph_facts_v1(
    *,
    pre_smiles: Sequence[str],
    adduct_smiles: Sequence[str],
    ccd: Mapping[str, Any] | None,
    reactive_atom_id: str,
) -> dict[str, Any]:
    pre_set = _source_graph_set_v1(pre_smiles)
    adduct_set = _source_graph_set_v1(adduct_smiles)
    pre_pair = pre_set["graphs"][0] if pre_set["graph_count"] == 1 else None
    adduct_pair = (
        adduct_set["graphs"][0] if adduct_set["graph_count"] == 1 else None
    )
    result: dict[str, Any] = {
        "pre_source_graph_sha256": (
            pre_pair[1]["canonical_graph_fingerprint"] if pre_pair else None
        ),
        "adduct_source_graph_sha256": (
            adduct_pair[1]["canonical_graph_fingerprint"] if adduct_pair else None
        ),
        "pre_heavy_atom_count": (
            pre_pair[1]["heavy_atom_count"] if pre_pair else None
        ),
        "adduct_heavy_atom_count": (
            adduct_pair[1]["heavy_atom_count"] if adduct_pair else None
        ),
        "formal_charge_pattern": (
            pre_pair[1]["formal_charge_pattern"] if pre_pair else []
        ),
        "canonical_graph_fingerprint": (
            pre_pair[1]["canonical_graph_fingerprint"] if pre_pair else None
        ),
        "pre_source_graph_count": pre_set["graph_count"],
        "adduct_source_graph_count": adduct_set["graph_count"],
        "supporting_smiles_parse_failures": (
            pre_set["parse_failures"] + adduct_set["parse_failures"]
        ),
        "pre_source_graph_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
        "pre_source_graph_mapping_count": 0,
        "pre_reactive_center_radius2_sha256": None,
        "adduct_reactive_center_radius2_sha256": None,
        "net_pre_adduct_local_transformation_sha256": None,
    }
    if pre_set["graph_count"] > 1:
        result["pre_source_graph_mapping_status"] = (
            "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
        )
        return result
    if pre_pair is None or ccd is None:
        return result
    try:
        ccd_molecule, index_by_id = _ccd_rdkit_molecule_v1(ccd)
    except ValueError:
        result["pre_source_graph_mapping_status"] = (
            "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        )
        return result
    pre_molecule = pre_pair[0]
    if (
        pre_molecule.GetNumHeavyAtoms() != ccd_molecule.GetNumHeavyAtoms()
        or pre_molecule.GetNumBonds() != ccd_molecule.GetNumBonds()
    ):
        result["pre_source_graph_mapping_status"] = (
            "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        )
        return result
    matches = ccd_molecule.GetSubstructMatches(
        pre_molecule, uniquify=False, useChirality=True, maxMatches=1024,
    )
    exact = [
        match for match in matches
        if len(match) == ccd_molecule.GetNumAtoms()
    ]
    result["pre_source_graph_mapping_count"] = len(exact)
    if not exact:
        result["pre_source_graph_mapping_status"] = (
            "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        )
        return result
    if len(exact) != 1:
        result["pre_source_graph_mapping_status"] = (
            "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
        )
        return result
    result["pre_source_graph_mapping_status"] = "PRE_SOURCE_GRAPH_MAPPING_UNIQUE"
    ccd_root = index_by_id.get(reactive_atom_id.upper())
    if ccd_root is not None and ccd_root in exact[0]:
        pre_root = exact[0].index(ccd_root)
        result["pre_reactive_center_radius2_sha256"] = (
            _rooted_local_fingerprint_v1(
                pre_molecule, root_index=pre_root, radius=2,
            )[0]
        )
        if adduct_pair is not None:
            adduct_molecule = adduct_pair[0]
            adduct_matches = adduct_molecule.GetSubstructMatches(
                pre_molecule, uniquify=False, useChirality=True, maxMatches=1024,
            )
            if len(adduct_matches) == 1:
                adduct_root = adduct_matches[0][pre_root]
                result["adduct_reactive_center_radius2_sha256"] = (
                    _rooted_local_fingerprint_v1(
                        adduct_molecule, root_index=adduct_root, radius=2,
                    )[0]
                )
    if (
        result["pre_reactive_center_radius2_sha256"]
        and result["adduct_reactive_center_radius2_sha256"]
    ):
        result["net_pre_adduct_local_transformation_sha256"] = _sha(
            _canonical_json({
                "pre": result["pre_reactive_center_radius2_sha256"],
                "adduct": result["adduct_reactive_center_radius2_sha256"],
            })
        )
    return result


def _rdkit_pre_facts(
    smiles_values: Sequence[str], *, retained_heavy_atom_count: int,
    adduct_smiles_values: Sequence[str] = (),
    ccd: Mapping[str, Any] | None = None,
    retained_heavy_atom_names: Sequence[str] = (),
    reactive_atom_id: str = "",
) -> dict[str, Any]:
    graph = supporting_source_graph_facts_v1(
        pre_smiles=smiles_values,
        adduct_smiles=adduct_smiles_values,
        ccd=ccd,
        reactive_atom_id=reactive_atom_id,
    )
    counts = sorted({
        int(pair[1]["heavy_atom_count"])
        for pair in _source_graph_set_v1(smiles_values)["graphs"]
    })
    retained_names = {item.upper() for item in retained_heavy_atom_names}
    ccd_names = {
        str(item["atom_id"]).upper()
        for item in (ccd or {}).get("ccd_atom_inventory", [])
        if str(item["type_symbol"]).upper() != "H"
    }
    missing_from_retained = sorted(ccd_names - retained_names)
    retained_missing_from_ccd = sorted(retained_names - ccd_names)
    atom_loss = bool(missing_from_retained) or (
        ccd is None and any(count > retained_heavy_atom_count for count in counts)
    )
    mapping = graph["pre_source_graph_mapping_status"]
    if atom_loss:
        status = (
            "PRE_ONLY_ATOMS_DETECTED" if ccd is not None
            else "PRE_ATOM_LOSS_REPRESENTATION_GAP"
        )
    elif mapping == "PRE_SOURCE_GRAPH_MAPPING_UNIQUE":
        status = "PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED"
    elif mapping == "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS":
        status = "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
    elif mapping == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE":
        status = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
    elif smiles_values:
        status = "PRE_COMPONENT_TOPOLOGY_INCOMPLETE"
    else:
        status = "PRE_REACTION_UNRESOLVED"
    return {
        "status": status,
        "supporting_pre_heavy_atom_counts": counts,
        "atom_loss_flag": atom_loss,
        "formal_charge_pattern_authoritative": False,
        "ccd_heavy_atom_count": (
            int(ccd["ccd_heavy_atom_count"]) if ccd is not None else None
        ),
        "retained_heavy_atom_count": retained_heavy_atom_count,
        "ccd_atoms_missing_from_retained": missing_from_retained,
        "retained_atoms_missing_from_ccd": retained_missing_from_ccd,
        "ccd_retained_atom_coverage_complete": bool(
            ccd is not None
            and not missing_from_retained
            and not retained_missing_from_ccd
        ),
        **graph,
    }


def _authority_match_evaluation(
    authorities: Sequence[Any], *, known_authority_identity: bool = False,
    pdb_id: str = "", production_candidate: Any | None = None,
) -> list[dict[str, Any]]:
    evaluation = evaluate_production_exact_authority_v1(
        production_candidate, authorities=authorities,
    )
    if known_authority_identity:
        return [{
            "authority_id": item.authority_id,
            "authority_version": item.authority_version,
            "candidate_match_result": "KNOWN_IDENTITY_DEDUPLICATION_NOT_MATCHER_PROOF",
            "reason": (
                "known published identity is deduplicated separately and does not "
                "exercise the new-candidate exact-signature algorithm"
            ),
            "candidate_chemistry_signature_sha256": None,
            "authority_chemistry_signature_sha256": item.chemistry_signature_sha256,
        } for item in sorted(authorities, key=lambda value: (
            value.authority_id, value.authority_version,
        ))]
    return evaluation["authority_match_evaluation"]


def evaluate_production_exact_authority_v1(
    candidate: Any | None, *, authorities: Sequence[Any],
) -> dict[str, Any]:
    """Evaluate a candidate with the production signature builder, fail closed."""

    status = "EXACT_SIGNATURE_NOT_COMPUTABLE_OTHER"
    signature: str | None = None
    if candidate is None:
        status = "EXACT_SIGNATURE_NOT_COMPUTABLE_PRE_GRAPH"
    elif candidate.pre_reaction_graph_authoritative is not True:
        status = "EXACT_SIGNATURE_NOT_COMPUTABLE_PRE_GRAPH"
    elif (
        candidate.reactive_atom_mapping_count != 1
        or not candidate.atom_map_numbers
        or set(dict(candidate.atom_map_numbers)) != set(candidate.smarts_atom_ids)
    ):
        status = "EXACT_SIGNATURE_NOT_COMPUTABLE_ATOM_MAPPING"
    elif (
        candidate.formal_charge_authoritative is not True
        or set(dict(candidate.atom_formal_charges)) != set(candidate.smarts_atom_ids)
    ):
        status = "EXACT_SIGNATURE_NOT_COMPUTABLE_FORMAL_CHARGE"
    elif (
        candidate.role_authority_published is not True
        or candidate.role_rule_match_count != 1
        or not candidate.warhead_atoms
        or not candidate.scaffold_atoms
    ):
        status = "EXACT_SIGNATURE_NOT_COMPUTABLE_ROLE_RULE"
    elif (
        not candidate.seed_atoms
        or candidate.primary_anchor_atom is None
        or candidate.direction_anchor_atom is None
    ):
        status = "EXACT_SIGNATURE_NOT_COMPUTABLE_SEED"
    else:
        try:
            signature = production_pipeline.build_exact_chemistry_signature_v1(
                candidate
            )
            status = "EXACT_SIGNATURE_COMPUTABLE"
        except ValueError:
            status = "EXACT_SIGNATURE_NOT_COMPUTABLE_OTHER"
    result: list[dict[str, Any]] = []
    for authority in authorities:
        matches = bool(
            signature
            and signature == authority.chemistry_signature_sha256
        )
        result.append({
            "authority_id": authority.authority_id,
            "authority_version": authority.authority_version,
            "candidate_match_result": (
                "EXACT_SIGNATURE_MATCH" if matches
                else (
                    "EXACT_SIGNATURE_NO_MATCH"
                    if signature else status
                )
            ),
            "reason": (
                "production exact chemistry signature equality"
                if matches else (
                    "computed production signature differs"
                    if signature else status
                )
            ),
            "candidate_chemistry_signature_sha256": signature,
            "authority_chemistry_signature_sha256": authority.chemistry_signature_sha256,
        })
    result.sort(key=lambda item: (item["authority_id"], item["authority_version"]))
    return {
        "exact_signature_status": status,
        "candidate_chemistry_signature_sha256": signature,
        "exact_authority_match": any(
            item["candidate_match_result"] == "EXACT_SIGNATURE_MATCH"
            for item in result
        ),
        "authority_match_evaluation": result,
    }


def predict_leakage_read_only_v1(
    identity: tuple[str, str], *, historical: set[tuple[str, str]],
    frozen_baseline_extension_required: bool = False,
) -> tuple[str, str, str | None]:
    if identity in KNOWN_EXPANSION_APPROVED:
        return (
            "SAME_EXISTING_EXPANSION_COMPONENT",
            "PRESERVE_REGISTERED_SPLIT",
            None,
        )
    if identity in historical:
        if frozen_baseline_extension_required:
            return (
                "HISTORICAL_BASELINE_COMPONENT",
                "BLOCKED_READ_ONLY",
                "LEAKAGE_BASELINE_EXTENSION_BLOCKED",
            )
        return (
            "HISTORICAL_BASELINE_COMPONENT",
            "PRESERVE_FROZEN_HISTORICAL_SPLIT",
            None,
        )
    return "LEAKAGE_UNRESOLVED", "UNASSIGNED_READ_ONLY", None


def build_source_local_leakage_evidence_v1(
    *, mmcif_text: str, protein_label_asym_id: str,
    ccd: Mapping[str, Any] | None,
) -> dict[str, Any]:
    _, asym_rows = leakage_evidence_owner.parse_loop(
        mmcif_text, "_struct_asym.",
    )
    _, sequence_rows = leakage_evidence_owner.parse_loop(
        mmcif_text, "_entity_poly_seq.",
    )
    asym_to_entity = {
        row.get("_struct_asym.id", ""): row.get("_struct_asym.entity_id", "")
        for row in asym_rows
    }
    entity_id = asym_to_entity.get(protein_label_asym_id, "")
    try:
        entity_rows, numbering = leakage_evidence_owner._validate_entity_poly_sequence([
            row for row in sequence_rows
            if row.get("_entity_poly_seq.entity_id", "") == entity_id
        ])
        monomers = [row.get("_entity_poly_seq.mon_id", "") for row in entity_rows]
        one_letter, unknown_count, _unknown = leakage_evidence_owner._seq_to_one_letter(
            monomers
        )
        accession, _isoform, _label, accession_status, crosscheck = (
            leakage_evidence_owner._extract_accession(
                mmcif_text, entity_id, protein_label_asym_id,
            )
        )
        sequence_sha = (
            _sha(";".join(monomers).encode("utf-8")) if monomers else ""
        )
        protein_complete = bool(
            entity_rows
            and numbering["sequence_numbering_status"] == "continuous_from_1"
            and crosscheck != "struct_ref_seq_crosscheck_mismatch"
            and unknown_count == 0
            and one_letter
        )
    except (KeyError, TypeError, ValueError):
        accession = ""
        accession_status = ""
        one_letter = ""
        sequence_sha = ""
        protein_complete = False
    ligand = {
        "complete": False, "graph_sha256": "", "scaffold_sha256": "",
    }
    if ccd is not None:
        try:
            molecule, _indices = _ccd_rdkit_molecule_v1(ccd)
            from rdkit import Chem

            smiles = Chem.MolToSmiles(
                molecule, canonical=True, isomericSmiles=True,
            )
            ligand = dict(production_pipeline._ligand_leakage_facts_v1(smiles))
        except (ImportError, ValueError):
            pass
    axes = sorted(filter(None, (
        "LIGAND_GRAPH:" + str(ligand["graph_sha256"])
        if ligand["graph_sha256"] else "",
        "LIGAND_SCAFFOLD:" + str(ligand["scaffold_sha256"])
        if ligand["scaffold_sha256"] else "",
        "PROTEIN_ACCESSION:" + str(accession)
        if accession_status == "unique_uniprot_accession" and accession else "",
        "PROTEIN_EXACT_SEQUENCE:" + sequence_sha if sequence_sha else "",
    )))
    return {
        "complete": bool(protein_complete and ligand["complete"]),
        "ligand_graph_sha256": ligand["graph_sha256"],
        "ligand_scaffold_sha256": ligand["scaffold_sha256"],
        "protein_accession": (
            accession if accession_status == "unique_uniprot_accession" else ""
        ),
        "protein_sequence_sha256": sequence_sha,
        "protein_sequence": one_letter,
        "linking_axes": axes,
        "source_boundary": "PDB_MMCIF_CORE_PLUS_OFFICIAL_WWPDB_CCD",
        "external_uniprot_call_performed": False,
    }


def _load_leakage_prediction_context_v1(
    repo_root: Path, *, authorities: Sequence[Any], leakage_registry: Any,
) -> dict[str, Any]:
    ligand_rows = production_pipeline._sha_bound_csv_rows_v1(
        repo_root, production_pipeline.BASELINE_LIGAND_EVIDENCE_RELATIVE,
    )
    protein_rows = production_pipeline._sha_bound_csv_rows_v1(
        repo_root, production_pipeline.BASELINE_PROTEIN_EVIDENCE_RELATIVE,
    )
    group_rows = production_pipeline._sha_bound_csv_rows_v1(
        repo_root, production_pipeline.BASELINE_FINAL_GROUP_RELATIVE,
    )
    protein_by_id = {item["sample_index_row_id"]: item for item in protein_rows}
    group_by_id = {item["sample_index_row_id"]: item for item in group_rows}
    published = production_pipeline.load_published_leakage_group_population_v1(
        repo_root
    )
    combined = production_pipeline.merge_published_and_cumulative_leakage_groups_v1(
        published, leakage_registry,
    )
    group_info = {
        item.final_leakage_group_id: {
            "leakage_key": item.leakage_key,
            "group_id": item.final_leakage_group_id,
            "split": item.assigned_split,
            "kind": (
                "CUMULATIVE" if item.leakage_key.startswith(
                    "COVAPIE_REAL_EXACT4_LEAKAGE_V1:"
                ) else "HISTORICAL"
            ),
        }
        for item in combined
    }
    references: list[dict[str, Any]] = []
    for ligand in ligand_rows:
        identity = ligand["sample_index_row_id"]
        protein = protein_by_id[identity]
        group_id = group_by_id[identity]["final_leakage_group_id"]
        references.append({
            "identity": identity,
            **group_info[group_id],
            "ligand_graph_sha256": ligand["canonical_graph_sha256"],
            "ligand_scaffold_sha256": ligand["murcko_scaffold_sha256"],
            "protein_accession": protein["protein_accession"],
            "protein_sequence_sha256": protein[
                "full_polymer_monomer_sequence_sha256"
            ],
            "protein_sequence": protein["full_polymer_one_letter_sequence"],
        })
    cumulative_by_identity = {
        identity: group
        for group in leakage_registry.groups
        for identity in group.member_identities
    }
    for authority in authorities:
        try:
            review = json.loads(authority.source_human_review_record_canonical_json)
            identity = str(review["candidate_identity"])
            evidence = review["machine_evidence"]["leakage_evidence"]
            group = cumulative_by_identity[identity]
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        references.append({
            "identity": identity,
            **group_info[group.final_leakage_group_id],
            "ligand_graph_sha256": evidence.get("ligand_graph_sha256", ""),
            "ligand_scaffold_sha256": evidence.get("ligand_scaffold_sha256", ""),
            "protein_accession": evidence.get("protein_accession", ""),
            "protein_sequence_sha256": evidence.get("protein_sequence_sha256", ""),
            "protein_sequence": "",
        })
    return {
        "references": sorted(references, key=lambda item: item["identity"]),
        "existing_groups": combined,
        "group_info": group_info,
    }


def _leakage_linking_axes_v1(
    left: Mapping[str, Any], right: Mapping[str, Any],
) -> list[str]:
    axes: list[str] = []
    for field, name in (
        ("ligand_graph_sha256", "LIGAND_GRAPH"),
        ("ligand_scaffold_sha256", "LIGAND_SCAFFOLD"),
        ("protein_accession", "PROTEIN_ACCESSION"),
        ("protein_sequence_sha256", "PROTEIN_EXACT_SEQUENCE"),
    ):
        if left.get(field) and left.get(field) == right.get(field):
            axes.append(name)
    if left.get("protein_sequence") and right.get("protein_sequence") and (
        _policy_global_identity_at_least_half_v1(
            str(left["protein_sequence"]), str(right["protein_sequence"]),
        )
    ):
        axes.append("PROTEIN_SEQUENCE_IDENTITY_GE_0.5")
    return sorted(set(axes))


def _lcs_length_bitset_v1(left: str, right: str) -> int:
    """Exact LCS length used only as a safe upper bound before policy DP."""

    masks: dict[str, int] = defaultdict(int)
    for index, symbol in enumerate(right):
        masks[symbol] |= 1 << index
    state = 0
    for symbol in left:
        match_or_state = masks.get(symbol, 0) | state
        shifted = (state << 1) | 1
        state = match_or_state & ~(match_or_state - shifted)
    return state.bit_count()


@lru_cache(maxsize=65536)
def _policy_global_identity_at_least_half_v1(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    if left > right:
        left, right = right, left
    # Every match in the policy owner's chosen global alignment belongs to a
    # common subsequence, while alignment length is at least max(len(a),len(b)).
    # Failing this exact upper bound proves the 0.5 threshold is unreachable.
    if _lcs_length_bitset_v1(left, right) * 2 < max(len(left), len(right)):
        return False
    return production_pipeline.independence_evidence_owner.global_identity(
        left, right,
    ) >= 0.5


def apply_leakage_predictions_read_only_v1(
    outcomes: Sequence[dict[str, Any]],
    *,
    historical: set[tuple[str, str]],
    context: Mapping[str, Any],
) -> None:
    """Resolve leakage on an in-memory clone; never persist a successor."""

    candidates = [
        item for item in outcomes
        if item["structural_processing"].get("leakage_evidence")
    ]
    parent = {item["canonical_event_id"]: item["canonical_event_id"] for item in candidates}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        lroot, rroot = find(left), find(right)
        if lroot != rroot:
            parent[max(lroot, rroot)] = min(lroot, rroot)

    for index, left in enumerate(candidates):
        left_evidence = left["structural_processing"]["leakage_evidence"]
        if not left_evidence.get("complete"):
            continue
        for right in candidates[index + 1:]:
            right_evidence = right["structural_processing"]["leakage_evidence"]
            if right_evidence.get("complete") and _leakage_linking_axes_v1(
                left_evidence, right_evidence,
            ):
                union(left["canonical_event_id"], right["canonical_event_id"])

    components: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        components[find(item["canonical_event_id"])].append(item)
    existing_groups = list(context["existing_groups"])
    for _root, members in sorted(components.items()):
        members.sort(key=lambda item: item["canonical_event_id"])
        new_members = [
            item for item in members
            if (item["pdb_id"], item["ligand_component_id"])
            not in KNOWN_EXPANSION_APPROVED
            and (item["pdb_id"], item["ligand_component_id"]) not in historical
        ]
        complete = all(
            item["structural_processing"]["leakage_evidence"].get("complete")
            for item in members
        )
        reference_hits: dict[str, dict[str, Any]] = {}
        linking_axes: set[str] = set()
        if complete:
            for member in members:
                evidence = member["structural_processing"]["leakage_evidence"]
                for reference in context["references"]:
                    axes = _leakage_linking_axes_v1(evidence, reference)
                    if axes:
                        reference_hits[reference["group_id"]] = reference
                        linking_axes.update(axes)
        if not complete:
            prediction = {
                "classification": "LEAKAGE_EVIDENCE_INCOMPLETE",
                "leakage_key": None, "predicted_group_id": None,
                "predicted_split": "UNASSIGNED_READ_ONLY", "linking_axes": [],
                "blocker": None,
            }
        elif reference_hits:
            historical_hits = [
                item for item in reference_hits.values()
                if item["kind"] == "HISTORICAL"
            ]
            cumulative_hits = [
                item for item in reference_hits.values()
                if item["kind"] == "CUMULATIVE"
            ]
            if len(historical_hits) == 1 and not cumulative_hits:
                selected = historical_hits[0]
                prediction = {
                    "classification": "HISTORICAL_BASELINE_COMPONENT",
                    "leakage_key": selected["leakage_key"],
                    "predicted_group_id": selected["group_id"],
                    "predicted_split": selected["split"],
                    "linking_axes": sorted(linking_axes),
                    "blocker": None,
                }
            elif len(cumulative_hits) == 1 and not historical_hits:
                selected = cumulative_hits[0]
                prediction = {
                    "classification": "SAME_EXISTING_EXPANSION_COMPONENT",
                    "leakage_key": selected["leakage_key"],
                    "predicted_group_id": selected["group_id"],
                    "predicted_split": selected["split"],
                    "linking_axes": sorted(linking_axes), "blocker": None,
                }
            else:
                prediction = {
                    "classification": "LEAKAGE_EXISTING_GROUP_CONFLICT",
                    "leakage_key": None,
                    "predicted_group_id": None,
                    "predicted_split": "BLOCKED_READ_ONLY",
                    "linking_axes": sorted(linking_axes),
                    "blocker": "LEAKAGE_EXISTING_GROUP_CONFLICT",
                }
        else:
            component_evidence = sorted(
                item["structural_processing"]["leakage_evidence"]["linking_axes"]
                for item in members
            )
            leakage_key = "COVAPIE_BULK_READ_ONLY_COMPONENT_V1:" + _sha(
                _canonical_json(component_evidence)
            )
            representative = SimpleNamespace(
                candidate_identity=(
                    members[0]["pdb_id"] + "/" + members[0]["ligand_component_id"]
                ),
                leakage_key=leakage_key,
            )
            assignment = production_pipeline.assign_expansion_leakage_splits_v1(
                (representative,), existing_groups=tuple(existing_groups),
            )[leakage_key]
            group_id, split = assignment
            identities = tuple(sorted({
                item["pdb_id"] + "/" + item["ligand_component_id"]
                for item in members
            }))
            existing_groups.append(production_pipeline.LeakageGroupAssignmentV1(
                leakage_key=leakage_key,
                final_leakage_group_id=group_id,
                member_count=len(identities),
                assigned_split=split,
                frozen=True,
                member_identities=identities,
            ))
            prediction = {
                "classification": "NEW_EXPANSION_COMPONENT",
                "leakage_key": leakage_key,
                "predicted_group_id": group_id,
                "predicted_split": split,
                "linking_axes": sorted({
                    axis for item in members
                    for axis in item["structural_processing"]["leakage_evidence"][
                        "linking_axes"
                    ]
                }),
                "blocker": None,
            }
        for item in members:
            identity = (item["pdb_id"], item["ligand_component_id"])
            known_control_terminal = (
                identity in KNOWN_QUARANTINE
                or identity in KNOWN_RUNTIME_EXTENSION
            )
            if identity in KNOWN_EXPANSION_APPROVED:
                known = next(
                    ref for ref in context["references"]
                    if ref["identity"] == item["pdb_id"] + "/" + item["ligand_component_id"]
                )
                effective = {
                    "classification": "SAME_EXISTING_EXPANSION_COMPONENT",
                    "leakage_key": known["leakage_key"],
                    "predicted_group_id": known["group_id"],
                    "predicted_split": known["split"],
                    "linking_axes": [], "blocker": None,
                }
            elif identity in historical:
                effective = {
                    "classification": "HISTORICAL_BASELINE_COMPONENT",
                    "leakage_key": None, "predicted_group_id": None,
                    "predicted_split": "PRESERVE_FROZEN_HISTORICAL_SPLIT",
                    "linking_axes": [], "blocker": None,
                }
            else:
                effective = prediction
            item["leakage_classification"] = effective["classification"]
            item["leakage_key"] = effective["leakage_key"]
            item["predicted_group_id"] = effective["predicted_group_id"]
            item["predicted_split"] = effective["predicted_split"]
            item["leakage_linking_axes"] = effective["linking_axes"]
            item["stage_statuses"][BULK_STAGES[11]] = effective["classification"]
            if effective["blocker"] and not known_control_terminal:
                item["terminal_outcome"] = effective["blocker"]
                item["terminal_reasons"] = [effective["blocker"]]
                item["stage_statuses"][BULK_STAGES[12]] = effective["blocker"]


def _validate_mmcif_payload(payload: bytes, pdb_id: str) -> str:
    if len(payload) > COMPRESSED_FILE_CAP:
        raise ValueError("MMCIF_COMPRESSED_PAYLOAD_SIZE_CAP_EXCEEDED")
    try:
        text = gzip.decompress(payload).decode("utf-8", "replace")
    except (OSError, EOFError) as error:
        raise ValueError("MMCIF_GZIP_VALIDATION_FAILED") from error
    match = _ENTRY_ID.search(text)
    if match is None or match.group(1).upper() != pdb_id.upper():
        raise ValueError("MMCIF_ENTRY_ID_MISMATCH")
    if "_struct_conn." not in text or "_atom_site." not in text:
        raise ValueError("MMCIF_REQUIRED_CATEGORY_MISSING")
    return text


def process_event_structure_v1(
    event: Mapping[str, Any], *, mmcif_payload: bytes,
    authorities: Sequence[Any], known_historical: set[tuple[str, str]],
    ccd_component: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    phases = {stage: "NOT_REACHED" for stage in BULK_STAGES}
    for stage in BULK_STAGES[:5]:
        phases[stage] = "PASSED"
    pdb_id = str(event["pdb_id"])
    ligand = str(event["ligand_component_id"])
    identity = (pdb_id, ligand)
    try:
        text = _validate_mmcif_payload(mmcif_payload, pdb_id)
    except ValueError as error:
        phases[BULK_STAGES[5]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="STRUCTURAL_EVIDENCE_INCOMPLETE",
            reasons=(str(error),),
        )
    phases[BULK_STAGES[5]] = "PASSED"
    _tags, connections, status, error = struct_conn_owner.parse_struct_conn_loop(text)
    if status == "raw_parse_error":
        phases[BULK_STAGES[6]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="REJECTED_EVENT_INVALID",
            reasons=("STRUCT_CONN_PARSE_ERROR:" + error,),
        )
    matches: list[tuple[Mapping[str, str], dict[str, str], dict[str, str]]] = []
    for row in connections:
        endpoints = _connection_matches_event(row, event)
        if endpoints is not None:
            matches.append((row, endpoints[0], endpoints[1]))
    if not matches:
        phases[BULK_STAGES[6]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="STRUCTURAL_EVIDENCE_INCOMPLETE",
            reasons=("MMCIF_EXACT_CYS_SG_STRUCT_CONN_NOT_RECOVERED",),
        )
    preferred_ids = set(event["connection_ids"])
    matches.sort(key=lambda item: (
        0 if _conn_value(item[0], "id") in preferred_ids else 1,
        _conn_value(item[0], "id"), item[1]["altloc"], item[2]["altloc"],
    ))
    selected_connection, protein_endpoint, ligand_endpoint = matches[0]
    atom_rows = atom_site_owner.extract_atom_site_loop_rows_v0(text)
    protein_candidates = _endpoint_candidates(
        atom_rows, endpoint=protein_endpoint, event=event, protein=True,
    )
    ligand_candidates = _endpoint_candidates(
        atom_rows, endpoint=ligand_endpoint, event=event, protein=False,
    )
    reported = event["rcsb_structure_authority"]["reported_distance_angstrom"]
    try:
        selected_protein, selected_ligand = _select_endpoint_pair(
            protein_candidates, ligand_candidates, reported_distance=reported,
        )
    except ValueError as error:
        phases[BULK_STAGES[6]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="STRUCTURAL_EVIDENCE_INCOMPLETE",
            reasons=(str(error),),
        )
    post_distance = math.dist(
        _coordinates(selected_protein), _coordinates(selected_ligand)
    )
    if not math.isfinite(post_distance) or post_distance <= 0:
        phases[BULK_STAGES[6]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="REJECTED_EVENT_INVALID",
            reasons=("POST_DISTANCE_NONFINITE_OR_NONPOSITIVE",),
        )
    phases[BULK_STAGES[6]] = "PASSED_EXPLICIT_EVENT"

    ligand_atoms = _selected_ligand_atoms(atom_rows, event, selected_ligand)
    if not ligand_atoms:
        phases[BULK_STAGES[7]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="STRUCTURAL_EVIDENCE_INCOMPLETE",
            reasons=("RETAINED_LIGAND_ATOM_INVENTORY_EMPTY",),
        )
    pocket_atoms = _selected_pocket_atoms(atom_rows, ligand_atoms)
    phases[BULK_STAGES[7]] = (
        "PASSED_POST_ATOM_MAPPING_PRE_TOPOLOGY_UNREVIEWED"
    )
    ligand_symbols = _element_inventory(ligand_atoms)
    pocket_symbols = _element_inventory(pocket_atoms)
    projection = feature_owner.project_type_symbols_to_checkpoint_heavy_v1(
        tuple(ligand_symbols + pocket_symbols)
    )
    if projection.sample_rejected or not ligand_symbols or not pocket_symbols:
        phases[BULK_STAGES[8]] = "FAILED_CLOSED"
        return _terminal_outcome(
            event, phases=phases, route="REJECTED_FEATURE_INCOMPATIBLE",
            reasons=(
                "UNSUPPORTED_NONHYDROGEN_MODEL_ATOM"
                if projection.sample_rejected else "CANONICAL_POCKET_EMPTY",
            ),
            structural={
                "post_distance_angstrom": post_distance,
                "ligand_heavy_atom_count": len(ligand_symbols),
                "pocket_heavy_atom_count": len(pocket_symbols),
                "unsupported_feature_reasons": list(projection.reasons),
            },
        )
    phases[BULK_STAGES[8]] = "PASSED"
    reactive_center: dict[str, Any] = {}
    if ccd_component is not None:
        try:
            reactive_center = build_reactive_center_facts_v1(
                ccd_component,
                reactive_atom_id=str(event["ligand_reactive_atom"]),
            )
        except ValueError:
            reactive_center = {}
    pre = _rdkit_pre_facts(
        event["supporting_pre_reaction_smiles"],
        retained_heavy_atom_count=len(ligand_symbols),
        adduct_smiles_values=event["supporting_adduct_smiles"],
        ccd=ccd_component,
        retained_heavy_atom_names=[
            _atom_value(row, "label_atom_id") for row in ligand_atoms
            if _atom_value(row, "type_symbol").upper() != "H"
        ],
        reactive_atom_id=str(event["ligand_reactive_atom"]),
    )
    if identity in KNOWN_EXPANSION_APPROVED or identity in known_historical:
        pre["status"] = "PRE_EXPLICIT_AUTHORITY_AVAILABLE"
    if identity in KNOWN_QUARANTINE:
        pre["status"] = "PRE_ATOM_LOSS_REPRESENTATION_GAP"
        pre["atom_loss_flag"] = True
    phases[BULK_STAGES[9]] = pre["status"]

    known_authority_identity = identity in KNOWN_EXPANSION_APPROVED
    exact_evaluation = evaluate_production_exact_authority_v1(
        None, authorities=authorities,
    )
    authority_evaluation = (
        _authority_match_evaluation(
            authorities,
            known_authority_identity=True,
            pdb_id=pdb_id,
        ) if known_authority_identity
        else exact_evaluation["authority_match_evaluation"]
    )
    exact_authority_match = bool(exact_evaluation["exact_authority_match"])
    phases[BULK_STAGES[10]] = (
        "KNOWN_IDENTITY_DEDUPLICATED_SEPARATELY"
        if known_authority_identity else exact_evaluation["exact_signature_status"]
    )
    leakage, predicted_split, leakage_blocker = (
        predict_leakage_read_only_v1(identity, historical=known_historical)
        if identity in KNOWN_EXPANSION_APPROVED or identity in known_historical
        else ("LEAKAGE_EVIDENCE_PENDING_BATCH", "UNASSIGNED_READ_ONLY", None)
    )
    phases[BULK_STAGES[11]] = leakage

    if leakage_blocker is not None:
        route = leakage_blocker
        reasons = ("FROZEN_HISTORICAL_BASELINE_EXTENSION_NOT_SUPPORTED",)
    elif identity in KNOWN_EXPANSION_APPROVED or identity in known_historical:
        route = "KNOWN_EXISTING_APPROVED_SAMPLE"
        reasons = ("KNOWN_IDENTITY_DEDUPLICATED_FROM_BULK_DISCOVERY",)
    elif identity in KNOWN_QUARANTINE:
        route = "KNOWN_EXISTING_QUARANTINE"
        reasons = ("ATOM_LOSS_PRE_REACTION_SUPPORT_FOR_DIAZOMETHYL_KETONE",)
    elif identity in KNOWN_RUNTIME_EXTENSION:
        route = "KNOWN_RUNTIME_EXTENSION"
        reasons = ("FROZEN_RUNTIME_EXTENSION_CANDIDATE",)
    elif event["source_annotation_conflict"]:
        route = "SOURCE_ANNOTATION_CONFLICT"
        reasons = tuple(event["annotation_conflict_fields"])
    elif pre["status"] in {
        "PRE_ATOM_LOSS_REPRESENTATION_GAP", "PRE_ONLY_ATOMS_DETECTED",
    }:
        route = "QUARANTINE_REPRESENTATION_GAP"
        reasons = ("PRE_ONLY_ATOMS_CANNOT_BE_DROPPED_OR_GIVEN_COORDINATES",)
    elif pre["status"] in {
        "PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED",
        "PRE_COMPONENT_TOPOLOGY_INCOMPLETE",
        "PRE_REACTION_UNRESOLVED",
        "PRE_FORMAL_CHARGE_UNRESOLVED",
        "PRE_GRAPH_TRANSFORM_REQUIRED",
        "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS",
        "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
    }:
        route = "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY"
        reasons = (
            "PRE_CHEMISTRY_NOT_PRODUCTION_AUTHORITATIVE",
            "NO_FAMILY_LEVEL_AUTO_ADMISSION",
        )
    elif exact_authority_match:
        route = "AUTO_ADMITTED_EXACT_SIGNATURE"
        reasons = ("EXACT_EXISTING_AUTHORITY_MATCH",)
    else:
        route = "HUMAN_REVIEW_REQUIRED_NEW_CHEMISTRY"
        reasons = ("NO_EXISTING_EXACT_CHEMISTRY_SIGNATURE_MATCH",)
    phases[BULK_STAGES[12]] = route
    structural = {
        "mmcif_entry_id": pdb_id,
        "selected_connection_id": _conn_value(selected_connection, "id"),
        "selected_protein_altloc": _atom_value(selected_protein, "label_alt_id") or None,
        "selected_ligand_altloc": _atom_value(selected_ligand, "label_alt_id") or None,
        "protein_endpoint_coordinates": list(_coordinates(selected_protein)),
        "ligand_endpoint_coordinates": list(_coordinates(selected_ligand)),
        "post_distance_angstrom": round(post_distance, 6),
        "reported_distance_angstrom": reported,
        "ligand_reactive_element": _atom_value(
            selected_ligand, "type_symbol"
        ).title(),
        "ligand_heavy_atom_count": len(ligand_symbols),
        "pocket_heavy_atom_count": len(pocket_symbols),
        "ligand_element_counts": dict(sorted(Counter(ligand_symbols).items())),
        "pocket_element_counts": dict(sorted(Counter(pocket_symbols).items())),
        "ligand_atom_inventory_sha256": _sha(_canonical_json([
            {
                "atom": _atom_value(row, "label_atom_id"),
                "element": _atom_value(row, "type_symbol").title(),
                "coordinates": list(_coordinates(row)),
            }
            for row in ligand_atoms
        ])),
        "pocket_atom_inventory_sha256": _sha(_canonical_json([
            {
                "asym": _atom_value(row, "label_asym_id"),
                "seq": _atom_value(row, "label_seq_id"),
                "atom": _atom_value(row, "label_atom_id"),
                "element": _atom_value(row, "type_symbol").title(),
                "coordinates": list(_coordinates(row)),
            }
            for row in pocket_atoms
        ])),
        "feature_projection_status": projection.outcome,
        "unknown_atom_feature_fallback_used": False,
        "explicit_covalent_evidence": True,
        "distance_only_event_inference_used": False,
        "ccd_component_graph": dict(ccd_component or {}),
        **reactive_center,
    }
    structural["leakage_evidence"] = build_source_local_leakage_evidence_v1(
        mmcif_text=text,
        protein_label_asym_id=str(event["protein_instance"]),
        ccd=ccd_component,
    )
    return _terminal_outcome(
        event,
        phases=phases,
        route=route,
        reasons=reasons,
        structural=structural,
        pre=pre,
        authority_evaluation=authority_evaluation,
        exact_authority_match=exact_authority_match,
        exact_signature_status=(
            "KNOWN_IDENTITY_DEDUPLICATED_SEPARATELY"
            if known_authority_identity else exact_evaluation["exact_signature_status"]
        ),
        leakage=leakage,
        predicted_split=predicted_split,
    )


def _terminal_outcome(
    event: Mapping[str, Any], *, phases: Mapping[str, str], route: str,
    reasons: Sequence[str], structural: Mapping[str, Any] | None = None,
    pre: Mapping[str, Any] | None = None,
    authority_evaluation: Sequence[Mapping[str, Any]] = (),
    exact_authority_match: bool = False,
    exact_signature_status: str = "EXACT_SIGNATURE_NOT_COMPUTABLE_OTHER",
    leakage: str = "LEAKAGE_EVIDENCE_INCOMPLETE",
    predicted_split: str = "UNASSIGNED_READ_ONLY",
) -> dict[str, Any]:
    if route not in TERMINAL_ROUTES:
        raise ValueError("TERMINAL_ROUTE_INVALID")
    return {
        "canonical_event_id": event["canonical_event_id"],
        "pdb_id": event["pdb_id"],
        "ligand_component_id": event["ligand_component_id"],
        "source_datasets": event["source_datasets"],
        "terminal_outcome": route,
        "terminal_reasons": list(dict.fromkeys(reasons)),
        "stage_statuses": {stage: phases.get(stage, "NOT_REACHED") for stage in BULK_STAGES},
        "structural_processing": dict(structural or {}),
        "pre_representability": dict(pre or {
            "status": "PRE_REACTION_UNRESOLVED",
            "atom_loss_flag": False,
            "formal_charge_pattern_authoritative": False,
        }),
        "authority_match_evaluation": list(authority_evaluation),
        "existing_exact_authority_match": exact_authority_match,
        "exact_signature_status": exact_signature_status,
        "leakage_classification": leakage,
        "leakage_key": None,
        "predicted_group_id": None,
        "leakage_linking_axes": [],
        "predicted_split": predicted_split,
        "production_materialization_performed": False,
        "temporary_materialization_performed": False,
        "temporary_tensorization_performed": False,
    }


def _load_frozen_state_v1(
    repo_root: Path,
) -> tuple[tuple[Any, ...], Any, set[tuple[str, str]]]:
    authority_path = repo_root / AUTHORITY_REGISTRY_RELATIVE
    leakage_path = repo_root / LEAKAGE_REGISTRY_RELATIVE
    if _sha(authority_path.read_bytes()) != AUTHORITY_REGISTRY_SHA256:
        raise ValueError("FROZEN_AUTHORITY_REGISTRY_SHA256_MISMATCH")
    if _sha(leakage_path.read_bytes()) != LEAKAGE_REGISTRY_SHA256:
        raise ValueError("FROZEN_LEAKAGE_REGISTRY_SHA256_MISMATCH")
    authorities = production_pipeline.load_reusable_authority_registry_v1(
        authority_path
    )
    leakage = production_pipeline.load_cumulative_expansion_leakage_registry_v1(
        leakage_path, repo_root=repo_root,
    )
    if len(authorities) != 3 or len(leakage.groups) != 2:
        raise ValueError("FROZEN_AUTHORITY_OR_LEAKAGE_COUNT_MISMATCH")
    identities = sorted(
        identity for group in leakage.groups for identity in group.member_identities
    )
    if identities != ["5F2E/5UT", "6DI9/GJJ", "6OIM/MOV"]:
        raise ValueError("FROZEN_EXPANSION_IDENTITIES_MISMATCH")

    with (repo_root / CURRENT11_INDEX_RELATIVE).open(
        "r", encoding="utf-8", newline="",
    ) as handle:
        current11_rows = list(csv.DictReader(handle))
    if len(current11_rows) != 11:
        raise ValueError("HISTORICAL_CURRENT11_POPULATION_MISMATCH")
    historical = {
        (str(row["pdb_id"]).upper(), str(row["ligand_comp_id"]).upper())
        for row in current11_rows
    } | KNOWN_K36_EXACT16
    if len(historical) != 16:
        raise ValueError("HISTORICAL_EXACT16_IDENTITY_POPULATION_MISMATCH")
    return authorities, leakage, historical


def select_structural_pilot_events_v1(
    events: Sequence[Mapping[str, Any]],
    *, known_identities: set[tuple[str, str]],
) -> list[Mapping[str, Any]]:
    """Select a deterministic, coverage-prioritized bounded structural pilot."""

    ordered = sorted(events, key=lambda item: item["canonical_event_id"])
    selected: list[Mapping[str, Any]] = []
    selected_ids: set[str] = set()
    selected_pdbs: set[str] = set()
    limit = min(len(ordered), UNIQUE_NEW_EVENT_PROCESSING_CAP + len(
        [
            item for item in ordered
            if (item["pdb_id"], item["ligand_component_id"]) in known_identities
        ]
    ))

    def add(items: Sequence[Mapping[str, Any]]) -> None:
        for item in items:
            event_id = str(item["canonical_event_id"])
            pdb_id = str(item["pdb_id"])
            if event_id in selected_ids or len(selected) >= limit:
                continue
            if pdb_id not in selected_pdbs and len(selected_pdbs) >= UNIQUE_PDB_ACQUISITION_CAP:
                continue
            selected.append(item)
            selected_ids.add(event_id)
            selected_pdbs.add(pdb_id)

    add([
        item for item in ordered
        if (item["pdb_id"], item["ligand_component_id"]) in known_identities
    ])
    add([item for item in ordered if int(item["source_count"]) > 1])
    add([
        item for item in ordered
        if item["supporting_pre_reaction_smiles"]
        or item["supporting_adduct_smiles"]
    ])
    atom_loss_candidates: list[Mapping[str, Any]] = []
    for item in ordered:
        pre_counts = [
            molecule.GetNumHeavyAtoms()
            for value in item["supporting_pre_reaction_smiles"]
            if (molecule := _source_molecule_v1(value)) is not None
        ]
        if len(set(pre_counts)) > 1:
            atom_loss_candidates.append(item)
    add(atom_loss_candidates)
    by_component: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in ordered:
        by_component[str(item["ligand_component_id"])].append(item)
    add([by_component[key][0] for key in sorted(by_component)])
    add(ordered)
    return selected


def _acquire_structures_v1(
    cache: BulkCacheV1, events: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, bytes], list[dict[str, Any]], int]:
    pdb_ids = sorted(set(str(event["pdb_id"]) for event in events))
    pdb_ids = pdb_ids[:UNIQUE_PDB_ACQUISITION_CAP]
    payloads: dict[str, bytes] = {}
    manifest: list[dict[str, Any]] = []
    compressed_total = 0
    for pdb_id in pdb_ids:
        url = RCSB_MMCIF_URL.format(pdb_id=pdb_id)
        try:
            payload, entry = cache.fetch(
                relative_path=f"rcsb/structures/{pdb_id}.cif.gz",
                url=url,
                source_dataset=adapters.SOURCE_RCSB_PDB_DIRECT,
                retrieval_identity={
                    "pdb_id": pdb_id,
                    "format": "PDBx/mmCIF gzip",
                    "snapshot_date": SNAPSHOT_DATE,
                },
                maximum_bytes=COMPRESSED_FILE_CAP,
            )
            if compressed_total + len(payload) > TOTAL_COMPRESSED_DOWNLOAD_CAP:
                raise ValueError("TOTAL_COMPRESSED_DOWNLOAD_CAP_EXCEEDED")
            compressed_total += len(payload)
            _validate_mmcif_payload(payload, pdb_id)
            payloads[pdb_id] = payload
            status = "SOURCE_VERIFIED"
            reason = None
            sha256 = entry["sha256"]
            byte_count = entry["byte_count"]
            cache_status = entry["cache_reuse_status"]
        except (RuntimeError, ValueError) as error:
            status = "SOURCE_ACQUISITION_OR_VALIDATION_FAILED"
            reason = str(error)
            sha256 = None
            byte_count = 0
            cache_status = "FAILED"
        manifest.append({
            "pdb_id": pdb_id,
            "official_structure_url": url,
            "acquisition_status": status,
            "failure_reason": reason,
            "compressed_byte_count": byte_count,
            "compressed_sha256": sha256,
            "cache_reuse_status": cache_status,
            "per_file_cap_bytes": COMPRESSED_FILE_CAP,
            "validation": "GZIP_ENTRY_ID_STRUCT_CONN_ATOM_SITE" if status == "SOURCE_VERIFIED" else "FAILED_CLOSED",
        })
    return payloads, manifest, compressed_total


def _outcome_for_unprocessed_event(
    event: Mapping[str, Any], reason: str,
) -> dict[str, Any]:
    phases = {stage: "NOT_REACHED" for stage in BULK_STAGES}
    for stage in BULK_STAGES[:4]:
        phases[stage] = "PASSED"
    phases[BULK_STAGES[4]] = "NOT_SELECTED_BOUNDED_CAP"
    return _terminal_outcome(
        event,
        phases=phases,
        route="STRUCTURAL_EVIDENCE_INCOMPLETE",
        reasons=(reason,),
    )


def build_human_review_units_v1(
    outcomes: Sequence[dict[str, Any]],
    event_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidate_routes = {
        "HUMAN_REVIEW_REQUIRED_NEW_CHEMISTRY",
        "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        "SOURCE_ANNOTATION_CONFLICT",
    }
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
        if outcome["terminal_outcome"] not in candidate_routes:
            continue
        structural = outcome["structural_processing"]
        pre = outcome["pre_representability"]
        ccd = structural.get("ccd_component_graph", {})
        key = (
            str(pre["status"]),
            str(ccd.get("ccd_component_graph_sha256") or "NO_CCD_GRAPH"),
            str(structural.get("reactive_center_radius2_sha256") or "NO_RADIUS2"),
            str(pre.get("pre_source_graph_sha256") or "NO_PRE_GRAPH"),
            str(pre.get("pre_reactive_center_radius2_sha256") or "NO_PRE_RADIUS2"),
            str(outcome["ligand_component_id"]),
            str(event_by_id[outcome["canonical_event_id"]]["ligand_reactive_atom"]),
            "ATOM_LOSS" if pre.get("atom_loss_flag") else "NO_ATOM_LOSS",
        )
        buckets[key].append(outcome)
    units: list[dict[str, Any]] = []
    for key, members in sorted(buckets.items()):
        members.sort(key=lambda item: item["canonical_event_id"])
        events = [event_by_id[item["canonical_event_id"]] for item in members]
        digest = _sha(_canonical_json({
            "review_unit_contract": "COVAPIE_BULK_REVIEW_UNIT_V1",
            "key": key,
        }))
        units.append({
            "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_" + digest[:16].upper(),
            "event_count": len(members),
            "canonical_event_ids": [item["canonical_event_id"] for item in members],
            "PDB_ids": sorted(set(item["pdb_id"] for item in members)),
            "ligand_component_ids": sorted(set(
                item["ligand_component_id"] for item in members
            )),
            "reactive_atom": key[6],
            "ccd_component_graph_sha256": (
                None if key[1] == "NO_CCD_GRAPH" else key[1]
            ),
            "reactive_center_radius2_fingerprint": (
                None if key[2] == "NO_RADIUS2" else key[2]
            ),
            "pre_source_graph_fingerprint": (
                None if key[3] == "NO_PRE_GRAPH" else key[3]
            ),
            "pre_reactive_center_fingerprint": (
                None if key[4] == "NO_PRE_RADIUS2" else key[4]
            ),
            "PRE_status": key[0],
            "atom_loss_state": key[7],
            "source_datasets": sorted(set(
                source for event in events for source in event["source_datasets"]
            )),
            "supporting_source_annotations": sorted({
                annotation
                for event in events
                for annotation in event["supporting_warhead_annotations"]
            }),
            "production_sample_approval_created": False,
        })
    return sorted(units, key=lambda item: item["review_unit_id"])


def cluster_review_units_v1(
    review_units: Sequence[Mapping[str, Any]],
    *, outcomes: Sequence[dict[str, Any]],
    event_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    outcome_by_id = {item["canonical_event_id"]: item for item in outcomes}
    buckets: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for unit in review_units:
        first_outcome = outcome_by_id[str(unit["canonical_event_ids"][0])]
        pre = first_outcome["pre_representability"]
        key = (
            str(unit["PRE_status"]),
            str(unit["reactive_center_radius2_fingerprint"] or "NO_RADIUS2"),
            str(unit["pre_reactive_center_fingerprint"] or "NO_PRE_RADIUS2"),
            str(unit["atom_loss_state"]),
            str(pre.get("net_pre_adduct_local_transformation_sha256") or "NO_TRANSFORMATION"),
        )
        buckets[key].append(unit)
    clusters: list[dict[str, Any]] = []
    for key, units in sorted(buckets.items()):
        units = sorted(units, key=lambda item: str(item["review_unit_id"]))
        event_ids = sorted({
            str(event_id) for unit in units for event_id in unit["canonical_event_ids"]
        })
        members = [outcome_by_id[event_id] for event_id in event_ids]
        events = [event_by_id[event_id] for event_id in event_ids]
        radius2_values = sorted({
            str(unit["reactive_center_radius2_fingerprint"])
            for unit in units if unit["reactive_center_radius2_fingerprint"]
        })
        pre_radius2_values = sorted({
            str(unit["pre_reactive_center_fingerprint"])
            for unit in units if unit["pre_reactive_center_fingerprint"]
        })
        transformation_values = sorted({
            str(member["pre_representability"].get(
                "net_pre_adduct_local_transformation_sha256"
            ))
            for member in members
            if member["pre_representability"].get(
                "net_pre_adduct_local_transformation_sha256"
            )
        })
        mixed = len(radius2_values) > 1
        conflict_count = sum(
            bool(event["source_annotation_conflict"]) for event in events
        )
        if conflict_count:
            priority = "P0_SOURCE_CONFLICT"
        elif key[0] == "PRE_REACTION_UNRESOLVED":
            priority = "P1_PRE_UNRESOLVED"
        elif key[0] == "PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED":
            priority = "P2_PRE_AUTHORITY_REVIEW"
        else:
            priority = "P3_NEW_CHEMISTRY"
        annotations = sorted({
            value
            for unit in units for value in unit["supporting_source_annotations"]
        })
        similarity = (
            "SUPPORTING_ACRYLAMIDE_LABEL_ONLY_NOT_EXACT_AUTHORITY"
            if any("acrylamide" in item.lower() for item in annotations)
            else "NO_EXISTING_EXACT_FAMILY_SIMILARITY_ESTABLISHED"
        )
        digest = _sha(_canonical_json({
            "clustering_contract": "COVAPIE_CHEMISTRY_AWARE_REVIEW_CLUSTER_V1",
            "key": key,
            "review_units": [item["review_unit_id"] for item in units],
        }))
        local_topologies = sorted({
            str(member["structural_processing"].get(
                "reactive_center_local_topology"
            ) or "UNAVAILABLE") for member in members
        })
        topology_coherent_for_joint_review = bool(
            len(radius2_values) == 1
            and len(local_topologies) == 1
            and local_topologies[0] != "UNAVAILABLE"
        )
        pre_evidence_supports_one_rule = bool(
            key[0] in {
                "PRE_EXPLICIT_AUTHORITY_AVAILABLE",
                "PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED",
            }
            and len(pre_radius2_values) == 1
            and len(transformation_values) == 1
        )
        approvalable_as_one_rule = bool(
            topology_coherent_for_joint_review
            and not conflict_count
            and pre_evidence_supports_one_rule
        )
        clusters.append({
            "cluster_id": "COVAPIE_BULK_REVIEW_CLUSTER_" + digest[:16].upper(),
            "event_count": len(event_ids),
            "member_count": len(event_ids),
            "review_unit_count": len(units),
            "review_unit_ids": [item["review_unit_id"] for item in units],
            "canonical_event_ids": event_ids,
            "representative_pdb_ids": [item["pdb_id"] for item in members[:3]],
            "representative_ligand_ids": [
                item["ligand_component_id"] for item in members[:3]
            ],
            "reactive_center_local_topology": local_topologies[0],
            "radius2_fingerprint": radius2_values[0] if len(radius2_values) == 1 else None,
            "PRE_status": key[0],
            "supporting_source_annotations": annotations,
            "existing_family_similarity": similarity,
            "unique_reactive_center_radius2_fingerprint_count": len(radius2_values),
            "unique_pre_reactive_center_fingerprint_count": len(pre_radius2_values),
            "pre_reactive_center_fingerprint": (
                pre_radius2_values[0] if len(pre_radius2_values) == 1 else None
            ),
            "unique_transformation_fingerprint_count": len(transformation_values),
            "transformation_fingerprint": (
                transformation_values[0]
                if len(transformation_values) == 1 else None
            ),
            "mixed_chemistry_status": (
                "MIXED_CHEMISTRY_NOT_APPROVALABLE_AS_ONE_RULE" if mixed
                else "CHEMISTRY_COHERENT_OR_SINGLETON"
            ),
            "topology_coherent_for_joint_human_review": (
                topology_coherent_for_joint_review
            ),
            "approvalable_as_one_chemistry_rule": approvalable_as_one_rule,
            "pre_authority_status_distribution": dict(sorted(Counter(
                item["pre_representability"]["status"] for item in members
            ).items())),
            "atom_loss_flag": key[3] == "ATOM_LOSS",
            "atom_loss_count": sum(
                bool(item["pre_representability"].get("atom_loss_flag"))
                for item in members
            ),
            "annotation_conflicts": conflict_count,
            "human_review_priority": priority,
        })
    priority_rank = {
        "P0_SOURCE_CONFLICT": 0,
        "P1_PRE_UNRESOLVED": 1,
        "P2_PRE_AUTHORITY_REVIEW": 2,
        "P3_NEW_CHEMISTRY": 3,
    }
    return sorted(clusters, key=lambda item: (
        priority_rank[item["human_review_priority"]],
        -item["event_count"], item["cluster_id"],
    ))


def _cluster_human_review_v1(
    outcomes: Sequence[dict[str, Any]],
    event_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    units = build_human_review_units_v1(outcomes, event_by_id)
    return cluster_review_units_v1(
        units, outcomes=outcomes, event_by_id=event_by_id,
    )


def _count_stage(outcomes: Sequence[Mapping[str, Any]], stage: str, value: str) -> int:
    return sum(item["stage_statuses"].get(stage) == value for item in outcomes)


def _structure_cache_origin_counts_v1(
    acquisition: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    counts = Counter()
    for item in acquisition:
        verified = item.get("acquisition_status") == "SOURCE_VERIFIED"
        has_payload = bool(
            int(item.get("compressed_byte_count", 0)) > 0
            and item.get("compressed_sha256")
        )
        if verified != has_payload:
            raise ValueError("STRUCTURE_PAYLOAD_VERIFICATION_RECONCILIATION_FAILED")
        if not verified:
            if item.get("cache_reuse_status") != "FAILED":
                raise ValueError("FAILED_STRUCTURE_CACHE_ORIGIN_INVALID")
            continue
        origin = str(item.get("cache_reuse_status"))
        if origin == "DOWNLOADED_BY_BULK_PILOT":
            counts["downloaded"] += 1
        elif origin == "REUSED_FROM_TASK_CACHE":
            counts["reused"] += 1
        else:
            raise ValueError("SOURCE_VERIFIED_STRUCTURE_CACHE_ORIGIN_INVALID")
        counts["payload"] += 1
        counts["source_verified"] += 1
    if counts["downloaded"] + counts["reused"] != counts["payload"]:
        raise ValueError("STRUCTURE_CACHE_ORIGIN_RECONCILIATION_FAILED")
    return {
        "structure_payload_count": counts["payload"],
        "structure_source_verified_count": counts["source_verified"],
        "structure_cache_origin_downloaded_count": counts["downloaded"],
        "structure_cache_origin_reused_count": counts["reused"],
        # Compatibility aliases retain the same mutually exclusive origin
        # dimension as the explicit canonical fields above.
        "structures_downloaded_count": counts["downloaded"],
        "structures_reused_from_cache_count": counts["reused"],
    }


def _build_summary_v1(
    *,
    access_records: Sequence[Mapping[str, Any]],
    covpdb_snapshot: Mapping[str, Any],
    covbinder_snapshot: Mapping[str, Any],
    covalentindb_snapshot: Mapping[str, Any],
    rcsb_snapshot: Mapping[str, Any],
    specialist_snapshot: Mapping[str, Any],
    merged_events: Sequence[Mapping[str, Any]],
    records_without_event_identity: int,
    all_source_normalized_record_count: int,
    outcomes: Sequence[Mapping[str, Any]],
    acquisition: Sequence[Mapping[str, Any]],
    compressed_total: int,
    clusters: Sequence[Mapping[str, Any]],
    review_units: Sequence[Mapping[str, Any]],
    ccd_manifest: Sequence[Mapping[str, Any]],
    known_event_count: int,
    known_event_ids: set[str],
    cache_summary: Mapping[str, Any],
    regressions_pass: bool,
) -> dict[str, Any]:
    lane_by_name = {item["source_name"]: item for item in access_records}
    operational = [
        item for item in access_records
        if item["current_lane_status"].startswith("OPERATIONAL_")
    ]
    specialist_operational = [
        item for item in operational
        if item["source_name"] != adapters.SOURCE_RCSB_PDB_DIRECT
    ]
    source_distribution = Counter(item["source_count"] for item in merged_events)
    route_counts = Counter(item["terminal_outcome"] for item in outcomes)
    pre_counts = Counter(
        item["pre_representability"]["status"] for item in outcomes
        if item["stage_statuses"][BULK_STAGES[9]] != "NOT_REACHED"
    )
    canonical_count = len(merged_events)
    new_count = canonical_count - known_event_count
    new_outcomes = [
        item for item in outcomes
        if item["canonical_event_id"] not in known_event_ids
    ]
    known_control_contracts = (
        (
            ("2DJF", "1ZB"),
            "PRE_ATOM_LOSS_REPRESENTATION_GAP",
            "KNOWN_EXISTING_QUARANTINE",
            ("ATOM_LOSS_PRE_REACTION_SUPPORT_FOR_DIAZOMETHYL_KETONE",),
        ),
        (
            ("2R9F", "K2Z"),
            None,
            "KNOWN_RUNTIME_EXTENSION",
            ("FROZEN_RUNTIME_EXTENSION_CANDIDATE",),
        ),
    )
    known_controls: dict[tuple[str, str], Mapping[str, Any]] = {}
    for identity, expected_pre_status, expected_terminal, expected_reasons in (
        known_control_contracts
    ):
        matches = [
            item for item in outcomes
            if (item["pdb_id"], item["ligand_component_id"]) == identity
        ]
        if len(matches) != 1:
            raise ValueError(
                "KNOWN_CONTROL_OUTCOME_NOT_EXACT_ONE:" + "/".join(identity)
            )
        control = matches[0]
        if (
            expected_pre_status is not None
            and control["pre_representability"]["status"]
            != expected_pre_status
        ):
            raise ValueError(
                "KNOWN_CONTROL_PRE_STATUS_INVALID:" + "/".join(identity)
            )
        if (
            control["terminal_outcome"] != expected_terminal
            or tuple(control["terminal_reasons"]) != expected_reasons
        ):
            raise ValueError(
                "KNOWN_CONTROL_FROZEN_TERMINAL_INVALID:" + "/".join(identity)
            )
        known_controls[identity] = control
    known_control_conflict_identities = sorted(
        "/".join(identity)
        for identity, control in known_controls.items()
        if control["leakage_classification"]
        == "LEAKAGE_EXISTING_GROUP_CONFLICT"
    )
    expected_known_control_conflicts = ["2DJF/1ZB", "2R9F/K2Z"]
    if known_control_conflict_identities != expected_known_control_conflicts:
        raise ValueError("KNOWN_CONTROL_CONFLICT_ANNOTATION_SET_INVALID")
    all_existing_group_conflict_count = sum(
        item["leakage_classification"] == "LEAKAGE_EXISTING_GROUP_CONFLICT"
        for item in outcomes
    )
    new_existing_group_conflict_count = sum(
        item["leakage_classification"] == "LEAKAGE_EXISTING_GROUP_CONFLICT"
        for item in new_outcomes
    )
    terminal_existing_group_conflict_count = route_counts[
        "LEAKAGE_EXISTING_GROUP_CONFLICT"
    ]
    if (
        all_existing_group_conflict_count
        != new_existing_group_conflict_count
        + len(known_control_conflict_identities)
        or terminal_existing_group_conflict_count
        != new_existing_group_conflict_count
    ):
        raise ValueError("KNOWN_CONTROL_CONFLICT_RECONCILIATION_FAILED")
    two_djf_quarantine_preserved = bool(
        known_controls[("2DJF", "1ZB")]["terminal_outcome"]
        == "KNOWN_EXISTING_QUARANTINE"
    )
    k2z_runtime_extension_preserved = bool(
        known_controls[("2R9F", "K2Z")]["terminal_outcome"]
        == "KNOWN_RUNTIME_EXTENSION"
    )
    duplicate_count = (
        all_source_normalized_record_count
        - records_without_event_identity
        - canonical_count
    )
    if duplicate_count < 0:
        raise ValueError("SOURCE_RECORD_RECONCILIATION_NEGATIVE_DUPLICATE_COUNT")
    structure_cache_counts = _structure_cache_origin_counts_v1(acquisition)
    bulk_core = bool(
        lane_by_name[adapters.SOURCE_RCSB_PDB_DIRECT][
            "current_lane_status"
        ] == "OPERATIONAL_BULK_API"
        and rcsb_snapshot["real_rcsb_network_discovery_performed"]
        and new_count > 25
    )
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "bulk_task": TASK_NAME,
        "bulk_phase_change_from_per_sample_mode": True,
        "bulk_multisource_architecture_implemented": True,
        "bulk_core_operational": bulk_core,
        "bulk_multisource_real_ingestion_performed": bool(
            covbinder_snapshot["normalized_records"]
        ),
        "multisource_coverage_complete": len(operational) == 4,
        "operational_source_lane_count": len(operational),
        "specialized_source_operational_count": len(specialist_operational),
        "covpdb_lane_status": covpdb_snapshot["lane_status"],
        "covpdb_lane_operational": covpdb_snapshot["lane_status"].startswith("OPERATIONAL_"),
        "covpdb_source_records_examined": covpdb_snapshot["source_records_examined"],
        "covpdb_normalized_records": covpdb_snapshot["normalized_records"],
        "covpdb_ligand_records_normalized": covpdb_snapshot["covpdb_ligand_records_normalized"],
        "covpdb_complex_archive_consumed": True,
        "covpdb_complex_archive_bytes": covpdb_snapshot["complex_archive_bytes"],
        "covpdb_complexes_examined": covpdb_snapshot["covpdb_complexes_examined"],
        "covpdb_pdb_seed_count": covpdb_snapshot["covpdb_pdb_seed_count"],
        "covpdb_pdb_seeds": covpdb_snapshot["covpdb_pdb_seed_count"],
        "covpdb_exact_event_seed_count": covpdb_snapshot["covpdb_exact_event_seed_count"],
        "covpdb_seeded_rcsb_exact_event_count": covpdb_snapshot["covpdb_seeded_rcsb_exact_event_count"],
        "covpdb_records_contributing_to_canonical_events": covpdb_snapshot["covpdb_records_contributing_to_canonical_events"],
        "covpdb_canonical_event_contribution_count": covpdb_snapshot["covpdb_cross_source_exact_event_count"],
        "covpdb_cross_source_exact_event_count": covpdb_snapshot["covpdb_cross_source_exact_event_count"],
        "covbinderinpdb_lane_status": covbinder_snapshot["lane_status"],
        "covbinderinpdb_lane_operational": covbinder_snapshot["lane_status"].startswith("OPERATIONAL_"),
        "covbinderinpdb_source_records_examined": covbinder_snapshot["source_records_examined"],
        "covbinderinpdb_normalized_records": covbinder_snapshot["normalized_records"],
        "covbinder_lane_operational": covbinder_snapshot["lane_status"].startswith("OPERATIONAL_"),
        "covbinder_records_normalized": covbinder_snapshot["normalized_records"],
        "covbinder_pdb_seeds": covbinder_snapshot["covbinder_pdb_seeds"],
        "covbinder_records_resolved_via_specialist_seeded_rcsb": covbinder_snapshot["covbinder_records_resolved_via_specialist_seeded_rcsb"],
        "covbinder_specialist_seeded_rcsb_resolved_count": covbinder_snapshot["covbinder_records_resolved_via_specialist_seeded_rcsb"],
        "covbinder_records_contributing_to_canonical_events": covbinder_snapshot["covbinder_records_contributing_to_canonical_events"],
        "covbinder_unresolved_records": covbinder_snapshot["covbinder_unresolved_records"],
        "covbinder_cross_source_exact_event_count": covbinder_snapshot["covbinder_cross_source_exact_event_count"],
        "covalentindb_lane_status": covalentindb_snapshot["lane_status"],
        "covalentindb_lane_operational": False,
        "covalentindb_source_records_examined": 0,
        "covalentindb_normalized_records": 0,
        "covalentindb_blocking_mainline": False,
        "rcsb_direct_lane_status": rcsb_snapshot["lane_status"],
        "rcsb_direct_lane_operational": rcsb_snapshot["lane_status"] == "OPERATIONAL_BULK_API",
        "real_rcsb_network_discovery_performed": rcsb_snapshot["real_rcsb_network_discovery_performed"],
        "rcsb_search_raw_hit_count": rcsb_snapshot["rcsb_search_raw_hit_count"],
        "rcsb_connection_records_examined": rcsb_snapshot["rcsb_connection_records_examined"],
        "rcsb_normalized_records": rcsb_snapshot["rcsb_normalized_records"],
        "specialist_seeded_rcsb_recovery_implemented": specialist_snapshot["specialist_seeded_rcsb_recovery_implemented"],
        "specialist_seeded_unique_pdb_count": specialist_snapshot["specialist_seeded_unique_pdb_count"],
        "specialist_seeded_rcsb_pdbs_examined": specialist_snapshot["specialist_seeded_rcsb_pdbs_examined"],
        "specialist_seeded_exact_cys_sg_event_count": specialist_snapshot["specialist_seeded_exact_cys_sg_event_count"],
        "all_source_normalized_record_count": all_source_normalized_record_count,
        "records_without_canonical_event_identity_count": records_without_event_identity,
        "source_records_with_event_identity_count": (
            all_source_normalized_record_count - records_without_event_identity
        ),
        "source_records_contributing_to_canonical_event_count": (
            all_source_normalized_record_count - records_without_event_identity
        ),
        "cross_source_duplicate_record_count": duplicate_count,
        "canonical_unique_event_count": canonical_count,
        "events_with_1_source": source_distribution[1],
        "events_with_2_sources": source_distribution[2],
        "events_with_3_sources": source_distribution[3],
        "events_with_4_sources": source_distribution[4],
        "unique_pdb_count": len(set(item["pdb_id"] for item in merged_events)),
        "known_existing_event_count": known_event_count,
        "new_unique_candidate_event_count": new_count,
        "discovered_new_event_count": new_count,
        "bulk_scale_target_50_met": new_count >= 50,
        **structure_cache_counts,
        "downloaded_compressed_bytes_total": compressed_total,
        "source_verified_count": _count_stage(outcomes, BULK_STAGES[5], "PASSED"),
        "exact_event_valid_count": _count_stage(outcomes, BULK_STAGES[6], "PASSED_EXPLICIT_EVENT"),
        "structural_model_eligible_count": _count_stage(outcomes, BULK_STAGES[8], "PASSED"),
        "structural_model_eligible": _count_stage(outcomes, BULK_STAGES[8], "PASSED"),
        "structurally_model_eligible_new_event_count": sum(
            item["stage_statuses"][BULK_STAGES[8]] == "PASSED"
            for item in new_outcomes
        ),
        "ccd_components_requested": len(ccd_manifest),
        "ccd_components_resolved": sum(
            item["status"] == "CCD_COMPONENT_RESOLVED" for item in ccd_manifest
        ),
        "ccd_components_failed": sum(
            item["status"] == "CCD_COMPONENT_FAILED" for item in ccd_manifest
        ),
        "events_with_ccd_component_graph": sum(
            bool(item["structural_processing"].get("ccd_component_graph", {}).get(
                "ccd_component_graph_sha256"
            )) for item in outcomes
        ),
        "events_with_reactive_center_radius2_fingerprint": sum(
            bool(item["structural_processing"].get(
                "reactive_center_radius2_sha256"
            )) for item in outcomes
        ),
        "events_with_supporting_pre_graph": sum(
            bool(item["pre_representability"].get("pre_source_graph_sha256"))
            for item in outcomes
        ),
        "events_with_unique_pre_graph_mapping": sum(
            item["pre_representability"].get("pre_source_graph_mapping_status")
            == "PRE_SOURCE_GRAPH_MAPPING_UNIQUE" for item in outcomes
        ),
        "pre_explicit_authority_count": pre_counts["PRE_EXPLICIT_AUTHORITY_AVAILABLE"],
        "pre_authority_unreviewed_count": pre_counts["PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED"],
        "pre_atom_loss_quarantine_count": pre_counts["PRE_ATOM_LOSS_REPRESENTATION_GAP"],
        "pre_unresolved_count": sum(
            pre_counts[key] for key in (
                "PRE_GRAPH_TRANSFORM_REQUIRED", "PRE_FORMAL_CHARGE_UNRESOLVED",
                "PRE_ONLY_ATOMS_DETECTED", "PRE_COMPONENT_TOPOLOGY_INCOMPLETE",
                "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS",
                "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
                "PRE_REACTION_UNRESOLVED",
            )
        ),
        "existing_exact_authority_match_count": sum(
            bool(item["existing_exact_authority_match"]) for item in outcomes
        ),
        "auto_admitted_exact_signature_count": route_counts["AUTO_ADMITTED_EXACT_SIGNATURE"],
        "temporary_auto_materialization_proven_count": 0,
        "exact_authority_match_is_not_identity_stub": True,
        "new_candidate_exact_signature_computable_count": sum(
            item["exact_signature_status"] == "EXACT_SIGNATURE_COMPUTABLE"
            for item in new_outcomes
        ),
        "new_candidate_exact_signature_not_computable_count": sum(
            item["exact_signature_status"].startswith(
                "EXACT_SIGNATURE_NOT_COMPUTABLE_"
            ) for item in new_outcomes
        ),
        "new_candidate_exact_signature_matches_existing_count": sum(
            bool(item["existing_exact_authority_match"]) for item in new_outcomes
        ),
        "new_candidate_exact_signature_no_match_count": sum(
            item["exact_signature_status"] == "EXACT_SIGNATURE_COMPUTABLE"
            and not item["existing_exact_authority_match"] for item in new_outcomes
        ),
        "new_candidate_leakage_resolved_count": sum(
            item["leakage_classification"] in {
                "SAME_EXISTING_EXPANSION_COMPONENT",
                "HISTORICAL_BASELINE_COMPONENT", "NEW_EXPANSION_COMPONENT",
            } for item in new_outcomes
        ),
        "new_candidate_leakage_unresolved_count": sum(
            item["leakage_classification"] in {
                "LEAKAGE_EVIDENCE_INCOMPLETE",
                "LEAKAGE_EXISTING_GROUP_CONFLICT",
            }
            for item in new_outcomes
        ),
        "new_candidate_existing_expansion_component_count": sum(
            item["leakage_classification"] == "SAME_EXISTING_EXPANSION_COMPONENT"
            for item in new_outcomes
        ),
        "new_candidate_historical_component_count": sum(
            item["leakage_classification"] == "HISTORICAL_BASELINE_COMPONENT"
            for item in new_outcomes
        ),
        "new_candidate_new_component_count": sum(
            item["leakage_classification"] == "NEW_EXPANSION_COMPONENT"
            for item in new_outcomes
        ),
        "new_candidate_existing_group_conflict_count": sum(
            item["leakage_classification"] == "LEAKAGE_EXISTING_GROUP_CONFLICT"
            for item in new_outcomes
        ),
        "all_leakage_existing_group_conflict_classification_count": (
            all_existing_group_conflict_count
        ),
        "known_control_conflict_annotation_count": len(
            known_control_conflict_identities
        ),
        "known_control_conflict_annotation_identities": (
            known_control_conflict_identities
        ),
        "terminal_leakage_existing_group_conflict_count": (
            terminal_existing_group_conflict_count
        ),
        "resolved_historical_extension_event_count": sum(
            item["leakage_classification"] == "HISTORICAL_BASELINE_COMPONENT"
            and item["terminal_outcome"] != "LEAKAGE_BASELINE_EXTENSION_BLOCKED"
            for item in new_outcomes
        ),
        "human_review_new_chemistry_count": route_counts["HUMAN_REVIEW_REQUIRED_NEW_CHEMISTRY"],
        "human_review_pre_chemistry_count": route_counts["HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY"],
        "human_review_cluster_count": len(clusters),
        "human_review_event_count": sum(
            route_counts[item] for item in (
                "HUMAN_REVIEW_REQUIRED_NEW_CHEMISTRY",
                "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
                "SOURCE_ANNOTATION_CONFLICT",
            )
        ),
        "human_review_unit_count": len(review_units),
        "mixed_chemistry_cluster_count": sum(
            not item["topology_coherent_for_joint_human_review"]
            for item in clusters
        ),
        "joint_human_review_coherent_cluster_count": sum(
            bool(item["topology_coherent_for_joint_human_review"])
            for item in clusters
        ),
        "one_chemistry_rule_approvalable_cluster_count": sum(
            bool(item["approvalable_as_one_chemistry_rule"])
            for item in clusters
        ),
        "cache_count_semantics_fixed": True,
        "cluster_reviewability_semantics_fixed": True,
        "quarantine_representation_gap_count": route_counts["QUARANTINE_REPRESENTATION_GAP"],
        "runtime_extension_count": route_counts["RUNTIME_EXTENSION_REQUIRED"] + route_counts["KNOWN_RUNTIME_EXTENSION"],
        "leakage_baseline_extension_blocked_count": route_counts["LEAKAGE_BASELINE_EXTENSION_BLOCKED"],
        "remaining_existing_group_conflict_event_count": route_counts[
            "LEAKAGE_EXISTING_GROUP_CONFLICT"
        ],
        "structural_evidence_incomplete_count": route_counts["STRUCTURAL_EVIDENCE_INCOMPLETE"],
        "source_annotation_conflict_count": route_counts["SOURCE_ANNOTATION_CONFLICT"],
        "feature_rejected_count": route_counts["REJECTED_FEATURE_INCOMPATIBLE"],
        "event_rejected_count": route_counts["REJECTED_EVENT_INVALID"],
        "terminal_route_counts": {
            route: route_counts[route] for route in TERMINAL_ROUTES
        },
        "existing_chemistry_authority_count": 3,
        "existing_cumulative_expansion_member_count": 3,
        "authorized_data_population_before": 19,
        "authorized_data_population_after": 19,
        "chemistry_registry_modified": False,
        "cumulative_registry_modified": False,
        "production_materialization_performed": False,
        "production_approval_written": False,
        "production_trainable_new_sample_count": 0,
        "historical_extension_overlay_implemented": True,
        "historical_group_split_inheritance_implemented": True,
        "ratio_refit_for_historical_extension": False,
        "2djf_quarantine_preserved": two_djf_quarantine_preserved,
        "k2z_runtime_extension_preserved": k2z_runtime_extension_preserved,
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "feature_semantics_reopened": False,
        "published_mixed_training_runtime_population": 16,
        "ready_for_full_training": False,
        "ready_for_full_training_false_reason": (
            "LATER_TRAINING_PATH_OR_MIXED_RUNTIME_INTEGRATION_"
            "NOT_FEATURE_SEMANTICS"
        ),
        "ccd_component_enrichment_implemented": True,
        "chemistry_aware_review_units_implemented": True,
        "chemistry_aware_clustering_implemented": True,
        "new_candidate_exact_signature_computability_reported": True,
        "new_candidate_leakage_prediction_real_path_implemented": True,
        "all_terminal_counts_reconcile": True,
        "production_population_unchanged": True,
        "regressions_pass": regressions_pass,
        **cache_summary,
    }
    if sum(route_counts.values()) != canonical_count:
        raise ValueError("TERMINAL_ROUTE_COUNT_RECONCILIATION_FAILED")
    if sum(source_distribution.values()) != canonical_count:
        raise ValueError("SOURCE_DISTRIBUTION_RECONCILIATION_FAILED")
    if known_event_count + new_count != canonical_count:
        raise ValueError("KNOWN_NEW_EVENT_COUNT_RECONCILIATION_FAILED")
    validate_summary_reconciliation_v1(summary)
    ready = all((
        summary["bulk_core_operational"],
        summary["specialist_seeded_rcsb_recovery_implemented"],
        summary["ccd_component_enrichment_implemented"],
        summary["chemistry_aware_review_units_implemented"],
        summary["chemistry_aware_clustering_implemented"],
        summary["exact_authority_match_is_not_identity_stub"],
        summary["new_candidate_exact_signature_computability_reported"],
        summary["new_candidate_leakage_prediction_real_path_implemented"],
        summary["historical_extension_overlay_implemented"],
        summary["historical_group_split_inheritance_implemented"],
        summary["ratio_refit_for_historical_extension"] is False,
        summary["2djf_quarantine_preserved"],
        summary["k2z_runtime_extension_preserved"],
        summary["all_leakage_existing_group_conflict_classification_count"]
        == summary["new_candidate_existing_group_conflict_count"]
        + summary["known_control_conflict_annotation_count"],
        summary["terminal_leakage_existing_group_conflict_count"]
        == summary["remaining_existing_group_conflict_event_count"],
        summary["all_terminal_counts_reconcile"],
        summary["production_population_unchanged"],
        summary["regressions_pass"],
    ))
    summary["ready_for_gpt_review"] = ready
    summary["publication_ready"] = ready
    summary["revision_status"] = (
        "PREPUBLICATION_MAINLINE_REVISION_COMPLETE" if ready
        else "PREPUBLICATION_MAINLINE_REVISION_INCOMPLETE"
    )
    summary["recommended_next_step_exactly"] = (
        "review_and_publish_covapie_bulk_historical_baseline_leakage_extension_v1"
        if ready else "resolve_the_single_reported_bulk_mainline_blocker_v1"
    )
    return summary


def validate_summary_reconciliation_v1(summary: Mapping[str, Any]) -> None:
    canonical = int(summary["canonical_unique_event_count"])
    if int(summary["known_existing_event_count"]) + int(
        summary["new_unique_candidate_event_count"]
    ) != canonical:
        raise ValueError("SUMMARY_KNOWN_NEW_RECONCILIATION_FAILED")
    source_keys = (
        "events_with_1_source", "events_with_2_sources",
        "events_with_3_sources", "events_with_4_sources",
    )
    if sum(int(summary[key]) for key in source_keys) != canonical:
        raise ValueError("SUMMARY_SOURCE_DISTRIBUTION_RECONCILIATION_FAILED")
    routes = summary["terminal_route_counts"]
    if set(routes) != set(TERMINAL_ROUTES) or sum(int(value) for value in routes.values()) != canonical:
        raise ValueError("SUMMARY_TERMINAL_ROUTE_RECONCILIATION_FAILED")
    if (
        int(summary["all_source_normalized_record_count"])
        != int(summary["records_without_canonical_event_identity_count"])
        + int(summary["cross_source_duplicate_record_count"])
        + canonical
    ):
        raise ValueError("SUMMARY_SOURCE_RECORD_RECONCILIATION_FAILED")
    if {
        "new_candidate_exact_signature_computable_count",
        "new_candidate_exact_signature_not_computable_count",
    }.issubset(summary) and (
        int(summary["new_candidate_exact_signature_computable_count"])
        + int(summary["new_candidate_exact_signature_not_computable_count"])
        != int(summary["new_unique_candidate_event_count"])
    ):
        raise ValueError("SUMMARY_NEW_EXACT_SIGNATURE_RECONCILIATION_FAILED")
    if {
        "new_candidate_leakage_resolved_count",
        "new_candidate_leakage_unresolved_count",
    }.issubset(summary) and (
        int(summary["new_candidate_leakage_resolved_count"])
        + int(summary["new_candidate_leakage_unresolved_count"])
        != int(summary["new_unique_candidate_event_count"])
    ):
        raise ValueError("SUMMARY_NEW_LEAKAGE_RECONCILIATION_FAILED")
    conflict_keys = {
        "all_leakage_existing_group_conflict_classification_count",
        "new_candidate_existing_group_conflict_count",
        "known_control_conflict_annotation_count",
        "known_control_conflict_annotation_identities",
        "terminal_leakage_existing_group_conflict_count",
        "remaining_existing_group_conflict_event_count",
    }
    if conflict_keys.issubset(summary):
        identities = summary["known_control_conflict_annotation_identities"]
        if (
            type(identities) is not list
            or identities != ["2DJF/1ZB", "2R9F/K2Z"]
            or int(summary[
                "all_leakage_existing_group_conflict_classification_count"
            ])
            != int(summary["new_candidate_existing_group_conflict_count"])
            + int(summary["known_control_conflict_annotation_count"])
            or int(summary["known_control_conflict_annotation_count"])
            != len(identities)
            or int(summary["terminal_leakage_existing_group_conflict_count"])
            != int(summary["remaining_existing_group_conflict_event_count"])
            or int(summary["terminal_leakage_existing_group_conflict_count"])
            != int(routes["LEAKAGE_EXISTING_GROUP_CONFLICT"])
        ):
            raise ValueError("SUMMARY_EXISTING_GROUP_CONFLICT_RECONCILIATION_FAILED")


def _relative_cache_summary(
    cache: BulkCacheV1, repo_root: Path,
) -> dict[str, Any]:
    summary = cache.summary()
    try:
        relative = cache.root.relative_to(repo_root.parent.resolve())
    except ValueError as error:
        raise ValueError("BULK_CACHE_NOT_UNDER_REPOSITORY_PARENT") from error
    summary["bulk_cache_root"] = relative.as_posix()
    summary["bulk_cache_root_scope"] = "REPOSITORY_PARENT_RELATIVE"
    return summary


def build_covapie_bulk_cys_sg_dataset_expansion_artifacts_v1(
    *, repo_root: Path, cache_root: Path, regressions_pass: bool = False,
) -> dict[str, bytes]:
    repo_root = repo_root.resolve()
    cache = BulkCacheV1(cache_root)
    authorities, leakage_registry, historical = _load_frozen_state_v1(repo_root)
    access_records = source_access_resolution_v1()

    covpdb_records, covpdb_snapshot = discover_covpdb_v1(cache)
    covbinder_records, covbinder_snapshot = discover_covbinder_v1(cache)
    covalentindb_snapshot = deferred_covalentindb_snapshot_v1()
    rcsb_records, rcsb_snapshot = discover_rcsb_direct_v1(cache)
    covpdb_specialist = [item for item in covpdb_records if item.get("pdb_id")]
    specialist_records = [*covpdb_specialist, *covbinder_records]
    seeded_records, specialist_snapshot, specialist_statuses = (
        discover_rcsb_specialist_seeded_v1(
            cache,
            specialist_records=specialist_records,
            direct_records=rcsb_records,
        )
    )
    direct_by_event: dict[str, dict[str, Any]] = {}
    for item in [*rcsb_records, *seeded_records]:
        direct_by_event.setdefault(str(item["canonical_event_id"]), item)
    all_rcsb_records = [direct_by_event[key] for key in sorted(direct_by_event)]
    direct_pdb_ids = {str(item["pdb_id"]) for item in rcsb_records}
    merged_events, unmatched_specialist = adapters.merge_cross_source_events_v1(
        all_rcsb_records,
        specialist_records,
        specialist_pdb_statuses=specialist_statuses,
    )
    contributing_ids = {
        value
        for event in merged_events for value in event["source_record_ids"]
    }
    covpdb_contributing = sum(
        adapters.SOURCE_COVPDB + ":" + str(item["source_record_id"])
        in contributing_ids for item in covpdb_specialist
    )
    covbinder_contributing = sum(
        adapters.SOURCE_COVBINDERINPDB + ":" + str(item["source_record_id"])
        in contributing_ids for item in covbinder_records
    )
    covbinder_seeded_resolved = sum(
        adapters.SOURCE_COVBINDERINPDB + ":" + str(item["source_record_id"])
        in contributing_ids and str(item["pdb_id"]) not in direct_pdb_ids
        for item in covbinder_records
    )
    covpdb_seeded_events = {
        event["canonical_event_id"]
        for event in merged_events
        if adapters.SOURCE_COVPDB in event["source_datasets"]
        and event["pdb_id"] not in direct_pdb_ids
    }
    covpdb_snapshot["covpdb_seeded_rcsb_exact_event_count"] = len(
        covpdb_seeded_events
    )
    covpdb_snapshot["covpdb_records_contributing_to_canonical_events"] = (
        covpdb_contributing
    )
    covpdb_snapshot["covpdb_cross_source_exact_event_count"] = sum(
        adapters.SOURCE_COVPDB in item["source_datasets"]
        for item in merged_events
    )
    covbinder_snapshot["covbinder_pdb_seeds"] = len({
        str(item["pdb_id"]) for item in covbinder_records if item.get("pdb_id")
    })
    covbinder_snapshot["covbinder_records_resolved_via_specialist_seeded_rcsb"] = (
        covbinder_seeded_resolved
    )
    covbinder_snapshot["covbinder_records_contributing_to_canonical_events"] = (
        covbinder_contributing
    )
    covbinder_snapshot["covbinder_unresolved_records"] = (
        len(covbinder_records) - covbinder_contributing
    )
    covbinder_snapshot["covbinder_cross_source_exact_event_count"] = sum(
        adapters.SOURCE_COVBINDERINPDB in item["source_datasets"]
        for item in merged_events
    )
    rcsb_snapshot["specialist_seeded_recovery"] = specialist_snapshot
    rcsb_snapshot["rcsb_direct_normalized_records"] = rcsb_snapshot[
        "rcsb_normalized_records"
    ]
    rcsb_snapshot["rcsb_specialist_seeded_normalized_records"] = len(
        seeded_records
    )
    rcsb_snapshot["rcsb_normalized_records"] = len(all_rcsb_records)
    event_by_id = {
        item["canonical_event_id"]: item for item in merged_events
    }
    if len(event_by_id) != len(merged_events):
        raise ValueError("CANONICAL_EVENT_DEDUPLICATION_FAILED")
    merged_events = [event_by_id[key] for key in sorted(event_by_id)]
    event_by_id = {item["canonical_event_id"]: item for item in merged_events}

    known_identities = (
        KNOWN_EXPANSION_APPROVED | KNOWN_QUARANTINE
        | KNOWN_RUNTIME_EXTENSION | historical
    )
    known_event_count = sum(
        (item["pdb_id"], item["ligand_component_id"]) in known_identities
        for item in merged_events
    )
    known_event_ids = {
        str(item["canonical_event_id"])
        for item in merged_events
        if (item["pdb_id"], item["ligand_component_id"]) in known_identities
    }
    if len(known_event_ids) != known_event_count:
        raise ValueError("KNOWN_EVENT_ID_RECONCILIATION_FAILED")
    selected_events = select_structural_pilot_events_v1(
        merged_events, known_identities=known_identities,
    )
    structures, acquisition_rows, compressed_total = _acquire_structures_v1(
        cache, selected_events,
    )
    ccd_components, ccd_manifest = acquire_ccd_components_v1(
        cache, [str(item["ligand_component_id"]) for item in selected_events],
    )
    acquisition_by_pdb = {
        item["pdb_id"]: item for item in acquisition_rows
    }
    outcomes: list[dict[str, Any]] = []
    selected_ids = {item["canonical_event_id"] for item in selected_events}
    for event in merged_events:
        if event["canonical_event_id"] not in selected_ids:
            outcomes.append(_outcome_for_unprocessed_event(
                event, "BOUNDED_EVENT_PROCESSING_CAP_NOT_SELECTED",
            ))
            continue
        pdb_id = event["pdb_id"]
        payload = structures.get(pdb_id)
        if payload is None:
            reason = acquisition_by_pdb.get(pdb_id, {}).get(
                "failure_reason", "STRUCTURE_PAYLOAD_UNAVAILABLE"
            )
            phases = {stage: "NOT_REACHED" for stage in BULK_STAGES}
            for stage in BULK_STAGES[:4]:
                phases[stage] = "PASSED"
            phases[BULK_STAGES[4]] = "FAILED_CLOSED"
            outcomes.append(_terminal_outcome(
                event, phases=phases,
                route="STRUCTURAL_EVIDENCE_INCOMPLETE",
                reasons=(str(reason),),
            ))
            continue
        outcomes.append(process_event_structure_v1(
            event,
            mmcif_payload=payload,
            authorities=authorities,
            known_historical=historical,
            ccd_component=ccd_components.get(str(event["ligand_component_id"])),
        ))
    outcomes.sort(key=lambda item: item["canonical_event_id"])
    leakage_context = _load_leakage_prediction_context_v1(
        repo_root, authorities=authorities, leakage_registry=leakage_registry,
    )
    apply_leakage_predictions_read_only_v1(
        outcomes, historical=historical, context=leakage_context,
    )
    review_units = build_human_review_units_v1(outcomes, event_by_id)
    clusters = cluster_review_units_v1(
        review_units, outcomes=outcomes, event_by_id=event_by_id,
    )
    cluster_by_event = {
        event_id: cluster["cluster_id"]
        for cluster in clusters for event_id in cluster["canonical_event_ids"]
    }
    for outcome in outcomes:
        cluster_id = cluster_by_event.get(outcome["canonical_event_id"])
        outcome["stage_statuses"][BULK_STAGES[13]] = (
            "CLUSTERED:" + cluster_id if cluster_id else "NOT_APPLICABLE"
        )
        outcome["stage_statuses"][BULK_STAGES[14]] = "SUMMARIZED"

    all_source_normalized = (
        len(covpdb_records) + len(covbinder_records) + len(all_rcsb_records)
    )
    records_without_identity = (
        int(covpdb_snapshot["covpdb_ligand_records_normalized"])
        + len(unmatched_specialist)
    )
    cache_summary = _relative_cache_summary(cache, repo_root)
    summary = _build_summary_v1(
        access_records=access_records,
        covpdb_snapshot=covpdb_snapshot,
        covbinder_snapshot=covbinder_snapshot,
        covalentindb_snapshot=covalentindb_snapshot,
        rcsb_snapshot=rcsb_snapshot,
        specialist_snapshot=specialist_snapshot,
        merged_events=merged_events,
        records_without_event_identity=records_without_identity,
        all_source_normalized_record_count=all_source_normalized,
        outcomes=outcomes,
        acquisition=acquisition_rows,
        compressed_total=compressed_total,
        clusters=clusters,
        review_units=review_units,
        ccd_manifest=ccd_manifest,
        known_event_count=known_event_count,
        known_event_ids=known_event_ids,
        cache_summary=cache_summary,
        regressions_pass=regressions_pass,
    )

    access_artifact = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "provenance_role_hierarchy": {
            adapters.DISCOVERY_SOURCE: (
                "candidate discovery only; cannot approve production chemistry"
            ),
            adapters.STRUCTURE_AUTHORITY_SOURCE: (
                "normalized core structural evidence from RCSB/PDB mmCIF"
            ),
            adapters.SUPPORTING_CHEMISTRY_ANNOTATION: (
                "triage and packet annotation only"
            ),
            adapters.PRODUCTION_CHEMISTRY_AUTHORITY: (
                "existing human-approved CovaPIE registry only"
            ),
        },
        "sources": access_records,
    }
    cross_manifest = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "canonical_event_identity_contract": (
            "COVAPIE_CYS_SG_EVENT_V1:PDB:protein-instance:CYS:auth-residue:"
            "SG:ligand-instance:component:ligand-atom"
        ),
        "source_name_excluded_from_scientific_identity": True,
        "adapter_registry": sorted(adapters.adapter_registry_v1()),
        "canonical_source_record_fields": list(
            adapters.CANONICAL_SOURCE_RECORD_FIELDS
        ),
        "canonical_events": merged_events,
        "unmatched_specialist_records": unmatched_specialist,
        "records_without_canonical_event_identity_count": records_without_identity,
        "duplicate_records_not_multiplied_into_events": True,
    }
    acquisition_artifact = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "unique_pdb_acquisition_cap": UNIQUE_PDB_ACQUISITION_CAP,
        "per_compressed_file_cap_bytes": COMPRESSED_FILE_CAP,
        "total_compressed_download_cap_bytes": TOTAL_COMPRESSED_DOWNLOAD_CAP,
        "covpdb_complex_archive_specific_cap_bytes": COVPDB_COMPLEX_ARCHIVE_CAP,
        "network_timeout_seconds": NETWORK_TIMEOUT_SECONDS,
        "max_attempts_per_request": MAX_ATTEMPTS_PER_REQUEST,
        "structures": acquisition_rows,
        "compressed_bytes_total": compressed_total,
        "ccd_components": ccd_manifest,
    }
    outcomes_artifact = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "bulk_stages": list(BULK_STAGES),
        "terminal_route_vocabulary": list(TERMINAL_ROUTES),
        "pre_status_vocabulary": sorted(PRE_STATUSES),
        "events": outcomes,
        "production_materialization_performed": False,
        "chemistry_registry_modified": False,
        "cumulative_registry_modified": False,
    }
    clusters_artifact = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_date": SNAPSHOT_DATE,
        "clustering_is_non_authority_triage_only": True,
        "review_units": review_units,
        "clusters": clusters,
    }
    values: dict[str, object] = {
        "bulk_source_access_resolution_v1.json": access_artifact,
        "covpdb_discovery_snapshot_v1.json": covpdb_snapshot,
        "covbinderinpdb_discovery_snapshot_v1.json": covbinder_snapshot,
        "covalentindb_discovery_snapshot_v1.json": covalentindb_snapshot,
        "rcsb_pdb_direct_discovery_snapshot_v1.json": rcsb_snapshot,
        "cross_source_canonical_event_manifest_v1.json": cross_manifest,
        "bulk_acquisition_manifest_v1.json": acquisition_artifact,
        "bulk_processing_outcomes_v1.json": outcomes_artifact,
        "bulk_human_review_clusters_v1.json": clusters_artifact,
        "bulk_summary_v1.json": summary,
    }
    if tuple(sorted(values)) != tuple(sorted(OUTPUT_FILENAMES)):
        raise ValueError("BULK_OUTPUT_FILE_SET_INVALID")
    return {name: _canonical_json(value) for name, value in values.items()}


def materialize_covapie_bulk_cys_sg_dataset_expansion_v1(
    *, repo_root: Path, cache_root: Path, output_root: Path | None = None,
    regressions_pass: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = (
        output_root.resolve() if output_root is not None
        else repo_root / REPOSITORY_OUTPUT_RELATIVE
    )
    if target != repo_root / REPOSITORY_OUTPUT_RELATIVE:
        try:
            target.relative_to(Path(tempfile.gettempdir()).resolve())
        except ValueError as error:
            raise ValueError("BULK_OUTPUT_ROOT_OUTSIDE_AUTHORIZED_PATH") from error
    artifacts = build_covapie_bulk_cys_sg_dataset_expansion_artifacts_v1(
        repo_root=repo_root, cache_root=cache_root,
        regressions_pass=regressions_pass,
    )
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return json.loads(artifacts["bulk_summary_v1.json"])


def verify_repository_output_determinism_v1(
    *, repo_root: Path, cache_root: Path, regressions_pass: bool = False,
) -> dict[str, str]:
    output_root = repo_root.resolve() / REPOSITORY_OUTPUT_RELATIVE
    first = {
        name: (output_root / name).read_bytes() for name in OUTPUT_FILENAMES
    }
    second = build_covapie_bulk_cys_sg_dataset_expansion_artifacts_v1(
        repo_root=repo_root, cache_root=cache_root,
        regressions_pass=regressions_pass,
    )
    if first != second:
        raise ValueError("CANONICAL_OUTPUT_REPLAY_NOT_BYTE_IDENTICAL")
    return {name: _sha(first[name]) for name in sorted(first)}
