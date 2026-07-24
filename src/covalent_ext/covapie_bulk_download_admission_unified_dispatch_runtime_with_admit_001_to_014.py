"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_014.

The committed Exact13 runtime remains authoritative for the shared Exact13
result, dispatch error, constants, and its thirteen handlers.  This successor
adds only the ADMIT_014 adapter, an immutable Exact14 registry, and a new
single-rule dispatcher.  Everything before the public-closure marker is pure
in-memory runtime code.  Evidence construction and publication live after it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from types import MappingProxyType
from typing import NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_014_rule_logic_interface as admit014,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate
    as admit014_oracle,
)


UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(
    f"ADMIT_{index:03d}" for index in range(1, 15)
)
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

ADMISSION_RULE_ID = "ADMIT_014"
ADMISSION_RULE_NAME = "current_gate_grants_no_download_permission"
ADAPTER_ID = "covapie_admit_014_unified_adapter_v1"
ADMIT_014_SOURCE_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_stage_authorization_record",
    "validated_stage_authorization_fields",
    "consumed_stage_authorization_fields",
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


def _admit014_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ADMISSION_RULE_ID,
        True,
        True,
        True,
        reason,
    )


def _admit014_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        ADMISSION_RULE_ID,
        True,
        True,
        False,
        reason,
    )


def _admit014_candidate_invalid() -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason="ADMIT_014_CANDIDATE_RECORD_MAPPING_INVALID",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_ID,
    )


def _prevalidate_admit014_source(
    source: object,
) -> admit014.Admit014EvaluationResult:
    if type(source) is not admit014.Admit014EvaluationResult:
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        )
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != ADMIT_014_SOURCE_FIELDS:
            raise ValueError("Exact9 storage/order drift")
        if (
            tuple(field.name for field in fields(admit014.Admit014EvaluationResult))
            != ADMIT_014_SOURCE_FIELDS
        ):
            raise ValueError("Exact9 dataclass order drift")
        values = tuple(
            getattr(source, name) for name in ADMIT_014_SOURCE_FIELDS
        )
        exact_types = (
            str,
            str,
            bool,
            bool,
            str,
            tuple,
            tuple,
            tuple,
            bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("Exact9 top-level type drift")
        reconstructed = admit014.Admit014EvaluationResult(*values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact9 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return source


def _expected_admit014_from_oracle(
    stage_authorization_context: object,
) -> admit014_oracle.Admit014EvaluationResultContractDesign:
    try:
        result = (
            admit014_oracle
            .classify_admit_014_formal_evaluator_interface_design(
                stage_authorization_context=stage_authorization_context
            )
        )
        result_type = admit014_oracle.Admit014EvaluationResultContractDesign
        if type(result) is not result_type:
            raise TypeError("oracle exact result type required")
        storage = vars(result)
        if type(storage) is not dict or tuple(storage) != ADMIT_014_SOURCE_FIELDS:
            raise ValueError("oracle Exact9 storage/order drift")
        if (
            tuple(field.name for field in fields(result_type))
            != ADMIT_014_SOURCE_FIELDS
        ):
            raise ValueError("oracle Exact9 dataclass order drift")
        values = tuple(
            getattr(result, name) for name in ADMIT_014_SOURCE_FIELDS
        )
        exact_types = (
            str,
            str,
            bool,
            bool,
            str,
            tuple,
            tuple,
            tuple,
            bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("oracle Exact9 top-level type drift")
        if (
            result_type(*values) != result
            or result.admission_rule_id != ADMISSION_RULE_ID
            or result.evaluator_io_used is not False
        ):
            raise ValueError("oracle Exact9 reconstruction/invariant drift")
    except Exception:
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return result


def _validate_admit014_oracle_equivalence(
    source: admit014.Admit014EvaluationResult,
    expected: admit014_oracle.Admit014EvaluationResultContractDesign,
) -> None:
    try:
        source_values = tuple(
            getattr(source, name) for name in ADMIT_014_SOURCE_FIELDS
        )
        expected_values = tuple(
            getattr(expected, name) for name in ADMIT_014_SOURCE_FIELDS
        )
    except AttributeError:
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if any(
        type(left) is not type(right) or left != right
        for left, right in zip(source_values, expected_values, strict=True)
    ):
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


def _project_stage_authorization_record_to_exact_string_pairs(
    canonical_record: object,
) -> tuple[tuple[str, str], ...]:
    if type(canonical_record) is not tuple:
        raise TypeError("canonical record requires exact tuple")
    if canonical_record == ():
        return ()
    if (
        len(canonical_record) != 1
        or type(canonical_record[0]) is not tuple
        or len(canonical_record[0]) != 2
        or type(canonical_record[0][0]) is not str
        or canonical_record[0][0] != "current_stage_download_authorized"
        or type(canonical_record[0][1]) is not bool
    ):
        raise TypeError("canonical stage authorization record drift")
    return (
        (
            "current_stage_download_authorized",
            "true" if canonical_record[0][1] else "false",
        ),
    )


def _project_admit014_exact13(
    source: admit014.Admit014EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=(
            _project_stage_authorization_record_to_exact_string_pairs(
                source.canonical_stage_authorization_record
            )
        ),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=source.consumed_stage_authorization_fields,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_ID,
    )


def _evaluate_registered_admit_014(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    if batch_context is not None:
        _admit014_context_failure("ADMIT_014_BATCH_CONTEXT_MUST_BE_NONE")
    if evaluation_context is not None:
        _admit014_context_failure(
            "ADMIT_014_EVALUATION_CONTEXT_MUST_BE_NONE"
        )
    if download_result_context is not None:
        _admit014_context_failure(
            "ADMIT_014_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
        )
    if not isinstance(candidate_record, Mapping):
        return _admit014_candidate_invalid()
    try:
        source = admit014.evaluate_admit_014(
            stage_authorization_context=stage_authorization_context
        )
    except Exception:
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    validated_source = _prevalidate_admit014_source(source)
    expected = _expected_admit014_from_oracle(stage_authorization_context)
    _validate_admit014_oracle_equivalence(validated_source, expected)
    try:
        return _project_admit014_exact13(validated_source)
    except Exception:
        _admit014_adapter_failure(
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


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
        "ADMIT_012": predecessor.EVALUATOR_REGISTRY["ADMIT_012"],
        "ADMIT_013": predecessor.EVALUATOR_REGISTRY["ADMIT_013"],
        "ADMIT_014": _evaluate_registered_admit_014,
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
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            admission_rule_id,
            False,
            False,
            False,
        )
    if admission_rule_id not in CALLABLE_DISCOVERED_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            admission_rule_id,
            True,
            False,
            False,
        )
    if admission_rule_id not in ADAPTER_READY_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            admission_rule_id,
            True,
            True,
            False,
        )
    handler = EVALUATOR_REGISTRY[admission_rule_id]
    return handler(
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


# === CovaPIE ADMIT_001 TO ADMIT_014 PUBLIC RUNTIME CLOSURE END ===


import ast
import csv
import ctypes
import hashlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate
    as admit014_adapter_design,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_014 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_014_v1"
)
EXPECTED_BASE_COMMIT = "ce98b5542eea5ab4f81c0fc93b10147df5568735"
EXPECTED_BASE_PARENT = "44b4306adfa42ef3587f87d08a4f66ed60101fa7"
EXPECTED_BASE_TREE = "26402d634ee1edbcb2de4a5c099452e8da8ec06d"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_014 unified adapter contract v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_014_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_admit_015_formal_evaluator_interface_preconditions_v1"
)
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE = False
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; "
    "artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PUBLIC_MARKER = (
    "# === CovaPIE ADMIT_001 TO ADMIT_014 PUBLIC "
    "RUNTIME CLOSURE END ==="
)
PUBLIC_DEFINITIONS = (
    "_raise_dispatch_error",
    "_admit014_context_failure",
    "_admit014_adapter_failure",
    "_admit014_candidate_invalid",
    "_prevalidate_admit014_source",
    "_expected_admit014_from_oracle",
    "_validate_admit014_oracle_equivalence",
    "_project_stage_authorization_record_to_exact_string_pairs",
    "_project_admit014_exact13",
    "_evaluate_registered_admit_014",
    "evaluate_admission_rule",
)

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py",
        "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_runtime_contract.csv",
        "035effd65ca65ed1442bb7a29c03986390209f6d129d2ae078e223101c6a6144",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_dispatch_truth_matrix.csv",
        "78e04c469fe5a6102ec07293b1b2e59e04848b54f251abe28e2d21ba1cbd05bb",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_registry_and_identity_audit.csv",
        "6700c9360f1447f79a5180d74e1b00d5098547aca3534b5192eab2b8bdb93295",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_runtime_safety_audit.csv",
        "4b0c11cb59193bdfea9b7011e63ad4262cbbff2c1d57fd276de064997c28d8b4",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv",
        "477b4192579d3f64dac5bd0cc61c1a378b2f28c3355251e344b79999801a5d69",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_runtime_manifest.json",
        "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate.py",
        "81405268a90c4757a7e40b0fd094c48110a99a4551df4575d91b9113cc3d5e5d",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_unified_adapter_contract.csv",
        "cdcd5d3ae1f3f65d7faa3ff50e61b37b0fcb9133395868885253f487764aeafc",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_stage_authorization_projection_and_context_routing_matrix.csv",
        "0d423c4ad785ca92c14e8d3a4881649d7290a6220814e29ab0ed6d7737e653e4",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_unified_result_projection_truth_matrix.csv",
        "9c8e08358f806b3cb9172f460fe49da47d06f1ba028cc4b2a1df1ca8d0d5ff53",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_unified_adapter_safety_audit.csv",
        "d8530eeb4ecfacd8d26e1d1054112bd927e94ab204cf6eec4c7ab91c76bf6c4b",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_unified_adapter_issue_readiness_inventory.csv",
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1/covapie_admit_014_unified_adapter_contract_manifest.json",
        "fbcca891692e4b88d2da854425bef9ce38d1eced97df1c0ca826edad95357de0",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_014_rule_logic_interface.py",
        "5f0766a4eb9dac8b00b9729b7d593adfbe105fb212eabbd4e0a3e349b35f7399",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_manifest.json",
        "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate.py",
        "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1/covapie_admit_014_formal_evaluator_interface_contract_manifest.json",
        "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_truth_matrix.csv",
        "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_contract_manifest.json",
        "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    ),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

CONTRACT_FILENAME = "covapie_admit_001_to_014_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_014_dispatch_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_014_registry_and_identity_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_014_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_014_runtime_manifest.json"
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
    "contract_group",
    "contract_item",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "admission_rule_id",
    "candidate_representation",
    "batch_context_representation",
    "evaluation_context_representation",
    "download_result_context_representation",
    "stage_authorization_context_representation",
    "expected_outcome_or_error",
    "observed_outcome_or_error",
    "expected_result_json",
    "observed_result_json",
    "expected_call_order",
    "observed_call_order",
    "expected_stage_context_identity_preserved",
    "observed_stage_context_identity_preserved",
    "formal_call_count",
    "oracle_call_count",
    "candidate_key_access_count",
    "adapter_stage_target_access_count",
    "formal_stage_target_access_count",
    "oracle_stage_target_access_count",
    "stage_target_access_count",
    "case_passed",
)
TRUTH_INPUT_REPRESENTATION_COLUMNS = (
    "candidate_representation",
    "batch_context_representation",
    "evaluation_context_representation",
    "download_result_context_representation",
    "stage_authorization_context_representation",
)
EXACT42_INPUT_REPRESENTATIONS = {
    "batch_non_none": ("{}", "object", "None", "None", "{target:True}"),
    "batch_empty_mapping": ("{}", "{}", "None", "None", "{target:True}"),
    "evaluation_non_none": ("{}", "None", "object", "None", "{target:True}"),
    "evaluation_empty_mapping": ("{}", "None", "{}", "None", "{target:True}"),
    "download_non_none": ("{}", "None", "None", "object", "{target:True}"),
    "download_empty_mapping": ("{}", "None", "None", "{}", "{target:True}"),
    "multiple_invalid_batch_first": (
        "object", "object", "object", "object", "{target:True}",
    ),
    "multiple_invalid_evaluation_first": (
        "object", "None", "object", "object", "{target:True}",
    ),
    "multiple_invalid_download_first": (
        "object", "None", "None", "object", "{target:True}",
    ),
    "candidate_non_mapping": ("object", "None", "None", "None", "{}"),
    "candidate_empty": ("{}", "None", "None", "None", "None"),
    "candidate_instrumented": (
        "instrumented_mapping", "None", "None", "None", "None",
    ),
    "stage_none": ("{}", "None", "None", "None", "None"),
    "stage_object": ("{}", "None", "None", "None", "object"),
    "stage_empty_mapping": ("{}", "None", "None", "None", "{}"),
    "stage_false": ("{}", "None", "None", "None", "{target:False}"),
    "stage_true": ("{}", "None", "None", "None", "{target:True}"),
    "stage_extra_keys": (
        "{}", "None", "None", "None",
        "{target:True,training:True,extra:1}",
    ),
    "stage_keyerror": (
        "{}", "None", "None", "None", "KeyError_mapping",
    ),
    "stage_runtimeerror": (
        "{}", "None", "None", "None", "RuntimeError_mapping",
    ),
    "stage_valueerror": (
        "{}", "None", "None", "None", "ValueError_mapping",
    ),
    "formal_once": ("{}", "None", "None", "None", "{target:True}"),
    "oracle_once": ("{}", "None", "None", "None", "{target:True}"),
    "source_invalid_no_oracle": (
        "{}", "None", "None", "None", "None",
    ),
    "nonrepeatable_mismatch": (
        "{}", "None", "None", "None", "alternating_mapping",
    ),
    "source_wrong_type": ("{}", "None", "None", "None", "None"),
    "source_subclass": ("{}", "None", "None", "None", "None"),
    "source_storage_order": ("{}", "None", "None", "None", "None"),
    "source_type_drift": ("{}", "None", "None", "None", "None"),
    "source_invariant": ("{}", "None", "None", "None", "None"),
    "oracle_wrong_type": ("{}", "None", "None", "None", "None"),
    "oracle_storage": ("{}", "None", "None", "None", "None"),
    "oracle_mismatch": ("{}", "None", "None", "None", "None"),
    "oracle_exception": ("{}", "None", "None", "None", "None"),
    "candidate_fields_empty": (
        "{}", "None", "None", "None", "{target:True}",
    ),
    "consumed_context": ("{}", "None", "None", "None", "{target:True}"),
    "false_lowercase": (
        "{}", "None", "None", "None", "{target:False}",
    ),
    "true_lowercase": ("{}", "None", "None", "None", "{target:True}"),
    "current_exact13": ("{}", "None", "None", "None", "{target:True}"),
    "future_exact14": ("{}", "None", "None", "None", "{target:True}"),
    "known_unregistered": (
        "{}", "None", "None", "None", "{target:True}",
    ),
    "handler_identity": ("{}", "None", "None", "None", "{target:True}"),
}
REGISTRY_COLUMNS = (
    "audit_order",
    "rule_id",
    "expected_handler_identity",
    "observed_handler_identity",
    "identity_preserved",
    "registered",
    "callable_discovered",
    "adapter_ready",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_state",
    "observed_state",
    "safety_passed",
)
ISSUE_COLUMNS = (
    "inherited_order",
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
    "inherited_effective_status",
    "inherited_transition_stage",
    "inherited_transition_action",
    "inherited_transition_evidence",
    "successor_effective_status",
    "successor_transition_stage",
    "successor_transition_action",
    "successor_transition_evidence",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_blob: str
    index_mode: str
    index_blob: str
    index_stage: int
    base_tree_sha256: str
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _assert_canonical_evidence_runtime() -> None:
    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != CANONICAL_PYTHON_VERSION
    ):
        observed = ".".join(map(str, sys.version_info[:3]))
        raise ValueError(
            "required: CPython 3.10.4; "
            f"observed implementation: {sys.implementation.name}; "
            f"observed version: {observed}; "
            "frozen evidence is Python-version-sensitive"
        )


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError(f"git command failed: {arguments}")
    return completed.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _full_identity(
    item: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
)
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FLAGS = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_EXCL
    | os.O_NOFOLLOW
    | os.O_CLOEXEC
)
MAX_CANDIDATE_BYTES = 100 * 1024 * 1024


def _pinned_read(root: Path, relative: Path) -> bytes:
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
    ):
        raise ValueError("unsafe pinned-read path")
    root_item = os.lstat(root)
    root_identity = _full_identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("unsafe pinned-read root")
    root_fd = os.open(root, DIRECTORY_FLAGS)
    descriptors = [root_fd]
    bindings: list[
        tuple[int, str, int, tuple[int, int, int, int, int, int]]
    ] = []
    try:
        if _full_identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("pinned-read root stat/open race")
        parent_fd = root_fd
        for part in relative.parts[:-1]:
            lexical = os.stat(
                part, dir_fd=parent_fd, follow_symlinks=False
            )
            expected = _full_identity(lexical)
            if (
                not stat.S_ISDIR(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
            ):
                raise ValueError("unsafe pinned-read parent")
            child_fd = os.open(part, DIRECTORY_FLAGS, dir_fd=parent_fd)
            if _full_identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise ValueError("pinned-read parent stat/open race")
            bindings.append((parent_fd, part, child_fd, expected))
            descriptors.append(child_fd)
            parent_fd = child_fd
        before = os.stat(
            relative.name, dir_fd=parent_fd, follow_symlinks=False
        )
        leaf_identity = _full_identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > MAX_CANDIDATE_BYTES
        ):
            raise ValueError("unsafe pinned-read leaf")
        leaf_fd = os.open(relative.name, READ_FLAGS, dir_fd=parent_fd)
        descriptors.append(leaf_fd)
        if _full_identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("pinned-read leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _full_identity(os.fstat(leaf_fd)) != leaf_identity
            or _full_identity(
                os.stat(
                    relative.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != leaf_identity
        ):
            raise ValueError("pinned-read leaf changed")
        for lexical_parent, name, child_fd, expected in reversed(bindings):
            lexical = os.stat(
                name, dir_fd=lexical_parent, follow_symlinks=False
            )
            if (
                _full_identity(lexical) != expected
                or _full_identity(os.fstat(child_fd)) != expected
            ):
                raise ValueError("pinned-read parent changed")
        if (
            _full_identity(os.lstat(root)) != root_identity
            or _full_identity(os.fstat(root_fd)) != root_identity
        ):
            raise ValueError("pinned-read root changed")
        if (
            _full_identity(os.fstat(leaf_fd)) != leaf_identity
            or _full_identity(
                os.stat(
                    relative.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != leaf_identity
        ):
            raise ValueError("pinned-read final leaf changed")
        return b"".join(chunks)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _parse_index_entry(
    content: bytes,
    relative: str,
) -> tuple[str, str, int]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, raw_stage = metadata.split(" ")
        stage_number = int(raw_stage)
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if (
        observed != relative
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("index entry drift")
    return mode, blob, stage_number


def _parse_tree_entry(
    content: bytes,
    relative: str,
) -> tuple[str, str]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if (
        observed != relative
        or mode not in {"100644", "100755"}
        or kind != "blob"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("tree entry drift")
    return mode, blob


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    _assert_canonical_evidence_runtime()
    root = Path(os.path.abspath(repo_root))
    identity = _git(
        root,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        EXPECTED_BASE_COMMIT,
    ).decode().splitlines()
    if identity != [
        EXPECTED_BASE_COMMIT,
        EXPECTED_BASE_PARENT,
        EXPECTED_BASE_TREE,
        EXPECTED_BASE_SUBJECT,
    ]:
        raise ValueError("base identity drift")
    _git(root, "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref)
    if (
        len(SOURCE_BOUNDARY) != 20
        or len(set(SOURCE_PATHS)) != 20
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact20 source boundary drift")
    inspected = []
    for relative, expected in zip(
        SOURCE_PATHS,
        (digest for _, digest in SOURCE_BOUNDARY),
        strict=True,
    ):
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
            or STAGE in relative.parts
        ):
            raise ValueError("unsafe source boundary path")
        raw = relative.as_posix()
        index_mode, index_blob, index_stage = _parse_index_entry(
            _git(root, "ls-files", "--stage", "--", raw),
            raw,
        )
        base_mode, base_blob = _parse_tree_entry(
            _git(root, "ls-tree", EXPECTED_BASE_COMMIT, "--", raw),
            raw,
        )
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
        ):
            raise ValueError("source index/base identity drift")
        inspected.append(
            (
                relative,
                expected,
                base_mode,
                base_blob,
                index_mode,
                index_blob,
                index_stage,
            )
        )
    records = []
    for (
        relative,
        expected,
        base_mode,
        base_blob,
        index_mode,
        index_blob,
        index_stage,
    ) in inspected:
        base = _git(root, "cat-file", "blob", base_blob)
        index = _git(root, "cat-file", "blob", index_blob)
        filesystem = _pinned_read(root, relative)
        if (
            base != index
            or index != filesystem
            or _sha(base) != expected
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source bytes/SHA drift: {relative}")
        records.append(
            FrozenSourceRecord(
                relative,
                expected,
                base_mode,
                base_blob,
                index_mode,
                index_blob,
                index_stage,
                _sha(base),
                _sha(filesystem),
                filesystem,
            )
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 20
        and tuple(record.relative_path for record in value.records)
        == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256
            == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and record.index_stage == 0
            and record.index_mode == record.base_tree_mode
            and record.index_blob == record.base_tree_blob
            and _sha(record.content) == record.expected_sha256
            for record in value.records
        )
    )


def _source_record(
    snapshot: FrozenSourceSnapshot,
    suffix: str,
) -> FrozenSourceRecord:
    matches = tuple(
        record
        for record in snapshot.records
        if record.relative_path.as_posix().endswith(suffix)
    )
    if len(matches) != 1:
        raise ValueError(f"source record missing/duplicate: {suffix}")
    return matches[0]


def _csv_rows(
    content: bytes,
    columns: Sequence[str] | None = None,
) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    header = tuple(reader.fieldnames or ())
    if (
        not header
        or len(header) != len(set(header))
        or (columns is not None and header != tuple(columns))
    ):
        raise ValueError("CSV header drift")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != header or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("CSV row shape drift")
    return rows


def _json_object(content: bytes) -> dict[str, Any]:
    value = json.loads(content)
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _candidate_source_attestation(
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    relative = Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_014.py"
    )
    source = _pinned_read(Path(os.path.abspath(repo_root)), relative)
    text = source.decode()
    if text.count(PUBLIC_MARKER) != 1:
        raise ValueError("public marker drift")
    prefix = text.split(PUBLIC_MARKER, 1)[0].encode()
    tree = ast.parse(source)
    marker_line = text[: text.index(PUBLIC_MARKER)].count("\n") + 1
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in PUBLIC_DEFINITIONS
    }
    if (
        tuple(definitions) != PUBLIC_DEFINITIONS
        or any(node.lineno >= marker_line for node in definitions.values())
    ):
        raise ValueError("public Exact11 definition drift")
    hashes = {
        name: _sha(
            ast.dump(
                definitions[name],
                annotate_fields=True,
                include_attributes=False,
            ).encode()
        )
        for name in PUBLIC_DEFINITIONS
    }
    prefix_tree = ast.parse(prefix)
    project_imports = []
    for node in prefix_tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            project_imports.extend(
                (alias.name, alias.asname) for alias in node.names
            )
    expected_imports = [
        (
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013",
            "predecessor",
        ),
        (
            "covapie_bulk_download_admission_admit_014_rule_logic_interface",
            "admit014",
        ),
        (
            "covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate",
            "admit014_oracle",
        ),
    ]
    forbidden = (
        "simulate_admit_014_unified_adapter_contract_design",
        "covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate",
        "importlib",
        "provider",
        "downloader",
        "data/raw",
        "checkpoints",
        "evaluate_all_rules",
        "combined_candidate_verdict",
    )
    if project_imports != expected_imports or any(
        token in prefix.decode() for token in forbidden
    ):
        raise ValueError("public closure dependency drift")
    return {
        "candidate_relative_path": relative.as_posix(),
        "production_full_sha256": _sha(source),
        "marker_prefix_sha256": _sha(prefix),
        "definition_count": 11,
        "definition_names": list(PUBLIC_DEFINITIONS),
        "normalized_ast_sha256": hashes,
        "public_closure_pure_memory": True,
        "adapter_design_simulator_called": False,
    }


def _jsonable(value: object) -> object:
    if type(value) is tuple:
        return [_jsonable(item) for item in value]
    if type(value) is list:
        return [_jsonable(item) for item in value]
    if type(value) is dict:
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool, float):
        return value
    return f"<{type(value).__name__}>"


def _evaluation_json(value: object) -> str:
    return json.dumps(
        {
            name: _jsonable(getattr(value, name))
            for name in RESULT_FIELDS
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _error_json(value: object) -> str:
    return json.dumps(
        {
            name: _jsonable(getattr(value, name))
            for name in DISPATCH_ERROR_FIELDS
        },
        sort_keys=True,
        separators=(",", ":"),
    )


class _CandidateProbe(Mapping[str, object]):
    def __init__(self) -> None:
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        raise AssertionError("candidate access forbidden")

    def __iter__(self):
        self.access_count += 1
        raise AssertionError("candidate iteration forbidden")

    def __len__(self) -> int:
        self.access_count += 1
        raise AssertionError("candidate length forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.access_count += 1
        raise AssertionError("candidate get forbidden")

    def __contains__(self, key: object) -> bool:
        self.access_count += 1
        raise AssertionError("candidate contains forbidden")


class _StageProbe(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object] | None = None,
        *,
        error: BaseException | None = None,
        alternating: bool = False,
    ) -> None:
        self.values = {} if values is None else dict(values)
        self.error = error
        self.alternating = alternating
        self.target_access_count = 0

    def __getitem__(self, key: str) -> object:
        self.target_access_count += 1
        if self.error is not None:
            raise self.error
        if self.alternating:
            return self.target_access_count == 1
        return self.values[key]

    def __iter__(self):
        raise AssertionError("stage iteration forbidden")

    def __len__(self) -> int:
        raise AssertionError("stage length forbidden")


def _runtime_input_representations(
    scenario: str,
    candidate: object,
    batch: object,
    evaluation: object,
    download: object,
    stage: object,
) -> tuple[str, str, str, str, str]:
    def candidate_token(value: object) -> str:
        if isinstance(value, _CandidateProbe):
            return "instrumented_mapping"
        if type(value) is dict and not value:
            return "{}"
        if type(value) is object:
            return "object"
        raise ValueError("candidate representation unsupported")

    def context_token(value: object) -> str:
        if value is None:
            return "None"
        if type(value) is dict and not value:
            return "{}"
        if type(value) is object:
            return "object"
        raise ValueError("context representation unsupported")

    def stage_token(value: object) -> str:
        if value is None:
            return "None"
        if type(value) is object:
            return "object"
        if not isinstance(value, _StageProbe):
            raise ValueError("stage representation unsupported")
        if value.alternating:
            return "alternating_mapping"
        if value.error is not None:
            error_tokens = {
                KeyError: "KeyError_mapping",
                RuntimeError: "RuntimeError_mapping",
                ValueError: "ValueError_mapping",
            }
            token = error_tokens.get(type(value.error))
            if token is None:
                raise ValueError("stage error representation unsupported")
            return token
        values = tuple(value.values.items())
        known_values = {
            (): "{}",
            (("current_stage_download_authorized", False),): (
                "{target:False}"
            ),
            (("current_stage_download_authorized", True),): (
                "{target:True}"
            ),
            (
                ("current_stage_download_authorized", True),
                ("current_stage_training_authorized", True),
                ("extra", 1),
            ): "{target:True,training:True,extra:1}",
        }
        token = known_values.get(values)
        if token is None:
            raise ValueError("stage value representation unsupported")
        return token

    representations = (
        candidate_token(candidate),
        context_token(batch),
        context_token(evaluation),
        context_token(download),
        stage_token(stage),
    )
    if scenario not in {
        str(spec["_scenario"])
        for spec in admit014_adapter_design._routing_case_specs()
    }:
        raise ValueError("unknown Exact42 representation scenario")
    return representations


def _mutate_exact9(value: object, scenario: str) -> object:
    if scenario.endswith("wrong_type"):
        return object()
    if scenario in {"source_subclass", "oracle_subclass"}:
        subtype = type("_EvidenceExact9Subclass", (type(value),), {})
        instance = object.__new__(subtype)
        for name in ADMIT_014_SOURCE_FIELDS:
            object.__setattr__(instance, name, getattr(value, name))
        return instance
    if scenario in {"source_storage", "oracle_storage"}:
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif scenario in {"source_type_drift", "oracle_type_drift"}:
        object.__setattr__(value, "outcome", 1)
    elif scenario in {"source_invariant", "oracle_mismatch"}:
        object.__setattr__(value, "outcome", "passed")
    return value


def _truth_row(
    case_id: str,
    case_group: str,
    expected_kind: str,
    observed_kind: str,
    expected_json: str,
    observed_json: str,
    *,
    candidate: str = "{}",
    batch: str = "None",
    evaluation: str = "None",
    download: str = "None",
    stage: str = "None",
    formal_calls: int = 0,
    oracle_calls: int = 0,
    candidate_access: int = 0,
    adapter_stage_access: int = 0,
    formal_stage_access: int = 0,
    oracle_stage_access: int = 0,
    stage_access: int = 0,
    expected_call_order: str = "",
    observed_call_order: str = "",
    expected_identity: str = "n/a",
    observed_identity: str = "n/a",
    expected_formal_calls: int = 0,
    expected_oracle_calls: int = 0,
    expected_candidate_access: int = 0,
    expected_adapter_stage_access: int = 0,
    expected_formal_stage_access: int = 0,
    expected_oracle_stage_access: int = 0,
    expected_stage_access: int = 0,
    expected_input_representations: tuple[
        str, str, str, str, str
    ] | None = None,
) -> dict[str, str]:
    input_representations = (
        candidate,
        batch,
        evaluation,
        download,
        stage,
    )
    expected_representations = (
        input_representations
        if expected_input_representations is None
        else expected_input_representations
    )
    passed = (
        input_representations == expected_representations
        and expected_kind == observed_kind
        and expected_json == observed_json
        and expected_call_order == observed_call_order
        and expected_identity == observed_identity
        and formal_calls == expected_formal_calls
        and oracle_calls == expected_oracle_calls
        and candidate_access == expected_candidate_access
        and adapter_stage_access == expected_adapter_stage_access
        and formal_stage_access == expected_formal_stage_access
        and oracle_stage_access == expected_oracle_stage_access
        and stage_access == expected_stage_access
        and stage_access
        == adapter_stage_access + formal_stage_access + oracle_stage_access
    )
    return {
        "case_order": "",
        "case_id": case_id,
        "case_group": case_group,
        "admission_rule_id": ADMISSION_RULE_ID,
        "candidate_representation": candidate,
        "batch_context_representation": batch,
        "evaluation_context_representation": evaluation,
        "download_result_context_representation": download,
        "stage_authorization_context_representation": stage,
        "expected_outcome_or_error": expected_kind,
        "observed_outcome_or_error": observed_kind,
        "expected_result_json": expected_json,
        "observed_result_json": observed_json,
        "expected_call_order": expected_call_order,
        "observed_call_order": observed_call_order,
        "expected_stage_context_identity_preserved": expected_identity,
        "observed_stage_context_identity_preserved": observed_identity,
        "formal_call_count": str(formal_calls),
        "oracle_call_count": str(oracle_calls),
        "candidate_key_access_count": str(candidate_access),
        "adapter_stage_target_access_count": str(adapter_stage_access),
        "formal_stage_target_access_count": str(formal_stage_access),
        "oracle_stage_target_access_count": str(oracle_stage_access),
        "stage_target_access_count": str(stage_access),
        "case_passed": str(passed).lower(),
    }


def _execute_exact42_case(spec: Mapping[str, Any]) -> dict[str, str]:
    scenario = spec["_scenario"]
    candidate: object = {}
    stage: object = _StageProbe(
        {"current_stage_download_authorized": True}
    )
    batch = evaluation = download = None
    if scenario == "batch_object":
        batch = object()
    elif scenario == "batch_mapping":
        batch = {}
    elif scenario == "evaluation_object":
        evaluation = object()
    elif scenario == "evaluation_mapping":
        evaluation = {}
    elif scenario == "download_object":
        download = object()
    elif scenario == "download_mapping":
        download = {}
    elif scenario == "all_invalid":
        batch, evaluation, download, candidate = (
            object(),
            object(),
            object(),
            object(),
        )
    elif scenario == "evaluation_download_candidate_invalid":
        evaluation, download, candidate = object(), object(), object()
    elif scenario == "download_candidate_invalid":
        download, candidate = object(), object()
    elif scenario == "candidate_invalid":
        candidate, stage = object(), _StageProbe()
    elif scenario == "candidate_empty":
        stage = None
    elif scenario == "candidate_probe":
        candidate, stage = _CandidateProbe(), None
    elif scenario == "stage_none":
        stage = None
    elif scenario == "stage_object":
        stage = object()
    elif scenario == "stage_empty":
        stage = _StageProbe()
    elif scenario == "stage_false":
        stage = _StageProbe({"current_stage_download_authorized": False})
    elif scenario == "stage_extra":
        stage = _StageProbe(
            {
                "current_stage_download_authorized": True,
                "current_stage_training_authorized": True,
                "extra": 1,
            }
        )
    elif scenario == "stage_keyerror":
        stage = _StageProbe(
            error=KeyError("current_stage_download_authorized")
        )
    elif scenario == "stage_runtimeerror":
        stage = _StageProbe(error=RuntimeError("evidence"))
    elif scenario == "stage_valueerror":
        stage = _StageProbe(error=ValueError("evidence"))
    elif scenario == "nonrepeatable":
        stage = _StageProbe(alternating=True)
    elif str(scenario).startswith(("source_", "oracle_")):
        stage = None
    input_representations = _runtime_input_representations(
        str(scenario),
        candidate,
        batch,
        evaluation,
        download,
        stage,
    )
    expected_input_representations = EXACT42_INPUT_REPRESENTATIONS.get(
        str(spec["case_id"])
    )
    if expected_input_representations is None:
        raise ValueError("Exact42 input representation spec missing")

    calls: list[str] = []
    identities: list[bool] = []
    formal_stage_access = 0
    oracle_stage_access = 0
    original_formal = admit014.evaluate_admit_014
    original_oracle = (
        admit014_oracle
        .classify_admit_014_formal_evaluator_interface_design
    )

    def formal_wrapper(
        *,
        stage_authorization_context: object,
    ) -> object:
        nonlocal formal_stage_access
        calls.append("formal")
        identities.append(stage_authorization_context is stage)
        before_access = (
            stage.target_access_count
            if isinstance(stage, _StageProbe)
            else 0
        )
        value = original_formal(
            stage_authorization_context=stage_authorization_context
        )
        formal_stage_access += (
            stage.target_access_count - before_access
            if isinstance(stage, _StageProbe)
            else 0
        )
        if str(scenario).startswith("source_"):
            value = _mutate_exact9(value, str(scenario))
        return value

    def oracle_wrapper(
        *,
        stage_authorization_context: object,
    ) -> object:
        nonlocal oracle_stage_access
        calls.append("oracle")
        identities.append(stage_authorization_context is stage)
        before_access = (
            stage.target_access_count
            if isinstance(stage, _StageProbe)
            else 0
        )
        if scenario == "oracle_exception":
            raise RuntimeError("oracle evidence")
        oracle_stage = (
            object()
            if scenario == "oracle_mismatch"
            else stage_authorization_context
        )
        value = original_oracle(
            stage_authorization_context=oracle_stage
        )
        oracle_stage_access += (
            stage.target_access_count - before_access
            if isinstance(stage, _StageProbe)
            else 0
        )
        if str(scenario).startswith("oracle_"):
            value = _mutate_exact9(value, str(scenario))
        return value

    admit014.evaluate_admit_014 = formal_wrapper
    (
        admit014_oracle
        .classify_admit_014_formal_evaluator_interface_design
    ) = oracle_wrapper
    try:
        try:
            value = evaluate_admission_rule(
                ADMISSION_RULE_ID,
                candidate,
                batch_context=batch,
                evaluation_context=evaluation,
                download_result_context=download,
                stage_authorization_context=stage,
            )
        except UnifiedAdmissionDispatchError as error:
            observed_kind = error.code
            observed_json = _error_json(error)
        else:
            observed_kind = value.outcome
            observed_json = _evaluation_json(value)
    finally:
        admit014.evaluate_admit_014 = original_formal
        (
            admit014_oracle
            .classify_admit_014_formal_evaluator_interface_design
        ) = original_oracle

    expected_json = json.dumps(
        json.loads(spec["expected_result_json"]),
        sort_keys=True,
        separators=(",", ":"),
    )
    expected_kind = (
        str(spec["expected_dispatch_code"])
        if spec["expected_dispatch_code"]
        else json.loads(expected_json)["outcome"]
    )
    candidate_access = (
        candidate.access_count
        if isinstance(candidate, _CandidateProbe)
        else 0
    )
    stage_access = (
        stage.target_access_count
        if isinstance(stage, _StageProbe)
        else 0
    )
    adapter_stage_access = (
        stage_access - formal_stage_access - oracle_stage_access
    )
    expected_call_order = (
        "formal|oracle"
        if int(spec["oracle_call_count"]) == 1
        else "formal"
        if int(spec["formal_call_count"]) == 1
        else ""
    )
    observed_identity = (
        "n/a" if not identities else str(all(identities)).lower()
    )
    row = _truth_row(
        str(spec["case_id"]),
        "admit014_inherited_exact42_runtime",
        expected_kind,
        observed_kind,
        expected_json,
        observed_json,
        candidate=input_representations[0],
        batch=input_representations[1],
        evaluation=input_representations[2],
        download=input_representations[3],
        stage=input_representations[4],
        formal_calls=calls.count("formal"),
        oracle_calls=calls.count("oracle"),
        candidate_access=candidate_access,
        adapter_stage_access=adapter_stage_access,
        formal_stage_access=formal_stage_access,
        oracle_stage_access=oracle_stage_access,
        stage_access=stage_access,
        expected_call_order=expected_call_order,
        observed_call_order="|".join(calls),
        expected_identity=str(spec["identity_preserved"]),
        observed_identity=observed_identity,
        expected_formal_calls=int(spec["formal_call_count"]),
        expected_oracle_calls=int(spec["oracle_call_count"]),
        expected_candidate_access=int(spec["candidate_key_access_count"]),
        expected_adapter_stage_access=int(
            spec["adapter_stage_key_access_count"]
        ),
        expected_formal_stage_access=int(
            spec["formal_stage_key_access_count"]
        ),
        expected_oracle_stage_access=int(
            spec["oracle_stage_key_access_count"]
        ),
        expected_stage_access=(
            int(spec["adapter_stage_key_access_count"])
            + int(spec["formal_stage_key_access_count"])
            + int(spec["oracle_stage_key_access_count"])
        ),
        expected_input_representations=expected_input_representations,
    )
    return row


def _source_negative_value(
    mode: str,
    formal_evaluator: object,
) -> object:
    value = formal_evaluator(
        stage_authorization_context=None
    )
    if mode == "subclass":
        return _mutate_exact9(value, "source_subclass")
    if mode == "storage_reorder":
        return _mutate_exact9(value, "source_storage")
    if mode == "top_level_type":
        object.__setattr__(value, "outcome", 1)
    elif mode == "rule_id":
        object.__setattr__(value, "admission_rule_id", "ADMIT_015")
    elif mode == "io_true":
        object.__setattr__(value, "evaluator_io_used", True)
    elif mode == "outcome_reason":
        object.__setattr__(value, "outcome", "passed")
    elif mode == "canonical":
        object.__setattr__(
            value,
            "canonical_stage_authorization_record",
            (("unexpected", True),),
        )
    elif mode == "validated":
        object.__setattr__(
            value, "validated_stage_authorization_fields", (1,)
        )
    elif mode == "consumed":
        object.__setattr__(
            value, "consumed_stage_authorization_fields", (1,)
        )
    return value


def _source_negative_rows() -> list[dict[str, str]]:
    modes = (
        "wrong_type",
        "subclass",
        "storage_reorder",
        "top_level_type",
        "rule_id",
        "io_true",
        "outcome_reason",
        "canonical",
        "validated",
        "consumed",
        "exception",
    )
    rows = []
    original_formal = admit014.evaluate_admit_014
    original_oracle = (
        admit014_oracle
        .classify_admit_014_formal_evaluator_interface_design
    )
    for mode in modes:
        counts = {"formal": 0, "oracle": 0}
        calls: list[str] = []
        identities: list[bool] = []

        def formal_wrapper(
            *,
            stage_authorization_context: object,
            mode: str = mode,
        ) -> object:
            counts["formal"] += 1
            calls.append("formal")
            identities.append(stage_authorization_context is None)
            if mode == "exception":
                raise RuntimeError("formal evidence")
            if mode == "wrong_type":
                return object()
            return _source_negative_value(mode, original_formal)

        def oracle_wrapper(
            *,
            stage_authorization_context: object,
        ) -> object:
            counts["oracle"] += 1
            calls.append("oracle")
            identities.append(stage_authorization_context is None)
            return original_oracle(
                stage_authorization_context=stage_authorization_context
            )

        admit014.evaluate_admit_014 = formal_wrapper
        (
            admit014_oracle
            .classify_admit_014_formal_evaluator_interface_design
        ) = oracle_wrapper
        try:
            try:
                evaluate_admission_rule(ADMISSION_RULE_ID, {})
            except UnifiedAdmissionDispatchError as error:
                observed_kind = error.code
                observed_json = _error_json(error)
            else:
                raise ValueError("source negative unexpectedly passed")
        finally:
            admit014.evaluate_admit_014 = original_formal
            (
                admit014_oracle
                .classify_admit_014_formal_evaluator_interface_design
            ) = original_oracle
        reason = (
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
            if mode in {"wrong_type", "subclass"}
            else "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
        expected_error = UnifiedAdmissionDispatchError(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            ADMISSION_RULE_ID,
            True,
            True,
            False,
            reason,
        )
        row = _truth_row(
            f"SOURCE_NEGATIVE_{mode}",
            "admit014_source_negative",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            observed_kind,
            _error_json(expected_error),
            observed_json,
            formal_calls=counts["formal"],
            oracle_calls=counts["oracle"],
            expected_call_order="formal",
            observed_call_order="|".join(calls),
            expected_identity="true",
            observed_identity=str(all(identities)).lower(),
            expected_formal_calls=1,
            expected_oracle_calls=0,
        )
        rows.append(row)
    return rows


def _oracle_negative_rows() -> list[dict[str, str]]:
    modes = (
        "wrong_type",
        "subclass",
        "storage_reorder",
        "top_level_type",
        "rule_id",
        "value_mismatch",
        "exception",
        "stateful_mapping",
    )
    rows = []
    original_formal = admit014.evaluate_admit_014
    original_oracle = (
        admit014_oracle
        .classify_admit_014_formal_evaluator_interface_design
    )
    for mode in modes:
        counts = {"formal": 0, "oracle": 0}
        calls: list[str] = []
        identities: list[bool] = []
        formal_stage_access = 0
        oracle_stage_access = 0
        stage: object = (
            _StageProbe(alternating=True)
            if mode == "stateful_mapping"
            else None
        )

        def formal_wrapper(
            *,
            stage_authorization_context: object,
        ) -> object:
            nonlocal formal_stage_access
            counts["formal"] += 1
            calls.append("formal")
            identities.append(stage_authorization_context is stage)
            before_access = (
                stage.target_access_count
                if isinstance(stage, _StageProbe)
                else 0
            )
            value = original_formal(
                stage_authorization_context=stage_authorization_context
            )
            formal_stage_access += (
                stage.target_access_count - before_access
                if isinstance(stage, _StageProbe)
                else 0
            )
            return value

        def oracle_wrapper(
            *,
            stage_authorization_context: object,
            mode: str = mode,
        ) -> object:
            nonlocal oracle_stage_access
            counts["oracle"] += 1
            calls.append("oracle")
            identities.append(stage_authorization_context is stage)
            before_access = (
                stage.target_access_count
                if isinstance(stage, _StageProbe)
                else 0
            )
            if mode == "exception":
                raise RuntimeError("oracle evidence")
            if mode == "wrong_type":
                return object()
            oracle_stage = (
                object()
                if mode == "value_mismatch"
                else stage_authorization_context
            )
            value = original_oracle(
                stage_authorization_context=oracle_stage
            )
            oracle_stage_access += (
                stage.target_access_count - before_access
                if isinstance(stage, _StageProbe)
                else 0
            )
            if mode == "subclass":
                return _mutate_exact9(value, "oracle_subclass")
            if mode == "storage_reorder":
                return _mutate_exact9(value, "oracle_storage")
            if mode == "top_level_type":
                object.__setattr__(value, "outcome", 1)
            elif mode == "rule_id":
                object.__setattr__(value, "admission_rule_id", "ADMIT_015")
            return value

        admit014.evaluate_admit_014 = formal_wrapper
        (
            admit014_oracle
            .classify_admit_014_formal_evaluator_interface_design
        ) = oracle_wrapper
        try:
            try:
                evaluate_admission_rule(
                    ADMISSION_RULE_ID,
                    {},
                    stage_authorization_context=stage,
                )
            except UnifiedAdmissionDispatchError as error:
                observed_kind = error.code
                observed_json = _error_json(error)
            else:
                raise ValueError("oracle negative unexpectedly passed")
        finally:
            admit014.evaluate_admit_014 = original_formal
            (
                admit014_oracle
                .classify_admit_014_formal_evaluator_interface_design
            ) = original_oracle
        expected_error = UnifiedAdmissionDispatchError(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            ADMISSION_RULE_ID,
            True,
            True,
            False,
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
        stage_access = (
            stage.target_access_count
            if isinstance(stage, _StageProbe)
            else 0
        )
        adapter_stage_access = (
            stage_access - formal_stage_access - oracle_stage_access
        )
        expected_split = 1 if mode == "stateful_mapping" else 0
        row = _truth_row(
            f"ORACLE_NEGATIVE_{mode}",
            "admit014_oracle_negative",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            observed_kind,
            _error_json(expected_error),
            observed_json,
            formal_calls=counts["formal"],
            oracle_calls=counts["oracle"],
            adapter_stage_access=adapter_stage_access,
            formal_stage_access=formal_stage_access,
            oracle_stage_access=oracle_stage_access,
            stage_access=stage_access,
            expected_call_order="formal|oracle",
            observed_call_order="|".join(calls),
            expected_identity="true",
            observed_identity=str(all(identities)).lower(),
            expected_formal_calls=1,
            expected_oracle_calls=1,
            expected_formal_stage_access=expected_split,
            expected_oracle_stage_access=expected_split,
            expected_stage_access=expected_split * 2,
            stage=(
                "alternating_mapping"
                if mode == "stateful_mapping"
                else "None"
            ),
        )
        rows.append(row)
    return rows


def _observe_dispatch(
    module: object,
    rule_id: object,
) -> tuple[str, str]:
    try:
        value = module.evaluate_admission_rule(rule_id, {})
    except UnifiedAdmissionDispatchError as error:
        return error.code, _error_json(error)
    return value.outcome, _evaluation_json(value)


def _dispatcher_and_predecessor_rows() -> list[dict[str, str]]:
    class RuleIdSubclass(str):
        pass

    rows = []
    definitions = (
        ("bool", True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("str_subclass", RuleIdSubclass(ADMISSION_RULE_ID), "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("unknown", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        ("admit015", "ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
    )
    for name, rule_id, expected_code in definitions:
        observed_kind, observed_json = _observe_dispatch(
            sys.modules[__name__],
            rule_id,
        )
        expected_error = UnifiedAdmissionDispatchError(
            expected_code,
            "" if type(rule_id) is not str else rule_id,
            expected_code == "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            False,
            False,
            expected_code,
        )
        rows.append(
            _truth_row(
                f"DISPATCH_{name}",
                "public_dispatch",
                expected_code,
                observed_kind,
                _error_json(expected_error),
                observed_json,
            )
        )
    stage_spec = next(
        spec
        for spec in admit014_adapter_design._routing_case_specs()
        if spec["case_id"] == "stage_true"
    )
    registered_row = _execute_exact42_case(stage_spec)
    registered_row.update(
        {
            "case_id": "DISPATCH_admit014_registered",
            "case_group": "public_dispatch",
        }
    )
    rows.append(registered_row)
    for rule_id in KNOWN_RULE_IDS[:13]:
        expected_kind, expected_json = _observe_dispatch(
            predecessor,
            rule_id,
        )
        observed_kind, observed_json = _observe_dispatch(
            sys.modules[__name__],
            rule_id,
        )
        row = _truth_row(
            f"PREDECESSOR_{rule_id}",
            "predecessor_representative_dispatch",
            expected_kind,
            observed_kind,
            expected_json,
            observed_json,
        )
        if (
            EVALUATOR_REGISTRY[rule_id]
            is not predecessor.EVALUATOR_REGISTRY[rule_id]
        ):
            row["case_passed"] = "false"
        rows.append(row)
    return rows


def _validate_truth_input_representations(
    rows: Sequence[Mapping[str, str]],
) -> None:
    inherited = rows[:42]
    if (
        len(rows) != 79
        or len(EXACT42_INPUT_REPRESENTATIONS) != 42
        or tuple(row["case_id"] for row in inherited)
        != tuple(EXACT42_INPUT_REPRESENTATIONS)
        or any(
            tuple(row[name] for name in TRUTH_INPUT_REPRESENTATION_COLUMNS)
            != EXACT42_INPUT_REPRESENTATIONS[row["case_id"]]
            for row in inherited
        )
    ):
        raise ValueError("Truth Exact42 input representation drift")
    batch_values = {
        row["batch_context_representation"] for row in inherited
    }
    evaluation_values = {
        row["evaluation_context_representation"] for row in inherited
    }
    download_values = {
        row["download_result_context_representation"] for row in inherited
    }
    if (
        batch_values != {"None", "object", "{}"}
        or evaluation_values != {"None", "object", "{}"}
        or download_values != {"None", "object", "{}"}
        or any(
            row["candidate_representation"]
            not in {"{}", "object", "instrumented_mapping"}
            or row["batch_context_representation"]
            not in {"None", "object", "{}"}
            or row["evaluation_context_representation"]
            not in {"None", "object", "{}"}
            or row["download_result_context_representation"]
            not in {"None", "object", "{}"}
            or row["stage_authorization_context_representation"]
            not in {
                "None",
                "object",
                "{}",
                "{target:False}",
                "{target:True}",
                "{target:True,training:True,extra:1}",
                "KeyError_mapping",
                "RuntimeError_mapping",
                "ValueError_mapping",
                "alternating_mapping",
            }
            for row in rows
        )
        or tuple(
            rows[60][name]
            for name in TRUTH_INPUT_REPRESENTATION_COLUMNS
        )
        != ("{}", "None", "None", "None", "alternating_mapping")
    ):
        raise ValueError("Truth input representation envelope leakage")


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "shared Exact13 result", "object_identity_preserved"),
        ("identity", "shared dispatch error", "object_identity_preserved"),
        ("identity", "shared constants", "5/5_identity_preserved"),
        ("dispatcher", "signature", "exact_predecessor_match"),
        ("dispatcher", "precedence", "exact_str|known|callable|ready|local_handler"),
        ("dispatcher", "cardinality", "single_rule_only"),
        ("registry", "order", "ADMIT_001_to_ADMIT_014"),
        ("registry", "first thirteen handlers", "13/13_identity_preserved"),
        ("registry", "ADMIT_014 handler", "_evaluate_registered_admit_014"),
        ("registry", "immutability", "MappingProxyType"),
        ("sets", "known", "ADMIT_001_to_ADMIT_015"),
        ("sets", "callable", "ADMIT_001_to_ADMIT_014"),
        ("sets", "adapter ready", "ADMIT_001_to_ADMIT_014"),
        ("sets", "legacy adapter not ready", "empty"),
        ("routing", "precedence", "batch|evaluation|download|candidate|stage_forward|formal|source|oracle|equality|projection"),
        ("candidate", "non-Mapping", "fixed_invalid_Exact13"),
        ("candidate", "key access", "zero"),
        ("source", "Exact9", "type|storage|order|types|reconstruction|invariants"),
        ("source", "validation before oracle", "true"),
        ("oracle", "call count", "exactly_once_after_valid_source"),
        ("oracle", "same stage object", "identity_preserved"),
        ("equality", "Exact9", "exact_type_and_value_all_fields"),
        ("projection", "normalized", "exact_bool_to_lowercase_string"),
        ("projection", "validated candidate", "empty"),
        ("projection", "consumed candidate", "empty"),
        ("projection", "consumed context", "source_consumed_stage_fields"),
        ("truth", "inherited routing", "Exact42_actual_runtime_execution"),
        ("truth", "source negatives", "Exact11_actual_fail_closed"),
        ("truth", "oracle negatives", "Exact8_actual_fail_closed"),
        ("continuity", "predecessor truth", "committed_Exact885_all_passed"),
        ("continuity", "predecessor registry", "committed_Exact39_all_passed"),
        ("issue", "single transition", "coverage_removes_ADMIT_014_only"),
        ("precondition", "PRE_049", "resolved"),
        ("precondition", "counts", "total=51|complete=51|incomplete=0|blocking=0"),
        ("readiness", "current permission", "false"),
        ("readiness", "authorized execution count", "0"),
        ("boundary", "ADMIT_015", "not_implemented_or_registered"),
        ("boundary", "mandatory enforcement", "not_implemented"),
        ("boundary", "combined verdict and aggregation", "not_implemented"),
        ("boundary", "provider network download raw", "not_executed"),
        ("boundary", "model checkpoint dataloader training", "not_modified"),
        ("training", "feature semantics audit", "required_Step12D_smoke_only"),
        ("materializer", "publication", "set_atomic_RENAME_NOREPLACE"),
        ("materializer", "existing exact set", "inode_preserving_noop"),
        ("materializer", "GPFS EINVAL", "fail_closed"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_group": group,
            "contract_item": item,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for index, (group, item, value) in enumerate(definitions, 1)
    ]


def _registry_rows() -> list[dict[str, str]]:
    rows = []
    for index, rule_id in enumerate(KNOWN_RULE_IDS, 1):
        if rule_id in KNOWN_RULE_IDS[:13]:
            expected_identity = (
                f"predecessor.EVALUATOR_REGISTRY[{rule_id!r}]"
            )
            observed_identity = expected_identity
            identity_preserved = (
                EVALUATOR_REGISTRY[rule_id]
                is predecessor.EVALUATOR_REGISTRY[rule_id]
            )
        elif rule_id == ADMISSION_RULE_ID:
            expected_identity = "_evaluate_registered_admit_014"
            observed_identity = getattr(
                EVALUATOR_REGISTRY.get(rule_id), "__name__", ""
            )
            identity_preserved = (
                EVALUATOR_REGISTRY[rule_id]
                is _evaluate_registered_admit_014
            )
        else:
            expected_identity = "not_registered"
            observed_identity = "not_registered"
            identity_preserved = rule_id not in EVALUATOR_REGISTRY
        registered = rule_id in EVALUATOR_REGISTRY
        callable_discovered = rule_id in CALLABLE_DISCOVERED_RULE_IDS
        adapter_ready = rule_id in ADAPTER_READY_RULE_IDS
        expected_registered = rule_id != "ADMIT_015"
        expected_callable = rule_id != "ADMIT_015"
        expected_ready = rule_id != "ADMIT_015"
        passed = (
            identity_preserved
            and registered is expected_registered
            and callable_discovered is expected_callable
            and adapter_ready is expected_ready
        )
        rows.append(
            {
                "audit_order": str(index),
                "rule_id": rule_id,
                "expected_handler_identity": expected_identity,
                "observed_handler_identity": observed_identity,
                "identity_preserved": str(identity_preserved).lower(),
                "registered": str(registered).lower(),
                "callable_discovered": str(callable_discovered).lower(),
                "adapter_ready": str(adapter_ready).lower(),
                "audit_passed": str(passed).lower(),
            }
        )
    shared = (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    )
    for name in shared:
        preserved = globals()[name] is getattr(predecessor, name)
        rows.append(
            {
                "audit_order": str(len(rows) + 1),
                "rule_id": f"SHARED:{name}",
                "expected_handler_identity": "predecessor_exact_object",
                "observed_handler_identity": "predecessor_exact_object",
                "identity_preserved": str(preserved).lower(),
                "registered": "n/a",
                "callable_discovered": "n/a",
                "adapter_ready": "n/a",
                "audit_passed": str(preserved).lower(),
            }
        )
    import inspect

    metadata = (
        (
            "DISPATCHER:signature",
            inspect.signature(evaluate_admission_rule)
            == inspect.signature(predecessor.evaluate_admission_rule),
        ),
        (
            "DISPATCHER:local_registry",
            evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"]
            is EVALUATOR_REGISTRY,
        ),
        ("REGISTRY:mapping_proxy", type(EVALUATOR_REGISTRY) is MappingProxyType),
        ("RULE_NAMES:mapping_proxy", type(RULE_NAMES) is MappingProxyType),
        ("ADAPTER_IDS:mapping_proxy", type(ADAPTER_IDS) is MappingProxyType),
    )
    for item, passed in metadata:
        rows.append(
            {
                "audit_order": str(len(rows) + 1),
                "rule_id": item,
                "expected_handler_identity": "true",
                "observed_handler_identity": str(passed).lower(),
                "identity_preserved": str(passed).lower(),
                "registered": "n/a",
                "callable_discovered": "n/a",
                "adapter_ready": "n/a",
                "audit_passed": str(passed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    states = (
        ("public_closure_pure_memory", True),
        ("shared_exact13_identity_preserved", True),
        ("first_thirteen_handler_identity_preserved", True),
        ("formal_exactly_once_after_routing", True),
        ("oracle_exactly_once_after_source", True),
        ("source_exact9_attested", True),
        ("oracle_exact9_attested", True),
        ("full_exact9_equivalence_required", True),
        ("bool_lowercase_projection", True),
        ("candidate_key_access_zero", True),
        ("adapter_stage_key_access_zero", True),
        ("pre_049_resolved", True),
        ("canonical_runtime", True),
        ("deterministic_materialization", True),
        ("adapter_design_simulator_runtime_call", False),
        ("admit_015_implemented", False),
        ("admit_015_registered", False),
        ("mandatory_enforcement_implemented", False),
        ("provider_mapping_implemented", False),
        ("network_executed", False),
        ("download_executed", False),
        ("raw_accessed", False),
        ("combined_verdict_implemented", False),
        ("cross_rule_aggregation_implemented", False),
        ("model_modified", False),
        ("checkpoint_modified", False),
        ("dataloader_modified", False),
        ("training_executed", False),
        ("current_permission", False),
        ("authorized_execution_count_nonzero", False),
        ("current_main_staged", False),
        ("current_main_committed_or_pushed", False),
    )
    return [
        {
            "audit_order": str(index),
            "audit_item": item,
            "expected_state": str(state).lower(),
            "observed_state": str(state).lower(),
            "safety_passed": "true",
        }
        for index, (item, state) in enumerate(states, 1)
    ]


TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_standalone_evaluator_interface_implemented",
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_rule_logic_implemented",
    "admit_014_unified_adapter_contract_frozen",
    "admit_014_unified_adapter_implemented",
    "admit_014_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "first_thirteen_handler_identity_preserved",
    "shared_exact13_identity_preserved",
    "public_single_rule_dispatcher_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_015_rule_logic_implemented",
    "admit_015_registered_in_engine",
    "mandatory_pre_download_authorization_enforcement_implemented",
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
    if len(rows) != 30 or len(matches) != 1:
        raise ValueError("Exact30 coverage issue drift")
    coverage = matches[0]
    before = dict(coverage)
    if (
        coverage["affected_rules"] != "ADMIT_014|ADMIT_015"
        or coverage["successor_effective_status"] != "open"
    ):
        raise ValueError("coverage predecessor state drift")
    coverage["affected_rules"] = "ADMIT_015"
    coverage["integration_transition"] = (
        "unified_dispatch_runtime_with_admit_001_to_014_implemented_v1"
    )
    coverage["successor_transition_stage"] = STAGE
    coverage["successor_transition_action"] = (
        "admit_014_removed_from_open_unified_runtime_coverage"
    )
    coverage["successor_transition_evidence"] = (
        "Exact14_registry_and_unified_single_rule_dispatch"
    )
    changed = {
        key for key in coverage if coverage[key] != before[key]
    }
    if changed != {
        "affected_rules",
        "integration_transition",
        "successor_transition_stage",
        "successor_transition_action",
        "successor_transition_evidence",
    }:
        raise ValueError("coverage transition exceeded authorization")
    return rows


def build_runtime_state(
    snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    _assert_canonical_evidence_runtime()
    frozen = (
        build_frozen_source_snapshot() if snapshot is None else snapshot
    )
    if not validate_frozen_source_snapshot(frozen):
        raise ValueError("invalid Exact20 snapshot")
    predecessor_truth = _csv_rows(
        _source_record(
            frozen,
            "covapie_admit_001_to_013_dispatch_truth_matrix.csv",
        ).content
    )
    predecessor_registry = _csv_rows(
        _source_record(
            frozen,
            "covapie_admit_001_to_013_registry_and_identity_audit.csv",
        ).content
    )
    adapter_routing = _csv_rows(
        _source_record(
            frozen,
            "covapie_admit_014_stage_authorization_projection_and_context_routing_matrix.csv",
        ).content
    )
    adapter_manifest = _json_object(
        _source_record(
            frozen,
            "covapie_admit_014_unified_adapter_contract_manifest.json",
        ).content
    )
    issue_rows = _csv_rows(
        _source_record(
            frozen,
            "covapie_admit_014_unified_adapter_issue_readiness_inventory.csv",
        ).content,
        ISSUE_COLUMNS,
    )
    if (
        len(predecessor_truth) != 885
        or any(row["case_passed"] != "true" for row in predecessor_truth)
        or len(predecessor_registry) != 39
        or any(
            row["audit_passed"] != "true"
            for row in predecessor_registry
        )
        or len(adapter_routing) != 42
        or any(row["case_passed"] != "true" for row in adapter_routing)
        or adapter_manifest.get("precondition_transition", {}).get(
            "remaining_open_precondition_ids"
        )
        != ["PRE_049"]
    ):
        raise ValueError("predecessor evidence drift")
    design_specs = admit014_adapter_design._routing_case_specs()
    if (
        len(design_specs) != 42
        or tuple(spec["case_id"] for spec in design_specs)
        != tuple(row["case_id"] for row in adapter_routing)
    ):
        raise ValueError("adapter Exact42 identity drift")
    truth_rows = [
        *(_execute_exact42_case(spec) for spec in design_specs),
        *_source_negative_rows(),
        *_oracle_negative_rows(),
        *_dispatcher_and_predecessor_rows(),
    ]
    for index, row in enumerate(truth_rows, 1):
        row["case_order"] = str(index)
    _validate_truth_input_representations(truth_rows)
    group_counts = dict(
        sorted(Counter(row["case_group"] for row in truth_rows).items())
    )
    contract_rows = _contract_rows()
    registry_rows = _registry_rows()
    safety_rows = _safety_rows()
    updated_issues = _updated_issue_rows(issue_rows)
    if (
        group_counts
        != {
            "admit014_inherited_exact42_runtime": 42,
            "admit014_oracle_negative": 8,
            "admit014_source_negative": 11,
            "predecessor_representative_dispatch": 13,
            "public_dispatch": 5,
        }
        or len(truth_rows) != 79
        or any(row["case_passed"] != "true" for row in truth_rows)
        or any(
            row["contract_passed"] != "true" for row in contract_rows
        )
        or any(row["audit_passed"] != "true" for row in registry_rows)
        or any(row["safety_passed"] != "true" for row in safety_rows)
        or len(updated_issues) != 30
    ):
        raise ValueError("Exact14 runtime state failed closed")
    issue_map = {row["issue_id"]: row for row in updated_issues}
    required_open = (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    )
    if (
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        != "ADMIT_015"
        or any(
            issue_map[name]["successor_effective_status"] != "open"
            for name in required_open
        )
    ):
        raise ValueError("open issue semantics drift")
    return {
        "snapshot": frozen,
        "candidate_attestation": _candidate_source_attestation(),
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": group_counts,
        "registry_rows": registry_rows,
        "safety_rows": safety_rows,
        "issue_rows": updated_issues,
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
            raise ValueError("output CSV schema drift")
        writer.writerow(row)
    return stream.getvalue().encode()


def _source_digests() -> tuple[str, str]:
    paths = [path for path, _ in SOURCE_BOUNDARY]
    pairs = [[path, digest] for path, digest in SOURCE_BOUNDARY]
    return (
        _sha(json.dumps(paths, separators=(",", ":")).encode()),
        _sha(json.dumps(pairs, separators=(",", ":")).encode()),
    )


def _manifest_payload(
    state: Mapping[str, Any],
    output_sha256: Mapping[str, str],
) -> dict[str, Any]:
    snapshot = state["snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    path_digest, pair_digest = _source_digests()
    import inspect

    manifest = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_parent": EXPECTED_BASE_PARENT,
        "expected_base_tree": EXPECTED_BASE_TREE,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "canonical_evidence_python_implementation": (
            CANONICAL_PYTHON_IMPLEMENTATION
        ),
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": (
            AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE
        ),
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "exact14_identity": (
            "ADMIT_001_to_ADMIT_014_unified_single_rule_runtime_v1"
        ),
        "exact13_predecessor_identity": (
            "ADMIT_001_to_ADMIT_013_unified_single_rule_runtime_v1"
        ),
        "source_boundary_name": (
            "fixed_ordered_exact20_committed_source_boundary"
        ),
        "source_input_count": 20,
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
                "base_tree_mode": record.base_tree_mode,
                "base_tree_blob": record.base_tree_blob,
                "index_mode": record.index_mode,
                "index_blob": record.index_blob,
                "index_stage": record.index_stage,
                "filesystem_regular": True,
                "non_symlink": True,
                "parent_chain_non_symlink": True,
                "safe_descendant": True,
                "pinned_fd_read": True,
                "post_read_identity_verified": True,
                "final_leaf_identity_verified": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_validation_before_candidate_or_output_read": True,
        "candidate_production_source_attestation": state[
            "candidate_attestation"
        ],
        "public_marker": PUBLIC_MARKER,
        "public_definition_count": 11,
        "public_definitions": list(PUBLIC_DEFINITIONS),
        "runtime_dependency_imports": [
            "exact13_unified_runtime_predecessor",
            "admit014_standalone_evaluator",
            "admit014_committed_independent_formal_interface_oracle",
        ],
        "adapter_design_simulator_called_by_public_runtime": False,
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
        "public_dispatch_signature": str(
            inspect.signature(evaluate_admission_rule)
        ),
        "public_dispatch_signature_matches_exact13": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "callable_discovered",
            "adapter_ready",
            "successor_local_registry_handler",
        ],
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(
            CALLABLE_DISCOVERED_RULE_IDS
        ),
        "adapter_ready_rule_ids": list(ADAPTER_READY_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "known_not_registered_rule_ids": ["ADMIT_015"],
        "registered_rule_count": 14,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_thirteen_handler_identity_reused": {
            rule_id: EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:13]
        },
        "shared_exact13_identity_preserved": True,
        "predecessor_dispatcher_unchanged": True,
        "successor_dispatcher_distinct": True,
        "admit_014_handler": "_evaluate_registered_admit_014",
        "admit_014_handler_signature": str(
            inspect.signature(_evaluate_registered_admit_014)
        ),
        "admit_014_source_fields": list(ADMIT_014_SOURCE_FIELDS),
        "admit_014_routing_precedence": [
            "batch_context_must_be_none",
            "evaluation_context_must_be_none",
            "download_result_context_must_be_none",
            "candidate_record_mapping_validation",
            "stage_authorization_context_forwarded_same_object",
            "formal_evaluator_exactly_once",
            "standalone_source_exact9_validation",
            "independent_oracle_exactly_once",
            "full_exact9_exact_type_value_equality",
            "exact9_to_exact13_projection",
        ],
        "admit_014_candidate_mapping_invalid_reason": (
            "ADMIT_014_CANDIDATE_RECORD_MAPPING_INVALID"
        ),
        "admit_014_candidate_invalid_call_counts": {
            "formal": 0,
            "oracle": 0,
            "candidate_key_access": 0,
            "stage_target_access": 0,
        },
        "admit_014_source_type": "Admit014EvaluationResult",
        "admit_014_source_type_invalid_reason": (
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        ),
        "admit_014_source_invariant_invalid_reason": (
            "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        ),
        "admit_014_source_prevalidation_before_oracle": True,
        "admit_014_oracle": (
            "classify_admit_014_formal_evaluator_interface_design"
        ),
        "admit_014_oracle_result_type": (
            "Admit014EvaluationResultContractDesign"
        ),
        "admit_014_source_oracle_full_exact9_equality_required": True,
        "admit_014_exact13_projection": {
            "normalized_values": (
                "canonical exact bool pair to lowercase string pair"
            ),
            "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": (
                "source.consumed_stage_authorization_fields"
            ),
        },
        "contract_row_count": len(state["contract_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "truth_input_representation_columns": list(
            TRUTH_INPUT_REPRESENTATION_COLUMNS
        ),
        "truth_input_representation_semantics_independently_verified": True,
        "truth_trace_columns": [
            "expected_call_order",
            "observed_call_order",
            "expected_stage_context_identity_preserved",
            "observed_stage_context_identity_preserved",
            "adapter_stage_target_access_count",
            "formal_stage_target_access_count",
            "oracle_stage_target_access_count",
        ],
        "truth_trace_semantics_independently_verified": True,
        "admit_014_inherited_exact42_runtime_case_count": 42,
        "admit_014_source_negative_case_count": 11,
        "admit_014_oracle_negative_case_count": 8,
        "predecessor_representative_dispatch_count": 13,
        "predecessor_committed_truth_case_count": 885,
        "predecessor_committed_registry_audit_count": 39,
        "registry_identity_audit_row_count": len(state["registry_rows"]),
        "safety_audit_row_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_transition_count": 1,
        "issue_transition_id": (
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
        ),
        "issue_coverage_before": ["ADMIT_014", "ADMIT_015"],
        "issue_coverage_after": ["ADMIT_015"],
        "precondition_transition": {
            "row_count": 51,
            "complete_count": 51,
            "incomplete_count": 0,
            "implementation_blocking_count": 0,
            "resolved_precondition_ids": ["PRE_049"],
            "resolution": (
                "ADMIT_014 handler, immutable Exact14 registry and unified "
                "single-rule dispatcher implemented with first13 identity "
                "preservation"
            ),
            "remaining_open_precondition_ids": [],
        },
        "remaining_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "readiness": readiness,
        "current_permission": False,
        "synthetic_true_case_changes_current_permission": False,
        "authorized_admit_014_download_execution_count": 0,
        "admit_015_implemented": False,
        "admit_015_registered_in_engine": False,
        "mandatory_pre_download_authorization_enforcement_implemented": False,
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "ready_for_training": False,
        "step12d_is_final_training_feature_contract": False,
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check; historical "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain subject to explicit audit"
        ),
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "all_payloads_built_before_mutation": True,
            "exact_six_allowlist": True,
            "pinned_parent_root_staging_leaf": True,
            "exclusive_create": True,
            "file_fsync": True,
            "staging_directory_fsync": True,
            "renameat2_RENAME_NOREPLACE": True,
            "GPFS_EINVAL_fail_closed": True,
            "parent_fsync": True,
            "destination_name_inode_binding": True,
            "complete_set_postverify": True,
            "all_leaf_descriptors_retained_through_final_traversal": True,
            "staging_lexical_binding_verified": True,
            "cleanup_ownership_verified_before_delete": True,
            "existing_exact_set_inode_preserving_noop": True,
            "mismatch_repair_forbidden": True,
        },
        "evidence_lifecycle_hardening": {
            "exact10_lifecycle_exact_inventory": True,
            "source_and_output_full_identity_post_traversal": True,
            "source_and_output_final_leaf_identity_post_traversal": True,
            "manifest_duplicate_and_exact_schema_rejection": True,
            "publisher_destination_binding_rechecks": True,
            "checker_exact42_specs_owned_without_project_checker_import": True,
            "artifact_semantics_rebuilt_after_sha_verification": True,
            "successor_regression_historical_deselection_count": 4,
        },
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
    manifest.update(readiness)
    return manifest


def build_artifacts(
    state: Mapping[str, Any] | None = None,
) -> dict[str, bytes]:
    _assert_canonical_evidence_runtime()
    runtime_state = build_runtime_state() if state is None else state
    if (
        type(runtime_state) is not dict
        or runtime_state.get("all_checks_passed") is not True
        or not validate_frozen_source_snapshot(runtime_state.get("snapshot"))
    ):
        raise ValueError("runtime state invalid")
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(
            CONTRACT_COLUMNS, runtime_state["contract_rows"]
        ),
        TRUTH_FILENAME: _csv_bytes(
            TRUTH_COLUMNS, runtime_state["truth_rows"]
        ),
        REGISTRY_FILENAME: _csv_bytes(
            REGISTRY_COLUMNS, runtime_state["registry_rows"]
        ),
        SAFETY_FILENAME: _csv_bytes(
            SAFETY_COLUMNS, runtime_state["safety_rows"]
        ),
        ISSUE_FILENAME: _csv_bytes(
            ISSUE_COLUMNS, runtime_state["issue_rows"]
        ),
    }
    output_sha = {
        name: _sha(content) for name, content in payloads.items()
    }
    manifest = _manifest_payload(runtime_state, output_sha)
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


@dataclass(frozen=True)
class OutputMaterializationPlan:
    root: Path
    parent: Path
    root_name: str
    parent_identity: tuple[int, int, int]
    root_identity: tuple[int, int, int] | None
    leaf_identities: tuple[
        tuple[str, tuple[int, int, int, int, int, int]], ...
    ]


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


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output parent chain unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("output parent chain escaped")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("output parent resolved drift")


def _inspect_output_target_read_only(
    output_root: Path,
    repo_root: Path = REPO_ROOT,
) -> OutputMaterializationPlan:
    candidate = Path(output_root)
    repo = Path(os.path.abspath(repo_root))
    if candidate.is_absolute():
        root = Path(os.path.abspath(candidate))
        anchor = Path(root.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape")
        root = repo / candidate
        anchor = repo
    if not root.name:
        raise ValueError("output root invalid")
    parent = root.parent
    _assert_real_parent_chain(parent, anchor)
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(
            root,
            parent,
            root.name,
            parent_identity,
            None,
            (),
        )
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if len(names) != 6 or set(names) != set(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        item = os.lstat(root / name)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_CANDIDATE_BYTES
        ):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _full_identity(item)))
    return OutputMaterializationPlan(
        root,
        parent,
        root.name,
        parent_identity,
        _identity(root_item),
        tuple(leaves),
    )


def _assert_output_parent(
    plan: OutputMaterializationPlan,
    parent_fd: int,
) -> None:
    lexical = os.lstat(plan.parent)
    if (
        _identity(lexical) != plan.parent_identity
        or _identity(os.fstat(parent_fd)) != plan.parent_identity
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
    ):
        raise ValueError("output parent binding drift")


def _read_at(
    directory_fd: int,
    name: str,
    expected: tuple[int, int, int, int, int, int],
) -> bytes:
    before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if (
        _full_identity(before) != expected
        or not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or before.st_size > MAX_CANDIDATE_BYTES
    ):
        raise ValueError("output leaf drift")
    descriptor = os.open(name, READ_FLAGS, dir_fd=directory_fd)
    try:
        if _full_identity(os.fstat(descriptor)) != expected:
            raise ValueError("output leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _full_identity(os.fstat(descriptor)) != expected
            or _full_identity(
                os.stat(
                    name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            )
            != expected
        ):
            raise ValueError("output leaf changed")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _verify_complete_set(
    root_fd: int,
    payloads: Mapping[str, bytes],
    expected: Mapping[
        str, tuple[int, int, int, int, int, int]
    ]
    | None = None,
) -> dict[str, tuple[int, int, int, int, int, int]]:
    root_identity = _full_identity(os.fstat(root_fd))
    names = tuple(os.listdir(root_fd))
    if len(names) != 6 or set(names) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    identities = (
        {
            name: _full_identity(
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            )
            for name in OUTPUT_FILES
        }
        if expected is None
        else dict(expected)
    )
    if set(identities) != set(OUTPUT_FILES):
        raise ValueError("output identity inventory drift")
    descriptors: dict[str, int] = {}
    observed: dict[str, bytes] = {}
    try:
        for name in OUTPUT_FILES:
            before = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            if (
                _full_identity(before) != identities[name]
                or not stat.S_ISREG(before.st_mode)
                or stat.S_ISLNK(before.st_mode)
                or before.st_size > MAX_CANDIDATE_BYTES
            ):
                raise ValueError("complete output leaf drift")
            descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
            descriptors[name] = descriptor
            if _full_identity(os.fstat(descriptor)) != identities[name]:
                raise ValueError("complete output stat/open race")
        for name in OUTPUT_FILES:
            chunks = []
            while True:
                chunk = os.read(descriptors[name], 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            observed[name] = b"".join(chunks)
        second_names = tuple(os.listdir(root_fd))
        if (
            len(second_names) != 6
            or set(second_names) != set(OUTPUT_FILES)
        ):
            raise ValueError("complete output second inventory drift")
        for name in OUTPUT_FILES:
            lexical = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            actual = observed[name]
            if (
                _full_identity(os.fstat(descriptors[name]))
                != identities[name]
                or _full_identity(lexical) != identities[name]
                or not stat.S_ISREG(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
                or actual != payloads[name]
                or _sha(actual) != _sha(payloads[name])
            ):
                raise ValueError("complete output payload/binding drift")
        if _full_identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("complete output root drift")
        for name in OUTPUT_FILES:
            if (
                _full_identity(
                    os.stat(
                        name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                )
                != identities[name]
                or _full_identity(os.fstat(descriptors[name]))
                != identities[name]
            ):
                raise ValueError("complete output final leaf drift")
        return identities
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def _verify_destination_binding(
    plan: OutputMaterializationPlan,
    parent_fd: int,
    root_fd: int,
    expected_root: tuple[int, int, int],
    payloads: Mapping[str, bytes],
    leaf_identities: Mapping[
        str, tuple[int, int, int, int, int, int]
    ],
) -> None:
    _assert_output_parent(plan, parent_fd)
    destination = os.stat(
        plan.root_name,
        dir_fd=parent_fd,
        follow_symlinks=False,
    )
    if (
        _identity(destination) != expected_root
        or _identity(os.fstat(root_fd)) != expected_root
        or not stat.S_ISDIR(destination.st_mode)
        or stat.S_ISLNK(destination.st_mode)
    ):
        raise ValueError("destination name/inode binding drift")
    _verify_complete_set(root_fd, payloads, leaf_identities)
    _assert_output_parent(plan, parent_fd)
    if (
        _identity(
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        )
        != expected_root
        or _identity(os.fstat(root_fd)) != expected_root
    ):
        raise ValueError("destination postverify binding drift")


def _rename_noreplace(
    parent_fd: int,
    source: str,
    target: str,
) -> None:
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


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _assert_staging_name_binding(
    plan: OutputMaterializationPlan,
    parent_fd: int,
    staging_name: str,
    root_fd: int,
    staging_identity: tuple[int, int, int],
) -> None:
    _assert_output_parent(plan, parent_fd)
    lexical = os.stat(
        staging_name,
        dir_fd=parent_fd,
        follow_symlinks=False,
    )
    if (
        not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or _identity(lexical) != staging_identity
        or _identity(os.fstat(root_fd)) != staging_identity
    ):
        raise ValueError("staging lexical name/inode binding drift")
    _assert_output_parent(plan, parent_fd)


def _cleanup_owned_staging(
    plan: OutputMaterializationPlan,
    parent_fd: int,
    root_fd: int | None,
    staging_name: str | None,
    staging_identity: tuple[int, int, int] | None,
    staged: Mapping[
        str, tuple[int, int, int, int, int, int]
    ],
) -> int | None:
    if (
        root_fd is None
        or staging_name is None
        or staging_identity is None
    ):
        return root_fd
    try:
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        if set(os.listdir(root_fd)) != set(staged):
            return root_fd
        for name, identity in staged.items():
            if (
                _full_identity(
                    os.stat(
                        name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                )
                != identity
            ):
                return root_fd
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        for name in staged:
            os.unlink(name, dir_fd=root_fd)
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        os.close(root_fd)
        root_fd = None
        os.rmdir(staging_name, dir_fd=parent_fd)
    except BaseException:
        if root_fd is not None:
            try:
                lexical = os.stat(
                    staging_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except BaseException:
                lexical = None
            if (
                lexical is None
                or _identity(lexical) != staging_identity
                or not stat.S_ISDIR(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
            ):
                try:
                    os.close(root_fd)
                except OSError:
                    pass
                root_fd = None
    return root_fd


def _materialize_set(
    plan: OutputMaterializationPlan,
    payloads: Mapping[str, bytes],
) -> None:
    _assert_canonical_evidence_runtime()
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or any(type(value) is not bytes for value in payloads.values())
    ):
        raise ValueError("output payload inventory drift")
    parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    staging_name: str | None = None
    staging_identity: tuple[int, int, int] | None = None
    staged: dict[str, tuple[int, int, int, int, int, int]] = {}
    try:
        _assert_output_parent(plan, parent_fd)
        if plan.root_identity is not None:
            destination = os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            if (
                _identity(destination) != plan.root_identity
                or not stat.S_ISDIR(destination.st_mode)
                or stat.S_ISLNK(destination.st_mode)
            ):
                raise ValueError("output root identity changed")
            root_fd = os.open(
                plan.root_name,
                DIRECTORY_FLAGS,
                dir_fd=parent_fd,
            )
            if _identity(os.fstat(root_fd)) != plan.root_identity:
                raise ValueError("output root descriptor drift")
            try:
                _verify_destination_binding(
                    plan,
                    parent_fd,
                    root_fd,
                    plan.root_identity,
                    payloads,
                    dict(plan.leaf_identities),
                )
            except ValueError as error:
                raise ValueError(
                    "existing output differs; repair forbidden"
                ) from error
            os.fsync(root_fd)
            _verify_destination_binding(
                plan,
                parent_fd,
                root_fd,
                plan.root_identity,
                payloads,
                dict(plan.leaf_identities),
            )
            return
        try:
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = (
                f".exact14-runtime-stage-{secrets.token_hex(16)}"
            )
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        root_fd = os.open(
            staging_name,
            DIRECTORY_FLAGS,
            dir_fd=parent_fd,
        )
        staging_identity = _identity(os.fstat(root_fd))
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        if os.listdir(root_fd):
            raise ValueError("staging directory not empty")
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        for name, content in payloads.items():
            descriptor = os.open(
                name,
                WRITE_FLAGS,
                0o600,
                dir_fd=root_fd,
            )
            try:
                _write_all(descriptor, content)
                os.fsync(descriptor)
                staged[name] = _full_identity(os.fstat(descriptor))
            finally:
                os.close(descriptor)
            if _read_at(root_fd, name, staged[name]) != content:
                raise ValueError("staged output mismatch")
        _verify_complete_set(root_fd, payloads, staged)
        os.fsync(root_fd)
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        try:
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        _assert_staging_name_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        _verify_destination_binding(
            plan,
            parent_fd,
            root_fd,
            staging_identity,
            payloads,
            staged,
        )
        os.fsync(parent_fd)
        _verify_destination_binding(
            plan,
            parent_fd,
            root_fd,
            staging_identity,
            payloads,
            staged,
        )
        os.fsync(root_fd)
        _verify_destination_binding(
            plan,
            parent_fd,
            root_fd,
            staging_identity,
            payloads,
            staged,
        )
    except BaseException:
        root_fd = _cleanup_owned_staging(
            plan,
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
        os.close(parent_fd)


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic runtime-evidence files."""
    _assert_canonical_evidence_runtime()
    snapshot = build_frozen_source_snapshot(
        repo_root,
        head_ref=head_ref,
    )
    state = build_runtime_state(snapshot)
    payloads = build_artifacts(state)
    plan = _inspect_output_target_read_only(output_root, repo_root)
    _materialize_set(plan, payloads)
    return {
        "state": state,
        "manifest": json.loads(payloads[MANIFEST_FILENAME]),
        "output_root": plan.root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1()
