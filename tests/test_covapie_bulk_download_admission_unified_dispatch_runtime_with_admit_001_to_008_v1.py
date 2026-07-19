from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008
    as runtime,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1.py"
)
OUTPUT_ROOT = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT


@pytest.fixture(scope="module")
def snapshot() -> runtime.FrozenSourceSnapshot:
    return runtime.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def state(snapshot: runtime.FrozenSourceSnapshot) -> dict[str, Any]:
    value = runtime.build_runtime_state(snapshot)
    assert value["all_checks_passed"] is True
    assert value["validation_failures"] == []
    return value


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "exact8_checker_for_test", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate(value: object) -> dict[str, object]:
    return {runtime.ADMIT_008_CANDIDATE_FIELDS[0]: value}


def _context(
    value: object = runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
) -> dict[str, object]:
    return {runtime.ADMIT_008_CONTEXT_ITEMS[0]: value}


def _values(value: object, names: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in names)


class _SingleLookupMapping(Mapping[str, object]):
    def __init__(self, key: str, value: object, *, present: bool = True) -> None:
        self.key = key
        self.value = value
        self.present = present
        self.lookup_count = 0

    def __getitem__(self, key: str) -> object:
        if key != self.key:
            raise KeyError(key)
        self.lookup_count += 1
        if self.lookup_count > 1:
            raise AssertionError("required field read twice")
        if not self.present:
            raise KeyError(key)
        return self.value

    def __iter__(self):
        raise AssertionError("Mapping iterated or copied")

    def __len__(self) -> int:
        raise AssertionError("Mapping sized or copied")


def _valid_source() -> runtime.admit008.Admit008EvaluationResult:
    return runtime.admit008.evaluate_admit_008(
        runtime.admit008.CANONICAL_ENUM_MEMBERS[0],
        runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )


def _mutate(value: object, name: str, replacement: object) -> object:
    object.__setattr__(value, name, replacement)
    return value


def test_exact18_order_structure_sha_and_lineage(
    snapshot: runtime.FrozenSourceSnapshot,
) -> None:
    checker = _load_checker()
    assert runtime.EXPECTED_BASE_COMMIT == (
        "f7079d9dfe5ef30889fb6fbe3bf5b66fdb0db5b0"
    )
    assert runtime.EXPECTED_BASE_SUBJECT == (
        "add CovaPIE ADMIT_008 unified adapter contract design v1"
    )
    assert len(runtime.SOURCE_PATHS) == len(set(runtime.SOURCE_PATHS)) == 18
    assert tuple(runtime.SOURCE_SHA256) == runtime.SOURCE_PATHS
    assert runtime.SOURCE_PATHS == tuple(
        Path(path) for path, _ in checker.SOURCE_BOUNDARY
    )
    assert runtime.SOURCE_SHA256 == {
        Path(path): digest for path, digest in checker.SOURCE_BOUNDARY
    }
    assert runtime.validate_frozen_source_snapshot(snapshot)
    for record in snapshot.records:
        assert record.expected_sha256 == record.base_tree_sha256
        assert record.expected_sha256 == record.filesystem_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == (
            record.expected_sha256
        )
    runtime._validate_expected_base_lineage(REPO_ROOT)


def test_all_structural_checks_precede_first_source_byte_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structural: list[Path] = []
    real_structural = runtime._structural_source_check
    real_git = runtime._git

    def counted(path: Path, root: Path) -> bool:
        structural.append(path)
        return real_structural(path, root)

    def guarded(arguments: list[str], root: Path, *, text: bool = True):
        if arguments[:1] == ["show"] and len(arguments) == 2 and ":" in arguments[1]:
            assert tuple(structural) == runtime.SOURCE_PATHS
        return real_git(arguments, root, text=text)

    monkeypatch.setattr(runtime, "_structural_source_check", counted)
    monkeypatch.setattr(runtime, "_git", guarded)
    assert runtime.validate_frozen_source_snapshot(
        runtime.build_frozen_source_snapshot()
    )


def test_source_sha_non_descendant_symlink_and_unsafe_paths_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    changed = dict(runtime.SOURCE_SHA256)
    changed[runtime.SOURCE_PATHS[0]] = "0" * 64
    monkeypatch.setattr(runtime, "SOURCE_SHA256", changed)
    with pytest.raises(ValueError, match="SHA256"):
        runtime.build_frozen_source_snapshot()
    monkeypatch.undo()

    real_git = runtime._git

    def non_descendant(arguments: list[str], root: Path, *, text: bool = True):
        if arguments[:2] == ["merge-base", "--is-ancestor"]:
            empty = "" if text else b""
            return subprocess.CompletedProcess(arguments, 1, empty, empty)
        return real_git(arguments, root, text=text)

    monkeypatch.setattr(runtime, "_git", non_descendant)
    with pytest.raises(ValueError, match="not an ancestor"):
        runtime.build_frozen_source_snapshot(head_ref="non_descendant")
    assert runtime._safe_relative_path(Path("../escape")) is False
    assert runtime._safe_relative_path(Path("data/raw/forbidden.cif")) is False
    assert runtime._safe_relative_path(Path("checkpoints/forbidden.ckpt")) is False

    victim = tmp_path / "victim"
    victim.write_text("x", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(victim)
    monkeypatch.setattr(
        runtime,
        "_git",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout="100644 blob abc\tlink\n"
        ),
    )
    assert runtime._structural_source_check(Path("link"), tmp_path) is False


def test_public_type_constant_and_signature_identity() -> None:
    assert (
        runtime.UnifiedAdmissionRuleEvaluation
        is runtime.predecessor.UnifiedAdmissionRuleEvaluation
    )
    assert (
        runtime.UnifiedAdmissionDispatchError
        is runtime.predecessor.UnifiedAdmissionDispatchError
    )
    for name in (
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        assert getattr(runtime, name) is getattr(runtime.predecessor, name)
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        runtime.predecessor.evaluate_admission_rule
    )
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")


def test_exact8_registry_names_adapters_and_handler_identity() -> None:
    assert runtime.KNOWN_RULE_IDS == tuple(
        f"ADMIT_{index:03d}" for index in range(1, 16)
    )
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == runtime.KNOWN_RULE_IDS[:8]
    assert runtime.ADAPTER_READY_RULE_IDS == runtime.KNOWN_RULE_IDS[:8]
    assert type(runtime.RULE_NAMES) is MappingProxyType
    assert type(runtime.ADAPTER_IDS) is MappingProxyType
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == runtime.KNOWN_RULE_IDS[:8]
    for rule_id in runtime.KNOWN_RULE_IDS[:7]:
        assert (
            runtime.EVALUATOR_REGISTRY[rule_id]
            is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        )
        assert runtime.RULE_NAMES[rule_id] == runtime.predecessor.RULE_NAMES[rule_id]
        assert runtime.ADAPTER_IDS[rule_id] == runtime.predecessor.ADAPTER_IDS[rule_id]
    assert (
        runtime.EVALUATOR_REGISTRY["ADMIT_008"]
        is runtime._evaluate_registered_admit_008
    )
    assert runtime.RULE_NAMES["ADMIT_008"] == "topology_restoration_disposition"
    assert runtime.ADAPTER_IDS["ADMIT_008"] == (
        "covapie_admit_008_unified_adapter_v1"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "mutable",
        "order",
        "wrapper",
        "missing008",
        "register009",
        "wrong008",
    ),
)
def test_registry_mutations_fail_runtime_state(
    monkeypatch: pytest.MonkeyPatch,
    snapshot: runtime.FrozenSourceSnapshot,
    mutation: str,
) -> None:
    values = dict(runtime.EVALUATOR_REGISTRY)
    if mutation == "mutable":
        replacement: object = values
    elif mutation == "order":
        replacement = MappingProxyType(
            {key: values[key] for key in ("ADMIT_002", "ADMIT_001", *runtime.KNOWN_RULE_IDS[2:8])}
        )
    elif mutation == "wrapper":
        original = values["ADMIT_001"]
        values["ADMIT_001"] = lambda *args, **kwargs: original(*args, **kwargs)
        replacement = MappingProxyType(values)
    elif mutation == "missing008":
        values.pop("ADMIT_008")
        replacement = MappingProxyType(values)
    elif mutation == "register009":
        values["ADMIT_009"] = runtime._evaluate_registered_admit_008
        replacement = MappingProxyType(values)
    else:
        values["ADMIT_008"] = values["ADMIT_007"]
        replacement = MappingProxyType(values)
    monkeypatch.setattr(runtime, "EVALUATOR_REGISTRY", replacement)
    assert runtime.build_runtime_state(snapshot)["all_checks_passed"] is False


def test_exact13_fields_and_public_signature_drift_fail_state(
    monkeypatch: pytest.MonkeyPatch,
    snapshot: runtime.FrozenSourceSnapshot,
) -> None:
    monkeypatch.setattr(runtime, "RESULT_FIELDS", (*runtime.RESULT_FIELDS[:-1], "drift"))
    assert runtime.build_runtime_state(snapshot)["all_checks_passed"] is False
    monkeypatch.undo()
    monkeypatch.setattr(runtime, "evaluate_admission_rule", lambda rule, candidate: None)
    assert runtime.build_runtime_state(snapshot)["all_checks_passed"] is False


@pytest.mark.parametrize(
    ("rule_id", "code", "reported", "flags"),
    (
        (8, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", (False, False, False)),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", (False, False, False)),
        ("ADMIT_009", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "ADMIT_009", (True, False, False)),
    ),
)
def test_global_dispatch_precedence_and_flags(
    rule_id: object,
    code: str,
    reported: str,
    flags: tuple[bool, bool, bool],
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})  # type: ignore[arg-type]
    assert _values(caught.value, runtime.DISPATCH_ERROR_FIELDS) == (
        code,
        reported,
        *flags,
        code,
    )


def test_rule_id_str_subclass_precedes_known_and_registered() -> None:
    class Text(str):
        pass

    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            Text("ADMIT_008"), [], batch_context={}, evaluation_context=[]
        )
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"


@pytest.mark.parametrize("rule_id", runtime.KNOWN_RULE_IDS[8:])
def test_admit009_to_015_are_known_not_registered(rule_id: str) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})
    assert (
        caught.value.known_rule,
        caught.value.callable_discovered,
        caught.value.adapter_ready,
    ) == (True, False, False)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    (
        ({"batch_context": {}}, "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": []}, "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED"),
        ({"evaluation_context": _context(), "download_result_context": {}}, "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": _context(), "stage_authorization_context": {}}, "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ({"batch_context": {}, "evaluation_context": [], "download_result_context": {}, "stage_authorization_context": {}}, "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_context_precedence_no_candidate_formal_or_oracle_access(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
    reason: str,
) -> None:
    class Bomb(Mapping[str, object]):
        accesses = 0

        def __getitem__(self, key: str) -> object:
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __iter__(self):
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __len__(self) -> int:
            self.accesses += 1
            raise AssertionError("candidate accessed")

    bomb = Bomb()
    monkeypatch.setattr(
        runtime.admit008,
        "evaluate_admit_008",
        lambda *args: pytest.fail("formal called"),
    )
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda *args: pytest.fail("oracle called"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_008", bomb, **kwargs)
    assert _values(caught.value, runtime.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_008",
        True,
        True,
        True,
        reason,
    )
    assert bomb.accesses == 0


def test_context_required_lookup_precedes_download_and_candidate() -> None:
    evaluation = _SingleLookupMapping(
        runtime.ADMIT_008_CONTEXT_ITEMS[0],
        runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )
    candidate = _SingleLookupMapping(
        runtime.ADMIT_008_CANDIDATE_FIELDS[0], object()
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_008",
            candidate,
            evaluation_context=evaluation,
            download_result_context={},
        )
    assert caught.value.reason == "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
    assert evaluation.lookup_count == 1
    assert candidate.lookup_count == 0


def test_mapping_subclasses_single_lookup_identity_no_copy_or_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scalar = object()
    context_value = object()
    candidate = _SingleLookupMapping(runtime.ADMIT_008_CANDIDATE_FIELDS[0], scalar)
    evaluation = _SingleLookupMapping(runtime.ADMIT_008_CONTEXT_ITEMS[0], context_value)
    source = _valid_source()
    oracle = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
        runtime.admit008.CANONICAL_ENUM_MEMBERS[0],
        runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )
    calls: dict[str, list[tuple[object, object]]] = {"formal": [], "oracle": []}
    monkeypatch.setattr(
        runtime.admit008,
        "evaluate_admit_008",
        lambda left, right: calls["formal"].append((left, right)) or source,
    )
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda left, right: calls["oracle"].append((left, right)) or oracle,
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_008", candidate, evaluation_context=evaluation
    )
    assert result.outcome == "passed"
    assert candidate.lookup_count == evaluation.lookup_count == 1
    assert calls == {
        "formal": [(scalar, context_value)],
        "oracle": [(scalar, context_value)],
    }


def test_provider_and_unrelated_candidate_fields_are_never_accessed() -> None:
    class ProviderBomb(Mapping[str, object]):
        def __getitem__(self, key: str) -> object:
            if key == runtime.ADMIT_008_CANDIDATE_FIELDS[0]:
                return runtime.admit008.CANONICAL_ENUM_MEMBERS[0]
            raise AssertionError(f"provider field accessed: {key}")

        def __iter__(self):
            raise AssertionError("candidate iterated")

        def __len__(self) -> int:
            raise AssertionError("candidate sized")

    result = runtime.evaluate_admission_rule(
        "ADMIT_008", ProviderBomb(), evaluation_context=_context()
    )
    assert result.outcome == "passed"


@pytest.mark.parametrize(
    ("candidate", "reason"),
    (
        ([], "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "topology_restoration_disposition_missing"),
    ),
)
def test_candidate_envelope_failures_are_exact13_with_zero_calls(
    monkeypatch: pytest.MonkeyPatch,
    candidate: object,
    reason: str,
) -> None:
    monkeypatch.setattr(
        runtime.admit008,
        "evaluate_admit_008",
        lambda *args: pytest.fail("formal called"),
    )
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda *args: pytest.fail("oracle called"),
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_008", candidate, evaluation_context=_context()  # type: ignore[arg-type]
    )
    assert _values(result, runtime.RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_008",
        "topology_restoration_disposition",
        "invalid",
        False,
        True,
        reason,
        (),
        (),
        runtime.ADMIT_008_CANDIDATE_FIELDS,
        runtime.ADMIT_008_CONTEXT_ITEMS,
        False,
        "covapie_admit_008_unified_adapter_v1",
    )


class _EmptyStringSubclass(str):
    pass


@pytest.mark.parametrize(
    ("value", "outcome", "reason"),
    (
        (None, "invalid", runtime.admit008.SCALAR_REASONS[0]),
        ("", "invalid", runtime.admit008.SCALAR_REASONS[1]),
        (_EmptyStringSubclass(""), "invalid", runtime.admit008.SCALAR_REASONS[0]),
        (" ", "invalid", runtime.admit008.SCALAR_REASONS[3]),
        (7, "invalid", runtime.admit008.SCALAR_REASONS[0]),
        ("unknown", "invalid", runtime.admit008.SCALAR_REASONS[4]),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[0], "passed", ""),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[1], "passed", ""),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[2], "blocked", runtime.admit008.BLOCKED_REASONS[runtime.admit008.CANONICAL_ENUM_MEMBERS[2]]),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[3], "blocked", runtime.admit008.BLOCKED_REASONS[runtime.admit008.CANONICAL_ENUM_MEMBERS[3]]),
    ),
)
def test_all_key_present_values_reach_formal_and_oracle_once_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    value: object,
    outcome: str,
    reason: str,
) -> None:
    calls = Counter()
    formal = runtime.admit008.evaluate_admit_008
    oracle = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design

    def formal_wrapper(left: object, right: object) -> object:
        assert left is value
        calls.update(["formal"])
        return formal(left, right)

    def oracle_wrapper(left: object, right: object) -> object:
        assert left is value
        calls.update(["oracle"])
        return oracle(left, right)

    monkeypatch.setattr(runtime.admit008, "evaluate_admit_008", formal_wrapper)
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        oracle_wrapper,
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_008", _candidate(value), evaluation_context=_context()
    )
    assert (result.outcome, result.reason) == (outcome, reason)
    assert calls == {"formal": 1, "oracle": 1}


@pytest.mark.parametrize(
    ("scalar", "context_value", "outcome", "reason", "validated"),
    (
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[0], runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "passed", "", ((runtime.ADMIT_008_CANDIDATE_FIELDS[0], runtime.admit008.CANONICAL_ENUM_MEMBERS[0]),)),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[1], runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "passed", "", ((runtime.ADMIT_008_CANDIDATE_FIELDS[0], runtime.admit008.CANONICAL_ENUM_MEMBERS[1]),)),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[2], runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "blocked", runtime.admit008.BLOCKED_REASONS[runtime.admit008.CANONICAL_ENUM_MEMBERS[2]], ((runtime.ADMIT_008_CANDIDATE_FIELDS[0], runtime.admit008.CANONICAL_ENUM_MEMBERS[2]),)),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[3], runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "blocked", runtime.admit008.BLOCKED_REASONS[runtime.admit008.CANONICAL_ENUM_MEMBERS[3]], ((runtime.ADMIT_008_CANDIDATE_FIELDS[0], runtime.admit008.CANONICAL_ENUM_MEMBERS[3]),)),
        ("unknown", runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS, "invalid", runtime.admit008.SCALAR_REASONS[4], ()),
        (runtime.admit008.CANONICAL_ENUM_MEMBERS[0], None, "invalid", runtime.admit008.CONTEXT_REASONS[0], ((runtime.ADMIT_008_CANDIDATE_FIELDS[0], runtime.admit008.CANONICAL_ENUM_MEMBERS[0]),)),
    ),
)
def test_exact13_projection_passed_blocked_scalar_and_context_invalid(
    scalar: object,
    context_value: object,
    outcome: str,
    reason: str,
    validated: tuple[tuple[str, str], ...],
) -> None:
    result = runtime.evaluate_admission_rule(
        "ADMIT_008", _candidate(scalar), evaluation_context=_context(context_value)
    )
    assert result.outcome == outcome
    assert result.passed is (outcome == "passed")
    assert result.blocks_candidate is (outcome != "passed")
    assert result.reason == reason
    assert result.normalized_values == result.validated_candidate_fields == validated
    assert result.consumed_candidate_fields == runtime.ADMIT_008_CANDIDATE_FIELDS
    assert result.consumed_context_items == runtime.ADMIT_008_CONTEXT_ITEMS
    assert result.evaluator_io_used is False


def _source_subclass(valid: runtime.admit008.Admit008EvaluationResult) -> object:
    class Subclass(runtime.admit008.Admit008EvaluationResult):
        pass

    value = object.__new__(Subclass)
    for name in runtime.admit008.RESULT_FIELDS:
        object.__setattr__(value, name, getattr(valid, name))
    return value


def _source_order_drift(
    valid: runtime.admit008.Admit008EvaluationResult,
) -> runtime.admit008.Admit008EvaluationResult:
    name = runtime.admit008.RESULT_FIELDS[0]
    value = getattr(valid, name)
    object.__delattr__(valid, name)
    object.__setattr__(valid, name, value)
    return valid


@pytest.mark.parametrize(
    ("factory", "reason"),
    (
        (lambda valid: object(), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (_source_subclass, "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (_source_order_drift, "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "admission_rule_id", "ADMIT_007"), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "outcome", "invalid"), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "passed", False), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "blocks_candidate", True), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "reason", runtime.admit008.SCALAR_REASONS[4]), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "canonical_topology_restoration_disposition", runtime.admit008.CANONICAL_ENUM_MEMBERS[1]), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "validated_candidate_fields", ()), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "consumed_candidate_fields", ()), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "consumed_context_items", ()), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "evaluator_io_used", True), "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
    ),
)
def test_source_full_exact10_prevalidation_precedes_oracle_and_projection(
    monkeypatch: pytest.MonkeyPatch,
    factory: Any,
    reason: str,
) -> None:
    source = factory(_valid_source())
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit008,
        "evaluate_admit_008",
        lambda *args: counts.update(["formal"]) or source,
    )
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda *args: counts.update(["oracle"]) or pytest.fail("oracle called"),
    )
    monkeypatch.setattr(
        runtime,
        "_project_admit008_exact13",
        lambda *args: pytest.fail("projected"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_008",
            _candidate(runtime.admit008.CANONICAL_ENUM_MEMBERS[0]),
            evaluation_context=_context(),
        )
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert caught.value.adapter_ready is False
    assert caught.value.reason == reason
    assert counts == {"formal": 1}


def test_dataclass_field_order_guard_precedes_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts = Counter()
    monkeypatch.setattr(runtime, "fields", lambda value: ())
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_008",
            _candidate(runtime.admit008.CANONICAL_ENUM_MEMBERS[0]),
            evaluation_context=_context(),
        )
    assert caught.value.reason == "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert counts == Counter()


def test_oracle_mismatch_and_malformed_structure_never_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = _valid_source()
    mismatch = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
        runtime.admit008.CANONICAL_ENUM_MEMBERS[1],
        runtime.admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit008,
        "evaluate_admit_008",
        lambda *args: counts.update(["formal"]) or valid,
    )
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda *args: counts.update(["oracle"]) or mismatch,
    )
    monkeypatch.setattr(
        runtime,
        "_project_admit008_exact13",
        lambda *args: pytest.fail("projected"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_008",
            _candidate(runtime.admit008.CANONICAL_ENUM_MEMBERS[0]),
            evaluation_context=_context(),
        )
    assert caught.value.reason == "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert counts == {"formal": 1, "oracle": 1}

    malformed = SimpleNamespace(admit_008=SimpleNamespace(outcome="passed"))
    monkeypatch.setattr(
        runtime.admit008_oracle,
        "classify_admit_008_topology_restoration_disposition_design",
        lambda *args: malformed,
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as malformed_error:
        runtime.evaluate_admission_rule(
            "ADMIT_008",
            _candidate(runtime.admit008.CANONICAL_ENUM_MEMBERS[0]),
            evaluation_context=_context(),
        )
    assert malformed_error.value.reason == (
        "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )


def test_exact38_complete_standalone_oracle_and_runtime_equivalence() -> None:
    checker = _load_checker()
    assert len(checker._exact38_definitions()) == 38
    for _, _, scalar, context_value in checker._exact38_definitions():
        source = runtime.admit008.evaluate_admit_008(scalar, context_value)
        classification = runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
            scalar, context_value
        )
        outcome = classification.admit_008
        expected = runtime.admit008.Admit008EvaluationResult(
            "ADMIT_008",
            outcome.outcome,
            outcome.passed,
            outcome.blocks_candidate,
            outcome.reason,
            outcome.canonical_value,
            outcome.validated_candidate_fields,
            runtime.ADMIT_008_CANDIDATE_FIELDS,
            runtime.ADMIT_008_CONTEXT_ITEMS,
            False,
        )
        observed = runtime.evaluate_admission_rule(
            "ADMIT_008", _candidate(scalar), evaluation_context=_context(context_value)
        )
        assert source == expected
        assert observed.outcome == source.outcome
        assert observed.reason == source.reason
        assert observed.normalized_values == source.validated_candidate_fields


def test_predecessor_exact7_truth_and_handler_identity_cover_all_rows(
    state: dict[str, Any],
) -> None:
    groups = state["truth_group_counts"]
    assert groups["predecessor_exact7_truth"] == 107
    assert groups["predecessor_handler_identity"] == 7
    assert all(
        runtime.EVALUATOR_REGISTRY[rule_id]
        is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in runtime.KNOWN_RULE_IDS[:7]
    )


def test_state_counts_groups_contract_registry_and_safety(
    state: dict[str, Any],
) -> None:
    assert len(state["contract_rows"]) == len(runtime._contract_definitions()) == 77
    assert len(state["truth_rows"]) == 203
    assert state["truth_group_counts"] == {
        "global_dispatch": 5,
        "predecessor_handler_identity": 7,
        "predecessor_exact7_truth": 107,
        "admit008_exact38": 38,
        "admit008_context_routing": 7,
        "admit008_candidate_envelope": 16,
        "admit008_source_oracle": 5,
        "admit008_projection": 6,
        "registry_issue_boundary": 12,
    }
    assert len(state["registry_rows"]) == 15
    assert len(state["safety_rows"]) == 41
    assert all(row["case_passed"] == "true" for row in state["truth_rows"])


def test_issue_inventory_only_coverage_row_transitions(
    state: dict[str, Any],
) -> None:
    old = list(state["predecessor"]["design_issue_rows"])
    new = state["issue_rows"]
    assert len(old) == len(new) == 11
    for before, after in zip(old, new, strict=True):
        if before["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE":
            assert after["affected_rules"] == "|".join(runtime.KNOWN_RULE_IDS[8:])
            assert after["integration_transition"] == (
                "admit_008_implemented_and_removed_from_open_coverage_scope"
            )
            changed = {key for key in after if after[key] != before[key]}
            assert changed == {"affected_rules", "integration_transition"}
        else:
            assert after == before
    issue_map = {row["issue_id"]: row for row in new}
    assert issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved"
    assert issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["integration_transition"] == (
        "topology_restoration_disposition_enum_contract_frozen_v1"
    )
    assert issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"] == "resolved"
    for issue_id in (
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
        "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
        "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
        "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
        "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ):
        assert issue_map[issue_id]["status"] == "open"


def test_manifest_exact_readiness_provider_and_stop_boundaries(
    state: dict[str, Any],
) -> None:
    _, manifest = runtime._payloads(state)
    checker = _load_checker()
    assert manifest == checker._expected_manifest()
    assert len(manifest) == 137
    assert len(manifest["readiness"]) == 38
    for key, value in manifest["readiness"].items():
        assert manifest[key] is value
    assert manifest["provider_fields_consumed"] == []
    assert manifest["real_provider_value_count"] == 0
    assert manifest["real_provider_mapping_executed"] is False
    assert manifest["adapter_design_gate_imported_by_runtime"] is False
    assert manifest["exact7_runtime_modified"] is False
    assert manifest["admit_009_started"] is False
    assert manifest["evaluate_all_rules_implemented"] is False
    assert manifest["combined_candidate_verdict_implemented"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert runtime.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_default_outputs_match_generated_payloads_and_six_frozen_sha(
    state: dict[str, Any],
) -> None:
    payloads, _ = runtime._payloads(state)
    checker = _load_checker()
    assert {path.name for path in OUTPUT_ROOT.iterdir()} == set(runtime.OUTPUT_FILES)
    for name in runtime.OUTPUT_FILES:
        assert (OUTPUT_ROOT / name).read_bytes() == payloads[name]
        assert hashlib.sha256(payloads[name]).hexdigest() == (
            checker.EXPECTED_OUTPUT_SHA256[name]
        )


def test_deterministic_double_materialization_and_no_temp_or_part(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1(first)
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1(second)
    assert {
        name: (first / name).read_bytes() for name in runtime.OUTPUT_FILES
    } == {
        name: (second / name).read_bytes() for name in runtime.OUTPUT_FILES
    }
    assert not tuple(first.glob("*.tmp"))
    assert not tuple(first.glob("*.part"))


@pytest.mark.parametrize("mode", ("unexpected", "directory", "symlink", "root_symlink"))
def test_materializer_rejects_unsafe_outputs(tmp_path: Path, mode: str) -> None:
    root = tmp_path / "outputs"
    if mode == "root_symlink":
        real = tmp_path / "real"
        real.mkdir()
        root.symlink_to(real, target_is_directory=True)
    else:
        root.mkdir()
        if mode == "unexpected":
            (root / "unexpected.txt").write_text("x", encoding="utf-8")
        elif mode == "directory":
            (root / runtime.CONTRACT_FILENAME).mkdir()
        else:
            outside = tmp_path / "outside"
            outside.write_text("unchanged", encoding="utf-8")
            (root / runtime.CONTRACT_FILENAME).symlink_to(outside)
    with pytest.raises(ValueError):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1(root)


def _rewrite_csv(path: Path, mutator: Any) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        header, rows = tuple(reader.fieldnames), list(reader)
    mutator(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _refresh_manifest_hash(root: Path, filename: str) -> None:
    path = root / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256(
        (root / filename).read_bytes()
    ).hexdigest()
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


@pytest.mark.parametrize(
    ("filename", "mutator"),
    (
        (runtime.CONTRACT_FILENAME, lambda rows: rows[0].__setitem__("observed_value", "false")),
        (runtime.TRUTH_FILENAME, lambda rows: rows[0].__setitem__("observed_result_or_error", "passed")),
        (runtime.REGISTRY_FILENAME, lambda rows: rows[7].__setitem__("registered", "false")),
        (runtime.SAFETY_FILENAME, lambda rows: rows[0].__setitem__("observed_executed", "false")),
        (runtime.ISSUE_FILENAME, lambda rows: next(row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE").__setitem__("affected_rules", "ADMIT_010|ADMIT_011")),
    ),
)
def test_checker_rejects_semantic_tamper_after_manifest_hash_refresh(
    tmp_path: Path, filename: str, mutator: Any
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    _rewrite_csv(candidate / filename, mutator)
    _refresh_manifest_hash(candidate, filename)
    with pytest.raises(AssertionError):
        _load_checker()._validate_output_root(
            candidate, enforce_frozen_hashes=False
        )


@pytest.mark.parametrize("mode", ("missing", "extra", "symlink"))
def test_checker_rejects_missing_extra_and_symlink_outputs(
    tmp_path: Path, mode: str
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    if mode == "missing":
        (candidate / runtime.CONTRACT_FILENAME).unlink()
    elif mode == "extra":
        (candidate / "unexpected.txt").write_text("x", encoding="utf-8")
    else:
        path = candidate / runtime.CONTRACT_FILENAME
        path.unlink()
        path.symlink_to(OUTPUT_ROOT / runtime.CONTRACT_FILENAME)
    with pytest.raises(AssertionError):
        _load_checker()._validate_output_root(candidate)


@pytest.mark.parametrize(
    ("mode", "message"),
    (
        ("nested_readiness", "semantic mismatch"),
        ("top_readiness", "semantic mismatch"),
        ("unknown_key", "key set mismatch"),
        ("provider_overclaim", "semantic mismatch"),
        ("registered009", "semantic mismatch"),
        ("source_paths", "semantic mismatch"),
    ),
)
def test_checker_rejects_manifest_drift_without_frozen_hashes(
    tmp_path: Path, mode: str, message: str
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    path = candidate / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mode == "nested_readiness":
        manifest["readiness"]["ready_for_training"] = True
    elif mode == "top_readiness":
        manifest["ready_for_training"] = True
    elif mode == "unknown_key":
        manifest["unknown_contract_key"] = False
    elif mode == "provider_overclaim":
        manifest["real_provider_mapping_executed"] = True
    elif mode == "registered009":
        manifest["registered_rule_ids"].append("ADMIT_009")
    else:
        manifest["source_input_paths"] = manifest["source_input_paths"][:-1]
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(AssertionError, match=message):
        _load_checker()._validate_output_root(
            candidate, enforce_frozen_hashes=False
        )


@pytest.mark.parametrize(
    "reference",
    (
        "runtime._truth_rows(())",
        "runtime.EVALUATOR_REGISTRY",
        "runtime.admit008.evaluate_admit_008(x, y)",
        "runtime.admit008_oracle.classify_admit_008_topology_restoration_disposition_design(x, y)",
        "runtime.SOURCE_PATHS",
        "runtime.SOURCE_SHA256",
        "runtime.TRUE_READINESS",
        "runtime._manifest_payload({}, {})",
    ),
)
def test_checker_ast_guard_rejects_production_dependencies(reference: str) -> None:
    checker = _load_checker()
    injected = f"def _expected_truth_rows():\n    return {reference}\n"
    with pytest.raises(AssertionError, match="depends on production"):
        checker._assert_checker_independent_ast(injected)


def test_checker_full_manifest_and_builder_inventory() -> None:
    checker = _load_checker()
    checker._assert_checker_independent_ast()
    manifest = checker._expected_manifest()
    assert len(manifest) == 137
    assert len(manifest["readiness"]) == 38
    assert manifest == json.loads(
        (OUTPUT_ROOT / runtime.MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    assert len(checker._expected_contract_rows()) == 77
    assert len(checker._expected_truth_rows()) == 203
    assert len(checker._expected_registry_rows()) == 15
    assert len(checker._expected_safety_rows()) == 41
    assert len(checker._expected_issue_rows()) == 11


def test_runtime_public_call_graph_and_import_boundary() -> None:
    checker = _load_checker()
    checker._check_public_call_graph()
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    import_section = source.split("PROJECT =", 1)[0]
    assert "admit_008_unified_adapter_contract_design_gate" not in import_section
    assert "torch" not in import_section
    assert "numpy" not in import_section
    assert "rdkit" not in import_section


@pytest.mark.parametrize("target", ("runtime", "checker"))
def test_imports_are_silent_and_side_effect_free(
    tmp_path: Path, target: str
) -> None:
    if target == "runtime":
        command = (
            "import covalent_ext."
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008"
        )
    else:
        command = (
            "import importlib.util;"
            f"s=importlib.util.spec_from_file_location('checker',{str(CHECKER_PATH)!r});"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
        )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()


def test_checker_runs_cleanly_twice_with_identical_stdout() -> None:
    command = [sys.executable, str(CHECKER_PATH)]
    first = subprocess.run(
        command, cwd=REPO_ROOT, capture_output=True, check=False
    )
    second = subprocess.run(
        command, cwd=REPO_ROOT, capture_output=True, check=False
    )
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"exact18_source_sha=18/18" in first.stdout
    assert b"registered_rule_count=8" in first.stdout
    assert b"contract_rows=77" in first.stdout
    assert b"truth_rows=203" in first.stdout


def test_required_exact50_negative_contract_inventory_is_explicit() -> None:
    cases = (
        "public_result_type_identity", "public_error_type_identity",
        "exact13_field_drift", "public_api_signature_drift", "registry_mutable",
        "registry_order", "predecessor_wrapper", "admit008_missing",
        "admit009_registered", "known_unknown_precedence", "context_precedence",
        "context_failure_candidate_access", "evaluation_nonmapping",
        "evaluation_key_absent", "context_multiple_lookup", "context_copy",
        "candidate_nonmapping_to_standalone", "candidate_absent_to_standalone",
        "none_folded_missing", "empty_folded_missing", "empty_subclass_missing",
        "scalar_normalized", "scalar_multiple_lookup", "formal_call_count",
        "source_subclass", "source_storage_order", "source_invariant",
        "source_failure_oracle_call", "oracle_call_count", "oracle_identity",
        "partial_exact10", "oracle_mismatch_projection", "normalized_projection",
        "blocked_changed", "blocked_reasons_swapped", "context_pair_cleared",
        "scalar_pair_fabricated", "provider_fields_read", "provider_overclaim",
        "old_runtime_issue_authority", "coverage_admit008_not_removed",
        "coverage_admit009_removed", "noncoverage_issue_changed",
        "source_sha_symlink_descendant", "raw_checkpoint_source",
        "output_missing_extra_symlink", "semantic_tamper_refreshed_hash",
        "readiness_mirror", "unknown_manifest_key", "import_side_effect",
    )
    assert len(cases) == len(set(cases)) == 50
    evidence = json.dumps(
        {
            "contract": runtime._contract_rows(),
            "truth_groups": runtime.build_runtime_state()["truth_group_counts"],
            "safety": runtime._safety_rows(),
            "readiness": {
                **{key: True for key in runtime.TRUE_READINESS},
                **{key: False for key in runtime.FALSE_READINESS},
            },
        },
        sort_keys=True,
    )
    for anchor in (
        "required_key_absent",
        "original_identity_single_lookup_no_prevalidation",
        "all_fields_before_oracle",
        "complete Exact10 equality",
        "two blocked passthrough",
        "provider fields consumed",
        "admit_008_implemented_and_removed_from_open_coverage_scope",
        "feature_semantics_audit_required_before_training",
    ):
        assert anchor in evidence
