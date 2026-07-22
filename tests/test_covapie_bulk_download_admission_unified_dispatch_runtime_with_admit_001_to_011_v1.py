from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate
    as oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_011_rule_logic_interface as standalone,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011
    as runtime,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / runtime.DEFAULT_OUTPUT_ROOT
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py"
SCALAR = "data/raw/a.cif"
CONTRACT = oracle.DEFAULT_CONTRACT
SNAPSHOT = standalone._empty_snapshot()
RUNTIME_SOURCE_PATH = Path(runtime.__file__)
RUNTIME_SOURCE_BYTES = RUNTIME_SOURCE_PATH.read_bytes()


def checker_module():
    spec = importlib.util.spec_from_file_location("exact11_runtime_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def successor_copy(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    parent = repo / "src"
    parent.mkdir(parents=True)
    relative = Path("src/successor.py")
    target = repo / relative
    target.write_bytes(RUNTIME_SOURCE_BYTES)
    return repo, relative, target


def inject_dispatch_statement(source: str, statement: str) -> str:
    needle = '    """Evaluate exactly one registered rule without I/O or aggregation."""\n'
    assert source.count(needle) == 1
    return source.replace(needle, needle + statement, 1)


def legacy_direct_denylist_accepts(source: str) -> bool:
    """Model the superseded direct-name-only check for bypass assertions."""
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    closure = set(checker_module().RUNTIME_DEFINITION_NAMES)
    forbidden = {
        "Path", "open", "read", "read_bytes", "read_text", "stat", "lstat",
        "subprocess", "build_frozen_source_snapshot", "build_runtime_state",
        "_payloads", "_materialize_set", "evaluate_all_rules",
        "combined_candidate_verdict", "download", "checkpoint", "training",
    }
    return all(
        not {
            ast.unparse(call.func).split(".")[-1]
            for call in ast.walk(functions[name])
            if isinstance(call, ast.Call)
        } & forbidden
        for name in closure
    )


def output_tree_metadata(root: Path) -> dict[str, tuple[int, int, int, int, str]]:
    return {
        path.name: (
            path.stat().st_dev,
            path.stat().st_ino,
            path.stat().st_mode,
            path.stat().st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in root.iterdir()
    }


def route(candidate: object, **overrides: object):
    kwargs = {
        "batch_context": None,
        "evaluation_context": {
            runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT,
            runtime.ADMIT_011_CONTEXT_ITEMS[1]: SNAPSHOT,
        },
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return runtime.evaluate_admission_rule("ADMIT_011", candidate, **kwargs)


def snapshot(*paths: str) -> oracle.ExistingRawTargetRelativePathsSnapshot:
    return oracle.ExistingRawTargetRelativePathsSnapshot(
        "covapie_existing_raw_target_relative_paths_snapshot_v1",
        CONTRACT.canonical_raw_root_identity,
        CONTRACT.candidate_coordinate_system,
        CONTRACT.path_grammar_version,
        CONTRACT.equality_policy,
        CONTRACT.snapshot_phase,
        True,
        tuple(paths),
    )


class CountingMapping(Mapping):
    def __init__(self, values: dict[str, object], error: Exception | None = None) -> None:
        self.values = values
        self.error = error
        self.calls: list[object] = []
        self.iterated = False
        self.len_called = False
        self.get_called = False
        self.contains_called = False

    def __getitem__(self, key: object) -> object:
        self.calls.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]  # type: ignore[index]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.len_called = True
        return len(self.values)

    def get(self, key: object, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)


class CandidateBomb(Mapping):
    def __getitem__(self, key: object) -> object:
        raise AssertionError("candidate accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def copied_outputs(tmp_path: Path, name: str) -> Path:
    copied = tmp_path / name
    shutil.copytree(OUTPUT_ROOT, copied)
    return copied


def rewrite_csv_cell(
    copied: Path,
    filename: str,
    row_index: int,
    column: str,
    replacement: str,
) -> None:
    path = copied / filename
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    assert rows and column in header
    rows[row_index][column] = replacement
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = copied / runtime.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_stage_identity_and_fixed_baseline() -> None:
    assert runtime.PROJECT == "CovaPIE"
    assert runtime.STEP == "unified dispatch runtime with ADMIT_001 to ADMIT_011 v1"
    assert runtime.STAGE == "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1"
    assert runtime.EXPECTED_BASE_COMMIT == "fab48133058b826f5e9387c06d3cb0024657aec9"
    assert runtime.EXPECTED_BASE_SUBJECT == "add CovaPIE ADMIT_011 unified adapter contract design v1"
    assert runtime.MANIFEST_SCHEMA_VERSION == "covapie_unified_dispatch_runtime_with_admit_001_to_011_manifest_v1"
    assert runtime.RECOMMENDED_NEXT_STEP == "audit_covapie_admit_012_formal_evaluator_interface_preconditions_v1"


def test_public_types_and_constants_reused_by_identity() -> None:
    for name in (
        "UnifiedAdmissionRuleEvaluation", "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        assert getattr(runtime, name) is getattr(predecessor, name)


def test_exact11_registry_and_mapping_proxies() -> None:
    assert runtime.KNOWN_RULE_IDS == tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == tuple(f"ADMIT_{index:03d}" for index in range(1, 12))
    assert runtime.ADAPTER_READY_RULE_IDS == runtime.CALLABLE_DISCOVERED_RULE_IDS
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert type(runtime.RULE_NAMES) is MappingProxyType
    assert type(runtime.ADAPTER_IDS) is MappingProxyType
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == runtime.CALLABLE_DISCOVERED_RULE_IDS
    assert runtime.RULE_NAMES["ADMIT_011"] == "raw_overwrite_forbidden"
    assert runtime.ADAPTER_IDS["ADMIT_011"] == "covapie_admit_011_unified_adapter_v1"


def test_first_ten_handlers_are_reused_by_identity() -> None:
    assert all(
        runtime.EVALUATOR_REGISTRY[rule] is predecessor.EVALUATOR_REGISTRY[rule]
        for rule in runtime.KNOWN_RULE_IDS[:10]
    )
    assert runtime.EVALUATOR_REGISTRY["ADMIT_011"] is runtime._evaluate_registered_admit_011


def test_new_dispatcher_signature_and_local_registry_binding() -> None:
    assert runtime.evaluate_admission_rule is not predecessor.evaluate_admission_rule
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(predecessor.evaluate_admission_rule)
    assert runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is runtime.EVALUATOR_REGISTRY
    assert runtime.EVALUATOR_REGISTRY is not predecessor.EVALUATOR_REGISTRY


@pytest.mark.parametrize(
    ("rule_id", "code", "known"),
    (
        (type("StringSubclass", (str,), {})("ADMIT_011"), "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", False),
        *((f"ADMIT_{index:03d}", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True) for index in range(12, 16)),
    ),
)
def test_global_dispatch_precedence(rule_id: object, code: str, known: bool) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})  # type: ignore[arg-type]
    assert caught.value.code == code
    assert caught.value.known_rule is known
    assert caught.value.callable_discovered is False
    assert caught.value.adapter_ready is False


def test_admit011_is_registered_and_dispatches() -> None:
    result = route({"raw_target_relative_path": SCALAR})
    assert result.outcome == "passed" and result.reason == ""


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"batch_context": object()}, "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": None}, "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": object()}, "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED"),
        ({"evaluation_context": {runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT}}, "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_context_failures_are_exact_and_precede_candidate(
    overrides: dict[str, object], reason: str,
) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        route(CandidateBomb(), **overrides)
    assert tuple(getattr(caught.value, name) for name in runtime.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "ADMIT_011", True, True, True, reason,
    )


def test_context_precedence_is_exact_six_gate_order() -> None:
    cases = (
        ({"batch_context": object(), "evaluation_context": object(), "download_result_context": object(), "stage_authorization_context": object()}, "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": object(), "download_result_context": object(), "stage_authorization_context": object()}, "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}, "download_result_context": object(), "stage_authorization_context": object()}, "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED"),
        ({"evaluation_context": {runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT}, "download_result_context": object(), "stage_authorization_context": object()}, "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED"),
        ({"download_result_context": object(), "stage_authorization_context": object()}, "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    )
    for overrides, reason in cases:
        with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
            route(CandidateBomb(), **overrides)
        assert caught.value.reason == reason


def test_mapping_subclasses_extra_keys_and_exact_single_lookups() -> None:
    candidate = CountingMapping({"raw_target_relative_path": SCALAR, "extra": object()})
    context = CountingMapping({
        runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT,
        runtime.ADMIT_011_CONTEXT_ITEMS[1]: SNAPSHOT,
        "extra": object(),
    })
    result = route(candidate, evaluation_context=context)
    assert result.outcome == "passed"
    assert candidate.calls == ["raw_target_relative_path"]
    assert context.calls == list(runtime.ADMIT_011_CONTEXT_ITEMS)
    assert not any((candidate.iterated, context.iterated, candidate.len_called, context.len_called,
                    candidate.get_called, context.get_called, candidate.contains_called, context.contains_called))


@pytest.mark.parametrize("location", ("contract", "snapshot", "candidate"))
def test_non_key_error_lookup_propagates_same_exception(location: str) -> None:
    sentinel = RuntimeError(location)
    context = {
        runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT,
        runtime.ADMIT_011_CONTEXT_ITEMS[1]: SNAPSHOT,
    }
    candidate: object = {}
    evaluation: object = context
    if location == "contract":
        evaluation = CountingMapping({}, sentinel)
    elif location == "snapshot":
        evaluation = CountingMapping({runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT}, sentinel)
    else:
        candidate = CountingMapping({}, sentinel)
    with pytest.raises(RuntimeError) as caught:
        route(candidate, evaluation_context=evaluation)
    assert caught.value is sentinel


@pytest.mark.parametrize(
    ("candidate", "reason"),
    (
        (object(), "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "raw_target_relative_path_missing"),
    ),
)
def test_candidate_invalid_exact13_without_calls(
    candidate: object, reason: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(standalone, "evaluate_admit_011", lambda *_: calls.append("formal"))
    monkeypatch.setattr(oracle, "classify_admit_011_raw_target_relative_path_design", lambda *_: calls.append("oracle"))
    result = route(candidate)
    assert tuple(getattr(result, name) for name in runtime.RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION, "ADMIT_011", "raw_overwrite_forbidden",
        "invalid", False, True, reason, (), (), ("raw_target_relative_path",),
        runtime.ADMIT_011_CONTEXT_ITEMS, False, "covapie_admit_011_unified_adapter_v1",
    )
    assert calls == []


@pytest.mark.parametrize(
    "scalar",
    (None, "", "docs/a", "data/raw/a/", type("StringSubclass", (str,), {})(SCALAR), SCALAR),
)
def test_present_scalar_is_forwarded_without_adapter_grammar(
    scalar: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[object] = []
    original = standalone.evaluate_admit_011

    def formal(value: object, snapshot_object: object, contract_object: object):
        seen.append(value)
        return original(value, snapshot_object, contract_object)

    monkeypatch.setattr(standalone, "evaluate_admit_011", formal)
    route({"raw_target_relative_path": scalar})
    assert seen == [scalar] and seen[0] is scalar


def test_formal_oracle_order_identity_and_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    scalar = object()
    snapshot_object = object()
    contract_object = object()
    calls: list[tuple[str, tuple[object, ...]]] = []
    formal_original = standalone.evaluate_admit_011
    oracle_original = oracle.classify_admit_011_raw_target_relative_path_design

    def formal(*args: object):
        calls.append(("formal", args))
        return formal_original(*args)

    def classify(*args: object):
        calls.append(("oracle", args))
        return oracle_original(*args)

    monkeypatch.setattr(standalone, "evaluate_admit_011", formal)
    monkeypatch.setattr(oracle, "classify_admit_011_raw_target_relative_path_design", classify)
    result = route(
        {"raw_target_relative_path": scalar},
        evaluation_context={
            runtime.ADMIT_011_CONTEXT_ITEMS[0]: contract_object,
            runtime.ADMIT_011_CONTEXT_ITEMS[1]: snapshot_object,
        },
    )
    assert result.reason == "RAW_TARGET_RELATIVE_PATH_TYPE_INVALID"
    assert [name for name, _ in calls] == ["formal", "oracle"]
    expected = (scalar, snapshot_object, contract_object)
    assert all(all(left is right for left, right in zip(args, expected, strict=True)) for _, args in calls)


def test_formal_exception_propagates_and_prevents_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = RuntimeError("formal sentinel")
    oracle_calls = 0

    def classify(*args: object):
        nonlocal oracle_calls
        oracle_calls += 1

    monkeypatch.setattr(standalone, "evaluate_admit_011", lambda *_: (_ for _ in ()).throw(sentinel))
    monkeypatch.setattr(oracle, "classify_admit_011_raw_target_relative_path_design", classify)
    with pytest.raises(RuntimeError) as caught:
        route({"raw_target_relative_path": SCALAR})
    assert caught.value is sentinel and oracle_calls == 0


def test_source_wrong_type_and_subclass_fail_before_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    source = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    class ResultSubclass(type(source)):
        pass
    subclass = object.__new__(ResultSubclass)
    for name in standalone.RESULT_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    for bad in (object(), {}, subclass):
        oracle_calls = []
        with monkeypatch.context() as patch:
            patch.setattr(standalone, "evaluate_admit_011", lambda *_args, value=bad: value)
            patch.setattr(oracle, "classify_admit_011_raw_target_relative_path_design", lambda *args: oracle_calls.append(args))
            with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
                route({"raw_target_relative_path": SCALAR})
        assert caught.value.reason == "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        assert caught.value.adapter_ready is False and oracle_calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("evaluator_io_used", True),
        ("admission_rule_id", "ADMIT_999"),
        ("passed", False),
        ("validated_candidate_fields", ()),
        ("consumed_candidate_fields", ()),
        ("consumed_context_items", ()),
        ("reason", "RAW_TARGET_RELATIVE_PATH_EMPTY"),
    ),
)
def test_source_invariant_tamper_fails_before_oracle(
    field: str, value: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    object.__setattr__(source, field, value)
    oracle_calls = []
    monkeypatch.setattr(standalone, "evaluate_admit_011", lambda *_: source)
    monkeypatch.setattr(oracle, "classify_admit_011_raw_target_relative_path_design", lambda *args: oracle_calls.append(args))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        route({"raw_target_relative_path": SCALAR})
    assert caught.value.reason == "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert oracle_calls == []


def test_source_storage_order_extra_storage_and_exact_type_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    values = []
    reordered = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    first = standalone.RESULT_FIELDS[0]
    saved = vars(reordered).pop(first)
    vars(reordered)[first] = saved
    values.append(reordered)
    extra = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    object.__setattr__(extra, "extra", "drift")
    values.append(extra)
    typed = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    object.__setattr__(typed, "passed", 1)
    values.append(typed)
    for bad in values:
        with monkeypatch.context() as patch:
            patch.setattr(standalone, "evaluate_admit_011", lambda *_args, value=bad: value)
            with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
                route({"raw_target_relative_path": SCALAR})
        assert caught.value.reason == "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


def test_source_dataclass_field_order_drift_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    source = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    monkeypatch.setattr(standalone, "evaluate_admit_011", lambda *_: source)
    monkeypatch.setattr(runtime, "fields", lambda _type: tuple(reversed(fields(standalone.Admit011EvaluationResult))))
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        route({"raw_target_relative_path": SCALAR})
    assert caught.value.reason == "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


@pytest.mark.parametrize("mode", ("exception", "wrong_type", "storage", "type_drift", "mismatch"))
def test_oracle_failures_convert_to_adapter_not_ready(
    mode: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    if mode == "exception":
        replacement = lambda *_: (_ for _ in ()).throw(RuntimeError("oracle"))
    elif mode == "wrong_type":
        replacement = lambda *_: standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    else:
        design = oracle.classify_admit_011_raw_target_relative_path_design(SCALAR, SNAPSHOT, CONTRACT)
        if mode == "storage":
            first = standalone.RESULT_FIELDS[0]
            saved = vars(design).pop(first)
            vars(design)[first] = saved
        elif mode == "type_drift":
            object.__setattr__(design, "passed", 1)
        else:
            design = oracle.classify_admit_011_raw_target_relative_path_design("docs/a", SNAPSHOT, CONTRACT)
        replacement = lambda *_args, value=design: value
    monkeypatch.setattr(oracle, "classify_admit_011_raw_target_relative_path_design", replacement)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        route({"raw_target_relative_path": SCALAR})
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert caught.value.reason == "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert caught.value.adapter_ready is False


def test_full_exact10_value_and_exact_type_equality() -> None:
    source = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    expected = runtime._expected_admit011_from_oracle(SCALAR, SNAPSHOT, CONTRACT)
    runtime._validate_admit011_oracle_equivalence(source, expected)
    mismatch = standalone.evaluate_admit_011("docs/a", SNAPSHOT, CONTRACT)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError):
        runtime._validate_admit011_oracle_equivalence(source, mismatch)


@pytest.mark.parametrize(
    ("scalar", "snapshot_object", "outcome", "reason"),
    (
        (SCALAR, SNAPSHOT, "passed", ""),
        (SCALAR, snapshot(SCALAR), "blocked", "RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED"),
        ("docs/a", SNAPSHOT, "invalid", "RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN"),
        (SCALAR, object(), "invalid", "EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_TYPE_INVALID"),
    ),
)
def test_exact13_projection_passed_blocked_invalid(
    scalar: object, snapshot_object: object, outcome: str, reason: str,
) -> None:
    result = route(
        {"raw_target_relative_path": scalar},
        evaluation_context={
            runtime.ADMIT_011_CONTEXT_ITEMS[0]: CONTRACT,
            runtime.ADMIT_011_CONTEXT_ITEMS[1]: snapshot_object,
        },
    )
    source = standalone.evaluate_admit_011(scalar, snapshot_object, CONTRACT)
    assert result.outcome == outcome and result.reason == reason
    assert result.normalized_values == result.validated_candidate_fields == source.validated_candidate_fields
    assert result.consumed_candidate_fields == source.consumed_candidate_fields
    assert result.consumed_context_items == source.consumed_context_items
    assert result.evaluator_io_used is False and result.adapter_id == runtime.ADAPTER_ID


def test_exact84_exact47_public_runtime_full_projection() -> None:
    truth_path = ROOT / runtime.STANDALONE_TRUTH_PATH
    with truth_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 84
    assert sum(row["case_id"].startswith("HIST_") for row in rows) == 47
    for row in rows:
        scalar = ast.literal_eval(row["candidate_representation"])
        contract, snapshot_object = standalone._case_context(row)
        result = route(
            {"raw_target_relative_path": scalar},
            evaluation_context={
                runtime.ADMIT_011_CONTEXT_ITEMS[0]: contract,
                runtime.ADMIT_011_CONTEXT_ITEMS[1]: snapshot_object,
            },
        )
        validated = tuple(tuple(pair) for pair in json.loads(row["validated_candidate_fields"]))
        assert tuple(getattr(result, name) for name in runtime.RESULT_FIELDS) == (
            runtime.RESULT_SCHEMA_VERSION, "ADMIT_011", "raw_overwrite_forbidden",
            row["outcome"], row["passed"] == "true", row["blocks_candidate"] == "true",
            row["reason"], validated, validated,
            tuple(json.loads(row["consumed_candidate_fields"])),
            tuple(json.loads(row["consumed_context_items"])),
            False, "covapie_admit_011_unified_adapter_v1",
        )


def test_first_ten_default_dispatch_parity() -> None:
    def observe(module: object, rule: str):
        try:
            value = module.evaluate_admission_rule(rule, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            return "error", tuple(getattr(error, name) for name in runtime.DISPATCH_ERROR_FIELDS)
        return "result", tuple(getattr(value, name) for name in runtime.RESULT_FIELDS)
    for rule in runtime.KNOWN_RULE_IDS[:10]:
        assert observe(runtime, rule) == observe(predecessor, rule)


def test_source_boundary_exact23_triple_sha_and_pinned_shape() -> None:
    value = runtime.build_frozen_source_snapshot(ROOT)
    assert runtime.validate_frozen_source_snapshot(value)
    assert len(value.records) == 23
    assert tuple(record.relative_path for record in value.records) == runtime.SOURCE_PATHS
    assert all(record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256 for record in value.records)


def test_runtime_state_counts_registry_issue_and_readiness() -> None:
    state = runtime.build_runtime_state(runtime.build_frozen_source_snapshot(ROOT))
    assert tuple(map(len, (state["contract_rows"], state["truth_rows"], state["registry_rows"], state["safety_rows"], state["issue_rows"]))) == (36, 534, 15, 35, 11)
    assert state["truth_group_counts"]["admit011_standalone_exact84"] == 84
    issue = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issue["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] == "resolved"
    assert issue["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    assert issue["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["integration_transition"] == "admit_011_implemented_and_removed_from_open_coverage_scope"
    assert issue["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open"


def test_manifest_required_readiness_and_stop_boundaries() -> None:
    manifest = json.loads((OUTPUT_ROOT / runtime.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert all(manifest[key] is True and manifest["readiness"][key] is True for key in runtime.TRUE_READINESS)
    assert all(manifest[key] is False and manifest["readiness"][key] is False for key in runtime.FALSE_READINESS)
    assert manifest["adapter_design_gate_imported_by_runtime"] is False
    assert manifest["step12d_is_final_training_feature_contract"] is False
    assert manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"


def test_public_call_graph_is_pure_and_design_gate_not_imported() -> None:
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.extend(alias.name for alias in node.names)
    assert not any("admit_011_unified_adapter_contract_design_gate" in name for name in imports)
    assert "evaluate_all_rules" not in runtime.__dict__
    assert "combined_candidate_verdict" not in runtime.__dict__
    checker = checker_module()
    attested = checker._attest_successor_source_before_import()
    checker._verify_runtime_ast(attested)


def test_successor_preimport_attestation_ast_and_imported_binding_provenance() -> None:
    checker = checker_module()
    records = checker._verify_sources()
    attested = checker._attest_successor_source_before_import()
    assert attested["path"] == RUNTIME_SOURCE_PATH
    assert attested["sha256"] == checker.EXPECTED_SUCCESSOR_SOURCE_SHA256
    assert attested["pinned_fd_read"] is True
    checker._verify_runtime_ast(attested)
    checker._verify_imported_successor(runtime, attested, records)
    assert tuple(checker.EXPECTED_RUNTIME_DEFINITION_AST_SHA256) == checker.RUNTIME_DEFINITION_NAMES
    assert len(checker.PROTECTED_RUNTIME_BINDINGS) == 34


def test_checker_module_import_is_silent_standard_library_only_and_project_free(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "marker"
    script = (
        "import importlib.util,sys;"
        "before={n for n in sys.modules if n=='covalent_ext' or n.startswith('covalent_ext.')};"
        f"s=importlib.util.spec_from_file_location('isolated_checker',{str(CHECKER_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "after={n for n in sys.modules if n=='covalent_ext' or n.startswith('covalent_ext.')};"
        "assert before==after==set()"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", script),
        cwd=ROOT,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "MARKER": str(marker)},
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""
    assert not marker.exists()


def test_successor_sha_drift_stops_main_before_import_and_output_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = checker_module()
    calls: list[str] = []
    monkeypatch.setattr(checker, "_verify_sources", lambda: ())
    monkeypatch.setattr(
        checker,
        "_attest_successor_source_before_import",
        lambda: (_ for _ in ()).throw(AssertionError("successor source SHA mismatch")),
    )
    monkeypatch.setattr(checker.importlib, "import_module", lambda *_: calls.append("import"))
    monkeypatch.setattr(checker, "_output_bytes", lambda *_args, **_kwargs: calls.append("output"))
    with pytest.raises(AssertionError, match="SHA mismatch"):
        checker.main()
    assert calls == []


def test_module_level_marker_source_is_rejected_by_sha_before_execution(
    tmp_path: Path,
) -> None:
    checker = checker_module()
    repo, relative, target = successor_copy(tmp_path)
    marker = tmp_path / "marker"
    target.write_bytes(
        RUNTIME_SOURCE_BYTES
        + f"\nopen({str(marker)!r}, 'w').write('owned')\n".encode("utf-8")
    )
    with pytest.raises(AssertionError, match="SHA mismatch"):
        checker._attest_successor_source_before_import(
            repo, relative_path=relative,
        )
    assert not marker.exists()


@pytest.mark.parametrize("kind", ("leaf_symlink", "parent_symlink"))
def test_successor_attestation_rejects_leaf_and_parent_symlinks(
    tmp_path: Path,
    kind: str,
) -> None:
    checker = checker_module()
    if kind == "leaf_symlink":
        repo = tmp_path / "repo"
        parent = repo / "src"
        parent.mkdir(parents=True)
        real = tmp_path / "real.py"
        real.write_bytes(RUNTIME_SOURCE_BYTES)
        target = parent / "successor.py"
        target.symlink_to(real)
        relative = Path("src/successor.py")
    else:
        repo = tmp_path / "repo"
        repo.mkdir()
        real_parent = tmp_path / "real_parent"
        real_parent.mkdir()
        (real_parent / "successor.py").write_bytes(RUNTIME_SOURCE_BYTES)
        (repo / "linked").symlink_to(real_parent, target_is_directory=True)
        relative = Path("linked/successor.py")
    imports: list[str] = []
    with pytest.raises((AssertionError, OSError)):
        attested = checker._attest_successor_source_before_import(
            repo, relative_path=relative,
        )
        checker._import_attested_successor(
            attested, (), importer=lambda *_: imports.append("import")
        )
    assert imports == []


def test_imported_successor_file_must_equal_attested_path(tmp_path: Path) -> None:
    checker = checker_module()
    repo, relative, _ = successor_copy(tmp_path)
    attested = checker._attest_successor_source_before_import(
        repo, relative_path=relative,
    )
    wrong = tmp_path / "wrong.py"
    wrong.write_bytes(RUNTIME_SOURCE_BYTES)

    class Spec:
        origin = str(wrong)

    class FakeModule:
        __file__ = str(wrong)
        __spec__ = Spec()

    with pytest.raises(AssertionError, match="path mismatch"):
        checker._verify_imported_successor(FakeModule(), attested)


def test_attestation_to_import_inode_replacement_rejected_before_import(
    tmp_path: Path,
) -> None:
    checker = checker_module()
    repo, relative, target = successor_copy(tmp_path)
    attested = checker._attest_successor_source_before_import(
        repo, relative_path=relative,
    )
    calls: list[str] = []

    def replace() -> None:
        replacement = target.with_suffix(".replacement")
        replacement.write_bytes(RUNTIME_SOURCE_BYTES)
        os.replace(replacement, target)

    with pytest.raises(AssertionError, match="identity changed"):
        checker._import_attested_successor(
            attested,
            (),
            importer=lambda *_: calls.append("import"),
            before_import_hook=replace,
        )
    assert calls == []


def test_import_to_postcheck_byte_replacement_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = checker_module()
    repo, relative, target = successor_copy(tmp_path)
    attested = checker._attest_successor_source_before_import(
        repo, relative_path=relative,
    )

    class Spec:
        origin = str(target)

    class FakeModule:
        __file__ = str(target)
        __spec__ = Spec()

    fake = FakeModule()
    monkeypatch.setitem(sys.modules, checker.MODULE, fake)

    def importer(_name: str):
        replacement = target.with_suffix(".replacement")
        replacement.write_bytes(RUNTIME_SOURCE_BYTES + b"\n# replaced\n")
        os.replace(replacement, target)
        return fake

    with pytest.raises(AssertionError, match="identity changed|bytes changed"):
        checker._import_attested_successor(attested, (), importer=importer)


def test_transitive_evil_helper_bypass_is_rejected_without_execution(
    tmp_path: Path,
) -> None:
    checker = checker_module()
    marker = tmp_path / "marker"
    source = inject_dispatch_statement(
        RUNTIME_SOURCE_BYTES.decode("utf-8"),
        "    _evil_helper()\n",
    )
    source += f"\n\ndef _evil_helper():\n    open({str(marker)!r}, 'w').write('x')\n"
    assert legacy_direct_denylist_accepts(source)
    with pytest.raises(AssertionError, match="unknown local/dynamic callable"):
        checker._verify_runtime_ast(source.encode("utf-8"))
    assert not marker.exists()


@pytest.mark.parametrize(
    "terminal",
    (
        "open('/tmp/exact11-revised1-marker', 'w').write('x')",
        "__import__('socket').socket()",
        "__import__('subprocess').run(('false',))",
    ),
)
def test_two_level_indirect_helper_bypass_is_rejected(terminal: str) -> None:
    checker = checker_module()
    source = inject_dispatch_statement(
        RUNTIME_SOURCE_BYTES.decode("utf-8"),
        "    _helper_a()\n",
    )
    source += f"\n\ndef _helper_a():\n    _helper_b()\n\ndef _helper_b():\n    {terminal}\n"
    assert legacy_direct_denylist_accepts(source)
    with pytest.raises(AssertionError, match="unknown local/dynamic callable"):
        checker._verify_runtime_ast(source.encode("utf-8"))


def test_module_rebinding_bypass_is_rejected_without_execution(tmp_path: Path) -> None:
    checker = checker_module()
    marker = tmp_path / "marker"
    source = RUNTIME_SOURCE_BYTES.decode("utf-8") + (
        "\n_ORIGINAL = _admit011_candidate_invalid\n"
        "_admit011_candidate_invalid = lambda reason: (\n"
        f"    open({str(marker)!r}, 'w').write('x'),\n"
        "    _ORIGINAL(reason),\n"
        ")[1]\n"
    )
    assert legacy_direct_denylist_accepts(source)
    with pytest.raises(AssertionError, match="protected runtime binding"):
        checker._verify_runtime_ast(source.encode("utf-8"))
    assert not marker.exists()


@pytest.mark.parametrize(
    "name",
    ("admit011", "admit011_oracle", "fields", "Mapping", "EVALUATOR_REGISTRY"),
)
def test_protected_runtime_module_rebindings_are_rejected(name: str) -> None:
    source = RUNTIME_SOURCE_BYTES + f"\n{name} = object()\n".encode("utf-8")
    with pytest.raises(AssertionError, match="protected runtime binding"):
        checker_module()._verify_runtime_ast(source)


@pytest.mark.parametrize("module_name", ("socket", "pathlib", "subprocess"))
def test_local_imports_in_public_closure_are_rejected(module_name: str) -> None:
    source = inject_dispatch_statement(
        RUNTIME_SOURCE_BYTES.decode("utf-8"),
        f"    import {module_name}\n",
    )
    with pytest.raises(AssertionError, match="nested import"):
        checker_module()._verify_runtime_ast(source.encode("utf-8"))


def test_static_policy_rejects_module_import_time_expression_and_decorator(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "marker"
    checker = checker_module()
    base = RUNTIME_SOURCE_BYTES.decode("utf-8")
    variants = (
        base + f"\nopen({str(marker)!r}, 'w').write('x')\n",
        base + (
            f"\n@open({str(marker)!r}, 'w').write('x')\n"
            "def _decorated_side_effect():\n    pass\n"
        ),
    )
    for source in variants:
        with pytest.raises(AssertionError, match="import-time expression|decorator"):
            checker._verify_runtime_ast(source.encode("utf-8"))
    assert not marker.exists()


def test_subscript_callable_bypass_is_rejected() -> None:
    source = inject_dispatch_statement(
        RUNTIME_SOURCE_BYTES.decode("utf-8"),
        "    builtins.__dict__['open']('/tmp/exact11-revised1-marker', 'w')\n",
    )
    with pytest.raises(AssertionError, match="subscript callable"):
        checker_module()._verify_runtime_ast(source.encode("utf-8"))


@pytest.mark.parametrize(
    "statement",
    (
        "    object.__subclasses__()\n",
        "    object.__getattribute__(object(), '__class__')\n",
    ),
)
def test_object_dunder_discovery_calls_are_rejected(statement: str) -> None:
    source = inject_dispatch_statement(RUNTIME_SOURCE_BYTES.decode("utf-8"), statement)
    with pytest.raises(AssertionError, match="imported/module callable forbidden"):
        checker_module()._verify_runtime_ast(source.encode("utf-8"))


@pytest.mark.parametrize(
    "statement",
    (
        "    (lambda: None)()\n",
        "    getattr(object(), '__class__')()\n",
        "    eval('1')\n",
        "    exec('pass')\n",
        "    compile('1', '<x>', 'eval')\n",
        "    __import__('socket')\n",
        "    setattr(candidate_record, 'x', 1)\n",
        "    delattr(candidate_record, 'x')\n",
        "    candidate_record.value = 1\n",
        "    candidate_record['x'] = 1\n",
        "    global EVALUATOR_REGISTRY\n",
        "    with open('/tmp/exact11-revised1-marker', 'w'):\n        pass\n",
    ),
)
def test_closed_world_dynamic_call_and_mutation_surfaces_are_rejected(
    statement: str,
) -> None:
    source = inject_dispatch_statement(RUNTIME_SOURCE_BYTES.decode("utf-8"), statement)
    with pytest.raises(AssertionError):
        checker_module()._verify_runtime_ast(source.encode("utf-8"))


def test_exact_six_outputs_and_checker_owned_full_semantics() -> None:
    checker = checker_module()
    assert checker._validate_output_tree() == checker.FROZEN_OUTPUT_SHA256
    assert {path.name for path in OUTPUT_ROOT.iterdir()} == set(runtime.OUTPUT_FILES)


@pytest.mark.parametrize(
    "kind",
    (
        "parent_symlink", "root_symlink", "broken_root_symlink", "root_file",
        "root_fifo", "unexpected", "missing_leaf", "leaf_symlink",
        "leaf_directory", "leaf_fifo",
    ),
)
def test_checker_pinned_output_preflight_rejects_unsafe_structures(
    tmp_path: Path,
    kind: str,
) -> None:
    checker = checker_module()
    if kind == "parent_symlink":
        real_parent = tmp_path / "real_parent"
        real_parent.mkdir()
        shutil.copytree(OUTPUT_ROOT, real_parent / "evidence")
        linked_parent = tmp_path / "linked_parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        output = linked_parent / "evidence"
    else:
        output = tmp_path / "evidence"
        if kind == "root_symlink":
            real = tmp_path / "real"
            shutil.copytree(OUTPUT_ROOT, real)
            output.symlink_to(real, target_is_directory=True)
        elif kind == "broken_root_symlink":
            output.symlink_to(tmp_path / "missing", target_is_directory=True)
        elif kind == "root_file":
            output.write_bytes(b"file")
        elif kind == "root_fifo":
            os.mkfifo(output)
        else:
            shutil.copytree(OUTPUT_ROOT, output)
            leaf = output / runtime.CONTRACT_FILENAME
            if kind == "unexpected":
                (output / "unexpected").write_bytes(b"x")
            elif kind == "missing_leaf":
                leaf.unlink()
            elif kind == "leaf_symlink":
                leaf.unlink()
                leaf.symlink_to(output / runtime.TRUTH_FILENAME)
            elif kind == "leaf_directory":
                leaf.unlink()
                leaf.mkdir()
            else:
                leaf.unlink()
                os.mkfifo(leaf)
    with pytest.raises((AssertionError, OSError)):
        checker._output_bytes(output)


def test_checker_pinned_output_normal_read_has_no_filesystem_mutation(
    tmp_path: Path,
) -> None:
    checker = checker_module()
    output = copied_outputs(tmp_path, "normal")
    before = output_tree_metadata(output)
    contents = checker._output_bytes(output)
    after = output_tree_metadata(output)
    assert tuple(contents) == checker.OUTPUTS
    assert contents == {name: (output / name).read_bytes() for name in checker.OUTPUTS}
    assert before == after


def test_checker_rejects_root_replacement_after_output_preflight(tmp_path: Path) -> None:
    checker = checker_module()
    output = copied_outputs(tmp_path, "root_race")
    moved = tmp_path / "moved_root"
    fired = False

    def hook(event: str, **_details: object) -> None:
        nonlocal fired
        if event == "after_preflight" and not fired:
            fired = True
            output.rename(moved)
            output.mkdir()

    with pytest.raises(AssertionError, match="root identity"):
        checker._output_bytes(output, event_hook=hook)
    assert fired


@pytest.mark.parametrize("phase", ("before_leaf_open", "during_leaf_read"))
def test_checker_rejects_leaf_replacement_across_stat_open_and_read(
    tmp_path: Path,
    phase: str,
) -> None:
    checker = checker_module()
    output = copied_outputs(tmp_path, phase)
    replacement = tmp_path / f"{phase}.replacement"
    target_name = runtime.CONTRACT_FILENAME
    replacement.write_bytes((output / target_name).read_bytes())
    fired = False

    def hook(event: str, **details: object) -> None:
        nonlocal fired
        if event == phase and details.get("name") == target_name and not fired:
            fired = True
            os.replace(replacement, output / target_name)

    with pytest.raises(AssertionError, match="leaf descriptor identity|leaf changed during read"):
        checker._output_bytes(output, event_hook=hook)
    assert fired


def test_checker_rejects_parent_inode_change_during_output_read(tmp_path: Path) -> None:
    checker = checker_module()
    parent = tmp_path / "parent"
    parent.mkdir()
    output = parent / "evidence"
    shutil.copytree(OUTPUT_ROOT, output)
    moved = tmp_path / "moved_parent"
    fired = False

    def hook(event: str, **_details: object) -> None:
        nonlocal fired
        if event == "before_final_validation" and not fired:
            fired = True
            parent.rename(moved)
            parent.mkdir()

    with pytest.raises((AssertionError, OSError)):
        checker._output_bytes(output, event_hook=hook)
    assert fired


def test_checker_rejects_inventory_change_after_all_leaf_reads(tmp_path: Path) -> None:
    checker = checker_module()
    output = copied_outputs(tmp_path, "inventory_race")
    fired = False

    def hook(event: str, **_details: object) -> None:
        nonlocal fired
        if event == "before_final_validation" and not fired:
            fired = True
            (output / "unexpected").write_bytes(b"x")

    with pytest.raises(AssertionError, match="inventory changed"):
        checker._output_bytes(output, event_hook=hook)
    assert fired


def test_double_materialization_and_inode_preserving_noop(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(first, repo_root=ROOT)
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(second, repo_root=ROOT)
    first_bytes = {name: (first / name).read_bytes() for name in runtime.OUTPUT_FILES}
    second_bytes = {name: (second / name).read_bytes() for name in runtime.OUTPUT_FILES}
    assert first_bytes == second_bytes
    before = {name: (first / name).stat().st_ino for name in runtime.OUTPUT_FILES}
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(first, repo_root=ROOT)
    assert before == {name: (first / name).stat().st_ino for name in runtime.OUTPUT_FILES}
    assert not tuple(tmp_path.rglob("*.tmp")) and not tuple(tmp_path.rglob("*.part"))


def test_existing_output_mismatch_fails_without_repair(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(output, repo_root=ROOT)
    target = output / runtime.CONTRACT_FILENAME
    target.write_bytes(b"tampered\n")
    before = {name: (output / name).read_bytes() for name in runtime.OUTPUT_FILES}
    with pytest.raises(ValueError, match="repair forbidden"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(output, repo_root=ROOT)
    assert before == {name: (output / name).read_bytes() for name in runtime.OUTPUT_FILES}


@pytest.mark.parametrize("kind", ("root_symlink", "root_file", "unexpected", "leaf_symlink"))
def test_materializer_preflight_rejects_unsafe_output_before_source_read(
    tmp_path: Path, kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "evidence"
    if kind == "root_symlink":
        target = tmp_path / "target"; target.mkdir(); output.symlink_to(target, target_is_directory=True)
    elif kind == "root_file":
        output.write_text("x", encoding="utf-8")
    else:
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(output, repo_root=ROOT)
        if kind == "unexpected":
            (output / "unexpected").write_text("x", encoding="utf-8")
        else:
            leaf = output / runtime.CONTRACT_FILENAME
            leaf.unlink(); leaf.symlink_to(output / runtime.TRUTH_FILENAME)
    called = False
    def bomb(*args: object, **kwargs: object):
        nonlocal called
        called = True
        raise AssertionError("source read")
    monkeypatch.setattr(runtime, "build_frozen_source_snapshot", bomb)
    with pytest.raises(ValueError):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(output, repo_root=ROOT)
    assert called is False


def test_materializer_source_failure_leaves_missing_target_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "missing"
    sentinel = ValueError("source sentinel")
    monkeypatch.setattr(runtime, "build_frozen_source_snapshot", lambda *_args, **_kwargs: (_ for _ in ()).throw(sentinel))
    with pytest.raises(ValueError) as caught:
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(output, repo_root=ROOT)
    assert caught.value is sentinel and not output.exists()
    assert not tuple(tmp_path.glob(".exact11-runtime-stage-*"))


def test_cleanup_does_not_delete_unknown_staging_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "evidence"
    injected = False
    def verify_with_unknown(fd: int, payloads: Mapping[str, bytes]) -> None:
        nonlocal injected
        if not injected:
            injected = True
            unknown = os.open("unknown", runtime.WRITE_FILE_FLAGS, 0o600, dir_fd=fd)
            os.close(unknown)
            raise RuntimeError("injected failure")
        raise AssertionError("unexpected second verification")
    monkeypatch.setattr(runtime, "_verify_complete_set", verify_with_unknown)
    with pytest.raises(RuntimeError, match="injected failure"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(output, repo_root=ROOT)
    staging = tuple(tmp_path.glob(".exact11-runtime-stage-*"))
    assert len(staging) == 1 and (staging[0] / "unknown").is_file()


@pytest.mark.parametrize(
    ("filename", "row_index", "column"),
    (
        (runtime.CONTRACT_FILENAME, 0, "contract_subject"),
        (runtime.TRUTH_FILENAME, 0, "behavior"),
        (runtime.REGISTRY_FILENAME, 10, "handler_identity_status"),
        (runtime.SAFETY_FILENAME, 0, "observed_executed"),
        (runtime.ISSUE_FILENAME, 0, "status"),
    ),
)
def test_checker_rejects_synchronized_csv_semantic_tamper(
    tmp_path: Path, filename: str, row_index: int, column: str,
) -> None:
    copied = copied_outputs(tmp_path, filename)
    rewrite_csv_cell(copied, filename, row_index, column, "tampered")
    with pytest.raises(AssertionError, match="semantic|registry|issue|safety|truth"):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "mutation",
    ("project", "readiness", "source", "output_sha", "unknown", "admit012", "training"),
)
def test_checker_rejects_manifest_semantic_tamper(tmp_path: Path, mutation: str) -> None:
    copied = copied_outputs(tmp_path, mutation)
    path = copied / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "project":
        manifest["project"] = "tampered"
    elif mutation == "readiness":
        manifest["readiness"][runtime.TRUE_READINESS[0]] = False
    elif mutation == "source":
        manifest["source_input_verification"][0]["tracked"] = False
    elif mutation == "output_sha":
        manifest["output_sha256"][runtime.CONTRACT_FILENAME] = "0" * 64
    elif mutation == "unknown":
        manifest["unknown"] = True
    elif mutation == "admit012":
        manifest["admit_012_started"] = True
    else:
        manifest["ready_for_training"] = True
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="manifest"):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_import_has_only_standard_library_before_main() -> None:
    source = CHECKER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported.add(node.module.split(".")[0])
            imported.update(alias.name.split(".")[0] for alias in node.names)
    assert "covalent_ext" not in imported
    main_source = ast.get_source_segment(source, next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"))
    assert main_source is not None
    assert main_source.index("_verify_sources()") < main_source.index("_attest_successor_source_before_import()")
    assert main_source.index("_attest_successor_source_before_import()") < main_source.index("_import_attested_successor(")
    assert "importlib.reload" not in main_source


def test_malicious_derived_representation_is_not_executed(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    expression = f"__import__('pathlib').Path({str(marker)!r}).write_text('owned')"
    with pytest.raises((ValueError, SyntaxError)):
        ast.literal_eval(expression)
    assert not marker.exists()


def test_runtime_and_checker_imports_are_silent_and_side_effect_free() -> None:
    script = (
        "import importlib,importlib.util;"
        f"importlib.import_module({runtime.__name__!r});"
        f"s=importlib.util.spec_from_file_location('c',{str(CHECKER_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    completed = subprocess.run(
        (sys.executable, "-B", "-c", script), cwd=ROOT, capture_output=True,
        text=True, check=False, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    assert completed.returncode == 0 and completed.stdout == completed.stderr == ""
    assert before == after


def test_no_forbidden_candidate_artifacts() -> None:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    status = subprocess.run(
        ("git", "status", "--short"), cwd=ROOT, capture_output=True,
        text=True, check=True,
    ).stdout.splitlines()
    assert not any((ROOT / line[3:]).suffix in forbidden for line in status)
