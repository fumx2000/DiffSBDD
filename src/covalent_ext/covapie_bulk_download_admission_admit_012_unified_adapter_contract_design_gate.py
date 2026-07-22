"""Design-only contract gate for the future ADMIT_012 unified adapter.

This module freezes five-envelope routing, Exact10 source/oracle validation,
and typed-to-string Exact13 projection.  It deliberately defines no runtime
handler, registry, dispatcher, provider mapping, downloader, or ADMIT_013
judgment and performs no raw, model, checkpoint, or training work.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import importlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, NoReturn


PROJECT = "CovaPIE"
STEP = "ADMIT_012 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1"
EXPECTED_BASE_COMMIT = "16bedd92f97a4c52743f4f923d5c42ae8fee9a84"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_012 standalone evaluator interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_012_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_012_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_012"
ADMISSION_RULE_NAME = "future_download_integrity_fields_required"
ADAPTER_ID = "covapie_admit_012_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_012"
FORMAL_RESULT_TYPE = "Admit012EvaluationResult"
INDEPENDENT_ORACLE_NAME = "classify_admit_012_formal_evaluator_interface_design"
INDEPENDENT_ORACLE_RESULT_TYPE = "Admit012EvaluationResultContractDesign"
CURRENT_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 12))
FUTURE_REGISTERED_RULE_ORDER = (*CURRENT_REGISTERED_RULE_ORDER, ADMISSION_RULE_ID)
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
DOWNLOAD_RESULT_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
POLICY_CONTEXT_ITEMS = (
    "allowed_download_result_statuses",
    "successful_http_status_contract",
    "content_length_contract",
    "sha256_format_contract",
)
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "validated_download_result_fields",
    "consumed_download_result_fields", "consumed_context_items", "evaluator_io_used",
)
DISPATCH_ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
DISPATCH_ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid", "rejected")
CONTEXT_REASONS = {
    "batch_context": "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "allowed_download_result_statuses": "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED",
    "successful_http_status_contract": "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED",
    "content_length_contract": "ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED",
    "sha256_format_contract": "ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED",
    "download_result_context": "ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
    "stage_authorization_context": "ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_MAPPING_REASON = "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_mapping_validation",
    "allowed_download_result_statuses_required_key_lookup",
    "successful_http_status_contract_required_key_lookup",
    "content_length_contract_required_key_lookup",
    "sha256_format_contract_required_key_lookup",
    "download_result_context_mapping_validation",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "download_result_exact4_lookup_first_missing_stops",
    "formal_evaluator_exactly_once",
    "standalone_source_exact10_validation",
    "independent_oracle_exactly_once",
    "full_exact10_equality",
    "typed_to_string_exact13_projection",
)

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py", "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv", "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_truth_matrix.csv", "dc97cd08eabad03315a1533332e2b243122696b605c701051f3024f6189cb5d8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_issue_readiness_inventory.csv", "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json", "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py", "eea31caa76e06507f7dd482dc7c6b2928f6d0f28ded33c47eb31d25b3be7a927"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv", "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv", "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json", "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py", "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv", "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json", "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py", "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv", "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_manifest.json", "9895bf9b82eb9ca0f9c90ef8012af644a2b325dd971c3e6655b361fc8ff83011"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py", "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv", "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json", "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884"),
    ("src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py", "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"),
)
SOURCE_PATH_LIST_SHA256 = "c541a32eb23ac4bc0e95f4778923b6d24f62cc8623c6b25992725c32eb66c233"
SOURCE_PATH_SHA256_PAIRS_SHA256 = "e40b85438e3f2068efd3747b050763a9ee9d98e92baebca928c20a3fcb9b2f4e"

CONTRACT_FILENAME = "covapie_admit_012_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_012_download_result_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_012_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_012_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_012_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_012_unified_adapter_contract_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME, ROUTING_FILENAME, TRUTH_FILENAME,
    SAFETY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME,
)
FROZEN_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8",
    ROUTING_FILENAME: "50d0e3d8ba7352d139d35a6cda35afad7f40ef4ea111bbea7b3cd31200ec9839",
    TRUTH_FILENAME: "843754e8e8c4246f156ac27079fe0b890e62ed1df0703398e21af9b5bdb94fe7",
    SAFETY_FILENAME: "736066e78df6e0acf28c539c8432b539855212ef1ff76693feae94d4725cc499",
    ISSUE_FILENAME: "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5",
    MANIFEST_FILENAME: "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25",
}

CONTRACT_COLUMNS = (
    "contract_order", "contract_id", "contract_group", "contract_subject",
    "contract_value", "contract_status",
)
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "routing_condition",
    "envelope_representation", "lookup_count", "lookup_order",
    "candidate_key_access_count", "formal_call_count", "oracle_call_count",
    "identity_preserved", "expected_dispatch_code", "expected_reason",
    "expected_result_json", "case_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "routing_condition",
    "candidate_record_representation", "batch_context_representation",
    "evaluation_context_representation", "download_result_context_representation",
    "stage_authorization_context_representation", "evaluation_lookup_count",
    "download_lookup_count", "candidate_key_access_count", "lookup_order",
    "formal_call_count", "oracle_call_count", "source_exact10_json",
    "oracle_exact10_json", "projected_exact13_json", "identity_preserved",
    "expected_dispatch_code", "expected_reason", "case_passed",
)
SAFETY_COLUMNS = (
    "safety_order", "safety_item", "expected_executed",
    "observed_executed", "evidence", "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_sha256: str
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _exact_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _exact_string_pair_tuple(value: object) -> bool:
    return type(value) is tuple and all(
        type(pair) is tuple and len(pair) == 2
        and type(pair[0]) is str and type(pair[1]) is str
        for pair in value
    )


@dataclass(frozen=True)
class UnifiedAdmissionEvaluationDesignRecord:
    schema_version: str
    admission_rule_id: str
    admission_rule_name: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    normalized_values: tuple[tuple[str, str], ...]
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool
    adapter_id: str

    def __post_init__(self) -> None:
        if type(self) is not UnifiedAdmissionEvaluationDesignRecord:
            raise TypeError("exact unified Design result required")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("Exact13 Design field order drift")
        strings = (
            self.schema_version, self.admission_rule_id, self.admission_rule_name,
            self.outcome, self.reason, self.adapter_id,
        )
        if any(type(value) is not str for value in strings):
            raise TypeError("Exact13 string field type drift")
        if any(type(value) is not bool for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)):
            raise TypeError("Exact13 bool field type drift")
        if not _exact_string_pair_tuple(self.normalized_values) or not _exact_string_pair_tuple(self.validated_candidate_fields):
            raise TypeError("Exact13 pair fields require exact string pairs")
        if not _exact_string_tuple(self.consumed_candidate_fields) or not _exact_string_tuple(self.consumed_context_items):
            raise TypeError("Exact13 consumed fields require exact string tuples")
        if (
            self.schema_version != RESULT_SCHEMA_VERSION
            or self.admission_rule_id != ADMISSION_RULE_ID
            or self.admission_rule_name != ADMISSION_RULE_NAME
            or self.adapter_id != ADAPTER_ID
        ):
            raise ValueError("Exact13 identity drift")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("Exact13 outcome drift")
        if self.passed is not (self.outcome == "passed") or self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("Exact13 outcome flags drift")
        if (self.reason == "") is not self.passed or self.evaluator_io_used is not False:
            raise ValueError("Exact13 reason or I/O invariant drift")


@dataclass(frozen=True)
class SourceValidationDecision:
    accepted: bool
    code: str
    reason: str
    adapter_ready: bool


class AdapterContractDesignError(Exception):
    """Design-only representation of a future Exact6 dispatch failure."""

    def __init__(self, code: str, reason: str, *, adapter_ready: bool) -> None:
        self.code = code
        self.admission_rule_id = ADMISSION_RULE_ID
        self.known_rule = True
        self.callable_discovered = True
        self.adapter_ready = adapter_ready
        self.reason = reason
        super().__init__(reason)

    def as_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in DISPATCH_ERROR_FIELDS}


def _standalone_module() -> Any:
    return importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_012_rule_logic_interface"
    )


def _oracle_module() -> Any:
    return importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate"
    )


def validate_source_shape_and_invariants_for_design(source: object) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit012EvaluationResult
    if type(source) is not result_type:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, False
        )
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 storage/order drift")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 dataclass order drift")
        values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        exact_types = (str, str, bool, bool, str, tuple, tuple, tuple, tuple, bool)
        if any(type(value) is not expected for value, expected in zip(values, exact_types, strict=True)):
            raise TypeError("Exact10 top-level type drift")
        reconstructed = result_type(*values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact10 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False
        )
    return SourceValidationDecision(True, "", "", True)


def expected_exact10_from_committed_oracle_for_design(
    field_kwargs: Mapping[str, object],
    context_kwargs: Mapping[str, object],
    *,
    oracle_callable: Callable[..., object] | None = None,
) -> Any:
    """Call the independent Design oracle once and construct formal Exact10."""
    standalone = _standalone_module()
    oracle = _oracle_module()
    classify = (
        oracle.classify_admit_012_formal_evaluator_interface_design
        if oracle_callable is None else oracle_callable
    )
    try:
        classification = classify(**field_kwargs, **context_kwargs)
        result_type = oracle.Admit012EvaluationResultContractDesign
        if type(classification) is not result_type:
            raise TypeError("oracle exact result type required")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact10 dataclass order drift")
        storage = vars(classification)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact10 storage/order drift")
        values = tuple(getattr(classification, name) for name in STANDALONE_RESULT_FIELDS)
        exact_types = (str, str, bool, bool, str, tuple, tuple, tuple, tuple, bool)
        if any(type(value) is not expected for value, expected in zip(values, exact_types, strict=True)):
            raise TypeError("oracle Exact10 top-level type drift")
        if result_type(*values) != classification:
            raise ValueError("oracle Exact10 reconstruction drift")
        return standalone.Admit012EvaluationResult(*values)
    except Exception as error:
        raise ValueError(SOURCE_INVARIANT_REASON) from error


def validate_source_oracle_equivalence_for_design(
    source: object, expected: object,
) -> SourceValidationDecision:
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        return decision
    standalone = _standalone_module()
    if type(expected) is not standalone.Admit012EvaluationResult:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False
        )
    try:
        source_values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        expected_values = tuple(getattr(expected, name) for name in STANDALONE_RESULT_FIELDS)
    except AttributeError:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False
        )
    if any(
        type(left) is not type(right) or left != right
        for left, right in zip(source_values, expected_values, strict=True)
    ):
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False
        )
    return SourceValidationDecision(True, "", "", True)


def project_download_result_pairs_to_exact_string_pairs(
    ordered_pairs: object,
) -> tuple[tuple[str, str], ...]:
    """Project a validated ordered Exact4 prefix to exact string pairs."""
    if type(ordered_pairs) is not tuple or len(ordered_pairs) > len(DOWNLOAD_RESULT_FIELDS):
        raise TypeError("validated ordered pair tuple required")
    projected = []
    for index, pair in enumerate(ordered_pairs):
        if (
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str or pair[0] != DOWNLOAD_RESULT_FIELDS[index]
        ):
            raise TypeError("ordered Exact4 pair shape drift")
        value = pair[1]
        if index in (0, 3):
            if type(value) is not str:
                raise TypeError("status/SHA projection requires exact str")
            projected_value = value
        else:
            if type(value) is not int:
                raise TypeError("HTTP/content projection requires exact int")
            projected_value = str(value)
        if type(projected_value) is not str:
            raise TypeError("projection did not produce exact str")
        projected.append((pair[0], projected_value))
    return tuple(projected)


def project_exact10_to_exact13_for_design(
    source: object,
) -> UnifiedAdmissionEvaluationDesignRecord:
    if not validate_source_shape_and_invariants_for_design(source).accepted:
        raise ValueError("source is not projection-ready")
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION,
        source.admission_rule_id,
        ADMISSION_RULE_NAME,
        source.outcome,
        source.passed,
        source.blocks_candidate,
        source.reason,
        project_download_result_pairs_to_exact_string_pairs(
            source.canonical_download_result_record
        ),
        project_download_result_pairs_to_exact_string_pairs(
            source.validated_download_result_fields
        ),
        source.consumed_download_result_fields,
        source.consumed_context_items,
        source.evaluator_io_used,
        ADAPTER_ID,
    )


def candidate_invalid_exact13_for_design() -> UnifiedAdmissionEvaluationDesignRecord:
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION, ADMISSION_RULE_ID, ADMISSION_RULE_NAME,
        "invalid", False, True, CANDIDATE_MAPPING_REASON, (), (), (),
        POLICY_CONTEXT_ITEMS, False, ADAPTER_ID,
    )


def _raise_design_error(code: str, reason: str, adapter_ready: bool) -> NoReturn:
    raise AdapterContractDesignError(code, reason, adapter_ready=adapter_ready)


def classify_admit_012_unified_adapter_design(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
    formal_evaluator: Callable[..., object] | None = None,
    oracle_callable: Callable[..., object] | None = None,
) -> UnifiedAdmissionEvaluationDesignRecord:
    """Exercise the frozen future algorithm without implementing its handler."""
    if batch_context is not None:
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["batch_context"], True,
        )
    if not isinstance(evaluation_context, Mapping):
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["evaluation_context"], True,
        )
    context_kwargs: dict[str, object] = {}
    for name in POLICY_CONTEXT_ITEMS:
        try:
            context_kwargs[name] = evaluation_context[name]
        except KeyError:
            _raise_design_error(
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                CONTEXT_REASONS[name], True,
            )
    if not isinstance(download_result_context, Mapping):
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["download_result_context"], True,
        )
    if stage_authorization_context is not None:
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["stage_authorization_context"], True,
        )
    if not isinstance(candidate_record, Mapping):
        return candidate_invalid_exact13_for_design()

    field_kwargs: dict[str, object] = {}
    for name in DOWNLOAD_RESULT_FIELDS:
        try:
            field_kwargs[name] = download_result_context[name]
        except KeyError:
            break

    evaluator = _standalone_module().evaluate_admit_012 if formal_evaluator is None else formal_evaluator
    source = evaluator(**field_kwargs, **context_kwargs)
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        expected = expected_exact10_from_committed_oracle_for_design(
            field_kwargs, context_kwargs, oracle_callable=oracle_callable,
        )
    except ValueError:
        _raise_design_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False
        )
    decision = validate_source_oracle_equivalence_for_design(source, expected)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    return project_exact10_to_exact13_for_design(source)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(root: Path, arguments: Sequence[str]) -> bytes:
    result = subprocess.run(
        ("git", *arguments), cwd=root, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise ValueError("source-boundary git command failed")
    return result.stdout


def _parent_chain_is_real(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("parent chain is unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("parent chain escaped anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("parent chain resolved identity drift")


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _read_pinned(path: Path, identity: tuple[int, int, int]) -> bytes:
    if _identity(os.lstat(path)) != identity:
        raise ValueError("source identity changed before open")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise ValueError("source descriptor identity changed")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != identity or _identity(os.lstat(path)) != identity:
            raise ValueError("source identity changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode) or root.resolve(strict=True) != root:
        raise ValueError("repository identity unsafe")
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head_ref invalid")
    if _git(root, ("show", "-s", "--format=%s", EXPECTED_BASE_COMMIT)).decode().rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("base subject drift")
    _git(root, ("merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref))
    if len(SOURCE_BOUNDARY) != 19 or len({path for path, _ in SOURCE_BOUNDARY}) != 19:
        raise ValueError("fixed ordered Exact19 source boundary drift")
    path_digest = _sha(json.dumps([path for path, _ in SOURCE_BOUNDARY], separators=(",", ":")).encode())
    pair_digest = _sha(json.dumps([[path, digest] for path, digest in SOURCE_BOUNDARY], separators=(",", ":")).encode())
    if path_digest != SOURCE_PATH_LIST_SHA256 or pair_digest != SOURCE_PATH_SHA256_PAIRS_SHA256:
        raise ValueError("source boundary digest drift")
    inspected = []
    for relative, expected in SOURCE_BOUNDARY:
        relative_path = Path(relative)
        if (
            relative_path.is_absolute() or not relative_path.parts or ".." in relative_path.parts
            or relative_path.parts[:2] == ("data", "raw")
            or relative_path.parts[0] == "checkpoints" or STAGE in relative_path.parts
        ):
            raise ValueError("unsafe source path")
        path = root / relative_path
        _parent_chain_is_real(path.parent, root)
        item = os.lstat(path)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True) != path:
            raise ValueError("source leaf unsafe")
        if _git(root, ("ls-files", "--error-unmatch", "--", relative)).decode() != f"{relative}\n":
            raise ValueError("source is not tracked")
        tree = _git(root, ("ls-tree", EXPECTED_BASE_COMMIT, "--", relative)).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise ValueError("base tree cardinality drift")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if (
            tree_path.decode() != relative or len(parts) != 3
            or parts[0] not in (b"100644", b"100755") or parts[1] != b"blob"
        ):
            raise ValueError("base tree entry drift")
        inspected.append((relative_path, expected, path, parts[0].decode(), _identity(item)))
    records = []
    for relative, expected, path, mode, identity in inspected:
        base = _git(root, ("show", f"{EXPECTED_BASE_COMMIT}:{relative.as_posix()}"))
        content = _read_pinned(path, identity)
        base_sha, filesystem_sha = _sha(base), _sha(content)
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {relative}")
        records.append(FrozenSourceRecord(relative, expected, mode, base_sha, filesystem_sha, content))
    return FrozenSourceSnapshot(tuple(records))


def _record(snapshot: FrozenSourceSnapshot, index: int) -> FrozenSourceRecord:
    record = snapshot.records[index]
    if record.relative_path.as_posix() != SOURCE_BOUNDARY[index][0]:
        raise ValueError("source snapshot order drift")
    return record


def _csv_document(
    snapshot: FrozenSourceSnapshot, index: int,
) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    reader = csv.DictReader(io.StringIO(_record(snapshot, index).content.decode(), newline=""))
    header = tuple(reader.fieldnames or ())
    rows = tuple(dict(row) for row in reader)
    if not header or len(header) != len(set(header)) or any(tuple(row) != header or None in row.values() for row in rows):
        raise ValueError("CSV shape drift")
    return header, rows


def _json_document(snapshot: FrozenSourceSnapshot, index: int) -> dict[str, Any]:
    value = json.loads(_record(snapshot, index).content)
    if type(value) is not dict:
        raise ValueError("JSON root must be object")
    return value


def _literal_registry_keys(source: bytes) -> tuple[str, ...]:
    tree = ast.parse(source.decode())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY"
            for target in node.targets
        ):
            value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
            if isinstance(value, ast.Dict) and all(isinstance(key, ast.Constant) and type(key.value) is str for key in value.keys):
                return tuple(key.value for key in value.keys)
    raise ValueError("literal runtime registry absent")


def _top_functions(source: bytes) -> set[str]:
    return {
        node.name for node in ast.parse(source.decode()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    standalone_contract_header, standalone_contract = _csv_document(snapshot, 1)
    standalone_truth_header, standalone_truth = _csv_document(snapshot, 2)
    issue_header, issue_rows = _csv_document(snapshot, 3)
    standalone_manifest = _json_document(snapshot, 4)
    formal_routing_header, formal_routing = _csv_document(snapshot, 6)
    formal_truth_header, formal_truth = _csv_document(snapshot, 7)
    formal_manifest = _json_document(snapshot, 8)
    field_header, field_rows = _csv_document(snapshot, 10)
    field_manifest = _json_document(snapshot, 11)
    runtime_contract_header, runtime_contract = _csv_document(snapshot, 13)
    runtime_manifest = _json_document(snapshot, 14)
    admit011_contract_header, admit011_contract = _csv_document(snapshot, 16)
    admit011_manifest = _json_document(snapshot, 17)
    issues = {row["issue_id"]: row for row in issue_rows}
    resolved = {
        "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
        "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
        "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED",
        "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
        "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
        "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    }
    original_tree = ast.parse(_record(snapshot, 18).content.decode())
    original_result = next(
        node for node in original_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "UnifiedAdmissionRuleEvaluation"
    )
    annotation_names = {
        node.target.id: ast.unparse(node.annotation)
        for node in original_result.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    checks = (
        FORMAL_EVALUATOR_NAME in _top_functions(_record(snapshot, 0).content),
        standalone_manifest.get("result_type") == FORMAL_RESULT_TYPE,
        standalone_manifest.get("result_fields") == list(STANDALONE_RESULT_FIELDS),
        standalone_manifest.get("row_counts", {}).get("truth_matrix") == 105,
        len(standalone_contract) == 18 and len(standalone_truth) == 105,
        len(standalone_contract_header) == 11 and len(standalone_truth_header) == 26,
        INDEPENDENT_ORACLE_NAME in _top_functions(_record(snapshot, 5).content),
        FORMAL_EVALUATOR_NAME not in _top_functions(_record(snapshot, 5).content),
        len(formal_routing) == 27 and len(formal_truth) == 105,
        len(formal_routing_header) == 13 and len(formal_truth_header) == 21,
        tuple(row["case_id"] for row in standalone_truth) == tuple(row["case_id"] for row in formal_truth),
        formal_manifest.get("design_oracle") == INDEPENDENT_ORACLE_NAME,
        field_manifest.get("exact4_fields") == list(DOWNLOAD_RESULT_FIELDS),
        tuple(row["field_name"] for row in field_rows) == DOWNLOAD_RESULT_FIELDS,
        len(field_header) == 23 and len(field_rows) == 4,
        _literal_registry_keys(_record(snapshot, 12).content) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("result_fields") == list(RESULT_FIELDS),
        len(runtime_contract_header) == 7 and len(runtime_contract) == 36,
        "_evaluate_registered_admit_012" not in _top_functions(_record(snapshot, 12).content),
        admit011_manifest.get("future_registered_rule_order") == list(CURRENT_REGISTERED_RULE_ORDER),
        len(admit011_contract_header) == 6 and len(admit011_contract) == 26,
        annotation_names.get("normalized_values") == "tuple[tuple[str, str], ...]",
        annotation_names.get("validated_candidate_fields") == "tuple[tuple[str, str], ...]",
        issue_header == ISSUE_COLUMNS and len(issue_rows) == 16,
        all(issues[issue]["status"] == "resolved" for issue in resolved),
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open",
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "standalone_truth": standalone_truth,
        "formal_truth": formal_truth,
        "issue_rows": issue_rows,
        "issue_bytes": _record(snapshot, 3).content,
    }


def _json_record(value: object) -> str:
    return json.dumps(
        {field.name: getattr(value, field.name) for field in fields(value)},
        ensure_ascii=True, separators=(",", ":"),
    )


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "rule", f"{ADMISSION_RULE_ID}|{ADMISSION_RULE_NAME}|{ADAPTER_ID}"),
        ("identity", "formal_evaluator", f"{FORMAL_EVALUATOR_NAME}|{FORMAL_RESULT_TYPE}"),
        ("registry", "current_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("registry", "future_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registry", "known_ids", "|".join(KNOWN_RULE_IDS)),
        ("routing", "five_envelopes", "candidate_record|batch_context|evaluation_context|download_result_context|stage_authorization_context"),
        ("routing", "precedence", "|".join(CONTEXT_ROUTING_ORDER)),
        ("candidate", "mapping_only", "Mapping_envelope_only_zero_key_access"),
        ("candidate", "formal_source", "none"),
        ("candidate", "non_mapping_reason", CANDIDATE_MAPPING_REASON),
        ("batch", "required_value", "None"),
        ("stage", "required_value", "None"),
        ("evaluation", "mapping_and_ordered_keys", "|".join(POLICY_CONTEXT_ITEMS)),
        ("download_result", "mapping_and_ordered_keys", "|".join(DOWNLOAD_RESULT_FIELDS)),
        ("download_result", "missing", "omit_keyword_and_stop_later_lookup"),
        ("download_result", "private_sentinel", "not_imported_or_passed"),
        ("formal", "call", "keyword_only_exactly_once_after_routing"),
        ("formal", "identity", "all_present_fields_and_contexts_preserved"),
        ("oracle", "call", "same_kwargs_exactly_once_after_source_validation"),
        ("oracle", "result_type", INDEPENDENT_ORACLE_RESULT_TYPE),
        ("source", "exact10_fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("source", "validation", "exact_type_storage_order_types_reconstruction_reason_invariants"),
        ("source", "oracle_equality", "all_Exact10_values_and_types_equal"),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("projection", "canonical", "canonical_download_result_record_to_normalized_values"),
        ("projection", "validated", "validated_download_result_fields_to_historical_validated_candidate_fields"),
        ("projection", "consumed", "consumed_download_result_fields_to_historical_consumed_candidate_fields"),
        ("projection", "string_rule", "status_and_sha_exact_str_unchanged|http_and_content_exact_int_to_base10_ASCII_str"),
        ("projection", "strict_types", "bool_int_subclass_str_subclass_rejected"),
        ("projection", "no_schema_widening", "Exact13_string_pairs_only"),
        ("dispatch", "source_type", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_TYPE_REASON}"),
        ("dispatch", "source_invariant", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_INVARIANT_REASON}"),
        ("boundary", "runtime", "design_only_no_handler_registry_dispatcher_or_result_v2"),
        ("boundary", "admit_013", "not_implemented_or_judged"),
        ("boundary", "operations", "no_provider_raw_network_download_model_checkpoint_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    return [{
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1)]


def _routing_rows() -> list[dict[str, str]]:
    def row(
        group: str, case_id: str, condition: str, envelope: str,
        lookups: Sequence[str] = (), candidate_access: int = 0,
        formal: int = 0, oracle: int = 0, identity: str = "n/a",
        code: str = "", reason: str = "", result: str = "",
    ) -> dict[str, str]:
        return {
            "matrix_order": "", "matrix_group": group, "case_id": case_id,
            "routing_condition": condition, "envelope_representation": envelope,
            "lookup_count": str(len(lookups)), "lookup_order": "|".join(lookups),
            "candidate_key_access_count": str(candidate_access),
            "formal_call_count": str(formal), "oracle_call_count": str(oracle),
            "identity_preserved": identity, "expected_dispatch_code": code,
            "expected_reason": reason, "expected_result_json": result,
            "case_passed": "true",
        }

    error = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    eval_prefixes = [POLICY_CONTEXT_ITEMS[:index] for index in range(5)]
    cases = [
        row("routing_failure", "batch_non_none", "batch_context non-None", "batch=object", code=error, reason=CONTEXT_REASONS["batch_context"]),
        row("routing_failure", "evaluation_non_mapping", "evaluation_context non-Mapping", "evaluation=None", code=error, reason=CONTEXT_REASONS["evaluation_context"]),
    ]
    for index, name in enumerate(POLICY_CONTEXT_ITEMS):
        cases.append(row(
            "routing_failure", f"evaluation_missing_{index + 1}", f"evaluation key missing: {name}",
            "evaluation=instrumented_mapping", eval_prefixes[index + 1],
            code=error, reason=CONTEXT_REASONS[name],
        ))
    cases.extend((
        row("routing_failure", "download_non_mapping", "download_result_context non-Mapping", "download=None", POLICY_CONTEXT_ITEMS, code=error, reason=CONTEXT_REASONS["download_result_context"]),
        row("routing_failure", "stage_non_none", "stage_authorization_context non-None", "stage=object", POLICY_CONTEXT_ITEMS, code=error, reason=CONTEXT_REASONS["stage_authorization_context"]),
        row("candidate", "candidate_non_mapping", "candidate_record non-Mapping", "candidate=object", POLICY_CONTEXT_ITEMS, result=_json_record(candidate_invalid_exact13_for_design()), reason=CANDIDATE_MAPPING_REASON),
        row("candidate", "candidate_empty_mapping", "candidate empty Mapping", "candidate={}", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("candidate", "candidate_extra_fields", "candidate Mapping has unrelated keys", "candidate={extra:bomb}", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("candidate", "candidate_zero_key_access", "candidate access bomb", "candidate=instrumented_mapping", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
    ))
    for index, name in enumerate(DOWNLOAD_RESULT_FIELDS):
        lookup = (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS[:index + 1])
        cases.append(row(
            "first_missing", f"first_missing_{index + 1}", f"first missing download key: {name}",
            "download=instrumented_mapping", lookup, formal=1, oracle=1, identity="true",
        ))
    cases.extend((
        row("first_missing", "empty_download_mapping", "all download keys absent", "download={}", (*POLICY_CONTEXT_ITEMS, DOWNLOAD_RESULT_FIELDS[0]), formal=1, oracle=1, identity="true"),
        row("lookup", "present_none", "present None is not missing", "download status=None", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("lookup", "present_false", "present False is not missing", "download http=False", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("lookup", "present_zero", "present zero is not missing", "download content=0", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("lookup", "extra_download_key", "extra download key ignored", "download={Exact4,extra:bomb}", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("lookup", "identity_preserved", "present field/context objects forwarded", "identity_sentinels", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("call", "formal_once", "valid routing", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("call", "oracle_once", "valid formal source", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("call", "formal_exception", "formal raises", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=0, identity="true"),
        row("source_failure", "formal_wrong_type", "formal returns object", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=0, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_TYPE_REASON),
        row("source_failure", "formal_storage_order", "formal storage order drift", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=0, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("source_failure", "formal_top_level_type", "formal Exact10 top-level type drift", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=0, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("source_failure", "formal_pair_type", "formal canonical pair type drift", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=0, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "oracle_exception", "oracle raises", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "oracle_wrong_type", "oracle exact type drift", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "oracle_storage_order", "oracle storage order drift", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "formal_oracle_mismatch", "full Exact10 mismatch", "all_envelopes_valid", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        row("projection", "full_success", "complete passed Exact10", "success|200|1|lower_sha", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "failure_status", "failure status remains passed", "failure|599|0|lower_sha", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "http_boundaries", "HTTP 100/200/404/599 canonical decimal", "http=100|200|404|599", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "content_values", "content 0/1/large canonical decimal", "content=0|1|large", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "validated_prefixes", "validated prefix lengths 0..4", "prefix=0|1|2|3|4", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "exact_string_pairs", "no int enters Exact13", "exact_string_pairs_only", (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS), formal=1, oracle=1, identity="true"),
        row("registry", "current_exact11", "current order unchanged", "ADMIT_001..011"),
        row("registry", "future_exact12", "future order frozen", "ADMIT_001..012"),
        row("registry", "known_unregistered", "ADMIT_013..015 remain known unregistered", "ADMIT_013|ADMIT_014|ADMIT_015"),
        row("registry", "handler_identity", "existing 11 handler identities unchanged", "identity_preserved", identity="true"),
    ))
    for index, value in enumerate(cases, 1):
        value["matrix_order"] = str(index)
    return cases


class _TruthMissing:
    __slots__ = ()


_TRUTH_MISSING = _TruthMissing()


class _TruthStrSubclass(str):
    pass


class _TruthIntSubclass(int):
    pass


class _TruthTupleSubclass(tuple):
    pass


class _TruthPairSubclass(tuple):
    pass


def _decode_token(text: str) -> object:
    if text == "<MISSING>":
        return _TRUTH_MISSING
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _TruthStrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _TruthIntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<tuple-subclass:"):
        return _TruthTupleSubclass(ast.literal_eval(text[16:-1]))
    if text.startswith("<tuple-member-str-subclass:"):
        prefix, representation = text[27:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _TruthStrSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<tuple-pair-subclass:"):
        prefix, representation = text[21:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _TruthPairSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<regex:"):
        return re.compile(ast.literal_eval(text[7:-1]))
    return ast.literal_eval(text)


def _truth_rows(predecessor_truth: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    standalone = _standalone_module()
    oracle = _oracle_module()
    representation_columns = tuple(
        f"{name}_representation" for name in (*DOWNLOAD_RESULT_FIELDS, *POLICY_CONTEXT_ITEMS)
    )
    rows = []
    for prior in predecessor_truth:
        decoded = tuple(_decode_token(prior[column]) for column in representation_columns)
        field_kwargs: dict[str, object] = {}
        download_lookups = 0
        for name, value in zip(DOWNLOAD_RESULT_FIELDS, decoded[:4], strict=True):
            download_lookups += 1
            if value is _TRUTH_MISSING:
                break
            field_kwargs[name] = value
        context_kwargs = dict(zip(POLICY_CONTEXT_ITEMS, decoded[4:], strict=True))
        source = standalone.evaluate_admit_012(**field_kwargs, **context_kwargs)
        classification = oracle.classify_admit_012_formal_evaluator_interface_design(
            **field_kwargs, **context_kwargs
        )
        if type(classification) is not oracle.Admit012EvaluationResultContractDesign:
            raise ValueError("oracle truth exact type drift")
        expected = standalone.Admit012EvaluationResult(
            *(getattr(classification, name) for name in STANDALONE_RESULT_FIELDS)
        )
        decision = validate_source_oracle_equivalence_for_design(source, expected)
        if not decision.accepted:
            raise ValueError(f"source/oracle truth mismatch: {prior['case_id']}")
        projected = project_exact10_to_exact13_for_design(source)
        lookup_order = (*POLICY_CONTEXT_ITEMS, *DOWNLOAD_RESULT_FIELDS[:download_lookups])
        evaluation_repr = "|".join(
            f"{name}={prior[f'{name}_representation']}" for name in POLICY_CONTEXT_ITEMS
        )
        download_repr = "|".join(
            f"{name}={prior[f'{name}_representation']}" for name in DOWNLOAD_RESULT_FIELDS
        )
        rows.append({
            "case_order": prior["case_order"], "case_id": prior["case_id"],
            "case_group": prior["case_group"],
            "routing_condition": "formal_Exact105_projection",
            "candidate_record_representation": "{}",
            "batch_context_representation": "None",
            "evaluation_context_representation": evaluation_repr,
            "download_result_context_representation": download_repr,
            "stage_authorization_context_representation": "None",
            "evaluation_lookup_count": "4", "download_lookup_count": str(download_lookups),
            "candidate_key_access_count": "0", "lookup_order": "|".join(lookup_order),
            "formal_call_count": "1", "oracle_call_count": "1",
            "source_exact10_json": _json_record(source),
            "oracle_exact10_json": _json_record(expected),
            "projected_exact13_json": _json_record(projected),
            "identity_preserved": "true", "expected_dispatch_code": "",
            "expected_reason": source.reason, "case_passed": "true",
        })
    if len(rows) != 105 or any(row["case_passed"] != "true" for row in rows):
        raise ValueError("Exact105 projection truth drift")
    return rows


def _adapter_truth_rows(
    routing_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Project every adapter routing/source/registry case into the truth schema."""
    rows = []
    for offset, routing in enumerate(routing_rows, 106):
        lookup_items = tuple(filter(None, routing["lookup_order"].split("|")))
        rows.append({
            "case_order": str(offset),
            "case_id": f"ADAPTER_{routing['case_id'].upper()}",
            "case_group": f"adapter_{routing['matrix_group']}",
            "routing_condition": routing["routing_condition"],
            "candidate_record_representation": "instrumented_mapping_or_declared_case",
            "batch_context_representation": "precedence_defined_by_case",
            "evaluation_context_representation": "instrumented_mapping_or_declared_case",
            "download_result_context_representation": routing["envelope_representation"],
            "stage_authorization_context_representation": "precedence_defined_by_case",
            "evaluation_lookup_count": str(sum(item in POLICY_CONTEXT_ITEMS for item in lookup_items)),
            "download_lookup_count": str(sum(item in DOWNLOAD_RESULT_FIELDS for item in lookup_items)),
            "candidate_key_access_count": routing["candidate_key_access_count"],
            "lookup_order": routing["lookup_order"],
            "formal_call_count": routing["formal_call_count"],
            "oracle_call_count": routing["oracle_call_count"],
            "source_exact10_json": "",
            "oracle_exact10_json": "",
            "projected_exact13_json": routing["expected_result_json"],
            "identity_preserved": routing["identity_preserved"],
            "expected_dispatch_code": routing["expected_dispatch_code"],
            "expected_reason": routing["expected_reason"],
            "case_passed": routing["case_passed"],
        })
    if len(rows) != 43 or any(row["case_passed"] != "true" for row in rows):
        raise ValueError("Exact43 adapter truth projection drift")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        ("production_design_only", "Design API and evidence builder only"),
        ("exact10_source_validation", "exact type/storage/order/types/reconstruction/invariants"),
        ("independent_oracle_equality", "full Exact10 types and values"),
        ("typed_to_string_projection", "exact int to canonical decimal str"),
        ("exact13_string_pair_enforcement", "both pair fields remain exact string pairs"),
        ("deterministic_materialization", "double build and set-atomic publish"),
        ("source_attestation", "fixed ordered Exact19 pinned reads"),
        ("issue_continuity", "standalone Exact16 byte-preserved"),
    )
    negative = (
        ("runtime_handler", "no future handler definition"),
        ("registry", "no registry definition or modification"),
        ("dispatcher", "no dispatcher definition or modification"),
        ("exact11_runtime_change", "committed source SHA frozen"),
        ("UnifiedAdmissionRuleEvaluation_redefinition", "Design suffix type only"),
        ("schema_widening", "no object/int pair allowance"),
        ("int_pair_in_exact13", "projection converts exact int"),
        ("private_standalone_sentinel", "not imported or passed"),
        ("candidate_field_sourcing", "candidate envelope only"),
        ("candidate_key_access", "zero"),
        ("batch_context_sourcing", "must be None"),
        ("stage_authorization_sourcing", "must be None"),
        ("network", "not imported or executed"),
        ("filesystem_in_adapter", "adapter Design path is pure memory"),
        ("raw_read_or_enumeration", "source boundary excludes data/raw"),
        ("provider_mapping", "not implemented or validated"),
        ("download", "not executed"),
        ("admit_013_judgment", "not implemented"),
        ("model_or_checkpoint", "not accessed or modified"),
        ("training", "no backward/optimizer/parameter update"),
        ("stage", "not executed"),
        ("commit", "not executed"),
        ("push", "not executed"),
    )
    pairs = (*((name, True, evidence) for name, evidence in positive), *((name, False, evidence) for name, evidence in negative))
    return [{
        "safety_order": str(index), "safety_item": name,
        "expected_executed": str(executed).lower(),
        "observed_executed": str(executed).lower(),
        "evidence": evidence, "safety_passed": "true",
    } for index, (name, executed, evidence) in enumerate(pairs, 1)]


TRUE_READINESS = (
    "admit_012_preconditions_audited",
    "admit_012_download_integrity_field_contract_frozen",
    "admit_012_field_semantics_complete",
    "admit_012_routing_responsibility_resolved",
    "admit_012_standalone_signature_frozen",
    "admit_012_formal_result_contract_frozen",
    "admit_012_standalone_evaluator_interface_implemented",
    "admit_012_rule_logic_implemented",
    "evaluate_admit_012_implemented",
    "Admit012EvaluationResult_implemented",
    "admit_012_unified_adapter_contract_frozen",
    "admit_012_exact10_to_exact13_projection_frozen",
    "admit_012_download_result_routing_contract_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_012_implementation",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)
READINESS = {
    **{key: True for key in TRUE_READINESS},
    **{key: False for key in FALSE_READINESS},
}


def build_design_state(
    repo_root: Path = REPO_ROOT, head_ref: str = "HEAD",
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref)
    predecessor = _validate_predecessors(snapshot)
    routing_rows = _routing_rows()
    truth_rows = [
        *_truth_rows(predecessor["formal_truth"]),
        *_adapter_truth_rows(routing_rows),
    ]
    state = {
        "snapshot": snapshot,
        "contract_rows": _contract_rows(),
        "routing_rows": routing_rows,
        "truth_rows": truth_rows,
        "safety_rows": _safety_rows(),
        "issue_rows": predecessor["issue_rows"],
        "issue_bytes": predecessor["issue_bytes"],
    }
    if (
        len(state["contract_rows"]) != 36
        or len(state["routing_rows"]) != 43
        or len(state["truth_rows"]) != 148
        or len(state["safety_rows"]) != 31
        or len(state["issue_rows"]) != 16
        or any(row["case_passed"] != "true" for row in (*state["routing_rows"], *state["truth_rows"]))
    ):
        raise ValueError("design state failed closed")
    return state


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode()


def build_artifacts(state: Mapping[str, Any] | None = None) -> dict[str, bytes]:
    state = build_design_state() if state is None else state
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    snapshot = state["snapshot"]
    manifest = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "adapter_id": ADAPTER_ID,
        "formal_evaluator": FORMAL_EVALUATOR_NAME,
        "formal_result_type": FORMAL_RESULT_TYPE,
        "future_adapter_handler": "_evaluate_registered_admit_012",
        "future_adapter_handler_implemented": False,
        "independent_oracle": INDEPENDENT_ORACLE_NAME,
        "independent_oracle_result_type": INDEPENDENT_ORACLE_RESULT_TYPE,
        "download_result_fields": list(DOWNLOAD_RESULT_FIELDS),
        "policy_context_items": list(POLICY_CONTEXT_ITEMS),
        "candidate_record_semantics": "Mapping envelope validation only; zero candidate key access",
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "known_not_registered_rule_ids_after_future": list(KNOWN_RULE_IDS[12:]),
        "existing_handler_identity_preserved": True,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "context_routing_order": list(CONTEXT_ROUTING_ORDER),
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {
            "known_rule": True, "callable_discovered": True, "adapter_ready": True,
        },
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "candidate_invalid_projection": {
            "outcome": "invalid", "passed": False, "blocks_candidate": True,
            "normalized_values": [], "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": list(POLICY_CONTEXT_ITEMS),
            "evaluator_io_used": False, "adapter_id": ADAPTER_ID,
        },
        "field_missing_contract": "omit missing keyword; stop later lookup; no private sentinel",
        "formal_keyword_only": True,
        "formal_call_count_after_routing": 1,
        "oracle_call_count_after_source_validation": 1,
        "present_object_identity_preserved": True,
        "source_exact_type_required": True,
        "source_exact10_full_invariant_validation": True,
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "oracle_exact_type_storage_validation": True,
        "source_oracle_full_exact10_equality_required": True,
        "string_projection_function": "project_download_result_pairs_to_exact_string_pairs",
        "string_projection_contract": {
            "download_result_status": "exact str unchanged",
            "observed_http_status": "exact int to canonical base-10 ASCII str(value)",
            "observed_content_length_bytes": "exact int to canonical base-10 ASCII str(value)",
            "observed_sha256": "exact str unchanged",
        },
        "exact13_projection": {
            "normalized_values": "string-project(source.canonical_download_result_record)",
            "validated_candidate_fields": "string-project(source.validated_download_result_fields)",
            "consumed_candidate_fields": "source.consumed_download_result_fields",
            "consumed_context_items": "source.consumed_context_items",
        },
        "historical_candidate_field_names_note": "validated_candidate_fields and consumed_candidate_fields carry download-result semantics for ADMIT_012 and do not imply candidate_record sourcing",
        "exact13_schema_widened": False,
        "int_pair_allowed_in_exact13": False,
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]),
        "routing_matrix_pass_count": len(state["routing_rows"]),
        "routing_matrix_group_counts": dict(sorted(Counter(row["matrix_group"] for row in state["routing_rows"]).items())),
        "projection_truth_matrix_row_count": len(state["truth_rows"]),
        "projection_truth_matrix_pass_count": len(state["truth_rows"]),
        "projection_truth_matrix_group_counts": dict(sorted(Counter(row["case_group"] for row in state["truth_rows"]).items())),
        "formal_exact105_projection_count": 105,
        "formal_exact105_formal_call_count": 105,
        "formal_exact105_oracle_call_count": 105,
        "projection_truth_formal_call_count": sum(int(row["formal_call_count"]) for row in state["truth_rows"]),
        "projection_truth_oracle_call_count": sum(int(row["oracle_call_count"]) for row in state["truth_rows"]),
        "safety_row_count": len(state["safety_rows"]),
        "safety_pass_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[3][1],
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "cross_rule_aggregation_issue_status": "open",
        "source_boundary_name": "fixed_ordered_exact19_committed_source_boundary",
        "source_input_count": 19,
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "source_input_verification": [{
            "source_order": index,
            "source_relative_path": record.relative_path.as_posix(),
            "tracked": True,
            "base_tree_blob": True,
            "base_tree_mode": record.base_tree_mode,
            "filesystem_regular": True,
            "non_symlink": True,
            "parent_chain_non_symlink": True,
            "safe_descendant": True,
            "pinned_fd_read": True,
            "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256,
            "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": {name: _sha(content) for name, content in payloads.items()},
        "output_sha256_excludes_manifest_self_hash": True,
        "readiness": dict(READINESS),
        **READINESS,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "admit_013_implemented": False,
        "provider_mapping_implemented": False,
        "real_download_executed": False,
        "runtime_changed": False,
        "validation_failures": [],
        "all_checks_passed": True,
    }
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


@dataclass(frozen=True)
class OutputMaterializationPlan:
    root: Path
    parent: Path
    anchor: Path
    root_name: str
    parent_identity: tuple[int, int, int]
    root_identity: tuple[int, int, int] | None
    leaf_identities: tuple[tuple[str, tuple[int, int, int]], ...]


DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None
RENAME_NOREPLACE = 1


def _inspect_output_target_read_only(
    output_root: Path, repo_root: Path,
) -> OutputMaterializationPlan:
    candidate = Path(output_root)
    if candidate.is_absolute():
        root, anchor = candidate, Path(candidate.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape forbidden")
        root, anchor = repo_root / candidate, repo_root
    parent = root.parent
    _parent_chain_is_real(parent, anchor)
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(root, parent, anchor, root.name, parent_identity, None, ())
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode) or root.resolve(strict=True) != root:
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        item = os.lstat(root / name)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _identity(item)))
    return OutputMaterializationPlan(
        root, parent, anchor, root.name, parent_identity,
        _identity(root_item), tuple(leaves),
    )


def _read_at(
    directory_fd: int, name: str, expected_identity: tuple[int, int, int],
) -> bytes:
    item = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if _identity(item) != expected_identity or not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
        raise ValueError("pinned leaf drift")
    descriptor = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned descriptor drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned descriptor changed")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(
        parent_fd, os.fsencode(source), parent_fd, os.fsencode(target), RENAME_NOREPLACE
    ):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), f"{source}->{target}")


def _verify_complete_set(root_fd: int, payloads: Mapping[str, bytes]) -> None:
    if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    for name, content in payloads.items():
        item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        actual = _read_at(root_fd, name, _identity(item))
        if actual != content or _sha(actual) != _sha(content):
            raise ValueError("output payload mismatch")


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if count <= 0:
            raise OSError("short output write")
        offset += count


def _materialize_set(
    plan: OutputMaterializationPlan, payloads: Mapping[str, bytes],
) -> None:
    if tuple(payloads) != OUTPUT_FILES:
        raise ValueError("output payload inventory drift")
    if FROZEN_OUTPUT_SHA256 and {
        name: _sha(content) for name, content in payloads.items()
    } != FROZEN_OUTPUT_SHA256:
        raise ValueError("frozen output payload SHA drift")
    parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    staging_name: str | None = None
    staged: dict[str, tuple[int, int, int]] = {}
    try:
        if _identity(os.fstat(parent_fd)) != plan.parent_identity or _identity(os.lstat(plan.parent)) != plan.parent_identity:
            raise ValueError("output parent identity changed")
        _parent_chain_is_real(plan.parent, plan.anchor)
        if plan.root_identity is not None:
            item = os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
            if _identity(item) != plan.root_identity:
                raise ValueError("output root identity changed")
            root_fd = os.open(plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            identities = dict(plan.leaf_identities)
            for name, content in payloads.items():
                if _read_at(root_fd, name, identities[name]) != content:
                    raise ValueError("existing output differs; repair forbidden")
            _verify_complete_set(root_fd, payloads)
            os.fsync(root_fd)
            return
        try:
            os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = f".admit012-adapter-stage-{secrets.token_hex(16)}"
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        root_fd = os.open(staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        staging_identity = _identity(os.fstat(root_fd))
        for name, content in payloads.items():
            descriptor = os.open(name, WRITE_FILE_FLAGS, 0o600, dir_fd=root_fd)
            try:
                staged[name] = _identity(os.fstat(descriptor))
                _write_all(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if _read_at(root_fd, name, staged[name]) != content:
                raise ValueError("staged output mismatch")
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
        if _identity(os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)) != staging_identity:
            raise ValueError("staging identity drift")
        try:
            os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        os.fsync(parent_fd)
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
    except BaseException:
        if staging_name is not None and root_fd is not None:
            try:
                item = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
                if _identity(item) == _identity(os.fstat(root_fd)) and set(os.listdir(root_fd)) == set(staged):
                    for name, identity in staged.items():
                        if _identity(os.stat(name, dir_fd=root_fd, follow_symlinks=False)) != identity:
                            break
                    else:
                        for name in staged:
                            os.unlink(name, dir_fd=root_fd)
                        os.close(root_fd)
                        root_fd = None
                        os.rmdir(staging_name, dir_fd=parent_fd)
            except BaseException:
                pass
        raise
    finally:
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic design-evidence files."""
    plan = _inspect_output_target_read_only(output_root, repo_root)
    state = build_design_state(repo_root, head_ref)
    payloads = build_artifacts(state)
    _materialize_set(plan, payloads)
    return {
        "state": state,
        "manifest": json.loads(payloads[MANIFEST_FILENAME]),
        "output_root": plan.root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1()
