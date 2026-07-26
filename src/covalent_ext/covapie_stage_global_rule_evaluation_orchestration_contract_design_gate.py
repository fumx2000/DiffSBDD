"""Pure design contract for future stage admission orchestration.

This module deliberately does not implement the future production
``orchestrate_stage_admission_scope`` API.  It never dispatches a rule, calls
an evaluator handler, calls the combined aggregator, performs a candidate
runtime loop, or grants an action permission.  The only executable planner
below validates the future input envelope and constructs deterministic,
identity-bearing design tokens.
"""

from __future__ import annotations

import csv
import ctypes
import errno
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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, NoReturn

from covalent_ext.covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1 import (
    AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES,
    AGGREGATION_OUTCOME_VOCABULARY,
    EVALUATION_INVARIANT_INVALID_REASON as COMBINED_EVALUATION_INVARIANT_INVALID_REASON,
    REQUIRED_RULE_BLOCKED_REASON as COMBINED_REQUIRED_RULE_BLOCKED_REASON,
    REQUIRED_RULE_INVALID_REASON as COMBINED_REQUIRED_RULE_INVALID_REASON,
    RESULT_FIELDS as COMBINED_RESULT_FIELDS,
    RESULT_SCHEMA_VERSION as COMBINED_RESULT_SCHEMA_VERSION,
    CombinedAdmissionCandidateVerdict,
)
from covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 import (
    OUTCOME_VOCABULARY,
    RESULT_FIELDS as UNIFIED_RESULT_FIELDS,
    RESULT_SCHEMA_VERSION as UNIFIED_RESULT_SCHEMA_VERSION,
    UnifiedAdmissionRuleEvaluation,
)


PROJECT = "CovaPIE"
STAGE = "covapie_stage_global_rule_evaluation_orchestration_contract_v1"
STEP = "stage-global rule evaluation orchestration design contract v1"
BASE_COMMIT = "3e55b6e58668ce66ba74df8e0894b15641601e52"
BASE_PARENT = "38eb228f6507bb36c19433050c75d4b28e2e65a2"
BASE_TREE = "3717e7a8c436a949fecf16ee4e8220e604c10d74"
BASE_SUBJECT = (
    "add CovaPIE combined candidate verdict and cross-rule aggregation v1"
)
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_stage_global_rule_evaluation_orchestration_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
STAGING_NAME_PREFIX = f"{STAGE}.__staging__."
LEGACY_STAGING_PREFIXES = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_v1.__staging__.",
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.__staging__.",
    ".combined-permission-semantics-stage-",
)

PUBLIC_API_RESULT_FILENAME = (
    "covapie_stage_global_orchestration_public_api_and_result_contract.csv"
)
CALL_PLAN_FILENAME = "covapie_stage_global_orchestration_scope_rule_call_plan.csv"
TRUTH_FILENAME = "covapie_stage_global_orchestration_truth_matrix.csv"
SAFETY_FILENAME = "covapie_stage_global_orchestration_safety_audit.csv"
ISSUE_FILENAME = (
    "covapie_stage_global_orchestration_issue_readiness_inventory.csv"
)
MANIFEST_FILENAME = (
    "covapie_stage_global_rule_evaluation_orchestration_contract_manifest.json"
)
OUTPUT_FILES = (
    PUBLIC_API_RESULT_FILENAME,
    CALL_PLAN_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)
SUPPORT_PATHS = (
    Path("src/covalent_ext")
    / "covapie_stage_global_rule_evaluation_orchestration_contract_design_gate.py",
    Path("scripts")
    / "check_covapie_stage_global_rule_evaluation_orchestration_contract_v1.py",
    Path("tests")
    / "test_covapie_stage_global_rule_evaluation_orchestration_contract_v1.py",
    Path("docs")
    / "covapie_stage_global_rule_evaluation_orchestration_contract_v1_summary.md",
)
EXACT10 = SUPPORT_PATHS + tuple(DEFAULT_OUTPUT_ROOT / name for name in OUTPUT_FILES)

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1.py",
        "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
    ),
    (
        "scripts/"
        "check_covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1.py",
        "66ceb15d169e84b1fec1040efde53ad791fadd86bb63becfe5c5421c75acfb43",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "implementation_manifest.json",
        "bc8c5a5fc52b74d9e6f6e9da0b75dd69832b09213a996a4c73913660ab3d87d6",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "runtime_contract.csv",
        "ae08a579aaeddd933f235bb7f380758eeb96825c7664ea77c3da4840eb474635",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_implementation_truth_matrix.csv",
        "04342ff96a73990cb5432271652dd384b520b27723066e1e154a15e878b1df19",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_implementation_safety_audit.csv",
        "1566c9e4915da8009cc34d739d5221d4a12305b79fe858b994592fbd9f1056f0",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_precondition_transition_inventory.csv",
        "9d8ef1265ff50d45dac3f95b4696a33c510d4272e2208a0cb1f87058d5054dd4",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_issue_readiness_inventory.csv",
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015.py",
        "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json",
        "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_014.py",
        "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json",
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/"
        "covapie_combined_permission_scope_and_rule_membership_contract.csv",
        "3e74d0ac1d7be7bd23cf6d243c9593e01099a6dd55ed5079d27b01c12cb71b55",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_mandatory_training_"
        "authorization_enforcement_v1/"
        "covapie_admit_015_mandatory_training_authorization_enforcement_"
        "manifest.json",
        "706fe24fe585cccaf9c4691adda673290e7604f35b6e63ffe2096087b17d1d77",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_formal_evaluator_"
        "interface_preconditions_audit_v1/"
        "covapie_admit_015_formal_evaluator_interface_precondition_"
        "inventory.csv",
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/"
        "covapie_bulk_download_admission_rule_registry.csv",
        "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    ),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

RULE_IDS = tuple(f"ADMIT_{number:03d}" for number in range(1, 16))
RULE_NAMES = MappingProxyType(
    {
        "ADMIT_001": "unique_candidate_identity",
        "ADMIT_002": "valid_pdb_id_format",
        "ADMIT_003": "ligand_or_het_identity_present",
        "ADMIT_004": "covalent_residue_identity_present",
        "ADMIT_005": "cys_sg_scope_only_v1",
        "ADMIT_006": "explicit_covalent_event_evidence",
        "ADMIT_007": "distance_only_inference_forbidden",
        "ADMIT_008": "topology_restoration_disposition",
        "ADMIT_009": "duplicate_identity_precheck",
        "ADMIT_010": "leakage_group_assignment_before_split",
        "ADMIT_011": "raw_overwrite_forbidden",
        "ADMIT_012": "future_download_integrity_fields_required",
        "ADMIT_013": "download_failure_fail_closed",
        "ADMIT_014": "current_gate_grants_no_download_permission",
        "ADMIT_015": "current_gate_grants_no_training_permission",
    }
)
ADAPTER_IDS = MappingProxyType(
    {
        rule_id: f"covapie_admit_{number:03d}_unified_adapter_v1"
        for number, rule_id in enumerate(RULE_IDS, 1)
    }
)
SCOPE_CONTRACT = (
    (
        "download_execution_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_011",
            "ADMIT_014",
        ),
    ),
    (
        "post_download_acceptance_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_011",
            "ADMIT_012",
            "ADMIT_013",
            "ADMIT_014",
        ),
    ),
    (
        "pre_final_split_acceptance_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_010",
            "ADMIT_011",
            "ADMIT_012",
            "ADMIT_013",
            "ADMIT_014",
        ),
    ),
    ("training_execution_admission_permission", RULE_IDS),
)
REQUIRED_RULE_IDS = MappingProxyType(dict(SCOPE_CONTRACT))
SCOPE_IDS = tuple(REQUIRED_RULE_IDS)
STAGE_GLOBAL_RULE_IDS_BY_SCOPE = MappingProxyType(
    {
        scope: tuple(
            rule_id
            for rule_id in required
            if rule_id in ("ADMIT_014", "ADMIT_015")
        )
        for scope, required in SCOPE_CONTRACT
    }
)
CANDIDATE_RULE_IDS_BY_SCOPE = MappingProxyType(
    {
        scope: tuple(
            rule_id
            for rule_id in required
            if rule_id not in STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
        )
        for scope, required in SCOPE_CONTRACT
    }
)
STAGE_GLOBAL_CANDIDATE_SENTINEL: Mapping[str, object] = MappingProxyType({})

INPUT_FIELDS = (
    "candidate_record",
    "evaluation_context",
    "download_result_context",
)
CANDIDATE_RESULT_FIELDS = (
    "candidate_index",
    "ordered_rule_evaluations",
    "combined_verdict",
    "dispatcher_call_count",
    "aggregator_call_count",
)
STAGE_RESULT_SCHEMA_VERSION = "covapie_stage_admission_orchestration_result_v1"
STAGE_RESULT_FIELDS = (
    "schema_version",
    "scope_id",
    "candidate_count",
    "required_rule_ids",
    "stage_global_rule_ids",
    "candidate_rule_ids",
    "stage_global_rule_evaluations",
    "candidate_results",
    "dispatcher_call_count",
    "aggregator_call_count",
    "orchestration_io_used",
    "action_permission_granted",
)
ERROR_FIELDS = (
    "code",
    "scope_id",
    "candidate_index",
    "admission_rule_id",
    "dispatcher_call_count",
    "aggregator_call_count",
    "reason",
    "cause_type",
)
ERROR_CODES = (
    "STAGE_ORCHESTRATION_SCOPE_ID_INVALID",
    "STAGE_ORCHESTRATION_CANDIDATE_INPUT_VECTOR_INVALID",
    "STAGE_ORCHESTRATION_CANDIDATE_INPUT_INVARIANT_INVALID",
    "STAGE_ORCHESTRATION_BATCH_CONTEXT_INVALID",
    "STAGE_ORCHESTRATION_STAGE_AUTHORIZATION_CONTEXT_INVALID",
    "STAGE_ORCHESTRATION_DISPATCH_ERROR",
    "STAGE_ORCHESTRATION_RULE_RESULT_INVARIANT_INVALID",
    "STAGE_ORCHESTRATION_AGGREGATOR_RESULT_INVARIANT_INVALID",
)

ACTUAL_DISPATCHER_CALL_COUNT = 0
ACTUAL_HANDLER_CALL_COUNT = 0
ACTUAL_AGGREGATOR_CALL_COUNT = 0
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0
ORCHESTRATION_IO_USED = False
ACTION_PERMISSION_GRANTED = False


@dataclass(frozen=True)
class AdmissionCandidateOrchestrationInput:
    candidate_record: Mapping[str, object]
    evaluation_context: Mapping[str, object] | None
    download_result_context: Mapping[str, object] | None


@dataclass(frozen=True)
class CandidateAdmissionOrchestrationResult:
    candidate_index: int
    ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]
    combined_verdict: CombinedAdmissionCandidateVerdict
    dispatcher_call_count: int
    aggregator_call_count: int


@dataclass(frozen=True)
class StageAdmissionOrchestrationResult:
    schema_version: str
    scope_id: str
    candidate_count: int
    required_rule_ids: tuple[str, ...]
    stage_global_rule_ids: tuple[str, ...]
    candidate_rule_ids: tuple[str, ...]
    stage_global_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]
    candidate_results: tuple[CandidateAdmissionOrchestrationResult, ...]
    dispatcher_call_count: int
    aggregator_call_count: int
    orchestration_io_used: bool
    action_permission_granted: bool


@dataclass(frozen=True)
class StageAdmissionOrchestrationError(Exception):
    code: str
    scope_id: str
    candidate_index: int
    admission_rule_id: str
    dispatcher_call_count: int
    aggregator_call_count: int
    reason: str
    cause_type: str

    def __post_init__(self) -> None:
        values = vars(self)
        if (
            type(values) is not dict
            or tuple(values) != ERROR_FIELDS
            or tuple(self.__dataclass_fields__) != ERROR_FIELDS
        ):
            raise TypeError("stage orchestration error Exact8 storage/order invalid")
        if type(self.code) is not str or self.code not in ERROR_CODES:
            raise ValueError("stage orchestration error code invalid")
        if any(
            type(values[name]) is not str
            for name in (
                "scope_id",
                "admission_rule_id",
                "reason",
                "cause_type",
            )
        ):
            raise TypeError("stage orchestration error string field type invalid")
        if type(self.candidate_index) is not int or self.candidate_index < -1:
            raise ValueError("stage orchestration error candidate index invalid")
        if any(
            type(values[name]) is not int or values[name] < 0
            for name in ("dispatcher_call_count", "aggregator_call_count")
        ):
            raise ValueError("stage orchestration error call count invalid")
        if self.reason == "":
            raise ValueError("stage orchestration error reason empty")
        Exception.__init__(self, self.reason)


@dataclass(frozen=True)
class _DesignRuleResultToken:
    admission_rule_id: str
    execution_domain: str
    candidate_index: int


@dataclass(frozen=True)
class _CandidateDesignPlan:
    candidate_index: int
    candidate_input: AdmissionCandidateOrchestrationInput
    candidate_rule_results: tuple[_DesignRuleResultToken, ...]
    ordered_rule_results: tuple[_DesignRuleResultToken, ...]
    dispatcher_call_count: int
    aggregator_call_count: int


@dataclass(frozen=True)
class StageGlobalOrchestrationDesignPlan:
    scope_id: str
    candidate_inputs: tuple[AdmissionCandidateOrchestrationInput, ...]
    batch_context: Mapping[str, object] | None
    stage_authorization_context: Mapping[str, object] | None
    required_rule_ids: tuple[str, ...]
    stage_global_rule_ids: tuple[str, ...]
    candidate_rule_ids: tuple[str, ...]
    stage_global_rule_results: tuple[_DesignRuleResultToken, ...]
    candidate_plans: tuple[_CandidateDesignPlan, ...]
    dispatcher_call_order: tuple[tuple[int, str], ...]
    dispatcher_call_count: int
    aggregator_call_count: int
    orchestration_io_used: bool
    action_permission_granted: bool


@dataclass(frozen=True)
class FailureCoordinateDesign:
    candidate_index: int
    admission_rule_id: str
    dispatcher_call_count: int
    aggregator_call_count: int


FAILURE_KINDS = (
    "stage_global_dispatch",
    "candidate_dispatch",
    "candidate_aggregator",
)


def compute_failure_coordinate_design(
    scope_id: str,
    failure_kind: str,
    *,
    candidate_index: int,
    rule_position: int,
) -> FailureCoordinateDesign:
    """Project attempted-call coordinates using the frozen V1 formulas."""
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        raise ValueError("failure-coordinate scope invalid")
    if type(failure_kind) is not str or failure_kind not in FAILURE_KINDS:
        raise ValueError("failure-coordinate kind invalid")
    if type(candidate_index) is not int or candidate_index < -1:
        raise ValueError("failure-coordinate candidate index invalid")
    if type(rule_position) is not int:
        raise TypeError("failure-coordinate rule position type invalid")
    stage_ids = STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
    candidate_ids = CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]
    global_count = len(stage_ids)
    candidate_count = len(candidate_ids)
    if failure_kind == "stage_global_dispatch":
        if candidate_index != -1 or not 1 <= rule_position <= global_count:
            raise ValueError("stage-global failure-coordinate input invalid")
        return FailureCoordinateDesign(
            -1,
            stage_ids[rule_position - 1],
            rule_position,
            0,
        )
    if candidate_index < 0:
        raise ValueError("candidate failure-coordinate index invalid")
    if failure_kind == "candidate_dispatch":
        if not 1 <= rule_position <= candidate_count:
            raise ValueError("candidate-rule failure-coordinate position invalid")
        return FailureCoordinateDesign(
            candidate_index,
            candidate_ids[rule_position - 1],
            global_count + candidate_index * candidate_count + rule_position,
            candidate_index,
        )
    if rule_position != 0:
        raise ValueError("aggregator failure-coordinate rule position must be zero")
    return FailureCoordinateDesign(
        candidate_index,
        "",
        global_count + (candidate_index + 1) * candidate_count,
        candidate_index + 1,
    )


def _failure_reason(
    code: str,
    scope_id: str,
    failure_kind: str,
    coordinate: FailureCoordinateDesign,
) -> str:
    return (
        f"{code}:{failure_kind}:{scope_id}:"
        f"candidate_index={coordinate.candidate_index}:"
        f"admission_rule_id={coordinate.admission_rule_id}"
    )


def raise_orchestration_failure_from_cause_design(
    scope_id: str,
    failure_kind: str,
    *,
    candidate_index: int,
    rule_position: int,
    cause: Exception,
) -> NoReturn:
    """Freeze future ``raise ... from cause`` without executing a runtime."""
    if not isinstance(cause, Exception):
        raise TypeError("orchestration cause must inherit Exception")
    coordinate = compute_failure_coordinate_design(
        scope_id,
        failure_kind,
        candidate_index=candidate_index,
        rule_position=rule_position,
    )
    code = (
        ERROR_CODES[5]
        if failure_kind != "candidate_aggregator"
        else ERROR_CODES[7]
    )
    raise StageAdmissionOrchestrationError(
        code=code,
        scope_id=scope_id,
        candidate_index=coordinate.candidate_index,
        admission_rule_id=coordinate.admission_rule_id,
        dispatcher_call_count=coordinate.dispatcher_call_count,
        aggregator_call_count=coordinate.aggregator_call_count,
        reason=_failure_reason(code, scope_id, failure_kind, coordinate),
        cause_type=type(cause).__name__,
    ) from cause


def _prevalidation_error(code: str, scope_id: object) -> StageAdmissionOrchestrationError:
    return StageAdmissionOrchestrationError(
        code=code,
        scope_id=scope_id if type(scope_id) is str else "",
        candidate_index=-1,
        admission_rule_id="",
        dispatcher_call_count=0,
        aggregator_call_count=0,
        reason=code,
        cause_type="",
    )


def _exact_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _exact_string_pair_tuple(value: object) -> bool:
    if type(value) is not tuple:
        return False
    return all(
        type(item) is tuple
        and len(item) == 2
        and type(item[0]) is str
        and type(item[1]) is str
        for item in value
    )


def _unified_result_invariant_valid(
    value: object,
    expected_rule_id: str,
) -> bool:
    if (
        type(value) is not UnifiedAdmissionRuleEvaluation
        or type(expected_rule_id) is not str
        or expected_rule_id not in RULE_IDS
    ):
        return False
    try:
        values = vars(value)
    except TypeError:
        return False
    if (
        type(values) is not dict
        or tuple(values) != UNIFIED_RESULT_FIELDS
        or tuple(value.__dataclass_fields__) != UNIFIED_RESULT_FIELDS
    ):
        return False
    if any(
        type(values[name]) is not str
        for name in (
            "schema_version",
            "admission_rule_id",
            "admission_rule_name",
            "outcome",
            "reason",
            "adapter_id",
        )
    ) or any(
        type(values[name]) is not bool
        for name in ("passed", "blocks_candidate", "evaluator_io_used")
    ):
        return False
    if (
        not _exact_string_pair_tuple(value.normalized_values)
        or not _exact_string_pair_tuple(value.validated_candidate_fields)
        or not _exact_string_tuple(value.consumed_candidate_fields)
        or not _exact_string_tuple(value.consumed_context_items)
    ):
        return False
    try:
        if type(value)(**values) != value:
            return False
    except (TypeError, ValueError):
        return False
    return (
        value.schema_version == UNIFIED_RESULT_SCHEMA_VERSION
        and value.outcome in OUTCOME_VOCABULARY
        and value.passed is (value.outcome == "passed")
        and value.blocks_candidate is (value.outcome != "passed")
        and (
            (value.outcome == "passed" and value.reason == "")
            or (value.outcome != "passed" and value.reason != "")
        )
        and value.evaluator_io_used is False
        and value.admission_rule_id == expected_rule_id
        and value.admission_rule_name == RULE_NAMES[expected_rule_id]
        and value.adapter_id == ADAPTER_IDS[expected_rule_id]
    )


def validate_unified_rule_evaluation_design(
    value: object,
    *,
    expected_rule_id: str,
    scope_id: str,
    candidate_index: int,
    dispatcher_call_count: int,
    aggregator_call_count: int,
) -> UnifiedAdmissionRuleEvaluation:
    if not _unified_result_invariant_valid(value, expected_rule_id):
        raise StageAdmissionOrchestrationError(
            code=ERROR_CODES[6],
            scope_id=scope_id,
            candidate_index=candidate_index,
            admission_rule_id=(
                expected_rule_id if type(expected_rule_id) is str else ""
            ),
            dispatcher_call_count=dispatcher_call_count,
            aggregator_call_count=aggregator_call_count,
            reason=ERROR_CODES[6],
            cause_type="",
        )
    assert type(value) is UnifiedAdmissionRuleEvaluation
    return value


def _combined_result_invariant_valid(
    value: object,
    expected_scope_id: str,
    ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...],
) -> bool:
    if (
        type(value) is not CombinedAdmissionCandidateVerdict
        or type(expected_scope_id) is not str
        or expected_scope_id not in REQUIRED_RULE_IDS
        or type(ordered_rule_evaluations) is not tuple
    ):
        return False
    try:
        values = vars(value)
    except TypeError:
        return False
    if (
        type(values) is not dict
        or tuple(values) != COMBINED_RESULT_FIELDS
        or tuple(value.__dataclass_fields__) != COMBINED_RESULT_FIELDS
    ):
        return False
    if any(
        type(values[name]) is not str
        for name in ("schema_version", "scope_id", "outcome", "reason")
    ) or any(
        type(values[name]) is not bool
        for name in ("passed", "blocks_scope_action", "aggregation_io_used")
    ):
        return False
    tuple_fields = (
        "required_rule_ids",
        "evaluated_rule_ids",
        "rule_evaluations",
        "invalid_rule_ids",
        "blocked_rule_ids",
        "failing_rule_ids",
    )
    if any(type(values[name]) is not tuple for name in tuple_fields):
        return False
    if any(
        not _exact_string_tuple(values[name])
        for name in (
            "required_rule_ids",
            "evaluated_rule_ids",
            "invalid_rule_ids",
            "blocked_rule_ids",
            "failing_rule_ids",
        )
    ):
        return False
    try:
        if type(value)(**values) != value:
            return False
    except (TypeError, ValueError):
        return False
    required = REQUIRED_RULE_IDS[expected_scope_id]
    if (
        value.schema_version != COMBINED_RESULT_SCHEMA_VERSION
        or value.scope_id != expected_scope_id
        or value.required_rule_ids != required
        or len(ordered_rule_evaluations) != len(required)
        or any(
            type(item) is not UnifiedAdmissionRuleEvaluation
            for item in ordered_rule_evaluations
        )
        or tuple(item.admission_rule_id for item in ordered_rule_evaluations)
        != required
        or any(
            not _unified_result_invariant_valid(item, rule_id)
            for item, rule_id in zip(
                ordered_rule_evaluations, required, strict=True
            )
        )
        or value.aggregation_io_used is not False
        or value.outcome not in AGGREGATION_OUTCOME_VOCABULARY
        or value.passed is not (value.outcome == "passed")
        or value.blocks_scope_action is not (value.outcome != "passed")
    ):
        return False
    rejected_present = any(
        item.outcome not in AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
        for item in ordered_rule_evaluations
    )
    if rejected_present:
        return (
            value.outcome == "invalid"
            and value.passed is False
            and value.blocks_scope_action is True
            and value.reason == COMBINED_EVALUATION_INVARIANT_INVALID_REASON
            and value.evaluated_rule_ids == ()
            and value.rule_evaluations == ()
            and value.invalid_rule_ids == ()
            and value.blocked_rule_ids == ()
            and value.failing_rule_ids == ()
        )
    if (
        value.evaluated_rule_ids != required
        or value.rule_evaluations is not ordered_rule_evaluations
    ):
        return False
    invalid = tuple(
        item.admission_rule_id
        for item in ordered_rule_evaluations
        if item.outcome == "invalid"
    )
    blocked = tuple(
        item.admission_rule_id
        for item in ordered_rule_evaluations
        if item.outcome == "blocked"
    )
    failing = tuple(
        item.admission_rule_id
        for item in ordered_rule_evaluations
        if item.outcome != "passed"
    )
    expected_outcome = "invalid" if invalid else "blocked" if blocked else "passed"
    expected_reason = (
        COMBINED_REQUIRED_RULE_INVALID_REASON
        if invalid
        else COMBINED_REQUIRED_RULE_BLOCKED_REASON
        if blocked
        else ""
    )
    return (
        value.invalid_rule_ids == invalid
        and value.blocked_rule_ids == blocked
        and value.failing_rule_ids == failing
        and value.outcome == expected_outcome
        and value.reason == expected_reason
    )


def validate_combined_candidate_verdict_design(
    value: object,
    *,
    expected_scope_id: str,
    ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...],
    candidate_index: int,
    dispatcher_call_count: int,
    aggregator_call_count: int,
) -> CombinedAdmissionCandidateVerdict:
    if not _combined_result_invariant_valid(
        value, expected_scope_id, ordered_rule_evaluations
    ):
        raise StageAdmissionOrchestrationError(
            code=ERROR_CODES[7],
            scope_id=(
                expected_scope_id if type(expected_scope_id) is str else ""
            ),
            candidate_index=candidate_index,
            admission_rule_id="",
            dispatcher_call_count=dispatcher_call_count,
            aggregator_call_count=aggregator_call_count,
            reason=ERROR_CODES[7],
            cause_type="",
        )
    assert type(value) is CombinedAdmissionCandidateVerdict
    return value


def classify_stage_global_orchestration_contract_design(
    scope_id: str,
    candidate_inputs: tuple[AdmissionCandidateOrchestrationInput, ...],
    *,
    batch_context: Mapping[str, object] | None,
    stage_authorization_context: Mapping[str, object] | None,
) -> StageGlobalOrchestrationDesignPlan:
    """Build a deterministic plan; this is not the future production API."""
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        raise _prevalidation_error(ERROR_CODES[0], scope_id)
    if type(candidate_inputs) is not tuple or not candidate_inputs:
        raise _prevalidation_error(ERROR_CODES[1], scope_id)
    for item in candidate_inputs:
        if type(item) is not AdmissionCandidateOrchestrationInput:
            raise _prevalidation_error(ERROR_CODES[2], scope_id)
        if (
            not isinstance(item.candidate_record, Mapping)
            or (
                item.evaluation_context is not None
                and not isinstance(item.evaluation_context, Mapping)
            )
            or (
                item.download_result_context is not None
                and not isinstance(item.download_result_context, Mapping)
            )
        ):
            raise _prevalidation_error(ERROR_CODES[2], scope_id)
    if batch_context is not None and not isinstance(batch_context, Mapping):
        raise _prevalidation_error(ERROR_CODES[3], scope_id)
    if (
        stage_authorization_context is not None
        and not isinstance(stage_authorization_context, Mapping)
    ):
        raise _prevalidation_error(ERROR_CODES[4], scope_id)

    required = REQUIRED_RULE_IDS[scope_id]
    stage_ids = STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
    candidate_ids = CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]
    stage_results = tuple(
        _DesignRuleResultToken(rule_id, "stage_global_once", -1)
        for rule_id in stage_ids
    )
    stage_by_id = {
        token.admission_rule_id: token for token in stage_results
    }
    dispatcher_order: list[tuple[int, str]] = [
        (-1, rule_id) for rule_id in stage_ids
    ]
    plans: list[_CandidateDesignPlan] = []
    for candidate_index, item in enumerate(candidate_inputs):
        candidate_results = tuple(
            _DesignRuleResultToken(
                rule_id, "per_candidate", candidate_index
            )
            for rule_id in candidate_ids
        )
        candidate_by_id = {
            token.admission_rule_id: token for token in candidate_results
        }
        vector = tuple(
            (
                stage_by_id[rule_id]
                if rule_id in stage_by_id
                else candidate_by_id[rule_id]
            )
            for rule_id in required
        )
        dispatcher_order.extend(
            (candidate_index, rule_id) for rule_id in candidate_ids
        )
        plans.append(
            _CandidateDesignPlan(
                candidate_index,
                item,
                candidate_results,
                vector,
                len(candidate_ids),
                1,
            )
        )
    return StageGlobalOrchestrationDesignPlan(
        scope_id,
        candidate_inputs,
        batch_context,
        stage_authorization_context,
        required,
        stage_ids,
        candidate_ids,
        stage_results,
        tuple(plans),
        tuple(dispatcher_order),
        len(stage_ids) + len(candidate_ids) * len(candidate_inputs),
        len(candidate_inputs),
        False,
        False,
    )


PUBLIC_API_COLUMNS = (
    "contract_area",
    "contract_order",
    "contract_item",
    "exact_requirement",
    "observed_contract",
    "contract_passed",
)
CALL_PLAN_COLUMNS = (
    "scope_order",
    "scope_id",
    "scope_rule_order",
    "admission_rule_id",
    "admission_rule_name",
    "execution_domain",
    "dispatcher_call_phase",
    "candidate_record_source",
    "batch_context_source",
    "evaluation_context_source",
    "download_result_context_source",
    "stage_authorization_context_source",
    "vector_position",
    "result_reuse_policy",
    "expected_calls_for_N",
    "contract_evidence_source",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_group",
    "case_id",
    "expected",
    "observed",
    "case_passed",
)
SAFETY_COLUMNS = (
    "safety_order",
    "safety_item",
    "expected",
    "observed",
    "safety_passed",
)


def _contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        area: str, order: int, item: str, requirement: str, observed: str
    ) -> None:
        rows.append(
            {
                "contract_area": area,
                "contract_order": str(order),
                "contract_item": item,
                "exact_requirement": requirement,
                "observed_contract": observed,
                "contract_passed": "true",
            }
        )

    api = (
        ("function_name", "orchestrate_stage_admission_scope"),
        ("parameter_count", "4"),
        ("scope_id_parameter_kind", "positional_or_keyword"),
        ("scope_id_annotation", "str"),
        ("scope_id_default", "absent"),
        ("candidate_inputs_parameter_kind", "positional_or_keyword"),
        (
            "candidate_inputs_annotation",
            "tuple[AdmissionCandidateOrchestrationInput, ...]",
        ),
        ("candidate_inputs_default", "absent"),
        ("batch_context_parameter_kind", "required_keyword_only"),
        ("batch_context_annotation", "Mapping[str, object] | None"),
        ("batch_context_default", "absent"),
        (
            "stage_authorization_context_parameter_kind",
            "required_keyword_only",
        ),
        (
            "stage_authorization_context_annotation",
            "Mapping[str, object] | None",
        ),
        ("stage_authorization_context_default", "absent"),
        ("return_annotation", "StageAdmissionOrchestrationResult"),
        ("var_positional_parameter", "absent"),
        ("var_keyword_parameter", "absent"),
        (
            "forbidden_injection_or_training_parameters",
            "absent:dispatcher|aggregator|registry|override|fallback|model|"
            "dataloader|checkpoint|training",
        ),
    )
    for order, (item, value) in enumerate(api, 1):
        add("future_public_api", order, item, value, value)
    schemas = (
        ("AdmissionCandidateOrchestrationInput", INPUT_FIELDS),
        ("CandidateAdmissionOrchestrationResult", CANDIDATE_RESULT_FIELDS),
        ("StageAdmissionOrchestrationResult", STAGE_RESULT_FIELDS),
        ("StageAdmissionOrchestrationError", ERROR_FIELDS),
    )
    annotations = {
        "AdmissionCandidateOrchestrationInput": (
            "Mapping[str, object]",
            "Mapping[str, object] | None",
            "Mapping[str, object] | None",
        ),
        "CandidateAdmissionOrchestrationResult": (
            "int",
            "tuple[UnifiedAdmissionRuleEvaluation, ...]",
            "CombinedAdmissionCandidateVerdict",
            "int",
            "int",
        ),
        "StageAdmissionOrchestrationResult": (
            "str",
            "str",
            "int",
            "tuple[str, ...]",
            "tuple[str, ...]",
            "tuple[str, ...]",
            "tuple[UnifiedAdmissionRuleEvaluation, ...]",
            "tuple[CandidateAdmissionOrchestrationResult, ...]",
            "int",
            "int",
            "bool",
            "bool",
        ),
        "StageAdmissionOrchestrationError": (
            "str",
            "str",
            "int",
            "str",
            "int",
            "int",
            "str",
            "str",
        ),
    }
    for area, names in schemas:
        for order, (name, annotation) in enumerate(
            zip(names, annotations[area], strict=True), 1
        ):
            value = f"{name}: {annotation}"
            add(area, order, name, value, value)
    for order, code in enumerate(ERROR_CODES, 1):
        add("StageAdmissionOrchestrationErrorCode", order, code, code, code)
    if len(rows) != 54:
        raise ValueError("Exact54 public API/result/error row drift")
    return rows


_CONTEXT_ROUTING = MappingProxyType(
    {
        "ADMIT_001": ("api_batch_context_same_identity", "None", "None", "None"),
        "ADMIT_002": ("None", "None", "None", "None"),
        "ADMIT_003": ("None", "None", "None", "None"),
        "ADMIT_004": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_005": ("None", "None", "None", "None"),
        "ADMIT_006": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_007": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_008": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_009": (
            "api_batch_context_same_identity",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_010": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_011": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "None",
            "None",
        ),
        "ADMIT_012": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "candidate_input.download_result_context_same_identity",
            "None",
        ),
        "ADMIT_013": (
            "None",
            "candidate_input.evaluation_context_same_identity",
            "candidate_input.download_result_context_same_identity",
            "None",
        ),
        "ADMIT_014": (
            "None",
            "None",
            "None",
            "api_stage_authorization_context_same_identity",
        ),
        "ADMIT_015": (
            "None",
            "None",
            "None",
            "api_stage_authorization_context_same_identity",
        ),
    }
)


def _call_plan_rows() -> list[dict[str, str]]:
    rows = []
    for scope_order, (scope, required) in enumerate(SCOPE_CONTRACT, 1):
        stage_ids = STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
        for rule_order, rule_id in enumerate(required, 1):
            stage = rule_id in stage_ids
            batch, evaluation, download, authorization = _CONTEXT_ROUTING[rule_id]
            rows.append(
                {
                    "scope_order": str(scope_order),
                    "scope_id": scope,
                    "scope_rule_order": str(rule_order),
                    "admission_rule_id": rule_id,
                    "admission_rule_name": RULE_NAMES[rule_id],
                    "execution_domain": (
                        "stage_global_once" if stage else "per_candidate"
                    ),
                    "dispatcher_call_phase": (
                        "stage_global_before_candidates"
                        if stage
                        else "candidate_tuple_order_then_scope_membership_order"
                    ),
                    "candidate_record_source": (
                        "STAGE_GLOBAL_CANDIDATE_SENTINEL_same_identity"
                        if stage
                        else "candidate_input.candidate_record_same_identity"
                    ),
                    "batch_context_source": batch,
                    "evaluation_context_source": evaluation,
                    "download_result_context_source": download,
                    "stage_authorization_context_source": authorization,
                    "vector_position": str(rule_order - 1),
                    "result_reuse_policy": (
                        "same_result_identity_reused_across_all_candidates"
                        if stage
                        else "same_candidate_result_identity_inserted_once"
                    ),
                    "expected_calls_for_N": "1" if stage else "N",
                    "contract_evidence_source": (
                        "Exact15/Exact14 committed runtime plus inherited "
                        f"registered handler contract:{rule_id}"
                    ),
                    "contract_passed": "true",
                }
            )
    if len(rows) != 53:
        raise ValueError("Exact53 call plan row drift")
    return rows


def _design_unified_result(
    rule_id: str,
    outcome: str = "passed",
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=UNIFIED_RESULT_SCHEMA_VERSION,
        admission_rule_id=rule_id,
        admission_rule_name=RULE_NAMES[rule_id],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"DESIGN_{outcome.upper()}",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS[rule_id],
    )


def _design_ordered_vector(
    scope_id: str,
    outcome_by_position: tuple[tuple[int, str], ...] = (),
) -> tuple[UnifiedAdmissionRuleEvaluation, ...]:
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        raise ValueError("design ordered-vector scope invalid")
    if type(outcome_by_position) is not tuple or any(
        type(item) is not tuple
        or len(item) != 2
        or type(item[0]) is not int
        or type(item[1]) is not str
        for item in outcome_by_position
    ):
        raise TypeError("design ordered-vector outcome projection invalid")
    required = REQUIRED_RULE_IDS[scope_id]
    positions = tuple(item[0] for item in outcome_by_position)
    if (
        len(positions) != len(set(positions))
        or any(not 1 <= position <= len(required) for position in positions)
        or any(
            outcome not in OUTCOME_VOCABULARY
            for _, outcome in outcome_by_position
        )
    ):
        raise ValueError("design ordered-vector outcome projection invalid")
    projected = dict(outcome_by_position)
    return tuple(
        _design_unified_result(rule_id, projected.get(position, "passed"))
        for position, rule_id in enumerate(required, 1)
    )


def _design_rejected_ordered_vector(
    scope_id: str,
    rejected_positions: tuple[int, ...],
    *,
    additional_outcomes: tuple[tuple[int, str], ...] = (),
) -> tuple[UnifiedAdmissionRuleEvaluation, ...]:
    if (
        type(rejected_positions) is not tuple
        or not rejected_positions
        or any(type(position) is not int for position in rejected_positions)
        or len(rejected_positions) != len(set(rejected_positions))
    ):
        raise ValueError("design rejected positions invalid")
    if any(
        outcome == "rejected" for _, outcome in additional_outcomes
    ) or set(rejected_positions).intersection(
        position for position, _ in additional_outcomes
    ):
        raise ValueError("design rejected/additional outcome overlap invalid")
    return _design_ordered_vector(
        scope_id,
        tuple((position, "rejected") for position in rejected_positions)
        + additional_outcomes,
    )


def _design_rejected_aggregator_fail_closed_verdict(
    scope_id: str,
) -> CombinedAdmissionCandidateVerdict:
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        raise ValueError("design rejected verdict scope invalid")
    return CombinedAdmissionCandidateVerdict(
        schema_version=COMBINED_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        outcome="invalid",
        passed=False,
        blocks_scope_action=True,
        reason=COMBINED_EVALUATION_INVARIANT_INVALID_REASON,
        required_rule_ids=REQUIRED_RULE_IDS[scope_id],
        evaluated_rule_ids=(),
        rule_evaluations=(),
        invalid_rule_ids=(),
        blocked_rule_ids=(),
        failing_rule_ids=(),
        aggregation_io_used=False,
    )


def _design_combined_verdict(
    scope_id: str,
    outcome: str,
) -> tuple[
    tuple[UnifiedAdmissionRuleEvaluation, ...],
    CombinedAdmissionCandidateVerdict,
]:
    required = REQUIRED_RULE_IDS[scope_id]
    if outcome not in AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES:
        raise ValueError("design retained verdict outcome invalid")
    vector = _design_ordered_vector(
        scope_id,
        () if outcome == "passed" else ((1, outcome),),
    )
    invalid = tuple(
        item.admission_rule_id for item in vector if item.outcome == "invalid"
    )
    blocked = tuple(
        item.admission_rule_id for item in vector if item.outcome == "blocked"
    )
    failing = tuple(
        item.admission_rule_id for item in vector if item.outcome != "passed"
    )
    combined_outcome = "invalid" if invalid else "blocked" if blocked else "passed"
    reason = (
        COMBINED_REQUIRED_RULE_INVALID_REASON
        if invalid
        else COMBINED_REQUIRED_RULE_BLOCKED_REASON
        if blocked
        else ""
    )
    verdict = CombinedAdmissionCandidateVerdict(
        schema_version=COMBINED_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        outcome=combined_outcome,
        passed=combined_outcome == "passed",
        blocks_scope_action=combined_outcome != "passed",
        reason=reason,
        required_rule_ids=required,
        evaluated_rule_ids=required,
        rule_evaluations=vector,
        invalid_rule_ids=invalid,
        blocked_rule_ids=blocked,
        failing_rule_ids=failing,
        aggregation_io_used=False,
    )
    return vector, verdict


def _forged_dataclass(
    cls: type[Any],
    source: object,
    **changes: object,
) -> object:
    values = dict(vars(source))
    values.update(changes)
    forged = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _validation_observation(operation: Callable[[], object]) -> str:
    try:
        operation()
    except StageAdmissionOrchestrationError as error:
        return error.code
    return "valid"


def _combined_projection(
    verdict: CombinedAdmissionCandidateVerdict,
) -> tuple[object, ...]:
    return tuple(vars(verdict).values())


def _rejected_case_observation(
    scope_id: str,
    vector: tuple[UnifiedAdmissionRuleEvaluation, ...],
    verdict: CombinedAdmissionCandidateVerdict,
) -> tuple[object, ...]:
    unified = tuple(
        _validation_observation(
            lambda item=item, rule_id=rule_id: (
                validate_unified_rule_evaluation_design(
                    item,
                    expected_rule_id=rule_id,
                    scope_id=scope_id,
                    candidate_index=0,
                    dispatcher_call_count=position,
                    aggregator_call_count=0,
                )
            )
        )
        for position, (item, rule_id) in enumerate(
            zip(vector, REQUIRED_RULE_IDS[scope_id], strict=True),
            1,
        )
    )
    combined = _validation_observation(
        lambda: validate_combined_candidate_verdict_design(
            verdict,
            expected_scope_id=scope_id,
            ordered_rule_evaluations=vector,
            candidate_index=0,
            dispatcher_call_count=len(vector),
            aggregator_call_count=1,
        )
    )
    return (
        tuple(item.admission_rule_id for item in vector),
        tuple(item.outcome for item in vector),
        unified,
        combined,
        _combined_projection(verdict),
    )


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(group: str, case_id: str, expected: object, observed: object) -> None:
        passed = expected == observed
        rows.append(
            {
                "case_group": group,
                "case_id": case_id,
                "expected": repr(expected),
                "observed": repr(observed),
                "case_passed": str(passed).lower(),
            }
        )

    mapping = MappingProxyType({"opaque": object()})
    evaluation = MappingProxyType({"opaque": object()})
    download = MappingProxyType({"opaque": object()})
    batch = MappingProxyType({"opaque": object()})
    authorization = MappingProxyType({"opaque": object()})
    for scope, required in SCOPE_CONTRACT:
        for count in (1, 2, 3):
            inputs = tuple(
                AdmissionCandidateOrchestrationInput(mapping, evaluation, download)
                for _ in range(count)
            )
            plan = classify_stage_global_orchestration_contract_design(
                scope,
                inputs,
                batch_context=batch,
                stage_authorization_context=authorization,
            )
            label = f"{scope}:N={count}"
            add("canonical_plan", label, scope, plan.scope_id)
            add("candidate_count", label, count, len(plan.candidate_plans))
            add(
                "dispatcher_cardinality",
                label,
                len(plan.stage_global_rule_ids)
                + len(plan.candidate_rule_ids) * count,
                plan.dispatcher_call_count,
            )
            add(
                "aggregator_cardinality",
                label,
                count,
                plan.aggregator_call_count,
            )
            add(
                "complete_vector_membership",
                label,
                required,
                tuple(
                    token.admission_rule_id
                    for token in plan.candidate_plans[-1].ordered_rule_results
                ),
            )
            add(
                "candidate_order",
                label,
                tuple(range(count)),
                tuple(item.candidate_index for item in plan.candidate_plans),
            )
            add(
                "candidate_rule_order",
                label,
                plan.candidate_rule_ids,
                tuple(
                    token.admission_rule_id
                    for token in plan.candidate_plans[0].candidate_rule_results
                ),
            )
            add(
                "input_object_identity",
                label,
                True,
                plan.candidate_inputs is inputs
                and plan.candidate_plans[0].candidate_input is inputs[0]
                and plan.batch_context is batch
                and plan.stage_authorization_context is authorization,
            )
            for stage_token in plan.stage_global_rule_results:
                positions = [
                    candidate.ordered_rule_results[
                        required.index(stage_token.admission_rule_id)
                    ]
                    for candidate in plan.candidate_plans
                ]
                add(
                    "stage_global_result_identity_reuse",
                    f"{label}:{stage_token.admission_rule_id}",
                    True,
                    all(item is stage_token for item in positions),
                )
            add(
                "action_permission_always_false",
                label,
                False,
                plan.action_permission_granted,
            )
            add(
                "design_oracle_io_false",
                label,
                False,
                plan.orchestration_io_used,
            )

    plan = classify_stage_global_orchestration_contract_design(
        "training_execution_admission_permission",
        (
            AdmissionCandidateOrchestrationInput(mapping, evaluation, download),
            AdmissionCandidateOrchestrationInput(mapping, evaluation, download),
        ),
        batch_context=batch,
        stage_authorization_context=authorization,
    )
    admit014 = tuple(
        item
        for item in plan.stage_global_rule_results
        if item.admission_rule_id == "ADMIT_014"
    )
    admit015 = tuple(
        item
        for item in plan.stage_global_rule_results
        if item.admission_rule_id == "ADMIT_015"
    )
    add("admit_014_exactly_once", "training", 1, len(admit014))
    add("admit_015_exactly_once", "training", 1, len(admit015))
    for scope in SCOPE_IDS[:-1]:
        add(
            "admit_015_training_only",
            scope,
            False,
            "ADMIT_015" in STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope],
        )
    add(
        "stage_global_result_insertion",
        "training",
        ("ADMIT_014", "ADMIT_015"),
        tuple(
            token.admission_rule_id
            for token in plan.candidate_plans[0].ordered_rule_results
            if token.execution_domain == "stage_global_once"
        ),
    )
    add(
        "candidate_result_insertion",
        "training",
        plan.candidate_rule_ids,
        tuple(
            token.admission_rule_id
            for token in plan.candidate_plans[0].ordered_rule_results
            if token.execution_domain == "per_candidate"
        ),
    )
    add(
        "no_normal_result_short_circuit",
        "passed_blocked_invalid_rejected",
        ("passed", "blocked", "invalid", "rejected"),
        ("passed", "blocked", "invalid", "rejected"),
    )
    add(
        "blocked_stage_result_diagnostics_continue",
        "design_plan",
        len(plan.candidate_rule_ids) * 2,
        sum(x.dispatcher_call_count for x in plan.candidate_plans),
    )
    add(
        "invalid_candidate_result_later_candidates_continue",
        "design_plan",
        2,
        len(plan.candidate_plans),
    )
    invalid_cases = (
        (
            "invalid_scope",
            lambda: classify_stage_global_orchestration_contract_design(
                "bad",
                (AdmissionCandidateOrchestrationInput(mapping, None, None),),
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[0],
        ),
        (
            "candidate_inputs_non_tuple",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                [],  # type: ignore[arg-type]
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[1],
        ),
        (
            "candidate_inputs_empty",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (),
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[1],
        ),
        (
            "wrong_input_element_type",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (object(),),  # type: ignore[arg-type]
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[2],
        ),
        (
            "candidate_record_non_mapping",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (
                    AdmissionCandidateOrchestrationInput(  # type: ignore[arg-type]
                        object(), None, None
                    ),
                ),
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[2],
        ),
        (
            "evaluation_context_type_invalid",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (
                    AdmissionCandidateOrchestrationInput(  # type: ignore[arg-type]
                        mapping, object(), None
                    ),
                ),
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[2],
        ),
        (
            "download_context_type_invalid",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (
                    AdmissionCandidateOrchestrationInput(  # type: ignore[arg-type]
                        mapping, None, object()
                    ),
                ),
                batch_context=None,
                stage_authorization_context=None,
            ),
            ERROR_CODES[2],
        ),
        (
            "batch_context_type_invalid",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (AdmissionCandidateOrchestrationInput(mapping, None, None),),
                batch_context=object(),  # type: ignore[arg-type]
                stage_authorization_context=None,
            ),
            ERROR_CODES[3],
        ),
        (
            "stage_authorization_context_type_invalid",
            lambda: classify_stage_global_orchestration_contract_design(
                SCOPE_IDS[0],
                (AdmissionCandidateOrchestrationInput(mapping, None, None),),
                batch_context=None,
                stage_authorization_context=object(),  # type: ignore[arg-type]
            ),
            ERROR_CODES[4],
        ),
    )
    for group, operation, expected in invalid_cases:
        observed = ""
        projection: tuple[int, str, int, int, str, str] | None = None
        try:
            operation()
        except StageAdmissionOrchestrationError as error:
            observed = error.code
            projection = (
                error.candidate_index,
                error.admission_rule_id,
                error.dispatcher_call_count,
                error.aggregator_call_count,
                error.reason,
                error.cause_type,
            )
        add(group, "fail_closed", expected, observed)
        add(
            "prevalidation_error_projection",
            group,
            (-1, "", 0, 0, expected, ""),
            projection,
        )

    class InputSubclass(AdmissionCandidateOrchestrationInput):
        pass

    try:
        classify_stage_global_orchestration_contract_design(
            SCOPE_IDS[0],
            (InputSubclass(mapping, None, None),),
            batch_context=None,
            stage_authorization_context=None,
        )
        subclass_observed = ""
        subclass_projection = None
    except StageAdmissionOrchestrationError as error:
        subclass_observed = error.code
        subclass_projection = (
            error.candidate_index,
            error.admission_rule_id,
            error.dispatcher_call_count,
            error.aggregator_call_count,
            error.reason,
            error.cause_type,
        )
    add("input_subclass_rejected", "fail_closed", ERROR_CODES[2], subclass_observed)
    add(
        "prevalidation_error_projection",
        "input_subclass_rejected",
        (-1, "", 0, 0, ERROR_CODES[2], ""),
        subclass_projection,
    )

    for scope in SCOPE_IDS:
        stage_ids = STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
        candidate_ids = CANDIDATE_RULE_IDS_BY_SCOPE[scope]
        global_count = len(stage_ids)
        candidate_count = len(candidate_ids)
        for position, rule_id in enumerate(stage_ids, 1):
            coordinate = compute_failure_coordinate_design(
                scope,
                "stage_global_dispatch",
                candidate_index=-1,
                rule_position=position,
            )
            add(
                "stage_global_dispatch_failure_formula",
                f"{scope}:k={position}:{rule_id}",
                (-1, rule_id, position, 0),
                (
                    coordinate.candidate_index,
                    coordinate.admission_rule_id,
                    coordinate.dispatcher_call_count,
                    coordinate.aggregator_call_count,
                ),
            )
        positions = (
            1,
            (candidate_count + 1) // 2,
            candidate_count,
        )
        for candidate_index in (0, 1, 2):
            for position in positions:
                coordinate = compute_failure_coordinate_design(
                    scope,
                    "candidate_dispatch",
                    candidate_index=candidate_index,
                    rule_position=position,
                )
                add(
                    "candidate_dispatch_failure_formula",
                    f"{scope}:i={candidate_index}:j={position}",
                    (
                        candidate_index,
                        candidate_ids[position - 1],
                        global_count
                        + candidate_index * candidate_count
                        + position,
                        candidate_index,
                    ),
                    (
                        coordinate.candidate_index,
                        coordinate.admission_rule_id,
                        coordinate.dispatcher_call_count,
                        coordinate.aggregator_call_count,
                    ),
                )
            coordinate = compute_failure_coordinate_design(
                scope,
                "candidate_aggregator",
                candidate_index=candidate_index,
                rule_position=0,
            )
            add(
                "candidate_aggregator_failure_formula",
                f"{scope}:i={candidate_index}",
                (
                    candidate_index,
                    "",
                    global_count + (candidate_index + 1) * candidate_count,
                    candidate_index + 1,
                ),
                (
                    coordinate.candidate_index,
                    coordinate.admission_rule_id,
                    coordinate.dispatcher_call_count,
                    coordinate.aggregator_call_count,
                ),
            )

    for failure_kind, candidate_index, position in (
        ("stage_global_dispatch", -1, 1),
        ("candidate_dispatch", 2, 3),
        ("candidate_aggregator", 1, 0),
    ):
        cause = RuntimeError("nondeterministic-address-not-projected")
        caught: StageAdmissionOrchestrationError | None = None
        try:
            raise_orchestration_failure_from_cause_design(
                SCOPE_IDS[-1],
                failure_kind,
                candidate_index=candidate_index,
                rule_position=position,
                cause=cause,
            )
        except StageAdmissionOrchestrationError as error:
            caught = error
        add(
            "exception_delivery_raise_from_cause",
            failure_kind,
            True,
            (
                caught is not None
                and isinstance(caught, Exception)
                and caught.__cause__ is cause
                and caught.cause_type == "RuntimeError"
                and caught.args == (caught.reason,)
                and "nondeterministic-address" not in caught.reason
            ),
        )

    for rule_id in RULE_IDS:
        item = _design_unified_result(rule_id)
        add(
            "unified_result_validator_valid",
            rule_id,
            "valid",
            _validation_observation(
                lambda item=item, rule_id=rule_id: (
                    validate_unified_rule_evaluation_design(
                        item,
                        expected_rule_id=rule_id,
                        scope_id=SCOPE_IDS[-1],
                        candidate_index=0,
                        dispatcher_call_count=1,
                        aggregator_call_count=0,
                    )
                )
            ),
        )
    rejected = _design_unified_result("ADMIT_001", "rejected")
    add(
        "unified_rejected_structurally_valid",
        "ADMIT_001",
        "valid",
        _validation_observation(
            lambda: validate_unified_rule_evaluation_design(
                rejected,
                expected_rule_id="ADMIT_001",
                scope_id=SCOPE_IDS[-1],
                candidate_index=0,
                dispatcher_call_count=1,
                aggregator_call_count=0,
            )
        ),
    )
    valid_unified = _design_unified_result("ADMIT_001")

    class UnifiedSubclass(UnifiedAdmissionRuleEvaluation):
        pass

    unified_subclass = UnifiedSubclass(**vars(valid_unified))
    reverse_storage = object.__new__(UnifiedAdmissionRuleEvaluation)
    for name in reversed(UNIFIED_RESULT_FIELDS):
        object.__setattr__(reverse_storage, name, vars(valid_unified)[name])
    unified_mutations = (
        ("subclass", unified_subclass, "ADMIT_001"),
        ("wrong_rule_identity", valid_unified, "ADMIT_002"),
        (
            "wrong_adapter",
            _forged_dataclass(
                UnifiedAdmissionRuleEvaluation,
                valid_unified,
                adapter_id="wrong",
            ),
            "ADMIT_001",
        ),
        (
            "wrong_name",
            _forged_dataclass(
                UnifiedAdmissionRuleEvaluation,
                valid_unified,
                admission_rule_name="wrong",
            ),
            "ADMIT_001",
        ),
        (
            "wrong_schema",
            _forged_dataclass(
                UnifiedAdmissionRuleEvaluation,
                valid_unified,
                schema_version="wrong",
            ),
            "ADMIT_001",
        ),
        (
            "wrong_tuple_representation",
            _forged_dataclass(
                UnifiedAdmissionRuleEvaluation,
                valid_unified,
                normalized_values=(("key", object()),),
            ),
            "ADMIT_001",
        ),
        (
            "wrong_top_level_type",
            _forged_dataclass(
                UnifiedAdmissionRuleEvaluation,
                valid_unified,
                passed=1,
            ),
            "ADMIT_001",
        ),
        ("wrong_storage_order", reverse_storage, "ADMIT_001"),
    )
    for case_id, value, expected_rule_id in unified_mutations:
        add(
            "unified_result_validator_fail_closed",
            case_id,
            ERROR_CODES[6],
            _validation_observation(
                lambda value=value, expected_rule_id=expected_rule_id: (
                    validate_unified_rule_evaluation_design(
                        value,
                        expected_rule_id=expected_rule_id,
                        scope_id=SCOPE_IDS[-1],
                        candidate_index=0,
                        dispatcher_call_count=1,
                        aggregator_call_count=0,
                    )
                )
            ),
        )

    for scope in SCOPE_IDS:
        for outcome in ("passed", "blocked", "invalid"):
            vector, verdict = _design_combined_verdict(scope, outcome)
            add(
                "combined_result_validator_valid",
                f"{scope}:{outcome}",
                "valid",
                _validation_observation(
                    lambda vector=vector, verdict=verdict, scope=scope: (
                        validate_combined_candidate_verdict_design(
                            verdict,
                            expected_scope_id=scope,
                            ordered_rule_evaluations=vector,
                            candidate_index=0,
                            dispatcher_call_count=len(vector),
                            aggregator_call_count=1,
                        )
                    )
                ),
            )

    for scope in SCOPE_IDS:
        required = REQUIRED_RULE_IDS[scope]
        for position in (1, (len(required) + 1) // 2, len(required)):
            vector = _design_rejected_ordered_vector(scope, (position,))
            verdict = _design_rejected_aggregator_fail_closed_verdict(scope)
            expected_outcomes = tuple(
                "rejected" if index == position else "passed"
                for index in range(1, len(required) + 1)
            )
            expected_projection = (
                COMBINED_RESULT_SCHEMA_VERSION,
                scope,
                "invalid",
                False,
                True,
                COMBINED_EVALUATION_INVARIANT_INVALID_REASON,
                required,
                (),
                (),
                (),
                (),
                (),
                False,
            )
            add(
                "rejected_exact4_position_validator_valid",
                f"{scope}:position={position}",
                (
                    required,
                    expected_outcomes,
                    ("valid",) * len(required),
                    "valid",
                    expected_projection,
                ),
                _rejected_case_observation(scope, vector, verdict),
            )

    precedence_scope = SCOPE_IDS[-1]
    precedence_required = REQUIRED_RULE_IDS[precedence_scope]
    middle = (len(precedence_required) + 1) // 2
    last = len(precedence_required)
    precedence_cases = (
        ("multiple_rejected", (1, last), ()),
        ("rejected_plus_blocked", (1,), ((middle, "blocked"),)),
        ("rejected_plus_invalid", (1,), ((last, "invalid"),)),
        (
            "rejected_plus_blocked_plus_invalid",
            (1,),
            ((middle, "blocked"), (last, "invalid")),
        ),
    )
    for case_id, rejected_positions, additional in precedence_cases:
        vector = _design_rejected_ordered_vector(
            precedence_scope,
            rejected_positions,
            additional_outcomes=additional,
        )
        verdict = _design_rejected_aggregator_fail_closed_verdict(
            precedence_scope
        )
        outcome_projection = {
            **{position: "rejected" for position in rejected_positions},
            **dict(additional),
        }
        expected_outcomes = tuple(
            outcome_projection.get(position, "passed")
            for position in range(1, len(precedence_required) + 1)
        )
        add(
            "rejected_mixed_precedence_validator_valid",
            case_id,
            (
                precedence_required,
                expected_outcomes,
                ("valid",) * len(precedence_required),
                "valid",
                (
                    COMBINED_RESULT_SCHEMA_VERSION,
                    precedence_scope,
                    "invalid",
                    False,
                    True,
                    COMBINED_EVALUATION_INVARIANT_INVALID_REASON,
                    precedence_required,
                    (),
                    (),
                    (),
                    (),
                    (),
                    False,
                ),
            ),
            _rejected_case_observation(precedence_scope, vector, verdict),
        )

    rejected_scope = SCOPE_IDS[0]
    rejected_vector = _design_rejected_ordered_vector(rejected_scope, (1,))
    rejected_verdict = _design_rejected_aggregator_fail_closed_verdict(
        rejected_scope
    )

    class RejectedVerdictSubclass(CombinedAdmissionCandidateVerdict):
        pass

    rejected_subclass = RejectedVerdictSubclass(**vars(rejected_verdict))
    reverse_rejected_storage = object.__new__(
        CombinedAdmissionCandidateVerdict
    )
    for name in reversed(COMBINED_RESULT_FIELDS):
        object.__setattr__(
            reverse_rejected_storage,
            name,
            vars(rejected_verdict)[name],
        )
    rejected_mutations = (
        (
            "wrong_schema",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                schema_version="wrong",
            ),
        ),
        (
            "wrong_scope",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                scope_id=SCOPE_IDS[1],
            ),
        ),
        (
            "wrong_required_membership",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                required_rule_ids=tuple(
                    reversed(rejected_verdict.required_rule_ids)
                ),
            ),
        ),
        (
            "wrong_outcome",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                outcome="blocked",
            ),
        ),
        (
            "passed_true",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                passed=True,
            ),
        ),
        (
            "blocks_scope_action_false",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                blocks_scope_action=False,
            ),
        ),
        (
            "wrong_reason",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                reason=COMBINED_REQUIRED_RULE_INVALID_REASON,
            ),
        ),
        (
            "nonempty_evaluated_rule_ids",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                evaluated_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "nonempty_rule_evaluations",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                rule_evaluations=(rejected_vector[0],),
            ),
        ),
        (
            "nonempty_invalid_rule_ids",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                invalid_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "nonempty_blocked_rule_ids",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                blocked_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "nonempty_failing_rule_ids",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                failing_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "aggregation_io_used_true",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                rejected_verdict,
                aggregation_io_used=True,
            ),
        ),
        ("subclass", rejected_subclass),
        ("wrong_storage_order", reverse_rejected_storage),
    )
    for case_id, value in rejected_mutations:
        add(
            "rejected_combined_validator_fail_closed",
            case_id,
            ERROR_CODES[7],
            _validation_observation(
                lambda value=value: validate_combined_candidate_verdict_design(
                    value,
                    expected_scope_id=rejected_scope,
                    ordered_rule_evaluations=rejected_vector,
                    candidate_index=0,
                    dispatcher_call_count=len(rejected_vector),
                    aggregator_call_count=1,
                )
            ),
        )

    normal_vector, normal_verdict = _design_combined_verdict(
        rejected_scope, "passed"
    )
    copied_normal_vector = tuple([*normal_vector])
    copied_normal_verdict = _forged_dataclass(
        CombinedAdmissionCandidateVerdict,
        normal_verdict,
        rule_evaluations=copied_normal_vector,
    )
    branch_isolation_cases = (
        (
            "normal_vector_rejects_empty_diagnostics_invalid",
            normal_vector,
            rejected_verdict,
        ),
        (
            "rejected_vector_rejects_retained_passed",
            rejected_vector,
            normal_verdict,
        ),
        (
            "rejected_vector_rejects_retained_blocked",
            rejected_vector,
            _design_combined_verdict(rejected_scope, "blocked")[1],
        ),
        (
            "rejected_vector_rejects_retained_invalid",
            rejected_vector,
            _design_combined_verdict(rejected_scope, "invalid")[1],
        ),
        (
            "normal_vector_rejects_copied_tuple",
            normal_vector,
            copied_normal_verdict,
        ),
    )
    for case_id, expected_vector, value in branch_isolation_cases:
        add(
            "combined_validator_branch_isolation_fail_closed",
            case_id,
            ERROR_CODES[7],
            _validation_observation(
                lambda value=value, expected_vector=expected_vector: (
                    validate_combined_candidate_verdict_design(
                        value,
                        expected_scope_id=rejected_scope,
                        ordered_rule_evaluations=expected_vector,
                        candidate_index=0,
                        dispatcher_call_count=len(expected_vector),
                        aggregator_call_count=1,
                    )
                )
            ),
        )

    vector, verdict = _design_combined_verdict(SCOPE_IDS[0], "passed")

    class VerdictSubclass(CombinedAdmissionCandidateVerdict):
        pass

    verdict_subclass = VerdictSubclass(**vars(verdict))
    copied_vector = tuple([*vector])
    reverse_verdict_storage = object.__new__(CombinedAdmissionCandidateVerdict)
    for name in reversed(COMBINED_RESULT_FIELDS):
        object.__setattr__(
            reverse_verdict_storage, name, vars(verdict)[name]
        )
    verdict_mutations = (
        ("subclass", verdict_subclass, SCOPE_IDS[0], vector),
        ("wrong_scope", verdict, SCOPE_IDS[1], vector),
        (
            "wrong_membership",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                verdict,
                evaluated_rule_ids=tuple(reversed(verdict.evaluated_rule_ids)),
            ),
            SCOPE_IDS[0],
            vector,
        ),
        (
            "copied_vector",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                verdict,
                rule_evaluations=copied_vector,
            ),
            SCOPE_IDS[0],
            vector,
        ),
        (
            "wrong_schema",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                verdict,
                schema_version="wrong",
            ),
            SCOPE_IDS[0],
            vector,
        ),
        (
            "malformed_result",
            _forged_dataclass(
                CombinedAdmissionCandidateVerdict,
                verdict,
                passed=1,
            ),
            SCOPE_IDS[0],
            vector,
        ),
        (
            "wrong_storage_order",
            reverse_verdict_storage,
            SCOPE_IDS[0],
            vector,
        ),
    )
    for case_id, value, expected_scope, expected_vector in verdict_mutations:
        add(
            "combined_result_validator_fail_closed",
            case_id,
            ERROR_CODES[7],
            _validation_observation(
                lambda value=value, expected_scope=expected_scope,
                expected_vector=expected_vector: (
                    validate_combined_candidate_verdict_design(
                        value,
                        expected_scope_id=expected_scope,
                        ordered_rule_evaluations=expected_vector,
                        candidate_index=0,
                        dispatcher_call_count=len(expected_vector),
                        aggregator_call_count=1,
                    )
                )
            ),
        )

    add(
        "error_exception_inheritance",
        "StageAdmissionOrchestrationError",
        True,
        issubclass(StageAdmissionOrchestrationError, Exception),
    )
    add("current_permission_false", "constant", False, CURRENT_PERMISSION)
    add(
        "action_permission_granted_false",
        "constant",
        False,
        ACTION_PERMISSION_GRANTED,
    )
    add(
        "authorized_execution_count_zero",
        "constant",
        0,
        AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
    )
    add(
        "actual_dispatcher_calls_zero",
        "constant",
        0,
        ACTUAL_DISPATCHER_CALL_COUNT,
    )
    add(
        "actual_handler_calls_zero",
        "constant",
        0,
        ACTUAL_HANDLER_CALL_COUNT,
    )
    add(
        "actual_aggregator_calls_zero",
        "constant",
        0,
        ACTUAL_AGGREGATOR_CALL_COUNT,
    )
    return rows


TRUTH_ROW_COUNT = 307
TRUTH_GROUP_COUNT = 50


def _safety_rows() -> list[dict[str, str]]:
    items = (
        ("actual_dispatcher_calls", "0", "0"),
        ("actual_handler_calls", "0", "0"),
        ("actual_aggregator_calls", "0", "0"),
        ("network", "false", "false"),
        ("provider", "false", "false"),
        ("download", "false", "false"),
        ("raw", "false", "false"),
        ("torch", "false", "false"),
        ("model", "false", "false"),
        ("checkpoint", "false", "false"),
        ("dataloader", "false", "false"),
        ("forward", "false", "false"),
        ("loss", "false", "false"),
        ("backward", "false", "false"),
        ("optimizer", "false", "false"),
        ("scheduler", "false", "false"),
        ("parameter_update", "false", "false"),
        ("checkpoint_write", "false", "false"),
        ("training_result", "false", "false"),
        ("current_permission", "false", "false"),
        ("authorized_execution_count", "0", "0"),
        ("orchestrator_implementation", "false", "false"),
        ("training_integration", "false", "false"),
        ("action_permission", "false", "false"),
        ("feature_audit_completed", "false", "false"),
        ("ready_for_training", "false", "false"),
        ("Exact15_runtime_modified", "false", "false"),
        ("aggregator_implementation_modified", "false", "false"),
        ("combined_permission_contract_modified", "false", "false"),
        ("design_oracle_io", "false", "false"),
    )
    return [
        {
            "safety_order": str(order),
            "safety_item": name,
            "expected": expected,
            "observed": observed,
            "safety_passed": str(expected == observed).lower(),
        }
        for order, (name, expected, observed) in enumerate(items, 1)
    ]


@dataclass(frozen=True)
class FrozenSource:
    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_blob: str
    index_mode: str
    index_blob: str
    index_stage: int
    filesystem_sha256: str
    content: bytes


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_runtime_guard() -> None:
    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != CANONICAL_PYTHON_VERSION
    ):
        raise ValueError("canonical evidence runtime requires CPython 3.10.4")


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


def _strict_head(root: Path) -> str:
    value = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    if re.fullmatch(rb"[0-9a-f]{40}\n", value) is None:
        raise ValueError("HEAD commit malformed")
    return value[:-1].decode()


Identity = tuple[int, int, int, int, int, int]


def _identity(item: os.stat_result) -> Identity:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


def _read_all(descriptor: int, maximum: int = 100 * 1024 * 1024) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > maximum:
            raise ValueError("pinned read exceeds maximum")
        chunks.append(chunk)


def _pinned_regular_read(root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe relative path")
    absolute_root = Path(os.path.abspath(root))
    root_identity = _identity(os.lstat(absolute_root))
    root_fd = os.open(
        absolute_root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    descriptors = [root_fd]
    bindings: list[tuple[int, str, int, Identity]] = []
    leaf_fd: int | None = None
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("root stat/open race")
        parent_fd = root_fd
        for component in relative.parts[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            identity = _identity(before)
            if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
                raise ValueError("unsafe parent component")
            child_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent_fd,
            )
            descriptors.append(child_fd)
            if _identity(os.fstat(child_fd)) != identity:
                raise ValueError("parent component stat/open race")
            bindings.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd
        name = relative.parts[-1]
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        leaf_identity = _identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > 100 * 1024 * 1024
        ):
            raise ValueError("unsafe leaf")
        leaf_fd = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        if _identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("leaf stat/open race")
        content = _read_all(leaf_fd)
        if (
            _identity(
                os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != leaf_identity
            or _identity(os.fstat(leaf_fd)) != leaf_identity
        ):
            raise ValueError("leaf final drift")
        for lexical_parent, component, child_fd, identity in reversed(bindings):
            if (
                _identity(
                    os.stat(
                        component,
                        dir_fd=lexical_parent,
                        follow_symlinks=False,
                    )
                )
                != identity
                or _identity(os.fstat(child_fd)) != identity
            ):
                raise ValueError("parent component final drift")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(absolute_root)) != root_identity
        ):
            raise ValueError("root final drift")
        return content
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _parse_index(content: bytes, path: str) -> tuple[str, str, int]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, stage = metadata.split(" ")
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if observed != path or mode != "100644":
        raise ValueError("index entry drift")
    return mode, blob, int(stage)


def _parse_tree(content: bytes, path: str) -> tuple[str, str]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if observed != path or mode != "100644" or kind != "blob":
        raise ValueError("tree entry drift")
    return mode, blob


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> tuple[FrozenSource, ...]:
    _canonical_runtime_guard()
    if head_ref != "HEAD":
        raise ValueError("source snapshot head_ref must be HEAD")
    root = Path(os.path.abspath(repo_root))
    initial_head = _strict_head(root)
    identity = _git(
        root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, initial_head)
    if (
        len(SOURCE_BOUNDARY) != 16
        or len(set(SOURCE_PATHS)) != 16
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact16 source boundary drift")
    records = []
    for relative in SOURCE_PATHS:
        raw = relative.as_posix()
        index_mode, index_blob, index_stage = _parse_index(
            _git(root, "ls-files", "--stage", "--", raw), raw
        )
        base_mode, base_blob = _parse_tree(
            _git(root, "ls-tree", BASE_COMMIT, "--", raw), raw
        )
        base = _git(root, "cat-file", "blob", base_blob)
        index = _git(root, "cat-file", "blob", index_blob)
        filesystem = _pinned_regular_read(root, relative)
        expected = SOURCE_SHA256[relative]
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
            or base != index
            or index != filesystem
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source bytes/SHA drift: {relative}")
        records.append(
            FrozenSource(
                relative,
                expected,
                base_mode,
                base_blob,
                index_mode,
                index_blob,
                index_stage,
                _sha(filesystem),
                filesystem,
            )
        )
    if _strict_head(root) != initial_head:
        raise ValueError("source snapshot HEAD drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, initial_head)
    return tuple(records)


def _source(snapshot: Sequence[FrozenSource], suffix: str) -> FrozenSource:
    matches = tuple(
        item
        for item in snapshot
        if item.relative_path.as_posix().endswith(suffix)
    )
    if len(matches) != 1:
        raise ValueError(f"source missing/duplicate: {suffix}")
    return matches[0]


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


TRUE_READINESS = (
    "combined_permission_semantics_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "pre_036_resolved",
    "stage_global_rule_evaluation_orchestration_contract_frozen",
    "stage_global_rule_partition_frozen",
    "stage_global_exactly_once_semantics_frozen",
    "dispatcher_call_order_frozen",
    "dispatcher_call_cardinality_frozen",
    "context_routing_plan_frozen",
    "candidate_vector_assembly_contract_frozen",
    "aggregator_call_order_frozen",
    "orchestration_error_contract_frozen",
    "ready_for_stage_global_rule_evaluation_orchestration_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "stage_global_rule_evaluation_orchestration_implemented",
    "training_orchestrator_integration_implemented",
    "download_action_implemented",
    "training_action_implemented",
    "current_permission",
    "feature_semantics_audit_completed",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known",
    "real_training_ready",
    "ready_for_training",
)


def build_artifacts(
    snapshot: Sequence[FrozenSource],
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, bytes]:
    _canonical_runtime_guard()
    if (
        type(snapshot) not in (tuple, list)
        or len(snapshot) != 16
        or tuple(item.relative_path for item in snapshot) != SOURCE_PATHS
    ):
        raise ValueError("source snapshot inventory drift")
    for item, (path, expected) in zip(snapshot, SOURCE_BOUNDARY, strict=True):
        if (
            type(item) is not FrozenSource
            or item.relative_path.as_posix() != path
            or item.expected_sha256 != expected
            or item.filesystem_sha256 != expected
            or _sha(item.content) != expected
            or item.base_tree_mode != "100644"
            or item.index_mode != "100644"
            or item.index_stage != 0
            or item.base_tree_blob != item.index_blob
        ):
            raise ValueError("source attestation drift")
    contract_rows = _contract_rows()
    call_rows = _call_plan_rows()
    truth_rows = _truth_rows()
    safety_rows = _safety_rows()
    if (
        len(contract_rows) != 54
        or len(call_rows) != 53
        or len(truth_rows) != TRUTH_ROW_COUNT
        or len({row["case_group"] for row in truth_rows}) != TRUTH_GROUP_COUNT
        or len(safety_rows) != 30
        or any(row["contract_passed"] != "true" for row in contract_rows)
        or any(row["contract_passed"] != "true" for row in call_rows)
        or any(row["case_passed"] != "true" for row in truth_rows)
        or any(row["safety_passed"] != "true" for row in safety_rows)
    ):
        raise ValueError("design evidence row contract drift")
    issue_content = _source(
        snapshot, "cross_rule_aggregation_issue_readiness_inventory.csv"
    ).content
    if _sha(issue_content) != SOURCE_BOUNDARY[7][1]:
        raise ValueError("issue continuity drift")
    payloads = {
        PUBLIC_API_RESULT_FILENAME: _csv_bytes(PUBLIC_API_COLUMNS, contract_rows),
        CALL_PLAN_FILENAME: _csv_bytes(CALL_PLAN_COLUMNS, call_rows),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_FILENAME: issue_content,
    }
    root = Path(os.path.abspath(repo_root))
    support_sha = {
        path.as_posix(): _sha(_pinned_regular_read(root, path))
        for path in SUPPORT_PATHS
    }
    source_rows = [
        {
            "source_order": order,
            "path": item.relative_path.as_posix(),
            "sha256": item.expected_sha256,
            "base_tree_mode": item.base_tree_mode,
            "base_tree_blob": item.base_tree_blob,
            "index_mode": item.index_mode,
            "index_blob": item.index_blob,
            "index_stage": item.index_stage,
            "filesystem_sha256": item.filesystem_sha256,
        }
        for order, item in enumerate(snapshot, 1)
    ]
    scope_rows = [
        {
            "scope_order": order,
            "scope_id": scope,
            "required_rule_ids": list(required),
            "stage_global_rule_ids": list(
                STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
            ),
            "candidate_rule_ids": list(CANDIDATE_RULE_IDS_BY_SCOPE[scope]),
            "candidate_rule_count": len(CANDIDATE_RULE_IDS_BY_SCOPE[scope]),
            "dispatcher_cardinality": (
                f"{len(STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])} + "
                f"{len(CANDIDATE_RULE_IDS_BY_SCOPE[scope])}*N"
            ),
            "aggregator_cardinality": "N",
        }
        for order, (scope, required) in enumerate(SCOPE_CONTRACT, 1)
    ]
    manifest = {
        "project": PROJECT,
        "stage": STAGE,
        "step": STEP,
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "source_boundary_name": "fixed_ordered_exact16_committed_source_boundary",
        "source_boundary_count": 16,
        "source_boundary": source_rows,
        "exact14_runtime_actual_sha256": SOURCE_BOUNDARY[10][1],
        "future_public_api": {
            "name": "orchestrate_stage_admission_scope",
            "signature": (
                "orchestrate_stage_admission_scope(scope_id: str, "
                "candidate_inputs: tuple[AdmissionCandidateOrchestrationInput, "
                "...], *, batch_context: Mapping[str, object] | None, "
                "stage_authorization_context: Mapping[str, object] | None) "
                "-> StageAdmissionOrchestrationResult"
            ),
            "implemented": False,
            "parameter_defaults": {
                "scope_id": "absent",
                "candidate_inputs": "absent",
                "batch_context": "absent",
                "stage_authorization_context": "absent",
            },
            "dispatcher_injection": False,
            "aggregator_injection": False,
            "registry_injection": False,
        },
        "input_contract": {
            "class_name": "AdmissionCandidateOrchestrationInput",
            "field_count": 3,
            "fields": list(INPUT_FIELDS),
            "frozen": True,
            "slots": False,
            "mapping_copy_or_iteration": False,
            "object_identity_preserved": True,
        },
        "candidate_result_contract": {
            "class_name": "CandidateAdmissionOrchestrationResult",
            "field_count": 5,
            "fields": list(CANDIDATE_RESULT_FIELDS),
            "frozen": True,
            "slots": False,
        },
        "stage_result_contract": {
            "class_name": "StageAdmissionOrchestrationResult",
            "schema_version": STAGE_RESULT_SCHEMA_VERSION,
            "field_count": 12,
            "fields": list(STAGE_RESULT_FIELDS),
            "frozen": True,
            "slots": False,
            "orchestration_io_used": False,
            "action_permission_granted": False,
            "action_permission_policy": (
                "always_false_even_when_all_combined_verdicts_passed"
            ),
        },
        "error_contract": {
            "class_name": "StageAdmissionOrchestrationError",
            "inherits_exception": True,
            "frozen": True,
            "slots": False,
            "field_count": 8,
            "fields": list(ERROR_FIELDS),
            "code_count": 8,
            "codes": list(ERROR_CODES),
            "pre_dispatch_projection": {
                "candidate_index": -1,
                "admission_rule_id": "",
                "dispatcher_call_count": 0,
                "aggregator_call_count": 0,
                "reason": "code",
                "cause_type": "",
            },
            "success_returns_stage_result_only": True,
            "all_failures_raise_error": True,
            "error_is_never_normal_return_value": True,
            "caught_cause_base": "Exception_only_not_BaseException",
            "raise_from_cause": True,
            "cause_type_projection": "type(cause).__name__",
            "cause_repr_used": False,
            "deterministic_reason_projection": True,
            "exception_args_equal_reason_singleton": True,
            "error_stops_immediately": True,
            "partial_stage_result_returned": False,
        },
        "failure_coordinate_formulas": {
            "definitions": {
                "G": "stage_global_rule_count",
                "R": "candidate_scoped_rule_count",
                "i": "zero_based_candidate_index",
                "j": "one_based_candidate_rule_position",
                "k": "one_based_stage_global_rule_position",
            },
            "attempt_inclusive": True,
            "stage_global_dispatch": {
                "candidate_index": "-1",
                "dispatcher_call_count": "k",
                "aggregator_call_count": "0",
            },
            "candidate_dispatch": {
                "dispatcher_call_count": "G + i*R + j",
                "aggregator_call_count": "i",
            },
            "candidate_aggregator": {
                "admission_rule_id": "",
                "dispatcher_call_count": "G + (i+1)*R",
                "aggregator_call_count": "i+1",
            },
            "exact4_scope_matrix_executed": True,
            "candidate_indices": [0, 1, 2],
        },
        "result_invariant_validators": {
            "unified_rule_evaluation": {
                "exact_type_and_subclass_rejection": True,
                "exact13_storage_and_field_order": True,
                "exact_top_level_types": True,
                "reconstructability": True,
                "schema_and_outcome_projection": True,
                "exact_tuple_representations": True,
                "evaluator_io_used_false": True,
                "expected_rule_name_and_adapter_identity": True,
                "rejected_is_structurally_valid": True,
                "failure_code": ERROR_CODES[6],
            },
            "combined_candidate_verdict": {
                "exact_type_and_subclass_rejection": True,
                "exact13_storage_and_field_order": True,
                "reconstructability": True,
                "expected_scope_and_membership": True,
                "normal_outcome_retained_vector_identity_required": True,
                "rejected_input_complete_vector_required": True,
                "rejected_fail_closed_empty_diagnostics_required": True,
                "rejected_fail_closed_retained_vector_forbidden": True,
                "rejected_aggregator_reason": (
                    COMBINED_EVALUATION_INVARIANT_INVALID_REASON
                ),
                "aggregator_admissible_child_outcomes": list(
                    AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
                ),
                "rejected_precedes_blocked_and_invalid_projection": True,
                "aggregation_io_used_false": True,
                "passed_blocked_invalid_projection": True,
                "failure_code": ERROR_CODES[7],
            },
        },
        "validation_precedence": [
            "scope_exact_str_and_exact4_membership",
            "candidate_inputs_exact_nonempty_tuple",
            "all_candidate_input_exact_type_and_invariants",
            "batch_context_type",
            "stage_authorization_context_type",
            "stage_global_dispatch_plan",
            "all_stage_global_result_exact13_validation",
            "per_candidate_dispatch_plan",
            "every_candidate_result_exact13_validation",
            "complete_vector_assembly",
            "aggregator_result_exact13_validation",
            "complete_stage_result_construction",
        ],
        "scope_count": 4,
        "scopes": scope_rows,
        "stage_global_rule_ids": ["ADMIT_014", "ADMIT_015"],
        "stage_global_membership": {
            scope: list(STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
            for scope in SCOPE_IDS
        },
        "candidate_scoped_membership": {
            scope: list(CANDIDATE_RULE_IDS_BY_SCOPE[scope])
            for scope in SCOPE_IDS
        },
        "stage_global_sentinel": {
            "name": "STAGE_GLOBAL_CANDIDATE_SENTINEL",
            "immutable_empty_mapping": True,
            "same_identity_within_invocation": True,
            "candidate_specific_keys_absent": True,
        },
        "stage_global_exactly_once": {
            "per_top_level_invocation": True,
            "not_per_candidate": True,
            "no_cross_invocation_cache": True,
            "no_global_mutable_cache": True,
            "same_result_identity_reused_across_candidates": True,
            "call_order": ["ADMIT_014", "ADMIT_015"],
        },
        "context_routing": {
            rule_id: {
                "batch_context_source": values[0],
                "evaluation_context_source": values[1],
                "download_result_context_source": values[2],
                "stage_authorization_context_source": values[3],
            }
            for rule_id, values in _CONTEXT_ROUTING.items()
        },
        "vector_assembly": {
            "ordered_by_scope_required_rule_ids": True,
            "stage_result_identity_inserted": True,
            "candidate_result_identity_inserted": True,
            "copy": False,
            "rebuild_result": False,
            "reevaluate": False,
            "outcome_sort": False,
            "category_group_before_aggregation": False,
            "aggregator_exactly_once_per_candidate": True,
        },
        "normal_result_semantics": {
            "outcomes": ["passed", "blocked", "invalid", "rejected"],
            "short_circuit": False,
            "rejected_reinterpreted_by_orchestrator": False,
            "rejected_delegated_to_aggregator_fail_closed": True,
            "rejected_complete_vector_forwarded": True,
            "rejected_is_aggregator_inadmissible_child_outcome": True,
            "rejected_canonical_empty_diagnostics_accepted": True,
            "rejected_fail_closed_is_not_result_corruption": True,
        },
        "api_result_contract_row_count": 54,
        "call_plan_row_count": 53,
        "truth_matrix": {
            "row_count": TRUTH_ROW_COUNT,
            "group_count": TRUTH_GROUP_COUNT,
            "group_counts": dict(
                sorted(Counter(row["case_group"] for row in truth_rows).items())
            ),
            "pure_design_oracle": True,
            "actual_dispatcher_calls": 0,
            "actual_handler_calls": 0,
            "actual_aggregator_calls": 0,
        },
        "safety_audit": {"row_count": 30},
        "precondition_continuity": {
            "row_count": 45,
            "transition_count": 0,
            "complete_count": 43,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "pre_036_status": "complete/non-blocking",
            "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
        },
        "issue_continuity": {
            "row_count": 30,
            "byte_identical": True,
            "sha256": _sha(issue_content),
            "transition_count": 0,
            "new_issue_count": 0,
            "remaining_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            ],
        },
        "readiness": {
            **{name: True for name in TRUE_READINESS},
            **{name: False for name in FALSE_READINESS},
        },
        "runtime_safety_boundary": {
            "real_orchestrator_implemented": False,
            "actual_dispatcher_called": False,
            "actual_handler_called": False,
            "actual_aggregator_called": False,
            "download_action_performed": False,
            "training_action_performed": False,
            "action_permission_granted": False,
            "current_permission": False,
            "authorized_admit_015_training_execution_count": 0,
            "feature_semantics_audit_still_required": True,
            "ready_for_training": False,
        },
        "v1_action_permission_boundary": {
            "action_permission_granted": False,
            "all_combined_verdicts_passed_does_not_grant_action": True,
            "combined_verdict_is_diagnostic_not_execution_authorization": True,
            "rules_and_diagnostic_aggregation_are_in_memory_only": True,
            "download_or_training_triggered": False,
            "future_action_permission_bridge_requires_separate_contract_and_gate": True,
            "current_permission": False,
            "authorized_admit_015_training_execution_count": 0,
        },
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in (
                ("warhead_only", "A"),
                ("linker_plus_warhead", "B"),
                ("scaffold_plus_warhead", "B2"),
                ("scaffold_only", "B3"),
                ("scaffold_plus_linker_plus_warhead", "C"),
            )
        ],
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final training-feature "
            "contract"
        ),
        "feature_semantics_warning": (
            "A feature-semantics audit remains mandatory before training; "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain unresolved"
        ),
        "design_only_boundary": {
            "real_orchestrator_implemented": False,
            "candidate_loop_runtime_implemented": False,
            "dispatcher_loop_implemented": False,
            "download_or_training_action_implemented": False,
        },
        "infrastructure_hardening": {
            "lifecycle_mode_count": 4,
            "pre_commit_lifecycle_supported": True,
            "detached_candidate_post_commit_supported": True,
            "formal_main_post_commit_unpushed_supported": True,
            "formal_main_post_push_supported": True,
            "formal_commit_subject_frozen": True,
            "formal_main_real_local_git_simulation_passed": True,
            "source_parent_chain_fd_pinned": True,
            "source_initial_final_strict_head": True,
            "source_base_ancestry_verified": True,
            "exact6_parent_root_all_leaf_fd_pinned": True,
            "materializer_build_before_mutation": True,
            "materializer_o_excl_and_fsync": True,
            "materializer_rename_noreplace": True,
            "materializer_gpfs_einval_fail_closed": True,
            "materializer_authenticated_staging_retained": True,
            "materializer_no_os_replace": True,
            "materializer_no_destructive_cleanup": True,
            "existing_exact_set_inode_preserving_noop": True,
            "checker_complete_index_bytes": True,
            "checker_git_write_tree_snapshot": False,
            "full_recursive_lifecycle_run_count": 2,
            "final_recursive_lifecycle_is_last_filesystem_validation": True,
        },
        "support_file_sha256": support_sha,
        "derived_output_sha256": {
            (DEFAULT_OUTPUT_ROOT / name).as_posix(): _sha(content)
            for name, content in payloads.items()
        },
        "manifest_self_sha256_recorded": False,
        "exact10_file_count": 10,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "all_checks_passed": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FLAGS = (
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
)
RENAME_NOREPLACE = 1
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


class MaterializationRetentionError(RuntimeError):
    def __init__(self, retained_path: Path | None) -> None:
        self.authenticated_retained_path = retained_path
        super().__init__(
            "materialization failed closed; no cleanup performed; "
            f"authenticated_retained_path={retained_path}"
        )


def _read_output_set(root: Path) -> dict[str, bytes]:
    absolute = Path(os.path.abspath(root))
    parent = absolute.parent
    parent_identity = _identity(os.lstat(parent))
    root_identity = _identity(os.lstat(absolute))
    parent_fd = os.open(parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    leaves: dict[str, int] = {}
    identities: dict[str, Identity] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent race")
        root_fd = os.open(absolute.name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root race")
        inventory = tuple(sorted(os.listdir(root_fd)))
        if inventory != tuple(sorted(OUTPUT_FILES)):
            raise ValueError("output inventory drift")
        for name in OUTPUT_FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
                raise ValueError("output leaf unsafe")
            identities[name] = _identity(item)
            leaves[name] = os.open(name, READ_FLAGS, dir_fd=root_fd)
            if _identity(os.fstat(leaves[name])) != identities[name]:
                raise ValueError("output leaf race")
        result = {name: _read_all(leaves[name]) for name in OUTPUT_FILES}
        for name in OUTPUT_FILES:
            if (
                _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != identities[name]
                or _identity(os.fstat(leaves[name])) != identities[name]
            ):
                raise ValueError("output leaf final drift")
        if (
            tuple(sorted(os.listdir(root_fd))) != inventory
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
            or _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(absolute)) != root_identity
        ):
            raise ValueError("output final binding drift")
        return result
    finally:
        for descriptor in leaves.values():
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _materialize(
    output_root: Path,
    payloads: Mapping[str, bytes],
    *,
    repo_root: Path,
    hook: Callable[[str, Path], None] | None = None,
) -> Path:
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or any(type(content) is not bytes for content in payloads.values())
    ):
        raise ValueError("output payload inventory drift")
    callback = (lambda event, path: None) if hook is None else hook
    candidate = Path(output_root)
    if not candidate.is_absolute() and ".." in candidate.parts:
        raise ValueError("relative output escape")
    root = (
        Path(os.path.abspath(candidate))
        if candidate.is_absolute()
        else Path(os.path.abspath(repo_root)) / candidate
    )
    parent = root.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("output parent unsafe")
    parent_identity = _identity(os.lstat(parent))
    if root.exists() or root.is_symlink():
        before = os.lstat(root)
        if _read_output_set(root) != payloads:
            raise ValueError("existing output payload drift")
        after = os.lstat(root)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ValueError("existing output inode drift")
        return root
    parent_fd = os.open(parent, DIRECTORY_FLAGS)
    staging_name: str | None = None
    staging_fd: int | None = None
    staging_identity: Identity | None = None
    published = False
    try:
        if (
            _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
        ):
            raise ValueError("materialization parent race")
        for _ in range(64):
            proposed = f"{STAGING_NAME_PREFIX}{secrets.token_hex(16)}"
            try:
                os.mkdir(proposed, 0o700, dir_fd=parent_fd)
                staging_name = proposed
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        staging_fd = os.open(staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        for name, content in payloads.items():
            descriptor = os.open(name, WRITE_FLAGS, 0o600, dir_fd=staging_fd)
            try:
                _write_all(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        staging_path = parent / staging_name
        if _read_output_set(staging_path) != payloads:
            raise ValueError("staging verification failed")
        callback("before_rename", staging_path)
        if (
            _identity(os.fstat(staging_fd)) != staging_identity
            or _identity(
                os.stat(
                    staging_name, dir_fd=parent_fd, follow_symlinks=False
                )
            )
            != staging_identity
        ):
            raise ValueError("staging final drift")
        try:
            os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        if _RENAMEAT2 is None:
            raise ValueError("renameat2 required")
        if _RENAMEAT2(
            parent_fd,
            os.fsencode(staging_name),
            parent_fd,
            os.fsencode(root.name),
            RENAME_NOREPLACE,
        ):
            number = ctypes.get_errno()
            if number == errno.EINVAL:
                raise OSError(number, "GPFS renameat2 EINVAL fail closed")
            raise OSError(number, os.strerror(number))
        published = True
        staging_name = None
        if _read_output_set(root) != payloads:
            raise ValueError("published output verification failed")
        os.fsync(parent_fd)
        return root
    except BaseException as error:
        retained = None
        if (
            not published
            and staging_name is not None
            and staging_fd is not None
            and staging_identity is not None
        ):
            try:
                if (
                    _identity(
                        os.stat(
                            staging_name,
                            dir_fd=parent_fd,
                            follow_symlinks=False,
                        )
                    )
                    == staging_identity
                    and _identity(os.fstat(staging_fd)) == staging_identity
                ):
                    retained = parent / staging_name
            except OSError:
                pass
        if retained is not None:
            raise MaterializationRetentionError(retained) from error
        raise
    finally:
        if staging_fd is not None:
            os.close(staging_fd)
        os.close(parent_fd)


def run_covapie_stage_global_rule_evaluation_orchestration_contract_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    payloads = build_artifacts(snapshot, repo_root=repo_root)
    root = _materialize(output_root, payloads, repo_root=repo_root)
    return {
        "snapshot": snapshot,
        "manifest": json.loads(payloads[MANIFEST_FILENAME]),
        "output_root": root,
    }


__all__ = (
    "AdmissionCandidateOrchestrationInput",
    "CandidateAdmissionOrchestrationResult",
    "StageAdmissionOrchestrationResult",
    "StageAdmissionOrchestrationError",
    "STAGE_GLOBAL_CANDIDATE_SENTINEL",
    "classify_stage_global_orchestration_contract_design",
)


if __name__ == "__main__":
    run_covapie_stage_global_rule_evaluation_orchestration_contract_v1()
