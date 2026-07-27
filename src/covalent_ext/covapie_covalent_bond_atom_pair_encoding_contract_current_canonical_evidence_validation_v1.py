"""Validate the frozen atom-pair encoding contract against committed evidence.

The row indices produced here are metadata-only derived views bound to the
committed CSV bytes and their exact row order.  This module never reads raw
structures and never materializes tensors or changes training code.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1 as contract,
)

__all__ = (
    "CovalentBondAtomPairEncodingContractValidationDecision",
    "CovalentBondAtomPairSampleEvidenceValidationObservation",
    "build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1",
    "derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1",
    "serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1",
    "validate_covapie_atom_table_locator_exact_one_v1",
    "validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1",
)

BASE_COMMIT = "7f432cecec8a3abed2339e4dd60dfa239cd2cbe7"
BASE_PARENT = "6f04eb7036aa926e433a02de3e244412af038800"
BASE_TREE = "e947c1da0ddfa26bcb733a777e8566c296646c38"
BASE_SUBJECT = "add CovaPIE covalent bond atom-pair encoding contract v1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE covalent bond atom-pair encoding contract validation v1"
)
SCHEMA_VERSION = (
    "covapie_covalent_bond_atom_pair_encoding_contract_validation_v1"
)
STAGE = (
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
SOURCE_INVENTORY_FILE = "covapie_atom_pair_contract_validation_source_inventory.csv"
CANONICAL_MATRIX_FILE = "covapie_atom_pair_canonical_record_validation_matrix.csv"
MAPPING_MATRIX_FILE = "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
FAILURE_MATRIX_FILE = "covapie_atom_pair_contract_validation_failure_matrix.csv"
ISSUE_INVENTORY_FILE = (
    "covapie_atom_pair_contract_validation_issue_readiness_inventory.csv"
)
MANIFEST_FILE = (
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    CANONICAL_MATRIX_FILE,
    MAPPING_MATRIX_FILE,
    FAILURE_MATRIX_FILE,
    ISSUE_INVENTORY_FILE,
    MANIFEST_FILE,
)
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_real_provider_export_blocking_rows_and_freeze_"
    "resolution_or_quarantine_policy_v1"
)

CONTRACT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py"
)
CONTRACT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1"
)
CONTRACT_MANIFEST = CONTRACT_ROOT / (
    "covapie_covalent_bond_atom_pair_encoding_contract_manifest.json"
)
PREDECESSOR_ISSUES = CONTRACT_ROOT / (
    "covapie_covalent_bond_atom_pair_issue_readiness_inventory.csv"
)
CURRENT_REPRESENTATION_AUDIT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
    "consumers_audit_gate_v1/"
    "covapie_covalent_bond_atom_pair_current_representation_audit.csv"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
FROZEN_SHA256 = {
    CONTRACT_SOURCE: "dd428bf4993dc24ed11ec54d0163c42ad161d1203433e219acba29b602a2e5ea",
    CONTRACT_MANIFEST: "8f0d80f7b54dd9635a1cdb1f6bd3ca0069a6c09059eeff806a6885e89a460920",
    PREDECESSOR_ISSUES: "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7",
    CURRENT_REPRESENTATION_AUDIT: "f63a5a8b0ed1d7ad0284a89826325f0d429ab33b202a5f2e468ae8a370eb1968",
    FINAL_DATASET_INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
}
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
FAILURE_CASES = (
    "contract predecessor SHA drift",
    "invalid canonical record schema",
    "unsupported authority",
    "missing authority provenance",
    "legacy projection mismatch",
    "event pair mismatch",
    "zero pair-table rows",
    "multiple pair-table rows",
    "missing pocket match",
    "duplicate pocket match",
    "missing ligand match",
    "duplicate ligand match",
    "target residue mismatch",
    "ligand instance mismatch",
    "pair-table residue atom_site mismatch",
    "pair-table ligand atom_site mismatch",
    "coordinate mismatch",
    "row-count mismatch",
    "row-order drift",
    "non-zero index base",
    "model ambiguity",
    "altloc ambiguity",
    "missing target table",
    "residue model field unavailable",
    "residue altloc field unavailable",
    "residue insertion-code field unavailable",
    "ligand insertion-code field unavailable",
)

SOURCE_COLUMNS = (
    "source_role",
    "source_path",
    "source_sha256",
    "committed_in_base",
    "data_row_count_if_tabular",
    "referenced_by_sample_index_row_id",
    "read_count",
    "verified",
)
CANONICAL_COLUMNS = (
    "sample_index_row_id", "event_id", "pdb_id", "pair_record_schema_version",
    "residue_entity_role", "residue_auth_asym_id", "residue_auth_seq_id",
    "residue_label_asym_id", "residue_label_seq_id", "residue_comp_id",
    "residue_atom_name", "ligand_entity_role", "ligand_auth_asym_id",
    "ligand_auth_seq_id", "ligand_label_asym_id", "ligand_label_seq_id",
    "ligand_comp_id", "ligand_atom_name", "explicit_bond_authority_class",
    "explicit_bond_provenance_id", "canonical_record_valid",
    "legacy_projection", "observed_legacy_value", "legacy_projection_matches",
    "event_pair_value_matches", "pair_table_value_matches",
    "final_index_value_matches", "explicit_authority_preserved", "verified",
)
MAPPING_COLUMNS = (
    "sample_index_row_id", "event_id", "pdb_id", "entity_role",
    "target_table_path", "target_table_sha256", "target_table_data_row_count",
    "mapping_key_fields", "nonempty_locator_fields_used",
    "optional_locator_fields_unavailable", "candidate_match_count",
    "expected_match_count", "matched_row_index_0based", "matched_atom_site_id",
    "pair_table_expected_atom_site_id", "atom_site_id_matches",
    "coordinate_crosscheck_passed", "distance_used_for_mapping_selection",
    "source_row_order_sha_bound", "model_index_base", "mapping_outcome",
    "mapping_reason", "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "expected_outcome", "observed_outcome", "fails_closed",
    "record_retained", "mapping_retained", "issue_resolved", "verified",
)


@dataclass(frozen=True)
class CovalentBondAtomPairEncodingContractValidationDecision:
    schema_version: str
    outcome: str
    contract_precondition_verified: bool
    current_canonical_record_count: int
    canonical_record_valid_count: int
    exact_one_residue_mapping_count: int
    exact_one_ligand_mapping_count: int
    pair_table_atom_site_crosscheck_count: int
    pair_table_coordinate_crosscheck_count: int
    legacy_projection_match_count: int
    explicit_bond_authority_preserved_count: int
    model_index_base: int
    row_order_validation_completed: bool
    encoding_contract_validation_completed: bool
    atom_pair_issue_resolved: bool
    provider_issue_resolved: bool
    atom_pair_ready_for_downstream_contracts: bool
    ready_for_tensorization: bool
    feature_semantics_audit_completed: bool
    ready_for_training: bool
    recommended_next_step: str


@dataclass(frozen=True)
class CovalentBondAtomPairSampleEvidenceValidationObservation:
    """One executable, fail-closed validation of a complete sample bundle."""

    outcome: str
    reason: str
    contract_precondition_verified: bool
    canonical_record_valid: bool
    pair_table_cardinality_valid: bool
    legacy_projection_matches: bool
    explicit_authority_valid: bool
    residue_mapping_valid: bool
    ligand_mapping_valid: bool
    atom_site_crosscheck_valid: bool
    coordinate_crosscheck_valid: bool
    row_count_valid: bool
    source_binding_valid: bool
    residue_candidate_match_count: int
    ligand_candidate_match_count: int
    residue_row_index_0based: int | None
    ligand_row_index_0based: int | None
    residue_atom_site_matches: bool
    ligand_atom_site_matches: bool
    residue_coordinate_matches: bool
    ligand_coordinate_matches: bool
    legacy_projection: str
    canonical_record: (
        contract.CovalentBondAtomPairCanonicalRecordDesign | None
    )
    record_retained: bool
    mapping_retained: bool


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _git(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(
        ("git", *args), cwd=repo_root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base_bytes(repo_root: Path, path: Path) -> bytes:
    relative = path.as_posix()
    _git(repo_root, "cat-file", "-e", f"{BASE_COMMIT}:{relative}")
    return _git(repo_root, "show", f"{BASE_COMMIT}:{relative}")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({
            key: ("true" if value is True else "false" if value is False else value)
            for key, value in row.items()
        })
    return stream.getvalue().encode("utf-8")


def _decimal_equal(left: str, right: str) -> bool:
    try:
        return Decimal(left) == Decimal(right)
    except InvalidOperation:
        return False


def _precondition(payloads: dict[Path, bytes]) -> bool:
    if any(_sha(payloads[path]) != expected for path, expected in FROZEN_SHA256.items()):
        return False
    manifest = json.loads(payloads[CONTRACT_MANIFEST])
    expected = {
        "outcome": "frozen",
        "canonical_pair_record_schema_frozen": True,
        "canonical_pair_record_validator_available": True,
        "model_input_index_space_compatibility_verified": True,
        "distance_only_inference_forbidden": True,
        "positive_pair_cardinality_policy": "exactly_one_positive_explicit_pair_per_sample",
        "residue_model_index_space": "pocket_atom_table_row_index",
        "ligand_model_index_space": "ligand_atom_table_row_index",
        "model_index_base": 0,
        "encoding_contract_validation_completed": False,
        "atom_pair_issue_resolved": False,
        "ready_for_contract_validation": True,
        "ready_for_tensorization": False,
        "ready_for_training": False,
    }
    return all(manifest.get(key) == value for key, value in expected.items())


def _locator(
    event: dict[str, str], *, residue: bool,
) -> contract.CovalentAtomLocatorContractDesign:
    prefix = "residue" if residue else "ligand"
    return contract.CovalentAtomLocatorContractDesign(
        locator_schema_version=contract.LOCATOR_SCHEMA_VERSION,
        entity_role="target_residue_atom" if residue else "ligand_atom",
        event_id=event["sample_preparation_input_id"],
        pdb_id=event["pdb_id"],
        model_id="",
        auth_asym_id=event[f"{prefix}_auth_asym_id"],
        auth_seq_id=event[f"{prefix}_auth_seq_id"],
        insertion_code="",
        label_asym_id=event[f"{prefix}_label_asym_id"],
        label_seq_id=event[f"{prefix}_label_seq_id"],
        comp_id=event[f"{prefix}_comp_id"],
        atom_name=event[f"{prefix}_atom_name"],
        altloc="",
    )


def _record(event: dict[str, str]) -> contract.CovalentBondAtomPairCanonicalRecordDesign:
    authority_ok = (
        event.get("event_status") == "validated"
        and event.get("conn_type_id") == "covale"
        and "struct_conn" in event.get("event_source", "")
        and event.get("conn_id", "") != ""
    )
    return contract.CovalentBondAtomPairCanonicalRecordDesign(
        pair_record_schema_version=contract.PAIR_RECORD_SCHEMA_VERSION,
        residue_atom_locator=_locator(event, residue=True),
        ligand_atom_locator=_locator(event, residue=False),
        explicit_bond_authority_class=(
            "validated_struct_conn" if authority_ok else "unsupported"
        ),
        explicit_bond_provenance_id=(
            f"{event['sample_preparation_input_id']}:{event['conn_id']}"
            if event.get("conn_id") else ""
        ),
    )


def validate_covapie_atom_table_locator_exact_one_v1(
    locator: contract.CovalentAtomLocatorContractDesign,
    table_rows: list[dict[str, str]],
    *,
    expected_het_id: str = "",
    model_index_base: int = 0,
) -> tuple[int, int | None]:
    """Return candidate count/index; missing columns and ambiguity fail closed."""
    if type(locator) is not contract.CovalentAtomLocatorContractDesign:
        return 0, None
    if not contract.validate_covapie_covalent_atom_locator_contract_design_v1(
        locator
    ):
        return 0, None
    if type(table_rows) is not list or not table_rows:
        return 0, None
    if any(
        type(row) is not dict
        or any(type(key) is not str or type(value) is not str for key, value in row.items())
        for row in table_rows
    ):
        return 0, None
    if type(expected_het_id) is not str:
        return 0, None
    if type(model_index_base) is not int or model_index_base != 0:
        return 0, None
    residue = locator.entity_role == "target_residue_atom"
    if not residue and locator.entity_role != "ligand_atom":
        return 0, None
    key_map = (
        (
            ("event_id", "sample_preparation_input_id"),
            ("pdb_id", "pdb_id"),
            ("comp_id", "residue_name"),
            ("atom_name", "atom_name"),
            ("auth_asym_id", "auth_asym_id"),
            ("auth_seq_id", "auth_seq_id"),
            ("label_asym_id", "label_asym_id"),
            ("label_seq_id", "label_seq_id"),
        )
        if residue
        else (
            ("event_id", "sample_preparation_input_id"),
            ("pdb_id", "pdb_id"),
            ("comp_id", "ligand_comp_id"),
            ("atom_name", "atom_name"),
            ("auth_asym_id", "auth_asym_id"),
            ("auth_seq_id", "auth_seq_id"),
            ("label_asym_id", "label_asym_id"),
            ("label_seq_id", "label_seq_id"),
        )
    )
    header = set(table_rows[0])
    optional_map = (
        ("model_id", "model_num"),
        ("altloc", "altloc"),
        ("insertion_code", "insertion_code"),
    )
    required_columns = {
        column for field, column in (*key_map, *optional_map)
        if getattr(locator, field)
    }
    required_columns.update(
        ("chain_id", "residue_index")
        if residue
        else ("expected_het_id", "is_covalent_ligand_atom")
    )
    if not required_columns <= header:
        return 0, None
    candidates = []
    for index, row in enumerate(table_rows):
        if any(
            getattr(locator, field) and row.get(column) != getattr(locator, field)
            for field, column in key_map
        ):
            continue
        if any(
            getattr(locator, field)
            and row.get(column) != getattr(locator, field)
            for field, column in optional_map
        ):
            continue
        if residue:
            if (
                row.get("chain_id") != locator.auth_asym_id
                or row.get("residue_index") != locator.auth_seq_id
            ):
                continue
        else:
            if (
                row.get("expected_het_id") != expected_het_id
                or row.get("is_covalent_ligand_atom") != "True"
            ):
                continue
        candidates.append(index)
    return len(candidates), candidates[0] if len(candidates) == 1 else None


def _invalid_sample_observation(
    reason: str,
    *,
    contract_precondition_verified: bool,
    canonical_record: (
        contract.CovalentBondAtomPairCanonicalRecordDesign | None
    ) = None,
    canonical_record_valid: bool = False,
    pair_table_cardinality_valid: bool = False,
    legacy_projection_matches: bool = False,
    explicit_authority_valid: bool = False,
    residue_mapping_valid: bool = False,
    ligand_mapping_valid: bool = False,
    atom_site_crosscheck_valid: bool = False,
    coordinate_crosscheck_valid: bool = False,
    row_count_valid: bool = False,
    source_binding_valid: bool = False,
    residue_candidate_match_count: int = 0,
    ligand_candidate_match_count: int = 0,
    residue_row_index_0based: int | None = None,
    ligand_row_index_0based: int | None = None,
    residue_atom_site_matches: bool = False,
    ligand_atom_site_matches: bool = False,
    residue_coordinate_matches: bool = False,
    ligand_coordinate_matches: bool = False,
    legacy_projection: str = "",
) -> CovalentBondAtomPairSampleEvidenceValidationObservation:
    return CovalentBondAtomPairSampleEvidenceValidationObservation(
        outcome="invalid",
        reason=reason,
        contract_precondition_verified=contract_precondition_verified,
        canonical_record_valid=canonical_record_valid,
        pair_table_cardinality_valid=pair_table_cardinality_valid,
        legacy_projection_matches=legacy_projection_matches,
        explicit_authority_valid=explicit_authority_valid,
        residue_mapping_valid=residue_mapping_valid,
        ligand_mapping_valid=ligand_mapping_valid,
        atom_site_crosscheck_valid=atom_site_crosscheck_valid,
        coordinate_crosscheck_valid=coordinate_crosscheck_valid,
        row_count_valid=row_count_valid,
        source_binding_valid=source_binding_valid,
        residue_candidate_match_count=residue_candidate_match_count,
        ligand_candidate_match_count=ligand_candidate_match_count,
        residue_row_index_0based=residue_row_index_0based,
        ligand_row_index_0based=ligand_row_index_0based,
        residue_atom_site_matches=residue_atom_site_matches,
        ligand_atom_site_matches=ligand_atom_site_matches,
        residue_coordinate_matches=residue_coordinate_matches,
        ligand_coordinate_matches=ligand_coordinate_matches,
        legacy_projection=legacy_projection,
        canonical_record=canonical_record,
        record_retained=False,
        mapping_retained=False,
    )


def validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
    *,
    contract_precondition_verified: bool,
    sample_row: dict[str, str],
    event_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    pocket_table_payload: bytes,
    pocket_table_rows: list[dict[str, str]],
    ligand_table_payload: bytes,
    ligand_table_rows: list[dict[str, str]],
    expected_pocket_table_sha256: str,
    expected_ligand_table_sha256: str,
    model_index_base: int = 0,
) -> CovalentBondAtomPairSampleEvidenceValidationObservation:
    """Validate one complete evidence bundle through the production path."""
    if type(contract_precondition_verified) is not bool:
        return _invalid_sample_observation(
            "invalid_contract_precondition_type",
            contract_precondition_verified=False,
        )
    if not contract_precondition_verified:
        return _invalid_sample_observation(
            "contract_precondition_failed",
            contract_precondition_verified=False,
        )
    typed_inputs = (
        type(sample_row) is dict
        and type(event_rows) is list
        and type(pair_rows) is list
        and type(pocket_table_payload) is bytes
        and type(pocket_table_rows) is list
        and type(ligand_table_payload) is bytes
        and type(ligand_table_rows) is list
        and type(expected_pocket_table_sha256) is str
        and type(expected_ligand_table_sha256) is str
        and type(model_index_base) is int
    )
    row_groups = (
        [sample_row],
        event_rows,
        pair_rows,
        pocket_table_rows,
        ligand_table_rows,
    )
    rows_typed = all(
        type(row) is dict
        and all(type(key) is str and type(value) is str for key, value in row.items())
        for rows in row_groups for row in rows
    )
    if not typed_inputs or not rows_typed:
        return _invalid_sample_observation(
            "invalid_bundle_input_type",
            contract_precondition_verified=True,
        )
    if len(event_rows) != 1:
        return _invalid_sample_observation(
            "event_table_cardinality_invalid",
            contract_precondition_verified=True,
        )
    if len(pair_rows) != 1:
        return _invalid_sample_observation(
            "pair_table_cardinality_invalid",
            contract_precondition_verified=True,
        )
    event = event_rows[0]
    pair = pair_rows[0]
    try:
        record = _record(event)
    except (KeyError, TypeError):
        return _invalid_sample_observation(
            "canonical_record_construction_failed",
            contract_precondition_verified=True,
            pair_table_cardinality_valid=True,
        )
    canonical_valid = (
        contract.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            record
        )
        and event.get("sample_preparation_input_id")
        == sample_row.get("sample_preparation_input_id")
        == pair.get("sample_preparation_input_id")
        == record.residue_atom_locator.event_id
        and event.get("pdb_id") == sample_row.get("pdb_id") == pair.get("pdb_id")
        and event.get("expected_het_id")
        == sample_row.get("expected_het_id")
        == pair.get("expected_het_id")
    )
    authority_valid = (
        record.explicit_bond_authority_class == "validated_struct_conn"
        and record.explicit_bond_provenance_id
        == f"{event.get('sample_preparation_input_id', '')}:{event.get('conn_id', '')}"
        and event.get("event_status") == "validated"
        and event.get("conn_type_id") == "covale"
        and "struct_conn" in event.get("event_source", "")
        and event.get("conn_id", "") != ""
    )
    try:
        legacy = contract.project_covapie_legacy_atom_name_pair_v1(record)
    except ValueError:
        legacy = ""
    legacy_matches = (
        legacy != ""
        and legacy == event.get("covalent_bond_atom_pair")
        == pair.get("covalent_bond_atom_pair")
        == sample_row.get("covalent_bond_atom_pair")
    )
    residue_count, residue_index = validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator,
        pocket_table_rows,
        expected_het_id=sample_row.get("expected_het_id", ""),
        model_index_base=model_index_base,
    )
    ligand_count, ligand_index = validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator,
        ligand_table_rows,
        expected_het_id=sample_row.get("expected_het_id", ""),
        model_index_base=model_index_base,
    )
    residue_mapping_valid = residue_count == 1 and residue_index is not None
    ligand_mapping_valid = ligand_count == 1 and ligand_index is not None
    try:
        pocket_payload_rows = _csv_rows(pocket_table_payload)
        ligand_payload_rows = _csv_rows(ligand_table_payload)
    except (UnicodeDecodeError, csv.Error):
        pocket_payload_rows = []
        ligand_payload_rows = []
    source_binding_valid = (
        sample_row.get("pocket_atom_table_path", "") != ""
        and sample_row.get("ligand_atom_table_path", "") != ""
        and _sha(pocket_table_payload) == expected_pocket_table_sha256
        and _sha(ligand_table_payload) == expected_ligand_table_sha256
        and pocket_payload_rows == pocket_table_rows
        and ligand_payload_rows == ligand_table_rows
    )
    try:
        row_count_valid = (
            len(pocket_table_rows) == int(sample_row["pocket_atom_count"])
            and len(ligand_table_rows) == int(sample_row["ligand_atom_count"])
        )
    except (KeyError, TypeError, ValueError):
        row_count_valid = False
    residue_row = (
        pocket_table_rows[residue_index]
        if residue_index is not None and residue_index < len(pocket_table_rows)
        else {}
    )
    ligand_row = (
        ligand_table_rows[ligand_index]
        if ligand_index is not None and ligand_index < len(ligand_table_rows)
        else {}
    )
    residue_site_matches = (
        bool(residue_row)
        and residue_row.get("atom_site_id") == pair.get("residue_atom_site_id")
    )
    ligand_site_matches = (
        bool(ligand_row)
        and ligand_row.get("atom_site_id") == pair.get("ligand_atom_site_id")
    )
    residue_coordinates_match = bool(residue_row) and all(
        _decimal_equal(residue_row.get(axis, ""), pair.get(f"residue_{axis}", ""))
        for axis in ("x", "y", "z")
    )
    ligand_coordinates_match = bool(ligand_row) and all(
        _decimal_equal(ligand_row.get(axis, ""), pair.get(f"ligand_{axis}", ""))
        for axis in ("x", "y", "z")
    )
    site_valid = residue_site_matches and ligand_site_matches
    coordinate_valid = residue_coordinates_match and ligand_coordinates_match
    checks = (
        ("canonical_record_invalid", canonical_valid),
        ("explicit_authority_invalid", authority_valid),
        ("legacy_projection_mismatch", legacy_matches),
        ("residue_mapping_invalid", residue_mapping_valid),
        ("ligand_mapping_invalid", ligand_mapping_valid),
        ("row_count_invalid", row_count_valid),
        ("source_binding_invalid", source_binding_valid),
        ("atom_site_crosscheck_invalid", site_valid),
        ("coordinate_crosscheck_invalid", coordinate_valid),
    )
    failure_reasons = [reason for reason, passed in checks if not passed]
    if failure_reasons:
        return _invalid_sample_observation(
            "|".join(failure_reasons),
            contract_precondition_verified=True,
            canonical_record=record,
            canonical_record_valid=canonical_valid,
            pair_table_cardinality_valid=True,
            legacy_projection_matches=legacy_matches,
            explicit_authority_valid=authority_valid,
            residue_mapping_valid=residue_mapping_valid,
            ligand_mapping_valid=ligand_mapping_valid,
            atom_site_crosscheck_valid=site_valid,
            coordinate_crosscheck_valid=coordinate_valid,
            row_count_valid=row_count_valid,
            source_binding_valid=source_binding_valid,
            residue_candidate_match_count=residue_count,
            ligand_candidate_match_count=ligand_count,
            residue_row_index_0based=residue_index,
            ligand_row_index_0based=ligand_index,
            residue_atom_site_matches=residue_site_matches,
            ligand_atom_site_matches=ligand_site_matches,
            residue_coordinate_matches=residue_coordinates_match,
            ligand_coordinate_matches=ligand_coordinates_match,
            legacy_projection=legacy,
        )
    return CovalentBondAtomPairSampleEvidenceValidationObservation(
        outcome="validated",
        reason="all_sample_bundle_checks_passed",
        contract_precondition_verified=True,
        canonical_record_valid=True,
        pair_table_cardinality_valid=True,
        legacy_projection_matches=True,
        explicit_authority_valid=True,
        residue_mapping_valid=True,
        ligand_mapping_valid=True,
        atom_site_crosscheck_valid=True,
        coordinate_crosscheck_valid=True,
        row_count_valid=True,
        source_binding_valid=True,
        residue_candidate_match_count=1,
        ligand_candidate_match_count=1,
        residue_row_index_0based=residue_index,
        ligand_row_index_0based=ligand_index,
        residue_atom_site_matches=True,
        ligand_atom_site_matches=True,
        residue_coordinate_matches=True,
        ligand_coordinate_matches=True,
        legacy_projection=legacy,
        canonical_record=record,
        record_retained=True,
        mapping_retained=True,
    )


def serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1(
    decision: CovalentBondAtomPairEncodingContractValidationDecision,
) -> bytes:
    if type(decision) is not CovalentBondAtomPairEncodingContractValidationDecision:
        raise TypeError("decision has the wrong exact type")
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _failure_observations(
    *,
    fixed_payloads: dict[Path, bytes],
    sample: dict[str, str],
    event: dict[str, str],
    pair: dict[str, str],
    pocket_payload: bytes,
    pocket: list[dict[str, str]],
    ligand_payload: bytes,
    ligand: list[dict[str, str]],
    record: contract.CovalentBondAtomPairCanonicalRecordDesign,
) -> dict[str, bool]:
    """Execute every failure case against the production validation path."""
    validate_record = (
        contract.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1
    )
    expected_pocket_sha = _sha(pocket_payload)
    expected_ligand_sha = _sha(ligand_payload)

    def bundle(**overrides: Any) -> (
        CovalentBondAtomPairSampleEvidenceValidationObservation
    ):
        values = {
            "contract_precondition_verified": True,
            "sample_row": deepcopy(sample),
            "event_rows": [deepcopy(event)],
            "pair_rows": [deepcopy(pair)],
            "pocket_table_payload": pocket_payload,
            "pocket_table_rows": deepcopy(pocket),
            "ligand_table_payload": ligand_payload,
            "ligand_table_rows": deepcopy(ligand),
            "expected_pocket_table_sha256": expected_pocket_sha,
            "expected_ligand_table_sha256": expected_ligand_sha,
            "model_index_base": 0,
        }
        values.update(overrides)
        return validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
            **values
        )

    normal = bundle()
    if normal.outcome != "validated":
        raise ValueError("tamper fixture does not validate normally")
    residue_index = normal.residue_row_index_0based
    ligand_index = normal.ligand_row_index_0based
    if residue_index is None or ligand_index is None:
        raise ValueError("tamper fixture lacks exact mapping indices")

    def fails_closed(observation: (
        CovalentBondAtomPairSampleEvidenceValidationObservation
    )) -> bool:
        return (
            observation.outcome == "invalid"
            and observation.record_retained is False
            and observation.mapping_retained is False
        )

    def table_payload(
        original: list[dict[str, str]], rows: list[dict[str, str]]
    ) -> bytes:
        return _csv_bytes(tuple(original[0]), rows)

    legacy_sample = deepcopy(sample)
    legacy_sample["covalent_bond_atom_pair"] = "SG--TAMPER"
    event_pair = deepcopy(event)
    event_pair["covalent_bond_atom_pair"] = "SG--TAMPER"
    missing_pocket = [
        deepcopy(row) for index, row in enumerate(pocket)
        if index != residue_index
    ]
    duplicate_pocket = deepcopy(pocket)
    duplicate_pocket.append(deepcopy(pocket[residue_index]))
    missing_ligand = [
        deepcopy(row) for index, row in enumerate(ligand)
        if index != ligand_index
    ]
    duplicate_ligand = deepcopy(ligand)
    duplicate_ligand.append(deepcopy(ligand[ligand_index]))
    wrong_residue_event = deepcopy(event)
    wrong_residue_event["residue_comp_id"] = "NOT_CYS"
    wrong_ligand_event = deepcopy(event)
    wrong_ligand_event["ligand_comp_id"] = "NOT_LIGAND"
    residue_site_pair = deepcopy(pair)
    residue_site_pair["residue_atom_site_id"] = "TAMPER"
    ligand_site_pair = deepcopy(pair)
    ligand_site_pair["ligand_atom_site_id"] = "TAMPER"
    coordinate_pair = deepcopy(pair)
    coordinate_pair["residue_x"] = "999999"
    row_count_sample = deepcopy(sample)
    row_count_sample["pocket_atom_count"] = str(len(pocket) + 1)
    drifted_pocket = list(reversed(deepcopy(pocket)))

    model_locator = replace(record.ligand_atom_locator, model_id="1")
    model_ambiguous = deepcopy(ligand)
    model_row = deepcopy(ligand[ligand_index])
    model_row["model_num"] = "1"
    model_ambiguous[ligand_index]["model_num"] = "1"
    model_ambiguous.append(model_row)
    altloc_locator = replace(record.ligand_atom_locator, altloc="A")
    altloc_ambiguous = deepcopy(ligand)
    altloc_row = deepcopy(ligand[ligand_index])
    altloc_row["altloc"] = "A"
    altloc_ambiguous[ligand_index]["altloc"] = "A"
    altloc_ambiguous.append(altloc_row)
    residue_model_locator = replace(record.residue_atom_locator, model_id="1")
    residue_altloc_locator = replace(record.residue_atom_locator, altloc="A")
    residue_insertion_locator = replace(
        record.residue_atom_locator, insertion_code="A"
    )
    ligand_insertion_locator = replace(
        record.ligand_atom_locator, insertion_code="A"
    )
    tampered_predecessor = dict(fixed_payloads)
    tampered_predecessor[CONTRACT_SOURCE] += b"\n# in-memory tamper\n"
    invalid_schema = replace(record, pair_record_schema_version="invalid")
    unsupported = replace(record, explicit_bond_authority_class="distance_only")
    missing_provenance = replace(record, explicit_bond_provenance_id="")

    observations = {
        "contract predecessor SHA drift": not _precondition(tampered_predecessor),
        "invalid canonical record schema": not validate_record(invalid_schema),
        "unsupported authority": not validate_record(unsupported),
        "missing authority provenance": not validate_record(missing_provenance),
        "legacy projection mismatch": fails_closed(
            bundle(sample_row=legacy_sample)
        ),
        "event pair mismatch": fails_closed(
            bundle(event_rows=[event_pair])
        ),
        "zero pair-table rows": fails_closed(bundle(pair_rows=[])),
        "multiple pair-table rows": fails_closed(
            bundle(pair_rows=[deepcopy(pair), deepcopy(pair)])
        ),
        "missing pocket match": fails_closed(bundle(
            pocket_table_payload=table_payload(pocket, missing_pocket),
            pocket_table_rows=missing_pocket,
        )),
        "duplicate pocket match": fails_closed(bundle(
            pocket_table_payload=table_payload(pocket, duplicate_pocket),
            pocket_table_rows=duplicate_pocket,
        )),
        "missing ligand match": fails_closed(bundle(
            ligand_table_payload=table_payload(ligand, missing_ligand),
            ligand_table_rows=missing_ligand,
        )),
        "duplicate ligand match": fails_closed(bundle(
            ligand_table_payload=table_payload(ligand, duplicate_ligand),
            ligand_table_rows=duplicate_ligand,
        )),
        "target residue mismatch": fails_closed(
            bundle(event_rows=[wrong_residue_event])
        ),
        "ligand instance mismatch": fails_closed(
            bundle(event_rows=[wrong_ligand_event])
        ),
        "pair-table residue atom_site mismatch": fails_closed(
            bundle(pair_rows=[residue_site_pair])
        ),
        "pair-table ligand atom_site mismatch": fails_closed(
            bundle(pair_rows=[ligand_site_pair])
        ),
        "coordinate mismatch": fails_closed(
            bundle(pair_rows=[coordinate_pair])
        ),
        "row-count mismatch": fails_closed(
            bundle(sample_row=row_count_sample)
        ),
        "row-order drift": (
            lambda observation: fails_closed(observation)
            and observation.source_binding_valid is False
        )(bundle(
            pocket_table_payload=table_payload(pocket, drifted_pocket),
            pocket_table_rows=drifted_pocket,
        )),
        "non-zero index base": fails_closed(bundle(model_index_base=1)),
        "model ambiguity": validate_covapie_atom_table_locator_exact_one_v1(
            model_locator, model_ambiguous,
            expected_het_id=sample["expected_het_id"],
        )[1] is None,
        "altloc ambiguity": validate_covapie_atom_table_locator_exact_one_v1(
            altloc_locator, altloc_ambiguous,
            expected_het_id=sample["expected_het_id"],
        )[1] is None,
        "missing target table": fails_closed(bundle(
            pocket_table_payload=_csv_bytes(tuple(pocket[0]), []),
            pocket_table_rows=[],
        )),
        "residue model field unavailable": (
            validate_covapie_atom_table_locator_exact_one_v1(
                residue_model_locator, pocket,
                expected_het_id=sample["expected_het_id"],
            ) == (0, None)
        ),
        "residue altloc field unavailable": (
            validate_covapie_atom_table_locator_exact_one_v1(
                residue_altloc_locator, pocket,
                expected_het_id=sample["expected_het_id"],
            ) == (0, None)
        ),
        "residue insertion-code field unavailable": (
            validate_covapie_atom_table_locator_exact_one_v1(
                residue_insertion_locator, pocket,
                expected_het_id=sample["expected_het_id"],
            ) == (0, None)
        ),
        "ligand insertion-code field unavailable": (
            validate_covapie_atom_table_locator_exact_one_v1(
                ligand_insertion_locator, ligand,
                expected_het_id=sample["expected_het_id"],
            ) == (0, None)
        ),
    }
    if tuple(observations) != FAILURE_CASES:
        raise ValueError("failure observations do not match frozen case order")
    return observations


def _source_row(
    role: str, path: Path, payload: bytes, reference: str, read_count: int,
) -> dict[str, Any]:
    count: str | int = ""
    if path.suffix == ".csv":
        count = len(_csv_rows(payload))
    return {
        "source_role": role,
        "source_path": path.as_posix(),
        "source_sha256": _sha(payload),
        "committed_in_base": True,
        "data_row_count_if_tabular": count,
        "referenced_by_sample_index_row_id": reference,
        "read_count": read_count,
        "verified": True,
    }


def _overall_validation_success(
    *,
    precondition: bool,
    all_canonical: bool,
    all_mappings: bool,
    row_order_ok: bool,
    all_failure_cases_verified: bool,
) -> bool:
    """Make executable failure completeness mandatory for issue resolution."""
    values = (
        precondition,
        all_canonical,
        all_mappings,
        row_order_ok,
        all_failure_cases_verified,
    )
    return all(type(value) is bool and value for value in values)


def derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(
    repo_root: Path,
) -> dict[str, Any]:
    """Derive all observations from BASE-bound bytes, retaining no bad record."""
    fixed_payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    precondition = _precondition(fixed_payloads)
    source_rows = [
        _source_row("encoding_contract_source", CONTRACT_SOURCE, fixed_payloads[CONTRACT_SOURCE], "", 1),
        _source_row("encoding_contract_manifest", CONTRACT_MANIFEST, fixed_payloads[CONTRACT_MANIFEST], "", 1),
        _source_row("predecessor_issue_inventory", PREDECESSOR_ISSUES, fixed_payloads[PREDECESSOR_ISSUES], "", 1),
        _source_row("current_representation_audit", CURRENT_REPRESENTATION_AUDIT, fixed_payloads[CURRENT_REPRESENTATION_AUDIT], "", 1),
        _source_row("final_dataset_index", FINAL_DATASET_INDEX, fixed_payloads[FINAL_DATASET_INDEX], "", 1),
    ]
    index_rows = _csv_rows(fixed_payloads[FINAL_DATASET_INDEX])
    canonical_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    records: list[contract.CovalentBondAtomPairCanonicalRecordDesign] = []
    sample_observations: list[
        CovalentBondAtomPairSampleEvidenceValidationObservation
    ] = []
    row_order_ok = True
    failure_context: dict[str, Any] | None = None
    for sample in index_rows:
        sample_id = sample["sample_index_row_id"]
        paths = {
            "event": Path(sample["covalent_event_table_path"]),
            "pair": Path(sample["ligand_residue_atom_pair_table_path"]),
            "pocket": Path(sample["pocket_atom_table_path"]),
            "ligand": Path(sample["ligand_atom_table_path"]),
        }
        payloads: dict[str, bytes] = {}
        parsed_repeats_by_role: dict[str, list[list[dict[str, str]]]] = {}
        for role, path in paths.items():
            repeats = [_base_bytes(repo_root, path) for _ in range(3 if role in {"pocket", "ligand"} else 1)]
            if any(value != repeats[0] for value in repeats[1:]):
                row_order_ok = False
            parsed_repeats_by_role[role] = [_csv_rows(value) for value in repeats]
            if any(
                rows != parsed_repeats_by_role[role][0]
                for rows in parsed_repeats_by_role[role][1:]
            ):
                row_order_ok = False
            payloads[role] = repeats[0]
            source_rows.append(_source_row(
                f"{role}_table", path, repeats[0], sample_id, len(repeats)
            ))
        events = _csv_rows(payloads["event"])
        pairs = _csv_rows(payloads["pair"])
        pockets = _csv_rows(payloads["pocket"])
        ligands = _csv_rows(payloads["ligand"])
        observation = (
            validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
                contract_precondition_verified=precondition,
                sample_row=sample,
                event_rows=events,
                pair_rows=pairs,
                pocket_table_payload=payloads["pocket"],
                pocket_table_rows=pockets,
                ligand_table_payload=payloads["ligand"],
                ligand_table_rows=ligands,
                expected_pocket_table_sha256=_sha(payloads["pocket"]),
                expected_ligand_table_sha256=_sha(payloads["ligand"]),
                model_index_base=0,
            )
        )
        sample_observations.append(observation)
        record = observation.canonical_record
        if record is None or len(events) != 1 or len(pairs) != 1:
            row_order_ok = False
            continue
        event, pair = events[0], pairs[0]
        if failure_context is None:
            failure_context = {
                "fixed_payloads": fixed_payloads,
                "sample": deepcopy(sample),
                "event": deepcopy(event),
                "pair": deepcopy(pair),
                "pocket_payload": payloads["pocket"],
                "pocket": deepcopy(pockets),
                "ligand_payload": payloads["ligand"],
                "ligand": deepcopy(ligands),
                "record": record,
            }
        if observation.record_retained:
            records.append(record)
        canonical_valid = observation.canonical_record_valid
        legacy = observation.legacy_projection
        legacy_matches = observation.legacy_projection_matches
        authority = observation.explicit_authority_valid
        canonical_rows.append({
            "sample_index_row_id": sample_id,
            "event_id": record.residue_atom_locator.event_id,
            "pdb_id": record.residue_atom_locator.pdb_id,
            "pair_record_schema_version": record.pair_record_schema_version,
            "residue_entity_role": record.residue_atom_locator.entity_role,
            "residue_auth_asym_id": record.residue_atom_locator.auth_asym_id,
            "residue_auth_seq_id": record.residue_atom_locator.auth_seq_id,
            "residue_label_asym_id": record.residue_atom_locator.label_asym_id,
            "residue_label_seq_id": record.residue_atom_locator.label_seq_id,
            "residue_comp_id": record.residue_atom_locator.comp_id,
            "residue_atom_name": record.residue_atom_locator.atom_name,
            "ligand_entity_role": record.ligand_atom_locator.entity_role,
            "ligand_auth_asym_id": record.ligand_atom_locator.auth_asym_id,
            "ligand_auth_seq_id": record.ligand_atom_locator.auth_seq_id,
            "ligand_label_asym_id": record.ligand_atom_locator.label_asym_id,
            "ligand_label_seq_id": record.ligand_atom_locator.label_seq_id,
            "ligand_comp_id": record.ligand_atom_locator.comp_id,
            "ligand_atom_name": record.ligand_atom_locator.atom_name,
            "explicit_bond_authority_class": record.explicit_bond_authority_class,
            "explicit_bond_provenance_id": record.explicit_bond_provenance_id,
            "canonical_record_valid": canonical_valid,
            "legacy_projection": legacy,
            "observed_legacy_value": event.get("covalent_bond_atom_pair", ""),
            "legacy_projection_matches": legacy_matches,
            "event_pair_value_matches": legacy == event.get("covalent_bond_atom_pair"),
            "pair_table_value_matches": legacy == pair.get("covalent_bond_atom_pair"),
            "final_index_value_matches": legacy == sample.get("covalent_bond_atom_pair"),
            "explicit_authority_preserved": authority,
            "verified": (
                observation.record_retained
                and canonical_valid and legacy_matches and authority
            ),
        })
        for role, table, locator, count_key in (
            ("target_residue_atom", pockets, record.residue_atom_locator, "pocket_atom_count"),
            ("ligand_atom", ligands, record.ligand_atom_locator, "ligand_atom_count"),
        ):
            target_key = "pocket" if role == "target_residue_atom" else "ligand"
            count = (
                observation.residue_candidate_match_count
                if role == "target_residue_atom"
                else observation.ligand_candidate_match_count
            )
            index = (
                observation.residue_row_index_0based
                if role == "target_residue_atom"
                else observation.ligand_row_index_0based
            )
            repeat_observations = []
            for repeated_table in parsed_repeats_by_role[target_key]:
                repeated_count, repeated_index = (
                    validate_covapie_atom_table_locator_exact_one_v1(
                        locator, repeated_table,
                        expected_het_id=sample["expected_het_id"],
                    )
                )
                repeated_site = (
                    repeated_table[repeated_index].get("atom_site_id", "")
                    if repeated_index is not None else ""
                )
                repeat_observations.append(
                    (repeated_count, repeated_index, repeated_site)
                )
            repeat_stable = (
                len(repeat_observations) == 3
                and len(set(repeat_observations)) == 1
            )
            row_order_ok = row_order_ok and repeat_stable
            expected_count = int(sample[count_key])
            count_ok = len(table) == expected_count
            row_order_ok = row_order_ok and count_ok
            matched = table[index] if index is not None else {}
            expected_site_key = (
                "residue_atom_site_id" if role == "target_residue_atom"
                else "ligand_atom_site_id"
            )
            prefix = "residue" if role == "target_residue_atom" else "ligand"
            site_ok = (
                observation.residue_atom_site_matches
                if role == "target_residue_atom"
                else observation.ligand_atom_site_matches
            )
            coords_ok = (
                observation.residue_coordinate_matches
                if role == "target_residue_atom"
                else observation.ligand_coordinate_matches
            )
            optional_unavailable = [
                name for name, column in (
                    ("model_id", "model_num"), ("insertion_code", "insertion_code"),
                    ("altloc", "altloc"),
                )
                if getattr(locator, name) and column not in (table[0] if table else {})
            ]
            used = [
                name for name in (
                    "event_id", "pdb_id", "auth_asym_id", "auth_seq_id",
                    "label_asym_id", "label_seq_id", "comp_id", "atom_name",
                    "model_id", "altloc", "insertion_code",
                ) if getattr(locator, name)
            ]
            success = (
                count == 1 and index is not None and count_ok and site_ok
                and coords_ok and not optional_unavailable and repeat_stable
                and observation.mapping_retained
                and observation.source_binding_valid
            )
            mapping_fields = (
                (
                    "sample_preparation_input_id", "pdb_id", "residue_name",
                    "atom_name", "auth_asym_id", "auth_seq_id",
                    "label_asym_id", "label_seq_id", "chain_id",
                    "residue_index",
                )
                if role == "target_residue_atom"
                else (
                    "sample_preparation_input_id", "pdb_id", "expected_het_id",
                    "ligand_comp_id", "atom_name", "auth_asym_id",
                    "auth_seq_id", "label_asym_id", "label_seq_id",
                    "is_covalent_ligand_atom",
                )
            )
            mapping_rows.append({
                "sample_index_row_id": sample_id,
                "event_id": locator.event_id,
                "pdb_id": locator.pdb_id,
                "entity_role": role,
                "target_table_path": paths[target_key].as_posix(),
                "target_table_sha256": _sha(payloads[target_key]),
                "target_table_data_row_count": len(table),
                "mapping_key_fields": "|".join(mapping_fields),
                "nonempty_locator_fields_used": "|".join(used),
                "optional_locator_fields_unavailable": "|".join(optional_unavailable),
                "candidate_match_count": count,
                "expected_match_count": 1,
                "matched_row_index_0based": "" if index is None else index,
                "matched_atom_site_id": matched.get("atom_site_id", ""),
                "pair_table_expected_atom_site_id": pair.get(expected_site_key, ""),
                "atom_site_id_matches": site_ok,
                "coordinate_crosscheck_passed": coords_ok,
                "distance_used_for_mapping_selection": False,
                "source_row_order_sha_bound": (
                    count_ok and repeat_stable
                    and observation.source_binding_valid
                ),
                "model_index_base": 0,
                "mapping_outcome": "mapped" if success else "invalid",
                "mapping_reason": "exact_one_identity_mapping" if success else "mapping_or_crosscheck_failed",
                "verified": success,
            })
    all_canonical = len(canonical_rows) == 11 and all(_truth(row["verified"]) for row in canonical_rows)
    residue_rows = [row for row in mapping_rows if row["entity_role"] == "target_residue_atom"]
    ligand_rows = [row for row in mapping_rows if row["entity_role"] == "ligand_atom"]
    all_mappings = (
        len(mapping_rows) == 22 and all(_truth(row["verified"]) for row in mapping_rows)
    )
    if failure_context is None:
        failure_observations = {name: False for name in FAILURE_CASES}
    else:
        failure_observations = _failure_observations(**failure_context)
    failure_rows = []
    for name in FAILURE_CASES:
        fails_closed = failure_observations[name]
        failure_rows.append({
            "failure_case": name,
            "expected_outcome": "invalid",
            "observed_outcome": "invalid" if fails_closed else "validated",
            "fails_closed": fails_closed,
            "record_retained": not fails_closed,
            "mapping_retained": not fails_closed,
            "issue_resolved": False,
            "verified": fails_closed,
        })
    all_failure_cases_verified = (
        len(failure_rows) == len(FAILURE_CASES)
        and all(_truth(row["verified"]) for row in failure_rows)
    )
    success = _overall_validation_success(
        precondition=precondition,
        all_canonical=all_canonical,
        all_mappings=all_mappings,
        row_order_ok=row_order_ok,
        all_failure_cases_verified=all_failure_cases_verified,
    )
    decision = CovalentBondAtomPairEncodingContractValidationDecision(
        schema_version=SCHEMA_VERSION,
        outcome="validated" if success else "invalid",
        contract_precondition_verified=precondition,
        current_canonical_record_count=len(canonical_rows),
        canonical_record_valid_count=sum(_truth(row["canonical_record_valid"]) for row in canonical_rows),
        exact_one_residue_mapping_count=sum(_truth(row["verified"]) for row in residue_rows),
        exact_one_ligand_mapping_count=sum(_truth(row["verified"]) for row in ligand_rows),
        pair_table_atom_site_crosscheck_count=sum(
            observation.atom_site_crosscheck_valid
            for observation in sample_observations
        ),
        pair_table_coordinate_crosscheck_count=sum(
            observation.coordinate_crosscheck_valid
            for observation in sample_observations
        ),
        legacy_projection_match_count=sum(_truth(row["legacy_projection_matches"]) for row in canonical_rows),
        explicit_bond_authority_preserved_count=sum(_truth(row["explicit_authority_preserved"]) for row in canonical_rows),
        model_index_base=0,
        row_order_validation_completed=row_order_ok and len(mapping_rows) == 22,
        encoding_contract_validation_completed=success,
        atom_pair_issue_resolved=success,
        provider_issue_resolved=False,
        atom_pair_ready_for_downstream_contracts=success,
        ready_for_tensorization=False,
        feature_semantics_audit_completed=False,
        ready_for_training=False,
        recommended_next_step=(
            RECOMMENDED_NEXT_STEP if success
            else "resolve_current_canonical_atom_pair_evidence_contradictions_v1"
        ),
    )
    issue_rows = _csv_rows(fixed_payloads[PREDECESSOR_ISSUES])
    if success:
        for row in issue_rows:
            if row["issue_id"] == "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED":
                row["successor_effective_status"] = "resolved"
                row["successor_transition_stage"] = STAGE
                row["successor_transition_action"] = (
                    "resolved_by_validated_structured_records_and_exact_atom_table_mapping_v1"
                )
                row["successor_transition_evidence"] = (
                    "11/11 canonical records valid; 11/11 residue exact-one mappings; "
                    "11/11 ligand exact-one mappings; 11/11 atom-site crosschecks; "
                    "legacy projection and explicit authority preserved"
                )
    return {
        "decision": decision,
        "records": tuple(records),
        "sample_observations": tuple(sample_observations),
        "source_rows": source_rows,
        "canonical_rows": canonical_rows,
        "mapping_rows": mapping_rows,
        "failure_rows": failure_rows,
        "all_failure_cases_verified": all_failure_cases_verified,
        "issue_rows": issue_rows,
    }


def _manifest(result: dict[str, Any]) -> dict[str, Any]:
    decision = result["decision"]
    issue_rows = result["issue_rows"]
    open_issues = [
        row["issue_id"] for row in issue_rows
        if row["successor_effective_status"] == "open"
    ]
    evidence_hashes = {
        name: _sha(payload) for name, payload in _non_manifest_artifacts(result).items()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "encoding_contract_validation_completed": decision.encoding_contract_validation_completed,
        "validation_outcome": decision.outcome,
        "current_canonical_record_count": decision.current_canonical_record_count,
        "canonical_record_valid_count": decision.canonical_record_valid_count,
        "exact_one_residue_mapping_count": decision.exact_one_residue_mapping_count,
        "exact_one_ligand_mapping_count": decision.exact_one_ligand_mapping_count,
        "atom_table_mapping_row_count": len(result["mapping_rows"]),
        "pair_table_atom_site_crosscheck_count": decision.pair_table_atom_site_crosscheck_count,
        "pair_table_coordinate_crosscheck_count": decision.pair_table_coordinate_crosscheck_count,
        "failure_matrix_executable": True,
        "failure_matrix_all_cases_verified": result["all_failure_cases_verified"],
        "failure_matrix_required_for_issue_resolution": True,
        "legacy_projection_match_count": decision.legacy_projection_match_count,
        "explicit_bond_authority_preserved_count": decision.explicit_bond_authority_preserved_count,
        "row_index_base": 0,
        "row_order_validation_completed": decision.row_order_validation_completed,
        "row_indices_materialized_as_metadata_only": True,
        "row_index_semantic_identity": False,
        "pair_tensor_materialized": False,
        "distance_used_for_mapping_selection": False,
        "nearest_atom_fallback_used": False,
        "first_row_fallback_used": False,
        "atom_pair_issue_resolved": decision.atom_pair_issue_resolved,
        "provider_issue_resolved": False,
        "issue_status_changed": decision.atom_pair_issue_resolved,
        "resolved_issue_count": 1 if decision.atom_pair_issue_resolved else 0,
        "new_issue_count": 0,
        "deleted_issue_count": 0,
        "effective_open_issue_count": len(open_issues),
        "effective_open_issues": open_issues,
        "atom_pair_ready_for_downstream_contracts": decision.atom_pair_ready_for_downstream_contracts,
        "next_training_preparation_blocker": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "ready_for_tensorization": False,
        "pair_tensor_shape_defined": False,
        "negative_pair_construction_defined": False,
        "negative_sampling_defined": False,
        "pair_loss_mask_defined": False,
        "pair_head_implemented": False,
        "pair_contrastive_loss_implemented": False,
        "provider_used": False, "download_used": False, "raw_read": False,
        "raw_write": False, "checkpoint_access": False, "model_changed": False,
        "dataloader_changed": False, "forward_changed": False,
        "loss_changed": False, "training_used": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "ready_for_training": False,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "source_inventory_row_count": len(result["source_rows"]),
        "canonical_record_validation_row_count": len(result["canonical_rows"]),
        "failure_matrix_row_count": len(result["failure_rows"]),
        "issue_inventory_row_count": len(result["issue_rows"]),
        "evidence_sha256": evidence_hashes,
        "recommended_next_step": decision.recommended_next_step,
    }


def _non_manifest_artifacts(result: dict[str, Any]) -> dict[str, bytes]:
    issue_columns = tuple(result["issue_rows"][0])
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(SOURCE_COLUMNS, result["source_rows"]),
        CANONICAL_MATRIX_FILE: _csv_bytes(CANONICAL_COLUMNS, result["canonical_rows"]),
        MAPPING_MATRIX_FILE: _csv_bytes(MAPPING_COLUMNS, result["mapping_rows"]),
        FAILURE_MATRIX_FILE: _csv_bytes(FAILURE_COLUMNS, result["failure_rows"]),
        ISSUE_INVENTORY_FILE: _csv_bytes(issue_columns, result["issue_rows"]),
    }


def build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    result = derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(
        repo_root
    )
    artifacts = _non_manifest_artifacts(result)
    artifacts[MANIFEST_FILE] = (
        json.dumps(_manifest(result), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return artifacts
