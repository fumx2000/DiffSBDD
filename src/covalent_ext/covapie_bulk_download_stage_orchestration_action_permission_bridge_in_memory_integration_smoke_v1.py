"""Two-chain, pure in-memory action-permission bridge integration smoke V1."""

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
    covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate
    as bridge_contract,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_v1
    as bridge_runtime,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as call_site_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as canonical_fixtures,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


BASE_COMMIT = "beb42c497d3f0e47e009b2dc84aac929938824e5"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration action-permission bridge "
    "integration smoke v1"
)
DOWNLOAD_SCOPE_ID = "download_execution_permission"
CURRENT_BLOCKED = "current_blocked"
FUTURE_ELIGIBLE = "future_eligible"
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
    "review_covapie_post_admission_control_plane_completion_and_select_"
    "next_training_preparation_blocker_v1"
)


@dataclass(frozen=True)
class ActionPermissionBridgeChainObservation:
    profile_name: str
    source_mode: str
    stage_scope_id: str
    candidate_count: int
    admit_014_outcome: str
    candidate_combined_outcomes: tuple[str, ...]
    call_site_outcome: str
    call_site_reason: str
    bridge_outcome: str
    bridge_reason: str
    source_lineage_verified: bool
    transition_eligible: bool
    action_permission_granted: bool
    download_action_invoked: bool
    bridge_io_used: bool


@dataclass(frozen=True)
class ActionPermissionBridgeIntegrationSmokeReport:
    observations: tuple[ActionPermissionBridgeChainObservation, ...]
    observation_count: int
    actual_orchestrator_called: bool
    actual_call_site_runtime_called: bool
    actual_bridge_runtime_called: bool
    runtime_identities_unchanged: bool
    monkeypatch_used_for_success_evidence: bool
    permission_transition_attempted: bool
    permission_transition_completed: bool
    transition_eligible_count: int
    action_permission_granted_count: int
    download_action_count: int
    bridge_io_count: int
    ready_for_download: bool
    ready_for_training: bool


def _runtime_identity_snapshot() -> tuple[object, ...]:
    return (
        orchestration_runtime.orchestrate_stage_admission_scope,
        call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )


_COMMITTED_RUNTIME_IDENTITIES = _runtime_identity_snapshot()


def _assert_runtime_identities_unchanged(
    before: tuple[object, ...], after: tuple[object, ...]
) -> None:
    if any(
        before[index] is not after[index]
        for index in (0, 1, 2, 3, 4, 6)
    ):
        raise RuntimeError("committed runtime identity changed")
    before_handlers = before[5]
    after_handlers = after[5]
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
        raise RuntimeError("committed registered handler identity changed")


def _expected_exact19(source_mode: str) -> dict[str, object]:
    if source_mode == CURRENT_BLOCKED:
        return {
            "schema_version": (
                "covapie_bulk_download_stage_orchestration_"
                "action_permission_bridge_decision_v1"
            ),
            "outcome": "blocked",
            "passed": False,
            "blocks_transition": True,
            "reason": "ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED",
            "source_scope_id": DOWNLOAD_SCOPE_ID,
            "candidate_count": 1,
            "admit_014_outcome": "blocked",
            "candidate_combined_outcomes": ("blocked",),
            "call_site_decision_outcome": "blocked",
            "call_site_decision_reason": (
                "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"
            ),
            "invalid_candidate_indexes": (),
            "blocked_candidate_indexes": (0,),
            "failing_candidate_indexes": (0,),
            "source_lineage_verified": True,
            "transition_eligible": False,
            "action_permission_granted": False,
            "download_action_invoked": False,
            "bridge_io_used": False,
        }
    if source_mode == FUTURE_ELIGIBLE:
        return {
            "schema_version": (
                "covapie_bulk_download_stage_orchestration_"
                "action_permission_bridge_decision_v1"
            ),
            "outcome": "eligible",
            "passed": True,
            "blocks_transition": False,
            "reason": "ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE",
            "source_scope_id": DOWNLOAD_SCOPE_ID,
            "candidate_count": 1,
            "admit_014_outcome": "passed",
            "candidate_combined_outcomes": ("passed",),
            "call_site_decision_outcome": "blocked",
            "call_site_decision_reason": (
                "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"
            ),
            "invalid_candidate_indexes": (),
            "blocked_candidate_indexes": (),
            "failing_candidate_indexes": (),
            "source_lineage_verified": True,
            "transition_eligible": True,
            "action_permission_granted": False,
            "download_action_invoked": False,
            "bridge_io_used": False,
        }
    raise ValueError("unknown source mode")


def _assert_exact19(decision: object, expected: dict[str, object]) -> None:
    if (
        type(decision)
        is not bridge_contract.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        or tuple(vars(decision)) != bridge_contract.DECISION_FIELDS
        or tuple(expected) != bridge_contract.DECISION_FIELDS
    ):
        raise RuntimeError("actual bridge Exact19 shape changed")
    for name in bridge_contract.DECISION_FIELDS:
        observed = getattr(decision, name)
        wanted = expected[name]
        if type(observed) is not type(wanted) or observed != wanted:
            raise RuntimeError(f"actual bridge Exact19 mismatch: {name}")


def _run_chain(
    fixture: object,
    source_mode: str,
    authorization: object,
) -> ActionPermissionBridgeChainObservation:
    result = orchestration_runtime.orchestrate_stage_admission_scope(
        DOWNLOAD_SCOPE_ID,
        fixture.candidate_inputs,
        batch_context=fixture.batch_context,
        stage_authorization_context=authorization,
    )
    call_site = (
        call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
            orchestration_result=result,
            orchestration_error=None,
        )
    )
    bridge = (
        bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge(
            orchestration_result=result,
            call_site_decision=call_site,
        )
    )
    _assert_exact19(bridge, _expected_exact19(source_mode))
    admit_014 = next(
        item.outcome
        for item in result.stage_global_rule_evaluations
        if item.admission_rule_id == "ADMIT_014"
    )
    return ActionPermissionBridgeChainObservation(
        profile_name=fixture.fixture_profile,
        source_mode=source_mode,
        stage_scope_id=result.scope_id,
        candidate_count=result.candidate_count,
        admit_014_outcome=admit_014,
        candidate_combined_outcomes=tuple(
            item.combined_verdict.outcome for item in result.candidate_results
        ),
        call_site_outcome=call_site.outcome,
        call_site_reason=call_site.reason,
        bridge_outcome=bridge.outcome,
        bridge_reason=bridge.reason,
        source_lineage_verified=bridge.source_lineage_verified,
        transition_eligible=bridge.transition_eligible,
        action_permission_granted=bridge.action_permission_granted,
        download_action_invoked=bridge.download_action_invoked,
        bridge_io_used=bridge.bridge_io_used,
    )


def run_covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke(
) -> ActionPermissionBridgeIntegrationSmokeReport:
    """Run the fixed blocked and future-eligible chains without transition."""
    _assert_runtime_identities_unchanged(
        _COMMITTED_RUNTIME_IDENTITIES, _runtime_identity_snapshot()
    )
    fixture = canonical_fixtures.build_canonical_in_memory_fixture_profiles()[0]
    original_authorization = dict(fixture.stage_authorization_context)
    current = _run_chain(
        fixture,
        CURRENT_BLOCKED,
        fixture.stage_authorization_context,
    )
    authorization = dict(fixture.stage_authorization_context)
    authorization["current_stage_download_authorized"] = True
    future = _run_chain(fixture, FUTURE_ELIGIBLE, authorization)
    if dict(fixture.stage_authorization_context) != original_authorization:
        raise RuntimeError("committed canonical fixture was modified")
    _assert_runtime_identities_unchanged(
        _COMMITTED_RUNTIME_IDENTITIES, _runtime_identity_snapshot()
    )

    observations = (current, future)
    transition_count = sum(
        item.transition_eligible for item in observations
    )
    permission_count = sum(
        item.action_permission_granted for item in observations
    )
    download_count = sum(item.download_action_invoked for item in observations)
    io_count = sum(item.bridge_io_used for item in observations)
    if (
        transition_count != 1
        or permission_count != 0
        or download_count != 0
        or io_count != 0
    ):
        raise RuntimeError("integration smoke safety invariant failed")
    return ActionPermissionBridgeIntegrationSmokeReport(
        observations=observations,
        observation_count=2,
        actual_orchestrator_called=True,
        actual_call_site_runtime_called=True,
        actual_bridge_runtime_called=True,
        runtime_identities_unchanged=True,
        monkeypatch_used_for_success_evidence=False,
        permission_transition_attempted=False,
        permission_transition_completed=False,
        transition_eligible_count=transition_count,
        action_permission_granted_count=permission_count,
        download_action_count=download_count,
        bridge_io_count=io_count,
        ready_for_download=False,
        ready_for_training=False,
    )


def serialize_integration_smoke_report(
    report: ActionPermissionBridgeIntegrationSmokeReport,
) -> bytes:
    """Return deterministic, address-free report bytes."""
    if type(report) is not ActionPermissionBridgeIntegrationSmokeReport:
        raise TypeError("exact integration smoke report required")
    return (
        json.dumps(asdict(report), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


__all__ = (
    "ActionPermissionBridgeChainObservation",
    "ActionPermissionBridgeIntegrationSmokeReport",
    "run_covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke",
    "serialize_integration_smoke_report",
)
