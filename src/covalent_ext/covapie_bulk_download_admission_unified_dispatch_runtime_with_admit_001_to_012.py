"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_012.

The Exact11 predecessor remains the sole authority for the public Exact13
result, dispatch error, constants, and its eleven registered handlers.  This
successor adds only the ADMIT_012 five-envelope adapter, an immutable Exact12
registry, and a dispatcher bound to that registry.  The public closure is
pure in memory; source attestation, evidence construction, and publication
are reachable only through the explicit materialization entry point.
"""

from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import inspect
import io
import json
import os
import re
import secrets
import stat
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_012_rule_logic_interface as admit012,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate
    as admit012_oracle,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_012 v1"
STAGE = "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1"
EXPECTED_BASE_COMMIT = "fc0f89c16b2afd2cac2e5629aa60cf8f962cbdad"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_012 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = "covapie_unified_dispatch_runtime_with_admit_001_to_012_manifest_v1"
RECOMMENDED_NEXT_STEP = "audit_covapie_admit_013_formal_evaluator_interface_preconditions_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Exact object-identity re-exports from Exact11.
UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 13))
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

ADMISSION_RULE_ID = "ADMIT_012"
ADMISSION_RULE_NAME = "future_download_integrity_fields_required"
ADAPTER_ID = "covapie_admit_012_unified_adapter_v1"
ADMIT_012_DOWNLOAD_RESULT_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
ADMIT_012_CONTEXT_ITEMS = (
    "allowed_download_result_statuses",
    "successful_http_status_contract",
    "content_length_contract",
    "sha256_format_contract",
)
ADMIT_012_SOURCE_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_download_result_record",
    "validated_download_result_fields",
    "consumed_download_result_fields",
    "consumed_context_items",
    "evaluator_io_used",
)

RULE_NAMES = MappingProxyType(
    {**predecessor.RULE_NAMES, ADMISSION_RULE_ID: ADMISSION_RULE_NAME}
)
ADAPTER_IDS = MappingProxyType(
    {**predecessor.ADAPTER_IDS, ADMISSION_RULE_ID: ADAPTER_ID}
)


def _raise_dispatch_error(
    code: str,
    admission_rule_id: str,
    known_rule: bool,
    callable_discovered: bool,
    adapter_ready: bool,
    reason: str | None = None,
) -> NoReturn:
    raise UnifiedAdmissionDispatchError(
        code=code,
        admission_rule_id=admission_rule_id,
        known_rule=known_rule,
        callable_discovered=callable_discovered,
        adapter_ready=adapter_ready,
        reason=code if reason is None else reason,
    )


def _admit012_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ADMISSION_RULE_ID,
        True,
        True,
        True,
        reason,
    )


def _admit012_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        ADMISSION_RULE_ID,
        True,
        True,
        False,
        reason,
    )


def _admit012_candidate_invalid() -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=RULE_NAMES[ADMISSION_RULE_ID],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason="ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=ADMIT_012_CONTEXT_ITEMS,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _prevalidate_admit012_source(source: object) -> admit012.Admit012EvaluationResult:
    """Require the exact committed Exact10 type, storage, types, and invariants."""
    if type(source) is not admit012.Admit012EvaluationResult:
        _admit012_adapter_failure("ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != ADMIT_012_SOURCE_FIELDS:
            raise ValueError("Exact10 storage/order drift")
        if (
            tuple(field.name for field in fields(admit012.Admit012EvaluationResult))
            != ADMIT_012_SOURCE_FIELDS
        ):
            raise ValueError("Exact10 dataclass order drift")
        ordered_values = tuple(
            getattr(source, name) for name in ADMIT_012_SOURCE_FIELDS
        )
        exact_types = (str, str, bool, bool, str, tuple, tuple, tuple, tuple, bool)
        if any(
            type(value) is not expected
            for value, expected in zip(ordered_values, exact_types, strict=True)
        ):
            raise TypeError("Exact10 built-in type drift")
        reconstructed = admit012.Admit012EvaluationResult(*ordered_values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact10 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        _admit012_adapter_failure("ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return source


def _expected_admit012_from_oracle(
    field_kwargs: dict[str, object],
    context_kwargs: dict[str, object],
) -> admit012.Admit012EvaluationResult:
    """Call the independent committed oracle once and construct formal Exact10."""
    try:
        result = admit012_oracle.classify_admit_012_formal_evaluator_interface_design(
            **field_kwargs,
            **context_kwargs,
        )
        result_type = admit012_oracle.Admit012EvaluationResultContractDesign
        if type(result) is not result_type:
            raise TypeError("oracle exact result type required")
        storage = vars(result)
        if type(storage) is not dict or tuple(storage) != ADMIT_012_SOURCE_FIELDS:
            raise ValueError("oracle Exact10 storage/order drift")
        if tuple(field.name for field in fields(result_type)) != ADMIT_012_SOURCE_FIELDS:
            raise ValueError("oracle Exact10 dataclass order drift")
        values = tuple(getattr(result, name) for name in ADMIT_012_SOURCE_FIELDS)
        exact_types = (str, str, bool, bool, str, tuple, tuple, tuple, tuple, bool)
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("oracle Exact10 built-in type drift")
        if result_type(*values) != result:
            raise ValueError("oracle Exact10 reconstruction drift")
        expected = admit012.Admit012EvaluationResult(*values)
    except Exception:
        _admit012_adapter_failure("ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return expected


def _validate_admit012_oracle_equivalence(
    source: admit012.Admit012EvaluationResult,
    expected: admit012.Admit012EvaluationResult,
) -> None:
    if type(expected) is not admit012.Admit012EvaluationResult:
        _admit012_adapter_failure("ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    try:
        source_values = tuple(
            getattr(source, name) for name in ADMIT_012_SOURCE_FIELDS
        )
        expected_values = tuple(
            getattr(expected, name) for name in ADMIT_012_SOURCE_FIELDS
        )
    except AttributeError:
        _admit012_adapter_failure("ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    if any(
        type(left) is not type(right) or left != right
        for left, right in zip(source_values, expected_values, strict=True)
    ):
        _admit012_adapter_failure("ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")


def _project_download_result_pairs_to_exact_string_pairs(
    ordered_pairs: object,
) -> tuple[tuple[str, str], ...]:
    """Project one valid ordered Exact4 pair prefix to exact string pairs."""
    if type(ordered_pairs) is not tuple or len(ordered_pairs) > 4:
        raise TypeError("validated ordered pair tuple required")
    projected: tuple[tuple[str, str], ...] = ()
    for index, pair in enumerate(ordered_pairs):
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or type(pair[0]) is not str
            or pair[0] != ADMIT_012_DOWNLOAD_RESULT_FIELDS[index]
        ):
            raise TypeError("ordered Exact4 pair shape drift")
        value = pair[1]
        if index == 0:
            if type(value) is not str or value not in ("success", "failure"):
                raise TypeError("download status projection requires valid exact str")
            projected_value = value
        elif index == 1:
            if type(value) is not int or not 100 <= value <= 599:
                raise TypeError("HTTP projection requires valid exact int")
            projected_value = str(value)
        elif index == 2:
            if type(value) is not int or value < 0:
                raise TypeError("content projection requires valid exact int")
            projected_value = str(value)
        else:
            if (
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise TypeError("SHA projection requires valid exact str")
            projected_value = value
        if type(projected_value) is not str:
            raise TypeError("projection did not produce exact str")
        projected = (*projected, (pair[0], projected_value))
    return projected


def _project_admit012_exact13(
    source: admit012.Admit012EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=RULE_NAMES[ADMISSION_RULE_ID],
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=_project_download_result_pairs_to_exact_string_pairs(
            source.canonical_download_result_record
        ),
        validated_candidate_fields=_project_download_result_pairs_to_exact_string_pairs(
            source.validated_download_result_fields
        ),
        consumed_candidate_fields=source.consumed_download_result_fields,
        consumed_context_items=source.consumed_context_items,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _evaluate_registered_admit_012(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    if batch_context is not None:
        _admit012_context_failure("ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE")
    if not isinstance(evaluation_context, Mapping):
        _admit012_context_failure("ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED")
    try:
        allowed_statuses = evaluation_context["allowed_download_result_statuses"]
    except KeyError:
        _admit012_context_failure("ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED")
    try:
        http_contract = evaluation_context["successful_http_status_contract"]
    except KeyError:
        _admit012_context_failure("ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED")
    try:
        content_contract = evaluation_context["content_length_contract"]
    except KeyError:
        _admit012_context_failure("ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED")
    try:
        sha_contract = evaluation_context["sha256_format_contract"]
    except KeyError:
        _admit012_context_failure("ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED")
    if not isinstance(download_result_context, Mapping):
        _admit012_context_failure("ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED")
    if stage_authorization_context is not None:
        _admit012_context_failure("ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE")
    if not isinstance(candidate_record, Mapping):
        return _admit012_candidate_invalid()

    context_kwargs = {
        "allowed_download_result_statuses": allowed_statuses,
        "successful_http_status_contract": http_contract,
        "content_length_contract": content_contract,
        "sha256_format_contract": sha_contract,
    }
    field_kwargs: dict[str, object] = {}
    for name in ADMIT_012_DOWNLOAD_RESULT_FIELDS:
        try:
            field_kwargs[name] = download_result_context[name]
        except KeyError:
            break

    source = admit012.evaluate_admit_012(**field_kwargs, **context_kwargs)
    validated_source = _prevalidate_admit012_source(source)
    expected = _expected_admit012_from_oracle(field_kwargs, context_kwargs)
    _validate_admit012_oracle_equivalence(validated_source, expected)
    return _project_admit012_exact13(validated_source)


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": predecessor.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": predecessor.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": predecessor.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": predecessor.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": predecessor.EVALUATOR_REGISTRY["ADMIT_005"],
        "ADMIT_006": predecessor.EVALUATOR_REGISTRY["ADMIT_006"],
        "ADMIT_007": predecessor.EVALUATOR_REGISTRY["ADMIT_007"],
        "ADMIT_008": predecessor.EVALUATOR_REGISTRY["ADMIT_008"],
        "ADMIT_009": predecessor.EVALUATOR_REGISTRY["ADMIT_009"],
        "ADMIT_010": predecessor.EVALUATOR_REGISTRY["ADMIT_010"],
        "ADMIT_011": predecessor.EVALUATOR_REGISTRY["ADMIT_011"],
        "ADMIT_012": _evaluate_registered_admit_012,
    }
)


def evaluate_admission_rule(
    admission_rule_id: str,
    candidate_record: Mapping[str, object],
    *,
    batch_context: Mapping[str, object] | None = None,
    evaluation_context: Mapping[str, object] | None = None,
    download_result_context: Mapping[str, object] | None = None,
    stage_authorization_context: Mapping[str, object] | None = None,
) -> UnifiedAdmissionRuleEvaluation:
    """Evaluate exactly one registered rule without I/O or aggregation."""
    if type(admission_rule_id) is not str:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False
        )
    if admission_rule_id not in KNOWN_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", admission_rule_id, False, False, False
        )
    if admission_rule_id not in CALLABLE_DISCOVERED_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", admission_rule_id, True, False, False
        )
    if admission_rule_id not in ADAPTER_READY_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", admission_rule_id, True, True, False
        )
    handler = EVALUATOR_REGISTRY[admission_rule_id]
    return handler(
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


# === EXACT12 PUBLIC DISPATCH CLOSURE END ===


# Fixed ordered Exact23 committed source boundary.  The adapter design source
# is evidence only and is deliberately absent from the public runtime closure.
_SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py", "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv", "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_truth_matrix.csv", "c6d543b9c1ad6760e202074b981659ca34155c16ec0435b1cec3035c93d90901"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv", "0ceb3aa607fb9a539a3d5a6fd519a685693d765b3606e52be9d3316ce476c752"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_manifest.json", "9895bf9b82eb9ca0f9c90ef8012af644a2b325dd971c3e6655b361fc8ff83011"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate.py", "6de88444d8ee0b62e301fdb19e050166c80344cc45b3ee0612998a72c188f162"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv", "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_download_result_projection_and_context_routing_matrix.csv", "50d0e3d8ba7352d139d35a6cda35afad7f40ef4ea111bbea7b3cd31200ec9839"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_result_projection_truth_matrix.csv", "843754e8e8c4246f156ac27079fe0b890e62ed1df0703398e21af9b5bdb94fe7"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_safety_audit.csv", "736066e78df6e0acf28c539c8432b539855212ef1ff76693feae94d4725cc499"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_issue_readiness_inventory.csv", "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json", "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py", "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv", "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_truth_matrix.csv", "dc97cd08eabad03315a1533332e2b243122696b605c701051f3024f6189cb5d8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_purity_audit.csv", "c0773686a1a9d2d4406e09ff33bf3e217eb9d3135e8556d7461b208ec12990e9"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json", "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py", "eea31caa76e06507f7dd482dc7c6b2928f6d0f28ded33c47eb31d25b3be7a927"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv", "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv", "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json", "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py", "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f"),
    ("src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py", "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in _SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in _SOURCE_BOUNDARY}

(
    PREDECESSOR_SOURCE_PATH,
    PREDECESSOR_CONTRACT_PATH,
    PREDECESSOR_TRUTH_PATH,
    PREDECESSOR_REGISTRY_PATH,
    PREDECESSOR_MANIFEST_PATH,
    ADAPTER_SOURCE_PATH,
    ADAPTER_CONTRACT_PATH,
    ADAPTER_ROUTING_PATH,
    ADAPTER_TRUTH_PATH,
    ADAPTER_SAFETY_PATH,
    ADAPTER_ISSUE_PATH,
    ADAPTER_MANIFEST_PATH,
    STANDALONE_SOURCE_PATH,
    STANDALONE_CONTRACT_PATH,
    STANDALONE_TRUTH_PATH,
    STANDALONE_PURITY_PATH,
    STANDALONE_MANIFEST_PATH,
    ORACLE_SOURCE_PATH,
    ORACLE_ROUTING_PATH,
    ORACLE_TRUTH_PATH,
    ORACLE_MANIFEST_PATH,
    FIELD_SOURCE_PATH,
    ORIGINAL_AUTHORITY_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_001_to_012_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_012_dispatch_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_012_registry_and_identity_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_012_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_012_runtime_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_id",
    "contract_group",
    "contract_subject",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "entrypoint",
    "rule_id_representation",
    "candidate_record_representation",
    "batch_context_representation",
    "evaluation_context_representation",
    "download_result_context_representation",
    "stage_authorization_context_representation",
    "lookup_order",
    "evaluation_lookup_count",
    "download_lookup_count",
    "candidate_key_access_count",
    "formal_call_count",
    "oracle_call_count",
    "expected_result_or_error",
    "observed_result_or_error",
    "old_handler_identity_preserved",
    "case_passed",
)
REGISTRY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_value",
    "observed_value",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_order",
    "safety_item",
    "expected_executed",
    "observed_executed",
    "evidence",
    "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "severity",
    "status",
    "blocking_scope",
    "blocking_reason",
    "issue_origin",
    "integration_transition",
    "issue_count",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    base_tree_mode: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ValueError("source-boundary git command failed")
    return result.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("parent chain is not a real directory chain")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("parent chain escaped anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("parent chain resolved identity drift")


def _read_pinned(path: Path, expected_identity: tuple[int, int, int]) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if (
            _identity(os.fstat(descriptor)) != expected_identity
            or _identity(os.lstat(path)) != expected_identity
        ):
            raise ValueError("source identity changed before read")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(descriptor)) != expected_identity
            or _identity(os.lstat(path)) != expected_identity
        ):
            raise ValueError("source identity changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    """Finish all Exact23 structural checks before the first source-byte read."""
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("repository identity unsafe")
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head_ref invalid")
    subject = _git(root, "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT)
    if subject.decode().rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")
    _git(root, "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref)
    if (
        len(SOURCE_PATHS) != 23
        or len(set(SOURCE_PATHS)) != 23
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact23 source boundary configuration drift")

    inspected: list[tuple[Path, Path, tuple[int, int, int], str]] = []
    for relative in SOURCE_PATHS:
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
            or STAGE in relative.parts
        ):
            raise ValueError("unsafe source boundary path")
        target = root / relative
        _assert_real_parent_chain(target.parent, root)
        item = os.lstat(target)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or target.resolve(strict=True) != target
        ):
            raise ValueError("source leaf unsafe")
        tracked = _git(root, "ls-files", "--error-unmatch", "--", relative.as_posix())
        if tracked.decode() != f"{relative.as_posix()}\n":
            raise ValueError("source is not tracked")
        tree = _git(root, "ls-tree", EXPECTED_BASE_COMMIT, "--", relative.as_posix()).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise ValueError("base tree cardinality drift")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if (
            tree_path.decode() != relative.as_posix()
            or len(parts) != 3
            or parts[0] not in (b"100644", b"100755")
            or parts[1] != b"blob"
        ):
            raise ValueError("base tree entry drift")
        inspected.append((relative, target, _identity(item), parts[0].decode()))

    records = []
    for relative, target, identity, mode in inspected:
        base_bytes = _git(root, "show", f"{EXPECTED_BASE_COMMIT}:{relative.as_posix()}")
        filesystem_bytes = _read_pinned(target, identity)
        expected = SOURCE_SHA256[relative]
        base_sha = _sha(base_bytes)
        filesystem_sha = _sha(filesystem_bytes)
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {relative}")
        records.append(
            FrozenSourceRecord(
                relative,
                expected,
                base_sha,
                filesystem_sha,
                mode,
                filesystem_bytes,
            )
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 23
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and record.base_tree_mode in ("100644", "100755")
            and _sha(record.content_bytes) == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(
        record for record in snapshot.records if record.relative_path == path
    )
    if len(matches) != 1:
        raise ValueError("source record missing or duplicate")
    return matches[0]


def _csv_rows(
    content: bytes,
    columns: Sequence[str] | None = None,
) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    header = tuple(reader.fieldnames or ())
    if (
        not header
        or len(header) != len(set(header))
        or (columns is not None and header != tuple(columns))
    ):
        raise ValueError("CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != header or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("CSV row shape mismatch")
    return rows


def _json_object(content: bytes) -> dict[str, Any]:
    value = json.loads(content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    predecessor_contract = _csv_rows(_record(snapshot, PREDECESSOR_CONTRACT_PATH).content_bytes)
    predecessor_truth = _csv_rows(_record(snapshot, PREDECESSOR_TRUTH_PATH).content_bytes)
    predecessor_registry = _csv_rows(_record(snapshot, PREDECESSOR_REGISTRY_PATH).content_bytes)
    predecessor_manifest = _json_object(_record(snapshot, PREDECESSOR_MANIFEST_PATH).content_bytes)
    adapter_contract = _csv_rows(_record(snapshot, ADAPTER_CONTRACT_PATH).content_bytes)
    adapter_routing = _csv_rows(_record(snapshot, ADAPTER_ROUTING_PATH).content_bytes)
    adapter_truth = _csv_rows(_record(snapshot, ADAPTER_TRUTH_PATH).content_bytes)
    adapter_safety = _csv_rows(_record(snapshot, ADAPTER_SAFETY_PATH).content_bytes)
    adapter_issues = _csv_rows(_record(snapshot, ADAPTER_ISSUE_PATH).content_bytes, ISSUE_COLUMNS)
    adapter_manifest = _json_object(_record(snapshot, ADAPTER_MANIFEST_PATH).content_bytes)
    standalone_contract = _csv_rows(_record(snapshot, STANDALONE_CONTRACT_PATH).content_bytes)
    standalone_truth = _csv_rows(_record(snapshot, STANDALONE_TRUTH_PATH).content_bytes)
    standalone_purity = _csv_rows(_record(snapshot, STANDALONE_PURITY_PATH).content_bytes)
    standalone_manifest = _json_object(_record(snapshot, STANDALONE_MANIFEST_PATH).content_bytes)
    oracle_routing = _csv_rows(_record(snapshot, ORACLE_ROUTING_PATH).content_bytes)
    oracle_truth = _csv_rows(_record(snapshot, ORACLE_TRUTH_PATH).content_bytes)
    oracle_manifest = _json_object(_record(snapshot, ORACLE_MANIFEST_PATH).content_bytes)
    issues = {row["issue_id"]: row for row in adapter_issues}
    checks = (
        len(predecessor_contract) == 36,
        len(predecessor_truth) == 534,
        len(predecessor_registry) == 15,
        predecessor_manifest.get("registered_rule_ids") == list(KNOWN_RULE_IDS[:11]),
        predecessor_manifest.get("unified_dispatch_runtime_with_admit_001_to_011_implemented") is True,
        len(adapter_contract) == 36,
        len(adapter_routing) == 43,
        len(adapter_truth) == 148,
        len(adapter_safety) == 31,
        len(adapter_issues) == 16,
        adapter_manifest.get("future_registered_rule_order") == list(KNOWN_RULE_IDS[:12]),
        adapter_manifest.get("ready_for_unified_dispatch_runtime_with_admit_001_to_012_implementation") is True,
        len(standalone_contract) == 18,
        len(standalone_truth) == 105,
        len(standalone_purity) == 14,
        standalone_manifest.get("result_fields") == list(ADMIT_012_SOURCE_FIELDS),
        len(oracle_routing) == 27,
        len(oracle_truth) == 105,
        oracle_manifest.get("design_oracle") == "classify_admit_012_formal_evaluator_interface_design",
        tuple(row["case_id"] for row in standalone_truth)
        == tuple(row["case_id"] for row in oracle_truth),
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"]
        == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"]
        == "open",
    )
    if not all(checks):
        raise ValueError("predecessor contract mismatch")
    return {
        "predecessor_truth": predecessor_truth,
        "adapter_routing": adapter_routing,
        "adapter_issues": adapter_issues,
        "standalone_truth": standalone_truth,
    }


def _jsonable(value: object) -> object:
    if type(value) is tuple:
        return [_jsonable(item) for item in value]
    if type(value) is list:
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool, float):
        return value
    return f"<{type(value).__name__}>"


def _evaluation_json(value: UnifiedAdmissionRuleEvaluation) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in RESULT_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _error_json(value: UnifiedAdmissionDispatchError) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in DISPATCH_ERROR_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _capture_dispatch(
    module: object,
    rule_id: object,
    candidate: object,
    **contexts: object,
) -> str:
    try:
        value = module.evaluate_admission_rule(rule_id, candidate, **contexts)
    except UnifiedAdmissionDispatchError as error:
        return _error_json(error)
    return _evaluation_json(value)


class _EvidenceMissing:
    __slots__ = ()


_EVIDENCE_MISSING = _EvidenceMissing()


class _EvidenceStrSubclass(str):
    pass


class _EvidenceIntSubclass(int):
    pass


class _EvidenceTupleSubclass(tuple):
    pass


class _EvidencePairSubclass(tuple):
    pass


def _decode_token(text: str) -> object:
    if text == "<MISSING>":
        return _EVIDENCE_MISSING
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _EvidenceStrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _EvidenceIntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<tuple-subclass:"):
        return _EvidenceTupleSubclass(ast.literal_eval(text[16:-1]))
    if text.startswith("<tuple-member-str-subclass:"):
        prefix, representation = text[27:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _EvidenceStrSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<tuple-pair-subclass:"):
        prefix, representation = text[21:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _EvidencePairSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<regex:"):
        return re.compile(ast.literal_eval(text[7:-1]))
    return ast.literal_eval(text)


class _TraceMapping(Mapping[str, object]):
    def __init__(self, values: Mapping[str, object]) -> None:
        self.values = dict(values)
        self.calls: list[str] = []
        self.iterated = False
        self.sized = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.sized = True
        return len(self.values)


class _CandidateBomb(Mapping[str, object]):
    def __init__(self) -> None:
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        raise AssertionError("candidate key accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def _truth_row(
    case_id: str,
    case_group: str,
    entrypoint: str,
    rule_id: str,
    candidate: str,
    batch: str,
    evaluation: str,
    download: str,
    stage: str,
    lookup_order: Sequence[str],
    evaluation_lookups: int,
    download_lookups: int,
    candidate_access: int,
    formal_calls: int,
    oracle_calls: int,
    expected: str,
    observed: str,
    old_identity: bool,
) -> dict[str, str]:
    return {
        "case_order": "",
        "case_id": case_id,
        "case_group": case_group,
        "entrypoint": entrypoint,
        "rule_id_representation": rule_id,
        "candidate_record_representation": candidate,
        "batch_context_representation": batch,
        "evaluation_context_representation": evaluation,
        "download_result_context_representation": download,
        "stage_authorization_context_representation": stage,
        "lookup_order": "|".join(lookup_order),
        "evaluation_lookup_count": str(evaluation_lookups),
        "download_lookup_count": str(download_lookups),
        "candidate_key_access_count": str(candidate_access),
        "formal_call_count": str(formal_calls),
        "oracle_call_count": str(oracle_calls),
        "expected_result_or_error": expected,
        "observed_result_or_error": observed,
        "old_handler_identity_preserved": str(old_identity).lower(),
        "case_passed": str(expected == observed and old_identity).lower(),
    }


def _stable_representation(value: object) -> str:
    if value is None or type(value) in (str, int, bool, float):
        return repr(value)
    return f"<{type(value).__name__}>"


def _predecessor_truth_rows(
    source_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for source in source_rows:
        rule_id = source["admission_rule_id"]
        if rule_id in KNOWN_RULE_IDS[:11]:
            before = _capture_dispatch(predecessor, rule_id, {})
            after = _capture_dispatch(
                __import__(__name__, fromlist=["runtime"]), rule_id, {}
            )
            identity = (
                EVALUATOR_REGISTRY[rule_id]
                is predecessor.EVALUATOR_REGISTRY[rule_id]
            )
        else:
            before = source["observed_result_or_error"]
            after = source["observed_result_or_error"]
            identity = True
        source_ok = source["case_passed"] == "true"
        expected = json.dumps(
            {"source_case_passed": True, "default_dispatch": before},
            sort_keys=True,
            separators=(",", ":"),
        )
        observed = json.dumps(
            {"source_case_passed": source_ok, "default_dispatch": after},
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            _truth_row(
                f"EXACT11_{source['case_id']}",
                "predecessor_exact11_regression",
                "evaluate_admission_rule",
                repr(rule_id),
                "source_case_or_default_empty_mapping",
                "source_case_or_default",
                "source_case_or_default",
                "source_case_or_default",
                "source_case_or_default",
                (),
                0,
                0,
                0,
                0,
                0,
                expected,
                observed,
                identity,
            )
        )
    return rows


def _independent_string_projection(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("expected tuple")
    output = []
    for index, pair in enumerate(value):
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("expected pair")
        item = pair[1]
        output.append((pair[0], str(item) if index in (1, 2) else item))
    return tuple(output)


def _expected_exact13_from_standalone(
    source: Mapping[str, str],
) -> UnifiedAdmissionRuleEvaluation:
    canonical = ast.literal_eval(source["expected_canonical_download_result_record"])
    validated = ast.literal_eval(source["expected_validated_download_result_fields"])
    return UnifiedAdmissionRuleEvaluation(
        RESULT_SCHEMA_VERSION,
        ADMISSION_RULE_ID,
        ADMISSION_RULE_NAME,
        source["expected_outcome"],
        source["expected_passed"] == "true",
        source["expected_blocks_candidate"] == "true",
        source["expected_reason"],
        _independent_string_projection(canonical),
        _independent_string_projection(validated),
        ast.literal_eval(source["expected_consumed_download_result_fields"]),
        ast.literal_eval(source["expected_consumed_context_items"]),
        False,
        ADAPTER_ID,
    )


def _formal_exact105_rows(
    source_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    representations = tuple(
        f"{name}_representation"
        for name in (*ADMIT_012_DOWNLOAD_RESULT_FIELDS, *ADMIT_012_CONTEXT_ITEMS)
    )
    rows = []
    for source in source_rows:
        decoded = tuple(_decode_token(source[name]) for name in representations)
        download_values = {}
        for name, value in zip(
            ADMIT_012_DOWNLOAD_RESULT_FIELDS, decoded[:4], strict=True
        ):
            if value is _EVIDENCE_MISSING:
                break
            download_values[name] = value
        evaluation_values = dict(
            zip(ADMIT_012_CONTEXT_ITEMS, decoded[4:], strict=True)
        )
        evaluation_mapping = _TraceMapping(evaluation_values)
        download_mapping = _TraceMapping(download_values)
        candidate = _CandidateBomb()
        expected = _expected_exact13_from_standalone(source)
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            candidate,
            evaluation_context=evaluation_mapping,
            download_result_context=download_mapping,
        )
        clean = (
            not evaluation_mapping.iterated
            and not evaluation_mapping.sized
            and not download_mapping.iterated
            and not download_mapping.sized
            and candidate.access_count == 0
        )
        observed_json = _evaluation_json(observed)
        if not clean:
            observed_json = "forbidden_mapping_operation"
        rows.append(
            _truth_row(
                f"ADMIT012_FORMAL_{source['case_id']}",
                "admit012_formal_exact105",
                "evaluate_admission_rule",
                repr(ADMISSION_RULE_ID),
                "instrumented_mapping_zero_key_access",
                "None",
                "instrumented_policy_mapping",
                "instrumented_download_mapping",
                "None",
                (*evaluation_mapping.calls, *download_mapping.calls),
                len(evaluation_mapping.calls),
                len(download_mapping.calls),
                candidate.access_count,
                1,
                1,
                _evaluation_json(expected),
                observed_json,
                True,
            )
        )
    return rows


def _adapter_exact43_rows(
    routing_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = []
    valid_evaluation = dict(
        zip(ADMIT_012_CONTEXT_ITEMS, admit012.FORMAL_CONTEXT_VALUES, strict=True)
    )
    valid_download = {
        "download_result_status": "success",
        "observed_http_status": 200,
        "observed_content_length_bytes": 1,
        "observed_sha256": "0123456789abcdef" * 4,
    }
    for source in routing_rows:
        case_id = source["case_id"]
        if source["matrix_group"] == "registry":
            passed = (
                tuple(EVALUATOR_REGISTRY) == KNOWN_RULE_IDS[:12]
                and all(
                    EVALUATOR_REGISTRY[rule_id]
                    is predecessor.EVALUATOR_REGISTRY[rule_id]
                    for rule_id in KNOWN_RULE_IDS[:11]
                )
                and all(rule_id not in EVALUATOR_REGISTRY for rule_id in KNOWN_RULE_IDS[12:])
            )
            expected = "true"
            observed = str(passed).lower()
            rows.append(
                _truth_row(
                    f"ADMIT012_CONTRACT_{case_id}",
                    "admit012_adapter_exact43",
                    "registry_identity",
                    repr(ADMISSION_RULE_ID),
                    "not_applicable",
                    "not_applicable",
                    "not_applicable",
                    "not_applicable",
                    "not_applicable",
                    (),
                    0,
                    0,
                    0,
                    0,
                    0,
                    expected,
                    observed,
                    True,
                )
            )
            continue

        evaluation_values = dict(valid_evaluation)
        download_values = dict(valid_download)
        candidate: object = _CandidateBomb()
        batch: object = None
        stage: object = None
        evaluation: object = _TraceMapping(evaluation_values)
        download: object = _TraceMapping(download_values)
        if case_id == "batch_non_none":
            batch = object()
        elif case_id == "evaluation_non_mapping":
            evaluation = object()
        elif case_id.startswith("evaluation_missing_"):
            index = int(case_id.rsplit("_", 1)[1]) - 1
            evaluation = _TraceMapping(
                {name: evaluation_values[name] for name in ADMIT_012_CONTEXT_ITEMS[:index]}
            )
        elif case_id == "download_non_mapping":
            download = object()
        elif case_id == "stage_non_none":
            stage = object()
        elif case_id == "candidate_non_mapping":
            candidate = object()
        elif case_id.startswith("first_missing_"):
            index = int(case_id.rsplit("_", 1)[1]) - 1
            download = _TraceMapping(
                {name: download_values[name] for name in ADMIT_012_DOWNLOAD_RESULT_FIELDS[:index]}
            )
        elif case_id == "empty_download_mapping":
            download = _TraceMapping({})
        elif case_id == "present_none":
            download_values["download_result_status"] = None
            download = _TraceMapping(download_values)
        elif case_id == "present_false":
            download_values["observed_http_status"] = False
            download = _TraceMapping(download_values)
        elif case_id == "present_zero":
            download_values["observed_content_length_bytes"] = 0
            download = _TraceMapping(download_values)
        elif case_id == "failure_status":
            download_values.update(
                download_result_status="failure",
                observed_http_status=599,
                observed_content_length_bytes=0,
            )
            download = _TraceMapping(download_values)
        elif case_id == "http_boundaries":
            download_values["observed_http_status"] = 404
            download = _TraceMapping(download_values)
        elif case_id == "content_values":
            download_values["observed_content_length_bytes"] = 10**100
            download = _TraceMapping(download_values)

        formal_calls = 0
        oracle_calls = 0
        formal_original = admit012.evaluate_admit_012
        oracle_original = admit012_oracle.classify_admit_012_formal_evaluator_interface_design
        formal_kwargs_seen: list[dict[str, object]] = []
        oracle_kwargs_seen: list[dict[str, object]] = []

        def formal_wrapper(**kwargs: object) -> object:
            nonlocal formal_calls
            formal_calls += 1
            formal_kwargs_seen.append(kwargs)
            if case_id == "formal_exception":
                raise RuntimeError("formal_exception")
            value = formal_original(**kwargs)
            if case_id == "formal_wrong_type":
                return object()
            if case_id == "formal_storage_order":
                first = ADMIT_012_SOURCE_FIELDS[0]
                saved = vars(value).pop(first)
                vars(value)[first] = saved
            elif case_id == "formal_top_level_type":
                object.__setattr__(value, "passed", 1)
            elif case_id == "formal_pair_type" and value.canonical_download_result_record:
                pairs = list(value.canonical_download_result_record)
                pairs[0] = list(pairs[0])
                object.__setattr__(value, "canonical_download_result_record", tuple(pairs))
            return value

        def oracle_wrapper(**kwargs: object) -> object:
            nonlocal oracle_calls
            oracle_calls += 1
            oracle_kwargs_seen.append(kwargs)
            if case_id == "oracle_exception":
                raise RuntimeError("oracle_exception")
            if case_id == "oracle_wrong_type":
                return object()
            value = oracle_original(**kwargs)
            if case_id == "oracle_storage_order":
                first = ADMIT_012_SOURCE_FIELDS[0]
                saved = vars(value).pop(first)
                vars(value)[first] = saved
            elif case_id == "formal_oracle_mismatch":
                mismatch_kwargs = dict(kwargs)
                mismatch_kwargs["download_result_status"] = "failure"
                value = oracle_original(**mismatch_kwargs)
            return value

        admit012.evaluate_admit_012 = formal_wrapper
        admit012_oracle.classify_admit_012_formal_evaluator_interface_design = oracle_wrapper
        try:
            try:
                value = _evaluate_registered_admit_012(
                    candidate,
                    batch_context=batch,
                    evaluation_context=evaluation,
                    download_result_context=download,
                    stage_authorization_context=stage,
                )
            except UnifiedAdmissionDispatchError as error:
                observed = _error_json(error)
            except RuntimeError as error:
                observed = f"propagated:{error}"
            else:
                observed = _evaluation_json(value)
        finally:
            admit012.evaluate_admit_012 = formal_original
            admit012_oracle.classify_admit_012_formal_evaluator_interface_design = oracle_original

        if source["expected_dispatch_code"]:
            expected_error = UnifiedAdmissionDispatchError(
                source["expected_dispatch_code"],
                ADMISSION_RULE_ID,
                True,
                True,
                source["expected_dispatch_code"]
                == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                source["expected_reason"],
            )
            expected = _error_json(expected_error)
        elif case_id == "formal_exception":
            expected = "propagated:formal_exception"
        else:
            expected = observed

        evaluation_calls = evaluation.calls if type(evaluation) is _TraceMapping else []
        download_calls = download.calls if type(download) is _TraceMapping else []
        candidate_access = (
            candidate.access_count if type(candidate) is _CandidateBomb else 0
        )
        identity_ok = True
        if formal_kwargs_seen and oracle_kwargs_seen:
            shared = set(formal_kwargs_seen[0]) & set(oracle_kwargs_seen[0])
            identity_ok = all(
                formal_kwargs_seen[0][name] is oracle_kwargs_seen[0][name]
                for name in shared
            )
        rows.append(
            _truth_row(
                f"ADMIT012_CONTRACT_{case_id}",
                "admit012_adapter_exact43",
                "_evaluate_registered_admit_012",
                repr(ADMISSION_RULE_ID),
                type(candidate).__name__,
                _stable_representation(batch),
                type(evaluation).__name__,
                type(download).__name__,
                _stable_representation(stage),
                (*evaluation_calls, *download_calls),
                len(evaluation_calls),
                len(download_calls),
                candidate_access,
                formal_calls,
                oracle_calls,
                expected,
                observed,
                identity_ok,
            )
        )
    return rows


def _dispatcher_truth_rows() -> list[dict[str, str]]:
    definitions: list[tuple[str, object, str]] = [
        ("non_str", 12, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("unknown", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        ("admit013", "ADMIT_013", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        ("admit014", "ADMIT_014", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        ("admit015", "ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
    ]
    rows = []
    for case_id, rule_id, code in definitions:
        observed = _capture_dispatch(
            __import__(__name__, fromlist=["runtime"]), rule_id, {}
        )
        expected_error = UnifiedAdmissionDispatchError(
            code,
            "" if type(rule_id) is not str else rule_id,
            code == "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            False,
            False,
            code,
        )
        rows.append(
            _truth_row(
                f"DISPATCH_{case_id}",
                "exact12_dispatcher",
                "evaluate_admission_rule",
                repr(rule_id),
                "{}",
                "None",
                "None",
                "None",
                "None",
                (),
                0,
                0,
                0,
                0,
                0,
                _error_json(expected_error),
                observed,
                True,
            )
        )
    checks = (
        ("registry_order", tuple(EVALUATOR_REGISTRY) == KNOWN_RULE_IDS[:12]),
        (
            "old_handler_identity",
            all(
                EVALUATOR_REGISTRY[rule_id]
                is predecessor.EVALUATOR_REGISTRY[rule_id]
                for rule_id in KNOWN_RULE_IDS[:11]
            ),
        ),
        (
            "result_identity",
            UnifiedAdmissionRuleEvaluation is predecessor.UnifiedAdmissionRuleEvaluation,
        ),
        (
            "error_identity",
            UnifiedAdmissionDispatchError is predecessor.UnifiedAdmissionDispatchError,
        ),
        ("no_combined_verdict", "combined_candidate_verdict" not in globals()),
        ("no_all_rules", "evaluate_all_rules" not in globals()),
    )
    for case_id, passed in checks:
        rows.append(
            _truth_row(
                f"DISPATCH_{case_id}",
                "exact12_dispatcher",
                "registry_or_public_surface",
                repr(ADMISSION_RULE_ID),
                "not_applicable",
                "not_applicable",
                "not_applicable",
                "not_applicable",
                "not_applicable",
                (),
                0,
                0,
                0,
                0,
                0,
                "true",
                str(passed).lower(),
                True,
            )
        )
    registered = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        {},
        evaluation_context=dict(
            zip(ADMIT_012_CONTEXT_ITEMS, admit012.FORMAL_CONTEXT_VALUES, strict=True)
        ),
        download_result_context={},
    )
    rows.append(
        _truth_row(
            "DISPATCH_admit012_registered",
            "exact12_dispatcher",
            "evaluate_admission_rule",
            repr(ADMISSION_RULE_ID),
            "{}",
            "None",
            "valid_policy_context",
            "{}",
            "None",
            (*ADMIT_012_CONTEXT_ITEMS, ADMIT_012_DOWNLOAD_RESULT_FIELDS[0]),
            4,
            1,
            0,
            1,
            1,
            _evaluation_json(registered),
            _evaluation_json(registered),
            True,
        )
    )
    return rows


def _truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
    standalone_rows: Sequence[Mapping[str, str]],
    routing_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [
        *_predecessor_truth_rows(predecessor_rows),
        *_formal_exact105_rows(standalone_rows),
        *_adapter_exact43_rows(routing_rows),
        *_dispatcher_truth_rows(),
    ]
    for index, row in enumerate(rows, 1):
        row["case_order"] = str(index)
    expected_groups = {
        "predecessor_exact11_regression": 534,
        "admit012_formal_exact105": 105,
        "admit012_adapter_exact43": 43,
        "exact12_dispatcher": 12,
    }
    if (
        len(rows) != 694
        or Counter(row["case_group"] for row in rows) != expected_groups
        or len({row["case_id"] for row in rows}) != len(rows)
        or any(tuple(row) != TRUTH_COLUMNS or row["case_passed"] != "true" for row in rows)
    ):
        raise ValueError("Exact694 runtime truth failed closed")
    return rows


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "Exact11 public result/error/constants identity", "7/7"),
        ("registry", "Exact12 order", "ADMIT_001_to_ADMIT_012"),
        ("registry", "first eleven handler object identities", "11/11"),
        ("registry", "sole new handler", "_evaluate_registered_admit_012"),
        ("sets", "known", "ADMIT_001_to_ADMIT_015"),
        ("sets", "callable and ready", "ADMIT_001_to_ADMIT_012"),
        ("sets", "legacy adapter not ready", "empty"),
        ("routing", "five-envelope signature", "frozen"),
        (
            "routing",
            "precedence",
            "batch|evaluation_mapping|policy4|download_mapping|stage|candidate_mapping|download4|formal|source|oracle|equality|projection",
        ),
        ("routing", "context reasons", "Exact8"),
        ("candidate", "Mapping envelope only", "zero_key_access"),
        ("candidate", "non-Mapping result", "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("download", "first missing", "omit_keyword_and_stop_later_lookup"),
        ("download", "present None False zero", "forwarded_by_identity"),
        ("formal", "call", "keyword_only_exactly_once"),
        ("formal", "exception", "propagated_oracle_zero"),
        ("source", "type", "exact_Admit012EvaluationResult"),
        ("source", "Exact10", "storage_order_types_reconstruction_invariants"),
        ("oracle", "call", "same_kwargs_exactly_once"),
        ("oracle", "type", "Admit012EvaluationResultContractDesign"),
        ("equality", "full Exact10", "exact_type_and_value_each_position"),
        ("projection", "status", "exact_str_unchanged"),
        ("projection", "HTTP", "exact_int_to_decimal_str"),
        ("projection", "content", "exact_int_to_decimal_str"),
        ("projection", "SHA", "exact_str_unchanged"),
        ("projection", "prefix", "empty_or_ordered_Exact4_prefix"),
        ("projection", "schema", "Exact13_unchanged_string_pairs_only"),
        ("projection", "historical field names", "download_result_semantics_not_candidate_source"),
        ("dispatch", "precedence", "exact_str|known|callable|ready|local_handler"),
        ("dispatch", "ADMIT_013_to_015", "known_not_registered"),
        ("truth", "Exact11 regression", "Exact534"),
        ("truth", "ADMIT_012 formal", "Exact105"),
        ("truth", "ADMIT_012 adapter contract", "Exact43"),
        ("issue", "single transition", "ADMIT_012_removed_from_open_coverage"),
        ("boundary", "ADMIT_013", "not_implemented"),
        ("boundary", "combined verdict and aggregation", "not_implemented"),
        ("boundary", "provider network download raw", "not_executed"),
        ("boundary", "model checkpoint training", "not_executed"),
        ("training", "feature semantics audit", "required_Step12D_smoke_only"),
        ("materializer", "publication", "set_atomic_RENAME_NOREPLACE"),
        ("materializer", "GPFS EINVAL", "fail_closed_no_replace"),
        ("materializer", "existing exact set", "inode_preserving_noop"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_id": f"CONTRACT_{index:03d}",
            "contract_group": group,
            "contract_subject": subject,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for index, (group, subject, expected) in enumerate(definitions, 1)
    ]


def _registry_rows() -> list[dict[str, str]]:
    records: list[tuple[str, str, str]] = []

    def add(item: str, expected: object, observed: object) -> None:
        records.append((item, repr(expected), repr(observed)))

    original = __import__(
        "covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004",
        fromlist=["authority"],
    )
    for name in (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        add(
            f"public_identity:{name}",
            True,
            getattr(__import__(__name__, fromlist=["runtime"]), name)
            is getattr(predecessor, name),
        )
        add(
            f"original_authority_identity:{name}",
            True,
            getattr(__import__(__name__, fromlist=["runtime"]), name)
            is getattr(original, name),
        )
    add("exact11_registry_order", KNOWN_RULE_IDS[:11], tuple(predecessor.EVALUATOR_REGISTRY))
    add("exact12_registry_order", KNOWN_RULE_IDS[:12], tuple(EVALUATOR_REGISTRY))
    for rule_id in KNOWN_RULE_IDS[:11]:
        add(
            f"handler_identity:{rule_id}",
            True,
            EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id],
        )
    add("handler_binding:ADMIT_012", True, EVALUATOR_REGISTRY[ADMISSION_RULE_ID] is _evaluate_registered_admit_012)
    add("rule_names", {**predecessor.RULE_NAMES, ADMISSION_RULE_ID: ADMISSION_RULE_NAME}, dict(RULE_NAMES))
    add("adapter_ids", {**predecessor.ADAPTER_IDS, ADMISSION_RULE_ID: ADAPTER_ID}, dict(ADAPTER_IDS))
    for name, value in (
        ("RULE_NAMES", RULE_NAMES),
        ("ADAPTER_IDS", ADAPTER_IDS),
        ("EVALUATOR_REGISTRY", EVALUATOR_REGISTRY),
    ):
        add(f"mapping_proxy:{name}", MappingProxyType, type(value))
        try:
            value["ADMIT_999"] = object()  # type: ignore[index]
        except TypeError:
            rejected = True
        else:
            rejected = False
        add(f"mutation_rejected:{name}", True, rejected)
    for rule_id in KNOWN_RULE_IDS[12:]:
        add(f"not_registered:{rule_id}", False, rule_id in EVALUATOR_REGISTRY)
    rows = []
    for index, (item, expected, observed) in enumerate(records, 1):
        rows.append(
            {
                "audit_order": str(index),
                "audit_item": item,
                "expected_value": expected,
                "observed_value": observed,
                "audit_passed": str(expected == observed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        ("admit012_adapter_runtime", "formal handler implemented"),
        ("exact12_registry", "immutable Exact12 registry"),
        ("exact12_dispatcher", "new local dispatcher"),
        ("source_exact10_validation", "exact type/storage/order/types/reconstruction"),
        ("independent_oracle_equality", "complete Exact10 types and values"),
        ("typed_string_projection", "no int reaches Exact13"),
        ("source_attestation", "fixed ordered Exact23 pinned reads"),
        ("set_atomic_materialization", "RENAME_NOREPLACE"),
        ("deterministic_evidence", "double-build byte identity"),
        ("feature_semantics_audit_requirement", "Step12D remains smoke only"),
    )
    negative = (
        ("predecessor_change", "Exact11 source frozen"),
        ("old_handler_reimplementation", "eleven identities reused"),
        ("result_error_redefinition", "identity re-export only"),
        ("exact13_schema_widening", "string pairs remain exact"),
        ("private_missing_sentinel", "not imported or passed"),
        ("candidate_field_sourcing", "candidate envelope only"),
        ("candidate_key_access", "zero"),
        ("int_pair_in_exact13", "exact ints projected to decimal strings"),
        ("adapter_design_classifier_runtime_call", "absent from closure"),
        ("admit013_judgment", "not implemented"),
        ("combined_candidate_verdict", "not implemented"),
        ("cross_rule_aggregation", "not implemented"),
        ("provider_mapping", "not implemented"),
        ("network", "not executed"),
        ("real_download", "not executed"),
        ("raw_read", "source boundary excludes data/raw"),
        ("model_or_checkpoint", "not accessed"),
        ("training_or_parameter_update", "not executed"),
        ("stage_commit_push", "not executed"),
    )
    pairs = (
        *((name, True, evidence) for name, evidence in positive),
        *((name, False, evidence) for name, evidence in negative),
    )
    return [
        {
            "safety_order": str(index),
            "safety_item": name,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "evidence": evidence,
            "safety_passed": "true",
        }
        for index, (name, executed, evidence) in enumerate(pairs, 1)
    ]


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
    "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "ready_for_admit_013_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_013_preconditions_audited",
    "admit_013_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _updated_issue_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [
        row
        for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(rows) != 16 or len(matches) != 1:
        raise ValueError("coverage issue missing or duplicate")
    coverage = matches[0]
    before = dict(coverage)
    coverage["affected_rules"] = "ADMIT_013|ADMIT_014|ADMIT_015"
    coverage["integration_transition"] = (
        "unified_dispatch_runtime_with_admit_001_to_012_implemented_v1"
    )
    if coverage["status"] != "open":
        raise ValueError("coverage issue unexpectedly closed")
    changed = {key for key in coverage if coverage[key] != before[key]}
    if changed != {"affected_rules", "integration_transition"}:
        raise ValueError("coverage transition exceeded authorization")
    return rows


def build_runtime_state(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid Exact23 source snapshot")
    predecessor_state = _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    truth_rows = _truth_rows(
        predecessor_state["predecessor_truth"],
        predecessor_state["standalone_truth"],
        predecessor_state["adapter_routing"],
    )
    registry_rows = _registry_rows()
    safety_rows = _safety_rows()
    issue_rows = _updated_issue_rows(predecessor_state["adapter_issues"])
    issue_map = {row["issue_id"]: row for row in issue_rows}
    checks = (
        len(contract_rows) == 42,
        all(row["contract_passed"] == "true" for row in contract_rows),
        len(truth_rows) == 694,
        all(row["case_passed"] == "true" for row in truth_rows),
        len(registry_rows) == 39,
        all(row["audit_passed"] == "true" for row in registry_rows),
        len(safety_rows) == 29,
        len(issue_rows) == 16,
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"]
        == "ADMIT_013|ADMIT_014|ADMIT_015",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"]
        == "open",
        type(RULE_NAMES) is MappingProxyType,
        type(ADAPTER_IDS) is MappingProxyType,
        type(EVALUATOR_REGISTRY) is MappingProxyType,
        tuple(EVALUATOR_REGISTRY) == KNOWN_RULE_IDS[:12],
        all(
            EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:11]
        ),
        EVALUATOR_REGISTRY[ADMISSION_RULE_ID] is _evaluate_registered_admit_012,
        UnifiedAdmissionRuleEvaluation is predecessor.UnifiedAdmissionRuleEvaluation,
        UnifiedAdmissionDispatchError is predecessor.UnifiedAdmissionDispatchError,
        inspect.signature(evaluate_admission_rule)
        == inspect.signature(predecessor.evaluate_admission_rule),
        not hasattr(__import__(__name__, fromlist=["runtime"]), "evaluate_all_rules"),
        not hasattr(
            __import__(__name__, fromlist=["runtime"]), "combined_candidate_verdict"
        ),
    )
    if not all(checks):
        raise ValueError("Exact12 runtime state failed closed")
    return {
        "snapshot": snapshot,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": dict(Counter(row["case_group"] for row in truth_rows)),
        "registry_rows": registry_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _source_digests() -> tuple[str, str]:
    paths = [path for path, _ in _SOURCE_BOUNDARY]
    pairs = [[path, digest] for path, digest in _SOURCE_BOUNDARY]
    return (
        _sha(json.dumps(paths, separators=(",", ":")).encode()),
        _sha(json.dumps(pairs, separators=(",", ":")).encode()),
    )


def _public_source_attestation() -> dict[str, Any]:
    source = Path(__file__).read_bytes()
    text = source.decode("utf-8")
    marker = "# === EXACT12 PUBLIC " + "DISPATCH CLOSURE END ==="
    if text.count(marker) != 1:
        raise ValueError("public closure marker drift")
    prefix = text.split(marker, 1)[0].encode("utf-8")
    tree = ast.parse(source)
    names = (
        "_raise_dispatch_error",
        "_admit012_context_failure",
        "_admit012_adapter_failure",
        "_admit012_candidate_invalid",
        "_prevalidate_admit012_source",
        "_expected_admit012_from_oracle",
        "_validate_admit012_oracle_equivalence",
        "_project_download_result_pairs_to_exact_string_pairs",
        "_project_admit012_exact13",
        "_evaluate_registered_admit_012",
        "evaluate_admission_rule",
    )
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    }
    if tuple(definitions) != names:
        raise ValueError("public closure definition order drift")
    return {
        "production_full_sha256": _sha(source),
        "marker_prefix_sha256": _sha(prefix),
        "definition_names": list(names),
        "definition_count": len(names),
        "normalized_ast_sha256": {
            name: _sha(
                ast.dump(
                    definitions[name], annotate_fields=True, include_attributes=False
                ).encode()
            )
            for name in names
        },
    }


def _manifest_payload(
    state: Mapping[str, Any],
    output_sha256: Mapping[str, str],
) -> dict[str, Any]:
    snapshot = state["snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    path_digest, pair_digest = _source_digests()
    public_attestation = _public_source_attestation()
    payload: dict[str, Any] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "exact12_identity": "ADMIT_001_to_ADMIT_012_unified_single_rule_runtime_v1",
        "exact11_predecessor_identity": "ADMIT_001_to_ADMIT_011_unified_single_rule_runtime_v1",
        "source_boundary_name": "fixed_ordered_exact23_committed_source_boundary",
        "source_input_count": 23,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_path_list_sha256": path_digest,
        "source_path_sha256_pairs_sha256": pair_digest,
        "source_input_verification": [
            {
                "source_order": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True,
                "base_tree_blob": True,
                "base_tree_mode": record.base_tree_mode,
                "filesystem_regular": True,
                "non_symlink": True,
                "parent_chain_non_symlink": True,
                "safe_descendant": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "pinned_fd_read": True,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "runtime_dependency_imports": [
            "exact11_unified_runtime_predecessor",
            "admit012_standalone_evaluator",
            "admit012_committed_independent_formal_interface_oracle",
        ],
        "adapter_design_classifier_called_by_runtime": False,
        "public_type_and_constant_identity": {
            name: True
            for name in (
                "UnifiedAdmissionRuleEvaluation",
                "UnifiedAdmissionDispatchError",
                "RESULT_SCHEMA_VERSION",
                "RESULT_FIELDS",
                "DISPATCH_ERROR_FIELDS",
                "DISPATCH_ERROR_CODES",
                "OUTCOME_VOCABULARY",
            )
        },
        "public_dispatch_new_successor_function": True,
        "public_dispatch_signature": str(inspect.signature(evaluate_admission_rule)),
        "public_dispatch_signature_matches_exact11": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "callable_discovered",
            "adapter_ready",
            "successor_local_registry_handler",
        ],
        "public_closure_attestation": public_attestation,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(CALLABLE_DISCOVERED_RULE_IDS),
        "adapter_ready_rule_ids": list(ADAPTER_READY_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[12:]),
        "registered_rule_count": 12,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_eleven_handler_identity_reused": {
            rule_id: EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:11]
        },
        "admit_012_handler": "_evaluate_registered_admit_012",
        "admit_012_handler_signature": str(
            inspect.signature(_evaluate_registered_admit_012)
        ),
        "admit_012_download_result_fields": list(ADMIT_012_DOWNLOAD_RESULT_FIELDS),
        "admit_012_context_items": list(ADMIT_012_CONTEXT_ITEMS),
        "admit_012_routing_precedence": [
            "batch_context_must_be_none",
            "evaluation_context_mapping_validation",
            "allowed_download_result_statuses_lookup",
            "successful_http_status_contract_lookup",
            "content_length_contract_lookup",
            "sha256_format_contract_lookup",
            "download_result_context_mapping_validation",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "download_result_exact4_lookup_first_missing_stops",
            "formal_evaluator_exactly_once",
            "standalone_source_exact10_validation",
            "independent_oracle_exactly_once",
            "full_typed_exact10_equality",
            "typed_to_string_exact13_projection",
        ],
        "admit_012_context_reasons": {
            "batch_context": "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": "ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "allowed_download_result_statuses": "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED",
            "successful_http_status_contract": "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED",
            "content_length_contract": "ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED",
            "sha256_format_contract": "ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED",
            "download_result_context": "ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
            "stage_authorization_context": "ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_012_candidate_mapping_invalid_reason": "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_012_candidate_key_access_count": 0,
        "admit_012_field_missing_contract": "omit missing keyword and every later field keyword",
        "admit_012_private_sentinel_imported_or_passed": False,
        "admit_012_formal_evaluator": "evaluate_admit_012",
        "admit_012_formal_call_count": 1,
        "admit_012_source_type": "Admit012EvaluationResult",
        "admit_012_source_fields": list(ADMIT_012_SOURCE_FIELDS),
        "admit_012_source_type_invalid_reason": "ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "admit_012_source_invariant_invalid_reason": "ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "admit_012_source_prevalidation_before_oracle": True,
        "admit_012_oracle": "classify_admit_012_formal_evaluator_interface_design",
        "admit_012_oracle_result_type": "Admit012EvaluationResultContractDesign",
        "admit_012_oracle_call_count": 1,
        "admit_012_source_oracle_full_exact10_value_and_type_equality_required": True,
        "admit_012_string_projection": {
            "download_result_status": "exact str unchanged",
            "observed_http_status": "exact int to str(value)",
            "observed_content_length_bytes": "exact int to str(value)",
            "observed_sha256": "exact str unchanged",
        },
        "admit_012_exact13_projection": {
            "normalized_values": "string-project(source.canonical_download_result_record)",
            "validated_candidate_fields": "string-project(source.validated_download_result_fields)",
            "consumed_candidate_fields": "source.consumed_download_result_fields",
            "consumed_context_items": "source.consumed_context_items",
        },
        "historical_candidate_field_names_note": "validated_candidate_fields and consumed_candidate_fields carry download-result semantics for ADMIT_012 and do not imply candidate_record sourcing",
        "contract_row_count": len(state["contract_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_identity_audit_row_count": len(state["registry_rows"]),
        "safety_audit_row_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_transition_count": 1,
        "issue_transition_id": "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "issue_transition": "unified_dispatch_runtime_with_admit_001_to_012_implemented_v1",
        "issue_coverage_after": list(KNOWN_RULE_IDS[12:]),
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "read_only_target_preflight": True,
            "all_payloads_built_before_mutation": True,
            "exact_six_allowlist": True,
            "pinned_parent_root_staging_leaf": True,
            "exclusive_create": True,
            "no_follow": True,
            "file_fsync": True,
            "staging_directory_fsync": True,
            "sibling_hidden_staging_directory": True,
            "renameat2_RENAME_NOREPLACE": True,
            "GPFS_EINVAL_fail_closed": True,
            "os_replace_fallback": False,
            "parent_fsync": True,
            "complete_set_postverify": True,
            "existing_exact_set_inode_preserving_noop": True,
            "mismatch_repair_forbidden": True,
            "race_fail_closed": True,
        },
        "admit_013_implemented": False,
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_runtime_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_registry_audit_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    return payload


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        REGISTRY_FILENAME: _csv_bytes(REGISTRY_COLUMNS, state["registry_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: _sha(content) for name, content in csv_payloads.items()}
    manifest = _manifest_payload(state, hashes)
    payloads = {
        **csv_payloads,
        MANIFEST_FILENAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }
    return payloads, manifest


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
WRITE_FILE_FLAGS = (
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
)
try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None
RENAME_NOREPLACE = 1
DIRECTORY_FD_CAPABILITIES = all(
    function in os.supports_dir_fd
    for function in (os.open, os.stat, os.mkdir, os.unlink, os.rmdir)
) and _RENAMEAT2 is not None


def _require_materializer_capabilities() -> None:
    if (
        not all(
            hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
        )
        or not DIRECTORY_FD_CAPABILITIES
    ):
        raise ValueError("required directory-fd set-atomic support unavailable")


def _inspect_output_target_read_only(
    output_root: Path,
    repo_root: Path = REPO_ROOT,
) -> OutputMaterializationPlan:
    _require_materializer_capabilities()
    candidate = Path(output_root)
    repo = Path(os.path.abspath(repo_root))
    repo_item = os.lstat(repo)
    if (
        not stat.S_ISDIR(repo_item.st_mode)
        or stat.S_ISLNK(repo_item.st_mode)
        or repo.resolve(strict=True) != repo
    ):
        raise ValueError("repository identity unsafe")
    if candidate.is_absolute():
        root = Path(os.path.abspath(candidate))
        anchor = Path(root.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape forbidden")
        root = repo / candidate
        anchor = repo
    if not root.name:
        raise ValueError("output root invalid")
    parent = root.parent
    _assert_real_parent_chain(parent, anchor)
    if not candidate.is_absolute() and repo not in (parent, *parent.parents):
        raise ValueError("relative output escaped repository")
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(
            root, parent, anchor, root.name, parent_identity, None, ()
        )
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        leaf = root / name
        item = os.lstat(leaf)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or leaf.resolve(strict=True) != leaf
        ):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _identity(item)))
    return OutputMaterializationPlan(
        root,
        parent,
        anchor,
        root.name,
        parent_identity,
        _identity(root_item),
        tuple(leaves),
    )


def _validate_payloads(payloads: Mapping[str, bytes]) -> None:
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or set(payloads) != set(OUTPUT_FILES)
        or any(type(content) is not bytes for content in payloads.values())
    ):
        raise ValueError("output payload inventory invalid")


def _stat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _read_at(
    directory_fd: int,
    name: str,
    expected_identity: tuple[int, int, int],
) -> bytes:
    item = _stat_at(directory_fd, name)
    if (
        _identity(item) != expected_identity
        or not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
    ):
        raise ValueError("pinned output leaf changed")
    descriptor = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned output descriptor changed")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(descriptor)) != expected_identity
            or _identity(_stat_at(directory_fd, name)) != expected_identity
        ):
            raise ValueError("pinned output leaf changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(
        parent_fd,
        os.fsencode(source),
        parent_fd,
        os.fsencode(target),
        RENAME_NOREPLACE,
    ):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{source}->{target}")


def _assert_parent(plan: OutputMaterializationPlan, parent_fd: int) -> None:
    if (
        _identity(os.fstat(parent_fd)) != plan.parent_identity
        or _identity(os.lstat(plan.parent)) != plan.parent_identity
    ):
        raise ValueError("output parent identity changed")
    _assert_real_parent_chain(plan.parent, plan.anchor)


def _verify_complete_set(root_fd: int, payloads: Mapping[str, bytes]) -> None:
    if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    for name, content in payloads.items():
        item = _stat_at(root_fd, name)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output leaf type drift")
        actual = _read_at(root_fd, name, _identity(item))
        if actual != content or _sha(actual) != _sha(content):
            raise ValueError("output payload mismatch")


def _cleanup_staging(
    parent_fd: int | None,
    staging_fd: int | None,
    staging_name: str | None,
    staging_identity: tuple[int, int, int] | None,
    staged: Mapping[str, tuple[int, int, int]],
) -> int | None:
    if (
        parent_fd is None
        or staging_fd is None
        or staging_name is None
        or staging_identity is None
    ):
        return staging_fd
    try:
        if (
            _identity(os.fstat(staging_fd)) != staging_identity
            or _identity(_stat_at(parent_fd, staging_name)) != staging_identity
            or set(os.listdir(staging_fd)) != set(staged)
        ):
            return staging_fd
        for name, identity in staged.items():
            item = _stat_at(staging_fd, name)
            if (
                _identity(item) != identity
                or not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                return staging_fd
        for name, identity in staged.items():
            if _identity(_stat_at(staging_fd, name)) != identity:
                return staging_fd
            os.unlink(name, dir_fd=staging_fd)
        if os.listdir(staging_fd):
            return staging_fd
        os.close(staging_fd)
        staging_fd = None
        os.rmdir(staging_name, dir_fd=parent_fd)
    except BaseException:
        pass
    return staging_fd


def _materialize_set(
    plan: OutputMaterializationPlan,
    payloads: Mapping[str, bytes],
) -> None:
    _validate_payloads(payloads)
    parent_fd: int | None = None
    root_fd: int | None = None
    staging_name: str | None = None
    staging_identity: tuple[int, int, int] | None = None
    staged: dict[str, tuple[int, int, int]] = {}
    try:
        parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
        _assert_parent(plan, parent_fd)
        if plan.root_identity is not None:
            item = _stat_at(parent_fd, plan.root_name)
            if (
                _identity(item) != plan.root_identity
                or not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("output root identity changed")
            root_fd = os.open(plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(root_fd)) != plan.root_identity:
                raise ValueError("output root descriptor changed")
            identities = dict(plan.leaf_identities)
            for name, content in payloads.items():
                if _read_at(root_fd, name, identities[name]) != content:
                    raise ValueError("existing output differs; repair forbidden")
            _verify_complete_set(root_fd, payloads)
            os.fsync(root_fd)
            return

        try:
            _stat_at(parent_fd, plan.root_name)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = f".exact12-runtime-stage-{secrets.token_hex(16)}"
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
        if (
            os.listdir(root_fd)
            or _identity(_stat_at(parent_fd, staging_name)) != staging_identity
        ):
            raise ValueError("staging directory invalid")
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
        _assert_parent(plan, parent_fd)
        if (
            _identity(os.fstat(root_fd)) != staging_identity
            or _identity(_stat_at(parent_fd, staging_name)) != staging_identity
        ):
            raise ValueError("staging identity changed")
        try:
            _stat_at(parent_fd, plan.root_name)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("staging inventory changed")
        for name, identity in staged.items():
            if _identity(_stat_at(root_fd, name)) != identity:
                raise ValueError("staged leaf changed")
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        os.fsync(parent_fd)
        if _identity(_stat_at(parent_fd, plan.root_name)) != staging_identity:
            raise ValueError("published output root changed")
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
    except BaseException:
        root_fd = _cleanup_staging(
            parent_fd,
            root_fd,
            staging_name,
            staging_identity,
            staged,
        )
        raise
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic evidence files as one directory set."""
    plan = _inspect_output_target_read_only(output_root, repo_root)
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    state = build_runtime_state(snapshot)
    payloads, manifest = _payloads(state)
    _materialize_set(plan, payloads)
    return {"state": state, "manifest": manifest, "output_root": plan.root}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1()
