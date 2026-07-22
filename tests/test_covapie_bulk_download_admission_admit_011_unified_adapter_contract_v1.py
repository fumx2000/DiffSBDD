from __future__ import annotations

import ast
import csv
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

from covalent_ext import covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate as oracle
from covalent_ext import covapie_bulk_download_admission_admit_011_rule_logic_interface as standalone
from covalent_ext import covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate as gate
from covalent_ext import covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010 as runtime


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / gate.DEFAULT_OUTPUT_ROOT
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_011_unified_adapter_contract_v1.py"
SCALAR = "data/raw/a.cif"


def snapshot(*paths: str) -> oracle.ExistingRawTargetRelativePathsSnapshot:
    return oracle.ExistingRawTargetRelativePathsSnapshot(
        "covapie_existing_raw_target_relative_paths_snapshot_v1",
        oracle.DEFAULT_CONTRACT.canonical_raw_root_identity,
        oracle.DEFAULT_CONTRACT.candidate_coordinate_system,
        oracle.DEFAULT_CONTRACT.path_grammar_version,
        oracle.DEFAULT_CONTRACT.equality_policy,
        oracle.DEFAULT_CONTRACT.snapshot_phase,
        True,
        tuple(paths),
    )


SNAPSHOT = snapshot()
CONTRACT = oracle.DEFAULT_CONTRACT


def checker_module():
    spec = importlib.util.spec_from_file_location("admit011_adapter_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copied_outputs(tmp_path: Path, name: str) -> Path:
    copied = tmp_path / name
    shutil.copytree(OUTPUT_ROOT, copied)
    return copied


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or ())
        rows = list(reader)
    assert header and rows and all(tuple(row) == tuple(header) for row in rows)
    return header, rows


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def sync_manifest_output_sha(copied: Path, filename: str) -> None:
    manifest_path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert filename in manifest["output_sha256"]
    manifest["output_sha256"][filename] = hashlib.sha256((copied / filename).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_synced_csv_tamper_rejected(copied: Path, filename: str) -> None:
    sync_manifest_output_sha(copied, filename)
    with pytest.raises((AssertionError, ValueError, KeyError, TypeError)):
        checker_module()._validate_output_tree(copied, enforce_frozen_hashes=False)


def route(candidate: object, **overrides: object):
    arguments = {
        "batch_context": None,
        "evaluation_context": {
            gate.CONTEXT_ITEMS[0]: CONTRACT,
            gate.CONTEXT_ITEMS[1]: SNAPSHOT,
        },
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    arguments.update(overrides)
    return gate.route_and_project_for_design(candidate, **arguments)


class CountingMapping(Mapping):
    def __init__(self, values: dict[str, object], *, repeat_bomb: bool = False, error: Exception | None = None):
        self.values = values
        self.repeat_bomb = repeat_bomb
        self.error = error
        self.calls: list[object] = []
        self.iterated = False

    def __getitem__(self, key: object) -> object:
        self.calls.append(key)
        if self.error is not None:
            raise self.error
        if self.repeat_bomb and self.calls.count(key) > 1:
            raise RuntimeError("duplicate lookup")
        return self.values[key]  # type: ignore[index]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)


class Bomb:
    def __getattribute__(self, name: str):
        raise AssertionError(f"bomb accessed: {name}")


def test_identity_schema_and_orders_are_exact() -> None:
    assert (gate.PROJECT, gate.STEP, gate.STAGE) == (
        "CovaPIE", "ADMIT_011 unified adapter contract design gate v1",
        "covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1",
    )
    assert (gate.ADMISSION_RULE_ID, gate.ADMISSION_RULE_NAME, gate.ADAPTER_ID) == (
        "ADMIT_011", "raw_overwrite_forbidden", "covapie_admit_011_unified_adapter_v1",
    )
    assert gate.CURRENT_REGISTERED_RULE_ORDER == tuple(f"ADMIT_{n:03d}" for n in range(1, 11))
    assert gate.FUTURE_REGISTERED_RULE_ORDER == tuple(f"ADMIT_{n:03d}" for n in range(1, 12))
    assert gate.KNOWN_RULE_IDS == tuple(f"ADMIT_{n:03d}" for n in range(1, 16))


def test_exact10_exact13_exact6_and_runtime_constants_match() -> None:
    assert gate.STANDALONE_RESULT_FIELDS == standalone.RESULT_FIELDS
    assert gate.RESULT_FIELDS == runtime.RESULT_FIELDS
    assert gate.DISPATCH_ERROR_FIELDS == runtime.DISPATCH_ERROR_FIELDS
    assert gate.DISPATCH_ERROR_CODES == runtime.DISPATCH_ERROR_CODES
    assert gate.OUTCOME_VOCABULARY == runtime.OUTCOME_VOCABULARY
    assert gate.RESULT_SCHEMA_VERSION == runtime.RESULT_SCHEMA_VERSION
    assert tuple(field.name for field in fields(gate.UnifiedAdmissionEvaluationDesignRecord)) == gate.RESULT_FIELDS


def test_design_source_has_no_runtime_handler_registry_or_dispatcher() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assignments = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    assert "_evaluate_registered_admit_011" not in functions | assignments
    assert "evaluate_admission_rule" not in functions | assignments
    assert "EVALUATOR_REGISTRY" not in assignments
    assert tuple(runtime.EVALUATOR_REGISTRY) == gate.CURRENT_REGISTERED_RULE_ORDER


@pytest.mark.parametrize("field,value,reason", (
    ("batch_context", object(), "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE"),
    ("evaluation_context", None, "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
    ("evaluation_context", {}, "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED"),
    ("evaluation_context", {gate.CONTEXT_ITEMS[0]: CONTRACT}, "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED"),
    ("download_result_context", object(), "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
    ("stage_authorization_context", object(), "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
))
def test_context_failures_are_exact6(field: str, value: object, reason: str) -> None:
    arguments = {
        "batch_context": None,
        "evaluation_context": {gate.CONTEXT_ITEMS[0]: CONTRACT, gate.CONTEXT_ITEMS[1]: SNAPSHOT},
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    arguments[field] = value
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(Bomb(), **arguments)
    assert tuple(caught.value.as_dict()) == gate.DISPATCH_ERROR_FIELDS
    assert caught.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "admission_rule_id": "ADMIT_011",
        "known_rule": True, "callable_discovered": True, "adapter_ready": True, "reason": reason,
    }


def test_context_precedence_blocks_later_access() -> None:
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(
            Bomb(), batch_context=object(), evaluation_context=Bomb(),
            download_result_context=object(), stage_authorization_context=object(),
        )
    assert caught.value.reason == gate.CONTEXT_REASONS["batch_context"]
    evaluation = CountingMapping({}, repeat_bomb=True)
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(Bomb(), batch_context=None, evaluation_context=evaluation, download_result_context=object(), stage_authorization_context=object())
    assert caught.value.reason == gate.CONTEXT_REASONS["contract_key"]
    assert evaluation.calls == [gate.CONTEXT_ITEMS[0]]


def test_contract_missing_precedes_snapshot_and_snapshot_missing_precedes_candidate() -> None:
    contract_missing = CountingMapping({gate.CONTEXT_ITEMS[1]: SNAPSHOT})
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(Bomb(), batch_context=None, evaluation_context=contract_missing, download_result_context=None, stage_authorization_context=None)
    assert caught.value.reason == gate.CONTEXT_REASONS["contract_key"]
    assert contract_missing.calls == [gate.CONTEXT_ITEMS[0]]
    snapshot_missing = CountingMapping({gate.CONTEXT_ITEMS[0]: CONTRACT})
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(Bomb(), batch_context=None, evaluation_context=snapshot_missing, download_result_context=None, stage_authorization_context=None)
    assert caught.value.reason == gate.CONTEXT_REASONS["snapshot_key"]
    assert snapshot_missing.calls == list(gate.CONTEXT_ITEMS)


def test_download_and_stage_errors_precede_candidate_access() -> None:
    context = CountingMapping({gate.CONTEXT_ITEMS[0]: CONTRACT, gate.CONTEXT_ITEMS[1]: SNAPSHOT})
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(Bomb(), batch_context=None, evaluation_context=context, download_result_context=object(), stage_authorization_context=None)
    assert caught.value.reason == gate.CONTEXT_REASONS["download_result_context"]
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        gate.route_and_project_for_design(Bomb(), batch_context=None, evaluation_context=context, download_result_context=None, stage_authorization_context=object())
    assert caught.value.reason == gate.CONTEXT_REASONS["stage_authorization_context"]


def test_mapping_subclasses_extra_keys_and_exact_lookup_counts() -> None:
    context = CountingMapping({gate.CONTEXT_ITEMS[0]: CONTRACT, gate.CONTEXT_ITEMS[1]: SNAPSHOT, "extra": Bomb()}, repeat_bomb=True)
    candidate = CountingMapping({gate.CANDIDATE_FIELDS[0]: SCALAR, "extra": Bomb()}, repeat_bomb=True)
    result = gate.route_and_project_for_design(candidate, batch_context=None, evaluation_context=context, download_result_context=None, stage_authorization_context=None)
    assert result.outcome == "passed"
    assert context.calls == list(gate.CONTEXT_ITEMS)
    assert candidate.calls == list(gate.CANDIDATE_FIELDS)
    assert not context.iterated and not candidate.iterated


@pytest.mark.parametrize("candidate,reason", ((object(), gate.CANDIDATE_MAPPING_REASON), ({}, gate.MISSING_REASON)))
def test_candidate_invalid_exact13_without_formal_or_oracle(candidate: object, reason: str) -> None:
    calls = {"formal": 0, "oracle": 0}
    def formal(*args: object):
        calls["formal"] += 1
        raise AssertionError
    def classify(*args: object):
        calls["oracle"] += 1
        raise AssertionError
    result = route(candidate, formal_evaluator=formal, oracle_callable=classify)
    assert result == gate.candidate_invalid_exact13_for_design(reason)
    assert tuple(getattr(result, name) for name in gate.RESULT_FIELDS) == (
        gate.RESULT_SCHEMA_VERSION, "ADMIT_011", "raw_overwrite_forbidden", "invalid", False, True,
        reason, (), (), ("raw_target_relative_path",), gate.CONTEXT_ITEMS, False, gate.ADAPTER_ID,
    )
    assert calls == {"formal": 0, "oracle": 0}


@pytest.mark.parametrize("scalar", (None, "", "docs/a", "data/raw/a/", "data/raw/a.cif"))
def test_present_scalar_is_forwarded_without_adapter_grammar(scalar: object) -> None:
    seen: list[tuple[object, object, object]] = []
    def formal(a: object, b: object, c: object):
        seen.append((a, b, c))
        return standalone.evaluate_admit_011(a, b, c)
    route({gate.CANDIDATE_FIELDS[0]: scalar}, formal_evaluator=formal)
    assert len(seen) == 1 and seen[0][0] is scalar


def test_formal_and_oracle_argument_order_identity_and_exactly_once() -> None:
    scalar = object()
    snap = object()
    contract = object()
    formal_seen: list[tuple[object, object, object]] = []
    oracle_seen: list[tuple[object, object, object]] = []
    def formal(a: object, b: object, c: object):
        formal_seen.append((a, b, c))
        return standalone.evaluate_admit_011(a, b, c)
    def classify(a: object, b: object, c: object):
        oracle_seen.append((a, b, c))
        return oracle.classify_admit_011_raw_target_relative_path_design(a, b, c)
    result = gate.route_and_project_for_design(
        {gate.CANDIDATE_FIELDS[0]: scalar}, batch_context=None,
        evaluation_context={gate.CONTEXT_ITEMS[0]: contract, gate.CONTEXT_ITEMS[1]: snap},
        download_result_context=None, stage_authorization_context=None,
        formal_evaluator=formal, oracle_callable=classify,
    )
    assert result.reason == "RAW_TARGET_RELATIVE_PATH_TYPE_INVALID"
    assert formal_seen == [(scalar, snap, contract)]
    assert oracle_seen == [(scalar, snap, contract)]
    assert all(left is right for left, right in zip(formal_seen[0], oracle_seen[0], strict=True))


def test_formal_exception_prevents_source_validation_and_oracle() -> None:
    calls = {"formal": 0, "oracle": 0}
    def formal(*args: object):
        calls["formal"] += 1
        raise RuntimeError("formal failure")
    def classify(*args: object):
        calls["oracle"] += 1
    with pytest.raises(RuntimeError, match="formal failure"):
        route({gate.CANDIDATE_FIELDS[0]: SCALAR}, formal_evaluator=formal, oracle_callable=classify)
    assert calls == {"formal": 1, "oracle": 0}


@pytest.mark.parametrize("value", (object(), None, {"outcome": "passed"}))
def test_source_wrong_type_fails_before_oracle(value: object) -> None:
    calls = {"oracle": 0}
    def classify(*args: object):
        calls["oracle"] += 1
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        route({gate.CANDIDATE_FIELDS[0]: SCALAR}, formal_evaluator=lambda *args: value, oracle_callable=classify)
    assert caught.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert caught.value.reason == gate.SOURCE_TYPE_REASON and caught.value.adapter_ready is False
    assert calls["oracle"] == 0


def test_source_subclass_is_rejected_before_oracle() -> None:
    class Subclass(standalone.Admit011EvaluationResult):
        pass
    value = object.__new__(Subclass)
    valid = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    for name in gate.STANDALONE_RESULT_FIELDS:
        object.__setattr__(value, name, getattr(valid, name))
    decision = gate.validate_source_shape_and_invariants_for_design(value)
    assert decision.reason == gate.SOURCE_TYPE_REASON and not decision.accepted


@pytest.mark.parametrize("name,value", (
    ("evaluator_io_used", True),
    ("admission_rule_id", "ADMIT_999"),
    ("validated_candidate_fields", ()),
    ("consumed_context_items", ()),
    ("passed", False),
))
def test_source_invariant_tamper_is_rejected(name: str, value: object) -> None:
    source = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    object.__setattr__(source, name, value)
    decision = gate.validate_source_shape_and_invariants_for_design(source)
    assert not decision.accepted and decision.reason == gate.SOURCE_INVARIANT_REASON


def test_source_extra_storage_is_rejected() -> None:
    source = standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
    object.__setattr__(source, "extra", "drift")
    assert gate.validate_source_shape_and_invariants_for_design(source).reason == gate.SOURCE_INVARIANT_REASON


def test_oracle_actual_exact_type_and_complete_conversion() -> None:
    design = oracle.classify_admit_011_raw_target_relative_path_design(SCALAR, SNAPSHOT, CONTRACT)
    assert type(design) is oracle.Admit011EvaluationResultDesign
    expected = gate.expected_exact10_from_committed_oracle_for_design(SCALAR, SNAPSHOT, CONTRACT)
    assert type(expected) is standalone.Admit011EvaluationResult
    assert tuple(getattr(expected, name) for name in gate.STANDALONE_RESULT_FIELDS) == tuple(getattr(design, name) for name in gate.STANDALONE_RESULT_FIELDS)


@pytest.mark.parametrize("mode", ("exception", "wrong_type", "mismatch"))
def test_oracle_failures_are_adapter_not_ready_without_projection(mode: str) -> None:
    def classify(*args: object):
        if mode == "exception":
            raise RuntimeError("oracle failure")
        if mode == "wrong_type":
            return standalone.evaluate_admit_011(SCALAR, SNAPSHOT, CONTRACT)
        return oracle.classify_admit_011_raw_target_relative_path_design("docs/a", SNAPSHOT, CONTRACT)
    with pytest.raises(gate.AdapterContractDesignError) as caught:
        route({gate.CANDIDATE_FIELDS[0]: SCALAR}, oracle_callable=classify)
    assert caught.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "admission_rule_id": "ADMIT_011",
        "known_rule": True, "callable_discovered": True, "adapter_ready": False,
        "reason": gate.SOURCE_INVARIANT_REASON,
    }


@pytest.mark.parametrize("scalar,snap,expected_outcome,reason", (
    (SCALAR, SNAPSHOT, "passed", ""),
    (SCALAR, snapshot(SCALAR), "blocked", "RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED"),
    ("docs/a", SNAPSHOT, "invalid", "RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN"),
    (SCALAR, object(), "invalid", "EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_TYPE_INVALID"),
))
def test_exact13_projection_passed_collision_and_invalid(scalar: object, snap: object, expected_outcome: str, reason: str) -> None:
    result = gate.route_and_project_for_design(
        {gate.CANDIDATE_FIELDS[0]: scalar}, batch_context=None,
        evaluation_context={gate.CONTEXT_ITEMS[0]: CONTRACT, gate.CONTEXT_ITEMS[1]: snap},
        download_result_context=None, stage_authorization_context=None,
    )
    source = standalone.evaluate_admit_011(scalar, snap, CONTRACT)
    assert result.outcome == expected_outcome and result.reason == reason
    assert result.normalized_values == result.validated_candidate_fields == source.validated_candidate_fields
    assert result.consumed_candidate_fields == source.consumed_candidate_fields
    assert result.consumed_context_items == source.consumed_context_items
    assert result.evaluator_io_used is False and result.adapter_id == gate.ADAPTER_ID


def test_exact84_exact47_and_all_semantic_groups() -> None:
    state = gate.build_design_state()
    rows = state["truth_rows"]
    assert len(rows) == 84
    assert sum(row["case_id"].startswith("HIST_") for row in rows) == 47
    assert sum(row["case_id"].startswith("SCALAR_") for row in rows) == 19
    assert sum(row["case_id"].startswith("MISMATCH_") for row in rows) == 5
    assert {row["case_id"] for row in rows} >= {"CONTRACT_TYPE", "CONTRACT_VALUE", "SNAPSHOT_TYPE", "SNAPSHOT_VALUE", "COLLISION", "PASSED", "MULTI_CONTRACT_SNAPSHOT"}
    assert all(row["formal_call_count"] == row["oracle_call_count"] == "1" and row["case_passed"] == "true" for row in rows)


def test_source_boundary_exact16_and_base_lineage() -> None:
    state = gate.build_design_state()
    snapshot_value = state["snapshot"]
    assert len(snapshot_value.records) == 16
    assert tuple(record.relative_path for record in snapshot_value.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256 for record in snapshot_value.records)


def test_issue_transition_is_preserved_not_closed() -> None:
    state = gate.build_design_state()
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issues["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] == "resolved"
    assert issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open"
    assert issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    assert issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open"


def test_manifest_readiness_exact_required_values() -> None:
    manifest = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILENAME).read_text())
    assert all(manifest[key] is True and manifest["readiness"][key] is True for key in gate.TRUE_READINESS)
    assert all(manifest[key] is False and manifest["readiness"][key] is False for key in gate.FALSE_READINESS)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["step12d_is_final_training_feature_contract"] is False


def test_six_outputs_have_exact_headers_and_hashes() -> None:
    checker = checker_module()
    hashes = checker._validate_output_tree()
    assert hashes == checker.FROZEN_OUTPUT_SHA256
    assert set(path.name for path in OUTPUT_ROOT.iterdir()) == set(gate.OUTPUT_FILES)


def test_double_materialization_and_existing_set_inode_preserving_noop(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    gate.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(root)
    before = {name: ((root / name).stat().st_ino, (root / name).read_bytes()) for name in gate.OUTPUT_FILES}
    gate.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(root)
    after = {name: ((root / name).stat().st_ino, (root / name).read_bytes()) for name in gate.OUTPUT_FILES}
    assert before == after
    assert {name: hashlib.sha256(value[1]).hexdigest() for name, value in after.items()} == checker_module().FROZEN_OUTPUT_SHA256


def test_existing_output_mismatch_fails_closed_without_repair(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    gate.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(root)
    target = root / gate.CONTRACT_FILENAME
    target.write_bytes(b"tampered\n")
    before = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    with pytest.raises(ValueError, match="repair forbidden"):
        gate.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(root)
    assert {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES} == before


@pytest.mark.parametrize("kind", ("root_symlink", "root_file", "unexpected", "leaf_symlink"))
def test_materializer_preflight_rejects_unsafe_output(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "evidence"
    if kind == "root_symlink":
        target = tmp_path / "target"; target.mkdir(); root.symlink_to(target, target_is_directory=True)
    elif kind == "root_file":
        root.write_text("x")
    else:
        gate.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(root)
        if kind == "unexpected":
            (root / "unexpected").write_text("x")
        else:
            leaf = root / gate.CONTRACT_FILENAME; leaf.unlink(); leaf.symlink_to(root / gate.ROUTING_FILENAME)
    with pytest.raises(ValueError):
        gate.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(root)


def test_checker_rejects_synchronized_semantic_tamper(tmp_path: Path) -> None:
    checker = checker_module()
    copied = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, copied)
    path = copied / gate.ROUTING_FILENAME
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); header = tuple(reader.fieldnames or ()); rows = list(reader)
    rows[0]["expected_reason"] = "tampered"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    manifest_path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][gate.ROUTING_FILENAME] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_owned_exact26_exact33_exact32_match_frozen_outputs() -> None:
    checker = checker_module()
    contract_header, contract = read_csv(OUTPUT_ROOT / gate.CONTRACT_FILENAME)
    routing_header, routing = read_csv(OUTPUT_ROOT / gate.ROUTING_FILENAME)
    safety_header, safety = read_csv(OUTPUT_ROOT / gate.SAFETY_FILENAME)
    assert tuple(contract_header) == checker.CONTRACT_COLUMNS
    assert tuple(routing_header) == checker.ROUTING_COLUMNS
    assert tuple(safety_header) == checker.SAFETY_COLUMNS
    assert tuple(contract) == checker._expected_contract_rows()
    assert tuple(routing) == checker._expected_routing_rows()
    assert tuple(safety) == checker._expected_safety_rows()
    assert len({(row["matrix_group"], row["case_id"]) for row in routing}) == 33


@pytest.mark.parametrize("row_index,column,expected,replacement", (
    (0, "contract_order", "1", "99"),
    (4, "contract_id", "CONTRACT_005", "CONTRACT_999"),
    (7, "contract_group", "formal", "tampered_group"),
    (13, "contract_subject", "error_codes", "tampered_subject"),
    (24, "contract_value", "no_provider_mapping_raw_network_download_model_checkpoint_training", "weakened_boundary"),
    (0, "contract_status", "frozen", "open"),
))
def test_checker_rejects_synced_contract_tamper_every_column(
    tmp_path: Path, row_index: int, column: str, expected: str, replacement: str,
) -> None:
    copied = copied_outputs(tmp_path, f"contract-{column}")
    path = copied / gate.CONTRACT_FILENAME
    header, rows = read_csv(path)
    assert rows[row_index][column] == expected
    rows[row_index][column] = replacement
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.CONTRACT_FILENAME)


@pytest.mark.parametrize("mode", ("reorder", "extra_row", "missing_row", "extra_column", "missing_column"))
def test_checker_rejects_synced_contract_shape_tamper(tmp_path: Path, mode: str) -> None:
    copied = copied_outputs(tmp_path, f"contract-shape-{mode}")
    path = copied / gate.CONTRACT_FILENAME
    header, rows = read_csv(path)
    if mode == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mode == "extra_row":
        rows.append(dict(rows[-1]))
    elif mode == "missing_row":
        rows.pop()
    elif mode == "extra_column":
        header.append("unexpected")
        for row in rows:
            row["unexpected"] = "x"
    else:
        assert "contract_subject" in header
        header.remove("contract_subject")
        for row in rows:
            row.pop("contract_subject")
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.CONTRACT_FILENAME)


@pytest.mark.parametrize("row_index,column,expected,replacement", (
    (0, "matrix_order", "1", "99"),
    (0, "matrix_group", "context", "tampered_group"),
    (0, "case_id", "batch_non_none", "tampered_case"),
    (0, "condition", "batch non-None", "tampered condition"),
    (21, "expected_behavior", "one positional candidate_snapshot_contract call", "tampered behavior"),
    (0, "expected_reason", "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE", "tampered reason"),
    (16, "expected_result_json", None, "{}"),
    (21, "formal_call_count", "1", "0"),
    (22, "oracle_call_count", "1", "0"),
    (21, "candidate_access_status", "value_read_once", "not_accessed"),
    (21, "required_lookup_count", "3", "99"),
    (21, "identity_preserved", "true", "false"),
    (21, "case_passed", "true", "false"),
))
def test_checker_rejects_synced_routing_tamper_every_column(
    tmp_path: Path, row_index: int, column: str, expected: str | None, replacement: str,
) -> None:
    copied = copied_outputs(tmp_path, f"routing-{column}")
    path = copied / gate.ROUTING_FILENAME
    header, rows = read_csv(path)
    if expected is None:
        assert rows[row_index][column].startswith("{")
    else:
        assert rows[row_index][column] == expected
    rows[row_index][column] = replacement
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.ROUTING_FILENAME)


@pytest.mark.parametrize("mode", ("reorder", "duplicate_case_id", "extra_row", "missing_row", "extra_column", "missing_column"))
def test_checker_rejects_synced_routing_shape_tamper(tmp_path: Path, mode: str) -> None:
    copied = copied_outputs(tmp_path, f"routing-shape-{mode}")
    path = copied / gate.ROUTING_FILENAME
    header, rows = read_csv(path)
    if mode == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mode == "duplicate_case_id":
        assert rows[0]["case_id"] != rows[1]["case_id"]
        rows[0]["case_id"] = rows[1]["case_id"]
    elif mode == "extra_row":
        rows.append(dict(rows[-1]))
    elif mode == "missing_row":
        rows.pop()
    elif mode == "extra_column":
        header.append("unexpected")
        for row in rows:
            row["unexpected"] = "x"
    else:
        assert "condition" in header
        header.remove("condition")
        for row in rows:
            row.pop("condition")
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.ROUTING_FILENAME)


@pytest.mark.parametrize("column,replacement", (
    ("case_id", "tampered_case"),
    ("case_group", "tampered_group"),
    ("behavior", "tampered_behavior"),
    ("expected_dispatch_code", "UNEXPECTED_CODE"),
    ("expected_reason", "tampered_reason"),
    ("source_exact10_json", "{}"),
    ("oracle_exact10_json", "{}"),
    ("unified_exact13_json", "{}"),
    ("formal_call_count", "0"),
    ("oracle_call_count", "0"),
    ("case_passed", "false"),
))
def test_checker_rejects_synced_truth_tamper_every_column(tmp_path: Path, column: str, replacement: str) -> None:
    copied = copied_outputs(tmp_path, f"truth-{column}")
    path = copied / gate.TRUTH_FILENAME
    header, rows = read_csv(path)
    expected = {
        "case_id": "HIST_001", "case_group": "historical_observed",
        "behavior": "exact10_to_exact13", "expected_dispatch_code": "",
        "expected_reason": "", "formal_call_count": "1", "oracle_call_count": "1",
        "case_passed": "true",
    }
    if column in expected:
        assert rows[0][column] == expected[column]
    else:
        parsed = json.loads(rows[0][column])
        assert type(parsed) is dict and parsed
    rows[0][column] = replacement
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.TRUTH_FILENAME)


@pytest.mark.parametrize("row_index,column,expected,replacement", (
    (0, "safety_item", "adapter_contract_design", "tampered_item"),
    (0, "expected_executed", "true", "false"),
    (0, "observed_executed", "true", "false"),
    (0, "safety_passed", "true", "false"),
    (16, "observed_executed", "false", "true"),
    (22, "observed_executed", "false", "true"),
    (23, "observed_executed", "false", "true"),
    (29, "observed_executed", "false", "true"),
))
def test_checker_rejects_synced_safety_tamper_all_fields_and_forbidden_rows(
    tmp_path: Path, row_index: int, column: str, expected: str, replacement: str,
) -> None:
    copied = copied_outputs(tmp_path, f"safety-{row_index}-{column}")
    path = copied / gate.SAFETY_FILENAME
    header, rows = read_csv(path)
    assert rows[row_index][column] == expected
    if row_index == 16:
        assert rows[row_index]["safety_item"] == "adapter_filesystem_use"
    elif row_index == 22:
        assert rows[row_index]["safety_item"] == "candidate_context_mutation"
    elif row_index == 23:
        assert rows[row_index]["safety_item"] == "model_forward"
    elif row_index == 29:
        assert rows[row_index]["safety_item"] == "stage"
    rows[row_index][column] = replacement
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.SAFETY_FILENAME)


@pytest.mark.parametrize("mode", ("reorder", "duplicate_item", "extra_row", "missing_row", "extra_column", "missing_column"))
def test_checker_rejects_synced_safety_shape_tamper(tmp_path: Path, mode: str) -> None:
    copied = copied_outputs(tmp_path, f"safety-shape-{mode}")
    path = copied / gate.SAFETY_FILENAME
    header, rows = read_csv(path)
    if mode == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mode == "duplicate_item":
        assert rows[0]["safety_item"] != rows[1]["safety_item"]
        rows[0]["safety_item"] = rows[1]["safety_item"]
    elif mode == "extra_row":
        rows.append(dict(rows[-1]))
    elif mode == "missing_row":
        rows.pop()
    elif mode == "extra_column":
        header.append("unexpected")
        for row in rows:
            row["unexpected"] = "x"
    else:
        assert "observed_executed" in header
        header.remove("observed_executed")
        for row in rows:
            row.pop("observed_executed")
    write_csv(path, header, rows)
    assert_synced_csv_tamper_rejected(copied, gate.SAFETY_FILENAME)


@pytest.mark.parametrize("mode", ("extra_key", "readiness", "source_verification", "projection_count"))
def test_checker_rejects_manifest_semantic_tamper_without_frozen_hashes(tmp_path: Path, mode: str) -> None:
    checker = checker_module()
    copied = tmp_path / mode
    shutil.copytree(OUTPUT_ROOT, copied)
    path = copied / gate.MANIFEST_FILENAME
    manifest = json.loads(path.read_text())
    if mode == "extra_key":
        manifest["unexpected"] = True
    elif mode == "readiness":
        manifest["readiness"][gate.TRUE_READINESS[0]] = False
    elif mode == "source_verification":
        manifest["source_input_verification"][0]["tracked"] = False
    else:
        manifest["projection_truth_matrix_row_count"] = 83
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        checker._validate_output_tree(copied, enforce_frozen_hashes=False)


def test_malicious_candidate_representation_is_not_executed(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    expression = f"__import__('pathlib').Path({str(marker)!r}).write_text('owned')"
    with pytest.raises((ValueError, SyntaxError)):
        ast.literal_eval(expression)
    assert not marker.exists()


def test_production_and_checker_import_are_silent_and_side_effect_free(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    script = (
        "import importlib.util; import covalent_ext.covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate;"
        f"s=importlib.util.spec_from_file_location('c',{str(CHECKER_PATH)!r});m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        f"assert not __import__('pathlib').Path({str(marker)!r}).exists()"
    )
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True, check=False)
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""
    assert not marker.exists()


def test_public_design_api_signature_is_frozen() -> None:
    signature = inspect.signature(gate.route_and_project_for_design)
    assert tuple(signature.parameters) == (
        "candidate_record", "batch_context", "evaluation_context", "download_result_context",
        "stage_authorization_context", "formal_evaluator", "oracle_callable",
    )
    assert all(signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY for name in tuple(signature.parameters)[1:])


def test_no_forbidden_artifact_in_candidate_delta() -> None:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    paths = [ROOT / line[3:] for line in status]
    assert not any(path.suffix in forbidden for path in paths)
