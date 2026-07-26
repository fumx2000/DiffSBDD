"""Pure fail-closed design classifier for a future bulk-download call site.

The orchestration output consumed here is diagnostic evidence, not execution
authorization.  This module performs only deterministic in-memory validation
and classification.  It deliberately exposes no download action and does not
implement ``evaluate_bulk_download_stage_orchestration_call_site``.
"""

from __future__ import annotations

from dataclasses import dataclass

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


BASE_COMMIT = "0963f4dbbd4d16eab8aaac1640d224ec135673ed"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration fail-closed call-site contract v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_decision_v1"
)
DOWNLOAD_SCOPE_ID = "download_execution_permission"
DECISION_SCHEMA_VERSION = (
    "covapie_bulk_download_stage_orchestration_call_site_decision_v1"
)
DECISION_FIELDS = (
    "schema_version",
    "outcome",
    "passed",
    "blocks_download",
    "reason",
    "source_kind",
    "source_scope_id",
    "source_error_code",
    "candidate_count",
    "invalid_candidate_indexes",
    "blocked_candidate_indexes",
    "failing_candidate_indexes",
    "action_permission_granted",
    "download_action_invoked",
    "call_site_io_used",
)
OUTCOME_VOCABULARY = ("authorized", "blocked", "invalid")
SOURCE_KIND_VOCABULARY = (
    "invalid_input",
    "orchestration_error",
    "orchestration_result",
)
REASON_VOCABULARY = (
    "BULK_DOWNLOAD_CALL_SITE_INPUT_CARDINALITY_INVALID",
    "BULK_DOWNLOAD_CALL_SITE_RESULT_TYPE_INVALID",
    "BULK_DOWNLOAD_CALL_SITE_ERROR_TYPE_INVALID",
    "BULK_DOWNLOAD_ORCHESTRATION_ERROR_INVARIANT_INVALID",
    "BULK_DOWNLOAD_ORCHESTRATION_ERROR_FAIL_CLOSED",
    "BULK_DOWNLOAD_STAGE_RESULT_INVARIANT_INVALID",
    "BULK_DOWNLOAD_STAGE_SCOPE_INVALID",
    "BULK_DOWNLOAD_STAGE_IO_INVARIANT_INVALID",
    "BULK_DOWNLOAD_ACTION_PERMISSION_TRANSITION_UNAUTHORIZED",
    "BULK_DOWNLOAD_CANDIDATE_VERDICT_INVALID",
    "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED",
    "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED",
)


@dataclass(frozen=True)
class BulkDownloadStageOrchestrationCallSiteDecisionDesign:
    schema_version: str
    outcome: str
    passed: bool
    blocks_download: bool
    reason: str
    source_kind: str
    source_scope_id: str
    source_error_code: str
    candidate_count: int
    invalid_candidate_indexes: tuple[int, ...]
    blocked_candidate_indexes: tuple[int, ...]
    failing_candidate_indexes: tuple[int, ...]
    action_permission_granted: bool
    download_action_invoked: bool
    call_site_io_used: bool

    def __post_init__(self) -> None:
        values = vars(self)
        if (
            type(values) is not dict
            or tuple(values) != DECISION_FIELDS
            or tuple(self.__dataclass_fields__) != DECISION_FIELDS
        ):
            raise TypeError("call-site decision Exact15 storage/order invalid")
        if any(
            type(values[name]) is not str
            for name in (
                "schema_version",
                "outcome",
                "reason",
                "source_kind",
                "source_scope_id",
                "source_error_code",
            )
        ):
            raise TypeError("call-site decision string field type invalid")
        if any(
            type(values[name]) is not bool
            for name in (
                "passed",
                "blocks_download",
                "action_permission_granted",
                "download_action_invoked",
                "call_site_io_used",
            )
        ):
            raise TypeError("call-site decision bool field type invalid")
        if type(self.candidate_count) is not int or self.candidate_count < 0:
            raise ValueError("call-site decision candidate count invalid")
        index_names = (
            "invalid_candidate_indexes",
            "blocked_candidate_indexes",
            "failing_candidate_indexes",
        )
        for name in index_names:
            indexes = values[name]
            if (
                type(indexes) is not tuple
                or any(type(index) is not int for index in indexes)
                or indexes != tuple(sorted(set(indexes)))
                or any(
                    index < 0 or index >= self.candidate_count
                    for index in indexes
                )
            ):
                raise ValueError("call-site decision diagnostic indexes invalid")
        expected_failing = tuple(
            index
            for index in range(self.candidate_count)
            if index in self.invalid_candidate_indexes
            or index in self.blocked_candidate_indexes
        )
        if self.failing_candidate_indexes != expected_failing:
            raise ValueError("call-site decision failing projection invalid")
        if (
            self.schema_version != DECISION_SCHEMA_VERSION
            or self.outcome not in OUTCOME_VOCABULARY
            or self.source_kind not in SOURCE_KIND_VOCABULARY
            or self.passed is not (self.outcome == "authorized")
            or self.blocks_download is not (self.outcome != "authorized")
            or self.download_action_invoked is not False
            or self.call_site_io_used is not False
            or (
                self.outcome == "authorized"
                and self.reason != ""
            )
            or (
                self.outcome != "authorized"
                and self.reason not in REASON_VOCABULARY
            )
        ):
            raise ValueError("call-site decision invariant invalid")


def _decision(
    outcome: str,
    reason: str,
    source_kind: str,
    *,
    source_scope_id: str = "",
    source_error_code: str = "",
    candidate_count: int = 0,
    invalid_candidate_indexes: tuple[int, ...] = (),
    blocked_candidate_indexes: tuple[int, ...] = (),
    action_permission_granted: bool = False,
) -> BulkDownloadStageOrchestrationCallSiteDecisionDesign:
    failing = tuple(
        index
        for index in range(candidate_count)
        if index in invalid_candidate_indexes
        or index in blocked_candidate_indexes
    )
    return BulkDownloadStageOrchestrationCallSiteDecisionDesign(
        schema_version=DECISION_SCHEMA_VERSION,
        outcome=outcome,
        passed=outcome == "authorized",
        blocks_download=outcome != "authorized",
        reason=reason,
        source_kind=source_kind,
        source_scope_id=source_scope_id,
        source_error_code=source_error_code,
        candidate_count=candidate_count,
        invalid_candidate_indexes=invalid_candidate_indexes,
        blocked_candidate_indexes=blocked_candidate_indexes,
        failing_candidate_indexes=failing,
        action_permission_granted=action_permission_granted,
        download_action_invoked=False,
        call_site_io_used=False,
    )


def _error_invariant_valid(value: object) -> bool:
    if type(value) is not contract.StageAdmissionOrchestrationError:
        return False
    try:
        values = vars(value)
        if (
            type(values) is not dict
            or tuple(values) != contract.ERROR_FIELDS
            or tuple(value.__dataclass_fields__) != contract.ERROR_FIELDS
        ):
            return False
        if (
            type(value.code) is not str
            or value.code not in contract.ERROR_CODES
            or any(
                type(values[name]) is not str
                for name in (
                    "scope_id",
                    "admission_rule_id",
                    "reason",
                    "cause_type",
                )
            )
            or type(value.candidate_index) is not int
            or value.candidate_index < -1
            or any(
                type(values[name]) is not int or values[name] < 0
                for name in (
                    "dispatcher_call_count",
                    "aggregator_call_count",
                )
            )
            or value.reason == ""
        ):
            return False
        reconstructed = type(value)(**values)
        return (
            reconstructed == value
            and str(value) == value.reason
            and value.args == (value.reason,)
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _candidate_invariant_valid(
    value: object,
    *,
    candidate_index: int,
    scope_id: str,
    candidate_rule_count: int,
    required_rule_ids: tuple[str, ...],
    stage_positions: tuple[tuple[int, UnifiedAdmissionRuleEvaluation], ...],
) -> bool:
    if type(value) is not contract.CandidateAdmissionOrchestrationResult:
        return False
    try:
        values = vars(value)
        if (
            type(values) is not dict
            or tuple(values) != contract.CANDIDATE_RESULT_FIELDS
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
            or len(value.ordered_rule_evaluations) != len(required_rule_ids)
        ):
            return False
        if type(value)(**values) != value:
            return False
        if tuple(
            item.admission_rule_id
            for item in value.ordered_rule_evaluations
        ) != required_rule_ids:
            return False
        for position, stage_result in stage_positions:
            if value.ordered_rule_evaluations[position] is not stage_result:
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
        values = vars(value)
        if (
            type(values) is not dict
            or tuple(values) != contract.STAGE_RESULT_FIELDS
            or tuple(value.__dataclass_fields__) != contract.STAGE_RESULT_FIELDS
        ):
            return False
        if any(
            type(values[name]) is not str
            for name in ("schema_version", "scope_id")
        ) or any(
            type(values[name]) is not int
            for name in (
                "candidate_count",
                "dispatcher_call_count",
                "aggregator_call_count",
            )
        ) or any(
            type(values[name]) is not bool
            for name in (
                "orchestration_io_used",
                "action_permission_granted",
            )
        ):
            return False
        tuple_names = (
            "required_rule_ids",
            "stage_global_rule_ids",
            "candidate_rule_ids",
            "stage_global_rule_evaluations",
            "candidate_results",
        )
        if any(type(values[name]) is not tuple for name in tuple_names):
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
        ):
            return False
        if type(value)(**values) != value:
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
            _candidate_invariant_valid(
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


def classify_bulk_download_stage_orchestration_call_site_contract_design(
    *,
    orchestration_result: contract.StageAdmissionOrchestrationResult | None,
    orchestration_error: contract.StageAdmissionOrchestrationError | None,
) -> BulkDownloadStageOrchestrationCallSiteDecisionDesign:
    """Validate one exact source and project the current V1 call-site decision."""
    result_present = orchestration_result is not None
    error_present = orchestration_error is not None
    if result_present is error_present:
        return _decision(
            "invalid",
            REASON_VOCABULARY[0],
            "invalid_input",
        )
    if result_present:
        if type(orchestration_result) is not contract.StageAdmissionOrchestrationResult:
            return _decision(
                "invalid",
                REASON_VOCABULARY[1],
                "orchestration_result",
            )
        if not _stage_result_invariant_valid(orchestration_result):
            return _decision(
                "invalid",
                REASON_VOCABULARY[5],
                "orchestration_result",
            )
        source = orchestration_result
        if source.scope_id != DOWNLOAD_SCOPE_ID:
            return _decision(
                "invalid",
                REASON_VOCABULARY[6],
                "orchestration_result",
                source_scope_id=source.scope_id,
                candidate_count=source.candidate_count,
                action_permission_granted=source.action_permission_granted,
            )
        if source.orchestration_io_used is not False:
            return _decision(
                "invalid",
                REASON_VOCABULARY[7],
                "orchestration_result",
                source_scope_id=source.scope_id,
                candidate_count=source.candidate_count,
                action_permission_granted=source.action_permission_granted,
            )
        invalid = tuple(
            item.candidate_index
            for item in source.candidate_results
            if item.combined_verdict.outcome == "invalid"
        )
        blocked = tuple(
            item.candidate_index
            for item in source.candidate_results
            if item.combined_verdict.outcome == "blocked"
        )
        projection = {
            "source_scope_id": source.scope_id,
            "candidate_count": source.candidate_count,
            "invalid_candidate_indexes": invalid,
            "blocked_candidate_indexes": blocked,
            "action_permission_granted": source.action_permission_granted,
        }
        if source.action_permission_granted is True:
            return _decision(
                "invalid",
                REASON_VOCABULARY[8],
                "orchestration_result",
                **projection,
            )
        if invalid:
            return _decision(
                "invalid",
                REASON_VOCABULARY[9],
                "orchestration_result",
                **projection,
            )
        if blocked:
            return _decision(
                "blocked",
                REASON_VOCABULARY[10],
                "orchestration_result",
                **projection,
            )
        return _decision(
            "blocked",
            REASON_VOCABULARY[11],
            "orchestration_result",
            **projection,
        )

    if type(orchestration_error) is not contract.StageAdmissionOrchestrationError:
        return _decision(
            "invalid",
            REASON_VOCABULARY[2],
            "orchestration_error",
        )
    if not _error_invariant_valid(orchestration_error):
        return _decision(
            "invalid",
            REASON_VOCABULARY[3],
            "orchestration_error",
        )
    return _decision(
        "invalid",
        REASON_VOCABULARY[4],
        "orchestration_error",
        source_scope_id=orchestration_error.scope_id,
        source_error_code=orchestration_error.code,
    )
