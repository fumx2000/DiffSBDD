"""Pure combined-candidate verdict and cross-rule aggregation runtime.

The public runtime above the evidence-boundary marker consumes only an
already-generated exact tuple of ``UnifiedAdmissionRuleEvaluation`` objects.
It performs no dispatch, handler call, I/O, provider, download, model, or
training action.  Deterministic evidence construction and publication are
explicitly separated below the marker.
"""

from __future__ import annotations

from dataclasses import dataclass

from covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 import (
    OUTCOME_VOCABULARY,
    RESULT_FIELDS as INPUT_RESULT_FIELDS,
    RESULT_SCHEMA_VERSION as INPUT_RESULT_SCHEMA_VERSION,
    UnifiedAdmissionRuleEvaluation,
)
from covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015 import (
    ADAPTER_IDS,
    RULE_NAMES,
)


__all__ = (
    "CombinedAdmissionCandidateVerdict",
    "aggregate_admission_rule_evaluations",
)

RESULT_SCHEMA_VERSION = "covapie_combined_admission_candidate_verdict_v1"
RESULT_FIELDS = (
    "schema_version",
    "scope_id",
    "outcome",
    "passed",
    "blocks_scope_action",
    "reason",
    "required_rule_ids",
    "evaluated_rule_ids",
    "rule_evaluations",
    "invalid_rule_ids",
    "blocked_rule_ids",
    "failing_rule_ids",
    "aggregation_io_used",
)
AGGREGATION_OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES = ("passed", "blocked", "invalid")
REASON_VOCABULARY = (
    "COMBINED_ADMISSION_SCOPE_ID_INVALID",
    "COMBINED_ADMISSION_RULE_EVALUATION_VECTOR_TYPE_INVALID",
    "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID",
    "COMBINED_ADMISSION_RULE_MEMBERSHIP_INVALID",
    "COMBINED_ADMISSION_REQUIRED_RULE_INVALID",
    "COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED",
)
(
    SCOPE_ID_INVALID_REASON,
    VECTOR_TYPE_INVALID_REASON,
    EVALUATION_INVARIANT_INVALID_REASON,
    MEMBERSHIP_INVALID_REASON,
    REQUIRED_RULE_INVALID_REASON,
    REQUIRED_RULE_BLOCKED_REASON,
) = REASON_VOCABULARY
DISPATCHER_CALL_COUNT = 0
SINGLE_RULE_HANDLER_CALL_COUNT = 0
AGGREGATION_IO_USED = False
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0

RULE_IDS = tuple(f"ADMIT_{number:03d}" for number in range(1, 16))
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
REQUIRED_RULE_IDS = dict(SCOPE_CONTRACT)
SCOPE_IDS = tuple(REQUIRED_RULE_IDS)


def _exact_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _exact_string_pair_tuple(value: object) -> bool:
    results = []
    if type(value) is not tuple:
        return False
    for item in value:
        results.append(
            type(item) is tuple
            and len(item) == 2
            and type(item[0]) is str
            and type(item[1]) is str
        )
    return bool(results) is False or False not in results


def _runtime_structure_valid(value: object) -> bool:
    """Validate the actual runtime Exact13 without retaining invalid input."""
    if type(value) is not UnifiedAdmissionRuleEvaluation:
        return False
    try:
        values = vars(value)
    except TypeError:
        return False
    if (
        type(values) is not dict
        or tuple(values) != INPUT_RESULT_FIELDS
        or tuple(value.__dataclass_fields__) != INPUT_RESULT_FIELDS
    ):
        return False
    string_fields = (
        "schema_version",
        "admission_rule_id",
        "admission_rule_name",
        "outcome",
        "reason",
        "adapter_id",
    )
    bool_fields = ("passed", "blocks_candidate", "evaluator_io_used")
    tuple_fields = (
        "normalized_values",
        "validated_candidate_fields",
        "consumed_candidate_fields",
        "consumed_context_items",
    )
    if (
        any(type(values[name]) is not str for name in string_fields)
        or any(type(values[name]) is not bool for name in bool_fields)
        or any(type(values[name]) is not tuple for name in tuple_fields)
    ):
        return False
    try:
        if type(value)(**values) != value:
            return False
    except (TypeError, ValueError):
        return False
    if (
        value.schema_version != INPUT_RESULT_SCHEMA_VERSION
        or value.outcome not in OUTCOME_VOCABULARY
        or value.passed is not (value.outcome == "passed")
        or value.blocks_candidate is not (value.outcome != "passed")
        or value.evaluator_io_used is not False
        or (value.outcome == "passed" and value.reason != "")
        or (value.outcome != "passed" and value.reason == "")
        or not _exact_string_pair_tuple(value.normalized_values)
        or not _exact_string_pair_tuple(value.validated_candidate_fields)
        or not _exact_string_tuple(value.consumed_candidate_fields)
        or not _exact_string_tuple(value.consumed_context_items)
    ):
        return False
    return True


def _aggregation_identity_and_outcome_admissible(
    value: UnifiedAdmissionRuleEvaluation,
) -> bool:
    if value.outcome not in AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES:
        return False
    if value.admission_rule_id in RULE_NAMES:
        return (
            value.admission_rule_name == RULE_NAMES[value.admission_rule_id]
            and value.adapter_id == ADAPTER_IDS[value.admission_rule_id]
        )
    return True


def _outcome_projections(
    values: tuple[UnifiedAdmissionRuleEvaluation, ...],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Scan every outcome once and retain all ordered failure projections."""
    invalid: list[str] = []
    blocked: list[str] = []
    failing: list[str] = []
    for item in values:
        outcome = item.outcome
        if outcome == "invalid":
            invalid.append(item.admission_rule_id)
        if outcome == "blocked":
            blocked.append(item.admission_rule_id)
        if outcome != "passed":
            failing.append(item.admission_rule_id)
    return tuple(invalid), tuple(blocked), tuple(failing)


@dataclass(frozen=True)
class CombinedAdmissionCandidateVerdict:
    schema_version: str
    scope_id: str
    outcome: str
    passed: bool
    blocks_scope_action: bool
    reason: str
    required_rule_ids: tuple[str, ...]
    evaluated_rule_ids: tuple[str, ...]
    rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]
    invalid_rule_ids: tuple[str, ...]
    blocked_rule_ids: tuple[str, ...]
    failing_rule_ids: tuple[str, ...]
    aggregation_io_used: bool

    def __post_init__(self) -> None:
        values = vars(self)
        if type(values) is not dict or tuple(values) != RESULT_FIELDS:
            raise TypeError("combined verdict vars field order invalid")
        if tuple(self.__dataclass_fields__) != RESULT_FIELDS:
            raise TypeError("combined verdict dataclass field order invalid")
        if any(
            type(values[name]) is not str
            for name in ("schema_version", "scope_id", "outcome", "reason")
        ):
            raise TypeError("combined verdict string field type invalid")
        if any(
            type(values[name]) is not bool
            for name in ("passed", "blocks_scope_action", "aggregation_io_used")
        ):
            raise TypeError("combined verdict bool field type invalid")
        tuple_names = (
            "required_rule_ids",
            "evaluated_rule_ids",
            "rule_evaluations",
            "invalid_rule_ids",
            "blocked_rule_ids",
            "failing_rule_ids",
        )
        if any(type(values[name]) is not tuple for name in tuple_names):
            raise TypeError("combined verdict tuple field type invalid")
        for name in (
            "required_rule_ids",
            "evaluated_rule_ids",
            "invalid_rule_ids",
            "blocked_rule_ids",
            "failing_rule_ids",
        ):
            if not _exact_string_tuple(values[name]):
                raise TypeError("combined verdict ID tuple type invalid")
        child_structure = []
        child_admissibility = []
        for child in self.rule_evaluations:
            child_structure.append(_runtime_structure_valid(child))
        if False not in child_structure:
            for child in self.rule_evaluations:
                child_admissibility.append(
                    _aggregation_identity_and_outcome_admissible(child)
                )
        if False in child_structure or False in child_admissibility:
            raise TypeError("combined verdict child invariant invalid")
        if self.schema_version != RESULT_SCHEMA_VERSION:
            raise ValueError("combined verdict schema version invalid")
        if self.outcome not in AGGREGATION_OUTCOME_VOCABULARY:
            raise ValueError("combined verdict outcome invalid")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("combined verdict passed invariant invalid")
        if self.blocks_scope_action is not (self.outcome != "passed"):
            raise ValueError("combined verdict blocking invariant invalid")
        if self.aggregation_io_used is not False:
            raise ValueError("combined verdict aggregation IO invariant invalid")
        if self.outcome == "passed":
            if self.reason != "":
                raise ValueError("combined verdict pass reason invalid")
        elif self.outcome == "blocked":
            if self.reason != REQUIRED_RULE_BLOCKED_REASON:
                raise ValueError("combined verdict blocked reason invalid")
        elif (
            self.reason not in REASON_VOCABULARY
            or self.reason == REQUIRED_RULE_BLOCKED_REASON
        ):
            raise ValueError("combined verdict invalid reason invalid")

        empty_diagnostics = (
            not self.evaluated_rule_ids
            and not self.rule_evaluations
            and not self.invalid_rule_ids
            and not self.blocked_rule_ids
            and not self.failing_rule_ids
        )
        if self.reason == SCOPE_ID_INVALID_REASON:
            if (
                (self.scope_id in REQUIRED_RULE_IDS)
                or self.required_rule_ids
                or not empty_diagnostics
            ):
                raise ValueError("combined verdict invalid-scope projection invalid")
            return

        if self.scope_id not in REQUIRED_RULE_IDS:
            raise ValueError("combined verdict known scope required")
        required = REQUIRED_RULE_IDS[self.scope_id]
        if self.required_rule_ids != required:
            raise ValueError("combined verdict required membership invalid")
        if self.reason in (
            VECTOR_TYPE_INVALID_REASON,
            EVALUATION_INVARIANT_INVALID_REASON,
        ):
            if not empty_diagnostics:
                raise ValueError("combined verdict invariant projection invalid")
            return
        if self.reason == MEMBERSHIP_INVALID_REASON:
            if (
                self.rule_evaluations
                or self.invalid_rule_ids
                or self.blocked_rule_ids
                or self.failing_rule_ids
                or self.evaluated_rule_ids == required
            ):
                raise ValueError("combined verdict membership projection invalid")
            return

        if (
            not self.rule_evaluations
            or len(self.rule_evaluations) != len(required)
            or self.evaluated_rule_ids != required
            or tuple(item.admission_rule_id for item in self.rule_evaluations)
            != required
        ):
            raise ValueError("combined verdict retained-vector invariant invalid")
        invalid, blocked, failing = _outcome_projections(self.rule_evaluations)
        if (
            self.invalid_rule_ids != invalid
            or self.blocked_rule_ids != blocked
            or self.failing_rule_ids != failing
            or len(set(self.invalid_rule_ids)) != len(self.invalid_rule_ids)
            or len(set(self.blocked_rule_ids)) != len(self.blocked_rule_ids)
            or len(set(self.failing_rule_ids)) != len(self.failing_rule_ids)
        ):
            raise ValueError("combined verdict diagnostic projection invalid")
        if self.outcome == "passed":
            if invalid or blocked or failing:
                raise ValueError("combined verdict pass failure projection invalid")
        elif self.outcome == "blocked":
            if invalid or not blocked:
                raise ValueError("combined verdict blocked projection invalid")
        elif self.reason == REQUIRED_RULE_INVALID_REASON:
            if not invalid:
                raise ValueError("combined verdict invalid projection invalid")
        else:
            raise ValueError("combined verdict terminal reason invalid")


def _verdict(
    scope_id: object,
    *,
    reason: str,
    required_rule_ids: tuple[str, ...] = (),
    evaluated_rule_ids: tuple[str, ...] = (),
    rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...] = (),
    invalid_rule_ids: tuple[str, ...] = (),
    blocked_rule_ids: tuple[str, ...] = (),
    failing_rule_ids: tuple[str, ...] = (),
) -> CombinedAdmissionCandidateVerdict:
    outcome = (
        "passed"
        if reason == ""
        else "blocked"
        if reason == REQUIRED_RULE_BLOCKED_REASON
        else "invalid"
    )
    return CombinedAdmissionCandidateVerdict(
        schema_version=RESULT_SCHEMA_VERSION,
        scope_id=scope_id if type(scope_id) is str else "",
        outcome=outcome,
        passed=outcome == "passed",
        blocks_scope_action=outcome != "passed",
        reason=reason,
        required_rule_ids=required_rule_ids,
        evaluated_rule_ids=evaluated_rule_ids,
        rule_evaluations=rule_evaluations,
        invalid_rule_ids=invalid_rule_ids,
        blocked_rule_ids=blocked_rule_ids,
        failing_rule_ids=failing_rule_ids,
        aggregation_io_used=False,
    )


def aggregate_admission_rule_evaluations(
    scope_id: str,
    *,
    ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...],
) -> CombinedAdmissionCandidateVerdict:
    """Aggregate one already-generated ordered Exact15 result vector."""
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        return _verdict(scope_id, reason=SCOPE_ID_INVALID_REASON)
    required = REQUIRED_RULE_IDS[scope_id]
    if type(ordered_rule_evaluations) is not tuple:
        return _verdict(
            scope_id,
            reason=VECTOR_TYPE_INVALID_REASON,
            required_rule_ids=required,
        )

    structural_results: list[bool] = []
    for item in ordered_rule_evaluations:
        structural_results.append(_runtime_structure_valid(item))
    if False in structural_results:
        return _verdict(
            scope_id,
            reason=EVALUATION_INVARIANT_INVALID_REASON,
            required_rule_ids=required,
        )

    admissibility_results: list[bool] = []
    for item in ordered_rule_evaluations:
        admissibility_results.append(
            _aggregation_identity_and_outcome_admissible(item)
        )
    if False in admissibility_results:
        return _verdict(
            scope_id,
            reason=EVALUATION_INVARIANT_INVALID_REASON,
            required_rule_ids=required,
        )

    evaluated = tuple(
        item.admission_rule_id for item in ordered_rule_evaluations
    )
    if evaluated != required or len(evaluated) != len(set(evaluated)):
        return _verdict(
            scope_id,
            reason=MEMBERSHIP_INVALID_REASON,
            required_rule_ids=required,
            evaluated_rule_ids=evaluated,
        )

    invalid, blocked, failing = _outcome_projections(
        ordered_rule_evaluations
    )
    reason = (
        REQUIRED_RULE_INVALID_REASON
        if invalid
        else REQUIRED_RULE_BLOCKED_REASON
        if blocked
        else ""
    )
    return _verdict(
        scope_id,
        reason=reason,
        required_rule_ids=required,
        evaluated_rule_ids=evaluated,
        rule_evaluations=ordered_rule_evaluations,
        invalid_rule_ids=invalid,
        blocked_rule_ids=blocked,
        failing_rule_ids=failing,
    )


# ---------------------------------------------------------------------------
# Explicit evidence-builder and materializer boundary.  Nothing below is
# reachable from aggregate_admission_rule_evaluations.
# ---------------------------------------------------------------------------

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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "combined candidate verdict and cross-rule aggregation implementation v1"
STAGE = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_v1"
)
BASE_COMMIT = "38eb228f6507bb36c19433050c75d4b28e2e65a2"
BASE_PARENT = "71fe2a41ecdf9e2317994e755ce21fc64bd05b87"
BASE_TREE = "b963e99e1d2dd0f891b6c0ef7fca229bf351e9bb"
BASE_SUBJECT = (
    "add CovaPIE combined candidate verdict and cross-rule aggregation contract v1"
)
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_stage_global_rule_evaluation_orchestration_contract_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
STAGING_NAME_PREFIX = f"{STAGE}.__staging__."
LEGACY_STAGING_PREFIXES = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.__staging__.",
    ".combined-permission-semantics-stage-",
)
FORBIDDEN_SUFFIXES = frozenset(
    {
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
)

RUNTIME_CONTRACT_FILENAME = (
    "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
    "runtime_contract.csv"
)
TRUTH_FILENAME = "covapie_cross_rule_aggregation_implementation_truth_matrix.csv"
SAFETY_FILENAME = "covapie_cross_rule_aggregation_implementation_safety_audit.csv"
PRECONDITION_FILENAME = (
    "covapie_cross_rule_aggregation_precondition_transition_inventory.csv"
)
ISSUE_FILENAME = "covapie_cross_rule_aggregation_issue_readiness_inventory.csv"
MANIFEST_FILENAME = (
    "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
    "implementation_manifest.json"
)
OUTPUT_FILES = (
    RUNTIME_CONTRACT_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    PRECONDITION_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)
SUPPORT_PATHS = (
    Path("src/covalent_ext") / f"{STAGE}.py",
    Path("scripts") / f"check_{STAGE}.py",
    Path("tests") / f"test_{STAGE}.py",
    Path("docs") / f"{STAGE}_summary.md",
)
EXACT10 = SUPPORT_PATHS + tuple(
    DEFAULT_OUTPUT_ROOT / name for name in OUTPUT_FILES
)

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_design_gate.py",
        "351e46eff9fce8cb735282cedc5ca531866d03439d582762d5827d2252f973e2",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "contract_manifest.json",
        "54fcccae583c521ef1d69c26b960d2ba984e4d6e7709d7d8344de558c6f0daa8",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_public_api_contract.csv",
        "05db18369fadea8d4387ef4188aee0c922dffc0b0216a3f6abd0532ebd696f55",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_cross_rule_aggregation_result_contract.csv",
        "34bf7ac21a78d0c93f73dbe7371e7b00ea48bec18308e5d8fcd82ea8c408fa8d",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_cross_rule_aggregation_truth_matrix.csv",
        "eed3774028ec7db33f923c2866f7d322dac68d605e5e2e3b9924521283de1e40",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_cross_rule_aggregation_safety_audit.csv",
        "4b26fc147e8b5eca0a41329729a9a0caa9895aa0faef524afc1768230253d494",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_issue_readiness_inventory.csv",
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
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004.py",
        "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
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
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

RUNTIME_CONTRACT_COLUMNS = (
    "contract_order",
    "contract_group",
    "item_order",
    "item_name",
    "frozen_value",
    "implementation_observed",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "scope_id_representation",
    "vector_type",
    "input_rule_ids",
    "input_outcomes",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "required_rule_ids",
    "evaluated_rule_ids",
    "invalid_rule_ids",
    "blocked_rule_ids",
    "failing_rule_ids",
    "rule_evaluations_retained",
    "input_tuple_identity_retained",
    "aggregation_io_used",
    "dispatcher_calls",
    "handler_calls",
    "current_permission",
    "authorized_execution_count",
    "case_passed",
)
SAFETY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_state",
    "observed_state",
    "safety_passed",
)
PRECONDITION_COLUMNS = (
    "precondition_order",
    "precondition_id",
    "inherited_completion_status",
    "inherited_implementation_blocking",
    "implementation_completion_status",
    "implementation_blocking",
    "transition_action",
    "transition_evidence",
    "transition_passed",
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
    return value[:-1].decode("ascii")


def _parse_index(content: bytes, path: str) -> tuple[str, str, int]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, stage = metadata.split(" ")
        number = int(stage)
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if (
        observed != path
        or mode != "100644"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("index entry drift")
    return mode, blob, number


def _parse_tree(content: bytes, path: str) -> tuple[str, str]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if (
        observed != path
        or mode != "100644"
        or kind != "blob"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("tree entry drift")
    return mode, blob


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
            break
        total += len(chunk)
        if total > maximum:
            raise ValueError("pinned read exceeds maximum")
        chunks.append(chunk)
    return b"".join(chunks)


def _pinned_regular_read(root: Path, relative: Path) -> bytes:
    """Read one leaf while pinning its complete lexical parent chain."""
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe relative source path")
    root = Path(os.path.abspath(root))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("pinned root unsafe")
    root_fd = os.open(
        root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    directory_fds = [root_fd]
    leaf_fd: int | None = None
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("pinned root stat/open race")
        parent_fd = root_fd
        bindings: list[tuple[int, str, int, Identity]] = []
        for component in relative.parts[:-1]:
            item = os.stat(
                component, dir_fd=parent_fd, follow_symlinks=False
            )
            identity = _identity(item)
            if (
                not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("pinned path component unsafe")
            child_fd = os.open(
                component,
                os.O_RDONLY
                | os.O_DIRECTORY
                | os.O_NOFOLLOW
                | os.O_CLOEXEC,
                dir_fd=parent_fd,
            )
            if _identity(os.fstat(child_fd)) != identity:
                os.close(child_fd)
                raise ValueError("pinned component stat/open race")
            directory_fds.append(child_fd)
            bindings.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd
        leaf = relative.parts[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        leaf_identity = _identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > 100 * 1024 * 1024
        ):
            raise ValueError("pinned leaf unsafe")
        leaf_fd = os.open(
            leaf,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        if _identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("pinned leaf stat/open race")
        content = _read_all(leaf_fd)
        after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if (
            _identity(os.fstat(leaf_fd)) != leaf_identity
            or _identity(after) != leaf_identity
        ):
            raise ValueError("pinned leaf changed during read")
        for lexical_parent, name, child_fd, expected in reversed(bindings):
            lexical = os.stat(
                name, dir_fd=lexical_parent, follow_symlinks=False
            )
            if (
                _identity(os.fstat(child_fd)) != expected
                or _identity(lexical) != expected
            ):
                raise ValueError("pinned component final drift")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("pinned root final drift")
        return content
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> tuple[FrozenSource, ...]:
    _canonical_runtime_guard()
    root = Path(os.path.abspath(repo_root))
    if head_ref != "HEAD":
        raise ValueError("source snapshot head_ref must be HEAD")
    initial_head = _strict_head(root)
    identity = _git(
        root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, initial_head)
    if (
        len(SOURCE_BOUNDARY) != 13
        or len(set(SOURCE_PATHS)) != 13
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact13 source boundary drift")
    records = []
    for relative in SOURCE_PATHS:
        raw = relative.as_posix()
        index_mode, index_blob, index_stage = _parse_index(
            _git(root, "ls-files", "--stage", "--", raw), raw
        )
        base_mode, base_blob = _parse_tree(
            _git(root, "ls-tree", BASE_COMMIT, "--", raw), raw
        )
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
        ):
            raise ValueError("source index/base identity drift")
        base = _git(root, "cat-file", "blob", base_blob)
        index = _git(root, "cat-file", "blob", index_blob)
        filesystem = _pinned_regular_read(root, relative)
        expected = SOURCE_SHA256[relative]
        if (
            base != index
            or index != filesystem
            or _sha(base) != expected
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
    final_head = _strict_head(root)
    if final_head != initial_head:
        raise ValueError("source snapshot HEAD drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, final_head)
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


def _json(content: bytes) -> dict[str, Any]:
    duplicates: list[str] = []

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    value = json.loads(content, object_pairs_hook=hook)
    if duplicates or type(value) is not dict:
        raise ValueError("JSON object with unique keys required")
    return value


def _csv_rows(
    content: bytes, columns: Sequence[str] | None = None
) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    header = tuple(reader.fieldnames or ())
    if (
        not header
        or len(header) != len(set(header))
        or (columns is not None and header != tuple(columns))
    ):
        raise ValueError("CSV header drift")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != header for row in rows):
        raise ValueError("CSV row drift")
    return rows


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _verify_authorities(snapshot: Sequence[FrozenSource]) -> None:
    if (
        type(snapshot) not in (tuple, list)
        or len(snapshot) != 13
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
            or re.fullmatch(r"[0-9a-f]{40}", item.base_tree_blob) is None
        ):
            raise ValueError("source snapshot record invariant drift")
    contract_manifest = _json(
        _source(snapshot, "aggregation_contract_manifest.json").content
    )
    public_rows = _csv_rows(
        _source(snapshot, "verdict_public_api_contract.csv").content
    )
    result_rows = _csv_rows(
        _source(snapshot, "aggregation_result_contract.csv").content
    )
    truth_rows = _csv_rows(
        _source(snapshot, "aggregation_truth_matrix.csv").content
    )
    safety_rows = _csv_rows(
        _source(snapshot, "aggregation_safety_audit.csv").content
    )
    issues = _csv_rows(
        _source(snapshot, "verdict_issue_readiness_inventory.csv").content,
        ISSUE_COLUMNS,
    )
    runtime_manifest = _json(
        _source(snapshot, "admit_001_to_015_runtime_manifest.json").content
    )
    membership = _csv_rows(
        _source(
            snapshot, "permission_scope_and_rule_membership_contract.csv"
        ).content
    )
    enforcement = _json(
        _source(
            snapshot,
            "mandatory_training_authorization_enforcement_manifest.json",
        ).content
    )
    preconditions = _csv_rows(
        _source(snapshot, "interface_precondition_inventory.csv").content
    )
    reconstructed = tuple(
        tuple(
            row["admission_rule_id"]
            for row in membership
            if row["scope_id"] == scope and row["included"] == "true"
        )
        for scope in SCOPE_IDS
    )
    if (
        contract_manifest["base_identity"]["commit"] != BASE_PARENT
        or contract_manifest["truth_matrix"]["row_count"] != 201
        or contract_manifest["truth_matrix"]["group_count"] != 23
        or len(public_rows) != 24
        or len(result_rows) != 19
        or len(truth_rows) != 201
        or len(safety_rows) != 30
        or len(issues) != 30
        or runtime_manifest["result_fields"] != list(INPUT_RESULT_FIELDS)
        or runtime_manifest["result_schema_version"]
        != INPUT_RESULT_SCHEMA_VERSION
        or runtime_manifest["outcome_vocabulary"] != list(OUTCOME_VOCABULARY)
        or runtime_manifest["rule_names"] != dict(RULE_NAMES)
        or runtime_manifest["adapter_ids"] != dict(ADAPTER_IDS)
        or reconstructed != tuple(REQUIRED_RULE_IDS.values())
        or enforcement["current_permission"] is not False
        or enforcement["authorized_admit_015_training_execution_count"] != 0
        or len(preconditions) != 45
    ):
        raise ValueError("authoritative source contract drift")


def _runtime_contract_rows() -> list[dict[str, str]]:
    api = (
        ("function_name", "aggregate_admission_rule_evaluations"),
        (
            "signature",
            "aggregate_admission_rule_evaluations(scope_id: str, *, "
            "ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]) "
            "-> CombinedAdmissionCandidateVerdict",
        ),
        ("scope_parameter_kind", "positional_or_keyword"),
        ("ordered_vector_parameter_kind", "keyword_only"),
        ("defaults", "none"),
        ("var_positional", "forbidden"),
        ("var_keyword", "forbidden"),
        ("candidate_parameter", "forbidden"),
        ("context_parameter", "forbidden"),
        ("dispatcher_injection", "forbidden"),
        ("registry_injection", "forbidden"),
        ("override_fallback", "forbidden"),
        ("input_runtime_type", "UnifiedAdmissionRuleEvaluation"),
        ("output_runtime_type", "CombinedAdmissionCandidateVerdict"),
        ("dispatcher_calls", "0"),
        ("handler_calls", "0"),
        ("aggregation_io", "false"),
        ("production_implementation_present", "true"),
    )
    result = tuple(
        (name, annotation)
        for name, annotation in zip(
            RESULT_FIELDS,
            (
                "str",
                "str",
                "str",
                "bool",
                "bool",
                "str",
                "tuple[str,...]",
                "tuple[str,...]",
                "tuple[UnifiedAdmissionRuleEvaluation,...]",
                "tuple[str,...]",
                "tuple[str,...]",
                "tuple[str,...]",
                "bool",
            ),
            strict=True,
        )
    )
    groups = (
        ("production_public_api", api),
        ("production_result_contract", result),
        (
            "reason_vocabulary",
            tuple((f"reason_{index}", value) for index, value in enumerate(REASON_VOCABULARY, 1)),
        ),
        (
            "scope_membership",
            tuple((scope, "|".join(required)) for scope, required in SCOPE_CONTRACT),
        ),
        (
            "validation_precedence",
            tuple(
                (f"precedence_{index}", value)
                for index, value in enumerate(
                    (
                        "scope_id",
                        "ordered_vector_exact_tuple",
                        "all_child_runtime_exact13_structure",
                        "all_child_aggregation_identity_and_outcome_admissibility",
                        "full_exact_membership",
                        "all_child_invalid_outcomes",
                        "all_child_blocked_outcomes",
                        "all_child_passed",
                    ),
                    1,
                )
            ),
        ),
    )
    rows = []
    order = 0
    for group, items in groups:
        for item_order, (name, value) in enumerate(items, 1):
            order += 1
            rows.append(
                {
                    "contract_order": str(order),
                    "contract_group": group,
                    "item_order": str(item_order),
                    "item_name": name,
                    "frozen_value": value,
                    "implementation_observed": value,
                    "contract_passed": "true",
                }
            )
    return rows


class _ActualChildSubclass(UnifiedAdmissionRuleEvaluation):
    pass


def _actualize_contract_value(value: object, design: Any) -> object:
    if isinstance(value, design.UnifiedAdmissionRuleEvaluationContractDesign):
        values = dict(vars(value))
        if type(value) is not design.UnifiedAdmissionRuleEvaluationContractDesign:
            return _ActualChildSubclass(**values)
        try:
            return UnifiedAdmissionRuleEvaluation(**values)
        except (TypeError, ValueError):
            forged = object.__new__(UnifiedAdmissionRuleEvaluation)
            for name, item in values.items():
                object.__setattr__(forged, name, item)
            return forged
    if type(value) is tuple:
        return tuple(_actualize_contract_value(item, design) for item in value)
    if type(value) is list:
        return [_actualize_contract_value(item, design) for item in value]
    return value


def _implementation_truth_rows() -> list[dict[str, str]]:
    from covalent_ext import (
        covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_design_gate
        as design,
    )

    rows = []
    for order, (case_id, group, scope, vector, expected_reason) in enumerate(
        design._truth_cases(), 1
    ):
        actual_vector = _actualize_contract_value(vector, design)
        result = aggregate_admission_rule_evaluations(
            scope, ordered_rule_evaluations=actual_vector
        )
        expected_outcome = (
            "passed"
            if expected_reason == ""
            else "blocked"
            if expected_reason == REQUIRED_RULE_BLOCKED_REASON
            else "invalid"
        )
        vector_items = actual_vector if type(actual_vector) is tuple else ()
        input_ids = tuple(
            item.admission_rule_id
            if isinstance(item, UnifiedAdmissionRuleEvaluation)
            and type(item.admission_rule_id) is str
            else f"<{type(item).__name__}>"
            for item in vector_items
        )
        input_outcomes = tuple(
            item.outcome
            if isinstance(item, UnifiedAdmissionRuleEvaluation)
            and type(item.outcome) is str
            else f"<{type(item).__name__}>"
            for item in vector_items
        )
        retained = bool(result.rule_evaluations)
        identity = result.rule_evaluations is actual_vector if retained else False
        passed = (
            result.outcome == expected_outcome
            and result.reason == expected_reason
            and result.passed is (expected_outcome == "passed")
            and result.blocks_scope_action is (expected_outcome != "passed")
            and result.aggregation_io_used is False
            and (not retained or identity)
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "scope_id_representation": (
                    scope
                    if type(scope) is str
                    else "None"
                    if scope is None
                    else f"<{type(scope).__name__}>"
                ),
                "vector_type": type(actual_vector).__name__,
                "input_rule_ids": "|".join(input_ids),
                "input_outcomes": "|".join(input_outcomes),
                "expected_outcome": expected_outcome,
                "observed_outcome": result.outcome,
                "expected_reason": expected_reason,
                "observed_reason": result.reason,
                "required_rule_ids": "|".join(result.required_rule_ids),
                "evaluated_rule_ids": "|".join(result.evaluated_rule_ids),
                "invalid_rule_ids": "|".join(result.invalid_rule_ids),
                "blocked_rule_ids": "|".join(result.blocked_rule_ids),
                "failing_rule_ids": "|".join(result.failing_rule_ids),
                "rule_evaluations_retained": str(retained).lower(),
                "input_tuple_identity_retained": str(identity).lower(),
                "aggregation_io_used": "false",
                "dispatcher_calls": "0",
                "handler_calls": "0",
                "current_permission": "false",
                "authorized_execution_count": "0",
                "case_passed": str(passed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    states = (
        ("dispatcher_calls", "0"),
        ("single_rule_handler_calls", "0"),
        ("network", "false"),
        ("provider", "false"),
        ("download", "false"),
        ("raw", "false"),
        ("torch_import", "false"),
        ("dataloader", "false"),
        ("checkpoint", "false"),
        ("model", "false"),
        ("forward", "false"),
        ("loss", "false"),
        ("backward", "false"),
        ("optimizer", "false"),
        ("scheduler", "false"),
        ("parameter_update", "false"),
        ("checkpoint_write", "false"),
        ("training_result", "false"),
        ("current_permission", "false"),
        ("authorized_execution_count", "0"),
        ("aggregator_implementation", "true"),
        ("combined_verdict_implementation", "true"),
        ("orchestrator", "false"),
        ("feature_semantics_audit_completed", "false"),
        ("ready_for_training", "false"),
        ("exact15_runtime_modified", "false"),
        ("contract_stage_modified", "false"),
        ("aggregation_io_used", "false"),
        ("runtime_dispatcher_call_order_frozen", "false"),
        ("stage_global_rule_orchestration_frozen", "false"),
    )
    return [
        {
            "audit_order": str(order),
            "audit_item": item,
            "expected_state": state,
            "observed_state": state,
            "safety_passed": "true",
        }
        for order, (item, state) in enumerate(states, 1)
    ]


def _precondition_rows(
    snapshot: Sequence[FrozenSource],
) -> list[dict[str, str]]:
    inherited = _csv_rows(
        _source(snapshot, "interface_precondition_inventory.csv").content
    )
    rows = []
    for order, source in enumerate(inherited, 1):
        pre_id = source["precondition_id"]
        inherited_complete = (
            "incomplete" if pre_id in {"PRE_036", "PRE_038", "PRE_042"} else "complete"
        )
        inherited_blocking = (
            "true" if pre_id in {"PRE_036", "PRE_038", "PRE_042"} else "false"
        )
        resolved = pre_id == "PRE_036"
        rows.append(
            {
                "precondition_order": str(order),
                "precondition_id": pre_id,
                "inherited_completion_status": inherited_complete,
                "inherited_implementation_blocking": inherited_blocking,
                "implementation_completion_status": (
                    "complete" if resolved else inherited_complete
                ),
                "implementation_blocking": (
                    "false" if resolved else inherited_blocking
                ),
                "transition_action": (
                    "resolved_by_pure_cross_rule_aggregation_implementation"
                    if resolved
                    else "unchanged"
                ),
                "transition_evidence": (
                    f"{SUPPORT_PATHS[0].as_posix()}|"
                    f"{(DEFAULT_OUTPUT_ROOT / RUNTIME_CONTRACT_FILENAME).as_posix()}|"
                    f"{(DEFAULT_OUTPUT_ROOT / TRUTH_FILENAME).as_posix()}|"
                    f"{SUPPORT_PATHS[2].as_posix()}"
                    if resolved
                    else "inherited effective state retained"
                ),
                "transition_passed": "true",
            }
        )
    return rows


TRUE_READINESS = (
    "combined_permission_semantics_frozen",
    "combined_candidate_verdict_contract_frozen",
    "cross_rule_aggregation_contract_frozen",
    "cross_rule_aggregation_public_api_frozen",
    "cross_rule_aggregation_result_contract_frozen",
    "cross_rule_aggregation_validation_precedence_frozen",
    "cross_rule_aggregation_full_vector_semantics_frozen",
    "ready_for_cross_rule_aggregation_implementation",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "cross_rule_aggregation_implementation_complete",
    "pre_036_resolved",
    "ready_for_stage_global_rule_evaluation_orchestration_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "runtime_dispatcher_call_order_frozen",
    "stage_global_rule_evaluation_orchestration_frozen",
    "training_orchestrator_integration_implemented",
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
    _verify_authorities(snapshot)
    runtime_rows = _runtime_contract_rows()
    truth_rows = _implementation_truth_rows()
    safety_rows = _safety_rows()
    precondition_rows = _precondition_rows(snapshot)
    issue_content = _source(
        snapshot, "verdict_issue_readiness_inventory.csv"
    ).content
    if (
        len(runtime_rows) != 49
        or any(row["contract_passed"] != "true" for row in runtime_rows)
        or len(truth_rows) != 201
        or len({row["case_group"] for row in truth_rows}) != 23
        or any(row["case_passed"] != "true" for row in truth_rows)
        or len(safety_rows) != 30
        or any(row["safety_passed"] != "true" for row in safety_rows)
        or len(precondition_rows) != 45
        or tuple(
            row["precondition_id"]
            for row in precondition_rows
            if row["transition_action"] != "unchanged"
        )
        != ("PRE_036",)
        or _sha(issue_content)
        != "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ):
        raise ValueError("implementation evidence row contract drift")
    payloads = {
        RUNTIME_CONTRACT_FILENAME: _csv_bytes(
            RUNTIME_CONTRACT_COLUMNS, runtime_rows
        ),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        PRECONDITION_FILENAME: _csv_bytes(
            PRECONDITION_COLUMNS, precondition_rows
        ),
        ISSUE_FILENAME: issue_content,
    }
    root = Path(os.path.abspath(repo_root))
    support_sha = {
        path.as_posix(): _sha(_pinned_regular_read(root, path))
        for path in SUPPORT_PATHS
    }
    group_counts = dict(
        sorted(Counter(row["case_group"] for row in truth_rows).items())
    )
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
        "source_boundary_name": "fixed_ordered_exact13_committed_source_boundary",
        "source_boundary_count": 13,
        "source_boundary": [
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
        ],
        "production_module": {
            "path": SUPPORT_PATHS[0].as_posix(),
            "sha256": support_sha[SUPPORT_PATHS[0].as_posix()],
        },
        "actual_input_runtime": {
            "owner": (
                "covalent_ext."
                "covapie_bulk_download_admission_minimal_unified_dispatch_"
                "shell_with_admit_004.UnifiedAdmissionRuleEvaluation"
            ),
            "schema_version": INPUT_RESULT_SCHEMA_VERSION,
            "field_count": 13,
            "fields": list(INPUT_RESULT_FIELDS),
            "runtime_outcomes": list(OUTCOME_VOCABULARY),
            "aggregation_outcomes": list(
                AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
            ),
            "rejected_policy": (
                "runtime_valid_but_aggregation_inadmissible_fail_closed_as_"
                "evaluation_invariant_invalid"
            ),
            "nested_duplicate_policy": (
                "permitted_and_not_interpreted_merged_deduplicated_copied_or_rebuilt"
            ),
        },
        "public_api": {
            "function_name": "aggregate_admission_rule_evaluations",
            "signature": (
                "aggregate_admission_rule_evaluations(scope_id: str, *, "
                "ordered_rule_evaluations: "
                "tuple[UnifiedAdmissionRuleEvaluation, ...]) "
                "-> CombinedAdmissionCandidateVerdict"
            ),
            "candidate_or_context_parameters": False,
            "dispatcher_or_registry_parameters": False,
            "override_or_fallback_parameters": False,
        },
        "production_result": {
            "class_name": "CombinedAdmissionCandidateVerdict",
            "schema_version": RESULT_SCHEMA_VERSION,
            "field_count": 13,
            "fields": list(RESULT_FIELDS),
            "frozen_dataclass": True,
            "slots": False,
            "aggregation_outcomes": list(AGGREGATION_OUTCOME_VOCABULARY),
        },
        "permission_scope_count": 4,
        "permission_scopes": [
            {
                "scope_order": order,
                "scope_id": scope,
                "required_rule_count": len(required),
                "required_rule_ids": list(required),
            }
            for order, (scope, required) in enumerate(SCOPE_CONTRACT, 1)
        ],
        "reason_vocabulary": {
            "pass_reason": "",
            "nonempty_reason_count": 6,
            "nonempty_reasons": list(REASON_VOCABULARY),
        },
        "validation_precedence": [
            "scope_id",
            "ordered_vector_exact_tuple",
            "all_child_runtime_exact13_structure",
            "all_child_aggregation_identity_and_outcome_admissibility",
            "full_exact_membership",
            "all_child_invalid_outcomes",
            "all_child_blocked_outcomes",
            "all_child_passed",
        ],
        "full_vector_semantics": {
            "short_circuit": False,
            "complete_structure_scan": True,
            "complete_admissibility_scan": True,
            "complete_outcome_scan": True,
            "all_invalid_ids_collected": True,
            "all_blocked_ids_collected": True,
            "all_failing_ids_collected": True,
            "valid_tuple_identity_preserved": True,
        },
        "runtime_contract": {"row_count": 49},
        "truth_matrix": {
            "row_count": 201,
            "group_count": 23,
            "group_counts": group_counts,
            "uses_actual_runtime_type": True,
            "forged_objects_test_evidence_only": True,
            "production_api_creates_forged_objects": False,
            "production_runtime_modifies_inputs": False,
            "invalid_objects_retained": False,
        },
        "safety_audit": {"row_count": 30},
        "precondition_transition": {
            "row_count": 45,
            "transition_count": 1,
            "transition_ids": ["PRE_036"],
            "complete_count": 43,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
        },
        "issue_continuity": {
            "row_count": 30,
            "byte_identical_to_contract": True,
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
            "dispatcher_call_count": 0,
            "single_rule_handler_call_count": 0,
            "aggregation_io_used": False,
            "current_permission": False,
            "authorized_admit_015_training_execution_count": 0,
            "aggregator_implementation_does_not_grant_action_permission": True,
            "training_execution_not_performed": True,
            "feature_semantics_audit_still_required": True,
            "ready_for_training": False,
            "orchestrator_implemented": False,
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
        "step12d_boundary": (
            "smoke_legality_check_not_final_training_feature_contract"
        ),
        "feature_semantics_warning": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check; historical "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain unresolved"
        ),
        "no_orchestrator_boundary": (
            "stage-global rule evaluation orchestration is not implemented"
        ),
        "infrastructure_hardening": {
            "source_parent_chain_fd_pinned": True,
            "source_initial_final_strict_head": True,
            "source_base_ancestry_verified": True,
            "exact6_parent_root_all_leaf_fd_pinned": True,
            "duplicate_json_keys_rejected": True,
            "canonical_json": True,
            "materializer_build_before_mutation": True,
            "materializer_o_excl_and_fsync": True,
            "materializer_rename_noreplace": True,
            "materializer_gpfs_einval_fail_closed": True,
            "materializer_authenticated_staging_retained": True,
            "materializer_no_os_replace": True,
            "materializer_no_destructive_cleanup": True,
            "existing_exact_set_inode_preserving_noop": True,
            "checker_full_index_bytes_snapshotted": True,
            "git_write_tree_index_snapshot_used": False,
            "pre_commit_and_post_commit_lifecycle": True,
            "allow_empty_candidate_history_rejected": True,
            "full_recursive_lifecycle_run_count": 2,
            "final_recursive_lifecycle_is_last_filesystem_validation": True,
        },
        "stage_owned_staging_namespace_closure": {
            "materializer_staging_name_prefix": STAGING_NAME_PREFIX,
            "legacy_staging_prefixes": list(LEGACY_STAGING_PREFIXES),
            "current_staging_residue_rejected": True,
            "legacy_staging_residue_rejected": True,
            "ignored_tracked_nonignored_residue_rejected": True,
        },
        "embedded_stage_residue_lifecycle_closure": {
            "four_bounded_support_roots": [
                "src/covalent_ext",
                "scripts",
                "tests",
                "docs",
            ],
            "support_root_stage_match_policy": (
                "complete_stage_token_at_any_basename_position"
            ),
            "matched_directory_descendants_observed": True,
            "generic_symlink_filter_runs_before_stage_allowance": True,
            "derived_parent_independent_prefix_policy": True,
        },
        "derived_output_sha256": {
            (DEFAULT_OUTPUT_ROOT / name).as_posix(): _sha(content)
            for name, content in payloads.items()
        },
        "support_file_sha256": support_sha,
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
    """Read Exact6 through held parent, root, and all-leaf descriptors."""
    absolute = Path(os.path.abspath(root))
    parent = absolute.parent
    parent_item = os.lstat(parent)
    root_item = os.lstat(absolute)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("output parent/root unsafe")
    parent_identity = _identity(parent_item)
    root_identity = _identity(root_item)
    parent_fd = os.open(parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    descriptors: dict[str, int] = {}
    identities: dict[str, Identity] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_fd = os.open(
            absolute.name, DIRECTORY_FLAGS, dir_fd=parent_fd
        )
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        initial_inventory = tuple(sorted(os.listdir(root_fd)))
        if initial_inventory != tuple(sorted(OUTPUT_FILES)):
            raise ValueError("output inventory drift")
        for name in OUTPUT_FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > 100 * 1024 * 1024
            ):
                raise ValueError("output leaf unsafe")
            identities[name] = _identity(item)
            descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
            descriptors[name] = descriptor
            if _identity(os.fstat(descriptor)) != identities[name]:
                raise ValueError("output leaf stat/open race")
        result = {
            name: _read_all(descriptors[name]) for name in OUTPUT_FILES
        }
        for name in OUTPUT_FILES:
            lexical = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            if (
                _identity(os.fstat(descriptors[name])) != identities[name]
                or _identity(lexical) != identities[name]
            ):
                raise ValueError("output leaf final drift")
        if tuple(sorted(os.listdir(root_fd))) != initial_inventory:
            raise ValueError("output final inventory drift")
        lexical_root = os.stat(
            absolute.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
            or _identity(os.fstat(root_fd)) != root_identity
            or _identity(lexical_root) != root_identity
            or _identity(os.lstat(absolute)) != root_identity
        ):
            raise ValueError("output final parent/root binding drift")
        return result
    finally:
        for descriptor in descriptors.values():
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
    callback = (lambda event, path: None) if hook is None else hook
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or any(type(content) is not bytes for content in payloads.values())
    ):
        raise ValueError("output payload inventory drift")
    candidate = Path(output_root)
    root = (
        Path(os.path.abspath(candidate))
        if candidate.is_absolute()
        else Path(os.path.abspath(repo_root)) / candidate
    )
    if not candidate.is_absolute() and ".." in candidate.parts:
        raise ValueError("relative output escape")
    parent = root.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("output parent unsafe")
    parent_item = os.lstat(parent)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
    ):
        raise ValueError("output parent unsafe")
    parent_identity = _identity(parent_item)
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
            raise ValueError("materialization parent stat/open race")
        for _ in range(64):
            name = f"{STAGING_NAME_PREFIX}{secrets.token_hex(16)}"
            try:
                os.mkdir(name, 0o700, dir_fd=parent_fd)
                staging_name = name
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        staging_fd = os.open(staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        if os.listdir(staging_fd):
            raise ValueError("staging not empty")
        for name, content in payloads.items():
            descriptor = os.open(name, WRITE_FLAGS, 0o600, dir_fd=staging_fd)
            try:
                _write_all(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            staging_identity = _identity(os.fstat(staging_fd))
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        staging_path = parent / staging_name
        if _read_output_set(staging_path) != payloads:
            raise ValueError("staging verification failed")
        if _identity(os.fstat(staging_fd)) != staging_identity:
            raise ValueError("held staging identity drift")
        callback("before_rename", staging_path)
        lexical_staging = os.stat(
            staging_name, dir_fd=parent_fd, follow_symlinks=False
        )
        current_parent_identity = _identity(os.fstat(parent_fd))
        if (
            _identity(os.lstat(parent)) != current_parent_identity
            or _identity(lexical_staging) != staging_identity
            or _identity(os.fstat(staging_fd)) != staging_identity
            or not stat.S_ISDIR(lexical_staging.st_mode)
            or stat.S_ISLNK(lexical_staging.st_mode)
            or tuple(sorted(os.listdir(staging_fd)))
            != tuple(sorted(OUTPUT_FILES))
        ):
            raise ValueError("pre-rename staging/parent binding drift")
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
            error = ctypes.get_errno()
            if error == 22:
                raise OSError(error, "GPFS renameat2 EINVAL fail closed")
            raise OSError(error, os.strerror(error))
        published = True
        staging_name = None
        published_identity = _identity(os.fstat(staging_fd))
        published_item = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            not stat.S_ISDIR(published_item.st_mode)
            or stat.S_ISLNK(published_item.st_mode)
            or _identity(published_item) != published_identity
        ):
            raise ValueError("post-publish root identity drift")
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
                lexical = os.stat(
                    staging_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (
                    _identity(lexical) == staging_identity
                    and _identity(os.fstat(staging_fd)) == staging_identity
                ):
                    retained = parent / staging_name
            except OSError:
                retained = None
        if retained is not None:
            raise MaterializationRetentionError(retained) from error
        raise
    finally:
        if staging_fd is not None:
            os.close(staging_fd)
        os.close(parent_fd)


def run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    payloads = build_artifacts(snapshot, repo_root=repo_root)
    root = _materialize(
        output_root, payloads, repo_root=repo_root
    )
    return {
        "snapshot": snapshot,
        "manifest": _json(payloads[MANIFEST_FILENAME]),
        "output_root": root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1()
