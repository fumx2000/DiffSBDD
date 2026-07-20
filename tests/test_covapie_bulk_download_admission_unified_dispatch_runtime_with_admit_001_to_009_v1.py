from __future__ import annotations

import ast
import csv
import dataclasses
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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009
    as runtime,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1.py"
)
OUTPUT_ROOT = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
SUMMARY_PATH = (
    REPO_ROOT
    / "docs/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1_summary.md"
)
KEY = "covapie_dup_v1_sha256_" + "1" * 64
OTHER = "covapie_dup_v1_sha256_" + "f" * 64
POLICY = "covapie_duplicate_identity_key_contract_v1"


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location("exact9_checker_for_test", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def snapshot() -> runtime.FrozenSourceSnapshot:
    return runtime.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def state(snapshot: runtime.FrozenSourceSnapshot) -> dict[str, Any]:
    value = runtime.build_runtime_state(snapshot)
    assert value["all_checks_passed"] is True
    assert value["validation_failures"] == []
    return value


def _kwargs(batch: object = (), policy: object = POLICY) -> dict[str, object]:
    return {
        "batch_context": {"batch_duplicate_identity_keys": batch},
        "evaluation_context": {"duplicate_identity_key_contract": policy},
    }


def _candidate(value: object = KEY) -> dict[str, object]:
    return {"duplicate_identity_key": value}


def _values(value: object, names: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in names)


def _valid_source(
    scalar: object = KEY, batch: object = (), policy: object = POLICY
) -> runtime.admit009.Admit009EvaluationResult:
    return runtime.admit009.evaluate_admit_009(scalar, batch, policy)


def _mutate(value: object, name: str, replacement: object) -> object:
    object.__setattr__(value, name, replacement)
    return value


class _SingleLookupMapping(Mapping[str, object]):
    def __init__(
        self,
        key: str,
        value: object,
        *,
        present: bool = True,
        failure: Exception | None = None,
    ) -> None:
        self.key = key
        self.value = value
        self.present = present
        self.failure = failure
        self.lookup_count = 0

    def __getitem__(self, key: str) -> object:
        if key != self.key:
            raise KeyError(key)
        self.lookup_count += 1
        if self.lookup_count > 1:
            raise AssertionError("required key read twice")
        if self.failure is not None:
            raise self.failure
        if not self.present:
            raise KeyError(key)
        return self.value

    def __iter__(self):
        raise AssertionError("Mapping iterated or copied")

    def __len__(self) -> int:
        raise AssertionError("Mapping sized or copied")


class _CandidateBomb(Mapping[str, object]):
    accesses = 0

    def __getitem__(self, key: str) -> object:
        self.accesses += 1
        raise AssertionError("candidate accessed")

    def __iter__(self):
        self.accesses += 1
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        self.accesses += 1
        raise AssertionError("candidate sized")


class _StringSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


def _assert_dispatch_error(
    caught: pytest.ExceptionInfo[runtime.UnifiedAdmissionDispatchError],
    code: str,
    reason: str,
    flags: tuple[bool, bool, bool],
) -> None:
    error = caught.value
    assert error.code == code
    assert error.reason == reason
    assert (error.known_rule, error.callable_discovered, error.adapter_ready) == flags


def test_exact18_order_structure_sha_and_lineage(
    snapshot: runtime.FrozenSourceSnapshot, checker: Any
) -> None:
    assert runtime.EXPECTED_BASE_COMMIT == "a0e5d56cc0afd8d2677aa53bd629fb33948ffaf3"
    assert runtime.EXPECTED_BASE_SUBJECT == "add CovaPIE ADMIT_009 unified adapter contract design v1"
    assert len(runtime.SOURCE_PATHS) == len(set(runtime.SOURCE_PATHS)) == 18
    assert tuple(runtime.SOURCE_SHA256) == runtime.SOURCE_PATHS
    assert runtime.SOURCE_PATHS == tuple(Path(path) for path, _ in checker.SOURCE_BOUNDARY)
    assert runtime.SOURCE_SHA256 == {
        Path(path): digest for path, digest in checker.SOURCE_BOUNDARY
    }
    assert runtime.validate_frozen_source_snapshot(snapshot)
    for record in snapshot.records:
        assert record.expected_sha256 == record.base_tree_sha256
        assert record.expected_sha256 == record.filesystem_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256
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
    assert runtime.validate_frozen_source_snapshot(runtime.build_frozen_source_snapshot())


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


def test_public_type_constant_dispatcher_and_signature_identity() -> None:
    predecessor = runtime.predecessor
    assert runtime.UnifiedAdmissionRuleEvaluation is predecessor.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is predecessor.UnifiedAdmissionDispatchError
    for name in (
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        assert getattr(runtime, name) is getattr(predecessor, name)
    assert runtime.evaluate_admission_rule is not predecessor.evaluate_admission_rule
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        predecessor.evaluate_admission_rule
    )
    assert runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is runtime.EVALUATOR_REGISTRY
    assert runtime.EVALUATOR_REGISTRY is not predecessor.EVALUATOR_REGISTRY
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")


def test_exact9_registry_names_adapters_and_handler_identity() -> None:
    assert runtime.KNOWN_RULE_IDS == tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == runtime.KNOWN_RULE_IDS[:9]
    assert runtime.ADAPTER_READY_RULE_IDS == runtime.KNOWN_RULE_IDS[:9]
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert type(runtime.RULE_NAMES) is MappingProxyType
    assert type(runtime.ADAPTER_IDS) is MappingProxyType
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == runtime.KNOWN_RULE_IDS[:9]
    for rule_id in runtime.KNOWN_RULE_IDS[:8]:
        assert runtime.EVALUATOR_REGISTRY[rule_id] is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        assert runtime.RULE_NAMES[rule_id] == runtime.predecessor.RULE_NAMES[rule_id]
        assert runtime.ADAPTER_IDS[rule_id] == runtime.predecessor.ADAPTER_IDS[rule_id]
    assert runtime.EVALUATOR_REGISTRY["ADMIT_009"] is runtime._evaluate_registered_admit_009
    assert runtime.RULE_NAMES["ADMIT_009"] == "duplicate_identity_precheck"
    assert runtime.ADAPTER_IDS["ADMIT_009"] == "covapie_admit_009_unified_adapter_v1"
    assert tuple(runtime.predecessor.EVALUATOR_REGISTRY) == runtime.KNOWN_RULE_IDS[:8]


@pytest.mark.parametrize(
    "mutation",
    (
        "mutable", "order", "wrapper", "missing009", "register010", "wrong009",
        "predecessor_changed",
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
            {key: values[key] for key in ("ADMIT_002", "ADMIT_001", *runtime.KNOWN_RULE_IDS[2:9])}
        )
    elif mutation == "wrapper":
        original = values["ADMIT_001"]
        values["ADMIT_001"] = lambda *args, **kwargs: original(*args, **kwargs)
        replacement = MappingProxyType(values)
    elif mutation == "missing009":
        values.pop("ADMIT_009")
        replacement = MappingProxyType(values)
    elif mutation == "register010":
        values["ADMIT_010"] = runtime._evaluate_registered_admit_009
        replacement = MappingProxyType(values)
    elif mutation == "wrong009":
        values["ADMIT_009"] = values["ADMIT_008"]
        replacement = MappingProxyType(values)
    else:
        predecessor_values = dict(runtime.predecessor.EVALUATOR_REGISTRY)
        predecessor_values["ADMIT_009"] = runtime._evaluate_registered_admit_009
        monkeypatch.setattr(runtime.predecessor, "EVALUATOR_REGISTRY", MappingProxyType(predecessor_values))
        replacement = runtime.EVALUATOR_REGISTRY
    monkeypatch.setattr(runtime, "EVALUATOR_REGISTRY", replacement)
    assert runtime.build_runtime_state(snapshot)["all_checks_passed"] is False


@pytest.mark.parametrize("mutation", ("same_object", "signature", "foreign_globals"))
def test_dispatcher_object_signature_and_registry_binding_drift_fail_state(
    monkeypatch: pytest.MonkeyPatch,
    snapshot: runtime.FrozenSourceSnapshot,
    mutation: str,
) -> None:
    if mutation == "same_object":
        replacement = runtime.predecessor.evaluate_admission_rule
    elif mutation == "signature":
        replacement = lambda rule, candidate: None
    else:
        def replacement(*args: object, **kwargs: object) -> object:
            return runtime.predecessor.evaluate_admission_rule(*args, **kwargs)

        replacement.__signature__ = inspect.signature(runtime.predecessor.evaluate_admission_rule)  # type: ignore[attr-defined]
    monkeypatch.setattr(runtime, "evaluate_admission_rule", replacement)
    assert runtime.build_runtime_state(snapshot)["all_checks_passed"] is False


@pytest.mark.parametrize(
    "rule_id,code,flags",
    (
        (9, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", (False, False, False)),
        (_StringSubclass("ADMIT_009"), "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", (False, False, False)),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", (False, False, False)),
    ),
)
def test_global_rule_id_errors(
    rule_id: object, code: str, flags: tuple[bool, bool, bool]
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})
    _assert_dispatch_error(caught, code, code, flags)


@pytest.mark.parametrize("rule_id", runtime.KNOWN_RULE_IDS[9:])
def test_admit010_to_015_known_but_not_registered(rule_id: str) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        (True, False, False),
    )


def test_predecessor_dispatcher_and_registry_remain_exact8() -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.predecessor.evaluate_admission_rule("ADMIT_009", {})
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        (True, False, False),
    )
    assert tuple(runtime.predecessor.EVALUATOR_REGISTRY) == runtime.KNOWN_RULE_IDS[:8]


@pytest.mark.parametrize(
    "kwargs,reason",
    (
        ({"batch_context": None, "evaluation_context": {"duplicate_identity_key_contract": POLICY}}, "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
        ({"batch_context": {}, "evaluation_context": {"duplicate_identity_key_contract": POLICY}}, "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED"),
        ({"batch_context": {"batch_duplicate_identity_keys": ()}, "evaluation_context": None}, "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"batch_context": {"batch_duplicate_identity_keys": ()}, "evaluation_context": {}}, "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED"),
        ({**_kwargs(), "download_result_context": {}}, "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({**_kwargs(), "stage_authorization_context": {}}, "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_exact_context_routing_errors(
    kwargs: dict[str, object], reason: str
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **kwargs)
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        reason,
        (True, True, True),
    )


def test_context_precedence_candidate_inaccessible_and_no_adapter_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bomb = _CandidateBomb()
    monkeypatch.setattr(
        runtime.admit009,
        "evaluate_admit_009",
        lambda *args: pytest.fail("formal called"),
    )
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: pytest.fail("oracle called"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_009",
            bomb,
            batch_context=None,
            evaluation_context=None,
            download_result_context={},
            stage_authorization_context={},
        )
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED",
        (True, True, True),
    )
    assert bomb.accesses == 0


def test_mapping_subclasses_single_lookup_no_copy_and_original_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scalar = object()
    batch = object()
    policy = object()
    candidate = _SingleLookupMapping("duplicate_identity_key", scalar)
    batch_context = _SingleLookupMapping("batch_duplicate_identity_keys", batch)
    evaluation_context = _SingleLookupMapping("duplicate_identity_key_contract", policy)
    formal = runtime.admit009.evaluate_admit_009
    oracle = runtime.admit009_oracle.classify_admit_009_duplicate_identity_key_design
    calls: list[tuple[str, tuple[object, ...]]] = []

    def counted_formal(*args: object) -> object:
        calls.append(("formal", args))
        return formal(*args)

    def counted_oracle(*args: object) -> object:
        calls.append(("oracle", args))
        return oracle(*args)

    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", counted_formal)
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        counted_oracle,
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_009",
        candidate,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
    )
    assert result.reason == runtime.admit009.SCALAR_REASONS[0]
    assert (candidate.lookup_count, batch_context.lookup_count, evaluation_context.lookup_count) == (1, 1, 1)
    assert [name for name, _ in calls] == ["formal", "oracle"]
    for _, args in calls:
        assert args[0] is scalar
        assert args[1] is batch
        assert args[2] is policy


@pytest.mark.parametrize("position", ("batch", "policy", "candidate"))
def test_non_keyerror_mapping_exception_propagates_unchanged(position: str) -> None:
    failure = RuntimeError(f"{position} sentinel")
    candidate: object = _candidate()
    batch_context: object = {"batch_duplicate_identity_keys": ()}
    evaluation_context: object = {"duplicate_identity_key_contract": POLICY}
    if position == "batch":
        batch_context = _SingleLookupMapping("batch_duplicate_identity_keys", (), failure=failure)
    elif position == "policy":
        evaluation_context = _SingleLookupMapping("duplicate_identity_key_contract", POLICY, failure=failure)
    else:
        candidate = _SingleLookupMapping("duplicate_identity_key", KEY, failure=failure)
    with pytest.raises(RuntimeError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_009",
            candidate,
            batch_context=batch_context,
            evaluation_context=evaluation_context,
        )
    assert caught.value is failure


@pytest.mark.parametrize("position", ("batch", "policy"))
def test_only_absent_context_key_is_missing(
    position: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: pytest.fail("formal called"))
    mapping = _SingleLookupMapping(
        "batch_duplicate_identity_keys" if position == "batch" else "duplicate_identity_key_contract",
        object(),
        present=False,
    )
    kwargs = _kwargs()
    kwargs["batch_context" if position == "batch" else "evaluation_context"] = mapping
    reason = (
        "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED"
        if position == "batch"
        else "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED"
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **kwargs)
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        reason,
        (True, True, True),
    )
    assert mapping.lookup_count == 1


@pytest.mark.parametrize(
    "candidate,reason",
    (
        (None, "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "duplicate_identity_key_missing"),
    ),
)
def test_candidate_invalid_exact13_no_formal_oracle(
    candidate: object,
    reason: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: pytest.fail("formal called"))
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: pytest.fail("oracle called"),
    )
    result = runtime.evaluate_admission_rule("ADMIT_009", candidate, **_kwargs())
    assert result.outcome == "invalid"
    assert result.passed is False
    assert result.blocks_candidate is True
    assert result.reason == reason
    assert result.normalized_values == result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == ("duplicate_identity_key",)
    assert result.consumed_context_items == (
        "duplicate_identity_key_contract", "batch_duplicate_identity_keys",
    )
    assert result.evaluator_io_used is False
    assert result.adapter_id == "covapie_admit_009_unified_adapter_v1"


def test_candidate_missing_single_direct_lookup() -> None:
    candidate = _SingleLookupMapping("duplicate_identity_key", object(), present=False)
    result = runtime.evaluate_admission_rule("ADMIT_009", candidate, **_kwargs())
    assert result.reason == "duplicate_identity_key_missing"
    assert candidate.lookup_count == 1


@pytest.mark.parametrize(
    "scalar,batch,policy",
    (
        (None, (), POLICY),
        (7, (), POLICY),
        ("", (), POLICY),
        (_StringSubclass(KEY), (), POLICY),
        (" " + KEY, (), POLICY),
        ("bad", (), POLICY),
        (KEY, None, POLICY),
        (KEY, [], POLICY),
        (KEY, _TupleSubclass(), POLICY),
        (KEY, (), None),
        (KEY, (), ""),
        (KEY, (), _StringSubclass(POLICY)),
        (KEY, (OTHER,), POLICY),
        (KEY, (KEY,), POLICY),
    ),
)
def test_present_values_forwarded_without_adapter_normalization(
    scalar: object,
    batch: object,
    policy: object,
) -> None:
    expected = runtime.admit009.evaluate_admit_009(scalar, batch, policy)
    observed = runtime.evaluate_admission_rule(
        "ADMIT_009", _candidate(scalar), **_kwargs(batch, policy)
    )
    assert observed.outcome == expected.outcome
    assert observed.passed is expected.passed
    assert observed.blocks_candidate is expected.blocks_candidate
    assert observed.reason == expected.reason
    assert observed.normalized_values == expected.validated_candidate_fields
    assert observed.validated_candidate_fields == expected.validated_candidate_fields
    assert observed.consumed_candidate_fields == expected.consumed_candidate_fields
    assert observed.consumed_context_items == expected.consumed_context_items


def test_mutable_candidate_extra_fields_not_mutated_or_iterated() -> None:
    candidate = {"duplicate_identity_key": KEY, "unrelated": [1, 2]}
    before = {"duplicate_identity_key": KEY, "unrelated": [1, 2]}
    result = runtime.evaluate_admission_rule("ADMIT_009", candidate, **_kwargs())
    assert result.outcome == "passed"
    assert candidate == before


@pytest.mark.parametrize("kind", ("wrong_type", "subclass"))
def test_source_wrong_type_and_subclass_fail_before_oracle(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if kind == "wrong_type":
        source: object = object()
    else:
        subclass = type("ResultSubclass", (runtime.admit009.Admit009EvaluationResult,), {})
        source = object.__new__(subclass)
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit009,
        "evaluate_admit_009",
        lambda *args: counts.update(["formal"]) or source,
    )
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        (True, True, False),
    )
    assert counts == {"formal": 1}


def test_source_storage_order_drift_fails_before_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _valid_source()
    value = vars(source).pop("admission_rule_id")
    vars(source)["admission_rule_id"] = value
    counts = Counter()
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or source)
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        (True, True, False),
    )
    assert counts == {"formal": 1}


def test_dataclass_field_order_drift_fails_before_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _valid_source()
    committed = dataclasses.fields(runtime.admit009.Admit009EvaluationResult)
    counts = Counter()
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or source)
    monkeypatch.setattr(runtime, "fields", lambda cls: tuple(reversed(committed)))
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    assert caught.value.reason == "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert counts == {"formal": 1}


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("blocks_candidate", False),
        ("passed", True),
        ("evaluator_io_used", True),
        ("consumed_context_items", ()),
        ("validated_candidate_fields", ()),
    ),
)
def test_source_reconstruction_and_post_init_invariants_fail_closed(
    field: str,
    replacement: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scalar = KEY if field in {"consumed_context_items", "validated_candidate_fields"} else None
    source = _mutate(_valid_source(scalar), field, replacement)
    counts = Counter()
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or source)
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(scalar), **_kwargs())
    assert caught.value.reason == "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert caught.value.adapter_ready is False
    assert counts == {"formal": 1}


@pytest.mark.parametrize(
    "classification",
    (object(), {}, {"outcome": "passed"}),
)
def test_oracle_mapping_shape_or_key_failure_is_adapter_not_ready(
    classification: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _valid_source()
    counts = Counter()
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or source)
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: counts.update(["oracle"]) or classification,
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    _assert_dispatch_error(
        caught,
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        (True, True, False),
    )
    assert counts == {"formal": 1, "oracle": 1}


def test_oracle_uncaught_runtimeerror_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = RuntimeError("oracle sentinel")
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: (_ for _ in ()).throw(failure),
    )
    with pytest.raises(RuntimeError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    assert caught.value is failure


def test_full_exact10_mismatch_blocks_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formal_source = _valid_source(KEY, (), POLICY)
    oracle_mismatch = runtime.admit009_oracle.classify_admit_009_duplicate_identity_key_design(
        KEY, (KEY,), POLICY
    )
    counts = Counter()
    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: counts.update(["formal"]) or formal_source)
    monkeypatch.setattr(
        runtime.admit009_oracle,
        "classify_admit_009_duplicate_identity_key_design",
        lambda *args: counts.update(["oracle"]) or oracle_mismatch,
    )
    monkeypatch.setattr(runtime, "_project_admit009_exact13", lambda *args: pytest.fail("partial projection"))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    assert caught.value.reason == "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert caught.value.adapter_ready is False
    assert counts == {"formal": 1, "oracle": 1}


@pytest.mark.parametrize(
    "scalar,batch,policy,expected_outcome",
    (
        (KEY, (OTHER,), POLICY, "passed"),
        (KEY, (KEY,), POLICY, "blocked"),
        (None, (), POLICY, "invalid"),
        (KEY, (), None, "invalid"),
        (KEY, [], POLICY, "invalid"),
    ),
)
def test_exact10_to_exact13_projection_states(
    scalar: object, batch: object, policy: object, expected_outcome: str
) -> None:
    source = runtime.admit009.evaluate_admit_009(scalar, batch, policy)
    result = runtime.evaluate_admission_rule(
        "ADMIT_009", _candidate(scalar), **_kwargs(batch, policy)
    )
    assert result.schema_version is runtime.RESULT_SCHEMA_VERSION
    assert result.admission_rule_id == source.admission_rule_id
    assert result.admission_rule_name == "duplicate_identity_precheck"
    assert result.outcome == expected_outcome == source.outcome
    assert result.passed is source.passed
    assert result.blocks_candidate is source.blocks_candidate
    assert result.reason == source.reason
    assert result.normalized_values == source.validated_candidate_fields
    assert result.validated_candidate_fields == source.validated_candidate_fields
    assert result.consumed_candidate_fields == source.consumed_candidate_fields
    assert result.consumed_context_items == source.consumed_context_items
    assert result.evaluator_io_used is source.evaluator_io_used
    assert result.adapter_id == "covapie_admit_009_unified_adapter_v1"


def test_context_error_and_adapter_not_ready_flags_are_not_confused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as context:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), batch_context=None)
    assert context.value.code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    assert context.value.adapter_ready is True

    monkeypatch.setattr(runtime.admit009, "evaluate_admit_009", lambda *args: object())
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as adapter:
        runtime.evaluate_admission_rule("ADMIT_009", _candidate(), **_kwargs())
    assert adapter.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert adapter.value.adapter_ready is False


def test_runtime_state_natural_counts_and_issue_transition(
    state: dict[str, Any], checker: Any
) -> None:
    assert len(state["contract_rows"]) == 79
    assert len(state["truth_rows"]) == 289
    assert state["truth_group_counts"] == checker.TRUTH_GROUP_COUNTS
    assert len(state["registry_rows"]) == 15
    assert len(state["safety_rows"]) == 43
    assert len(state["issue_rows"]) == 11
    assert state["contract_rows"] == checker._expected_contract_rows()
    assert state["truth_rows"] == checker._expected_truth_rows()
    assert state["registry_rows"] == checker._expected_registry_rows()
    assert state["safety_rows"] == checker._expected_safety_rows()
    assert state["issue_rows"] == checker._expected_issue_rows()
    safety = {row["safety_item"]: row for row in state["safety_rows"]}
    assert "raw_read" not in safety
    assert safety["exact9_runtime_or_materializer_raw_read"] == {
        "safety_item": "exact9_runtime_or_materializer_raw_read",
        "expected_executed": "false",
        "observed_executed": "false",
        "safety_passed": "true",
    }
    assert safety["validation_incident_documented_and_contained"] == {
        "safety_item": "validation_incident_documented_and_contained",
        "expected_executed": "true",
        "observed_executed": "true",
        "safety_passed": "true",
    }
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    coverage = issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["affected_rules"] == "|".join(runtime.KNOWN_RULE_IDS[9:])
    assert coverage["integration_transition"] == "admit_009_implemented_and_removed_from_open_coverage_scope"
    duplicate = issues["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]
    assert duplicate["status"] == "resolved"
    assert duplicate["integration_transition"] == "duplicate_identity_key_contract_frozen_v1"


def test_only_coverage_issue_row_and_two_fields_change(
    state: dict[str, Any], snapshot: runtime.FrozenSourceSnapshot
) -> None:
    predecessor = runtime._csv_document(snapshot, runtime.DESIGN_ISSUE_PATH).rows
    successor = state["issue_rows"]
    assert len(predecessor) == len(successor) == 11
    changed_rows = []
    for before, after in zip(predecessor, successor, strict=True):
        assert before["issue_id"] == after["issue_id"]
        changed = {key for key in before if before[key] != after[key]}
        if changed:
            changed_rows.append((before["issue_id"], changed))
    assert changed_rows == [
        ("UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", {"affected_rules", "integration_transition"})
    ]


def test_manifest_full_semantics_counts_and_readiness(
    state: dict[str, Any], checker: Any
) -> None:
    manifest = runtime._manifest_payload(state, checker.MANIFEST_OUTPUT_SHA256)
    assert manifest == checker._expected_manifest()
    assert len(manifest) == manifest["manifest_top_level_key_count"] == 146
    assert manifest["readiness_true_count"] == len(runtime.TRUE_READINESS) == 21
    assert manifest["readiness_false_count"] == len(runtime.FALSE_READINESS) == 13
    for name in runtime.TRUE_READINESS:
        assert manifest[name] is manifest["readiness"][name] is True
    for name in runtime.FALSE_READINESS:
        assert manifest[name] is manifest["readiness"][name] is False
    assert manifest["real_provider_duplicate_identity_key_count"] == 0
    assert manifest["real_provider_duplicate_identity_mapping_executed"] is False
    assert manifest["admit_010_started"] is False
    assert manifest["evaluate_all_rules_implemented"] is False
    assert manifest["combined_candidate_verdict_implemented"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["validation_incident"] == checker.VALIDATION_INCIDENT
    assert manifest["validation_incident"] == runtime.VALIDATION_INCIDENT
    assert manifest["stop_boundaries"] == [
        "no_admit_010",
        "no_provider_mapping",
        "no_real_candidate_evaluation",
        "no_evaluate_all_rules",
        "no_combined_candidate_verdict",
        "no_raw_read_by_exact9_public_runtime_or_exact9_materializer",
        "no_network_or_download",
        "no_model_forward_loss_training",
    ]
    assert "no_raw_network_download" not in manifest["stop_boundaries"]
    summary = SUMMARY_PATH.read_text(encoding="utf-8")
    for statement in (
        "Exact9 public runtime and Exact9 materializer did not read raw data",
        "legacy real-provider checker was run in error",
        "read existing local raw data",
        "temporarily rematerialized and modified eight tracked historical outputs",
        "restored exactly to HEAD",
        "tracked and staged residual diff counts are both zero",
        "No network access or download occurred",
        "workflow instruction violation",
        "documented and contained",
        "safe checker allowlist",
        "unsafe checker was not run again",
    ):
        assert statement in summary


def test_deterministic_double_materialization_and_committed_outputs(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1(first)
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1(second)
    assert {path.name for path in first.iterdir()} == set(runtime.OUTPUT_FILES)
    for filename in runtime.OUTPUT_FILES:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
        assert (first / filename).read_bytes() == (OUTPUT_ROOT / filename).read_bytes()


@pytest.mark.parametrize("mode", ("unexpected", "directory", "symlink", "root_symlink"))
def test_output_preflight_rejects_unsafe_existing_state(
    tmp_path: Path, mode: str
) -> None:
    root = tmp_path / "output"
    if mode == "root_symlink":
        target = tmp_path / "target"
        target.mkdir()
        root.symlink_to(target, target_is_directory=True)
    else:
        root.mkdir()
        path = root / (
            "unexpected.txt" if mode == "unexpected" else runtime.CONTRACT_FILENAME
        )
        if mode == "unexpected":
            path.write_text("x", encoding="utf-8")
        elif mode == "directory":
            path.mkdir()
        else:
            target = tmp_path / "target"
            target.write_text("x", encoding="utf-8")
            path.symlink_to(target)
    with pytest.raises(ValueError):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1(root)


def test_checker_full_output_validation_and_independence(checker: Any) -> None:
    checker._assert_checker_independent_ast()
    checker._check_source_boundary()
    checker._check_public_call_graph()
    checker._check_runtime_directly()
    counts = checker._validate_output_root(OUTPUT_ROOT)
    assert counts == {
        "contract_rows": 79,
        "truth_rows": 289,
        "registry_rows": 15,
        "safety_rows": 43,
        "issue_rows": 11,
    }


def test_checker_rejects_semantic_tamper_with_refreshed_manifest_hash(
    checker: Any, tmp_path: Path
) -> None:
    root = tmp_path / "tampered"
    shutil.copytree(OUTPUT_ROOT, root)
    path = root / runtime.CONTRACT_FILENAME
    header, rows = checker._csv(path)
    rows[0]["observed_value"] = "false"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")
    manifest_path = root / runtime.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][runtime.CONTRACT_FILENAME] = checker._sha256(path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_output_root(root, enforce_frozen_hashes=False)

    for field, false_value in (
        ("incident_occurred", False),
        ("existing_raw_read_occurred", False),
        ("temporary_tracked_modification_count", 0),
        ("temporary_changes_restored_to_head", False),
        ("incident_contained", False),
    ):
        incident_root = tmp_path / f"incident-{field}"
        shutil.copytree(OUTPUT_ROOT, incident_root)
        incident_path = incident_root / runtime.MANIFEST_FILENAME
        incident_manifest = json.loads(incident_path.read_text(encoding="utf-8"))
        incident_manifest["validation_incident"][field] = false_value
        incident_path.write_text(
            json.dumps(incident_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(AssertionError):
            checker._validate_output_root(
                incident_root, enforce_frozen_hashes=False
            )


@pytest.mark.parametrize("mode", ("missing", "extra", "symlink"))
def test_checker_rejects_missing_extra_and_symlink_output(
    checker: Any, tmp_path: Path, mode: str
) -> None:
    root = tmp_path / mode
    shutil.copytree(OUTPUT_ROOT, root)
    victim = root / runtime.CONTRACT_FILENAME
    if mode == "missing":
        victim.unlink()
    elif mode == "extra":
        (root / "unexpected.txt").write_text("x", encoding="utf-8")
    else:
        victim.unlink()
        victim.symlink_to(OUTPUT_ROOT / runtime.CONTRACT_FILENAME)
    with pytest.raises(AssertionError):
        checker._validate_output_root(root)


@pytest.mark.parametrize(
    "mutation",
    (
        "unknown_key", "readiness_top", "readiness_nested", "registered",
        "provider", "coverage", "source_sha", "output_sha",
    ),
)
def test_checker_rejects_manifest_semantic_drift(
    checker: Any, tmp_path: Path, mutation: str
) -> None:
    root = tmp_path / mutation
    shutil.copytree(OUTPUT_ROOT, root)
    path = root / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "unknown_key":
        manifest["unknown"] = True
    elif mutation == "readiness_top":
        manifest["ready_for_training"] = True
    elif mutation == "readiness_nested":
        manifest["readiness"]["ready_for_training"] = True
    elif mutation == "registered":
        manifest["registered_rule_ids"].append("ADMIT_010")
    elif mutation == "provider":
        manifest["real_provider_duplicate_identity_key_count"] = 1
    elif mutation == "coverage":
        manifest["issue_coverage_after"].insert(0, "ADMIT_009")
    elif mutation == "source_sha":
        manifest["source_input_sha256"][str(runtime.SOURCE_PATHS[0])] = "0" * 64
    else:
        manifest["output_sha256"][runtime.CONTRACT_FILENAME] = "0" * 64
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_output_root(root, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "needle",
    (
        "runtime._contract_rows()",
        "runtime._truth_rows(())",
        "runtime._manifest_payload({}, {})",
        "runtime.SOURCE_PATHS",
        "runtime.TRUE_READINESS",
    ),
)
def test_checker_ast_rejects_production_expected_dependencies(
    checker: Any, needle: str
) -> None:
    source = CHECKER_PATH.read_text(encoding="utf-8")
    marker = "def _expected_manifest() -> dict[str, object]:"
    replacement = marker + f"\n    {needle}\n"
    tampered = source.replace(marker, replacement, 1)
    with pytest.raises(AssertionError, match="depends on production"):
        checker._assert_checker_independent_ast(tampered)


def test_public_runtime_call_graph_and_import_boundary(checker: Any) -> None:
    checker._check_public_call_graph()
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    import_section = source.split("PROJECT =", 1)[0]
    assert "admit_009_unified_adapter_contract_design_gate" not in import_section
    assert "provider" not in import_section.lower()
    assert "torch" not in import_section
    assert "numpy" not in import_section
    assert "rdkit" not in import_section.lower()
    assert import_section.count("from covalent_ext import") == 3


@pytest.mark.parametrize("target", ("runtime", "checker"))
def test_silent_imports(target: str) -> None:
    if target == "runtime":
        command = "import covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009"
    else:
        command = (
            "import importlib.util;"
            f"s=importlib.util.spec_from_file_location('exact9_checker',{str(CHECKER_PATH)!r});"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
        )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_checker_double_run_is_deterministic() -> None:
    first = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        check=False,
    )
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"all_checks_passed=true" in first.stdout


def test_no_import_output_materialization_side_effect(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    command = (
        "from pathlib import Path;"
        f"p=Path({str(marker)!r});"
        "import covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009;"
        "assert not p.exists()"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_production_and_checker_parse_without_dynamic_code_generation() -> None:
    for path in (Path(runtime.__file__), CHECKER_PATH, Path(__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "eval" not in calls
        assert "exec" not in calls
