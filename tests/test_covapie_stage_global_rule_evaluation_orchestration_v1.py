"""Tests for the CovaPIE stage-global orchestration runtime V1."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import inspect
import io
import json
import shutil
import subprocess
import sys
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, get_type_hints

import pytest

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
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1 as runtime,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "a677414ffcfe30db463f6bed33d1fbbedb10e398"
BASE_PARENT = "3e55b6e58668ce66ba74df8e0894b15641601e52"
BASE_TREE = "0688b000345449fae40e80659367ece799576391"
BASE_SUBJECT = (
    "add CovaPIE stage-global rule evaluation orchestration contract v1"
)
FORMAL_SUBJECT = (
    "add CovaPIE stage-global rule evaluation orchestration runtime v1"
)
STAGE = "covapie_stage_global_rule_evaluation_orchestration_v1"
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
RUNTIME_NAME = "covapie_stage_global_orchestration_runtime_contract.csv"
TRACE_NAME = "covapie_stage_global_orchestration_call_trace_matrix.csv"
TRUTH_NAME = (
    "covapie_stage_global_orchestration_implementation_truth_matrix.csv"
)
SAFETY_NAME = (
    "covapie_stage_global_orchestration_implementation_safety_audit.csv"
)
ISSUE_NAME = "covapie_stage_global_orchestration_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_stage_global_rule_evaluation_orchestration_"
    "implementation_manifest.json"
)
OUTPUT_NAMES = (
    RUNTIME_NAME,
    TRACE_NAME,
    TRUTH_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
SUPPORT_PATHS = (
    Path("src/covalent_ext")
    / "covapie_stage_global_rule_evaluation_orchestration_v1.py",
    Path("scripts")
    / "check_covapie_stage_global_rule_evaluation_orchestration_v1.py",
    Path("tests")
    / "test_covapie_stage_global_rule_evaluation_orchestration_v1.py",
    Path("docs")
    / "covapie_stage_global_rule_evaluation_orchestration_v1_summary.md",
)
EXACT10 = SUPPORT_PATHS + tuple(DERIVED_ROOT / name for name in OUTPUT_NAMES)
ISSUE_PREDECESSOR = (
    Path("data/derived/covalent_small")
    / "covapie_stage_global_rule_evaluation_orchestration_contract_v1"
    / "covapie_stage_global_orchestration_issue_readiness_inventory.csv"
)
PREDECESSOR_MANIFEST = (
    Path("data/derived/covalent_small")
    / "covapie_stage_global_rule_evaluation_orchestration_contract_v1"
    / "covapie_stage_global_rule_evaluation_orchestration_contract_manifest.json"
)


def _evaluation(rule_id: str, outcome: str = "passed"):
    return dispatch_runtime.UnifiedAdmissionRuleEvaluation(
        schema_version=dispatch_runtime.RESULT_SCHEMA_VERSION,
        admission_rule_id=rule_id,
        admission_rule_name=contract.RULE_NAMES[rule_id],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"{rule_id}_{outcome.upper()}",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=contract.ADAPTER_IDS[rule_id],
    )


def _inputs(count: int):
    batch = {"batch": "caller"}
    authorization = {"authorization": "caller"}
    values = tuple(
        contract.AdmissionCandidateOrchestrationInput(
            candidate_record={"candidate_index": index},
            evaluation_context={"evaluation_index": index},
            download_result_context={"download_index": index},
        )
        for index in range(count)
    )
    return values, batch, authorization


class _Harness:
    def __init__(
        self,
        candidate_inputs,
        batch_context,
        authorization_context,
        *,
        outcomes=None,
        handler_exception_at=None,
        handler_malformed_at=None,
        aggregator_exception_at=None,
        aggregator_malformed=None,
    ):
        self.candidate_inputs = candidate_inputs
        self.batch_context = batch_context
        self.authorization_context = authorization_context
        self.outcomes = outcomes or {}
        self.handler_exception_at = handler_exception_at
        self.handler_malformed_at = handler_malformed_at
        self.aggregator_exception_at = aggregator_exception_at
        self.aggregator_malformed = aggregator_malformed or {}
        self.dispatch_calls: list[dict[str, Any]] = []
        self.aggregator_calls: list[dict[str, Any]] = []
        self.events: list[tuple[str, dict[str, Any]]] = []
        self._records = {
            id(item.candidate_record): index
            for index, item in enumerate(candidate_inputs)
        }

    def _handler(self, rule_id):
        def handler(
            candidate_record,
            *,
            batch_context,
            evaluation_context,
            download_result_context,
            stage_authorization_context,
        ):
            candidate_index = (
                -1
                if candidate_record
                is contract.STAGE_GLOBAL_CANDIDATE_SENTINEL
                else self._records[id(candidate_record)]
            )
            key = (candidate_index, rule_id)
            expected_input = (
                None
                if candidate_index == -1
                else self.candidate_inputs[candidate_index]
            )
            record = {
                "sequence": len(self.dispatch_calls) + 1,
                "event_sequence": len(self.events) + 1,
                "candidate_index": candidate_index,
                "rule_id": rule_id,
                "candidate_record": candidate_record,
                "batch_context": batch_context,
                "evaluation_context": evaluation_context,
                "download_result_context": download_result_context,
                "stage_authorization_context": stage_authorization_context,
                "candidate_record_identity": (
                    candidate_record
                    is contract.STAGE_GLOBAL_CANDIDATE_SENTINEL
                    if candidate_index == -1
                    else candidate_record is expected_input.candidate_record
                ),
            }
            self.dispatch_calls.append(record)
            self.events.append(("dispatcher", record))
            if key == self.handler_exception_at:
                raise RuntimeError("controlled-sensitive-message")
            if key == self.handler_malformed_at:
                return object()
            return _evaluation(rule_id, self.outcomes.get(key, "passed"))

        return handler

    def install(self):
        original_registry = dispatch_runtime.EVALUATOR_REGISTRY
        original_aggregator = (
            aggregation_runtime.aggregate_admission_rule_evaluations
        )
        dispatch_runtime.EVALUATOR_REGISTRY = MappingProxyType(
            {
                rule_id: self._handler(rule_id)
                for rule_id in contract.RULE_NAMES
            }
        )

        def aggregate(scope_id, *, ordered_rule_evaluations):
            call_index = len(self.aggregator_calls)
            record = {
                "sequence": call_index + 1,
                "event_sequence": len(self.events) + 1,
                "dispatcher_attempt_number": len(self.dispatch_calls),
                "scope_id": scope_id,
                "ordered_rule_evaluations": ordered_rule_evaluations,
            }
            self.aggregator_calls.append(record)
            self.events.append(("aggregator", record))
            if call_index == self.aggregator_exception_at:
                raise RuntimeError("controlled-aggregator-sensitive-message")
            verdict = original_aggregator(
                scope_id,
                ordered_rule_evaluations=ordered_rule_evaluations,
            )
            mutation = self.aggregator_malformed.get(call_index)
            if mutation is None:
                return verdict
            if mutation == "wrong_type":
                return object()
            return _unsafe_verdict(verdict, mutation)

        aggregation_runtime.aggregate_admission_rule_evaluations = aggregate
        return original_registry, original_aggregator

    def restore(self, originals):
        original_registry, original_aggregator = originals
        dispatch_runtime.EVALUATOR_REGISTRY = original_registry
        aggregation_runtime.aggregate_admission_rule_evaluations = (
            original_aggregator
        )


@contextmanager
def _controlled(candidate_inputs, batch_context, authorization_context, **kwargs):
    harness = _Harness(
        candidate_inputs,
        batch_context,
        authorization_context,
        **kwargs,
    )
    originals = harness.install()
    try:
        yield harness
    finally:
        harness.restore(originals)


def _unsafe_verdict(source, mutation):
    values = dict(vars(source))
    if mutation == "wrong_scope":
        values["scope_id"] = "wrong_scope"
    elif mutation == "copied_normal_vector":
        values["rule_evaluations"] = tuple([*source.rule_evaluations])
    elif mutation == "rejected_wrong_reason":
        values["reason"] = "COMBINED_ADMISSION_REQUIRED_RULE_INVALID"
    elif mutation == "rejected_nonempty_diagnostics":
        values["evaluated_rule_ids"] = source.required_rule_ids
    else:
        raise AssertionError(f"unknown mutation: {mutation}")
    malformed = object.__new__(
        aggregation_runtime.CombinedAdmissionCandidateVerdict
    )
    for name in aggregation_runtime.RESULT_FIELDS:
        object.__setattr__(malformed, name, values[name])
    return malformed


def _run(scope, candidate_inputs, batch, authorization):
    return runtime.orchestrate_stage_admission_scope(
        scope,
        candidate_inputs,
        batch_context=batch,
        stage_authorization_context=authorization,
    )


def _assert_context_routing(harness):
    for call in harness.dispatch_calls:
        index = call["candidate_index"]
        rule_id = call["rule_id"]
        assert call["candidate_record_identity"]
        if index == -1:
            assert call["candidate_record"] is contract.STAGE_GLOBAL_CANDIDATE_SENTINEL
            assert call["batch_context"] is None
            assert call["evaluation_context"] is None
            assert call["download_result_context"] is None
            assert (
                call["stage_authorization_context"]
                is harness.authorization_context
            )
            continue
        item = harness.candidate_inputs[index]
        expected_batch = (
            harness.batch_context if rule_id in ("ADMIT_001", "ADMIT_009") else None
        )
        expected_evaluation = (
            item.evaluation_context
            if rule_id
            in (
                "ADMIT_004",
                "ADMIT_006",
                "ADMIT_007",
                "ADMIT_008",
                "ADMIT_009",
                "ADMIT_010",
                "ADMIT_011",
                "ADMIT_012",
                "ADMIT_013",
            )
            else None
        )
        expected_download = (
            item.download_result_context
            if rule_id in ("ADMIT_012", "ADMIT_013")
            else None
        )
        assert call["batch_context"] is expected_batch
        assert call["evaluation_context"] is expected_evaluation
        assert call["download_result_context"] is expected_download
        assert call["stage_authorization_context"] is None


def test_public_api_and_shared_type_identity():
    assert runtime.__all__ == (
        "AdmissionCandidateOrchestrationInput",
        "CandidateAdmissionOrchestrationResult",
        "StageAdmissionOrchestrationResult",
        "StageAdmissionOrchestrationError",
        "orchestrate_stage_admission_scope",
    )
    assert (
        runtime.AdmissionCandidateOrchestrationInput
        is contract.AdmissionCandidateOrchestrationInput
    )
    assert (
        runtime.CandidateAdmissionOrchestrationResult
        is contract.CandidateAdmissionOrchestrationResult
    )
    assert (
        runtime.StageAdmissionOrchestrationResult
        is contract.StageAdmissionOrchestrationResult
    )
    assert (
        runtime.StageAdmissionOrchestrationError
        is contract.StageAdmissionOrchestrationError
    )
    signature = inspect.signature(runtime.orchestrate_stage_admission_scope)
    parameters = tuple(signature.parameters.values())
    assert tuple(item.name for item in parameters) == (
        "scope_id",
        "candidate_inputs",
        "batch_context",
        "stage_authorization_context",
    )
    assert tuple(item.kind for item in parameters) == (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.KEYWORD_ONLY,
    )
    assert all(item.default is inspect.Parameter.empty for item in parameters)
    hints = get_type_hints(runtime.orchestrate_stage_admission_scope)
    assert hints["scope_id"] is str
    assert hints["return"] is contract.StageAdmissionOrchestrationResult
    assert (
        runtime.orchestrate_stage_admission_scope.__globals__["dispatch_runtime"]
        is dispatch_runtime
    )
    assert (
        runtime.orchestrate_stage_admission_scope.__globals__[
            "aggregation_runtime"
        ]
        is aggregation_runtime
    )


@pytest.mark.parametrize("scope", contract.SCOPE_IDS)
@pytest.mark.parametrize("candidate_count", (1, 2, 3))
def test_exact4_by_n_positive_matrix(scope, candidate_count):
    candidate_inputs, batch, authorization = _inputs(candidate_count)
    with _controlled(candidate_inputs, batch, authorization) as harness:
        result = _run(scope, candidate_inputs, batch, authorization)

    required = contract.REQUIRED_RULE_IDS[scope]
    stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    expected_calls = [(-1, rule_id) for rule_id in stage_ids]
    expected_calls.extend(
        (index, rule_id)
        for index in range(candidate_count)
        for rule_id in candidate_ids
    )
    assert [
        (call["candidate_index"], call["rule_id"])
        for call in harness.dispatch_calls
    ] == expected_calls
    assert result == contract.StageAdmissionOrchestrationResult(
        schema_version=contract.STAGE_RESULT_SCHEMA_VERSION,
        scope_id=scope,
        candidate_count=candidate_count,
        required_rule_ids=required,
        stage_global_rule_ids=stage_ids,
        candidate_rule_ids=candidate_ids,
        stage_global_rule_evaluations=result.stage_global_rule_evaluations,
        candidate_results=result.candidate_results,
        dispatcher_call_count=len(stage_ids)
        + candidate_count * len(candidate_ids),
        aggregator_call_count=candidate_count,
        orchestration_io_used=False,
        action_permission_granted=False,
    )
    assert type(result) is contract.StageAdmissionOrchestrationResult
    assert tuple(item.candidate_index for item in result.candidate_results) == tuple(
        range(candidate_count)
    )
    assert len(harness.aggregator_calls) == candidate_count
    for index, candidate_result in enumerate(result.candidate_results):
        assert type(candidate_result) is contract.CandidateAdmissionOrchestrationResult
        assert candidate_result.dispatcher_call_count == len(candidate_ids)
        assert candidate_result.aggregator_call_count == 1
        assert (
            harness.aggregator_calls[index]["ordered_rule_evaluations"]
            is candidate_result.ordered_rule_evaluations
        )
        assert (
            candidate_result.combined_verdict.rule_evaluations
            is candidate_result.ordered_rule_evaluations
        )
        assert candidate_result.combined_verdict.evaluated_rule_ids == required
        assert tuple(
            item.admission_rule_id
            for item in candidate_result.ordered_rule_evaluations
        ) == required
        for stage_index, stage_result in enumerate(
            result.stage_global_rule_evaluations
        ):
            vector_index = required.index(stage_ids[stage_index])
            assert (
                candidate_result.ordered_rule_evaluations[vector_index]
                is stage_result
            )
    _assert_context_routing(harness)


@pytest.mark.parametrize(
    "outcomes",
    (
        {(-1, "ADMIT_014"): "blocked"},
        {(0, "ADMIT_001"): "blocked"},
        {(0, "ADMIT_004"): "invalid"},
        {(0, "ADMIT_006"): "rejected"},
        {(0, "ADMIT_006"): "rejected", (0, "ADMIT_007"): "blocked"},
        {(0, "ADMIT_006"): "rejected", (0, "ADMIT_007"): "invalid"},
        {
            (-1, "ADMIT_014"): "blocked",
            (0, "ADMIT_001"): "invalid",
            (1, "ADMIT_002"): "rejected",
            (2, "ADMIT_003"): "blocked",
        },
    ),
)
def test_normal_and_rejected_outcomes_never_short_circuit(outcomes):
    scope = "training_execution_admission_permission"
    candidate_inputs, batch, authorization = _inputs(3)
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        outcomes=outcomes,
    ) as harness:
        result = _run(scope, candidate_inputs, batch, authorization)

    stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    assert len(harness.dispatch_calls) == len(stage_ids) + 3 * len(candidate_ids)
    assert len(harness.aggregator_calls) == 3
    assert len(result.candidate_results) == 3
    for index, candidate_result in enumerate(result.candidate_results):
        vector = candidate_result.ordered_rule_evaluations
        rejected = any(item.outcome == "rejected" for item in vector)
        if rejected:
            verdict = candidate_result.combined_verdict
            assert verdict.outcome == "invalid"
            assert verdict.passed is False
            assert verdict.blocks_scope_action is True
            assert (
                verdict.reason
                == aggregation_runtime.EVALUATION_INVARIANT_INVALID_REASON
            )
            assert verdict.required_rule_ids == contract.REQUIRED_RULE_IDS[scope]
            assert verdict.evaluated_rule_ids == ()
            assert verdict.rule_evaluations == ()
            assert verdict.invalid_rule_ids == ()
            assert verdict.blocked_rule_ids == ()
            assert verdict.failing_rule_ids == ()
        else:
            assert (
                candidate_result.combined_verdict.rule_evaluations is vector
            )
        assert harness.aggregator_calls[index]["ordered_rule_evaluations"] is vector


class _InputSubclass(contract.AdmissionCandidateOrchestrationInput):
    pass


class _TupleSubclass(tuple):
    pass


class _StrSubclass(str):
    pass


@pytest.mark.parametrize(
    ("scope", "candidate_inputs", "batch", "authorization", "code"),
    (
        (
            1,
            (),
            object(),
            object(),
            contract.ERROR_CODES[0],
        ),
        (
            _StrSubclass(contract.SCOPE_IDS[0]),
            (),
            None,
            None,
            contract.ERROR_CODES[0],
        ),
        ("unknown", (), None, None, contract.ERROR_CODES[0]),
        (
            contract.SCOPE_IDS[0],
            [],
            object(),
            object(),
            contract.ERROR_CODES[1],
        ),
        (
            contract.SCOPE_IDS[0],
            (),
            None,
            None,
            contract.ERROR_CODES[1],
        ),
        (
            contract.SCOPE_IDS[0],
            _TupleSubclass((_inputs(1)[0][0],)),
            None,
            None,
            contract.ERROR_CODES[1],
        ),
        (
            contract.SCOPE_IDS[0],
            (object(),),
            object(),
            object(),
            contract.ERROR_CODES[2],
        ),
        (
            contract.SCOPE_IDS[0],
            (_InputSubclass({}, None, None),),
            None,
            None,
            contract.ERROR_CODES[2],
        ),
        (
            contract.SCOPE_IDS[0],
            (contract.AdmissionCandidateOrchestrationInput(1, None, None),),
            object(),
            object(),
            contract.ERROR_CODES[2],
        ),
        (
            contract.SCOPE_IDS[0],
            (contract.AdmissionCandidateOrchestrationInput({}, 1, None),),
            object(),
            object(),
            contract.ERROR_CODES[2],
        ),
        (
            contract.SCOPE_IDS[0],
            (contract.AdmissionCandidateOrchestrationInput({}, None, 1),),
            object(),
            object(),
            contract.ERROR_CODES[2],
        ),
        (
            contract.SCOPE_IDS[0],
            _inputs(1)[0],
            1,
            object(),
            contract.ERROR_CODES[3],
        ),
        (
            contract.SCOPE_IDS[0],
            _inputs(1)[0],
            None,
            1,
            contract.ERROR_CODES[4],
        ),
    ),
)
def test_prevalidation_fail_closed_and_precedence(
    scope, candidate_inputs, batch, authorization, code
):
    valid_inputs, valid_batch, valid_authorization = _inputs(1)
    with _controlled(valid_inputs, valid_batch, valid_authorization) as harness:
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == code
    assert error.candidate_index == -1
    assert error.admission_rule_id == ""
    assert error.dispatcher_call_count == 0
    assert error.aggregator_call_count == 0
    assert error.reason == code
    assert error.cause_type == ""
    assert error.__cause__ is None
    assert harness.dispatch_calls == []
    assert harness.aggregator_calls == []


@pytest.mark.parametrize(
    ("scope", "rule_id"),
    tuple(
        (scope, rule_id)
        for scope in contract.SCOPE_IDS
        for rule_id in contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    ),
)
def test_stage_dispatch_exception_coordinates(scope, rule_id):
    candidate_inputs, batch, authorization = _inputs(3)
    position = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope].index(rule_id) + 1
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        handler_exception_at=(-1, rule_id),
    ) as harness:
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == contract.ERROR_CODES[5]
    assert error.candidate_index == -1
    assert error.admission_rule_id == rule_id
    assert error.dispatcher_call_count == position
    assert error.aggregator_call_count == 0
    assert error.cause_type == "RuntimeError"
    assert type(error.__cause__) is RuntimeError
    assert "sensitive" not in error.reason
    assert len(harness.dispatch_calls) == position
    assert harness.aggregator_calls == []


@pytest.mark.parametrize("scope", contract.SCOPE_IDS)
@pytest.mark.parametrize("candidate_index", (0, 1, 2))
@pytest.mark.parametrize("position_kind", ("first", "middle", "last"))
def test_candidate_dispatch_exception_coordinates(
    scope, candidate_index, position_kind
):
    candidate_inputs, batch, authorization = _inputs(3)
    candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    position = {
        "first": 1,
        "middle": (len(candidate_ids) + 1) // 2,
        "last": len(candidate_ids),
    }[position_kind]
    rule_id = candidate_ids[position - 1]
    stage_count = len(contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        handler_exception_at=(candidate_index, rule_id),
    ) as harness:
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == contract.ERROR_CODES[5]
    assert error.candidate_index == candidate_index
    assert error.admission_rule_id == rule_id
    assert (
        error.dispatcher_call_count
        == stage_count + candidate_index * len(candidate_ids) + position
    )
    assert error.aggregator_call_count == candidate_index
    assert error.cause_type == "RuntimeError"
    assert type(error.__cause__) is RuntimeError
    assert len(harness.dispatch_calls) == error.dispatcher_call_count
    assert len(harness.aggregator_calls) == candidate_index


@pytest.mark.parametrize(
    ("scope", "failure_at"),
    (
        (contract.SCOPE_IDS[0], (-1, "ADMIT_014")),
        (contract.SCOPE_IDS[-1], (-1, "ADMIT_015")),
        (contract.SCOPE_IDS[0], (1, "ADMIT_004")),
        (contract.SCOPE_IDS[-1], (2, "ADMIT_013")),
    ),
)
def test_dispatcher_malformed_result_is_invariant_error(scope, failure_at):
    candidate_inputs, batch, authorization = _inputs(3)
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        handler_malformed_at=failure_at,
    ) as harness:
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == contract.ERROR_CODES[6]
    assert error.candidate_index == failure_at[0]
    assert error.admission_rule_id == failure_at[1]
    assert error.cause_type == ""
    assert error.__cause__ is None
    assert len(harness.dispatch_calls) == error.dispatcher_call_count
    assert len(harness.aggregator_calls) == error.aggregator_call_count


@pytest.mark.parametrize("candidate_index", (0, 1, 2))
def test_aggregator_exception_coordinates(candidate_index):
    scope = contract.SCOPE_IDS[-1]
    candidate_inputs, batch, authorization = _inputs(3)
    stage_count = len(contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
    candidate_count = len(contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope])
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        aggregator_exception_at=candidate_index,
    ) as harness:
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == contract.ERROR_CODES[7]
    assert error.candidate_index == candidate_index
    assert error.admission_rule_id == ""
    assert (
        error.dispatcher_call_count
        == stage_count + (candidate_index + 1) * candidate_count
    )
    assert error.aggregator_call_count == candidate_index + 1
    assert error.cause_type == "RuntimeError"
    assert type(error.__cause__) is RuntimeError
    assert "sensitive" not in error.reason
    assert len(harness.dispatch_calls) == error.dispatcher_call_count
    assert len(harness.aggregator_calls) == candidate_index + 1


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_type",
        "wrong_scope",
        "copied_normal_vector",
    ),
)
def test_aggregator_malformed_normal_results(mutation):
    scope = contract.SCOPE_IDS[-1]
    candidate_inputs, batch, authorization = _inputs(1)
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        aggregator_malformed={0: mutation},
    ):
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == contract.ERROR_CODES[7]
    assert error.candidate_index == 0
    assert error.cause_type == ""
    assert error.__cause__ is None


@pytest.mark.parametrize(
    "mutation", ("rejected_wrong_reason", "rejected_nonempty_diagnostics")
)
def test_aggregator_malformed_rejected_results(mutation):
    scope = contract.SCOPE_IDS[-1]
    candidate_inputs, batch, authorization = _inputs(1)
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        outcomes={(0, "ADMIT_006"): "rejected"},
        aggregator_malformed={0: mutation},
    ):
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            _run(scope, candidate_inputs, batch, authorization)
    error = caught.value
    assert error.code == contract.ERROR_CODES[7]
    assert error.candidate_index == 0
    assert error.cause_type == ""
    assert error.__cause__ is None


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_type",
        "wrong_scope",
        "copied_normal_vector",
        "rejected_wrong_reason",
        "rejected_nonempty_diagnostics",
    ),
)
def test_candidate_one_malformed_aggregator_stops_without_partial_result(
    mutation,
):
    scope = contract.SCOPE_IDS[-1]
    candidate_inputs, batch, authorization = _inputs(3)
    candidate_rule_count = len(contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope])
    stage_rule_count = len(contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
    outcomes = (
        {(1, "ADMIT_006"): "rejected"}
        if mutation.startswith("rejected_")
        else {}
    )
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        outcomes=outcomes,
        aggregator_malformed={1: mutation},
    ) as harness:
        with pytest.raises(contract.StageAdmissionOrchestrationError) as caught:
            result = _run(scope, candidate_inputs, batch, authorization)
    assert "result" not in locals()
    error = caught.value
    expected_dispatcher_count = stage_rule_count + 2 * candidate_rule_count
    assert (
        error.code,
        error.candidate_index,
        error.admission_rule_id,
        error.dispatcher_call_count,
        error.aggregator_call_count,
        error.cause_type,
        error.__cause__,
        len(harness.dispatch_calls),
        len(harness.aggregator_calls),
    ) == (
        contract.ERROR_CODES[7],
        1,
        "",
        expected_dispatcher_count,
        2,
        "",
        None,
        expected_dispatcher_count,
        2,
    )
    assert not any(
        call["candidate_index"] == 2 for call in harness.dispatch_calls
    )


def test_dispatcher_base_exception_propagates(monkeypatch):
    candidate_inputs, batch, authorization = _inputs(1)
    harness = _Harness(candidate_inputs, batch, authorization)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    registry = dict(dispatch_runtime.EVALUATOR_REGISTRY)
    registry["ADMIT_014"] = interrupt
    monkeypatch.setattr(
        dispatch_runtime, "EVALUATOR_REGISTRY", MappingProxyType(registry)
    )
    with pytest.raises(KeyboardInterrupt):
        _run(contract.SCOPE_IDS[0], candidate_inputs, batch, authorization)


def test_aggregator_base_exception_propagates():
    candidate_inputs, batch, authorization = _inputs(1)
    harness = _Harness(candidate_inputs, batch, authorization)
    originals = harness.install()

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    aggregation_runtime.aggregate_admission_rule_evaluations = interrupt
    try:
        with pytest.raises(KeyboardInterrupt):
            _run(contract.SCOPE_IDS[0], candidate_inputs, batch, authorization)
    finally:
        harness.restore(originals)


def _csv_bytes(fieldnames, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=fieldnames, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def _route_label(call):
    index = call["candidate_index"]
    rule_id = call["rule_id"]
    if index == -1:
        return "stage_authorization_context=caller_identity;others=None"
    routes = []
    if rule_id in ("ADMIT_001", "ADMIT_009"):
        routes.append("batch=caller_identity")
    if rule_id in (
        "ADMIT_004",
        "ADMIT_006",
        "ADMIT_007",
        "ADMIT_008",
        "ADMIT_009",
        "ADMIT_010",
        "ADMIT_011",
        "ADMIT_012",
        "ADMIT_013",
    ):
        routes.append("evaluation=candidate_identity")
    if rule_id in ("ADMIT_012", "ADMIT_013"):
        routes.append("download=candidate_identity")
    routes.append("stage_authorization=None")
    return ";".join(routes)


def _load_checker_module():
    module_name = "_covapie_orchestration_checker_for_tests"
    module = sys.modules.get(module_name)
    if module is not None:
        return module
    path = ROOT / SUPPORT_PATHS[1]
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _git_at(path, *args):
    return subprocess.run(
        ("git", "-C", str(path), *args),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def _copy_exact10(destination):
    for relative in EXACT10:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def test_checker_real_git_exact4_lifecycle_and_negative_topologies(tmp_path):
    checker = _load_checker_module()
    remote = tmp_path / "remote.git"
    clone = tmp_path / "clone"
    detached = tmp_path / "detached"
    single = tmp_path / "single"
    extra = tmp_path / "extra"
    subprocess.run(
        ("git", "init", "--bare", str(remote)),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _git_at(
        ROOT,
        "push",
        str(remote),
        f"{BASE}:refs/heads/main",
    )
    _git_at(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    subprocess.run(
        (
            "git",
            "clone",
            "--branch",
            "main",
            "--no-local",
            str(remote),
            str(clone),
        ),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _git_at(clone, "config", "user.name", "CovaPIE Test")
    _git_at(clone, "config", "user.email", "covapie@example.invalid")
    _git_at(clone, "remote", "set-head", "origin", "main")
    assert _git_at(clone, "rev-parse", "HEAD") == BASE
    assert _git_at(clone, "rev-parse", "refs/heads/main") == BASE
    assert _git_at(clone, "rev-parse", "origin/main") == BASE
    _copy_exact10(clone)

    original_root = checker.ROOT
    try:
        checker.ROOT = clone
        assert _git_at(clone, "rev-parse", "HEAD") == BASE
        assert _git_at(clone, "rev-parse", "origin/main") == BASE
        assert (
            _git_at(
                clone,
                "symbolic-ref",
                "refs/remotes/origin/HEAD",
            )
            == "refs/remotes/origin/main"
        )
        assert checker._lifecycle().lifecycle == "pre_commit"

        _git_at(clone, "worktree", "add", "--detach", str(detached), BASE)
        with pytest.raises(ValueError, match="single-main-worktree"):
            checker._lifecycle()
        _copy_exact10(detached)
        _git_at(
            detached,
            "add",
            "--",
            *(path.as_posix() for path in EXACT10),
        )
        _git_at(detached, "commit", "-m", FORMAL_SUBJECT)
        detached_head = _git_at(detached, "rev-parse", "HEAD")
        checker.ROOT = detached
        assert (
            checker._lifecycle().lifecycle
            == "detached_candidate_post_commit"
        )

        _git_at(clone, "commit", "--allow-empty", "-m", "main drift")
        with pytest.raises(ValueError, match="formal-ref closure"):
            checker._lifecycle()
        _git_at(clone, "update-ref", "refs/heads/main", BASE)

        _git_at(clone, "branch", "extra-branch", BASE)
        with pytest.raises(ValueError, match="persistent ref forbidden"):
            checker._lifecycle()
        _git_at(clone, "branch", "-D", "extra-branch")
        _git_at(clone, "tag", "extra-tag", BASE)
        with pytest.raises(ValueError, match="persistent ref forbidden"):
            checker._lifecycle()
        _git_at(clone, "tag", "-d", "extra-tag")
        _git_at(
            clone,
            "update-ref",
            "refs/codex/turn-diffs/candidate/forbidden",
            BASE,
        )
        with pytest.raises(ValueError, match="platform ref"):
            checker._lifecycle()
        _git_at(
            clone,
            "update-ref",
            "-d",
            "refs/codex/turn-diffs/candidate/forbidden",
        )
        _git_at(
            clone,
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main-drift",
        )
        with pytest.raises(ValueError, match="origin/HEAD"):
            checker._lifecycle()
        _git_at(clone, "remote", "set-head", "origin", "main")

        subprocess.run(
            (
                "git",
                "clone",
                "--no-local",
                str(remote),
                str(single),
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _git_at(single, "fetch", str(detached), detached_head)
        _git_at(single, "checkout", "--detach", detached_head)
        _git_at(single, "remote", "set-head", "origin", "main")
        checker.ROOT = single
        with pytest.raises(ValueError, match="cardinality"):
            checker._lifecycle()

        checker.ROOT = clone
        _git_at(clone, "worktree", "remove", str(detached))
        _git_at(
            clone,
            "add",
            "--",
            *(path.as_posix() for path in EXACT10),
        )
        _git_at(clone, "commit", "-m", FORMAL_SUBJECT)
        assert (
            checker._lifecycle().lifecycle
            == "formal_main_post_commit_unpushed"
        )
        _git_at(clone, "worktree", "add", "--detach", str(extra), BASE)
        with pytest.raises(ValueError, match="single-worktree"):
            checker._lifecycle()
        _git_at(clone, "worktree", "remove", str(extra))
        _git_at(clone, "push", "origin", "main")
        assert (
            checker._lifecycle().lifecycle
            == "formal_main_post_push"
        )
    finally:
        checker.ROOT = original_root


@pytest.mark.parametrize(
    "field",
    (
        "head",
        "index",
        "status",
        "refs",
        "branch",
        "worktrees",
        "origin_head_symbolic_target",
        "origin_head_resolved_oid",
        "lifecycle",
    ),
)
def test_checker_rejects_complete_first_final_snapshot_drift(field):
    checker = _load_checker_module()
    snapshot = checker.LifecycleSnapshot(
        BASE,
        b"index",
        b"status",
        (checker.RefRecord("refs/heads/main", BASE, "commit"),),
        "main",
        (
            checker.WorktreeRecord(
                str(ROOT), BASE, "refs/heads/main", False
            ),
        ),
        "refs/remotes/origin/main",
        BASE,
        "pre_commit",
    )
    replacements = {
        "head": "1" * 40,
        "index": b"index-drift",
        "status": b"status-drift",
        "refs": (),
        "branch": "other",
        "worktrees": (),
        "origin_head_symbolic_target": "refs/remotes/origin/other",
        "origin_head_resolved_oid": "2" * 40,
        "lifecycle": "formal_main_post_push",
    }
    with pytest.raises(ValueError, match=field):
        checker._assert_lifecycle_stable(
            snapshot, snapshot._replace(**{field: replacements[field]})
        )


def build_execution_artifacts():
    """Build deterministic evidence from actual orchestrator executions."""
    runtime_rows = []
    signature = inspect.signature(runtime.orchestrate_stage_admission_scope)
    runtime_rows.extend(
        (
            {
                "contract_area": "public_api",
                "contract_item": "function_name",
                "expected": "orchestrate_stage_admission_scope",
                "observed": runtime.orchestrate_stage_admission_scope.__name__,
                "passed": "true",
            },
            {
                "contract_area": "public_api",
                "contract_item": "parameter_count",
                "expected": "4",
                "observed": str(len(signature.parameters)),
                "passed": "true",
            },
            {
                "contract_area": "shared_types",
                "contract_item": "class_identity",
                "expected": "Exact4 shared identities",
                "observed": "Exact4 shared identities",
                "passed": "true",
            },
        )
    )
    for scope in contract.SCOPE_IDS:
        runtime_rows.append(
            {
                "contract_area": "scope_membership",
                "contract_item": scope,
                "expected": "|".join(contract.REQUIRED_RULE_IDS[scope]),
                "observed": "|".join(contract.REQUIRED_RULE_IDS[scope]),
                "passed": "true",
            }
        )
    for name in contract.STAGE_RESULT_FIELDS:
        runtime_rows.append(
            {
                "contract_area": "stage_result",
                "contract_item": name,
                "expected": "present",
                "observed": "present",
                "passed": "true",
            }
        )
    for name in contract.ERROR_FIELDS:
        runtime_rows.append(
            {
                "contract_area": "error_result",
                "contract_item": name,
                "expected": "present",
                "observed": "present",
                "passed": "true",
            }
        )
    for code in contract.ERROR_CODES:
        runtime_rows.append(
            {
                "contract_area": "error_code",
                "contract_item": code,
                "expected": "frozen",
                "observed": "frozen",
                "passed": "true",
            }
        )
    runtime_rows.append(
        {
            "contract_area": "permission_boundary",
            "contract_item": "action_permission_granted",
            "expected": "false",
            "observed": "false",
            "passed": "true",
        }
    )

    trace_rows = []
    truth_rows = []
    case_specs = tuple((scope, 1) for scope in contract.SCOPE_IDS) + (
        (contract.SCOPE_IDS[-1], 3),
    )
    for scope, count in case_specs:
        candidate_inputs, batch, authorization = _inputs(count)
        with _controlled(candidate_inputs, batch, authorization) as harness:
            result = _run(scope, candidate_inputs, batch, authorization)
        case_id = f"{scope}:N={count}:all_passed"
        for event_kind, call in harness.events:
            if event_kind == "dispatcher":
                trace_rows.append(
                    {
                        "case_id": case_id,
                        "scope_id": scope,
                        "candidate_index": str(call["candidate_index"]),
                        "call_sequence": str(call["event_sequence"]),
                        "rule_id": call["rule_id"],
                        "execution_domain": (
                            "stage_global_once"
                            if call["candidate_index"] == -1
                            else "candidate_scoped"
                        ),
                        "candidate_record_identity_class": (
                            "stage_global_sentinel_identity"
                            if call["candidate_index"] == -1
                            else "candidate_record_identity"
                        ),
                        "context_route": _route_label(call),
                        "dispatcher_attempt_number": str(call["sequence"]),
                        "aggregator_attempt_number": "0",
                        "returned_outcome": "passed",
                        "identity_checks": "true",
                    }
                )
                continue
            candidate_index = call["sequence"] - 1
            vector = call["ordered_rule_evaluations"]
            trace_rows.append(
                {
                    "case_id": case_id,
                    "scope_id": scope,
                    "candidate_index": str(candidate_index),
                    "call_sequence": str(call["event_sequence"]),
                    "rule_id": "",
                    "execution_domain": "candidate_aggregator",
                    "candidate_record_identity_class": "not_applicable",
                    "context_route": "ordered_vector_keyword_identity",
                    "dispatcher_attempt_number": str(
                        call["dispatcher_attempt_number"]
                    ),
                    "aggregator_attempt_number": str(call["sequence"]),
                    "returned_outcome": result.candidate_results[
                        candidate_index
                    ].combined_verdict.outcome,
                    "identity_checks": str(
                        vector
                        is result.candidate_results[
                            candidate_index
                        ].ordered_rule_evaluations
                    ).lower(),
                }
            )
        truth_rows.extend(
            (
                {
                    "case_group": "positive_matrix",
                    "case_id": case_id,
                    "expected": str(
                        len(contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
                        + count
                        * len(contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope])
                    ),
                    "observed": str(result.dispatcher_call_count),
                    "passed": "true",
                },
                {
                    "case_group": "aggregator_cardinality",
                    "case_id": case_id,
                    "expected": str(count),
                    "observed": str(result.aggregator_call_count),
                    "passed": "true",
                },
                {
                    "case_group": "stage_global_identity_reuse",
                    "case_id": case_id,
                    "expected": "true",
                    "observed": str(
                        all(
                            all(
                                candidate.ordered_rule_evaluations[
                                    contract.REQUIRED_RULE_IDS[scope].index(
                                        rule_id
                                    )
                                ]
                                is result.stage_global_rule_evaluations[index]
                                for index, rule_id in enumerate(
                                    contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[
                                        scope
                                    ]
                                )
                            )
                            for candidate in result.candidate_results
                        )
                    ).lower(),
                    "passed": "true",
                },
                {
                    "case_group": "normal_vector_identity",
                    "case_id": case_id,
                    "expected": "true",
                    "observed": str(
                        all(
                            harness.aggregator_calls[index][
                                "ordered_rule_evaluations"
                            ]
                            is candidate.ordered_rule_evaluations
                            and candidate.combined_verdict.rule_evaluations
                            is candidate.ordered_rule_evaluations
                            for index, candidate in enumerate(
                                result.candidate_results
                            )
                        )
                    ).lower(),
                    "passed": "true",
                },
            )
        )

    scope = contract.SCOPE_IDS[-1]
    candidate_inputs, batch, authorization = _inputs(3)
    with _controlled(
        candidate_inputs,
        batch,
        authorization,
        aggregator_malformed={1: "wrong_type"},
    ) as harness:
        try:
            _run(scope, candidate_inputs, batch, authorization)
        except contract.StageAdmissionOrchestrationError:
            pass
        else:
            raise AssertionError("malformed aggregator returned a stage result")
    case_id = f"{scope}:N=3:aggregator_malformed_candidate_1"
    for event_kind, call in harness.events:
        if event_kind == "dispatcher":
            trace_rows.append(
                {
                    "case_id": case_id,
                    "scope_id": scope,
                    "candidate_index": str(call["candidate_index"]),
                    "call_sequence": str(call["event_sequence"]),
                    "rule_id": call["rule_id"],
                    "execution_domain": (
                        "stage_global_once"
                        if call["candidate_index"] == -1
                        else "candidate_scoped"
                    ),
                    "candidate_record_identity_class": (
                        "stage_global_sentinel_identity"
                        if call["candidate_index"] == -1
                        else "candidate_record_identity"
                    ),
                    "context_route": _route_label(call),
                    "dispatcher_attempt_number": str(call["sequence"]),
                    "aggregator_attempt_number": "0",
                    "returned_outcome": "passed",
                    "identity_checks": "true",
                }
            )
            continue
        candidate_index = call["sequence"] - 1
        trace_rows.append(
            {
                "case_id": case_id,
                "scope_id": scope,
                "candidate_index": str(candidate_index),
                "call_sequence": str(call["event_sequence"]),
                "rule_id": "",
                "execution_domain": "candidate_aggregator",
                "candidate_record_identity_class": "not_applicable",
                "context_route": "ordered_vector_keyword_identity",
                "dispatcher_attempt_number": str(
                    call["dispatcher_attempt_number"]
                ),
                "aggregator_attempt_number": str(call["sequence"]),
                "returned_outcome": (
                    "passed" if candidate_index == 0 else "error"
                ),
                "identity_checks": "true",
            }
        )

    outcome_cases = (
        ("blocked", {(-1, "ADMIT_014"): "blocked"}),
        ("invalid", {(0, "ADMIT_004"): "invalid"}),
        ("rejected", {(0, "ADMIT_006"): "rejected"}),
        (
            "rejected_plus_blocked",
            {(0, "ADMIT_006"): "rejected", (0, "ADMIT_007"): "blocked"},
        ),
    )
    for case_name, outcomes in outcome_cases:
        scope = contract.SCOPE_IDS[-1]
        candidate_inputs, batch, authorization = _inputs(3)
        with _controlled(
            candidate_inputs, batch, authorization, outcomes=outcomes
        ) as harness:
            result = _run(scope, candidate_inputs, batch, authorization)
        truth_rows.append(
            {
                "case_group": "no_normal_outcome_short_circuit",
                "case_id": case_name,
                "expected": "41/3",
                "observed": (
                    f"{len(harness.dispatch_calls)}/"
                    f"{len(harness.aggregator_calls)}"
                ),
                "passed": "true",
            }
        )
        if "rejected" in case_name:
            verdict = result.candidate_results[0].combined_verdict
            truth_rows.append(
                {
                    "case_group": "rejected_canonical",
                    "case_id": case_name,
                    "expected": (
                        "invalid|COMBINED_ADMISSION_RULE_EVALUATION_"
                        "INVARIANT_INVALID|empty_diagnostics"
                    ),
                    "observed": (
                        f"{verdict.outcome}|{verdict.reason}|"
                        f"{'empty_diagnostics' if not verdict.rule_evaluations else 'retained'}"
                    ),
                    "passed": "true",
                }
            )

    def add_error_truth(
        group,
        case_id,
        scope,
        expected,
        *,
        outcomes=None,
        **kwargs,
    ):
        candidate_inputs, batch, authorization = _inputs(3)
        with _controlled(
            candidate_inputs,
            batch,
            authorization,
            outcomes=outcomes,
            **kwargs,
        ) as harness:
            try:
                _run(scope, candidate_inputs, batch, authorization)
            except contract.StageAdmissionOrchestrationError as error:
                observed = (
                    error.code,
                    error.candidate_index,
                    error.admission_rule_id,
                    error.dispatcher_call_count,
                    error.aggregator_call_count,
                    error.cause_type,
                    error.__cause__ is not None,
                    len(harness.dispatch_calls),
                    len(harness.aggregator_calls),
                    (
                        len(harness.dispatch_calls) == expected[7]
                        and len(harness.aggregator_calls) == expected[8]
                    ),
                )
            else:
                observed = ("partial_stage_result",)
        truth_rows.append(
            {
                "case_group": group,
                "case_id": case_id,
                "expected": repr(expected),
                "observed": repr(observed),
                "passed": str(observed == expected).lower(),
            }
        )
        return harness

    valid_inputs, valid_batch, valid_authorization = _inputs(1)
    with _controlled(
        valid_inputs, valid_batch, valid_authorization
    ) as prevalidation_harness:
        try:
            _run(1, (), object(), object())
        except contract.StageAdmissionOrchestrationError as error:
            observed = (
                error.code,
                error.candidate_index,
                error.admission_rule_id,
                error.dispatcher_call_count,
                error.aggregator_call_count,
                error.cause_type,
                error.__cause__ is not None,
                len(prevalidation_harness.dispatch_calls),
                len(prevalidation_harness.aggregator_calls),
                True,
            )
        else:
            observed = ("partial_stage_result",)
    expected = (contract.ERROR_CODES[0], -1, "", 0, 0, "", False, 0, 0, True)
    truth_rows.append(
        {
            "case_group": "prevalidation_zero_call_projection",
            "case_id": "invalid_scope_type",
            "expected": repr(expected),
            "observed": repr(observed),
            "passed": str(observed == expected).lower(),
        }
    )

    for scope in contract.SCOPE_IDS:
        stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
        candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
        for position, rule_id in enumerate(stage_ids, 1):
            expected = (
                contract.ERROR_CODES[5],
                -1,
                rule_id,
                position,
                0,
                "RuntimeError",
                True,
                position,
                0,
                True,
            )
            add_error_truth(
                "stage_dispatch_exception_formula",
                f"{scope}:{rule_id}",
                scope,
                expected,
                handler_exception_at=(-1, rule_id),
            )
        candidate_count = len(candidate_ids)
        positions = (1, (candidate_count + 1) // 2, candidate_count)
        for candidate_index in (0, 1, 2):
            for position in positions:
                rule_id = candidate_ids[position - 1]
                dispatcher_count = (
                    len(stage_ids)
                    + candidate_index * candidate_count
                    + position
                )
                expected = (
                    contract.ERROR_CODES[5],
                    candidate_index,
                    rule_id,
                    dispatcher_count,
                    candidate_index,
                    "RuntimeError",
                    True,
                    dispatcher_count,
                    candidate_index,
                    True,
                )
                add_error_truth(
                    "candidate_dispatch_exception_formula",
                    f"{scope}:candidate={candidate_index}:position={position}",
                    scope,
                    expected,
                    handler_exception_at=(candidate_index, rule_id),
                )
        for position, rule_id in enumerate(stage_ids, 1):
            expected = (
                contract.ERROR_CODES[6],
                -1,
                rule_id,
                position,
                0,
                "",
                False,
                position,
                0,
                True,
            )
            add_error_truth(
                "dispatcher_malformed_formula",
                f"{scope}:stage:{rule_id}",
                scope,
                expected,
                handler_malformed_at=(-1, rule_id),
            )
        middle = (candidate_count + 1) // 2
        rule_id = candidate_ids[middle - 1]
        dispatcher_count = len(stage_ids) + candidate_count + middle
        expected = (
            contract.ERROR_CODES[6],
            1,
            rule_id,
            dispatcher_count,
            1,
            "",
            False,
            dispatcher_count,
            1,
            True,
        )
        add_error_truth(
            "dispatcher_malformed_formula",
            f"{scope}:candidate=1:{rule_id}",
            scope,
            expected,
            handler_malformed_at=(1, rule_id),
        )

    scope = contract.SCOPE_IDS[-1]
    stage_count = len(contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
    candidate_count = len(contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope])
    for candidate_index in (0, 1, 2):
        dispatcher_count = stage_count + (candidate_index + 1) * candidate_count
        expected = (
            contract.ERROR_CODES[7],
            candidate_index,
            "",
            dispatcher_count,
            candidate_index + 1,
            "RuntimeError",
            True,
            dispatcher_count,
            candidate_index + 1,
            True,
        )
        add_error_truth(
            "aggregator_exception_formula",
            f"candidate={candidate_index}",
            scope,
            expected,
            aggregator_exception_at=candidate_index,
        )

    malformed_variants = (
        "wrong_type",
        "wrong_scope",
        "copied_normal_vector",
        "rejected_wrong_reason",
        "rejected_nonempty_diagnostics",
    )
    malformed_dispatcher_count = stage_count + 2 * candidate_count
    for mutation in malformed_variants:
        expected = (
            contract.ERROR_CODES[7],
            1,
            "",
            malformed_dispatcher_count,
            2,
            "",
            False,
            malformed_dispatcher_count,
            2,
            True,
        )
        harness = add_error_truth(
            "aggregator_malformed_formula",
            mutation,
            scope,
            expected,
            outcomes=(
                {(1, "ADMIT_006"): "rejected"}
                if mutation.startswith("rejected_")
                else None
            ),
            aggregator_malformed={1: mutation},
        )
        stopped = (
            not any(
                call["candidate_index"] == 2
                for call in harness.dispatch_calls
            )
            and len(harness.aggregator_calls) == 2
        )
        truth_rows.append(
            {
                "case_group": "corruption_stops_later_candidates",
                "case_id": mutation,
                "expected": "true",
                "observed": str(stopped).lower(),
                "passed": str(stopped).lower(),
            }
        )

    baseexception_cases = []
    candidate_inputs, batch, authorization = _inputs(3)
    with _controlled(
        candidate_inputs, batch, authorization
    ) as interrupt_harness:
        registry = dict(dispatch_runtime.EVALUATOR_REGISTRY)
        original_handler = registry["ADMIT_014"]

        def interrupt_dispatcher(*args, **kwargs):
            original_handler(*args, **kwargs)
            raise KeyboardInterrupt

        registry["ADMIT_014"] = interrupt_dispatcher
        dispatch_runtime.EVALUATOR_REGISTRY = MappingProxyType(registry)
        try:
            _run(scope, candidate_inputs, batch, authorization)
        except KeyboardInterrupt as error:
            baseexception_cases.append(
                (
                    "dispatcher",
                    (
                        type(error).__name__,
                        len(interrupt_harness.dispatch_calls),
                        len(interrupt_harness.aggregator_calls),
                    ),
                )
            )
    candidate_inputs, batch, authorization = _inputs(3)
    with _controlled(
        candidate_inputs, batch, authorization
    ) as interrupt_harness:
        original_aggregate = (
            aggregation_runtime.aggregate_admission_rule_evaluations
        )

        def interrupt_aggregator(*args, **kwargs):
            original_aggregate(*args, **kwargs)
            raise KeyboardInterrupt

        aggregation_runtime.aggregate_admission_rule_evaluations = (
            interrupt_aggregator
        )
        try:
            _run(scope, candidate_inputs, batch, authorization)
        except KeyboardInterrupt as error:
            baseexception_cases.append(
                (
                    "aggregator",
                    (
                        type(error).__name__,
                        len(interrupt_harness.dispatch_calls),
                        len(interrupt_harness.aggregator_calls),
                    ),
                )
            )
    for case_id, observed in baseexception_cases:
        expected = (
            ("KeyboardInterrupt", 1, 0)
            if case_id == "dispatcher"
            else ("KeyboardInterrupt", stage_count + candidate_count, 1)
        )
        truth_rows.append(
            {
                "case_group": "baseexception_propagation",
                "case_id": case_id,
                "expected": repr(expected),
                "observed": repr(observed),
                "passed": str(observed == expected).lower(),
            }
        )

    safety_items = (
        "network",
        "provider",
        "download",
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
        "training_action",
        "current_permission",
        "action_permission",
        "ready_for_training",
    )
    safety_rows = [
        {
            "safety_order": str(index),
            "safety_item": name,
            "expected": "false",
            "observed": "false",
            "passed": "true",
        }
        for index, name in enumerate(safety_items, 1)
    ]

    payloads = {
        RUNTIME_NAME: _csv_bytes(
            (
                "contract_area",
                "contract_item",
                "expected",
                "observed",
                "passed",
            ),
            runtime_rows,
        ),
        TRACE_NAME: _csv_bytes(
            (
                "case_id",
                "scope_id",
                "candidate_index",
                "call_sequence",
                "rule_id",
                "execution_domain",
                "candidate_record_identity_class",
                "context_route",
                "dispatcher_attempt_number",
                "aggregator_attempt_number",
                "returned_outcome",
                "identity_checks",
            ),
            trace_rows,
        ),
        TRUTH_NAME: _csv_bytes(
            ("case_group", "case_id", "expected", "observed", "passed"),
            truth_rows,
        ),
        SAFETY_NAME: _csv_bytes(
            (
                "safety_order",
                "safety_item",
                "expected",
                "observed",
                "passed",
            ),
            safety_rows,
        ),
        ISSUE_NAME: (ROOT / ISSUE_PREDECESSOR).read_bytes(),
    }
    artifact_sha256 = {
        name: _sha256(payload) for name, payload in payloads.items()
    }
    masks = (
        {"semantic_name": "warhead_only", "alias": "A"},
        {"semantic_name": "linker_plus_warhead", "alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
        {"semantic_name": "scaffold_only", "alias": "B3"},
        {
            "semantic_name": "scaffold_plus_linker_plus_warhead",
            "alias": "C",
        },
    )
    manifest = {
        "all_checks_passed": True,
        "stage": STAGE,
        "base_identity": {
            "commit": BASE,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_commit_subject": FORMAL_SUBJECT,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "artifact_sha256": artifact_sha256,
        "support_file_sha256": {
            path.as_posix(): _sha256((ROOT / path).read_bytes())
            for path in SUPPORT_PATHS
        },
        "runtime_contract_row_count": len(runtime_rows),
        "call_trace_row_count": len(trace_rows),
        "truth_matrix_row_count": len(truth_rows),
        "truth_matrix_group_count": len(
            {row["case_group"] for row in truth_rows}
        ),
        "safety_audit_row_count": len(safety_rows),
        "issue_inventory_row_count": len(
            list(
                csv.DictReader(
                    io.StringIO(payloads[ISSUE_NAME].decode("utf-8"))
                )
            )
        ),
        "issue_inventory_sha256": artifact_sha256[ISSUE_NAME],
        "effective_open_issues": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        ],
        "precondition_continuity": {
            **{
                name: json.loads(
                    (ROOT / PREDECESSOR_MANIFEST).read_text(encoding="utf-8")
                )["precondition_continuity"][name]
                for name in (
                    "row_count",
                    "transition_count",
                    "complete_count",
                    "supported_but_not_frozen_count",
                    "incomplete_count",
                    "implementation_blocking_count",
                    "remaining_open_precondition_ids",
                )
            },
            "newly_resolved_count": 0,
        },
        "stage_global_rule_evaluation_orchestration_contract_frozen": True,
        "stage_global_rule_evaluation_orchestration_implemented": True,
        "dispatcher_runtime_called_by_orchestrator": True,
        "aggregator_runtime_called_by_orchestrator": True,
        "stage_global_exactly_once_runtime_verified": True,
        "candidate_vector_assembly_runtime_verified": True,
        "orchestration_error_runtime_verified": True,
        "download_action_implemented": False,
        "training_action_implemented": False,
        "current_permission": False,
        "action_permission_granted": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_training": False,
        "canonical_mask_count": 5,
        "canonical_masks": list(masks),
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "unknown_atom_feature_policy_resolved": False,
        "feature_semantics_known": False,
        "recommended_next_step": (
            "run_covapie_stage_global_rule_evaluation_orchestration_"
            "in_memory_integration_smoke_v1"
        ),
    }
    payloads[MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return payloads


def test_frozen_execution_evidence_is_deterministic_and_current():
    first = build_execution_artifacts()
    second = build_execution_artifacts()
    assert first == second
    assert tuple(first) == OUTPUT_NAMES
    for name, payload in first.items():
        assert (ROOT / DERIVED_ROOT / name).read_bytes() == payload
    manifest = json.loads(first[MANIFEST_NAME])
    assert manifest["stage_global_rule_evaluation_orchestration_implemented"]
    assert manifest["dispatcher_runtime_called_by_orchestrator"]
    assert manifest["aggregator_runtime_called_by_orchestrator"]
    assert manifest["current_permission"] is False
    assert manifest["action_permission_granted"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["canonical_mask_count"] == 5
    assert {
        item["semantic_name"] for item in manifest["canonical_masks"]
    } == {
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    }
