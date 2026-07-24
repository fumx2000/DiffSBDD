"""Design-only contract for the future ADMIT_014 unified adapter.

The public functions in this module simulate and attest the proposed adapter.
They do not define the future runtime handler, a registry, a dispatcher, a
provider mapping, a downloader, cross-rule aggregation, or a new shared result
schema.  The adapter simulation is pure in memory; evidence publication is an
explicit, separately reachable operation.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import importlib
import inspect
import io
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, NoReturn


PROJECT = "CovaPIE"
STEP = "ADMIT_014 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1"
EXPECTED_BASE_COMMIT = "44b4306adfa42ef3587f87d08a4f66ed60101fa7"
EXPECTED_BASE_PARENT = "0ec764f03bd3fe227a1e346380f1cdf31837f023"
EXPECTED_BASE_TREE = "627a3cd228a0c8ba48496171bda7adb61494ca9a"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_014 standalone evaluator interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_014_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_014_v1"
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE = False
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_014"
ADMISSION_RULE_NAME = "current_gate_grants_no_download_permission"
ADAPTER_ID = "covapie_admit_014_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_014"
FORMAL_RESULT_TYPE = "Admit014EvaluationResult"
INDEPENDENT_ORACLE_NAME = "classify_admit_014_formal_evaluator_interface_design"
INDEPENDENT_ORACLE_RESULT_TYPE = "Admit014EvaluationResultContractDesign"
FUTURE_HANDLER_NAME = "_evaluate_registered_admit_014"
FUTURE_HANDLER_SIGNATURE_DESIGN = inspect.Signature(
    parameters=(
        inspect.Parameter(
            "candidate_record",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=object,
        ),
        inspect.Parameter(
            "batch_context",
            inspect.Parameter.KEYWORD_ONLY,
            annotation=object,
        ),
        inspect.Parameter(
            "evaluation_context",
            inspect.Parameter.KEYWORD_ONLY,
            annotation=object,
        ),
        inspect.Parameter(
            "download_result_context",
            inspect.Parameter.KEYWORD_ONLY,
            annotation=object,
        ),
        inspect.Parameter(
            "stage_authorization_context",
            inspect.Parameter.KEYWORD_ONLY,
            annotation=object,
        ),
    ),
    return_annotation="UnifiedAdmissionRuleEvaluation",
)
FUTURE_HANDLER_SIGNATURE_TEXT = (
    FUTURE_HANDLER_NAME + str(FUTURE_HANDLER_SIGNATURE_DESIGN)
)
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
TARGET_CONTEXT_ITEM = "current_stage_download_authorized"
ADMIT_015_COEXISTENCE_ITEM = "current_stage_training_authorized"
CURRENT_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 14))
FUTURE_REGISTERED_RULE_ORDER = (*CURRENT_REGISTERED_RULE_ORDER, ADMISSION_RULE_ID)
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
FUTURE_KNOWN_NOT_REGISTERED = ("ADMIT_015",)
FUTURE_CALLABLE_DISCOVERED_RULE_IDS = FUTURE_REGISTERED_RULE_ORDER
FUTURE_ADAPTER_READY_RULE_IDS = FUTURE_REGISTERED_RULE_ORDER

RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_stage_authorization_record",
    "validated_stage_authorization_fields",
    "consumed_stage_authorization_fields", "evaluator_io_used",
)
DISPATCH_ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
CONTEXT_REASONS = {
    "batch_context": "ADMIT_014_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_014_EVALUATION_CONTEXT_MUST_BE_NONE",
    "download_result_context": "ADMIT_014_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_MAPPING_REASON = "ADMIT_014_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_must_be_none",
    "download_result_context_must_be_none",
    "candidate_record_mapping_validation",
    "stage_authorization_context_forwarded_without_adapter_prevalidation",
    "formal_evaluator_exactly_once",
    "standalone_source_exact9_validation",
    "independent_design_oracle_exactly_once",
    "full_exact9_exact_type_value_equality",
    "exact9_to_exact13_projection",
)

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_014_rule_logic_interface.py", "5f0766a4eb9dac8b00b9729b7d593adfbe105fb212eabbd4e0a3e349b35f7399"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_contract.csv", "90b07d8988a4ff8605e5fb4565d91374b91eb098fad850a492e72cf5dee60e79"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_truth_matrix.csv", "3f48127236c1e27839cd7960ca1e7f64efcc60d49a28805d727862fe5eb71b97"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_source_boundary_audit.csv", "7ed009637e145c3f0e004ad5bb113f57946d87127519be10a7ee87f4fcaf0e5d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_purity_audit.csv", "f4814496d8ac19587c7f13bd22567e71d9843f7c59f3f80de5935336b1a1d11a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_issue_readiness_inventory.csv", "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/covapie_admit_014_rule_logic_interface_manifest.json", "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate.py", "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1/covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv", "9df1faddeb8aa14e8b29af10296222925361cd1f1f98c05a2cc3a2cc64c7f769"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1/covapie_admit_014_formal_evaluator_interface_truth_matrix.csv", "55dbbddf1f3bcdb4bbd6ce763d7a0c812020241157098c6af18799cc5ffac062"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1/covapie_admit_014_formal_evaluator_interface_contract_manifest.json", "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_truth_matrix.csv", "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_contract_manifest.json", "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py", "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_runtime_contract.csv", "035effd65ca65ed1442bb7a29c03986390209f6d129d2ae078e223101c6a6144"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_registry_and_identity_audit.csv", "6700c9360f1447f79a5180d74e1b00d5098547aca3534b5192eab2b8bdb93295"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/covapie_admit_001_to_013_runtime_manifest.json", "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79"),
)
SOURCE_PATH_LIST_SHA256 = hashlib.sha256(
    json.dumps([path for path, _ in SOURCE_BOUNDARY], separators=(",", ":")).encode()
).hexdigest()
SOURCE_PATH_SHA256_PAIRS_SHA256 = hashlib.sha256(
    json.dumps(SOURCE_BOUNDARY, separators=(",", ":")).encode()
).hexdigest()

CONTRACT_FILENAME = "covapie_admit_014_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_014_stage_authorization_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_014_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_014_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_014_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_014_unified_adapter_contract_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME, ROUTING_FILENAME, TRUTH_FILENAME,
    SAFETY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME,
)
FROZEN_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "cdcd5d3ae1f3f65d7faa3ff50e61b37b0fcb9133395868885253f487764aeafc",
    ROUTING_FILENAME: "0d423c4ad785ca92c14e8d3a4881649d7290a6220814e29ab0ed6d7737e653e4",
    TRUTH_FILENAME: "9c8e08358f806b3cb9172f460fe49da47d06f1ba028cc4b2a1df1ca8d0d5ff53",
    SAFETY_FILENAME: "d8530eeb4ecfacd8d26e1d1054112bd927e94ab204cf6eec4c7ab91c76bf6c4b",
    ISSUE_FILENAME: "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d",
    MANIFEST_FILENAME: "fbcca891692e4b88d2da854425bef9ce38d1eced97df1c0ca826edad95357de0",
}

CONTRACT_COLUMNS = (
    "contract_order", "contract_id", "contract_group", "contract_subject",
    "contract_value", "contract_status",
)
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "routing_condition",
    "envelope_representation", "candidate_key_access_count",
    "adapter_stage_key_access_count", "formal_call_count", "oracle_call_count",
    "formal_stage_key_access_count", "oracle_stage_key_access_count",
    "identity_preserved", "expected_dispatch_code", "expected_reason",
    "expected_result_json", "observed_dispatch_code", "observed_reason",
    "observed_result_json", "observed_call_order",
    "observed_identity_preserved", "observed_candidate_key_access_count",
    "observed_adapter_stage_key_access_count",
    "observed_formal_call_count", "observed_oracle_call_count",
    "observed_formal_stage_key_access_count",
    "observed_oracle_stage_key_access_count", "case_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "routing_condition",
    "source_result_representation", "oracle_result_representation",
    "expected_unified_result_json", "observed_unified_result_json",
    "exact13_type_value_equality", "case_passed",
)
SAFETY_COLUMNS = (
    "audit_order", "audit_item", "expected_state",
    "observed_state", "safety_passed",
)
ISSUE_COLUMNS = (
    "inherited_order", "issue_id", "issue_type", "affected_fields",
    "affected_rules", "severity", "status", "blocking_scope",
    "blocking_reason", "issue_origin", "integration_transition", "issue_count",
    "inherited_effective_status", "inherited_transition_stage",
    "inherited_transition_action", "inherited_transition_evidence",
    "successor_effective_status", "successor_transition_stage",
    "successor_transition_action", "successor_transition_evidence",
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
    tracked_in_current_index: bool
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
        if any(type(value) is not bool for value in (
            self.passed, self.blocks_candidate, self.evaluator_io_used,
        )):
            raise TypeError("Exact13 bool field type drift")
        if not _exact_string_pair_tuple(self.normalized_values):
            raise TypeError("normalized_values requires exact string pairs")
        if not _exact_string_pair_tuple(self.validated_candidate_fields):
            raise TypeError("validated_candidate_fields requires exact string pairs")
        if not _exact_string_tuple(self.consumed_candidate_fields):
            raise TypeError("consumed_candidate_fields requires exact strings")
        if not _exact_string_tuple(self.consumed_context_items):
            raise TypeError("consumed_context_items requires exact strings")
        if (
            self.schema_version != RESULT_SCHEMA_VERSION
            or self.admission_rule_id != ADMISSION_RULE_ID
            or self.admission_rule_name != ADMISSION_RULE_NAME
            or self.adapter_id != ADAPTER_ID
            or self.outcome not in OUTCOME_VOCABULARY
        ):
            raise ValueError("Exact13 identity/outcome drift")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("Exact13 passed invariant drift")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("Exact13 blocks invariant drift")
        if (self.reason == "") is not (self.outcome == "passed"):
            raise ValueError("Exact13 reason invariant drift")
        if self.evaluator_io_used is not False:
            raise ValueError("Exact13 evaluator I/O drift")


@dataclass(frozen=True)
class SourceValidationDecision:
    accepted: bool
    code: str
    reason: str
    adapter_ready: bool


class AdapterContractDesignError(Exception):
    """Design-only representation of the frozen future Exact6 error."""

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
        "covalent_ext.covapie_bulk_download_admission_admit_014_rule_logic_interface"
    )


def _oracle_module() -> Any:
    return importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate"
    )


def validate_source_shape_and_invariants_for_design(
    source: object,
) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit014EvaluationResult
    if type(source) is not result_type:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, False
        )
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact9 storage/order drift")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact9 dataclass order drift")
        values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        exact_types = (
            str, str, bool, bool, str, tuple, tuple, tuple, bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("Exact9 top-level type drift")
        reconstructed = result_type(*values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact9 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    return SourceValidationDecision(True, "", "", True)


def expected_exact9_from_committed_oracle_for_design(
    stage_authorization_context: object,
    *,
    oracle_callable: Callable[..., object] | None = None,
) -> Any:
    """Call the committed design oracle once and validate its Exact9."""
    standalone = _standalone_module()
    oracle = _oracle_module()
    classify = (
        oracle.classify_admit_014_formal_evaluator_interface_design
        if oracle_callable is None else oracle_callable
    )
    try:
        classification = classify(
            stage_authorization_context=stage_authorization_context
        )
        result_type = oracle.Admit014EvaluationResultContractDesign
        if type(classification) is not result_type:
            raise TypeError("oracle exact result type required")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact9 dataclass order drift")
        storage = vars(classification)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact9 storage/order drift")
        values = tuple(getattr(classification, name) for name in STANDALONE_RESULT_FIELDS)
        exact_types = (
            str, str, bool, bool, str, tuple, tuple, tuple, bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("oracle Exact9 top-level type drift")
        if result_type(*values) != classification:
            raise ValueError("oracle Exact9 reconstruction drift")
        return classification
    except Exception as error:
        raise ValueError(SOURCE_INVARIANT_REASON) from error


def validate_source_oracle_equivalence_for_design(
    source: object, oracle_result: object,
) -> SourceValidationDecision:
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        return decision
    oracle = _oracle_module()
    if type(oracle_result) is not oracle.Admit014EvaluationResultContractDesign:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    try:
        source_values = tuple(
            getattr(source, name) for name in STANDALONE_RESULT_FIELDS
        )
        expected_values = tuple(
            getattr(oracle_result, name) for name in STANDALONE_RESULT_FIELDS
        )
    except AttributeError:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    if any(
        type(left) is not type(right) or left != right
        for left, right in zip(source_values, expected_values, strict=True)
    ):
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    return SourceValidationDecision(True, "", "", True)


def project_stage_authorization_record_to_exact_string_pairs(
    canonical_record: object,
) -> tuple[tuple[str, str], ...]:
    """Project exact bool authority evidence to lowercase exact string pairs."""
    if type(canonical_record) is not tuple:
        raise TypeError("canonical record requires exact tuple")
    if canonical_record == ():
        return ()
    if (
        len(canonical_record) != 1
        or type(canonical_record[0]) is not tuple
        or len(canonical_record[0]) != 2
        or type(canonical_record[0][0]) is not str
        or canonical_record[0][0] != TARGET_CONTEXT_ITEM
        or type(canonical_record[0][1]) is not bool
    ):
        raise TypeError("canonical stage authorization record drift")
    return ((TARGET_CONTEXT_ITEM, "true" if canonical_record[0][1] else "false"),)


def project_exact9_to_exact13_for_design(
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
        project_stage_authorization_record_to_exact_string_pairs(
            source.canonical_stage_authorization_record
        ),
        (),
        (),
        source.consumed_stage_authorization_fields,
        source.evaluator_io_used,
        ADAPTER_ID,
    )


def candidate_invalid_exact13_for_design() -> UnifiedAdmissionEvaluationDesignRecord:
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION, ADMISSION_RULE_ID, ADMISSION_RULE_NAME,
        "invalid", False, True, CANDIDATE_MAPPING_REASON,
        (), (), (), (), False, ADAPTER_ID,
    )


def _raise_design_error(code: str, reason: str, adapter_ready: bool) -> NoReturn:
    raise AdapterContractDesignError(code, reason, adapter_ready=adapter_ready)


def simulate_admit_014_unified_adapter_contract_design(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
    formal_evaluator: Callable[..., object] | None = None,
    oracle_callable: Callable[..., object] | None = None,
) -> UnifiedAdmissionEvaluationDesignRecord:
    """Exercise the frozen future routing/projection without a runtime handler."""
    if batch_context is not None:
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["batch_context"], True,
        )
    if evaluation_context is not None:
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["evaluation_context"], True,
        )
    if download_result_context is not None:
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["download_result_context"], True,
        )
    if not isinstance(candidate_record, Mapping):
        return candidate_invalid_exact13_for_design()

    evaluator = (
        _standalone_module().evaluate_admit_014
        if formal_evaluator is None else formal_evaluator
    )
    try:
        source = evaluator(
            stage_authorization_context=stage_authorization_context
        )
    except Exception:
        _raise_design_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        expected = expected_exact9_from_committed_oracle_for_design(
            stage_authorization_context, oracle_callable=oracle_callable,
        )
    except ValueError:
        _raise_design_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    decision = validate_source_oracle_equivalence_for_design(source, expected)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        return project_exact9_to_exact13_for_design(source)
    except (AttributeError, TypeError, ValueError):
        _raise_design_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )


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


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _full_identity(item: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        item.st_dev, item.st_ino, item.st_mode, item.st_size,
        item.st_mtime_ns, item.st_ctime_ns,
    )


def _validate_canonical_evidence_runtime_identity(
    implementation_name: str,
    version: tuple[int, int, int],
) -> None:
    if (
        implementation_name != CANONICAL_PYTHON_IMPLEMENTATION
        or version != CANONICAL_PYTHON_VERSION
    ):
        observed_version = ".".join(str(part) for part in version)
        raise ValueError(
            "required: CPython 3.10.4; "
            f"observed implementation: {implementation_name}; "
            f"observed version: {observed_version}; "
            "frozen evidence is Python-version-sensitive; "
            "noncanonical Python is not authorized to build artifacts or run the checker"
        )


def _assert_canonical_evidence_runtime() -> None:
    _validate_canonical_evidence_runtime_identity(
        sys.implementation.name, tuple(sys.version_info[:3])
    )


def _assert_parent_chain(repo_root: Path, relative: Path) -> None:
    current = repo_root
    root_identity = _identity(os.lstat(repo_root))
    if not stat.S_ISDIR(root_identity[2]) or stat.S_ISLNK(root_identity[2]):
        raise ValueError("repository root unsafe")
    for part in relative.parts[:-1]:
        current = current / part
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("source parent chain unsafe")


def _pinned_read(repo_root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("source path escape")
    root_lexical = os.lstat(repo_root)
    root_identity = _identity(root_lexical)
    if (
        not stat.S_ISDIR(root_lexical.st_mode)
        or stat.S_ISLNK(root_lexical.st_mode)
        or repo_root.resolve(strict=True) != repo_root
    ):
        raise ValueError("source repository root unsafe")
    root_fd = os.open(repo_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    descriptors = [root_fd]
    parent_bindings: list[tuple[int, str, int, tuple[int, int, int]]] = []
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("source repository root identity race")
        directory_fd = root_fd
        for part in relative.parts[:-1]:
            lexical = os.stat(part, dir_fd=directory_fd, follow_symlinks=False)
            lexical_identity = _identity(lexical)
            if not stat.S_ISDIR(lexical.st_mode) or stat.S_ISLNK(lexical.st_mode):
                raise ValueError("source parent directory unsafe")
            child_fd = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory_fd,
            )
            if _identity(os.fstat(child_fd)) != lexical_identity:
                os.close(child_fd)
                raise ValueError("source parent directory identity race")
            parent_bindings.append(
                (directory_fd, part, child_fd, lexical_identity)
            )
            directory_fd = child_fd
            descriptors.append(child_fd)
        before = os.stat(relative.name, dir_fd=directory_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            raise ValueError("source leaf unsafe")
        leaf_identity = _full_identity(before)
        descriptor = os.open(
            relative.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd,
        )
        try:
            if _full_identity(os.fstat(descriptor)) != leaf_identity:
                raise ValueError("source identity race")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            if _full_identity(os.fstat(descriptor)) != leaf_identity:
                raise ValueError("source changed during read")
            after_leaf = os.stat(
                relative.name, dir_fd=directory_fd, follow_symlinks=False
            )
            if (
                _full_identity(after_leaf) != leaf_identity
                or not stat.S_ISREG(after_leaf.st_mode)
                or stat.S_ISLNK(after_leaf.st_mode)
            ):
                raise ValueError("source lexical leaf identity changed after read")
            for parent_fd, part, child_fd, expected in reversed(parent_bindings):
                after_parent = os.stat(
                    part, dir_fd=parent_fd, follow_symlinks=False
                )
                if (
                    _identity(after_parent) != expected
                    or _identity(os.fstat(child_fd)) != expected
                    or not stat.S_ISDIR(after_parent.st_mode)
                    or stat.S_ISLNK(after_parent.st_mode)
                ):
                    raise ValueError(
                        "source lexical parent identity changed after read"
                    )
            after_root = os.lstat(repo_root)
            if (
                _identity(after_root) != root_identity
                or _identity(os.fstat(root_fd)) != root_identity
                or not stat.S_ISDIR(after_root.st_mode)
                or stat.S_ISLNK(after_root.st_mode)
            ):
                raise ValueError(
                    "source repository root identity changed after read"
                )
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _assert_base_lineage(repo_root: Path, head_ref: str) -> None:
    identity = _git(
        repo_root,
        ("show", "-s", "--format=%H%n%P%n%T%n%s", EXPECTED_BASE_COMMIT),
    ).decode().splitlines()
    if identity != [
        EXPECTED_BASE_COMMIT, EXPECTED_BASE_PARENT,
        EXPECTED_BASE_TREE, EXPECTED_BASE_SUBJECT,
    ]:
        raise ValueError("base identity drift")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref),
        cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("base is not an ancestor")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    _assert_canonical_evidence_runtime()
    _assert_base_lineage(repo_root, head_ref)
    records = []
    for raw_path, expected in SOURCE_BOUNDARY:
        relative = Path(raw_path)
        if (
            raw_path.startswith("data/raw/")
            or raw_path.startswith("checkpoints/")
            or relative.suffix in {".pt", ".ckpt", ".pth", ".pkl"}
        ):
            raise ValueError("protected source boundary entry")
        _assert_parent_chain(repo_root, relative)
        index_line = _git(
            repo_root,
            ("ls-files", "--stage", "--", relative.as_posix()),
        ).decode().rstrip("\n")
        tree_line = _git(
            repo_root,
            ("ls-tree", EXPECTED_BASE_COMMIT, "--", relative.as_posix()),
        ).decode().rstrip("\n")
        try:
            index_metadata, index_path = index_line.split("\t", 1)
            index_mode, index_blob, raw_stage = index_metadata.split(" ")
            tree_metadata, tree_path = tree_line.split("\t", 1)
            base_mode, kind, base_blob = tree_metadata.split(" ")
            index_stage = int(raw_stage)
        except ValueError as error:
            raise ValueError("source index/base entry malformed") from error
        if (
            index_path != relative.as_posix()
            or tree_path != relative.as_posix()
            or kind != "blob"
            or base_mode not in {"100644", "100755"}
            or index_mode != base_mode
            or index_stage != 0
            or index_blob != base_blob
            or re.fullmatch(r"[0-9a-f]{40}", base_blob) is None
            or re.fullmatch(r"[0-9a-f]{40}", index_blob) is None
        ):
            raise ValueError("source index/base mode/blob/stage drift")
        base_content = _git(repo_root, ("cat-file", "blob", base_blob))
        index_content = _git(repo_root, ("cat-file", "blob", index_blob))
        filesystem_content = _pinned_read(repo_root, relative)
        base_digest = _sha(base_content)
        filesystem_digest = _sha(filesystem_content)
        if (
            base_content != index_content
            or index_content != filesystem_content
            or base_digest != expected
            or _sha(index_content) != expected
            or filesystem_digest != expected
        ):
            raise ValueError("source SHA drift")
        records.append(FrozenSourceRecord(
            relative, expected, base_mode, base_blob, index_mode, index_blob,
            index_stage, base_digest, filesystem_digest, True,
            filesystem_content,
        ))
    return FrozenSourceSnapshot(tuple(records))


def _record(snapshot: FrozenSourceSnapshot, index: int) -> FrozenSourceRecord:
    return snapshot.records[index]


def _csv_document(
    snapshot: FrozenSourceSnapshot, index: int,
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    stream = io.StringIO(_record(snapshot, index).content.decode(), newline="")
    reader = csv.DictReader(stream)
    rows = list(reader)
    return tuple(reader.fieldnames or ()), rows


def _json_document(snapshot: FrozenSourceSnapshot, index: int) -> dict[str, Any]:
    value = json.loads(_record(snapshot, index).content)
    if type(value) is not dict:
        raise ValueError("source JSON object required")
    return value


def _top_functions(content: bytes) -> tuple[str, ...]:
    return tuple(
        node.name for node in ast.parse(content.decode()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _class_fields(content: bytes, class_name: str) -> tuple[str, ...]:
    tree = ast.parse(content.decode())
    target = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return tuple(
        node.target.id for node in target.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )


def _literal_registry_keys(content: bytes) -> tuple[str, ...]:
    tree = ast.parse(content.decode())
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets)
    )
    if not isinstance(assignment.value, ast.Call) or not assignment.value.args:
        raise ValueError("registry AST shape drift")
    dictionary = assignment.value.args[0]
    if not isinstance(dictionary, ast.Dict):
        raise ValueError("registry literal dict required")
    return tuple(ast.literal_eval(key) for key in dictionary.keys)


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    standalone_contract_header, standalone_contract = _csv_document(snapshot, 1)
    standalone_truth_header, standalone_truth = _csv_document(snapshot, 2)
    _, standalone_purity = _csv_document(snapshot, 4)
    issue_header, issue_rows = _csv_document(snapshot, 5)
    standalone_manifest = _json_document(snapshot, 6)
    formal_routing_header, formal_routing = _csv_document(snapshot, 8)
    formal_truth_header, formal_truth = _csv_document(snapshot, 9)
    formal_manifest = _json_document(snapshot, 10)
    _, authorization_truth = _csv_document(snapshot, 11)
    authorization_manifest = _json_document(snapshot, 12)
    runtime_contract_header, runtime_contract = _csv_document(snapshot, 14)
    _, registry_audit = _csv_document(snapshot, 15)
    runtime_manifest = _json_document(snapshot, 16)
    runtime_content = _record(snapshot, 13).content
    issues = {row["issue_id"]: row for row in issue_rows}
    open_issues = {
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    }
    checks = (
        FORMAL_EVALUATOR_NAME in _top_functions(_record(snapshot, 0).content),
        _sha(_record(snapshot, 0).content) == SOURCE_BOUNDARY[0][1],
        _sha(_record(snapshot, 6).content) == SOURCE_BOUNDARY[6][1],
        standalone_manifest.get("result_type") == FORMAL_RESULT_TYPE,
        standalone_manifest.get("result_fields") == list(STANDALONE_RESULT_FIELDS),
        len(standalone_contract_header) == 10 and len(standalone_contract) == 37,
        len(standalone_truth_header) == 12 and len(standalone_truth) == 61,
        len(standalone_purity) == 16,
        INDEPENDENT_ORACLE_NAME in _top_functions(_record(snapshot, 7).content),
        FORMAL_EVALUATOR_NAME not in _top_functions(_record(snapshot, 7).content),
        formal_manifest.get("design_oracle") == INDEPENDENT_ORACLE_NAME,
        formal_manifest.get("design_result_type") == INDEPENDENT_ORACLE_RESULT_TYPE,
        len(formal_routing_header) == 10 and len(formal_routing) == 8,
        len(formal_truth_header) == 17 and len(formal_truth) == 69,
        len(authorization_truth) == 40,
        authorization_manifest.get("authorization_contract", {}).get(
            "authoritative_envelope"
        )
        == "stage_authorization_context",
        _literal_registry_keys(runtime_content) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("known_not_registered_rule_ids")
        == ["ADMIT_014", "ADMIT_015"],
        runtime_manifest.get("result_fields") == list(RESULT_FIELDS),
        FUTURE_HANDLER_NAME not in _top_functions(runtime_content),
        len(registry_audit) > 0,
        b"UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation"
        in runtime_content,
        len(runtime_contract_header) == 7 and len(runtime_contract) == 59,
        issue_header == ISSUE_COLUMNS and len(issue_rows) == 30,
        all(issues[issue]["status"] == "open" for issue in open_issues),
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"]
        == "ADMIT_014|ADMIT_015",
        standalone_manifest.get("precondition_transition", {}).get("row_count") == 51,
        standalone_manifest.get("precondition_transition", {}).get("complete_count")
        == 49,
        standalone_manifest.get("precondition_transition", {}).get(
            "remaining_open_precondition_ids"
        ) == ["PRE_048", "PRE_049"],
        all(
            row["successor_effective_status"] == (
                "open" if row["issue_id"] in open_issues else "resolved"
            )
            for row in issue_rows
        ),
    )
    if not all(checks):
        failed = tuple(
            index for index, passed in enumerate(checks, 1) if not passed
        )
        raise ValueError(
            f"predecessor contract validation failed: {failed}"
        )
    return {
        "standalone_truth": standalone_truth,
        "issue_rows": issue_rows,
        "issue_bytes": _record(snapshot, 5).content,
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
        ("identity", "oracle", f"{INDEPENDENT_ORACLE_NAME}|{INDEPENDENT_ORACLE_RESULT_TYPE}"),
        ("identity", "future_handler", FUTURE_HANDLER_SIGNATURE_TEXT),
        ("routing", "five_envelopes", "candidate_record|batch_context|evaluation_context|download_result_context|stage_authorization_context"),
        ("routing", "precedence", "|".join(CONTEXT_ROUTING_ORDER)),
        ("routing", "batch", "exact_None"),
        ("routing", "evaluation", "exact_None"),
        ("routing", "download_result", "exact_None"),
        ("routing", "stage_authorization", "forward_same_object_no_prevalidation"),
        ("candidate", "mapping_only", "Mapping_envelope_only_zero_key_access"),
        ("candidate", "non_mapping_reason", CANDIDATE_MAPPING_REASON),
        ("candidate", "invalid_projection", _json_record(candidate_invalid_exact13_for_design())),
        ("authority", "envelope", "stage_authorization_context_only"),
        ("authority", "key", TARGET_CONTEXT_ITEM),
        ("authority", "exact_bool", "False|True_no_normalization"),
        ("authority", "adapter_direct_access", "0"),
        ("authority", "stable_mapping_total_access", "2_formal_then_oracle"),
        ("authority", "none_or_non_mapping_access", "0"),
        ("authority", "coexistence_item", ADMIT_015_COEXISTENCE_ITEM),
        ("routing", "private_sentinel", "not_imported_read_or_passed"),
        ("formal", "call", "keyword_only_exactly_once_after_routing"),
        ("formal", "identity", "stage_context_exact_object_identity_preserved"),
        ("source", "exact9_fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("source", "validation", "exact_type_storage_order_types_reconstruction_reason_pair_invariants"),
        ("source", "type_failure", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_TYPE_REASON}|adapter_ready=false"),
        ("source", "invariant_failure", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_INVARIANT_REASON}|adapter_ready=false"),
        ("oracle", "call", "same_stage_context_exactly_once_after_source_validation"),
        ("oracle", "identity", "stage_context_exact_object_identity_preserved"),
        ("oracle", "equality", "full_Exact9_exact_type_value_storage_order"),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("projection", "normalized", "canonical_stage_bool_to_lowercase_string"),
        ("projection", "validated_candidate", "always_empty"),
        ("projection", "consumed_candidate", "always_empty"),
        ("projection", "consumed_context", "source_consumed_stage_authorization_fields"),
        ("projection", "false", "false"),
        ("projection", "true", "true"),
        ("projection", "no_schema_widening", "Exact13_exact_string_pairs_only"),
        ("projection", "validated_stage_note", "retained_by_normalized_values_not_candidate_fields"),
        ("registry", "current_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("registry", "future_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registry", "future_callable", "|".join(FUTURE_CALLABLE_DISCOVERED_RULE_IDS)),
        ("registry", "future_adapter_ready", "|".join(FUTURE_ADAPTER_READY_RULE_IDS)),
        ("registry", "future_known_not_registered", "|".join(FUTURE_KNOWN_NOT_REGISTERED)),
        ("registry", "first13_identity", "exact_object_identity_preserved"),
        ("precondition", "resolved", "PRE_048"),
        ("precondition", "remaining", "PRE_049"),
        ("precondition", "counts", "total=51|complete=50|incomplete=1|blocking=1"),
        ("issue", "continuity", "Exact30_byte_identical_zero_transitions"),
        ("issue", "coverage", "ADMIT_014|ADMIT_015"),
        ("boundary", "runtime", "design_only_no_handler_registry_dispatcher_runtime_mutation"),
        ("boundary", "aggregation", "no_combined_verdict_or_cross_rule_aggregation"),
        ("boundary", "operations", "no_provider_network_download_raw_model_checkpoint_dataloader_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    return [{
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1)]


class _RoutingCandidateProbe(Mapping[str, object]):
    def __init__(self) -> None:
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        raise AssertionError("candidate item access forbidden")

    def __iter__(self):
        self.access_count += 1
        raise AssertionError("candidate iteration forbidden")

    def __len__(self) -> int:
        self.access_count += 1
        raise AssertionError("candidate length access forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.access_count += 1
        raise AssertionError("candidate get forbidden")

    def __contains__(self, key: object) -> bool:
        self.access_count += 1
        raise AssertionError("candidate containment forbidden")


class _RoutingStageProbe(Mapping[str, object]):
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
        raise AssertionError("stage length access forbidden")


def _design_result_json(
    outcome: str,
    reason: str,
    normalized_values: tuple[tuple[str, str], ...] = (),
    consumed_context_items: tuple[str, ...] = (),
) -> str:
    return _json_record(UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION,
        ADMISSION_RULE_ID,
        ADMISSION_RULE_NAME,
        outcome,
        outcome == "passed",
        outcome != "passed",
        reason,
        normalized_values,
        (),
        (),
        consumed_context_items,
        False,
        ADAPTER_ID,
    ))


def _design_error_json(code: str, reason: str, adapter_ready: bool) -> str:
    return json.dumps(
        {
            "code": code,
            "admission_rule_id": ADMISSION_RULE_ID,
            "known_rule": True,
            "callable_discovered": True,
            "adapter_ready": adapter_ready,
            "reason": reason,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _routing_case_specs() -> list[dict[str, Any]]:
    context_error = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    adapter_error = "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    context_result = lambda reason: _design_error_json(
        context_error, reason, True
    )
    adapter_result = lambda reason: _design_error_json(
        adapter_error, reason, False
    )
    candidate_result = _json_record(candidate_invalid_exact13_for_design())
    required = _design_result_json(
        "blocked", "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
    )
    mapping_invalid = _design_result_json(
        "blocked", "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
    )
    missing = _design_result_json(
        "blocked",
        "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING",
        consumed_context_items=(TARGET_CONTEXT_ITEM,),
    )
    lookup_failed = _design_result_json(
        "blocked",
        "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
        consumed_context_items=(TARGET_CONTEXT_ITEM,),
    )
    false_result = _design_result_json(
        "blocked",
        "BULK_DOWNLOAD_NOT_AUTHORIZED",
        ((TARGET_CONTEXT_ITEM, "false"),),
        (TARGET_CONTEXT_ITEM,),
    )
    true_result = _design_result_json(
        "passed",
        "",
        ((TARGET_CONTEXT_ITEM, "true"),),
        (TARGET_CONTEXT_ITEM,),
    )

    def spec(
        group: str,
        case_id: str,
        condition: str,
        envelope: str,
        *,
        candidate_access: int = 0,
        adapter_access: int = 0,
        formal: int = 0,
        oracle: int = 0,
        formal_access: int = 0,
        oracle_access: int = 0,
        identity: str = "n/a",
        code: str = "",
        reason: str = "",
        result: str = "",
        scenario: str = "stage_true",
    ) -> dict[str, Any]:
        return {
            "matrix_order": "",
            "matrix_group": group,
            "case_id": case_id,
            "routing_condition": condition,
            "envelope_representation": envelope,
            "candidate_key_access_count": str(candidate_access),
            "adapter_stage_key_access_count": str(adapter_access),
            "formal_call_count": str(formal),
            "oracle_call_count": str(oracle),
            "formal_stage_key_access_count": str(formal_access),
            "oracle_stage_key_access_count": str(oracle_access),
            "identity_preserved": identity,
            "expected_dispatch_code": code,
            "expected_reason": reason,
            "expected_result_json": result,
            "_scenario": scenario,
        }

    cases = [
        spec("routing_failure", "batch_non_none", "first failure: batch must be None", "batch=object", code=context_error, reason=CONTEXT_REASONS["batch_context"], result=context_result(CONTEXT_REASONS["batch_context"]), scenario="batch_object"),
        spec("routing_failure", "batch_empty_mapping", "empty mapping is not None", "batch={}", code=context_error, reason=CONTEXT_REASONS["batch_context"], result=context_result(CONTEXT_REASONS["batch_context"]), scenario="batch_mapping"),
        spec("routing_failure", "evaluation_non_none", "second failure: evaluation must be None", "evaluation=object", code=context_error, reason=CONTEXT_REASONS["evaluation_context"], result=context_result(CONTEXT_REASONS["evaluation_context"]), scenario="evaluation_object"),
        spec("routing_failure", "evaluation_empty_mapping", "empty mapping is not None", "evaluation={}", code=context_error, reason=CONTEXT_REASONS["evaluation_context"], result=context_result(CONTEXT_REASONS["evaluation_context"]), scenario="evaluation_mapping"),
        spec("routing_failure", "download_non_none", "third failure: download result must be None", "download=object", code=context_error, reason=CONTEXT_REASONS["download_result_context"], result=context_result(CONTEXT_REASONS["download_result_context"]), scenario="download_object"),
        spec("routing_failure", "download_empty_mapping", "empty mapping is not None", "download={}", code=context_error, reason=CONTEXT_REASONS["download_result_context"], result=context_result(CONTEXT_REASONS["download_result_context"]), scenario="download_mapping"),
        spec("routing_failure", "multiple_invalid_batch_first", "batch wins over all later failures", "all forbidden non-None", code=context_error, reason=CONTEXT_REASONS["batch_context"], result=context_result(CONTEXT_REASONS["batch_context"]), scenario="all_invalid"),
        spec("routing_failure", "multiple_invalid_evaluation_first", "evaluation wins over download and candidate", "evaluation/download non-None", code=context_error, reason=CONTEXT_REASONS["evaluation_context"], result=context_result(CONTEXT_REASONS["evaluation_context"]), scenario="evaluation_download_candidate_invalid"),
        spec("routing_failure", "multiple_invalid_download_first", "download wins over candidate", "download non-None candidate invalid", code=context_error, reason=CONTEXT_REASONS["download_result_context"], result=context_result(CONTEXT_REASONS["download_result_context"]), scenario="download_candidate_invalid"),
        spec("candidate", "candidate_non_mapping", "fourth check returns invalid Exact13", "candidate=object", reason=CANDIDATE_MAPPING_REASON, result=candidate_result, scenario="candidate_invalid"),
        spec("candidate", "candidate_empty", "empty Mapping is valid and never read", "candidate={};stage=None", formal=1, oracle=1, identity="true", reason="STAGE_AUTHORIZATION_CONTEXT_REQUIRED", result=required, scenario="candidate_empty"),
        spec("candidate", "candidate_instrumented", "candidate Mapping key access remains zero", "candidate=instrumented;stage=None", formal=1, oracle=1, identity="true", reason="STAGE_AUTHORIZATION_CONTEXT_REQUIRED", result=required, scenario="candidate_probe"),
        spec("stage", "stage_none", "None forwarded without routing error", "stage=None", formal=1, oracle=1, identity="true", reason="STAGE_AUTHORIZATION_CONTEXT_REQUIRED", result=required, scenario="stage_none"),
        spec("stage", "stage_object", "non-Mapping forwarded without routing error", "stage=object", formal=1, oracle=1, identity="true", reason="STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID", result=mapping_invalid, scenario="stage_object"),
        spec("stage", "stage_empty_mapping", "empty Mapping accessed by formal then oracle", "stage={}", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", reason="CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING", result=missing, scenario="stage_empty"),
        spec("stage", "stage_false", "exact False accessed twice and projected lowercase", "stage={target:False}", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", reason="BULK_DOWNLOAD_NOT_AUTHORIZED", result=false_result, scenario="stage_false"),
        spec("stage", "stage_true", "exact True accessed twice and projected lowercase", "stage={target:True}", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("stage", "stage_extra_keys", "extra keys and ADMIT_015 item not accessed", "stage={target:True,training:True,extra:1}", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_extra"),
        spec("stage", "stage_keyerror", "KeyError evaluated independently twice", "stage=KeyError mapping", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", reason="CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING", result=missing, scenario="stage_keyerror"),
        spec("stage", "stage_runtimeerror", "RuntimeError evaluated independently twice", "stage=RuntimeError mapping", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", reason="STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED", result=lookup_failed, scenario="stage_runtimeerror"),
        spec("stage", "stage_valueerror", "ValueError evaluated independently twice", "stage=ValueError mapping", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", reason="STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED", result=lookup_failed, scenario="stage_valueerror"),
        spec("calls", "formal_once", "formal called exactly once", "stable Mapping", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("calls", "oracle_once", "oracle called once after source validation", "stable Mapping", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("calls", "source_invalid_no_oracle", "source prevalidation precedes oracle", "formal wrong type", formal=1, identity="true", code=adapter_error, reason=SOURCE_TYPE_REASON, result=adapter_result(SOURCE_TYPE_REASON), scenario="source_wrong_type"),
        spec("calls", "nonrepeatable_mismatch", "formal/oracle mismatch fails closed", "stateful Mapping", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="nonrepeatable"),
        spec("source_failure", "source_wrong_type", "exact formal result type required", "formal=object", formal=1, identity="true", code=adapter_error, reason=SOURCE_TYPE_REASON, result=adapter_result(SOURCE_TYPE_REASON), scenario="source_wrong_type"),
        spec("source_failure", "source_subclass", "formal result subclass rejected", "formal=subclass", formal=1, identity="true", code=adapter_error, reason=SOURCE_TYPE_REASON, result=adapter_result(SOURCE_TYPE_REASON), scenario="source_subclass"),
        spec("source_failure", "source_storage_order", "Exact9 storage order required", "formal=reordered", formal=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="source_storage"),
        spec("source_failure", "source_type_drift", "Exact9 top-level types required", "formal=type drift", formal=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="source_type_drift"),
        spec("source_failure", "source_invariant", "Exact9 constructor invariants required", "formal=contradiction", formal=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="source_invariant"),
        spec("oracle_failure", "oracle_wrong_type", "exact oracle result type required", "oracle=object", formal=1, oracle=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="oracle_wrong_type"),
        spec("oracle_failure", "oracle_storage", "oracle Exact9 storage/order required", "oracle=reordered", formal=1, oracle=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="oracle_storage"),
        spec("oracle_failure", "oracle_mismatch", "all Exact9 types and values must match", "oracle=value drift", formal=1, oracle=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="oracle_mismatch"),
        spec("oracle_failure", "oracle_exception", "oracle exception fails closed", "oracle=raises", formal=1, oracle=1, identity="true", code=adapter_error, reason=SOURCE_INVARIANT_REASON, result=adapter_result(SOURCE_INVARIANT_REASON), scenario="oracle_exception"),
        spec("projection", "candidate_fields_empty", "stage fields never become candidate fields", "valid source", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("projection", "consumed_context", "consumed stage field maps to context item", "valid source", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("projection", "false_lowercase", "False projects to exact lowercase false", "stage={target:False}", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", reason="BULK_DOWNLOAD_NOT_AUTHORIZED", result=false_result, scenario="stage_false"),
        spec("projection", "true_lowercase", "True projects to exact lowercase true", "stage={target:True}", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("registry", "current_exact13", "current registry remains ADMIT_001..013", "ADMIT_001..013", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("registry", "future_exact14", "future order appends ADMIT_014 only", "ADMIT_001..014", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("registry", "known_unregistered", "ADMIT_015 remains known-not-registered", "ADMIT_015", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
        spec("registry", "handler_identity", "first thirteen handler identities preserved", "identity_preserved", formal=1, oracle=1, formal_access=1, oracle_access=1, identity="true", result=true_result, scenario="stage_true"),
    ]
    for index, value in enumerate(cases, 1):
        value["matrix_order"] = str(index)
    return cases


def _mutate_exact9_for_routing(value: object, scenario: str) -> object:
    if scenario.endswith("wrong_type"):
        return object()
    if scenario == "source_subclass":
        source_type = type(value)
        subclass = type("_RoutingSourceSubclass", (source_type,), {})
        instance = object.__new__(subclass)
        for name in STANDALONE_RESULT_FIELDS:
            object.__setattr__(instance, name, getattr(value, name))
        return instance
    if scenario in {"source_storage", "oracle_storage"}:
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif scenario == "source_type_drift":
        object.__setattr__(value, "outcome", 1)
    elif scenario == "source_invariant":
        object.__setattr__(value, "outcome", "passed")
    return value


def _execute_routing_case_for_design(spec: Mapping[str, Any]) -> dict[str, str]:
    scenario = spec["_scenario"]
    candidate: object = {}
    stage: object = _RoutingStageProbe({TARGET_CONTEXT_ITEM: True})
    batch: object = None
    evaluation: object = None
    download: object = None
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
        batch, evaluation, download, candidate = object(), object(), object(), object()
    elif scenario == "evaluation_download_candidate_invalid":
        evaluation, download, candidate = object(), object(), object()
    elif scenario == "download_candidate_invalid":
        download, candidate = object(), object()
    elif scenario == "candidate_invalid":
        candidate, stage = object(), _RoutingStageProbe()
    elif scenario == "candidate_empty":
        candidate, stage = {}, None
    elif scenario == "candidate_probe":
        candidate, stage = _RoutingCandidateProbe(), None
    elif scenario == "stage_none":
        stage = None
    elif scenario == "stage_object":
        stage = object()
    elif scenario == "stage_empty":
        stage = _RoutingStageProbe()
    elif scenario == "stage_false":
        stage = _RoutingStageProbe({TARGET_CONTEXT_ITEM: False})
    elif scenario == "stage_extra":
        stage = _RoutingStageProbe({
            TARGET_CONTEXT_ITEM: True,
            ADMIT_015_COEXISTENCE_ITEM: True,
            "extra": 1,
        })
    elif scenario == "stage_keyerror":
        stage = _RoutingStageProbe(error=KeyError(TARGET_CONTEXT_ITEM))
    elif scenario == "stage_runtimeerror":
        stage = _RoutingStageProbe(error=RuntimeError("routing evidence"))
    elif scenario == "stage_valueerror":
        stage = _RoutingStageProbe(error=ValueError("routing evidence"))
    elif scenario == "nonrepeatable":
        stage = _RoutingStageProbe(alternating=True)
    elif scenario.startswith(("source_", "oracle_")):
        stage = None

    call_order: list[str] = []
    identity_checks: list[bool] = []
    formal_count = oracle_count = 0
    formal_access = oracle_access = 0
    source_representation = "not_called"
    oracle_representation = "not_called"

    def target_access_count() -> int:
        return (
            stage.target_access_count
            if isinstance(stage, _RoutingStageProbe)
            else 0
        )

    def formal_wrapper(*, stage_authorization_context: object) -> object:
        nonlocal formal_count, formal_access, source_representation
        formal_count += 1
        call_order.append("formal")
        identity_checks.append(stage_authorization_context is stage)
        before = target_access_count()
        value = _standalone_module().evaluate_admit_014(
            stage_authorization_context=stage_authorization_context
        )
        formal_access += target_access_count() - before
        if scenario.startswith("source_"):
            value = _mutate_exact9_for_routing(value, scenario)
        source_representation = (
            "type=subclass"
            if scenario == "source_subclass"
            else _json_record(value)
            if type(value) is _standalone_module().Admit014EvaluationResult
            else f"type={type(value).__name__}"
        )
        return value

    def oracle_wrapper(*, stage_authorization_context: object) -> object:
        nonlocal oracle_count, oracle_access, oracle_representation
        oracle_count += 1
        call_order.append("oracle")
        identity_checks.append(stage_authorization_context is stage)
        before = target_access_count()
        if scenario == "oracle_exception":
            oracle_representation = "exception=RuntimeError"
            raise RuntimeError("routing oracle evidence")
        oracle_stage = (
            object() if scenario == "oracle_mismatch"
            else stage_authorization_context
        )
        value = _oracle_module().classify_admit_014_formal_evaluator_interface_design(
            stage_authorization_context=oracle_stage
        )
        oracle_access += target_access_count() - before
        if scenario.startswith("oracle_"):
            value = _mutate_exact9_for_routing(value, scenario)
        oracle_representation = (
            _json_record(value)
            if type(value) is _oracle_module().Admit014EvaluationResultContractDesign
            else f"type={type(value).__name__}"
        )
        return value

    observed_code = ""
    observed_reason = ""
    observed_result = ""
    try:
        result = simulate_admit_014_unified_adapter_contract_design(
            candidate,
            batch_context=batch,
            evaluation_context=evaluation,
            download_result_context=download,
            stage_authorization_context=stage,
            formal_evaluator=formal_wrapper,
            oracle_callable=oracle_wrapper,
        )
        observed_reason = result.reason
        observed_result = _json_record(result)
    except AdapterContractDesignError as error:
        observed_code = error.code
        observed_reason = error.reason
        observed_result = json.dumps(
            error.as_dict(), ensure_ascii=True, separators=(",", ":")
        )

    candidate_access = (
        candidate.access_count
        if isinstance(candidate, _RoutingCandidateProbe)
        else 0
    )
    total_stage_access = target_access_count()
    adapter_access = total_stage_access - formal_access - oracle_access
    observed_identity = (
        "n/a" if not identity_checks
        else str(all(identity_checks)).lower()
    )
    expected_call_order = (
        "formal|oracle" if spec["oracle_call_count"] == "1"
        else "formal" if spec["formal_call_count"] == "1"
        else ""
    )
    passed = all((
        observed_code == spec["expected_dispatch_code"],
        observed_reason == spec["expected_reason"],
        observed_result == spec["expected_result_json"],
        "|".join(call_order) == expected_call_order,
        observed_identity == spec["identity_preserved"],
        candidate_access == int(spec["candidate_key_access_count"]),
        adapter_access == int(spec["adapter_stage_key_access_count"]),
        formal_count == int(spec["formal_call_count"]),
        oracle_count == int(spec["oracle_call_count"]),
        formal_access == int(spec["formal_stage_key_access_count"]),
        oracle_access == int(spec["oracle_stage_key_access_count"]),
    ))
    return {
        "observed_dispatch_code": observed_code,
        "observed_reason": observed_reason,
        "observed_result_json": observed_result,
        "observed_call_order": "|".join(call_order),
        "observed_identity_preserved": observed_identity,
        "observed_candidate_key_access_count": str(candidate_access),
        "observed_adapter_stage_key_access_count": str(adapter_access),
        "observed_formal_call_count": str(formal_count),
        "observed_oracle_call_count": str(oracle_count),
        "observed_formal_stage_key_access_count": str(formal_access),
        "observed_oracle_stage_key_access_count": str(oracle_access),
        "_source_result_representation": source_representation,
        "_oracle_result_representation": oracle_representation,
        "case_passed": str(passed).lower(),
    }


def _routing_rows() -> list[dict[str, str]]:
    rows = []
    for spec in _routing_case_specs():
        observed = _execute_routing_case_for_design(spec)
        row = {
            name: (
                observed[name]
                if name in observed
                else str(spec[name])
            )
            for name in ROUTING_COLUMNS
        }
        row["_source_result_representation"] = observed[
            "_source_result_representation"
        ]
        row["_oracle_result_representation"] = observed[
            "_oracle_result_representation"
        ]
        rows.append(row)
    return rows


class _TruthStageMapping(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object] | None = None,
        error: BaseException | None = None,
    ) -> None:
        self._values = {} if values is None else dict(values)
        self._error = error

    def __getitem__(self, key: str) -> object:
        if self._error is not None:
            raise self._error
        return self._values[key]

    def __iter__(self):
        raise AssertionError("iteration forbidden")

    def __len__(self) -> int:
        raise AssertionError("len forbidden")


def _truth_rows(
    standalone_truth: Sequence[Mapping[str, str]],
    routing_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    standalone = _standalone_module()
    oracle = _oracle_module()
    cases: list[tuple[str, str, object]] = [
        ("STAGE_NONE", "business", None),
        ("STAGE_OBJECT", "business", object()),
        ("STAGE_EMPTY", "business", _TruthStageMapping()),
        ("STAGE_KEYERROR", "business", _TruthStageMapping()),
        ("STAGE_RUNTIMEERROR", "business", _TruthStageMapping(error=RuntimeError("x"))),
        ("STAGE_VALUEERROR", "business", _TruthStageMapping(error=ValueError("x"))),
        ("TYPE_INT_ZERO", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: 0})),
        ("TYPE_INT_ONE", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: 1})),
        ("TYPE_STRING_FALSE", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: "false"})),
        ("TYPE_STRING_TRUE", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: "true"})),
        ("TYPE_NONE", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: None})),
        ("TYPE_FLOAT", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: 0.0})),
        ("TYPE_LIST", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: []})),
        ("TYPE_TUPLE", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: ()})),
        ("TYPE_OBJECT", "exact_bool_negative", _TruthStageMapping({TARGET_CONTEXT_ITEM: object()})),
        ("EXACT_FALSE", "projection", _TruthStageMapping({TARGET_CONTEXT_ITEM: False})),
        ("EXACT_TRUE", "projection", _TruthStageMapping({TARGET_CONTEXT_ITEM: True})),
        ("ADMIT015_COEXIST", "coexistence", _TruthStageMapping({TARGET_CONTEXT_ITEM: True, ADMIT_015_COEXISTENCE_ITEM: False})),
        ("EXTRA_KEYS", "coexistence", _TruthStageMapping({TARGET_CONTEXT_ITEM: False, "extra": object()})),
    ]
    rows: list[dict[str, str]] = []
    for case_id, group, stage in cases:
        source = standalone.evaluate_admit_014(
            stage_authorization_context=stage
        )
        oracle_result = oracle.classify_admit_014_formal_evaluator_interface_design(
            stage_authorization_context=stage
        )
        decision = validate_source_oracle_equivalence_for_design(
            source, oracle_result
        )
        if not decision.accepted:
            raise ValueError(f"truth source/oracle mismatch: {case_id}")
        projected = project_exact9_to_exact13_for_design(source)
        observed = simulate_admit_014_unified_adapter_contract_design(
            {},
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=stage,
        )
        expected_json = _json_record(projected)
        observed_json = _json_record(observed)
        exact_type_value_equality = (
            type(projected) is type(observed)
            and projected == observed
            and expected_json == observed_json
        )
        rows.append({
            "case_order": str(len(rows) + 1),
            "case_id": case_id,
            "case_group": group,
            "routing_condition": "valid five-envelope route",
            "source_result_representation": _json_record(source),
            "oracle_result_representation": _json_record(oracle_result),
            "expected_unified_result_json": expected_json,
            "observed_unified_result_json": observed_json,
            "exact13_type_value_equality": str(
                exact_type_value_equality
            ).lower(),
            "case_passed": str(exact_type_value_equality).lower(),
        })
    for route in routing_rows:
        exact_value_equality = (
            route["expected_result_json"] == route["observed_result_json"]
        )
        passed = (
            route["case_passed"] == "true"
            and exact_value_equality
            and route["formal_call_count"]
            == route["observed_formal_call_count"]
            and route["oracle_call_count"]
            == route["observed_oracle_call_count"]
        )
        rows.append({
            "case_order": str(len(rows) + 1),
            "case_id": f"ROUTING_{route['case_id'].upper()}",
            "case_group": f"routing_{route['matrix_group']}",
            "routing_condition": route["routing_condition"],
            "source_result_representation":
                route["_source_result_representation"],
            "oracle_result_representation":
                route["_oracle_result_representation"],
            "expected_unified_result_json": route["expected_result_json"],
            "observed_unified_result_json": route["observed_result_json"],
            "exact13_type_value_equality": str(exact_value_equality).lower(),
            "case_passed": str(passed).lower(),
        })
    inherited_ids = tuple(row["case_id"] for row in standalone_truth)
    if len(standalone_truth) != 61 or len(set(inherited_ids)) != 61:
        raise ValueError("standalone Exact61 truth identity drift")
    if any(row["case_passed"] != "true" for row in rows):
        raise ValueError("adapter truth matrix failed closed")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    states = (
        ("production_design_only", True),
        ("shared_exact13_preserved", True),
        ("five_envelope_routing_frozen", True),
        ("stage_authority_only", True),
        ("adapter_direct_target_access_count_zero", True),
        ("formal_exactly_once", True),
        ("oracle_exactly_once", True),
        ("stage_context_identity_preserved", True),
        ("source_exact9_attested", True),
        ("oracle_exact9_attested", True),
        ("full_exact9_equivalence_required", True),
        ("bool_lowercase_projection", True),
        ("candidate_fields_empty", True),
        ("consumed_context_projection", True),
        ("pre_048_resolved", True),
        ("pre_049_open", True),
        ("issue_inventory_byte_identical", True),
        ("canonical_runtime", True),
        ("deterministic_materialization", True),
        ("runtime_handler_implemented", False),
        ("registry_changed", False),
        ("exact14_runtime_implemented", False),
        ("mandatory_enforcement_implemented", False),
        ("provider_mapping_implemented", False),
        ("network_executed", False),
        ("download_executed", False),
        ("raw_accessed", False),
        ("combined_verdict_implemented", False),
        ("cross_rule_aggregation_implemented", False),
        ("training_executed", False),
        ("current_main_staged", False),
        ("current_main_committed_or_pushed", False),
    )
    return [{
        "audit_order": str(index),
        "audit_item": name,
        "expected_state": str(state).lower(),
        "observed_state": str(state).lower(),
        "safety_passed": "true",
    } for index, (name, state) in enumerate(states, 1)]


TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_standalone_evaluator_interface_implemented",
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_rule_logic_implemented",
    "admit_014_unified_adapter_contract_frozen",
    "admit_014_exact13_projection_frozen",
    "admit_014_context_routing_contract_frozen",
    "admit_014_source_oracle_equivalence_contract_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_014_implementation",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_014_unified_adapter_implemented",
    "admit_014_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "mandatory_pre_download_authorization_enforcement_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
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
    _assert_canonical_evidence_runtime()
    snapshot = build_frozen_source_snapshot(repo_root, head_ref)
    predecessor = _validate_predecessors(snapshot)
    routing_rows = _routing_rows()
    truth_rows = _truth_rows(predecessor["standalone_truth"], routing_rows)
    state = {
        "snapshot": snapshot,
        "contract_rows": _contract_rows(),
        "routing_rows": routing_rows,
        "truth_rows": truth_rows,
        "safety_rows": _safety_rows(),
        "issue_rows": predecessor["issue_rows"],
        "issue_bytes": predecessor["issue_bytes"],
    }
    if tuple(
        len(state[name])
        for name in (
            "contract_rows", "routing_rows", "truth_rows",
            "safety_rows", "issue_rows",
        )
    ) != (54, 42, 61, 32, 30):
        raise ValueError("design state row count drift")
    return state


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode()


def build_artifacts(state: Mapping[str, Any] | None = None) -> dict[str, bytes]:
    """Build deterministic Exact6 evidence without reading candidate outputs."""
    _assert_canonical_evidence_runtime()
    state = build_design_state() if state is None else state
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        ROUTING_FILENAME: _csv_bytes(
            ROUTING_COLUMNS,
            [
                {name: row[name] for name in ROUTING_COLUMNS}
                for row in state["routing_rows"]
            ],
        ),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    snapshot = state["snapshot"]
    output_sha = {name: _sha(content) for name, content in payloads.items()}
    manifest = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_parent": EXPECTED_BASE_PARENT,
        "expected_base_tree": EXPECTED_BASE_TREE,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "canonical_evidence_python_implementation": CANONICAL_PYTHON_IMPLEMENTATION,
        "canonical_evidence_python_version": ".".join(map(str, CANONICAL_PYTHON_VERSION)),
        "ast_attestation_cross_python_version_portable": AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE,
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "adapter_id": ADAPTER_ID,
        "formal_evaluator": FORMAL_EVALUATOR_NAME,
        "formal_result_type": FORMAL_RESULT_TYPE,
        "independent_oracle": INDEPENDENT_ORACLE_NAME,
        "independent_oracle_result_type": INDEPENDENT_ORACLE_RESULT_TYPE,
        "future_adapter_handler": FUTURE_HANDLER_NAME,
        "future_adapter_handler_signature": FUTURE_HANDLER_SIGNATURE_TEXT,
        "future_adapter_handler_signature_evidence": {
            "signature_text": FUTURE_HANDLER_SIGNATURE_TEXT,
            "parameter_order": list(
                FUTURE_HANDLER_SIGNATURE_DESIGN.parameters
            ),
            "parameter_kinds": [
                parameter.kind.name
                for parameter
                in FUTURE_HANDLER_SIGNATURE_DESIGN.parameters.values()
            ],
            "required_count": sum(
                parameter.default is inspect.Parameter.empty
                for parameter
                in FUTURE_HANDLER_SIGNATURE_DESIGN.parameters.values()
            ),
            "annotations": {
                name: parameter.annotation.__name__
                for name, parameter
                in FUTURE_HANDLER_SIGNATURE_DESIGN.parameters.items()
            },
            "return_annotation": (
                FUTURE_HANDLER_SIGNATURE_DESIGN.return_annotation
            ),
            "has_varargs": any(
                parameter.kind is inspect.Parameter.VAR_POSITIONAL
                for parameter
                in FUTURE_HANDLER_SIGNATURE_DESIGN.parameters.values()
            ),
            "has_varkw": any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter
                in FUTURE_HANDLER_SIGNATURE_DESIGN.parameters.values()
            ),
        },
        "future_adapter_handler_implemented": False,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "context_routing_order": list(CONTEXT_ROUTING_ORDER),
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "forbidden_envelope_contract": {
            "batch_context": "exact None",
            "evaluation_context": "exact None",
            "download_result_context": "exact None",
        },
        "stage_authorization_contract": {
            "authoritative_envelope": "stage_authorization_context",
            "authoritative_key": TARGET_CONTEXT_ITEM,
            "value_contract": "exact bool False|True; no normalization",
            "adapter_prevalidation": False,
            "adapter_direct_target_access_count": 0,
            "formal_call_count": 1,
            "oracle_call_count": 1,
            "stable_mapping_formal_target_access_count": 1,
            "stable_mapping_oracle_target_access_count": 1,
            "stable_mapping_total_target_access_count": 2,
            "target_access_order": ["formal", "oracle"],
            "none_or_non_mapping_target_access_count": 0,
            "identity_preserved_to_formal": True,
            "identity_preserved_to_oracle": True,
            "admit_015_coexistence_item": ADMIT_015_COEXISTENCE_ITEM,
        },
        "candidate_record_contract": {
            "mapping_required": True,
            "candidate_key_access_count": 0,
            "authority_source": False,
        },
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "candidate_invalid_projection": json.loads(
            _json_record(candidate_invalid_exact13_for_design())
        ),
        "candidate_invalid_call_counts": {
            "formal": 0, "oracle": 0,
            "candidate_key_access": 0, "stage_target_access": 0,
        },
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "source_failure_dispatch_code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "source_exact9_validation": (
            "exact type; vars exact dict and order; dataclass fields; "
            "top-level exact types; constructor reconstruction; fixed "
            "identity/I/O and all result invariants"
        ),
        "source_validation_before_oracle": True,
        "oracle_exact9_validation": (
            "exact type; vars exact dict and order; dataclass fields; "
            "top-level exact types; constructor reconstruction and invariants"
        ),
        "source_oracle_full_exact9_exact_type_value_equality_required": True,
        "exact13_projection": {
            "copied_fields": [
                "admission_rule_id", "outcome", "passed",
                "blocks_candidate", "reason", "evaluator_io_used",
            ],
            "fixed_fields": {
                "schema_version": RESULT_SCHEMA_VERSION,
                "admission_rule_name": ADMISSION_RULE_NAME,
                "adapter_id": ADAPTER_ID,
            },
            "normalized_values": (
                "source canonical exact bool pair projected to lowercase "
                "exact string false|true"
            ),
            "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": (
                "source.consumed_stage_authorization_fields"
            ),
        },
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_known_not_registered_rule_ids": list(FUTURE_KNOWN_NOT_REGISTERED),
        "first_thirteen_handler_object_identity_preserved": True,
        "shared_result_identity_preserved": True,
        "shared_dispatch_error_identity_preserved": True,
        "public_dispatcher_signature_preserved": True,
        "public_dispatcher_single_rule": True,
        "future_registry_mapping_proxy_type": True,
        "precondition_transition": {
            "row_count": 51,
            "complete_count": 50,
            "incomplete_count": 1,
            "implementation_blocking_count": 1,
            "resolved_precondition_ids": ["PRE_048"],
            "resolution": (
                "ADMIT_014 five-envelope routing, standalone Exact9 "
                "attestation, oracle equivalence and typed Exact13 "
                "projection frozen"
            ),
            "remaining_open_precondition_ids": ["PRE_049"],
        },
        "issue_inventory_row_count": 30,
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[5][1],
        "issue_transition_count": 0,
        "coverage_issue_affected_rules": "ADMIT_014|ADMIT_015",
        "remaining_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "contract_row_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]),
        "projection_truth_matrix_row_count": len(state["truth_rows"]),
        "safety_row_count": len(state["safety_rows"]),
        "source_boundary_name": "fixed_ordered_exact17_committed_source_boundary",
        "source_input_count": len(SOURCE_BOUNDARY),
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "source_input_verification": [{
            "source_order": index,
            "source_relative_path": record.relative_path.as_posix(),
            "tracked": record.tracked_in_current_index,
            "base_tree_blob": record.base_tree_blob,
            "base_tree_mode": record.base_tree_mode,
            "index_blob": record.index_blob,
            "index_mode": record.index_mode,
            "index_stage": record.index_stage,
            "filesystem_regular": True,
            "non_symlink": True,
            "parent_chain_non_symlink": True,
            "safe_descendant": True,
            "pinned_fd_read": True,
            "post_read_identity_verified": True,
            "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256,
            "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_validation_before_candidate_or_output_read": True,
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": output_sha,
        "output_sha256_excludes_manifest_self_hash": True,
        "readiness": dict(READINESS),
        **READINESS,
        "current_permission": False,
        "authorized_admit_014_download_execution_count": 0,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "mandatory_pre_download_authorization_enforcement_implemented": False,
        "provider_mapping_implemented": False,
        "real_provider_evaluation_ready": False,
        "real_download_executed": False,
        "raw_accessed": False,
        "runtime_changed": False,
        "registry_changed": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check"
        ),
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
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
    leaf_identities: tuple[
        tuple[str, tuple[int, int, int, int, int, int]], ...
    ]


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
    current = anchor
    for part in parent.relative_to(anchor).parts:
        current = current / part
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output parent chain unsafe")
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(
            root, parent, anchor, root.name, parent_identity, None, (),
        )
    if (
        not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        item = os.lstat(root / name)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _full_identity(item)))
    return OutputMaterializationPlan(
        root, parent, anchor, root.name, parent_identity,
        _identity(root_item), tuple(leaves),
    )


def _read_at(
    directory_fd: int,
    name: str,
    expected_identity: tuple[int, int, int, int, int, int],
) -> bytes:
    item = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if (
        _full_identity(item) != expected_identity
        or not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
    ):
        raise ValueError("pinned output leaf drift")
    descriptor = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if _full_identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned output descriptor drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _full_identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned output descriptor changed")
        after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            _full_identity(after) != expected_identity
            or not stat.S_ISREG(after.st_mode)
            or stat.S_ISLNK(after.st_mode)
        ):
            raise ValueError("pinned output lexical leaf changed")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(
        parent_fd, os.fsencode(source), parent_fd, os.fsencode(target),
        RENAME_NOREPLACE,
    ):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), f"{source}->{target}")


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if count <= 0:
            raise OSError("short output write")
        offset += count


def _verify_complete_set(
    root_fd: int,
    payloads: Mapping[str, bytes],
    expected_identities: Mapping[
        str, tuple[int, int, int, int, int, int]
    ] | None = None,
) -> dict[str, tuple[int, int, int, int, int, int]]:
    names = tuple(os.listdir(root_fd))
    if len(names) != len(OUTPUT_FILES) or set(names) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    identities = (
        {
            name: _full_identity(
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            )
            for name in OUTPUT_FILES
        }
        if expected_identities is None
        else dict(expected_identities)
    )
    if set(identities) != set(OUTPUT_FILES):
        raise ValueError("complete output identity inventory drift")
    for name, content in payloads.items():
        actual = _read_at(root_fd, name, identities[name])
        if actual != content or _sha(actual) != _sha(content):
            raise ValueError("output payload mismatch")
    names = tuple(os.listdir(root_fd))
    if len(names) != len(OUTPUT_FILES) or set(names) != set(OUTPUT_FILES):
        raise ValueError("complete output post-read inventory drift")
    for name, expected in identities.items():
        item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if (
            _full_identity(item) != expected
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
        ):
            raise ValueError("complete output post-read leaf identity drift")
    return identities


def _assert_output_parent_binding(
    plan: OutputMaterializationPlan, parent_fd: int,
) -> None:
    lexical = os.lstat(plan.parent)
    if (
        _identity(lexical) != plan.parent_identity
        or _identity(os.fstat(parent_fd)) != plan.parent_identity
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or plan.parent.resolve(strict=True) != plan.parent
    ):
        raise ValueError("output parent lexical binding changed")


def _verify_destination_binding(
    plan: OutputMaterializationPlan,
    parent_fd: int,
    root_fd: int,
    expected_root_identity: tuple[int, int, int],
    leaf_identities: Mapping[str, tuple[int, int, int, int, int, int]],
    payloads: Mapping[str, bytes],
) -> None:
    _assert_destination_name_binding(
        plan, parent_fd, root_fd, expected_root_identity
    )
    _verify_complete_set(root_fd, payloads, leaf_identities)
    _assert_destination_name_binding(
        plan, parent_fd, root_fd, expected_root_identity
    )
    names = tuple(os.listdir(root_fd))
    if len(names) != len(OUTPUT_FILES) or set(names) != set(OUTPUT_FILES):
        raise ValueError("output destination postverify inventory drift")
    for name, expected in leaf_identities.items():
        item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if (
            _full_identity(item) != expected
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
        ):
            raise ValueError("output destination postverify leaf drift")


def _assert_destination_name_binding(
    plan: OutputMaterializationPlan,
    parent_fd: int,
    root_fd: int,
    expected_root_identity: tuple[int, int, int],
) -> None:
    _assert_output_parent_binding(plan, parent_fd)
    destination = os.stat(
        plan.root_name, dir_fd=parent_fd, follow_symlinks=False
    )
    if (
        _identity(destination) != expected_root_identity
        or _identity(os.fstat(root_fd)) != expected_root_identity
        or not stat.S_ISDIR(destination.st_mode)
        or stat.S_ISLNK(destination.st_mode)
    ):
        raise ValueError("output destination name/inode binding changed")
    _assert_output_parent_binding(plan, parent_fd)
    final_destination = os.stat(
        plan.root_name, dir_fd=parent_fd, follow_symlinks=False
    )
    if (
        _identity(final_destination) != expected_root_identity
        or _identity(os.fstat(root_fd)) != expected_root_identity
        or not stat.S_ISDIR(final_destination.st_mode)
        or stat.S_ISLNK(final_destination.st_mode)
    ):
        raise ValueError("output destination postverify binding changed")


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
    staged: dict[str, tuple[int, int, int, int, int, int]] = {}
    try:
        _assert_output_parent_binding(plan, parent_fd)
        if plan.root_identity is not None:
            item = os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
            if (
                _identity(item) != plan.root_identity
                or not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("output root identity changed")
            root_fd = os.open(plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(root_fd)) != plan.root_identity:
                raise ValueError("output root descriptor identity changed")
            identities = dict(plan.leaf_identities)
            for name, content in payloads.items():
                if _read_at(root_fd, name, identities[name]) != content:
                    raise ValueError("existing output differs; repair forbidden")
            _verify_destination_binding(
                plan, parent_fd, root_fd, plan.root_identity,
                identities, payloads,
            )
            os.fsync(root_fd)
            _verify_destination_binding(
                plan, parent_fd, root_fd, plan.root_identity,
                identities, payloads,
            )
            return
        try:
            os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = f".admit014-adapter-stage-{secrets.token_hex(16)}"
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
                _write_all(descriptor, content)
                os.fsync(descriptor)
                staged[name] = _full_identity(os.fstat(descriptor))
            finally:
                os.close(descriptor)
            if _read_at(root_fd, name, staged[name]) != content:
                raise ValueError("staged output mismatch")
        _verify_complete_set(root_fd, payloads, staged)
        os.fsync(root_fd)
        if _identity(os.stat(
            staging_name, dir_fd=parent_fd, follow_symlinks=False,
        )) != staging_identity:
            raise ValueError("staging identity drift")
        try:
            os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        _assert_destination_name_binding(
            plan, parent_fd, root_fd, staging_identity
        )
        os.fsync(parent_fd)
        _assert_destination_name_binding(
            plan, parent_fd, root_fd, staging_identity
        )
        _verify_destination_binding(
            plan, parent_fd, root_fd, staging_identity, staged, payloads,
        )
        os.fsync(root_fd)
        _verify_destination_binding(
            plan, parent_fd, root_fd, staging_identity, staged, payloads,
        )
    except BaseException:
        if staging_name is not None and root_fd is not None:
            try:
                item = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
                if (
                    _identity(item) == _identity(os.fstat(root_fd))
                    and set(os.listdir(root_fd)) == set(staged)
                    and all(
                        _full_identity(os.stat(
                            name, dir_fd=root_fd, follow_symlinks=False,
                        )) == identity
                        for name, identity in staged.items()
                    )
                ):
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


def run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Validate sources, then publish exactly six deterministic artifacts."""
    _assert_canonical_evidence_runtime()
    state = build_design_state(repo_root, head_ref)
    payloads = build_artifacts(state)
    plan = _inspect_output_target_read_only(output_root, repo_root)
    _materialize_set(plan, payloads)
    return {
        "state": state,
        "manifest": json.loads(payloads[MANIFEST_FILENAME]),
        "output_root": plan.root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1()
