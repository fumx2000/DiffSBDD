#!/usr/bin/env python3
"""Checker-owned semantic verification for the ADMIT_007 adapter design gate."""

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
MODULE_NAME = "covalent_ext.covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE = "0c7081a281fe3b4dac774bc6772a10ea599b8a76"
EXPECTED_SUBJECT = "add CovaPIE standalone ADMIT_007 rule logic interface v1"
RULE_ID = "ADMIT_007"
RULE_NAME = "distance_only_inference_forbidden"
ADAPTER_ID = "covapie_admit_007_unified_adapter_v1"
FORMAL_EVALUATOR = "evaluate_admit_007"
FORMAL_SOURCE = "src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py"
ORACLE_ID = "classify_admit_006_admit_007_evidence_design"
SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_007_v1"
FUTURE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 8))
CURRENT_ORDER = FUTURE_ORDER[:6]
CANDIDATE_FIELDS = ("covalent_event_evidence_source",)
CONTEXT_ITEMS = ("allowed_covalent_evidence_classes",)
ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
ALLOWED_CLASSES = ENUM_MEMBERS[:2]
SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
CONTEXT_VALUE_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
BLOCKED_REASON = "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
MISSING_REASON = "covalent_event_evidence_missing"
CANDIDATE_REASON = "ADMIT_007_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_007_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_REASONS = {
    "batch_context": "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_007_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_007_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED",
    "download_result_context": "ADMIT_007_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_007_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome", "passed",
    "blocks_candidate", "reason", "normalized_values", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_covalent_event_evidence_source", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered", "adapter_ready", "reason",
)
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
EXECUTION_PRECEDENCE = (
    "global_admission_rule_id_exact_type_validation",
    "known_rule_validation",
    "registration_adapter_ready_validation",
    "batch_context_validation",
    "evaluation_context_mapping_validation",
    "allowed_covalent_evidence_classes_key_validation",
    "download_result_context_validation",
    "stage_authorization_context_validation",
    "candidate_record_mapping_validation",
    "required_candidate_field_presence",
    "adapter_missing_value_classification",
    "formal_evaluate_admit_007_exactly_once",
    "standalone_source_exact_type_and_exact10_invariant_validation",
    "independent_expected_exact10_oracle_derivation",
    "source_oracle_complete_exact10_equality",
    "exact13_unified_result_construction",
)
OUTPUTS = (
    "covapie_admit_007_unified_adapter_contract.csv",
    "covapie_admit_007_candidate_projection_and_context_routing_matrix.csv",
    "covapie_admit_007_unified_result_projection_truth_matrix.csv",
    "covapie_admit_007_unified_adapter_safety_audit.csv",
    "covapie_admit_007_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_007_unified_adapter_contract_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    OUTPUTS[0]: "9c155462b7ffe83a172eb16dccde0da0c8c6be03fff93aa1a405aa9ca7b14537",
    OUTPUTS[1]: "5cca82bac1f9e971b238735a9c8aad3c06f5876e32dad535f639645453720c59",
    OUTPUTS[2]: "0423420e0442f9d6ea7cf8b1befe319f0b6bc6527d1038a0a4f95883d982cddd",
    OUTPUTS[3]: "4641829cb8912cfbd9a84689feed03b2780baee199d13070cd0b97c8e90c9992",
    OUTPUTS[4]: "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    OUTPUTS[5]: "9cb470520b666624ecbde992354c05587dd38c3006f1f21db4a2dfe3733a4eb4",
}
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py", "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_manifest.json", "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_issue_inventory.csv", "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196"),
    (FORMAL_SOURCE, "ce5cbf09765e8b12db162458ca9518d71d431b175f3225e5558a8b57fdd133f6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_manifest.json", "f5212100bf458372dd908a234557ee34858cf24cf2360e39b1e61cba8a562958"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_contract.csv", "d6183b2f6dba1c50f6131e28d14519c29d6645b879f954fed7668e776bb0f425"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_truth_matrix.csv", "e0ac129e65333e7d1808b8d165391e9188a22c61e8f96ce5e0def8895a34b30c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_formal_evaluator_preconditions_manifest.json", "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a"),
    ("src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py", "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_admit_006_admit_007_evidence_responsibility_matrix.csv", "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv", "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv", "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate.py", "7645a99f107bd784d1868dbab7136803804645874b33a210273944b00447ac89"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1/covapie_admit_006_unified_adapter_contract_manifest.json", "449f3f2f5bcf7b7e6a2d60504238da91f41f67822a9747e32fd6eb60b88468b2"),
)
READINESS_TRUE = (
    "admit_007_standalone_evaluator_available",
    "admit_007_unified_adapter_contract_frozen",
    "admit_007_candidate_projection_contract_frozen",
    "admit_007_context_routing_contract_frozen",
    "admit_007_missing_field_value_contract_frozen",
    "admit_007_source_result_validation_contract_frozen",
    "admit_007_source_oracle_equivalence_contract_frozen",
    "admit_007_unified_result_projection_contract_frozen",
    "admit_007_blocked_passthrough_contract_frozen",
    "admit_007_context_invalid_partial_canonical_projection_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_007_implementation",
    "feature_semantics_audit_required_before_training",
)
READINESS_FALSE = (
    "admit_007_unified_adapter_implemented", "admit_007_registered_in_engine",
    "current_exact6_runtime_modified", "admit_008_standalone_evaluator_implemented",
    "admit_008_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_provider_enum_mapping_validated",
    "real_candidate_evaluation", "exact11_real_rows_evaluated", "ready_for_bulk_download_now",
    "ready_for_training", "ready_to_train_now",
)

CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = ("matrix_order", "matrix_group", "case_id", "condition", "expected_behavior", "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count", "candidate_access_status", "case_passed")
TRUTH_COLUMNS = ("case_id", "case_group", "behavior", "expected_dispatch_code", "expected_reason", "source_exact10_json", "oracle_exact10_json", "unified_exact13_json", "formal_call_count", "oracle_call_count", "case_passed")
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = ("issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count")
STANDALONE_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "context_input_display", "expected_outcome", "expected_reason",
    "observed_outcome", "observed_reason", "expected_canonical_evidence_source",
    "observed_canonical_evidence_source", "expected_validated_candidate_fields",
    "observed_validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "expected_full_result",
    "observed_full_result", "independent_oracle_full_result", "case_passed",
)


class _StringSubclass(str):
    pass


def _expected_readiness() -> dict[str, bool]:
    return {**{key: True for key in READINESS_TRUE}, **{key: False for key in READINESS_FALSE}}


def _expected_source_boundary() -> tuple[tuple[str, str], ...]:
    return SOURCE_BOUNDARY


def _expected_exact13(outcome: str, reason: str, validated: Sequence[Sequence[str]]) -> dict[str, Any]:
    pairs = [list(pair) for pair in validated]
    return dict(zip(RESULT_FIELDS, (
        SCHEMA, RULE_ID, RULE_NAME, outcome, outcome == "passed", outcome != "passed", reason,
        pairs, pairs, list(CANDIDATE_FIELDS), list(CONTEXT_ITEMS), False, ADAPTER_ID,
    ), strict=True))


def _expected_dispatch(reason: str) -> dict[str, Any]:
    return dict(zip(ERROR_FIELDS, (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", RULE_ID, True, True, True, reason,
    ), strict=True))


def _expected_source(outcome: str, reason: str, canonical: str) -> dict[str, Any]:
    validated = [] if canonical == "" else [[CANDIDATE_FIELDS[0], canonical]]
    return dict(zip(SOURCE_FIELDS, (
        RULE_ID, outcome, outcome == "passed", outcome != "passed", reason, canonical,
        validated, list(CANDIDATE_FIELDS), list(CONTEXT_ITEMS), False,
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
    if type(context) is not tuple:
        context_reason = CONTEXT_VALUE_REASONS[0]
    elif any(type(member) is not str for member in context) or context != ALLOWED_CLASSES:
        context_reason = CONTEXT_VALUE_REASONS[1]
    else:
        context_reason = ""
    if reason:
        return _expected_source("invalid", reason, "")
    if context_reason:
        return _expected_source("invalid", context_reason, canonical)
    if canonical == ENUM_MEMBERS[2]:
        return _expected_source("blocked", BLOCKED_REASON, canonical)
    return _expected_source("passed", "", canonical)


def _json_value(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _expected_contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "admission_rule_id", RULE_ID),
        ("identity", "admission_rule_name", RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID),
        ("identity", "formal_evaluator", FORMAL_EVALUATOR),
        ("identity", "formal_evaluator_source", FORMAL_SOURCE),
        ("runtime_reuse", "public_api", "evaluate_admission_rule"),
        ("runtime_reuse", "result_type", "UnifiedAdmissionRuleEvaluation"),
        ("runtime_reuse", "dispatch_error_type", "UnifiedAdmissionDispatchError"),
        ("runtime_reuse", "schema_version", SCHEMA),
        ("runtime_reuse", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("runtime_reuse", "exact6_dispatch_fields", "|".join(ERROR_FIELDS)),
        ("registration", "future_exact7_order", "|".join(FUTURE_ORDER)),
        ("registration", "current_exact6_order", "|".join(CURRENT_ORDER)),
        ("precedence", "complete_execution_precedence", "|".join(EXECUTION_PRECEDENCE)),
        ("routing", "context_order", "batch_context|evaluation_context|download_result_context|stage_authorization_context"),
        ("routing", "batch_context", "exact_none"),
        ("routing", "evaluation_context", "mapping_subclass_accepted_required_key_extra_keys_ignored"),
        ("routing", "routed_context_value", "single_getitem_original_identity_no_prevalidation_copy_or_mutation"),
        ("routing", "download_result_context", "exact_none"),
        ("routing", "stage_authorization_context", "exact_none"),
        ("candidate", "candidate_record", "mapping_subclass_accepted_extra_fields_ignored_no_copy_no_mutation"),
        ("candidate", "required_field", f"{CANDIDATE_FIELDS[0]}_single_getitem_original_identity"),
        ("candidate", "non_mapping", CANDIDATE_REASON),
        ("missing", "missing_field", MISSING_REASON),
        ("missing", "exact_none", MISSING_REASON),
        ("missing", "exact_builtin_empty_str", MISSING_REASON),
        ("missing", "empty_str_subclass", "not_missing_routed_to_standalone"),
        ("call", "formal_call", "exactly_one_positional_call_original_scalar_and_context_identity"),
        ("call", "normalization", "none_no_trim_casefold_alias_conversion_copy_repair_mutation_or_io"),
        ("source", "exact_type", "type(source)_is_Admit007EvaluationResult_subclass_rejected"),
        ("source", "exact10_fields", "|".join(SOURCE_FIELDS)),
        ("source", "invariants", "exact_vars_dict_order_dataclass_field_order_ordered_reads_committed_dataclass_reconstruction_equality_and_complete_cross_field_validation_before_oracle"),
        ("oracle", "identity", ORACLE_ID),
        ("oracle", "equivalence", "same_original_objects_exactly_once_classification_scalar_context_admit_007_complete_ordered_exact10_equality"),
        ("projection", "mapping", "source_exact10_to_existing_unified_exact13"),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "blocked", "blocked_passthrough_not_rejected_or_invalid"),
        ("projection", "context_invalid", "canonical_and_validated_pair_retained"),
        ("issues", "exact11", "byte_identical_preserved"),
        ("readiness", "next_step", NEXT_STEP),
        ("stop", "adapter_handler", "not_implemented"),
        ("stop", "runtime_registry", "current_exact6_unmodified_admit_007_not_registered"),
        ("stop", "training", "feature_semantics_audit_required_step12d_not_final_contract"),
    )
    return [{"contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
             "contract_group": group, "contract_subject": subject,
             "contract_value": value, "contract_status": "frozen"}
            for index, (group, subject, value) in enumerate(definitions, 1)]


def _expected_routing_rows() -> list[dict[str, str]]:
    context_invalid = _expected_exact13("invalid", CONTEXT_VALUE_REASONS[0], ((CANDIDATE_FIELDS[0], ENUM_MEMBERS[0]),))
    candidate_invalid = _expected_exact13("invalid", CANDIDATE_REASON, ())
    missing_invalid = _expected_exact13("invalid", MISSING_REASON, ())
    cases = (
        ("context", "batch_non_none", "batch_context is object", "dispatch_error", CONTEXT_REASONS["batch_context"], _json_value(_expected_dispatch(CONTEXT_REASONS["batch_context"])), 0, 0, "not_accessed"),
        ("context", "evaluation_non_mapping", "evaluation_context is list", "dispatch_error", CONTEXT_REASONS["evaluation_context"], _json_value(_expected_dispatch(CONTEXT_REASONS["evaluation_context"])), 0, 0, "not_accessed"),
        ("context", "evaluation_key_missing", "evaluation Mapping lacks required key", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], _json_value(_expected_dispatch(CONTEXT_REASONS["evaluation_context_key"])), 0, 0, "not_accessed"),
        ("context", "download_non_none", "download_result_context is object", "dispatch_error", CONTEXT_REASONS["download_result_context"], _json_value(_expected_dispatch(CONTEXT_REASONS["download_result_context"])), 0, 0, "not_accessed"),
        ("context", "stage_non_none", "stage_authorization_context is object", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], _json_value(_expected_dispatch(CONTEXT_REASONS["stage_authorization_context"])), 0, 0, "not_accessed"),
        ("context", "multiple_failure_precedence", "batch and later contexts invalid", "first_dispatch_error_only", CONTEXT_REASONS["batch_context"], _json_value(_expected_dispatch(CONTEXT_REASONS["batch_context"])), 0, 0, "not_accessed"),
        ("context", "evaluation_mapping_subclass", "Mapping subclass with required key", "accepted_without_copy", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_extra_keys", "extra evaluation keys", "ignored", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_not_mutated", "mutable Mapping sentinel", "not_mutated", "", "", 1, 1, "accessed_after_context"),
        ("context", "context_value_identity", "required value identity sentinel with single __getitem__ lookup", "same_object_passed_single_lookup", "", "", 1, 1, "accessed_after_context"),
        ("context", "invalid_value_reaches_standalone", "required value is list", "exact13_invalid_not_dispatch", CONTEXT_VALUE_REASONS[0], _json_value(context_invalid), 1, 1, "accessed_after_context"),
        ("candidate", "candidate_non_mapping", "candidate_record is list", "exact13_invalid", CANDIDATE_REASON, _json_value(candidate_invalid), 0, 0, "envelope_checked"),
        ("candidate", "candidate_key_missing", "required key absent", "exact13_invalid", MISSING_REASON, _json_value(missing_invalid), 0, 0, "presence_only"),
        ("candidate", "candidate_exact_none", "required value is exact None", "exact13_invalid", MISSING_REASON, _json_value(missing_invalid), 0, 0, "value_read_once"),
        ("candidate", "candidate_builtin_empty", "required value exact built-in empty str", "exact13_invalid", MISSING_REASON, _json_value(missing_invalid), 0, 0, "value_read_once"),
        ("candidate", "empty_str_subclass", "required value empty str subclass", "routed_to_standalone_invalid", SCALAR_REASONS[0], "", 1, 1, "value_read_once"),
        ("candidate", "whitespace_not_missing", "required value whitespace-only", "routed_to_standalone_invalid", SCALAR_REASONS[3], "", 1, 1, "value_read_once"),
        ("candidate", "malformed_not_missing", "required value integer", "routed_to_standalone_invalid", SCALAR_REASONS[0], "", 1, 1, "value_read_once"),
        ("candidate", "distance_not_missing", "required value distance_only_inference", "routed_to_standalone_blocked", BLOCKED_REASON, "", 1, 1, "value_read_once"),
        ("candidate", "candidate_mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_extra_fields", "extra candidate fields", "ignored", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_not_mutated", "mutable candidate sentinel", "not_mutated", "", "", 1, 1, "value_read_once"),
        ("candidate", "scalar_identity", "scalar object identity sentinel with single __getitem__ lookup", "same_object_passed_single_lookup", "", "", 1, 1, "value_read_once"),
    )
    return [{"matrix_order": str(index), "matrix_group": group, "case_id": case_id,
             "condition": condition, "expected_behavior": behavior, "expected_reason": reason,
             "expected_result_json": result, "formal_call_count": str(formal),
             "oracle_call_count": str(oracle), "candidate_access_status": access,
             "case_passed": "true"}
            for index, (group, case_id, condition, behavior, reason, result, formal, oracle, access)
            in enumerate(cases, 1)]


STANDALONE_CORPUS = (
    ("CASE_001_canonical_structure_bond", "str", '"explicit_structure_bond_record"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_002_canonical_curated_annotation", "str", '"explicit_curated_covalent_annotation"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_003_canonical_distance_only", "str", '"distance_only_inference"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_004_type_none", "NoneType", "NoneType:None", "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_005_type_int", "int", "int:7", "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_006_type_bool", "bool", "bool:True", "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_007_type_str_subclass", "_StringSubclass", 'str_subclass:"explicit_structure_bond_record"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_008_type_list", "list", 'list:["explicit_structure_bond_record"]', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_009_type_mapping", "dict", 'dict:{"value": "explicit_structure_bond_record"}', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_010_empty", "str", '""', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_011_whitespace_only", "str", '" "', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_012_leading_whitespace", "str", '" explicit_structure_bond_record"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_013_trailing_whitespace", "str", '"explicit_structure_bond_record "', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_014_uppercase", "str", '"Explicit_structure_bond_record"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_015_hyphen", "str", '"explicit-structure-bond-record"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_016_dot", "str", '"explicit.structure"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_017_slash", "str", '"explicit/structure"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_018_non_ascii", "str", '"explicit_\\u00e9vidence"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_019_over_length", "str", '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_020_leading_digit", "str", '"1explicit"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_021_unknown_valid", "str", '"unregistered_value"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_022_unknown_explicit_looking", "str", '"explicit_database_bond"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_023_unknown_manual_review", "str", '"manual_review"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_024_unknown_other", "str", '"other"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_025_unknown_unknown", "str", '"unknown"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_026_context_exact_tuple", "str", '"explicit_structure_bond_record"', "exact_tuple", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_027_context_none", "str", '"explicit_structure_bond_record"', "none", "NoneType:None"),
    ("CASE_028_context_list", "str", '"explicit_structure_bond_record"', "list", 'list:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_029_context_set", "str", '"explicit_structure_bond_record"', "set", 'set:["explicit_curated_covalent_annotation", "explicit_structure_bond_record"]'),
    ("CASE_030_context_frozenset", "str", '"explicit_structure_bond_record"', "frozenset", 'frozenset:["explicit_curated_covalent_annotation", "explicit_structure_bond_record"]'),
    ("CASE_031_context_wrong_order", "str", '"explicit_structure_bond_record"', "wrong_order", 'tuple:["explicit_curated_covalent_annotation", "explicit_structure_bond_record"]'),
    ("CASE_032_context_missing_member", "str", '"explicit_structure_bond_record"', "missing_member", 'tuple:["explicit_structure_bond_record"]'),
    ("CASE_033_context_duplicate", "str", '"explicit_structure_bond_record"', "duplicate", 'tuple:["explicit_structure_bond_record", "explicit_structure_bond_record"]'),
    ("CASE_034_context_distance_only", "str", '"explicit_structure_bond_record"', "distance_only", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation", "distance_only_inference"]'),
    ("CASE_035_context_unknown", "str", '"explicit_structure_bond_record"', "unknown", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation", "unknown"]'),
    ("CASE_036_context_str_subclass", "str", '"explicit_structure_bond_record"', "str_subclass", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation"]'),
    ("CASE_037_context_extra_member", "str", '"explicit_structure_bond_record"', "extra_member", 'tuple:["explicit_structure_bond_record", "explicit_curated_covalent_annotation", "explicit_database_bond"]'),
)


def _decode_corpus_row(specification: Sequence[str]) -> tuple[object, object]:
    _, scalar_kind, scalar_display, context_kind, context_display = specification
    if scalar_kind == "str":
        scalar: object = json.loads(scalar_display)
    elif scalar_kind == "NoneType":
        scalar = None
    elif scalar_kind == "int":
        scalar = int(scalar_display.removeprefix("int:"))
    elif scalar_kind == "bool":
        scalar = scalar_display == "bool:True"
    elif scalar_kind == "_StringSubclass":
        scalar = _StringSubclass(json.loads(scalar_display.removeprefix("str_subclass:")))
    elif scalar_kind == "list":
        scalar = json.loads(scalar_display.removeprefix("list:"))
    elif scalar_kind == "dict":
        scalar = json.loads(scalar_display.removeprefix("dict:"))
    else:
        raise AssertionError(f"unknown checker corpus scalar kind: {scalar_kind}")
    if context_kind == "none":
        context: object = None
    elif context_kind == "list":
        context = json.loads(context_display.removeprefix("list:"))
    elif context_kind == "set":
        context = set(json.loads(context_display.removeprefix("set:")))
    elif context_kind == "frozenset":
        context = frozenset(json.loads(context_display.removeprefix("frozenset:")))
    else:
        members = json.loads(context_display.removeprefix("tuple:"))
        if context_kind == "str_subclass":
            members[0] = _StringSubclass(members[0])
        context = tuple(members)
    return scalar, context


def _truth_row(case_id: str, group: str, behavior: str, reason: str = "", *,
               source: Mapping[str, Any] | None = None, oracle: Mapping[str, Any] | None = None,
               unified: Mapping[str, Any] | None = None, code: str = "", formal: int = 0,
               oracle_calls: int = 0) -> dict[str, str]:
    return {"case_id": case_id, "case_group": group, "behavior": behavior,
            "expected_dispatch_code": code, "expected_reason": reason,
            "source_exact10_json": _json_value(source) if source is not None else "",
            "oracle_exact10_json": _json_value(oracle) if oracle is not None else "",
            "unified_exact13_json": _json_value(unified) if unified is not None else "",
            "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls),
            "case_passed": "true"}


def _expected_truth_rows(standalone_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    observed_corpus = tuple((row["case_id"], row["scalar_input_kind"], row["scalar_input_display"], row["context_input_kind"], row["context_input_display"]) for row in standalone_rows)
    if observed_corpus != STANDALONE_CORPUS:
        raise AssertionError("committed standalone Exact37 corpus changed")
    rows = []
    for specification, predecessor in zip(STANDALONE_CORPUS, standalone_rows, strict=True):
        scalar, context = _decode_corpus_row(specification)
        source = _classify(scalar, context)
        if predecessor["observed_outcome"] != source["outcome"] or predecessor["observed_reason"] != source["reason"]:
            raise AssertionError(f"standalone/oracle outcome mismatch: {specification[0]}")
        if predecessor["observed_canonical_evidence_source"] != source["canonical_covalent_event_evidence_source"]:
            raise AssertionError(f"standalone/oracle canonical mismatch: {specification[0]}")
        if json.loads(predecessor["observed_validated_candidate_fields"]) != source["validated_candidate_fields"]:
            raise AssertionError(f"standalone/oracle validated mismatch: {specification[0]}")
        unified = _expected_exact13(source["outcome"], source["reason"], source["validated_candidate_fields"])
        rows.append(_truth_row(f"STANDALONE_{specification[0]}", "standalone_exact37", "exact10_to_exact13",
                               source["reason"], source=source, oracle=source, unified=unified,
                               formal=1, oracle_calls=1))
    rows.append(_truth_row("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13",
                           CANDIDATE_REASON, unified=_expected_exact13("invalid", CANDIDATE_REASON, ())))
    for suffix in ("field_missing", "value_none", "value_builtin_empty"):
        rows.append(_truth_row(f"CANDIDATE_{suffix}", "adapter_candidate_invalid", "adapter_generated_exact13",
                               MISSING_REASON, unified=_expected_exact13("invalid", MISSING_REASON, ())))
    for key in ("batch_context", "evaluation_context", "evaluation_context_key", "download_result_context", "stage_authorization_context"):
        rows.append(_truth_row(f"ROUTING_{key}", "routing_dispatch", "exact6_no_partial_result",
                               CONTEXT_REASONS[key], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"))
    valid = _classify(ENUM_MEMBERS[0], ALLOWED_CLASSES)
    rows.extend((
        _truth_row("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_invariant", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_oracle_mismatch", "source_validation_failure", "no_projection", SOURCE_INVARIANT_REASON, source=valid, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1, oracle_calls=1),
    ))
    special = (
        ("explicit_passed", ENUM_MEMBERS[0], ALLOWED_CLASSES),
        ("distance_blocked", ENUM_MEMBERS[2], ALLOWED_CLASSES),
        ("scalar_invalid", object(), ALLOWED_CLASSES),
        ("context_invalid_canonical_retained", ENUM_MEMBERS[0], []),
    )
    for name, scalar, context in special:
        source = _classify(scalar, context)
        rows.append(_truth_row(f"PROJECTION_{name}", "projection_semantics", "projection_frozen",
                               source["reason"], source=source, oracle=source,
                               unified=_expected_exact13(source["outcome"], source["reason"], source["validated_candidate_fields"]),
                               formal=1, oracle_calls=1))
    rows.extend((
        _truth_row("BOUNDARY_current_exact6", "runtime_boundary", "registry_unchanged"),
        _truth_row("BOUNDARY_admit007_not_registered", "runtime_boundary", "handler_not_implemented_runtime_unchanged"),
    ))
    return rows


def _expected_safety_rows() -> list[dict[str, str]]:
    positive = (
        "fixed_ordered_source_boundary", "all_structural_checks_before_source_bytes", "source_sha256_verified",
        "snapshot_only_ast_csv_json_parsing", "exact11_issue_byte_preservation", "deterministic_materialization",
        "candidate_projection_contract", "context_routing_contract", "missing_value_contract",
        "exact10_source_validation", "independent_oracle_equivalence", "exact13_projection_contract",
        "blocked_passthrough", "context_invalid_partial_canonical_projection", "current_exact6_verified",
    )
    negative = (
        "adapter_handler_implementation", "registry_modification", "admit_007_registration", "admit_008_work",
        "evaluate_all_rules", "combined_candidate_verdict", "cross_rule_aggregation", "provider_mapping",
        "raw_read", "structure_parsing", "network", "download", "real_candidate_evaluation", "checkpoint_access",
        "torch", "numpy", "rdkit", "model_forward", "loss", "training", "fine_tune", "parameter_update",
        "stage", "commit", "push", "gh",
    )
    return [{"safety_item": item, "expected_executed": expected, "observed_executed": expected, "safety_passed": "true"}
            for item, expected in ((*((item, "true") for item in positive), *((item, "false") for item in negative)))]


PROTECTED_BUILDERS = {
    "_expected_exact13", "_expected_dispatch", "_expected_source", "_classify",
    "_decode_corpus_row", "_expected_contract_rows", "_expected_routing_rows",
    "_expected_truth_rows", "_expected_safety_rows", "_expected_readiness",
    "_expected_source_boundary",
}


def _assert_ast_independence(source_text: str | None = None) -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8") if source_text is None else source_text)
    forbidden_attributes = {
        "_contract_rows", "_routing_rows", "_truth_rows", "_safety_rows", "_payloads",
        "build_design_state", "classify_admit_007_independent_design",
        "project_exact10_to_exact13_for_design", "candidate_invalid_exact13_for_design",
        "validate_source_shape_and_invariants_for_design", "validate_source_oracle_equivalence_for_design",
        "SOURCE_PATHS", "SOURCE_SHA256", "READINESS", "EXECUTION_PRECEDENCE",
    }
    seen = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in PROTECTED_BUILDERS:
            seen.add(node.name)
            names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
            attributes = {child.attr for child in ast.walk(node) if isinstance(child, ast.Attribute)}
            if names & {"gate", "standalone", "runtime", "registry"} or attributes & forbidden_attributes:
                raise AssertionError(f"checker semantic builder depends on production: {node.name}")
    if source_text is None and seen != PROTECTED_BUILDERS:
        raise AssertionError("protected checker builder inventory changed")


def _read_csv_document(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AssertionError(f"CSV header missing: {path.name}")
        return tuple(reader.fieldnames), list(reader)


def _validate_frozen_output_hashes(root: Path) -> None:
    for name, expected in FROZEN_OUTPUT_SHA256.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"frozen output SHA256 mismatch: {name}")


def _validate_source_boundary(production: Any) -> None:
    expected = _expected_source_boundary()
    if tuple(path.as_posix() for path in production.SOURCE_PATHS) != tuple(path for path, _ in expected):
        raise AssertionError("production source boundary path/order mismatch")
    if tuple(production.SOURCE_SHA256[path] for path in production.SOURCE_PATHS) != tuple(digest for _, digest in expected):
        raise AssertionError("production source boundary SHA map mismatch")
    for relative, digest in expected:
        path = ROOT / relative
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise AssertionError(f"source not regular non-symlink: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise AssertionError(f"source SHA mismatch: {relative}")


def _validate_contract_rows(header: Sequence[str], rows: Sequence[Mapping[str, str]]) -> None:
    expected = _expected_contract_rows()
    if tuple(header) != CONTRACT_COLUMNS or list(rows) != expected:
        raise AssertionError("Exact43 contract rows mismatch")
    if len(rows) != 43 or len({row["contract_id"] for row in rows}) != 43 or any(row["contract_status"] != "frozen" for row in rows):
        raise AssertionError("Exact43 contract invariants mismatch")


def _validate_routing_rows(header: Sequence[str], rows: Sequence[Mapping[str, str]]) -> None:
    expected = _expected_routing_rows()
    if tuple(header) != ROUTING_COLUMNS or list(rows) != expected:
        raise AssertionError("Exact23 routing rows mismatch")


def _validate_truth_rows(header: Sequence[str], rows: Sequence[Mapping[str, str]],
                         standalone_header: Sequence[str], standalone_rows: Sequence[Mapping[str, str]]) -> None:
    if tuple(standalone_header) != STANDALONE_COLUMNS or len(standalone_rows) != 37:
        raise AssertionError("committed standalone Exact37 shape mismatch")
    expected = _expected_truth_rows(standalone_rows)
    if tuple(header) != TRUTH_COLUMNS or list(rows) != expected:
        raise AssertionError("Exact56 truth rows mismatch")
    counts = Counter(row["case_group"] for row in rows)
    if counts != {"standalone_exact37": 37, "adapter_candidate_invalid": 4, "routing_dispatch": 5,
                  "source_validation_failure": 4, "projection_semantics": 4, "runtime_boundary": 2}:
        raise AssertionError("Exact56 truth groups mismatch")


def _validate_safety_rows(header: Sequence[str], rows: Sequence[Mapping[str, str]]) -> None:
    expected = _expected_safety_rows()
    if tuple(header) != SAFETY_COLUMNS or list(rows) != expected or len(rows) != 41:
        raise AssertionError("Exact41 safety rows mismatch")


def _validate_issue_rows(header: Sequence[str], rows: Sequence[Mapping[str, str]], content: bytes) -> None:
    predecessor = ROOT / SOURCE_BOUNDARY[2][0]
    if tuple(header) != ISSUE_COLUMNS or len(rows) != 11:
        raise AssertionError("Exact11 issue shape mismatch")
    if content != predecessor.read_bytes() or hashlib.sha256(content).hexdigest() != FROZEN_OUTPUT_SHA256[OUTPUTS[4]]:
        raise AssertionError("Exact11 issue bytes mismatch")
    issues = {row["issue_id"]: row for row in rows}
    if issues["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"] != "resolved":
        raise AssertionError("enum issue state mismatch")
    if issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] != "open" or "ADMIT_007" not in issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].split("|"):
        raise AssertionError("coverage issue state mismatch")
    if issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise AssertionError("aggregation issue state mismatch")


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    readiness = _expected_readiness()
    expected_output_hashes = {name: FROZEN_OUTPUT_SHA256[name] for name in OUTPUTS[:-1]}
    exact = {
        "project": "CovaPIE", "step": "ADMIT_007 unified adapter contract design gate v1",
        "stage": "covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1",
        "manifest_schema_version": "covapie_admit_007_unified_adapter_contract_manifest_v1",
        "expected_base_commit": EXPECTED_BASE, "expected_base_subject": EXPECTED_SUBJECT,
        "recommended_next_step": NEXT_STEP, "admission_rule_id": RULE_ID,
        "admission_rule_name": RULE_NAME, "adapter_id": ADAPTER_ID,
        "formal_evaluator": FORMAL_EVALUATOR, "formal_result_type": "Admit007EvaluationResult",
        "future_adapter_handler": "_evaluate_registered_admit_007",
        "formal_evaluator_source": FORMAL_SOURCE,
        "independent_oracle": ORACLE_ID, "independent_oracle_outcome_view": "classification.admit_007",
        "candidate_field": CANDIDATE_FIELDS[0], "evaluation_context_item": CONTEXT_ITEMS[0],
        "future_registered_rule_order": list(FUTURE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_ORDER),
        "current_registered_rule_order": list(CURRENT_ORDER), "execution_precedence": list(EXECUTION_PRECEDENCE),
        "known_rule_ids": list(KNOWN_RULE_IDS), "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[7:]),
        "known_not_registered_behavior": "known_not_registered_fail_closed",
        "result_schema_version": SCHEMA, "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(SOURCE_FIELDS), "dispatch_error_fields": list(ERROR_FIELDS),
        "dispatch_error_codes": list(ERROR_CODES), "outcome_vocabulary": list(OUTCOMES),
        "adapter_missing_categories": ["required_key_absent", "exact_none", "exact_builtin_empty_str"],
        "adapter_missing_reason": MISSING_REASON, "candidate_mapping_invalid_reason": CANDIDATE_REASON,
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "formal_blocked_reason": BLOCKED_REASON, "blocked_passthrough": True,
        "context_invalid_partial_canonical_projection": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "contract_row_count": 43, "routing_matrix_row_count": 23,
        "routing_matrix_group_counts": {"candidate": 12, "context": 11},
        "projection_truth_matrix_row_count": 56,
        "projection_truth_matrix_group_counts": {"adapter_candidate_invalid": 4, "projection_semantics": 4, "routing_dispatch": 5, "runtime_boundary": 2, "source_validation_failure": 4, "standalone_exact37": 37},
        "issue_inventory_row_count": 11, "issue_inventory_preserved_byte_identical": True,
        "source_input_count": 14, "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": {path: digest for path, digest in SOURCE_BOUNDARY},
        "source_input_verification": "expected_sha256_equals_base_tree_sha256_equals_filesystem_sha256",
        "source_boundary_name": "fixed_exact14_committed_source_boundary",
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_file_count": 6, "output_files": list(OUTPUTS), "output_sha256": expected_output_hashes,
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "adapter_handler_not_implemented", "exact6_runtime_unchanged", "admit_007_unregistered",
            "admit_008_not_started", "evaluate_all_rules_not_implemented",
            "combined_candidate_verdict_not_implemented", "provider_mapping_not_validated",
            "real_candidate_evaluation_not_executed", "bulk_download_forbidden", "training_forbidden",
        ],
        "attestations": {
            "exact43_contract_frozen": True, "exact23_routing_frozen": True,
            "exact56_truth_frozen": True, "exact41_safety_frozen": True,
            "exact11_issue_bytes_preserved": True, "exact14_sources_verified": True,
            "formal_called_exactly_once_after_missing_gate": True,
            "source_prevalidated_before_oracle": True,
            "oracle_complete_exact10_equality_required": True,
            "no_partial_exact13_on_failure": True,
        },
        "validation_failures": [], "readiness": readiness,
        **readiness, "all_checks_passed": True,
    }
    if type(manifest) is not dict or dict(manifest) != exact:
        raise AssertionError("manifest complete dictionary mismatch")


def _validate_output_tree(root: Path, *, enforce_frozen_hashes: bool = True,
                          expected_materialized: Path | None = None,
                          production: Any | None = None) -> dict[str, int]:
    entries = tuple(sorted(path.name for path in root.iterdir()))
    if entries != tuple(sorted(OUTPUTS)):
        raise AssertionError("output set is not Exact6")
    for name in OUTPUTS:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise AssertionError(f"output not regular non-symlink: {name}")
    if enforce_frozen_hashes:
        _validate_frozen_output_hashes(root)
    contract_header, contract_rows = _read_csv_document(root / OUTPUTS[0])
    routing_header, routing_rows = _read_csv_document(root / OUTPUTS[1])
    truth_header, truth_rows = _read_csv_document(root / OUTPUTS[2])
    safety_header, safety_rows = _read_csv_document(root / OUTPUTS[3])
    issue_header, issue_rows = _read_csv_document(root / OUTPUTS[4])
    standalone_header, standalone_rows = _read_csv_document(ROOT / SOURCE_BOUNDARY[6][0])
    _validate_contract_rows(contract_header, contract_rows)
    _validate_routing_rows(routing_header, routing_rows)
    _validate_truth_rows(truth_header, truth_rows, standalone_header, standalone_rows)
    _validate_safety_rows(safety_header, safety_rows)
    _validate_issue_rows(issue_header, issue_rows, (root / OUTPUTS[4]).read_bytes())
    _validate_manifest(json.loads((root / OUTPUTS[5]).read_text(encoding="utf-8")))
    if production is not None:
        _validate_source_boundary(production)
        expected_state = (_expected_contract_rows(), _expected_routing_rows(),
                          _expected_truth_rows(standalone_rows), _expected_safety_rows(), _expected_readiness())
        observed_state = (production._contract_rows(), production._routing_rows(),
                          production._truth_rows(standalone_rows), production._safety_rows(), production.READINESS)
        if observed_state != expected_state:
            raise AssertionError("production design state differs from checker-owned semantics")
    if expected_materialized is not None:
        for name in OUTPUTS:
            if (root / name).read_bytes() != (expected_materialized / name).read_bytes():
                raise AssertionError(f"disk output differs from deterministic rematerialization: {name}")
    return {"contract_rows": 43, "routing_rows": 23, "truth_rows": 56,
            "safety_rows": 41, "issue_rows": 11, "source_count": 14}


def _assert_production_ast() -> None:
    path = ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "_evaluate_registered_admit_007" in functions or "evaluate_admission_rule" in functions:
        raise AssertionError("runtime handler present in design gate")
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in targets):
            raise AssertionError("registry present in design gate")


def main() -> int:
    _assert_ast_independence()
    _assert_production_ast()
    if subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_BASE, "HEAD"], cwd=ROOT).returncode:
        raise AssertionError("non-descendant base")
    subject = subprocess.run(["git", "show", "-s", "--format=%s", EXPECTED_BASE], cwd=ROOT, capture_output=True, text=True, check=True).stdout.rstrip("\n")
    if subject != EXPECTED_SUBJECT:
        raise AssertionError("base subject mismatch")
    # Construct all checker-owned semantics before production is imported.
    standalone_header, standalone_rows = _read_csv_document(ROOT / SOURCE_BOUNDARY[6][0])
    _expected_source_boundary(); _expected_readiness(); _expected_contract_rows()
    _expected_routing_rows(); _expected_truth_rows(standalone_rows); _expected_safety_rows()
    if standalone_header != STANDALONE_COLUMNS:
        raise AssertionError("standalone corpus header mismatch")
    sys.path.insert(0, str(ROOT / "src"))
    production = importlib.import_module(MODULE_NAME)
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root, second_root = Path(first), Path(second)
        production.run_covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1(first_root)
        production.run_covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1(second_root)
        for name in OUTPUTS:
            if (first_root / name).read_bytes() != (second_root / name).read_bytes():
                raise AssertionError(f"double materialization differs: {name}")
        summary = _validate_output_tree(OUTPUT_ROOT, expected_materialized=first_root, production=production)
    summary.update({"all_checks_passed": True, "output_file_count": 6,
                    "readiness": "ready_for_unified_dispatch_runtime_with_admit_001_to_007_implementation"})
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
