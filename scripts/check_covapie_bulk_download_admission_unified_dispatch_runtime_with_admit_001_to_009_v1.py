#!/usr/bin/env python3
"""Independent fail-closed checker for the ADMIT_001-to-009 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009
    as runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_009_rule_logic_interface as admit009,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate
    as admit009_oracle,
)


EXPECTED_BASE_COMMIT = "a0e5d56cc0afd8d2677aa53bd629fb33948ffaf3"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_009 unified adapter contract design v1"
PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_009 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_009_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_009_manifest_v1"
)
NEXT_STEP = "audit_covapie_admit_010_formal_evaluator_interface_preconditions_v1"
SOURCE_BOUNDARY_NAME = "fixed_ordered_exact18_committed_source_boundary"
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py", "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_manifest.json", "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_contract.csv", "27d0c9d941698d99d045b367889ccd388f708353bcd342eb7f57729bb99940f9"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_truth_matrix.csv", "4b2010ac1fc84a884cfa798e825c26816acb6feb7d330b14fcf823b67f8bf65e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_registry_routing_and_oracle_audit.csv", "a77ca44d59dd3984be23f86923acabd52594e9b2e6958a38aeb5719313d88c4f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_safety_audit.csv", "4467d5d2c33808aa7e5ef793278462a8a5fa6796768d9c37717d2a6b07189635"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_issue_inventory.csv", "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py", "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json", "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_contract.csv", "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_truth_matrix.csv", "42b2373c398c737d697ffd8177b6971fe2ad9aa9cbfb813d594b9527b0eaa9b3"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py", "9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract_manifest.json", "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract.csv", "1b490f4b3263292e5d42a58ef53caf53e6b2e836d27d9966fc8250ccffb2f7b3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_candidate_projection_and_context_routing_matrix.csv", "b91a358411f1ac4600868c6f6ef4e2d02e4348edd22cb25cb7b8822de9c9a5e6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_result_projection_truth_matrix.csv", "f98d5c0ab1a41e02a6a389757e447b85469887e718cd8a9a07ac4d84d84892bd"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_issue_readiness_inventory.csv", "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py", "bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26"),
)
PREDECESSOR_TRUTH_PATH = Path(SOURCE_BOUNDARY[3][0])
DESIGN_ISSUE_PATH = Path(SOURCE_BOUNDARY[16][0])
DESIGN_ISSUE_SHA256 = SOURCE_BOUNDARY[16][1]

CONTRACT_FILENAME = "covapie_admit_001_to_009_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_009_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_009_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_009_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_009_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_009_runtime_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

# Independently frozen after deterministic double materialization; no value is
# inferred from the manifest being checked.
EXPECTED_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "28afebbc6351d10ceeabedb5fdbe99bd3549b784a02682d9875a66b769f12bec",
    TRUTH_FILENAME: "60bbd1f01390da057a954e3b531cd28ffa97041f38577e49160625218c0186bf",
    REGISTRY_FILENAME: "6a3471a08d65e0d0d0f6c6cf258016a670e7f324ab5b9ea4a3b8cff7b1723ba9",
    SAFETY_FILENAME: "8109395409a7a26ba483eb84bb14c0db1c19365bad0c96a3d0d9656ef524c344",
    ISSUE_FILENAME: "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6",
    MANIFEST_FILENAME: "b4d5092949292f27310a05ef2c5c77c8036e7ad0474a15b8a0574bc910931dfc",
}
MANIFEST_OUTPUT_SHA256 = {
    name: EXPECTED_OUTPUT_SHA256[name] for name in CSV_OUTPUTS
}

CONTRACT_HEADER = (
    "contract_id", "contract_area", "contract_statement", "expected_value",
    "observed_value", "contract_passed",
)
TRUTH_HEADER = (
    "case_id", "case_group", "admission_rule_id", "behavior",
    "expected_result_or_error", "observed_result_or_error", "expected_reason",
    "observed_reason", "formal_call_count", "oracle_call_count",
    "candidate_access_status", "predecessor_handler_identity_status",
    "case_passed",
)
REGISTRY_HEADER = (
    "rule_id", "rule_name", "known_rule", "callable_discovered",
    "adapter_ready", "registered", "adapter_id", "handler_identity_status",
    "dispatch_disposition", "audit_passed",
)
SAFETY_HEADER = (
    "safety_item", "expected_executed", "observed_executed", "safety_passed",
)
ISSUE_HEADER = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)
HEADERS = {
    CONTRACT_FILENAME: CONTRACT_HEADER,
    TRUTH_FILENAME: TRUTH_HEADER,
    REGISTRY_FILENAME: REGISTRY_HEADER,
    SAFETY_FILENAME: SAFETY_HEADER,
    ISSUE_FILENAME: ISSUE_HEADER,
}

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED_RULE_IDS = KNOWN_RULE_IDS[:9]
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_duplicate_identity_key", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid", "rejected")
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
PUBLIC_SIGNATURE = (
    "(admission_rule_id: 'str', candidate_record: 'Mapping[str, object]', *, "
    "batch_context: 'Mapping[str, object] | None' = None, evaluation_context: "
    "'Mapping[str, object] | None' = None, download_result_context: "
    "'Mapping[str, object] | None' = None, stage_authorization_context: "
    "'Mapping[str, object] | None' = None) -> 'UnifiedAdmissionRuleEvaluation'"
)
RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
    "ADMIT_008": "topology_restoration_disposition",
    "ADMIT_009": "duplicate_identity_precheck",
}
ADAPTER_IDS = {
    rule_id: f"covapie_admit_{index:03d}_unified_adapter_v1"
    for index, rule_id in enumerate(REGISTERED_RULE_IDS, 1)
}
CANDIDATE_FIELDS = ("duplicate_identity_key",)
CONTEXT_ITEMS = (
    "duplicate_identity_key_contract",
    "batch_duplicate_identity_keys",
)
KEY_PREFIX = "covapie_dup_v1_sha256_"
POLICY_VALUE = "covapie_duplicate_identity_key_contract_v1"
SCALAR_REASONS = (
    "DUPLICATE_IDENTITY_KEY_TYPE_INVALID",
    "DUPLICATE_IDENTITY_KEY_EMPTY",
    "DUPLICATE_IDENTITY_KEY_NON_ASCII",
    "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID",
)
POLICY_REASONS = (
    "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID",
    "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID",
)
BATCH_REASONS = (
    "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID",
)
DUPLICATE_REASON = "DUPLICATE_IDENTITY_KEY_ALREADY_PRESENT"
TRUTH_GROUP_COUNTS = {
    "predecessor_exact8_truth": 203,
    "global_dispatch": 9,
    "predecessor_handler_identity": 8,
    "admit009_standalone_exact32": 32,
    "admit009_context_routing": 8,
    "admit009_candidate_and_lookup": 6,
    "admit009_call_identity": 4,
    "admit009_source_oracle": 7,
    "registry_issue_boundary": 12,
}
TRUE_READINESS = (
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "exact9_public_dispatch_new_successor_function",
    "exact9_public_dispatch_signature_matches_exact8",
    "exact9_public_dispatch_uses_local_registry",
    "exact9_reuses_exact8_public_type_identity",
    "exact9_first_eight_handler_identity_preserved",
    "admit_009_context_routing_runtime_enforced",
    "admit_009_key_absent_only_missing_runtime_enforced",
    "admit_009_original_object_identity_runtime_enforced",
    "admit_009_formal_exactly_once_runtime_enforced",
    "admit_009_source_exact10_validation_runtime_enforced",
    "admit_009_oracle_exactly_once_runtime_enforced",
    "admit_009_source_oracle_full_exact10_equality_runtime_enforced",
    "admit_009_exact10_to_exact13_projection_runtime_enforced",
    "admit_009_provider_mapping_boundary_preserved",
    "ready_for_admit_010_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero",
    "admit_010_standalone_evaluator_implemented",
    "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)


class _StringSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AssertionError("CSV header missing")
        rows = [dict(row) for row in reader]
    return tuple(reader.fieldnames), rows


def _readiness() -> dict[str, bool]:
    return {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }


def _canonical_key(value: object) -> bool:
    if type(value) is not str or not value.isascii():
        return False
    if not value.startswith(KEY_PREFIX) or len(value) != len(KEY_PREFIX) + 64:
        return False
    return all(character in "0123456789abcdef" for character in value[len(KEY_PREFIX):])


def _classify(scalar: object, batch: object, policy: object) -> dict[str, Any]:
    if type(scalar) is not str:
        reason = SCALAR_REASONS[0]
        canonical = ""
        contexts: tuple[str, ...] = ()
    elif scalar == "":
        reason = SCALAR_REASONS[1]
        canonical = ""
        contexts = ()
    elif not scalar.isascii():
        reason = SCALAR_REASONS[2]
        canonical = ""
        contexts = ()
    elif not _canonical_key(scalar):
        reason = SCALAR_REASONS[3]
        canonical = ""
        contexts = ()
    else:
        canonical = scalar
        if type(policy) is not str:
            reason = POLICY_REASONS[0]
            contexts = CONTEXT_ITEMS[:1]
        elif policy != POLICY_VALUE:
            reason = POLICY_REASONS[1]
            contexts = CONTEXT_ITEMS[:1]
        elif type(batch) is not tuple:
            reason = BATCH_REASONS[0]
            contexts = CONTEXT_ITEMS
        elif any(type(member) is not str for member in batch):
            reason = BATCH_REASONS[1]
            contexts = CONTEXT_ITEMS
        elif any(not _canonical_key(member) for member in batch):
            reason = BATCH_REASONS[2]
            contexts = CONTEXT_ITEMS
        elif any(left >= right for left, right in zip(batch, batch[1:])):
            reason = BATCH_REASONS[3]
            contexts = CONTEXT_ITEMS
        elif canonical in batch:
            reason = DUPLICATE_REASON
            contexts = CONTEXT_ITEMS
        else:
            reason = ""
            contexts = CONTEXT_ITEMS
    outcome = "passed" if reason == "" else (
        "blocked" if reason == DUPLICATE_REASON else "invalid"
    )
    validated = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
    return {
        "admission_rule_id": "ADMIT_009",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_duplicate_identity_key": canonical,
        "validated_candidate_fields": validated,
        "consumed_candidate_fields": CANDIDATE_FIELDS,
        "consumed_context_items": contexts,
        "evaluator_io_used": False,
    }


def _project(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "admission_rule_id": source["admission_rule_id"],
        "admission_rule_name": "duplicate_identity_precheck",
        "outcome": source["outcome"],
        "passed": source["passed"],
        "blocks_candidate": source["blocks_candidate"],
        "reason": source["reason"],
        "normalized_values": source["validated_candidate_fields"],
        "validated_candidate_fields": source["validated_candidate_fields"],
        "consumed_candidate_fields": source["consumed_candidate_fields"],
        "consumed_context_items": source["consumed_context_items"],
        "evaluator_io_used": source["evaluator_io_used"],
        "adapter_id": "covapie_admit_009_unified_adapter_v1",
    }


def _candidate_invalid(reason: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "admission_rule_id": "ADMIT_009",
        "admission_rule_name": "duplicate_identity_precheck",
        "outcome": "invalid",
        "passed": False,
        "blocks_candidate": True,
        "reason": reason,
        "normalized_values": (),
        "validated_candidate_fields": (),
        "consumed_candidate_fields": CANDIDATE_FIELDS,
        "consumed_context_items": CONTEXT_ITEMS,
        "evaluator_io_used": False,
        "adapter_id": "covapie_admit_009_unified_adapter_v1",
    }


def _error(
    code: str,
    rule_id: str,
    reason: str,
    *,
    known: bool,
    callable_discovered: bool,
    adapter_ready: bool,
) -> dict[str, Any]:
    return {
        "code": code,
        "admission_rule_id": rule_id,
        "known_rule": known,
        "callable_discovered": callable_discovered,
        "adapter_ready": adapter_ready,
        "reason": reason,
    }


def _json_record(value: Mapping[str, Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=False)


def _expected_row(
    case_id: str,
    group: str,
    rule_id: str,
    behavior: str,
    value: Mapping[str, Any],
    *,
    formal: int = 0,
    oracle: int = 0,
    access: str = "not_applicable",
    identity: str = "not_applicable",
) -> dict[str, str]:
    reason = str(value["reason"])
    rendered = _json_record(value)
    return {
        "case_id": case_id,
        "case_group": group,
        "admission_rule_id": rule_id,
        "behavior": behavior,
        "expected_result_or_error": rendered,
        "observed_result_or_error": rendered,
        "expected_reason": reason,
        "observed_reason": reason,
        "formal_call_count": str(formal),
        "oracle_call_count": str(oracle),
        "candidate_access_status": access,
        "predecessor_handler_identity_status": identity,
        "case_passed": "true",
    }


def _truth_definitions() -> tuple[tuple[str, str, object, object, object], ...]:
    key = KEY_PREFIX + "1" * 64
    low = KEY_PREFIX + "0" * 64
    high = KEY_PREFIX + "2" * 64
    other = KEY_PREFIX + "f" * 64
    empty: tuple[str, ...] = ()
    return (
        ("scalar", "scalar_none", None, empty, POLICY_VALUE),
        ("scalar", "scalar_integer", 7, empty, POLICY_VALUE),
        ("scalar", "scalar_str_subclass", _StringSubclass(key), empty, POLICY_VALUE),
        ("scalar", "scalar_empty", "", empty, POLICY_VALUE),
        ("scalar", "scalar_non_ascii", KEY_PREFIX + "é" * 64, empty, POLICY_VALUE),
        ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, empty, POLICY_VALUE),
        ("scalar", "scalar_uppercase_digest", KEY_PREFIX + "A" * 64, empty, POLICY_VALUE),
        ("scalar", "scalar_short_digest", KEY_PREFIX + "1" * 63, empty, POLICY_VALUE),
        ("scalar", "scalar_long_digest", KEY_PREFIX + "1" * 65, empty, POLICY_VALUE),
        ("scalar", "scalar_non_hex", KEY_PREFIX + "g" * 64, empty, POLICY_VALUE),
        ("scalar", "scalar_whitespace", " " + key, empty, POLICY_VALUE),
        ("scalar", "scalar_canonical", key, empty, POLICY_VALUE),
        ("policy", "policy_none", key, empty, None),
        ("policy", "policy_str_subclass", key, empty, _StringSubclass(POLICY_VALUE)),
        ("policy", "policy_wrong_value", key, empty, "covapie_duplicate_identity_key_contract_v2"),
        ("policy", "policy_exact_valid", key, empty, POLICY_VALUE),
        ("batch", "batch_none", key, None, POLICY_VALUE),
        ("batch", "batch_list", key, [], POLICY_VALUE),
        ("batch", "batch_tuple_subclass", key, _TupleSubclass(), POLICY_VALUE),
        ("batch", "batch_non_str_member", key, (7,), POLICY_VALUE),
        ("batch", "batch_str_subclass_member", key, (_StringSubclass(other),), POLICY_VALUE),
        ("batch", "batch_malformed_member", key, ("bad",), POLICY_VALUE),
        ("batch", "batch_unsorted", key, (high, low), POLICY_VALUE),
        ("batch", "batch_duplicate_members", key, (other, other), POLICY_VALUE),
        ("batch", "batch_empty_valid", key, (), POLICY_VALUE),
        ("batch", "batch_one_unrelated", key, (other,), POLICY_VALUE),
        ("batch", "batch_one_matching", key, (key,), POLICY_VALUE),
        ("batch", "batch_multiple_contains", key, (low, key, high), POLICY_VALUE),
        ("outcome_state", "canonical_unique_passed", key, (other,), POLICY_VALUE),
        ("outcome_state", "canonical_duplicate_blocked", key, (key,), POLICY_VALUE),
        ("outcome_state", "policy_invalid_retains_pair", key, (), "wrong"),
        ("outcome_state", "batch_invalid_retains_pair", key, [key], POLICY_VALUE),
    )


def _expected_truth_rows() -> list[dict[str, str]]:
    _, predecessor_rows = _csv(REPO_ROOT / PREDECESSOR_TRUTH_PATH)
    rows = [
        {
            **row,
            "case_id": f"EXACT8_{row['case_id']}",
            "case_group": "predecessor_exact8_truth",
        }
        for row in predecessor_rows
    ]
    rows.append(_expected_row(
        "GLOBAL_rule_id_exact_str", "global_dispatch", "",
        "non_exact_str_type_error",
        _error("UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", known=False, callable_discovered=False, adapter_ready=False),
    ))
    rows.append(_expected_row(
        "GLOBAL_unknown_rule", "global_dispatch", "ADMIT_999",
        "unknown_rule_error",
        _error("UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", known=False, callable_discovered=False, adapter_ready=False),
    ))
    for rule_id in KNOWN_RULE_IDS[9:]:
        rows.append(_expected_row(
            f"GLOBAL_{rule_id}_not_registered", "global_dispatch", rule_id,
            "known_rule_not_registered",
            _error("UNIFIED_ADMISSION_RULE_NOT_REGISTERED", rule_id, "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", known=True, callable_discovered=False, adapter_ready=False),
        ))
    rows.append(_expected_row(
        "GLOBAL_predecessor_admit009_unchanged", "global_dispatch", "ADMIT_009",
        "Exact8_still_not_registered",
        _error("UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "ADMIT_009", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", known=True, callable_discovered=False, adapter_ready=False),
    ))
    missing = _candidate_invalid("duplicate_identity_key_missing")
    for rule_id in KNOWN_RULE_IDS[:8]:
        rows.append(_expected_row(
            f"IDENTITY_{rule_id}", "predecessor_handler_identity", rule_id,
            "exact_predecessor_handler_object_identity", missing,
            identity="predecessor_object_identity",
        ))
    for _, case_id, scalar, batch, policy in _truth_definitions():
        rows.append(_expected_row(
            f"A009_EXACT32_{case_id}", "admit009_standalone_exact32", "ADMIT_009",
            "standalone_exact10_to_unified_exact13",
            _project(_classify(scalar, batch, policy)), formal=1, oracle=1,
            access="single_required_lookup",
        ))
    context_cases = (
        ("batch_mapping", "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
        ("batch_key", "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED"),
        ("evaluation_mapping", "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("evaluation_key", "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED"),
        ("download_none", "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("stage_none", "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("precedence", "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
        ("candidate_bomb", "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
    )
    for case_id, reason in context_cases:
        rows.append(_expected_row(
            f"A009_CONTEXT_{case_id}", "admit009_context_routing", "ADMIT_009",
            "context_failure_before_candidate_formal_oracle",
            _error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "ADMIT_009", reason, known=True, callable_discovered=True, adapter_ready=True),
            access="not_accessed",
        ))
    rows.append(_expected_row(
        "A009_CANDIDATE_non_mapping", "admit009_candidate_and_lookup", "ADMIT_009",
        "adapter_generated_invalid_without_formal_oracle",
        _candidate_invalid("ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID"),
        access="envelope_or_single_lookup",
    ))
    rows.append(_expected_row(
        "A009_CANDIDATE_key_missing", "admit009_candidate_and_lookup", "ADMIT_009",
        "adapter_generated_invalid_without_formal_oracle", missing,
        access="envelope_or_single_lookup",
    ))
    key = KEY_PREFIX + "1" * 64
    passed = _project(_classify(key, (), POLICY_VALUE))
    rows.append(_expected_row(
        "A009_LOOKUP_single_and_mapping_subclass", "admit009_candidate_and_lookup", "ADMIT_009",
        "mapping_subclasses_single_direct_lookup_no_iteration", passed,
        formal=1, oracle=1, access="single_required_lookup",
    ))
    for case_id in (
        "batch_non_key_error", "policy_non_key_error", "candidate_non_key_error",
    ):
        rows.append(_expected_row(
            f"A009_LOOKUP_{case_id}", "admit009_candidate_and_lookup", "ADMIT_009",
            "non_KeyError_propagated_unchanged", missing,
            access="exception_propagated",
        ))
    scalar_invalid = _project(_classify(object(), object(), object()))
    for case_id in (
        "formal_exactly_once", "oracle_exactly_once", "three_object_identity",
        "lookup_and_no_copy",
    ):
        rows.append(_expected_row(
            f"A009_CALL_{case_id}", "admit009_call_identity", "ADMIT_009",
            "original_objects_positional_and_exactly_once", scalar_invalid,
            formal=1, oracle=1, access="single_required_lookup",
        ))
    source_cases = (
        ("wrong_type", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", 0),
        ("subclass", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", 0),
        ("storage_order", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 0),
        ("reconstruction_invariant", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 0),
        ("oracle_mapping_invalid", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1),
        ("oracle_key_missing", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1),
        ("full_exact10_mismatch", "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1),
    )
    for case_id, reason, oracle_calls in source_cases:
        rows.append(_expected_row(
            f"A009_SOURCE_{case_id}", "admit009_source_oracle", "ADMIT_009",
            "fail_closed_no_partial_exact13",
            _error("UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "ADMIT_009", reason, known=True, callable_discovered=True, adapter_ready=False),
            formal=1, oracle=oracle_calls, access="single_required_lookup",
        ))
    for case_id in (
        "dispatcher_new_object", "dispatcher_signature_equal",
        "dispatcher_local_registry", "predecessor_registry_distinct",
        "registry_exact9", "admit009_new_handler", "coverage_starts_admit010",
        "provider_mapping_false", "provider_key_count_zero", "admit010_not_started",
        "evaluate_all_rules_absent", "combined_verdict_absent",
    ):
        rows.append(_expected_row(
            f"BOUNDARY_{case_id}", "registry_issue_boundary", "ADMIT_009",
            "successor_and_stop_boundary", missing,
        ))
    if Counter(row["case_group"] for row in rows) != TRUTH_GROUP_COUNTS:
        raise AssertionError("checker truth group definitions drifted")
    return rows


def _contract_definitions() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("TYPE_001", "public_identity", "result type identity", "true"),
        ("TYPE_002", "public_identity", "dispatch error type identity", "true"),
        ("TYPE_003", "public_identity", "result schema identity", "true"),
        ("TYPE_004", "public_identity", "Exact13 field identity", "true"),
        ("TYPE_005", "public_identity", "Exact6 field identity", "true"),
        ("TYPE_006", "public_identity", "dispatch code identity", "true"),
        ("TYPE_007", "public_identity", "outcome vocabulary identity", "true"),
        ("DISPATCH_001", "dispatcher", "new successor function object", "true"),
        ("DISPATCH_002", "dispatcher", "Exact8 signature equality", "true"),
        ("DISPATCH_003", "dispatcher", "local Exact9 registry binding", "true"),
        ("DISPATCH_004", "dispatcher", "exact built-in str precedence", "first"),
        ("DISPATCH_005", "dispatcher", "known rule precedence", "second"),
        ("DISPATCH_006", "dispatcher", "registered readiness precedence", "third"),
        ("DISPATCH_007", "dispatcher", "local handler call precedence", "fourth"),
        ("REGISTRY_001", "registry", "MappingProxyType", "true"),
        ("REGISTRY_002", "registry", "exact registered order", "ADMIT_001_to_ADMIT_009"),
        ("REGISTRY_003", "registry", "first eight handler identity", "8/8"),
        ("REGISTRY_004", "registry", "sole new handler", "_evaluate_registered_admit_009"),
        ("REGISTRY_005", "registry", "known IDs", "ADMIT_001_to_ADMIT_015"),
        ("REGISTRY_006", "registry", "callable IDs", "ADMIT_001_to_ADMIT_009"),
        ("REGISTRY_007", "registry", "adapter-ready IDs", "ADMIT_001_to_ADMIT_009"),
        ("REGISTRY_008", "registry", "legacy not ready IDs", "empty"),
        ("IDENTITY_001", "admit009_identity", "rule ID", "ADMIT_009"),
        ("IDENTITY_002", "admit009_identity", "rule name", "duplicate_identity_precheck"),
        ("IDENTITY_003", "admit009_identity", "adapter ID", "covapie_admit_009_unified_adapter_v1"),
        ("IDENTITY_004", "admit009_identity", "candidate field", "duplicate_identity_key"),
        ("IDENTITY_005", "admit009_identity", "canonical context order", "policy_then_batch"),
        ("ROUTING_001", "context_routing", "batch Mapping validation", "first"),
        ("ROUTING_002", "context_routing", "batch required direct lookup", "second"),
        ("ROUTING_003", "context_routing", "evaluation Mapping validation", "third"),
        ("ROUTING_004", "context_routing", "policy required direct lookup", "fourth"),
        ("ROUTING_005", "context_routing", "download must be None", "fifth"),
        ("ROUTING_006", "context_routing", "stage must be None", "sixth"),
        ("ROUTING_007", "context_routing", "all context before candidate", "true"),
        ("ROUTING_008", "context_routing", "Mapping subclasses", "accepted"),
        ("ROUTING_009", "context_routing", "required lookup", "once_direct"),
        ("ROUTING_010", "context_routing", "only KeyError means missing", "true"),
        ("CANDIDATE_001", "candidate", "Mapping validation after contexts", "true"),
        ("CANDIDATE_002", "candidate", "non-Mapping", "Exact13_invalid"),
        ("CANDIDATE_003", "candidate", "absent key", "duplicate_identity_key_missing"),
        ("CANDIDATE_004", "candidate", "present values", "forwarded_unchanged"),
        ("CANDIDATE_005", "candidate", "invalid formal calls", "0"),
        ("CANDIDATE_006", "candidate", "invalid oracle calls", "0"),
        ("CALL_001", "formal", "formal function", "evaluate_admit_009"),
        ("CALL_002", "formal", "formal call count", "1"),
        ("CALL_003", "formal", "formal positional order", "scalar_batch_policy"),
        ("CALL_004", "formal", "original object identity", "3/3"),
        ("CALL_005", "formal", "adapter normalization", "false"),
        ("SOURCE_001", "source", "exact committed result type", "required"),
        ("SOURCE_002", "source", "subclass", "rejected"),
        ("SOURCE_003", "source", "vars storage", "exact_dict"),
        ("SOURCE_004", "source", "storage field order", "Exact10"),
        ("SOURCE_005", "source", "dataclass field order", "Exact10"),
        ("SOURCE_006", "source", "all ordered field reads", "Exact10"),
        ("SOURCE_007", "source", "committed reconstruction", "required"),
        ("SOURCE_008", "source", "full reconstruction equality", "required"),
        ("SOURCE_009", "source", "committed post-init invariants", "required"),
        ("SOURCE_010", "source", "failure oracle call count", "0"),
        ("ORACLE_001", "oracle", "committed independent oracle", "duplicate_identity_key_design"),
        ("ORACLE_002", "oracle", "Mapping classification", "required"),
        ("ORACLE_003", "oracle", "oracle call count", "1"),
        ("ORACLE_004", "oracle", "same positional objects", "3/3"),
        ("ORACLE_005", "oracle", "complete committed Exact10 construction", "true"),
        ("ORACLE_006", "oracle", "full Exact10 equality", "required"),
        ("ORACLE_007", "oracle", "partial equality", "forbidden"),
        ("PROJECTION_001", "projection", "schema", RESULT_SCHEMA_VERSION),
        ("PROJECTION_002", "projection", "normalized values", "source.validated_candidate_fields"),
        ("PROJECTION_003", "projection", "validated fields", "source.validated_candidate_fields"),
        ("PROJECTION_004", "projection", "passed", "preserved"),
        ("PROJECTION_005", "projection", "blocked", "preserved"),
        ("PROJECTION_006", "projection", "scalar invalid", "preserved"),
        ("PROJECTION_007", "projection", "policy invalid", "preserved"),
        ("PROJECTION_008", "projection", "batch invalid", "preserved"),
        ("BOUNDARY_001", "boundary", "provider mapping", "false"),
        ("BOUNDARY_002", "boundary", "real provider keys", "0"),
        ("BOUNDARY_003", "boundary", "ADMIT_010", "not_started"),
        ("BOUNDARY_004", "boundary", "evaluate_all_rules", "absent"),
        ("BOUNDARY_005", "boundary", "combined verdict", "absent"),
        ("BOUNDARY_006", "boundary", "training", "forbidden"),
    )


def _expected_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_id": contract_id,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for contract_id, area, statement, expected in _contract_definitions()
    ]


def _expected_registry_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in REGISTERED_RULE_IDS
        identity = (
            "predecessor_object_identity"
            if rule_id in KNOWN_RULE_IDS[:8]
            else "exact_new_admit009_handler"
            if rule_id == "ADMIT_009"
            else "not_registered"
        )
        rows.append({
            "rule_id": rule_id,
            "rule_name": RULE_NAMES.get(rule_id, ""),
            "known_rule": "true",
            "callable_discovered": str(registered).lower(),
            "adapter_ready": str(registered).lower(),
            "registered": str(registered).lower(),
            "adapter_id": ADAPTER_IDS.get(rule_id, ""),
            "handler_identity_status": identity,
            "dispatch_disposition": "registered_local_handler" if registered else "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "audit_passed": "true",
        })
    return rows


EXECUTED_SAFETY_ITEMS = (
    "successor_runtime_implementation", "admit009_adapter_implementation",
    "admit009_registry_extension", "exact8_identity_reuse",
    "standalone_formal_call", "committed_oracle_call",
    "exact10_source_validation", "exact10_oracle_equality", "exact13_projection",
    "deterministic_materialization", "source_boundary_verification",
    "issue_successor_transition", "targeted_tests", "checker",
    "validation_incident_documented_and_contained",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "exact8_runtime_modification", "adapter_design_runtime_import",
    "provider_mapping", "provider_key_generation", "real_candidate_evaluation",
    "admit010", "evaluate_all_rules", "combined_candidate_verdict",
    "cross_rule_precedence", "exact9_runtime_or_materializer_raw_read",
    "network", "download",
    "checkpoint_read", "torch", "numpy", "rdkit", "model_code",
    "model_forward", "model_loss", "backward", "optimizer_step", "training",
    "fine_tune", "parameter_update", "stage", "commit", "push", "gh",
)

VALIDATION_INCIDENT = {
    "incident_id": "legacy_real_provider_checker_raw_read_and_historical_rematerialization",
    "incident_occurred": True,
    "workflow_instruction_violation_occurred": True,
    "incident_scope": "validation_command_outside_exact9_public_runtime_and_exact9_materializer",
    "existing_raw_read_occurred": True,
    "network_or_download_occurred": False,
    "temporary_tracked_modification_count": 8,
    "temporary_changes_restored_to_head": True,
    "residual_tracked_diff_count": 0,
    "residual_staged_diff_count": 0,
    "post_restoration_validation_rerun": True,
    "incident_contained": True,
}


def _expected_safety_rows() -> list[dict[str, str]]:
    definitions = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple(
        (item, False) for item in NOT_EXECUTED_SAFETY_ITEMS
    )
    return [
        {
            "safety_item": item,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "safety_passed": "true",
        }
        for item, executed in definitions
    ]


def _expected_issue_rows() -> list[dict[str, str]]:
    header, rows = _csv(REPO_ROOT / DESIGN_ISSUE_PATH)
    if header != ISSUE_HEADER or len(rows) != 11:
        raise AssertionError("authoritative issue source changed")
    matches = [
        row for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(matches) != 1:
        raise AssertionError("coverage issue missing or duplicate")
    matches[0]["affected_rules"] = "|".join(KNOWN_RULE_IDS[9:])
    matches[0]["integration_transition"] = (
        "admit_009_implemented_and_removed_from_open_coverage_scope"
    )
    return rows


def _expected_manifest() -> dict[str, object]:
    readiness = _readiness()
    paths = [path for path, _ in SOURCE_BOUNDARY]
    source_sha = {path: digest for path, digest in SOURCE_BOUNDARY}
    payload: dict[str, object] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "exact9_identity": "ADMIT_001_to_ADMIT_009_unified_single_rule_runtime_v1",
        "exact8_predecessor_identity": "ADMIT_001_to_ADMIT_008_unified_single_rule_runtime_v1",
        "source_boundary_name": SOURCE_BOUNDARY_NAME,
        "source_input_count": 18,
        "source_input_paths": paths,
        "source_input_sha256": source_sha,
        "source_input_verification": [
            {
                "source_ordinal": index,
                "source_relative_path": path,
                "tracked": True,
                "base_tree_blob": True,
                "filesystem_regular": True,
                "non_symlink": True,
                "safe_descendant": True,
                "expected_sha256": digest,
                "base_tree_sha256": digest,
                "filesystem_sha256": digest,
                "source_verified": True,
            }
            for index, (path, digest) in enumerate(SOURCE_BOUNDARY, 1)
        ],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "runtime_dependency_imports": [
            "exact8_unified_runtime_predecessor",
            "admit009_standalone_evaluator",
            "admit009_committed_independent_duplicate_key_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
        "public_type_and_constant_identity": {
            "UnifiedAdmissionRuleEvaluation": True,
            "UnifiedAdmissionDispatchError": True,
            "RESULT_SCHEMA_VERSION": True,
            "RESULT_FIELDS": True,
            "DISPATCH_ERROR_FIELDS": True,
            "DISPATCH_ERROR_CODES": True,
            "OUTCOME_VOCABULARY": True,
        },
        "public_dispatch_new_successor_function": True,
        "public_dispatch_signature": PUBLIC_SIGNATURE,
        "public_dispatch_signature_matches_exact8": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str", "known_rule", "registered_adapter_ready",
            "local_registry_handler",
        ],
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(ERROR_FIELDS),
        "dispatch_error_codes": list(ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(REGISTERED_RULE_IDS),
        "adapter_ready_rule_ids": list(REGISTERED_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(REGISTERED_RULE_IDS),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[9:]),
        "registered_rule_count": 9,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_eight_handler_identity_reused": {
            rule_id: True for rule_id in KNOWN_RULE_IDS[:8]
        },
        "admit_009_handler": "_evaluate_registered_admit_009",
        "admit_009_handler_identity": "exact_new_admit009_handler",
        "admit_009_candidate_fields": list(CANDIDATE_FIELDS),
        "admit_009_context_items": list(CONTEXT_ITEMS),
        "admit_009_context_validation_order": [
            "batch_context_mapping_validation",
            "batch_duplicate_identity_keys_required_key_lookup",
            "evaluation_context_mapping_validation",
            "duplicate_identity_key_contract_required_key_lookup",
            "download_result_context_must_be_none",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "duplicate_identity_key_required_key_lookup",
            "formal_evaluator", "source_validation", "independent_oracle",
            "full_exact10_equality", "exact13_projection",
        ],
        "admit_009_context_reasons": {
            "batch_context": "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED",
            "batch_required_key": "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED",
            "evaluation_context": "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "policy_required_key": "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED",
            "download_result_context": "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_009_candidate_mapping_invalid_reason": "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_009_missing_reason": "duplicate_identity_key_missing",
        "admit_009_required_lookup": "single_direct_lookup_KeyError_only",
        "admit_009_present_values_forwarded_unchanged": True,
        "admit_009_formal_evaluator": "evaluate_admit_009",
        "admit_009_formal_positional_argument_order": [
            "scalar_object", "batch_duplicate_identity_keys_object",
            "duplicate_identity_key_contract_object",
        ],
        "admit_009_formal_call_count": 1,
        "admit_009_adapter_normalization": False,
        "admit_009_source_type": "Admit009EvaluationResult",
        "admit_009_source_fields": list(SOURCE_FIELDS),
        "admit_009_source_type_invalid_reason": "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "admit_009_source_invariant_invalid_reason": "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "admit_009_source_prevalidation_before_oracle": True,
        "admit_009_source_full_exact10_invariant_validation": True,
        "admit_009_oracle": "classify_admit_009_duplicate_identity_key_design",
        "admit_009_oracle_call_count": 1,
        "admit_009_source_oracle_full_exact10_equality_required": True,
        "admit_009_normalized_values_projection": "source.validated_candidate_fields",
        "admit_009_no_partial_exact13_on_failure": True,
        "standalone_exact32_projection_count": 32,
        "contract_row_count": 79,
        "contract_pass_count": 79,
        "truth_matrix_row_count": 289,
        "truth_matrix_pass_count": 289,
        "truth_matrix_group_counts": dict(TRUTH_GROUP_COUNTS),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "safety_audit_row_count": 43,
        "safety_audit_pass_count": 43,
        "issue_inventory_row_count": 11,
        "issue_transition_count": 1,
        "issue_transition_id": "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "issue_transition": "admit_009_implemented_and_removed_from_open_coverage_scope",
        "issue_coverage_after": list(KNOWN_RULE_IDS[9:]),
        "issue_authoritative_predecessor_sha256": DESIGN_ISSUE_SHA256,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(MANIFEST_OUTPUT_SHA256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "provider_fields_consumed": [],
        "real_provider_duplicate_identity_key_count": 0,
        "real_provider_duplicate_identity_mapping_executed": False,
        "exact8_runtime_modified": False,
        "admit_010_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "validation_incident": dict(VALIDATION_INCIDENT),
        "stop_boundaries": [
            "no_admit_010", "no_provider_mapping", "no_real_candidate_evaluation",
            "no_evaluate_all_rules", "no_combined_candidate_verdict",
            "no_raw_read_by_exact9_public_runtime_or_exact9_materializer",
            "no_network_or_download", "no_model_forward_loss_training",
        ],
        "readiness_true_count": len(TRUE_READINESS),
        "readiness_false_count": len(FALSE_READINESS),
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
        "recommended_next_step": NEXT_STEP,
        "manifest_top_level_key_count": 0,
    }
    payload["manifest_top_level_key_count"] = len(payload)
    return payload


PROTECTED_BUILDERS = {
    "_readiness", "_canonical_key", "_classify", "_project",
    "_candidate_invalid", "_error", "_truth_definitions",
    "_expected_truth_rows", "_contract_definitions", "_expected_contract_rows",
    "_expected_registry_rows", "_expected_safety_rows", "_expected_issue_rows",
    "_expected_manifest",
}


def _assert_checker_independent_ast(source_text: str | None = None) -> None:
    tree = ast.parse(
        Path(__file__).read_text(encoding="utf-8")
        if source_text is None
        else source_text
    )
    forbidden_roots = {
        "runtime", "predecessor", "admit009", "admit009_oracle", "design_gate",
    }
    forbidden_attributes = {
        "_contract_rows", "_truth_rows", "_registry_rows", "_safety_rows",
        "EVALUATOR_REGISTRY", "evaluate_admit_009",
        "classify_admit_009_duplicate_identity_key_design",
        "SOURCE_PATHS", "SOURCE_SHA256", "CONTRACT_COLUMNS", "TRUTH_COLUMNS",
        "REGISTRY_COLUMNS", "SAFETY_COLUMNS", "ISSUE_COLUMNS", "OUTPUT_FILES",
        "TRUE_READINESS", "FALSE_READINESS", "ADAPTER_IDS", "RESULT_FIELDS",
        "_manifest_payload", "build_runtime_state",
    }
    seen: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in PROTECTED_BUILDERS:
            seen.add(node.name)
            names = {
                child.id for child in ast.walk(node) if isinstance(child, ast.Name)
            }
            attributes = {
                child.attr for child in ast.walk(node)
                if isinstance(child, ast.Attribute)
            }
            if names & forbidden_roots or attributes & forbidden_attributes:
                raise AssertionError(
                    f"checker semantic builder depends on production: {node.name}"
                )
    if source_text is None and seen != PROTECTED_BUILDERS:
        raise AssertionError("checker protected builder inventory changed")


def _assert_error(call: Any, code: str, reason: str):
    try:
        call()
    except runtime.UnifiedAdmissionDispatchError as error:
        if error.code != code or error.reason != reason:
            raise AssertionError("dispatch error mismatch")
        return error
    raise AssertionError("dispatch did not fail closed")


def _check_production_alignment() -> None:
    checks = (
        runtime.PROJECT == PROJECT,
        runtime.STEP == STEP,
        runtime.STAGE == STAGE,
        runtime.EXPECTED_BASE_COMMIT == EXPECTED_BASE_COMMIT,
        runtime.EXPECTED_BASE_SUBJECT == EXPECTED_BASE_SUBJECT,
        runtime.MANIFEST_SCHEMA_VERSION == MANIFEST_SCHEMA_VERSION,
        runtime.RECOMMENDED_NEXT_STEP == NEXT_STEP,
        runtime.SOURCE_PATHS == tuple(Path(path) for path, _ in SOURCE_BOUNDARY),
        runtime.SOURCE_SHA256 == {Path(path): digest for path, digest in SOURCE_BOUNDARY},
        runtime.OUTPUT_FILES == OUTPUT_FILES,
        runtime.CSV_OUTPUTS == CSV_OUTPUTS,
        runtime.RESULT_FIELDS == RESULT_FIELDS,
        runtime.DISPATCH_ERROR_FIELDS == ERROR_FIELDS,
        runtime.DISPATCH_ERROR_CODES == ERROR_CODES,
        runtime.OUTCOME_VOCABULARY == OUTCOME_VOCABULARY,
        runtime.KNOWN_RULE_IDS == KNOWN_RULE_IDS,
        runtime.CALLABLE_DISCOVERED_RULE_IDS == REGISTERED_RULE_IDS,
        runtime.ADAPTER_READY_RULE_IDS == REGISTERED_RULE_IDS,
        runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == (),
        dict(runtime.RULE_NAMES) == RULE_NAMES,
        dict(runtime.ADAPTER_IDS) == ADAPTER_IDS,
        tuple(runtime.TRUE_READINESS) == TRUE_READINESS,
        tuple(runtime.FALSE_READINESS) == FALSE_READINESS,
        runtime.VALIDATION_INCIDENT == VALIDATION_INCIDENT,
    )
    if not all(checks):
        raise AssertionError("production constants differ from checker contract")
    observed_headers = {
        runtime.CONTRACT_FILENAME: runtime.CONTRACT_COLUMNS,
        runtime.TRUTH_FILENAME: runtime.TRUTH_COLUMNS,
        runtime.REGISTRY_FILENAME: runtime.REGISTRY_COLUMNS,
        runtime.SAFETY_FILENAME: runtime.SAFETY_COLUMNS,
        runtime.ISSUE_FILENAME: runtime.ISSUE_COLUMNS,
    }
    if observed_headers != HEADERS:
        raise AssertionError("production CSV headers changed")


class _SingleLookup(Mapping[str, object]):
    def __init__(
        self, key: str, value: object, *, present: bool = True,
        failure: Exception | None = None,
    ) -> None:
        self.key = key
        self.value = value
        self.present = present
        self.failure = failure
        self.lookups = 0

    def __getitem__(self, key: str) -> object:
        if key != self.key:
            raise KeyError(key)
        self.lookups += 1
        if self.lookups > 1:
            raise AssertionError("required key read more than once")
        if self.failure is not None:
            raise self.failure
        if not self.present:
            raise KeyError(key)
        return self.value

    def __iter__(self):
        raise AssertionError("Mapping iterated")

    def __len__(self) -> int:
        raise AssertionError("Mapping sized")


class _Bomb(Mapping[str, object]):
    accesses = 0

    def __getitem__(self, key: str) -> object:
        self.accesses += 1
        raise AssertionError("candidate accessed")

    def __iter__(self):
        self.accesses += 1
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        self.accesses += 1
        raise AssertionError("candidate sized")


def _check_runtime_directly() -> None:
    predecessor = runtime.predecessor
    if runtime.evaluate_admission_rule is predecessor.evaluate_admission_rule:
        raise AssertionError("successor dispatcher reused predecessor object")
    if inspect.signature(runtime.evaluate_admission_rule) != inspect.signature(
        predecessor.evaluate_admission_rule
    ):
        raise AssertionError("public signature changed")
    if runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is not runtime.EVALUATOR_REGISTRY:
        raise AssertionError("successor dispatcher does not use local registry")
    if runtime.EVALUATOR_REGISTRY is predecessor.EVALUATOR_REGISTRY:
        raise AssertionError("predecessor registry reused or modified")
    if (
        runtime.UnifiedAdmissionRuleEvaluation is not predecessor.UnifiedAdmissionRuleEvaluation
        or runtime.UnifiedAdmissionDispatchError is not predecessor.UnifiedAdmissionDispatchError
    ):
        raise AssertionError("public type identity changed")
    for name in (
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        if getattr(runtime, name) is not getattr(predecessor, name):
            raise AssertionError(f"public constant identity changed: {name}")
    if type(runtime.RULE_NAMES) is not MappingProxyType:
        raise AssertionError("rule names are mutable")
    if type(runtime.ADAPTER_IDS) is not MappingProxyType:
        raise AssertionError("adapter IDs are mutable")
    if type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType:
        raise AssertionError("registry is mutable")
    if tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_RULE_IDS:
        raise AssertionError("registry order changed")
    if tuple(predecessor.EVALUATOR_REGISTRY) != KNOWN_RULE_IDS[:8]:
        raise AssertionError("predecessor registry was modified")
    for rule_id in KNOWN_RULE_IDS[:8]:
        if runtime.EVALUATOR_REGISTRY[rule_id] is not predecessor.EVALUATOR_REGISTRY[rule_id]:
            raise AssertionError(f"predecessor handler wrapped: {rule_id}")
    if runtime.EVALUATOR_REGISTRY["ADMIT_009"] is not runtime._evaluate_registered_admit_009:
        raise AssertionError("ADMIT_009 handler identity changed")
    if hasattr(runtime, "evaluate_all_rules") or hasattr(runtime, "combined_candidate_verdict"):
        raise AssertionError("aggregation boundary expanded")

    class Text(str):
        pass

    error = _assert_error(
        lambda: runtime.evaluate_admission_rule(Text("ADMIT_009"), {}),
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    )
    if (error.known_rule, error.callable_discovered, error.adapter_ready) != (False, False, False):
        raise AssertionError("rule-id exact-type flags changed")
    _assert_error(
        lambda: runtime.evaluate_admission_rule("ADMIT_999", {}),
        "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
        "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    )
    for rule_id in KNOWN_RULE_IDS[9:]:
        error = _assert_error(
            lambda rule_id=rule_id: runtime.evaluate_admission_rule(rule_id, {}),
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        )
        if (error.known_rule, error.callable_discovered, error.adapter_ready) != (True, False, False):
            raise AssertionError("known-not-registered flags changed")
    _assert_error(
        lambda: predecessor.evaluate_admission_rule("ADMIT_009", {}),
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    )

    bomb = _Bomb()
    with (
        patch.object(admit009, "evaluate_admit_009", side_effect=AssertionError("formal called")),
        patch.object(admit009_oracle, "classify_admit_009_duplicate_identity_key_design", side_effect=AssertionError("oracle called")),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_009", bomb, batch_context=None,
                evaluation_context={"duplicate_identity_key_contract": POLICY_VALUE},
            ),
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED",
        )
    if error.adapter_ready is not True or bomb.accesses:
        raise AssertionError("context failure reached candidate or adapter")

    scalar = object()
    batch = object()
    policy = object()
    candidate = _SingleLookup("duplicate_identity_key", scalar)
    batch_context = _SingleLookup("batch_duplicate_identity_keys", batch)
    evaluation_context = _SingleLookup("duplicate_identity_key_contract", policy)
    formal_result = admit009.evaluate_admit_009(scalar, batch, policy)
    oracle_result = admit009_oracle.classify_admit_009_duplicate_identity_key_design(scalar, batch, policy)
    calls: list[tuple[str, tuple[object, ...]]] = []
    with (
        patch.object(admit009, "evaluate_admit_009", lambda *args: calls.append(("formal", args)) or formal_result),
        patch.object(admit009_oracle, "classify_admit_009_duplicate_identity_key_design", lambda *args: calls.append(("oracle", args)) or oracle_result),
    ):
        result = runtime.evaluate_admission_rule(
            "ADMIT_009", candidate, batch_context=batch_context,
            evaluation_context=evaluation_context,
        )
    if result.reason != SCALAR_REASONS[0]:
        raise AssertionError("opaque scalar forwarding changed")
    if (candidate.lookups, batch_context.lookups, evaluation_context.lookups) != (1, 1, 1):
        raise AssertionError("required lookup count changed")
    if [name for name, _ in calls] != ["formal", "oracle"]:
        raise AssertionError("formal/oracle order or count changed")
    for _, args in calls:
        if not (args[0] is scalar and args[1] is batch and args[2] is policy):
            raise AssertionError("original object identity lost")

    for position in ("batch", "policy", "candidate"):
        sentinel = RuntimeError(f"{position} sentinel")
        candidate_value: object = {"duplicate_identity_key": KEY_PREFIX + "1" * 64}
        batch_value: object = {"batch_duplicate_identity_keys": ()}
        policy_value: object = {"duplicate_identity_key_contract": POLICY_VALUE}
        if position == "batch":
            batch_value = _SingleLookup("batch_duplicate_identity_keys", (), failure=sentinel)
        elif position == "policy":
            policy_value = _SingleLookup("duplicate_identity_key_contract", POLICY_VALUE, failure=sentinel)
        else:
            candidate_value = _SingleLookup("duplicate_identity_key", KEY_PREFIX + "1" * 64, failure=sentinel)
        try:
            runtime.evaluate_admission_rule(
                "ADMIT_009", candidate_value, batch_context=batch_value,
                evaluation_context=policy_value,
            )
        except RuntimeError as caught:
            if caught is not sentinel:
                raise AssertionError("non-KeyError exception identity changed")
        else:
            raise AssertionError("non-KeyError folded into missing")

    missing = _SingleLookup("duplicate_identity_key", object(), present=False)
    with (
        patch.object(admit009, "evaluate_admit_009", side_effect=AssertionError("formal called")),
        patch.object(admit009_oracle, "classify_admit_009_duplicate_identity_key_design", side_effect=AssertionError("oracle called")),
    ):
        missing_result = runtime.evaluate_admission_rule(
            "ADMIT_009", missing,
            batch_context={"batch_duplicate_identity_keys": ()},
            evaluation_context={"duplicate_identity_key_contract": POLICY_VALUE},
        )
    if missing.lookups != 1 or missing_result.reason != "duplicate_identity_key_missing":
        raise AssertionError("candidate missing contract changed")
    if (
        missing_result.blocks_candidate is not True
        or missing_result.consumed_context_items != CONTEXT_ITEMS
        or missing_result.adapter_id != "covapie_admit_009_unified_adapter_v1"
    ):
        raise AssertionError("candidate invalid Exact13 changed")

    for _, _, scalar_value, batch_value, policy_value in _truth_definitions():
        expected = _project(_classify(scalar_value, batch_value, policy_value))
        observed = runtime.evaluate_admission_rule(
            "ADMIT_009", {"duplicate_identity_key": scalar_value},
            batch_context={"batch_duplicate_identity_keys": batch_value},
            evaluation_context={"duplicate_identity_key_contract": policy_value},
        )
        if {name: getattr(observed, name) for name in RESULT_FIELDS} != expected:
            raise AssertionError("Exact32 projection changed")

    corrupt = admit009.evaluate_admit_009(None, (), POLICY_VALUE)
    object.__setattr__(corrupt, "blocks_candidate", False)
    counts = Counter()
    with (
        patch.object(admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or corrupt),
        patch.object(admit009_oracle, "classify_admit_009_duplicate_identity_key_design", lambda *args: counts.update(["oracle"])),
        patch.object(runtime, "_project_admit009_exact13", side_effect=AssertionError("projected")),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_009", {"duplicate_identity_key": None},
                batch_context={"batch_duplicate_identity_keys": ()},
                evaluation_context={"duplicate_identity_key_contract": POLICY_VALUE},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    if error.adapter_ready is not False or counts != {"formal": 1}:
        raise AssertionError("source validation did not prevent oracle")

    key = KEY_PREFIX + "1" * 64
    valid = admit009.evaluate_admit_009(key, (), POLICY_VALUE)
    mismatch = admit009_oracle.classify_admit_009_duplicate_identity_key_design(key, (key,), POLICY_VALUE)
    counts.clear()
    with (
        patch.object(admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or valid),
        patch.object(admit009_oracle, "classify_admit_009_duplicate_identity_key_design", lambda *args: counts.update(["oracle"]) or mismatch),
        patch.object(runtime, "_project_admit009_exact13", side_effect=AssertionError("projected")),
    ):
        _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_009", {"duplicate_identity_key": key},
                batch_context={"batch_duplicate_identity_keys": ()},
                evaluation_context={"duplicate_identity_key_contract": POLICY_VALUE},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    if counts != {"formal": 1, "oracle": 1}:
        raise AssertionError("full Exact10 mismatch call counts changed")


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _check_public_call_graph() -> None:
    path = Path(runtime.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    banned = {
        "build_runtime_state", "build_frozen_source_snapshot",
        "run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1",
        "_git", "open", "read", "read_bytes", "read_text", "write",
        "write_bytes", "write_text", "run", "Popen", "system", "urlopen",
    }
    pending = ["evaluate_admission_rule", "_evaluate_registered_admit_009"]
    closure: set[str] = set()
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        calls = _called_names(functions[name])
        if calls & banned:
            raise AssertionError(f"public runtime reaches metadata I/O: {calls & banned}")
        pending.extend(call for call in calls if call in functions)
    required = {
        "evaluate_admission_rule", "_raise_dispatch_error",
        "_evaluate_registered_admit_009", "_admit009_context_failure",
        "_admit009_candidate_invalid", "_prevalidate_admit009_source",
        "_expected_admit009_from_oracle", "_validate_admit009_oracle_equivalence",
        "_project_admit009_exact13", "_admit009_adapter_failure",
    }
    if not required <= closure:
        raise AssertionError("public runtime closure incomplete")
    import_section = source.split("PROJECT =", 1)[0]
    if "admit_009_unified_adapter_contract_design_gate" in import_section:
        raise AssertionError("adapter design gate imported by runtime")
    import_lines = [line for line in import_section.splitlines() if line.startswith("from covalent_ext import")]
    if len(import_lines) != 3:
        raise AssertionError("runtime dependency import count changed")
    for dependency in ("provider", "data.raw", "checkpoints", "torch", "numpy", "rdkit"):
        if dependency in import_section.lower():
            raise AssertionError(f"disallowed runtime dependency: {dependency}")


def _check_source_boundary() -> None:
    _check_production_alignment()
    if len(SOURCE_BOUNDARY) != 18 or len({path for path, _ in SOURCE_BOUNDARY}) != 18:
        raise AssertionError("checker Exact18 shape changed")
    subject = subprocess.run(
        ["git", "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT, capture_output=True, check=False,
    )
    if subject.returncode != 0 or subject.stdout.strip() != EXPECTED_BASE_SUBJECT or ancestor.returncode != 0:
        raise AssertionError("checker base lineage mismatch")

    structural: list[tuple[str, str]] = []
    for relative, expected_sha in SOURCE_BOUNDARY:
        path = Path(relative)
        absolute = REPO_ROOT / path
        if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints":
            raise AssertionError(f"unsafe source path: {relative}")
        metadata = os.lstat(absolute)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
        tree = subprocess.run(
            ["git", "ls-tree", EXPECTED_BASE_COMMIT, "--", relative],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        fields_value = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        try:
            absolute.resolve().relative_to(REPO_ROOT.resolve())
            descendant = True
        except ValueError:
            descendant = False
        if (
            tracked.returncode != 0 or tree.returncode != 0
            or len(fields_value) != 3 or fields_value[0] not in ("100644", "100755")
            or fields_value[1] != "blob" or not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode) or not descendant
        ):
            raise AssertionError(f"checker source structure mismatch: {relative}")
        structural.append((relative, expected_sha))
    if tuple(structural) != SOURCE_BOUNDARY:
        raise AssertionError("not all structures completed before reads")
    for relative, expected_sha in SOURCE_BOUNDARY:
        base = subprocess.run(
            ["git", "show", f"{EXPECTED_BASE_COMMIT}:{relative}"],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
        filesystem = (REPO_ROOT / relative).read_bytes()
        if (
            base.returncode != 0
            or hashlib.sha256(base.stdout).hexdigest() != expected_sha
            or hashlib.sha256(filesystem).hexdigest() != expected_sha
        ):
            raise AssertionError(f"checker source SHA mismatch: {relative}")


def _validate_manifest(manifest: object, root: Path) -> None:
    expected = _expected_manifest()
    if type(manifest) is not dict:
        raise AssertionError("manifest must be exact dict")
    if set(manifest) != set(expected):
        raise AssertionError("manifest key set mismatch")
    if manifest != expected:
        mismatch = sorted(key for key in expected if manifest[key] != expected[key])
        raise AssertionError(f"manifest semantic mismatch: {mismatch}")
    if manifest["manifest_top_level_key_count"] != len(manifest):
        raise AssertionError("manifest top-level count mismatch")
    for key, value in expected["readiness"].items():
        if manifest[key] is not value or manifest["readiness"][key] is not value:
            raise AssertionError(f"readiness mirror mismatch: {key}")
    for name, digest in expected["output_sha256"].items():
        if _sha256(root / name) != digest:
            raise AssertionError(f"manifest output SHA mismatch: {name}")


def _validate_output_root(
    root: Path, *, enforce_frozen_hashes: bool = True
) -> dict[str, int]:
    if not root.is_dir() or root.is_symlink():
        raise AssertionError("unsafe output root")
    if {path.name for path in root.iterdir()} != set(OUTPUT_FILES):
        raise AssertionError("output set mismatch")
    for name in OUTPUT_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise AssertionError(f"unsafe output entry: {name}")
    manifest = json.loads((root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    _validate_manifest(manifest, root)
    if enforce_frozen_hashes:
        for name, digest in EXPECTED_OUTPUT_SHA256.items():
            if _sha256(root / name) != digest:
                raise AssertionError(f"frozen output SHA mismatch: {name}")
    contract_header, contract_rows = _csv(root / CONTRACT_FILENAME)
    truth_header, truth_rows = _csv(root / TRUTH_FILENAME)
    registry_header, registry_rows = _csv(root / REGISTRY_FILENAME)
    safety_header, safety_rows = _csv(root / SAFETY_FILENAME)
    issue_header, issue_rows = _csv(root / ISSUE_FILENAME)
    if contract_header != CONTRACT_HEADER or contract_rows != _expected_contract_rows():
        raise AssertionError("Exact79 contract semantics mismatch")
    if truth_header != TRUTH_HEADER or truth_rows != _expected_truth_rows():
        raise AssertionError("Exact289 truth semantics mismatch")
    if registry_header != REGISTRY_HEADER or registry_rows != _expected_registry_rows():
        raise AssertionError("Exact15 registry semantics mismatch")
    if safety_header != SAFETY_HEADER or safety_rows != _expected_safety_rows():
        raise AssertionError("Exact43 safety semantics mismatch")
    if issue_header != ISSUE_HEADER or issue_rows != _expected_issue_rows():
        raise AssertionError("Exact11 issue semantics mismatch")
    issue_map = {row["issue_id"]: row for row in issue_rows}
    if (
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"] != "resolved"
        or issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["integration_transition"] != "duplicate_identity_key_contract_frozen_v1"
        or issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] != "open"
        or issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open"
    ):
        raise AssertionError("noncoverage issue state changed")
    return {
        "contract_rows": len(contract_rows),
        "truth_rows": len(truth_rows),
        "registry_rows": len(registry_rows),
        "safety_rows": len(safety_rows),
        "issue_rows": len(issue_rows),
    }


def _check_materialization() -> None:
    with tempfile.TemporaryDirectory(prefix="covapie-exact9-check-") as temporary:
        first = Path(temporary) / "first"
        second = Path(temporary) / "second"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1(first)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1(second)
        committed = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
        for name in OUTPUT_FILES:
            if (first / name).read_bytes() != (second / name).read_bytes():
                raise AssertionError(f"double materialization differs: {name}")
            if (first / name).read_bytes() != (committed / name).read_bytes():
                raise AssertionError(f"committed output differs: {name}")
        _validate_output_root(first)

        tampered = Path(temporary) / "tampered"
        shutil.copytree(first, tampered)
        path = tampered / CONTRACT_FILENAME
        header, rows = _csv(path)
        rows[0]["observed_value"] = "false"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path.write_text(stream.getvalue(), encoding="utf-8")
        manifest_path = tampered / MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["output_sha256"][CONTRACT_FILENAME] = _sha256(path)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            _validate_output_root(tampered, enforce_frozen_hashes=False)
        except AssertionError:
            pass
        else:
            raise AssertionError("synchronized semantic tamper accepted")

        incident_mutations = {
            "incident_occurred": lambda value: value.__setitem__(
                "incident_occurred", False
            ),
            "existing_raw_read_occurred": lambda value: value.__setitem__(
                "existing_raw_read_occurred", False
            ),
            "temporary_tracked_modification_count": lambda value: value.__setitem__(
                "temporary_tracked_modification_count", 0
            ),
            "temporary_changes_restored_to_head": lambda value: value.__setitem__(
                "temporary_changes_restored_to_head", False
            ),
            "incident_contained": lambda value: value.__setitem__(
                "incident_contained", False
            ),
        }
        for label, mutate in incident_mutations.items():
            candidate = Path(temporary) / f"incident-{label}"
            shutil.copytree(first, candidate)
            manifest_path = candidate / MANIFEST_FILENAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            mutate(manifest["validation_incident"])
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            try:
                _validate_output_root(candidate, enforce_frozen_hashes=False)
            except AssertionError:
                continue
            raise AssertionError(f"incident semantic tamper accepted: {label}")

        manifest_mutations = {
            "missing_incident": lambda value: value.pop("validation_incident"),
            "old_stop_boundary": lambda value: value.__setitem__(
                "stop_boundaries",
                [
                    boundary
                    for boundary in value["stop_boundaries"]
                    if boundary
                    not in {
                        "no_raw_read_by_exact9_public_runtime_or_exact9_materializer",
                        "no_network_or_download",
                    }
                ]
                + ["no_raw_network_download"],
            ),
            "unknown_key": lambda value: value.__setitem__("unknown", True),
            "readiness_mirror": lambda value: value["readiness"].__setitem__(
                "ready_for_training", True
            ),
        }
        for label, mutate in manifest_mutations.items():
            candidate = Path(temporary) / f"manifest-{label}"
            shutil.copytree(first, candidate)
            manifest_path = candidate / MANIFEST_FILENAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            mutate(manifest)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            try:
                _validate_output_root(candidate, enforce_frozen_hashes=False)
            except AssertionError:
                continue
            raise AssertionError(f"manifest semantic tamper accepted: {label}")

        safety_mutations = {
            "scoped_item_replaced_by_raw_read": lambda rows: rows[
                next(
                    index
                    for index, row in enumerate(rows)
                    if row["safety_item"]
                    == "exact9_runtime_or_materializer_raw_read"
                )
            ].__setitem__("safety_item", "raw_read"),
            "incident_item_deleted": lambda rows: rows.pop(
                next(
                    index
                    for index, row in enumerate(rows)
                    if row["safety_item"]
                    == "validation_incident_documented_and_contained"
                )
            ),
            "runtime_or_materializer_marked_raw_reading": lambda rows: rows[
                next(
                    index
                    for index, row in enumerate(rows)
                    if row["safety_item"]
                    == "exact9_runtime_or_materializer_raw_read"
                )
            ].__setitem__("observed_executed", "true"),
        }
        for label, mutate in safety_mutations.items():
            candidate = Path(temporary) / f"safety-{label}"
            shutil.copytree(first, candidate)
            safety_path = candidate / SAFETY_FILENAME
            header, rows = _csv(safety_path)
            mutate(rows)
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            safety_path.write_text(stream.getvalue(), encoding="utf-8")
            manifest_path = candidate / MANIFEST_FILENAME
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["output_sha256"][SAFETY_FILENAME] = _sha256(safety_path)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            try:
                _validate_output_root(candidate, enforce_frozen_hashes=False)
            except AssertionError:
                continue
            raise AssertionError(f"safety semantic tamper accepted: {label}")

        for mode in ("missing", "extra", "symlink"):
            candidate = Path(temporary) / mode
            shutil.copytree(first, candidate)
            if mode == "missing":
                (candidate / CONTRACT_FILENAME).unlink()
            elif mode == "extra":
                (candidate / "unexpected.txt").write_text("x", encoding="utf-8")
            else:
                victim = candidate / CONTRACT_FILENAME
                victim.unlink()
                victim.symlink_to(first / CONTRACT_FILENAME)
            try:
                _validate_output_root(candidate)
            except AssertionError:
                continue
            raise AssertionError(f"unsafe output accepted: {mode}")


def _silent_import(command: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(SRC_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout or completed.stderr:
        raise AssertionError("silent import contract failed")


def main() -> int:
    _assert_checker_independent_ast()
    _check_source_boundary()
    _check_public_call_graph()
    _check_runtime_directly()
    state = runtime.build_runtime_state()
    if state["all_checks_passed"] is not True or state["validation_failures"]:
        raise AssertionError("runtime state failed closed")
    counts = _validate_output_root(REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT)
    _check_materialization()
    _silent_import(
        "import covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009"
    )
    checker_path = Path(__file__)
    _silent_import(
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('exact9_checker',{str(checker_path)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    print("all_checks_passed=true")
    print("exact18_source_sha=18/18")
    print("registered_rule_count=9")
    print("predecessor_handler_identity_reused=8/8")
    print("public_dispatch_new_successor_function=true")
    print("public_dispatch_signature_matches_exact8=true")
    print("public_dispatch_uses_local_registry=true")
    print(f"contract_rows={counts['contract_rows']}")
    print(f"truth_rows={counts['truth_rows']}")
    print(
        "truth_groups="
        + json.dumps(TRUTH_GROUP_COUNTS, sort_keys=True, separators=(",", ":"))
    )
    print(f"registry_rows={counts['registry_rows']}")
    print(f"safety_rows={counts['safety_rows']}")
    print(f"issue_rows={counts['issue_rows']}")
    print("frozen_output_sha=6/6")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
