"""Pure in-memory design contract for a future action-permission bridge.

The classifier establishes eligibility for a future permission-state
transition.  It never grants that permission and never invokes an action.
"""

from __future__ import annotations

from dataclasses import dataclass

from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as call_site_contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext.covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1 import (
    CombinedAdmissionCandidateVerdict,
)
from covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 import (
    UnifiedAdmissionRuleEvaluation,
)


BASE_COMMIT = "f24bc241b1a492a514ed44649d57220a68c3ae6d"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration action-permission bridge contract v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_v1"
)
DOWNLOAD_SCOPE_ID = call_site_contract.DOWNLOAD_SCOPE_ID
DECISION_SCHEMA_VERSION = (
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_decision_v1"
)
DECISION_FIELDS = (
    "schema_version",
    "outcome",
    "passed",
    "blocks_transition",
    "reason",
    "source_scope_id",
    "candidate_count",
    "admit_014_outcome",
    "candidate_combined_outcomes",
    "call_site_decision_outcome",
    "call_site_decision_reason",
    "invalid_candidate_indexes",
    "blocked_candidate_indexes",
    "failing_candidate_indexes",
    "source_lineage_verified",
    "transition_eligible",
    "action_permission_granted",
    "download_action_invoked",
    "bridge_io_used",
)
OUTCOME_VOCABULARY = ("eligible", "blocked", "invalid")
REASON_VOCABULARY = (
    "ACTION_PERMISSION_BRIDGE_RESULT_TYPE_INVALID",
    "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_TYPE_INVALID",
    "ACTION_PERMISSION_BRIDGE_STAGE_RESULT_INVARIANT_INVALID",
    "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_INVARIANT_INVALID",
    "ACTION_PERMISSION_BRIDGE_STAGE_SCOPE_INVALID",
    "ACTION_PERMISSION_BRIDGE_STAGE_IO_INVARIANT_INVALID",
    "ACTION_PERMISSION_BRIDGE_SOURCE_ALREADY_TRANSITIONED",
    "ACTION_PERMISSION_BRIDGE_SOURCE_LINEAGE_MISMATCH",
    "ACTION_PERMISSION_BRIDGE_CANDIDATE_VERDICT_INVALID",
    "ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED",
    "ACTION_PERMISSION_BRIDGE_CANDIDATE_VERDICT_BLOCKED",
    "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_NOT_PERMISSION_PENDING",
    "ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE",
)
PERMISSION_PENDING_OUTCOME = "blocked"
PERMISSION_PENDING_REASON = "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"
CALL_SITE_DECISION_NOT_PERMISSION_PENDING_REASON_RESERVED = True
CALL_SITE_DECISION_NOT_PERMISSION_PENDING_BRANCH_REACHABLE = False


@dataclass(frozen=True)
class BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign:
    schema_version: str
    outcome: str
    passed: bool
    blocks_transition: bool
    reason: str
    source_scope_id: str
    candidate_count: int
    admit_014_outcome: str
    candidate_combined_outcomes: tuple[str, ...]
    call_site_decision_outcome: str
    call_site_decision_reason: str
    invalid_candidate_indexes: tuple[int, ...]
    blocked_candidate_indexes: tuple[int, ...]
    failing_candidate_indexes: tuple[int, ...]
    source_lineage_verified: bool
    transition_eligible: bool
    action_permission_granted: bool
    download_action_invoked: bool
    bridge_io_used: bool

    def __post_init__(self) -> None:
        stored = vars(self)
        if (
            type(stored) is not dict
            or tuple(stored) != DECISION_FIELDS
            or tuple(self.__dataclass_fields__) != DECISION_FIELDS
        ):
            raise TypeError("bridge decision Exact19 storage/order invalid")
        string_fields = (
            "schema_version",
            "outcome",
            "reason",
            "source_scope_id",
            "admit_014_outcome",
            "call_site_decision_outcome",
            "call_site_decision_reason",
        )
        bool_fields = (
            "passed",
            "blocks_transition",
            "source_lineage_verified",
            "transition_eligible",
            "action_permission_granted",
            "download_action_invoked",
            "bridge_io_used",
        )
        if any(type(stored[name]) is not str for name in string_fields):
            raise TypeError("bridge decision string field type invalid")
        if any(type(stored[name]) is not bool for name in bool_fields):
            raise TypeError("bridge decision bool field type invalid")
        if type(self.candidate_count) is not int or self.candidate_count < 0:
            raise ValueError("bridge decision candidate count invalid")
        if (
            type(self.candidate_combined_outcomes) is not tuple
            or any(
                type(item) is not str
                for item in self.candidate_combined_outcomes
            )
        ):
            raise TypeError("bridge decision candidate outcomes invalid")
        for name in (
            "invalid_candidate_indexes",
            "blocked_candidate_indexes",
            "failing_candidate_indexes",
        ):
            indexes = stored[name]
            if (
                type(indexes) is not tuple
                or any(type(index) is not int for index in indexes)
                or indexes != tuple(sorted(set(indexes)))
                or any(
                    index < 0 or index >= self.candidate_count
                    for index in indexes
                )
            ):
                raise ValueError("bridge decision diagnostic indexes invalid")
        expected_failing = tuple(
            index
            for index in range(self.candidate_count)
            if (
                index in self.invalid_candidate_indexes
                or index in self.blocked_candidate_indexes
            )
        )
        if self.failing_candidate_indexes != expected_failing:
            raise ValueError("bridge decision failing projection invalid")
        if (
            self.schema_version != DECISION_SCHEMA_VERSION
            or self.outcome not in OUTCOME_VOCABULARY
            or self.reason not in REASON_VOCABULARY
            or self.passed is not (self.outcome == "eligible")
            or self.blocks_transition is not (self.outcome != "eligible")
            or self.transition_eligible is not (self.outcome == "eligible")
            or self.action_permission_granted is not False
            or self.download_action_invoked is not False
            or self.bridge_io_used is not False
            or (
                self.outcome == "eligible"
                and self.reason != REASON_VOCABULARY[12]
            )
        ):
            raise ValueError("bridge decision invariant invalid")


def _decision(
    outcome: str,
    reason: str,
    *,
    source_scope_id: str = "",
    candidate_count: int = 0,
    admit_014_outcome: str = "",
    candidate_combined_outcomes: tuple[str, ...] = (),
    call_site_decision_outcome: str = "",
    call_site_decision_reason: str = "",
    invalid_candidate_indexes: tuple[int, ...] = (),
    blocked_candidate_indexes: tuple[int, ...] = (),
    source_lineage_verified: bool = False,
) -> BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign:
    failing = tuple(
        index
        for index in range(candidate_count)
        if (
            index in invalid_candidate_indexes
            or index in blocked_candidate_indexes
        )
    )
    return BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign(
        schema_version=DECISION_SCHEMA_VERSION,
        outcome=outcome,
        passed=outcome == "eligible",
        blocks_transition=outcome != "eligible",
        reason=reason,
        source_scope_id=source_scope_id,
        candidate_count=candidate_count,
        admit_014_outcome=admit_014_outcome,
        candidate_combined_outcomes=candidate_combined_outcomes,
        call_site_decision_outcome=call_site_decision_outcome,
        call_site_decision_reason=call_site_decision_reason,
        invalid_candidate_indexes=invalid_candidate_indexes,
        blocked_candidate_indexes=blocked_candidate_indexes,
        failing_candidate_indexes=failing,
        source_lineage_verified=source_lineage_verified,
        transition_eligible=outcome == "eligible",
        action_permission_granted=False,
        download_action_invoked=False,
        bridge_io_used=False,
    )


def _candidate_result_invariant_valid(
    value: object,
    *,
    candidate_index: int,
    scope_id: str,
    candidate_rule_count: int,
    required_rule_ids: tuple[str, ...],
    stage_positions: tuple[
        tuple[int, UnifiedAdmissionRuleEvaluation], ...
    ],
) -> bool:
    if type(value) is not contract.CandidateAdmissionOrchestrationResult:
        return False
    try:
        stored = vars(value)
        if (
            type(stored) is not dict
            or tuple(stored) != contract.CANDIDATE_RESULT_FIELDS
            or tuple(value.__dataclass_fields__)
            != contract.CANDIDATE_RESULT_FIELDS
            or type(value.candidate_index) is not int
            or value.candidate_index != candidate_index
            or type(value.ordered_rule_evaluations) is not tuple
            or type(value.combined_verdict)
            is not CombinedAdmissionCandidateVerdict
            or type(value.dispatcher_call_count) is not int
            or value.dispatcher_call_count != candidate_rule_count
            or type(value.aggregator_call_count) is not int
            or value.aggregator_call_count != 1
            or len(value.ordered_rule_evaluations)
            != len(required_rule_ids)
            or type(value)(**stored) != value
        ):
            return False
        if tuple(
            item.admission_rule_id
            for item in value.ordered_rule_evaluations
        ) != required_rule_ids:
            return False
        if any(
            value.ordered_rule_evaluations[position] is not stage_result
            for position, stage_result in stage_positions
        ):
            return False
        for rule_result, rule_id in zip(
            value.ordered_rule_evaluations,
            required_rule_ids,
            strict=True,
        ):
            contract.validate_unified_rule_evaluation_design(
                rule_result,
                expected_rule_id=rule_id,
                scope_id=scope_id,
                candidate_index=candidate_index,
                dispatcher_call_count=value.dispatcher_call_count,
                aggregator_call_count=value.aggregator_call_count,
            )
        contract.validate_combined_candidate_verdict_design(
            value.combined_verdict,
            expected_scope_id=scope_id,
            ordered_rule_evaluations=value.ordered_rule_evaluations,
            candidate_index=candidate_index,
            dispatcher_call_count=value.dispatcher_call_count,
            aggregator_call_count=value.aggregator_call_count,
        )
        return True
    except (
        AttributeError,
        TypeError,
        ValueError,
        contract.StageAdmissionOrchestrationError,
    ):
        return False


def _stage_result_invariant_valid(value: object) -> bool:
    if type(value) is not contract.StageAdmissionOrchestrationResult:
        return False
    try:
        stored = vars(value)
        if (
            type(stored) is not dict
            or tuple(stored) != contract.STAGE_RESULT_FIELDS
            or tuple(value.__dataclass_fields__) != contract.STAGE_RESULT_FIELDS
        ):
            return False
        if any(
            type(stored[name]) is not str
            for name in ("schema_version", "scope_id")
        ):
            return False
        if any(
            type(stored[name]) is not int
            for name in (
                "candidate_count",
                "dispatcher_call_count",
                "aggregator_call_count",
            )
        ):
            return False
        if any(
            type(stored[name]) is not bool
            for name in (
                "orchestration_io_used",
                "action_permission_granted",
            )
        ):
            return False
        tuple_fields = (
            "required_rule_ids",
            "stage_global_rule_ids",
            "candidate_rule_ids",
            "stage_global_rule_evaluations",
            "candidate_results",
        )
        if any(type(stored[name]) is not tuple for name in tuple_fields):
            return False
        if (
            value.schema_version != contract.STAGE_RESULT_SCHEMA_VERSION
            or value.scope_id not in contract.SCOPE_IDS
            or value.candidate_count <= 0
            or value.required_rule_ids
            != contract.REQUIRED_RULE_IDS[value.scope_id]
            or value.stage_global_rule_ids
            != contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[value.scope_id]
            or value.candidate_rule_ids
            != contract.CANDIDATE_RULE_IDS_BY_SCOPE[value.scope_id]
            or len(value.stage_global_rule_evaluations)
            != len(value.stage_global_rule_ids)
            or len(value.candidate_results) != value.candidate_count
            or value.dispatcher_call_count
            != (
                len(value.stage_global_rule_ids)
                + value.candidate_count * len(value.candidate_rule_ids)
            )
            or value.aggregator_call_count != value.candidate_count
            or type(value)(**stored) != value
        ):
            return False
        stage_positions = tuple(
            (
                value.required_rule_ids.index(rule_id),
                rule_result,
            )
            for rule_id, rule_result in zip(
                value.stage_global_rule_ids,
                value.stage_global_rule_evaluations,
                strict=True,
            )
        )
        for rule_result, rule_id in zip(
            value.stage_global_rule_evaluations,
            value.stage_global_rule_ids,
            strict=True,
        ):
            contract.validate_unified_rule_evaluation_design(
                rule_result,
                expected_rule_id=rule_id,
                scope_id=value.scope_id,
                candidate_index=-1,
                dispatcher_call_count=value.dispatcher_call_count,
                aggregator_call_count=value.aggregator_call_count,
            )
        return all(
            _candidate_result_invariant_valid(
                candidate,
                candidate_index=index,
                scope_id=value.scope_id,
                candidate_rule_count=len(value.candidate_rule_ids),
                required_rule_ids=value.required_rule_ids,
                stage_positions=stage_positions,
            )
            for index, candidate in enumerate(value.candidate_results)
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        contract.StageAdmissionOrchestrationError,
    ):
        return False


def _call_site_decision_invariant_valid(value: object) -> bool:
    if (
        type(value)
        is not call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
    ):
        return False
    try:
        stored = vars(value)
        if (
            type(stored) is not dict
            or tuple(stored) != call_site_contract.DECISION_FIELDS
            or tuple(value.__dataclass_fields__)
            != call_site_contract.DECISION_FIELDS
        ):
            return False
        if any(
            type(stored[name]) is not str
            for name in (
                "schema_version",
                "outcome",
                "reason",
                "source_kind",
                "source_scope_id",
                "source_error_code",
            )
        ):
            return False
        if any(
            type(stored[name]) is not bool
            for name in (
                "passed",
                "blocks_download",
                "action_permission_granted",
                "download_action_invoked",
                "call_site_io_used",
            )
        ):
            return False
        if (
            type(value.candidate_count) is not int
            or value.candidate_count < 0
            or value.schema_version != call_site_contract.DECISION_SCHEMA_VERSION
            or value.outcome not in call_site_contract.OUTCOME_VOCABULARY
            or value.source_kind != "orchestration_result"
            or value.source_scope_id not in contract.SCOPE_IDS
            or value.passed is not (value.outcome == "authorized")
            or value.blocks_download is not (value.outcome != "authorized")
            or value.download_action_invoked is not False
            or value.call_site_io_used is not False
            or (
                value.outcome == "authorized"
                and value.reason != ""
            )
            or (
                value.outcome != "authorized"
                and value.reason not in call_site_contract.REASON_VOCABULARY
            )
        ):
            return False
        for name in (
            "invalid_candidate_indexes",
            "blocked_candidate_indexes",
            "failing_candidate_indexes",
        ):
            indexes = stored[name]
            if (
                type(indexes) is not tuple
                or any(type(index) is not int for index in indexes)
                or indexes != tuple(sorted(set(indexes)))
                or any(
                    index < 0 or index >= value.candidate_count
                    for index in indexes
                )
            ):
                return False
        expected_failing = tuple(
            index
            for index in range(value.candidate_count)
            if (
                index in value.invalid_candidate_indexes
                or index in value.blocked_candidate_indexes
            )
        )
        return (
            value.failing_candidate_indexes == expected_failing
            and type(value)(**stored) == value
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _source_projection(
    result: contract.StageAdmissionOrchestrationResult,
) -> tuple[
    tuple[str, ...],
    tuple[int, ...],
    tuple[int, ...],
    tuple[int, ...],
    str,
    str,
    bool,
    bool,
]:
    outcomes = tuple(
        candidate.combined_verdict.outcome
        for candidate in result.candidate_results
    )
    invalid = tuple(
        candidate.candidate_index
        for candidate in result.candidate_results
        if candidate.combined_verdict.outcome == "invalid"
    )
    blocked = tuple(
        candidate.candidate_index
        for candidate in result.candidate_results
        if candidate.combined_verdict.outcome == "blocked"
    )
    failing = tuple(
        index
        for index in range(result.candidate_count)
        if index in invalid or index in blocked
    )
    if invalid:
        outcome = "invalid"
        reason = "BULK_DOWNLOAD_CANDIDATE_VERDICT_INVALID"
    elif blocked:
        outcome = "blocked"
        reason = "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"
    elif result.action_permission_granted:
        outcome = "authorized"
        reason = ""
    else:
        outcome = "blocked"
        reason = PERMISSION_PENDING_REASON
    return (
        outcomes,
        invalid,
        blocked,
        failing,
        outcome,
        reason,
        outcome == "authorized",
        outcome != "authorized",
    )


def _lineage_matches(
    result: contract.StageAdmissionOrchestrationResult,
    decision: call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign,
    projection: tuple[
        tuple[str, ...],
        tuple[int, ...],
        tuple[int, ...],
        tuple[int, ...],
        str,
        str,
        bool,
        bool,
    ],
) -> bool:
    (
        _,
        invalid,
        blocked,
        failing,
        expected_outcome,
        expected_reason,
        expected_passed,
        expected_blocks,
    ) = projection
    return (
        decision.source_kind == "orchestration_result"
        and decision.source_scope_id == result.scope_id
        and decision.source_error_code == ""
        and decision.candidate_count == result.candidate_count
        and decision.invalid_candidate_indexes == invalid
        and decision.blocked_candidate_indexes == blocked
        and decision.failing_candidate_indexes == failing
        and decision.action_permission_granted is result.action_permission_granted
        and decision.download_action_invoked is False
        and decision.call_site_io_used is False
        and decision.outcome == expected_outcome
        and decision.reason == expected_reason
        and decision.passed is expected_passed
        and decision.blocks_download is expected_blocks
    )


def classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design(
    *,
    orchestration_result: contract.StageAdmissionOrchestrationResult,
    call_site_decision: call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign,
) -> BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign:
    """Classify eligibility for a future transition without granting it."""
    if type(orchestration_result) is not contract.StageAdmissionOrchestrationResult:
        return _decision("invalid", REASON_VOCABULARY[0])
    if (
        type(call_site_decision)
        is not call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
    ):
        return _decision("invalid", REASON_VOCABULARY[1])
    if not _stage_result_invariant_valid(orchestration_result):
        return _decision("invalid", REASON_VOCABULARY[2])
    if not _call_site_decision_invariant_valid(call_site_decision):
        return _decision("invalid", REASON_VOCABULARY[3])

    result = orchestration_result
    projection = _source_projection(result)
    outcomes, invalid, blocked, failing = projection[:4]
    stage_outcomes = {
        item.admission_rule_id: item.outcome
        for item in result.stage_global_rule_evaluations
    }
    admit_014_outcome = stage_outcomes["ADMIT_014"]
    evidence = {
        "source_scope_id": result.scope_id,
        "candidate_count": result.candidate_count,
        "admit_014_outcome": admit_014_outcome,
        "candidate_combined_outcomes": outcomes,
        "call_site_decision_outcome": call_site_decision.outcome,
        "call_site_decision_reason": call_site_decision.reason,
        "invalid_candidate_indexes": invalid,
        "blocked_candidate_indexes": blocked,
    }
    empty_evidence = {
        "source_scope_id": result.scope_id,
        "candidate_count": result.candidate_count,
        "admit_014_outcome": admit_014_outcome,
        "candidate_combined_outcomes": outcomes,
        "call_site_decision_outcome": call_site_decision.outcome,
        "call_site_decision_reason": call_site_decision.reason,
    }

    if result.scope_id != DOWNLOAD_SCOPE_ID:
        return _decision("invalid", REASON_VOCABULARY[4], **empty_evidence)
    if result.orchestration_io_used is not False:
        return _decision("invalid", REASON_VOCABULARY[5], **empty_evidence)
    if result.action_permission_granted is True:
        return _decision("invalid", REASON_VOCABULARY[6], **empty_evidence)
    if not _lineage_matches(result, call_site_decision, projection):
        return _decision("invalid", REASON_VOCABULARY[7], **evidence)

    evidence["source_lineage_verified"] = True
    if invalid:
        return _decision("invalid", REASON_VOCABULARY[8], **evidence)
    if admit_014_outcome != "passed":
        return _decision("blocked", REASON_VOCABULARY[9], **evidence)
    if blocked or any(outcome != "passed" for outcome in outcomes):
        return _decision("blocked", REASON_VOCABULARY[10], **evidence)
    return _decision("eligible", REASON_VOCABULARY[12], **evidence)
