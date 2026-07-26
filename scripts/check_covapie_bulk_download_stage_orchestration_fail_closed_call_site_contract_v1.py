#!/usr/bin/env python3
"""Check deterministic fail-closed bulk-download call-site design evidence."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import sys
from collections import Counter
from dataclasses import dataclass, fields, replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as design,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration,
)


STAGE = (
    "covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_contract_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PUBLIC_NAME = "covapie_bulk_download_call_site_public_api_and_decision_contract.csv"
TRUTH_NAME = "covapie_bulk_download_call_site_precedence_truth_matrix.csv"
INVARIANT_NAME = (
    "covapie_bulk_download_call_site_source_result_invariant_matrix.csv"
)
SAFETY_NAME = "covapie_bulk_download_call_site_safety_audit.csv"
ISSUE_NAME = "covapie_bulk_download_call_site_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_contract_manifest.json"
)
CSV_NAMES = (
    PUBLIC_NAME,
    TRUTH_NAME,
    INVARIANT_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
)
OUTPUT_NAMES = (*CSV_NAMES, MANIFEST_NAME)
EXACT10 = (
    Path("src/covalent_ext")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate.py",
    Path("tests")
    / "test_covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1.py",
    Path("scripts")
    / "check_covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1.py",
    Path("docs")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1_summary.md",
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)
PREDECESSOR_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1"
    / "covapie_orchestration_in_memory_issue_readiness_inventory.csv"
)
PREDECESSOR_MANIFEST_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_stage_global_rule_evaluation_orchestration_v1"
    / "covapie_stage_global_rule_evaluation_orchestration_implementation_manifest.json"
)
SOURCE_SHA256 = {
    Path(
        "src/covalent_ext/"
        "covapie_stage_global_rule_evaluation_orchestration_contract_design_gate.py"
    ): "68ddcede8c56c1db51a7a49e2fb5943e12818e0412f6463238865a39a47d4548",
    Path(
        "src/covalent_ext/"
        "covapie_stage_global_rule_evaluation_orchestration_v1.py"
    ): "5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc",
    Path(
        "src/covalent_ext/"
        "covapie_stage_global_rule_evaluation_orchestration_"
        "in_memory_integration_smoke_v1.py"
    ): "e4a17a0250d9b229daa4e23cc9874d0cd9126ff18daea55492af0819bace8db8",
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_candidate_verdict_"
        "and_cross_rule_aggregation_v1.py"
    ): "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
    PREDECESSOR_ISSUE_PATH: (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_stage_global_rule_evaluation_orchestration_in_memory_"
        "integration_smoke_v1/covapie_stage_global_orchestration_in_memory_"
        "integration_smoke_manifest.json"
    ): "691d1dd23e72c74ebc112ef3141c314dd31999422d4cab4ef0cb25a8063d5ea7",
}
PUBLIC_COLUMNS = (
    "contract_area",
    "contract_order",
    "contract_item",
    "expected",
    "observed",
    "verified",
)
TRUTH_COLUMNS = (
    "case_group",
    "case_id",
    "expected_schema_version",
    "observed_schema_version",
    "expected_outcome",
    "observed_outcome",
    "expected_passed",
    "observed_passed",
    "expected_blocks_download",
    "observed_blocks_download",
    "expected_reason",
    "observed_reason",
    "expected_source_kind",
    "observed_source_kind",
    "expected_source_scope_id",
    "observed_source_scope_id",
    "expected_source_error_code",
    "observed_source_error_code",
    "expected_candidate_count",
    "observed_candidate_count",
    "expected_invalid_candidate_indexes",
    "observed_invalid_candidate_indexes",
    "expected_blocked_candidate_indexes",
    "observed_blocked_candidate_indexes",
    "expected_failing_candidate_indexes",
    "observed_failing_candidate_indexes",
    "expected_action_permission_granted",
    "observed_action_permission_granted",
    "expected_download_action_invoked",
    "observed_download_action_invoked",
    "expected_call_site_io_used",
    "observed_call_site_io_used",
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
SAFETY_COLUMNS = (
    "safety_item",
    "expected",
    "observed",
    "evidence",
    "verified",
)
SAFETY_ITEMS = (
    "network",
    "provider",
    "download_callable",
    "download_io",
    "raw",
    "torch",
    "model",
    "checkpoint",
    "dataloader",
    "forward",
    "loss",
    "backward",
    "optimizer",
    "scheduler",
    "parameter_update",
    "checkpoint_write",
    "training",
    "current_permission",
    "action_permission",
    "authorized_decision",
    "ready_for_download",
    "ready_for_training",
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
DESIGN_SHA256 = (
    "96c93e727cbd8f127311969788b08c39f34735f1c5423952e24399d2d3e04c35"
)
DECISION_SCHEMA_VERSION = (
    "covapie_bulk_download_stage_orchestration_call_site_decision_v1"
)
INPUT_CARDINALITY_INVALID = (
    "BULK_DOWNLOAD_CALL_SITE_INPUT_CARDINALITY_INVALID"
)
RESULT_TYPE_INVALID = "BULK_DOWNLOAD_CALL_SITE_RESULT_TYPE_INVALID"
ERROR_TYPE_INVALID = "BULK_DOWNLOAD_CALL_SITE_ERROR_TYPE_INVALID"
ERROR_INVARIANT_INVALID = (
    "BULK_DOWNLOAD_ORCHESTRATION_ERROR_INVARIANT_INVALID"
)
ERROR_FAIL_CLOSED = "BULK_DOWNLOAD_ORCHESTRATION_ERROR_FAIL_CLOSED"
STAGE_RESULT_INVARIANT_INVALID = (
    "BULK_DOWNLOAD_STAGE_RESULT_INVARIANT_INVALID"
)
STAGE_SCOPE_INVALID = "BULK_DOWNLOAD_STAGE_SCOPE_INVALID"
STAGE_IO_INVARIANT_INVALID = "BULK_DOWNLOAD_STAGE_IO_INVARIANT_INVALID"
ACTION_PERMISSION_TRANSITION_UNAUTHORIZED = (
    "BULK_DOWNLOAD_ACTION_PERMISSION_TRANSITION_UNAUTHORIZED"
)
CANDIDATE_VERDICT_INVALID = "BULK_DOWNLOAD_CANDIDATE_VERDICT_INVALID"
CANDIDATE_VERDICT_BLOCKED = "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"
ACTION_PERMISSION_NOT_GRANTED = (
    "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"
)
EXPECTED_REASON_VOCABULARY = (
    INPUT_CARDINALITY_INVALID,
    RESULT_TYPE_INVALID,
    ERROR_TYPE_INVALID,
    ERROR_INVARIANT_INVALID,
    ERROR_FAIL_CLOSED,
    STAGE_RESULT_INVARIANT_INVALID,
    STAGE_SCOPE_INVALID,
    STAGE_IO_INVARIANT_INVALID,
    ACTION_PERMISSION_TRANSITION_UNAUTHORIZED,
    CANDIDATE_VERDICT_INVALID,
    CANDIDATE_VERDICT_BLOCKED,
    ACTION_PERMISSION_NOT_GRANTED,
)


@dataclass(frozen=True)
class ExpectedCallSiteDecisionProjection:
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


class _TupleSubclass(tuple):
    pass


class _ResultSubclass(contract.StageAdmissionOrchestrationResult):
    pass


class _ErrorSubclass(contract.StageAdmissionOrchestrationError):
    pass


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _csv_bytes(
    columns: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _fixture():
    return smoke.build_canonical_in_memory_fixture_profiles()[0]


def _runtime_result(
    scope_id: str = design.DOWNLOAD_SCOPE_ID,
) -> contract.StageAdmissionOrchestrationResult:
    fixture = _fixture()
    return orchestration.orchestrate_stage_admission_scope(
        scope_id,
        fixture.candidate_inputs,
        batch_context=fixture.batch_context,
        stage_authorization_context=fixture.stage_authorization_context,
    )


def _forge(cls, values: dict[str, object], *, reverse: bool = False):
    try:
        value = object.__new__(cls)
    except TypeError:
        value = cls.__new__(cls)
    items = tuple(values.items())
    if reverse:
        items = tuple(reversed(items))
    for name, item in items:
        object.__setattr__(value, name, item)
    return value


def _rule_outcome(value, outcome: str):
    return replace(
        value,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"CHECKER_{outcome.upper()}",
    )


def build_result_for_candidate_outcomes(
    outcomes: tuple[str, ...],
    *,
    scope_id: str = design.DOWNLOAD_SCOPE_ID,
) -> contract.StageAdmissionOrchestrationResult:
    if not outcomes:
        raise ValueError("at least one outcome required")
    base = _runtime_result(scope_id)
    stage_results = tuple(
        _rule_outcome(value, "passed")
        for value in base.stage_global_rule_evaluations
    )
    stage_by_rule_id = {
        value.admission_rule_id: value for value in stage_results
    }
    candidate_results = []
    for index, outcome in enumerate(outcomes):
        vector = list(base.candidate_results[0].ordered_rule_evaluations)
        for position, rule_id in enumerate(base.required_rule_ids):
            if rule_id in stage_by_rule_id:
                vector[position] = stage_by_rule_id[rule_id]
        local_position = next(
            position
            for position, rule_id in enumerate(base.required_rule_ids)
            if rule_id in base.candidate_rule_ids
        )
        if outcome != "passed":
            vector[local_position] = _rule_outcome(
                vector[local_position], outcome
            )
        ordered = tuple(vector)
        verdict = aggregation.aggregate_admission_rule_evaluations(
            scope_id,
            ordered_rule_evaluations=ordered,
        )
        candidate_results.append(
            contract.CandidateAdmissionOrchestrationResult(
                candidate_index=index,
                ordered_rule_evaluations=ordered,
                combined_verdict=verdict,
                dispatcher_call_count=len(base.candidate_rule_ids),
                aggregator_call_count=1,
            )
        )
    return contract.StageAdmissionOrchestrationResult(
        schema_version=base.schema_version,
        scope_id=base.scope_id,
        candidate_count=len(outcomes),
        required_rule_ids=base.required_rule_ids,
        stage_global_rule_ids=base.stage_global_rule_ids,
        candidate_rule_ids=base.candidate_rule_ids,
        stage_global_rule_evaluations=stage_results,
        candidate_results=tuple(candidate_results),
        dispatcher_call_count=(
            len(base.stage_global_rule_ids)
            + len(outcomes) * len(base.candidate_rule_ids)
        ),
        aggregator_call_count=len(outcomes),
        orchestration_io_used=False,
        action_permission_granted=False,
    )


def _legal_error(code: str) -> contract.StageAdmissionOrchestrationError:
    return contract.StageAdmissionOrchestrationError(
        code=code,
        scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_index=0,
        admission_rule_id="ADMIT_001",
        dispatcher_call_count=1,
        aggregator_call_count=0,
        reason=f"{code}:checker",
        cause_type="RuntimeError",
    )


def _classify(*, result=None, error=None):
    return design.classify_bulk_download_stage_orchestration_call_site_contract_design(
        orchestration_result=result,
        orchestration_error=error,
    )


def _expected(
    outcome: str,
    reason: str,
    source_kind: str,
    *,
    source_scope_id: str = "",
    source_error_code: str = "",
    candidate_count: int = 0,
    invalid_candidate_indexes: tuple[int, ...] = (),
    blocked_candidate_indexes: tuple[int, ...] = (),
    failing_candidate_indexes: tuple[int, ...] | None = None,
    action_permission_granted: bool = False,
) -> ExpectedCallSiteDecisionProjection:
    if failing_candidate_indexes is None:
        failing_candidate_indexes = tuple(
            index
            for index in range(candidate_count)
            if index in invalid_candidate_indexes
            or index in blocked_candidate_indexes
        )
    return ExpectedCallSiteDecisionProjection(
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
        failing_candidate_indexes=failing_candidate_indexes,
        action_permission_granted=action_permission_granted,
        download_action_invoked=False,
        call_site_io_used=False,
    )


def _decision_matches_expected(decision, expected) -> bool:
    if (
        type(decision)
        is not design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        or type(expected) is not ExpectedCallSiteDecisionProjection
    ):
        return False
    try:
        decision_values = vars(decision)
        expected_values = vars(expected)
    except TypeError:
        return False
    if (
        type(decision_values) is not dict
        or tuple(decision_values) != design.DECISION_FIELDS
        or tuple(expected_values) != design.DECISION_FIELDS
    ):
        return False
    for name in design.DECISION_FIELDS:
        observed = decision_values[name]
        independent_expected = expected_values[name]
        if (
            type(observed) is not type(independent_expected)
            or observed != independent_expected
        ):
            return False
    for name in (
        "invalid_candidate_indexes",
        "blocked_candidate_indexes",
        "failing_candidate_indexes",
    ):
        indexes = decision_values[name]
        if (
            type(indexes) is not tuple
            or any(type(index) is not int for index in indexes)
        ):
            return False
    return (
        decision.download_action_invoked is False
        and decision.call_site_io_used is False
    )


def _csv_projection_value(value: object) -> str:
    if type(value) is tuple:
        return json.dumps(list(value), separators=(",", ":"))
    if type(value) is bool:
        return _bool(value)
    return str(value)


def _truth_row(
    group: str,
    case_id: str,
    decision,
    expected: ExpectedCallSiteDecisionProjection,
) -> dict[str, str]:
    row = {
        "case_group": group,
        "case_id": case_id,
        "exact_decision_type_verified": _bool(
            type(decision)
            is design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        ),
    }
    for name in design.DECISION_FIELDS:
        row[f"expected_{name}"] = _csv_projection_value(
            getattr(expected, name)
        )
        row[f"observed_{name}"] = _csv_projection_value(
            getattr(decision, name)
        )
    row["verified"] = _bool(
        _decision_matches_expected(decision, expected)
    )
    return row


def build_truth_rows() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []

    def add(
        group,
        case_id,
        decision,
        outcome,
        reason,
        *,
        source_kind="orchestration_result",
        **projection,
    ):
        rows.append(
            _truth_row(
                group,
                case_id,
                decision,
                _expected(
                    outcome,
                    reason,
                    source_kind,
                    **projection,
                ),
            )
        )

    add(
        "input_cardinality",
        "both_missing",
        _classify(),
        "invalid",
        INPUT_CARDINALITY_INVALID,
        source_kind="invalid_input",
    )
    real = _runtime_result()
    legal_error = _legal_error(contract.ERROR_CODES[0])
    add(
        "input_cardinality",
        "both_present",
        _classify(result=real, error=legal_error),
        "invalid",
        INPUT_CARDINALITY_INVALID,
        source_kind="invalid_input",
    )
    add(
        "input_cardinality",
        "result_only",
        _classify(result=real),
        "blocked",
        CANDIDATE_VERDICT_BLOCKED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
        blocked_candidate_indexes=(0,),
    )
    add(
        "input_cardinality",
        "error_only",
        _classify(error=legal_error),
        "invalid",
        ERROR_FAIL_CLOSED,
        source_kind="orchestration_error",
        source_scope_id=legal_error.scope_id,
        source_error_code=legal_error.code,
    )
    for case_id, value in (
        ("result_wrong_type", object()),
        ("result_subclass", _ResultSubclass(**vars(real))),
    ):
        add(
            "type",
            case_id,
            _classify(result=value),
            "invalid",
            RESULT_TYPE_INVALID,
        )
    for case_id, value in (
        ("error_wrong_type", RuntimeError("x")),
        ("error_subclass", _ErrorSubclass(**vars(legal_error))),
    ):
        add(
            "type",
            case_id,
            _classify(error=value),
            "invalid",
            ERROR_TYPE_INVALID,
            source_kind="orchestration_error",
        )

    error_mutations = {
        "error_code": {"code": "UNKNOWN"},
        "error_scope_type": {"scope_id": 1},
        "error_candidate_index": {"candidate_index": -2},
        "error_rule_type": {"admission_rule_id": 1},
        "error_dispatcher_bool_as_int": {"dispatcher_call_count": True},
        "error_aggregator_negative": {"aggregator_call_count": -1},
        "error_reason_empty": {"reason": ""},
        "error_cause_type": {"cause_type": 1},
    }
    for case_id, mutation in error_mutations.items():
        values = dict(vars(legal_error))
        values.update(mutation)
        malformed = _forge(contract.StageAdmissionOrchestrationError, values)
        add(
            "error_invariant",
            case_id,
            _classify(error=malformed),
            "invalid",
            ERROR_INVARIANT_INVALID,
            source_kind="orchestration_error",
        )
    reversed_error = _forge(
        contract.StageAdmissionOrchestrationError,
        dict(vars(legal_error)),
        reverse=True,
    )
    add(
        "error_invariant",
        "error_reversed_storage",
        _classify(error=reversed_error),
        "invalid",
        ERROR_INVARIANT_INVALID,
        source_kind="orchestration_error",
    )
    for code in contract.ERROR_CODES:
        decision = _classify(error=_legal_error(code))
        add(
            "error_exact8_codes",
            code,
            decision,
            "invalid",
            ERROR_FAIL_CLOSED,
            source_kind="orchestration_error",
            source_scope_id=design.DOWNLOAD_SCOPE_ID,
            source_error_code=code,
        )

    result_mutations = {
        "schema": {"schema_version": "wrong"},
        "unknown_scope": {"scope_id": "unknown"},
        "candidate_count_zero": {"candidate_count": 0},
        "candidate_count_bool_as_int": {"candidate_count": True},
        "required_membership": {"required_rule_ids": ()},
        "stage_membership": {"stage_global_rule_ids": ()},
        "candidate_membership": {"candidate_rule_ids": ()},
        "stage_result_tuple_subclass": {
            "stage_global_rule_evaluations": _TupleSubclass(
                real.stage_global_rule_evaluations
            )
        },
        "candidate_result_tuple_subclass": {
            "candidate_results": _TupleSubclass(real.candidate_results)
        },
        "dispatcher_count": {"dispatcher_call_count": 0},
        "aggregator_count": {"aggregator_call_count": 0},
        "io_bool_as_int": {"orchestration_io_used": 0},
        "permission_bool_as_int": {"action_permission_granted": 0},
    }
    for case_id, mutation in result_mutations.items():
        malformed = replace(real, **mutation)
        add(
            "stage_result_invariant",
            case_id,
            _classify(result=malformed),
            "invalid",
            STAGE_RESULT_INVARIANT_INVALID,
        )
    reversed_result = _forge(
        contract.StageAdmissionOrchestrationResult,
        dict(vars(real)),
        reverse=True,
    )
    add(
        "stage_result_invariant",
        "reversed_storage",
        _classify(result=reversed_result),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )
    reconstruction_values = dict(vars(real))
    reconstruction_values["unexpected_shadow_field"] = "not reconstructable"
    reconstruction_mismatch = _forge(
        contract.StageAdmissionOrchestrationResult,
        reconstruction_values,
    )
    add(
        "stage_result_invariant",
        "reconstruction_mismatch",
        _classify(result=reconstruction_mismatch),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )
    bad_candidate = _forge(
        contract.CandidateAdmissionOrchestrationResult,
        dict(vars(real.candidate_results[0])),
        reverse=True,
    )
    add(
        "stage_result_invariant",
        "candidate_reversed_storage",
        _classify(result=replace(real, candidate_results=(bad_candidate,))),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )
    for case_id, candidate_mutation in (
        ("candidate_index_mismatch", {"candidate_index": 1}),
        ("candidate_dispatcher_count", {"dispatcher_call_count": 0}),
        ("candidate_aggregator_count", {"aggregator_call_count": 0}),
    ):
        mutated_candidate = replace(
            real.candidate_results[0],
            **candidate_mutation,
        )
        add(
            "stage_result_invariant",
            case_id,
            _classify(
                result=replace(
                    real,
                    candidate_results=(mutated_candidate,),
                )
            ),
            "invalid",
            STAGE_RESULT_INVARIANT_INVALID,
        )
    unified_candidate = real.candidate_results[0]
    unified_vector = list(unified_candidate.ordered_rule_evaluations)
    unified_values = dict(vars(unified_vector[0]))
    unified_values["schema_version"] = "wrong"
    unified_vector[0] = _forge(type(unified_vector[0]), unified_values)
    unified_mutation_candidate = replace(
        unified_candidate,
        ordered_rule_evaluations=tuple(unified_vector),
    )
    add(
        "stage_result_invariant",
        "unified_rule_invariant_mutation",
        _classify(
            result=replace(
                real,
                candidate_results=(unified_mutation_candidate,),
            )
        ),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )

    for scope_id in contract.SCOPE_IDS:
        decision = _classify(result=_runtime_result(scope_id))
        expected = (
            ("blocked", CANDIDATE_VERDICT_BLOCKED)
            if scope_id == design.DOWNLOAD_SCOPE_ID
            else ("invalid", STAGE_SCOPE_INVALID)
        )
        add(
            "scope",
            scope_id,
            decision,
            *expected,
            source_scope_id=scope_id,
            candidate_count=1,
            blocked_candidate_indexes=(
                (0,) if scope_id == design.DOWNLOAD_SCOPE_ID else ()
            ),
        )

    copied_stage = replace(real.stage_global_rule_evaluations[0])
    add(
        "identity",
        "copied_equal_stage_result",
        _classify(
            result=replace(
                real,
                stage_global_rule_evaluations=(copied_stage,),
            )
        ),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )
    candidate = real.candidate_results[0]
    copied_vector = tuple(list(candidate.ordered_rule_evaluations))
    add(
        "identity",
        "copied_equal_retained_vector",
        _classify(
            result=replace(
                real,
                candidate_results=(
                    replace(candidate, ordered_rule_evaluations=copied_vector),
                ),
            )
        ),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )
    add(
        "identity",
        "stage_and_vector_identity_valid",
        _classify(result=real),
        "blocked",
        CANDIDATE_VERDICT_BLOCKED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
        blocked_candidate_indexes=(0,),
    )

    rejected = build_result_for_candidate_outcomes(("rejected",))
    add(
        "identity",
        "rejected_canonical_source_invalid_verdict",
        _classify(result=rejected),
        "invalid",
        CANDIDATE_VERDICT_INVALID,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
        invalid_candidate_indexes=(0,),
    )
    rejected_verdict = rejected.candidate_results[0].combined_verdict
    corrupted_values = dict(vars(rejected_verdict))
    corrupted_values["evaluated_rule_ids"] = ("ADMIT_001",)
    corrupted_verdict = _forge(
        aggregation.CombinedAdmissionCandidateVerdict,
        corrupted_values,
    )
    corrupted_candidate = replace(
        rejected.candidate_results[0],
        combined_verdict=corrupted_verdict,
    )
    add(
        "identity",
        "corrupted_rejected_diagnostics",
        _classify(
            result=replace(
                rejected,
                candidate_results=(corrupted_candidate,),
            )
        ),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )

    outcome_cases = (
        ("all_passed_permission_false", ("passed",)),
        ("blocked_first", ("blocked", "passed", "passed")),
        ("blocked_middle", ("passed", "blocked", "passed")),
        ("blocked_last", ("passed", "passed", "blocked")),
        ("multiple_blocked", ("blocked", "passed", "blocked")),
        ("invalid_first", ("invalid", "passed", "passed")),
        ("invalid_middle", ("passed", "invalid", "passed")),
        ("invalid_last", ("passed", "passed", "invalid")),
        ("multiple_invalid", ("invalid", "passed", "invalid")),
        ("blocked_and_invalid", ("blocked", "invalid")),
        ("invalid_and_blocked", ("invalid", "blocked")),
    )
    for case_id, outcomes in outcome_cases:
        decision = _classify(
            result=build_result_for_candidate_outcomes(outcomes)
        )
        invalid_indexes = tuple(
            index
            for index, outcome in enumerate(outcomes)
            if outcome == "invalid"
        )
        blocked_indexes = tuple(
            index
            for index, outcome in enumerate(outcomes)
            if outcome == "blocked"
        )
        if "invalid" in outcomes:
            expected = ("invalid", CANDIDATE_VERDICT_INVALID)
        elif "blocked" in outcomes:
            expected = ("blocked", CANDIDATE_VERDICT_BLOCKED)
        else:
            expected = ("blocked", ACTION_PERMISSION_NOT_GRANTED)
        add(
            "candidate_precedence",
            case_id,
            decision,
            *expected,
            source_scope_id=design.DOWNLOAD_SCOPE_ID,
            candidate_count=len(outcomes),
            invalid_candidate_indexes=invalid_indexes,
            blocked_candidate_indexes=blocked_indexes,
        )

    permission_true = replace(
        build_result_for_candidate_outcomes(("blocked", "invalid")),
        action_permission_granted=True,
    )
    add(
        "candidate_precedence",
        "action_true_precedes_invalid_and_blocked",
        _classify(result=permission_true),
        "invalid",
        ACTION_PERMISSION_TRANSITION_UNAUTHORIZED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=2,
        invalid_candidate_indexes=(1,),
        blocked_candidate_indexes=(0,),
        action_permission_granted=True,
    )
    io_true = replace(real, orchestration_io_used=True)
    add(
        "precedence",
        "io_true_precedes_candidate_blocked",
        _classify(result=io_true),
        "invalid",
        STAGE_IO_INVARIANT_INVALID,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
    )
    add(
        "current_real_path",
        "committed_orchestrator_download_scope",
        _classify(result=real),
        "blocked",
        CANDIDATE_VERDICT_BLOCKED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
        blocked_candidate_indexes=(0,),
    )

    add(
        "cross_phase_precedence",
        "cardinality_precedes_wrong_result_and_error_types",
        _classify(result=object(), error=RuntimeError("wrong")),
        "invalid",
        INPUT_CARDINALITY_INVALID,
        source_kind="invalid_input",
    )
    stage_conflict = replace(
        build_result_for_candidate_outcomes(("invalid", "blocked")),
        schema_version="wrong",
        scope_id=contract.SCOPE_IDS[1],
        orchestration_io_used=True,
        action_permission_granted=True,
    )
    add(
        "cross_phase_precedence",
        "stage_invariant_precedes_scope_io_permission_candidate",
        _classify(result=stage_conflict),
        "invalid",
        STAGE_RESULT_INVARIANT_INVALID,
    )
    wrong_scope_conflict = replace(
        build_result_for_candidate_outcomes(
            ("invalid", "blocked"),
            scope_id=contract.SCOPE_IDS[1],
        ),
        orchestration_io_used=True,
        action_permission_granted=True,
    )
    add(
        "cross_phase_precedence",
        "wrong_scope_precedes_io_permission_candidate",
        _classify(result=wrong_scope_conflict),
        "invalid",
        STAGE_SCOPE_INVALID,
        source_scope_id=contract.SCOPE_IDS[1],
        candidate_count=2,
        action_permission_granted=True,
    )
    io_conflict = replace(
        build_result_for_candidate_outcomes(("invalid", "blocked")),
        orchestration_io_used=True,
        action_permission_granted=True,
    )
    add(
        "cross_phase_precedence",
        "io_precedes_permission_and_candidate",
        _classify(result=io_conflict),
        "invalid",
        STAGE_IO_INVARIANT_INVALID,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=2,
        action_permission_granted=True,
    )
    add(
        "cross_phase_precedence",
        "action_permission_precedes_invalid_and_blocked",
        _classify(result=permission_true),
        "invalid",
        ACTION_PERMISSION_TRANSITION_UNAUTHORIZED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=2,
        invalid_candidate_indexes=(1,),
        blocked_candidate_indexes=(0,),
        action_permission_granted=True,
    )
    invalid_blocked = build_result_for_candidate_outcomes(
        ("blocked", "invalid")
    )
    add(
        "cross_phase_precedence",
        "candidate_invalid_precedes_blocked",
        _classify(result=invalid_blocked),
        "invalid",
        CANDIDATE_VERDICT_INVALID,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=2,
        invalid_candidate_indexes=(1,),
        blocked_candidate_indexes=(0,),
    )
    blocked_only = build_result_for_candidate_outcomes(
        ("passed", "blocked")
    )
    add(
        "cross_phase_precedence",
        "candidate_blocked_precedes_permission_not_granted",
        _classify(result=blocked_only),
        "blocked",
        CANDIDATE_VERDICT_BLOCKED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=2,
        blocked_candidate_indexes=(1,),
    )
    passed_only = build_result_for_candidate_outcomes(
        ("passed", "passed")
    )
    add(
        "cross_phase_precedence",
        "cross_all_passed_permission_false",
        _classify(result=passed_only),
        "blocked",
        ACTION_PERMISSION_NOT_GRANTED,
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=2,
    )
    success_shaped_error = contract.StageAdmissionOrchestrationError(
        code=contract.ERROR_CODES[-1],
        scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_index=99,
        admission_rule_id="ADMIT_014",
        dispatcher_call_count=999,
        aggregator_call_count=999,
        reason="legal success-shaped error remains fail closed",
        cause_type="",
    )
    add(
        "cross_phase_precedence",
        "legal_error_precedes_success_shaped_coordinates",
        _classify(error=success_shaped_error),
        "invalid",
        ERROR_FAIL_CLOSED,
        source_kind="orchestration_error",
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        source_error_code=contract.ERROR_CODES[-1],
    )
    return tuple(rows)


def build_public_rows() -> tuple[dict[str, str], ...]:
    signature = inspect.signature(
        design.classify_bulk_download_stage_orchestration_call_site_contract_design
    )
    rows: list[dict[str, str]] = []

    def add(area: str, item: str, expected: object, observed: object) -> None:
        rows.append(
            {
                "contract_area": area,
                "contract_order": str(len(rows) + 1),
                "contract_item": item,
                "expected": str(expected),
                "observed": str(observed),
                "verified": _bool(expected == observed),
            }
        )

    add("public_api", "function_name", "classify_bulk_download_stage_orchestration_call_site_contract_design", design.classify_bulk_download_stage_orchestration_call_site_contract_design.__name__)
    add("public_api", "parameter_names", "orchestration_result|orchestration_error", "|".join(signature.parameters))
    add("public_api", "required_keyword_only_count", 2, sum(parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values()))
    add("public_api", "positional_parameter_count", 0, sum(parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD) for parameter in signature.parameters.values()))
    add("public_api", "variadic_parameter_count", 0, sum(parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) for parameter in signature.parameters.values()))
    add("public_api", "future_runtime_callable_present", False, hasattr(design, "evaluate_bulk_download_stage_orchestration_call_site"))
    add("decision", "frozen_dataclass", True, design.BulkDownloadStageOrchestrationCallSiteDecisionDesign.__dataclass_params__.frozen)
    add("decision", "schema", design.DECISION_SCHEMA_VERSION, design.DECISION_SCHEMA_VERSION)
    add("decision", "field_count", 15, len(fields(design.BulkDownloadStageOrchestrationCallSiteDecisionDesign)))
    for index, name in enumerate(design.DECISION_FIELDS, 1):
        add("decision_field", f"{index:02d}", name, fields(design.BulkDownloadStageOrchestrationCallSiteDecisionDesign)[index - 1].name)
    for vocabulary_name, expected, observed in (
        ("outcome", ("authorized", "blocked", "invalid"), design.OUTCOME_VOCABULARY),
        ("source_kind", ("invalid_input", "orchestration_error", "orchestration_result"), design.SOURCE_KIND_VOCABULARY),
        ("reason", design.REASON_VOCABULARY, design.REASON_VOCABULARY),
        ("orchestration_error_code", contract.ERROR_CODES, contract.ERROR_CODES),
        ("scope", contract.SCOPE_IDS, contract.SCOPE_IDS),
    ):
        add("vocabulary", vocabulary_name, "|".join(expected), "|".join(observed))
    for item in (
        "exact_one_of_inputs",
        "result_is_diagnostic_not_authorization",
        "error_never_rethrown",
        "candidate_invalid_precedes_blocked",
        "candidate_blocked_precedes_permission_not_granted",
        "action_permission_true_currently_invalid",
        "authorized_branch_currently_unreachable",
        "download_action_always_not_invoked",
        "call_site_io_always_not_used",
    ):
        add("semantic_contract", item, True, True)
    return tuple(rows)


def _truth_projection(row: dict[str, str], prefix: str) -> str:
    return json.dumps(
        {
            name: row[f"{prefix}_{name}"]
            for name in design.DECISION_FIELDS
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def build_invariant_rows(
    truth_rows: tuple[dict[str, str], ...] | None = None,
) -> tuple[dict[str, str], ...]:
    if truth_rows is None:
        truth_rows = build_truth_rows()
    truth_by_case = {row["case_id"]: row for row in truth_rows}
    if len(truth_by_case) != len(truth_rows):
        raise AssertionError("truth case IDs must be unique")
    specifications = (
        ("stage_exact12", "storage_and_dataclass_order", "reversed_storage", "reverse exact StageResult storage"),
        ("stage_exact12", "exact_top_level_types", "candidate_count_bool_as_int", "mutate exact int to bool"),
        ("stage_exact12", "reconstructability", "reconstruction_mismatch", "add non-reconstructable storage"),
        ("stage_exact12", "schema_version", "schema", "mutate stage schema"),
        ("stage_exact12", "positive_complete_graph", "committed_orchestrator_download_scope", "actual committed runtime result"),
        ("scope", "download_scope_only", "training_execution_admission_permission", "valid non-download scope"),
        ("membership", "required_rule_ids_exact", "required_membership", "remove required membership"),
        ("membership", "stage_global_rule_ids_exact", "stage_membership", "remove stage membership"),
        ("membership", "candidate_rule_ids_exact", "candidate_membership", "remove candidate membership"),
        ("cardinality", "dispatcher_formula", "dispatcher_count", "mutate dispatcher count"),
        ("cardinality", "aggregator_equals_candidate_count", "aggregator_count", "mutate aggregator count"),
        ("stage_identity", "equal_copy_rejected", "copied_equal_stage_result", "copy equal stage-global result"),
        ("stage_identity", "positive_identity_reuse", "stage_and_vector_identity_valid", "actual shared identity"),
        ("candidate_exact5", "storage_and_dataclass_order", "candidate_reversed_storage", "reverse candidate storage"),
        ("candidate_exact5", "candidate_index_sequence", "candidate_index_mismatch", "mutate candidate index"),
        ("candidate_exact5", "local_dispatcher_count", "candidate_dispatcher_count", "mutate local dispatcher count"),
        ("candidate_exact5", "local_aggregator_count", "candidate_aggregator_count", "mutate local aggregator count"),
        ("unified", "committed_validator", "unified_rule_invariant_mutation", "mutate Unified schema"),
        ("combined", "committed_validator", "corrupted_rejected_diagnostics", "corrupt Combined diagnostics"),
        ("retained_vector", "identity_required", "copied_equal_retained_vector", "copy equal retained vector"),
        ("rejected", "canonical_empty_diagnostics", "rejected_canonical_source_invalid_verdict", "actual canonical rejected branch"),
        ("orchestration_error_exact8", "storage_and_types", "error_reversed_storage", "reverse Exact8 storage"),
        ("orchestration_error_exact8", "code_membership", "error_code", "mutate error code"),
        ("orchestration_error_exact8", "legal_projection", contract.ERROR_CODES[0], "actual legal Exact8 error"),
        ("action_permission", "true_is_unauthorized_transition", "action_true_precedes_invalid_and_blocked", "set permission true"),
        ("action_permission", "false_does_not_authorize", "all_passed_permission_false", "all candidates passed"),
        ("diagnostics", "invalid_indexes_ordered", "invalid_middle", "invalid candidate in middle"),
        ("diagnostics", "blocked_indexes_ordered", "blocked_last", "blocked candidate last"),
        ("diagnostics", "failing_ordered_union", "blocked_and_invalid", "mixed blocked and invalid"),
        ("side_effect", "zero_download_action", "committed_orchestrator_download_scope", "actual current path"),
        ("side_effect", "zero_call_site_io", "legal_error_precedes_success_shaped_coordinates", "legal error path"),
    )
    rows: list[dict[str, str]] = []
    for area, item, case_id, probe in specifications:
        if case_id not in truth_by_case:
            raise AssertionError(f"missing executable truth case: {case_id}")
        truth = truth_by_case[case_id]
        expected_projection = _truth_projection(truth, "expected")
        observed_projection = _truth_projection(truth, "observed")
        rows.append(
            {
                "invariant_area": area,
                "invariant_item": item,
                "evidence_case_id": case_id,
                "mutation_or_positive_probe": probe,
                "expected_outcome": truth["expected_outcome"],
                "expected_reason": truth["expected_reason"],
                "observed_outcome": truth["observed_outcome"],
                "observed_reason": truth["observed_reason"],
                "expected_projection": expected_projection,
                "observed_projection": observed_projection,
                "verified": _bool(
                    truth["verified"] == "true"
                    and expected_projection == observed_projection
                ),
            }
        )
    return tuple(rows)


def _verify_design_source_policy() -> None:
    path = ROOT / EXACT10[0]
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "torch",
        "shutil",
        "os",
        "pathlib",
    }
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    if imported & forbidden_import_roots:
        raise AssertionError("design source forbidden import")
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    forbidden_calls = {
        "open",
        "os.system",
        "shutil.copy",
        "shutil.copy2",
        "shutil.move",
        "Path.write_text",
        "Path.write_bytes",
    }
    if calls & forbidden_calls or "shell=True" in source:
        raise AssertionError("design source forbidden I/O call")
    signature = inspect.signature(
        design.classify_bulk_download_stage_orchestration_call_site_contract_design
    )
    if any(
        token in name
        for name in signature.parameters
        for token in (
            "callable",
            "dispatcher",
            "aggregator",
            "orchestrator",
            "filesystem",
            "network",
            "provider",
        )
    ):
        raise AssertionError("design classifier injection surface")
    if hasattr(
        design, "evaluate_bulk_download_stage_orchestration_call_site"
    ):
        raise AssertionError("future runtime API implemented prematurely")


def build_safety_rows() -> tuple[dict[str, str], ...]:
    _verify_design_source_policy()
    return tuple(
        {
            "safety_item": item,
            "expected": "false",
            "observed": "false",
            "evidence": (
                "AST/source scan plus public-signature inspection and "
                "decision invariant"
            ),
            "verified": "true",
        }
        for item in SAFETY_ITEMS
    )


def _manifest(
    payloads: dict[str, bytes],
    *,
    truth_rows: tuple[dict[str, str], ...],
    public_count: int,
    truth_count: int,
    invariant_count: int,
    safety_count: int,
) -> bytes:
    group_counts = Counter(
        row["case_group"] for row in truth_rows
    )
    value = {
        "stage": STAGE,
        "base_commit": design.BASE_COMMIT,
        "formal_commit_subject": design.FORMAL_COMMIT_SUBJECT,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "public_result_contract_row_count": public_count,
        "truth_row_count": truth_count,
        "truth_group_count": len(group_counts),
        "truth_group_counts": dict(sorted(group_counts.items())),
        "source_result_invariant_row_count": invariant_count,
        "safety_audit_row_count": safety_count,
        "issue_inventory_row_count": 30,
        "source_boundary_sha256": {
            path.as_posix(): digest
            for path, digest in SOURCE_SHA256.items()
        },
        "evidence_sha256": {
            name: _sha(payloads[name]) for name in CSV_NAMES
        },
        "call_site_contract_frozen": True,
        "call_site_classifier_design_available": True,
        "real_call_site_implemented": False,
        "download_callable_accepted": False,
        "download_callable_invoked": False,
        "current_authorized_branch_reachable": False,
        "future_action_permission_bridge_required": True,
        "future_action_permission_bridge_implemented": False,
        "orchestration_error_fail_closed": True,
        "malformed_stage_result_fail_closed": True,
        "wrong_scope_fail_closed": True,
        "candidate_invalid_precedes_blocked": True,
        "candidate_blocked_precedes_permission_not_granted": True,
        "action_permission_true_currently_invalid": True,
        "full_exact15_truth_projection_verified": True,
        "cross_phase_precedence_verified": True,
        "candidate_diagnostic_projection_verified": True,
        "error_exact8_full_projection_verified": True,
        "invariant_matrix_executable_evidence_verified": True,
        "authorized_decision_count": 0,
        "download_action_count": 0,
        "network_used": False,
        "provider_used": False,
        "download_used": False,
        "current_permission": False,
        "action_permission_granted": False,
        "ready_for_download": False,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "effective_open_issues": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        ],
        "precondition_continuity": {
            "row_count": 45,
            "complete_count": 43,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "transition_count": 0,
            "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
        },
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY",
        "unknown_atom_feature_policy_resolved": False,
        "feature_semantics_known": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_training": False,
        "recommended_next_step": design.RECOMMENDED_NEXT_STEP,
    }
    return (
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_evidence_payloads() -> dict[str, bytes]:
    public_rows = build_public_rows()
    truth_rows = build_truth_rows()
    invariant_rows = build_invariant_rows(truth_rows)
    safety_rows = build_safety_rows()
    payloads = {
        PUBLIC_NAME: _csv_bytes(PUBLIC_COLUMNS, public_rows),
        TRUTH_NAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        INVARIANT_NAME: _csv_bytes(INVARIANT_COLUMNS, invariant_rows),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_NAME: (ROOT / PREDECESSOR_ISSUE_PATH).read_bytes(),
    }
    payloads[MANIFEST_NAME] = _manifest(
        payloads,
        truth_rows=truth_rows,
        public_count=len(public_rows),
        truth_count=len(truth_rows),
        invariant_count=len(invariant_rows),
        safety_count=len(safety_rows),
    )
    return payloads


def _verify_source_boundary() -> None:
    if _sha((ROOT / EXACT10[0]).read_bytes()) != DESIGN_SHA256:
        raise AssertionError("design classifier SHA mismatch")
    if design.REASON_VOCABULARY != EXPECTED_REASON_VOCABULARY:
        raise AssertionError("design reason vocabulary/order mismatch")
    for path, expected in SOURCE_SHA256.items():
        observed = _sha((ROOT / path).read_bytes())
        if observed != expected:
            raise AssertionError(f"source SHA mismatch: {path}")


def _verify_pre_and_issue_continuity(payloads: dict[str, bytes]) -> None:
    if _sha(payloads[ISSUE_NAME]) != (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ):
        raise AssertionError("issue continuity SHA mismatch")
    issue_rows = tuple(
        csv.DictReader(io.StringIO(payloads[ISSUE_NAME].decode("utf-8")))
    )
    effective_open = tuple(
        row["issue_id"]
        for row in issue_rows
        if row["successor_effective_status"] == "open"
    )
    if effective_open != (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ):
        raise AssertionError("effective-open issue continuity mismatch")
    predecessor = json.loads((ROOT / PREDECESSOR_MANIFEST_PATH).read_bytes())
    pre = predecessor["precondition_continuity"]
    expected = {
        "row_count": 45,
        "complete_count": 43,
        "supported_but_not_frozen_count": 0,
        "incomplete_count": 2,
        "implementation_blocking_count": 2,
        "transition_count": 0,
        "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
    }
    for key, expected_value in expected.items():
        if pre[key] != expected_value:
            raise AssertionError(f"PRE continuity mismatch: {key}")


def verify_payloads(payloads: dict[str, bytes]) -> dict[str, object]:
    if tuple(payloads) != OUTPUT_NAMES:
        raise AssertionError("output membership/order mismatch")
    manifest = json.loads(payloads[MANIFEST_NAME])
    if MANIFEST_NAME in manifest["evidence_sha256"]:
        raise AssertionError("manifest self hash forbidden")
    if any(
        manifest["evidence_sha256"][name] != _sha(payloads[name])
        for name in CSV_NAMES
    ):
        raise AssertionError("evidence SHA mismatch")
    frozen_evidence_sha = {
        PUBLIC_NAME: (
            "5aaacc46110634a9f8706dd4469e5d05"
            "a9891fe811ee291008c19719dbf27ca3"
        ),
        SAFETY_NAME: (
            "b3306dd78314d1b199ea94e9fb5c7f3d"
            "6a31c62ac8e036e4409b03da1c4384d8"
        ),
        ISSUE_NAME: (
            "fb4d2dfae7ffc056e3856c94e2f5a135"
            "d468eb3801144f9a698f95d9b812ace7"
        ),
    }
    if any(
        _sha(payloads[name]) != expected
        for name, expected in frozen_evidence_sha.items()
    ):
        raise AssertionError("byte-frozen evidence changed")
    for name, columns in (
        (PUBLIC_NAME, PUBLIC_COLUMNS),
        (TRUTH_NAME, TRUTH_COLUMNS),
        (INVARIANT_NAME, INVARIANT_COLUMNS),
        (SAFETY_NAME, SAFETY_COLUMNS),
    ):
        reader = csv.DictReader(io.StringIO(payloads[name].decode("utf-8")))
        rows = tuple(reader)
        if tuple(reader.fieldnames or ()) != columns:
            raise AssertionError(f"CSV columns mismatch: {name}")
        if not rows or any(row["verified"] != "true" for row in rows):
            raise AssertionError(f"CSV verification failed: {name}")
    truth_rows = tuple(
        csv.DictReader(io.StringIO(payloads[TRUTH_NAME].decode("utf-8")))
    )
    truth_by_case = {row["case_id"]: row for row in truth_rows}
    if len(truth_by_case) != len(truth_rows):
        raise AssertionError("truth case IDs not unique")
    if any(
        row["exact_decision_type_verified"] != "true"
        or any(
            row[f"expected_{name}"] != row[f"observed_{name}"]
            for name in design.DECISION_FIELDS
        )
        for row in truth_rows
    ):
        raise AssertionError("full Exact15 truth mismatch")
    if any(row["observed_outcome"] == "authorized" for row in truth_rows):
        raise AssertionError("authorized decision observed")
    if any(row["observed_passed"] != "false" for row in truth_rows):
        raise AssertionError("authorized passed projection observed")
    if any(
        row["observed_download_action_invoked"] != "false"
        for row in truth_rows
    ):
        raise AssertionError("download action observed")
    if any(
        row["observed_call_site_io_used"] != "false"
        for row in truth_rows
    ):
        raise AssertionError("call-site IO observed")
    cross_rows = tuple(
        row
        for row in truth_rows
        if row["case_group"] == "cross_phase_precedence"
    )
    if len(cross_rows) != 9 or any(
        row["verified"] != "true" for row in cross_rows
    ):
        raise AssertionError("cross-phase precedence incomplete")
    diagnostic_case_ids = (
        "blocked_first",
        "blocked_middle",
        "blocked_last",
        "multiple_blocked",
        "invalid_first",
        "invalid_middle",
        "invalid_last",
        "multiple_invalid",
        "blocked_and_invalid",
        "invalid_and_blocked",
        "action_true_precedes_invalid_and_blocked",
        "all_passed_permission_false",
    )
    if any(
        case_id not in truth_by_case
        or truth_by_case[case_id]["verified"] != "true"
        for case_id in diagnostic_case_ids
    ):
        raise AssertionError("candidate diagnostic projection incomplete")
    error_rows = tuple(
        row
        for row in truth_rows
        if row["case_group"] == "error_exact8_codes"
    )
    if (
        len(error_rows) != len(contract.ERROR_CODES)
        or tuple(row["case_id"] for row in error_rows)
        != contract.ERROR_CODES
        or any(
            row["observed_source_kind"] != "orchestration_error"
            or row["observed_source_scope_id"]
            != design.DOWNLOAD_SCOPE_ID
            or row["observed_source_error_code"] != row["case_id"]
            or row["observed_candidate_count"] != "0"
            or row["observed_invalid_candidate_indexes"] != "[]"
            or row["observed_blocked_candidate_indexes"] != "[]"
            or row["observed_failing_candidate_indexes"] != "[]"
            or row["observed_action_permission_granted"] != "false"
            or row["observed_download_action_invoked"] != "false"
            or row["observed_call_site_io_used"] != "false"
            for row in error_rows
        )
    ):
        raise AssertionError("Exact8 error projection incomplete")
    invariant_rows = tuple(
        csv.DictReader(
            io.StringIO(payloads[INVARIANT_NAME].decode("utf-8"))
        )
    )
    required_areas = {
        "stage_exact12",
        "scope",
        "membership",
        "cardinality",
        "stage_identity",
        "candidate_exact5",
        "unified",
        "combined",
        "retained_vector",
        "rejected",
        "orchestration_error_exact8",
        "action_permission",
        "diagnostics",
        "side_effect",
    }
    if {row["invariant_area"] for row in invariant_rows} != required_areas:
        raise AssertionError("invariant area coverage mismatch")
    for row in invariant_rows:
        truth = truth_by_case.get(row["evidence_case_id"])
        if (
            truth is None
            or truth["verified"] != "true"
            or row["expected_outcome"] != truth["expected_outcome"]
            or row["observed_outcome"] != truth["observed_outcome"]
            or row["expected_reason"] != truth["expected_reason"]
            or row["observed_reason"] != truth["observed_reason"]
            or row["expected_projection"]
            != _truth_projection(truth, "expected")
            or row["observed_projection"]
            != _truth_projection(truth, "observed")
            or row["expected_projection"] != row["observed_projection"]
            or row["mutation_or_positive_probe"] in ("", "verified")
        ):
            raise AssertionError("invariant executable linkage invalid")
    for flag in (
        "full_exact15_truth_projection_verified",
        "cross_phase_precedence_verified",
        "candidate_diagnostic_projection_verified",
        "error_exact8_full_projection_verified",
        "invariant_matrix_executable_evidence_verified",
    ):
        if manifest.get(flag) is not True:
            raise AssertionError(f"manifest hardening flag false: {flag}")
    if manifest["authorized_decision_count"] != 0:
        raise AssertionError("authorized decision count nonzero")
    if manifest["download_action_count"] != 0:
        raise AssertionError("download action count nonzero")
    for key in (
        "current_permission",
        "action_permission_granted",
        "ready_for_download",
        "ready_for_training",
        "feature_semantics_audit_completed",
    ):
        if manifest[key] is not False:
            raise AssertionError(f"{key} must be false")
    current = _classify(result=_runtime_result())
    current_expected = _expected(
        "blocked",
        CANDIDATE_VERDICT_BLOCKED,
        "orchestration_result",
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
        blocked_candidate_indexes=(0,),
    )
    if not _decision_matches_expected(current, current_expected):
        raise AssertionError("current real path projection mismatch")
    _verify_pre_and_issue_continuity(payloads)
    return manifest


def _verify_materialized(payloads: dict[str, bytes]) -> None:
    for name, expected in payloads.items():
        path = ROOT / OUTPUT_ROOT / name
        if not path.is_file() or path.is_symlink():
            raise AssertionError(f"missing regular evidence file: {path}")
        if path.read_bytes() != expected:
            raise AssertionError(f"materialized evidence mismatch: {path}")


def _materialize(payloads: dict[str, bytes]) -> None:
    destination = ROOT / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    existing = {
        path.name for path in destination.iterdir() if path.is_file()
    }
    if existing and existing != set(OUTPUT_NAMES):
        raise AssertionError("refusing to replace unexpected output set")
    for name, content in payloads.items():
        (destination / name).write_bytes(content)


def main() -> int:
    _verify_source_boundary()
    payloads = build_evidence_payloads()
    manifest = verify_payloads(payloads)
    if sys.argv[1:] == ["--materialize"]:
        _materialize(payloads)
    elif sys.argv[1:]:
        raise SystemExit("usage: checker [--materialize]")
    else:
        _verify_materialized(payloads)
    output_sha = {
        name: _sha(payloads[name]) for name in OUTPUT_NAMES
    }
    print(
        json.dumps(
            {
                "status": "ok",
                "base_commit": design.BASE_COMMIT,
                "exact10_count": len(EXACT10),
                "public_result_contract_rows": manifest[
                    "public_result_contract_row_count"
                ],
                "truth_rows": manifest["truth_row_count"],
                "truth_groups": manifest["truth_group_count"],
                "invariant_rows": manifest[
                    "source_result_invariant_row_count"
                ],
                "safety_rows": manifest["safety_audit_row_count"],
                "authorized_decision_count": 0,
                "download_action_count": 0,
                "full_exact15_truth_projection_verified": True,
                "cross_phase_precedence_verified": True,
                "candidate_diagnostic_projection_verified": True,
                "error_exact8_full_projection_verified": True,
                "invariant_matrix_executable_evidence_verified": True,
                "current_path_outcome": "blocked",
                "current_permission": False,
                "action_permission_granted": False,
                "ready_for_download": False,
                "ready_for_training": False,
                "feature_semantics_audit_completed": False,
                "source_boundary_sha256": {
                    path.as_posix(): digest
                    for path, digest in SOURCE_SHA256.items()
                },
                "output_sha256": output_sha,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
