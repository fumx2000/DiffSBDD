#!/usr/bin/env python3
"""Checker-owned verification for the ADMIT_008 unified-adapter design gate."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import re
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "covalent_ext.covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE = "39f077e9e5ea460f9199fb8921e89bcd46087fa8"
EXPECTED_SUBJECT = "add CovaPIE standalone ADMIT_008 rule logic interface v1"
RULE_ID = "ADMIT_008"
RULE_NAME = "topology_restoration_disposition"
ADAPTER_ID = "covapie_admit_008_unified_adapter_v1"
FORMAL_EVALUATOR = "evaluate_admit_008"
FORMAL_SOURCE = "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py"
ORACLE_ID = "classify_admit_008_topology_restoration_disposition_design"
SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_008_v1"
FUTURE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 9))
CURRENT_ORDER = FUTURE_ORDER[:7]
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("topology_restoration_disposition",)
CONTEXT_ITEMS = ("allowed_topology_restoration_dispositions",)
ENUM_MEMBERS = (
    "approved_restoration_template", "explicit_manual_review_approved",
    "manual_review_required", "quarantine_required",
)
ALLOWED = ENUM_MEMBERS[:2]
SCALAR_REASONS = (
    "TOPOLOGY_RESTORATION_DISPOSITION_TYPE_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_EMPTY",
    "TOPOLOGY_RESTORATION_DISPOSITION_NON_ASCII",
    "TOPOLOGY_RESTORATION_DISPOSITION_SYNTAX_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_UNKNOWN",
)
CONTEXT_VALUE_REASONS = (
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_TYPE_INVALID",
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_CONTENT_INVALID",
)
BLOCKED_REASONS = {
    "manual_review_required": "TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED",
    "quarantine_required": "TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED",
}
MISSING_REASON = "topology_restoration_disposition_missing"
CANDIDATE_REASON = "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_REASONS = {
    "batch_context": "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED",
    "download_result_context": "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome", "passed",
    "blocks_candidate", "reason", "normalized_values", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_topology_restoration_disposition", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
ERROR_FIELDS = ("code", "admission_rule_id", "known_rule", "callable_discovered", "adapter_ready", "reason")
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
EXECUTION_PRECEDENCE = (
    "global_admission_rule_id_exact_type_validation", "known_rule_validation",
    "registration_adapter_ready_validation", "batch_context_validation",
    "evaluation_context_mapping_validation",
    "allowed_topology_restoration_dispositions_required_key_validation",
    "download_result_context_validation", "stage_authorization_context_validation",
    "candidate_record_mapping_validation", "topology_restoration_disposition_required_key_lookup",
    "candidate_key_absent_classification", "formal_evaluate_admit_008_exactly_once",
    "standalone_source_exact_type_validation", "standalone_exact10_invariant_validation",
    "independent_expected_exact10_oracle_derivation", "source_oracle_complete_exact10_equality",
    "unified_exact13_result_construction",
)
OUTPUTS = (
    "covapie_admit_008_unified_adapter_contract.csv",
    "covapie_admit_008_candidate_projection_and_context_routing_matrix.csv",
    "covapie_admit_008_unified_result_projection_truth_matrix.csv",
    "covapie_admit_008_unified_adapter_safety_audit.csv",
    "covapie_admit_008_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_008_unified_adapter_contract_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    OUTPUTS[0]: "29d4ceacd263cf4b1bb0a4320a8eda03a8742e9bb344b512f8412baed7967e8a",
    OUTPUTS[1]: "7c8060203e71b83f7398d79977dfa69057089231fec034afba95fcf37d99fef2",
    OUTPUTS[2]: "59fa45d08d8950387ebd752d0f867312a47a67326c9b23bed886500307a36e4c",
    OUTPUTS[3]: "46e0cefc9e28d2072de2565270abf65fbeaaf41709212a73f2e88f7e5f052b13",
    OUTPUTS[4]: "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
    OUTPUTS[5]: "d7423c337512dff3f66a68209301c91dd3fee2bdd2a3a5b669185854c622d922",
}
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py", "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json", "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_issue_inventory.csv", "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0"),
    (FORMAL_SOURCE, "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_manifest.json", "ae5fc1c5aa28618765ed07fe5aae67c02d31e7650fb5921dae954c0a3cfefd7e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_contract.csv", "62fdcf8c18f5baf3b08cd29515804abba7543d5da21056d2d93a392d5c188ac9"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_truth_matrix.csv", "a78510cf512782f9bd586e040d26a7fb459ba8b0e1eec310195b417cd0b9c636"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_issue_readiness_inventory.csv", "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate.py", "d4b2480e5d1cff17377fa0856eeac007629c4db1e5cdb413e4ea83771d08461d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json", "4da97951abe63d46ded0ad5ffc6048e1a1c40eb2fdedd3553de094ac1ad0c85b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_enum_registry.csv", "38e41ef09b62848e55e6d43fa2ee65ecc3b24378fd8ac9ca72fd2e313261556a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv", "d15cc2f468b158bdd0871386af041231f563af34ff394c2d25e8b5797fa3599b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv", "f449e7441045f52a2222f70f2b7378446424ea46610859641ae2baf5e4565be4"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate.py", "5c3171fb19efdafecad5258ce4d6c0185b731ab93dece947232d80ef089b4a88"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_adapter_contract_manifest.json", "9cb470520b666624ecbde992354c05587dd38c3006f1f21db4a2dfe3733a4eb4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv", "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv", "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05"),
)
CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = ("matrix_order", "matrix_group", "case_id", "condition", "expected_behavior", "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count", "candidate_access_status", "case_passed")
TRUTH_COLUMNS = ("case_id", "case_group", "behavior", "expected_dispatch_code", "expected_reason", "source_exact10_json", "oracle_exact10_json", "unified_exact13_json", "formal_call_count", "oracle_call_count", "case_passed")
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = ("issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count")


class _StringSubclass(str):
    pass


def _expected_readiness() -> dict[str, bool]:
    true = (
        "admit_008_standalone_evaluator_available", "admit_008_unified_adapter_contract_frozen",
        "admit_008_context_routing_contract_frozen", "admit_008_candidate_projection_contract_frozen",
        "admit_008_key_absent_contract_frozen", "admit_008_none_empty_forwarding_contract_frozen",
        "admit_008_source_result_validation_contract_frozen", "admit_008_source_oracle_equivalence_contract_frozen",
        "admit_008_unified_result_projection_contract_frozen", "admit_008_blocked_passthrough_contract_frozen",
        "admit_008_context_invalid_partial_canonical_projection_frozen",
        "admit_008_provider_mapping_boundary_preserved",
        "ready_for_unified_dispatch_runtime_with_admit_001_to_008_implementation",
        "feature_semantics_audit_required_before_training",
    )
    false = (
        "admit_008_unified_adapter_implemented", "admit_008_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_008_implemented", "exact7_runtime_modified",
        "real_provider_topology_disposition_mapping_validated", "real_provider_value_count_nonzero",
        "admit_009_standalone_evaluator_implemented", "admit_009_to_015_registered_in_engine",
        "all_15_rules_covered", "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
        "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen", "real_candidate_evaluation",
        "exact11_real_rows_evaluated", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    )
    return {**{key: True for key in true}, **{key: False for key in false}}


def _source(outcome: str, reason: str, canonical: str) -> dict[str, Any]:
    validated = [] if canonical == "" else [[CANDIDATE_FIELDS[0], canonical]]
    return dict(zip(SOURCE_FIELDS, (
        RULE_ID, outcome, outcome == "passed", outcome != "passed", reason, canonical,
        validated, list(CANDIDATE_FIELDS), list(CONTEXT_ITEMS), False,
    ), strict=True))


def _exact13(outcome: str, reason: str, validated: Sequence[Sequence[str]]) -> dict[str, Any]:
    pairs = [list(pair) for pair in validated]
    return dict(zip(RESULT_FIELDS, (
        SCHEMA, RULE_ID, RULE_NAME, outcome, outcome == "passed", outcome != "passed", reason,
        pairs, pairs, list(CANDIDATE_FIELDS), list(CONTEXT_ITEMS), False, ADAPTER_ID,
    ), strict=True))


def _classify(scalar: object, context: object) -> dict[str, Any]:
    canonical = ""
    if type(scalar) is not str:
        reason = SCALAR_REASONS[0]
    elif scalar == "":
        reason = SCALAR_REASONS[1]
    elif not scalar.isascii():
        reason = SCALAR_REASONS[2]
    elif re.fullmatch(r"[a-z][a-z0-9_]{0,63}", scalar, re.ASCII) is None:
        reason = SCALAR_REASONS[3]
    elif scalar not in ENUM_MEMBERS:
        reason = SCALAR_REASONS[4]
    else:
        canonical, reason = scalar, ""
    if reason:
        return _source("invalid", reason, "")
    if type(context) is not tuple:
        return _source("invalid", CONTEXT_VALUE_REASONS[0], canonical)
    if any(type(member) is not str for member in context) or context != ALLOWED:
        return _source("invalid", CONTEXT_VALUE_REASONS[1], canonical)
    if canonical in BLOCKED_REASONS:
        return _source("blocked", BLOCKED_REASONS[canonical], canonical)
    return _source("passed", "", canonical)


def _decode(kind: str, display: str) -> object:
    if kind == "str":
        return json.loads(display)
    if kind in ("NoneType", "none"):
        return None
    if kind == "int":
        return int(display.removeprefix("int:"))
    if kind == "bool":
        return display == "bool:True"
    if kind == "_StringSubclass":
        return _StringSubclass(json.loads(display.removeprefix("str_subclass:")))
    if kind == "list":
        return json.loads(display.removeprefix("list:"))
    if kind == "dict":
        return json.loads(display.removeprefix("dict:"))
    if kind == "set":
        return set(json.loads(display.removeprefix("set:")))
    if kind == "frozenset":
        return frozenset(json.loads(display.removeprefix("frozenset:")))
    members = json.loads(display.removeprefix("tuple:"))
    if kind == "str_subclass_member":
        members[0] = _StringSubclass(members[0])
    return tuple(members)


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _dispatch(reason: str) -> str:
    return _json(dict(zip(ERROR_FIELDS, ("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", RULE_ID, True, True, True, reason), strict=True)))


def _expected_contract_rows() -> list[dict[str, str]]:
    values = (
        ("identity", "admission_rule_id", RULE_ID), ("identity", "admission_rule_name", RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID), ("identity", "formal_evaluator", FORMAL_EVALUATOR),
        ("identity", "formal_evaluator_source", FORMAL_SOURCE), ("identity", "independent_oracle", ORACLE_ID),
        ("runtime_reuse", "public_api", "evaluate_admission_rule_current_exact7_identity"),
        ("runtime_reuse", "result_type", "UnifiedAdmissionRuleEvaluation_current_exact7_identity"),
        ("runtime_reuse", "dispatch_error_type", "UnifiedAdmissionDispatchError_current_exact7_identity"),
        ("runtime_reuse", "schema_version", SCHEMA), ("runtime_reuse", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("runtime_reuse", "exact6_dispatch_fields", "|".join(ERROR_FIELDS)),
        ("runtime_reuse", "known_rule_vocabulary", "|".join(KNOWN_RULE_IDS)),
        ("registration", "future_exact8_order", "|".join(FUTURE_ORDER)),
        ("registration", "current_exact7_order", "|".join(CURRENT_ORDER)),
        ("registration", "admit001_to_007_handler_identity", "unchanged"),
        ("precedence", "complete_execution_precedence", "|".join(EXECUTION_PRECEDENCE)),
        ("routing", "context_order", "batch_context|evaluation_context|evaluation_required_key|download_result_context|stage_authorization_context"),
        ("routing", "batch_context", "exact_none"),
        ("routing", "evaluation_context", "mapping_subclass_accepted_required_key_extra_keys_ignored"),
        ("routing", "routed_context_value", "single_getitem_original_identity_no_prevalidation_copy_mutation_or_normalization"),
        ("routing", "download_result_context", "exact_none"), ("routing", "stage_authorization_context", "exact_none"),
        ("routing", "early_failure", "candidate_not_accessed"),
        ("candidate", "candidate_record", "mapping_subclass_accepted_extra_fields_ignored_no_copy_mutation_or_unrelated_iteration"),
        ("candidate", "required_field", "topology_restoration_disposition_single_getitem_original_identity"),
        ("candidate", "non_mapping", CANDIDATE_REASON), ("missing", "only_category", "required_key_absent"),
        ("missing", "reason", MISSING_REASON), ("forwarding", "exact_none", SCALAR_REASONS[0]),
        ("forwarding", "exact_builtin_empty_str", SCALAR_REASONS[1]),
        ("forwarding", "empty_str_subclass", SCALAR_REASONS[0]),
        ("forwarding", "whitespace_and_malformed", "standalone_exact_reason"),
        ("call", "formal_call", "exactly_one_positional_call_original_scalar_and_context_identity"),
        ("call", "normalization", "none_no_trim_casefold_alias_conversion_copy_repair_mutation_or_io"),
        ("source", "exact_type", "type(source)_is_Admit008EvaluationResult_subclass_rejected"),
        ("source", "exact10_fields", "|".join(SOURCE_FIELDS)),
        ("source", "invariants", "vars_order|dataclass_field_order|ordered_reads|reconstruction|equality|complete_cross_field_validation"),
        ("source", "failure", "oracle_not_called_no_partial_exact13_adapter_ready_false"),
        ("oracle", "call", "same_original_objects_exactly_once_after_source_validation"),
        ("oracle", "equivalence", "complete_ordered_exact10_equality"),
        ("projection", "mapping", "source_exact10_to_existing_unified_exact13"),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "passed", "two_exact4_allowed_members_passthrough"),
        ("projection", "blocked", "two_distinct_blocked_reasons_passthrough"),
        ("projection", "scalar_invalid", "empty_normalized_and_validated_exact_reason_retained"),
        ("projection", "context_invalid", "canonical_and_validated_pair_retained"),
        ("provider", "fields", "restoration_rule_and_provenance_not_consumed"),
        ("issues", "exact11", "byte_identical_no_transition_coverage_still_admit008_to_015"),
        ("readiness", "next_step", NEXT_STEP), ("stop", "adapter_handler", "not_implemented"),
        ("stop", "runtime_registry", "current_exact7_unmodified_admit008_not_registered"),
        ("stop", "provider_mapping", "not_validated_real_provider_value_count_zero"),
        ("stop", "training", "feature_semantics_audit_required_step12d_not_final_contract"),
    )
    return [{"contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
             "contract_group": group, "contract_subject": subject, "contract_value": value,
             "contract_status": "frozen"} for index, (group, subject, value) in enumerate(values, 1)]


def _expected_routing_rows() -> list[dict[str, str]]:
    def result(scalar: object, context: object = ALLOWED) -> str:
        source = _classify(scalar, context)
        return _json(_exact13(source["outcome"], source["reason"], source["validated_candidate_fields"]))
    candidate = _json(_exact13("invalid", CANDIDATE_REASON, ()))
    missing = _json(_exact13("invalid", MISSING_REASON, ()))
    cases = (
        ("context", "batch_non_none", "batch_context non-None", "dispatch_error", CONTEXT_REASONS["batch_context"], _dispatch(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_non_mapping", "evaluation_context non-Mapping", "dispatch_error", CONTEXT_REASONS["evaluation_context"], _dispatch(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_key_missing", "evaluation required key missing", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], _dispatch(CONTEXT_REASONS["evaluation_context_key"]), 0, 0, "not_accessed"),
        ("context", "download_non_none", "download_result_context non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], _dispatch(CONTEXT_REASONS["download_result_context"]), 0, 0, "not_accessed"),
        ("context", "stage_non_none", "stage_authorization_context non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], _dispatch(CONTEXT_REASONS["stage_authorization_context"]), 0, 0, "not_accessed"),
        ("context", "multiple_failure_precedence", "batch and later contexts invalid", "first_dispatch_error_only", CONTEXT_REASONS["batch_context"], _dispatch(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_mapping_subclass", "evaluation Mapping subclass", "accepted_without_copy", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_extra_keys", "evaluation extra keys", "ignored", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_not_mutated", "mutable evaluation Mapping", "not_mutated", "", "", 1, 1, "accessed_after_context"),
        ("context", "context_identity_single_lookup", "required context identity sentinel", "same_object_single_lookup", "", "", 1, 1, "accessed_after_context"),
        ("context", "invalid_context_reaches_standalone", "invalid context value", "exact13_invalid_canonical_retained", CONTEXT_VALUE_REASONS[0], result(ENUM_MEMBERS[0], list(ALLOWED)), 1, 1, "accessed_after_context"),
        ("candidate", "candidate_non_mapping", "candidate non-Mapping", "exact13_invalid", CANDIDATE_REASON, candidate, 0, 0, "envelope_checked"),
        ("candidate", "candidate_key_absent", "candidate key absent", "exact13_invalid", MISSING_REASON, missing, 0, 0, "single_lookup"),
        ("candidate", "candidate_exact_none", "candidate exact None", "standalone_type_invalid", SCALAR_REASONS[0], result(None), 1, 1, "value_read_once"),
        ("candidate", "candidate_exact_empty", "candidate exact built-in empty str", "standalone_empty_invalid", SCALAR_REASONS[1], result(""), 1, 1, "value_read_once"),
        ("candidate", "candidate_empty_subclass", "candidate empty str subclass", "standalone_type_invalid", SCALAR_REASONS[0], result(_StringSubclass("")), 1, 1, "value_read_once"),
        ("candidate", "candidate_whitespace", "candidate whitespace", "standalone_syntax_invalid", SCALAR_REASONS[3], result(" "), 1, 1, "value_read_once"),
        ("candidate", "candidate_integer", "candidate malformed integer", "standalone_type_invalid", SCALAR_REASONS[0], result(7), 1, 1, "value_read_once"),
        ("candidate", "approved_template", "approved_restoration_template", "passed", "", result(ENUM_MEMBERS[0]), 1, 1, "value_read_once"),
        ("candidate", "manual_approved", "explicit_manual_review_approved", "passed", "", result(ENUM_MEMBERS[1]), 1, 1, "value_read_once"),
        ("candidate", "manual_review_required", "manual_review_required", "blocked", BLOCKED_REASONS[ENUM_MEMBERS[2]], result(ENUM_MEMBERS[2]), 1, 1, "value_read_once"),
        ("candidate", "quarantine_required", "quarantine_required", "blocked", BLOCKED_REASONS[ENUM_MEMBERS[3]], result(ENUM_MEMBERS[3]), 1, 1, "value_read_once"),
        ("candidate", "candidate_mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_extra_fields", "candidate extra fields", "ignored_without_iteration", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_not_mutated", "mutable candidate Mapping", "not_mutated", "", "", 1, 1, "value_read_once"),
        ("candidate", "scalar_identity_single_lookup", "scalar identity sentinel", "same_object_single_lookup", "", "", 1, 1, "value_read_once"),
    )
    return [{"matrix_order": str(index), "matrix_group": group, "case_id": case_id,
             "condition": condition, "expected_behavior": behavior, "expected_reason": reason,
             "expected_result_json": expected, "formal_call_count": str(formal),
             "oracle_call_count": str(oracle), "candidate_access_status": access, "case_passed": "true"}
            for index, (group, case_id, condition, behavior, reason, expected, formal, oracle, access) in enumerate(cases, 1)]


def _expected_truth_rows(corpus: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    def row(case_id: str, group: str, behavior: str, reason: str = "", *, source: Mapping[str, Any] | None = None,
            oracle: Mapping[str, Any] | None = None, unified: Mapping[str, Any] | None = None,
            code: str = "", formal: int = 0, oracle_calls: int = 0) -> dict[str, str]:
        return {"case_id": case_id, "case_group": group, "behavior": behavior,
                "expected_dispatch_code": code, "expected_reason": reason,
                "source_exact10_json": _json(source) if source is not None else "",
                "oracle_exact10_json": _json(oracle) if oracle is not None else "",
                "unified_exact13_json": _json(unified) if unified is not None else "",
                "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls), "case_passed": "true"}
    rows = []
    for prior in corpus:
        scalar = _decode(prior["scalar_input_kind"], prior["scalar_input_display"])
        context = _decode(prior["context_input_kind"], prior["context_input_display"])
        source = _classify(scalar, context)
        if json.loads(prior["observed_full_result"]) != source:
            raise AssertionError("standalone corpus differs from independent classifier")
        unified = _exact13(source["outcome"], source["reason"], source["validated_candidate_fields"])
        rows.append(row(f"STANDALONE_{prior['case_id']}", "standalone_exact38", "exact10_to_exact13",
                        source["reason"], source=source, oracle=source, unified=unified, formal=1, oracle_calls=1))
    for key in ("batch_context", "evaluation_context", "evaluation_context_key", "download_result_context", "stage_authorization_context"):
        rows.append(row(f"ROUTING_{key}", "routing_dispatch", "exact6_no_partial_result", CONTEXT_REASONS[key], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"))
    rows.append(row("ROUTING_multiple_precedence", "routing_dispatch", "first_exact6_no_candidate_access", CONTEXT_REASONS["batch_context"], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"))
    rows.append(row("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13", CANDIDATE_REASON, unified=_exact13("invalid", CANDIDATE_REASON, ())))
    rows.append(row("CANDIDATE_key_absent", "adapter_candidate_invalid", "adapter_generated_exact13", MISSING_REASON, unified=_exact13("invalid", MISSING_REASON, ())))
    valid = _classify(ENUM_MEMBERS[0], ALLOWED)
    rows.extend((
        row("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        row("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        row("SOURCE_invariant", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        row("SOURCE_oracle_mismatch", "source_validation_failure", "no_projection", SOURCE_INVARIANT_REASON, source=valid, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1, oracle_calls=1),
        row("BOUNDARY_issue_bytes", "issue_coverage_boundary", "exact11_byte_identical_no_transition"),
        row("BOUNDARY_coverage", "issue_coverage_boundary", "admit008_to_015_remain_open"),
    ))
    return rows


def _expected_safety_rows() -> list[dict[str, str]]:
    positive = ("adapter_contract_design", "context_routing_design", "candidate_projection_design", "key_absent_policy_design", "none_empty_forwarding_design", "standalone_exact10_validation_design", "independent_oracle_equivalence_design", "exact13_projection_design", "synthetic_exact26_routing", "synthetic_projection_truth", "fixed_exact17_source_verification", "exact11_issue_byte_preservation", "deterministic_materialization")
    negative = ("adapter_handler_implementation", "runtime_source_modification", "registry_mutation", "admit_008_registration", "provider_mapping", "provider_value_materialization", "restoration_rule_provenance_consumption", "admit_009", "evaluate_all_rules", "combined_candidate_verdict", "real_candidate_evaluation", "raw_read", "network", "download", "checkpoint", "torch", "numpy", "rdkit", "model_forward", "loss", "training", "fine_tune", "parameter_update", "stage", "commit", "push", "gh")
    return [{"safety_item": item, "expected_executed": value, "observed_executed": value, "safety_passed": "true"}
            for item, value in ((*((item, "true") for item in positive), *((item, "false") for item in negative)))]


PROTECTED_BUILDERS = {"_expected_readiness", "_source", "_exact13", "_classify", "_expected_contract_rows", "_expected_routing_rows", "_expected_truth_rows", "_expected_safety_rows"}


def _assert_ast_independence(source_text: str | None = None) -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8") if source_text is None else source_text)
    forbidden = {"_contract_rows", "_routing_rows", "_truth_rows", "_safety_rows", "_payloads", "build_design_state", "SOURCE_PATHS", "SOURCE_SHA256", "READINESS"}
    seen = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in PROTECTED_BUILDERS:
            seen.add(node.name)
            names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
            attrs = {child.attr for child in ast.walk(node) if isinstance(child, ast.Attribute)}
            if names & {"production", "gate"} or attrs & forbidden:
                raise AssertionError(f"checker builder depends on production: {node.name}")
    if source_text is None and seen != PROTECTED_BUILDERS:
        raise AssertionError("protected checker builder inventory changed")


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AssertionError("CSV header missing")
        return tuple(reader.fieldnames), list(reader)


def _validate_source_boundary(production: Any | None = None) -> None:
    for relative, _ in SOURCE_BOUNDARY:
        path = ROOT / relative
        mode = path.lstat().st_mode
        tree = subprocess.run(["git", "ls-tree", EXPECTED_BASE, "--", relative], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode) or not tree.startswith("100644 blob "):
            raise AssertionError(f"unsafe source: {relative}")
        try:
            path.resolve().relative_to(ROOT)
        except ValueError as error:
            raise AssertionError(f"source escapes root: {relative}") from error
    for relative, digest in SOURCE_BOUNDARY:
        base = subprocess.run(["git", "show", f"{EXPECTED_BASE}:{relative}"], cwd=ROOT, capture_output=True, check=True).stdout
        if hashlib.sha256(base).hexdigest() != digest or hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise AssertionError(f"source SHA mismatch: {relative}")
    if production is not None:
        if tuple(path.as_posix() for path in production.SOURCE_PATHS) != tuple(path for path, _ in SOURCE_BOUNDARY):
            raise AssertionError("production source path order mismatch")
        if tuple(production.SOURCE_SHA256[path] for path in production.SOURCE_PATHS) != tuple(digest for _, digest in SOURCE_BOUNDARY):
            raise AssertionError("production source SHA map mismatch")


def _validate_manifest(manifest: Mapping[str, Any], rows: Mapping[str, Sequence[Mapping[str, str]]]) -> None:
    readiness = _expected_readiness()
    required = {
        "project": "CovaPIE", "step": "ADMIT_008 unified adapter contract design gate v1",
        "stage": "covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1",
        "manifest_schema_version": "covapie_admit_008_unified_adapter_contract_manifest_v1",
        "expected_base_commit": EXPECTED_BASE, "expected_base_subject": EXPECTED_SUBJECT,
        "admission_rule_id": RULE_ID, "admission_rule_name": RULE_NAME, "adapter_id": ADAPTER_ID,
        "formal_evaluator": FORMAL_EVALUATOR, "formal_result_type": "Admit008EvaluationResult",
        "future_adapter_handler": "_evaluate_registered_admit_008", "formal_evaluator_source": FORMAL_SOURCE,
        "independent_oracle": ORACLE_ID, "independent_oracle_outcome_view": "classification.admit_008",
        "candidate_field": CANDIDATE_FIELDS[0], "evaluation_context_item": CONTEXT_ITEMS[0],
        "runtime_public_api_reused_by_identity": "evaluate_admission_rule",
        "runtime_result_type_reused_by_identity": "UnifiedAdmissionRuleEvaluation",
        "runtime_dispatch_error_type_reused_by_identity": "UnifiedAdmissionDispatchError",
        "future_registered_rule_order": list(FUTURE_ORDER), "future_callable_discovered_rule_ids": list(FUTURE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_ORDER), "current_registered_rule_order": list(CURRENT_ORDER),
        "admit_001_to_007_handler_identity_unchanged": True, "known_rule_ids": list(KNOWN_RULE_IDS),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[8:]), "known_not_registered_behavior": "known_not_registered_fail_closed",
        "execution_precedence": list(EXECUTION_PRECEDENCE), "result_schema_version": SCHEMA,
        "result_fields": list(RESULT_FIELDS), "standalone_result_fields": list(SOURCE_FIELDS),
        "dispatch_error_fields": list(ERROR_FIELDS), "dispatch_error_codes": list(ERROR_CODES),
        "outcome_vocabulary": ["passed", "blocked", "invalid", "rejected"],
        "context_routing_order": ["batch_context", "evaluation_context", "evaluation_required_key", "download_result_context", "stage_authorization_context"],
        "context_routing_reasons": dict(CONTEXT_REASONS), "candidate_mapping_invalid_reason": CANDIDATE_REASON,
        "adapter_missing_categories": ["required_key_absent"], "adapter_missing_reason": MISSING_REASON,
        "none_empty_forwarding_policy": {"exact_none": SCALAR_REASONS[0], "exact_builtin_empty_str": SCALAR_REASONS[1], "empty_str_subclass": SCALAR_REASONS[0], "historical_lowercase_used": False},
        "canonical_enum_members": list(ENUM_MEMBERS), "allowed_topology_restoration_dispositions": list(ALLOWED),
        "blocked_reason_mapping": dict(BLOCKED_REASONS), "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON, "formal_call_count_after_candidate_gate": 1,
        "oracle_call_count_after_source_validation": 1, "source_prevalidated_before_oracle": True,
        "oracle_complete_exact10_equality_required": True, "no_partial_exact13_on_failure": True,
        "blocked_passthrough": True, "context_invalid_partial_canonical_projection": True,
        "normalized_values_projection": "source.validated_candidate_fields", "provider_fields_consumed": [],
        "real_provider_mapping_executed": False, "real_provider_value_count": 0,
        "contract_row_count": 54, "contract_pass_count": 54, "routing_matrix_row_count": 26,
        "routing_matrix_pass_count": 26, "routing_matrix_group_counts": {"candidate": 15, "context": 11},
        "projection_truth_matrix_row_count": 52, "projection_truth_matrix_pass_count": 52,
        "projection_truth_matrix_group_counts": {"adapter_candidate_invalid": 2, "issue_coverage_boundary": 2, "routing_dispatch": 6, "source_validation_failure": 4, "standalone_exact38": 38},
        "safety_row_count": 40, "safety_pass_count": 40, "issue_inventory_row_count": 11,
        "issue_inventory_preserved_byte_identical": True, "issue_inventory_sha256": FROZEN_OUTPUT_SHA256[OUTPUTS[4]],
        "coverage_issue_still_includes_admit_008_to_015": True, "source_input_count": 17,
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": {path: digest for path, digest in SOURCE_BOUNDARY},
        "source_input_verification": "expected_sha256_equals_base_tree_sha256_equals_filesystem_sha256",
        "source_boundary_name": "fixed_exact17_committed_source_boundary",
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True, "output_file_count": 6,
        "output_files": list(OUTPUTS), "output_sha256": {name: FROZEN_OUTPUT_SHA256[name] for name in OUTPUTS[:-1]},
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": ["adapter_handler_not_implemented", "exact7_runtime_unchanged", "admit_008_unregistered", "exact8_runtime_not_implemented", "provider_mapping_not_validated", "admit_009_not_started", "evaluate_all_rules_not_implemented", "combined_candidate_verdict_not_implemented", "real_candidate_evaluation_not_executed", "raw_network_download_forbidden", "training_forbidden"],
        "recommended_next_step": NEXT_STEP, "validation_failures": [], "readiness": readiness,
        **readiness, "all_checks_passed": True,
    }
    if type(manifest) is not dict or dict(manifest) != required:
        raise AssertionError("manifest complete dictionary mismatch")
    if any(len(rows[key]) != count for key, count in (("contract", 54), ("routing", 26), ("truth", 52), ("safety", 40), ("issue", 11))):
        raise AssertionError("manifest row count evidence mismatch")


def _assert_production_ast() -> None:
    path = ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "_evaluate_registered_admit_008" in functions or "evaluate_admission_rule" in functions:
        raise AssertionError("runtime handler present")
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in targets):
            raise AssertionError("registry present")


def _validate_output_tree(root: Path, *, enforce_frozen_hashes: bool = True,
                          expected_materialized: Path | None = None,
                          production: Any | None = None) -> dict[str, int]:
    if tuple(sorted(path.name for path in root.iterdir())) != tuple(sorted(OUTPUTS)):
        raise AssertionError("output set is not Exact6")
    for name in OUTPUTS:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise AssertionError(f"unsafe output: {name}")
        if enforce_frozen_hashes and hashlib.sha256(path.read_bytes()).hexdigest() != FROZEN_OUTPUT_SHA256[name]:
            raise AssertionError(f"frozen output SHA mismatch: {name}")
    contract_header, contract_rows = _read_csv(root / OUTPUTS[0])
    routing_header, routing_rows = _read_csv(root / OUTPUTS[1])
    truth_header, truth_rows = _read_csv(root / OUTPUTS[2])
    safety_header, safety_rows = _read_csv(root / OUTPUTS[3])
    issue_header, issue_rows = _read_csv(root / OUTPUTS[4])
    _, corpus = _read_csv(ROOT / SOURCE_BOUNDARY[6][0])
    expected = (_expected_contract_rows(), _expected_routing_rows(), _expected_truth_rows(corpus), _expected_safety_rows())
    observed = (contract_rows, routing_rows, truth_rows, safety_rows)
    if (contract_header, routing_header, truth_header, safety_header, issue_header) != (CONTRACT_COLUMNS, ROUTING_COLUMNS, TRUTH_COLUMNS, SAFETY_COLUMNS, ISSUE_COLUMNS):
        raise AssertionError("output header mismatch")
    if observed != expected:
        raise AssertionError("checker-owned semantic rows mismatch")
    issue_bytes = (root / OUTPUTS[4]).read_bytes()
    if issue_bytes != (ROOT / SOURCE_BOUNDARY[7][0]).read_bytes() or hashlib.sha256(issue_bytes).hexdigest() != FROZEN_OUTPUT_SHA256[OUTPUTS[4]]:
        raise AssertionError("Exact11 issue bytes changed")
    issue_map = {row["issue_id"]: row for row in issue_rows}
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] != "resolved" or coverage["status"] != "open" or coverage["affected_rules"].split("|")[:8] != [f"ADMIT_{index:03d}" for index in range(8, 16)]:
        raise AssertionError("Exact11 issue semantics changed")
    row_map = {"contract": contract_rows, "routing": routing_rows, "truth": truth_rows, "safety": safety_rows, "issue": issue_rows}
    _validate_manifest(json.loads((root / OUTPUTS[5]).read_text(encoding="utf-8")), row_map)
    if expected_materialized is not None:
        for name in OUTPUTS:
            if (root / name).read_bytes() != (expected_materialized / name).read_bytes():
                raise AssertionError(f"deterministic rematerialization mismatch: {name}")
    if production is not None:
        _validate_source_boundary(production)
        if (production._contract_rows(), production._routing_rows(), production._truth_rows(corpus), production._safety_rows(), production.READINESS) != (*expected, _expected_readiness()):
            raise AssertionError("production design builders differ from checker-owned semantics")
    return {"contract_rows": 54, "routing_rows": 26, "truth_rows": 52, "safety_rows": 40, "issue_rows": 11, "source_count": 17}


def main() -> int:
    _assert_ast_independence()
    _assert_production_ast()
    if subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_BASE, "HEAD"], cwd=ROOT).returncode:
        raise AssertionError("non-descendant base")
    subject = subprocess.run(["git", "show", "-s", "--format=%s", EXPECTED_BASE], cwd=ROOT, capture_output=True, text=True, check=True).stdout.rstrip("\n")
    if subject != EXPECTED_SUBJECT:
        raise AssertionError("base subject mismatch")
    _validate_source_boundary()
    _, corpus = _read_csv(ROOT / SOURCE_BOUNDARY[6][0])
    _expected_readiness(); _expected_contract_rows(); _expected_routing_rows(); _expected_truth_rows(corpus); _expected_safety_rows()
    sys.path.insert(0, str(ROOT / "src"))
    production = importlib.import_module(MODULE_NAME)
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root, second_root = Path(first), Path(second)
        production.run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(first_root)
        production.run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(second_root)
        for name in OUTPUTS:
            if (first_root / name).read_bytes() != (second_root / name).read_bytes():
                raise AssertionError(f"double materialization differs: {name}")
        summary = _validate_output_tree(OUTPUT_ROOT, expected_materialized=first_root, production=production)
    summary.update({"all_checks_passed": True, "output_file_count": 6,
                    "readiness": "ready_for_unified_dispatch_runtime_with_admit_001_to_008_implementation"})
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
