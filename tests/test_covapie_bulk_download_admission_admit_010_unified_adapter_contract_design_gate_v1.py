from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
from collections.abc import Mapping
from dataclasses import fields, replace
from pathlib import Path

import pytest

from covalent_ext import covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate as oracle
from covalent_ext import covapie_bulk_download_admission_admit_010_rule_logic_interface as standalone
from covalent_ext import covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate as gate
from covalent_ext import covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009 as runtime


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / gate.DEFAULT_OUTPUT_ROOT
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1.py"
SCALAR = "COVAPIE_LEAKAGE_GROUP_000001"
PROVENANCE = standalone._valid_contract(candidate=SCALAR)


def _checker():
    spec = importlib.util.spec_from_file_location("admit010_adapter_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    manifest_path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _route(candidate: object, **overrides: object):
    kwargs = {
        "batch_context": None,
        "evaluation_context": {gate.CONTEXT_ITEMS[0]: PROVENANCE},
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return gate.route_and_project_for_design(candidate, **kwargs)


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


def test_identity_exact_fields_and_design_only_boundary() -> None:
    assert gate.ADMISSION_RULE_ID == "ADMIT_010"
    assert gate.ADMISSION_RULE_NAME == "leakage_group_assignment_before_split"
    assert gate.ADAPTER_ID == "covapie_admit_010_unified_adapter_v1"
    assert gate.CANDIDATE_FIELDS == ("leakage_group_id",)
    assert gate.CONTEXT_ITEMS == ("leakage_group_assignment_provenance_contract",)
    assert gate.CURRENT_REGISTERED_RULE_ORDER == tuple(f"ADMIT_{i:03d}" for i in range(1, 10))
    assert gate.FUTURE_REGISTERED_RULE_ORDER == tuple(f"ADMIT_{i:03d}" for i in range(1, 11))
    assert tuple(field.name for field in fields(gate.UnifiedAdmissionEvaluationDesignRecord)) == gate.RESULT_FIELDS
    tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assignments = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    assert "_evaluate_registered_admit_010" not in names
    assert "evaluate_admission_rule" not in names
    assert "EVALUATOR_REGISTRY" not in assignments


def test_current_exact9_public_and_handler_object_identities() -> None:
    predecessor = runtime.predecessor
    for name in (
        "UnifiedAdmissionRuleEvaluation", "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        assert getattr(runtime, name) is getattr(predecessor, name)
    assert tuple(runtime.EVALUATOR_REGISTRY) == gate.CURRENT_REGISTERED_RULE_ORDER
    assert all(runtime.EVALUATOR_REGISTRY[rule] is predecessor.EVALUATOR_REGISTRY[rule] for rule in gate.CURRENT_REGISTERED_RULE_ORDER[:8])
    assert runtime.EVALUATOR_REGISTRY["ADMIT_009"] is runtime._evaluate_registered_admit_009
    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(predecessor.evaluate_admission_rule)


def test_exact15_snapshot_is_ordered_and_verified() -> None:
    snapshot = gate.build_frozen_source_snapshot(ROOT)
    assert len(snapshot.records) == 15
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256 for record in snapshot.records)


@pytest.mark.parametrize(
    ("overrides", "reason"),
    (
        ({"batch_context": {}}, "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"batch_context": object()}, "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": None}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    ),
)
def test_context_failures_are_exact6_and_precede_candidate(overrides: dict[str, object], reason: str) -> None:
    class Bomb:
        def __getattribute__(self, name: str) -> object:
            raise AssertionError("candidate accessed")

    calls: list[str] = []
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        _route(Bomb(), formal_evaluator=lambda *args: calls.append("formal"), oracle_callable=lambda *args: calls.append("oracle"), **overrides)
    assert tuple(getattr(caught.value, name) for name in gate.DISPATCH_ERROR_FIELDS) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "ADMIT_010", True, True, True, reason,
    )
    assert calls == []


def test_context_failure_precedence_is_batch_evaluation_key_download_stage() -> None:
    cases = (
        ({"batch_context": object(), "evaluation_context": None, "download_result_context": object(), "stage_authorization_context": object()}, "batch_context"),
        ({"evaluation_context": None, "download_result_context": object(), "stage_authorization_context": object()}, "evaluation_context"),
        ({"evaluation_context": {}, "download_result_context": object(), "stage_authorization_context": object()}, "evaluation_context_key"),
        ({"download_result_context": object(), "stage_authorization_context": object()}, "download_result_context"),
        ({"stage_authorization_context": object()}, "stage_authorization_context"),
    )
    for overrides, key in cases:
        with pytest.raises(gate.AdapterContractDesignError) as caught:
            _route(object(), **overrides)
        assert caught.value.reason == gate.CONTEXT_REASONS[key]


def test_mapping_subclasses_use_single_direct_lookups_without_iteration_or_copy() -> None:
    candidate = CountingMapping({"leakage_group_id": SCALAR, "ignored": object()})
    evaluation = CountingMapping({gate.CONTEXT_ITEMS[0]: PROVENANCE, "ignored": object()})
    result = _route(candidate, evaluation_context=evaluation)
    assert result.outcome == "passed"
    assert candidate.getitem_calls == ["leakage_group_id"]
    assert evaluation.getitem_calls == [gate.CONTEXT_ITEMS[0]]
    assert not candidate.iterated and not evaluation.iterated
    assert not candidate.get_called and not evaluation.get_called
    assert not candidate.contains_called and not evaluation.contains_called


def test_non_key_error_lookup_exceptions_propagate_unchanged() -> None:
    evaluation_error = RuntimeError("evaluation sentinel")
    with pytest.raises(RuntimeError) as caught:
        _route(object(), evaluation_context=CountingMapping({}, evaluation_error))
    assert caught.value is evaluation_error
    candidate_error = RuntimeError("candidate sentinel")
    with pytest.raises(RuntimeError) as caught:
        _route(CountingMapping({}, candidate_error))
    assert caught.value is candidate_error


def test_present_none_is_not_missing_and_original_two_objects_are_forwarded_once() -> None:
    provenance = object()
    calls: list[tuple[str, object, object]] = []

    def formal(scalar: object, context: object):
        calls.append(("formal", scalar, context))
        return standalone.evaluate_admit_010(scalar, context)

    def classify(scalar: object, context: object):
        calls.append(("oracle", scalar, context))
        return oracle.classify_admit_010_leakage_group_assignment_provenance_design(scalar, context)

    result = _route(
        {"leakage_group_id": None},
        evaluation_context={gate.CONTEXT_ITEMS[0]: provenance},
        formal_evaluator=formal, oracle_callable=classify,
    )
    assert result.reason == "LEAKAGE_GROUP_ID_TYPE_INVALID"
    assert [call[0] for call in calls] == ["formal", "oracle"]
    assert all(call[1] is None and call[2] is provenance for call in calls)


def test_candidate_nonmapping_and_missing_are_exact13_without_calls() -> None:
    calls: list[str] = []
    for candidate, reason in ((object(), gate.CANDIDATE_MAPPING_REASON), ({}, gate.MISSING_REASON)):
        result = _route(candidate, formal_evaluator=lambda *args: calls.append("formal"), oracle_callable=lambda *args: calls.append("oracle"))
        assert (result.outcome, result.passed, result.blocks_candidate, result.reason) == ("invalid", False, True, reason)
        assert result.normalized_values == result.validated_candidate_fields == ()
        assert result.consumed_candidate_fields == ("leakage_group_id",)
        assert result.consumed_context_items == gate.CONTEXT_ITEMS
        assert result.evaluator_io_used is False and result.adapter_id == gate.ADAPTER_ID
    assert calls == []


@pytest.mark.parametrize("scalar", (None, 7, "", "é", "bad", SCALAR))
def test_all_present_candidate_values_are_forwarded_without_adapter_prevalidation(scalar: object) -> None:
    seen: list[object] = []

    def formal(value: object, provenance: object):
        seen.append(value)
        return standalone.evaluate_admit_010(value, provenance)

    _route({"leakage_group_id": scalar}, formal_evaluator=formal)
    assert seen == [scalar] and seen[0] is scalar


def test_source_wrong_type_and_subclass_fail_before_oracle() -> None:
    source = standalone.evaluate_admit_010(SCALAR, PROVENANCE)

    class ResultSubclass(type(source)):
        pass

    subclass = object.__new__(ResultSubclass)
    for name in gate.STANDALONE_RESULT_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    for bad in (object(), {}, subclass):
        oracle_calls: list[object] = []
        with pytest.raises(gate.AdapterContractDesignError) as caught:
            _route({"leakage_group_id": SCALAR}, formal_evaluator=lambda *_: bad, oracle_callable=lambda *args: oracle_calls.append(args))
        assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        assert caught.value.reason == gate.SOURCE_TYPE_REASON
        assert caught.value.adapter_ready is False and oracle_calls == []


def test_source_storage_order_and_cross_field_tamper_fail_reconstruction_before_oracle() -> None:
    ordered = standalone.evaluate_admit_010(SCALAR, PROVENANCE)
    first = gate.STANDALONE_RESULT_FIELDS[0]
    value = vars(ordered).pop(first)
    vars(ordered)[first] = value
    cross = standalone.evaluate_admit_010(SCALAR, PROVENANCE)
    object.__setattr__(cross, "reason", "LEAKAGE_GROUP_ID_TYPE_INVALID")
    for bad in (ordered, cross):
        calls: list[object] = []
        with pytest.raises(gate.AdapterContractDesignError) as caught:
            _route({"leakage_group_id": SCALAR}, formal_evaluator=lambda *_: bad, oracle_callable=lambda *args: calls.append(args))
        assert caught.value.reason == gate.SOURCE_INVARIANT_REASON
        assert calls == []


def test_oracle_mapping_and_full_exact10_mismatch_fail_without_projection() -> None:
    for classify in (
        lambda *_: object(),
        lambda scalar, provenance: {**dict(oracle.classify_admit_010_leakage_group_assignment_provenance_design(scalar, provenance)), "evaluator_io_used": True},
    ):
        with pytest.raises(gate.AdapterContractDesignError) as caught:
            _route({"leakage_group_id": SCALAR}, oracle_callable=classify)
        assert caught.value.reason == gate.SOURCE_INVARIANT_REASON
        assert caught.value.adapter_ready is False


def test_scalar_short_projection_does_not_inject_envelope_context() -> None:
    result = _route({"leakage_group_id": ""})
    assert result.reason == "leakage_group_unassigned"
    assert result.normalized_values == result.validated_candidate_fields == ()
    assert result.consumed_context_items == ()


def test_context_invalid_blocked_and_passed_states_are_exact_passthroughs() -> None:
    cases = (
        (SCALAR, None),
        (SCALAR, replace(PROVENANCE, assignment_passed=False)),
        (SCALAR, PROVENANCE),
    )
    for scalar, provenance in cases:
        source = standalone.evaluate_admit_010(scalar, provenance)
        result = _route({"leakage_group_id": scalar}, evaluation_context={gate.CONTEXT_ITEMS[0]: provenance})
        assert result.normalized_values == result.validated_candidate_fields == source.validated_candidate_fields
        for name in ("outcome", "passed", "blocks_candidate", "reason", "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used"):
            assert getattr(result, name) == getattr(source, name)


def test_exact71_formal_oracle_and_exact13_projection_full_parity() -> None:
    rows = gate._truth_rows()
    assert len(rows) == 85
    cases = standalone._natural_cases()
    assert tuple(row["case_id"] for row in rows[:71]) == tuple(f"STANDALONE_{case[1]}" for case in cases)
    for row in rows[:71]:
        assert json.loads(row["source_exact10_json"]) == json.loads(row["oracle_exact10_json"])
        unified = json.loads(row["unified_exact13_json"])
        source = json.loads(row["source_exact10_json"])
        assert unified["normalized_values"] == source["validated_candidate_fields"]
        assert (row["formal_call_count"], row["oracle_call_count"]) == ("1", "1")


def test_design_state_counts_readiness_and_issue_bytes() -> None:
    state = gate.build_design_state(ROOT)
    assert (len(state["contract_rows"]), len(state["routing_rows"]), len(state["truth_rows"])) == (62, 39, 85)
    assert state["issue_bytes"] == (ROOT / gate.SOURCE_PATHS[6]).read_bytes()
    assert hashlib.sha256(state["issue_bytes"]).hexdigest() == "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd"
    assert all(gate.READINESS[name] for name in gate.TRUE_READINESS)
    assert not any(gate.READINESS[name] for name in gate.FALSE_READINESS)


def test_outputs_are_exact_six_and_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    gate.run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(first, repo_root=ROOT)
    gate.run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(second, repo_root=ROOT)
    assert {path.name for path in first.iterdir()} == set(gate.OUTPUT_FILES)
    assert {name: (first / name).read_bytes() for name in gate.OUTPUT_FILES} == {name: (second / name).read_bytes() for name in gate.OUTPUT_FILES}


def test_materializer_rejects_unsafe_inventory_before_source_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "unexpected").write_text("x", encoding="utf-8")
    called = False

    def bomb(*args: object, **kwargs: object):
        nonlocal called
        called = True
        raise AssertionError("source read")

    monkeypatch.setattr(gate, "build_design_state", bomb)
    with pytest.raises(ValueError, match="unexpected output entry"):
        gate.run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(output, repo_root=ROOT)
    assert called is False


def test_materializer_rejects_output_parent_symlink_before_source_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    called = False

    def bomb(*args: object, **kwargs: object):
        nonlocal called
        called = True
        raise AssertionError("source read")

    monkeypatch.setattr(gate, "build_design_state", bomb)
    with pytest.raises(ValueError, match="resolved containment"):
        gate.run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(link / "output", repo_root=ROOT)
    assert called is False


def test_checker_accepts_frozen_repo_relative_and_real_absolute_outputs(tmp_path: Path) -> None:
    checker = _checker()
    checker._validate_output_tree()
    checker._validate_output_tree(gate.DEFAULT_OUTPUT_ROOT, enforce_frozen_hashes=False)
    copied = _copied_outputs(tmp_path, "absolute")
    checker._validate_output_tree(copied.resolve(strict=True), enforce_frozen_hashes=False)


def test_checker_rejects_parent_symlink_before_any_output_or_source_byte_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _checker()
    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    external_outputs = outside / "nested" / "outputs"
    repo.mkdir()
    shutil.copytree(OUTPUT_ROOT, external_outputs)
    marker = outside / "marker.bin"
    marker.write_bytes(b"external-marker-must-remain")
    (repo / "linked").symlink_to(outside, target_is_directory=True)
    before = {path.relative_to(outside): path.read_bytes() for path in outside.rglob("*") if path.is_file()}
    output_reads = 0
    source_calls = 0
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def tracked_read_bytes(path: Path) -> bytes:
        nonlocal output_reads
        try:
            path.resolve(strict=True).relative_to(outside.resolve(strict=True))
        except (OSError, ValueError):
            pass
        else:
            output_reads += 1
        return original_read_bytes(path)

    def tracked_read_text(path: Path, *args: object, **kwargs: object) -> str:
        nonlocal output_reads
        try:
            path.resolve(strict=True).relative_to(outside.resolve(strict=True))
        except (OSError, ValueError):
            pass
        else:
            output_reads += 1
        return original_read_text(path, *args, **kwargs)

    def tracked_verify_sources() -> tuple[()]:
        nonlocal source_calls
        source_calls += 1
        return ()

    monkeypatch.setattr(Path, "read_bytes", tracked_read_bytes)
    monkeypatch.setattr(Path, "read_text", tracked_read_text)
    monkeypatch.setattr(checker, "_verify_sources", tracked_verify_sources)
    with pytest.raises(AssertionError, match="resolved containment"):
        checker._validate_output_tree(repo / "linked/nested/outputs", enforce_frozen_hashes=False)
    assert output_reads == 0
    assert source_calls == 0
    after = {path.relative_to(outside): original_read_bytes(path) for path in outside.rglob("*") if path.is_file()}
    assert after == before
    assert original_read_bytes(marker) == b"external-marker-must-remain"
    assert not any(path.suffix in {".tmp", ".part"} for path in outside.rglob("*"))


@pytest.mark.parametrize(
    ("contract_subject", "replacement"),
    (
        ("admission_rule_name", "tampered_rule_name"),
        ("evaluation_context_item", "tampered_context_item"),
        ("known_not_registered", "ADMIT_011"),
        ("mutation", "allowed"),
        ("operations", "tampered_boundary"),
    ),
)
def test_checker_rejects_exact62_contract_tamper_with_refreshed_hash(
    tmp_path: Path, contract_subject: str, replacement: str,
) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, contract_subject)
    _rewrite_csv_cell(
        copied, gate.CONTRACT_FILENAME, "contract_subject", contract_subject,
        "contract_value", replacement,
    )
    with pytest.raises(AssertionError, match="Exact62 contract complete equality"):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("case_id", "field", "replacement"),
    (
        ("batch_none", "expected_behavior", "tampered"),
        ("evaluation_mapping_subclass", "identity_preserved", "false"),
        ("context_identity", "formal_call_count", "2"),
        ("none_present", "expected_reason", "tampered"),
        ("oracle_once", "oracle_call_count", "2"),
        ("passed", "expected_result_json", "{}"),
    ),
)
def test_checker_rejects_exact39_routing_tamper_with_refreshed_hash(
    tmp_path: Path, case_id: str, field: str, replacement: str,
) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, f"routing-{case_id}")
    _rewrite_csv_cell(
        copied, gate.ROUTING_FILENAME, "case_id", case_id, field, replacement,
    )
    with pytest.raises(AssertionError, match="Exact39 routing complete equality"):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("case_id", "field", "replacement"),
    (
        ("ROUTING_batch_context", "expected_reason", "tampered"),
        ("CANDIDATE_non_mapping", "behavior", "tampered"),
        ("SOURCE_wrong_type", "expected_reason", "tampered"),
        ("SOURCE_wrong_type", "formal_call_count", "2"),
        ("SOURCE_oracle_mismatch", "behavior", "tampered"),
    ),
)
def test_checker_rejects_exact85_truth_tamper_with_refreshed_hash(
    tmp_path: Path, case_id: str, field: str, replacement: str,
) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, f"truth-{case_id}-{field}")
    _rewrite_csv_cell(
        copied, gate.TRUTH_FILENAME, "case_id", case_id, field, replacement,
    )
    with pytest.raises(AssertionError, match="Exact85 truth complete equality"):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    ("safety_item", "field", "replacement"),
    (
        ("adapter_contract_design", "safety_item", "tampered_identity"),
        ("actual_adapter_handler", "expected_executed", "true"),
        ("actual_adapter_handler", "observed_executed", "true"),
    ),
)
def test_checker_rejects_exact35_safety_tamper_with_refreshed_hash(
    tmp_path: Path, safety_item: str, field: str, replacement: str,
) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, f"safety-{field}")
    _rewrite_csv_cell(
        copied, gate.SAFETY_FILENAME, "safety_item", safety_item, field, replacement,
    )
    with pytest.raises(AssertionError, match="Exact35 safety complete equality"):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize(
    "mutation",
    (
        "project", "step", "manifest_schema_version", "result_schema_version",
        "adapter_side_normalization", "context_before_candidate",
        "source_structural_checks_before_first_explicit_content_read",
        "output_sha256_excludes_manifest_self_hash", "source_nested_unknown",
        "readiness_mirror", "top_level_unknown",
    ),
)
def test_checker_rejects_exact123_manifest_tamper(tmp_path: Path, mutation: str) -> None:
    checker = _checker()
    copied = _copied_outputs(tmp_path, f"manifest-{mutation}")
    path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "project":
        manifest["project"] = "TAMPERED"
    elif mutation == "step":
        manifest["step"] = "tampered step"
    elif mutation == "manifest_schema_version":
        manifest["manifest_schema_version"] = "tampered_manifest_v1"
    elif mutation == "result_schema_version":
        manifest["result_schema_version"] = "tampered_result_v1"
    elif mutation == "adapter_side_normalization":
        manifest["adapter_side_normalization"] = True
    elif mutation == "context_before_candidate":
        manifest["context_before_candidate"] = False
    elif mutation == "source_structural_checks_before_first_explicit_content_read":
        manifest[mutation] = False
    elif mutation == "output_sha256_excludes_manifest_self_hash":
        manifest[mutation] = False
    elif mutation == "source_nested_unknown":
        manifest["source_input_verification"][0]["unknown_key"] = True
    elif mutation == "readiness_mirror":
        manifest["ready_for_training"] = True
    elif mutation == "top_level_unknown":
        manifest["unknown_key"] = True
    else:
        raise AssertionError("unhandled mutation")
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="Exact123 manifest complete equality"):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)
