"""Minimal additive executor for the published CovaPIE 500-event cohort.

The default entry point is a read-only, no-network preflight.  Controlled
network acquisition exists for a later explicitly authorized run, but it is
separated from structural processing and finalization so that cache reuse,
download budgets, and predecessor provenance remain auditable.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
import copy
import csv
from dataclasses import dataclass, field
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
from typing import Any
from urllib.request import Request, urlopen

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as frozen_bulk
from covalent_ext import covapie_bulk_500_new_event_scale_up_rehearsal_v1 as rehearsal


SCHEMA_VERSION = "covapie_bulk_500_event_executor_v1"
PREFLIGHT_NO_NETWORK = "PREFLIGHT_NO_NETWORK"
CONTROLLED_NETWORK_EXECUTION = "CONTROLLED_NETWORK_EXECUTION"
DEFAULT_MODE = PREFLIGHT_NO_NETWORK

FROZEN_HISTORICAL_PREDECESSOR = "FROZEN_HISTORICAL_PREDECESSOR"
NEW_INCREMENTAL_EXECUTION = "NEW_INCREMENTAL_EXECUTION"
KNOWN_EXISTING_CONTROL_REFERENCE = "KNOWN_EXISTING_CONTROL_REFERENCE"

PUBLISHED_EXECUTOR_BASELINE_ANCESTOR = (
    "89e43b747e8d36e6f1845bd4e66c49e8d5779907"
)
PUBLISHED_REHEARSAL_ROOT_RELATIVE = rehearsal.OUTPUT_ROOT_RELATIVE
PUBLISHED_REHEARSAL_BINDINGS: dict[str, tuple[int, str]] = {
    rehearsal.MANIFEST: (
        16759,
        "d8c6d5d4ef181427cb4d1c970de8d03f75ecc976ed18ea9e1ce42f94e3cde4b9",
    ),
    rehearsal.COHORT: (
        232178,
        "0bc006f417604ea17e530e884c1148c99713224eb9726e15dc661f3e41bbbb4c",
    ),
    rehearsal.ACQUISITION: (
        219699,
        "03f8d0db72e59a6eba340fc718ed1c1e1ffcf7aebbcb96a1435c64b923851ccd",
    ),
    rehearsal.SUMMARY: (
        5051,
        "253b8829cd7437b6bb379fed0bf19acdb18fa8df9effa5f4aebe6b125134e1fa",
    ),
}

CANONICAL_EVENT_MANIFEST_RELATIVE = (
    rehearsal.PILOT_ROOT_RELATIVE / "cross_source_canonical_event_manifest_v1.json"
)
CANONICAL_EVENT_MANIFEST_SHA256 = (
    "d3f35987af92fca669b85d62a86914c7a01bf35d867c4a779e7fc08e76445dae"
)
HISTORICAL_OUTCOMES_RELATIVE = (
    rehearsal.PILOT_ROOT_RELATIVE / "bulk_processing_outcomes_v1.json"
)
HISTORICAL_OUTCOMES_SHA256 = (
    "0270dd93a31427042d02f7751ab7b46679308c7f1ee5207a5560b199a6a94d57"
)
INCREMENTAL_ORDERED_EVENT_IDS_SHA256 = (
    "cd8b85e7b7e4da924a5c73800e84aff48f029d3df842eac71d9210d0139b7e3c"
)

DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-multisource-cys-sg-v1"
)
DEFAULT_CONTROLLED_OUTPUT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-500-controlled-execution-v1"
)

PDB_SINGLE_PAYLOAD_CAP_BYTES = frozen_bulk.COMPRESSED_FILE_CAP
CCD_SINGLE_PAYLOAD_CAP_BYTES = 4 * 1024 * 1024
HARD_TOTAL_DOWNLOAD_CAP_BYTES = frozen_bulk.TOTAL_COMPRESSED_DOWNLOAD_CAP
EXECUTOR_DOWNLOAD_PROVENANCE = "DOWNLOADED_BY_500_EVENT_EXECUTOR_V1"
REUSED_CACHE_PROVENANCE = "REUSED_EXISTING_CACHE"

CONTROLLED_OUTPUT_FILENAMES = (
    "incremental_processing_outcomes_v1.json",
    "cumulative_processing_view_v1.json",
    "controlled_execution_result_v1.json",
)
EXECUTOR_IMPLEMENTATION_PATHS = frozenset({
    "src/covalent_ext/covapie_bulk_500_event_executor_v1.py",
    "scripts/run_covapie_bulk_500_event_executor_v1.py",
    "scripts/check_covapie_bulk_500_event_executor_v1.py",
    "tests/test_covapie_bulk_500_event_executor_v1.py",
})
LEAKAGE_BATCH_POPULATION_COUNT = 527


class ExecutorSafetyError(ValueError):
    """Fail-closed executor authorization or integrity error."""


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8") + b"\n"


def _ordered_ids_sha256(records: Sequence[Mapping[str, Any]]) -> str:
    return _sha(frozen_bulk._canonical_json([
        str(item["canonical_event_id"]) for item in records
    ]))


def _bound_payload(
    repo_root: Path,
    relative: Path,
    *,
    expected_sha256: str,
    expected_bytes: int | None = None,
) -> bytes:
    path = repo_root / relative
    payload = path.read_bytes()
    if expected_bytes is not None and len(payload) != expected_bytes:
        raise ExecutorSafetyError("PUBLISHED_BINDING_BYTE_COUNT_MISMATCH:" + relative.as_posix())
    if _sha(payload) != expected_sha256:
        raise ExecutorSafetyError("PUBLISHED_BINDING_SHA256_MISMATCH:" + relative.as_posix())
    return payload


def _binding(relative: Path, payload: bytes) -> dict[str, object]:
    return {
        "path": relative.as_posix(),
        "byte_count": len(payload),
        "sha256": _sha(payload),
    }


def load_published_executor_inputs_v1(repo_root: Path) -> dict[str, Any]:
    """Load exact published execution identities without discovery or selection."""

    repo_root = repo_root.resolve()
    rehearsal_payloads: dict[str, bytes] = {}
    for name, (byte_count, digest) in PUBLISHED_REHEARSAL_BINDINGS.items():
        rehearsal_payloads[name] = _bound_payload(
            repo_root,
            PUBLISHED_REHEARSAL_ROOT_RELATIVE / name,
            expected_sha256=digest,
            expected_bytes=byte_count,
        )

    manifest = json.loads(rehearsal_payloads[rehearsal.MANIFEST])
    requirements = json.loads(rehearsal_payloads[rehearsal.ACQUISITION])
    summary = json.loads(rehearsal_payloads[rehearsal.SUMMARY])
    reader = csv.DictReader(
        io.StringIO(rehearsal_payloads[rehearsal.COHORT].decode("utf-8"))
    )
    if tuple(reader.fieldnames or ()) != rehearsal.EVENT_HEADER:
        raise ExecutorSafetyError("PUBLISHED_COHORT_HEADER_MISMATCH")
    cohort_rows = list(reader)
    if (
        len(cohort_rows) != 500
        or [int(item["scaleup_rank"]) for item in cohort_rows] != list(range(1, 501))
        or len({item["canonical_event_id"] for item in cohort_rows}) != 500
    ):
        raise ExecutorSafetyError("PUBLISHED_COHORT_IDENTITY_OR_RANK_MISMATCH")
    if not (
        all(item["tranche"] == rehearsal.HISTORICAL_TRANCHE for item in cohort_rows[:250])
        and all(item["tranche"] == rehearsal.INCREMENTAL_TRANCHE for item in cohort_rows[250:])
        and all(item["historical_pilot_processed"] == "true" for item in cohort_rows[:250])
        and all(item["historical_pilot_processed"] == "false" for item in cohort_rows[250:])
    ):
        raise ExecutorSafetyError("PUBLISHED_COHORT_LANE_BOUNDARY_MISMATCH")

    population = requirements.get("population", {})
    pdb_requirements = requirements.get("pdb_requirements", {})
    ccd_requirements = requirements.get("ccd_requirements", {})
    cohort_summary = summary.get("cohort", {})
    prefix_proof = manifest.get("prefix_parity_proof", {})
    required_values = (
        population.get("cumulative_new_event_count") == 500,
        population.get("historical_pilot_new_event_count") == 250,
        population.get("incremental_new_event_count") == 250,
        population.get("known_existing_control_event_count") == 27,
        cohort_summary.get("remaining_unselected_new_event_count") == 1860,
        prefix_proof.get("historical_250_exact_prefix_of_500") is True,
        pdb_requirements.get("cumulative_500_unique_pdb_count") == 290,
        pdb_requirements.get("incremental_new_unique_pdb_count") == 136,
        pdb_requirements.get("planning_universe_unique_pdb_count_including_controls") == 311,
        ccd_requirements.get("cumulative_500_unique_ccd_count") == 225,
        ccd_requirements.get("incremental_new_ccd_count") == 102,
        requirements.get("execution_not_performed") is True,
        requirements.get("network_performed") is False,
    )
    if not all(required_values):
        raise ExecutorSafetyError("PUBLISHED_REHEARSAL_SEMANTICS_MISMATCH")

    canonical_payload = _bound_payload(
        repo_root,
        CANONICAL_EVENT_MANIFEST_RELATIVE,
        expected_sha256=CANONICAL_EVENT_MANIFEST_SHA256,
    )
    outcomes_payload = _bound_payload(
        repo_root,
        HISTORICAL_OUTCOMES_RELATIVE,
        expected_sha256=HISTORICAL_OUTCOMES_SHA256,
    )
    canonical_artifact = json.loads(canonical_payload)
    historical_artifact = json.loads(outcomes_payload)
    event_by_id = {
        str(item["canonical_event_id"]): item
        for item in canonical_artifact["canonical_events"]
    }
    outcome_by_id = {
        str(item["canonical_event_id"]): item
        for item in historical_artifact["events"]
    }
    if len(event_by_id) != 2387 or len(outcome_by_id) != 2387:
        raise ExecutorSafetyError("PUBLISHED_CANONICAL_SOURCE_POPULATION_MISMATCH")

    ordered_event_ids = [item["canonical_event_id"] for item in cohort_rows]
    try:
        cohort_records = [event_by_id[event_id] for event_id in ordered_event_ids]
        historical_outcomes = [outcome_by_id[event_id] for event_id in ordered_event_ids[:250]]
    except KeyError as error:
        raise ExecutorSafetyError("PUBLISHED_COHORT_EVENT_MISSING_FROM_CANONICAL_SOURCE") from error
    for row, record in zip(cohort_rows, cohort_records, strict=True):
        if (
            row["pdb_id"] != str(record["pdb_id"])
            or row["ligand_component_id"] != str(record["ligand_component_id"])
            or row["ligand_reactive_atom"] != str(record["ligand_reactive_atom"])
            or row["protein_reactive_atom"] != str(record["protein_reactive_atom"])
        ):
            raise ExecutorSafetyError("PUBLISHED_COHORT_CANONICAL_RECORD_MISMATCH")

    incremental_records = cohort_records[250:]
    if len(incremental_records) != 250 or _ordered_ids_sha256(
        incremental_records
    ) != INCREMENTAL_ORDERED_EVENT_IDS_SHA256:
        raise ExecutorSafetyError("INCREMENTAL_ORDERED_WORKSET_MISMATCH")

    control_pdb_ids = {
        event_id
        for item in pdb_requirements["known_control_requirements"]
        for event_id in item["canonical_event_ids"]
    }
    control_ccd_ids = {
        event_id
        for item in ccd_requirements["known_control_requirements"]
        for event_id in item["canonical_event_ids"]
    }
    if control_pdb_ids != control_ccd_ids or len(control_pdb_ids) != 27:
        raise ExecutorSafetyError("KNOWN_CONTROL_IDENTITY_SET_MISMATCH")
    if set(ordered_event_ids) & control_pdb_ids:
        raise ExecutorSafetyError("KNOWN_CONTROLS_MIXED_INTO_NEW_EVENT_COHORT")
    try:
        control_records = [event_by_id[event_id] for event_id in sorted(control_pdb_ids)]
        control_outcomes = [outcome_by_id[event_id] for event_id in sorted(control_pdb_ids)]
    except KeyError as error:
        raise ExecutorSafetyError("KNOWN_CONTROL_MISSING_FROM_PUBLISHED_PREDECESSOR") from error

    pdb_ids = {str(item["pdb_id"]) for item in pdb_requirements["requirements"]}
    ccd_ids = {str(item["ccd_id"]) for item in ccd_requirements["requirements"]}
    if (
        len(pdb_ids) != 290
        or len(ccd_ids) != 225
        or pdb_ids != {str(item["pdb_id"]) for item in cohort_records}
        or ccd_ids != {str(item["ligand_component_id"]) for item in cohort_records}
    ):
        raise ExecutorSafetyError("PUBLISHED_ACQUISITION_REQUIREMENT_SET_MISMATCH")

    return {
        "repo_root": repo_root,
        "manifest": manifest,
        "requirements": requirements,
        "summary": summary,
        "cohort_rows": cohort_rows,
        "cohort_records": cohort_records,
        "historical_records": cohort_records[:250],
        "incremental_records": incremental_records,
        "historical_outcomes": historical_outcomes,
        "control_records": control_records,
        "control_outcomes": control_outcomes,
        "known_control_event_ids": control_pdb_ids,
        "required_pdb_ids": frozenset(pdb_ids),
        "required_ccd_ids": frozenset(ccd_ids),
        "bindings": {
            "published_rehearsal": [
                _binding(PUBLISHED_REHEARSAL_ROOT_RELATIVE / name, rehearsal_payloads[name])
                for name in rehearsal.OUTPUT_FILENAMES
            ],
            "canonical_event_manifest": _binding(
                CANONICAL_EVENT_MANIFEST_RELATIVE, canonical_payload
            ),
            "historical_processing_outcomes": _binding(
                HISTORICAL_OUTCOMES_RELATIVE, outcomes_payload
            ),
        },
    }


def _retrieval_identity(payload_kind: str, identity: str) -> dict[str, str]:
    if payload_kind == "PDB":
        return {
            "pdb_id": identity,
            "format": "PDBx/mmCIF gzip",
            "snapshot_date": frozen_bulk.SNAPSHOT_DATE,
        }
    if payload_kind == "CCD":
        return {
            "ccd_id": identity,
            "definition": "wwPDB Chemical Component Dictionary CIF",
            "snapshot_date": frozen_bulk.SNAPSHOT_DATE,
        }
    raise ExecutorSafetyError("PAYLOAD_KIND_INVALID")


def _payload_descriptor(payload_kind: str, identity: str) -> dict[str, Any]:
    if payload_kind == "PDB":
        return {
            "relative_path": f"rcsb/structures/{identity}.cif.gz",
            "url": frozen_bulk.RCSB_MMCIF_URL.format(pdb_id=identity),
            "maximum_bytes": PDB_SINGLE_PAYLOAD_CAP_BYTES,
            "retrieval_identity": _retrieval_identity(payload_kind, identity),
        }
    if payload_kind == "CCD":
        return {
            "relative_path": f"rcsb/ccd/{identity}.cif",
            "url": frozen_bulk.RCSB_CCD_URL.format(ccd_id=identity),
            "maximum_bytes": CCD_SINGLE_PAYLOAD_CAP_BYTES,
            "retrieval_identity": _retrieval_identity(payload_kind, identity),
        }
    raise ExecutorSafetyError("PAYLOAD_KIND_INVALID")


def snapshot_cache_tree_v1(cache_root: Path) -> dict[str, Any]:
    """Capture bytes plus stat identity without creating the cache root."""

    root = cache_root.resolve()
    if not root.is_dir():
        return {
            "available": False,
            "file_count": 0,
            "total_bytes": 0,
            "stat_tree_sha256": None,
            "ledger_sha256": None,
        }
    rows = []
    total = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        rows.append((path.relative_to(root).as_posix(), stat.st_size, stat.st_mtime_ns))
        total += stat.st_size
    ledger = root / "cache_manifest_v1.json"
    return {
        "available": ledger.is_file(),
        "file_count": len(rows),
        "total_bytes": total,
        "stat_tree_sha256": _sha(frozen_bulk._canonical_json(rows)),
        "ledger_sha256": _sha(ledger.read_bytes()) if ledger.is_file() else None,
    }


def _load_cache_entries(cache_root: Path) -> tuple[dict[str, dict[str, Any]], bool]:
    root = cache_root.resolve()
    ledger_path = root / "cache_manifest_v1.json"
    if not ledger_path.is_file():
        existing_files = [path for path in root.rglob("*") if path.is_file()] if root.is_dir() else []
        if existing_files:
            raise ExecutorSafetyError("CACHE_MANIFEST_MISSING_FOR_NONEMPTY_CACHE")
        return {}, False
    try:
        parsed = json.loads(ledger_path.read_bytes())
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ExecutorSafetyError("CACHE_MANIFEST_PARSE_FAILED") from error
    if parsed.get("schema_version") != "covapie_bulk_cache_manifest_v1":
        raise ExecutorSafetyError("CACHE_MANIFEST_SCHEMA_INVALID")
    payloads = parsed.get("payloads")
    if not isinstance(payloads, list):
        raise ExecutorSafetyError("CACHE_MANIFEST_PAYLOADS_INVALID")
    entries: dict[str, dict[str, Any]] = {}
    for item in payloads:
        if not isinstance(item, dict) or not isinstance(item.get("relative_path"), str):
            raise ExecutorSafetyError("CACHE_MANIFEST_ENTRY_INVALID")
        relative = item["relative_path"]
        if relative in entries:
            raise ExecutorSafetyError("CACHE_MANIFEST_DUPLICATE_RELATIVE_PATH")
        entries[relative] = item
    return entries, True


def _validate_payload_science(payload_kind: str, identity: str, payload: bytes) -> Any:
    if payload_kind == "PDB":
        frozen_bulk._validate_mmcif_payload(payload, identity)
        return payload
    if payload_kind == "CCD":
        return frozen_bulk.parse_ccd_cif_v1(payload, ccd_id=identity)
    raise ExecutorSafetyError("PAYLOAD_KIND_INVALID")


def _validate_cache_payload(
    *,
    cache_root: Path,
    entries: Mapping[str, Mapping[str, Any]],
    payload_kind: str,
    identity: str,
) -> tuple[bytes, Any]:
    descriptor = _payload_descriptor(payload_kind, identity)
    relative = descriptor["relative_path"]
    entry = entries.get(relative)
    path = cache_root / relative
    if entry is None or not path.is_file():
        raise ExecutorSafetyError("CACHE_ENTRY_OR_PAYLOAD_MISSING:" + relative)
    expected_identity_sha = _sha(
        frozen_bulk._canonical_json(descriptor["retrieval_identity"])
    )
    if (
        entry.get("relative_path") != relative
        or entry.get("source_url_or_endpoint") != descriptor["url"]
        or entry.get("source_dataset") != frozen_bulk.adapters.SOURCE_RCSB_PDB_DIRECT
        or entry.get("retrieval_identity_sha256") != expected_identity_sha
        or entry.get("http_status") != 200
    ):
        raise ExecutorSafetyError("CACHE_RETRIEVAL_IDENTITY_CONFLICT:" + relative)
    payload = path.read_bytes()
    try:
        byte_count = int(entry.get("byte_count"))
    except (TypeError, ValueError) as error:
        raise ExecutorSafetyError("CACHE_LEDGER_BYTE_COUNT_INVALID:" + relative) from error
    if byte_count != len(payload) or entry.get("sha256") != _sha(payload):
        raise ExecutorSafetyError("CACHE_PAYLOAD_LEDGER_CONFLICT:" + relative)
    if len(payload) > int(descriptor["maximum_bytes"]):
        raise ExecutorSafetyError("CACHE_PAYLOAD_SINGLE_FILE_CAP_EXCEEDED:" + relative)
    try:
        parsed = _validate_payload_science(payload_kind, identity, payload)
    except ValueError as error:
        raise ExecutorSafetyError("CACHE_PAYLOAD_SCIENTIFIC_VALIDATION_FAILED:" + relative) from error
    return payload, parsed


@dataclass(frozen=True)
class CacheInspectionV1:
    summary: dict[str, Any]
    pdb_payloads: dict[str, bytes] = field(default_factory=dict)
    ccd_components: dict[str, dict[str, Any]] = field(default_factory=dict)


def _nearest_rank(values: Sequence[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def inspect_cache_read_only_v1(
    *,
    cache_root: Path,
    inputs: Mapping[str, Any],
    include_payloads: bool = False,
) -> CacheInspectionV1:
    """Validate required cache payloads and ledger identities without writes."""

    root = cache_root.resolve()
    before = snapshot_cache_tree_v1(root)
    entries, ledger_available = _load_cache_entries(root)
    hits: dict[str, set[str]] = {"PDB": set(), "CCD": set()}
    missing: dict[str, set[str]] = {"PDB": set(), "CCD": set()}
    failures: dict[str, str] = {}
    pdb_payloads: dict[str, bytes] = {}
    ccd_components: dict[str, dict[str, Any]] = {}

    for payload_kind, identities in (
        ("PDB", inputs["required_pdb_ids"]),
        ("CCD", inputs["required_ccd_ids"]),
    ):
        for identity in sorted(identities):
            relative = _payload_descriptor(payload_kind, identity)["relative_path"]
            entry_exists = relative in entries
            payload_exists = (root / relative).is_file()
            if not entry_exists and not payload_exists:
                missing[payload_kind].add(identity)
                continue
            try:
                payload, parsed = _validate_cache_payload(
                    cache_root=root,
                    entries=entries,
                    payload_kind=payload_kind,
                    identity=identity,
                )
            except ExecutorSafetyError as error:
                failures[f"{payload_kind}:{identity}"] = str(error)
                missing[payload_kind].add(identity)
                continue
            hits[payload_kind].add(identity)
            if include_payloads and payload_kind == "PDB":
                pdb_payloads[identity] = payload
            if include_payloads and payload_kind == "CCD":
                ccd_components[identity] = parsed

    control_hits: dict[str, int] = {}
    control_misses: dict[str, int] = {}
    requirements = inputs["requirements"]
    for payload_kind, section, field_name in (
        ("PDB", "pdb_requirements", "pdb_id"),
        ("CCD", "ccd_requirements", "ccd_id"),
    ):
        identities = {
            str(item[field_name])
            for item in requirements[section]["known_control_requirements"]
        }
        valid_count = 0
        for identity in sorted(identities):
            relative = _payload_descriptor(payload_kind, identity)["relative_path"]
            try:
                _validate_cache_payload(
                    cache_root=root,
                    entries=entries,
                    payload_kind=payload_kind,
                    identity=identity,
                )
            except ExecutorSafetyError as error:
                if relative in entries or (root / relative).is_file():
                    failures[f"CONTROL_{payload_kind}:{identity}"] = str(error)
                continue
            valid_count += 1
        control_hits[payload_kind] = valid_count
        control_misses[payload_kind] = len(identities) - valid_count

    structure_sizes: list[int] = []
    ccd_sizes: list[int] = []
    for relative, entry in sorted(entries.items()):
        path = root / relative
        if not path.is_file():
            continue
        try:
            byte_count = int(entry.get("byte_count"))
        except (TypeError, ValueError):
            continue
        if path.stat().st_size != byte_count or _sha(path.read_bytes()) != entry.get("sha256"):
            continue
        if relative.startswith("rcsb/structures/") and relative.endswith(".cif.gz"):
            structure_sizes.append(byte_count)
        elif relative.startswith("rcsb/ccd/") and relative.endswith(".cif"):
            ccd_sizes.append(byte_count)

    pdb_mean = sum(structure_sizes) / len(structure_sizes) if structure_sizes else None
    ccd_mean = sum(ccd_sizes) / len(ccd_sizes) if ccd_sizes else None
    pdb_p95 = _nearest_rank(structure_sizes, 0.95)
    ccd_p95 = _nearest_rank(ccd_sizes, 0.95)
    if None in (pdb_mean, ccd_mean, pdb_p95, ccd_p95):
        projected_mean = None
        projected_p95 = None
    else:
        projected_mean = math.ceil(
            len(missing["PDB"]) * float(pdb_mean)
            + len(missing["CCD"]) * float(ccd_mean)
        )
        projected_p95 = (
            len(missing["PDB"]) * int(pdb_p95)
            + len(missing["CCD"]) * int(ccd_p95)
        )
    after = snapshot_cache_tree_v1(root)
    if before != after:
        raise ExecutorSafetyError("READ_ONLY_CACHE_INSPECTION_MODIFIED_CACHE")

    summary = {
        "cache_available": ledger_available,
        "cache_snapshot": before,
        "valid_pdb_hits": len(hits["PDB"]),
        "missing_pdb_count": len(missing["PDB"]),
        "missing_pdb_ids": sorted(missing["PDB"]),
        "valid_ccd_hits": len(hits["CCD"]),
        "missing_ccd_count": len(missing["CCD"]),
        "missing_ccd_ids": sorted(missing["CCD"]),
        "valid_control_pdb_hits": control_hits["PDB"],
        "missing_control_pdb_count": control_misses["PDB"],
        "valid_control_ccd_hits": control_hits["CCD"],
        "missing_control_ccd_count": control_misses["CCD"],
        "cache_integrity_failure_count": len(failures),
        "cache_integrity_failures": dict(sorted(failures.items())),
        "projected_mean_download_bytes": projected_mean,
        "projected_p95_download_bytes": projected_p95,
        "observation_only": True,
        "cache_modified": False,
    }
    return CacheInspectionV1(summary, pdb_payloads, ccd_components)


@dataclass(frozen=True)
class ProcessingContextV1:
    authorities: tuple[Any, ...]
    leakage_registry: Any
    historical_identities: set[tuple[str, str]]
    leakage_context: Mapping[str, Any]


def build_processing_context_v1(repo_root: Path) -> ProcessingContextV1:
    """Construct the same frozen authority and leakage context as the pilot."""

    authorities, leakage_registry, historical = frozen_bulk._load_frozen_state_v1(
        repo_root.resolve()
    )
    leakage_context = frozen_bulk._load_leakage_prediction_context_v1(
        repo_root.resolve(),
        authorities=authorities,
        leakage_registry=leakage_registry,
    )
    return ProcessingContextV1(
        tuple(authorities), leakage_registry, historical, leakage_context
    )


def preflight_no_network_v1(
    *, repo_root: Path, cache_root: Path | None = None,
) -> dict[str, Any]:
    """Run the safe default preflight with zero network, writes, or processing."""

    repo_root = repo_root.resolve()
    inputs = load_published_executor_inputs_v1(repo_root)
    root = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.parent / DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT
    )
    inspection = inspect_cache_read_only_v1(cache_root=root, inputs=inputs)
    context = build_processing_context_v1(repo_root)
    publication_observation = observe_repository_publication_state_v1(repo_root)
    try:
        validate_controlled_publication_observation_v1(publication_observation)
    except ExecutorSafetyError as error:
        publication_gate_satisfied = False
        publication_gate_reason = str(error)
    else:
        publication_gate_satisfied = True
        publication_gate_reason = None
    cache = inspection.summary
    projected_p95 = cache["projected_p95_download_bytes"]
    ready = all((
        len(inputs["incremental_records"]) == 250,
        _ordered_ids_sha256(inputs["incremental_records"])
        == INCREMENTAL_ORDERED_EVENT_IDS_SHA256,
        cache["cache_integrity_failure_count"] == 0,
        len(context.authorities) == 3,
        projected_p95 is None or projected_p95 <= HARD_TOTAL_DOWNLOAD_CAP_BYTES,
        HARD_TOTAL_DOWNLOAD_CAP_BYTES == 2 * 1024 * 1024 * 1024,
        LEAKAGE_BATCH_POPULATION_COUNT == 250 + 27 + 250,
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": PREFLIGHT_NO_NETWORK,
        "published_rehearsal_binding_valid": True,
        "cumulative_new_event_count": 500,
        "historical_frozen_new_event_count": 250,
        "incremental_execution_event_count": 250,
        "known_control_event_count": 27,
        "required_unique_pdb_count": 290,
        "required_unique_ccd_count": 225,
        "planning_unique_pdb_with_controls": 311,
        "incremental_ordered_event_ids_sha256": INCREMENTAL_ORDERED_EVENT_IDS_SHA256,
        "historical_lane": FROZEN_HISTORICAL_PREDECESSOR,
        "incremental_lane": NEW_INCREMENTAL_EXECUTION,
        "control_lane": KNOWN_EXISTING_CONTROL_REFERENCE,
        "current_valid_pdb_cache_hits": cache["valid_pdb_hits"],
        "current_missing_pdb_count": cache["missing_pdb_count"],
        "current_missing_pdb_ids": cache["missing_pdb_ids"],
        "current_valid_ccd_cache_hits": cache["valid_ccd_hits"],
        "current_missing_ccd_count": cache["missing_ccd_count"],
        "current_missing_ccd_ids": cache["missing_ccd_ids"],
        "current_valid_control_pdb_cache_hits": cache["valid_control_pdb_hits"],
        "current_missing_control_pdb_count": cache["missing_control_pdb_count"],
        "current_valid_control_ccd_cache_hits": cache["valid_control_ccd_hits"],
        "current_missing_control_ccd_count": cache["missing_control_ccd_count"],
        "cache_integrity_failure_count": cache["cache_integrity_failure_count"],
        "cache_integrity_failures": cache["cache_integrity_failures"],
        "cache_snapshot": cache["cache_snapshot"],
        "projected_mean_download_bytes": cache["projected_mean_download_bytes"],
        "projected_p95_download_bytes": projected_p95,
        "hard_total_download_cap_bytes": HARD_TOTAL_DOWNLOAD_CAP_BYTES,
        "pdb_single_payload_cap_bytes": PDB_SINGLE_PAYLOAD_CAP_BYTES,
        "ccd_single_payload_cap_bytes": CCD_SINGLE_PAYLOAD_CAP_BYTES,
        "processing_context_available": True,
        "all_received_network_bytes_budget_enforcement_active": True,
        "controlled_state_root_separation_active": True,
        "leakage_batch_population_count": LEAKAGE_BATCH_POPULATION_COUNT,
        "frozen_control_outcomes_in_leakage_context": 27,
        "implementation_ready_for_publication": ready,
        "controlled_network_execution_publication_gate_currently_satisfied": (
            publication_gate_satisfied
        ),
        "controlled_network_execution_publication_gate_current_reason": (
            publication_gate_reason
        ),
        "network_authorized": False,
        "network_performed": False,
        "cache_modified": False,
        "structural_processing_performed": False,
        "ready_for_controlled_network_execution": ready,
        "training_materialization_performed": False,
        "production_authority_created": False,
    }


@dataclass
class DownloadBudgetV1:
    total_cap_bytes: int = HARD_TOTAL_DOWNLOAD_CAP_BYTES
    network_bytes_received_this_execution: int = 0
    hard_stopped: bool = False

    @property
    def downloaded_this_execution_bytes(self) -> int:
        """Compatibility name; the value is all received network bytes."""

        return self.network_bytes_received_this_execution

    @property
    def remaining_execution_download_budget(self) -> int:
        return self.total_cap_bytes - self.network_bytes_received_this_execution

    def request_limit(self, single_payload_cap_bytes: int) -> int:
        remaining = self.remaining_execution_download_budget
        if self.hard_stopped or remaining <= 0:
            self.hard_stopped = True
            raise ExecutorSafetyError("TOTAL_DOWNLOAD_BUDGET_EXHAUSTED_BEFORE_REQUEST")
        if single_payload_cap_bytes <= 0:
            raise ExecutorSafetyError("SINGLE_PAYLOAD_CAP_INVALID")
        return min(single_payload_cap_bytes, remaining)

    def record_received_bytes(self, byte_count: int) -> None:
        """Charge bytes immediately, independent of validation or persistence."""

        if byte_count < 0:
            raise ExecutorSafetyError("NETWORK_RECEIVED_BYTE_COUNT_INVALID")
        remaining = self.remaining_execution_download_budget
        if byte_count > remaining:
            self.network_bytes_received_this_execution = self.total_cap_bytes
            self.hard_stopped = True
            raise ExecutorSafetyError("TOTAL_NETWORK_BYTE_BUDGET_WOULD_BE_EXCEEDED")
        self.network_bytes_received_this_execution += byte_count

    def record_success(self, byte_count: int, *, request_limit: int) -> None:
        """Backward-compatible helper for callers with an unmetered payload."""

        if byte_count > request_limit:
            self.hard_stopped = True
            raise ExecutorSafetyError("NETWORK_BACKEND_EXCEEDED_REQUEST_BYTE_BOUND")
        self.record_received_bytes(byte_count)


NetworkBackendV1 = Callable[..., bytes]


def official_network_backend_v1(
    *,
    url: str,
    maximum_bytes: int,
    timeout_seconds: int,
    record_received_bytes: Callable[[int], None],
) -> bytes:
    """Read an official payload without ever reading beyond ``maximum_bytes``."""

    if maximum_bytes <= 0:
        raise ExecutorSafetyError("NETWORK_MAXIMUM_BYTES_INVALID")
    request = Request(
        url,
        headers={
            "User-Agent": (
                "CovaPIE-500-event-executor-v1/1.0 "
                "(explicitly-authorized bounded official acquisition)"
            )
        },
        method="GET",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        if int(response.status) != 200:
            raise ExecutorSafetyError("NETWORK_HTTP_STATUS_INVALID")
        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                declared = int(content_length)
            except ValueError as error:
                raise ExecutorSafetyError("NETWORK_CONTENT_LENGTH_INVALID") from error
            if declared < 0 or declared > maximum_bytes:
                raise ExecutorSafetyError("NETWORK_CONTENT_LENGTH_CAP_EXCEEDED")
        chunks: list[bytes] = []
        count = 0
        while count < maximum_bytes:
            chunk = response.read(min(1024 * 1024, maximum_bytes - count))
            if not chunk:
                break
            record_received_bytes(len(chunk))
            count += len(chunk)
            chunks.append(chunk)
        if count == maximum_bytes and content_length is None:
            raise ExecutorSafetyError("NETWORK_STREAM_REACHED_UNVERIFIABLE_HARD_BOUND")
        payload = b"".join(chunks)
        if content_length is not None and len(payload) != int(content_length):
            raise ExecutorSafetyError("NETWORK_CONTENT_LENGTH_BODY_MISMATCH")
        return payload


def _flush_cache_entries(cache_root: Path, entries: Mapping[str, Mapping[str, Any]]) -> None:
    payload = frozen_bulk._canonical_json({
        "schema_version": "covapie_bulk_cache_manifest_v1",
        "snapshot_date": frozen_bulk.SNAPSHOT_DATE,
        "payloads": [entries[key] for key in sorted(entries)],
    })
    frozen_bulk._atomic_write(cache_root / "cache_manifest_v1.json", payload)


def _write_downloaded_cache_payload(
    *,
    cache_root: Path,
    entries: dict[str, dict[str, Any]],
    payload_kind: str,
    identity: str,
    payload: bytes,
) -> dict[str, Any]:
    descriptor = _payload_descriptor(payload_kind, identity)
    relative = descriptor["relative_path"]
    path = cache_root / relative
    if relative in entries or path.exists():
        raise ExecutorSafetyError("CACHE_EXISTING_PAYLOAD_NEVER_OVERWRITTEN:" + relative)
    frozen_bulk.atomic_cache_write_v1(path, payload)
    entry = {
        "relative_path": relative,
        "source_url_or_endpoint": descriptor["url"],
        "source_dataset": frozen_bulk.adapters.SOURCE_RCSB_PDB_DIRECT,
        "retrieval_identity_sha256": _sha(
            frozen_bulk._canonical_json(descriptor["retrieval_identity"])
        ),
        "http_status": 200,
        "byte_count": len(payload),
        "sha256": _sha(payload),
        "validation_status": "SHA256_SIZE_AND_SCIENTIFIC_VALIDATION_PASSED",
        "cache_reuse_status": EXECUTOR_DOWNLOAD_PROVENANCE,
    }
    entries[relative] = entry
    _flush_cache_entries(cache_root, entries)
    return entry


def acquire_payload_v1(
    *,
    repo_root: Path,
    cache_root: Path,
    payload_kind: str,
    identity: str,
    budget: DownloadBudgetV1,
    network_authorized: bool,
    network_backend: NetworkBackendV1 = official_network_backend_v1,
    requested_url: str | None = None,
    inputs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Acquire one allowlisted payload under explicit authorization and caps."""

    if network_authorized is not True:
        raise ExecutorSafetyError("CONTROLLED_NETWORK_EXECUTION_NOT_AUTHORIZED")
    if payload_kind not in {"PDB", "CCD"}:
        raise ExecutorSafetyError("PAYLOAD_KIND_INVALID")
    published = inputs or load_published_executor_inputs_v1(repo_root)
    normalized = identity.upper()
    allowed = (
        published["required_pdb_ids"] if payload_kind == "PDB"
        else published["required_ccd_ids"]
    )
    if normalized not in allowed or normalized != identity:
        raise ExecutorSafetyError("PAYLOAD_IDENTITY_OUTSIDE_PUBLISHED_ALLOWLIST")
    descriptor = _payload_descriptor(payload_kind, normalized)
    if requested_url is not None and requested_url != descriptor["url"]:
        raise ExecutorSafetyError("URL_OUTSIDE_OFFICIAL_PUBLISHED_ALLOWLIST")

    root = cache_root.resolve()
    entries, _available = _load_cache_entries(root)
    relative = descriptor["relative_path"]
    path = root / relative
    if relative in entries or path.exists():
        payload, parsed = _validate_cache_payload(
            cache_root=root,
            entries=entries,
            payload_kind=payload_kind,
            identity=normalized,
        )
        return {
            "payload_kind": payload_kind,
            "identity": normalized,
            "status": "CACHE_REUSED",
            "executor_provenance": REUSED_CACHE_PROVENANCE,
            "byte_count": len(payload),
            "new_download_bytes": 0,
            "payload": payload,
            "parsed": parsed,
        }

    request_limit = budget.request_limit(int(descriptor["maximum_bytes"]))
    received_before = budget.network_bytes_received_this_execution
    request_received = 0

    def record_request_received_bytes(byte_count: int) -> None:
        nonlocal request_received
        if byte_count < 0:
            raise ExecutorSafetyError("NETWORK_RECEIVED_BYTE_COUNT_INVALID")
        if request_received + byte_count > request_limit:
            allowed = request_limit - request_received
            if allowed > 0:
                budget.record_received_bytes(allowed)
                request_received += allowed
            budget.hard_stopped = True
            raise ExecutorSafetyError("NETWORK_BACKEND_EXCEEDED_REQUEST_BYTE_BOUND")
        budget.record_received_bytes(byte_count)
        request_received += byte_count

    try:
        payload = network_backend(
            url=descriptor["url"],
            maximum_bytes=request_limit,
            timeout_seconds=frozen_bulk.NETWORK_TIMEOUT_SECONDS,
            record_received_bytes=record_request_received_bytes,
        )
    except ExecutorSafetyError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise ExecutorSafetyError(
            "NETWORK_BACKEND_FAILED:" + type(error).__name__ + ":" + str(error)
        ) from error
    received_during_call = (
        budget.network_bytes_received_this_execution - received_before
    )
    if not isinstance(payload, bytes):
        raise ExecutorSafetyError("NETWORK_BACKEND_PAYLOAD_TYPE_INVALID")
    if len(payload) > request_limit:
        if received_during_call < request_limit:
            budget.record_received_bytes(request_limit - received_during_call)
        budget.hard_stopped = True
        raise ExecutorSafetyError("NETWORK_BACKEND_EXCEEDED_REQUEST_BYTE_BOUND")
    if received_during_call > len(payload):
        budget.hard_stopped = True
        raise ExecutorSafetyError("NETWORK_BACKEND_BYTE_METER_PAYLOAD_MISMATCH")
    if received_during_call < len(payload):
        budget.record_received_bytes(len(payload) - received_during_call)
    try:
        parsed = _validate_payload_science(payload_kind, normalized, payload)
    except ValueError as error:
        raise ExecutorSafetyError(
            "DOWNLOADED_" + payload_kind + "_SCIENTIFIC_VALIDATION_FAILED:"
            + str(error).split(":", 1)[0]
        ) from error
    entry = _write_downloaded_cache_payload(
        cache_root=root,
        entries=entries,
        payload_kind=payload_kind,
        identity=normalized,
        payload=payload,
    )
    return {
        "payload_kind": payload_kind,
        "identity": normalized,
        "status": "NEWLY_DOWNLOADED",
        "executor_provenance": EXECUTOR_DOWNLOAD_PROVENANCE,
        "legacy_cache_provenance_preserved": False,
        "byte_count": len(payload),
        "new_download_bytes": len(payload),
        "sha256": entry["sha256"],
        "payload": payload,
        "parsed": parsed,
    }


@dataclass(frozen=True)
class AcquisitionExecutionV1:
    result: dict[str, Any]
    pdb_payloads: dict[str, bytes]
    ccd_components: dict[str, dict[str, Any]]


def acquire_required_payloads_v1(
    *,
    repo_root: Path,
    cache_root: Path,
    network_authorized: bool,
    network_backend: NetworkBackendV1 = official_network_backend_v1,
    total_download_cap_bytes: int = HARD_TOTAL_DOWNLOAD_CAP_BYTES,
) -> AcquisitionExecutionV1:
    """Acquire only missing cohort requirements in deterministic PDB/CCD order."""

    if network_authorized is not True:
        raise ExecutorSafetyError("CONTROLLED_NETWORK_EXECUTION_NOT_AUTHORIZED")
    inputs = load_published_executor_inputs_v1(repo_root)
    before = inspect_cache_read_only_v1(
        cache_root=cache_root, inputs=inputs, include_payloads=True
    )
    if before.summary["cache_integrity_failure_count"]:
        raise ExecutorSafetyError("CACHE_INTEGRITY_FAILURE_BLOCKS_ACQUISITION")
    budget = DownloadBudgetV1(total_download_cap_bytes)
    rows: list[dict[str, Any]] = []
    failures: dict[str, str] = {}
    missing_order = [
        *(("PDB", identity) for identity in before.summary["missing_pdb_ids"]),
        *(("CCD", identity) for identity in before.summary["missing_ccd_ids"]),
    ]
    requested_network_count = 0
    for index, (payload_kind, identity) in enumerate(missing_order):
        if budget.hard_stopped or budget.remaining_execution_download_budget <= 0:
            budget.hard_stopped = True
            failures[f"{payload_kind}:{identity}"] = "TOTAL_DOWNLOAD_BUDGET_EXHAUSTED_BEFORE_REQUEST"
            for remaining_kind, remaining_identity in missing_order[index + 1:]:
                failures[f"{remaining_kind}:{remaining_identity}"] = (
                    "NOT_REQUESTED_AFTER_TOTAL_DOWNLOAD_BUDGET_HARD_STOP"
                )
            break
        try:
            requested_network_count += 1
            acquired = acquire_payload_v1(
                repo_root=repo_root,
                cache_root=cache_root,
                payload_kind=payload_kind,
                identity=identity,
                budget=budget,
                network_authorized=True,
                network_backend=network_backend,
                inputs=inputs,
            )
            rows.append({
                key: value
                for key, value in acquired.items()
                if key not in {"payload", "parsed"}
            })
        except (ExecutorSafetyError, OSError) as error:
            failures[f"{payload_kind}:{identity}"] = str(error)
            if budget.hard_stopped:
                for remaining_kind, remaining_identity in missing_order[index + 1:]:
                    failures[f"{remaining_kind}:{remaining_identity}"] = (
                        "NOT_REQUESTED_AFTER_TOTAL_DOWNLOAD_BUDGET_HARD_STOP"
                    )
                break

    after = inspect_cache_read_only_v1(
        cache_root=cache_root, inputs=inputs, include_payloads=True
    )
    downloaded_by_kind = Counter(item["payload_kind"] for item in rows)
    result = {
        "schema_version": SCHEMA_VERSION,
        "mode": CONTROLLED_NETWORK_EXECUTION,
        "acquisition_order": "MISSING_PDB_LEXICOGRAPHIC_THEN_MISSING_CCD_LEXICOGRAPHIC",
        "requested_pdb_count": 290,
        "cache_reused_pdb_count": before.summary["valid_pdb_hits"],
        "newly_downloaded_pdb_count": downloaded_by_kind["PDB"],
        "failed_pdb_count": sum(key.startswith("PDB:") for key in failures),
        "requested_ccd_count": 225,
        "cache_reused_ccd_count": before.summary["valid_ccd_hits"],
        "newly_downloaded_ccd_count": downloaded_by_kind["CCD"],
        "failed_ccd_count": sum(key.startswith("CCD:") for key in failures),
        "network_request_count": requested_network_count,
        "new_download_bytes": budget.downloaded_this_execution_bytes,
        "network_bytes_received_this_execution": (
            budget.network_bytes_received_this_execution
        ),
        "budget_remaining_bytes": budget.remaining_execution_download_budget,
        "hard_total_download_cap_bytes": budget.total_cap_bytes,
        "cache_reuse_executor_provenance": REUSED_CACHE_PROVENANCE,
        "new_download_executor_provenance": EXECUTOR_DOWNLOAD_PROVENANCE,
        "historical_cache_ledger_entries_reauthored": False,
        "network_performed": requested_network_count > 0,
        "cache_modified": (
            before.summary["cache_snapshot"] != after.summary["cache_snapshot"]
        ),
        "post_acquisition_cache_integrity_failure_count": after.summary[
            "cache_integrity_failure_count"
        ],
        "failures": dict(sorted(failures.items())),
        "payload_results": rows,
    }
    return AcquisitionExecutionV1(
        result=result,
        pdb_payloads=after.pdb_payloads,
        ccd_components=after.ccd_components,
    )


def _failed_processing_outcome(event: Mapping[str, Any], reason: str) -> dict[str, Any]:
    phases = {stage: "NOT_REACHED" for stage in frozen_bulk.BULK_STAGES}
    for stage in frozen_bulk.BULK_STAGES[:4]:
        phases[stage] = "PASSED"
    phases[frozen_bulk.BULK_STAGES[4]] = "FAILED_CLOSED"
    return frozen_bulk._terminal_outcome(
        event,
        phases=phases,
        route="STRUCTURAL_EVIDENCE_INCOMPLETE",
        reasons=(reason,),
    )


def process_incremental_250_v1(
    *,
    incremental_records: Sequence[Mapping[str, Any]],
    pdb_payloads: Mapping[str, bytes],
    ccd_components: Mapping[str, Mapping[str, Any]],
    processing_context: ProcessingContextV1,
    frozen_historical_outcomes: Sequence[Mapping[str, Any]],
    frozen_control_outcomes: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Process only ranks 251-500 using already validated payload access."""

    records = list(incremental_records)
    if len(records) != 250 or _ordered_ids_sha256(records) != INCREMENTAL_ORDERED_EVENT_IDS_SHA256:
        raise ExecutorSafetyError("PROCESSING_WORKSET_NOT_EXACT_INCREMENTAL_250")
    historical_ids = {
        str(item["canonical_event_id"]) for item in frozen_historical_outcomes
    }
    control_ids = {
        str(item["canonical_event_id"]) for item in frozen_control_outcomes
    }
    incremental_ids = {str(item["canonical_event_id"]) for item in records}
    if len(historical_ids) != 250:
        raise ExecutorSafetyError("FROZEN_HISTORICAL_LEAKAGE_CONTEXT_COUNT_INVALID")
    if len(control_ids) != 27:
        raise ExecutorSafetyError("FROZEN_CONTROL_LEAKAGE_CONTEXT_COUNT_INVALID")
    if historical_ids & incremental_ids:
        raise ExecutorSafetyError("FROZEN_HISTORICAL_EVENT_ENTERED_INCREMENTAL_LANE")
    if control_ids & (historical_ids | incremental_ids):
        raise ExecutorSafetyError("FROZEN_CONTROL_EVENT_MIXED_WITH_NEW_EVENT_LANES")

    outcomes: list[dict[str, Any]] = []
    for event in records:
        pdb_id = str(event["pdb_id"])
        ccd_id = str(event["ligand_component_id"])
        if pdb_id not in pdb_payloads:
            outcomes.append(_failed_processing_outcome(event, "REQUIRED_PDB_PAYLOAD_UNAVAILABLE"))
            continue
        if ccd_id not in ccd_components:
            outcomes.append(_failed_processing_outcome(event, "REQUIRED_CCD_PAYLOAD_UNAVAILABLE"))
            continue
        outcomes.append(frozen_bulk.process_event_structure_v1(
            event,
            mmcif_payload=pdb_payloads[pdb_id],
            authorities=processing_context.authorities,
            known_historical=processing_context.historical_identities,
            ccd_component=ccd_components[ccd_id],
        ))

    # Historical and control outcomes are copied only to provide cumulative
    # leakage context.  Neither frozen lane is re-authored.
    # Mutations performed by the existing leakage owner are discarded for the
    # frozen predecessor lane; only incremental outcomes are retained.
    historical_context_copy = copy.deepcopy(list(frozen_historical_outcomes))
    control_context_copy = copy.deepcopy(list(frozen_control_outcomes))
    combined_context = [
        *historical_context_copy, *control_context_copy, *outcomes,
    ]
    if len(combined_context) != LEAKAGE_BATCH_POPULATION_COUNT:
        raise ExecutorSafetyError("LEAKAGE_BATCH_POPULATION_COUNT_INVALID")
    frozen_bulk.apply_leakage_predictions_read_only_v1(
        combined_context,
        historical=processing_context.historical_identities,
        context=processing_context.leakage_context,
    )
    frozen_prefix_count = len(historical_context_copy) + len(control_context_copy)
    outcomes = combined_context[frozen_prefix_count:]
    failed_routes = {
        "STRUCTURAL_EVIDENCE_INCOMPLETE",
        "REJECTED_EVENT_INVALID",
        "REJECTED_FEATURE_INCOMPATIBLE",
    }
    route_counts = Counter(str(item["terminal_outcome"]) for item in outcomes)
    failed_closed = sum(item["terminal_outcome"] in failed_routes for item in outcomes)
    metrics = {
        "incremental_events_attempted": len(records),
        "incremental_events_structurally_completed": len(outcomes) - failed_closed,
        "incremental_events_failed_closed": failed_closed,
        "incremental_terminal_route_counts": dict(sorted(route_counts.items())),
        "leakage_batch_population_count": LEAKAGE_BATCH_POPULATION_COUNT,
        "frozen_historical_outcomes_in_leakage_context": 250,
        "frozen_control_outcomes_in_leakage_context": 27,
        "historical_or_control_outcomes_reauthored": False,
        "structural_processing_performed": True,
        "task_domain_successor_routing_performed": False,
    }
    return outcomes, metrics


def finalize_cumulative_view_v1(
    *, inputs: Mapping[str, Any], incremental_outcomes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a lane-labelled view while preserving predecessor outcome bytes."""

    incremental = list(incremental_outcomes)
    expected_ids = [
        str(item["canonical_event_id"]) for item in inputs["incremental_records"]
    ]
    if [str(item["canonical_event_id"]) for item in incremental] != expected_ids:
        raise ExecutorSafetyError("INCREMENTAL_FINALIZATION_IDENTITY_ORDER_MISMATCH")
    cumulative_rows = [
        {
            "scaleup_rank": rank,
            "lane": FROZEN_HISTORICAL_PREDECESSOR,
            "processing_outcome": copy.deepcopy(outcome),
        }
        for rank, outcome in enumerate(inputs["historical_outcomes"], 1)
    ] + [
        {
            "scaleup_rank": rank,
            "lane": NEW_INCREMENTAL_EXECUTION,
            "processing_outcome": copy.deepcopy(outcome),
        }
        for rank, outcome in enumerate(incremental, 251)
    ]
    controls = [
        {
            "lane": KNOWN_EXISTING_CONTROL_REFERENCE,
            "processing_outcome": copy.deepcopy(outcome),
        }
        for outcome in inputs["control_outcomes"]
    ]
    if len(cumulative_rows) != 500 or len(controls) != 27:
        raise ExecutorSafetyError("CUMULATIVE_VIEW_POPULATION_MISMATCH")
    return {
        "schema_version": SCHEMA_VERSION,
        "cumulative_new_event_count": 500,
        "newly_executed_event_count": 250,
        "frozen_predecessor_event_count": 250,
        "known_controls_separate": True,
        "events": cumulative_rows,
        "known_control_references": controls,
        "historical_predecessor_recomputed": False,
        "task_domain_successor_routing_performed": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
    }


def canonical_controlled_cache_root_v1(repo_root: Path) -> Path:
    return (
        repo_root.resolve().parent / DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT
    ).resolve()


def controlled_output_namespace_v1(repo_root: Path) -> Path:
    return (
        repo_root.resolve().parent
        / DEFAULT_CONTROLLED_OUTPUT_RELATIVE_TO_REPOSITORY_PARENT
    ).resolve()


def _same_or_descendant(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_controlled_state_roots_v1(
    *, repo_root: Path, cache_root: Path, output_root: Path,
) -> tuple[Path, Path]:
    """Freeze real controlled writes to disjoint executor-owned namespaces."""

    canonical_cache = canonical_controlled_cache_root_v1(repo_root)
    actual_cache = cache_root.resolve()
    output_namespace = controlled_output_namespace_v1(repo_root)
    actual_output = output_root.resolve()
    if actual_cache != canonical_cache:
        raise ExecutorSafetyError("CONTROLLED_CACHE_ROOT_NOT_CANONICAL")
    if not _same_or_descendant(actual_output, output_namespace):
        raise ExecutorSafetyError("CONTROLLED_OUTPUT_ROOT_OUTSIDE_EXECUTOR_NAMESPACE")
    if (
        _same_or_descendant(actual_output, actual_cache)
        or _same_or_descendant(actual_cache, actual_output)
    ):
        raise ExecutorSafetyError("CONTROLLED_CACHE_OUTPUT_ROOTS_OVERLAP")
    return actual_cache, actual_output


def _write_external_output_fail_closed(path: Path, payload: bytes) -> None:
    """Reuse identical external output bytes and reject conflicting bytes."""

    frozen_bulk.atomic_cache_write_v1(path, payload)


def execute_controlled_network_v1(
    *,
    repo_root: Path,
    cache_root: Path,
    output_root: Path,
    network_authorized: bool,
    network_backend: NetworkBackendV1 = official_network_backend_v1,
) -> dict[str, Any]:
    """Execute the later-authorized additive acquisition and processing flow."""

    if network_authorized is not True:
        raise ExecutorSafetyError("CONTROLLED_NETWORK_EXECUTION_NOT_AUTHORIZED")
    repo_root = repo_root.resolve()
    canonical_cache, target = validate_controlled_state_roots_v1(
        repo_root=repo_root, cache_root=cache_root, output_root=output_root
    )
    verify_controlled_executor_publication_v1(repo_root)
    preflight = preflight_no_network_v1(
        repo_root=repo_root, cache_root=canonical_cache
    )
    if not preflight["ready_for_controlled_network_execution"]:
        raise ExecutorSafetyError("PREFLIGHT_NOT_READY_FOR_CONTROLLED_EXECUTION")
    inputs = load_published_executor_inputs_v1(repo_root)
    acquisition = acquire_required_payloads_v1(
        repo_root=repo_root,
        cache_root=canonical_cache,
        network_authorized=True,
        network_backend=network_backend,
    )
    context = build_processing_context_v1(repo_root)
    outcomes, processing = process_incremental_250_v1(
        incremental_records=inputs["incremental_records"],
        pdb_payloads=acquisition.pdb_payloads,
        ccd_components=acquisition.ccd_components,
        processing_context=context,
        frozen_historical_outcomes=inputs["historical_outcomes"],
        frozen_control_outcomes=inputs["control_outcomes"],
    )
    cumulative = finalize_cumulative_view_v1(
        inputs=inputs, incremental_outcomes=outcomes
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "mode": CONTROLLED_NETWORK_EXECUTION,
        **{
            key: value
            for key, value in acquisition.result.items()
            if key not in {"schema_version", "mode", "payload_results"}
        },
        **processing,
        "network_authorized": True,
        "execution_complete": (
            not acquisition.result["failures"]
            and processing["incremental_events_attempted"] == 250
            and len(outcomes) == 250
        ),
        "external_output_root": target.as_posix(),
        "production_authority_created": False,
        "production_readiness_claimed": False,
        "training_materialization_performed": False,
    }
    target.mkdir(parents=True, exist_ok=True)
    _write_external_output_fail_closed(
        target / CONTROLLED_OUTPUT_FILENAMES[0],
        _json_bytes({
            "schema_version": SCHEMA_VERSION,
            "lane": NEW_INCREMENTAL_EXECUTION,
            "events": outcomes,
            **processing,
        }),
    )
    _write_external_output_fail_closed(
        target / CONTROLLED_OUTPUT_FILENAMES[1], _json_bytes(cumulative)
    )
    _write_external_output_fail_closed(
        target / CONTROLLED_OUTPUT_FILENAMES[2], _json_bytes(result)
    )
    return result


def run_v1(
    *,
    repo_root: Path,
    mode: str = DEFAULT_MODE,
    network_authorized: bool = False,
    cache_root: Path | None = None,
    output_root: Path | None = None,
    network_backend: NetworkBackendV1 = official_network_backend_v1,
) -> dict[str, Any]:
    """Dispatch only the explicitly selected executor mode."""

    repo_root = repo_root.resolve()
    root = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.parent / DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT
    )
    if mode == PREFLIGHT_NO_NETWORK:
        if network_authorized:
            raise ExecutorSafetyError("NETWORK_AUTHORIZATION_INVALID_IN_PREFLIGHT_MODE")
        if output_root is not None:
            raise ExecutorSafetyError("OUTPUT_ROOT_INVALID_IN_PREFLIGHT_MODE")
        return preflight_no_network_v1(repo_root=repo_root, cache_root=root)
    if mode != CONTROLLED_NETWORK_EXECUTION:
        raise ExecutorSafetyError("EXECUTOR_MODE_INVALID")
    if network_authorized is not True:
        raise ExecutorSafetyError("CONTROLLED_NETWORK_EXECUTION_NOT_AUTHORIZED")
    if output_root is None:
        raise ExecutorSafetyError("CONTROLLED_EXTERNAL_OUTPUT_ROOT_REQUIRED")
    validate_controlled_state_roots_v1(
        repo_root=repo_root, cache_root=root, output_root=output_root
    )
    return execute_controlled_network_v1(
        repo_root=repo_root,
        cache_root=root,
        output_root=output_root,
        network_authorized=True,
        network_backend=network_backend,
    )


def verify_synchronized_descendant_repository_v1(repo_root: Path) -> dict[str, Any]:
    """Verify synchronized main and ancestor semantics without exact-HEAD pinning."""

    root = repo_root.resolve()

    def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments),
            cwd=root,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    branch = git("branch", "--show-current").stdout.strip()
    head = git("rev-parse", "HEAD").stdout.strip()
    origin_main = git("rev-parse", "origin/main").stdout.strip()
    ahead, behind = (
        int(value)
        for value in git(
            "rev-list", "--left-right", "--count", "HEAD...origin/main"
        ).stdout.split()
    )
    ancestor_head = git(
        "merge-base", "--is-ancestor", PUBLISHED_EXECUTOR_BASELINE_ANCESTOR, "HEAD",
        check=False,
    ).returncode == 0
    ancestor_origin = git(
        "merge-base", "--is-ancestor", PUBLISHED_EXECUTOR_BASELINE_ANCESTOR, "origin/main",
        check=False,
    ).returncode == 0
    if branch != "main":
        raise ExecutorSafetyError("REPOSITORY_BRANCH_NOT_MAIN")
    if head != origin_main or ahead != 0 or behind != 0:
        raise ExecutorSafetyError("REPOSITORY_NOT_SYNCHRONIZED_WITH_ORIGIN_MAIN")
    if not ancestor_head or not ancestor_origin:
        raise ExecutorSafetyError("PUBLISHED_EXECUTOR_BASELINE_NOT_ANCESTOR")
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "ahead": ahead,
        "behind": behind,
        "published_baseline_ancestor_of_head": ancestor_head,
        "published_baseline_ancestor_of_origin_main": ancestor_origin,
    }


def observe_repository_publication_state_v1(repo_root: Path) -> dict[str, Any]:
    """Observe the clean tracked publication state required for real network work."""

    root = repo_root.resolve()

    def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments),
            cwd=root,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    branch = git("branch", "--show-current").stdout.strip()
    head = git("rev-parse", "HEAD").stdout.strip()
    origin_main = git("rev-parse", "origin/main").stdout.strip()
    ahead, behind = (
        int(value)
        for value in git(
            "rev-list", "--left-right", "--count", "HEAD...origin/main"
        ).stdout.split()
    )
    ancestor_head = git(
        "merge-base", "--is-ancestor", PUBLISHED_EXECUTOR_BASELINE_ANCESTOR,
        "HEAD", check=False,
    ).returncode == 0
    ancestor_origin = git(
        "merge-base", "--is-ancestor", PUBLISHED_EXECUTOR_BASELINE_ANCESTOR,
        "origin/main", check=False,
    ).returncode == 0
    tracked = git(
        "ls-files", "--", *sorted(EXECUTOR_IMPLEMENTATION_PATHS)
    ).stdout.splitlines()
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "ahead": ahead,
        "behind": behind,
        "published_baseline_ancestor_of_head": ancestor_head,
        "published_baseline_ancestor_of_origin_main": ancestor_origin,
        "modified_tracked": git("diff", "--name-only").stdout.splitlines(),
        "staged": git("diff", "--cached", "--name-only").stdout.splitlines(),
        "untracked": git(
            "ls-files", "--others", "--exclude-standard"
        ).stdout.splitlines(),
        "tracked_executor_paths": tracked,
    }


def validate_controlled_publication_observation_v1(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    """Pure fail-closed validator for the real controlled publication gate."""

    if observation.get("branch") != "main":
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_BRANCH_NOT_MAIN")
    if observation.get("head") != observation.get("origin_main"):
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_HEAD_ORIGIN_MISMATCH")
    if observation.get("ahead") != 0 or observation.get("behind") != 0:
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_AHEAD_BEHIND_MISMATCH")
    if not (
        observation.get("published_baseline_ancestor_of_head") is True
        and observation.get("published_baseline_ancestor_of_origin_main") is True
    ):
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_BASELINE_ANCESTRY_INVALID")
    if list(observation.get("modified_tracked", [])):
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_WORKTREE_NOT_CLEAN")
    if list(observation.get("staged", [])):
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_INDEX_NOT_CLEAN")
    if list(observation.get("untracked", [])):
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_UNTRACKED_FILES_PRESENT")
    if set(observation.get("tracked_executor_paths", [])) != set(
        EXECUTOR_IMPLEMENTATION_PATHS
    ):
        raise ExecutorSafetyError("CONTROLLED_PUBLICATION_EXECUTOR_PATHS_NOT_TRACKED")
    return dict(observation)


def verify_controlled_executor_publication_v1(repo_root: Path) -> dict[str, Any]:
    return validate_controlled_publication_observation_v1(
        observe_repository_publication_state_v1(repo_root)
    )
