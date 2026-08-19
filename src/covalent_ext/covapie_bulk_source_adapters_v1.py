"""Canonical source adapters for the CovaPIE bulk CYS-SG pilot V1.

The adapters deliberately separate discovery/supporting annotation from
structure and production-chemistry authority.  Missing source fields remain
``None`` and no specialist annotation can create CovaPIE approval authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import hashlib
import json
import re
from typing import Any


SOURCE_COVPDB = "SOURCE_COVPDB"
SOURCE_COVBINDERINPDB = "SOURCE_COVBINDERINPDB"
SOURCE_COVALENTINDB = "SOURCE_COVALENTINDB"
SOURCE_RCSB_PDB_DIRECT = "SOURCE_RCSB_PDB_DIRECT"

SOURCE_DATASETS = (
    SOURCE_COVPDB,
    SOURCE_COVBINDERINPDB,
    SOURCE_COVALENTINDB,
    SOURCE_RCSB_PDB_DIRECT,
)

DISCOVERY_SOURCE = "DISCOVERY_SOURCE"
STRUCTURE_AUTHORITY_SOURCE = "STRUCTURE_AUTHORITY_SOURCE"
SUPPORTING_CHEMISTRY_ANNOTATION = "SUPPORTING_CHEMISTRY_ANNOTATION"
PRODUCTION_CHEMISTRY_AUTHORITY = "PRODUCTION_CHEMISTRY_AUTHORITY"

LANE_STATUSES = frozenset((
    "OPERATIONAL_BULK_API",
    "OPERATIONAL_OFFICIAL_BULK_DOWNLOAD",
    "OPERATIONAL_STRUCTURED_OFFICIAL_EXPORT",
    "DEFERRED_ACCESS_TERMS_UNRESOLVED",
    "DEFERRED_NO_MACHINE_READABLE_BULK_ACCESS",
    "DEFERRED_NETWORK_UNAVAILABLE",
    "DEFERRED_SOURCE_UNAVAILABLE",
))

CANONICAL_SOURCE_RECORD_FIELDS = (
    "source_dataset",
    "source_record_id",
    "source_snapshot_or_version",
    "source_access_basis",
    "source_payload_sha256",
    "source_record_provenance",
    "pdb_id",
    "protein_chain",
    "protein_residue_name",
    "protein_residue_number",
    "protein_reactive_atom",
    "ligand_component_id",
    "ligand_instance_id",
    "ligand_reactive_atom",
    "source_covalent_event_annotation",
    "source_warhead_annotation",
    "source_reaction_annotation",
    "source_quality_flags",
    "source_fields_missing",
)

_OPTIONAL_SOURCE_RECORD_FIELDS = (
    "canonical_event_id",
    "connection_id",
    "protein_label_asym_id",
    "protein_label_seq_id",
    "protein_auth_asym_id",
    "protein_auth_seq_id",
    "protein_insertion_code",
    "ligand_label_asym_id",
    "ligand_label_seq_id",
    "ligand_auth_asym_id",
    "ligand_auth_seq_id",
    "protein_altloc",
    "ligand_altloc",
    "reported_distance_angstrom",
    "value_order",
    "rcsb_entry_id",
    "rcsb_polymer_instance_id",
    "search_request_sha256",
    "search_result_identity_digest",
    "data_api_endpoint_descriptor",
    "supporting_pre_reaction_smiles",
    "supporting_adduct_smiles",
    "supporting_target_accession",
    "supporting_doi",
)

ACCESS_RESOLUTION_REQUIRED_FIELDS = (
    "source_name",
    "official_home",
    "official_bulk_download_endpoint",
    "official_API_endpoint",
    "current_access_mode",
    "usage_license_terms_source",
    "usage_license_terms_snapshot_sha256",
    "metadata_bulk_access_allowed",
    "programmatic_access_allowed",
    "automated_scraping_allowed",
    "structure_files_directly_provided",
    "PDB_ids_available",
    "current_lane_status",
)

_PDB_ID = re.compile(r"^[0-9][A-Z0-9]{3}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MISSING = {None, "", ".", "?"}
_WATER_COMPONENTS = {"DOD", "HOH", "H2O", "WAT"}
_METAL_COMPONENTS = {
    "AG", "AL", "AU", "BA", "BE", "CA", "CD", "CO", "CR", "CS",
    "CU", "FE", "GA", "HG", "K", "LI", "MG", "MN", "MO", "NA",
    "NI", "PB", "PD", "PT", "RB", "SR", "V", "W", "YB", "ZN",
}


def canonical_json_bytes_v1(value: object) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")


def sha256_bytes_v1(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _clean(value: object) -> str | None:
    if value in _MISSING:
        return None
    text = str(value).strip()
    return None if text in {"", ".", "?"} else text


def _upper(value: object) -> str | None:
    text = _clean(value)
    return text.upper() if text else None


def _float_or_none(value: object) -> float | None:
    text = _clean(value)
    if text is None:
        return None
    try:
        result = float(text)
    except (TypeError, ValueError):
        return None
    return result


def validate_source_access_resolution_v1(record: Mapping[str, Any]) -> None:
    if tuple(sorted(record)) != tuple(sorted(ACCESS_RESOLUTION_REQUIRED_FIELDS)):
        raise ValueError("SOURCE_ACCESS_RESOLUTION_SCHEMA_INVALID")
    if record["source_name"] not in SOURCE_DATASETS:
        raise ValueError("SOURCE_ACCESS_RESOLUTION_SOURCE_INVALID")
    if record["current_lane_status"] not in LANE_STATUSES:
        raise ValueError("SOURCE_ACCESS_RESOLUTION_STATUS_INVALID")
    if not _SHA256.fullmatch(str(record["usage_license_terms_snapshot_sha256"])):
        raise ValueError("SOURCE_ACCESS_RESOLUTION_TERMS_DIGEST_INVALID")
    for field in (
        "metadata_bulk_access_allowed",
        "programmatic_access_allowed",
        "automated_scraping_allowed",
    ):
        if record[field] not in (True, False, "unresolved"):
            raise ValueError("SOURCE_ACCESS_RESOLUTION_TRISTATE_INVALID:" + field)
    for field in ("structure_files_directly_provided", "PDB_ids_available"):
        if type(record[field]) is not bool:
            raise ValueError("SOURCE_ACCESS_RESOLUTION_BOOLEAN_INVALID:" + field)
    status = str(record["current_lane_status"])
    operational = status.startswith("OPERATIONAL_")
    if operational and record["programmatic_access_allowed"] is not True:
        raise ValueError("OPERATIONAL_LANE_PROGRAMMATIC_ACCESS_NOT_ALLOWED")


def _base_record(
    *,
    source_dataset: str,
    source_record_id: object,
    source_snapshot_or_version: object,
    source_access_basis: str,
    source_payload_sha256: str,
    source_record_provenance: Sequence[str],
    pdb_id: object = None,
    protein_chain: object = None,
    protein_residue_name: object = None,
    protein_residue_number: object = None,
    protein_reactive_atom: object = None,
    ligand_component_id: object = None,
    ligand_instance_id: object = None,
    ligand_reactive_atom: object = None,
    source_covalent_event_annotation: object = None,
    source_warhead_annotation: object = None,
    source_reaction_annotation: object = None,
    source_quality_flags: Sequence[str] = (),
    **extra: Any,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source_dataset": source_dataset,
        "source_record_id": _clean(source_record_id),
        "source_snapshot_or_version": _clean(source_snapshot_or_version),
        "source_access_basis": source_access_basis,
        "source_payload_sha256": source_payload_sha256,
        "source_record_provenance": sorted(set(source_record_provenance)),
        "pdb_id": _upper(pdb_id),
        "protein_chain": _clean(protein_chain),
        "protein_residue_name": _upper(protein_residue_name),
        "protein_residue_number": _clean(protein_residue_number),
        "protein_reactive_atom": _upper(protein_reactive_atom),
        "ligand_component_id": _upper(ligand_component_id),
        "ligand_instance_id": _clean(ligand_instance_id),
        "ligand_reactive_atom": _upper(ligand_reactive_atom),
        "source_covalent_event_annotation": _clean(
            source_covalent_event_annotation
        ),
        "source_warhead_annotation": _clean(source_warhead_annotation),
        "source_reaction_annotation": _clean(source_reaction_annotation),
        "source_quality_flags": sorted(set(source_quality_flags)),
        "source_fields_missing": [],
    }
    record.update({field: None for field in _OPTIONAL_SOURCE_RECORD_FIELDS})
    unknown = set(extra) - set(_OPTIONAL_SOURCE_RECORD_FIELDS)
    if unknown:
        raise ValueError("CANONICAL_SOURCE_RECORD_UNKNOWN_EXTRA_FIELDS")
    record.update(extra)
    missing_fields = [
        field for field in CANONICAL_SOURCE_RECORD_FIELDS
        if field not in {"source_fields_missing", "source_quality_flags"}
        and record[field] in (None, [], "")
    ]
    record["source_fields_missing"] = sorted(missing_fields)
    validate_canonical_source_record_v1(record)
    return record


def validate_canonical_source_record_v1(record: Mapping[str, Any]) -> None:
    expected = set(CANONICAL_SOURCE_RECORD_FIELDS) | set(
        _OPTIONAL_SOURCE_RECORD_FIELDS
    )
    if set(record) != expected:
        raise ValueError("CANONICAL_SOURCE_RECORD_SCHEMA_INVALID")
    if record["source_dataset"] not in SOURCE_DATASETS:
        raise ValueError("CANONICAL_SOURCE_RECORD_SOURCE_INVALID")
    if not _clean(record["source_record_id"]):
        raise ValueError("CANONICAL_SOURCE_RECORD_ID_MISSING")
    if not _SHA256.fullmatch(str(record["source_payload_sha256"])):
        raise ValueError("CANONICAL_SOURCE_RECORD_PAYLOAD_SHA_INVALID")
    pdb_id = record["pdb_id"]
    if pdb_id is not None and not _PDB_ID.fullmatch(str(pdb_id)):
        raise ValueError("CANONICAL_SOURCE_RECORD_PDB_ID_INVALID")
    if tuple(record["source_fields_missing"]) != tuple(sorted(
        set(record["source_fields_missing"])
    )):
        raise ValueError("CANONICAL_SOURCE_RECORD_MISSING_FIELDS_INVALID")
    if tuple(record["source_quality_flags"]) != tuple(sorted(
        set(record["source_quality_flags"])
    )):
        raise ValueError("CANONICAL_SOURCE_RECORD_QUALITY_FLAGS_INVALID")
    if PRODUCTION_CHEMISTRY_AUTHORITY in record["source_record_provenance"]:
        raise ValueError("SPECIALIST_OR_RCSB_RECORD_CANNOT_CREATE_PRODUCTION_AUTHORITY")


def normalize_covpdb_ligand_record_v1(
    *, record_id: str, source_payload_sha256: str,
) -> dict[str, Any]:
    """Normalize a ligand-only CovPDB export row without inventing an event."""

    return _base_record(
        source_dataset=SOURCE_COVPDB,
        source_record_id=record_id,
        source_snapshot_or_version="official_export_2021-09-27",
        source_access_basis=(
            "official CovPDB freely-provided All Ligands SDF bulk export"
        ),
        source_payload_sha256=source_payload_sha256,
        source_record_provenance=(DISCOVERY_SOURCE,),
        source_quality_flags=("LIGAND_ONLY_EXPORT_NO_EVENT_MAPPING",),
    )


def normalize_covpdb_complex_seed_v1(
    *,
    record_id: str,
    pdb_id: str,
    source_payload_sha256: str,
    protein_chain: object = None,
    protein_residue_number: object = None,
    ligand_component_id: object = None,
    ligand_instance_id: object = None,
    ligand_reactive_atom: object = None,
    explicit_cys_sg_link: bool = False,
) -> dict[str, Any]:
    """Normalize one official CovPDB complex member without filling gaps.

    A PDB-only archive member is a discovery seed.  A parsed ``LINK`` record
    may additionally carry its literal CYS-SG/ligand endpoints, but it remains
    specialist evidence until an exact current RCSB event is recovered.
    """

    if type(explicit_cys_sg_link) is not bool:
        raise ValueError("COVPDB_EXPLICIT_LINK_FLAG_INVALID")
    flags = () if explicit_cys_sg_link else ("PARTIAL_PDB_SEED_NO_EXACT_EVENT",)
    return _base_record(
        source_dataset=SOURCE_COVPDB,
        source_record_id=record_id,
        source_snapshot_or_version="official_export_2021-09-27",
        source_access_basis=(
            "official CovPDB freely-provided All Complexes PDB ZIP export"
        ),
        source_payload_sha256=source_payload_sha256,
        source_record_provenance=(
            DISCOVERY_SOURCE,
            *((STRUCTURE_AUTHORITY_SOURCE,) if explicit_cys_sg_link else ()),
        ),
        pdb_id=pdb_id,
        protein_chain=protein_chain,
        protein_residue_name="CYS" if explicit_cys_sg_link else None,
        protein_residue_number=protein_residue_number,
        protein_reactive_atom="SG" if explicit_cys_sg_link else None,
        ligand_component_id=ligand_component_id,
        ligand_instance_id=ligand_instance_id,
        ligand_reactive_atom=ligand_reactive_atom,
        source_covalent_event_annotation=(
            "explicit PDB LINK CYS-SG to ligand endpoint"
            if explicit_cys_sg_link else None
        ),
        source_quality_flags=flags,
    )


def normalize_covbinderinpdb_record_v1(
    row: Mapping[str, object], *, source_payload_sha256: str,
) -> dict[str, Any]:
    residue = _clean(row.get("full_residue_name"))
    residue_name = "CYS" if residue == "Cysteine" else residue
    ligand_instance = None
    binder_chain = _clean(row.get("binder_chain_id"))
    binder_number = _clean(row.get("binder_num"))
    if binder_chain or binder_number:
        ligand_instance = ":".join((binder_chain or "?", binder_number or "?"))
    flags: list[str] = []
    if residue_name != "CYS":
        flags.append("OUTSIDE_CYS_BULK_SCOPE")
    return _base_record(
        source_dataset=SOURCE_COVBINDERINPDB,
        source_record_id=row.get("record_id"),
        source_snapshot_or_version="2022Q4",
        source_access_basis=(
            "official CovBinderInPDB Download All Records and Binder Structures ZIP"
        ),
        source_payload_sha256=source_payload_sha256,
        source_record_provenance=(
            DISCOVERY_SOURCE, SUPPORTING_CHEMISTRY_ANNOTATION,
        ),
        pdb_id=row.get("pdb_id"),
        protein_chain=row.get("chain_id"),
        protein_residue_name=residue_name,
        protein_residue_number=row.get("res_num"),
        protein_reactive_atom=None,
        ligand_component_id=row.get("binder_id_in_adduct"),
        ligand_instance_id=ligand_instance,
        ligand_reactive_atom=None,
        source_covalent_event_annotation="curated residue-binder reaction record",
        source_warhead_annotation=row.get("warhead_name"),
        source_reaction_annotation=row.get("binder_type"),
        source_quality_flags=flags,
        supporting_pre_reaction_smiles=_clean(row.get("binder_smiles")),
        supporting_adduct_smiles=_clean(row.get("adduct_smiles")),
        supporting_target_accession=_clean(row.get("unp_accessionid")),
        supporting_doi=_clean(row.get("doi")),
    )


def normalize_covalentindb_record_v1(
    row: Mapping[str, object], *, source_payload_sha256: str,
) -> dict[str, Any]:
    return _base_record(
        source_dataset=SOURCE_COVALENTINDB,
        source_record_id=row.get("record_id"),
        source_snapshot_or_version=row.get("source_version"),
        source_access_basis="official structured export only",
        source_payload_sha256=source_payload_sha256,
        source_record_provenance=(
            DISCOVERY_SOURCE, SUPPORTING_CHEMISTRY_ANNOTATION,
        ),
        pdb_id=row.get("pdb_id"),
        protein_chain=row.get("protein_chain"),
        protein_residue_name=row.get("protein_residue_name"),
        protein_residue_number=row.get("protein_residue_number"),
        protein_reactive_atom=row.get("protein_reactive_atom"),
        ligand_component_id=row.get("ligand_component_id"),
        ligand_instance_id=row.get("ligand_instance_id"),
        ligand_reactive_atom=row.get("ligand_reactive_atom"),
        source_covalent_event_annotation=row.get("covalent_event_annotation"),
        source_warhead_annotation=row.get("warhead_annotation"),
        source_reaction_annotation=row.get("reaction_annotation"),
        source_quality_flags=tuple(row.get("quality_flags", ()) or ()),
    )


def build_canonical_event_id_v1(record: Mapping[str, Any]) -> str:
    required = {
        "pdb_id": _upper(record.get("pdb_id")),
        "protein_instance": _clean(
            record.get("protein_label_asym_id") or record.get("protein_chain")
        ),
        "protein_residue_number": _clean(
            record.get("protein_auth_seq_id")
            or record.get("protein_residue_number")
            or record.get("protein_label_seq_id")
        ),
        "ligand_instance": _clean(
            record.get("ligand_label_asym_id")
            or record.get("ligand_instance_id")
        ),
        "ligand_component_id": _upper(record.get("ligand_component_id")),
        "ligand_reactive_atom": _upper(record.get("ligand_reactive_atom")),
    }
    if not all(required.values()):
        raise ValueError("CANONICAL_EVENT_IDENTITY_INCOMPLETE")
    if _upper(record.get("protein_residue_name")) != "CYS":
        raise ValueError("CANONICAL_EVENT_PROTEIN_NOT_CYS")
    if _upper(record.get("protein_reactive_atom")) != "SG":
        raise ValueError("CANONICAL_EVENT_PROTEIN_ATOM_NOT_SG")
    insertion = _clean(record.get("protein_insertion_code")) or "-"
    return ":".join((
        "COVAPIE_CYS_SG_EVENT_V1",
        str(required["pdb_id"]),
        str(required["protein_instance"]),
        "CYS",
        str(required["protein_residue_number"]) + insertion,
        "SG",
        str(required["ligand_instance"]),
        str(required["ligand_component_id"]),
        str(required["ligand_reactive_atom"]),
    ))


def _rcsb_endpoint(endpoint: Mapping[str, Any] | None) -> dict[str, Any]:
    endpoint = endpoint or {}
    return {
        "auth_asym_id": _clean(endpoint.get("auth_asym_id")),
        "auth_seq_id": _clean(endpoint.get("auth_seq_id")),
        "label_alt_id": _clean(endpoint.get("label_alt_id")),
        "label_asym_id": _clean(endpoint.get("label_asym_id")),
        "label_atom_id": _upper(endpoint.get("label_atom_id")),
        "label_comp_id": _upper(endpoint.get("label_comp_id")),
        "label_seq_id": _clean(endpoint.get("label_seq_id")),
        "symmetry": _clean(endpoint.get("symmetry")),
    }


def exact_cys_sg_rcsb_connection_v1(
    connection: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    connect_type = (_clean(connection.get("connect_type")) or "").lower()
    if connect_type not in {"covalent bond", "covalent residue modification"}:
        return None
    target = _rcsb_endpoint(connection.get("connect_target"))
    partner = _rcsb_endpoint(connection.get("connect_partner"))
    endpoints = ((target, partner), (partner, target))
    for protein, ligand in endpoints:
        if not (
            protein["label_comp_id"] == "CYS"
            and protein["label_atom_id"] == "SG"
        ):
            continue
        # A non-polymer endpoint has no label_seq_id in the RCSB Data model.
        if ligand["label_seq_id"] is not None:
            continue
        component = ligand["label_comp_id"]
        if (
            not component
            or component in _WATER_COMPONENTS
            or component in _METAL_COMPONENTS
            or (component == "CYS" and ligand["label_atom_id"] == "SG")
        ):
            continue
        if not ligand["label_asym_id"] or not ligand["label_atom_id"]:
            continue
        return protein, ligand
    return None


def normalize_rcsb_connection_record_v1(
    *,
    entry_id: str,
    polymer_instance_id: str,
    connection: Mapping[str, Any],
    source_payload_sha256: str,
    search_request_sha256: str,
    search_result_identity_digest: str,
    data_api_endpoint_descriptor: str,
) -> dict[str, Any] | None:
    endpoints = exact_cys_sg_rcsb_connection_v1(connection)
    if endpoints is None:
        return None
    protein, ligand = endpoints
    protein_instance = protein["label_asym_id"] or polymer_instance_id.rsplit(
        ".", 1
    )[-1]
    protein_number = protein["auth_seq_id"] or protein["label_seq_id"]
    ligand_instance = ligand["label_asym_id"]
    record = _base_record(
        source_dataset=SOURCE_RCSB_PDB_DIRECT,
        source_record_id=f"{entry_id.upper()}:{connection.get('id')}",
        source_snapshot_or_version="RCSB_API_SNAPSHOT_2026-08-19",
        source_access_basis="official RCSB Search and Data APIs; CC0",
        source_payload_sha256=source_payload_sha256,
        source_record_provenance=(
            DISCOVERY_SOURCE, STRUCTURE_AUTHORITY_SOURCE,
        ),
        pdb_id=entry_id,
        protein_chain=protein_instance,
        protein_residue_name="CYS",
        protein_residue_number=protein_number,
        protein_reactive_atom="SG",
        ligand_component_id=ligand["label_comp_id"],
        ligand_instance_id=ligand_instance,
        ligand_reactive_atom=ligand["label_atom_id"],
        source_covalent_event_annotation=connection.get("connect_type"),
        source_quality_flags=(),
        connection_id=_clean(connection.get("id")),
        protein_label_asym_id=protein["label_asym_id"],
        protein_label_seq_id=protein["label_seq_id"],
        protein_auth_asym_id=protein["auth_asym_id"],
        protein_auth_seq_id=protein["auth_seq_id"],
        protein_insertion_code=None,
        ligand_label_asym_id=ligand["label_asym_id"],
        ligand_label_seq_id=ligand["label_seq_id"],
        ligand_auth_asym_id=ligand["auth_asym_id"],
        ligand_auth_seq_id=ligand["auth_seq_id"],
        protein_altloc=protein["label_alt_id"],
        ligand_altloc=ligand["label_alt_id"],
        reported_distance_angstrom=_float_or_none(connection.get("dist_value")),
        value_order=_clean(connection.get("value_order")),
        rcsb_entry_id=entry_id.upper(),
        rcsb_polymer_instance_id=polymer_instance_id,
        search_request_sha256=search_request_sha256,
        search_result_identity_digest=search_result_identity_digest,
        data_api_endpoint_descriptor=data_api_endpoint_descriptor,
    )
    record["canonical_event_id"] = build_canonical_event_id_v1(record)
    validate_canonical_source_record_v1(record)
    return record


def specialist_matches_rcsb_event_v1(
    specialist: Mapping[str, Any], rcsb: Mapping[str, Any],
) -> bool:
    matches, _reason = resolve_specialist_event_mapping_v1(
        specialist, (rcsb,), pdb_recovery_status="EXAMINED",
    )
    return len(matches) == 1


def resolve_specialist_event_mapping_v1(
    specialist: Mapping[str, Any],
    rcsb_records: Sequence[Mapping[str, Any]],
    *,
    pdb_recovery_status: str,
) -> tuple[list[Mapping[str, Any]], str]:
    """Map a specialist seed to exact RCSB events using every known field."""

    pdb_id = _upper(specialist.get("pdb_id"))
    if not pdb_id:
        return [], "SPECIALIST_EVENT_MAPPING_INCOMPLETE"
    if pdb_recovery_status == "NOT_AVAILABLE":
        return [], "SPECIALIST_PDB_NOT_AVAILABLE"
    pdb_events = [
        item for item in rcsb_records if _upper(item.get("pdb_id")) == pdb_id
    ]
    if not pdb_events:
        return [], "SPECIALIST_PDB_NO_EXACT_CYS_SG_EVENT"
    component = _upper(specialist.get("ligand_component_id"))
    if not component:
        return [], "SPECIALIST_EVENT_MAPPING_INCOMPLETE"
    ligand_events = [
        item for item in pdb_events
        if _upper(item.get("ligand_component_id")) == component
    ]
    if not ligand_events:
        return [], "SPECIALIST_LIGAND_NOT_FOUND_IN_EXACT_EVENT"

    residue = _clean(specialist.get("protein_residue_number"))
    specialist_chain = _clean(specialist.get("protein_chain"))
    reactive_atom = _upper(specialist.get("ligand_reactive_atom"))
    ligand_instance = _clean(specialist.get("ligand_instance_id"))
    instance_chain: str | None = None
    instance_number: str | None = None
    if ligand_instance:
        parts = ligand_instance.split(":", 1)
        instance_chain = _clean(parts[0])
        instance_number = _clean(parts[1]) if len(parts) == 2 else None

    matches: list[Mapping[str, Any]] = []
    for rcsb in ligand_events:
        if residue and residue not in {
            _clean(rcsb.get("protein_residue_number")),
            _clean(rcsb.get("protein_label_seq_id")),
            _clean(rcsb.get("protein_auth_seq_id")),
        }:
            continue
        protein_chains = {
            _clean(rcsb.get("protein_chain")),
            _clean(rcsb.get("protein_label_asym_id")),
            _clean(rcsb.get("protein_auth_asym_id")),
        } - {None}
        if specialist_chain and specialist_chain not in protein_chains:
            continue
        if reactive_atom and reactive_atom != _upper(
            rcsb.get("ligand_reactive_atom")
        ):
            continue
        ligand_label_chains = {
            _clean(rcsb.get("ligand_instance_id")),
            _clean(rcsb.get("ligand_label_asym_id")),
        } - {None}
        ligand_auth_chain = _clean(rcsb.get("ligand_auth_asym_id"))
        ligand_numbers = {
            _clean(rcsb.get("ligand_label_seq_id")),
            _clean(rcsb.get("ligand_auth_seq_id")),
        } - {None}
        if instance_chain and instance_chain != "?":
            if ligand_auth_chain and instance_chain not in {
                ligand_auth_chain, *ligand_label_chains,
            }:
                continue
            # The Data API connection partner exposes label asymmetry only.
            # A specialist auth-chain value cannot be declared conflicting
            # when no auth-asym value exists in the exact RCSB record.
        if (
            instance_number and instance_number != "?" and ligand_numbers
            and instance_number not in ligand_numbers
        ):
            continue
        matches.append(rcsb)
    event_ids = sorted(set(str(item["canonical_event_id"]) for item in matches))
    exact = [
        next(item for item in matches if item["canonical_event_id"] == event_id)
        for event_id in event_ids
    ]
    if len(exact) == 1:
        return exact, "SPECIALIST_EXACT_EVENT_RESOLVED"
    if len(exact) > 1:
        return exact, "SPECIALIST_EVENT_MAPPING_AMBIGUOUS"
    return [], "SPECIALIST_EVENT_MAPPING_INCOMPLETE"


def merge_cross_source_events_v1(
    rcsb_records: Sequence[Mapping[str, Any]],
    specialist_records: Sequence[Mapping[str, Any]],
    *,
    specialist_pdb_statuses: Mapping[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Merge exact RCSB events and compatible specialist records once."""

    by_event: dict[str, list[Mapping[str, Any]]] = {}
    for record in rcsb_records:
        event_id = _clean(record.get("canonical_event_id"))
        if not event_id:
            raise ValueError("RCSB_CANONICAL_EVENT_ID_MISSING")
        by_event.setdefault(event_id, []).append(record)
    unmatched: list[dict[str, Any]] = []
    for record in specialist_records:
        pdb_id = str(record.get("pdb_id") or "").upper()
        status = (specialist_pdb_statuses or {}).get(pdb_id, "EXAMINED")
        matches, reason = resolve_specialist_event_mapping_v1(
            record, rcsb_records, pdb_recovery_status=status,
        )
        event_ids = sorted(set(
            str(item["canonical_event_id"]) for item in matches
        ))
        if len(event_ids) == 1:
            by_event[event_ids[0]].append(record)
        else:
            unmatched.append({
                "source_dataset": record["source_dataset"],
                "source_record_id": record["source_record_id"],
                "pdb_id": record["pdb_id"],
                "ligand_component_id": record["ligand_component_id"],
                "reason": reason,
            })
    merged: list[dict[str, Any]] = []
    for event_id, records in sorted(by_event.items()):
        ordered = sorted(records, key=lambda item: (
            str(item["source_dataset"]), str(item["source_record_id"]),
        ))
        rcsb = next(
            item for item in ordered
            if item["source_dataset"] == SOURCE_RCSB_PDB_DIRECT
        )
        sources = sorted(set(str(item["source_dataset"]) for item in ordered))
        annotations = sorted({
            json.dumps({
                "source_dataset": item["source_dataset"],
                "source_record_id": item["source_record_id"],
                "covalent_event": item["source_covalent_event_annotation"],
                "warhead": item["source_warhead_annotation"],
                "reaction": item["source_reaction_annotation"],
            }, sort_keys=True, separators=(",", ":"))
            for item in ordered
        })
        warheads = sorted(set(
            str(item["source_warhead_annotation"])
            for item in ordered if item["source_warhead_annotation"]
        ))
        reactions = sorted(set(
            str(item["source_reaction_annotation"])
            for item in ordered if item["source_reaction_annotation"]
        ))
        conflict_fields: list[str] = []
        if len(warheads) > 1:
            conflict_fields.append("source_warhead_annotation")
        if len(reactions) > 1:
            conflict_fields.append("source_reaction_annotation")
        supporting = [
            item for item in ordered
            if item["source_dataset"] != SOURCE_RCSB_PDB_DIRECT
        ]
        merged.append({
            "canonical_event_id": event_id,
            "pdb_id": rcsb["pdb_id"],
            "protein_instance": rcsb["protein_label_asym_id"],
            "protein_auth_chain": rcsb["protein_auth_asym_id"],
            "protein_residue_name": "CYS",
            "protein_residue_number": rcsb["protein_residue_number"],
            "protein_reactive_atom": "SG",
            "ligand_instance": rcsb["ligand_label_asym_id"],
            "ligand_component_id": rcsb["ligand_component_id"],
            "ligand_reactive_atom": rcsb["ligand_reactive_atom"],
            "connection_ids": sorted(set(
                str(item["connection_id"])
                for item in ordered if item.get("connection_id")
            )),
            "source_count": len(sources),
            "source_record_count": len(ordered),
            "source_datasets": sources,
            "source_record_ids": sorted({
                str(item["source_dataset"]) + ":" + str(item["source_record_id"])
                for item in ordered
            }),
            "source_payload_sha256s": sorted(set(
                str(item["source_payload_sha256"]) for item in ordered
            )),
            "source_annotations": [json.loads(item) for item in annotations],
            "source_specific_missing_fields": [
                {
                    "source_dataset": item["source_dataset"],
                    "source_record_id": item["source_record_id"],
                    "fields": item["source_fields_missing"],
                }
                for item in ordered
            ],
            "annotation_conflict_fields": sorted(conflict_fields),
            "source_annotation_conflict": bool(conflict_fields),
            "supporting_warhead_annotations": warheads,
            "supporting_reaction_annotations": reactions,
            "supporting_pre_reaction_smiles": sorted(set(
                str(item["supporting_pre_reaction_smiles"])
                for item in supporting if item.get("supporting_pre_reaction_smiles")
            )),
            "supporting_adduct_smiles": sorted(set(
                str(item["supporting_adduct_smiles"])
                for item in supporting if item.get("supporting_adduct_smiles")
            )),
            "supporting_target_accessions": sorted(set(
                str(item["supporting_target_accession"])
                for item in supporting if item.get("supporting_target_accession")
            )),
            "rcsb_structure_authority": {
                "connection_id": rcsb["connection_id"],
                "protein_altloc": rcsb["protein_altloc"],
                "ligand_altloc": rcsb["ligand_altloc"],
                "reported_distance_angstrom": rcsb[
                    "reported_distance_angstrom"
                ],
                "data_api_endpoint_descriptor": rcsb[
                    "data_api_endpoint_descriptor"
                ],
            },
        })
    return merged, sorted(unmatched, key=lambda item: (
        str(item["source_dataset"]), str(item["source_record_id"]),
    ))


def adapter_registry_v1() -> dict[str, Any]:
    return {
        SOURCE_COVPDB: normalize_covpdb_ligand_record_v1,
        SOURCE_COVBINDERINPDB: normalize_covbinderinpdb_record_v1,
        SOURCE_COVALENTINDB: normalize_covalentindb_record_v1,
        SOURCE_RCSB_PDB_DIRECT: normalize_rcsb_connection_record_v1,
    }


def validate_shared_adapter_contract_v1(
    records: Iterable[Mapping[str, Any]],
) -> None:
    for record in records:
        validate_canonical_source_record_v1(record)
