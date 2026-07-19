#!/usr/bin/env python3
"""Independent fail-closed checker for the ADMIT_001-to-008 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008
    as runtime,
)


EXPECTED_BASE_COMMIT = "f7079d9dfe5ef30889fb6fbe3bf5b66fdb0db5b0"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_008 unified adapter contract design v1"
PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_008 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_008_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_008_manifest_v1"
)
NEXT_STEP = "audit_covapie_admit_009_formal_evaluator_interface_preconditions_v1"
SOURCE_BOUNDARY_NAME = "fixed_ordered_exact18_committed_source_boundary"
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py", "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json", "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_contract.csv", "d3a1ad40803ceb25f30e106bbab44ab11cfcc26717b7c244266ab1ce1378f29d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_truth_matrix.csv", "149b838e9fe8254df7ba7a610ae64377cb7c7a41da8010cedee4722dcea081b5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_registry_routing_and_oracle_audit.csv", "1dbb5453277a93dff5d7612715c5fdd5edfde0d63cf114802220f962e22118f3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_safety_audit.csv", "97fba54037625b78a82b17753b77870366f8c3fa492ee506923ed3ca369c9f88"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_issue_inventory.csv", "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py", "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_manifest.json", "ae5fc1c5aa28618765ed07fe5aae67c02d31e7650fb5921dae954c0a3cfefd7e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_contract.csv", "62fdcf8c18f5baf3b08cd29515804abba7543d5da21056d2d93a392d5c188ac9"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_truth_matrix.csv", "a78510cf512782f9bd586e040d26a7fb459ba8b0e1eec310195b417cd0b9c636"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate.py", "930a8791bd129a06b272163766a5431aeaf1a3e79003b22df77d6af16319fecb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_contract_manifest.json", "d7423c337512dff3f66a68209301c91dd3fee2bdd2a3a5b669185854c622d922"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_contract.csv", "29d4ceacd263cf4b1bb0a4320a8eda03a8742e9bb344b512f8412baed7967e8a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_candidate_projection_and_context_routing_matrix.csv", "7c8060203e71b83f7398d79977dfa69057089231fec034afba95fcf37d99fef2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_result_projection_truth_matrix.csv", "59fa45d08d8950387ebd752d0f867312a47a67326c9b23bed886500307a36e4c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_issue_readiness_inventory.csv", "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate.py", "d4b2480e5d1cff17377fa0856eeac007629c4db1e5cdb413e4ea83771d08461d"),
)
DESIGN_ISSUE_PATH = Path(SOURCE_BOUNDARY[16][0])
DESIGN_ISSUE_SHA256 = SOURCE_BOUNDARY[16][1]

CONTRACT_FILENAME = "covapie_admit_001_to_008_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_008_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_008_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_008_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_008_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_008_runtime_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
EXPECTED_OUTPUT_SHA256 = {
    REGISTRY_FILENAME: "a77ca44d59dd3984be23f86923acabd52594e9b2e6958a38aeb5719313d88c4f",
    CONTRACT_FILENAME: "27d0c9d941698d99d045b367889ccd388f708353bcd342eb7f57729bb99940f9",
    ISSUE_FILENAME: "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    MANIFEST_FILENAME: "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    SAFETY_FILENAME: "4467d5d2c33808aa7e5ef793278462a8a5fa6796768d9c37717d2a6b07189635",
    TRUTH_FILENAME: "4b2010ac1fc84a884cfa798e825c26816acb6feb7d330b14fcf823b67f8bf65e",
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
    "candidate_access_status", "predecessor_handler_identity_status", "case_passed",
)
REGISTRY_HEADER = (
    "admission_rule_id", "admission_rule_name", "adapter_id", "known_rule",
    "callable_discovered", "adapter_ready", "registered",
    "predecessor_handler_identity_reused", "successor_handler_implemented",
    "expected_dispatch_behavior", "audit_passed",
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
REGISTERED_RULE_IDS = KNOWN_RULE_IDS[:8]
CANDIDATE_FIELD = "topology_restoration_disposition"
CONTEXT_ITEM = "allowed_topology_restoration_dispositions"
CANDIDATE_FIELDS = (CANDIDATE_FIELD,)
CONTEXT_ITEMS = (CONTEXT_ITEM,)
ENUM_MEMBERS = (
    "approved_restoration_template",
    "explicit_manual_review_approved",
    "manual_review_required",
    "quarantine_required",
)
ALLOWED_DISPOSITIONS = ENUM_MEMBERS[:2]
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
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_topology_restoration_disposition", "validated_candidate_fields",
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
}
ADAPTER_IDS = {
    rule_id: f"covapie_admit_{index:03d}_unified_adapter_v1"
    for index, rule_id in enumerate(REGISTERED_RULE_IDS, 1)
}
TRUTH_GROUP_COUNTS = {
    "global_dispatch": 5,
    "predecessor_handler_identity": 7,
    "predecessor_exact7_truth": 107,
    "admit008_exact38": 38,
    "admit008_context_routing": 7,
    "admit008_candidate_envelope": 16,
    "admit008_source_oracle": 5,
    "admit008_projection": 6,
    "registry_issue_boundary": 12,
}
TRUE_READINESS = (
    "unified_dispatch_runtime_with_admit_001_to_008_implemented",
    "admit_008_unified_adapter_implemented",
    "admit_008_registered_in_engine",
    "admit_008_context_routing_runtime_enforced",
    "admit_008_candidate_projection_runtime_enforced",
    "admit_008_key_absent_runtime_enforced",
    "admit_008_none_empty_forwarding_runtime_enforced",
    "admit_008_source_prevalidation_before_oracle_runtime_enforced",
    "admit_008_semantic_oracle_equivalence_runtime_enforced",
    "admit_008_unified_result_projection_runtime_enforced",
    "admit_008_blocked_passthrough_runtime_enforced",
    "admit_008_context_invalid_partial_canonical_projection_runtime_enforced",
    "exact7_public_types_reused_by_identity",
    "admit_001_to_007_handler_identity_reused",
    "registry_is_mapping_proxy_type",
    "registered_rule_count_is_8",
    "callable_discovered_rule_count_is_8",
    "adapter_ready_rule_count_is_8",
    "ready_for_admit_009_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "exact7_runtime_modified",
    "real_provider_topology_disposition_mapping_validated",
    "real_provider_value_count_nonzero",
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine",
    "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)


class _StringSubclass(str):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(
        io.StringIO(path.read_text(encoding="utf-8"), newline="")
    )
    if reader.fieldnames is None:
        raise AssertionError(f"CSV header missing: {path.name}")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != tuple(reader.fieldnames) for row in rows):
        raise AssertionError(f"CSV row shape mismatch: {path.name}")
    return tuple(reader.fieldnames), rows


def _readiness() -> dict[str, bool]:
    return {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }


def _classify(
    scalar: object, context: object
) -> tuple[str, str, tuple[tuple[str, str], ...]]:
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
        return "invalid", reason, ()
    validated = ((CANDIDATE_FIELD, canonical),)
    if type(context) is not tuple:
        return "invalid", CONTEXT_VALUE_REASONS[0], validated
    if (
        any(type(member) is not str for member in context)
        or context != ALLOWED_DISPOSITIONS
    ):
        return "invalid", CONTEXT_VALUE_REASONS[1], validated
    if canonical in BLOCKED_REASONS:
        return "blocked", BLOCKED_REASONS[canonical], validated
    return "passed", "", validated


def _exact38_definitions() -> tuple[tuple[str, str, object, object], ...]:
    exact = ALLOWED_DISPOSITIONS
    scalars = (
        ("canonical_approved_template", "canonical", ENUM_MEMBERS[0]),
        ("canonical_manual_approved", "canonical", ENUM_MEMBERS[1]),
        ("canonical_manual_required", "canonical", ENUM_MEMBERS[2]),
        ("canonical_quarantine", "canonical", ENUM_MEMBERS[3]),
        ("type_none", "scalar_type", None),
        ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(exact[0])),
        ("type_list", "scalar_type", [exact[0]]),
        ("type_mapping", "scalar_type", {"value": exact[0]}),
        ("empty", "empty_syntax", ""),
        ("whitespace", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " approved_restoration_template"),
        ("trailing_whitespace", "empty_syntax", "approved_restoration_template "),
        ("uppercase", "empty_syntax", "Approved_restoration_template"),
        ("hyphen", "empty_syntax", "approved-restoration-template"),
        ("dot", "empty_syntax", "approved.restoration"),
        ("slash", "empty_syntax", "approved/restoration"),
        ("non_ascii", "empty_syntax", "approved_restoratión"),
        ("over_length", "empty_syntax", "a" * 65),
        ("leading_digit", "empty_syntax", "1approved"),
        ("unknown_valid", "unknown", "unregistered_disposition"),
        ("unknown_approved_looking", "unknown", "approved_manual_review"),
        ("unknown_manual_review_looking", "unknown", "manual_review_approved"),
        ("unknown_other", "unknown", "other"),
        ("unknown_unknown", "unknown", "unknown"),
    )
    contexts = (
        ("context_exact_tuple", exact),
        ("context_none", None),
        ("context_list", list(exact)),
        ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_reversed", tuple(reversed(exact))),
        ("context_missing", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_blocked_added", (*exact, ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass_member", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra", (*exact, "explicit_approval")),
    )
    definitions = [
        (name, group, scalar, exact) for name, group, scalar in scalars
    ]
    definitions.extend(
        (name, "context", ENUM_MEMBERS[0], context)
        for name, context in contexts
    )
    return tuple(definitions)


def _truth_row(
    case_id: str,
    group: str,
    rule_id: str,
    behavior: str,
    value: str,
    reason: str,
    *,
    formal: int = 0,
    oracle: int = 0,
    access: str = "not_applicable",
    identity: str = "not_applicable",
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "case_group": group,
        "admission_rule_id": rule_id,
        "behavior": behavior,
        "expected_result_or_error": value,
        "observed_result_or_error": value,
        "expected_reason": reason,
        "observed_reason": reason,
        "formal_call_count": str(formal),
        "oracle_call_count": str(oracle),
        "candidate_access_status": access,
        "predecessor_handler_identity_status": identity,
        "case_passed": "true",
    }


def _expected_truth_rows() -> list[dict[str, str]]:
    rows = [
        _truth_row("GLOBAL_NON_STR", "global_dispatch", "8", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        _truth_row("GLOBAL_STR_SUBCLASS", "global_dispatch", "ADMIT_008", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        _truth_row("GLOBAL_UNKNOWN", "global_dispatch", "ADMIT_999", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        _truth_row("GLOBAL_KNOWN_UNREGISTERED", "global_dispatch", "ADMIT_009", "global_precedence", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        _truth_row("GLOBAL_PRECEDENCE", "global_dispatch", "ADMIT_999", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
    ]
    for rule_id in KNOWN_RULE_IDS[:7]:
        rows.append(
            _truth_row(
                f"PRED_IDENTITY_{rule_id}",
                "predecessor_handler_identity",
                rule_id,
                "handler_identity",
                "identity_reused",
                "",
                identity="true",
            )
        )
    _, predecessor_rows = _csv(REPO_ROOT / SOURCE_BOUNDARY[3][0])
    if len(predecessor_rows) != 107:
        raise AssertionError("committed Exact7 truth changed")
    for prior in predecessor_rows:
        row = {
            "case_id": f"PRED_EXACT7_{prior['case_id']}",
            "case_group": "predecessor_exact7_truth",
            "admission_rule_id": prior["admission_rule_id"],
            "behavior": f"{prior['case_group']}|{prior['behavior']}",
            "expected_result_or_error": prior["expected_result_or_error"],
            "observed_result_or_error": prior["observed_result_or_error"],
            "expected_reason": prior["expected_reason"],
            "observed_reason": prior["observed_reason"],
            "formal_call_count": prior["formal_call_count"],
            "oracle_call_count": prior["oracle_call_count"],
            "candidate_access_status": prior["candidate_access_status"],
            "predecessor_handler_identity_status": prior["predecessor_handler_identity_status"],
            "case_passed": prior["case_passed"],
        }
        rows.append(row)
    for index, (name, semantic_group, scalar, context) in enumerate(
        _exact38_definitions(), 1
    ):
        outcome, reason, _ = _classify(scalar, context)
        rows.append(
            _truth_row(
                f"A008_EXACT38_{index:03d}_{name}",
                "admit008_exact38",
                "ADMIT_008",
                f"complete_exact10_oracle_and_exact13|{semantic_group}",
                outcome,
                reason,
                formal=1,
                oracle=1,
                access="value_read_once",
            )
        )
    for case_id, reason in (
        ("A008_CONTEXT_BATCH", "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE"),
        ("A008_CONTEXT_EVALUATION", "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("A008_CONTEXT_KEY", "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED"),
        ("A008_CONTEXT_DOWNLOAD", "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("A008_CONTEXT_STAGE", "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("A008_CONTEXT_MULTI_PRECEDENCE", "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE"),
    ):
        rows.append(
            _truth_row(
                case_id,
                "admit008_context_routing",
                "ADMIT_008",
                "ordered_context_failure_no_candidate_access",
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                reason,
                access="not_accessed",
            )
        )
    rows.append(
        _truth_row(
            "A008_CONTEXT_CANDIDATE_BOMB",
            "admit008_context_routing",
            "ADMIT_008",
            "candidate_not_accessed",
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
            access="not_accessed",
        )
    )
    for case_id, outcome, reason, formal, oracle, access in (
        ("A008_CANDIDATE_NON_MAPPING", "invalid", "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID", 0, 0, "envelope_checked"),
        ("A008_CANDIDATE_KEY_MISSING", "invalid", "topology_restoration_disposition_missing", 0, 0, "value_read_once"),
        ("A008_CANDIDATE_NONE", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_EMPTY", "invalid", SCALAR_REASONS[1], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_EMPTY_SUBCLASS", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_WHITESPACE", "invalid", SCALAR_REASONS[3], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_INTEGER", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_UNKNOWN", "invalid", SCALAR_REASONS[4], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_PASSED_TEMPLATE", "passed", "", 1, 1, "value_read_once"),
        ("A008_CANDIDATE_PASSED_MANUAL", "passed", "", 1, 1, "value_read_once"),
        ("A008_CANDIDATE_BLOCKED_MANUAL", "blocked", BLOCKED_REASONS[ENUM_MEMBERS[2]], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_BLOCKED_QUARANTINE", "blocked", BLOCKED_REASONS[ENUM_MEMBERS[3]], 1, 1, "value_read_once"),
        ("A008_CANDIDATE_MAPPING_SUBCLASS", "passed", "", 1, 1, "value_read_once"),
        ("A008_CANDIDATE_EXTRA_FIELDS", "passed", "", 1, 1, "value_read_once"),
        ("A008_CANDIDATE_NO_MUTATION", "passed", "", 1, 1, "value_read_once"),
        ("A008_CANDIDATE_IDENTITY", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
    ):
        rows.append(
            _truth_row(
                case_id,
                "admit008_candidate_envelope",
                "ADMIT_008",
                "candidate_projection_key_absent_only_missing",
                outcome,
                reason,
                formal=formal,
                oracle=oracle,
                access=access,
            )
        )
    for case_id, reason, oracle in (
        ("A008_SOURCE_WRONG_TYPE", "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", 0),
        ("A008_SOURCE_SUBCLASS", "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", 0),
        ("A008_SOURCE_STORAGE_ORDER", "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 0),
        ("A008_SOURCE_INVARIANT_CONFLICT", "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 0),
        ("A008_SOURCE_ORACLE_MISMATCH", "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1),
    ):
        rows.append(
            _truth_row(
                case_id,
                "admit008_source_oracle",
                "ADMIT_008",
                (
                    "complete_exact10_mismatch_no_projection"
                    if oracle
                    else "source_prevalidation_before_oracle_no_partial_result"
                ),
                "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
                reason,
                formal=1,
                oracle=oracle,
                access="value_read_once",
            )
        )
    for case_id, scalar, context in (
        ("PASSED_TEMPLATE", ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS),
        ("PASSED_MANUAL", ENUM_MEMBERS[1], ALLOWED_DISPOSITIONS),
        ("BLOCKED_MANUAL", ENUM_MEMBERS[2], ALLOWED_DISPOSITIONS),
        ("BLOCKED_QUARANTINE", ENUM_MEMBERS[3], ALLOWED_DISPOSITIONS),
        ("SCALAR_INVALID", "unknown", ALLOWED_DISPOSITIONS),
        ("CONTEXT_INVALID_CANONICAL", ENUM_MEMBERS[0], None),
    ):
        outcome, reason, _ = _classify(scalar, context)
        rows.append(
            _truth_row(
                f"A008_PROJECTION_{case_id}",
                "admit008_projection",
                "ADMIT_008",
                "complete_exact10_to_existing_exact13",
                outcome,
                reason,
                formal=1,
                oracle=1,
                access="value_read_once",
            )
        )
    for rule_id in KNOWN_RULE_IDS[8:]:
        rows.append(
            _truth_row(
                f"UNSUPPORTED_{rule_id}",
                "registry_issue_boundary",
                rule_id,
                "known_not_registered_fail_closed",
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            )
        )
    rows.extend(
        (
            _truth_row("BOUNDARY_ADMIT008_REGISTERED", "registry_issue_boundary", "ADMIT_008", "successor_handler_registered", "registered", ""),
            _truth_row("BOUNDARY_COVERAGE_ONLY_ADMIT008", "registry_issue_boundary", "ADMIT_008", "coverage_transition", "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015", ""),
            _truth_row("BOUNDARY_ENUM_RESOLVED", "registry_issue_boundary", "ADMIT_008", "enum_issue_preserved", "resolved", ""),
            _truth_row("BOUNDARY_NO_EVALUATE_ALL", "registry_issue_boundary", "", "public_boundary_absent", "absent", ""),
            _truth_row("BOUNDARY_NO_COMBINED_VERDICT", "registry_issue_boundary", "", "public_boundary_absent", "absent", ""),
        )
    )
    if Counter(row["case_group"] for row in rows) != TRUTH_GROUP_COUNTS:
        raise AssertionError("checker truth group construction failed")
    return rows


def _contract_definitions() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("TYPE_001", "type_identity", "result type identity", "true"),
        ("TYPE_002", "type_identity", "dispatch error type identity", "true"),
        ("TYPE_003", "type_identity", "Exact13 fields", "|".join(RESULT_FIELDS)),
        ("TYPE_004", "type_identity", "Exact6 fields", "|".join(ERROR_FIELDS)),
        ("TYPE_005", "type_identity", "result schema", RESULT_SCHEMA_VERSION),
        ("TYPE_006", "type_identity", "outcome vocabulary", "|".join(OUTCOME_VOCABULARY)),
        ("API_001", "public_api", "signature", PUBLIC_SIGNATURE),
        ("API_002", "public_api", "dispatch cardinality", "single_rule_only"),
        ("API_003", "public_api", "evaluate_all_rules", "excluded"),
        ("API_004", "public_api", "combined candidate verdict", "excluded"),
        ("DISPATCH_001", "global_dispatch", "precedence", "exact_str|known|registered|handler"),
        ("REGISTRY_001", "registry", "immutable registry", "true"),
        ("REGISTRY_002", "registry", "registered IDs", "|".join(REGISTERED_RULE_IDS)),
        ("REGISTRY_003", "registry", "registered count", "8"),
        ("REGISTRY_004", "registry", "callable discovered count", "8"),
        ("REGISTRY_005", "registry", "adapter ready count", "8"),
        ("REUSE_001", "predecessor_reuse", "first seven handler identity", "true"),
        ("REUSE_002", "predecessor_reuse", "first seven names and adapters", "true"),
        ("A008_001", "admit008_identity", "rule name", RULE_NAMES["ADMIT_008"]),
        ("A008_002", "admit008_identity", "adapter ID", ADAPTER_IDS["ADMIT_008"]),
        ("CONTEXT_001", "context_routing", "precedence", "batch|evaluation_mapping|evaluation_key|download_result|stage_authorization"),
        ("CONTEXT_002", "context_routing", "batch context", "exact_none"),
        ("CONTEXT_003", "context_routing", "evaluation Mapping subclass", "accepted"),
        ("CONTEXT_004", "context_routing", "evaluation extra keys", "ignored"),
        ("CONTEXT_005", "context_routing", "required value", "original_identity_single_lookup_no_prevalidation"),
        ("CONTEXT_006", "context_routing", "download result context", "exact_none"),
        ("CONTEXT_007", "context_routing", "stage authorization context", "exact_none"),
        ("CONTEXT_008", "context_routing", "candidate access before routing", "false"),
        ("CANDIDATE_001", "candidate_projection", "field", CANDIDATE_FIELD),
        ("CANDIDATE_002", "candidate_projection", "Mapping subclasses", "accepted"),
        ("CANDIDATE_003", "candidate_projection", "extra fields", "ignored"),
        ("CANDIDATE_004", "candidate_projection", "non Mapping reason", "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("CANDIDATE_005", "candidate_projection", "consumed context retained", "true"),
        ("MISSING_001", "missing", "only category", "required_key_absent"),
        ("MISSING_002", "missing", "reason", "topology_restoration_disposition_missing"),
        ("FORWARD_001", "forwarding", "exact None", SCALAR_REASONS[0]),
        ("FORWARD_002", "forwarding", "exact built-in empty str", SCALAR_REASONS[1]),
        ("FORWARD_003", "forwarding", "empty str subclass", SCALAR_REASONS[0]),
        ("FORWARD_004", "forwarding", "whitespace malformed unknown and blocked", "standalone_exact_reason"),
        ("FORMAL_001", "formal_evaluator", "positional original objects", "single_candidate_lookup_single_context_lookup_exact_once"),
        ("FORMAL_002", "formal_evaluator", "normalization", "none"),
        ("FORMAL_003", "formal_evaluator", "provider mapping", "none"),
        ("FORMAL_004", "formal_evaluator", "I/O", "false"),
        ("SOURCE_001", "source_prevalidation", "exact source type", "required"),
        ("SOURCE_002", "source_prevalidation", "source subclass", "rejected"),
        ("SOURCE_003", "source_prevalidation", "storage", "exact_builtin_dict_exact10_key_order"),
        ("SOURCE_004", "source_prevalidation", "dataclass fields", "exact10_order"),
        ("SOURCE_005", "source_prevalidation", "ordered reads and reconstruction", "all_fields_before_oracle"),
        ("SOURCE_006", "source_prevalidation", "cross field invariants", "committed_post_init"),
        ("SOURCE_007", "source_prevalidation", "failure adapter readiness", "false"),
        ("SOURCE_008", "source_prevalidation", "oracle after failure", "false"),
        ("ORACLE_001", "semantic_oracle", "identity", "classify_admit_008_topology_restoration_disposition_design"),
        ("ORACLE_002", "semantic_oracle", "outcome view", "classification.admit_008"),
        ("ORACLE_003", "semantic_oracle", "original objects", "exact_once"),
        ("ORACLE_004", "semantic_oracle", "complete Exact10 construction", "required"),
        ("ORACLE_005", "semantic_oracle", "complete Exact10 equality", "required"),
        ("PROJECTION_001", "exact13", "normalized from validated", "true"),
        ("PROJECTION_002", "exact13", "two passed passthrough", "true"),
        ("PROJECTION_003", "exact13", "two blocked passthrough", "true"),
        ("PROJECTION_004", "exact13", "blocked reasons distinct", "true"),
        ("PROJECTION_005", "exact13", "scalar invalid empty pair", "true"),
        ("PROJECTION_006", "exact13", "context invalid canonical retained", "true"),
        ("PROJECTION_007", "exact13", "partial result on failure", "false"),
        ("SAFETY_001", "runtime_safety", "candidate mutation", "false"),
        ("SAFETY_002", "runtime_safety", "evaluation context mutation", "false"),
        ("SAFETY_003", "runtime_safety", "public runtime metadata I/O", "false"),
        ("SAFETY_004", "runtime_safety", "pure in memory runtime", "true"),
        ("ISSUE_001", "issues", "authoritative predecessor", DESIGN_ISSUE_SHA256),
        ("ISSUE_002", "issues", "coverage transition", "admit_008_implemented_and_removed_from_open_coverage_scope"),
        ("ISSUE_003", "issues", "remaining coverage", "|".join(KNOWN_RULE_IDS[8:])),
        ("ISSUE_004", "issues", "topology enum", "resolved"),
        ("BOUNDARY_001", "boundary", "ADMIT_009 to ADMIT_015 registered", "false"),
        ("BOUNDARY_002", "boundary", "provider fields consumed", "none"),
        ("BOUNDARY_003", "boundary", "provider values", "zero"),
        ("BOUNDARY_004", "boundary", "real candidate evaluation", "excluded"),
        ("BOUNDARY_005", "boundary", "download and training", "excluded"),
        ("BOUNDARY_006", "boundary", "ADMIT_009 implementation", "excluded"),
    )


def _expected_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_id": identifier,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for identifier, area, statement, value in _contract_definitions()
    ]


def _expected_registry_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in REGISTERED_RULE_IDS
        rows.append(
            {
                "admission_rule_id": rule_id,
                "admission_rule_name": RULE_NAMES.get(rule_id, ""),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(registered).lower(),
                "adapter_ready": str(registered).lower(),
                "registered": str(registered).lower(),
                "predecessor_handler_identity_reused": str(rule_id in KNOWN_RULE_IDS[:7]).lower(),
                "successor_handler_implemented": str(rule_id == "ADMIT_008").lower(),
                "expected_dispatch_behavior": "registered_single_rule_runtime" if registered else "known_not_registered_fail_closed",
                "audit_passed": "true",
            }
        )
    return rows


EXECUTED_SAFETY_ITEMS = (
    "exact8_successor_runtime_implementation",
    "admit_008_adapter_handler_implementation",
    "exact8_registry_extension",
    "public_type_identity_reuse",
    "predecessor_handler_identity_reuse",
    "context_routing",
    "candidate_projection",
    "standalone_exact10_validation",
    "oracle_complete_exact10_equivalence",
    "exact13_projection",
    "synthetic_runtime_truth",
    "exact18_source_verification",
    "issue_coverage_transition",
    "deterministic_materialization",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "predecessor_exact7_runtime_modification",
    "admit_001_to_007_handler_modification",
    "admit_009_implementation",
    "admit_009_to_015_registration",
    "provider_mapping",
    "provider_value_materialization",
    "restoration_provenance_consumption",
    "real_candidate_evaluation",
    "evaluate_all_rules",
    "combined_candidate_verdict",
    "cross_rule_precedence_change",
    "raw_read",
    "network",
    "bulk_download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward",
    "model_loss",
    "training",
    "fine_tune",
    "parameter_update",
    "stage",
    "commit",
    "push",
    "gh",
)


def _expected_safety_rows() -> list[dict[str, str]]:
    values = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple(
        (item, False) for item in NOT_EXECUTED_SAFETY_ITEMS
    )
    return [
        {
            "safety_item": item,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "safety_passed": "true",
        }
        for item, executed in values
    ]


def _expected_issue_rows() -> list[dict[str, str]]:
    header, rows = _csv(REPO_ROOT / DESIGN_ISSUE_PATH)
    if header != ISSUE_HEADER or len(rows) != 11:
        raise AssertionError("authoritative Exact11 issue shape changed")
    matches = [
        row for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(matches) != 1:
        raise AssertionError("coverage issue missing or duplicate")
    matches[0]["affected_rules"] = "|".join(KNOWN_RULE_IDS[8:])
    matches[0]["integration_transition"] = (
        "admit_008_implemented_and_removed_from_open_coverage_scope"
    )
    return rows


def _expected_manifest() -> dict[str, object]:
    readiness = _readiness()
    paths = [path for path, _ in SOURCE_BOUNDARY]
    source_sha = {path: digest for path, digest in SOURCE_BOUNDARY}
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
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
            "exact7_unified_runtime_predecessor",
            "admit008_standalone_evaluator",
            "admit008_committed_independent_enum_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
        "public_api_signature": PUBLIC_SIGNATURE,
        "public_dispatch_cardinality": "single_rule_only",
        "result_type_reused_by_identity": True,
        "dispatch_error_type_reused_by_identity": True,
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
        "registered_rule_ids": list(REGISTERED_RULE_IDS),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[8:]),
        "registered_rule_count": 8,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_seven_handler_identity_reused": {
            rule_id: True for rule_id in KNOWN_RULE_IDS[:7]
        },
        "admit_008_handler": "_evaluate_registered_admit_008",
        "admit_008_candidate_fields": list(CANDIDATE_FIELDS),
        "admit_008_context_items": list(CONTEXT_ITEMS),
        "admit_008_context_order": [
            "batch_context",
            "evaluation_context_mapping",
            "evaluation_required_key",
            "download_result_context",
            "stage_authorization_context",
            "candidate_record",
        ],
        "admit_008_context_reasons": {
            "batch_context": "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "evaluation_required_key": "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED",
            "download_result_context": "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_008_candidate_mapping_invalid_reason": "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_008_missing_categories": ["required_key_absent"],
        "admit_008_missing_reason": "topology_restoration_disposition_missing",
        "admit_008_none_empty_forwarding": {
            "exact_none": SCALAR_REASONS[0],
            "exact_builtin_empty_str": SCALAR_REASONS[1],
            "empty_str_subclass": SCALAR_REASONS[0],
        },
        "admit_008_formal_evaluator": "evaluate_admit_008",
        "admit_008_formal_call_count": 1,
        "admit_008_adapter_normalization": False,
        "admit_008_source_type": "Admit008EvaluationResult",
        "admit_008_source_fields": list(SOURCE_FIELDS),
        "admit_008_source_prevalidation_before_oracle": True,
        "admit_008_oracle": "classify_admit_008_topology_restoration_disposition_design",
        "admit_008_oracle_outcome_view": "classification.admit_008",
        "admit_008_oracle_call_count": 1,
        "admit_008_complete_exact10_equality_required": True,
        "admit_008_normalized_values_projection": "source.validated_candidate_fields",
        "admit_008_no_partial_exact13_on_failure": True,
        "admit_008_passed_members": list(ALLOWED_DISPOSITIONS),
        "admit_008_blocked_reason_mapping": dict(BLOCKED_REASONS),
        "admit_008_scalar_invalid_empty_projection": True,
        "admit_008_context_invalid_canonical_projection": True,
        "contract_row_count": 77,
        "contract_pass_count": 77,
        "truth_matrix_row_count": 203,
        "truth_matrix_pass_count": 203,
        "truth_matrix_group_counts": dict(TRUTH_GROUP_COUNTS),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "safety_audit_row_count": 41,
        "safety_audit_pass_count": 41,
        "issue_inventory_row_count": 11,
        "issue_transition_count": 1,
        "issue_transition_id": "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "issue_authoritative_predecessor_sha256": DESIGN_ISSUE_SHA256,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(MANIFEST_OUTPUT_SHA256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "provider_fields_consumed": [],
        "real_provider_value_count": 0,
        "real_provider_mapping_executed": False,
        "exact7_runtime_modified": False,
        "admit_009_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "stop_boundaries": [
            "no_admit_009",
            "no_provider_mapping",
            "no_real_candidate_evaluation",
            "no_evaluate_all_rules",
            "no_combined_candidate_verdict",
            "no_raw_network_download",
            "no_model_forward_loss_training",
        ],
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
    }


PROTECTED_BUILDERS = {
    "_readiness",
    "_classify",
    "_exact38_definitions",
    "_expected_truth_rows",
    "_contract_definitions",
    "_expected_contract_rows",
    "_expected_registry_rows",
    "_expected_safety_rows",
    "_expected_issue_rows",
    "_expected_manifest",
}


def _assert_checker_independent_ast(source_text: str | None = None) -> None:
    tree = ast.parse(
        Path(__file__).read_text(encoding="utf-8")
        if source_text is None
        else source_text
    )
    forbidden_roots = {
        "runtime", "predecessor", "admit008", "admit008_oracle", "design_gate",
    }
    forbidden_attributes = {
        "_contract_rows", "_truth_rows", "_registry_rows", "_safety_rows",
        "EVALUATOR_REGISTRY", "evaluate_admit_008",
        "classify_admit_008_topology_restoration_disposition_design",
        "SOURCE_PATHS", "SOURCE_SHA256", "CONTRACT_COLUMNS", "TRUTH_COLUMNS",
        "REGISTRY_COLUMNS", "SAFETY_COLUMNS", "ISSUE_COLUMNS", "OUTPUT_FILES",
        "TRUE_READINESS", "FALSE_READINESS", "ADAPTER_IDS", "RESULT_FIELDS",
        "_manifest_payload",
    }
    seen: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in PROTECTED_BUILDERS:
            seen.add(node.name)
            names = {
                child.id for child in ast.walk(node) if isinstance(child, ast.Name)
            }
            attributes = {
                child.attr
                for child in ast.walk(node)
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
    identity = (
        runtime.PROJECT == PROJECT,
        runtime.STEP == STEP,
        runtime.STAGE == STAGE,
        runtime.EXPECTED_BASE_COMMIT == EXPECTED_BASE_COMMIT,
        runtime.EXPECTED_BASE_SUBJECT == EXPECTED_BASE_SUBJECT,
        runtime.MANIFEST_SCHEMA_VERSION == MANIFEST_SCHEMA_VERSION,
        runtime.RECOMMENDED_NEXT_STEP == NEXT_STEP,
        runtime.SOURCE_PATHS == tuple(Path(path) for path, _ in SOURCE_BOUNDARY),
        runtime.SOURCE_SHA256
        == {Path(path): digest for path, digest in SOURCE_BOUNDARY},
        runtime.OUTPUT_FILES == OUTPUT_FILES,
        runtime.CSV_OUTPUTS == CSV_OUTPUTS,
        runtime.RESULT_FIELDS == RESULT_FIELDS,
        runtime.DISPATCH_ERROR_FIELDS == ERROR_FIELDS,
        runtime.DISPATCH_ERROR_CODES == ERROR_CODES,
        runtime.OUTCOME_VOCABULARY == OUTCOME_VOCABULARY,
        runtime.KNOWN_RULE_IDS == KNOWN_RULE_IDS,
        runtime.CALLABLE_DISCOVERED_RULE_IDS == REGISTERED_RULE_IDS,
        runtime.ADAPTER_READY_RULE_IDS == REGISTERED_RULE_IDS,
        dict(runtime.RULE_NAMES) == RULE_NAMES,
        dict(runtime.ADAPTER_IDS) == ADAPTER_IDS,
        tuple(runtime.TRUE_READINESS) == TRUE_READINESS,
        tuple(runtime.FALSE_READINESS) == FALSE_READINESS,
    )
    if not all(identity):
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


def _check_runtime_directly() -> None:
    if (
        runtime.UnifiedAdmissionRuleEvaluation
        is not runtime.predecessor.UnifiedAdmissionRuleEvaluation
        or runtime.UnifiedAdmissionDispatchError
        is not runtime.predecessor.UnifiedAdmissionDispatchError
    ):
        raise AssertionError("public type identity changed")
    for name in (
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        if getattr(runtime, name) is not getattr(runtime.predecessor, name):
            raise AssertionError(f"public constant identity changed: {name}")
    if inspect.signature(runtime.evaluate_admission_rule) != inspect.signature(
        runtime.predecessor.evaluate_admission_rule
    ):
        raise AssertionError("public API signature changed")
    if type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType:
        raise AssertionError("registry is not MappingProxyType")
    if tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_RULE_IDS:
        raise AssertionError("registry order changed")
    for rule_id in KNOWN_RULE_IDS[:7]:
        if (
            runtime.EVALUATOR_REGISTRY[rule_id]
            is not runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        ):
            raise AssertionError(f"predecessor handler wrapped: {rule_id}")
    if (
        runtime.EVALUATOR_REGISTRY["ADMIT_008"]
        is not runtime._evaluate_registered_admit_008
    ):
        raise AssertionError("ADMIT_008 handler identity changed")
    if hasattr(runtime, "evaluate_all_rules") or hasattr(
        runtime, "combined_candidate_verdict"
    ):
        raise AssertionError("aggregation boundary expanded")

    class Text(str):
        pass

    error = _assert_error(
        lambda: runtime.evaluate_admission_rule(Text("ADMIT_008"), {}),
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    )
    if (error.known_rule, error.callable_discovered, error.adapter_ready) != (
        False, False, False
    ):
        raise AssertionError("rule-id exact-type flags changed")
    for rule_id in KNOWN_RULE_IDS[8:]:
        error = _assert_error(
            lambda rule_id=rule_id: runtime.evaluate_admission_rule(rule_id, {}),
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        )
        if (error.known_rule, error.callable_discovered, error.adapter_ready) != (
            True, False, False
        ):
            raise AssertionError("known-not-registered flags changed")

    class SingleLookup(Mapping[str, object]):
        def __init__(self, key: str, value: object, present: bool = True) -> None:
            self.key = key
            self.value = value
            self.present = present
            self.lookups = 0

        def __getitem__(self, key: str) -> object:
            if key != self.key:
                raise KeyError(key)
            self.lookups += 1
            if self.lookups > 1:
                raise AssertionError("required field read twice")
            if not self.present:
                raise KeyError(key)
            return self.value

        def __iter__(self):
            raise AssertionError("Mapping iterated")

        def __len__(self) -> int:
            raise AssertionError("Mapping sized")

    class Bomb(Mapping[str, object]):
        accesses = 0

        def __getitem__(self, key: str) -> object:
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __iter__(self):
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __len__(self) -> int:
            self.accesses += 1
            raise AssertionError("candidate accessed")

    bomb = Bomb()
    with (
        patch.object(runtime.admit008, "evaluate_admit_008", side_effect=AssertionError("formal called")),
        patch.object(runtime.admit008_oracle, "classify_admit_008_topology_restoration_disposition_design", side_effect=AssertionError("oracle called")),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_008", bomb, batch_context={}, evaluation_context=[]
            ),
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
        )
    if error.adapter_ready is not True or bomb.accesses:
        raise AssertionError("context failure reached candidate")

    scalar = object()
    context = object()
    candidate = SingleLookup(CANDIDATE_FIELD, scalar)
    evaluation = SingleLookup(CONTEXT_ITEM, context)
    source = runtime.admit008.evaluate_admit_008(
        ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS
    )
    classification = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
        ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS
    )
    calls: dict[str, list[tuple[object, object]]] = {"formal": [], "oracle": []}
    with (
        patch.object(runtime.admit008, "evaluate_admit_008", lambda left, right: calls["formal"].append((left, right)) or source),
        patch.object(runtime.admit008_oracle, "classify_admit_008_topology_restoration_disposition_design", lambda left, right: calls["oracle"].append((left, right)) or classification),
    ):
        result = runtime.evaluate_admission_rule(
            "ADMIT_008", candidate, evaluation_context=evaluation
        )
    if result.outcome != "passed" or candidate.lookups != 1 or evaluation.lookups != 1:
        raise AssertionError("single lookup contract changed")
    if calls != {"formal": [(scalar, context)], "oracle": [(scalar, context)]}:
        raise AssertionError("original object identity lost")

    missing = SingleLookup(CANDIDATE_FIELD, object(), False)
    with patch.object(
        runtime.admit008, "evaluate_admit_008", side_effect=AssertionError("formal called")
    ):
        result = runtime.evaluate_admission_rule(
            "ADMIT_008", missing, evaluation_context={CONTEXT_ITEM: ALLOWED_DISPOSITIONS}
        )
    if result.reason != "topology_restoration_disposition_missing" or missing.lookups != 1:
        raise AssertionError("key-absent missing contract changed")

    for value, expected_reason in ((None, SCALAR_REASONS[0]), ("", SCALAR_REASONS[1])):
        counts = Counter()
        formal = runtime.admit008.evaluate_admit_008
        oracle = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design
        with (
            patch.object(runtime.admit008, "evaluate_admit_008", lambda left, right, formal=formal: counts.update(["formal"]) or formal(left, right)),
            patch.object(runtime.admit008_oracle, "classify_admit_008_topology_restoration_disposition_design", lambda left, right, oracle=oracle: counts.update(["oracle"]) or oracle(left, right)),
        ):
            result = runtime.evaluate_admission_rule(
                "ADMIT_008",
                {CANDIDATE_FIELD: value},
                evaluation_context={CONTEXT_ITEM: ALLOWED_DISPOSITIONS},
            )
        if result.reason != expected_reason or counts != {"formal": 1, "oracle": 1}:
            raise AssertionError("None/empty forwarding changed")

    corrupt = runtime.admit008.evaluate_admit_008(
        ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS
    )
    object.__setattr__(corrupt, "evaluator_io_used", True)
    counts = Counter()
    with (
        patch.object(runtime.admit008, "evaluate_admit_008", lambda *args: counts.update(["formal"]) or corrupt),
        patch.object(runtime.admit008_oracle, "classify_admit_008_topology_restoration_disposition_design", lambda *args: counts.update(["oracle"])),
        patch.object(runtime, "_project_admit008_exact13", side_effect=AssertionError("projected")),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_008",
                {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
                evaluation_context={CONTEXT_ITEM: ALLOWED_DISPOSITIONS},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    if error.adapter_ready is not False or counts != {"formal": 1}:
        raise AssertionError("source validation did not precede oracle")

    mismatch = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
        ENUM_MEMBERS[1], ALLOWED_DISPOSITIONS
    )
    valid = runtime.admit008.evaluate_admit_008(ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS)
    counts.clear()
    with (
        patch.object(runtime.admit008, "evaluate_admit_008", lambda *args: counts.update(["formal"]) or valid),
        patch.object(runtime.admit008_oracle, "classify_admit_008_topology_restoration_disposition_design", lambda *args: counts.update(["oracle"]) or mismatch),
        patch.object(runtime, "_project_admit008_exact13", side_effect=AssertionError("projected")),
    ):
        _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_008",
                {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
                evaluation_context={CONTEXT_ITEM: ALLOWED_DISPOSITIONS},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    if counts != {"formal": 1, "oracle": 1}:
        raise AssertionError("oracle mismatch call count changed")

    reasons = []
    for scalar in ENUM_MEMBERS[2:]:
        result = runtime.evaluate_admission_rule(
            "ADMIT_008", {CANDIDATE_FIELD: scalar},
            evaluation_context={CONTEXT_ITEM: ALLOWED_DISPOSITIONS},
        )
        if result.outcome != "blocked" or result.reason != BLOCKED_REASONS[scalar]:
            raise AssertionError("blocked passthrough changed")
        reasons.append(result.reason)
    if len(set(reasons)) != 2:
        raise AssertionError("blocked reasons collapsed")
    retained = runtime.evaluate_admission_rule(
        "ADMIT_008", {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
        evaluation_context={CONTEXT_ITEM: None},
    )
    pair = ((CANDIDATE_FIELD, ENUM_MEMBERS[0]),)
    if retained.normalized_values != pair or retained.validated_candidate_fields != pair:
        raise AssertionError("context-invalid canonical pair lost")


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
        "run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1",
        "_git", "open", "read", "read_bytes", "read_text", "write",
        "write_bytes", "write_text", "run", "Popen", "system", "urlopen",
    }
    pending = ["evaluate_admission_rule", "_evaluate_registered_admit_008"]
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
        "_evaluate_registered_admit_008", "_admit008_context_failure",
        "_admit008_candidate_invalid", "_prevalidate_admit008_source",
        "_expected_admit008_from_oracle", "_validate_admit008_oracle_equivalence",
        "_project_admit008_exact13", "_admit008_adapter_failure",
    }
    if not required <= closure:
        raise AssertionError("public runtime closure incomplete")
    import_section = source.split("PROJECT =", 1)[0]
    if "admit_008_unified_adapter_contract_design_gate" in import_section:
        raise AssertionError("adapter design gate imported by runtime")
    for dependency in ("torch", "numpy", "rdkit"):
        if dependency in import_section:
            raise AssertionError(f"disallowed runtime dependency: {dependency}")


def _check_source_boundary() -> runtime.FrozenSourceSnapshot:
    _check_production_alignment()
    if len(SOURCE_BOUNDARY) != 18 or len({path for path, _ in SOURCE_BOUNDARY}) != 18:
        raise AssertionError("checker Exact18 source boundary shape changed")
    subject = subprocess.run(
        ["git", "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"],
        cwd=REPO_ROOT, capture_output=True, check=False,
    )
    if (
        subject.returncode != 0
        or subject.stdout.strip() != EXPECTED_BASE_SUBJECT
        or ancestor.returncode != 0
    ):
        raise AssertionError("checker base lineage mismatch")
    for relative, expected_sha in SOURCE_BOUNDARY:
        path = Path(relative)
        absolute = REPO_ROOT / path
        metadata = os.lstat(absolute)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
        base = subprocess.run(
            ["git", "show", f"{EXPECTED_BASE_COMMIT}:{relative}"],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
        try:
            absolute.resolve().relative_to(REPO_ROOT.resolve())
            descendant = True
        except ValueError:
            descendant = False
        if (
            tracked.returncode != 0
            or base.returncode != 0
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or not descendant
            or hashlib.sha256(base.stdout).hexdigest() != expected_sha
            or _sha256(absolute) != expected_sha
        ):
            raise AssertionError(f"checker source mismatch: {relative}")
    snapshot = runtime.build_frozen_source_snapshot()
    if not runtime.validate_frozen_source_snapshot(snapshot):
        raise AssertionError("runtime Exact18 source snapshot invalid")
    return snapshot


def _validate_manifest(manifest: object, root: Path) -> None:
    expected = _expected_manifest()
    if type(manifest) is not dict:
        raise AssertionError("manifest must be exact dict")
    if set(manifest) != set(expected):
        raise AssertionError("manifest key set mismatch")
    if manifest != expected:
        mismatch = sorted(key for key in expected if manifest[key] != expected[key])
        raise AssertionError(f"manifest semantic mismatch: {mismatch}")
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
        raise AssertionError("Exact77 contract semantics mismatch")
    if truth_header != TRUTH_HEADER or truth_rows != _expected_truth_rows():
        raise AssertionError("Exact203 truth semantics mismatch")
    if registry_header != REGISTRY_HEADER or registry_rows != _expected_registry_rows():
        raise AssertionError("Exact15 registry semantics mismatch")
    if safety_header != SAFETY_HEADER or safety_rows != _expected_safety_rows():
        raise AssertionError("Exact41 safety semantics mismatch")
    if issue_header != ISSUE_HEADER or issue_rows != _expected_issue_rows():
        raise AssertionError("Exact11 issue semantics mismatch")
    issue_map = {row["issue_id"]: row for row in issue_rows}
    if (
        issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] != "resolved"
        or issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"] != "resolved"
        or issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] != "open"
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
    with tempfile.TemporaryDirectory(prefix="covapie-exact8-check-") as temporary:
        first = Path(temporary) / "first"
        second = Path(temporary) / "second"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1(first)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1(second)
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
        "import covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008"
    )
    checker_path = Path(__file__)
    _silent_import(
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('exact8_checker',{str(checker_path)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    print("all_checks_passed=true")
    print("exact18_source_sha=18/18")
    print("registered_rule_count=8")
    print("predecessor_handler_identity_reused=7/7")
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
