from __future__ import annotations

import ast
import csv
import errno
import importlib
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013
    as runtime,
)


CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "covapie_exact13_checker",
    CHECKER_PATH,
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)

PREDECESSOR = runtime.predecessor
ORIGINAL = importlib.import_module(
    "covalent_ext."
    "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
    "with_admit_004"
)
KNOWN = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED = KNOWN[:13]
DOWNLOAD_FIELDS = runtime.ADMIT_013_DOWNLOAD_RESULT_FIELDS
AUTHORITY_FIELDS = runtime.ADMIT_013_INTEGRITY_AUTHORITY_FIELDS
SOURCE_FIELDS = runtime.ADMIT_013_SOURCE_FIELDS
RESULT_FIELDS = runtime.RESULT_FIELDS
ERROR_FIELDS = runtime.DISPATCH_ERROR_FIELDS
SHA = "0123456789abcdef" * 4
VALID_DOWNLOAD = {
    "download_result_status": "success",
    "observed_http_status": 200,
    "observed_content_length_bytes": 7,
    "observed_sha256": SHA,
}
VALID_AUTHORITY = {
    "expected_content_length_bytes": 7,
    "expected_sha256": SHA,
    "explicit_integrity_verdict": "verified",
}
OUTPUT_ROOT = ROOT / runtime.DEFAULT_OUTPUT_ROOT


class CountingMapping(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object],
        *,
        error_key: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.values = dict(values)
        self.error_key = error_key
        self.error = error
        self.calls: list[str] = []
        self.iterated = False
        self.sized = False
        self.contains_called = False
        self.get_called = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        if key == self.error_key and self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.sized = True
        return len(self.values)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)

    def get(self, key: str, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)


class CandidateBomb(Mapping[str, object]):
    def __init__(self) -> None:
        self.accesses = 0

    def __getitem__(self, key: str) -> object:
        self.accesses += 1
        raise AssertionError("candidate key accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def route(candidate: object = None, **overrides: object) -> object:
    kwargs: dict[str, object] = {
        "batch_context": None,
        "evaluation_context": VALID_AUTHORITY,
        "download_result_context": VALID_DOWNLOAD,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return runtime._evaluate_registered_admit_013(
        {} if candidate is None else candidate,
        **kwargs,
    )


def source_value(**overrides: object) -> object:
    values = {**VALID_DOWNLOAD, **VALID_AUTHORITY, **overrides}
    return runtime.admit013.evaluate_admit_013(**values)


def exact_error(reason: str) -> tuple[object, ...]:
    return (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_013",
        True,
        True,
        True,
        reason,
    )


@pytest.mark.parametrize(
    "name",
    (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ),
)
def test_shared_public_objects_are_reused_by_exact_identity(name: str) -> None:
    assert getattr(runtime, name) is getattr(PREDECESSOR, name)
    assert getattr(runtime, name) is getattr(ORIGINAL, name)


def test_exact13_rule_sets_registry_and_mapping_proxy() -> None:
    assert runtime.KNOWN_RULE_IDS == KNOWN
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == REGISTERED
    assert runtime.ADAPTER_READY_RULE_IDS == REGISTERED
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert tuple(runtime.EVALUATOR_REGISTRY) == REGISTERED
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    with pytest.raises(TypeError):
        runtime.EVALUATOR_REGISTRY["ADMIT_999"] = object()


@pytest.mark.parametrize("rule_id", KNOWN[:12])
def test_first_twelve_handler_object_identities_preserved(
    rule_id: str,
) -> None:
    assert (
        runtime.EVALUATOR_REGISTRY[rule_id]
        is PREDECESSOR.EVALUATOR_REGISTRY[rule_id]
    )


def test_admit013_handler_and_successor_dispatcher_identity_signature() -> None:
    assert (
        runtime.EVALUATOR_REGISTRY["ADMIT_013"]
        is runtime._evaluate_registered_admit_013
    )
    assert runtime.evaluate_admission_rule is not PREDECESSOR.evaluate_admission_rule
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        PREDECESSOR.evaluate_admission_rule
    )
    assert str(inspect.signature(runtime._evaluate_registered_admit_013)) == (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', download_result_context: 'object', "
        "stage_authorization_context: 'object') -> "
        "'UnifiedAdmissionRuleEvaluation'"
    )
    assert (
        runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"]
        is runtime.EVALUATOR_REGISTRY
    )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"batch_context": object()}, "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE"),
        (
            {"evaluation_context": object()},
            "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            {"download_result_context": object()},
            "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            {"stage_authorization_context": object()},
            "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ),
    ),
)
def test_context_routing_errors_are_exact_and_precede_candidate(
    overrides: dict[str, object],
    reason: str,
) -> None:
    candidate = CandidateBomb()
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route(candidate, **overrides)
    assert tuple(
        getattr(captured.value, name) for name in ERROR_FIELDS
    ) == exact_error(reason)
    assert candidate.accesses == 0


def test_batch_failure_precedes_every_later_envelope() -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route(
            CandidateBomb(),
            batch_context=object(),
            evaluation_context=object(),
            download_result_context=object(),
            stage_authorization_context=object(),
        )
    assert captured.value.reason == "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE"


def test_candidate_non_mapping_fixed_result_and_zero_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime.admit013,
        "evaluate_admit_013",
        lambda **kwargs: pytest.fail("formal called"),
    )
    monkeypatch.setattr(
        runtime.admit013_oracle,
        "classify_admit_013_formal_evaluator_interface_design",
        lambda **kwargs: pytest.fail("oracle called"),
    )
    download = CountingMapping({})
    authority = CountingMapping({})
    value = route(
        object(),
        evaluation_context=authority,
        download_result_context=download,
    )
    assert tuple(getattr(value, name) for name in RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_013",
        "download_failure_fail_closed",
        "invalid",
        False,
        True,
        "ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID",
        (),
        (),
        (),
        (),
        False,
        "covapie_admit_013_unified_adapter_v1",
    )
    assert download.calls == authority.calls == []


def test_candidate_mapping_has_zero_key_iteration_size_get_or_contains() -> None:
    candidate = CandidateBomb()
    value = route(candidate)
    assert value.outcome == "passed"
    assert candidate.accesses == 0


@pytest.mark.parametrize("missing_index", range(4))
def test_required_exact4_first_missing_stops_and_skips_authority(
    missing_index: int,
) -> None:
    download = CountingMapping(
        {
            name: VALID_DOWNLOAD[name]
            for name in DOWNLOAD_FIELDS[:missing_index]
        }
    )
    authority = CountingMapping(VALID_AUTHORITY)
    candidate = CandidateBomb()
    value = route(
        candidate,
        evaluation_context=authority,
        download_result_context=download,
    )
    assert download.calls == list(DOWNLOAD_FIELDS[: missing_index + 1])
    assert authority.calls == []
    assert value.reason == runtime.admit013.MISSING_REASONS[missing_index]
    assert candidate.accesses == 0
    assert not any(
        (
            download.iterated,
            download.sized,
            download.contains_called,
            download.get_called,
        )
    )


@pytest.mark.parametrize("missing_index", range(3))
def test_optional_exact3_missing_continues_all_later_lookups(
    missing_index: int,
) -> None:
    values = dict(VALID_AUTHORITY)
    values.pop(AUTHORITY_FIELDS[missing_index])
    authority = CountingMapping(values)
    value = route({}, evaluation_context=authority)
    assert authority.calls == list(AUTHORITY_FIELDS)
    assert value.outcome in {"passed", "blocked"}
    assert not any(
        (
            authority.iterated,
            authority.sized,
            authority.contains_called,
            authority.get_called,
        )
    )


@pytest.mark.parametrize("location", ("download", "authority"))
def test_non_key_error_lookups_become_exact_context_error(
    location: str,
) -> None:
    sentinel = RuntimeError(location)
    download: object = VALID_DOWNLOAD
    authority: object = VALID_AUTHORITY
    if location == "download":
        download = CountingMapping(
            VALID_DOWNLOAD,
            error_key=DOWNLOAD_FIELDS[0],
            error=sentinel,
        )
        reason = "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED"
    else:
        authority = CountingMapping(
            VALID_AUTHORITY,
            error_key=AUTHORITY_FIELDS[0],
            error=sentinel,
        )
        reason = "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED"
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route(
            CandidateBomb(),
            evaluation_context=authority,
            download_result_context=download,
        )
    assert tuple(
        getattr(captured.value, name) for name in ERROR_FIELDS
    ) == exact_error(reason)


def test_present_objects_forwarded_by_identity_to_formal_then_oracle_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    objects = {
        name: object() for name in (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
    }
    calls: list[tuple[str, dict[str, object]]] = []
    formal = runtime.admit013.evaluate_admit_013
    oracle = (
        runtime.admit013_oracle
        .classify_admit_013_formal_evaluator_interface_design
    )

    def formal_wrapper(**kwargs: object) -> object:
        calls.append(("formal", kwargs))
        return formal(**kwargs)

    def oracle_wrapper(**kwargs: object) -> object:
        calls.append(("oracle", kwargs))
        return oracle(**kwargs)

    monkeypatch.setattr(
        runtime.admit013,
        "evaluate_admit_013",
        formal_wrapper,
    )
    monkeypatch.setattr(
        runtime.admit013_oracle,
        "classify_admit_013_formal_evaluator_interface_design",
        oracle_wrapper,
    )
    value = route(
        {},
        evaluation_context={
            name: objects[name] for name in AUTHORITY_FIELDS
        },
        download_result_context={
            name: objects[name] for name in DOWNLOAD_FIELDS
        },
    )
    assert value.outcome == "invalid"
    assert [name for name, _ in calls] == ["formal", "oracle"]
    assert all(
        kwargs[name] is objects[name]
        for _, kwargs in calls
        for name in (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
    )


def test_formal_exception_propagates_and_oracle_count_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = RuntimeError("formal")
    counts = {"formal": 0, "oracle": 0}

    def formal(**kwargs: object) -> object:
        counts["formal"] += 1
        raise sentinel

    def oracle(**kwargs: object) -> object:
        counts["oracle"] += 1
        return object()

    monkeypatch.setattr(runtime.admit013, "evaluate_admit_013", formal)
    monkeypatch.setattr(
        runtime.admit013_oracle,
        "classify_admit_013_formal_evaluator_interface_design",
        oracle,
    )
    with pytest.raises(RuntimeError) as captured:
        route({})
    assert captured.value is sentinel
    assert counts == {"formal": 1, "oracle": 0}


@pytest.mark.parametrize("source", (object(), 1, {}))
def test_source_wrong_exact_type_fails_before_oracle(
    source: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"oracle": 0}
    monkeypatch.setattr(
        runtime.admit013,
        "evaluate_admit_013",
        lambda **kwargs: source,
    )

    def oracle(**kwargs: object) -> object:
        calls["oracle"] += 1
        return object()

    monkeypatch.setattr(
        runtime.admit013_oracle,
        "classify_admit_013_formal_evaluator_interface_design",
        oracle,
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route({})
    assert (
        captured.value.reason
        == "ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
    )
    assert captured.value.adapter_ready is False
    assert calls["oracle"] == 0


def test_source_subclass_rejected_as_wrong_exact_type() -> None:
    source = source_value()
    subclass_type = type("ResultSubclass", (type(source),), {})
    subclass = object.__new__(subclass_type)
    for name in SOURCE_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime._prevalidate_admit013_source(subclass)
    assert (
        captured.value.reason
        == "ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
    )


def test_source_exact_storage_order_types_and_reconstruction() -> None:
    source = source_value()
    assert type(vars(source)) is dict
    assert tuple(vars(source)) == SOURCE_FIELDS
    assert tuple(field.name for field in fields(type(source))) == SOURCE_FIELDS
    assert type(source)(
        *(getattr(source, name) for name in SOURCE_FIELDS)
    ) == source
    assert runtime._prevalidate_admit013_source(source) is source


@pytest.mark.parametrize(
    "mode",
    ("storage", "top_type", "pair", "reason", "io"),
)
def test_source_invariant_tamper_fails_closed_before_oracle(
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = source_value()
    if mode == "storage":
        first = SOURCE_FIELDS[0]
        saved = vars(source).pop(first)
        vars(source)[first] = saved
    elif mode == "top_type":
        object.__setattr__(source, "passed", 1)
    elif mode == "pair":
        pairs = list(source.canonical_download_result_record)
        pairs[0] = list(pairs[0])
        object.__setattr__(
            source,
            "canonical_download_result_record",
            tuple(pairs),
        )
    elif mode == "reason":
        object.__setattr__(source, "reason", "DOWNLOAD_RESULT_STATUS_FAILURE")
    else:
        object.__setattr__(source, "evaluator_io_used", True)
    monkeypatch.setattr(
        runtime.admit013,
        "evaluate_admit_013",
        lambda **kwargs: source,
    )
    monkeypatch.setattr(
        runtime.admit013_oracle,
        "classify_admit_013_formal_evaluator_interface_design",
        lambda **kwargs: pytest.fail("oracle called"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route({})
    assert (
        captured.value.reason
        == "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )
    assert captured.value.adapter_ready is False


@pytest.mark.parametrize(
    "mode",
    ("exception", "wrong_type", "storage", "mismatch"),
)
def test_oracle_exception_type_storage_and_mismatch_fail_closed(
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = (
        runtime.admit013_oracle
        .classify_admit_013_formal_evaluator_interface_design
    )

    def replacement(**kwargs: object) -> object:
        if mode == "exception":
            raise RuntimeError("oracle")
        if mode == "wrong_type":
            return object()
        result = original(**kwargs)
        if mode == "storage":
            first = SOURCE_FIELDS[0]
            saved = vars(result).pop(first)
            vars(result)[first] = saved
        else:
            object.__setattr__(result, "reason", "INTEGRITY_AUTHORITY_MISSING")
        return result

    monkeypatch.setattr(
        runtime.admit013_oracle,
        "classify_admit_013_formal_evaluator_interface_design",
        replacement,
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route({})
    assert (
        captured.value.reason
        == "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )
    assert captured.value.adapter_ready is False


@pytest.mark.parametrize("field_name", SOURCE_FIELDS)
def test_full_exact12_equality_checks_every_field(
    field_name: str,
) -> None:
    source = source_value()
    expected = source_value()
    value = getattr(expected, field_name)
    replacement: object
    if type(value) is str:
        replacement = value + "x"
    elif type(value) is bool:
        replacement = not value
    else:
        replacement = (*value, "drift")
    object.__setattr__(expected, field_name, replacement)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime._validate_admit013_oracle_equivalence(source, expected)
    assert (
        captured.value.reason
        == "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )


def test_exact13_projection_combines_pairs_and_separates_consumption() -> None:
    value = route({})
    assert tuple(name for name, _ in value.normalized_values) == (
        *DOWNLOAD_FIELDS,
        *AUTHORITY_FIELDS,
    )
    assert tuple(name for name, _ in value.validated_candidate_fields) == (
        DOWNLOAD_FIELDS
    )
    assert value.consumed_candidate_fields == DOWNLOAD_FIELDS
    assert value.consumed_context_items == AUTHORITY_FIELDS
    assert all(type(item) is str for _, item in value.normalized_values)
    assert value.normalized_values[1][1] == "200"
    assert value.normalized_values[2][1] == "7"
    assert value.normalized_values[4][1] == "7"


class IntSubclass(int):
    pass


class StrSubclass(str):
    pass


class TupleSubclass(tuple):
    pass


class PairSubclass(tuple):
    pass


@pytest.mark.parametrize(
    "pairs",
    (
        [],
        {},
        TupleSubclass(()),
        (("download_result_status", "success", "extra"),),
        (("wrong", "success"),),
        (("observed_http_status", 200),),
        (("download_result_status", True),),
        (("download_result_status", StrSubclass("success")),),
        (
            ("download_result_status", "success"),
            ("observed_http_status", True),
        ),
        (
            ("download_result_status", "success"),
            ("observed_http_status", IntSubclass(200)),
        ),
        (PairSubclass(("download_result_status", "success")),),
        (
            ("download_result_status", "success"),
            ("download_result_status", "success"),
        ),
        (
            ("expected_sha256", SHA),
            ("observed_sha256", SHA),
        ),
    ),
)
def test_projection_rejects_container_pair_name_order_duplicate_and_subclass(
    pairs: object,
) -> None:
    with pytest.raises(TypeError):
        runtime._project_named_pairs_to_exact_string_pairs(pairs)


@pytest.mark.parametrize(
    ("rule_id", "code", "known"),
    (
        (True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False),
        (13, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", False),
        ("ADMIT_014", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True),
        ("ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True),
    ),
)
def test_successor_dispatcher_fail_closed_precedence(
    rule_id: object,
    code: str,
    known: bool,
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime.evaluate_admission_rule(rule_id, {})
    assert captured.value.code == code
    assert captured.value.known_rule is known


def test_rule_id_str_subclass_is_type_invalid() -> None:
    class RuleIdSubclass(str):
        pass

    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime.evaluate_admission_rule(RuleIdSubclass("ADMIT_013"), {})
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"


def test_public_dispatcher_registers_admit013() -> None:
    value = runtime.evaluate_admission_rule(
        "ADMIT_013",
        {},
        evaluation_context=VALID_AUTHORITY,
        download_result_context=VALID_DOWNLOAD,
    )
    assert value.outcome == "passed"


@pytest.mark.parametrize("rule_id", KNOWN[:12])
def test_predecessor_default_dispatch_continuity(rule_id: str) -> None:
    def observe(module: object) -> tuple[str, tuple[object, ...]]:
        try:
            value = module.evaluate_admission_rule(rule_id, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            return "error", tuple(
                getattr(error, name) for name in ERROR_FIELDS
            )
        return "result", tuple(
            getattr(value, name) for name in RESULT_FIELDS
        )

    assert observe(runtime) == observe(PREDECESSOR)


def test_predecessor_exact694_truth_and_all_handler_identities() -> None:
    path = (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_012_v1/"
        "covapie_admit_001_to_012_dispatch_truth_matrix.csv"
    )
    rows = list(csv.DictReader(path.open(newline="")))
    assert len(rows) == 694
    assert all(
        row["case_passed"] == "true"
        and row["expected_result_or_error"]
        == row["observed_result_or_error"]
        for row in rows
    )
    assert all(
        runtime.EVALUATOR_REGISTRY[rule_id]
        is PREDECESSOR.EVALUATOR_REGISTRY[rule_id]
        for rule_id in KNOWN[:12]
    )


def test_committed_exact128_102_26_and_exact23_business_lineage() -> None:
    path = (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_013_formal_"
        "evaluator_interface_contract_v1/"
        "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv"
    )
    rows = list(csv.DictReader(path.open(newline="")))
    assert len(rows) == 128
    assert Counter(row["assertion_kind"] for row in rows) == {
        "formal_interface_projection": 102,
        "result_contract_rejection": 26,
    }
    assert sum(
        row["case_group"] == "inherited_exact7_business_projection"
        for row in rows
    ) == 23
    assert len({row["case_id"] for row in rows}) == 128


def test_runtime_state_exact_counts_groups_issue_transition_and_readiness() -> None:
    state = runtime.build_runtime_state()
    assert tuple(
        len(state[name])
        for name in (
            "contract_rows",
            "truth_rows",
            "registry_rows",
            "safety_rows",
            "issue_rows",
        )
    ) == (59, 885, 39, 30, 23)
    assert state["truth_group_counts"] == {
        "admit013_exact128_negative": 26,
        "admit013_exact128_normal": 102,
        "admit013_exact44_routing": 44,
        "predecessor_exact12_all_cases": 694,
        "successor_dispatcher": 19,
    }
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    coverage = issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "ADMIT_014|ADMIT_015"
    assert coverage["integration_transition"] == (
        "unified_dispatch_runtime_with_admit_001_to_013_implemented_v1"
    )
    assert issues[
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    ]["status"] == "open"


def test_build_artifacts_is_deterministic_and_canonical_guarded() -> None:
    state = runtime.build_runtime_state()
    first = runtime.build_artifacts(state)
    second = runtime.build_artifacts(state)
    assert first == second
    assert tuple(first) == runtime.OUTPUT_FILES
    with pytest.raises(ValueError, match="required: CPython 3.10.4"):
        runtime._validate_canonical_evidence_runtime_identity(
            "cpython",
            (3, 12, 0),
        )


def test_public_closure_attestation_hashes_imports_and_no_simulator() -> None:
    attested = checker._attest_candidate()
    state_attested = runtime._candidate_source_attestation()
    assert attested["sha256"] == state_attested["production_full_sha256"]
    assert (
        attested["marker_prefix_sha256"]
        == state_attested["marker_prefix_sha256"]
    )
    assert attested["ast_sha256"] == state_attested["normalized_ast_sha256"]
    prefix = attested["content"].decode().split(checker.MARKER, 1)[0]
    assert "simulate_admit_013_unified_adapter_design" not in prefix
    assert (
        "covapie_bulk_download_admission_admit_013_"
        "unified_adapter_contract_design_gate"
        not in prefix
    )


def test_no_aggregation_combined_verdict_provider_or_download_api() -> None:
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")
    assert not hasattr(runtime, "provider_mapping")
    assert not hasattr(runtime, "download_candidates")


def test_source_boundary_exact20_tracked_pinned_and_no_protected_paths() -> None:
    records = checker._verify_base_and_sources()
    assert len(records) == 20
    assert [row["source_relative_path"] for row in records] == [
        path for path, _ in checker.SOURCE_BOUNDARY
    ]
    assert not any(
        path.startswith("data/raw/") or path.startswith("checkpoints/")
        for path, _ in checker.SOURCE_BOUNDARY
    )


def test_exact6_output_tree_and_independent_checker_semantics() -> None:
    records = checker._verify_base_and_sources()
    assert checker._verify_output_tree(records) == checker.FROZEN_OUTPUT_SHA256


def test_manifest_readiness_and_recommended_next_step() -> None:
    manifest = json.loads((OUTPUT_ROOT / runtime.MANIFEST_FILENAME).read_text())
    assert all(manifest[name] is True for name in runtime.TRUE_READINESS)
    assert all(manifest[name] is False for name in runtime.FALSE_READINESS)
    assert manifest["recommended_next_step"] == (
        "audit_covapie_admit_014_formal_evaluator_interface_"
        "preconditions_v1"
    )
    assert manifest["step12d_status"] == (
        "smoke_legality_only_not_final_training_feature_contract"
    )


def test_temp_materialization_double_build_and_existing_set_noop(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
        first
    )
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
        second
    )
    assert checker._output_bytes(first) == checker._output_bytes(second)
    inodes = {
        name: (first / name).stat().st_ino for name in runtime.OUTPUT_FILES
    }
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
        first
    )
    assert inodes == {
        name: (first / name).stat().st_ino for name in runtime.OUTPUT_FILES
    }


def test_gpfs_einval_fails_closed_without_replace_or_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "set"
    replace_called = False

    def fail(*args: object) -> None:
        raise OSError(errno.EINVAL, "simulated GPFS EINVAL")

    def forbidden_replace(*args: object) -> None:
        nonlocal replace_called
        replace_called = True

    monkeypatch.setattr(runtime, "_rename_noreplace", fail)
    monkeypatch.setattr(runtime.os, "replace", forbidden_replace)
    with pytest.raises(OSError) as captured:
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
            target
        )
    assert captured.value.errno == errno.EINVAL
    assert not target.exists()
    assert not replace_called
    assert not tuple(tmp_path.glob(".exact13-runtime-stage-*"))


def test_existing_output_mismatch_fails_without_repair(
    tmp_path: Path,
) -> None:
    target = tmp_path / "set"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
        target
    )
    leaf = target / runtime.CONTRACT_FILENAME
    original = leaf.read_bytes()
    leaf.write_bytes(original + b"tamper\n")
    with pytest.raises(ValueError, match="repair forbidden"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
            target
        )
    assert leaf.read_bytes() == original + b"tamper\n"


def test_production_checker_and_test_isolated_imports_silent() -> None:
    snippets = (
        f"import {checker.MODULE}",
        (
            "import importlib.util;"
            f"s=importlib.util.spec_from_file_location('c',{str(CHECKER_PATH)!r});"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
        ),
        (
            "import importlib.util;"
            f"s=importlib.util.spec_from_file_location('t',{str(Path(__file__))!r});"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
        ),
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for snippet in snippets:
        completed = subprocess.run(
            (sys.executable, "-B", "-c", snippet),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )
        assert completed.returncode == 0
        assert completed.stdout == completed.stderr == b""


def test_checker_top_level_imports_standard_library_only() -> None:
    tree = ast.parse(CHECKER_PATH.read_text())
    project = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            project.extend(
                alias.name
                for alias in node.names
                if alias.name.startswith("covalent_ext")
            )
        elif isinstance(node, ast.ImportFrom) and (
            node.module or ""
        ).startswith("covalent_ext"):
            project.append(node.module)
    assert project == []


def test_exact10_lifecycle_and_no_forbidden_candidate_suffix() -> None:
    assert checker._verify_lifecycle() in {"pre_commit", "post_commit"}
    forbidden = (
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
    )
    assert len(checker.EXACT10) == 10
    assert not any(path.endswith(forbidden) for path in checker.EXACT10)


def _small_source_tree(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    relative = Path("a/b/source.txt")
    (root / relative.parent).mkdir(parents=True)
    (root / relative).write_bytes(b"pinned source\n")
    return root, relative


@pytest.mark.parametrize(
    ("source_module", "open_parent_name"),
    (
        (runtime, "_open_pinned_source_parent"),
        (checker, "_open_pinned_parent"),
    ),
)
def test_source_pinned_traversal_rejects_root_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_module: object,
    open_parent_name: str,
) -> None:
    root, relative = _small_source_tree(tmp_path)
    original = getattr(source_module, open_parent_name)
    replaced = False

    def replace_root(*args: object, **kwargs: object) -> object:
        nonlocal replaced
        if not replaced:
            replaced = True
            moved = tmp_path / "moved-repo"
            root.rename(moved)
            (root / relative.parent).mkdir(parents=True)
            (root / relative).write_bytes(b"pinned source\n")
        return original(*args, **kwargs)

    monkeypatch.setattr(source_module, open_parent_name, replace_root)
    with pytest.raises((AssertionError, ValueError, OSError)):
        source_module._read_one_pinned_source(root, relative)


@pytest.mark.parametrize("source_module", (runtime, checker))
def test_source_pinned_traversal_rejects_parent_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_module: object,
) -> None:
    root, relative = _small_source_tree(tmp_path)
    original = source_module._source_leaf_identity
    replaced = False

    def replace_parent(*args: object, **kwargs: object) -> object:
        nonlocal replaced
        if not replaced:
            replaced = True
            old_parent = root / "old-a"
            (root / "a").rename(old_parent)
            (root / relative.parent).mkdir(parents=True)
            (root / relative).write_bytes(b"pinned source\n")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        source_module,
        "_source_leaf_identity",
        replace_parent,
    )
    with pytest.raises((AssertionError, ValueError, OSError)):
        source_module._read_one_pinned_source(root, relative)


@pytest.mark.parametrize("source_module", (runtime, checker))
@pytest.mark.parametrize("replacement", (b"changed\n", b"pinned source\n"))
def test_source_pinned_traversal_rejects_leaf_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_module: object,
    replacement: bytes,
) -> None:
    root, relative = _small_source_tree(tmp_path)
    original = source_module._read_pinned_source_at
    replaced = False

    def replace_leaf(*args: object, **kwargs: object) -> object:
        nonlocal replaced
        if not replaced:
            replaced = True
            leaf = root / relative
            old_leaf = root / relative.with_name("old-source.txt")
            new_leaf = root / relative.with_name("new-source.txt")
            new_leaf.write_bytes(replacement)
            leaf.rename(old_leaf)
            new_leaf.rename(leaf)
        return original(*args, **kwargs)

    monkeypatch.setattr(
        source_module,
        "_read_pinned_source_at",
        replace_leaf,
    )
    with pytest.raises((AssertionError, ValueError, OSError)):
        source_module._read_one_pinned_source(root, relative)


@pytest.mark.parametrize("source_module", (runtime, checker))
@pytest.mark.parametrize("link_kind", ("root", "parent", "leaf"))
def test_source_pinned_traversal_rejects_symlinks(
    tmp_path: Path,
    source_module: object,
    link_kind: str,
) -> None:
    root, relative = _small_source_tree(tmp_path)
    if link_kind == "root":
        real_root = tmp_path / "real-repo"
        root.rename(real_root)
        root.symlink_to(real_root, target_is_directory=True)
    elif link_kind == "parent":
        real_parent = root / "real-a"
        (root / "a").rename(real_parent)
        (root / "a").symlink_to(real_parent, target_is_directory=True)
    else:
        real_leaf = root / relative.with_name("real-source.txt")
        (root / relative).rename(real_leaf)
        (root / relative).symlink_to(real_leaf)
    with pytest.raises((AssertionError, ValueError, OSError)):
        source_module._read_one_pinned_source(root, relative)


def test_production_source_snapshot_rejects_current_index_untracked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = runtime._git

    def untrack_first(root: Path, *arguments: str) -> bytes:
        if (
            arguments
            and arguments[0] == "ls-files"
            and "--error-unmatch" in arguments
        ):
            return b""
        return original(root, *arguments)

    monkeypatch.setattr(runtime, "_git", untrack_first)
    with pytest.raises(ValueError, match="current index"):
        runtime.build_frozen_source_snapshot()


def _copied_output_tree(tmp_path: Path) -> Path:
    target = tmp_path / "parent" / "set"
    target.parent.mkdir()
    shutil.copytree(OUTPUT_ROOT, target)
    return target


def test_checker_output_rejects_root_replacement_during_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _copied_output_tree(tmp_path)
    original = checker._read_output_leaf
    replaced = False

    def replace_root(*args: object, **kwargs: object) -> bytes:
        nonlocal replaced
        if not replaced:
            replaced = True
            moved = target.with_name("moved-set")
            target.rename(moved)
            shutil.copytree(moved, target)
        return original(*args, **kwargs)

    monkeypatch.setattr(checker, "_read_output_leaf", replace_root)
    with pytest.raises(AssertionError):
        checker._output_bytes(target)


def test_checker_output_rejects_parent_replacement_during_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _copied_output_tree(tmp_path)
    parent = target.parent
    original = checker._read_output_leaf
    replaced = False

    def replace_parent(*args: object, **kwargs: object) -> bytes:
        nonlocal replaced
        if not replaced:
            replaced = True
            moved = parent.with_name("moved-parent")
            parent.rename(moved)
            parent.mkdir()
            shutil.copytree(moved / target.name, target)
        return original(*args, **kwargs)

    monkeypatch.setattr(checker, "_read_output_leaf", replace_parent)
    with pytest.raises(AssertionError):
        checker._output_bytes(target)


def test_checker_output_rejects_early_leaf_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _copied_output_tree(tmp_path)
    original = checker._read_output_leaf
    calls = 0

    def replace_early_leaf(*args: object, **kwargs: object) -> bytes:
        nonlocal calls
        content = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            leaf = target / checker.OUTPUTS[0]
            leaf.unlink()
            leaf.write_bytes(content)
        return content

    monkeypatch.setattr(
        checker,
        "_read_output_leaf",
        replace_early_leaf,
    )
    with pytest.raises(AssertionError):
        checker._output_bytes(target)


@pytest.mark.parametrize("mutation", ("extra", "missing"))
def test_checker_output_rejects_post_traversal_inventory_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    target = _copied_output_tree(tmp_path)
    original = checker._read_output_leaf
    calls = 0

    def mutate_after_last(*args: object, **kwargs: object) -> bytes:
        nonlocal calls
        content = original(*args, **kwargs)
        calls += 1
        if calls == len(checker.OUTPUTS):
            if mutation == "extra":
                (target / "extra.txt").write_bytes(b"extra")
            else:
                (target / checker.OUTPUTS[0]).unlink()
        return content

    monkeypatch.setattr(
        checker,
        "_read_output_leaf",
        mutate_after_last,
    )
    with pytest.raises(AssertionError):
        checker._output_bytes(target)


@pytest.mark.parametrize("link_kind", ("root", "leaf"))
def test_checker_output_rejects_symlink(
    tmp_path: Path,
    link_kind: str,
) -> None:
    target = _copied_output_tree(tmp_path)
    if link_kind == "root":
        real_target = target.with_name("real-set")
        target.rename(real_target)
        target.symlink_to(real_target, target_is_directory=True)
    else:
        leaf = target / checker.OUTPUTS[0]
        real_leaf = target / "real-leaf"
        leaf.rename(real_leaf)
        leaf.symlink_to(real_leaf)
    with pytest.raises((AssertionError, OSError)):
        checker._output_bytes(target)


@pytest.fixture(scope="module")
def revised_payloads() -> dict[str, bytes]:
    return runtime.build_artifacts()


def _publish_payloads(
    target: Path,
    payloads: Mapping[str, bytes],
) -> None:
    plan = runtime._inspect_output_target_read_only(target)
    runtime._materialize_set(plan, payloads)


@pytest.mark.parametrize(
    "mutation",
    ("destination", "parent", "leaf", "extra", "missing"),
)
def test_existing_set_rechecks_final_destination_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    revised_payloads: Mapping[str, bytes],
    mutation: str,
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    target = parent / "set"
    _publish_payloads(target, revised_payloads)
    original = runtime._verify_destination_binding
    calls = 0

    def race(*args: object, **kwargs: object) -> None:
        nonlocal calls
        original(*args, **kwargs)
        calls += 1
        if calls != 1:
            return
        if mutation == "destination":
            target.rename(parent / "old-set")
            target.mkdir()
        elif mutation == "parent":
            parent.rename(tmp_path / "old-parent")
            parent.mkdir()
        elif mutation == "leaf":
            leaf = target / runtime.CONTRACT_FILENAME
            content = leaf.read_bytes()
            leaf.unlink()
            leaf.write_bytes(content)
        elif mutation == "extra":
            (target / "extra.txt").write_bytes(b"extra")
        else:
            (target / runtime.CONTRACT_FILENAME).unlink()

    monkeypatch.setattr(runtime, "_verify_destination_binding", race)
    plan = runtime._inspect_output_target_read_only(target)
    with pytest.raises((ValueError, FileNotFoundError)):
        runtime._materialize_set(plan, revised_payloads)


@pytest.mark.parametrize(
    "mutation",
    ("destination", "deletion", "parent", "leaf"),
)
def test_post_rename_rechecks_final_destination_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    revised_payloads: Mapping[str, bytes],
    mutation: str,
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    target = parent / "set"
    original = runtime._verify_destination_binding
    calls = 0

    def race(*args: object, **kwargs: object) -> None:
        nonlocal calls
        original(*args, **kwargs)
        calls += 1
        if calls != 1:
            return
        if mutation == "destination":
            target.rename(parent / "old-set")
            target.mkdir()
        elif mutation == "deletion":
            shutil.rmtree(target)
        elif mutation == "parent":
            parent.rename(tmp_path / "old-parent")
            parent.mkdir()
        else:
            leaf = target / runtime.CONTRACT_FILENAME
            content = leaf.read_bytes()
            leaf.unlink()
            leaf.write_bytes(content)

    monkeypatch.setattr(runtime, "_verify_destination_binding", race)
    with pytest.raises((ValueError, FileNotFoundError)):
        _publish_payloads(target, revised_payloads)


def test_existing_set_normal_noop_preserves_root_and_leaf_inodes(
    tmp_path: Path,
    revised_payloads: Mapping[str, bytes],
) -> None:
    target = tmp_path / "set"
    _publish_payloads(target, revised_payloads)
    before = {
        name: (target / name).stat().st_ino
        for name in runtime.OUTPUT_FILES
    }
    root_inode = target.stat().st_ino
    _publish_payloads(target, revised_payloads)
    assert target.stat().st_ino == root_inode
    assert before == {
        name: (target / name).stat().st_ino
        for name in runtime.OUTPUT_FILES
    }


def _run_git(repo: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ("git", *arguments),
        cwd=repo,
        text=True,
    ).strip()


def _synthetic_lifecycle_repo(
    tmp_path: Path,
) -> tuple[Path, str]:
    repo = tmp_path / "synthetic"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.invalid")
    _run_git(repo, "config", "user.name", "CovaPIE Test")
    (repo / "README").write_text("base\n")
    _run_git(repo, "add", "--", "README")
    _run_git(repo, "commit", "-q", "-m", "base")
    base = _run_git(repo, "rev-parse", "HEAD")
    for raw_path in checker.EXACT10:
        path = repo / raw_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{raw_path}\n")
    return repo, base


@pytest.mark.parametrize(
    ("state", "expected_lifecycle"),
    (
        ("all_untracked", "pre_commit"),
        ("descendant_unrelated_commit", "pre_commit"),
        ("all_tracked_clean", "post_commit"),
        ("unrelated_state", "pre_commit"),
        ("mixed", None),
        ("stage_path_staged", None),
        ("dirty", None),
        ("missing", None),
        ("ignored", None),
        ("extra_top", None),
        ("extra_output", None),
        ("symlink", None),
        ("oversized", None),
        ("nonancestor", None),
    ),
)
def test_exact10_lifecycle_synthetic_states(
    tmp_path: Path,
    state: str,
    expected_lifecycle: str | None,
) -> None:
    repo, base = _synthetic_lifecycle_repo(tmp_path)
    base_for_check = base
    if state == "descendant_unrelated_commit":
        (repo / "unrelated.txt").write_text("unrelated\n")
        _run_git(repo, "add", "--", "unrelated.txt")
        _run_git(repo, "commit", "-q", "-m", "unrelated")
    elif state == "all_tracked_clean":
        _run_git(repo, "add", "--", *checker.EXACT10)
        _run_git(repo, "commit", "-q", "-m", "candidate")
    elif state == "unrelated_state":
        (repo / ".gitignore").write_text("cache/\n")
        (repo / "staged.txt").write_text("staged\n")
        (repo / "loose.txt").write_text("loose\n")
        (repo / "cache").mkdir()
        (repo / "cache/ignored.bin").write_bytes(b"cache")
        _run_git(repo, "add", "--", "staged.txt")
    elif state == "mixed":
        _run_git(repo, "add", "--", checker.EXACT10[0])
        _run_git(repo, "commit", "-q", "-m", "one candidate")
    elif state == "stage_path_staged":
        _run_git(repo, "add", "--", checker.EXACT10[0])
    elif state == "dirty":
        _run_git(repo, "add", "--", *checker.EXACT10)
        _run_git(repo, "commit", "-q", "-m", "candidate")
        (repo / checker.EXACT10[0]).write_text("dirty\n")
    elif state == "missing":
        (repo / checker.EXACT10[-1]).unlink()
    elif state == "ignored":
        (repo / ".gitignore").write_text(
            f"/{checker.EXACT10[0]}\n"
        )
        _run_git(repo, "add", "--", ".gitignore")
        _run_git(repo, "commit", "-q", "-m", "ignore candidate")
    elif state == "extra_top":
        (
            repo
            / "src/covalent_ext/"
            "extra_unified_dispatch_runtime_with_admit_001_to_013.py"
        ).write_text("extra\n")
    elif state == "extra_output":
        output_parent = (repo / checker.EXACT10[-1]).parent
        (output_parent / "seventh.tmp").write_bytes(b"extra")
    elif state == "symlink":
        candidate = repo / checker.EXACT10[0]
        candidate.unlink()
        candidate.symlink_to(repo / "README")
    elif state == "oversized":
        with (repo / checker.EXACT10[0]).open("wb") as stream:
            stream.truncate(checker.MAX_CANDIDATE_BYTES + 1)
    elif state == "nonancestor":
        tree = _run_git(repo, "rev-parse", f"{base}^{{tree}}")
        base_for_check = subprocess.check_output(
            ("git", "commit-tree", tree),
            cwd=repo,
            input=b"unrelated root\n",
        ).decode().strip()
    if expected_lifecycle is None:
        with pytest.raises(AssertionError):
            checker._verify_lifecycle(
                repo,
                checker.EXACT10,
                base_commit=base_for_check,
            )
    else:
        assert (
            checker._verify_lifecycle(
                repo,
                checker.EXACT10,
                base_commit=base_for_check,
            )
            == expected_lifecycle
        )


def _generated_manifest_bytes(
    revised_payloads: Mapping[str, bytes],
) -> bytes:
    return revised_payloads[runtime.MANIFEST_FILENAME]


def _dump_manifest(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def test_manifest_rejects_duplicate_key(
    revised_payloads: Mapping[str, bytes],
) -> None:
    content = _generated_manifest_bytes(revised_payloads)
    duplicate = content.replace(
        b"{\n",
        b'{\n  "Admit013EvaluationResult_implemented": true,\n',
        1,
    )
    with pytest.raises(AssertionError, match="duplicate"):
        checker._manifest_object(duplicate)


@pytest.mark.parametrize("mutation", ("missing", "extra", "reorder"))
def test_manifest_rejects_top_level_exact_key_drift(
    revised_payloads: Mapping[str, bytes],
    mutation: str,
) -> None:
    manifest = json.loads(_generated_manifest_bytes(revised_payloads))
    if mutation == "missing":
        manifest.pop("project")
    elif mutation == "extra":
        manifest["unexpected"] = True
    else:
        first = next(iter(manifest))
        value = manifest.pop(first)
        manifest[first] = value
    with pytest.raises(AssertionError, match="top-level"):
        checker._manifest_object(_dump_manifest(manifest))


@pytest.mark.parametrize(
    ("nested", "mutation"),
    (
        ("readiness", "missing"),
        ("readiness", "extra"),
        ("readiness", "reorder"),
        ("output_sha256", "missing"),
        ("output_sha256", "extra"),
        ("candidate_production_source_attestation", "missing"),
        ("candidate_production_source_attestation", "extra"),
    ),
)
def test_manifest_rejects_nested_exact_key_drift(
    revised_payloads: Mapping[str, bytes],
    nested: str,
    mutation: str,
) -> None:
    manifest = json.loads(_generated_manifest_bytes(revised_payloads))
    values = manifest[nested]
    if mutation == "missing":
        values.pop(next(iter(values)))
    elif mutation == "extra":
        values["unexpected"] = True
    else:
        first = next(iter(values))
        value = values.pop(first)
        values[first] = value
    with pytest.raises(AssertionError, match="nested"):
        checker._manifest_object(_dump_manifest(manifest))


def test_checker_rejects_synchronized_csv_and_manifest_tamper(
    revised_payloads: Mapping[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tampered = dict(revised_payloads)
    name = runtime.CONTRACT_FILENAME
    tampered[name] += b"tamper\n"
    manifest = json.loads(tampered[runtime.MANIFEST_FILENAME])
    manifest["output_sha256"][name] = checker._sha(tampered[name])
    tampered[runtime.MANIFEST_FILENAME] = _dump_manifest(manifest)
    monkeypatch.setattr(checker, "_output_bytes", lambda: tampered)
    with pytest.raises(AssertionError, match="frozen Exact6"):
        checker._verify_output_tree(())


def test_exact4_stage_local_deselections_include_obsolete_absence_node() -> None:
    assert len(checker.STAGE_LOCAL_DESELECTIONS) == 4
    assert checker.STAGE_LOCAL_DESELECTIONS[-1] == (
        "tests/test_covapie_bulk_download_admission_admit_013_formal_"
        "evaluator_interface_contract_v1.py::"
        "test_no_formal_evaluator_result_adapter_registry_or_exact13_"
        "runtime"
    )
