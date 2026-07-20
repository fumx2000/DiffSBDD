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

from covalent_ext import covapie_bulk_download_admission_admit_010_rule_logic_interface as standalone
from covalent_ext import covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate as oracle
from covalent_ext import covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009 as predecessor
from covalent_ext import covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010 as runtime


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / runtime.DEFAULT_OUTPUT_ROOT
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1.py"
SCALAR = "COVAPIE_LEAKAGE_GROUP_000001"
PROVENANCE = standalone._valid_contract(candidate=SCALAR)


def _checker():
    spec = importlib.util.spec_from_file_location("exact10_runtime_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _route(candidate: object, **overrides: object):
    kwargs = {
        "batch_context": None,
        "evaluation_context": {runtime.ADMIT_010_CONTEXT_ITEMS[0]: PROVENANCE},
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return runtime.evaluate_admission_rule("ADMIT_010", candidate, **kwargs)


def _copied_outputs(tmp_path: Path, name: str) -> Path:
    copied = tmp_path / name
    shutil.copytree(OUTPUT_ROOT, copied)
    return copied


def _rewrite_csv_cell(
    copied: Path,
    filename: str,
    identity_field: str,
    identity_value: str,
    target_field: str,
    target_value: str,
) -> None:
    path = copied / filename
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    matches = [row for row in rows if row[identity_field] == identity_value]
    assert len(matches) == 1
    matches[0][target_field] = target_value
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = copied / runtime.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_manifest_mapping(
    copied: Path,
    mapping_name: str,
    rule_id: str,
    replacement: str,
) -> None:
    path = copied / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest[mapping_name][rule_id] = replacement
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CountingMapping(Mapping):
    def __init__(self, values: dict[str, object], error: Exception | None = None) -> None:
        self.values = values
        self.error = error
        self.getitem_calls: list[object] = []
        self.iterated = False
        self.get_called = False
        self.contains_called = False

    def __getitem__(self, key: object) -> object:
        self.getitem_calls.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]  # type: ignore[index]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
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


def test_public_identity_constants_and_exact10_registry() -> None:
    assert runtime.STEP == "unified dispatch runtime with ADMIT_001 to ADMIT_010 v1"
    assert runtime.STAGE == "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1"
    assert runtime.EXPECTED_BASE_COMMIT == "73aa9b4e91e3f80da47da2909eb2702dc04e15c9"
    assert runtime.EXPECTED_BASE_SUBJECT == "add CovaPIE ADMIT_010 unified adapter contract design v1"
    assert runtime.MANIFEST_SCHEMA_VERSION == "covapie_unified_dispatch_runtime_with_admit_001_to_010_manifest_v1"
    assert runtime.RECOMMENDED_NEXT_STEP == "audit_covapie_admit_011_formal_evaluator_interface_preconditions_v1"
    for name in (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        assert getattr(runtime, name) is getattr(predecessor, name)
    assert runtime.ADMISSION_RULE_ID == "ADMIT_010"
    assert runtime.ADMISSION_RULE_NAME == "leakage_group_assignment_before_split"
    assert runtime.ADAPTER_ID == "covapie_admit_010_unified_adapter_v1"
    assert runtime.ADMIT_010_CANDIDATE_FIELDS == ("leakage_group_id",)
    assert runtime.ADMIT_010_CONTEXT_ITEMS == ("leakage_group_assignment_provenance_contract",)
    assert runtime.KNOWN_RULE_IDS == tuple(f"ADMIT_{i:03d}" for i in range(1, 16))
    assert runtime.CALLABLE_DISCOVERED_RULE_IDS == tuple(f"ADMIT_{i:03d}" for i in range(1, 11))
    assert runtime.ADAPTER_READY_RULE_IDS == runtime.CALLABLE_DISCOVERED_RULE_IDS
    assert runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
    assert type(runtime.RULE_NAMES) is MappingProxyType
    assert type(runtime.ADAPTER_IDS) is MappingProxyType
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == runtime.CALLABLE_DISCOVERED_RULE_IDS
    assert all(
        runtime.EVALUATOR_REGISTRY[rule] is predecessor.EVALUATOR_REGISTRY[rule]
        for rule in runtime.KNOWN_RULE_IDS[:9]
    )
    assert runtime.EVALUATOR_REGISTRY["ADMIT_010"] is runtime._evaluate_registered_admit_010


def test_new_dispatcher_has_exact9_signature_and_local_registry_binding() -> None:
    assert runtime.evaluate_admission_rule is not predecessor.evaluate_admission_rule
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(predecessor.evaluate_admission_rule)
    assert runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is runtime.EVALUATOR_REGISTRY
    assert runtime.EVALUATOR_REGISTRY is not predecessor.EVALUATOR_REGISTRY


@pytest.mark.parametrize(
    ("rule_id", "code", "known"),
    (
        (type("StringSubclass", (str,), {})("ADMIT_010"), "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", False),
        *( (f"ADMIT_{index:03d}", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", True) for index in range(11, 16) ),
    ),
)
def test_global_dispatch_precedence(rule_id: object, code: str, known: bool) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        runtime.evaluate_admission_rule(rule_id, {})  # type: ignore[arg-type]
    assert caught.value.code == code
    assert caught.value.known_rule is known
    assert caught.value.callable_discovered is False
    assert caught.value.adapter_ready is False


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"batch_context": {}}, "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"batch_context": object()}, "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": None}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": object()}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_context_failures_are_exact_and_precede_candidate(overrides: dict[str, object], reason: str) -> None:
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
        _route(CandidateBomb(), **overrides)
    assert tuple(getattr(caught.value, name) for name in runtime.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_010",
        True,
        True,
        True,
        reason,
    )


def test_context_failure_precedence_is_exact_five_gate_order() -> None:
    cases = (
        (
            {"batch_context": object(), "evaluation_context": object(), "download_result_context": object(), "stage_authorization_context": object()},
            "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"evaluation_context": object(), "download_result_context": object(), "stage_authorization_context": object()},
            "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            {"evaluation_context": {}, "download_result_context": object(), "stage_authorization_context": object()},
            "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED",
        ),
        (
            {"download_result_context": object(), "stage_authorization_context": object()},
            "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ),
        ({"stage_authorization_context": object()}, "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    )
    for overrides, reason in cases:
        with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
            _route(CandidateBomb(), **overrides)
        assert caught.value.reason == reason


def test_mapping_subclasses_single_direct_lookup_without_other_operations() -> None:
    candidate = CountingMapping({"leakage_group_id": SCALAR, "ignored": object()})
    context = CountingMapping({runtime.ADMIT_010_CONTEXT_ITEMS[0]: PROVENANCE, "ignored": object()})
    result = _route(candidate, evaluation_context=context)
    assert result.outcome == "passed"
    assert candidate.getitem_calls == ["leakage_group_id"]
    assert context.getitem_calls == [runtime.ADMIT_010_CONTEXT_ITEMS[0]]
    assert not candidate.iterated and not context.iterated
    assert not candidate.get_called and not context.get_called
    assert not candidate.contains_called and not context.contains_called
    assert candidate.values["ignored"] is not None and context.values["ignored"] is not None


def test_non_key_error_lookup_exceptions_propagate_unchanged() -> None:
    context_error = RuntimeError("context sentinel")
    with pytest.raises(RuntimeError) as caught:
        _route({}, evaluation_context=CountingMapping({}, context_error))
    assert caught.value is context_error
    candidate_error = RuntimeError("candidate sentinel")
    with pytest.raises(RuntimeError) as caught:
        _route(CountingMapping({}, candidate_error))
    assert caught.value is candidate_error


def test_present_none_and_original_objects_are_forwarded_once(monkeypatch: pytest.MonkeyPatch) -> None:
    scalar = None
    provenance = object()
    calls: list[tuple[str, object, object]] = []
    original_formal = standalone.evaluate_admit_010
    original_oracle = oracle.classify_admit_010_leakage_group_assignment_provenance_design

    def formal(value: object, contract: object):
        calls.append(("formal", value, contract))
        return original_formal(value, contract)

    def classify(value: object, contract: object):
        calls.append(("oracle", value, contract))
        return original_oracle(value, contract)

    monkeypatch.setattr(standalone, "evaluate_admit_010", formal)
    monkeypatch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", classify)
    result = _route(
        {"leakage_group_id": scalar},
        evaluation_context={runtime.ADMIT_010_CONTEXT_ITEMS[0]: provenance},
    )
    assert result.reason == "LEAKAGE_GROUP_ID_TYPE_INVALID"
    assert [call[0] for call in calls] == ["formal", "oracle"]
    assert all(call[1] is scalar and call[2] is provenance for call in calls)


def test_candidate_nonmapping_and_missing_return_exact13_without_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(standalone, "evaluate_admit_010", lambda *_: calls.append("formal"))
    monkeypatch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", lambda *_: calls.append("oracle"))
    for candidate, reason in (
        (object(), "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "leakage_group_id_missing"),
    ):
        result = _route(candidate)
        assert tuple(getattr(result, name) for name in runtime.RESULT_FIELDS) == (
            runtime.RESULT_SCHEMA_VERSION,
            "ADMIT_010",
            "leakage_group_assignment_before_split",
            "invalid",
            False,
            True,
            reason,
            (),
            (),
            ("leakage_group_id",),
            ("leakage_group_assignment_provenance_contract",),
            False,
            "covapie_admit_010_unified_adapter_v1",
        )
    assert calls == []


@pytest.mark.parametrize(
    "scalar",
    (None, "", type("StringSubclass", (str,), {})(SCALAR), "COVAPIE_LEAKAGE_GROUP_00000é", "bad", SCALAR),
)
def test_present_candidate_scalar_values_are_forwarded_without_adapter_normalization(
    scalar: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[object] = []
    original = standalone.evaluate_admit_010

    def formal(value: object, provenance: object):
        seen.append(value)
        return original(value, provenance)

    monkeypatch.setattr(standalone, "evaluate_admit_010", formal)
    _route({"leakage_group_id": scalar})
    assert seen == [scalar]
    assert seen[0] is scalar


def test_exact71_formal_oracle_and_exact13_projection_full_parity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formal_calls = 0
    oracle_calls = 0
    original_formal = standalone.evaluate_admit_010
    original_oracle = oracle.classify_admit_010_leakage_group_assignment_provenance_design

    def formal(value: object, provenance: object):
        nonlocal formal_calls
        formal_calls += 1
        return original_formal(value, provenance)

    def classify(value: object, provenance: object):
        nonlocal oracle_calls
        oracle_calls += 1
        return original_oracle(value, provenance)

    monkeypatch.setattr(standalone, "evaluate_admit_010", formal)
    monkeypatch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", classify)
    cases = standalone._natural_cases()
    assert len(cases) == 71
    for _group, _case_id, scalar, provenance, _precedence in cases:
        source = original_formal(scalar, provenance)
        result = _route(
            {"leakage_group_id": scalar},
            evaluation_context={runtime.ADMIT_010_CONTEXT_ITEMS[0]: provenance},
        )
        assert result.normalized_values == source.validated_candidate_fields
        assert result.validated_candidate_fields == source.validated_candidate_fields
        assert tuple(getattr(result, name) for name in (
            "outcome", "passed", "blocks_candidate", "reason",
            "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
        )) == tuple(getattr(source, name) for name in (
            "outcome", "passed", "blocks_candidate", "reason",
            "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
        ))
    assert formal_calls == 71
    assert oracle_calls == 71


def test_source_wrong_type_and_subclass_fail_before_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    source = standalone.evaluate_admit_010(SCALAR, PROVENANCE)
    class ResultSubclass(type(source)):
        pass
    subclass = object.__new__(ResultSubclass)
    for name in standalone.RESULT_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    for bad in (object(), {}, subclass):
        calls: list[object] = []
        monkeypatch.setattr(standalone, "evaluate_admit_010", lambda *_args, value=bad: value)
        monkeypatch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", lambda *args: calls.append(args))
        with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
            _route({"leakage_group_id": SCALAR})
        assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        assert caught.value.reason == "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        assert caught.value.adapter_ready is False
        assert calls == []


def test_source_vars_storage_dataclass_and_cross_field_fail_before_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    original_formal = standalone.evaluate_admit_010
    ordered = original_formal(SCALAR, PROVENANCE)
    first = standalone.RESULT_FIELDS[0]
    saved = vars(ordered).pop(first)
    vars(ordered)[first] = saved
    cross = original_formal(SCALAR, PROVENANCE)
    object.__setattr__(cross, "reason", "LEAKAGE_GROUP_ID_TYPE_INVALID")

    for bad in (ordered, cross):
        calls: list[object] = []
        with monkeypatch.context() as patch:
            patch.setattr(standalone, "evaluate_admit_010", lambda *_args, value=bad: value)
            patch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", lambda *args: calls.append(args))
            with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
                _route({"leakage_group_id": SCALAR})
        assert caught.value.reason == "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        assert calls == []

    exact = original_formal(SCALAR, PROVENANCE)
    calls = []
    with monkeypatch.context() as patch:
        patch.setattr(standalone, "evaluate_admit_010", lambda *_: exact)
        patch.setattr(runtime, "vars", lambda _value: MappingProxyType(dict(vars(exact))), raising=False)
        patch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", lambda *args: calls.append(args))
        with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
            _route({"leakage_group_id": SCALAR})
    assert caught.value.reason == "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert calls == []

    calls = []
    with monkeypatch.context() as patch:
        patch.setattr(standalone, "evaluate_admit_010", lambda *_: exact)
        patch.setattr(runtime, "fields", lambda _type: tuple(reversed(fields(standalone.Admit010EvaluationResult))))
        patch.setattr(oracle, "classify_admit_010_leakage_group_assignment_provenance_design", lambda *args: calls.append(args))
        with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
            _route({"leakage_group_id": SCALAR})
    assert caught.value.reason == "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert calls == []


def test_oracle_nonmapping_missing_key_and_mismatch_fail_without_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    valid = dict(oracle.classify_admit_010_leakage_group_assignment_provenance_design(SCALAR, PROVENANCE))
    missing = dict(valid)
    missing.pop("reason")
    mismatch = {**valid, "evaluator_io_used": True}
    for classification in (object(), missing, mismatch):
        with monkeypatch.context() as patch:
            patch.setattr(
                oracle,
                "classify_admit_010_leakage_group_assignment_provenance_design",
                lambda *_args, value=classification: value,
            )
            with pytest.raises(runtime.UnifiedAdmissionDispatchError) as caught:
                _route({"leakage_group_id": SCALAR})
        assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        assert caught.value.reason == "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        assert caught.value.adapter_ready is False


def test_scalar_short_projection_does_not_inject_envelope_context() -> None:
    result = _route({"leakage_group_id": ""})
    assert result.reason == "leakage_group_unassigned"
    assert result.normalized_values == result.validated_candidate_fields == ()
    assert result.consumed_context_items == ()


def test_public_call_graph_is_pure_and_design_gate_is_not_imported() -> None:
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.extend(alias.name for alias in node.names)
    assert not any("admit_010_unified_adapter_contract_design_gate" in name for name in imported)
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    for builder in (
        "runtime._global_rows",
        "runtime._identity_rows",
        "runtime._context_rows",
        "runtime._mapping_rows",
        "runtime._candidate_rows",
        "runtime._exact71_rows",
        "runtime._source_failure_rows",
        "runtime._contract_rows",
        "runtime._manifest_payload",
    ):
        assert builder not in checker_source
    assert "evaluate_all_rules" not in runtime.__dict__
    assert "combined_candidate_verdict" not in runtime.__dict__


def test_exact18_snapshot_order_hash_and_structure() -> None:
    snapshot = runtime.build_frozen_source_snapshot(ROOT)
    assert len(snapshot.records) == 18
    assert tuple(record.relative_path for record in snapshot.records) == runtime.SOURCE_PATHS
    assert all(
        record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        for record in snapshot.records
    )
    assert runtime.validate_frozen_source_snapshot(snapshot)


def test_runtime_state_natural_counts_and_issue_transition() -> None:
    state = runtime.build_runtime_state(runtime.build_frozen_source_snapshot(ROOT))
    assert len(state["contract_rows"]) == 80
    assert len(state["truth_rows"]) == 407
    assert state["truth_group_counts"] == {
        "predecessor_exact9_truth": 289,
        "global_dispatch": 9,
        "predecessor_handler_identity": 9,
        "admit010_context_routing": 7,
        "admit010_mapping_semantics": 5,
        "admit010_candidate_envelope": 8,
        "admit010_standalone_exact71": 71,
        "admit010_source_failure": 9,
    }
    assert len(state["registry_rows"]) == 15
    assert len(state["safety_rows"]) == 20
    assert len(state["issue_rows"]) == 11
    issue_bytes = runtime._csv_bytes(runtime.ISSUE_COLUMNS, state["issue_rows"])
    assert hashlib.sha256(issue_bytes).hexdigest() == "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c"
    source_rows = list(csv.DictReader((ROOT / runtime.DESIGN_ISSUE_PATH).read_text(encoding="utf-8").splitlines()))
    changed = [
        (before, after)
        for before, after in zip(source_rows, state["issue_rows"], strict=True)
        if before != after
    ]
    assert len(changed) == 1
    before, after = changed[0]
    assert before["issue_id"] == after["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    assert {key for key in before if before[key] != after[key]} == {"affected_rules", "integration_transition"}
    assert after["affected_rules"] == "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    assert after["integration_transition"] == "admit_010_implemented_and_removed_from_open_coverage_scope"
    assert after["status"] == "open"


def test_outputs_are_exact_six_regular_and_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(first, repo_root=ROOT)
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(second, repo_root=ROOT)
    assert {path.name for path in first.iterdir()} == set(runtime.OUTPUT_FILES)
    assert all(stat.S_ISREG(os.lstat(path).st_mode) and not stat.S_ISLNK(os.lstat(path).st_mode) for path in first.iterdir())
    assert {name: (first / name).read_bytes() for name in runtime.OUTPUT_FILES} == {
        name: (second / name).read_bytes() for name in runtime.OUTPUT_FILES
    }
    assert not tuple(tmp_path.rglob("*.tmp"))


def test_materializer_source_failure_leaves_missing_root_and_parent_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "real-parent"
    parent.mkdir()
    marker = parent / "parent-marker.bin"
    marker.write_bytes(b"parent-must-remain-byte-identical")
    output = parent / "missing-output"
    before = {
        path.name: (path.read_bytes(), os.lstat(path).st_mtime_ns)
        for path in parent.iterdir()
    }
    sentinel = ValueError("source validation sentinel")
    atomic_calls = 0

    def atomic_bomb(*args: object, **kwargs: object) -> None:
        nonlocal atomic_calls
        atomic_calls += 1
        raise AssertionError("atomic write reached")

    monkeypatch.setattr(runtime, "build_frozen_source_snapshot", lambda *_args, **_kwargs: (_ for _ in ()).throw(sentinel))
    monkeypatch.setattr(runtime, "_atomic_write", atomic_bomb)
    with pytest.raises(ValueError) as caught:
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(
            output, repo_root=ROOT
        )
    assert caught.value is sentinel
    assert not output.exists() and not output.is_symlink()
    after = {
        path.name: (path.read_bytes(), os.lstat(path).st_mtime_ns)
        for path in parent.iterdir()
    }
    assert after == before
    assert atomic_calls == 0
    assert not tuple(parent.rglob("*.tmp"))
    assert not tuple(parent.rglob("*.part"))


def test_materializer_source_failure_preserves_existing_safe_root_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "existing-output"
    output.mkdir()
    old_files = {
        runtime.CONTRACT_FILENAME: b"old-contract-marker\n",
        runtime.MANIFEST_FILENAME: b"old-manifest-marker\n",
    }
    for name, content in old_files.items():
        (output / name).write_bytes(content)
    before = {
        path.name: (
            path.read_bytes(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            os.lstat(path).st_mtime_ns,
        )
        for path in output.iterdir()
    }
    sentinel = ValueError("source validation sentinel")
    atomic_calls = 0

    def atomic_bomb(*args: object, **kwargs: object) -> None:
        nonlocal atomic_calls
        atomic_calls += 1
        raise AssertionError("atomic write reached")

    monkeypatch.setattr(runtime, "build_frozen_source_snapshot", lambda *_args, **_kwargs: (_ for _ in ()).throw(sentinel))
    monkeypatch.setattr(runtime, "_atomic_write", atomic_bomb)
    with pytest.raises(ValueError) as caught:
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(
            output, repo_root=ROOT
        )
    assert caught.value is sentinel
    after = {
        path.name: (
            path.read_bytes(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            os.lstat(path).st_mtime_ns,
        )
        for path in output.iterdir()
    }
    assert after == before
    assert atomic_calls == 0
    assert not tuple(output.rglob("*.tmp"))
    assert not tuple(output.rglob("*.part"))


def test_preflight_is_nonmutating_and_runner_order_is_exact() -> None:
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    preflight = functions["_resolved_output_preflight"]
    preflight_calls = {
        ast.unparse(node.func).split(".")[-1]
        for node in ast.walk(preflight)
        if isinstance(node, ast.Call)
    }
    assert not preflight_calls & {
        "mkdir", "touch", "write", "write_bytes", "write_text", "unlink",
        "replace", "mkstemp", "NamedTemporaryFile",
    }
    runner = functions[
        "run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1"
    ]
    runner_source = ast.get_source_segment(source, runner)
    assert runner_source is not None
    ordered_tokens = (
        "_resolved_output_preflight(",
        "build_frozen_source_snapshot(",
        "build_runtime_state(",
        "_payloads(",
        "root.mkdir(",
        "_validate_prewrite_output_root(",
        "_atomic_write(",
        "_postvalidate_output_root(",
    )
    positions = tuple(runner_source.index(token) for token in ordered_tokens)
    assert positions == tuple(sorted(positions))


@pytest.mark.parametrize("unsafe_kind", ("extra", "directory", "symlink", "fifo"))
def test_materializer_rejects_unsafe_inventory_before_source_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsafe_kind: str,
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    target = output / ("unexpected" if unsafe_kind == "extra" else runtime.CONTRACT_FILENAME)
    if unsafe_kind == "extra":
        target.write_text("x", encoding="utf-8")
    elif unsafe_kind == "directory":
        target.mkdir()
    elif unsafe_kind == "symlink":
        target.symlink_to(tmp_path)
    else:
        os.mkfifo(target)
    called = False

    def bomb(*args: object, **kwargs: object):
        nonlocal called
        called = True
        raise AssertionError("source read")

    monkeypatch.setattr(runtime, "build_frozen_source_snapshot", bomb)
    with pytest.raises(ValueError):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(output, repo_root=ROOT)
    assert called is False
    assert not tuple(output.glob("*.tmp"))


def test_materializer_rejects_parent_symlink_and_relative_escape_before_source_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    called = False

    def bomb(*args: object, **kwargs: object):
        nonlocal called
        called = True
        raise AssertionError("source read")

    monkeypatch.setattr(runtime, "build_frozen_source_snapshot", bomb)
    with pytest.raises(ValueError, match="resolved containment"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(link / "output", repo_root=ROOT)
    with pytest.raises(ValueError, match="resolved containment"):
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(Path("../outside"), repo_root=ROOT)
    assert called is False
    assert not (real / "output").exists()


def test_checker_accepts_frozen_relative_and_real_absolute_outputs(tmp_path: Path) -> None:
    checker = _checker()
    checker._validate_output_tree()
    checker._validate_output_tree(runtime.DEFAULT_OUTPUT_ROOT, enforce_frozen_hashes=False)
    copied = _copied_outputs(tmp_path, "absolute")
    checker._validate_output_tree(copied.resolve(strict=True), enforce_frozen_hashes=False)


def test_checker_owns_complete_exact10_rule_and_adapter_mappings() -> None:
    checker = _checker()
    assert tuple(checker.EXPECTED_RULE_NAMES) == checker.REGISTERED_IDS
    assert checker.EXPECTED_RULE_NAMES == {
        "ADMIT_001": "unique_candidate_identity",
        "ADMIT_002": "valid_pdb_id_format",
        "ADMIT_003": "ligand_or_het_identity_present",
        "ADMIT_004": "covalent_residue_identity_present",
        "ADMIT_005": "cys_sg_scope_only_v1",
        "ADMIT_006": "explicit_covalent_event_evidence",
        "ADMIT_007": "distance_only_inference_forbidden",
        "ADMIT_008": "topology_restoration_disposition",
        "ADMIT_009": "duplicate_identity_precheck",
        "ADMIT_010": "leakage_group_assignment_before_split",
    }
    assert tuple(checker.EXPECTED_ADAPTER_IDS) == checker.REGISTERED_IDS
    assert checker.EXPECTED_ADAPTER_IDS == {
        f"ADMIT_{index:03d}": f"covapie_admit_{index:03d}_unified_adapter_v1"
        for index in range(1, 11)
    }
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    checker_tree = ast.parse(checker_source)
    assignments = {
        target.id: node.value
        for node in checker_tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert isinstance(assignments["EXPECTED_RULE_NAMES"], ast.Dict)
    assert isinstance(assignments["EXPECTED_ADAPTER_IDS"], ast.Dict)
    functions = {
        node.name: ast.get_source_segment(checker_source, node)
        for node in checker_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert "runtime." not in functions["_expected_registry_rows"]
    assert "runtime." not in functions["_expected_manifest"]


@pytest.mark.parametrize(
    ("runtime_attribute", "manifest_mapping", "registry_field", "rule_id"),
    (
        ("RULE_NAMES", "rule_names", "rule_name", "ADMIT_001"),
        ("RULE_NAMES", "rule_names", "rule_name", "ADMIT_010"),
        ("ADAPTER_IDS", "adapter_ids", "adapter_id", "ADMIT_001"),
        ("ADAPTER_IDS", "adapter_ids", "adapter_id", "ADMIT_010"),
    ),
)
def test_checker_rejects_synchronized_runtime_and_output_mapping_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime_attribute: str,
    manifest_mapping: str,
    registry_field: str,
    rule_id: str,
) -> None:
    checker = _checker()
    replacement = f"tampered_{runtime_attribute.lower()}_{rule_id.lower()}"
    tampered = dict(getattr(runtime, runtime_attribute))
    tampered[rule_id] = replacement
    copied = _copied_outputs(
        tmp_path, f"{runtime_attribute.lower()}-{rule_id.lower()}"
    )
    _rewrite_csv_cell(
        copied,
        runtime.REGISTRY_FILENAME,
        "rule_id",
        rule_id,
        registry_field,
        replacement,
    )
    _rewrite_manifest_mapping(copied, manifest_mapping, rule_id, replacement)
    with monkeypatch.context() as patch:
        patch.setattr(runtime, runtime_attribute, MappingProxyType(tampered))
        with pytest.raises(AssertionError, match="mapping drift"):
            checker._verify_runtime_identity(runtime)
        with pytest.raises(AssertionError, match="Exact15 registry complete equality"):
            checker._validate_output_tree(copied, enforce_frozen_hashes=False)
    checker._verify_runtime_identity(runtime)


def test_runtime_business_function_ast_sha256_is_unchanged() -> None:
    expected = {
        "_raise_dispatch_error": "23e7ddd78bcd38e7f3be5adc5aff66f364dc74bf479457faca7509ec1db701af",
        "_admit010_context_failure": "fae5b22764562c557566eb59a59edf204fe6738c8c5d5bcf4586fb40a7e8f067",
        "_admit010_adapter_failure": "47d47b6a6d8321f7df1f901317ddf51c3b25029f01b16de800740faf788e55e8",
        "_admit010_candidate_invalid": "f8792b120eef195e234e525a2b9438502897ed1c8eab0b8077578450c7968709",
        "_prevalidate_admit010_source": "626a7d492400b98196f8074f567170fc5103adc377733d74bf74633411f86b37",
        "_expected_admit010_from_oracle": "71e0064ff8602101fd6066518bc559ea5c7ae8e1f2945cd284234de0149dbf5a",
        "_validate_admit010_oracle_equivalence": "d5f0edf6bad450ffa9b90c78783a686d58ab6e0053f9bdd2eb6144a9557e813c",
        "_project_admit010_exact13": "32f68ab48417ecb891417127cd42c38bd0131d9120401683885092188d6f2f1c",
        "_evaluate_registered_admit_010": "20054e9df7dc35942aa5bbea6d605668689a83060bd2142a05b4936086a3fa58",
        "evaluate_admission_rule": "b857b74f6f82388174004c57a1e99c6f10b0c5ff81b373eb8417e28c01687864",
    }
    tree = ast.parse(Path(runtime.__file__).read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    actual = {
        name: hashlib.sha256(
            ast.dump(
                functions[name], annotate_fields=True, include_attributes=False
            ).encode("utf-8")
        ).hexdigest()
        for name in expected
    }
    assert actual == expected


def test_checker_completes_exact18_verification_before_expected_source_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _checker()
    source_verified = False
    original_verify = checker._verify_sources
    original_truth = checker._verify_truth_rows
    original_issues = checker._expected_issue_rows

    def verify_sources():
        nonlocal source_verified
        result = original_verify()
        source_verified = True
        return result

    def verify_truth(*args: object, **kwargs: object):
        assert source_verified
        return original_truth(*args, **kwargs)

    def expected_issues():
        assert source_verified
        return original_issues()

    monkeypatch.setattr(checker, "_verify_sources", verify_sources)
    monkeypatch.setattr(checker, "_verify_truth_rows", verify_truth)
    monkeypatch.setattr(checker, "_expected_issue_rows", expected_issues)
    checker._validate_output_tree(enforce_frozen_hashes=False)
    assert source_verified


def test_checker_rejects_parent_symlink_before_output_or_source_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _checker()
    outside = tmp_path / "outside"
    external = outside / "nested" / "outputs"
    shutil.copytree(OUTPUT_ROOT, external)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "linked").symlink_to(outside, target_is_directory=True)
    output_reads = 0
    source_calls = 0
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def tracked_bytes(path: Path) -> bytes:
        nonlocal output_reads
        try:
            path.resolve(strict=True).relative_to(outside.resolve(strict=True))
        except (OSError, ValueError):
            pass
        else:
            output_reads += 1
        return original_read_bytes(path)

    def tracked_text(path: Path, *args: object, **kwargs: object) -> str:
        nonlocal output_reads
        try:
            path.resolve(strict=True).relative_to(outside.resolve(strict=True))
        except (OSError, ValueError):
            pass
        else:
            output_reads += 1
        return original_read_text(path, *args, **kwargs)

    def tracked_sources() -> tuple[()]:
        nonlocal source_calls
        source_calls += 1
        return ()

    monkeypatch.setattr(Path, "read_bytes", tracked_bytes)
    monkeypatch.setattr(Path, "read_text", tracked_text)
    monkeypatch.setattr(checker, "_verify_sources", tracked_sources)
    with pytest.raises(AssertionError, match="resolved containment"):
        checker._validate_output_tree(repo / "linked/nested/outputs", enforce_frozen_hashes=False)
    assert output_reads == 0
    assert source_calls == 0


@pytest.mark.parametrize(
    ("filename", "identity_field", "identity_value", "target_field", "replacement", "message"),
    (
        (runtime.CONTRACT_FILENAME, "contract_id", "TYPE_001", "contract_statement", "tampered", "Exact80 contract complete equality"),
        (runtime.TRUTH_FILENAME, "case_id", "GLOBAL_unknown_rule", "behavior", "tampered", "successor Exact118 truth complete equality"),
        (runtime.REGISTRY_FILENAME, "rule_id", "ADMIT_010", "handler_identity_status", "tampered", "Exact15 registry complete equality"),
        (runtime.SAFETY_FILENAME, "safety_item", "provider_mapping", "observed_executed", "true", "Exact20 safety complete equality"),
        (runtime.ISSUE_FILENAME, "issue_id", "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED", "status", "resolved", "Exact11 issue complete equality"),
    ),
)
def test_checker_rejects_csv_semantic_tamper_with_refreshed_manifest_hash(
    tmp_path: Path,
    filename: str,
    identity_field: str,
    identity_value: str,
    target_field: str,
    replacement: str,
    message: str,
) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, identity_value)
    _rewrite_csv_cell(copied, filename, identity_field, identity_value, target_field, replacement)
    with pytest.raises(AssertionError, match=message):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "mutation",
    (
        "project",
        "step",
        "manifest_schema_version",
        "source_nested_unknown",
        "readiness_mirror",
        "readiness_unknown",
        "top_level_unknown",
        "provider_mapping",
        "admit011",
    ),
)
def test_checker_rejects_manifest_tamper(tmp_path: Path, mutation: str) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, mutation)
    path = copied / runtime.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "project":
        manifest["project"] = "tampered"
    elif mutation == "step":
        manifest["step"] = "tampered"
    elif mutation == "manifest_schema_version":
        manifest["manifest_schema_version"] = "tampered_v1"
    elif mutation == "source_nested_unknown":
        manifest["source_input_verification"][0]["unknown"] = True
    elif mutation == "readiness_mirror":
        manifest["ready_for_training"] = True
    elif mutation == "readiness_unknown":
        manifest["readiness"]["unknown"] = False
    elif mutation == "top_level_unknown":
        manifest["unknown"] = True
    elif mutation == "provider_mapping":
        manifest["leakage_group_id_provider_mapping_validated"] = True
    elif mutation == "admit011":
        manifest["admit_011_started"] = True
    else:
        raise AssertionError("unhandled mutation")
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="manifest complete equality"):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_runtime_and_checker_imports_are_silent_and_side_effect_free() -> None:
    script = (
        "import importlib;"
        f"importlib.import_module({runtime.__name__!r});"
        f"s=__import__('importlib.util',fromlist=['x']).spec_from_file_location('c',{str(CHECKER_PATH)!r});"
        "m=__import__('importlib.util',fromlist=['x']).module_from_spec(s);s.loader.exec_module(m)"
    )
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    completed = subprocess.run(
        (sys.executable, "-c", script),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""
    assert before == after
