#!/usr/bin/env python3
"""Independent checker for the action-permission bridge design contract."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import get_type_hints

from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as call_site_contract,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as call_site_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as fixture_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1"
)
EXACT10 = (
    Path("src/covalent_ext/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate.py"),
    Path("tests/test_covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1.py"),
    Path("scripts/check_covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1.py"),
    Path("docs/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1_summary.md"),
    OUTPUT_ROOT / "covapie_action_permission_bridge_public_api_and_decision_contract.csv",
    OUTPUT_ROOT / "covapie_action_permission_bridge_precedence_truth_matrix.csv",
    OUTPUT_ROOT / "covapie_action_permission_bridge_source_lineage_invariant_matrix.csv",
    OUTPUT_ROOT / "covapie_action_permission_bridge_safety_audit.csv",
    OUTPUT_ROOT / "covapie_action_permission_bridge_issue_readiness_inventory.csv",
    OUTPUT_ROOT / "covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_manifest.json",
)
OUTPUT_NAMES = tuple(path.name for path in EXACT10[4:])
PREDECESSOR_ISSUE_PATH = (
    ROOT
    / "data/derived/covalent_small"
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1"
    / "covapie_call_site_decision_in_memory_issue_readiness_inventory.csv"
)
ISSUE_SHA256 = "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
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

R_RESULT_TYPE_INVALID = "ACTION_PERMISSION_BRIDGE_RESULT_TYPE_INVALID"
R_DECISION_TYPE_INVALID = (
    "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_TYPE_INVALID"
)
R_STAGE_INVARIANT_INVALID = (
    "ACTION_PERMISSION_BRIDGE_STAGE_RESULT_INVARIANT_INVALID"
)
R_DECISION_INVARIANT_INVALID = (
    "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_INVARIANT_INVALID"
)
R_SCOPE_INVALID = "ACTION_PERMISSION_BRIDGE_STAGE_SCOPE_INVALID"
R_IO_INVALID = "ACTION_PERMISSION_BRIDGE_STAGE_IO_INVARIANT_INVALID"
R_ALREADY_TRANSITIONED = "ACTION_PERMISSION_BRIDGE_SOURCE_ALREADY_TRANSITIONED"
R_LINEAGE_MISMATCH = "ACTION_PERMISSION_BRIDGE_SOURCE_LINEAGE_MISMATCH"
R_CANDIDATE_INVALID = "ACTION_PERMISSION_BRIDGE_CANDIDATE_VERDICT_INVALID"
R_ADMIT_014_BLOCKED = "ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED"
R_CANDIDATE_BLOCKED = "ACTION_PERMISSION_BRIDGE_CANDIDATE_VERDICT_BLOCKED"
R_NOT_PERMISSION_PENDING = (
    "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_NOT_PERMISSION_PENDING"
)
R_TRANSITION_ELIGIBLE = "ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE"
INDEPENDENT_REASON_VOCABULARY = (
    R_RESULT_TYPE_INVALID,
    R_DECISION_TYPE_INVALID,
    R_STAGE_INVARIANT_INVALID,
    R_DECISION_INVARIANT_INVALID,
    R_SCOPE_INVALID,
    R_IO_INVALID,
    R_ALREADY_TRANSITIONED,
    R_LINEAGE_MISMATCH,
    R_CANDIDATE_INVALID,
    R_ADMIT_014_BLOCKED,
    R_CANDIDATE_BLOCKED,
    R_NOT_PERMISSION_PENDING,
    R_TRANSITION_ELIGIBLE,
)


@dataclass(frozen=True)
class ExpectedBridgeDecisionProjection:
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


EXACT19_FIELDS = tuple(field.name for field in fields(ExpectedBridgeDecisionProjection))
TRUTH_COLUMNS = (
    "case_id",
    "case_group",
    "mutation_or_positive_probe",
    *tuple(
        column
        for field_name in EXACT19_FIELDS
        for column in (
            f"expected_{field_name}",
            f"observed_{field_name}",
        )
    ),
    "exact_decision_type_verified",
    "verified",
)
INVARIANT_COLUMNS = (
    "invariant_area",
    "invariant_item",
    "evidence_case_id",
    "mutation_or_positive_probe",
    "expected_outcome",
    "expected_reason",
    "observed_outcome",
    "observed_reason",
    "expected_projection",
    "observed_projection",
    "verified",
)
PUBLIC_COLUMNS = ("contract_area", "contract_item", "expected", "observed", "verified")
SAFETY_COLUMNS = ("safety_area", "expected", "observed", "evidence", "verified")


class _ResultSubclass(contract.StageAdmissionOrchestrationResult):
    pass


class _DecisionSubclass(
    call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
):
    pass


class _TupleSubclass(tuple):
    pass


def _profile():
    profiles = fixture_runtime.build_canonical_in_memory_fixture_profiles()
    assert type(profiles) is tuple
    return profiles[0]


def _source_pair(*, authorized: bool, batch_context=None, candidate_inputs=None):
    profile = _profile()
    authorization = dict(profile.stage_authorization_context)
    authorization["current_stage_download_authorized"] = authorized
    authorization["current_stage_training_authorized"] = (
        profile.stage_authorization_context["current_stage_training_authorized"]
    )
    result = orchestration_runtime.orchestrate_stage_admission_scope(
        design.DOWNLOAD_SCOPE_ID,
        profile.candidate_inputs if candidate_inputs is None else candidate_inputs,
        batch_context=profile.batch_context if batch_context is None else batch_context,
        stage_authorization_context=authorization,
    )
    decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
        orchestration_result=result,
        orchestration_error=None,
    )
    return result, decision


def _wrong_scope_pair():
    profile = _profile()
    result = orchestration_runtime.orchestrate_stage_admission_scope(
        "post_download_acceptance_permission",
        profile.candidate_inputs,
        batch_context=profile.batch_context,
        stage_authorization_context=profile.stage_authorization_context,
    )
    decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
        orchestration_result=result,
        orchestration_error=None,
    )
    return result, decision


def _invalid_candidate_pair(*, authorized=True):
    profile = _profile()
    candidate = profile.candidate_inputs[0]
    record = dict(candidate.candidate_record)
    record["pdb_id"] = "BAD"
    return _source_pair(
        authorized=authorized,
        candidate_inputs=(replace(candidate, candidate_record=record),),
    )


def _other_blocked_pair():
    profile = _profile()
    batch = dict(profile.batch_context)
    batch["batch_candidate_record_ids"] = ("REC_NOT_PRESENT",)
    return _source_pair(authorized=True, batch_context=batch)


def _forge(value, updates=None, *, reverse_storage=False):
    updates = {} if updates is None else updates
    forged = object.__new__(type(value))
    items = list(vars(value).items())
    if reverse_storage:
        items.reverse()
    for name, original in items:
        object.__setattr__(forged, name, updates.get(name, original))
    return forged


def _classify(result, decision):
    return design.classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design(
        orchestration_result=result,
        call_site_decision=decision,
    )


def _source_evidence(result):
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
    admit_014 = next(
        item.outcome
        for item in result.stage_global_rule_evaluations
        if item.admission_rule_id == "ADMIT_014"
    )
    return outcomes, invalid, blocked, failing, admit_014


def _expected_projection(
    *,
    outcome,
    reason,
    result=None,
    decision=None,
    evidence_level="empty",
    source_lineage_verified=False,
):
    source_scope_id = ""
    candidate_count = 0
    admit_014_outcome = ""
    candidate_combined_outcomes = ()
    call_site_decision_outcome = ""
    call_site_decision_reason = ""
    invalid = ()
    blocked = ()
    failing = ()
    if evidence_level != "empty":
        (
            candidate_combined_outcomes,
            source_invalid,
            source_blocked,
            source_failing,
            admit_014_outcome,
        ) = _source_evidence(result)
        source_scope_id = result.scope_id
        candidate_count = result.candidate_count
        call_site_decision_outcome = decision.outcome
        call_site_decision_reason = decision.reason
        if evidence_level == "diagnostic":
            invalid = source_invalid
            blocked = source_blocked
            failing = source_failing
    return ExpectedBridgeDecisionProjection(
        schema_version=(
            "covapie_bulk_download_stage_orchestration_"
            "action_permission_bridge_decision_v1"
        ),
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
        invalid_candidate_indexes=invalid,
        blocked_candidate_indexes=blocked,
        failing_candidate_indexes=failing,
        source_lineage_verified=source_lineage_verified,
        transition_eligible=outcome == "eligible",
        action_permission_granted=False,
        download_action_invoked=False,
        bridge_io_used=False,
    )


def _canonical_field(value):
    if type(value) in (str, int, bool):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if type(value) is tuple:
        return json.dumps(list(value), ensure_ascii=True, separators=(",", ":"))
    return json.dumps(
        {"invalid_exact_type": type(value).__name__},
        sort_keys=True,
        separators=(",", ":"),
    )


def _exact19_verified(expected, observed):
    if (
        type(expected) is not ExpectedBridgeDecisionProjection
        or type(observed)
        is not design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        or type(vars(observed)) is not dict
        or tuple(vars(observed)) != design.DECISION_FIELDS
        or tuple(observed.__dataclass_fields__) != design.DECISION_FIELDS
        or EXACT19_FIELDS != design.DECISION_FIELDS
    ):
        return False
    for field_name in EXACT19_FIELDS:
        expected_value = getattr(expected, field_name)
        observed_value = getattr(observed, field_name)
        if (
            type(expected_value) is not type(observed_value)
            or expected_value != observed_value
        ):
            return False
    tuple_types = (
        ("candidate_combined_outcomes", str),
        ("invalid_candidate_indexes", int),
        ("blocked_candidate_indexes", int),
        ("failing_candidate_indexes", int),
    )
    if any(
        type(getattr(observed, field_name)) is not tuple
        or any(
            type(item) is not element_type
            for item in getattr(observed, field_name)
        )
        for field_name, element_type in tuple_types
    ):
        return False
    return (
        observed.action_permission_granted is False
        and observed.download_action_invoked is False
        and observed.bridge_io_used is False
    )


def _truth_row(
    case_id,
    group,
    probe,
    expected,
    result,
    decision,
    *,
    observed_override=None,
):
    observed = (
        _classify(result, decision)
        if observed_override is None
        else observed_override
    )
    exact_type_verified = (
        type(observed)
        is design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
    )
    verified = _exact19_verified(expected, observed)
    row = {
        "case_id": case_id,
        "case_group": group,
        "mutation_or_positive_probe": probe,
        "exact_decision_type_verified": str(exact_type_verified).lower(),
        "verified": str(verified).lower(),
    }
    for field_name in EXACT19_FIELDS:
        row[f"expected_{field_name}"] = _canonical_field(
            getattr(expected, field_name)
        )
        row[f"observed_{field_name}"] = _canonical_field(
            getattr(observed, field_name, None)
        )
    return row


def build_truth_rows():
    current_result, current_decision = _source_pair(authorized=False)
    eligible_result, eligible_decision = _source_pair(authorized=True)
    wrong_scope_result, wrong_scope_decision = _wrong_scope_pair()
    invalid_result, invalid_decision = _invalid_candidate_pair()
    invalid_with_admit_blocked_result, invalid_with_admit_blocked_decision = (
        _invalid_candidate_pair(authorized=False)
    )
    other_blocked_result, other_blocked_decision = _other_blocked_pair()
    profile = _profile()
    blocked_batch = dict(profile.batch_context)
    blocked_batch["batch_candidate_record_ids"] = ("REC_NOT_PRESENT",)
    other_with_admit_blocked_result, other_with_admit_blocked_decision = (
        _source_pair(authorized=False, batch_context=blocked_batch)
    )
    rows = []

    def add(case_id, group, probe, outcome, reason, result, decision):
        independent_reasons = {
            R_RESULT_TYPE_INVALID: R_RESULT_TYPE_INVALID,
            R_DECISION_TYPE_INVALID: R_DECISION_TYPE_INVALID,
            R_STAGE_INVARIANT_INVALID: R_STAGE_INVARIANT_INVALID,
            R_DECISION_INVARIANT_INVALID: R_DECISION_INVARIANT_INVALID,
            R_SCOPE_INVALID: R_SCOPE_INVALID,
            R_IO_INVALID: R_IO_INVALID,
            R_ALREADY_TRANSITIONED: R_ALREADY_TRANSITIONED,
            R_LINEAGE_MISMATCH: R_LINEAGE_MISMATCH,
            R_CANDIDATE_INVALID: R_CANDIDATE_INVALID,
            R_ADMIT_014_BLOCKED: R_ADMIT_014_BLOCKED,
            R_CANDIDATE_BLOCKED: R_CANDIDATE_BLOCKED,
            R_NOT_PERMISSION_PENDING: R_NOT_PERMISSION_PENDING,
            R_TRANSITION_ELIGIBLE: R_TRANSITION_ELIGIBLE,
        }
        independent_reason = independent_reasons[reason]
        if independent_reason in (
            R_RESULT_TYPE_INVALID,
            R_DECISION_TYPE_INVALID,
            R_STAGE_INVARIANT_INVALID,
            R_DECISION_INVARIANT_INVALID,
        ):
            evidence_level = "empty"
        elif independent_reason in (
            R_SCOPE_INVALID,
            R_IO_INVALID,
            R_ALREADY_TRANSITIONED,
        ):
            evidence_level = "source"
        else:
            evidence_level = "diagnostic"
        lineage_verified = independent_reason in (
            R_CANDIDATE_INVALID,
            R_ADMIT_014_BLOCKED,
            R_CANDIDATE_BLOCKED,
            R_TRANSITION_ELIGIBLE,
        )
        expected = _expected_projection(
            outcome=outcome,
            reason=independent_reason,
            result=result,
            decision=decision,
            evidence_level=evidence_level,
            source_lineage_verified=lineage_verified,
        )
        rows.append(
            _truth_row(
                case_id,
                group,
                probe,
                expected,
                result,
                decision,
            )
        )

    add("TYPE_RESULT_WRONG", "type", "object instead of exact StageResult", "invalid", R_RESULT_TYPE_INVALID, object(), current_decision)
    add("TYPE_RESULT_SUBCLASS", "type", "StageResult subclass rejected", "invalid", R_RESULT_TYPE_INVALID, _ResultSubclass(**vars(current_result)), current_decision)
    add("TYPE_DECISION_WRONG", "type", "object instead of shared Exact15 decision", "invalid", R_DECISION_TYPE_INVALID, current_result, object())
    add("TYPE_DECISION_SUBCLASS", "type", "Exact15 decision subclass rejected", "invalid", R_DECISION_TYPE_INVALID, current_result, _DecisionSubclass(**vars(current_decision)))

    stage_mutations = (
        ("STAGE_SCHEMA", {"schema_version": "wrong"}, False, "schema mutation"),
        ("STAGE_STORAGE", {}, True, "reversed Exact12 storage"),
        ("STAGE_TUPLE_SUBCLASS", {"required_rule_ids": _TupleSubclass(current_result.required_rule_ids)}, False, "tuple subclass"),
        ("STAGE_COUNT", {"candidate_count": 2}, False, "candidate count mismatch"),
        ("STAGE_MEMBERSHIP", {"required_rule_ids": tuple(reversed(current_result.required_rule_ids))}, False, "rule membership/order"),
        ("STAGE_CARDINALITY", {"dispatcher_call_count": 0}, False, "dispatcher cardinality"),
    )
    for case_id, updates, reverse_storage, probe in stage_mutations:
        add(case_id, "stage_result_invariant", probe, "invalid", R_STAGE_INVARIANT_INVALID, _forge(current_result, updates, reverse_storage=reverse_storage), current_decision)
    candidate = current_result.candidate_results[0]
    stage_clone = _forge(current_result.stage_global_rule_evaluations[0])
    stage_position = current_result.required_rule_ids.index("ADMIT_014")
    vector = list(candidate.ordered_rule_evaluations)
    vector[stage_position] = stage_clone
    add("STAGE_IDENTITY", "stage_result_invariant", "stage-global identity clone", "invalid", R_STAGE_INVARIANT_INVALID, _forge(current_result, {"candidate_results": (_forge(candidate, {"ordered_rule_evaluations": tuple(vector)}),)}), current_decision)
    normal_position = next(index for index, item in enumerate(candidate.ordered_rule_evaluations) if item.admission_rule_id != "ADMIT_014")
    vector = list(candidate.ordered_rule_evaluations)
    vector[normal_position] = _forge(vector[normal_position])
    add("RETAINED_IDENTITY", "stage_result_invariant", "retained-vector identity clone", "invalid", R_STAGE_INVARIANT_INVALID, _forge(current_result, {"candidate_results": (_forge(candidate, {"ordered_rule_evaluations": tuple(vector)}),)}), current_decision)
    corrupt_unified = _forge(current_result.stage_global_rule_evaluations[0], {"outcome": "corrupt"})
    add("UNIFIED_CORRUPT", "stage_result_invariant", "corrupted Unified result", "invalid", R_STAGE_INVARIANT_INVALID, _forge(current_result, {"stage_global_rule_evaluations": (corrupt_unified,)}), current_decision)
    corrupt_combined = _forge(candidate.combined_verdict, {"outcome": "corrupt"})
    add("COMBINED_CORRUPT", "stage_result_invariant", "corrupted Combined verdict", "invalid", R_STAGE_INVARIANT_INVALID, _forge(current_result, {"candidate_results": (_forge(candidate, {"combined_verdict": corrupt_combined}),)}), current_decision)

    decision_mutations = (
        ("DECISION_SCHEMA", {"schema_version": "wrong"}, False, "schema"),
        ("DECISION_STORAGE", {}, True, "reversed Exact15 storage"),
        ("DECISION_SOURCE_KIND", {"source_kind": "invalid_input"}, False, "wrong source kind"),
        ("DECISION_SCOPE_UNKNOWN", {"source_scope_id": "__wrong__"}, False, "unknown source scope"),
        ("DECISION_DIAGNOSTICS", {"blocked_candidate_indexes": (0, 0)}, False, "duplicate diagnostics"),
        ("DECISION_FAILING", {"failing_candidate_indexes": ()}, False, "failing union mismatch"),
        ("DECISION_PERMISSION_TYPE", {"action_permission_granted": 0}, False, "action permission exact bool"),
        ("DECISION_DOWNLOAD_ACTION", {"download_action_invoked": True}, False, "download action nonzero"),
        ("DECISION_IO", {"call_site_io_used": True}, False, "call-site I/O nonzero"),
    )
    for case_id, updates, reverse_storage, probe in decision_mutations:
        add(case_id, "decision_invariant", probe, "invalid", R_DECISION_INVARIANT_INVALID, current_result, _forge(current_decision, updates, reverse_storage=reverse_storage))

    add("WRONG_SCOPE", "scope_io_transition", "valid non-download scope pair", "invalid", R_SCOPE_INVALID, wrong_scope_result, wrong_scope_decision)
    io_result = replace(eligible_result, orchestration_io_used=True)
    io_decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(orchestration_result=io_result, orchestration_error=None)
    add("ORCHESTRATION_IO", "scope_io_transition", "source orchestration I/O true", "invalid", R_IO_INVALID, io_result, io_decision)
    transitioned_result = replace(eligible_result, action_permission_granted=True)
    transitioned_decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(orchestration_result=transitioned_result, orchestration_error=None)
    add("SOURCE_TRANSITIONED", "scope_io_transition", "source permission already true", "invalid", R_ALREADY_TRANSITIONED, transitioned_result, transitioned_decision)

    add("LINEAGE_CURRENT_VALID", "lineage", "actual current blocked source pair", "blocked", R_ADMIT_014_BLOCKED, current_result, current_decision)
    add("LINEAGE_ELIGIBLE_VALID", "lineage", "actual future eligible source pair", "eligible", R_TRANSITION_ELIGIBLE, eligible_result, eligible_decision)
    lineage_mutations = (
        ("LINEAGE_COUNT", {"candidate_count": 2}, "wrong candidate count"),
        ("LINEAGE_SCOPE", {"source_scope_id": "post_download_acceptance_permission"}, "wrong valid source scope"),
        ("LINEAGE_DIAGNOSTIC", {"blocked_candidate_indexes": (), "failing_candidate_indexes": ()}, "wrong diagnostics"),
        ("LINEAGE_OUTCOME", {"outcome": "invalid", "passed": False, "blocks_download": True, "reason": "BULK_DOWNLOAD_CANDIDATE_VERDICT_INVALID"}, "wrong outcome"),
        ("LINEAGE_REASON", {"reason": "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"}, "wrong reason"),
    )
    for case_id, updates, probe in lineage_mutations:
        add(case_id, "lineage", probe, "invalid", R_LINEAGE_MISMATCH, current_result, replace(current_decision, **updates))
    add("LINEAGE_UNRELATED", "lineage", "unrelated partially similar valid decision", "invalid", R_LINEAGE_MISMATCH, current_result, wrong_scope_decision)

    add("CANDIDATE_INVALID", "candidate_authority", "actual invalid candidate with ADMIT_014 passed", "invalid", R_CANDIDATE_INVALID, invalid_result, invalid_decision)
    add("ADMIT_014_BLOCKED", "candidate_authority", "actual current ADMIT_014 blocked", "blocked", R_ADMIT_014_BLOCKED, current_result, current_decision)
    add("OTHER_CANDIDATE_BLOCKED", "candidate_authority", "actual ADMIT_001 blocked with ADMIT_014 passed", "blocked", R_CANDIDATE_BLOCKED, other_blocked_result, other_blocked_decision)
    nonpending_decision = replace(
        eligible_decision,
        outcome="authorized",
        passed=True,
        blocks_download=False,
        reason="",
    )
    add("DECISION_NOT_PENDING", "candidate_authority", "structurally valid authorized decision rejected by exact lineage", "invalid", R_LINEAGE_MISMATCH, eligible_result, nonpending_decision)
    add("FULLY_ELIGIBLE", "candidate_authority", "actual all-passed permission-pending pair", "eligible", R_TRANSITION_ELIGIBLE, eligible_result, eligible_decision)

    add("PRECEDENCE_STAGE_OVER_SCOPE", "precedence", "invalid stage plus wrong scope semantics", "invalid", R_STAGE_INVARIANT_INVALID, _forge(wrong_scope_result, {"schema_version": "wrong"}), wrong_scope_decision)
    add("PRECEDENCE_DECISION_OVER_SCOPE", "precedence", "invalid decision plus wrong scope result", "invalid", R_DECISION_INVARIANT_INVALID, wrong_scope_result, _forge(wrong_scope_decision, {"schema_version": "wrong"}))
    add("PRECEDENCE_SCOPE_OVER_IO", "precedence", "wrong scope plus source I/O", "invalid", R_SCOPE_INVALID, replace(wrong_scope_result, orchestration_io_used=True), wrong_scope_decision)
    add("PRECEDENCE_IO_OVER_TRANSITION", "precedence", "I/O plus transitioned", "invalid", R_IO_INVALID, replace(eligible_result, orchestration_io_used=True, action_permission_granted=True), eligible_decision)
    add("PRECEDENCE_TRANSITION_OVER_LINEAGE", "precedence", "transitioned plus unrelated decision", "invalid", R_ALREADY_TRANSITIONED, transitioned_result, wrong_scope_decision)
    add("PRECEDENCE_LINEAGE_OVER_BUSINESS", "precedence", "lineage mismatch before ADMIT authority", "invalid", R_LINEAGE_MISMATCH, current_result, replace(current_decision, candidate_count=2))
    add("PRECEDENCE_INVALID_OVER_ADMIT", "precedence", "invalid candidate precedes blocked ADMIT_014", "invalid", R_CANDIDATE_INVALID, invalid_with_admit_blocked_result, invalid_with_admit_blocked_decision)
    add("PRECEDENCE_ADMIT_OVER_BLOCKED", "precedence", "blocked ADMIT_014 precedes other candidate block", "blocked", R_ADMIT_014_BLOCKED, other_with_admit_blocked_result, other_with_admit_blocked_decision)
    add("PRECEDENCE_BLOCKED_OVER_ELIGIBLE", "precedence", "other candidate block precedes eligibility", "blocked", R_CANDIDATE_BLOCKED, other_blocked_result, other_blocked_decision)
    add("PRECEDENCE_NOT_PENDING_OVER_ELIGIBLE", "precedence", "nonpending decision is lineage mismatch before eligibility", "invalid", R_LINEAGE_MISMATCH, eligible_result, nonpending_decision)
    add("PRECEDENCE_ELIGIBLE", "precedence", "terminal eligible classification", "eligible", R_TRANSITION_ELIGIBLE, eligible_result, eligible_decision)
    assert all(row["verified"] == "true" for row in rows)
    return tuple(rows)


def build_public_rows():
    function = design.classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    annotation_projection = "|".join(
        (
            hints["orchestration_result"].__name__,
            hints["call_site_decision"].__name__,
            hints["return"].__name__,
        )
    )
    source = (ROOT / EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    predecessor_private_calls = tuple(
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "call_site_contract"
            and node.func.attr.startswith("_")
        )
    )
    observations = (
        ("api", "public_function_name", "classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design", function.__name__),
        ("api", "exact_parameter_order", "orchestration_result|call_site_decision", "|".join(signature.parameters)),
        ("api", "exact_annotations", "StageAdmissionOrchestrationResult|BulkDownloadStageOrchestrationCallSiteDecisionDesign|BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign", annotation_projection),
        ("api", "required_keyword_only", "true", str(all(item.kind is inspect.Parameter.KEYWORD_ONLY and item.default is inspect.Parameter.empty for item in signature.parameters.values())).lower()),
        ("api", "no_injection_parameters", "true", str(not any(token in name for name in signature.parameters for token in ("callable", "dispatcher", "aggregator", "orchestrator", "filesystem", "network", "provider"))).lower()),
        ("api", "future_runtime_absent", "true", str(not hasattr(design, "evaluate_bulk_download_stage_orchestration_action_permission_bridge")).lower()),
        ("decision", "exact_field_count", "19", str(len(fields(design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign)))),
        ("decision", "exact_field_order", "|".join(design.DECISION_FIELDS), "|".join(item.name for item in fields(design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign))),
        ("decision", "outcome_vocabulary", "eligible|blocked|invalid", "|".join(design.OUTCOME_VOCABULARY)),
        ("decision", "reason_vocabulary_count", "13", str(len(design.REASON_VOCABULARY))),
        ("lineage", "exact_source_lineage_semantics", "true", str("coherent_nonpending_projection" not in source and "exact_semantic_projection or" not in source).lower()),
        ("lineage", "authorized_decision_lineage_exception_removed", "true", str("coherent_nonpending_projection" not in source).lower()),
        ("reason", "call_site_decision_not_permission_pending_reason_reserved", "true", str(design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_REASON_RESERVED).lower()),
        ("reason", "call_site_decision_not_permission_pending_branch_reachable", "false", str(design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_BRANCH_REACHABLE).lower()),
        ("dependency", "predecessor_private_helper_called", "false", str(bool(predecessor_private_calls)).lower()),
        ("evidence", "full_exact19_truth_schema", "true", str(all(f"expected_{name}" in TRUTH_COLUMNS and f"observed_{name}" in TRUTH_COLUMNS for name in EXACT19_FIELDS)).lower()),
        ("boundary", "transition_eligible_not_permission", "true", "transition_eligible" in source and "action_permission_granted=False" in source),
        ("boundary", "zero_download", "true", "download_action_invoked=False" in source),
        ("boundary", "zero_bridge_io", "true", "bridge_io_used=False" in source),
    )
    return tuple(
        {
            "contract_area": area,
            "contract_item": item,
            "expected": expected,
            "observed": str(observed).lower() if type(observed) is bool else observed,
            "verified": str(expected == (str(observed).lower() if type(observed) is bool else observed)).lower(),
        }
        for area, item, expected, observed in observations
    )


def build_invariant_rows(truth_rows):
    truth = {row["case_id"]: row for row in truth_rows}
    links = (
        ("stage_result", "exact type", "TYPE_RESULT_SUBCLASS"),
        ("stage_result", "Exact12/schema/membership/cardinality", "STAGE_SCHEMA"),
        ("stage_result", "stage-global identity", "STAGE_IDENTITY"),
        ("stage_result", "normal retained-vector identity", "RETAINED_IDENTITY"),
        ("stage_result", "Unified validator", "UNIFIED_CORRUPT"),
        ("stage_result", "Combined validator", "COMBINED_CORRUPT"),
        ("call_site_decision", "exact shared type", "TYPE_DECISION_SUBCLASS"),
        ("call_site_decision", "Exact15/schema/reconstructability", "DECISION_SCHEMA"),
        ("call_site_decision", "diagnostics and failing union", "DECISION_FAILING"),
        ("scope", "download scope only", "WRONG_SCOPE"),
        ("io", "orchestration I/O false", "ORCHESTRATION_IO"),
        ("pre_transition", "source permission false", "SOURCE_TRANSITIONED"),
        ("lineage", "current blocked exact projection", "LINEAGE_CURRENT_VALID"),
        ("lineage", "eligible exact projection", "LINEAGE_ELIGIBLE_VALID"),
        ("lineage", "wrong source projection rejected", "LINEAGE_UNRELATED"),
        ("candidate_diagnostics", "invalid indexes", "CANDIDATE_INVALID"),
        ("candidate_diagnostics", "blocked/failing indexes", "ADMIT_014_BLOCKED"),
        ("authority", "ADMIT_014 authority", "ADMIT_014_BLOCKED"),
        ("candidate_blocker", "other candidate blocker", "OTHER_CANDIDATE_BLOCKED"),
        ("permission_pending", "all passed pending decision", "FULLY_ELIGIBLE"),
        ("eligible_transition", "eligible but permission false", "FULLY_ELIGIBLE"),
        ("zero_action", "download action remains false", "FULLY_ELIGIBLE"),
        ("zero_io", "bridge I/O remains false", "FULLY_ELIGIBLE"),
    )
    rows = []
    for area, item, case_id in links:
        evidence = truth[case_id]
        expected_projection = json.dumps(
            {
                field_name: json.loads(evidence[f"expected_{field_name}"])
                for field_name in EXACT19_FIELDS
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        observed_projection = json.dumps(
            {
                field_name: json.loads(evidence[f"observed_{field_name}"])
                for field_name in EXACT19_FIELDS
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            {
                "invariant_area": area,
                "invariant_item": item,
                "evidence_case_id": case_id,
                "mutation_or_positive_probe": evidence["mutation_or_positive_probe"],
                "expected_outcome": json.loads(evidence["expected_outcome"]),
                "expected_reason": json.loads(evidence["expected_reason"]),
                "observed_outcome": json.loads(evidence["observed_outcome"]),
                "observed_reason": json.loads(evidence["observed_reason"]),
                "expected_projection": expected_projection,
                "observed_projection": observed_projection,
                "verified": str(expected_projection == observed_projection).lower(),
            }
        )
    return tuple(rows)


def build_safety_rows(truth_rows):
    source = (ROOT / EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    forbidden_imports = {"requests", "urllib", "socket", "subprocess", "pathlib", "shutil", "os", "torch"}
    scan_clean = not imports.intersection(forbidden_imports) and "open" not in calls
    eligible = next(row for row in truth_rows if row["case_id"] == "FULLY_ELIGIBLE")
    areas = (
        "network", "provider", "download_callable", "download_io", "raw",
        "torch", "model", "checkpoint", "dataloader", "forward", "loss",
        "backward", "optimizer", "scheduler", "parameter_update",
        "checkpoint_write", "training", "current_permission",
        "action_permission", "download_action", "bridge_io",
        "ready_for_download", "ready_for_training",
    )
    rows = []
    for area in areas:
        evidence = "AST/source scan; public signature; truth cases; zero-action invariants"
        observed = "false"
        if area in ("action_permission", "download_action", "bridge_io"):
            key = {
                "action_permission": "action_permission_granted",
                "download_action": "download_action_invoked",
                "bridge_io": "bridge_io_used",
            }[area]
            observed = str(
                json.loads(eligible[f"observed_{key}"])
            ).lower()
        rows.append(
            {
                "safety_area": area,
                "expected": "false",
                "observed": observed,
                "evidence": evidence,
                "verified": str(scan_clean and observed == "false").lower(),
            }
        )
    return tuple(rows)


def _csv_bytes(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def expected_evidence_bytes():
    truth = build_truth_rows()
    return {
        OUTPUT_NAMES[0]: _csv_bytes(PUBLIC_COLUMNS, build_public_rows()),
        OUTPUT_NAMES[1]: _csv_bytes(TRUTH_COLUMNS, truth),
        OUTPUT_NAMES[2]: _csv_bytes(INVARIANT_COLUMNS, build_invariant_rows(truth)),
        OUTPUT_NAMES[3]: _csv_bytes(SAFETY_COLUMNS, build_safety_rows(truth)),
        OUTPUT_NAMES[4]: PREDECESSOR_ISSUE_PATH.read_bytes(),
    }


def check():
    assert design.BASE_COMMIT == "f24bc241b1a492a514ed44649d57220a68c3ae6d"
    assert INDEPENDENT_REASON_VOCABULARY == design.REASON_VOCABULARY
    assert len(EXACT10) == 10 and len(set(EXACT10)) == 10
    assert all((ROOT / path).is_file() and not (ROOT / path).is_symlink() for path in EXACT10)
    assert hashlib.sha256(PREDECESSOR_ISSUE_PATH.read_bytes()).hexdigest() == ISSUE_SHA256
    truth = build_truth_rows()
    assert len({row["case_id"] for row in truth}) == len(truth)
    assert all(row["verified"] == "true" for row in truth)
    assert all(
        row["exact_decision_type_verified"] == "true"
        for row in truth
    )
    assert {row["case_group"] for row in truth} == {
        "type", "stage_result_invariant", "decision_invariant",
        "scope_io_transition", "lineage", "candidate_authority", "precedence",
    }
    current = next(row for row in truth if row["case_id"] == "LINEAGE_CURRENT_VALID")
    eligible = next(row for row in truth if row["case_id"] == "FULLY_ELIGIBLE")
    assert json.loads(current["observed_outcome"]) == "blocked"
    assert json.loads(eligible["observed_outcome"]) == "eligible"
    assert json.loads(eligible["observed_transition_eligible"]) is True
    assert all(
        json.loads(row["observed_action_permission_granted"]) is False
        for row in truth
    )
    assert all(
        json.loads(row["observed_download_action_invoked"]) is False
        for row in truth
    )
    assert all(
        json.loads(row["observed_bridge_io_used"]) is False
        for row in truth
    )
    for case_id in (
        "DECISION_NOT_PENDING",
        "PRECEDENCE_NOT_PENDING_OVER_ELIGIBLE",
    ):
        row = next(item for item in truth if item["case_id"] == case_id)
        assert json.loads(row["observed_outcome"]) == "invalid"
        assert json.loads(row["observed_reason"]) == R_LINEAGE_MISMATCH
        assert json.loads(row["observed_source_lineage_verified"]) is False
        assert json.loads(row["observed_transition_eligible"]) is False
    public = build_public_rows()
    invariants = build_invariant_rows(truth)
    safety = build_safety_rows(truth)
    assert all(row["verified"] == "true" for row in public)
    assert all(row["verified"] == "true" for row in invariants)
    assert all(row["verified"] == "true" for row in safety)
    assert all(
        row["expected_projection"] == row["observed_projection"]
        and tuple(
            json.loads(row["expected_projection"])
        ) == tuple(sorted(EXACT19_FIELDS))
        for row in invariants
    )
    design_tree = ast.parse((ROOT / EXACT10[0]).read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "call_site_contract"
        and node.func.attr.startswith("_")
        for node in ast.walk(design_tree)
    )
    expected = expected_evidence_bytes()
    for name, content in expected.items():
        assert (ROOT / OUTPUT_ROOT / name).read_bytes() == content
    manifest_path = ROOT / EXACT10[-1]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert (
        hashlib.sha256((ROOT / EXACT10[0]).read_bytes()).hexdigest()
        == manifest["design_source_sha256"]
    )
    assert manifest["truth_row_count"] == len(truth)
    assert manifest["truth_group_count"] == len({row["case_group"] for row in truth})
    assert manifest["source_lineage_invariant_row_count"] == len(invariants)
    assert manifest["public_contract_row_count"] == len(public)
    assert manifest["safety_row_count"] == len(safety)
    assert manifest["issue_inventory_data_row_count"] == 30
    assert tuple(manifest["effective_open_issues"]) == EFFECTIVE_OPEN_ISSUES
    assert tuple((item["semantic_name"], item["alias"]) for item in manifest["canonical_masks"]) == CANONICAL_MASKS
    for name, digest in manifest["evidence_sha256"].items():
        assert hashlib.sha256((ROOT / OUTPUT_ROOT / name).read_bytes()).hexdigest() == digest
    required_true = (
        "action_permission_bridge_contract_frozen",
        "action_permission_bridge_classifier_design_available",
        "current_blocked_path_verified",
        "future_eligible_path_verified",
        "transition_eligible_branch_reachable",
        "transition_eligible_is_not_action_permission",
        "source_lineage_validation_frozen",
        "admit_014_authority_semantics_frozen",
        "candidate_invalid_precedes_admit_014_blocked",
        "admit_014_blocked_precedes_other_candidate_blocked",
        "future_action_permission_bridge_required",
        "feature_semantics_audit_required_before_training",
        "exact_source_lineage_semantics_frozen",
        "authorized_decision_lineage_exception_removed",
        "full_exact19_truth_projection_verified",
        "full_exact19_invariant_projection_verified",
        "call_site_decision_not_permission_pending_reason_reserved",
    )
    required_false = (
        "action_permission_bridge_runtime_implemented",
        "action_permission_granted",
        "current_authorized_branch_reachable",
        "future_action_permission_bridge_implemented",
        "network_used", "provider_used", "download_used",
        "current_permission", "ready_for_download",
        "feature_semantics_audit_completed", "feature_semantics_known",
        "ready_for_training",
        "predecessor_private_helper_called",
        "call_site_decision_not_permission_pending_branch_reachable",
    )
    assert all(manifest[name] is True for name in required_true)
    assert all(manifest[name] is False for name in required_false)
    assert manifest["download_action_count"] == 0
    assert manifest["bridge_io_count"] == 0
    return {
        "action_permission_granted_count": 0,
        "admit_014_authority": True,
        "bridge_io_count": 0,
        "current_blocked_path": True,
        "download_action_count": 0,
        "future_eligible_path": True,
        "ready_for_download": False,
        "ready_for_training": False,
        "exact_lineage": True,
        "authorized_lineage_exception_removed": True,
        "full_exact19_truth": True,
        "full_exact19_invariant": True,
        "predecessor_private_helper_called": False,
        "reason_11_branch_reachable": False,
        "source_lineage": True,
        "transition_eligible_count": sum(
            json.loads(row["observed_transition_eligible"]) is True
            for row in truth
        ),
        "truth_group_count": len({row["case_group"] for row in truth}),
        "truth_row_count": len(truth),
    }


def main():
    print(json.dumps(check(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
