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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007
    as runtime,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1.py"
)
OUTPUT_ROOT = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
OLD_EXACT6_ISSUE_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/"
    "covapie_admit_001_to_006_runtime_issue_inventory.csv"
)
OLD_EXACT6_ISSUE_SHA256 = (
    "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196"
)


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
    spec = importlib.util.spec_from_file_location("exact7_checker_for_test", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _values(value: object, names: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in names)


def _candidate(value: object = "explicit_structure_bond_record") -> dict[str, object]:
    return {runtime.ADMIT_007_CANDIDATE_FIELDS[0]: value}


def _context(value: object = runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES) -> dict[str, object]:
    return {runtime.ADMIT_007_CONTEXT_ITEMS[0]: value}


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
            raise AssertionError("required value read twice")
        if not self.present:
            raise KeyError(key)
        return self.value

    def __iter__(self):
        raise AssertionError("Mapping copied or iterated")

    def __len__(self) -> int:
        raise AssertionError("Mapping copied or sized")

    def payload(self) -> tuple[str, object, bool]:
        return (self.key, self.value, self.present)


def _mutate(value: object, name: str, replacement: object) -> object:
    object.__setattr__(value, name, replacement)
    return value


def _valid_source() -> runtime.admit007.Admit007EvaluationResult:
    return runtime.admit007.evaluate_admit_007(
        runtime.admit007.CANONICAL_ENUM_MEMBERS[0],
        runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )


def test_exact18_order_and_sha_are_frozen(snapshot: runtime.FrozenSourceSnapshot) -> None:
    checker = _load_checker()
    expected = checker._expected_source_boundary()
    assert len(runtime.SOURCE_PATHS) == len(set(runtime.SOURCE_PATHS)) == 18
    assert tuple(runtime.SOURCE_SHA256) == runtime.SOURCE_PATHS
    assert runtime.SOURCE_PATHS == tuple(path for path, _ in expected)
    assert runtime.SOURCE_SHA256 == dict(expected)
    assert OLD_EXACT6_ISSUE_PATH not in runtime.SOURCE_PATHS
    assert not hasattr(runtime, "EXACT6_ISSUE_PATH")
    assert runtime.validate_frozen_source_snapshot(snapshot)
    for record in snapshot.records:
        assert record.expected_sha256 == runtime.SOURCE_SHA256[record.relative_path]
        assert record.base_tree_sha256 == record.expected_sha256
        assert record.filesystem_sha256 == record.expected_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256


def test_base_commit_subject_and_lineage() -> None:
    assert runtime.EXPECTED_BASE_COMMIT == "ea6678caef867bf2c4c0901bc4066f4d5e4f7520"
    assert runtime.EXPECTED_BASE_SUBJECT == "add CovaPIE ADMIT_007 unified adapter contract design v1"
    runtime._validate_expected_base_lineage(REPO_ROOT)


def test_all_structural_checks_precede_first_source_byte_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_structural = runtime._structural_source_check
    real_git = runtime._git
    structural: list[Path] = []

    def counted(path: Path, root: Path) -> bool:
        structural.append(path)
        return real_structural(path, root)

    def guarded(
        arguments: list[str], root: Path, *, text: bool = True
    ) -> subprocess.CompletedProcess[Any]:
        if arguments and arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1]:
            assert tuple(structural) == runtime.SOURCE_PATHS
        return real_git(arguments, root, text=text)

    monkeypatch.setattr(runtime, "_structural_source_check", counted)
    monkeypatch.setattr(runtime, "_git", guarded)
    assert runtime.validate_frozen_source_snapshot(runtime.build_frozen_source_snapshot())


def test_non_descendant_lineage_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    real_git = runtime._git

    def non_descendant(
        arguments: list[str], root: Path, *, text: bool = True
    ) -> subprocess.CompletedProcess[Any]:
        if arguments[:2] == ["merge-base", "--is-ancestor"]:
            empty = "" if text else b""
            return subprocess.CompletedProcess(arguments, 1, empty, empty)
        return real_git(arguments, root, text=text)

    monkeypatch.setattr(runtime, "_git", non_descendant)
    with pytest.raises(ValueError, match="not an ancestor"):
        runtime.build_frozen_source_snapshot(head_ref="deterministic_non_descendant")


def test_source_sha_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    changed = dict(runtime.SOURCE_SHA256)
    changed[runtime.SOURCE_PATHS[0]] = "0" * 64
    monkeypatch.setattr(runtime, "SOURCE_SHA256", changed)
    with pytest.raises(ValueError, match="source SHA256 mismatch"):
        runtime.build_frozen_source_snapshot()


def test_source_symlink_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_public_type_schema_and_vocabulary_identity() -> None:
    assert runtime.UnifiedAdmissionRuleEvaluation is runtime.predecessor.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionDispatchError is runtime.predecessor.UnifiedAdmissionDispatchError
    assert runtime.RESULT_SCHEMA_VERSION is runtime.predecessor.RESULT_SCHEMA_VERSION
    assert runtime.RESULT_FIELDS is runtime.predecessor.RESULT_FIELDS
    assert runtime.DISPATCH_ERROR_FIELDS is runtime.predecessor.DISPATCH_ERROR_FIELDS
    assert runtime.DISPATCH_ERROR_CODES is runtime.predecessor.DISPATCH_ERROR_CODES
    assert runtime.OUTCOME_VOCABULARY is runtime.predecessor.OUTCOME_VOCABULARY


def test_public_signature_and_single_rule_boundary() -> None:
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        runtime.predecessor.evaluate_admission_rule
    )
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")


def test_exact7_registry_and_first_six_identity() -> None:
    assert runtime.KNOWN_RULE_IDS == tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == runtime.KNOWN_RULE_IDS[:7]
    assert runtime.ADAPTER_READY_RULE_IDS == runtime.CALLABLE_DISCOVERED_RULE_IDS
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == runtime.KNOWN_RULE_IDS[:7]
    for rule_id in runtime.KNOWN_RULE_IDS[:6]:
        assert runtime.EVALUATOR_REGISTRY[rule_id] is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        assert runtime.RULE_NAMES[rule_id] == runtime.predecessor.RULE_NAMES[rule_id]
        assert runtime.ADAPTER_IDS[rule_id] == runtime.predecessor.ADAPTER_IDS[rule_id]
    assert runtime.EVALUATOR_REGISTRY["ADMIT_007"] is runtime._evaluate_registered_admit_007
    assert runtime.RULE_NAMES["ADMIT_007"] == "distance_only_inference_forbidden"
    assert runtime.ADAPTER_IDS["ADMIT_007"] == "covapie_admit_007_unified_adapter_v1"


@pytest.mark.parametrize("mutation", ("wrapper", "mutable", "order", "missing007", "register008"))
def test_registry_mutations_fail_runtime_state(
    monkeypatch: pytest.MonkeyPatch,
    snapshot: runtime.FrozenSourceSnapshot,
    mutation: str,
) -> None:
    values = dict(runtime.EVALUATOR_REGISTRY)
    if mutation == "wrapper":
        original = values["ADMIT_001"]
        values["ADMIT_001"] = lambda *args, **kwargs: original(*args, **kwargs)
        replacement: object = MappingProxyType(values)
    elif mutation == "mutable":
        replacement = values
    elif mutation == "order":
        replacement = MappingProxyType(
            {key: values[key] for key in ("ADMIT_002", "ADMIT_001", *runtime.KNOWN_RULE_IDS[2:7])}
        )
    elif mutation == "missing007":
        values.pop("ADMIT_007")
        replacement = MappingProxyType(values)
    else:
        values["ADMIT_008"] = runtime._evaluate_registered_admit_007
        replacement = MappingProxyType(values)
    monkeypatch.setattr(runtime, "EVALUATOR_REGISTRY", replacement)
    assert runtime.build_runtime_state(snapshot)["all_checks_passed"] is False


@pytest.mark.parametrize(
    ("rule_id", "code", "reported", "flags"),
    (
        (6, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", (False, False, False)),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", (False, False, False)),
        ("ADMIT_008", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "ADMIT_008", (True, False, False)),
    ),
)
def test_global_dispatch_errors(
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


def test_rule_id_str_subclass_is_rejected_before_known_and_registered() -> None:
    class Text(str):
        pass

    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            Text("ADMIT_007"),
            [],
            batch_context={},
            evaluation_context=[],
        )
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"
    assert _values(caught.value, runtime.DISPATCH_ERROR_FIELDS)[1:5] == (
        "",
        False,
        False,
        False,
    )


@pytest.mark.parametrize("rule_id", runtime.KNOWN_RULE_IDS[7:])
def test_admit008_to_015_known_not_registered_flags(rule_id: str) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})
    assert (caught.value.known_rule, caught.value.callable_discovered, caught.value.adapter_ready) == (
        True,
        False,
        False,
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    (
        ({"batch_context": {}}, "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": []}, "ADMIT_007_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_007_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED"),
        (
            {"evaluation_context": _context(), "download_result_context": {}},
            "ADMIT_007_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"evaluation_context": _context(), "stage_authorization_context": {}},
            "ADMIT_007_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ),
        (
            {
                "batch_context": {},
                "evaluation_context": [],
                "download_result_context": {},
                "stage_authorization_context": {},
            },
            "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE",
        ),
    ),
)
def test_context_precedence_candidate_not_accessed_and_zero_calls(
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
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: counts.update(["formal"]),
    )
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule("ADMIT_007", bomb, **kwargs)
    assert _values(caught.value, runtime.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_007",
        True,
        True,
        True,
        reason,
    )
    assert counts == Counter()
    assert bomb.accesses == 0


def test_invalid_routed_context_reaches_standalone_not_dispatch() -> None:
    result = runtime.evaluate_admission_rule(
        "ADMIT_007",
        _candidate(),
        evaluation_context=_context(None),
    )
    expected_pair = ((runtime.ADMIT_007_CANDIDATE_FIELDS[0], runtime.admit007.CANONICAL_ENUM_MEMBERS[0]),)
    assert result.outcome == "invalid"
    assert result.reason == runtime.admit007.CONTEXT_REASONS[0]
    assert result.normalized_values == result.validated_candidate_fields == expected_pair


def test_mapping_subclasses_extra_keys_identity_no_copy_and_no_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scalar = object()
    context_value = object()
    candidate = _SingleLookupMapping(
        runtime.ADMIT_007_CANDIDATE_FIELDS[0], scalar
    )
    evaluation = _SingleLookupMapping(
        runtime.ADMIT_007_CONTEXT_ITEMS[0], context_value
    )
    candidate_before = candidate.payload()
    evaluation_before = evaluation.payload()
    source = _valid_source()
    oracle = runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design(
        runtime.admit007.CANONICAL_ENUM_MEMBERS[0],
        runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    calls: dict[str, list[tuple[object, object]]] = {"formal": [], "oracle": []}
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda left, right: calls["formal"].append((left, right)) or source,
    )
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda left, right: calls["oracle"].append((left, right)) or oracle,
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_007", candidate, evaluation_context=evaluation
    )
    assert result.outcome == "passed"
    assert calls == {
        "formal": [(scalar, context_value)],
        "oracle": [(scalar, context_value)],
    }
    assert candidate.lookup_count == evaluation.lookup_count == 1
    assert candidate.payload() == candidate_before
    assert evaluation.payload() == evaluation_before


def test_stateful_candidate_mapping_uses_only_first_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = runtime.admit007.CANONICAL_ENUM_MEMBERS[0]
    second = runtime.admit007.CANONICAL_ENUM_MEMBERS[1]

    class StatefulMapping(Mapping[str, object]):
        lookup_count = 0

        def __getitem__(self, key: str) -> object:
            if key != runtime.ADMIT_007_CANDIDATE_FIELDS[0]:
                raise KeyError(key)
            self.lookup_count += 1
            return first if self.lookup_count == 1 else second

        def __iter__(self):
            raise AssertionError("Mapping copied or iterated")

        def __len__(self) -> int:
            raise AssertionError("Mapping copied or sized")

    candidate = StatefulMapping()
    formal_real = runtime.admit007.evaluate_admit_007
    oracle_real = (
        runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design
    )
    calls: dict[str, list[object]] = {"formal": [], "oracle": []}

    def formal(left: object, right: object) -> object:
        calls["formal"].append(left)
        return formal_real(left, right)

    def oracle(left: object, right: object) -> object:
        calls["oracle"].append(left)
        return oracle_real(left, right)

    monkeypatch.setattr(runtime.admit007, "evaluate_admit_007", formal)
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        oracle,
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_007", candidate, evaluation_context=_context()
    )
    assert result.outcome == "passed"
    assert result.normalized_values == (
        (runtime.ADMIT_007_CANDIDATE_FIELDS[0], first),
    )
    assert candidate.lookup_count == 1
    assert calls == {"formal": [first], "oracle": [first]}


def test_missing_candidate_key_uses_one_lookup_and_no_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _SingleLookupMapping(
        runtime.ADMIT_007_CANDIDATE_FIELDS[0], object(), present=False
    )
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: pytest.fail("formal called"),
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_007", candidate, evaluation_context=_context()
    )
    assert result.reason == "covalent_event_evidence_missing"
    assert candidate.lookup_count == 1


def test_missing_context_key_uses_one_lookup_before_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evaluation = _SingleLookupMapping(
        runtime.ADMIT_007_CONTEXT_ITEMS[0], object(), present=False
    )
    candidate = _SingleLookupMapping(
        runtime.ADMIT_007_CANDIDATE_FIELDS[0], object()
    )
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: pytest.fail("formal called"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007", candidate, evaluation_context=evaluation
        )
    assert caught.value.reason == (
        "ADMIT_007_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED"
    )
    assert evaluation.lookup_count == 1
    assert candidate.lookup_count == 0


def test_context_lookup_precedes_download_gate_and_candidate_access() -> None:
    evaluation = _SingleLookupMapping(
        runtime.ADMIT_007_CONTEXT_ITEMS[0],
        runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    candidate = _SingleLookupMapping(
        runtime.ADMIT_007_CANDIDATE_FIELDS[0], object()
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007",
            candidate,
            evaluation_context=evaluation,
            download_result_context={},
        )
    assert caught.value.reason == "ADMIT_007_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
    assert evaluation.lookup_count == 1
    assert candidate.lookup_count == 0


@pytest.mark.parametrize(
    ("candidate", "reason"),
    (
        ([], "ADMIT_007_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "covalent_event_evidence_missing"),
        (_candidate(None), "covalent_event_evidence_missing"),
        (_candidate(""), "covalent_event_evidence_missing"),
    ),
)
def test_candidate_envelope_and_missing_exact13_zero_calls(
    monkeypatch: pytest.MonkeyPatch,
    candidate: object,
    reason: str,
) -> None:
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: pytest.fail("formal called"),
    )
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: pytest.fail("oracle called"),
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_007", candidate, evaluation_context=_context()  # type: ignore[arg-type]
    )
    assert _values(result, runtime.RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_007",
        "distance_only_inference_forbidden",
        "invalid",
        False,
        True,
        reason,
        (),
        (),
        runtime.ADMIT_007_CANDIDATE_FIELDS,
        runtime.ADMIT_007_CONTEXT_ITEMS,
        False,
        "covapie_admit_007_unified_adapter_v1",
    )


class _EmptyStringSubclass(str):
    pass


@pytest.mark.parametrize(
    ("value", "outcome", "reason"),
    (
        (_EmptyStringSubclass(""), "invalid", runtime.admit007.SCALAR_REASONS[0]),
        (" ", "invalid", runtime.admit007.SCALAR_REASONS[3]),
        ("BAD", "invalid", runtime.admit007.SCALAR_REASONS[3]),
        ("é", "invalid", runtime.admit007.SCALAR_REASONS[2]),
        (7, "invalid", runtime.admit007.SCALAR_REASONS[0]),
        (True, "invalid", runtime.admit007.SCALAR_REASONS[0]),
        ([], "invalid", runtime.admit007.SCALAR_REASONS[0]),
        ({}, "invalid", runtime.admit007.SCALAR_REASONS[0]),
        ((), "invalid", runtime.admit007.SCALAR_REASONS[0]),
        ("distance_only_inference", "blocked", runtime.admit007.BLOCKED_REASON),
    ),
)
def test_nonmissing_values_reach_formal_and_oracle_once(
    monkeypatch: pytest.MonkeyPatch,
    value: object,
    outcome: str,
    reason: str,
) -> None:
    formal_real = runtime.admit007.evaluate_admit_007
    oracle_real = runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design
    calls = Counter()

    def formal(left: object, right: object) -> object:
        calls.update(["formal"])
        assert left is value
        return formal_real(left, right)

    def oracle(left: object, right: object) -> object:
        calls.update(["oracle"])
        assert left is value
        return oracle_real(left, right)

    monkeypatch.setattr(runtime.admit007, "evaluate_admit_007", formal)
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        oracle,
    )
    result = runtime.evaluate_admission_rule(
        "ADMIT_007", _candidate(value), evaluation_context=_context()
    )
    assert (result.outcome, result.reason) == (outcome, reason)
    assert calls == {"formal": 1, "oracle": 1}


@pytest.mark.parametrize(
    ("scalar", "context_value", "outcome", "reason", "validated"),
    (
        (
            "explicit_structure_bond_record",
            runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
            ((runtime.ADMIT_007_CANDIDATE_FIELDS[0], "explicit_structure_bond_record"),),
        ),
        (
            "explicit_curated_covalent_annotation",
            runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
            ((runtime.ADMIT_007_CANDIDATE_FIELDS[0], "explicit_curated_covalent_annotation"),),
        ),
        (
            "distance_only_inference",
            runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "blocked",
            runtime.admit007.BLOCKED_REASON,
            ((runtime.ADMIT_007_CANDIDATE_FIELDS[0], "distance_only_inference"),),
        ),
        (
            "unknown",
            runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            runtime.admit007.SCALAR_REASONS[4],
            (),
        ),
        (
            "explicit_structure_bond_record",
            None,
            "invalid",
            runtime.admit007.CONTEXT_REASONS[0],
            ((runtime.ADMIT_007_CANDIDATE_FIELDS[0], "explicit_structure_bond_record"),),
        ),
    ),
)
def test_exact13_projection_semantics(
    scalar: object,
    context_value: object,
    outcome: str,
    reason: str,
    validated: tuple[tuple[str, str], ...],
) -> None:
    result = runtime.evaluate_admission_rule(
        "ADMIT_007",
        _candidate(scalar),
        evaluation_context=_context(context_value),
    )
    assert result.outcome == outcome
    assert result.passed is (outcome == "passed")
    assert result.blocks_candidate is (outcome != "passed")
    assert result.reason == reason
    assert result.normalized_values == result.validated_candidate_fields == validated
    assert result.consumed_candidate_fields == runtime.ADMIT_007_CANDIDATE_FIELDS
    assert result.consumed_context_items == runtime.ADMIT_007_CONTEXT_ITEMS
    assert result.evaluator_io_used is False


def _source_subclass(valid: runtime.admit007.Admit007EvaluationResult) -> object:
    class Subclass(runtime.admit007.Admit007EvaluationResult):
        pass

    value = object.__new__(Subclass)
    for name in runtime.admit007.RESULT_FIELDS:
        object.__setattr__(value, name, getattr(valid, name))
    return value


def _source_missing_storage(
    valid: runtime.admit007.Admit007EvaluationResult,
) -> runtime.admit007.Admit007EvaluationResult:
    object.__delattr__(valid, runtime.admit007.RESULT_FIELDS[-1])
    return valid


def _source_extra_storage(
    valid: runtime.admit007.Admit007EvaluationResult,
) -> runtime.admit007.Admit007EvaluationResult:
    object.__setattr__(valid, "extra", True)
    return valid


@pytest.mark.parametrize(
    ("factory", "reason"),
    (
        (lambda valid: object(), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (lambda valid: _source_subclass(valid), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (_source_missing_storage, "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (_source_extra_storage, "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "admission_rule_id", "ADMIT_005"), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "outcome", "invalid"), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "passed", False), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "blocks_candidate", True), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "reason", runtime.admit007.SCALAR_REASONS[4]), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "canonical_covalent_event_evidence_source", "distance_only_inference"), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "validated_candidate_fields", ()), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "consumed_candidate_fields", ()), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "consumed_context_items", ()), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        (lambda valid: _mutate(valid, "evaluator_io_used", True), "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
    ),
)
def test_source_failures_precede_oracle_and_projection(
    monkeypatch: pytest.MonkeyPatch,
    factory: Any,
    reason: str,
) -> None:
    source = factory(_valid_source())
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: counts.update(["formal"]) or source,
    )
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: counts.update(["oracle"]) or pytest.fail("oracle called"),
    )
    monkeypatch.setattr(
        runtime,
        "_project_admit007_exact13",
        lambda *args: pytest.fail("projected"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007", _candidate(), evaluation_context=_context()
        )
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert caught.value.adapter_ready is False
    assert caught.value.reason == reason
    assert counts == {"formal": 1}


@pytest.mark.parametrize(
    "factory", (_source_missing_storage, _source_extra_storage)
)
def test_exact_source_storage_shape_corruption_is_exact_type_and_rejected(
    monkeypatch: pytest.MonkeyPatch,
    factory: Any,
) -> None:
    source = factory(_valid_source())
    assert type(source) is runtime.admit007.Admit007EvaluationResult
    assert tuple(vars(source)) != runtime.admit007.RESULT_FIELDS
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: counts.update(["formal"]) or source,
    )
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: counts.update(["oracle"]),
    )
    monkeypatch.setattr(
        runtime,
        "_project_admit007_exact13",
        lambda *args: counts.update(["projection"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007", _candidate(), evaluation_context=_context()
        )
    assert caught.value.reason == (
        "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )
    assert counts == {"formal": 1}


def test_source_result_field_shape_guard_precedes_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts = Counter()
    monkeypatch.setattr(runtime, "fields", lambda value: ())
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: counts.update(["oracle"]),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007", _candidate(), evaluation_context=_context()
        )
    assert caught.value.reason == "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert counts == Counter()


def test_oracle_mismatch_calls_each_once_and_never_projects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = _valid_source()
    mismatch = runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design(
        "explicit_curated_covalent_annotation",
        runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    counts = Counter()
    monkeypatch.setattr(
        runtime.admit007,
        "evaluate_admit_007",
        lambda *args: counts.update(["formal"]) or valid,
    )
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: counts.update(["oracle"]) or mismatch,
    )
    monkeypatch.setattr(
        runtime,
        "_project_admit007_exact13",
        lambda *args: pytest.fail("projected"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007", _candidate(), evaluation_context=_context()
        )
    assert caught.value.reason == "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert counts == {"formal": 1, "oracle": 1}


@pytest.mark.parametrize("attribute", ("scalar", "context", "admit_007"))
def test_malformed_oracle_classification_fails_without_projection(
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
) -> None:
    classification = runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design(
        runtime.admit007.CANONICAL_ENUM_MEMBERS[0],
        runtime.admit007.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    values = {
        "scalar": classification.scalar,
        "context": classification.context,
        "admit_007": classification.admit_007,
    }
    values.pop(attribute)
    malformed = SimpleNamespace(**values)
    monkeypatch.setattr(
        runtime.admit007_oracle,
        "classify_admit_006_admit_007_evidence_design",
        lambda *args: malformed,
    )
    monkeypatch.setattr(
        runtime,
        "_project_admit007_exact13",
        lambda *args: pytest.fail("projected"),
    )
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(
            "ADMIT_007", _candidate(), evaluation_context=_context()
        )
    assert caught.value.reason == "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


@pytest.mark.parametrize("case", runtime._predecessor_parity_definitions(), ids=lambda case: case["id"])
def test_predecessor_representative_behavior_parity(case: dict[str, Any]) -> None:
    def invoke(module: object) -> object:
        try:
            return module.evaluate_admission_rule(
                case["rule"], case["candidate"], **case["kwargs"]
            )
        except runtime.UnifiedAdmissionDispatchError as error:
            return error

    successor = invoke(runtime)
    predecessor = invoke(runtime.predecessor)
    assert type(successor) is type(predecessor)
    names = (
        runtime.RESULT_FIELDS
        if type(successor) is runtime.UnifiedAdmissionRuleEvaluation
        else runtime.DISPATCH_ERROR_FIELDS
    )
    assert _values(successor, names) == _values(predecessor, names)


def test_exact37_runtime_paths_and_adapter_missing_override() -> None:
    counts = Counter()
    for _, scalar, context_value in runtime._synthetic_exact37_definitions():
        result = runtime.evaluate_admission_rule(
            "ADMIT_007",
            _candidate(scalar),
            evaluation_context=_context(context_value),
        )
        if scalar is None or (type(scalar) is str and scalar == ""):
            assert result.reason == "covalent_event_evidence_missing"
            counts.update(["adapter_missing"])
        else:
            standalone = runtime.admit007.evaluate_admit_007(scalar, context_value)
            assert (result.outcome, result.reason) == (
                standalone.outcome,
                standalone.reason,
            )
            assert result.validated_candidate_fields == standalone.validated_candidate_fields
            counts.update(["standalone"])
    assert counts == {"adapter_missing": 2, "standalone": 35}


def test_runtime_state_exact_counts_and_groups(state: dict[str, Any]) -> None:
    assert len(state["contract_rows"]) == len(runtime._contract_definitions()) == 56
    assert len(state["truth_rows"]) == 107
    assert state["truth_group_counts"] == {
        "global_dispatch": 5,
        "predecessor_identity_and_behavior": 14,
        "context_routing": 7,
        "candidate_envelope": 12,
        "standalone_semantics": 37,
        "source_fail_closed": 15,
        "projection_semantics": 7,
        "unsupported_boundary": 10,
    }
    assert len(state["registry_rows"]) == 15
    assert len(state["safety_rows"]) == 36
    assert all(row["case_passed"] == "true" for row in state["truth_rows"])


def test_issue_inventory_only_coverage_row_transitions(state: dict[str, Any]) -> None:
    old = list(state["predecessor"]["design_issue_rows"])
    new = state["issue_rows"]
    assert len(old) == len(new) == 11
    for before, after in zip(old, new, strict=True):
        if before["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE":
            assert after["status"] == "open"
            assert after["affected_rules"] == "|".join(runtime.KNOWN_RULE_IDS[7:])
            assert after["integration_transition"] == "admit_007_implemented_and_removed_from_open_coverage_scope"
            assert after["issue_count"] == "1"
            for key in runtime.ISSUE_COLUMNS:
                if key not in (
                    "status",
                    "affected_rules",
                    "integration_transition",
                    "issue_count",
                ):
                    assert after[key] == before[key]
        else:
            assert after == before
    issue_map = {row["issue_id"]: row for row in new}
    assert issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"] == "resolved"
    assert issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open"
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] == "open"
    assert issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"


def test_manifest_readiness_exact(state: dict[str, Any]) -> None:
    _, manifest = runtime._payloads(state)
    assert manifest["source_boundary_name"] == (
        "fixed_ordered_minimal_exact18_committed_source_boundary"
    )
    assert manifest["source_input_count"] == 18
    assert manifest["source_input_paths"] == [
        path.as_posix() for path in runtime.SOURCE_PATHS
    ]
    assert OLD_EXACT6_ISSUE_PATH.as_posix() not in manifest["source_input_paths"]
    assert manifest["registered_rule_ids"] == list(runtime.KNOWN_RULE_IDS[:7])
    assert manifest["registered_rule_count"] == 7
    assert manifest["predecessor_exact6_runtime_modified"] is False
    assert manifest["predecessor_handlers_reused_by_identity"] is True
    assert manifest["admit_007_implemented"] is True
    assert manifest["admit_007_registered"] is True
    assert manifest["admit_008_to_015_registered"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["feature_semantics_audit_required"] is True
    assert runtime.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["recommended_next_step"] == "audit_covapie_admit_008_formal_evaluator_interface_preconditions_v1"


def test_revised_contract_values_freeze_lookup_and_storage_shape(
    state: dict[str, Any],
) -> None:
    rows = {row["contract_id"]: row for row in state["contract_rows"]}
    assert rows["CONTEXT_004"]["expected_value"] == (
        "original_identity_single_lookup_no_prevalidation"
    )
    assert rows["FORMAL_001"]["expected_value"] == (
        "single_candidate_lookup_single_context_lookup_exact_positional_call"
    )
    assert rows["SOURCE_003"]["expected_value"] == (
        "exact_storage_keys_and_reconstruction_before_oracle"
    )


def test_default_outputs_match_generated_payloads(state: dict[str, Any]) -> None:
    payloads, _ = runtime._payloads(state)
    assert {path.name for path in OUTPUT_ROOT.iterdir()} == set(runtime.OUTPUT_FILES)
    for name in runtime.OUTPUT_FILES:
        assert (OUTPUT_ROOT / name).read_bytes() == payloads[name]


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(root)
    first = {name: (root / name).read_bytes() for name in runtime.OUTPUT_FILES}
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(root)
    second = {name: (root / name).read_bytes() for name in runtime.OUTPUT_FILES}
    assert first == second
    assert not tuple(root.glob("*.tmp"))
    assert not tuple(root.glob("*.part"))


@pytest.mark.parametrize("mode", ("unexpected", "directory", "symlink"))
def test_materializer_rejects_unsafe_existing_entries(tmp_path: Path, mode: str) -> None:
    root = tmp_path / "outputs"
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
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(root)


def test_output_root_symlink_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="real non-symlink"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(link)


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
    manifest_path = root / runtime.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("filename", "mutator", "message"),
    (
        (
            runtime.CONTRACT_FILENAME,
            lambda rows: rows[0].__setitem__("observed_value", "false"),
            "manifest semantic mismatch",
        ),
        (
            runtime.TRUTH_FILENAME,
            lambda rows: rows[0].__setitem__("observed_result_or_error", "passed"),
            "manifest semantic mismatch",
        ),
        (
            runtime.REGISTRY_FILENAME,
            lambda rows: rows[5].__setitem__("registered", "false"),
            "manifest semantic mismatch",
        ),
        (
            runtime.SAFETY_FILENAME,
            lambda rows: rows[0].__setitem__("observed_executed", "false"),
            "manifest semantic mismatch",
        ),
    ),
)
def test_checker_rejects_semantic_tamper_after_manifest_hash_refresh(
    tmp_path: Path,
    filename: str,
    mutator: Any,
    message: str,
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    _rewrite_csv(candidate / filename, mutator)
    _refresh_manifest_hash(candidate, filename)
    with pytest.raises(AssertionError, match=message):
        _load_checker()._validate_output_root(candidate, enforce_frozen_hashes=False)


@pytest.mark.parametrize("mode", ("missing", "extra", "symlink"))
def test_checker_rejects_missing_extra_and_symlink_outputs(tmp_path: Path, mode: str) -> None:
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


def test_checker_rejects_manifest_readiness_overclaim(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    path = candidate / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["readiness"]["ready_for_training"] = True
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="readiness"):
        _load_checker()._validate_output_root(candidate, enforce_frozen_hashes=False)


def _apply_full_manifest_mutation(
    case_id: str,
    manifest: dict[str, Any],
    candidate: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if case_id == "admit008_top_level_overclaim":
        manifest["admit_008_registered_in_engine"] = True
    elif case_id == "nested_false_top_level_true":
        manifest["ready_for_training"] = True
    elif case_id == "missing_top_level_readiness_mirror":
        del manifest["ready_to_train_now"]
    elif case_id == "unknown_top_level_key":
        manifest["unknown_manifest_field"] = False
    elif case_id == "missing_manifest_schema_version":
        del manifest["manifest_schema_version"]
    elif case_id == "adapter_design_gate_imported":
        manifest["adapter_design_gate_imported_by_runtime"] = True
    elif case_id == "runtime_dependency_import_added":
        manifest["runtime_dependency_imports"].append(
            "admit007_adapter_design_gate"
        )
    elif case_id == "artifact_reference_recursion":
        manifest["artifact_reference_paths_not_recursively_opened"] = False
    elif case_id == "synchronized_result_fields_drift":
        drifted = list(manifest["result_fields"])
        drifted[-1] = "adapter_identifier"
        manifest["result_fields"] = drifted
        monkeypatch.setattr(runtime, "RESULT_FIELDS", tuple(drifted))
    elif case_id == "synchronized_dispatch_error_codes_drift":
        drifted = list(manifest["dispatch_error_codes"])
        drifted[-1] = "UNIFIED_ADMISSION_CONTEXT_ROUTE_INVALID"
        manifest["dispatch_error_codes"] = drifted
        monkeypatch.setattr(runtime, "DISPATCH_ERROR_CODES", tuple(drifted))
    elif case_id == "admit007_adapter_id_replaced":
        manifest["adapter_ids"]["ADMIT_007"] = (
            "covapie_admit_007_replacement_adapter_v1"
        )
    elif case_id == "callable_discovered_missing_admit007":
        manifest["callable_discovered_rule_ids"].remove("ADMIT_007")
    elif case_id == "source_attestation_false":
        manifest["all_source_boundary_checks_passed"] = False
    elif case_id == "issue_attestation_false":
        manifest["all_issue_checks_passed"] = False
    elif case_id == "validation_failures_nonempty":
        manifest["validation_failures"] = ["SYNCHRONIZED_OVERCLAIM"]
    elif case_id == "truth_pass_count_drift":
        manifest["truth_matrix_pass_count"] = 106
    elif case_id == "extra_readiness_like_key":
        manifest["ready_for_uncontracted_future_step"] = False
    elif case_id == "output_sha_key_set_drift":
        del manifest["output_sha256"][runtime.ISSUE_FILENAME]
        assert all(
            hashlib.sha256((candidate / name).read_bytes()).hexdigest()
            == digest
            for name, digest in manifest["output_sha256"].items()
        )
    else:
        raise AssertionError(f"unknown manifest mutation: {case_id}")


@pytest.mark.parametrize(
    ("case_id", "message"),
    (
        ("admit008_top_level_overclaim", "manifest semantic mismatch"),
        ("nested_false_top_level_true", "manifest semantic mismatch"),
        ("missing_top_level_readiness_mirror", "manifest key set mismatch"),
        ("unknown_top_level_key", "manifest key set mismatch"),
        ("missing_manifest_schema_version", "manifest key set mismatch"),
        ("adapter_design_gate_imported", "manifest semantic mismatch"),
        ("runtime_dependency_import_added", "manifest semantic mismatch"),
        ("artifact_reference_recursion", "manifest semantic mismatch"),
        ("synchronized_result_fields_drift", "manifest semantic mismatch"),
        (
            "synchronized_dispatch_error_codes_drift",
            "manifest semantic mismatch",
        ),
        ("admit007_adapter_id_replaced", "manifest semantic mismatch"),
        (
            "callable_discovered_missing_admit007",
            "manifest semantic mismatch",
        ),
        ("source_attestation_false", "manifest semantic mismatch"),
        ("issue_attestation_false", "manifest semantic mismatch"),
        ("validation_failures_nonempty", "manifest semantic mismatch"),
        ("truth_pass_count_drift", "manifest semantic mismatch"),
        ("extra_readiness_like_key", "manifest key set mismatch"),
        ("output_sha_key_set_drift", "manifest semantic mismatch"),
    ),
)
def test_checker_full_manifest_contract_fails_closed_without_frozen_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    message: str,
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    path = candidate / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    _apply_full_manifest_mutation(case_id, manifest, candidate, monkeypatch)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match=message):
        _load_checker()._validate_output_root(
            candidate,
            enforce_frozen_hashes=False,
        )


def test_checker_owns_exact18_boundary_headers_issue_and_manifest() -> None:
    checker = _load_checker()
    boundary = checker._expected_source_boundary()
    assert len(boundary) == 18
    assert OLD_EXACT6_ISSUE_PATH not in tuple(path for path, _ in boundary)
    assert checker._expected_output_filenames() == checker.CHECKER_OUTPUT_FILES
    assert checker._expected_headers() == {
        checker.CHECKER_CONTRACT_FILENAME: checker.CHECKER_CONTRACT_HEADER,
        checker.CHECKER_TRUTH_FILENAME: checker.CHECKER_TRUTH_HEADER,
        checker.CHECKER_REGISTRY_FILENAME: checker.CHECKER_REGISTRY_HEADER,
        checker.CHECKER_SAFETY_FILENAME: checker.CHECKER_SAFETY_HEADER,
        checker.CHECKER_ISSUE_FILENAME: checker.CHECKER_ISSUE_HEADER,
    }
    manifest = checker._expected_manifest()
    assert len(manifest) == 98
    assert len(manifest["readiness"]) == 37
    assert manifest["source_input_count"] == 18
    assert manifest["source_input_paths"] == [
        path.as_posix() for path, _ in boundary
    ]
    assert checker.CHECKER_DESIGN_ISSUE_PATH == boundary[14][0]
    assert checker.CHECKER_DESIGN_ISSUE_SHA256 == boundary[14][1]
    disk_manifest = json.loads(
        (OUTPUT_ROOT / checker.CHECKER_MANIFEST_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert set(disk_manifest) == set(manifest)
    assert disk_manifest == manifest
    for key, value in manifest["readiness"].items():
        assert disk_manifest[key] is value
        assert disk_manifest["readiness"][key] is value


def test_checker_rejects_self_consistent_old_issue_boundary_addition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    paths = (*runtime.SOURCE_PATHS, OLD_EXACT6_ISSUE_PATH)
    sha = dict(runtime.SOURCE_SHA256)
    sha[OLD_EXACT6_ISSUE_PATH] = OLD_EXACT6_ISSUE_SHA256
    monkeypatch.setattr(runtime, "SOURCE_PATHS", paths)
    monkeypatch.setattr(runtime, "SOURCE_SHA256", sha)
    with pytest.raises(AssertionError, match="checker Exact18"):
        checker._check_source_boundary()


def test_checker_rejects_self_consistent_source_replacement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    paths = (*runtime.SOURCE_PATHS[:-1], OLD_EXACT6_ISSUE_PATH)
    sha = {
        path: (
            OLD_EXACT6_ISSUE_SHA256
            if path == OLD_EXACT6_ISSUE_PATH
            else runtime.SOURCE_SHA256[path]
        )
        for path in paths
    }
    monkeypatch.setattr(runtime, "SOURCE_PATHS", paths)
    monkeypatch.setattr(runtime, "SOURCE_SHA256", sha)
    with pytest.raises(AssertionError, match="checker Exact18"):
        checker._check_source_boundary()


def test_checker_rejects_manifest_and_production_exact19_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    manifest_path = candidate / checker.CHECKER_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_boundary_name"] = (
        "fixed_ordered_minimal_exact19_committed_source_boundary"
    )
    manifest["source_input_count"] = 19
    manifest["source_input_paths"].append(OLD_EXACT6_ISSUE_PATH.as_posix())
    manifest["source_input_sha256"][
        OLD_EXACT6_ISSUE_PATH.as_posix()
    ] = OLD_EXACT6_ISSUE_SHA256
    manifest["source_input_verification"].append(
        {
            "source_ordinal": 19,
            "source_relative_path": OLD_EXACT6_ISSUE_PATH.as_posix(),
            "tracked": True,
            "base_tree_blob": True,
            "filesystem_regular": True,
            "non_symlink": True,
            "expected_sha256": OLD_EXACT6_ISSUE_SHA256,
            "base_tree_sha256": OLD_EXACT6_ISSUE_SHA256,
            "filesystem_sha256": OLD_EXACT6_ISSUE_SHA256,
            "source_verified": True,
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = (*runtime.SOURCE_PATHS, OLD_EXACT6_ISSUE_PATH)
    sha = dict(runtime.SOURCE_SHA256)
    sha[OLD_EXACT6_ISSUE_PATH] = OLD_EXACT6_ISSUE_SHA256
    monkeypatch.setattr(runtime, "SOURCE_PATHS", paths)
    monkeypatch.setattr(runtime, "SOURCE_SHA256", sha)
    with pytest.raises(AssertionError, match="manifest semantic mismatch"):
        checker._validate_output_root(candidate, enforce_frozen_hashes=False)


def test_checker_rejects_synchronized_contract_header_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    candidate = tmp_path / "candidate"
    shutil.copytree(OUTPUT_ROOT, candidate)
    path = candidate / checker.CHECKER_CONTRACT_FILENAME
    header, rows = checker._csv(path)
    drifted_header = (*header, "synchronized_drift")
    for row in rows:
        row["synchronized_drift"] = "true"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=drifted_header, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    monkeypatch.setattr(runtime, "CONTRACT_COLUMNS", drifted_header)
    with pytest.raises(AssertionError, match="production CSV headers"):
        checker._validate_output_root(candidate, enforce_frozen_hashes=False)


def test_checker_rejects_authoritative_issue_path_reversion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    _, rows = checker._csv(OUTPUT_ROOT / checker.CHECKER_ISSUE_FILENAME)
    monkeypatch.setattr(runtime, "DESIGN_ISSUE_PATH", OLD_EXACT6_ISSUE_PATH)
    with pytest.raises(AssertionError, match="authoritative design issue path"):
        checker._validate_issue_rows(rows)


@pytest.mark.parametrize(
    "reference",
    (
        "runtime._truth_rows()",
        "runtime.EVALUATOR_REGISTRY",
        "runtime.admit007.evaluate_admit_007(x, y)",
        "runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design(x, y)",
        "runtime.SOURCE_PATHS",
        "runtime.SOURCE_SHA256",
        "runtime.CONTRACT_COLUMNS",
        "runtime.DESIGN_ISSUE_PATH",
    ),
)
def test_checker_ast_guard_rejects_production_dependency(reference: str) -> None:
    checker = _load_checker()
    injected = f"def _expected_truth_rows():\n    return {reference}\n"
    with pytest.raises(AssertionError, match="depends on production"):
        checker._assert_checker_independent_ast(injected)


@pytest.mark.parametrize(
    "reference",
    (
        "runtime.TRUE_READINESS",
        "runtime.FALSE_READINESS",
        "runtime.ADAPTER_IDS",
        "runtime.DISPATCH_ERROR_CODES",
        "runtime.RESULT_FIELDS",
        "runtime._manifest_payload({}, {})",
    ),
)
def test_checker_manifest_builder_ast_guard_rejects_production_dependency(
    reference: str,
) -> None:
    checker = _load_checker()
    injected = f"def _expected_manifest():\n    return {reference}\n"
    with pytest.raises(AssertionError, match="depends on production"):
        checker._assert_checker_independent_ast(injected)


def test_checker_protected_builder_inventory_is_complete() -> None:
    checker = _load_checker()
    assert {
        "_expected_source_boundary",
        "_expected_output_filenames",
        "_expected_headers",
        "_expected_readiness",
        "_expected_manifest",
        "_expected_issue_rows",
        "_expected_contract_rows",
        "_expected_truth_rows",
        "_expected_registry_rows",
        "_expected_safety_rows",
    } <= checker.PROTECTED_BUILDERS
    checker._assert_checker_independent_ast()


def test_runtime_public_call_graph_is_metadata_io_free() -> None:
    _load_checker()._check_public_call_graph()


def test_runtime_does_not_import_adapter_design_gate_or_heavy_dependencies() -> None:
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    import_section = source.split("PROJECT =", 1)[0]
    assert "admit_007_unified_adapter_contract_design_gate" not in import_section
    assert "torch" not in import_section
    assert "numpy" not in import_section
    assert "rdkit" not in import_section


def test_standalone_evaluator_does_not_call_design_oracle() -> None:
    tree = ast.parse(Path(runtime.admit007.__file__).read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate_admit_007"
    )
    calls = {
        node.func.attr
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "classify_admit_006_admit_007_evidence_design" not in calls


@pytest.mark.parametrize("target", ("runtime", "checker"))
def test_imports_are_silent_and_have_no_output_side_effect(
    tmp_path: Path,
    target: str,
) -> None:
    if target == "runtime":
        command = (
            "import covalent_ext."
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007"
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


def test_checker_passes_and_reports_exact_counts() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert "exact18_source_sha=18/18" in completed.stdout
    assert "registered_rule_count=7" in completed.stdout
    assert "contract_rows=56" in completed.stdout
    assert "truth_rows=107" in completed.stdout


def test_predecessor_exact6_source_and_outputs_match_frozen_sha() -> None:
    paths = (*runtime.SOURCE_PATHS[:6], OLD_EXACT6_ISSUE_PATH)
    expected = {
        **{path: runtime.SOURCE_SHA256[path] for path in runtime.SOURCE_PATHS[:6]},
        OLD_EXACT6_ISSUE_PATH: OLD_EXACT6_ISSUE_SHA256,
    }
    for path in paths:
        assert hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected[path]
