"""Recover exact structural evidence for the 12 open Cys-SG Stage-A rows.

This successor is deliberately bounded.  It verifies the published Stage-A
artifacts, searches existing local files, and reuses published mmCIF,
``struct_conn``, atom-site, altloc, PDB LINK, and Exact10 owners.  It never
downloads data, infers a reactive pair from distance, creates Geometry, loads
a model, or trains.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import stat
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_covpdb_raw_structure_event_annotation_smoke as pdb_event_owner,
)
from covalent_ext import (
    covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1
    as stage_a,
)
from covalent_ext import (
    covapie_cys_sg_future_struct_conn_crosscheck_execution_gate
    as struct_conn_owner,
)
from covalent_ext import (
    real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun
    as atom_site_owner,
)

__all__ = (
    "ExactEventRecoveryDecision",
    "LocalEvidenceLookup",
    "build_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_artifacts_v1",
    "classify_unrecovered_evidence_v1",
    "lookup_local_evidence_v1",
    "materialize_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1",
    "recover_exact_struct_conn_event_v1",
)

SCHEMA_VERSION = (
    "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1"
)
PUBLISHED_STAGE_A_COMMIT = "19d07143c41026bb5a54bc1e02d81ac1d649dd76"
BASELINE_COMMIT = PUBLISHED_STAGE_A_COMMIT
REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"

STAGE_A_ROOT = (
    Path("data/derived/covalent_small")
    / "covapie_cys_sg_expanded_source_candidate_inventory_and_"
    "canonical_eligibility_v1"
)
STAGE_A_CANDIDATE = STAGE_A_ROOT / stage_a.CANDIDATE_FILE
STAGE_A_ISSUE = STAGE_A_ROOT / stage_a.ISSUE_FILE
STAGE_A_MANIFEST = STAGE_A_ROOT / stage_a.MANIFEST_FILE
PUBLISHED_STAGE_A_SHA256: Mapping[Path, str] = {
    STAGE_A_CANDIDATE:
        "c6ccbb6cdbfaffde501e53d03acfe11daca8bf35262e5287db5516e8952eaa28",
    STAGE_A_ISSUE:
        "4448369c937da656de2a8b64b0cb32cdb5ab3faeff8ef12a18869a7787012d41",
    STAGE_A_MANIFEST:
        "97af04623f473fbdbcdeb881bbfdb7cdab89bad0738895f65fb48a9dc7444236",
}

HISTORICAL_RAW_DOWNLOAD_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_covpdb_raw_structure_event_annotation_smoke_v0/"
    "covapie_raw_structure_download_audit.csv"
)
HISTORICAL_STRUCT_CONN_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_covpdb_raw_structure_event_annotation_smoke_v0/"
    "covapie_mmcif_struct_conn_inventory.csv"
)
HISTORICAL_PDB_CONNECTION_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_covpdb_raw_structure_event_annotation_smoke_v0/"
    "covapie_pdb_link_conect_inventory.csv"
)
HISTORICAL_ATOM_SITE_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_covpdb_raw_structure_event_annotation_smoke_v0/"
    "covapie_mmcif_atom_site_validation_audit.csv"
)
HISTORICAL_CROSSCHECK_PARSE_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate_v0/"
    "covapie_cys_sg_raw_struct_conn_parse_audit.csv"
)
BOUNDED_ACQUISITION_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_"
    "acquisition_gate_v0/"
    "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_"
    "manifest.json"
)
BOUNDED_ACQUISITION_POLICY = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_"
    "acquisition_gate_v0/covapie_cys_sg_controlled_raw_acquisition_"
    "policy_contract.csv"
)
BOUNDED_ACQUISITION_REQUESTS = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_"
    "acquisition_gate_v0/covapie_cys_sg_controlled_raw_acquisition_"
    "request_manifest.csv"
)
BULK_AUTHORIZATION_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_download_authorization_"
    "contract_v1/covapie_admit_014_download_authorization_contract_"
    "manifest.json"
)

FROZEN_LOCAL_AUTHORITY_SHA256: Mapping[Path, str] = {
    HISTORICAL_RAW_DOWNLOAD_AUDIT:
        "d379b116e90f3f5758c7fd3af3ae0769c3d4642e7349d244121e8f6437cc3262",
    HISTORICAL_STRUCT_CONN_AUDIT:
        "aede7be05b7428ba476f9d781d4fb192ac58231dbca5be1ee62a8b17b224ad17",
    HISTORICAL_PDB_CONNECTION_AUDIT:
        "3574bd9d586425eeb42692e2e2ed93db6b19a97b4269b94c4862bce3c8b1bcf5",
    HISTORICAL_ATOM_SITE_AUDIT:
        "0985ef31a6ccf227ce69ba199b4cd66a6e6237b0aba0624056fa9078552622bf",
    HISTORICAL_CROSSCHECK_PARSE_AUDIT:
        "3a2bb143062d639600f19041e2ee830438e71069850d7583624e5b07d6e58ca6",
    BOUNDED_ACQUISITION_MANIFEST:
        "4c2de6e2ef662dd0e28bf98eb36b84a9eebd4f1f95feab9b699a78dc46367f19",
    BOUNDED_ACQUISITION_POLICY:
        "170ba9f59229c0529dff35d4c09414fdbcc4a16cfa2ba372d0ffa234f3104bac",
    BOUNDED_ACQUISITION_REQUESTS:
        "0db05f8ef79c595aa388e0cbb88684d77c8f2881c63c9eb0da9f2be16943254a",
    BULK_AUTHORIZATION_MANIFEST:
        "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
}

RECOVERY_IDENTITIES = (
    ("1A54", "MDC"),
    ("2DJF", "1ZB"),
    ("6VWE", "JY1"),
    ("2R9F", "K2Z"),
    ("4DCD", "K36"),
    ("6WTT", "K36"),
    ("4F49", "K36"),
    ("6L70", "K36"),
    ("6WTJ", "K36"),
    ("7C8U", "K36"),
    ("5WKJ", "K36"),
    ("6WTK", "UED"),
)
K36_UED_IDENTITIES = RECOVERY_IDENTITIES[4:]
ELIGIBLE_CONTROL_IDENTITIES = {
    ("6DI9", "GJJ"), ("5F2E", "5UT"), ("6OIM", "MOV"),
}
REJECT_IDENTITIES = {("1ATK", "E64"), ("6BV9", "JUG")}

RECOVERY_DISPOSITIONS = (
    "AUTO_RECOVERED_STAGE_B_ELIGIBLE",
    "AUTO_RECOVERED_BUT_DOWNSTREAM_LABEL_REVIEW_REQUIRED",
    "HUMAN_STRUCTURAL_REVIEW_REQUIRED",
    "TARGETED_EXTERNAL_ACQUISITION_REQUIRED",
    "REJECT",
)
WORKLIST_CATEGORIES = (
    "TARGETED_EXTERNAL_ACQUISITION_REQUIRED",
    "HUMAN_STRUCTURAL_REVIEW_REQUIRED",
    "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_REQUIRED",
)

OUTPUT_ROOT = (
    Path("data/derived/covalent_small")
    / "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1"
)
RECOVERY_FILE = "covapie_cys_sg_stage_b0_recovery_matrix.csv"
WORKLIST_FILE = "covapie_cys_sg_stage_b0_acquisition_and_review_worklist.csv"
MANIFEST_FILE = (
    "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_"
    "manifest.json"
)
OUTPUT_FILES = (RECOVERY_FILE, WORKLIST_FILE, MANIFEST_FILE)

RECOVERY_COLUMNS = (
    "canonical_candidate_id", "pdb_id", "ligand_component_id",
    "stage_a_disposition", "stage_a_primary_issue",
    "stage_a_expected_protein_chain", "stage_a_expected_cys_residue_sequence",
    "local_raw_structure_found", "raw_structure_identity",
    "local_structure_path_or_authority", "raw_structure_sha256_or_NONE",
    "explicit_connection_evidence_status", "cys_sg_event_recovered",
    "protein_chain", "cys_residue_sequence", "cys_insertion_code",
    "reactive_residue_atom", "ligand_chain_or_instance",
    "ligand_sequence_or_instance", "reactive_ligand_atom",
    "coordinate_status", "altloc_occupancy_provenance",
    "parent_post_topology_status", "canonical_model_graph_status",
    "exact10_status", "pocket_readiness_status",
    "structural_recovery_status", "recovery_disposition",
    "downstream_label_authority_status", "acquisition_authorization_status",
    "primary_remaining_issue", "recovery_mechanism_group",
    "canonical_sample_authority_created",
)
WORKLIST_COLUMNS = (
    "worklist_item_id", "canonical_candidate_id", "pdb_id",
    "ligand_component_id", "worklist_category",
    "required_missing_artifact_or_evidence",
    "existing_project_acquisition_authorization_status",
    "authorization_evidence_authority", "bulk_download_authorization_status",
    "next_manual_or_acquisition_action", "canonical_sample_authority_created",
)

FULL_STRUCTURE_SUFFIXES = {".cif", ".mmcif", ".pdb"}
TOPOLOGY_SUFFIXES = {".sdf", ".mol", ".mol2"}
HISTORICAL_1A54_RAW_SHA256 = (
    "72027fd8250ab981a082a8081f7624ca81f2cc78dfeaba8ea124a3ead1543d11"
)
RECOMMENDED_NEXT_STEP = (
    "review_and_publish_covapie_cys_sg_stage_b0_open_candidate_structural_"
    "evidence_recovery_v1"
)


@dataclass(frozen=True)
class LocalEvidenceLookup:
    raw_structure_paths: tuple[Path, ...]
    derived_structure_paths: tuple[Path, ...]
    topology_paths: tuple[Path, ...]


@dataclass(frozen=True)
class ExactEventRecoveryDecision:
    recovered: bool
    status: str
    explicit_connection_evidence_status: str
    fundamental_reject: bool = False
    protein_chain: str = "NONE"
    cys_residue_sequence: str = "NONE"
    cys_insertion_code: str = "NONE"
    ligand_chain_or_instance: str = "NONE"
    ligand_sequence_or_instance: str = "NONE"
    reactive_ligand_atom: str = "NONE"
    coordinate_status: str = "COORDINATE_EVIDENCE_INCOMPLETE"
    altloc_occupancy_provenance: str = "NONE"
    protein_coordinates: tuple[float, float, float] | None = None
    ligand_coordinates: tuple[float, float, float] | None = None


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _verify(payload: bytes, expected: str, identity: str) -> None:
    if _sha256(payload) != expected:
        raise ValueError(f"STAGE_B0_SOURCE_SHA_MISMATCH:{identity}")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(
    rows: Sequence[Mapping[str, Any]], columns: Sequence[str],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="raise", lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            column: str(row[column]).lower()
            if isinstance(row[column], bool) else row[column]
            for column in columns
        })
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False, indent=2,
    ) + "\n").encode("utf-8")


def _clean(value: object) -> str:
    text = str(value or "")
    return "" if text in {".", "?", "NONE"} else text


def _none(value: object) -> str:
    return _clean(value) or "NONE"


def _truth(value: object) -> bool:
    return value is True or str(value).lower() == "true"


def _path_identity(path: Path, repo_root: Path, state_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return "state://" + path.relative_to(state_root).as_posix()


def _identity_in_filename(path: Path, identity: str) -> bool:
    return re.search(
        rf"(^|[^A-Za-z0-9]){re.escape(identity)}([^A-Za-z0-9]|$)",
        path.stem,
        flags=re.IGNORECASE,
    ) is not None


def _bounded_files(root: Path) -> tuple[Path, ...]:
    if not root.is_dir():
        return ()
    return tuple(sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.as_posix(),
    ))


def lookup_local_evidence_v1(
    pdb_id: str,
    ligand_component_id: str,
    *,
    repo_root: Path = REPO_ROOT,
    state_root: Path = STATE_ROOT,
) -> LocalEvidenceLookup:
    """Return deterministic candidate-specific local structure evidence."""

    raw_files = _bounded_files(repo_root / "data/raw")
    derived_files = _bounded_files(repo_root / "data/derived")
    state_files = _bounded_files(state_root)
    raw_paths = sorted(
        path for path in (*raw_files, *state_files)
        if path.suffix.lower() in FULL_STRUCTURE_SUFFIXES
        and _identity_in_filename(path, pdb_id)
    )
    derived_paths = sorted(
        path for path in derived_files
        if path.suffix.lower() in FULL_STRUCTURE_SUFFIXES
        and _identity_in_filename(path, pdb_id)
    )
    topology_paths = sorted(
        path for path in (*raw_files, *derived_files, *state_files)
        if path.suffix.lower() in TOPOLOGY_SUFFIXES
        and (
            _identity_in_filename(path, pdb_id)
            or _identity_in_filename(path, ligand_component_id)
        )
    )
    return LocalEvidenceLookup(
        tuple(raw_paths), tuple(derived_paths), tuple(topology_paths),
    )


def _side_altloc(record: Mapping[str, str], side: str) -> str:
    return _clean(
        record.get(f"_struct_conn.pdbx_{side}_label_alt_id", "")
        or record.get(f"_struct_conn.{side}_label_alt_id", "")
    )


def _side_insertion(record: Mapping[str, str], side: str) -> str:
    return _none(record.get(f"_struct_conn.pdbx_{side}_PDB_ins_code", ""))


def _contract_row(side: Mapping[str, str], role: str) -> dict[str, str]:
    atom = side["atom_id"]
    return {
        "endpoint_role": role,
        "endpoint_label_asym_id": side["label_asym_id"],
        "endpoint_label_comp_id": side["comp_id"],
        "endpoint_label_seq_id": side["label_seq_id"],
        "endpoint_label_atom_id": atom,
        "endpoint_auth_asym_id": side["auth_asym_id"],
        "endpoint_auth_comp_id": side["comp_id"],
        "endpoint_auth_seq_id": side["auth_seq_id"],
        "endpoint_auth_atom_id": atom,
    }


def _atom_value(row: Mapping[str, str], field: str) -> str:
    return _clean(row.get("_atom_site." + field, ""))


def _finite_atom_rows(rows: Sequence[dict[str, str]]) -> bool:
    for row in rows:
        try:
            values = [float(_atom_value(row, axis)) for axis in (
                "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
            )]
        except ValueError:
            return False
        if not all(math.isfinite(value) for value in values):
            return False
    return True


def _filter_explicit_altloc(
    rows: Sequence[dict[str, str]], altloc: str,
) -> list[dict[str, str]]:
    if not altloc:
        return list(rows)
    return [row for row in rows if _atom_value(row, "label_alt_id") == altloc]


def _pair_semantic_key(
    protein: Mapping[str, str], ligand: Mapping[str, str], reported: float,
) -> tuple[float, int, float, int]:
    def coordinate(row: Mapping[str, str], axis: str) -> float:
        return float(_atom_value(row, axis))

    distance = math.sqrt(sum(
        (coordinate(protein, axis) - coordinate(ligand, axis)) ** 2
        for axis in ("Cartn_x", "Cartn_y", "Cartn_z")
    ))
    model_rank = sum(
        0 if _atom_value(row, "pdbx_PDB_model_num") in {"", "1"} else 1
        for row in (protein, ligand)
    )
    occupancy_rank = -sum(
        float(_atom_value(row, "occupancy")) for row in (protein, ligand)
    )
    ligand_altloc_rank = 0 if not _atom_value(ligand, "label_alt_id") else 1
    return (round(abs(distance - reported), 10), model_rank,
            occupancy_rank, ligand_altloc_rank)


def _coordinates(row: Mapping[str, str]) -> tuple[float, float, float]:
    return tuple(float(_atom_value(row, axis)) for axis in (
        "Cartn_x", "Cartn_y", "Cartn_z",
    ))  # type: ignore[return-value]


def recover_exact_struct_conn_event_v1(
    mmcif_text: str, stage_a_row: Mapping[str, str],
) -> ExactEventRecoveryDecision:
    """Recover an exact event; distance is used only after endpoint identity."""

    _, records, parse_status, parse_error = (
        struct_conn_owner.parse_struct_conn_loop(mmcif_text)
    )
    if parse_status == "raw_parse_error":
        return ExactEventRecoveryDecision(
            False, "STRUCT_CONN_PARSE_ERROR:" + parse_error,
            "STRUCT_CONN_PARSE_ERROR",
        )
    if not records:
        return ExactEventRecoveryDecision(
            False, "STRUCT_CONN_EXACT_PAIR_MISSING",
            "STRUCT_CONN_LOOP_ABSENT" if parse_status == "no_struct_conn_loop_found"
            else "STRUCT_CONN_LOOP_PRESENT_NO_RECORDS",
        )
    query = {
        "ligand_comp_id": stage_a_row["ligand_component_id"],
        "residue_chain_id": stage_a_row["protein_chain"],
        "residue_index": stage_a_row["cys_residue_sequence"],
    }
    matches, match_status, _, _ = struct_conn_owner.match_struct_conn_records(
        query, records,
    )
    if match_status == "ligand_comp_id_mismatch":
        return ExactEventRecoveryDecision(
            False, "LIGAND_COMPONENT_MISMATCH",
            "EXPLICIT_CYS_SG_CONNECTION_COMPONENT_MISMATCH", True,
        )
    if len(matches) != 1:
        status = (
            "STRUCT_CONN_EXACT_PAIR_AMBIGUOUS" if len(matches) > 1
            else "STRUCT_CONN_EXACT_PAIR_MISSING"
        )
        return ExactEventRecoveryDecision(False, status, match_status.upper())

    match = matches[0]
    record = match["record"]
    residue = match["residue"]
    ligand = match["ligand"]
    conn_type = _clean(record.get("_struct_conn.conn_type_id", "")).lower()
    if "cov" not in conn_type:
        return ExactEventRecoveryDecision(
            False, "STRUCT_CONN_NOT_EXPLICITLY_COVALENT",
            "NONCOVALENT_STRUCT_CONN_RECORD",
        )
    protein_chain = _clean(residue["auth_asym_id"] or residue["label_asym_id"])
    protein_sequence = _clean(residue["auth_seq_id"] or residue["label_seq_id"])
    ligand_chain = _clean(ligand["auth_asym_id"] or ligand["label_asym_id"])
    ligand_sequence = _clean(ligand["auth_seq_id"] or ligand["label_seq_id"])
    ligand_atom = _clean(ligand["atom_id"])
    required = (protein_chain, protein_sequence, ligand_chain,
                ligand_sequence, ligand_atom)
    if not all(required):
        return ExactEventRecoveryDecision(
            False, "STRUCT_CONN_ENDPOINT_IDENTITY_INCOMPLETE",
            "STRUCT_CONN_EXACT_RECORD_ENDPOINT_IDENTITY_INCOMPLETE",
        )
    residue_side = residue["side"]
    ligand_side = ligand["side"]
    insertion = _side_insertion(record, residue_side)
    expected_insertion = _none(stage_a_row["cys_insertion_code"])
    if insertion != expected_insertion:
        return ExactEventRecoveryDecision(
            False, "CYS_INSERTION_CODE_MISMATCH",
            "STRUCT_CONN_EXACT_RECORD_INSERTION_MISMATCH", True,
        )

    atom_rows = atom_site_owner.extract_atom_site_loop_rows_v0(mmcif_text)
    protein_match = atom_site_owner.find_atom_site_candidate_matches_v0(
        atom_rows, _contract_row(residue, "protein_residue"),
    )
    ligand_match = atom_site_owner.find_atom_site_candidate_matches_v0(
        atom_rows, _contract_row(ligand, "ligand"),
    )
    protein_candidates = _filter_explicit_altloc(
        protein_match["candidate_rows"], _side_altloc(record, residue_side),
    )
    ligand_candidates = _filter_explicit_altloc(
        ligand_match["candidate_rows"], _side_altloc(record, ligand_side),
    )
    if not protein_candidates or not ligand_candidates:
        return ExactEventRecoveryDecision(
            False, "STRUCT_CONN_ENDPOINT_COORDINATE_MISSING",
            "STRUCT_CONN_EXACT_PAIR_ENDPOINT_ATOM_SITE_MISSING",
        )
    if not _finite_atom_rows((*protein_candidates, *ligand_candidates)):
        return ExactEventRecoveryDecision(
            False, "STRUCT_CONN_ENDPOINT_COORDINATE_NONFINITE",
            "STRUCT_CONN_EXACT_PAIR_ENDPOINT_COORDINATE_INVALID",
        )

    if len(protein_candidates) == len(ligand_candidates) == 1:
        selected_protein = protein_candidates[0]
        selected_ligand = ligand_candidates[0]
    else:
        reported_text = _clean(record.get("_struct_conn.pdbx_dist_value", ""))
        try:
            reported = float(reported_text)
        except ValueError:
            return ExactEventRecoveryDecision(
                False, "ALTLOC_AMBIGUOUS_FAIL_CLOSED",
                "STRUCT_CONN_EXACT_PAIR_ALTLOC_AMBIGUOUS",
            )
        keys = [
            _pair_semantic_key(protein, ligand_row, reported)
            for protein in protein_candidates for ligand_row in ligand_candidates
        ]
        best = min(keys)
        if sum(key == best for key in keys) != 1:
            return ExactEventRecoveryDecision(
                False, "ALTLOC_AMBIGUOUS_FAIL_CLOSED",
                "STRUCT_CONN_EXACT_PAIR_ALTLOC_AMBIGUOUS",
            )
        selected = atom_site_owner.select_altloc_aware_pair_v0(
            {"review_row_id": "STAGE_B0", "confirmed_candidate_id":
             stage_a_row["canonical_candidate_id"]},
            {"review_row_id": "STAGE_B0", "confirmed_candidate_id":
             stage_a_row["canonical_candidate_id"]},
            protein_candidates, ligand_candidates, reported_text,
        )
        selected_protein = selected["selected_protein"]
        selected_ligand = selected["selected_ligand"]

    provenance = "|".join((
        "protein_altloc=" + _none(_atom_value(selected_protein, "label_alt_id")),
        "protein_occupancy=" + _none(_atom_value(selected_protein, "occupancy")),
        "ligand_altloc=" + _none(_atom_value(selected_ligand, "label_alt_id")),
        "ligand_occupancy=" + _none(_atom_value(selected_ligand, "occupancy")),
        "model=" + _none(_atom_value(selected_protein, "pdbx_PDB_model_num")),
    ))
    return ExactEventRecoveryDecision(
        True,
        "STRUCT_CONN_EXACT_CYS_SG_EVENT_AND_COORDINATES_RECOVERED",
        "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR",
        False,
        protein_chain,
        protein_sequence,
        insertion,
        ligand_chain,
        ligand_sequence,
        ligand_atom,
        "COORDINATES_FINITE_ALTLOC_DETERMINISTIC",
        provenance,
        _coordinates(selected_protein),
        _coordinates(selected_ligand),
    )


def classify_unrecovered_evidence_v1(
    *, local_raw_structure_found: bool, exact_event_ambiguous: bool = False,
) -> str:
    if not local_raw_structure_found:
        return "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
    if exact_event_ambiguous:
        return "HUMAN_STRUCTURAL_REVIEW_REQUIRED"
    return "HUMAN_STRUCTURAL_REVIEW_REQUIRED"


def _load_and_validate_inputs(
    repo_root: Path,
) -> tuple[list[dict[str, str]], dict[Path, bytes]]:
    payloads: dict[Path, bytes] = {}
    for path, expected in {
        **PUBLISHED_STAGE_A_SHA256, **FROZEN_LOCAL_AUTHORITY_SHA256,
    }.items():
        payload = (repo_root / path).read_bytes()
        _verify(payload, expected, path.as_posix())
        payloads[path] = payload
    registry = _csv_rows(payloads[STAGE_A_CANDIDATE])
    recovery_rows = [
        row for row in registry
        if row["registry_disposition"] == "HUMAN_REVIEW_REQUIRED"
    ]
    identities = tuple(
        (row["pdb_id"], row["ligand_component_id"]) for row in recovery_rows
    )
    if identities != RECOVERY_IDENTITIES:
        raise ValueError(f"STAGE_B0_RECOVERY_COHORT_MISMATCH:{identities!r}")
    gold = [row for row in registry if row["registry_disposition"] == "GOLD_REFERENCE"]
    eligible = {
        (row["pdb_id"], row["ligand_component_id"]) for row in registry
        if row["registry_disposition"] == "ELIGIBLE_FOR_STAGE_B"
    }
    rejects = {
        (row["pdb_id"], row["ligand_component_id"]) for row in registry
        if row["registry_disposition"] == "REJECT"
    }
    if len(gold) != 11 or eligible != ELIGIBLE_CONTROL_IDENTITIES:
        raise ValueError("STAGE_B0_FROZEN_GOLD_OR_ELIGIBLE_SCOPE_MISMATCH")
    if rejects != REJECT_IDENTITIES:
        raise ValueError("STAGE_B0_FROZEN_REJECT_SCOPE_MISMATCH")

    raw_download = next(
        row for row in _csv_rows(payloads[HISTORICAL_RAW_DOWNLOAD_AUDIT])
        if row["pdb_id"] == "1A54"
    )
    struct_conn = next(
        row for row in _csv_rows(payloads[HISTORICAL_STRUCT_CONN_AUDIT])
        if row["pdb_id"] == "1A54"
    )
    pdb_connections = next(
        row for row in _csv_rows(payloads[HISTORICAL_PDB_CONNECTION_AUDIT])
        if row["pdb_id"] == "1A54"
    )
    atom_site = next(
        row for row in _csv_rows(payloads[HISTORICAL_ATOM_SITE_AUDIT])
        if row["pdb_id"] == "1A54"
    )
    parse_audit = next(
        row for row in _csv_rows(payloads[HISTORICAL_CROSSCHECK_PARSE_AUDIT])
        if row["pdb_id"] == "1A54"
    )
    historical_ok = (
        raw_download["raw_sha256"] == HISTORICAL_1A54_RAW_SHA256
        and not _truth(struct_conn["struct_conn_loop_found"])
        and int(pdb_connections["link_record_count"]) == 0
        and int(pdb_connections["conect_record_count"]) == 0
        and _truth(atom_site["atom_site_loop_found"])
        and int(atom_site["atom_site_row_count"]) > 0
        and not _truth(parse_audit["struct_conn_loop_found"])
        and parse_audit["raw_file_sha256"] == HISTORICAL_1A54_RAW_SHA256
    )
    if not historical_ok:
        raise ValueError("STAGE_B0_1A54_HISTORICAL_AUTHORITY_INVALID")

    bounded = json.loads(payloads[BOUNDED_ACQUISITION_MANIFEST])
    bulk = json.loads(payloads[BULK_AUTHORIZATION_MANIFEST])
    request_pairs = {
        (row["pdb_id"], row["expected_het_id"])
        for row in _csv_rows(payloads[BOUNDED_ACQUISITION_REQUESTS])
    }
    if (
        bounded.get("all_checks_passed") is not True
        or ("1A54", "MDC") not in request_pairs
        or bulk.get("current_permission") is not False
        or bulk.get("ready_for_bulk_download_now") is not False
    ):
        raise ValueError("STAGE_B0_ACQUISITION_AUTHORITY_INVALID")
    return recovery_rows, payloads


def _authorization_status(pdb_id: str, ligand: str) -> str:
    if (pdb_id, ligand) == ("1A54", "MDC"):
        return (
            "BOUNDED_TARGETED_ACQUISITION_AUTHORIZED_FOR_IDENTITY_BY_"
            "PUBLISHED_RUNTIME_OWNER_NO_EXECUTION_THIS_TASK"
        )
    return (
        "NOT_AUTHORIZED_BY_EXISTING_PUBLISHED_BOUNDED_OWNER_NEW_BOUNDED_"
        "AUTHORIZATION_REQUIRED"
    )


def _raw_identity(
    stage_a_row: Mapping[str, str], lookup: LocalEvidenceLookup,
    repo_root: Path, state_root: Path,
) -> tuple[str, str, str]:
    if lookup.raw_structure_paths:
        hashes = {_sha256(path.read_bytes()) for path in lookup.raw_structure_paths}
        paths = ";".join(
            _path_identity(path, repo_root, state_root)
            for path in lookup.raw_structure_paths
        )
        sha = next(iter(hashes)) if len(hashes) == 1 else "MULTIPLE_DIFFERING_SHA256"
        identity = (
            f"PDB={stage_a_row['pdb_id']}|LOCAL_RAW_COUNT="
            f"{len(lookup.raw_structure_paths)}"
        )
        return identity, paths, sha
    if stage_a_row["pdb_id"] == "1A54":
        authority = (
            HISTORICAL_CROSSCHECK_PARSE_AUDIT.as_posix() + "#pdb_id=1A54"
        )
        return (
            "PDB=1A54|FORMAT=MMCIF|AVAILABILITY=HISTORICAL_SHA_BOUND_"
            "DERIVED_AUTHORITY_ONLY",
            authority,
            HISTORICAL_1A54_RAW_SHA256,
        )
    return (
        f"PDB={stage_a_row['pdb_id']}|FORMAT=MMCIF_OR_PDB_REQUIRED|"
        "AVAILABILITY=NOT_LOCAL",
        "NONE",
        "NONE",
    )


def _missing_matrix_row(
    source: Mapping[str, str], lookup: LocalEvidenceLookup,
    repo_root: Path, state_root: Path,
) -> dict[str, Any]:
    pdb_id = source["pdb_id"]
    ligand = source["ligand_component_id"]
    local_found = bool(lookup.raw_structure_paths)
    raw_identity, authority, raw_sha = _raw_identity(
        source, lookup, repo_root, state_root,
    )
    if len(lookup.raw_structure_paths) > 1:
        hashes = {_sha256(path.read_bytes()) for path in lookup.raw_structure_paths}
        if len(hashes) > 1:
            explicit_status = "LOCAL_RAW_STRUCTURE_IDENTITY_AMBIGUOUS"
        else:
            explicit_status = "LOCAL_RAW_MULTIPLE_BYTE_IDENTICAL_FILES_PENDING_PARSE"
    elif local_found:
        explicit_status = "LOCAL_RAW_STRUCTURE_PRESENT_PENDING_EXACT_PARSE"
    elif pdb_id == "1A54":
        explicit_status = (
            "HISTORICAL_MMCIF_STRUCT_CONN_LOOP_ABSENT_AND_PDB_LINK_CONECT_ABSENT"
        )
    else:
        explicit_status = "REQUIRED_RAW_STRUCTURE_NOT_LOCAL"

    decision: ExactEventRecoveryDecision | None = None
    if len(lookup.raw_structure_paths) == 1:
        raw_path = lookup.raw_structure_paths[0]
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        if raw_path.suffix.lower() in {".cif", ".mmcif"}:
            decision = recover_exact_struct_conn_event_v1(text, source)
        elif raw_path.suffix.lower() == ".pdb":
            links, _, _ = pdb_event_owner.parse_pdb_records(text)
            link_candidates = pdb_event_owner.extract_pdb_link_candidates(
                pdb_id, ligand, links,
            )
            explicit_status = (
                "PDB_LINK_EXPLICIT_CANDIDATE_REQUIRES_FULL_ENDPOINT_REVIEW"
                if len(link_candidates) == 1 else
                "PDB_LINK_EXPLICIT_EVIDENCE_MISSING_OR_AMBIGUOUS"
            )

    if decision is not None:
        explicit_status = decision.explicit_connection_evidence_status
    recovered = bool(decision and decision.recovered)
    fundamental_reject = bool(decision and decision.fundamental_reject)
    if fundamental_reject:
        disposition = "REJECT"
        structural_status = decision.status if decision else "REJECT"
        remaining = decision.status if decision else "RECOVERED_STAGE_A_VIOLATION"
    elif recovered:
        # Exact event recovery is kept separate from topology/label authority.
        disposition = "AUTO_RECOVERED_BUT_DOWNSTREAM_LABEL_REVIEW_REQUIRED"
        structural_status = (
            "EXACT_EVENT_AND_COORDINATES_AUTO_RECOVERED_CANONICAL_TOPOLOGY_PENDING"
        )
        remaining = (
            "PARENT_POST_TOPOLOGY_CANONICAL_MODEL_GRAPH_EXACT10_POCKET_AND_"
            "REACTION_WARHEAD_BOUNDARY_AUTHORITY_REQUIRED"
        )
    else:
        disposition = classify_unrecovered_evidence_v1(
            local_raw_structure_found=local_found,
            exact_event_ambiguous=local_found,
        )
        structural_status = (
            decision.status if decision is not None
            else "BLOCKED_RAW_STRUCTURE_NOT_LOCAL"
        )
        if pdb_id == "1A54" and not local_found:
            structural_status = (
                "BLOCKED_LOCAL_RAW_ABSENT_HISTORICAL_EXPLICIT_CONNECTION_ABSENCE_PROVED"
            )
        remaining = (
            "RAW_MMCIF_REACQUISITION_AND_INDEPENDENT_EXPLICIT_CONNECTION_"
            "EVIDENCE_REQUIRED"
            if pdb_id == "1A54"
            else "RAW_MMCIF_STRUCT_CONN_ATOM_SITE_AND_COMPONENT_TOPOLOGY_REQUIRED"
        )
    if pdb_id == "6VWE" and not recovered:
        remaining = (
            "RAW_MMCIF_EXACT_EVENT_AND_CANONICAL_MODEL_GRAPH_RH_MEMBERSHIP_"
            "EVIDENCE_REQUIRED"
        )

    return {
        "canonical_candidate_id": source["canonical_candidate_id"],
        "pdb_id": pdb_id,
        "ligand_component_id": ligand,
        "stage_a_disposition": source["registry_disposition"],
        "stage_a_primary_issue": source["primary_issue_code_or_NONE"],
        "stage_a_expected_protein_chain": source["protein_chain"],
        "stage_a_expected_cys_residue_sequence": source["cys_residue_sequence"],
        "local_raw_structure_found": local_found,
        "raw_structure_identity": raw_identity,
        "local_structure_path_or_authority": authority,
        "raw_structure_sha256_or_NONE": raw_sha,
        "explicit_connection_evidence_status": explicit_status,
        "cys_sg_event_recovered": recovered,
        "protein_chain": decision.protein_chain if recovered and decision else "NONE",
        "cys_residue_sequence": decision.cys_residue_sequence if recovered and decision else "NONE",
        "cys_insertion_code": decision.cys_insertion_code if recovered and decision else "NONE",
        "reactive_residue_atom": "SG" if recovered else "NONE",
        "ligand_chain_or_instance": decision.ligand_chain_or_instance if recovered and decision else "NONE",
        "ligand_sequence_or_instance": decision.ligand_sequence_or_instance if recovered and decision else "NONE",
        "reactive_ligand_atom": decision.reactive_ligand_atom if recovered and decision else "NONE",
        "coordinate_status": (
            decision.coordinate_status if decision else
            "HISTORICAL_ATOM_SITE_PRESENT_EVENT_ENDPOINTS_UNRESOLVED"
            if pdb_id == "1A54" else
            "COORDINATE_EVIDENCE_UNAVAILABLE_RAW_NOT_LOCAL"
        ),
        "altloc_occupancy_provenance": (
            decision.altloc_occupancy_provenance if decision else "NONE"
        ),
        "parent_post_topology_status": source["parent_post_topology_status"],
        "canonical_model_graph_status": (
            "FORMULA_RH_PRESENT_MODEL_GRAPH_MEMBERSHIP_UNRESOLVED"
            if pdb_id == "6VWE" else "CANONICAL_MODEL_GRAPH_EVIDENCE_MISSING"
        ),
        "exact10_status": source["exact10_status"],
        "pocket_readiness_status": "POCKET_EVIDENCE_INCOMPLETE",
        "structural_recovery_status": structural_status,
        "recovery_disposition": disposition,
        "downstream_label_authority_status": (
            "NOT_EVALUATED_STRUCTURAL_RECOVERY_BLOCKED"
            if not recovered else "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_PENDING"
        ),
        "acquisition_authorization_status": (
            "NOT_APPLICABLE_LOCAL_RAW_EXACT_EVENT_ALREADY_RECOVERED"
            if recovered else _authorization_status(pdb_id, ligand)
        ),
        "primary_remaining_issue": remaining,
        "recovery_mechanism_group": (
            "K36_UED_SHARED_BOUNDED_MMCIF_STRUCT_CONN_ATOM_SITE_PATH"
            if (pdb_id, ligand) in K36_UED_IDENTITIES
            else "CANDIDATE_SPECIFIC_BOUNDED_MMCIF_STRUCT_CONN_ATOM_SITE_PATH"
        ),
        "canonical_sample_authority_created": False,
    }


def _worklist_rows(recovery_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for recovery in recovery_rows:
        disposition = recovery["recovery_disposition"]
        if disposition == "AUTO_RECOVERED_STAGE_B_ELIGIBLE":
            continue
        if disposition == "AUTO_RECOVERED_BUT_DOWNSTREAM_LABEL_REVIEW_REQUIRED":
            category = "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_REQUIRED"
        elif disposition == "HUMAN_STRUCTURAL_REVIEW_REQUIRED":
            category = "HUMAN_STRUCTURAL_REVIEW_REQUIRED"
        elif disposition == "TARGETED_EXTERNAL_ACQUISITION_REQUIRED":
            category = "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
        else:
            continue
        if category == "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_REQUIRED":
            required = (
                "PARENT_POST_TOPOLOGY_CANONICAL_MODEL_GRAPH_EXACT10_POCKET_"
                "AND_REACTION_WARHEAD_BOUNDARY_AUTHORITY"
            )
        elif recovery["pdb_id"] == "1A54":
            required = (
                "RAW_MMCIF_REACQUISITION_FOR_REPRODUCIBLE_REVIEW_PLUS_"
                "INDEPENDENT_EXPLICIT_COVALENT_CONNECTION_AUTHORITY"
            )
        else:
            required = (
                "RAW_MMCIF_WITH_STRUCT_CONN_AND_ATOM_SITE_PLUS_COMPONENT_"
                "TOPOLOGY_EVIDENCE"
            )
        rows.append({
            "worklist_item_id": f"CYS_SG_STAGE_B0_WORK_{len(rows) + 1:06d}",
            "canonical_candidate_id": recovery["canonical_candidate_id"],
            "pdb_id": recovery["pdb_id"],
            "ligand_component_id": recovery["ligand_component_id"],
            "worklist_category": category,
            "required_missing_artifact_or_evidence": required,
            "existing_project_acquisition_authorization_status":
                recovery["acquisition_authorization_status"],
            "authorization_evidence_authority": (
                "NOT_APPLICABLE_RAW_ALREADY_LOCAL"
                if category == "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_REQUIRED"
                else
                BOUNDED_ACQUISITION_MANIFEST.as_posix()
                if recovery["pdb_id"] == "1A54"
                else BULK_AUTHORIZATION_MANIFEST.as_posix()
            ),
            "bulk_download_authorization_status": "BULK_DOWNLOAD_NOT_AUTHORIZED",
            "next_manual_or_acquisition_action": (
                "REVIEW_DOWNSTREAM_CANONICAL_TOPOLOGY_AND_CHEMISTRY_LABEL_AUTHORITY"
                if category == "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_REQUIRED"
                else
                "EXECUTE_ONLY_UNDER_SEPARATELY_AUTHORIZED_BOUNDED_TARGETED_"
                "ACQUISITION_STAGE"
            ),
            "canonical_sample_authority_created": False,
        })
    return rows


def _manifest(
    recovery_rows: Sequence[Mapping[str, Any]],
    worklist_rows: Sequence[Mapping[str, Any]],
    payloads: Mapping[Path, bytes],
    recovery_payload: bytes,
    worklist_payload: bytes,
) -> dict[str, Any]:
    dispositions = Counter(row["recovery_disposition"] for row in recovery_rows)
    auto_structural = sum(_truth(row["cys_sg_event_recovered"]) for row in recovery_rows)
    local_count = sum(_truth(row["local_raw_structure_found"]) for row in recovery_rows)
    human_count = dispositions["HUMAN_STRUCTURAL_REVIEW_REQUIRED"]
    input_count = len(recovery_rows)
    input_inventory = [
        {"path": path.as_posix(), "sha256": _sha256(payload)}
        for path, payload in sorted(payloads.items(), key=lambda item: item[0].as_posix())
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": "CovaPIE",
        "baseline_commit": BASELINE_COMMIT,
        "published_stage_a_commit": PUBLISHED_STAGE_A_COMMIT,
        "candidate_scope": "EXACT_12_PUBLISHED_STAGE_A_HUMAN_REVIEW_REQUIRED_ROWS_ONLY",
        "recovery_disposition_vocabulary": list(RECOVERY_DISPOSITIONS),
        "worklist_category_vocabulary": list(WORKLIST_CATEGORIES),
        "recovery_candidate_count": input_count,
        "recovery_candidate_identities": [
            f"{row['pdb_id']}/{row['ligand_component_id']}" for row in recovery_rows
        ],
        "auto_recovered_structural_count": auto_structural,
        "auto_recovered_stage_b_eligible_count":
            dispositions["AUTO_RECOVERED_STAGE_B_ELIGIBLE"],
        "auto_recovered_downstream_label_review_count":
            dispositions["AUTO_RECOVERED_BUT_DOWNSTREAM_LABEL_REVIEW_REQUIRED"],
        "human_structural_review_count": human_count,
        "targeted_external_acquisition_required_count":
            dispositions["TARGETED_EXTERNAL_ACQUISITION_REQUIRED"],
        "new_reject_count": dispositions["REJECT"],
        "structural_evidence_recovery_fraction": {
            "numerator": auto_structural, "denominator": input_count,
            "value": auto_structural / input_count,
        },
        "remaining_true_human_structural_review_fraction": {
            "numerator": human_count, "denominator": input_count,
            "value": human_count / input_count,
        },
        "local_raw_structure_available_count": local_count,
        "missing_raw_structure_count": input_count - local_count,
        "struct_conn_exact_event_recovered_count": sum(
            row["explicit_connection_evidence_status"]
            == "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
            and _truth(row["cys_sg_event_recovered"])
            for row in recovery_rows
        ),
        "other_explicit_event_authority_recovered_count": 0,
        "distance_only_inference_used": False,
        "k36_ued_recovery_reuse_possible": True,
        "k36_ued_shared_recovery_records": [
            f"{pdb}/{ligand}" for pdb, ligand in K36_UED_IDENTITIES
        ],
        "k36_ued_shared_recovery_mechanism":
            "BOUNDED_MMCIF_ACQUISITION_THEN_PUBLISHED_STRUCT_CONN_AND_ATOM_SITE_ADAPTER",
        "k36_ued_duplicate_sample_authority_created": False,
        "six_vwe_rh_final_status":
            "FORMULA_RH_PRESENT_MODEL_GRAPH_MEMBERSHIP_UNRESOLVED_NO_REJECT",
        "evidence_complete_nonduplicate_stage_a_pass_count": 3,
        "evidence_complete_nonduplicate_stage_a_total_count": 3,
        "historical_1a54_raw_sha256": HISTORICAL_1A54_RAW_SHA256,
        "historical_1a54_struct_conn_loop_absent": True,
        "historical_1a54_pdb_link_conect_absent": True,
        "bulk_download_authorized_now": False,
        "bounded_targeted_identity_already_authorized": ["1A54/MDC"],
        "existing_bounded_authorized_count": 1,
        "bounded_targeted_identity_not_yet_authorized": [
            f"{pdb}/{ligand}" for pdb, ligand in RECOVERY_IDENTITIES[1:]
        ],
        "new_bounded_authorization_required_count": 11,
        "input_evidence_identities": input_inventory,
        "recovery_worklist_row_count": len(worklist_rows),
        "deterministic_output_hashes": {
            RECOVERY_FILE: _sha256(recovery_payload),
            WORKLIST_FILE: _sha256(worklist_payload),
        },
        "manifest_self_sha256_recorded": False,
        "published_stage_a_modified": False,
        "current11_modified": False,
        "raw_modified": False,
        "canonical_sample_authority_created": False,
        "inverse_reaction_chemistry_executed": False,
        "pre_reconstruction_executed": False,
        "torsion_sampling_executed": False,
        "geometry_executed": False,
        "rdkit_minimization_executed": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "trainer_fit": False,
        "rl": False,
        "bulk_acquisition_executed": False,
        "targeted_acquisition_executed": False,
        "ready_for_evidence_recovery_publication": input_count == 12,
        "ready_for_stage_b_automated_label_and_geometry_pilot": True,
        "ready_for_bulk_expansion": False,
        "ready_for_geometry_loss_activation": False,
        "ready_for_training": False,
        "recommended_next_step_exactly": RECOMMENDED_NEXT_STEP,
    }


def build_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_artifacts_v1(
    *, repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT,
) -> dict[str, bytes]:
    source_rows, payloads = _load_and_validate_inputs(repo_root)
    recovery_rows = [
        _missing_matrix_row(
            source,
            lookup_local_evidence_v1(
                source["pdb_id"], source["ligand_component_id"],
                repo_root=repo_root, state_root=state_root,
            ),
            repo_root,
            state_root,
        )
        for source in source_rows
    ]
    if len({row["canonical_candidate_id"] for row in recovery_rows}) != 12:
        raise ValueError("STAGE_B0_CANDIDATE_SILENTLY_DROPPED_OR_DUPLICATED")
    worklist_rows = _worklist_rows(recovery_rows)
    recovery_payload = _csv_bytes(recovery_rows, RECOVERY_COLUMNS)
    worklist_payload = _csv_bytes(worklist_rows, WORKLIST_COLUMNS)
    manifest = _manifest(
        recovery_rows, worklist_rows, payloads,
        recovery_payload, worklist_payload,
    )
    return {
        RECOVERY_FILE: recovery_payload,
        WORKLIST_FILE: worklist_payload,
        MANIFEST_FILE: _json_bytes(manifest),
    }


def materialize_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1(
    output_root: Path = REPO_ROOT / OUTPUT_ROOT,
    *, repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT,
) -> dict[str, str]:
    artifacts = (
        build_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_artifacts_v1(
            repo_root=repo_root, state_root=state_root,
        )
    )
    output_root.mkdir(parents=True, exist_ok=True, mode=0o755)
    os.chmod(output_root, 0o755)
    hashes: dict[str, str] = {}
    for filename in OUTPUT_FILES:
        path = output_root / filename
        path.write_bytes(artifacts[filename])
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        hashes[filename] = _sha256(artifacts[filename])
    return hashes


def main() -> None:
    print(json.dumps(
        materialize_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1(),
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
