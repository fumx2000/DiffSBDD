"""Actual-chain, pure in-memory call-site decision integration smoke V1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as decision_contract,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as decision_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as orchestration_contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as canonical_fixtures,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


BASE_COMMIT = "6e5f3b02183086fea4bb4f35fd03a5c5def7ed8e"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration call-site decision "
    "integration smoke v1"
)
INVALID_SCOPE_ID = "__covapie_invalid_scope_for_integration_smoke__"
ERROR_FIXTURE_PROFILE = "canonical_single_candidate_actual_orchestration_error"
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
EFFECTIVE_OPEN_ISSUES = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_contract_v1"
)


@dataclass(frozen=True)
class CallSiteDecisionChainObservation:
    fixture_profile: str
    source_path_kind: str
    scope_id: str
    candidate_count: int
    orchestrator_completed: bool
    orchestration_error_code: str
    decision_outcome: str
    decision_reason: str
    decision_source_kind: str
    decision_source_scope_id: str
    decision_source_error_code: str
    invalid_candidate_indexes: tuple[int, ...]
    blocked_candidate_indexes: tuple[int, ...]
    failing_candidate_indexes: tuple[int, ...]
    action_permission_granted: bool
    download_action_invoked: bool
    call_site_io_used: bool


@dataclass(frozen=True)
class CallSiteDecisionIntegrationSmokeReport:
    observations: tuple[CallSiteDecisionChainObservation, ...]
    observation_count: int
    actual_orchestrator_called: bool
    actual_decision_runtime_called: bool
    actual_orchestration_error_consumed: bool
    runtime_callable_identities_unchanged: bool
    monkeypatch_used_for_success_evidence: bool
    authorized_decision_count: int
    download_action_count: int
    call_site_io_count: int
    network_used: bool
    provider_used: bool
    download_used: bool
    training_used: bool
    ready_for_download: bool
    ready_for_training: bool


def _runtime_identity_snapshot() -> tuple[object, ...]:
    return (
        orchestration_runtime.orchestrate_stage_admission_scope,
        decision_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )


_COMMITTED_RUNTIME_IDENTITIES = _runtime_identity_snapshot()


def _assert_runtime_identity_unchanged(
    before: tuple[object, ...], after: tuple[object, ...]
) -> None:
    if any(before[index] is not after[index] for index in (0, 1, 2, 3, 5)):
        raise RuntimeError("committed runtime callable identity changed")
    before_handlers = before[4]
    after_handlers = after[4]
    if (
        type(before_handlers) is not tuple
        or type(after_handlers) is not tuple
        or len(before_handlers) != len(after_handlers)
        or any(
            left[0] != right[0] or left[1] is not right[1]
            for left, right in zip(
                before_handlers, after_handlers, strict=True
            )
        )
    ):
        raise RuntimeError("committed Exact15 handler identity changed")


def _expected_exact15(
    *,
    source_path_kind: str,
    scope_id: str,
    candidate_count: int,
    error_code: str,
) -> dict[str, object]:
    if source_path_kind == "orchestration_error":
        outcome = "invalid"
        reason = "BULK_DOWNLOAD_ORCHESTRATION_ERROR_FAIL_CLOSED"
        source_kind = "orchestration_error"
        source_error_code = error_code
        count = 0
        blocked: tuple[int, ...] = ()
    elif scope_id == decision_contract.DOWNLOAD_SCOPE_ID:
        outcome = "blocked"
        reason = "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"
        source_kind = "orchestration_result"
        source_error_code = ""
        count = candidate_count
        blocked = (0,)
    else:
        outcome = "invalid"
        reason = "BULK_DOWNLOAD_STAGE_SCOPE_INVALID"
        source_kind = "orchestration_result"
        source_error_code = ""
        count = candidate_count
        blocked = ()
    return {
        "schema_version": decision_contract.DECISION_SCHEMA_VERSION,
        "outcome": outcome,
        "passed": False,
        "blocks_download": True,
        "reason": reason,
        "source_kind": source_kind,
        "source_scope_id": scope_id,
        "source_error_code": source_error_code,
        "candidate_count": count,
        "invalid_candidate_indexes": (),
        "blocked_candidate_indexes": blocked,
        "failing_candidate_indexes": blocked,
        "action_permission_granted": False,
        "download_action_invoked": False,
        "call_site_io_used": False,
    }


def _assert_exact15(
    decision: object, expected: dict[str, object]
) -> None:
    if (
        type(decision)
        is not decision_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        or tuple(vars(decision)) != decision_contract.DECISION_FIELDS
        or tuple(expected) != decision_contract.DECISION_FIELDS
    ):
        raise RuntimeError("actual decision Exact15 contract changed")
    for field_name in decision_contract.DECISION_FIELDS:
        observed = getattr(decision, field_name)
        wanted = expected[field_name]
        if type(observed) is not type(wanted) or observed != wanted:
            raise RuntimeError(
                f"actual decision Exact15 mismatch: {field_name}"
            )


def _observation(
    fixture_profile: str,
    source_path_kind: str,
    scope_id: str,
    candidate_count: int,
    orchestrator_completed: bool,
    error_code: str,
    decision: object,
) -> CallSiteDecisionChainObservation:
    return CallSiteDecisionChainObservation(
        fixture_profile=fixture_profile,
        source_path_kind=source_path_kind,
        scope_id=scope_id,
        candidate_count=candidate_count,
        orchestrator_completed=orchestrator_completed,
        orchestration_error_code=error_code,
        decision_outcome=decision.outcome,
        decision_reason=decision.reason,
        decision_source_kind=decision.source_kind,
        decision_source_scope_id=decision.source_scope_id,
        decision_source_error_code=decision.source_error_code,
        invalid_candidate_indexes=decision.invalid_candidate_indexes,
        blocked_candidate_indexes=decision.blocked_candidate_indexes,
        failing_candidate_indexes=decision.failing_candidate_indexes,
        action_permission_granted=decision.action_permission_granted,
        download_action_invoked=decision.download_action_invoked,
        call_site_io_used=decision.call_site_io_used,
    )


def run_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke(
) -> CallSiteDecisionIntegrationSmokeReport:
    """Run the fixed six-observation actual chain without action or I/O."""
    _assert_runtime_identity_unchanged(
        _COMMITTED_RUNTIME_IDENTITIES, _runtime_identity_snapshot()
    )
    fixtures = canonical_fixtures.build_canonical_in_memory_fixture_profiles()
    single_fixture, two_fixture = fixtures
    observations: list[CallSiteDecisionChainObservation] = []

    for scope_id in single_fixture.scopes:
        result = orchestration_runtime.orchestrate_stage_admission_scope(
            scope_id,
            single_fixture.candidate_inputs,
            batch_context=single_fixture.batch_context,
            stage_authorization_context=(
                single_fixture.stage_authorization_context
            ),
        )
        decision = (
            decision_runtime.evaluate_bulk_download_stage_orchestration_call_site(
                orchestration_result=result,
                orchestration_error=None,
            )
        )
        expected = _expected_exact15(
            source_path_kind="orchestration_result",
            scope_id=scope_id,
            candidate_count=result.candidate_count,
            error_code="",
        )
        _assert_exact15(decision, expected)
        observations.append(
            _observation(
                single_fixture.fixture_profile,
                "orchestration_result",
                scope_id,
                result.candidate_count,
                True,
                "",
                decision,
            )
        )

    training_scope = two_fixture.scopes[0]
    training_result = (
        orchestration_runtime.orchestrate_stage_admission_scope(
            training_scope,
            two_fixture.candidate_inputs,
            batch_context=two_fixture.batch_context,
            stage_authorization_context=(
                two_fixture.stage_authorization_context
            ),
        )
    )
    training_decision = (
        decision_runtime.evaluate_bulk_download_stage_orchestration_call_site(
            orchestration_result=training_result,
            orchestration_error=None,
        )
    )
    _assert_exact15(
        training_decision,
        _expected_exact15(
            source_path_kind="orchestration_result",
            scope_id=training_scope,
            candidate_count=training_result.candidate_count,
            error_code="",
        ),
    )
    observations.append(
        _observation(
            two_fixture.fixture_profile,
            "orchestration_result",
            training_scope,
            training_result.candidate_count,
            True,
            "",
            training_decision,
        )
    )

    try:
        orchestration_runtime.orchestrate_stage_admission_scope(
            INVALID_SCOPE_ID,
            single_fixture.candidate_inputs,
            batch_context=single_fixture.batch_context,
            stage_authorization_context=(
                single_fixture.stage_authorization_context
            ),
        )
    except orchestration_contract.StageAdmissionOrchestrationError as error:
        if type(error) is not orchestration_contract.StageAdmissionOrchestrationError:
            raise RuntimeError("actual orchestration error type changed")
        error_decision = (
            decision_runtime.evaluate_bulk_download_stage_orchestration_call_site(
                orchestration_result=None,
                orchestration_error=error,
            )
        )
        _assert_exact15(
            error_decision,
            _expected_exact15(
                source_path_kind="orchestration_error",
                scope_id=error.scope_id,
                candidate_count=0,
                error_code=error.code,
            ),
        )
        observations.append(
            _observation(
                ERROR_FIXTURE_PROFILE,
                "orchestration_error",
                error.scope_id,
                0,
                False,
                error.code,
                error_decision,
            )
        )
    else:
        raise RuntimeError("invalid orchestration scope did not fail closed")

    _assert_runtime_identity_unchanged(
        _COMMITTED_RUNTIME_IDENTITIES, _runtime_identity_snapshot()
    )
    frozen_observations = tuple(observations)
    authorized_count = sum(
        item.decision_outcome == "authorized"
        for item in frozen_observations
    )
    action_count = sum(
        item.download_action_invoked for item in frozen_observations
    )
    io_count = sum(item.call_site_io_used for item in frozen_observations)
    if (
        len(frozen_observations) != 6
        or authorized_count != 0
        or action_count != 0
        or io_count != 0
    ):
        raise RuntimeError("integration smoke closed-state invariant failed")
    return CallSiteDecisionIntegrationSmokeReport(
        observations=frozen_observations,
        observation_count=6,
        actual_orchestrator_called=True,
        actual_decision_runtime_called=True,
        actual_orchestration_error_consumed=True,
        runtime_callable_identities_unchanged=True,
        monkeypatch_used_for_success_evidence=False,
        authorized_decision_count=authorized_count,
        download_action_count=action_count,
        call_site_io_count=io_count,
        network_used=False,
        provider_used=False,
        download_used=False,
        training_used=False,
        ready_for_download=False,
        ready_for_training=False,
    )


def serialize_integration_smoke_report(
    report: CallSiteDecisionIntegrationSmokeReport,
) -> bytes:
    """Return deterministic, address-free report bytes."""
    if type(report) is not CallSiteDecisionIntegrationSmokeReport:
        raise TypeError("exact integration smoke report required")
    return (
        json.dumps(asdict(report), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


__all__ = (
    "CallSiteDecisionChainObservation",
    "CallSiteDecisionIntegrationSmokeReport",
    "run_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke",
    "serialize_integration_smoke_report",
)
