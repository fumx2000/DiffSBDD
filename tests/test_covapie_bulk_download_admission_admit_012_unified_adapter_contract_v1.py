from __future__ import annotations

import ast
import csv
import errno
import hashlib
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

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate
    as oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_012_rule_logic_interface as standalone,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate
    as gate,
)
from covalent_ext import (
    covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004
    as original_runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011
    as runtime,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / gate.DEFAULT_OUTPUT_ROOT
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1.py"
SHA = "0123456789abcdef" * 4
CONTEXT = {
    "allowed_download_result_statuses": standalone.ALLOWED_DOWNLOAD_RESULT_STATUSES,
    "successful_http_status_contract": standalone.SUCCESSFUL_HTTP_STATUS_CONTRACT,
    "content_length_contract": standalone.CONTENT_LENGTH_CONTRACT,
    "sha256_format_contract": standalone.SHA256_FORMAT_CONTRACT,
}
DOWNLOAD = {
    "download_result_status": "success",
    "observed_http_status": 200,
    "observed_content_length_bytes": 1,
    "observed_sha256": SHA,
}


def checker_module():
    spec = importlib.util.spec_from_file_location("admit012_adapter_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def route(candidate: object = None, **overrides: object):
    arguments = {
        "batch_context": None,
        "evaluation_context": dict(CONTEXT),
        "download_result_context": dict(DOWNLOAD),
        "stage_authorization_context": None,
    }
    arguments.update(overrides)
    return gate.classify_admit_012_unified_adapter_design(
        {} if candidate is None else candidate, **arguments
    )


class CountingMapping(Mapping):
    def __init__(
        self,
        values: dict[str, object],
        *,
        repeat_bomb: bool = False,
        iteration_bomb: bool = False,
    ) -> None:
        self.values = values
        self.repeat_bomb = repeat_bomb
        self.iteration_bomb = iteration_bomb
        self.calls: list[object] = []
        self.iterated = False

    def __getitem__(self, key: object) -> object:
        self.calls.append(key)
        if self.repeat_bomb and self.calls.count(key) > 1:
            raise RuntimeError("duplicate lookup")
        return self.values[key]  # type: ignore[index]

    def __iter__(self):
        self.iterated = True
        if self.iteration_bomb:
            raise AssertionError("mapping iteration forbidden")
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)


class Bomb:
    def __getattribute__(self, name: str):
        raise AssertionError(f"bomb accessed: {name}")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or ())
        rows = list(reader)
    assert header and rows and all(tuple(row) == tuple(header) for row in rows)
    return header, rows


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=header, lineterminator="\n", extrasaction="raise"
        )
        writer.writeheader()
        writer.writerows(rows)


def copied_outputs(tmp_path: Path, name: str) -> Path:
    copied = tmp_path / name
    shutil.copytree(OUTPUT_ROOT, copied)
    return copied


def sync_manifest_sha(copied: Path, filename: str) -> None:
    manifest_path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][filename] = hashlib.sha256(
        (copied / filename).read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def test_identity_current_future_and_known_orders() -> None:
    assert (gate.PROJECT, gate.STEP, gate.STAGE) == (
        "CovaPIE",
        "ADMIT_012 unified adapter contract design gate v1",
        "covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1",
    )
    assert (gate.ADMISSION_RULE_ID, gate.ADMISSION_RULE_NAME, gate.ADAPTER_ID) == (
        "ADMIT_012",
        "future_download_integrity_fields_required",
        "covapie_admit_012_unified_adapter_v1",
    )
    assert gate.CURRENT_REGISTERED_RULE_ORDER == tuple(
        f"ADMIT_{number:03d}" for number in range(1, 12)
    )
    assert gate.FUTURE_REGISTERED_RULE_ORDER == tuple(
        f"ADMIT_{number:03d}" for number in range(1, 13)
    )
    assert gate.KNOWN_RULE_IDS == tuple(
        f"ADMIT_{number:03d}" for number in range(1, 16)
    )


def test_exact11_runtime_result_and_error_object_identity_is_unchanged() -> None:
    assert runtime.UnifiedAdmissionRuleEvaluation is original_runtime.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is original_runtime.UnifiedAdmissionDispatchError
    assert gate.RESULT_FIELDS == runtime.RESULT_FIELDS
    assert gate.DISPATCH_ERROR_FIELDS == runtime.DISPATCH_ERROR_FIELDS
    assert gate.DISPATCH_ERROR_CODES == runtime.DISPATCH_ERROR_CODES
    assert tuple(runtime.EVALUATOR_REGISTRY) == gate.CURRENT_REGISTERED_RULE_ORDER


def test_existing_exact11_handler_identities_are_preserved() -> None:
    predecessor = runtime.predecessor
    assert all(
        runtime.EVALUATOR_REGISTRY[rule_id]
        is predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in gate.CURRENT_REGISTERED_RULE_ORDER[:-1]
    )
    assert runtime.EVALUATOR_REGISTRY["ADMIT_011"] is runtime._evaluate_registered_admit_011


def test_design_source_has_no_handler_registry_dispatcher_or_result_redefinition() -> None:
    source = Path(gate.__file__).read_text()
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assignments = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "_evaluate_registered_admit_012" not in functions | assignments
    assert "evaluate_admission_rule" not in functions | assignments
    assert "EVALUATOR_REGISTRY" not in assignments
    assert "UnifiedAdmissionRuleEvaluation" not in classes
    assert "UnifiedAdmissionEvaluationDesignRecord" in classes


def test_private_standalone_missing_sentinel_is_not_imported_or_referenced() -> None:
    tree = ast.parse(Path(gate.__file__).read_bytes())
    assert not any(isinstance(node, ast.Name) and node.id == "_MISSING" for node in ast.walk(tree))
    assert gate._standalone_module() is standalone


@pytest.mark.parametrize(
    "field,value,reason",
    (
        ("batch_context", object(), "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE"),
        ("evaluation_context", None, "ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("evaluation_context", {}, "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED"),
        (
            "evaluation_context",
            {gate.POLICY_CONTEXT_ITEMS[0]: CONTEXT[gate.POLICY_CONTEXT_ITEMS[0]]},
            "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED",
        ),
        ("download_result_context", None, "ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED"),
        (
            "stage_authorization_context",
            object(),
            "ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ),
    ),
)
def test_context_routing_failures_return_exact_design_error(
    field: str, value: object, reason: str,
) -> None:
    arguments = {
        "batch_context": None,
        "evaluation_context": dict(CONTEXT),
        "download_result_context": dict(DOWNLOAD),
        "stage_authorization_context": None,
    }
    arguments[field] = value
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.classify_admit_012_unified_adapter_design(Bomb(), **arguments)
    assert caught.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "admission_rule_id": "ADMIT_012",
        "known_rule": True,
        "callable_discovered": True,
        "adapter_ready": True,
        "reason": reason,
    }


@pytest.mark.parametrize("missing_index", range(4))
def test_each_evaluation_key_missing_has_fixed_order_and_reason(missing_index: int) -> None:
    values = {
        name: CONTEXT[name]
        for name in gate.POLICY_CONTEXT_ITEMS
        if name != gate.POLICY_CONTEXT_ITEMS[missing_index]
    }
    context = CountingMapping(values, repeat_bomb=True, iteration_bomb=True)
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        route(evaluation_context=context)
    assert caught.value.reason == gate.CONTEXT_REASONS[
        gate.POLICY_CONTEXT_ITEMS[missing_index]
    ]
    assert context.calls == list(gate.POLICY_CONTEXT_ITEMS[: missing_index + 1])
    assert not context.iterated


def test_batch_failure_precedes_all_later_envelopes_and_zero_calls() -> None:
    calls = {"formal": 0, "oracle": 0}

    def formal(**kwargs: object):
        calls["formal"] += 1
        raise AssertionError

    def classify(**kwargs: object):
        calls["oracle"] += 1
        raise AssertionError

    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.classify_admit_012_unified_adapter_design(
            Bomb(), batch_context=object(), evaluation_context=Bomb(),
            download_result_context=Bomb(), stage_authorization_context=Bomb(),
            formal_evaluator=formal, oracle_callable=classify,
        )
    assert caught.value.reason == gate.CONTEXT_REASONS["batch_context"]
    assert calls == {"formal": 0, "oracle": 0}


def test_evaluation_missing_precedes_download_stage_candidate_and_zero_calls() -> None:
    context = CountingMapping({}, iteration_bomb=True)
    calls = {"formal": 0, "oracle": 0}

    def formal(**kwargs: object):
        calls["formal"] += 1

    def classify(**kwargs: object):
        calls["oracle"] += 1

    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.classify_admit_012_unified_adapter_design(
            Bomb(), batch_context=None, evaluation_context=context,
            download_result_context=object(), stage_authorization_context=Bomb(),
            formal_evaluator=formal, oracle_callable=classify,
        )
    assert caught.value.reason == gate.CONTEXT_REASONS[gate.POLICY_CONTEXT_ITEMS[0]]
    assert context.calls == [gate.POLICY_CONTEXT_ITEMS[0]]
    assert calls == {"formal": 0, "oracle": 0}


def test_download_mapping_gate_precedes_stage_and_candidate() -> None:
    context = CountingMapping(dict(CONTEXT), repeat_bomb=True, iteration_bomb=True)
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.classify_admit_012_unified_adapter_design(
            Bomb(), batch_context=None, evaluation_context=context,
            download_result_context=object(), stage_authorization_context=Bomb(),
        )
    assert caught.value.reason == gate.CONTEXT_REASONS["download_result_context"]
    assert context.calls == list(gate.POLICY_CONTEXT_ITEMS)
    assert not context.iterated


def test_stage_gate_precedes_candidate_and_download_field_access() -> None:
    download = CountingMapping(dict(DOWNLOAD), iteration_bomb=True)
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.classify_admit_012_unified_adapter_design(
            Bomb(), batch_context=None, evaluation_context=dict(CONTEXT),
            download_result_context=download, stage_authorization_context=object(),
        )
    assert caught.value.reason == gate.CONTEXT_REASONS["stage_authorization_context"]
    assert download.calls == [] and not download.iterated


def test_candidate_non_mapping_exact13_has_zero_candidate_access_and_zero_calls() -> None:
    calls = {"formal": 0, "oracle": 0}

    def formal(**kwargs: object):
        calls["formal"] += 1
        raise AssertionError

    def classify(**kwargs: object):
        calls["oracle"] += 1
        raise AssertionError

    result = route(object(), formal_evaluator=formal, oracle_callable=classify)
    assert result == gate.candidate_invalid_exact13_for_design()
    assert tuple(getattr(result, name) for name in gate.RESULT_FIELDS) == (
        gate.RESULT_SCHEMA_VERSION,
        "ADMIT_012",
        "future_download_integrity_fields_required",
        "invalid",
        False,
        True,
        gate.CANDIDATE_MAPPING_REASON,
        (),
        (),
        (),
        gate.POLICY_CONTEXT_ITEMS,
        False,
        gate.ADAPTER_ID,
    )
    assert calls == {"formal": 0, "oracle": 0}


@pytest.mark.parametrize("candidate_values", ({}, {"extra": Bomb()}))
def test_candidate_mapping_empty_or_extra_has_zero_key_access(
    candidate_values: dict[str, object],
) -> None:
    candidate = CountingMapping(
        candidate_values, repeat_bomb=True, iteration_bomb=True
    )
    result = route(candidate)
    assert result.outcome == "passed"
    assert candidate.calls == [] and not candidate.iterated


def test_context_and_download_mapping_subclasses_lookup_once_ignore_extras() -> None:
    context = CountingMapping(
        {**CONTEXT, "extra": Bomb()}, repeat_bomb=True, iteration_bomb=True
    )
    download = CountingMapping(
        {**DOWNLOAD, "extra": Bomb()}, repeat_bomb=True, iteration_bomb=True
    )
    result = route(evaluation_context=context, download_result_context=download)
    assert result.outcome == "passed"
    assert context.calls == list(gate.POLICY_CONTEXT_ITEMS)
    assert download.calls == list(gate.DOWNLOAD_RESULT_FIELDS)
    assert not context.iterated and not download.iterated


@pytest.mark.parametrize("missing_index", range(4))
def test_first_missing_stops_later_download_lookups_and_omits_keywords(
    missing_index: int,
) -> None:
    values = {
        name: DOWNLOAD[name]
        for name in gate.DOWNLOAD_RESULT_FIELDS
        if name != gate.DOWNLOAD_RESULT_FIELDS[missing_index]
    }
    download = CountingMapping(values, repeat_bomb=True, iteration_bomb=True)
    formal_seen: list[dict[str, object]] = []
    oracle_seen: list[dict[str, object]] = []

    def formal(**kwargs: object):
        formal_seen.append(kwargs)
        return standalone.evaluate_admit_012(**kwargs)

    def classify(**kwargs: object):
        oracle_seen.append(kwargs)
        return oracle.classify_admit_012_formal_evaluator_interface_design(**kwargs)

    result = route(
        download_result_context=download,
        formal_evaluator=formal,
        oracle_callable=classify,
    )
    assert result.outcome == "blocked"
    assert result.reason == standalone.MISSING_REASONS[missing_index]
    assert download.calls == list(gate.DOWNLOAD_RESULT_FIELDS[: missing_index + 1])
    assert not download.iterated
    expected_keys = (*gate.DOWNLOAD_RESULT_FIELDS[:missing_index], *gate.POLICY_CONTEXT_ITEMS)
    assert tuple(formal_seen[0]) == expected_keys
    assert tuple(oracle_seen[0]) == expected_keys
    assert len(formal_seen) == len(oracle_seen) == 1


def test_empty_download_mapping_omits_all_fields_and_calls_both_once() -> None:
    download = CountingMapping({}, repeat_bomb=True, iteration_bomb=True)
    formal_seen = []
    oracle_seen = []

    def formal(**kwargs: object):
        formal_seen.append(kwargs)
        return standalone.evaluate_admit_012(**kwargs)

    def classify(**kwargs: object):
        oracle_seen.append(kwargs)
        return oracle.classify_admit_012_formal_evaluator_interface_design(**kwargs)

    result = route(
        download_result_context=download,
        formal_evaluator=formal,
        oracle_callable=classify,
    )
    assert result.reason == "DOWNLOAD_RESULT_STATUS_MISSING"
    assert download.calls == [gate.DOWNLOAD_RESULT_FIELDS[0]]
    assert tuple(formal_seen[0]) == tuple(oracle_seen[0]) == gate.POLICY_CONTEXT_ITEMS


@pytest.mark.parametrize(
    "field,value,expected_reason",
    (
        ("download_result_status", None, "DOWNLOAD_RESULT_STATUS_TYPE_INVALID"),
        ("observed_http_status", False, "OBSERVED_HTTP_STATUS_TYPE_INVALID"),
        ("observed_content_length_bytes", 0, ""),
    ),
)
def test_present_none_false_and_zero_are_not_missing(
    field: str, value: object, expected_reason: str,
) -> None:
    download = dict(DOWNLOAD)
    download[field] = value
    result = route(download_result_context=download)
    assert result.reason == expected_reason
    assert not result.reason.endswith("_MISSING")


def test_formal_and_oracle_receive_same_original_objects_keyword_only_once() -> None:
    field_values = {name: object() for name in gate.DOWNLOAD_RESULT_FIELDS}
    context_values = {name: object() for name in gate.POLICY_CONTEXT_ITEMS}
    formal_seen: list[dict[str, object]] = []
    oracle_seen: list[dict[str, object]] = []

    def formal(**kwargs: object):
        formal_seen.append(kwargs)
        return standalone.evaluate_admit_012(**kwargs)

    def classify(**kwargs: object):
        oracle_seen.append(kwargs)
        return oracle.classify_admit_012_formal_evaluator_interface_design(**kwargs)

    result = route(
        evaluation_context=context_values,
        download_result_context=field_values,
        formal_evaluator=formal,
        oracle_callable=classify,
    )
    assert result.reason == "DOWNLOAD_RESULT_STATUS_TYPE_INVALID"
    assert len(formal_seen) == len(oracle_seen) == 1
    expected_order = (*gate.DOWNLOAD_RESULT_FIELDS, *gate.POLICY_CONTEXT_ITEMS)
    assert tuple(formal_seen[0]) == tuple(oracle_seen[0]) == expected_order
    for name in expected_order:
        expected = field_values.get(name, context_values.get(name))
        assert formal_seen[0][name] is expected
        assert oracle_seen[0][name] is expected


def test_formal_exception_propagates_and_prevents_oracle_call() -> None:
    calls = {"formal": 0, "oracle": 0}

    def formal(**kwargs: object):
        calls["formal"] += 1
        raise RuntimeError("formal failed")

    def classify(**kwargs: object):
        calls["oracle"] += 1

    with pytest.raises(RuntimeError, match="formal failed"):
        route(formal_evaluator=formal, oracle_callable=classify)
    assert calls == {"formal": 1, "oracle": 0}


@pytest.mark.parametrize("source", (object(), None, {"outcome": "passed"}))
def test_wrong_formal_source_type_fails_before_oracle(source: object) -> None:
    calls = {"oracle": 0}

    def classify(**kwargs: object):
        calls["oracle"] += 1

    with pytest.raises(gate.AdapterContractDesignError) as caught:
        route(formal_evaluator=lambda **kwargs: source, oracle_callable=classify)
    assert caught.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "admission_rule_id": "ADMIT_012",
        "known_rule": True,
        "callable_discovered": True,
        "adapter_ready": False,
        "reason": gate.SOURCE_TYPE_REASON,
    }
    assert calls["oracle"] == 0


def valid_source():
    return standalone.evaluate_admit_012(**DOWNLOAD, **CONTEXT)


def test_formal_source_exact_type_storage_order_and_reconstruction() -> None:
    source = valid_source()
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert decision.accepted
    assert type(vars(source)) is dict
    assert tuple(vars(source)) == gate.STANDALONE_RESULT_FIELDS
    values = tuple(getattr(source, name) for name in gate.STANDALONE_RESULT_FIELDS)
    assert standalone.Admit012EvaluationResult(*values) == source


def test_formal_source_subclass_is_rejected_as_type_invalid() -> None:
    class Subclass(standalone.Admit012EvaluationResult):
        pass

    source = object.__new__(Subclass)
    valid = valid_source()
    for name in gate.STANDALONE_RESULT_FIELDS:
        object.__setattr__(source, name, getattr(valid, name))
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.reason == gate.SOURCE_TYPE_REASON


def test_formal_source_wrong_storage_order_is_invariant_invalid() -> None:
    source = valid_source()
    storage = vars(source)
    value = storage.pop("admission_rule_id")
    storage["admission_rule_id"] = value
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


@pytest.mark.parametrize(
    "name,value",
    (
        ("passed", 1),
        ("admission_rule_id", "ADMIT_999"),
        ("evaluator_io_used", True),
        ("consumed_context_items", ()),
    ),
)
def test_formal_source_top_level_or_reason_invariant_tamper_is_rejected(
    name: str, value: object,
) -> None:
    source = valid_source()
    object.__setattr__(source, name, value)
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


def test_formal_source_wrong_canonical_pair_type_is_rejected() -> None:
    source = valid_source()
    canonical = list(source.canonical_download_result_record)
    canonical[0] = list(canonical[0])
    object.__setattr__(source, "canonical_download_result_record", tuple(canonical))
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


def test_oracle_exact_type_storage_and_complete_exact10_conversion() -> None:
    classification = oracle.classify_admit_012_formal_evaluator_interface_design(
        **DOWNLOAD, **CONTEXT
    )
    expected = gate.expected_exact10_from_committed_oracle_for_design(
        DOWNLOAD, CONTEXT
    )
    assert type(classification) is oracle.Admit012EvaluationResultContractDesign
    assert type(expected) is standalone.Admit012EvaluationResult
    assert tuple(vars(classification)) == gate.STANDALONE_RESULT_FIELDS
    assert tuple(getattr(expected, name) for name in gate.STANDALONE_RESULT_FIELDS) == tuple(
        getattr(classification, name) for name in gate.STANDALONE_RESULT_FIELDS
    )


@pytest.mark.parametrize("mode", ("exception", "wrong_type", "storage", "mismatch"))
def test_oracle_failures_are_adapter_not_ready(mode: str) -> None:
    def classify(**kwargs: object):
        if mode == "exception":
            raise RuntimeError("oracle failed")
        if mode == "wrong_type":
            return valid_source()
        if mode == "storage":
            value = oracle.classify_admit_012_formal_evaluator_interface_design(
                **DOWNLOAD, **CONTEXT
            )
            storage = vars(value)
            item = storage.pop("admission_rule_id")
            storage["admission_rule_id"] = item
            return value
        changed = dict(DOWNLOAD)
        changed["download_result_status"] = "failure"
        return oracle.classify_admit_012_formal_evaluator_interface_design(
            **changed, **CONTEXT
        )

    with pytest.raises(gate.AdapterContractDesignError) as caught:
        route(oracle_callable=classify)
    assert caught.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "admission_rule_id": "ADMIT_012",
        "known_rule": True,
        "callable_discovered": True,
        "adapter_ready": False,
        "reason": gate.SOURCE_INVARIANT_REASON,
    }


def test_full_exact10_equality_includes_every_field_and_type() -> None:
    source = valid_source()
    expected = gate.expected_exact10_from_committed_oracle_for_design(DOWNLOAD, CONTEXT)
    decision = gate.validate_source_oracle_equivalence_for_design(source, expected)
    assert decision.accepted
    object.__setattr__(expected, "consumed_context_items", ())
    decision = gate.validate_source_oracle_equivalence_for_design(source, expected)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


@pytest.mark.parametrize(
    "pairs,expected",
    (
        ((), ()),
        (
            (("download_result_status", "success"),),
            (("download_result_status", "success"),),
        ),
        (
            (
                ("download_result_status", "failure"),
                ("observed_http_status", 0),
                ("observed_content_length_bytes", 200),
                ("observed_sha256", SHA),
            ),
            (
                ("download_result_status", "failure"),
                ("observed_http_status", "0"),
                ("observed_content_length_bytes", "200"),
                ("observed_sha256", SHA),
            ),
        ),
    ),
)
def test_typed_to_string_projection_rules(
    pairs: tuple, expected: tuple | None,
) -> None:
    if expected is None:
        expected = pairs
    assert gate.project_download_result_pairs_to_exact_string_pairs(pairs) == expected


@pytest.mark.parametrize("integer", (0, 1, 200, 10**100))
def test_projection_uses_canonical_decimal_for_zero_and_large_ints(integer: int) -> None:
    pairs = (
        ("download_result_status", "success"),
        ("observed_http_status", integer),
    )
    assert gate.project_download_result_pairs_to_exact_string_pairs(pairs)[1][1] == str(integer)


@pytest.mark.parametrize(
    "pairs",
    (
        (("download_result_status", str.__new__(type("S", (str,), {}), "success")),),
        (("download_result_status", "success"), ("observed_http_status", True)),
        (
            ("download_result_status", "success"),
            ("observed_http_status", type("I", (int,), {})(200)),
        ),
        (["download_result_status", "success"],),
    ),
)
def test_projection_rejects_subclasses_bool_and_non_tuple_pairs(pairs: tuple) -> None:
    with pytest.raises(TypeError):
        gate.project_download_result_pairs_to_exact_string_pairs(pairs)


def test_projection_preserves_prefix_length_names_status_sha_and_never_int() -> None:
    full = (
        ("download_result_status", "failure"),
        ("observed_http_status", 404),
        ("observed_content_length_bytes", 10**50),
        ("observed_sha256", SHA),
    )
    for length in range(5):
        projected = gate.project_download_result_pairs_to_exact_string_pairs(full[:length])
        assert len(projected) == length
        assert tuple(pair[0] for pair in projected) == gate.DOWNLOAD_RESULT_FIELDS[:length]
        assert all(type(name) is str and type(value) is str for name, value in projected)


@pytest.mark.parametrize(
    "status,http,content",
    (
        ("success", 100, 0),
        ("success", 200, 1),
        ("failure", 404, 10**80),
        ("failure", 599, 0),
    ),
)
def test_exact13_full_projection_and_failure_4xx_5xx_remain_passed(
    status: str, http: int, content: int,
) -> None:
    download = {
        "download_result_status": status,
        "observed_http_status": http,
        "observed_content_length_bytes": content,
        "observed_sha256": SHA,
    }
    result = route(download_result_context=download)
    assert result.outcome == "passed" and result.passed is True
    assert result.normalized_values == (
        ("download_result_status", status),
        ("observed_http_status", str(http)),
        ("observed_content_length_bytes", str(content)),
        ("observed_sha256", SHA),
    )
    assert result.validated_candidate_fields == result.normalized_values
    assert result.consumed_candidate_fields == gate.DOWNLOAD_RESULT_FIELDS
    assert result.consumed_context_items == gate.POLICY_CONTEXT_ITEMS
    assert all(type(value) is str for _, value in result.normalized_values)


def test_historical_candidate_field_names_carry_download_result_semantics() -> None:
    result = route()
    assert result.validated_candidate_fields[0][0] == "download_result_status"
    assert result.consumed_candidate_fields == gate.DOWNLOAD_RESULT_FIELDS
    assert not any(name in {} for name in result.consumed_candidate_fields)
    manifest = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILENAME).read_text())
    assert "do not imply candidate_record sourcing" in manifest[
        "historical_candidate_field_names_note"
    ]


def test_all_exact105_formal_cases_have_one_formal_one_oracle_and_exact13() -> None:
    state = gate.build_design_state()
    assert len(state["truth_rows"]) == 148
    rows = state["truth_rows"][:105]
    assert len(rows) == 105
    assert all(
        row["formal_call_count"] == row["oracle_call_count"] == "1"
        and row["candidate_key_access_count"] == "0"
        and row["case_passed"] == "true"
        for row in rows
    )
    for row in rows:
        source = json.loads(row["source_exact10_json"])
        expected = json.loads(row["oracle_exact10_json"])
        projected = json.loads(row["projected_exact13_json"])
        assert source == expected
        assert tuple(projected) == gate.RESULT_FIELDS
        assert all(
            type(value) is str
            for _, value in (
                *projected["normalized_values"],
                *projected["validated_candidate_fields"],
            )
        )


def test_truth_matrix_group_counts_and_projection_boundaries() -> None:
    rows = gate.build_design_state()["truth_rows"][:105]
    groups = {group: sum(row["case_group"] == group for row in rows) for group in {row["case_group"] for row in rows}}
    assert groups["context_validation"] == 39
    assert groups["result_invariant_negative"] == 8
    assert groups["field52_missing"] == 6
    assert groups["field52_admit_013_boundary"] == 3


def test_truth_matrix_includes_all_exact43_adapter_contract_cases() -> None:
    state = gate.build_design_state()
    routing = state["routing_rows"]
    adapter_truth = state["truth_rows"][105:]
    assert len(routing) == len(adapter_truth) == 43
    assert tuple(row["case_id"] for row in adapter_truth) == tuple(
        f"ADAPTER_{row['case_id'].upper()}" for row in routing
    )
    assert sum(int(row["formal_call_count"]) for row in state["truth_rows"]) == 135
    assert sum(int(row["oracle_call_count"]) for row in state["truth_rows"]) == 130
    assert {
        row["case_group"] for row in adapter_truth
    } == {
        "adapter_routing_failure", "adapter_candidate", "adapter_first_missing",
        "adapter_lookup", "adapter_call", "adapter_source_failure",
        "adapter_oracle_failure", "adapter_projection", "adapter_registry",
    }


def test_source_boundary_exact19_base_lineage_and_pinned_hashes() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert len(snapshot.records) == 19
    assert tuple(record.relative_path.as_posix() for record in snapshot.records) == tuple(
        path for path, _ in gate.SOURCE_BOUNDARY
    )
    assert all(
        record.expected_sha256
        == record.base_tree_sha256
        == record.filesystem_sha256
        for record in snapshot.records
    )
    assert gate.SOURCE_PATH_LIST_SHA256 == "c541a32eb23ac4bc0e95f4778923b6d24f62cc8623c6b25992725c32eb66c233"
    assert gate.SOURCE_PATH_SHA256_PAIRS_SHA256 == "e40b85438e3f2068efd3747b050763a9ee9d98e92baebca928c20a3fcb9b2f4e"


def test_issue_continuity_exact16_and_required_open_resolved_states() -> None:
    state = gate.build_design_state()
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    assert len(issues) == 16
    for issue_id in (
        "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
        "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
        "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED",
        "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
        "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
        "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    ):
        assert issues[issue_id]["status"] == "resolved"
    coverage = issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    assert issues[
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    ]["status"] == "open"


def test_readiness_and_recommended_next_step_are_exact() -> None:
    manifest = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILENAME).read_text())
    assert all(
        manifest[name] is True and manifest["readiness"][name] is True
        for name in gate.TRUE_READINESS
    )
    assert all(
        manifest[name] is False and manifest["readiness"][name] is False
        for name in gate.FALSE_READINESS
    )
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"


def test_exact_six_outputs_headers_and_frozen_hashes() -> None:
    checker = checker_module()
    assert checker._validate_output_tree() == checker.FROZEN_OUTPUT_SHA256
    assert tuple(path.name for path in OUTPUT_ROOT.iterdir()) != ()
    assert set(path.name for path in OUTPUT_ROOT.iterdir()) == set(gate.OUTPUT_FILES)


def test_deterministic_double_materialization_and_existing_set_noop(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(first)
    gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(second)
    first_bytes = {name: (first / name).read_bytes() for name in gate.OUTPUT_FILES}
    second_bytes = {name: (second / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first_bytes == second_bytes
    inodes = {name: (first / name).stat().st_ino for name in gate.OUTPUT_FILES}
    gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(first)
    assert inodes == {name: (first / name).stat().st_ino for name in gate.OUTPUT_FILES}


def test_materializer_gpfs_einval_fails_closed_without_staging_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"

    def fail(parent_fd: int, source: str, target: str) -> None:
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL), f"{source}->{target}")

    monkeypatch.setattr(gate, "_rename_noreplace", fail)
    with pytest.raises(OSError) as caught:
        gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(root)
    assert caught.value.errno == errno.EINVAL
    assert not root.exists()
    assert not tuple(tmp_path.glob(".admit012-adapter-stage-*"))


def test_materializer_existing_mismatch_fails_closed_without_repair(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(root)
    target = root / gate.CONTRACT_FILENAME
    target.write_bytes(b"tampered\n")
    before = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    with pytest.raises(ValueError, match="repair forbidden"):
        gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(root)
    assert before == {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}


@pytest.mark.parametrize("kind", ("root_symlink", "root_file", "unexpected", "leaf_symlink"))
def test_materializer_rejects_output_traversal_and_unsafe_shapes(
    tmp_path: Path, kind: str,
) -> None:
    root = tmp_path / "evidence"
    if kind == "root_symlink":
        target = tmp_path / "target"
        target.mkdir()
        root.symlink_to(target, target_is_directory=True)
    elif kind == "root_file":
        root.write_text("x")
    else:
        gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(root)
        if kind == "unexpected":
            (root / "unexpected").write_text("x")
        else:
            leaf = root / gate.CONTRACT_FILENAME
            leaf.unlink()
            leaf.symlink_to(root / gate.ROUTING_FILENAME)
    with pytest.raises(ValueError):
        gate.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(root)


@pytest.mark.parametrize(
    "filename,column,replacement",
    (
        (gate.CONTRACT_FILENAME, "contract_value", "tampered"),
        (gate.ROUTING_FILENAME, "lookup_order", "tampered"),
        (gate.TRUTH_FILENAME, "formal_call_count", "0"),
        (gate.SAFETY_FILENAME, "observed_executed", "tampered"),
    ),
)
def test_checker_rejects_synchronized_semantic_tamper(
    tmp_path: Path, filename: str, column: str, replacement: str,
) -> None:
    copied = copied_outputs(tmp_path, column)
    path = copied / filename
    header, rows = read_csv(path)
    rows[0][column] = replacement
    write_csv(path, header, rows)
    sync_manifest_sha(copied, filename)
    with pytest.raises((AssertionError, ValueError, TypeError, KeyError)):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_rejects_synchronized_issue_tamper(tmp_path: Path) -> None:
    copied = copied_outputs(tmp_path, "issue")
    path = copied / gate.ISSUE_FILENAME
    header, rows = read_csv(path)
    coverage = next(
        row for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    assert coverage["status"] == "open"
    coverage["status"] = "resolved"
    write_csv(path, header, rows)
    sync_manifest_sha(copied, gate.ISSUE_FILENAME)
    with pytest.raises(AssertionError):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "mode",
    ("extra_key", "readiness", "source_verification", "row_count", "schema_widening"),
)
def test_checker_rejects_manifest_semantic_tamper_without_hash_enforcement(
    tmp_path: Path, mode: str,
) -> None:
    copied = copied_outputs(tmp_path, mode)
    path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    if mode == "extra_key":
        manifest["unexpected"] = True
    elif mode == "readiness":
        manifest["readiness"][gate.TRUE_READINESS[0]] = False
    elif mode == "source_verification":
        manifest["source_input_verification"][0]["tracked"] = False
    elif mode == "row_count":
        manifest["projection_truth_matrix_row_count"] = 104
    else:
        manifest["exact13_schema_widened"] = True
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_pinned_output_read_rejects_symlink_leaf(tmp_path: Path) -> None:
    copied = copied_outputs(tmp_path, "symlink")
    leaf = copied / gate.CONTRACT_FILENAME
    leaf.unlink()
    leaf.symlink_to(copied / gate.ROUTING_FILENAME)
    with pytest.raises(AssertionError):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_literal_decoder_does_not_execute_malicious_payload(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    expression = f"__import__('pathlib').Path({str(marker)!r}).write_text('owned')"
    with pytest.raises((ValueError, SyntaxError)):
        gate._decode_token(expression)
    with pytest.raises((ValueError, SyntaxError)):
        checker_module()._decode_token(expression)
    assert not marker.exists()


def test_public_design_api_signature_is_frozen() -> None:
    signature = inspect.signature(gate.classify_admit_012_unified_adapter_design)
    assert tuple(signature.parameters) == (
        "candidate_record", "batch_context", "evaluation_context",
        "download_result_context", "stage_authorization_context",
        "formal_evaluator", "oracle_callable",
    )
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in tuple(signature.parameters)[1:]
    )


def test_production_and_checker_imports_are_silent_and_side_effect_free(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "marker"
    script = (
        "import importlib.util;"
        "import covalent_ext.covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate;"
        f"s=importlib.util.spec_from_file_location('c',{str(CHECKER_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        f"assert not __import__('pathlib').Path({str(marker)!r}).exists()"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", script], cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""
    assert not marker.exists()


def test_exactly_ten_authorized_candidate_files_and_no_forbidden_artifact() -> None:
    expected = {
        "src/covalent_ext/covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate.py",
        "scripts/check_covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1.py",
        "tests/test_covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1.py",
        "docs/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1_summary.md",
        *{
            f"data/derived/covalent_small/{gate.STAGE}/{name}"
            for name in gate.OUTPUT_FILES
        },
    }
    status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"], cwd=ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    observed = {line[3:] for line in status}
    assert observed <= expected
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar",
        ".zip", ".tgz", ".npz", ".tmp", ".part",
    }
    assert not any((ROOT / path).suffix in forbidden for path in observed)
