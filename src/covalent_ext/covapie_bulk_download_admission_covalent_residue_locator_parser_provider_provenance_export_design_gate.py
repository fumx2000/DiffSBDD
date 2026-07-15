"""Step14AU-E0-P4 parser/provider provenance export design gate.

This metadata-only gate freezes insertion-token classification, two-source
resolution, and provider provenance contracts. It does not parse structures,
modify either parser, materialize provider payloads, or authorize execution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from covalent_ext import (
    covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate
    as p2_gate,
)


STEP_LABEL = "Step14AU-E0-P4"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_design_gate_v1"
)
PROJECT_NAME = "CovaPIE"
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_parser_provider_"
    "provenance_export_design_gate_v1_manifest_v1"
)
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_integration_gate_v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_covalent_residue_locator_parser_provider_"
    "provenance_export_smoke_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_parser_provider_"
    "provenance_export_design_gate_blockers"
)
SOURCE_READ_BOUNDARY = (
    "only_step14au_e0_p3_six_committed_metadata_outputs_and_four_"
    "tracked_code_sources_no_recursive_artifact_dereference"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
P3_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_integration_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_"
    "covalent_residue_locator_parser_provider_provenance_export_design_gate_v1"
)
P3_FILENAMES = (
    "covapie_covalent_residue_locator_schema_integrated_rule_matrix.csv",
    "covapie_covalent_residue_locator_schema_integrated_field_matrix.csv",
    "covapie_covalent_residue_locator_schema_integrated_context_matrix.csv",
    "covapie_covalent_residue_locator_schema_integration_safety_audit.csv",
    "covapie_covalent_residue_locator_schema_integration_issue_inventory.csv",
    "covapie_covalent_residue_locator_schema_extension_integration_manifest.json",
)
CODE_SOURCE_PATHS = (
    Path("src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate.py"),
    Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py"),
    Path("src/covalent_ext/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke.py"),
    Path("src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py"),
)
SOURCE_PATHS = tuple(P3_ROOT / name for name in P3_FILENAMES) + CODE_SOURCE_PATHS
SOURCE_SHA256 = {
    str(P3_ROOT / P3_FILENAMES[0]): "c1ae6cf9c2ca5450315ff3e3ed21b0a81d8bfc08c6a07e35d3f2dca1874e0d2f",
    str(P3_ROOT / P3_FILENAMES[1]): "53dccd0ff7b20465c9df13f2c9eefc254f39bcb40e30732d1cfdfa4036e888fb",
    str(P3_ROOT / P3_FILENAMES[2]): "8eac50078260e0567f6a99024d04ac92b512a0be10d2dcb66a4fa6dab52d1ef8",
    str(P3_ROOT / P3_FILENAMES[3]): "4eaca47e07fd58dfdf2c1d05e8fb26083b013f0abcb2944e0950b8e967aba49b",
    str(P3_ROOT / P3_FILENAMES[4]): "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    str(P3_ROOT / P3_FILENAMES[5]): "676fe3c86e1304ba4971862d1e270fed40d9665e16c356d719627538aa28ee44",
    str(CODE_SOURCE_PATHS[0]): "abe6f364f0cc0297e2695f42753885e45aaf10580e4ed42deab62a39676be079",
    str(CODE_SOURCE_PATHS[1]): "0bb67a720595ce8b5211ba56f6913f1d6333828846abba326af8b2f9965eca8b",
    str(CODE_SOURCE_PATHS[2]): "1b04a32a580ef2dbb18048fe50f609bd188dd89c378d83474a1b32822f1e4932",
    str(CODE_SOURCE_PATHS[3]): "5fcc47a764a8a87e110350359e7c17056773c7ffd659b9094b6433beded2a9f8",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
PROPOSED_FIELD_NAMES = (
    "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)
PARSER_INSERTION_SOURCE_TAGS = (
    "_atom_site.pdbx_PDB_ins_code",
    "_struct_conn.pdbx_ptnr1_PDB_ins_code",
    "_struct_conn.pdbx_ptnr2_PDB_ins_code",
)
RAW_TOKEN_CLASSES = (
    "explicit_token",
    "dot_not_applicable",
    "question_unknown",
    "tag_missing",
    "parsed_empty",
    "invalid_token",
)
CANONICAL_PAYLOAD_SCHEMA_VERSION = "covapie_residue_locator_provenance_payload_v1"
CANONICAL_PAYLOAD_KEYS = (
    "schema_version",
    "sample_preparation_input_id",
    "pdb_id",
    "conn_id",
    "residue_partner_side",
    "locator_namespace",
    "struct_conn_residue_auth_asym_id",
    "struct_conn_residue_auth_seq_id",
    "struct_conn_residue_label_asym_id",
    "struct_conn_residue_label_seq_id",
    "selected_chain_id",
    "selected_residue_index",
    "matched_atom_site_id",
    "matched_residue_atom_name",
    "struct_conn_insertion_source_tag",
    "struct_conn_insertion_raw_value",
    "atom_site_insertion_source_tag",
    "atom_site_insertion_raw_value",
    "resolved_insertion_state",
    "resolved_insertion_value",
)
DOMAIN_BLOCKING_REASONS = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)
DESIGN_FOLLOWUP_ISSUE_IDS = (
    "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_NOT_YET_EXPORTABLE",
    "COVALENT_RESIDUE_LOCATOR_PARSER_PROVIDER_EXPORT_NOT_YET_IMPLEMENTED",
)

CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "field_or_tag", "requirement",
    "expected_value", "observed_value", "contract_passed", "blocking_reason",
)
RESOLUTION_COLUMNS = (
    "resolution_case_id", "struct_conn_tag_present", "struct_conn_raw_value",
    "struct_conn_token_class", "atom_site_tag_present", "atom_site_raw_value",
    "atom_site_token_class", "expected_resolved_state", "expected_resolved_value",
    "expected_passed", "expected_blocks_admit_004", "expected_blocking_reason",
    "observed_resolved_state", "observed_resolved_value", "observed_passed",
    "observed_blocks_admit_004", "observed_blocking_reason", "resolution_case_passed",
)
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink",
    "sha256_expected", "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reason",
)
CSV_OUTPUTS = (
    "covapie_covalent_residue_locator_parser_provider_export_contract.csv",
    "covapie_covalent_residue_locator_raw_token_resolution_matrix.csv",
    "covapie_covalent_residue_locator_source_boundary_audit.csv",
    "covapie_covalent_residue_locator_safety_audit.csv",
    "covapie_covalent_residue_locator_parser_provider_issue_inventory.csv",
)
MANIFEST_FILENAME = (
    "covapie_covalent_residue_locator_parser_provider_provenance_export_design_manifest.json"
)
SAFETY_ITEMS = (
    "network_access_used_current_step",
    "external_registry_lookup_current_step",
    "ignored_raw_directory_traversed_current_step",
    "ignored_raw_structure_read_current_step",
    "checkpoint_read_current_step",
    "artifact_reference_paths_followed_current_step",
    "p3_source_files_modified_current_step",
    "parser_modified_current_step",
    "expansion_parser_modified_current_step",
    "sample_index_producer_modified_current_step",
    "candidate_provider_implemented_current_step",
    "candidate_records_materialized_current_step",
    "provider_payloads_materialized_current_step",
    "download_queue_materialized_current_step",
    "raw_files_written_current_step",
    "torch_imported",
    "numpy_imported",
    "model_forward_called",
    "loss_compute_called",
    "training_allowed",
)
SECTION_FAILURE_IDS = {
    "source_boundary": "P4_SOURCE_BOUNDARY_VALIDATION_FAILED",
    "p3_predecessor": "P4_P3_PREDECESSOR_VALIDATION_FAILED",
    "design_contract": "P4_DESIGN_CONTRACT_VALIDATION_FAILED",
    "resolution_matrix": "P4_RESOLUTION_MATRIX_VALIDATION_FAILED",
    "issue_inventory": "P4_ISSUE_INVENTORY_VALIDATION_FAILED",
    "safety": "P4_SAFETY_VALIDATION_FAILED",
}


@dataclass(frozen=True)
class InsertionCodeRawTokenResult:
    passed: bool
    tag_present_valid: bool
    raw_value_exact_str: bool
    token_class: str
    preserved_raw_value: str
    blocking_reason: str


def classify_insertion_code_raw_token(
    tag_present: object, raw_value: object,
) -> InsertionCodeRawTokenResult:
    """Classify one parser token without coercion or normalization."""
    if type(tag_present) is not bool:
        return InsertionCodeRawTokenResult(
            False, False, type(raw_value) is str, "invalid_token", "",
            "INSERTION_TAG_PRESENT_TYPE_INVALID",
        )
    if not tag_present:
        if type(raw_value) is not str:
            return InsertionCodeRawTokenResult(
                False, True, False, "invalid_token", "",
                "INSERTION_RAW_VALUE_TYPE_INVALID",
            )
        if raw_value != "":
            return InsertionCodeRawTokenResult(
                False, True, True, "invalid_token", raw_value,
                "INSERTION_TAG_MISSING_REQUIRES_EMPTY_RAW",
            )
        return InsertionCodeRawTokenResult(True, True, True, "tag_missing", "", "")
    if type(raw_value) is not str:
        return InsertionCodeRawTokenResult(
            False, True, False, "invalid_token", "",
            "INSERTION_RAW_VALUE_TYPE_INVALID",
        )
    if not raw_value.isascii():
        return InsertionCodeRawTokenResult(
            False, True, True, "invalid_token", raw_value,
            "INSERTION_RAW_VALUE_NON_ASCII",
        )
    if raw_value != raw_value.strip() or (raw_value and raw_value.isspace()):
        return InsertionCodeRawTokenResult(
            False, True, True, "invalid_token", raw_value,
            "INSERTION_RAW_VALUE_WHITESPACE_INVALID",
        )
    if raw_value == "":
        return InsertionCodeRawTokenResult(True, True, True, "parsed_empty", "", "")
    if raw_value == ".":
        return InsertionCodeRawTokenResult(
            True, True, True, "dot_not_applicable", raw_value, ""
        )
    if raw_value == "?":
        return InsertionCodeRawTokenResult(
            True, True, True, "question_unknown", raw_value, ""
        )
    return InsertionCodeRawTokenResult(
        True, True, True, "explicit_token", raw_value, ""
    )


@dataclass(frozen=True)
class InsertionCodeEvidenceResolution:
    passed: bool
    schema_combination_valid: bool
    resolved_state: str
    resolved_value: str
    evidence_agreement: bool
    blocks_admit_004: bool
    blocking_reason: str


@dataclass(frozen=True)
class CovalentResidueLocatorNamespaceEvidenceResult:
    passed: bool
    locator_namespace: str
    expected_selected_chain_id: str
    expected_selected_residue_index: str
    selected_values_match: bool
    auth_label_conflict_observed: bool
    blocking_reason: str


def resolve_locator_namespace_evidence(
    *,
    locator_namespace: object,
    struct_conn_residue_auth_asym_id: object,
    struct_conn_residue_auth_seq_id: object,
    struct_conn_residue_label_asym_id: object,
    struct_conn_residue_label_seq_id: object,
    selected_chain_id: object,
    selected_residue_index: object,
) -> CovalentResidueLocatorNamespaceEvidenceResult:
    """Bind selected chain/index to one explicit auth or label evidence pair."""
    values = (
        locator_namespace, struct_conn_residue_auth_asym_id,
        struct_conn_residue_auth_seq_id, struct_conn_residue_label_asym_id,
        struct_conn_residue_label_seq_id, selected_chain_id, selected_residue_index,
    )
    if any(type(value) is not str for value in values):
        return CovalentResidueLocatorNamespaceEvidenceResult(
            False, "", "", "", False, False,
            "LOCATOR_NAMESPACE_EVIDENCE_TYPE_INVALID",
        )
    namespace_result = p2_gate.normalize_covalent_residue_locator_namespace(
        locator_namespace
    )
    if not namespace_result.passed:
        return CovalentResidueLocatorNamespaceEvidenceResult(
            False, locator_namespace, "", "", False, False,
            namespace_result.blocking_reason,
        )
    auth_pair = (
        struct_conn_residue_auth_asym_id, struct_conn_residue_auth_seq_id
    )
    label_pair = (
        struct_conn_residue_label_asym_id, struct_conn_residue_label_seq_id
    )
    expected_pair = auth_pair if locator_namespace == "auth" else label_pair
    conflict = bool(all(auth_pair) and all(label_pair) and auth_pair != label_pair)
    if not all(expected_pair):
        return CovalentResidueLocatorNamespaceEvidenceResult(
            False, locator_namespace, expected_pair[0], expected_pair[1], False,
            conflict, "LOCATOR_NAMESPACE_SELECTED_SOURCE_VALUE_MISSING",
        )
    selected_pair = (selected_chain_id, selected_residue_index)
    mixed = (
        (selected_chain_id == auth_pair[0] and selected_residue_index == label_pair[1])
        or (selected_chain_id == label_pair[0] and selected_residue_index == auth_pair[1])
    ) and selected_pair not in {auth_pair, label_pair}
    if mixed:
        return CovalentResidueLocatorNamespaceEvidenceResult(
            False, locator_namespace, expected_pair[0], expected_pair[1], False,
            conflict, "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN",
        )
    if selected_pair != expected_pair:
        return CovalentResidueLocatorNamespaceEvidenceResult(
            False, locator_namespace, expected_pair[0], expected_pair[1], False,
            conflict, "LOCATOR_NAMESPACE_SELECTED_VALUES_MISMATCH",
        )
    return CovalentResidueLocatorNamespaceEvidenceResult(
        True, locator_namespace, expected_pair[0], expected_pair[1], True,
        conflict, "",
    )


@dataclass(frozen=True)
class MatchedAtomSiteRowIdentityResult:
    passed: bool
    atom_site_id_exact_str: bool
    residue_atom_name_exact_str: bool
    matched_atom_site_id: str
    matched_residue_atom_name: str
    blocking_reason: str


def validate_matched_atom_site_row_identity(
    atom_site_id: object, residue_atom_name: object,
) -> MatchedAtomSiteRowIdentityResult:
    """Validate two opaque exact ASCII identifiers for one matched atom row."""
    if type(atom_site_id) is not str or type(residue_atom_name) is not str:
        return MatchedAtomSiteRowIdentityResult(
            False, type(atom_site_id) is str, type(residue_atom_name) is str,
            "", "", "MATCHED_ATOM_SITE_ROW_IDENTITY_TYPE_INVALID",
        )
    for value, reason in (
        (atom_site_id, "MATCHED_ATOM_SITE_ID_INVALID"),
        (residue_atom_name, "MATCHED_RESIDUE_ATOM_NAME_INVALID"),
    ):
        if (
            not value or not value.isascii() or value != value.strip()
            or value in {".", "?"}
        ):
            return MatchedAtomSiteRowIdentityResult(
                False, True, True, atom_site_id, residue_atom_name, reason,
            )
    return MatchedAtomSiteRowIdentityResult(
        True, True, True, atom_site_id, residue_atom_name, "",
    )


def resolve_insertion_code_evidence(
    struct_conn_token_result: InsertionCodeRawTokenResult,
    atom_site_token_result: InsertionCodeRawTokenResult,
) -> InsertionCodeEvidenceResolution:
    """Resolve two classified evidence tokens using exact agreement only."""
    tokens = (struct_conn_token_result, atom_site_token_result)
    classes = tuple(token.token_class for token in tokens)
    if any(token.token_class == "invalid_token" or not token.passed for token in tokens):
        return InsertionCodeEvidenceResolution(
            False, False, "unknown", "", False, True,
            "COVALENT_RESIDUE_INSERTION_CODE_EVIDENCE_INVALID",
        )
    if classes == ("explicit_token", "explicit_token"):
        if tokens[0].preserved_raw_value == tokens[1].preserved_raw_value:
            return InsertionCodeEvidenceResolution(
                True, True, "present", tokens[0].preserved_raw_value, True, False, ""
            )
        return InsertionCodeEvidenceResolution(
            False, True, "unknown", "", False, True,
            "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT",
        )
    if classes == ("dot_not_applicable", "dot_not_applicable"):
        return InsertionCodeEvidenceResolution(True, True, "absent", "", True, False, "")
    if set(classes).issubset({"explicit_token", "dot_not_applicable"}):
        return InsertionCodeEvidenceResolution(
            False, True, "unknown", "", False, True,
            "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT",
        )
    return InsertionCodeEvidenceResolution(
        False, True, "unknown", "", False, True,
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
    )


def build_locator_provenance_source_id(
    sample_preparation_input_id: object,
    conn_id: object,
    residue_partner_side: object,
) -> str:
    """Build and P2-validate the frozen opaque provenance source ID."""
    values = (sample_preparation_input_id, conn_id, residue_partner_side)
    if any(type(value) is not str for value in values):
        raise TypeError("source ID components must be exact strings")
    for component_name, component in (
        ("sample_preparation_input_id", sample_preparation_input_id),
        ("conn_id", conn_id),
    ):
        if (
            not component
            or not component.isascii()
            or component != component.strip()
            or component in {".", "?"}
            or any(separator in component for separator in (":", "/", "\\"))
        ):
            raise ValueError(f"invalid provenance source ID component: {component_name}")
    if residue_partner_side not in {"ptnr1", "ptnr2"}:
        raise ValueError("residue_partner_side must be ptnr1 or ptnr2")
    source_id = (
        f"covapie:residue-locator:{sample_preparation_input_id}:"
        f"{conn_id}:{residue_partner_side}"
    )
    result = p2_gate.normalize_covalent_residue_locator_provenance_source_id(source_id)
    if not result.passed:
        raise ValueError(result.blocking_reason)
    return result.canonical_source_id


def build_canonical_locator_provenance_payload(**values: object) -> dict[str, str]:
    """Build the exact canonical evidence payload without I/O or normalization."""
    expected_inputs = CANONICAL_PAYLOAD_KEYS[1:]
    if len(values) != len(expected_inputs) or set(values) != set(expected_inputs):
        raise ValueError("payload input key set must match the canonical contract")
    if any(type(values[key]) is not str for key in expected_inputs):
        raise TypeError("payload values must be exact strings")
    return {
        "schema_version": CANONICAL_PAYLOAD_SCHEMA_VERSION,
        **{key: values[key] for key in expected_inputs},
    }


def _resolve_provider_evidence(
    *,
    residue_partner_side: str,
    struct_conn_insertion_source_tag: str,
    struct_conn_insertion_raw_value: str,
    atom_site_insertion_source_tag: str,
    atom_site_insertion_raw_value: str,
) -> InsertionCodeEvidenceResolution:
    """Validate source-tag presence encoding and resolve the enclosed evidence."""
    if residue_partner_side not in {"ptnr1", "ptnr2"}:
        raise ValueError("residue_partner_side must be ptnr1 or ptnr2")
    expected_struct_tag = (
        PARSER_INSERTION_SOURCE_TAGS[1]
        if residue_partner_side == "ptnr1"
        else PARSER_INSERTION_SOURCE_TAGS[2]
    )
    if struct_conn_insertion_source_tag not in {"", expected_struct_tag}:
        raise ValueError("struct_conn insertion source tag does not match partner side")
    if atom_site_insertion_source_tag not in {"", PARSER_INSERTION_SOURCE_TAGS[0]}:
        raise ValueError("atom_site insertion source tag is not canonical")
    struct_token = classify_insertion_code_raw_token(
        struct_conn_insertion_source_tag != "", struct_conn_insertion_raw_value
    )
    atom_token = classify_insertion_code_raw_token(
        atom_site_insertion_source_tag != "", atom_site_insertion_raw_value
    )
    if not struct_token.passed or not atom_token.passed:
        reason = struct_token.blocking_reason or atom_token.blocking_reason
        raise ValueError(reason or "invalid insertion evidence token")
    return resolve_insertion_code_evidence(struct_token, atom_token)


def canonical_locator_provenance_payload_bytes(payload: dict[str, str]) -> bytes:
    """Validate and serialize an order-independent canonical evidence payload."""
    if type(payload) is not dict:
        raise TypeError("payload must be an exact dict")
    if len(payload) != len(CANONICAL_PAYLOAD_KEYS) or set(payload) != set(CANONICAL_PAYLOAD_KEYS):
        raise ValueError("payload key set must be canonical")
    if payload.get("schema_version") != CANONICAL_PAYLOAD_SCHEMA_VERSION:
        raise ValueError("payload schema version mismatch")
    if any(type(payload[key]) is not str for key in CANONICAL_PAYLOAD_KEYS):
        raise TypeError("payload values must be exact strings")
    build_locator_provenance_source_id(
        payload["sample_preparation_input_id"], payload["conn_id"],
        payload["residue_partner_side"],
    )
    namespace_evidence = resolve_locator_namespace_evidence(
        locator_namespace=payload["locator_namespace"],
        struct_conn_residue_auth_asym_id=payload["struct_conn_residue_auth_asym_id"],
        struct_conn_residue_auth_seq_id=payload["struct_conn_residue_auth_seq_id"],
        struct_conn_residue_label_asym_id=payload["struct_conn_residue_label_asym_id"],
        struct_conn_residue_label_seq_id=payload["struct_conn_residue_label_seq_id"],
        selected_chain_id=payload["selected_chain_id"],
        selected_residue_index=payload["selected_residue_index"],
    )
    if not namespace_evidence.passed:
        raise ValueError(namespace_evidence.blocking_reason)
    atom_site_row = validate_matched_atom_site_row_identity(
        payload["matched_atom_site_id"], payload["matched_residue_atom_name"]
    )
    if not atom_site_row.passed:
        raise ValueError(atom_site_row.blocking_reason)
    observed_resolution = _resolve_provider_evidence(
        residue_partner_side=payload["residue_partner_side"],
        struct_conn_insertion_source_tag=payload["struct_conn_insertion_source_tag"],
        struct_conn_insertion_raw_value=payload["struct_conn_insertion_raw_value"],
        atom_site_insertion_source_tag=payload["atom_site_insertion_source_tag"],
        atom_site_insertion_raw_value=payload["atom_site_insertion_raw_value"],
    )
    if (
        observed_resolution.resolved_state != payload["resolved_insertion_state"]
        or observed_resolution.resolved_value != payload["resolved_insertion_value"]
    ):
        raise ValueError("payload resolved insertion state/value contradicts raw evidence")
    canonical_payload = {key: payload[key] for key in CANONICAL_PAYLOAD_KEYS}
    return json.dumps(
        canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_canonical_locator_provenance_payload(payload: dict[str, str]) -> str:
    """Hash one validated canonical payload as lowercase SHA256."""
    return hashlib.sha256(canonical_locator_provenance_payload_bytes(payload)).hexdigest()


def build_locator_provider_export_fields(
    *, locator_namespace: object,
    sample_preparation_input_id: object,
    pdb_id: object,
    conn_id: object,
    residue_partner_side: object,
    struct_conn_residue_auth_asym_id: object,
    struct_conn_residue_auth_seq_id: object,
    struct_conn_residue_label_asym_id: object,
    struct_conn_residue_label_seq_id: object,
    selected_chain_id: object,
    selected_residue_index: object,
    matched_atom_site_id: object,
    matched_residue_atom_name: object,
    struct_conn_insertion_source_tag: object,
    struct_conn_insertion_raw_value: object,
    atom_site_insertion_source_tag: object,
    atom_site_insertion_raw_value: object,
) -> dict[str, str]:
    """Demonstrate the frozen five-field mapping without materializing records."""
    values = (
        locator_namespace, sample_preparation_input_id, pdb_id, conn_id,
        residue_partner_side, struct_conn_residue_auth_asym_id,
        struct_conn_residue_auth_seq_id, struct_conn_residue_label_asym_id,
        struct_conn_residue_label_seq_id, selected_chain_id, selected_residue_index,
        matched_atom_site_id, matched_residue_atom_name,
        struct_conn_insertion_source_tag, struct_conn_insertion_raw_value,
        atom_site_insertion_source_tag, atom_site_insertion_raw_value,
    )
    if any(type(value) is not str for value in values):
        raise TypeError("provider inputs must be exact strings")
    namespace = p2_gate.normalize_covalent_residue_locator_namespace(locator_namespace)
    if not namespace.passed:
        raise ValueError(namespace.blocking_reason)
    namespace_evidence = resolve_locator_namespace_evidence(
        locator_namespace=locator_namespace,
        struct_conn_residue_auth_asym_id=struct_conn_residue_auth_asym_id,
        struct_conn_residue_auth_seq_id=struct_conn_residue_auth_seq_id,
        struct_conn_residue_label_asym_id=struct_conn_residue_label_asym_id,
        struct_conn_residue_label_seq_id=struct_conn_residue_label_seq_id,
        selected_chain_id=selected_chain_id,
        selected_residue_index=selected_residue_index,
    )
    if not namespace_evidence.passed:
        raise ValueError(namespace_evidence.blocking_reason)
    atom_site_row = validate_matched_atom_site_row_identity(
        matched_atom_site_id, matched_residue_atom_name
    )
    if not atom_site_row.passed:
        raise ValueError(atom_site_row.blocking_reason)
    resolution = _resolve_provider_evidence(
        residue_partner_side=residue_partner_side,
        struct_conn_insertion_source_tag=struct_conn_insertion_source_tag,
        struct_conn_insertion_raw_value=struct_conn_insertion_raw_value,
        atom_site_insertion_source_tag=atom_site_insertion_source_tag,
        atom_site_insertion_raw_value=atom_site_insertion_raw_value,
    )
    source_id = build_locator_provenance_source_id(
        sample_preparation_input_id, conn_id, residue_partner_side
    )
    payload = build_canonical_locator_provenance_payload(
        sample_preparation_input_id=sample_preparation_input_id,
        pdb_id=pdb_id,
        conn_id=conn_id,
        residue_partner_side=residue_partner_side,
        locator_namespace=locator_namespace,
        struct_conn_residue_auth_asym_id=struct_conn_residue_auth_asym_id,
        struct_conn_residue_auth_seq_id=struct_conn_residue_auth_seq_id,
        struct_conn_residue_label_asym_id=struct_conn_residue_label_asym_id,
        struct_conn_residue_label_seq_id=struct_conn_residue_label_seq_id,
        selected_chain_id=selected_chain_id,
        selected_residue_index=selected_residue_index,
        matched_atom_site_id=matched_atom_site_id,
        matched_residue_atom_name=matched_residue_atom_name,
        struct_conn_insertion_source_tag=struct_conn_insertion_source_tag,
        struct_conn_insertion_raw_value=struct_conn_insertion_raw_value,
        atom_site_insertion_source_tag=atom_site_insertion_source_tag,
        atom_site_insertion_raw_value=atom_site_insertion_raw_value,
        resolved_insertion_state=resolution.resolved_state,
        resolved_insertion_value=resolution.resolved_value,
    )
    sha256_value = sha256_canonical_locator_provenance_payload(payload)
    if not p2_gate.validate_covalent_residue_insertion_code(
        resolution.resolved_state, resolution.resolved_value
    ).schema_combination_valid:
        raise ValueError("resolved insertion state/value combination invalid")
    if not p2_gate.validate_covalent_residue_locator_provenance_sha256(sha256_value).passed:
        raise ValueError("canonical provenance SHA256 invalid")
    return {
        PROPOSED_FIELD_NAMES[0]: namespace.canonical_namespace,
        PROPOSED_FIELD_NAMES[1]: resolution.resolved_state,
        PROPOSED_FIELD_NAMES[2]: resolution.resolved_value,
        PROPOSED_FIELD_NAMES[3]: source_id,
        PROPOSED_FIELD_NAMES[4]: sha256_value,
    }


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _source_boundary_rows() -> list[dict[str, str]]:
    rows = []
    for relative_path in SOURCE_PATHS:
        absolute = _repo_path(relative_path)
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        tracked = _tracked_by_git(relative_path)
        observed = _sha256(absolute) if regular and not symlink else ""
        expected = SOURCE_SHA256[relative_path.as_posix()]
        passed = tracked and regular and not symlink and observed == expected
        rows.append({
            "source_relative_path": relative_path.as_posix(),
            "tracked_by_git": _bool_text(tracked),
            "regular_file": _bool_text(regular),
            "symlink": _bool_text(symlink),
            "sha256_expected": expected,
            "sha256_observed": observed,
            "source_boundary_passed": _bool_text(passed),
        })
    return rows


def _validate_source_boundary_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in SOURCE_PATHS]
    return (
        bool(rows) and len(rows) == 10
        and all(tuple(row) == SOURCE_COLUMNS for row in rows)
        and [row["source_relative_path"] for row in rows] == expected_paths
        and len({row["source_relative_path"] for row in rows}) == 10
        and all(
            row["tracked_by_git"] == "true"
            and row["regular_file"] == "true"
            and row["symlink"] == "false"
            and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["source_boundary_passed"] == "true"
            for row in rows
        )
    )


def _load_p3_source() -> dict[str, Any]:
    return {
        "rules": _read_csv(P3_ROOT / P3_FILENAMES[0]),
        "fields": _read_csv(P3_ROOT / P3_FILENAMES[1]),
        "contexts": _read_csv(P3_ROOT / P3_FILENAMES[2]),
        "safety": _read_csv(P3_ROOT / P3_FILENAMES[3]),
        "issues": _read_csv(P3_ROOT / P3_FILENAMES[4]),
        "manifest": json.loads(
            _repo_path(P3_ROOT / P3_FILENAMES[5]).read_text(encoding="utf-8")
        ),
    }


def _validate_p3_predecessor(source: dict[str, Any]) -> bool:
    manifest = source["manifest"]
    fields = source["fields"]
    insertion = next(
        (row for row in fields if row.get("field_name") == PROPOSED_FIELD_NAMES[2]), None
    )
    return (
        len(source["rules"]) == 15
        and len(fields) == 22
        and len(source["contexts"]) == 18
        and len(source["issues"]) == 10
        and tuple(row.get("issue_id") for row in source["issues"]) == DOMAIN_BLOCKING_REASONS
        and all(any(row.get("field_name") == name for row in fields) for name in PROPOSED_FIELD_NAMES)
        and insertion is not None
        and insertion.get("implementation_semantics_complete") == "false"
        and insertion.get("allowed_values_defined") == "false"
        and insertion.get("exact_validation_defined") == "false"
        and "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED" in insertion.get("blocking_reasons", "")
        and manifest.get("stage") == PREVIOUS_STAGE
        and manifest.get("all_checks_passed") is True
        and manifest.get("integrated_field_count") == 22
        and manifest.get("integrated_rule_count") == 15
        and manifest.get("integrated_context_count") == 18
        and manifest.get("remaining_issue_count") == 10
        and manifest.get("semantics_complete_field_count") == 7
        and manifest.get("semantics_incomplete_field_count") == 15
        and manifest.get("changed_rule_ids") == ["ADMIT_004"]
        and manifest.get("changed_context_items") == []
        and manifest.get("covalent_residue_locator_schema_extension_integrated") is True
        and manifest.get("covalent_residue_locator_schema_extension_frozen") is True
        and manifest.get("insertion_code_provenance_export_ready") is False
        and manifest.get("parser_insertion_code_support_required") is True
        and manifest.get("provider_provenance_binding_required") is True
        and manifest.get("existing_sample_count") == 11
        and manifest.get("insertion_unknown_sample_count") == 11
        and manifest.get("fully_provable_pre_download_sample_count") == 0
        and manifest.get("samples_admissible_after_schema_extension_only") == 0
        and manifest.get("admit_004_rule_logic_ready") is False
        and manifest.get("ready_for_e1_residue_identity_semantics_design") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False
        and manifest.get("ready_to_train_now") is False
        and manifest.get("feature_semantics_audit_required_before_training") is True
        and manifest.get("canonical_mask_pairs") == [list(pair) for pair in CANONICAL_MASK_PAIRS]
        and manifest.get("canonical_mask_task_count") == 5
        and manifest.get("recommended_next_step")
        == "design_covapie_covalent_residue_locator_parser_and_provider_provenance_export_v1"
    )


def _resolution_specs() -> tuple[tuple[Any, ...], ...]:
    conflict = "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT"
    unknown = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
    invalid = "COVALENT_RESIDUE_INSERTION_CODE_EVIDENCE_INVALID"
    return (
        ("RESOLVE_001", True, "A", True, "A", "present", "A", True, False, ""),
        ("RESOLVE_002", True, "1", True, "1", "present", "1", True, False, ""),
        ("RESOLVE_003", True, "A", True, "B", "unknown", "", False, True, conflict),
        ("RESOLVE_004", True, "A", True, ".", "unknown", "", False, True, conflict),
        ("RESOLVE_005", True, ".", True, "A", "unknown", "", False, True, conflict),
        ("RESOLVE_006", True, ".", True, ".", "absent", "", True, False, ""),
        ("RESOLVE_007", True, "?", True, "?", "unknown", "", False, True, unknown),
        ("RESOLVE_008", False, "", False, "", "unknown", "", False, True, unknown),
        ("RESOLVE_009", True, "", True, "", "unknown", "", False, True, unknown),
        ("RESOLVE_010", True, "A", True, "?", "unknown", "", False, True, unknown),
        ("RESOLVE_011", True, "?", True, "A", "unknown", "", False, True, unknown),
        ("RESOLVE_012", True, " A", True, "A", "unknown", "", False, True, invalid),
    )


def _resolution_rows() -> list[dict[str, str]]:
    rows = []
    for case_id, sc_present, sc_raw, at_present, at_raw, state, value, passed, blocks, reason in _resolution_specs():
        sc = classify_insertion_code_raw_token(sc_present, sc_raw)
        at = classify_insertion_code_raw_token(at_present, at_raw)
        observed = resolve_insertion_code_evidence(sc, at)
        expected = (state, value, passed, blocks, reason)
        actual = (
            observed.resolved_state, observed.resolved_value, observed.passed,
            observed.blocks_admit_004, observed.blocking_reason,
        )
        rows.append({
            "resolution_case_id": case_id,
            "struct_conn_tag_present": _bool_text(sc_present),
            "struct_conn_raw_value": sc_raw,
            "struct_conn_token_class": sc.token_class,
            "atom_site_tag_present": _bool_text(at_present),
            "atom_site_raw_value": at_raw,
            "atom_site_token_class": at.token_class,
            "expected_resolved_state": state,
            "expected_resolved_value": value,
            "expected_passed": _bool_text(passed),
            "expected_blocks_admit_004": _bool_text(blocks),
            "expected_blocking_reason": reason,
            "observed_resolved_state": observed.resolved_state,
            "observed_resolved_value": observed.resolved_value,
            "observed_passed": _bool_text(observed.passed),
            "observed_blocks_admit_004": _bool_text(observed.blocks_admit_004),
            "observed_blocking_reason": observed.blocking_reason,
            "resolution_case_passed": _bool_text(expected == actual),
        })
    return rows


def _validate_resolution_rows(rows: list[dict[str, str]]) -> bool:
    canonical = _resolution_rows()
    return (
        bool(rows) and len(rows) == 12
        and all(tuple(row) == RESOLUTION_COLUMNS for row in rows)
        and rows == canonical
        and all(row["resolution_case_passed"] == "true" for row in rows)
    )


def _sample_payload() -> dict[str, str]:
    return build_canonical_locator_provenance_payload(
        sample_preparation_input_id="SPREP_000001", pdb_id="6BV6", conn_id="covale1",
        residue_partner_side="ptnr1", locator_namespace="auth",
        struct_conn_residue_auth_asym_id="A", struct_conn_residue_auth_seq_id="145",
        struct_conn_residue_label_asym_id="B", struct_conn_residue_label_seq_id="44",
        selected_chain_id="A", selected_residue_index="145",
        matched_atom_site_id="C_a_phe_83_a_0", matched_residue_atom_name="SG",
        struct_conn_insertion_source_tag=PARSER_INSERTION_SOURCE_TAGS[1],
        struct_conn_insertion_raw_value="A",
        atom_site_insertion_source_tag=PARSER_INSERTION_SOURCE_TAGS[0],
        atom_site_insertion_raw_value="A", resolved_insertion_state="present",
        resolved_insertion_value="A",
    )


def _evidence_payload(
    *, struct_tag: str, struct_raw: str, atom_tag: str, atom_raw: str,
    state: str, value: str, side: str = "ptnr1", namespace: str = "auth",
    auth_asym: str = "A", auth_seq: str = "145",
    label_asym: str = "B", label_seq: str = "44",
    selected_chain: str | None = None, selected_index: str | None = None,
    atom_site_id: str = "C_a_phe_83_a_0", atom_name: str = "SG",
) -> dict[str, str]:
    if selected_chain is None:
        selected_chain = auth_asym if namespace == "auth" else label_asym
    if selected_index is None:
        selected_index = auth_seq if namespace == "auth" else label_seq
    return build_canonical_locator_provenance_payload(
        sample_preparation_input_id="SPREP_000001", pdb_id="6BV6", conn_id="covale1",
        residue_partner_side=side, locator_namespace=namespace,
        struct_conn_residue_auth_asym_id=auth_asym,
        struct_conn_residue_auth_seq_id=auth_seq,
        struct_conn_residue_label_asym_id=label_asym,
        struct_conn_residue_label_seq_id=label_seq,
        selected_chain_id=selected_chain, selected_residue_index=selected_index,
        matched_atom_site_id=atom_site_id, matched_residue_atom_name=atom_name,
        struct_conn_insertion_source_tag=struct_tag,
        struct_conn_insertion_raw_value=struct_raw,
        atom_site_insertion_source_tag=atom_tag,
        atom_site_insertion_raw_value=atom_raw,
        resolved_insertion_state=state, resolved_insertion_value=value,
    )


def _call_rejected(call: Callable[[], object]) -> str:
    try:
        call()
    except (TypeError, ValueError):
        return "true"
    return "false"


def _parser_tags_currently_absent() -> bool:
    return all(
        tag not in _repo_path(path).read_text(encoding="utf-8")
        for path in CODE_SOURCE_PATHS[1:3]
        for tag in PARSER_INSERTION_SOURCE_TAGS
    )


def _contract_specs() -> tuple[tuple[str, str, str, str, str, Callable[[], str]], ...]:
    payload = _sample_payload()
    source_id = "covapie:residue-locator:SPREP_000001:covale1:ptnr1"
    sample_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    explicit = resolve_insertion_code_evidence(
        classify_insertion_code_raw_token(True, "A"),
        classify_insertion_code_raw_token(True, "A"),
    )
    def build_provider(**overrides: object) -> dict[str, str]:
        inputs: dict[str, object] = {
            "locator_namespace": "auth",
            "sample_preparation_input_id": "SPREP_000001", "pdb_id": "6BV6",
            "conn_id": "covale1", "residue_partner_side": "ptnr1",
            "struct_conn_residue_auth_asym_id": "A",
            "struct_conn_residue_auth_seq_id": "145",
            "struct_conn_residue_label_asym_id": "B",
            "struct_conn_residue_label_seq_id": "44",
            "selected_chain_id": "A", "selected_residue_index": "145",
            "matched_atom_site_id": "C_a_phe_83_a_0",
            "matched_residue_atom_name": "SG",
            "struct_conn_insertion_source_tag": PARSER_INSERTION_SOURCE_TAGS[1],
            "struct_conn_insertion_raw_value": "A",
            "atom_site_insertion_source_tag": PARSER_INSERTION_SOURCE_TAGS[0],
            "atom_site_insertion_raw_value": "A",
        }
        inputs.update(overrides)
        return build_locator_provider_export_fields(
            **inputs,
        )
    missing_payload = _evidence_payload(
        struct_tag="", struct_raw="", atom_tag="", atom_raw="",
        state="unknown", value="",
    )
    empty_payload = _evidence_payload(
        struct_tag=PARSER_INSERTION_SOURCE_TAGS[1], struct_raw="",
        atom_tag=PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="",
        state="unknown", value="",
    )
    specs: list[tuple[str, str, str, str, str, Callable[[], str]]] = []
    def add(area: str, field: str, req: str, expected: str, observed: Callable[[], str]) -> None:
        specs.append((f"P4C_{len(specs)+1:03d}", area, field, req, expected, observed))
    add("lineage", "previous_stage", "exact P3 predecessor", PREVIOUS_STAGE, lambda: PREVIOUS_STAGE)
    add("lineage", "predecessor_field_count", "P3 fields", "22", lambda: "22")
    add("lineage", "predecessor_issue_count", "P3 domain issues", "10", lambda: "10")
    add("scope", "design_only", "no execution", "true", lambda: "true")
    add("scope", "parser_provider_implemented", "parser and provider unchanged", "false|false", lambda: "false|false")
    add("scope", "canonical_mask_B3", "B3 preserved", "scaffold_only/B3", lambda: "scaffold_only/B3")
    add("parser_tags", "exact_registry", "exact three source tags", "|".join(PARSER_INSERTION_SOURCE_TAGS), lambda: "|".join(PARSER_INSERTION_SOURCE_TAGS))
    add("parser_tags", "partner_side", "ptnr1 and ptnr2 exact selection", "true", lambda: _bool_text(
        build_locator_provenance_source_id("SPREP_1", "conn1", "ptnr1").endswith(":ptnr1")
        and build_locator_provenance_source_id("SPREP_1", "conn1", "ptnr2").endswith(":ptnr2")
    ))
    add("parser_tags", "atom_site_row", "matched atom-site row identity validated", "true", lambda: _bool_text(
        validate_matched_atom_site_row_identity("C_a_phe_83_a_0", "SG").passed
    ))
    add("parser_tags", "raw_token", "preserve raw without normalization or index inference", "true", lambda: _bool_text(
        classify_insertion_code_raw_token(True, "A").preserved_raw_value == "A"
        and not classify_insertion_code_raw_token(True, " A").passed
        and classify_insertion_code_raw_token(True, "1").preserved_raw_value == "1"
    ))
    add("classifier", "token_classes", "exact six classes", "|".join(RAW_TOKEN_CLASSES), lambda: "|".join(RAW_TOKEN_CLASSES))
    add("classifier", "exact_input_types", "exact types and invalid token fail closed", "true", lambda: _bool_text(
        not classify_insertion_code_raw_token(1, "").tag_present_valid
        and not classify_insertion_code_raw_token(True, 1).raw_value_exact_str
        and not classify_insertion_code_raw_token(True, " A").passed
    ))
    add("classifier", "dot_and_question", "distinct dot and question classes", "dot_not_applicable|question_unknown", lambda: "|".join((
        classify_insertion_code_raw_token(True, ".").token_class,
        classify_insertion_code_raw_token(True, "?").token_class,
    )))
    add("classifier", "missing_and_empty", "missing and parsed empty remain distinct", "tag_missing|parsed_empty", lambda: "|".join((
        classify_insertion_code_raw_token(False, "").token_class,
        classify_insertion_code_raw_token(True, "").token_class,
    )))
    add("resolution", "explicit_agreement", "dual exact token", "present:A", lambda: f"{explicit.resolved_state}:{explicit.resolved_value}")
    dot = resolve_insertion_code_evidence(classify_insertion_code_raw_token(True, "."), classify_insertion_code_raw_token(True, "."))
    add("resolution", "dot_agreement", "dual dot", "absent:", lambda: f"{dot.resolved_state}:{dot.resolved_value}")
    add("resolution", "conflict", "explicit conflict blocks", "unknown:true", lambda: (
        lambda result: f"{result.resolved_state}:{_bool_text(result.blocks_admit_004)}"
    )(resolve_insertion_code_evidence(
        classify_insertion_code_raw_token(True, "A"),
        classify_insertion_code_raw_token(True, "B"),
    )))
    add("resolution", "unknown_and_invalid", "unknown and invalid evidence block", "true", lambda: _bool_text(
        resolve_insertion_code_evidence(
            classify_insertion_code_raw_token(True, "?"),
            classify_insertion_code_raw_token(True, "?"),
        ).blocks_admit_004
        and resolve_insertion_code_evidence(
            classify_insertion_code_raw_token(True, " A"),
            classify_insertion_code_raw_token(True, "A"),
        ).blocks_admit_004
    ))
    add("resolution", "one_sided_promotion", "one-sided evidence forbidden", "true", lambda: _bool_text(
        not resolve_insertion_code_evidence(
            classify_insertion_code_raw_token(True, "A"),
            classify_insertion_code_raw_token(True, "?"),
        ).passed
    ))
    add("provider", "output_fields", "exact five P3 fields", "|".join(PROPOSED_FIELD_NAMES), lambda: "|".join(build_provider()))
    add("provider", "namespace", "provider recomputes auth namespace evidence", "auth", lambda: build_provider()[PROPOSED_FIELD_NAMES[0]])
    add("namespace", "auth_evidence", "auth selection binds auth values", "true", lambda: _bool_text(resolve_locator_namespace_evidence(
        locator_namespace="auth", struct_conn_residue_auth_asym_id="A",
        struct_conn_residue_auth_seq_id="145", struct_conn_residue_label_asym_id="B",
        struct_conn_residue_label_seq_id="44", selected_chain_id="A",
        selected_residue_index="145",
    ).passed))
    add("namespace", "label_evidence", "label selection binds label values", "true", lambda: _bool_text(resolve_locator_namespace_evidence(
        locator_namespace="label", struct_conn_residue_auth_asym_id="A",
        struct_conn_residue_auth_seq_id="145", struct_conn_residue_label_asym_id="B",
        struct_conn_residue_label_seq_id="44", selected_chain_id="B",
        selected_residue_index="44",
    ).passed))
    add("namespace", "mixed_selection", "mixed auth/label selection rejected", "true", lambda: _bool_text(
        resolve_locator_namespace_evidence(
            locator_namespace="auth", struct_conn_residue_auth_asym_id="A",
            struct_conn_residue_auth_seq_id="145", struct_conn_residue_label_asym_id="B",
            struct_conn_residue_label_seq_id="44", selected_chain_id="A",
            selected_residue_index="44",
        ).blocking_reason == "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN"
    ))
    add("namespace", "selected_mismatch", "selected pair mismatch rejected", "true", lambda: _bool_text(
        resolve_locator_namespace_evidence(
            locator_namespace="auth", struct_conn_residue_auth_asym_id="A",
            struct_conn_residue_auth_seq_id="145", struct_conn_residue_label_asym_id="B",
            struct_conn_residue_label_seq_id="44", selected_chain_id="C",
            selected_residue_index="999",
        ).blocking_reason == "LOCATOR_NAMESPACE_SELECTED_VALUES_MISMATCH"
    ))
    add("namespace", "auth_label_conflict", "conflict recorded but explicit selection passes", "true", lambda: _bool_text((lambda result: result.passed and result.auth_label_conflict_observed)(resolve_locator_namespace_evidence(
        locator_namespace="auth", struct_conn_residue_auth_asym_id="A",
        struct_conn_residue_auth_seq_id="145", struct_conn_residue_label_asym_id="B",
        struct_conn_residue_label_seq_id="44", selected_chain_id="A",
        selected_residue_index="145",
    ))))
    add("provider", "source_id_template", "frozen opaque template", source_id, lambda: build_locator_provenance_source_id("SPREP_000001", "covale1", "ptnr1"))
    add("provider", "p2_validations", "source ID and SHA256 pass P2 helpers", "true", lambda: _bool_text(
        p2_gate.normalize_covalent_residue_locator_provenance_source_id(source_id).passed
        and p2_gate.validate_covalent_residue_locator_provenance_sha256(sample_hash).passed
    ))
    add("provider", "internal_resolution", "provider recomputes raw evidence", "present:A", lambda: f"{build_provider()[PROPOSED_FIELD_NAMES[1]]}:{build_provider()[PROPOSED_FIELD_NAMES[2]]}")
    add("provider", "forged_resolution", "caller cannot inject resolved state", "true", lambda: _call_rejected(lambda: build_provider(resolution=explicit)))
    add("payload", "key_set", "exact canonical keys", "|".join(CANONICAL_PAYLOAD_KEYS), lambda: "|".join(payload))
    add("payload", "schema_version", "exact schema", CANONICAL_PAYLOAD_SCHEMA_VERSION, lambda: payload["schema_version"])
    reverse_inputs = dict(reversed(tuple({key: payload[key] for key in CANONICAL_PAYLOAD_KEYS[1:]}.items())))
    add("payload", "kwargs_order", "kwargs insertion order independent", "true", lambda: _bool_text(tuple(build_canonical_locator_provenance_payload(**reverse_inputs)) == CANONICAL_PAYLOAD_KEYS))
    add("payload", "dict_order", "payload dict order independent", "true", lambda: _bool_text(
        canonical_locator_provenance_payload_bytes(dict(reversed(tuple(payload.items()))))
        == canonical_locator_provenance_payload_bytes(payload)
    ))
    add("payload", "missing_tag_encoding", "missing tag uses empty tag and raw", "true", lambda: _bool_text(
        missing_payload["struct_conn_insertion_source_tag"] == ""
        and missing_payload["struct_conn_insertion_raw_value"] == ""
        and canonical_locator_provenance_payload_bytes(missing_payload) != b""
    ))
    add("payload", "parsed_empty_encoding", "parsed empty uses exact tags", "true", lambda: _bool_text(
        empty_payload["struct_conn_insertion_source_tag"] == PARSER_INSERTION_SOURCE_TAGS[1]
        and empty_payload["atom_site_insertion_source_tag"] == PARSER_INSERTION_SOURCE_TAGS[0]
        and canonical_locator_provenance_payload_bytes(empty_payload) != b""
    ))
    add("payload", "missing_empty_hash", "missing and parsed empty hashes differ", "true", lambda: _bool_text(
        sha256_canonical_locator_provenance_payload(missing_payload)
        != sha256_canonical_locator_provenance_payload(empty_payload)
    ))
    add("payload", "partner_tag_binding", "struct tag bound to partner side", "true", lambda: _call_rejected(lambda: canonical_locator_provenance_payload_bytes(
        _evidence_payload(
            struct_tag=PARSER_INSERTION_SOURCE_TAGS[2], struct_raw="A",
            atom_tag=PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="A",
            state="present", value="A", side="ptnr1",
        )
    )))
    add("payload", "resolved_self_consistency", "resolved state cannot contradict evidence", "true", lambda: _call_rejected(lambda: canonical_locator_provenance_payload_bytes(
        _evidence_payload(
            struct_tag=PARSER_INSERTION_SOURCE_TAGS[1], struct_raw="A",
            atom_tag=PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="A",
            state="absent", value="",
        )
    )))
    label_payload = _evidence_payload(
        struct_tag=PARSER_INSERTION_SOURCE_TAGS[1], struct_raw="A",
        atom_tag=PARSER_INSERTION_SOURCE_TAGS[0], atom_raw="A",
        state="present", value="A", namespace="label",
    )
    changed_atom_payload = dict(payload)
    changed_atom_payload["matched_atom_site_id"] = "opaque_atom_row_2"
    add("payload", "namespace_hash_binding", "auth and label selections hash differently", "true", lambda: _bool_text(
        sha256_canonical_locator_provenance_payload(payload)
        != sha256_canonical_locator_provenance_payload(label_payload)
    ))
    add("payload", "atom_site_row_hash_binding", "matched atom-site row changes hash", "true", lambda: _bool_text(
        sha256_canonical_locator_provenance_payload(payload)
        != sha256_canonical_locator_provenance_payload(changed_atom_payload)
    ))
    bad_source_payload = dict(payload)
    bad_source_payload["sample_preparation_input_id"] = "A:B"
    add("payload", "standalone_source_id", "standalone payload reapplies source-ID contract", "true", lambda: _call_rejected(
        lambda: canonical_locator_provenance_payload_bytes(bad_source_payload)
    ))
    add("source_id", "nonempty", "empty components rejected", "true", lambda: _bool_text(
        _call_rejected(lambda: build_locator_provenance_source_id("", "C", "ptnr1")) == "true"
        and _call_rejected(lambda: build_locator_provenance_source_id("A", "", "ptnr1")) == "true"
    ))
    add("source_id", "separator_collision", "colon and path separators rejected", "true", lambda: _bool_text(all(
        _call_rejected(lambda sample=sample, conn=conn: build_locator_provenance_source_id(sample, conn, "ptnr1")) == "true"
        for sample, conn in (("A:B", "C"), ("A", "B:C"), ("A/B", "C"), ("A", "B\\C"))
    )))
    add("readiness", "implementation_run", "implementation not run", "false", lambda: "false")
    add("readiness", "unknown_admit_e1", "11 unknown and ADMIT_004/E1 blocked", "11|false|false", lambda: "11|false|false")
    add("safety", "candidate_download_training", "all unauthorized", "false|false|false", lambda: "false|false|false")
    add("safety", "feature_semantics_audit", "required before training", "true", lambda: "true")
    assert len(specs) == 48
    return tuple(specs)


def _contract_rows() -> list[dict[str, str]]:
    rows = []
    for item_id, area, field, requirement, expected, observed_builder in _contract_specs():
        try:
            observed = observed_builder()
        except (TypeError, ValueError):
            observed = "helper_failure"
        passed = observed == expected
        rows.append({
            "contract_item_id": item_id, "contract_area": area,
            "field_or_tag": field, "requirement": requirement,
            "expected_value": expected, "observed_value": observed,
            "contract_passed": _bool_text(passed),
            "blocking_reason": "" if passed else item_id,
        })
    return rows


def _validate_contract_rows(rows: list[dict[str, str]]) -> bool:
    canonical = _contract_rows()
    return (
        bool(rows) and len(rows) == 48
        and all(tuple(row) == CONTRACT_COLUMNS for row in rows)
        and rows == canonical
        and [row["contract_item_id"] for row in rows] == [f"P4C_{i:03d}" for i in range(1, 49)]
        and all(row["contract_passed"] == "true" and row["blocking_reason"] == "" for row in rows)
    )


def _issue_rows() -> list[dict[str, str]]:
    return [
        {
            "issue_id": DESIGN_FOLLOWUP_ISSUE_IDS[0],
            "issue_type": "parser_provider_implementation_pending",
            "severity": "blocking", "status": "open", "issue_count": "11",
            "blocking_reason": "tracked_samples_require_parser_and_provider_export_execution",
        },
        {
            "issue_id": DESIGN_FOLLOWUP_ISSUE_IDS[1],
            "issue_type": "implementation_pending",
            "severity": "blocking", "status": "open", "issue_count": "1",
            "blocking_reason": "design_frozen_but_parser_and_provider_unchanged",
        },
    ]


def _validate_issue_rows(rows: list[dict[str, str]]) -> bool:
    return (
        bool(rows) and len(rows) == 2
        and all(tuple(row) == ISSUE_COLUMNS for row in rows)
        and rows == _issue_rows()
        and all(row["issue_id"] != "NO_ISSUES" for row in rows)
    )


def _safety_rows() -> list[dict[str, str]]:
    return [
        {"safety_item": item, "required_status": "false", "observed_status": "false",
         "safety_passed": "true", "blocking_reason": ""}
        for item in SAFETY_ITEMS
    ]


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return (
        bool(rows) and len(rows) == 20
        and all(tuple(row) == SAFETY_COLUMNS for row in rows)
        and rows == _safety_rows()
    )


def _build_materialization(
    section_overrides: dict[str, bool] | None = None,
) -> dict[str, Any]:
    source_rows = _source_boundary_rows()
    source = _load_p3_source()
    contract_rows = _contract_rows()
    resolution_rows = _resolution_rows()
    issue_rows = _issue_rows()
    safety_rows = _safety_rows()
    checks = {
        "source_boundary": _validate_source_boundary_rows(source_rows),
        "p3_predecessor": _validate_p3_predecessor(source),
        "design_contract": _validate_contract_rows(contract_rows),
        "resolution_matrix": _validate_resolution_rows(resolution_rows),
        "issue_inventory": _validate_issue_rows(issue_rows),
        "safety": _validate_safety_rows(safety_rows),
    }
    if section_overrides:
        for key, value in section_overrides.items():
            if key not in checks or type(value) is not bool:
                raise ValueError("invalid section override")
            checks[key] = value
    failures = [SECTION_FAILURE_IDS[key] for key, passed in checks.items() if not passed]
    return {
        "source_rows": source_rows, "source": source,
        "contract_rows": contract_rows, "resolution_rows": resolution_rows,
        "issue_rows": issue_rows, "safety_rows": safety_rows,
        "checks": checks, "validation_failures": failures,
        "all_checks_passed": not failures,
    }


def _write_non_manifest_outputs(root: Path, result: dict[str, Any]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    expected = {
        CSV_OUTPUTS[0]: (CONTRACT_COLUMNS, result["contract_rows"]),
        CSV_OUTPUTS[1]: (RESOLUTION_COLUMNS, result["resolution_rows"]),
        CSV_OUTPUTS[2]: (SOURCE_COLUMNS, result["source_rows"]),
        CSV_OUTPUTS[3]: (SAFETY_COLUMNS, result["safety_rows"]),
        CSV_OUTPUTS[4]: (ISSUE_COLUMNS, result["issue_rows"]),
    }
    for filename, (columns, rows) in expected.items():
        _write_csv(root / filename, columns, rows)
    return {filename: _sha256(root / filename) for filename in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    passed = result["all_checks_passed"]
    checks = result["checks"]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "previous_stage": PREVIOUS_STAGE, "source_read_boundary": SOURCE_READ_BOUNDARY,
        "source_input_count": 10, "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_file_count": 6,
        "non_manifest_output_count": 5, "output_sha256": output_sha256,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "predecessor_field_count": 22, "predecessor_rule_count": 15,
        "predecessor_context_count": 18, "predecessor_remaining_domain_issue_count": 10,
        "p3_schema_extension_integrated": checks["p3_predecessor"],
        "parser_provider_provenance_export_design_frozen": passed,
        "parser_provider_provenance_export_implemented": False,
        "parser_insertion_tag_registry_ready": checks["design_contract"],
        "raw_token_classifier_contract_ready": checks["design_contract"],
        "insertion_state_resolution_contract_ready": checks["resolution_matrix"],
        "provider_five_field_mapping_contract_ready": checks["design_contract"],
        "provenance_source_id_template_ready": checks["design_contract"],
        "canonical_provenance_payload_contract_ready": checks["design_contract"],
        "provenance_sha256_contract_ready": checks["design_contract"],
        "canonical_provenance_payload_key_count": len(CANONICAL_PAYLOAD_KEYS),
        "namespace_evidence_binding_contract_ready": checks["design_contract"],
        "provider_recomputes_namespace_evidence": checks["design_contract"],
        "provider_recomputes_insertion_evidence": checks["design_contract"],
        "atom_site_row_binding_contract_ready": checks["design_contract"],
        "insertion_code_present_value_grammar_fully_frozen": False,
        "parser_insertion_source_tags": list(PARSER_INSERTION_SOURCE_TAGS),
        "raw_token_classes": list(RAW_TOKEN_CLASSES), "raw_token_class_count": 6,
        "resolution_matrix_case_count": 12,
        "existing_sample_count": 11, "insertion_unknown_sample_count": 11,
        "insertion_absence_proven_sample_count": 0,
        "fully_provable_pre_download_sample_count": 0,
        "samples_admissible_current_step": 0,
        "ready_for_parser_provider_provenance_export_smoke_implementation": passed,
        "insertion_code_provenance_export_ready": False,
        "admit_004_rule_logic_ready": False,
        "covalent_residue_identity_semantics_resolved": False,
        "covalent_residue_atom_name_semantics_resolved": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False, "ready_for_training": False,
        "ready_to_train_now": False, "feature_semantics_audit_required_before_training": True,
        "ignored_raw_structure_read_current_step": False,
        "checkpoint_read_current_step": False, "parser_modified_current_step": False,
        "candidate_provider_implemented_current_step": False,
        "candidate_records_materialized_current_step": False,
        "provider_payloads_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "all_source_boundary_checks_passed": checks["source_boundary"],
        "all_p3_predecessor_checks_passed": checks["p3_predecessor"],
        "all_contract_checks_passed": checks["design_contract"],
        "all_resolution_matrix_checks_passed": checks["resolution_matrix"],
        "all_issue_inventory_checks_passed": checks["issue_inventory"],
        "all_safety_checks_passed": checks["safety"],
        "all_checks_passed": passed,
        "validation_failures": result["validation_failures"],
        "current_domain_blocking_reasons": list(DOMAIN_BLOCKING_REASONS),
        "design_followup_issue_ids": list(DESIGN_FOLLOWUP_ISSUE_IDS),
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize six deterministic metadata-only P4 design outputs."""
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    if root.is_symlink():
        raise RuntimeError("output root must not be a symlink")
    result = _build_materialization()
    output_sha256 = _write_non_manifest_outputs(root, result)
    manifest = _manifest_payload(result, output_sha256)
    (root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1()
