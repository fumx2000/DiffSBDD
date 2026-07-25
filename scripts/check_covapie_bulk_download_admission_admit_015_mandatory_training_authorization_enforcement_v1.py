"""Check the standalone ADMIT_015 mandatory training guard and Exact10 evidence."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Any, NamedTuple

from covalent_ext import (
    covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement
    as enforcement,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as exact15_runtime,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "1e076d90439e75ec9f797ed4890f8fd6594dc9fa"
STAGE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1"
)
PRODUCTION_REL = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement.py"
)
CHECKER_REL = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1.py"
)
TESTS_REL = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1.py"
)
SUMMARY_REL = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1_summary.md"
)
IMPLEMENTATION_NAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_implementation_contract.csv"
)
ERROR_RESULT_NAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_error_and_result_contract.csv"
)
TRUTH_NAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_runtime_truth_matrix.csv"
)
PROTECTED_NAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_protected_action_safety_audit.csv"
)
ISSUES_NAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_issue_readiness_inventory.csv"
)
MANIFEST_NAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_manifest.json"
)
DERIVED_NAMES = (
    IMPLEMENTATION_NAME,
    ERROR_RESULT_NAME,
    TRUTH_NAME,
    PROTECTED_NAME,
    ISSUES_NAME,
    MANIFEST_NAME,
)
PREDECESSOR_ISSUES_REL = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_contract_v1/"
    "covapie_admit_015_mandatory_enforcement_issue_readiness_inventory.csv"
)
EXACT10 = (
    PRODUCTION_REL,
    CHECKER_REL,
    TESTS_REL,
    SUMMARY_REL,
    *(STAGE / name for name in DERIVED_NAMES),
)
SUPPORT_RELATIVE_PATHS = (
    CHECKER_REL,
    TESTS_REL,
    SUMMARY_REL,
)
PRODUCTION = REPO_ROOT / PRODUCTION_REL
DERIVED_ROOT = REPO_ROOT / STAGE
MAX_BYTES = 100 * 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
FORBIDDEN_SUFFIXES = {
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".tmp",
    ".part",
}
STAGE_TOKEN = (
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_v1"
)
PRODUCTION_SHA256 = (
    "a2c5f5a20778d799acd04e75ac1a3cd3f920597cca613a2e5f2918ab4ee538de"
)
EXPECTED_DERIVED_SHA256 = {
    IMPLEMENTATION_NAME: (
        "a7824a8f09ec3aa824d503c789c1165a2678adc1a6cfb962ec394eb6ba49b161"
    ),
    ERROR_RESULT_NAME: (
        "62540ba89f434a1527b60d547debb63592b285d2d317390a6c8ee3b2284e8c7d"
    ),
    TRUTH_NAME: (
        "f111c928be3a45eaa5a841a41cd0e18300c5e07fbed5bd684a1b5dfba3538821"
    ),
    PROTECTED_NAME: (
        "8f83cad89c8b2cb3306b722cf8926baa241f158eb553f0ced682cdd45a92b24e"
    ),
    ISSUES_NAME: (
        "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d"
    ),
}
SOURCE_BOUNDARY = (
    (
        Path(
            "src/covalent_ext/"
            "covapie_bulk_download_admission_unified_dispatch_runtime_"
            "with_admit_001_to_015.py"
        ),
        "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
        "100644",
        "5f3c17a80fad6c84bb0a69506260e18bafe2e488",
    ),
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_bulk_download_admission_unified_dispatch_runtime_"
            "with_admit_001_to_015_v1/"
            "covapie_admit_001_to_015_runtime_manifest.json"
        ),
        "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
        "100644",
        "78b54694a31225f7eb8499e0e618bfc79aa43896",
    ),
    (
        Path(
            "src/covalent_ext/"
            "covapie_bulk_download_admission_admit_015_mandatory_"
            "training_authorization_enforcement_contract_design_gate.py"
        ),
        "6acee7df5d64a1362e66646964bc6965a1ee5ffd3ac088fe81df056ea9ce1d46",
        "100644",
        "5233f10f5ae24f1a2d85ab58937e82810c452334",
    ),
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_bulk_download_admission_admit_015_mandatory_"
            "training_authorization_enforcement_contract_v1/"
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_contract_manifest.json"
        ),
        "d1300557d62d845fd40f62992baee3784bb0b8bb33c560e7fa7f656245528171",
        "100644",
        "ce8f726abc02167f9ec826649351eb3717522aca",
    ),
    (
        PREDECESSOR_ISSUES_REL,
        "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d",
        "100644",
        "f943bbf155b36d26f6053470e017d238f3ead2d3",
    ),
)
PUBLIC_MARKER = (
    "# === CovaPIE ADMIT_015 MANDATORY TRAINING AUTHORIZATION "
    "ENFORCEMENT PUBLIC CLOSURE END ==="
)
ERROR_FIELDS = (
    "schema_version",
    "error_code",
    "admission_rule_id",
    "reason",
)
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
ERROR_CODES = (
    "ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED",
    "ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID",
    "ADMIT_015_TRAINING_AUTHORIZATION_DENIED",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN",
)
PROTECTED_ACTIONS = (
    ("TRAIN_ACTION_001", "dataloader instantiation"),
    ("TRAIN_ACTION_002", "checkpoint loading"),
    ("TRAIN_ACTION_003", "model initialization"),
    ("TRAIN_ACTION_004", "model forward"),
    ("TRAIN_ACTION_005", "loss computation"),
    ("TRAIN_ACTION_006", "backward"),
    ("TRAIN_ACTION_007", "optimizer creation"),
    ("TRAIN_ACTION_008", "scheduler creation"),
    ("TRAIN_ACTION_009", "parameter update"),
    ("TRAIN_ACTION_010", "checkpoint write"),
    ("TRAIN_ACTION_011", "training-result materialization"),
)


IMPLEMENTATION_COLUMNS = (
    "contract_order",
    "contract_group",
    "contract_item",
    "frozen_value",
    "implementation_status",
    "contract_passed",
)
ERROR_RESULT_COLUMNS = (
    "case_order",
    "contract_group",
    "case_id",
    "expected_behavior",
    "error_code",
    "reachability",
    "result_identity_preserved",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "expected_decision",
    "observed_decision",
    "error_code",
    "runtime_call_count",
    "selected_rule_id",
    "candidate_identity_preserved",
    "stage_identity_preserved",
    "contexts_none",
    "protected_action_count",
    "current_permission",
    "authorized_execution_count",
    "case_passed",
)
PROTECTED_COLUMNS = (
    "action_order",
    "action_id",
    "action_semantic_name",
    "implementation_call_count",
    "blocked_call_count",
    "canonical_pass_call_count",
    "guard_only_in_memory",
    "no_training_integration",
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


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _identity(item: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


def _strict_json(content: bytes) -> dict[str, Any]:
    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(content, object_pairs_hook=pairs_hook)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("manifest JSON invalid") from error
    if type(value) is not dict:
        raise ValueError("manifest root requires exact object")
    return value


def _csv_rows(
    content: bytes,
    columns: Sequence[str],
) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("CSV encoding invalid") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise ValueError("CSV header drift")
    rows = [dict(row) for row in reader]
    if any(
        tuple(row) != tuple(columns)
        or None in row
        or any(type(value) is not str for value in row.values())
        for row in rows
    ):
        raise ValueError("CSV row schema/type drift")
    return rows


def _csv_bytes(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if (
            tuple(row) != tuple(columns)
            or any(type(value) is not str for value in row.values())
        ):
            raise ValueError("local expected CSV row drift")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _assert_recursive_exact(
    actual: Any,
    expected: Any,
    path: str = "$",
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{path}: exact type drift")
    if type(expected) is dict:
        if tuple(actual) != tuple(expected):
            raise ValueError(f"{path}: key inventory/order drift")
        for key in expected:
            _assert_recursive_exact(actual[key], expected[key], f"{path}.{key}")
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValueError(f"{path}: list length drift")
        for index, (left, right) in enumerate(
            zip(actual, expected, strict=True)
        ):
            _assert_recursive_exact(left, right, f"{path}[{index}]")
        return
    if actual != expected:
        raise ValueError(f"{path}: scalar drift")


def _row(
    columns: Sequence[str],
    values: Sequence[str],
) -> dict[str, str]:
    if (
        len(columns) != len(values)
        or any(type(value) is not str for value in values)
    ):
        raise ValueError("local row construction drift")
    return dict(zip(columns, values, strict=True))


def _expected_implementation_rows() -> list[dict[str, str]]:
    specifications = (
        ("identity", "public_function", "require_admit_015_training_authorization", "implemented"),
        ("identity", "public_signature", "candidate_record positional-or-keyword; stage_authorization_context keyword-only", "implemented"),
        ("identity", "return_type", "UnifiedAdmissionRuleEvaluation", "implemented"),
        ("identity", "error_type", "Admit015TrainingAuthorizationEnforcementError", "implemented"),
        ("identity", "error_schema", "covapie_admit_015_training_authorization_enforcement_error_v1", "implemented"),
        ("identity", "error_fields", "schema_version|error_code|admission_rule_id|reason", "implemented"),
        ("identity", "error_field_types", "exact built-in str|str|str|str", "implemented"),
        ("dependency", "direct_production_dependency", "current committed Exact15 runtime only", "implemented"),
        ("runtime", "selected_rule_id", "ADMIT_015", "implemented"),
        ("runtime", "dispatcher_call_sites", "1", "implemented"),
        ("runtime", "dispatcher_calls_per_invocation", "exactly 1", "implemented"),
        ("routing", "candidate_record", "same object without guard access", "implemented"),
        ("routing", "batch_context", "None", "implemented"),
        ("routing", "evaluation_context", "None", "implemented"),
        ("routing", "download_result_context", "None", "implemented"),
        ("routing", "stage_authorization_context", "same object without guard access", "implemented"),
        ("validation", "result_exact_type", "no subclass", "implemented"),
        ("validation", "result_storage", "exact dict and Exact13 order", "implemented"),
        ("validation", "dataclass_fields", "Exact13 order", "implemented"),
        ("validation", "top_level_types", "exact str/bool/tuple contract", "implemented"),
        ("validation", "reconstruction", "equal exact result", "implemented"),
        ("validation", "pass_invariants", "complete frozen Exact13 pass contract", "implemented"),
        ("behavior", "canonical_pass_return", "original result identity", "implemented"),
        ("behavior", "dispatcher_exception", "raise DISPATCH_FAILED", "implemented"),
        ("behavior", "wrong_type_or_subclass", "raise RESULT_INVALID", "implemented"),
        ("behavior", "exact_type_nonpass_or_drift", "raise DENIED", "implemented"),
        ("behavior", "error_reason", "deterministic error_code with no exception leak", "implemented"),
        ("forbidden", "external_dispatcher_injection", "rejected by exact signature", "implemented"),
        ("forbidden", "precomputed_result_or_permission", "rejected by exact signature", "implemented"),
        ("forbidden", "combined_verdict_or_admit014_permission", "rejected by exact signature", "implemented"),
        ("forbidden", "retry_loop_recursion_fallback", "absent", "implemented"),
        ("boundary", "training_orchestrator_integration", "false", "not_implemented"),
        ("boundary", "protected_action_execution_count", "0", "not_executed"),
        ("boundary", "combined_permission_or_cross_rule_aggregation", "false", "not_implemented"),
        ("boundary", "feature_semantics_resolution", "false", "not_resolved"),
        ("status", "mandatory_training_authorization_enforcement_api_frozen", "true", "implemented"),
        ("status", "mandatory_training_authorization_enforcement_implemented", "true", "implemented"),
        ("status", "ready_for_combined_permission_semantics_contract_design", "true", "ready"),
    )
    return [
        _row(
            IMPLEMENTATION_COLUMNS,
            (
                str(index),
                group,
                item,
                value,
                status,
                "true",
            ),
        )
        for index, (group, item, value, status) in enumerate(
            specifications,
            1,
        )
    ]


def _expected_error_result_rows() -> list[dict[str, str]]:
    specifications = [
        (
            "canonical_result",
            "canonical_return",
            "return exact runtime result",
            "",
            "reachable",
            "true",
        ),
    ]
    mapping_cases = (
        ("dispatcher_failure", ERROR_CODES[0]),
        ("wrong_result_type", ERROR_CODES[1]),
        ("result_subclass", ERROR_CODES[1]),
        ("exact13_field_order_drift", ERROR_CODES[2]),
        ("dataclass_field_order_drift", ERROR_CODES[2]),
        ("top_level_field_type_drift", ERROR_CODES[2]),
        ("reconstruction_drift", ERROR_CODES[2]),
        ("schema_drift", ERROR_CODES[2]),
        ("rule_drift", ERROR_CODES[2]),
        ("outcome_drift", ERROR_CODES[2]),
        ("passed_drift", ERROR_CODES[2]),
        ("blocks_drift", ERROR_CODES[2]),
        ("reason_drift", ERROR_CODES[2]),
        ("normalized_drift", ERROR_CODES[2]),
        ("validated_candidate_field_drift", ERROR_CODES[2]),
        ("consumed_candidate_field_drift", ERROR_CODES[2]),
        ("consumed_context_drift", ERROR_CODES[2]),
        ("evaluator_io_drift", ERROR_CODES[2]),
        ("adapter_drift", ERROR_CODES[2]),
    )
    specifications.extend(
        (
            "error_mapping",
            case_id,
            "raise fail closed",
            error_code,
            "reachable",
            "not_applicable",
        )
        for case_id, error_code in mapping_cases
    )
    specifications.extend(
        (
            "error_object",
            case_id,
            behavior,
            "",
            "reachable",
            "not_applicable",
        )
        for case_id, behavior in (
            ("exact_class", "exact class"),
            ("frozen_dataclass", "frozen"),
            (
                "exact_field_order",
                "schema_version|error_code|admission_rule_id|reason",
            ),
            ("exact_field_types", "exact built-in str only"),
            (
                "fixed_schema_and_rule",
                "covapie error schema and ADMIT_015",
            ),
            ("deterministic_reason", "reason equals error_code"),
            (
                "no_original_exception_message",
                "dispatcher detail not retained",
            ),
        )
    )
    for index, (case_id, error_code) in enumerate(
        (
            ("dispatch_failed", ERROR_CODES[0]),
            ("result_invalid", ERROR_CODES[1]),
            ("denied", ERROR_CODES[2]),
            ("replay_forbidden", ERROR_CODES[3]),
            ("repeated_call_forbidden", ERROR_CODES[4]),
            ("override_forbidden", ERROR_CODES[5]),
        )
    ):
        specifications.append(
            (
                "error_vocabulary",
                case_id,
                "frozen",
                error_code,
                (
                    "reachable"
                    if index < 3
                    else "reserved_unreachable_by_exact_public_signature"
                ),
                "not_applicable",
            )
        )
    return [
        _row(
            ERROR_RESULT_COLUMNS,
            (str(index), *specification, "true"),
        )
        for index, specification in enumerate(specifications, 1)
    ]


def _expected_truth_rows() -> list[dict[str, str]]:
    specifications = (
        ("canonical_pass", "return_original_result", "return_original_result", "", "1", "ADMIT_015", "true", "true", "true"),
        ("false_authorization", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[2], "1", "ADMIT_015", "true", "true", "true"),
        ("missing_stage_context", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[2], "1", "ADMIT_015", "true", "true", "true"),
        ("invalid_candidate", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[2], "1", "ADMIT_015", "true", "true", "true"),
        ("dispatcher_exception", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[0], "1", "ADMIT_015", "true", "true", "true"),
        ("wrong_result_type", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[1], "1", "ADMIT_015", "true", "true", "true"),
        ("result_subclass", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[1], "1", "ADMIT_015", "true", "true", "true"),
        ("exact_result_drift", "raise_fail_closed", "raise_fail_closed", ERROR_CODES[2], "1", "ADMIT_015", "true", "true", "true"),
        ("candidate_probe_not_read", "return_original_result", "return_original_result", "", "1", "ADMIT_015", "true", "true", "true"),
        ("stage_identity", "return_original_result", "return_original_result", "", "1", "ADMIT_015", "true", "true", "true"),
        ("exactly_one_call", "one_runtime_call", "one_runtime_call", "", "1", "ADMIT_015", "true", "true", "true"),
        ("original_result_identity", "return_same_object", "return_same_object", "", "1", "ADMIT_015", "true", "true", "true"),
        ("batch_context_none", "route_none", "route_none", "", "1", "ADMIT_015", "true", "true", "true"),
        ("evaluation_context_none", "route_none", "route_none", "", "1", "ADMIT_015", "true", "true", "true"),
        ("download_result_context_none", "route_none", "route_none", "", "1", "ADMIT_015", "true", "true", "true"),
        ("unexpected_precomputed_result", "python_type_error_before_dispatch", "python_type_error_before_dispatch", "", "0", "", "not_applicable", "not_applicable", "not_applicable"),
        ("unexpected_combined_verdict", "python_type_error_before_dispatch", "python_type_error_before_dispatch", "", "0", "", "not_applicable", "not_applicable", "not_applicable"),
        ("unexpected_admit014_permission", "python_type_error_before_dispatch", "python_type_error_before_dispatch", "", "0", "", "not_applicable", "not_applicable", "not_applicable"),
        ("unexpected_dispatcher", "python_type_error_before_dispatch", "python_type_error_before_dispatch", "", "0", "", "not_applicable", "not_applicable", "not_applicable"),
        ("no_protected_action_execution", "all_exact11_counts_zero", "all_exact11_counts_zero", "", "1", "ADMIT_015", "true", "true", "true"),
        ("synthetic_pass_permission_count_unchanged", "false_and_zero", "false_and_zero", "", "1", "ADMIT_015", "true", "true", "true"),
        ("no_retry_loop", "one_call_site_and_one_call", "one_call_site_and_one_call", "", "1", "ADMIT_015", "true", "true", "true"),
        ("no_combined_or_admit014_branch", "absent", "absent", "", "1", "ADMIT_015", "true", "true", "true"),
    )
    return [
        _row(
            TRUTH_COLUMNS,
            (
                str(index),
                *specification,
                "0",
                "false",
                "0",
                "true",
            ),
        )
        for index, specification in enumerate(specifications, 1)
    ]


def _expected_protected_rows() -> list[dict[str, str]]:
    return [
        _row(
            PROTECTED_COLUMNS,
            (
                str(index),
                action_id,
                semantic,
                "0",
                "0",
                "0",
                "true",
                "true",
                "true",
            ),
        )
        for index, (action_id, semantic) in enumerate(PROTECTED_ACTIONS, 1)
    ]


def _expected_manifest(
    support_file_sha256: Mapping[str, str],
) -> dict[str, Any]:
    support_paths = tuple(
        relative.as_posix() for relative in SUPPORT_RELATIVE_PATHS
    )
    if (
        type(support_file_sha256) is not dict
        or tuple(support_file_sha256) != support_paths
        or any(
            type(digest) is not str
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            for digest in support_file_sha256.values()
        )
    ):
        raise ValueError("support-file SHA256 inventory/type/order drift")
    output_prefix = f"{STAGE.as_posix()}/"
    expected: dict[str, Any] = {
        "all_checks_passed": True,
        "authorized_admit_015_training_execution_count": 0,
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": "4a3e813912cf704a1c6508ab21cd198e911b6b3c",
            "subject": (
                "add CovaPIE ADMIT_015 mandatory training authorization "
                "enforcement contract v1"
            ),
            "tree": "0ba4bc65f523564717c609d8cfd8b77ad2821201",
        },
        "canonical_evidence_runtime": {
            "implementation": "cpython",
            "pytest_version": "9.1.0",
            "version": "3.10.4",
        },
        "canonical_mask_count": 5,
        "canonical_mask_long_names_are_authoritative": True,
        "canonical_masks": [
            {"alias": "A", "semantic_name": "warhead_only"},
            {"alias": "B", "semantic_name": "linker_plus_warhead"},
            {"alias": "B2", "semantic_name": "scaffold_plus_warhead"},
            {"alias": "B3", "semantic_name": "scaffold_only"},
            {
                "alias": "C",
                "semantic_name": "scaffold_plus_linker_plus_warhead",
            },
        ],
        "current_permission": False,
        "derived_file_count": 6,
        "error_contract": {
            "admission_rule_id": "ADMIT_015",
            "error_codes": list(ERROR_CODES),
            "fields": list(ERROR_FIELDS),
            "field_types": ["str", "str", "str", "str"],
            "reachable_error_codes": list(ERROR_CODES[:3]),
            "reason_equals_error_code": True,
            "reserved_unreachable_by_exact_public_signature": list(
                ERROR_CODES[3:]
            ),
            "schema_version": (
                "covapie_admit_015_training_authorization_"
                "enforcement_error_v1"
            ),
            "type": "Admit015TrainingAuthorizationEnforcementError",
        },
        "exact10_file_count": 10,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "historical UNKNOWN_ATOM_FEATURE_POLICY and "
            "feature_semantics_known=False remain unresolved"
        ),
        "issue_continuity": {
            "byte_identical_to_predecessor": True,
            "remaining_required_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
                (
                    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_"
                    "SEMANTICS_UNRESOLVED"
                ),
            ],
            "row_count": 30,
            "sha256": EXPECTED_DERIVED_SHA256[ISSUES_NAME],
            "transition_count": 0,
        },
        "manifest_schema_version": (
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_manifest_v1"
        ),
        "output_sha256": {
            output_prefix + ERROR_RESULT_NAME: (
                EXPECTED_DERIVED_SHA256[ERROR_RESULT_NAME]
            ),
            output_prefix + IMPLEMENTATION_NAME: (
                EXPECTED_DERIVED_SHA256[IMPLEMENTATION_NAME]
            ),
            output_prefix + ISSUES_NAME: (
                EXPECTED_DERIVED_SHA256[ISSUES_NAME]
            ),
            output_prefix + PROTECTED_NAME: (
                EXPECTED_DERIVED_SHA256[PROTECTED_NAME]
            ),
            output_prefix + TRUTH_NAME: (
                EXPECTED_DERIVED_SHA256[TRUTH_NAME]
            ),
            SUMMARY_REL.as_posix(): support_file_sha256[
                SUMMARY_REL.as_posix()
            ],
            CHECKER_REL.as_posix(): support_file_sha256[
                CHECKER_REL.as_posix()
            ],
            PRODUCTION_REL.as_posix(): PRODUCTION_SHA256,
            TESTS_REL.as_posix(): support_file_sha256[
                TESTS_REL.as_posix()
            ],
        },
        "output_sha256_excludes_manifest_self_hash": True,
        "pass_invariants": {
            "adapter_id": "covapie_admit_015_unified_adapter_v1",
            "admission_rule_id": "ADMIT_015",
            "blocks_candidate": False,
            "consumed_candidate_fields": [],
            "consumed_context_items": [
                "current_stage_training_authorized"
            ],
            "evaluator_io_used": False,
            "exact_result_type": (
                "UnifiedAdmissionRuleEvaluation_no_subclass"
            ),
            "field_order": list(RESULT_FIELDS),
            "normalized_values": [
                ["current_stage_training_authorized", "true"]
            ],
            "outcome": "passed",
            "passed": True,
            "reason": "",
            "reconstruction_equality_required": True,
            "schema_version": (
                "covapie_unified_admission_rule_evaluation_v1"
            ),
            "validated_candidate_fields": [],
            "vars_exact_dict_required": True,
        },
        "precondition_transition": {
            "complete_count": 41,
            "implementation_blocking_count": 4,
            "incomplete_count": 4,
            "remaining_open_precondition_ids": [
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
            "resolved_precondition_ids": ["PRE_034"],
            "row_count": 45,
            "supported_but_not_frozen_count": 0,
        },
        "production_contract": {
            "candidate_record_accessed_by_guard": False,
            "combined_verdict_accepted": False,
            "dispatcher_call_site_count": 1,
            "dispatcher_calls_per_invocation": 1,
            "dispatcher_injection_accepted": False,
            "download_result_context": None,
            "evaluation_context": None,
            "exact_signature": (
                "require_admit_015_training_authorization("
                "candidate_record: Mapping[str, object], *, "
                "stage_authorization_context: Mapping[str, object] | None"
                ") -> UnifiedAdmissionRuleEvaluation"
            ),
            "precomputed_result_accepted": False,
            "public_function_name": (
                "require_admit_015_training_authorization"
            ),
            "return_original_result_identity": True,
            "runtime_dependency": (
                "covapie_bulk_download_admission_unified_dispatch_"
                "runtime_with_admit_001_to_015.evaluate_admission_rule"
            ),
            "selected_rule_id": "ADMIT_015",
            "stage_authorization_context_accessed_by_guard": False,
            "stage_authorization_context_same_identity": True,
            "batch_context": None,
        },
        "project": "CovaPIE",
        "protected_action_count": 11,
        "protected_actions": [
            {
                "action_id": action_id,
                "call_count": 0,
                "semantic_name": semantic,
            }
            for action_id, semantic in PROTECTED_ACTIONS
        ],
        "readiness": {
            "combined_candidate_verdict_implemented": False,
            "combined_permission_semantics_frozen": False,
            "cross_rule_aggregation_implemented": False,
            "feature_semantics_audit_completed": False,
            "historical_feature_semantics_known": False,
            "historical_unknown_atom_feature_policy_resolved": False,
            "mandatory_training_authorization_enforcement_api_frozen": True,
            "mandatory_training_authorization_enforcement_implemented": True,
            "ready_for_combined_permission_semantics_contract_design": True,
            "ready_for_training": False,
            "real_training_ready": False,
            "training_orchestrator_integration_implemented": False,
        },
        "recommended_next_step": (
            "design_covapie_combined_permission_semantics_contract_v1"
        ),
        "scope": {
            "checkpoint_or_training_io": False,
            "combined_candidate_verdict": False,
            "combined_permission_semantics": False,
            "cross_rule_aggregation": False,
            "feature_semantics_resolution": False,
            "protected_action_execution": False,
            "real_training": False,
            "standalone_pure_in_memory_guard": True,
            "training_orchestrator_integration": False,
        },
        "source_boundary_sha256": {
            PREDECESSOR_ISSUES_REL.as_posix(): (
                "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d"
            ),
            (
                "data/derived/covalent_small/"
                "covapie_bulk_download_admission_admit_015_mandatory_"
                "training_authorization_enforcement_contract_v1/"
                "covapie_admit_015_mandatory_training_authorization_"
                "enforcement_contract_manifest.json"
            ): (
                "d1300557d62d845fd40f62992baee3784bb0b8bb33c560e7fa7f656245528171"
            ),
            (
                "data/derived/covalent_small/"
                "covapie_bulk_download_admission_unified_dispatch_"
                "runtime_with_admit_001_to_015_v1/"
                "covapie_admit_001_to_015_runtime_manifest.json"
            ): (
                "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3"
            ),
            (
                "src/covalent_ext/"
                "covapie_bulk_download_admission_admit_015_mandatory_"
                "training_authorization_enforcement_contract_design_gate.py"
            ): (
                "6acee7df5d64a1362e66646964bc6965a1ee5ffd3ac088fe81df056ea9ce1d46"
            ),
            (
                "src/covalent_ext/"
                "covapie_bulk_download_admission_unified_dispatch_"
                "runtime_with_admit_001_to_015.py"
            ): (
                "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1"
            ),
        },
        "stage": STAGE.name,
        "step": (
            "ADMIT_015 mandatory training authorization enforcement v1"
        ),
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "synthetic_canonical_pass_changes_current_permission": False,
        "synthetic_canonical_pass_increments_authorized_execution_count": (
            False
        ),
        "validation_failures": [],
    }
    return expected


def _read_all(descriptor: int, maximum: int = MAX_BYTES) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            break
        total += len(chunk)
        if total > maximum:
            raise ValueError("pinned read exceeds maximum")
        chunks.append(chunk)
    return b"".join(chunks)


def read_exact6_no_follow(
    root: Path = DERIVED_ROOT,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> dict[str, bytes]:
    """Read the Exact6 through held no-follow descriptors and final bindings."""
    root = Path(os.path.abspath(root))
    parent = root.parent
    callback = (lambda event, path: None) if hook is None else hook
    parent_item = os.lstat(parent)
    root_item = os.lstat(root)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("Exact6 parent/root unsafe")
    parent_identity = _identity(parent_item)
    root_identity = _identity(root_item)
    callback("after_initial_lstat", root)
    parent_fd = os.open(parent, DIR_FLAGS)
    root_fd: int | None = None
    descriptors: dict[str, int] = {}
    identities: dict[str, tuple[int, int, int, int, int, int]] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("Exact6 parent stat/open race")
        root_fd = os.open(root.name, DIR_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("Exact6 root stat/open race")
        callback("after_root_open", root)

        def inventory(reason: str) -> tuple[str, ...]:
            names = tuple(sorted(os.listdir(root_fd)))
            if names != tuple(sorted(DERIVED_NAMES)):
                raise ValueError(reason)
            return names

        def assert_parent_root(reason: str) -> None:
            try:
                lexical_root = os.stat(
                    root.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except OSError as error:
                raise ValueError(reason) from error
            if (
                _identity(os.fstat(parent_fd)) != parent_identity
                or _identity(os.fstat(root_fd)) != root_identity
                or _identity(os.lstat(parent)) != parent_identity
                or _identity(os.lstat(root)) != root_identity
                or _identity(lexical_root) != root_identity
            ):
                raise ValueError(reason)

        def assert_all_leaves(reason: str) -> None:
            for name in DERIVED_NAMES:
                try:
                    lexical = os.stat(
                        name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                except OSError as error:
                    raise ValueError(reason) from error
                if (
                    _identity(lexical) != identities[name]
                    or _identity(os.fstat(descriptors[name]))
                    != identities[name]
                    or not stat.S_ISREG(lexical.st_mode)
                    or stat.S_ISLNK(lexical.st_mode)
                ):
                    raise ValueError(reason)

        assert_parent_root("Exact6 initial parent/root drift")
        initial_inventory = inventory("Exact6 inventory is not exact")
        for name in DERIVED_NAMES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > MAX_BYTES
                or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
            ):
                raise ValueError("Exact6 leaf unsafe")
            identities[name] = _identity(item)
            descriptor = os.open(
                name,
                READ_FLAGS,
                dir_fd=root_fd,
            )
            descriptors[name] = descriptor
            if _identity(os.fstat(descriptor)) != identities[name]:
                raise ValueError("Exact6 leaf stat/open race")
        callback("after_leaf_open", root)
        payloads = {
            name: _read_all(descriptors[name]) for name in DERIVED_NAMES
        }
        assert_all_leaves("Exact6 first all-leaf drift")
        assert_parent_root("Exact6 first parent/root drift")
        if inventory("Exact6 second inventory drift") != initial_inventory:
            raise ValueError("Exact6 second inventory drift")
        callback("before_final_checks", root)
        assert_all_leaves("Exact6 final all-leaf drift")
        if inventory("Exact6 final inventory drift") != initial_inventory:
            raise ValueError("Exact6 final inventory drift")
        # Deliberately the last successful validation operation.
        assert_parent_root("Exact6 final parent/root binding drift")
        return payloads
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def _read_repo_relative_no_follow(root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("source relative path unsafe")
    root = Path(os.path.abspath(root))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("source repository root unsafe")
    root_fd = os.open(root, DIR_FLAGS)
    directory_fds = [root_fd]
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("source root stat/open race")
        parent_fd = root_fd
        bindings = []
        for component in relative.parts[:-1]:
            item = os.stat(
                component,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            identity = _identity(item)
            if (
                not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("source path component unsafe")
            child_fd = os.open(component, DIR_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != identity:
                os.close(child_fd)
                raise ValueError("source component stat/open race")
            directory_fds.append(child_fd)
            bindings.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd
        leaf = relative.name
        item = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        identity = _identity(item)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
        ):
            raise ValueError("source leaf unsafe")
        descriptor = os.open(leaf, READ_FLAGS, dir_fd=parent_fd)
        try:
            if _identity(os.fstat(descriptor)) != identity:
                raise ValueError("source leaf stat/open race")
            content = _read_all(descriptor)
            if (
                _identity(os.fstat(descriptor)) != identity
                or _identity(
                    os.stat(
                        leaf,
                        dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                )
                != identity
            ):
                raise ValueError("source leaf final drift")
        finally:
            os.close(descriptor)
        for lexical_parent, name, child_fd, expected in reversed(bindings):
            if (
                _identity(os.fstat(child_fd)) != expected
                or _identity(
                    os.stat(
                        name,
                        dir_fd=lexical_parent,
                        follow_symlinks=False,
                    )
                )
                != expected
            ):
                raise ValueError("source component final drift")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("source repository root final drift")
        return content
    finally:
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def read_support_file_sha256(root: Path = REPO_ROOT) -> dict[str, str]:
    return {
        relative.as_posix(): _sha(
            _read_repo_relative_no_follow(root, relative)
        )
        for relative in SUPPORT_RELATIVE_PATHS
    }


def _git_result(
    root: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _strict_head(root: Path) -> str:
    result = _git_result(root, "rev-parse", "--verify", "HEAD^{commit}")
    if result.returncode:
        raise ValueError("HEAD commit query failed")
    try:
        value = result.stdout.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("HEAD commit encoding drift") from error
    if re.fullmatch(r"[0-9a-f]{40}\n", value) is None:
        raise ValueError("HEAD commit malformed")
    return value[:-1]


class SourceAttestation(NamedTuple):
    relative_path: Path
    sha256: str
    base_mode: str
    base_blob: str
    index_mode: str
    index_blob: str
    index_stage: int
    content: bytes


def _parse_tree_entry(
    content: bytes,
    relative: Path,
) -> tuple[str, str]:
    try:
        metadata, path = content.decode("utf-8").rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if (
        path != relative.as_posix()
        or kind != "blob"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("tree entry identity drift")
    return mode, blob


def _parse_index_entry(
    content: bytes,
    relative: Path,
) -> tuple[str, str, int]:
    try:
        metadata, path = content.decode("utf-8").rstrip("\n").split("\t", 1)
        mode, blob, stage = metadata.split(" ")
        stage_number = int(stage)
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if (
        path != relative.as_posix()
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("index entry identity drift")
    return mode, blob, stage_number


def attest_committed_sources(
    root: Path = REPO_ROOT,
    *,
    base: str = BASE_COMMIT,
) -> tuple[SourceAttestation, ...]:
    root = Path(os.path.abspath(root))
    initial_head = _strict_head(root)
    if _git_result(
        root,
        "merge-base",
        "--is-ancestor",
        base,
        initial_head,
    ).returncode:
        raise ValueError("source base is not initial HEAD ancestor")
    records = []
    for relative, expected_sha, expected_mode, expected_blob in SOURCE_BOUNDARY:
        tree_result = _git_result(
            root,
            "ls-tree",
            base,
            "--",
            relative.as_posix(),
        )
        index_result = _git_result(
            root,
            "ls-files",
            "--stage",
            "--",
            relative.as_posix(),
        )
        if tree_result.returncode or index_result.returncode:
            raise ValueError("source Git query failed")
        tree_mode, tree_blob = _parse_tree_entry(
            tree_result.stdout,
            relative,
        )
        index_mode, index_blob, index_stage = _parse_index_entry(
            index_result.stdout,
            relative,
        )
        if (
            tree_mode != expected_mode
            or tree_blob != expected_blob
            or index_mode != expected_mode
            or index_blob != expected_blob
            or index_stage != 0
        ):
            raise ValueError("source tree/index attestation drift")
        blob_result = _git_result(root, "cat-file", "blob", expected_blob)
        if blob_result.returncode:
            raise ValueError("source Git blob read failed")
        filesystem = _read_repo_relative_no_follow(root, relative)
        if (
            blob_result.stdout != filesystem
            or _sha(filesystem) != expected_sha
        ):
            raise ValueError("source Git/filesystem/SHA drift")
        records.append(
            SourceAttestation(
                relative,
                expected_sha,
                tree_mode,
                tree_blob,
                index_mode,
                index_blob,
                index_stage,
                filesystem,
            )
        )
    final_head = _strict_head(root)
    if (
        final_head != initial_head
        or _git_result(
            root,
            "merge-base",
            "--is-ancestor",
            base,
            final_head,
        ).returncode
    ):
        raise ValueError("source HEAD/ancestry final drift")
    return tuple(records)


def _canonical_result():
    return exact15_runtime.UnifiedAdmissionRuleEvaluation(
        schema_version="covapie_unified_admission_rule_evaluation_v1",
        admission_rule_id="ADMIT_015",
        admission_rule_name="current_gate_grants_no_training_permission",
        outcome="passed",
        passed=True,
        blocks_candidate=False,
        reason="",
        normalized_values=(
            ("current_stage_training_authorized", "true"),
        ),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=("current_stage_training_authorized",),
        evaluator_io_used=False,
        adapter_id="covapie_admit_015_unified_adapter_v1",
    )


def _assert_error(error: object, code: str) -> None:
    if (
        type(error)
        is not enforcement.Admit015TrainingAuthorizationEnforcementError
        or tuple(vars(error)) != ERROR_FIELDS
        or tuple(field.name for field in fields(type(error))) != ERROR_FIELDS
        or any(type(value) is not str for value in vars(error).values())
        or error.schema_version
        != "covapie_admit_015_training_authorization_enforcement_error_v1"
        or error.error_code != code
        or error.admission_rule_id != "ADMIT_015"
        or error.reason != code
        or "checker-secret" in repr(error)
        or "checker-secret" in str(error)
    ):
        raise ValueError("error contract drift")


def _check_signature_and_ast(production_bytes: bytes) -> None:
    signature = inspect.signature(
        enforcement.require_admit_015_training_authorization
    )
    parameters = tuple(signature.parameters.values())
    if (
        tuple(parameter.name for parameter in parameters)
        != ("candidate_record", "stage_authorization_context")
        or parameters[0].kind
        is not inspect.Parameter.POSITIONAL_OR_KEYWORD
        or parameters[1].kind is not inspect.Parameter.KEYWORD_ONLY
        or str(parameters[0].annotation) != "Mapping[str, object]"
        or str(parameters[1].annotation) != "Mapping[str, object] | None"
        or str(signature.return_annotation)
        != "UnifiedAdmissionRuleEvaluation"
    ):
        raise ValueError("public signature drift")

    if _sha(production_bytes) != PRODUCTION_SHA256:
        raise ValueError("production SHA drift")
    try:
        source = production_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("production encoding invalid") from error
    if source.count(PUBLIC_MARKER) != 1:
        raise ValueError("public closure marker drift")
    public_source, after_marker = source.split(PUBLIC_MARKER, 1)
    if after_marker.strip():
        raise ValueError("code found after public closure")
    tree = ast.parse(public_source)
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name
            == "require_admit_015_training_authorization"
        ),
        None,
    )
    if function is None:
        raise ValueError("public function missing")
    dispatch_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "exact15_runtime"
        and node.func.attr == "evaluate_admission_rule"
    ]
    if len(dispatch_calls) != 1:
        raise ValueError("dispatcher call-site count drift")
    if any(
        isinstance(node, (ast.For, ast.AsyncFor, ast.While))
        for node in ast.walk(function)
    ):
        raise ValueError("loop/retry forbidden")
    called_names = {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if (
        {"eval", "exec", "__import__"} & called_names
        or function.name in called_names
    ):
        raise ValueError("dynamic or recursive call forbidden")
    function_names = {
        node.id for node in ast.walk(function) if isinstance(node, ast.Name)
    }
    if {
        "combined_verdict",
        "admit014_permission",
        "precomputed_result",
        "dispatcher",
    } & function_names:
        raise ValueError("bypass branch forbidden")

    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
    if not imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "typing",
        "covalent_ext",
    }:
        raise ValueError("production import boundary drift")
    if imported_roots & {
        "torch",
        "numpy",
        "pytorch_lightning",
        "rdkit",
        "Bio",
        "gemmi",
        "requests",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
    }:
        raise ValueError("forbidden production import")


def _check_error_type() -> None:
    if (
        enforcement.ERROR_CODES != ERROR_CODES
        or tuple(
            field.name
            for field in fields(
                enforcement.Admit015TrainingAuthorizationEnforcementError
            )
        )
        != ERROR_FIELDS
    ):
        raise ValueError("Exact6 error vocabulary drift")
    error = enforcement.Admit015TrainingAuthorizationEnforcementError(
        enforcement.ERROR_SCHEMA_VERSION,
        ERROR_CODES[0],
        "ADMIT_015",
        ERROR_CODES[0],
    )
    _assert_error(error, ERROR_CODES[0])
    try:
        error.reason = "changed"
    except FrozenInstanceError:
        pass
    else:
        raise ValueError("error type is not frozen")

    class StringSubclass(str):
        pass

    for invalid in (True, 1, StringSubclass(ERROR_CODES[0])):
        try:
            enforcement.Admit015TrainingAuthorizationEnforcementError(
                enforcement.ERROR_SCHEMA_VERSION,
                invalid,
                "ADMIT_015",
                ERROR_CODES[0],
            )
        except TypeError:
            pass
        else:
            raise ValueError("non-exact string accepted")


def _check_dynamic_guard() -> None:
    original_dispatcher = exact15_runtime.evaluate_admission_rule
    candidate = object()
    stage = object()
    canonical = _canonical_result()
    calls = []

    def passing_dispatcher(admission_rule_id, candidate_record, **contexts):
        calls.append((admission_rule_id, candidate_record, contexts))
        return canonical

    exact15_runtime.evaluate_admission_rule = passing_dispatcher
    try:
        observed = enforcement.require_admit_015_training_authorization(
            candidate,
            stage_authorization_context=stage,
        )
        if observed is not canonical or len(calls) != 1:
            raise ValueError("pass identity or exactly-once drift")
        rule_id, routed_candidate, contexts = calls[0]
        if (
            rule_id != "ADMIT_015"
            or routed_candidate is not candidate
            or tuple(contexts)
            != (
                "batch_context",
                "evaluation_context",
                "download_result_context",
                "stage_authorization_context",
            )
            or contexts["batch_context"] is not None
            or contexts["evaluation_context"] is not None
            or contexts["download_result_context"] is not None
            or contexts["stage_authorization_context"] is not stage
        ):
            raise ValueError("routing contract drift")

        before = len(calls)
        for keyword in (
            "precomputed_result",
            "combined_verdict",
            "admit014_permission",
            "dispatcher",
        ):
            try:
                enforcement.require_admit_015_training_authorization(
                    {},
                    stage_authorization_context={},
                    **{keyword: object()},
                )
            except TypeError:
                pass
            else:
                raise ValueError("bypass keyword accepted")
        if len(calls) != before:
            raise ValueError("bypass keyword reached runtime")

        class ResultSubclass(
            exact15_runtime.UnifiedAdmissionRuleEvaluation
        ):
            pass

        subclass = ResultSubclass(*vars(canonical).values())

        def subclass_dispatcher(*args, **kwargs):
            return subclass

        exact15_runtime.evaluate_admission_rule = subclass_dispatcher
        try:
            enforcement.require_admit_015_training_authorization(
                {},
                stage_authorization_context={},
            )
        except Exception as error:
            _assert_error(error, ERROR_CODES[1])
        else:
            raise ValueError("result subclass accepted")

        drift = _canonical_result()
        object.__setattr__(drift, "adapter_id", "drift")

        def drift_dispatcher(*args, **kwargs):
            return drift

        exact15_runtime.evaluate_admission_rule = drift_dispatcher
        try:
            enforcement.require_admit_015_training_authorization(
                {},
                stage_authorization_context={},
            )
        except Exception as error:
            _assert_error(error, ERROR_CODES[2])
        else:
            raise ValueError("exact result drift accepted")

        def failing_dispatcher(*args, **kwargs):
            raise RuntimeError("checker-secret")

        exact15_runtime.evaluate_admission_rule = failing_dispatcher
        try:
            enforcement.require_admit_015_training_authorization(
                {},
                stage_authorization_context={},
            )
        except Exception as error:
            _assert_error(error, ERROR_CODES[0])
        else:
            raise ValueError("dispatcher exception accepted")
    finally:
        exact15_runtime.evaluate_admission_rule = original_dispatcher

    real_result = enforcement.require_admit_015_training_authorization(
        {},
        stage_authorization_context={
            "current_stage_training_authorized": True
        },
    )
    if (
        type(real_result)
        is not exact15_runtime.UnifiedAdmissionRuleEvaluation
        or real_result.passed is not True
    ):
        raise ValueError("real Exact15 synthetic pass failed")


def _verify_semantics(
    payloads: Mapping[str, bytes],
    source_records: Sequence[SourceAttestation],
    support_file_sha256: Mapping[str, str],
) -> dict[str, Any]:
    if (
        type(payloads) is not dict
        or tuple(payloads) != DERIVED_NAMES
        or any(type(value) is not bytes for value in payloads.values())
    ):
        raise ValueError("Exact6 payload inventory/type/order drift")
    for name, expected_sha256 in EXPECTED_DERIVED_SHA256.items():
        if _sha(payloads[name]) != expected_sha256:
            raise ValueError(f"checker-local frozen SHA drift: {name}")

    expected_csvs = (
        (
            IMPLEMENTATION_NAME,
            IMPLEMENTATION_COLUMNS,
            _expected_implementation_rows(),
        ),
        (
            ERROR_RESULT_NAME,
            ERROR_RESULT_COLUMNS,
            _expected_error_result_rows(),
        ),
        (TRUTH_NAME, TRUTH_COLUMNS, _expected_truth_rows()),
        (
            PROTECTED_NAME,
            PROTECTED_COLUMNS,
            _expected_protected_rows(),
        ),
    )
    for name, columns, expected_rows in expected_csvs:
        actual_rows = _csv_rows(payloads[name], columns)
        _assert_recursive_exact(actual_rows, expected_rows, f"$.{name}")

    issue_records = [
        record
        for record in source_records
        if record.relative_path == PREDECESSOR_ISSUES_REL
    ]
    if len(issue_records) != 1:
        raise ValueError("committed issue source attestation missing")
    issue_rows = _csv_rows(payloads[ISSUES_NAME], ISSUE_COLUMNS)
    if (
        len(issue_rows) != 30
        or payloads[ISSUES_NAME] != issue_records[0].content
    ):
        raise ValueError("Exact30 issue byte continuity drift")

    actual_manifest = _strict_json(payloads[MANIFEST_NAME])
    expected_manifest = _expected_manifest(support_file_sha256)
    _assert_recursive_exact(
        actual_manifest,
        expected_manifest,
        "$.manifest",
    )
    if (
        json.dumps(actual_manifest, indent=2, ensure_ascii=True).encode()
        + b"\n"
        != payloads[MANIFEST_NAME]
    ):
        raise ValueError("Manifest canonical serialization drift")
    return actual_manifest


def verify_artifacts(root: Path = REPO_ROOT) -> dict[str, Any]:
    source_records = attest_committed_sources(root)
    support_file_sha256 = read_support_file_sha256(root)
    production_bytes = _read_repo_relative_no_follow(root, PRODUCTION_REL)
    _check_signature_and_ast(production_bytes)
    _check_error_type()
    _check_dynamic_guard()
    payloads = read_exact6_no_follow(root / STAGE)
    manifest = _verify_semantics(
        payloads,
        source_records,
        support_file_sha256,
    )
    return {
        "manifest": manifest,
        "payloads": payloads,
        "source_records": source_records,
        "support_file_sha256": support_file_sha256,
    }


def _matches_stage_family(name: str) -> bool:
    return (
        STAGE_TOKEN in name
        or name == PRODUCTION_REL.name
        or name.startswith(STAGE.name)
    )


def _bounded_recursive_stage_inventory(
    root: Path,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> tuple[dict[Path, os.stat_result], tuple[Path, ...]]:
    root = Path(os.path.abspath(root))
    callback = (lambda event, path: None) if hook is None else hook
    observed: dict[Path, os.stat_result] = {}
    derived_roots: list[Path] = []
    fd_identities: dict[int, tuple[int, int, int, int, int, int]] = {}

    def stat_at(parent_fd: int, name: str, reason: str) -> os.stat_result:
        try:
            return os.stat(
                name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except OSError as error:
            raise ValueError(f"{reason} stat failed") from error

    def names(directory_fd: int, reason: str) -> tuple[str, ...]:
        try:
            return tuple(sorted(os.listdir(directory_fd)))
        except OSError as error:
            raise ValueError(f"{reason} inventory failed") from error

    def assert_directory(
        item: os.stat_result,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> None:
        if (
            _identity(item) != expected
            or not stat.S_ISDIR(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
        ):
            raise ValueError(f"{reason} directory binding drift")

    def open_directory(
        parent_fd: int,
        name: str,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> int:
        callback("before_top_root_open", Path(name))
        try:
            descriptor = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
        except OSError as error:
            raise ValueError(f"{reason} open failed") from error
        try:
            assert_directory(os.fstat(descriptor), expected, reason)
        except BaseException:
            os.close(descriptor)
            raise
        callback("after_top_root_open", Path(name))
        return descriptor

    def assert_child_binding(
        parent_fd: int,
        name: str,
        child_fd: int,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> None:
        assert_directory(
            os.fstat(parent_fd),
            fd_identities[parent_fd],
            reason,
        )
        assert_directory(stat_at(parent_fd, name, reason), expected, reason)
        assert_directory(os.fstat(child_fd), expected, reason)

    def scan_directory(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, int, int, int, int, int],
        *,
        observe_all: bool,
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "bounded scan")
        initial_names = names(directory_fd, "bounded scan initial")
        identities = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "bounded scan entry")
            identity = _identity(item)
            identities[name] = identity
            # Generic symlinks are rejected before any name filtering.
            if stat.S_ISLNK(item.st_mode):
                raise ValueError("bounded scan generic symlink rejected")
            relative = logical / name
            matched = observe_all or _matches_stage_family(name)
            if matched:
                observed[relative] = item
            if not stat.S_ISDIR(item.st_mode):
                continue
            child_fd = open_directory(
                directory_fd,
                name,
                identity,
                "bounded scan child",
            )
            fd_identities[child_fd] = identity
            try:
                scan_directory(
                    child_fd,
                    relative,
                    identity,
                    observe_all=matched,
                )
                assert_child_binding(
                    directory_fd,
                    name,
                    child_fd,
                    identity,
                    "bounded scan child post-recursion",
                )
            finally:
                fd_identities.pop(child_fd, None)
                os.close(child_fd)
        if names(directory_fd, "bounded scan final") != initial_names:
            raise ValueError("bounded scan inventory drift")
        assert_directory(os.fstat(directory_fd), expected, "bounded final")
        for name, identity in identities.items():
            item = stat_at(directory_fd, name, "bounded final entry")
            if _identity(item) != identity or stat.S_ISLNK(item.st_mode):
                raise ValueError("bounded scan entry identity drift")

    def scan_derived_parent(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, int, int, int, int, int],
    ) -> None:
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "derived parent",
        )
        initial_names = names(directory_fd, "derived parent initial")
        matching = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "derived parent entry")
            # This is intentionally before the matching-root filter.
            if stat.S_ISLNK(item.st_mode):
                raise ValueError("derived parent generic symlink rejected")
            if not name.startswith(STAGE.name):
                continue
            identity = _identity(item)
            if not stat.S_ISDIR(item.st_mode):
                raise ValueError("matching derived root unsafe")
            relative = logical / name
            matching[name] = identity
            derived_roots.append(relative)
            observed[relative] = item
            child_fd = open_directory(
                directory_fd,
                name,
                identity,
                "matching derived root",
            )
            fd_identities[child_fd] = identity
            try:
                scan_directory(
                    child_fd,
                    relative,
                    identity,
                    observe_all=True,
                )
                assert_child_binding(
                    directory_fd,
                    name,
                    child_fd,
                    identity,
                    "derived root post-recursion",
                )
            finally:
                fd_identities.pop(child_fd, None)
                os.close(child_fd)
        if names(directory_fd, "derived parent final") != initial_names:
            raise ValueError("derived parent inventory drift")
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "derived parent final",
        )
        for name, identity in matching.items():
            assert_directory(
                stat_at(directory_fd, name, "derived root final"),
                identity,
                "derived root final",
            )

    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("bounded repository root unsafe")
    callback("before_repository_root_open", root)
    root_fd = os.open(root, DIR_FLAGS)
    fd_identities[root_fd] = root_identity
    callback("after_repository_root_open", root)

    def with_open_path(relative: Path, *, derived: bool) -> None:
        parent_fd = root_fd
        descriptors = []
        bindings = []
        try:
            for component in relative.parts:
                item = stat_at(parent_fd, component, "bounded root component")
                identity = _identity(item)
                if (
                    not stat.S_ISDIR(item.st_mode)
                    or stat.S_ISLNK(item.st_mode)
                ):
                    raise ValueError("bounded root component unsafe")
                child_fd = open_directory(
                    parent_fd,
                    component,
                    identity,
                    "bounded root component",
                )
                descriptors.append(child_fd)
                bindings.append(
                    (parent_fd, component, child_fd, identity)
                )
                fd_identities[child_fd] = identity
                parent_fd = child_fd
            expected = fd_identities[parent_fd]
            if derived:
                scan_derived_parent(parent_fd, relative, expected)
            else:
                scan_directory(
                    parent_fd,
                    relative,
                    expected,
                    observe_all=False,
                )
            for lexical_parent, name, child_fd, identity in reversed(
                bindings
            ):
                assert_child_binding(
                    lexical_parent,
                    name,
                    child_fd,
                    identity,
                    "bounded root post-scan",
                )
        finally:
            for descriptor in reversed(descriptors):
                fd_identities.pop(descriptor, None)
                os.close(descriptor)

    try:
        assert_directory(
            os.fstat(root_fd),
            root_identity,
            "bounded repository root",
        )
        for relative in (
            Path("src/covalent_ext"),
            Path("scripts"),
            Path("tests"),
            Path("docs"),
        ):
            with_open_path(relative, derived=False)
        with_open_path(
            Path("data/derived/covalent_small"),
            derived=True,
        )
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("bounded repository root final drift")
        return observed, tuple(derived_roots)
    finally:
        fd_identities.pop(root_fd, None)
        os.close(root_fd)


def _assert_candidate_safe(
    root: Path,
    relative: Path,
    item: os.stat_result,
) -> None:
    ignored = _git_result(
        root,
        "check-ignore",
        "--no-index",
        "-q",
        "--",
        relative.as_posix(),
    )
    if ignored.returncode == 0:
        raise ValueError("same-stage candidate ignored")
    if ignored.returncode != 1:
        raise ValueError("same-stage check-ignore failed")
    if stat.S_ISLNK(item.st_mode):
        raise ValueError("same-stage symlink rejected")
    if relative == STAGE:
        if not stat.S_ISDIR(item.st_mode):
            raise ValueError("same-stage derived root unsafe")
        return
    if (
        not stat.S_ISREG(item.st_mode)
        or relative.suffix.lower() in FORBIDDEN_SUFFIXES
        or item.st_size > MAX_BYTES
    ):
        raise ValueError("same-stage leaf unsafe")


def assert_exact10_recursive_inventory(
    root: Path = REPO_ROOT,
    exact10: Sequence[Path] = EXACT10,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> None:
    observed, derived_roots = _bounded_recursive_stage_inventory(
        root,
        hook=hook,
    )
    for relative, item in observed.items():
        _assert_candidate_safe(root, relative, item)
    expected = {*exact10, STAGE}
    if set(observed) != expected:
        raise ValueError("same-stage recursive Exact10 inventory drift")
    if derived_roots != (STAGE,):
        raise ValueError("matching derived root inventory drift")
    derived_names = tuple(
        relative.name
        for relative in observed
        if relative.parent == STAGE
    )
    if len(derived_names) != 6 or set(derived_names) != set(DERIVED_NAMES):
        raise ValueError("same-stage Exact6 recursive inventory drift")


def _nul_paths(content: bytes, reason: str) -> tuple[str, ...]:
    try:
        values = tuple(
            value for value in content.decode("utf-8").split("\0") if value
        )
    except UnicodeDecodeError as error:
        raise ValueError(f"{reason} path encoding drift") from error
    if len(values) != len(set(values)):
        raise ValueError(f"{reason} duplicate path")
    return values


class LifecycleSnapshot(NamedTuple):
    head: str
    identities: tuple[tuple[str, tuple[int, ...]], ...]
    tracked: frozenset[str]
    untracked: frozenset[str]
    listed_untracked: tuple[str, ...]
    staged: tuple[str, ...]
    unstaged: tuple[str, ...]
    status: bytes
    full_index: bytes


def _capture_lifecycle_state(
    root: Path,
    ordered: Sequence[str],
    *,
    base: str,
) -> LifecycleSnapshot:
    head = _strict_head(root)
    if _git_result(
        root,
        "merge-base",
        "--is-ancestor",
        base,
        head,
    ).returncode:
        raise ValueError("lifecycle base is not HEAD ancestor")
    identities = []
    tracked = set()
    untracked = set()
    for relative in ordered:
        path = Path(relative)
        item = os.lstat(root / path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise ValueError("Exact10 lifecycle leaf unsafe")
        identities.append((relative, _identity(item)))
        ignored = _git_result(
            root,
            "check-ignore",
            "--no-index",
            "-q",
            "--",
            relative,
        )
        if ignored.returncode == 0:
            raise ValueError("Exact10 lifecycle leaf ignored")
        if ignored.returncode != 1:
            raise ValueError("lifecycle check-ignore failed")
        index = _git_result(root, "ls-files", "--stage", "--", relative)
        if index.returncode:
            raise ValueError("lifecycle index query failed")
        if index.stdout:
            mode, _, stage_number = _parse_index_entry(
                index.stdout,
                path,
            )
            if mode != "100644" or stage_number != 0:
                raise ValueError("Exact10 index mode/stage drift")
            tracked.add(relative)
        else:
            untracked.add(relative)
    commands = {
        "untracked": (
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ),
        "staged": ("diff", "--cached", "--name-only", "-z"),
        "unstaged": ("diff", "--name-only", "-z"),
        "status": (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
        "index": ("ls-files", "--stage", "-z"),
    }
    results = {
        name: _git_result(root, *arguments)
        for name, arguments in commands.items()
    }
    if any(result.returncode for result in results.values()):
        raise ValueError("lifecycle Git state query failed")
    listed_untracked = _nul_paths(
        results["untracked"].stdout,
        "untracked",
    )
    staged = _nul_paths(results["staged"].stdout, "staged")
    unstaged = _nul_paths(results["unstaged"].stdout, "unstaged")
    if staged or unstaged:
        raise ValueError("lifecycle repository staged/dirty")
    if tracked and untracked:
        raise ValueError("mixed tracked/untracked lifecycle")
    if set(listed_untracked) != untracked:
        raise ValueError("entire untracked inventory is not Exact10")
    return LifecycleSnapshot(
        head,
        tuple(identities),
        frozenset(tracked),
        frozenset(untracked),
        listed_untracked,
        staged,
        unstaged,
        results["status"].stdout,
        results["index"].stdout,
    )


def _assert_post_commit_history(
    root: Path,
    head: str,
    expected: set[str],
    base: str,
) -> None:
    changed = _git_result(
        root,
        "diff",
        "--name-only",
        "-z",
        f"{base}..{head}",
    )
    commits = _git_result(root, "rev-list", "--reverse", f"{base}..{head}")
    if changed.returncode or commits.returncode:
        raise ValueError("post-commit history query failed")
    if set(_nul_paths(changed.stdout, "candidate diff")) != expected:
        raise ValueError("candidate commit does not contain Exact10 only")
    commit_ids = tuple(commits.stdout.decode("ascii").splitlines())
    if not commit_ids or commit_ids[-1] != head:
        raise ValueError("candidate descendant chain drift")
    for commit in commit_ids:
        if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise ValueError("candidate commit malformed")
        delta = _git_result(
            root,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            commit,
        )
        if delta.returncode:
            raise ValueError("candidate commit delta query failed")
        paths = set(_nul_paths(delta.stdout, "candidate delta"))
        if not paths:
            raise ValueError("allow-empty HEAD/history drift")
        if not paths <= expected:
            raise ValueError("candidate commit out-of-scope history")
    tree = _git_result(
        root,
        "ls-tree",
        "-r",
        "-z",
        head,
        "--",
        *sorted(expected),
    )
    entries = tuple(entry for entry in tree.stdout.split(b"\0") if entry)
    if tree.returncode or len(entries) != 10:
        raise ValueError("candidate Exact10 tree count drift")
    for entry in entries:
        try:
            metadata, path = entry.decode("utf-8").split("\t", 1)
            mode, kind, blob = metadata.split(" ")
        except ValueError as error:
            raise ValueError("candidate tree entry malformed") from error
        if (
            path not in expected
            or mode != "100644"
            or kind != "blob"
            or re.fullmatch(r"[0-9a-f]{40}", blob) is None
        ):
            raise ValueError("candidate Exact10 tree mode drift")


def verify_lifecycle(
    root: Path = REPO_ROOT,
    exact10: Sequence[Path] = EXACT10,
    *,
    base: str = BASE_COMMIT,
) -> str:
    root = Path(os.path.abspath(root))
    ordered = tuple(path.as_posix() for path in exact10)
    expected = set(ordered)
    if len(ordered) != 10 or len(expected) != 10:
        raise ValueError("candidate is not Exact10")
    initial = _capture_lifecycle_state(root, ordered, base=base)
    assert_exact10_recursive_inventory(root, exact10)
    final = _capture_lifecycle_state(root, ordered, base=base)
    if final != initial:
        raise ValueError("final HEAD/inventory/index/identity drift")
    if initial.untracked == expected and not initial.tracked:
        return "pre_commit"
    if initial.tracked != expected or initial.untracked:
        raise ValueError("post-commit lifecycle inventory drift")
    _assert_post_commit_history(root, initial.head, expected, base)
    return "post_commit"


def main() -> None:
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise ValueError("checker requires canonical CPython 3.10.4")
    result = verify_artifacts()
    lifecycle = verify_lifecycle()
    print(
        json.dumps(
            {
                "all_checks_passed": True,
                "authorized_admit_015_training_execution_count": 0,
                "current_permission": False,
                "exact10_file_count": 10,
                "exact30_issue_sha256": (
                    EXPECTED_DERIVED_SHA256[ISSUES_NAME]
                ),
                "lifecycle": lifecycle,
                "mandatory_training_authorization_enforcement_api_frozen": (
                    True
                ),
                "mandatory_training_authorization_enforcement_implemented": (
                    True
                ),
                "manifest_sha256": _sha(
                    result["payloads"][MANIFEST_NAME]
                ),
                "protected_action_count": 11,
                "ready_for_combined_permission_semantics_contract_design": (
                    True
                ),
                "recommended_next_step": (
                    "design_covapie_combined_permission_semantics_contract_v1"
                ),
                "source_attestation_count": len(
                    result["source_records"]
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
