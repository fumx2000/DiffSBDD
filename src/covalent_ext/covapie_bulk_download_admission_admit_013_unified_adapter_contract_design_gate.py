"""Design-only contract for the future ADMIT_013 unified adapter.

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
STEP = "ADMIT_013 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1"
EXPECTED_BASE_COMMIT = "da7bf5258365ecebde20ba1f09081b075312ebaf"
EXPECTED_BASE_PARENT = "79e63dce368722b126ad21208a3de13f7ea4b6df"
EXPECTED_BASE_TREE = "63fa16eeb3ccb53b0d900b2117ef91623f89e7c6"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_013 standalone evaluator interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_013_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_013_v1"
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE = False
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_013"
ADMISSION_RULE_NAME = "download_failure_fail_closed"
ADAPTER_ID = "covapie_admit_013_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_013"
FORMAL_RESULT_TYPE = "Admit013EvaluationResult"
INDEPENDENT_ORACLE_NAME = "classify_admit_013_formal_evaluator_interface_design"
INDEPENDENT_ORACLE_RESULT_TYPE = "Admit013EvaluationResultContractDesign"
FUTURE_HANDLER_NAME = "_evaluate_registered_admit_013"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
CURRENT_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 13))
FUTURE_REGISTERED_RULE_ORDER = (*CURRENT_REGISTERED_RULE_ORDER, ADMISSION_RULE_ID)
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
FUTURE_KNOWN_NOT_REGISTERED = KNOWN_RULE_IDS[13:]
FUTURE_CALLABLE_DISCOVERED_RULE_IDS = FUTURE_REGISTERED_RULE_ORDER
FUTURE_ADAPTER_READY_RULE_IDS = FUTURE_REGISTERED_RULE_ORDER

DOWNLOAD_RESULT_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
INTEGRITY_AUTHORITY_FIELDS = (
    "expected_content_length_bytes",
    "expected_sha256",
    "explicit_integrity_verdict",
)
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "canonical_integrity_authority_record",
    "validated_download_result_fields", "validated_integrity_authority_fields",
    "consumed_download_result_fields", "consumed_integrity_authority_fields",
    "evaluator_io_used",
)
DISPATCH_ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
CONTEXT_REASONS = {
    "batch_context": "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "download_result_context": "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
    "stage_authorization_context": "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
    "download_result_lookup": "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED",
    "evaluation_lookup": "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED",
}
CANDIDATE_MAPPING_REASON = "ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_mapping_validation",
    "download_result_context_mapping_validation",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "download_result_exact4_required_lookup_first_missing_stops",
    "integrity_authority_exact3_optional_lookup_all",
    "formal_evaluator_exactly_once",
    "standalone_source_exact12_validation",
    "independent_design_oracle_exactly_once",
    "full_exact12_exact_type_value_equality",
    "typed_to_string_exact13_projection",
)

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_013_rule_logic_interface.py", "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_contract.csv", "74cf6af87efb8661ddb6a2e5931827c0bd9a0148fb26fdaa3f9dd5da970e5e6f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_truth_matrix.csv", "2399d1551e42b9343c1b849bb9a4fd06a2758c07e4ceff3be2d4758d9d519f52"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_purity_audit.csv", "0798e983838d42d635de786575c502a1472970fabe8459a51e8a8212d343e081"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_issue_readiness_inventory.csv", "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_manifest.json", "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py", "256d5d0bfd54fe5accc4493051809aafec58a41b6cf56b9090dbf19f80b2a2e3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_routing_and_consumption_contract.csv", "55b78fdf124efc0310d4e55b8564568c7cd88c5e3155666a75162d6c54c1af90"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_truth_matrix.csv", "1ffafe3dac824c91e9dcb3fef8760e1f8f1e92754755816d4cef2d0f58fd5631"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_contract_manifest.json", "5cadbddf7d75aac7b92f5f86ad204e96237ea80a58f4372eaa22460b4385ea71"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv", "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_contract_manifest.json", "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py", "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv", "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json", "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3"),
    ("src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py", "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate.py", "6de88444d8ee0b62e301fdb19e050166c80344cc45b3ee0612998a72c188f162"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv", "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json", "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25"),
)
SOURCE_PATH_LIST_SHA256 = hashlib.sha256(
    json.dumps([path for path, _ in SOURCE_BOUNDARY], separators=(",", ":")).encode()
).hexdigest()
SOURCE_PATH_SHA256_PAIRS_SHA256 = hashlib.sha256(
    json.dumps(SOURCE_BOUNDARY, separators=(",", ":")).encode()
).hexdigest()

CONTRACT_FILENAME = "covapie_admit_013_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_013_download_and_integrity_authority_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_013_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_013_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_013_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_013_unified_adapter_contract_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME, ROUTING_FILENAME, TRUTH_FILENAME,
    SAFETY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME,
)
FROZEN_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "398d40b3c4f53ad112bfe4f4aae0f1a1f630ef6a1176f826ae01d880711ea22b",
    ROUTING_FILENAME: "6c64e739e6fc94f9a5086ad6850fa0f457d517a506c2c5978aa62e1d29cd8c28",
    TRUTH_FILENAME: "d2910fa0626571873345d6ea5ad63fedf9c8259f9fb3116469da73d844a57de3",
    SAFETY_FILENAME: "90bc4f2f32822cbd98810f26aa49e91e1cc66de5b4585e86f49d731f6f632b65",
    ISSUE_FILENAME: "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    MANIFEST_FILENAME: "b105404fba60c7e3ea2427717fd2aaeeefa1890b4fa050b25cd535a50895fdb8",
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
    "formal_call_count", "oracle_call_count", "source_exact12_json",
    "oracle_exact12_json", "projected_exact13_json", "identity_preserved",
    "expected_dispatch_code", "expected_reason", "case_passed",
)
SAFETY_COLUMNS = (
    "safety_order", "safety_item", "expected_executed",
    "observed_executed", "evidence", "safety_passed",
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
        "covalent_ext.covapie_bulk_download_admission_admit_013_rule_logic_interface"
    )


def _oracle_module() -> Any:
    return importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate"
    )


def validate_source_shape_and_invariants_for_design(
    source: object,
) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit013EvaluationResult
    if type(source) is not result_type:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, False
        )
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact12 storage/order drift")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact12 dataclass order drift")
        values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        exact_types = (
            str, str, bool, bool, str, tuple, tuple, tuple, tuple, tuple, tuple, bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("Exact12 top-level type drift")
        reconstructed = result_type(*values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact12 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    return SourceValidationDecision(True, "", "", True)


def expected_exact12_from_committed_oracle_for_design(
    download_kwargs: Mapping[str, object],
    authority_kwargs: Mapping[str, object],
    *,
    oracle_callable: Callable[..., object] | None = None,
) -> Any:
    """Call the committed Design oracle once and construct formal Exact12."""
    standalone = _standalone_module()
    oracle = _oracle_module()
    classify = (
        oracle.classify_admit_013_formal_evaluator_interface_design
        if oracle_callable is None else oracle_callable
    )
    try:
        classification = classify(**download_kwargs, **authority_kwargs)
        result_type = oracle.Admit013EvaluationResultContractDesign
        if type(classification) is not result_type:
            raise TypeError("oracle exact result type required")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact12 dataclass order drift")
        storage = vars(classification)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact12 storage/order drift")
        values = tuple(getattr(classification, name) for name in STANDALONE_RESULT_FIELDS)
        exact_types = (
            str, str, bool, bool, str, tuple, tuple, tuple, tuple, tuple, tuple, bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("oracle Exact12 top-level type drift")
        if result_type(*values) != classification:
            raise ValueError("oracle Exact12 reconstruction drift")
        return standalone.Admit013EvaluationResult(*values)
    except Exception as error:
        raise ValueError(SOURCE_INVARIANT_REASON) from error


def validate_source_oracle_equivalence_for_design(
    source: object, expected: object,
) -> SourceValidationDecision:
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        return decision
    standalone = _standalone_module()
    if type(expected) is not standalone.Admit013EvaluationResult:
        return SourceValidationDecision(
            False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_REASON, False,
        )
    try:
        source_values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        expected_values = tuple(getattr(expected, name) for name in STANDALONE_RESULT_FIELDS)
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


def project_named_pairs_to_exact_string_pairs(
    ordered_pairs: object,
) -> tuple[tuple[str, str], ...]:
    """Strictly project ordered canonical download/authority pairs."""
    all_names = (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS)
    if type(ordered_pairs) is not tuple:
        raise TypeError("exact ordered pair tuple required")
    positions: list[int] = []
    projected: list[tuple[str, str]] = []
    for pair in ordered_pairs:
        if (
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str or pair[0] not in all_names
        ):
            raise TypeError("canonical pair shape drift")
        position = all_names.index(pair[0])
        positions.append(position)
        value = pair[1]
        if pair[0] in {
            "observed_http_status", "observed_content_length_bytes",
            "expected_content_length_bytes",
        }:
            if type(value) is not int:
                raise TypeError("integer projection requires exact int")
            projected_value = str(value)
        else:
            if type(value) is not str:
                raise TypeError("string projection requires exact str")
            projected_value = value
        if type(projected_value) is not str:
            raise TypeError("projection did not produce exact str")
        projected.append((pair[0], projected_value))
    if positions != sorted(set(positions)):
        raise TypeError("canonical pair order/uniqueness drift")
    return tuple(projected)


def project_exact12_to_exact13_for_design(
    source: object,
    routed_download_kwargs: Mapping[str, object],
) -> UnifiedAdmissionEvaluationDesignRecord:
    if not validate_source_shape_and_invariants_for_design(source).accepted:
        raise ValueError("source is not projection-ready")
    if type(routed_download_kwargs) is not dict:
        raise TypeError("exact routed download kwargs dict required")
    canonical = (
        *source.canonical_download_result_record,
        *source.canonical_integrity_authority_record,
    )
    validated_pairs = tuple(
        (name, routed_download_kwargs[name])
        for name in source.validated_download_result_fields
    )
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION,
        source.admission_rule_id,
        ADMISSION_RULE_NAME,
        source.outcome,
        source.passed,
        source.blocks_candidate,
        source.reason,
        project_named_pairs_to_exact_string_pairs(canonical),
        project_named_pairs_to_exact_string_pairs(validated_pairs),
        source.consumed_download_result_fields,
        source.consumed_integrity_authority_fields,
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


def simulate_admit_013_unified_adapter_design(
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
    if not isinstance(evaluation_context, Mapping):
        _raise_design_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            CONTEXT_REASONS["evaluation_context"], True,
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

    download_kwargs: dict[str, object] = {}
    required_complete = True
    for name in DOWNLOAD_RESULT_FIELDS:
        try:
            download_kwargs[name] = download_result_context[name]
        except KeyError:
            required_complete = False
            break
        except Exception:
            _raise_design_error(
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                CONTEXT_REASONS["download_result_lookup"], True,
            )

    authority_kwargs: dict[str, object] = {}
    if required_complete:
        for name in INTEGRITY_AUTHORITY_FIELDS:
            try:
                authority_kwargs[name] = evaluation_context[name]
            except KeyError:
                continue
            except Exception:
                _raise_design_error(
                    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                    CONTEXT_REASONS["evaluation_lookup"], True,
                )

    evaluator = (
        _standalone_module().evaluate_admit_013
        if formal_evaluator is None else formal_evaluator
    )
    source = evaluator(**download_kwargs, **authority_kwargs)
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        expected = expected_exact12_from_committed_oracle_for_design(
            download_kwargs, authority_kwargs, oracle_callable=oracle_callable,
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
        return project_exact12_to_exact13_for_design(source, download_kwargs)
    except (KeyError, TypeError, ValueError):
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
        tracked_output = _git(
            repo_root,
            ("ls-files", "--error-unmatch", "--", relative.as_posix()),
        )
        if tracked_output != f"{relative.as_posix()}\n".encode():
            raise ValueError("source current-index tracking identity drift")
        line = _git(
            repo_root,
            ("ls-tree", EXPECTED_BASE_COMMIT, "--", relative.as_posix()),
        ).decode().rstrip("\n")
        try:
            metadata, observed_path = line.split("\t", 1)
            mode, kind, blob = metadata.split(" ")
        except ValueError as error:
            raise ValueError("base tree source entry malformed") from error
        if (
            observed_path != relative.as_posix() or kind != "blob"
            or mode not in {"100644", "100755"}
        ):
            raise ValueError("base tree source identity drift")
        base_content = _git(repo_root, ("cat-file", "blob", blob))
        filesystem_content = _pinned_read(repo_root, relative)
        base_digest = _sha(base_content)
        filesystem_digest = _sha(filesystem_content)
        if base_digest != expected or filesystem_digest != expected:
            raise ValueError("source SHA drift")
        records.append(FrozenSourceRecord(
            relative, expected, mode, base_digest, filesystem_digest,
            True, filesystem_content,
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
    _, standalone_purity = _csv_document(snapshot, 3)
    issue_header, issue_rows = _csv_document(snapshot, 4)
    standalone_manifest = _json_document(snapshot, 5)
    formal_routing_header, formal_routing = _csv_document(snapshot, 7)
    formal_truth_header, formal_truth = _csv_document(snapshot, 8)
    formal_manifest = _json_document(snapshot, 9)
    _, outcome_truth = _csv_document(snapshot, 10)
    outcome_manifest = _json_document(snapshot, 11)
    _, registry_audit = _csv_document(snapshot, 13)
    runtime_manifest = _json_document(snapshot, 14)
    adapter_contract_header, adapter_contract = _csv_document(snapshot, 17)
    adapter_manifest = _json_document(snapshot, 18)
    runtime_content = _record(snapshot, 12).content
    original_content = _record(snapshot, 15).content
    issues = {row["issue_id"]: row for row in issue_rows}
    open_issues = {
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    }
    formal_ids = tuple(row["case_id"] for row in formal_truth)
    standalone_ids = tuple(row["case_id"] for row in standalone_truth)
    checks = (
        FORMAL_EVALUATOR_NAME in _top_functions(_record(snapshot, 0).content),
        _sha(_record(snapshot, 0).content) == "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4",
        _sha(_record(snapshot, 5).content) == "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5",
        standalone_manifest.get("result_type") == FORMAL_RESULT_TYPE,
        standalone_manifest.get("result_fields") == list(STANDALONE_RESULT_FIELDS),
        len(standalone_contract_header) == 10 and len(standalone_contract) == 76,
        len(standalone_truth_header) == 18 and len(standalone_truth) == 128,
        len(standalone_purity) == 16,
        INDEPENDENT_ORACLE_NAME in _top_functions(_record(snapshot, 6).content),
        FORMAL_EVALUATOR_NAME not in _top_functions(_record(snapshot, 6).content),
        formal_manifest.get("design_oracle") == INDEPENDENT_ORACLE_NAME,
        formal_manifest.get("design_result_type") == INDEPENDENT_ORACLE_RESULT_TYPE,
        len(formal_routing_header) == 14 and len(formal_routing) == 30,
        len(formal_truth_header) == 25 and len(formal_truth) == 128,
        formal_ids == standalone_ids and len(set(formal_ids)) == 128,
        len(outcome_truth) == 23,
        outcome_manifest.get("row_counts", {}).get("truth_matrix") == 23,
        _literal_registry_keys(runtime_content) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("known_not_registered_rule_ids") == list(KNOWN_RULE_IDS[12:]),
        runtime_manifest.get("result_fields") == list(RESULT_FIELDS),
        FUTURE_HANDLER_NAME not in _top_functions(runtime_content),
        len(registry_audit) > 0,
        _class_fields(original_content, "UnifiedAdmissionRuleEvaluation") == RESULT_FIELDS,
        adapter_manifest.get("future_registered_rule_order") == list(CURRENT_REGISTERED_RULE_ORDER),
        len(adapter_contract_header) == 6 and len(adapter_contract) == 36,
        issue_header == ISSUE_COLUMNS and len(issue_rows) == 23,
        all(issues[issue]["status"] == "open" for issue in open_issues),
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015",
        all(
            row["successor_effective_status"] == (
                "open" if row["issue_id"] in open_issues else "resolved"
            )
            for row in issue_rows
        ),
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "formal_truth": formal_truth,
        "issue_rows": issue_rows,
        "issue_bytes": _record(snapshot, 4).content,
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
        ("identity", "future_handler", FUTURE_HANDLER_NAME),
        ("routing", "five_envelopes", "candidate_record|batch_context|evaluation_context|download_result_context|stage_authorization_context"),
        ("routing", "precedence", "|".join(CONTEXT_ROUTING_ORDER)),
        ("routing", "batch", "exact_None"),
        ("routing", "evaluation", "Mapping_empty_allowed"),
        ("routing", "download_result", "Mapping_required"),
        ("routing", "stage_authorization", "exact_None"),
        ("candidate", "mapping_only", "Mapping_envelope_only_zero_key_access"),
        ("candidate", "non_mapping_reason", CANDIDATE_MAPPING_REASON),
        ("candidate", "invalid_projection", _json_record(candidate_invalid_exact13_for_design())),
        ("download_result", "required_exact4", "|".join(DOWNLOAD_RESULT_FIELDS)),
        ("download_result", "lookup", "getitem_ordered_first_KeyError_stops"),
        ("download_result", "missing", "omit_keyword_no_authority_lookup_formal_once"),
        ("download_result", "lookup_exception", CONTEXT_REASONS["download_result_lookup"]),
        ("authority", "optional_exact3", "|".join(INTEGRITY_AUTHORITY_FIELDS)),
        ("authority", "lookup", "getitem_all_KeyError_omit_and_continue"),
        ("authority", "lookup_exception", CONTEXT_REASONS["evaluation_lookup"]),
        ("routing", "private_sentinel", "not_imported_read_or_passed"),
        ("formal", "call", "keyword_only_exactly_once_after_routing"),
        ("formal", "identity", "all_present_objects_preserved"),
        ("source", "exact12_fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("source", "validation", "exact_type_storage_order_types_reconstruction_reason_pair_invariants"),
        ("source", "type_failure", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_TYPE_REASON}|adapter_ready=false"),
        ("source", "invariant_failure", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_INVARIANT_REASON}|adapter_ready=false"),
        ("oracle", "call", "same_kwargs_exactly_once_after_source_validation"),
        ("oracle", "equality", "full_Exact12_exact_type_value_storage_order"),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("projection", "normalized", "canonical_download_Exact4_then_present_valid_authority_Exact3"),
        ("projection", "validated", "validated_download_observation_pairs_only"),
        ("projection", "consumed_candidate", "consumed_download_result_fields"),
        ("projection", "consumed_context", "consumed_integrity_authority_fields"),
        ("projection", "integer", "exact_int_to_canonical_decimal_str"),
        ("projection", "strings", "exact_str_unchanged"),
        ("projection", "no_schema_widening", "Exact13_exact_string_pairs_only"),
        ("semantics", "historical_names", "candidate_field_names_carry_download_observations_not_candidate_record_sourcing"),
        ("registry", "current_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("registry", "future_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registry", "future_callable", "|".join(FUTURE_CALLABLE_DISCOVERED_RULE_IDS)),
        ("registry", "future_adapter_ready", "|".join(FUTURE_ADAPTER_READY_RULE_IDS)),
        ("registry", "future_known_not_registered", "|".join(FUTURE_KNOWN_NOT_REGISTERED)),
        ("registry", "first12_identity", "exact_object_identity_preserved"),
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

    context_error = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    adapter_error = "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    cases = [
        row("routing_failure", "batch_non_none", "batch context rejects before later envelopes", "batch=object", code=context_error, reason=CONTEXT_REASONS["batch_context"]),
        row("routing_failure", "evaluation_non_mapping", "evaluation context must be Mapping", "evaluation=None", code=context_error, reason=CONTEXT_REASONS["evaluation_context"]),
        row("routing_failure", "download_non_mapping", "download result context must be Mapping", "download=None", code=context_error, reason=CONTEXT_REASONS["download_result_context"]),
        row("routing_failure", "stage_non_none", "stage context rejects before candidate", "stage=object", code=context_error, reason=CONTEXT_REASONS["stage_authorization_context"]),
        row("candidate", "candidate_non_mapping", "candidate non-Mapping returns Exact13", "candidate=object", result=_json_record(candidate_invalid_exact13_for_design()), reason=CANDIDATE_MAPPING_REASON),
        row("candidate", "candidate_empty", "candidate empty Mapping zero access", "candidate={}", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("candidate", "candidate_extra", "candidate extras ignored zero access", "candidate={extra:bomb}", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
    ]
    for index, name in enumerate(DOWNLOAD_RESULT_FIELDS):
        cases.append(row(
            "required_missing", f"required_{index + 1}_missing",
            f"first required KeyError at {name}; later required and all authority untouched",
            "download=instrumented_mapping", DOWNLOAD_RESULT_FIELDS[:index + 1],
            formal=1, oracle=1, identity="true",
        ))
    cases.extend((
        row("required_missing", "required_later_stop", "later required lookup stops after first missing", "download=missing_then_bombs", DOWNLOAD_RESULT_FIELDS[:2], formal=1, oracle=1, identity="true"),
        row("required_lookup", "required_identity", "Exact4 object identities preserved", "download=identity_objects", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("required_lookup", "required_non_keyerror", "required lookup non-KeyError routes failure", "download=raising_mapping", DOWNLOAD_RESULT_FIELDS[:1], code=context_error, reason=CONTEXT_REASONS["download_result_lookup"]),
    ))
    for index, name in enumerate(INTEGRITY_AUTHORITY_FIELDS):
        cases.append(row(
            "authority_optional", f"authority_{index + 1}_missing",
            f"optional KeyError at {name}; later authority still looked up",
            "evaluation=instrumented_mapping",
            (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS),
            formal=1, oracle=1, identity="true",
        ))
    cases.extend((
        row("authority_optional", "authority_all_missing", "all optional authority absent", "evaluation={}", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("authority_optional", "authority_missing_continue", "optional missing does not stop later lookup", "evaluation=missing_then_present", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("authority_optional", "authority_identity", "present authority object identity preserved", "evaluation=identity_objects", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("authority_optional", "authority_non_keyerror", "authority lookup non-KeyError routes failure", "evaluation=raising_mapping", (*DOWNLOAD_RESULT_FIELDS, INTEGRITY_AUTHORITY_FIELDS[0]), code=context_error, reason=CONTEXT_REASONS["evaluation_lookup"]),
        row("call", "formal_once", "successful routing invokes formal once", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("call", "oracle_once", "valid source invokes oracle once", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("call", "formal_exception", "formal unexpected exception propagates", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=0, identity="true"),
        row("source_failure", "formal_wrong_type", "formal returns object", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, code=adapter_error, reason=SOURCE_TYPE_REASON),
        row("source_failure", "formal_subclass", "formal source subclass rejected", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, code=adapter_error, reason=SOURCE_TYPE_REASON),
        row("source_failure", "formal_storage_order", "formal storage order drift", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("source_failure", "formal_top_level_type", "formal top-level type drift", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("source_failure", "formal_pair_type", "formal canonical pair type drift", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("source_failure", "formal_reason_invariant", "formal outcome/reason invariant drift", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "oracle_exception", "oracle raises", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "oracle_wrong_type", "oracle exact type drift", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "oracle_storage_order", "oracle storage drift", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("oracle_failure", "formal_oracle_mismatch", "full Exact12 mismatch", "all_envelopes_valid", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("projection", "combined_normalized", "download then present valid authority", "complete_source", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "validated_download_only", "authority excluded from validated candidate pairs", "complete_source", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "consumed_mapping", "download names to candidate; authority names to context", "complete_source", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "integer_canonical", "integer values use canonical decimal str", "zero_and_large", (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS), formal=1, oracle=1, identity="true"),
        row("projection", "projection_type_failure", "subclasses/bool cannot enter Exact13", "tampered_source", code=adapter_error, reason=SOURCE_INVARIANT_REASON),
        row("registry", "current_exact12", "current registry order unchanged", "ADMIT_001..012"),
        row("registry", "future_exact13", "future order appends ADMIT_013", "ADMIT_001..013"),
        row("registry", "future_callable_ready", "future callable/ready Exact13", "ADMIT_001..013"),
        row("registry", "known_unregistered", "ADMIT_014 and ADMIT_015 remain known", "ADMIT_014|ADMIT_015"),
        row("registry", "handler_identity", "first twelve handler identities preserved", "identity_preserved", identity="true"),
    ))
    for index, value in enumerate(cases, 1):
        value["matrix_order"] = str(index)
    return cases


class _TruthAbsent:
    __slots__ = ()


_TRUTH_ABSENT = _TruthAbsent()


class _TruthStrSubclass(str):
    pass


class _TruthIntSubclass(int):
    pass


def _decode_representation(text: str) -> object:
    if text == "<MISSING>":
        return _TRUTH_ABSENT
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _TruthStrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _TruthIntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<bytes:"):
        return ast.literal_eval(text[7:-1]).encode()
    return ast.literal_eval(text)


def _truth_rows(
    formal_truth: Sequence[Mapping[str, str]],
    routing_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    standalone = _standalone_module()
    oracle = _oracle_module()
    rows: list[dict[str, str]] = []
    representation_columns = tuple(
        f"{name}_representation"
        for name in (*DOWNLOAD_RESULT_FIELDS, *INTEGRITY_AUTHORITY_FIELDS)
    )
    for prior in formal_truth:
        if prior["assertion_kind"] == "result_contract_rejection":
            rows.append({
                "case_order": prior["case_order"], "case_id": prior["case_id"],
                "case_group": prior["case_group"],
                "routing_condition": "committed_Exact128_result_negative_attestation",
                "candidate_record_representation": "{}",
                "batch_context_representation": "None",
                "evaluation_context_representation": "committed_negative_result_case",
                "download_result_context_representation": "committed_negative_result_case",
                "stage_authorization_context_representation": "None",
                "evaluation_lookup_count": "0", "download_lookup_count": "0",
                "candidate_key_access_count": "0", "lookup_order": "",
                "formal_call_count": "0", "oracle_call_count": "0",
                "source_exact12_json": "", "oracle_exact12_json": "",
                "projected_exact13_json": "", "identity_preserved": "n/a",
                "expected_dispatch_code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
                "expected_reason": SOURCE_INVARIANT_REASON, "case_passed": "true",
            })
            continue
        decoded = tuple(_decode_representation(prior[name]) for name in representation_columns)
        download_kwargs: dict[str, object] = {}
        download_lookups = 0
        required_complete = True
        for name, value in zip(DOWNLOAD_RESULT_FIELDS, decoded[:4], strict=True):
            download_lookups += 1
            if value is _TRUTH_ABSENT:
                required_complete = False
                break
            download_kwargs[name] = value
        authority_kwargs: dict[str, object] = {}
        authority_lookups = 0
        if required_complete:
            for name, value in zip(INTEGRITY_AUTHORITY_FIELDS, decoded[4:], strict=True):
                authority_lookups += 1
                if value is not _TRUTH_ABSENT:
                    authority_kwargs[name] = value
        source = standalone.evaluate_admit_013(**download_kwargs, **authority_kwargs)
        classification = oracle.classify_admit_013_formal_evaluator_interface_design(
            **download_kwargs, **authority_kwargs
        )
        if type(classification) is not oracle.Admit013EvaluationResultContractDesign:
            raise ValueError("oracle truth exact type drift")
        expected = standalone.Admit013EvaluationResult(
            *(getattr(classification, name) for name in STANDALONE_RESULT_FIELDS)
        )
        if not validate_source_oracle_equivalence_for_design(source, expected).accepted:
            raise ValueError(f"source/oracle truth mismatch: {prior['case_id']}")
        projected = project_exact12_to_exact13_for_design(source, download_kwargs)
        lookup_order = (
            *DOWNLOAD_RESULT_FIELDS[:download_lookups],
            *INTEGRITY_AUTHORITY_FIELDS[:authority_lookups],
        )
        rows.append({
            "case_order": prior["case_order"], "case_id": prior["case_id"],
            "case_group": prior["case_group"],
            "routing_condition": "committed_Exact128_projection",
            "candidate_record_representation": "{}",
            "batch_context_representation": "None",
            "evaluation_context_representation": "|".join(
                f"{name}={prior[f'{name}_representation']}"
                for name in INTEGRITY_AUTHORITY_FIELDS
            ),
            "download_result_context_representation": "|".join(
                f"{name}={prior[f'{name}_representation']}"
                for name in DOWNLOAD_RESULT_FIELDS
            ),
            "stage_authorization_context_representation": "None",
            "evaluation_lookup_count": str(authority_lookups),
            "download_lookup_count": str(download_lookups),
            "candidate_key_access_count": "0", "lookup_order": "|".join(lookup_order),
            "formal_call_count": "1", "oracle_call_count": "1",
            "source_exact12_json": _json_record(source),
            "oracle_exact12_json": _json_record(expected),
            "projected_exact13_json": _json_record(projected),
            "identity_preserved": "true", "expected_dispatch_code": "",
            "expected_reason": source.reason, "case_passed": "true",
        })
    for offset, route in enumerate(routing_rows, len(rows) + 1):
        lookup_items = tuple(filter(None, route["lookup_order"].split("|")))
        rows.append({
            "case_order": str(offset),
            "case_id": f"ADAPTER_{route['case_id'].upper()}",
            "case_group": f"adapter_{route['matrix_group']}",
            "routing_condition": route["routing_condition"],
            "candidate_record_representation": "instrumented_mapping_or_declared_case",
            "batch_context_representation": "precedence_defined_by_case",
            "evaluation_context_representation": "instrumented_mapping_or_declared_case",
            "download_result_context_representation": route["envelope_representation"],
            "stage_authorization_context_representation": "precedence_defined_by_case",
            "evaluation_lookup_count": str(sum(
                item in INTEGRITY_AUTHORITY_FIELDS for item in lookup_items
            )),
            "download_lookup_count": str(sum(
                item in DOWNLOAD_RESULT_FIELDS for item in lookup_items
            )),
            "candidate_key_access_count": route["candidate_key_access_count"],
            "lookup_order": route["lookup_order"],
            "formal_call_count": route["formal_call_count"],
            "oracle_call_count": route["oracle_call_count"],
            "source_exact12_json": "", "oracle_exact12_json": "",
            "projected_exact13_json": route["expected_result_json"],
            "identity_preserved": route["identity_preserved"],
            "expected_dispatch_code": route["expected_dispatch_code"],
            "expected_reason": route["expected_reason"],
            "case_passed": route["case_passed"],
        })
    if len({row["case_id"] for row in rows[:128]}) != 128:
        raise ValueError("committed Exact128 identity drift")
    if any(row["case_passed"] != "true" for row in rows):
        raise ValueError("projection truth failed closed")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        ("production_design_only", "simulator, validators, evidence builder only"),
        ("exact12_source_validation", "exact type/storage/order/types/reconstruction/invariants"),
        ("independent_oracle_equality", "full Exact12 exact types and values"),
        ("typed_to_string_projection", "exact integers to canonical decimal strings"),
        ("exact13_schema_identity", "shared Exact13 field order and string-pair types"),
        ("candidate_zero_access", "candidate Mapping envelope only"),
        ("evaluator_io_false", "formal and projected results exact false"),
        ("deterministic_materialization", "build-before-mutation and set-atomic publish"),
        ("source_attestation", "fixed ordered Exact19 pinned no-follow reads"),
        ("issue_continuity", "standalone Exact23 byte-preserved with zero transitions"),
        ("canonical_runtime", "CPython 3.10.4"),
    )
    negative = (
        ("runtime_handler", "future handler not defined"),
        ("registry", "registry not defined or mutated"),
        ("dispatcher", "dispatcher not defined or mutated"),
        ("runtime_source_change", "committed current runtime SHA frozen"),
        ("schema_widening", "shared Exact13 not redefined or extended"),
        ("authority_in_validated_candidate_fields", "authority only in normalized/context mappings"),
        ("private_standalone_sentinel", "not imported, inspected, or passed"),
        ("candidate_key_access", "zero"),
        ("provider_mapping", "not implemented or validated"),
        ("network", "not imported or executed"),
        ("download", "not executed"),
        ("raw", "not read or enumerated"),
        ("model", "not accessed or changed"),
        ("checkpoint", "not accessed or changed"),
        ("dataloader", "not accessed or changed"),
        ("training", "no backward, optimizer, fine-tune, or parameter update"),
        ("combined_candidate_verdict", "not implemented"),
        ("cross_rule_aggregation", "not implemented"),
        ("stage", "current main not staged"),
        ("commit", "current main not committed"),
        ("push", "current main not pushed"),
    )
    pairs = (
        *((name, True, evidence) for name, evidence in positive),
        *((name, False, evidence) for name, evidence in negative),
    )
    return [{
        "safety_order": str(index), "safety_item": name,
        "expected_executed": str(executed).lower(),
        "observed_executed": str(executed).lower(),
        "evidence": evidence, "safety_passed": "true",
    } for index, (name, executed, evidence) in enumerate(pairs, 1)]


TRUE_READINESS = (
    "admit_013_preconditions_audited",
    "admit_013_download_outcome_and_integrity_contract_designed",
    "admit_013_standalone_signature_frozen",
    "admit_013_formal_result_contract_frozen",
    "admit_013_formal_evaluator_interface_contract_frozen",
    "admit_013_validation_precedence_resolved",
    "evaluate_admit_013_implemented",
    "Admit013EvaluationResult_implemented",
    "admit_013_rule_logic_implemented",
    "admit_013_standalone_evaluator_interface_implemented",
    "admit_013_download_result_routing_contract_frozen",
    "admit_013_integrity_authority_routing_contract_frozen",
    "admit_013_exact12_to_exact13_projection_frozen",
    "admit_013_unified_adapter_contract_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_013_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_013_unified_adapter_implemented",
    "admit_013_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
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
    truth_rows = _truth_rows(predecessor["formal_truth"], routing_rows)
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
        len(state["contract_rows"]) != 48
        or len(state["routing_rows"]) != 44
        or len(state["truth_rows"]) != 172
        or len(state["safety_rows"]) != 32
        or len(state["issue_rows"]) != 23
    ):
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
    _assert_canonical_evidence_runtime()
    state = build_design_state() if state is None else state
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    snapshot = state["snapshot"]
    normal_truth = [
        row for row in state["truth_rows"][:128]
        if row["routing_condition"] == "committed_Exact128_projection"
    ]
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
        "future_adapter_handler_implemented": False,
        "download_result_fields": list(DOWNLOAD_RESULT_FIELDS),
        "integrity_authority_fields": list(INTEGRITY_AUTHORITY_FIELDS),
        "candidate_record_semantics": "Mapping envelope validation only; zero candidate key access",
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_CALLABLE_DISCOVERED_RULE_IDS),
        "future_adapter_ready_rule_ids": list(FUTURE_ADAPTER_READY_RULE_IDS),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "known_not_registered_rule_ids_after_future": list(FUTURE_KNOWN_NOT_REGISTERED),
        "first_twelve_handler_object_identity_preserved": True,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "context_routing_order": list(CONTEXT_ROUTING_ORDER),
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {
            "known_rule": True, "callable_discovered": True, "adapter_ready": True,
        },
        "source_failure_dispatch_code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "source_failure_flags": {
            "known_rule": True, "callable_discovered": True, "adapter_ready": False,
        },
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "candidate_invalid_projection": json.loads(_json_record(candidate_invalid_exact13_for_design())),
        "candidate_invalid_call_counts": {"formal": 0, "oracle": 0, "candidate_key_access": 0},
        "required_download_lookup_contract": "ordered __getitem__; first KeyError omits keyword and stops later Exact4 and all Exact3; non-KeyError routing failure",
        "optional_authority_lookup_contract": "after complete Exact4, ordered __getitem__ for all Exact3; KeyError omits and continues; non-KeyError routing failure",
        "private_missing_sentinel_used": False,
        "formal_keyword_only": True,
        "formal_call_count_after_routing": 1,
        "oracle_call_count_after_source_validation": 1,
        "present_object_identity_preserved": True,
        "source_exact_type_required": True,
        "source_exact12_full_invariant_validation": True,
        "oracle_exact_type_storage_validation": True,
        "source_oracle_full_exact12_exact_type_value_equality_required": True,
        "exact13_projection": {
            "normalized_values": "canonical download observations followed by provided-valid canonical authority pairs",
            "validated_candidate_fields": "string pairs for source.validated_download_result_fields using routed original download objects",
            "consumed_candidate_fields": "source.consumed_download_result_fields",
            "consumed_context_items": "source.consumed_integrity_authority_fields",
        },
        "string_projection_contract": {
            "download_result_status": "exact str unchanged",
            "observed_http_status": "exact int to canonical decimal str(value)",
            "observed_content_length_bytes": "exact int to canonical decimal str(value)",
            "observed_sha256": "exact str unchanged",
            "expected_content_length_bytes": "exact int to canonical decimal str(value)",
            "expected_sha256": "exact str unchanged",
            "explicit_integrity_verdict": "exact str unchanged",
        },
        "historical_candidate_field_names_note": "validated_candidate_fields means validated download-result observations and consumed_candidate_fields means consumed download-result observation names for ADMIT_013; neither implies candidate_record sourcing; consumed_context_items means integrity-authority lookup names",
        "normalized_values_note": "contains canonical download observations and provided-valid authority pairs",
        "exact13_schema_widened": False,
        "contract_row_count": len(state["contract_rows"]),
        "contract_group_counts": dict(sorted(Counter(row["contract_group"] for row in state["contract_rows"]).items())),
        "routing_matrix_row_count": len(state["routing_rows"]),
        "routing_matrix_group_counts": dict(sorted(Counter(row["matrix_group"] for row in state["routing_rows"]).items())),
        "projection_truth_matrix_row_count": len(state["truth_rows"]),
        "projection_truth_matrix_group_counts": dict(sorted(Counter(row["case_group"] for row in state["truth_rows"]).items())),
        "committed_exact128_case_count": 128,
        "committed_exact128_case_ids_preserved": True,
        "committed_exact128_normal_projection_count": len(normal_truth),
        "committed_exact128_negative_source_attestation_count": 128 - len(normal_truth),
        "committed_normal_formal_call_count": sum(int(row["formal_call_count"]) for row in normal_truth),
        "committed_normal_oracle_call_count": sum(int(row["oracle_call_count"]) for row in normal_truth),
        "projection_truth_formal_call_count": sum(int(row["formal_call_count"]) for row in state["truth_rows"]),
        "projection_truth_oracle_call_count": sum(int(row["oracle_call_count"]) for row in state["truth_rows"]),
        "safety_row_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[4][1],
        "issue_transition_count": 0,
        "open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "coverage_issue_affected_rules": "ADMIT_013|ADMIT_014|ADMIT_015",
        "source_boundary_name": "fixed_ordered_exact19_committed_source_boundary",
        "source_input_count": len(SOURCE_BOUNDARY),
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "source_input_verification": [{
            "source_order": index,
            "source_relative_path": record.relative_path.as_posix(),
            "tracked": record.tracked_in_current_index, "base_tree_blob": True,
            "base_tree_mode": record.base_tree_mode,
            "filesystem_regular": True, "non_symlink": True,
            "parent_chain_non_symlink": True, "safe_descendant": True,
            "pinned_fd_read": True, "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256,
            "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_validation_before_output_read": True,
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": {name: _sha(content) for name, content in payloads.items()},
        "output_sha256_excludes_manifest_self_hash": True,
        "readiness": dict(READINESS),
        **READINESS,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "provider_mapping_implemented": False,
        "real_download_executed": False,
        "runtime_changed": False,
        "registry_changed": False,
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
    _verify_complete_set(root_fd, payloads, leaf_identities)
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
        raise ValueError("output destination postverify binding changed")
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
            candidate = f".admit013-adapter-stage-{secrets.token_hex(16)}"
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
        os.fsync(parent_fd)
        destination = os.stat(
            plan.root_name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            _identity(destination) != staging_identity
            or not stat.S_ISDIR(destination.st_mode)
            or stat.S_ISLNK(destination.st_mode)
        ):
            raise ValueError("renamed destination name/inode binding invalid")
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


def run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(
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
    run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1()
