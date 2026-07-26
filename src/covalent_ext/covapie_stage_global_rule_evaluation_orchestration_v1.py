"""Pure in-memory stage-global admission orchestration runtime.

The runtime evaluates the committed stage-global rules once, evaluates every
candidate-scoped rule in canonical order, assembles each complete scope
vector, and delegates the verdict to the committed combined aggregator.  It
performs no provider, network, download, raw-data, model, checkpoint,
dataloader, or training action.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)


AdmissionCandidateOrchestrationInput = (
    contract.AdmissionCandidateOrchestrationInput
)
CandidateAdmissionOrchestrationResult = (
    contract.CandidateAdmissionOrchestrationResult
)
StageAdmissionOrchestrationResult = contract.StageAdmissionOrchestrationResult
StageAdmissionOrchestrationError = contract.StageAdmissionOrchestrationError

__all__ = (
    "AdmissionCandidateOrchestrationInput",
    "CandidateAdmissionOrchestrationResult",
    "StageAdmissionOrchestrationResult",
    "StageAdmissionOrchestrationError",
    "orchestrate_stage_admission_scope",
)


_NONE_CONTEXT_ROUTE = (False, False, False)
_CANDIDATE_CONTEXT_ROUTING = MappingProxyType(
    {
        "ADMIT_001": (True, False, False),
        "ADMIT_002": _NONE_CONTEXT_ROUTE,
        "ADMIT_003": _NONE_CONTEXT_ROUTE,
        "ADMIT_004": (False, True, False),
        "ADMIT_005": _NONE_CONTEXT_ROUTE,
        "ADMIT_006": (False, True, False),
        "ADMIT_007": (False, True, False),
        "ADMIT_008": (False, True, False),
        "ADMIT_009": (True, True, False),
        "ADMIT_010": (False, True, False),
        "ADMIT_011": (False, True, False),
        "ADMIT_012": (False, True, True),
        "ADMIT_013": (False, True, True),
    }
)


def _prevalidation_error(
    code: str,
    scope_id: object,
) -> StageAdmissionOrchestrationError:
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


def _failure_reason(
    code: str,
    failure_kind: str,
    scope_id: str,
    candidate_index: int,
    admission_rule_id: str,
) -> str:
    return (
        f"{code}:{failure_kind}:{scope_id}:"
        f"candidate_index={candidate_index}:"
        f"admission_rule_id={admission_rule_id}"
    )


def _raise_callable_failure(
    code: str,
    failure_kind: str,
    scope_id: str,
    *,
    candidate_index: int,
    rule_position: int,
    cause: Exception,
) -> NoReturn:
    coordinate = contract.compute_failure_coordinate_design(
        scope_id,
        failure_kind,
        candidate_index=candidate_index,
        rule_position=rule_position,
    )
    raise StageAdmissionOrchestrationError(
        code=code,
        scope_id=scope_id,
        candidate_index=coordinate.candidate_index,
        admission_rule_id=coordinate.admission_rule_id,
        dispatcher_call_count=coordinate.dispatcher_call_count,
        aggregator_call_count=coordinate.aggregator_call_count,
        reason=_failure_reason(
            code,
            failure_kind,
            scope_id,
            coordinate.candidate_index,
            coordinate.admission_rule_id,
        ),
        cause_type=type(cause).__name__,
    ) from cause


def _candidate_contexts(
    admission_rule_id: str,
    candidate_input: AdmissionCandidateOrchestrationInput,
    batch_context: Mapping[str, object] | None,
) -> tuple[
    Mapping[str, object] | None,
    Mapping[str, object] | None,
    Mapping[str, object] | None,
]:
    use_batch, use_evaluation, use_download = _CANDIDATE_CONTEXT_ROUTING[
        admission_rule_id
    ]
    return (
        batch_context if use_batch else None,
        candidate_input.evaluation_context if use_evaluation else None,
        candidate_input.download_result_context if use_download else None,
    )


def orchestrate_stage_admission_scope(
    scope_id: str,
    candidate_inputs: tuple[AdmissionCandidateOrchestrationInput, ...],
    *,
    batch_context: Mapping[str, object] | None,
    stage_authorization_context: Mapping[str, object] | None,
) -> StageAdmissionOrchestrationResult:
    """Evaluate and aggregate one complete in-memory admission stage."""
    if type(scope_id) is not str:
        raise _prevalidation_error(contract.ERROR_CODES[0], scope_id)
    if scope_id not in contract.SCOPE_IDS:
        raise _prevalidation_error(contract.ERROR_CODES[0], scope_id)
    if type(candidate_inputs) is not tuple or not candidate_inputs:
        raise _prevalidation_error(contract.ERROR_CODES[1], scope_id)
    for candidate_input in candidate_inputs:
        if type(candidate_input) is not AdmissionCandidateOrchestrationInput:
            raise _prevalidation_error(contract.ERROR_CODES[2], scope_id)
    for candidate_input in candidate_inputs:
        if not isinstance(candidate_input.candidate_record, Mapping):
            raise _prevalidation_error(contract.ERROR_CODES[2], scope_id)
        if (
            candidate_input.evaluation_context is not None
            and not isinstance(candidate_input.evaluation_context, Mapping)
        ):
            raise _prevalidation_error(contract.ERROR_CODES[2], scope_id)
        if (
            candidate_input.download_result_context is not None
            and not isinstance(
                candidate_input.download_result_context, Mapping
            )
        ):
            raise _prevalidation_error(contract.ERROR_CODES[2], scope_id)
    if batch_context is not None and not isinstance(batch_context, Mapping):
        raise _prevalidation_error(contract.ERROR_CODES[3], scope_id)
    if (
        stage_authorization_context is not None
        and not isinstance(stage_authorization_context, Mapping)
    ):
        raise _prevalidation_error(contract.ERROR_CODES[4], scope_id)

    required_rule_ids = contract.REQUIRED_RULE_IDS[scope_id]
    stage_global_rule_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
    candidate_rule_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]
    dispatcher_call_count = 0
    aggregator_call_count = 0

    stage_global_results: list[object] = []
    for rule_position, admission_rule_id in enumerate(
        stage_global_rule_ids, 1
    ):
        dispatcher_call_count += 1
        try:
            result = dispatch_runtime.evaluate_admission_rule(
                admission_rule_id,
                contract.STAGE_GLOBAL_CANDIDATE_SENTINEL,
                batch_context=None,
                evaluation_context=None,
                download_result_context=None,
                stage_authorization_context=stage_authorization_context,
            )
        except Exception as cause:
            _raise_callable_failure(
                contract.ERROR_CODES[5],
                "stage_global_dispatch",
                scope_id,
                candidate_index=-1,
                rule_position=rule_position,
                cause=cause,
            )
        validated = contract.validate_unified_rule_evaluation_design(
            result,
            expected_rule_id=admission_rule_id,
            scope_id=scope_id,
            candidate_index=-1,
            dispatcher_call_count=dispatcher_call_count,
            aggregator_call_count=aggregator_call_count,
        )
        stage_global_results.append(validated)

    stage_global_rule_evaluations = tuple(stage_global_results)
    stage_results_by_rule_id = {
        item.admission_rule_id: item
        for item in stage_global_rule_evaluations
    }
    candidate_results: list[CandidateAdmissionOrchestrationResult] = []

    for candidate_index, candidate_input in enumerate(candidate_inputs):
        candidate_results_by_rule_id: dict[str, object] = {}
        for rule_position, admission_rule_id in enumerate(
            candidate_rule_ids, 1
        ):
            routed_batch, routed_evaluation, routed_download = (
                _candidate_contexts(
                    admission_rule_id,
                    candidate_input,
                    batch_context,
                )
            )
            dispatcher_call_count += 1
            try:
                result = dispatch_runtime.evaluate_admission_rule(
                    admission_rule_id,
                    candidate_input.candidate_record,
                    batch_context=routed_batch,
                    evaluation_context=routed_evaluation,
                    download_result_context=routed_download,
                    stage_authorization_context=None,
                )
            except Exception as cause:
                _raise_callable_failure(
                    contract.ERROR_CODES[5],
                    "candidate_dispatch",
                    scope_id,
                    candidate_index=candidate_index,
                    rule_position=rule_position,
                    cause=cause,
                )
            validated = contract.validate_unified_rule_evaluation_design(
                result,
                expected_rule_id=admission_rule_id,
                scope_id=scope_id,
                candidate_index=candidate_index,
                dispatcher_call_count=dispatcher_call_count,
                aggregator_call_count=aggregator_call_count,
            )
            candidate_results_by_rule_id[admission_rule_id] = validated

        ordered_vector = tuple(
            (
                stage_results_by_rule_id[admission_rule_id]
                if admission_rule_id in stage_results_by_rule_id
                else candidate_results_by_rule_id[admission_rule_id]
            )
            for admission_rule_id in required_rule_ids
        )
        aggregator_call_count += 1
        try:
            verdict = (
                aggregation_runtime.aggregate_admission_rule_evaluations(
                    scope_id,
                    ordered_rule_evaluations=ordered_vector,
                )
            )
        except Exception as cause:
            _raise_callable_failure(
                contract.ERROR_CODES[7],
                "candidate_aggregator",
                scope_id,
                candidate_index=candidate_index,
                rule_position=0,
                cause=cause,
            )
        validated_verdict = contract.validate_combined_candidate_verdict_design(
            verdict,
            expected_scope_id=scope_id,
            ordered_rule_evaluations=ordered_vector,
            candidate_index=candidate_index,
            dispatcher_call_count=dispatcher_call_count,
            aggregator_call_count=aggregator_call_count,
        )
        candidate_results.append(
            CandidateAdmissionOrchestrationResult(
                candidate_index=candidate_index,
                ordered_rule_evaluations=ordered_vector,
                combined_verdict=validated_verdict,
                dispatcher_call_count=len(candidate_rule_ids),
                aggregator_call_count=1,
            )
        )

    return StageAdmissionOrchestrationResult(
        schema_version=contract.STAGE_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        candidate_count=len(candidate_inputs),
        required_rule_ids=required_rule_ids,
        stage_global_rule_ids=stage_global_rule_ids,
        candidate_rule_ids=candidate_rule_ids,
        stage_global_rule_evaluations=stage_global_rule_evaluations,
        candidate_results=tuple(candidate_results),
        dispatcher_call_count=dispatcher_call_count,
        aggregator_call_count=aggregator_call_count,
        orchestration_io_used=False,
        action_permission_granted=False,
    )
