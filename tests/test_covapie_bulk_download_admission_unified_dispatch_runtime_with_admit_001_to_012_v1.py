from __future__ import annotations

import ast
import errno
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012
    as runtime,
)


CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location("covapie_exact12_checker", CHECKER_PATH)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)

PREDECESSOR = runtime.predecessor
ORIGINAL = importlib.import_module(
    "covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004"
)
KNOWN = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED = KNOWN[:12]
CONTEXT_ITEMS = runtime.ADMIT_012_CONTEXT_ITEMS
DOWNLOAD_FIELDS = runtime.ADMIT_012_DOWNLOAD_RESULT_FIELDS
SOURCE_FIELDS = runtime.ADMIT_012_SOURCE_FIELDS
RESULT_FIELDS = runtime.RESULT_FIELDS
ERROR_FIELDS = runtime.DISPATCH_ERROR_FIELDS
VALID_CONTEXT = dict(
    zip(CONTEXT_ITEMS, runtime.admit012.FORMAL_CONTEXT_VALUES, strict=True)
)
VALID_DOWNLOAD = {
    "download_result_status": "success",
    "observed_http_status": 200,
    "observed_content_length_bytes": 0,
    "observed_sha256": "0123456789abcdef" * 4,
}
OUTPUT_ROOT = ROOT / runtime.DEFAULT_OUTPUT_ROOT


class CountingMapping(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object],
        error: Exception | None = None,
    ) -> None:
        self.values = dict(values)
        self.error = error
        self.calls: list[str] = []
        self.iterated = False
        self.sized = False
        self.contains_called = False
        self.get_called = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        if self.error is not None:
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
        "evaluation_context": VALID_CONTEXT,
        "download_result_context": VALID_DOWNLOAD,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return runtime._evaluate_registered_admit_012(
        {} if candidate is None else candidate,
        **kwargs,
    )


def exact_error(reason: str) -> tuple[object, ...]:
    return (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_012",
        True,
        True,
        True,
        reason,
    )


def source_value(**kwargs: object) -> object:
    values = dict(VALID_DOWNLOAD)
    values.update(kwargs)
    return runtime.admit012.evaluate_admit_012(**values, **VALID_CONTEXT)


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
def test_public_objects_and_constants_reused_by_identity(name: str) -> None:
    assert getattr(runtime, name) is getattr(PREDECESSOR, name)
    assert getattr(runtime, name) is getattr(ORIGINAL, name)


def test_exact12_rule_sets_and_registry_order() -> None:
    assert runtime.KNOWN_RULE_IDS == KNOWN
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == REGISTERED
    assert runtime.ADAPTER_READY_RULE_IDS == REGISTERED
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert tuple(runtime.EVALUATOR_REGISTRY) == REGISTERED


@pytest.mark.parametrize("name", ("RULE_NAMES", "ADAPTER_IDS", "EVALUATOR_REGISTRY"))
def test_registries_are_new_immutable_mapping_proxies(name: str) -> None:
    value = getattr(runtime, name)
    assert type(value) is MappingProxyType
    assert value is not getattr(PREDECESSOR, name)
    with pytest.raises(TypeError):
        value["ADMIT_999"] = object()


@pytest.mark.parametrize("rule_id", KNOWN[:11])
def test_first_eleven_handler_identities_are_preserved(rule_id: str) -> None:
    assert runtime.EVALUATOR_REGISTRY[rule_id] is PREDECESSOR.EVALUATOR_REGISTRY[rule_id]


def test_admit012_handler_binding_and_dispatcher_local_registry() -> None:
    assert runtime.EVALUATOR_REGISTRY["ADMIT_012"] is runtime._evaluate_registered_admit_012
    assert runtime.evaluate_admission_rule is not PREDECESSOR.evaluate_admission_rule
    assert runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is runtime.EVALUATOR_REGISTRY


def test_exact_handler_and_public_dispatcher_signatures() -> None:
    assert str(inspect.signature(runtime._evaluate_registered_admit_012)) == (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', download_result_context: 'object', "
        "stage_authorization_context: 'object') -> 'UnifiedAdmissionRuleEvaluation'"
    )
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        PREDECESSOR.evaluate_admission_rule
    )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"batch_context": object()}, "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": object()}, "ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED"),
        ({"evaluation_context": {CONTEXT_ITEMS[0]: object()}}, "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED"),
        ({"evaluation_context": {CONTEXT_ITEMS[0]: object(), CONTEXT_ITEMS[1]: object()}}, "ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED"),
        ({"evaluation_context": {CONTEXT_ITEMS[0]: object(), CONTEXT_ITEMS[1]: object(), CONTEXT_ITEMS[2]: object()}}, "ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED"),
        ({"stage_authorization_context": object()}, "ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_context_routing_failures_are_exact_and_precede_candidate(
    overrides: dict[str, object], reason: str
) -> None:
    candidate = CandidateBomb()
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route(candidate, **overrides)
    assert tuple(getattr(captured.value, name) for name in ERROR_FIELDS) == exact_error(reason)
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
    assert captured.value.reason == "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE"


@pytest.mark.parametrize("missing_index", range(4))
def test_evaluation_policy_lookup_order_and_first_missing_reason(missing_index: int) -> None:
    mapping = CountingMapping(
        {name: VALID_CONTEXT[name] for name in CONTEXT_ITEMS[:missing_index]}
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route(CandidateBomb(), evaluation_context=mapping, download_result_context=object())
    assert mapping.calls == list(CONTEXT_ITEMS[: missing_index + 1])
    assert captured.value.reason == (
        "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED",
        "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED",
        "ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED",
        "ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED",
    )[missing_index]
    assert not any((mapping.iterated, mapping.sized, mapping.contains_called, mapping.get_called))


@pytest.mark.parametrize("location", ("evaluation", "download"))
def test_non_key_error_lookup_propagates_same_exception(location: str) -> None:
    sentinel = RuntimeError(location)
    with pytest.raises(RuntimeError) as captured:
        route(
            CandidateBomb(),
            evaluation_context=(CountingMapping({}, sentinel) if location == "evaluation" else VALID_CONTEXT),
            download_result_context=(CountingMapping({}, sentinel) if location == "download" else VALID_DOWNLOAD),
        )
    assert captured.value is sentinel


def test_candidate_non_mapping_exact13_and_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime.admit012, "evaluate_admit_012", lambda **kwargs: pytest.fail("formal called"))
    monkeypatch.setattr(
        runtime.admit012_oracle,
        "classify_admit_012_formal_evaluator_interface_design",
        lambda **kwargs: pytest.fail("oracle called"),
    )
    value = route(object(), download_result_context=CountingMapping({}))
    assert tuple(getattr(value, name) for name in RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_012",
        runtime.ADMISSION_RULE_NAME,
        "invalid",
        False,
        True,
        "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID",
        (),
        (),
        (),
        CONTEXT_ITEMS,
        False,
        runtime.ADAPTER_ID,
    )


@pytest.mark.parametrize("candidate", ({}, {"extra": object()}))
def test_candidate_empty_or_unrelated_mapping_has_zero_key_access(candidate: dict[str, object]) -> None:
    value = route(candidate)
    assert value.outcome == "passed"


def test_candidate_mapping_key_value_bombs_are_not_triggered() -> None:
    candidate = CandidateBomb()
    value = route(candidate)
    assert value.outcome == "passed"
    assert candidate.accesses == 0


@pytest.mark.parametrize("missing_index", range(4))
def test_download_first_missing_stops_later_lookups(missing_index: int) -> None:
    mapping = CountingMapping(
        {name: VALID_DOWNLOAD[name] for name in DOWNLOAD_FIELDS[:missing_index]}
    )
    candidate = CandidateBomb()
    value = route(candidate, download_result_context=mapping)
    assert mapping.calls == list(DOWNLOAD_FIELDS[: missing_index + 1])
    assert value.reason == runtime.admit012.MISSING_REASONS[missing_index]
    assert candidate.accesses == 0
    assert not any((mapping.iterated, mapping.sized, mapping.contains_called, mapping.get_called))


@pytest.mark.parametrize("missing_index", range(4))
def test_missing_keyword_and_every_later_keyword_are_omitted(
    missing_index: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    formal_kwargs: list[dict[str, object]] = []
    oracle_kwargs: list[dict[str, object]] = []
    formal = runtime.admit012.evaluate_admit_012
    oracle = runtime.admit012_oracle.classify_admit_012_formal_evaluator_interface_design

    def formal_wrapper(**kwargs: object) -> object:
        formal_kwargs.append(kwargs)
        return formal(**kwargs)

    def oracle_wrapper(**kwargs: object) -> object:
        oracle_kwargs.append(kwargs)
        return oracle(**kwargs)

    monkeypatch.setattr(runtime.admit012, "evaluate_admit_012", formal_wrapper)
    monkeypatch.setattr(
        runtime.admit012_oracle,
        "classify_admit_012_formal_evaluator_interface_design",
        oracle_wrapper,
    )
    route(
        {},
        download_result_context={
            name: VALID_DOWNLOAD[name] for name in DOWNLOAD_FIELDS[:missing_index]
        },
    )
    expected_keys = (*DOWNLOAD_FIELDS[:missing_index], *CONTEXT_ITEMS)
    assert tuple(formal_kwargs[0]) == expected_keys
    assert tuple(oracle_kwargs[0]) == expected_keys
    assert "_MISSING" not in repr(formal_kwargs[0])


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("download_result_status", None),
        ("observed_http_status", False),
        ("observed_content_length_bytes", 0),
    ),
)
def test_present_none_false_and_zero_are_not_missing(field: str, value: object) -> None:
    values = dict(VALID_DOWNLOAD)
    values[field] = value
    result = route({}, download_result_context=values)
    assert "MISSING" not in result.reason


def test_mapping_subclasses_exact_single_lookups_and_extra_keys_ignored() -> None:
    evaluation = CountingMapping({**VALID_CONTEXT, "extra": object()})
    download = CountingMapping({**VALID_DOWNLOAD, "extra": object()})
    candidate = CandidateBomb()
    value = route(candidate, evaluation_context=evaluation, download_result_context=download)
    assert value.outcome == "passed"
    assert evaluation.calls == list(CONTEXT_ITEMS)
    assert download.calls == list(DOWNLOAD_FIELDS)
    assert candidate.accesses == 0
    assert not any(
        (
            evaluation.iterated,
            evaluation.sized,
            evaluation.contains_called,
            evaluation.get_called,
            download.iterated,
            download.sized,
            download.contains_called,
            download.get_called,
        )
    )


def test_formal_then_oracle_exactly_once_same_object_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinels = {name: object() for name in (*DOWNLOAD_FIELDS, *CONTEXT_ITEMS)}
    calls: list[tuple[str, dict[str, object]]] = []
    formal = runtime.admit012.evaluate_admit_012
    oracle = runtime.admit012_oracle.classify_admit_012_formal_evaluator_interface_design

    def formal_wrapper(**kwargs: object) -> object:
        calls.append(("formal", kwargs))
        return formal(**kwargs)

    def oracle_wrapper(**kwargs: object) -> object:
        calls.append(("oracle", kwargs))
        return oracle(**kwargs)

    monkeypatch.setattr(runtime.admit012, "evaluate_admit_012", formal_wrapper)
    monkeypatch.setattr(
        runtime.admit012_oracle,
        "classify_admit_012_formal_evaluator_interface_design",
        oracle_wrapper,
    )
    route(
        {},
        evaluation_context={name: sentinels[name] for name in CONTEXT_ITEMS},
        download_result_context={name: sentinels[name] for name in DOWNLOAD_FIELDS},
    )
    assert [name for name, _ in calls] == ["formal", "oracle"]
    assert all(
        kwargs[name] is sentinels[name]
        for _, kwargs in calls
        for name in (*DOWNLOAD_FIELDS, *CONTEXT_ITEMS)
    )


def test_formal_exception_propagates_and_oracle_is_not_called(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = RuntimeError("formal")
    counts = {"formal": 0, "oracle": 0}

    def formal(**kwargs: object) -> object:
        counts["formal"] += 1
        raise sentinel

    def oracle(**kwargs: object) -> object:
        counts["oracle"] += 1
        return object()

    monkeypatch.setattr(runtime.admit012, "evaluate_admit_012", formal)
    monkeypatch.setattr(
        runtime.admit012_oracle,
        "classify_admit_012_formal_evaluator_interface_design",
        oracle,
    )
    with pytest.raises(RuntimeError) as captured:
        route({})
    assert captured.value is sentinel
    assert counts == {"formal": 1, "oracle": 0}


@pytest.mark.parametrize("source", (object(), 1, {}))
def test_source_wrong_exact_type_fails_closed_before_oracle(
    source: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"oracle": 0}
    monkeypatch.setattr(runtime.admit012, "evaluate_admit_012", lambda **kwargs: source)

    def oracle(**kwargs: object) -> object:
        calls["oracle"] += 1
        return object()

    monkeypatch.setattr(
        runtime.admit012_oracle,
        "classify_admit_012_formal_evaluator_interface_design",
        oracle,
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route({})
    assert captured.value.reason == "ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
    assert captured.value.adapter_ready is False
    assert calls["oracle"] == 0


def test_source_subclass_is_rejected_as_wrong_type() -> None:
    source = source_value()
    subclass_type = type("ResultSubclass", (type(source),), {})
    subclass = object.__new__(subclass_type)
    for name in SOURCE_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime._prevalidate_admit012_source(subclass)
    assert captured.value.reason == "ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"


def test_source_exact_storage_and_dataclass_order_reconstruct() -> None:
    source = source_value()
    assert type(vars(source)) is dict
    assert tuple(vars(source)) == SOURCE_FIELDS
    assert tuple(field.name for field in fields(type(source))) == SOURCE_FIELDS
    assert type(source)(*(getattr(source, name) for name in SOURCE_FIELDS)) == source
    assert runtime._prevalidate_admit012_source(source) is source


@pytest.mark.parametrize("mode", ("storage", "top_type", "pair", "io"))
def test_source_invariant_tamper_fails_closed(mode: str) -> None:
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
        object.__setattr__(source, "canonical_download_result_record", tuple(pairs))
    else:
        object.__setattr__(source, "evaluator_io_used", True)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime._prevalidate_admit012_source(source)
    assert captured.value.reason == "ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


def test_oracle_exact_type_storage_order_and_conversion() -> None:
    design = runtime.admit012_oracle.classify_admit_012_formal_evaluator_interface_design(
        **VALID_DOWNLOAD, **VALID_CONTEXT
    )
    assert type(design) is runtime.admit012_oracle.Admit012EvaluationResultContractDesign
    assert type(vars(design)) is dict
    assert tuple(vars(design)) == SOURCE_FIELDS
    expected = runtime._expected_admit012_from_oracle(dict(VALID_DOWNLOAD), dict(VALID_CONTEXT))
    assert type(expected) is runtime.admit012.Admit012EvaluationResult


@pytest.mark.parametrize("mode", ("exception", "wrong_type", "storage"))
def test_oracle_failure_modes_become_adapter_not_ready(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    oracle = runtime.admit012_oracle.classify_admit_012_formal_evaluator_interface_design

    def replacement(**kwargs: object) -> object:
        if mode == "exception":
            raise RuntimeError("oracle")
        if mode == "wrong_type":
            return object()
        value = oracle(**kwargs)
        first = SOURCE_FIELDS[0]
        saved = vars(value).pop(first)
        vars(value)[first] = saved
        return value

    monkeypatch.setattr(
        runtime.admit012_oracle,
        "classify_admit_012_formal_evaluator_interface_design",
        replacement,
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        route({})
    assert captured.value.reason == "ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert captured.value.adapter_ready is False


@pytest.mark.parametrize("field_name", SOURCE_FIELDS)
def test_full_exact10_equality_checks_every_field_value_and_type(field_name: str) -> None:
    source = source_value()
    expected = source_value()
    value = getattr(expected, field_name)
    if type(value) is str:
        replacement: object = value + "x"
    elif type(value) is bool:
        replacement = not value
    else:
        replacement = (*value, "drift")
    object.__setattr__(expected, field_name, replacement)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime._validate_admit012_oracle_equivalence(source, expected)
    assert captured.value.reason == "ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


@pytest.mark.parametrize(
    ("pairs", "expected"),
    (
        ((), ()),
        ((("download_result_status", "failure"),), (("download_result_status", "failure"),)),
        (
            (("download_result_status", "success"), ("observed_http_status", 404)),
            (("download_result_status", "success"), ("observed_http_status", "404")),
        ),
        (
            (
                ("download_result_status", "success"),
                ("observed_http_status", 200),
                ("observed_content_length_bytes", 0),
            ),
            (
                ("download_result_status", "success"),
                ("observed_http_status", "200"),
                ("observed_content_length_bytes", "0"),
            ),
        ),
    ),
)
def test_projection_accepts_empty_and_ordered_prefixes(
    pairs: tuple[tuple[str, object], ...], expected: tuple[tuple[str, str], ...]
) -> None:
    assert runtime._project_download_result_pairs_to_exact_string_pairs(pairs) == expected


def test_projection_uses_canonical_decimal_for_large_integer() -> None:
    value = 10**100
    pairs = (
        ("download_result_status", "success"),
        ("observed_http_status", 200),
        ("observed_content_length_bytes", value),
    )
    projected = runtime._project_download_result_pairs_to_exact_string_pairs(pairs)
    assert projected[-1][1] == str(value)
    assert "e" not in projected[-1][1].lower()


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
        (("download_result_status", "success"), ("observed_http_status", True)),
        (("download_result_status", "success"), ("observed_http_status", IntSubclass(200))),
        (PairSubclass(("download_result_status", "success")),),
        tuple((name, value) for name, value in (*VALID_DOWNLOAD.items(), ("extra", "x"))),
    ),
)
def test_projection_rejects_wrong_container_pair_order_type_and_extra(pairs: object) -> None:
    with pytest.raises(TypeError):
        runtime._project_download_result_pairs_to_exact_string_pairs(pairs)


def test_exact13_projection_has_no_integer_pair_values() -> None:
    value = route({})
    assert all(type(item) is str for _, item in value.normalized_values)
    assert all(type(item) is str for _, item in value.validated_candidate_fields)
    assert value.consumed_candidate_fields == DOWNLOAD_FIELDS


def test_historical_candidate_field_names_hold_download_result_semantics() -> None:
    value = route({})
    assert value.validated_candidate_fields[0][0] == "download_result_status"
    assert value.consumed_candidate_fields == DOWNLOAD_FIELDS
    assert not any(name in {} for name in value.consumed_candidate_fields)


@pytest.mark.parametrize(
    ("rule_id", "code", "known"),
    (
        (12, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", False),
        ("ADMIT_013", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True),
        ("ADMIT_014", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True),
        ("ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True),
    ),
)
def test_public_dispatcher_fail_closed_precedence(
    rule_id: object, code: str, known: bool
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime.evaluate_admission_rule(rule_id, {})
    assert captured.value.code == code
    assert captured.value.known_rule is known


def test_admit012_is_registered_in_public_dispatcher() -> None:
    value = runtime.evaluate_admission_rule(
        "ADMIT_012",
        {},
        evaluation_context=VALID_CONTEXT,
        download_result_context=VALID_DOWNLOAD,
    )
    assert value.outcome == "passed"


@pytest.mark.parametrize("rule_id", KNOWN[:11])
def test_old_rule_default_dispatch_behavior_regression(rule_id: str) -> None:
    def observe(module: object) -> tuple[str, tuple[object, ...]]:
        try:
            value = module.evaluate_admission_rule(rule_id, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            return "error", tuple(getattr(error, name) for name in ERROR_FIELDS)
        return "result", tuple(getattr(value, name) for name in RESULT_FIELDS)

    assert observe(runtime) == observe(PREDECESSOR)


def test_no_aggregation_or_combined_verdict_api() -> None:
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")


def test_public_closure_marker_hashes_calls_and_bindings() -> None:
    attested = checker._attest_successor_source_before_import()
    checker._verify_runtime_ast(attested)
    manifest = json.loads((OUTPUT_ROOT / runtime.MANIFEST_FILENAME).read_text())
    assert manifest["public_closure_attestation"]["definition_count"] == 11
    assert manifest["public_closure_attestation"]["production_full_sha256"] == checker.EXPECTED_SOURCE_SHA256
    assert manifest["public_closure_attestation"]["marker_prefix_sha256"] == checker.EXPECTED_MARKER_PREFIX_SHA256


def test_adapter_design_classifier_absent_from_runtime_prefix() -> None:
    source = (ROOT / checker.SOURCE_RELATIVE_PATH).read_text()
    prefix = source.split(checker.MARKER, 1)[0]
    assert "classify_admit_012_unified_adapter_design" not in prefix
    assert "covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate" not in prefix


@pytest.mark.parametrize(
    "mutation",
    (
        "local_import",
        "indirect_io",
        "dynamic_call",
        "handler_rebinding",
        "second_marker",
    ),
)
def test_static_checker_rejects_public_closure_or_binding_bypass(mutation: str) -> None:
    source = (ROOT / checker.SOURCE_RELATIVE_PATH).read_text()
    if mutation == "local_import":
        changed = source.replace(
            "def _admit012_context_failure(reason: str) -> NoReturn:\n",
            "def _admit012_context_failure(reason: str) -> NoReturn:\n    import os\n",
            1,
        )
    elif mutation == "indirect_io":
        changed = source.replace("return handler(\n", "return open('/tmp/forbidden') and handler(\n", 1)
    elif mutation == "dynamic_call":
        changed = source.replace("return handler(\n", "return globals()['handler'](\n", 1)
    elif mutation == "handler_rebinding":
        changed = source + "\nEVALUATOR_REGISTRY = {}\n"
    else:
        changed = source + f"\n{checker.MARKER}\n"
    with pytest.raises(AssertionError):
        checker._verify_runtime_ast(changed.encode())


def test_source_attestation_rejects_inode_replacement(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    target = root / checker.SOURCE_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / checker.SOURCE_RELATIVE_PATH).read_bytes())

    def replace(event: str, **kwargs: object) -> None:
        if event == "before_open":
            old = target.with_suffix(".old")
            target.rename(old)
            target.write_bytes(old.read_bytes())

    with pytest.raises(AssertionError):
        checker._attest_successor_source_before_import(
            root,
            expected_sha256=checker.EXPECTED_SOURCE_SHA256,
            event_hook=replace,
        )


def test_source_boundary_exact23_triple_hash_and_no_protected_paths() -> None:
    records = checker._verify_sources()
    assert len(records) == 23
    assert [row["source_relative_path"] for row in records] == [
        path for path, _ in checker.SOURCE_BOUNDARY
    ]
    assert all(
        row["expected_sha256"] == hashlib.sha256(row["content"]).hexdigest()
        for row in records
    )
    assert not any(
        path.startswith("data/raw/") or path.startswith("checkpoints/")
        for path, _ in checker.SOURCE_BOUNDARY
    )


def test_runtime_state_exact_counts_issue_transition_and_readiness() -> None:
    state = runtime.build_runtime_state(runtime.build_frozen_source_snapshot())
    assert tuple(
        len(state[name])
        for name in (
            "contract_rows",
            "truth_rows",
            "registry_rows",
            "safety_rows",
            "issue_rows",
        )
    ) == (42, 694, 39, 29, 16)
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    coverage = issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
    assert coverage["integration_transition"] == "unified_dispatch_runtime_with_admit_001_to_012_implemented_v1"
    assert issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open"


def test_manifest_readiness_and_historical_name_note() -> None:
    manifest = json.loads((OUTPUT_ROOT / runtime.MANIFEST_FILENAME).read_text())
    assert all(manifest[name] is True for name in runtime.TRUE_READINESS)
    assert all(manifest[name] is False for name in runtime.FALSE_READINESS)
    assert manifest["recommended_next_step"] == "audit_covapie_admit_013_formal_evaluator_interface_preconditions_v1"
    assert "download-result semantics" in manifest["historical_candidate_field_names_note"]
    assert manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"


def test_exact_six_output_tree_and_independent_checker_semantics() -> None:
    hashes = checker._validate_output_tree()
    assert hashes == checker.FROZEN_OUTPUT_SHA256


def test_deterministic_double_materialization_and_inode_noop(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(first)
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(second)
    first_bytes = checker._output_bytes(first)
    assert first_bytes == checker._output_bytes(second) == checker._output_bytes(OUTPUT_ROOT)
    inodes = {name: (first / name).stat().st_ino for name in runtime.OUTPUT_FILES}
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(first)
    assert inodes == {name: (first / name).stat().st_ino for name in runtime.OUTPUT_FILES}


def test_gpfs_einval_fails_closed_without_replace_or_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(target)
    assert captured.value.errno == errno.EINVAL
    assert not target.exists()
    assert not replace_called
    assert not tuple(tmp_path.glob(".exact12-runtime-stage-*"))


def test_existing_output_mismatch_fails_without_repair(tmp_path: Path) -> None:
    target = tmp_path / "set"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(target)
    leaf = target / runtime.CONTRACT_FILENAME
    before = leaf.read_bytes()
    leaf.write_bytes(before + b"tamper\n")
    with pytest.raises(ValueError, match="repair forbidden"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(target)
    assert leaf.read_bytes() == before + b"tamper\n"


@pytest.mark.parametrize("shape", ("escape", "symlink_root", "extra_leaf"))
def test_materializer_rejects_output_traversal_and_unsafe_shapes(
    shape: str, tmp_path: Path
) -> None:
    if shape == "escape":
        with pytest.raises(ValueError, match="escape"):
            runtime._inspect_output_target_read_only(Path("../escape"), ROOT)
        return
    target = tmp_path / "set"
    if shape == "symlink_root":
        real = tmp_path / "real"
        real.mkdir()
        target.symlink_to(real, target_is_directory=True)
    else:
        target.mkdir()
        (target / "extra").write_text("x")
    with pytest.raises(ValueError):
        runtime._inspect_output_target_read_only(target, ROOT)


@pytest.mark.parametrize("output_name", checker.OUTPUTS[:5])
def test_checker_rejects_synchronized_csv_tamper_without_frozen_byte_hash(
    output_name: str, tmp_path: Path
) -> None:
    target = tmp_path / "set"
    shutil.copytree(OUTPUT_ROOT, target)
    path = target / output_name
    rows = list(__import__("csv").DictReader(path.open(newline="")))
    columns = tuple(rows[0])
    field = next(name for name in columns if name not in {columns[0], "case_passed", "contract_passed", "audit_passed", "safety_passed"})
    rows[0][field] += "_tamper"
    with path.open("w", newline="") as stream:
        writer = __import__("csv").DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(AssertionError):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


def test_checker_rejects_synchronized_manifest_tamper(tmp_path: Path) -> None:
    target = tmp_path / "set"
    shutil.copytree(OUTPUT_ROOT, target)
    path = target / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    manifest["recommended_next_step"] = "tampered"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(target, enforce_frozen_hashes=False)


def test_checker_pinned_output_rejects_symlink_leaf(tmp_path: Path) -> None:
    target = tmp_path / "set"
    shutil.copytree(OUTPUT_ROOT, target)
    leaf = target / runtime.CONTRACT_FILENAME
    content = leaf.read_bytes()
    leaf.unlink()
    outside = tmp_path / "outside"
    outside.write_bytes(content)
    leaf.symlink_to(outside)
    with pytest.raises(AssertionError):
        checker._output_bytes(target)


def test_checker_top_level_imports_are_standard_library_only() -> None:
    tree = ast.parse(CHECKER_PATH.read_text())
    project = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            project.extend(alias.name for alias in node.names if alias.name.startswith("covalent_ext"))
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("covalent_ext"):
            project.append(node.module)
    assert project == []


@pytest.mark.parametrize("module_path", (ROOT / checker.SOURCE_RELATIVE_PATH, CHECKER_PATH))
def test_production_and_checker_isolated_imports_are_silent(module_path: Path) -> None:
    if module_path == CHECKER_PATH:
        script = (
            "import importlib.util\n"
            f"s=importlib.util.spec_from_file_location('isolated_checker',{str(module_path)!r})\n"
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)\n"
        )
    else:
        script = f"import {checker.MODULE}\n"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC)
    completed = subprocess.run(
        (sys.executable, "-B", "-c", script),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_exact_ten_authorized_files_and_no_forbidden_artifacts() -> None:
    untracked = subprocess.run(
        ("git", "ls-files", "--others", "--exclude-standard"),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    paths = set(untracked)
    expected = {
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py",
        "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1.py",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1.py",
        "docs/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1_summary.md",
        *(f"{runtime.DEFAULT_OUTPUT_ROOT.as_posix()}/{name}" for name in runtime.OUTPUT_FILES),
    }
    assert paths == expected
    assert subprocess.run(
        ("git", "diff", "--name-only"), cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout == ""
    assert subprocess.run(
        ("git", "diff", "--cached", "--name-only"),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout == ""
    forbidden = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part")
    assert not any(path.endswith(forbidden) for path in paths)
