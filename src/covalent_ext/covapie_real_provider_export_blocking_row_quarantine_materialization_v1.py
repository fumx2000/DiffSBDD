"""Materialize the V1 fail-closed quarantine for real-provider blocking rows.

This stage reads only artifacts committed in ``BASE_COMMIT``.  Raw structure
paths are treated as opaque provenance strings.  The quarantine is forward
looking and applies only to the real-provider export ingestion path; it does
not rewrite the provider sidecar or retroactively alter current canonical
sample artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from copy import deepcopy
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

__all__ = (
    "RealProviderExportBlockingRowQuarantineMaterializationDecision",
    "RealProviderExportQuarantineFailureCaseDecision",
    "build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1",
    "derive_covapie_real_provider_export_blocking_row_quarantine_materialization_v1",
    "evaluate_covapie_real_provider_export_quarantine_failure_case_v1",
    "serialize_covapie_real_provider_export_blocking_row_quarantine_materialization_decision_v1",
)

BASE_COMMIT = "8ebb40bd4ee105a89698376722422a0728b05fba"
BASE_PARENT = "e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf"
BASE_TREE = "33af4d39f86464bfdf4ab9fd993ab1e2f0846b3c"
BASE_SUBJECT = "add CovaPIE real-provider export blocking-row policy audit v1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE real-provider export blocking-row quarantine v1"
)
SCHEMA_VERSION = (
    "covapie_real_provider_export_blocking_row_quarantine_materialization_v1"
)
STAGE = SCHEMA_VERSION
QUARANTINE_SCOPE = "real_provider_export_ingestion_path_only"
OUTCOME_MATERIALIZED = "materialized"
OUTCOME_INVALID = "invalid"
ISSUE_ID = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
ATOM_PAIR_ISSUE_ID = "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED"
ADMISSION_RULE_ID = "ADMIT_004"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
AUDIT_DISPOSITION = "quarantine_required_pending_provider_reexport"
QUARANTINE_STATUS = "active_pending_provider_reexport"
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_final_training_feature_semantics_and_unknown_atom_policy_v1"
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
EXCLUSION_SCOPES = (
    "provider_admitted_candidate_set",
    "provider_export_passed_set",
    "future_provider_derived_canonical_materialization_input",
    "tensorization_input",
    "training_input",
)
EXCLUSION_REASON = (
    "active fail-closed quarantine pending provider re-export "
    "or human-curated explicit evidence"
)

POLICY_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_real_provider_export_blocking_rows_"
    "resolution_or_quarantine_policy_audit_v1"
)
POLICY_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_real_provider_export_blocking_rows_"
    "resolution_or_quarantine_policy_audit_v1.py"
)
POLICY_MANIFEST = POLICY_ROOT / (
    "covapie_real_provider_export_blocking_rows_"
    "resolution_or_quarantine_policy_audit_manifest.json"
)
POLICY_SOURCE_INVENTORY = POLICY_ROOT / (
    "covapie_real_provider_export_blocking_row_source_inventory.csv"
)
POLICY_BLOCKING_MATRIX = POLICY_ROOT / (
    "covapie_real_provider_export_blocking_row_audit_matrix.csv"
)
POLICY_SUFFICIENCY_MATRIX = POLICY_ROOT / (
    "covapie_real_provider_export_insertion_code_evidence_sufficiency_matrix.csv"
)
POLICY_MATRIX = POLICY_ROOT / (
    "covapie_real_provider_export_resolution_or_quarantine_policy_matrix.csv"
)
POLICY_ISSUES = POLICY_ROOT / (
    "covapie_real_provider_export_issue_readiness_inventory.csv"
)
PROVIDER_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1"
)
PROVIDER_SIDECAR = PROVIDER_ROOT / (
    "covapie_covalent_residue_locator_real_provider_export_sidecar.csv"
)
INTEGRATION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_sidecar_integration_gate_v1"
)
INTEGRATION_OVERLAY = INTEGRATION_ROOT / (
    "covapie_covalent_residue_locator_real_provider_integration_overlay.csv"
)
INTEGRATION_EVIDENCE = INTEGRATION_ROOT / (
    "covapie_covalent_residue_locator_real_provider_integration_evidence_audit.csv"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
ATOM_PAIR_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_v1/"
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_manifest.json"
)

FROZEN_SHA256 = {
    POLICY_SOURCE: "f7b00e7e152928983274d371db357fe42fa61ce0d7ab4faf7fe604385ee716c1",
    POLICY_MANIFEST: "5d3d802e295dd8775f908fe75ef1238980de7c4082684dbe47ba97a4440ad66d",
    POLICY_SOURCE_INVENTORY: "b8c5a16c05967f70c388c96bbaca5459d3799f402d6c7648e5995ae876ead69d",
    POLICY_BLOCKING_MATRIX: "0d2299d4d95dcbf328407063269ca73e92a9501fa24ef2d477b45971085e70fa",
    POLICY_SUFFICIENCY_MATRIX: "8cc17d04453f05043ef7f94b0f155a3ee86c4222cccca0697a8535c74d85d633",
    POLICY_MATRIX: "cde3b64e70401ab9bb9f13f9eedeb2ddf28f29f3de7855fa77c618872a14f4d2",
    POLICY_ISSUES: "09ee8271157343c4fd39c2edd73e38d6f0e896b8da247d8e3a8588c0b1cd0afa",
    PROVIDER_SIDECAR: "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    INTEGRATION_OVERLAY: "cc4c5965083340a040e4e1fc531da03bd74471e20fdc521ce92464d1d359627a",
    INTEGRATION_EVIDENCE: "c5efc4610762004829897064965bb4e06a1390d52c9f97254e66fbb1c7c899ec",
    FINAL_DATASET_INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    ATOM_PAIR_MANIFEST: "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152",
}
SOURCE_ROLES = (
    ("policy_audit_source", POLICY_SOURCE, "materialization predecessor implementation"),
    ("policy_audit_manifest", POLICY_MANIFEST, "audit_outcome=audited_policy_frozen"),
    ("policy_audit_source_inventory", POLICY_SOURCE_INVENTORY, "whole committed artifact"),
    ("blocking_row_audit_matrix", POLICY_BLOCKING_MATRIX, f"audit_disposition={AUDIT_DISPOSITION}"),
    ("insertion_code_evidence_sufficiency_matrix", POLICY_SUFFICIENCY_MATRIX, "whole committed artifact"),
    ("executable_policy_matrix", POLICY_MATRIX, "fails_closed=true"),
    ("predecessor_issue_inventory", POLICY_ISSUES, f"issue_id={ISSUE_ID}"),
    ("original_provider_sidecar", PROVIDER_SIDECAR, "provider_export_status=exported_blocking"),
    ("provider_integration_overlay", INTEGRATION_OVERLAY, "binding_row_id join"),
    ("provider_integration_evidence", INTEGRATION_EVIDENCE, "binding_row_id join"),
    ("current_final_dataset_index_scope_boundary", FINAL_DATASET_INDEX, "11 committed current canonical rows"),
    ("atom_pair_validation_scope_boundary", ATOM_PAIR_MANIFEST, "validation_outcome=validated"),
)

OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
SOURCE_INVENTORY_FILE = "covapie_real_provider_export_quarantine_source_inventory.csv"
QUARANTINE_INVENTORY_FILE = "covapie_real_provider_export_quarantine_inventory.csv"
EXCLUSION_MATRIX_FILE = "covapie_real_provider_export_quarantine_exclusion_matrix.csv"
FAILURE_MATRIX_FILE = "covapie_real_provider_export_quarantine_failure_matrix.csv"
ISSUE_INVENTORY_FILE = "covapie_real_provider_export_quarantine_issue_readiness_inventory.csv"
MANIFEST_FILE = (
    "covapie_real_provider_export_blocking_row_quarantine_"
    "materialization_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    QUARANTINE_INVENTORY_FILE,
    EXCLUSION_MATRIX_FILE,
    FAILURE_MATRIX_FILE,
    ISSUE_INVENTORY_FILE,
    MANIFEST_FILE,
)

SOURCE_COLUMNS = (
    "source_role", "source_path", "source_sha256", "committed_in_base",
    "data_row_count_if_tabular", "selector_or_symbol",
    "referenced_quarantine_row_count", "verified",
)
QUARANTINE_COLUMNS = (
    "quarantine_row_order", "quarantine_id", "blocking_row_identity",
    "provider_export_row_identity", "candidate_identity", "pdb_id",
    "ligand_identity", "residue_name", "residue_chain_or_asym_id",
    "residue_sequence_id", "observed_insertion_code_state",
    "observed_insertion_code", "admission_rule_id", "admit_004_outcome",
    "admit_004_reason", "audit_disposition", "quarantine_reason",
    "quarantine_status", "original_provider_export_status",
    "original_provider_row_source_path", "original_provider_row_source_sha256",
    "original_provider_row_selector", "provider_provenance_source_id",
    "provider_provenance_sha256", "provider_row_mutated",
    "provider_value_resolved", "provider_reexport_required",
    "provider_admitted_membership", "provider_passed_membership",
    "future_canonical_materialization_membership", "tensorization_membership",
    "training_membership", "verified",
)
EXCLUSION_COLUMNS = (
    "quarantine_id", "blocking_row_identity", "candidate_identity",
    "exclusion_scope", "expected_membership", "observed_membership",
    "exclusion_reason", "source_quarantine_status", "fails_closed", "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "expected_outcome", "observed_outcome",
    "failure_detected", "candidate_quarantine_registry_valid",
    "candidate_exclusion_registry_valid",
    "provider_issue_transition_applied",
    "provider_issue_effective_status",
    "ready_for_feature_semantics_audit", "ready_for_tensorization",
    "ready_for_training", "fails_closed", "verified",
)

FAILURE_CASES = (
    "predecessor_sha_drift",
    "policy_audit_outcome_not_frozen",
    "quarantine_ready_false",
    "blocking_row_count_not_11",
    "duplicate_blocking_identity",
    "non_quarantine_audit_disposition",
    "source_provider_row_missing",
    "source_provider_row_sha_drift",
    "source_selector_mismatch",
    "provider_status_not_exported_blocking",
    "admit_004_outcome_mismatch",
    "admit_004_reason_mismatch",
    "duplicate_quarantine_id",
    "missing_quarantine_row",
    "quarantine_identity_projection_mismatch",
    "provider_row_mutation_attempted",
    "provider_value_falsely_marked_resolved",
    "provider_reexport_requirement_removed",
    "provider_admitted_membership_true",
    "provider_passed_membership_true",
    "future_canonical_membership_true",
    "tensorization_membership_true",
    "training_membership_true",
    "existing_final_dataset_mutation_attempted",
    "atom_pair_issue_regressed_to_open",
    "provider_issue_resolved_before_exact11_quarantine",
    "provider_issue_resolved_before_exact55_exclusions",
    "feature_semantics_audit_prematurely_completed",
    "ready_for_training_prematurely_true",
    "quarantine_provider_export_identity_mismatch",
    "quarantine_pdb_or_ligand_projection_mismatch",
    "quarantine_residue_projection_mismatch",
    "quarantine_insertion_state_or_code_mismatch",
    "quarantine_admit_004_projection_mismatch",
    "quarantine_reason_mismatch",
    "exclusion_reason_mismatch",
)
_SHA_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)


@dataclass(frozen=True)
class RealProviderExportBlockingRowQuarantineMaterializationDecision:
    schema_version: str
    outcome: str
    predecessor_verified: bool
    quarantine_scope_compatible: bool
    blocking_row_count: int
    quarantine_row_count: int
    unique_quarantine_row_count: int
    quarantine_identity_projection_verified: bool
    source_provenance_preserved_count: int
    provider_admitted_exclusion_count: int
    provider_passed_exclusion_count: int
    future_canonical_exclusion_count: int
    tensorization_exclusion_count: int
    training_exclusion_count: int
    provider_rows_mutated: bool
    existing_final_dataset_modified: bool
    quarantine_materialized: bool
    provider_blocking_effect_contained: bool
    provider_issue_resolved: bool
    provider_values_resolved: bool
    provider_reexport_still_required: bool
    ready_for_feature_semantics_audit: bool
    ready_for_tensorization: bool
    feature_semantics_audit_completed: bool
    ready_for_training: bool
    recommended_next_step: str


@dataclass(frozen=True)
class RealProviderExportQuarantineFailureCaseDecision:
    failure_case: str
    outcome: str
    failure_detected: bool
    candidate_quarantine_registry_valid: bool
    candidate_exclusion_registry_valid: bool
    provider_issue_transition_applied: bool
    provider_issue_effective_status: str
    ready_for_feature_semantics_audit: bool
    ready_for_tensorization: bool
    ready_for_training: bool


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(
        ("git", *args), cwd=repo_root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base_bytes(repo_root: Path, path: Path) -> bytes:
    if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw"):
        raise ValueError(f"unsafe committed source path: {path}")
    spec = f"{BASE_COMMIT}:{path.as_posix()}"
    _git(repo_root, "cat-file", "-e", spec)
    payload = _git(repo_root, "show", spec)
    if _sha(payload) != FROZEN_SHA256[path]:
        raise ValueError(f"BASE source SHA256 mismatch: {path}")
    return payload


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != tuple(reader.fieldnames) for row in rows):
        raise ValueError("invalid CSV row")
    return rows


def _csv_bytes(columns: tuple[str, ...], rows: list[Mapping[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != columns:
            raise ValueError("output row schema/order mismatch")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _json(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if type(value) is not dict:
        raise ValueError("JSON document must be an object")
    return value


def _keyed(
    rows: list[dict[str, str]], key: str
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError(f"missing/duplicate {key}")
        result[value] = row
    return result


def _predecessor_manifest_verified(manifest: Mapping[str, Any]) -> bool:
    expected = {
        "audit_outcome": "audited_policy_frozen",
        "real_provider_export_blocking_rows_policy_audit_completed": True,
        "blocking_row_count": 11,
        "unique_blocking_row_count": 11,
        "resolvable_from_committed_evidence_count": 0,
        "quarantine_required_count": 11,
        "contradictory_or_invalid_count": 0,
        "all_rows_classified": True,
        "resolution_or_quarantine_policy_frozen": True,
        "policy_matrix_executable": True,
        "policy_matrix_classifier_consistency_verified": True,
        "provider_rows_mutated": False,
        "quarantine_materialized": False,
        "provider_issue_resolved": False,
        "ready_for_quarantine_materialization": True,
        "ready_for_feature_semantics_audit": False,
        "ready_for_tensorization": False,
        "ready_for_training": False,
    }
    return all(manifest.get(key) == value for key, value in expected.items())


def _scope_compatible(
    final_rows: list[dict[str, str]], atom_pair_manifest: Mapping[str, Any]
) -> bool:
    return (
        len(final_rows) == 11
        and len({row.get("sample_index_row_id", "") for row in final_rows}) == 11
        and all(
            row.get("sample_index_status")
            == "sample_index_materialized_from_qa_passed_sample"
            and row.get("ready_for_training_current_step") == "False"
            for row in final_rows
        )
        and atom_pair_manifest.get("validation_outcome") == "validated"
        and atom_pair_manifest.get("encoding_contract_validation_completed") is True
        and atom_pair_manifest.get("current_canonical_record_count") == 11
        and atom_pair_manifest.get("canonical_record_valid_count") == 11
        and atom_pair_manifest.get("atom_pair_issue_resolved") is True
        and atom_pair_manifest.get("atom_pair_ready_for_downstream_contracts") is True
        and atom_pair_manifest.get("provider_issue_resolved") is False
        and atom_pair_manifest.get("effective_open_issues") == [ISSUE_ID]
        and atom_pair_manifest.get("ready_for_tensorization") is False
        and atom_pair_manifest.get("ready_for_training") is False
    )


def _source_rows(payloads: Mapping[Path, bytes]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role, path, selector in SOURCE_ROLES:
        payload = payloads[path]
        count: int | str = ""
        if path.suffix == ".csv":
            count = len(_csv_rows(payload))
        rows.append({
            "source_role": role,
            "source_path": path.as_posix(),
            "source_sha256": _sha(payload),
            "committed_in_base": "true",
            "data_row_count_if_tabular": count,
            "selector_or_symbol": selector,
            "referenced_quarantine_row_count": 11 if role not in (
                "policy_audit_source_inventory",
                "insertion_code_evidence_sufficiency_matrix",
                "executable_policy_matrix",
            ) else 0,
            "verified": "true",
        })
    return rows


def _expected_quarantine_row_v1(
    *,
    row_order: int,
    audit_row: Mapping[str, str],
    provider_row: Mapping[str, str],
) -> dict[str, Any]:
    """Return the complete frozen projection for one quarantine row."""
    if type(row_order) is not int or row_order < 1:
        raise TypeError("row_order must be an exact positive int")
    identity = f"REAL_LOCATOR_BINDING_{row_order:06d}"
    if (
        audit_row.get("blocking_row_identity") != identity
        or audit_row.get("provider_export_row_identity") != identity
        or provider_row.get("binding_row_id") != identity
    ):
        raise ValueError("provider/blocking identity projection mismatch")
    if (
        audit_row.get("observed_insertion_code_state")
        != provider_row.get("covalent_residue_insertion_code_state")
        or audit_row.get("observed_insertion_code")
        != provider_row.get("covalent_residue_insertion_code")
    ):
        raise ValueError("insertion-code projection mismatch")
    if (
        audit_row.get("admission_rule_id") != ADMISSION_RULE_ID
        or audit_row.get("admit_004_outcome") != "blocked"
        or audit_row.get("admit_004_reason") != UNKNOWN_REASON
        or audit_row.get("audit_disposition") != AUDIT_DISPOSITION
    ):
        raise ValueError("audit decision projection mismatch")
    row = {
        "quarantine_row_order": row_order,
        "quarantine_id": f"REAL_PROVIDER_EXPORT_QUARANTINE_{row_order:06d}",
        "blocking_row_identity": identity,
        "provider_export_row_identity": identity,
        "candidate_identity": audit_row["candidate_identity"],
        "pdb_id": audit_row["pdb_id"],
        "ligand_identity": audit_row["ligand_identity"],
        "residue_name": audit_row["residue_name"],
        "residue_chain_or_asym_id": audit_row["residue_chain_or_asym_id"],
        "residue_sequence_id": audit_row["residue_sequence_id"],
        "observed_insertion_code_state": audit_row[
            "observed_insertion_code_state"
        ],
        "observed_insertion_code": audit_row["observed_insertion_code"],
        "admission_rule_id": ADMISSION_RULE_ID,
        "admit_004_outcome": "blocked",
        "admit_004_reason": UNKNOWN_REASON,
        "audit_disposition": AUDIT_DISPOSITION,
        "quarantine_reason": audit_row["audit_reason"],
        "quarantine_status": QUARANTINE_STATUS,
        "original_provider_export_status": provider_row[
            "provider_export_status"
        ],
        "original_provider_row_source_path": PROVIDER_SIDECAR.as_posix(),
        "original_provider_row_source_sha256": FROZEN_SHA256[
            PROVIDER_SIDECAR
        ],
        "original_provider_row_selector": f"binding_row_id={identity}",
        "provider_provenance_source_id": provider_row[
            "covalent_residue_locator_provenance_source_id"
        ],
        "provider_provenance_sha256": provider_row[
            "covalent_residue_locator_provenance_sha256"
        ],
        "provider_row_mutated": "false",
        "provider_value_resolved": "false",
        "provider_reexport_required": "true",
        "provider_admitted_membership": "false",
        "provider_passed_membership": "false",
        "future_canonical_materialization_membership": "false",
        "tensorization_membership": "false",
        "training_membership": "false",
        "verified": "true",
    }
    if tuple(row) != QUARANTINE_COLUMNS:
        raise ValueError("internal quarantine schema/order drift")
    if type(row["quarantine_row_order"]) is not int or any(
        type(value) is not str
        for key, value in row.items()
        if key != "quarantine_row_order"
    ):
        raise TypeError("internal quarantine field type drift")
    return row


def _quarantine_rows(
    audit_rows: list[dict[str, str]],
    sidecar_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    sidecars = _keyed(sidecar_rows, "binding_row_id")
    return [
        _expected_quarantine_row_v1(
            row_order=index,
            audit_row=audit,
            provider_row=sidecars[
                f"REAL_LOCATOR_BINDING_{index:06d}"
            ],
        )
        for index, audit in enumerate(audit_rows, 1)
    ]


def _expected_exclusion_row_v1(
    quarantine_row: Mapping[str, Any],
    exclusion_scope: str,
) -> dict[str, str]:
    """Return the complete frozen contract for one exclusion row."""
    if exclusion_scope not in EXCLUSION_SCOPES:
        raise ValueError("unsupported exclusion scope")
    row = {
        "quarantine_id": quarantine_row["quarantine_id"],
        "blocking_row_identity": quarantine_row["blocking_row_identity"],
        "candidate_identity": quarantine_row["candidate_identity"],
        "exclusion_scope": exclusion_scope,
        "expected_membership": "false",
        "observed_membership": "false",
        "exclusion_reason": EXCLUSION_REASON,
        "source_quarantine_status": QUARANTINE_STATUS,
        "fails_closed": "true",
        "verified": "true",
    }
    if tuple(row) != EXCLUSION_COLUMNS:
        raise ValueError("internal exclusion schema/order drift")
    if any(type(value) is not str for value in row.values()):
        raise TypeError("internal exclusion field type drift")
    return row


def _exclusion_rows(
    quarantine_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for quarantine in quarantine_rows:
        for scope in EXCLUSION_SCOPES:
            result.append(_expected_exclusion_row_v1(quarantine, scope))
    return result


def _apply_provider_issue_transition_after_success_v1(
    predecessor_issue_rows: list[dict[str, str]],
    *,
    materialization_success: bool,
) -> list[dict[str, str]]:
    """Apply the provider transition only after all success evidence is valid."""
    if type(materialization_success) is not bool:
        raise TypeError("materialization_success must be an exact bool")
    result = deepcopy(predecessor_issue_rows)
    if not materialization_success:
        return result
    provider = next(row for row in result if row["issue_id"] == ISSUE_ID)
    provider["successor_effective_status"] = "resolved"
    provider["successor_transition_stage"] = STAGE
    provider["successor_transition_action"] = (
        "resolved_by_fail_closed_quarantine_containment_v1"
    )
    provider["successor_transition_evidence"] = (
        "11/11 blocking rows materialized in active quarantine; "
        "11/11 excluded from provider-admitted, provider-passed, future "
        "provider-derived canonical materialization, tensorization, and "
        "training sets; provider rows and values unchanged; provider re-export "
        "remains required"
    )
    return result


def _state(
    audit_rows: list[dict[str, str]],
    sidecar_rows: list[dict[str, str]],
    quarantine_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    candidate_issue_rows: list[dict[str, str]],
    predecessor_issue_rows: list[dict[str, str]],
    policy_manifest: dict[str, Any],
    *,
    predecessor_sha_verified: bool = True,
    source_sidecar_sha_verified: bool = True,
    scope_compatible: bool = True,
    failure_matrix_complete: bool = False,
    existing_final_dataset_modified: bool = False,
    atom_pair_validation_artifacts_modified: bool = False,
    feature_semantics_audit_completed: bool = False,
    ready_for_training: bool = False,
) -> dict[str, Any]:
    return {
        "audit_rows": audit_rows,
        "sidecar_rows": sidecar_rows,
        "quarantine_rows": quarantine_rows,
        "exclusion_rows": exclusion_rows,
        "candidate_issue_rows": candidate_issue_rows,
        "predecessor_issue_rows": predecessor_issue_rows,
        "policy_manifest": policy_manifest,
        "predecessor_sha_verified": predecessor_sha_verified,
        "source_sidecar_sha_verified": source_sidecar_sha_verified,
        "scope_compatible": scope_compatible,
        "failure_matrix_complete": failure_matrix_complete,
        "existing_final_dataset_modified": existing_final_dataset_modified,
        "atom_pair_validation_artifacts_modified": atom_pair_validation_artifacts_modified,
        "feature_semantics_audit_completed": feature_semantics_audit_completed,
        "ready_for_training": ready_for_training,
    }


def _provider_issue_effective_status(
    issue_rows: list[dict[str, str]],
) -> str:
    try:
        provider = _keyed(issue_rows, "issue_id")[ISSUE_ID]
    except (KeyError, TypeError, ValueError):
        return "invalid"
    return provider.get("successor_effective_status", "")


def _prevalidation_issue_inventory_valid(
    candidate_issue_rows: list[dict[str, str]],
    predecessor_issue_rows: list[dict[str, str]],
) -> bool:
    try:
        candidate = _keyed(candidate_issue_rows, "issue_id")
        predecessor = _keyed(predecessor_issue_rows, "issue_id")
    except (KeyError, TypeError, ValueError):
        return False
    return (
        candidate_issue_rows == predecessor_issue_rows
        and set(candidate) == set(predecessor)
        and candidate[ISSUE_ID].get("successor_effective_status") == "open"
        and candidate[ATOM_PAIR_ISSUE_ID]
        == predecessor[ATOM_PAIR_ISSUE_ID]
        and candidate[ATOM_PAIR_ISSUE_ID].get("successor_effective_status")
        == "resolved"
    )


def _successor_issue_inventory_valid(
    predecessor_issue_rows: list[dict[str, str]],
    successor_issue_rows: list[dict[str, str]],
    *,
    materialization_success: bool,
) -> bool:
    try:
        predecessor = _keyed(predecessor_issue_rows, "issue_id")
        successor = _keyed(successor_issue_rows, "issue_id")
    except (KeyError, TypeError, ValueError):
        return False
    if set(predecessor) != set(successor):
        return False
    if not materialization_success:
        return (
            successor_issue_rows == predecessor_issue_rows
            and successor[ISSUE_ID].get("successor_effective_status") == "open"
        )
    transition_fields = {
        "successor_effective_status",
        "successor_transition_stage",
        "successor_transition_action",
        "successor_transition_evidence",
    }
    for issue_id, original in predecessor.items():
        current = successor[issue_id]
        changed = {
            key for key in original if original[key] != current.get(key)
        }
        if issue_id == ISSUE_ID:
            if (
                changed != transition_fields
                or current.get("successor_effective_status") != "resolved"
                or current.get("successor_transition_stage") != STAGE
                or current.get("successor_transition_action")
                != "resolved_by_fail_closed_quarantine_containment_v1"
            ):
                return False
        elif current != original:
            return False
    return successor[ATOM_PAIR_ISSUE_ID] == predecessor[ATOM_PAIR_ISSUE_ID]


def _provider_issue_transition_metrics(
    predecessor_issue_rows: list[dict[str, str]],
    successor_issue_rows: list[dict[str, str]],
) -> tuple[int, bool]:
    try:
        predecessor = _keyed(predecessor_issue_rows, "issue_id")
        successor = _keyed(successor_issue_rows, "issue_id")
    except (KeyError, TypeError, ValueError):
        return 0, False
    changed_issue_ids = [
        issue_id
        for issue_id in predecessor
        if predecessor[issue_id] != successor.get(issue_id)
    ]
    provider_changed_fields = {
        key
        for key in predecessor[ISSUE_ID]
        if predecessor[ISSUE_ID][key]
        != successor.get(ISSUE_ID, {}).get(key)
    }
    expected_fields = {
        "successor_effective_status",
        "successor_transition_stage",
        "successor_transition_action",
        "successor_transition_evidence",
    }
    return (
        len(provider_changed_fields),
        changed_issue_ids == [ISSUE_ID]
        and provider_changed_fields == expected_fields,
    )


def _provider_source_protection_valid(state: Mapping[str, Any]) -> bool:
    try:
        sidecars = state["sidecar_rows"]
        sidecar_map = _keyed(sidecars, "binding_row_id")
    except (KeyError, TypeError, ValueError):
        return False
    expected_identities = {
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    }
    return (
        state.get("source_sidecar_sha_verified") is True
        and len(sidecars) == 11
        and set(sidecar_map) == expected_identities
        and all(
            source.get("provider_export_status") == "exported_blocking"
            and source.get("provider_export_blocking_reason") == UNKNOWN_REASON
            and source.get("covalent_residue_insertion_code_state") == "unknown"
            and source.get("covalent_residue_insertion_code") == ""
            and bool(
                source.get("covalent_residue_locator_provenance_source_id")
            )
            and _SHA_RE.fullmatch(
                source.get("covalent_residue_locator_provenance_sha256", "")
            )
            is not None
            for source in sidecars
        )
    )


def _quarantine_inventory_exact_schema_valid(rows: object) -> bool:
    return (
        type(rows) is list
        and all(
            type(row) is dict and tuple(row) == QUARANTINE_COLUMNS
            for row in rows
        )
    )


def _quarantine_inventory_exact_types_valid(rows: object) -> bool:
    return (
        _quarantine_inventory_exact_schema_valid(rows)
        and all(
            type(row["quarantine_row_order"]) is int
            and all(
                type(value) is str
                for key, value in row.items()
                if key != "quarantine_row_order"
            )
            for row in rows
        )
    )


def _exclusion_inventory_exact_schema_valid(rows: object) -> bool:
    return (
        type(rows) is list
        and all(
            type(row) is dict and tuple(row) == EXCLUSION_COLUMNS
            for row in rows
        )
    )


def _exclusion_inventory_exact_types_valid(rows: object) -> bool:
    return (
        _exclusion_inventory_exact_schema_valid(rows)
        and all(
            all(type(value) is str for value in row.values())
            for row in rows
        )
    )


def _candidate_quarantine_registry_valid(state: Mapping[str, Any]) -> bool:
    try:
        audits = state["audit_rows"]
        sidecars = state["sidecar_rows"]
        quarantines = state["quarantine_rows"]
        if (
            type(audits) is not list
            or type(sidecars) is not list
            or type(quarantines) is not list
            or any(type(row) is not dict for row in audits)
            or any(type(row) is not dict for row in sidecars)
            or any(type(row) is not dict for row in quarantines)
        ):
            return False
        sidecar_map = _keyed(sidecars, "binding_row_id")
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
    expected_identities = [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]
    if (
        len(audits) != 11
        or [row.get("blocking_row_identity") for row in audits]
        != expected_identities
        or len(quarantines) != 11
        or len(sidecar_map) != 11
        or set(sidecar_map) != set(expected_identities)
        or any(
            row.get("audit_disposition") != AUDIT_DISPOSITION
            or row.get("provider_export_status") != "exported_blocking"
            or row.get("admission_rule_id") != ADMISSION_RULE_ID
            or row.get("admit_004_outcome") != "blocked"
            or row.get("admit_004_reason") != UNKNOWN_REASON
            or row.get("observed_insertion_code_state") != "unknown"
            or row.get("observed_insertion_code") != ""
            or row.get("source_selector")
            != f"binding_row_id={row.get('blocking_row_identity')}"
            or row.get("source_sha256") != FROZEN_SHA256[PROVIDER_SIDECAR]
            for row in audits
        )
    ):
        return False
    if not _provider_source_protection_valid(state):
        return False
    try:
        expected_rows = [
            _expected_quarantine_row_v1(
                row_order=index,
                audit_row=audit,
                provider_row=sidecar_map[
                    f"REAL_LOCATOR_BINDING_{index:06d}"
                ],
            )
            for index, audit in enumerate(audits, 1)
        ]
    except (KeyError, TypeError, ValueError):
        return False
    return (
        quarantines == expected_rows
        and _quarantine_inventory_exact_schema_valid(quarantines)
        and _quarantine_inventory_exact_types_valid(quarantines)
    )


def _candidate_exclusion_registry_valid(state: Mapping[str, Any]) -> bool:
    if not _candidate_quarantine_registry_valid(state):
        return False
    try:
        quarantines = state["quarantine_rows"]
        exclusions = state["exclusion_rows"]
        if (
            type(quarantines) is not list
            or type(exclusions) is not list
            or any(type(row) is not dict for row in quarantines)
            or any(type(row) is not dict for row in exclusions)
        ):
            return False
    except (KeyError, TypeError):
        return False
    try:
        expected_rows = [
            _expected_exclusion_row_v1(quarantine, scope)
            for quarantine in quarantines
            for scope in EXCLUSION_SCOPES
        ]
    except (KeyError, TypeError, ValueError):
        return False
    return (
        exclusions == expected_rows
        and len(exclusions) == 55
        and _exclusion_inventory_exact_schema_valid(exclusions)
        and _exclusion_inventory_exact_types_valid(exclusions)
    )


def _core_materialization_valid(state: Mapping[str, Any]) -> bool:
    """Validate all materialization evidence without requiring resolution."""
    try:
        candidate_issues = state["candidate_issue_rows"]
        predecessor_issues = state["predecessor_issue_rows"]
    except (KeyError, TypeError):
        return False
    return (
        state.get("predecessor_sha_verified") is True
        and _predecessor_manifest_verified(state.get("policy_manifest", {}))
        and state.get("scope_compatible") is True
        and _candidate_quarantine_registry_valid(state)
        and _candidate_exclusion_registry_valid(state)
        and _provider_source_protection_valid(state)
        and state.get("existing_final_dataset_modified") is False
        and state.get("atom_pair_validation_artifacts_modified") is False
        and _prevalidation_issue_inventory_valid(
            candidate_issues, predecessor_issues
        )
        and state.get("failure_matrix_complete") is True
        and state.get("feature_semantics_audit_completed") is False
        and state.get("ready_for_training") is False
    )


def _materialization_evaluation(state: Mapping[str, Any]) -> dict[str, Any]:
    quarantine_valid = _candidate_quarantine_registry_valid(state)
    exclusion_valid = _candidate_exclusion_registry_valid(state)
    core_valid = _core_materialization_valid(state)
    predecessor_issues = state.get("predecessor_issue_rows", [])
    successor_issues = _apply_provider_issue_transition_after_success_v1(
        predecessor_issues, materialization_success=core_valid
    )
    successor_valid = _successor_issue_inventory_valid(
        predecessor_issues, successor_issues,
        materialization_success=core_valid,
    )
    success = core_valid and successor_valid
    transition_applied = successor_issues != predecessor_issues
    changed_field_count, applied_exactly_once = (
        _provider_issue_transition_metrics(
            predecessor_issues, successor_issues
        )
    )
    return {
        "candidate_quarantine_registry_valid": quarantine_valid,
        "candidate_exclusion_registry_valid": exclusion_valid,
        "core_materialization_valid": core_valid,
        "materialization_success": success,
        "issue_rows": successor_issues,
        "provider_issue_transition_applied": transition_applied,
        "provider_issue_transition_changed_field_count": changed_field_count,
        "provider_issue_transition_applied_exactly_once": (
            applied_exactly_once
        ),
        "provider_issue_effective_status": _provider_issue_effective_status(
            successor_issues
        ),
    }


def _decision_from_state(
    state: Mapping[str, Any],
) -> RealProviderExportBlockingRowQuarantineMaterializationDecision:
    evaluation = _materialization_evaluation(state)
    valid = evaluation["materialization_success"]
    quarantines = state.get("quarantine_rows", [])
    exclusions = state.get("exclusion_rows", [])
    scope_counts = {
        scope: sum(
            row.get("exclusion_scope") == scope
            and row.get("observed_membership") == "false"
            for row in exclusions
        )
        for scope in EXCLUSION_SCOPES
    }
    identities = [row.get("quarantine_id") for row in quarantines]
    projection = identities == [
        f"REAL_PROVIDER_EXPORT_QUARANTINE_{index:06d}"
        for index in range(1, 12)
    ]
    provenance_count = sum(
        bool(row.get("provider_provenance_source_id"))
        and _SHA_RE.fullmatch(str(row.get("provider_provenance_sha256", "")))
        is not None
        for row in quarantines
    )
    return RealProviderExportBlockingRowQuarantineMaterializationDecision(
        schema_version=SCHEMA_VERSION,
        outcome=OUTCOME_MATERIALIZED if valid else OUTCOME_INVALID,
        predecessor_verified=bool(
            state.get("predecessor_sha_verified")
            and _predecessor_manifest_verified(state.get("policy_manifest", {}))
        ),
        quarantine_scope_compatible=state.get("scope_compatible") is True,
        blocking_row_count=len(state.get("audit_rows", [])),
        quarantine_row_count=len(quarantines),
        unique_quarantine_row_count=len(set(identities)),
        quarantine_identity_projection_verified=projection,
        source_provenance_preserved_count=provenance_count,
        provider_admitted_exclusion_count=scope_counts[EXCLUSION_SCOPES[0]],
        provider_passed_exclusion_count=scope_counts[EXCLUSION_SCOPES[1]],
        future_canonical_exclusion_count=scope_counts[EXCLUSION_SCOPES[2]],
        tensorization_exclusion_count=scope_counts[EXCLUSION_SCOPES[3]],
        training_exclusion_count=scope_counts[EXCLUSION_SCOPES[4]],
        provider_rows_mutated=any(
            row.get("provider_row_mutated") != "false" for row in quarantines
        ),
        existing_final_dataset_modified=(
            state.get("existing_final_dataset_modified") is not False
        ),
        quarantine_materialized=valid,
        provider_blocking_effect_contained=valid,
        provider_issue_resolved=valid,
        provider_values_resolved=False,
        provider_reexport_still_required=True,
        ready_for_feature_semantics_audit=valid,
        ready_for_tensorization=False,
        feature_semantics_audit_completed=False,
        ready_for_training=False,
        recommended_next_step=RECOMMENDED_NEXT_STEP if valid else "",
    )


def _apply_failure_case(state: dict[str, Any], case: str) -> None:
    audits = state["audit_rows"]
    sidecars = state["sidecar_rows"]
    quarantines = state["quarantine_rows"]
    exclusions = state["exclusion_rows"]
    issues = state["candidate_issue_rows"]
    if case == "predecessor_sha_drift":
        state["predecessor_sha_verified"] = False
    elif case == "policy_audit_outcome_not_frozen":
        state["policy_manifest"]["audit_outcome"] = "invalid"
    elif case == "quarantine_ready_false":
        state["policy_manifest"]["ready_for_quarantine_materialization"] = False
    elif case == "blocking_row_count_not_11":
        audits.pop()
    elif case == "duplicate_blocking_identity":
        audits[1]["blocking_row_identity"] = audits[0]["blocking_row_identity"]
    elif case == "non_quarantine_audit_disposition":
        audits[0]["audit_disposition"] = (
            "explicitly_resolvable_from_committed_evidence"
        )
    elif case == "source_provider_row_missing":
        sidecars.pop()
    elif case == "source_provider_row_sha_drift":
        state["source_sidecar_sha_verified"] = False
    elif case == "source_selector_mismatch":
        audits[0]["source_selector"] = "binding_row_id=WRONG"
    elif case == "provider_status_not_exported_blocking":
        sidecars[0]["provider_export_status"] = "passed"
    elif case == "admit_004_outcome_mismatch":
        audits[0]["admit_004_outcome"] = "passed"
    elif case == "admit_004_reason_mismatch":
        audits[0]["admit_004_reason"] = "WRONG"
    elif case == "duplicate_quarantine_id":
        quarantines[1]["quarantine_id"] = quarantines[0]["quarantine_id"]
    elif case == "missing_quarantine_row":
        quarantines.pop()
    elif case == "quarantine_identity_projection_mismatch":
        quarantines[0]["blocking_row_identity"] = "REAL_LOCATOR_BINDING_999999"
    elif case == "provider_row_mutation_attempted":
        quarantines[0]["provider_row_mutated"] = "true"
    elif case == "provider_value_falsely_marked_resolved":
        quarantines[0]["provider_value_resolved"] = "true"
    elif case == "provider_reexport_requirement_removed":
        quarantines[0]["provider_reexport_required"] = "false"
    elif case == "provider_admitted_membership_true":
        quarantines[0]["provider_admitted_membership"] = "true"
    elif case == "provider_passed_membership_true":
        quarantines[0]["provider_passed_membership"] = "true"
    elif case == "future_canonical_membership_true":
        quarantines[0]["future_canonical_materialization_membership"] = "true"
    elif case == "tensorization_membership_true":
        quarantines[0]["tensorization_membership"] = "true"
    elif case == "training_membership_true":
        quarantines[0]["training_membership"] = "true"
    elif case == "existing_final_dataset_mutation_attempted":
        state["existing_final_dataset_modified"] = True
    elif case == "atom_pair_issue_regressed_to_open":
        next(
            row for row in issues if row["issue_id"] == ATOM_PAIR_ISSUE_ID
        )["successor_effective_status"] = "open"
    elif case == "provider_issue_resolved_before_exact11_quarantine":
        quarantines.pop()
        state["candidate_issue_rows"] = (
            _apply_provider_issue_transition_after_success_v1(
                state["predecessor_issue_rows"],
                materialization_success=True,
            )
        )
    elif case == "provider_issue_resolved_before_exact55_exclusions":
        exclusions.pop()
        state["candidate_issue_rows"] = (
            _apply_provider_issue_transition_after_success_v1(
                state["predecessor_issue_rows"],
                materialization_success=True,
            )
        )
    elif case == "feature_semantics_audit_prematurely_completed":
        state["feature_semantics_audit_completed"] = True
    elif case == "ready_for_training_prematurely_true":
        state["ready_for_training"] = True
    elif case == "quarantine_provider_export_identity_mismatch":
        quarantines[0]["provider_export_row_identity"] = (
            "REAL_LOCATOR_BINDING_999999"
        )
    elif case == "quarantine_pdb_or_ligand_projection_mismatch":
        quarantines[0]["pdb_id"] = "WRONG"
    elif case == "quarantine_residue_projection_mismatch":
        quarantines[0]["residue_name"] = "WRONG"
    elif case == "quarantine_insertion_state_or_code_mismatch":
        quarantines[0]["observed_insertion_code_state"] = "absent"
    elif case == "quarantine_admit_004_projection_mismatch":
        quarantines[0]["admit_004_outcome"] = "passed"
    elif case == "quarantine_reason_mismatch":
        quarantines[0]["quarantine_reason"] = "WRONG"
    elif case == "exclusion_reason_mismatch":
        exclusions[0]["exclusion_reason"] = "WRONG"
    else:
        raise ValueError(f"unknown failure case: {case}")


@lru_cache(maxsize=None)
def _cached_baseline_state(repo_root: Path) -> dict[str, Any]:
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    manifest = _json(payloads[POLICY_MANIFEST])
    audits = _csv_rows(payloads[POLICY_BLOCKING_MATRIX])
    sidecars = _csv_rows(payloads[PROVIDER_SIDECAR])
    predecessor_issues = _csv_rows(payloads[POLICY_ISSUES])
    quarantines = _quarantine_rows(audits, sidecars)
    exclusions = _exclusion_rows(quarantines)
    prevalidation_issues = deepcopy(predecessor_issues)
    compatible = _scope_compatible(
        _csv_rows(payloads[FINAL_DATASET_INDEX]),
        _json(payloads[ATOM_PAIR_MANIFEST]),
    )
    return _state(
        audits, sidecars, quarantines, exclusions, prevalidation_issues,
        predecessor_issues, manifest, scope_compatible=compatible,
    )


def _baseline_state(repo_root: Path) -> dict[str, Any]:
    return deepcopy(_cached_baseline_state(repo_root.resolve()))


def evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
    repo_root: Path, failure_case: str
) -> RealProviderExportQuarantineFailureCaseDecision:
    if failure_case not in FAILURE_CASES:
        raise ValueError(f"unknown failure case: {failure_case}")
    state = _baseline_state(repo_root)
    state["failure_matrix_complete"] = True
    _apply_failure_case(state, failure_case)
    evaluation = _materialization_evaluation(state)
    decision = _decision_from_state(state)
    failure_detected = decision.outcome == OUTCOME_INVALID
    return RealProviderExportQuarantineFailureCaseDecision(
        failure_case=failure_case,
        outcome=decision.outcome,
        failure_detected=failure_detected,
        candidate_quarantine_registry_valid=(
            evaluation["candidate_quarantine_registry_valid"]
        ),
        candidate_exclusion_registry_valid=(
            evaluation["candidate_exclusion_registry_valid"]
        ),
        provider_issue_transition_applied=(
            evaluation["provider_issue_transition_applied"]
        ),
        provider_issue_effective_status=(
            evaluation["provider_issue_effective_status"]
        ),
        ready_for_feature_semantics_audit=(
            decision.ready_for_feature_semantics_audit
        ),
        ready_for_tensorization=decision.ready_for_tensorization,
        ready_for_training=decision.ready_for_training,
    )


def _failure_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows = []
    for case in FAILURE_CASES:
        decision = (
            evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
                repo_root, case
            )
        )
        verified = (
            decision.outcome == OUTCOME_INVALID
            and decision.failure_detected
            and not decision.provider_issue_transition_applied
            and decision.provider_issue_effective_status == "open"
            and not decision.ready_for_feature_semantics_audit
            and not decision.ready_for_tensorization
            and not decision.ready_for_training
        )
        rows.append({
            "failure_case": case,
            "expected_outcome": OUTCOME_INVALID,
            "observed_outcome": decision.outcome,
            "failure_detected": (
                "true" if decision.failure_detected else "false"
            ),
            "candidate_quarantine_registry_valid": (
                "true"
                if decision.candidate_quarantine_registry_valid
                else "false"
            ),
            "candidate_exclusion_registry_valid": (
                "true"
                if decision.candidate_exclusion_registry_valid
                else "false"
            ),
            "provider_issue_transition_applied": (
                "true"
                if decision.provider_issue_transition_applied
                else "false"
            ),
            "provider_issue_effective_status": (
                decision.provider_issue_effective_status
            ),
            "ready_for_feature_semantics_audit": (
                "true"
                if decision.ready_for_feature_semantics_audit
                else "false"
            ),
            "ready_for_tensorization": (
                "true" if decision.ready_for_tensorization else "false"
            ),
            "ready_for_training": (
                "true" if decision.ready_for_training else "false"
            ),
            "fails_closed": "true" if verified else "false",
            "verified": "true" if verified else "false",
        })
    return rows


def derive_covapie_real_provider_export_blocking_row_quarantine_materialization_v1(
    repo_root: Path,
) -> dict[str, Any]:
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    state = _baseline_state(repo_root)
    failure_rows = _failure_rows(repo_root)
    state["failure_matrix_complete"] = (
        len(failure_rows) == len(FAILURE_CASES)
        and all(row["verified"] == "true" for row in failure_rows)
    )
    evaluation = _materialization_evaluation(state)
    decision = _decision_from_state(state)
    if decision.outcome != OUTCOME_MATERIALIZED:
        if not decision.quarantine_scope_compatible:
            raise ValueError("provider_quarantine_scope_conflict_requires_review")
        raise ValueError("quarantine materialization failed closed")
    return {
        "decision": decision,
        "source_rows": _source_rows(payloads),
        "quarantine_rows": state["quarantine_rows"],
        "exclusion_rows": state["exclusion_rows"],
        "failure_rows": failure_rows,
        "issue_rows": evaluation["issue_rows"],
        "prevalidation_issue_rows": state["candidate_issue_rows"],
        "predecessor_issue_rows": state["predecessor_issue_rows"],
        "materialization_evaluation": evaluation,
        "payloads": payloads,
    }


def serialize_covapie_real_provider_export_blocking_row_quarantine_materialization_decision_v1(
    decision: RealProviderExportBlockingRowQuarantineMaterializationDecision,
) -> bytes:
    if (
        type(decision)
        is not RealProviderExportBlockingRowQuarantineMaterializationDecision
    ):
        raise TypeError("decision has the wrong exact type")
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _non_manifest_artifacts(result: Mapping[str, Any]) -> dict[str, bytes]:
    issue_columns = tuple(result["issue_rows"][0])
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(
            SOURCE_COLUMNS, result["source_rows"]
        ),
        QUARANTINE_INVENTORY_FILE: _csv_bytes(
            QUARANTINE_COLUMNS, result["quarantine_rows"]
        ),
        EXCLUSION_MATRIX_FILE: _csv_bytes(
            EXCLUSION_COLUMNS, result["exclusion_rows"]
        ),
        FAILURE_MATRIX_FILE: _csv_bytes(
            FAILURE_COLUMNS, result["failure_rows"]
        ),
        ISSUE_INVENTORY_FILE: _csv_bytes(
            issue_columns, result["issue_rows"]
        ),
    }


def _manifest(
    result: Mapping[str, Any], artifacts: Mapping[str, bytes]
) -> dict[str, Any]:
    decision = result["decision"]
    evaluation = result["materialization_evaluation"]
    failures = result["failure_rows"]
    all_failures_verified = (
        len(failures) == len(FAILURE_CASES)
        and all(row["verified"] == "true" for row in failures)
    )
    failure_observations_truthful = all(
        row["observed_outcome"] == OUTCOME_INVALID
        and row["failure_detected"] == "true"
        and row["provider_issue_transition_applied"] == "false"
        and row["provider_issue_effective_status"] == "open"
        and row["ready_for_feature_semantics_audit"] == "false"
        and row["ready_for_tensorization"] == "false"
        and row["ready_for_training"] == "false"
        for row in failures
    )
    failure_registry_validity_recorded = all(
        row["candidate_quarantine_registry_valid"] in ("true", "false")
        and row["candidate_exclusion_registry_valid"] in ("true", "false")
        for row in failures
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "quarantine_materialization_completed": True,
        "materialization_outcome": decision.outcome,
        "quarantine_scope": QUARANTINE_SCOPE,
        "quarantine_scope_compatible": decision.quarantine_scope_compatible,
        "blocking_row_count": decision.blocking_row_count,
        "quarantine_row_count": decision.quarantine_row_count,
        "unique_quarantine_row_count": decision.unique_quarantine_row_count,
        "quarantine_exclusion_matrix_row_count": len(result["exclusion_rows"]),
        "quarantine_identity_projection_verified": (
            decision.quarantine_identity_projection_verified
        ),
        "quarantine_inventory_full_field_projection_verified": (
            evaluation["candidate_quarantine_registry_valid"]
        ),
        "quarantine_inventory_exact_schema_verified": (
            _quarantine_inventory_exact_schema_valid(
                result["quarantine_rows"]
            )
        ),
        "quarantine_inventory_exact_types_verified": (
            _quarantine_inventory_exact_types_valid(
                result["quarantine_rows"]
            )
        ),
        "exclusion_inventory_full_field_projection_verified": (
            evaluation["candidate_exclusion_registry_valid"]
        ),
        "exclusion_inventory_exact_schema_verified": (
            _exclusion_inventory_exact_schema_valid(
                result["exclusion_rows"]
            )
        ),
        "exclusion_inventory_exact_types_verified": (
            _exclusion_inventory_exact_types_valid(
                result["exclusion_rows"]
            )
        ),
        "source_provenance_preserved_count": (
            decision.source_provenance_preserved_count
        ),
        "provider_admitted_exclusion_count": (
            decision.provider_admitted_exclusion_count
        ),
        "provider_passed_exclusion_count": (
            decision.provider_passed_exclusion_count
        ),
        "future_canonical_exclusion_count": (
            decision.future_canonical_exclusion_count
        ),
        "tensorization_exclusion_count": decision.tensorization_exclusion_count,
        "training_exclusion_count": decision.training_exclusion_count,
        "provider_rows_mutated": False,
        "provider_rows_present": True,
        "provider_rows_quarantined": True,
        "provider_values_resolved": False,
        "provider_reexport_still_required": True,
        "provider_coverage_complete": False,
        "existing_final_dataset_modified": False,
        "existing_canonical_samples_deleted": False,
        "atom_pair_validation_artifacts_modified": False,
        "quarantine_retroactively_invalidates_current_canonical_samples": False,
        "provider_blocking_effect_contained": True,
        "provider_issue_resolved": True,
        "prevalidation_provider_issue_effective_status": (
            _provider_issue_effective_status(
                result["prevalidation_issue_rows"]
            )
        ),
        "provider_issue_transition_applied_after_validation": (
            evaluation["provider_issue_transition_applied"]
        ),
        "provider_issue_transition_preconditions_verified": (
            evaluation["core_materialization_valid"]
        ),
        "provider_issue_transition_applied_exactly_once": (
            evaluation["provider_issue_transition_applied_exactly_once"]
        ),
        "provider_issue_transition_changed_field_count": (
            evaluation["provider_issue_transition_changed_field_count"]
        ),
        "issue_status_changed": True,
        "resolved_issue_count": 1,
        "new_issue_count": 0,
        "deleted_issue_count": 0,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "atom_pair_issue_resolved": True,
        "atom_pair_ready_for_downstream_contracts": True,
        "failure_matrix_executable": True,
        "failure_matrix_all_cases_verified": all_failures_verified,
        "failure_observation_semantics_truthful": (
            failure_observations_truthful
        ),
        "failure_matrix_uses_actual_registry_validity": (
            failure_registry_validity_recorded
        ),
        "invalid_candidate_provider_issue_effective_status": (
            "open"
            if {row["provider_issue_effective_status"] for row in failures}
            == {"open"}
            else "invalid"
        ),
        "failure_matrix_required_for_issue_resolution": True,
        "ready_for_feature_semantics_audit": True,
        "ready_for_tensorization": False,
        "pair_tensor_materialized": False,
        "pair_tensor_shape_defined": False,
        "negative_pair_construction_defined": False,
        "negative_sampling_defined": False,
        "pair_loss_mask_defined": False,
        "pair_head_implemented": False,
        "pair_contrastive_loss_implemented": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "ready_for_training": False,
        "provider_used": False,
        "network_used": False,
        "download_used": False,
        "raw_read": False,
        "raw_write": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "training_used": False,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "source_inventory_row_count": len(result["source_rows"]),
        "quarantine_inventory_row_count": len(result["quarantine_rows"]),
        "exclusion_matrix_row_count": len(result["exclusion_rows"]),
        "failure_matrix_row_count": len(result["failure_rows"]),
        "issue_inventory_row_count": len(result["issue_rows"]),
        "evidence_sha256": {
            name: _sha(payload) for name, payload in artifacts.items()
        },
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    result = (
        derive_covapie_real_provider_export_blocking_row_quarantine_materialization_v1(
            repo_root
        )
    )
    artifacts = _non_manifest_artifacts(result)
    artifacts[MANIFEST_FILE] = (
        json.dumps(_manifest(result, artifacts), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return artifacts
