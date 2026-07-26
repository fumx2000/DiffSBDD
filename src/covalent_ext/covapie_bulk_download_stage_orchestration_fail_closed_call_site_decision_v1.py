"""Deterministic in-memory bulk-download orchestration call-site decision."""

from __future__ import annotations

from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as design,
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


BulkDownloadStageOrchestrationCallSiteDecisionDesign = (
    design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
)

__all__ = (
    "BulkDownloadStageOrchestrationCallSiteDecisionDesign",
    "evaluate_bulk_download_stage_orchestration_call_site",
)


def _build_decision(
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
    failing_candidate_indexes = tuple(
        index
        for index in range(candidate_count)
        if (
            index in invalid_candidate_indexes
            or index in blocked_candidate_indexes
        )
    )
    return BulkDownloadStageOrchestrationCallSiteDecisionDesign(
        schema_version=design.DECISION_SCHEMA_VERSION,
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
        failing_candidate_indexes=failing_candidate_indexes,
        action_permission_granted=action_permission_granted,
        download_action_invoked=False,
        call_site_io_used=False,
    )


def _orchestration_error_is_valid(value: object) -> bool:
    if type(value) is not contract.StageAdmissionOrchestrationError:
        return False
    try:
        stored = vars(value)
        if (
            type(stored) is not dict
            or tuple(stored) != contract.ERROR_FIELDS
            or tuple(value.__dataclass_fields__) != contract.ERROR_FIELDS
        ):
            return False
        if (
            type(value.code) is not str
            or value.code not in contract.ERROR_CODES
            or type(value.scope_id) is not str
            or type(value.candidate_index) is not int
            or value.candidate_index < -1
            or type(value.admission_rule_id) is not str
            or type(value.dispatcher_call_count) is not int
            or value.dispatcher_call_count < 0
            or type(value.aggregator_call_count) is not int
            or value.aggregator_call_count < 0
            or type(value.reason) is not str
            or value.reason == ""
            or type(value.cause_type) is not str
        ):
            return False
        reconstructed = type(value)(**stored)
        return (
            reconstructed == value
            and str(value) == value.reason
            and value.args == (value.reason,)
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _candidate_result_is_valid(
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


def _stage_result_is_valid(value: object) -> bool:
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
            _candidate_result_is_valid(
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


def evaluate_bulk_download_stage_orchestration_call_site(
    *,
    orchestration_result: contract.StageAdmissionOrchestrationResult | None,
    orchestration_error: contract.StageAdmissionOrchestrationError | None,
) -> design.BulkDownloadStageOrchestrationCallSiteDecisionDesign:
    """Validate exactly one orchestration source and return a closed decision."""
    result_present = orchestration_result is not None
    error_present = orchestration_error is not None
    if result_present is error_present:
        return _build_decision(
            "invalid",
            design.REASON_VOCABULARY[0],
            "invalid_input",
        )

    if result_present:
        if (
            type(orchestration_result)
            is not contract.StageAdmissionOrchestrationResult
        ):
            return _build_decision(
                "invalid",
                design.REASON_VOCABULARY[1],
                "orchestration_result",
            )
        if not _stage_result_is_valid(orchestration_result):
            return _build_decision(
                "invalid",
                design.REASON_VOCABULARY[5],
                "orchestration_result",
            )
        source = orchestration_result
        if source.scope_id != design.DOWNLOAD_SCOPE_ID:
            return _build_decision(
                "invalid",
                design.REASON_VOCABULARY[6],
                "orchestration_result",
                source_scope_id=source.scope_id,
                candidate_count=source.candidate_count,
                action_permission_granted=source.action_permission_granted,
            )
        if source.orchestration_io_used is not False:
            return _build_decision(
                "invalid",
                design.REASON_VOCABULARY[7],
                "orchestration_result",
                source_scope_id=source.scope_id,
                candidate_count=source.candidate_count,
                action_permission_granted=source.action_permission_granted,
            )
        invalid_candidate_indexes = tuple(
            candidate.candidate_index
            for candidate in source.candidate_results
            if candidate.combined_verdict.outcome == "invalid"
        )
        blocked_candidate_indexes = tuple(
            candidate.candidate_index
            for candidate in source.candidate_results
            if candidate.combined_verdict.outcome == "blocked"
        )
        projection = {
            "source_scope_id": source.scope_id,
            "candidate_count": source.candidate_count,
            "invalid_candidate_indexes": invalid_candidate_indexes,
            "blocked_candidate_indexes": blocked_candidate_indexes,
            "action_permission_granted": source.action_permission_granted,
        }
        if source.action_permission_granted is True:
            return _build_decision(
                "invalid",
                design.REASON_VOCABULARY[8],
                "orchestration_result",
                **projection,
            )
        if invalid_candidate_indexes:
            return _build_decision(
                "invalid",
                design.REASON_VOCABULARY[9],
                "orchestration_result",
                **projection,
            )
        if blocked_candidate_indexes:
            return _build_decision(
                "blocked",
                design.REASON_VOCABULARY[10],
                "orchestration_result",
                **projection,
            )
        return _build_decision(
            "blocked",
            design.REASON_VOCABULARY[11],
            "orchestration_result",
            **projection,
        )

    if (
        type(orchestration_error)
        is not contract.StageAdmissionOrchestrationError
    ):
        return _build_decision(
            "invalid",
            design.REASON_VOCABULARY[2],
            "orchestration_error",
        )
    if not _orchestration_error_is_valid(orchestration_error):
        return _build_decision(
            "invalid",
            design.REASON_VOCABULARY[3],
            "orchestration_error",
        )
    return _build_decision(
        "invalid",
        design.REASON_VOCABULARY[4],
        "orchestration_error",
        source_scope_id=orchestration_error.scope_id,
        source_error_code=orchestration_error.code,
    )
